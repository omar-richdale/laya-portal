"""Measure three hosted CUDA checkpoints against a fixed, sourced real-data corpus.

Reference agreement measures routing against metadata/evidence-audit labels; it
does not measure vulnerability truth. Full response records remain locally auditable.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.common import Client
from laya_portal.workflows import LABELS, QUESTIONS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "benchmark"
MODELS = ("english", "multilingual", "typed-decisions")


def percentile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p
    lo = int(position)
    hi = min(lo + 1, len(values) - 1)
    return round(values[lo] + (values[hi] - values[lo]) * (position - lo), 2)


def metrics(records):
    counts = Counter()
    confusion = defaultdict(Counter)
    for row in records:
        confusion[row["expected"]][row["predicted"]] += 1
        counts["correct"] += row["correct"]
        counts["review"] += row["confidence"] < 0.8 or row["truncated"]
        counts["high_confidence_wrong"] += not row["correct"] and row["confidence"] >= 0.8
    f1s = []
    for label in sorted({row["expected"] for row in records}):
        tp = confusion[label][label]
        fp = sum(v[label] for k, v in confusion.items() if k != label)
        fn = sum(v for k, v in confusion[label].items() if k != label)
        f1s.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0)
    return {"count": len(records), **dict(counts),
            "agreement": round(counts["correct"] / len(records), 4),
            "macro_f1": round(statistics.mean(f1s), 4),
            "confusion": {k: dict(v) for k, v in confusion.items()}}


def benchmark(repeats=3):
    corpus_bytes = (OUT / "corpus.json").read_bytes()
    corpus = json.loads(corpus_bytes)
    cases = corpus["cases"]
    result = {"started_at": datetime.now(timezone.utc).isoformat(), "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
              "corpus_metadata": corpus["metadata"], "repeats": repeats, "models": {},
              "method": {"transport": "authenticated localhost HTTP; shared single worker", "microbatch": 1,
                         "max_len": 512, "head_max_len": 192, "warmup_calls": 3,
                         "seed": 4050, "reference_quality": "metadata routing + seven manually audited QA failures, not exploit validation",
                         "gpu_memory": "observed service allocator values after calls; lifetime peak is explicitly separate and may include prior models"}}
    client = Client()
    try:
        original = client.request("GET", "/api/v1/status")
        result["environment"] = {k: original[k] for k in ("gpu", "versions", "revision", "default_model")}
        for model in MODELS:
            before = client.request("GET", "/api/v1/status")
            load_calls = []
            warm_payload = {"model": model, "state": cases[0]["state"], "questions": QUESTIONS[cases[0]["workflow"]], "max_len": 512, "head_max_len": 192}
            for _ in range(3):
                load_calls.append(client.request("POST", "/api/v1/predict", json=warm_payload)["runtime"])
            rows, allocated, reserved = [], [], []
            for repeat in range(repeats):
                order = list(range(len(cases)))
                random.Random(4050 + repeat).shuffle(order)
                for index in order:
                    case = cases[index]
                    request = {"model": model, "state": case["state"], "questions": QUESTIONS[case["workflow"]],
                               "max_len": 512, "head_max_len": 192, "min_confidence": 0.8}
                    start = time.perf_counter()
                    response = client.request("POST", "/api/v1/predict", json=request)
                    http_ms = round((time.perf_counter() - start) * 1000, 2)
                    if response["runtime"]["device"] != "cuda:0":
                        raise RuntimeError("Benchmark result was not computed on CUDA")
                    answer = response["answers"]["decision"]
                    rows.append({"id": case["id"], "workflow": case["workflow"], "source": case["source"], "repeat": repeat,
                                 "expected": case["expected"], "predicted": answer["choice"], "confidence": answer["answer_confidence"],
                                 "correct": answer["choice"] == case["expected"], "truncated": bool(response["usage"].get("truncated")),
                                 "http_ms": http_ms, "service_ms": response["runtime"]["elapsed_ms"], "response": response})
                    status = client.request("GET", "/api/v1/status")
                    allocated.append(status["gpu"]["allocated_bytes"])
                    reserved.append(status["gpu"]["reserved_bytes"])
                print(f"{model}: pass {repeat + 1}/{repeats}, {len(cases)} sourced cases on CUDA", flush=True)
            # A mixed sample measures the existing ordered batch path; timing is
            # a different workload from individual-request latency above.
            sample = [c for c in cases if c["workflow"] != "issue_lane"] + cases[:18]
            batch_request = {"requests": [{"model": model, "state": c["state"], "questions": QUESTIONS[c["workflow"]],
                                          "max_len": 512, "head_max_len": 192} for c in sample], "batch_size": 2}
            batches = []
            for _ in range(3):
                batch = client.request("POST", "/api/v1/predict/batch", json=batch_request)
                assert len(batch["results"]) == len(sample)
                assert all(r["runtime"]["device"] == "cuda:0" for r in batch["results"])
                batches.append(batch["runtime"]["elapsed_ms"])
            first = [r for r in rows if r["repeat"] == 0]
            service_ms = [r["service_ms"] for r in rows]
            http_ms = [r["http_ms"] for r in rows]
            status = client.request("GET", "/api/v1/status")
            report = {
                "quality": {workflow: metrics([r for r in first if r["workflow"] == workflow]) for workflow in QUESTIONS},
                "service_ms": {"median": percentile(service_ms, .5), "p95": percentile(service_ms, .95)},
                "http_ms": {"median": percentile(http_ms, .5), "p95": percentile(http_ms, .95)},
                "warmup": {"resident_before": before["resident_model"], "calls": load_calls},
                "batch": {"states": len(sample), "microbatch": 2, "median_ms": percentile(batches, .5),
                          "states_per_second": round(len(sample) / (statistics.median(batches) / 1000), 2)},
                "max_observed_allocated_bytes": max(allocated), "max_observed_reserved_bytes": max(reserved),
                "service_lifetime_peak_allocated_bytes": status["gpu"]["peak_allocated_bytes"],
                "truncated_calls": sum(r["truncated"] for r in rows),
                "changed_predictions_across_repeats": sum(len({r["predicted"] for r in rows if r["id"] == case["id"]}) > 1 for case in cases),
                "records": rows,
            }
            result["models"][model] = report
            # Preserve completed models if a later load or request fails.
            (OUT / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            print(json.dumps({"model": model, **{k: v for k, v in report.items() if k in ("quality", "service_ms", "batch", "truncated_calls")}}), flush=True)
        result["finished_at"] = datetime.now(timezone.utc).isoformat()
        result["default_after"] = client.request("GET", "/api/v1/status")["default_model"]
        assert result["default_after"] == original["default_model"]
        (OUT / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved full real-data benchmark to {OUT / 'results.json'}", flush=True)
    finally:
        client.close()


if __name__ == "__main__":
    benchmark()
