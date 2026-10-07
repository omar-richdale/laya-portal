"""Measure long-context requests and confirm truncation/abstention metadata on real CUDA."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
import requests

base = f"http://127.0.0.1:{os.environ.get('LAYA_PORT','8000')}"
headers = {"Authorization":"Bearer "+os.environ["LAYA_API_KEY"]}
questions = {"topic":{"type":"choice","instructions":"What is this document about?",
                     "criteria":{"billing":"payments and refunds","technical":"software bugs","other":"anything else"}}}
report = {"contexts":[]}

for budget in (1024,4096,8192):
    response = requests.post(base+"/api/v1/predict", headers=headers, timeout=180, json={
        "state":"The customer requests a refund for a duplicate payment. "*(budget//12),
        "questions":questions,"model":"multilingual","max_len":budget,"min_confidence":1,
    })
    result = response.json()
    if response.status_code == 503 and result["error"]["code"] == "gpu_oom":
        report["contexts"].append({"max_len":budget,"gpu_oom":True,"cpu_inference":False})
    else:
        response.raise_for_status()
        assert result["runtime"]["device"] == "cuda:0"
        report["contexts"].append({"max_len":budget,"elapsed_ms":result["runtime"]["elapsed_ms"],
                                  "usage":result["usage"],"low_confidence":result["answers"]["topic"].get("low_confidence",False)})
    print(json.dumps(report["contexts"][-1]),flush=True)

response = requests.post(base+"/api/v1/predict", headers=headers, timeout=180, json={
    "state":"Please refund the duplicate payment. "*300,"questions":questions,"model":"english",
})
response.raise_for_status()
truncated=response.json()
assert truncated["usage"]["truncated"]
assert any("truncated" in w for w in truncated["runtime"]["warnings"])
report["truncation_reported"] = True
report["gpu"] = requests.get(base+"/api/v1/status",headers=headers).json()["gpu"]
(ROOT/"data"/"verification"/"context-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
