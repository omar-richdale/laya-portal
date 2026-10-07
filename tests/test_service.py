"""Exercise lifecycle and queue guarantees without loading large GPU checkpoints."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import threading
from types import SimpleNamespace
import weakref

import pytest
import torch
from fastapi.testclient import TestClient

from laya_portal.app import create_app
from laya_portal.gpu import GPUOnlyAgent
from laya_portal.schemas import BatchRequest, PredictRequest
from laya_portal.service import InferenceService, ServiceError
import laya_portal.service as service_module

KEY = "test-only-key-that-is-long-enough"
Q = {"route": {"type": "choice", "instructions": "Route this", "criteria": {"A": "first", "B": "second"}}}


class FakeRouter:
    def __init__(self):
        self.agents = {}
        self.calls = []
    def route(self, state, questions, model=None):
        return {"model": model or ("multilingual" if any(ord(c)>127 for c in str(state)) else "english"), "reason": "test routing"}
    def attach(self, name, agent):
        assert not self.agents, "The old checkpoint must be removed before attaching a new one"
        self.agents[name] = agent
    def unload(self):
        self.agents.clear()
    def predict(self, **payload):
        if payload["state"] == "OOM":
            raise torch.cuda.OutOfMemoryError("simulated")
        return {"answers": {"route": {"type": "choice", "choice": payload["state"], "answer_confidence": .9}}, "usage": {}, "model": "laya-rl-agent"}
    def predict_batch(self, requests, **kwargs):
        self.calls.append(kwargs)
        return [self.predict(**p) for p in requests]


@pytest.fixture
def service(tmp_path, monkeypatch):
    paths = {}
    for name in ("english", "multilingual", "typed-decisions"):
        path = tmp_path / name
        path.mkdir()
        (path / "model.safetensors").touch()
        paths[name] = path
    monkeypatch.setattr(service_module, "MODEL_DIRS", paths)
    live = weakref.WeakValueDictionary()
    def factory(path):
        assert not live, "Old agent remains alive while another is being loaded"
        agent = SimpleNamespace(device="cuda:0")
        # SimpleNamespace cannot be weak-referenced; use a small owned object instead.
        class FakeAgent:
            device = "cuda:0"
        agent = FakeAgent()
        live[path] = agent
        return agent
    runtime = InferenceService(data_root=tmp_path / "settings", agent_factory=factory, router=FakeRouter())
    runtime._update(ready=True, phase="idle", device="cuda:0")
    return runtime


@pytest.mark.asyncio
async def test_model_override_and_atomic_saved_default(service):
    try:
        await service.set_default("multilingual")
        result = await service.predict(PredictRequest(state="one", questions=Q, model="english"))
        assert result["routing"]["model"] == "english"
        assert service.default_model == "multilingual"
        assert json.loads(service.settings_path.read_text())["model"] == "multilingual"
        result = await service.predict(PredictRequest(state="two", questions=Q))
        assert result["routing"]["model"] == "multilingual"
        reloaded = InferenceService(data_root=service.data_root, router=FakeRouter())
        assert reloaded.default_model == "multilingual"
        await reloaded.close()
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_batch_restores_order_and_microbatch(service):
    try:
        req = BatchRequest(requests=[PredictRequest(state=str(i), questions=Q, model=m) for i,m in enumerate(
            ["english", "multilingual", "english", "typed-decisions"])])
        result = await service.batch(req)
        assert [r["answers"]["route"]["choice"] for r in result["results"]] == ["0","1","2","3"]
        assert all(call["batch_size"] == 2 for call in service.router.calls)
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_oom_is_error_and_unloads_model(service):
    try:
        with pytest.raises(ServiceError) as error:
            await service.predict(PredictRequest(state="OOM", questions=Q))
        assert error.value.code == "gpu_oom"
        assert service._agent is None
        assert service.status()["resident_model"] is None
        assert "CPU inference is disabled" in error.value.message
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_failed_load_preserves_default(service):
    service.agent_factory = lambda _: (_ for _ in ()).throw(RuntimeError("load failed"))
    try:
        with pytest.raises(ServiceError):
            await service.set_default("english")
        assert service.default_model == "auto"
        assert not service.settings_path.exists()
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_queue_cancellation_does_not_free_slot(service):
    gate = threading.Event()
    tasks = [asyncio.create_task(service.submit(gate.wait)) for _ in range(8)]
    try:
        await asyncio.sleep(.1)
        tasks[0].cancel()
        await asyncio.sleep(.02)
        assert service.status()["outstanding_jobs"] == 8
        with pytest.raises(ServiceError) as error:
            await service.submit(lambda: None)
        assert error.value.code == "busy"
    finally:
        gate.set()
        await asyncio.gather(*tasks, return_exceptions=True)
        await service.close()
    assert service.status()["outstanding_jobs"] == 0


def test_gpu_adapter_never_attempts_cpu_retry():
    agent = GPUOnlyAgent.__new__(GPUOnlyAgent)
    agent.device = torch.device("cuda:0")
    agent.dtype = torch.float32
    agent._amp_enabled_for = lambda _: False
    class Tensor:
        shape = (1, 2)
        def to(self, device):
            assert device.type == "cuda"
            return self
    def model(*args):
        raise torch.cuda.OutOfMemoryError("simulated real-forward failure")
    agent.model = model
    batch = {k:Tensor() for k in ("input_ids","attention_mask","marker_pos","marker_mask","qtype")}
    with pytest.raises(torch.cuda.OutOfMemoryError):
        agent._infer(batch)
    assert agent.device.type == "cuda"


@pytest.mark.parametrize("change", [{"state":None},{"max_len":True},{"max_len":32},{"min_confidence":2},
                                   {"questions":{}},{"model":"unknown"},{"extra":"not allowed"}])
def test_request_validation(change):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PredictRequest.model_validate({"state":"test","questions":Q,**change})


def test_auth_json_limits_and_openapi(service):
    app = create_app(service, api_key=KEY, initialize=False)
    with TestClient(app) as client:
        assert client.get("/api/v1/status").status_code == 401
        assert client.post("/mcp/", json={}).status_code == 401
        headers = {"Authorization":"Bearer "+KEY}
        assert client.get("/api/v1/status", headers=headers).status_code == 200
        assert client.get("/openapi.json").json()["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
        assert client.post("/api/v1/predict", headers=headers, json={"state":None,"questions":Q}).status_code == 422
        assert client.post("/api/v1/predict", headers=headers, content='{"state":"a","state":"b"}').status_code == 400
        assert client.post("/api/v1/predict", headers=headers, content=b"x"*(4*1024*1024+1)).status_code == 413
        response = client.post("/api/v1/predict", headers=headers, json={"state":"hello","questions":Q})
        assert response.status_code == 200
        assert response.json()["runtime"]["device"] == "cuda:0"
        assert "Access-Control-Allow-Origin" not in response.headers
