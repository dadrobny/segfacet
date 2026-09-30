<!-- aide-template: item 3 -->
# Item 206 — A fixture for one label over two full, separate vertebrae

> **Created:** 2026-09-30 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (D5 re-plan)
> **Queue:** [`../queue/queue-027.md`](../queue/queue-027.md) · Item 206
> **Objectives:** G2, G7
> **Suggested branch:** `aide/206-a-fixture-for-one-label`

---

## Description

This item adds the second mode-2 (fused vertebra segments) case to the
committed geometric corpus. It is one of the four re-plan items (205–208) that
must land before the at-the-bar sign-off of modes 2 and 3 under gate
`gate-0133` (item 203; `queue-027.md`, "Re-plan").

**Why the case is needed.** Mode 2 today has two corpus cases. `split`
(re-homed to mode 2 by item 205) is the paired case, where one label covers
its own vertebra plus a cap of its neighbour. `neighbour_contact`'s
`stray_contact` detector decides it, because the cap touches the vertebra it
was taken from. `fuse_adjacent` (item 176) is the bridged case: one connected
label over L3 and L4 with the disc gap filled, which fires nothing. Neither
covers the variant in which one label covers two complete vertebrae that do
not touch. There the second body is a stray component with no contact, so
contact cannot see it, and mode 2's fused-label detector (item 207) needs a
case of this shape to fire on besides `fuse_adjacent`.

**The case.** `fuse_separate`, on the lordotic base (item 173). Label 22 (L3)
covers both the L3 body and the L4 body. The 8 mm disc gap between them stays
unlabelled. L5 (clean label 24) is renumbered 23, so the label sequence stays
continuous (20, 21, 22, 23), as `fuse_adjacent` does. The case is attributed
to mode 2. Its expected set records what fires today, measured live:
`fragmentation` alone (detector `components`, on label 22), because the label
now has two components and its `fragmentation_index` (0.5012) is below the
0.75 threshold. That firing is a co-detection: `fragmentation` serves mode 1
("one label in several parts"), and mode 1 is attributed only when no other
mode applies (item 194). The case is not a mode-1 case, because the two parts
are two whole vertebrae under one label.

**What this item changes.**

- `synth/component_shape.py`: `FusePerturbation` gains a `renumber` keyword,
  so the unbridged form can renumber the caudal labels (A2).
- `synth/corpus.py`: one `CASE_RECIPE` entry, appended last.
- `failure_modes.py`, `_MODE_2`: one `CorpusCaseExpectation` for
  `fuse_separate`, and a mechanism sentence naming it.
- The corpus (`tests/corpus/manifest.json`, one new fixture), the corpus
  sheet, and the generated specification, traceability, catalogue and
  golden-evidence documents are regenerated.
- `docs/aide/golden-decision-table.md` gains the new fixture's Section-1 row
  and its Divergences bullet, as items 174 and 175 did for theirs.
- The existing tests that pin the corpus's case set or counts are reconciled
  (Testing Strategy).

**Not in scope.**

- No detector, no rule change and no threshold. Every existing corpus case
  fires exactly what it fires today, and every existing fixture regenerates
  byte-identical (A6).
- Mode 2's fused-label detector is item 207. This item's expected set is
  today's firing, and item 207 adds its detector to it.
- `MODE_SIGN_OFFS` is not touched (item 203).
- `tests/corpus/094_pre_migration_snapshot.json` is not extended (Decisions).

## Acceptance Criteria

Terms used below:

- **"The case"** is the entry of `segfacet.synth.corpus.load_manifest()["cases"]`
  whose `case_id` is `"fuse_separate"`. **"Its fixture"** is the label array
  loaded (`segfacet.io.load_case`, or
  `segfacet.synth.regression.loaded_seg_image`) from the case's `seg_fixture`
  under `segfacet.synth.corpus.CORPUS_DIR`.
- **"The clean array"** is the label array loaded the same way from the
  `clean_control` case's `seg_fixture`.
- **"The modes carrying case C"** is the set of mode ids `m` over every entry
  of `segfacet.failure_modes.SPECIFICATION` such that some element of mode
  `m`'s `corpus_cases` has `case_id == C`. The test computes it over all
  modes.

- [ ] **AC1: `fuse_separate` is attributed to mode 2 alone.** The modes
  carrying case `"fuse_separate"` equal `{2}`.
