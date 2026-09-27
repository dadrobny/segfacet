<!-- aide-template: item 2 -->
# Item 188 — `coverage` re-homed from mode 6 to mode 10

> **Created:** 2026-09-28 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-025.md`](../queue/queue-025.md) · Item 188
> **Objectives:** G2, G8
> **Suggested branch:** `aide/188-coverage-re-homed-from-mode`

---

## Description

This item implements roadmap Stage 33 D3's second bullet. It closes the `gap`
entry in `docs/aide/insights.md` dated 2026-09-22 (queue-022 review, the
`coverage` decision), and follows the maintainer feedback of 2026-09-25
recorded in `queue-025.md`.

**Why the move.** `coverage` reads `relationships.missing_levels[]` and
`relationships.present_levels[]`. Those are lists of labels. The rule sees a
missing *label* in the sequence and cannot see whether a vertebra is there. So
it serves mode 10 (skipped level label), a child of mode 8, and not mode 6
(vertebra not segmented). Today `coverage` declares `modes=(6,)` and is mode 6's
only edge, and mode 10 is authored `proposed` with no rule.

**What stays.** `remove_level` and `remove_level_relabel` stay attributed to
mode 6, in the specification and in the committed manifest. Mode 6 should fire
on both, and that is its detection target. `coverage` still fires on
`remove_level`. That firing is now a co-detection by mode 10's detector, and it
does not validate mode 6. Mode 6's own rule, over the inter-centroid spacing, is
decided later and is not in Stage 33 (roadmap Stage 33, scope decisions). So
after this item no rule declares mode 6. Its derived status is `specified` and
its derived rung is `None`, which is how the specification records that no rule
detects it yet. Neither case moves to another mode to fill the gap.

**What this item changes.**

- `heuristics/coverage.py`: `mode_declaration.modes` becomes `(10,)`. The
  evidence, the module docstring and the class comment are re-pointed at mode 10.
  The detectors, consumed paths, thresholds and firing do not change.
- `failure_modes.py`: mode 6 loses its `coverage` edge. Mode 10 gains a
  `coverage` edge at `needs-real-data` and is re-authored `specified`. Both
  mechanisms are rewritten, and so is the `remove_level` case's `reason`.
- `traceability.py`: the generated note says that a `specified` mode with no
  rule written yet is a hole too, and names mode 6.
- The three generated specification, matrix and catalogue documents are
  regenerated.
- The count clauses that `progress.md` attests for Stages 20 and 30 are amended
  with `aide progress amend`.
- The pins listed under Testing Strategy are reconciled.

**Not in scope.**

- No corpus change. Both manifests, every fixture, `synth/coverage_border_overlap.py`'s
  `Expectation`s and `docs/aide/corpus_sheet.png` stay as they are (A5).
- No new rule for mode 6, and no mode-10 corpus fixture (Left open).
- No change to `coverage`'s behaviour, and none to the `fov_truncation`
  condition's `exempting_rules` (item 191's).
- `sequence`'s sub-types across modes 8–11 (item 192), the detector-granular bar
  checker (Stage 33 D4) and the stage's re-stated detection count (D6) belong to
  other items.

## Acceptance Criteria

Terms used below:

- **"The coverage rule"** is the `CoverageRule` class in
  `segfacet.heuristics.coverage`, and **"its detector ids"** is
  `tuple(sorted(d.detector_id for d in CoverageRule.mode_declaration.detectors))`.
- **"Mode N"** is `segfacet.failure_modes.SPECIFICATION[N]`.
- **"The declared set of mode N"** is the set of `rule_id`s over
  `segfacet.heuristics.rule.iter_rule_declarations()` whose declaration is not
  `None` and lists N in `modes`. The test computes it.

- [ ] **AC1: `coverage` declares mode 10 alone.**
  `CoverageRule.mode_declaration.modes == (10,)`.
- [ ] **AC2: mode 10 carries the `coverage` edge at `needs-real-data`.** The
  edges of mode 10 whose `rule_id == "coverage"` are exactly
  `[IntendedRule(rule_id="coverage", detector_ids=<its detector ids>, evidence_rung="needs-real-data")]`.
- [ ] **AC3: mode 6 carries no edge.** `SPECIFICATION[6].intended_rules == ()`.
- [ ] **AC4: every `coverage` detector serves mode 10 alone.** For each id in
  its detector ids, `segfacet.failure_modes.modes_for_detector("coverage", id) == (10,)`.
- [ ] **AC5: no registered rule declares mode 6.** The declared set of mode 6
  is empty.
- [ ] **AC6: both `remove_level` cases stay attributed to mode 6.**
  `{c.case_id for c in SPECIFICATION[6].corpus_cases} == {"remove_level", "remove_level_relabel"}`.
- [ ] **AC7: mode 6's derived status records that no rule detects it.**
  `segfacet.failure_modes.derive_status(SPECIFICATION[6]) == "specified"`.
- [ ] **AC8: mode 6's derived rung is absent.**
  `segfacet.failure_modes.derive_mode_rung(SPECIFICATION[6]) is None`.
- [ ] **AC9: mode 10 derives `implemented`.**
  `segfacet.failure_modes.derive_status(SPECIFICATION[10]) == "implemented"`.
- [ ] **AC10: mode 10's derived rung is `needs-real-data`.**
  `segfacet.failure_modes.derive_mode_rung(SPECIFICATION[10]) == "needs-real-data"`.

Why each is written:

- AC1, AC6 and AC7 are the queue line's *Testable* sentences: the declaration
  names mode 10 and not mode 6, both cases stay attributed to mode 6, and
  mode 6's status records that no rule detects it.
- AC2 and AC3 are the specification half of the move, one per mode. Without
  them `catalogue.rule_declaration_conflicts()` still passes when the edge is
  simply dropped: that check only asks that a declared mode has *some* edge.
- AC4 is what makes `coverage`'s firing on `remove_level` a mode-10
  co-detection rather than mode 6's detection. It is also what Stage 33 D4's
  detector-granular bar checker reads.
- AC5 is the fact behind AC7. Another rule declaring mode 6 would make it
  `implemented` whatever `coverage` does.
- AC8 records mode 6's rung. AC9 and AC10 record mode 10's first rule edge.
- The queue's "both modes' derived status and rung match an independent
  recomputation" is already held for all 16 modes by
  `tests/test_151_stage30_validation.py`'s AC13 and AC18. Those tests
  recompute both values independently and compare them against the committed
  rendering and the matrix row. So it is not restated here.
- The queue's "the ratchet is green" is `tests/test_163_specificity_ratchet.py`'s
  job. No firing moves in this item (A5), so the ratchet must stay green
  unedited.

None of these closes a Stage 33 acceptance criterion. Criterion 3 ("no rule
declares a mode through a detector that reads another mode's signal") is still
open for `mislabel` (item 189) and for the detector-granular bar checker (D4).

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
measured value below was taken on this branch on 2026-09-28 with
`.venv/bin/python`, by a scratch probe that applied Implementation Steps 1–3 in
memory (the declaration and both `ModeSpec`s replaced with
`dataclasses.replace`) and re-ran every derivation. The builder re-measures each
one on the real change.

- **A1 (defensible default: mode 10's edge is `needs-real-data`).** Mode 10 has
  no corpus case. A `synthetic-demonstrable` edge must fire on one of the mode's
  own pipeline cases: `tests/test_145_eight_hypothesised_modes.py::test_ac8_every_synthetic_demonstrable_edge_is_demonstrated`
  enforces it, and so does `test_146`'s AC6 principle for mode 16.
  `remove_level` is mode 6's case, not mode 10's, so it cannot demonstrate
  mode 10. The fixture that could, a skip-relabel case, belongs to no stage
  (roadmap Stage 33, Dependencies). Mode 8's `reference_delta` edge is the
  precedent: a declared edge with no case of its own, at `needs-real-data`.
- **A2 (defensible default: all three detectors move with the rule).** The
  mode-10 edge names `count_shortfall`, `incomplete_span` and `missing_interior`,
  as mode 6's edge did. The queue re-homes the rule, and each detector reads a
  list of labels. The traceability matrix's `detector_to_edge` direction needs
  every declared detector named by an edge or carrying a `mode_less_reason`, and
  moving all three keeps it complete. The two opt-in detectors ship disabled.
  Which mode each would serve on real data is left open.
- **A3 (defensible default: mode 6 stays authored `specified`).** In vision.md's
  lifecycle, `specified` means "definition, discriminator, observability and
  candidate features settled; rules named but not written". That is mode 6
  after this item: its spacing rule is named (`insights.md`, 2026-09-22,
  queue-022 review, the open `gap` entry on mode 6) and not written. `proposed`
  ("no features, rules or corpus yet") would contradict its two corpus cases.
  So mode 6 is the first mode that is not `proposed` and has no declaring rule.
  Several tests used `proposed` as a stand-in for "has no rule" (A7).
- **A4 (forced: mode 10 is re-authored `specified`).** A `proposed` mode that a
  registered rule declares is reported by `failure_modes.specification_conflicts()`
  as `proposed` drift, and `tests/test_146_ninth_mode_and_first_proposed.py`'s
  AC31 asserts that the check returns `()`.
- **A5 (measured: nothing in the corpus moves).** `remove_level` stays
  `failure_mode=6` with `expected_rule_ids=["coverage"]` in
  `tests/corpus/manifest.json`, and its specification `expected_firing` stays
  `("coverage",)`. `remove_level_relabel` stays `()`. So:
  - `catalogue.scan_synth_rule_mode_map()` is unchanged (`coverage -> (6,)`);
  - `("coverage", 6)` becomes a corpus-designated pair that the rule does not
    declare. `catalogue.rule_declaration_conflicts()` accepts it as a recorded
    co-detection (coverage is in `remove_level`'s `expected_firing` and is not
    one of mode 6's intended rules);
  - `specification_conflicts()`, `rule_declaration_conflicts()` and
    `path_classification_conflicts()` stay `()`;
  - conformance stays 18 agreeing cases, 0 disagreeing, and `coverage` stays
    exercised by `remove_level`;
  - `docs/aide/golden_evidence.generated.json` does not move, because no finding
    moves and it records no mode;
  - `docs/aide/corpus_sheet.png` does not move, because the manifest does not.
- **A6 (measured: what the derivations move).**
  - Mode 6: status `validated` → `specified`, rung `synthetic-demonstrable` →
    `None`. Matrix row: `rules []`, `rule_attribution {}`, `read_paths []`.
    `bar_conditions(6)` meets none of conditions 1–5.
  - Mode 10: status `proposed` → `implemented`, rung `None` → `needs-real-data`.
    Matrix row: `rules ["coverage"]`, `rule_attribution {"coverage": "analytic"}`,
    `read_paths` equal to the two level lists. `bar_conditions(10)` meets
    condition 4 only.
  - `mode_to_rule` holes: `{5, 7, 10, 11, 12, 13, 14}` → `{5, 6, 7, 11, 12, 13, 14}`.
    The other five matrix directions stay complete.
  - Catalogue: `relationships.missing_levels[]` and
    `relationships.present_levels[]` carry `failure_modes` `(6,)` → `(6, 10)`.
    The map gives 6, the declaration gives 10, and `mode_evidence` is unchanged.
    No leaf path is added or removed, so
    `tests/corpus/119_pre_119_digests.json` does not move.
  - Counts over 16 modes:
    - derived status: validated 7 → 6, implemented 2 → 3, specified 0 → 1,
      proposed 7 → 6;
    - derived mode rung: synthetic-demonstrable 6 → 5, needs-real-data 2 → 3,
      structurally-unobservable 1, none 7;
    - per-edge rungs over 18 edges (one removed, one added):
      synthetic-demonstrable 6 → 5, needs-real-data 11 → 12,
      structurally-unobservable 1;
    - validated modes reached through a pipeline-detected case: 6 → 5, and
      through a reconstructed record only: 1.
- **A7 (defensible default: the rule-less specified mode is named, not
  inferred).** Several tests hold the invariant "every `specified` mode has a
  rule", and one guard (`test_146`'s
  `test_review_mode_to_rule_holes_are_exactly_the_proposed_modes`) exists to
  fail loudly when a `specified` mode loses its last rule.
  - Each of these tests is reconciled by exempting mode 6 **by name**, with a
    dated item-188 comment citing the maintainer decision of 2026-09-25. It is
    not reconciled by widening the invariant to "any mode with no rule". Any
    other `specified` mode that loses its rule still fails.
  - `traceability._NOTE`, which the guard's docstring cites as excusing only
    `proposed` holes, is revised to name mode 6's hole as a recorded gap.
- **A8 (defensible default: the declaration's evidence is `"analytic"`).** No
  corpus case attributed to mode 10 designates `coverage`, so the evidence tuple
  leads with `"analytic"`, as `bounds` and `reference_delta` do. The matrix
  derives attribution from the specification's corpus cases, never from this
  tag (`tests/test_138_traceability_matrix.py::test_adv_ac20_mistagged_corpus_evidence_changes_no_attribution`),
  so it reads `"analytic"` either way.
- **A9: no human gate, and no environment-gated capability.**

## Implementation Steps

1. **`src/segfacet/heuristics/coverage.py`.**
   - Set `mode_declaration.modes=(10,)`.
   - Replace `evidence` with `("analytic", <sentence>)`. The sentence says what
     the always-active `missing_interior` detector reads (the label gap in
     `relationships.missing_levels[]`), that this is what a skipped label
     leaves, and that the rule cannot see whether the vertebra is present. It
     says that `remove_level` (mode 6) therefore fires it as a recorded
     co-detection, and that no committed case expresses mode 10.
   - Re-point the module docstring's opening paragraph and the class comment
     above `mode_declaration` at mode 10 (skipped level label). Record that item
     188 moved the rule off mode 6.
   - Change nothing else: `consumed_paths`, `detectors` and `evaluate` stay as
     they are.
   - Cite `failure_modes.SPECIFICATION`, never vision.md §6, because
     `tests/test_161_stage31_validation.py::test_criterion2_no_module_attributes_a_numbered_mode_to_section6`
     scans all module prose.
2. **`src/segfacet/failure_modes.py`, `_MODE_6`.**
   - Set `intended_rules=()`. The candidate features, corpus cases, `status`
     (`"specified"`) and discriminator stay.
   - Rewrite `mechanism`. It says that no registered rule decides the mode yet.
     It says that `coverage`'s interior-gap detector fires on `remove_level`'s
     label gap but serves mode 10, so that firing is a recorded co-detection. It
     says that `remove_level_relabel` fires nothing. It says that the mode's own
     label-map signal, a doubled inter-centroid spacing over
     `stage3.spacing_consistency.spacings_mm[]`, is read by no rule, and that
     the rule is decided in a later per-mode queue.
   - The mechanism must name `remove_level` or `remove_level_relabel` as a
     whole word (`test_138`'s AC31 token check). Any catalogue path it names
     must be one that `coverage` consumes, or one that no rule consumes
     (`test_138`'s `test_ac31_named_feature_path_is_consumed_by_one_of_the_modes_declared_rules`,
     through its co-detection widening). In practice that means only
     `relationships.missing_levels[]`, `relationships.present_levels[]` and
     `stage3.spacing_consistency.spacings_mm[]`. Item 187 lost a validation
     round to exactly this check.
   - Rewrite `remove_level`'s `reason`. It still says the case is
     pipeline-detected with `coverage` as the sole rule firing. It now says that
     `coverage` serves mode 10, so the firing is a co-detection that does not
     validate mode 6, and it carries the date it was re-measured.
     `remove_level_relabel`'s `reason` stays.
3. **`src/segfacet/failure_modes.py`, `_MODE_10`.**
   - Set `status="specified"`.
   - Set `intended_rules=(IntendedRule(rule_id="coverage", detector_ids=("count_shortfall", "incomplete_span", "missing_interior"), evidence_rung="needs-real-data"),)`.
   - Rewrite `mechanism`. It names `coverage` as a whole word, because mode 10
     now leaves the `proposed` branch of the AC31 token check and its only live
     token is its rule id. It says that the interior-gap detector fires on the
     label gap in `relationships.missing_levels[]`. It says that the detector
     cannot tell the gap from a missed vertebra, so on `remove_level` (mode 6)
     it is a co-detection. It says that no committed case expresses this mode,
     so the edge is `needs-real-data`: a skip-relabel fixture is not authored.
     It says that the separating signal is an ordinary spacing across the label
     gap. The same path rule as mode 6 applies.
   - Candidate features, corpus cases (none), discriminator and severity stay.
4. **`src/segfacet/failure_modes.py`, prose.**
   - Append an item-188 paragraph to the module docstring's history. The
     2026-09-15 paragraph stays as the record of that revision.
   - Append a dated correction to `derive_status`'s docstring sentence "all ten
     entries that reach the corpus-agreement clause are declared". Mode 6 now
     reaches the clause undeclared and derives its authored `specified`.
5. **`src/segfacet/traceability.py`.**
   - Extend `_NOTE`'s hole sentence: a `specified` entry whose rule is named but
     not yet written also appears as a mode → rule hole, and that hole is a
     recorded gap, not an excused one. Mode 6 is the one such entry since item
     188.
   - Keep the words `complete` and `holes`, and add none of `test_146`'s
     `_UNCONDITIONAL_COMPLETENESS_PHRASES`.
   - Re-point the two comments that cite mode 10 as the edge-less example
     (`build_matrix`'s rung comment and `matrix_to_dict`'s rung comment).
6. **`src/segfacet/heuristics/bounds.py`.** The class comment's "coverage owns
   mode 6" becomes "no shipped rule decides mode 6 since item 188 (coverage
   serves mode 10)". This is a comment edit only.
7. **Regenerate** each of the following twice, with `--json <tmp> --md <tmp>`.
   Byte-compare the two runs, then run the generator once more with no flags to
   write the committed copies:
   - `.venv/bin/python -m segfacet.failure_modes`;
   - `.venv/bin/python -m segfacet.traceability`;
   - `.venv/bin/python -m segfacet.catalogue`.

   The expected diffs:
   - `failure_modes`: modes 6 and 10 (status, edges, rung, mechanism) and
     `remove_level`'s reason;
   - `traceability_matrix`: the note, the mode 6 and 10 rows, `coverage`'s rule
     row, and the `mode_to_rule` holes;
   - `feature_catalogue`: the two level-list entries' `failure_modes`.

   Do **not** regenerate the corpus, `corpus_sheet` or `golden_evidence`. If a
   fresh `python -m segfacet.golden_evidence` into a temp path differs from the
   committed copy, hand back (A5).
8. **Amend the attested count clauses** with `python .aide/scripts/aide.py progress amend`.
   Re-measure every number live first; the values below are A6's. Each
   `--evidence` starts `Item 188 (2026-09-28): coverage re-homed from mode 6
   to mode 10; mode 6 derives specified with no rule, mode 10 implemented at
   needs-real-data. Re-measured live:` and continues with the exact clause:
   - `amend 30 --criterion 1`: `derived status counts over 16 modes: validated 6, implemented 3, specified 1, proposed 6; validated through a pipeline-detected case 5, through a reconstructed record only 1.`
   - `amend 30 --criterion 3`: `derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7; per-edge rung counts over 18 edges: synthetic-demonstrable 5, needs-real-data 12, structurally-unobservable 1.`
   - `amend 20 --criterion 5`: `derived status counts over 16 modes: validated 6, implemented 3, specified 1, proposed 6. derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7.`

   The rung clause goes under Stage 30 criterion 3, not criterion 1.
   `test_151`'s AC35 reads the **last** match in the section, and criterion 3's
   existing 2026-09-20 line sits below criterion 1. Stage 32's criterion-4
   clause is a dated clean-clone measurement that no test re-reads. Stage 33
   D6 re-states it, so it is not amended here.
9. **Reconcile** the tests listed under Testing Strategy, each change with a
   dated item-188 comment.
10. Run `python .aide/scripts/aide.py scope 188` and `python .aide/scripts/aide.py check`.
    Both must report no error.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/coverage.py` — the declaration, evidence and prose re-pointed at mode 10 (step 1).
