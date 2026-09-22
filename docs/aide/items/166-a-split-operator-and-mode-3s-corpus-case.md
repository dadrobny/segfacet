<!-- aide-template: item 2 -->
# Item 166 — A split operator and mode 3's corpus case

> **Created:** 2026-09-20 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 32 — Selected-Mode Refinement: one failure mode fully specified end to end
> **Queue:** [`../queue/queue-022.md`](../queue/queue-022.md) · Item 166
> **Objectives:** G2, G7, G8
> **Suggested branch:** `aide/166-a-split-operator-and-mode`

---

## Description

Mode 3 (*split vertebra segment*) is one of the two modes the maintainer selected
for this queue (queue-022, 2026-09-18; roadmap Stage 32 **D2**). Today it derives
`implemented` and its specification entry carries **no corpus case at all** —
`SPECIFICATION[3].corpus_cases == ()` — so the only thing standing behind it is
the pair of generic volume proxies (`bounds`, `reference_delta`) at
`needs-real-data`, neither of which fires without a reference. Its `mechanism`
field says so in as many words: *"A split fixture (part of one label reassigned
to its neighbour) is not yet authored."*

This item authors that fixture. It adds **one perturbation operator** (`split`)
and **one committed geometric corpus case** generated from it, with the case's
`expected_firing` authored in `src/segfacet/failure_modes.py` from the measured
firing — because item 163's specificity ratchet asserts
`set(measured_firing) == set(expected_firing)` for every committed corpus case
and derives its case list live, so a new case with no authored expected set
turns the suite red. Satisfying the ratchet **is** the deliverable.

**What a "split" is, concretely.** Mode 3's definition: *a substantial part of
one ground-truth vertebra is covered by the label of a neighbouring vertebra*.
As a perturbation of a label map that is: take a contiguous end-slab of the
target label's voxels — the end facing its adjacent neighbour along the
stacking axis — and **relabel them to the neighbour's id**. Nothing is deleted,
nothing is created: the foreground mask is unchanged and exactly one label's
voxels change hands.

**Why no existing operator expresses it** (measured against the registry on this
tree, 2026-09-20 — eleven operators: `identity`, `displace`, `fragment`, `fuse`,
`inject_islands`, `relabel_swap`, `remove_level`, `remove_level_relabel`,
`crop_at_border`, `force_overlap`, `sequence_break`):

- `fragment` carves interior slabs out of one label so it breaks into pieces of
  **its own** label — the voxels stay with the target (mode 1). A split gives
  them to a *different* label.
- `fuse` is mode 3's **converse**: it relabels the whole neighbour onto the
  target. It is whole-label, in the opposite direction.
- `relabel_swap` exchanges two labels **entirely** (mode 9); `displace` moves a
  whole label; `remove_level_relabel` renumbers whole labels. All are
  whole-label operations.
