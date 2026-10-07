# Model capability guides

## Metadata
- Scope: Research, portal learning guides, machine-readable model metadata and MCP discovery
- Status: complete
- Owner: agent
- Started: 2026-10-01
- Last updated: 2026-10-01

## Objective
Explain each hosted checkpoint with accurate local token limits, architecture, use cases, examples, benchmark evidence and limitations; make the same information available to agents and offline.

## Progress log

### 2026-10-01 — research and contract inspection
- Actions taken: Read current upstream family/model cards, benchmark and API documentation; inspected pinned configs and safetensors headers without loading a second model.
- Findings: Upstream capability claims need separation from our local service constraints and benchmark. English/typed encoders list 8192 positions, but hosted service caps them at 512/1024. The question/options budget shares context with state. Confidence is not calibrated for our domain; score returns expected ordinal level, and noul has label sensitivity.
- Validation: Verified checkpoint configs, tensor counts, storage sizes and service limits locally. Documentation reviewed 2026-10-01.
- Status: in progress
- Next steps: Implement shared offline catalog, readable portal guide, REST/MCP discovery and tests, rebuild/restart the service.


### 2026-10-01 — guides delivered and verified
- Summary: Added an offline, versioned model catalog and a readable public portal guide for all three hosted checkpoints.
- Actions taken: Generated docs/models.json and docs/models.md from reviewed upstream descriptions, local config/header data and frozen RTX 4050 measurements. Added public /models.json and Markdown discovery, protected full/per-model REST metadata, structured MCP laya_model_info and JSON/Markdown resources. Added direct model-card guide links, explicit per-model examples and an interactive budget illustration; rebuilt and restarted the service.
- Findings: Distinguish encoder capacity from hosted cap, approximate state room from total context, modal answer confidence from entropy confidence, fractional expected score from numeric generation, and calibration claims from domain correctness. Upstream language benchmark tables include revisions; the guide avoids treating older coverage/accuracy rows as definitive. No keys or raw issue inputs are public metadata.
- Files touched: scripts/build_model_catalog.py; laya_portal/model_catalog.py, app.py, schemas.py, service.py, mcp_api.py; frontend ModelGuide, navigation/styles/tests/dev proxy; docs/models.*, agents/api/llms, README; scripts/verify_model_catalog.py and verification tool discovery.
- Validation: 36 Python tests passed; seven browser cases passed across full/focused runs, including two new public guide cases. The initial guide test assumed comma number separators; fixed the assertion to accept the browser's locale. Desktop/mobile screenshots visually checked. Live REST/MCP parity/auth/resources verified; metadata reads preserved GPU allocation, no resident checkpoint and auto default. All three runnable guide examples returned CUDA results. Production frontend build and credential/diff checks passed.
- Status: complete
- Next steps: None required. Catalog updates are deliberate, reviewed and offline; rebuild after config/evidence/source changes and restart to refresh the cached catalog. The service is running on port 8000. No model weights, dependencies, persistent default or sibling integration behavior was changed.
