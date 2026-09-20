<!-- aide-template: item 2 -->
# Item 165 — Mode 4 (islands) brought to the fully-specified bar

> **Created:** 2026-09-20 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 32 — Selected-Mode Refinement: one failure mode fully specified end to end (**D1** — the MVP mode)
> **Queue:** [`../queue/queue-022.md`](../queue/queue-022.md) · Item 165
> **Objectives:** G2 (the MVP mode is demonstrated end to end, and the demonstration is checked rather than asserted), G8 (the bar a refined mode must clear becomes a mechanical check any later mode reuses)
> **Suggested branch:** `aide/165-mode-4-islands-brought-to`

---

## Description

### Where the bar is defined

"The fully-specified bar" is **defined in exactly one place**: `roadmap.md`'s
Stage 32 section, under the heading *"What 'fully specified end to end' means —
the bar a mode must clear to count toward this stage"*. It is a numbered list
of six conditions, quoted verbatim here because every acceptance criterion
below is written against one of them:

1. "Its specification entry is complete and confirmed by the maintainer
   (definition, discriminator, scope, observability, severity, candidate
   features, intended rules, corpus cases)."
2. "At least one committed synthetic fixture expresses the mode, and its
   expected firing set names at least one of the mode's own intended rules and
   agrees with the measured firing."
3. "Every feature path that detector reads is extracted and catalogued."
4. "At least one detector decides the mode and serves no other mode — the
   generic volume proxies (`bounds`, `reference_delta`) do not count."
5. "Its status derives `validated`."
6. "It is signed off by the maintainer, with date and outcome recorded in the
   specification module."

**It is defined nowhere else.** `vision.md` was searched (2026-09-20): it
defines the four-state **lifecycle** — `proposed` / `specified` / `implemented`
/ `validated`, and what `validated` demands — which is the *substance of
condition 5* and nothing more; it never names the bar.
`src/segfacet/failure_modes.py` was searched: it implements the machinery
conditions 2, 4 and 5 rest on (`case_agrees`, `_demonstrates`,
`modes_for_detector`, `derive_status`) but **contains no enumeration of the
bar** and nowhere joins those pieces into the question "is this mode at the
bar". Nothing in `src/` or `tests/` names the bar at all (grepped 2026-09-20
for `fully specified`, `at the bar`, `bar condition` — one unrelated hit in
`catalogue.py`).

So the bar's conditions **are** written down in resolvable form, in
`roadmap.md`; what does not exist is any mechanical check of them. That gap is
this item's deliverable.

### What this item delivers

`segfacet.traceability` gains **`bar_conditions(mode_id)`**: the bar's
conditions 1–5, each recomputed live from the specification, the rule registry
and the feature catalogue, returned as one `BarCondition` record per
condition. Condition 6 is deliberately absent — it is a person's act, item
168's, and no agent can satisfy it (Assumption A2).

The checker is written once and generically, because three siblings in this
same queue consume it: item 167 measures mode 3 against it, item 168's test
that "a mode claimed at the bar whose live state fails any of conditions 1–5
fails the suite" is a call to it, and item 169 replays it from a clean clone.

### Mode 4 is already at the bar — measured, not assumed

The honest finding, measured on this tree on 2026-09-20 through the public
entry points the checker will use:

| Condition | Live state on 2026-09-20 |
| --- | --- |
| 1 — entry complete | all eight roadmap-named fields on `SPECIFICATION[4]` non-empty (3 candidate features, 3 intended rules, 1 corpus case) |
| 2 — a fixture expresses it | `inject_islands`, expected `('fragmentation',)`, measured `('fragmentation',)` via `failure_modes.case_agrees` → agrees; `fragmentation` is one of mode 4's own `intended_rules` |
| 3 — the detector's paths extracted and catalogued | all five `signal_paths` of `fragmentation`'s `islands` detector are catalogue entries with `observed.corpus.covered is True` |
| 4 — a detector serves no other mode | `modes_for_detector('fragmentation', 'islands') == (4,)`; the proxies do not qualify — `bounds/metric_out_of_range` → `(1, 2, 3, 4)`, `reference_delta`'s three detectors → `(1, 2, 3, 4, 8)` |
| 5 — status derives `validated` | `derive_status(SPECIFICATION[4]) == 'validated'` |

