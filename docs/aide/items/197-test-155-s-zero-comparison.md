<!-- aide-template: item 3 -->
# Item 197 — `test_155`'s zero-comparison scan covers truthiness and ordering

> **Created:** 2026-09-29 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (maintenance)
> **Queue:** [`../queue/queue-026.md`](../queue/queue-026.md) · Item 197
> **Objectives:** G7
> **Suggested branch:** `aide/197-test-155-s-zero-comparison`

---

## Description

Item 155 retired "`failure_mode` is 0" as the test for "clean control". A
corpus case is classified by its recorded `kind`, read through
`segfacet.synth.perturbation.corpus_case_kind`. `tests/test_155_corpus_case_kind.py`
keeps the old test from coming back with an AST scanner,
`_zero_comparisons(source, filename)`. Its AC12 test runs the scanner over
every `*.py` under `src/segfacet` and `tests` and asserts that it reports
nothing.

The scanner reports shapes against a **tracked access**: `x["failure_mode"]`,
`x.get("failure_mode")`, or a local name bound from either in the same scope.
After item 184 it reports an `Eq`/`NotEq`/`Is`/`IsNot` comparison against a
**zero sentinel** (the literal `0`, or a `CLEAN_CONTROL_MODE`/`_CLEAN_MODE_ID`
name or attribute), in any pair of a chained comparison; membership in a
`Tuple`/`Set`/`List` literal holding a zero sentinel; `not <tracked access>`;
and `bool(<tracked access>)`.

Two shapes express the same test and still pass the scan (`insights.md`,
entry 2026-09-25-31b7, item 184):

- **Bare truthiness in a test position.** A tracked access that is itself the
  test of an `if`, a `while` or a ternary, an operand of `and`/`or`, or a
  comprehension `if`.
- **Ordering against the zero boundary.** `x["failure_mode"] > 0`, `>= 1`,
  and their mirrors.

One live hit exists. `tests/test_138_traceability_matrix.py`'s liveness block
in `test_ac31_measured_findings_claim_matches_the_live_pipeline_firing_set` selects a pipeline case with
`case.get("detection") == "pipeline" and case.get("failure_mode")`. That reads
"`failure_mode` truthy means a failure case", the double meaning item 155
retired.

This item widens `_zero_comparisons` to report both shapes, and rewrites the
live hit to read `corpus_case_kind`. It keeps the scopes, the tracked-access
rule, the zero-sentinel rule, the `assert` exemption, the `case_kind`
exemption and every shape item 184 added as they are.

**Not in scope:**

- Any change under `src/segfacet/`. The widened scan finds nothing there (A3).
- A tracked access used as a value (`return x["failure_mode"]`, an argument, an
  assignment). Only a test position is a truthiness test.
- Ordering against a named container or any bound other than 0 and 1.

## Acceptance Criteria

Each of AC1–AC7 calls `_zero_comparisons(snippet, "synthetic.py")` from
`tests/test_155_corpus_case_kind.py` on the exact snippet given. "Reported at
line 2" means that the returned list equals `[("synthetic.py", 2)]`. The
scanner on the base returns `[]` for all seven snippets, so each test fails
before the change.

- [ ] **AC1: A tracked access as an `if` test is reported.** The snippet
  `"def f(case):\n    if case.get('failure_mode'):\n        pass\n"` is
  reported at line 2.
- [ ] **AC2: A tracked access as a `while` test is reported.** The snippet
  `"def f(case):\n    while case['failure_mode']:\n        break\n"` is
  reported at line 2.
- [ ] **AC3: A tracked access as a ternary test is reported.** The snippet
  `"def f(case):\n    x = 1 if case.get('failure_mode') else 2\n"` is
  reported at line 2.
- [ ] **AC4: A tracked access as an `and`/`or` operand is reported.** The
  snippet
  `"def f(case):\n    ok = case['detection'] == 'pipeline' and case.get('failure_mode')\n"`
  is reported at line 2.
- [ ] **AC5: A tracked access as a comprehension `if` is reported.** The
  snippet `"def f(cs):\n    xs = [c for c in cs if c['failure_mode']]\n"` is
  reported at line 2.
- [ ] **AC6: `> 0` of a tracked access is reported.** The snippet
  `"def f(case):\n    if case['failure_mode'] > 0:\n        pass\n"` is
  reported at line 2.
- [ ] **AC7: `>= 1` of a tracked access is reported.** The snippet
  `"def f(case):\n    if case['failure_mode'] >= 1:\n        pass\n"` is
  reported at line 2.
- [ ] **AC8: The live tree reports nothing.** Running the widened
  `_zero_comparisons` over every `*.py` under `src/segfacet` and `tests`
  returns no violation. The test is the existing
  `tests/test_155_corpus_case_kind.py::test_ac12_no_tree_wide_zero_comparison_of_failure_mode_remains`.
  It must pass unchanged, and no new test is written for this AC. It fails on
  the widened scan until `test_138`'s live hit is rewritten.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

