"""Download only reference checkpoint artifacts and create the local API secret."""
import json
from pathlib import Path
import secrets
import shutil
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from laya_portal.config import MODEL_REPO, MODEL_REVISION, MODEL_ROOT


def main():
    from huggingface_hub import snapshot_download
    allow = ["model.safetensors", "rl_agent_config.json", "encoder/*", "tokenizer/*",
             "multilingual/model.safetensors", "multilingual/rl_agent_config.json", "multilingual/encoder/*", "multilingual/tokenizer/*",
             "typed-decisions/model.safetensors", "typed-decisions/rl_agent_config.json", "typed-decisions/encoder/*", "typed-decisions/tokenizer/*"]
    if shutil.disk_usage(ROOT).free < 5 * 1024**3:
        raise RuntimeError("At least 5 GiB free disk space is required for checkpoint download and working space")
    env = ROOT / ".env"
    if not env.exists():
        template = (ROOT / ".env.example").read_text(encoding="utf-8")
        env.write_text(template.replace("replace-with-a-long-random-key", secrets.token_urlsafe(36)), encoding="utf-8")
        print("Created .env with a private API key (not printed).")
    snapshot_download(MODEL_REPO, revision=MODEL_REVISION, local_dir=MODEL_ROOT, allow_patterns=allow, max_workers=3)
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "checkpoint.json").write_text(json.dumps({"repo": MODEL_REPO, "revision": MODEL_REVISION}), encoding="utf-8")
    print("All three reference checkpoints are available locally.")


if __name__ == "__main__":
    main()