- `src/segfacet/failure_modes.py` — modes 6 and 10, `remove_level`'s reason, and two docstrings (steps 2–4).
- `src/segfacet/traceability.py` — `_NOTE`'s hole sentence and two comments (step 5).
- `src/segfacet/heuristics/bounds.py` — one comment (step 6).
- `docs/aide/failure_modes.generated.json` — regenerated (step 7).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 7).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated; two entries' `failure_modes` (step 7).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `tests/test_188_coverage_rehomed.py` — **new**: this item's test module.
- `tests/test_136_rule_mode_declarations.py` — `_CORROBORATED["coverage"]` and the co-detection witness.
- `tests/test_138_traceability_matrix.py` — the rule-less-mode set, hole witness, analytic-edge witness and AC31 path check.
- `tests/test_144_failure_mode_specification.py` — AC16's "every specified entry has an edge".
- `tests/test_145_eight_hypothesised_modes.py` — `_PROPOSED_MODE_IDS`, `_EXPECTED_DERIVED_STATUS` and six tests' rule-less branches.
- `tests/test_146_ninth_mode_and_first_proposed.py` — AC31's specified list and the holes-equal-proposed guard.
- `tests/test_147_specification_is_the_record.py` — AC8's edgeless set and AC26's expected statuses.
- `tests/test_148_per_path_mode_attribution.py` — AC12's unreachable set.
- `tests/test_149_conformance_report.py` — `_DEGENERATE_MODES`.
- `tests/test_103_feature_catalogue.py` — one docstring only (`coverage` "declares `(6,)`").
- `tests/test_038_coverage_border_overlap_perturbations.py` — one docstring and one block comment only ("mode 6's detectable form").

