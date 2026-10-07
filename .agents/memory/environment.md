# Environment and operation

- Date: 2026-09-30
  Scope: environment
  Topic: Native Windows CUDA environment
  Note: Project uses Python 3.12.10 in .venv and torch 2.10.0+cu128. Global Python has a CPU-only torch build and must remain untouched. RTX 4050 Laptop GPU has 6 GiB VRAM.
  Evidence: CUDA probe and real inference on all three checkpoints succeeded.
  Action for future work: Use .venv/Scripts/python.exe or uv sync --locked. Do not install into global Python.

- Date: 2026-09-30
  Scope: environment
  Topic: Local operation
  Note: Manual start.ps1 / stop.ps1, default port 8000, .env secret, data/settings.json saved default. Server launches offline. Frontend is a Vite build served by Python. No automatic sign-in startup.
  Evidence: Authenticated REST/MCP, desktop/mobile browser tests and graceful stop/restart verified.
  Action for future work: Never print .env or put credentials into docs or screenshots. Stop the service before running verify_gpu.py so two processes do not compete for VRAM.


- Date: 2026-10-01
  Scope: environment
  Topic: Agentic-production checkouts and Windows source hashes
  Note: Bugsmith now lives at C:/Users/richd/Documents/oMAR/Agentic-production/vpn-bugsmith; the original root was removed. Sift, QA_Web_Testing_Agent, VPN_website and total_guard_vpn_website share Agentic-production. Sift's hash-verified docs/assets/skills Markdown must remain LF; its scoped .gitattributes rule preserves the original source hashes. Sibling test Python dependencies are isolated under Laya/.cache/integration-venv.
  Evidence: Destination .git/history verified; Sift's 116 reviewer tests passed after restoring original LF bytes, without changing manifest hashes.
  Action for future work: Resolve sibling paths through Agentic-production and preserve the LF rule. Keep Laya's pinned .venv and global Python packages separate from sibling test dependencies.

- Date: 2026-10-07
  Scope: environment
  Topic: Repository access and reproducible screenshots
  Note: Origin is the private omar-richdale/laya-portal repository. GitHub CLI's globally active account can differ from the saved owner identity; process-local owner authentication with the gh credential helper works without switching the global account. In frontend/, npm run screenshots captures the real production portal via installed Edge, resolves .env relative to its file, preserves the default and writes seven PNGs plus a hash manifest under docs/screenshots.
  Evidence: Remote fetch and repository ownership verified; production capture and all seven screenshot hashes checked.
  Action for future work: Keep credentials process-local and out of command output. Use docs/development.md for capture/verification; distinguish capture date from frozen benchmark/source-review dates. Preserve ignored docs/.obsidian user settings.
