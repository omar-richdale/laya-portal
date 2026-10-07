"""Build the offline learning catalog from reviewed sources and pinned local evidence.

Run with the project venv after deliberately reviewing new weights or documentation.
This reads safetensors headers, never loads tensors or starts a model process.
"""
import json
from copy import deepcopy
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from laya_portal.config import MODEL_DIRS, MODEL_INFO, MODEL_REPO, MODEL_REVISION

REVIEWED = "2026-10-01"
SOURCES = [
    {"id": "family", "title": "Laya family model card", "url": "https://huggingface.co/convaiinnovations/laya/blob/main/README.md"},
    {"id": "multilingual", "title": "Multilingual model card", "url": "https://huggingface.co/convaiinnovations/laya-multilingual/blob/main/README.md"},
    {"id": "typed", "title": "Typed-decisions model card", "url": "https://huggingface.co/convaiinnovations/laya-typed-decisions/blob/main/README.md"},
    {"id": "limits", "title": "Upstream benchmark limitations", "url": "https://nandhakishorm.github.io/laya/benchmarks/"},
    {"id": "benchmarks", "title": "Upstream benchmark tables and corrections", "url": "https://github.com/NandhaKishorM/laya/blob/main/BENCHMARKS.md"},
    {"id": "sdk", "title": "Upstream Agent API", "url": "https://nandhakishorm.github.io/laya/reference/agent/"},
    {"id": "structured", "title": "Upstream schema-driven decisions", "url": "https://nandhakishorm.github.io/laya/structured/"},
    {"id": "adoption", "title": "Upstream staged adoption", "url": "https://nandhakishorm.github.io/laya/staged-adoption/"},
]
DESCRIPTIONS = {
    "english": {
        "summary": "Start here for short English tickets and bounded classification questions.",
        "languages": {"primary": "English", "examples": ["en"], "coverage": "Prefer multilingual for non-English input; English confidence can remain high on an unreadable language."},
        "good_at": ["English email or support-ticket routing", "Small-label intent, topic and sentiment decisions", "Candidate guardrail signals, evaluated on your own examples"],
        "local_recommendation": "Best issue-lane agreement in our English backlog snapshot. Existing scanner metadata is still the first routing source.",
        "caveats": ["Stored choice:11+ temperature is 0.10058; Laya 0.3.22 clamps it to 0.5 and emits a warning.", "A confident output can still be wrong. Our synthetic action-alignment examples matched only 1/6 references.", "Our real QA cases matched 4/7; it missed the card-required trial contract."],
        "source_ids": ["family", "limits"],
        "upstream_evidence": {"description": "The family card recommends English classification, guardrails and email triage. Those are candidate uses, not validated security guarantees.", "metrics": [], "source_ids": ["family"]},
        "example": {"state": "I was charged twice for my VPN subscription. Please refund the duplicate payment.", "questions": {"team": {"type": "choice", "instructions": "Which team should review this ticket?", "criteria": {"A": "billing: invoices, duplicate payments or refund requests", "B": "technical support: broken apps or connectivity", "C": "sales: pricing or new subscriptions"}}}},
    },
    "multilingual": {
        "summary": "Use for French, Arabic and other languages, or longer compact evidence.",
        "languages": {"primary": "Multilingual", "examples": ["en", "fr", "ar", "es", "de", "pt", "it", "hi", "zh", "ja", "ko", "tr", "ru"], "coverage": "Upstream claims 100+ languages; coverage and accuracy vary by language and task. Our backlog benchmark was English, not a multilingual-quality evaluation."},
        "good_at": ["Routing and classification of non-English tickets", "French or Arabic support queues with English question descriptions", "Longer state inputs when essential evidence does not fit the shorter checkpoints"],
        "local_recommendation": "Use for language coverage. It was fastest in our compact benchmark, but less accurate on the English backlog.",
        "caveats": ["Pinned config has temperatures [1, 1, 1] and no option-count buckets: it ships without fitted calibration.", "A longer accepted context is not proof of long-document accuracy or safe memory use.", "Our real QA cases matched 0/7; two issue-lane mistakes exceeded the 0.8 review threshold."],
        "source_ids": ["multilingual", "limits"],
        "upstream_evidence": {"description": "The model card describes 100+ languages and a 1,024-token default expandable to 8,192. Coverage does not guarantee useful accuracy in every language. Published language-sweep numbers have been revised; consult the current benchmark's correction notes.", "metrics": [], "source_ids": ["multilingual", "benchmarks"]},
        "example": {"state": "تم تحصيل رسوم اشتراك VPN مرتين. أرجو إعادة المبلغ المكرر.", "questions": {"team": {"type": "choice", "instructions": "Which team should review this Arabic ticket?", "criteria": {"A": "billing: duplicate charges and refunds", "B": "technical support: connection failures", "C": "sales: new subscriptions"}}}},
    },
    "typed-decisions": {
        "summary": "An English specialist for invoice, security, support and agent-trace decisions.",
        "languages": {"primary": "English", "examples": ["en"], "coverage": "Upstream documents English-only fine-tuning; choose multilingual for other languages."},
        "good_at": ["Invoice-processing decisions with fixed fields or categories", "Security-incident and customer-service triage", "Agent-trace observability: choosing among a small set of known outcomes"],
        "local_recommendation": "Promising for security-topic hints: 7/7 references in our small sample, all below the 0.8 review threshold. This does not establish reliable prompt-injection detection or action authorization.",
        "caveats": ["Specialized on four synthetic workflows; transfer to new domains is unproven.", "Inherited option-count temperatures override per-type values. The stored choice:11+ bucket also requires the runtime clamp.", "Upstream warns its per-type calibration used training items. Treat current probabilities as uncalibrated for your domain.", "Our QA cases matched 4/7 and missed the card-required trial; synthetic action alignment matched 1/6."],
        "source_ids": ["typed", "limits"],
        "upstream_evidence": {"description": "Upstream reports fine-tuning on 1,200 training cases (6,000 decisions), then 400 test cases (2,000 decisions) across four workflows. This is a benchmark-specific specialist result, not general production accuracy. Its confidence needs independent held-out calibration.", "metrics": [{"name": "Typed-decisions accuracy", "value": 0.766}, {"name": "Invoice processing accuracy", "value": 0.804}, {"name": "Security incidents accuracy", "value": 0.766}, {"name": "Customer service accuracy", "value": 0.764}, {"name": "Agent-trace accuracy", "value": 0.730}, {"name": "Expected calibration error (lower is better)", "value": 0.213}], "source_ids": ["typed"]},
        "example": {"state": {"incident": "A deployment used a token that was revoked. The API returned 401. No successful access is recorded.", "evidence": "revoked-token request rejected"}, "questions": {"topic": {"type": "choice", "instructions": "Which specialist should inspect this incident? Do not infer a successful attack without evidence.", "criteria": {"A": "authentication and session handling", "B": "billing and invoice processing", "C": "network availability"}}}},
    },
}


