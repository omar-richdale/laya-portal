# Verification history on the RTX 4050

This page separates current documentation checks from historical GPU acceptance and the frozen real-data study. Dates matter: refreshing a screenshot does not rerun the accuracy benchmark.

## October 7, 2026 — documentation refresh

- Python suite: **36 tests passed** after the public operations/development routes were added.
- Production frontend: TypeScript and Vite build passed.
- Browser suite: **seven checks passed**, including two opt-in live CUDA requests, model learning without authentication, editors/exports, mobile reduced-motion layout and locally served assets.
- Actual REST/MCP check: authenticated CUDA predictions, six MCP tools, resource reads, REST/MCP answer equality, ordered batches, invalid-input rejection, unauthorized rejection and MCP origin rejection passed. New public operating/development guides returned successfully.
- Published client examples: Python HTTP, PowerShell HTTP, JavaScript HTTP and Python MCP all executed successfully.
- Model catalog: public/authenticated JSON and Markdown, per-model responses, MCP structured metadata/resources and unauthorized rejection passed. Metadata reads kept the resident English checkpoint, saved `auto` default and CUDA allocation unchanged.
- LAN-address status calls from this PC succeeded. Reachability from a second physical device was not newly tested.
- Seven production portal screenshots were captured with real Playground/Batch GPU calls, no browser fixtures, reduced motion, unchanged saved default, and no key in the artifacts. See [gallery and provenance](screenshots/README.md).

Local Markdown file links and screenshot manifest hashes were checked before publication; the actual API key was absent from publishable files. Raw current verification reports remain under ignored `data/verification/` and `frontend/test-results/`.

## October 1, 2026 — real-data benchmark and model guide

[The frozen report](benchmark/REPORT.md) covers 247 unique decision cases across all three checkpoints, repeated three times, plus batch and startup measurements. It distinguishes reference agreement from independent vulnerability accuracy and records the missed card-required trial policy. [The model guide](models.md) separates upstream capabilities, hosted limits and local evidence; its source-review date remains October 1.

## September 30, 2026 — initial acceptance

Hardware: NVIDIA GeForce RTX 4050 Laptop GPU, 6 GiB VRAM. Native Windows, Python 3.12.10, PyTorch 2.10.0+cu128. Checkpoint revision: `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`.

### Measured GPU checks

These are small synthetic requests, not an accuracy benchmark or a throughput promise.

| Case | Selected checkpoint | First request | Warm request | Reference answers match |
|---|---|---:|---:|---|
| English billing | English | 49,999.79 ms | 64.98 ms | Yes |
| French billing | Multilingual | 3,842.21 ms | 47.64 ms | Yes |
| Arabic billing | Multilingual already loaded | 50.75 ms | 49.30 ms | Yes |
| Typed request | Typed-decisions | 3,088.95 ms | 72.00 ms | Yes |

Cold timings include Windows disk/model initialization and first inference. Subsequent English reloads were around 7–8 seconds in live service checks. The mixed four-request GPU batch finished in 5,664.82 ms and preserved its English/multilingual/typed-decisions/English order.

Long-context multilingual checks succeeded at limits of 1,024, 4,096 and 8,192. Actual rendered input lengths were 880, 3,440 and 6,850 tokens respectively; warm long-input timings were 197.30 and 688.06 ms for the latter two. These did not consume every token in the limit. A deliberately overlong English state reported dropped tokens, truncation, and a user-visible warning. A confidence threshold of 1 flagged the tested answers as low-confidence.

The real browser playground returned `choice`, `score`, and `noul` results on `cuda:0`. Actual choice probabilities matched the reference GPU path. CPU retries are disabled in the production adapter; simulated GPU OOM tests verify propagation and cleanup.

### Service and browser checks

- 14 backend tests: validation, body limits, authentication, output schemas, saved-default persistence, failed loads, ordered batching, cancellation/admission limits, GPU OOM and no CPU retry.
- Browser checks: editing, JSON output, exports, batch/model controls, responsive mobile layout, reduced motion, escaped input and local assets.
- Live browser request and offline Swagger rendering.
- Actual REST/MCP: five tools, resource reads, structured outputs, prediction equality, ordered batches, tool errors and unauthorized rejection.
- LAN-address requests made from this PC succeeded; access from a separate device still depends on the Windows firewall rule.
- Runnable documentation: Python HTTP, PowerShell HTTP, backend JavaScript HTTP and MCP examples passed.
- Graceful stop/restart works. Serving sets Hub/Transformers offline flags and loads from local checkpoint directories.

Raw reports are under `data/verification/` and exclude credentials. The English checkpoint's invalid stored temperature for choice questions with 11+ options is recorded by the reference runtime and surfaced as a calibration notice; it was not silently changed by portal logic.
