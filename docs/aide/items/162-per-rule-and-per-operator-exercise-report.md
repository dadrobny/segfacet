<!-- aide-template: item 2 -->
# Item 162 — Per-rule and per-operator corpus-exercise report

> **Created:** 2026-09-18 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 32 — Selected-Mode Refinement: one failure mode fully specified end to end (D0; closes Stage 20's held exercise-reporting deliverable)
> **Queue:** [`../queue/queue-022.md`](../queue/queue-022.md) · Item 162
> **Objectives:** G2 (every registered rule is exercised by ≥1 corpus case or recorded unexercised with a reason), G7 (the exercise count is measured on every regeneration, never transcribed)
> **Suggested branch:** `aide/162-per-rule-and-per-operator`

---

## Description

`segfacet.traceability` reports, per failure mode, what the specification
expects and what the corpus measures (item 149's `ConformanceReport`). It
reports nothing per **rule** or per **operator**: a registered rule that fires
on no case, and a registered perturbation operator that generates no corpus
case, are both invisible today. This item adds those two directions to the
same generator and the same two committed artifacts, so that neither can recur
unnoticed:

- **Per rule** — exercised by ≥1 committed corpus case, across **both** corpora
  (`tests/corpus/manifest.json` and `tests/corpus/intensity/manifest.json`), or
  recorded unexercised with a reason **derived from the signed-off
  specification**: the strongest evidence rung among the
  `SPECIFICATION[*].intended_rules` edges naming that rule, together with the
  mode ids those edges belong to.
- **Per operator** — used by ≥1 `segfacet.synth.corpus.CASE_RECIPE` entry, or
  recorded unused with a reason.

A rule or operator that is **neither exercised nor recorded** is a named hole
in its direction, and the direction's completeness flag turns the suite red.

### Re-authored, not amended — and re-measured

This replaces item 139's preserved spec
([`139-per-rule-and-per-operator.md`](139-per-rule-and-per-operator.md), 33
criteria against the pre-sign-off catalogue). That file keeps its name as the
provenance of the measurements re-measured here; it is not edited. Its
2026-09-03 figures were inputs, and **two of the three have since moved** —
measured on this tree, 2026-09-18, through the public entry points the
generator will use:

| Claim (2026-09-03) | Measured 2026-09-18 |
| --- | --- |
| the registered `fuse` operator generates no corpus case | **stale** — `CASE_RECIPE`'s `fuse_adjacent` uses it; **all 11** registered operators are used and **none** is unused |
| 7 of 10 rules exercised | **holds, with a different membership** — exercised: `border`, `coverage`, `fragmentation`, `intensity`, `mislabel`, `overlap`, `sequence`; unexercised: `bounds`, `reference_delta`, `intensity_reference_delta` |
| `intensity_reference_delta` is driven by nothing | **holds** — the intensity corpus is built against no reference and `intensity_pipeline_findings` attaches none |

Those figures are provenance. Every criterion below asserts agreement with a
**fresh** measurement, never a literal (A6): items 163–167 legitimately move
them, which is the point of the report.

### The reasons are derived, not authored (the central discipline)

The queue names three kinds of reason an unexercised rule may carry: an
evidence rung, a `proposed` mode, and "no harness attaches a reference". All
three already exist, written down and signed off, in
`src/segfacet/failure_modes.py`. This item **reads** them rather than
re-authoring a second copy beside them:

- Each of the three unexercised rules is named only by edges at the
  `needs-real-data` rung (`bounds` on modes 1–4, `reference_delta` on modes
  1–4 and 8, `intensity_reference_delta` on mode 16, measured 2026-09-18), so
  the derived reason is that rung, and the record names the modes it came from.
- *Why* that rung was authored — mode 16's "the synthetic intensity corpus is
  built against no reference distribution and the harness attaches none" — is
  `ModeSpec.mechanism`, rendered in the **same** two artifacts, one section
  above. Copying it into the exercise record would be a second, drifting
  statement of one fact.
- A `proposed` mode carries no `intended_rules` (measured 2026-09-18: modes 5,
  7, 10–14 all carry zero edges), so no registered rule can be named **only**
  by a proposed mode. That reason kind cannot arise for a rule on this tree and
  is not pre-built.
- An unexercised rule whose specification edges include a
  `synthetic-demonstrable` one has **no** derivable reason — the specification
  claims the corpus demonstrates it and the corpus does not. That is a hole, by
  design, and the case the suite exists to catch.

So the only authored string in the whole feature is an unused **operator's**
reason, in a module-level mapping that ships **empty** on this tree (A4).

### What this item is NOT

It adds **no** corpus case to either corpus and edits neither manifest. It
attaches no reference to any harness path. It changes no rule, threshold,
extractor, detector, verdict, report schema or CLI behaviour, edits no
`ModeSpec`, regenerates neither catalogue artifact, and adopts no specificity
ratchet (item 163) and no detector ids (item 164). It does not touch
`vision.md` or `roadmap.md`, and it ticks no `progress.md` box — item 169
attests Stage 20's criteria with evidence.

## Acceptance Criteria

- [ ] **AC1: One exercise record per registered rule.** In the committed JSON,
  `sorted(payload["exercise"]["rules"])` equals
  `sorted(rule.rule_id for rule in segfacet.heuristics.iter_rules())` as the
  test reads the registry in the same session — no more, no fewer.

- [ ] **AC2: One exercise record per registered operator.**
  `sorted(payload["exercise"]["operators"])` equals
  `sorted(segfacet.synth.perturbation.perturbation_names())` as the test reads
  the registry in the same session — no more, no fewer.

- [ ] **AC3: A rule's exercising cases are re-derived from the measured firing
  of both corpora.** For every rule, its `exercised_by` list equals the sorted
  `(corpus, case_id)` pairs of every case in `build_matrix().conformance.cases`
  whose `measured_firing` contains that `rule_id`, recomputed by the test from
  a fresh `build_matrix()` — so the geometric and the intensity manifest both
  contribute, and no case is transcribed.

- [ ] **AC4: A rule record is exercised or reasoned, never both and never
  neither.** Each record has `state == "exercised"` with a non-empty
  `exercised_by` and an empty `reason`, **or** `state == "unexercised"` with an
  empty `exercised_by` and a `reason` drawn from exactly
  `tuple(r for r in segfacet.failure_modes.EVIDENCE_RUNGS if r != "synthetic-demonstrable")`,
  recomputed by the test from that live vocabulary.

- [ ] **AC5: An unexercised rule's reason is the strongest specification rung
  naming it, and its `reason_modes` are the modes that named it.** For every
  `state == "unexercised"` record, `reason` equals the strongest (earliest in
  `EVIDENCE_RUNGS`) `IntendedRule.evidence_rung` over every
  `SPECIFICATION[m].intended_rules` edge whose `rule_id` is that rule, and
  `reason_modes` equals the sorted mode ids `m` carrying such an edge — both
  recomputed by the test from `segfacet.failure_modes.SPECIFICATION`.

- [ ] **AC6: The rule direction is complete exactly when no registered rule is
  both unexercised and unreasoned.** `payload["directions"]["rule_exercise"]`
  reports `complete: true` with an empty `holes` list when every record
  satisfies AC4, and `complete: false` with `holes` naming exactly the
  `rule_id`s of the records that do not. *(closes Stage 20 criterion 3)*

- [ ] **AC7: An operator's cases are re-derived from `CASE_RECIPE`.** For every
  operator, its `cases` list equals the sorted `case_id`s of
  `segfacet.synth.corpus.CASE_RECIPE` entries whose `perturbation` equals that
  operator's name, recomputed by the test from the live recipe.

- [ ] **AC8: An operator record is used or reasoned, and the operator direction
  reports its holes.** Each record has `state == "used"` with a non-empty
  `cases` and an empty `reason`, **or** `state == "unused"` with an empty
  `cases` and a `reason`; and `payload["directions"]["operator_exercise"]`
  reports `complete: false` with `holes` naming exactly the operator names that
  are unused with an empty `reason`, `complete: true` with an empty `holes`
  otherwise.

- [ ] **AC9: The committed JSON is byte-identical to a fresh build.**
  `docs/aide/traceability_matrix.generated.json` read as bytes equals
  `json.dumps(matrix_to_dict(build_matrix()), indent=2, sort_keys=True,
  ensure_ascii=False)` plus one trailing newline, encoded UTF-8, computed in
  the test.

- [ ] **AC10: The committed Markdown is byte-identical to a fresh render.**
  `docs/aide/traceability_matrix.generated.md` read as bytes equals
  `render_markdown(build_matrix())` encoded UTF-8, computed in the test.

- [ ] **AC11: The Markdown carries every exercise record.** For every rule
  record and every operator record in the committed JSON, the committed
  Markdown holds a table row in the matching exercise section whose first cell
  is that record's key and whose remaining cells carry its `state` and either
  each of its `case_id`s (rules: each `corpus/case_id`) or its `reason`.

- [ ] **AC12: The exercise sections render after the rule-declaration table.**
  In the committed Markdown, the `## Rules -> failure modes` heading precedes
  both exercise headings, and for every registered `rule_id` the **first**
  table row in the document whose first cell equals that `rule_id` is that
  rule's declaration row.

- [ ] **AC13 (added 2026-09-20): the exercise report records membership, never
  a stored count — item 149's AC33 fence, narrowed to the claim that survives.**
  The token `exercise_count` appears nowhere in
  `docs/aide/traceability_matrix.generated.json`, nowhere in
  `docs/aide/traceability_matrix.generated.md` and nowhere in
  `src/segfacet/traceability.py`: every exercise record names the cases that
  exercise it (`exercised_by` for a rule, `cases` for an operator), from which
  any count is recomputable, and no scalar count is stored anywhere (**G7** —
  measured on every regeneration, never transcribed).

- [ ] **AC14 (added 2026-09-20): item 150's Stage-20 held-items gate asserts
  each bullet's true leading icon.** Read from `docs/aide/progress.md` as
  committed, the Stage 20 deliverable bullet owning the `*(Item NNN)*` marker
  starts with `- ❌` for items 139, 140 and 142 — their numbers were retired at
  the queue-022 boundary (2026-09-18) — and with `- ⏸️` for item 141, whose
  work moved to Stage 31 (item 154) and was not re-queued.

## Assumptions

- **A1 (this item extends item 149's module and its two committed artifacts):**
  the generator stays `src/segfacet/traceability.py` and the report stays
  `docs/aide/traceability_matrix.generated.{json,md}`. The module's own scope
  fence names this item as the carrier ("It builds **no** per-rule or
  per-operator corpus-**exercise** columns — item 139's deliverable,
  re-specified against this output"). A second artifact would duplicate the
  registry and manifest reads, need its own `.gitattributes` pins, and hand
  item 169 two files to reconcile where one claim is made. **No
  `.gitattributes` edit is needed**: lines 54–55 already pin both paths
  `text eol=lf`, which is what keeps AC9/AC10's byte comparisons true on
  Windows after a fresh checkout (CLAUDE.md, "Byte-reproducible committed
  fixtures need a `.gitattributes` LF pin").
- **A2 (the exercise state is derived from item 149's `ConformanceReport`, not
  from a second corpus drive):** `_build_conformance` already runs every case
  of both committed manifests through
  `segfacet.failure_modes.measured_firing`, so the rule direction is a
  re-keying of a measurement `build_matrix()` has already paid for. A second
  drive would be a second source of truth about what fires, and the two would
  eventually disagree with no document able to adjudicate — the defect item 149
  retired for the mode direction.
- **A3 (the reason vocabulary is the specification's own rung vocabulary, minus
  the demonstrable rung):** derived as
  `tuple(r for r in EVIDENCE_RUNGS if r != "synthetic-demonstrable")`, never
  retyped, so a future rung added in `failure_modes.py` is admitted without
  editing this module. Measured 2026-09-18, all three unexercised rules resolve
  to `needs-real-data`; `structurally-unobservable` is reachable but unused
  (mode 15's `overlap` edge carries it and that rule **is** exercised, through
  `force_overlap`'s `reconstructed_record` path).
- **A4 (an unused operator's reason is the one authored string, and it ships
  empty):** `UNUSED_OPERATOR_REASONS: Dict[str, str]` is empty on this tree —
  all 11 registered operators are used (measured 2026-09-18) — so the recorded
  branch is reachable and tested only adversarially. It exists because the
  deliverable requires "used, **or** recorded unused with a reason"; without it
  an operator deliberately kept for a mode with no fixture could only ever be a
  hole. An operator name in that mapping that is not registered, or is
  registered and used, is itself a conflict the module reports rather than
  ignores.
- **A5 (measured figures are provenance, not assertions):** the Description's
  7-of-10, its 11-of-11 and the per-rule membership are the 2026-09-18
  measurement on this tree. Every criterion asserts agreement with a fresh
  measurement, because items 163 (the ratchet), 166 (a split operator and its
  case) and 167 (mode 3's detector) are queue-mates that legitimately move
  them.
- **A6 (item 138's `_row_for_rule` scans the whole document, so section order is
  load-bearing):** `tests/test_138_traceability_matrix.py::_row_for_rule`
  returns the **first** Markdown table row whose first cell equals the
  `rule_id`. A rule-exercise table rendered before `## Rules -> failure modes`
  would silently hand that helper the wrong row. AC12 pins the ordering from
  this item's side, so the constraint is enforced rather than remembered.
- **A7 (the payload stays float-free, so the byte comparisons stay
  legitimate):** `tests/committed_artifact_guard.py`'s `ALLOWLIST` covers both
  artifacts under the `no-float-leaf` ground, discharged by
  `tests/test_149_conformance_report.py::test_ac21_traceability_matrix_has_no_float_leaf`.
  The exercise section adds rule ids, case ids, operator names, state strings,
  rung strings and integer mode ids only — no float, and no date (item 138's
  AC28 forbids a `YYYY-MM-DD` anywhere in either artifact). No `ALLOWLIST` or
  `GROUNDS` edit, so the guard's own vocabulary count is untouched.
- **A8 (no human gate):** every input is committed state on this tree and every
  judgement here is derived from the signed-off specification, the rule
  registry or a committed manifest. Nothing needs a person's decision or an
  out-of-band prerequisite, so no row is added to `progress.md`'s
  `## Human gates` table.
- **A9 (engine 1.59.2):** `aide check`'s `.gitattributes` lint resolves a
  fixture path through the test's AST; both artifact paths are already pinned
  (A1), so it stays silent for this item with no `.gitattributes` edit.

## Implementation Steps

1. **Extend `src/segfacet/traceability.py`'s module docstring** with the two
   exercise directions, the completeness contract (both complete, always — a
   hole in either is a defect), and the scope fence: this module reports; it
   adds no corpus case, attaches no reference, and authors no reason a rule's
   specification edges do not already carry. Replace the stale "it builds **no**
   per-rule or per-operator corpus-exercise columns — item 139's deliverable"
   paragraph with what this item landed. Leave `SCHEMA_VERSION` at `"1.1"` (see
   Decisions).
2. **Add the two closed vocabularies and the one authored mapping**, beside the
   module's existing module-level constants: `EXERCISE_STATES = ("exercised",
   "unexercised")`, `OPERATOR_STATES = ("used", "unused")`, and
   `UNUSED_OPERATOR_REASONS: Dict[str, str] = {}` (A4). The unexercised-reason
   vocabulary is **not** a constant — derive it in the function body from
   `failure_modes.EVIDENCE_RUNGS` (A3).
3. **Add three frozen record dataclasses** in the module's existing style, beside
   `ConformanceCase`: `RuleExercise(rule_id, state, exercised_by, reason,
   reason_modes)`, `OperatorExercise(name, state, cases, reason)` and
   `ExerciseReport(rules, operators, rule_direction, operator_direction)` — the
   two directions reusing the existing `DirectionReport`, not a new shape. Add
   `exercise: ExerciseReport` to `TraceabilityMatrix`.
4. **`_build_exercise(conformance, failure_modes_module)` — the rule half.**
   Take the already-built `ConformanceReport` as an argument (A2; no second
   corpus drive). Invert `case.measured_firing` into
   `{rule_id: [(corpus, case_id), …]}`. For each `rule.rule_id` from
   `heuristics.iter_rules()`, emit `exercised` with the sorted pairs, or
   `unexercised` with the strongest rung over the `SPECIFICATION[m].intended_rules`
   edges naming it (strength = index in `EVIDENCE_RUNGS`, the ordering
   `derive_mode_rung` already uses) and the sorted mode ids that carried them —
   and an empty reason when the strongest rung is `synthetic-demonstrable` or
   no edge names the rule at all, which makes it a hole.
5. **`_build_exercise` — the operator half.** For each
   `perturbation_names()` entry, collect the sorted `case_id`s of `CASE_RECIPE`
   entries whose `perturbation` matches; `used` when non-empty, else `unused`
   with `UNUSED_OPERATOR_REASONS.get(name, "")`. No operator is probed,
   constructed or applied — the used/unused split is a recipe read, and a probe
   would put a fixture generator inside a reporting module.
6. **Both `DirectionReport`s** are scored the same way: `holes` is the sorted
   keys of every record with neither a case nor a reason, `complete` is
   `not holes`.
7. **Call it from `build_matrix()`** immediately after `_build_conformance`,
   passing that report in, and attach it to the matrix.
8. **`matrix_to_dict`** gains a top-level `"exercise"` block
   (`{"rules": {…}, "operators": {…}}`, each keyed by name and sorted), and
   `"directions"` gains `"rule_exercise"` and `"operator_exercise"` in the same
   `{complete, holes}` shape the two existing entries use. Strings and integers
   only — no float, no date, no absolute path (A7).
9. **`render_markdown`** gains two sections **after** the conformance section,
   at the end of the document (never before `## Rules -> failure modes` — A6):
   `## Rule corpus exercise` (`Rule | State | Exercised by | Reason | Reason modes`,
   `exercised_by` rendered `corpus/case_id`) and `## Operator corpus exercise`
   (`Operator | State | Cases | Reason`), each preceded by its direction's
   `complete`/`holes` line in the form the existing sections use.
10. **Regenerate and commit both artifacts** —
    `.venv/bin/python -m segfacet.traceability` — and check the result against
    the Description's 2026-09-18 measurement, investigating (never silencing)
    any divergence.
11. **Narrow item 149's AC33 fence** in `tests/test_149_conformance_report.py`
    (added 2026-09-20; exact wording under `## Correction — 2026-09-20`):
    forbid only `"exercise_count"`, rename both guards to say so, and record
    the narrowing in a dated comment above the block.
12. **Update item 150's held-items pin** in
    `tests/test_150_maintainer_sign_off.py` (added 2026-09-20): replace the
    `_HELD_ITEMS` tuple with the icon each bullet must now carry, and assert
    that icon rather than `⏸️` unconditionally.

## Authorised paths

**May change:**

- `src/segfacet/traceability.py` — the generator gains the two exercise directions (AC1–AC8).
- `docs/aide/traceability_matrix.generated.json` — the regenerated report, now carrying `exercise` (AC1–AC9).
- `docs/aide/traceability_matrix.generated.md` — its rendered form, now carrying the two exercise sections (AC10, AC11, AC12).
- `tests/test_162_corpus_exercise_report.py` — this item's test module.
- `tests/test_149_conformance_report.py` — **added 2026-09-20.** AC13 narrows item 149's AC33 fence, whose premise ("item 139's deliverable is observably absent") this item expires by landing that deliverable: AC6/AC8 require the very `operator_exercise` key the fence forbids.
- `tests/test_150_maintainer_sign_off.py` — **added 2026-09-20.** AC14 updates the held-items pin, discharging the dated handover item 150 recorded above `_HELD_ITEMS` itself ("the first item that lands any of 139-142 must list this test file under its 'Authorised paths -> May change' and update this test").

**Asserts against:**

- `src/segfacet/failure_modes.py` — `SPECIFICATION`, `EVIDENCE_RUNGS` and each `IntendedRule.evidence_rung`; AC4 and AC5 recompute the reason and the reason modes from them. Unchanged: no `ModeSpec` field is edited by this item.
- `src/segfacet/heuristics/rule.py` — `iter_rules()`, the registry AC1 and AC6 enumerate. Unchanged, and no rule, threshold or declaration is edited.
- `src/segfacet/synth/corpus.py` — `CASE_RECIPE`, the sole source of AC7's used/unused split; unchanged.
- `src/segfacet/synth/perturbation.py` — `perturbation_names()`, the operator registry AC2 enumerates; unchanged.
- `tests/corpus/manifest.json` — the eleven geometric cases, reached through `build_matrix().conformance` (AC3). Read-only: no case is added, removed or edited.
- `tests/corpus/intensity/manifest.json` — the four intensity cases, same path and same AC. Read-only — the adversarial `intensity-corpus-is-read` case removes cases from what the *generator loads*, via a monkeypatched loader, never from the committed file.
- `tests/test_138_traceability_matrix.py` — not edited; AC12 pins the whole-document `_row_for_rule` invariant it depends on (A6), and its schema-hygiene tests re-run against the grown artifacts as the standing guard.
<!-- 2026-09-20: the `tests/test_149_conformance_report.py` bullet that stood
     here has moved to **May change** (AC13). Its original text is preserved
     verbatim under `## Correction — 2026-09-20`; it is removed from this list
     rather than annotated in place because `aide scope` reads Asserts against
     as pinned-not-changed and would report every AC13 edit as a contradiction.
     The claims it carried are unchanged and still hold: the float-leaf test
     still discharges the `no-float-leaf` ground (A7), and `SCHEMA_VERSION`
     stays `"1.1"`. -->
- `tests/committed_artifact_guard.py` — the `ALLOWLIST` entries that make AC9/AC10 legitimate byte comparisons; read-only, with no entry added and no ground added.

## Testing Strategy

New module: **`tests/test_162_corpus_exercise_report.py`**, one focused test per
AC (AC1/AC3/AC4/AC5 parametrised over the ten registered rules, AC2/AC7/AC8 over
the eleven registered operators), building the matrix once through a
**module-scoped fixture** and re-deriving every asserted value in-session from
the registry, the specification and `CASE_RECIPE` rather than comparing against
a literal. Beyond the AC tests, exactly these cases:

- **stub-rule-hole**: register a stub rule (registry snapshot/restore, the house
  pattern in `tests/test_026_rule_engine_core.py`) that fires on no case and
  that no `SPECIFICATION` edge names — `rule_exercise` reports `complete: false`
  with a hole naming it. *Guards:* a registered rule that fires nowhere and is
  recorded nowhere passing silently — the failure this report exists to make
  impossible.
- **stub-operator-hole**: register a stub `Perturbation` that no `CASE_RECIPE`
  entry uses and that carries no `UNUSED_OPERATOR_REASONS` entry —
  `operator_exercise` reports `complete: false` with a hole naming it.
  *Guards:* the 2026-09-03 `fuse` defect class — an operator generating no case
  at all, invisible in every artifact.
- **recorded-unused-operator**: the same stub with a monkeypatched
  `UNUSED_OPERATOR_REASONS` entry — its record is `unused` with that reason and
  the direction is complete. *Guards:* the recorded branch being unreachable, so
  that a deliberately unused operator could only ever read as a defect.
- **demonstrable-rule-unexercised-is-a-hole**: monkeypatch the specification so
  an unexercised rule's only edge reads `synthetic-demonstrable` — no reason is
  derived and the direction reports a hole. *Guards:* the rung derivation
  rubber-stamping a rule the specification claims the corpus demonstrates and
  that the corpus does not fire.
- **intensity-corpus-is-read**: monkeypatch the generator's intensity-manifest
  loader to drop `implausible_metal`, `implausible_soft_tissue` and
  `degenerate_uniform` — `intensity` flips from `exercised` to `unexercised`.
  *Guards:* a report that reads only `tests/corpus/manifest.json` and is wrong
  about every intensity-corpus rule while reading plausibly.
- **frozen-and-uncached**: two `build_matrix()` calls in one session return
  equal exercise reports, the records refuse in-place mutation, and
  `matrix_to_dict` returns a fresh tree each call. *Guards:* a memoised or
  mutable report silently defeating the four monkeypatch cases above — the
  module's stated determinism contract.

**Existing tests to reconcile — none requires editing**, and all four were
checked against this tree on 2026-09-18:

- `tests/test_149_conformance_report.py::test_ac2_schema_version_bumped_to_1_1`
  — pins `SCHEMA_VERSION == "1.1"` in both the module and the committed payload.
  Leaving the version alone (Decisions) is what keeps it green. **Verify, do not
  edit.**
- `tests/test_149_conformance_report.py::test_ac21_traceability_matrix_has_no_float_leaf`
  — walks the payload for `float` instances. The exercise section adds none
  (A7). **Verify, do not edit.**
- `tests/test_138_traceability_matrix.py::test_ac5_markdown_rows_agree_with_json_for_every_mode_and_rule`
  — its `_row_for_rule` helper scans the **whole** document for the first row
  whose first cell is the `rule_id`; rendering the rule-exercise table before the
  declaration table turns it red. AC12 is the guard (A6). **Verify, do not
  edit.**
- `tests/test_138_traceability_matrix.py::test_ac28_committed_artifacts_carry_nothing_environment_dependent`
  — forbids any float leaf, any `YYYY-MM-DD`, the repo root, a drive-letter
  prefix and this machine's hostname in either artifact. The new section is
  strings and integers only and carries no date (step 8). **Verify, do not
  edit.**

- **Superseded 2026-09-20 — two merged items' test files DO require editing,
  and a third pair of corrections lands in this item's own module.** The
  sweep above missed `tests/test_149_conformance_report.py`'s AC33 fence and
  `tests/test_150_maintainer_sign_off.py`'s held-items pin, both of which
  contradict this item's criteria on this tree. Read
  `## Correction — 2026-09-20` below before writing or re-deriving any test;
  it names the four cases the test-writer must land and supersedes this list's
  "none requires editing" for those two files only. The other two entries
  (`tests/test_138_traceability_matrix.py`) stand as written.

No test anywhere pins the per-rule firing membership, the operator registry's
used/unused split, or the artifacts' section count, so nothing else changes
behaviour under this item.

## Validation

Beyond the suite, observe the report directly (no `[validation]` profile
needed — CPU-only, and the intensity harness pins `enable_pyradiomics=False`,
so the `pyradiomics` profile is deliberately irrelevant here):

1. `.venv/bin/python -m segfacet.traceability` — regenerates both artifacts in
   place.
2. `git status --short docs/aide/traceability_matrix.generated.json docs/aide/traceability_matrix.generated.md`
   — expect no change after step 1 on a committed tree: the byte-reproducibility
   claim observed rather than asserted.
3. Read `## Rule corpus exercise` in
   `docs/aide/traceability_matrix.generated.md` end to end and confirm by eye:
   ten rule rows, seven `exercised`; `overlap` exercised by
   `geometric/force_overlap`; `intensity` exercised by three intensity-corpus
   cases; `bounds`, `reference_delta` and `intensity_reference_delta`
   `unexercised` at `needs-real-data` with their reason modes.
4. Read `## Operator corpus exercise` and confirm: eleven operator rows, all
   `used`, `fuse` among them with `fuse_adjacent`.
5. `.venv/bin/python -c "import json;d=json.load(open('docs/aide/traceability_matrix.generated.json'));print(d['directions']['rule_exercise'],d['directions']['operator_exercise'])"`
   — expect both `complete: true` with empty holes.
6. `python .aide/scripts/aide.py check` — expect no `.gitattributes` warning
   (both paths are already pinned).

## Dependencies

- **Item 149** — `segfacet.traceability.ConformanceReport` and its per-case
  measured firing, which the rule direction re-keys rather than re-measuring;
  the `DirectionReport` shape; the JSON/Markdown serialisation contract; and the
  `no-float-leaf` allowlist ground AC9/AC10 rest on.
- **Item 150** — the maintainer-signed-off sixteen-mode specification, whose
  per-edge evidence rungs are the reasons this report derives.
- **Item 155** — the corpus-case `kind` field (`clean_control` / `condition` /
  `failure`), which is what lets a clean control fire nothing without being
  scored as a disagreement in the report this one extends.
- **Item 157** — the current corpus `case_id`s (no `modeN_` prefix), which every
  `exercised_by` entry carries.

**Downstream:** item 163 (the specificity ratchet) reads the same measured
firing sets; item 164 narrows this report's per-rule rows to per-detector ones;
items 166 and 167 add an operator, a case and a detector that this report must
pick up without being edited; item 169 regenerates it from a clean clone and
attests Stage 20 criteria 3–5 with evidence.

## Decisions & Trade-offs

- **D1 (`reason_modes` is every naming edge, not just the strongest-rung
  ones):** AC5 reads "the sorted mode ids `m` carrying such an edge" over
  "every `SPECIFICATION[m].intended_rules` edge whose `rule_id` is that
  rule" — the antecedent is the whole edge set, not the subset at the
  winning rung. Implemented as: collect every mode id with any edge naming
  the rule, take the strongest rung across that same set for `reason`, and
  report all of those mode ids as `reason_modes`. On this tree every
  unexercised rule's edges are single-rung per rule (`bounds` and
  `reference_delta` only ever carry `needs-real-data`; `intensity_reference_delta`
  likewise), so the two readings coincide today; the distinction only bites
  if a future rule ever carries edges at two different rungs across modes.
- **D2 (a hole's `reason_modes` is empty, matching its empty `reason`):**
  neither AC4 nor AC5 specifies `reason_modes` for the two hole shapes (no
  naming edge at all; strongest edge is `synthetic-demonstrable`). Both are
  implemented as `reason_modes = ()`, kept in lockstep with the empty
  `reason` — a hole record carries no derived content in either field,
  which is what "no derivable reason" (Description) means for the mode list
  too. No registered rule takes this path on this tree — the
  `demonstrable-rule-unexercised-is-a-hole` adversarial case is what
  exercises it, via a specification monkeypatch.
- **D3 (added 2026-09-20 — why this item edits two merged items' test
  files):** both guards were written *about* this item's deliverable, not
  about their own. Item 149's AC33 fenced item 139's deliverable out of the
  module it was extending, and named it as such ("item 139's deliverable is
  observably absent"); item 150 recorded, in the comment directly above
  `_HELD_ITEMS`, that the first item landing any of items 139–142 must widen
  its own Authorised paths to include that file and update the test. Item 162
  is the item both of them named. Neither edit weakens what its author was
  guarding: AC33's surviving claim (no stored exercise **count**) is kept and
  tightened onto one token, and item 150's pin keeps item 141, the one
  deliverable still genuinely held. Leaving either alone is not an option —
  no implementation can satisfy AC6/AC8 and keep AC33's `operator_exercise`
  token out of the JSON, and the held-items pin is red on this tree
  regardless of what this item builds, because the queue-022 planning commit
  flipped three icons the pin asserts. Handing the second one off as a
  pre-existing base defect would hand it to an item that did not land 139's
  deliverable, which is exactly the hand-off item 150's comment wrote to
  prevent.
- **Left open:** whether the additive `exercise` section warrants a
  `SCHEMA_VERSION` bump to `"1.2"`. Not taken here —
  `tests/test_149_conformance_report.py::test_ac2_schema_version_bumped_to_1_1`
  pins `"1.1"` in both the module and the payload, and no consumer reads the
  version at all, so a bump would buy an edit to a merged item's test and
  nothing else. It belongs with the next change that actually breaks a reader.

## Correction — 2026-09-20

**Appended, not a rewrite.** Everything above stands as authored on
2026-09-18; this section records what validation round 1 found wrong with it
and what replaces it. Four corrections, two of them spec defects that no
implementation could have satisfied.

### 1. `tests/test_149_conformance_report.py` — AC33's fence has expired

**The conflict.** `test_ac33_no_per_rule_or_per_operator_exercise_column_in_either_artifact`
and `test_ac33_traceability_module_defines_no_exercise_derivation` assert that
the literal tokens `"exercise_count"`, `"operator_exercise"`, `"corpus_exercise"`
(and `"exercise column"`, artifacts only) appear **nowhere** in either
committed artifact or in `src/segfacet/traceability.py`. AC6 and AC8 above
require exactly the keys `payload["directions"]["rule_exercise"]` and
`payload["directions"]["operator_exercise"]`. This was item 149's "this is a
later item's deliverable" fence, and item 162 **is** that later item — its own
AC33 text says so ("item 139's deliverable is observably absent"). The fence's
premise expires by design when this item lands, so the spec's original claim
that this file is "not edited" cannot hold.

**The resolution.** Narrowed, not deleted — one claim of item 149's AC33
survives this item and is worth keeping: an exercise record states *which*
cases exercise it, never a stored scalar count, which is what **G7**
("measured on every regeneration, never transcribed") asks of it, and what
this item's own design already does (`exercised_by`, `cases`; no count field
anywhere in steps 3–9). AC13 pins that surviving claim. Concretely, in
`tests/test_149_conformance_report.py`:

- The block comment above the two guards becomes a dated record of the
  narrowing, naming item 162 as the item that expired the rest:
  item 149's AC33 fenced item 139's whole deliverable out of this module;
  item 162 lands it (AC6/AC8), so only the no-stored-count half remains.
- `test_ac33_no_per_rule_or_per_operator_exercise_column_in_either_artifact`
  is renamed `test_ac33_no_exercise_count_scalar_in_either_artifact` and its
  `forbidden_token` loop narrows from the four tokens to exactly
  `("exercise_count",)`. The two `read_text` reads, the two asserts and the
  failure message are otherwise unchanged.
- `test_ac33_traceability_module_defines_no_exercise_derivation` is renamed
  `test_ac33_traceability_module_derives_no_exercise_count` and its loop
  narrows the same way, over the same module source read.
- Nothing else in the file changes. The renames are safe: no `progress.md`
  attestation, queue or item spec cites either name (grepped 2026-09-20), and
  item 128 is the house precedent for renaming a merged item's test when its
  subject narrows.

**The Authorised-paths bullet this displaces**, preserved verbatim as
authored on 2026-09-18 under **Asserts against**:

```
- `tests/test_149_conformance_report.py` — not edited; its float-leaf test is what discharges the `no-float-leaf` allowlist ground AC9/AC10 rely on (A7), and its `SCHEMA_VERSION == "1.1"` pin is why the version is left alone (Decisions).
```

Both of its substantive claims still hold — `test_ac21_…_no_float_leaf` still
discharges the `no-float-leaf` ground (A7), and `SCHEMA_VERSION` is still left
at `"1.1"` (Left open, above). Only "not edited" is false, and the path is
therefore listed under **May change** instead: a path may not sit in both
lists, and `aide scope` reads Asserts against as pinned-not-changed, so
leaving it there would fail this item's scope check on the AC13 edit with no
spec-side fix visible.

### 2. `tests/test_150_maintainer_sign_off.py` — the held-items pin is stale

**The conflict.** `_HELD_ITEMS = (139, 140, 141, 142)` and
`test_ac13_the_four_held_stage_20_items_are_still_deferred` assert that each
of those items' Stage 20 deliverable bullet still leads with `⏸️`. Measured on
this tree 2026-09-20: items 139, 140 and 142 lead with `❌` and carry
"**Number retired, 2026-09-18:** the deliverable is re-queued as item
162/163/169"; only item 141 still leads with `⏸️`. Three of the four
parametrisations are red.

**Why it is item 162's to discharge, not a base-branch defect to hand off.**
Item 150 wrote the hand-off itself, in the comment directly above
`_HELD_ITEMS`: *"**A dated claim** (D3): the first item that lands any of
139-142 must list this test file under its 'Authorised paths -> May change'
and update this test. Recorded here so that item's author does not discover it
as a red suite."* Item 162 is the item landing item 139's deliverable. The
icons were flipped by queue-022's planning commit rather than by this branch,
but the discharge was addressed to this item by name.

**The resolution.** The pin is updated, not dropped — item 141 remains
genuinely held, and a Stage-20 bullet silently losing its icon is still worth
catching. Concretely:

- `_HELD_ITEMS` is replaced by a mapping from item number to the leading icon
  its bullet must now carry — `{139: "❌", 140: "❌", 141: "⏸️", 142: "❌"}` —
  and its comment gains a dated line recording the 2026-09-18 retirement, the
  successor item for each of the three, and that item 141 keeps `⏸️` because
  its work moved to Stage 31 (item 154) and was not re-queued.
- `test_ac13_the_four_held_stage_20_items_are_still_deferred` is renamed
  `test_ac13_each_stage_20_held_item_bullet_carries_its_recorded_icon`,
  parametrised over that mapping's items, and its final assertion becomes
  `bullet.startswith(f"- {icon}")` with the icon taken from the mapping. The
  marker lookup, the walk back to the owning bullet and the
  exactly-one-marker assertion are unchanged — the located line is still the
  bullet that owns the item's `*(Item NNN)*` marker, never a file-wide icon
  scan.
- Nothing else in the file changes, and `docs/aide/progress.md` is **not**
  edited: the document is right and the test was stale.

### 3. AC5's test computes the narrower quantity, and by the wrong ordering

`tests/test_162_corpus_exercise_report.py::test_ac5_unexercised_reason_and_reason_modes_derived_from_specification`
as committed has two defects against the spec above. It must be re-derived so
that, for each unexercised rule:

- `strongest` is the edge rung **earliest in `EVIDENCE_RUNGS`**, taken with
  the index ordering the test already builds and then never uses
  (`min(rungs, key=strength.__getitem__)`), not Python's alphabetical `min`
  over the rung strings. The two disagree on this tree: alphabetically
  `"needs-real-data" < "structurally-unobservable" < "synthetic-demonstrable"`,
  while the declared strength order is `synthetic-demonstrable` (0),
  `needs-real-data` (1), `structurally-unobservable` (2). A rule carrying both
  a demonstrable and a needs-real-data edge would be scored
  `needs-real-data` — reading as reasoned where the production module
  correctly reports a hole.
- `expected_reason_modes` is **every** mode id carrying an edge that names the
  rule, per **D1** above, not the subset whose rung equals `strongest`. The
  narrower set agrees with production only because every unexercised rule's
  edges happen to sit at one rung on this tree, which is the coincidence D1
  says not to rely on.

Both are test-side only: `src/segfacet/traceability.py` already derives
`strongest_rung` by `rung_strength` index and collects `edge_modes` over every
naming edge (verified 2026-09-20), so no production change follows from this
correction.

### 4. `test_min_by_strength_matches_earliest_in_evidence_rungs` is dropped

That test names no acceptance criterion and no Testing-Strategy case, so
`aide scope` flags it under §6, and it earns neither. Its whole subject is
whether alphabetical `min` may stand in for strength order — a question that
exists only because of correction 3's defect and disappears with it. Its own
claim is also false on this tree (for `a = "synthetic-demonstrable"`,
`b = "needs-real-data"` its assertion is `False == True`), so it cannot be
promoted to a case as written. Delete it; no replacement, and no
Testing-Strategy entry is added for it. The property it was reaching for is
covered where it belongs — AC5's test now computes the index ordering
explicitly, and `demonstrable-rule-unexercised-is-a-hole` is the adversarial
case that fails if the ordering is ever inverted.

### What this correction does not change

No acceptance criterion AC1–AC12 is reworded, no assumption is withdrawn, and
no implementation step 1–10 is altered. `docs/aide/progress.md` is not edited,
no human gate is raised (A8 still holds — both conflicts are resolved from
committed state on this tree), and neither `src/segfacet/failure_modes.py` nor
`src/segfacet/heuristics/rule.py` is touched.
