# Laya and repository integration diagrams

Four separate descriptive PNGs, generated with the built-in image generation tool:

- [Current local Laya architecture](laya-local.png): portal, authenticated REST/MCP, bounded single GPU worker and offline checkpoints.
- [Laya inside Sift](laya-sift.png): authoritative scanner/intelligence/priority pipeline alongside optional typed shadow metrics. The implemented native hook emits topic metadata; the issue-workflow branch also illustrates the separate available advisory endpoint.
- [Laya with vpn-bugsmith](laya-bugsmith.png): issue-workflow planning lanes and the existing trusted QA repair pipeline. Shadow advice never changes repair selection or permissions.
- [Laya with VPN QA](laya-qa-agent.png): trusted product contract, captured evidence and optional cause metadata alongside authoritative test outcomes.

Solid paths are authoritative; dashed paths represent optional advisory extensions. Laya selects fixed labels and probabilities, not prose guidance or patches. Counts use the captured source-kind inventory (196 dependency, 20 secret, seven code, ten business); the semantic work taxonomy in the report moves two credential-related SAST findings into credential review.

The diagrams are explanatory generated illustrations, not screenshots or proof that a production integration is deployed. Actual applied hooks, live replay results and limitations are in [the report](../benchmark/REPORT.md). Native adapters are local and opt-in. Source prompts and follow-up corrections are retained in `prompts/`.

Sift and Bugsmith diagrams received explicit image-generation edits to show shadow-only metadata with no verifier/repair influence. The QA diagram received a correction to distinguish the GhostShield policy mismatch from TotalGuard token-revocation evidence and to show probability output rather than generated rationales. Original generated images remain in Codex's generation directory; delivered copies are here.
