<!-- aide-template: item 2 -->
# Item 177 — `displace` moves mostly left-right

> **Created:** 2026-09-24 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-023.md`](../queue/queue-023.md) · Item 177
> **Objectives:** G2, G7
> **Suggested branch:** `aide/177-displace-moves-mostly-left-right`

---

## Description

This item implements roadmap Stage 33 D2's fourth bullet. It rests on the
`docs/aide/insights.md` entry dated 2026-09-22 (queue-022 review): the
maintainer decided that the `displace` case's displacement should be mostly
left-right, with the anterior-posterior component reduced.

Today the committed case `displace` applies `DisplacePerturbation(target_label=22)`
with the default `displacement_mm=18.0`. The operator splits the magnitude
evenly over the two array axes that are not the stacking axis, and shifts toward
the higher-index end of each. On the RAS base that is 13 voxels toward the right
and 13 voxels toward anterior.

**What this item changes: the case, in place.**

- **Operator.** `DisplacePerturbation` (`"displace"`, in
  `src/segfacet/synth/identity_ordering_alignment.py`) gains a keyword
  `ap_angle_deg: Optional[float] = None`. With a value, the translation is
  resolved anatomically: `displacement_mm·cos θ` toward the **right** face and
  `displacement_mm·sin θ` toward the **anterior** face, in the axial plane,
  each rounded to whole voxels on its own axis. The default (`None`) is
  today's diagonal array-axis split, byte for byte. The severity ladder still
  applies that form (Assumptions, A2).
- **Case.** `displace` keeps its id, its recipe position, its attribution to
  mode 1 (kind `failure`), its target (label 22, L3) and its expected set. Its
  recipe passes `{"target_label": 22, "displacement_mm": 15.0, "ap_angle_deg": 20.0}`,
  which realises **14 voxels right and 5 voxels anterior** (1 mm isotropic, so
  14 mm and 5 mm).
- **Expected set.** Unchanged, re-measured (A3): `mislabel`'s `spline_offset`
  detector still fires on label 22 alone, now at 14.615923 mm against the
  13.0 mm threshold, naming the direction "left-right".

**Not in scope.**

- No rule, detector, threshold, rule declaration or `IntendedRule` edge
  changes. Re-attributing `displace` to a displaced-vertebra condition is D3's
  (next queue).
- `src/segfacet/eval/severity_ladder.py` is untouched. Its `displace` ladder
  keeps the diagonal default, and D3/D4 re-home and re-measure it (A2).
- `src/segfacet/failure_modes.py` is untouched: the case's `expected_firing`
  and its `reason` ("rigidly translated off the fitted spinal curve") stay
  true, so no generated document moves (A3).
- `src/segfacet/heuristics/mislabel.py`'s docstring margins are untouched (A5).
- No new corpus case, and no case-count literal moves.
- The prototype directory is not touched. Item 178 deletes it.

## Acceptance Criteria

Terms used below:

- **"The default base"** is `segfacet.synth.clean_gt.build_clean_spine().seg_img`.
- **"The lateral operator"** is
  `DisplacePerturbation(target_label=22, displacement_mm=15.0, ap_angle_deg=20.0)`,
  applied with seed 0.
- **Anatomical axes.** The L-R axis and its right end come from
  `segfacet.synth.axes.resolve_face(img.affine, "right")`; the A-P axis and its
  anterior end from `resolve_face(img.affine, "anterior")`; the stacking axis
  from `si_axis(img.affine)`. On the default base (axcodes RAS, shape
  (61, 86, 193)) these are array axis 0 with right at the **high** end, array
  axis 1 with anterior at the **high** end, and array axis 2. No test assumes
  that mapping: each resolves it from the affine it is given.
- **"Translated by (r, a, s)"** means the output mask equals the input mask
  shifted by `r` voxels toward the right end of the L-R axis, `a` toward the
  anterior end of the A-P axis and `s` along the stacking axis, with nothing
  wrapped (compare `np.argwhere` coordinate sets).
- **Committed fixtures** are resolved through
  `segfacet.synth.corpus.load_manifest()` and loaded with
  `segfacet.synth.regression.loaded_seg_image`, never by a hard-coded path.

- [ ] **AC1: the target moves 14 right, 5 anterior, 0 along the stack.** On the
  default base, the lateral operator's output label-22 mask is the input
  label-22 mask translated by (14, 5, 0).
- [ ] **AC2: nothing else moves.** Every output voxel outside the input and
  output label-22 masks equals the input voxel.
- [ ] **AC3: the committed fixture is the lateral operator's output.** The
  committed `displace` seg array equals the lateral operator's output array
  when it is applied to the committed `clean_control` seg image.
- [ ] **AC4: the committed displacement is mostly left-right.** In world
  coordinates, the committed `displace` fixture's label-22 centroid minus the
  committed `clean_control` fixture's label-22 centroid (each via
  `segfacet.features.centroids.compute_centroid(...).centroid_mm`) equals
  (+14.0, +5.0, 0.0) mm in RAS, to 1e-9. This is the queue's "L-R component
  dominates its A-P component", as a measured equality: 14 mm against 5 mm.
- [ ] **AC5: the expected set equals the measured firing.** For `c`, the
  `displace` entry of `failure_modes.SPECIFICATION[1].corpus_cases`,
  `failure_modes.measured_firing(c) == c.expected_firing == ("mislabel",)`.

These criteria close no stage acceptance criterion. Stage 33's criterion 2 is
attested by D6.

## Assumptions

- **A1 (defensible default: the case changes in place, not a new case).** The
  queue line, roadmap D2 and the 2026-09-22 maintainer decision all name
  `displace` itself. In place moves no case-count literal, and every consumer
  that iterates the manifest picks the change up unedited. What moves is listed
  in the Testing Strategy. The one consequence that was the maintainer's to
  accept, the isolation-matrix exception, was accepted on 2026-09-24
  (Decisions R1).
- **A2 (defensible default: a keyword on `displace`, not a new operator; the
  ladder keeps the diagonal).**
  - **Why the default stays diagonal.** `eval/severity_ladder.py`'s
    `_displace_ladder` applies `displace` at `displacement_mm` 4, 8, 12 and 16
    with no direction keyword; `tests/test_100_*`, `tests/test_102_*` and
    `tests/test_154_*` pin its rungs, responses and margins. A lateral default
    would also fail its 16 mm rung: at 20 degrees it realises (15, 5) voxels,
    and label 22's L-R extent (voxels 15–45 of 61) leaves room for 14 at most
    with the operator's 1-voxel inset. Re-homing the ladder with the case is
    D3's, and re-measuring it D4's.
  - **Why an angle rather than per-axis millimetres.** `displacement_mm` stays
    the one severity knob (the ladder's), so a later lateral ladder sweeps it
    at a fixed angle. Per-axis keywords would need a refusal for mixing them
    with `displacement_mm`.
  - **The lateral form, on a private copy of the input:**
    1. `lr_axis, lr_side = resolve_face(affine, "right")` and
       `ap_axis, ap_side = resolve_face(affine, "anterior")`.
    2. `r = round(displacement_mm·cos θ / zoom[lr_axis])`,
       `a = round(displacement_mm·sin θ / zoom[ap_axis])`, with θ in radians.
       A component that rounds to 0 is allowed.
    3. The signed shift is `+r` on `lr_axis` when `lr_side == "high"`, else
       `-r`; likewise `a` on `ap_axis`. Nothing moves on the stacking axis.
    4. Refuse with `FacetInputError` when any shifted coordinate falls below
       index 1 or above `shape − 2` on **any** axis (both ends: the side is
       resolved, so the shift may be toward index 0). Refuse a non-finite
       `ap_angle_deg` at construction.
    5. Clear the target, write it at the shifted coordinates.
  - **The `Expectation`.** One call, as today: `failure_mode=1`,
    `expected_rule_ids=frozenset({"mislabel"})`, labels `{target}`, verdict
    `"flagged-for-review"`. Only `detail` is computed per branch. The lateral
    `detail` records the voxel counts, the resolved axes and faces, and that
    the translation is mostly left-right. `catalogue._scan_synth_rule_mode_map`
    reads the same literal as before, so `rule_declaration_conflicts()` stays
    `()` and the catalogue does not move (measured, A3).
- **A3 (measured on this branch, 2026-09-24).** Measured with a probe of A2's
  rule in a scratch copy of the tree (operator and recipe patched, corpus and
  all four generators re-run). The builder re-measures every value.
  - **Fixture.** Label 22's bounding box moves from x 15–45, y 42–69 to
    x 29–59, y 47–74 (z 84–111 unchanged); 19 437 voxels; it touches no face.
  - **Firing.** `run_qc` under `bundled_default_config()` gives one finding:
    `mislabel`/`spline_offset` on [22], reason "… centroid lies 14.6 mm off
    the fitted spinal curve, predominantly left-right (threshold 13.0 mm)."
    Verdict `flagged-for-review`. Before: 17.6 mm, same direction clause.
  - **Offsets.** Label 22 reads 14.615923 mm (dx 14.0, dy 4.157901,
    dz −0.580578); the next-largest is 6.918745 (label 21). Gap 7.697178 mm,
    before 9.247464.
  - **Margin.** 1.616 mm over the 13.0 mm threshold. The maintainer's
    prototype (`scripts/prototypes/2026-09-22-lordotic-corpus/corpus_v2.py`,
    `displace_lr(dx=13, dy=3)`) reads 13.202 mm, a 0.2 mm margin; 14 is the
    most L-R the field of view admits, and 5 keeps the ratio at 2.8.
  - **Curvature.** `stage3.curvature.curvature_plane` moves from `sagittal`
    to `coronal` (coronal 56.331544, sagittal 35.478865): the displacement is
    now in the coronal plane, as intended.
  - **Per-mode metric.** `unanchored_foreground_fraction` (displace vs
    `clean_control`) moves from 0.14814776607487337 to 0.11493031556577983.
    It falls below the legacy `crop_at_border` case's 0.1429485129517109
    (Decisions R1). Any mostly-L-R shift that fits reads below it: A-P must
    reach 12 voxels (with L-R 14) before displace peaks again.
  - **Generated documents.** `failure_modes`, `traceability`, `catalogue`
    (`.json` and `.md`) and `golden_evidence` all regenerate **byte-identical**
    to the committed files. Only `tests/corpus/manifest.json` (the `displace`
    entry: `perturbation_params`, `detail`) and
    `tests/corpus/fixtures/displace_seg.nii.gz` differ.
  - **Cohort.** `displace` stays a detected mode-1 case, so tp/fp/tn/fn,
    sensitivity 10/11 and every per-mode entry are unchanged.
- **A4 (merged dependencies, read live on `aide/queue-023`, not forward pins).**
  - Item 173's `build_clean_spine()`: shape (61, 86, 193), RAS, L3 (22) on
    slices 84–111; the stacking-axis index decreases caudally (unused here: the
    shift is zero along it).
  - Item 175's manifest and `crop_to_grid` pairing; `displace` is on the base
    grid and names `fixtures/base_scan.nii.gz`.
  - Item 176's merged regeneration: this item's measurements were taken on
    top of it.
  - Items 170 and 171: their session fixtures and live-derived negative
    controls apply to any test touched here.
- **A5 (pre-existing, not moved here).** `src/segfacet/heuristics/mislabel.py`'s
  docstring still quotes box-base margins (2.510990, 17.507445, 18.718604),
  and `tests/test_123_*::test_ac16_docstring_records_the_margins_and_the_artifact_name`
  pins those strings in the docstring. That is the open `insights.md` defect
  (item 173, 2026-09-23). This item moves `displace`'s reading again, but D3
  re-homes Detector A and rewrites that docstring, so it is left for D3.
- **A6: no human gate and no environment-gated capability.** R1's decision
  was taken by the maintainer on 2026-09-24, before this spec was committed,
  so no gate row is needed.

## Implementation Steps

1. **`DisplacePerturbation`** in
   `src/segfacet/synth/identity_ordering_alignment.py`, per A2.
   - Import `resolve_face` beside `non_stacking_axes` from
     `segfacet.synth.axes`. Reuse `_present_labels`, `_choose_label`,
     `_require_present`, `_new_image` and `FAILURE_MODE_NAMES`. No dependency
     is added.
   - The diagonal branch's arithmetic, refusal and `detail` string are
     unchanged.
   - Update the class docstring and the module docstring bullet: the diagonal
     default is kept for the severity ladder; the lateral form is the corpus
     fixture (item 177).
2. **Recipe** in `src/segfacet/synth/corpus.py`. The `displace` entry's
   `perturbation_params` becomes
   `{"target_label": 22, "displacement_mm": 15.0, "ap_angle_deg": 20.0}`, with a
   dated item-177 comment: the magnitude is explicit so a default change cannot
   move the fixture, and 14 L-R voxels is the field of view's limit.
3. **Regenerate the geometric corpus.** Run `python -m segfacet.synth.corpus`
   twice into two temp directories and byte-compare them before overwriting.
   Only `tests/corpus/manifest.json` (the `displace` entry) and
   `tests/corpus/fixtures/displace_seg.nii.gz` may differ from the committed
   tree. Any other difference is a hand-back.
4. **Confirm the derived documents do not move.** Run `segfacet.failure_modes`,
   `segfacet.traceability`, `segfacet.catalogue` and `segfacet.golden_evidence`
   into temp and byte-compare each against its committed file. Any difference
   is a hand-back (A3 measured none).
5. **Reconcile the existing tests** listed in the Testing Strategy, under the
   fence in Authorised paths. Record every edit in Decisions, by node id, with
   old → new.
6. Run `python .aide/scripts/aide.py scope 177 --base aide/queue-023` and
   confirm it exits 0.

## Authorised paths

**May change:**

- `src/segfacet/synth/identity_ordering_alignment.py` — the `ap_angle_deg` keyword and lateral branch (step 1).
- `src/segfacet/synth/corpus.py` — the `displace` recipe params and comment (step 2).
- `tests/corpus/manifest.json` — the regenerated `displace` entry (step 3).
- `tests/corpus/fixtures/displace_seg.nii.gz` — the regenerated fixture (step 3).
- `tests/test_177_displace_lateral.py` — **new**: this item's test module.
- `tests/test_098_stray_components.py` — reconciliation (a): the pinned `displace` reason.
- `tests/test_099_per_mode_metrics.py` — reconciliation (a), plus R1's named exception clause.
- `tests/test_120_leave_one_out_offset.py` — reconciliation (a) AC6 and (b) AC17.
- `tests/test_131_tangent_direction_normalisation.py` — reconciliation (a): three `displace` rows.
- `tests/test_132_monotonicity_against_traversal_order.py` — reconciliation (a): the `displace` u-values.
- `tests/corpus/094_pre_migration_snapshot.json` — regenerated artifact: the `displace_seg` entry's `data_sha256` only (amendment 2026-09-24, Testing Strategy entry 7).

**The reconciliation fence.** It applies to the listed `tests/test_*.py` files
other than this item's own module. **The builder** does the reconciliation,
after regeneration, because every new value comes from the regenerated corpus.
Two kinds of change are allowed:

- **(a) A moved literal.** A literal value, reason string or table row that
  this item moved is updated to the fresh measurement. The assertion keeps its
  shape and its tolerance, and gains a dated item-177 comment. Prose that
  quotes the literal follows it.
- **(b) A re-derived premise.** A comparison whose stated premise this item
  falsified is re-derived from live state. The test keeps what it asserts. The
  instance is named in the Testing Strategy.

One change beyond (a) and (b) is authorised, by the maintainer's decision
recorded in Decisions R1: **(c) the isolation-matrix exception** in
`tests/test_099_per_mode_metrics.py`, exactly as the Testing Strategy's entry 2
writes it, and nothing wider.

No test is retired, renamed, skipped, `xfail`-marked or loosened in tolerance;
names that record an old value are kept (items 173–176 precedent). A red test
in a file not listed here is a hand-back to spec-author, not an edit.

**Asserts against:**

- `src/segfacet/eval/severity_ladder.py` — its `displace` ladder applies the diagonal default; unchanged, and `tests/test_100_*`/`tests/test_154_*` keep pinning it.
- `src/segfacet/failure_modes.py` — `displace`'s `expected_firing` stays `("mislabel",)` (AC5).
- `src/segfacet/heuristics/mislabel.py` — threshold and docstring untouched (A5).
- `docs/aide/failure_modes.generated.json` — predicted byte-identical (A3).
- `docs/aide/traceability_matrix.generated.json` — predicted byte-identical (A3).
- `docs/aide/feature_catalogue.generated.json` — predicted byte-identical (A3); `rule_declaration_conflicts()` stays `()`.
- `docs/aide/golden_evidence.generated.json` — predicted byte-identical (A3).

Some paths stay off **May change** on purpose, so `aide scope` refuses them:

- `.gitattributes`: `tests/corpus/manifest.json` (`text eol=lf`) and
  `tests/corpus/fixtures/*.nii.gz` (`binary`) are already pinned.
- `tests/test_123_*`: its AC28 pair reads test_098's constant and follows it;
  its AC16 docstring pin is A5's.
- `tests/test_102_*`: its parametrised verdict/findings test reads test_098's
  constant and follows it.
- The ratchet's module `tests/test_163_*`: it must stay green unedited.
- The prototype directory.

## Testing Strategy

**The new module is `tests/test_177_displace_lateral.py`**, with one test per AC
(AC1–AC5). The test-writer writes it.

- AC1 and AC2 apply the lateral operator to `build_clean_spine().seg_img` and
  resolve every axis and side from its affine through `segfacet.synth.axes`.
- AC3 applies the lateral operator to `loaded_seg_image` of the committed
  `clean_control` case and compares arrays with `np.array_equal`.
- AC4 uses `compute_centroid` on both committed fixtures.
- AC5 uses `failure_modes.measured_firing`.

The queue's other *Testable* claims are already enforced by tests that iterate
the live manifest or specification, and pick up the change with no edit:

- **The corpus regenerates byte-identically.**
  `tests/test_040_synthetic_corpus.py::test_ac16_regeneration_is_byte_identical_across_runs_and_vs_committed`,
  plus `test_143` AC11–AC13.
- **The machine-readable record holds.** `test_040` AC17 rebuilds each case's
  `Expectation` from its recipe, so the operator must accept `ap_angle_deg` in
  `perturbation_params`; `tests/test_041_regression_suite.py` runs
  `verify_case` on every case.
- **The ratchet is green.**
  `tests/test_163_specificity_ratchet.py::test_ac2_ratchet_measured_equals_expected[geometric-displace]`.

Adversarial cases, each written once:

- **`displace-lateral-resolves-axes`**: apply the lateral operator to
  `build_clean_spine().seg_img.as_reoriented(np.array([[1, 1], [0, 1], [2, 1]]))`
  (array axes 0 and 1 swapped, axcodes ARS). Its output array equals the RAS
  output array transposed the same way. This guards taking the L-R axis as
  `non_stacking_axes(...)[0]`, which is L-R only on RAS: that passes AC1–AC4
  and fails here.
- **`displace-lateral-resolves-side`**: apply the lateral operator to
  `build_clean_spine().seg_img.as_reoriented(np.array([[0, -1], [1, 1], [2, 1]]))`
  (axcodes LAS, so right is the **low** end of axis 0). Its output array equals
  the RAS output array flipped the same way. This guards a shift hard-coded
  toward the high index, as the diagonal branch does.
- **`displace-lateral-refuses-low-overflow`**: on the LAS base above,
  `DisplacePerturbation(target_label=22, displacement_mm=15.0, ap_angle_deg=0.0).apply(..., 0)`
  (15 voxels toward right, i.e. toward index 0, where label 22 starts at index
  15) raises `FacetInputError`. This guards a fit check on the high end only,
  which would let the lateral branch write past index 0.
- **`displace-default-form-unchanged`**:
  `DisplacePerturbation(target_label=22).apply(default base, 0)` returns the
  input with label 22 translated by 13 voxels along each of
  `non_stacking_axes(affine)`, toward the high index, and nothing else changed.
  This guards the lateral branch leaking into the default the severity ladder
  applies; `tests/test_100_*` pins the ladder's responses, not the operator's
  exact transform.
- **`displace-lateral-non-mutating`**: after a lateral `apply`, the input array
  is `np.array_equal` to a copy taken before. This guards writing the shift
  into the caller's array, which would corrupt the base that `build_corpus`
  hands the next recipe entry.

**Existing tests to reconcile.** This is the stale-assumption sweep, run
2026-09-24: every test naming `displace` (40 files), a grep of `tests/` for the
old values' literals (17.615, 17.6 mm, the displace offsets, u-values, tangent
and curvature values, 0.148…), and every test iterating the manifest over
`stage3` fields. Each file below is under **May change**, and **the builder**
edits it after regeneration. New values are A3's; the builder re-measures.

**Red without the edit, (a) moved literals:**

1. **`tests/test_098_stray_components.py::_PRE_098_GOLDEN_VERDICT_AND_FINDINGS["displace"]`**:
   the reason's "centroid lies 17.6 mm off" → "centroid lies 14.6 mm off".
   "predominantly left-right" and the live threshold clause stay. Its comment
   block gains an item-177 line. It feeds
   `test_098::test_ac15_golden_verdict_and_findings_unchanged[displace]`,
   `tests/test_102_*`'s verdict/findings parametrisation `[displace]` and
   `tests/test_123_*::test_ac28_*` (both), which follow with no edit.
2. **`tests/test_099_per_mode_metrics.py`:**
   - `_EXPECTED_ISOLATION_MATRIX["unanchored_foreground_fraction"]["displace"]`:
     `0.14814776607487337` → `0.11493031556577983`
     (`test_ac15_actual_matrix_matches_frozen_table`).
   - `test_ac6_mode1_own_case_exceeds_014`: `> 0.14` → `> 0.11`. The name is
     kept.
   - **(c) The isolation-matrix exception (R1, maintainer, 2026-09-24).** Red
     without it: `test_ac15_frozen_table_itself_is_diagonally_dominant` and
     `test_ac15_each_metric_peaks_on_its_own_designated_case`, because the
     `unanchored_foreground_fraction` row's `crop_at_border` cell (0.14295)
     now exceeds its `displace` cell (0.11493). The edit, and nothing else:
     1. Add one module constant beside `_OWN_CASE`:
        `_DOMINANCE_EXCEPTIONS = {"unanchored_foreground_fraction": frozenset({"crop_at_border"})}`,
        with a dated item-177 comment stating: the maintainer's decision
        (2026-09-24, item 177 Decisions R1); why (`crop_at_border` has been a
        condition case since item 150, and its legacy operator is a translation
        of the body, so it reads high on the displacement metric); and when it
        ends (D3 re-homes `displace` and D4 re-measures).
     2. `_is_diagonal_dominant` gains a keyword `exceptions` (default
        `_DOMINANCE_EXCEPTIONS`). In the inner loop, a `cid` in
        `exceptions.get(mode, ())` is skipped, and nothing else is skipped.
        Every other row, and every other case in this row, is still compared
        strictly as before.
     3. The two tests above call it unchanged, so they take the default.
        `test_ac15_negative_control_swapping_mode3_row_into_mode2_breaks_dominance`
        is not edited and still fails dominance on the
        `min_dominant_component_fraction` row.
     4. The builder adds **one** test, as part of this reconciliation:
        `test_ac15_dominance_exception_is_exact_and_still_needed`. It asserts
        that `_DOMINANCE_EXCEPTIONS` names exactly that one (metric, case) pair.
        On the live matrix (`_build_actual_matrix`), it asserts the excepted
        cell still out-reads the own cell:
        `row["crop_at_border"] > row["displace"]` for that metric. So a
        widened exception fails, and so does a stale exception after D3/D4.

     **Why it stays falsifiable.** The `unanchored_foreground_fraction` row
     still fails if `displace` stops strictly out-reading any case other than
     `crop_at_border`. On this base those are `clean_control` 0.0,
     `inject_islands` 0.000279, `force_overlap` 0.075152 and 0.0 for the rest.
     Setting the frozen table's `displace` cell to 0.07 must make
     `_is_diagonal_dominant` return False. The test-writer does not add this
     check: it is the validator's replay, in Validation step 5.
3. **`tests/test_120_leave_one_out_offset.py::test_ac6_mode1_displace_dominant_outlier_exceeds_by_at_least_9mm`**:
   `>= 9.0` → `>= 7.5` (measured gap 7.697178, floored to the half-millimetre
   as the old 9.0 floored 9.247). Docstring "18.719 mm vs 8.701 mm" follows.
   The name is kept.
4. **`tests/test_131_tangent_direction_normalisation.py`**, the `displace` row
   of each of:
   - `_PRE_ITEM_TANGENT_ANGLES_DEG` (AC5):
     `[25.9391, 23.5042, 7.7742, 34.4209, 36.1447]`;
   - `_PRE_ITEM_INTER_TANGENT_ANGLES_DEG` (AC7):
     `[48.936337, 25.787973, 30.209688, 50.406207]`;
   - `_PRE_ITEM_OTHER_CURVATURE_FIELDS` (AC21): total 56.331544, coronal
     56.331544, sagittal 35.478865, `curvature_plane` `"coronal"`, coronal
     angles `[25.89443, -22.28683, -1.465662, 24.377859, -30.437115]`,
     sagittal `[1.753769, -8.274653, 7.638103, 27.204212, 23.455504]`.

   `_PRE_ITEM_NET_ADVANCE_S_MM["displace"]` does not move (no S-I shift).
5. **`tests/test_132_monotonicity_against_traversal_order.py::_PRE_ITEM_U_VALUES["displace"]`**
   (AC4, abs 1e-9):
   `[0.000000561, 0.229606218, 0.479875022, 0.747093991, 0.999999440]`.

**Red without the edit, (b) re-derived premise:**

6. **`tests/test_120_leave_one_out_offset.py::test_ac17_threshold_margins_hold_on_corpus`**:
   `displaced["offset_mm"] > 15.0` → `> _DEFAULT_MAX_OFFSET_MM`, read live from
   `segfacet.heuristics.mislabel`. Its premise, "15.0 is the firing
   threshold", has been false since item 123 (13.0), and this item's 14.616
   falls between. The non-firing ceiling's `< 15.0` excludes `displace` and
   does not move. The name is kept.

**Checked and unaffected** (sweep, 2026-09-24):

- `test_039`: every construction uses the default; its AC20–AC23 factories
  keep the diagonal branch.
- `test_100`, `test_102` (ladder blocks), `test_112`, `test_153`, `test_154`:
  the `displace` ladder is unchanged; `test_112` and `test_101` use the
  committed fixture only in live equivalence checks.
- `test_123::test_ac15_mode1_displace_fires_mislabel_naming_exactly_label_22`,
  `test_120` AC18/AC20, `test_129` (`("mislabel", (22,))`), `test_148`,
  `test_145` AC16 (no face touched: x max 59 of 60) and AC18, `test_116` AC7,
  `test_110` AC11, `test_041`: the firing set, labels and detection are
  unchanged.
- `test_125::test_ac9_*`: 14.616 > 13.0 and the > 5.0 separation floor hold.
- `test_123::test_ac45_*`: `displace` is excluded from the interior ceiling.
- `test_143` AC table (`131.974…`): no S-I component.
- `test_057`, `test_120` AC24, `test_136`, `test_103`: the cohort and the
  rule→mode scan are unchanged.
- `test_105`, `test_126`, `test_157`, `test_151`: case-id lists and document
  digests; no count or document moves.
- `test_018`, `test_022`, `test_024`, `test_119`, `test_129`/`test_130`/`test_135`
  scenarios: synthetic centroids, not the corpus case.

**Regeneration-gated, green once step 3's fixture is committed:** `test_040`
AC15–AC17, `test_143` AC11–AC13, `test_157` AC18, `test_163`.

**Stale but green, not edited** (prose only): `test_125` AC9's "18.7186"
comment, `test_119`'s "18.719 mm" retirement notes, `test_098`'s item-173
comment quoting "displace 18.7 mm", `src/segfacet/heuristics/mislabel.py`'s
docstring (A5), and `identity_ordering_alignment.py`'s
`_DEFAULT_DISPLACEMENT_MM` comment, which still names a 15.0 mm threshold
(the builder may correct it, since the file is under May change).

**Amendment (2026-09-24, after the builder's hand-back B6; entries 1–6, the
sweep's scope and the paths kept off May change stand as the record the item
was specified from).** The 2026-09-24 sweep searched `tests/` for tests naming
`displace` and for the old values' literals. It missed one test because that
test names no case and holds no literal. It reads the fixture's content hash
from a committed snapshot file:

7. **`tests/corpus/094_pre_migration_snapshot.json`**, a regenerated artifact,
   not a test edit. Red without it:
   `tests/test_094_tptbox_image_layer.py::test_ac3_fixture_loads_byte_identically_to_pre_migration_snapshot[corpus/fixtures/displace_seg.nii.gz|seg]`,
   which compares each fixture's loaded-data sha256 against this snapshot.
   - **What changes.** The builder re-captures only the
     `corpus/fixtures/displace_seg.nii.gz|seg` entry's `data_sha256` from the
     regenerated fixture. Measured in B6:
     `e8d5dfeeb6445bedd2f8522b8dd393a767e440b12df1b6fdf99be26ff5c0bd33` →
     `aaf0c2c714b6429419572a121bf114ac0178c90c1a18c00e05ff792dd1ea6839`.
   - **What stays unchanged.** That entry's other fields (`path`,
     `integer_labels`, `shape` (61, 86, 193), `dtype` `int64`, `spacing`,
     `affine`) and every other entry stay byte-for-byte unchanged. The
     re-captured file's diff against the base is that one line.
   - **Method.** It is the item 143 method, restated as item 173 step 4. A
     throwaway script mirrors `test_094`'s own reader: it loads each fixture
     through `segfacet.io.load_volume` with its recorded `integer_labels`,
     takes `sha256` over `np.ascontiguousarray(data).tobytes()`, and writes
     `json.dumps(..., indent=2, sort_keys=True).encode() + b"\n"` with
     `write_bytes`. The script is not committed. Every entry but `displace_seg`
     must come out identical, and that is also the check on the method. If any
     other entry moves, hand back to spec-author; do not commit it.
   - **Line endings.** The file is already pinned `text eol=lf` in
     `.gitattributes` (line 16, `tests/corpus/094_pre_migration_snapshot.json`),
     so `.gitattributes` stays off May change. Writing bytes with `\n` keeps it
     byte-clean on a Windows checkout (CLAUDE.md, Gotchas).
   - **`tests/test_094_tptbox_image_layer.py` is not edited.** It is not
     under May change and needs no change. Items 173, 174 and 175 each
     re-captured this snapshot when they regenerated fixtures.

## Validation

1. Run `python -m segfacet.synth.corpus --out <tmp>` and diff `<tmp>` against
   `tests/corpus/`. Confirm there is no difference.
2. Run
   `.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/displace_seg.nii.gz --no-reference --out <tmp>`.
   `--no-reference` is required (CLAUDE.md gotcha). Expect verdict
   `flagged-for-review` with one `mislabel` finding on label 22 reading
   "14.6 mm … predominantly left-right".
3. Run `python .aide/scripts/aide.py scope 177 --base aide/queue-023` and
   confirm it exits 0.
4. Run `.venv/bin/python -m pytest --collect-only -q` on this branch and on
   `aide/queue-023`. The only differences are the added
   `tests/test_177_displace_lateral.py` tests and the one added
   `tests/test_099_per_mode_metrics.py::test_ac15_dominance_exception_is_exact_and_still_needed`.
5. In a Python session, import `test_099_per_mode_metrics`, deep-copy
   `_EXPECTED_ISOLATION_MATRIX` and set
   `["unanchored_foreground_fraction"]["displace"] = 0.07`. Confirm
   `_is_diagonal_dominant(copy, _EXPECTED_BASELINES, _OWN_CASE)` is `False`,
   because `force_overlap`'s 0.075 now out-reads it. This shows the exception
   did not make the row vacuous.

No `[validation]` profile is needed, so there is no ❓ Unverified downgrade
path.

## Dependencies

- Item 173 (merged into `aide/queue-023`): the lordotic base.
- Item 176 (merged): the manifest this item re-measures on top of.

**Downstream:**

- D3 re-attributes `displace` to the displaced-vertebra condition and re-homes
  its ladder; that item lists `tests/test_177_displace_lateral.py` under May
  change if AC5's expected set moves.
- D4 re-measures the severity ladders, including whether `displace`'s ladder
  takes the lateral form.
- Whichever of D3/D4 ends the isolation-matrix exception (R1) lists
  `tests/test_099_per_mode_metrics.py` under May change.
- Item 178 renders the re-authored case.

## Decisions & Trade-offs

To be updated during implementation.

- **R1: mode 1's metric no longer peaks on `displace`. Decided by the
  maintainer on 2026-09-24: option A.**
  - **The problem.** Item 099's isolation matrix (`tests/test_099_*` AC15)
    asserts that each per-mode metric peaks on its own designated case.
    `unanchored_foreground_fraction`'s own case is `displace`. Measured (A3):
    `displace` now reads 0.11493 and the legacy `crop_at_border` 0.14295, so
    the row is no longer diagonal-dominant. No mostly-L-R shift that fits the
    field of view restores it: A-P must reach 12 voxels beside 14 L-R. Neither
    (a) nor (b) of the fence covers the change.
  - **Options put to the maintainer:**
    - **A:** re-author in place, and exclude `crop_at_border` from that
      row's comparison as a named, dated exception.
    - **B:** add a new lateral case and keep the diagonal `displace`
      (item 175's precedent). Isolation holds, but the corpus gains a
      fifteenth case and its count literals move.
    - **C:** keep isolation with A-P of 12 voxels or more (14:12). That is
      not "mostly" left-right.
  - **Decision: A.** Re-author `displace` in place. In test_099's isolation
    claim, `crop_at_border` is excluded from the
    `unanchored_foreground_fraction` row as a named, dated exception.
    - **Why.** `crop_at_border` has been a condition case since item 150,
      and its legacy operator is effectively a translation (the 2026-09-22
      review).
    - **Until when.** D3 re-homes `displace` and D4 re-measures.
    - **How.** Exactly as the Testing Strategy's entry 2 writes it:
      fence kind (c), authorised by this decision and by nothing else.
    - **It stays falsifiable.** The row still fails if `displace` stops
      strictly out-reading any other case. The exception is pinned exact, and
      pinned still needed.
- **Downstream obligation of R1.** The D3 item that re-homes `displace`, or the
  D4 item that re-measures, must list `tests/test_099_per_mode_metrics.py`
  under May change, because
  `test_ac15_dominance_exception_is_exact_and_still_needed` is built to go red
  when the exception stops being needed.
- **Left open:** whether the `displace` severity ladder should take the
  lateral form. Its 16 mm rung does not fit laterally; D3 re-homes the ladder
  and D4 re-measures it.
- **B1 (builder, 2026-09-24): one `Expectation` call; `detail` per branch.**
  `apply` picks `_shift_diagonal` (the unchanged pre-177 arithmetic, refusal
  and `detail` text) or `_shift_lateral` (A2's rule), each returning
  `(data, detail)`, and builds the single `Expectation(...)` literal the
  catalogue scan reads. Generated documents re-ran byte-identical (see B4).
- **B2 (builder, 2026-09-24): `_new_image` passes `dtype=data.dtype`.** AC3
  applies the operator to `loaded_seg_image(...)`, whose array is `int64`;
  nibabel refuses `Nifti1Image(int64_array, affine)` without an explicit
  dtype (the same reason `loaded_seg_image` passes one, item 040). For every
  other dtype the header already takes the array's dtype, so the output is
  unchanged: the whole corpus regenerated byte-identical after the change.
  Shared by `relabel_swap` and `sequence_break` in the same file.
- **B3 (builder, 2026-09-24): measured values, all equal to A3.** Lateral
  shift 14/5/0 voxels (right, anterior, stack). Firing: one
  `mislabel`/`spline_offset` on [22], "14.6 mm … predominantly left-right
  (threshold 13.0 mm)", verdict `flagged-for-review`. Offsets: label 22
  14.615923365 mm (dx 14.0, dy 4.157901, dz −0.580578), next label 21
  6.918745057, gap 7.697178. `unanchored_foreground_fraction` displace
  0.11493031556577983 vs `crop_at_border` 0.1429485129517109. Curvature plane
  `coronal` (56.331544 / sagittal 35.478865). Validation step 5 replay: the
  frozen table with displace = 0.07 is not diagonal-dominant (True → False).
- **B4 (builder, 2026-09-24): regeneration.** `python -m segfacet.synth.corpus`
  run twice into temp: byte-identical to each other; against the committed
  tree only `tests/corpus/manifest.json` (the `displace` entry's `detail` and
  `perturbation_params`) and `tests/corpus/fixtures/displace_seg.nii.gz`
  differ. `failure_modes`, `traceability`, `catalogue` (`.json`, `.md`) and
  `golden_evidence` regenerate byte-identical to the committed files.
- **B5 (builder, 2026-09-24): reconciled tests, old → new.**
  - `test_098::_PRE_098_GOLDEN_VERDICT_AND_FINDINGS["displace"]` reason:
    "17.6 mm" → "14.6 mm" (a).
  - `test_099::_EXPECTED_ISOLATION_MATRIX["unanchored_foreground_fraction"]["displace"]`:
    0.14814776607487337 → 0.11493031556577983 (a).
  - `test_099::test_ac6_mode1_own_case_exceeds_014`: `> 0.14` → `> 0.11` (a).
  - `test_099`: `_DOMINANCE_EXCEPTIONS`, the `exceptions=` keyword on
    `_is_diagonal_dominant`, and
    `test_ac15_dominance_exception_is_exact_and_still_needed` (c, R1).
  - `test_120::test_ac6_mode1_displace_dominant_outlier_exceeds_by_at_least_9mm`:
    `>= 9.0` → `>= 7.5`; docstring gains "14.616 mm vs 6.919 mm" (a).
  - `test_120::test_ac17_threshold_margins_hold_on_corpus`: `> 15.0` →
    `> _DEFAULT_MAX_OFFSET_MM` read live from `segfacet.heuristics.mislabel` (b).
  - `test_131` `displace` rows: tangent angles `[27.8284, 27.8378, 6.0299,
    41.7355, 26.6063]` → `[25.9391, 23.5042, 7.7742, 34.4209, 36.1447]`;
    inter-tangent `[55.387489, 30.552099, 38.203632, 53.0888]` →
    `[48.936337, 25.787973, 30.209688, 50.406207]`; other curvature fields
    total/coronal/sagittal 58.548579/49.467784/58.548579 plane `sagittal` →
    56.331544/56.331544/35.478865 plane `coronal`, coronal angles and sagittal
    angles to A3's values (a).
  - `test_132::_PRE_ITEM_U_VALUES["displace"]`: `[.., 0.222516283,
    0.473947274, 0.754651307, ..]` → `[.., 0.229606218, 0.479875022,
    0.747093991, ..]` (a).
- **B6 (builder, 2026-09-24): handed back, a red test off the list.**
  `tests/test_094_tptbox_image_layer.py::test_ac3_fixture_loads_byte_identically_to_pre_migration_snapshot[corpus/fixtures/displace_seg.nii.gz|seg]`
  fails: it compares the loaded fixture's sha256 against
  `tests/corpus/094_pre_migration_snapshot.json`, which is not under **May
  change** and which the stale-assumption sweep did not name. Items 173, 174
  and 175 each updated that snapshot when they regenerated fixtures. Measured:
  only the entry's `data_sha256` moves,
  `e8d5dfeeb6445bedd2f8522b8dd393a767e440b12df1b6fdf99be26ff5c0bd33` →
  `aaf0c2c714b6429419572a121bf114ac0178c90c1a18c00e05ff792dd1ea6839`; shape
  (61, 86, 193), dtype int64, spacing and affine unchanged. Every other test in
  the full suite is green.
- **B7 (builder, 2026-09-24): 094 snapshot re-captured (Testing Strategy
  entry 7).** A throwaway script mirroring `test_094`'s reader re-hashed every
  entry and wrote bytes with `\n`. Only
  `corpus/fixtures/displace_seg.nii.gz|seg`'s `data_sha256` moved
  (`e8d5dfee…c0bd33` → `aaf0c2c7…1ea6839`), and the file's diff is that one
  line. Every other entry came out identical.
