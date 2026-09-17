<!-- aide-template: item 1 -->
# Item 158 — The committed-artifact guard's two blind spots

> **Created:** 2026-09-17 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update
> **Queue:** [`../queue/queue-021.md`](../queue/queue-021.md) · Item 158
> **Objectives:** G7
> **Suggested branch:** `aide/158-the-committed-artifact-guard-s`

---

## Description

Roadmap Stage 31 D5, the committed-artifact guard part. It absorbs two
`insights.md` entries, both already ticked with the pointer `→ item 158`: the
gap about the missing ground for the traceability matrix (item 143,
2026-09-03) and the gap about the `parents[1]` module root (item 144,
2026-09-03).

`tests/committed_artifact_guard.py` (item 127) is the static AST classifier
behind every byte-exact fresh-vs-committed comparison under `tests/`. It
resolves an operand to a committed path only when the path is built from a
**literal** `Path(__file__)` chain with at least two `.parent` steps
(`_file_root_parent_count` / `_is_file_root_chain`, now at
`committed_artifact_guard.py:258-294`; the queue cited `:239-255` before items
149–157 moved it). A committed path built any other way is skipped without a
report. Two root idioms that mean the same thing as the literal chain are
skipped today:

1. **`Path(__file__).resolve().parents[N]`**, which is the same directory as
   N+1 `.parent` steps. Measured 2026-09-17: 18 modules under `tests/` build a
   path this way.
2. **The two-hop name-carried root**: `_TESTS_DIR = Path(__file__).resolve().parent`
   followed by `_REPO_ROOT = _TESTS_DIR.parent`. The resolver never follows a
   `.parent` on a *name*. Measured 2026-09-17: 11 modules use this shape.

**What has already landed (verified 2026-09-17, not redone here).** Item 149
already fixed the queue's second half. `ALLOWLIST` carries
`docs/aide/traceability_matrix.generated.{json,md}` under the `no-float-leaf`
ground (`committed_artifact_guard.py:190-201`), and
`test_149_conformance_report.py`'s AC24/AC25 pin that entry and show it is
needed. Item 149 also rewrote `test_138_traceability_matrix.py:98`,
`test_143_s_axis_correction.py:68` and `test_144_failure_mode_specification.py:36`
to use the literal `.parent.parent` root. It did that by editing the
*callers*, not the resolver. So the queue's cited lines `test_138:69` and
`test_144:33` no longer use `parents[1]`, and those three modules are already
visible. The blind spot is still there for every other module.

**This item fixes the resolver.** `parents[N]` with a non-negative integer
literal, and a name bound to a `Path(__file__)` chain, both count as the steps
they stand for. The guard's docstring then lists, in a form a test can read
back, the operand shapes the guard **still** skips. A test proves that each
listed shape really is skipped.

**Every comparison the fixed resolver newly sees** is listed below. It was
measured 2026-09-17 at `be0bb5b` with a read-only script that patched the
resolver in memory and ran `iter_violations` over `tests/` with `ALLOWLIST`
emptied. Before the fix, 13 comparisons were visible, and all 13 stay visible.
The fix adds 22. **All 22 are grounded by an existing `ALLOWLIST` entry, and
none is a violation.** So this item adds no `ALLOWLIST` entry and no `GROUNDS`
member.

