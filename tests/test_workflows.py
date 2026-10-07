"""Advisory responses and benchmark evidence remain authenticated and non-authorizing."""
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from laya_portal.app import create_app
from laya_portal.workflows import advice

KEY = "workflow-test-key-that-is-long-enough"


class Stub:
    def __init__(self):
        self.requests = []
    async def close(self):
        pass
    async def predict(self, request):
        self.requests.append(request)
        return {"model": "laya-rl-agent", "answers": {"decision": {"type": "choice", "choice": "B", "answer_confidence": .6, "low_confidence": True}},
                "routing": {"model": request.model or "english", "reason": "test"}, "usage": {"truncated": False},
                "runtime": {"device": "cuda:0", "elapsed_ms": 1, "load_ms": 0, "revision": "test", "warnings": []}}


def test_workflow_auth_validation_and_advice():
    service = Stub()
    with TestClient(create_app(service, api_key=KEY, initialize=False)) as client:
        assert client.post("/api/v1/workflows/issue_lane", json={"state": "secret"}).status_code == 401
        client.headers["Authorization"] = f"Bearer {KEY}"
        response = client.post("/api/v1/workflows/issue_lane", json={"state": "credential finding", "model": "typed-decisions"})
        assert response.status_code == 200
        result = response.json()
        assert result["advice"] == {"workflow": "issue_lane", "label": "credential_review", "answer_confidence": .6,
                                    "review_required": True, "advisory_only": True, "authorization": False}
        assert service.requests[0].model == "typed-decisions"
        assert service.requests[0].max_len == 512
        assert client.post("/api/v1/workflows/delete_everything", json={"state": "x"}).status_code == 422
        assert client.post("/api/v1/workflows/issue_lane", json={"state": ""}).status_code == 422
        assert client.post("/api/v1/workflows/issue_lane", json={"state": "x", "model": "wrong"}).status_code == 422
        assert len(service.requests) == 1


def test_benchmark_authenticated_and_replayable():
    with TestClient(create_app(Stub(), api_key=KEY, initialize=False)) as client:
        assert client.get("/api/v1/benchmark").status_code == 401
        result = client.get("/api/v1/benchmark", headers={"Authorization": f"Bearer {KEY}"}).json()
        assert result["unique_decisions"] == 247
        assert len(result["examples"]) == 5
        trial = next(e for e in result["examples"] if "GS-018" in e["id"])
        assert trial["expected_label"] == "TEST_BUG"
        assert all(not o["matches_reference"] for o in trial["observations"].values())
        assert "expected" not in trial["prediction"]["state"]
    root = Path(__file__).resolve().parents[1]
    corpus = (root / "docs/benchmark/corpus.json").read_bytes()
    results = json.loads((root / "docs/benchmark/results.json").read_text())
    assert hashlib.sha256(corpus).hexdigest() == results["corpus_sha256"]


def test_truncated_advice_requires_review():
    value = {"answers": {"decision": {"choice": "A", "answer_confidence": .99}}, "usage": {"truncated": True}}
    assert advice("issue_lane", value)["review_required"] is True
