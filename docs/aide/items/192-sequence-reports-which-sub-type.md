<!-- aide-template: item 2 -->
# Item 192 — `sequence` reports which sub-type it saw

> **Created:** 2026-09-28 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-025.md`](../queue/queue-025.md) · Item 192
> **Objectives:** G2, G8
> **Suggested branch:** `aide/192-sequence-reports-which-sub-type`

---

## Description

This item implements roadmap Stage 33 D3's bullet "`sequence` reports which
sub-type it saw across modes 8–11. Mode 12 stays out." It closes the `gap`
entry in `docs/aide/insights.md` dated 2026-09-22 (queue-022 review, the
`sequence` decision) and the `defect` entry dated 2026-09-27 (item 186) on
`relationships.is_continuous` / `out_of_order_labels` walking integer-label
order.

**The defect.** `sequence` fires on `relationships.out_of_order_labels[]`.
`segfacet.pipeline.extract_feature_record` passes centroids to
`compute_spine_relationships` in ascending integer-label order, and that
function walks them in the order given. TPTBox integer values are not
anatomical order: T13 is 28, after L1–L5 (20–24), and `Cocc` is 27, before
S2–S6 (29–33). So today the rule fires only when a T13 sits with a lumbar
label, or `Cocc` with S2 or lower, and it fires on those even when the spine
is labelled correctly. It never sees a real swap: `relabel_swap` exchanges L2
and L3 and `sequence` stays silent.

**The fix.** `sequence` stops reading `relationships`. It reads each label's
level name and centroid from `per_label`, orders the labels head-to-tail by
their position, and compares that order, and the names present, with item
186's expected sequence. It reports what it sees as one of four sub-types,
each its own detector:

| Detector | What it sees | Mode |
|---|---|---|
| `swap` | two labels exchanged along the spine | 9 |
| `shift` | a label moved to another place, the labels between it shifted by one | 9 |
| `skip` | a level absent between present levels of the expected sequence | 10 |
| `transitional` | a non-default section count the field of view does not corroborate (item 186) | 11 |

Mode 8 is served through these three children (each has `parent=8`), and it
gets no edge of its own: a mode-8 mislabelling that keeps the sequence valid
cannot be seen by a rule that reads the sequence. Mode 12, a whole-sequence
shift, is internally valid and stays out.

**What moves on the corpus** (A10, measured). `relabel_swap` gains a `sequence`
`swap` finding, `remove_level` gains a `sequence` `skip` finding (a mode-10
co-detection on a mode-6 case, like `coverage`'s), and `sequence_break`'s
finding becomes `shift`. Nothing else fires differently, and no verdict moves.

**Not in scope.**

- `relationships.is_continuous` and `relationships.out_of_order_labels[]` are
  not changed. They keep walking integer order, and
  `segfacet.eval.per_mode`'s `out_of_order_label_count` and the text report
  still read them (Left open).
- `mislabel`'s `ordering` detector is not changed. It reads
  `stage3.monotonic_consistency.non_monotonic_pairs[]`, which is judged in the
  same ascending-integer order and misreads a correct T13 or `Cocc` the same way
  (A11, Left open).
- No supplied section counts reach the rule (item 186's Left open stands).
- No corpus fixture, manifest or severity ladder changes. No config key
  changes.

## Acceptance Criteria

Terms used below:

- **`cfg`** is `segfacet.config.bundled_default_config()`.
- **"The manifest"** is `segfacet.synth.corpus.load_manifest()`, and **"the
  `X` case"** is its entry whose `case_id == "X"`.
- **"The clean map"** is
  `segfacet.synth.regression.loaded_seg_image(<the clean_control case>)`:
  labels 20–24 (L1–L5), with L1 the most superior.
- **`relabel(M)`** is the clean map with every voxel value `a` in `M` replaced
  by `M[a]` (each replacement read from the original data), on the same
  affine and header.
- **`seq(X)`** is
  `{(f.detector_id, f.labels) for f in segfacet.heuristics.run_rules(segfacet.pipeline.extract_feature_record(X, cfg), cfg) if f.rule_id == "sequence"}`.

- [ ] **AC1: a swap is reported as `swap`.**
  `seq(loaded_seg_image(<the relabel_swap case>)) == {("swap", frozenset({21, 22}))}`.
- [ ] **AC2: a moved label is reported as `shift`.**
  `seq(relabel({20: 21, 21: 22, 22: 20})) == {("shift", frozenset({20}))}`.
  The labels read L2, L3, L1, L4, L5 head-to-tail, and only the moved L1 is
  named.
- [ ] **AC3: a skipped level is reported as `skip`.**
  `seq(relabel({20: 19, 21: 20, 22: 21})) == {("skip", frozenset())}`. The
  labels read T12, L1, L2, L4, L5 on five adjacent vertebrae.
- [ ] **AC4: an uncorroborated T13 is reported as `transitional`.**
  `seq(relabel({20: 28, 21: 20, 22: 21, 23: 22, 24: 23})) == {("transitional", frozenset({28}))}`.
  The labels read T13, L1–L4 in anatomical order, with no C7.
- [ ] **AC5: an uncorroborated short thoracic reading is `transitional`, not
  `skip`.**
  `seq(relabel({20: 17, 21: 18, 22: 20, 23: 21, 24: 22})) == {("transitional", frozenset({18}))}`.
  The labels read T10, T11, L1–L3, with no C7.
- [ ] **AC6: a correct coccyx below the sacrum fires nothing.**
  `seq(relabel({20: 23, 21: 24, 22: 26, 23: 29, 24: 27})) == set()`. The
  labels read L4, L5, S1, S2, `Cocc` head-to-tail.
- [ ] **AC7: `sequence_break`'s finding names its sub-type.** The findings of
  `segfacet.synth.regression.pipeline_findings(<the sequence_break case>)`
  with `rule_id == "sequence"`, reduced to `(detector_id, labels)`, are
  `{("shift", frozenset({28}))}`.
- [ ] **AC8: the rule declares modes 9–11 and no other.**
  `segfacet.heuristics.get_rule("sequence").mode_declaration.modes == (9, 10, 11)`.
- [ ] **AC9: each sub-type serves its own mode.**
  `{d: segfacet.failure_modes.modes_for_detector("sequence", d) for d in ("shift", "skip", "swap", "transitional")} == {"shift": (9,), "skip": (10,), "swap": (9,), "transitional": (11,)}`.
- [ ] **AC10: a swap on a label that reads as displaced still fires.** Let
  `r = extract_feature_record(relabel({20: 21, 21: 20}), cfg)`. Then
  `{(f.rule_id, f.detector_id, f.labels) for f in run_rules(r, cfg) if f.rule_id in {"sequence", "spline_offset"}} == {("sequence", "swap", frozenset({20, 21})), ("spline_offset", "spline_offset", frozenset({21}))}`.

Why each is written:

- AC1–AC4 are the queue's "each sub-type, constructed as a label map, yields a
  finding that names it", one per sub-type. AC4 is also the item-186 insight's
  T13 half: the same map fires a `discontinuity` finding on label 28 today.
- AC5 is the queue's "a non-default count that the field of view does not
  show, and no supplied count backs, is reported as the transitional
  sub-type", for the reading item 186's AC6 refuses. It fails if the gap the
  refused reading leaves is reported as a skip.
- AC6 is the insight's `Cocc` half. Today the map fires `discontinuity` on S2.
- AC7 is the queue's "`sequence_break`'s finding names its sub-type".
- AC8 is "serves that family" and "no mode-12 edge is declared". AC9 ties each
  sub-type to its mode; without it the four detectors could all serve mode 9.
- AC10 is the condition decision (A8). Without `sequence`'s opt-in to
  `displaced_vertebra`, the runner drops the swap finding, because
  `spline_offset` reads label 21 as displaced. The `spline_offset` member is the
  precondition: if 21 stopped reading as displaced, the equality fails instead
  of passing without exercising the gate.
- The re-authored expected sets of `relabel_swap` and `remove_level` are not
  restated. `tests/test_163_specificity_ratchet.py` fails unless each authored
  set equals its measured firing.

None of these closes a Stage 33 acceptance criterion. Criterion 2 is attested
by D6's stage validation over the whole corpus, and criterion 3 by D4's
detector-granular bar checker.

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
measured value below was taken on 2026-09-28 with `.venv/bin/python` against a
scratch copy of this branch's `src/`, `tests/` and `docs/`. The copy carried a
prototype of Implementation Steps 1–2, ran under `python -S` with its own
`src` first on `sys.path`, and so was not shadowed by the working checkout's
editable install (`CLAUDE.md`, Gotchas). The builder re-measures each value
on the real change.

- **A1 (interface pin, item 186, read from the merged code on 2026-09-28).**
  From `segfacet.labels`:
  - `resolve_section_counts(present_levels, supplied=None)` returns
    `ResolvedSectionCounts(counts, unaccepted)`. `counts` is a
    `SectionCounts(cervical, thoracic, lumbar)` `NamedTuple`, so
    `counts._replace(thoracic=13)` is valid. `unaccepted` is a
    `Dict[str, int]` keyed `"thoracic"` or `"lumbar"`.
  - A thoracic reading is taken only when L1 is present, and a lumbar reading
    only when a sacral label is present. The reading is the highest index in
    the section. A reading of 11/13 (4/6) is unaccepted without C7 (without
    T*t*).
  - `expected_level_sequence(counts)` returns C1–C7, T1–T*t*, L1–L*l*, then
    `SACRUM` (`"S"`). The coccyx is not in it.
- **A2 (interface pin, item 191, read from the merged code on 2026-09-28).**
  - `segfacet.heuristics.rule.ConditionOptIn(condition, paths, reason)`, a
    frozen dataclass; `paths` is a non-empty tuple of catalogue paths the rule
    reads (`tests/test_191_condition_gate.py` AC12).
  - `Rule.condition_opt_ins` is a class attribute read by `run_rules` only.
  - `run_rules` drops a finding when any of its labels is in `fov_truncation`
    (a true `touches_*` flag) or `displaced_vertebra` (named by a surviving
    `spline_offset` finding), unless its rule opts in. A case-level finding is
    never dropped.
  - `CONDITIONS[c].opting_in_rules` must equal the registry-derived sorted
    tuple (`tests/test_191_condition_gate.py` AC10).
- **A3 (defensible default: the four sub-types).** The queue names "a swap, a
  skip, a transitional label, or a shift". A whole-sequence shift is mode 12
  and stays out, so "a shift" is read as the moved-label form mode 9's
  definition names ("a level ranked above its cranial neighbour"): one label
  moved several places, the labels between it each displaced by one. A skip
  is a label gap (mode 10) and a transitional label is an uncorroborated
  numbering variant (mode 11). Mode 8 gets no direct edge (Description).
- **A4 (defensible default: head-to-tail order).**
  - The rule reads `per_label.{label}.level_name`,
    `per_label.{label}.label` and `per_label.{label}.centroid.centroid_mm`.
    It no longer reads `relationships`.
  - An entry is kept when it is a mapping, its `level_name` is in
    `segfacet.labels.CANONICAL_ORDER`, and `centroid_mm` has three numbers.
    Every other entry is ignored. So a hand-built record with no centroids
    yields no finding.
  - Head-to-tail is descending `centroid_mm[2]`, ties broken by ascending
    label. The record's `centroid_mm` is world RAS mm (items 094 and 116), so
    index 2 is superior. Measured on the clean map: L1 163.40 mm down to L5
    31.43 mm.
- **A5 (defensible default: `swap` and `shift`).**
  - Rank is the `CANONICAL_ORDER` index, with S1–S6 sharing one rank (item
    186: the sacrum is one element). `Cocc` keeps its rank, after the sacrum.
    The rank ordering is the same for every section count, because every
    expected sequence is a subsequence of `CANONICAL_ORDER`.
  - The expected order is the head-to-tail order stably re-sorted by rank.
    Label at head-to-tail slot *i* belongs at expected slot *e(i)*. The slots
    with *e(i) ≠ i* decompose into cycles.
  - A 2-cycle is a `swap`, and both labels are named. A longer cycle is a
    `shift`, and the labels with the largest |*e(i) − i*| in the cycle are
    named. So the swap 20↔24 names 20 and 24 (not the descent pairs 21–23 that
    `mislabel` names, item 189's Left open), and `sequence_break`'s tail T13
    names 28 alone.
  - Two sacral labels are never out of order with each other.
- **A6 (defensible default: `transitional` and `skip`).**
  - Resolve counts with `resolve_section_counts(<kept level names>)`, no
    `supplied`. The **reading counts** are the resolved counts with each
    unaccepted reading substituted.
  - `transitional` names the level T*n* (thoracic) or L*n* (lumbar) of each
    unaccepted reading, plus each kept level other than `Cocc` that is not an
    element of `expected_level_sequence(<reading counts>)` (sacral names map to
    `SACRUM`). A level already named by `swap` or `shift` is dropped from it:
    a variant label out of order is mode 9, not mode 11 (mode 11's
    discriminator). Named in `CANONICAL_ORDER` order.
  - `skip` walks `expected_level_sequence(<reading counts>)`. It names every
    element strictly between the first and last present element that is
    absent, in sequence order, when at least two distinct elements are
    present. Its finding is case-level (`labels` empty), as `coverage`'s
    `missing_interior` is: a gap has no label.
  - Using the reading counts is what makes AC5 a `transitional` and not a
    `skip`. `coverage` still reports T12 missing on that map, because
    `relationships.missing_levels[]` uses the resolved counts.
- **A7 (defensible default: the finding shape).**
  - At most one finding per detector, emitted in ascending `detector_id`
    order: `shift`, `skip`, `swap`, `transitional`.
  - Names are joined with `", "`. For `swap` and `shift` they are in
    head-to-tail order; for `skip` in sequence order.
  - Reasons, exactly:
    - `swap`: `f"Non-continuous label sequence: swap of {names}."`
    - `shift`: `f"Non-continuous label sequence: shift of {names}."`
    - `skip`: `f"Skipped level label: {names} absent between present levels."`
    - `transitional`: `f"Transitional level label without field-of-view evidence: {names}."`
  - The two order sub-types keep the `Non-continuous label sequence:` prefix,
    which is the vision seed's name for mode 9 and what
    `tests/test_039_identity_ordering_alignment_perturbations.py` matches.
  - The severity is still `rules.sequence.params.severity` (default
    `flagged-for-review`), read before any record processing. No config key
    changes, so `reference.artifact.config_hash` does not move.
- **A8 (defensible default, measured: the condition opt-ins).**
  - `sequence` opts in to `displaced_vertebra`, with paths
    `per_label.{label}.centroid.centroid_mm[]` and
    `per_label.{label}.level_name`. A label swap puts a centroid off the curve
    fitted in label order, so `spline_offset` reads it as displaced. Measured:
    of the swaps 20↔21, 20↔22, 22↔24, 21↔23 and 20↔24 on the clean map, the
    first three lose their `swap` finding without the opt-in and keep it with
    it. A displacement mostly left-right leaves the S order unchanged.
  - `sequence` does not opt in to `fov_truncation`: no case needs it (Left
    open). `swap`, `shift` and `transitional` findings on a border-touching
    label are dropped. `skip` findings are case-level and never dropped.
  - `CONDITIONS["displaced_vertebra"].opting_in_rules` becomes
    `("mislabel", "sequence", "spline_offset")`.
- **A9 (defensible default: the specification).**
  - Mode 9: the `sequence` edge's `detector_ids` become `("shift", "swap")`.
    Its rung stays `needs-real-data`, and `tests/test_138_traceability_matrix.py`
    AC17 pins that. `relabel_swap`'s `expected_firing` becomes
    `("mislabel", "sequence")`.
  - Mode 10 gains `IntendedRule(rule_id="sequence", detector_ids=("skip",), evidence_rung="needs-real-data")`
    after `coverage`'s edge.
  - Mode 11: authored `status` `"proposed"` → `"specified"`, and
    `intended_rules` becomes
    `(IntendedRule(rule_id="sequence", detector_ids=("transitional",), evidence_rung="needs-real-data"),)`.
    It derives `implemented`, rung `needs-real-data`. No corpus case.
  - Mode 6: `remove_level`'s `expected_firing` becomes
    `("coverage", "sequence")`, a recorded co-detection.
  - Mode 12 is not touched.
  - The mechanism sentences of modes 6, 9, 10 and 11 and the displaced-vertebra
    condition, and the `reason`s of `relabel_swap`, `remove_level` and
    `sequence_break`, are rewritten (Implementation Step 3 lists the tokens
    existing tests require).
- **A10 (measured: what moves).**
  - Plain pipeline, both corpora: three cases change and nothing else.
    - `relabel_swap`: `mislabel/ordering` on {21, 22} (kept) plus
      `sequence/swap` on {21, 22}, reason
      `"Non-continuous label sequence: swap of L3, L2."`.
    - `remove_level`: `coverage/missing_interior` (kept) plus `sequence/skip`,
      reason `"Skipped level label: L3 absent between present levels."`.
    - `sequence_break`: `sequence/discontinuity` on {28} becomes
      `sequence/shift` on {28}, reason
      `"Non-continuous label sequence: shift of T13."`.
    - Every verdict is unchanged. The intensity corpus is unchanged.
  - `segfacet.eval.severity_ladder.run_severity_harness()` is identical
    (serialised and compared).
  - `docs/aide/golden_evidence.generated.json` regenerates byte-identical.
  - `tests/corpus/manifest.json` does not move: its `expected_rule_ids` is a
    designated subset (`failure_modes._corpus_case_conflicts`), and
    `{"mislabel"}` and `{"coverage"}` stay subsets. No fixture moves, so
    `docs/aide/corpus_sheet.png` does not move either.
  - `traceability.build_matrix()`, with the specification re-authored:
    conformance 18 agreeing, 0 disagreeing; `exercise.rules.sequence.exercised_by`
    becomes `relabel_swap`, `remove_level`, `sequence_break`;
    `features.by_rule.sequence` 5 → 4; `features.read_by_rule` stays 52 and
    `read_by_no_rule` stays 93; `directions.mode_to_rule.holes` loses `"11"`;
    `modes["11"]` becomes `implemented` with rules `["sequence"]`;
    `modes["10"].rules` becomes `["coverage", "sequence"]`.
  - `catalogue.build_catalogue()`: `per_label.{label}.centroid.centroid_mm[]`
    gains `sequence` (signal, modes 9–11); `per_label.{label}.level_name` gains
    modes 9–11 and `sequence`'s role becomes `signal`; `relationships` loses
    `sequence`; `relationships.out_of_order_labels[]` loses its only consumer
    and its mode 9. `path_classification_conflicts()` and
    `rule_declaration_conflicts()` are `()`.
- **A11 (measured, out of scope: `mislabel` misreads the same maps).** On AC4's
  map `mislabel/ordering` fires on (20, 21), (21, 22) and (22, 23); on AC6's
  map it fires on (27, 29). The `non_monotonic_pairs[]` walk uses the
  pipeline's ascending-integer centroid order, like the relationships fields.
  Reordering that sequence moves the spline fit and every Stage 3 feature, so
  it is not done here (Left open, and one `insights.md` line).
- **A12:** no human gate, and no environment-gated capability.

**Correction (2026-09-28, before any test was written): A4's direction and
A10's scope.** A1–A12 stand as written. Two things are corrected.

- **A4 corrected: the traversal direction is chosen, not fixed.** A4 fixed
  head-to-tail as descending `centroid_mm[2]`. Measured with that rule, the unit
  fixtures that stack ascending labels at ascending z produce `sequence` findings:
  - `tests/synthetic.py`'s `labelled_blocks_case` (C3 above C1 and C2) gives
    `shift` on label 3;
  - `anisotropic_case` gives `swap` on (1, 2).
  `tests/test_010_pipeline.py:272` and `tests/test_cli_run.py:143` and `:428`
  pin "every finding is `bounds`" on those fixtures, and the sweeps did not list
  them. So the rule follows the house convention of items 131/132 and item 189's
  A4: a full reversal reads as the same spine traversed the other way.
  - Sort the kept entries both ways: descending `centroid_mm[2]` and ascending
    `centroid_mm[2]`, ties broken by ascending label in both.
  - For each order, count the inversions: pairs *i < j* whose rank (A5) at *i*
    exceeds the rank at *j*.
  - Take the ascending order only when it has strictly fewer inversions.
    Otherwise take the descending order, which is anatomical head-to-tail in the
    RAS world frame.
  - "Head-to-tail order" in A5–A7 means the chosen order.
  - Measured with the choice on 2026-09-28: every AC fixture, AC10 and
    `sequence_break` give the values the ACs state. Both corpora change exactly
    as A10 says. `labelled_blocks_case` and `anisotropic_case` fire no
    `sequence` finding, so their tests need no edit.
  - The cost has two parts. A full reversal is not reported: relabelling
    20↔24 and 21↔23 on the clean map fires nothing, from `sequence` or
    `mislabel`. A two-label record is never out of order. A swap of the two end
    labels reads as a swap of the middle: relabelling 20↔24 gives `swap` on
    {21, 23} (L4, L2). Both limits are Left open.
- **A10 extended: the manifest does not move, confirmed.**
  `tests/corpus/manifest.json` is written from each operator's `Expectation`
  in `src/segfacet/synth/`, and this item edits neither.
  `relabel_swap` keeps `expected_rule_ids ["mislabel"]` and `remove_level`
  keeps `["coverage"]`. `failure_modes._corpus_case_conflicts` compares the
  geometric manifest by subset, so both stay conflict-free against the
  re-authored `expected_firing`. So these stay green unedited:
  - `tests/test_103_feature_catalogue.py:604` and `:625`;
  - `tests/test_136_rule_mode_declarations.py:337` (its co-detection set derives
    from the manifest);
  - `tests/test_039_identity_ordering_alignment_perturbations.py:431` and
    `:414`.
- **Severities, confirmed.** Every new `sequence` finding is
  `flagged-for-review` under the bundled config, measured on all three corpus
  cases. So `tests/test_145_eight_hypothesised_modes.py:1346` (mode 9's own
  rules measure `{"flagged-for-review"}`) and `tests/test_041_regression_suite.py`
  (manifest `expected_verdict`) hold.

## Implementation Steps

1. **`src/segfacet/heuristics/sequence.py`** — rewrite the rule per A4–A8.
   - Import `CANONICAL_ORDER`, `SACRUM`, `expected_level_sequence` and
     `resolve_section_counts` from `segfacet.labels` (item 186's helpers; no
     re-implementation of the section model) and `ConditionOptIn` from
     `segfacet.heuristics.rule`.
   - Keep `_severity_from_param` and the up-front severity read. Drop
     `_label_for_level` (labels come from each kept entry) and the
     `relationships` read.
   - Reason tags as module constants: `_ORDER_TAG = "Non-continuous label sequence:"`,
     `_SKIP_TAG = "Skipped level label:"`,
     `_TRANSITIONAL_TAG = "Transitional level label without field-of-view evidence:"`.
   - `mode_declaration`: `modes=(9, 10, 11)`; `evidence` re-worded (which cases
     fire which detector, and that modes 10 and 11 are analytic); consumed
     paths, ascending: `per_label` (bookkeeping, container),
     `per_label.{label}.centroid.centroid_mm[]` (signal),
     `per_label.{label}.label` (bookkeeping, identity),
     `per_label.{label}.level_name` (signal). Detectors, ascending: `shift`
     and `swap` with both signal paths, `skip` and `transitional` with
     `level_name` only.
   - `condition_opt_ins` per A8, with a `reason` saying a swap reads as
     displaced and that the head-to-tail order survives a displacement that
     does not pass a neighbour.
   - Rewrite the module docstring: the four sub-types and their modes, the
     head-to-tail order, why `relationships` is not read (the integer-order
     defect, `insights.md` 2026-09-27), the opt-in, and item 192 credited.
   - Confirm `segfacet.catalogue.path_classification_conflicts() == ()`.
2. **`src/segfacet/failure_modes.py`** — A8 and A9's data edits.
3. **The same file, prose.** Rewrite, each re-measured and dated:
   - mode 9's `mechanism`. It must keep the tokens `CANONICAL_ORDER`, `T13`,
     `T12`, `L1`, `L2` and `needs-real-data`, name `sequence`, and name no path
     that no mode-9 rule reads (`relationships.is_continuous` and
     `relationships.out_of_order_labels[]` included). Say: `sequence`'s `swap`
     and `shift` detectors order labels by `per_label.{label}.centroid.centroid_mm[]`
     and rank them by `CANONICAL_ORDER` (which puts T13 between T12 and L1);
     `relabel_swap` fires `swap` beside `mislabel`'s `ordering`;
     `sequence_break`'s tail T13 fires `shift`; the edge stays
     `needs-real-data` because a multi-relabel scramble is not expressible by
     the fixture generator.
   - mode 10's `mechanism`: add that `sequence`'s `skip` detector reads the same
     gap from `per_label.{label}.level_name`, and co-detects on `remove_level`
     like `coverage`.
   - mode 11's `mechanism`: `sequence`'s `transitional` detector reads
     `per_label.{label}.level_name` and fires on a non-default count item 186
     does not accept. Drop the "No rule and no corpus case: listed as proposed"
     sentence and the `relationships.present_levels[]` path, which no mode-11
     rule reads (`tests/test_138_traceability_matrix.py` AC31 check (1)).
   - mode 6's `mechanism`: `remove_level` is co-detected by `coverage` and by
     `sequence`'s `skip`, both mode-10 detectors.
   - the displaced-vertebra condition's `mechanism`: `sequence` opts in, for the
     reason A8 gives.
   - the `reason` of `relabel_swap`, `remove_level` and `sequence_break`: the
     measured firing of A10. None may contain `rank(v) == v - 1`.
   - A dated item-192 paragraph in the module docstring.
4. **`src/segfacet/feature_docs.py`** — the module docstring's mode-9 bullet
   says `sequence` reads its signal from the `relationships` sub-block. Say
   instead that `relationships.is_continuous` stays the metric anchor and that
   `sequence` reads `per_label` since item 192. No `FeatureDoc` and no
   `MODE_ANCHOR_PATHS` entry changes.
5. **`src/segfacet/default_config.yaml`** — the `sequence` comment only: it
   reports four sub-types from per-label centroids and level names. No key
   changes (A7).
6. **Regenerate**, each module's `main` twice into temp paths, byte-compare the
   runs, then write the committed copy:
   - `segfacet.failure_modes` → `docs/aide/failure_modes.generated.{json,md}`;
   - `segfacet.traceability` → `docs/aide/traceability_matrix.generated.{json,md}`;
   - `segfacet.catalogue` → `docs/aide/feature_catalogue.generated.{json,md}`;
   - `segfacet.golden_evidence`, into temp only. It must equal the committed
     file (A10). If it does not, hand back.
7. **Reconcile** the tests under Testing Strategy, each edit with a dated
   item-192 comment.
8. Run `python .aide/scripts/aide.py scope 192` and
   `python .aide/scripts/aide.py check`. Both must report no error.

No dependency is added.

**Correction (2026-09-28, before any test was written): two steps are
refined.** Steps 1–8 stand.

- Step 1 applies A4's corrected direction choice. `per_label` stays the
  **first** entry of `consumed_paths`: `tests/test_148_per_path_mode_attribution.py:415`
  drops `consumed_paths[0]` as its adversarial probe. `evaluate` is the module's
  only `def evaluate`, because `test_148` AC17 counts 12 across the rule
  modules. Nothing inside `evaluate` names `mode_declaration`,
  `consumed_paths` or `ConsumedPath` (`test_148:1031`). The module holds no mode
  name, short name, evidence-rung literal, `MODE_ANCHOR_PATHS` reference
  (`test_147:253`, `:291`, `:353`) or `rank(v) == v - 1` (`test_147:559`,
  `test_154:477`).
- Step 3's mode-11 mechanism must contain the whole word `sequence`
  (`test_138` AC31 and `test_147:519`) and must not name
  `relationships.present_levels[]`.
- **Step 7a (new): amend the attested count clauses** with
  `python .aide/scripts/aide.py progress amend`, as item 188's step 8 did.
  Re-measure every number live first. The values below were measured on the
  prototype. Each `--evidence` starts
  `Item 192 (2026-09-28): sequence serves modes 9-11 by sub-type; mode 11 derives implemented at needs-real-data, mode 10 gains a second edge. Re-measured live:`
  and continues with:
  - `amend 30 --criterion 1`: `derived status counts over 16 modes: validated 6, implemented 4, specified 1, proposed 5; validated through a pipeline-detected case 5, through a reconstructed record only 1.`
  - `amend 30 --criterion 3`: `derived mode rung counts: synthetic-demonstrable 5, needs-real-data 4, structurally-unobservable 1, none 6; per-edge rung counts over 20 edges: synthetic-demonstrable 5, needs-real-data 14, structurally-unobservable 1.`
  - `amend 20 --criterion 5`: `derived status counts over 16 modes: validated 6, implemented 4, specified 1, proposed 5. derived mode rung counts: synthetic-demonstrable 5, needs-real-data 4, structurally-unobservable 1, none 6.`

  These clauses are what `tests/test_151_stage30_validation.py`'s AC35 and
  `tests/test_169_stage32_validation.py` (lines 229 and 296) read, taking the
  last match in each section. `docs/aide/progress.md` is always authorised, so
  it is not listed below. Only these appended amendments are made there.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/sequence.py` — the four sub-type detectors and the opt-in (step 1).