| # | Module:line | Root idiom that hid it | Committed path | Decision | Ground (existing entry) |
|---|---|---|---|---|---|
| 1 | `test_103_feature_catalogue.py:974` | `parents[1]` | `docs/aide/feature_catalogue.generated.json` | ground | `emission-clamped` |
| 2 | `test_103_feature_catalogue.py:975` | `parents[1]` | `docs/aide/feature_catalogue.generated.md` | ground | `emission-clamped` |
| 3 | `test_119_curve_formulation.py:824` | `parents[1]` | `docs/aide/feature_catalogue.generated.json` | ground | `emission-clamped` |
| 4 | `test_119_curve_formulation.py:825` | `parents[1]` | `docs/aide/feature_catalogue.generated.md` | ground | `emission-clamped` |
| 5 | `test_120_leave_one_out_offset.py:917` | `parents[1]` | `docs/aide/feature_catalogue.generated.json` | ground | `emission-clamped` |
| 6 | `test_120_leave_one_out_offset.py:918` | `parents[1]` | `docs/aide/feature_catalogue.generated.md` | ground | `emission-clamped` |
| 7 | `test_123_recalibrate_and_regenerate.py:1488` | `parents[1]` | `docs/aide/feature_catalogue.generated.json` | ground | `emission-clamped` |
| 8 | `test_123_recalibrate_and_regenerate.py:1489` | `parents[1]` | `docs/aide/feature_catalogue.generated.md` | ground | `emission-clamped` |
| 9 | `test_124_observed_range.py:529` | `parents[1]` | `docs/aide/feature_catalogue.generated.json` | ground | `emission-clamped` |
| 10 | `test_124_observed_range.py:530` | `parents[1]` | `docs/aide/feature_catalogue.generated.md` | ground | `emission-clamped` |
| 11 | `test_129_coincident_centroids_and_held_out_floor.py:581` | `parents[1]` | `docs/aide/feature_catalogue.generated.json` | ground | `emission-clamped` |
| 12 | `test_129_coincident_centroids_and_held_out_floor.py:582` | `parents[1]` | `docs/aide/feature_catalogue.generated.md` | ground | `emission-clamped` |
| 13 | `test_130_one_closest_point_search.py:736` | `parents[1]` | `docs/aide/feature_catalogue.generated.json` | ground | `emission-clamped` |
| 14 | `test_130_one_closest_point_search.py:737` | `parents[1]` | `docs/aide/feature_catalogue.generated.md` | ground | `emission-clamped` |
| 15 | `test_136_rule_mode_declarations.py:758` | `parents[1]` | `docs/aide/feature_catalogue.generated.json` | ground | `emission-clamped` |
| 16 | `test_136_rule_mode_declarations.py:759` | `parents[1]` | `docs/aide/feature_catalogue.generated.md` | ground | `emission-clamped` |
| 17 | `test_137_mode_less_rule_disposition.py:732` | `parents[1]` | `docs/aide/feature_catalogue.generated.json` | ground | `emission-clamped` |
| 18 | `test_137_mode_less_rule_disposition.py:733` | `parents[1]` | `docs/aide/feature_catalogue.generated.md` | ground | `emission-clamped` |
| 19 | `test_106_stage19_validation.py:618` | `_TESTS_DIR.parent` | `docs/aide/feature_catalogue.generated.json` | ground | `emission-clamped` |
| 20 | `test_106_stage19_validation.py:619` | `_TESTS_DIR.parent` | `docs/aide/feature_catalogue.generated.md` | ground | `emission-clamped` |
| 21 | `test_106_stage19_validation.py:631` | `_TESTS_DIR.parent` | `docs/aide/feature_catalogue.generated.md` | ground | `emission-clamped` |
| 22 | `test_128_relocation_checks.py:157` | `_TESTS_DIR.parent` | `src/segfacet/reference/reference_verse_v1.json` | ground | `integrity-pin` |

Rows 1–21 each compare a freshly regenerated catalogue with the committed
one. That artifact's floats are quantised and clamped when it is written (item
124), which is the ground its existing entry names. Row 22 compares a digest
of the released reference artifact with a recorded constant, which is the
integrity-pin ground. The same script checked a third idiom,
`pathlib.Path(__file__)` (the attribute-call form of `Path`), and found no
hidden comparison. That shape stays unresolved and is listed as still skipped
(**A3**).

**Not in scope:** changing any `ALLOWLIST` entry or `GROUNDS` member; editing
any test module other than this item's own; resolving the placement shapes the
guard skips (comparisons in class methods, module-level asserts, modules in
subdirectories of `tests/`, `in`/`is`/chained comparisons); rewriting callers
back to `parents[1]`.

