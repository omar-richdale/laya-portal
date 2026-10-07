# Runtime decisions

- Date: 2026-09-30
  Scope: decision
  Topic: GPU-only reference implementation
  Note: GPUOnlyAgent is bound to Laya 0.3.22 and overrides only _infer's CUDA error policy. Reference Agent silently retries OOM on CPU; Router normally loads before evicting. The service unloads both owners first, attaches the reviewed adapter, and serializes all GPU work in one bounded executor.
  Evidence: Reference output equality for English, multilingual and typed-decisions; OOM/no-CPU and single-owner lifecycle tests passed.
  Action for future work: Review this adapter before changing the Laya version. Keep REST and MCP on the same service instance.

- Date: 2026-09-30
  Scope: preference
  Topic: Models and dashboard
  Note: All three checkpoints; default auto English/multilingual routing; explicit typed-decisions. Panel selection changes persistent default, explicit requests do not. Expressive dark React Bits styling and Font Awesome Free SVG icons, with offline assets and notices.
  Evidence: User's approved implementation plan; real routing, override persistence and frontend tests passed.

- Date: 2026-09-30
  Scope: fix
  Topic: MCP SDK 2.2 client/output contracts
  Note: MCP Client authentication uses mcp.client.streamable_http.streamable_http_client with a configured httpx2.AsyncClient. Bare dict return annotations produced unstructured tools; Pydantic response envelopes produce structured_content at the root and publish output schemas.
  Evidence: Actual HTTP/MCP prediction equality, all five tools, batch, resource and error checks passed.

- Date: 2026-09-30
  Scope: environment
  Topic: Checkpoint caveats
  Note: English checkpoint has an invalid stored choice:11+ temperature; Laya clamps it and warns. Raw details remain in status; prediction warnings summarize the calibration caveat. Pinned weights are under models/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851.
  Evidence: Real model loading emitted the warning; 1,024/4,096/8,192 context multilingual tests and English truncation checks passed on CUDA.

- Date: 2026-09-30
  Scope: decision
  Topic: Bugsmith examples and advisory model use
  Note: examples/run.py and three standalone clients resolve the project .env relative to their file and use the shared hosted API. QA cross-checks withhold the supplied classification to avoid anchoring. Synthetic fixtures show checkpoint-dependent errors: multilingual incorrectly permits self-merge at 86.44% confidence; explicit tool/path rules still block it. Keep model signals advisory and retain Bugsmith's sandbox, structural plan policy, red-green validation and human merge gate.
  Evidence: 48 final CUDA predictions, 25 tests, interactive menus from another working directory. Detailed fixture results and integration seams are in examples/README.md.
  Action for future work: Evaluate custom policies on labeled domain data; do not interpret fixture agreement or confidence as production accuracy. Do not replace deterministic gates with this classifier.


- Date: 2026-10-01
  Scope: decision
  Topic: Real-data System One shadow integrations
  Note: The 247-case issue/QA benchmark found English strongest for workflow hints (225/233), typed-decisions matched seven source-topic references, and all checkpoints misclassified the intentional card-required trial. Native Sift, Bugsmith and QA adapters are disabled by default; bounded hints never change independent verification, repair selection, test status or tool authorization. Env prefixes REVIEWER_LAYA, FIXER_LAYA and QA_LAYA; warm the shared resident checkpoint before short-timeout calls. Fixed workflows and saved benchmark API share the existing CUDA worker.
  Evidence: docs/benchmark/REPORT.md, results.json and integration-replay.json; native contrary-hint tests preserve authoritative behavior.
  Action for future work: Treat these small-reference agreement scores as advisory evidence. Preserve current product contracts and independently evaluate before introducing automated gates. Do not send dependency backlog into Bugsmith's current no-upgrade repair policy.


- Date: 2026-10-01
  Scope: decision
  Topic: Shared offline model learning catalog
  Note: docs/models.json is the canonical reviewed catalog; scripts/build_model_catalog.py regenerates it and docs/models.md from pinned configs/weight headers, frozen local benchmark and reviewed upstream summaries. Portal /model-guide works without login; public /models.json contains learning data only. Protected REST /api/v1/model-metadata and /api/v1/models/{model}/metadata plus MCP laya_model_info, laya://models and laya://model-guide share the catalog without GPU work. Runtime status stays separate.
  Evidence: 36 Python tests, public/mobile guide browser checks and live authenticated REST/MCP parity/no-residency/allocation-change verification. Three guide examples verified on CUDA.
  Action for future work: Keep published claims, installed config and measured evidence distinct. English/typed backbones list 8192 positions but hosted caps remain 512/1024; multilingual max is 8192. Head budget shares context with state. Review provenance before refreshing; restart after catalog replacement because the loader caches it.