- `src/segfacet/failure_modes.py` — modes 6, 9, 10, 11 and the displaced-vertebra condition (steps 2–3).
- `src/segfacet/feature_docs.py` — the module docstring's mode-9 bullet (step 4).
- `src/segfacet/default_config.yaml` — the `sequence` comment only (step 5).
- `docs/aide/failure_modes.generated.json` — regenerated (step 6).
- `docs/aide/failure_modes.generated.md` — regenerated.
- `docs/aide/traceability_matrix.generated.json` — regenerated.
- `docs/aide/traceability_matrix.generated.md` — regenerated.
- `docs/aide/feature_catalogue.generated.json` — regenerated.
- `docs/aide/feature_catalogue.generated.md` — regenerated.
- `tests/test_192_sequence_sub_types.py` — **new**: this item's test module.
- `tests/test_030_sequence_continuity.py` — its records move onto per-label centroids (Testing Strategy).
- `tests/test_098_stray_components.py` — three entries of `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`.
- `tests/test_138_traceability_matrix.py` — the proposed-mode set loses 11.

**The reconciliation fence.** Every edit to an existing test is one of: a
moved literal (a firing set, a finding list, a reason, a detector id, a
proposed-mode set, a count); a hand-built record given centroids so the
rewritten rule can read it; or an assertion about the retired
`relationships.out_of_order_labels[]` input re-pointed to the measured
behaviour of the new rule. Each carries a dated item-192 comment. No test is
retired, skipped, `xfail`-marked or loosened. **A red test in a file not
listed here is a hand-back to spec-author**: the read-only sweeps commissioned
for this list had not reported when the spec was committed (Testing
Strategy).

