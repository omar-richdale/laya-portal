"""Execute the published client examples against localhost without printing credentials."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

document = (ROOT / "docs" / "agents.md").read_text(encoding="utf-8")
blocks = re.findall(r"```(python|powershell|javascript)\n(.*?)```", document, re.S)
target = ROOT / "data" / "verification" / "examples"
target.mkdir(parents=True, exist_ok=True)
report = []
for i, (language, body) in enumerate(blocks):
    extension = {"python":"py","powershell":"ps1","javascript":"mjs"}[language]
    path = target / f"client-{i}.{extension}"
    path.write_text(body, encoding="utf-8")
    if language == "python":
        command = [sys.executable, str(path)]
    elif language == "powershell":
        command = ["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(path)]
    else:
        command = ["node",str(path)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    if result.returncode:
        raise RuntimeError(f"{language} example failed: {result.stderr}")
    report.append({"language":language,"passed":True})
    print(f"{language} example passed",flush=True)
(target.parent / "docs-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
