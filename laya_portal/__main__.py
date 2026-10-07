"""Launch one on-demand process; model downloads are disabled during serving."""
import os
import uvicorn

from .config import PORT

# Set before importing the Agent so no inference path tries to reach the Hub.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

if __name__ == "__main__":
    from .app import create_app
    app = create_app()
    server = uvicorn.Server(uvicorn.Config(app, host=os.environ.get("LAYA_HOST", "0.0.0.0"), port=PORT,
                                          log_level="info", access_log=False))
    app.state.request_shutdown = lambda: setattr(server, "should_exit", True)
    server.run()
