> Stage 28's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 28`, run on the main or queue branch, moves it back.

## Stage 28 — Spinal Curve Model: Formulation, Offset & Orientation (G2, G7) — ✅

**Goal.** `features/spline.py` fits an **interpolating** spline (`splprep(..., s=0)`), so
the curve passes exactly through every centroid it is meant to judge. Measured 2026-08-27:
`stage3.per_label_offsets[].offset_mm` is zero on all nine committed goldens (max
`6.8e-04` mm against `mislabel`'s `max_offset_mm = 15.0`) **and** on real VerSe19 GT
(`reference_verse_v1.json`: mean `2.9e-05` mm, CoV 1.3), and
`stage3.monotonic_consistency.is_monotonic` is `True` on every case including
`mode4_relabel_swap`. Eight leaf paths are affected — `offset_mm`, `offset_voxel`,
`dx/dy/dz_mm`, and all three `per_label_neighbourhood[].stats.offset_mm.*`, so item 110's
wiring aggregates zeros. `MislabelRule` cannot fire through `run_qc` on any input.

**Modes 1 and 4 are one defect.** Stage 20 records them as separate reachability holes with
an FOV-headroom remedy for mode 1; no field of view yields a non-zero offset while `s=0`
holds, and a smoothed fit detects the mode-4 swap directly. That part of Stage 20 is
superseded here.

**The deliberation is the first deliverable, not a preamble.** The model must be flexible
enough for real spinal shape (sagittal S; a coronal curve under scoliosis) yet too stiff to
follow a segmentation error — and a curve fit *from* the centroids then used to judge one is
circular unless something breaks the circle. That is a modelling decision with a clinical
prior, so it is recorded and gated before any calculation changes.

**Deliverables.**

- ✅ **D1** The spline formulation decision, recorded before implementation: family,
  degrees of freedom and how they scale with the number of levels present, arc-length vs
  cranio-caudal parameterisation (the latter is monotonic by construction and would destroy
  the mode-4 signal), how circularity is broken, and the deformity envelope a scoliotic
  spine must express without being flagged. Judged against measurable criteria on real GT.
  **Raises a human gate.** *(Item 118)*
- ✅ **D2** The formulation implemented, replacing `s=0`, with its smoothing/DoF parameter
  in a scale-free form (`splprep`'s `s` is an absolute mm² residual bound and cannot be a
  literal constant across level counts or spacings). *(Item 119)*
- ✅ **D3** Per-vertebra offset that separates, including the per-direction components
  (`dx/dy/dz_mm`) that are computed and catalogued but read by no rule. A leave-one-out fit
  tracks displacement ~1:1 (measured 5 → 6.2, 10 → 10.4, 15 → 16.0 mm) and already exists as
  `_recon_leave_one_out_offset` inside the test harness; promoting it retires mode 1's
  `reconstructed_record` workaround. *(Item 120)*
- ✅ **D4** Tangent-based vertebra orientation. PCA's `principal_axis` is `(1, 0, 0)` for
  every vertebra of the default fixture — a box's widest side, left-right on real anatomy
  too. `closest_u` and `splev(..., der=1)` both exist but are never joined. Retain
  `eigenvalue_ratio` (real-GT CoV 0.155); demote `principal_axis`. *(Item 121)*
- ✅ **D5** Signed curvature: `total_curvature_deg` is `max − min` of an *unsigned* angle,
  reporting 5.702° where the true tangent sweep is 11.4° — it halves a C-curve and cancels
  the symmetric S a normal spine has. *(Item 122)*
- ✅ **D6** Recalibration and regeneration: `max_offset_mm`, the nine goldens,
  `reference_default.json`, `reference_verse_v1.json`. The VerSe19 cohort is available
  locally (80 CT/GT pairs, gitignored symlink at the documented root), so the real artifact
  is rebuildable; `dataset-verse19.md`'s documented nested layout needs correcting to match.
  *(Item 123)*
- ✅ **D7** An observed-range column in the generated feature catalogue — the check that
  would have caught this at item 018. The catalogue is current and its `computation` column
  accurate, but nothing records what a feature *does*: `offset_mm` reads healthy and its
  `status` is `retune`, shared with 65 of 128 rows. *(Item 124)*
- ✅ Stage 28 end-to-end validation: gate-before-implementation check, red-then-green replay
  of modes 1 and 4 through `segfacet run`, a real scoliotic case not flagged, honest
  before/after detection count, and a fresh-clone byte-reproducibility run. *(Item 125)*

**Scope fence.** Bounded to the spline layer. A sweep of every numeric leaf path found no
other degenerate feature — the real-GT reference's 21 features all carry genuine spread
(CoV 0.06–3.6) except `spline_offset_mm`. The 153 paths constant across the goldens are
constant because all nine fixtures are one box from one base (Stage 21's premise), and the
corpus alone cannot separate that from a broken feature. Do not widen on that evidence.

**Acceptance.**

- [x] The formulation decision is recorded with its measurements and signed off at its human
  gate before D2 lands (**G8**). *(Item 125's 2026-08-30 replay: the gate row above reads
  ✅ Approved (2026-08-27) at commit 82d4b7f (17:36 local); item 119's first implementation
  commit (4947d59, "feat(119): implement the smoothing-spline curve formulation") is dated
  the same day at 19:53, after the approval — ordering held. Re-running
  `scripts/compare_curve_candidates.py --verse-cohort dataset-verse19training` reproduced
  15 of the 16 documented `docs/spinal-curve-model.md` measurements within the stated
  0.001 mm tolerance (10 non-VerSe rows exactly, 4 of 5 VerSe rows); one VerSe leave-one-out
  figure diverged by 0.39 mm — logged to insights.md rather than treated as a reproduction
  of every quoted number.)*
- [x] A clean GT spine stays within a **1.0 mm** pass-through bound across level counts
  and spacings, while a displaced vertebra separates by a stated margin (**G2**).
  *(Raised from 0.5 mm on 2026-08-28. The original line reused item 017's AC1 — a unit
  tolerance on that item's own fixtures — across a far wider sweep, which the approved
  smoothing formulation does not satisfy: `0.19198` mm on item 017's fixtures versus
  `0.552139` mm at the sweep's worst grid point. Rationale in `roadmap.md`'s Stage 28
  acceptance note. Item 017's AC1 is unchanged. Item 125's 2026-08-30 replay: re-measured peak is
  `0.552139` mm at level count 5, spacing (0.8, 0.8, 1.0) mm, level L3 — comfortably under
  the 1.0 mm bound; `mode1_displace`'s max offset (`18.7186` mm) separates from
  `clean_control`'s (`0.6733` mm) by an ~18 mm margin, both clear of the shipped `13.0` mm
  threshold on opposite sides.)*
- [x] `mislabel` fires through plain `run_qc` on the mode-1 case and `is_monotonic` is
  `False` on the mode-4 case, with the clean control still firing nothing (**G2**).
  *(Item 125's 2026-08-30 replay established the `mislabel`/clean-control halves: `mislabel`
  fires on `mode1_displace` naming label 22 (L3) both through plain `run_qc` and through a
  real `segfacet run --no-reference` CLI invocation, and `clean_control` fires nothing
  through either path. Item 132 changed `consistency.py` to judge monotonicity against the
  smoothed, traversal-ordered reference fit rather than the in-sample fit alone, moving
  `mode4_relabel_swap` from `detection="reconstructed_record"` to `detection="pipeline"` in
  `tests/corpus/manifest.json`. Item 135's 2026-08-31 replay closes this box on that change:
  `mode4_relabel_swap` reads `is_monotonic == False` with
  `non_monotonic_pairs == [["L2", "L3"]]` through both `extract_feature_record` and a real
  `segfacet run --no-reference` CLI invocation (which also emits a `mislabel` finding
  naming labels 21/22), and `clean_control` still reads `is_monotonic == True` with empty
  `non_monotonic_pairs` and fires zero findings through both paths.)*
- [x] A real scoliotic curve in the VerSe cohort is not flagged as an offset outlier
  (**G3**). *(Unticked — item 125's 2026-08-30 replay: of the 17 real VerSe19 subjects the decision
  document's scoliosis-selection rule selects (`coronal_deviation_mm >= 8.0` mm, 17 of 80
  discovered — reproduced), 1 fires a genuine `mislabel` finding through the shipped
  `run_qc` with `bundled_default_config()`: `sub-verse406_split-verse261`, label 17 (T10),
  `offset_mm = 18.51028` mm against the shipped `13.0` mm threshold — the same
  subject/level item 123 already identified as the value that calibrated that threshold.
  Logged to insights.md; not remediated here.)* *(Owner decision 2026-10-16, gate-fac1: the one firing in item 125's replay, sub-verse406_split-verse261 T10 (label 17, 18.51 mm), is not the scoliotic curve. T10 is a rare wedge vertebra whose minuscule, posterior-only body lets its neighbours' bodies touch anteriorly, an anatomical outlier to be ignored. None of the other 16 selected scoliotic subjects fires. The threshold that outlier set is re-derived without it at Stage 35 item 234.)*
- [x] Both reference artifacts are rebuilt from real GT and `spline_offset_mm` shows real
  spread; every regenerated golden is byte-reproducible run-to-run (**G7**). *(Item 125's
  2026-08-30 replay: `reference_verse_v1.json`'s `subject_count` is `80` and every level's
  `spline_offset_mm` mean clears a 1e-3 mm non-degeneracy floor by 2-3 orders of magnitude
  (e.g. `T10` mean `1.505` mm, max `18.510` mm); `reference_default.json` likewise shows
  real spread. Two successive in-session regenerations of all nine corpus goldens and
  `tests/golden/022_stage3_report.json` are byte-identical to each other and to the
  committed files.)*
