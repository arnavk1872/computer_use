# Computer Use Research

This repository collects independent computer-use implementations and investigations in one place. Each directory under `apps/` has its own purpose and entry point.

| Directory | What is here | Start with |
| --- | --- | --- |
| [`apps/cua/`](apps/cua/) | The Cua Driver lab: replaceable drivers, capability probes, and a model-driven agent. | [`apps/cua/README.md`](apps/cua/README.md) |
| [`apps/codex-rea/`](apps/codex-rea/) | The Codex computer-use reverse-engineering investigation and native test notes. | [`apps/codex-rea/README.md`](apps/codex-rea/README.md) |

The apps are independent; there is no root package install. For the Cua lab, run its commands from `apps/cua/` (for example, `cd apps/cua && uv sync --locked`). The Codex REA app is research documentation, not an executable integration. Its raw local Evidence and the third-party REA checkout are not committed. The investigation README explains their provenance and limits.

Agents should read [`AGENTS.md`](AGENTS.md) and the relevant app README before making claims or changes.
