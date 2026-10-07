"""Measure one checkpoint in a freshly restarted service, including allocator peak.

Run stop.ps1/start.ps1 before each model. The process must have no resident model;
otherwise its allocator lifetime peak cannot be attributed to one checkpoint.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.common import Client, ROOT
from laya_portal.workflows import QUESTIONS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=("english", "multilingual", "typed-decisions"))
    args = parser.parse_args()
    client = Client()
    try:
        before = client.request("GET", "/api/v1/status")
        if before["resident_model"] is not None or before["outstanding_jobs"]:
            parser.error("Restart the service before measuring an isolated checkpoint")
        cases = json.loads((ROOT / "docs/benchmark/corpus.json").read_text(encoding="utf-8"))["cases"]
        selected = [c for c in cases if c["workflow"] != "issue_lane"] + [c for c in cases if c["workflow"] == "issue_lane"][:18]
        requests = [{"state": c["state"], "questions": QUESTIONS[c["workflow"]], "model": args.model,
                     "max_len": 512, "head_max_len": 192, "min_confidence": .8} for c in selected]
        first = client.request("POST", "/api/v1/predict", json=requests[0])
        batch = client.request("POST", "/api/v1/predict/batch", json={"requests": requests, "batch_size": 2})
        after = client.request("GET", "/api/v1/status")
        assert first["runtime"]["device"] == "cuda:0"
        assert all(r["runtime"]["device"] == "cuda:0" for r in batch["results"])
        assert after["resident_model"] == args.model
        result = {"recorded_at": datetime.now(timezone.utc).isoformat(), "checkpoint": args.model,
                  "method": "Fresh service process; one checkpoint; first request plus 32-state batch, microbatch 2, budgets 512/192. Peak is PyTorch process allocator peak including load, not total system VRAM.",
                  "before": before, "first_response": first, "batch_response": batch, "after": after,
                  "first_service_ms": first["runtime"]["elapsed_ms"], "load_ms": first["runtime"]["load_ms"],
                  "process_peak_allocated_bytes": after["gpu"]["peak_allocated_bytes"]}
        path = ROOT / f"docs/benchmark/startup-{args.model}.json"
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"{args.model}: first request {result['first_service_ms']:.2f} ms; load {result['load_ms']:.2f} ms; peak allocator {result['process_peak_allocated_bytes']/1024**3:.3f} GiB")
    finally:
        client.close()


if __name__ == "__main__":
    main()