- **A1: What "test position" means, and how often it is reported.** A tracked
  access is reported when it is exactly one of these expressions:
  `If.test`, `While.test`, `IfExp.test`, an element of `BoolOp.values`, or an
  element of `comprehension.ifs`. Each such tracked expression is one
  violation, reported at its own `lineno`. An `elif` is a nested `If`, so it is
  covered. A test that is a `Compare`, a `not` or a `bool(...)` call is not
  itself a tracked access, so today's branches keep reporting it once and the
  new branch does not report it again. A tracked expression inside an `assert`
  is exempt, as every other shape is.
- **A2: What "ordering against 0" matches.** An `ast.Lt`/`LtE`/`Gt`/`GtE`
  pair of a `Compare` (any pair of a chain, as item 184's loop reads them) is
  reported when it splits 0 from the positive mode ids. With the tracked
  access on the left, that is `> Z`, `<= Z`, `>= 1` and `< 1`, where `Z` is a
  zero sentinel by the existing `_is_zero_sentinel` and `1` is the int literal
  1 (not `True`). With the tracked access on the right, the mirrors are
  `Z < x`, `Z >= x`, `1 <= x` and `1 > x`. `>= 0`, `< 0`, `> 1` and every other
  bound are not reported: none of them tests "is this a clean control". A
  matching pair sets item 184's `matched` flag, so a `Compare` is still
  reported once however many pairs match.
- **A3: The live tree has exactly one hit under the widened scan.** Measured
  2026-09-29 on this branch's base (`aide/queue-026` after item 196) with a
  scratch copy of the A1 and A2 rules, reusing `test_155`'s
  `_is_failure_mode_access`, `_is_zero_sentinel`, `_EXEMPT_FILE`,
  `_EXEMPT_FUNCTION` and `_iter_scanned_files`. It found one truthiness hit,
  `tests/test_138_traceability_matrix.py` line 2224, and nothing else in
  `src/segfacet` or `tests`. It found no ordering hit, even with the broader
  rule "any ordering against 0 or 1". The builder hands back if AC8 fails on
  something other than that line.
- **A4: The rewrite of the live hit.** The liveness block's generator becomes
  `case.get("detection") == "pipeline" and perturbation_module.corpus_case_kind(case) == perturbation_module.CASE_KIND_FAILURE`,
  with `import segfacet.synth.perturbation as perturbation_module` in the test
  body. That is the form the same module's
  `matrix_unregistered_designated_rule` fixture already uses. It selects the
  same case: `case_kind` returns `failure` exactly when `failure_mode` is
  non-zero, and `test_155`'s AC7 pins every committed case's `kind` to
  `case_kind(failure_mode, condition)`. Measured 2026-09-29: both predicates
  select the same 9 pipeline cases, and the first in sorted order is
  `fragment`. `!= CASE_KIND_CLEAN_CONTROL` is not an equivalent rewrite,
  because it admits condition cases.
- **A5: No dependency pin.** Item 155, which wrote the scanner, and item 184,
  which last widened it, are both merged. This item reads the scanner as it
  stands on the base, so there is no interface pin to re-check.

## Implementation Steps

Nothing under `source_dir` changes, and no dependency is added.

1. In `tests/test_155_corpus_case_kind.py`'s `_zero_comparisons`, inside
   `scan_scope`'s per-node loop and after the existing `exempt_test_ids`
   check, collect the test-position expressions of the node (A1):
   `[node.test]` for `ast.If`/`ast.While`/`ast.IfExp`, `node.values` for
   `ast.BoolOp`, and `node.ifs` for `ast.comprehension`. Append
   `(filename, expr.lineno)` for each one where `is_tracked(expr)` holds and
   `id(expr)` is not in `exempt_test_ids`. This branch is separate from the
   existing `Compare`/`UnaryOp`/`Call` chain, because an `If` is none of
   those. Reuse the `is_tracked` closure.
2. In the same function's `Compare` pair loop, add an `ast.Lt`/`LtE`/`Gt`/`GtE`
   branch that sets `matched` per A2. Reuse `_is_zero_sentinel` for the 0 side.
   The literal-1 check excludes `bool`, as `_is_zero_sentinel` does for 0.
3. Update the scanner's description in the module docstring (the AC12/AC13
   paragraph) and in `_zero_comparisons`'s docstring. Name the two added
   shapes and cite item 197.
4. In `tests/test_138_traceability_matrix.py`, rewrite the liveness block's
   case selection per A4. Change nothing else in that test.

## Authorised paths

**May change:**

- `tests/test_155_corpus_case_kind.py` — the widened `_zero_comparisons` and its two docstrings
- `tests/test_138_traceability_matrix.py` — the live hit rewritten to read `corpus_case_kind`
- `tests/test_197_zero_comparison_truthiness_ordering.py` — the AC1–AC7 tests and the named adversarial cases

