<!-- aide-template: item 3 -->
# Item 219 — One check per failure mode for label order and label-set gaps

> **Created:** 2026-10-12 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-030.md`](../queue/queue-030.md) · Item 219
> **Objectives:** G2, G3
> **Suggested branch:** `aide/219-one-check-per-mode-9-and-10`

---

## Description

Insight `2026-09-29-a832` records two pairs of rules that implement the same
check:

- **Mode 9** (labels out of order along the spine): `mislabel`'s `ordering`
  detector reads `pairs.adjacent.non_monotonic_pairs[]`, which is position
  along item 210's label-free path. `sequence`'s `swap` and `shift`
  detectors (item 192) sort centroids by `centroid_mm[2]`.
- **Mode 10** (a gap in the label set): `coverage`'s `missing_interior` and
  `sequence`'s `skip` both report the same label gap.

The z-sort is not robust to curvature or pose. On correctly labelled spines
it fires `shift`, and sometimes `swap`, where the path-based check reads
nothing (A2). Item 210 made the path-based check label-free, which the
insight named as the precondition.

This item makes six changes, all decided by the maintainer on 2026-10-12:

1. **Mode 9 belongs to `mislabel`'s `ordering`.** `sequence`'s `swap` and
   `shift` detectors are retired, not re-based on path position. Re-basing
   them would leave three detectors on mode 9.
2. **Mode 10 belongs to `coverage`'s `missing_interior`.** `sequence`'s
   `skip` detector is retired.
3. **`coverage`'s `count_shortfall` and `incomplete_span` become mode-less.**
   Each gets a detector-level `mode_less_reason`: they are opt-in curation
   checks against a configured expectation, not a label-map failure mode.
   Mode 10 is then declared against exactly one detector.
4. **`sequence`'s `transitional` detector skips every level named in
   `pairs.adjacent.non_monotonic_pairs[]`.** Today it skips the levels
   `swap`/`shift` named. Without a replacement, `sequence_break`'s T13 would
   fire `transitional` (mode 11) on a mode-9 case (A3), against mode 11's
   own discriminator ("a T13 below an L-level is out of order, not a
   variant").
5. **`sequence`'s `displaced_vertebra` opt-in is removed.** It existed for
   the swap finding, and the rule no longer reads centroids.
6. **The owner's line is appended to the override.** In
   `feature_docs.STATUS_OVERRIDES["case.curve.is_monotonic"]`, the dated line
   of 2026-10-12 goes after the unchanged item-106 note (insight
   `2026-10-09-9de3`).

`failure_modes.py`'s declarations follow from these changes:

- Mode 9 keeps one edge, `mislabel`/`ordering`.
- Mode 10 keeps one edge, `coverage`/`missing_interior`.
- `sequence` declares mode 11 only.
- `sequence_break` designates `mislabel` with expected labels {20, 28}.
- `remove_level` drops `sequence` from its expected firing.

**Not in scope.**

- `pairs.adjacent.non_monotonic_pairs[]`, `per_label.{label}.curve.path_u`
  and `features/**` are unchanged (A5).
- `mislabel`'s `ordering` detector is unchanged in what it fires on.
- `case.sequence.missing_levels[]` keeps its meaning, so the mode-10/11
  double report stays (Left open).
- `coverage`'s two opt-in detectors keep their behaviour; only their
  declaration changes.
- Mode 6's edges, its corpus case `remove_level_relabel`, and
  `remove_level`'s designated rule are item 218's.
- `src/segfacet/synth/corpus.py` and the `relabel_swap` expectation's
  `detail` are item 227's.

## Acceptance Criteria

Terms used below:

- **"Both corpora"** are `segfacet.synth.corpus.load_manifest()["cases"]`
  (geometric) and `tests/corpus/intensity/manifest.json`'s `cases`.
  Findings come from `segfacet.synth.regression.pipeline_findings` and
  `intensity_pipeline_findings` respectively.
- **"The order rules"** are `{"mislabel", "sequence", "coverage"}`.
- **"The curved spine"** is item 210's `ARC`: ten centroids T8–L5 on a 210°
  arc of radius 60 mm in the y–z plane, centroid `i` at
  `(0, 60·cos t, 60·sin t)` with `t = radians(-90 + 210·i/9)`.
- **"The reclined spine"** is ten centroids T8–L5 (labels 15–24) on a 90° arc
  of radius 150 mm whose chord lies 10° from horizontal. Centroid `i` (0–9)
  has `t = radians(135 - 10·i)`, `y = 150·cos t` and `z = 150·sin t`, then
  is rotated 10° about x: `(0, y·cos 10° − z·sin 10°, y·sin 10° + z·cos 10°)`.
- **"A spine record"** is built from such centroids, listed in T8→L5 order,
  as:

  ```
  {"per_label": {...},
   "pairs": {"adjacent": {"non_monotonic_pairs": [...]}}}
  ```

  - `per_label` maps each label to
    `{"label", "level_name", "centroid": {"centroid_mm": [...]}}`.
  - `non_monotonic_pairs` is
    `compute_monotonic_consistency(centroids, None).non_monotonic_pairs`,
    each pair as a list. This is the producer's output, in the order the
    pipeline hands it the centroids.

- [ ] **AC1: mode 9 is declared against one detector.** The set of
  `(edge.rule_id, detector_id)` pairs over every `IntendedRule` edge of
  `segfacet.failure_modes.SPECIFICATION[9]` equals
  `{("mislabel", "ordering")}`.
- [ ] **AC2: mode 10 is declared against one detector.** The same set for
  `SPECIFICATION[10]` equals `{("coverage", "missing_interior")}`.
- [ ] **AC3: `sequence` declares only `transitional`.** The `detector_id`s
  of the registered `sequence` rule's `mode_declaration.detectors` equal
  `{"transitional"}`.
- [ ] **AC4: `sequence` declares mode 11 only.** The registered `sequence`
  rule's `mode_declaration.modes == (11,)`.
- [ ] **AC5: `count_shortfall` is mode-less.** The `coverage` rule's
  `count_shortfall` detector has a non-empty `mode_less_reason`.
- [ ] **AC6: `incomplete_span` is mode-less.** The `coverage` rule's
  `incomplete_span` detector has a non-empty `mode_less_reason`.
- [ ] **AC7: `sequence` opts in to no condition.** The registered `sequence`
  rule's `condition_opt_ins == ()`.
- [ ] **AC8: a curved spine fires no ordering finding.**
  `segfacet.heuristics.run_rules(<the curved spine record>, bundled_default_config())`
  returns no finding whose `rule_id` is in the order rules.
- [ ] **AC9: a reclined spine fires no ordering finding.** The same holds for
  the reclined spine record.
- [ ] **AC10: the order rules fire exactly where expected.** Over both
  corpora, the set of `(case_id, rule_id, detector_id, labels)` tuples taken
  from every finding whose `rule_id` is in the order rules equals:
  - `("relabel_swap", "mislabel", "ordering", frozenset({21, 22}))`
  - `("sequence_break", "mislabel", "ordering", frozenset({20, 28}))`
  - `("remove_level", "coverage", "missing_interior", frozenset())`
- [ ] **AC11: `sequence_break` designates `mislabel`.** The geometric
  manifest entry with `case_id == "sequence_break"` has
  `expected_rule_ids == ["mislabel"]`.
- [ ] **AC12: `sequence_break` names the ordering pair.** The same entry has
  `sorted(expected_labels) == [20, 28]`.
- [ ] **AC13: the override carries the owner's line.**
  `segfacet.feature_docs.STATUS_OVERRIDES["case.curve.is_monotonic"]` equals:

  ```
  ("retune",
   "Should be wired into the sequence rule directly; "
   "sequence-related checks should typically verify order along the "
   "spline parameter, not only label order. "
   "2026-10-12: Done: order is judged along the label-free path by "
   "`mislabel`, items 210/219.")
  ```

  The item-106 note is unchanged, and the dated line follows it after one
  space.

Why each is written:

- **AC1 and AC2** are the queue's "each of modes 9 and 10 is declared
  against exactly one detector".
- **AC3 and AC4** are the retirement itself. Without AC3 a retired detector
  could stay declared and be excused some other way.
- **AC5 and AC6** are the maintainer's Q2 answer, which AC2 needs: test_164
  AC8 fails on any declared detector that no edge names and no
  `mode_less_reason` excuses.
- **AC7** is the opt-in removal. test_191 AC10 keeps the specification's
  `opting_in_rules` in step with the registry, but not whether `sequence` is
  in it.
- **AC8 and AC9** are the queue's "a curved or reclined spine, correctly
  labelled, fires no ordering finding". Both fail today: `sequence` fires
  `shift` on the curved spine (L5), and `shift` (L5) plus `swap` (L1, L4) on
  the reclined one (A2).
- **AC10** covers three of the queue's testable claims in one measured
  equality:
  - every case that expected a mode-9 or mode-10 detection still has one;
  - `sequence` is silent on every case, `sequence_break` included (Q3);
  - `remove_level` keeps `coverage`.

  It fails today on the three `sequence` findings.
- **AC11 and AC12** are the designation the maintainer chose.
- **AC13** is the queue's last testable claim, as an equality.

Not written, because an existing test already fails without them:

- **"Every corpus case's measured firing equals its expected set."**
  `tests/test_147_specification_is_the_record.py::test_ac26_every_corpus_case_agrees_and_status_derives_correctly`
  asserts `case_agrees` for every case, so `relabel_swap`, `sequence_break`
  and `remove_level`'s `expected_firing` must move with the firing.
- **"The manifest's labels and verdicts match the pipeline."**
  `tests/test_041_regression_suite.py` (`verify_case`).
- **"No case fires a rule it does not expect."**
  `tests/test_163_specificity_ratchet.py`.
- **"The condition's opt-in list matches the registry."**
  `tests/test_191_condition_gate.py::test_ac10_specification_records_the_registrys_opt_ins`.

No AC closes a Stage 34 criterion. This is a maintenance item.

## Assumptions

`loop.clarify` was forced to interactive for this batch. The maintainer
answered on 2026-10-12:

- Mode 9: retire `swap`/`shift`, no re-basing, and the opt-in goes with them.
- Q1(a): `coverage`/`missing_interior` keeps mode 10, and `sequence`/`skip`
  is retired.
- Q2(a): `count_shortfall` and `incomplete_span` each get a
  `mode_less_reason`.
- Q3(a): `transitional` skips levels named in `non_monotonic_pairs[]`.
- F6: the owner's line is appended, and test_132 AC30 is reconciled.

Every number below was measured on `aide/queue-030` at `2a1491d` on
2026-10-12 with `.venv/bin/python`. The scratch probes simulated the change
by patching `SequenceRule` in memory. The builder re-measures on the real
change.

- **A1 (measured: today's firing of the order rules).** Over both corpora,
  only three cases fire them:
  - `relabel_swap`: `mislabel`/`ordering` {21, 22} and `sequence`/`swap`
    {21, 22}.
  - `sequence_break`: `mislabel`/`ordering` {20, 28} and `sequence`/`shift`
    {28}.
  - `remove_level`: `coverage`/`missing_interior` and `sequence`/`skip`, both
    with no labels.

  Under the simulated change, exactly AC10's three tuples remain. Every
  verdict is unchanged: the three cases stay `flagged-for-review`. The
  intensity corpus fires none of these rules either before or after.
- **A2 (measured: the z-sort fails on correctly labelled spines).** For each
  geometry, `sequence` today, then the label-free path:
  - The curved spine: `shift` on L5. `non_monotonic_pairs == ()`.
  - The reclined spine: `shift` on L5 and `swap` on L1/L4.
    `non_monotonic_pairs == ()`.
  - A 90° arc swept through every tilt from 0° to 180°: the z-sort fires at
    0–40° and 150–180° from horizontal. The path reads `()` at every tilt.

  Rotating the clean-control map's affine fires neither, because five
  near-straight lumbar levels never break the z-sort. That is why AC8 and
  AC9 use spine records rather than a label map.
- **A3 (measured: why `transitional` needs a new exclusion).** With
  `swap`/`shift` gone and nothing in their place, `sequence_break` fires
  `transitional` on T13 (label 28): T13 is an uncorroborated thoracic count
  of 13.
  - With Q3's exclusion, `sequence_break` fires nothing from `sequence`.
  - `mislabel`'s pair on that case is `(T13, L1)`, labels 28 and 20.
  - item 192's in-order uncorroborated T13 and T11 maps (test_192 AC4 and
    AC5) have empty `non_monotonic_pairs`, so `transitional` still fires
    there.
- **A4 (measured: `sequence_break` with other targets).** Under the
  simulated change, `SequenceBreakPerturbation` fires
  `mislabel`/`ordering` {20, 28} for each of target 21, 22 and 23, beside
  `coverage`/`missing_interior`. Target 21 also fires `spline_offset` on 20.
  The pair is always (T13, the next present level after T13 in
  `CANONICAL_ORDER`), which is how step 5 computes `expected_labels`.
- **A5 (pins the interface item 218 reads; this item is its producer of
  record).** This item keeps both of these unchanged:
  - `mislabel`/`ordering`: what it fires on and its `detector_id`.
  - `pairs.adjacent.non_monotonic_pairs[]`: consecutive `(level_a, level_b)`
    pairs in `CANONICAL_ORDER` order whose `path_u` does not advance (its
    `FEATURE_DOCS` entry).

  `transitional` reads that field as bookkeeping, through
  `record["pairs"]["adjacent"]["non_monotonic_pairs"]`. A record without it
  (no `pairs`, or no `adjacent`) excludes nothing.
- **A6 (decided: `sequence` stops reading centroids).** The kept-entry gate
  drops its `centroid.centroid_mm` requirement. An entry is kept when it is
  a mapping, its `level_name` is a recognised vertebra name, and its `label`
  is an integer. `transitional` reads level names only.
  - `consumed_paths` drops `per_label.{label}.centroid.centroid_mm[]`.
  - It adds `pairs.adjacent.non_monotonic_pairs[]` as bookkeeping, with the
    reason "gate: levels mislabel's ordering detector names are mode 9's,
    not a numbering variant".
  - If item 218 has not landed, `centroid_mm[]` is then read by no rule.
    The regenerated catalogue records whichever is true.
- **A7 (decided: the `mode_less_reason` texts).**
  - `count_shortfall`: "opt-in curation check against a configured minimum
    level count (expected_count); off by default and judges the dataset's
    coverage, not a label-map failure mode".
  - `incomplete_span`: "opt-in curation check against configured expected
    levels beyond the present span; off by default and judges field-of-view
    coverage, not a label-map failure mode".

  `coverage`'s rule-level `modes` stays `(10,)`. A detector-level
  `mode_less_reason` on a rule that declares modes is what
  `RuleDetector`'s docstring provides for. Every shipped precedent is on a
  mode-less rule, so the builder confirms that `aide check` and the
  regenerated traceability matrix accept it. The builder hands back if a
  validator rejects it.
- **A8 (decided: the catalogue's mode attribution moves only through
  declarations).** The catalogue attributes modes per rule, not per
  detector. So `case.sequence.present_levels[]`, a `coverage` signal path
  read only by the two now mode-less detectors, keeps mode 10 through
  `coverage`'s rule-level declaration. This is recorded, not changed
  (Left open).
- **A9 (decided: test_103 AC13's witness filter).** `sequence` now consumes
  `pairs.adjacent.non_monotonic_pairs[]` as bookkeeping. So `mislabel`'s
  only signal path is no longer consumed by `mislabel` alone.
  - test_103's AC13 asks for "a signal-classified entry consumed only by"
    each mapped rule. It is restated as "an entry this rule classifies
    `signal` and every other consuming rule classifies `bookkeeping`".
  - A bookkeeping read contributes no mode (item 148). The builder confirms
    that on the regenerated catalogue: `non_monotonic_pairs[]`'s
    `failure_modes` must stay `mislabel`'s plus its anchor's. Hand back if
    it does not.
  - `feature_docs.py`'s module docstring sentence calling it "the *only*
    leaf path exclusively consumed by `mislabel`" is corrected to match.
- **A10: no human gate and no environment-gated capability.** No mode
  sign-off covers modes 9, 10 or 11 (`MODE_SIGN_OFFS` holds 2, 3 and 4), so
  nothing is re-signed.

## Implementation Steps

1. **`src/segfacet/heuristics/sequence.py`**:
   - Delete `_ORDER_TAG`, `_SKIP_TAG`, `_inversions`, `_head_to_tail`,
     `_swaps_and_shifts`, `_skip_names` and the `shift`, `skip` and `swap`
     branches of `evaluate`.
   - Remove `condition_opt_ins`.
   - Keep `_RANK`, `_BASE_RANK`, `_element`, `_reading` and
     `_transitional_names`.
   - In `evaluate`:
     - Build `present_names` with A6's gate.
     - Read the excluded names as every level named in
       `pairs.adjacent.non_monotonic_pairs[]` (A5; absent means none).
     - Pass them to `_transitional_names` where `named_names` went.
   - `mode_declaration`:
     - `modes=(11,)`.
     - Evidence: analytic. No committed case designates the rule; the A3
       measurement is named.
     - `consumed_paths` per A6.
     - One `RuleDetector`, `transitional`, whose `fires_when` says
       "excluding levels named in `pairs.adjacent.non_monotonic_pairs[]`".
   - Rewrite the module and class docstrings: the rule now reads only level
     names, item 219 retired three detectors, and the A2/A3 measurements.
2. **`src/segfacet/heuristics/coverage.py`**:
   - Add A7's `mode_less_reason` to the `count_shortfall` and
     `incomplete_span` detectors.
   - Rewrite the module docstring's mode-10 sentence: `missing_interior`
     alone serves mode 10.
   - Rewrite the evidence string's last sentence: "The two opt-in checks …
     serve the same mode" becomes mode-less.
   - Leave the comment above `mode_declaration` to item 218.
3. **`src/segfacet/heuristics/mislabel.py`**:
   - The evidence names `sequence_break` beside `relabel_swap`.
   - The module docstring records that mode 9 is this rule's alone since
     item 219.
   - No behaviour change.
4. **`src/segfacet/failure_modes.py`**:
   - `_MODE_9`:
     - Drop the `sequence` `IntendedRule`.
     - Rewrite the mechanism around `mislabel`'s ordering alone. It keeps
       the tokens `CANONICAL_ORDER` and `T13`, which
       `tests/test_138_traceability_matrix.py` checks, and records that the
       z-sort detectors were retired by item 219 and why (A2).
     - Both corpus cases' `expected_firing` becomes `("mislabel",)`. Their
       reasons are re-measured and dated 2026-10-12, item 219.
   - `_MODE_10`:
     - The `coverage` edge's `detector_ids` becomes `("missing_interior",)`.
     - Drop the `sequence` edge.
     - Remove `skip` from the mechanism.
   - `_MODE_11`: the mechanism adds the `non_monotonic_pairs[]` exclusion
     (A3).
   - `_MODE_6`'s `remove_level` entry: **drop `"sequence"` from
     `expected_firing`**, leaving whatever else is there (item 218 may have
     added `centroid_spacing`). Remove the `skip` co-detection from its
     reason and from mode 6's mechanism.
   - `CONDITIONS["displaced_vertebra"]`: drop `"sequence"` from
     `opting_in_rules`, and the sentence about it in the definition.
   - Correct the module docstring wherever it describes `swap`/`shift`/`skip`
     as live. Add one item-219 paragraph.
5. **`src/segfacet/synth/identity_ordering_alignment.py`**, in
   `SequenceBreakPerturbation` only:
   - `expected_rule_ids=frozenset({"mislabel"})`.
   - `expected_labels` is `{new_label, n}`, where `n` is the label right
     after `new_label` in
     `segfacet.labels.anatomical_order({l: DEFAULT_LABEL_MAP[l] for l in <labels after the relabel>})`
     (A4). If `new_label` is last in that order, it stays `{new_label}`.
   - Rewrite the `detail` and the class docstring: `mislabel`'s ordering
     detector catches it, not `sequence`.
   - The `relabel_swap` expectation is item 227's and is left alone.
6. **`src/segfacet/feature_docs.py`**:
   - Append AC13's dated line to the `case.curve.is_monotonic` override.
     The item-106 text is untouched.
   - Correct the module docstring's mode-8 sentence (A9) and mode-9
     sentence. The mode-9 sentence should say that `sequence` no longer
     reads `per_label` centroids and that `mislabel` reads
     `non_monotonic_pairs[]`.
7. **`src/segfacet/default_config.yaml`**: the comment above `sequence:`
   names only the `transitional` sub-type. It stays a comment, so
   `config_hash` does not move.
8. **Regenerate.** Run each generator twice into scratch paths, byte-compare
   the two runs, then write the committed copies:
   - `.venv/bin/python -m segfacet.synth.corpus`: the manifest only. The
     fixtures must not change; hand back if one does.
   - `-m segfacet.failure_modes`
   - `-m segfacet.traceability`
   - `-m segfacet.catalogue`
   - `-m segfacet.rule_table`
   - `-m segfacet.golden_evidence`, which may be byte-identical.
9. **Reconcile the existing tests** listed under Testing Strategy. Add a
   dated `# Item 219 (2026-10-12): ...` line beside each changed value.
10. Run `python .aide/scripts/aide.py scope 219` and
    `python .aide/scripts/aide.py check`. Neither may report an error.

No dependency is added. Every helper is already in the tree:
`compute_monotonic_consistency`, `anatomical_order`, `DEFAULT_LABEL_MAP`,
`resolve_section_counts` and `expected_level_sequence`.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/sequence.py` — three detectors retired, the exclusion, the declaration (step 1).
- `src/segfacet/heuristics/coverage.py` — two `mode_less_reason`s and the docstring and evidence (step 2).
- `src/segfacet/heuristics/mislabel.py` — evidence and docstring (step 3).
- `src/segfacet/failure_modes.py` — modes 6, 9, 10 and 11, the condition, the docstring (step 4).
- `src/segfacet/synth/identity_ordering_alignment.py` — the `sequence_break` expectation and docstring (step 5).
- `src/segfacet/feature_docs.py` — the override line and two docstring sentences (step 6).
- `src/segfacet/default_config.yaml` — one comment (step 7).
- `tests/corpus/manifest.json` — regenerated (step 8).
- `docs/aide/failure_modes.generated.json` — regenerated (step 8).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 8).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 8).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `docs/aide/rules.generated.md` — regenerated (step 8).
- `docs/aide/golden_evidence.generated.json` — regenerated if it moves (step 8).
- `tests/test_219_one_check_per_mode.py` — **new**: this item's test module.
- `tests/test_030_sequence_continuity.py` — reconcile (swap/shift/skip assertions).
- `tests/test_035_failure_modes.py` — reconcile (the mode-7 seed record fired `sequence`'s swap).
- `tests/test_038_coverage_border_overlap_perturbations.py` — reconcile (remove_level's fired-rule set).
- `tests/test_039_identity_ordering_alignment_perturbations.py` — reconcile (sequence_break's expectation and findings).
- `tests/test_098_stray_components.py` — reconcile (three sequence findings in the shared constant).
- `tests/test_103_feature_catalogue.py` — reconcile (AC10 row, `_RULE_MODE_MAP`, AC13 filter).
- `tests/test_116_ras_native_corpus.py` — reconcile (the item-192 sequence pairs against the aeb2f55 golden).
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — reconcile (three cases' finding sets).
- `tests/test_132_monotonicity_against_traversal_order.py` — reconcile (AC13, AC25, AC30).
- `tests/test_136_rule_mode_declarations.py` — reconcile (`_CORROBORATED`, catalogue counts if they move).
- `tests/test_137_mode_less_rule_disposition.py` — reconcile only if the regenerated catalogue moves a bucket it pins.
- `tests/test_138_traceability_matrix.py` — reconcile (mode 9's sequence edge, the analytic witness, the mixed set).
- `tests/test_145_eight_hypothesised_modes.py` — reconcile (mode 9's sequence edge; mode 10's rule set).
- `tests/test_147_specification_is_the_record.py` — reconcile (AC11 sequence-caps-nothing).
- `tests/test_148_per_path_mode_attribution.py` — reconcile (AC16's sequence driver).
- `tests/test_149_conformance_report.py` — reconcile (mode 9's read path).
- `tests/test_188_coverage_rehomed.py` — reconcile (AC2 and AC4: coverage's mode-10 detectors).
- `tests/test_192_sequence_sub_types.py` — reconcile (the retired sub-types).
- `tests/test_220_collapsed_labels_rule.py` — only if red: item 220 pins the manifest and test_129 as unmoved, and this item, landing after it, moves both (Dependencies).

**Asserts against:**

- `tests/corpus/fixtures/**` — AC10 reads the committed fixtures; step 8 must not change them.
- `tests/corpus/intensity/manifest.json` — AC10 drives the intensity cases; none may fire an order rule.
- `tests/test_163_specificity_ratchet.py` — must stay green unedited: no case fires a rule it does not expect.
- `tests/test_164_detector_ids.py` — must stay green unedited: every declared detector is named by an edge or excused.
- `tests/test_191_condition_gate.py` — must stay green unedited: the condition's opt-ins match the registry.
- `tests/test_202_rule_table.py` — must stay green unedited once step 8 regenerates `rules.generated.md`.
- `tests/test_104_feature_catalogue_drift.py` — must stay green unedited once step 8 regenerates the catalogue.
- `tests/test_210_label_free_monotonic_reference.py` — must stay green unedited: `ordering` and `non_monotonic_pairs[]` keep their meaning (A5), and AC8 reuses its `ARC`.

## Testing Strategy

The test module is `tests/test_219_one_check_per_mode.py`, with one test per
AC.

- AC8 and AC9 build the spine records from `LabelCentroid`s and take
  `non_monotonic_pairs` from `compute_monotonic_consistency`, never from a
  hand-typed list.
- AC10 reads every case through the `regression` harness.
- AC11 and AC12 read the committed manifest through `load_manifest`.

Adversarial cases, each with the failure mode it guards, and no others:

- `unrelated-pair-does-not-silence-transitional`: a `per_label` record of
  T10, T11, L1, L2, L3 (labels 17, 18, 20, 21, 22) with
  `pairs.adjacent.non_monotonic_pairs == [["L2", "L3"]]`. The `sequence`
  rule returns exactly one `transitional` finding on `frozenset({18})`. It
  guards an exclusion that silences `transitional` whenever any pair exists,
  or that excludes every present level.
- `pair-member-excluded-from-transitional`: a `per_label` record of L1, L2,
  L3, L4, T13 (labels 20, 21, 22, 23, 28) with
  `pairs.adjacent.non_monotonic_pairs == [["T13", "L1"]]`. The `sequence`
  rule returns `[]`. It guards an exclusion read from the wrong key, or from
  the pair's second member only. Measured 2026-10-12: without the pairs
  block the same record yields `transitional` on T13, so the exclusion is
  what silences it.

**Existing tests to reconcile.** These were found on 2026-10-12 by grepping
`tests/` for:

- the retired detector ids and reason tags;
- `SequenceRule`, `"sequence"` as a rule id, `count_shortfall`,
  `incomplete_span` and `opting_in_rules`;
- mode 9/10 edge pins and the per-path catalogue counts.

The list is a lower bound (`CLAUDE.md`, "A spec-time probe ... is a lower
bound"). **The fence:** an edit either drops a retired `sequence` finding or
edge from a pinned value, re-points a pin from `sequence` to
`mislabel`/`ordering`, or retires an assertion about a retired detector,
with a dated note. Nothing else is loosened. A red test outside this list
gets the same treatment, or a hand-back.

- **`test_192`**:
  - Retire AC1 (`swap`), AC2 (`shift`), AC3 (`skip`), AC7 (`sequence_break`
    as `shift`), AC10 (swap beside a displaced reading) and
    `test_sacral_labels_share_one_rank` (`skip`).
  - AC8 becomes `(11,)`. AC9 becomes `{"transitional": (11,)}`.
  - AC4, AC5, AC6, `test_lumbar_reading_uncorroborated`,
    `test_no_centroid_no_finding`, `test_full_reversal_reads_as_flipped` and
    `test_ascending_fixture_fires_no_sequence` stay as they are.
- **`test_030`**:
  - Retire AC3–AC5 (swap on L1/T12) and AC6 (skip plus swap).
  - Retire the L730–745 test (shift plus skip).
  - AC1, AC2, AC7 and the tolerance tests stay.
- **`test_035_failure_modes`**: the vision-seed "mode 7" record and AC25 now
  expect `mislabel`. Give the record `pairs.adjacent.non_monotonic_pairs`
  from `compute_monotonic_consistency` over its own centroids, in anatomical
  order. The `_MODE_RECORDS_AND_RULE_IDS` row for 7 becomes `mislabel`.
- **`test_039`**:
  - AC16 becomes `mislabel`/`ordering` on {20, 28}.
  - AC17 becomes `{"mislabel"}`.
  - AC18 becomes `expected_rule_ids == {"mislabel"}` and
    `expected_labels == {20, 28}`.
  - `_designated_rule_fires_run_qc` checks a `mislabel` finding whose labels
    equal `expectation.expected_labels`.
  - The interior-target adversarial asserts `mislabel` and `coverage` (A4).
- **`test_038`** AC5: the fired-rule set is `{"coverage"}`, plus whatever
  item 218 adds if it has landed.
- **`test_098`** `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`: drop the three
  `sequence` findings (`relabel_swap` swap, `remove_level` skip,
  `sequence_break` shift). Items 218 and 224 also edit this module.
- **`test_129`** `_PRE_129_FINDINGS`: drop `("sequence", …)` from
  `relabel_swap`, `remove_level` and `sequence_break`.
- **`test_132`**:
  - AC13: one finding, `mislabel`.
  - AC25: `relabel_swap`'s pinned set is `{("mislabel", (21, 22))}`.
  - AC30: `case.curve.is_monotonic`'s note must *start with* the pre-item
    text and the status stays `"retune"`. The `path_u` entry stays
    byte-identical.
- **`test_116`**: drop `_ITEM_192_ADDED_SEQUENCE_PAIRS`' two entries. Record
  `sequence_break`'s `("sequence", (28,))` as removed against the aeb2f55
  golden, as a dated item-219 map beside the item-198 one. The test is
  git-gated (`aeb2f55` must be reachable), so run it from a real clone.
- **`test_103`**:
  - AC10: drop the `("per_label.{label}.centroid.centroid_mm[]", "sequence")`
    row, or re-point it to `centroid_spacing` if item 218 has landed.
  - `_RULE_MODE_MAP`: drop `"sequence": (9,)`.
  - AC13: restate the witness filter per A9.
- **`test_136`**:
  - `_CORROBORATED["sequence"]` becomes `(11,)`.
  - The catalogue counts (`len(entries)`, `stayed_empty`) are re-measured
    from the regenerated catalogue.
- **`test_138`**:
  - The mode-9 rung test drops the `edge_rungs["sequence"]` and
    `"needs-real-data" in mechanism` assertions; the mode rung stays
    `synthetic-demonstrable`.
  - The analytic witness drops `(10, "sequence")`.
  - `mixed` becomes `{"bounds"}`.
  - The anchor-not-consumed fixture's `declared_rules` and
    `co_detecting_rules` become `{"mislabel"}`.
- **`test_145`**:
  - The mode-9 rung test asserts the single `mislabel` edge at
    `synthetic-demonstrable` and `"mislabel" in measured(sequence_break)`.
  - Mode 10's rule sets become `{"coverage"}`.
- **`test_147`** AC11 (`sequence` caps nothing): retire it. Its subject, one
  swap finding folding every offender, is gone.
- **`test_148`** `_AC16_CASES`: `sequence_break` drives `mislabel`, and
  `relabel_swap` stays. Add a planted-record row for `sequence`, built like
  `_overlap_reconstructed_record`, from the
  `unrelated-pair-does-not-silence-transitional` record. Without it, AC16's
  every-rule-is-driven check loses `sequence`.
- **`test_149`** AC9: mode 9's read path becomes
  `pairs.adjacent.non_monotonic_pairs[]`.
- **`test_188`**:
  - AC2: the edge's `detector_ids` becomes `("missing_interior",)`.
  - AC4 (every coverage detector serves mode 10 alone) is restated:
    `missing_interior` serves `(10,)`, and the two opt-in detectors serve
    `()` with a `mode_less_reason`.

Red until step 8's regeneration lands, with no test edit: the drift tests
that compare a committed generated document with a fresh render
(`test_104`, `test_202`, and the failure-mode and traceability drift
tests).

## Validation

Replay the two mode-9 cases and the mode-6 case through the CLI.
`--no-reference` is needed for the reason `CLAUDE.md` gives.

```
.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/sequence_break_seg.nii.gz --out <tmp1> --no-reference
.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/relabel_swap_seg.nii.gz --out <tmp2> --no-reference
.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/remove_level_seg.nii.gz --out <tmp3> --no-reference
```

- `<tmp1>`: one finding, `mislabel`, reason starting `Vertebra ordering
  inconsistent with label:`, on labels 20 and 28. No `sequence` finding.
  Verdict `flagged-for-review`.
- `<tmp2>`: one `mislabel` finding on 21 and 22. No `sequence` finding.
- `<tmp3>`: `coverage`'s `Missing interior level(s):` finding, plus item
  218's rule if it has landed. No `sequence` finding.

Record the three outcomes with the commit in Decisions & Trade-offs.

## Dependencies

- Item 220: its Asserts against pins `tests/corpus/manifest.json` ("no
  case's firing may move") and
  `tests/test_129_coincident_centroids_and_held_out_floor.py` as unedited,
  and this item changes both. This item lands after it.

**Downstream:**

- Item 218 reads A5's interface: `mislabel`/`ordering` and
  `pairs.adjacent.non_monotonic_pairs[]` keep their meaning. Both items
  edit `failure_modes.py` (mode 6's mechanism and `remove_level`'s expected
  set, mode 10's mechanism) and reconcile `test_038`, `test_098`,
  `test_103`, `test_129` and `test_136`. Step 4 drops `"sequence"` from
  `remove_level`'s expected set rather than rewriting it, so either order
  composes. Whichever lands later re-measures and regenerates.
- Item 227 edits the `relabel_swap` expectation in the same synth module
  and regenerates the manifest.
- Item 224 edits `tests/test_098_stray_components.py`.
- Item 223 re-attributes catalogue reads, and sees this item's
  consumed-path changes (A6).

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** the mode-10/11 double report. On 2026-10-12 the label-set
  sweep found 1,183 of 16,368 sets where they differ, and every difference
  is an uncorroborated short section: T11 as the last thoracic level with
  no C7, or L4 as the last lumbar level beside S1.
  - `missing_interior` reports T12 or L5 missing (mode 10).
  - `transitional` flags the T11 or L4 reading (mode 11).
  - `case.sequence.missing_levels[]` is built under the default section
    counts. Making it use `transitional`'s reading would change a record
    field and every report built from it, so it was not done here.
- **Left open:** `case.sequence.present_levels[]` keeps mode 10 in the
  catalogue through `coverage`'s rule-level declaration, although only the
  two now mode-less detectors read it (A8). Per-detector catalogue
  attribution is a catalogue design question.
- **Left open:** the `case.curve.is_monotonic` override keeps status
  `retune` beside a note that now reads "Done". The status is the
  maintainer's signed text, and the owner's line asked only for the note.
