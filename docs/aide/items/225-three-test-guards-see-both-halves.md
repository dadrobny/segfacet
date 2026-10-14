<!-- aide-template: item 3 -->
# Item 225 — Three test guards that see only half of what they guard

> **Created:** 2026-10-13 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-030.md`](../queue/queue-030.md) · Item 225
> **Objectives:** G6, G7
> **Suggested branch:** `aide/225-test-guards-both-halves`

---

## Description

Three shipped test guards each see only part of the shape they exist to catch.
This item closes the part each one misses.

1. **`tests/committed_artifact_guard.py`** (item 127; insight `2026-10-05-aac0`).
   Today it flags an exact `==`/`!=` only when an operand is a direct
   `.read_bytes()` / `.read_text()` / sha256 read of a committed path, or a
   function-local name bound to such a read. It misses a value **parsed** from
   that read, such as `json.loads(p.read_text())["x"] == fresh`, and it misses
   a **module-level** name bound to a read. This item widens operand
   resolution to see through `json.loads(...)` and through subscript / `.get()`
   chains, inline and on a bound name, at function and at module level. The
   widening newly reaches three live comparisons, measured 2026-10-12:
   `tests/test_119_curve_formulation.py:846`,
   `tests/test_120_leave_one_out_offset.py:468` and
   `tests/test_123_recalibrate_and_regenerate.py:1608`. All three compare
   against `tests/corpus/119_pre_119_digests.json`, a fixture holding one
   sha256 hex string. One `ALLOWLIST` entry under the `integrity-pin` ground
   clears all three. No test module changes.
2. **`tests/test_155_corpus_case_kind.py::_zero_comparisons`** (insight
   `2026-10-05-90c4`). The behaviour this insight asks for is **already on the
   base**. Item 209's `walk_scope` puts a def's decorators, defaults and
   annotations into the enclosing scope for every def it meets, module-level
   defs and methods included. All six shapes named in the ACs below are
   reported today (probe, 2026-10-12). But nothing pins the module-level or
   method shapes: `test_209` pins only the nested-def header. This leg is
   therefore **test-only**. It adds planted-instance pins, and the scanner
   does not change.
3. **`docs/aide/golden-decision-table.md`'s `asserted by` column** (insight
   `2026-10-09-7e82`). `tests/test_105_golden_decision_table.py` AC6 checks
   the column in one direction only: every named test exists. This item adds
   the reverse check for rows whose fixture lives under `tests/golden/`: every
   test module that reads the fixture is named in that row. The insight, and
   the queue entry built from it, counted "twelve modules" reading
   `tests/golden/report_format_contract.json`. Counted by code reference, the
   number is **five**:
   - test_016, test_022, test_111, test_126 and test_135 are the readers.
   - test_119, test_120, test_122, test_123 and test_143 mention the file only
     in comments.
   - `committed_artifact_guard.py` and `report_format_fixture.py` are helper
     modules, which the column's `tests/test_\d+…` form cannot name.

   Only `tests/test_135_stage29_validation.py` is unnamed. It reads the
   fixture through `fixture_mod.GOLDEN_PATH`, and the row gains it.

**Not in scope:**
- The reverse check is not run over keep rows outside `tests/golden/`. Measured
  2026-10-12, that would demand roughly 200 more names, mostly incidental
  mentions.
- No guard shape beyond those named here is added. The "Still skipped in
  silence" list keeps its entries.
- No change to `_zero_comparisons`.

## Acceptance Criteria

*Committed-artifact guard.* Each planted snippet below is a test module
source passed to `committed_artifact_guard.classify_module(source,
"tests/test_synthetic.py")`. `REF` stands for the string literal
`"src/segfacet/reference/reference_default.json"`, which is deliberately off
the allowlist. Every snippet starts with `import json` and
`from pathlib import Path`.

- [ ] **AC1: an inline parsed read is flagged.** The function body
  `assert json.loads(Path(REF).read_text())["x"] == fresh` (with `fresh = 1`
  bound above it) yields exactly one `Violation`, whose `committed_path` is
  `src/segfacet/reference/reference_default.json`.
- [ ] **AC2: a function-local name bound to a parsed read is flagged.** This
  function body yields exactly one `Violation` with that `committed_path`:
  `data = json.loads(Path(REF).read_text())` followed by
  `assert data["x"] == 1`.
- [ ] **AC3: a module-level name bound to a parsed read is flagged.** The
  module-level `DATA = json.loads(Path(REF).read_text())`, with a test
  function whose body is `assert DATA["x"] == 1`, yields exactly one
  `Violation` with that `committed_path`.
- [ ] **AC4: the live `tests/` tree is guard-clean.**
  `list(committed_artifact_guard.iter_violations(<repo>/tests)) == []`. The
  existing `tests/test_127_committed_artifact_tolerance.py::test_ac15_classifier_reports_zero_violations_on_tests_tree`
  already asserts this, and no new test is written for it. It holds on the
  base. The widening without the new `ALLOWLIST` entry would make it fail on
  the three comparisons named in the Description.

*Zero-comparison scanner (test-only pins).* Each snippet below is passed to
`test_155_corpus_case_kind._zero_comparisons(snippet, "synthetic.py")`.

- [ ] **AC5: a module-level def's default is reported.**
  `"def g(x=(c['failure_mode'] == 0)):\n    pass\n"` returns
  `[("synthetic.py", 1)]`.
- [ ] **AC6: a module-level def's decorator is reported.**
  `"@deco(c['failure_mode'] == 0)\ndef g():\n    pass\n"` returns
  `[("synthetic.py", 1)]`.
- [ ] **AC7: a module-level def's annotation is reported.**
  `"def g(x: (c['failure_mode'] == 0)):\n    pass\n"` returns
  `[("synthetic.py", 1)]`.
- [ ] **AC8: a method's default is reported.**
  `"class K:\n    def g(self, x=(c['failure_mode'] == 0)):\n        pass\n"`
  returns `[("synthetic.py", 2)]`.
- [ ] **AC9: a method's decorator is reported.**
  `"class K:\n    @deco(c['failure_mode'] == 0)\n    def g(self):\n        pass\n"`
  returns `[("synthetic.py", 2)]`.
- [ ] **AC10: a method's annotation is reported.**
  `"class K:\n    def g(self, x: (c['failure_mode'] == 0)):\n        pass\n"`
  returns `[("synthetic.py", 2)]`.

*Decision-table reverse check.* `_unnamed_golden_readers(rows, repo_root)` is
the helper pinned in Assumption A4. In AC12–AC15, a planted tree is built
under `tmp_path` as follows:
- `tests/golden/x.json` exists.
- A row reads `{"fixture": "tests/golden/x.json", "asserted by": "tests/test_901_named.py"}`.
- The planted modules are written directly under `tmp_path / "tests"`.
- Each AC plants only the modules it names.

- [ ] **AC11: every reader of a live `tests/golden/` fixture is named in its
  row.** `_unnamed_golden_readers` returns `[]` when called with the
  Section-1 rows parsed from `docs/aide/golden-decision-table.md` and the
  repository root.
- [ ] **AC12: a string-constant reader is reported.** The planted
  `tests/test_900_reader.py`, whose code holds
  `P = Path(__file__).parent / "golden" / "x.json"`, makes the result equal
  `[("tests/golden/x.json", "tests/test_900_reader.py")]`.
- [ ] **AC13: a shared-attribute reader is reported.** The planted
  `tests/helper_mod.py` binds `GOLDEN_PATH = Path(__file__).parent / "golden" / "x.json"`
  at module level. The planted `tests/test_902_attr.py` contains
  `import helper_mod` and `helper_mod.GOLDEN_PATH.read_text()`, and no
  literal naming `x.json`. Together they make the result equal
  `[("tests/golden/x.json", "tests/test_902_attr.py")]`.
- [ ] **AC14: a `setattr` reader is reported.** With the same `helper_mod.py`,
  the planted `tests/test_903_setattr.py` contains
  `monkeypatch.setattr(helper_mod, "GOLDEN_PATH", tmp_path)` and no literal
  naming `x.json`. It makes the result equal
  `[("tests/golden/x.json", "tests/test_903_setattr.py")]`.
- [ ] **AC15: a docstring-only mention is not a reader.** The planted
  `tests/test_904_doc.py`, whose only mention of `x.json` is in its module
  docstring, makes the result equal `[]`.

## Assumptions

- **A1 (owner decision, 2026-10-12).** The guard widening reaches inline
  operands, function-local bound names and module-level bound names. The
  three live comparisons it newly reaches are cleared by one `ALLOWLIST`
  entry for `tests/corpus/119_pre_119_digests.json` under ground
  `integrity-pin`. They are not cleared by rewriting the tests. The fixture
  is a recorded sha256 hex digest, compared as a string against the same
  digest recomputed, so an exact comparison is correct. The entry's reason
  string must not contain `143`, which
  `tests/test_143_s_axis_correction.py:624` forbids in any reason. The
  fixture is already pinned `text eol=lf` in `.gitattributes`, so
  `test_127`'s AC14 holds without a `.gitattributes` edit.
- **A2 (orchestrator default, 2026-10-12).** The test_155 leg is test-only.
  Item 209 closed the behaviour on the base. AC5–AC10 are regression pins
  that pass on day one. A failure in any of them means the scanner
  regressed, never that this item's build is incomplete.
- **A3 (owner decision, 2026-10-12): what "reads the fixture" means.** Only a
  module directly under `tests/` whose file name matches
  `test_\d+\w*\.py` can be a reader. That is the form the `asserted by`
  column's `_MODULE_NAME_RE` can name. Such a module reads the fixture if its
  AST has any of:
  - (i) a `str` constant containing the fixture's file name (for example
    `report_format_contract.json`) that is not a module, class or function
    docstring;
  - (ii) an `ast.Attribute` whose `attr` is a *bound name*;
  - (iii) a `str` constant exactly equal to a bound name, as in
    `setattr(mod, "GOLDEN_PATH", …)`.

  A *bound name* is the target of a module-level single-name assignment in
  any `*.py` directly under `tests/`, helpers included, whose value
  expression contains a `str` constant containing the fixture's file name.
  Today the bound names are `GOLDEN_PATH`, `GOLDEN_REL` and
  `_FORMAT_FIXTURE`. Comments are invisible to the AST and never count. Only
  rows whose `fixture` starts with `tests/golden/` and exists on disk under
  `repo_root` are checked. The retired `016_features_report.json` and
  `022_stage3_report.json` rows are therefore skipped: test_126 names their
  file names as AC17 needles, and that is not a read.
- **A4: the reverse-check interface the tests read.**
  - The builder adds `_unnamed_golden_readers(rows, repo_root)` to
    `tests/test_105_golden_decision_table.py`, the module that owns the
    column's forward check (AC6).
  - `rows` is a list of dicts carrying at least the `"fixture"` and
    `"asserted by"` keys, as test_105's `_parse_first_pipe_table` yields
    them.
  - `repo_root` is a `pathlib.Path`, and the scan reads `repo_root / "tests"`.
  - It returns a sorted `list` of `(fixture, module)` tuples. `module` is
    spelled `"tests/<file name>"`, and only readers the row does not name
    are included.
  - A row names a module when `_MODULE_NAME_RE.findall(cell)` (the existing
    test_105 regex) yields it. A bare module path and a `module::function`
    form both count.
  - Tests import it as `import test_105_golden_decision_table as t105`, the
    way `test_184` imports `test_155`.
- **A5 (measured 2026-10-12): live readers of `tests/golden/report_format_contract.json`
  under A3.** The readers are test_016, test_022, test_111, test_126 and
  test_135. The row names the first four, so AC11 fails on the base until
  the row gains test_135.

## Implementation Steps

1. **`tests/committed_artifact_guard.py`, parsed-value resolution.** Add
   `_unwrap_parsed(node)`. It strips any chain of `ast.Subscript` and
   `<x>.get(...)` calls. If what remains is `json.loads(<arg>)` with exactly
   one positional argument, it returns `<arg>`; otherwise it returns what
   remains. Use it in `_resolve_operand`, after the existing direct-read
   check:
   - an unwrapped node that `_extract_path_expr_from_read` recognises is
     resolved through `_resolve_expr`, as today;
   - an unwrapped `ast.Name` found in `read_results` returns that entry.

   Reuse `_extract_path_expr_from_read` and `_resolve_expr` unchanged.
2. **Function-local bindings.** In `_classify_function`'s pre-scan, record a
   name in `local_reads` when its assigned value, after `_unwrap_parsed`, is
   a recognised read that resolves. The existing rebind rule stays: a later
   unrelated assignment pops the name. Seed `local_reads` from the
   module-level reads in step 3, minus every parameter name of the function
   (`func.args`: posonly, args, kwonly, vararg, kwarg), so that a parameter
   shadowing a module-level name is never resolved.
3. **Module-level bindings.** Add `_module_level_reads(tree, known, depths)`,
   which returns `{name: committed_path}`. It applies the same unwrap to
   every module-level single-name `ast.Assign`, and a later module-level
   rebind of the name drops it. `classify_module` calls it after
   `_module_level_paths` and passes the result to `_classify_function`.
   **Do not change `_module_level_paths`'s `(known, depths)` return shape**:
   `tests/test_185_guard_os_path_root.py:130` unpacks it.
4. **`ALLOWLIST` entry** (A1). Add `path="tests/corpus/119_pre_119_digests.json"`,
   `ground="integrity-pin"`, with a one-line reason that names item 119 and
   says the payload is one sha256 hex digest compared as a string. The
   reason must not contain `143`. `GROUNDS` stays at six members.
5. **Guard docstring.** Update the "Precise, not exhaustive" paragraph to name
   the new resolution: `json.loads` over a recognised read, subscript and
   `.get()` chains, and module-level bound read names. Leave every "Still
   skipped in silence" entry as it is. Its `json.loads` entry is
   `(Path(json.loads(arg)) / ARTIFACT).read_bytes()`, a *root* reached through
   `json.loads`, and it stays skipped. `tests/test_158_committed_artifact_guard_resolver.py`
   AC12 renders and checks every entry.
6. **`tests/test_105_golden_decision_table.py`.** Add
   `_unnamed_golden_readers(rows, repo_root)` per A3 and A4, beside AC6's
   section. Use stdlib `ast` and `re` only, and reuse the module's
   `_MODULE_NAME_RE`. Add no test function: the tests are test-writer's, in
   `tests/test_225_guard_blind_spots.py`.
7. **`docs/aide/golden-decision-table.md`.** In the Section-1 row for
   `tests/golden/report_format_contract.json`, append
   `, tests/test_135_stage29_validation.py::test_ac2_replacement_iv_format_fixture_builder_resolves`
   to the `asserted by` cell. Change no other cell or row. The file is
   pinned `text eol=lf`, so keep `\n` line endings.
8. No change to `tests/test_155_corpus_case_kind.py` (A2). No dependency is
   added.

## Authorised paths

**May change:**

- `tests/committed_artifact_guard.py` — parsed and module-level read resolution, the `ALLOWLIST` entry, and the docstring (steps 1–5)
- `tests/test_105_golden_decision_table.py` — the `_unnamed_golden_readers` helper (step 6)
- `docs/aide/golden-decision-table.md` — the golden row's `asserted by` cell gains test_135 (step 7)
- `tests/test_225_guard_blind_spots.py` — this item's tests

**Asserts against:**

- `tests/test_155_corpus_case_kind.py` — AC5–AC10 call its `_zero_comparisons` unchanged

## Testing Strategy

Test module: `tests/test_225_guard_blind_spots.py`. It imports
`committed_artifact_guard as guard`, `test_155_corpus_case_kind as t155` and
`test_105_golden_decision_table as t105`. Write one test per AC, except AC4,
which is the existing `test_127::test_ac15_…`. AC11 parses the live rows
with `t105._split_sections` and `t105._parse_first_pipe_table` on
`t105._DOC_PATH.read_text(encoding="utf-8")`, taking the
`"Section 1 — Committed test fixtures"` section.

**This module must carry none of the OS-sensitivity signals
`tests/test_213_windows_ci_subset.py`'s `_signals` detects** (amended
2026-10-13, cross-spec review). Any one of them would make test_213 AC5
require `tests/test_225_*` in `.github/workflows/ci.yml`'s `WINDOWS_TESTS`,
and this item does not authorise `ci.yml`. In the module's own code there
must be:
- no `.read_bytes` attribute (read with `read_text(encoding="utf-8")`);
- no `.as_posix` attribute;
- no `os.sep` or `os.path.sep`;
- no `PureWindowsPath` or `PurePosixPath`;
- no `newline=` keyword (write planted modules with
  `write_text(source, encoding="utf-8")`);
- no import of `subprocess`, `run_process` or `segfacet.cli`, and no
  `sys.executable`;
- no string constant starting `segfacet.cli` or containing `.gitattributes`;
- no parameter named `regenerated_failure_modes`, `regenerated_traceability`
  or `aide_check_result`.

Inside a planted snippet's source string, `read_bytes` is only a string
constant, not an attribute, so the `parsed-read-bytes` and
`module-level-raw-read` snippets below stay signal-free. Build expected module
paths with an f-string (`f"tests/{name}"`), not `.as_posix()`.

Adversarial cases, each with the failure mode it guards:

- `get-chain`: `json.loads(Path(REF).read_text()).get("x") == 1` is one
  violation. Guards against `.get()` being missed while subscripts are seen.
- `parsed-read-bytes`: `json.loads(Path(REF).read_bytes())["x"] == 1` is one
  violation. Guards against unwrapping only `read_text`.
- `module-level-raw-read`: a module-level `RAW = Path(REF).read_bytes()`
  compared `RAW == b""` in a function is one violation. Guards against
  module-level tracking that works only through `json.loads`.
- `both-sides-parsed-same-path`:
  `json.loads(Path(REF).read_text())["a"] == json.loads(Path(REF).read_text())["b"]`
  is no violation. Guards against the widening turning a committed-vs-committed
  comparison into a false positive.
- `local-rebind-shadows-module-read`: a module-level
  `DATA = json.loads(Path(REF).read_text())`, then `DATA = {}` inside the
  function before `assert DATA["x"] == 1`, is no violation. Guards against a
  stale module-level binding leaking past a local rebind.
- `parameter-shadows-module-read`: the same module-level `DATA`, with
  `def test_x(DATA): assert DATA["x"] == 1`, is no violation. Guards against
  a parameter being resolved as the module-level read.
- `allowlisted-parsed-read`: AC1's shape against
  `Path("tests/corpus/manifest.json")` is no violation. Guards against the
  widening bypassing allowlist matching.
- `live-idiom-non-vacuity`: with `guard.ALLOWLIST` monkeypatched to drop the
  `tests/corpus/119_pre_119_digests.json` entry,
  `iter_violations(<repo>/tests)` reports at least one violation whose
  `committed_path` is that file. Guards against a widening that passes the
  planted snippets but misses the real multi-line, `encoding=`-keyword idiom.
  It is a lower bound on purpose, so it does not pin other modules' line
  numbers.
- `retired-golden-row-skipped`: a planted row for a `tests/golden/` fixture
  absent from disk, with a planted module naming its file name in code,
  returns `[]`. Guards against the retired 016/022 rows demanding test_126.
- `qualified-name-counts-as-named`: a planted reader named in the row only as
  `tests/test_900_reader.py::test_x` returns `[]`. Guards against the
  `module::function` form not being recognised. The live row uses it.
- `unnumbered-module-not-a-reader`: a planted `tests/test_aide_x.py` and a
  planted `tests/helper_mod.py`, each with a literal naming the fixture, are
  not returned. Guards against demanding a name the column's regex cannot
  hold.

**Existing tests to reconcile.** None found. I searched `tests/` for tests
that pin the guard's old reach: `json.loads` snippets, `ALLOWLIST` size
pins and `_module_level_paths` callers.
- test_149 AC25 and test_158 AC11 narrow the allowlist by path and still see
  only the paths they expect, because the new entry stays in their narrowed
  sets.
- test_158 AC9's normalised-source equivalence holds, because the widening
  treats a module-level name the same before and after its root is inlined.
- test_185 unpacks `_module_level_paths`, whose shape is kept (step 3).

This sweep is a lower bound (see CLAUDE.md, "A spec-time probe … is a lower
bound"), so the builder's full suite run is the check.

## Review findings

- `ac11-live-check-not-vacuous` (minor): the live AC11 check asserted only
  that the rows were non-empty and that the helper returned `[]`, so a change
  in the table's fixture-cell shape could filter every row out and still pass.
  Fix: the same test now strips `tests/test_135_stage29_validation.py` from the
  live `report_format_contract.json` row and asserts the helper then reports
  exactly that module. Test:
  `test_ac11_every_reader_of_live_golden_fixture_is_named`.

## Dependencies

None.

**Downstream:** none. Sibling item 224 edits `tests/test_123_recalibrate_and_regenerate.py`
at AC28, away from line 1608. That comparison is allowlisted here, not
edited, so neither item touches the other's paths. Sibling 226 deletes
`tests/test_021_sagittal_projection.py`, which reads no golden.

## Decisions & Trade-offs

- `_unwrap_parsed` strips subscripts and `.get()` calls, then unwraps a
  one-argument `json.loads`; a shared `_read_target` serves both the function
  pre-scan and the new `_module_level_reads`, so the direct-read and parsed-read
  binding rules cannot drift apart. `_module_level_paths` keeps its return shape.
- Module-level reads seed `local_reads` minus the function's parameters; a local
  rebind pops the name through the existing pre-scan rule.
- `_unnamed_golden_readers` matches a bound name by `ast.Attribute.attr` or an
  exact `str` constant, per A3; docstrings are excluded by node identity.
- A throwaway script (not pytest) confirmed `iter_violations(tests)` and the
  live Section-1 reverse check both return `[]`.

- Review-fix round: `_read_target` takes the read map, so `json.loads(raw)` on a
  name already bound to a read binds the new name to the same path (function
  pre-scan and `_module_level_reads`). Any `Store`-context name or `except ... as`
  name in a function now shadows a module-level read, not only a single-name
  assignment or parameter. `_unnamed_golden_readers` also counts an
  `ast.ImportFrom` alias whose name is a bound name. The throwaway script again
  returned `[]` for the live tree.

- **Left open:** whether the reverse check should extend to keep rows outside
  `tests/golden/`. Measured 2026-10-12, it would demand roughly 200 more
  names, most of them incidental mentions (`tests/corpus/manifest.json`
  alone has 23 unnamed "readers"). A useful version needs a stricter
  definition of "reads" than A3, and that is a decision for a stage of its
  own, not this maintenance item.
