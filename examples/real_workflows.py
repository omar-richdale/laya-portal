"""Try the exact real benchmark cases using the key in this project's .env."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.common import Client, ExampleError, MODELS, MODEL_HELP, menu


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODELS)
    parser.add_argument("--example", type=int, help="Example number; omit for an interactive menu")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--raw", action="store_true")
    args = parser.parse_args()
    client = None
    try:
        model = args.model or MODELS[menu("Which checkpoint?", MODEL_HELP)]
        client = Client()
        examples = client.request("GET", "/api/v1/benchmark")["examples"]
        index = args.example - 1 if args.example else menu("Which real example?", [e["title"] for e in examples]) if not args.all else 0
        if not 0 <= index < len(examples):
            parser.error(f"--example must be 1-{len(examples)}")
        for example in examples if args.all else [examples[index]]:
            response = client.request("POST", f"/api/v1/workflows/{example['workflow']}", json={"state": example["state"], "model": model})
            advice = response["advice"]
            print(f"\n{example['title']}\nSource: {example['source']}")
            print(f"Laya: {advice['label']} (p={advice['answer_confidence']:.1%})")
            print(f"Evidence reference: {example['expected_label']} — {example['reference_basis']}")
            print(f"Reference agreement: {advice['label'] == example['expected_label']}; review required: {advice['review_required']}")
            print(f"Actual device: {response['runtime']['device']}; checkpoint: {response['routing']['model']}; service: {response['runtime']['elapsed_ms']:.2f} ms")
            print("Probabilities:", json.dumps(response["answers"]["decision"]["probabilities"]))
            print("Advice only: no repair, tool execution or issue closure authorized.")
            if args.raw:
                print(json.dumps(response, indent=2))
    except (ExampleError, KeyboardInterrupt) as exc:
        parser.exit(1, f"{exc}\n")
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    main()
