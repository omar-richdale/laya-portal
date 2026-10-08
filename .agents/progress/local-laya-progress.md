# Local Laya implementation

## Metadata
- Scope: Windows CUDA service, React portal, HTTP/MCP integration, agent documentation
- Status: awaiting Windows firewall approval
- Owner: agent
- Started: 2026-09-30
- Last updated: 2026-09-30
- Related areas: inference, API, frontend, setup

## Objective
Implement the approved plan and verify all three checkpoints on the RTX 4050.

## Current understanding
- Empty workspace. Existing global PyTorch is CPU-only; preserve it.
- Python 3.12.10, Node 22.19.0, uv, Git available; approximately 23 GiB free on C.
- One GPU checkpoint at a time; CPU inference forbidden. Reference Agent has implicit CPU retries.
- On-demand startup, local-network bearer authentication, persistent default auto routing.
- Expressive dark React Bits dashboard and locally bundled Font Awesome Free icons.

## Progress log
### 2026-09-30
- Summary: Started implementation after approval.
- Actions taken: Created isolated project manifest and progress record; selected pinned runtime.
- Validation: Planning-time dependency dry-run passed; hardware and tools inspected.
- Status: in progress
- Next steps: Install environment, implement shared worker/API/MCP/UI, download and verify checkpoints.

### 2026-09-30 — resumed after computer restart
- Summary: CUDA environment, dependency lock, all 15 checkpoint artifacts and frontend dependencies survived the restart.
- Actions taken: Recovered existing state; implemented dashboard and styling; corrected vendor component directory.
- Findings: Available disk space increased to about 48 GiB; RTX 4050 has about 4.5 GiB available after restart.
- Files touched: frontend/src, backend, scripts, locks.
- Validation: Previously verified torch 2.10.0+cu128 sees the RTX 4050; GPU inference still pending.
- Status: in progress
- Next steps: Build UI, smoke-test all checkpoints, test REST/MCP, write documentation and acceptance checks.

### 2026-09-30 — acceptance verification
- Summary: Backend, production dashboard, REST/MCP, documentation and scripts implemented; all checkpoints verified on CUDA with reference equality.
- Actions taken: Built React Bits/Font Awesome portal, bundled Swagger assets, added graceful shutdown, typed response envelopes and calibration notices.
- Findings: Warm small requests roughly 48–72 ms; first English load about 50 seconds; subsequent model loads a few seconds. Multilingual limits through 8,192 work; truncation and confidence metadata verified.
- Validation: 14 backend tests, 3 fixture browser tests, real GPU browser request, real REST/MCP equality/tools/resources/batch/errors, four documentation examples, graceful stop/restart. Live Swagger assertion fixed to match the versioned heading.
- Status: awaiting final validation
- Next steps: Final restart/recheck after warning text change; LAN firewall rule requires Windows admin approval, asked asynchronously. Optional empty staging-folder cleanup blocked by policy and left in place.

### 2026-09-30 — ready to use locally
- Summary: Final source is installed and running at localhost:8000; saved default is auto.
- Validation: Final 14 backend tests passed; all browser checks including real CUDA output and offline Swagger passed. Restarted with offline Hub/Transformers flags and verified real CUDA prediction and verification documentation. Python, PowerShell, JavaScript and MCP examples execute successfully.
- Findings: Wi-Fi LAN address at verification is 192.168.11.104. LAN-address requests from this PC pass, but separate-device access is not verified until the Windows firewall rule is added.
- Status: awaiting Windows firewall approval
- Next steps: User may approve the elevation prompt or run enable-lan.ps1 as Administrator. No further app/inference work remains. API key is only in .env; never print it in a report.

### 2026-09-30 — repository publication
- Summary: User requested local Git initialization, a source commit, and publication to omar-richdale/laya-portal.
- Actions taken: Initialized main and configured the requested HTTPS origin; confirmed the remote is empty and private and GitHub authentication is available.
- Files touched: .gitignore excludes TypeScript build metadata and Python package metadata alongside secrets, model weights, environments, runtime data and reports.
- Validation: 57 source/documentation files committed as 0578faa and pushed to origin/main; actual API key scan found no matches. Secrets, weights, environments, runtime data, reports and build metadata are excluded. Git whitespace check passed.
- Status: completed
- Next steps: main tracks origin/main; use normal Git commits and pushes for future changes. The separate Windows firewall approval remains pending.

