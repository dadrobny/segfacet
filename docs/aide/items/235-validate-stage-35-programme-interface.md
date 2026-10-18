<!-- aide-template: item 3 -->
# Item 235 — Validate stage 35: Programme Interface: the SegFACET Side

> **Created:** 2026-10-18 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 35 — Programme Interface: the SegFACET Side
> **Queue:** [`../queue/queue-031.md`](../queue/queue-031.md) · Item 235
> **Objectives:** G2, G3, G7
> **Suggested branch:** `aide/235-validate-stage-35-programme-interface`

---

## Description

Stage 35's validation item. Items 228–234 each proved their own deliverable
against their own tests. This item asks the stage-level question: does the
merged tree, measured from a clean clone and on the real VerSe releases, meet
the five criteria in [`roadmap.md`](../roadmap.md)'s Stage 35 "Validation /
acceptance" block? It records the measured answer in `progress.md` one
criterion at a time, **including where the answer is no.** It fixes nothing it
finds.

The five criteria, verbatim:

1. A descriptor whose subsets are case-id lists resolves exactly those cases,
   and the VerSe19 and VerSe20 descriptors resolve the three role subsets over
   the release splits (**G7**).
2. An `rl1` table at the pinned version becomes a per-label,
   several-modes-per-case expectation the evaluation harness scores against,
   and a table at any other version is refused (**G2**).
3. Every per-case and evaluation report carries the FACET commit and a schema
   version, and a feature path that moves without a schema-version change fails
   the suite (**G7**).
4. The rebuilt reference draws only on development-role cases, and no
   calibration-role or test-role case contributes to it (**G3**).
5. `spline_offset.max_offset_mm` is re-derived from the rebuilt distribution,
   and the excluded wedge-vertebra label contributes nothing to it (**G3**).

**Where the boxes stand on 2026-10-18** (base `0d20543e`). Criteria 2, 4 and 5
are ticked by item validators on their own branches: criterion 2 by item 231's,
criteria 4 and 5 by item 234's. Criteria 1 and 3 are unticked. Each joins two
items: criterion 1 joins item 228's list-form subsets and item 229's role
subsets, and criterion 3 joins item 232's revision block and item 233's
schema-version pin. Neither item of a pair closes its criterion alone (item 229
"Why each AC is here", item 232 and item 233 Downstream). So this item **accepts**
criteria 1 and 3 and **amends** criteria 2, 4 and 5 with clean-clone evidence.

**What was actually built, read from the merged specs** (not from the queue's
one-liners):

- **Item 228** kept the existing `{"ids": [...]}` selector as the list form.
  It made a listed id with no mask an error naming every such id, and it
  refuses a malformed selector at construction (key set and value types).
- **Item 229** added `verse20.yaml` and renamed `verse19.yaml`'s
  `training`/`validation` subsets to `development`/`calibration`, with no
  aliases. The VerSe20 case id drops the `dir-` entity. VerSe20's committed
  `data_root` is the relative placeholder `VerSe20`, so a run passes
  `--data-root`.
- **Items 230 and 231**: `label_mode_expectation`, per-label scoring and
  `label_metrics`; then the vendored `review_label_schema_rl1.json` pinned at
  `spine-failure-lab` commit `7436b0f250dd413c2358600d9ea4d1adcace8696`, the
  CSV reader that refuses any other `schema` tag, and
  `segfacet evaluate --review-labels`. A cohort case with no row is dropped.
  Item 231's transcription check against the sibling's field table was
  recorded `❓ Unverified` by its builder and handed to its validator, and
  nothing in its spec records the result.
- **Item 232**: a `facet_revision` block (`commit`, `package_version`) in
  every report `segfacet run` and `segfacet evaluate` write. The commit is
  `HEAD` of the work tree that tracks the imported package's source.
- **Item 233**: the report `schema_version` moved to `"0.2"`
  (`segfacet.report.REPORT_SCHEMA_VERSION`). The committed pin
  `src/segfacet/report_schema_pin.json` ties it to the catalogue's leaf-path
  set, and `pin_conflicts()` is asserted empty by
  `tests/test_233_report_schema_pin.py::test_ac2_shipped_tree_has_no_pin_conflict`.
  The evaluation report's `EVAL_REPORT_SCHEMA_VERSION` stays `"0.1"`.
