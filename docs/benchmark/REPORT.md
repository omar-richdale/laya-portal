# Real-data Laya benchmark and applied integrations

**Date: 2026-10-01. GPU: NVIDIA GeForce RTX 4050 Laptop GPU, nominal 6 GiB.**

English is the strongest of these checkpoints for general issue-workflow hints on this snapshot. Typed-decisions is the best match for the seven source-topic references. The QA results do not support automated cause classification: every checkpoint missed GhostShield's intentional card-required trial change. The implemented integrations therefore record shadow advice while existing evidence, product contracts and policies control actions.

## Work completed

- Reviewed Sift's scanner/intelligence priorities, issue lifecycle and independent Python reviewer; Bugsmith's report intake, triage, repair policy, sandbox and trusted regression validation; and QA's deterministic tests, investigation/assessment, report and notification flow.
- Moved the Bugsmith checkout, including `.git`, to `C:\Users\richd\Documents\oMAR\Agentic-production\vpn-bugsmith`. The old root was initially locked; its contents were moved into the verified destination and the empty original directory was removed after its lock cleared. Git history and local files were preserved. TotalGuard's actual path is under `Agentic-production`, correcting the supplied path typo.
- Captured all 134 GhostShield and 99 TotalGuard open GitHub issues and the three requested QA reports. Built an auditable fixed corpus with source links and independent reference fields outside model inputs.
- Ran all three hosted CUDA checkpoints through the same authenticated HTTP worker: 2,223 single predictions, 288 additional batched states, nine warmups. Recorded raw responses, timing, probabilities, errors and memory observations. Added separate fresh-process startup/peak-memory measurements, another 99 states.
- Added fixed advisory HTTP workflows, a real-benchmark portal view with five understandable real examples, an interactive Python client, a read-only backlog planner and native-adapter replay.
- Applied opt-in native shadow adapters in Sift, Bugsmith and QA. Corrected GhostShield's obsolete automatic-trial test contract. Added an LF checkout rule for Sift's hash-verified source skills on Windows.
- Generated four separate diagrams and twelve complete presentation slides with image generation, plus reusable prompts, PowerPoint, PDF, offline gallery and presenter notes in this repository.

No production deployment, issue closure, dependency upgrade, credential rotation, browser/account operation, credit-card submission, notification or merge was performed. The local adapters are disabled unless their trusted service environment is explicitly configured. The evidence replay invokes only local inference.

## Sources and inventory

GitHub issue snapshots were read with `gh issue list --state open --limit 1000`. The captured inventory is a point-in-time observation, not a claim about future issue counts. Raw fetched pages/reports live under ignored `data/benchmark/sources`; the redacted corpus and model responses are under this directory.