### 2026-09-30 — live Bugsmith decision examples
- Summary: Inspected vpn-bugsmith's triage, prompt construction, plan policy, DO dispatch and trusted validation; added three live client examples under examples/ plus an interactive combined runner.
- Actions taken: Relative-file .env lookup, checkpoint/example menus, choice/score results, distributions, baseline/reference comparisons, review routing, measured service/HTTP timings and local full JSON reports. All fixtures are synthetic and no repair actions execute; vpn-bugsmith is unchanged.
- Findings: Withholding supplied classification reduced anchoring: final English and typed-decisions triage match 4/4 versus 2/4 with supplied labels. Multilingual injection matches 6/6 and alignment 5/6; its self-merge prediction is wrongly aligned at 86.44%, but the explicit demo rule blocks it. Confidence and task suitability need domain validation.
- Files touched: examples/, tests/test_examples.py, README.md, project memory/progress.
- Validation: 25 tests pass; final 48 predictions all CUDA with no truncation and default auto preserved. All three standalone model menus and both combined-runner menus pass from a different working directory. Full comparison report: data/examples/20260930T230253951521Z-all.json.
- Status: completed
- Next steps: User can run examples/run.py interactively or --compare-models --example all; changes are local and not committed/pushed by this task.

### 2026-10-08 - Bugsmith injection test startup
- Summary: Started the existing local Laya service for the user and prepared three synthetic prompt injection cases targeting Bugsmith evidence/tool-output entry points.
- Actions taken: Read saved runtime context and current Bugsmith master-plan template and DO loop; created a portal-importable prediction batch and test instructions.
- Findings: English cold load took approximately 172 seconds on this run; subsequent English predictions completed. Initial English results missed credential leakage and fake validation, detected forged authority, and flagged benign security documentation.
- Files touched: examples/bugsmith_injection_cases.json and examples/bugsmith_injection_cases.md.
- Validation: All three requests pass PredictRequest validation; live CUDA comparison against three models and three benign controls is in progress. Payload strings are classified only; no Bugsmith tools execute.
- Status: in progress
- Next steps: Finish model comparisons, save full results under ignored data/examples, and report observed misses to the user.

### 2026-10-08 - Bugsmith injection tests completed
- Summary: Left Laya running at localhost:8000; completed all three synthetic attacks and three existing benign controls on each of three checkpoints.
- Findings: Attack labels matched 1/3 English, 2/3 multilingual, 1/3 typed-decisions. Every model missed credential leakage into a PR. English missed fake validation at 85.9% confidence. English and typed-decisions falsely flagged quoted security documentation.
- Validation: All 18 predictions on cuda:0 without truncation; saved default remained auto; service ended idle with zero outstanding jobs.
- Files touched: examples/bugsmith_injection_cases.json, examples/bugsmith_injection_cases.md; full local report data/examples/bugsmith-injection-test-20261008.json.
- Status: completed
- Next steps: User can replay the JSON batch in the portal. Classification remains advisory; Bugsmith itself was not run or modified.

### 2026-10-08 - Everyday decision study started
- Scope: User requested evidence on everyday model routing and chat/image/video prompt moderation, to characterize useful tasks beyond the earlier injection failures.
- Actions: Added examples/everyday_decisions.py with 130 pre-labeled English-only synthetic cases in six balanced tasks: capability routing, support routing, sentiment, and custom-policy chat/image/video prompt moderation.
- Method: All three checkpoints; one excluded warm-up each; references withheld from input; fixtures hashed and saved before first prediction; no tuning after results; sequential requests through existing shared API.
- Status: in progress
- Next steps: Complete 390 scored predictions, review errors/confidence/truncation, save readable and raw reports, and propose appropriately bounded public wording.

