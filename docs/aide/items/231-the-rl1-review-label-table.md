<!-- aide-template: item 3 -->
# Item 231 — The `rl1` review-label table read against a pinned schema

> **Created:** 2026-10-18 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 35 — Programme Interface: the SegFACET Side
> **Queue:** [`../queue/queue-031.md`](../queue/queue-031.md) · Item 231
> **Objectives:** G2, G7
> **Suggested branch:** `aide/231-the-rl1-review-label-table`

---

## Description

This is the reader half of Stage 35's third deliverable, the real-label
expectation. Item 230 built the harness half:
`segfacet.eval.label_outcome.label_mode_expectation(pairs)` turns
`(label, mode)` pairs into an `EvaluationCase.expected` mapping, and the
harness scores it per label.

`spine-failure-lab` (package `spinelab`) owns the schema of the review-label
table, schema tag `rl1`. The schema is the `review-label-fields` table of its
`docs/project/facet-interface.md`, adopted here at commit `7436b0f`
(`vision.md` §7.5). The interface's rule is that the consumer vendors a copy
of the schema pinned at a named commit and refuses an instance whose version
differs. This item does that:

- **The vendored schema.** `src/segfacet/eval/review_label_schema_rl1.json`
  holds the schema tag, the ten fields with their types, and the source it was
  copied from: repository, path, table anchor and the full `spinelab` commit.
- **The reader.** `segfacet.eval.review_labels.read_review_label_table(path)`
  reads the table (a CSV with a header row) into one mapping per row. It
  refuses a table whose header differs from the vendored field list, a row
  whose schema tag is not `rl1`, an integer field that does not parse, and a
  role outside the three dataset roles.
- **Rows become expectations.** `apply_review_labels(cases, rows)` gives each
  cohort case with at least one row the expectation `label_mode_expectation`
  builds from its rows' `(label_id, mode_id)` pairs. Mode 0 rows are the
  reviewed-clean labels. The case's role goes into `EvaluationCase.metadata`.
  A cohort case with no row is dropped, because a case nobody reviewed is not
  known to be clean (insight `2026-10-18-5f3f`).
- **The role rule.** `calibrate_thresholds` refuses a cohort holding a
  test-role case. This is the interface's rule that a label's use follows its
  case's role: a test label is never used to fit or calibrate.
- **The CLI.** `segfacet evaluate --review-labels <table.csv>` applies the
  table to the cohort the command already loads (`--cohort` or
  `--dataset-schema` / `--subset`). Item 235 replays the stage through this
  flag.

**Not in scope.**

