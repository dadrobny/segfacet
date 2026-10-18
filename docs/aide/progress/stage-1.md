> Stage 1's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 1`, run on the main or queue branch, moves it back.

## Stage 1 — End-to-End Thin Slice: Empty Detection + Report (G1, G4) — ✅

**Goal.** Smallest complete pipeline (input → verdict → report) detecting
empty / trivially-failed segmentations.

**Deliverables.**

- ✅ Empty / near-empty detection (no labels, foreground < N voxels, < K labels), configurable. *(Item 007)*
- ✅ QC verdict model: `pass` / `flagged-for-review` / `fail` with per-case + per-vertebra reasons. *(Item 008)*
- ✅ JSON report schema v0 (machine-readable, versioned). *(Item 009)*
- ✅ Human-readable report (Markdown/plain text) from the same model. *(Item 010)*
- ✅ CLI wires loader → empty-check → verdict → both report formats. *(Item 010)*
  - **2026-10-17** → item 006 taken off this bullet's marker by item 236: item 006's deliverable is the CLI entry point, Stage 0's bullet, which this wiring extends.

**Acceptance.**

- [X] 100% of empty / near-empty fixtures flagged `fail` with explicit reason (**G1**). *(`test_007_empty_detection.py`)*
- [X] A non-empty fixture passes the empty check. *(`test_007_empty_detection.py`)*
- [X] JSON validates against schema; human report generated (**G4**). *(`test_009_json_report.py`, `test_010_human_report.py`)*
- [X] Tests cover empty-detection thresholds. *(`test_007_empty_detection.py`)*
