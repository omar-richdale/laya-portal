"""The portal's replay catalog must match the measured study without running GPU work."""
from collections import Counter
import hashlib
import json

from fastapi.testclient import TestClient

from laya_portal.app import create_app
from laya_portal.config import ROOT
from laya_portal.decision_suite import catalog
from laya_portal.schemas import PredictRequest

KEY = "decision-suite-test-key-long-enough"


class ReadOnlyService:
    async def close(self):
        pass


def test_catalog_authentication_and_no_inference_dependency():
    with TestClient(create_app(ReadOnlyService(), api_key=KEY, initialize=False)) as client:
        assert client.get("/api/v1/decision-suite").status_code == 401
        response = client.get("/api/v1/decision-suite", headers={"Authorization": f"Bearer {KEY}"})
        assert response.status_code == 200
        value = response.json()
        assert len(value["tasks"]) == 6
        assert sum(len(t["cases"]) for t in value["tasks"]) == 130
        assert len(value["baseline"]["records"]) == 390


def test_replays_match_frozen_cli_fixtures_and_withhold_references():
    from examples.everyday_decisions import TASKS, payload
    value = catalog()
    canonical = json.dumps(TASKS, sort_keys=True, ensure_ascii=False).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == value["fixture_sha256"]
    references = {}
    for task in value["tasks"]:
        counts = Counter(c["expected"] for c in task["cases"])
        assert len(set(counts.values())) == 1
        for case in task["cases"]:
            expected = PredictRequest.model_validate(payload(TASKS[task["id"]], case["prompt"], "english"))
            actual = PredictRequest.model_validate({**case["prediction"], "model": "english"})
            assert actual == expected
            assert "expected" not in case["prediction"]
            assert set(actual.state) == {"policy", "request"}
            references[case["id"]] = case["expected"]
    records = value["baseline"]["records"]
    ordered_requests = [c["prediction"] for t in value["tasks"] for c in t["cases"]]
    request_digest = hashlib.sha256(json.dumps(ordered_requests, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    assert request_digest == value["request_sha256"] == value["baseline"]["request_sha256"]
    assert list(value["tasks"][0]["criteria"]) == ["fast", "reasoning", "coding", "image", "video"]
    assert len({(r["model"], r["case_id"]) for r in records}) == 390
    for model, matches in (("english", 89), ("multilingual", 65), ("typed-decisions", 99)):
        rows = [r for r in records if r["model"] == model]
        assert len(rows) == 130
        assert sum(r["choice"] == references[r["case_id"]] for r in rows) == matches
        assert all(r["device"] == "cuda:0" and r["valid"] for r in rows)
    assert catalog()["fixture_sha256"] == json.loads((ROOT / "docs/benchmark/everyday-baseline.json").read_text(encoding="utf-8"))["fixture_sha256"]