## Acceptance Criteria

All synthetic sources below go through
`committed_artifact_guard.classify_module(source, "tests/test_zz_synthetic_158.py")`.
In every synthetic case, `ARTIFACT` means the committed path
`src/segfacet/reference/reference_default.json`, which is deliberately
off-allowlist. Each synthetic module has the shape
`<root binding>` + `def test_x(tmp_path):` + `fresh = tmp_path / "fresh.json"` +
`assert fresh.read_bytes() == (<root expr> / "src" / "segfacet" / "reference" / "reference_default.json").read_bytes()`.
"Classifies identically" means the two returned `Violation` lists compare equal,
with both modules laid out line-for-line alike so the `line` fields match.

- [ ] **AC1: `parents[1]` resolves to the repo root.** A module whose root is
  `_REPO_ROOT = Path(__file__).resolve().parents[1]` classifies to exactly one
  `Violation`, whose `committed_path` equals `ARTIFACT`.
- [ ] **AC2: `parents[1]` and `.parent.parent` classify identically.** The
  AC1 module and the same module with its root written
  `Path(__file__).resolve().parent.parent` return equal `Violation` lists.
- [ ] **AC3: `parents[0]` and a single `.parent` classify identically.** A
  module rooted at `Path(__file__).resolve().parents[0]` and one rooted at
  `Path(__file__).resolve().parent` return equal lists. Both lists are empty,
  because a one-step root is still not the repo root.
- [ ] **AC4: `parents[2]` and three `.parent` steps classify identically.**
  A module rooted at `Path(__file__).resolve().parents[2]` and one rooted at
  `Path(__file__).resolve().parent.parent.parent` return equal lists, each
  holding one `Violation` whose `committed_path` equals `ARTIFACT`.
- [ ] **AC5: a `parents` index that is not a non-negative int literal resolves
  nothing.** Three modules return an empty list: one rooted at
  `Path(__file__).resolve().parents[-1]`, one at `...parents[n]` (with `n` a
  module-level int), and one at `...parents[True]`.
- [ ] **AC6: a module-level two-hop root and the literal chain classify
  identically.** A module binding `_TESTS_DIR = Path(__file__).resolve().parent`
  then `_REPO_ROOT = _TESTS_DIR.parent`, and comparing against
  `_REPO_ROOT / ...`, returns a list equal to the same module with
  `_REPO_ROOT = Path(__file__).resolve().parent.parent`. The list holds one
  `Violation` for `ARTIFACT`.
- [ ] **AC7: a name carrying a one-step root is still not the repo root.** A
  module binding `_TESTS_DIR = Path(__file__).resolve().parent` and comparing
  against `_TESTS_DIR / "src" / "segfacet" / "reference" / "reference_default.json"`
  returns an empty list.
- [ ] **AC8: a function-local two-hop root and the literal chain classify
  identically.** A test function that binds `here = Path(__file__).resolve().parent`
  and then `root = here.parent` before comparing against `root / ...` returns
  a list equal to the same function with
  `root = Path(__file__).resolve().parent.parent`. The list holds one
  `Violation` for `ARTIFACT`.
- [ ] **AC9: every real test module classifies the same as its normalised
  source.** Take each `tests/*.py`, with `ALLOWLIST` emptied. Normalise its
  source by replacing every `<expr>.parents[<int literal N ≥ 0>]` with
  `<expr>` followed by N+1 `.parent` steps, then replacing every load of a
  module-level name bound to a `Path(__file__)` chain with that chain's
  (normalised) expression. The sorted list of `committed_path` values that
  `classify_module` returns for the original source equals the one it returns
  for the normalised source.
- [ ] **AC10: the tests tree is guard-clean with the committed allowlist.**
  `list(committed_artifact_guard.iter_violations(<repo>/tests))` equals `[]`.