def build():
    sources = list(SOURCES)
    results = json.loads((ROOT / "docs/benchmark/results.json").read_text(encoding="utf-8"))
    models = []
    for name, path in MODEL_DIRS.items():
        cfg = json.loads((path / "rl_agent_config.json").read_text(encoding="utf-8"))
        enc = json.loads((path / "encoder/config.json").read_text(encoding="utf-8"))
        with (path / "model.safetensors").open("rb") as stream:
            tensors = json.loads(stream.read(struct.unpack("<Q", stream.read(8))[0]))
        startup = json.loads((ROOT / f"docs/benchmark/startup-{name}.json").read_text(encoding="utf-8"))
        stats = results["models"][name]
        subfolder = "" if name == "english" else name
        config_url = f"https://huggingface.co/{MODEL_REPO}/blob/{MODEL_REVISION}/{subfolder + '/' if subfolder else ''}rl_agent_config.json"
        source_id = f"config-{name}"
        sources.append({"id": source_id, "title": f"Pinned {name} configuration", "url": config_url})
        metadata = {
            "id": name, "title": MODEL_INFO[name]["title"], **deepcopy(DESCRIPTIONS[name]),
            "identity": {"repository": MODEL_REPO, "subfolder": subfolder or None, "revision": MODEL_REVISION, "license": "Apache-2.0", "knowledge_cutoff": "Not published; use supplied evidence rather than assuming up-to-date knowledge."},
            "architecture": {"backbone": cfg["encoder"], "parameters_approx_millions": 322 if name == "multilingual" else 421, "stored_tensor_elements": sum(math.prod(t["shape"]) for key, t in tensors.items() if key != "__metadata__"), "encoder_layers": enc["num_hidden_layers"], "hidden_size": enc["hidden_size"], "attention_heads": enc["num_attention_heads"], "vocabulary_size": enc["vocab_size"], "decision_head_layers": cfg["head_layers"], "encoder_position_capacity": enc["max_position_embeddings"], "weights_bytes": (path / "model.safetensors").stat().st_size, "stored_tensor_dtypes": sorted({t["dtype"] for key, t in tensors.items() if key != "__metadata__"}), "cuda_autocast": cfg["amp_dtype"], "parameter_note": "Approximate model size from upstream; exact stored tensor elements are counted from the local safetensors header and can include buffers."},
            "tokens": {"default_total": MODEL_INFO[name]["context"], "default_question": MODEL_INFO[name]["head"], "approx_state_before_formatting": MODEL_INFO[name]["context"] - MODEL_INFO[name]["head"], "hosted_max_total": 8192 if name == "multilingual" else MODEL_INFO[name]["context"], "encoder_max_positions": enc["max_position_embeddings"], "head_override_max": 1024, "option_description_token_cap": 48, "recommended_max_choices": 20, "output_tokens": 0},
            "local_evidence": {"recorded_on": "2026-10-01", "device": "NVIDIA GeForce RTX 4050 Laptop GPU / cuda:0", "max_len": 512, "head_max_len": 192, "repeats": results["repeats"], "quality": {k: {field: value for field, value in v.items() if field != "confusion"} for k, v in stats["quality"].items()}, "service_ms": stats["service_ms"], "http_ms": stats["http_ms"], "batch": stats["batch"], "fresh_process_first_service_ms": startup["first_service_ms"], "fresh_process_load_ms": startup["load_ms"], "fresh_process_peak_allocated_bytes": startup["process_peak_allocated_bytes"], "method": "247 unique cases: 233 issue lanes, seven security topics, seven QA observations. Three repeated passes; quality uses first pass. Fixed label order. Reference agreement, not independent vulnerability or production accuracy. All three missed the card-required trial. Baseline: always dependency matches 196/233 (84.12%). Startup is one fresh-process sample, not a percentile or cold boot. Allocator peak excludes other processes and CUDA/display overhead."},
            "metadata_url": f"/api/v1/models/{name}/metadata",
        }
        metadata["source_ids"].append(source_id)
        metadata["example"].update(model=name, min_confidence=0.8)
        models.append(metadata)
    catalog = {
        "schema_version": "1.0", "reviewed_at": REVIEWED, "checkpoint_revision": MODEL_REVISION,
        "family": {"name": "Laya System One", "description": "A bidirectional encoder and decision head score request-defined options in one forward pass. Outputs are choice, ordinal score or yes-probability; no generated prose, code patches or free-form extraction.", "question_types": [{"type": "choice", "meaning": "Selects the highest-probability key from your criteria object; returns per-key probabilities.", "example": "billing / technical / sales"}, {"type": "score", "meaning": "Returns the expected zero-based ordinal level, potentially fractional, plus level probabilities and legend; not a free-form numeric calculation.", "example": "0 = routine, 1 = soon, 2 = blocking"}, {"type": "noul", "meaning": "Returns P(true) between 0 and 1; no criteria or custom boolean labels are accepted by this hosted API.", "example": "Does this ticket explicitly request a refund?"}], "training": "Upstream describes RLCD reinforcement learning for decision distributions; typed-decisions adds domain fine-tuning. A probability-oriented training objective does not establish calibration on your data.", "source_ids": ["family", "sdk"]},
        "service": {"runtime": "Python 3.12 / PyTorch 2.10.0+cu128 / Laya 0.3.22 / Transformers 4.57.6", "device_policy": "CUDA only; no CPU retry. One checkpoint resident; one serialized worker. Compilation and TileLang disabled.", "routing": "auto selects English or multilingual using upstream language/script heuristics; typed-decisions requires explicit selection. Omitted model uses saved default. Per-request model never changes it.", "limits": {"max_questions": 64, "max_choice_options": 100, "max_score_levels": 32, "max_total_options": 512, "max_state_serialized_characters": 50000, "max_batch_requests": 32, "max_microbatch_states": 2, "max_outstanding_jobs": 8, "max_body_bytes": 4194304}, "token_notes": ["Tokens are tokenizer pieces, not words or characters. JSON keys, punctuation, instructions and choice descriptions count.", "max_len covers the full sequence for each question. head_max_len budgets question/options within it. Approximate state room assumes a full head; actual room varies with formatting and special markers.", "Long text/objects retain their beginning; JSON conversation lists retain the end. Check usage.truncated, state_tokens_dropped and truncated_questions before relying on a decision.", "Each option description is initially capped at 48 tokens in the pinned runtime; crowded choices can be shortened further. Inspect option-distinctness warnings. Increasing total context alone does not expand the choice budget.", "The API validates head_max_len < max_len - 8. max_len can be 64..8192 globally, but the selected checkpoint's smaller hosted cap still applies.", "auto with a large context can route to English and be rejected. Explicitly choose multilingual for max_len above 1024.", "Accepted limits are not throughput/VRAM guarantees. More questions, options, longer contexts and batches increase memory and latency."], "confidence_notes": ["answer_confidence is the largest option probability. For noul this is max(P(true), 1-P(true)). For score it refers to a modal level, not a guarantee that the fractional expected score is correct.", "Legacy confidence on choice/score is normalized entropy and is not the same quantity. action.act_probability is learned act/escalate evidence, not tool authorization.", "min_confidence only adds low_confidence=true below your threshold; it keeps the answer and does not enforce review or block execution. Fixed workflow adapters separately attach advisory review metadata.", "Our fixed workflows use 0.8 for review, but that threshold has not been calibrated for production. All seven real QA cases and all seven typed security-topic cases required review."], "usage_tips": ["Supply only relevant, redacted evidence and a trusted product contract. Give a clear decision question and distinct short descriptions.", "Prefer a small shortlist; include unknown/review where the task allows it. Use neutral A/B keys to cross-check unreliable yes/no answers.", "Test wording, option order and each question type on held-out domain data; probabilities can be confident and wrong.", "Keep scanner facts, application permissions and test outcomes authoritative. Prompt-injection and misalignment screening are candidate advisory experiments, not proven defenses."], "unexposed_upstream_features": ["predict_long sliding-window aggregation", "decide JSON Schema / Pydantic convenience methods", "arbitrary Python hooks, custom noul labels and lang/lang_guess request controls", "fine-tuning or calibration training endpoints"], "errors": "401 authentication; 422 validation/budget; 503 busy with Retry-After: 2 or runtime/GPU errors. Inspect error.code; only queue saturation warrants an unchanged automatic retry.", "privacy": "Inference is local and offline after setup. Portal keys are tab-scoped; inputs/results stay in browser memory unless exported. Runtime logs may contain model/error diagnostics. Metadata fetches do not load a checkpoint.", "source_ids": ["sdk", "limits", "adoption", "structured"]},
        "models": models, "sources": [{**s, "reviewed_at": REVIEWED} for s in sources],
        "provenance": "Published capability summaries were reviewed on the stated date and may change upstream. Local configs, hosted constraints and measured evidence describe the pinned installation. Guides do not update weights or perform network requests at runtime.",
        "links": {"json": "/models.json", "markdown": "/docs/models.md", "authenticated_api": "/api/v1/model-metadata", "mcp_resource": "laya://models", "mcp_guide": "laya://model-guide", "mcp_tool": "laya_model_info", "openapi": "/openapi.json", "benchmark": "/api/v1/benchmark"},
    }
    (ROOT / "docs/models.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source_by_id = {s["id"]: s for s in catalog["sources"]}
    lines = ["# Hosted Laya model guide", "", f"Reviewed {REVIEWED}. Catalog schema 1.0. Offline checkpoint revision `{MODEL_REVISION}`.", "", catalog["family"]["description"], "", "[Machine-readable catalog](/models.json) · [API contract](/docs/api.md) · [Integration guide](/docs/agents.md)", "", "## Choose a checkpoint", "", "| Model | Parameters (approx.) | Total default | Question/options budget | Approximate state before formatting | Hosted maximum |", "|---|---:|---:|---:|---:|---:|"]
    for m in models:
        t = m["tokens"]
        lines.append(f"| {m['title']} | {m['architecture']['parameters_approx_millions']}M | {t['default_total']} | {t['default_question']} | {t['approx_state_before_formatting']} | {t['hosted_max_total']} |")
    lines += ["", "All counts are tokens, not words. Approximate state room is not an exact allowance. Encoder configs list 8,192 positions for all three backbones; this service deliberately exposes only the hosted limits above.", ""]
    for m in models:
        a, t, ev = m["architecture"], m["tokens"], m["local_evidence"]
        lines += [f"## {m['title']} (`{m['id']}`)", "", m["summary"], "", "**Candidate uses:** " + "; ".join(m["good_at"]) + ".", "", "**Languages:** " + m["languages"]["coverage"], "", f"**Architecture:** `{a['backbone']}`, {a['encoder_layers']} encoder layers, hidden size {a['hidden_size']}, {a['attention_heads']} attention heads, vocabulary {a['vocabulary_size']:,}, {a['decision_head_layers']}-layer decision head. Local weight file {a['weights_bytes']/1024**2:.2f} MiB (excludes tokenizer/configs and runtime memory). CUDA autocast `{a['cuda_autocast']}`; stored types {', '.join(a['stored_tensor_dtypes'])}. Apache-2.0. Knowledge cutoff is not published.", "", "**Published evidence:** " + m["upstream_evidence"]["description"]]
        for metric in m["upstream_evidence"]["metrics"]:
            lines.append(f"- {metric['name']}: {metric['value']}")
        lines += ["", "**Local guidance:** " + m["local_recommendation"], "", "**Measured RTX 4050 evidence:**"]
        for task, q in ev["quality"].items():
            lines.append(f"- {task}: {q['correct']}/{q['count']} reference matches; macro F1 {q['macro_f1']}; review {q['review']}/{q['count']}.")
        lines += [f"- Warm service median/p95: {ev['service_ms']['median']}/{ev['service_ms']['p95']} ms. HTTP median/p95: {ev['http_ms']['median']}/{ev['http_ms']['p95']} ms.", f"- 32-state batch, microbatch two: {ev['batch']['median_ms']} ms; {ev['batch']['states_per_second']} states/sec.", f"- One fresh-process sample: first call {ev['fresh_process_first_service_ms']} ms, load {ev['fresh_process_load_ms']} ms; allocator peak {ev['fresh_process_peak_allocated_bytes']/1024**3:.3f} GiB.", "", ev["method"], "", "**Checkpoint caveats:**"] + [f"- {c}" for c in m["caveats"]]
        lines += ["", "**Runnable request body:**", "", "```json", json.dumps(m["example"], ensure_ascii=False, indent=2), "```", "", "Sources: " + ", ".join(f"[{source_by_id[s]['title']}]({source_by_id[s]['url']})" for s in m["source_ids"]) + ".", ""]
    lines += ["## Outputs and budgets", ""]
    for q in catalog["family"]["question_types"]:
        lines += [f"- `{q['type']}`: {q['meaning']}"]
    for title, key in [("Token budgeting", "token_notes"), ("Confidence and review", "confidence_notes"), ("Using a model well", "usage_tips")]:
        lines += ["", f"## {title}", ""] + [f"- {s}" for s in catalog["service"][key]]
    lines += ["", "## Hosted service contract", "", catalog["service"]["routing"], "", catalog["service"]["device_policy"], "", "```json", json.dumps(catalog["service"]["limits"], indent=2), "```", "", catalog["service"]["errors"], "", catalog["service"]["privacy"], "", "Upstream SDK features **not exposed** by this server: " + "; ".join(catalog["service"]["unexposed_upstream_features"]) + ".", "", "## Fetch from an agent", "", "Public, credential-free metadata: `GET /models.json` and `GET /docs/models.md`. These files contain learning information and aggregate measurements, never credentials, runtime status or raw issue inputs.", "", "Authenticated metadata: `GET /api/v1/model-metadata`, or `GET /api/v1/models/{english|multilingual|typed-decisions}/metadata`. Send `Authorization: Bearer <LAYA_API_KEY>`.", "", "MCP: tool `laya_model_info` (optional named model), JSON resource `laya://models`, Markdown resource `laya://model-guide`. Metadata does not load or switch a checkpoint. Use `laya_status` for live readiness/device; the static catalog is not runtime status.", "", "```powershell", 'Invoke-RestMethod http://localhost:8000/models.json', 'Invoke-RestMethod http://localhost:8000/api/v1/models/english/metadata -Headers @{Authorization="Bearer <LAYA_API_KEY>"}', "```", "", "```python", "import requests", 'catalog = requests.get("http://localhost:8000/models.json", timeout=10).json()', 'model = next(m for m in catalog["models"] if m["id"] == "multilingual")', 'print(model["tokens"], model["caveats"])', "```", "", "```javascript", 'const catalog = await fetch("http://localhost:8000/models.json").then(r => r.json());', 'console.log(catalog.models.find(m => m.id === "typed-decisions"));', "```", "", "POST an example body to `/api/v1/predict` with the bearer key. REST/MCP inference use the same worker. Browser examples work from the portal's origin; cross-origin browser access remains disabled. A cloud agent needs a network path to this computer.", "", "## Sources and update policy", "", catalog["provenance"], "", "Our raw benchmark and complete methods are in repository file `docs/benchmark/REPORT.md`; the authenticated `/api/v1/benchmark` endpoint provides saved aggregates. Run `scripts/build_model_catalog.py` only after reviewing a catalog update; it does not change runtime settings.", ""]
    lines += [f"- [{s['title']}]({s['url']}) — reviewed {REVIEWED}." for s in catalog["sources"]]
    (ROOT / "docs/models.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Built docs/models.json and docs/models.md without GPU work.")


if __name__ == "__main__":
    build()
