> Stage 14's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 14`, run on the main or queue branch, moves it back.

## Stage 14 — Real-Data Grounding & Heuristic Recalibration (G3, G7) — ✅

**Goal.** Close the G3 gap the first real-data run exposed: recalibrate and
reshape the heuristics against **real** VerSe-derived distributions so real GT
passes at a high rate, **without** buying that specificity by blinding the rules.
Scoped 2026-07-17. The stage's **measured goal** — **held-out real-GT FPR ≤ 0.10
with no sensitivity regression** against item 057's recorded synthetic baseline —
is an outcome the shipped work aims at but cannot guarantee; it is tracked as two
rows in the [Outcome targets](#outcome-targets) table (both **❌ Not met**), not
as this stage's acceptance. The stage is ✅ because **its planned work shipped and
is verified**; the objectives it feeds (G3, G7) stay 🚧, held there by those unmet
targets. See "Why the goal is not met" below.

**Deliverables.**

- ✅ Default config switches from hand-set to **reference-derived bounds** grounded
  on `reference_verse_v1.json` (the switch exists — item 048 — but the shipped
  default is still the synthetic-calibrated hand-set one). *(Item 090)*
- ✅ **FOV-aware `coverage` / `border` rules** — the largest single contributor.
  Real scans are legitimately partial (cervical-only, lumbar-only): a level
  outside the field of view is *not* a missing level, and a vertebra cut by the
  FOV edge is *not* a border defect. Distinguish "absent though inside FOV"
  (a real failure) from "outside FOV" (normal). *(Item 089)*
- ✅ **`fragmentation` / `bounds` tolerance re-derived from real per-level
  variation** rather than synthetic-clean geometry. *(Item 090)*
- ✅ **Recalibration run** via the Stage-7 `calibrate.py` grid search fitted on the
  VerSe19 **training** subset only, then measured on the **held-out**
  validation/test subsets through the Stage-13 adapter (disjoint cohorts — no
  circularity). *(Item 091)*
- ✅ **Anti-gaming sensitivity guard**: re-run the Stage-5 synthetic corpus **and**
  Stage-5 perturbations applied to **real** VerSe GT, asserting per-mode
  sensitivity does not regress below item 057's baseline. FPR alone is trivially
  driven to 0.0 by loosening rules; the FPR/sensitivity **pair** is the bar.
  *(Item 091)*
- ✅ **Evaluation-harness reference wiring** (found + fixed while executing this
  stage's own held-out measurement): `eval.harness.evaluate_case`/
  `evaluate_cohort` and `eval.calibrate.calibrate_thresholds` called plain
  `run_qc` unconditionally, so items 089/090's reference-derived rules and the
  `reference_delta` rule never engaged when FPR was measured via `segqc evaluate` — only single-case `segqc run` attached a reference. Every
  historical "Real VerSe GT" FPR (item 084's, and this stage's own first
  measurement) was computed against the wrong config. Fixed with an opt-in
  `reference=` parameter (default `None`, byte-identical for every existing
  caller) + `segqc evaluate --reference/--reference-artifact` CLI wiring.
  *(Item 092)*
- ✅ Recorded metrics + the G3 target: **target NOT met** (see below); recorded
  honestly rather than committed as achieved.

**Acceptance.** _(Checks of the built thing — all met. The two **measured
outcomes** this stage aimed at, FPR ≤ 0.10 and no sensitivity regression, are
not acceptance boxes; they live in the [Outcome targets](#outcome-targets)
table, both ❌ Not met, and gate G3/G7 rather than this stage.)_

- [X] The recalibration + held-out measurement pipeline runs end-to-end
  (training-fitted grid search on the VerSe19 training subset, measured on the
  disjoint held-out validation/test subsets through the Stage-13 adapter) and
  records held-out FPR + per-mode sensitivity **honestly**, rather than
  committing a target as achieved.
- [X] The item-092 harness fix (opt-in `reference=`) is in place, so the
  reference-derived rules and `reference_delta` actually engage under `segqc evaluate`/`calibrate_thresholds` — every earlier "Real VerSe GT" FPR had been
  measured against the wrong, reference-less config.
- [X] Every flag on a real case still carries a reason + offending labels
  (explainability is not traded away for specificity — every rule still emits a
  reason + labels).
- [X] The "Real VerSe GT" verification row is updated with the
  post-recalibration number (2026-07-19).

**Why the goal is not met, and what would close the targets.** The stage's
deliverables all shipped (so it is ✅), but its measured G3/G7 targets are not
met and are deliberately held open. Threshold-loosening alone cannot clear the
FPR bar without breaking the sensitivity target: the
`reference_delta` rule compares a per-feature z-score (`robust_z`, computed
against the reference's median/IQR) to a single fixed constant across all
levels/features; real per-level distributions have a heavy tail (median
`robust_z` ≈ 0.7, p90 ≈ 1.5, but max ≈ 25 on an 8-case sample), so a threshold
loose enough to admit the tail is also loose enough to admit a genuinely
fragmented or reordered real level. The grid search used here (a handful of
hand-picked candidate thresholds) is a coarser tool than the percentile-derived
approach `bounds`/`fragmentation` already use (item 090: read the threshold
directly off the training distribution's own percentile grid). Deriving
`reference_delta`'s threshold the same way — directly from the training
cohort's own `robust_z`/`distribution_distance` distribution, rather than
grid-searching guessed constants — is the natural next step. It is **not one of
this stage's deliverables** (it is newly-identified follow-on work), so it is
captured as a `gap` in [`insights.md`](../insights.md) for the feedback loop to
plan into a future queue, rather than retro-added to a closed stage's
deliverable list. The two Outcome targets close when that rework lands and the
held-out FPR/sensitivity are re-measured against the bar.