- [ ] **AC2: label 22 is exactly the two full bodies.** Under 6-connectivity
  (`scipy.ndimage.label` with its default structure, the connectivity
  `segfacet.features.components.CONNECTIVITY` documents), the set of voxel
  sets of the connected components of `fixture == 22` equals
  `{clean == 22, clean == 23}`. There are two components, each equal to one
  clean body.
- [ ] **AC3: every other voxel is the clean map with L5 renumbered.** On the
  voxels where the clean array is neither 22 nor 23, the fixture equals the
  clean array with 24 replaced by 23 and every other value unchanged.

Why each is written:

- AC1 is the queue's "It is attributed to mode 2". Without it the case could
  be attached to another mode, or to none, while the manifest still carried
  `failure_mode` 2. `specification_conflicts()` would then report the
  mismatch, but not which side is wrong.
- AC2 is the queue's "The fused label has exactly two components, each one a
  full vertebral body". It is what makes the case the separate-bodies variant
  rather than `fuse_adjacent` (one component) or a partial fuse. Item 207's
  detector reads this case as a label twice a single level's size, flanked by
  wide spacing, and it would read neither with one body missing or cut.
- AC3 is the queue's "the labels caudal to it are renumbered so the sequence
  stays continuous". Without the renumbering the label map also expresses a
  skipped level (mode 10), and `coverage` and `sequence` fire on it. Item 207
  must stay silent on mode-10 and mode-6 cases, so a case that mixes the two
  would not isolate its signal.

Not written, because something already fails without them:

- "The case is in the committed manifest": every AC above reads the case from
  the manifest and fails when it is absent.
- "The case is in the corpus sheet": `sheet_panels()` renders one panel per
  manifest case, and `tests/test_178_corpus_sheet.py` compares the committed
  PNG's `Source` digest (over the manifest and every seg fixture) with a
  fresh one, so a sheet not regenerated after the case is added fails there.
- "Its measured firing equals its expected set":
  `tests/test_163_specificity_ratchet.py` parametrises one test per committed
  case and fails on any case that disagrees or has no `SPECIFICATION` entry.
  The expected set's value (`("fragmentation",)`) is recorded in A4, not
  pinned by this item's tests, because item 207 adds its own rule to it.
- The manifest's `failure_mode` 2 and its designation:
  `tests/test_146_ninth_mode_and_first_proposed.py`'s AC31
  (`specification_conflicts() == ()`), `tests/test_040_synthetic_corpus.py`'s
  AC17 (manifest equals the operator's `Expectation`) and
  `tests/test_041_regression_suite.py`'s AC4–AC6 (verdict, designated rule,
  offending labels) cover it.
- "Every existing fixture is unchanged": `aide scope` proves it on the diff,
  since no existing fixture is under **May change**, and
  `tests/test_040_synthetic_corpus.py`'s AC15/AC16 compare every committed
  fixture with a fresh regeneration.

