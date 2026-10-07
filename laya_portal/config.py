"""Project paths and immutable checkpoint identities used by setup and serving."""
from pathlib import Path
import os

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
MODEL_REPO = "convaiinnovations/laya"
MODEL_REVISION = "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"
MODEL_ROOT = ROOT / "models" / MODEL_REVISION
DATA_ROOT = ROOT / "data"
MODEL_DIRS = {
    "english": MODEL_ROOT,
    "multilingual": MODEL_ROOT / "multilingual",
    "typed-decisions": MODEL_ROOT / "typed-decisions",
}
MODEL_INFO = {
    "english": {"title": "English", "description": "English classification, routing and guardrails", "context": 512, "head": 192},
    "multilingual": {"title": "Multilingual", "description": "English, Arabic, French and 100+ languages", "context": 1024, "head": 256},
    "typed-decisions": {"title": "Typed decisions", "description": "Fine-tuned invoice, security, support and agent-trace workflows", "context": 1024, "head": 256},
}
MAX_JOBS = 8
MAX_BATCH = 32
MAX_BODY_BYTES = 4 * 1024 * 1024
PORT = int(os.environ.get("LAYA_PORT", "8000"))
