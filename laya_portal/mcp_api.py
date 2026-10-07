"""Agent tools share the HTTP app's queue rather than owning another checkpoint."""
import os
import socket

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings

from .config import PORT, ROOT
from .schemas import BatchRequest, BatchResponse, CheckpointName, ModelMetadataResponse, ModelName, ModelsResponse, PredictRequest, PredictionResponse, StatusResponse
from .model_catalog import metadata, catalog_json
from .service import ServiceError


def build_mcp(service):
    server = MCPServer("Laya Local", instructions="GPU-only typed decisions. Read laya://integration and laya://model-guide before inference; laya_model_info returns model capabilities and hosted limits without GPU work.")

    async def checked(call):
        try:
            return await call
        except ServiceError as exc:
            retry = "; retry_after_seconds=2" if exc.status == 503 else ""
            raise ToolError(f"{exc.code}: {exc.message}{retry}") from exc

    @server.tool()
    async def laya_predict(request: PredictRequest) -> PredictionResponse:
        """Answer choice, score and noul questions. A model override applies only to this request."""
        return PredictionResponse.model_validate(await checked(service.predict(request)))

    @server.tool()
    async def laya_predict_batch(request: BatchRequest) -> BatchResponse:
        """Answer up to 32 requests, preserving order with at most two states per forward batch."""
        return BatchResponse.model_validate(await checked(service.batch(request)))

    @server.tool()
    def laya_models() -> ModelsResponse:
        """List checkpoints and live model selection. Use laya_model_info for capabilities and token limits."""
        return ModelsResponse.model_validate(service.models())

    @server.tool()
    def laya_model_info(model: CheckpointName | None = None) -> ModelMetadataResponse:
        """Read detailed model capabilities, budgets, examples and caveats; omitted model returns all three. No loading or switching."""
        return metadata(model)

    @server.tool()
    def laya_status() -> StatusResponse:
        """Report actual CUDA device, memory, queue, versions and most recent runtime error."""
        return StatusResponse.model_validate(service.status())

    @server.tool()
    async def laya_set_default_model(model: ModelName) -> ModelsResponse:
        """Change the shared persistent default for all clients; use predict.model for a temporary override."""
        return ModelsResponse.model_validate(await checked(service.set_default(model)))

    @server.resource("laya://integration")
    def integration() -> str:
        """How to integrate with this local service, including errors and model limits."""
        return (ROOT / "docs" / "agents.md").read_text(encoding="utf-8")

    @server.resource("laya://architecture")
    def architecture() -> str:
        return (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")

    @server.resource("laya://models", mime_type="application/json")
    def model_catalog() -> str:
        return catalog_json()

    @server.resource("laya://model-guide", mime_type="text/markdown")
    def model_guide() -> str:
        return (ROOT / "docs" / "models.md").read_text(encoding="utf-8")

    hosts = {"localhost", "127.0.0.1", "[::1]", socket.gethostname().lower()}
    try:
        hosts.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    hosts.update(h.strip().lower() for h in os.environ.get("LAYA_ALLOWED_HOSTS", "").split(",") if h.strip())
    allowed_hosts = sorted({value for host in hosts for value in (host, f"{host}:{PORT}")})
    origins = sorted({f"http://{host}:{PORT}" for host in hosts})
    app = server.streamable_http_app(streamable_http_path="/", stateless_http=True,
                                    transport_security=TransportSecuritySettings(
                                        enable_dns_rebinding_protection=True,
                                        allowed_hosts=allowed_hosts, allowed_origins=origins),
                                    max_request_body_size=4 * 1024 * 1024)
    return server, app