So mode 4 needs **no refinement of its entry, its fixture, its features or its
rule**. That is a measurement, not a shortcut: had any condition come back
unmet, this item would have refined mode 4 until it was met, which is what
Stage 32 D1 authorises. What was missing was never the mode — it was that
nothing anywhere checked the claim, so Stage 32's acceptance ("each checked
against live state") could not be honoured.

### How this keeps item 163's ratchet green

`tests/test_163_specificity_ratchet.py` asserts
`set(measured_firing) == set(expected_firing)` for all 15 committed corpus
cases, and forces any change in what fires to be authored in `SPECIFICATION`
in the same change. **This item changes nothing that fires.** It adds no rule,
no detector, no threshold, no operator, no fixture and no feature; it does not
edit `src/segfacet/failure_modes.py` (declared under *Asserts against*), and
it regenerates no committed artifact. `bar_conditions` is a pure reader. The
ratchet therefore stays green with **no `SPECIFICATION` edit at all** — which
is the correct outcome, not an evasion of the ratchet: the ratchet exists to
catch firing changes, and there are none to author.

The one decision that *could* have changed firing —
`island_distance_from_main_body_mm` — is deliberately not taken here
(Assumption A3, and the `Left open` note below).

### What this item is NOT

- **Not the sign-off.** Condition 6 is item 168's human gate. This item raises
  no gate and resolves none.
- **Not an attestation.** No acceptance criterion below carries a
  *(closes Stage N criterion M)* annotation, and therefore **none closes a
  stage criterion**. Stage 32's acceptance criterion 1 requires all **six**
  conditions; condition 6 becomes true only when item 168 records the
  sign-off, and **item 169 performs the attestation from a clean clone with
  its own venv**. Item 163's validator ticked Stage 20 criterion 4 from the
  working checkout on 2026-09-20 and it was retracted the same day; this item
  does not repeat that.
- **Not a change to the specification module.** Mode 4's entry is read and
  pinned, never edited.
- **Not a new generated artifact.** `bar_conditions` is a function, not a
  matrix field: adding it to `TraceabilityMatrix` would change
  `traceability_matrix.generated.json` / `.md` and every test pinning their
  shape, for no consumer that needs it rendered.

## Acceptance Criteria

