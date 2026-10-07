"""Serve the offline dashboard, validated REST API and MCP from one ASGI process."""
from contextlib import asynccontextmanager
import hmac
import json
import os
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html

from .config import MAX_BODY_BYTES, ROOT
from .mcp_api import build_mcp
from .schemas import BatchRequest, BatchResponse, ModelSetting, ModelsResponse, PredictRequest, PredictionResponse, StatusResponse
from .service import InferenceService, ServiceError
from .model_catalog import metadata
from .schemas import CheckpointName, ModelMetadataResponse


class AccessMiddleware:
    """Authenticate before buffering request bodies; bound JSON and MCP payloads."""
    def __init__(self, app, api_key):
        self.app, self.api_key = app, api_key.encode("utf-8")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope["path"]
        protected = path.startswith("/api/") or path == "/mcp" or path.startswith("/mcp/")
        if protected:
            headers = dict(scope["headers"])
            auth = headers.get(b"authorization", b"")
            expected = b"Bearer " + self.api_key
            if not hmac.compare_digest(auth, expected):
                response = JSONResponse({"error": {"code": "unauthorized", "message": "A valid bearer API key is required"}},
                                        status_code=401, headers={"WWW-Authenticate": "Bearer"})
                return await response(scope, receive, send)
        if protected and scope["method"] in ("POST", "PUT", "PATCH"):
            chunks, size = [], 0
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                body = message.get("body", b"")
                size += len(body)
                if size > MAX_BODY_BYTES:
                    return await JSONResponse({"error": {"code": "body_too_large", "message": "Maximum request body is 4 MiB"}},
                                              status_code=413)(scope, receive, send)
                chunks.append(body)
                if not message.get("more_body", False):
                    break
            body = b"".join(chunks)
            if path.startswith("/api/"):
                try:
                    def reject_constant(value):
                        raise ValueError(f"Invalid JSON constant: {value}")
                    def unique_pairs(pairs):
                        result = {}
                        for key, value in pairs:
                            if key in result:
                                raise ValueError("Duplicate JSON keys are not allowed")
                            result[key] = value
                        return result
                    json.loads(body, parse_constant=reject_constant, object_pairs_hook=unique_pairs)
                except (ValueError, UnicodeDecodeError):
                    return await JSONResponse({"error": {"code": "invalid_json", "message": "Body must be valid JSON without duplicate keys"}},
                                              status_code=400)(scope, receive, send)
            replayed = False
            async def replay():
                nonlocal replayed
                if not replayed:
                    replayed = True
                    return {"type": "http.request", "body": body, "more_body": False}
                return await receive()
            return await self.app(scope, replay, send)
        return await self.app(scope, receive, send)


