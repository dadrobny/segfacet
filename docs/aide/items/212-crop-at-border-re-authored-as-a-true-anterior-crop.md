<!-- aide-template: item 3 -->
# Item 212 — `crop_at_border` re-authored as a true anterior crop

> **Created:** 2026-10-03 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 27 — Feature Schema Taxonomy & Coordinate System (maintenance)
> **Queue:** [`../queue/queue-028.md`](../queue/queue-028.md) · Item 212
> **Objectives:** G2, G7
> **Suggested branch:** `aide/212-crop-at-border-re-authored-as`

---

## Description

This item absorbs two `docs/aide/insights.md` entries: the maintainer's
direction of 2026-10-03 that the corpus case `crop_at_border` should be a crop
and not a shift, and the 2026-09-30 nit that the `split`/`split_own_label`
recipe comments in `src/segfacet/synth/corpus.py` are stale.

Today the committed `crop_at_border` case is built by the legacy
`CropAtBorderPerturbation` (`src/segfacet/synth/coverage_border_overlap.py`).
That operator moves label 22 (L3) margin + 5 voxels toward the anterior face
and clips the overhang. It is a translation, so the fixture also carries an
18.025609 mm interior spline offset on label 22, above `spline_offset`'s
13.0 mm threshold. Only the runner's `fov_truncation` gate (item 191) keeps
that finding out of the pipeline.

**What this item does.**

- **The case is re-authored on item 175's `crop_fov` operator** with
  `face="anterior"`, `target_label=22`, at the shallowest whole-slice cut that
  reaches label 22: one slice of it. The output is a true volume crop, a
  smaller grid with a translated affine, so the case carries its own scan
  fixture, as `crop_fov_si` does. Its id, its `fov_truncation` condition and
  its `border` coverage are kept.
- **`CropFovPerturbation`'s `Expectation` becomes face-aware.** At a
  cranio-caudal face it stays as item 191 left it (nothing fires, verdict
  `pass`). At an in-plane face it expects `border` on every label the cut
  leaves on that face, with verdict `flagged-for-review`, because `border`
  records an in-plane clip as unexpected.
- **The legacy operator stays registered and keeps driving its severity
  ladder**, but no corpus case uses it any more. It is recorded in
  `traceability.UNUSED_OPERATOR_REASONS` (Assumptions, A5).
- **Every test pin on the case's old content is re-measured** under the fence
  in Authorised paths. The probe run recorded in the Testing Strategy found
  54 failing tests in 21 files.
- **The `corpus.py` recipe comments are corrected.** `split` is named as mode
  2, `split_own_label` as mode 3, and the "sub-type (a)/(b)" lettering is
  dropped.

**Not in scope.**

- No rule, detector, threshold, condition gate or `IntendedRule` edge
  changes.
- `src/segfacet/eval/severity_ladder.py` is untouched. The `crop_at_border`
  ladder keeps the legacy operator, its rungs, its margins and its
  cross-mode coupling (Left open).
- The legacy operator is not deleted (Left open).
- `crop_fov_si` is not touched: its content and expectation stay as they are.
- No new corpus case. The case count stays the same.

## Acceptance Criteria

Terms used below:

- **Committed fixtures** are resolved through
  `segfacet.synth.corpus.load_manifest()` and `CORPUS_DIR`, never through a
  hard-coded path. "The case" is the manifest entry whose `case_id` is
  `"crop_at_border"`.
- **"The affine-located sub-block of A at B"** is item 175's definition. Take
  `o = inv(A.affine) @ B.affine[:, 3]`. `o[:3]` is integral, and
  `A.affine[:3, :3] == B.affine[:3, :3]`. The sub-block is
  `A_array[o0:o0+s0, o1:o1+s1, o2:o2+s2]`, where `s` is B's shape.
- **The anterior axis and side** are `resolve_face(img.affine, "anterior")`
  (`segfacet.synth.axes`). **The anterior face slice** of an image is index 0
  on that axis for side `"low"`, and the last index for side `"high"`. Tests
  never assume the axis.
- **The offset threshold** is
  `bundled_default_config().rule_param("spline_offset", "max_offset_mm", default=_DEFAULT_MAX_OFFSET_MM)`,
  read live as `tests/test_151_stage30_validation.py::_max_offset_mm` reads it.

- [ ] **AC1: the case names the volume-crop operator.** The case's
  `perturbation` is `"crop_fov"`, its `perturbation_params["face"]` is
  `"anterior"`, and its `perturbation_params["target_label"]` is `22`.
- [ ] **AC2: the committed case is a crop of the clean control, not a
  translation.** The committed `crop_at_border` seg array equals the committed
  `clean_control` seg's affine-located sub-block at it. The `crop_at_border`
  shape is smaller than `clean_control`'s on the anterior axis and equal on
  the other two.
- [ ] **AC3: the cut is the shallowest that reaches label 22.** Take the
  slices of the committed `clean_control` seg on the anterior axis that lie
  outside the AC2 sub-block. Label 22 occurs on exactly one of them.
- [ ] **AC4: no interior label is displaced past the threshold.** Take
  `extract_feature_record(loaded_seg_image(case), bundled_default_config())`.
  Every `stage3.per_label_offsets` entry with `is_terminal` False has
  `offset_mm` at most the offset threshold.
- [ ] **AC5: the case fires `border` on exactly the labels on its cut face.**
  Let F be the set of non-zero labels on the anterior face slice of the
  committed `crop_at_border` seg array. The set of
  `(f.rule_id, f.detector_id, frozenset(f.labels))` over
  `segfacet.synth.regression.pipeline_findings(case)` equals
  `{("border", "unexpected_clip", frozenset({l})) for l in F}`.
- [ ] **AC6: the operator expects `border` at an in-plane face.** Let `r` be
  `CropFovPerturbation(target_label=22, face="anterior", removed_fraction=0.005).apply(build_clean_spine().seg_img, 0)`.
  `r.expectation.expected_rule_ids == frozenset({"border"})`, and
  `r.expectation.expected_verdict == "flagged-for-review"`.