**The reconciliation fence.** Every edit to an existing test is a moved literal,
or mode 6 exempted by name from a "specified means it has a rule" branch (A7),
with a dated item-188 comment. No test is retired, skipped, `xfail`-marked or
loosened to "any mode with no rule". `tests/test_151_stage30_validation.py` and
`tests/test_169_stage32_validation.py` are **not** edited: step 8's amendments
make them green. A red test in a file not listed here is a hand-back to
spec-author.

**Asserts against:**

- `tests/corpus/manifest.json` — AC6's attribution must agree with it (`specification_conflicts()`); `remove_level`/`remove_level_relabel` stay `failure_mode` 6 (A5).
- `src/segfacet/synth/coverage_border_overlap.py` — `RemoveLevelPerturbation`'s `Expectation` (mode 6, `{"coverage"}`) is what the manifest carries; it must not move (A5).
- `docs/aide/golden_evidence.generated.json` — no finding moves, so it must not move (A5).
- `tests/test_151_stage30_validation.py` — its AC13/AC18 recompute both modes' status and rung independently, and its AC35 reads step 8's Stage 30 amendments.
- `tests/test_169_stage32_validation.py` — its AC6/AC7 read step 8's Stage 20 amendment.
- `tests/test_163_specificity_ratchet.py` — must stay green unedited (no firing moves).

