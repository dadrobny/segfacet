<!-- aide-template: item 2 -->
# Item 174 — Mode 3's two sub-types: `split` at a 20 % cap, and `split_own_label`

> **Created:** 2026-09-23 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-023.md`](../queue/queue-023.md) · Item 174
> **Objectives:** G2, G7
> **Suggested branch:** `aide/174-mode-3-s-two-sub`

---

## Description

Roadmap Stage 33 D2, first bullet. The maintainer decision is the `gap` entry
in `docs/aide/insights.md` dated 2026-09-22 on mode 3 (split vertebra segment)
and its fixtures. It is read together with the entry of the same date that
sets the split fraction at about 20 % of the body.

Mode 3 has two sub-types:

- **(a)** part of a vertebra carries a neighbouring vertebra's label;
- **(b)** part of a vertebra carries a label of its own.

Today's `split` case expresses neither well. It donates 40 % of L3's S-I
extent to L4, so the receiving label reads as fragmented and `fragmentation`'s
`components` detector (mode 1's) fires beside mode 3's own `neighbour_contact`
detector.

This item authors both sub-types on the lordotic base item 173 built:

- **`split` (sub-type a), re-authored.** A caudal cap of L4 (label 23) is
  relabelled L5 (label 24). The cap is the part of L4 below one S-I cut, and
  holds about 20 % of L4's voxels (A1).
- **`split_own_label` (sub-type b), new operator and new case.** The same cap
  gets its own label, and every label cranial to it shifts up one level. L5
  stays 24, the cap becomes 23 (L4), the rest of L4 becomes 22 (L3), and so on
  up to L1, which becomes 19 (T12).

Both cases are attributed to mode 3. Each case's `expected_firing` is authored
from its measured firing. `split_own_label` fires `coverage` on a "missing"
T13 between T12 and L1. That finding is recorded as a co-detection, and the
next queue's `CANONICAL_ORDER` item (roadmap Stage 33 D3) removes it.

`neighbour_contact`'s 100.0 mm² threshold is re-examined against the contact
areas the lordotic corpus produces (A5). It stays where it is. Every `src/`
quote of the firing contact value is re-measured, including the
`default_config.yaml` comment that item 173 could not reach
(`docs/aide/insights.md`, item 173, 2026-09-23).

**Not in scope.**

- No rule, detector, threshold or `IntendedRule` edge changes. Re-homing
  `neighbour_contact` and the `coverage` T13 fix are D3's.
- No severity-ladder entry for either split operator. That is D4's.
- `MODE_SIGN_OFFS` and mode 3's signed `definition` are not edited.
- No other corpus case changes. The prototype directory is not touched,
  because item 178 deletes it.

## Acceptance Criteria

Unless stated otherwise, "the default base" is
`segfacet.synth.clean_gt.build_clean_spine().seg_img`, and "the stacking axis"
is `segfacet.synth.axes.si_axis(affine)`. Committed fixtures are resolved
through `segfacet.synth.corpus.load_manifest()` and `CORPUS_DIR`, never a
hard-coded path.

- [ ] **AC1: `split`'s cap is everything of the target beyond one S-I cut.**
  Apply `SplitPerturbation(target_label=23, neighbour_label=24, donated_fraction=0.2)`
  to the default base with seed 0. Let D be the voxels that are 23 in the
  input and 24 in the output. D is non-empty. Its stacking-axis indices form
  one contiguous run that contains the target's extreme index on the side of
  the neighbour's mean stacking-axis index. D equals the set of input
  label-23 voxels whose stacking-axis index lies in that run.
- [ ] **AC2: the cap is the smallest whole-slice cap holding at least the
  fraction.** For AC1's D and N = the input's label-23 voxel count:
  `len(D) >= 0.2 * N`, and `len(D)` minus the number of input label-23 voxels
  in D's slice farthest from the neighbour is `< 0.2 * N`.
- [ ] **AC3: the committed `split` fixture gives an L4 part to L5.** Compare
  the committed `split` seg fixture with the committed `clean_control` seg
  fixture. The set of voxels at which they differ is non-empty. It equals the
  set of voxels that are 23 in `clean_control` and 24 in `split`.
- [ ] **AC4: the committed `split_own_label` fixture is the same cap under its
  own label, with the cranial labels shifted.** Build E from the committed
  `clean_control` array. Every voxel of a label l ≤ 23 becomes l − 1. Then
  every voxel of AC3's differing set becomes 23. Everything else is copied.
  The committed `split_own_label` array is `np.array_equal` to E.
- [ ] **AC5: `split_own_label` is deterministic under its seed.**
  `SplitOwnLabelPerturbation()` has no explicit target. Applied twice to the
  default base with seed 3, it returns two results whose label arrays are
  `np.array_equal` and whose `Expectation`s compare equal.
- [ ] **AC6: `split_own_label` is attributed to mode 3.** The committed
  manifest case `split_own_label` has `failure_mode == 3`.
- [ ] **AC7: `split_own_label`'s machine-readable record holds.**
  `segfacet.synth.regression.verify_case` returns `True` for the committed
  `split_own_label` manifest case. It checks, live, that the verdict label
  matches, that the designated rule fires, and that the offending labels
  match.
- [ ] **AC8: `split_own_label` fires `bounds` and `coverage`.**
  Take the `CorpusCaseExpectation` with `case_id == "split_own_label"` from
  `failure_modes.SPECIFICATION[3].corpus_cases`. `set(failure_modes.measured_firing(case))`
  equals `{"bounds", "coverage"}`.
- [ ] **AC9: `split` fires mode 3's own detector alone.** Take the committed
  `split` manifest case. The set of `(rule_id, detector_id)` over
  `segfacet.synth.regression.pipeline_findings(case)` equals
  `{("fragmentation", "neighbour_contact")}`.
- [ ] **AC10: the exercise report records the new operator as used by its
  case.** Take the operator record named `split_own_label` in
  `segfacet.traceability.build_matrix().exercise.operators`. Its `state` is
  `"used"`. Its `cases` equals the sorted tuple of `CASE_RECIPE` case ids whose
  `perturbation == "split_own_label"`, recomputed live, and that tuple is
  non-empty.

These criteria close no stage acceptance criterion. Stage 33's criteria are
closed by D5 and D6.

## Assumptions

- **A1 (defensible default: "about 20 %" is a voxel fraction).** The queue
  says "about 20 % of the body and cut below an S-I level". On the tilted L4
  the two readings differ:
  - Today's `donated_fraction` is a fraction of the stacking-axis span. At 0.2
    it donates 6 of 32 slices and 1 798 voxels, which is 9.3 % of L4.
  - The prototype (`corpus_v2.py::caudal_cap`) cuts at `np.quantile(z, 0.2)`.
    That lands on a slice boundary and takes 3 224 voxels, which is 16.7 %.

  This item redefines `donated_fraction` as a fraction of the target's
  **voxels**. The cap is the smallest number of whole stacking-axis slices,
  counted from the target's neighbour-facing end, whose voxel count is at
  least `donated_fraction × N`. On the default base at 0.2 that is slices
  49–57 of L4's 49–80: 9 slices, 4 030 voxels, 20.83 %. The rule is
  deterministic, it never falls short of the fraction, and it keeps the cut a
  single S-I plane.
  - `donated_fraction` must lie strictly inside (0, 1). Otherwise the operator
    raises `FacetInputError`, so 0.0 no longer silently rounds up to one slice.
  - A cap that would take every slice of the target also raises.
  - The default becomes 0.2.
- **A2 (defensible default: the `split_own_label` operator).** The class is
  `SplitOwnLabelPerturbation`, registered as `"split_own_label"` in
  `synth/component_shape.py` beside `split`. Keyword arguments:
  `target_label: Optional[int] = None` and `donated_fraction: float = 0.2`.
  - **The cap faces caudally.** It faces the next-higher present label, which
    is caudal because ascending labels advance caudally (`clean_gt`). It uses
    the same helper and rule as `split` (A1).
  - **The relabel.** Every present label l ≤ target becomes l − 1, and the cap
    becomes the target. That is the prototype's integer shift. On the lumbar
    base it is the maintainer's anatomical shift, with L1 (20) becoming T12
    (19).
  - **Refusals.** Each of these raises `FacetInputError`: a target absent from
    the map, a target that is the highest present label (no caudal
    neighbour), and a map whose lowest present label is 1 (the shift would
    write background).
  - **Unspecified target.** `_choose_label(labels[:-1], seed)` picks it, so the
    seed decides.
- **A3 (defensible default: the `split_own_label` `Expectation`).**
  `failure_mode=3`, `expected_rule_ids=frozenset({"bounds"})`,
  `expected_labels=frozenset({target})` and
  `expected_verdict="flagged-for-review"`. `bounds` is mode 3's own intended
  rule (a needs-real-data proxy), and it is what fires on the cap. `coverage`
  is left out of `expected_rule_ids`, and is recorded only in the
  specification's `expected_firing`, as a co-detection. Naming it in the
  `Expectation` would add `("coverage", 3)` to the catalogue's corpus map and a
  co-detection pair to `test_136`'s exact partition, both of which D3 then has
  to undo.
  - The `Expectation(...)` call must spell `failure_mode=3` and
    `expected_rule_ids=frozenset({"bounds"})` as literals.
    `catalogue._scan_synth_rule_mode_map` reads them from the AST.
  - Consequence, measured 2026-09-23 by patching the scan: `bounds` gains
    corpus mode 3. Its four signal paths (`per_label.{label}.geometry.physical_volume_mm3`
    and `extent_{x,y,z}_mm`) move from the `("rule_declaration",)` bucket to
    `("rule_mode_map", "rule_declaration")`. The bucket counts go 6 → 2 and
    7 → 11. No entry's `failure_modes` moves. There are still 140 entries,
    and the mode 1/2/3/16 counts are unchanged at 14/15/13/2.
    `catalogue.rule_declaration_conflicts()` stays empty, because `bounds`
    declares mode 3.
- **A4 (measured 2026-09-23, spec-author probe on this branch, not
  committed).** The probe built both cases in memory per A1–A3 on the default
  base, ran them through `run_qc` with `bundled_default_config()`, and built
  reports through `synth.golden.build_report_for_case`.

  | | `split` (23 → 24) | `split_own_label` |
  |---|---|---|
  | verdict | flagged-for-review | flagged-for-review |
  | findings (rule.detector, labels) | `fragmentation.neighbour_contact` [24] | `bounds.metric_out_of_range` [23] ×2, `coverage.missing_interior` [] |
  | cap label | 24: sizes [19344, 4030], fragmentation_index 0.8276 | 23: one component, 4 030 mm³, extent_z 9 mm |
  | donor / rest of L4 | 23: 15 314 mm³, extents 31 / 31 / 23 mm | 22: 15 314 mm³ |
  | `stray_contact_area_mm2` | 806.0 on 24 (against 23), 0.0 elsewhere | 0.0 on every label |
  | missing levels | none | `['T13']` |

  - `bounds` fires twice on the cap: volume 4 030 is below 8 000 mm³, and
    extent_z 9 mm is below 15 mm (lumbar group).
  - `components` does not fire on `split`. The fragmentation index is 0.8276,
    and the detector fires only strictly below 0.75.
  - Every principal axis except `split`'s label 24 is the L-R axis to within
    3.2e-16. Label 24's axis is `[0.0, 0.607, 0.795]`.
  - Interior spline offsets peak at 0.286 mm on `split` and 4.251 mm on
    `split_own_label`. Both are below `test_123`'s ceiling of 5.624555.
  - No report float collides with `tests/report_format_fixture.py`'s
    distinctive literals.

  The builder re-measures every value above.
- **A5 (measured 2026-09-23): the `neighbour_contact` threshold stays at
  100.0 mm².** Across both corpora after this item, the only non-zero
  `stray_contact_area_mm2` is 806.0 mm², on `split`'s label 24. That is
  +706.0 above the threshold, and every other label reads 0.0.
  Sub-type (b) produces no stray component, so this detector cannot see it
  (Left open). Thinner caps on the same body read:
  - 1 slice (31 voxels): contact 31 mm². `islands` fires, not
    `neighbour_contact`.
  - 2 slices: 155 mm².
  - 3 slices: 248 mm².
  - 4 slices: 341 mm².

  So the threshold separates a real cap from a one-slice sliver on this base,
  and no value sits within 100 mm² of it. The re-examination changes prose
  only.
- **A6 (defensible default: the recipe).** The `split` recipe entry's
  `perturbation_params` become
  `{"target_label": 23, "neighbour_label": 24, "donated_fraction": 0.2}`.
  A new entry is appended after it, with `case_id="split_own_label"`,
  `perturbation="split_own_label"`,
  `perturbation_params={"target_label": 23, "donated_fraction": 0.2}` and
  `detection="pipeline"`. The fraction is written explicitly, so the manifest
  records it and a later change of default cannot move a committed fixture.
- **A7 (merged dependencies, read live on `aide/queue-023`, not forward
  pins).**
  - Item 173's `build_clean_spine()` is the lordotic base: shape
    `(61, 86, 193)`, and L4 has 19 344 voxels on stacking-axis slices 49–80.
  - Item 170's session fixtures (`regenerated_failure_modes`,
    `regenerated_traceability`, `aide_check_result`) serve any reconciled test
    that needs a regeneration.
  - Item 171's rule applies to any negative control written here: its "wrong"
    value is derived from live state.
  - Item 172's `traceability.operator_reason_conflicts()` stays empty. No
    operator falls out of use.
- **A8: no human gate, and no environment-gated capability.** Every step runs
  in the plain project venv.

## Implementation Steps

1. **One cap helper in `src/segfacet/synth/component_shape.py`.** Add a private
   `_neighbour_facing_cap(data, target, neighbour, fraction, axis)`. It returns
   the cap mask and its slice range, per A1.
   - The side is chosen the way `SplitPerturbation` chooses it today: by
     comparing the target's and the neighbour's mean stacking-axis index.
   - The cap is counted from that end with `np.bincount` over the target's
     stacking-axis indices and a cumulative sum.
   - Reuse `_label_bbox` and `si_axis`. No dependency is added.
2. **Re-author `SplitPerturbation` on the helper.**
   - The default `donated_fraction` becomes 0.2. Keep the fraction
     validation and the existing adjacency and presence guards.
   - Replace the stale `donated_fraction` comment ("exactly 15.0 mm", item 173's
     Left open) with the measured donor values from A4 and the date.
   - Rewrite the class docstring. The fraction is a voxel fraction of the
     target, and the operator is mode 3 sub-type (a).
   - Rewrite the `Expectation.detail`. Record the requested fraction, the
     donated slice range out of the target's range, and the donated and
     target voxel counts. Do not claim which detectors fire.
   - `expected_rule_ids`, `expected_labels={neighbour}` and the verdict stay as
     they are.
3. **Add `SplitOwnLabelPerturbation`** per A2 and A3, registered with
   `@register_perturbation`. Add it to `__all__` and to the module docstring's
   operator bullets. It reuses `_present_labels`, `_choose_label`,
   `_require_present`, `_new_image` and the step 1 helper.
4. **Update `src/segfacet/synth/corpus.py`** per A6. The module docstring and
   the `CASE_RECIPE` comment say "twelve"; make them "thirteen", naming
   item 174's case.
5. **Regenerate the geometric corpus.** Run `python -m segfacet.synth.corpus`
   twice into two temp directories and diff the bytes before overwriting the
   committed copy. Only `manifest.json`, `split_seg.nii.gz` and the new
   `split_own_label_seg.nii.gz` may differ from the committed tree. Any other
   difference is a hand-back.
6. **Re-capture `tests/corpus/094_pre_migration_snapshot.json`** by item 173's
   step 4 method: a throwaway script that mirrors `test_094`'s reader over both
   manifests, written with `write_bytes`. Do not commit the script.
7. **Author the specification** in `src/segfacet/failure_modes.py`. Use
   `failure_modes.measured_firing` per case.
   - **The `split` case's `reason`.** Re-word it for the 20 % caudal cap of L4
     given to L5. Record `neighbour_contact` alone on label 24 at the fresh
     value. `components` is now silent, with the fresh fragmentation index.
     `expected_firing` stays `("fragmentation",)`.
   - **Append a `split_own_label` `CorpusCaseExpectation`** to mode 3's
     `corpus_cases`, with `corpus="geometric"` and
     `expected_firing=("bounds", "coverage")`. Its `reason` records three
     things. `bounds` fires on the cap's volume and extent_z, as mode 3's own
     needs-real-data proxy. `coverage` fires `missing_interior` on T13 and is a
     co-detection that the next queue's `CANONICAL_ORDER` item removes.
     `neighbour_contact` does not fire, because the cap is its own label's only
     component.
   - **Mode 3's `mechanism`.** Replace the 775.0 / +675.0 / "label 23 against
     label 22" quote with the fresh value, pair and margin. Add one sentence:
     sub-type (b) is seen only by `bounds`, not by this detector.
   - **Hands off.** Do not edit `definition`, `discriminator`, `intended_rules`
     or any `MODE_SIGN_OFFS` note.
8. **Re-measure the other quoted contact values** and update, as prose only:
   - `heuristics/fragmentation.py`: the `DEFAULT_NEIGHBOUR_CONTACT_AREA_MM2`
     docstring.
   - `heuristics/fragmentation.py`: the `mode_declaration` evidence string.
     Update the label pair and the "other fifteen committed corpus cases"
     count, which becomes sixteen.
   - `default_config.yaml`: the comment's 750.0. It is a comment only, so
     `config_hash` reads parsed content and does not move.

   This closes the `defect` entry in `docs/aide/insights.md` (item 173,
   2026-09-23) on that comment. Record that in Decisions, and leave the tick
   to the feedback loop.
9. **Regenerate the derived documents** after step 7. Use each module's `main`
   with the committed `--json`/`--md` paths, twice into temp first:
   - `segfacet.catalogue`, which moves per A3;
   - `segfacet.failure_modes`;
   - `segfacet.traceability`;
   - `segfacet.golden_evidence`.
10. **`docs/aide/golden-decision-table.md`.** Add one Section-1 row for
    `tests/corpus/fixtures/split_own_label_seg.nii.gz`, worded like the
    `split_seg.nii.gz` row, with disposition `keep`. Add the matching
    `## Divergences from the roadmap's working assumption` bullet: "input
    fixture, not a report snapshot (added by item 174, 2026-09-23)". This is the
    item 166 precedent.