- [ ] **AC7: the operator's expected labels are the labels on the cut face.**
  For AC6's `r`, `r.expectation.expected_labels` equals the set of non-zero
  labels on the anterior face slice of `r.labelmap`'s array.
- [ ] **AC8: the legacy operator is recorded unused, with a reason.** In
  `segfacet.traceability.build_matrix()`'s exercise report, the operator
  record named `"crop_at_border"` has `state == "unused"` and a non-empty
  `reason`.
- [ ] **AC9: each split recipe comment names the case's live mode.** For each
  of `split` and `split_own_label`, take the comment lines in
  `src/segfacet/synth/corpus.py` between the previous `_RecipeEntry` and that
  case's own `_RecipeEntry(`. They contain `f"mode {m}"`, where `m` is the
  `failure_modes.SPECIFICATION` mode whose `corpus_cases` holds that case id.
  The test is parametrised over the two ids.
- [ ] **AC10: no recipe comment carries sub-type lettering.** The text of
  `src/segfacet/synth/corpus.py` from the `CASE_RECIPE:` line to the line
  that closes its list contains no match of `sub-type \([a-z]\)`.

These criteria close no stage acceptance criterion.

## Assumptions

- **A1 (measured: the depth).** Every value below was measured on
  `aide/queue-028` (2026-10-03) with `CropFovPerturbation` applied to
  `build_clean_spine().seg_img`.
  - The base is RAS, shape (61, 86, 193). Anterior is axis 1, side `"high"`.
  - Label 22 spans axis-1 indices 42–69. From the face, its first slice holds
    155 voxels of 19 437 (0.797 %), then 372 and 589.
  - The shallowest cut that reaches label 22 removes 17 whole slices (indices
    69–85) and takes 155 label-22 voxels. Output shape (61, 69, 193).
  - Any `removed_fraction` in (0, 155/19437 ≈ 0.00797] gives that cut. The
    recipe writes **`removed_fraction=0.005`** explicitly, so a later default
    change cannot move the fixture.

  The builder re-measures every value.

  **Re-checked 2026-10-05 (agrees).** Re-measured on `aide/queue-028` after
  items 209, 210 and 211 merged: RAS (61, 86, 193), anterior axis 1 side
  `"high"`; label 22 spans 42–69, first slices 155, 372, 589 of 19 437
  (0.007974); `removed_fraction=0.005` removes 17 slices, output shape
  (61, 69, 193). Every value above holds.
- **A2 (measured: one cut, three labels on the face).** The lordotic base
  (item 173) puts L1, L2 and L3 at almost the same anterior extent: label 20
  spans axis-1 indices 42–69, label 21 46–70, label 22 42–69. So an anterior
  volume crop that reaches label 22 also cuts labels 20 and 21. L2 is the
  most anterior and loses 1 550 voxels. L1 and L3 lose 155 voxels each.
  Measured on the shallowest cut:
  - all three labels have `touches_anterior`, and no other face flag is set;
  - `pipeline_findings` is exactly three `border.unexpected_clip` findings,
    on [20], [21] and [22], with verdict `flagged-for-review`;
  - no rule other than `border` fires, even before the runner's gate;
  - interior offsets are 0.115125 (21), 0.226480 (22) and 0.084664 (23) mm,
    so `spline_offset`'s own `evaluate` returns nothing;
  - `per_mode.fov_clipped_label_count` reads 3.0 (the legacy case read 1.0);
  - with each case paired with `crop_to_grid(clean_control, case)`,
    `unanchored_foreground_fraction` reads 0.0 (the legacy case read
    0.1429485), and every other per-mode metric sits at its baseline;
  - at three or more target slices, `bounds`' own `evaluate` also fires on
    label 21 and the gate drops it. At one slice it does not fire at all.

  The case therefore expects `border` on {20, 21, 22}, not on {22} alone.
  This is the cut's own geometry on this base, not an operator choice. The
  maintainer may prefer a single-label clip (Left open).

  **Re-checked 2026-10-05 (corrects one bullet; the rest agrees).**
  Re-measured on `aide/queue-028` after items 209, 210 and 211 merged, with
  `CropFovPerturbation(target_label=22, face="anterior", removed_fraction=0.005)`
  on `build_clean_spine().seg_img`:
  - the face slice holds {20, 21, 22}; L1, L2, L3 lose 155, 1 550 and 155
    voxels; each has `touches_anterior` and no other face flag;
  - every registered rule's own `evaluate` returns exactly the three
    `border.unexpected_clip` findings on [20], [21], [22]; `pipeline` gives
    the same three, verdict `flagged-for-review`. Item 210's label-free
    `mislabel` `ordering` detector and item 211's mean-spacing `fused_label`
    do not fire: `monotonic_consistency` is monotonic, with no
    non-monotonic pair and `u_values` [0.0, 0.244872173, 0.483901517,
    0.730771541, 1.0];
  - interior offsets 0.115125 (21), 0.226480 (22), 0.084664 (23) mm;
  - against `crop_to_grid(clean_control, case)`, the per-mode metrics read
    `unanchored_foreground_fraction` 0.0 and `fov_clipped_label_count` 3.0,
    and the other six sit at the clean control's baseline
    (`out_of_order_label_count` 0.0 included).

  **Correction:** the last bullet does not reproduce. `bounds`' own
  `evaluate` does not fire at three target slices. Swept one slice at a
  time, it first fires, on label 21, at **five** target slices (output
  shape (61, 65, 193)), and on {20, 21, 22} from nine. At one to four
  slices it does not fire. The conclusion the bullet supported stands: at
  the one-slice cut this case uses, `bounds` does not fire.
