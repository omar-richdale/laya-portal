"""Expose a small authenticated view of the frozen benchmark, without GPU work."""
import json
from functools import lru_cache

from .config import ROOT
from .workflows import LABELS, QUESTIONS


@lru_cache(maxsize=1)
def summary():
    results = json.loads((ROOT / "docs/benchmark/results.json").read_text(encoding="utf-8"))
    corpus = json.loads((ROOT / "docs/benchmark/corpus.json").read_text(encoding="utf-8"))
    wanted = {
        "VPN_website#157": "Who handles a vulnerable email package?",
        "VPN_website#68": "A credential finding can fool a confident model",
        "VPN_website#150": "Two branches return the same thing",
        "20260930-060000-9iy9o:GS-018": "The trial now needs a credit card",
        "20260930-071000-9o49u:GS-027": "A signed-out app token still works",
    }
    examples = []
    for case in corpus["cases"]:
        if case["id"] not in wanted or case["workflow"] == "security_specialist":
            continue
        example = {**case, "title": wanted[case["id"]],
                   "expected_label": LABELS[case["workflow"]][case["expected"]],
                   "prediction": {"state": case["state"], "questions": QUESTIONS[case["workflow"]],
                                  "max_len": 512, "head_max_len": 192, "min_confidence": .8}}
        example["observations"] = {}
        for model, stats in results["models"].items():
            record = next(row for row in stats["records"] if row["repeat"] == 0 and
                          row["id"] == case["id"] and row["workflow"] == case["workflow"])
            example["observations"][model] = {
                "label": LABELS[case["workflow"]][record["predicted"]],
                "confidence": record["confidence"], "matches_reference": record["correct"],
            }
        examples.append(example)
    return {
        "started_at": results["started_at"], "finished_at": results["finished_at"],
        "corpus_sha256": results["corpus_sha256"], "repeats": results["repeats"],
        "inventory": corpus["metadata"]["inventory"], "unique_decisions": len(corpus["cases"]),
        "dependency_groups": len(corpus["metadata"]["package_work_groups"]),
        "models": {model: {key: value for key, value in stats.items() if key != "records"}
                   for model, stats in results["models"].items()},
        "examples": examples,
        "interpretation": "Reference-label agreement on a fixed local corpus, not independently verified vulnerability accuracy. All checkpoints missed the card-required trial policy. Keep decisions advisory.",
        "environment": results["environment"],
    }
