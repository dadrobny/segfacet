<!-- aide-template: item 2 -->
# Item 175 — `crop_at_border` as a crop of the volume

> **Created:** 2026-09-24 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-023.md`](../queue/queue-023.md) · Item 175
> **Objectives:** G2, G7
> **Suggested branch:** `aide/175-crop-at-border-as-a`

---

## Description

This item implements roadmap Stage 33 D2's second bullet. It rests on three
`docs/aide/insights.md` entries, all dated 2026-09-22:

- the maintainer decision on `crop_at_border`;
- the fused-case entry, which settles the 65 % inferior cut depth;
- the prototype entry, which records `crop_inferior` in
  `scripts/prototypes/2026-09-22-lordotic-corpus/corpus_v2.py`.

Today's `crop_at_border` operator does not crop the field of view (FOV). It
moves label 22 (L3) 5 voxels past the **anterior** face and clips the part
that overhangs. It is a displacement, and the maintainer's contact sheet
shows exactly that.

**What this item adds: a new operator and a new case. The legacy case stays.**
The maintainer decided on 2026-09-24 that a committed case must keep firing
`border` (Decisions, D1).

- **Operator `crop_fov`** (`CropFovPerturbation`, in
  `src/segfacet/synth/coverage_border_overlap.py`). It crops the whole volume
  at a named image face. The face is resolved from the input's own affine.
  The cut is the smallest whole-slice cut that removes at least a given
  fraction of a target label's voxels. The output is the sub-block of the
  input grid on the far side of the cut, and its affine is translated so
  every kept voxel stays at its world position.
- **Case `crop_fov_si`: the S-I FOV crop.** It applies
  `crop_fov(target_label=24, face="inferior", removed_fraction=0.65)` to the
  clean control. The result is L5 cut by the inferior image face. This is the
  common, realistic FOV truncation, the "expected end" form of the
  `fov_truncation` condition. It is the fixture the next queue's border gating
  of the size rules (roadmap Stage 33 D3) is measured on.
- **The legacy case `crop_at_border` keeps its id, operator, content and
  expected firing** (`border`, `mislabel` on label 22). It is kept because it
  is the corpus's only `border` firing. It is not kept as a realistic crop: an
  anterior clip is the rare direction (Decisions, D2).

Both cases are fixtures of `failure_modes.CONDITIONS["fov_truncation"]`:
`crop_at_border` for the unexpected, in-plane form, and `crop_fov_si` for the
expected, cranio-caudal form. The new case's `expected_firing` records what
fires today, `("bounds",)`. `border` suppresses an expected-end touch by
default, so it does not fire.

The new case lives on a **smaller grid** than the base, so it carries its own
scan fixture. `segfacet.io.load_case` rejects a scan and a segmentation that
differ in shape or affine, and so does `segfacet.eval.overlap.compute_overlap`.
A public helper `segfacet.synth.corpus.crop_to_grid` cuts a base-grid image to
a sub-grid. It serves two consumers:

- the corpus writer, for the new scan;
- the four test cohort builders that pair every case with the clean control,
  which now pair each case with the clean control on that case's own grid.

**Not in scope.**

- No rule, detector, threshold or `IntendedRule` edge changes. Border gating of
  `bounds` and `reference_delta` is D3's.
- `src/segfacet/eval/severity_ladder.py` is untouched. The legacy operator
  still drives its `crop_at_border` ladder, so nothing is re-transcribed and
  `tests/test_100_*`/`tests/test_154_*` do not move.
- No `UNUSED_OPERATOR_REASONS` entry. Every registered operator stays used.
- The legacy case's content and face are not changed (Decisions, D2).
- The `mislabel.py` docstring margins are not touched. They belong to the
  item-173 insight, and their `crop_at_border` quote stays true.
- The prototype directory is not touched. Item 178 deletes it.
- No LR crop case (Left open).

## Acceptance Criteria

Terms used below:

- **"The default base"** is `segfacet.synth.clean_gt.build_clean_spine().seg_img`.
- **"The affine-located sub-block of A at B"** is found as follows. Take
  `o = inv(A.affine) @ B.affine[:, 3]`. `o[:3]` is integral, and
  `A.affine[:3, :3] == B.affine[:3, :3]`. The sub-block is
  `A_array[o0:o0+s0, o1:o1+s1, o2:o2+s2]`, where `s` is B's shape.
- **Committed fixtures** are resolved through
  `segfacet.synth.corpus.load_manifest()` and `CORPUS_DIR`, never a
  hard-coded path.
- **Stacking axis.** On this base the stacking axis is array axis 2, and its
  index **decreases caudally**: L5 (24) lies on slices 15–48 and L1 (20) on
  150–177. Every "which end" in a test is resolved with
  `segfacet.synth.axes.resolve_face` on the image's own affine, never assumed.

- [ ] **AC1: `crop_fov` is a crop, not a translation.**
  `CropFovPerturbation(target_label=24, face="inferior", removed_fraction=0.65).apply(default base, 0)`
  returns an image whose array equals the default base's affine-located
  sub-block at that image.
- [ ] **AC2: the target is cut by the requested face.** In AC1's output, take
  the face slice resolved by `resolve_face(out.affine, "inferior")`: index 0
  on the axis for a `"low"` side, the last index for a `"high"` side. That
  slice contains label 24.
- [ ] **AC3: the cut is the smallest whole-slice cut removing at least the
  fraction.** For AC1, let N be the input's label-24 voxel count and R be N
  minus the output's label-24 voxel count. Then `R >= 0.65 * N`. Also,
  `R` minus the input's label-24 count on the removed slice nearest the kept
  side is `< 0.65 * N`.
- [ ] **AC4: the committed `crop_fov_si` fixture is a volume crop of
  `clean_control`.** The committed `crop_fov_si` seg array equals the
  committed `clean_control` seg's affine-located sub-block at it. The
  `crop_fov_si` shape is smaller than `clean_control`'s on the stacking axis.
- [ ] **AC5: the truncated L5's volume.** Take the `extract_feature_record`
  of each committed fixture under `bundled_default_config()`. The
  `crop_fov_si` value `per_label["24"]["geometry"]["physical_volume_mm3"]`
  is at most 0.35 × the `clean_control` value.
- [ ] **AC6: the truncated L5's S-I extent.** For the same records,
  `crop_fov_si`'s label-24 `extent_z_mm` (array axis 2, the stacking axis) is
  smaller than `clean_control`'s.
- [ ] **AC7: only the inferior face is touched.** For the same `crop_fov_si`
  record, collect every pair `(label, face_flag)` where
  `per_label[label]["geometry"][face_flag]` is True and `face_flag` is one of
  the six `touches_*` keys. That set equals `{("24", "touches_inferior")}`.
- [ ] **AC8: the case's scan is the base scan on the case's grid.** The
  committed `crop_fov_si` scan fixture matches the seg fixture's shape, and
  its affine is `np.allclose` to the seg fixture's. Its array equals the
  committed `clean_control` case's scan fixture's affine-located sub-block at
  it.
- [ ] **AC9: the case fires `bounds` on the remnant and nothing else.** Take
  the committed `crop_fov_si` manifest case. The set of
  `(f.rule_id, f.detector_id, frozenset(f.labels))` over
  `segfacet.synth.regression.pipeline_findings(case)` equals
  `{("bounds", "metric_out_of_range", frozenset({24}))}`.
- [ ] **AC10: both crops are the condition's fixtures.** Take the case ids of
  `failure_modes.CONDITIONS["fov_truncation"].corpus_cases`. They equal the
  set of committed geometric manifest case ids whose `condition` is
  `"fov_truncation"`, recomputed live. That set is
  `{"crop_at_border", "crop_fov_si"}`.
- [ ] **AC11: a committed case still fires `border`.** `"border"` is in
  `set(failure_modes.measured_firing(c))` for the `crop_at_border` entry of
  `CONDITIONS["fov_truncation"].corpus_cases`.

These criteria close no stage acceptance criterion. Stage 33's criteria are
closed by D5 and D6.

## Assumptions

- **A1 (defensible default: a true crop).** The output grid is a proper
  sub-block of the input grid, and its affine is translated. It is built with
  nibabel's `SpatialImage.slicer` (already a dependency), and the slab's data
  is copied so the result is never a view of the input. Two alternatives were
  rejected:
  - **Same shape, translated affine, content shifted.** This keeps the array
    shape but shifts every voxel's index. Array-indexed consumers such as
    `compute_overlap` against `clean_control` then compare misaligned voxels
    without raising.
  - **Same shape and same affine, content shifted.** This moves the whole
    spine in world space, which is a translation, the thing the queue rules
    out.

  The true crop fails loudly at every same-grid consumer, and each consumer is
  re-derived below.
- **A2 (defensible default: the operator).** `CropFovPerturbation`, registered
  as `"crop_fov"`, with keyword arguments `target_label: Optional[int] = None`,
  `face: str = "inferior"` and `removed_fraction: float = 0.65`.
  - **The face.** It is validated eagerly (`_validate_face_name`) and resolved
    at `apply()` time with `resolve_face(labelmap.affine, face)`. Any of the
    six faces works, so an LR crop later is a recipe change (Left open).
  - **The cut.** Walk the target's slices from its face-side extreme toward
    the far side. The cut is the smallest number of whole slices, counted from
    that extreme, whose target voxel count reaches at least
    `removed_fraction × N`. Every slice from the face through the last counted
    slice is removed.
  - **Refusals.** Each raises `FacetInputError`: `removed_fraction` outside
    (0, 1); a target absent from the map; an input with no labels; and a cut
    that would remove every slice of the target.
  - **Unspecified target.** `_choose_label(labels, seed)` picks it, like the
    sibling operators.
  - **The `Expectation`.**
    - `failure_mode=CLEAN_CONTROL_MODE`, written as the **name**, never a
      literal `0`. `catalogue._scan_synth_rule_mode_map` reads only literal
      ints, so the name keeps `bounds → (0,)` out of the corpus rule-mode map.
      That map feeds `catalogue.rule_declaration_conflicts` and
      `tests/test_103_*`/`test_136_*`/`test_156_*`. This is the legacy
      operator's own idiom.
    - `failure_mode_name=FOV_TRUNCATION_CONDITION_NAME` and
      `condition=FOV_TRUNCATION_CONDITION`.
    - `expected_rule_ids=frozenset({"bounds"})`, which is what fires today
      (queue), and `expected_labels=frozenset({target})`.
    - `expected_verdict="flagged-for-review"`.
    - The `detail` records the face, the requested fraction, the removed slice
      count, the removed and target voxel counts and the output shape. It
      makes no claim about which detectors fire.
- **A3 (measured, and different from the queue line: the fraction).** The
  queue quotes "removes 65 % of L5 (L5 remnant ≈ 7 719 mm³ on the prototype)".
  Those two numbers disagree:
  - The prototype cuts at `int(np.quantile(z, 0.65))`, which is slice 34. It
    keeps 7 719 voxels, so it removes **60.1 %**.
  - The smallest whole-slice cut that removes at least 65 % is slice 35. It
    removes 12 586 of 19 344 voxels (**65.06 %**) and keeps **6 758 mm³**.

  This item takes the words, "at least 65 %", by item 174's at-least rule.
  That also avoids a threshold coincidence: the prototype's cut leaves
  `extent_z` at exactly 15 mm, which is `bounds`' lumbar minimum. Measured on
  this branch, 2026-09-24:
  - output shape (61, 86, 158) against the base's (61, 86, 193);
  - affine translation z = 35 with an unchanged rotation;
  - labels 20–23 complete, and label 24 keeping 6 758 voxels;
  - extents 31/30/14 mm; `touches_inferior` only;
  - `run_qc` gives verdict `flagged-for-review` with exactly two findings,
    both `bounds.metric_out_of_range` on [24]: volume 6758 < 8000, and
    `extent_z` 14 < 15;
  - no `border` finding (expected end suppressed), no `mislabel` finding;
  - interior spline offsets at most 1.048 mm;
  - every principal axis is L-R, with residue ≤ 3.2e-16;
  - no report float collides with `tests/report_format_fixture.py`'s
    distinctive literals.

  The builder re-measures every value.
- **A4 (defensible default: naming).** The case id is `crop_fov_si`, named
  after its operator plus the crop direction the maintainer asked for (item
  157's convention: a case id names its operator). The new fixture files are
  `tests/corpus/fixtures/crop_fov_si_seg.nii.gz` and
  `tests/corpus/fixtures/crop_fov_si_scan.nii.gz`. The recipe entry is
  appended after `split_own_label`:
  `_RecipeEntry(case_id="crop_fov_si", perturbation="crop_fov", perturbation_params={"target_label": 24, "face": "inferior", "removed_fraction": 0.65}, detection="pipeline")`.
  The fraction and face are written explicitly, so a later change of default
  cannot move the fixture.
- **A5 (defensible default: `crop_to_grid`).** It is a public function in
  `src/segfacet/synth/corpus.py`, added to `__all__`:
  `crop_to_grid(img, grid_img) -> nib.Nifti1Image`.
  - It returns the affine-located sub-block of `img` at `grid_img`, built as
    a fresh image with a copy of the data, `img`'s dtype and `grid_img`'s
    affine.
  - It returns `img` itself when the two grids are identical, meaning equal
    shape and `np.allclose` affines. That keeps `base_scan.nii.gz`
    byte-identical and shared.
  - It raises `FacetInputError` when the rotation blocks differ, when the
    offset is not integral within 1e-6, or when the block leaves `img`'s grid.
- **A6 (defensible default: the corpus writer).** `build_corpus` sets each
  case's `scan_img = crop_to_grid(clean.scan_img, result.labelmap)`.
  `write_corpus` replaces its "every scan equals the base scan" assertion:
  - A case whose scan is array- and affine-equal to the first case's writes
    no scan and names `fixtures/base_scan.nii.gz`.
  - Any other case writes `fixtures/<case_id>_scan.nii.gz` and names that.

  The manifest schema is unchanged: every case already carries `scan_fixture`.
- **A7 (merged dependencies, read live on `aide/queue-023`, not forward
  pins).**
  - Item 173's `build_clean_spine()`: shape (61, 86, 193), RAS, L5 on slices
    15–48.
  - Item 174's 13-case geometric manifest, with `split_own_label` last.
  - Item 172's `operator_reason_conflicts()`, which stays `()`: no entry is
    added.
  - Items 170 and 171: their session fixtures and their live-derived negative
    controls apply to any test touched here.
- **A8: no human gate, and no environment-gated capability.**

## Implementation Steps

1. **`crop_to_grid`** in `src/segfacet/synth/corpus.py`, per A5. It reuses
   `nibabel`'s `slicer` and `segfacet.io.FacetInputError`.
2. **`CropFovPerturbation`** in `src/segfacet/synth/coverage_border_overlap.py`,
   per A2, registered with `@register_perturbation`.
   - It reuses `_present_labels`, `_choose_label`, `_require_present`,
     `_validate_face_name`, `resolve_face`, `FOV_TRUNCATION_CONDITION` and
     `FOV_TRUNCATION_CONDITION_NAME`.
   - Count the slices with `np.bincount` over the target's indices on the cut
     axis, with a cumulative sum taken from the face side.
   - Add the class to `__all__`, and add a bullet to the module docstring.
     The docstring says the legacy `crop_at_border` is an in-plane clip made
     by translation, kept for `border`. `CropAtBorderPerturbation` itself is
     unchanged.
3. **`src/segfacet/synth/corpus.py` recipe and writer**, per A4 and A6.
   "thirteen" becomes "fourteen" in the module docstring and the
   `CASE_RECIPE` comment, naming item 175's case. Update the
   `_BASE_SCAN_FIXTURE_NAME` comment ("operators preserve shape/affine") to
   say that a different-grid case carries its own scan.
4. **Regenerate the geometric corpus.** Run `python -m segfacet.synth.corpus`
   twice into two temp directories and diff the bytes before overwriting.
   Only `manifest.json` (one appended case) and the two new fixtures may
   differ from the committed tree. Any other difference is a hand-back.
5. **Re-capture `tests/corpus/094_pre_migration_snapshot.json`** by item
   174's method: a throwaway mirror of `test_094`'s reader, written with
   `write_bytes` and not committed. Keep the 16 existing keys with unchanged
   digests. Add `corpus/fixtures/crop_fov_si_seg.nii.gz|seg` and
   `corpus/fixtures/crop_fov_si_scan.nii.gz|scan`, for 18 in total.
6. **Specification (`src/segfacet/failure_modes.py`, `_CONDITION_FOV_TRUNCATION`).**
   Use `failure_modes.measured_firing` per case.
   - **Append a `crop_fov_si` case.** `CorpusCaseExpectation(case_id="crop_fov_si", corpus="geometric", expected_firing=("bounds",), reason=...)`.
     The reason records three things. The inferior face cuts L5 (the S-I FOV
     crop, the common form). `border` suppresses the expected end. `bounds`
     fires on the remnant's volume and `extent_z`, and that firing is what
     D3's border gating will remove.
   - **Legacy reason.** Append one sentence to `crop_at_border`'s `reason`:
     the anterior clip is the rare crop direction, and the case is kept for
     `border` coverage, not realism (maintainer, 2026-09-24).
     `tests/test_145_*` AC14's tokens ("crop"/"border", "centroid",
     "curve"/"spline") must survive.
   - **Mechanism.** Re-word it to name both fixtures: `crop_at_border` for the
     unexpected in-plane form and `crop_fov_si` for the expected cranio-caudal
     form. Keep the `is_terminal` token that `test_145` AC15 reads.
   - **Hands off.** `recording_rules`, `exempting_rules`,
     `candidate_features` and `definition` are not edited.
   - **Module docstring.** The docstring line that calls `crop_at_border`
     "the" fixture becomes plural.
7. **Regenerate the derived documents** with each module's `main`, twice into
   temp first:
   - `segfacet.failure_modes`;
   - `segfacet.traceability` (conformance, exercise and attribution gain the
     case; `bounds`' `exercised_by` gains it);
   - `segfacet.golden_evidence`.

   Also run `segfacet.catalogue`'s `main` into temp and confirm it is
   byte-identical to the committed catalogue (A2). If it is not, hand back.
8. **`docs/aide/golden-decision-table.md`.** Add two Section-1 rows, for
   `tests/corpus/fixtures/crop_fov_si_seg.nii.gz` and
   `tests/corpus/fixtures/crop_fov_si_scan.nii.gz`, worded like the
   `split_own_label_seg.nii.gz` row, with disposition `keep`. Add two matching
   `## Divergences from the roadmap's working assumption` bullets: "input
   fixture, not a report snapshot (added by item 175, 2026-09-24)". This is
   the item 166/174 precedent.
