> Stage 1's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 1`, run on the main or queue branch, moves it back.

## Stage 1 — End-to-End Thin Slice: Empty Detection + Report (G1, G4)

**Goal.** The smallest *complete* pipeline — input → verdict → report — that
detects empty / trivially-failed segmentations. Proves the full data flow before
any heavy feature work.

**Deliverables.**

- Empty / near-empty detection: no labels, total foreground < N voxels, or
  < K distinct labels — all configurable.
- **QC verdict model**: `pass` / `flagged-for-review` / `fail`, carrying per-case
  and per-vertebra reasons.
- **JSON report schema v0** (machine-readable, versioned).
- **Human-readable report** (Markdown/plain text) rendered from the same model.
- CLI wires loader → empty-check → verdict → both report formats.

**Dependencies.** Stage 0.

**Validation / acceptance.**

- 100% of empty / near-empty fixtures flagged `fail` with an explicit reason
  (**G1**).
- A non-empty fixture passes the empty check.
- JSON validates against the schema; human report generated (**G4**).
- Tests cover the empty-detection thresholds.
