<!-- aide-template: item 3 -->
# Item 232 — Every report names the FACET revision that wrote it

> **Created:** 2026-10-18 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 35 — Programme Interface: the SegFACET Side
> **Queue:** [`../queue/queue-031.md`](../queue/queue-031.md) · Item 232
> **Objectives:** G7
> **Suggested branch:** `aide/232-every-report-names-the-facet`

---

## Description

This is the revision half of Stage 35's fourth deliverable, artefact
versioning. `vision.md` §7.5 says each report that leaves FACET carries the
FACET revision that wrote it, so that `spine-failure-lab` (package
`spinelab`) can pin a report to the code that produced it. Item 233 owns the
other half, the report `schema_version`.

Today neither report names a revision. The per-case report
(`segfacet run` writes `<out>/segfacet_report.json` through
`segfacet.report.serialize_report_json`) has no commit and no package
version. The evaluation report (`segfacet evaluate` writes
`<out>/eval_report.json` through `segfacet.eval.report.build_evaluation_report`)
has an optional `provenance.segfacet_version` that the CLI never fills, and
no commit.

The item delivers three things:

1. **`segfacet.revision`**, a new stdlib-only module. Its
   `facet_revision(package_dir=None)` returns
   `{"commit": <hex SHA or None>, "package_version": segfacet.__version__}`.
   The commit is `HEAD` of the git work tree that **tracks the imported
   package's own source**. It is `None` when no work tree tracks it (an
   installed wheel, or a non-editable install into a venv that sits inside a
   checkout), when `git` is not on `PATH`, or when a `git` call fails.
2. **A `facet_revision` top-level block** in both reports. Each report
   builder takes it as an optional keyword argument. The CLI always passes
   `facet_revision()`, so every report `segfacet run` and `segfacet evaluate`
   write carries the block. Both bundled JSON schemas declare it.
3. **A `## Releasing` section in `README.md`.** It defines how a revision
   `spinelab` consumes is tagged. The item tags nothing, and pushing a tag is
   the owner's job.

**Not in scope.** The plain-text reports (`segfacet_report.txt`,
`eval_report.txt`), the `compare-runs` artefact, the feature catalogue, and
`provenance.segfacet_version` are untouched (see Left open). No tag is created
or pushed. The report `schema_version` does not move here: adding a top-level
provenance block moves no feature path, and item 233 makes the one bump.

## Acceptance Criteria

- [ ] **AC1: A per-case report carries the checkout's commit.** The
  `facet_revision.commit` of the `segfacet_report.json` that `segfacet run`
  writes equals the stripped stdout of `git rev-parse HEAD`, run with its
  working directory at `Path(segfacet.__file__).resolve().parent`.
  *(closes Stage 35 criterion 3)*
- [ ] **AC2: A per-case report carries the package version.** The
  `facet_revision.package_version` of that `segfacet_report.json` equals
  `segfacet.__version__`.
- [ ] **AC3: An evaluation report carries the checkout's commit.** The
  `facet_revision.commit` of the `eval_report.json` that `segfacet evaluate`
  writes equals the stripped stdout of `git rev-parse HEAD`, run with its
  working directory at `Path(segfacet.__file__).resolve().parent`.
  *(closes Stage 35 criterion 3)*
- [ ] **AC4: An evaluation report carries the package version.** The
  `facet_revision.package_version` of that `eval_report.json` equals
  `segfacet.__version__`.
- [ ] **AC5: A per-case run with no git metadata records the commit as
  unknown.** When `segfacet.revision.facet_revision` resolves against a
  package directory that no git work tree tracks, `segfacet run` writes a
  `segfacet_report.json` whose `facet_revision.commit` is JSON `null`.
- [ ] **AC6: An evaluation run with no git metadata records the commit as
  unknown.** Under the same condition, `segfacet evaluate` writes an
  `eval_report.json` whose `facet_revision.commit` is JSON `null`.
- [ ] **AC7: The tagging procedure is in the README.** `README.md` has a
  `## Releasing` section. The section gives the tag name as the literal
  template `v<package_version>` and names `src/segfacet/__init__.py` as the
  file whose `__version__` a release bumps.

## Assumptions

