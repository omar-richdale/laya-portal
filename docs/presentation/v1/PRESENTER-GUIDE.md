# Presenter guide

## 01 — Local System One
Introduce a local fixed-choice classifier alongside the existing reasoning/coding agents. It returns labels and probability distributions, not generated explanations or patches.

## 02 — The real workload
134 GhostShield and 99 TotalGuard open issues were captured. Source-kind counts were 196 dependency, 20 secret, 7 code and 10 business. Two code-scanner findings concern Google credentials, giving semantic work lanes of 22 credential and five source-code findings. All 99 TotalGuard GitHub issues in this snapshot are dependencies. QA's app-token observations are a separate evidence source.

## 03 — Decide first, investigate next
Small decisions can organize investigation. A label cannot verify a vulnerability or grant a tool permission. Policy and evidence remain outside the classifier.

## 04 — One local GPU worker
Portal, REST and MCP use one service. One checkpoint resides on CUDA at a time; changing checkpoint adds loading cost. The key protects runtime/inference endpoints. Weights and frontend assets work offline after setup.

## 05 — A fair local comparison
247 cases include overlapping issue/topic tasks and seven QA observations. There were 2,223 single-request predictions and 288 batched states, plus separate warmups. The same token budgets and label order were used. No label-order counterbalancing, multilingual real-data evaluation, exploit validation or end-to-end repair benchmark occurred.

## 06 — Fast enough for a hint
Warm service medians: English 61.53 ms, multilingual 51.43 ms, typed-decisions 63.27 ms. HTTP medians are slightly higher. The 32-state batch uses microbatch two. These are measurements of this corpus/run, not promised upstream speed. The slide's allocated-memory figures are post-call observations; the report also gives fresh-process allocator peaks. A separate first request took 28.86 seconds, demonstrating why startup must be reported separately.

## 07 — Accuracy depends on the task
Interpret the table as agreement with metadata and evidence-audit references. English issue routing beat the 196/233 majority baseline but missed eight business reports. Typed-decisions matched all seven topic references, all with low confidence. Multilingual made two credential-topic workflow errors at about 94.3% probability. Seven-case sets cannot establish production accuracy or calibration.

## 08 — The card-required trial
The user confirmed GhostShield's intentional card requirement. The captured test expected an automatic no-card trial. All models called it a product defect despite the supplied contract. The applied correction changes the QA site profile explicitly; it does not rely on a model. Historical trial reports need a contract-aware rerun before repair. No card was submitted or charged.

## 09 — Sift
The main scanner/intelligence and independent-review paths stay authoritative. The native Python adapter emits a topic event after mechanical evidence validation. It does not change the verifier prompt or verdict. Reliable scanner metadata wins over model guesses. A Windows LF checkout rule restores the hash-verified source skills without changing expected hashes.

## 10 — Bugsmith
196 dependency findings form 34 repository/package investigation groups. This organizes work without suppressing findings. Current Bugsmith policy forbids dependency updates, so package remediation needs its own explicit contract. Credentials require owner verification/rotation planning. Existing QA repair gates and trusted regression validation remain. Optional QA disagreements are operator metadata only.

## 11 — VPN QA
Playwright status remains the test result. Laya sees a trusted contract and compact redacted facts and appends optional report metadata. Existing reasoning triage and notification policy do not consume it. Preserve TotalGuard's rejection-after-signout assertions: reports observed app tokens validating after signout on two days. Reproduce independently on the captured deployment before changing production auth code.

## 12 — Measured advice
The immediate benefit is fast, structured investigation hints and a clearer backlog. No verified time saving in complete repairs, no issue resolution count, no model-based security gate and no production deployment are claimed. Start with shadow observations and expand independent evaluation before granting any automated influence.

## Evidence

- [Local benchmark report](../../benchmark/REPORT.md), [corpus](../../benchmark/corpus.json), [raw responses](../../benchmark/results.json), [native replay](../../benchmark/integration-replay.json).
- [GhostShield QA report](https://vpnqa.richdalelab.com/reports/20260930-060000-9iy9o/index.html).
- [TotalGuard September 30 report](https://vpnqa.richdalelab.com/reports/20260930-071000-9o49u/report.md).
- [TotalGuard September 29 report](https://vpnqa.richdalelab.com/reports/20260929-071000-wzuvk/report.md).
- [Laya model documentation](https://huggingface.co/convaiinnovations/laya/blob/main/README.md).
- Reviewed code: Sift `deploy/reviewer/sift_reviewer/engine.py`; Bugsmith `src/fixer/triage.py`, `autonomy.py` and `validate.py`; QA `src/run.ts`, `src/llm/triage.ts`, `src/sites/ghostshield.ts` and `src/tests/trial-redeem.spec.ts`.
