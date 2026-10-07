"""Exercise the actual sibling clients against a bounded fake HTTP service."""
import importlib.util
import json
from pathlib import Path
from threading import Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

SIBLINGS = Path(__file__).resolve().parents[2] / "Agentic-production"
TARGETS = [
    ("sift/deploy/reviewer/sift_reviewer/system_one.py", "REVIEWER_LAYA", "authentication-session"),
    ("vpn-bugsmith/src/fixer/system_one.py", "FIXER_LAYA", "TEST_BUG"),
]


def load(path):
    spec = importlib.util.spec_from_file_location("shadow_client", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("path,prefix,label", TARGETS)
def test_adapter_auth_redaction_failures_and_no_authorization(path, prefix, label, monkeypatch):
    if not (SIBLINGS / path).exists():
        pytest.skip("Sibling checkout is not installed on this machine")
    module = load(SIBLINGS / path)
    monkeypatch.delenv(prefix + "_URL", raising=False)
    assert module.hint({"title": "x"}) is None
    requests = []
    mode = ["valid"]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            requests.append((self.path, self.headers["Authorization"], json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
            data = {"advice": {"workflow": module.WORKFLOW, "label": label, "answer_confidence": .9, "review_required": False,
                               "advisory_only": True, "authorization": mode[0] == "authorization"},
                    "routing": {"model": "english"}, "runtime": {"device": "cpu" if mode[0] == "cpu" else "cuda:0", "revision": "test"}}
            self.send_response(503 if mode[0] == "busy" else 200)
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv(prefix + "_URL", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setenv(prefix + "_API_KEY", "test-only")
    try:
        hint = module.hint({"title": "email=user@example.com password=actual-secret token=actual-token"})
        assert hint["label"] == label and hint["authorization"] is False
        assert requests[0][1] == "Bearer test-only"
        state = requests[0][2]["state"]["title"]
        assert "actual-secret" not in state and "actual-token" not in state and "user@example.com" not in state
        for failure in ("cpu", "authorization", "busy"):
            mode[0] = failure
            assert module.hint({"title": "x"}) is None
        monkeypatch.setenv(prefix + "_TIMEOUT_SECONDS", "nan")
        assert module.hint({"title": "x"}) is None
        assert len(requests) == 4
    finally:
        server.shutdown()
        server.server_close()
