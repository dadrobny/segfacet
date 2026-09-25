<!-- aide-template: item 2 -->
# Item 185 — `committed_artifact_guard` resolves the `dirname(abspath(__file__))` root

> **Created:** 2026-09-25 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (maintenance)
> **Queue:** [`../queue/queue-024.md`](../queue/queue-024.md) · Item 185
> **Objectives:** G7
> **Suggested branch:** `aide/185-committed-artifact-guard-resolves-the`

---

## Description

`tests/committed_artifact_guard.py` (item 127) is the static AST classifier
behind every byte-exact fresh-vs-committed comparison under `tests/`. It
reports a comparison only when one operand resolves to a committed,
repo-relative path. It resolves a path only when the path is built from a
`Path(__file__)` root that is at least two directory steps up. Item 158 taught
it two more spellings of that root: `.parents[N]`, and a name that carries a
`Path(__file__)` chain. Both go through `_file_root_parent_count`.

A third spelling is still skipped without a report. It is the `os.path` string
form:

```python
_tests_dir = os.path.dirname(os.path.abspath(__file__))
```

Four test modules bind it today: `test_019_vertebra_orientation_curvature.py`,
`test_121_tangent_orientation.py`, `test_122_signed_curvature.py` and
`test_131_tangent_direction_normalisation.py`. All four use it only for the
`sys.path` setup, so it hides no comparison today. It is the same defect class
as item 158's two fixes, and it is missing from the docstring's
`Still skipped in silence:` list (`insights.md`, gap entry of item 158,
2026-09-17, already ticked `→ item 185`).

**This item teaches `_file_root_parent_count` the `os.path` root.**
`os.path.abspath(x)` keeps the depth of `x`, `os.path.dirname(x)` adds one
step, `__file__` is depth 0, and `Path(x)` keeps the depth of whatever chain
`x` is. A name bound to any of these carries its depth, through the existing
`depths` mapping. The rule that a root counts as the repo root only at depth 2
or more is unchanged.

**Measured 2026-09-25 at `e4d87c5`** with a read-only script that patched
`_file_root_parent_count` in memory as above. With `ALLOWLIST` emptied,
`iter_violations(tests/)` sees the same 38 `(module, committed_path)` pairs
before and after the patch: none is added and none is lost. Each of the four
modules gets a depth-1 entry for `_tests_dir` and nothing else. So this item
adds no `ALLOWLIST` entry and no `GROUNDS` member.

**Not in scope:**

- `os.path.join(...)` as a path join, and `open(...).read()` as a read shape.
  The guard's join is `/` with literal segments, and its read shapes are the
  three the docstring lists. The join form goes into the still-skipped list
  (Implementation Step 3); see **Left open**.
- `os.path.realpath`, and a bare `dirname(...)`/`abspath(...)` reached through
  `from os.path import ...`. No module under `tests/` uses either.
- Any change to `ALLOWLIST`, `GROUNDS`, the placement shapes the guard skips,
  or any test module other than this item's own.

## Acceptance Criteria

Every synthetic source below goes through
`committed_artifact_guard.classify_module(source, "tests/test_zz_synthetic_185.py")`.
`ARTIFACT` means the committed path
`src/segfacet/reference/reference_default.json`, which is deliberately
off-allowlist. Each synthetic module has this shape, with `<root lines>`
binding `_ROOT`:

```python
import os
from pathlib import Path
<root lines>


def test_x(tmp_path):
    fresh = tmp_path / "fresh.json"
    assert fresh.read_bytes() == (_ROOT / "src" / "segfacet" / "reference" / "reference_default.json").read_bytes()
```

"One violation for `ARTIFACT`" means the returned list has length 1 and its
element's `committed_path` equals `ARTIFACT`. The shipped guard returns `[]`
for all three AC1–AC3 sources, so each test fails before the change.

- [ ] **AC1: the inline `os.path` repo root is resolved.** With root lines
  `_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))`,
  `classify_module` returns one violation for `ARTIFACT`.
- [ ] **AC2: the live `_tests_dir` binding, stepped up with `.parent`, is
  resolved.** With root lines
  `_tests_dir = os.path.dirname(os.path.abspath(__file__))` then
  `_ROOT = Path(_tests_dir).parent`, `classify_module` returns one violation
  for `ARTIFACT`.