- [ ] **AC1: The bar is enumerated in code as exactly the five mechanically
      checkable conditions.** `traceability.bar_conditions(4)` returns five
      `BarCondition` records whose `number` fields are `(1, 2, 3, 4, 5)` in
      ascending order, with no record numbered 6 — condition 6 (the
      maintainer's sign-off) is item 168's and is excluded by design.

- [ ] **AC2: Condition 1 holds for mode 4, by live measurement.** The
      `number == 1` record's `met` is `True`, and the test asserts it by
      recomputing the predicate itself from `failure_modes.SPECIFICATION[4]` —
      every one of the eight fields the roadmap names (`definition`,
      `discriminator`, `scope`, `observability`, `severity`,
      `candidate_features`, `intended_rules`, `corpus_cases`) is non-empty —
      and asserting the record agrees with that recomputation.

- [ ] **AC3: Condition 2 holds for mode 4, by live measurement.** The
      `number == 2` record's `met` is `True`, recomputed in the test from
      `failure_modes.case_agrees` over every `SPECIFICATION[4].corpus_cases`
      entry together with the requirement that at least one non-empty
      `expected_firing` intersects `{edge.rule_id for edge in
      SPECIFICATION[4].intended_rules}`; the record's `subjects` equals the
      tuple of case ids that satisfy that intersection.

- [ ] **AC4: Condition 3 holds for mode 4, by live measurement.** The
      `number == 3` record's `met` is `True`, recomputed in the test as: every
      `signal_paths` entry of every detector the `number == 4` record names is
      the `path` of an entry of `catalogue.build_catalogue(strict=True)` whose
      `observed.corpus.covered` is `True`; the record's `subjects` equals the
      sorted tuple of those paths.

- [ ] **AC5: Condition 4 holds for mode 4, by live measurement.** The
      `number == 4` record's `subjects` equals `("fragmentation/islands",)`,
      recomputed in the test as the `"{rule_id}/{detector_id}"` pairs over
      `SPECIFICATION[4].intended_rules` whose `rule_id` is not in
      `traceability.PROXY_RULE_IDS` and for which
      `failure_modes.modes_for_detector(rule_id, detector_id) == (4,)`; `met`
      is `True` exactly when that tuple is non-empty.

- [ ] **AC6: Condition 5 holds for mode 4, by live measurement.** The
      `number == 5` record's `met` is `True` and equals
      `failure_modes.derive_status(failure_modes.SPECIFICATION[4]) ==
      "validated"`, recomputed in the test.

- [ ] **AC7: Every condition record carries the subject its verdict turned
      on.** For each of the five records returned by `bar_conditions(4)`,
      `subjects` is a tuple of non-empty strings and `detail` is a non-empty
      string that is not merely the condition's own restatement — measured as:
      every element of `subjects` occurs in `detail`, so a failure message
      names the live values the verdict was computed from rather than
      re-printing the condition.

## Assumptions  <!-- MANDATORY -->

- **A1 (audit entry, 2026-09-20):** the bar's six conditions are defined only
  in `docs/aide/roadmap.md`'s Stage 32 section and are quoted verbatim in the
  Description above. `vision.md` contributes condition 5's lifecycle ladder
  and nothing else; `src/segfacet/failure_modes.py` implements the machinery
  conditions 2/4/5 rest on but enumerates no bar. Searched 2026-09-20 across
  `src/`, `tests/` and `docs/aide/` for `fully specified`, `at the bar` and
  `bar condition`.

- **A2 (clarify = `assume`):** condition 1's second half — "and confirmed by
  the maintainer" — is read as **subsumed by condition 6**, the dated sign-off
  recorded in the specification module. A recorded sign-off *is* the
  confirmation, and it is the one part of the bar an agent cannot perform. So
  `bar_conditions` computes condition 1 over the completeness half alone and
  its `detail` says so. Item 168 owns the confirmation. The alternative —
  computing condition 1 as permanently unmet until a sign-off exists — would
  make conditions 1 and 6 the same check under two numbers.

- **A3 (clarify = `assume`, the queue line's explicit choice):**
  `island_distance_from_main_body_mm` **stays a `hypothesised` candidate
  path** and is not extracted, catalogued, or read by any detector in this
  item. Reasons: the `prototype` posture writes acceptance criteria for the
  deliverable only; **no bar condition needs it** — condition 3 quantifies
  over the paths the *deciding detector reads*, and the `islands` detector
  reads five paths, all catalogued and observed; and the definition's own
  wording is that distance *grades* the finding rather than bounds the mode,
  which the bar does not ask for. Building it would change `fragmentation`'s
  findings, require a near-island and a far-island fixture, a new
  `CandidateFeature` role, a `feature_docs.MODE_ANCHOR_PATHS[4]` extension
  (pinned by `tests/test_147_specification_is_the_record.py`) and a
  `SPECIFICATION` edit to keep item 163's ratchet green. The maintainer may
  overturn this at item 168's gate; see the `Left open` note.

- **A4 (clarify = `assume`):** condition 3's "extracted **and** catalogued" is
  read as two live facts about one path: it is the `path` of an entry of
  `catalogue.build_catalogue(strict=True)` (catalogued), **and** that entry's
  `observed.corpus.covered` is `True` (extracted — a real corpus record
  produced a value for it). Measured 2026-09-20: all five `islands`
  `signal_paths` satisfy both. Reading "catalogued" alone would let a path
  that is documented but never computed clear condition 3.

- **A5 (clarify = `assume`):** condition 4's proxy exclusion is implemented as
  a module constant `PROXY_RULE_IDS = ("bounds", "reference_delta")`, quoting
  the roadmap's parenthetical, applied **in addition to** the
  serves-exactly-this-mode test. Measured 2026-09-20, the single-mode test
  alone already excludes both on this tree (`bounds/metric_out_of_range` →
  `(1, 2, 3, 4)`; `reference_delta`'s `distance` / `out_of_range` / `robust_z`
  → `(1, 2, 3, 4, 8)`), so the constant changes no answer today. It exists so
  that a later item narrowing those edges to a single mode cannot make a
  generic volume proxy silently clear the bar — the failure the roadmap's
  parenthetical was written against.

- **A6 (measured, not pinned — item 164 has merged):** item 164's surfaces
  were re-measured on this tree on 2026-09-20 rather than assumed:
  `failure_modes.modes_for_detector('fragmentation', 'islands')` returns
  `(4,)`; `fragmentation`'s `RuleModeDeclaration.detectors` carries an
  `islands` `RuleDetector` whose `signal_paths` are the five
  `per_label.{label}.components.*` paths; `IntendedRule.detector_ids` is a
  tuple. No interface is pinned ahead of its implementation in this spec.

- **A7 (engine 1.59.0):** `loop.clarify = "assume"` in `aide.toml`, so A2–A5
  are defensible defaults recorded for audit at the queue boundary rather than
  questions put to the maintainer. Stage 32's "items are interactive by
  design" is honoured by item 168's gate, which is where a person reads modes
  3 and 4 and can overturn any of them.

## Implementation Steps

1. **`src/segfacet/traceability.py`** — add two module constants beside the
   existing ones: `PROXY_RULE_IDS: Tuple[str, ...] = ("bounds",
   "reference_delta")` and `BAR_CONDITIONS: Tuple[Tuple[int, str], ...]`,
   the five condition texts quoted from `roadmap.md` Stage 32 with a comment
   naming that section as the source and recording that condition 6 is
   excluded because it is a person's act (A2).

2. Add `@dataclasses.dataclass(frozen=True) class BarCondition` beside the
   existing frozen records (`ConformanceCase`, `RuleExercise`, …):
   `number: int`, `met: bool`, `subjects: Tuple[str, ...]`, `detail: str`.
   `subjects` is what the verdict turned on (case ids, feature paths,
   `"rule/detector"` pairs) so that no caller has to parse `detail`.

3. Add `def bar_conditions(mode_id: int, catalogue=None) -> Tuple[BarCondition,
   ...]`, returning the five records in ascending `number` order. A `mode_id`
   absent from `SPECIFICATION` raises `KeyError` from the plain dict lookup —
   no hand-written guard. **Every heavy import goes inside the function body**
   (`from segfacet.catalogue import build_catalogue`, `from
   segfacet.heuristics.rule import iter_rules`), exactly as `build_matrix`
   already does: `tests/test_159_prerequisite_test_and_import_defects.py`
   AC2 asserts that `import segfacet.traceability` pulls no `numpy` / `scipy`
   / `nibabel` root into `sys.modules`, and a module-level import turns it red.

4. Condition 1 — read `failure_modes.SPECIFICATION[mode_id]` and test the
   eight roadmap-named fields for truthiness. Add no validation helper:
   `ModeSpec.__post_init__` already validated the tree at construction.
   `subjects` = the field names checked; `detail` states that the
   maintainer-confirmation half is condition 6's (A2).

5. Condition 2 — reuse `failure_modes.case_agrees` (item 149) over
   `mode.corpus_cases`, plus the intersection of each non-empty
   `expected_firing` with the mode's own `{edge.rule_id}`. Do **not**
   re-implement `measured_firing`; `case_agrees` already drives it.

6. Condition 4 **before** condition 3, since condition 3 quantifies over
   condition 4's answer. Reuse `failure_modes.modes_for_detector` (item 164)
   per `(edge.rule_id, detector_id)` over `mode.intended_rules`, skipping any
   `edge.rule_id` in `PROXY_RULE_IDS`; a pair qualifies when
   `modes_for_detector(...) == (mode_id,)`. `subjects` = the qualifying
   `"{rule_id}/{detector_id}"` strings, sorted.

7. Condition 3 — resolve each qualifying detector back to its
   `RuleDetector.signal_paths` via `iter_rules()` and the rule's
   `mode_declaration.detectors`, then check each path against
   `catalogue.build_catalogue(strict=True)` (built once, or taken from the
   `catalogue` argument) for an entry whose `observed.corpus.covered` is
   `True` (A4). `subjects` = the sorted paths checked when met, the unmet
   paths when not.

8. Condition 5 — reuse `failure_modes.derive_status(mode) == "validated"`.

9. Extend `__all__` with `"BarCondition"`, `"bar_conditions"`,
   `"BAR_CONDITIONS"` and `"PROXY_RULE_IDS"`.
   `tests/test_138_traceability_matrix.py`'s surface test is a membership
   check (`name in traceability.__all__`), not an equality pin, so additions
   are safe.

10. **Change nothing else.** No edit to `src/segfacet/failure_modes.py`, no
    rule, detector, threshold, fixture or operator, and no regeneration of any
    committed artifact — so nothing fires differently and item 163's ratchet
    needs no authored expected set. **Adds no dependency.**

## Authorised paths

**May change:**

- `src/segfacet/traceability.py` — `BarCondition`, `BAR_CONDITIONS`,
  `PROXY_RULE_IDS`, `bar_conditions()` and the `__all__` additions.
- `tests/test_165_mode_4_at_the_bar.py` — this item's test module.

**Asserts against:**

- `src/segfacet/failure_modes.py` — every acceptance criterion reads
  `SPECIFICATION[4]`, `case_agrees`, `modes_for_detector` and `derive_status`
  from it. Mode 4's entry is pinned, not changed: `island_distance_from_main_body_mm`
  stays `hypothesised` (A3) and no expected firing set is authored.
- `src/segfacet/heuristics/fragmentation.py` — the `islands` `RuleDetector`
  and its five `signal_paths`, which AC4 and AC5 read live; unchanged, so the
  rule's findings are untouched.
- `docs/aide/feature_catalogue.generated.json` — the committed form of the
  catalogue AC4 recomputes live via `build_catalogue(strict=True)`; pinned,
  never regenerated by this item.
- `tests/corpus/manifest.json` — the geometric corpus `case_agrees` drives for
  AC3; read-only, no case added, removed or regenerated.

## Testing Strategy

**Module:** `tests/test_165_mode_4_at_the_bar.py`.

**Shape.** One module-scoped fixture calling
`catalogue.build_catalogue(strict=True)` once, and one module-scoped fixture
holding `bar_conditions(4, catalogue=<that catalogue>)`. **No
`build_catalogue()` call in any test body** — the adversarial cases below
re-call `bar_conditions` inside their patch, passing the same cached
catalogue, which is the sole reason the `catalogue` argument exists (item
169's clean-clone replay is its other consumer). This follows the
module-scoped-drive idiom of `tests/test_149_conformance_report.py`,
`tests/test_162_corpus_exercise_report.py` and
`tests/test_163_specificity_ratchet.py`.

**One test per AC** (AC1–AC7), each recomputing its predicate from the primary
source — `failure_modes` and the live catalogue — and asserting the record
agrees, never comparing against a literal.

**Adversarial cases beyond the AC tests — exactly four:**

- `proxy-detector-never-decides-the-mode`: with `SPECIFICATION` patched so
  that `bounds`'s `metric_out_of_range` edge is named by mode 4 alone (the
  same edge removed from modes 1, 2 and 3) and mode 4's `fragmentation` edge
  removed, `modes_for_detector('bounds', 'metric_out_of_range')` returns
  `(4,)` yet condition 4 stays unmet and `subjects` stays empty. Guards the
  failure mode where the roadmap's explicit exclusion of the generic volume
  proxies is implemented only as "serves exactly one mode", under which a mode
  whose sole single-mode detector is `bounds` or `reference_delta` silently
  clears the bar — the exact claim Stage 32 was written to prevent.
- `uncatalogued-detector-path-fails-condition-3`: with `fragmentation`'s
  `islands` `RuleDetector` patched to declare one extra `signal_paths` entry
  that no catalogue entry carries, condition 3 becomes unmet and names that
  path in `subjects`. Guards a condition-3 check that quantifies over the
  catalogue instead of over the detector's read paths, which is vacuously true
  for every detector and would report condition 3 met for a mode whose
  detector reads a path nothing extracts.
- `co-detection-alone-fails-condition-2`: with mode 4's `fragmentation` edge
  removed from `intended_rules` and nothing else changed, `inject_islands`
  still agrees with its expected set yet condition 2 becomes unmet. Guards a
  condition-2 check reduced to `case_agrees`, under which a mode detected only
  by *another* mode's rule reads as expressed by a committed fixture — the
  distinction `vision.md`'s `validated` rung and `_demonstrates` already draw,
  and which the bar restates.
- `unknown-mode-id-raises`: `bar_conditions(99)` raises `KeyError` rather than
  returning five unmet records. Guards a checker that answers "not at the bar"
  for a mode id that does not exist, under which item 168 could sign off, or
  refuse to sign off, against a typo'd id and read a real verdict into it.

**Existing tests to reconcile: none.** Swept 2026-09-20 across `tests/` by
surface rather than by name, for every shape this item could invalidate — a
fence asserting mode 4 is *not* yet at the bar, a pin on its status or rung, a
closed field-set pin on a `traceability` dataclass, an equality pin on
`traceability.__all__`, and a pin on any firing set. What was found, and why
each stays green untouched:

1. `tests/test_138_traceability_matrix.py` (~line 602) — asserts
   `name in traceability.__all__` for four names. A **membership** check, not
   an equality pin: step 9's additions do not touch it.
2. `tests/test_146_ninth_mode_and_first_proposed.py` (~line 1824) — asserts
   `derive_status(SPECIFICATION[4]) == "validated"`. It **agrees with AC6**
   and is left exactly as it is; this item changes no status.
3. `tests/test_151_stage30_validation.py` (~lines 1031–1090) — parses
   `progress.md`'s derived-status counts and compares them against **live**
   recomputed counts. No mode's derived status moves, so the counts do not.
4. `tests/test_147_specification_is_the_record.py` (~lines 339, 521) and
   `tests/test_151_stage30_validation.py` (~line 309) — pin every
   `stage18-metric-anchor` candidate feature against
   `feature_docs.MODE_ANCHOR_PATHS`, and every mode's `mechanism` against a
   token that resolves live. Both would bind if
   `island_distance_from_main_body_mm` were promoted; A3 leaves it
   `hypothesised`, so neither is touched.
5. `tests/test_149_conformance_report.py`, `tests/test_162_corpus_exercise_report.py`,
   `tests/test_163_specificity_ratchet.py` — drive measured-vs-expected firing
   over all 15 corpus cases. Nothing fires differently, so all three stay
   green with no `SPECIFICATION` edit.
6. `tests/test_159_prerequisite_test_and_import_defects.py` (AC2) — asserts
   `import segfacet.traceability` pulls in no `numpy` / `scipy` / `nibabel`.
   This is a **constraint on the implementation**, not a test to reconcile:
   step 3 keeps every heavy import inside the function body.

**No test fence needs narrowing**, and nothing in `tests/test_144_*`,
`tests/test_145_eight_hypothesised_modes.py`, `tests/test_150_maintainer_sign_off.py`
or `tests/test_151_stage30_validation.py` asserts that mode 4 is unfinished or
pins a rung this item moves.

## Validation

Beyond the suite, the maintainer's gate at item 168 needs the bar rendered for
a human to read. Run, on the claim branch:

    .venv/bin/python -c "import segfacet.traceability as t; print('\n'.join(repr(c) for c in t.bar_conditions(4)))"

Expect five `BarCondition` records, numbers 1–5, every one `met=True`, with
condition 4's `subjects` naming `fragmentation/islands` and condition 3's
naming the five `per_label.{label}.components.*` paths. Needs no
`[validation]` profile — it is CPU-only and uses no environment-gated
capability.

## Dependencies

- **Item 163** (specificity ratchet) — its
  `set(measured_firing) == set(expected_firing)` assertion over all 15 corpus
  cases is a hard constraint this item satisfies by changing nothing that
  fires; the Description says how.
- **Item 164** (first-class detector ids) — supplies
  `modes_for_detector()`, `RuleDetector.signal_paths` and
  `IntendedRule.detector_ids`, which conditions 3 and 4 are built on. Without
  it condition 4 is not mechanically answerable at all.

**Downstream:** item 167 measures mode 3 against `bar_conditions`. Item 168
consumes it twice over — its test that a mode claimed "at the bar" whose live
state fails any of conditions 1–5 fails the suite is a call to
`bar_conditions`, and **what this item leaves ready for that sign-off** is:
conditions 1–5 measured and asserted green for mode 4, the
`island_distance_from_main_body_mm` question surfaced as a `Left open` for the
maintainer to overturn or confirm, and no edit to mode 4's rendering in
`docs/aide/failure_modes.generated.md`, so item 168 signs off exactly the text
item 150 already signed. **Condition 6 can only be met by a person's
decision** — no acceptance criterion above attempts it. Item 169 attests
Stage 32's acceptance from a clean clone with its own venv.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether `island_distance_from_main_body_mm` is extracted,
  catalogued and read by the `islands` detector to *grade* an island finding
  by its distance from the main body. Deferred because no bar condition needs
  it (A3): condition 3 asks only about paths the deciding detector already
  reads, and building it would change `fragmentation`'s findings, needing a
  near/far fixture pair and an authored expected-set edit to keep item 163's
  ratchet green — work the `prototype` posture does not license for a
  deliverable that is already met. It stays a `hypothesised` candidate path,
  which is precisely the record that says "named, not built". The maintainer
  can overturn this at item 168's gate; if they do, it is a new item, not an
  amendment to this one.

- **Left open:** whether `bar_conditions` should eventually render into
  `traceability_matrix.generated.md` as a per-mode column. Not done here: no
  consumer in this queue reads it from the artifact, and adding a
  `TraceabilityMatrix` field would move both committed artifacts and every
  test pinning their shape. Item 169, which regenerates every artifact, is the
  natural place to decide it.

- **Noted for item 169, not fixed here:** `progress.md`'s Stage 32 deliverable
  bullets carry **item numbers two lower than the queue's** — the
  detector-ids bullet reads *(Item 162)*, the **D1** MVP-mode bullet (this
  item's own deliverable) reads *(Item 163)*, the D2 split-operator bullet
  reads *(Item 164)*, and so on through *(Item 166)*. The consequence is live:
  **D1 and D2 are already marked ✅** because items 163 and 164 merged against
  bullets that describe items 165 and 166. Correcting `progress.md` is outside
  this item's edit scope (only the Human gates table is permitted to
  `spec-author`), so it is captured in `docs/aide/insights.md` and raised in
  this item's hand-back; item 169's attestation must not inherit those ✅s.