- [ ] **AC11: the traceability-matrix comparison is visible and its entry is
  what grounds it.** Remove only the `ALLOWLIST` entries whose `path` starts
  with `docs/aide/traceability_matrix.generated.`, then run `iter_violations`
  over `tests/`. It returns a non-empty list, and every returned
  `committed_path` starts with `docs/aide/traceability_matrix.generated.`.
- [ ] **AC12: every shape the docstring lists as still skipped is skipped.**
  The module docstring holds a list introduced by the line
  `Still skipped in silence:`, with bullets of the form
  ``- <prose>: ``<expression>`` `` (**A6**). The list is non-empty. Render each
  `<expression>`, with the token `ARTIFACT` replaced by the string literal
  `"src/segfacet/reference/reference_default.json"`, into the fixed template in
  **A6**. Every rendered module parses with `ast.parse`, and
  `classify_module` returns an empty list for each one.
- [ ] **AC13: the AC12 template can see a violation.** Render the control
  expression `(Path(__file__).resolve().parent.parent / ARTIFACT).read_bytes()`
  into the same A6 template. `classify_module` returns exactly one `Violation`,
  whose `committed_path` equals `ARTIFACT`.

**Clarification (2026-09-17), AC6 and AC8 fixtures.** The criteria stand as
written, and `Violation` equality includes `line`. The preamble above already
requires the two members of a pair to be laid out line-for-line alike, so a
fixture pair whose root bindings differ in statement count fails for a correct
resolver and is a fixture defect, not a resolver finding. Where the two-hop
variant needs two binding lines, the literal variant must carry the same
number of lines before the comparison. Pad it with a neutral no-op binding
that no resolver can read as a root: `_PAD = None` at module level for AC6,
and `    here = None` inside the function for AC8, placed first so the root
binding stays on the same line in both members. The padding must not bind a
`Path(__file__)` chain, since that would put resolver-relevant input into the
control member. The test should also assert that the two sources have the
same number of lines, so a future layout drift fails on the fixture rather
than on the `line` field.

No AC closes a Stage 31 acceptance criterion: none of the stage's five boxes
is about the guard. D5 is a deliverable bullet and is not closed by annotation.

## Assumptions

- **A1:** The queue's second half is already done and is not redone. The
  `no-float-leaf` ground and the two traceability-matrix `ALLOWLIST` entries
  came from item 149 (`committed_artifact_guard.py:190-201`), and are pinned
  by `test_149_conformance_report.py` AC23–AC25. The same item rewrote
  `test_138`, `test_143` and `test_144` to the literal `.parent.parent` root.
  This item does not change those modules back to `parents[1]`. Since
  `test_138:1670` (AC29) now runs over a resolver that sees `parents[N]` and
  two-hop roots, the queue's "test_138's and test_144's guard-clean
  attestations still hold" is met by AC10. `test_144` has no guard-clean
  attestation of its own; its only guard mentions are docstring prose.
- **A2:** The name-carried two-hop root is in scope as well as `parents[N]`.
  The item-143 insight that points at this item names that shape explicitly,
  11 modules use it, and it hides 4 of the 22 comparisons in the Description's
  table. Leaving it would keep the same defect class under another spelling.
- **A3:** `pathlib.Path(__file__)` (the attribute-call form) stays unresolved.
  It hides no comparison (measured 2026-09-17), and fixing it is not needed.
  It goes in the docstring's still-skipped list, so AC12 checks the claim that
  it is skipped.
- **A4:** The existing rule "two or more steps above `Path(__file__)` is the
  repo root, and one step is not" is kept exactly as it is. `iter_violations`
  is non-recursive over `tests/*.py`, so depth 2 is the real repo root for
  every module it scans. `parents[N]` maps to depth N+1 under the same rule.
- **A5:** An index counts only if it is an `int` literal ≥ 0, and `bool` is
  not an `int` literal here. Any other index — negative, a name, an
  expression, `True` — resolves nothing. That is silence, not a guess:
  `parents[-1]` is the filesystem root, not the repo.
