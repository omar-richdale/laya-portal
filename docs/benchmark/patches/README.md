# Review packets for applied sibling changes

These patches include tracked modifications and the new adapter/test/documentation files. They describe the local applied changes and were checked with `git apply --reverse --check`; no patch was applied by that validation. Source checkout commits are in [provenance.json](../provenance.json).

- [Sift](sift.patch): opt-in topic event, unchanged verifier authority, eight-call cap, regression test and source-skill LF checkout rule.
- [vpn-bugsmith](vpn-bugsmith.patch): optional QA cross-check metadata after trusted gates, operator output and regression test.
- [VPN QA](QA_Web_Testing_Agent.patch): optional report metadata, native replay client, adapter tests and explicit card-required trial contract correction.

On a clean matching checkout, review before using `git apply <patch>`. The current local repositories already contain these changes; applying them again would duplicate/conflict. No commit, push, deployment or GitHub issue mutation was performed for these integrations.

The LF rule preserves Sift's original manifest-compatible source-skill bytes. It does not change expected hashes. Local normalized Markdown files have the same Git content as the original LF blobs.