**Asserts against:**

- `src/segfacet/labels.py` — A1's functions, read and unchanged.
- `src/segfacet/heuristics/runner.py` — the gate AC10 exercises, unchanged.
- `src/segfacet/features/relationships.py` — unchanged (Not in scope).
- `tests/corpus/manifest.json` — must not move (A10).
- `tests/corpus/fixtures/clean_control_seg.nii.gz` — AC2–AC6 and AC10 relabel it.
- `tests/corpus/fixtures/relabel_swap_seg.nii.gz` — AC1 reads it.
- `tests/corpus/fixtures/sequence_break_seg.nii.gz` — AC7 reads it.
- `docs/aide/golden_evidence.generated.json` — must not move (A10).
- `tests/test_163_specificity_ratchet.py` — red unless step 2 re-authors `relabel_swap` and `remove_level`.
- `tests/test_191_condition_gate.py` — AC10 and AC12 green unedited once step 2 updates `opting_in_rules`.
- `tests/test_039_identity_ordering_alignment_perturbations.py` — its `startswith("Non-continuous label sequence:")` checks hold (A7).
This section was amended on 2026-09-28, before any test was written, after the
three read-only sweeps reported. The lists above stand, with one exception.
Two Asserts-against bullets were removed from the committed list:
`test_147_specification_is_the_record.py` (AC10's mode-9 mechanism tokens) and
`test_145_eight_hypothesised_modes.py` (`test_ac10b`'s mode-9 mechanism
tokens). Both files also pin mode 11 as proposed, so they move to May change
below. A path left under both lists would make `aide scope` report every
authorised edit to it as a contradiction. Their mode-9 mechanism-token tests
still pass unedited, because step 3 keeps the tokens.
`tests/test_138_traceability_matrix.py` needs more edits than line 1298. The
reconciliation fence is unchanged, and the exact edits are under the Testing
Strategy's correction of the same date.

**May change:**

- `tests/test_035_failure_modes.py` — `_mode7_record` gains centroids (amended 2026-09-28).
- `tests/test_038_coverage_border_overlap_perturbations.py` — AC5 admits `sequence`'s case-level `skip` (amended 2026-09-28).
- `tests/test_103_feature_catalogue.py` — one AC10 parameter row (amended 2026-09-28).
- `tests/test_116_ras_native_corpus.py` — item 192's added pairs stripped (amended 2026-09-28).
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — two `_PRE_129_FINDINGS` entries (amended 2026-09-28).
- `tests/test_132_monotonicity_against_traversal_order.py` — AC13, AC25 and AC26 read two findings on `relabel_swap` (amended 2026-09-28).
- `tests/test_136_rule_mode_declarations.py` — `_CORROBORATED["sequence"]` (amended 2026-09-28).
- `tests/test_137_mode_less_rule_disposition.py` — two mode-evidence buckets (amended 2026-09-28).
- `tests/test_145_eight_hypothesised_modes.py` — mode 11 leaves the proposed set; mode 10 gains `sequence` (amended 2026-09-28).
- `tests/test_146_ninth_mode_and_first_proposed.py` — mode 11 joins the specified ids (amended 2026-09-28).
- `tests/test_147_specification_is_the_record.py` — edgeless set, mode 11's derived status, AC11's records (amended 2026-09-28).
- `tests/test_148_per_path_mode_attribution.py` — the unreachable-mode set (amended 2026-09-28).
- `tests/test_149_conformance_report.py` — degenerate modes and mode 9's read path (amended 2026-09-28).
- `tests/test_151_stage30_validation.py` — AC12's `total_edges == 18` literal becomes 20; AC35 reads step 7a's clauses unedited (amended 2026-09-28).

**Asserts against:**

- `tests/test_169_stage32_validation.py` — reads step 7a's Stage 20 clause (amended 2026-09-28).
- `tests/test_102_stage18_validation.py` — parametrised over `test_098`'s reconciled constant, unedited (amended 2026-09-28).
- `tests/test_143_s_axis_correction.py` — AC9 reads the same constant, unedited (amended 2026-09-28).
- `tests/test_131_tangent_direction_normalisation.py` — calls `test_129`'s reconciled check, unedited (amended 2026-09-28).
- `tests/test_010_pipeline.py` — `labelled_blocks_case` fires no `sequence` finding under A4's corrected direction (amended 2026-09-28).
- `tests/test_cli_run.py` — the same, for `labelled_blocks_case` and `anisotropic_case` (amended 2026-09-28).

## Testing Strategy

The test module is `tests/test_192_sequence_sub_types.py`, one test per AC.
`relabel` is a module helper built with NumPy on `loaded_seg_image`'s data and
`nibabel.Nifti1Image(data, img.affine, img.header)`, reading each replacement
from the original array. Every AC fixture and named case below was verified
by the scratch probe of Assumptions (2026-09-28).

Named adversarial cases, and no others:

- **non-adjacent-swap-names-moved-labels:** `seq(relabel({20: 24, 24: 20})) == {("swap", frozenset({20, 24}))}`.
  It guards naming the descent pairs (21–23) instead of the exchanged labels.
- **lumbar-reading-uncorroborated:** `seq(relabel({24: 26})) == {("transitional", frozenset({23}))}`
  (L1–L4 then S1, no T12). It guards a `transitional` detector that reads only
  the thoracic section.
- **sacral-labels-share-one-rank:** `seq(relabel({23: 29, 24: 26})) == {("skip", frozenset())}`
  (L1–L3, then S2 above S1). It guards ranking S1–S6 separately, which would
  report a swap inside the one sacral element item 186 defines.
- **no-centroid-no-finding:** `get_rule("sequence").evaluate(r, cfg) == []` for
  `r = {"relationships": {"present_levels": ["L1", "T12"], "is_continuous": False, "out_of_order_labels": ["T12"]}, "per_label": {"19": {"label": 19, "level_name": "T12"}, "20": {"label": 20, "level_name": "L1"}}}`.
  It guards a fallback to the integer-ordered `out_of_order_labels[]`, which is
  the defect this item removes.

**Existing tests to reconcile** (measured on the prototype, 2026-09-28).

- **`tests/test_030_sequence_continuity.py`.** Its records carry only `label`
  and `level_name`, so the rewritten rule reads nothing from them.
  `_make_per_label_entry` gains a `centroid: {"centroid_mm": [0.0, 0.0, z]}`
  and `_make_record` gives the listed levels `z = n − i` for the *i*-th level
  of the record's order (the order `out_of_order_labels` used to express, now
  head-to-tail). Then:
  - AC1 ×3, AC2, AC7, AC8, AC9 (None, absent, keys absent, not-a-mapping),
    AC11 ×2, AC12 ×3, AC13 two-runs, AC14 ×3, `is_continuous_false_but_empty`,
    `out_of_order_labels_absent_key` and `determinism_with_unmappable_offender`
    keep their assertions.
  - AC3 (L1, T12) keeps its assertions: one finding, detector `swap`, reason
    `"Non-continuous label sequence: swap of L1, T12."`.
  - AC4: `labels == frozenset({19, 20})` (a swap names both).
  - AC5 (L2, T12, L1): one finding, `shift`, reason
    `"Non-continuous label sequence: shift of L2."`, `labels == frozenset({21})`.
  - AC6 (L1, T12, L2, L5): two findings, `skip` with reason
    `"Skipped level label: L3, L4 absent between present levels."` and empty
    labels, and `swap` on `frozenset({19, 20})` naming T12.
  - AC13 reason order (L2, L1): unchanged, reason
    `"Non-continuous label sequence: swap of L2, L1."`.
  - `test_adv_three_offenders_all_named_and_attributed` (L5, T12, L1, L2): two
    findings, `shift` on `frozenset({24})` (reason `"... shift of L5."`) and
    `skip` naming L3, L4.
  - `test_ac9_per_label_empty_no_raise`, `test_ac9_per_label_absent_no_raise`,
    both AC10 tests and `test_adv_per_label_entry_not_a_mapping_no_raise`
    assert `[]`: an offender without a per-label entry has no position to judge.
  - The module docstring gains a dated item-192 paragraph saying the rule's
    input moved from `out_of_order_labels[]` to per-label centroids.
