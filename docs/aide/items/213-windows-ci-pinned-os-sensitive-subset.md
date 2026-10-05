<!-- aide-template: item 3 -->
# Item 213 — The Windows CI leg runs a pinned OS-sensitive subset

> **Created:** 2026-10-03 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 27 — Feature Schema Taxonomy & Coordinate System (maintenance)
> **Queue:** [`../queue/queue-028.md`](../queue/queue-028.md) · Item 213
> **Objectives:** G7
> **Suggested branch:** `aide/213-windows-ci-pinned-os-sensitive-subset`

---

## Description

`test (windows-latest)` is the CI workflow's critical path. On run
37042666246 it took 25.5 min against Ubuntu's 16.5 min, and most of that time
went on tests Windows cannot refute (insight 2026-10-03-5252 in
`docs/aide/insights.md`). The maintainer's 2026-10-03 maintenance branch
landed the first half. On the Windows leg the Test step `--ignore`s
`.aide/scripts/tests`, and both legs report `--durations=30`.

This item does the second half. It decides which test modules *need* Windows
and runs only those there:

- **One rule decides OS-sensitivity.** It is a static classifier over each
  `tests/test_*.py` module's AST. A module is OS-sensitive when it shows at
  least one of five signals:
  1. it spawns a subprocess;
  2. it invokes the `segfacet` CLI;
  3. it reads bytes or newlines;
  4. it handles path text;
  5. it loads the AIDE engine in-process.

  Assumption A1 gives each signal's exact AST shape. A short hand-kept
  `WINDOWS_EXTRA` dict, with one reason per entry, adds the path-text modules
  the classifier cannot see.
- **Floats are not a Windows signal.** Machine and OS float differences are
  absorbed by tolerance, not by running a test on Windows. A fresh-vs-committed
  comparison goes through `segfacet.synth.golden.assert_matches_committed_artifact`
  (numeric-tolerance leaves, item 078), and `tests/committed_artifact_guard.py`
  (item 127) enforces that statically. The guard already runs over every
  `tests/*.py`, in `tests/test_127_committed_artifact_tolerance.py::test_ac15_classifier_reports_zero_violations_on_tests_tree`.
  So a module that compares a committed artifact exactly fails the suite
  instead of silently leaving Windows, with no new check here.
- **The workflow names the list.** The `test` job carries a job-level
  `env: WINDOWS_TESTS: >-` block that names those modules as paths. The Test
  step appends `env.WINDOWS_TESTS` behind a `runner.os == 'Windows'` guard.
  So Windows runs exactly the named modules, and Ubuntu still runs bare
  `python -m pytest -n 4 --durations=30`, which is the whole `testpaths`
  suite, `.aide/scripts/tests` included.
- **A test pins the list.** The new `tests/test_213_windows_ci_subset.py`
  checks that the workflow's list equals the classifier's set joined with
  `WINDOWS_EXTRA`. If a new module spawns a subprocess, reads committed bytes
  or invokes the CLI, and nobody adds it to the workflow, the suite goes red on
  every leg. This follows `aide-loop`'s `tests/test_ci_shards.py`, which pins
  that repo's `UBUNTU_ONLY` list. Here the pinned list is the inverse one: what
  Windows runs.

**Not in scope:**

- Sharding the Windows leg.
- Changing `test-numpy-majors` or `verify-environment-gated`.
- Changing any test's content, except the reconciliation of
  `tests/test_113_ci_numpy_matrix_scope.py`'s AC6 below.
- Adding a pytest marker.
- Changing what CI triggers on.

## Acceptance Criteria

- [ ] **AC1: Ubuntu runs the whole suite, Windows the named list.** The `test`
  job's step named `Test` has a `run` command that, after whitespace
  normalisation, equals exactly
  `python -m pytest -n 4 --durations=30 ${{ runner.os == 'Windows' && env.WINDOWS_TESTS || '' }}`.
- [ ] **AC2: the list has one definition.** `WINDOWS_TESTS` is defined only
  as a key of the `test` job's own `env` mapping. It is not a key of the
  workflow-level `env`, of any other job's `env`, or of any step's `env`.
