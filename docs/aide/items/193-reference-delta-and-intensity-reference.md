<!-- aide-template: item 2 -->
# Item 193 — `reference_delta` and `intensity_reference_delta` claim no mode as their own

> **Created:** 2026-09-28 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-025.md`](../queue/queue-025.md) · Item 193
> **Objectives:** G2, G8
> **Suggested branch:** `aide/193-reference-delta-and-intensity-reference`

---

## Description

This item implements roadmap Stage 33 D3's sixth bullet. It closes the `gap`
entry in `docs/aide/insights.md` dated 2026-09-20 (item 164,
`intensity_reference_delta`'s zero-signal claim on mode 16), which was routed
to Stage 33 D3 on 2026-09-22.

**Why.** Both rules threshold a label's deviation from its level's cohort
reference distribution. The roadmap keeps them as general outlier detectors
that are no mode's own detector. Today they claim modes anyway:

- `reference_delta` declares `modes=(1, 2, 3, 4, 8)` on analytic grounds, and
  it is mode 8's only rule.
- `intensity_reference_delta` declares `modes=(16,)`, but none of its eight
  `consumed_paths` entries is classified `signal`. It reads a block that no
  driver realises, so it has no catalogued leaf path of its own. By item 148's
  contract a rule in that state contributes no mode anywhere. Yet it still
  holds a mode-16 edge, and `traceability.bar_conditions(16)` counts its three
  detectors toward condition 4.
- `catalogue.path_classification_conflicts()` cannot see that state. It
  refuses a non-empty `modes` beside an *empty* `consumed_paths`, not beside a
  non-empty set that carries no `signal` path.

**What this item changes.**

- Both rules become **mode-less** (`mode_less_reason`, the state `border` and
  `spline_offset` already use). Every `IntendedRule` edge naming either rule
  leaves `failure_modes.SPECIFICATION`: `reference_delta` from modes 1, 2, 3,
  4 and 8, and `intensity_reference_delta` from mode 16.
- `path_classification_conflicts()` gains one check: a registered rule whose
  declaration has a non-empty `modes` and a non-empty `consumed_paths` with no
  `signal` entry is reported.
- The rule-exercise direction keeps a reason for both rules, which no committed
  case exercises, through a new authored map in `traceability.py` (A5).
- The mechanism sentences and reasons that name either rule as a mode's rule
  are rewritten. The three generated document pairs are regenerated. The
  Stage 30 and Stage 20 count clauses are amended, and the test pins listed
  under Testing Strategy are reconciled.

**Not in scope.**

- No change to either rule's `evaluate`, thresholds, detector ids, findings or
  `default_config.yaml`. No corpus change: neither rule fires on either
  committed corpus, because neither harness attaches a reference.
- `PROXY_RULE_IDS` stays `("bounds", "reference_delta")`, and
  `BAR_CONDITIONS` still quotes the roadmap verbatim (A7).
- Mode 8's own rule, the detector-granular bar checker and
  `rules.generated.md` (Stage 33 D4), and mode-1 attribution (item 194).

## Acceptance Criteria

Terms used below:

- **"The live conflicts"** is `segfacet.catalogue.path_classification_conflicts()`
  on the shipped registry.
- **"The planted declaration"** is
  `dataclasses.replace(live, modes=(16,), evidence=("planted",), mode_less_reason="")`,
  where `live` is the registered `intensity_reference_delta` rule's
  `mode_declaration` after this item. It restores the pre-item mode-16 claim
  over the post-item `consumed_paths`, none of which is `signal`.
- **"The matrix"** is `segfacet.traceability.matrix_to_dict(segfacet.traceability.build_matrix())`.

- [ ] **AC1: `reference_delta` is mode-less.**
  `segfacet.heuristics.rule.declaration_for("reference_delta").mode_less_reason != ""`.
  `RuleModeDeclaration` admits exactly one of its three states, so a non-empty
  reason means no mode and no pending disposition.
- [ ] **AC2: `intensity_reference_delta` is mode-less.**
  `declaration_for("intensity_reference_delta").mode_less_reason != ""`.
- [ ] **AC3: no specification edge names either rule.** The set of `rule_id`s
  over every `IntendedRule` of every `SPECIFICATION` entry, intersected with
  `{"reference_delta", "intensity_reference_delta"}`, is empty.
- [ ] **AC4: neither rule counts toward bar condition 4 for any mode.** For
  every `mode_id` in `SPECIFICATION`, no element of the `subjects` of the
  `BarCondition` with `number == 4` in `traceability.bar_conditions(mode_id)`
  starts with `"reference_delta/"` or `"intensity_reference_delta/"`.
- [ ] **AC5: a mode claim with no signal path is reported.** With the
  registered `intensity_reference_delta` rule's `mode_declaration`
  monkeypatched to the planted declaration,
  `set(path_classification_conflicts()) - set(<the live conflicts>)` holds
  exactly one message, and that message contains `'intensity_reference_delta'`.
- [ ] **AC6: the live registry reports nothing.** The live conflicts `== ()`.
- [ ] **AC7: the rule-exercise direction stays complete.**
  The matrix's `["directions"]["rule_exercise"]["holes"] == []`.
- [ ] **AC8: every authored unexercised-rule reason is the reason the matrix
  reports.** For every `rule_id, reason` in
  `segfacet.traceability.UNEXERCISED_RULE_REASONS`,
  the matrix's `["exercise"]["rules"][rule_id]["reason"] == reason`.

Why each is written:

- AC1–AC3 are the queue line's "resolve the mode-16 claim" and the roadmap's
  "no mode's own detector". AC3 is the specification half. Without it,
  `catalogue.rule_declaration_conflicts()` still passes when an edge is left
  behind on a mode the rule no longer declares, because that check reads the
  declaration → specification direction only.
- AC4 is the queue line's third *Testable* sentence. It fails on the pre-item
  tree for mode 16, whose condition-4 subjects include
  `intensity_reference_delta/distance`, `/out_of_range` and `/robust_z`.
- AC5 and AC6 are the queue line's first two *Testable* sentences. AC5 fails
  on the pre-item code, where the planted declaration equals the live one and
  the check returns `()`. AC6 also fails for a check wired to report every
  declared rule, since all eight declared rules keep modes.
- AC7 protects Stage 20's attested criterion that every registered rule is
  exercised by a case or recorded unexercised with a reason. Without A5 both
  rules become rule-exercise holes, because that reason used to derive from
  their now-removed edges (A6).
- AC8 is written because an authored reason map rots silently. Item 172 was a
  whole item for the same shape on `UNUSED_OPERATOR_REASONS`. The equality
  fails for an entry naming an unregistered rule (no record), an exercised
  rule (reason `""`), or a rule whose derived reason now differs.

None of these closes a Stage 33 acceptance criterion. Criterion 3 still waits
on the detector-granular bar checker (D4).

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`, engine
2.1.0. Every measured value below was taken on this branch on 2026-09-28 with
`.venv/bin/python`, on a scratch copy of the tree (`git archive HEAD`) with
Implementation Steps 1, 2, 4 (the edges only), 5 and 6 applied. The editable
install's finder was removed from `sys.meta_path` so that the copy's `src/`
was the one imported (the CLAUDE.md gotcha). The three generators and
`segfacet.golden_evidence` were run in that copy and diffed against the
committed documents. The builder re-measures each value on the real change.