- `crop_at_border` and `remove_level` delete voxels to background — mode 3's
  discriminator explicitly separates that case ("mode 1 when the missing part is
  left as background rather than claimed by another label").

So no registered operator moves *part* of one label onto its neighbour, which is
precisely mode 3's definition.

**What the new case is expected to fire, and why** — measured on this tree
(2026-09-20, `.venv/bin/python`, `run_qc` with `bundled_default_config()`, no
reference), donating 40 % of label 22 (L3) to label 23 (L4) on the default clean
spine:

> **`("fragmentation",)`** — one finding, on label **23**:
> `Fragmentation: Label 23: fragmentation_index=0.714286 is strictly below
> threshold 0.75. component_count=2, component_sizes=[18750, 7500]`;
> verdict `flagged-for-review`.

The receiving label 23 now spans two disconnected bodies (its own, plus the
donated slab across the intervertebral gap), so `fragmentation`'s
`Fragmentation:` detector — detector id **`components`**, which
`SPECIFICATION[1]` claims for mode 1 — fires on it. That is a **recorded
co-detection by another mode's detector**, exactly the shape mode 2's
`fuse_adjacent` case already has, and the queue explicitly permits it: *"Whatever
fires today is recorded as found."* Mode 3's own `intended_rules` are **not
touched**: no new `IntendedRule` edge and no new `detector_ids` are authored
here, so item 164's two conformance directions are unaffected. Mode 3's own
feature and detector are **item 167's**.

**Where that leaves mode 3 against the roadmap's bar.** Measured today,
`traceability.bar_conditions(3)` returns `(False, False, False, False, False)`;
condition 1's `subjects` lists seven of the eight completeness fields, with
`corpus_cases` the one empty field. After this item condition 1 is **met** and
conditions 2–5 remain **unmet** — mode 3 has no non-proxy detector
(`bar_conditions`' condition 4 excludes `bounds`/`reference_delta` by
construction, and condition 3 quantifies over condition 4's qualifying
detectors), and `derive_status` stays `implemented` because the case's expected
firing names none of mode 3's own intended rules. **Mode 3 is not at the bar
after this item, and is not meant to be.** That recorded intermediate state is
what the queue and roadmap Stage 32 D2 permit.

**Not in scope.** No new feature, no new rule, no new detector, no threshold
change, no new `IntendedRule` edge, no sign-off (item 168's), no stage
attestation (item 169's, from a clean clone), and nothing touching the intensity
corpus.

## Acceptance Criteria

- [ ] **AC1: the operator is registered under `split`.**
      `segfacet.synth.perturbation.perturbation_names()` contains `"split"`, and
      `get_perturbation("split")` returns a `Perturbation` subclass whose `name`
      class attribute equals `"split"`.

- [ ] **AC2: a split reassigns target voxels to the neighbour and changes
      nothing else.** Applying the operator to the default clean spine
      (`build_clean_spine(**_DEFAULT_BASE_PARAMS)`) with `target_label=22`,
      `neighbour_label=23`, the set of voxel indices where the output label
      differs from the input is **exactly** the set where input `== 22` and
      output `== 23`, and that set is non-empty. Recomputed from the two arrays,
      not from the operator's own report.

- [ ] **AC3: the donated voxels are a contiguous end-slab on the neighbour's
      side of the affine-resolved stacking axis.** The stacking-axis indices of
      the donated voxels form a contiguous run, and that run lies on the side of
      the target's extent nearer the neighbour's mean position along
      `segfacet.synth.axes.si_axis(labelmap.affine)` — both sides recomputed from
      the input array and affine, so the claim holds under either axis
      orientation rather than a hardcoded index.

- [ ] **AC4: the operator is deterministic under its seed.** Two `apply` calls
      with the same input image and the same seed return label-map arrays that
      are `numpy.array_equal`.

- [ ] **AC5: a label map with no adjacent neighbour is refused.** Applying the
      operator to a label map carrying fewer than two present non-zero labels
      raises `segfacet.io.FacetInputError`.

- [ ] **AC6: the operator's record attributes the case to mode 3.** The
      `Expectation` returned by `apply` carries `failure_mode == 3` and
      `failure_mode_name == segfacet.synth.perturbation.FAILURE_MODE_NAMES[3]`
      (`"split vertebra segment"`), compared against that mapping rather than a
      transcribed string.

- [ ] **AC7: the committed geometric corpus carries the case.**
      `tests/corpus/manifest.json` carries exactly one case whose
      `perturbation == "split"`; that case's `failure_mode` is `3`, its
      `detection` is `"pipeline"`, and the fixture file its `seg` path names
      exists on disk under `tests/corpus/fixtures/`.

- [ ] **AC8: the authored expected firing equals the measured firing, and is
      `{"fragmentation"}`.** For mode 3's `split` corpus case in
      `SPECIFICATION[3].corpus_cases`,
      `set(segfacet.failure_modes.measured_firing(case)) == set(case.expected_firing) == {"fragmentation"}`,
      every term recomputed live (the measurement through
      `segfacet.synth.regression.pipeline_findings`, as
      `failure_modes.measured_firing` drives it).

- [ ] **AC9: mode 3's recorded state against the fully-specified bar.**
      `tuple(c.met for c in segfacet.traceability.bar_conditions(3))` equals
      `(True, False, False, False, False)`, and condition 1's `subjects` contains
      all eight completeness fields including `"corpus_cases"` — mode 3's entry
      is now complete, and conditions 2–5 are not met. Closes no stage
      criterion: Stage 32's acceptance is attested by **item 169**, from a clean
      clone with its own venv (item 163's tick from the working checkout was
      retracted on 2026-09-20).

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

`loop.clarify = "assume"`. Each defensible default taken while specifying the
queued one-liner is recorded here for audit at the queue boundary. The four
measurement assumptions below were taken **by measuring on this tree**, not by
reasoning; each names what was run.

- **A1 (measured 2026-09-20):** the split fraction is **0.4** of the target's
  stacking-axis extent (10 of label 22's 25 slices). Measured with `run_qc` on
  the default clean spine: **0.3** fires *nothing at all*
  (`fragmentation_index = 0.757 > 0.75`, verdict `pass`) — an invisible fixture;
  **0.4** fires `fragmentation` on label 23 alone; **0.5** additionally fires
  `bounds` on label 22 (`extent_z = 13 mm` below the lumbar minimum `15 mm`).
  0.5 is rejected deliberately: `bounds` **is** one of mode 3's own intended
  rules, so a 0.5 case would flip condition 2 and `derive_status` to
  `validated` — validating mode 3 through a generic volume proxy that the
  roadmap's condition 4 explicitly excludes, and moving `bounds` off
  `needs-real-data` in item 162's exercise report on the strength of a fixture
  built to trip a size range. 0.4 is the only measured fraction of the three
  that expresses the split and nothing else.

- **A2 (measured 2026-09-20):** the case is built on the **same `target=22`,
  `neighbour=23` pair as `fuse_adjacent`**, which is mode 3's converse. Mode 2's
  case absorbs 23 into 22; mode 3's case donates part of 22 to 23. The pair is
  reused so the two converse modes are expressed on the same anatomy.

- **A3 (measured 2026-09-20):** the operator and the case are both named
  `split` — the roadmap menu's word ("*Mode 3 split:* a split operator"), and
  consistent with item 157's convention that a case id names its operator.

- **A4 (measured 2026-09-20):** the manifest case's `expected_labels` is
  **`{23}` (the neighbour alone)**, not `{22, 23}`.
  `segfacet.synth.regression.offending_labels_match` asserts the union of fired
  findings' labels **equals** `set(case["expected_labels"])`, and
  `tests/test_041_regression_suite.py::test_ac6_offending_labels_match_manifest_for_pipeline_cases`
  runs it over every pipeline case. The one measured finding is on label 23. The
  intuitive `{target, neighbour}` fails that equality.

- **A5:** no `.gitattributes` edit is needed. The existing globs
  `tests/corpus/fixtures/*.nii.gz binary` and
  `tests/corpus/manifest.json text eol=lf` already cover the new fixture and the
  regenerated manifest, so CLAUDE.md's LF-pin gotcha is discharged by the pins
  that are already there rather than by a new line. Byte-reproducibility comes
  from the existing generator path: `synth.corpus.write_corpus` →
  `_save_deterministic` (nibabel's `mtime=0` gzip wrapper) for the `.nii.gz`
  blob, and the same `write_corpus` call for `manifest.json`, both already
  asserted byte-identical against the committed copies by
  `tests/test_040_synthetic_corpus.py::test_ac16_regeneration_is_byte_identical_across_runs_and_vs_committed`,
  which iterates every manifest case and so picks the new one up unedited.

- **A6:** mode 3's `intended_rules` are left exactly as authored
  (`bounds` + `reference_delta`, both `needs-real-data`). The `fragmentation`
  firing is recorded as a co-detection in the case's `expected_firing` and
  `reason`, in the shape `SPECIFICATION[2].corpus_cases[0]` already uses. This is
  what keeps `catalogue.rule_declaration_conflicts`' corpus → declaration
  direction silent: its co-detection exemption applies precisely to a rule that
  fires on a mode's case **without** being one of that mode's intended rules.

- **A7 (engine 1.59.2):** `aide scope` proves this item's diff against the
  **Authorised paths** list below; a path listed there and left unchanged is not
  a scope violation, so the conditional reconciliations named below
  (`tests/test_123_recalibrate_and_regenerate.py` in particular) are declared
  whether or not the suite run turns out to need them.

## Implementation Steps

1. **Add `SplitPerturbation` to `src/segfacet/synth/component_shape.py`**, sited
   directly after `FusePerturbation` (its converse) so the two read together.
   Reuse the module's existing helpers rather than re-implementing any of them:
   `_present_labels`, `_require_present`, `_choose_adjacent_pair`,
   `_label_bbox`, `_new_image`, and `segfacet.synth.axes.si_axis` for the
   stacking axis (item 116 — never a hardcoded axis index). Register it with the
   existing `@register_perturbation` decorator under `name = "split"`. **No new
   dependency**, and no new module.

2. **Signature and guards**, mirroring `FusePerturbation`'s shape:
   `__init__(self, *, target_label=None, neighbour_label=None, donated_fraction=0.4)`.
   In `apply`: raise `FacetInputError` when fewer than two labels are present
   (AC5); when either of `target_label`/`neighbour_label` is given, require both,
   require both present (`_require_present`), and require them adjacent in the
   sorted present-label order (the same `abs(idx_t - idx_n) != 1` check `fuse`
   uses); otherwise fall back to `_choose_adjacent_pair(labels, seed)`. Raise
   `FacetInputError` when the computed slab would be empty or would leave the
   target no voxels.

3. **The split itself.** Copy the array (never mutate the caller's image).
   Resolve `axis = si_axis(labelmap.affine)`. Take the target's bbox along that
   axis via `_label_bbox`; compute `k = round(donated_fraction * span)`. Decide
   the donated end by comparing the two labels' **measured** mean index along
   `axis` — the neighbour-facing end — and set `data[slab][target_mask] = neighbour`.
   Build the output with `_new_image`.

4. **Author the `Expectation`** with the literal keyword form the AST scan in
   `catalogue._scan_synth_rule_mode_map` reads:
   `failure_mode=3`, `failure_mode_name=FAILURE_MODE_NAMES[3]`,
   `expected_rule_ids=frozenset({"fragmentation"})` (a literal `frozenset({...})`,
   not a variable), `expected_labels=frozenset({neighbour})` (A4),
   `expected_verdict="flagged-for-review"`, and a `detail` naming the donated
   fraction, the slab indices, and that the firing is mode 1's `Fragmentation:`
   detector co-detecting on the receiving label rather than mode 3's own signal.

5. **Add the recipe entry** to `CASE_RECIPE` in
   `src/segfacet/synth/corpus.py`, after `remove_level_relabel`:
   `_RecipeEntry(case_id="split", perturbation="split",
   perturbation_params={"target_label": 22, "neighbour_label": 23},
   detection="pipeline")`. Update the module docstring and the `CASE_RECIPE`
   comment, which both say "eleven canonical cases", to twelve with a dated
   item-166 note.

6. **Regenerate the committed corpus** with the existing one-command entry point
   (`src/segfacet/synth/corpus.py`'s `main`, the same path
   `test_040::test_ac18_the_one_command_regeneration_entry_point_runs`
   exercises), writing `tests/corpus/fixtures/split_seg.nii.gz` and the updated
   `tests/corpus/manifest.json`. Do not hand-edit either.

7. **Measure, then author, mode 3's corpus case.** Run
   `segfacet.failure_modes.measured_firing` (or
   `synth.regression.pipeline_findings` on the new manifest case) and author
   `CorpusCaseExpectation(case_id="split", corpus="geometric",
   expected_firing=<the measured tuple>, reason=...)` into
   `SPECIFICATION[3].corpus_cases` in `src/segfacet/failure_modes.py`. **The
   measurement is the authority** — AC8 predicts `("fragmentation",)` from a
   2026-09-20 measurement; if the build measures something else, that is a
   contradiction between the spec and reality and comes back to `spec-author`
   as a dated correction rather than being reconciled by editing the ratchet.
   The `reason` must state, in the shape mode 2's `fuse_adjacent` reason uses:
   the measurement date and the function it was measured through; that the
   firing is `fragmentation`'s `Fragmentation:` detector (detector id
   `components`, mode 1's) co-detecting on the *receiving* label; and that
   neither of mode 3's own intended rules fires without a reference, so the case
   does not validate mode 3.

8. **Update `SPECIFICATION[3].mechanism`**, whose current text asserts "*No
   corpus case and no detector of its own*" and "*A split fixture … is not yet
   authored*" — both false after step 7. Correct to: the fixture is authored,
   what it fires and via whose detector, and that mode 3 still has no detector of
   its own (item 167's).

9. **Regenerate every derived artifact** with its own entry point, none of them
   hand-edited: `docs/aide/failure_modes.generated.{json,md}` (mode 3 gains a
   corpus case), `docs/aide/traceability_matrix.generated.{json,md}` (the
   conformance report gains a case; the exercise report gains the operator),
   `docs/aide/feature_catalogue.generated.{json,md}` (mechanism C's
   `_scan_synth_rule_mode_map` now maps `fragmentation → (1, 2, 3, 4)`, which
   moves per-path mode attribution), and
   `docs/aide/golden_evidence.generated.json` (one row per corpus case).

10. **Reconcile the existing tests named under "existing tests to reconcile"
    below**, then **run the full suite** and reconcile whatever else it names —
    item 164's `## Correction 2` records why a grep is not enough here: this
    change's surfaces are the manifest's case set, the manifest's mode set, the
    corpus-derived rule → mode map, the `tests/` fixture inventory, and every
    historical "cases added after item N" exclusion set. A file the suite names
    that is not declared under **Authorised paths** is a dated correction to this
    spec, not a silent edit.

## Authorised paths

**May change:**

- `src/segfacet/synth/component_shape.py` — the new `SplitPerturbation` (steps 1–4)
- `src/segfacet/synth/corpus.py` — the `CASE_RECIPE` entry and the "eleven cases" docstrings (step 5)
- `src/segfacet/failure_modes.py` — mode 3's corpus case and corrected `mechanism` (steps 7–8)
- `tests/corpus/manifest.json` — regenerated by `write_corpus` (step 6)
- `tests/corpus/fixtures/split_seg.nii.gz` — the new committed fixture (step 6)
- `docs/aide/failure_modes.generated.json` — regenerated; mode 3 gains a corpus case
- `docs/aide/failure_modes.generated.md` — regenerated; same
- `docs/aide/traceability_matrix.generated.json` — regenerated; conformance gains a case, exercise gains the operator
- `docs/aide/traceability_matrix.generated.md` — regenerated; same
- `docs/aide/feature_catalogue.generated.json` — regenerated; mechanism C's rule → mode map moves
- `docs/aide/feature_catalogue.generated.md` — regenerated; same
- `docs/aide/golden_evidence.generated.json` — regenerated; one row per corpus case
- `docs/aide/golden-decision-table.md` — a Section-1 row for the new fixture; `test_105`'s on-disk ⊆ documented direction fails without it
- `tests/test_166_split_operator.py` — this item's own test module
- `tests/test_040_synthetic_corpus.py` — `_PIPELINE_ONLY_MODES` gains `3`
- `tests/test_041_regression_suite.py` — only if the suite names it; its per-case checks are derived
- `tests/test_057_acceptance_stage7.py` — `test_overall_corpus_sensitivity_is_eight_of_nine_not_over_claimed` re-measures (8/9 → 9/10) and is renamed to its new ratio; `_PIPELINE_DETECTABLE_MODES` gains `3`
- `tests/test_103_feature_catalogue.py` — `_RULE_MODE_MAP["fragmentation"]` becomes `(1, 2, 3, 4)`
- `tests/test_105_golden_decision_table.py` — `test_ac3_current_tree_has_30_non_py_fixtures` count `22` → `23`
- `tests/test_116_ras_native_corpus.py` — `_ITEM_150_NEW_CASES` (the post-item exclusion) gains `"split"`
- `tests/test_121_tangent_orientation.py` — `_FUSED_BODY_SPAN_EXCLUSIONS` gains `("split", 23)` and the named-exceptions set gains `"split"`
- `tests/test_123_recalibrate_and_regenerate.py` — only if the interior-offset ceiling moves; measured 2026-09-20, the split's interior offsets peak at 0.678 mm, below the pinned 2.510990, so no edit is expected
- `tests/test_125_stage28_validation.py` — `modes == {1, 2, 4, 6, 9}` and `len(modes) == 5` become `{1, 2, 3, 4, 6, 9}` / `6`
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — `_ADDED_AFTER_129` gains `"split"`
- `tests/test_131_tangent_direction_normalisation.py` — `_ADDED_AFTER_ITEM` gains `"split"`
- `tests/test_132_monotonicity_against_traversal_order.py` — `_ADDED_AFTER_ITEM` gains `"split"`, and the `t040._PIPELINE_ONLY_MODES == {0, 1, 2, 4, 6, 9}` cross-check gains `3`
- `tests/test_134_decision_table_evidence_companion.py` — `_INVENTORY_ADDED_AFTER_126` gains `tests/corpus/fixtures/split_seg.nii.gz`
- `tests/test_135_stage29_validation.py` — same two assertions as `test_125`
- `tests/test_136_rule_mode_declarations.py` — `expected_co_detections` gains `("fragmentation", 3)`
- `tests/test_143_s_axis_correction.py` — `_ADDED_AFTER_ITEM` gains `"split"`
- `tests/test_145_eight_hypothesised_modes.py` — `_GEOMETRIC_CORPUS_MODE_IDS` gains `3` and its comment stops saying mode 3 carries no case
- `tests/test_149_conformance_report.py` — case counts `15` → `16` and `11` → `12`
- `tests/test_151_stage30_validation.py` — both `== 15` case-count assertions become `16`
- `tests/test_120_leave_one_out_offset.py` — reconciliation (added 2026-09-20, Correction): its AC24 block is a **second, independently-authored pin of the same corpus-wide detection totals `test_057` pins** — its own `_corpus_cohort_metrics()` helper over the whole manifest, then `metrics.sensitivity == 8/9`, a hardcoded `expected_sensitivity` per-mode dict, `sum(m.n_cases …) == 9`, and the ratio in the test's own name

- `tests/report_format_fixture.py` — reconciliation (added 2026-09-20, Correction 2 §1): its plain round float literals collide with a float the new corpus case emits, failing `test_126`'s fixture/corpus disjointness guard
- `tests/golden/report_format_contract.json` — reconciliation (added 2026-09-20, Correction 2 §1): the committed contract regenerated from the fixture above, only via `.venv/bin/python -m tests.report_format_fixture`

**Asserts against:**

- `src/segfacet/heuristics/fragmentation.py` — AC8's measured firing is this rule's `Fragmentation:` detector (`components`); the rule and its threshold are read, never changed
- `src/segfacet/heuristics/bounds.py` — the `bounds-stays-silent-on-the-donor` case recomputes the lumbar volume/extent range from `DEFAULT_BOUNDS` rather than pinning A1's numbers
- `src/segfacet/traceability.py` — AC9 recomputes `bar_conditions(3)` live; this item adds no reader and changes no scorer
- `.gitattributes` — A5: the existing `tests/corpus/**` globs must already cover the new fixture and the regenerated manifest

## Testing Strategy

**Test module:** `tests/test_166_split_operator.py`.

One test per acceptance criterion (AC1–AC9), written without being asked. Every
test of the committed corpus reads it through
`segfacet.synth.corpus.load_manifest` / `segfacet.failure_modes.measured_firing`
/ `segfacet.traceability.bar_conditions`, never a hand-built copy of the case.

Beyond those, exactly these cases:

- `non-mutating-apply`: `apply` leaves the caller's image array unchanged — a mutating operator corrupts the shared clean base that `build_corpus` reuses for every later `CASE_RECIPE` entry, silently changing other cases' committed fixtures.
- `explicit-non-adjacent-pair-refused`: `target_label=22, neighbour_label=24` raises `FacetInputError` — without the adjacency guard a "split" onto a non-adjacent level produces a mode-14-shaped fixture filed under mode 3.
- `absent-label-refused`: an explicit `target_label` not present in the map raises `FacetInputError` — silently falling back to `_choose_adjacent_pair` would make the committed fixture depend on the seed instead of the recipe.
- `degenerate-fraction-refused`: a `donated_fraction` that would donate no slices, or leave the target none, raises `FacetInputError` — a zero-donation split is an identity fixture that passes every structural check while expressing nothing.
- `target-stays-one-component`: after the split the target label is a single connected component — a slab cut that fragmented the donor too would fire `fragmentation` on both labels and stop the case being a split.
- `expected-labels-equal-the-fired-labels`: `segfacet.synth.regression.offending_labels_match` returns `True` for the committed `split` manifest case — it is an exact equality (A4), and the intuitive `expected_labels = {target, neighbour}` fails it.
- `bounds-stays-silent-on-the-donor`: the donor label's `physical_volume_mm3` and stacking-axis extent in the committed fixture stay inside `bounds.DEFAULT_BOUNDS["lumbar"]`, recomputed from that mapping — at a 0.5 fraction the donor's `extent_z` falls to 13 mm and `bounds` fires (A1), which would validate mode 3 through a proxy the bar's condition 4 excludes.
- `mode-3-intended-rules-unchanged`: `SPECIFICATION[3].intended_rules` still names exactly `bounds` and `reference_delta`, and `"fragmentation"` is not among them — A6; if a later hand authored the co-detection as an edge instead, condition 4 and `derive_status` would both move on a proxy rule.

**Existing tests to reconcile.** Each was found by reading the surface, then
confirmed against this tree on 2026-09-20. Every file is declared under
**Authorised paths → May change** above with its edit named. The first group
goes **red** without the edit:

1. `tests/test_040_synthetic_corpus.py` — `_PIPELINE_ONLY_MODES = {0, 1, 2, 4, 6, 9}`; `test_ac8_modes_4_8_reconstructed_record_rest_pipeline` raises `AssertionError("unexpected failure_mode 3")` on the new case. Add `3`.
2. `tests/test_132_monotonicity_against_traversal_order.py` (line ~502) cross-checks `t040._PIPELINE_ONLY_MODES == {0, 1, 2, 4, 6, 9}`; and its `_ADDED_AFTER_ITEM` pins the uncovered-case set exactly. Both edits.
3. `tests/test_125_stage28_validation.py` and `tests/test_135_stage29_validation.py` — both assert `len(modes) == 5` and `modes == {1, 2, 4, 6, 9}` over the manifest's pipeline-detected modes.
4. `tests/test_149_conformance_report.py` — `len(cases) == 15` and `len(geometric) == ... == 11`.
5. `tests/test_151_stage30_validation.py` — `len(keys) == 15` and `agree_count == 15`.
6. `tests/test_103_feature_catalogue.py` — `_RULE_MODE_MAP` is asserted equal to the live `_scan_synth_rule_mode_map()`; `"fragmentation"` moves from `(1, 2, 4)` to `(1, 2, 3, 4)`.
7. `tests/test_136_rule_mode_declarations.py` — `expected_co_detections` is an **exact** partition; `("fragmentation", 3)` joins it.
8. `tests/test_105_golden_decision_table.py` — `test_ac3_current_tree_has_30_non_py_fixtures` asserts the `tests/` non-`.py` inventory is `22`; and `test_ac3_section1_fixture_set_equals_filesystem_walk_both_directions` requires every on-disk fixture to be documented in `docs/aide/golden-decision-table.md` Section 1, so that document needs a row for `tests/corpus/fixtures/split_seg.nii.gz`.
9. `tests/test_134_decision_table_evidence_companion.py` — `len(inventory) == _ITEM_126_INVENTORY_COUNT + len(_INVENTORY_ADDED_AFTER_126)`; name the new fixture in that set rather than bumping the count.
10. `tests/test_121_tangent_orientation.py` — measured: the receiving label 23's `principal_axis` becomes `[0.0734, 0.0, 0.9973]` (cranio-caudal, as `fuse_adjacent`'s label 22 already is), so `test_ac10_principal_axis_within_0996_of_left_right_on_every_golden` and `test_ac10_principal_axis_exactly_left_right_off_the_named_exceptions` both fail. Add `("split", 23)` to `_FUSED_BODY_SPAN_EXCLUSIONS` and `"split"` to the named-exceptions set, as item 150 did for `fuse_adjacent`; do **not** loosen the 0.996 threshold.
11. `tests/test_116_ras_native_corpus.py`, `tests/test_129_coincident_centroids_and_held_out_floor.py`, `tests/test_131_tangent_direction_normalisation.py`, `tests/test_143_s_axis_correction.py` — each pins the set of cases its pre-item measurement table does **not** cover, as an exact equality against `{"fuse_adjacent", "remove_level_relabel"}`. Add `"split"` to each, with a dated item-166 comment; do not extend the pre-item tables with values those items never measured.
12. `tests/test_057_acceptance_stage7.py` — `test_overall_corpus_sensitivity_is_eight_of_nine_not_over_claimed` pins `metrics.sensitivity == 8/9`; the new case is an expected-failure record and is caught, so the ratio moves. Re-measure, update the docstring's history line, and rename the test to the new ratio.

Stale by omission rather than red, and reconciled anyway:

13. `tests/test_145_eight_hypothesised_modes.py` — `_GEOMETRIC_CORPUS_MODE_IDS = (1, 2, 4, 6, 9, 15)` filters which modes `test_ac8_every_synthetic_demonstrable_edge_is_demonstrated` iterates, and its comment says "Modes 3 and 8 are specified but carry no case". Add `3` and correct the comment. Its `_EXPECTED_DERIVED_STATUS[3] = "implemented"` stays correct and must **not** move.

Conditional:

14. `tests/test_123_recalibrate_and_regenerate.py` — `test_ac45_interior_corpus_ceiling_is_2_510990` maxes the interior spline offset over every corpus case. Measured 2026-09-20, the split case's interior offsets peak at **0.678 mm**, well under the pinned ceiling, so no edit is expected; the file is declared only so a surprise is not a scope violation.

**Found after authoring (Correction — 2026-09-20). Belongs to the first group
above — red without the edit — and is numbered onward rather than inserted, so
entries 1–14 keep the numbers they were authored with:**

15. `tests/test_120_leave_one_out_offset.py` — the AC24 block (lines 722–775 on this tree, 2026-09-20) re-derives `_corpus_cohort_metrics()` over the whole committed manifest and pins the corpus-wide totals a second time, independently of entry 12's `test_057`. Four assertions plus the test's own name go stale; the full site-by-site prescription, and why mode 3's per-mode entry is `1.0`, are in **Correction — 2026-09-20** below.

**Found by validation round 1 (Correction 2 — 2026-09-20). Also the first
group — red without the edit — and numbered onward, so entries 1–15 keep the
numbers they were authored with:**

16. `tests/report_format_fixture.py` + `tests/golden/report_format_contract.json`
    — `tests/test_126_golden_retirement.py::test_adv_format_fixture_floats_do_not_appear_in_any_fresh_corpus_report`
    fails with `overlap == {3.0}`: the fixture's plain round float literals are
    not distinctive in the sense that guard requires, and the new `split` case
    emits a `3.0`. A latent item-126 defect this item exposed rather than
    caused. The site-by-site prescription, the class sweep and the regeneration
    rule are in **Correction 2 — 2026-09-20 §1** below; `test_126` itself needs
    no edit.
17. `docs/aide/golden-decision-table.md` — entry 8 above named the Section-1
    row (already carried on this tree) but not the matching bullet in
    `## Divergences from the roadmap's working assumption`, which
    `test_105::test_ac13_divergences_section_names_exactly_the_keep_rows`
    requires of every `keep` row. The bullet is prescribed in **Correction 2 —
    2026-09-20 §2** below; the file was already authorised.

**Covered automatically — no edit and no new test:**

- **Item 162's exercise report.** `traceability._build_exercise` derives the operator direction from `CASE_RECIPE` live, so the new operator lands as `state="used"`, `cases=("split",)`, and `operator_direction.holes` stays empty. `test_162::test_ac7_operator_cases_match_case_recipe` and `::test_ac8_...` both recompute from the recipe.
- **Item 163's specificity ratchet.** `test_163::test_ac2_ratchet_measured_equals_expected` is parametrised from the live conformance report, so the new case simply appears — and fails unless step 7's authored set is right. That is the point.
- **Item 164's detector conformance.** No `IntendedRule` edge and no `detector_ids` change (A6), so both directions are untouched.
- **Byte-reproducibility.** `test_040::test_ac15/ac16` iterate every manifest case; `test_147::test_ac24` regenerates all three artifact pairs.

## Validation

Beyond the suite, observe the two things the item exists to produce, from the
repo root with the bootstrapped venv:

1. **The fixture expresses a split, not a shrinkage.**
   `.venv/bin/python -m segfacet.synth.golden --out <tmp>` (or
   `segfacet run --seg tests/corpus/fixtures/split_seg.nii.gz --no-reference --out <tmp>`;
   `--no-reference` is required — CLAUDE.md's gotcha on the real-VerSe default).
   Inspect the report: label 22's volume is reduced and label 23's is increased
   by the same amount, the total foreground is unchanged from
   `clean_control_seg.nii.gz`, and the only finding is `fragmentation` on label
   23.
2. **Mode 3's rendering is honest.** Read mode 3's section in the regenerated
   `docs/aide/failure_modes.generated.md`: it must show the `split` corpus case
   with its expected firing and reason, still derive `implemented`, and no
   longer claim that no split fixture is authored. This is the rendering item
   168's human gate puts in front of the maintainer.

No `[validation]` profile is needed: everything above runs CPU-only in the
default venv.

## Dependencies

- **Item 162** (per-rule and per-operator exercise report) — this item's new operator must land in its operator direction without editing the report's code; merged.
- **Item 163** (specificity ratchet) — the ratchet is what forces this item's expected set to be authored; it must stay green with no widening. Merged.
- **Item 164** (first-class detector ids) — supplies the detector id (`fragmentation` / `components`) this item's Description and case `reason` name; merged.

**Downstream:** item 167 authors mode 3's own feature and detector and
**re-authors this case's `expected_firing`** once that detector fires, so item
167's spec lists `src/segfacet/failure_modes.py` and this item's test module
under its own **May change** from the start. Item 168 raises the queue's human
gate over modes 3 and 4 as rendered in
`docs/aide/failure_modes.generated.md`; what this item must leave ready for it
is exactly that rendering — mode 3's entry complete (condition 1 met), its
corpus case and reason stating what fires and via whose detector, and its
derived status honest at `implemented`. Item 169 attests Stage 32 and Stage 20
from a clean clone with its own venv.

**What only a person can decide, and is therefore not an AC here:** whether the
intermediate state this item leaves mode 3 in is an acceptable outcome for the
mode. That is condition 6 of the roadmap's bar, and item 168's gate is where it
is answered; no agent resolves it, and nothing in this spec asserts an outcome
for it.

## Decisions & Trade-offs

- **2026-09-20 (build):** `SplitPerturbation.apply` computes the target's
  stacking-axis span as `axis_max - axis_min + 1` (voxel count, not the raw
  index delta) so `donated_fraction * span` yields the "10 of 25 slices"
  A1 measures at 0.4; the donated slab is selected by comparing the target's
  and neighbour's mean stacking-axis index (never a hardcoded high/low end),
  matching AC3's requirement that the claim hold under either affine
  orientation. Measured against the built fixture: label 22's stacking-axis
  extent shrinks from 25 to 15 voxels (11250 mm³, 15 mm extent_z — exactly at
  `DEFAULT_BOUNDS["lumbar"]["min_extent_z_mm"]`, inclusive, so `bounds` stays
  silent per A1), label 23 gains the donated 7500-voxel slab as a second
  component (`fragmentation_index = 0.714286`), and `run_qc` on the resulting
  fixture (no reference) produces exactly one finding — `fragmentation` on
  label 23, verdict `flagged-for-review` — matching the Description's
  measurement and AC8 exactly.
- **2026-09-20 (build):** all named reconciliations under "existing tests to
  reconcile" (including the Correction's entry 15,
  `tests/test_120_leave_one_out_offset.py`) were already committed by the
  test-writer before this build began (commits `da68784`, `ed01b84`); no test
  file was touched during implementation. `docs/aide/golden-decision-table.md`
  already carried the `split_seg.nii.gz` Section-1 row from the same
  test-writer commit. Verified live: `python .aide/scripts/aide.py scope`
  reports only the two known-and-accepted `§6` traceability warnings (the
  `test_ac24_.../test_overall_corpus_sensitivity_...` renames not carrying an
  item-166 AC number, per the Correction's note that this is a recorded
  framework gap, not a defect) and otherwise OK.
- **2026-09-20 (build):** `test_123_recalibrate_and_regenerate.py`'s interior
  offset ceiling did not need an edit, as A1/entry 14 predicted — no build
  activity touched that file.
- **Left open:** whether `fuse` should gain a *bridged* variant so mode 2 is decided by its own signal rather than by co-detections (roadmap Stage 32's menu, "Mode 2 fused"). This item builds mode 3's converse operator and deliberately does not touch mode 2 — the two are separate maintainer selections, and mode 2 was not selected for queue-022.
- **Left open:** whether `donated_fraction` should eventually be calibrated against real split failures rather than against the synthetic corpus's `fragmentation` threshold. A1's 0.4 is a synthetic-corpus calibration only; roadmap Stage 21 re-calibrates thresholds on real GT.

- **2026-09-20 — the reconciliation list was widened by one file, pre-build; the
  deliverable is unchanged.** `tests/test_120_leave_one_out_offset.py` was
  added to **Authorised paths → May change** and to the "existing tests to
  reconcile" block as entry 15 (**Correction — 2026-09-20**). No acceptance
  criterion, implementation step or assumption moved, and no originally
  authored Authorised-paths entry was altered: what the item builds is exactly
  what it was specified to build, and only the set of files it must carry
  across its own change grew. **Why one grep of the obvious file was not
  enough:** the surface — the corpus's cohort-wide detection totals — is pinned
  **twice, by two independently authored tests in two modules**. Entry 12's
  `tests/test_057_acceptance_stage7.py` owns the claim by subject (Stage 7
  acceptance, overall corpus sensitivity) and was found by reading that
  subject; `tests/test_120_leave_one_out_offset.py` is item 120's
  leave-one-out-offset module, which re-derives the same cohort metrics under
  its own AC24 for a reason unrelated to its module title, with its own
  private copy of the `_corpus_cohort_metrics()` helper and no import of or
  reference to `test_057`. Nothing in the file's name, its item, or the
  surface's obvious owner points at it, and the two copies share no identifier
  a grep of one would surface from the other — so the honest rule is that a
  spec touching a **corpus-wide aggregate** greps the tree for the *measured
  quantity* (`compute_cohort_metrics`, `sensitivity`, `n_cases` totals), not
  for the file that plainly owns it. The same defect class is already on the
  record for item 164 (`docs/aide/insights.md`, item 164, 2026-09-20).

- **2026-09-20 — this is the second reconciliation widening on this item, and
  the deliverable is still unchanged.** `## Correction 2 — 2026-09-20` adds
  `tests/report_format_fixture.py` and
  `tests/golden/report_format_contract.json` to **Authorised paths → May
  change** after validation round 1, and prescribes the fixture's plain round
  float literals away. No acceptance criterion, Assumption, Implementation
  Step, `Asserts against` entry or previously authored `May change` entry
  moved. **The lesson is a different one from Correction 1's, and it is the
  one worth carrying forward: a corpus-wide *value* surface can be pinned by a
  test that names no corpus file at all.** Correction 1's miss was a second
  *file* pinning an aggregate the obvious owner's name would not surface;
  this one is
  `tests/test_126_golden_retirement.py::test_adv_format_fixture_floats_do_not_appear_in_any_fresh_corpus_report`,
  which asserts the hand-written format fixture's distinctive float literals
  are **disjoint from every float a fresh walk of the whole committed corpus
  emits**. What it pins is therefore the corpus's *value* surface: a new case
  turns it red by emitting a number, with nothing in the change's file list,
  its case set, its mode set or its aggregates to point at it. Neither earlier
  sweep could have found it — the authoring sweep searched the surfaces this
  change *touches*, and Correction 1's sweep searched for a measured quantity
  by name (`compute_cohort_metrics`, `sensitivity`, `n_cases`) — because both
  searched **names**, and this test names only the fixture module. So the rule
  a reconciliation sweep needs, stated for the next spec: for a change that
  adds a corpus case, ask what new **values** it emits and grep for assertions
  whose subject is freshly computed output compared against a *literal set* (a
  disjointness, a membership, an exact-value ratchet), not only for the files
  and aggregates the change touches.

- **2026-09-20 (build):** applied `## Correction 2 — 2026-09-20`'s three
  prescribed fixes. **§1:** `tests/report_format_fixture.py`'s
  `_NEGATIVE_FLOAT` changed from `-2.5` to `-84.62037195428361`; added
  `_SECOND_DECIMAL_FLOAT = 53.47129068415773` and
  `_THIRD_DECIMAL_FLOAT = 27.31460592837104`; replaced the five plain-round-float
  sites (`bbox_voxel`/`bbox_physical` maxima, `centroid_voxel`, `centroid_mm`,
  `per_label_offsets[0]["offset_mm"]`) with the named constants per the
  site-by-site prescription; extended the constants-block comment with the
  no-plain-round-float invariant; regenerated
  `tests/golden/report_format_contract.json` via
  `.venv/bin/python -m tests.report_format_fixture` and committed it alongside
  the fixture. Verified directly (not via pytest, per this agent's remit): a
  fresh `build_report_for_case` walk of all twelve committed manifest cases
  emits 948 distinct floats, matching the correction's measurement, and the
  post-fix `distinctive_floats` set
  `{-84.62037195428361, 1e-12, 27.31460592837104, 53.47129068415773,
  106.98418277680141}` has an **empty** intersection with that fresh set.
  **§2:** added the `tests/corpus/fixtures/split_seg.nii.gz` bullet to
  `docs/aide/golden-decision-table.md`'s "Divergences from the roadmap's
  working assumption" section, immediately after the
  `remove_level_relabel_seg.nii.gz` bullet, exactly as prescribed. **§3:**
  added the one-line zero-margin comment at
  `src/segfacet/synth/component_shape.py`'s `donated_fraction: float = 0.4`
  default — comment only, no behaviour or threshold change. Fix 3's plain
  test-bug item (`tests/test_166_split_operator.py`'s
  `compute_label_geometry` call signature) was out of this agent's remit
  (test files) and is left for the validator/test-writer as the correction
  itself notes it needs no spec change.

## Correction — 2026-09-20

**Appended, not a rewrite.** Everything above stands as authored on 2026-09-20.
This section records one **completeness defect in the reconciliation list**,
found **before any build** by the test-writer while deriving the tests from the
criteria above, and prescribes what it adds. **No acceptance criterion, no
implementation step, no assumption, no `Asserts against` entry and no
originally authored `May change` entry is changed by it, and the deliverable is
unchanged** — a split operator, one committed corpus case, and mode 3's
authored expected firing, exactly as specified. What grew is only the set of
files this item must carry across its own change.

### 1. `tests/test_120_leave_one_out_offset.py` pins the same corpus totals a second time

**The gap.** The Testing Strategy's "existing tests to reconcile" block named
14 files; `tests/test_120_leave_one_out_offset.py::test_ac24_corpus_pipeline_detection_is_eight_of_nine`
is a fifteenth, named in neither that block nor **Authorised paths**. Verified
on this tree 2026-09-20, lines 722–775: the test builds its **own**
`_corpus_cohort_metrics()` helper (a private copy, lines 729–747 — it does not
import `test_057`'s) over every case in `load_manifest()`, then asserts

```python
assert metrics.sensitivity == pytest.approx(8.0 / 9.0)
expected_sensitivity = {0: 1.0, 1: 1.0, 2: 1.0, 4: 1.0, 6: 1.0, 9: 1.0, 15: 0.0}
...
assert sum(m.n_cases for m in metrics.per_mode) == 9
```

This is the same surface entry 12 caught on `tests/test_057_acceptance_stage7.py`
(`test_overall_corpus_sensitivity_is_…`, ratio `8/9` → `9/10`); `test_120` was
simply missed. The new split case makes the corpus **ten** expected-failure
records, **nine** of them caught, and adds mode 3 to the per-mode breakdown, so
all three assertions plus the test's own name — which carries the ratio in its
identifier — go stale. The file is outside the originally declared Authorised
paths, so without this correction the builder would be unauthorised to touch
the very test the change turns red.

**The resolution.** `tests/test_120_leave_one_out_offset.py` is added under
**Authorised paths → May change**, and entry **15** of the reconcile block
points here. The edits, prescribed site by site so the test-writer decides
nothing:

- **(a) Section banner, line 723.** `# AC24: The corpus's pipeline-detection
  count is 6 of 8` → `# AC24: The corpus's pipeline-detection count is 9 of
  10`. Note this banner is **already stale on the current tree** (it says 6 of
  8 while the test below it asserts 8/9 — items 132 and 150 moved the ratio and
  left the banner); correcting it is not needed to make the suite green, and it
  is prescribed only because this item is editing the block anyway.

- **(b) The rename, line 750.** `test_ac24_corpus_pipeline_detection_is_eight_of_nine`
  → `test_ac24_corpus_pipeline_detection_is_nine_of_ten`. **Yes — follow
  `test_057`'s new name for consistency**: the test-writer's already-committed
  reconciliation (commit `da68784`) renamed
  `test_overall_corpus_sensitivity_is_eight_of_nine_not_over_claimed` to
  `…_is_nine_of_ten_not_over_claimed`, and the two tests pin the same ratio, so
  they should spell it the same way. The `test_ac24_` prefix and the
  `corpus_pipeline_detection` subject are **kept** — the prefix is item **120**'s
  AC24, which is this test's true provenance, and renaming it to an item-166 AC
  number would falsify that. (Consequence, already on the record: `aide scope`'s
  §6 traceability check attributes a test in a changed file to the *changing*
  item, so it will read `ac24` as an AC item 166 does not have. That is the
  known framework gap captured at `docs/aide/insights.md`, item 164,
  2026-09-20 — not a defect in this rename, and not a reason to renumber.)

- **(c) The rename is safe — checked, not assumed.** Grepped `tests/` and
  `src/` on 2026-09-20 for `test_ac24_corpus_pipeline_detection`: the only hit
  is its own definition. No module calls it by identifier the way
  `tests/test_132_monotonicity_against_traversal_order.py` (line 540) calls
  `test_057`'s renamed function. The two tests that read `test_120`'s **source
  text** — `tests/test_123_recalibrate_and_regenerate.py::test_ac34_retired_test_names_absent_from_test_120_source`
  and its AC50 sibling (lines 1135–1145) — name only
  `test_ac29_reference_verse_v1_unchanged`,
  `test_ac16_default_max_offset_mm_still_15` and a nine-key field set, none of
  them this test. `tests/test_126_golden_retirement.py`'s `test_120` name lists
  (lines 442–444, 507–508) name AC17/AC23/AC25/AC26 only.
  `tests/test_127_committed_artifact_tolerance.py` (line 49) names the *file*,
  not a test in it. So no third file needs an edit for the rename.

- **(d) The docstring.** Keep the existing history chain verbatim (6/8 → 7/8 →
  8/9, with its item-132 and item-150 provenance) and **append** one dated
  line: re-measured 2026-09-20 (item 166) — mode 3's `split` case is the tenth
  expected-failure record and is caught, so overall sensitivity is 9/10 and the
  per-mode breakdown gains mode 3 at 1.0.

- **(e) The overall ratio, line 765.** `pytest.approx(8.0 / 9.0)` →
  `pytest.approx(9.0 / 10.0)`. Derived, not copied from `test_057`:
  `metrics.sensitivity` is `_safe_rate(counts.tp, counts.tp + counts.fn)`
  (`src/segfacet/eval/metrics.py`, `compute_cohort_metrics`) — an
  **outcome**-based ratio. The split case's manifest entry carries
  `expected_verdict="flagged-for-review"` (Implementation Step 4) and the
  measured pipeline verdict is `flagged-for-review` (the Description's
  measurement), so `Outcome.from_flags(True, True)` makes it a **TP**: ten
  expected-failure records, nine TP, the overlap case (mode 15) still the only
  FN.

- **(f) The per-mode dict, line 767.** Add `3: 1.0`, keeping key order:
  `expected_sensitivity = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 6: 1.0, 9: 1.0, 15: 0.0}`.
  **`1.0` — and the reasoning matters, because this metric is not the one in
  (e).** Per-mode `sensitivity` is `n_caught_by_designated_rule / n_cases`
  (`src/segfacet/eval/metrics.py`, `_per_mode_entry`), the **strict** signal,
  not the outcome ratio. `segfacet.eval.outcome.classify_outcome` sets
  `caught_by_designated_rule` True only when some actual finding's `rule_id` is
  in the case's `expected_rule_ids` **and** that finding's labels intersect
  `expected_labels`. For the split case both hold: Implementation Step 4
  authors `expected_rule_ids=frozenset({"fragmentation"})` and
  `expected_labels=frozenset({23})` (A4), and the measured firing is exactly
  one `fragmentation` finding on label 23. So `n_cases == 1`,
  `n_caught_by_designated_rule == 1`, and the entry is `1.0`. The loop's
  `assert entry.n_cases > 0` is satisfied for the same reason.

  **So yes: the `fragmentation` co-detection does count as a detection for this
  metric — and that is not in tension with A6.** The metric reads the *case's*
  `expected_rule_ids`, i.e. what the committed fixture is authored to fire, not
  mode 3's `SPECIFICATION[3].intended_rules`, i.e. what mode 3 is *supposed* to
  be detected by (still `bounds` + `reference_delta`, untouched). They are
  deliberately different objects scored by different code: the eval harness
  asks "did the pipeline raise the rule this fixture predicts", while
  `traceability.bar_conditions` asks "is that rule one of the mode's own". This
  is precisely why **AC9 keeps conditions 2–5 unmet while this entry reads
  1.0** — a 1.0 here is not a claim that mode 3 is detected by its own signal,
  and nothing in this correction weakens AC9. Had the `Expectation` instead
  named mode 3's own `bounds`/`reference_delta`, neither fires without a
  reference, this entry would be `0.0`, and the case would additionally fail
  `offending_labels_match` (A4).

  Corroboration, not derivation: the test-writer's committed reconciliation of
  entry 12 (commit `da68784`) added `3` to `test_057`'s
  `_PIPELINE_DETECTABLE_MODES`, so
  `test_ac9_pipeline_detectable_mode_sensitivity_is_one[3]` independently
  asserts the same `1.0` through the same `_per_mode_entry` path.

- **(g) The record total, line 772.** `sum(m.n_cases for m in metrics.per_mode) == 9`
  → `== 10`. `_compute_per_mode` groups only records with
  `outcome.expected_failure is True`; the split case expects
  `flagged-for-review`, so it contributes exactly one.

- **(h) Unchanged, and must stay so:** lines 773–775 —
  `mode_six.n_cases == 1` (mode 6's other case, `remove_level_relabel`, still
  expects `"pass"` and is still not an expected-failure record) and the mode-10
  all-zero assertion (mode 10 still has no corpus case). The helper at lines
  729–747 also needs **no** edit: it derives its case list from
  `load_manifest()` live, so the new case appears on its own.

### 2. The sweep for a third pin of the same surface — none found

Because two files had now been found pinning corpus-wide detection totals, the
whole of `tests/` was swept on 2026-09-20 for the measured quantity rather than
for the obvious owner: `compute_cohort_metrics`, `sensitivity ==`, `n_cases`,
`per_mode`, the ratio in every form (`8/9`, `8.0 / 9.0`, `eight_of`, `nine_of`)
and cross-references to `test_120` / `test_ac24`. **Exactly three modules build
cohort metrics over the committed manifest, and there is no third pin:**

- `tests/test_057_acceptance_stage7.py` — entry 12, already prescribed and
  already reconciled in commit `da68784`.
- `tests/test_120_leave_one_out_offset.py` — this correction.
- `tests/test_116_ras_native_corpus.py::test_ac8_mode6_crop_at_border_sensitivity_is_restored_to_one`
  (lines ~455–489) — builds the same full-manifest cohort but asserts **only**
  mode **0**'s entry (`n_cases > 0`, `sensitivity == 1.0`) and the crop case's
  own `Outcome.TRUE_POSITIVE`. No corpus-wide total and no exact mode-set
  equality, so a new mode-3 record cannot move it. The file is already under
  **May change** for `_ITEM_150_NEW_CASES`, and **needs no further edit**.

Cleared as not pinning this surface: `tests/test_091_stage14_acceptance.py`
(`per_mode_sensitivity` and `metrics.n_cases == len(held_cases)` are derived
from whichever cohort is passed, and the cohorts are purpose-built stand-ins,
not the committed corpus); and `tests/test_054_metrics.py`,
`tests/test_055_calibrate.py`, `tests/test_056_eval_report.py`,
`tests/test_096_run_manifest.py`, `tests/test_099_per_mode_metrics.py`,
`tests/test_101_per_mode_cohort.py`, `tests/test_153_eval_harness_rekey.py` —
all hand-built or empty cohorts with no corpus dependency.

**Insight inbox.** The `gap` entry the test-writer appended to
`docs/aide/insights.md` (item 166, 2026-09-20) records this same finding. It is
left **exactly as written and unticked** — a captured claim is immutable — and
is **resolved in-item** by this correction.

## Correction 2 — 2026-09-20

**Appended, not a rewrite.** Everything above stands exactly as written: every
acceptance criterion, every Assumption, every Implementation Step, every
`Asserts against` entry, every originally authored `May change` entry, and the
whole of `## Correction — 2026-09-20`. **No acceptance criterion is in dispute
and the deliverable does not change** — a `split` operator, one committed
geometric corpus case, and mode 3's authored expected firing, exactly as
specified. This section resolves the one validation-round-1 failure that needs
the spec's authority before anyone may fix it, and folds two smaller
instructions into the same set so the fix dispatches once.

**Validation round 1 (2026-09-20) returned three failures:**

1. `tests/test_126_golden_retirement.py::test_adv_format_fixture_floats_do_not_appear_in_any_fresh_corpus_report`
   — **§1 below.** It needs two files this item is not authorised to touch.
2. `tests/test_105_golden_decision_table.py::test_ac13_divergences_section_names_exactly_the_keep_rows`
   — **§2 below.** The file is already authorised; the prescription is what was
   missing.
3. `tests/test_166_split_operator.py::test_bounds_stays_silent_on_the_donor`
   calls `compute_label_geometry(donor_img, 22, config)` against the real
   signature `compute_label_geometry(seg_img, label, *, backend=None)` — a
   plain test bug inside this item's **own** already-authorised test module.
   It needs no spec change and is not discussed further here.

§3 records a zero-margin observation the reviewer and the validator both
raised, and prescribes the one-line comment the reviewer suggested.

### 1. The report-format fixture's plain round float literals

**What fails, and what it guards.**
`tests/test_126_golden_retirement.py::test_adv_format_fixture_floats_do_not_appear_in_any_fresh_corpus_report`
(lines 1236–1268 on this tree) collects every float in
`tests/report_format_fixture.py`'s `format_contract_inputs()`, drops the three
values the guard exempts by design — `0.0`, `0.5`, `1.0`, which real reports
legitimately emit as zero extents, midpoint offsets and unit axis components —
and asserts the remainder is **disjoint** from every float a fresh
`build_report_for_case` walk of the whole committed manifest emits. That
disjointness is item 126's contract: the hand-written, feature-value-free
format fixture must use literals unlike anything a real extractor produces, so
the committed `tests/golden/report_format_contract.json` pins the report
*format* and cannot be invalidated by a feature retune. It now fails with
`overlap == {3.0}`, because the new `split` case emits a float `3.0` and
`tests/report_format_fixture.py` line 122 uses `"centroid_voxel": [3.0, 3.0, 3.0]`.

**This is a latent defect item 126 left, which item 166 exposed rather than
caused.** The module's own constants — `_LONG_DECIMAL_FLOAT = 106.98418277680141`
and `_NEAR_ZERO_FLOAT = 1e-12` — were chosen for exactly this property. But
lines 122–123 (`[3.0, 3.0, 3.0]`, `[6.0, 6.0, _NEAR_ZERO_FLOAT]`), and three
further sites named below, use plain round numbers instead. **`3.0` and `6.0`
were never distinctive in the sense the guard requires**; they simply had not
yet collided with a real value. Any corpus case added at any time could have
done this, and the ones still uncollided can do it tomorrow. Item 166's role is
to have been the case that arrived first.

**Measured on this tree, 2026-09-20** (`.venv/bin/python`, the same
`segfacet.synth.golden.build_report_for_case` walk the guard performs, over all
twelve committed manifest cases including the new `split` case):

- the fixture's float literals are
  `{-2.5, 0.0, 1e-12, 0.5, 1.0, 2.5, 3.0, 6.0, 12.0, 106.98418277680141}`;
- the guard's `distinctive_floats` is therefore
  `{-2.5, 1e-12, 2.5, 3.0, 6.0, 12.0, 106.98418277680141}`;
- a fresh walk emits **948** distinct floats, and the intersection is exactly
  `{3.0}`;
- `6.0`, `12.0`, `2.5` and `-2.5` are **not** in the fresh set today. They are
  the same class as `3.0` — plain round values the guard treats as distinctive
  while an extractor may plausibly emit them — and are prescribed away below,
  so this correction closes the class rather than patching the one collision.

Integer literals in the module (`voxel_count: 42`, `component_sizes: [42]`,
`overlap_voxels: 3`, `label: 7`) are **not** at risk: `_collect_floats` gathers
only `float` instances, and an `int` is never one.

**Authorised paths → May change gains two entries** (appended; no existing
entry is altered):

- `tests/report_format_fixture.py` — the sole source of the format contract;
  its plain round float literals are what collide with the new corpus case
- `tests/golden/report_format_contract.json` — the committed contract the line
  above regenerates; four consumer tests compare it byte-for-byte

**The prescribed fix, site by site, so the fix dispatch decides nothing.**

- **(a) The constants block, lines 49–57.** Keep `_INTEGRAL_FLOAT = 1.0`,
  `_LONG_DECIMAL_FLOAT = 106.98418277680141` and `_NEAR_ZERO_FLOAT = 1e-12`
  **unchanged** — the first is guard-exempt by design and carries the integral
  rendering shape; the other two are named by
  `test_126::test_ac10_key_order_key_set_and_float_rendering_asserted_explicitly`.
  Change `_NEGATIVE_FLOAT` from `-2.5` to **`-84.62037195428361`**, keeping the
  negative rendering shape and losing the round value. Add two constants in the
  module's own pattern:

  ```python
  _SECOND_DECIMAL_FLOAT = 53.47129068415773
  _THIRD_DECIMAL_FLOAT = 27.31460592837104
  ```

  and extend the block's comment (lines 49–53) to state the invariant the next
  author must keep: **every float literal in this module is either `0.0`, `0.5`
  or `1.0` — the three values `test_126`'s guard exempts because real reports
  legitimately emit them — or one of the named long-decimal / exponent-form
  constants. No plain round float is ever written here directly.**

- **(b) `bbox_voxel`, lines 93–95.** `x_max`, `y_max`, `z_max`: `6.0` →
  `_SECOND_DECIMAL_FLOAT`. The three `*_min` stay `0.0`.

- **(c) `bbox_physical`, lines 98–100.** `x_max`, `y_max`, `z_max`: `12.0` →
  `_THIRD_DECIMAL_FLOAT`. The three `*_min` stay `0.0`.

- **(d) `centroid_voxel`, line 122.** `[3.0, 3.0, 3.0]` →
  `[_SECOND_DECIMAL_FLOAT, _SECOND_DECIMAL_FLOAT, _SECOND_DECIMAL_FLOAT]`.
  **This is the one site failing today.**

- **(e) `centroid_mm`, line 123.** `[6.0, 6.0, _NEAR_ZERO_FLOAT]` →
  `[_THIRD_DECIMAL_FLOAT, _THIRD_DECIMAL_FLOAT, _NEAR_ZERO_FLOAT]`.

- **(f) `per_label_offsets[0]["offset_mm"]`, line 159.** `2.5` →
  `_SECOND_DECIMAL_FLOAT`. Keep the existing
  `# offset_mm is schema-constrained to >= 0` comment; `53.47129068415773`
  satisfies it.

- **(g) Nothing else moves.** Every remaining float literal is already either
  guard-exempt (`0.0` at the bbox minima, `stray_volume_mm3`,
  `stray_volume_fraction`, `cv_spacing`, `sagittal_curvature_deg`,
  `principal_axis[0..1]`, `u_values[0]`; `0.5` at `closest_u` and `u_values[1]`;
  `_INTEGRAL_FLOAT`) or one of the named distinctive constants. The four sites
  that read `_NEGATIVE_FLOAT` (`extent_y_mm`, `dx_mm`,
  `coronal_tangent_angles_deg`, `deviations_mm`) pick up (a)'s new value with
  no edit of their own.

**Why these three values — checked, not asserted.** Measured on this tree
2026-09-20 against the 948-float fresh walk: none of `53.47129068415773`,
`27.31460592837104`, `-84.62037195428361` appears in it, each is repr-stable
(`repr(float(repr(x))) == repr(x)`, so the serialised JSON text round-trips
exactly), and the post-fix `distinctive_floats` is
`{-84.62037195428361, 1e-12, 27.31460592837104, 53.47129068415773, 106.98418277680141}`
with an **empty** intersection against the fresh set. The substituted inputs
were serialised through `serialize_report_json` and validated against
`src/segfacet/report_schema_v0.json`: **schema OK.** The schema constrains none
of these sites beyond type — `bbox` carries no min/max ordering rule, the
extents and tangent-angle and deviation arrays are unbounded `number`s, and the
only `minimum: 0` in play (`offset_mm`, `offset_voxel`) is satisfied.

**The regeneration rule, stated because getting it wrong is itself a defect.**
`tests/golden/report_format_contract.json` regenerates **only** via

```
.venv/bin/python -m tests.report_format_fixture
```

**never from a test** — item 111's write-and-skip prohibition, carried forward
by item 126 AC11, whose static half is enforced by
`tests/committed_artifact_guard.py` (its `tests/golden/*.json` allowlist entry,
ground `hand-written-literals`, which the prescription above keeps true) and by
`test_126::test_ac11_consumer_source_has_no_skip_or_write_branch`. **The
builder runs it**, once, by hand, after the fixture edit, and **commits the
regenerated contract in the same change as the fixture** — the two are compared
byte-for-byte by `test_016_features_json.py`, `test_022_stage3_serialisation.py`,
`test_126::test_ac9_fixture_text_is_reproduced_by_the_builder_module_alone` and
`test_135_stage29_validation.py`, so a fixture edit without the regenerated
contract is red in four places, and a hand-edited contract is red in the same
four. No `.gitattributes` edit is needed: `tests/golden/*.json text eol=lf`
(line 69) already covers it, and the module already writes with `write_bytes`.

**Does `tests/test_126_golden_retirement.py` itself need an edit? No — read on
this tree, 2026-09-20, before answering.**

- The guard stands as authored. Its exempt set `(0.0, 0.5, 1.0)` is **correct**,
  and widening it to admit `3.0`/`6.0`/`12.0` would blunt precisely the coupling
  check item 126 built — those are values a real extractor emits, which is the
  whole reason the fixture must not use them. The defect is in the fixture, and
  that is where it is fixed.
- `test_ac10_key_order_key_set_and_float_rendering_asserted_explicitly`
  (line 348) requires `"1e-12"` or `"106.98418277680141"` to appear in
  **`test_016`/`test_022`'s** source, not in the fixture's; both constants are
  kept unchanged by (a), and that test does not read this module at all.
- `test_ac9_fixture_builder_module_exists_and_imports_no_extractor` passes
  unchanged: the prescription adds literals, no imports.
- `test_ac8_*`, `test_ac21_*`, `test_ac23_*` and `test_ac24_*` are about paths,
  decision-table rows and `.gitattributes` pins, none of which move.

**And no other consumer needs an edit.** `test_016`, `test_022` and `test_135`
compare `format_contract_text()` against the committed file rather than
pinning any value from it; `test_111_golden_guard.py` and
`committed_artifact_guard.py` key on the path and the `tests/golden/*.json`
glob. Grepped `tests/` and `src/` on 2026-09-20 for `106.98418277680141`: the
only hits are the fixture itself, the `test_126` line above, and
`tests/test_042_golden_determinism.py:482`, which uses the same number in a
hand-built numeric-tolerance example unrelated to this module and unaffected by
this change. **So editing `tests/report_format_fixture.py` and committing the
regenerated contract is sufficient.**

### 2. `docs/aide/golden-decision-table.md` — the missing divergences bullet

`docs/aide/golden-decision-table.md` is **already** under **Authorised paths →
May change**, and already carries the Section-1 `keep` row for
`tests/corpus/fixtures/split_seg.nii.gz` (line 184 on this tree). What is
missing is the matching entry in `## Divergences from the roadmap's working
assumption`, which `test_105::test_ac13_divergences_section_names_exactly_the_keep_rows`
requires of **every** `keep` row — it asserts each keep fixture's path appears
verbatim in that section's body — and which every other `keep` input fixture,
including the two item 150 added, has.

Prescribed, in the shape the existing entries use, placed immediately after the
`tests/corpus/fixtures/remove_level_relabel_seg.nii.gz` bullet (line ~295) so
the geometric fixtures stay together and ahead of the intensity group:

```
- `tests/corpus/fixtures/split_seg.nii.gz` — input fixture, not a
  report snapshot (added by item 166, 2026-09-20).
```

Nothing else in that document moves: the Section-1 row stands as committed, no
`disposition`, `rationale`, `evidence` or `replacement guarantee` cell changes,
and the retirement execution log is untouched.

### 3. The donor's zero margin against `min_extent_z_mm` — an appended note to A1

**A1 stands exactly as written; this is a note beside it, not a correction of
it.** A1 records that a `donated_fraction` of 0.5 fires `bounds` on the donor
and 0.4 does not. What it does not record is **how close 0.4 is**: measured on
the built fixture, donor label 22's `extent_z_mm` is exactly **15.0 mm**
against `bounds.DEFAULT_BOUNDS["lumbar"]["min_extent_z_mm"] == 15.0`, and
`bounds` stays silent **only because the comparison is strict** — `if value < lo`,
`src/segfacet/heuristics/bounds.py:480`. The margin is **zero**. Both the
reviewer and the validator flagged it.

**The reviewer judged it not a defect and ranked it a nit, and this spec
records that reasoning rather than re-opening it.** The equality is exact
integer-voxel arithmetic — 15 remaining slices at spacing `[1.0, 1.0, 1.0]` —
not floating-point luck, so it cannot drift by a ULP; and three independent
tests catch a real drift: this item's `bounds-stays-silent-on-the-donor` case
(which recomputes the range from `DEFAULT_BOUNDS` rather than pinning A1's
numbers), AC8's measured-equals-expected firing set, and item 163's specificity
ratchet.

**Prescribed, as the reviewer suggested:** a one-line comment at
`src/segfacet/synth/component_shape.py`'s `donated_fraction: float = 0.4`
default (line 313 on this tree) recording that 0.4 leaves the donor's
`extent_z` at exactly the lumbar `min_extent_z_mm` of 15.0 mm — a zero margin
held by the strict `<` — and that raising the default fires `bounds` (A1). That
file is already under **May change**. No behaviour change, no threshold change,
no acceptance criterion, and nothing in AC8 or AC9 moves.
