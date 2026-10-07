"""Metadata must be readable without GPU work and must match hosted constraints."""
import json

from fastapi.testclient import TestClient
import pytest

from laya_portal.app import create_app
from laya_portal.config import MODEL_INFO, MODEL_REVISION, ROOT
from laya_portal.mcp_api import build_mcp
from laya_portal.model_catalog import metadata
from laya_portal.schemas import PredictRequest

KEY = "metadata-test-key-that-is-long-enough"


class NoInference:
    async def close(self):
        pass

    async def predict(self, request):
        raise AssertionError("Reading metadata must not start inference")


def test_public_and_authenticated_discovery():
    with TestClient(create_app(NoInference(), api_key=KEY, initialize=False)) as client:
        catalog = client.get("/models.json")
        assert catalog.status_code == 200
        assert len(catalog.json()["models"]) == 3
        assert client.get("/docs/models.md").status_code == 200
        assert "Model capability guide" in client.get("/llms.txt").text
        assert client.get("/api/v1/model-metadata").status_code == 401
        assert client.get("/api/v1/models/english/metadata").status_code == 401
        client.headers["Authorization"] = f"Bearer {KEY}"
        assert client.get("/api/v1/model-metadata").json() == catalog.json()
        single = client.get("/api/v1/models/typed-decisions/metadata").json()
        assert [m["id"] for m in single["models"]] == ["typed-decisions"]
        assert client.get("/api/v1/models/auto/metadata").status_code == 422
        assert client.get("/api/v1/models/unknown/metadata").status_code == 422
        paths = client.get("/openapi.json").json()["paths"]
        assert paths["/api/v1/model-metadata"]["get"]["security"]
        assert "Access-Control-Allow-Origin" not in catalog.headers


@pytest.mark.parametrize("name", list(MODEL_INFO))
def test_catalog_limits_evidence_and_examples(name):
    catalog = metadata(name)
    m = catalog.models[0]
    config_path = ROOT / "models" / MODEL_REVISION / ("" if name == "english" else name) / "rl_agent_config.json"
    assert m["identity"]["revision"] == MODEL_REVISION
    assert m["tokens"]["default_total"] == MODEL_INFO[name]["context"]
    assert m["tokens"]["default_question"] == MODEL_INFO[name]["head"]
    # A clean checkout can test discovery without downloading gigabytes of weights.
    if config_path.exists():
        config = json.loads(config_path.read_text())
        assert m["tokens"]["default_total"] == config["max_len"]
        assert m["tokens"]["default_question"] == config["head_max_len"]
    assert m["tokens"]["hosted_max_total"] == (8192 if name == "multilingual" else MODEL_INFO[name]["context"])
    assert m["tokens"]["output_tokens"] == 0
    request = PredictRequest.model_validate(m["example"])
    assert request.model == name
    assert m["local_evidence"]["quality"]["issue_lane"]["count"] == 233
    assert m["local_evidence"]["max_len"] == 512
    assert set(m["source_ids"]) <= {s["id"] for s in catalog.sources}


def test_returned_catalog_cannot_mutate_shared_source():
    changed = metadata("english")
    changed.models[0]["tokens"]["hosted_max_total"] = 999999
    assert metadata("english").models[0]["tokens"]["hosted_max_total"] == 512
    assert len(metadata().models) == 3


@pytest.mark.asyncio
async def test_mcp_metadata_is_structured_without_inference():
    server, _ = build_mcp(NoInference())
    result = await server.call_tool("laya_model_info", {"model": "multilingual"})
    assert not result.is_error
    assert result.structured_content["models"][0]["id"] == "multilingual"
    resources = await server.list_resources()
    assert {"laya://models", "laya://model-guide"} <= {str(r.uri) for r in resources}