11. **Reconcile the existing tests** listed in the Testing Strategy, under the
    fence in Authorised paths. Record each edit in Decisions, by node id, with
    old → new.
12. **Run `python .aide/scripts/aide.py scope 174 --base aide/queue-023`** and
    confirm it exits 0.

## Authorised paths

**May change:**

- `src/segfacet/synth/component_shape.py` — the cap helper, the re-authored `split`, the new `split_own_label` (steps 1–3).
- `src/segfacet/synth/corpus.py` — the recipe entries and the case-count prose (step 4).
- `src/segfacet/failure_modes.py` — mode 3's mechanism, the `split` reason, the new corpus case (step 7).
- `src/segfacet/heuristics/fragmentation.py` — prose only: the re-measured contact quotes (step 8).
- `src/segfacet/default_config.yaml` — comment only: the re-measured contact quote (step 8).
- `tests/corpus/manifest.json` — regenerated (step 5).
- `tests/corpus/fixtures/split_seg.nii.gz` — regenerated (step 5).
- `tests/corpus/fixtures/split_own_label_seg.nii.gz` — **new** fixture (step 5).
- `tests/corpus/094_pre_migration_snapshot.json` — re-captured (step 6).
- `docs/aide/feature_catalogue.generated.json` — `bounds`' paths gain `rule_mode_map` evidence (A3).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `docs/aide/failure_modes.generated.json` — mode 3's new case and prose.
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — conformance, exercise and attribution gain the case.
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/golden_evidence.generated.json` — one row per corpus case.
- `docs/aide/golden-decision-table.md` — the new fixture's Section-1 row and divergences bullet (step 10).
- `tests/test_174_split_sub_types.py` — **new**: this item's test module.
- `tests/test_057_acceptance_stage7.py` — reconciliation (a): overall sensitivity.
- `tests/test_103_feature_catalogue.py` — reconciliation (a): `_RULE_MODE_MAP`.
- `tests/test_105_golden_decision_table.py` — reconciliation (a): fixture inventory count.
- `tests/test_116_ras_native_corpus.py` — reconciliation (a): post-item case set.
- `tests/test_120_leave_one_out_offset.py` — reconciliation (a): AC24 totals.
- `tests/test_121_tangent_orientation.py` — reconciliation (a): principal-axis exclusion.
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — reconciliation (a): post-item case set.
- `tests/test_131_tangent_direction_normalisation.py` — reconciliation (a): post-item case set.
- `tests/test_132_monotonicity_against_traversal_order.py` — reconciliation (a): post-item case set.
- `tests/test_134_decision_table_evidence_companion.py` — reconciliation (a): fixture inventory.
- `tests/test_137_mode_less_rule_disposition.py` — reconciliation (a): evidence-bucket counts.
- `tests/test_138_traceability_matrix.py` — reconciliation (a): the dated attribution witness.
- `tests/test_143_s_axis_correction.py` — reconciliation (a): post-item case set and snapshot count.
- `tests/test_149_conformance_report.py` — reconciliation (a): case counts.
- `tests/test_151_stage30_validation.py` — reconciliation (a): case counts.
- `tests/test_162_corpus_exercise_report.py` — reconciliation (b): the unexercised-rule fixture.
- `tests/test_166_split_operator.py` — reconciliation (a) and (b): donor label and docstrings.
- `tests/test_167_mode_3_detector.py` — reconciliation (a) and (b): label pair, contact value, detector inputs.
- `tests/test_123_recalibrate_and_regenerate.py` — conditional only: A4 measures no move of the interior ceiling.

**The reconciliation fence.** It applies to the listed `tests/test_*.py` files
other than this item's own module. The builder does the reconciliation, after
regeneration, because every new value comes from the regenerated corpus. Two
kinds of change are allowed:

- **(a) A moved literal.** A literal expected value, count or case/fixture set
  that this item's corpus change moved is updated to the fresh measurement.
  The assertion keeps its shape and its tolerance, and gains a dated
  item-174 comment. Prose that quotes the literal follows it.
- **(b) A re-derived premise.** A constructed input or selection whose stated
  premise this item falsified is re-derived. The test keeps what it asserts.
  The three instances are named in the Testing Strategy.

No test is retired, renamed, skipped, `xfail`-marked or loosened in tolerance.
Following item 173's precedent, a test whose name records an old value
(`..._nine_of_ten...`, `..._covers_all_15_...`, `..._has_30_...`) keeps its
name, and its literal carries the dated comment. A red test in a file not
listed here is a hand-back to spec-author, not an edit.

**Asserts against:**

- `src/segfacet/heuristics/bounds.py` — AC7 and the `split`-donor case read `DEFAULT_BOUNDS` and the rule live; this item changes neither.

Some paths are left off **May change** on purpose, so `aide scope` refuses
them. The traceability module and the ratchet's test module are two of them:
the queue's claim is that the ratchet and the exercise report pick up the new
case and operator without being edited, and keeping both out of this diff is
how that claim is proven. The `.gitattributes` file is another: its existing
`tests/corpus/fixtures/*.nii.gz binary` and `text eol=lf` pins already cover
every path regenerated here (the manifest, the 094 snapshot and the four
`docs/aide/*.generated.*` families). Every other operator module, the
heuristics' logic and the prototype directory stay out too.

## Testing Strategy

**The new module is `tests/test_174_split_sub_types.py`**, with one test per
AC (AC1–AC10).

- Committed fixtures are loaded with `nib.load` from the manifest's
  `seg_fixture` under `CORPUS_DIR`.
- AC1 and AC2 recompute the cap from the input array themselves. They never
  read the helper under test.
- AC4 builds E with plain NumPy from the two committed arrays.
- AC10 reads `build_matrix()` once through a module-scoped fixture. It is the
  only `build_matrix()` call in the module.

The queue's other *Testable* claims are already enforced by existing tests
that iterate the live manifest. They pick up the new case with no edit:

- **The corpus regenerates byte-identically.**
  `tests/test_040_synthetic_corpus.py` AC15/AC16,
  `tests/test_116_ras_native_corpus.py` AC10/AC11 and
  `tests/test_143_s_axis_correction.py` AC11–AC13 cover it.
- **The ratchet picks up the case.**
  `tests/test_163_specificity_ratchet.py::test_ac2_ratchet_measured_equals_expected[geometric-split_own_label]`
  appears by parametrisation.
- **`split` stays deterministic under its seed.**
  `tests/test_166_split_operator.py::test_ac4_operator_deterministic_under_seed`
  still holds.

Adversarial cases, each written once:

- **`cap-faces-a-cranial-neighbour`**: apply
  `SplitPerturbation(target_label=23, neighbour_label=22, donated_fraction=0.2)`
  to the default base. The donated voxels' stacking-axis indices include L4's
  index nearest label 22's mean. The cap is the smallest whole-slice run from
  that end holding at least 20 % of L4. This guards a cumulative count taken
  from the low end whatever side the neighbour is on. AC1 and AC2 only
  exercise a caudal neighbour.
  - **Clarification (2026-09-23, after the builder's contradiction hand-back;
    the case above stands).** The case is side-agnostic and correct. A test
    that asserted label 22 sits at the *low* end of the stacking axis
    contradicted it, and that test is what gets re-derived. On the default
    base (item 143's S-axis correction, item 173's lordotic base) the stacking
    axis is array axis 2, and **its index decreases caudally**. Measured on
    this branch: L5 (24) spans 15–48 (mean 31.43), L4 (23) spans 49–80
    (mean 64.41) and L3 (22) spans 84–111 (mean 97.40). So AC1/AC2's caudal
    neighbour exercises L4's **low** end (slices 49–57), and "a cumulative
    count taken from the low end" is exactly the defect: such a helper passes
    AC1/AC2 and fails here. This case exercises the **high** end. The test
    must assert, each recomputed from the input array and never from a literal:
    `neighbour_mean > target_mean`; `max(donated) == ` the target's max
    stacking-axis index; the donated indices are one contiguous run; the
    donated set equals the input label-23 voxels on that run;
    `len(D) >= 0.2 * N`; and, with the slice farthest from the neighbour being
    `min(donated)`, `len(D)` minus that slice's label-23 count is `< 0.2 * N`.
    Measured for reference only (not to be pinned): slices 72–80, 3 875 of
    19 344 voxels (20.03 %), and 3 069 without slice 72.
- **`own-label-non-mutating`**: after `SplitOwnLabelPerturbation(target_label=23).apply(base, 0)`,
  the input array is `np.array_equal` to a copy taken before. This guards a
  mutating operator, which would corrupt the shared base that `build_corpus`
  reuses for every later recipe entry.
- **`own-label-top-label-refused`**: `SplitOwnLabelPerturbation(target_label=24)`
  on the default base raises `FacetInputError`. This guards a cap cut toward a
  neighbour that does not exist, which would take the wrong end or crash on an
  empty neighbour.
- **`own-label-shift-to-background-refused`**: `SplitOwnLabelPerturbation(target_label=2)`
  on `build_clean_spine(levels=("C1", "C2", "C3")).seg_img` (labels 1, 2, 3)
  raises `FacetInputError`. This guards the shift writing label 1's voxels as
  0, which silently deletes a vertebra.
- **`own-label-absent-target-refused`**: `SplitOwnLabelPerturbation(target_label=999)`
  raises `FacetInputError`. This guards a silent fallback to the seeded
  choice, which would make a committed fixture depend on the seed rather than
  the recipe.
- **`own-label-degenerate-fraction-refused`**: parametrised over
  `donated_fraction` 0.0 and 1.0, each raising `FacetInputError`. This guards
  an identity fixture at 0.0 (the at-least rule would otherwise round up to a
  one-slice cap) and a cap that consumes the whole target at 1.0.

**Existing tests to reconcile.** This is the stale-assumption sweep, and every
entry was checked against this tree on 2026-09-23. Each file is under **May
change**, and the clause is named.

**Red without the edit:**

1. `tests/test_167_mode_3_detector.py`:
   - (a) AC1: label 23 → 24 in both the recomputation and
     `compute_components`, and `775.0` → the fresh value (806.0 measured).
   - (a) AC2: 23 → 24, with the claiming label 22 → 23.
   - (a) AC3: `{("geometric", "split", 24)}`.
   - (a) AC6: `frozenset({24})`.
   - (b) AC8: select mode 3's case by `case_id == "split"` instead of
     asserting `len(cases) == 1`, because mode 3 now carries two cases. The
     `("fragmentation",)` assertion stays.
   - (b) `test_existing_detectors_unchanged`: the committed 20 % split no
     longer fires `components`. The test's subject is that item 167 left the
     `components` and `islands` detectors unchanged. Show it on an in-memory
     `SplitPerturbation(target_label=23, neighbour_label=24, donated_fraction=0.4).apply(build_clean_spine().seg_img, 0)`,
     run through `run_qc` with `bundled_default_config()`. Measured: one
     `components` finding on 24 and no `islands`.
2. `tests/test_121_tangent_orientation.py` (a):
   `_FUSED_BODY_SPAN_EXCLUSIONS` has `("split", 23)` → `("split", 24)`,
   because label 24 is now the one spanning two bodies (A4). The comment and
   docstring move with it.
3. `tests/test_162_corpus_exercise_report.py` (b):
   `matrix_demonstrable_rule_unexercised` and
   `test_demonstrable_rule_unexercised_is_a_hole` swap `"bounds"` for
   `"reference_delta"`. `bounds` is now exercised by `split_own_label`.
   `reference_delta` stays unexercised, named only at needs-real-data, and
   carries a mode-1 edge. The fixture's docstring says why.
4. `tests/test_138_traceability_matrix.py` (a): in
   `test_ac20_analytic_edges_equal_edges_the_specification_never_designates_corpus`,
   the dated `witness` loses `(3, "bounds")`, and `mixed == set()` becomes
   `mixed == {"bounds"}`. `bounds` is now corpus-attributed for mode 3 and
   analytic for 1, 2 and 4. The dated comment records the move.
5. `tests/test_137_mode_less_rule_disposition.py` (a): the distribution table
   has `("rule_declaration",)` 6 → 2 and `("rule_mode_map", "rule_declaration")`
   7 → 11 (A3). Totals and mode counts are unchanged.
6. `tests/test_103_feature_catalogue.py` (a): `_RULE_MODE_MAP` gains
   `"bounds": (3,)` with a `split_own_label (3)` comment.
7. `tests/test_116_ras_native_corpus.py`, `tests/test_129_coincident_centroids_and_held_out_floor.py`,
   `tests/test_131_tangent_direction_normalisation.py`,
   `tests/test_132_monotonicity_against_traversal_order.py` and
   `tests/test_143_s_axis_correction.py` (a): each pins, as an exact set,
   which cases its pre-item table does not cover. Add `"split_own_label"` to
   each. Do not extend the tables.
8. `tests/test_143_s_axis_correction.py` (a): AC19's `len(snapshot) == 15`
   becomes 16, after step 6.
9. `tests/test_149_conformance_report.py` (a): `len(cases) == 16` → 17, and
   the geometric `== 12` → 13.
10. `tests/test_151_stage30_validation.py` (a): `len(keys) == 16` and
    `agree_count == 16` → 17.
11. `tests/test_057_acceptance_stage7.py` (a):
    `test_overall_corpus_sensitivity_is_nine_of_ten_not_over_claimed` asserts
    `9/10` → `10/11`. `split_own_label` is an eleventh expected-failure record
    and is caught. Its docstring gains a history line. Its name, which
    `test_132` calls, is kept.
12. `tests/test_120_leave_one_out_offset.py` (a): AC24's
    `metrics.sensitivity` goes 9/10 → 10/11 and `sum(n_cases) == 10` → 11. The
    per-mode dict is unchanged, since mode 3 stays at 1.0 over two cases.
13. `tests/test_105_golden_decision_table.py` (a): both `== 23` → 24
    (`test_ac3_current_tree_has_30_non_py_fixtures` and the empty-table
    adversarial). Its Section-1 and divergences checks are satisfied by
    step 10.
14. `tests/test_134_decision_table_evidence_companion.py` (a):
    `_INVENTORY_ADDED_AFTER_126` gains
    `tests/corpus/fixtures/split_own_label_seg.nii.gz`, and its comment names
    item 174.

**Stale but not red, reconciled anyway:**

15. `tests/test_166_split_operator.py`:
    - (b) `test_bounds_stays_silent_on_the_donor` reads the donor label from
      the committed `split` case's `perturbation_params["target_label"]`
      instead of the literal 22. Otherwise it would pass vacuously on the
      untouched L3. The docstring drops the 0.4/0.5 narrative for the 20 %
      cap. Measured donor: 15 314 mm³, extents 31/31/23 mm, inside the lumbar
      range.
    - (a) `test_expected_labels_equal_the_fired_labels`' docstring changes
      `{23}` → `{24}`.

**Conditional:**

16. `tests/test_123_recalibrate_and_regenerate.py`: AC45's interior ceiling of
    5.624555 is predicted not to move, because the new interior offsets peak
    at 4.251 mm (A4). It is declared only so a surprise is a fence edit and
    not a scope violation.

**Covered automatically, no edit.** A full run confirms each of these:

- `test_040`, `test_041`, `test_042`, `test_155` and `test_157`: they iterate
  the manifest, and `split_own_label` has no `modeN_` prefix.
- `test_094`: it reads the re-captured snapshot.
- `test_098` and `test_102`: their snapshots are keyed by the old cases only.
- `test_099`: its per-case parametrised tests expect no border finding, no
  out-of-order label and no overlap on the new case, and A4 measured none.
- `test_126`: A4 found no float collision.
- `test_136`: `("bounds", 3)` is declared, so it is not a co-detection.
- `test_145` and `test_163`.
- `test_164` and `test_165`: neither pins the corpus-wide detector set.

**Sibling note.** Items 175–177 regenerate the same manifest, the 094 snapshot
and the generated documents, and several of them move the same count
literals (entries 8–14). Whichever lands later re-measures on top of the
earlier. None of them asserts against a path listed here.

## Validation

1. Run `python -m segfacet.synth.corpus --out <tmp>` and diff `<tmp>` against
   `tests/corpus/`. Confirm there is no difference.
2. Run
   `.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/split_seg.nii.gz --no-reference --out <tmp>`,
   and the same for `split_own_label_seg.nii.gz`. `--no-reference` is required
   (see the CLAUDE.md gotcha). Expect `flagged-for-review` in both runs:
   - `split`: exactly one finding, `Neighbour contact:` on label 24.
   - `split_own_label`: two `bounds` findings on label 23 and the `coverage`
     T13 finding.
3. Print the regenerated `split` case's `stray_contact_area_mm2` for label 24.
   Confirm it is the value quoted in these places:
   - `docs/aide/failure_modes.generated.md`: mode 3's mechanism and the `split`
     row;
   - `docs/aide/traceability_matrix.generated.md`: the `fragmentation`
     declaration evidence;
   - `src/segfacet/default_config.yaml`'s comment.
4. Run `python .aide/scripts/aide.py scope 174 --base aide/queue-023` and
   confirm it exits 0.
5. Run `.venv/bin/python -m pytest --collect-only -q` on this branch and on
   `aide/queue-023`. The branch's collected test-id set must equal the base's
   set plus this item's new tests plus the parametrised ids whose parameter is
   the new case or its fixture. An example is
   `test_163_specificity_ratchet.py::test_ac2_ratchet_measured_equals_expected[geometric-split_own_label]`.
   Nothing is removed or renamed.

No `[validation]` profile is needed, so there is no ❓ Unverified downgrade
path.

## Dependencies

Item 173 (merged into `aide/queue-023`), the lordotic base both cases are cut
from. Items 170, 171 and 172 are also merged (A7).

**Downstream:** item 178 renders both cases. The next queue's
`CANONICAL_ORDER` item (roadmap Stage 33 D3) removes `coverage` from
`split_own_label`'s measured firing. Its spec must re-author AC8's set and
list `tests/test_174_split_sub_types.py` under May change. D4 re-measures the
severity ladder, covering both split operators. D5's gate reads mode 3's
rendering and the corpus sheet.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** which detector serves sub-type (b). `neighbour_contact` cannot
  see an own-label cap, because the cap is its label's only component (A5).
  Today only `bounds` fires on it, and `bounds` is a needs-real-data proxy
  that `PROXY_RULE_IDS` keeps out of bar condition 4. Whether mode 3 at the
  bar needs a sub-type (b) signal, such as the inter-centroid spacing the
  mode-6 insight proposes, is D3/D5's question and not this fixture item's.
- **Left open:** the `bounds → mode 3` edge's `evidence_rung`. It stays
  `needs-real-data`, although `bounds` now fires on a synthetic mode-3 case.
  Re-grading an edge is a specification decision that belongs with D3's rule
  re-homing and D4's bar checker. It is not a side effect of adding a
  fixture.
- **Left open:** `split_own_label` on non-contiguous label numbering. The
  shift is an integer −1 (A2), which is the anatomical shift for labels 2–24
  but not across the T13 (28) or L6 (25) slots. The committed case is lumbar,
  so the question waits for a corpus that needs it.

### Implementation (builder, 2026-09-23)

- **Measured values.** Every A4 and A5 value was re-measured on this branch
  and matches the spec exactly:
  - The `split` cap is L4's slices 49–57 of 49–80, 4 030 of 19 344 voxels.
  - Label 24's `stray_contact_area_mm2` is 806.0 against label 23, and its
    fragmentation index is 0.8276. The donor keeps 15 314 mm³ with extents
    31/31/23 mm.
  - `split` fires only `fragmentation.neighbour_contact` [24].
    `split_own_label` fires `bounds.metric_out_of_range` [23] ×2 (4 030 mm³,
    extent_z 9 mm) and `coverage.missing_interior` (T13).
  - Thinner caps read 31 mm² (islands), 155, 248 and 341 mm². The intensity
    corpus has no stray contact.
  - The catalogue moves exactly per A3: `bounds`' four paths gain
    `rule_mode_map` evidence, and the catalogue `.md` is byte-unchanged.
- **Fraction validation lives in the cap helper.** `_neighbour_facing_cap`
  raises `FacetInputError` for a fraction outside (0, 1) and for a cap that
  would take every slice. `split` and `split_own_label` therefore refuse
  degenerate fractions identically.
- **`split_own_label` shift.** It reads the input array and writes a copy,
  so the operator never mutates its input. `shift = (data != 0) & (data <= target)`
  keeps background at 0.
- **094 snapshot key set.** The committed snapshot never covered
  `fuse_adjacent`, `remove_level_relabel` or `split`: it held 15 keys, the
  pre-item-150 fixtures. The re-capture kept exactly those 15 keys, and
  their digests were unchanged. It added only
  `corpus/fixtures/split_own_label_seg.nii.gz|seg`, giving the 16 entries
  that reconciliation entry 8 names. A full re-capture of both manifests
  would give 19 keys and contradict that entry.
- **Closes the item-173 `default_config.yaml` insight.** The
  `default_config.yaml` comment's 750.0 now reads 806.0 (split, label 24
  against 23). This closes the `defect` entry in `docs/aide/insights.md`
  (item 173, 2026-09-23). The tick is left to the feedback loop.
- **Test reconciliation (step 11).** Each edit carries a dated item-174
  comment. Values are shown as old → new.
  - Clause (a), moved literals:
    - `test_167_mode_3_detector.py`:
      - `::test_ac1_feature_measures_the_split`: label 23 → 24 in the
        recomputation and in `compute_components`, and 775.0 → 806.0.
      - `::test_ac2_feature_names_the_claiming_label`: 23 → 24, and the
        claiming label 22 → 23.
      - `::test_ac3_silent_everywhere_else_in_both_corpora`:
        `("geometric", "split", 23)` → `24`.
      - `::test_ac6_detector_fires_on_the_split_case`: `frozenset({23})` →
        `frozenset({24})`.
    - `test_121_tangent_orientation.py::_FUSED_BODY_SPAN_EXCLUSIONS`:
      `("split", 23)` → `("split", 24)`. The comment and the sibling
      docstring follow.
    - `test_138_traceability_matrix.py::test_ac20_analytic_edges_equal_edges_the_specification_never_designates_corpus`:
      the witness loses `(3, "bounds")`, and `mixed == set()` →
      `mixed == {"bounds"}`.
    - `test_137_mode_less_rule_disposition.py::test_adv_measured_artifact_movement_counts_from_spec`:
      `("rule_declaration",)` 6 → 2, and `("rule_mode_map", "rule_declaration")`
      7 → 11.
    - `test_103_feature_catalogue.py::_RULE_MODE_MAP`: gains
      `"bounds": (3,)`.
    - `"split_own_label"` is added to the pinned post-item case sets in five
      files:
      - `test_116_ras_native_corpus.py::_ITEM_150_NEW_CASES`
      - `test_129_…::_ADDED_AFTER_129`
      - `test_131_…::_ADDED_AFTER_ITEM`
      - `test_132_…::_ADDED_AFTER_ITEM`
      - `test_143_…::_ADDED_AFTER_ITEM`

      No pre-item table was extended.
    - `test_143_s_axis_correction.py::test_ac19_snapshot_covers_all_15_entries_across_both_corpora`:
      15 → 16.
    - `test_149_conformance_report.py::test_ac13_…`: `len(cases)` 16 → 17,
      and geometric 12 → 13.
    - `test_151_stage30_validation.py`:
      - `::test_ac8_case_count_equals_summed_manifest_case_count`: 16 → 17.
      - `::test_ac9_no_unspecified_case_and_matrix_is_fully_conformant`:
        `agree_count` 16 → 17.
      - `::test_ac14_recorded_analytic_edge_list`: `(3, "bounds")` removed
        from the expected analytic list. The Testing Strategy's entry 10 did
        not name this test. It is in a listed file, and it is the same moved
        literal as the test_138 witness (entry 4), so clause (a) covers it.
    - `test_057_acceptance_stage7.py::test_overall_corpus_sensitivity_is_nine_of_ten_not_over_claimed`:
      9/10 → 10/11, with a docstring history line. The name is kept.
    - `test_120_leave_one_out_offset.py::test_ac24_corpus_pipeline_detection_is_nine_of_ten`:
      sensitivity 9/10 → 10/11, and `sum(n_cases)` 10 → 11. The per-mode
      dict is unchanged.
    - `test_105_golden_decision_table.py`:
      - `::test_ac3_current_tree_has_30_non_py_fixtures`: 23 → 24.
      - `::test_adv_ac3_empty_header_only_table_fails_with_full_missing_list`:
        23 → 24.
    - `test_134_decision_table_evidence_companion.py::_INVENTORY_ADDED_AFTER_126`:
      gains `tests/corpus/fixtures/split_own_label_seg.nii.gz`.
    - `test_166_split_operator.py::test_expected_labels_equal_the_fired_labels`:
      the docstring's `{23}` → `{24}`.
  - Clause (b), re-derived premises:
    1. `test_167_mode_3_detector.py::test_ac8_split_case_expected_firing_unmoved`
       selects mode 3's case by `case_id == "split"` instead of asserting
       `len(cases) == 1`. The `("fragmentation",)` assertion stays.
    2. `test_167_mode_3_detector.py::test_existing_detectors_unchanged` runs
       on an in-memory `SplitPerturbation(target_label=23, neighbour_label=24, donated_fraction=0.4)`
       of `build_clean_spine().seg_img` through `run_qc` with
       `bundled_default_config()`. As measured, it gives one `components`
       finding and no `islands` finding.
    3. `test_162_corpus_exercise_report.py::matrix_demonstrable_rule_unexercised`
       and `::test_demonstrable_rule_unexercised_is_a_hole` use
       `"reference_delta"` instead of `"bounds"`, because `bounds` is now
       exercised by `split_own_label`.

    Also re-derived: `test_166_split_operator.py::test_bounds_stays_silent_on_the_donor`
    reads the donor label from the committed case's
    `perturbation_params["target_label"]` instead of the literal 22.
  - `test_123_recalibrate_and_regenerate.py` needed no edit. AC45's interior
    ceiling did not move.
  - `tests/test_174_split_sub_types.py`, `traceability.py` and `test_163`
    are untouched.