- **A3 (defensible default: the face-aware `Expectation`).** In
  `CropFovPerturbation.apply`, for a `face` in the module's existing
  `_IN_PLANE_FACES`:
  - `expected_rule_ids=frozenset({"border"})`;
  - `expected_labels` = the non-zero labels on the output's face slice
    (index 0 for side `"low"`, the last index for `"high"`), which is exactly
    what `border` reads through `touches_<face>`;
  - `expected_verdict="flagged-for-review"`.

  `failure_mode=CLEAN_CONTROL_MODE` (the name, never a literal `0`; item 175
  A2), the condition, the condition name and the `detail` wording are shared
  with the cranio-caudal branch. The cranio-caudal branch is unchanged, so
  `crop_fov_si`'s manifest entry does not move. Without this change,
  `verify_case` (`tests/test_041_*`) and the ratchet would compare the case
  against an empty expectation while `border` fires.

  **Re-checked 2026-10-05 (agrees).** Item 175's code on `aide/queue-028`:
  `_IN_PLANE_FACES = frozenset({"left", "right", "anterior", "posterior"})`
  is a module constant in `coverage_border_overlap.py`;
  `CropFovPerturbation.apply` resolves `axis, side = resolve_face(...)`
  first; its single `Expectation` uses `failure_mode=CLEAN_CONTROL_MODE`,
  `FOV_TRUNCATION_CONDITION_NAME`, `FOV_TRUNCATION_CONDITION`, empty
  rule ids and labels, and `"pass"`. Applied to the base, today's operator
  still returns that empty expectation at the anterior face, so the branch
  is still needed. The adversarial base
  `as_reoriented([[0, 1], [1, -1], [2, 1]])` resolves anterior to axis 1
  side `"low"` and its index-0 face holds {20, 21, 22}. The
  `face="inferior"`, `target_label=24`, `removed_fraction=0.65` case still
  expects nothing, verdict `pass`.
- **A4 (defensible default: id and attribution kept).** The case keeps id
  `crop_at_border`, `condition="fov_truncation"`, manifest `failure_mode` 0
  and `kind` `"condition"`, and it stays the corpus's `border` fixture (item
  175 D1). The queue names it by that id.
  - Item 157's convention says a case id names its operator. This case no
    longer does: it is named for what it shows, a crop at the border.
  - A rename would move every id pin as well as every content pin, with no
    change in what the case shows.

  **Re-checked 2026-10-05 (agrees).** Item 175's Decisions D1 still records
  the maintainer keeping a `border` case (2026-09-24), and the committed
  case still carries id `crop_at_border` under `fov_truncation`.
- **A5 (defensible default: the legacy operator stays, recorded unused).**
  - `CropAtBorderPerturbation` stays registered as `"crop_at_border"`.
    `SEVERITY_LADDERS["crop_at_border"]` keeps applying it: three cumulative
    anterior clips of labels 20, 21 and 22 on the base grid, stepping
    `fov_clipped_label_count` 1 → 2 → 3.
  - A volume crop cannot step that axis on this base, because one anterior
    cut already clips three labels (A2). It also cannot be scored on the base
    grid: the ladder harness compares candidate and ground-truth (GT) arrays
    of equal shape.
  - So `traceability.UNUSED_OPERATOR_REASONS` gains one entry,
    `"crop_at_border"`. Its reason says that the operator now drives only the
    `fov_truncation` severity ladder, that it is a translation clip kept
    because the ladder's axis needs one grid, and that the corpus case moved
    to `crop_fov` in item 212.
  - `traceability.operator_reason_conflicts()` stays `()`: the operator is
    registered and no `CASE_RECIPE` entry uses it.

  **Re-checked 2026-10-05 (agrees).** On `aide/queue-028`,
  `UNUSED_OPERATOR_REASONS` is `{}` and `operator_reason_conflicts()` is
  `()`. The function reports only an unregistered key or a key a
  `CASE_RECIPE` entry uses, and `perturbation_names()` still lists
  `"crop_at_border"`. `_build_exercise` gives a recipe-less operator
  `state="unused"` with `reason=UNUSED_OPERATOR_REASONS.get(name, "")`, which
  is what AC8 reads. `SEVERITY_LADDERS["crop_at_border"]` still applies the
  legacy operator at `crop_depth` 5 for labels 20, then +21, then +22.
- **A6 (consequence: the ladder home is re-derived, not moved).**
  `_LADDER_HOMES["crop_at_border"]` stays `(None, "fov_truncation")`.
  `tests/test_153_*`'s rule (b) derives a home from the operator's manifest
  cases, and this operator now has none, so the test's derivation is
  re-derived (Testing Strategy, entry 10). The derived value does not change.

  **Re-checked 2026-10-05 (agrees).** `_LADDER_HOMES["crop_at_border"]` reads
  `(None, "fov_truncation")` on `aide/queue-028`. The parenthetical
  "entry 10" is the Testing Strategy's entry 3 (`test_153` rule (b)); the
  claim itself is unchanged.
- **A7 (merged dependencies, read live on `aide/queue-028`).**
  - Item 175: `CropFovPerturbation`, `crop_to_grid`, and `write_corpus`'s
    own-grid scan rule (A6 of item 175). A non-base-grid case writes
    `fixtures/<case_id>_scan.nii.gz`, so this case gains
    `fixtures/crop_at_border_scan.nii.gz` with no writer change.
  - Item 191: the runner's condition gate.
  - Item 172: `operator_reason_conflicts()`.

  **Re-checked 2026-10-05 (agrees).** On `aide/queue-028`:
  - item 175: `crop_to_grid` is in `segfacet.synth.corpus`. The corpus
    builder sets each case's `scan_img = crop_to_grid(clean.scan_img, result.labelmap)`,
    and `write_corpus` writes `fixtures/<case_id>_scan.nii.gz` for any case
    whose scan differs from the base scan in data or affine. So the case
    gains its own scan with no writer change;
  - item 191: `run_rules` drops a finding when any of its labels is in
    `border_touching_labels(record)` and the producing rule does not opt in
    to `fov_truncation`. It then runs the `displaced_vertebra` gate on the
    survivors;
  - item 172: as A5's re-check records.
- **A8: no human gate, and no environment-gated capability.**

## Implementation Steps

