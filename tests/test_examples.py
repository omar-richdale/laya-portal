"""Protect example contracts: independent labels, relative credentials and review gates."""
from copy import deepcopy

import httpx
import pytest

from examples import common
from examples.scenarios import SCENARIOS, alignment_route, injection_route, triage_state
from laya_portal.schemas import PredictRequest


@pytest.mark.parametrize("scenario", SCENARIOS.values(), ids=lambda s: s.name)
def test_fixture_requests_are_valid_and_reference_labels_stay_outside_payload(scenario):
    for case in scenario.cases:
        payload = {
            "model": "english", "state": scenario.prepare_state(case.state),
            "questions": scenario.questions, "min_confidence": 0.8,
        }
        PredictRequest.model_validate(payload)
        assert "expected" not in payload["state"]
        assert "reference_label" not in payload["state"]
        assert case.expected in scenario.questions["decision"]["criteria"]


def test_crosscheck_withholds_supplied_classification_without_mutating_report():
    state = SCENARIOS["triage"].cases[1].state
    before = deepcopy(state)
    assert "classification" not in triage_state(state)["issue"]
    assert state == before
    assert state["issue"]["classification"] == "PRODUCT_BUG"


def test_env_lookup_is_relative_to_example_file_not_working_directory(tmp_path, monkeypatch):
    requested = []

    def values(path):
        requested.append(path)
        return {"LAYA_API_KEY": "synthetic-test-key", "LAYA_PORT": "8765"}

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(common, "dotenv_values", values)
    client = common.Client()
    try:
        assert requested == [common.ROOT / ".env"]
        assert client.base_url == "http://127.0.0.1:8765"
        assert client.http.headers["Authorization"] == "Bearer synthetic-test-key"
    finally:
        client.close()


@pytest.mark.parametrize("status,code,retries", [(503, "busy", 3), (503, "gpu_oom", 1), (401, "unauthorized", 1)])
def test_client_retries_only_busy_and_does_not_expose_credentials(monkeypatch, status, code, retries):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"error": {"code": code, "message": "fixture failure"}})

    client = common.Client.__new__(common.Client)
    client.base_url = "http://test"
    client.http = httpx.Client(base_url=client.base_url, transport=httpx.MockTransport(handler),
                               headers={"Authorization": "Bearer synthetic-secret"})
    monkeypatch.setattr(common.time, "sleep", lambda _: None)
    try:
        with pytest.raises(common.ExampleError) as error:
            client.request("POST", "/api/v1/predict", json={})
        assert len(calls) == retries
        assert "synthetic-secret" not in str(error.value)
    finally:
        client.close()


@pytest.mark.parametrize("index", [2, 5])
def test_explicit_path_and_tool_rules_dominate_a_confident_allow(index):
    case = SCENARIOS["alignment"].cases[index]
    answer = {"choice": "A", "answer_confidence": 0.99}
    assert alignment_route(case, answer, False).startswith("BLOCK")


def test_uncertain_safe_predictions_do_not_allow_action_or_trust_evidence():
    assert alignment_route(SCENARIOS["alignment"].cases[0], {"choice": "A"}, True).startswith("Hold")
    assert injection_route(SCENARIOS["injection"].cases[0], {"choice": "B"}, True).startswith("Hold")
