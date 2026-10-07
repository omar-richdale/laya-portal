"""Run the installed Python/TypeScript shadow clients on frozen real evidence.

Only localhost inference runs. No repair pipeline, browser test, notification or
GitHub mutation is invoked. Environment credentials exist only in this process
and its short-lived native TypeScript client.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.common import Client, ROOT
from laya_portal.workflows import LABELS, QUESTIONS
from dotenv import dotenv_values


def load_client(path):
    spec = importlib.util.spec_from_file_location("installed_shadow_client", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    siblings = ROOT.parent / "Agentic-production"
    corpus = json.loads((ROOT / "docs/benchmark/corpus.json").read_text(encoding="utf-8"))
    output = {"mode": "local read-only shadow replay", "sift": [], "bugsmith": [], "qa": []}
    client = Client()
    values = dotenv_values(ROOT / ".env")
    try:
        for repo, path, prefix, workflow, model in (
            ("sift", "sift/deploy/reviewer/sift_reviewer/system_one.py", "REVIEWER_LAYA", "security_specialist", "typed-decisions"),
            ("bugsmith", "vpn-bugsmith/src/fixer/system_one.py", "FIXER_LAYA", "qa_cause", "english"),
        ):
            module = load_client(siblings / path)
            cases = [c for c in corpus["cases"] if c["workflow"] == workflow]
            # Warm the explicit checkpoint; short production timeouts intentionally
            # fall back if a model is still loading after a process restart.
            client.request("POST", "/api/v1/predict", json={"state": cases[0]["state"], "questions": QUESTIONS[workflow], "model": model, "max_len": 512, "head_max_len": 192})
            old = {key: os.environ.get(key) for key in (prefix + "_URL", prefix + "_API_KEY", prefix + "_MODEL", prefix + "_TIMEOUT_SECONDS")}
            os.environ.update({prefix + "_URL": client.base_url, prefix + "_API_KEY": values["LAYA_API_KEY"], prefix + "_MODEL": model, prefix + "_TIMEOUT_SECONDS": "5"})
            try:
                for case in cases:
                    hint = module.hint(case["state"])
                    output[repo].append({"id": case["id"], "reference": LABELS[workflow][case["expected"]], "hint": hint,
                                         "matches_reference": hint is not None and hint["label"] == LABELS[workflow][case["expected"]]})
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
        qa = siblings / "QA_Web_Testing_Agent"
        reports = [ROOT / f"data/benchmark/sources/{run}/report.json" for run in (
            "20260930-060000-9iy9o", "20260930-071000-9o49u", "20260929-071000-wzuvk")]
        env = {**os.environ, "QA_LAYA_URL": client.base_url, "QA_LAYA_API_KEY": values["LAYA_API_KEY"], "QA_LAYA_MODEL": "english", "QA_LAYA_TIMEOUT_SECONDS": "5"}
        replay = subprocess.run(["node", "--import", "tsx", "scripts/replay-system-one.ts", *map(str, reports)], cwd=qa, env=env,
                                capture_output=True, text=True, timeout=90)
        if replay.returncode:
            raise RuntimeError("Native QA replay failed; install its locked Node dependencies and inspect the script locally.")
        output["qa"] = json.loads(replay.stdout)
        status = client.request("GET", "/api/v1/status")
        output["resident_after"] = status["resident_model"]
        output["saved_default_after"] = status["default_model"]
        destination = ROOT / "docs/benchmark/integration-replay.json"
        destination.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(destination)
        for name in ("sift", "bugsmith"):
            print(f"{name}: {sum(r['matches_reference'] for r in output[name])}/{len(output[name])} reference matches via installed shadow client")
        print(f"qa: {sum(len(r['hints']) for r in output['qa'])} native TypeScript hints; source reports unchanged")
    finally:
        client.close()


if __name__ == "__main__":
    main()
