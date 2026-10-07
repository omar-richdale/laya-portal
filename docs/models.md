# Hosted Laya model guide

Reviewed 2026-10-01. Catalog schema 1.0. Offline checkpoint revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`.

A bidirectional encoder and decision head score request-defined options in one forward pass. Outputs are choice, ordinal score or yes-probability; no generated prose, code patches or free-form extraction.

[Machine-readable catalog](/models.json) · [API contract](/docs/api.md) · [Integration guide](/docs/agents.md)

## Choose a checkpoint

| Model | Parameters (approx.) | Total default | Question/options budget | Approximate state before formatting | Hosted maximum |
|---|---:|---:|---:|---:|---:|
| English | 421M | 512 | 192 | 320 | 512 |
| Multilingual | 322M | 1024 | 256 | 768 | 8192 |
| Typed decisions | 421M | 1024 | 256 | 768 | 1024 |

All counts are tokens, not words. Approximate state room is not an exact allowance. Encoder configs list 8,192 positions for all three backbones; this service deliberately exposes only the hosted limits above.

## English (`english`)

Start here for short English tickets and bounded classification questions.

**Candidate uses:** English email or support-ticket routing; Small-label intent, topic and sentiment decisions; Candidate guardrail signals, evaluated on your own examples.

**Languages:** Prefer multilingual for non-English input; English confidence can remain high on an unreadable language.

**Architecture:** `answerdotai/ModernBERT-large`, 28 encoder layers, hidden size 1024, 16 attention heads, vocabulary 50,368, 2-layer decision head. Local weight file 803.57 MiB (excludes tokenizer/configs and runtime memory). CUDA autocast `bf16`; stored types F16, F32. Apache-2.0. Knowledge cutoff is not published.

**Published evidence:** The family card recommends English classification, guardrails and email triage. Those are candidate uses, not validated security guarantees.

**Local guidance:** Best issue-lane agreement in our English backlog snapshot. Existing scanner metadata is still the first routing source.

**Measured RTX 4050 evidence:**
- issue_lane: 225/233 reference matches; macro F1 0.7222; review 204/233.
- qa_cause: 4/7 reference matches; macro F1 0.2424; review 7/7.
- security_specialist: 4/7 reference matches; macro F1 0.3889; review 7/7.
- Warm service median/p95: 61.53/76.52 ms. HTTP median/p95: 64.36/80.38 ms.
- 32-state batch, microbatch two: 1132.47 ms; 28.26 states/sec.
- One fresh-process sample: first call 7027.08 ms, load 6448.45 ms; allocator peak 2.286 GiB.

247 unique cases: 233 issue lanes, seven security topics, seven QA observations. Three repeated passes; quality uses first pass. Fixed label order. Reference agreement, not independent vulnerability or production accuracy. All three missed the card-required trial. Baseline: always dependency matches 196/233 (84.12%). Startup is one fresh-process sample, not a percentile or cold boot. Allocator peak excludes other processes and CUDA/display overhead.

**Checkpoint caveats:**
- Stored choice:11+ temperature is 0.10058; Laya 0.3.22 clamps it to 0.5 and emits a warning.
- A confident output can still be wrong. Our synthetic action-alignment examples matched only 1/6 references.
- Our real QA cases matched 4/7; it missed the card-required trial contract.

**Runnable request body:**

```json
{
  "state": "I was charged twice for my VPN subscription. Please refund the duplicate payment.",
  "questions": {
    "team": {
      "type": "choice",
      "instructions": "Which team should review this ticket?",
      "criteria": {
        "A": "billing: invoices, duplicate payments or refund requests",
        "B": "technical support: broken apps or connectivity",
        "C": "sales: pricing or new subscriptions"
      }
    }
  },
  "model": "english",
  "min_confidence": 0.8
}
```

Sources: [Laya family model card](https://huggingface.co/convaiinnovations/laya/blob/main/README.md), [Upstream benchmark limitations](https://nandhakishorm.github.io/laya/benchmarks/), [Pinned english configuration](https://huggingface.co/convaiinnovations/laya/blob/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/rl_agent_config.json).

## Multilingual (`multilingual`)

Use for French, Arabic and other languages, or longer compact evidence.

**Candidate uses:** Routing and classification of non-English tickets; French or Arabic support queues with English question descriptions; Longer state inputs when essential evidence does not fit the shorter checkpoints.

**Languages:** Upstream claims 100+ languages; coverage and accuracy vary by language and task. Our backlog benchmark was English, not a multilingual-quality evaluation.

**Architecture:** `jhu-clsp/mmBERT-base`, 22 encoder layers, hidden size 768, 12 attention heads, vocabulary 256,000, 2-layer decision head. Local weight file 614.01 MiB (excludes tokenizer/configs and runtime memory). CUDA autocast `bf16`; stored types F16, F32. Apache-2.0. Knowledge cutoff is not published.

**Published evidence:** The model card describes 100+ languages and a 1,024-token default expandable to 8,192. Coverage does not guarantee useful accuracy in every language. Published language-sweep numbers have been revised; consult the current benchmark's correction notes.

**Local guidance:** Use for language coverage. It was fastest in our compact benchmark, but less accurate on the English backlog.

**Measured RTX 4050 evidence:**
- issue_lane: 170/233 reference matches; macro F1 0.6202; review 228/233.
- qa_cause: 0/7 reference matches; macro F1 0.0; review 7/7.
- security_specialist: 3/7 reference matches; macro F1 0.2; review 4/7.
- Warm service median/p95: 51.43/67.56 ms. HTTP median/p95: 54.4/70.95 ms.
- 32-state batch, microbatch two: 900.52 ms; 35.54 states/sec.
- One fresh-process sample: first call 9003.82 ms, load 8380.26 ms; allocator peak 1.480 GiB.

247 unique cases: 233 issue lanes, seven security topics, seven QA observations. Three repeated passes; quality uses first pass. Fixed label order. Reference agreement, not independent vulnerability or production accuracy. All three missed the card-required trial. Baseline: always dependency matches 196/233 (84.12%). Startup is one fresh-process sample, not a percentile or cold boot. Allocator peak excludes other processes and CUDA/display overhead.

**Checkpoint caveats:**
- Pinned config has temperatures [1, 1, 1] and no option-count buckets: it ships without fitted calibration.
- A longer accepted context is not proof of long-document accuracy or safe memory use.
- Our real QA cases matched 0/7; two issue-lane mistakes exceeded the 0.8 review threshold.

**Runnable request body:**

```json
{
  "state": "تم تحصيل رسوم اشتراك VPN مرتين. أرجو إعادة المبلغ المكرر.",
  "questions": {
    "team": {
      "type": "choice",
      "instructions": "Which team should review this Arabic ticket?",
      "criteria": {
        "A": "billing: duplicate charges and refunds",
        "B": "technical support: connection failures",
        "C": "sales: new subscriptions"
      }
    }
  },
  "model": "multilingual",
  "min_confidence": 0.8
}
```

Sources: [Multilingual model card](https://huggingface.co/convaiinnovations/laya-multilingual/blob/main/README.md), [Upstream benchmark limitations](https://nandhakishorm.github.io/laya/benchmarks/), [Pinned multilingual configuration](https://huggingface.co/convaiinnovations/laya/blob/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/multilingual/rl_agent_config.json).

## Typed decisions (`typed-decisions`)

An English specialist for invoice, security, support and agent-trace decisions.

**Candidate uses:** Invoice-processing decisions with fixed fields or categories; Security-incident and customer-service triage; Agent-trace observability: choosing among a small set of known outcomes.

**Languages:** Upstream documents English-only fine-tuning; choose multilingual for other languages.

**Architecture:** `answerdotai/ModernBERT-large`, 28 encoder layers, hidden size 1024, 16 attention heads, vocabulary 50,368, 2-layer decision head. Local weight file 803.57 MiB (excludes tokenizer/configs and runtime memory). CUDA autocast `bf16`; stored types F16. Apache-2.0. Knowledge cutoff is not published.

**Published evidence:** Upstream reports fine-tuning on 1,200 training cases (6,000 decisions), then 400 test cases (2,000 decisions) across four workflows. This is a benchmark-specific specialist result, not general production accuracy. Its confidence needs independent held-out calibration.
- Typed-decisions accuracy: 0.766
- Invoice processing accuracy: 0.804
- Security incidents accuracy: 0.766
- Customer service accuracy: 0.764
- Agent-trace accuracy: 0.73
- Expected calibration error (lower is better): 0.213

**Local guidance:** Promising for security-topic hints: 7/7 references in our small sample, all below the 0.8 review threshold. This does not establish reliable prompt-injection detection or action authorization.

**Measured RTX 4050 evidence:**
- issue_lane: 222/233 reference matches; macro F1 0.6526; review 233/233.
- qa_cause: 4/7 reference matches; macro F1 0.2667; review 7/7.
- security_specialist: 7/7 reference matches; macro F1 1.0; review 7/7.
- Warm service median/p95: 63.27/79.02 ms. HTTP median/p95: 66.32/82.15 ms.
- 32-state batch, microbatch two: 1126.44 ms; 28.41 states/sec.
- One fresh-process sample: first call 7966.35 ms, load 7393.04 ms; allocator peak 2.286 GiB.

247 unique cases: 233 issue lanes, seven security topics, seven QA observations. Three repeated passes; quality uses first pass. Fixed label order. Reference agreement, not independent vulnerability or production accuracy. All three missed the card-required trial. Baseline: always dependency matches 196/233 (84.12%). Startup is one fresh-process sample, not a percentile or cold boot. Allocator peak excludes other processes and CUDA/display overhead.

**Checkpoint caveats:**
- Specialized on four synthetic workflows; transfer to new domains is unproven.
- Inherited option-count temperatures override per-type values. The stored choice:11+ bucket also requires the runtime clamp.
- Upstream warns its per-type calibration used training items. Treat current probabilities as uncalibrated for your domain.
- Our QA cases matched 4/7 and missed the card-required trial; synthetic action alignment matched 1/6.

**Runnable request body:**

```json
{
  "state": {
    "incident": "A deployment used a token that was revoked. The API returned 401. No successful access is recorded.",
    "evidence": "revoked-token request rejected"
  },
  "questions": {
    "topic": {
      "type": "choice",
      "instructions": "Which specialist should inspect this incident? Do not infer a successful attack without evidence.",
      "criteria": {
        "A": "authentication and session handling",
        "B": "billing and invoice processing",
        "C": "network availability"
      }
    }
  },
  "model": "typed-decisions",
  "min_confidence": 0.8
}
```

Sources: [Typed-decisions model card](https://huggingface.co/convaiinnovations/laya-typed-decisions/blob/main/README.md), [Upstream benchmark limitations](https://nandhakishorm.github.io/laya/benchmarks/), [Pinned typed-decisions configuration](https://huggingface.co/convaiinnovations/laya/blob/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/typed-decisions/rl_agent_config.json).

## Outputs and budgets

- `choice`: Selects the highest-probability key from your criteria object; returns per-key probabilities.
- `score`: Returns the expected zero-based ordinal level, potentially fractional, plus level probabilities and legend; not a free-form numeric calculation.
- `noul`: Returns P(true) between 0 and 1; no criteria or custom boolean labels are accepted by this hosted API.

## Token budgeting

- Tokens are tokenizer pieces, not words or characters. JSON keys, punctuation, instructions and choice descriptions count.
- max_len covers the full sequence for each question. head_max_len budgets question/options within it. Approximate state room assumes a full head; actual room varies with formatting and special markers.
- Long text/objects retain their beginning; JSON conversation lists retain the end. Check usage.truncated, state_tokens_dropped and truncated_questions before relying on a decision.
- Each option description is initially capped at 48 tokens in the pinned runtime; crowded choices can be shortened further. Inspect option-distinctness warnings. Increasing total context alone does not expand the choice budget.
- The API validates head_max_len < max_len - 8. max_len can be 64..8192 globally, but the selected checkpoint's smaller hosted cap still applies.
- auto with a large context can route to English and be rejected. Explicitly choose multilingual for max_len above 1024.
- Accepted limits are not throughput/VRAM guarantees. More questions, options, longer contexts and batches increase memory and latency.

## Confidence and review

- answer_confidence is the largest option probability. For noul this is max(P(true), 1-P(true)). For score it refers to a modal level, not a guarantee that the fractional expected score is correct.
- Legacy confidence on choice/score is normalized entropy and is not the same quantity. action.act_probability is learned act/escalate evidence, not tool authorization.
- min_confidence only adds low_confidence=true below your threshold; it keeps the answer and does not enforce review or block execution. Fixed workflow adapters separately attach advisory review metadata.
- Our fixed workflows use 0.8 for review, but that threshold has not been calibrated for production. All seven real QA cases and all seven typed security-topic cases required review.

## Using a model well

- Supply only relevant, redacted evidence and a trusted product contract. Give a clear decision question and distinct short descriptions.
- Prefer a small shortlist; include unknown/review where the task allows it. Use neutral A/B keys to cross-check unreliable yes/no answers.
- Test wording, option order and each question type on held-out domain data; probabilities can be confident and wrong.
- Keep scanner facts, application permissions and test outcomes authoritative. Prompt-injection and misalignment screening are candidate advisory experiments, not proven defenses.

## Hosted service contract

auto selects English or multilingual using upstream language/script heuristics; typed-decisions requires explicit selection. Omitted model uses saved default. Per-request model never changes it.

CUDA only; no CPU retry. One checkpoint resident; one serialized worker. Compilation and TileLang disabled.

```json
{
  "max_questions": 64,
  "max_choice_options": 100,
  "max_score_levels": 32,
  "max_total_options": 512,
  "max_state_serialized_characters": 50000,
  "max_batch_requests": 32,
  "max_microbatch_states": 2,
  "max_outstanding_jobs": 8,
  "max_body_bytes": 4194304
}
```

401 authentication; 422 validation/budget; 503 busy with Retry-After: 2 or runtime/GPU errors. Inspect error.code; only queue saturation warrants an unchanged automatic retry.

Inference is local and offline after setup. Portal keys are tab-scoped; inputs/results stay in browser memory unless exported. Runtime logs may contain model/error diagnostics. Metadata fetches do not load a checkpoint.

Upstream SDK features **not exposed** by this server: predict_long sliding-window aggregation; decide JSON Schema / Pydantic convenience methods; arbitrary Python hooks, custom noul labels and lang/lang_guess request controls; fine-tuning or calibration training endpoints.

## Fetch from an agent

Public, credential-free metadata: `GET /models.json` and `GET /docs/models.md`. These files contain learning information and aggregate measurements, never credentials, runtime status or raw issue inputs.

Authenticated metadata: `GET /api/v1/model-metadata`, or `GET /api/v1/models/{english|multilingual|typed-decisions}/metadata`. Send `Authorization: Bearer <LAYA_API_KEY>`.

MCP: tool `laya_model_info` (optional named model), JSON resource `laya://models`, Markdown resource `laya://model-guide`. Metadata does not load or switch a checkpoint. Use `laya_status` for live readiness/device; the static catalog is not runtime status.

