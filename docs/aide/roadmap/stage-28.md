> Stage 28's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 28`, run on the main or queue branch, moves it back.

## Stage 28 — Spinal Curve Model: Formulation, Offset & Orientation (G2, G7)

**Goal.** The spinal curve is fit with an **interpolating** spline
(`features/spline.py`, `splprep(..., s=0)`), so it passes exactly through every centroid it
is meant to judge. Two features derived from it are therefore structurally incapable of
carrying signal, and one downstream rule can never fire:

- `stage3.per_label_offsets[].offset_mm` is **zero on every case**. Across the nine
  committed goldens its maximum is `6.8e-04` mm against `mislabel`'s `max_offset_mm = 15.0`
  — four orders of magnitude short. It is not synthetic-only: `reference_verse_v1.json`,
  built from real VerSe19 GT, records `spline_offset_mm` with mean `2.9e-05` mm and
  CoV 1.3, i.e. noise about zero. A per-level reference distribution has been committed for
  a feature that measures nothing.
- `stage3.monotonic_consistency.is_monotonic` is **`True` on every case**, including
  `mode4_relabel_swap`. The interpolating spline is fit through the centroids in ascending
  label order, so it detours through the swapped pair and its own parameter increases along
  the detour. Monotonicity is true by construction, never observed.

Eight leaf paths are affected in total — `offset_mm`, `offset_voxel`, `dx_mm`, `dy_mm`,
`dz_mm`, and all three `per_label_neighbourhood[].stats.offset_mm.*`, meaning item 110's
neighbourhood wiring computes mean/median/std of zeros. `MislabelRule` is unreachable
through `run_qc` on any input, which is why 6 of 10 registered rules fire on zero corpus
cases.

**This is one defect, not two.** Stage 20's roadmap entry treats mode 1 (FOV-capped
displacement) and mode 4 (cause "to be determined") as separate reachability holes. Both
are the interpolating fit. A smoothed fit detects the mode-4 swap directly
(`non_monotonic_pairs=(('L2','L3'),)`, clean control unaffected), and no field of view
produces a non-zero offset while `s=0` holds — so Stage 20's proposed FOV-headroom remedy
could not have worked.

**The deliberation comes first.** The formulation is a modelling decision with a clinical
prior, not a parameter to tune until the corpus goes green: the model must be flexible
enough to represent real spinal shape (cervical lordosis / thoracic kyphosis / lumbar
lordosis — an S in the sagittal plane; a coronal curve under scoliosis, single or double)
while being **too stiff to follow a segmentation error**. Those two requirements pull
against each other, and the tension is the whole problem — a curve fit from the centroids
and then used to judge a centroid is circular unless something breaks the circle. So the
stage opens with a recorded design decision, evidenced against real GT, before any
calculation changes.

**Deliverables.**

- **D1 — the spline formulation decision, recorded before implementation.** What family
  (smoothing spline, fixed-knot least-squares B-spline, per-plane low-order polynomial,
  robust/principal-curve fit); how degrees of freedom are set and how they scale with the
  number of levels present, since a field of view may show five lumbar levels or a whole
  spine and a fixed knot count cannot serve both; whether the curve is parameterised by arc
  length or treated as a function of the cranio-caudal coordinate — noting that the latter
  is monotonic by construction and would destroy the mode-4 signal this stage exists to
  restore; how the circularity is broken (leave-one-out, robust down-weighting, or an
  external reference prior); and what a scoliotic spine must be able to express without
  being flagged. Judged against measurable criteria on GT, not argued in the abstract.
  **Raises a human gate** — the deformity envelope the model must represent is a clinical
  judgement, not derivable from the corpus.
- **D2 — the formulation implemented**, replacing `s=0`, with the smoothing/DoF parameter
  expressed in a scale-free form. `splprep`'s `s` is an absolute sum-of-squared-residuals
  bound in mm², so a literal constant cannot survive a change of level count or spacing.
- **D3 — per-vertebra offset that separates.** Including its per-direction components
  (`dx/dy/dz_mm`), which are computed and catalogued today but read by no rule. A
  leave-one-out fit tracks displacement roughly 1:1 (measured: 5 → 6.2 mm, 10 → 10.4 mm,
  15 → 16.0 mm) and is already implemented inside the test harness as
  `_recon_leave_one_out_offset`; promoting it into the pipeline retires mode 1's
  `reconstructed_record` workaround rather than working around it.
