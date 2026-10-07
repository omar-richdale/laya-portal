# Documentation

Laya Local runs three pinned System One checkpoints through one CUDA worker. Use these guides to operate it, choose a model or integrate a client.

| Task | Guide |
|---|---|
| Install and try it | [Project README](../README.md) |
| Start, stop, inspect logs or connect over LAN | [Operations](operations.md) |
| Understand a model or its token limits | [Model guide](models.md) · [JSON catalog](models.json) |
| Call REST or MCP | [Agent integration](agents.md) · [API contract](api.md) |
| Understand inference and memory ownership | [Architecture](architecture.md) |
| Build, test or capture screenshots | [Development](development.md) |
| Review actual GPU checks | [Verification history](verification.md) |
| Review real-data results | [Benchmark report](benchmark/REPORT.md) |
| Integrate Sift, Bugsmith or VPN QA | [System One integrations](system-one-integrations.md) |
| Run examples | [Example clients](../examples/README.md) |
| See the current portal | [Screenshot gallery](screenshots/README.md) |
| Reuse visual material | [Diagrams](diagrams/README.md) · [Presentation](presentation/v1/README.md) |

## Documentation for agents

With the service running, fetch `/llms.txt`, `/docs/agents.md`, `/docs/api.md`, `/docs/models.md`, `/models.json` or `/openapi.json` without a key. Authenticated metadata is at `/api/v1/model-metadata`. Runtime, inference and MCP require the bearer key.

MCP has six tools and four resources. Start with `laya_model_info` or `laya://model-guide`, then read `laya://integration`. Reading metadata does not load a model. Use `laya_status` for current readiness and residency.

## Dates and evidence

- **September 30:** initial GPU/reference parity, REST/MCP and offline checks.
- **October 1:** frozen real-data benchmark, local advisory integrations and reviewed metadata.
- **October 7:** documentation consolidation and new live screenshots.

Screenshots show the UI; their instantaneous latency/memory values are not a benchmark. The benchmark retains its original date and independent reference fields. No weights or calibration were updated during the documentation refresh.