def create_app(service=None, *, api_key=None, initialize=True):
    service = service or InferenceService()
    api_key = api_key or os.environ.get("LAYA_API_KEY", "")
    if len(api_key) < 24 or api_key == "replace-with-a-long-random-key":
        raise RuntimeError("Set a random LAYA_API_KEY of at least 24 characters using setup.ps1")
    mcp, mcp_app = build_mcp(service)

    @asynccontextmanager
    async def lifespan(app):
        try:
            if initialize:
                await service.start()
            async with mcp.session_manager.run():
                yield
        finally:
            await service.close()

    app = FastAPI(title="Laya Local", version="0.1.0", description="GPU-only typed decisions on this machine.",
                  lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.service = service
    app.add_middleware(AccessMiddleware, api_key=api_key)
    bearer = HTTPBearer()

    @app.exception_handler(ServiceError)
    async def service_error(request, exc):
        return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=exc.status,
                            headers={"Retry-After": "2"} if exc.status == 503 else {})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Avoid echoing submitted states and credentials in public error responses.
        details = [{"loc": list(e["loc"]), "message": e["msg"], "type": e["type"]} for e in exc.errors()]
        return JSONResponse({"error": {"code": "validation_error", "message": "Request validation failed", "details": details}}, status_code=422)

    auth = [Depends(bearer)]

    @app.post("/api/v1/predict", dependencies=auth, tags=["Inference"], response_model=PredictionResponse)
    async def predict(request: PredictRequest) -> dict:
        return await service.predict(request)

    @app.post("/api/v1/predict/batch", dependencies=auth, tags=["Inference"], response_model=BatchResponse)
    async def batch(request: BatchRequest) -> dict:
        return await service.batch(request)

    from .workflows import WorkflowRequest, advice

    @app.post("/api/v1/workflows/{workflow}", dependencies=auth, tags=["Advisory workflows"], response_model=PredictionResponse)
    async def workflow_advice(workflow: Literal["issue_lane", "qa_cause", "security_specialist"], request: WorkflowRequest) -> dict:
        result = await service.predict(request.prediction(workflow))
        result["advice"] = advice(workflow, result)
        return result

    @app.get("/api/v1/benchmark", dependencies=auth, tags=["Benchmark"])
    def benchmark():
        from .benchmark import summary
        return summary()

    @app.get("/api/v1/models", dependencies=auth, tags=["Runtime"], response_model=ModelsResponse)
    def models() -> dict:
        return service.models()

    @app.get("/api/v1/model-metadata", dependencies=auth, tags=["Model learning"], response_model=ModelMetadataResponse)
    def model_metadata():
        """Read capabilities, local budgets, measured evidence and sources without GPU work."""
        return metadata()

    @app.get("/api/v1/models/{model}/metadata", dependencies=auth, tags=["Model learning"], response_model=ModelMetadataResponse)
    def checkpoint_metadata(model: CheckpointName):
        """Read a named checkpoint's guide. auto is routing mode, not a checkpoint."""
        return metadata(model)

    @app.put("/api/v1/settings/model", dependencies=auth, tags=["Runtime"], response_model=ModelsResponse)
    async def set_model(setting: ModelSetting) -> dict:
        return await service.set_default(setting.model)

    @app.get("/api/v1/status", dependencies=auth, tags=["Runtime"], response_model=StatusResponse)
    def status() -> dict:
        return service.status()

    @app.post("/api/v1/shutdown", dependencies=auth, tags=["Runtime"])
    def shutdown(tasks: BackgroundTasks) -> dict:
        callback = getattr(app.state, "request_shutdown", None)
        if callback is None:
            raise ServiceError("shutdown_unavailable", "This app is not running through the managed launcher")
        tasks.add_task(callback)
        return {"status": "stopping"}

    @app.get("/health", include_in_schema=False)
    def health():
        return {"status": "ok" if service.status()["ready"] else "starting"}

    @app.get("/llms.txt", include_in_schema=False)
    def llms():
        return FileResponse(ROOT / "docs" / "llms.txt", media_type="text/plain")

    @app.get("/models.json", include_in_schema=False)
    def public_model_catalog():
        """Public learning data contains no credentials, issue inputs or live runtime state."""
        return metadata()

    @app.get("/docs", include_in_schema=False)
    def swagger():
        return get_swagger_ui_html(openapi_url="/openapi.json", title="Laya Local API",
                                   swagger_js_url="/api-docs/swagger-ui-bundle.js",
                                   swagger_css_url="/api-docs/swagger-ui.css", swagger_favicon_url="/favicon.svg")

    @app.get("/docs/{name}.md", include_in_schema=False)
    def markdown(name: str):
        if name not in ("agents", "architecture", "api", "verification", "system-one-integrations", "models", "operations", "development"):
            return PlainTextResponse("Not found", status_code=404)
        return FileResponse(ROOT / "docs" / f"{name}.md", media_type="text/markdown")

    # Mount MCP before the SPA so its transport never falls through to index.html.
    app.mount("/mcp", mcp_app)
    dist = ROOT / "frontend" / "dist"
    if (dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def portal(path: str):
        if path.startswith(("api/", "mcp", "docs/")):
            return PlainTextResponse("Not found", status_code=404)
        candidate = (dist / path).resolve()
        if candidate.is_relative_to(dist.resolve()) and candidate.is_file():
            return FileResponse(candidate)
        if path in ("", "playground", "batch", "models", "guide", "benchmark", "model-guide") and (dist / "index.html").exists():
            return FileResponse(dist / "index.html")
        return PlainTextResponse("Portal is not built. Run setup.ps1.", status_code=404)

    return app
