<!-- aide-template: item 2 -->
# Item 176 — `fuse_adjacent` bridged and renumbered

> **Created:** 2026-09-24 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-023.md`](../queue/queue-023.md) · Item 176
> **Objectives:** G2, G7
> **Suggested branch:** `aide/176-fuse-adjacent-bridged-and-renumbered`

---

## Description

This item implements roadmap Stage 33 D2's third bullet. It rests on two
`docs/aide/insights.md` entries dated 2026-09-22 (queue-022 review): the
maintainer decision on `fuse_adjacent`, and the fused-case entry measuring the
bridged form on the prototype.

Today the committed case `fuse_adjacent` applies `fuse(target_label=22,
neighbour_label=23)`: every L4 (23) voxel is relabelled L3 (22) and the disc gap
between them is left empty. Label 22 is then two disconnected bodies, and the
label sequence has a hole at 23. So the case fires `fragmentation` and
`coverage`, and neither rule reads a fused vertebra. The maintainer's
definition is different: a fused vertebra segment is **one connected label over
two bodies, with the caudal labels renumbered so the sequence stays
continuous**.

**What this item changes: the case, in place.**

- **Operator.** `FusePerturbation` (`"fuse"`, in
  `src/segfacet/synth/component_shape.py`) gains a keyword
  `bridged: bool = False`. With `bridged=True` it:
  1. fills the gap between the pair with the target label, column by column
     along the stacking axis;
  2. relabels the neighbour onto the target;
  3. renumbers every label caudal to the neighbour one position up.

  The default (`bridged=False`) is today's unbridged absorb, byte for byte.
  The supplementary severity ladder still applies that form (Assumptions, A2).
- **Case.** `fuse_adjacent` keeps its id, its position in the recipe, and its
  attribution to mode 2 (kind `failure`). Its recipe passes `"bridged": True`.
- **Expected set.** The case fires nothing under the shipped rules. Its
  expectation records that honestly: no rule, verdict `pass`. Mode 2's own
  signal is the inter-centroid spacing, which no shipped rule reads. That rule
  belongs to a later per-mode queue (roadmap Stage 33, "Scope decisions").

**Consequences this item carries, all measured (A3):**

- **Specification (`src/segfacet/failure_modes.py`).** Mode 2's `fuse_adjacent`
  `expected_firing` becomes `()` and gets a rewritten `reason`. Mode 2's
  `mechanism` is rewritten. One clause of mode 3's `mechanism` is corrected.
- **Corpus-derived rule→mode map.** It no longer attributes mode 2 to
  `coverage` or `fragmentation`. The feature catalogue regenerates, and eight
  paths lose mode 2 (A6).
- **Corpus evaluation cohort.** The case becomes a TRUE_NEGATIVE (an
  expected-`pass` case). Sensitivity goes from 11/12 to 10/11, and mode 2 has
  no expected-failure case left.

**Not in scope.**

- No rule, detector, threshold, rule declaration or `IntendedRule` edge
  changes. Mode 2's spacing rule is a later per-mode queue's (roadmap Stage 33).
  Re-homing `coverage` and `fragmentation` is D3's.
- `src/segfacet/eval/severity_ladder.py` is untouched. Its `fuse` ladder keeps
  the unbridged default, and D4 re-measures the ladders.
- No `UNUSED_OPERATOR_REASONS` entry: `fuse` stays used by the recipe.
- No new corpus case, and no case-count literal moves.
- The prototype directory is not touched. Item 178 deletes it.

## Acceptance Criteria

Terms used below:

- **"The default base"** is `segfacet.synth.clean_gt.build_clean_spine().seg_img`.
- **"The bridged operator"** is
  `FusePerturbation(target_label=22, neighbour_label=23, bridged=True)`, applied
  with seed 0.
- **Stacking axis.** `segfacet.synth.axes.si_axis(img.affine)`. A **column** is
  the 1-D line of voxels along that axis at a fixed pair of other indices. On
  the default base it is array axis 2, and its index **decreases caudally**: L3
  (22) lies on slices 84–111, L4 (23) on 49–80 and L5 (24) on 15–48. No test
  assumes that direction. A test that needs "which end" orders the two labels by
  their mean index on the axis.
- **Committed fixtures** are resolved through
  `segfacet.synth.corpus.load_manifest()` and loaded with
  `segfacet.synth.regression.loaded_seg_image`, never by a hard-coded path.

- [ ] **AC1: the fused label is one component.** In the bridged operator's
  output on the default base, `scipy.ndimage.label(out == 22)` (default
  structure, face connectivity) returns exactly 1 component.
- [ ] **AC2: the fused label covers both bodies.** Every voxel whose input value
  is 22 or 23 has output value 22.
- [ ] **AC3: the bridge stays inside the gap.** Every voxel that is 0 in the
  input and non-zero in the output has output value 22. Each one lies in a
  column holding both input labels 22 and 23, strictly between the nearest
  label-23 voxel and the nearest label-22 voxel of that column.
- [ ] **AC4: the bridge fills the gap.** In every column holding both input
  labels 22 and 23, every input-background voxel strictly between the two
  labels' facing ends has output value 22.
- [ ] **AC5: the caudal label is renumbered.** The output's label-23 mask equals
  the input's label-24 mask.
- [ ] **AC6: the cranial labels are unchanged.** For each input label below 22
  (derived live from the input), the output's mask for that label equals the
  input's.
- [ ] **AC7: the committed fixture is the operator's output.** The committed
  `fuse_adjacent` seg array equals the bridged operator's output array when it is
  applied to the committed `clean_control` seg image.
- [ ] **AC8: the committed fixture's labels are a continuous run.** For `s`, the
  sorted non-zero values of the committed `fuse_adjacent` seg,
  `s == list(range(s[0], s[0] + len(s)))`.
- [ ] **AC9: the pipeline measures one component.** On the committed fixture,
  `extract_feature_record(loaded_seg_image(case), bundled_default_config())["per_label"]["22"]["components"]["component_count"] == 1`.
- [ ] **AC10: nothing fires.** For `c`, the `fuse_adjacent` entry of
  `failure_modes.SPECIFICATION[2].corpus_cases`,
  `failure_modes.measured_firing(c) == ()`.
- [ ] **AC11: the authored expected set equals the measured firing.** For the
  same `c`, `c.expected_firing == failure_modes.measured_firing(c)`.

These criteria close no stage acceptance criterion. Stage 33's criterion 2 is
attested by D6.

## Assumptions

- **A1 (defensible default: the case changes in place, not a new case).** Item
  175 avoided test churn by adding a case. That trade-off was weighed here and
  rejected, for four reasons:
  - The queue line, roadmap D2 and the 2026-09-22 maintainer decision all name
    `fuse_adjacent` itself for re-authoring.
  - Stage 33's acceptance criterion 2 forbids any committed case attributed to
    a mode its label map does not express. The review named the unbridged
    `fuse_adjacent` as exactly such a case, so keeping it under mode 2 beside a
    new case is not open.
  - Its two firings lose nothing. `coverage.missing_interior` stays exercised
    by `remove_level` and `split_own_label`, and `fragmentation.components` by
    `fragment` (measured, A3).
  - In place moves no case-count literal, so the count-literal reconciliation
    items 174/175 paid does not recur. What moves is listed in the Testing
    Strategy.
- **A2 (defensible default: a keyword on `fuse`, not a new operator).**
  `FusePerturbation.__init__` gains `bridged: bool = False`.
  - **Why the default stays unbridged.** `eval/severity_ladder.py`'s
    `_fuse_ladder` applies `fuse` cumulatively: (20, 21), then (20, 22), then
    (20, 23). Its metric is `min_dominant_component_fraction`.
    - A renumbering default would make its second step non-adjacent, and the
      operator would refuse it.
    - A bridged default would flatten the metric at 1.0.

    The ladder is D4's, so the default stays byte-identical.
  - **Why not a new operator.** A new registered operator (for example
    `fuse_bridged`) was rejected. It would leave `fuse` used only by the ladder,
    which needs a first `UNUSED_OPERATOR_REASONS` entry and moves the
    traceability exercise report's operator records. It would break item 157's
    "a case id names its operator". And it would still hit the designation
    problem below.
  - **The bridged form, in order, on a private copy of the input:**
    1. Resolve `axis = si_axis(affine)`. The neighbour is caudal of the target
       when its mean index on the axis is on the caudal side of the target's.
       This is the same mean-index comparison `_neighbour_facing_cap` uses.
    2. For every column holding both labels, set to the target every
       **background** voxel strictly between the neighbour's end nearest the
       target and the target's end nearest the neighbour. A non-zero voxel of
       any label is never overwritten.
    3. Relabel the neighbour's voxels as the target.
    4. Renumber each present label greater than the neighbour to the value of
       the present label before it in sorted order. With `labels > neighbour`
       as `caudal`, that is `zip(caudal, [neighbour] + caudal[:-1])`, the
       positional idiom of `RemoveLevelRelabelPerturbation`. Apply it
       cranial-most first, reading from the original array so no relabel
       collides.
  - **Refusals, each raising `FacetInputError`:** the existing refusals (fewer
    than two labels, one of the pair given without the other, a label absent, a
    non-adjacent pair). Plus, only when `bridged=True`: a neighbour that is not
    the next-higher present label than the target. That refusal keeps step 4
    from renumbering into the target. The seeded path
    (`_choose_adjacent_pair`) always returns the lower label as target and
    satisfies it.
  - **The `Expectation`, and why it is branch-computed.**
    `catalogue._scan_synth_rule_mode_map` reads every literal
    `Expectation(failure_mode=<int>, expected_rule_ids=frozenset({...}))` in
    `src/segfacet/synth/*.py`. `catalogue.rule_declaration_conflicts` excuses
    a scanned (rule, mode) pair only while the specification records the rule
    in that mode's case `expected_firing`.
    - Measured: keeping today's literal (2 → `coverage`, `fragmentation`) while
      `fuse_adjacent` expects `()` yields exactly two conflicts, one for
      `coverage` and one for `fragmentation`, each "corpus designates failure
      mode 2 but the declaration does not include it".
    - So `apply` computes the designation per branch into local names, then
      makes one `Expectation(failure_mode=2, ..., expected_rule_ids=<local>, ...)`
      call.
    - The **unbridged** branch's runtime values are unchanged: rule ids
      `{"coverage", "fragmentation"}`, labels `{target}`, verdict
      `"flagged-for-review"`. `tests/test_037_*` AC10 pins them.
    - The **bridged** branch gives `frozenset()`, `frozenset()` and `"pass"`.
    - The literal-only scan then reads no mode-2 designation from `fuse`. That
      is the intended state: the corpus's only `fuse` case designates no rule,
      and the unbridged branch is applied only by the severity ladder, which
      reads no `Expectation`.
  - **The detail.** For the bridged form, the `detail` records the pair, the
    stacking axis, the bridged voxel and column counts, and the renumbering
    pairs. It says mode 2's spacing signal is read by no shipped rule, so no
    rule is designated.
- **A3 (measured on this branch, 2026-09-24, and where the queue line differs).**
  The measurement used a probe of A2's rule on the default base, since the
  operator is not yet written. The builder re-measures every value.
  - **Bridge.** 6 262 background voxels filled over 682 columns. No non-zero
    voxel lies inside any bridge span.
  - **Fused label.** Label 22 is one face-connected component of 45 043 voxels
    (1 mm isotropic, so 45 043 mm³; L3 + L4 were 38 781). Extents are
    31 / 37 / 63 mm, `fragmentation_index` is 1.0 and `stray_contact_area_mm2`
    is 0.0.
  - **Labels.** Label 23 equals the old 24's mask, labels 20 and 21 are
    unchanged, and the present labels are [20, 21, 22, 23].
  - **Firing.** `run_qc` under `bundled_default_config()` gives verdict `pass`
    with **no finding**, and `relationships.missing_levels` is `[]`. This
    matches the 2026-09-22 prototype measurement ("one connected label of
    45 k mm³, … verdict pass").
  - **Spacing.** `stage3.spacing_consistency.spacings_mm` is
    [33.49, 49.51, 53.52], against the clean control's
    [33.49, 32.70, 33.87, 36.84] (mean 34.23). The two spacings around the
    fused label are about 1.45× and 1.56× the clean mean. This is mode 2's own
    hypothesised signal, which no shipped rule reads.
  - **Legacy form.** The legacy unbridged form on the same base still fires
    `coverage.missing_interior` and `fragmentation.components` on [22], with
    `flagged-for-review`.
  - **Cohort (differs from the queue line).** The corpus cohort uses item 175's
    pairing (`gt = crop_to_grid(clean_control, candidate)`). There, the case is
    classified **TRUE_NEGATIVE**, not a missed detection: `eval/outcome.py`
    treats an expected-`pass` case as an expected negative, as it already does
    `remove_level_relabel`.
    - Counts go from tp 11, fp 0, tn 2, fn 1 to **tp 10, fp 0, tn 3, fn 1**.
    - Sensitivity goes from 11/12 to **10/11**. FPR stays 0.0 and specificity
      stays 1.0.
    - Mode 2's per-mode entry goes from (1, 1.0) to **(0, None)**, and the sum
      of per-mode `n_cases` from 12 to **11**.
    - Every other mode is unchanged:
      `{0: (2, 1.0), 1: (2, 1.0), 3: (2, 1.0), 4: (1, 1.0), 6: (1, 1.0), 9: (2, 1.0), 15: (1, 0.0)}`.
  - **`docs/aide/golden_evidence.generated.json`.** The `fuse_adjacent` row
    re-measures at `total_leaf_paths` 96 and `unwired_leaf_paths` 26, which is
    unchanged. The regenerated companion is therefore predicted
    byte-identical.
  - **Feature catalogue.** See A6.
- **A4 (merged dependencies, read live on `aide/queue-023`, not forward pins).**
  - Item 173's `build_clean_spine()`: shape (61, 86, 193), RAS, slices as in
    the AC terms.
  - Item 174's `_neighbour_facing_cap` mean-index idiom, and the
    `split_own_label` case this item's sweep counted on.
  - Item 175's 14-case geometric manifest, `crop_to_grid`, and the cohort
    pairing. `fuse_adjacent` is on the base grid, so it names
    `fixtures/base_scan.nii.gz`.
  - Items 170 and 171: their session fixtures and live-derived negative
    controls apply to any test touched here.
- **A5: no human gate, and no environment-gated capability.**
- **A6 (measured consequence: the feature catalogue moves).** With the fuse
  designation gone from the scan, `scan_synth_rule_mode_map()` goes from
  `{'fragmentation': (1, 2, 3, 4), 'coverage': (2, 6), ...}` to
  `{'fragmentation': (1, 3, 4), 'coverage': (6,), ...}`. The other entries are
  unchanged, and `rule_declaration_conflicts()` stays `()`.
  - Measured by rebuilding the catalogue with that map: exactly eight entries'
    `failure_modes` lose mode 2 and nothing else changes.
    - `per_label.{label}.components.component_count`
    - `per_label.{label}.components.component_sizes[]`
    - `per_label.{label}.components.fragmentation_index`
    - `per_label.{label}.components.largest_component_fraction`
    - `per_label.{label}.components.stray_component_sizes[]`
    - `per_label.{label}.components.stray_contact_area_mm2`

    Those six go from [1, 2, 3, 4] to [1, 3, 4]. Then:
    - `relationships.missing_levels[]`
    - `relationships.present_levels[]`

    Those two go from [2, 6] to [6].
  - This is the honest outcome. Those paths were tied to mode 2 only by the
    unbridged co-detection, and it matches D3's direction that no rule serves a
    mode through another mode's signal.

## Implementation Steps

1. **`FusePerturbation`** in `src/segfacet/synth/component_shape.py`, per A2.
   - Reuse `_present_labels`, `_require_present`, `_choose_adjacent_pair`,
     `_new_image`, `si_axis` and `FAILURE_MODE_NAMES`.
   - For the column walk, move the stacking axis last with `np.moveaxis` on a
     **private copy**, never on the input array. Take the columns holding both
     labels with `.any(-1)` on each mask.
   - Update the class docstring and the module docstring bullet: the unbridged
     default is kept for the supplementary severity ladder, and the bridged
     form is mode 2's corpus fixture (item 176).
   - Remove the "see the item spec's Assumptions for why not `bounds`" pointer
     only if it is no longer true. No dependency is added.
2. **Recipe** in `src/segfacet/synth/corpus.py`. The `fuse_adjacent` entry's
   `perturbation_params` becomes
   `{"target_label": 22, "neighbour_label": 23, "bridged": True}`. Add a dated
   item-176 comment saying the flag is explicit so that a default change cannot
   move the fixture.
3. **Regenerate the geometric corpus.** Run `python -m segfacet.synth.corpus`
   twice into two temp directories and byte-compare them before overwriting.
   Only `tests/corpus/manifest.json` (the `fuse_adjacent` entry) and
   `tests/corpus/fixtures/fuse_adjacent_seg.nii.gz` may differ from the
   committed tree. Any other difference is a hand-back.
4. **Specification** (`src/segfacet/failure_modes.py`).
   - **Mode 2's `fuse_adjacent`.** Set `expected_firing=()`, with a `reason`
     that states:
     - the bridged, renumbered map is one connected label over two bodies with
       a continuous sequence, so no shipped rule fires (measured live through
       `segfacet.synth.regression.pipeline_findings`, 2026-09-24);
     - mode 2's own signal is the inter-centroid spacing around the fused label
       (`stage3.spacing_consistency.spacings_mm[]`, about 1.5× the pitch);
     - no shipped rule reads that spacing, and the rule that would is left to a
       later per-mode queue (roadmap Stage 33);
     - an empty expected set never validates a mode.
   - **Mode 2's `mechanism`.** Keep the `bounds`/`reference_delta` proxy
     sentence. Replace the unbridged-case sentence with the bridged fact: the
     corpus case `fuse_adjacent` fires nothing, and its signature is the doubled
     spacing, which no shipped rule reads. Two constraints:
     - `tests/test_138_*::test_ac31_*`: the rewrite must **not** name any
       `per_label.{label}.components.*` or `relationships.*` path. With
       `expected_firing == ()`, only paths consumed by mode 2's declared rules
       (`bounds`, `reference_delta`) are permitted. `stage3.spacing_consistency.spacings_mm[]`
       is consumed by no rule and is not mode 2's anchor, so it may be named.
     - `tests/test_147_*::test_ac9_*`: the rewrite must keep a token that
       resolves live, such as `bounds`, `reference_delta` or `fuse_adjacent`.
   - **Mode 3's `mechanism`.** The clause "fuse_adjacent (mode 2, this mode's
     converse), whose absorbed neighbour is detached but touches nothing"
     becomes a statement that the fused label is a single component, so it has
     no stray component to measure. The 0.0 mm² measurement stands.
   - **Hands off.** `candidate_features`, `intended_rules`, `definition`,
     `discriminator`, `status` and every other mode are not edited.
5. **Regenerate the derived documents** with each module's `main`, twice into
   temp first, and byte-compare the two runs.
   - `segfacet.failure_modes` writes `docs/aide/failure_modes.generated.json`
     and `.md`.
   - `segfacet.traceability` writes `docs/aide/traceability_matrix.generated.json`
     and `.md`. `coverage`'s and `fragmentation`'s `exercised_by` lose
     `fuse_adjacent`, and mode 2's record changes.
   - `segfacet.catalogue` writes `docs/aide/feature_catalogue.generated.json`
     and `.md`. The diff must be exactly A6's eight `failure_modes` edits, plus
     whatever the Markdown renders from them. Anything else is a hand-back.
   - `segfacet.golden_evidence`, into temp only. It must equal the committed
     `docs/aide/golden_evidence.generated.json` byte for byte (A3). If it does
     not, hand back.
6. **Reconcile the existing tests** listed in the Testing Strategy, under the
   fence in Authorised paths. Record every edit in Decisions, by node id, with
   old → new.
7. Run `python .aide/scripts/aide.py scope 176 --base aide/queue-023` and
   confirm it exits 0.

## Authorised paths

**May change:**

- `src/segfacet/synth/component_shape.py` — the `bridged` keyword and branch (step 1).
- `src/segfacet/synth/corpus.py` — the `fuse_adjacent` recipe params and comment (step 2).
- `src/segfacet/failure_modes.py` — mode 2's case and mechanism, mode 3's clause (step 4).
- `tests/corpus/manifest.json` — the regenerated `fuse_adjacent` entry (step 3).
- `tests/corpus/fixtures/fuse_adjacent_seg.nii.gz` — the regenerated fixture (step 3).
- `docs/aide/failure_modes.generated.json` — embeds mode 2's reason and mechanism (step 5).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — conformance, exercise and mode records (step 5).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — eight entries lose mode 2 (A6).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `tests/test_176_fuse_bridged.py` — **new**: this item's test module.
- `tests/test_040_synthetic_corpus.py` — reconciliation (a) and an authorised rename (Decisions, R2).
- `tests/test_057_acceptance_stage7.py` — reconciliation (a): sensitivity, detectable-mode constant.
- `tests/test_103_feature_catalogue.py` — reconciliation (a): `_RULE_MODE_MAP`.
- `tests/test_120_leave_one_out_offset.py` — reconciliation (a): AC24 totals.
- `tests/test_125_stage28_validation.py` — reconciliation (b): the test_057 agreement set (R1).
- `tests/test_135_stage29_validation.py` — reconciliation (b): the test_057 agreement set (R1).
- `tests/test_136_rule_mode_declarations.py` — reconciliation (a): AC4's co-detection set.
- `tests/test_137_mode_less_rule_disposition.py` — reconciliation (a): the mode-2 path count.
- `tests/test_167_mode_3_detector.py` — reconciliation (b): the fused label's component count.

**The reconciliation fence.** It applies to the listed `tests/test_*.py` files
other than this item's own module. **The builder** does the reconciliation,
after regeneration, because every new value comes from the regenerated corpus
and documents. Two kinds of change are allowed:

- **(a) A moved literal.** A literal count, fraction, set or rule→mode table
  that this item moved is updated to the fresh measurement. The assertion keeps
  its shape and its tolerance, and gains a dated item-176 comment. Prose that
  quotes the literal follows it.
- **(b) A re-derived premise.** A constructed input, selection or comparison
  set whose stated premise this item falsified is re-derived. The test keeps
  what it asserts. The instances are named in the Testing Strategy.

No test is retired, skipped, `xfail`-marked or loosened in tolerance. Exactly
one rename is authorised (R2). Every other test keeps its name, even where the
name records an old value (items 173–175 precedent). A red test in a file not
listed here is a hand-back to spec-author, not an edit.

**Asserts against:**

- `src/segfacet/eval/severity_ladder.py` — its `fuse` ladder applies the unbridged default; unchanged, and `tests/test_100_*` keeps pinning its values.
- `src/segfacet/catalogue.py` — the scan and conflict checker are unchanged; A6's move comes from their input, and `rule_declaration_conflicts()` must stay `()`.
- `src/segfacet/heuristics/fragmentation.py` — its `RuleModeDeclaration` stays `(1, 3, 4)`.
- `src/segfacet/heuristics/coverage.py` — its `RuleModeDeclaration` stays `(6,)`.
- `docs/aide/golden_evidence.generated.json` — predicted byte-identical (A3); `tests/test_134_*` AC4 recomputes it live.

Some paths stay off **May change** on purpose, so `aide scope` refuses them:

- `src/segfacet/traceability.py`: no `UNUSED_OPERATOR_REASONS` entry.
- `tests/corpus/094_pre_migration_snapshot.json`: it holds no `fuse_adjacent`
  key.
- `docs/aide/golden-decision-table.md`: the fixture's row already exists, and no
  count moves.
- `.gitattributes`: `tests/corpus/manifest.json` (`text eol=lf`),
  `tests/corpus/fixtures/*.nii.gz` (`binary`) and every
  `docs/aide/*.generated.*` path above are already pinned.
- The ratchet's module `tests/test_163_*`: it must pick up the new expected set
  unedited.
- The prototype directory.

## Testing Strategy

**The new module is `tests/test_176_fuse_bridged.py`**, with one test per AC
(AC1–AC11). The test-writer writes it.

- AC1–AC6 apply the bridged operator to `build_clean_spine().seg_img`.
- AC3 and AC4 walk columns with plain NumPy. The axis comes from `si_axis`, and
  the side from the two labels' mean index on it. The tests never call the
  operator's internals.
- AC7 applies the operator to `loaded_seg_image` of the committed
  `clean_control` case and compares arrays with `np.array_equal`.
- AC9 uses `extract_feature_record`. AC10 and AC11 use
  `failure_modes.measured_firing`.

The queue's other *Testable* claims are already enforced by tests that iterate
the live manifest or specification, and pick up the change with no edit:

- **The corpus regenerates byte-identically.**
  `tests/test_040_synthetic_corpus.py::test_ac16_regeneration_is_byte_identical_across_runs_and_vs_committed`,
  plus `test_143` AC11–AC13.
- **The machine-readable record holds.** `test_040` AC17 rebuilds each case's
  `Expectation` from its recipe, so the operator must accept `bridged` in
  `perturbation_params`. `tests/test_041_regression_suite.py` runs `verify_case`
  on every case.
- **The ratchet is green.**
  `tests/test_163_specificity_ratchet.py::test_ac2_ratchet_measured_equals_expected[geometric-fuse_adjacent]`.
- **No declaration conflict.**
  `tests/test_136_rule_mode_declarations.py::test_ac6_rule_declaration_conflicts_empty_on_this_tree`.
  It is what fails if a literal (2 → `coverage`, `fragmentation`) designation
  is left in synth source (A2).

Adversarial cases, each written once:

- **`fuse-bridge-resolves-direction`**: apply the bridged operator to
  `build_clean_spine().seg_img.as_reoriented(np.array([[0, 1], [1, 1], [2, -1]]))`
  (axcodes RAI, so the caudal end is the **high** end of axis 2). Its output
  array equals the RAS output array reoriented the same way. This guards a
  hard-coded axis or side: the prototype's column walk assumed the neighbour
  lies at lower indices. That passes AC1–AC6 on the RAS base and fails here.
- **`fuse-bridge-keeps-third-label`**: on a copy of the default base, set one
  voxel inside a bridge span to label 20. Choose the span live: the first
  column holding both 22 and 23, at the first background index strictly
  between them. After the bridged `apply`, that voxel is still 20. This guards
  a bridge that fills the whole span regardless of content and silently
  overwrites another label.
- **`fuse-bridged-refuses-cranial-neighbour`**:
  `FusePerturbation(target_label=23, neighbour_label=22, bridged=True).apply(default base, 0)`
  raises `FacetInputError`. This guards step 4's renumbering running with the
  neighbour cranial of the target, which would relabel the target itself and
  leave a hole.
- **`fuse-default-form-unchanged`**:
  `FusePerturbation(target_label=22, neighbour_label=23).apply(default base, 0)`
  (no `bridged`) returns an array equal to the input with every 23 set to 22,
  and nothing else changed. This guards the bridged branch leaking into the
  default that the severity ladder applies. `tests/test_100_*` pins the ladder's
  values, but not the operator's exact transform.
- **`fuse-bridged-non-mutating`**: after a bridged `apply`, the input array is
  `np.array_equal` to a copy taken before. This guards writing through an
  `np.moveaxis` view of the caller's array, which would corrupt the base that
  `build_corpus` hands the next recipe entry.

**Existing tests to reconcile.** This is the stale-assumption sweep. Three
read-only agents checked it on 2026-09-24:

- every test naming `fuse_adjacent`, `fuse` or `FusePerturbation`;
- the rule-mode scan and catalogue mode pins;
- mode-2/3 prose tokens;
- the corpus-cohort sensitivity pins.

Each file below is under **May change**, and **the builder** edits it after
regeneration.

**Red without the edit, (a) moved literals:**

1. **`tests/test_040_synthetic_corpus.py::test_fuse_adjacent_case_records_mode_2_with_both_co_detected_rules`**
   (renamed per R2). The body mirrors its twin
   `test_remove_level_relabel_case_records_mode_6_and_honestly_fires_nothing`:
   - `failure_mode == 2`, `condition == ""` and `detection == "pipeline"` stay;
   - `expected_rule_ids`: `["coverage", "fragmentation"]` → `[]`;
   - `expected_labels == []` is added;
   - `expected_verdict`: `"flagged-for-review"` → `"pass"`;
   - the subset check becomes `list(case_result.findings) == []`, with
     `verdict.overall == Severity.PASS`.

   The docstring states the bridged fact, with a dated item-176 line.
2. **`tests/test_057_acceptance_stage7.py`:**
   - `_PIPELINE_DETECTABLE_MODES`: `(1, 2, 3, 4, 6, 9)` → `(1, 3, 4, 6, 9)`.
     Its comment block gains an item-176 line: mode 2's only case now expects
     `pass`. This removes the parametrised node
     `test_ac9_pipeline_detectable_mode_sensitivity_is_one[2]` (R1).
   - `test_overall_corpus_sensitivity_is_nine_of_ten_not_over_claimed`:
     `approx(11.0 / 12.0)` → `approx(10.0 / 11.0)`, with a docstring history
     line. The name is kept.
   - `tests/test_132_*` AC22 calls this test and follows with no edit.
3. **`tests/test_120_leave_one_out_offset.py::test_ac24_corpus_pipeline_detection_is_nine_of_ten`:**
   - sensitivity `11.0 / 12.0` → `10.0 / 11.0`;
   - remove the `2: 1.0` entry from `expected_sensitivity`;
   - `sum(n_cases) == 12` → `11`.

   The "(2 (fuse), …)" docstring prose follows.
4. **`tests/test_103_feature_catalogue.py::_RULE_MODE_MAP`** (read by
   `test_ac13_rule_mode_map_matches_the_corpus_scan` and the
   `test_ac13_rule_mode_map_effect_on_failure_modes[...]` parametrisation):
   - `"fragmentation": (1, 2, 3, 4)` → `(1, 3, 4)`;
   - `"coverage": (2, 6)` → `(6,)`;
   - drop "fuse_adjacent (2)" from the trailing comments. The stale docstring
     "coverage's corpus modes are (2, 6)" follows.
5. **`tests/test_136_rule_mode_declarations.py::test_ac4_corroborated_modes_are_covered_by_the_measured_corpus_map`:**
   `expected_co_detections` goes from
   `{("coverage", 2), ("fragmentation", 2), ("mislabel", 1)}` to
   `{("mislabel", 1)}`. Its comment and docstring clause ("coverage,
   fragmentation and mislabel are each designated one mode more than they
   declare") follow.
6. **`tests/test_137_mode_less_rule_disposition.py::test_adv_measured_artifact_movement_counts_from_spec`:**
   `mode2_count == 15` → `7` (the four `bounds` `geometry.*` paths plus three
   `reference_delta.*` paths). The other counts (140, 14, 2) and the evidence
   table hold. Add a dated "Re-measured (item 176)" paragraph. The earlier
   `{1, 2, 3, 4}` prose stays as history.

**Red without the edit, (b) re-derived premises:**

7. **`tests/test_167_mode_3_detector.py::test_fuse_adjacent_stays_silent`.**
   Its premise "label 22 carries a detached component" is false. Assert
   `info.component_count == 1` instead of `> 1`, with a re-worded message. The
   test still pins `stray_contact_area_mm2 == 0.0`, so what it guards (mode 3's
   detector stays silent on mode 2's case) holds. The name is kept.
8. **`tests/test_125_stage28_validation.py::test_ac15_agrees_with_test_057_pipeline_detectable_modes`**
   and
   **`tests/test_135_stage29_validation.py::test_ac25_agrees_with_test_057_pipeline_detectable_modes`.**
   Their stated premise, "every pipeline-typed mode has a detected case", is
   falsified. Each test compares `t057._PIPELINE_DETECTABLE_MODES` against a
   set built **inline in that test**: the `failure_mode` of every manifest case
   with `detection == "pipeline"`, kind `failure` and a **non-empty**
   `expected_rule_ids`. It is `{1, 3, 4, 6, 9}` today.
   - The module helper `_pipeline_detected_modes_excluding_clean_control` is
     **not** edited. It still feeds `test_ac15/ac25_manifest_pipeline_detected_mode_count_is_five`
     (`{1, 2, 3, 4, 6, 9}`) and the `agrees_with_test_040_mode_sets` tests,
     which stay green: mode 2's case is still a pipeline-path failure case.
   - The in-test comments are re-worded to name `remove_level_relabel` and
     `fuse_adjacent` as the two expected-`pass` failure cases (R1).

**Checked and unaffected** (sweep, 2026-09-24):

- `test_037`: every construction uses the default. Its AC10 pins the
  unbridged runtime `Expectation`, which A2 keeps.
- `test_100`, `test_153` AC19 and `test_154`: the severity ladder and the
  `fuse` ladder's home are unchanged.
- `test_035` and `test_038`.
- `test_094` and the 094 snapshot: there is no `fuse_adjacent` key.
- `test_091` (baseline modes 0, 1, 4, 6, 9) and `test_116` AC8 (mode 0).
- `test_057` AC8 (FPR 0) and AC13: `calibrate.py` skips modes with
  `n_cases == 0`.
- The case-id-only sets in `test_116`, `test_129`, `test_131`, `test_132`,
  `test_134`, `test_143`, `test_105` and `test_126`, and the case/count pins in
  `test_149`: the count is unchanged.
- `test_145` AC8/9/20/21 (L806's `empty_expected >= 1` becomes 2, still true),
  `test_146`, `test_148`, `test_155`, `test_156`, `test_162`, `test_171`,
  `test_172`, `test_173`, `test_166` and `test_174`.
- `test_159`: its name list does not include the renamed test.
- `test_138` AC20/AC21, and AC31's co-detection existence clause, which mode 1
  still satisfies.
- `test_121` AC10: its `("fuse_adjacent", 22)` exclusion still describes a
  label over two bodies. Only a run confirms this.
- `report_format_fixture` and its contract.

**Regeneration-gated, green once step 5's artifacts are committed:**

- `test_040` AC15–AC17, `test_143` AC11–AC13 and AC15, `test_134` AC4, and
  `test_157` AC18;
- `test_162` AC9/AC10, `test_145` AC23, `test_137` AC15, `test_136` AC13,
  `test_131` AC15 and `test_129` AC20;
- `test_104`'s drift test;
- `test_138` AC2–AC5, and `test_144`/`146`/`147`/`150`/`151`/`152`'s
  fresh-versus-committed comparisons.

**Stale but green, not edited** (prose only; none pins a moved value):

- `test_145::test_ac13_co_detection_alone_does_not_validate` and its
  docstrings, and `test_145` L104;
- the `test_147` L1195 comment and `test_146` L869;
- `test_121`'s "absorbs … into" docstrings;
- `test_149` L771 and `test_099` L1007;
- the `src/segfacet/heuristics/fragmentation.py` comment "FusePerturbation
  designates mode 2", which is off May change (Asserts against).

**Sibling note.** Item 177 (`displace`) regenerates the same manifest,
traceability and specification documents. Whichever lands later re-measures on
top of the earlier one. `displace` stays a detected mode-1 case, so it moves
none of entries 2–3 above.

## Validation

1. Run `python -m segfacet.synth.corpus --out <tmp>` and diff `<tmp>` against
   `tests/corpus/`. Confirm there is no difference.
2. Run
   `.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/fuse_adjacent_seg.nii.gz --no-reference --out <tmp>`.
   `--no-reference` is required (CLAUDE.md gotcha). Expect verdict `pass` with
   zero findings.
3. Run `python .aide/scripts/aide.py scope 176 --base aide/queue-023` and
   confirm it exits 0.
4. Run `.venv/bin/python -m pytest --collect-only -q` on this branch and on
   `aide/queue-023`. The branch's collected test-id set must equal the base's,
   with exactly these differences:
   - **Added:** every test in `tests/test_176_fuse_bridged.py`,
     `tests/test_040_synthetic_corpus.py::test_fuse_adjacent_case_records_mode_2_bridged_and_fires_nothing`,
     and
     `tests/test_041_regression_suite.py::test_ac5_undetected_failure_case_fires_nothing_and_verifies[fuse_adjacent]`.
   - **Removed:**
     - `tests/test_040_synthetic_corpus.py::test_fuse_adjacent_case_records_mode_2_with_both_co_detected_rules` (R2);
     - `tests/test_041_regression_suite.py::test_ac5_designated_heuristic_fires_for_pipeline_cases[fuse_adjacent]`
       and `::test_ac6_offending_labels_match_manifest_for_pipeline_cases[fuse_adjacent]`;
     - `tests/test_057_acceptance_stage7.py::test_ac9_pipeline_detectable_mode_sensitivity_is_one[2]`.

   The `test_041` moves are automatic, because its `_NON_CLEAN_PIPELINE_CASES`
   and `_UNDETECTED_PIPELINE_CASES` partition the manifest live. It needs no
   edit. Any other difference is a finding.

No `[validation]` profile is needed, so there is no ❓ Unverified downgrade
path.

## Dependencies

- Item 173 (merged into `aide/queue-023`): the lordotic base the fuse bridges.
- Item 174 (merged): the mean-index cap idiom and the manifest this item
  re-measures.
- Item 175 (merged): the 14-case manifest, `crop_to_grid` and the corpus-cohort
  pairing whose literals this item moves again.

**Downstream:**

- Mode 2's inter-centroid-spacing rule (a later per-mode queue, roadmap
  Stage 33 "Scope decisions") is the first rule expected to fire on
  `fuse_adjacent`. That item must re-author its `expected_firing` and list
  `tests/test_176_fuse_bridged.py` under May change, because AC10's empty set
  will move.
- D4 re-measures the severity ladders, including the unbridged `fuse` ladder.
- Item 178 renders the re-authored case.

## Decisions & Trade-offs

To be updated during implementation.

- **R1: `_PIPELINE_DETECTABLE_MODES` against the test_125/test_135 agreement
  tests (spec-author, 2026-09-24).**
  - **Decision.** The faithful reading of test_057's constant is its own
    comment: "modes with ≥1 corpus case detected by plain run_qc". Mode 2 no
    longer has one, so the constant drops 2. The two agreement tests are
    re-derived to compare against that same notion, computed from the manifest:
    pipeline-path failure cases that designate a rule.
  - **Rejected: changing `fuse_adjacent`'s `detection`.** `detection` names
    the path the case is measured on (`pipeline` against
    `reconstructed_record`), not whether anything fires. `remove_level_relabel`
    is the precedent: `pipeline`, with an empty expected set. `test_040`
    AC8's `_PIPELINE_ONLY_MODES` partition (`{0, 1, 2, 3, 4, 6, 9}`) depends
    on it and stays.
  - **Rejected: editing the shared helper.** That would move
    `mode_count_is_five`'s `{1, 2, 3, 4, 6, 9}` and the `test_040` agreement
    for no gain.
  - **Tests this moves:**
    - `test_057`'s constant, which removes node `test_ac9_…[2]`;
    - `test_125::test_ac15_agrees_with_test_057_pipeline_detectable_modes`;
    - `test_135::test_ac25_agrees_with_test_057_pipeline_detectable_modes`.
- **R2: the `test_040` name (spec-author, 2026-09-24).**
  - **Decision.** `test_fuse_adjacent_case_records_mode_2_with_both_co_detected_rules`
    is **renamed** to
    `test_fuse_adjacent_case_records_mode_2_bridged_and_fires_nothing`.
  - **Why not keep the name.** Unlike the count-in-name tests kept by items
    173–175, this name asserts a property the test now refutes.
  - **Checked.** Nothing pins the name: no reference in `tests/`, `src/` or
    `docs/aide/` outside the permissions log, and it is absent from
    `tests/test_159_*`'s name list.
  - This is the only rename authorised. The Validation collect-only accounting
    names it.
- **R3: mode 2's mechanism rewrite (spec-author, 2026-09-24).** It is
  constrained as step 4 states:
  - no `components.*` or `relationships.*` path, for `test_138` AC31 (with an
    empty expected set, only `bounds`/`reference_delta`-consumed paths are
    permitted);
  - a live token, for `test_147` AC9.
- **R4: golden evidence (spec-author, 2026-09-24).** Re-measured, not assumed:
  the bridged case reads 96 / 26, the same as today, because
  `relationships.missing_levels[]` is realised as a leaf either way. So
  `docs/aide/golden_evidence.generated.json` is **Asserts against**, and step 5
  hands back if it moves.
- **R5: test_041's node ids (spec-author, 2026-09-24).** `fuse_adjacent` moves
  from `test_041`'s designated-rule partition to its undetected partition by
  live parametrisation. This is accounted for in Validation step 4, not
  edited.
- **Left open:** whether the unbridged absorb should stay registered as
  `fuse`'s default once D4 re-measures the severity ladders. The maintainer's
  vocabulary makes it a "one label in several parts" map rather than a fused
  segment. Its ladder is D4's, so it is not settled here.
- **Left open:** `catalogue._scan_synth_rule_mode_map` derives the "corpus"
  rule→mode map from operator-source literals, not from the manifest's cases,
  so an operator branch no corpus case applies can still designate. This item
  works with that (A2) and records it in `insights.md` rather than changing the
  scan.