1. **`CropFovPerturbation.apply`** (`src/segfacet/synth/coverage_border_overlap.py`)
   gets the in-plane branch of A3. It reuses `_IN_PLANE_FACES`, the
   `axis, side` that `apply` already resolved, and the shared constants.
   Update the class docstring ("Expects nothing to fire" is true only for a
   cranio-caudal face). In the module docstring:
   - the `CropAtBorderPerturbation` bullet says the operator is no longer used
     by the corpus and drives the `fov_truncation` severity ladder (item
     212);
   - the `CropFovPerturbation` bullet says that one case crops at the
     inferior face and one at the anterior face.

   `CropAtBorderPerturbation`'s code is unchanged.
2. **`src/segfacet/synth/corpus.py`.**
   - The `crop_at_border` recipe entry becomes
     `perturbation="crop_fov"`,
     `perturbation_params={"target_label": 22, "face": "anterior", "removed_fraction": 0.005}`.
   - Its comment block is rewritten. It says this is a true anterior volume
     crop at the shallowest whole-slice depth that reaches label 22, that the
     cut also reaches labels 20 and 21 on the lordotic base, and that the case
     is on its own grid with its own scan. It drops the translation and
     18.0 mm text.
   - The `split` comment says mode 2, the `split_own_label` comment says mode
     3, and neither carries "sub-type (a)/(b)" (AC9, AC10).
   - The `_BASE_SCAN_FIXTURE_NAME` comment names both own-grid cases. The
     module docstring's operator list adds `crop_fov` (item 175) beside item
     038's operators.
3. **`src/segfacet/traceability.py`:** add the A5 entry to
   `UNUSED_OPERATOR_REASONS`. Update the module docstring's "empty on this
   tree" wording.
4. **Regenerate the geometric corpus.** Run
   `python -m segfacet.synth.corpus --out <tmp>` twice and diff the bytes,
   then overwrite `tests/corpus/`. Only these may differ from the committed
   tree:
   - `manifest.json` (the `crop_at_border` entry);
   - `fixtures/crop_at_border_seg.nii.gz`;
   - the new `fixtures/crop_at_border_scan.nii.gz`.

   Any other difference is a hand-back.
5. **Re-capture `tests/corpus/094_pre_migration_snapshot.json`** by item
   175's step-5 method: a throwaway mirror of `test_094`'s reader, writing
   bytes with `write_bytes`, not committed.
   - Re-dump `corpus/fixtures/crop_at_border_seg.nii.gz|seg`.
   - Add `corpus/fixtures/crop_at_border_scan.nii.gz|scan`.
   - Every other entry stays byte-unchanged.
6. **`src/segfacet/failure_modes.py`, `_CONDITION_FOV_TRUNCATION`.**
   - Rewrite the `crop_at_border` `CorpusCaseExpectation.reason` from a fresh
     `measured_firing`. It says: a volume crop at the anterior face, the
     shallowest one reaching label 22; `border` fires on the three labels the
     cut leaves on the face; no other rule's own `evaluate` fires; and the
     anterior clip is the rare direction, kept for `border` coverage
     (maintainer, 2026-09-24).
   - The reason must keep the tokens `tests/test_145_*` AC14 reads ("crop" or
     "border", "centroid", and "curve" or "spline"). Phrase the centroid
     sentence as "the one-slice cut moves no interior centroid off the fitted
     spinal curve beyond the threshold".
   - `expected_firing` stays `("border",)`.
   - In the `mechanism`, replace the sentences claiming that the crop
     displaces label 22's centroid and that `spline_offset` fires and is
     gated. Name the three labels the anterior cut reaches.
   - In `_CONDITION_DISPLACED_VERTEBRA.mechanism`, drop the sentences saying
     the crop on `crop_at_border` displaces the centroid and is gated.
   - The module docstring's dated history bullets (items 150, 189) are records
     and are not edited.