- **`tests/test_098_stray_components.py`** `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`:
  - `remove_level`: append `{"rule_id": "sequence", "detector_id": "skip", "severity": "flagged-for-review", "labels": [], "reason": "Skipped level label: L3 absent between present levels."}` after the `coverage` finding;
  - `relabel_swap`: append the `sequence` `swap` finding on `[21, 22]`, reason
    `"Non-continuous label sequence: swap of L3, L2."`, after `mislabel`'s;
  - `sequence_break`: reason `"Non-continuous label sequence: shift of T13."`,
    with `"detector_id": "shift"` if the entry's siblings carry the key.
  Verdicts stay `flagged-for-review`. `tests/test_102_stage18_validation.py`
  reads the same constant and needs no edit.
- **`tests/test_138_traceability_matrix.py`** line 1298:
  `PROPOSED_MODES == {5, 7, 12, 13, 14}`.

**Not yet swept.** Three read-only sweeps were commissioned (the `sequence`
findings, the specification and matrix, the catalogue and docs) and had not
reported when this spec was committed. Pins they would have found are most
likely in: tests pinning mode 11 as `proposed` or the proposed/implemented
counts (`test_145`, `test_146`, `test_150`, `test_151`, `test_188`); the
`discontinuity` detector id or a registry detector count (`test_164`, `test_162`);
`sequence`'s `exercised_by`, `feature_path_count` or `by_rule` (`test_149`,
`test_162`); the catalogue's `out_of_order_labels[]` or `level_name` roles
(`test_103`, `test_148`); `relabel_swap`/`remove_level` firing literals
(`test_041`, `test_116`, `test_125`, `test_151`). The builder treats any red
test outside the list above as a hand-back, and spec-author amends this list.

