<!-- aide-template: item 2 -->
# Item 171 — Literal negative controls rebuilt from live values

> **Created:** 2026-09-23 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-023.md`](../queue/queue-023.md) · Item 171
> **Objectives:** G7
> **Suggested branch:** `aide/171-literal-negative-controls-rebuilt-from`

---

## Description

Roadmap Stage 33 D0, second bullet. The `defect` entry in `insights.md`
dated 2026-09-20 (item 167) records the problem. A negative control builds a
"wrong" input and asserts that a check rejects it. When that wrong input is a
literal, and whether it is wrong depends on a value derived from live state,
the control stops being a control once live state moves onto the literal. Its
verdict then depends on that coincidence instead of on the check it
exercises. Item 167 hit this in validation round 1:
`test_151::test_adv_ac35_status_counts_parser_rejects_off_by_one` compared
the literal `validated 7` with a live count that had become 7. Item 167
rebuilt that test from the live counts. Its sibling
`test_adv_ac35_status_counts_parser_rejects_wrong_n` (the literal `15 modes`
against a live 16) was left as it was, and nobody had grepped `tests/` for
the rest of the class.

Stage 33 moves every corpus value (items 173–177 regenerate the corpus on the
lordotic base), and several of the controls below read those values. This
item runs before those items so that no corpus move can turn one of these
controls into a coincidence.

**The class (A1).** A test is in the class when all three of these hold:

1. It is a negative control. It builds an input meant to be wrong and
   asserts that the input differs from, or is rejected against, a reference
   value.
2. The wrong input is a literal, or is built from one.
3. The reference value is derived from live state (the specification, the
   rule registry, the per-mode metric registry, or the pipeline's measured
   output on a committed corpus case), and a legitimate change could move it
   onto the literal.

A test where the literal is the claim's subject is **not** in the class. In
that case the claim is "live state is not this value", so live state moving
onto the literal makes the claim false, and a red test is correct.

**The sweep (A2), 2026-09-23.** Four greps over `tests/test_*.py`, and every
candidate read in context:

- `assert … != ` (about 200 hits)
- names such as `drifted`, `wrong`, `bad`, `perturbed`, `mutated`,
  `overclaim*`, `stale` and `fake` assigned a literal
- `failure_mode=<int>` and `mode_id=<int>` replacements
- `is False` and `pytest.raises(AssertionError)` in `test_15*` and `test_16*`

**Rebuilt: six hits.** Each is rebuilt in place and keeps its name.

| # | Test | Old literal | Live value it was wrong against | Rebuilt wrong input |
|---|---|---|---|---|
| H1 | `test_151_stage30_validation.py::test_adv_ac35_status_counts_parser_rejects_wrong_n` | `15 modes` (the whole clause is a literal) | `_live_status_counts()[0]`, which is `len(fm.SPECIFICATION)` | a clause whose mode count is `live_n + 1` and whose four status counts are the live ones |
| H2 | `test_041_regression_suite.py::test_ac9_verdict_drift_is_caught` | `expected_verdict = "pass"` | `pipeline_verdict_label(case)` on `sequence_break` | the first `Severity` member's `.label`, in enum order, that differs from the live label |
| H3 | `test_041_regression_suite.py::test_ac10_fired_rule_drift_is_caught` | `expected_rule_ids = ["overlap"]` | the rule ids of `pipeline_findings(case)` on `sequence_break` | `[r]`, where `r` is the lowest-sorted `rule_id` from `segfacet.heuristics.rule.iter_rules()` that is not in the live firing set |
| H4 | `test_138_traceability_matrix.py::test_adv_ac31_measured_findings_claim_overclaiming_a_rule_is_detectable` | the claim `['bounds', 'fragmentation', 'reference_delta']` | the rule ids of `pipeline_findings(case)` on `fragment` | the same mechanism sentence, with the bracketed list rendered from the live firing set plus the lowest-sorted registered `rule_id` outside it |
| H5 | `test_153_eval_harness_rekey.py::test_adv_ac5_wrong_home_is_detected` | `failure_mode=99` | `_derived_home("unanchored_foreground_fraction")` | the lowest `fm.SPECIFICATION` id that differs from the live derived home |
| H6 | `test_154_ladder_remeasurement.py::test_adv_ac14_rehoming_a_metric_changes_the_derived_tuple` | re-homing `"rogue_island_count"` to mode 1 | that metric's live `failure_mode` (it must not already be 1), and `sl.MODE_LADDER_DISPOSITIONS[1].ladders` | re-homing to mode 1 the designated metric of the first ladder in `sl.SEVERITY_LADDERS` order whose live home is not 1 |

In H2, H3 and H4, the literal wrong input sat behind a literal precondition
that pinned the corpus value it was wrong against:

- H2: `drifted["expected_verdict"] == "flagged-for-review"`
- H3: `case["expected_rule_ids"] == ["sequence"]`
- H4: `actual_rule_ids == {"fragmentation"}`

Each of those preconditions is removed with its literal (A3). The structural
preconditions stay: `case["detection"] == "pipeline"` in H2, H3 and H4.
Each rebuilt control also asserts, before it runs the check, that its wrong
input differs from the live value. That assertion is the "check the planted
defect is present" step (§6).

**Recorded: in the class, but cannot coincide.**

- `test_041::test_ac11_offending_label_drift_is_caught`,
  `expected_labels = [999]`. A finding's labels are label-map values. The
  label convention (`labels.DEFAULT_LABEL_MAP`, which is TPTBox's) is an
  external, fixed numbering whose keys run from 1 to 33, and every corpus
  operator emits labels from it. Only a change to the label convention
  itself could put 999 in a finding.
- `test_155_corpus_case_kind.py::_ac14_condition_probe`,
  `expected_rule_ids = ["border"]` on the clean control. This input is wrong
  because the clean control fires nothing. That is a stage-level contract
  (roadmap Stage 33 D1, "the clean control fires nothing"), and the
  specificity ratchet (item 163) and `test_041` AC3 pin it directly. So it is
  an invariant, not a coincidence.
- `test_100_severity_ladder.py::test_adv_assignment_outside_valid_mode_range_raises`,
  `"displace": 99`. The mapping's keys are metric names (`str`), so the
  integer 99 cannot equal any of them.
- Sentinel names built to be impossible: `__no_such_rule__`,
  `not_a_real_technique`, `quantum_superposition`,
  `does_not_exist_at_all.nii.gz`, `synthetic_unspecified_case` and
  `candidates.does_not_exist.max_mm`.

**Out of the class: the literal is the claim's subject.** In these tests a
red result on drift is the correct outcome:

- `test_123::test_ac13_default_is_no_longer_fifteen`
- `test_135`'s `_MIN_LEVELS_FOR_HELD_OUT != 4`
- `test_102::test_ac6_default_flag_run_does_not_equal_pre_098_snapshot`
- `test_150::test_adv_ac2_hand_edited_status_cells_are_not_what_aide_gate_writes`
- `test_128`'s one-byte-mutation digest check, where the wrong input is
  derived from live bytes and is not a literal

**Not in scope:**

- Positive assertions that pin a corpus value as a literal. Examples are
  `test_151` AC11's `touches_anterior is True` on `crop_at_border` and
  `test_149`'s `mode1["status"] == "validated"`. Those are the "reconciliation
  risk" that roadmap Stage 33 D2 gives to each corpus item's own sweep.
- Any production code. Nothing under `src/segfacet/` changes.

## Acceptance Criteria

No AC here closes a Stage 33 acceptance criterion. D0 has no acceptance line
of its own.

Each AC below is the queue's testable clause, applied to one hit: the rebuilt
control still rejects its perturbed input when the live value is
monkeypatched to equal the old literal. "Passes" means the function returns
without raising (A5). A4 lists the seam each AC patches.

- [ ] **AC1: H1 survives a mode count of 15.** With the loaded `test_151`
  module's `_live_status_counts` monkeypatched to return `(15, <the live
  status counts>)`,
  `test_adv_ac35_status_counts_parser_rejects_wrong_n()` passes. *Why:* this
  is the known instance the queue names, and it is how `test_151` stays a
  control if the specification's mode count ever changes.
- [ ] **AC2: H2 survives a live verdict of `"pass"`.** With
  `pipeline_verdict_label` monkeypatched to return `"pass"`, both on the
  loaded `test_041` module and on `segfacet.synth.regression`,
  `test_ac9_verdict_drift_is_caught()` passes. *Why:* items 173–177
  regenerate `sequence_break`, and its verdict is exactly the value this
  control's wrong input used to depend on.
- [ ] **AC3: H3 survives a live firing set of `{"overlap"}`.** With
  `pipeline_findings` monkeypatched to return one finding whose `rule_id` is
  `"overlap"` and whose `labels` is `(28,)`, both on the loaded `test_041`
  module and on `segfacet.synth.regression`,
  `test_ac10_fired_rule_drift_is_caught()` passes. *Why:* this is the same
  case with the same exposure to the corpus regeneration as AC2, read here
  through the firing set.
- [ ] **AC4: H4 survives a live firing set equal to the old claim.** With
  `segfacet.synth.regression.pipeline_findings` monkeypatched to return one
  finding for each of `bounds`, `fragmentation` and `reference_delta`,
  `test_adv_ac31_measured_findings_claim_overclaiming_a_rule_is_detectable(monkeypatch)`
  passes. *Why:* item 173 regenerates `fragment` on the new base, and the
  queue records that its firing may change.
- [ ] **AC5: H5 survives a derived home of 99.** With the loaded `test_153`
  module's `_derived_home` monkeypatched to return `99` for every metric,
  `test_adv_ac5_wrong_home_is_detected()` passes. *Why:* the specification's
  mode-id domain grows. It went from 8 modes to 16, and Stage 33 D3 adds a
  condition. So a numeric literal chosen as "not a home" is a guess about
  the future.
- [ ] **AC6: H6 survives `rogue_island_count` already living in mode 1.**
  With `segfacet.eval.per_mode.PER_MODE_METRIC_SPECS` monkeypatched so that
  `rogue_island_count`'s `failure_mode` is 1, and
  `sl.MODE_LADDER_DISPOSITIONS` monkeypatched so that entry 1's `ladders` is
  the tuple recomputed from those patched specs the way
  `severity_ladder.py` computes it at import,
  `test_adv_ac14_rehoming_a_metric_changes_the_derived_tuple(monkeypatch, sl)`
  passes. *Why:* Stage 33 D3 re-homes ladders and metrics, and this control
  is non-vacuous only while its metric's home is not 1.

## Assumptions

- **A1: the class, and how to tell a hit from a subject.** The queue defines
  the class as "a 'must differ / must reject' assertion whose wrong input is
  a literal compared against a live-derived value". This spec adds one test
  to that definition: is the literal a stand-in for "some wrong value", or is
  it the value the claim is about? Only a stand-in is a hit. A subject
  literal going red on drift is the claim working as intended. This is the
  most defensible reading of "stops being a control": only a stand-in can
  stop being one.
- **A2: the sweep is the one in the Description, as of 2026-09-23.** The
  item's record of the sweep is this spec. The Description's three lists are
  that record, as the queue's "recorded with why it cannot drift" asks. The
  test-writer does not re-run the sweep. A hit found later is a new
  `insights.md` line, not a change to this item.
- **A3: removing the literal preconditions in H2–H4 keeps the controls'
  meaning.** Each of those preconditions pinned the corpus value that the
  literal was wrong against. Under a patch where live state equals the old
  literal, each one would fail first. It is also itself a literal
  corpus-value pin that items 173–177 would have to reconcile. The rebuilt
  control's "wrong input differs from live" assertion takes its place as the
  non-vacuity check. What each control asserts about the check under test
  (`verify_case` returns `False`, `designated_rule_fired` returns `False`,
  and the parsed claim differs from the measured set) is unchanged.
- **A4: "the live value, monkeypatched" means the names the control and its
  checked predicate read it through.** For each hit:
  - H1: the loaded module's `_live_status_counts`.
  - H2 and H3: the name that `test_041` imported, and the attribute on
    `segfacet.synth.regression` that `verify_case` and
    `designated_findings` call.
  - H4: `segfacet.synth.regression.pipeline_findings`. The test imports it
    inside its own body, so patching the module attribute is enough.
  - H5: the loaded module's `_derived_home`.
  - H6: both `PER_MODE_METRIC_SPECS` and `MODE_LADDER_DISPOSITIONS`.
    `MODE_LADDER_DISPOSITIONS[1]` is computed from the specs at import, so
    patching the specs alone would leave the table showing the old home.
    That inconsistent state would let the old literal form pass as well.

  A fake finding is a `types.SimpleNamespace` with `rule_id` and `labels`,
  the only two attributes the patched paths read (`designated_findings`,
  `offending_labels_match`, and the rule-id set comprehensions).
- **A5: "still rejects its perturbed input" means the rebuilt test function
  returns without raising.** Every hit asserts its rejection with a plain
  `assert`. So under the patch, returning normally is the control still
  holding, and an `AssertionError` is the coincidence this item removes.

## Implementation Steps

This item changes nothing under `source_dir`. Every edit is under
`tests_dir`, so all of it is the **test-writer's** work. `builder.md` forbids
the builder to touch tests. The builder's step is to confirm that no
`src/segfacet/` change is needed, and to record that in Decisions.

1. **H1, `tests/test_151_stage30_validation.py`.** Build the clause in
   `test_adv_ac35_status_counts_parser_rejects_wrong_n` from
   `_live_status_counts()`, using the mode count `live_n + 1` and the four
   live status counts. Follow the f-string shape that
   `test_adv_ac35_status_counts_parser_rejects_off_by_one` already uses,
   directly above it. Keep `assert n != live_n`.
2. **H2 and H3, `tests/test_041_regression_suite.py`.**
   - AC9: derive the wrong verdict from `pipeline_verdict_label(case)` and
     `segfacet.verdict.Severity`'s member labels. Assert that it differs
     from the live label, then keep `verify_case(drifted) is False`.
   - AC10: derive the wrong rule id from `pipeline_findings(case)` and
     `segfacet.heuristics.rule.iter_rules()`. Assert that it is not in the
     live firing set, then keep `designated_rule_fired(drifted) is False`.
   - Drop the two literal preconditions A3 names, and keep
     `case["detection"] == "pipeline"`.

   Import `Severity` and `iter_rules` at module level, next to the existing
   `segfacet` imports.
3. **H4, `tests/test_138_traceability_matrix.py`.** In the adversarial AC31
   test, take the live set from `pipeline_findings(case)`. Choose the extra
   rule the way H3 does, then render the bracketed list inside the existing
   mechanism sentence from `live | {extra}`. Use the same `"%s" % ", ".join(sorted(repr(...)))`
   rendering as the liveness half of AC31 above it. Assert that
   `_parse_measured_findings_claim` returns `live | {extra}` and that this
   differs from `live`. Drop `actual_rule_ids == {"fragmentation"}`. Update
   the docstring: the test now reproduces the **shape** of the pre-fix
   mode-2 defect (a claim naming one rule the case does not fire), not its
   literal rule list.
4. **H5, `tests/test_153_eval_harness_rekey.py`.** Replace `99` with
   `min(i for i in fm.SPECIFICATION if i != live)`, where
   `live = _derived_home("unanchored_foreground_fraction")`.
5. **H6, `tests/test_154_ladder_remeasurement.py`.** Choose the metric as
   `sl.SEVERITY_LADDERS[op].designated_metric` for the first `op` in
   `sl.SEVERITY_LADDERS` whose metric's live
   `per_mode.PER_MODE_METRIC_SPECS[...].failure_mode` is not 1. Assert that
   one exists, then re-home it to 1 in the patched copy, as the test does
   today. The comparison against `sl.MODE_LADDER_DISPOSITIONS[1].ladders`
   stays.
6. **Leave one comment at each rebuilt site** naming this item and the
   2026-09-20 insight. The comment that item 167 left on `..._off_by_one` is
   the model.

## Authorised paths

**May change:**

- `tests/test_171_literal_negative_controls.py` — this item's own test module
- `tests/test_151_stage30_validation.py` — H1
- `tests/test_041_regression_suite.py` — H2 and H3
- `tests/test_138_traceability_matrix.py` — H4
- `tests/test_153_eval_harness_rekey.py` — H5
- `tests/test_154_ladder_remeasurement.py` — H6

**Asserts against:**

None. `test_171` calls the six rebuilt functions under monkeypatches, and
their modules are all under **May change** above. What each rebuilt control
compares against is live state, read at call time, not a committed file.

## Testing Strategy

The module is `tests/test_171_literal_negative_controls.py`. It has one test
per AC and the one adversarial case below, and no others.

It loads the five target modules by path, under module names unique to this
file, using the loader `test_170` has (`_load_module_from_path`, which
follows `test_159`), so that pytest does not collect them twice. Patches use
the test's own `monkeypatch`.

Before calling its target, each AC test asserts that the patch took. The seam
must return the old literal:

- AC1: `_live_status_counts()[0] == 15`
- AC2: the patched label is `"pass"`
- AC3 and AC4: the patched firing set equals the old literal set
- AC5: `_derived_home(...) == 99`
- AC6: `MODE_LADDER_DISPOSITIONS[1].ladders` includes every ladder that
  designates `rogue_island_count`

That is §6's "the planted defect is really present". Without it, a patch that
missed its seam would leave the AC passing on unpatched live state.

Adversarial case:

- **`old-literal-form-fails-under-patch`**, parametrised over H1–H6. Under
  each AC's own patch, an inline copy of that hit's **pre-item** body raises
  `AssertionError`. For each hit, the copy keeps the wrong input and the
  final rejection assertion, and drops the literal preconditions A3 removes,
  so that the rejection is the assertion that fires. It guards against a
  patch that does not reach the seam the control reads. Such a patch lets
  the old and rebuilt forms both pass, so AC1–AC6 would certify nothing.
  H6's naive patch (the specs alone, per A4) is the known instance.

**Existing tests to reconcile.** No production default or behaviour changes,
so no other test's assumption goes stale. The reconciliation is the six
rebuilt functions themselves (Implementation Steps 1–5). The six names are
unchanged. A grep on 2026-09-23 found no reference to any of them outside
its own module, apart from the provenance lines in `insights.md`, item
167's spec and queue-023, which cite the H1 name as history.

## Validation

1. From the item branch, run
   `.venv/bin/python -m pytest tests/test_171_literal_negative_controls.py tests/test_041_regression_suite.py tests/test_138_traceability_matrix.py tests/test_151_stage30_validation.py tests/test_153_eval_harness_rekey.py tests/test_154_ladder_remeasurement.py -n auto`.
   It must be green, with no new skip. The six rebuilt controls must pass on
   unpatched live state as well as under AC1–AC6's patches.
2. `python .aide/scripts/aide.py check` must report no error.

## Dependencies

None. Item 170 changed none of the five target modules.

**Downstream:** items 173–177 regenerate the corpus. H2, H3 and H4 read
`sequence_break`'s and `fragment`'s measured output live, and after this
item none of the three carries a literal copy of those values for those
items to reconcile.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** a standing check for the class, such as an AST lint in the
  suite or in `aide check` that flags a literal-built wrong input compared
  against a live-derived value. The queue asks for one sweep, not a
  guard. Telling a stand-in literal from a subject literal (A1) is a
  judgement a shape check cannot make reliably.
- **Left open:** the positive literal corpus-value pins named under "Not in
  scope". Each corpus item's reconciliation sweep owns them (roadmap
  Stage 33 D2).