| Source | Open issues | Source-kind inventory |
|---|---:|---|
| [GhostShield repository](https://github.com/Richdale-AI/VPN_website/issues) | 134 | 97 dependencies, 20 secrets, 7 code, 10 business reports |
| [TotalGuard repository](https://github.com/Richdale-AI/total_guard_vpn_website/issues) | 99 | 99 dependencies |

The semantic routing reference groups two SAST Google-credential findings with credential work: **196 dependency, 22 credential, 5 source-code and 10 business** issues. A credential-topic label does not establish that a credential is actually exposed. No flagged credential file or secret value was opened for this study.

QA evidence:

- [GhostShield September 30](https://vpnqa.richdalelab.com/reports/20260930-060000-9iy9o/index.html): FAIL, 174 tests, three reported observations. GS-018 expected an automatic trial but saw a paywall; GS-015 hit an overlay-blocked logout click; GS-027 timed out during app-token validation.
- [TotalGuard September 30](https://vpnqa.richdalelab.com/reports/20260930-071000-9o49u/report.md) and [September 29](https://vpnqa.richdalelab.com/reports/20260929-071000-wzuvk/report.md): DEGRADED, 126 tests each. Mobile/desktop app-token assertions observed `valid=true` after sign-out on both days.

Four TotalGuard observations repeat two flows across two dates; they are not four independent verified bugs. Captured report revisions and current local checkout revisions are recorded separately in [provenance.json](provenance.json). The current checkout is not assumed to be identical to a deployed report's revision.

## Benchmark method

Runtime: Python 3.12, Laya 0.3.22, PyTorch 2.10.0+cu128, Transformers 4.57.6, MCP 2.2.0; pinned offline checkpoint revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`. Compilation and TileLang remain disabled. One checkpoint resides on CUDA; inference and switching are serialized.

The [corpus](corpus.json) contains **247 decision cases**: 233 issue-workflow cases, seven overlapping source-topic cases and seven QA observations. Routing references come from scanner metadata plus an audited work taxonomy. QA references are a small evidence audit, using the user-confirmed product contract and captured observations; they are not independently reproduced exploit findings or a human-annotated production evaluation set.

Each checkpoint received the same inputs, fixed choice order and 512/192 context/question budgets. Three warmups preceded three randomly ordered passes, seed 4050. Quality is computed on the first pass; repeats assess choice stability, not extra independent examples. Separate 32-state batches used microbatch two, repeated three times per checkpoint. The client verified `cuda:0` in every prediction response. There were no errors, truncations or changed choices across repeats.

Input references and prior QA classification labels were withheld from the model. The trusted product contract was deliberately included. No label-order counterbalancing, prompt tuning sweep, multilingual-language evaluation, adversarial benchmark, comparison with another classifier, production replay or complete repair-time measurement occurred.

Corpus SHA-256: `ecc526420c6a1c0198e39d0683a67a2ecaf6def78152762d6d88c33a05583ad0`.

Raw [results.json](results.json) records the run from 00:25:28 to 00:28:36 UTC on October 1. Read [examples/benchmark_real.py](../../examples/benchmark_real.py) for the executable methodology.

## Quality: agreement with references

| Checkpoint | Issue workflow | Macro F1 | Security topic | QA cause |
|---|---:|---:|---:|---:|
| English | 225/233 · 96.57% | 0.7222 | 4/7 | 4/7 |
| Multilingual | 170/233 · 72.96% | 0.6202 | 3/7 | 0/7 |
| Typed-decisions | 222/233 · 95.28% | 0.6526 | 7/7 | 4/7 |

The always-dependency majority baseline is already **196/233, or 84.12%**. English's headline agreement therefore overstates the hard part of this imbalanced task. Its eight errors were business reports routed into source review. Typed-decisions missed nine business reports and two credential workflows. Multilingual missed 49 dependency, ten credential, two source-code and two business workflows. These are workflow errors, not false-positive vulnerability verdicts.

At the illustrative 0.8 threshold, issue-workflow review counts were **204/233 English, 228/233 multilingual and 233/233 typed**. English and typed had no wrong issue decisions above that threshold in this snapshot; multilingual had two. This does not establish a calibrated acceptance threshold. Every QA decision was below 0.8, as were all seven typed-decisions topic answers.

Examples with practical consequences:

| Evidence | Reference | Observed model behavior | Consequence |
|---|---|---|---|
| [VPN #157, Nodemailer](https://github.com/Richdale-AI/VPN_website/issues/157) | dependency update investigation | All three choose dependency work | Use scanner/package metadata first; investigate affected paths and fixed versions |
| [VPN #68](https://github.com/Richdale-AI/VPN_website/issues/68), also #55 | credential-topic investigation | Multilingual chooses source review at approximately 94.3% probability | A high probability can accompany a wrong work lane |
| [VPN #150](https://github.com/Richdale-AI/VPN_website/issues/150) | source review for duplicate branches | English/typed match; multilingual chooses dependency work | A focused regression investigation is still required |
| GhostShield GS-018 | TEST_BUG: obsolete automatic-trial expectation | All three choose PRODUCT_BUG | Apply the explicit current product contract; do not ask the model to approve it |
| TotalGuard GS-027/028 | PRODUCT_BUG evidence reference | English/typed match four observations; multilingual matches none | Keep token-revocation assertions and independently reproduce on the captured revision |

Timeout/overlay evidence alone does not establish GhostShield's GS-015/027 root cause; these references remain UNKNOWN. English labeled every QA observation PRODUCT_BUG, explaining its 4/7 score. The seven-case QA set contains no INFRA reference case. The English checkpoint also emits an upstream stored-temperature warning for an affected option-count entry; these four-choice experiments do not supply domain calibration.

## Latency and GPU memory

Resident inference measurements on this workload:

| Checkpoint | Service median / p95 | HTTP median / p95 | 32-state batch median | States/s |
|---|---:|---:|---:|---:|
| English | 61.53 / 76.52 ms | 64.36 / 80.38 ms | 1,132.47 ms | 28.26 |
| Multilingual | 51.43 / 67.56 ms | 54.40 / 70.95 ms | 900.52 ms | 35.54 |
| Typed-decisions | 63.27 / 79.02 ms | 66.32 / 82.15 ms | 1,126.44 ms | 28.41 |

First calls with checkpoint switching in the primary run took 2,408.66 / 1,586.26 / 2,060.99 ms. These are not cold-process guarantees. A separate example after restart took **28,859.16 ms**, including 27,198.08 ms model load, while later requests in that replay took roughly 83–120 ms. Startup is excluded from the resident latency table.

Three supplementary measurements each restarted the service, required no prior resident model, loaded only one checkpoint and then ran a 32-state batch at microbatch two:

| Checkpoint | First request in fresh process | Model load | PyTorch process peak allocated |
|---|---:|---:|---:|
| English | 7,027.08 ms | 6,448.45 ms | 2.286 GiB |
| Multilingual | 9,003.82 ms | 8,380.26 ms | 1.480 GiB |
| Typed-decisions | 7,966.35 ms | 7,393.04 ms | 2.286 GiB |

See [startup-english.json](startup-english.json), [startup-multilingual.json](startup-multilingual.json), [startup-typed-decisions.json](startup-typed-decisions.json) and [measure_startup.py](../../examples/measure_startup.py). These are single fresh-process samples, not cold machine boots or startup percentiles. File/driver caches and other host work can vary between samples; no cause was isolated for the earlier slower request.

The primary run's maximum observed post-call allocation was 1.579 / 1.228 / 1.579 GiB, with observed reserved allocation 2.443 / 1.484 / 2.443 GiB. Its allocator lifetime peak included prior checkpoints and cannot be attributed to each model. The supplementary fresh-process peaks correct that attribution limitation. PyTorch allocator peaks exclude other processes, Windows display allocations and some CUDA overhead; total physical VRAM peak was not sampled. Figures apply to these compact 512/192 inputs, not arbitrary 8,192-token multilingual batches.

## Best applications and actual changes

### Sift

Keep Syft/OSV/Trivy/Gitleaks/OpenGrep outputs, monotonic CVSS/EPSS/KEV priorities, independent evidence verification and scanner-managed issue lifecycle authoritative. Laya should not classify away a known scanner label or suppress findings. Its most promising use here is a bounded topic hint for unstructured candidate metadata. Typed-decisions matched the seven topic references, with low confidence throughout.

The native `system_one.py` adapter now emits a small `system_one_hint` progress event after mechanical evidence validation. It sends title/CWE/root-cause/sink metadata, excluding quoted source spans. It does not enter the verifier prompt or modify claim, attack class, verdict, severity or budget. The opt-in branch caps calls at eight and stops on failure. This is measurement and operator advice, not implemented specialist reassignment.

Windows checkout CRLF conversion broke Sift's existing source-skill manifest verification. Normalizing the 41 Markdown assets to their original LF bytes restored the expected hashes; a scoped `.gitattributes` rule preserves them. No expected security hash was changed or verification bypassed.

### vpn-bugsmith

The biggest backlog is package remediation: **196 findings across 34 repository/package investigation groups** (16 GhostShield, 18 TotalGuard). The [read-only plan](backlog-plan.json) retains every issue link. Grouping is an investigation aid, not vulnerability resolution or a reason to close findings. Many issue bodies contain advisory IDs without complete affected/fixed-version information; actual dependency paths, advisory ranges and regression checks are still needed.

Current Bugsmith accepts QA reports and forbids dependency upgrades in its repair policy. Feeding this dependency backlog straight into that repair loop is incompatible with its contract. A separate package-update workflow needs an explicit policy and verification contract before it can act. Credentials require owner review and a rotation plan; business reports go to the operator. Source findings need reproduction and bounded regression-backed repair.

The native optional QA cross-check records model/report disagreements only after the existing classification, investigation confidence, priority and budget gates determine the candidate lists. It does not change selected/deferred/skipped findings or coding prompts. Historical GS-018 automatic-trial reports still contain obsolete PRODUCT_BUG assessments: rerun QA with the updated product contract before using them for automated repair.

### VPN QA

Corrected the GhostShield site profile from automatic no-card trial to `signupGrantsTrial=false`. GS-018 now selects the existing no-automatic-entitlement assertion branch. This follows the user's current requirement and website trial/start code. No card-activation/payment flow was executed, and app-token rejection-after-signout assertions remain intact.

The native TypeScript adapter appends optional `systemOneAdvice` to report.json from trusted contract plus compact redacted evidence. It does not feed the existing reasoning assessment or change Playwright status, cleanup or notifications. Real-data failure labels were unreliable, so a model-controlled triage gate was not introduced.

### Laya service and portal

Added `/api/v1/workflows/{workflow}` for issue_lane, security_specialist and qa_cause, backed by the same worker. Responses preserve reference answer/routing/usage fields and add readable advice with `advisory_only=true`, `authorization=false`. Empty evidence is rejected before GPU work. `/api/v1/benchmark` serves saved aggregates and replay inputs behind bearer authentication without GPU work.

The **Real benchmark** view shows measured successes/misses and loads five original cases into Playground: Nodemailer dependency work, duplicated branches, a confident credential-routing error, the card-required trial and signed-out app tokens. Desktop/mobile layouts, reduced motion, locally bundled assets and a real CUDA prediction were exercised. API key remains tab-scoped; test inputs/results remain in browser memory unless exported.

## Native replay and validation

[integration-replay.json](integration-replay.json) records actual installed clients against localhost: Sift typed topic hints matched 7/7 references; Bugsmith English QA hints matched 4/7; the native QA TypeScript client returned seven hints from the three raw reports. Source report JSON remained unchanged. Client projections differ from the compact benchmark inputs, so their probabilities are not claimed to be identical. The saved default remained auto.

Completed checks:

- Laya: 30 Python tests, including authenticated workflows, input validation, frozen-corpus integrity, native-client redaction/response validation and existing GPU-only/queue/lifecycle/error tests.
- Sift reviewer: 116 tests. Explicit shadow-disagreement test preserves independent verifier context, verdict and severity. Four relevant verification tests reran after adding the eight-call cap. Source-skill manifests verify on Windows with the LF rule.
- Bugsmith: eight focused triage/master-plan tests, including a high-confidence contrary model hint that cannot change repair selection. No complete repair agent or external tool dispatch was run.
- QA: type check, five new adapter/contract tests, and all 97 unit tests. Native SQLite dependency and the existing dashboard were built locally for the broader suite; the initial unbuilt-dashboard deep-link failure disappeared after the required build.
- Portal: production TypeScript/Vite build and five Playwright tests, including real CUDA inference, real-case replay, responsive layout, reduced motion, exports and offline assets.
- Fresh offline service restart and all three isolated checkpoint probes: CUDA verified, 32-state batches completed. PowerPoint package/layout/import checks completed and all 12 final slides were rendered for inspection.

Dependencies used for sibling tests were isolated in ignored `.cache/integration-venv`; the pinned Laya inference environment and global Python packages were preserved. No new model process is created by an adapter. Existing host/LAN API behavior is retained; this task did not change the Windows firewall or verify access from a second LAN device.

## Reproduce and read the deliverables

```powershell
# Start the already-installed local service.
.\start.ps1
.\.venv\Scripts\python.exe examples\real_workflows.py
.\.venv\Scripts\python.exe examples\plan_real_backlog.py
.\.venv\Scripts\python.exe examples\replay_shadow_adapters.py

# Full three-checkpoint resident benchmark; writes new results.json.
# Preserve the frozen evidence files before intentionally replacing this study.
.\.venv\Scripts\python.exe examples\benchmark_real.py

# Isolated first-use/allocator probe: repeat restart for each named checkpoint.
.\stop.ps1
.\start.ps1
.\.venv\Scripts\python.exe examples\measure_startup.py --model english
```

Clients resolve `.env` relative to their own file, never the terminal's current directory, and do not print credentials. Read [integration setup and boundaries](../system-one-integrations.md) before configuring optional service environments. Native replay needs sibling checkouts, QA Node dependencies and ignored captured reports; the portal examples and real-workflows client do not require those sibling dependencies.

- [Diagrams and prompts](../diagrams/README.md): Laya, Sift, Bugsmith, VPN QA.
- [Generated-slide presentation](../presentation/v1/README.md): PowerPoint, PDF, offline gallery, exact briefs/prompts and presenter guide.
- [Local integration patches](patches/README.md): reviewable changes to the three sibling repositories, plus the applied local files.

The measured benefit is inexpensive structured advice and organized investigation queues. Complete repair-time savings, reduced vulnerability exposure, calibrated probabilities, prompt-injection defense effectiveness and production issue resolutions remain unmeasured. The existing synthetic injection/alignment examples illustrate failure modes and retain deterministic tool policies; this study does not validate them as security filters.