- **A6:** The docstring's still-skipped list is machine-readable. It is
  introduced by the exact line `Still skipped in silence:`. Each entry is one
  line of the form ``- <prose>: ``<expression>`` ``, where `<expression>` is a
  single Python expression that uses the token `ARTIFACT` where the committed
  path goes. The list ends at the first blank line. The test renders each
  entry into this template (4-space indent, `<EXPR>` substituted):

  ```
  import hashlib
  import json
  import pathlib
  from pathlib import Path


  def test_shape(tmp_path, arg):
      fresh = tmp_path / "fresh.json"
      assert fresh.read_bytes() == <EXPR>
  ```

  The list must include at least these operand shapes, which the builder may
  word and extend: a `pathlib.Path(__file__)` root; a function argument used as
  a root (`arg`); the result of an arbitrary call used as a root (`arg()`); a
  `parents` index that is not a non-negative int literal; a value reached
  through `json.loads`; a comprehension variable; and a path segment that is
  not a string literal (an f-string). Placement shapes — class methods,
  module-level comparisons, modules in subdirectories, and `in`/`is`/chained
  comparisons — cannot be written as an operand. They are described in prose
  outside this list and no AC claims them.
- **A7:** The queue cited `committed_artifact_guard.py:239-255`,
  `test_138:69` and `test_144:33`. Items 149–157 moved all three. The spec
  uses the positions measured 2026-09-17 at `be0bb5b`. The table's line
  numbers are provenance, not assertions: no test pins them.
- **A8:** Both absorbed insight entries (2026-09-03, items 143 and 144) are
  already ticked `→ item 158`. This item adds no trail line under them. The
  Stage 31 triage (item 160) owns the inbox state.
- **A9:** `_is_file_root_chain` keeps its name.
  `tests/test_128_reference_verse_v1_integrity.py:26` refers to it by name in a
  comment, and this item may not edit that module.

## Implementation Steps

1. **`_file_root_parent_count`** (`tests/committed_artifact_guard.py`). Add an
   `ast.Subscript` branch: `node.value` is an `ast.Attribute` with
   `attr == "parents"`, and `node.slice` is an `ast.Constant` whose
   `type(value) is int` and `value >= 0`. The result is the inner chain's count
   + N + 1, or `None` if the inner chain does not resolve. On Python 3.9+,
   `node.slice` is the index expression itself, and `requires-python` is ≥3.9.
2. **Name-carried depth.** Give `_file_root_parent_count` and
   `_is_file_root_chain` an optional `depths: Dict[str, int]` mapping. An
   `ast.Name` found in `depths` returns its depth. `_resolve_expr` passes the
   mapping through. `_module_level_paths` records the depth of every
   module-level single-name assignment whose value has a count, at any depth
   including 1. `_classify_function` copies that mapping and extends it with
   the function's own assignments, in source order, in the same pre-scan that
   builds `local_known`. The two-step root rule is unchanged (**A4**).
3. **Docstring.** Rewrite the "Precise, not exhaustive" section. Name the
   resolved root shapes, adding `parents[N]` and name-carried roots. Add the
   `Still skipped in silence:` list in the **A6** form. Describe the placement
   shapes in prose. Remove "a loop variable" from the prose sentence only if
   the list now covers it. Update `_is_file_root_chain`'s own docstring to
   cover the new forms.
4. **Stale comment.** The comment above `GROUNDS` says "Adding a sixth member".
   Six members already exist, so it becomes "Adding a member". No behaviour
   change.