- Pairing a candidate-role descriptor with a ground-truth descriptor. That is
  Stage 16 (item 229's Left open). With `--dataset-schema`, the cases stay the
  ground-truth cases the command already builds.
- How a transitional L5 is scored (insight `2026-10-12-76ac`, Stage 16's
  decision), and any use of the `call` field. `mode_id` is read as the table
  states it.
- Printing label metrics in the human-readable report (item 230's Left open).
- Writing an `rl1` table. `spinelab` writes it.

## Acceptance Criteria

Terms used below:

- **The vendored schema** is the mapping `load_rl1_schema()` returns, read
  from `src/segfacet/eval/review_label_schema_rl1.json`.
- **The vendored field names** are `[f["name"] for f in schema["fields"]]`.
- **A valid table** is a CSV file whose header row is exactly the vendored
  field names, and whose every data row has `schema` = `rl1`, integer
  `label_id` and `mode_id` cells, and a `role` in `{development, calibration,
  test}`.

- [ ] **AC1: The schema names its source.** `load_rl1_schema()["source"]`
  equals `{"repository": "spine-failure-lab", "path":
  "docs/project/facet-interface.md", "table": "review-label-fields", "commit":
  "7436b0f250dd413c2358600d9ea4d1adcace8696"}`.
- [ ] **AC2: The schema's tag.** `load_rl1_schema()["schema"]` equals `"rl1"`.
- [ ] **AC3: The schema's fields.** `[(f["name"], f["type"]) for f in
  load_rl1_schema()["fields"]]` equals the ten pairs of the field table under
  Assumptions A2, in that order.
- [ ] **AC4: A valid table is read row by row.** For a valid table,
  `read_review_label_table(path)` returns one mapping per data row, in file
  order. Each mapping's keys equal the set of vendored field names.
- [ ] **AC5: Integer fields are ints.** In each mapping AC4 returns,
  `label_id` and `mode_id` equal `int` of the row's cell, as `int` values.
- [ ] **AC6: A null cell is `None`.** In each mapping AC4 returns, an empty
  `call_provenance` cell is `None`. Every other value equals the row's cell
  string.
- [ ] **AC7: Another schema tag is refused.** A table with a row whose `schema`
  cell is not `rl1` makes `read_review_label_table` raise `FacetInputError`.
  The message names the tag found and the pinned tag `rl1`. *(closes Stage 35
  criterion 2)*
- [ ] **AC8: An unlisted field is refused.** A table whose header holds a
  column that is not a vendored field name makes `read_review_label_table`
  raise `FacetInputError`. The message names that column.
- [ ] **AC9: A missing field is refused.** A table whose header lacks a
  vendored field name makes `read_review_label_table` raise
  `FacetInputError`. The message names that field.
- [ ] **AC10: A non-integer cell is refused.** A table with a `label_id` or
  `mode_id` cell that `int()` cannot parse makes `read_review_label_table`
  raise `FacetInputError`. The message names that field.
- [ ] **AC11: An unknown role is refused.** A table with a row whose `role` is
  not one of `development`, `calibration`, `test` makes
  `read_review_label_table` raise `FacetInputError`. The message names that
  role value.
- [ ] **AC12: A reviewed case gets the table's expectation.** For each case
  that `apply_review_labels(cases, rows)` returns, its `expected` equals
  `label_mode_expectation([(r["label_id"], r["mode_id"]) for r in rows if
  r["case_id"] == case.case_id])`.
- [ ] **AC13: A reviewed case carries its role.** For each case that
  `apply_review_labels(cases, rows)` returns, `case.metadata["role"]` equals
  the `role` of its rows.
- [ ] **AC14: An unreviewed case is dropped.** The case ids that
  `apply_review_labels(cases, rows)` returns equal, in the input order, the
  ids of the input cases that some row's `case_id` names.
- [ ] **AC15: A case with two roles is refused.** `apply_review_labels` raises
  `FacetInputError` when two rows of one case carry different roles. The
  message names that case id.
- [ ] **AC16: Calibration refuses a test-role case.** `calibrate_thresholds`
  raises `FacetInputError` for a cohort with a case whose
  `metadata["role"]` is `"test"`. The message names that case id.
- [ ] **AC17: The CLI scores the table.** `segfacet evaluate --dataset-schema
  <descriptor> --subset <name> --review-labels <table> --out <dir>` writes
  `<dir>/eval_report.json`, whose `metrics.label_metrics` equals
  `compute_cohort_metrics(evaluate_cohort(apply_review_labels(cases,
  read_review_label_table(table)), bundled_default_config())).to_dict()
  ["label_metrics"]`. Here `cases` are the ground-truth cases the command
  builds from that descriptor subset. *(closes Stage 35 criterion 2)*

## Assumptions

`loop.clarify = "assume"`. Each entry records a default taken where the queue
line left a choice. A8 records the interface of item 230, which had already
merged when this spec was written: it was read from the merged code, so it is
not a pin written ahead of the build.

- **A1: The table is a CSV with a header row.** The interface does not name a
  file format. Its table is written by `spinelab`'s collation ("collation
  (Stage 8, extended)"), and that collation already writes a CSV
  (`spinelab.qc_collation.write_table`: a header row, `\n` line ends, UTF-8,
  `None` written as an empty cell). No `rl1` writer exists in `spinelab` yet
  (searched 2026-10-18), so this item reads the format its producer already
  uses: `csv.DictReader` over the file opened with `newline=""` and
  `encoding="utf-8"`. An empty cell of a `string or null` field reads as
  `None`.
- **A2: The vendored fields.** These are the field table's rows at
  `7436b0f250dd413c2358600d9ea4d1adcace8696`, copied 2026-10-18. Each field's
  type is the table's Type cell, verbatim:

  | name | type |
  | --- | --- |
  | schema | string |
  | case_id | string |
  | run_id | string |
  | mask_hash | string |
  | label_id | integer |
  | mode_id | integer |
  | call | string |
  | call_provenance | string or null |
  | reviewer | string |
  | role | string |

  The reader converts by type and nothing else: an `integer` field becomes an
  `int`, an empty `string or null` field becomes `None`, and a `string` field
  stays the cell's string. The `call` vocabulary (`tool-error`, `pathology`,
  `undetermined`) is stated only in the Meaning column and is not checked,
  because nothing here reads `call`.
- **A3: The header is compared as a list of names, in any order.** A header
  that names every vendored field exactly once is accepted in any column
  order. An unlisted column (AC8), a missing field (AC9) and a column named
  twice (adversarial case `duplicate-column`) are refused. The queue line asks
  for the first. The other two are refused because they would otherwise fail
  later, as a `KeyError`, or pass silently, since `csv.DictReader` keeps the
  last of two columns with one name.
- **A4: The schema tag is checked on every row.** The interface carries the
  tag as the table's first field, so each row states its version. One row at
  another tag refuses the whole table (AC7). A table with a header and no
  rows reads as an empty list.
- **A5: The three roles, one per case.** The role vocabulary is the
  interface's dataset-roles table: `development`, `calibration`, `test`. An
  unknown value is refused (AC11), because a misspelt `Test` would otherwise
  pass the test-role rule. A role belongs to a case ("the dataset role of the
  case"), so a case whose rows disagree is refused (AC15) rather than given
  one of the two.
- **A6: A cohort case with no row is dropped, and a row with no cohort case is
  ignored** (insight `2026-10-18-5f3f`). `label_mode_expectation([])` returns
  an expected-pass case with no pairs, so a case with no row would enter the
  cohort as a clean case it was never reviewed as. Dropping it keeps the rule
  item 230's A3 set for an unreviewed label: not looked at is not clean. The
  case is dropped rather than refused, because a role subset normally holds
  many more cases than the reviewers looked at. A row whose `case_id` names no
  cohort case is ignored, because one table covers all three roles while one
  run selects one subset. If no cohort case has a row, the CLI reports the
  empty cohort as an error, as `--dataset-schema` already does.
- **A7: The role rule sits in `calibrate_thresholds`.** "Fit or calibrate"
  has one consumer of expectations in this repository: the threshold
  calibration loop. `build-reference` reads ground truth and no expectation,
  so no table reaches it. The guard reads `EvaluationCase.metadata["role"]`.
  It refuses `"test"` only, which is the rule the queue line states (see
  Left open for the calibration role). It also refuses a case whose role came
  from a hand-written cohort manifest's `metadata`, since a case's role
  governs whatever set it.
- **A8: Item 230's interface, as merged** (read from
  `src/segfacet/eval/label_outcome.py` at `dec51639`, 2026-10-18).
  `label_mode_expectation(pairs)` takes an iterable of `(label_id, mode_id)`
  integer pairs and returns a `dict` with exactly the keys
  `"expected_verdict"` and `"label_modes"`. It deduplicates the pairs and
  raises `segfacet.io.FacetInputError` for an unknown mode, or for a label
  paired with both 0 and a non-zero mode. The harness reads `label_modes` from
  `EvaluationCase.expected` and carries `metadata` through unchanged. This
  item calls the helper and adds nothing to item 230's modules.
- **A9: One flag, both cohort sources.** `--review-labels` is applied after
  the command loads its cohort, whichever of `--cohort` or `--dataset-schema`
  loaded it, so both go through one call to `apply_review_labels`. AC17 tests
  the `--dataset-schema` path, which is the one item 235 replays.

## Implementation Steps

1. **New file `src/segfacet/eval/review_label_schema_rl1.json`.** Write it by
   hand from A2:
   `{"schema": "rl1", "source": {"repository": "spine-failure-lab", "path":
   "docs/project/facet-interface.md", "table": "review-label-fields",
   "commit": "7436b0f250dd413c2358600d9ea4d1adcace8696"}, "fields":
   [{"name": ..., "type": ...}, ...]}`, with the fields in the table's order.
   Write it with `\n` line ends. It is read with `read_text` and `json.loads`,
   so it needs no `.gitattributes` pin. Hatchling ships it as package data,
   as it does `eval_report_schema_v0.json` in the same directory.
2. **New module `src/segfacet/eval/review_labels.py`.** Its docstring names
   item 231, the interface and its commit, A1–A7 and the scope fence (no
   candidate pairing, no use of `call`). It holds:
   - `RL1_SCHEMA_TAG = "rl1"`, `REVIEW_ROLES = ("development", "calibration",
     "test")` and `ROLE_METADATA_KEY = "role"`.
   - `load_rl1_schema() -> dict`. It reads the JSON through
     `importlib.resources.files(segfacet.eval)`, the pattern of
     `segfacet.eval.report._load_eval_schema`.
   - `read_review_label_table(path) -> List[dict]`. It opens the file with
     `newline=""` and `encoding="utf-8"` and reads it with `csv.DictReader`.
     It compares `reader.fieldnames` with the vendored field names: duplicates
     first, then unlisted columns, then missing fields (AC8, AC9, A3). Then,
     row by row, it checks the tag (AC7) and converts by each field's type
     (AC5, AC6, AC10), then checks the role (AC11). Each message names the
     file and the CSV line (`reader.line_num`). Every error is
     `segfacet.io.FacetInputError`.
   - `apply_review_labels(cases, rows) -> List[EvaluationCase]`. It groups
     the rows by `case_id`, checks each group has one role (AC15), and walks
     `cases` in order. A case with no group is dropped (AC14). A case with a
     group is rebuilt with `dataclasses.replace`: `expected` becomes
     `label_mode_expectation(pairs)` (AC12), and `metadata` becomes the case's
     own metadata (or `{}`) with `ROLE_METADATA_KEY` set to the role (AC13).
     A `FacetInputError` from `label_mode_expectation` is re-raised with the
     case id prefixed (adversarial case `conflicting-reviews`).
   - `refuse_test_role(cases, *, purpose: str) -> None`. It raises
     `FacetInputError` naming every case whose `metadata` carries
     `ROLE_METADATA_KEY == "test"`, and the purpose. A case with no metadata
     passes.
3. **`src/segfacet/eval/calibrate.py`.** At the top of
   `calibrate_thresholds`, before the grid-size check, call
   `refuse_test_role(cases, purpose="threshold calibration")` (AC16). Add
   the new `Raises` entry to its docstring.
4. **`src/segfacet/cli.py`.** Add `--review-labels <csv>` to the `evaluate`
   subparser. Its help names the `rl1` schema and the role rule. In
   `_handle_evaluate`, after step 1 has loaded `cases`, read the table and
   apply it inside the existing `try` that catches `FacetInputError` (A9). If
   the result is empty, print an `Error:` line saying no cohort case has a row
   in the table, and return 1 (A6). Wrap the `calibrate_thresholds` call so a
   `FacetInputError` prints an `Error:` line and returns 1, not a traceback.
   Imports stay inside the handler, as the rest of the file does.
5. **`.github/workflows/ci.yml`.** Add `tests/test_231_review_label_table.py`
   to `jobs.test.env.WINDOWS_TESTS`. The module invokes `segfacet.cli`, one of
   the signals `tests/test_213_windows_ci_subset.py` classifies, and it must
   be listed for that test to pass.
6. **No change** to `label_outcome.py`, `harness.py`, `metrics.py`,
   `report.py`, `cohort.py` or `segfacet.datasets`. No dependency is added:
   `csv`, `json` and `importlib.resources` are stdlib.

## Authorised paths

**May change:**

- `src/segfacet/eval/review_label_schema_rl1.json` — the vendored `rl1` schema (AC1–AC3)
- `src/segfacet/eval/review_labels.py` — the reader, `apply_review_labels` and the role guard (AC4–AC15)
- `src/segfacet/eval/calibrate.py` — the test-role refusal at the top of `calibrate_thresholds` (AC16)
- `src/segfacet/cli.py` — `segfacet evaluate --review-labels` (AC17)
- `.github/workflows/ci.yml` — the new test module in `WINDOWS_TESTS`, which `tests/test_213_windows_ci_subset.py` requires
- `tests/test_231_review_label_table.py` — the item's tests

**Asserts against:**

- `src/segfacet/eval/label_outcome.py` — AC12 recomputes each expectation through `label_mode_expectation`, and AC17 recomputes `label_metrics` through the harness that reads it

## Testing Strategy

Test module: `tests/test_231_review_label_table.py`. It invokes the CLI
in-process (`segfacet.cli.main([...])`) for AC17, so it is OS-sensitive under
`tests/test_213_windows_ci_subset.py`'s rule and is listed in `ci.yml`'s
`WINDOWS_TESTS` (step 5).

Fixtures:

- **Tables** are written under `tmp_path` by a small helper that writes the
  header from `load_rl1_schema()`'s field names and rows from dicts, with
  `csv.writer(..., lineterminator="\n")`. The field list is read from the
  vendored schema, never re-typed, except in AC3, whose subject is the
  transcription itself.
- **Mode ids** in valid rows come from `segfacet.failure_modes.SPECIFICATION`
  keys, plus 0. A row's mode must be one `label_mode_expectation` accepts.
- **AC12–AC15** use `EvaluationCase` objects with placeholder `gt` values.
  `apply_review_labels` loads no image, so no label map is needed.
- **AC16** needs no label map either: the refusal comes before any case is
  evaluated. Pass `default_calibration_axes()` and `bundled_default_config()`.
- **AC17** writes a dataset descriptor under `tmp_path` that resolves at
  least two synthetic ground-truth masks (`tests/synthetic.py`), following the
  descriptor-in-`tmp_path` pattern of `tests/test_087_dataset_cli.py`, with
  one named subset. The table gives one case a non-zero mode and a mode-0
  label, and another case a mode-0 label only. It leaves one resolved case
  unreviewed, so AC17 also runs the drop. The expected `label_metrics` is
  recomputed from the live library calls, never from literals, so the fixture
  needs no particular rule to fire. If the test-writer wants a label
  `detected` as well, whether `run_qc` fires on that map is live pipeline
  behaviour: probe it with a standalone scratch script before writing it in
  (insights `2026-10-18-661d` and `2026-10-18-7035`). AC17 does not need
  that.

Adversarial cases, each with the failure mode it guards:

- `duplicate-column`: a header naming `mode_id` twice is refused, and the
  message names `mode_id`. This guards `csv.DictReader` silently keeping the
  second column's values (A3).
- `crlf-table`: a valid table written with `\r\n` line ends reads to the same
  mappings as the `\n` version. This guards a `\r` left on the last header
  name (`role\r`), which would refuse a table written on Windows as having an
  unlisted field.
- `empty-table`: a header-only valid table reads as `[]`, and
  `apply_review_labels(cases, [])` returns `[]`. This guards a header-only
  table raising, and the drop rule turning every case into a vacuous
  expected-pass case (A6, insight `2026-10-18-5f3f`).
- `unknown-mode-row`: a valid row whose `mode_id` is not a specified mode
  makes `apply_review_labels` raise `FacetInputError`, and the message names
  the case id. This guards a row passing the reader and failing later,
  unnamed, at scoring.
- `conflicting-reviews`: two rows of one case pair one label with mode 0 and
  with a non-zero mode, and `apply_review_labels` raises `FacetInputError`
  whose message names the case id. This guards two reviews of one case that
  disagree surfacing with no case to look at.
- `row-outside-cohort`: a row whose `case_id` names no input case leaves the
  returned cases the same as without that row. This guards an all-roles
  table refusing a one-subset run (A6).
- `metadata-kept`: an input case with `metadata={"source": "x"}` comes back
  with `"source"` unchanged beside `"role"`. This guards the role overwriting
  a manifest case's own metadata.
- `calibration-role-allowed`: `calibrate_thresholds` over a cohort whose only
  role is `"calibration"` does not raise the test-role refusal. Use a
  one-value axis and one corpus case so the sweep is a single evaluation. This
  guards a guard that refuses every role-tagged case.

**Existing tests to reconcile: none.** The sweep (`grep` over `tests/` for
`calibrate_thresholds` callers, `metadata` on `EvaluationCase`, a `"role"`
metadata key, and pins of the `evaluate` subparser's options) found no test
whose cases carry a `"test"` role and no test pinning the evaluate option
set. `tests/test_075_cli_backend.py` reads only the `--backend` action.
`tests/test_213_windows_ci_subset.py` passes once step 5 lists the new
module.

## Validation

The suite cannot reach the primary source of A2: it is in a sibling
repository at a pinned commit. The validator checks the transcription once,
on the branch:

1. From a local clone of `spine-failure-lab` (a declared sibling,
   `.aide/local.toml`), run `git -C <clone> show
   7436b0f250dd413c2358600d9ea4d1adcace8696:docs/project/facet-interface.md`.
   Read the table under `<!-- table: review-label-fields -->`.
2. Compare its Field and Type columns, row by row and in order, with
   `src/segfacet/eval/review_label_schema_rl1.json`'s `fields`. They must be
   equal.
3. With no clone on the validating machine, record the transcription check as
   `❓ Unverified` under Decisions & Trade-offs, with the reason. Never pass
   it silently.

## Dependencies

- Item 230 — `label_mode_expectation` and the harness's per-label scoring (A8). Merged.

**Downstream:** item 235 replays the stage through `segfacet evaluate
--review-labels`. Stage 16 scores real `rl1` tables through this reader.

## Decisions & Trade-offs

- **Header order is free; checks run duplicates, unlisted, missing.** As A3
  states. A row whose `schema` cell is another tag is refused before any cell of
  that row is converted, so the tag message is never masked by a type error.
- **`calibrate.py` imports `refuse_test_role` inside the function.** The guard
  lives in `review_labels.py` (which imports the harness); a function-local
  import keeps `calibrate.py`'s module-level imports unchanged.
- **CLI.** The table is read and applied in the existing step-1 `try`, so any
  `FacetInputError` is an `Error:` line and exit 1. An all-dropped cohort
  prints `no cohort case has a row in the --review-labels table` and exits 1
  (A6). The `calibrate_thresholds` call now catches `FacetInputError` the same
  way, so a test-role cohort with `--calibrate` is an error line, not a
  traceback.
- **Transcription check (Validation step 3): ❓ Unverified by the builder.**
  The builder did not open the `spine-failure-lab` clone; the field list was
  copied from A2. The validator performs the comparison against commit
  `7436b0f2` per the Validation section.

- **Left open:** whether threshold calibration should also refuse
  calibration-role cases. The interface's dataset-roles table gives FACET's
  calibration role to held-out false-positive rate and per-mode sensitivity,
  and threshold calibration to the development role. The queue line names
  only the test role, so that is the rule enforced. Stage 16 is the first
  calibration on real labels, and it decides.
- **Left open:** whether a table row whose `case_id` matches no cohort case
  should be reported. It is ignored (A6), so a misspelt id is silent. A
  report needs to know which cases the table should have matched, and that is
  the candidate-to-ground-truth pairing Stage 16 builds.
- **Left open:** whether the `call` field changes scoring. A `pathology` call
  says a reviewer saw anatomy rather than a tool error. It is the same
  question as insight `2026-10-12-76ac`, so it is Stage 16's decision.