**Correction (2026-09-28, before any test was written): the sweeps' pins and
A4's direction.** The list above stands except where a bullet below replaces
it. Every value below was measured on 2026-09-28 against the scratch prototype
with A4's corrected direction choice. That prototype is Implementation Step 1,
plus Step 2's data edits applied to a copy of `failure_modes.py`, run under
`python -S` from its own `src`. Each edit carries a dated item-192 comment.

The new corpus findings, measured through `segfacet.synth.regression.pipeline_findings`
and `segfacet.synth.golden.build_report_for_case`, in report order:

| Case | Findings (`rule_id`, `detector_id`, `severity`, `labels`, `reason`) | Verdict |
|---|---|---|
| `relabel_swap` | `mislabel`, `ordering`, `flagged-for-review`, `[21, 22]`, unchanged; then `sequence`, `swap`, `flagged-for-review`, `[21, 22]`, `"Non-continuous label sequence: swap of L3, L2."` | `flagged-for-review` |
| `remove_level` | `coverage`, `missing_interior`, `flagged-for-review`, `[]`, unchanged; then `sequence`, `skip`, `flagged-for-review`, `[]`, `"Skipped level label: L3 absent between present levels."` | `flagged-for-review` |
| `sequence_break` | `sequence`, `shift`, `flagged-for-review`, `[28]`, `"Non-continuous label sequence: shift of T13."` | `flagged-for-review` |