5. **Tests.** Write `tests/test_158_committed_artifact_guard_resolver.py`
   (test-writer's file; see **Testing Strategy**).

## Authorised paths

**May change:**

- `tests/committed_artifact_guard.py` — the resolver (steps 1–2), the
  docstring list (step 3) and the stale comment (step 4). Neither `ALLOWLIST`
  nor `GROUNDS` changes.
- `tests/test_158_committed_artifact_guard_resolver.py` — this item's tests.

**Asserts against:**

- `tests/test_149_conformance_report.py` — its byte comparison against
  `docs/aide/traceability_matrix.generated.md` is one of the comparisons that
  keeps AC11 non-empty; read by the tree sweep, never edited.

AC9, AC10 and AC11 sweep every `tests/*.py`, but they assert invariants that
hold for any content: normalisation equivalence, and guard-cleanness. They pin
no module's content, so the tree is not listed here. A sibling item's edit to
a test module changes what the sweep reads, not what it claims.

## Testing Strategy

New module `tests/test_158_committed_artifact_guard_resolver.py`. It imports
`committed_artifact_guard` the way the existing guard tests do, since `tests/`
is on `sys.path`. It writes one focused test per AC and uses only in-memory
source strings; nothing goes into the real `tests/` tree.

- **AC1–AC8.** Build the paired sources from one helper that takes the root
  binding lines, so the two members of a pair differ only in the root
  expression and share a line layout. Assert list equality between the pair
  **and**, where the AC says so, the exact expected content: one `Violation`
  with `committed_path == ARTIFACT`, or empty. Asserting only equality would
  let two equally blind classifications pass. Use `monkeypatch` only if a test
  needs `ALLOWLIST` changed; `ARTIFACT` is already off-allowlist.
- **AC9.** Write an `ast.NodeTransformer` that (a) expands `parents[N]` for
  an int literal N ≥ 0 and (b) inlines loads of module-level names bound to a
  `Path(__file__)` chain. Render with `ast.unparse`. Empty `ALLOWLIST` with
  `monkeypatch`. For every `tests/*.py`, compare the sorted `committed_path`
  lists. **Non-vacuity, derived live:** the test also counts modules where
  the normalisation changed `ast.dump` **and** the normalised source
  classifies non-empty, and asserts that count is ≥ 1. That makes the
  equivalence meaningful rather than true because no module ever used either
  idiom. Measured 2026-09-17, it is 11 modules (9 `parents[1]`, 2 two-hop).
- **AC10.** Run `iter_violations` over the real tree with the committed
  allowlist. On failure, report with `violation_message`.
- **AC11.** Narrow `ALLOWLIST` with `monkeypatch` by filtering on the path
  prefix. Before asserting, check that the narrowing removed at least one
  entry, so the fixture assumption is stated.
- **AC12.** Parse `committed_artifact_guard.__doc__` for the list in the A6
  form. Fail with a clear message if the intro line is missing or the list is
  empty. For each entry, assert `ast.parse` succeeds on the rendered module,
  since invalid Python classifies clean vacuously. Assert the expression
  contains `ARTIFACT`, then assert `classify_module(...) == []`.
- **AC13.** The same template and renderer as AC12, with the control
  expression.

**Adversarial / edge cases** (inside the AC tests or as `test_adv_*`):
- `parents[1]` directly on `Path(__file__)` with no `.resolve()` resolves the
  same as AC1.
- A chained root `Path(__file__).resolve().parent.parents[0]` has depth 2, so
  it resolves.
- A module-level name bound to `parents[1]` and then joined with
  `/ "docs" / "aide" / "x.json"` resolves to `docs/aide/x.json`.
- Classifying the same source twice returns equal lists (determinism).
- The existing behaviours still hold, shown by re-running the synthetic
  sources of test_127's `test_edge_unresolvable_operands_are_skipped_in_silence`
  and `test_ac18_unchanged_fence_is_not_a_violation` in this module: a loop
  variable is skipped, and the unchanged-fence idiom is not a violation.

**Existing tests to reconcile:** none expected. A grep of `tests/` on
2026-09-17 found no test asserting that `parents[N]` or a name-carried root is
skipped. The whole-tree guard-clean tests will now also read the 22
comparisons in the Description's table, and all of them are allowlisted, so
those tests stay green: `test_111::test_committed_artifact_guard_reports_zero_violations`,
`test_127::test_ac15_…`, `test_128_relocation_checks.py:717`,
`test_129::test_ac33_…`, `test_131::test_ac25_…`, `test_134::test_ac16_…`,
`test_138::test_ac29_…` and `test_149::test_ac26_…`. The non-vacuity tests
(`test_149::test_ac25_…` and `test_128_relocation_checks.py:860`) only gain
visibility. If any of them fails, it is a real finding, not a stale
assertion. Hand it back.

## Validation

Replay the Description's table. With the fix in place, run a read-only
`.venv/bin/python` snippet that empties `committed_artifact_guard.ALLOWLIST`
and lists `iter_violations(tests)`. Check that the set of `(module,
committed_path)` pairs is at least the 13 pre-fix pairs plus the 22 rows
above. Then restore the allowlist and check that `iter_violations` is empty.
Line numbers may have drifted since 2026-09-17. If they have, record the drift
under Decisions & Trade-offs rather than editing the table.

## Dependencies

None. Item 149, which supplied the `no-float-leaf` ground and the
traceability-matrix entries this item relies on, is merged.

**Downstream:** item 160 (insight triage) reads the two absorbed entries
already ticked to this item. Item 159 edits test modules that this item's
tree sweeps read, but it pins nothing this item changes.

## Decisions & Trade-offs

- Implemented per the spec: `_file_root_parent_count` gained an `ast.Subscript`
  branch (`.parents[N]`, `N` a non-negative `int` literal per `type(value) is
  int`, contributing `N+1` steps) and an `ast.Name` branch consulting a new
  `depths: Dict[str, int]` parameter threaded through it, `_is_file_root_chain`
  (name unchanged, A9), `_resolve_expr`, `_resolve_operand`,
  `_module_level_paths` (now returns `(known, depths)`, recording every
  module-level `Path(__file__)`-chain assignment's depth, one-step roots
  included) and `_classify_function` (copies the module depths, extends them
  with the function's own assignments in the same pre-scan pass that already
  built `local_known`). `classify_module` threads the new `module_depths`
  through.
- Docstring: rewrote "Precise, not exhaustive" to name `parents[N]` and the
  two-hop name-carried root, and added the `Still skipped in silence:` list in
  the A6 form (intro line immediately followed by bullets, no blank line
  before the first bullet, since the parser treats a blank line as the list's
  end) covering all seven required shapes. Placement shapes (class methods,
  module-level comparisons, subdirectory modules, `in`/`is`/chained
  comparisons) are described in prose after the list, per A6. The "a loop
  variable" phrase stays in prose since the list's "comprehension variable"
  entry is a distinct shape (`for` binding vs. a comprehension).
  `GROUNDS`'s comment fixed from "Adding a sixth member" to "Adding a member"
  (six members already existed).
- Verified: `iter_violations` over `tests/` with the committed `ALLOWLIST` is
  `[]` (per the item's own instruction to STOP if not); no `ALLOWLIST` or
  `GROUNDS` change was made, matching the spec's claim that all 22 newly
  visible comparisons are already grounded.
- Tests (already committed by test-writer) verified directly via
  `classify_module`/`iter_violations` calls rather than `pytest`, per this
  role's constraints: all 23 tests in
  `tests/test_158_committed_artifact_guard_resolver.py` pass.
- 2026-09-17: Validation round 1 found a soundness defect in the depth/known
  tracking added above: `_module_level_paths`'s and `_classify_function`'s
  pre-scan loops only ever *set* `depths[name]` (and `known[name]`) when a new
  assignment resolves; a rebinding of an already-tracked name to something
  that does *not* resolve (e.g. `_TESTS_DIR = some_call()`) left the old entry
  in place, so a later `_TESTS_DIR.parent` read the stale depth/path and could
  manufacture a false-positive `Violation` — the guard's own contract ("a
  reported Violation is authoritative") depends on there being no such
  staleness. Fixed by popping `name` from `depths`/`known`/`local_reads`
  whenever the corresponding resolution attempt comes back `None`, so a
  rebinding always overwrites-or-clears rather than only ever overwriting.
  Function-local rebindings still only mutate the function's own copies
  (`local_known`/`local_depths`/`local_reads`), never the module-level dicts.
