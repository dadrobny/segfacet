<!-- aide-template: item 2 -->
# Item 172 — `UNUSED_OPERATOR_REASONS` entries validated

> **Created:** 2026-09-23 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-023.md`](../queue/queue-023.md) · Item 172
> **Objectives:** G2, G7
> **Suggested branch:** `aide/172-unused-operator-reasons-entries-validated`

---

## Description

Roadmap Stage 33 D0, third bullet. The `gap` entry in `insights.md` dated
2026-09-20 (item 162) records the problem.

`segfacet.traceability.UNUSED_OPERATOR_REASONS` is the one authored string in
item 162's exercise report. It maps a registered perturbation operator that no
`CASE_RECIPE` entry uses to the reason it is kept. `_build_exercise` reads it
only as `UNUSED_OPERATOR_REASONS.get(name, "")`, for operators it has already
found unused. That leaves two kinds of bad entry that nothing reports:

1. **An unregistered name.** The operator was renamed or deleted, and its
   entry stayed behind. `_build_exercise` iterates only registered names, so
   it never looks the entry up.
2. **A registered operator that is used.** Some `CASE_RECIPE` entry uses the
   operator, so the recorded reason ("this operator is deliberately unused")
   is false. `_build_exercise` records the operator as `used` and never reads
   the entry.

Item 162's Assumption A4 said both would be reported as conflicts. The code
does not do that. The mapping is empty on this tree, so nothing is wrong
today. Item 175 re-authors `crop_at_border` and may take the current
translate-and-clip operator out of use. That would add the mapping's first
entry, so this check has to exist before item 175 lands.

**Deliverable.** A public function,
`segfacet.traceability.operator_reason_conflicts()`, that returns one conflict
message for each entry of either kind. Each message names the operator. A
standing test asserts that the function returns nothing on the live tree, so
the first commit that adds a bad entry fails the suite.

**Not in scope.** The generated traceability matrix, its JSON and Markdown
artifacts, and `SCHEMA_VERSION` do not change (Decision D1). No entry is added
to `UNUSED_OPERATOR_REASONS`. `_build_exercise`'s records and holes do not
change. No operator, corpus case or rule changes.

## Acceptance Criteria

- [ ] **AC1: An entry for an unregistered name is reported.** Set
  `traceability.UNUSED_OPERATOR_REASONS` to a single entry whose key is a name
  absent from `perturbation_names()`. `operator_reason_conflicts()` then
  returns a one-element tuple, and that element contains the name.
- [ ] **AC2: An entry for a used operator is reported.** Take an operator
  name from the live `CASE_RECIPE` and set the mapping to a single entry for
  it. `operator_reason_conflicts()` then returns a one-element tuple, and
  that element contains the name.
- [ ] **AC3: An entry for a registered, unused operator is not reported.**
  Register a stub operator that no `CASE_RECIPE` entry uses, and set the
  mapping to a single entry for it. `operator_reason_conflicts()` then
  returns `()`.
- [ ] **AC4: The live tree reports no conflict.** With nothing patched,
  `operator_reason_conflicts()` returns `()`.

AC3 is written for item 175: its legitimate first entry must pass the check.
AC4 is the standing check that fails the suite on the first bad entry. It
does not assert that the mapping is empty, so it stays true after item 175
adds a legitimate entry.

## Assumptions

- **A1 (default, clarify=assume):** "The module reports" means a public
  function in `segfacet.traceability` that returns conflict messages as a
  `Tuple[str, ...]`. That is the shape the two existing checks already use
  (`segfacet.catalogue.path_classification_conflicts()` and
  `segfacet.failure_modes.specification_conflicts()`). "The check" in the
  queue's *Testable* line is AC4's standing test. The function is not folded
  into `build_matrix` (Decision D1).
- **A2 (default):** "Used" means what `_build_exercise` means by it: named as
  the `perturbation` of at least one `segfacet.synth.corpus.CASE_RECIPE`
  entry. "Registered" means listed by
  `segfacet.synth.perturbation.perturbation_names()`. The intensity corpus
  does not count toward "used" here, because `_build_exercise` does not count
  it either. One definition is shared between the two (Implementation
  Step 1), so they cannot drift.
- **A3 (default):** The function takes no argument. It reads the module
  attribute `UNUSED_OPERATOR_REASONS` when called, not when it is defined, so
  `monkeypatch.setattr(traceability, "UNUSED_OPERATOR_REASONS", ...)` reaches
  it. That is how item 162's tests already seed the mapping, and how this
  item's tests seed it.
- **A4 (default):** Each conflicting entry yields exactly one message. The
  output is sorted by operator name, so it is deterministic. The message
  wording is not pinned beyond containing the operator name. The builder
  should say which of the two kinds of conflict it is, and for a used
  operator, name the cases that use it.
- **A5 (measured 2026-09-23, on `aide/queue-023` after items 170 and 171
  merged):** `UNUSED_OPERATOR_REASONS` is `{}`. Every name that
  `perturbation_names()` returns is used by `CASE_RECIPE`. Items 170 and 171
  touched neither `src/segfacet/traceability.py` nor the synth registry.

## Implementation Steps

All changes are in `src/segfacet/traceability.py`. No dependency is added.

1. **Share the "used" definition.** Move the `cases_by_operator` loop out of
   `_build_exercise` into a private helper, for example
   `_cases_by_operator() -> Dict[str, list]`. It imports `CASE_RECIPE` from
   `segfacet.synth.corpus` inside the function body (house style). Importing
   it also imports `segfacet.synth`, whose `__init__` imports every module
   that registers an operator, so the registry is complete before anything
   reads it. `_build_exercise` calls the helper. Its output does not change.
2. **Add `operator_reason_conflicts() -> Tuple[str, ...]`.** Read
   `UNUSED_OPERATOR_REASONS` as a module global at call time. Read
   `perturbation_names()` and step 1's helper. For each entry, sorted by key:
   - if the key is not a registered name, append a message that names it as
     not registered;
   - otherwise, if the key has cases in step 1's helper, append a message
     that names the operator as used and lists those case ids.

   An entry for a registered, unused operator adds nothing. Put the heavy
   imports inside the function body, as `_build_exercise` does.
3. **Export the function.** Add `"operator_reason_conflicts"` to `__all__`.
   Add one sentence to the module docstring's item-162 paragraph, and to the
   comment above `UNUSED_OPERATOR_REASONS`, saying that entries are
   validated by this function (item 172). Do not change `_NOTE` or anything
   else that reaches the generated artifacts. `test_162`'s AC9 and AC10
   compare those artifacts byte for byte.

## Authorised paths

**May change:**

- `src/segfacet/traceability.py` — the new function, the shared helper for
  "used", `__all__`, and the docstring and comment
- `tests/test_172_unused_operator_reasons_validated.py` — the new test module

**Asserts against:**

- `src/segfacet/synth/corpus.py` — AC2 takes its used operator from the live
  `CASE_RECIPE`, and AC4 holds the mapping consistent with it
- `src/segfacet/synth/perturbation.py` — AC1 and AC4 read the live registry
  through `perturbation_names()`

## Testing Strategy

The test module is `tests/test_172_unused_operator_reasons_validated.py`,
with one test per AC (AC1–AC4).

- Seed the mapping with
  `monkeypatch.setattr(traceability, "UNUSED_OPERATOR_REASONS", {...})`.
  Never mutate the real dict.
- AC1's name is built by the test, and the test asserts that
  `perturbation_names()` does not contain it before relying on it.
- AC2 derives its operator from the live `CASE_RECIPE`, for example the
  sorted first `entry.perturbation`. It never uses a literal operator name,
  because item 175 may take any named operator out of use (see item 171's
  class of literal negative controls).
- AC3 registers its stub the way `test_162`'s
  `_isolated_perturbation_registry` fixture does: snapshot `_PERTURBATIONS`,
  register, and restore in `finally`. It asserts that `CASE_RECIPE` does not
  use the stub's name. Copy that fixture into the new module. Do not import
  it across test modules.
- None of these tests calls `build_matrix()`. The function does not depend
  on the matrix, so the slow regeneration is not needed.

The one adversarial case:

- **`both-kinds-at-once`**: seed one unregistered name, one used operator and
  one registered, unused stub together. Exactly two conflicts come back, one
  containing each bad name, and neither contains the stub's name. This guards
  an implementation that stops at the first conflict. It also guards one
  that decides per mapping instead of per entry, and so reports the
  legitimate entry, or drops a bad one, when the entries are mixed.

**Existing tests to reconcile:** none. This item changes no default and no
behaviour that any existing test pins. `test_162`'s
`matrix_recorded_unused_operator` fixture seeds a reason for a registered,
unused stub, which is a legitimate entry. It goes through `build_matrix`,
which does not call the new function, so the fixture is unaffected. A
`tests/` grep for `UNUSED_OPERATOR_REASONS` finds only `test_162`.

## Dependencies

None.

**Downstream:** this item reads nothing that items 170 and 171 produced
(both are merged into `aide/queue-023`; A5). item 175 (`crop_at_border` as a crop of the volume) may add
the first `UNUSED_OPERATOR_REASONS` entry, and AC4 holds that entry to this
check. Item 175's spec should list this item under its own Dependencies,
because this item's Asserts-against list includes
`src/segfacet/synth/corpus.py`.

## Decisions & Trade-offs

- **D1 (spec-author, 2026-09-23): a standalone check plus a standing test,
  not a new field in the generated matrix.** The matrix does not render
  either bad entry wrongly:
  - a used operator is shown as `used` whatever the mapping says;
  - an unregistered name has no row at all.

  The mapping is what is wrong, and the defect enters on the commit that
  edits it. The standing AC4 test fails that commit. Reporting the conflict
  inside the matrix would add a serialised field, regenerate both committed
  traceability artifacts, and bump `SCHEMA_VERSION`. `test_149` pins
  `SCHEMA_VERSION` at `"1.2"`. Nothing in this batch needs that extra work.
- **Left open:** should `build_matrix` fold these conflicts into
  `directions.operator_exercise` (setting `complete` to false), or into
  `conformance.conformant`? That would put them in the generated artifact
  and not only in the suite. It waits for a consumer that reads the matrix
  and needs them there. No item in queue-023 is such a consumer.
- **D2 (builder, 2026-09-23): message wording carries the operator name via
  `repr()` and is not otherwise pinned.** Each message starts with
  `UNUSED_OPERATOR_REASONS entry 'name' ...` so a substring match on the bare
  name always succeeds (AC1/AC2), and a used-operator message lists the
  offending `CASE_RECIPE` case ids, sorted and comma-joined (A4).
- **D3 (builder, 2026-09-23): `_cases_by_operator()` is the shared helper
  named in Implementation Step 1**, returning `Dict[str, list]` exactly as
  `_build_exercise`'s former inline loop built it; `_build_exercise` now
  calls it instead of rebuilding the dict inline, and its output is
  unchanged.
