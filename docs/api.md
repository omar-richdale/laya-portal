# HTTP API contract

All `/api/v1/*` routes require an exact `Authorization: Bearer <LAYA_API_KEY>` header. The default port is 8000. Schemas are generated at `/openapi.json`; interactive docs are at `/docs`.

| Method | Path | Contract |
|---|---|---|
| POST | `/api/v1/predict` | One prediction request → upstream result plus runtime metadata |
| POST | `/api/v1/predict/batch` | `{requests: [prediction,...], batch_size: 1 or 2, sort_by_length: true}` → `{results: [...], runtime: {...}}` |
| GET | `/api/v1/models` | Saved default, resident model, downloaded checkpoint list and context budgets |
| GET | `/api/v1/model-metadata` | Reviewed capabilities and detailed offline metadata for all three checkpoints |
| GET | `/api/v1/models/{model}/metadata` | Detailed learning metadata for one named checkpoint; auto is routing mode |
| PUT | `/api/v1/settings/model` | `{model: "auto" or checkpoint name}` → updated model listing |
| GET | `/api/v1/status` | Actual device, lifecycle phase, queue depth, GPU memory, versions and latest error |
| POST | `/api/v1/shutdown` | `{}` → request graceful shutdown of the managed process; accepted work drains first |

## Prediction request

Required: `state` (text, JSON object or list) and `questions` (mapping of question IDs to definitions). Optional: `model`, `max_len`, `head_max_len`, `min_confidence`.

- Model names: `auto`, `english`, `multilingual`, `typed-decisions`. Omitted model captures the saved default when the job is admitted.
- Question IDs: 1–128 characters. Instructions: 1–4,000 characters.
- `choice`: `criteria` maps 1–100 nonblank labels to descriptions.
- `score`: `criteria` is an ordered list of 2–32 nonblank descriptions.
- `noul`: no criteria; answers give probability of yes.
- 1–64 questions, at most 512 total options, at most 50,000 serialized state characters.
- Request body limit: 4 MiB, checked before JSON parsing. Duplicate keys and nonfinite JSON numbers are rejected.
- `max_len`: integer 64–8,192 subject to checkpoint caps (512 English, 1,024 typed-decisions, 8,192 multilingual). `head_max_len`: integer 16–1,024 and must leave at least eight tokens for state.
- `min_confidence`: number 0–1. This flags answers; it does not replace them with a guessed value.
- Unknown request fields are rejected. Batch list limit: 32; outstanding GPU jobs including the active job: eight.

## Results

`answers`, `model`, `routing`, and `usage` preserve upstream fields. `runtime` adds `device`, pinned `revision`, total `elapsed_ms` (load + inference, excluding queue wait), resident checkpoint `load_ms`, and `warnings` for truncated state/collapsed options. Batch total elapsed time covers its grouped work; each result carries elapsed time through completion in that batch.

`choice` answers include a label and `probabilities` mapping. `score` answers include an expected ordinal score and distribution across levels. `noul` is P(yes). Every answer also has upstream confidence fields. See `/docs/agents.md` for their limitations.

No server-side history is saved. Settings, download metadata and verification reports are local files. Runtime errors have a stable code and message; submitted state is not echoed in validation errors. See the integration guide for status codes and retry behavior.

## Advisory workflows and recorded benchmark

`POST /api/v1/workflows/{workflow}` uses `issue_lane`, `security_specialist` or `qa_cause`; JSON body contains non-empty `state`, optional `model`, optional `min_confidence`. Questions and 512/192 budgets are fixed. The response adds `advice` with a readable label, answer_confidence, review_required, advisory_only=true and authorization=false. All normal authentication, queue, validation and GPU-error rules apply. See `/docs/system-one-integrations.md`.

`GET /api/v1/benchmark` is authenticated and returns saved aggregate metrics and five replayable inputs; it performs no inference.


## Learning metadata

`GET /models.json` and `GET /docs/models.md` are public learning documents, distinct from protected inference/runtime endpoints. Catalog schema 1.0 includes a review date, pinned revision, family primitives, hosted service policy, three model entries, aggregate local benchmark evidence and primary source URLs. Read the date/provenance before treating a published claim as a current local capability. `/api/v1/model-metadata` returns the same catalog with bearer authentication; `/api/v1/models/{model}/metadata` filters its `models` list to one named checkpoint. Invalid names and `auto` return 422. Metadata fetches do not load or switch a model.

Generic operating and development instructions are available at `/docs/operations.md` and `/docs/development.md`. `/llms.txt` links the fetchable Markdown guides. Repository-only screenshots, presentation files and curated benchmark artifacts are linked from the GitHub README rather than exposed as public runtime routes.
