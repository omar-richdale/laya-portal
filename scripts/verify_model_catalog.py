"""Check the running metadata endpoints and MCP discovery without GPU inference."""
import asyncio
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from examples.common import Client as HttpClient
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


async def main():
    http = HttpClient()
    try:
        before = http.request("GET", "/api/v1/status")
        public = http.http.get("/models.json")
        public.raise_for_status()
        catalog = public.json()
        assert catalog == http.request("GET", "/api/v1/model-metadata")
        unauthorized = http.http.get("/api/v1/model-metadata", headers={"Authorization": ""})
        assert unauthorized.status_code == 401
        assert http.http.get("/docs/models.md").status_code == 200
        assert http.http.get("/model-guide").status_code == 200
        for model in catalog["models"]:
            single = http.request("GET", model["metadata_url"])
            assert single["models"] == [model]
        async with httpx2.AsyncClient(headers={"Authorization": http.http.headers["Authorization"]}, timeout=30) as transport_http:
            async with Client(streamable_http_client(http.base_url + "/mcp/", http_client=transport_http), read_timeout_seconds=30) as mcp:
                tool = await mcp.call_tool("laya_model_info", {"model": "multilingual"})
                assert not tool.is_error
                assert tool.structured_content["models"][0]["tokens"]["hosted_max_total"] == 8192
                all_models = await mcp.call_tool("laya_model_info")
                assert all_models.structured_content == catalog
                resource = await mcp.read_resource("laya://models")
                assert json.loads(resource.contents[0].text) == catalog
                guide = await mcp.read_resource("laya://model-guide")
                assert "Hosted Laya model guide" in guide.contents[0].text
                invalid = await mcp.call_tool("laya_model_info", {"model": "auto"})
                assert invalid.is_error
        after = http.request("GET", "/api/v1/status")
        assert before["resident_model"] == after["resident_model"]
        assert before["default_model"] == after["default_model"]
        assert before["gpu"]["allocated_bytes"] == after["gpu"]["allocated_bytes"]
        report = {"passed": True, "catalog_schema": catalog["schema_version"], "reviewed_at": catalog["reviewed_at"], "models": len(catalog["models"]), "public_markdown_json": True, "authenticated_rest": True, "unauthorized_rejected": True, "mcp_structured_tool_and_resources": True, "resident_model_unchanged": before["resident_model"], "saved_default_unchanged": before["default_model"], "gpu_allocation_unchanged": True}
        destination = ROOT / "data/verification/model-catalog-report.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
    finally:
        http.close()


if __name__ == "__main__":
    asyncio.run(main())