- **A1 (forced: "no mode's own detector" is a mode-less declaration).** A
  declared mode needs an `IntendedRule` edge in the specification (item 156's
  declaration → specification direction in `rule_declaration_conflicts()`),
  and every edge is one of the mode's own intended rules for
  `failure_modes._demonstrates` and for bar conditions 2 and 4. The
  specification has no proxy-edge kind. So a rule that is no mode's own
  detector declares no mode. `border` and `spline_offset` are the precedent.
- **A2 (forced: `reference_delta`'s three signal paths become `bookkeeping`).**
  `RuleModeDeclaration.__post_init__` refuses a `signal` path on a declaration
  with no `modes`, and `condition-signal` needs a condition the rule records.
  So `reference_delta.{label}.distribution_distance`,
  `reference_delta.{label}.features.physical_volume_mm3.robust_z` and
  `reference_delta.{label}.out_of_range_features[]` are re-classified
  `bookkeeping`, each with a reason naming the item-193 decision. Each
  detector's `signal_paths` becomes `()`.
- **A3 (forced: every detector of both rules carries a `mode_less_reason`).**
  The matrix's `detector_to_edge` direction needs every declared detector
  named by an edge or carrying its own reason, and all six lose their edges.
  `tests/test_164_detector_ids.py`'s AC14 pins that direction's holes exactly.
  The detector ids stay: `test_164`'s collision fixture needs both rules to
  keep declaring `out_of_range`.
- **A4 (defensible default: mode 8 stays authored `specified`).** Mode 8 loses
  its only edge, so it derives `specified` with rung `None`, like mode 6 since
  item 188. Its definition, discriminator and observability were signed off at
  item 150. `proposed` ("no features, rules or corpus yet") would erase that
  sign-off, and re-authoring a signed-off status is the maintainer's call
  (Left open). So mode 8 joins mode 6 as a `specified` mode with no rule. The
  tests that hold "a specified mode has a rule" exempt it **by name**, as item
  188's A7 did for mode 6.
- **A5 (defensible default: an authored reason map for edgeless unexercised
  rules).** `traceability._build_exercise` derives an unexercised rule's reason
  from the strongest rung among the edges naming it. Neither rule has an edge
  after this item, and neither fires on a committed case, so both would become
  `rule_exercise` holes. That breaks Stage 20's attested criterion
  (`progress.md`, Stage 20: "every registered rule is exercised by ≥1 case or
  recorded as unexercised with a reason"). The reason is real: both rules read
  a reference block that no corpus harness attaches. So `traceability.py`
  gains
  `UNEXERCISED_RULE_REASONS: Dict[str, str] = {"intensity_reference_delta": "needs-real-data", "reference_delta": "needs-real-data"}`
  beside `UNUSED_OPERATOR_REASONS`. `_build_exercise` reads it only when no
  edge names the rule, and then sets `reason_modes=()`. The values stay inside
  `EVIDENCE_RUNGS[1:]`, which `tests/test_162_corpus_exercise_report.py`'s AC4
  requires. The module's scope-fence sentence, "the sole authored string is an
  unused operator's reason", gains a dated item-193 correction.
- **A6 (measured: what moves).**
  - Declarations: the mode-less rules go from `{border, spline_offset}` to
    `{border, intensity_reference_delta, reference_delta, spline_offset}`.
    Declared rules go from 10 to 8 of 12 registered. Both rules' matrix rows
    read `declaration_state` `"mode_less"`, `modes []` and `evidence []`.
  - Edges per mode: mode 1 `fragmentation, bounds`; mode 2 `bounds`; mode 3
    `bounds, neighbour_contact`; mode 4 `fragmentation, bounds`; mode 8 none;
    mode 16 `intensity`.
  - Mode 8: status `implemented` → `specified`, rung `needs-real-data` →
    `None`. Its matrix row reads `rules []`, `rule_attribution {}`,
    `read_paths []` and `pipeline_detected false`. Every other mode keeps its
    status and rung.
  - Modes 1–4 lose the three `reference_delta.*` paths from `read_paths`. Mode
    16's `read_paths` stays the two `image_features` paths.
  - `mode_to_rule` holes go from `{5, 6, 7, 12, 13, 14}` to
    `{5, 6, 7, 8, 12, 13, 14}`. `rule_to_mode`, `edge_to_detector`,
    `detector_to_edge` and `operator_exercise` stay complete. `rule_exercise`
    stays complete with A5: both records read `unexercised`, reason
    `needs-real-data`, `reason_modes []`. Without A5 its holes are
    `["intensity_reference_delta", "reference_delta"]`.
  - `bar_conditions`: mode 16's condition-4 subjects lose the three
    `intensity_reference_delta/*` pairs and keep the three `intensity/*`
    pairs, so the condition is still met. No mode's met/unmet vector changes.
  - `specification_conflicts()`, `rule_declaration_conflicts()` and
    `path_classification_conflicts()` stay `()`. Conformance stays 18
    agreeing, 0 disagreeing, conformant.
  - Counts over 16 modes:
    - derived status: validated 6, implemented 4 → 3, specified 1 → 2,
      proposed 5;
    - derived mode rung: synthetic-demonstrable 5, needs-real-data 4 → 3,
      structurally-unobservable 1, none 6 → 7;
    - per-edge rungs over 20 → 14 edges: synthetic-demonstrable 5,
      needs-real-data 14 → 8, structurally-unobservable 1;
    - validated through a pipeline-detected case 5, through a reconstructed
      record only 1 (unchanged).
  - Catalogue (145 entries; no leaf path added or removed; every `status`
    cell unchanged):
    - The three re-classified paths: `failure_modes` `[1, 2, 3, 4, 8]` → `[]`;
      the `mode_roles` pair `["reference_delta", "signal"]` →
      `["reference_delta", "bookkeeping"]`; `mode_evidence`
      `["rule_declaration", "rule_not_read"]` →
      `["rule_mode_less", "rule_bookkeeping", "rule_not_read"]`.
    - Seven more `reference_delta.*` entries gain `"rule_mode_less"` at the
      head of `mode_evidence`: `lower_pct`, `upper_pct`, `{label}.available`,
      `{label}.features.physical_volume_mm3.percentile_rank`,
      `{label}.features.physical_volume_mm3.value`, `{label}.label` and
      `{label}.level_name`.
    - Entries carrying each mode: mode 1 12 → 9, mode 2 7 → 4, mode 3 8 → 5,
      mode 4 12 → 9, mode 8 4 → 1, mode 16 2.
    - `mode_evidence` buckets: `("rule_bookkeeping",)` 13 → 10;
      `("rule_mode_less", "rule_bookkeeping")` 6 → 9;
      `("rule_mode_less", "rule_bookkeeping", "rule_not_read")` 1 → 8;
      `("rule_bookkeeping", "rule_not_read")` 4 → absent;
      `("rule_declaration", "rule_not_read")` 3 → absent. The other buckets
      and `(): 91` do not move.
  - `docs/aide/golden_evidence.generated.json` regenerates byte-identical. No
    manifest, fixture or `docs/aide/corpus_sheet.png` moves.
    `tests/corpus/119_pre_119_digests.json` hashes only the leaf-path set, so
    it does not move.
  - With the planted declaration, the new check adds exactly
    `rule 'intensity_reference_delta': declares failure mode(s) [16] but none of its 8 'consumed_paths' entries is classified 'signal', so it contributes no mode to any path.`
    With the planted declaration's `consumed_paths` also set to `()`, only the
    existing empty-classification message appears, not both.
- **A7 (defensible default: `PROXY_RULE_IDS` and `BAR_CONDITIONS` stay).**
  After this item no edge names `reference_delta`, so its place in
  `PROXY_RULE_IDS` is inert. That tuple exists so that a later edge cannot
  clear the bar silently (item 165, A5). `BAR_CONDITIONS[3]` quotes the
  roadmap's parenthetical verbatim.
- **A8 (defensible default: candidate features stay).**
  `reference_delta.{label}.features.physical_volume_mm3.robust_z` on modes 1,
  2, 3 and 8, and `intensity_reference_delta.per_label[].robust_z` on mode 16,
  are `hypothesised` candidate features. They are inputs someone might use,
  not rule claims, so they stay.
- **A9 (defensible default: mode 8's mechanism names its hypothesised
  candidates, not its anchor).** Mode 8's anchor,
  `stage3.monotonic_consistency.is_monotonic`, is read by no rule. With no
  declared or co-detecting rule, `test_138`'s check (1) fails on any catalogue
  path the mechanism names, anchor included. `test_138`'s token check accepts
  only anchors, cases and rules. No wording passes both, so the token check is
  widened for the rule-less `specified` modes to accept the mode's own
  candidate-feature paths, as `test_147`'s AC9 already does. Check (1) stays
  strict. Mode 8's mechanism names `vertebra_level_classifier_output` and
  `eval.per_mode.mislabelled_volume_fraction`. The draft in Implementation
  Step 4 was checked on the prototype and names no path from check (1)'s
  universe.
- **A10: no human gate, and no environment-gated capability.**

## Implementation Steps

1. **`src/segfacet/heuristics/reference_delta.py`.**
   - Replace `modes=(1, 2, 3, 4, 8)` and `evidence=(...)` with
     `mode_less_reason=(...)`. The sentence says the rule is a general outlier
     detector: it thresholds a label's deviation from its level's cohort
     reference distribution, which is no failure mode's own signal (roadmap
     Stage 33 D3, item 193). It also says the rule still runs and fires as
     before.
   - Re-classify the three `signal` `ConsumedPath`s as `bookkeeping` (A2).
     Each reason says the path is this mode-less rule's own firing value and
     evidences no mode. Keep `consumed_paths` ascending by `path`.
   - Each of the three `RuleDetector`s drops `signal_paths` and gains a
     `mode_less_reason` (A3).
   - Rewrite the module docstring's last paragraph and the class comment above
     `mode_declaration`: the rule declared modes 1, 2, 3, 4 and 8 from item
     137 until item 193, and serves none since. Cite
     `failure_modes.SPECIFICATION`, never vision.md §6.
     `tests/test_161_stage31_validation.py::test_criterion2_no_module_attributes_a_numbered_mode_to_section6`
     rejects `§6 mode N`, `§6's numbered` and `numbered eight` on any
     `src/segfacet/**` line.
   - `evaluate` does not change.
2. **`src/segfacet/heuristics/intensity_reference_delta.py`.** Do the same for
   `modes=(16,)`. Its `consumed_paths` need no re-classification, because none
   is `signal`. Rewrite the module docstring's "Failure mode 16" paragraph and
   the class comment to say item 193 made the rule mode-less.
3. **`src/segfacet/heuristics/rule.py`.** Add one sentence to the `"bookkeeping"`
   bullet of the `PATH_ROLES` comment: a mode-less rule's own firing value is
   classified `bookkeeping`, because a `signal` path needs a mode (item 193).
   No code changes.
4. **`src/segfacet/failure_modes.py`.**
   - Remove the `reference_delta` `IntendedRule` from `_MODE_1`, `_MODE_2`,
     `_MODE_3`, `_MODE_4` and `_MODE_8`, and the `intensity_reference_delta`
     edge from `_MODE_16`. `_MODE_8.intended_rules` becomes `()`, and its
     `status` stays `"specified"` (A4).
   - Rewrite the `mechanism` of modes 1, 2, 3, 4, 8 and 16. None may claim
     that either rule serves the mode, and none may name a `reference_delta.*`
     path. `tests/test_138_traceability_matrix.py::test_ac31_named_feature_path_is_consumed_by_one_of_the_modes_declared_rules`
     fails on any catalogue path that no declared or co-detecting rule of the
     mode consumes. Modes 1, 2, 3, 4 and 16 keep naming their remaining rules.
     Mode 8's mechanism must contain neither `per_label`, `relationships`,
     `overlaps[]` nor any dotted catalogue path (A9). The prototype used this
     draft, which passes:
     > No shipped rule decides this mode itself since item 193 (2026-09-28):
     > reference_delta, which scored a vertebra's geometry against its named
     > level's cohort, is a general outlier detector and serves no mode. The
     > observable forms are the sub-modes': an out-of-order sequence (mode 9),
     > a skipped level label (mode 10) and an unprompted numbering variant
     > (mode 11) each carry their own rules. A wrong identity that keeps the
     > sequence valid needs an external vertebra-level classifier
     > (vertebra_level_classifier_output); against ground truth it is
     > eval.per_mode.mislabelled_volume_fraction. The whole-sequence shift is
     > mode 12. The corpus swap case (relabel_swap) is a mode-9 case.
   - Rewrite the `split` case's `reason` clause "Neither of the two
     needs-real-data intended rules (bounds, reference_delta) fires" so it
     names `bounds` alone. Rewrite the clauses of the three mode-16 case
     reasons that say `intensity_reference_delta`'s edge stays
     `needs-real-data`: the rule has no edge, and it cannot fire because the
     harness attaches no reference. `expected_firing` does not change anywhere.
   - Append a dated item-193 paragraph to the module docstring's history. The
     earlier paragraphs stay as the record.
5. **`src/segfacet/catalogue.py`, `path_classification_conflicts`.** After the
   existing empty-`consumed_paths` check, add one more: when `decl.modes` and
   `decl.consumed_paths` are both non-empty and no entry has
   `role == "signal"`, append
   `f"rule {rule_id!r}: declares failure mode(s) {sorted(decl.modes)!r} but none of its {len(decl.consumed_paths)} 'consumed_paths' entries is classified 'signal', so it contributes no mode to any path."`
   The `decl.consumed_paths` condition keeps an empty classification down to
   its one existing message. Add the new check to the docstring's bullet list.
6. **`src/segfacet/traceability.py`.**
   - Add `UNEXERCISED_RULE_REASONS` below `UNUSED_OPERATOR_REASONS`, with a
     comment (A5), and add it to `__all__`.
   - In `_build_exercise`, before the existing
     `if strongest_rung is None or strongest_rung == evidence_rungs[0]:` add a
     branch: when `strongest_rung is None` and the rule id is in the map, the
     reason is the map's value and `reason_modes` is `()`.
   - Append the dated correction to the module docstring's scope-fence
     sentence (A5), and mention the map where the docstring describes
     `UNUSED_OPERATOR_REASONS`.
   - In `_NOTE`, replace "mode 6 is the one such entry" with a sentence naming
     modes 6 and 8. It says mode 8 has had no rule since item 193 made
     `reference_delta` a general outlier detector. Keep the words `complete`
     and `holes`, and add none of
     `tests/test_146_ninth_mode_and_first_proposed.py`'s
     `_UNCONDITIONAL_COMPLETENESS_PHRASES`.
   - Optionally re-word the two comments that cite mode 6 as the edge-less
     example (the rung comment in `build_matrix` and the one in
     `matrix_to_dict`) to cite modes 6 and 8.
7. **`src/segfacet/synth/component_shape.py`.** In the non-bridged `fuse`
   branch's `detail` prose ("not mode 2's own bounds / reference_delta
   proxies, which need a reference"), drop `/ reference_delta`. This is prose
   only: the string is not written into any manifest.
8. **Regenerate** each of the following twice with `--json <tmp> --md <tmp>`,
   byte-compare the two runs, then run it once more with no flags to write the
   committed copies:
   - `.venv/bin/python -m segfacet.failure_modes`;
   - `.venv/bin/python -m segfacet.traceability`;
   - `.venv/bin/python -m segfacet.catalogue`.

   The expected diffs are A6's. Do **not** regenerate the corpus or
   `corpus_sheet`. If a fresh `.venv/bin/python -m segfacet.golden_evidence`
   into a temp path differs from the committed copy, hand back.
9. **Amend the attested count clauses** with
   `python .aide/scripts/aide.py progress amend`. Re-measure every number live
   first; the values below are A6's. Each `--evidence` string starts
   `Item 193 (2026-09-28): reference_delta and intensity_reference_delta made mode-less; mode 8 derives specified with no rule, mode 16 keeps its intensity edge. Re-measured live:`
   and continues with the exact clause:
   - `amend 30 --criterion 1`: `derived status counts over 16 modes: validated 6, implemented 3, specified 2, proposed 5; validated through a pipeline-detected case 5, through a reconstructed record only 1.`
   - `amend 30 --criterion 3`: `derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7; per-edge rung counts over 14 edges: synthetic-demonstrable 5, needs-real-data 8, structurally-unobservable 1.`
   - `amend 20 --criterion 5`: `derived status counts over 16 modes: validated 6, implemented 3, specified 2, proposed 5. derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7.`

   `test_151`'s AC35 reads the **last** match in the `## Stage 30` section, and
   `test_169`'s AC6 and AC7 read the last match in the `## Stage 20` section.
   The mode-rung clause and the per-edge clause must sit in one string, joined
   by `; `. Item 192's three amendments (2026-09-28) are the shape to mirror.
10. Leave `tests/` alone: the test-writer owns every edit listed under Testing
    Strategy.
11. Run `python .aide/scripts/aide.py scope 193` and
    `python .aide/scripts/aide.py check`. Both must report no error.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/reference_delta.py` — mode-less declaration, re-classified paths, prose (step 1).
- `src/segfacet/heuristics/intensity_reference_delta.py` — mode-less declaration, prose (step 2).
- `src/segfacet/heuristics/rule.py` — one comment sentence (step 3).
- `src/segfacet/failure_modes.py` — six edges, six mechanisms, four case reasons, docstring (step 4).
- `src/segfacet/catalogue.py` — the new check (step 5).
- `src/segfacet/traceability.py` — `UNEXERCISED_RULE_REASONS`, `_build_exercise`, `_NOTE`, docstring (step 6).
- `src/segfacet/synth/component_shape.py` — one prose fragment in a `detail` string (step 7).
- `docs/aide/failure_modes.generated.json` — regenerated (step 8).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 8).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 8).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `tests/test_193_reference_delta_mode_less.py` — **new**: this item's test module.
- `tests/test_137_mode_less_rule_disposition.py` — roll calls, AC5/AC6, the shared-entry test, the movement counts.
- `tests/test_138_traceability_matrix.py` — `RULELESS_SPECIFIED_MODES`, holes, witnesses, AC31 token widening, the anchor-not-consumed re-point.
- `tests/test_144_failure_mode_specification.py` — AC16's mode-6 exemption gains mode 8.
- `tests/test_145_eight_hypothesised_modes.py` — `_RULELESS_SPECIFIED_MODE_IDS`, `_EXPECTED_DERIVED_STATUS`, AC9 targets.
- `tests/test_146_ninth_mode_and_first_proposed.py` — mode-16 declarer sets, AC9/AC10 parametrisation, AC31 and holes exemptions.
- `tests/test_147_specification_is_the_record.py` — AC8's edgeless set, `_EXPECTED_DERIVED_STATUS`.
- `tests/test_148_per_path_mode_attribution.py` — AC11's signal-path control re-pointed.
- `tests/test_149_conformance_report.py` — `_DEGENERATE_MODES`, `_AC9_SPLIT_COLUMN_MODES`, AC10/AC19 pins, two fixtures re-pointed.
- `tests/test_151_stage30_validation.py` — AC12's edge total, AC14's analytic list, AC23's rule set.
- `tests/test_156_conformance_seams.py` — six perturbations re-pointed from `reference_delta` to `bounds`.
- `tests/test_162_corpus_exercise_report.py` — AC5's no-edge branch reads the map; one fixture re-pointed.
- `tests/test_164_detector_ids.py` — one stale comment only.
- `tests/test_166_split_operator.py` — mode 3's edge set.
- `tests/test_136_rule_mode_declarations.py` — one stale comment only.
- `tests/test_103_feature_catalogue.py` — stale docstrings only.

**The reconciliation fence.** Every edit to an existing test is one of these:

- a moved literal;
- mode 8 exempted **by name** beside mode 6 from a "specified means it has a
  rule" branch (A4);
- a perturbation or fixture re-pointed to a subject that still carries the
  premise, with the premise asserted;
- `test_138`'s AC31 token check widened for the rule-less specified modes
  (A9).

Each edit carries a dated item-193 comment. No test is retired, skipped,
`xfail`-marked or loosened to "any mode with no rule". A red test in a file not
listed here is a hand-back to spec-author.

**Asserts against:**

- `tests/corpus/manifest.json` — no case moves; `specification_conflicts()` stays `()` (A6).
- `tests/corpus/intensity/manifest.json` — the mode-16 cases keep `expected_firing` `["intensity"]` (A6).
- `docs/aide/golden_evidence.generated.json` — no finding moves, so it must not move (A6).
- `tests/test_169_stage32_validation.py` — its AC6/AC7 read step 9's Stage 20 amendment.
- `tests/test_163_specificity_ratchet.py` — must stay green unedited (no firing moves).

## Testing Strategy

The test module is `tests/test_193_reference_delta_mode_less.py`, with one
test per AC. AC5 monkeypatches the registered rule instance
(`segfacet.heuristics.rule._RULES["intensity_reference_delta"]`) with
`monkeypatch.setattr(rule, "mode_declaration", ...)`, as `test_156` does, so
the registry is restored after the test. AC4 iterates `SPECIFICATION`'s keys,
never a literal mode list. AC7 and AC8 read the matrix through
`segfacet.traceability`, never the committed JSON.

Named adversarial cases, and no others:

- **empty-classification-reported-once:** with the planted declaration's
  `consumed_paths` also set to `()`, exactly one message in
  `set(path_classification_conflicts()) - set(<the live conflicts>)` contains
  `'intensity_reference_delta'`. It guards the new check double-reporting the
  empty-classification state, which the existing message already covers.

**Existing tests to reconcile.** Four read-only sweeps over `tests/`, plus
`docs/aide/progress.md` and `src/segfacet/`, found these. They covered
rule→mode pairs, `_CORROBORATED`, mode-less and declared sets, declared-mode
tuples, status/rung/edge counts, analytic witnesses, `mixed` sets,
`_DEGENERATE_MODES`, `unreachable`, the mode-evidence bucket table, per-path
mode tuples, catalogue roles and the progress.md clauses. Every new literal
below was measured on the prototype (A6). Each file goes red without the edit
named.

- **`tests/test_137_mode_less_rule_disposition.py`:**
  - `_ANALYTIC_RULES = ("bounds",)` and
    `_ANALYTIC_DECLARED_MODES = {"bounds": (1, 2, 3, 4)}`. This reconciles
    `test_ac2_ac3_…`, `test_ac4_…` and `test_ac9_analytic_modes_are_within_…`.
  - `_DISPOSITIONED` is spelled out as
    `("bounds", "intensity", "intensity_reference_delta", "reference_delta")`,
    so it does not shrink with `_ANALYTIC_RULES`. The comment above it
    records this defect class.
  - `test_ac5_mode_less_rule_declares_no_modes_not_pending`: for `intensity`,
    `modes == (16,)` and `mode_less_reason == ""`. For
    `intensity_reference_delta`, `modes == ()` and `mode_less_reason != ""`.
    `pending_reason == ""` holds for both.
  - `test_ac6_mode_less_reason_is_substantive`: for `intensity_reference_delta`,
    `mode_less_reason != ""`. For `intensity`, the evidence-length branch is
    unchanged.
  - `test_adv_shared_reference_delta_and_intensity_entry_carries_declaration_tag`
    is rewritten under the name
    `test_adv_shared_reference_delta_and_intensity_entry_is_mode_less`. Its
    candidates are the `reference_delta.*` entries consumed by both
    `reference_delta` and `intensity_reference_delta` (seven on the
    prototype). The test asserts the list is non-empty, and for each entry:
    `"rule_mode_less" in mode_evidence`, `"rule_declaration" not in mode_evidence`
    and `failure_modes == ()`.
  - `test_adv_measured_artifact_movement_counts_from_spec`:
    - `mode1_count == 9`, `mode2_count == 4`, `mode16_count == 2`;
    - buckets `("rule_bookkeeping",): 10`,
      `("rule_mode_less", "rule_bookkeeping"): 9` and
      `("rule_mode_less", "rule_bookkeeping", "rule_not_read"): 8`;
    - the keys `("rule_bookkeeping", "rule_not_read")` and
      `("rule_declaration", "rule_not_read")` are removed, because the table
      is exhaustive;
    - `(): 91` and the total of 145 stay;
    - add a dated item-193 paragraph to its docstring.
  - Stale prose: the module docstring (AC2/AC3/AC5 lines), the comments above
    the roll calls, and the AC13 docstring.
- **`tests/test_138_traceability_matrix.py`:**
  - `RULELESS_SPECIFIED_MODES = frozenset({6, 8})`, with a dated item-193
    line.
  - `test_ac10_…`: `no_rule_mode_ids == {"5", "6", "7", "8", "12", "13", "14"}`.
    The proposed set stays `{"5", "7", "12", "13", "14"}`.
  - `test_adv_ac16_rung_unmoved_by_weaker_rules_joining_a_modes_rule_list`:
    mode 4's rules become `{"bounds", "fragmentation"}`. Delete the
    `edge_rungs["reference_delta"]` line.
  - `test_ac19_…`: mode 16's attribution becomes `{"intensity": "corpus"}`.
  - `test_ac20_…`: `witness` becomes
    `{(1, "bounds"), (2, "bounds"), (4, "bounds"), (10, "coverage"), (10, "sequence"), (11, "sequence")}`,
    and `mixed == {"bounds", "sequence"}` stays.
  - `test_ac31_mode_mechanism_names_a_resolvable_live_token`: for a mode in
    `RULELESS_SPECIFIED_MODES`, the candidate tokens also include that mode's
    `SPECIFICATION[mode].candidate_features` paths, matched by substring as
    `test_147`'s AC9 does (A9). Every other branch is unchanged.
  - `test_ac31_named_feature_path_is_consumed_by_one_of_the_modes_declared_rules`
    needs no edit beyond the constant.
  - `_ANCHOR_NOT_CONSUMED_MODE = 9` (re-pointed from 8). In
    `matrix_anchor_not_consumed_bogus_mechanism`, the bogus mechanism reads
    `f"caught by mislabel via {bogus_path}, on purpose, for a test."`.
    `test_adv_ac31_named_anchor_path_not_consumed_by_declared_rule_is_detectable`
    asserts these premises:
    - `declared_rules == {"mislabel", "sequence"}`;
    - `bogus_path == "relationships.is_continuous"`;
    - no rule in the declared rules or the co-detecting rules (every rule id
      in `SPECIFICATION[9].corpus_cases`' `expected_firing`) lists the path in
      its `feature_paths`.

    That last premise replaces the `corpus_cases == ()` premise.
    Measured on the prototype: mode 9's co-detecting set is
    `{"mislabel", "sequence"}`, and neither lists the path. The rest of the
    test is unchanged.
  - `matrix_reference_delta_renarrowed` and
    `test_adv_ac32_renarrowed_reference_delta_declaration_fails_the_matrix_level_check`
    are re-pointed to `bounds`. The fixture sets
    `dataclasses.replace(<bounds' live declaration>, modes=(2, 3, 4))`. The
    test asserts `"bounds"` is in the unpatched matrix's mode-1 rules and not
    in the patched one's. Measured: mode 1's rules go from
    `["bounds", "fragmentation"]` to `["fragmentation"]`. Without the re-point
    the test passes vacuously.
  - Stale prose: the module docstring, the AC16 docstring and the comments
    that call mode 6 the only rule-less specified mode.
- **`tests/test_144_failure_mode_specification.py`:**
  `test_ac16_proposed_entries_are_the_empty_ones` exempts `mode.id in (6, 8)`.
- **`tests/test_145_eight_hypothesised_modes.py`:**
  - `_RULELESS_SPECIFIED_MODE_IDS = (6, 8)`.
  - `_EXPECTED_DERIVED_STATUS[8] = "specified"`.
  - `test_ac9_the_three_analytic_only_edges_are_needs_real_data_and_undemonstrated`:
    `targets = {(1, "bounds"), (2, "bounds"), (4, "bounds")}`. The name's
    "three" stays true.
  - Stale prose: the comments naming the proxy-only modes and
    `bounds / reference_delta`.
- **`tests/test_146_ninth_mode_and_first_proposed.py`:**
  - AC5: `declared == {"intensity"}`.
  - AC6: `checked == 1`.
  - `test_ac9_both_intensity_rules_declare_mode16` and
    `test_ac10_neither_declaration_binds_reserved_corpus_tag` are parametrised
    over `["intensity"]` only.
  - AC31: the exemption becomes `if mode_id in (6, 8):`, and `specified_ids`
    stays `[1, 2, 3, 4, 6, 8, 9, 10, 11, 15, 16]`.
  - AC34: `declarers == {"intensity"}`.
  - `test_review_mode_to_rule_holes_are_exactly_the_proposed_modes`:
    `sorted(proposed_mode_ids + [6, 8])`, and its docstring cites the revised
    `_NOTE`.
- **`tests/test_147_specification_is_the_record.py`:**
  - AC8: the edgeless set becomes `{5, 6, 7, 8, 12, 13, 14}`.
  - `_EXPECTED_DERIVED_STATUS[8] = "specified"`.
  - Update the module docstring's AC8 line.
- **`tests/test_148_per_path_mode_attribution.py`:**
  `test_ac11_three_bookkeeping_paths_empty_signal_path_still_shows` keeps its
  three `reference_delta` bookkeeping-path assertions (`== ()`). Its control is
  re-pointed to `intensity`, a declared rule with both roles:
  `image_features.available` has `failure_modes == ()`, and
  `image_features.per_label.{label}.first_order.median` has
  `failure_modes == (16,)`. Both were measured on the prototype. Its comment
  is re-worded.
- **`tests/test_149_conformance_report.py`:**
  - `_DEGENERATE_MODES = (5, 6, 7, 8, 12, 13, 14)`.
  - `_AC9_SPLIT_COLUMN_MODES` drops the mode-8 tuple and keeps mode 9's.
  - `test_ac10_mode1_read_paths_are_signal_classified_only`: assert
    `"per_label.{label}.geometry.physical_volume_mm3" in mode1["read_paths"]`
    in place of the `robust_z` path. The two `not in` lines stay.
  - `matrix_consumed_path_dropped` builds its replacement with
    `dataclasses.replace(original_decl, consumed_paths=remaining)`. Measured:
    it then reports one completeness message naming `reference_delta` and the
    `robust_z` path.
  - `matrix_reference_delta_renarrowed` narrows `bounds` to
    `modes=(2, 3, 4)`, as in `test_138`.
    `test_adv_ac10_…` asserts `after < before` and
    `"per_label.{label}.geometry.physical_volume_mm3" not in after`.
    `test_adv_ac19_…` asserts `"bounds"` is in `before` and not in `after`.
    Measured: mode 1 loses the four `per_label.{label}.geometry.*` paths and
    the `bounds` attribution.
  - `test_ac19_intensity_mode_attributes_corpus_and_reference_delta_analytic`:
    assert `"intensity_reference_delta" not in mode10["rule_attribution"]` in
    place of the `== "analytic"` line.
- **`tests/test_151_stage30_validation.py`:**
  - AC12: `total_edges == 14`.
  - AC14's recorded analytic list becomes
    `[(1, "bounds"), (2, "bounds"), (4, "bounds")]`.
  - `test_ac23_both_intensity_rules_declare_mode16`: loop over `("intensity",)`
    and assert `{"intensity"} <= rule_ids`.
  - AC35 goes green through step 9's amendments.
- **`tests/test_156_conformance_seams.py`:** every perturbation moves from
  `reference_delta` to `bounds`, with
  `dataclasses.replace(<bounds' live declaration>, modes=...)`. Measured on the
  prototype against an empty baseline:
  - AC2 and the undo test: `modes=(1, 2, 3, 4, 6)` gives exactly one new
    message, naming `bounds` and 6;
  - AC3: `modes=(1, 2, 5)` gives a message naming `bounds` and 5;
  - AC5: `modes=(1, 2, 3, 4, 6)` gives `rule_to_mode.holes == ()`;
  - AC6 and `test_adv_known_and_unknown_…`: `modes=(1, 2, 3, 4, 999)` gives
    exactly one new message, naming `bounds` and 999. Do not use `(999,)` or
    `(1, 999)`: dropping mode 3 adds bounds' "corpus designates failure mode
    3" message, which also contains `999`.

  Update the docstring premises: bounds declares and mirrors modes 1–4.
- **`tests/test_162_corpus_exercise_report.py`:**
  - `test_ac5_unexercised_reason_and_reason_modes_derived_from_specification`:
    when no edge names the rule, expect
    `record["reason"] == traceability.UNEXERCISED_RULE_REASONS.get(rule_id, "")`
    and `record["reason_modes"] == []`. Without this edit A5's map turns it
    red.
  - `matrix_demonstrable_rule_unexercised` plants the premise instead of
    finding it. It patches mode 1 with an added
    `IntendedRule(rule_id="reference_delta", detector_ids=("distance", "out_of_range", "robust_z"), evidence_rung="synthetic-demonstrable")`
    and drops the assertion that mode 1 already carries one. Once an edge
    names the rule, its strongest rung decides and the map is never read, so
    `test_demonstrable_rule_unexercised_is_a_hole`'s assertions stand
    unchanged. Update the fixture docstring.
- **`tests/test_166_split_operator.py`:** `test_mode_3_proxy_edges_unchanged`
  asserts `{"bounds"} <= rule_ids` and
  `rule_ids == {"bounds", "neighbour_contact"}`.
- **Stale prose only:** `tests/test_164_detector_ids.py` (the comment "three
  detectors carry a mode_less_reason", which is nine now: border 2,
  spline_offset 1, and 3 for each of the two rules), `tests/test_136_rule_mode_declarations.py`
  (the comment calling `reference_delta` analytic for mode 2) and
  `tests/test_103_feature_catalogue.py` (the AC15 docstrings).

**Green without an edit** once step 8 regenerates and step 9 amends:

- every fresh-vs-committed artifact test the sweeps listed. The catalogue
  ones are in `test_103`, `test_106`, `test_119`, `test_120`, `test_123`,
  `test_124`, `test_129`–`test_132`, `test_136`, `test_137`'s AC15,
  `test_143`, `test_146`–`test_148`. The matrix ones are in `test_138`,
  `test_143`, `test_146`–`test_149`, `test_157` and `test_164`'s AC9. The
  specification ones are in `test_144`, `test_145`, `test_146`, `test_147`,
  `test_150`, `test_151` and `test_157`. `test_179` is data-driven off the
  same JSON.
- `tests/test_151_stage30_validation.py`'s AC35 and
  `tests/test_169_stage32_validation.py`'s AC6/AC7.
- `tests/test_164_detector_ids.py`'s AC4, AC14 and the collision fixture
  (A2, A3).
- `tests/test_148_per_path_mode_attribution.py`'s AC5/AC7 (`== ()`) and AC12
  (`unreachable` stays `{5, 7, 12, 13, 14}`: mode 8 keeps its anchor).
- `tests/test_165_mode_4_at_the_bar.py`, `tests/test_171_literal_negative_controls.py`,
  `tests/test_182_corpus_derived_rule_mode_map.py` and every behaviour test
  that runs either rule on a record (`test_046`, `test_047`, `test_049`,
  `test_064`, `test_065` and others), since `evaluate` does not change.

## Validation

1. Regenerate the three document pairs (step 8), then inspect them:
   - In `docs/aide/failure_modes.generated.md`, mode 8 reads
     `Status, derived (live): specified` with no intended rule. Modes 1–4
     list no `reference_delta` edge, and mode 16 lists `intensity` alone.
   - In `docs/aide/traceability_matrix.generated.md`:
     - the `mode_to_rule` holes are `12, 13, 14, 5, 6, 7, 8`;
     - both rules' rows read `mode_less`;
     - both rule-exercise rows read `unexercised`, `needs-real-data`,
       `(none)`.
2. Run
   `.venv/bin/python -c "import segfacet.heuristics; from segfacet.catalogue import path_classification_conflicts as c; print(c())"`
   and confirm it prints `()`.
3. Run `python .aide/scripts/aide.py status` and confirm Stages 20 and 30
   show step 9's amendments.

No environment profile is needed.

## Dependencies

- Item 188: made mode 6 the first `specified` mode with no rule, and set the
  test pattern (`RULELESS_SPECIFIED_MODES`) that this item extends to mode 8
  (✅).
- Item 192: last moved the mode 9–11 edges and the count clauses that step 9
  amends (✅).

**Downstream:**

- Item 194 (mode-1 catch-all attribution) and item 195 (`force_overlap`
  removed) regenerate the same three document pairs and re-amend the same
  count clauses.
- Stage 33 D4's detector-granular bar checker and `rules.generated.md` read
  both rules as mode-less.
- D6 re-states the detection count that step 9 amends.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** mode 8's own detection. After this item no rule decides
  mode 8 itself. Its sub-modes 9–11 carry the observable forms, and a wrong
  identity that keeps the sequence valid needs an external vertebra-level
  classifier. Whether mode 8 stays authored `specified` or is re-authored is
  the maintainer's call at the Stage 33 D5 review (A4).
- **Left open:** a dedicated path role for a mode-less rule's firing value.
  `bookkeeping` now carries two meanings: "read, but cannot evidence a mode",
  and "a mode-less rule's own signal" (A2). A separate role would change
  `PATH_ROLES`, which several tests pin, and no consumer needs the
  distinction yet.
- **Left open:** whether the reference-relative intensity judgement returns
  to mode 16 once a reference-backed intensity corpus exists. It would need a
  `signal` path, which it cannot have while no driver realises the
  `intensity_reference_delta` block.