7. **`src/segfacet/heuristics/spline_offset.py`, module docstring only.** The
   "Corpus margins" bullet for `crop_at_border` becomes a non-firing interior
   reading: label 22's `0.226480` mm, quoted to six decimals exactly as
   `test_189::test_ac14_recorded_corpus_margins_are_live` formats it. The
   threshold's upper bound now rests on `displace`'s `14.615923` mm alone. Say
   so. The non-firing ceiling (`relabel_swap`'s 5.624555) does not move.
8. **`src/segfacet/heuristics/border.py`, one comment.** The comment above
   `mode_declaration` that names `CropAtBorderPerturbation` as the condition's
   fixture names `CropFovPerturbation` instead. `mode_less_reason` and the
   logic are unchanged.
9. **Regenerate the derived documents** with each module's `main`, twice into
   a temp directory first:
   - `segfacet.failure_modes`;
   - `segfacet.traceability`;
   - `segfacet.synth.corpus_sheet` (`docs/aide/corpus_sheet.png`, whose
     `Source` digest `tests/test_178_*` AC7 checks).

   Also run `segfacet.golden_evidence` into temp. It is predicted
   byte-identical (measured on the probe). A difference is a hand-back.
10. **`docs/aide/golden-decision-table.md`.** Add a Section-1 row for
    `tests/corpus/fixtures/crop_at_border_scan.nii.gz`, worded like the
    `crop_fov_si_scan.nii.gz` row, with disposition `keep`. Add the matching
    `## Divergences` bullet (item 175's step-8 precedent).
11. **Reconcile the existing tests** listed in the Testing Strategy, under the
    fence in Authorised paths. Record every edit in Decisions by node id, with
    old → new.
12. **Run `python .aide/scripts/aide.py scope 212 --base aide/queue-028`** and
    confirm it exits 0.

No dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/synth/coverage_border_overlap.py` — the in-plane `Expectation` branch and the docstrings (step 1).
- `src/segfacet/synth/corpus.py` — the recipe entry and the recipe comments (step 2).
- `src/segfacet/traceability.py` — the `UNUSED_OPERATOR_REASONS` entry (step 3).
- `src/segfacet/failure_modes.py` — the case reason and the two mechanisms (step 6).
- `src/segfacet/heuristics/spline_offset.py` — the module docstring's corpus margins only (step 7).
- `src/segfacet/heuristics/border.py` — one comment naming the fixture's operator (step 8).
- `tests/corpus/manifest.json` — regenerated (step 4).
- `tests/corpus/fixtures/crop_at_border_seg.nii.gz` — regenerated (step 4).
- `tests/corpus/fixtures/crop_at_border_scan.nii.gz` — **new**, the case's own-grid scan (step 4).
- `tests/corpus/094_pre_migration_snapshot.json` — one entry re-dumped, one added (step 5).
- `docs/aide/failure_modes.generated.json` — regenerated (step 9).
- `docs/aide/failure_modes.generated.md` — regenerated (step 9).
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 9).
- `docs/aide/traceability_matrix.generated.md` — regenerated (step 9).
- `docs/aide/corpus_sheet.png` — regenerated (step 9).
- `docs/aide/golden-decision-table.md` — one Section-1 row and one divergences bullet (step 10).
- `tests/test_212_crop_at_border_volume_crop.py` — **new**, this item's test module.
- `tests/test_057_evaluate_cli.py` — reconciliation (b): the cohort pairing.
- `tests/test_089_fov_aware_coverage_border.py` — reconciliation (a): the case's findings snapshot.
- `tests/test_098_stray_components.py` — reconciliation (a): the case's findings snapshot.
- `tests/test_099_per_mode_metrics.py` — reconciliation (a), (b) and (c): the isolation matrix.
- `tests/test_101_compare_runs_cli.py` — reconciliation (b): the cohort pairing.
- `tests/test_102_stage18_validation.py` — reconciliation (a): the case's findings snapshot.
- `tests/test_105_golden_decision_table.py` — reconciliation (a): the fixture inventory count.
- `tests/test_108_affine_faces.py` — reconciliation (a): the case's border labels.
- `tests/test_120_leave_one_out_offset.py` — reconciliation (a): the case's border labels and label 22's offset.
- `tests/test_123_recalibrate_and_regenerate.py` — reconciliation (a): the crop margin literal quoted from `spline_offset.py`'s docstring.
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — reconciliation (a): the case's findings.
- `tests/test_131_tangent_direction_normalisation.py` — reconciliation (a): the case's curve tables.
- `tests/test_132_monotonicity_against_traversal_order.py` — reconciliation (a): the case's `u` values and findings.
- `tests/test_134_decision_table_evidence_companion.py` — reconciliation (a): the post-126 inventory.
- `tests/test_143_s_axis_correction.py` — reconciliation (a): the case's net advance, angles, firing and the snapshot count.
- `tests/test_145_eight_hypothesised_modes.py` — reconciliation (c): AC15's displacement claim.
- `tests/test_151_stage30_validation.py` — reconciliation (c): AC11's offset half.
- `tests/test_153_eval_harness_rekey.py` — reconciliation (b): rule (b) for an operator with no manifest case.

**The reconciliation fence.** It applies to the listed `tests/test_*.py`
files other than this item's own module. **The builder** does the
reconciliation after regeneration, because every new value comes from the
regenerated corpus. Three kinds of change are allowed.

**(a) A moved literal.** A literal value, label set, count or table cell
that this item's re-authored case moved is updated to the fresh
measurement. The assertion keeps its shape and its tolerance and gains a
dated item-212 comment. Prose quoting the literal follows it.

**(b) A re-derived premise.** A constructed input whose stated premise this
item falsified is re-derived. The premises are "the case shares the clean
control's grid" and "every ladder operator has a manifest case". The test
keeps what it asserts.

**(c) A withdrawn claim re-pointed.** This applies only to the three tests
named under (c) in the Testing Strategy. Each asserts that the case
displaces a centroid past the threshold, or that the case needs the
displacement metric's dominance exception. This item withdraws that claim on
purpose. The test gains a dated item-212 docstring line and asserts the
replacement claim stated there. It keeps its name, except for the one rename
allowed below.

No test is retired, skipped, `xfail`-marked or loosened in tolerance. No test
is renamed, with exactly two exceptions, because each old name would state the
opposite of what the test then asserts:

- `tests/test_151_stage30_validation.py::test_ac11_crop_at_border_touches_anterior_and_offset_exceeds_threshold`
  becomes `test_ac11_crop_at_border_touches_anterior_and_offset_within_threshold`;
- `tests/test_099_per_mode_metrics.py::test_ac11_mode6_crop_at_border_is_one`
  becomes `test_ac11_mode6_crop_at_border_is_three`.

Each renamed test records its old name in a dated item-212 docstring line. A
red test in a file not listed here is a hand-back to spec-author, not an
edit.

**Re-run each listed test after editing it.** The probe reports only the
first failing assertion of each test, so a test can hold a second stale
literal behind the first. Edit, re-run, and repeat until the test is green.
A new failure in a listed test is reconciled under the same fence and
recorded in Decisions.

**Asserts against:**

- `src/segfacet/eval/severity_ladder.py` — A5/A6: the legacy ladder, its rungs and `_LADDER_HOMES["crop_at_border"]` stay as they are; the re-derived `test_153` AC19 reads them live.
- `src/segfacet/heuristics/runner.py` — AC5 reads the gated pipeline; the gate is unchanged.

Some paths stay off **May change** on purpose, so `aide scope` refuses them.
The golden-evidence companion and the feature catalogue are predicted to
regenerate byte-identical. Item 175's test module and the specificity ratchet
must pass unedited. `.gitattributes` already covers the new scan through its
`tests/corpus/fixtures/*.nii.gz binary` pin.

## Testing Strategy

**The new module is `tests/test_212_crop_at_border_volume_crop.py`**, with one
test per AC (AC1–AC10). The test-writer writes it.

- Committed fixtures are loaded with `nib.load` from the manifest's
  `seg_fixture`, under `CORPUS_DIR`.
- AC2 and AC3 compute the affine-located sub-block with plain NumPy from the
  two images' affines, as `tests/test_175_*` does. They never call
  `crop_to_grid` or the operator's internals.
- AC5 and AC7 compute the face-slice label set from the array with
  `resolve_face`. They never read `touches_*` or the manifest's
  `expected_labels`, because those are what is being checked.
- AC9 and AC10 read `corpus.py`'s source text, located with
  `Path(segfacet.synth.corpus.__file__)`, and AC9 reads the mode live from
  `failure_modes.SPECIFICATION`.

The queue's other *Testable* claims are already enforced by tests that
iterate the live manifest:

- "its measured firing equals its expected set" is
  `tests/test_163_specificity_ratchet.py::test_ac2_ratchet_measured_equals_expected[geometric-crop_at_border]`;
- the machine-readable record is checked by `tests/test_041_*`'s
  `verify_case` and `test_040` AC17;
- byte-identical regeneration is checked by `test_040` AC16.

Adversarial cases, each written once:

- **`anterior-face-resolved-from-affine`**: apply AC6's operator to
  `build_clean_spine().seg_img.as_reoriented(np.array([[0, 1], [1, -1], [2, 1]]))`.
  That image's anterior face is the **low** end of axis 1.
  `expectation.expected_labels` equals the non-zero labels on index 0 of axis
  1 of the output, and that set is non-empty. This guards a face slice
  hard-coded to the last index, which passes AC7 on the RAS base and names
  the wrong (empty) slice here.
- **`cranio-caudal-expectation-unchanged`**: apply
  `CropFovPerturbation(target_label=24, face="inferior", removed_fraction=0.65)`
  to the default base. `expected_rule_ids` is empty, `expected_labels` is
  empty, and `expected_verdict` is `"pass"`. This guards the in-plane branch
  leaking to every face. That would make `crop_fov_si` expect `border`, which
  `border` suppresses at an expected end.

**Probe run (2026-10-03, the stale-assumption sweep).** Steps 1–4 and 9
(corpus and traceability only, no prose edits) were applied to a copy of the
tree, and the full `tests/` suite was run against it. The copy was run with
`PYTHONPATH` pointing at its own `src`; the editable install here is a plain
`.pth` path entry, so `PYTHONPATH` takes precedence. Result: 8 040 tests, 64
failed.

- 10 of the failures are the copy's own environment and are **not** this
  item's: it had no `.git`, so `git check-attr`, `git show` and `aide check`
  failed. They are `test_111` AC2/AC3, `test_126` AC23, `test_127` AC14,
  `test_128_relocation_checks` AC14, `test_134` AC6, `test_146` adv
  aide-check, `test_155` AC11 ×2 and `test_202` AC11.
- The other **54 failures, in 21 files**, are listed below. Each file is under
  **May change** except the four marked *follows*, which go green with no
  edit once the named step lands.

**(b) Re-derived premises: red without the edit.**

1. **CLI cohorts pairing `crop_at_border` with the full-grid clean control.**
   `segfacet evaluate` exits 1 with
   `compute_overlap: candidate and gt must have identical shape`.
   - `tests/test_101_compare_runs_cli.py`: AC23 ×6, AC24 ×2, AC25 ×4, and
     `test_adv_nonexistent_run_b_path_exits_1`.
   - `tests/test_057_evaluate_cli.py`: AC3, AC4, AC5 ×2, AC6.
   - `tests/test_153_*` AC37/AC38 call `test_101`'s helpers and follow.

   Re-derive the GT: the `"cropped"` case's `gt` points to a fixture written
   into the test's own `tmp_path/fixtures` as
   `crop_to_grid(clean_control seg, crop_at_border seg)`, so it is the clean
   spine seen through the same field of view, as item 175 paired
   `crop_fov_si`. The cohort's `"expected_labels": [22]` becomes the case's
   live expected set {20, 21, 22}, under (a). `test_057_evaluate_cli`'s
   cohort-loading test, which asserts `first.gt` is `clean_control_seg`,
   builds its own dict and was green. It is not edited.
2. **`tests/test_099_per_mode_metrics.py` AC15 ×3**
   (`actual_matrix_matches_frozen_table`, `each_metric_peaks_on_its_own_designated_case`,
   `dominance_exception_is_exact_and_still_needed`). `_build_actual_matrix`
   pairs every case with `_GT_ARRAY`. Pair each case with its own-grid GT
   (`crop_to_grid`), which is the clean control itself for every base-grid
   case. Then, under (a), the `crop_at_border` column of
   `_EXPECTED_ISOLATION_MATRIX` moves:
   `unanchored_foreground_fraction` 0.1429485129517109 → 0.0, and
   `fov_clipped_label_count` 1.0 → 3.0. Under (a) as well, `test_ac11_mode6_crop_at_border_is_one`
   moves 1.0 → 3.0 and is renamed `test_ac11_mode6_crop_at_border_is_three`
   (one of the fence's two allowed renames).
3. **`tests/test_153_eval_harness_rekey.py` AC5, AC11 and AC19.**
   `_manifest_case_id(s)_for_perturbation("crop_at_border")` now finds no
   case.
   - **Re-derive rule (b)** for a ladder operator with no manifest case. Its
     home is read from the operator's own `Expectation`, applying the ladder's
     first non-identity rung step to `build_clean_spine().seg_img` with
     `LADDER_SEED`. `failure_mode` maps to `None` when it is
     `CLEAN_CONTROL_MODE`, and `condition` is read as it stands.
     `_rule_b_home` keeps its manifest route for every operator that has
     cases. AC19's literal `(None, "fov_truncation")` checks still hold.
   - **Re-derive AC11** to find the crop case by `case_id == "crop_at_border"`
     rather than by perturbation. `crop_fov` now has two cases.

**(c) Withdrawn claims, re-pointed (the only three):**

4. `tests/test_145_eight_hypothesised_modes.py::test_ac15_fov_truncation_displacement_claim_holds_live`
   asserts that `border` names one label, which carries a positive interior
   offset. Re-point it to the replacement claim: `border`'s label set equals
   the non-zero labels on the case's anterior face slice, and no interior
   offset of those labels exceeds the offset threshold.
5. `tests/test_151_stage30_validation.py::test_ac11_crop_at_border_touches_anterior_and_offset_exceeds_threshold`:
   keep the `touches_anterior` and `is_terminal False` checks, and invert the
   last assertion to `offset_mm <= threshold`. The test is renamed
   `test_ac11_crop_at_border_touches_anterior_and_offset_within_threshold`
   (one of the fence's two allowed renames). `test_adv_ac11_*` stays as it
   is.
6. `tests/test_099_*::_DOMINANCE_EXCEPTIONS` is emptied, as item 177 R1's
   comment planned ("the exception then ends"), and
   `test_ac15_dominance_exception_is_exact_and_still_needed` is re-pointed.
   It asserts `_DOMINANCE_EXCEPTIONS == {}`, and that on the live matrix
   `row["displace"] > row["crop_at_border"]` for
   `unanchored_foreground_fraction`. The exception is gone because nothing
   needs it.

**(a) Moved literals: red without the edit.** The probe gave these fresh
values; the builder re-measures each.

7. Findings snapshots, where `{("border", (22,))}` moves to three border
   findings on (20,), (21,) and (22,):
   - `tests/test_089_*::test_ac16_committed_corpus_coverage_and_border_findings_unchanged`;
   - `tests/test_098_*::test_ac15_golden_verdict_and_findings_unchanged[crop_at_border]`;
   - `tests/test_102_*::test_ac5_report_verdict_and_findings_match_pre_098_snapshot[crop_at_border]`;
   - `tests/test_108_*::test_ac8_border_and_coverage_presence_and_labels_unchanged[crop_at_border]`;
   - `tests/test_129_*::test_ac29_no_corpus_case_changes_findings`;
   - `tests/test_131_*::test_ac19_no_corpus_case_changes_findings`;
   - `tests/test_132_*::test_ac25_item_129_pre_findings_baseline_reconciled`;
   - `tests/test_143_*::test_ac9_no_rule_firing_set_moves[crop_at_border]`.
8. `tests/test_120_*::test_ac23_border_crop_case_gains_mislabel_finding_border_unchanged`
   carries two moved literals, both under (a):
   - the `border` label union moves {22} → {20, 21, 22};
   - `entry["offset_mm"] == pytest.approx(18.0256, abs=0.05)` for label 22
     moves to the fresh reading, 0.2265 on the probe. Its tolerance stays
     `abs=0.05`, and the comment above it gains an item-212 line.

   This is (a) and not (c): the test pins the offset's value and makes no
   claim that it exceeds the threshold. Its name is kept.
9. Curve tables for the case's row:
   - `tests/test_131_*` AC5 (`tangent_angles_deg`), AC6 (net advance
     −131.974029 → −132.041569), AC7 (`inter_tangent_angles_deg`) and AC21
     (`total_curvature_deg` 73.307982 → 40.007575);
   - `tests/test_132_*::test_ac4_no_clean_case_u_values_move[crop_at_border]`;
   - `tests/test_143_*` AC6 (|net advance|) and AC7 (`tangent_angles_deg`).
10. Fixture inventory, from the new scan:
    - `tests/test_105_*` `test_ac3_current_tree_has_30_non_py_fixtures` and
      `test_adv_ac3_empty_header_only_table_fails_with_full_missing_list`:
      26 → 27;
    - `test_ac3_section1_fixture_set_equals_filesystem_walk_both_directions`
      follows step 10;
    - `tests/test_134_*::_INVENTORY_ADDED_AFTER_126` adds
      `tests/corpus/fixtures/crop_at_border_scan.nii.gz` with an item-212
      comment, which turns `test_ac18_test105_inventory_unchanged_by_this_item`
      green;
    - *follows*: `tests/test_126_*` AC20 ×2 reads `test_105`'s constant and
      the step-10 table.
11. **After step 5**, `tests/test_143_*::test_ac19_snapshot_covers_all_15_entries_across_both_corpora`'s
    snapshot length literal moves by +1. The probe did not re-capture, so it
    stayed green there.
    - *follows*: `tests/test_094_*::test_ac3_*[corpus/fixtures/crop_at_border_seg.nii.gz|seg]`
      after step 5.
12. *follows*: `tests/test_189_*::test_ac14_recorded_corpus_margins_are_live`
    after step 7's docstring. `tests/test_178_*::test_ac7_committed_sheet_is_current`
    follows after step 9's sheet.
13. **After step 7**,
    `tests/test_123_recalibrate_and_regenerate.py::test_ac16_docstring_records_the_margins_and_the_artifact_name`
    goes red, because it requires `"18.025609"` in `spline_offset.py`'s
    docstring. Under (a), the literal in its tuple moves to the six-decimal
    value step 7 writes (`0.226480` on the probe). The sentence in its
    docstring that calls this crop_at_border's "firing reading" becomes a
    dated item-212 line naming it a non-firing interior reading. The probe
    did not edit prose, so this test stayed green there.

**Checked and green on the probe** (no edit): `test_040` (including the
own-grid scan rule and byte-identical regeneration), `test_041`, `test_049`,
`test_090`, `test_116`, `test_163`, `test_172`, `test_175`, `test_189` AC11,
and every other file naming `crop_at_border`.

**Sibling note.** Items in this queue that change what a rule fires
re-measure both corpora's expected sets, and whichever lands second does so
on top of the first (queue-028 scope). Several of the files above, such as
`test_131`, `test_132` and `test_143`, pin per-case tables that a
monotonicity or fused-label change can also move. The later item re-measures
the shared cells.

**Re-check after items 209, 210 and 211 merged (2026-10-05).** Item 212 is
the later item for every shared cell. Measured on `aide/queue-028` with the
re-authored case built by the operator, not yet committed:

- **`test_132` AC4.** Item 210 re-measured `_PRE_ITEM_U_VALUES` as normalised
  arc length along the label-free path. The `crop_at_border` row is now
  [0.0, 0.22390374, 0.469607133, 0.753728411, 1.0]. The re-authored case
  reads [0.0, 0.244872173, 0.483901517, 0.730771541, 1.0]. Entry 9 still
  applies, against 210's row.
- **The case's findings pins are untouched by item 210.** These are
  `test_098`'s golden entry, `test_129`'s `_PRE_129_FINDINGS` and
  `test_120` AC23's `mislabel == []`. Item 210 edited only those files'
  `sequence_break` rows. The re-authored case fires no `mislabel` and no
  `fused_label` finding, so entries 7 and 8 stand as written.
- **Entry 9's curve values hold.** They come from the spline, which items 210
  and 211 did not touch. Net advance is −132.041569, `total_curvature_deg`
  40.007575, `tangent_angles_deg` [5.0652, 0.3074, 7.2771, 18.6393,
  34.9423], and `inter_tangent_angles_deg` [4.757852, 7.584527, 11.362139,
  16.303057].
- **Item 209's `test_155` scanner** walks every `*.py` under `src/segfacet`
  and `tests`. It flags a manifest-case `x["failure_mode"]` /
  `x.get("failure_mode")` access compared to `0` or to `CLEAN_CONTROL_MODE`
  outside an `assert`. Entry 3's re-derived rule (b) therefore reads
  `Expectation.failure_mode`, an attribute the scanner does not track. It
  does not compare a manifest dict's `failure_mode` to that name.
- **The feature catalogue prediction holds.** `catalogue.iter_driver_records`
  builds its records from the operators and never reads `crop_at_border`.
  Its manifest scan reads failure-kind cases only, and this case is a
  condition case. So the catalogue stays off May change.

## Validation

1. Run `python -m segfacet.synth.corpus --out <tmp>` and diff `<tmp>` against
   `tests/corpus/`. Confirm there is no difference.
2. Run
   `.venv/bin/segfacet run --scan tests/corpus/fixtures/crop_at_border_scan.nii.gz --seg tests/corpus/fixtures/crop_at_border_seg.nii.gz --no-reference --out <tmp>`.
   `--no-reference` is required (CLAUDE.md gotcha). Expect
   `flagged-for-review` with exactly three `border` findings, on labels 20, 21
   and 22, and no `spline_offset` finding. Then run the same `--seg` with
   `--scan tests/corpus/fixtures/base_scan.nii.gz`. Expect exit 1 with a
   shape-mismatch message, which shows why the case needs its own scan.
3. Open `docs/aide/corpus_sheet.png` and confirm the `crop_at_border` panel
   shows the anterior edge cut straight across, with no body displaced.
4. Run `python .aide/scripts/aide.py scope 212 --base aide/queue-028` and
   confirm it exits 0.
5. Run `.venv/bin/python -m pytest --collect-only -q` on this branch and on
   `aide/queue-028`. The branch's test-id set must equal the base's set plus
   this item's new tests plus the new `test_094` parametrised id for
   `crop_at_border_scan`, with exactly the fence's two renames applied:
   `test_151`'s `..._offset_exceeds_threshold` →
   `..._offset_within_threshold`, and `test_099`'s
   `test_ac11_mode6_crop_at_border_is_one` → `..._is_three`. Nothing else is
   removed or renamed.

No `[validation]` profile is needed, so there is no ❓ Unverified downgrade
path.

## Dependencies

None open. Item 175 (`crop_fov`, `crop_to_grid`, the own-grid scan writer),
item 191 (the condition gate) and item 172 (`operator_reason_conflicts`) are
merged.

**Downstream and siblings (not blockers):** queue-028's items 210 and 211
re-measure corpus expected sets as well. The queue orders none of them, and
whichever lands later re-measures the shared literals.

## Decisions & Trade-offs

- **D2: implementation (2026-10-05).** Steps 1-10 landed. The geometric
  corpus regenerated twice into scratch with identical bytes, and differs
  from the committed tree only in `manifest.json`,
  `fixtures/crop_at_border_seg.nii.gz` and the new
  `fixtures/crop_at_border_scan.nii.gz`. `golden_evidence` regenerates
  byte-identical. The fresh case reads shape (61, 69, 193); label 22's
  interior offset 0.226480 mm; `tangent_angles_deg` [5.0652315, 0.3073795,
  7.2771474, 18.6392868, 34.942344]; net advance -132.04156876;
  `total_curvature_deg` 40.0075755; `u_values` [0.0, 0.2448721729,
  0.4839015166, 0.7307715411, 1.0]. The test reconciliation (step 11) was
  done by the test-writer before this step (commit 80c7bd1), so the builder
  edited no test.
- **Left open:** re-keying the `fov_truncation` severity ladder onto
  `crop_fov` and then deleting `CropAtBorderPerturbation`. A volume-crop
  ladder needs a severity axis an anterior cut can step on this base, where
  one cut already clips three labels, and GT on each rung's own grid in the
  ladder harness. Both are ladder design, so this belongs to the next ladder
  re-measurement and not to a corpus item.
- **Left open:** whether the maintainer wants the anterior case to clip a
  single label. On the lordotic base, L1–L3 share their anterior extent, so
  only a different base or a non-volume operator could clip L3 alone, and
  either one gives up the true crop this item exists for.
- **D1: queue-028 spec review (2026-10-05).** The maintainer accepted four
  resolutions to the review's findings on this spec.
  1. **(High)** Step 7 moves `spline_offset.py`'s docstring off
     `18.025609`, which
     `tests/test_123_recalibrate_and_regenerate.py::test_ac16_docstring_records_the_margins_and_the_artifact_name`
     requires. That file is added to May change as an (a) moved literal, and
     to the reconciliation list as entry 13.
  2. **(Medium)** `test_120` AC23's second literal, the label-22
     `offset_mm ≈ 18.0256` pin, is named in entry 8 as an (a) moved literal,
     not a fourth (c) test, because it pins a value and claims no threshold.
     The fence now tells the builder to re-run each listed test after editing
     it, since the probe reports only each test's first failing assertion.
  3. **(Low)** The Downstream sentence about item 213 landing first is
     removed: item 213 declares item 212 a blocker, so it cannot land first.
  4. **(Nit)** The fence allows exactly two renames whose old names would
     state the opposite of the new assertions. In `test_151`,
     `..._offset_exceeds_threshold` becomes `..._offset_within_threshold`. In
     `test_099`, `..._crop_at_border_is_one` becomes `..._is_three`. Validation
     step 5's test-id check allows exactly these two.
