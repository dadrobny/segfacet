<!-- aide-template: item 2 -->
# Item 187 — `neighbour_contact` becomes a rule of its own, serving mode 3

> **Created:** 2026-09-27 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-025.md`](../queue/queue-025.md) · Item 187
> **Objectives:** G2, G8
> **Suggested branch:** `aide/187-neighbour-contact-becomes-a-rule`

---

## Description

This item implements roadmap Stage 33 D3's first bullet: `neighbour_contact`
leaves `fragmentation` and becomes a rule of its own, serving mode 3 (split
vertebra segment). It closes the `gap` entry in `docs/aide/insights.md` dated
2026-09-22 (queue-022 review, the `neighbour_contact` decision) and the `defect`
entry dated 2026-09-23 (item 173, the stale threshold comment in
`default_config.yaml`). It follows the maintainer feedback of 2026-09-25
recorded in `queue-025.md`.

**Why the move.** `fragmentation`'s `components` and `islands` detectors read one
label in several parts. That is not mode 3, which is one vertebra under several
labels. Item 167 added mode 3's own signal as a third `fragmentation` detector,
so today `fragmentation` declares modes (1, 3, 4). After this item
`fragmentation` declares (1, 4), and a new rule `neighbour_contact` declares
(3,).

**Why the measure changes.** `components.stray_contact_area_mm2` is an absolute
area. A small component shows little absolute contact even when most of its
surface touches a neighbour. So contact is also measured relative to the
component's own surface: the contact area with its most-contacted neighbour,
divided by the component's surface area. It is reported at two scopes:

- **per connected component**, naming the neighbour each part touches, which is
  what says which part of a fragmented label may need merging, and into which
  label;
- **per whole label**, whether or not the label is fragmented.

The new rule reads the per-component fraction of a label's non-largest
components, with the threshold re-expressed on the relative measure and
re-measured on the lordotic corpus.

**What this item changes.**

- `features/components.py`: `ComponentsInfo` gains `component_contacts` and
  `label_contact_fraction` (A1, A2, A3). The absolute `stray_contact_*` fields
  stay (A4).
- A new `heuristics/neighbour_contact.py` registers the rule (A5–A7).
  `fragmentation.py` loses the `neighbour_contact` detector, its threshold
  constant, its two consumed paths, and mode 3.
- `failure_modes.py`: mode 3's edge moves to the new rule, and the `split` case's
  expected set becomes `("neighbour_contact",)`.
- `synth/component_shape.py`: `SplitPerturbation`'s `Expectation` designates
  `neighbour_contact`, so the committed manifest's `split` entry moves. No
  fixture's bytes move.
- The rule-count and rule-id pins in `tests_dir` are paid once, here.
- Every generated artifact that reads any of the above is regenerated.

**Not in scope.**

- No new corpus case, and no fixture change. `split_own_label` (mode 3 sub-type
  b) is not detected by the new rule (Left open).
- No active `rules.neighbour_contact` section in `default_config.yaml`. The
  threshold is documented as a comment, like `intensity` and
  `intensity_reference_delta` (A7).
- No change to `fragmentation`'s `components` or `islands` detectors, their
  thresholds, or modes 1 and 4.
- `coverage` (item 188), `mislabel` (item 189), the condition gate (item 191) and
  the bar checker (Stage 33 D4) are other items'.

## Acceptance Criteria

Terms used below:

- **"The split case"** is the `split` entry of
  `segfacet.synth.corpus.load_manifest()`, and **"its image"** is
  `segfacet.synth.regression.loaded_seg_image(<that case>)` (the committed
  `tests/corpus/fixtures/split_seg.nii.gz`).
- **"Components of label N"** is
  `compute_components(<its image>, N, bundled_default_config())`.
- **"Recomputed in the test"** means computed by the test itself from the image's
  array and `header.get_zooms()`, by the definitions of A2, never read back from
  the code under test.

- [ ] **AC1: each component's contact fraction is measured.** For every index
  `i` of components of label 24, `component_contacts[i].contact_fraction`
  equals the fraction recomputed in the test for the `i`-th component in
  `component_sizes` order (A1), to `abs=1e-12`.
- [ ] **AC2: each component's record names the neighbour it touches.** For every
  index `i` of components of label 24, `component_contacts[i].neighbour_label`
  equals the most-contacted other label recomputed in the test for that
  component (`0` when it touches none).
- [ ] **AC3: a small component with most of its surface in contact scores higher
  than a large one with the same contact area.** On a constructed label map (see
  Testing Strategy), the two components' `contact_area_mm2` values are equal and
  the small component's `contact_fraction` is strictly greater than the large
  one's.
- [ ] **AC4: an unfragmented label carries a label-level contact fraction.** For
  components of label 23 of the split case, `component_count == 1` and
  `label_contact_fraction` equals the label-level fraction recomputed in the
  test (A3), to `abs=1e-12`.
- [ ] **AC5: the rule count is 11.** `len(list(segfacet.heuristics.iter_rules())) == 11`.
- [ ] **AC6: the rule declares one detector on the relative measure.**
  `NeighbourContactRule.mode_declaration.detectors` holds exactly one
  `RuleDetector`, whose `detector_id == "stray_contact"` and whose
  `signal_paths == ("per_label.{label}.components.component_contacts[].contact_fraction",)`.
- [ ] **AC7: the detector serves mode 3 and no other mode.**
  `segfacet.failure_modes.modes_for_detector("neighbour_contact", "stray_contact") == (3,)`.
- [ ] **AC8: `fragmentation` declares no mode 3.**
  `3 not in FragmentationRule.mode_declaration.modes`.
- [ ] **AC9: the rule fires on the split case.** The findings of
  `pipeline_findings(<the split case>)` whose `rule_id == "neighbour_contact"`
  are exactly one finding, with `detector_id == "stray_contact"` and
  `labels == frozenset({24})`.
- [ ] **AC10: the rule fires on no other corpus case.** Over every case of both
  committed manifests, each driven through the detection path its manifest entry
  names (as `segfacet.failure_modes.measured_firing` dispatches it), the set of
  `(corpus, case_id)` pairs producing any finding with
  `rule_id == "neighbour_contact"` equals `{("geometric", "split")}`.
- [ ] **AC11: the split case's measured firing is the new rule alone.** For `c`,
  the `split` entry of `failure_modes.SPECIFICATION[3].corpus_cases`,
  `set(failure_modes.measured_firing(c)) == {"neighbour_contact"}`.
- [ ] **AC12: the committed manifest designates the new rule for the split
  case.** The split case's `expected_rule_ids == ["neighbour_contact"]`.
- [ ] **AC13: mode 3 still meets the bar's conditions 1–5.**
  `tuple(c.met for c in segfacet.traceability.bar_conditions(3)) == (True, True, True, True, True)`.
- [ ] **AC14: mode 3's deciding detector is the new rule's.** Condition 4 of
  `bar_conditions(3)` has `subjects == ("neighbour_contact/stray_contact",)`.
- [ ] **AC15: the threshold is on the relative measure, fired strictly above.**
  With `rules.neighbour_contact.params.contact_fraction_threshold` set to the
  split case's own recorded stray-component `contact_fraction` (read from
  `extract_feature_record(<its image>, ...)`), `run_rules` over that record
  returns no finding with `rule_id == "neighbour_contact"`.

Why each is written: AC1–AC4 are the queue line's *Testable* sentences for the
measure, one each. AC5, AC8 and AC9–AC10 are its sentences for the rule. AC6–AC7
and AC13–AC14 are what Stage 33 D5's at-the-bar sign-off reads for mode 3: the
move must leave mode 3 at conditions 1–5, now through the new rule. AC11 and AC12
are the queue's stated consequence for the corpus, one per record (the
specification and the manifest). AC15 is "the threshold is re-expressed on the
relative measure". That the split case's authored expected set equals its
measured firing is the specificity ratchet's job
(`tests/test_163_specificity_ratchet.py`), and that the specification and the
manifest agree is `failure_modes.specification_conflicts()`'s, so neither is
restated. None of these closes a Stage 33 acceptance criterion: criterion 3
("no rule declares a mode through a detector that reads another mode's signal")
still has `coverage` and `mislabel` open (items 188, 189) and the detector-granular
bar checker (D4).

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
measurement below was run on this branch on 2026-09-27 with `.venv/bin/python`
and a scratch probe of A2's definitions over every committed fixture of both
corpora. The builder re-measures each one.

- **A1 (the record interface).** In `segfacet.features.components`, added to
  `__all__`:
  - `ComponentContact`, a frozen dataclass with fields `neighbour_label: int`,
    `contact_area_mm2: float`, `surface_area_mm2: float` and
    `contact_fraction: float`, in that order.
  - `ComponentsInfo.component_contacts: List[ComponentContact]`, one entry per
    component, in `component_sizes` order: descending voxel count, ties broken by
    ascending component id (item 167's policy). So index 0 is the label's largest
    component, and `component_contacts[1:]` are its stray components.
  - `ComponentsInfo.label_contact_fraction: float` (A3).

  `feature_report.components_to_dict` serialises them as
  `components.component_contacts`, a list of dicts with those four keys, and
  `components.label_contact_fraction`. The catalogue gains five leaf paths:
  `per_label.{label}.components.component_contacts[].<key>` for the four keys,
  and `per_label.{label}.components.label_contact_fraction`.

  The new rule is the one consumer in this batch. It reads the serialised record,
  so the key names and the index-0-is-largest order are what it depends on.
- **A2 (defensible default: what "contact" and "surface" mean).** For a boolean
  mask M of one component (or one label), over the label map padded by one
  background voxel on every side:
  - a **face** is a 6-neighbour pair (v, w) with v in M and w not in M. Its area
    is the product of the two zooms orthogonal to the pair's axis, from
    `header.get_zooms()`;
  - **surface_area_mm2** is the summed area of every face, including faces on
    the image boundary (w is padding);
  - the **contact area with label k** is the summed area of the faces whose w
    carries label k, for k non-zero and not the label itself;
  - **neighbour_label** is the k with the largest contact area, the lowest k on
    a tie, and `0` when no face touches another label;
  - **contact_area_mm2** is the contact area with `neighbour_label` (`0.0` when
    it is `0`), and **contact_fraction** is `contact_area_mm2 / surface_area_mm2`.

  So the fraction lies in [0, 1]. This is item 167's face-contact definition,
  kept, divided by the same component's own face count. Two components of one
  label never share a face (6-connectivity), so a component's surface is exactly
  its faces toward other labels, background and the image boundary.
- **A3 (defensible default: the label scope is the same measure over the whole
  label).** `label_contact_fraction` is A2's `contact_fraction` for the mask of
  the whole label: the label's contact area with its single most-contacted
  neighbour, over the label's total surface. It is computed from the per-component
  contact tallies (a label's contact with k is the sum of its components' contact
  with k, and its surface is the sum of their surfaces), not by a second pass.
  One definition at both scopes means a component's fraction and its label's
  fraction are never read against different denominators. The queue asks for the
  neighbour to be named per component, so the label scope carries the fraction
  only (Left open).
- **A4 (defensible default: the absolute fields stay).** The queue says contact
  is *also* measured relatively. `stray_contact_area_mm2` and
  `stray_contact_label` keep their item-167 definition and serialisation. No rule
  reads them after this item, and mode 3 keeps `stray_contact_area_mm2` as a
  `hypothesised` candidate feature. `tests/test_167_mode_3_detector.py`'s AC1–AC3
  still pin them and stay green unedited.
- **A5 (defensible default: the rule reads stray components only).** The rule
  reads `component_contacts[1:]` of each label, never index 0 and never
  `label_contact_fraction`. Measured: the only non-zero stray fraction in either
  corpus is `split`'s label-24 cap, **0.3317** (806.0 mm² against label 23, over
  2430.0 mm² of surface, 4030 voxels). Every other stray component measures 0.0
  (`fragment`'s second piece of label 22, `inject_islands`'s 27-voxel island).
  Largest components and whole labels do touch neighbours:
  `force_overlap` labels 20 and 21 read 0.1771 and 0.1956, the split donor
  (label 23 of `split`) reads 0.1859, and `split_own_label`'s cap (label 23, its
  own label's only component) reads 0.3317. Reading any of those would fire on
  cases that do not express sub-type (a). That is why the queue's "fires on
  `split` and on no other corpus case" holds only for the stray reading.
- **A6 (measured: the threshold).** `DEFAULT_CONTACT_FRACTION = 0.1` in
  `heuristics/neighbour_contact.py`, fired strictly above (item 027's convention,
  which `fragmentation` follows). Margins over both corpora: the one firing value
  0.3317 sits +0.2317 above it (3.3x), and every non-firing stray value (0.0) sits
  0.1 below it. Its physical reading is a stray part with more than a tenth of
  its surface pressed against another label. Calibrated on the synthetic corpus
  only; Stage 21 re-calibrates on real ground truth.
- **A7 (defensible defaults: the rule's shape).**
  - `rule_id = "neighbour_contact"`, one detector `stray_contact` with reason tag
    `"Neighbour contact:"`, `mode_declaration.modes == (3,)`.
  - One finding per stray component above threshold, with
    `labels == frozenset({label})`, so the manifest's exact
    `expected_labels == [24]` for `split` holds. The reason names the label, the
    component's rank and voxel count, its `contact_fraction`, and its
    `neighbour_label` as the merge candidate.
  - Params, read through `config.rule_param`: `contact_fraction_threshold`
    (default A6) and `severity` (default `"flagged-for-review"`, unknown label
    raises `ValueError` before any per-label work, as in `fragmentation`).
  - Absence-tolerant: a label whose `components` block lacks `component_contacts`
    emits nothing.
  - No active `rules.neighbour_contact` section in `default_config.yaml`: an
    active section moves `config_hash` in every report and breaks
    `tests/test_035_default_config.py`'s seven-section pin. `rule_enabled`
    defaults to `True` for an absent section.
- **A8 (measured: nothing else moves in the corpus).** The new rule adds no
  finding to any case but `split`. `split` loses its `fragmentation` finding and
  gains one `neighbour_contact` finding, on the same label 24, so its verdict
  (`flagged-for-review`) and `expected_labels` are unchanged. `fragmentation`'s
  `components` and `islands` detectors still fire where they did (`fragment`,
  `inject_islands`), so modes 1 and 4 keep their expected sets. No committed
  fixture's bytes change, and the intensity manifest does not move.
- **A9 (defensible default: the schema).** `report_schema_v0.json`'s `components`
  block declares `additionalProperties: false`, so the two new keys are added
  under `properties` (with `component_contacts` an array of objects carrying the
  four keys), and not under `required`. Item 167's A5 took the same choice, for
  the same reason: several test modules hand-build a `components` block.
- **A10 (predicted, re-measured by the builder): Stage 30's recorded counts stay
  true.** `tests/test_151_stage30_validation.py`'s AC35 tests compare Stage 30's
  attestation text in `progress.md` against live counts of derived statuses and
  per-edge rungs. Moving mode 3's `synthetic-demonstrable` edge from one rule to
  another keeps the edge count and every rung count, and mode 3 stays
  `validated`. So no `progress.md` amendment is expected. If the suite says
  otherwise, the builder hands back.
- **A11: no human gate, and no environment-gated capability.**

## Implementation Steps

1. **`src/segfacet/features/components.py`.** Add `ComponentContact` and the two
   `ComponentsInfo` fields (A1), with docstrings crediting item 187. Compute them
   in the existing loop: extend the item-167 per-component tally (the
   `neighbour_slices` walk over `padded`, which already builds `area_by_other`)
   to run over **every** component, largest included, and to tally the face area
   whose neighbour voxel is outside the component (the surface). Build each
   `ComponentContact` from that tally, and sum the tallies for the label scope
   (A3). Keep `stray_contact_area_mm2` / `stray_contact_label` derived exactly
   as today (A4); they must not change value on any fixture. A single-component
   label still gets its one-entry `component_contacts`. No second labelling pass
   and no new dependency.
2. **`src/segfacet/feature_report.py`.** `components_to_dict` emits
   `component_contacts` (a fresh list of fresh dicts, no aliasing) and
   `label_contact_fraction`.
3. **`src/segfacet/report_schema_v0.json`.** Add both properties (A9).
4. **`src/segfacet/feature_docs.py`.** One `FeatureDoc` per new leaf path (A1),
   stating A2's and A3's definitions; `build_catalogue(strict=True)` raises
   without them.
5. **`src/segfacet/heuristics/neighbour_contact.py`** (new). `NeighbourContactRule`
   per A5–A7, modelled on `sequence.py`'s single-detector layout and
   `fragmentation.py`'s severity helper. Its `mode_declaration`:
   `modes=(3,)`; `evidence` naming the `split` case and A5's measured values;
   `consumed_paths` of `per_label` (bookkeeping, container),
   `per_label.{label}.components.component_contacts[].contact_fraction`
   (signal), and `per_label.{label}.components.component_contacts[].neighbour_label`
   (bookkeeping: names the merge candidate in the reason). Add any further path
   the reason reads (for example `component_sizes[]`) as bookkeeping with a
   reason. The module docstring carries the design decisions and a scope fence,
   house style.
6. **`src/segfacet/heuristics/__init__.py`.** Import the new module so it
   registers, beside the others.
7. **`src/segfacet/heuristics/fragmentation.py`.** Remove the `neighbour_contact`
   detector, its evaluate branch, `_NEIGHBOUR_CONTACT_TAG`,
   `DEFAULT_NEIGHBOUR_CONTACT_AREA_MM2` (and its `__all__` entry), and the two
   `stray_contact_*` consumed paths. `modes=(1, 4)`. Drop the mode-3 sentence
   from `evidence` and the class comment; record in the module docstring that
   item 187 moved mode 3's detector out.
8. **`src/segfacet/default_config.yaml`.** Delete the fragmentation block's
   neighbour-contact comment. Add a commented, section-less `neighbour_contact`
   block after `mislabel`, in the `intensity` block's form, documenting
   `contact_fraction_threshold: 0.1` and `severity`, with A6's re-measured values
   and date. The parsed config must not change.
9. **`src/segfacet/synth/component_shape.py`.** `SplitPerturbation`'s
   `Expectation(expected_rule_ids=frozenset({"neighbour_contact"}))`.
10. **`src/segfacet/failure_modes.py`**, mode 3 only:
    - the `IntendedRule` with `rule_id="fragmentation"` becomes
      `rule_id="neighbour_contact"`, `detector_ids=("stray_contact",)`, rung
      `"synthetic-demonstrable"`;
    - add `CandidateFeature(path="per_label.{label}.components.component_contacts[].contact_fraction", role="hypothesised")`;
    - rewrite `mechanism` for the new rule, the relative measure and A5's values;
    - `split`: `expected_firing=("neighbour_contact",)`, and its `reason`
      re-measured (label 24's cap, contact fraction, neighbour 23, and that
      `fragmentation` no longer fires on it);
    - `split_own_label`'s `reason`: its `neighbour_contact` sentence re-worded
      for the new rule (the cap is its label's only component, so it has no
      stray component; its `label_contact_fraction` reads about 0.33, which no
      rule reads).

    Also correct the stale `_registry_declares` docstring example
    (`fragmentation` "declares `modes=(2, 3)`") to the real (1, 4). Edit no other
    mode.
11. **Regenerate**, each twice into temp directories, byte-comparing the two runs
    before writing the committed copy:
    - `python -m segfacet.synth.corpus --out <tmp>`: copy only
      `manifest.json` into `tests/corpus/`. Every fixture in `<tmp>` must equal
      the committed one byte for byte (A8); if not, hand back;
    - `python -m segfacet.synth.corpus_sheet` (the manifest digest moved);
    - `python -m segfacet.failure_modes`, `python -m segfacet.traceability`,
      `python -m segfacet.catalogue`, `python -m segfacet.golden_evidence`;
    - `.venv/bin/python -m tests.report_format_fixture`, after adding both keys to
      the fixture's hand-written components block.
12. **Reconcile** the tests listed under Testing Strategy, each as a moved literal
    with a dated item-187 comment.
13. Run `python .aide/scripts/aide.py scope 187` and confirm it exits 0.

## Authorised paths

**May change:**

- `src/segfacet/features/components.py` — `ComponentContact`, the two new fields and their computation (step 1).
- `src/segfacet/feature_report.py` — serialises them (step 2).
- `src/segfacet/report_schema_v0.json` — the two new properties (step 3).
- `src/segfacet/feature_docs.py` — a `FeatureDoc` per new leaf path (step 4).
- `src/segfacet/heuristics/neighbour_contact.py` — **new**: the rule (step 5).
- `src/segfacet/heuristics/__init__.py` — registers it (step 6).
- `src/segfacet/heuristics/fragmentation.py` — the detector and mode 3 removed (step 7).
- `src/segfacet/default_config.yaml` — the threshold comment moved and re-measured (step 8).
- `src/segfacet/synth/component_shape.py` — `SplitPerturbation`'s expectation (step 9).
- `src/segfacet/failure_modes.py` — mode 3's edge, candidate feature, mechanism and case reasons (step 10).
- `tests/corpus/manifest.json` — `split`'s `expected_rule_ids` (step 11).
- `docs/aide/corpus_sheet.png` — regenerated for the new manifest digest (step 11).
- `docs/aide/failure_modes.generated.json` — regenerated (step 11).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 11).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated; five new leaf paths (step 11).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `docs/aide/golden_evidence.generated.json` — regenerated; `split`'s finding and every case's leaf-path counts move (step 11).
- `tests/report_format_fixture.py` — the hand-written components block gains both keys (step 11).
- `tests/golden/report_format_contract.json` — regenerated from that fixture only (step 11).
- `tests/test_187_neighbour_contact_rule.py` — **new**: this item's test module.

- `tests/test_136_rule_mode_declarations.py` — `len(list(iter_rules())) == 10`, `_CORROBORATED["fragmentation"]` and its expected co-detections.
- `tests/test_137_mode_less_rule_disposition.py` — `len(rules) == 10`, the leaf-path count and per-mode path counts.
- `tests/test_138_traceability_matrix.py` — the exact `RULE_IDS` tuple.
- `tests/test_167_mode_3_detector.py` — the moved `(rule_id, detector_id)` pair, mode-3 edge and `split` expected-set literals, and its import of the removed constant.
- `tests/test_166_split_operator.py` — `split`'s `{"fragmentation"}` expected set and mode 3's edge rule-id set.
- `tests/test_174_split_sub_types.py` — AC9's `("fragmentation", "neighbour_contact")` pair.
- `tests/test_124_observed_range.py` — the catalogue leaf-path count.
- `tests/test_131_tangent_direction_normalisation.py` — `_PRE_ITEM_TOTAL_LEAF_PATH_COUNT`.
- `tests/test_132_monotonicity_against_traversal_order.py` — the leaf-path count.
- `tests/test_148_per_path_mode_attribution.py` — the catalogue entry count and `stray_contact_*` mode attribution.
- `tests/test_126_golden_retirement.py` — the golden-evidence leaf-path count pair.
- `tests/corpus/119_pre_119_digests.json` — `catalogue_leaf_path_set_sha256` recomputed (item 121's standing obligation).
- `tests/test_103_feature_catalogue.py` — only if the suite names it: its corpus-derived rule-to-mode map.
- `tests/test_145_eight_hypothesised_modes.py` — only if the suite names it: mode 3's derived status is expected unchanged.
- `tests/test_147_specification_is_the_record.py` — only if the suite names it: same.
- `tests/test_098_stray_components.py` — only if the suite names it: subset-shaped key-set checks are expected to stay green.

**The reconciliation fence.** Each file above is reconciled as a moved literal
with a dated item-187 comment. The one retirement is
`tests/test_167_mode_3_detector.py::test_threshold_margin_on_the_committed_corpora`,
whose constant no longer exists; this item's `threshold-margin-on-the-committed-corpora`
case replaces it. Its `test_absence_tolerant_detector` is re-pointed to
`NeighbourContactRule`. No other test is retired, skipped, `xfail`-marked or
loosened. A red test in a file not listed here is a hand-back to spec-author.

**Asserts against:**

- `tests/corpus/fixtures/split_seg.nii.gz` — AC1–AC4, AC9 and AC15 recompute from its bytes; it must not move (A8).
- `tests/corpus/intensity/manifest.json` — AC10 sweeps it unchanged.
- `src/segfacet/traceability.py` — AC13–AC14 recompute `bar_conditions(3)` live; no scorer changes here.
- `src/segfacet/synth/regression.py` — AC9–AC11 drive the committed cases through it unchanged.

## Testing Strategy

The test module is `tests/test_187_neighbour_contact_rule.py`. There is one test
per AC. AC1, AC2 and AC4 share one module-scoped fixture that loads the split
case's image once. AC10 builds the findings of every case of both corpora once,
in a module-scoped fixture, through `measured_firing`'s dispatch (the detection
path each manifest entry names), not by re-implementing it.

**The AC3 map.** A constructed map from `tests.synthetic` helpers, 1 mm isotropic:
label 2 is a wall; label 1 has a large component (a 10×10×10 cube with one
10×10 face on the wall) and a separate small component (a 1×10×10 slab lying
flat on the wall, not touching the cube). Both contact areas are 100.0 mm²; the
small component's fraction is 100/240 and the cube's is 100/600. The test asserts
the equal contact areas and the ordering, not those literals.

**Correction (2026-09-27, builder hand-back on AC3).** The paragraph above does
not say where the slab sits, and it cannot be read literally: a single planar
wall carrying both a 10×10 cube face and a 10×10 slab face, with the two not
touching, needs a placement it never gives. The tests written from it put the
slab one voxel clear of the wall (`data[12] = 1` beside background at x=11 and
x=13), so its `contact_area_mm2` is 0.0 under A2 and AC3 is unsatisfiable. AC3
itself stands unchanged. The AC3 map, and the `spacing-read-from-header` map
built from it, is this construction, with the slab and the cube on opposite
sides of a one-voxel wall:

```python
data = np.zeros((12, 10, 10), dtype=LABEL_DTYPE)
data[0, :, :] = 1     # the slab, 1x10x10 (100 voxels)
data[1, :, :] = 2     # the wall
data[2:12, :, :] = 1  # the cube, 10x10x10 (1000 voxels)
```

The slab and the cube are two x-planes apart, so they are two components of
label 1 under `compute_components`' 6-connectivity (and would be under 26 too),
and `component_contacts` lists the cube first, then the slab (A1). Faces on the
image boundary count toward surface (A2). Expected values, verified by a numpy
probe of A2's definitions on 2026-09-27:

| Spacing | Component | `neighbour_label` | `contact_area_mm2` | `surface_area_mm2` | `contact_fraction` |
|---|---|---|---|---|---|
| (1.0, 1.0, 1.0) | cube | 2 | 100.0 | 600.0 | 1/6 = 0.16667 |
| (1.0, 1.0, 1.0) | slab | 2 | 100.0 | 240.0 | 5/12 = 0.41667 |
| (1.0, 2.0, 3.0) | cube | 2 | 600.0 | 2200.0 | 3/11 = 0.27273 |
| (1.0, 2.0, 3.0) | slab | 2 | 600.0 | 1300.0 | 6/13 = 0.46154 |

At (1.0, 2.0, 3.0) a wall face lies on axis 0 and has area 2.0 × 3.0 = 6.0 mm².
The cube's surface is 200 × 6.0 + 200 × 3.0 + 200 × 2.0, and the slab's is
200 × 6.0 + 20 × 3.0 + 20 × 2.0. The box-surface recomputation already in
`test_spacing_read_from_header` gives these values for this map unchanged. Only
the array construction in the two tests moves.

Named adversarial cases, and no others:

- `largest-component-not-read`: a constructed record whose label has
  `component_contacts[0].contact_fraction = 0.9` and every stray entry at `0.0`
  produces no `neighbour_contact` finding. It guards reading index 0, which would
  fire on `force_overlap` and on every real vertebra pressed against its
  neighbour (A5).
- `label-scope-not-read`: a constructed record with
  `label_contact_fraction = 0.9` and one stray entry at `0.0` produces no finding.
  It guards the rule firing on `split_own_label`'s own-label cap (A5).
- `just-above-threshold-fires`: the AC15 record with the threshold set 1e-9 below
  the recorded fraction produces exactly one finding. It guards AC15 passing
  because the rule never reads the configured threshold at all.
- `absence-tolerant`: a record whose `components` block has no
  `component_contacts` key produces no finding and does not raise. It guards the
  hand-built legacy components blocks across `tests_dir` (A7).
- `threshold-margin-on-the-committed-corpora`: over every stray component of
  every label of every committed fixture of both corpora, recomputed through
  `compute_components`, each `contact_fraction` is either at least
  `DEFAULT_CONTACT_FRACTION + 0.1` or at most `DEFAULT_CONTACT_FRACTION - 0.1`.
  It guards a corpus value drifting next to the threshold, the zero-margin trap
  item 166 recorded.
- `absolute-fields-unchanged`: for every label of the split case,
  `stray_contact_area_mm2` equals the maximum `contact_area_mm2` over
  `component_contacts[1:]` (0.0 for a single component). It guards step 1's
  rework moving the item-167 fields, which A4 keeps.
- `spacing-read-from-header`: the AC3 map rebuilt at spacing (1.0, 2.0, 3.0)
  gives surface and contact areas equal to the test's own per-axis recomputation.
  It guards an isotropic face-area assumption.

**Existing tests to reconcile.** Every test file under **May change** after
this module, for the reason given there. The grep behind that list covered rule
counts (`== 10`), exact rule-id enumerations, `fragmentation`'s mode 3 and its
`neighbour_contact` detector, `split`'s expected set, and the catalogue
leaf-path count. `tests/test_035_default_config.py`'s seven-section pins and
`tests/test_035_failure_modes.py`'s AC27 (a subset check) stay green unedited,
since no config section is added (A7).

`tests/test_163_specificity_ratchet.py` must stay green; it goes red if step 10's
`split` expected set is not re-authored.

## Validation

Replay the split case through the CLI:

```
.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/split_seg.nii.gz --out <tmp> --no-reference
```

Pass `--no-reference` for the reason `CLAUDE.md` gives: the bundled VerSe
reference is not calibrated for the synthetic corpus. Inspect
`<tmp>/segfacet_report.json`:

- `features.per_label` label 24's `components.component_contacts` has two
  entries; the second names `neighbour_label` 23 with a `contact_fraction` of
  about 0.33;
- label 23's `components.label_contact_fraction` is about 0.19;
- exactly one entry of `findings` has `rule_id == "neighbour_contact"`, on label
  24, and none has `rule_id == "fragmentation"`.

No environment profile is needed.

## Dependencies

- Item 186 — removed `split_own_label`'s spurious `coverage` firing, so the mode-3
  expected sets this item re-authors are measured after it (✅).

**Downstream:** items 188–195 re-author expected sets with the rule count at 11.
Stage 33 D4's generated `rules.generated.md` gains the new rule's row, and D5's
sign-off reads mode 3 through it.

## Decisions & Trade-offs

- **Implemented as specified, no deviations.** `ComponentContact`/
  `component_contacts`/`label_contact_fraction` land exactly per A1-A3;
  `compute_components` extends the existing item-167 per-component tally to
  run over every component (largest included) rather than only the strays,
  computing each component's surface alongside its neighbour-area tally in
  the same walk, then derives `stray_contact_area_mm2`/`stray_contact_label`
  from `component_contacts[1:]` (A4, unchanged values, verified against the
  split fixture and the whole corpus) and `label_contact_fraction` from the
  same per-component tallies summed (A3), with no second labelling pass.
- **Measured values matched the spec's predictions exactly** on re-run
  (2026-09-27, `.venv/bin/python`): the split case's label-24 stray
  component reads `contact_fraction=0.33168724279835393` (806.0/2430.0
  mm^2) and label 23's `label_contact_fraction=0.18588560885608857`; the AC3
  map's four (spacing, component) combinations reproduced the spec's table
  to the sixth decimal. No hand-back was needed.
- **`tests/corpus/119_pre_119_digests.json`'s `catalogue_leaf_path_set_sha256`
  recomputed** (item 121's standing obligation, explicitly authorised
  here): `477a4be8e34d7f669ec1bdb49cc5386ca21096bf76f53c7ba1d070e49ce77798`,
  replacing the item-167 value, since the catalogue's leaf-path set gained
  five entries (140 -> 145).
- **Regeneration verified byte-reproducible**: `segfacet.synth.corpus` was
  run twice into separate temp directories and byte-compared (identical),
  and every fixture in that run byte-matches the committed
  `tests/corpus/fixtures/` (A8) -- only `manifest.json`'s `split` entry
  moved (`"fragmentation"` -> `"neighbour_contact"`).
- **Follow-up for validation, not fixed here**: `tests/test_148_per_path_mode_attribution.py`
  is listed in this item's Authorised paths for reconciliation as a moved
  literal, but this builder pass found it still hardcodes the pre-item-187
  registry shape in several places -- `_EXPECTED_THRESHOLD_CONSTANTS` has no
  `neighbour_contact` entry (so `_RULE_MODULE_NAMES` stays at 10 and two
  `checked == 10` asserts, lines ~363, ~1024, ~1058, don't see the eleventh
  rule) and `test_ac19_realised_universe_unchanged_and_item104_reports_no_drift`
  still asserts `len(cat.entries) == 140`. Builders don't write tests
  (framework rule), so this is left for the validator to route back to
  test-writer rather than fixed here.

- **Left open:** mode 3 sub-type (b), `split_own_label`, is still seen only by
  `bounds`. Its cap is its own label's only component, so the stray reading is
  silent. The label-scope fraction does separate it on this corpus (0.3317 against
  at most 0.1956 elsewhere), but only by 0.14, and a real vertebra pressed against
  its neighbour reads the same way. Whether a label-scope detector serves
  sub-type (b) is a measurement question for the at-the-bar review, not this
  item's.
- **Left open:** the label scope reports the fraction only, not the neighbour,
  and against the single most-contacted neighbour, not all neighbours together
  (A3). No consumer in this queue reads it. A merge-guidance consumer that needs
  either is the one to decide.
- **Validator round 1 (2026-09-28): mode 3's mechanism prose named
  fragmentation's catalogue path while explaining its silence on the split
  case, tripping AC31** (fragmentation is no longer one of mode 3's declared
  rules post-move, so naming its `feature_paths`-eligible path there is
  disallowed). Reworded to name the rule/detector in prose
  ("mode 1's Fragmentation: detector (the fragmentation rule's per-label
  fragmentation index)") instead of the literal
  `per_label.{label}.components.fragmentation_index` string. Regenerated
  `docs/aide/failure_modes.generated.{json,md}` and
  `docs/aide/traceability_matrix.generated.{json,md}` via
  `.venv/bin/python -m segfacet.failure_modes` and
  `.venv/bin/python -m segfacet.traceability`; no other generated artifact
  embeds this mechanism text.
