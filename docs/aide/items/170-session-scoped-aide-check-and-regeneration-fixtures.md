<!-- aide-template: item 2 -->
# Item 170 — Session-scoped `aide check` and specification-regeneration fixtures

> **Created:** 2026-09-23 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-023.md`](../queue/queue-023.md) · Item 170
> **Objectives:** G7
> **Suggested branch:** `aide/170-session-scoped-aide-check-and`

---

## Description

Roadmap Stage 33 D0, first bullet. The `automation` entry in `insights.md`
dated 2026-09-18 measured the suite at 8989 tests in 8m35s (`-n 4`, Linux)
against 4m51s on 2026-09-01. Two repeated-work clusters account for about 5
of the ~34 CPU-minutes:

- **(a) the whole `aide check`.** Eleven tests call `run_checks` in-process
  on the live repository, at 11–13 s each. A twelfth,
  `test_146::test_adv_aide_check_exits_zero`, runs it as a subprocess.
- **(b) specification and traceability regeneration.** Twenty-one tests call
  `segfacet.failure_modes.main` or `segfacet.traceability.main` into a
  temporary directory, 33 regenerations in all, at 7–27 s each. Some call it
  once to compare against the committed artifact, some twice for a run-to-run
  comparison, and a few do both.

Stage 33 regenerates the corpus and every downstream artifact several times
(items 173–177), so each saved regeneration is saved again on every one of
those items.

**What this item delivers.**

1. **Three session-scoped fixtures in `tests/conftest.py`.**
   `aide_check_result` holds one in-process `run_checks` result.
   `regenerated_failure_modes` and `regenerated_traceability` each run their
   regenerator's `main` twice, into two distinct temporary destinations, and
   capture the committed pair's bytes before the first run. The logic lives
   in a plain helper module, `tests/session_artifacts.py`, and the fixtures
   are thin wrappers over it (A3).
2. **The migration.** Each test in list **M** (below) takes its expensive
   input from one of those fixtures instead of computing it. Its assertions
   keep their meaning: the same comparisons run on the same kinds of bytes.
3. **The removal.** The five tests in list **R** are removed, not ported.
   Four of them pin `aide check`'s warning set, which is the per-item shape
   retired on 2026-09-16. The fifth is the non-vacuity guard of one of those
   four. Helpers left unused by the removal go with them.

**List M — migrated tests** (module: functions):

- *`aide check` cluster → `aide_check_result`:*
  - `tests/test_aide_check_no_errors.py`: `test_aide_check_reports_no_errors`
  - `tests/test_146_ninth_mode_and_first_proposed.py`:
    `test_ac36_aide_check_reports_no_error_and_no_new_warning_class`
  - `tests/test_150_maintainer_sign_off.py`:
    `test_ac4_aide_check_reports_no_error_and_no_unfilled_slot`,
    `test_ac4_gate_warnings_feed_run_checks`
  - `tests/test_159_prerequisite_test_and_import_defects.py`:
    `test_ac7_test_146_no_longer_pins_the_warning_class_set`,
    `test_ac8_test_150_no_longer_pins_the_warning_class_set`,
    `test_ac9_test_150_still_catches_an_unfilled_slot`
- *Failure-mode specification cluster → `regenerated_failure_modes`:*
  - `tests/test_144_failure_mode_specification.py`:
    `test_ac17_redirected_run_leaves_committed_artifacts_untouched`,
    `test_ac18_artifacts_are_byte_reproducible_run_to_run`,
    `test_adv_main_called_twice_is_deterministic`
  - `tests/test_145_eight_hypothesised_modes.py`:
    `test_ac23_regeneration_is_byte_reproducible_run_to_run`
  - `tests/test_146_ninth_mode_and_first_proposed.py`:
    `test_ac32_specification_artifacts_regenerate_byte_identically_run_to_run`
  - `tests/test_147_specification_is_the_record.py`:
    `test_ac23_new_fields_reach_both_artifacts`,
    `test_ac24_all_three_artifact_pairs_regenerate_byte_identically` (its
    failure-mode half; its traceability half is in the next cluster)
  - `tests/test_150_maintainer_sign_off.py`:
    `test_ac11_artifacts_are_byte_identical_to_a_fresh_regeneration`,
    `test_ac11_two_successive_regenerations_agree_byte_for_byte`
  - `tests/test_157_case_id_rename.py`:
    `test_ac16_failure_mode_specification_artifacts_regenerate_identically`
- *Traceability cluster → `regenerated_traceability`:*
  - `tests/test_138_traceability_matrix.py`:
    `test_ac2_main_redirects_writes_and_leaves_committed_artifacts_unchanged`,
    `test_ac3_artifacts_are_byte_reproducible_run_to_run`
  - `tests/test_143_s_axis_correction.py`:
    `test_ac11_traceability_matrix_regenerates_byte_identically`,
    `test_ac12_traceability_matrix_json_matches_committed`,
    `test_ac15_traceability_matrix_markdown_matches_committed_byte_for_byte`
  - `tests/test_146_ninth_mode_and_first_proposed.py`:
    `test_ac33_downstream_artifacts_regenerate_byte_identically_run_to_run`
    (its traceability half; the `catalogue.main` half stays in the test),
    `test_ac33_traceability_matrix_matches_committed_structurally`
  - `tests/test_147_specification_is_the_record.py`:
    `test_ac24_all_three_artifact_pairs_regenerate_byte_identically` (its
    traceability half; the `catalogue.main` half stays in the test)
  - `tests/test_148_per_path_mode_attribution.py`:
    `test_ac18_traceability_untouched_and_paths_derived_from_consuming_rules`
    (the `main` run only; its `build_matrix()` call stays)
  - `tests/test_149_conformance_report.py`:
    `test_ac20_both_artifacts_regenerate_byte_identically_run_to_run`,
    `test_ac20_fresh_matches_committed_byte_for_byte`
  - `tests/test_157_case_id_rename.py`:
    `test_ac17_traceability_matrix_artifacts_regenerate_identically`

**List R — removed tests:**

- `tests/test_128_relocation_checks.py`:
  `test_ac23_aide_check_emits_no_gitattributes_lint_warning`
- `tests/test_134_decision_table_evidence_companion.py`:
  `test_ac7_aide_check_names_neither_new_path`
- `tests/test_146_ninth_mode_and_first_proposed.py`:
  `test_ac36_no_warning_names_a_path_this_item_writes`,
  `test_adv_unclassified_warning_would_be_caught`
- `tests/test_149_conformance_report.py`:
  `test_ac22_aide_check_reports_no_gitattributes_warning_for_these_paths`

**Not in scope:**

- The tests that run a regenerator under a patch, whose subject is `main`'s
  own I/O (A4).
- The subprocess `aide check` run (A6).
- Direct `specification_to_dict()`, `render_markdown()` and `build_matrix()`
  calls.
- The two slow singles the insight names, `test_126` AC12 and `test_113`
  AC7's setup.
- Any production code: nothing under `src/segfacet/` changes.

Each item on this list is a `Left open` line below.

## Acceptance Criteria

No AC here closes a Stage 33 acceptance criterion. D0 has no acceptance line
of its own.

- [ ] **AC1: the three fixtures are session-scoped.** In `tests/conftest.py`,
  each of `aide_check_result`, `regenerated_failure_modes` and
  `regenerated_traceability` is a module-level function decorated
  `@pytest.fixture(scope="session")`. The test checks this by AST. *Why:* a
  function-scoped fixture would re-run the work for every consumer, and the
  item would deliver no saving.
- [ ] **AC2: the `aide check` helper returns the run as immutable tuples.**
  `session_artifacts.load_aide_check_result(stub)` equals
  `AideCheckResult(errors=("e1",), warnings=("w1", "w2"))`, where `stub` is a
  temporary `aide.py` stand-in. The stub defines `find_repo_root`,
  `load_config` and a `run_checks` that returns `(["e1"], ["w1", "w2"])`.
  *Why:* every consumer in list M reads this shape. Tuples stop one consumer
  from mutating the result that the others share, and tuple-to-list equality
  is `False` in Python, so the equality also pins the type.
- [ ] **AC3: the regeneration helper returns exactly what its two runs
  produced.** Call `session_artifacts.regenerate(stub_main, committed_json,
  committed_md, out_dir)` with a `stub_main` that records its argv,
  overwrites both committed stand-ins with new bytes, and returns `0` on the
  first call and `7` on the second. The helper returns a `Regeneration` equal
  to one built from the stub's own record: `json_a`/`md_a` are the first
  call's `--json`/`--md` destinations, `json_b`/`md_b` are the second call's,
  `exit_codes == (0, 7)`, and `committed_json_before`/`committed_md_before`
  are the stand-ins' bytes from before the first call. *Why:* the run-to-run
  tests read `*_a` against `*_b`, the "untouched" tests read the before
  bytes, and `test_143`/`test_150` read the exit codes.
- [ ] **AC4: the two runs write to four distinct paths.** In the
  `Regeneration` returned under AC3's stub, `{json_a, md_a, json_b, md_b}`
  has four members, and each of them is inside `out_dir`. *Why:* if the two
  runs shared a destination, every run-to-run test in list M would compare a
  file with itself and pass while checking nothing.
- [ ] **AC5: no migrated test regenerates.** Every function in list M is
  defined at module level in its module, and none of them contains an
  `ast.Call` whose `func` is an `ast.Attribute` with `attr == "main"`,
  unless the receiver is the name `catalogue`. *Why:* this is the
  regeneration half of the migration. A function in M that still calls a
  regenerator is still a slow test. Every regeneration call in list M is
  direct today, so a per-function check is enough.
- [ ] **AC6: the warning-set pins are gone.** No function in list R is
  defined at module level in its module. *Why:* this is the removal the
  queue line asks for. Each of those tests is also a whole `aide check` run.
- [ ] **AC7: no `aide check` run is left in the touched modules.** None of
  these modules contains an `ast.Call` anywhere (helpers and class methods
  included) whose `func` is an `ast.Attribute` with `attr == "run_checks"`:
  - `tests/test_aide_check_no_errors.py`
  - `tests/test_128_relocation_checks.py`
  - `tests/test_134_decision_table_evidence_companion.py`
  - `tests/test_146_ninth_mode_and_first_proposed.py`
  - `tests/test_149_conformance_report.py`
  - `tests/test_150_maintainer_sign_off.py`
  - `tests/test_159_prerequisite_test_and_import_defects.py`

  *Why:* the `aide check` half of the migration. It is module-wide and not
  per-function, because today's calls sit in helpers
  (`_aide_check_errors`, `_aide_check_warnings`) and in `test_159`'s
  `_InjectingAide.run_checks`. A per-function check of list M would pass
  while those helpers still ran the whole check.

## Assumptions

- **A1: "one" means one per pytest process.** Under pytest-xdist (`-n auto`
  in `aide.toml`, `-n 4` in CI), each worker computes a session fixture at
  most once, and only if some test on that worker requests it. The item does
  not share results across workers. That would need a lock-and-cache file,
  which means adding a dependency (`filelock`) or hand-rolling locking. The
  cost ceiling is therefore one `aide check` and four regenerations per
  worker, down from 11 and 33 across the suite.
- **A2: one fixture per regenerator, not one for both.** The queue says "one
  session-scoped regeneration fixture". This spec reads that as one per
  artifact pair, so a worker whose tests need only one pair does not pay for
  the other. Each fixture runs its `main` twice, as the queue asks, so the
  run-to-run tests compare two independent runs.
- **A3: the interface. This spec pins it, and test_170 and every migrated
  test read it.** A plain module, `tests/session_artifacts.py`, defines:
  - `class AideCheckResult(NamedTuple)`, with fields `errors: Tuple[str,
    ...]` and `warnings: Tuple[str, ...]`.
  - `def load_aide_check_result(aide_script: Path = <repo>/.aide/scripts/aide.py) -> AideCheckResult`.
    It loads the script with `importlib.util.spec_from_file_location`, under
    a module name no test uses. It calls `run_checks(find_repo_root(<repo
    root>), load_config(<that root>))` and converts both lists to tuples.
  - `class Regeneration(NamedTuple)`, with fields `json_a`, `md_a`,
    `json_b`, `md_b: Path`, `exit_codes: Tuple[int, int]`, and
    `committed_json_before`, `committed_md_before: bytes`.
  - `def regenerate(main, committed_json: Path, committed_md: Path, out_dir: Path) -> Regeneration`.
    It reads both committed files' bytes first. Then it calls `main(["--json",
    str(out_dir / "a.json"), "--md", str(out_dir / "a.md")])` and the same
    with `b.json`/`b.md`, in that order.

  `tests/conftest.py` wraps these. `aide_check_result` returns
  `load_aide_check_result()`. `regenerated_failure_modes` returns
  `regenerate(fm.main, fm.JSON_PATH, fm.MD_PATH, tmp_path_factory.mktemp("failure_modes"))`,
  and `regenerated_traceability` is the same with `segfacet.traceability`.
  Both modules are imported inside the fixture body, so collecting the tests
  stays cheap. The helpers live outside `conftest.py` because
  `testpaths` also collects `.aide/scripts/tests`, so `import conftest` from
  a test is ambiguous. The precedents for a plain helper module are
  `tests/run_process.py` and `tests/committed_artifact_guard.py`.
- **A4: the migration covers unpatched runs only.** A test migrates when its
  regeneration is an unpatched `main([...])` into a temporary directory, or
  its `aide check` is `run_checks` on the live repository. Four tests run
  `main` under a monkeypatch whose effect *is* the assertion, and they stay
  as they are:
  - `test_144::test_ac1_zero_argument_calls_accepted`
  - `test_144::test_ac17_main_no_args_writes_exactly_the_two_committed_paths`
  - `test_144::test_ac21_main_writes_through_write_bytes_even_if_write_text_raises`
  - `test_138::test_ac2_default_output_paths_are_the_committed_docs_aide_paths`

  A shared run cannot carry their patch.
- **A5: what the removal covers, and what stays.** List R holds the tests
  that pin `aide check` warnings with a path or string sweep. §6 says a
  warning count is never pinned and a diff-time claim belongs on the branch.
  It also says never to assert that "the eol-pin lint passes", but to assert
  the pin itself. The pin assertions already exist and stay:
  - `test_128` AC14
  - `test_134`'s `git check-attr` test
  - `test_149::test_ac22_gitattributes_pins_all_four_generated_paths_eol_lf`

  `test_150` AC4's unfilled-template-slot negative stays. It matches one
  warning class that is a defect wherever it appears, which is §6's "assert
  on the warning you mean by matching it". Item 159's AC9 kept it on purpose.
  `test_146::test_adv_unclassified_warning_would_be_caught` is removed along
  with the sweep it guarded. With the sweep gone, `test_146`'s
  `_classify_warning` has no other caller. `test_150`'s own
  `_classify_warning` stays, because its adversarial gate tests use it.
- **A6: the subprocess `aide check` stays.**
  `test_146::test_adv_aide_check_exits_zero` asserts the CLI's *exit code*,
  and an in-process result cannot observe that. It is neither migrated nor
  removed, and it is the one remaining whole-`aide check` run.
- **A7 (engine 2.1.0):** `.aide/scripts/aide.py` exposes
  `run_checks(repo_root, config, branches=None) -> (List[str], List[str])`,
  `find_repo_root(path)` and `load_config(repo_root)`. The existing tests in
  list M already call exactly these.
- **A8: the committed-artifact guard is unaffected.**
  `tests/committed_artifact_guard.py` resolves an operand to a committed path
  only through literal-built paths. A fixture attribute is skipped in
  silence, as the old `tmp_path` operand was, so every migrated comparison
  classifies as before. The "unchanged fence" in `test_138` AC2 and
  `test_144` AC17 now compares the live committed bytes against the
  fixture's before-snapshot, which is a committed operand against an
  unresolved one. All four artifacts are on `ALLOWLIST` under
  `no-float-leaf`, so the change raises no violation. Measured by reading
  the allowlist on 2026-09-23.
- **A9: no requesting test's patch reaches a regeneration.** pytest
  instantiates a test's fixtures from the highest scope down, so the session
  fixtures run before any function-scoped `monkeypatch` of the test that
  requests them first. A grep on 2026-09-23 found `pytest.MonkeyPatch.context`
  only in `test_073`, `test_075` and `test_106`, and none of those is in
  list M.

## Implementation Steps

This item changes nothing under `source_dir`. Every edit is under
`tests_dir`, so all of it is the **test-writer's** work. `builder.md` forbids
the builder to touch tests. The builder's step is to confirm that no
`src/segfacet/` change is needed, and to record that in Decisions.

1. **`tests/session_artifacts.py` (new).** Write the four names A3 pins. Use
   stdlib only (`importlib.util`, `pathlib`, `typing.NamedTuple`). Reuse the
   aide-loading lines that `test_aide_check_no_errors._aide_check_errors`
   already has, and do not write a new loader.
2. **`tests/conftest.py`.** Add the three session fixtures after the existing
   `docker_image_tag` block. It is the precedent for a session fixture in
   this file. Add one docstring line per fixture naming this item and the
   2026-09-18 measurement. Import `segfacet.*` inside the fixture bodies.
3. **Migrate list M.** For each function, add the fixture parameter, delete
   the local `main(...)` or `run_checks(...)` call, and read the fixture's
   fields in its place:
   - `json_a`/`md_a` stand in for a single run's destinations.
   - `json_a`/`md_a` against `json_b`/`md_b` stand in for the two runs.
   - `committed_*_before` stands in for the "before" read.
   - `exit_codes` stands in for `assert main(...) == 0`, as
     `assert exit_codes == (0, 0)`.

   Where a result was compared to `[]`, compare `errors == ()`. Every other
   assertion stays as written. Remove `tmp_path` from a signature only where
   nothing else in the test uses it.
4. **Reshape `test_159` AC7–AC9.** Drive the target test directly with
   `AideCheckResult(errors=aide_check_result.errors,
   warnings=aide_check_result.warnings + (<injected>,))`, instead of
   monkeypatching `_aide_module`. Keep the injected literals and the
   expected outcomes (no raise for AC7/AC8, `AssertionError` for AC9).
   Delete `_InjectingAide`. Its `run_checks` call is what AC7 forbids.
   Also delete `test_aide_check_no_errors._aide_check_errors` once step 1
   has taken over its loading lines.
5. **Remove list R.** Also remove every helper, constant and import left
   unused: `test_128`'s and `test_134`'s `_aide_check_warnings`, `test_146`'s
   `_aide_module`, `_classify_warning` and `_BRANCH_STATE_WARNING_PREFIXES`,
   and `test_149`'s `_aide_module`. At each removal site, leave one comment
   saying why: §6, the retirement of 2026-09-16, and this item. Use the
   comment `test_147` carries at line 1249 as the model.
6. **Fix stale cross-references.** `test_147`'s comment at line 1256 names
   `test_128::test_ac23_...` as the holder of the `.gitattributes` guard.
   Re-point it to `test_128` AC14's pin assertion. `test_146`'s module
   docstring lists `test_ac36_no_warning_names_a_path_this_item_writes`
   under AC36. Drop that name.

## Authorised paths

**May change:**

- `tests/session_artifacts.py` — new: the helpers and types pinned by A3
- `tests/conftest.py` — the three session fixtures
- `tests/test_170_session_fixtures.py` — this item's own test module
- `tests/test_aide_check_no_errors.py` — migrate (list M)
- `tests/test_128_relocation_checks.py` — remove AC23 and its helper (list R)
- `tests/test_134_decision_table_evidence_companion.py` — remove AC7 and its helper (list R)
- `tests/test_138_traceability_matrix.py` — migrate AC2 (redirect) and AC3
- `tests/test_143_s_axis_correction.py` — migrate the three traceability AC11/AC12/AC15 tests
- `tests/test_144_failure_mode_specification.py` — migrate AC17 (redirect), AC18 and the twice-called adversarial test
- `tests/test_145_eight_hypothesised_modes.py` — migrate AC23 run-to-run
- `tests/test_146_ninth_mode_and_first_proposed.py` — migrate AC32/AC33/AC36, remove the sweep and its guard (list R), docstring line
- `tests/test_147_specification_is_the_record.py` — migrate AC23/AC24, re-point the stale comment
- `tests/test_148_per_path_mode_attribution.py` — migrate AC18's `main` run
- `tests/test_149_conformance_report.py` — migrate AC20, remove AC22's warning sweep (list R)
- `tests/test_150_maintainer_sign_off.py` — migrate AC4 and AC11
- `tests/test_157_case_id_rename.py` — migrate AC16/AC17
- `tests/test_159_prerequisite_test_and_import_defects.py` — reshape AC7–AC9 to inject through the fixture

**Asserts against:**

None. `test_170` reads `tests/conftest.py` and the list M and list R
modules by AST, and all of them are under **May change** above. Its
adversarial cases read the committed `docs/aide/*.generated.*` artifacts only
to build perturbed copies, and the outcome is the same whatever those files
hold, so that read is not a pin. The fresh-versus-committed pins that the
migrated tests carry belong to the items that wrote those tests (138, 143,
144, 145, 146, 147, 148, 149, 150, 157), and this item leaves their meaning
unchanged.

## Testing Strategy

Module: `tests/test_170_session_fixtures.py`. It has one test per AC, plus the
cases below and no others. It loads other test modules by path with
`importlib.util.spec_from_file_location`, under a module name unique to this
file, the way `test_159` does, so that pytest does not collect them twice.
AC2–AC4 run on stubs under `tmp_path`, and none of them triggers a real
regeneration or `aide check`.

Adversarial cases. The first four are the queue's "every migrated test still
fails on the defect it guards", one representative per cluster. Each calls
the migrated test function directly with a constructed fixture value, after
first checking that the planted defect is really present (§6), and expects
`AssertionError`.

- **`aide-check-representative`:**
  `test_aide_check_no_errors.test_aide_check_reports_no_errors`, given
  `AideCheckResult(errors=("planted error",), warnings=())`, raises. Guards
  against a migration that stopped reading `errors`.
- **`run-to-run-representative`:**
  `test_144...test_ac18_artifacts_are_byte_reproducible_run_to_run`, given a
  `Regeneration` whose `json_b` is a copy of `json_a` with one byte changed,
  raises. Guards against a migration that compares `json_a` with itself.
  `json_a`/`md_a` are copies of the committed pair written under `tmp_path`.
- **`fresh-vs-committed-representative`:**
  `test_157...test_ac17_traceability_matrix_artifacts_regenerate_identically`,
  given a `Regeneration` whose `json_a` is the committed traceability JSON
  with one **string** leaf changed, raises. A string change, because
  `assert_matches_committed_artifact` tolerates numeric leaves. Guards against
  a migration that reads the committed file on both sides.
- **`untouched-representative`:**
  `test_138...test_ac2_main_redirects_writes_and_leaves_committed_artifacts_unchanged`,
  given a `Regeneration` whose `committed_json_before` is the live committed
  bytes plus `b"x"`, raises. Guards against an "untouched" check that
  compares the live file with itself.
- **`ast-checker-negative-control`:** the helpers behind AC5–AC7 report
  each of these snippets correctly. They flag `def test_x(): fm.main([])`,
  flag a `run_checks` call nested in a class method (`class W:\n def
  run_checks(self):\n  return self._real.run_checks()`), do not flag `def
  test_x(): catalogue.main([])`, and report a function name that is not
  defined as absent. Guards against a checker that never flags anything, or
  one that walks only top-level function bodies, either of which would make
  AC5–AC7 pass vacuously.

**Existing tests to reconcile.** No production default or behaviour changes,
so no other test's assumption goes stale. The reconciliation is this item's
own edits:

- Every function in list M: the migration.
- Every function in list R: the removal, with the helpers step 5 names.
- `test_159` AC7–AC9: the injection seam moves from `_aide_module` to a
  constructed `AideCheckResult` (step 4).
- `test_147`'s comment at line 1256 and `test_146`'s module docstring: stale
  names (step 6).
- Swept 2026-09-23 with an AST walk over `tests/test_*.py`: no other test
  calls `run_checks`, `failure_modes.main` or `traceability.main`. Nothing
  outside the modules above references a list R name or a helper step 5
  removes. `test_138`/`test_149`'s `build_matrix()` call-site budget (AC28)
  counts only `build_matrix()` calls, and this item moves none of them.

## Validation

1. From the item branch, run `.venv/bin/python -m pytest -n auto
   --durations=40`. It must be green, with no new skip.
2. Read its `--durations` list. No `call` entry may name a test in list M.
   A `setup` entry that names a test in list M must be the first request of
   one of the three session fixtures on its worker: at most one per fixture
   per worker. That is the queue's "`--durations` names none of the migrated
   tests among its slowest entries", read with A1, because pytest charges a
   session fixture's one-off cost to the setup of whichever test requests it
   first.
3. Record the suite wall-clock and the three fixtures' setup durations in
   Decisions. Put them beside the 2026-09-18 baseline (8989 tests in 8m35s,
   `-n 4`, Linux). The machines differ, so the comparison is informative,
   not a gate.
4. `python .aide/scripts/aide.py check` must report no error.

## Dependencies

None.

**Downstream:** items 173–177 regenerate the corpus and every downstream
artifact. The migrated fresh-vs-committed tests then read through this
item's fixtures, so each of those items pays one regeneration per worker
instead of 33 across the suite.

## Decisions & Trade-offs

- **Builder confirmation (2026-09-23):** per the spec's own Implementation
  Steps, this item changes nothing under `source_dir`. Verified via `git diff
  HEAD~2 --stat` against the test-writer's commit (f78afca): every touched
  path is under `tests/` (`tests/session_artifacts.py`, `tests/conftest.py`,
  and the list M/R modules plus `tests/test_170_session_fixtures.py`); no
  `src/segfacet/**` path appears. No production code was written or needed.

- **Left open:** the four patched-I/O `main` tests in A4. A shared run cannot
  carry their patch. Stubbing `specification_to_dict`/`render_markdown`
  inside them would make them cheap without changing what they assert, but
  that is a per-test judgement to make once `--durations` shows their cost.
- **Left open:** direct `specification_to_dict()`, `render_markdown()` and
  `build_matrix()` calls in test bodies and module fixtures (for example
  `test_148` AC18, `test_151` AC4, `test_162` AC9/AC10). Several of them
  assert that the function returns a fresh, uncached result, which a shared
  build cannot serve. The queue names regeneration, not building.
- **Left open:** `test_146::test_adv_aide_check_exits_zero` (A6), the one
  remaining whole-`aide check` run. `aide merge` has run `aide check` beside
  the suite since engine 1.53.0, so whether the suite still needs its own
  exit-code check is a separate question.
- **Left open:** `test_126` AC12 (27 s) and `test_113` AC7's nested-collection
  setup (22 s), which the 2026-09-18 insight names as slow singles. Neither
  is in either cluster.
