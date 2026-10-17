> Stage 14's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 14`, run on the main or queue branch, moves it back.

## Stage 14 — Real-Data Grounding & Heuristic Recalibration (G3, G7)

**Goal.** Make real ground truth pass. Stages 6/7 calibrated the heuristics
against a synthetic stand-in and recorded an FPR of 0.0; the first real
measurement (2026-07-17, through the Stage-13 adapter) put the **held-out real
VerSe19 FPR at 0.925 (validation) / 0.975 (test)**. The rules are conflating
legitimate real-world variation with failure. This stage re-grounds them in the
real per-level distributions now available in `reference_verse_v1.json` (25
levels, C1…S, from 80 real training subjects).

**The failure is diagnosed, not mysterious.** The four contributing rules, from
the held-out run: `bounds` (4/6 of flagged cases), `fragmentation` (3/6),
`coverage` (3/6 — partial-FOV scans read as "missing levels"), `border` (2/6).
One real case passed entirely clean, which is what rules out a systematic bug and
points at calibration.

**Deliverables.**

- **Reference-derived bounds by default.** Item 048 already built the config
  switch from hand-set to reference-derived bounds; the shipped default is still
  the synthetic-calibrated hand-set one. Ground it on `reference_verse_v1.json`.
- **FOV-aware `coverage` / `border` rules.** The key conceptual fix: real scans
  are legitimately partial (cervical-only, lumbar-only). A level *outside* the
  field of view is not a missing level; a vertebra clipped by the FOV boundary is
  not a border defect. Only levels *expected inside the FOV* may be reported
  missing.
- **`fragmentation` / `bounds` tolerances re-derived** from real per-level
  variation instead of synthetic-clean geometry.
- **Recalibration run** using the Stage-7 `calibrate.py` grid search, fitted on
  the VerSe19 **training** subset and measured on the **held-out**
  validation/test subsets, resolved as disjoint adapter subsets (no circularity —
  the framework sees only "calibration cohort" and "eval cohort").
- **Anti-gaming sensitivity guard.** Re-run the Stage-5 synthetic corpus *and*
  Stage-5 perturbations applied to **real** VerSe GT, asserting per-mode
  sensitivity does not regress below item 057's baseline.
- **Committed G3 target** in `vision.md` §2 + recorded metrics in `progress.md`.

**Dependencies.** Stages 12, 13 (✅ — the real artifact and the adapter exist).

**Validation / acceptance.**

- Target: held-out real VerSe19 GT yields **FPR ≤ 0.10** (**G3**).
- Target: per-mode sensitivity ≥ item 057's synthetic baseline (5/8
  pipeline-detectable modes at 1.0), and those modes still fire on perturbed
  **real** GT (**G7**). *FPR and sensitivity are a **pair**: FPR alone is
  trivially driven to 0.0 by loosening or disabling rules.*
- The recalibration + held-out measurement pipeline runs end-to-end and records
  held-out FPR + per-mode sensitivity honestly, rather than committing a target
  as achieved.
- The evaluation harness engages the reference-derived rules and
  `reference_delta`, so a measured FPR is measured against the shipped config.
- Flags on real cases still carry reasons + offending labels (explainability is
  not traded for specificity).
- The "Real VerSe GT" verification row carries the post-recalibration number.
