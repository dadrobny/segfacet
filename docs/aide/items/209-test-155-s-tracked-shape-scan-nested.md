<!-- aide-template: item 3 -->
# Item 209 — `test_155`'s tracked-shape scan: nested scopes and value defaults

> **Created:** 2026-10-03 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 27 — Feature Schema Taxonomy & Coordinate System (maintenance)
> **Queue:** [`../queue/queue-028.md`](../queue/queue-028.md) · Item 209
> **Objectives:** G7
> **Suggested branch:** `aide/209-test-155-s-tracked-shape-scan-nested`

---

## Description

`tests/test_155_corpus_case_kind.py` keeps "`failure_mode` is 0 means clean
control" from coming back (item 155). Its scanner `_zero_comparisons(source,
filename)` reports forbidden shapes against a **tracked access** (a
`failure_mode` subscript or `.get`, or a local name bound from one), and its
AC12 test runs the scanner over every `*.py` under `src/segfacet` and `tests`
and requires no violation. Items 184 and 197 widened the shapes it reports.

Two `insights.md` entries from item 197 (both 2026-09-29) record four defects
in it:

- **Nested scopes are scanned twice.** `scan_scope` uses `ast.walk`, which
  enters a nested `def`. The final loop then finds that `def` with
  `ast.walk(tree)` and scans its body again. So a violation inside a nested
  function, or inside a method of a class nested in a function, is reported
  twice. Measured on the base: `def f(c): def g(d): if d['failure_mode'] == 0`
  gives two violations at line 3.
- **Three shapes are missed.** A walrus test, `if (m := c['failure_mode']):`.
  A `match` guard, `case 1 if c['failure_mode']:`. And a float bound,
  `c['failure_mode'] >= 1.0`. The base reports none of the three.
- **A value default is reported.** The `and`/`or`-operand rule (item 197 A1)
  reports `m = c.get("failure_mode") or 0`. That expression maps a missing mode
  to 0 and leaves every int mode id as it is, so it is not a truthiness test.
  A legitimate default written this way would fail AC12.

This item fixes all four in `_zero_comparisons`. The tracked-access rule, the
zero-sentinel rule, the `assert` exemption, the `case_kind` exemption and every
shape items 184 and 197 report are unchanged.

**Not in scope:**

- Any change under `src/segfacet/`. A scratch copy of the A1–A5 rules finds
  nothing there (A6).
- A `match` statement whose **subject** is a tracked access and whose pattern
  is `0` (`match c['failure_mode']: case 0:`). The queue names the guard only.
  This is left open below.
- A walrus target as a newly bound local name (`if (m := c['failure_mode']) is
  not None: ... if m:`). Only the walrus expression itself is tracked.

## Acceptance Criteria

Each of AC1–AC5 calls `_zero_comparisons(snippet, "synthetic.py")` from
`tests/test_155_corpus_case_kind.py` on the exact snippet given. "Reported at
line N" means that the returned list equals `[("synthetic.py", N)]`. The
scanner on the base returns a different list for each of the five snippets
(two entries for AC1, `[]` for AC2–AC4, one entry for AC5), so each test fails
before the change.

- [ ] **AC1: A violation in a nested function is reported once.** The snippet
  `"def f(c):\n    def g(d):\n        if d['failure_mode'] == 0:\n            pass\n"`
  is reported at line 3.
- [ ] **AC2: A walrus test is reported.** The snippet
  `"def f(c):\n    if (m := c['failure_mode']):\n        pass\n"` is reported
  at line 2.
- [ ] **AC3: A `match` guard is reported.** The snippet
  `"def f(c, x):\n    match x:\n        case 1 if c['failure_mode']:\n            pass\n"`
  is reported at line 3.
- [ ] **AC4: `>= 1.0` is reported.** The snippet
  `"def f(c):\n    if c['failure_mode'] >= 1.0:\n        pass\n"` is reported
  at line 2.
- [ ] **AC5: A zero value default is not reported.** The snippet
  `"def f(c):\n    x = c.get('failure_mode') or 0\n"` returns `[]`.
- [ ] **AC6: The live tree reports nothing.** Running the changed
  `_zero_comparisons` over every `*.py` under `src/segfacet` and `tests`
  returns no violation. The test is the existing
  `tests/test_155_corpus_case_kind.py::test_ac12_no_tree_wide_zero_comparison_of_failure_mode_remains`.
  It must pass unchanged, and no new test is written for this AC.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

- **A1: What a scope is.** A scope is the module body or one function body
  (`FunctionDef`/`AsyncFunctionDef`). A scope is walked node by node, but the
  walk does not enter a nested function definition: it records the `def` and
  scans its body afterwards as a scope of its own. That holds at any depth, so
  a method of a class nested inside a function is also its own scope. A class
  body is not a scope: its statements belong to the enclosing scope, and its
  methods are nested definitions. A `lambda` is not a scope either, so its body
  stays in the enclosing scope as it does today. The exempt `case_kind` body in
  `src/segfacet/synth/perturbation.py` is skipped where it is found, as today.
  Each node is visited by exactly one scope, so each violation is reported
  once.
  *Re-checked 2026-10-05 against `aide/queue-028` at `3f64294`: agrees.
  `scan_scope(stmts)` still walks each statement with `ast.walk` in both
  passes, the module body is still filtered of `FunctionDef`/`AsyncFunctionDef`/
  `ClassDef`, and the final `ast.walk(tree)` loop still skips the
  `_EXEMPT_FILE`/`_EXEMPT_FUNCTION` body. No commit since `39b7c9c` touches
  `tests/test_155_corpus_case_kind.py`.*
- **A2: A nested scope inherits the enclosing scope's tracked names.** A
  nested function's tracked local names are its own bindings plus every
  tracked name of the scope that encloses it. That keeps a closure covered:
  `m = c['failure_mode']` in `f`, then `if m == 0` in a nested `g`. The base
  reports it once, through `f`'s walk entering `g`. Without inheritance it
  would be missed once that walk stops at `g`. Two side effects follow from
  making the module body a scope like any other. Module-level tracked names
  reach module functions, and module-level class-body statements are now
  scanned. Both find nothing in the live tree (A6).
  *Re-checked 2026-10-05 against `aide/queue-028` at `3f64294`: agrees. The
  base scanner returns `[("synthetic.py", 4)]` for the `closure-name` snippet,
  once.*
- **A3: The walrus rule.** `is_tracked` also holds for an `ast.NamedExpr`
  whose `value` is tracked. So every branch that tests a tracked operand
  (test position, comparison, `not`, `bool(...)`) covers the walrus form, and
  `if (m := c['failure_mode']) == 0:` is reported once, by the comparison
  branch. The walrus target is not added to the scope's tracked names.
  *Re-checked 2026-10-05 against `aide/queue-028` at `3f64294`: agrees.
  `is_tracked` is still `_is_failure_mode_access(node)` or an `ast.Name` in
  `local_names`, and it is the one predicate every reporting branch calls.*
- **A4: The `match` guard and the float bound.** `ast.match_case.guard`, when
  present, is one more test position next to `If.test`, `While.test`,
  `IfExp.test`, `BoolOp.values` and `comprehension.ifs` (item 197 A1). A guard
  that is a comparison is already reported by the comparison branch, because
  the walk enters it, and the guard rule does not report it a second time.
  `ast.match_case` exists on every supported Python (`requires-python =
  ">=3.11"`). The ordering branch's "literal 1" check accepts an `int` or
  `float` constant equal to 1, still excluding `bool`. So `>= 1.0` and `< 1.0`
  join `>= 1` and `< 1`. The zero side already accepts `0.0` through
  `_is_zero_sentinel`.
  *Re-checked 2026-10-05 against `aide/queue-028` at `3f64294`: agrees. The
  test-position branch covers exactly `If`/`While`/`IfExp`, `BoolOp.values`
  and `comprehension.ifs`; `is_one` requires `type(bound.value) is int`;
  `_is_zero_sentinel` accepts any non-`bool` constant equal to 0, so `0.0`;
  `pyproject.toml` still says `requires-python = ">=3.11"`.*
- **A5: What a value default is.** In an `or` (`ast.BoolOp` with `ast.Or`),
  the tracked operand that comes immediately before a **last operand that is a
  zero sentinel** (by the existing `_is_zero_sentinel`) is not reported.
  `x or 0` and `x or CLEAN_CONTROL_MODE` leave every int mode id unchanged and
  only replace a missing value with 0, so they do not test "is this a clean
  control". Every other operand is reported as before. That includes
  `x or None` and `x or -1`, which map mode 0 to something else and so do
  test it; a tracked operand that is not the second-to-last, as in
  `x or other or 0`; and every operand of an `and`. Item 197's AC4 (an `and`)
  is unaffected.
  *Re-checked 2026-10-05 against `aide/queue-028` at `3f64294`: agrees. The
  `BoolOp` case still reports every tracked value regardless of op, and
  `_is_zero_sentinel` matches `0` and the names `CLEAN_CONTROL_MODE` and
  `_CLEAN_MODE_ID` (bare or as an attribute).*
- **A6: The live tree stays clean.** Measured 2026-10-03 on this branch's base
  (`aide/queue-028` at `39b7c9c`) with a scratch copy of the A1–A5 rules,
  reusing `test_155`'s `_is_failure_mode_access`, `_is_zero_sentinel`,
  `_EXEMPT_FILE`, `_EXEMPT_FUNCTION` and `_iter_scanned_files`. It found no
  violation in `src/segfacet` or `tests`. The same scratch scanner gave the
  AC1–AC5 results on their snippets, and on the base each snippet gives the
  "before" result stated above the ACs. The builder hands back if AC6 fails.
  *Re-checked 2026-10-05 against `aide/queue-028` at `3f64294`: agrees. The
  four reused helpers and `_iter_scanned_files` exist as named. Replaying the
  base `_zero_comparisons` on the AC1–AC5 snippets gives two entries at line
  3, `[]`, `[]`, `[]` and one entry at line 2, the "before" results stated
  above the ACs. The live-tree scan was not re-run with the A1–A5 rules; AC6
  stays the builder's check.*
- **A7: No dependency pin.** Items 155, 184 and 197, which wrote and widened
  the scanner, are merged. This item reads the scanner as it stands on the
  base. No queue-028 sibling reads `_zero_comparisons`, so nothing here pins an
  interface for another item.
  *Re-checked 2026-10-05 against `aide/queue-028` at `3f64294`: agrees. The
  scanner is unchanged since `39b7c9c`, and `_zero_comparisons` is still read
  only by `tests/test_155_corpus_case_kind.py`, `tests/test_184_zero_comparison_shapes.py`
  and `tests/test_197_zero_comparison_truthiness_ordering.py`; no queue-028
  sibling spec names it.*

## Implementation Steps

Nothing under `source_dir` changes, and no dependency is added. All changes
are in `tests/test_155_corpus_case_kind.py`'s `_zero_comparisons`.

1. Replace `scan_scope`'s two `ast.walk(stmt)` loops with one scope walk (A1).
   It visits nodes breadth-first from the scope's statements, as `ast.walk`
   does (a `collections.deque` and `ast.iter_child_nodes`), but when it reaches
   a `FunctionDef`/`AsyncFunctionDef` it records that definition and does not
   enter it. The binding pass and the reporting pass both use it.
2. Give `scan_scope` an `inherited` set of tracked names, used to seed
   `local_names` (A2). After the reporting pass, call `scan_scope(d.body,
   local_names)` for each recorded nested definition, skipping the exempt
   `case_kind` body by the existing `_EXEMPT_FILE`/`_EXEMPT_FUNCTION` check.
3. Replace the module-level filter and the final `ast.walk(tree)` loop with
   one call, `scan_scope(tree.body, set())`.
4. In `is_tracked`, unwrap an `ast.NamedExpr` to its `value` before the
   existing check (A3).
5. In the test-position branch, add `ast.match_case`, taking `[node.guard]`
   when the guard is not `None` (A4). In the `BoolOp` case, when the op is
   `ast.Or`, there are at least two values and the last value satisfies
   `_is_zero_sentinel`, leave the second-to-last value out of the list
   (A5).
6. In the ordering branch, let `is_one` accept `type(bound.value) in (int,
   float)` (A4).
7. Update the scanner's description in the module docstring (the AC12/AC13
   paragraph) and in `_zero_comparisons`'s docstring. Say that each scope is
   scanned once, name the walrus, `match`-guard and float-bound shapes, and the
   zero-default exemption, and cite item 209.

## Authorised paths

**May change:**

- `tests/test_155_corpus_case_kind.py` — the changed `_zero_comparisons` and its two docstrings
- `tests/test_209_zero_comparison_scopes_and_defaults.py` — the AC1–AC5 tests and the named adversarial cases

**Asserts against:**

None.

## Testing Strategy

New module `tests/test_209_zero_comparison_scopes_and_defaults.py`, with one
test each for AC1–AC5. It imports the scanner from the module that owns it,
`import test_155_corpus_case_kind as t155`, as
`tests/test_184_zero_comparison_shapes.py` and
`tests/test_197_zero_comparison_truthiness_ordering.py` do. It calls
`t155._zero_comparisons(snippet, "synthetic.py")` and does not copy the
scanner. AC6's test is the existing `test_155` AC12.

Adversarial cases. Write these, as one parametrised test or several, and no
others. Each gives the full snippet and the exact expected list:

- `closure-name`:
  `"def f(c):\n    m = c['failure_mode']\n    def g():\n        if m == 0:\n            pass\n"`
  is reported at line 4. This guards a scope fix that stops the outer walk at
  `g` but does not pass `f`'s tracked names into `g`, which loses the closure
  form the base catches.
- `method-in-nested-class`:
  `"def f(c):\n    class K:\n        def g(self, d):\n            if d['failure_mode'] == 0:\n                pass\n"`
  is reported at line 4. This guards a fix that skips only the nested `def`s
  that are direct statements of the scope. That fix passes AC1 but still walks
  into a method below a class and reports it twice.
- `walrus-compare`:
  `"def f(c):\n    if (m := c['failure_mode']) == 0:\n        pass\n"` is
  reported at line 2. This guards a walrus rule added only to the
  test-position branch instead of to `is_tracked`, which misses the walrus as
  a comparison operand.
- `or-none-default`: `"def f(c):\n    x = c.get('failure_mode') or None\n"` is
  reported at line 2. This guards an exemption that lets any `or` default
  through, although `or None` turns mode 0 into `None`.
- `or-named-sentinel-default`:
  `"def f(c):\n    x = c.get('failure_mode') or CLEAN_CONTROL_MODE\n"` returns
  `[]`. This guards an exemption that tests for the literal 0 instead of
  calling `_is_zero_sentinel`.
- `or-not-second-to-last`:
  `"def f(c, o):\n    x = c.get('failure_mode') or o or 0\n"` is reported at
  line 2. This guards an exemption that drops every operand of an `or` ending
  in 0, although here mode 0 falls through to `o`.

**Existing tests to reconcile:** none need editing. `test_155`'s
`test_ac13_scan_detects_each_forbidden_shape` (seven snippets) and
`test_ac13_scan_exempts_case_kind_body_in_perturbation_module`,
`tests/test_184_zero_comparison_shapes.py` and
`tests/test_197_zero_comparison_truthiness_ordering.py` must stay green
unchanged. None of their snippets nests a function, uses a walrus, a `match`,
a float bound or an `or` ending in a zero sentinel (grep made 2026-10-03), so
their exact results hold. The `case_kind` exemption test uses a module-level
`def`, which step 2's exemption check still skips. A grep made 2026-10-03
found no other caller of `_zero_comparisons`.

## Dependencies

None. Items 155, 184 and 197, which wrote and widened the scanner, are merged.

## Decisions & Trade-offs

- **Implemented as specced (2026-10-05).** `_zero_comparisons` gained a
  `walk_scope` helper (deque plus `ast.iter_child_nodes`, recording nested
  defs without entering them) and `scan_scope(stmts, inherited)`; the module is
  scanned via `scan_scope(tree.body, set())`. Run directly (not via pytest):
  AC1-AC5 and the six adversarial snippets give the stated lists, and the
  live tree reports nothing (AC6).

- **No `Asserts against` entry.** Item 197 listed `src/segfacet/**` for its
  live-tree AC. AC6 here is the existing tree-wide AC12, which every item's
  merge runs again over whatever the tree then holds. It pins no particular
  source file. Queue-028 items 210–212 change files under `src/segfacet/`, and
  listing the subtree would turn each of those authorised edits into a pin
  conflict, with no file this item actually depends on.
- **A test-position `or 0` is let through too.** `if c.get('failure_mode') or
  0:` is a truthiness test that A5's exemption no longer reports. Nobody writes
  it, and telling it apart from the value default needs the parent of the
  `BoolOp`. That is not worth the code here.
- **Left open:** whether `match <tracked access>: case 0:` (a literal-0
  pattern against a tracked subject) should be reported. It tests "is this a
  clean control" as directly as `== 0` does, but the queue and both insights
  name only the guard, and the live tree has no `match` on `failure_mode`.