## Testing Strategy

The test module is `tests/test_188_coverage_rehomed.py`, with one test per AC.
AC5's declared set is computed in the test from `iter_rule_declarations()`,
never from `SPECIFICATION`. AC2 builds its expected `IntendedRule` from the
coverage rule's own declared detector ids, not from a literal tuple.

Named adversarial cases, and no others:

- `declared-set-reads-the-registry`: with a stub rule declaring `modes=(6,)`
  registered in an isolated registry (the snapshot/restore pattern of
  `tests/test_136_rule_mode_declarations.py`'s `isolated_registry`), AC5's
  computation returns `{<the stub's rule_id>}`. It guards AC5 passing because
  its set is read from somewhere that cannot see a declaration, such as mode 6's
  own empty `intended_rules`.

**Existing tests to reconcile.** Four parallel read-only sweeps over every test
module that imports `failure_modes`, `traceability`, `catalogue` or a rule's
`mode_declaration`, or that reads `progress.md`, found these. Their grep covered
`coverage` as a literal, mode 6 and mode 10 pins, `proposed`-id sets,
`specified`-id lists, derived-status maps, edgeless sets, hole witnesses,
analytic-edge witnesses, co-detection witnesses, per-path mode tuples and count
clauses. Each will go red without the edit named:

- `tests/test_136_rule_mode_declarations.py`
  - `_CORROBORATED["coverage"]`: `(6,)` → `(10,)`. It drives
    `test_ac4_corroborated_rule_declares_its_signed_off_modes[coverage-…]`.
  - `test_ac4_corroborated_modes_are_covered_by_the_measured_corpus_map`:
    `expected_co_detections` gains `("coverage", 6)`, because the corpus map
    still designates 6 and the declaration no longer carries it. Update the
    comment block above `_CORROBORATED` and the dated history above the witness.
- `tests/test_138_traceability_matrix.py`
  - `PROPOSED_MODES` stays live-derived and becomes `{5, 7, 11, 12, 13, 14}`.
    Add a dated constant `RULELESS_SPECIFIED_MODES = frozenset({6})` (A7), and
    use `PROPOSED_MODES | RULELESS_SPECIFIED_MODES` wherever the branch means
    "declares no rule".
  - `test_ac10_mode_to_rule_direction_complete_and_every_mode_has_a_rule`:
    - the no-rule branch uses that union;
    - `set(direction["holes"])` equals the union as strings;
    - the witness becomes `{"5", "6", "7", "11", "12", "13", "14"}` for the
      holes, and `proposed_mode_ids` loses `"10"`.
  - `test_ac12_mode_rung_is_member_of_closed_vocabulary_or_none_when_proposed[6]`:
    `None` is legal for the union.
  - `test_ac19_every_mode_to_rule_edge_is_attributed_from_the_specification`:
    - the literal `PROPOSED_MODES == {5, 7, 10, 11, 12, 13, 14}` becomes
      `{5, 7, 11, 12, 13, 14}`;
    - the `rules == []`, `rule_attribution == {}` and `read_paths == []` loop
      and the attribution loop's skip both use the union.
  - `test_ac20_analytic_edges_equal_edges_the_specification_never_designates_corpus`:
    - `witness` gains `(10, "coverage")`;
    - `mixed == {"bounds"}` stays;
    - update the dated comments that say coverage is a corpus edge of mode 6.
  - `test_ac24_mode_read_paths_and_anchor_paths_are_two_separate_fields[6]`:
    the no-rule branch uses the union.
  - `test_ac31_named_feature_path_is_consumed_by_one_of_the_modes_declared_rules`:
    - `assert declared_rules, mode` is not applied to a mode in
      `RULELESS_SPECIFIED_MODES`;
    - that mode's named paths are still checked against its co-detecting rules
      (`permitted_rules` = the co-detecting set), not skipped;
    - the proposed-mode skip is unchanged.
  - Stale prose to update in the same file: the module docstring on
    `PROPOSED_MODES`, `_proposed_mode_ids`' docstring, the `present_levels[]`
    fixture docstring ("now mode 6's"), `test_ac5`'s two "mode 10, the first
    proposed" comments, `test_ac10`'s and `test_ac12`'s docstrings,
    `test_ac17`'s "mislabel's and coverage's edges", and `test_ac19`'s and
    `test_ac20`'s dated comments. Also the AC24 banner, which calls mode 10 "the
    one mode with zero declaring rules", and `test_ac31`'s "seven proposed
    modes".
- `tests/test_144_failure_mode_specification.py`
  - `test_ac16_proposed_entries_are_the_empty_ones`: `assert mode.intended_rules`
    over `specified` entries exempts mode 6 by name. The docstring is updated
    to match.
  - Stale docstring only: `test_ac9_multi_mode_declaration_implements_every_mode_it_lists`
    cites `coverage` `(6, 10)`.
- `tests/test_145_eight_hypothesised_modes.py`
  - Constants:
    - `_PROPOSED_MODE_IDS` → `(5, 7, 11, 12, 13, 14)`;
    - add `_RULELESS_SPECIFIED_MODE_IDS = (6,)`, dated;
    - `_EXPECTED_DERIVED_STATUS`: `6: "specified"`, `10: "implemented"`.
  - `test_ac2_proposed_entries_carry_no_edges_and_no_cases`: the
    non-proposed loop's `assert mode.intended_rules` exempts the rule-less
    specified ids, and asserts `== ()` for them instead.
  - `test_ac5_edge_set_equals_live_registry_declared_set[6]`: `declared ==
    set()` for the rule-less specified ids. `[10]` goes green with the
    constant.
  - `test_ac6_mode_rung_is_the_strongest_of_its_own_edges[6]`: the edgeless
    branch accepts the rule-less specified ids.
  - `test_ac13_derived_status_is_the_signed_off_ladder`: goes green with the
    constant.
  - `test_ac21_sequence_mode_severity_leads_its_rules`:
    - mode 10's block becomes `status == "specified"`;
    - its edge rule ids become `{"coverage"}`;
    - `corpus_cases == ()` stays;
    - `_live_declared_rule_ids(10) == {"coverage"}`;
    - `failing == [9, 10]` stays;
    - the docstring is updated.
  - `test_ac22_implemented_derives_on_registered_rule_containment[6]`: the
    expected value is the authored `"specified"` for the rule-less specified
    ids. `[10]` goes green with the constant.
  - `test_adv_every_specified_mode_is_declared_and_no_proposed_one_is`: the
    rule-less specified ids are asserted **not** declared.
  - Stale docstrings to update: the module docstring, the constants' comments,
    and the docstrings of `test_ac2_every_field_populated`,
    `test_ac13_every_expected_firing_…`, `test_ac13_derived_status_…`,
    `test_ac13_co_detection_alone_…` and `test_ac20_detector_…`.
- `tests/test_146_ninth_mode_and_first_proposed.py`
  - `test_ac31_specified_entry_deriving_further_is_not_reported`:
    - `specified_ids == [1, 2, 3, 4, 6, 8, 9, 10, 15, 16]`;
    - the "derives further" loop exempts mode 6 by name, and asserts
      `derive_status(mode) == "specified"` for it instead;
    - `specification_conflicts() == ()` stays.
  - `test_review_mode_to_rule_holes_are_exactly_the_proposed_modes`: the holes
    equal the proposed ids plus exactly `[6]`, named with a dated comment (A7).
    The guard stays loud for any other `specified` mode. The docstring is
    updated to cite the revised `_NOTE`.
  - Stale comments to update: the comment that says mode 6 derives
    "implemented", and the comment that says every entry reaching the
    corpus-agreement clause is declared.
- `tests/test_147_specification_is_the_record.py`
  - `test_ac8_absent_rung_renders_explicitly_for_every_edgeless_mode`: the
    edgeless set becomes `{5, 6, 7, 11, 12, 13, 14}`.
  - `_EXPECTED_DERIVED_STATUS` (drives
    `test_ac26_every_corpus_case_agrees_and_status_derives_correctly`):
    `6: "specified"`, `10: "implemented"`, with the inline comments
    re-worded.
  - Update the module docstring's AC8 line and the AC8 banner.
- `tests/test_148_per_path_mode_attribution.py`
  - `test_ac12_every_declared_mode_keeps_a_signal_path`: `unreachable ==
    {5, 7, 11, 12, 13, 14}`. Mode 6 keeps its `MODE_ANCHOR_PATHS` entry, so it
    does **not** join the set. The following `paths_by_mode` assertion then
    passes: mode 6 reaches both level lists through its anchor and the corpus
    map, and mode 10 reaches them through the declaration.
  - Update the docstring.
- `tests/test_149_conformance_report.py`
  - `_DEGENERATE_MODES` → `(5, 6, 7, 11, 12, 13, 14)`. It drives
    `test_ac7_degenerate_row_renders_null_rung_and_empty_edges_without_raising`
    and `test_ac7_committed_markdown_renders_degenerate_rung_as_explicit_none`.
    Mode 6 now has a null rung, no edges and no rules. Mode 10 has none of
    these.
  - Update its comment, the module docstring's "seven proposed modes", and
    `test_ac5`'s "one of the seven proposed entries".
- `tests/test_103_feature_catalogue.py`: `test_ac13_rule_mode_map_effect_on_failure_modes`'s
  docstring says `coverage` "declares `(6,)`". This is a docstring-only edit.
  `_RULE_MODE_MAP["coverage"] == (6,)` stays correct, because the corpus scan is
  unchanged.
- `tests/test_038_coverage_border_overlap_perturbations.py`: `test_ac6_remove_level_expectation_well_formed_and_pipeline_agrees`'s
  docstring and the block comment above it call `remove_level` "mode 6's
  detectable form". Re-word them to say `coverage` co-detects it. This is a
  prose-only edit, and every assertion stays.

**Green without an edit** once step 7 regenerates and step 8 amends:

- `tests/test_151_stage30_validation.py`:
  - AC35's three clause tests;
  - AC13 and AC18, which recompute status and rung for all 16 modes;
  - AC5, which parametrises over `[6, 8, 9, 16]` and still passes on mode 6's
    anchor alone.
- `tests/test_169_stage32_validation.py`: AC6 and AC7.
- `tests/test_171_literal_negative_controls.py`: its literal clause is a
  deliberately wrong control, compared only on the mode total.
- `tests/test_164_detector_ids.py`, `tests/test_179_status_report_corpus.py`
  and `tests/test_103_feature_catalogue.py`'s AC19: these compare against the
  committed artifacts.
- `tests/test_156_conformance_seams.py`, `tests/test_162_corpus_exercise_report.py`
  and `tests/test_163_specificity_ratchet.py`: these are live-derived.
- `tests/test_137_mode_less_rule_disposition.py`: its counts pin modes 1, 2 and
  16 only.
- `tests/test_182_corpus_derived_rule_mode_map.py`: it runs off the unchanged
  manifest.
- Every other module the sweep read pins nothing that moves. Each derives from
  the manifest, whose `failure_mode` keys do not move, or pins firing only.

## Validation

1. Regenerate the three document pairs (step 7), then inspect them:
   - in `docs/aide/failure_modes.generated.md`:
     - mode 6 reads `Status, derived (live): specified` and a rung of `none`,
       with no intended rule;
     - mode 10 reads `implemented` and `needs-real-data`, with one `coverage`
       edge;
   - in `docs/aide/traceability_matrix.generated.md`:
     - the `mode_to_rule` holes are `5, 6, 7, 11, 12, 13, 14`;
     - `coverage`'s row lists mode `10`;
     - the note names mode 6's hole.
2. Replay `remove_level` through the CLI:

   ```
   .venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/remove_level_seg.nii.gz --out <tmp> --no-reference
   ```

   `--no-reference` is needed for the reason `CLAUDE.md` gives: the bundled
   VerSe reference is not calibrated for the synthetic corpus. Check that
   `<tmp>/segfacet_report.json`'s `findings` hold exactly one `coverage` finding
   tagged `Missing interior level(s):`, unchanged by this item.
3. Run `python .aide/scripts/aide.py status` and confirm Stages 20 and 30 show
   step 8's amendments.

No environment profile is needed.

## Dependencies

- Item 186: removed `split_own_label`'s spurious `coverage` firing, so
  `coverage`'s corpus designation is `remove_level` alone (✅).
- Item 187: paid the rule-count pins once (11 rules) and last amended the
  matrix and specification pins this item reconciles (✅).

**Downstream:**

- Item 192 makes `sequence` serve modes 8–11. It may add a second mode-10 edge,
  so AC2 filters by `rule_id`. AC9 and AC10's derived values may move with it,
  and that item lists `tests/test_188_coverage_rehomed.py` under May change if
  they do.
- Stage 33 D4's detector-granular bar checker reads AC4's detector → mode map.
- D6 re-states the detection count that step 8 amends.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** mode 6's own rule. Its label-map signal is a doubled
  inter-centroid spacing over `stage3.spacing_consistency.spacings_mm[]`, which
  would also detect `remove_level_relabel`. The rule is left to a later
  per-mode queue by the roadmap's Stage 33 scope decisions (`insights.md`,
  2026-09-22, queue-022 review, the open `gap` entry on mode 6). Until then
  mode 6 is the one `specified` mode that is a mode → rule hole (A7).
- **Left open:** a mode-10 corpus fixture, a skip-relabel case that renumbers
  the labels caudal to a level without deleting a vertebra. It would move
  mode 10's edge to `synthetic-demonstrable`. The roadmap assigns it to no
  stage.
- **Left open:** which mode `coverage`'s two opt-in detectors (`count_shortfall`,
  `incomplete_span`) serve on real data. A count shortfall can also be a missed
  vertebra. They moved with the rule (A2), and both ship disabled at
  `needs-real-data`.