**Named adversarial cases, corrected.** One case is replaced and one is added.
The other three stand.

- **non-adjacent-swap-names-moved-labels:** withdrawn. Under the corrected
  direction, relabelling 20↔24 gives `{("swap", frozenset({21, 23}))}` (A4's
  correction, Left open).
- **full-reversal-reads-as-flipped:** `seq(relabel({20: 24, 21: 23, 23: 21, 24: 20})) == set()`.
  It guards a fixed descending direction, which makes every unit fixture that
  stacks ascending labels at ascending z fire.
- **ascending-fixture-fires-no-sequence:** for `tests.synthetic.labelled_blocks_case()`
  and `anisotropic_case()`, the findings of
  `run_rules(extract_feature_record(case.seg_img, cfg), cfg)` include no
  `sequence` finding. It guards the same regression on the fixtures
  `tests/test_010_pipeline.py` and `tests/test_cli_run.py` pin.

**`tests/test_030_sequence_continuity.py`, corrected.** The bullet above
stands, with two changes:
- A two-label record is never out of order under A4's correction, so every
  record whose order was L1, T12 gains **L2** (label 21) as a third, in-order
  level at the tail. That applies to AC3, AC4, AC11 ×2, AC12's first test,
  `test_ac14_out_of_order_labels_list_not_mutated` and
  `test_ac14_per_label_dict_not_mutated`.
- AC13's reason-order record (L2, L1) gains **L3** (label 22) at the tail.

Measured, with `z = n − i` for the *i*-th level of the record's order:
- L1, T12, L2: one `swap` on `frozenset({19, 20})`, reason
  `"Non-continuous label sequence: swap of L1, T12."`. AC3's existing
  assertions hold, and AC4's labels become `frozenset({19, 20})`.
