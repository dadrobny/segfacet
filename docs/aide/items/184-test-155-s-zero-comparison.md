<!-- aide-template: item 2 -->
# Item 184 — `test_155`'s zero-comparison scan covers every comparison shape

> **Created:** 2026-09-25 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (maintenance)
> **Queue:** [`../queue/queue-024.md`](../queue/queue-024.md) · Item 184
> **Objectives:** G7
> **Suggested branch:** `aide/184-test-155-s-zero-comparison`

---

## Description

Item 155 retired `failure_mode == 0` as the test for "clean control". A corpus
case is now classified by its recorded `kind`, read through
`segfacet.synth.perturbation.corpus_case_kind`. To keep the old test from
coming back, `tests/test_155_corpus_case_kind.py` ships an AST scanner,
`_zero_comparisons(source, filename)`. Its AC12 test runs the scanner over every
`*.py` under `src/segfacet` and `tests` and asserts it reports nothing.

The scanner reports two shapes against a **tracked access**. A tracked access
is `x["failure_mode"]`, `x.get("failure_mode")`, or a local name bound from
either in the same scope. The two shapes are:

- a comparison with **exactly one operator** (`Eq`, `NotEq`, `Is` or `IsNot`)
  whose other side is a **zero sentinel**: the literal `0`, or a
  `CLEAN_CONTROL_MODE`/`_CLEAN_MODE_ID` name or attribute;
- `not <tracked access>`.

Three other shapes express the same test and pass the scan undetected
(`insights.md`, gap entry of item 155, 2026-09-16):

- **Membership.** `case["failure_mode"] in (0,)` or `in {0}`, and `not in`.
- **Chained comparison.** `lo <= case["failure_mode"] == 0`. The scanner
  skips every `Compare` with more than one operator.
- **`bool(...)` truthiness.** `bool(case.get("failure_mode"))`.

This item widens `_zero_comparisons` to report all three. It keeps the scopes,
the tracked-access rule, the zero-sentinel rule, the `assert` exemption and the
`case_kind` exemption as they are.

**Not in scope:**

- Any change under `src/segfacet/`. The widened scan reports nothing on the
  live tree (A2), so no production code moves.
- Bare truthiness in a test position (`if case.get("failure_mode"):`, an
  `and`/`or` operand), and ordering comparisons against 0 (`> 0`). The queue
  names neither. See **Left open**.
- Membership against a named container (`in _CLEAN_MODES`). The scanner cannot
  resolve a name's value.

## Acceptance Criteria

Each of AC1–AC3 calls `_zero_comparisons(snippet, "synthetic.py")` from
`tests/test_155_corpus_case_kind.py` on the exact snippet given. "Reported at
line 2" means the returned list equals `[("synthetic.py", 2)]`. The shipped
scanner returns `[]` for all three snippets, so each test fails before the
change.

- [ ] **AC1: A membership test against a zero literal is reported.** The snippet
  `"def f(case):\n    if case['failure_mode'] in (0,):\n        pass\n"`
  is reported at line 2.
- [ ] **AC2: A chained comparison with a zero comparison in it is reported.**
  The snippet
  `"def f(case, lo):\n    if lo <= case['failure_mode'] == 0:\n        pass\n"`
  is reported at line 2.
- [ ] **AC3: `bool(...)` truthiness of a tracked access is reported.** The
  snippet `"def f(case):\n    flag = bool(case.get('failure_mode'))\n"` is
  reported at line 2.
- [ ] **AC4: The live tree reports nothing.** Running the widened
  `_zero_comparisons` over every `*.py` under `src/segfacet` and `tests`
  returns no violation. The test is the existing
  `tests/test_155_corpus_case_kind.py::test_ac12_no_tree_wide_zero_comparison_of_failure_mode_remains`.
  It must pass unchanged, and no new test is written for this AC.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

- **A1: What each new shape matches.** The queue line names the shapes by
  example only. The rule taken here:
  - **Membership.** A `Compare` pair whose operator is `In` or `NotIn`, whose
    left side is a tracked access, and whose right side is a `Tuple`, `Set` or
    `List` literal with at least one zero-sentinel element (by the existing
    `_is_zero_sentinel`). `in (0, 3)` is reported, because it still treats 0
    as one identity. `in (1, 2)` is not reported.
  - **Chained.** The pair rules apply to every adjacent pair
    `(operands[i], ops[i], operands[i+1])` of a `Compare`, whatever its
    length. A `Compare` is reported once if any of its pairs matches, which
    keeps a single-op comparison at one violation, as today.
  - **`bool(...)`.** A `Call` whose `func` is the bare name `bool`, with
    exactly one positional argument that is a tracked access.
    `not bool(case["failure_mode"])` is one violation (the `bool` call). The
    `not` operand is a call, not a tracked access.