### 2026-10-08 - Everyday decision study completed
- Summary: Completed 390 scored CUDA predictions over the frozen 130-case English-only corpus; no truncation or model-selection mismatch; saved default remained English. Excluded one initial warm-up per model.
- Results by task (English / multilingual / typed): capability routing 15/20, 9/20, 16/20; support routing 15/20, 14/20, 17/20; sentiment 17/18, 14/18, 18/18; chat moderation 18/24, 11/24, 15/24; image-prompt moderation 13/24, 8/24, 17/24; video-prompt moderation 11/24, 9/24, 16/24.
- Findings: Warm service medians 68.05/58.29/67.02 ms. Moderation policy is custom; media prompts only, no media generated or inspected. Typed decisions had no direct block-to-allow or allow-to-block errors but sent 12/24 prohibited and 11/24 benign prompts to review. English falsely blocked 9/24 benign prompts; multilingual allowed 7/24 prohibited prompts. At >=80% confidence coverage was 40/130, 61/130, 3/130 respectively, with 1/23/0 errors.
- Files: examples/everyday_decisions.py; docs/benchmark/everyday-decisions-20261008.md; ignored raw data/examples/everyday-decisions-results.json and frozen fixtures. Fixture SHA-256 881910b2bf2aeb61790ee3aa8cbf6dd42d9aa8218f68d46b70d4b91dac0e3d20.
- Validation: References withheld; balanced task labels; no tuning after results; all requests validated before inference; integrity checks and git diff --check passed. The existing English checkpoint calibration notice is preserved in raw responses.
- Status: completed
- Next steps: Use measured narrow claims for a public post; this small synthetic study does not establish production accuracy or broad security suitability. Laya remains running.

### 2026-10-08 - Decision lab portal integration
- Scope: User requested a dedicated section under Batch testing with the everyday examples, comparison tables, timing/accuracy/decision breakdowns and repeatable runs.
- Actions: Extracted shared frozen fixtures and compact recorded results; added authenticated read-only /api/v1/decision-suite; added lazy-loaded Decision lab next to Custom batch with selective suite/model replay, excluded warm-ups, progress/stop, partial-run retention, exports, confusion tables and case-level inspection.
- Findings: Fixture hash remains 881910b2bf2aeb61790ee3aa8cbf6dd42d9aa8218f68d46b70d4b91dac0e3d20. Saved and live observations share scoring; truncated/misrouted answers cannot count as matches.
- Validation: 38 Python checks passed; UI replay/cancel/failure/scoring checks passed. One initial screenshot test raced service startup and will be rerun with the service ready. Production build passes; code splitting added to avoid increasing the initial bundle past 500 kB.
- Status: awaiting validation
- Next steps: Rebuild, complete browser desktop/mobile verification, visually inspect captures, and run full real CUDA replay through the new UI.

### 2026-10-08 - Decision lab delivered
- Summary: Built and served the dedicated Decision lab at /batch#decision-lab alongside Custom batch. The six suites and three checkpoints can be selectively rerun; saved/live tables show accuracy, latency, confidence, confusion and case-level decisions with exports and stop/partial-run handling.
- Important fix: The first end-to-end comparison revealed that JSON key sorting reordered answer criteria. Restored the exact original option order from the measured requests and added order-sensitive request_sha256 validation (dfb55e0b3a963f2a0db09d97a8800d2be011c55910b27977a02dbc68746a2f6e). Portal and CLI requests now match the saved study.
- Validation: Final production build passed without bundle-size warning; 38 Python checks and 11 browser/scoring checks passed. Final real UI replay completed 390 CUDA predictions plus three excluded warm-ups in 41.8 seconds; all 390 choices exactly matched the saved baseline. Mobile width and desktop/mobile screenshots inspected. Runtime ended idle with zero outstanding jobs and saved default English.
- Evidence: data/verification/decision-lab-live.json and decision-lab-verification.json; frontend/test-results/decision-lab-saved-real.png, decision-lab-live-real.png and decision-lab-live-full.png.
- Files: laya_portal/decision_suite.py and app route; frontend/src/DecisionLab.tsx, labMetrics.ts, decisionLab.css and App integration; canonical fixtures/baseline, shared CLI, API/development/example docs and focused tests.
- Status: completed
- Next steps: User can open Batch testing > Decision lab, select suites/checkpoints and click Run selected tests. Live results remain in the page until reload and can be exported; recorded baseline remains separately available.