- L2, T12, L1 (AC5, AC13 two-runs, AC14 whole-record): ascending has fewer
  inversions, so one `swap` on `frozenset({19, 20})`, reason
  `"Non-continuous label sequence: swap of L1, T12."`. AC5's
  `reason.index("T12") < reason.index("L1")` becomes
  `reason.index("L1") < reason.index("T12")`. Its labels assertion
  `frozenset({19, 20})` holds.
- L1, T12, L2, L5 (AC6): two findings, in this order:
  - `skip`, empty labels, `"Skipped level label: L3, L4 absent between present levels."`;
  - `swap` on `frozenset({19, 20})`, `"Non-continuous label sequence: swap of L1, T12."`.
- L2, L1, L3 (AC13 reason order): one `swap` on `frozenset({20, 21})`, reason
  `"Non-continuous label sequence: swap of L2, L1."`. The existing assertion
  holds.
- L5, T12, L1, L2 (`test_adv_three_offenders_all_named_and_attributed`): the
  inversion counts tie (3 and 3), so descending is kept. Two findings:
  - `shift` on `frozenset({24})`, `"Non-continuous label sequence: shift of L5."`;
  - `skip`, empty labels, `"Skipped level label: L3, L4 absent between present levels."`.
- Every severity is `flagged-for-review` under `default_config()`. AC11's
  `severity: fail` config still gives `Severity.FAIL`.

**Tests the sweeps found, with their exact edits:**

- **`tests/test_035_failure_modes.py`.** `_mode7_record` (line 242): each
  `per_label` entry gains `"centroid": {"centroid_mm": [0.0, 0.0, z]}`, with
  L1 at z 3.0 and T12 at z 2.0. Add `_L2: {"label": _L2, "level_name": "L2", "centroid": {"centroid_mm": [0.0, 0.0, 1.0]}}`.
  Measured: one `sequence` `swap` on `frozenset({19, 20})`, so AC25's
  `{_L1, _T12} <= f.labels`, AC27's table row `(7, _mode7_record, "sequence")`
  and the union test hold with no other edit. The records at lines 406, 452 and
  470 stay silent, because they carry no centroids.
- **`tests/test_038_coverage_border_overlap_perturbations.py`**
  `test_ac5_remove_level_only_fired_rule_is_coverage_and_case_level`
  (line 217): `f.rule_id == "coverage"` becomes
  `f.rule_id in {"coverage", "sequence"}`. Add
  `{f.rule_id for f in findings} == {"coverage", "sequence"}` so the set is
  still exact. The case-level assertion holds, since `skip` is case-level.
- **`tests/test_103_feature_catalogue.py`** AC10 parameter (line 538):
  `("relationships.out_of_order_labels[]", "sequence")` becomes
  `("per_label.{label}.centroid.centroid_mm[]", "sequence")`. Measured: that
  entry's `rule_evidence` holds `("sequence", "observed")`. Lines 604 and 625
  stay (A10 extended).
- **`tests/test_116_ras_native_corpus.py`** `test_ac7_case_identity_preserved_vs_merge_base`
  (line 416): add, beside `_ITEM_132_ADDED_MISLABEL_PAIR`,
  `_ITEM_192_ADDED_SEQUENCE_PAIRS = {"relabel_swap": ("sequence", (21, 22)), "remove_level": ("sequence", ())}`.
  For those two cases, assert the pair is present in `fresh_pairs` and strip
  it, the way the item-132 pair is handled. `sequence_break`'s pair,
  `("sequence", (28,))`, is unchanged against the aeb2f55 golden. The test
  skips where that commit is absent.
- **`tests/test_129_coincident_centroids_and_held_out_floor.py`** `_PRE_129_FINDINGS`
  (line 716):
  - `"relabel_swap"` becomes `{("mislabel", (21, 22)), ("sequence", (21, 22))}`;
  - `"remove_level"` becomes `{("coverage", ()), ("sequence", ())}`;
  - `"sequence_break"` stays `{("sequence", (28,))}`.
  `tests/test_131_tangent_direction_normalisation.py` calls the reconciled
  check unedited.
- **`tests/test_132_monotonicity_against_traversal_order.py`:**
  - AC13 (line 418): `len(case_result.findings) == 2`. `findings[0]` keeps
    every existing assertion (`mislabel`, `{21, 22}`, `FLAG`, the reason
    prefix). Add: `findings[1].rule_id == "sequence"`,
    `findings[1].detector_id == "swap"` and
    `findings[1].labels == frozenset({21, 22})`.
  - AC25 (line 578): the literal becomes
    `{("mislabel", (21, 22)), ("sequence", (21, 22))}`.
  - AC26 (lines 586–588): `len(expected["findings"]) == 2`,
    `expected["findings"][0]["rule_id"] == "mislabel"` and
    `expected["findings"][1]["rule_id"] == "sequence"`.
- **`tests/test_098_stray_components.py`** `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`
  per the table above:
  - `relabel_swap` (line 926): append
    `{"rule_id": "sequence", "detector_id": "swap", "severity": "flagged-for-review", "labels": [21, 22], "reason": "Non-continuous label sequence: swap of L3, L2."}`.
  - `remove_level` (line 942): append
    `{"rule_id": "sequence", "detector_id": "skip", "severity": "flagged-for-review", "labels": [], "reason": "Skipped level label: L3 absent between present levels."}`.
  - `sequence_break` (line 978): reason
    `"Non-continuous label sequence: shift of T13."`, and add
    `"detector_id": "shift"`, as its siblings carry the key.
  `test_102`, `test_143` and the other importers (`test_089`, `test_090`,
  `test_094`, `test_105`, `test_108`, `test_123`, `test_126`, `test_135`)
  read the reconciled constant unedited. A red one among them is a hand-back.
- **`tests/test_136_rule_mode_declarations.py`** `_CORROBORATED["sequence"]`
  (line 119): `(9,)` becomes `(9, 10, 11)`.
- **`tests/test_137_mode_less_rule_disposition.py`**
  `test_adv_measured_artifact_movement_counts_from_spec` (line 908):
  - `("rule_mode_less", "rule_bookkeeping"): 7` becomes `6`;
  - add the bucket
    `("rule_mode_map", "rule_declaration", "rule_mode_less", "rule_bookkeeping"): 1`
    (`per_label.{label}.level_name`).
  Every other count is unchanged, measured: 145 entries, `()` 91,
  `("rule_mode_map", "rule_declaration")` 10, mode 1 12, mode 2 7, mode 16 2.
- **`tests/test_138_traceability_matrix.py`:**
  - line 984: `{"5", "7", "12", "13", "14"}`;
  - line 985: `{"5", "6", "7", "12", "13", "14"}`;
  - line 1298: `PROPOSED_MODES == {5, 7, 12, 13, 14}`;
  - the analytic witness (line 1397): add `(10, "sequence")` and `(11, "sequence")`;
  - line 1436: `mixed == {"bounds", "sequence"}`. `sequence` is corpus-attributed
    for mode 9 and analytic for modes 10 and 11, as measured in the matrix's
    `rule_attribution`.
  - The dated witness comments move with each edit. AC17 (line 1189) and AC31
    stay unedited, given step 3's mechanism constraints.
