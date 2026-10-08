# Build, verify and maintain the repository

Run PowerShell commands from the repository root unless stated otherwise. The runtime is pinned in `pyproject.toml`/`uv.lock`; do not upgrade Laya without reviewing the version-bound GPU-only adapter.

## Code map

| Location | Responsibility |
|---|---|
| `laya_portal/app.py` | FastAPI routes, authentication, public docs and static frontend. |
| `laya_portal/service.py`, `gpu.py` | Bounded single worker, checkpoint lifecycle and CUDA-only inference. |
| `laya_portal/mcp_api.py` | MCP tools/resources sharing the service lifespan. |
| `laya_portal/model_catalog.py`, `docs/models.json` | Cached, versioned model learning metadata. |
| `laya_portal/workflows.py`, `benchmark.py` | Fixed advisory questions and frozen benchmark access. |
| `laya_portal/decision_suite.py`, `frontend/src/DecisionLab.tsx` | Authenticated everyday study catalog and selectable live replay under Batch testing. |
| `frontend/src/` | React dashboard, model guide and real-example replay. |
| `examples/` | Runnable HTTP, workflow, benchmark and advisory clients. |
| `scripts/` | Setup support, verification, corpus and documentation tooling. |
| `tests/`, `frontend/tests/` | Python tests and Playwright checks. |

## Build and test

```powershell
# Isolated locked Python environment, created by setup.
uv sync --locked --python 3.12
.\.venv\Scripts\python.exe -m pytest -q

cd frontend
npm ci
npm run build
npm test
cd ..
```

The production frontend build is served from `frontend/dist`. Start the Python service before Playwright: tests use `http://127.0.0.1:8000` and installed Microsoft Edge. Most browser checks use deterministic API fixtures. Enable the separate real CUDA checks explicitly:

```powershell
cd frontend
$env:LAYA_LIVE_TEST = '1'
npm test
Remove-Item Env:LAYA_LIVE_TEST
cd ..
```

For UI development, `npm run dev` starts Vite on localhost. Its configured proxy forwards API, documentation and model-catalog requests to the Python service; MCP clients connect directly to Python's port 8000. Vite does not run inference. Build again before capturing production screenshots.

## Live verification

With the service running:

```powershell
.\.venv\Scripts\python.exe scripts\verify_model_catalog.py
.\.venv\Scripts\python.exe scripts\verify_docs.py
.\.venv\Scripts\python.exe scripts\verify_http.py
```

The catalog check reads public/authenticated REST metadata and MCP tools/resources, checks unauthorized rejection, and verifies that residency, default and CUDA allocations stay unchanged. The documentation check executes the Python, PowerShell, JavaScript and MCP code blocks in `docs/agents.md`. The HTTP check exercises inference, routing, ordered batching, errors and MCP; it temporarily changes the saved default and restores it. These clients read credentials internally and write reports under ignored `data/verification/`.

For direct reference-versus-adapter GPU verification, stop the service first and run `scripts/verify_gpu.py` with the project Python. That script creates its own GPU agents. Do not compete with the production worker for the RTX 4050's VRAM. `scripts/verify_context.py` instead calls the running service to check supported token budgets/truncation. Record new measurements with their date; preserve the distinction between initial acceptance and the frozen real-data benchmark.

## Refresh portal screenshots

Start the service, then:

```powershell
cd frontend
npm run screenshots
cd ..
```

`frontend/scripts/capture-docs.mjs` resolves `.env` relative to its own file, opens a temporary headless Edge session, connects to the actual production portal and runs real CUDA requests. It captures seven desktop/mobile views in `docs/screenshots/` and writes a timestamped manifest with file hashes, device/revision and captions. It uses reduced motion and disables animations for captures. It does not save a browser profile, trace or API key. Explicit per-request models preserve the saved service default.

Review the resulting PNGs before committing. They contain example input/output and measured request timings; a first-load screenshot is not a warm latency benchmark. Update the gallery date/captions and verification page when refreshing them. [Current gallery](screenshots/README.md).

## Maintain the model catalog

`scripts/build_model_catalog.py` generates `docs/models.json` and `docs/models.md` from pinned local checkpoint configurations/headers and the frozen benchmark. Inspect its source-review date and source references before changing them; rebuilding alone is not a new internet/source review. Run it with the project Python after intentional metadata changes, review the output, and restart the service because the catalog loader caches it in-process.

Metadata reads do not load a checkpoint. Source claims, hosted limits and measured local results are distinct fields. Keep all three aligned with the reference runtime and service validation. Never present an encoder's positional capacity as a guarantee of supported inference quality or available VRAM.

## Benchmark and sibling adapters

The everyday Decision lab uses `docs/benchmark/everyday-fixtures.json` as the shared case source for the CLI and portal. `everyday-baseline.json` holds a compact snapshot of the October 8 measured run; fresh UI runs never replace it. Preserve dictionary insertion order for answer criteria: sorting JSON keys can change the model's predictions. The API checks both an order-insensitive fixture hash and an order-sensitive request hash against the baseline. `tests/test_decision_suite.py` verifies authentication, reference withholding, fixture identity and recorded counts. Browser checks cover scores, warm-up exclusion, exports, partial stop/failure and mobile layout. With `LAYA_LIVE_TEST=1`, the Decision lab browser check replays the entire 390-prediction study through the production UI. `examples/everyday_decisions.py` remains the CLI alternative and writes new full reports under ignored `data/examples/`.

[The benchmark report](benchmark/REPORT.md) records the October 1 corpus, references, results and limitations. `examples/benchmark_real.py` runs real GPU measurements and may replace the checked-in result files; archive an earlier study before intentionally rerunning. `examples/real_workflows.py` replays individual examples without rebuilding the corpus.

Optional native integrations live in sibling checkouts under `../Agentic-production`. Their review patches and replay evidence are stored in `docs/benchmark/`; do not blindly reapply patches already installed there. They remain advisory and opt-in. Updating this Laya repository does not publish sibling changes or deploy their services. See [integration boundaries](system-one-integrations.md).

## Files to keep private/local

Do not commit `.env`, checkpoint weights, raw report downloads, runtime logs, browser traces or local settings. `.gitignore` excludes those and local Obsidian workspace settings. The checked-in benchmark is a curated project artifact; the repository is private. Keep any additional exports within the authorized project and review them before publication.

`.gitattributes` preserves generated PDF/PowerPoint/image bytes and LF for hashed benchmark data on Windows. Keep these rules: newline conversion can invalidate PDF offsets or corpus hashes. Unified-diff packets retain their required blank context-line prefix.
