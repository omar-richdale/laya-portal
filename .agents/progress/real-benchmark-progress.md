# Real-world Laya benchmark and integrations

## Metadata
- Scope: Sift, Bugsmith and VPN QA review; real issue/report benchmark; portal examples; advisory applications; generated diagrams and presentation
- Status: complete
- Owner: agent
- Started: 2026-10-01
- Last updated: 2026-10-01
- Related areas: examples, benchmarking, frontend, docs, sibling repositories

## Objective
Benchmark all three hosted checkpoints on real GitHub issues and QA evidence, apply the best bounded decision workflows, and deliver a report plus four generated diagrams and a generated-slide presentation matching Sift v3.

## Current understanding
- Previous examples were synthetic and exposed significant checkpoint-dependent errors. Keep independent reference labels and distinguish source-report labels from human-reviewed ground truth.
- Global inference setup is already working. Model choice must not rewrite persistent default; use the shared GPU service.
- User authorized moving Bugsmith into Agentic-production and local integration changes; no issue closure, notification, merge or production deployment was requested.

## Progress log

### 2026-10-01 — research started
- Actions taken: Recalled project memory; inspected repository locations/remotes and Sift v3 presentation structure; moved Bugsmith safely to the requested Agentic-production path.
- Findings: Sift is Go, QA agent is TypeScript, Bugsmith Python. Actual TotalGuard path is Agentic-production (user's Agentic-productio path was a typo). The requested QA reports are dated September 29–30.
- Validation: Bugsmith checkout was clean before and after moving; destination .git exists.
- Status: in progress
- Next steps: Fetch issue/report snapshots, inspect classification contracts, assemble labeled real-data tasks and run the GPU benchmark.


### 2026-10-01 — benchmark and local delivery completed
- Summary: Finished real-data CUDA evaluation, bounded native integrations, portal examples and all requested visual/document artifacts.
- Actions taken: Captured 134 GhostShield and 99 TotalGuard issues plus three QA reports; built 247-case corpus with references outside inputs; ran three passes per checkpoint, batched replay and isolated fresh-process startup probes. Moved Bugsmith including Git history into Agentic-production and removed the empty original directory.
- Findings: English issue routing matched 225/233, multilingual 170/233, typed-decisions 222/233. Typed matched 7/7 security topics. English/typed QA matched 4/7, multilingual 0/7; every checkpoint missed the card-required trial policy. Warm service medians: 61.53/51.43/63.27 ms. Dependency findings form 34 investigation groups; Bugsmith's current policy prohibits dependency upgrades.
- Files touched: Laya fixed advisory workflows, authenticated saved-benchmark API, Real benchmark frontend, relative-.env examples, docs/benchmark, docs/diagrams and docs/presentation/v1. Native opt-in adapters in Sift reviewer, Bugsmith triage and QA report metadata; GhostShield trial contract fixed. Sift source-skill LF checkout rule restores existing manifest hashes.
- Validation: All predictions CUDA; zero errors/truncations/repeat choice changes in primary run. Native replay: Sift 7/7, Bugsmith 4/7, QA seven hints with source JSON unchanged; default auto preserved. Laya 30 tests, Sift 116, Bugsmith eight focused tests, QA 97 plus typecheck, frontend production build and five Playwright checks passed. Final PPTX package/layout/import validation passed; all 12 final rendered slides visually inspected; PDF has 12 pages; credential scan passed.
- Deliverables: docs/benchmark/REPORT.md plus raw results/corpus/provenance/startup/replay/patch files; four generated diagrams; 12 fully generated slide PNGs, prompts, briefs, presenter notes, gallery, checked PowerPoint and PDF.
- Status: complete
- Next steps: None required for this local request. Production rollout, calibration, actual dependency upgrades/rotations, live QA payment flow and issue resolutions remain outside the delivered measurement/shadow integration. Local API is running on port 8000 with English resident and saved default auto; optional sibling adapters remain disabled unless configured.
