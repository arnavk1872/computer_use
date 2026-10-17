# Repository guide for agents

- Start at the root README, then read the README for the app relevant to the task.
- `apps/cua/` is the runnable Python lab. Run its `uv` and test commands from that directory; its `pyproject.toml`, `uv.lock`, examples, source, and tests belong together.
- `apps/codex-rea/` contains an investigation of one installed Codex build. Separate directly observed behavior, source-derived findings, inference, and unknowns. Do not turn a single probe into a general performance claim.
- The REA investigation names raw Evidence retained in a local research folder. Those files and the upstream REA checkout are absent from this repository. State that limitation when relying on the reports, and ask for the original Evidence if a task requires independent verification.
- Keep screenshots, captured application data, credentials, and raw reverse-engineering outputs out of commits. The Cua lab writes local reports to ignored `reports/` directories.