- **D4 — tangent-based vertebra orientation.** PCA's `principal_axis` returns exactly
  `(1, 0, 0)` for every vertebra of the default fixture with identical `eigenvalue_ratio`:
  the voxel cloud is a box and PCA finds its widest side, which is left-right on a real
  vertebra too. It carries no per-vertebra information. Both ingredients for the
  replacement already exist — `closest_u` in `spline_offset.py` and `splev(..., der=1)` in
  `orientation.py` — but are never joined: the tangent is evaluated at `fit.u`, not at the
  centroid's closest point, and is collapsed to a scalar angle. Retain `eigenvalue_ratio`
  (real-GT CoV 0.155, genuinely informative); demote `principal_axis`.
- **D5 — signed curvature.** `total_curvature_deg` is `max − min` of the *unsigned* angle to
  the cranio-caudal axis, so it reports 5.702° on the clean fixture whose true tangent sweep
  is 11.4°: it halves a C-curve and cancels a symmetric S-curve — the shape a normal spine
  actually has.
- **D6 — recalibration and regeneration.** `max_offset_mm`, the nine goldens,
  `reference_default.json` and `reference_verse_v1.json`. The VerSe19 cohort is available
  locally (80 CT/GT pairs) and reachable via a gitignored symlink at the documented root, so
  the real artifact is rebuildable rather than stale — see `dataset-verse19.md`, whose
  documented nested layout needs correcting to match.
- **D7 — an observed-range column in the generated feature catalogue.** The catalogue is
  current and its `computation` column is accurate, but it has no column for what a feature
  *does*: `offset_mm`'s row reads healthy while the value is a constant zero, and its
  `status` is `retune`, shared with 65 of 128 rows. Recording each numeric path's observed
  range across the corpus and the reference cohort is the check that would have caught this
  at item 018 instead of after a reference build on real data.

**Scope fence.** The rethink is **bounded to the spline layer**. A sweep of every numeric
leaf path across both populations found no other degenerate feature: the 21 features in the
real-GT reference all carry genuine spread (CoV 0.06–3.6) except `spline_offset_mm`. The
153 paths that are constant across the committed goldens are constant because all nine
fixtures are the same box built from one base — Stage 21's premise, not a feature defect —
and the corpus cannot by itself distinguish the two cases. Do not widen this stage on that
evidence.

**Dependencies.** Stage 26 (✅). **Runs before Stage 20**, for the same reason Stage 26 did
and more directly: Stage 20 audits rule↔mode↔feature traceability and adopts a specificity
ratchet, and this stage changes which rules fire on which cases. Auditing first would
record a matrix that is about to move, and would pin a specificity baseline against a
corpus where `mislabel` cannot fire.

**Validation / acceptance.**

- The formulation decision is recorded with its measurements and signed off at
  its human gate before D2 lands (**G8**).
- A clean GT spine stays within a **1.0 mm** pass-through bound across level
  counts and spacings, while a displaced vertebra separates from the clean
  distribution by a stated margin (**G2**).
- `mislabel` fires through plain `run_qc` on the mode-1 case and `is_monotonic`
  is `False` on the mode-4 case, with the clean control still firing nothing
  (**G2**).
- A real scoliotic curve in the VerSe cohort is not flagged as an offset outlier
  (**G3**).
- Both reference artifacts are rebuilt from real GT and `spline_offset_mm` shows
  real spread; every regenerated golden is byte-reproducible run-to-run
  (**G7**).

**The pass-through bound was raised 0.5 mm → 1.0 mm on 2026-08-28.** This acceptance line
originally reused item 017's AC1 tolerance, which is a *unit* tolerance measured on that
item's own GT-like fixtures, and stretched it over a much wider domain — `build_clean_spine`
at every level count and spacing. The approved smoothing formulation (item 118's gate,
approved 2026-08-27) does not satisfy the stretched version: measured under it, item 017's
fixtures peak at `0.19198` mm while the sweep peaks at `0.552139` mm at 5 levels ×
`(0.8, 0.8, 1.0)` spacing. That is a property of the decision, not a defect — an
interpolating spline passed through every centroid by construction and so satisfied any
bound at all, including on broken input, which is the behaviour item 118 set out to retire.
1.0 mm is sub-voxel at every spacing on the grid and leaves ~1.8× headroom over the measured
peak. Item 017's AC1 keeps its own 0.5 mm tolerance on its own fixtures — it is unaffected
and was not weakened.