**Asserts against:**

- `src/segfacet/**` — AC8: the existing `test_155` AC12 runs the widened scan over every source file and requires no violation. It also scans every file under `tests/`, which is not listed here because this item changes three files there.

## Testing Strategy

New module `tests/test_197_zero_comparison_truthiness_ordering.py`, with one
test each for AC1–AC7. It imports the scanner from the module that owns it,
`import test_155_corpus_case_kind as t155`, as
`tests/test_184_zero_comparison_shapes.py` does. It calls
`t155._zero_comparisons(snippet, "synthetic.py")` and does not copy the
scanner. AC8's test is the existing `test_155` AC12.

Adversarial cases. Write these, as one parametrised test or several, and no
others. Each gives the snippet body inside `def f(case):` (or `def f(cs):`
where it iterates) and the exact expected count:

- `local-name-truthiness`: `m = case.get('failure_mode')` then `if m: pass` is
  reported once. This guards a truthiness branch that calls
  `_is_failure_mode_access` directly instead of `is_tracked`, and so misses the
  local-name form.
- `value-use-not-reported`: `return case.get('failure_mode')` is not reported.
  This guards a branch that reports every tracked access rather than one in a
  test position.
- `assert-exempts-truthiness`: `assert case['detection'] and case['failure_mode']`
  is not reported. This guards a truthiness branch that skips the
  `exempt_test_ids` check on the collected expression.
- `mirrored-ordering`: `if 0 < case['failure_mode']: pass` is reported once.
  This guards an ordering branch that handles the tracked access on the left
  only.
- `less-than-one`: `if case['failure_mode'] < 1: pass` is reported once. This
  guards an ordering branch that handles only the "is a failure case"
  direction.
- `named-sentinel-ordering`: `if case['failure_mode'] > CLEAN_CONTROL_MODE: pass`
  is reported once. This guards an ordering branch that tests for the literal
  0 instead of calling `_is_zero_sentinel`.
- `ordering-off-boundary`: `if case['failure_mode'] > 1: pass` is not
  reported. This guards a rule that reports every ordering against a small
  literal, which would forbid a legitimate "mode 2 or above" filter.
- `chained-ordering`: `if 0 < case['failure_mode'] < 99: pass` is reported
  once. This guards an ordering branch that reads only `node.left` and
  `comparators[0]`, or that reports once per matching pair.

**Existing tests to reconcile:** none need editing. `test_155`'s
`test_ac13_scan_detects_each_forbidden_shape` (seven snippets),
`test_ac13_scan_exempts_case_kind_body_in_perturbation_module`, and
`tests/test_184_zero_comparison_shapes.py` (AC1–AC3 and five adversarial
cases) must stay green unchanged. Under A1 none of their snippets has a
tracked access as a bare test, and none has an ordering comparison, so their
exact counts still hold. A grep made 2026-09-29 found no other caller of
`_zero_comparisons`. `test_138`'s `test_ac31_measured_findings_claim_matches_the_live_pipeline_firing_set` must also stay green; A4
keeps its selected case.

## Validation

The rewrite in `test_138` sits inline in a test body, so no test can call it.
Confirm that it selects the same case as the old predicate. Run once on the
branch:

```
.venv/bin/python -c "from segfacet.synth.corpus import load_manifest as L; from segfacet.synth.perturbation import corpus_case_kind as k, CASE_KIND_FAILURE as F; c={x['case_id']:x for x in L()['cases']}; a=[i for i,x in sorted(c.items()) if x.get('detection')=='pipeline' and x.get('failure_mode')]; b=[i for i,x in sorted(c.items()) if x.get('detection')=='pipeline' and k(x)==F]; print(a[0], b[0], a==b)"
```

It prints the same case id twice, followed by `True`. The value measured on
2026-09-29 was `fragment fragment True`. Then read the diff of
`tests/test_138_traceability_matrix.py` and confirm that its new predicate is
the `b` predicate above.

## Dependencies

None. Item 155, which wrote the scanner, and item 184, which last widened it,
are both merged.

## Decisions & Trade-offs

- **Ordering normalised to "tracked op bound".** The scanner flips the operator
  when the tracked access is on the right, then matches `>`/`<=` against a zero
  sentinel and `>=`/`<` against the int literal 1 (A2), in one branch.

- **No new test for "`test_138`'s selection is unchanged".** The queue names
  that claim as testable. The selection is inline in a test body, so a test
  could only restate both predicates, and `test_155`'s AC7 already pins the
  fact that makes them agree (A4). The Validation command measures it once
  instead.

- **2026-09-29 review fix.** The `_zero_comparisons` function docstring in `tests/test_155_corpus_case_kind.py` now names the two shapes item 197 added (truthiness test positions; zero-vs-positive ordering), as Implementation Step 3 requires. Docstring only, no logic change.
