"""Save checkout provenance and portable review patches without staging or pushing."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SIBLINGS = ROOT.parent / "Agentic-production"
OUT = ROOT / "docs/benchmark"


def git(repo, *args):
    return subprocess.check_output(["git", "-c", "color.ui=false", "-C", str(repo), *args])


names = ("sift", "vpn-bugsmith", "QA_Web_Testing_Agent", "VPN_website", "total_guard_vpn_website")
provenance = {"recorded_at": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
              "platform": platform.platform(), "repositories": {
                  name: {"path": str(SIBLINGS / name), "commit": git(SIBLINGS / name, "rev-parse", "HEAD").decode().strip()}
                  for name in names},
              "driver_version": subprocess.check_output(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], text=True).strip(),
              "qa_revisions": {}}
for run in ("20260930-060000-9iy9o", "20260930-071000-9o49u", "20260929-071000-wzuvk"):
    report = json.loads((ROOT / f"data/benchmark/sources/{run}/report.json").read_text(encoding="utf-8"))
    provenance["qa_revisions"][run] = {k: v for k, v in (report.get("sourceRevision") or {}).items()
                                       if k in ("repository", "commitSha", "commitRef", "resolvedRevision", "deploymentId", "source")}
(OUT / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
targets = {
    "sift": [".gitattributes", "deploy/reviewer/sift_reviewer/engine.py", "deploy/reviewer/sift_reviewer/system_one.py",
             "deploy/reviewer/tests/test_suppressions.py", "docs/system-one-advice.md"],
    "vpn-bugsmith": ["src/fixer/triage.py", "src/fixer/pipeline.py", "src/fixer/system_one.py",
                     "tests/fixer/test_triage.py", "docs/fixer/system-one-advice.md"],
    "QA_Web_Testing_Agent": ["src/llm/systemOne.ts", "src/llm/systemOne.test.ts", "src/run.ts", "src/report/model.ts",
                            "src/sites/ghostshield.ts", "src/tests/trial-redeem.spec.ts", "scripts/replay-system-one.ts", "docs/system-one-advice.md"],
}
patches = OUT / "patches"
patches.mkdir(exist_ok=True)
for name, paths in targets.items():
    repo = SIBLINGS / name
    patch = git(repo, "diff", "--binary", "--", *paths)
    tracked = set(git(repo, "ls-files").decode().splitlines())
    for rel in paths:
        if rel in tracked:
            continue
        raw = (repo / rel).read_text(encoding="utf-8")
        lines = raw.splitlines()
        part = f"diff --git a/{rel} b/{rel}\nnew file mode 100644\n--- /dev/null\n+++ b/{rel}\n@@ -0,0 +1,{len(lines)} @@\n"
        part += "".join("+" + line + "\n" for line in lines)
        patch += part.encode()
    path = patches / f"{name}.patch"
    path.write_bytes(patch)
    # Check the packet describes the applied local changes; this never applies it.
    subprocess.run(["git", "-C", str(repo), "apply", "--reverse", "--check", str(path)], check=True, capture_output=True)
    print(name, hashlib.sha256(patch).hexdigest())