None of these closes a Stage 33 acceptance criterion. Criterion 2 ("no case
attributed to a mode its label map does not express") is attested by item 204
over the whole corpus.

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
measured value below was taken on this branch on 2026-09-30 with
`.venv/bin/python`, by a scratch probe that applied the change in memory. The
probe patched `FusePerturbation` as A2 describes, appended the A1 recipe entry,
ran `write_corpus` into a scratch directory, pointed `load_manifest`,
`loaded_seg_image`, `build_report_for_case` and the corpus-sheet functions at
it, and replaced `failure_modes.SPECIFICATION` with a dict whose mode 2 carries
the A4 case. It then re-ran every derivation and every generator into scratch
paths and compared them with the committed copies. The builder re-measures
each value on the real change.

- **A1 (defensible default: the case id, recipe and placement).** The case id
  is `fuse_separate`. It names the operator, as `fuse_adjacent` does, and says
  what distinguishes it. The recipe entry is appended **last** in
  `CASE_RECIPE`, so the existing 13 manifest entries keep their order and
  bytes and the sheet's existing panels keep their positions:
  `_RecipeEntry(case_id="fuse_separate", perturbation="fuse",
  perturbation_params={"target_label": 22, "neighbour_label": 23,
  "bridged": False, "renumber": True}, detection="pipeline")`, on the default
  base. The pair is L3/L4, the same pair as `fuse_adjacent`, so the two mode-2
  fuse cases differ only in the disc gap. Every parameter is written
  explicitly so that a later default change cannot move the fixture.
  **Item 207 reads the case by this id.**
- **A2 (defensible default: the operator form).** `FusePerturbation.__init__`
  gains `renumber: Optional[bool] = None`, where `None` resolves to the value
  of `bridged`. So the default unbridged form (the supplementary severity
  ladder's) and the bridged form (`fuse_adjacent`) are unchanged, byte for
  byte, and `fuse_adjacent`'s recipe parameters do not change.
  - `bridged=False, renumber=True` is the new form. It relabels the neighbour
    onto the target, fills nothing, and renumbers every present label greater
    than the neighbour to the present label before it, as the bridged branch
    does today. It requires the neighbour to be the next-higher present label,
    with the same `FacetInputError` the bridged branch raises.
  - `bridged=True, renumber=False` raises `FacetInputError`. The bridged form
    always renumbers, and no case needs the combination.
  - The new form's `Expectation`: `failure_mode=2`,
    `failure_mode_name=FAILURE_MODE_NAMES[2]`,
    `expected_rule_ids=frozenset({"fragmentation"})`,
    `expected_labels=frozenset({target})`,
    `expected_verdict="flagged-for-review"`, and a `detail` that names the
    renumbering and calls `fragmentation` a co-detection.

  No new operator is registered. A new name would reach
  `UNUSED_OPERATOR_REASONS`, the exercise report's operator table and item
  201's `per_ladder` coverage for no gain.
- **A3 (constraint: the case must designate `fragmentation`).**
  `tests/test_041_regression_suite.py::test_ac5_undetected_failure_case_fires_nothing_and_verifies`
  requires a failure case that designates no rule to fire nothing, and this
  case fires `fragmentation`. So the manifest designates it, as `remove_level`
  designates `coverage` under mode 6. `catalogue.rule_declaration_conflicts()`
  stays `()`: the corpus-designated pair `(fragmentation, 2)` is exempt
  because mode 2's `corpus_cases` record `fragmentation` in an
  `expected_firing` and mode 2 has no `fragmentation` edge (the item-150
  co-detection exemption). No declaration and no `IntendedRule` changes.
- **A4 (measured: what the case fires).** Through
  `segfacet.synth.regression.pipeline_findings` under the bundled default
  config there is exactly one finding: `fragmentation`, detector
  `components`, labels `[22]`. The verdict is `flagged-for-review`.
  `measured_detector_firing` is `(("fragmentation", "components"),)`.
  `designated_rule_fired`, `offending_labels_match` and `verify_case` are all
  `True`. So the `SPECIFICATION[2]` entry is
  `CorpusCaseExpectation(case_id="fuse_separate", corpus="geometric",
  expected_firing=("fragmentation",), reason=...)`, and its reason records
  these values with the date. Label 22 reads `component_count` 2, sizes
  `[19437, 19344]`, `fragmentation_index` 0.5012,
  `stray_contact_area_mm2` 0.0 and `label_contact_fraction` 0.0, and
  `neighbour_contact` is silent. Stage 3 `spacing_consistency.spacings_mm` is
  `[33.49, 49.46, 53.50]`, against clean_control's
  `[33.49, 32.70, 33.87, 36.84]` and fuse_adjacent's `[33.49, 49.51, 53.52]`.
  Label 22's volume is 38781 mm³, against 19437 and 19344 for the two clean
  bodies. Those are the two signals item 207 reads.
- **A5 (measured: the fixture).** Voxel counts in the probe: clean labels 22
  and 23 hold 19437 and 19344 voxels, and the case's label 22 has two
  6-connected (and two 26-connected) components, equal to those two sets. The
  present labels are `{20, 21, 22, 23}`.
- **A6 (measured: what the derivations move).**
  - Every existing fixture under `tests/corpus/fixtures/` regenerates
    byte-identical. The manifest gains one entry, and the first 13 entries are
    unchanged.
  - `specification_conflicts()`, `catalogue.rule_declaration_conflicts()`,
    `catalogue.path_classification_conflicts()` and
    `traceability.operator_reason_conflicts()` all return `()`.
  - Conformance: 17 → 18 cases (14 geometric plus 4 intensity), all agree.
  - `bar_conditions(2)` and `bar_conditions(3)` are unchanged from item 205's
    record. Mode 2 meets conditions 1–5, and condition 2's subjects stay
    `("split",)`, because `fragmentation/components` is not a mode-2 pair.
    Mode 3 meets 1, 2 and 5.
  - Every mode's derived status and rung is unchanged. Counts over 16 modes:
    validated 6, implemented 3, specified 2, proposed 5. Rungs:
    synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1,
    none 7. **So no `progress.md` count clause moves.**
    `tests/test_151_stage30_validation.py`'s AC35 and
    `tests/test_169_stage32_validation.py`'s AC6/AC7/AC8 stay green with no
    `aide progress amend`.
  - `catalogue.scan_synth_rule_mode_map()["fragmentation"]` goes from
    `(1, 4)` to `(1, 2, 4)`. So five catalogue leaves gain mode 2:
    `per_label.{label}.components.component_count`, `component_sizes[]`,
    `fragmentation_index`, `largest_component_fraction` and
    `stray_component_sizes[]`. Catalogue entries carrying mode 2 go from 5 to
    10, and the entry count stays 145.
  - Generated artifacts that move: `failure_modes.generated.{json,md}`,
    `traceability_matrix.generated.{json,md}` (a conformance row, and
    `fragmentation`'s and `fuse`'s exercise rows),
    `feature_catalogue.generated.{json,md}`, `golden_evidence.generated.json`
    (a `fuse_separate` entry) and `corpus_sheet.png` (a 14th panel and the
    digest). `rules.generated.md` does not move.
  - The cohort evaluation over the corpus (`tests/test_057_acceptance_stage7.py`)
    gains one expected-failure record, which is caught. Overall sensitivity
    goes from 9/9 to 10/10, still 1.0. Mode 2's per-mode sensitivity stays
    1.0.
- **A7: no human gate, and no environment-gated capability.**

## Implementation Steps

1. **`src/segfacet/synth/component_shape.py`, `FusePerturbation`.**
   - Add `renumber: Optional[bool] = None` to `__init__` and store
     `self._renumber = self._bridged if renumber is None else bool(renumber)`.
     Raise `FacetInputError` for `bridged=True` with `renumber=False` (A2).
   - In `apply`, add the `not bridged and renumber` branch. Reuse the bridged
     branch's next-higher check and its caudal renumbering (`caudal`,
     `renumbered` and the `data[orig == old] = new` loop) rather than writing
     them a second time. Factoring both into one module-private helper is the
     expected shape. The bridged branch's voxel output must not change.
   - Give the branch its `Expectation` (A2).
   - Update the class and module docstrings: three forms, and which corpus
     case or ladder uses each.
2. **`src/segfacet/synth/corpus.py`.** Append the A1 `_RecipeEntry` with a
   dated item-206 comment. Update the module docstring's case count and list
   ("thirteen canonical cases") and the `CASE_RECIPE` comment.
3. **`src/segfacet/failure_modes.py`, `_MODE_2`.**
   - `corpus_cases`: append the A4 `CorpusCaseExpectation`. Its `reason`
     says the case is pipeline-detected, measured live via
     `segfacet.synth.regression.pipeline_findings` (date, item 206). It gives
     the construction (L3 and L4 under label 22, the gap unlabelled, L5
     renumbered 23), the one `fragmentation`/`components` finding on label 22
     with its `fragmentation_index`, and calls it a co-detection: mode 1's
     detector, not mode 2's own. It also says that `neighbour_contact` is
     silent because the second body touches nothing, and that mode 2's own
     signal (label size and the spacings around it, values from A4) is read
     by no rule yet.
   - `mechanism`: add one sentence for the separate-bodies case that names
     `fuse_separate` as a whole word. `tests/test_138_traceability_matrix.py`'s
     AC31 checks: a feature path the sentence names must be consumed by mode
     2's declared rules (`bounds`, `neighbour_contact`) or by a rule
     co-detecting on a mode-2 case. `fragmentation` becomes one, so its
     `components` paths may be named. Do not use the
     `(measured: findings == [...])` idiom.
   - No other field, and no other mode, changes.
4. **Regenerate.** Run each generator twice into temp paths, byte-compare,
   then once with no flags to write the committed copies:
   - `.venv/bin/python -m segfacet.synth.corpus`. Only `manifest.json` and the
     new `fixtures/fuse_separate_seg.nii.gz` may change. If an existing
     fixture's bytes change, hand back (A6);
   - `.venv/bin/python -m segfacet.synth.corpus_sheet`;
   - `.venv/bin/python -m segfacet.failure_modes`;
   - `.venv/bin/python -m segfacet.traceability`;
   - `.venv/bin/python -m segfacet.catalogue`;
   - `.venv/bin/python -m segfacet.golden_evidence`.

   Then confirm that a fresh `python -m segfacet.rule_table --md <tmp>` is
   byte-identical to the committed `docs/aide/rules.generated.md` (A6).
5. **`docs/aide/golden-decision-table.md`.** Add a Section-1 row for
   `tests/corpus/fixtures/fuse_separate_seg.nii.gz` directly after the
   `crop_fov_si_scan.nii.gz` row, in the shape of the other corpus-fixture
   rows. The asserted-by cell is `tests/test_040_synthetic_corpus.py`, the
   evidence cell `n/a`, the disposition `keep` and the replacement guarantee
   `—`. Add a matching bullet to "Divergences from the roadmap's working
   assumption" after the `crop_fov_si_scan.nii.gz` bullet: "input fixture,
   not a report snapshot (added by item 206, 2026-09-30)". Write the file
   with `\n` line endings; it is pinned `text eol=lf`.
6. **Reconcile** the tests listed under Testing Strategy, each edit with a
   dated item-206 comment.
7. Run `python .aide/scripts/aide.py scope 206` and
   `python .aide/scripts/aide.py check`. Neither may report an error.

No dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/synth/component_shape.py` — `FusePerturbation`'s `renumber` form and docstrings (step 1).
- `src/segfacet/synth/corpus.py` — the `fuse_separate` recipe entry and the module docstring (step 2).
- `src/segfacet/failure_modes.py` — `_MODE_2`'s new corpus case and one mechanism sentence (step 3).
- `tests/corpus/manifest.json` — regenerated; one appended case (step 4).
- `tests/corpus/fixtures/fuse_separate_seg.nii.gz` — **new**: the case's fixture (step 4).
- `docs/aide/corpus_sheet.png` — regenerated; a 14th panel and the input digest (step 4).
- `docs/aide/failure_modes.generated.json` — regenerated (step 4).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 4).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated; five `components` leaves gain mode 2 (step 4).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `docs/aide/golden_evidence.generated.json` — regenerated; a `fuse_separate` entry (step 4).
- `docs/aide/golden-decision-table.md` — the new fixture's Section-1 row and Divergences bullet (step 5).
- `tests/test_206_fuse_separate_fixture.py` — **new**: this item's test module.
- `tests/test_103_feature_catalogue.py` — `_RULE_MODE_MAP["fragmentation"]` `(1, 4)` → `(1, 2, 4)`.
- `tests/test_105_golden_decision_table.py` — the non-.py inventory count 25 → 26, in two places.
- `tests/test_116_ras_native_corpus.py` — `fuse_separate` joins `_ITEM_150_NEW_CASES`.
- `tests/test_120_leave_one_out_offset.py` — the per-mode `n_cases` sum 9 → 10.
- `tests/test_121_tangent_orientation.py` — `fuse_separate` joins both principal-axis exception sets.
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — `fuse_separate` joins `_ADDED_AFTER_129`.
- `tests/test_131_tangent_direction_normalisation.py` — `fuse_separate` joins `_ADDED_AFTER_ITEM`.
- `tests/test_132_monotonicity_against_traversal_order.py` — `fuse_separate` joins `_ADDED_AFTER_ITEM`.
- `tests/test_134_decision_table_evidence_companion.py` — the new fixture joins `_INVENTORY_ADDED_AFTER_126`.
- `tests/test_136_rule_mode_declarations.py` — `("fragmentation", 2)` joins `expected_co_detections`.
- `tests/test_137_mode_less_rule_disposition.py` — `mode2_count` 5 → 10, a dated comment and an appended docstring paragraph.
- `tests/test_143_s_axis_correction.py` — `fuse_separate` joins `_ADDED_AFTER_ITEM`.
- `tests/test_149_conformance_report.py` — conformance case counts 17 → 18 and 13 → 14.
- `tests/test_151_stage30_validation.py` — conformance case count 17 → 18, in two places.
- `tests/test_153_eval_harness_rekey.py` — `_rule_b_home` reads every manifest case of an operator (the one structural edit; see the fence).

**The reconciliation fence.** Every edit to an existing test is a moved
literal: a count, a case added to a named set of post-item cases or of
exceptions, a mode tuple, a co-detection pair. Each carries a dated item-206
comment. No test is retired, skipped, `xfail`-marked or loosened. The fence
is widened for one named edit that is not a moved literal:
`tests/test_153_eval_harness_rekey.py`'s `_rule_b_home` (Testing Strategy).
A red test in a file not listed here is a hand-back to spec-author.

**Asserts against:**

- `docs/aide/rules.generated.md` — must not move (A6); `tests/test_202_rule_table.py` compares it with a fresh render.
- `tests/test_163_specificity_ratchet.py` — must stay green unedited; it drives the new case's firing against its expected set.
- `tests/test_041_regression_suite.py` — must stay green unedited; it drives the new case's verdict, designation and labels.

`tests/test_169_stage32_validation.py` is deliberately listed under neither
heading. It must stay green on this branch, because this item moves no
`progress.md` clause it reads (A6). But item 203, which runs later, may edit
it, so pinning it here would be a premise about that item's schedule.

## Testing Strategy

The test module is `tests/test_206_fuse_separate_fixture.py`, with one test
per AC.

- AC1 computes the modes carrying `fuse_separate` over every entry of
  `SPECIFICATION`, never from mode 2 alone.
- AC2 and AC3 load both fixtures through the committed manifest's
  `seg_fixture` paths (never a fresh `build_corpus()`), so they pin the
  committed bytes. AC2 compares the components as a set of voxel-index sets
  (for example `frozenset` of `np.flatnonzero` tuples), so neither the
  component order nor the labelling order matters.

Adversarial cases, each with the failure mode it guards:

- `bridged-renumber-false-raises`: `FusePerturbation(target_label=22,
  neighbour_label=23, bridged=True, renumber=False).apply(...)` (or its
  constructor) raises `FacetInputError`. It guards against the combination
  silently producing a label map whose `Expectation` (the bridged branch's
  "fires nothing") no longer describes it.
- `default-unbridged-form-unchanged`: `FusePerturbation(target_label=22,
  neighbour_label=23)` on the clean base still leaves label 24 present and
  still returns `expected_rule_ids == {"coverage", "fragmentation"}`. It
  guards against the new keyword's `None` default renumbering the
  supplementary ladder's form, which no existing corpus fixture would catch,
  because the ladder is not a committed case.

**Existing tests to reconcile.** Found by applying the change in memory
(Assumptions, preamble) and reading every test module that iterates the
geometric manifest, `CASE_RECIPE`, the specification's corpus cases, the
catalogue, the traceability matrix, the golden evidence or the corpus sheet,
on 2026-09-30:

Moved literals, each with a dated item-206 comment:

- `tests/test_149_conformance_report.py::test_ac13_conformance_carries_one_row_per_manifest_case_across_both_corpora`:
  L836 `== 17` → `== 18`. L839 `== 13` → `== 14`. Extend the count history
  comment above them.
- `tests/test_151_stage30_validation.py`: L350
  (`test_ac8_case_count_equals_summed_manifest_case_count`) `== 17` →
  `== 18`, and L369
  (`test_ac9_no_unspecified_case_and_matrix_is_fully_conformant`) `== 17` →
  `== 18`. This is a count of cases, not a `progress.md` clause.
- `tests/test_120_leave_one_out_offset.py::test_ac24_corpus_pipeline_detection_is_nine_of_nine`:
  L815 `sum(m.n_cases ...) == 9` → `== 10`. Measured per-mode `n_cases`:
  mode 1: 1, 2: 2, 3: 1, 4: 1, 6: 1, 9: 2, `displaced_vertebra` 1,
  `fov_truncation` 1. Every sensitivity stays 1.0. The name and docstring
  say "nine" and are history; append one dated sentence and do not rename.
- `tests/test_116_ras_native_corpus.py`: `_ITEM_150_NEW_CASES` (L381–383)
  gains `"fuse_separate"`. No pre-migration golden exists for it at the
  reference commit, so `test_ac7_case_identity_preserved_vs_merge_base` must
  not collect it.
- `_ADDED_AFTER*` sets, each gaining `"fuse_separate"` (the tables were
  measured before the case existed):
  - `tests/test_129_coincident_centroids_and_held_out_floor.py` L755 `_ADDED_AFTER_129`;
  - `tests/test_131_tangent_direction_normalisation.py` L318 `_ADDED_AFTER_ITEM`;
  - `tests/test_132_monotonicity_against_traversal_order.py` L225 `_ADDED_AFTER_ITEM`;
  - `tests/test_143_s_axis_correction.py` L291 `_ADDED_AFTER_ITEM`.
- `tests/test_121_tangent_orientation.py`: `_FUSED_BODY_SPAN_EXCLUSIONS`
  (L392) gains `("fuse_separate", 22)`, and the `exceptions` set in
  `test_ac10_principal_axis_exactly_left_right_off_the_named_exceptions`
  (L447) gains `"fuse_separate"`. Label 22 spans two bodies, and its
  principal axis measures `[0.0, 0.2267, 0.9740]`. Labels 20, 21 and 23 are
  exactly L-R. Extend the comment above L392.
- `tests/test_103_feature_catalogue.py`: `_RULE_MODE_MAP["fragmentation"]`
  (L608) `(1, 4)` → `(1, 2, 4)`, with the comment naming `fuse_separate`.
- `tests/test_136_rule_mode_declarations.py::test_ac4_corroborated_modes_are_covered_by_the_measured_corpus_map`:
  `expected_co_detections` (L339–344) gains `("fragmentation", 2)`. Append a
  dated comment after the L334–335 item-176 sentence saying the pair
  re-enters through `fuse_separate`. The item-176 sentence stays as the
  record.
- `tests/test_137_mode_less_rule_disposition.py::test_adv_measured_artifact_movement_counts_from_spec`:
  L942 `mode2_count == 5` → `== 10`. Append a `Re-measured (item 206,
  2026-09-30)` paragraph to the docstring in the shape of item 205's: five
  `components` leaves gain mode 2. `len(entries)` stays 145 and
  `mode1_count` stays 5.
- `tests/test_105_golden_decision_table.py`: L273
  (`test_ac3_current_tree_has_30_non_py_fixtures`) and L713
  (`test_adv_ac3_empty_header_only_table_fails_with_full_missing_list`)
  `25` → `26`, each with a dated comment. The name keeps its old value.
  `tests/test_126_golden_retirement.py`'s
  `test_ac20_test105_inventory_constant_is_current` reads this constant and
  goes green with it, unedited.
- `tests/test_134_decision_table_evidence_companion.py`:
  `_INVENTORY_ADDED_AFTER_126` (L566) gains
  `"tests/corpus/fixtures/fuse_separate_seg.nii.gz"`.

The one structural edit, which the fence is widened for:

- `tests/test_153_eval_harness_rekey.py::test_ac19_ladder_homes_are_derived_from_the_specification`.
  `_rule_b_home` (L117–139) resolves an operator's home through
  `_manifest_case_id_for_perturbation`, which asserts exactly one manifest
  case per operator (L96). The supplementary `fuse` ladder's operator now has
  two cases, `fuse_adjacent` and `fuse_separate`. **Decision:** add a plural
  helper that returns every manifest case id whose `perturbation` is the
  operator, and asserts at least one. `_rule_b_home` collects `mode_hits` and
  `condition_hits` as sets over all of those ids, and keeps both `<= 1`
  asserts. So an operator whose cases sit in two different modes still
  fails, and the claim is not loosened. Both fuse cases are mode 2, so the
  `fuse` ladder's home stays 2. The singular helper stays for its other
  caller (L312, `crop_at_border`). The docstring gains a dated item-206
  sentence.

Red until step 4 regenerates, with no test edit: the fresh-versus-committed
checks over the regenerated artifacts. These are:

- failure_modes: `test_144` AC19/AC20, `test_145` AC23, `test_146`
  (L1270–1290), `test_147` AC24;
- catalogue: `test_103`, `test_106` AC7, `test_123` AC47, `test_136` AC13,
  `test_148` AC14;
- traceability: `test_138` AC4, `test_148` AC18, `test_162` AC9/AC10;
- golden evidence: `test_134`;
- corpus sheet: `test_178` AC7 (the `Source` digest);
- the regenerated set in general: `test_120` AC30, `test_137` AC15, `test_157`
  AC15–AC18.

The Section-1 row and Divergences bullet of step 5 are what
`tests/test_105_golden_decision_table.py`'s AC3 and AC13 and
`tests/test_126_golden_retirement.py`'s AC20 read. Those tests need no edit.

Checked and unaffected (measured or read):

- `tests/test_125_stage28_validation.py` AC15 and
  `tests/test_135_stage29_validation.py` AC25: mode 2 is already in
  `test_057`'s `_PIPELINE_DETECTABLE_MODES`.
- `tests/test_057_acceptance_stage7.py`: sensitivity 10/10; FPR 0;
  calibration feasible.
- `tests/test_195_force_overlap_removed.py`: its fixture-versus-manifest
  symmetric difference stays empty.
- `tests/test_040_synthetic_corpus.py`: the case shares `base_scan`, and
  mode 2 is in `_PIPELINE_ONLY_MODES`.
- `tests/test_094_tptbox_image_layer.py`: the snapshot is not required to
  cover every fixture.

Comments that go stale but assert nothing, left alone:

- `tests/test_190_condition_keyed_eval_bucket.py` ("14 pipeline runs");
- `tests/test_146_ninth_mode_and_first_proposed.py` L874;
- `tests/test_145_eight_hypothesised_modes.py` L831 (a `>= 13` floor).

**`progress.md` count clauses.** None moves (A6). The clauses tests read are
Stage 30 criterion 1 (`tests/test_151_stage30_validation.py` AC35), and Stage
20 criterion 5 and the refined/bar/drafts clause
(`tests/test_169_stage32_validation.py` AC6, AC7, AC8). The derived status,
rung and bar partition were re-measured with the case in place, and each
equals its last attested clause. No `aide progress amend` is needed.

## Validation

1. Regenerate (step 4), then read `docs/aide/failure_modes.generated.md`.
   Mode 2 lists the cases `fuse_adjacent`, `split` and `fuse_separate`, with
   `fuse_separate`'s expected firing `fragmentation`. Mode 2 still reads
   `Status, derived (live): validated`.
2. Open `docs/aide/corpus_sheet.png`. The 14th panel is titled
   `fuse_separate`, `failure / 2`, `fragmentation`. Its sagittal view shows
   L3 and L4 in one colour with the gap between them, and the L5 body in the
   colour L4 has on `clean_control`.
3. Replay the case through the CLI:

   ```
   .venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/fuse_separate_seg.nii.gz --out <tmp> --no-reference
   ```

   `--no-reference` is needed for the reason `CLAUDE.md` gives: the bundled
   VerSe reference is not calibrated for the synthetic corpus. Check that the
   `findings` in `<tmp>/segfacet_report.json` hold exactly one
   `fragmentation` finding, on label 22.

No environment profile is needed.

## Dependencies

- Item 205: re-homed `split` and `neighbour_contact`'s `stray_contact` to
  mode 2, and wrote the mode-2 entry this item extends (✅).
- Item 173: the lordotic base the case is built on (✅).
- Item 176: the bridged `fuse` form whose caudal renumbering the new form
  reuses (✅).

**Downstream:**

- Item 207 adds mode 2's fused-label detector. It fires on `fuse_adjacent` and
  on this item's `fuse_separate`, read by case id (A1), and adds its rule to
  both cases' expected sets. So `fuse_separate`'s `expected_firing`, the
  manifest's `expected_rule_ids` and the operator's `Expectation` move then.
  This item's tests pin none of the three.
- Item 203 re-measures `bar_conditions(2)` for its decision brief after items
  205–208.

## Decisions & Trade-offs

To be updated during implementation.

- **`tests/corpus/094_pre_migration_snapshot.json` is not extended.** Items
  174 and 175 added their fixtures to it, but nothing requires that:
  `tests/test_094_tptbox_image_layer.py`'s coverage check asks only for at
  least ten entries that span both corpora. The snapshot records how the
  pre-TPTBox loader read fixtures that existed before that migration, and
  `fuse_separate` did not. Leaving it alone also leaves
  `tests/test_143_s_axis_correction.py`'s AC19 count and
  `tests/committed_artifact_guard.py`'s float count
  (`tests/test_196_stale_prose.py`) where they are.
- **Left open:** whether `fragmentation`'s co-detection on a mode-2 case
  should reach the catalogue's `failure_modes` column. Today the
  corpus-derived map puts mode 2 on five `components` leaves that no mode-2
  detector reads (A6). That is the existing semantics for every co-detection
  (`coverage` carries mode 6 through `remove_level` the same way), and
  changing it belongs to the catalogue, not to a fixture item.