- **A1 (versioning scheme, defensible default for the owner to confirm).**
  The interface leaves FACET's versioning scheme to the owner, and the queue
  asks this spec to put the question to them. `loop.clarify = "assume"`, so
  the spec takes this default, and the owner confirms or replaces it at the
  queue boundary:
  - every revision `spinelab` consumes gets an **annotated tag
    `v<package_version>`** on a commit of `main`, where `package_version` is
    `segfacet.__version__`;
  - before tagging, the release commit bumps `__version__` in
    `src/segfacet/__init__.py`, so tags never collide and a report's
    `package_version` names its tag;
  - the owner pushes the tag.
  The `README.md` section is prose, so a different scheme costs one edit
  there and nothing in code.
- **A2 (the commit's source).** "The FACET commit" means `HEAD` of the work
  tree that tracks the **imported package's source**. It is not the process's
  working directory: `spinelab` runs `segfacet` from inside its own
  repository, and a cwd-based lookup would record `spinelab`'s commit. Two
  checks decide "tracked": `git ls-files --error-unmatch __init__.py`
  succeeds in the package directory, then `git rev-parse HEAD` answers there.
  A package directory inside a work tree but not tracked by it (a
  non-editable install into this checkout's own `.venv`) therefore records
  `null`, not the enclosing checkout's commit.
- **A3 (what "says so" means).** A report with no git metadata says so with
  `"commit": null`. The schema description defines null as "unknown: no git
  work tree tracks the package, or git is unavailable". No separate flag is
  added.
- **A4 (determinism).** The report builders stay pure. `serialize_report` and
  `build_evaluation_report` read no git state. They embed a caller-supplied
  `facet_revision` and emit no key when it is `None`, as `run_manifest` does
  (item 096). Only the CLI resolves the revision. Three consequences follow:
  - `tests/golden/report_format_contract.json`, built by
    `tests/report_format_fixture.py` without the block, carries no commit
    and does not change;
  - within one checkout `HEAD` is fixed, so the existing run-to-run
    byte-identity tests (`test_057` AC6, `test_101_compare_runs_cli` AC23,
    `test_075`'s CPU/GPU byte-identity) still hold;
  - no committed artefact contains a CLI-written report (`git ls-files`
    lists none, measured 2026-10-18), so no fresh-vs-committed comparison
    sees a commit.
  A commit inside a committed, byte-compared artefact would be
  self-referential, and this design never puts one there.
- **A5 (dirty trees).** A tree with uncommitted changes records its `HEAD`
  commit with no dirty marker. The A1 procedure tags a clean commit of
  `main`, and a report `spinelab` pins comes from a checkout of that tag.

## Implementation Steps

1. **New `src/segfacet/revision.py`** (stdlib only: `subprocess`,
   `pathlib`). It holds one public function,
   `facet_revision(package_dir: Optional[os.PathLike] = None) -> dict`:
   - The default `package_dir` is `Path(segfacet.__file__).resolve().parent`.
   - It runs `["git", "ls-files", "--error-unmatch", "__init__.py"]`, then
     `["git", "rev-parse", "HEAD"]`, each through `subprocess.run` with
     `cwd=package_dir`, `capture_output=True`, `encoding="utf-8"` and a short
     `timeout`.
   - It returns `{"commit": <stripped stdout>, "package_version": segfacet.__version__}`.
   - `commit` is `None` on a nonzero exit, `FileNotFoundError` (no `git`),
     `OSError`, `subprocess.TimeoutExpired`, or output that is not a
     lowercase hex SHA.
   - It never raises.
   - The module docstring carries the item number and a scope fence: no
     tagging, no dirty detection, no wall clock.
2. **`src/segfacet/report.py`**: add `facet_revision: "dict | None" = None`
   to `serialize_report` and `serialize_report_json`. When it is non-`None`,
   set `report["facet_revision"]` after the existing optional blocks, before
   `jsonschema.validate`. When it is `None`, emit no key. Update the
   docstrings.
3. **`src/segfacet/report_schema_v0.json`**: add an optional top-level
   `facet_revision` property. It is an object with
   `additionalProperties: false` and requires `commit` and
   `package_version`:
   - `commit`: `["string", "null"]`, pattern `^([0-9a-f]{40}|[0-9a-f]{64})$`,
     with A3's meaning of null in the description;
   - `package_version`: a non-empty string.
   Leave `required` and `schema_version`'s `const` unchanged.
4. **`src/segfacet/eval/report.py`** and
   **`src/segfacet/eval/eval_report_schema_v0.json`**: make the same keyword
   change on `build_evaluation_report` and the same property definition in
   the evaluation schema. `EvaluationProvenance` is untouched.
5. **`src/segfacet/cli.py`**: in `_handle_run` (which batch mode reuses
   through `_run_batch`) and `_handle_evaluate`, import inside the function
   body with `from segfacet import revision` (keeping `--help` fast). Pass
   `facet_revision=revision.facet_revision()` to `serialize_report_json` and
   `build_evaluation_report`. Read it through the module attribute at call
   time, which lets a test monkeypatch `segfacet.revision.facet_revision`.
6. **`README.md`**: add a `## Releasing` section stating A1's procedure:
   - the tag template `v<package_version>`;
   - bump `__version__` in `src/segfacet/__init__.py` first;
   - tag a clean commit of `main` with an annotated tag;
   - the owner pushes it;
   - a report's `facet_revision.commit` and `package_version` are what
     `spinelab` pins against.
   Keep it to a few lines.
7. **`.github/workflows/ci.yml`**: add `tests/test_232_facet_revision.py` to
   `jobs.test.env.WINDOWS_TESTS`, in sorted position. The module imports
   `segfacet.cli` and spawns `git`, both signals that
   `tests/test_213_windows_ci_subset.py` flags.
8. Reconcile the existing tests listed under Testing Strategy.

No dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/revision.py` — new: the revision resolver
- `src/segfacet/report.py` — `facet_revision` keyword on the per-case serializer
- `src/segfacet/report_schema_v0.json` — the optional `facet_revision` property
- `src/segfacet/eval/report.py` — `facet_revision` keyword on `build_evaluation_report`
- `src/segfacet/eval/eval_report_schema_v0.json` — the optional `facet_revision` property
- `src/segfacet/cli.py` — `run` and `evaluate` pass the resolved revision
- `README.md` — the `## Releasing` section (AC7)
- `.github/workflows/ci.yml` — the new test module joins `WINDOWS_TESTS`
- `tests/test_232_facet_revision.py` — new: this item's tests
- `tests/test_049_reference_integration.py` — AC6's exact CLI key set gains `facet_revision`
- `tests/test_065_cli_intensity.py` — AC10's exact CLI key set gains `facet_revision`
- `tests/test_090_reference_derived_defaults.py` — AC4's exact CLI key set gains `facet_revision`
- `tests/test_216_neighbour_pair_and_case_level_migration.py` — `_NON_CONTENT_KEYS` gains `facet_revision`
- `tests/test_215_per_label_migration.py` — the same `_NON_CONTENT_KEYS` tuple, edited only if it fails

**Asserts against:**

- `src/segfacet/__init__.py` — AC2, AC4 and AC7 read its `__version__`

## Testing Strategy

The new module is `tests/test_232_facet_revision.py`. It has one test per AC.
Its own `git` calls go through `tests/run_process.run_utf8`, with no skip.
The suite runs from a git checkout in the loop and in CI (`fetch-depth: 0`),
so a missing `git` fails loudly instead of degrading to a skip.

- **AC1 and AC2** share one `segfacet run --no-reference` invocation (a
  module-scoped fixture) on a committed corpus case such as `clean_control`.
  `--no-reference` keeps the run fast and is irrelevant to the block.
- **AC3 and AC4** share one `segfacet evaluate` over the cheapest cohort
  `tests/test_057_evaluate_cli.py` already uses.
- **AC5 and AC6** monkeypatch `segfacet.revision.facet_revision` with a
  `functools.partial` of the real function bound to
  `package_dir=tmp_path / "pkg"` (an empty, untracked directory), then run
  the CLI.
- **AC7** reads `README.md`, extracts the `## Releasing` section up to the
  next `## `, and asserts the two literals. It also asserts that the file it
  names defines `__version__ = "<segfacet.__version__>"`.

Adversarial cases. Write these and no others:

- `cwd-independence`: run AC1's invocation with `monkeypatch.chdir(tmp_path)`
  and compare to the same `HEAD`. Guards a resolver that reads the process
  cwd and so records the caller's repository (`spinelab`'s) commit instead
  of FACET's.
- `untracked-inside-a-work-tree`: `git init` a repo in `tmp_path` with one
  committed file, using `-c user.name=… -c user.email=…`, and an *untracked*
  `pkg/__init__.py`. `facet_revision(package_dir=<that pkg>)["commit"]` is
  `None`. Guards a non-editable install into a venv inside a checkout
  recording the enclosing checkout's unrelated commit.
- `no-git-on-path`: `monkeypatch.setenv("PATH", str(tmp_path))`.
  `facet_revision()` returns `commit is None` and does not raise. Guards a
  `FileNotFoundError` traceback on a host without git, such as the CPU
  Docker image.

**Existing tests to reconcile.** A text sweep of `tests/` for exact
top-level key sets over CLI-written reports found these. It is a lower
bound: the builder's full-suite run is the check.

- `tests/test_049_reference_integration.py::test_ac6_default_report_shape_matches_pre_item_shape`:
  its exact `expected_keys` gains `"facet_revision"`.
- `tests/test_065_cli_intensity.py::test_ac10_no_intensity_flag_report_shape_matches_pre_065_shape`:
  the same change.
- `tests/test_090_reference_derived_defaults.py::test_ac4_no_reference_flag_restores_reference_less_shape`:
  the same change.
- `tests/test_216_neighbour_pair_and_case_level_migration.py::test_ac2_every_top_level_container_is_one_the_table_populates`:
  the CLI report's container set would gain `facet_revision`, so
  `_NON_CONTENT_KEYS` gains `"facet_revision"`, beside `"run_manifest"`.
- `tests/test_215_per_label_migration.py`: it has the same
  `_NON_CONTENT_KEYS` tuple. By reading, its ACs do not fail, because AC1
  counts only `label`/`level_name` leaves and AC2 and AC3 read the
  catalogue. It is authorised so the builder may keep the tuple in step if
  the suite says otherwise.

The library-level key-set pins are unaffected, because the block is
omitted when `facet_revision` is `None`:
- `tests/test_009_json_report.py::test_golden_snapshot_keys_in_expected_set`;
- `tests/test_035_report_integration.py::test_ac13_omitted_findings_matches_item_009_shape`;
- the comparison-report pins in `tests/test_101_per_mode_cohort.py`.

Leave them as they are.

## Validation

Replay from the repository root on the claim branch:

1. Run `.venv/bin/segfacet run --scan <clean_control scan> --seg <clean_control seg> --out <scratch>/run --no-reference`, taking the two fixture paths from `tests/corpus/manifest.json`.
2. Check that `facet_revision.commit` in `<scratch>/run/segfacet_report.json`
   equals `git rev-parse HEAD`, and that `package_version` equals the
   `__version__` in `src/segfacet/__init__.py`.
3. Run `segfacet evaluate` over the same small cohort AC3 uses, and inspect
   `eval_report.json` the same way.

No special environment is needed.

## Dependencies

None.

**Downstream:** item 233 touches the same report module and schema, but
neither item pins what the other changes. Item 235 (stage validation) attests Stage 35 criterion 3
from AC1 and AC3 together with item 233's schema-version half.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether the plain-text reports (`segfacet_report.txt`,
  `eval_report.txt`) also print the revision. `spinelab` pins the JSON
  reports, and nothing declared reads the text ones.
- **Left open:** whether the `compare-runs` artefact
  (`per_mode_comparison.json`) carries a `facet_revision`. The interface
  names the per-case and evaluation reports only.
- **Left open:** `vision.md` §7.5 also lists the feature catalogue as
  carrying the revision. The catalogue is committed and byte-compared, so it
  cannot contain its own commit, and the commit that adds it is its
  revision. Whether `spinelab` needs more is for when it consumes one.
- **Left open:** `provenance.segfacet_version` in the evaluation report
  stays `null` from the CLI, beside the new
  `facet_revision.package_version`. Filling or retiring it changes the
  `EvaluationProvenance` contract that `compare-runs` reads, and no consumer
  asks for it.
- **Left open:** a dirty-tree marker (A5).