- [ ] **AC3: the live `_tests_dir` binding, stepped up with
  `os.path.dirname`, is resolved.** With root lines
  `_tests_dir = os.path.dirname(os.path.abspath(__file__))` then
  `_ROOT = Path(os.path.dirname(_tests_dir))`, `classify_module` returns one
  violation for `ARTIFACT`.
- [ ] **AC4: the live tree is still guard-clean.**
  `list(committed_artifact_guard.iter_violations(<repo>/tests))` equals `[]`
  with the committed `ALLOWLIST`. The test is the existing
  `tests/test_158_committed_artifact_guard_resolver.py::test_ac10_tests_tree_is_guard_clean_with_committed_allowlist`.
  It must pass unchanged, and no new test is written for this AC.

No AC closes a Stage 33 acceptance criterion. This is a maintenance item, and
none of the stage's criteria is about the guard.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

- **A1: What "resolve the idiom" covers.** The queue names the idiom
  `os.path.dirname(os.path.abspath(__file__))`. A root one step up is not the
  repo root, so a comparison rooted through the idiom needs one more step. The
  two spellings a test author would add to the live `_tests_dir` binding are
  `Path(_tests_dir).parent` and `os.path.dirname(_tests_dir)`. The resolver
  therefore needs four rules: `os.path.dirname` adds a step,
  `os.path.abspath` keeps the depth, `__file__` is the base at depth 0, and
  `Path(<chain>)` keeps the chain's depth. The last rule generalises today's
  `Path(__file__)` branch. `Path(<string literal>)` in `_resolve_expr` is
  unchanged. `os.path.dirname` and `os.path.abspath` match only as the
  attribute chain `os.path.<name>`, called with exactly one positional
  argument and no keywords.
- **A2: The one-step rule is kept.** A depth-1 `os.path` root (the live
  `_tests_dir` itself) is not the repo root, for the reason
  `_is_file_root_chain`'s docstring gives. `iter_violations` is
  non-recursive, so depth 2 is the real repo root for every module it scans.
- **A3: No hidden comparison exists today.** This was measured, as the
  Description says, at `e4d87c5`: 38 pairs before and after, none added and
  none lost. If AC4 fails on the real change, it is a finding, not a stale
  assertion, and the builder hands back.
- **A4: `pathlib.Path(...)` stays unresolved.** The generalised `Path(<chain>)`
  branch still matches only the bare name `Path`, as `_is_name(node.func,
  "Path")` does today. The docstring's existing `pathlib.Path(__file__)`
  still-skipped entry stays true, and `test_158`'s AC12 keeps checking it.
- **A5: No dependency pin.** Item 158, which wrote the `depths` mapping and the
  still-skipped list this item extends, is merged. This item reads the guard
  as it stands on the base, so there is no interface pin to re-check.

## Implementation Steps

All changes are in `tests/committed_artifact_guard.py`. Nothing under
`source_dir` changes, and no dependency is added.

1. **`_file_root_parent_count`.** Add these branches, reusing the existing
   `depths` threading and recursion. Do not write a second resolver.
   - `ast.Name` with `id == "__file__"` returns 0. Check it before the
     existing `depths.get(node.id)` lookup.
   - An `ast.Call` whose `func` is the attribute chain `os.path.abspath`, with
     one positional argument and no keywords, returns the argument's count.
   - The same shape for `os.path.dirname` returns the argument's count + 1, or
     `None` if the argument has no count.
   - Replace the `Path(__file__)` branch: `Path(<one arg>)` returns the
     argument's count. With the `__file__` rule above, `Path(__file__)` is
     still 0.

   `_module_level_paths` and `_classify_function` already record the depth of
   every single-name assignment that has a count. So `_tests_dir` picks up
   depth 1 with no change to either function.
2. **Docstrings.** In the module docstring's "Precise, not exhaustive"
   section, name the `os.path` root (`os.path.dirname`/`os.path.abspath` over
   `__file__`, optionally wrapped in `Path(...)`) among the resolved roots.
   Cite item 185. Update `_file_root_parent_count`'s and `_is_file_root_chain`'s
   docstrings to match.
