# Laya Local

**Run three Laya decision models on your NVIDIA GPU, test them in a web portal, and call them from apps or AI agents.**

Inference uses Python + PyTorch. The React portal is built once and served by FastAPI. Everything runs locally after setup, with one checkpoint resident on the GPU and no CPU inference fallback.

![Live Laya playground showing structured decisions on CUDA](docs/screenshots/playground.png)

[Quick start](#quick-start) · [Models](#choose-a-model) · [API and agents](#connect-apps-and-ai-agents) · [Documentation](#documentation) · [Screenshots](docs/screenshots/README.md)

## What you can do

| Portal view | Use it to |
|---|---|
| **Playground** | Enter text or JSON; inspect typed answers, probabilities, latency and actual device. |
| **Batch testing** | Import/export JSON or JSONL, or open Decision lab to compare and replay 130 built-in cases. |
| **Models & GPU** | Inspect GPU memory and residency; change the persistent default. |
| **Model guide** | Learn capabilities, token budgets, limitations and measured results. No key needed to read it. |
| **Real benchmark** | Compare the frozen study and replay five understandable real examples. |
| **Integration** | Find REST, MCP, OpenAPI and fetchable agent documentation. |

Laya returns **decisions**, not generated prose or code:

- `choice`: choose a key from the options you define.
- `score`: return an expected ordinal level, which can be fractional.
- `noul`: return the probability that a statement is true.

A model answer can be wrong even at high confidence. Applications retain control of permissions, tools and review.

## Quick start

### First installation

The verified host is Windows with an **RTX 4050 Laptop GPU, 6 GiB VRAM**. Setup needs an NVIDIA driver, Python 3.12, `uv`, Node.js/npm and at least **10 GiB free disk space**. The locked Vite build accepts Node 20.19+ in the 20.x line or Node 22.12+. Other GPUs and operating systems are not covered by this machine's acceptance results.

```powershell
git clone https://github.com/omar-richdale/laya-portal.git
cd laya-portal
.\setup.ps1
.\start.ps1 -OpenBrowser
```

Setup installs locked dependencies into `.venv`, downloads all three pinned checkpoints, builds the frontend and creates `.env` with a random API key. It preserves global Python packages. Repository and model downloads need network access during setup.

Open **http://localhost:8000**. Enter `LAYA_API_KEY` from your local `.env` into the connection field. The key stays in the current tab; inputs/results stay in browser memory unless exported.

### Start it next time

On the existing installation:

```powershell
cd C:\Users\richd\Documents\oMAR\Laya
.\start.ps1 -OpenBrowser
```

Run `.\stop.ps1` to stop the managed process and release its GPU allocations. Use `.\start.ps1 -Foreground` to see logs in the terminal; Ctrl+C stops that foreground session. The service starts manually, not at sign-in.

**First prediction:** loading can take seconds or longer. Later requests reuse the resident checkpoint. Switching adds loading time. [Operation and troubleshooting](docs/operations.md) covers logs, keys, LAN access and errors.

## Choose a model

| API name | Good starting point | Approx. size | Default total / question tokens | Hosted maximum total |
|---|---|---:|---:|---:|
| `english` | English tickets, routing and classification | 421M | 512 / 192 | 512 |
| `multilingual` | French, Arabic and other multilingual inputs | 322M | 1,024 / 256 | 8,192 |
| `typed-decisions` | English invoice, security, support and agent-trace workflows | 421M | 1,024 / 256 | 1,024 |

Question/options share the total context with the state. Approximate state room at defaults is 320 / 768 / 768 tokens before formatting; actual room varies. Tokens are pieces of text, not words. Read truncation warnings.

- `auto` selects English or multilingual using language/script heuristics. It does not select typed-decisions automatically.
- Omit `model` to use the saved default. An explicit model overrides it for that request only.
- **Use as default** changes the shared saved setting after a named checkpoint loads successfully.

[Detailed model guide](docs/models.md) · [JSON catalog](docs/models.json) · [Live guide](http://localhost:8000/model-guide)

## Connect apps and AI agents

**Base URL:** `http://localhost:8000`. Protected calls require `Authorization: Bearer <LAYA_API_KEY>`.

| Interface | Address |
|---|---|
| Prediction | `POST /api/v1/predict` |
| Ordered batch, up to 32 requests | `POST /api/v1/predict/batch` |
| Live readiness, device and memory | `GET /api/v1/status` |
| Model listing / detailed metadata | `GET /api/v1/models` / `GET /api/v1/model-metadata` |
| Streamable HTTP MCP | `/mcp/` |
| Swagger / OpenAPI | `/docs` / `/openapi.json` |
| Public agent discovery | `/llms.txt` |
| Public model learning data | `/docs/models.md` / `/models.json` |

Six MCP tools share the same worker: `laya_predict`, `laya_predict_batch`, `laya_models`, `laya_model_info`, `laya_status` and `laya_set_default_model`. Resources include `laya://integration`, `laya://architecture`, `laya://models` and `laya://model-guide`.

[The agent guide](docs/agents.md) has runnable Python, PowerShell, JavaScript and MCP clients. [The API contract](docs/api.md) gives endpoints, schemas, limits and errors.

Another trusted LAN device uses the server PC's address printed by `start.ps1`, the same key, and the optional local-subnet firewall rule. Third-party browser origins are disabled. A cloud agent needs a network path to this PC. [LAN setup](docs/operations.md#use-it-on-your-local-network)

## Try the examples

In **Batch testing → Decision lab**, explore the recorded everyday comparison, choose any of six suites and three checkpoints, and rerun the tests on your GPU. Tables show reference accuracy, median/p95 inference, HTTP timing, warm-up time and confidence coverage. Inspect individual decisions, policies and confusion tables; export results or a suite's requests. The saved comparison remains available alongside your latest run. A full replay scores 390 decisions plus three excluded warm-ups. These are synthetic English-only cases with custom moderation policies; image/video suites classify text prompts only.

Start the service, then run:

```powershell
# Choose a checkpoint and replay a real issue or QA example.
.\.venv\Scripts\python.exe examples\real_workflows.py

# Choose a synthetic QA, prompt-injection or action-alignment scenario.
.\.venv\Scripts\python.exe examples\run.py
```

Clients find `.env` relative to their own files and print results, probabilities, device and timings. They do not execute repair tools. See [examples/README.md](examples/README.md) for comparisons and commands.

## Measured results

On **October 1, 2026**, all three checkpoints were tested on the RTX 4050 against **247 unique decision cases**: 233 issue-workflow cases, seven overlapping security-topic cases and seven QA observations. Each model ran three passes.

| Checkpoint | Issue-workflow reference matches | Security topic / 7 | QA cause / 7 | Warm service median |
|---|---:|---:|---:|---:|
| English | 225 / 233 | 4 | 4 | 61.53 ms |
| Multilingual | 170 / 233 | 3 | 0 | 51.43 ms |
| Typed-decisions | 222 / 233 | 7 | 4 | 63.27 ms |

These are reference matches on a fixed local corpus, not production accuracy. Always choosing the dominant dependency category already matches 196/233 issues. All three models missed the intentional credit-card requirement in a QA case. The local Sift, Bugsmith and QA integrations therefore provide **optional advisory metadata**, preserving existing verification and execution policies.

[Full benchmark report](docs/benchmark/REPORT.md) · [Integration boundaries](docs/system-one-integrations.md) · [Validation history](docs/verification.md)

## Documentation

| Guide | Contents |
|---|---|
| [Documentation index](docs/README.md) | Find the right guide for your task. |
| [Operations](docs/operations.md) | Start/stop, settings, keys, logs, LAN and troubleshooting. |
| [Models](docs/models.md) | Capabilities, tokens, architecture, measurements and sources. |
| [API and agents](docs/agents.md) | Authentication, REST/MCP examples and guidance. |
| [Architecture](docs/architecture.md) | Shared GPU worker, lifecycle and Mermaid diagrams. |
| [Development](docs/development.md) | Build, test, verify and refresh screenshots. |
| [Screenshots](docs/screenshots/README.md) | Seven live portal captures with provenance. |
| [Integration diagrams](docs/diagrams/README.md) | Laya, Sift, Bugsmith and VPN QA illustrations. |
| [Presentation](docs/presentation/v1/README.md) | Twelve slides, PowerPoint, PDF and reusable prompts. |

Runtime pins: **Laya 0.3.22, PyTorch 2.10.0+cu128, Transformers 4.57.6, MCP 2.2.0**. Checkpoint revision: `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`. Node builds the frontend; Python owns inference. React Bits and Font Awesome Free assets and notices are bundled locally.

Model source information was reviewed October 1; screenshots and documentation checks were refreshed October 7. Fine-tuning, domain calibration and public internet hosting are outside this version.
