"""Verify actual REST/MCP/LAN behavior against the running on-demand service."""
import asyncio
import json
import os
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
import httpx
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

BASE = f"http://127.0.0.1:{os.environ.get('LAYA_PORT', '8000')}"
HEADERS = {"Authorization": "Bearer " + os.environ["LAYA_API_KEY"]}
REQUEST = {"state": "Please refund the duplicate payment.", "model": "english", "questions": {
    "department": {"type": "choice", "instructions": "Which department should handle this?",
                   "criteria": {"billing": "payments and refunds", "technical": "bugs and outages"}}}}


async def main():
    report = {}
    async with httpx.AsyncClient(base_url=BASE, headers=HEADERS, timeout=180) as http:
        assert (await http.get("/api/v1/status", headers={"Authorization":"Bearer wrong"})).status_code == 401
        assert (await http.post("/mcp/", headers={"Authorization":"Bearer wrong"}, json={})).status_code == 401
        for path in ("/", "/llms.txt", "/docs/agents.md", "/docs/api.md", "/docs/architecture.md", "/docs/operations.md", "/docs/development.md", "/openapi.json", "/docs", "/api-docs/swagger-ui-bundle.js", "/credits.txt"):
            response = await http.get(path)
            assert response.status_code == 200, (path, response.status_code)
        rest = await http.post("/api/v1/predict", json=REQUEST)
        rest.raise_for_status()
        result = rest.json()
        assert result["runtime"]["device"] == "cuda:0"
        report["rest"] = {"elapsed_ms": result["runtime"]["elapsed_ms"], "device": result["runtime"]["device"]}
        assert (await http.post("/api/v1/predict", json={**REQUEST, "model":"unknown"})).status_code == 422
        assert (await http.post("/api/v1/predict", json={**REQUEST, "max_len":8192})).status_code == 422
        old = (await http.get("/api/v1/models")).json()["default_model"]
        try:
            changed = await http.put("/api/v1/settings/model", json={"model":"multilingual"})
            changed.raise_for_status()
            await http.post("/api/v1/predict", json=REQUEST)
            assert (await http.get("/api/v1/models")).json()["default_model"] == "multilingual"
        finally:
            (await http.put("/api/v1/settings/model", json={"model":old})).raise_for_status()
        batch = await http.post("/api/v1/predict/batch", json={"requests":[REQUEST,{**REQUEST,"model":"multilingual"},REQUEST],"batch_size":2})
        batch.raise_for_status()
        assert [r["routing"]["model"] for r in batch.json()["results"]] == ["english","multilingual","english"]
        report["rest_batch"] = {"ordered":True,"count":3}
        # Warm English for a direct REST/MCP comparison of the same GPU service.
        result = (await http.post("/api/v1/predict", json=REQUEST)).json()
        async with httpx2.AsyncClient(headers=HEADERS, timeout=180) as mcp_http:
            transport = streamable_http_client(BASE+"/mcp/", http_client=mcp_http)
            async with Client(transport, read_timeout_seconds=180) as client:
                tools = await client.list_tools()
                assert {t.name for t in tools.tools} == {"laya_predict","laya_predict_batch","laya_models","laya_status","laya_set_default_model","laya_model_info"}
                resource = await client.read_resource("laya://integration")
                assert resource.contents
                mcp_result = await client.call_tool("laya_predict", {"request":REQUEST})
                assert not mcp_result.is_error, mcp_result.content
                assert mcp_result.structured_content["answers"] == result["answers"]
                mcp_status = await client.call_tool("laya_status")
                assert mcp_status.structured_content["resident_model"] == "english"
                mcp_batch = await client.call_tool("laya_predict_batch", {"request":{"requests":[REQUEST,REQUEST],"batch_size":1}})
                assert not mcp_batch.is_error
                assert len(mcp_batch.structured_content["results"]) == 2
                failure = await client.call_tool("laya_predict", {"request":{**REQUEST,"max_len":8192}})
                assert failure.is_error
                report["mcp"] = {"tools":len(tools.tools),"resource":True,"reference_http_equal":True,"batch":True,"errors":True}
        evil = await http.post("/mcp/", headers={"Origin":"http://evil.example"}, json={"jsonrpc":"2.0","id":1,"method":"initialize","params":{}})
        assert evil.status_code == 403
        for address in socket.gethostbyname_ex(socket.gethostname())[2]:
            if not address.startswith("127."):
                try:
                    lan = await http.get(f"http://{address}:{os.environ.get('LAYA_PORT','8000')}/api/v1/status")
                    report.setdefault("lan", []).append({"address":address,"status":lan.status_code})
                    assert lan.status_code == 200
                except httpx.RequestError as exc:
                    report.setdefault("lan", []).append({"address":address,"error":type(exc).__name__})
        status = (await http.get("/api/v1/status")).json()
        report["gpu"] = status["gpu"]
        report["passed"] = True
    target = ROOT / "data" / "verification" / "http-report.json"
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
