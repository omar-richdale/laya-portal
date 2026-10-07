"""Build investigation queues from the frozen inventory; never mutate GitHub issues.

Scanner/package metadata takes precedence over model guesses. Laya is useful for
unstructured fallback/topic advice, not rediscovering an existing scanner label.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def plan():
    corpus = json.loads((ROOT / "docs/benchmark/corpus.json").read_text(encoding="utf-8"))
    cases = [case for case in corpus["cases"] if case["workflow"] == "issue_lane"]
    lanes = {
        "dependency_update": {"issues": [], "contract": "Separate from current Bugsmith repair policy. Inspect installed dependency paths, affected ranges and fixed versions before proposing an update."},
        "credential_review": {"issues": [], "contract": "Owner confirms exposure and rotation scope. Never place credential values in agent context."},
        "source_review": {"issues": [], "contract": "Reproduce with pinned source, validate impact, then create a bounded repair with regression tests."},
        "business_report": {"issues": [], "contract": "Operator/business intake; not an automatic code repair."},
    }
    labels = {"A": "dependency_update", "B": "credential_review", "C": "source_review", "D": "business_report"}
    for case in cases:
        lanes[labels[case["expected"]]]["issues"].append({"id": case["id"], "url": case["source"], "basis": case["reference_basis"]})
    output = {"snapshot": corpus["metadata"]["created_at"], "mode": "read-only investigation plan",
              "priority_policy": "Preserve Sift's source priorities and issue lifecycle. No findings suppressed or closed.",
              "lanes": lanes, "dependency_package_groups": corpus["metadata"]["package_work_groups"],
              "qa_actions": [
                  {"case": "GhostShield GS-018", "action": "Apply explicit card-required contract to the QA profile; rerun through approved QA workflow."},
                  {"case": "TotalGuard GS-027 / GS-028", "action": "Keep rejection-after-signout assertions. Reproduce app-token revocation independently on the report's deployed revision."},
                  {"case": "GhostShield GS-015 / GS-027", "action": "Inspect overlay and request evidence; root cause is not established by a timeout."},
              ]}
    destination = ROOT / "docs/benchmark/backlog-plan.json"
    destination.write_text(json.dumps(output, indent=2), encoding="utf-8")
    for name, lane in lanes.items():
        print(f"{name}: {len(lane['issues'])} issues")
    print(f"Dependency groups: {len(output['dependency_package_groups'])}; no vulnerabilities resolved by grouping.")
    print(destination)


if __name__ == "__main__":
    plan()
