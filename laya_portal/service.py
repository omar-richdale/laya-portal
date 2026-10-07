"""Own model lifecycle and queue all GPU work in one thread shared by REST/MCP."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from importlib.metadata import version
import json
import logging
from pathlib import Path
import threading
import time
import warnings
from typing import Any

from .config import DATA_ROOT, MAX_JOBS, MODEL_DIRS, MODEL_INFO, MODEL_REVISION
from .schemas import BatchRequest, PredictRequest

log = logging.getLogger(__name__)


class ServiceError(Exception):
    def __init__(self, code: str, message: str, status: int = 503):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


class InferenceService:
    def __init__(self, *, data_root: Path = DATA_ROOT, agent_factory=None, router=None):
        self.data_root = data_root
        self.settings_path = data_root / "settings.json"
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="laya-gpu")
        self._pending = 0
        self._closed = False
        self._agent = None
        self._resident = None
        self.agent_factory = agent_factory
        self.router = router
        self._snapshot = {"ready": False, "phase": "starting", "resident_model": None, "device": None,
                          "last_error": None, "gpu": None, "load_ms": None, "checkpoint_warnings": []}
        self.default_model = "auto"
        if self.settings_path.exists():
            saved = json.loads(self.settings_path.read_text(encoding="utf-8"))
            self.default_model = saved["model"]
            if self.default_model not in ("auto", *MODEL_DIRS):
                raise ValueError("Invalid model in data/settings.json")

    def _update(self, **kwargs):
        with self._lock:
            self._snapshot.update(kwargs)

    async def submit(self, fn, *args):
        """Admission slots remain occupied until actual work ends, even if a client disconnects."""
        with self._lock:
            if self._closed:
                raise ServiceError("stopping", "Service is shutting down")
            if self._pending >= MAX_JOBS:
                raise ServiceError("busy", "Inference queue is full; retry later")
            self._pending += 1
            try:
                future = self._executor.submit(fn, *args)
            except Exception:
                self._pending -= 1
                raise

        def released(_):
            with self._lock:
                self._pending -= 1
        future.add_done_callback(released)
        return await asyncio.shield(asyncio.wrap_future(future))

    async def start(self):
        await self.submit(self._initialize)

    def _initialize(self):
        import torch
        from laya import Router
        from .gpu import GPUOnlyAgent
        if not torch.cuda.is_available():
            raise ServiceError("cuda_unavailable", "CUDA is unavailable. Run setup.ps1; CPU inference is disabled.")
        probe = torch.ones(1, device="cuda:0")
        torch.cuda.synchronize()
        del probe
        self.router = self.router or Router(device="cuda:0", max_loaded=1, preload=False, auto_task_detection=False)
        self.agent_factory = self.agent_factory or GPUOnlyAgent
        self._update(ready=True, phase="idle", device="cuda:0")
        self._memory()
        if self.default_model != "auto":
            self._ensure_model(self.default_model)

    def _memory(self):
        if self.agent_factory is None:
            return
        import torch
        if torch.cuda.is_available():
            free, total = torch.cuda.mem_get_info()
            self._update(gpu={"name": torch.cuda.get_device_name(0), "free_bytes": free, "total_bytes": total,
                              "allocated_bytes": torch.cuda.memory_allocated(), "reserved_bytes": torch.cuda.memory_reserved(),
                              "peak_allocated_bytes": torch.cuda.max_memory_allocated()})

    def _unload(self):
        # Clear both owners before the next allocation; Router evicts after loading by default.
        self._agent = None
        self._resident = None
        if self.router is not None:
            self.router.unload()
        self._update(resident_model=None)

    def _ensure_model(self, name):
        if name == self._resident:
            return
        self._update(phase="loading", loading_model=name)
        self._unload()
        started = time.perf_counter()
        if not (MODEL_DIRS[name] / "model.safetensors").exists():
            raise ServiceError("model_missing", f"Checkpoint {name} is not downloaded. Run setup.ps1.")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RuntimeWarning)
            agent = self.agent_factory(str(MODEL_DIRS[name]))
        checkpoint_warnings = [str(w.message) for w in caught]
        for warning in checkpoint_warnings:
            log.warning("Checkpoint %s: %s", name, warning)
        if str(agent.device) not in ("cuda", "cuda:0"):
            raise ServiceError("gpu_load_failed", "Checkpoint is not on CUDA; CPU inference is disabled")
        self._agent = agent
        self.router.attach(name, agent)
        self._resident = name
        self._update(resident_model=name, load_ms=round((time.perf_counter() - started) * 1000, 2), loading_model=None,
                     checkpoint_warnings=checkpoint_warnings)
        self._memory()

    def status(self):
        with self._lock:
            return {**deepcopy(self._snapshot), "default_model": self.default_model, "outstanding_jobs": self._pending,
                    "max_jobs": MAX_JOBS, "revision": MODEL_REVISION,
                    "versions": {p: version(p) for p in ("laya", "torch", "transformers", "mcp")}}

    def models(self):
        status = self.status()
        return {"default_model": status["default_model"], "resident_model": status["resident_model"],
                "models": [{"id": name, **info, "downloaded": (MODEL_DIRS[name] / "model.safetensors").exists(),
                            "resident": name == status["resident_model"], "revision": MODEL_REVISION,
                            "metadata_url": f"/api/v1/models/{name}/metadata", "guide_url": f"/model-guide#{name}"}
                           for name, info in MODEL_INFO.items()]}

    def _selection(self, req: PredictRequest, default):
        chosen = req.model or default
        questions = {key: q.model_dump(exclude_none=True) for key, q in req.questions.items()}
        route = self.router.route(req.state, questions, model=None if chosen == "auto" else chosen)
        name = route["model"]
        budget = req.max_len or MODEL_INFO[name]["context"]
        head = req.head_max_len or MODEL_INFO[name]["head"]
        if name != "multilingual" and budget > MODEL_INFO[name]["context"]:
            raise ServiceError("invalid_budget", f"{name} supports max_len up to {MODEL_INFO[name]['context']} in this service", 422)
        if head >= budget - 8:
            raise ServiceError("invalid_budget", "head_max_len must leave at least 8 tokens for state", 422)
        return name, questions, route, budget, head

    def _payload(self, req, default):
        name, questions, route, budget, head = self._selection(req, default)
        self._ensure_model(name)
        payload = {"state": req.state, "questions": questions, "model": name, "max_len": budget, "head_max_len": head}
        return payload, route, []

    def _decorate(self, result, route, warnings, started):
        if self._snapshot.get("checkpoint_warnings"):
            warnings.append("Calibration notice: this checkpoint has invalid stored temperatures for some option counts. The reference runtime corrected them; validate affected confidence values on your data. Details are in Models & GPU.")
        # Upstream records actual truncation per question; an estimate can falsely flag short heads.
        usage = result.get("usage", {})
        if usage.get("truncated"):
            warnings.append(f"Input was truncated: {usage.get('state_tokens_dropped', 0)} state tokens dropped. See usage.truncated_questions.")
        if usage.get("options"):
            warnings.append("Some options share tokens after the question budget was applied. Increase head_max_len or reduce options.")
        result["routing"] = dict(route)
        result["runtime"] = {"device": str(self._agent.device), "revision": MODEL_REVISION,
                             "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                             "load_ms": self._snapshot["load_ms"], "warnings": warnings}
        return result

    def _handle_error(self, exc):
        import torch
        if isinstance(exc, ServiceError):
            error = exc
        elif isinstance(exc, torch.cuda.OutOfMemoryError):
            self._unload()
            torch.cuda.empty_cache()
            error = ServiceError("gpu_oom", "GPU memory exhausted. Reduce context, question count or batch size; CPU inference is disabled.")
        elif isinstance(exc, (ValueError, TypeError)):
            error = ServiceError("invalid_request", str(exc), 422)
        else:
            log.exception("Laya runtime failure")
            self._unload()
            error = ServiceError("inference_failed", "GPU inference failed. See the local service log.")
        self._update(last_error={"code": error.code, "message": error.message})
        return error

    async def predict(self, req):
        with self._lock:
            default = self.default_model
        return await self.submit(self._predict, req, default)

    def _predict(self, req, default):
        started = time.perf_counter()
        try:
            # Resolve all budgets before changing GPU state.
            self._selection(req, default)
            payload, route, warnings = self._payload(req, default)
            self._update(phase="inferencing", last_error=None)
            result = self.router.predict(**payload, min_confidence=req.min_confidence)
            return self._decorate(result, route, warnings, started)
        except Exception as exc:
            raise self._handle_error(exc) from exc
        finally:
            self._update(phase="idle", loading_model=None)
            self._memory()

    async def batch(self, req: BatchRequest):
        with self._lock:
            default = self.default_model
        return await self.submit(self._batch, req, default)

    def _batch(self, req, default):
        started = time.perf_counter()
        try:
            groups = {}
            for index, item in enumerate(req.requests):
                name, *_ = self._selection(item, default)
                # Per-item abstention cannot leak into another item's schema group.
                groups.setdefault((name, item.min_confidence), []).append((index, item))
            results: list[Any] = [None] * len(req.requests)
            self._update(last_error=None)
            for entries in groups.values():
                built = [self._payload(item, default) for _, item in entries]
                self._update(phase="inferencing")
                outputs = self.router.predict_batch([p for p, _, _ in built], batch_size=req.batch_size,
                                                    sort_by_length=req.sort_by_length,
                                                    min_confidence=entries[0][1].min_confidence)
                for (index, _), result, (_, route, warnings) in zip(entries, outputs, built, strict=True):
                    results[index] = self._decorate(result, route, warnings, started)
            return {"results": results, "runtime": {"elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                                                       "device": "cuda:0", "count": len(results)}}
        except Exception as exc:
            raise self._handle_error(exc) from exc
        finally:
            self._update(phase="idle", loading_model=None)
            self._memory()

    async def set_default(self, model):
        return await self.submit(self._set_default, model)

    def _set_default(self, model):
        try:
            if model != "auto":
                self._ensure_model(model)
            self.data_root.mkdir(parents=True, exist_ok=True)
            temp = self.settings_path.with_suffix(".tmp")
            temp.write_text(json.dumps({"model": model}), encoding="utf-8")
            temp.replace(self.settings_path)
            with self._lock:
                self.default_model = model
            self._update(last_error=None)
            return self.models()
        except Exception as exc:
            raise self._handle_error(exc) from exc
        finally:
            self._update(phase="idle", loading_model=None)

    async def close(self):
        with self._lock:
            self._closed = True
        # A final queued unload runs after accepted work; shutdown waits off the event loop.
        future = self._executor.submit(self._unload)
        await asyncio.shield(asyncio.wrap_future(future))
        await asyncio.to_thread(self._executor.shutdown, wait=True)
        self._update(ready=False, phase="stopped", device=None)
