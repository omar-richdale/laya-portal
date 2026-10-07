"""Snapshot requested GitHub issues and QA reports without modifying remote state."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "benchmark" / "sources"
REPOS = ("Richdale-AI/VPN_website", "Richdale-AI/total_guard_vpn_website")
REPORTS = ("20260930-060000-9iy9o", "20260930-071000-9o49u", "20260929-071000-wzuvk")


def issues(repo):
    result = subprocess.run([
        "gh", "issue", "list", "--repo", repo, "--state", "open", "--limit", "1000",
        "--json", "number,title,body,labels,url,createdAt,updatedAt",
    ], capture_output=True, text=True, encoding="utf-8", check=True)
    rows = json.loads(result.stdout)
    (OUT / f"{repo.split('/')[-1]}-issues.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"kind": "issues", "repo": repo, "count": len(rows), "source": f"https://github.com/{repo}/issues"}


def report(run):
    base = f"https://vpnqa.richdalelab.com/reports/{run}"
    results = []
    with httpx.Client(timeout=40, follow_redirects=True) as http:
        for name in ("report.json", "report.md", "index.html"):
            try:
                response = http.get(f"{base}/{name}")
                results.append({"file": name, "status": response.status_code, "bytes": len(response.content)})
                if response.status_code == 200:
                    target = OUT / run
                    target.mkdir(exist_ok=True)
                    (target / name).write_bytes(response.content)
            except httpx.HTTPError as exc:
                results.append({"file": name, "error": type(exc).__name__})
    return {"kind": "report", "run": run, "source": base, "files": results}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(issues, repo) for repo in REPOS] + [pool.submit(report, run) for run in REPORTS]
        records = [future.result() for future in futures]
    manifest = {"fetched_at": datetime.now(timezone.utc).isoformat(), "sources": records}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