- **A2: The live tree is clean under the widened scan.** Measured 2026-09-25 on
  this branch's base (`aide/queue-024` after items 182 and 183) with a scratch
  copy of the A1 rule. It reuses `test_155`'s `_is_failure_mode_access`,
  `_is_zero_sentinel` and `_iter_scanned_files`. Over all 3 shapes it found 0
  hits in `src/segfacet` and 0 in `tests`. Item 182's new
  `catalogue._scan_synth_rule_mode_map` classifies each case with
  `corpus_case_kind(case) != CASE_KIND_FAILURE` and reads `case["failure_mode"]`
  only as a value, so the scan does not report it. The builder hands back if
  AC4 fails on the real change.
- **A3: No dependency pin.** Item 155, which wrote the scanner, and item 182,
  whose code the scan now reads, are both merged. This item reads the scanner
  as it stands on the base, so there is no interface pin to re-check.

## Implementation Steps

All changes are in `tests/test_155_corpus_case_kind.py`. Nothing under
`source_dir` changes, and no dependency is added.

1. In `_zero_comparisons`'s inner `scan_scope`, replace the
   `isinstance(node, ast.Compare) and len(node.ops) == 1` branch with a loop over
   the adjacent pairs of `[node.left] + node.comparators` and `node.ops`. A
   pair matches when:
   - its operator is `Eq`/`NotEq`/`Is`/`IsNot`, with a tracked access on one
     side and a zero sentinel on the other (today's rule), or
   - its operator is `In`/`NotIn`, with a tracked access on the left and a
     `Tuple`/`Set`/`List` literal on the right whose `elts` include a zero
     sentinel.

   Append `(filename, node.lineno)` once per `Compare` when any pair matches.
   Reuse the existing `is_tracked` closure and `_is_zero_sentinel`.
2. Add one branch for `ast.Call` with `func` an `ast.Name` whose `id` is
   `"bool"`, one positional argument, and `is_tracked(args[0])`. Put it after
   the existing `id(node) in exempt_test_ids` check, as the other branches
   are, so the `assert` exemption covers it.
3. Update the scanner's description in the module docstring (the AC12/AC13
   paragraph) and in `_zero_comparisons`'s docstring. Name the three added
   shapes and cite item 184.

## Authorised paths

**May change:**

- `tests/test_155_corpus_case_kind.py` — the widened `_zero_comparisons` and its two docstrings
- `tests/test_184_zero_comparison_shapes.py` — the AC1–AC3 tests and the named adversarial cases

**Asserts against:**

- `src/segfacet/**` — AC4: the existing `test_155` AC12 runs the widened scan over every source file and requires no violation. It also scans every file under `tests/`, which is not listed here because this item changes two files there.

## Testing Strategy

New module `tests/test_184_zero_comparison_shapes.py`, with one test each for
AC1, AC2 and AC3. It imports the scanner from the test module that owns it,
`import test_155_corpus_case_kind as t155`, as
`tests/test_159_prerequisite_test_and_import_defects.py` imports
`test_143_s_axis_correction`. It calls `t155._zero_comparisons(snippet,
"synthetic.py")` and does not copy the scanner. AC4's test is the existing
`test_155` AC12 (see AC4).

Adversarial cases. Write these, as one parametrised test or several, and no
others. Each gives the snippet body inside `def f(case):` and the exact
expected result:

- `not-in-membership`: `if case['failure_mode'] not in (0,): pass` is
  reported once. This guards a membership branch that checks `ast.In` only,
  which would miss the "is a failure case" form of the test.
- `list-literal-membership`: `if case['failure_mode'] in [0]: pass` is reported
  once. This guards a membership branch that accepts `Tuple`/`Set` containers
  only.
- `membership-without-zero`: `if case['failure_mode'] in (1, 2): pass` is not
  reported. This guards a membership branch that reports every membership test
  of the access, whatever the container holds.
- `local-name-membership`: `m = case['failure_mode']` then `if m in {0}: pass`
  is reported once. This guards a new branch that calls
  `_is_failure_mode_access` directly instead of `is_tracked`, and so misses the
  local-name form the other shapes already catch.
- `assert-exempts-new-shapes`: `assert case['failure_mode'] in (0,)` is not
  reported. This guards a new branch placed before the `exempt_test_ids`
  check.

**Existing tests to reconcile:** none need editing. `test_155`'s
`test_ac13_scan_detects_each_forbidden_shape` (seven snippets) and
`test_ac13_scan_exempts_case_kind_body_in_perturbation_module` must stay green
unchanged. A1 keeps every single-op comparison at one violation, so their
exact counts still hold. A grep made 2026-09-25 found no other caller of
`_zero_comparisons`.

## Dependencies

None. Item 155, which wrote the scanner, and item 182, whose catalogue code
the scan reads, are both merged.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** bare truthiness of a tracked access in a test position
  (`if`/`while`/ternary test, an `and`/`or` operand, a comprehension `if`), and
  ordering comparisons against 0. The queue names neither. Bare truthiness has
  one live hit: `tests/test_138_traceability_matrix.py` line 2080,
  `... and case.get("failure_mode")`. Scanning for it would also mean changing
  that test to use `corpus_case_kind`. Recorded in `insights.md` (item 184,
  2026-09-25).