9. **Reconcile the existing tests** listed in the Testing Strategy, under the
   fence in Authorised paths. Record every edit in Decisions, by node id, with
   old → new.
10. **Run `python .aide/scripts/aide.py scope 175 --base aide/queue-023`** and
    confirm it exits 0.

## Authorised paths

**May change:**

- `src/segfacet/synth/coverage_border_overlap.py` — the new `CropFovPerturbation` (step 2).
- `src/segfacet/synth/corpus.py` — `crop_to_grid`, the recipe entry, the per-grid scan writer (steps 1, 3).
- `src/segfacet/failure_modes.py` — the new condition case, the legacy reason sentence, the mechanism (step 6).
- `tests/corpus/manifest.json` — regenerated with the appended case (step 4).
- `tests/corpus/fixtures/crop_fov_si_seg.nii.gz` — **new** fixture (step 4).
- `tests/corpus/fixtures/crop_fov_si_scan.nii.gz` — **new** fixture (step 4).
- `tests/corpus/094_pre_migration_snapshot.json` — two keys added (step 5).
- `docs/aide/failure_modes.generated.json` — the condition's new case and prose.
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — conformance, exercise and attribution gain the case.
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/golden_evidence.generated.json` — one row per corpus case.
- `docs/aide/golden-decision-table.md` — two Section-1 rows and two divergences bullets (step 8).
- `tests/test_175_crop_fov_si.py` — **new**: this item's test module.
- `tests/test_040_synthetic_corpus.py` — reconciliation (b): the scan-dedup contract.
- `tests/test_057_acceptance_stage7.py` — reconciliation (b) cohort pairing and (a) sensitivity.
- `tests/test_091_stage14_acceptance.py` — reconciliation (b): cohort pairing.
- `tests/test_102_stage18_validation.py` — reconciliation (b): each case's own scan.
- `tests/test_105_golden_decision_table.py` — reconciliation (a): fixture inventory count.
- `tests/test_116_ras_native_corpus.py` — reconciliation (b) cohort pairing and (a) post-item case set.
- `tests/test_120_leave_one_out_offset.py` — reconciliation (b) cohort pairing and (a) AC24 totals.
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — reconciliation (a): post-item case set.
- `tests/test_131_tangent_direction_normalisation.py` — reconciliation (a): post-item case set.
- `tests/test_132_monotonicity_against_traversal_order.py` — reconciliation (a): post-item case set.
- `tests/test_134_decision_table_evidence_companion.py` — reconciliation (a): fixture inventory.
- `tests/test_143_s_axis_correction.py` — reconciliation (a): post-item case set and snapshot count.
- `tests/test_145_eight_hypothesised_modes.py` — reconciliation (a): the conditioned-case list.
- `tests/test_149_conformance_report.py` — reconciliation (a): case counts.
- `tests/test_151_stage30_validation.py` — reconciliation (a): case counts.

**The reconciliation fence.** It applies to the listed `tests/test_*.py`
files other than this item's own module. **The builder** does the
reconciliation, after regeneration, because every new value comes from the
regenerated corpus. Two kinds of change are allowed:

- **(a) A moved literal.** A literal count, fraction or case/fixture set that
  this item's corpus change moved is updated to the fresh measurement. The
  assertion keeps its shape and its tolerance, and gains a dated item-175
  comment. Prose that quotes the literal follows it.
- **(b) A re-derived premise.** A constructed input or selection whose stated
  premise this item falsified is re-derived. The test keeps what it asserts.
  The instances are named in the Testing Strategy.

No test is retired, renamed, skipped, `xfail`-marked or loosened in
tolerance. A test whose name records an old value keeps its name (items
173/174 precedent). A red test in a file not listed here is a hand-back to
spec-author, not an edit.

**Asserts against:**

- `src/segfacet/heuristics/bounds.py` — AC9 reads the rule live; this item changes neither thresholds nor logic.
- `src/segfacet/heuristics/border.py` — AC9 and AC11 rest on its expected-end suppression and in-plane firing; unchanged.
- `src/segfacet/eval/severity_ladder.py` — still drives the legacy operator, which is why that operator stays used; unchanged.

Some paths stay off **May change** on purpose, so `aide scope` refuses them:

- `src/segfacet/traceability.py`: no `UNUSED_OPERATOR_REASONS` entry.
- `src/segfacet/heuristics/mislabel.py`: its evidence stays true.
- `docs/aide/feature_catalogue.generated.*`: predicted byte-identical (A2).
- The ratchet's test module: it must pick the case up unedited.
- `.gitattributes`: `tests/corpus/fixtures/*.nii.gz binary` and the existing
  `text eol=lf` pins already cover every regenerated path.
- The prototype directory.

## Testing Strategy

**The new module is `tests/test_175_crop_fov_si.py`**, with one test per AC
(AC1–AC11). The test-writer writes it.

- Committed fixtures are loaded with `nib.load` from the manifest's
  `seg_fixture`/`scan_fixture` under `CORPUS_DIR`.
- AC1, AC3, AC4 and AC8 compute the affine-located sub-block with plain
  NumPy from the two images' affines. They never call `crop_to_grid` or the
  operator's internals.
- AC5–AC7 use `extract_feature_record(loaded_seg_image(case), bundled_default_config())`.

The queue's other *Testable* claims are already enforced by tests that
iterate the live manifest, and pick up the new case with no edit:

- **The corpus regenerates byte-identically.**
  `tests/test_040_synthetic_corpus.py::test_ac16_regeneration_is_byte_identical_across_runs_and_vs_committed`
  globs every fixture, including the new scan. `test_116` AC10/AC11 and
  `test_143` AC11–AC13 also cover it.
- **The ratchet is green.**
  `tests/test_163_specificity_ratchet.py::test_ac2_ratchet_measured_equals_expected[geometric-crop_fov_si]`
  appears by parametrisation.
- **The machine-readable record holds.** `tests/test_041_*` runs
  `verify_case` per manifest case, and `test_040` AC17 rebuilds each case's
  `Expectation` from its recipe.

Adversarial cases, each written once:

- **`crop-resolves-face-from-affine`**: apply
  `CropFovPerturbation(target_label=24, face="inferior", removed_fraction=0.65)`
  to `build_clean_spine().seg_img.as_reoriented(np.array([[0, 1], [1, 1], [2, -1]]))`.
  That image's axcodes are RAI, so the inferior face is the **high** end of
  axis 2 and L5 lies on slices 144–177 (measured). The output equals the
  input's affine-located sub-block at it, and the last slice on axis 2
  contains label 24. This guards a hard-coded low-end cut (`[:, :, cut:]`, as
  in the prototype), which passes AC1–AC3 on the RAS base and fails here.
- **`crop-output-not-a-view`**: after `apply`, write into the output array.
  The input array is `np.array_equal` to a copy taken before `apply`. This
  guards returning `slicer`'s view, which would let a later edit of a case
  corrupt the base that `build_corpus` hands the next recipe entry.
- **`crop-degenerate-fraction-refused`**: parametrised over
  `removed_fraction` 0.0 and 1.0, each raising `FacetInputError`. This guards
  an identity "crop" at 0.0 (the at-least rule would round up to one slice)
  and a cut that deletes the target at 1.0.
- **`crop-whole-target-refused`**: `removed_fraction=0.99` on the default
  base with target 24 raises `FacetInputError`. The test first asserts, from
  the input array, that reaching 99 % needs every slice of label 24. This
  guards a returned map that silently lacks its target label.
- **`crop-absent-target-refused`**: `target_label=999` raises
  `FacetInputError`. This guards a silent fallback to the seeded choice.
- **`grid-helper-refuses-non-subgrid`**: `crop_to_grid(default base, grid)`,
  where `grid`'s affine is the base's plus a 0.5-voxel translation, raises
  `FacetInputError`. This guards rounding a non-integral offset to a wrong
  slab, which would pair a case with a shifted ground truth (GT) in every
  re-derived cohort builder.

**Existing tests to reconcile.** This is the stale-assumption sweep. Three
read-only agents checked every test file naming `crop_at_border`, plus the
corpus-wide count and set pins, on 2026-09-24. Under this item's shape a new
case is added and the legacy case is unchanged, so what still moves is listed
below. Each file is under **May change**, and **the builder** edits it.

**Red without the edit, (b) re-derived premises:**

1. **Cohort pairing.** A builder that pairs every case with the full-grid
   `clean_control` raises on `crop_fov_si` in `compute_overlap`. The premise
   "every case shares `clean_control`'s grid" is falsified. Each builder
   pairs a case with `crop_to_grid(clean_control_img, candidate_img)`. That is
   the clean control itself for every base-grid case, and the `crop_fov_si`
   seg for the new one: a condition case's GT is the clean spine seen through
   the same FOV. The builders are:
   - `tests/test_057_acceptance_stage7.py::_build_corpus_cohort`;
   - `tests/test_091_stage14_acceptance.py::_build_corpus_cohort`;
   - `tests/test_116_ras_native_corpus.py::_build_corpus_cohort`;
   - `tests/test_120_leave_one_out_offset.py::_corpus_cohort_metrics`.

   Measured with that pairing on 2026-09-24:
   - false positive rate (FPR) 0.0;
   - sensitivity 11/12;
   - per-mode `{0: (2, 1.0), 1: (2, 1.0), 2: (1, 1.0), 3: (2, 1.0), 4: (1, 1.0), 6: (1, 1.0), 9: (2, 1.0), 15: (1, 0.0)}`,
     read as `mode: (n_cases, sensitivity)`;
   - the new case is a TRUE_POSITIVE.

   `tests/test_132_*` AC21/AC22 call `test_057`'s functions and follow with no
   edit.
2. **`tests/test_102_stage18_validation.py::block_b`** runs `segfacet run`
   for every manifest case with the hard-coded `_BASE_SCAN`. The premise "one
   shared scan" is falsified. Pass each case's own manifest `scan_fixture`,
   resolved under `CORPUS_DIR`. `block_a` (inject_islands) stays as it is.
3. **`tests/test_040_synthetic_corpus.py::test_adv_all_cases_share_exactly_one_scan_fixture`**
   asserts `len({scan_fixture}) == 1`. Re-derive it; it keeps its guard
   against a duplicated scan:
   - every case whose seg fixture's shape and affine equal `clean_control`'s
     names `fixtures/base_scan.nii.gz`;
   - every other case names a scan fixture whose shape and affine equal its
     own seg's.

   The name is kept, and its docstring records why.

**Red without the edit, (a) moved literals:**

4. **Post-item case sets.** Each file pins, as an exact set, the cases its
   pre-item table does not cover. Add `"crop_fov_si"` to each, and do not
   extend the tables:
   - `tests/test_116_ras_native_corpus.py::_ITEM_150_NEW_CASES`;
   - `tests/test_129_*::_ADDED_AFTER_129`;
   - `tests/test_131_*::_ADDED_AFTER_ITEM`;
   - `tests/test_132_*::_ADDED_AFTER_ITEM`;
   - `tests/test_143_*::_ADDED_AFTER_ITEM`.
5. **`tests/test_143_s_axis_correction.py::test_ac19_snapshot_covers_all_15_entries_across_both_corpora`:**
   `len(snapshot) == 16` → 18, after step 5.
6. **`tests/test_149_conformance_report.py`:** `len(cases) == 17` → 18, and
   the geometric count `== 13` → 14.
7. **`tests/test_151_stage30_validation.py`:** `len(keys) == 17` and
   `agree_count == 17` → 18.
8. **`tests/test_057_acceptance_stage7.py::test_overall_corpus_sensitivity_is_nine_of_ten_not_over_claimed`:**
   `10/11` → `11/12`, with a docstring history line. The name is kept.
9. **`tests/test_120_leave_one_out_offset.py::test_ac24_corpus_pipeline_detection_is_nine_of_ten`:**
   - sensitivity `10/11` → `11/12`;
   - `sum(n_cases) == 11` → 12.

   The per-mode dict is unchanged: mode 0 stays at 1.0, now over two cases.
10. **`tests/test_105_golden_decision_table.py`:** both `== 24` → 26
    (`test_ac3_current_tree_has_30_non_py_fixtures` and the empty-table
    adversarial). The Section-1 and divergences checks are satisfied by step
    8. `test_126` AC20 reads this constant and follows.
11. **`tests/test_134_decision_table_evidence_companion.py::_INVENTORY_ADDED_AFTER_126`:**
    add both new fixture paths, with a comment naming item 175.
12. **`tests/test_145_eight_hypothesised_modes.py::test_ac14_condition_case_is_carried_by_the_manifest_as_a_condition`:**
    `conditioned == ["crop_at_border"]` → `["crop_at_border", "crop_fov_si"]`,
    in manifest order. Its "every other case names no condition" comment is
    re-worded to "only the two FOV crops name a condition".

**Checked and unaffected** (sweep, 2026-09-24):

- `test_038`, `test_049`, `test_090`, `test_098`, `test_100`, `test_101_*`,
  `test_110`, `test_123`, `test_125`, `test_128_*`, `test_148`, `test_153`,
  `test_154` and `test_157`: they read the unchanged legacy case or operator.
- `test_099`: its records are seg-only. The isolation matrix reads
  `_LEGACY_CASE_IDS`. The new case reads `fov_clipped_label_count` 0.0, which
  AC12's agreement-with-`BorderRule` parametrisation expects.
- `test_121`: every principal axis is L-R within 1e-12 (A3).
- `test_126`: no float collision (A3).
- `test_136`, `test_137`, `test_103` and `test_156`: the `Expectation` uses the
  `CLEAN_CONTROL_MODE` name (A2).
- `test_162`, `test_172` and `test_174`: their values are derived live.
  `border` stays exercised, and no `UNUSED_OPERATOR_REASONS` entry is added.
- `test_094`: the snapshot is re-captured by step 5.

One stale docstring is not edited, because it pins no literal:
`test_099::test_ac12_mode6_zero_on_expected_fov_end_touch_real_data_case`
says the synthetic corpus has no expected FOV-end touch.

**Sibling note.** Items 176 and 177 regenerate the same manifest, the 094
snapshot and the generated documents. Whichever lands later re-measures the
shared count literals (entries 5–10) on top of the earlier one. None of them
asserts against a path listed here.

## Validation

1. Run `python -m segfacet.synth.corpus --out <tmp>` and diff `<tmp>` against
   `tests/corpus/`. Confirm there is no difference.
2. Run
   `.venv/bin/segfacet run --scan tests/corpus/fixtures/crop_fov_si_scan.nii.gz --seg tests/corpus/fixtures/crop_fov_si_seg.nii.gz --no-reference --out <tmp>`.
   `--no-reference` is required (CLAUDE.md gotcha). Expect
   `flagged-for-review` with exactly two `bounds` findings on label 24 and no
   `border` finding. Then run the same `--seg` with
   `--scan tests/corpus/fixtures/base_scan.nii.gz`. Expect exit 1 with a
   shape-mismatch message, which shows why the case needs its own scan.
3. Run `python .aide/scripts/aide.py scope 175 --base aide/queue-023` and
   confirm it exits 0.
4. Run `.venv/bin/python -m pytest --collect-only -q` on this branch and on
   `aide/queue-023`. The branch's collected test-id set must equal the base's
   set plus this item's new tests plus the parametrised ids whose parameter
   is the new case or its fixtures. Nothing is removed or renamed.

No `[validation]` profile is needed, so there is no ❓ Unverified downgrade
path.

## Dependencies

- Item 172 (merged into `aide/queue-023`): `operator_reason_conflicts()`.
  Item 172's spec asks item 175 to name it, because item 175 could have added
  the first `UNUSED_OPERATOR_REASONS` entry. Under this shape it adds none.
- Item 173 (merged): the lordotic base the crop cuts.
- Item 174 (merged): the 13-case manifest and count literals this item moves
  again.

**Downstream:**

- The next queue's border-gating item (roadmap Stage 33 D3) measures its
  suppression of `bounds`/`reference_delta` on `crop_fov_si`. It must
  re-author `crop_fov_si`'s `expected_firing` and list
  `tests/test_175_crop_fov_si.py` under May change, because AC9's set will
  move.
- Item 178 renders the new case, on its smaller grid.
- D4 re-measures the severity ladder, which still uses the legacy operator.

## Decisions & Trade-offs

To be updated during implementation.

- **D1: the maintainer keeps a `border` case (2026-09-24).** A committed case
  must keep firing `border`, so the legacy in-grid `crop_at_border` operator
  and case stay. `test_099`'s `fov_clipped_label_count` checks are re-derived,
  not the metric. With the legacy case unchanged, they need no edit: the
  metric's own case is still `crop_at_border`, where it reads 1.0.
- **D2: which case is which, and why.** The maintainer said on 2026-09-24:
  "Makes sense to differentiate crops — the most common FOV crop is in the SI
  direction, MRI often has an LR crop, an AP crop is rare."
  - The legacy case keeps id `crop_at_border` with its anterior clip of label
    22. It is recorded as the rare direction, kept for `border` coverage and
    not as a realistic crop.
  - The true volume crop is the new case `crop_fov_si`, the common S-I form.
  - Re-authoring the legacy id in place was rejected. The three sweeps counted
    about 60 test pins on `crop_at_border`'s content: its firing, labels, grid,
    per-mode value, and operator-keyed ladder home in `test_153`. A new id
    pins nothing and moves only the count literals listed above.
  - Re-facing the legacy case to LR was rejected for the same reason.
  - Both cases are `fov_truncation` fixtures. The condition's `definition`
    already names the expected cranio-caudal form and the unexpected in-plane
    form, so each case expresses what it is attributed to.
- **D3: the queue title reads differently under this shape.** "Replace the
  operator" became "add the operator": the maintainer's D1 keeps the old one
  used. So the queue's "if the old operator falls out of use" branch does not
  arise, and item 172's check stays empty.
- **Left open:** an LR crop case, the form common in MRI, as follow-up corpus
  work. `crop_fov`'s `face` is resolved generically from the affine (A2), so
  an LR crop is one recipe entry. It is not added here: neither D3's gating
  nor D5's sign-off needs it yet.
- **Left open:** whether the legacy in-plane `crop_at_border` should later be
  re-authored as a true in-plane volume crop, so the condition's unexpected
  form is also expressed as a real FOV cut and not a translation. That would
  move its ladder and about 60 test pins, so it belongs with D4's ladder
  re-measurement or a later corpus item.
- **Left open:** `bounds` fires on `crop_fov_si` for `extent_z` as well as
  volume (A3). Which of the two D3's gating must suppress is D3's question.