3. **Still-skipped list.** Add one entry to the `Still skipped in silence:`
   list, in the existing one-line form (``- <prose>: ``<expression>`` ``, no
   colon in the prose), for a path built with `os.path.join` on the `os.path`
   root. The expression is
   `Path(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ARTIFACT)).read_bytes()`.
   `test_158`'s AC12 then checks that the shape really is skipped. Do not add
   the `os.path` root itself, because it is now resolved.

## Authorised paths

**May change:**

- `tests/committed_artifact_guard.py` — the resolver (step 1), its docstrings (step 2) and the still-skipped list (step 3)
- `tests/test_185_guard_os_path_root.py` — the AC1–AC3 tests and the named adversarial cases

**Asserts against:**

- `tests/test_158_committed_artifact_guard_resolver.py` — AC4 is its AC10 test, run unchanged; its AC12 tests also check the still-skipped entry step 3 adds

## Testing Strategy

New module `tests/test_185_guard_os_path_root.py`, with one test each for AC1,
AC2 and AC3. It imports the guard as `import committed_artifact_guard as
guard`, as `test_158` does, and builds each source from one helper that takes
the root lines. Everything stays in in-memory strings, and nothing is written
into the real `tests/` tree. AC4's test is `test_158`'s existing AC10.

Adversarial cases. Write these, and no others:

- `one-step-os-path-root`: root lines
  `_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))` return `[]`.
  This guards a resolver that treats the idiom as the repo root whatever its
  depth. That would read a `tests/`-relative path as repo-relative, and so
  report a `Violation` against a path that is not the one being read.
- `dirname-off-a-non-file-base`: root lines
  `_ROOT = Path(os.path.dirname(os.path.dirname(os.getcwd())))` return `[]`.
  This guards a resolver that counts `dirname` steps without checking that
  the chain starts at `__file__`. It would report a `Violation` that is not
  real, and the guard's docstring promises that a reported `Violation` is
  authoritative.
- `live-binding-alone-is-not-a-root`: the real source of
  `tests/test_019_vertebra_orientation_curvature.py`, read from disk, goes
  through `committed_artifact_guard._module_level_paths`. The returned
  `depths` maps `_tests_dir` to `1`, and the returned `known` has no
  `_tests_dir` key. This guards the recording itself. The AC tests only see
  the depth through a stepped-up root. This case pins that the live binding
  is tracked at the right depth, and that it is not taken for the repo root.

**Existing tests to reconcile:** none need editing. Three groups must stay
green unchanged:

- `test_158`'s AC12 tests. Step 3 adds one entry, and
  `test_ac12_still_skipped_covers_the_required_operand_shapes` only checks
  that required shapes are present.
- `test_158`'s AC9 test. Its normaliser inlines only names bound to a
  `Path(__file__)` chain. So a name bound to an `os.path` chain is left in
  place, and both sides are classified by the same resolver.
- Every whole-tree guard-clean test (`test_111`, `test_127` AC15, `test_128`,
  `test_129` AC33, `test_131` AC25, `test_134` AC16, `test_138` AC29,
  `test_149` AC26, `test_158` AC10). By A3 they see the same 38 pairs.

A grep of `tests/` on 2026-09-25 found no test asserting that the `os.path`
root is skipped.

## Validation

Replay A3's measurement against the real change. Run a read-only
`.venv/bin/python` snippet that empties `committed_artifact_guard.ALLOWLIST`
and collects the `(module, committed_path)` pairs from
`iter_violations(tests/)`. Compare the set with the one from the base commit
of this branch. The two sets are expected to be equal, at 38 pairs. If they
differ, record each new or lost pair under Decisions & Trade-offs and hand
back.

## Dependencies

None. Item 158, whose resolver and still-skipped list this item extends, is
merged.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** `os.path.join(...)` as a path join, and `open(...).read()`
  as a read shape. No module under `tests/` builds a committed path either
  way. Resolving them would widen the guard's read and join model, not just
  its root model. Step 3 records the join form as still skipped, so the gap
  is written down and checked rather than silent.