- **Item 234**: `scripts/rebuild_verse_reference.py` builds from the
  `development` role of both descriptors, refuses a role overlap, records
  `provenance.case_ids`, and withholds `sub-verse406_split-verse261` T10's
  `spline_offset_mm`. The committed artifact is 141 subjects (80 VerSe19 + 61
  VerSe20). The owner's decisions of 2026-10-18 stand as recorded in item 234's
  dated corrections:
  - the interior `max_offset_mm` is the derived **8.0 mm**;
  - terminals keep **13.0 mm** under the new `max_terminal_offset_mm`;
  - the two label-21 `spline_offset` findings at 8.0 mm on operator-default
    fixtures are accepted as real behaviour;
  - `CLAUDE.md` is not edited by item 234.

  `docs/reference-build.md`'s item-234 record states that a second, real
  determinism rebuild was **not run**, so the byte-identity of two real
  rebuilds is unverified there. This item runs that rebuild (AC14).

**"From a clean clone" means a fresh `git clone` with its own venv**, the rig
the Stage 29–33 and Stage 27 validation items used (item 135's rig). The
editable-install shadowing gotcha in `CLAUDE.md` is why: with a second tree on
`PYTHONPATH`, the working checkout can resolve `segfacet` ahead of it. Insight
`2026-10-05-dc87` also binds. A tree copied without `.git` lets git-gated tests
skip silently, and item 232's commit check needs `.git`. So the replay runs
from a real clone, and every pytest run it records lists its skips.

**The stage's use case, end to end.** The queue line asks for two real-data
runs where the VerSe data is present:
- `segfacet evaluate` over a VerSe role subset with a table-backed
  expectation (AC6, AC7);
- a reference build from the development role (AC14, Assumption A6).

The project host holds both releases.

**In scope:**

- the clean-clone replay, the real-data runs, and their recorded measurements;
- Stage 35's acceptance bookkeeping in `progress.md`, through `aide progress
  accept`, `amend` and, where a ticked criterion's replay fails, `retract`;
- one-line `insights.md` findings.

**Not in scope:**

- Fixing anything the replay finds. Each divergence becomes a finding.
- Any change under `src/segfacet/**`, `scripts/**`, `tests/**` or
  `.github/**`, and any committed artifact.
- `CLAUDE.md`'s stale item-090 finding count (insight `2026-10-18-8f8f`). The
  owner decided on 2026-10-18 that it is fixed in a separate reviewed edit, and
  `CLAUDE.md` is a process file.
- The Stage 16 deferral lines that read "Resumed when Stage 35 closes". Those
  bullets also wait on `gate-9776`, the hand-off bundle gate, and resuming them is a planning decision.
- Ticking, rewording or archiving any existing `insights.md` entry.

## Acceptance Criteria

Every criterion here is a **replay** criterion, as in item 217. The builder
executes it and the validator re-executes it. The observed output is recorded
verbatim in Decisions & Trade-offs, and no criterion adds a test (A2).

Terms used below:

- **The clone** is AC1's clone.
- **Passes in the clone** means the named modules or node ids exit `0` with no
  skip among them. They are run in the foreground from the clone's venv, with
  `-P -c <clone>/pyproject.toml --rootdir <clone> -ra`.
- **Clone HEAD** is the SHA AC1 records.
- **The VerSe19 root** is the host's three-split VerSe19 directory, the one
  `verse19.yaml`'s `data_root` names. **The VerSe20 root** is a
  machine-local directory of symlinks that presents the host's VerSe20 splits
  under the release names `dataset-01training`, `dataset-02validation` and
  `dataset-03test` (item 229 A1). Neither path is written into any committed
  file (A4).
- A criterion annotated *(closes Stage 35 criterion M)* is evidence for that
  criterion. A criterion with no annotation closes none.

### The clean-clone rig

- [ ] **AC1: the replay runs in a fresh clone whose code is the clone's own.**
  Clone this branch into the session scratchpad with `git clone`. Bootstrap
  the clone's venv with `python <clone>/.aide/scripts/aide.py --repo <clone>
  env --bootstrap`. Record three things:
  - that the clone exists (its path goes in the return to the orchestrator,
    not into this spec);
  - Clone HEAD, read with `git ls-remote <clone> HEAD`, which equals this
    branch's tip at clone time;
  - `segfacet.__file__` as printed by `<clone>/.venv/bin/python -P`, which
    resolves under the clone.

  If it resolves under the working checkout, every clone result below is
  invalid.

### Stage 35's own modules

- [ ] **AC2: every Stage 35 item's test module passes in the clone with the
  VerSe variables unset.** With `SEGFACET_VERSE_COHORT` and
  `SEGFACET_VERSE20_COHORT` unset, run these modules in the clone. They pass,
  apart from the real-data tests of `test_229`, `test_234` and `test_088`,
  which skip here and run in AC3. Record each skip by node id.
  - `tests/test_228_case_id_list_subsets.py`
  - `tests/test_229_verse_role_subsets.py`
  - `tests/test_230_label_mode_expectation.py`
  - `tests/test_231_review_label_table.py`
  - `tests/test_232_facet_revision.py`
  - `tests/test_233_report_schema_pin.py`
  - `tests/test_234_development_role_reference.py`
  - `tests/test_086_datasets.py`, `tests/test_087_dataset_cli.py` and
    `tests/test_088_stage13_acceptance.py`: root subsets as before, and the
    stand-in CLI build through `--subset development`
  - `tests/test_123_recalibrate_and_regenerate.py`: its AC12 carries item
    234's AC12

  The skipped node ids are exactly the `@requires_*`-marked tests of those
  three modules. Any other skip fails this criterion.
  *(closes Stage 35 criterion 1)* *(closes Stage 35 criterion 3)*
- [ ] **AC3: the real-data tests pass in the clone on both releases.** Set
  `SEGFACET_VERSE_COHORT` to the VerSe19 root and `SEGFACET_VERSE20_COHORT` to
  the VerSe20 root, and run in the clone:
  `tests/test_229_verse_role_subsets.py`,
  `tests/test_234_development_role_reference.py` and
  `tests/test_088_stage13_acceptance.py`, with
  `--deselect tests/test_088_stage13_acceptance.py::test_real_verse_clause_is_genuine_skip`.
  The run passes with no skip. The deselect is insight `2026-10-18-62a6`: that
  test asserts the real-data clause skips, so it fails whenever the variable is
  set. No other module runs with the variables set (A5). Record the `-ra` line
  for each of `test_229` AC5–AC7, `test_234` AC9–AC11 and
  `test_088::test_real_verse_resolves_training_split`.
  *(closes Stage 35 criterion 1)* *(closes Stage 35 criterion 4)*
  *(closes Stage 35 criterion 5)*

### Stage 35 criterion 1: list subsets and role subsets

- [ ] **AC4: each role subset of each bundled descriptor resolves exactly the
  masks of its release split, on the real data.** In the clone's venv, for
  each of the six (descriptor, role) pairs, compute two id sets:
  - `resolve(load_descriptor(bundled_descriptor_path(<name>)), data_root=<root>, subset=<role>).case_ids`;
  - the ids recomputed independently, one per `*_seg-vert_msk.nii.gz` that
    `Path.rglob` finds under `<root>/<split dir>/derivatives/`. The id is
    derived with the descriptor's own `case_id` regex applied to the file
    name.

  The pairs are (`development`, training), (`calibration`, validation) and
  (`test`, test) for each release. For every pair the two sets are equal, and
  their size equals the number of masks the walk found. Record the six
  counts. They were 80 / 40 / 40 for VerSe19 and 61 / 80 / 73 for VerSe20 at
  spec time (item 234 A1).
  *(closes Stage 35 criterion 1)*
- [ ] **AC5: a case-id-list subset over the real VerSe20 data resolves exactly
  the listed cases.** In the clone's venv, build a scratch descriptor that is
  `verse20.yaml`'s content plus one subset `picked: {ids: [...]}`. It names
  three VerSe20 development case ids: the first, the middle and the last of
  AC4's sorted development ids. `resolve(..., data_root=<VerSe20 root>,
  subset="picked").case_ids` equals the sorted tuple of those three ids. The
  scratch descriptor lives in the scratchpad and is not committed.
  *(closes Stage 35 criterion 1)*

### Stage 35 criterion 2: the `rl1` table

- [ ] **AC6: the vendored `rl1` schema equals the sibling's field table at the
  pinned commit.** First read `spine-failure-lab`'s instruction file (§8).
  Then run `git -C <spine-failure-lab clone> show
  7436b0f250dd413c2358600d9ea4d1adcace8696:docs/project/facet-interface.md`
  (the repository is declared in `.aide/local.toml`) and read the table under
  `<!-- table: review-label-fields -->`. Its (Field, Type) pairs, in order,
  equal `[(f["name"], f["type"]) for f in load_rl1_schema()["fields"]]` read
  in the clone. `load_rl1_schema()["source"]["commit"]` equals that commit.
  This is item 231's Validation, which nothing records as done. With no
  sibling clone on the host, record this criterion `❓ Unverified` with the
  reason.
  *(closes Stage 35 criterion 2)*
- [ ] **AC7: `segfacet evaluate` scores a real VerSe role subset against an
  `rl1` table.** Write a scratch `rl1` table (A7) for two VerSe20
  calibration-role cases. These are the two of AC4's calibration ids whose
  mask files are smallest by byte size.
  - Case 1: every label in its mask is mode 0, except its lowest label at
    mode `m1` and its highest label at mode `m2`. `m1` and `m2` are the two
    smallest keys of `failure_modes.SPECIFICATION`.
  - Case 2: every label in its mask is mode 0.

  Every row has `schema` `rl1` and `role` `calibration`. The labels are read
  from each mask (the non-zero `numpy.unique` values). From the clone's venv,
  run `segfacet evaluate --dataset-schema <bundled verse20.yaml> --data-root
  <VerSe20 root> --subset calibration --review-labels <table> --out <dir>`.
  It exits `0`. Its `<dir>/eval_report.json` `metrics.label_metrics` equals
  `compute_cohort_metrics(evaluate_cohort(apply_review_labels(cases,
  read_review_label_table(<table>)), bundled_default_config())).to_dict()["label_metrics"]`,
  computed in-process in the clone. Here `cases` are built exactly as
  `_handle_evaluate` builds them from the same resolved subset: one
  `EvaluationCase(case_id=c.case_id, gt=c.seg_path,
  expected={"expected_verdict": "pass"})` per resolved case. Record the table
  rows, both cases' ids and the `label_metrics` block.
  *(closes Stage 35 criterion 2)*
- [ ] **AC8: the same run with a table at another schema version is
  refused.** Copy AC7's table and set the first data row's `schema` cell to
  `rl2`. AC7's command, with this table and a fresh `--out`, exits `1`. Its
  stderr names both `rl2` and `rl1`, and no `eval_report.json` is written.
  *(closes Stage 35 criterion 2)*

### Stage 35 criterion 3: revision and schema version

- [ ] **AC9: a per-case report from a real case carries Clone HEAD.** From
  the clone's venv, run `segfacet run --scan <scan> --seg <seg> --out <dir>`
  with no reference flag on AC7's case 1. The scan and seg come from its
  resolved `scan_path` and `seg_path`. The run exits `0`, and
  `<dir>/segfacet_report.json`'s `facet_revision.commit` equals Clone HEAD.
  *(closes Stage 35 criterion 3)*
- [ ] **AC10: that per-case report's schema version is the pinned one.** AC9's
  report's `schema_version` equals `segfacet.report.REPORT_SCHEMA_VERSION`, as
  read in the clone. It also equals the `schema_version` of the clone's
  `src/segfacet/report_schema_pin.json`.
  *(closes Stage 35 criterion 3)*
- [ ] **AC11: AC7's evaluation report carries Clone HEAD and its schema
  version.** AC7's `eval_report.json` has a `facet_revision.commit` equal to
  Clone HEAD, and a `schema_version` equal to
  `segfacet.eval.report.EVAL_REPORT_SCHEMA_VERSION` read in the clone.
  *(closes Stage 35 criterion 3)*
- [ ] **AC12: a feature path renamed in the code without a version change
  fails the suite.** In the clone only, edit one key string literal in a
  module under `src/segfacet/features/`. The key must be the last segment of
  a path the pin lists. Rename it by appending `_item235_renamed` and change
  no version. Record the file's `sha256sum` before the edit. Then
  `tests/test_233_report_schema_pin.py::test_ac2_shipped_tree_has_no_pin_conflict`
  fails in the clone, and its failure output names both the old path and the
  renamed path. Record the file, the line, the old key and the failure
  output.
  *(closes Stage 35 criterion 3)*
- [ ] **AC13: the reverted file is byte-identical to the committed one, and
  the same node passes.** Undo AC12's edit. The file's `sha256sum` equals the
  one AC12 recorded before the edit, and
  `tests/test_233_report_schema_pin.py::test_ac2_shipped_tree_has_no_pin_conflict`
  passes in the clone. Every later criterion runs on this reverted clone.

### Stage 35 criteria 4 and 5: the development-role reference

- [ ] **AC14: a fresh development-role rebuild in the clone matches the
  committed artifact.** From the clone's venv, run
  `scripts/rebuild_verse_reference.py --out <scratch> --verse-cohort <VerSe19
  root> --verse20-cohort <VerSe20 root> --build-date <the committed
  artifact's provenance.build_date> --jobs <n>`. Choose `<n>` for the host
  and record it. The run exits `0` and writes `<scratch>/reference_verse_v1.json`.
  `segfacet.synth.golden.assert_matches_committed_artifact(<that file>,
  <clone>/src/segfacet/reference/reference_verse_v1.json)` raises nothing.
  Record:
  - the wall time;
  - the fresh file's sha256 against the committed file's;
  - whether the two files' `read_bytes()` are equal.

  Byte equality is a recorded fact, not the bar (A9). This is item 234's
  unrun determinism rebuild, and it is the reference build the queue line
  asks for (A6). *(closes Stage 35 criterion 4)*
- [ ] **AC15: the rebuild ingested the development roles and nothing else.**
  AC14's `<scratch>/verse_rebuild_summary.json` has `cohort.status` and
  `build.status` both `"ran"`. Its `cohort.case_ids` equals the sorted union
  of AC4's two `development` id sets. Its `cohort.role_counts` equals AC4's
  six counts, per release and role.
  *(closes Stage 35 criterion 4)*
- [ ] **AC16: the rebuild withheld exactly the excluded label.** AC14's
  summary `calibration.excluded_offsets` is a one-element list. Its
  `case_id` is `sub-verse406_split-verse261` and its `level_name` is `T10`.
  Record its `offset_mm`: 18.51028119357566 in item 234's record.
  *(closes Stage 35 criterion 5)*
- [ ] **AC17: the shipped interior threshold is the one the fresh rebuild
  derives.** In the clone's venv,
  `derive_max_offset_mm(load_artifact(<AC14's fresh file>))` equals
  `segfacet.heuristics.spline_offset._DEFAULT_MAX_OFFSET_MM`.
  `derive_max_offset_mm` is the tool's own function, loaded the way
  `tests/test_123_recalibrate_and_regenerate.py` loads it. Record both values
  and the P level and count from `_p99_by_level`: 8.0 mm, `L4` and 106 in
  item 234's record.
  *(closes Stage 35 criterion 5)*

### Bookkeeping

- [ ] **AC18: each criterion is attested through the matching verb, and no box
  is ticked on evidence that failed.** Record the exact command and evidence
  text for each criterion, in ascending order:
  - **Criterion 1:** `aide progress accept 35 --criterion 1 --evidence "…"`,
    citing AC2–AC5.
  - **Criterion 2:** `aide progress amend 35 --criterion 2 --evidence "…"`,
    citing AC6–AC8.
  - **Criterion 3:** `aide progress accept 35 --criterion 3 --evidence "…"`,
    citing AC2 and AC9–AC13.
  - **Criterion 4:** `aide progress amend 35 --criterion 4 --evidence "…"`,
    citing AC3, AC14 and AC15.
  - **Criterion 5:** `aide progress amend 35 --criterion 5 --evidence "…"`,
    citing AC3, AC16 and AC17.

  Each text names the ACs behind it, Clone HEAD and the measured values. A
  failure is handled by the box's state:
  - **An unticked criterion (1 or 3) whose ACs do not all hold** stays
    unticked. Append a hand-written ` *(not attested 2026-MM-DD, item 235:
    <measured reason>)*` to the end of its last line, and append one `gap`
    line naming the stage, the criterion and the reason with `aide insights
    add`.
  - **A ticked criterion (2, 4 or 5) whose replay ran and failed** is
    withdrawn with `aide progress retract 35 --criterion N --reason "…"`,
    which captures its own `gap` insight.
  - **A ticked criterion whose replay could not run** keeps its tick. Its
    `amend` line states which replay was not performed and why (A9).

### Environment and suite

- [ ] **AC19: Stage 35 adds no environment-gated row, and the table is left
  unchanged.** Confirm and record two facts:
  - no row of `progress.md`'s Environment-Gated Capability Verification table
    names Stage 35, or any of items 228–235, in its "Introduced by" cell;
  - no item spec numbered 228–234 carries a `## Environment / Hardware
    Dependencies` section.

  Items 229 (A7) and 234 (A15) place the VerSe20 data under the existing "Real
  VerSe GT reference distributions" row. That row is not edited. Record the
  output and exit code of `python .aide/scripts/aide.py env` and of `env
  --profile pyradiomics`, `--profile docker` and `--profile gpu`.
- [ ] **AC20: the full configured suite is green in a fresh clone of the final
  commit, with the VerSe variables unset.** Once every commit of this item has
  landed:
  1. Bring AC1's clone up to the branch tip with `python
     <clone>/.aide/scripts/aide.py --repo <clone> sync --item 235`.
  2. Re-print AC1's resolution proof.
  3. Unset `SEGFACET_VERSE_COHORT` and `SEGFACET_VERSE20_COHORT` (insights
     `2026-10-18-62a6` and `2026-10-17-e94a`).
  4. Run the configured suite from the clone's venv in the foreground with
     `-n auto`. Pass both `testpaths` (`<clone>/tests` and
     `<clone>/.aide/scripts/tests`) explicitly, as item 204 did.

  Record the pass, skip and fail counts, the commit, and the reason for each
  environment-gated skip. The run has no failures. A skip is never recorded as
  verification.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Items
228–234 had all merged (✅) when this spec was written, so nothing here pins an
interface ahead of its build. Every value was read on 2026-10-18 at
`0d20543e`.

- **A1: the clone rig is item 204's.** That is a `git clone` of this branch
  into the scratchpad, with the clone's own `aide env --bootstrap`. Every
  pytest run uses `-P`, `-c <clone>/pyproject.toml` and `--rootdir <clone>`,
  so the working checkout's `tests` package cannot shadow the clone's. The
  clone's HEAD is read with `git ls-remote <clone> HEAD`, a single command with
  no repo-override wrapper (§3). The clone and every scratch file live in the
  session scratchpad and are deleted after AC20.
- **A2: no new test module, and no `ci.yml` change.** Under posture
  `prototype`, a test is written only where the deliverable fails without it.
  Each criterion half already has a merged in-suite check (AC2, AC3). The
  remaining evidence is real-data or clone-specific, which the suite cannot
  hold:
  - a role subset over the real release (AC4);
  - the sibling's field table at a pinned commit (AC6);
  - a real VerSe case through the CLI (AC7–AC11);
  - a code mutation the suite must catch (AC12);
  - the real rebuild (AC14–AC17).

  So `.github/workflows/ci.yml`'s `WINDOWS_TESTS` is not touched. Item 217 is
  the precedent for a validation item with no test module.
- **A3 (engine 2.52.2): which verb each box takes.** `accept` reports an
  already-ticked box as unchanged, so the ticked criteria 2, 4 and 5 take
  `amend`, which appends a dated line and keeps the tick. Item 204's A5 read
  the same behaviour at engine 2.25.0. A ticked criterion whose replay fails
  takes `retract`. It unticks the box, keeps the original attestation visible
  and captures a `gap` insight (`aide progress -h`, engine 2.52.2). `aide
  merge 235` flips this item's 📋 deliverable bullet. Stage 35 then rolls up
  only if all five boxes are ticked. No bullet is hand-edited.
- **A4: the two real-data roots are named by role, never by path.** The
  VerSe19 root is the host directory `verse19.yaml`'s committed `data_root`
  already names (insight `2026-10-18-4313` records that this is a machine
  path). The local VerSe20 copy names its splits `01_training`,
  `02_validation` and `03_test`, so it is presented through a directory of
  symlinks in the session scratchpad that carry the release names (item 229
  A1, item 234 step 6). That directory is machine-local. If it is missing in
  the builder's session, it is recreated the same way. Its path, and the
  clone's, go in the return to the orchestrator, and never into this spec,
  `progress.md` evidence or any committed file.
- **A5: what runs with the VerSe variables set.** Only AC3's three modules
  run with them set, with insight `2026-10-18-62a6`'s deselect. Every other
  VerSe-gated module is left out of AC3: `test_084`, `test_091`, `test_118`,
  `test_125` and `test_240`. They test earlier stages, and
  `tests/test_125_stage28_validation.py`'s AC10 expects a training-only root
  (insight `2026-10-17-e94a`), so no single value runs them all green. AC20's
  full suite runs with both variables unset, where those modules skip.
- **A6: the queue's "`segfacet build-reference` from the development role" is
  replayed through the rebuild tool.** Since item 234, the committed
  development-role reference is produced by
  `scripts/rebuild_verse_reference.py`. It merges the `development` roles of
  both descriptors, refuses a role overlap and withholds the `gate-fac1`
  reading. `segfacet build-reference` takes one descriptor, has no `--jobs`
  flag and applies no exclusion. Its whole development-role build is serial:
  item 234 A14 measured about 19 CPU-hours for 141 cases, and over 90 minutes
  for the slowest single case. So the CLI's `--subset development` path is
  held in-suite by
  `tests/test_088_stage13_acceptance.py::test_standin_build_reference_and_evaluate_cli`
  (AC2). The real build is the tool (AC14), which also closes item 234's
  unrun determinism rebuild.
- **A7: the AC7 table is a synthetic stand-in on real data.** No real `rl1`
  table exists in this repository until `gate-9776`'s hand-off bundle (the gate earlier records call `gate-ae46`)
  arrives. The non-zero modes in AC7's table are fictitious labels over
  ground truth. The replay proves the reader-to-harness path on real cases
  and the CLI-equals-library equality, not a sensitivity. How a real label is
  scored stays Stage 16's question (insight `2026-10-12-76ac`). The reader
  does not check these columns, so they carry placeholders, recorded in
  Decisions:
  - `run_id` and `reviewer`: `item-235-replay`;
  - `mask_hash`: the mask file's sha256;
  - `call`: `tool-error` on the two non-zero rows and `undetermined` on the
    mode-0 rows;
  - `call_provenance`: empty.
- **A8: the mutation in AC12 is a clone-only edit, reverted before anything
  else runs.** The clone is a scratch copy, so its tree is the one place a
  deliberate defect can be observed through the suite without touching this
  branch. The key renamed is the builder's choice, under AC12's two
  constraints, and it is recorded. AC13's before-and-after `sha256sum` proves
  the revert, so AC14–AC20 run on unmutated code. The clone's `aide sync` is
  not the check: it also pulls the working branch's newer commits into the
  clone, which would move Clone HEAD in the middle of the replay.
- **A9: AC14's bar is the tolerance comparison, not byte equality.**
  `CLAUDE.md` names `assert_matches_committed_artifact` as the route for any
  fresh-vs-committed comparison. The clone's freshly bootstrapped venv may
  carry different NumPy/SciPy patch versions from the venv that built the
  committed file. Byte equality is recorded as a fact. A rebuild that cannot
  run is recorded as **not performed**, naming what was missing, such as the
  data or the host time. Criterion 4's and 5's ticks then stand on item 234's
  evidence, and the `amend` lines say so. A rebuild that runs and fails the
  comparison is a finding, and its criterion is retracted (A3).
- **A10: no new human gate.** Every decision this stage needed is recorded:
  `gate-fac1` (approved 2026-10-16), and the owner's 2026-10-18 decisions in
  item 234. Item 232's tagging scheme is A1 of item 232, a default the owner
  confirms at the queue boundary. It is not a criterion of Stage 35's.
- **A11: AC2 and AC3 each close more than one criterion, deliberately.** One
  pytest run is the evidence for several criteria (item 204's AC3 precedent),
  and splitting it would only re-run the same modules.

## Implementation Steps

1. **Preconditions.** Run `python .aide/scripts/aide.py status` and confirm
   that items 228–234 are ✅ and Stage 35's boxes stand as the Description
   says. Record `aide check`'s output as a baseline. It is pinned nowhere.
2. **Rig (AC1).** Clone, bootstrap and print the resolution proof. Confirm
   that the VerSe20 symlink root exists, or recreate it (A4).
3. **Named modules (AC2, AC3).** Run AC2 with the variables unset, then AC3
   with both set. Each runs in the foreground, from the clone's venv.
4. **Resolution (AC4, AC5).** Write one scratch script in the scratchpad. It
   reuses `segfacet.datasets.resolve`, `load_descriptor` and
   `bundled_descriptor_path`. The independent walk is `Path.rglob` plus the
   descriptor's own `case_id` pattern. Write no resolver.
5. **Sibling table (AC6).** Read `spine-failure-lab`'s instruction file, then
   `git -C <sibling> show …`. Compare it with `load_rl1_schema()`.
6. **Evaluate replay (AC7, AC8, AC11).** Write the scratch table with
   `csv.writer(..., lineterminator="\n")`, taking the header from
   `load_rl1_schema()`'s field names. Run the CLI, then the in-process
   recomputation, reusing `apply_review_labels`, `read_review_label_table`,
   `evaluate_cohort`, `compute_cohort_metrics` and `bundled_default_config`.
   Then run the `rl2` copy.
7. **Per-case report (AC9, AC10).** Run `segfacet run` on AC7's case 1 and
   read the report.
8. **Mutation (AC12, AC13).** Hash the file, edit it in the clone, run the
   one node, revert, then re-hash the file and re-run the node.
9. **Rebuild (AC14–AC17).** Run the tool with `--jobs` sized to the host,
   outside pytest. Then compare with `assert_matches_committed_artifact`,
   read the summary, and derive the threshold with the tool's
   `derive_max_offset_mm`.
10. **Bookkeeping (AC18).** Run the verbs in ascending criterion order. Append
    one `insights.md` line per divergence the replay finds, and one per
    criterion left unticked.
11. **Environment (AC19).** Run `aide env` and the three profile checks, then
    read the gated table and the specs.
12. **Check.** Re-run `aide check` and record every warning against step 1's
    baseline. A new error is a finding, and `aide merge` refuses on one (§4).
13. **Suite (AC20).** Bring the clone up to the final commit, run the suite,
    record the counts, then delete the clone and every scratch file of this
    item.
14. Record everything in Decisions & Trade-offs.

No change under `src/segfacet/**`, `scripts/**` or `tests/**`, and no new
dependency.

## Authorised paths

**May change:**

None. This item commits only three files, all always authorised:
`docs/aide/progress.md` (through `aide progress accept`, `amend` or
`retract`, or the hand annotation AC18 allows beside an unticked box),
`docs/aide/insights.md` (through `aide insights add`), and this spec's
Decisions record. Its replay writes only in the session scratchpad and in the
clone. AC12's edit is made in the clone and reverted there.

**Asserts against:**

- `src/segfacet/**` — the package the clone runs; read by every replay criterion
- `scripts/rebuild_verse_reference.py` — the development-role rebuild run in the clone (AC14–AC17)
- `tests/**` — the modules AC2, AC3 and AC12 run, and the suite AC20 runs
- `docs/aide/roadmap.md` — Stage 35's five criteria, quoted in the Description and attested by AC18

## Testing Strategy

**No new test module** (A2). The test-writer writes nothing for this item.
Every criterion is a replay whose evidence is the output recorded in
Decisions, which the validator re-executes. If the test-writer is dispatched,
it returns with no commit and says so.

**Discipline.** Nothing this item records is turned into a suite assertion:
- no `aide check` warning count;
- no suite total;
- no `progress.md` text;
- no `insights.md` entry;
- no engine version;
- no real-data count.

The real-data counts are dated measurements in Decisions. Their standing
in-suite checks are item 229's AC5–AC7 and item 234's AC9–AC11, gated on the
data.

**Existing tests to reconcile: none.** A sweep of `tests/` for `Stage 35`,
`stage 35`, `_STAGE_35` and `Item 235` (2026-10-18) found no test that reads
Stage 35's section of `progress.md` or `roadmap.md`. Ticking criteria 1 and 3
therefore breaks no test, and neither do the `amend` lines.
`tests/test_aide_check_no_errors.py` asserts no errors. The hand annotation
beside an unticked box is a shape `aide check` accepts, with item 204 and item
169 as precedent.

## Validation  <!-- OPTIONAL: how to OBSERVE this working, beyond the tests -->

This item **is** the stage validation. The validator re-executes the replay
criteria, not only the suite, and checks each Decisions record against its own
run:

- the rig and the resolution proof (AC1);
- the two module runs, with and without the VerSe variables (AC2, AC3);
- the six role resolutions and the list subset (AC4, AC5);
- the sibling table comparison (AC6);
- the evaluate replay, its refusal and both reports (AC7–AC11);
- the mutation and its revert (AC12, AC13);
- the rebuild comparison, summary and threshold (AC14–AC17);
- each `aide progress` command against the `progress.md` diff (AC18);
- the profiles and the gated table (AC19);
- the full-suite counts from a fresh clone of the final commit (AC20);
- `python .aide/scripts/aide.py scope`.

**The rebuild is the one expensive replay.** It takes about 19 CPU-hours
serial, and the slowest case takes over 90 minutes, so its wall time is
bounded below by that case. The validator re-runs AC14–AC17's comparisons on
the builder's fresh artifact and summary when they still exist in the session
scratchpad. If they do not, it re-runs the rebuild. If it can do neither, it
records AC14–AC17's re-execution as **not performed** and does not count the
builder's record as its own.

**Environment gating.** AC3–AC17 need the real VerSe releases on the host.
`aide.toml` has no `[validation]` profile for them, and none is added
(`aide.toml` is a process file, item 229 A6). The gate is the two environment
variables plus the three-split check the tests already apply. `pyradiomics`,
`docker` and `gpu` are evaluated and recorded only (AC19).

**Honest downgrade.** A replay that cannot run is recorded as **not
performed**, naming what was missing. Its unticked criterion stays unticked
with that reason, and a ticked one keeps its tick with an `amend` saying so
(A9). A skip-clean run is never evidence.

**Do not run `aide gate approve` or `aide gate decline`.**

## Dependencies

- **Item 228**: case-id-list subsets with the missing-id error and the
  selector check (AC2, AC5). Merged ✅.
- **Item 229**: `verse20.yaml` and the role subsets on both descriptors (AC2–AC5,
  AC7). Merged ✅.
- **Item 230**: the per-label, several-modes expectation and `label_metrics`
  (AC2, AC7). Merged ✅.
- **Item 231**: the vendored `rl1` schema, the reader and `evaluate
  --review-labels` (AC2, AC6–AC8). Merged ✅.
- **Item 232**: the `facet_revision` block in both reports (AC2, AC9, AC11).
  Merged ✅.
- **Item 233**: the report schema version and its leaf-path pin (AC2, AC10,
  AC12, AC13). Merged ✅.
- **Item 234**: the development-role rebuild tool and the committed artifact
  (AC3, AC14–AC17). Merged ✅.

**Downstream:** none in this queue; item 235 runs last. Stage 16's deferred
deliverables say they resume when Stage 35 closes, and they also wait on
`gate-9776`.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether the Environment-Gated "Real VerSe GT reference
  distributions" row should gain a trail line recording VerSe20's first
  real-data run (items 229, 234, 235). The row is already `✅ Verified`, and
  items 229 and 234 placed VerSe20 under it without editing it. Whoever writes
  a row writes its trail, and this item writes no row.
- **Left open:** whether `segfacet build-reference` should gain the rebuild
  tool's `--jobs` and multi-descriptor input, so that the CLI itself can build
  the development-role reference. The queue line names the CLI. The tool is
  what produces the committed artifact (A6), and adding to the CLI is a
  feature item, not a validation.
