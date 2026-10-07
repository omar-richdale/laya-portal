"""Install opt-in, metadata-only clients into the reviewed sibling checkouts.

The adapters do not select tools, verify vulnerabilities or alter repair gates.
Their response projections deliberately exclude source, prompts and raw outputs.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIBLINGS = ROOT.parent / "Agentic-production"
TEMPLATE = '''"""Optional local System One hints; existing evidence and policy remain authoritative."""
import json
import math
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

PREFIX = "__PREFIX__"
WORKFLOW = "__WORKFLOW__"
DEFAULT_MODEL = "__MODEL__"
LABELS = __LABELS__


def redact(value):
    """Project text only after removing common credential forms and identifiers."""
    text = str(value)
    text = re.sub(r"\\x1b\\[[0-9;]*m", "", text)
    text = re.sub(r"[\\w.+-]+@[\\w.-]+\\.[A-Za-z]{2,}", "[email]", text)
    text = re.sub(r"(?i)(bearer\\s+)[^\\s\\\"']+", r"\\1[redacted]", text)
    text = re.sub(r"(?i)((?:password|secret|api[_-]?key|access[_-]?token|token)\\s*[=:]\\s*)[^\\s,;]+", r"\\1[redacted]", text)
    text = re.sub(r"[A-Za-z0-9_+/=-]{32,}", "[redacted-long-value]", text)
    return text[:550]


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def hint(state):
    """Return validated advice or None, with no requests unless explicitly configured."""
    url, key = os.getenv(PREFIX + "_URL", ""), os.getenv(PREFIX + "_API_KEY", "")
    if not url or not key:
        return None
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            return None
        model = os.getenv(PREFIX + "_MODEL", DEFAULT_MODEL)
        if model not in ("auto", "english", "multilingual", "typed-decisions"):
            return None
        timeout = float(os.getenv(PREFIX + "_TIMEOUT_SECONDS", "2"))
        if not math.isfinite(timeout) or not 0 < timeout <= 5:
            return None
        payload = {"state": {k: redact(v) for k, v in state.items()}, "model": model, "min_confidence": .8}
        request = Request(url.rstrip("/") + "/api/v1/workflows/" + WORKFLOW,
                          data=json.dumps(payload).encode(), headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            data = json.loads(response.read(65537))
        if not isinstance(data, dict) or not all(isinstance(data.get(k), dict) for k in ("advice", "runtime", "routing")):
            return None
        advice = data["advice"]
        confidence = advice["answer_confidence"]
        if (advice.get("advisory_only") is not True or advice.get("authorization") is not False
                or advice.get("workflow") != WORKFLOW or advice.get("label") not in LABELS
                or isinstance(confidence, bool) or not isinstance(confidence, (int, float))
                or not math.isfinite(confidence) or not 0 <= confidence <= 1
                or not isinstance(advice.get("review_required"), bool)
                or data["runtime"].get("device") != "cuda:0"
                or data["routing"].get("model") not in ("english", "multilingual", "typed-decisions")
                or not isinstance(data["runtime"].get("revision"), str)):
            return None
        return {"label": advice["label"], "answer_confidence": confidence,
                "review_required": advice["review_required"], "advisory_only": True, "authorization": False,
                "checkpoint": data["routing"]["model"], "revision": data["runtime"]["revision"]}
    except (OSError, HTTPError, URLError, ValueError, KeyError, TypeError):
        return None
'''

targets = [
    ("sift/deploy/reviewer/sift_reviewer/system_one.py", "REVIEWER_LAYA", "security_specialist", "typed-decisions",
     {"authentication-session", "crypto-secret-handling", "code-correctness", "other"}),
    ("vpn-bugsmith/src/fixer/system_one.py", "FIXER_LAYA", "qa_cause", "english",
     {"PRODUCT_BUG", "TEST_BUG", "INFRA", "UNKNOWN"}),
]
for path, prefix, workflow, model, labels in targets:
    source = TEMPLATE.replace("__PREFIX__", prefix).replace("__WORKFLOW__", workflow).replace("__MODEL__", model)
    source = source.replace("__LABELS__", repr(sorted(labels)))
    (SIBLINGS / path).write_text(source, encoding="utf-8")
    print(path)