```powershell
Invoke-RestMethod http://localhost:8000/models.json
Invoke-RestMethod http://localhost:8000/api/v1/models/english/metadata -Headers @{Authorization="Bearer <LAYA_API_KEY>"}
```

```python
import requests
catalog = requests.get("http://localhost:8000/models.json", timeout=10).json()
model = next(m for m in catalog["models"] if m["id"] == "multilingual")
print(model["tokens"], model["caveats"])
```

```javascript
const catalog = await fetch("http://localhost:8000/models.json").then(r => r.json());
console.log(catalog.models.find(m => m.id === "typed-decisions"));
```

POST an example body to `/api/v1/predict` with the bearer key. REST/MCP inference use the same worker. Browser examples work from the portal's origin; cross-origin browser access remains disabled. A cloud agent needs a network path to this computer.

## Sources and update policy

Published capability summaries were reviewed on the stated date and may change upstream. Local configs, hosted constraints and measured evidence describe the pinned installation. Guides do not update weights or perform network requests at runtime.

Our raw benchmark and complete methods are in repository file `docs/benchmark/REPORT.md`; the authenticated `/api/v1/benchmark` endpoint provides saved aggregates. Run `scripts/build_model_catalog.py` only after reviewing a catalog update; it does not change runtime settings.

- [Laya family model card](https://huggingface.co/convaiinnovations/laya/blob/main/README.md) — reviewed 2026-10-01.
- [Multilingual model card](https://huggingface.co/convaiinnovations/laya-multilingual/blob/main/README.md) — reviewed 2026-10-01.
- [Typed-decisions model card](https://huggingface.co/convaiinnovations/laya-typed-decisions/blob/main/README.md) — reviewed 2026-10-01.
- [Upstream benchmark limitations](https://nandhakishorm.github.io/laya/benchmarks/) — reviewed 2026-10-01.
- [Upstream benchmark tables and corrections](https://github.com/NandhaKishorM/laya/blob/main/BENCHMARKS.md) — reviewed 2026-10-01.
- [Upstream Agent API](https://nandhakishorm.github.io/laya/reference/agent/) — reviewed 2026-10-01.
- [Upstream schema-driven decisions](https://nandhakishorm.github.io/laya/structured/) — reviewed 2026-10-01.
- [Upstream staged adoption](https://nandhakishorm.github.io/laya/staged-adoption/) — reviewed 2026-10-01.
- [Pinned english configuration](https://huggingface.co/convaiinnovations/laya/blob/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/rl_agent_config.json) — reviewed 2026-10-01.
- [Pinned multilingual configuration](https://huggingface.co/convaiinnovations/laya/blob/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/multilingual/rl_agent_config.json) — reviewed 2026-10-01.
- [Pinned typed-decisions configuration](https://huggingface.co/convaiinnovations/laya/blob/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/typed-decisions/rl_agent_config.json) — reviewed 2026-10-01.