- [ ] **AC5: the list is exactly the OS-sensitive set.** The set of
  `jobs.test.env.WINDOWS_TESTS` tokens equals the set made of every
  `tests/test_*.py` module the classifier flags (computed live from each
  module's source), joined with the keys of `WINDOWS_EXTRA`. On failure the
  message names both differences: modules flagged but not listed, and modules
  listed but neither flagged nor in `WINDOWS_EXTRA`.
- [ ] **AC6: each signal shape is detected.** The classifier flags a module
  source containing any one of the signal shapes listed in Assumption A1,
  checked one shape per parametrised case.
- [ ] **AC7: a pure module is not flagged.** The classifier flags nothing in a
  module source that imports only `numpy`, `pytest` and `segfacet.features`
  and whose docstring mentions the word `subprocess`.
- [ ] **AC8: every hand-listed module exists.** Every key of `WINDOWS_EXTRA`
  is the repo-relative POSIX path of a file that exists, directly under
  `tests/`, whose name matches `test_*.py`.

AC3, AC4 and AC9 were withdrawn by the queue-028 spec review on 2026-10-05,
before any test was written (see Decisions & Trade-offs). The remaining
criteria keep their numbers. Testing Strategy says why each one is not
written.

## Assumptions

- **A1 (the classifier's signals).** Each signal is the stated shape, found
  by walking the module's `ast` tree. The classifier never runs a regex over
  the raw text, so a docstring that only *mentions* `subprocess` (as
  `tests/test_104_feature_catalogue_drift.py` does) is not a signal.
  1. **Subprocess.** Any of:
     - `import subprocess` or `from subprocess import …`;
     - `import run_process` or `from run_process import …`
       (`tests/run_process.py` is the UTF-8 subprocess wrapper);
     - the attribute `sys.executable`.
  2. **CLI.** Any of:
     - `import segfacet.cli`, `from segfacet.cli import …` or
       `from segfacet import cli`;
     - a string constant that starts with `segfacet.cli` (the
       `monkeypatch.setattr("segfacet.cli.main", …)` target
       `tests/test_068_entrypoint.py` uses).
  3. **Bytes or newlines.** Any of:
     - any `.read_bytes` attribute;
     - a call keyword named `newline`;
     - a string constant containing `.gitattributes`;
     - a function parameter named `regenerated_failure_modes` or
       `regenerated_traceability`. These session fixtures read committed bytes
       through `tests/session_artifacts.py::regenerate`.
  4. **Path text.** Any of:
     - an `.as_posix` attribute;
     - `os.sep` or `os.path.sep`;
     - the name `PureWindowsPath` or `PurePosixPath`.
  5. **AIDE engine in-process.** A function parameter named
     `aide_check_result`. That session fixture runs `aide check`'s
     `run_checks` in-process. `tests/test_114_documentation_corrections.py`
     and items 145/146 record path-separator and capture differences from it
     on the Windows runner.

  **Floating-point behaviour is deliberately not a signal** (maintainer
  decision, 2026-10-05). An earlier draft had a sixth signal, any import of
  `segfacet.synth.golden`, on the strength of item 078's finding that Windows
  and Ubuntu x86 floats can differ against committed artifacts. It was
  dropped: a test absorbs a machine/OS float difference with a tolerance, and
  a fresh-vs-committed comparison already has one, through
  `assert_matches_committed_artifact`, enforced by
  `tests/committed_artifact_guard.py`.
  `tests/test_127_committed_artifact_tolerance.py::test_ac15_classifier_reports_zero_violations_on_tests_tree`
  runs that guard over every `tests/*.py`, so the guarantee holds for every
  module off the Windows list.
- **A2 (seed of `WINDOWS_EXTRA`).** The dict starts with one entry:
  `tests/test_086_datasets.py`. Its reason: it compares dataset-descriptor path
  text (`descriptor_dir == str(tmp_path.resolve())`) and calls `is_absolute()`
  on a POSIX-rooted `Path("/does/not/exist")`. Both differ on Windows. It also
  writes `str(tmp_path)` into descriptor YAML, the same class of bug as
  a8f3497, where a YAML double-quoted scalar dropped the backslashes in
  `tmp_path` on Windows in `test_087`. No signal sees any of this. Two modules
  that Windows CI once caught a bug in are deliberately **not** seeded:
  `tests/test_099_per_mode_metrics.py`, whose path-separator scope-fence hash
  was retired by item 107, and `tests/test_114_documentation_corrections.py`,
  whose subprocess capture is gone. The code Windows caught no longer exists
  in either.
- **A3 (list size, measured 2026-10-05 on `aide/queue-028`).** The five
  signals flag 87 of the 216 `tests/test_*.py` modules. The list adds
  `WINDOWS_EXTRA`'s one entry and the new module itself. That module flags
  itself because its own signal-shape fixtures are string constants that
  start with `segfacet.cli` and contain `.gitattributes`. So the Windows list
  is 89 paths. The six-signal draft flagged 91 modules, for a 93-path list.
  The builder takes the real list from AC5's failure message, never from this
  count, since items 209–212 may change it (A5).
- **A6 (the modules that leave Windows when the float signal is dropped,
  reviewed 2026-10-05).** Of the 31 modules that import `segfacet.synth.golden`, 27
  carry another signal and stay on Windows. Four leave. Each was read for a
  fresh-vs-committed float comparison done without a tolerance:
  - `tests/test_073_verdict_equivalence.py` imports `canonical_json` only
    for CPU-vs-GPU and run-to-run comparisons. Both sides are fresh, and
    nothing committed is read.
  - `tests/test_089_fov_aware_coverage_border.py` imports
    `build_report_for_case`. AC16 compares fresh `coverage`/`border` findings
    exactly against the in-source literal
    `test_098_stray_components._PRE_098_GOLDEN_VERDICT_AND_FINDINGS`. The
    `coverage`/`border` entries of that literal carry no number (labels and
    face/level names only), so no float is compared.
  - `tests/test_094_tptbox_image_layer.py` imports `build_report_for_case`.
    Its own AC3 reads the committed `tests/corpus/094_pre_migration_snapshot.json`,
    which records each fixture's shape, dtype, voxel-data hash, spacing and
    affine. Spacing is checked with `pytest.approx` and the affine with
    `np.allclose`. The hash is over voxel data decoded from the committed
    NIfTI, with no arithmetic on it. Its AC7 compares verdict strings only.
  - `tests/test_121_tangent_orientation.py` imports `build_report_for_case`.
    Every float check is against a hand-written literal under
    `pytest.approx`, and it reads no committed artifact.

  No defect was found among the four. `committed_artifact_guard.iter_violations`
  reports none across `tests/`, which test_127's AC15 already asserts.
- **A4 (GitHub Actions behaviour).** A `>-` folded scalar under job-level
  `env` reaches `${{ env.WINDOWS_TESTS }}` as one space-separated line. The
  expression is expanded before the shell runs: pwsh by default on
  windows-latest, bash on ubuntu. About 89 paths of 40–60 characters each is
  roughly 5 kB, well under the pwsh/CreateProcess command-line limit of
  32,767 characters. Given explicit file arguments, pytest ignores
  `testpaths`, which is why `.aide/scripts/tests` stays off the Windows leg
  with no `--ignore`.
- **A5 (ordering with the queue-mates).** Items 209–212 add or change test
  modules. If one of them adds a module the classifier flags, then whichever
  of that item and this one lands second has to add the module to
  `WINDOWS_TESTS`. Items 209–212 are not authorised to touch
  `.github/workflows/ci.yml`. This item therefore declares 209–212 under
  `## Dependencies`, so it is built last and its list includes their modules.
  Every later item that adds an OS-sensitive test module will need
  `.github/workflows/ci.yml` under its own **May change**. That friction is
  deliberate: it is how a new OS-sensitive module cannot silently miss
  Windows.

## Implementation Steps

The test-writer commits `tests/test_213_windows_ci_subset.py` first. The
builder then changes only the workflow.

1. **The test module (test-writer).** In `tests/test_213_windows_ci_subset.py`:
   - The module docstring states the rule: the five signals of A1, why
     floating-point behaviour is not one (test_127's AC15 covers it), and that
     `WINDOWS_EXTRA` is for an OS-sensitive module the signals cannot see,
     each entry with its reason.
   - `_signals(source: str) -> set[str]` walks `ast.parse(source)` for
     A1's shapes.
   - `WINDOWS_EXTRA: dict[str, str]` is seeded per A2.
   - `_expected()` is the set of `tests/<name>` for every `tests/test_*.py`
     whose `_signals` is non-empty, joined with `WINDOWS_EXTRA`.
   - `_workflow()` parses `.github/workflows/ci.yml` with `yaml.safe_load`.
     PyYAML is a core dependency and `test_113` already uses it.
   - One comparison helper reports both differences between the list and the
     expected set. The AC5 test and its adversarial counterpart both call
     this same helper.
   - Reuse `tests/test_113_ci_numpy_matrix_scope.py`'s whitespace
     normalisation idea for AC1. Copy the three-line `_normalize_run` rather
     than importing it from another test module.
   - Add no dependency.
2. **Reconcile `tests/test_113_ci_numpy_matrix_scope.py` (test-writer).** In
   `test_ac6_test_job_install_and_test_commands_unchanged`:
   - Two assertions pin the old Windows guard: the literal
     `${{ runner.os == 'Windows' && '--ignore=.aide/scripts/tests' || '' }}`
     string, and `test_run.count("--ignore") == 1`. Replace both with
     `assert "--ignore" not in test_run`.
   - Rewrite the adjacent comment so it says the Windows selection is now
     pinned by `tests/test_213_windows_ci_subset.py`.
   - Leave the prefix assertion and the `--deselect` / `--ignore=tests/` leak
     checks unchanged.
3. **The workflow (builder).** In `.github/workflows/ci.yml`'s `test` job:
   - Add a job-level `env:` with `WINDOWS_TESTS: >-`, listing one path per
     line in sorted order.
   - Above the list, add a comment saying the rule and each `WINDOWS_EXTRA`
     reason live in `tests/test_213_windows_ci_subset.py`, which fails when
     the two disagree.
   - Change the Test step's `run` to AC1's string.
   - Rewrite the Test step's comment. It currently says the next step "is open
     in docs/aide/insights.md (2026-10-03)". It should say the Windows leg runs
     only the pinned OS-sensitive list, and why.
   - To get the list, run `.venv/bin/python -m pytest tests/test_213_windows_ci_subset.py`
     and take the paths from AC5's failure message. Do not hand-derive them.
4. **Leave the rest alone.** Do not touch `test-numpy-majors`,
   `verify-environment-gated` or `scope-check`.

## Authorised paths

**May change:**

- `.github/workflows/ci.yml` — the `test` job's `WINDOWS_TESTS` env block, its Test step command and comment
- `tests/test_213_windows_ci_subset.py` — the new module holding the classifier, `WINDOWS_EXTRA` and the pin
- `tests/test_113_ci_numpy_matrix_scope.py` — AC6's two assertions on the retired Windows `--ignore` guard reconciled

**Asserts against:**

None. AC5 reads every `tests/test_*.py` module's source live. That is a
recomputation, not a pin, and a glob over `tests/test_*.py` would sweep the
two test modules named under May change.

## Testing Strategy

The test module is `tests/test_213_windows_ci_subset.py`, with one test per
AC (AC6 parametrised over A1's shapes). It reads `ci.yml` and the test sources
with `read_text(encoding="utf-8")` and spawns nothing.

**Adversarial cases:**

- **missing-module:** the AC5 comparison helper, given the live expected set
  and a workflow list with one flagged module removed, reports that module
  under "flagged but not listed". This guards a helper that compares in only
  one direction and so lets a new OS-sensitive module miss Windows silently.
- **stray-module:** the same helper, given a list with an extra
  `tests/test_*.py` that is neither flagged nor in `WINDOWS_EXTRA`, reports it
  under "listed but not OS-sensitive". This guards the Windows list growing
  back toward the whole suite by hand.
- **step-env-override:** AC2's check, applied to a parsed workflow dict in
  which one step also defines `WINDOWS_TESTS`, fails. This guards against a
  step-level value deciding what Windows runs without being pinned.
- **unguarded-list:** AC1's check, applied to a `run` string that appends
  `${{ env.WINDOWS_TESTS }}` with no `runner.os` guard, fails. Without the
  guard Ubuntu would silently run only the subset.
- **aliased-import:** `import subprocess as sp` and
  `from segfacet.cli import main as cli_main` are each flagged. This guards a
  classifier that matches on the bound name instead of the module.

**Not written because an existing test or tool already fails:**

- **Withdrawn AC9 (no off-Windows module compares a committed artifact
  exactly).** `tests/test_127_committed_artifact_tolerance.py::test_ac15_classifier_reports_zero_violations_on_tests_tree`
  already requires `committed_artifact_guard.iter_violations(TESTS_DIR)` to
  be empty over every `tests/*.py`, and that covers every off-Windows module.
  Nothing could turn AC9 red without also turning test_127's AC15 red. That
  test is how the maintainer's review caveat on the dropped float signal stays
  met. A6 keeps the hand review of the four modules that leave Windows.
- **Withdrawn AC3 (the list holds `tests/test_*.py` paths only).** A token
  that is not a test module path is outside the expected set, so AC5's set
  comparison already reports it under "listed but not OS-sensitive".
- **Withdrawn AC4 (no path listed twice).** A duplicate breaks nothing.
  pytest ignores a repeated file argument unless `--keep-duplicates` is
  passed, so the module still runs once on Windows.

**Existing tests to reconcile:**

- `tests/test_113_ci_numpy_matrix_scope.py::test_ac6_test_job_install_and_test_commands_unchanged`
  pins the old guard string and `count("--ignore") == 1`. This item's AC1
  makes both false. Implementation step 2 reconciles them.

The sweep grep found no other test that reads the `test` job's Test step:
`grep -rn "test_test_run\|runner.os\|durations" tests/` hits only `test_113`.

## Validation

Run the Windows subset's collection locally:
`.venv/bin/python -m pytest --collect-only -q` with the `WINDOWS_TESTS` paths
as arguments. Record two numbers against the unscoped `--collect-only` count:
the subset's test count, and the fact that it has no collection error. This
observes that every named path exists and is collectable as a set, which the
unit suite checks only path by path.

The point of the change is a shorter `test (windows-latest)` wall clock. Only
a CI run on windows-latest can observe that, and CI runs only once the queue
PR is marked ready (CLAUDE.md, "Code review"). The loop's Linux host has no
`[validation]` profile for it. The validator records the wall-clock effect as
❓ Unverified, with the reason "observable only at queue-028's mark-ready CI
run". It is read off that run's `test (windows-latest)` Test step duration at
queue end and compared with run 37042666246's 24.4 min.

## Dependencies

- Item 209: changes `tests/test_155_corpus_case_kind.py`, a flagged module,
  and may add test modules. This item's list must include whatever 209 leaves
  (A5).
- Item 210: changes the monotonicity check and its tests. Any new test module
  it adds must be in this item's list (A5).
- Item 211: changes `fused_label` and its tests. Same reason (A5).
- Item 212: re-authors `crop_at_border` and its tests. Same reason (A5).

## Decisions & Trade-offs

To be updated during implementation.

- **2026-10-05, maintainer answers to the spec's open decisions:**
  - The list is decided by a static classifier plus `WINDOWS_EXTRA`, written
    out in `ci.yml`, with an exact-equality test. A list computed at CI time
    was rejected, so that every change to what Windows runs is a reviewable
    diff.
  - This item depends on items 209–212 and is built last (A5).
  - The committed-float signal is dropped (A1, A6). The maintainer attached a
    caveat: the tolerance-carrying fresh-vs-committed tests need a review.
    That review is not this item's.
- **2026-10-05, queue-028 spec review** (accepted by the maintainer):
  - Three criteria duplicated something that already fails, so they are
    withdrawn. AC9 duplicated test_127's AC15. AC3 is subsumed by AC5's set
    comparison. AC4 guarded nothing, because pytest de-duplicates file
    arguments. Testing Strategy, under "Not written because", gives each
    reason.
  - AC9's helper and its `exact-committed-off-windows` adversarial case go
    with it.
  - The remaining criteria keep their numbers (AC1, AC2, AC5–AC8), and the
    withdrawn ones are marked under Acceptance Criteria. Item specs do not
    need contiguous AC numbers, and renumbering would silently change what
    "AC5" and "AC8" mean in the Implementation Steps, in A3 and in any review
    note that already cites them.
- **Left open:** whether `WINDOWS_EXTRA` should also hold modules that once
  failed on Windows CI but no longer contain the code that failed (`test_099`,
  `test_114`). A2 leaves them off. The question waits for a Windows-only
  failure that the classifier and the seed both miss, which would show the
  rule is too narrow.
- **Left open:** whether `committed_artifact_guard` should also catch an exact comparison of
  a value *parsed* from a committed artifact, such as
  `json.loads(p.read_text())["x"] == fresh_x`. `committed_artifact_guard` is
  "precise, not exhaustive" by its own docstring: it resolves `==` operands
  that are direct `.read_bytes()` / `.read_text()` / `sha256` reads of a
  committed path. A6's hand review found no such parsed comparison among the
  four modules leaving Windows. Widening the guard is item 127's surface, and
  the maintainer asked for a review of those tests, which is a different
  question from where they run.
- **Left open:** whether the Windows leg should be split into shards, as
  `aide-loop`'s `tests.yml` does. That waits for the first Windows timing of
  the subset (Validation). This item does not presume the subset is still the
  critical path.