- **`tests/test_145_eight_hypothesised_modes.py`:**
  - `_PROPOSED_MODE_IDS` (line 96) becomes `(5, 7, 12, 13, 14)`, which drops the
    `[11]` parametrisations at lines 356, 508, 579, 1361 and 1559;
  - `_EXPECTED_DERIVED_STATUS[11]` (line 132) becomes `"implemented"`;
  - line 1350: `{"coverage", "sequence"}`;
  - line 1352: `_live_declared_rule_ids(10) == {"coverage", "sequence"}`.
  Line 1335 (`failing == [9, 10]`) stays, because mode 11's severity is
  `flagged-for-review`. Line 1346 stays (measured `{"flagged-for-review"}`).
- **`tests/test_146_ninth_mode_and_first_proposed.py`** line 1218:
  `specified_ids == [1, 2, 3, 4, 6, 8, 9, 10, 11, 15, 16]`. The loop below it
  must accept mode 11 deriving `implemented`, which is already the
  specified-and-declared branch. Edit only the literal and its comment.
- **`tests/test_147_specification_is_the_record.py`:**
  - line 487: `{5, 6, 7, 12, 13, 14}`;
  - line 1214: `_EXPECTED_DERIVED_STATUS[11] = "implemented"`;
  - AC11 `test_ac11_sequence_rule_caps_nothing` (line 630): `_sequence_record`
    takes an ordered level list and builds `per_label` entries with centroids
    at `z = n − i`, using labels from `DEFAULT_LABEL_MAP`. "One descent" is
    `["L1", "T12", "L2"]`, measured as one finding, `swap` on
    `frozenset({19, 20})`. "Two descents" is
    `["L1", "T12", "L2", "L4", "L3", "L5"]`, measured as one finding, `swap` on
    `frozenset({19, 20, 22, 23})`, reason
    `"Non-continuous label sequence: swap of L1, T12, L4, L3."`. Both
    `len(...) == 1` assertions hold, so the claim ("caps nothing: every
    offender in one finding") stays.
- **`tests/test_148_per_path_mode_attribution.py`** line 671:
  `unreachable == {5, 7, 12, 13, 14}`. Line 850 is a containment check and
  stays.
- **`tests/test_149_conformance_report.py`:**
  - `_DEGENERATE_MODES` (line 567) becomes `(5, 6, 7, 12, 13, 14)`;
  - `_AC9_SPLIT_COLUMN_MODES`' mode-9 row (line 629) becomes
    `(9, "relationships.is_continuous", "per_label.{label}.centroid.centroid_mm[]")`.
    Measured: that path is in mode 9's `read_paths`, and the anchor is not.
- **`tests/test_151_stage30_validation.py`** AC12 (line 474):
  `total_edges == 20`. The two new edges are `sequence` on modes 10 and 11,
  and the mode-9 `sequence` edge is still one edge. AC35 reads step 7a's clauses
  unedited. `tests/test_169_stage32_validation.py` does the same for Stage 20.

**Why the three pins the sweeps missed need no edit.**
`tests/test_010_pipeline.py:272`, `tests/test_cli_run.py:143` and
`tests/test_cli_run.py:428` pin "every finding is `bounds`" on
`labelled_blocks_case` and `anisotropic_case`. Under A4's corrected direction
neither fixture fires `sequence` (measured, and pinned by
`ascending-fixture-fires-no-sequence`).

**Still unmeasured.** `make_labelmap` is used by 25 test modules, and the
sweeps covered the ones that assert on findings. A fixture whose labels are
neither ascending nor descending in z would still fire `sequence`. No such
fixture was found. The builder treats a red test outside these lists as a
hand-back.

## Validation

Replay `sequence_break` and `relabel_swap` through the CLI, without a
reference, for the reason `CLAUDE.md` gives:

```
.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/sequence_break_seg.nii.gz --out <tmp1> --no-reference
.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/relabel_swap_seg.nii.gz --out <tmp2> --no-reference
```

- `<tmp1>/segfacet_report.json` holds one finding, `rule_id` `sequence`,
  `detector_id` `shift`, labels `[28]`.
- `<tmp2>/segfacet_report.json` holds a `sequence` finding with `detector_id`
  `swap` and labels `[21, 22]`, beside `mislabel`'s.
- In `docs/aide/failure_modes.generated.md`, mode 11 is `specified` /
  `implemented` with the one `sequence` edge, and no mode-12 edge exists.

No environment profile is needed.

## Dependencies

- Item 186: the expected sequence and `resolve_section_counts`, which the
  `transitional` and `skip` detectors read (A1) (✅).
- Item 191: the condition gate and `Rule.condition_opt_ins`, which the
  `displaced_vertebra` opt-in uses (A2) (✅).
- Items 187–190: last re-measured the corpus firing sets, the rule count and the
  matrix this item's ratchet run reads (✅).

**Downstream:**

- Item 194's mode-1 attribution and item 195's `force_overlap` removal
  regenerate the same artifacts.
- Stage 33 D4's `rules.generated.md` gains one row per `sequence` detector, and
  its detector-granular bar reads AC9's mapping.

## Decisions & Trade-offs

**Implemented as specified (2026-09-28).** `src/segfacet/heuristics/sequence.py`
was rewritten per A4-A8: it reads only `per_label` (no `relationships`),
chooses the head-to-tail direction by the inversion-count tie-break (A4
corrected), ranks by `CANONICAL_ORDER` with S1-S6 collapsed to one rank (A5),
decomposes the rank permutation into cycles (a 2-cycle names both members as
`swap`; a longer cycle names its largest-|displacement| member(s) as `shift`,
one finding aggregating every cycle of that shape), and derives `skip`/
`transitional` from `segfacet.labels.resolve_section_counts`'s reading (A6).
Every measured value in the spec (AC1-AC10, the four surviving named
adversarial cases, A9's corpus table, A10's manifest/golden-evidence
stability) reproduced exactly against the live implementation, including the
two `progress.md` amend clauses (Step 7a), which were re-measured live before
`aide progress amend` was run (derived status counts 6/4/1/5,
validated-via-pipeline 5/reconstructed-only 1, mode rung counts
5/4/1/6, per-edge rung counts over 20 edges 5/14/1). No deviation from the
spec's Assumptions or Implementation Steps was needed; no path outside
Authorised paths was touched.
- **Left open:** `relationships.is_continuous` and
  `relationships.out_of_order_labels[]` still walk ascending integer order, so
  they misread a correct T13 or `Cocc`. No rule reads them after this item, but
  `eval.per_mode.out_of_order_label_count` and the text report do. Changing
  their input order is a record change that moves those consumers, and this
  item changes only the rule.
- **Left open:** `mislabel`'s `ordering` detector misreads the same maps (A11).
  Its input is the pipeline's integer-ordered centroid sequence, which also
  feeds the spline fit.
- **Left open:** how a supplied section count reaches the rule (item 186's Left
  open). With none, a subject whose true thoracic count is 13 and whose scan
  lacks C7 is reported `transitional` on every scan.
- **Left open:** whether `sequence` opts in to `fov_truncation`. A truncated
  label keeps its name, and its centroid moves toward the interior. No case
  needs it yet.
- **Left open:** whether the mode-9 `sequence` edge rises to
  `synthetic-demonstrable` now that `relabel_swap` and `sequence_break` fire
  it. The at-the-bar review (D5) or D4's re-measurement decides that.
- **Left open** (added 2026-09-28, A4's correction): a full reversal and a
  two-label reversal are not reported, and an end-to-end swap (20↔24) is named
  as a swap of the middle labels (21, 23). Telling them apart needs an absolute
  head-to-tail direction, which the unit fixtures that stack ascending labels at
  ascending z do not honour. Using the RAS world direction outright is the
  alternative, and it needs those fixtures re-stacked first.
