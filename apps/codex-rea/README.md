# Codex computer-use REA investigation

This directory preserves research from the local `Codex R-E-A` folder, dated 16 October 2026. It documents the observed architecture of the installed Codex computer-use stack, the REA analysis used to inspect shipped JavaScript packages, and hands-on native UI runs.

1. Read [the investigation](Codex-Computer-Use-REA.md) for architecture, evidence, and limits.
2. Read [the native test runs](Native-Computer-Use-Test-Runs.md) for Calculator, TextEdit, and Finder observations.
3. The [small saved test artifact](native-test-runs/native-cua-test-2026-10-16.txt) corroborates the text content created during the native run.

The analysis used the third-party [REA repository](https://github.com/morluto/rea) at commit [`60bf1024592888b5efb78f9c9458b4633da298bd`](https://github.com/morluto/rea/tree/60bf1024592888b5efb78f9c9458b4633da298bd) (package version 6.5.0). REA is a research tool used in the investigation; its source is not vendored here.

The original local folder also holds approximately 64 MB of raw `evidence/` output and the REA checkout. Those files are intentionally absent from this public repository. The [local Evidence inventory](LOCAL_EVIDENCE.md) records filenames, sizes, and SHA-256 digests. The reports summarize selected results and record limitations; they are not a substitute for the raw artifacts when independent verification is required. Ask the owner for the local folder if a task requires those artifacts.
