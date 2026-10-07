"""Connect the examples to the hosted service and display reproducible decisions.

Credentials resolve relative to this file, never the terminal's working directory.
Only the existing HTTP service owns a model; these clients do not import PyTorch.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from copy import deepcopy
import json
from pathlib import Path
import statistics
import time
from typing import Callable

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
MODELS = ("english", "multilingual", "typed-decisions", "auto")
MODEL_HELP = (
    "English: English triage and guardrail decisions",
    "Multilingual: English, French, Arabic and other languages",
    "Typed decisions: security/support/agent-trace specialization",
    "Auto: route each state to English or multilingual",
)


@dataclass(frozen=True)
class Case:
    """Keep reference labels outside the model input to avoid label leakage."""
    name: str
    state: dict
    expected: str
    baseline: str
    detail: str


@dataclass(frozen=True)
class Scenario:
    name: str
    title: str
    questions: dict
    cases: list[Case]
    labels: dict[str, str]
    hook: str
    benefit: str
    route: Callable[[Case, dict, bool], str]
    prepare_state: Callable[[dict], dict] = deepcopy


class ExampleError(Exception):
    """User-readable client failures; authentication headers are never printed."""


class Client:
    def __init__(self, base_url: str | None = None):
        values = dotenv_values(ROOT / ".env")
        key = values.get("LAYA_API_KEY")
        if not key or key == "replace-with-a-long-random-key":
            raise ExampleError(f"Configure LAYA_API_KEY in {ROOT / '.env'} using setup.ps1.")
        self.base_url = (base_url or f"http://127.0.0.1:{values.get('LAYA_PORT') or '8000'}").rstrip("/")
        self.http = httpx.Client(
            base_url=self.base_url, headers={"Authorization": f"Bearer {key}"},
            timeout=180, trust_env=False,
        )

    def close(self):
        self.http.close()

    def request(self, method: str, path: str, **kwargs) -> dict:
        # Retry only queue saturation. OOM/setup/validation failures need a change,
        # so replaying the same input would hide the problem or prolong it.
        for attempt in range(3):
            try:
                response = self.http.request(method, path, **kwargs)
            except httpx.ConnectError:
                raise ExampleError(f"Cannot reach {self.base_url}. Run start.ps1 in the Laya project.") from None
            except httpx.TimeoutException:
                raise ExampleError("The service exceeded the 180-second timeout. Check logs/service.err.log.") from None
            try:
                body = response.json()
            except ValueError:
                raise ExampleError(f"Unexpected non-JSON response (HTTP {response.status_code}).") from None
            if response.is_success:
                return body
            error = body.get("error", {})
            code = error.get("code", f"http_{response.status_code}")
            if code == "busy" and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            if response.status_code == 401:
                raise ExampleError("API key rejected. Check the project's .env and restart after changing it.")
            raise ExampleError(f"{code}: {error.get('message', 'Request failed')}")
        raise ExampleError("Inference queue remained busy.")


def menu(title: str, options: tuple[str, ...] | list[str], default: int = 1) -> int:
    print(f"\n{title}")
    for i, label in enumerate(options, 1):
        print(f"  {i}. {label}")
    while True:
        try:
            answer = input(f"Choose 1-{len(options)} [{default}]: ").strip()
        except EOFError:
            raise ExampleError("Interactive input is unavailable. Supply --model and --example (see --help).") from None
        if not answer:
            return default - 1
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
        print("Enter one of the menu numbers.")


def build_parser(example: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Live Laya decisions for vpn-bugsmith; examples never execute agent actions.")
    parser.add_argument("--model", choices=MODELS, help="Omit to choose interactively.")
    parser.add_argument("--compare-models", action="store_true", help="Run all three named checkpoints and compare actual results.")
    if example is None:
        parser.add_argument("--example", choices=("triage", "injection", "alignment", "all"), help="Omit to choose interactively.")
    else:
        parser.set_defaults(example=example)
    parser.add_argument("--base-url", help="Explicit service address; default localhost using ../.env LAYA_PORT.")
    parser.add_argument("--threshold", type=float, default=0.8, help="Illustrative review threshold, not domain calibration (default 0.8).")
    parser.add_argument("--raw", action="store_true", help="Also print complete API responses.")
    parser.add_argument("--no-save", action="store_true", help="Skip the local JSON report under data/examples/.")
    return parser


def confidence(answer: dict) -> float:
    return float(answer.get("answer_confidence", 0))


def run_scenario(client: Client, scenario: Scenario, model: str, args) -> dict:
    print(f"\n{'=' * 72}\n{scenario.title} | requested checkpoint: {model}\n{'=' * 72}")
    print(f"Bugsmith hook: {scenario.hook}\nPurpose: {scenario.benefit}")
    records = []
    before = client.request("GET", "/api/v1/status")
    for case in scenario.cases:
        payload = {
            "model": model, "state": scenario.prepare_state(case.state), "questions": scenario.questions,
            "min_confidence": args.threshold,
        }
        started = time.perf_counter()
        response = client.request("POST", "/api/v1/predict", json=payload)
        wall_ms = round((time.perf_counter() - started) * 1000, 2)
        answer = response["answers"]["decision"]
        choice = answer["choice"]
        runtime, usage = response["runtime"], response["usage"]
        incomplete = bool(usage.get("truncated") or usage.get("options") or usage.get("truncated_questions"))
        review = incomplete or bool(answer.get("low_confidence")) or confidence(answer) < args.threshold
        correct = choice == case.expected
        print(f"\n{case.name}\n  Model input: {json.dumps(payload['state'], ensure_ascii=False)}")
        print(f"  Baseline: {case.baseline}")
        print(f"  Laya: {scenario.labels.get(choice, choice)} | confidence {confidence(answer):.1%}")
        print(f"  Fixture reference: {scenario.labels[case.expected]} | {'MATCH' if correct else 'MISMATCH'}")
        print(f"  Suggested handling: {scenario.route(case, answer, review)}")
        for label, probability in answer.get("probabilities", {}).items():
            bar = '#' * round(float(probability) * 24)
            print(f"    {scenario.labels.get(label, label):24} {float(probability):7.1%} {bar}")
        for name, extra in response["answers"].items():
            if name != "decision":
                print(f"  {name}: {json.dumps(extra, ensure_ascii=False)}")
        print(f"  Actual: {response['routing']['model']} / {runtime['device']} | service {runtime['elapsed_ms']:.2f} ms | HTTP {wall_ms:.2f} ms")
        print(f"  Token usage: {usage.get('input_tokens')} | truncated: {usage.get('truncated', False)}")
        print(f"  Integration: {case.detail}")
        if review:
            print("  REVIEW: low confidence or incomplete input; do not automate this decision.")
        for warning in runtime.get("warnings", []):
            print(f"  Runtime notice: {warning}")
        if args.raw:
            print(json.dumps(response, indent=2, ensure_ascii=False))
        records.append({
            "name": case.name, "source_state": case.state, "request": payload, "response": response,
            "reference_label": case.expected, "matches_reference": correct,
            "baseline": case.baseline, "suggested_handling": scenario.route(case, answer, review),
            "review_required": review, "http_ms": wall_ms,
        })
    after = client.request("GET", "/api/v1/status")
    matches = sum(record["matches_reference"] for record in records)
    warm = [r["response"]["runtime"]["elapsed_ms"] for r in records[1:]]
    summary = {
        "example": scenario.name, "requested_model": model, "cases": len(records), "matches": matches,
        "mismatches": len(records) - matches,
        "review_count": sum(r["review_required"] for r in records),
        "first_service_ms": records[0]["response"]["runtime"]["elapsed_ms"],
        "later_service_median_ms": round(statistics.median(warm), 2) if warm else None,
        "default_before": before["default_model"], "default_after": after["default_model"],
    }
    print(f"\nObserved: {matches}/{len(records)} fixture labels matched; {summary['review_count']} require review.")
    print(f"First call: {summary['first_service_ms']:.2f} ms; later median: {summary['later_service_median_ms']} ms.")
    print("Fixture agreement is an illustration, not measured accuracy on your real QA reports.")
    return {"summary": summary, "records": records}


def main(example: str | None = None):
    from examples.scenarios import SCENARIOS

    parser = build_parser(example)
    args = parser.parse_args()
    if not 0 <= args.threshold <= 1:
        parser.error("--threshold must be between 0 and 1")
    if args.compare_models and args.model:
        parser.error("Choose --model or --compare-models, not both")
    client = None
    try:
        print("Live examples: local HTTP service, synthetic Bugsmith fixtures, no tools executed.")
        models = list(MODELS[:3]) if args.compare_models else [args.model or MODELS[menu("Which model version?", MODEL_HELP)]]
        selected = args.example or ("triage", "injection", "alignment", "all")[menu(
            "Which example?", [s.title for s in SCENARIOS.values()] + ["Run all three examples"], default=4,
        )]
        scenarios = list(SCENARIOS.values()) if selected == "all" else [SCENARIOS[selected]]
        client = Client(args.base_url)
        status = client.request("GET", "/api/v1/status")
        print(f"Service: {client.base_url} | GPU: {(status.get('gpu') or {}).get('name', status.get('device'))}")
        print("Checkpoint switching can add loading time. Explicit selection leaves the saved default unchanged.")
        runs = [run_scenario(client, scenario, model, args) for model in models for scenario in scenarios]
        print(f"\n{'Example':12} {'Model':17} {'Matches':9} {'Reviews':8} {'Later median ms':16}")
        for run in runs:
            s = run["summary"]
            print(f"{s['example']:12} {s['requested_model']:17} {s['matches']}/{s['cases']:<7} {s['review_count']:<8} {s['later_service_median_ms']}")
        if not args.no_save:
            destination = ROOT / "data" / "examples" / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}-{selected}.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({"created_at": datetime.now(timezone.utc).isoformat(), "runs": runs}, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"\nFull requests and responses saved to {destination}")
    except (ExampleError, KeyboardInterrupt) as exc:
        parser.exit(1, f"\n{str(exc) or 'Cancelled.'}\n")
    finally:
        if client is not None:
            client.close()
