"""Acceptance checks on real CUDA checkpoints; save measured results without secrets."""
import asyncio
import json
import os
from pathlib import Path
import sys
import time
from types import MethodType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from laya_portal.schemas import BatchRequest, PredictRequest
from laya_portal.service import InferenceService

QUESTIONS = {"department": {"type": "choice", "instructions": "Which department should handle this request?",
                           "criteria": {"billing": "payments, invoices, refunds", "technical": "bugs, outages", "other": "everything else"}}}


async def main():
    import torch
    from laya.agent import Agent
    report = {"torch": torch.__version__, "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0), "cases": []}
    service = InferenceService(data_root=ROOT / "data" / "verification")
    await service.start()
    try:
        cases = [("english", "Please refund the duplicate charge.", "english"),
                 ("french", "J’ai été facturé deux fois. Merci de me rembourser.", "multilingual"),
                 ("arabic", "تم خصم المبلغ مرتين من حسابي. أرجو إعادة المبلغ الزائد.", "multilingual"),
                 ("typed", "The customer was charged twice and requests a refund.", "typed-decisions")]
        for label, state, expected in cases:
            req = PredictRequest(state=state, questions=QUESTIONS, model=expected if label=="typed" else "auto")
            started = time.perf_counter()
            result = await service.predict(req)
            assert result["routing"]["model"] == expected, result["routing"]
            assert result["runtime"]["device"] == "cuda:0"
            warm = await service.predict(req)
            agent = service._agent
            original_infer = agent._infer
            original_to = agent.model.to
            fallback_before = agent.cpu_fallback_count

            def cuda_only_to(*args, **kwargs):
                target = args[0] if args else kwargs.get("device")
                if target is not None and str(target) == "cpu":
                    raise AssertionError("Reference baseline attempted CPU inference")
                return original_to(*args, **kwargs)

            # Compare the same weights through the upstream _infer implementation, with a guard
            # that forbids its CPU retry. No second model is allocated for the baseline.
            agent.model.to = cuda_only_to
            agent._infer = MethodType(Agent._infer, agent)
            try:
                baseline = await service.predict(req)
            finally:
                agent._infer = original_infer
                agent.model.to = original_to
            assert baseline["answers"] == warm["answers"]
            assert agent.cpu_fallback_count == fallback_before
            record = {"name": label, "model": expected, "cold_ms": result["runtime"]["elapsed_ms"],
                      "warm_ms": warm["runtime"]["elapsed_ms"], "answers": result["answers"],
                      "reference_equal": True, "gpu": service.status()["gpu"]}
            report["cases"].append(record)
            print(json.dumps({k: record[k] for k in ("name", "model", "cold_ms", "warm_ms", "reference_equal")}), flush=True)
            del agent, original_infer, original_to, cuda_only_to
        batch = await service.batch(BatchRequest(requests=[
            PredictRequest(state="Please refund my payment.", questions=QUESTIONS, model="english"),
            PredictRequest(state="L’application ne fonctionne plus.", questions=QUESTIONS, model="multilingual"),
            PredictRequest(state="The invoice is ready for payment.", questions=QUESTIONS, model="typed-decisions"),
            PredictRequest(state="The app crashes on startup.", questions=QUESTIONS, model="english"),
        ]))
        assert [r["routing"]["model"] for r in batch["results"]] == ["english", "multilingual", "typed-decisions", "english"]
        report["batch"] = {"count": len(batch["results"]), "runtime": batch["runtime"], "ordered": True}
        report["passed"] = True
    finally:
        await service.close()
        (ROOT / "data" / "verification").mkdir(parents=True, exist_ok=True)
        (ROOT / "data" / "verification" / "gpu-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
