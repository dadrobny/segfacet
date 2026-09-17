<!-- aide-template: item 1 -->
# Item 159 — The prerequisite test and import defects Stage 32 edits

> **Created:** 2026-09-17 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update
> **Queue:** [`../queue/queue-021.md`](../queue/queue-021.md) · Item 159
> **Objectives:** G7
> **Suggested branch:** `aide/159-the-prerequisite-test-and-import`

---

## Description

Roadmap Stage 31 D5, the test-and-import part. The queue line names a set of
located `insights.md` defects in the surfaces Stage 32 edits and tells this
item to **verify before re-fixing**, because items 147–158 repaired several of
them in passing. Each one was measured on `aide/queue-021` at `561a673`
(2026-09-17, item 158 merged) before this spec was written. The table is the
result. Only the rows marked **fix** are work for this item.

The named insight entries are cited by provenance and date, because list
numbers change when the inbox is archived.

| # | Defect (insight entry) | Measured 2026-09-17 | Disposition |
|---|---|---|---|
| D-a | `src/segfacet/__init__.py` imports NumPy/NiBabel eagerly (item 144, 2026-09-03) | **Still present.** In a fresh subprocess, `import segfacet.failure_modes` and `import segfacet.traceability` each load 162 `numpy`/`scipy`/`nibabel` modules. With the package init bypassed (a stub `segfacet` package object carrying only `__path__`), both load **none**. Of the six re-exports in the init, two are heavy: `segfacet.empty` (top-level `import numpy`) and `segfacet.features.fragmentation` (NumPy, SciPy, NiBabel). `verdict`, `human_report` and `feature_report` load none. `report` has no heavy top-level import | **fix** (AC1–AC4) |
| D-b | `test_147::test_ac3_...` "exactly four files mention `MODE_ANCHOR_PATHS`" is broken by a comment in `heuristics/reference_delta.py` (item 147, 2026-09-04) | **Already fixed.** The test now counts files through the AST helper `_references_name`, which ignores comments. `reference_delta.py:133` is a comment, so the set is the four files it expects | pointer: commit `d6efddc` (2026-09-04, item 147) |
| D-c | `test_147::test_ac9_every_mechanism_names_a_token_that_resolves_live[10]` leaves out the candidate feature (item 147, 2026-09-04) | **Already fixed.** The candidate set now includes `{f.path for f in mode.candidate_features}`. Re-running the test's logic outside pytest resolves all 16 modes, with no mode unresolved | pointer: commit `d6efddc` |
| D-d | `test_147::test_ac4_vision_parse_has_one_home` (same entry) | **Item 152's**, as the queue says | pointer: item 152 |
| D-e | `test_136::test_ac8_surplus_declared_mode_is_reported_naming_both` still uses the retired `"corpus"` tag (item 147, 2026-09-04) | **Already fixed.** It now declares `evidence=("test-evidence-item147",)` and a surplus mode outside `SPECIFICATION`'s key set. No `evidence=("corpus"` is left under `src/` or `tests/` | pointer: commit `ef9cb22` (item 147) |
| D-f | `test_143::test_ac16_record_covers_exactly_the_required_artifact_set` is an equality against a set derived live from the manifests (item 143, 2026-09-03) | **Still present, in a new shape.** Item 157 kept it passing through the case-id rename by mapping live ids back through `RENAMED_CASE_IDS` (`_as_of_record_path`). The required set is still derived from both live manifests, though, so the next corpus case added turns a dated 2026-09-03 record red. Today it holds: 27 rows equal 27 derived paths | **fix** (AC5, AC6) |
| D-g | `test_145::test_ac23_...` asserts `committed_ids == {1..8}` (item 146, 2026-09-04) | **Already fixed, in a new shape.** It is now `committed_ids == set(_MODE_IDS)`, with sixteen ids hand-listed. Item 150 put the equality back on purpose because the sign-off closed the catalogue. It compares the committed artifact with the signed-off id list, not with a set derived from the corpus, so adding a corpus case cannot break it | pointer: commit `3cb522f` (item 150). Not re-fixed (A5) |
| D-h | `test_146::test_ac30_...`'s closing `!=` cannot hold by construction (item 146, 2026-09-04) | **Already fixed.** The closing assertion now removes the stub and asserts `specification_conflicts() == ()` | pointer: commit `710f2c6` (item 146) |
| D-i | `test_148`'s `_status_report_module()` lacks `sys.modules[spec.name] = module` (item 148, 2026-09-04) | **Already fixed.** The helper registers the module before `exec_module` and removes it afterwards | pointer: commit `5298f8c` (item 148) |
| D-j | `test_103::test_ac13_...[overlap-...]` match set is empty by construction (same entry) | **Already fixed.** A rule whose every signal path is an anchor path is asserted directly (`signal_paths <= anchor paths`) | pointer: commit `5298f8c`, reconciled again in `3cb522f` |
| D-k | `aide/queue-018` base-ref tests skip forever (item 143, 2026-09-03) | **Already fixed**, as the queue says (D0's pass). Every `aide/queue-018` left under `tests/` is a comment or a docstring. The pinned-SHA skips that remain in `test_132`/`test_134` point at reachable commits (`57b8bf1`, `ca92471`) | pointer: commit `b11cef3` (2026-09-16). A tree-wide guard is added (AC9) |
| D-l | `test_137`'s AC18 invariance tests are vacuous (item 146, 2026-09-04; roadmap D5 names them) | **Already fixed** | pointer: commit `1fa31f8` (already on the entry) |
| D-m | committed-artifact guard blind spots (roadmap D5) | **Item 158's** | pointer: item 158 |
| D-n | `test_146::test_ac36_aide_check_reports_no_error_and_no_new_warning_class` and `test_150::test_ac4_aide_check_reports_no_error_and_no_unfilled_slot` pin `aide check`'s set of warning classes (item 158, 2026-09-17) | **Still present.** Neither is in the queue line. **Taken into scope by this spec** (A6): both are tests that pin live-derived state, which is the defect class D5 exists to remove. They went red twice in this queue (items 155 and 158), and each time a document was reworded to satisfy them. Today `aide check` reports 7 warnings in the four baseline classes, so both pass | **fix** (AC7, AC8) |

**What this item does.** It makes one production change and three test-side
reconciliations:

1. **Lazy re-exports in `segfacet/__init__.py`.** `check_empty`, `CheckResult`
   and `compute_fragmentation_index` are resolved on first access through a
   module-level `__getattr__` (PEP 562, available from Python 3.7). `__all__`
   keeps its twelve names and each name still resolves to the same object.
   Once this lands, the "import-cheap" claims already made in the docstrings
   of `failure_modes.py` and `traceability.py` are true, and those docstrings
   are not edited.
2. **`test_143` AC16** compares the record against a path set frozen in the
   test module: the 27 paths as of the 2026-09-03 record, pre-item-157 names.
   It no longer derives that set from the live manifests.
3. **`test_146` AC36 and `test_150` AC4** stop asserting that the classes of
   the live warnings are a subset of a recorded baseline. The error half and
   the other negatives in each test stay. What claim replaces the retired
   assertion is written at the retirement site.
4. The item-144 subprocess test in **`test_144`** is reconciled to the fixed
   tree. Today it *requires* a bare `import segfacet` to load a heavy module.

**Not in scope:** anything under "Already fixed" (no re-fix); the
`os.path.dirname(os.path.abspath(__file__))` guard root (item 158,
2026-09-17, a gap entry for item 160's triage); the engine behaviour where
`aide progress set` splits a shared deliverable bullet into copies with
identical prose (a framework concern, see A7); any mode, rule or corpus
content.

## Acceptance Criteria

- [ ] **AC1: failure_modes imports light.** In a fresh `sys.executable`
  subprocess (cwd = repo root), `import segfacet.failure_modes` leaves
  `sys.modules` with no key whose first dotted component is `numpy`, `scipy`
  or `nibabel`.
- [ ] **AC2: traceability imports light.** In a fresh `sys.executable`
  subprocess, `import segfacet.traceability` leaves `sys.modules` with no key
  whose first dotted component is `numpy`, `scipy` or `nibabel`.
- [ ] **AC3: public surface unchanged.** After `import segfacet`, the set
  `segfacet.__all__` equals `{"__version__", "Severity", "Reason", "Verdict",
  "CheckResult", "check_empty", "serialize_report", "serialize_report_json",
  "render_human_report", "render_feature_table", "build_features_block",
  "compute_fragmentation_index"}`. For every name in it other than
  `__version__`, `getattr(segfacet, name)` is the same object (`is`) as the
  attribute of that name on its defining module (`segfacet.verdict`,
  `segfacet.empty`, `segfacet.report`, `segfacet.human_report`,
  `segfacet.feature_report`, `segfacet.features.fragmentation`).
- [ ] **AC4: unknown attribute still raises.** `getattr(segfacet,
  "no_such_attribute_159")` raises `AttributeError`.
- [ ] **AC5: the S-axis record check survives a new corpus case.** The
  `test_143` AC16 check passes when both corpus manifests it could read carry
  one extra synthetic case with fixture paths that are not in the record. The
  extra case is injected into copies, never into the committed manifests.
- [ ] **AC6: the S-axis record check keeps its force.** The `test_143` AC16
  check fails when it is run against a copy of
  `docs/corpus-s-axis-correction.md` with one of its 27 data rows removed.
- [ ] **AC7: test_146 no longer pins the warning-class set.**
  `test_146::test_ac36_aide_check_reports_no_error_and_no_new_warning_class`,
  or the test that replaces it at that site, passes when `run_checks` returns
  the live warnings plus one warning of a shape no classifier recognises. Use
  the literal `"progress.md: 2 deliverable bullets with identical prose,
  attributed to item 999"`.
- [ ] **AC8: test_150 no longer pins the warning-class set.**
  `test_150::test_ac4_aide_check_reports_no_error_and_no_unfilled_slot`
  passes when `run_checks` returns the live warnings plus the same
  unrecognised warning as AC7.
- [ ] **AC9: test_150 still catches an unfilled slot.**
  `test_150::test_ac4_aide_check_reports_no_error_and_no_unfilled_slot`
  fails when `run_checks` returns the live warnings plus a warning containing
  `"unfilled template slot"`.
- [ ] **AC10: no git-ref use of the deleted queue-018 branch.** Across every
  `tests/**/*.py`, no string constant that is not a docstring contains the
  substring `aide/queue-018`. The check builds that substring by
  concatenation, so the module that holds it does not match itself.
- [ ] **AC11: the already-fixed tests were kept, not deleted.** Each of these
  function names is defined at module level in its module, checked by AST:
  `test_147_specification_is_the_record.py`
  `test_ac3_mode_anchor_paths_stays_under_its_own_metric_label` and
  `test_ac9_every_mechanism_names_a_token_that_resolves_live`;
  `test_136_rule_mode_declarations.py`
  `test_ac8_surplus_declared_mode_is_reported_naming_both`;
  `test_145_eight_hypothesised_modes.py`
  `test_ac23_fresh_matches_committed_structurally_and_carries_every_signed_off_id`;
  `test_146_ninth_mode_and_first_proposed.py`
  `test_ac30_proposed_entry_acquiring_a_declaring_rule_is_reported`;
  `test_148_per_path_mode_attribution.py` `_status_report_module`;
  `test_103_feature_catalogue.py`
  `test_ac13_rule_mode_map_effect_on_failure_modes`.

No AC here closes a Stage 31 acceptance criterion. D5 has no acceptance line
of its own in `progress.md`.

## Assumptions

- **A1:** "Import-light" means no `numpy`, `scipy` or `nibabel` root in
  `sys.modules`. The queue names NumPy and NiBabel. SciPy is added because
  `test_144`'s existing `_HEAVY_ROOTS` already treats all three as heavy, and
  `features.fragmentation` loads all three.
- **A2:** The fix is PEP-562 lazy re-exports, not dropping the re-exports.
  The queue requires that `import segfacet` "keeps its public surface", and
  `tests/test_025_fragmentation_index.py:165-172` pins
  `segfacet.compute_fragmentation_index`. Only the two heavy sources become
  lazy: `segfacet.empty` (the `check_empty` and `CheckResult` names) and
  `segfacet.features.fragmentation`. The four cheap imports stay eager. A
  bare `import segfacet` also becomes light as a result, but no AC pins that,
  since the queue does not ask for it.
- **A3:** The frozen AC16 set is the 27 paths the record holds today. They
  were measured equal to the live-derived set on 2026-09-17 at `561a673`,
  using pre-item-157 case names. Freezing that set is exact, not an
  approximation. If `_as_of_record_path` has no remaining caller, it may be
  removed with the derivation.
- **A4:** An assertion whose only job was the retired class pin is retired
  with it. In `test_146` AC36 that means `assert warnings, "... expected the
  baseline"`, and the whole test if nothing else is left in it. In `test_150`
  AC4 it means the `classes <= _BASELINE_WARNING_CLASSES` assertion and the
  `assert warnings` line. These are claims about live warnings that may
  legitimately disappear. The `errors == []` claim is already kept by
  `tests/test_aide_check_no_errors.py`. `test_150`'s unfilled-slot negative
  and its gate-section doubled-brace check are kept. `_classify_warning` stays in both
  modules because other tests use it (`test_146:1512`, `:1526`;
  `test_150:415`, `:420`). `_BASELINE_WARNING_CLASSES` is removed wherever it
  ends up unused.
- **A5:** D-g is not re-fixed. `committed_ids == set(_MODE_IDS)` is an
  equality between a committed artifact and the signed-off catalogue's id
  list, and item 150 chose it on purpose. A new *corpus* case cannot break
  it, and a new *mode* changing it is the intended signal. That is a
  different claim from D-f's dated record.
- **A6:** D-n (the pin in `test_146`/`test_150`) is in scope although the
  queue line does not name it. Roadmap D5 is "the open `defect` entries in
  the surfaces Stage 32 edits", and this entry is an open `defect`. It
  belongs to the class the queue's own testable line targets: a test that
  pins state derived live, which a later legitimate change turns red. It
  also went red twice in this queue. Leaving it open means item 160 or 161
  meets it again on its first `aide progress set`.
- **A7 (engine 1.52.1):** `aide progress set` splitting a shared `*(Items A,
  B)*` bullet into copies with identical prose, and the warning that
  follows, is engine behaviour. This item does not change it. Item 159's own
  D5 bullet in `progress.md` is attributed to item 159 alone (measured
  2026-09-17), so its status changes cannot trigger that split. If a split
  happens anyway, the builder rewords each copy for its own item rather than
  re-pinning a class.
- **A8 (engine 1.52.1):** `aide insights tick N --pointer P` on an entry
  that is already ticked appends a dated trail line and does not re-tick
  (`aide insights -h`). The trail lines in step 5 rely on this.
- **A9 (engine 1.52.1):** `run_checks(repo_root, config)` returns
  `(errors, warnings)` as lists of strings. AC7–AC9 inject a warning by
  wrapping the `_aide_module()` loader in the target module, or an
  equivalent seam, so that its `run_checks` appends to the live result.

## Implementation Steps

1. **Builder — `src/segfacet/__init__.py`.** Keep `__version__ = "0.0.1"` as
   a literal on its own line, because hatch reads it by regex. Keep the eager
   imports from `verdict`, `report`, `human_report` and `feature_report`.
   Remove the eager `from segfacet.empty import …` and
   `from segfacet.features.fragmentation import …`. Add a module-level
   `__getattr__(name)` that maps `check_empty`/`CheckResult` to
   `segfacet.empty` and `compute_fragmentation_index` to
   `segfacet.features.fragmentation`. It imports the target with
   `importlib.import_module`, caches the value in `globals()`, returns it,
   and raises `AttributeError(f"module 'segfacet' has no attribute {name!r}")`
   for any other name. `__all__` is unchanged. Add one sentence to the module
   docstring saying why the two re-exports are lazy.
2. **Test-writer — `tests/test_144_failure_mode_specification.py`.** Reconcile
   `test_ac1_import_adds_no_heavy_module_beyond_the_package_init` to the fixed
   tree. Drop `assert heavy_bare, ...`, which pins the defect. Assert instead
   that `import segfacet.failure_modes` loads no heavy root. Renaming the test
   is allowed. Its docstring's "the package init's own cost" parenthetical
   goes with the change.
3. **Test-writer — `tests/test_143_s_axis_correction.py`.** Replace the
   manifest derivation in `_required_artifact_paths()` with a module-level
   frozen set of the 27 record paths, taken from the table rows as they stand.
   Add a comment that dates it (2026-09-03 record, pre-item-157 ids, frozen
   2026-09-17 by item 159). Remove `_as_of_record_path`, and the
   `RENAMED_CASE_IDS` import if no other test uses them. Structure it so AC5
   and AC6 can drive the check against substituted inputs, for example by
   giving the helper and the record loader path parameters that default to
   the committed files.
4. **Test-writer — `tests/test_146_ninth_mode_and_first_proposed.py` and
   `tests/test_150_maintainer_sign_off.py`.** Retire the class-subset pin per
   A4. At the retirement site, leave one comment naming what holds the
   remaining claim (`tests/test_aide_check_no_errors.py` for errors) and why
   the warning set is not pinned: §6, plus the item-158 insight dated
   2026-09-17.
5. **Builder — `docs/aide/insights.md`, through the verb only.** Tick the
   open `defect` entry (item 158, 2026-09-17) about the two `_classify_warning`
   pins with `aide insights tick <N> --pointer "item 159"`. For each entry
   already ticked `→ item 159` that turned out to be fixed earlier, append a
   trail line with `aide insights tick <N> --pointer "<commit> (verified by
   item 159)"`, using the commit from the table: item 146 2026-09-04 AC23 →
   `3cb522f`; item 146 2026-09-04 AC30 → `710f2c6`; item 147 2026-09-04
   surplus-mode → `ef9cb22`; item 147 2026-09-04 three `test_147` checks →
   `d6efddc` (plus item 152 for `test_ac4`); item 148 2026-09-04 two tests →
   `5298f8c`. Find `<N>` with `aide insights list` at build time, never from
   this spec.
6. Record in Decisions & Trade-offs the `sys.modules` counts before and after,
   measured in a subprocess.

## Authorised paths

**May change:**

- `src/segfacet/__init__.py` — the lazy re-exports (D-a)
- `tests/test_159_prerequisite_test_and_import_defects.py` — this item's own test module
- `tests/test_144_failure_mode_specification.py` — reconcile the item-144 subprocess test that pins the eager import
- `tests/test_143_s_axis_correction.py` — freeze AC16's required set (D-f)
- `tests/test_146_ninth_mode_and_first_proposed.py` — retire the warning-class pin (D-n)
- `tests/test_150_maintainer_sign_off.py` — retire the warning-class pin (D-n)

**Asserts against:**

- `docs/corpus-s-axis-correction.md` — AC5/AC6 read its 27 rows (AC6 through a copy)
- `tests/corpus/manifest.json` — AC5 copies it and adds a case
- `tests/corpus/intensity/manifest.json` — AC5 copies it and adds a case
- `src/segfacet/failure_modes.py` — AC1 imports it in a subprocess
- `src/segfacet/traceability.py` — AC2 imports it in a subprocess
- `src/segfacet/empty.py` — AC3 identity of `check_empty`/`CheckResult`
- `src/segfacet/features/fragmentation.py` — AC3 identity of `compute_fragmentation_index`
- `.aide/scripts/aide.py` — AC7–AC9 call its `run_checks` through the target tests' loader
- `tests/test_147_specification_is_the_record.py` — AC11 AST presence
- `tests/test_136_rule_mode_declarations.py` — AC11 AST presence
- `tests/test_145_eight_hypothesised_modes.py` — AC11 AST presence
- `tests/test_148_per_path_mode_attribution.py` — AC11 AST presence
- `tests/test_103_feature_catalogue.py` — AC11 AST presence

## Testing Strategy

Module: `tests/test_159_prerequisite_test_and_import_defects.py`, one test per
AC plus these adversarial cases:

- **AC1/AC2:** run in a subprocess through `tests/run_process.py::run_utf8`,
  never in-process, because the suite's own imports would hide the result.
  Assert the subprocess succeeded and printed a non-empty module list
  *before* asserting that nothing heavy is in it (§6). Negative control: the
  same helper run on `import segfacet.features.fragmentation` reports
  `numpy`. Without it, a helper that always returns an empty set would pass.
- **AC3:** also do a fresh-subprocess `from segfacet import check_empty,
  CheckResult, compute_fragmentation_index`, which covers the `from`-import
  path of PEP 562 and exits 0.
- **AC4:** check that the message names the attribute.
- **AC5/AC6:** work under `tmp_path` only. Nothing is written to `tests/corpus/`
  or `docs/`. For AC5, check that the injected paths really are absent from
  the record, so the test cannot pass on a no-op injection. For AC6, check
  that the removed row really was one of the 27.
- **AC7–AC9:** load `test_146`/`test_150` with
  `importlib.util.spec_from_file_location` under a unique module name, so
  pytest does not collect them twice. Monkeypatch the loaded module's
  `_aide_module` to return a wrapper whose `run_checks` appends the injected
  warning. Call the target test function directly and expect no exception
  for AC7/AC8 and an `AssertionError` for AC9. Guard against vacuity: check
  that the wrapper was actually called and that the injected warning is in
  what it returned.
- **AC10:** walk every `tests/**/*.py` with `ast`. Drop constants that are
  the first statement of a module, class or function body (docstrings).
  Build the needle as `"aide/" + "queue-018"`. Negative control: a planted
  snippet `subprocess.run(["git", "diff", "aide/queue-018"])`, parsed from a
  string, is flagged.
- **AC11:** positive per name. Negative control: a name that is not defined
  is reported absent.

**Existing tests to reconcile** (a stale assumption the fix falsifies):

- `tests/test_144_failure_mode_specification.py::test_ac1_import_adds_no_heavy_module_beyond_the_package_init`
  — `assert heavy_bare` pins the eager import and goes red once D-a lands
  (step 2).
- `tests/test_025_fragmentation_index.py` (around line 165) pins
  `compute_fragmentation_index` in `__all__` and callable. It is expected to
  stay green unchanged under the lazy export, and is **not** authorised for
  edits. If it goes red, hand back.
- Swept 2026-09-17: nothing else under `tests/` names `segfacet.check_empty`,
  `segfacet.CheckResult`, `segfacet.compute_fragmentation_index` or `from
  segfacet import` one of the heavy names.

## Validation

1. Run the full suite from the item branch:
   `.venv/bin/python -m pytest -n auto`. It must be green, with no new skip.
2. Run `.venv/bin/python -c "import sys, segfacet.failure_modes; print(sorted({m.split('.')[0] for m in sys.modules} & {'numpy','scipy','nibabel'}))"`
   and the same command for `segfacet.traceability`. Each must print `[]`.
   Before the fix each printed all three.
3. `python .aide/scripts/aide.py check` must report no error and no warning
   naming a path this item changed.
4. `python .aide/scripts/aide.py insights list --trail` must show the item-158
   `_classify_warning` entry ticked `→ item 159`, and the five trail lines
   from step 5.

## Dependencies

- Item 152 — retired `test_147::test_ac4_vision_parse_has_one_home` and the
  vision-seed tests (D-d).
- Item 157 — renamed the corpus case ids and added `_as_of_record_path` to
  `test_143`, which is the shape this item freezes (D-f).
- Item 158 — the committed-artifact guard resolver, which `test_143`/`test_144`
  must stay clean under (D-m), and the 2026-09-17 insight this item absorbs
  (D-n).

**Downstream:** item 160 counts this item's ticks and trail lines, and item
161 replays `aide check` without a warning-class pin.

## Decisions & Trade-offs

To be updated during implementation.
