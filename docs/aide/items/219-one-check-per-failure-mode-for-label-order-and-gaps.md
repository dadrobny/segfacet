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
  - **Re-checked 2026-10-13, after items 220 (`ef48313`) and 218
    (`ca12774`) merged: agrees.** Re-measured on `aide/queue-030` at
    `ca12774` over both corpora. The order rules fire exactly the six
    findings above. `remove_level` now also fires
    `centroid_spacing`/`missing_level` on {21, 23} (item 218), which is not
    an order rule, so AC10's set is unaffected. With `swap`/`shift`/`skip`
    removed (a scratch-worktree prototype of steps 1–5, below), exactly
    AC10's three tuples remain and every verdict is unchanged.
    `collapsed_labels` fires on no corpus case.
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
  - **Re-checked 2026-10-13, after items 220 and 218 merged: agrees.** Both
    spine records were run through `run_rules` with the full registry on
    `ca12774`. The curved spine fires only `sequence`/`shift` on L5; the
    reclined spine fires only `sequence`/`shift` on L5 and `sequence`/`swap`
    on L1/L4. `non_monotonic_pairs == ()` for both. Neither new rule fires or
    raises: `centroid_spacing` returns `[]` because the record has no
    `pairs.adjacent.mean_spacing_mm`, and `collapsed_labels` finds no pair
    within 2.0 mm.
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
  - **Re-checked 2026-10-13, after item 218 merged: agrees.** On the
    prototype, targets 21, 22, 23 and 24 each fire `mislabel`/`ordering` on
    {20, 28}, with `coverage`/`missing_interior` beside it for 21–23 and
    `spline_offset` on 20 for target 21. `centroid_spacing` fires on none:
    the relabelled vertebra stays at a regular pitch along the path (item
    218's A2).
- **A5 (pins the interface item 218 reads; this item is its producer of
  record).** This item keeps both of these unchanged:
  - `mislabel`/`ordering`: what it fires on and its `detector_id`.
  - `pairs.adjacent.non_monotonic_pairs[]`: consecutive `(level_a, level_b)`
    pairs in `CANONICAL_ORDER` order whose `path_u` does not advance (its
    `FEATURE_DOCS` entry).

  `transitional` reads that field as bookkeeping, through
  `record["pairs"]["adjacent"]["non_monotonic_pairs"]`. A record without it
  (no `pairs`, or no `adjacent`) excludes nothing.
  - **Re-checked 2026-10-13, after item 218 merged (`ca12774`): agrees.**
    Item 218's `centroid_spacing` does not read
    `pairs.adjacent.non_monotonic_pairs[]`. On the committed catalogue its
    only consumer is `mislabel` (signal). `mislabel`/`ordering` is unchanged
    by both items. `centroid_spacing` orders labels by `curve.path_u`, which
    this item does not touch.
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
  - **Re-checked 2026-10-13, after items 220 and 218 merged: corrected.**
    The bullets above stand as written at `2a1491d`. The last one is
    superseded. Item 220 made `collapsed_labels` a signal consumer of
    `per_label.{label}.centroid.centroid_mm[]`, and item 218 made
    `centroid_spacing` one. Today the entry's consumers are
    `{centroid_spacing, collapsed_labels, sequence}`, with modes
    (2, 6, 9, 10, 11, 13).
    - **After this item** (measured on the regenerated catalogue of the
      prototype): consumers `{centroid_spacing, collapsed_labels}`, modes
      (2, 6, 13), and `mode_evidence` unchanged.
    - `pairs.adjacent.non_monotonic_pairs[]` gains `sequence` as a
      bookkeeping consumer. Its modes stay (9,), and its `mode_evidence`
      gains `rule_bookkeeping`.
    - `per_label.{label}.level_name` goes from modes (9, 10, 11) to (11,), and
      its `mode_evidence` loses `rule_mode_map`.
    - The entry count stays 159 and the leaf-path set is unchanged. The
      empty-evidence count stays 104.
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
  - **Re-checked 2026-10-13 on the prototype: agrees.**
    `segfacet.traceability` and `segfacet.rule_table` regenerate without
    error. `rules.generated.md` renders both opt-in detectors' mode as
    `none`, while `missing_interior` keeps 10. `tests/test_164_detector_ids.py`
    and `tests/test_202_rule_table.py` pass.
- **A8 (decided: the catalogue's mode attribution moves only through
  declarations).** The catalogue attributes modes per rule, not per
  detector. So `case.sequence.present_levels[]`, a `coverage` signal path
  read only by the two now mode-less detectors, keeps mode 10 through
  `coverage`'s rule-level declaration. This is recorded, not changed
  (Left open).
  - **Re-checked 2026-10-13, after item 218 merged: agrees.**
    `case.sequence.present_levels[]` carries (6, 10) before and after this
    item. Its mode 6 now comes from `MODE_ANCHOR_PATHS[6]` alone (item 218's
    A4 re-check), and its mode 10 from `coverage`'s rule-level declaration.
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
  - **Re-checked 2026-10-13, after items 220 and 218 merged: corrected.**
    The bullets above stand. The test they describe has moved since
    `2a1491d`.
    - Items 220 and 218 already widened test_103 AC13's match filter
      (`test_ac13_rule_mode_map_effect_on_failure_modes`). It now admits
      entries whose `consuming_rules` are a subset of
      `{rule_id, "collapsed_labels", "centroid_spacing"}`, and it adds those
      two rules' declared modes to `expected` where they read the entry as
      signal.
    - This item removes `"sequence": (9,)` from `_RULE_MODE_MAP`, because no
      failure case designates `sequence` any more. So the `[sequence]`
      parametrisation disappears and its precondition is moot. On the
      prototype, `test_ac13_rule_mode_map_matches_the_corpus_scan` fails until
      the key is dropped.
    - **`[mislabel]` goes red.** `non_monotonic_pairs[]`'s consumers become
      `{mislabel, sequence}`, which is not a subset, so the match set is
      empty. The prototype measured this.
    - **The restatement, composed with the two widenings:** an entry matches
      when this rule reads it as signal and every other consumer that reads
      it as signal is in `{"collapsed_labels", "centroid_spacing"}`.
      Consumers that read it as bookkeeping are ignored. The two
      `expected |=` additions stay, and equality stays exact.
    - The bookkeeping read contributes no mode: on the prototype's catalogue
      `non_monotonic_pairs[]` keeps `failure_modes == (9,)`.
- **A10: no human gate and no environment-gated capability.** No mode
  sign-off covers modes 9, 10 or 11 (`MODE_SIGN_OFFS` holds 2, 3 and 4), so
  nothing is re-signed.
- **A11 (measured: the progress count clauses this item moves).**
  `tests/test_151_stage30_validation.py` AC35 and
  `tests/test_169_stage32_validation.py` AC6/AC7 compare the last count
  clauses in `progress.md`'s Stage 30 and Stage 20 sections with the live
  derivation. test_151 AC12 pins `total_edges == 15`.
  - This item alone removes two `needs-real-data` edges: mode 9's
    `sequence` edge and mode 10's `sequence` edge.
  - Before this item, at `2a1491d`, there were 15 edges at 7 / 7 / 1
    (item 220's A9). This item alone moves that to 13 edges, with
    needs-real-data 5.
  - No mode's derived status or rung moves. Mode 9 keeps `mislabel`'s
    `synthetic-demonstrable` edge, mode 10 keeps `coverage`'s
    `needs-real-data` edge, and mode 11 keeps `sequence`'s.
  - Siblings 218 and 220 move these counts too, so step 10 re-measures live
    and writes whatever the tree holds. The test_151 AC12 literal is
    reconciled to the live count.
  - **Re-checked 2026-10-13, after items 220 and 218 merged (`ca12774`):
    corrected.** The figures above are true of `2a1491d` and stand as that
    record. Measured live on `ca12774`:
    - **The base:** derived status validated 7, implemented 4, specified 1,
      proposed 4, with a validated split of 7 pipeline and 0 reconstructed.
      Mode rungs: synthetic-demonstrable 7, needs-real-data 3,
      structurally-unobservable 1, none 5. Edges: 17, at 8 / 8 / 1. test_151
      AC12 pins `total_edges == 17`.
    - **After this item (prototype):** edges 15, at 8 / 6 / 1. Derived status,
      the validated split and mode rungs are unchanged. Modes 9, 10 and 11
      derive validated, implemented and implemented, as before. The edgeless
      set stays {5, 7, 8, 12, 14}.
    - **So test_151 AC12 moves 17 → 15.** Of step 10's three amends, only
      `amend 30 --criterion 3` should find its last clause differing (the
      per-edge counts). Criteria 30.1 and 20.5 already carry item 218's live
      values, which this item does not move. test_151
      `test_ac35_rung_counts_note_matches_live_derivation` stays red until
      that amend lands (prototype: `17 == 15`).

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
     - In each corpus case's `expected_firing` (`relabel_swap`,
       `sequence_break`), **drop `"sequence"`** and leave every other member
       as it stands. Do not replace the tuple with `("mislabel",)`: item 222
       adds `spline_offset` to `sequence_break`'s set as a co-detection, and
       a replacement would erase it if 222 lands first. Re-measure the
       reasons and date them 2026-10-12, item 219.
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
   - `expected_rule_ids=frozenset({"mislabel"})`. This is the designated
     rule, so it is replaced outright. Item 222's `spline_offset` is a
     co-detection in `failure_modes.py`, not a designated rule, and is not
     added here.
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
   - `.venv/bin/python -m segfacet.synth.corpus_sheet`, after the manifest:
     `docs/aide/corpus_sheet.png` renders each case's expected rules, and
     test_178 AC7 checks its digest against the manifest and fixtures.
9. **Reconcile the existing tests** listed under Testing Strategy. Add a
   dated `# Item 219 (2026-10-12): ...` line beside each changed value.
10. **Amend the count clauses** (A11) with
    `python .aide/scripts/aide.py progress amend`, in item 220's step-9
    format. Re-measure all three clauses live first, and amend each one
    whose last recorded value differs from the tree:
    - `amend 30 --criterion 1`: derived status counts over 16 modes, plus
      the validated split;
    - `amend 30 --criterion 3`: derived mode rung counts, plus per-edge rung
      counts over N edges;
    - `amend 20 --criterion 5`: derived status counts and derived mode rung
      counts.

    Each `--evidence` starts `Item 219 (<date>): mode 9 loses sequence's
    swap/shift edge and mode 10 its skip edge, both needs-real-data.
    Re-measured live:`.
11. Run `python .aide/scripts/aide.py scope 219` and
    `python .aide/scripts/aide.py check`. Neither may report an error.

No dependency is added. Every helper is already in the tree:
`compute_monotonic_consistency`, `anatomical_order`, `DEFAULT_LABEL_MAP`,
`resolve_section_counts` and `expected_level_sequence`.

**Correction (2026-10-13, re-check after items 220 (`ef48313`) and 218
(`ca12774`) merged).** The steps above stand. This adds what the two merges
moved.

**The prototype the re-checks cite.** A throwaway `git worktree` of
`ca12774` was set up under the session scratchpad. It applied steps 1, 2, 4
(edges, expected sets, the condition, and mode 9's mechanism), 5 and 6's
override line, then ran step 8's generators. Its corpus fixtures and
`golden_evidence.generated.json` came out byte-identical. The product suite
(`tests/`) then ran against it with `PYTHONPATH` pointing at the worktree's
`src` (confirmed by `segfacet.__file__`), and the git-gated test_116 ran
because the worktree shares `.git`. The result was 64 failed, 8035 passed and
73 skipped. Every failure is listed under Testing Strategy's correction of
this date. The prototype is not the builder's implementation, and the builder
re-measures on the real change.

- **Step 4, `_MODE_6`.** Item 218 left `remove_level`'s `expected_firing`
  as `("centroid_spacing", "coverage", "sequence")`. Dropping `"sequence"`
  leaves `("centroid_spacing", "coverage")`.
  - In the mechanism's sentence "coverage's interior-gap detector and
    sequence's skip detector fire on the label gap in
    case.sequence.missing_levels[]; both serve mode 10", name `coverage`
    alone.
  - **Keep the dotted path `case.sequence.missing_levels[]` in that
    sentence.** It is consumed by the co-detecting `coverage` and not by the
    declared `centroid_spacing`. That makes it a witness for
    `tests/test_138_traceability_matrix.py`'s AC31
    `checked_any_co_detection`. The prototype kept it, and AC31 passed.
  - In the `remove_level` reason, drop "and, since item 192, sequence's skip
    detector also fire: both serve mode 10, so those two are". `coverage`
    alone is recorded as the co-detection.
- **Step 4, `_MODE_10`.** Item 218 rewrote the mechanism. Remove its
  `sequence` sentence ("sequence's skip detector reads the same gap ... like
  coverage"). Item 218's closing clause about `centroid_spacing` stays.
- **Step 4, `_MODE_9`'s rewritten mechanism must keep five tokens.**
  `CANONICAL_ORDER` and `T13` are needed for test_138 AC17.
  `tests/test_145_eight_hypothesised_modes.py::test_ac10b_sequence_case_records_the_single_rank_descent_correction`
  also needs `t12`, `l1` and `l2`, matched case-insensitively. Neither test
  file needs an edit for these tokens. The prototype's terse mechanism
  dropped `T12`, and AC10b went red.
- **Step 10.** Only Stage 30 criterion 3 is predicted to move (A11's
  re-check).

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
- `docs/aide/corpus_sheet.png` — regenerated after the manifest; it renders each case's expected rules (step 8).
- `tests/test_151_stage30_validation.py` — reconcile AC12's `total_edges` literal to the live count (A11).
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

**Correction (2026-10-13, re-check after items 220 and 218 merged).** The
list above stands. On the prototype suite, one red fell outside it:

- `tests/test_041_regression_suite.py` — `test_ac11_offending_label_drift_is_caught`'s precondition `drifted["expected_labels"] == [28]` becomes `[20, 28]` (AC12).

`tests/test_220_collapsed_labels_rule.py` stayed green on the prototype. Its
bullet stays, conditional as written.

**Asserts against:**

- `tests/corpus/fixtures/**` — AC10 reads the committed fixtures; step 8 must not change them.
- `tests/corpus/intensity/manifest.json` — AC10 drives the intensity cases; none may fire an order rule.
- `tests/test_163_specificity_ratchet.py` — must stay green unedited: no case fires a rule it does not expect.
- `tests/test_164_detector_ids.py` — must stay green unedited: every declared detector is named by an edge or excused.
- `tests/test_191_condition_gate.py` — must stay green unedited: the condition's opt-ins match the registry.
- `tests/test_202_rule_table.py` — must stay green unedited once step 8 regenerates `rules.generated.md`.
- `tests/test_104_feature_catalogue_drift.py` — must stay green unedited once step 8 regenerates the catalogue.
- `tests/test_178_corpus_sheet.py` — must stay green unedited: AC7 checks the regenerated sheet's digest against the manifest and fixtures.
- `tests/test_210_label_free_monotonic_reference.py` — must stay green unedited: `ordering` and `non_monotonic_pairs[]` keep their meaning (A5), and AC8 reuses its `ARC`.

Added 2026-10-13 by the re-check after items 220 and 218. Each of the first
three goes red on the prototype only because it imports a constant that this
item reconciles in another file. Each goes green with no edit of its own once
that constant is reconciled.

- `tests/test_102_stage18_validation.py` — AC5 imports test_098's `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS` (`relabel_swap`, `remove_level`, `sequence_break`).
- `tests/test_131_tangent_direction_normalisation.py` — AC19 iterates test_129's `_PRE_129_FINDINGS`.
- `tests/test_143_s_axis_correction.py` — AC9 imports test_098's `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`.
- `tests/test_218_centroid_spacing_rule.py` — must stay green unedited: AC1's `centroid_spacing` firing set, `remove_level` included, does not move (A1 re-check).

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
- **`test_151`** AC12: `total_edges` moves to the live count, which is 13
  for this item alone (A11), with a dated comment in the house style. AC35
  needs no edit once step 10 has amended the clauses.
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

**Correction (2026-10-13, re-check after items 220 and 218 merged).** The
list above stands. It was a lower bound, and the prototype suite
(Implementation Steps, correction of this date) gives the measured red set:
64 failures. Each is named below under the file that owns it. The fence is
unchanged. Each edit carries a dated `# Item 219 (YYYY-MM-DD): ...` comment.

- **Already listed above, with every red the prototype showed:**
  - test_030 AC3–AC6 and the three-offenders adversarial; test_035 AC25 and
    `test_ac27_each_of_eight_modes_fires_its_mapped_rule`; test_038 AC5,
    whose set is now `{"centroid_spacing", "coverage"}`, since item 218 has
    landed; test_039 AC16–AC18 and the interior-target adversarial; and
    test_132 AC13 and AC30.
  - test_192: AC1, AC2, AC3, AC7, AC8, AC9, AC10 and
    `test_sacral_labels_share_one_rank`.
  - test_116 AC7, three cases: `relabel_swap`, `remove_level` and
    `sequence_break`. The item-218 map
    `_ITEM_218_ADDED_CENTROID_SPACING_PAIRS` now sits beside the item-198
    one. It stays, because `remove_level`'s `centroid_spacing` finding is
    unaffected.
  - test_098 AC15, three cases. Item 218 added `remove_level`'s
    `centroid_spacing` entry to `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`, and
    that entry stays. Only the three `sequence` entries go.
  - test_129 AC29 (`_PRE_129_FINDINGS`). `remove_level` keeps
    `("centroid_spacing", (21, 23))` and `("coverage", ())`.
  - test_103: AC10's `centroid_mm[]` row, re-pointed to `centroid_spacing`,
    which is now definite because item 218 has landed;
    `test_ac13_rule_mode_map_matches_the_corpus_scan`; and AC13's
    `[mislabel]` and `[sequence]` parametrisations (A9 re-check).
  - test_136 AC4 `[sequence]`.
  - test_138: AC17 (the mode-9 rung test), AC20 (the analytic witness) and
    `test_adv_ac31_named_anchor_path_not_consumed_by_declared_rule_is_detectable`.
  - test_145: AC10a, and AC21 (`test_ac21_sequence_mode_severity_leads_its_rules`,
    mode 10's rule set → `{"coverage"}`). AC10b is fixed in `src` (the
    mode-9 tokens), not in the test.
  - test_147 AC11, test_148 AC16, test_149 AC9 (both tests read the one
    `_AC9_SPLIT_COLUMN_MODES` read path), test_151 AC12, and test_188 AC2
    and AC4.
- **test_030, beyond the list above.** Also red:
  `test_ac11_default_severity_is_flag`,
  `test_ac11_severity_param_fail_overrides_default` and
  `test_ac13_reason_names_offenders_in_out_of_order_labels_order`.
  - **AC11 ×2 is re-pointed, not retired.** The severity claim survives on
    `transitional`. Use the `unrelated-pair-does-not-silence-transitional`
    record without its pairs block: T10, T11, L1, L2 and L3 (labels 17, 18,
    20, 21 and 22). Measured on the prototype, it yields one `transitional`
    finding on {18} at `Severity.FLAG` by default. The `severity: fail` arm
    asserts `Severity.FAIL` on the same record.
  - **AC13 is retired.** Its subject is the `swap` reason's offender order.
  - The "L730–745 test" above is `test_adv_three_offenders_all_named_and_attributed`.
- **test_035_failure_modes, beyond the list above.**
  - `test_ac27_union_of_all_modes_covers_every_mapped_rule_id`: drop
    `"sequence"` from its `expected` set, because no seed record fires it
    any more.
  - AC25: re-point the name and docstring to `mislabel`. Measured on the
    branch: the mode-7 record, given `pairs.adjacent.non_monotonic_pairs`
    from `compute_monotonic_consistency` over its centroids in anatomical
    order, reads `(("T12", "L1"),)`. `mislabel`/`ordering` fires on
    {19, 20}, so `{_L1, _T12} <= f.labels` holds.
  - Since item 220, the same record also fires three
    `collapsed_labels`/`near_coincident_centroids` findings, because its
    centroids sit 1 mm apart. AC25 and AC27 check containment, so they are
    unaffected and nothing is edited for it.
- **test_039, beyond the list above.**
  `test_ac24_spacing_aware_under_anisotropic_spacing[sequence_break]` raises
  `ValueError` at `_designated_rule_fires_run_qc`'s
  `(target,) = expectation.expected_labels`. The helper's listed
  re-pointing fixes it: match `mislabel` on the whole `expected_labels`, and
  remove the single-element unpack. The interior-target adversarial (L709)
  is the listed one.
- **test_132, beyond the list above.**
  `test_ac26_item_098_shared_golden_constant_reconciled` pins
  `len(expected["findings"]) == 2` and `findings[1]["rule_id"] == "sequence"`
  for `relabel_swap`. Both become one finding, `mislabel`. AC25's pinned set
  becomes `{("mislabel", (21, 22))}`, as listed.
- **test_137, `test_adv_measured_artifact_movement_counts_from_spec`.**
  This is no longer conditional. Measured on the prototype's regenerated
  catalogue, `mode_evidence` buckets:
  - `("rule_mode_map", "rule_declaration")`: 11 → 10.
    `non_monotonic_pairs[]` leaves.
  - `("rule_mode_map", "rule_declaration", "rule_bookkeeping")`: 1 → 2.
    `non_monotonic_pairs[]` joins.
  - `("rule_mode_map", "rule_declaration", "rule_mode_less", "rule_bookkeeping")`:
    1 → 0, removed from the exhaustive table. `level_name` leaves.
  - `("rule_declaration", "rule_mode_less", "rule_bookkeeping")`: new, 1.
    `level_name` joins.
  - Unchanged: `()` 104, a total of 159, and `mode2_count` 12. Per-mode
    path counts for modes 9, 10 and 11 go 4 → 2, 4 → 2 and 2 → 1, and
    test_137 pins none of them.
- **test_041** (Authorised paths, correction of this date): AC11's
  precondition `[28]` → `[20, 28]`.
- **test_151 `test_ac35_rung_counts_note_matches_live_derivation`** is red
  until step 10's `amend 30 --criterion 3`, with no test edit.
- **Green on the prototype with no edit:** test_163, test_164, test_191,
  test_202, test_104, test_178, test_210, test_218, test_220, test_171 and
  test_126. The last two read `sequence_break` through test_041's AC9/AC10
  and golden-decision-table digests only.
- **Red only through a constant reconciled elsewhere:** test_102 AC5 and
  test_143 AC9 (test_098's constant) and test_131 AC19 (test_129's). They
  are listed under Asserts against and get no edit.

## Review findings

- `sequence-break-expectation-matches-pipeline-for-both-targets`:
  (minor, fixed 2026-10-13): `SequenceBreakPerturbation(target_label=20)`
  stated `mislabel`/{20, 28} while the pipeline fires only `sequence`/{28}
  there. Fix: the expectation is derived from whether the relabel leaves
  canonical order. Test: the default target still states and fires
  `mislabel`/{20, 28}; `target_label=20` states and fires `sequence`/{28}.
- `sequence-break-unranked-new-label-raises-facet-input-error`:
  (minor, fixed 2026-10-13): `new_label=99` (no canonical rank) escaped as a
  bare `ValueError`. Fix: raise `FacetInputError`. Test: that call raises it.
- `sequence-tolerates-malformed-pairs`: (minor, fixed 2026-10-13):
  `sequence` raised on malformed `pairs.adjacent.non_monotonic_pairs`
  entries. Fix: the pair read is guarded. Test: `[None]`, `5`, `['T13']` and
  `[['T13', None]]` raise nothing and the T13 transitional finding fires.
- `pair-member-excluded-from-transitional`: (weak test, 2026-10-13): the
  case only put the transitional level first in the pair. Test now also
  covers it second (`["L1", "T13"]`).
- `transitional-fires-without-centroids`: (weak test, 2026-10-13):
  test_192's no-centroid test used a T12+L1 record that can never fire
  `transitional`. Re-targeted to a T13 record with no centroids that fires.

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

**Correction (2026-10-13, re-check after item 218 merged).** Item 218 has
landed. So `<tmp3>`'s expected findings are definite:

- `centroid_spacing`'s `Missing level:` finding on labels 21 and 23;
- `coverage`'s `Missing interior level(s):` finding;
- no `sequence` finding.

The verdict is `flagged-for-review`.

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

Implemented 2026-10-13 on `aide/219-one-check-per-failure-mode`.

- **Built to the spec's steps 1-10.** `sequence` keeps only `transitional`,
  reads level names and `pairs.adjacent.non_monotonic_pairs[]` (bookkeeping),
  and no longer opts in to `displaced_vertebra`. `consumed_paths` is listed in
  ascending path order, which `RuleModeDeclaration` enforces. `coverage`'s two
  opt-in detectors carry A7's `mode_less_reason` texts, and the traceability
  matrix and rule table regenerate and render them as mode `none`.
- **Regeneration.** Every generator ran twice into scratch paths and the two
  runs were byte-identical before the committed copies were written. The
  corpus run changed the manifest only (the `sequence_break` entry:
  `expected_rule_ids ["mislabel"]`, `expected_labels [20, 28]`, new `detail`);
  no fixture moved and `golden_evidence.generated.json` came out unchanged.
- **Reconciliations.** Each edit carries a dated `item 219 (2026-10-13)`
  note: test_030, 035, 038, 039, 041, 098, 103, 116, 129, 132, 136, 137,
  138, 145, 147, 148, 149, 151, 188 and 192, as the Testing Strategy lists.
  test_137's four buckets were re-measured live and agree with the spec's
  figures. test_220, 102, 131, 143 and 218 needed no edit.
- **Stage 30 criterion 3** was amended with live numbers: derived mode rungs
  7 / 3 / 1 / 5, per-edge rungs over 15 edges at 8 / 6 / 1. Criteria 30.1 and
  20.5 were already current and not amended.
- **Validation replays** (`segfacet run ... --no-reference`):
  `sequence_break` gives one `mislabel` finding, `Vertebra ordering
  inconsistent with label:` on labels 28 and 20, verdict
  flagged-for-review. `relabel_swap` gives one `mislabel` finding on 21 and
  22. `remove_level` gives `centroid_spacing`'s `Missing level:` on 21 and 23
  plus `coverage`'s `Missing interior level(s):`. No run has a `sequence`
  finding.

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
- **2026-10-13 (review fix): `SequenceBreakPerturbation`'s expectation follows
  what the pipeline fires.** `mislabel`/`{new_label, next level}` holds only
  when the relabel moves the level out of canonical order (the target's index
  among the present labels differs from `new_label`'s index in the canonical
  order). When the relabel keeps its position (e.g. `target_label=20`, the
  head, relabelled to T13) `non_monotonic_pairs` is empty and only
  `sequence`/`transitional` fires on `{new_label}`, so the expectation is
  `sequence`/`{new_label}` as before the item, not a construction error: such a
  target is a valid, if weaker, break. The default target (28) is out of order,
  so corpus output is unchanged.
- **2026-10-13 (review fix): a `new_label` outside `DEFAULT_LABEL_MAP` is
  rejected with `FacetInputError`.** It has no canonical rank, so the item's
  `order.index` raised a bare `ValueError`; and the pipeline treats such a label
  inconsistently (probe: `mislabel` on a pair naming it), so no honest
  expectation exists to fall back to. Failing clearly at `apply` beats a
  guessed expectation. No test or caller passed such a label.
- **2026-10-13 (review fix): `sequence` guards `non_monotonic_pairs` as
  `mislabel` does.** A non-list value, a non-pair entry, or a non-string member
  is skipped silently (the retired rule tolerated malformed records, test_030
  AC9), so a bare string no longer contributes its characters as level names.
