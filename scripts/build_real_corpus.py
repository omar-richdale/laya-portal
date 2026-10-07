"""Build redacted, fixed real-data decisions with separately documented references."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "benchmark" / "sources"
OUT = ROOT / "docs" / "benchmark"


def clean(text, limit=750):
    text = re.sub(r"\x1b\[[0-9;]*m", "", str(text or ""))
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[redacted-email]", text)
    text = re.sub(r"\b(?:gh[opusr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,})\b", "[redacted-token]", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def field(body, name):
    match = re.search(r"\*\*" + re.escape(name) + r"\*\*\s*\|\s*([^|\n]+)", body)
    return match.group(1).strip().strip("`") if match else None


def build():
    cases, inventory, packages = [], {}, defaultdict(list)
    for name in ("VPN_website", "total_guard_vpn_website"):
        rows = json.loads((SOURCES / f"{name}-issues.json").read_text(encoding="utf-8"))
        counts = Counter()
        for row in rows:
            labels = [label["name"] for label in row["labels"]]
            if any(label.startswith("cve:") for label in labels):
                expected, category = "A", "dependency"
            elif "sift:secret" in labels or "detected-google-gcm-service-account" in row["title"]:
                expected, category = "B", "credential"
            elif "sift:sast" in labels or "sift:agent_review" in labels:
                expected, category = "C", "code"
            else:
                expected, category = "D", "business"
            # Secret scanner metadata describes a suspicion, not a confirmed secret.
            # Never load the repository's flagged file or a scanner's raw secret here.
            state = {"title": clean(row["title"], 280), "description": clean(row["body"], 550)}
            package = field(row["body"], "Package")
            if package:
                state["package"] = package
                packages[f"{name}:{package.rsplit(' ', 1)[0]}"] .append(row["number"])
            identifier = f"{name}#{row['number']}"
            cases.append({"id": identifier, "workflow": "issue_lane", "source": row["url"],
                          "state": state, "expected": expected,
                          "reference_basis": "Sift issue metadata and manually reviewed routing taxonomy; not vulnerability truth", "category": category})
            counts[category] += 1
            if "sift:sast" in labels or "sift:agent_review" in labels:
                title = row["title"].lower()
                topic = "A" if "jwt_secret" in title else "B" if any(token in title for token in ("logged", "secret", "service account")) else "C"
                cases.append({"id": identifier + ":specialist", "workflow": "security_specialist", "source": row["url"],
                              "state": state, "expected": topic,
                              "reference_basis": "Manual topic label from finding title/rule, not exploit confirmation", "category": "code_topic"})
        inventory[name] = {"open_issues": len(rows), "categories": dict(counts)}

    for run in ("20260930-060000-9iy9o", "20260930-071000-9o49u", "20260929-071000-wzuvk"):
        report = json.loads((SOURCES / run / "report.json").read_text(encoding="utf-8"))
        for issue in (report.get("assessment") or {}).get("issues", []):
            spec = issue["specId"]
            tests = [test for test in report["tests"] if test.get("specId") == spec and test["outcome"] in ("failed", "timedOut")]
            test = tests[0] if tests else {}
            investigation = next((inv for inv in report.get("investigations", []) if inv.get("specId") == spec), {})
            if report["site"] == "ghostshield" and spec == "GS-018":
                expected = "TEST_BUG"
                basis = "User-confirmed card requirement; website trial/start code; QA profile still asserts an automatic no-card trial"
                contract = "Current approved GhostShield policy: a credit card must be saved before a trial starts. Signup alone does not grant a trial. The test still expected an automatic trial."
            elif report["site"] == "ghostshield":
                expected = "UNKNOWN"
                basis = "Evidence audit: overlay interception or a request timeout alone does not establish a root cause under the changed onboarding flow"
                contract = "Card-required onboarding is intentional. A visible modal may block background clicks. Timeouts alone do not prove a website defect."
            else:
                expected = "PRODUCT_BUG"
                basis = "QA contract requires rejection after sign-out; captured assertion received valid=true (reference is evidence-based, not independent exploit validation)"
                contract = "A mobile or desktop token must be rejected after its device signs out. Web-session 401 responses alone do not prove app-token revocation."
            evidence = clean(" ".join(investigation.get("evidence", [])[:3]), 380)
            state = {"site": report["site"], "test": clean(test.get("title") or issue["whatItChecks"], 120),
                     "trusted_contract": contract, "observed_error": clean((test.get("errors") or [""])[0], 300),
                     "evidence": evidence}
            cases.append({"id": f"{run}:{spec}", "workflow": "qa_cause", "source": f"https://vpnqa.richdalelab.com/reports/{run}/report.md",
                          "state": state, "expected": expected, "source_classification": issue["classification"],
                          "reference_basis": basis, "category": "qa_failure"})

    metadata = {"created_at": datetime.now(timezone.utc).isoformat(), "inventory": inventory,
                "package_work_groups": {key: values for key, values in sorted(packages.items())},
                "unique_source_issues": sum(v["open_issues"] for v in inventory.values()),
                "cases_by_workflow": dict(Counter(case["workflow"] for case in cases)),
                "notes": ["All inputs originate from fetched real issues or specified QA reports; no generated attacks are counted.",
                          "Metadata-routing labels do not prove vulnerabilities; QA references are a small evidence audit.",
                          "Source labels, issue tags, reference_basis and expected are excluded from model state.",
                          "Two source-code credential detections are intentionally assigned to credential review rather than ordinary code repair."]}
    result = {"metadata": metadata, "cases": cases}
    encoded = json.dumps(result, indent=2, ensure_ascii=False).encode()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "corpus.json").write_bytes(encoded)
    (OUT / "corpus.sha256").write_text(hashlib.sha256(encoded).hexdigest() + "  corpus.json\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    build()
