<!-- aide-template: item 3 -->
# Item 217 — Validate stage 27: Feature Schema Taxonomy & Coordinate System

> **Created:** 2026-10-05 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 27 — Feature Schema Taxonomy & Coordinate System
> **Queue:** [`../queue/queue-029.md`](../queue/queue-029.md) · Item 217
> **Objectives:** G8
> **Suggested branch:** `aide/217-validate-stage-27-feature-schema`

---

## Description

Stage 27's validation item. Items 214–216 each proved their own deliverable
against their own tests. This item asks the stage-level question: does the
merged tree, measured from a clean clone, meet the three criteria in
[`roadmap.md`](../roadmap.md)'s Stage 27 "Validation / acceptance" block? It
records the measured answer in `progress.md` one criterion at a time,
**including where the answer is no.** It fixes nothing it finds.

The three criteria, verbatim:

1. The taxonomy is documented with its rationale and every deviation from the
   starting proposal justified, and is signed off by the maintainer before
   migration (**G8**).
2. Every feature is addressable under it; no identity field is stored more
   than once.
3. The regenerated catalogue and the drift test agree; no rule's behaviour
   changes on the corpus except where a retune is explicitly authorised.

**"From a clean clone" means a fresh `git clone` with its own venv**, the rig
the Stage 29–33 validation items used. CLAUDE.md's Gotchas give the reason: a
second tree reached through `PYTHONPATH` can be silently shadowed by the
working checkout's editable install. Open insight `2026-10-05-ec3b` records
that this venv's `.pth` is a plain path entry, so the shadowing may not occur
on every machine. The clone stays required regardless: it is what "replay from
a clean clone" means. Insight `2026-10-05-dc87` also binds: a tree copied
without `.git` lets git-gated tests skip silently. So the replay runs from a
real clone, and every pytest run it records lists its skips.

**Criterion 3 is a before/after claim, so the replay has two trees.** The
standing invariant behind it is the specificity ratchet
(`tests/test_163_specificity_ratchet.py`), which compares each committed case's
measured firing with its expected set. It cannot see a change that was
re-expected in the same edit. It also runs without a reference, so it never
exercises the reference-backed rules. The replay therefore also measures the
same cases on the **pre-migration commit B** (A6) and compares the two trees.
That comparison is a dated measurement. §1 forbids it as a standing test, since
it bounds a diff against a baseline, and it is recorded in Decisions.

**One retune is explicitly authorised, and it is attested as such, not as
"nothing changed".** The maintainer decided on 2026-10-05 that the two stored
adjacent-pair spacing arrays collapse into one, in anatomical order: *"the
integer-label order is anatomically meaningless"*. The two arrays are
`relationships.neighbour_spacings_mm[]`, in anatomical order over recognised
levels, and `stage3.spacing_consistency.spacings_mm[]`, in integer-label order
over every label. Item 214's note records the collapse under its Deviations
section, and gate-0080 signs it. Item 216 carries it (its D1). Wherever the
two orders disagreed, what is measured changes on purpose: the surviving
array, and the statistics derived from it (`mean_spacing_mm`, `cv_spacing`,
`deviations_mm[]`, `outlier_pairs[]`). If the signed note re-derives them,
the per-element `stage3.per_label_neighbourhood[].stats.spacing_mm.*` values
change too.

**No rule's firing changes on either corpus in this stage** (item 216's D8).
On the committed corpora the orders disagree on exactly one case,
`sequence_break` (A5). There, `fused_label`'s spacing ratios rise, but its
size gate keeps it silent. So the retune's corpus footprint is a **value
change on `sequence_break` only**, and every case's findings stay equal.
The rule-level effect of the collapse is shown on a constructed variant by
item 216's AC5, not on a committed case. The replay measures both the
unchanged findings and the value footprint. It does not assume either.

**Live state on 2026-10-05**, measured at `f5c79df` (`aide/queue-029`, items
214–216 not yet built) with `.venv/bin/python`. These are starting points.
The item re-measures every one in the clone. Where a re-measurement differs,
the measured value wins and Decisions records the difference.

- The catalogue holds 145 leaf paths. Item 214's pre-migration path set
  holds 165 (A1, A9), and its mapping table has one row for each.
- On the `clean_control` case report (item 215's definition, A3), the last
  segment `label` ends 6 leaf paths and `level_name` ends 5.
- The same report has 158 leaf paths in catalogue notation. Twenty of them
  are not catalogue paths. All 20 are
  `reference_delta.{label}.features.<name>.<stat>`, for `extent_x_mm`,
  `extent_y_mm`, `extent_z_mm` and `spline_offset_mm`, five statistics each.
  They are the report-only rows of item 214's table (A9).
- The two corpora hold 14 geometric and 4 intensity cases (A8).
- On `sequence_break`:
  - `relationships.neighbour_spacings_mm` = `[134.1605, 33.4940, 32.6952, 33.8724]`;
  - `stage3.spacing_consistency.spacings_mm` = `[33.4940, 32.6952, 33.8724, 36.8400]`,
    with mean 34.2254, cv 0.0458 and `outlier_pairs` `[]`;
  - derived from the anatomical-order array instead (item 216, A5): mean ≈
    58.556, cv ≈ 0.746, deviations ≈ [75.605, −25.062, −25.860, −24.683] and
    `outlier_pairs` `[["T13", "L1"]]`;
  - its findings are `mislabel/ordering` on {20, 28} and `sequence/shift` on
    {28}. Neither reason renders a spacing value.

*Corrected at claim (2026-10-06, base `aide/queue-029` at `8a5ebed`: items
214–216 merged, gate-0080 ✅ Approved).* Item 216 was amended at its own claim
and built differently from what this Description assumed in four ways. The
three paragraphs above stand as the record of what this spec was written
against. Where they disagree with this correction, the correction holds.

- **The authorised retune is wider than the spacing collapse.** At gate-0080
  the maintainer also signed one anatomical element order for the whole
  record, stored as `case.sequence.order[]` (the note's "Element order" and
  Deviation 11; item 216's D11). Item 216 attests it as the same explicitly
  authorised exception as D1. So wherever the integer and anatomical orders
  disagree, every Stage 3 value changes, not only the spacing family. On the
  corpora that is still `sequence_break` alone. There, 37 table rows resolve
  differently, and the spacing family's four statistics are 4 of them (A4's
  and A5's re-checks).
- **Findings without a reference do not move.** Measured at claim: every one
  of the 18 cases gives the same `Finding.to_dict()` list on B and on the tip,
  reasons included (A10's re-check).
- **The reference-backed report on `sequence_break` does move.** With the
  bundled real-VerSe19 reference, its `reference_delta` findings change. The
  distribution distances of labels 20–23 move, and the `spline_offset_mm`
  out-of-range finding passes from label 21 to label 20. That reference was
  built from integer-order fits, so it is stale for exactly this T13 shape
  (insight `2026-10-06-f318`). So AC16 is predicted not to hold on
  `sequence_break`. Whether the authorisation covers this is the maintainer's
  to rule, not this item's (AC16's correction, and the new **Left open**).
- **The record has one stored path with no table row,
  `case.sequence.order[]`,** and the report's top-level `image_features` key
  is gone (item 216's A14 and AC1 correction). AC10 and AC11 are corrected to
  count that path.

**Live state on 2026-10-06**, re-measured at claim on `8a5ebed` with
`.venv/bin/python`. B was measured from a `git worktree` on `PYTHONPATH`, with
`segfacet.__file__` printed under it (insight `2026-10-05-ec3b`'s shortcut).
That shortcut is not the replay's rig. These are starting points, and the
clone re-measures each one:

- The catalogue holds 154 paths. The table has 165 rows: 80 `kept`, 73
  `moved` and 12 `merged`, with 130 Moved by 215 and 35 by 216. The
  `kept`/`moved` new paths number 153, and the catalogue holds those 153 plus
  `case.sequence.order[]`.
- The `clean_control` case report has 149 leaf paths. 148 of them are table
  new paths, and the one that is not is `case.sequence.order[]`. The last
  segment `label` ends exactly one path, `per_label.{label}.label`, and
  `level_name` ends exactly one, `per_label.{label}.level_name`. All 20
  report-only rows' new paths are among the 149.
- On `sequence_break` the spacing family is, on B:
  `[33.4940, 32.6952, 33.8724, 36.8400]`, mean 34.2254, cv 0.0458, deviations
  `[-0.7314, -1.5302, -0.3530, 2.6146]` and `outlier_pairs` `[]`. On the tip it
  is `[134.1605, 33.4940, 32.6952, 33.8724]`, mean 58.5555, cv 0.7455,
  deviations `[75.6050, -25.0615, -25.8603, -24.6831]` and `outlier_pairs`
  `[["T13", "L1"]]`.
- `segfacet_report.txt` is byte-identical across B and the tip for
  `clean_control` (462 lines) and `displace` (378 lines). It differs for
  `sequence_break` (379 lines in both).

**In scope:**

- the clean-clone replay, the base-tree comparison, and their recorded
  measurements;
- Stage 27's acceptance bookkeeping in `progress.md` through `aide progress
  accept`, plus the hand-written annotation §1 allows beside a box left
  unticked;
- one-line `insights.md` findings, through `aide insights add`.

**Not in scope:**

- Fixing anything the replay finds. Each divergence becomes a finding.
- Any change under `src/segfacet/`, to a test, to a generated artifact, to a
  corpus case or to the design note.
- Ticking, rewording or archiving any `insights.md` entry. Open insights
  `2026-10-02-3eba`, `2026-09-30-88a5` and `2026-09-22-c151` are design inputs
  the note answers and this queue does not close. The attestation prose may
  say where the note answered each.
- Editing the Environment-Gated Capability Verification table (AC17 confirms
  it needs no row).

## Acceptance Criteria

Every criterion is a **replay** criterion. The builder executes it, and the
validator re-executes it. Its observed output is recorded verbatim in
Decisions & Trade-offs, and it adds no test (Testing Strategy).

Terms used below:

- **The clone** is AC1's clone, and **the base tree** is AC2's.
- **Passes in the clone** means this: the named modules or node ids, run from
  the clone's own venv in the foreground, exit `0`, and the run's skip list
  is recorded and empty.
- **The table** is the list `tests/feature_taxonomy_mapping.py::read_mapping()`
  returns, run in the clone (A1).
- **The catalogue's path set** is the `path` of every entry under
  `groups[*].entries[*]` in the clone's `docs/aide/feature_catalogue.generated.json`.
- **The case report**, its **leaf paths** and a path's **last segment** are
  as item 215's spec defines them (A3), built in the clone.
- **The survivor** and **`new(p)`** are item 216's terms (A4): the new path
  both spacing rows share, and the new path of the row whose old path is `p`.
  **Resolving** a catalogue-notation path in a record is item 216's
  definition too.
- **The spacing family** of a record is five values: the survivor, and
  `new(p)` resolved for each `p` in
  `stage3.spacing_consistency.{mean_spacing_mm, cv_spacing, deviations_mm[],
  outlier_pairs[]}`. In the base tree, `new(p)` is `p` itself, and the
  array is `stage3.spacing_consistency.spacings_mm[]`.
- **A touched case** is one where, in the base tree, the record from
  `extract_feature_record(seg, bundled_default_config())` holds two arrays
  that differ in length or in any element:
  `["relationships"]["neighbour_spacings_mm"]` and
  `["stage3"]["spacing_consistency"]["spacings_mm"]`.

A criterion annotated *(closes Stage 27 criterion M)* is evidence for that
criterion. A criterion with no annotation closes none.

### The rig

- [ ] **AC1: the replay runs in a fresh clone whose code is the clone's own.**
  Clone the claim branch into the session scratchpad with `git clone <working
  checkout> <scratch>/clone217`. Bootstrap the clone's venv with `python
  <scratch>/clone217/.aide/scripts/aide.py --repo <scratch>/clone217 env
  --bootstrap`. Record three things:
  - the clone path;
  - the clone's `HEAD` SHA, which equals the claim branch's tip at clone time.
    This SHA is **the clone commit** every attestation cites;
  - `segfacet.__file__`, as printed by `<clone>/.venv/bin/python -P`, which
    resolves under the clone.

  A resolution outside the clone invalidates every clone result below.
  *Correction at claim (2026-10-06):* the wording stands. Also record the
  clone venv's `sys.version`. Insight `2026-10-06-934c` records that path
  positions can differ in the last bit on Python 3.12 and later, so every
  byte comparison below holds for the interpreter it ran on. CI's single leg
  is 3.11, and the working venv was 3.11.15 at claim.
- [ ] **AC2: the base tree holds commit B, and its code is its own.**
  Find B as A6 defines it. Create the base tree with `git worktree add
  --detach <scratch>/base217 <B>`, run from the working checkout. Bootstrap
  its venv with its own `aide env --bootstrap` (`--repo <scratch>/base217`).
  Record B's SHA, and `segfacet.__file__` from `<scratch>/base217/.venv/bin/python -P`,
  which resolves under the base tree.

### Every generated artifact regenerates

- [ ] **AC3: each committed text or fixture artifact equals a fresh
  regeneration in the clone, byte for byte.** From the clone's venv with
  `-P`, regenerate each artifact into a scratch directory. Compare each output
  with the clone's committed file using `read_bytes()`. Every comparison must
  be equal.
  - `docs/aide/feature_catalogue.generated.json` and `.md`:
    `-m segfacet.catalogue --json <tmp>/fc.json --md <tmp>/fc.md`
  - `docs/aide/failure_modes.generated.json` and `.md`:
    `-m segfacet.failure_modes --json <tmp>/fm.json --md <tmp>/fm.md`
  - `docs/aide/traceability_matrix.generated.json` and `.md`:
    `-m segfacet.traceability --json <tmp>/tm.json --md <tmp>/tm.md`
  - `docs/aide/golden_evidence.generated.json`:
    `-m segfacet.golden_evidence --out <tmp>/ge.json`
  - `docs/aide/rules.generated.md`: `-m segfacet.rule_table --md <tmp>/rules.md`
  - `tests/golden/report_format_contract.json`:
    `tests.report_format_fixture.format_contract_text().encode("utf-8")`.
    It is computed by a scratch script that puts the clone root first on
    `sys.path`. The module's `__main__` writes only to the committed path,
    and has no output argument.
  - `tests/corpus/manifest.json` and every file it names:
    `-m segfacet.synth.corpus --out <tmp>/corpus`
  - `tests/corpus/intensity/manifest.json` and every file it names:
    `-m segfacet.synth.intensity --out <tmp>/intensity`
  - `tests/corpus/119_pre_119_digests.json`'s `catalogue_leaf_path_set_sha256`
    value, which item 216 rewrites: it equals the SHA-256 of
    `"\n".join(sorted(<regenerated catalogue's path set>))` encoded UTF-8,
    computed exactly as `tests/test_119_curve_formulation.py` does. This is a
    value comparison, because the file's other keys are historical digests
    that no generator writes.

  Record each artifact with its result. A mismatch is recorded with its diff
  and is not repaired here.
- [ ] **AC4: the bundled synthetic reference equals a fresh regeneration
  under the committed-artifact comparator.** In the clone, run
  `-m segfacet.reference.artifact --out <tmp>/ref.json`. Then
  `segfacet.synth.golden.assert_matches_committed_artifact(json.loads(<tmp>/ref.json),
  <clone>/src/segfacet/reference/reference_default.json)` returns without
  raising (A7).
- [ ] **AC5: the corpus sheet is current by its input digest.**
  `tests/test_178_corpus_sheet.py::test_ac7_committed_sheet_is_current`
  passes in the clone (A7).

### Stage 27 criterion 1: the design, signed before migration

- [ ] **AC6: the sign-off gate reads approved.** In the clone, `python
  <clone>/.aide/scripts/aide.py --repo <clone> gate list` prints exactly one
  gate whose text contains `Stage 27 feature-record taxonomy sign-off`. Its
  ID is gate-0080 (A2), and its status is `✅` with an approval date. Record
  the ID, the date and the Decision / evidence cell as `progress.md` holds it.
  *(closes Stage 27 criterion 1)*
  *Correction at claim (2026-10-06):* the wording stands, and the date has a
  named source. `gate list` (engine 2.39.0) prints `✅ gate-0080 …` with no
  date. So the approval date is read from the row's Status cell in the
  clone's `progress.md`, which reads `✅ Approved (2026-10-06)` at claim (A2's
  re-check).
- [ ] **AC7: the approval precedes the migration.** The approval date from
  AC6 is on or before the committer date, read as an ISO date, of the
  `aide/queue-029` commit whose subject is `progress(aide): item 215 ->
  in-progress`. Record both dates.
  *(closes Stage 27 criterion 1)*
  *Correction at claim (2026-10-06):* the date comparison stands, and one
  ordering check is added. Both dates are 2026-10-06, and a date cannot order
  two events on one day. Also, that `in-progress` commit (`54b1553`, 16:08:58)
  landed after item 215's first code commit (`c09b07d`, 16:08:55), so it is
  not a lower bound on the migration. So AC7 also checks the following, in
  the working checkout:
  - the commit whose subject is exactly `docs: human gate-0080 approved`;
  - the earliest `aide/queue-029` commit whose subject starts `feat(215)`;
  - that `git merge-base --is-ancestor <gate commit> <feat commit>` exits
    `0`.

  Each `git log --grep` must print exactly one SHA. Record both SHAs, their
  committer timestamps and the exit code. Measured at claim: `00fe6f5`
  (15:19:25) is an ancestor of `c09b07d` (16:08:55), with exit code `0`.

### The stage's own item checks

- [ ] **AC8: the three migration-stage modules pass in the clone.**
  `tests/test_214_feature_taxonomy_design.py`,
  `tests/test_215_per_label_migration.py` and
  `tests/test_216_neighbour_pair_and_case_level_migration.py` pass in the
  clone. `test_214` passes unchanged. Its AC1 compares the table's old paths
  with a frozen pre-migration literal, so it stays true after both
  migrations (A1). Record the node count of each.

### Stage 27 criterion 2: addressable, and identity stored once

- [ ] **AC9: each identity key ends exactly one leaf path of a pipeline
  record.** On the case report built in the clone, for each `k` in
  (`label`, `level_name`), exactly one leaf path has last segment `k`. Record
  both counts as numbers, and the one path each.
  *(closes Stage 27 criterion 2)*
- [ ] **AC10: the catalogue's path set equals the table's stored new paths.**
  The catalogue's path set equals the set of new paths of all the table's
  rows (both owners, all 165 rows) whose change is `kept` or `moved`. Record
  the size of each set, and the count of `kept`, `moved` and `merged` rows.
  *(closes Stage 27 criterion 2)*
  *Corrected at claim (2026-10-06):* the set the catalogue is compared with
  is those new paths **plus `case.sequence.order[]`**. That is the one stored
  path with no table row: the signed note's Deviation 11, carried by item
  216's AC1 correction. As written, AC10 would fail on that path alone.
  Record it as the one addition. Measured at claim: 153 new paths plus 1
  gives 154, equal to the catalogue's 154 (80 `kept`, 73 `moved`, 12
  `merged`).
  *Settled (2026-10-06; source: maintainer ruling, 2026-10-06, in the
  item-217 claim session):* the maintainer confirmed that
  `case.sequence.order[]` is counted, here and in AC11.
- [ ] **AC11: every leaf of a real pipeline record is a stored new path in
  the table.** The case report's leaf paths minus the set of new paths of the
  table's `kept`/`moved` rows is empty. The case report is AC9's
  `clean_control` run with the bundled reference, so its reference-delta
  block carries every tracked feature.

  Before that comparison, two recognisability facts are asserted:
  - the case report's leaf paths are non-empty;
  - they include the new path of every one of the 20 report-only rows (the
    table's rows whose old path starts `reference_delta.{label}.features.`
    and names a feature other than `physical_volume_mm3`). So a run that lost
    the reference block, or scored fewer features, fails rather than passing
    with less to check.

  Record the case report's leaf-path count, how many lie among the table's
  new paths, and the difference set, which must be empty. This is direct
  evidence on a real record, not inferred from the catalogue (A9).
  *(closes Stage 27 criterion 2)*
  *Corrected at claim (2026-10-06):* the leaf paths are compared with the
  `kept`/`moved` new paths **plus `case.sequence.order[]`** (AC10's
  correction), and the difference must still be empty. The recognisability
  facts stand. Measured at claim: 149 leaf paths, 148 among the new paths,
  and a difference of exactly `{case.sequence.order[]}` against the table
  alone. That difference is empty once the path is added.

### Stage 27 criterion 3: catalogue, drift test, and rule behaviour

- [ ] **AC12: the drift test agrees with the committed catalogue.**
  `tests/test_104_feature_catalogue_drift.py` passes in the clone. Record its
  node count.
  *(closes Stage 27 criterion 3)*
- [ ] **AC13: every committed case's measured firing equals its expected set,
  across both corpora.** `tests/test_163_specificity_ratchet.py` passes in
  the clone, in full. Read `segfacet.traceability.build_matrix().conformance`
  in the clone, and record two things:
  - the case ids driven, split by corpus. This set equals the union of both
    committed manifests' `case_id` values;
  - the count of cases whose `agrees` is `False`, which must be `0`.

  *(closes Stage 27 criterion 3)*
- [ ] **AC14: every case's findings are unchanged across both corpora,
  touched cases included.** Run the same scratch script in the base tree and
  in the clone, each with its own venv and `-P`. It serialises each case's
  findings in order with `Finding.to_dict()`, which includes the `reason`
  string:
  - for every geometric case, through
    `segfacet.synth.regression.pipeline_findings(case)`;
  - for every intensity case, through
    `segfacet.synth.regression.intensity_pipeline_findings(case)`.

  For every case id in both trees' manifests, the clone's list equals the
  base tree's list exactly. No case and no rule is exempt (item 216, D8).
  Before the comparison, the script asserts that the two trees' case-id sets
  are equal and non-empty. Record the case count compared, and each case's
  finding count in each tree.

  A touched case gets no special treatment, because no finding reason
  renders a spacing statistic (A5). If the tip's reasons for a touched case
  differ only in a rendered spacing value, AC14 does not hold. The
  difference is recorded verbatim and criterion 3 stays unticked: whether
  the 2026-10-05 decision covers a rendered reason is the maintainer's to
  rule, not this item's.
  *(closes Stage 27 criterion 3)*
- [ ] **AC15: the authorised retune changes measured values exactly on the
  touched cases.** In each tree, read every case's spacing family from
  `extract_feature_record(seg, bundled_default_config())`. Use
  `loaded_seg_image(case)` for a geometric case, and the seg half of
  `loaded_intensity_case(case)` for an intensity case. The set of cases
  whose spacing family differs between the trees equals the set of touched
  cases. Values are compared to `abs=1e-9`, and lists elementwise with equal
  length. Record:
  - the touched case ids, which on 2026-10-05 is `sequence_break` alone (A5);
  - for each touched case, the base tree's and the clone's five values in
    full. This is the authorised retune's measured footprint on the corpora.

  *(closes Stage 27 criterion 3)*
  *Corrected at claim (2026-10-06):* the spacing-family equality stands. It
  is now the retune's spacing part, not its whole footprint, because item
  216's D11 widened the authorised change to every Stage 3 value wherever the
  two orders disagree (A4's re-check). The whole footprint gets one more
  measured equality, read from the same two records per case:
  - **What is compared.** Every table row whose change is `kept` or `moved`,
    except the row whose old path is `features_version`. Item 215 bumped that
    value on every Stage-3 record, from `"0.2"` to `"0.3"`, by the batch rule
    (A3's re-check).
  - **How.** Resolve the row's old path in the base tree's record and its new
    path in the clone's. A row is skipped for a case when any value it
    resolves to, in either tree, is a mapping. Such a value is a container
    (`relationships`, `per_label`) whose shape the migration changed by
    design.
  - **The equality.** The set of cases where any compared row resolves
    differently equals the set of touched cases. Values are compared to
    `abs=1e-9`, and lists elementwise with equal length.
  - **What is recorded.** For each touched case, the old paths of the rows
    that differ. On a touched case a row can differ by element order alone,
    because per-label values resolve in `per_label` key order. At claim
    `stage3.monotonic_consistency.u_values[]` was the one such row, with the
    same value per label.

  Measured at claim: the case set is `{sequence_break}`, with 37 differing
  rows (A5's re-check). This record is what AC18's criterion-3 text cites as
  the retune's footprint.
- [ ] **AC16: the reference-backed human report does not move.** For `<case>`
  in `clean_control`, `displace` and `sequence_break`, run
  `<tree>/.venv/bin/segfacet run --scan
  <tree>/tests/corpus/fixtures/base_scan.nii.gz --seg
  <tree>/tests/corpus/fixtures/<case>_seg.nii.gz --intensity --out <scratch>/<tree>-<case>`
  once in the base tree and once in the clone. No reference flag is passed,
  so the bundled real-VerSe19 reference applies (CLAUDE.md "Gotchas"). Each
  case's `segfacet_report.txt` is byte-identical across the two trees. This
  replays item 215's Validation step 4 (`clean_control`, `displace`) and item
  216's Validation step 5 (`clean_control`, `sequence_break`) together (A3,
  A4). Record each file's line count and finding count.
  *(closes Stage 27 criterion 3)*
  *Correction at claim (2026-10-06):* the wording stands, and so does its
  byte-identical bar for all three cases. **It is predicted not to hold on
  `sequence_break`.** Item 216's corrected Validation step 5 measured this,
  and it was re-measured at claim from B and the tip:
  - **The distribution distances move.** Labels 20–23 go from 3.70, 3.90,
    4.07 and 3.96 to 3.47, 3.89, 4.06 and 4.40.
  - **One out-of-range finding changes label.** The `reference_delta`
    finding on `spline_offset_mm` is on label 21 (value 0.1513) in B, and on
    label 20 (value 0.0038) on the tip.
  - **Unchanged.** `clean_control` and `displace` are byte-identical.

  The cause is the record-wide anatomical order (item 216's D11), read
  against a reference built from integer-order fits (insight
  `2026-10-06-f318`).

  This spec does not widen AC16 to item 216's bounded comparison. That
  comparison asked only that the `(rule_id, labels)` set stay the same, and
  that reasons differ only within a measured list. The maintainer authorised
  measured values to change (D1, D11) and decided that no corpus firing
  changes (A10). Neither decision says whether a reference-backed finding on
  a corpus case may change. That is the maintainer's to rule (**Left
  open**), so on this outcome criterion 3 stays unticked under AC18.

  For `sequence_break`, the replay still records:
  - the verbatim diff of the two `.txt` files;
  - both trees' `(rule_id, sorted labels)` finding lists, read from each
    `segfacet_report.json`;
  - whether every differing line renders a `reference_delta` finding (its
    reason, or its `Labels:` line) on a label in {20, 21, 22, 23}.

  Those records inform the ruling and close nothing. A ruling made before the
  replay is recorded here by spec-author as a further dated correction.
  *Corrected after the maintainer's ruling (2026-10-06; source: maintainer
  ruling, 2026-10-06, in the item-217 claim session).* **The ruling.** The
  reference-backed change on `sequence_break` is covered by the gate-0080
  sign-off, within the authorised retune: item 216's D1, widened by its D11.
  The **Left open** on this question is settled. AC16's bar is now exactly
  this, and it replaces the byte-identical bar for `sequence_break` only:
  - **`clean_control` and `displace`.** Each `segfacet_report.txt` is
    byte-identical across the two trees, as before.
  - **`sequence_break`: what may differ.** Compute the line diff of the two
    trees' `segfacet_report.txt` with `difflib.ndiff` over `splitlines()`,
    keeping the lines prefixed `- ` (base tree only) and `+ ` (clone only),
    each with its two-character prefix removed. The base-only list must
    equal the 11 lines of the **base only** block below, and the
    clone-only list must equal the 11 lines of the **clone only**
    block, each in order and compared exactly. Read each block line with
    its first two spaces removed, which are the block's own indent. Every
    remaining leading space is part of the line.
  - **`sequence_break`: everything else.** No other line differs. Any
    difference beyond the listed lines, or a listed line that does not
    differ, fails AC16.
  - **Recorded, not asserted.** Both trees' `(rule_id, sorted labels)`
    finding lists, read from each `segfacet_report.json`.

  The listed lines are the diff measured at claim, from B and the tip, on
  `.venv/bin/python` 3.11.15. Each change appears once in the verdict's
  reasons and once in the findings section, where a finding also carries its
  `Labels:` line. There are three kinds of change:
  - the four distribution distances for labels 20–23, which go 3.70 → 3.47,
    3.90 → 3.89, 4.07 → 4.06 and 3.96 → 4.40;
  - the `spline_offset_mm` out-of-range finding, which leaves label 21
    (value 0.1513);
  - the same finding, which appears on label 20 (value 0.0038).

  Base only (11 lines):

  ```
      [flagged-for-review] Reference distribution-distance outlier: label 20 (L1) distribution distance 3.70 exceeds threshold 3.00.
      [flagged-for-review] Reference distribution-distance outlier: label 21 (L2) distribution distance 3.90 exceeds threshold 3.00.
      [flagged-for-review] Reference out-of-range: label 21 (L2) feature 'spline_offset_mm' value 0.15134108416356312 falls outside the reference range (percentile_rank=0.3493569870181564, band=(1, 99)).
      [flagged-for-review] Reference distribution-distance outlier: label 22 (L3) distribution distance 4.07 exceeds threshold 3.00.
      [flagged-for-review] Reference distribution-distance outlier: label 23 (L4) distribution distance 3.96 exceeds threshold 3.00.
    [flagged-for-review] (reference_delta) Reference distribution-distance outlier: label 20 (L1) distribution distance 3.70 exceeds threshold 3.00.
    [flagged-for-review] (reference_delta) Reference distribution-distance outlier: label 21 (L2) distribution distance 3.90 exceeds threshold 3.00.
    [flagged-for-review] (reference_delta) Reference out-of-range: label 21 (L2) feature 'spline_offset_mm' value 0.15134108416356312 falls outside the reference range (percentile_rank=0.3493569870181564, band=(1, 99)).
      Labels: 21
    [flagged-for-review] (reference_delta) Reference distribution-distance outlier: label 22 (L3) distribution distance 4.07 exceeds threshold 3.00.
    [flagged-for-review] (reference_delta) Reference distribution-distance outlier: label 23 (L4) distribution distance 3.96 exceeds threshold 3.00.
  ```

  Clone only (11 lines):

  ```
      [flagged-for-review] Reference distribution-distance outlier: label 20 (L1) distribution distance 3.47 exceeds threshold 3.00.
      [flagged-for-review] Reference out-of-range: label 20 (L1) feature 'spline_offset_mm' value 0.0037851190125903753 falls outside the reference range (percentile_rank=0.0, band=(1, 99)).
      [flagged-for-review] Reference distribution-distance outlier: label 21 (L2) distribution distance 3.89 exceeds threshold 3.00.
      [flagged-for-review] Reference distribution-distance outlier: label 22 (L3) distribution distance 4.06 exceeds threshold 3.00.
      [flagged-for-review] Reference distribution-distance outlier: label 23 (L4) distribution distance 4.40 exceeds threshold 3.00.
    [flagged-for-review] (reference_delta) Reference distribution-distance outlier: label 20 (L1) distribution distance 3.47 exceeds threshold 3.00.
    [flagged-for-review] (reference_delta) Reference out-of-range: label 20 (L1) feature 'spline_offset_mm' value 0.0037851190125903753 falls outside the reference range (percentile_rank=0.0, band=(1, 99)).
      Labels: 20
    [flagged-for-review] (reference_delta) Reference distribution-distance outlier: label 21 (L2) distribution distance 3.89 exceeds threshold 3.00.
    [flagged-for-review] (reference_delta) Reference distribution-distance outlier: label 22 (L3) distribution distance 4.06 exceeds threshold 3.00.
    [flagged-for-review] (reference_delta) Reference distribution-distance outlier: label 23 (L4) distribution distance 4.40 exceeds threshold 3.00.
  ```

### Environment, bookkeeping, suite

- [ ] **AC17: Stage 27 introduces no environment-gated capability, and the
  table is left unchanged.** Record two facts:
  - no row of `progress.md`'s Environment-Gated Capability Verification table
    names Stage 27, or any of the item numbers in Stage 27's deliverable
    bullets, in its "Introduced by" cell;
  - no spec of those items carries a `## Environment / Hardware Dependencies`
    section.

  Record the output and exit code of `python .aide/scripts/aide.py env`, and
  of `env --profile pyradiomics`, `--profile docker` and `--profile gpu`. The
  table is not edited.
- [ ] **AC18: each criterion is attested through `aide progress accept`, and
  no box is ticked on evidence that failed.** For each criterion N in 1, 2
  and 3, in ascending order, run `python .aide/scripts/aide.py progress accept
  27 --criterion N --evidence "…"`. Each evidence text:
  - names the clone commit (AC1) and, for criterion 3, B (AC2);
  - names the ACs behind the criterion: AC6 and AC7 for 1, AC9–AC11 for 2,
    AC12–AC16 for 3;
  - names the checks or measurements those ACs ran, with their measured
    values.

  What each criterion's text must also state:
  - **Criterion 1:** the gate ID, its approval date and the date of the
    migration's first claim.
  - **Criterion 2:** both identity counts (AC9) and both set sizes (AC10).
    It also gives the case report's leaf-path count and the size of its
    difference from the table's stored new paths, which is 0 (AC11). It
    states that "every feature" was read as every leaf of a real
    bundled-reference report, the 20 report-only reference-delta paths
    included (maintainer decision, 2026-10-05; A9). It lists the case
    report's neighbour-pair identity leaf paths as a measurement, and says
    they are not counted (A11).
  - **Criterion 3:** that a retune was explicitly authorised: the
    maintainer's 2026-10-05 decision to collapse the two adjacent-pair spacing
    arrays into one in anatomical order, signed in the note's Deviations
    section at gate-0080, and carried by item 216 (its D1). It states that no
    case's findings changed on either corpus (AC14). It names the touched
    cases, and gives each one's spacing family in both trees (AC15) as the
    retune's measured footprint.

  When a criterion's ACs do not all hold, its box stays unticked. Instead:
  - append a hand-written ` *(not attested YYYY-MM-DD, item 217: <measured
    reason>)*` to the end of its last line;
  - capture one `gap` line with `aide insights add`, naming the stage, the
    criterion and the reason.

  *Corrected at claim (2026-10-06):* the verbs, the order and the
  unticked-box rule stand. What each evidence text must state changes as
  follows.
  - **Criterion 1** also names the gate-approval commit, the first
    `feat(215)` commit, and the ancestry exit code (AC7's correction).
  - **Criterion 2** gives AC10's sizes as the table's `kept`/`moved` new
    paths plus `case.sequence.order[]`, against the catalogue (154 at claim).
    It says that `case.sequence.order[]` is the one stored path with no row,
    by the signed note's Deviation 11. The A11 measurement adds one list
    beside the pair-identity paths: the leaf paths that store label
    references rather than an entity's own identity. At claim these were
    `case.sequence.order[]`,
    `per_label.{label}.components.component_contacts[].neighbour_label` and
    `per_label.{label}.neighbourhood.window_labels[]`. They are listed, not
    counted (A11's re-check).
  - **Criterion 3** describes the authorised retune as item 216's D1 widened
    by its D11. D11 is the record-wide anatomical element order the
    maintainer signed at gate-0080 on 2026-10-06 ("one anatomical element
    order stored as case.sequence.order[]"). The text names AC15's corrected
    footprint record: the touched cases, each one's spacing family in both
    trees, and its differing rows. It states AC16's outcome per case. If
    `sequence_break` differs and the maintainer has not ruled (AC16's
    correction), criterion 3 is not attested. The annotation's reason names
    the reference-backed `reference_delta` change on `sequence_break` and
    insight `2026-10-06-f318`.

  *Corrected after the maintainer's ruling (2026-10-06; source: maintainer
  ruling, 2026-10-06, in the item-217 claim session).* The criterion-3 text
  now states four things:
  - **The ruling.** The maintainer ruled that the reference-backed change on
    `sequence_break` is covered by the gate-0080 sign-off, within D1 widened
    by D11.
  - **AC16's outcome against the corrected bar.** `clean_control` and
    `displace` are byte-identical. `sequence_break` differs in exactly the
    listed 11 base-only and 11 clone-only lines: the `spline_offset_mm`
    out-of-range finding moves from label 21 to label 20, and the distances
    go 3.70/3.90/4.07/3.96 → 3.47/3.89/4.06/4.40.
  - **Both trees' recorded `(rule_id, labels)` lists for `sequence_break`.**
  - **Insight `2026-10-06-f318`,** as the reason the bundled reference sits
    out of step with the new order until it is rebuilt.

  The criterion is unattested only if an AC fails, AC16's corrected bar
  included. The earlier "maintainer has not ruled" branch no longer applies.
  - **Criterion 2.** Counting `case.sequence.order[]` (AC10, AC11) is now
    the maintainer's settled reading (maintainer ruling, 2026-10-06, in the
    item-217 claim session). The text says so.
- [ ] **AC19: the full configured suite is green in a fresh clone of the final
  commit.** Once every commit of this item has landed, take these steps:
  1. Bring AC1's clone up to the branch tip with `python
     <clone>/.aide/scripts/aide.py --repo <clone> sync --item 217`.
  2. Re-print AC1's resolution proof.
  3. Run the configured suite from the clone's venv in the foreground with
     `-n auto`. Both `testpaths` (`tests` and `.aide/scripts/tests`) must be
     covered.

  Record the pass, skip and fail counts, the commit, and the reason for each
  skip. The run has no failures. A skip is never recorded as verification.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

The orchestrator ran clarify as interactive, without access to the human.
Three questions went back on 2026-10-05, and the maintainer settled them the
same day after the cross-spec review: A9 and A11 record the answers, and A10
records the firing decision. A1–A4 pin items 214–216, which are unbuilt, at
the level this item reads them. They are re-checked at claim
(Implementation Steps, step 0). Everything measured was measured on
2026-10-05 at `f5c79df` (`aide/queue-029`).

- **A1 (pin, item 214): the table is read through item 214's reader only.**
  `tests/feature_taxonomy_mapping.py` exposes `read_mapping(text=None)`.
  It returns `(old, new, change, moved_by)` tuples, with `change` in
  {`kept`, `moved`, `merged`} and `moved_by` in {215, 216}. New paths use the
  catalogue's notation.
  - **Rows.** The table has 165 rows: the catalogue's 145 pre-migration
    paths, plus 20 report-only `reference_delta.{label}.features.<f>.<s>`
    paths. Each report-only old path names its feature literally. Item 215
    owns the 20 rows (A9).
  - **The spacing rows.** The rows whose old paths are
    `relationships.neighbour_spacings_mm[]` and
    `stage3.spacing_consistency.spacings_mm[]` share one new path, and one of
    the two is `merged` (item 214, AC8).
  - **The design test.** `tests/test_214_feature_taxonomy_design.py` is not
    retired by either migration item. Its AC1 compares the table's old paths
    with the frozen literal `(165, <SHA-256 of the sorted pre-migration
    set>)`, so it stays true through the stage, and item 214 lists nothing
    under Asserts against. AC8 runs it unchanged.
  - *Re-checked at claim (2026-10-06, base `8a5ebed`): agrees.* The module
    exposes `NOTE_PATH`, `read_mapping(text=None)` and `answer_lines`, and
    this item uses only `read_mapping`. Measured:
    - **Rows.** 165 rows: 80 `kept`, 73 `moved`, 12 `merged`. By owner, 130
      are Moved by 215 (item 215's A2 re-check: its 126 plus the four
      Deviation-5 rows) and 35 by 216. The 20 report-only rows are item
      215's.
    - **The spacing rows.** Both map to `pairs.adjacent.spacings_mm[]`.
      `relationships.neighbour_spacings_mm[]` is `moved` and
      `stage3.spacing_consistency.spacings_mm[]` is `merged`.
    - **The design test.** `git diff 3be6c38 aide/queue-029` is empty for
      both `tests/test_214_feature_taxonomy_design.py` and the reader module.
      Neither migration item edited them. The note itself changed after B,
      at `2364df4` (the maintainer's review decisions). The frozen literal
      pins old paths only, so the change does not reach it.

    One stored path has no row: `case.sequence.order[]` (A4's re-check). That
    is why AC10 and AC11 are corrected.
- **A2 (pin, item 214; engine 2.35.0, re-checked 2.39.0): the sign-off gate.** It is gate-0080,
  the `progress.md` `## Human gates` row whose Gate cell contains `Stage 27
  feature-record taxonomy sign-off`. It reads `⏳ Awaiting` on 2026-10-05, and
  its reach is `Blocks: 215, 216, 217`. A person resolves it with `aide gate
  approve`, which writes `✅ Approved (YYYY-MM-DD)` into its Status cell.
  `aide claim` holds this item until then, so a claim implies the approval. AC6
  still records it from live state. Rewording the Gate cell would change the
  ID, so AC6 also selects the row by its substring.
  - *Re-checked at claim (2026-10-06, base `8a5ebed`, engine 2.39.0):
    corrected on two reads, agrees on the rest.*
    - **Agrees.** The row's Status cell reads `✅ Approved (2026-10-06)`, its
      reach is `215, 216, 217`, and it is the only gate whose text contains
      the substring. Its Decision / evidence cell reads "Signed 2026-10-06
      after review: one anatomical element order stored as
      case.sequence.order[]; per-label values stored per label whatever
      computed them; intensity enters the persisted record (Option A). Scope
      axis unchanged, items 215/216 not re-cut. docs/feature-taxonomy.md @
      2364df4."
    - **Corrected: where the date comes from.** `aide gate list` prints
      `✅ gate-0080 …` and no date, so AC6 reads the date from the
      `progress.md` Status cell (AC6's correction).
    - **Corrected: what the dates can order.** The approval commit,
      `docs: human gate-0080 approved`, is `00fe6f5`, committed at
      2026-10-06T15:19:25+01:00. Item 215's `in-progress` commit, `54b1553`,
      was committed at 16:08:58 on the same day, three seconds after item
      215's code commit `c09b07d`. So a date comparison cannot show that
      approval preceded migration. AC7 adds an ancestry check (AC7's
      correction). Measured at claim: `00fe6f5` is an ancestor of
      `c09b07d`.
- **A3 (pin, item 215): the identity count and the human-report comparison.**
  - **The case report** is the `segfacet_report.json` that `segfacet run
    --scan <scan> --seg <seg> --intensity --out <dir>` writes for the
    `clean_control` manifest case, with no reference flag.
  - **Its leaf paths** are `segfacet.catalogue.iter_leaf_paths` over the
    report without `schema_version`, `config_version`, `case_id`, `verdict`,
    `reasons`, `per_label`, `findings` and `run_manifest`, each with one
    leading `features.` removed.
  - **A path's last segment** is the text after its last `.`, with one
    trailing `[]` removed.

  Item 215's AC1 holds both counts at exactly 1, in
  `tests/test_215_per_label_migration.py`. Its Validation step 4 holds
  `segfacet_report.txt` byte-identical for `clean_control` and `displace`
  across its own base and branch. Its author asked this item to replay
  steps 2 and 4 from a clean clone, and AC3 and AC16 do so.
  `segfacet_report.txt` renders the verdict, the reasons, the per-label
  findings, the findings and the intensity table. It carries no
  `features_version` and no spacing value, measured on `clean_control` at
  `f5c79df` (462 lines). So neither the stage's version bumps nor the
  spacing collapse is expected to move it. Those bumps are
  `FEATURES_VERSION_STAGE3` from `"0.2"` to `"0.3"` in item 215, and the
  base `FEATURES_VERSION` bumped once by whichever item first reshapes a
  block without Stage 3. The top-level `schema_version` stays `"0.1"`. No
  replay step here reads a version value. AC3 compares regenerated
  artifacts with their committed copies, both built from the same tree, so
  a bump appears on both sides.
  - **The catalogue driver (item 215, step 5).** Item 215 extends the
    catalogue's reference-delta driver, so the regenerated catalogue lists
    the 20 report-only paths at their new paths. AC10 and AC12 rely on that.
  - *Re-checked at claim (2026-10-06, base `8a5ebed`): agrees on the
    definitions, corrected on the versions and on one report.*
    - **The definitions stand.** The `clean_control` report's top-level keys
      are `schema_version`, `config_version`, `case_id`, `verdict`,
      `reasons`, `per_label`, `features`, `findings` and `reference_delta`.
      The report-level `image_features` key is gone (item 216's A14). So
      A3's exclusion list leaves `features` and `reference_delta`, as
      intended. The report has 149 leaf paths.
    - **Identity counts.** Item 215's AC1 holds after item 216: one leaf
      path ends `label` and one ends `level_name`.
    - **The catalogue driver.** It lists all 20 report-only paths, and all 20
      are in the report.
    - **Versions (corrected).** Item 215 made every bump (its D10), and item
      216 bumped none:
      - `FEATURES_VERSION_STAGE3` went `"0.2"` → `"0.3"`;
      - the base `FEATURES_VERSION` went `"0.1"` → `"0.2"`;
      - `IMAGE_FEATURES_VERSION` and `REFERENCE_DELTA_VERSION` went `"1.0"` →
        `"1.1"`;
      - the report's `schema_version` stays `"0.1"`.

      So every Stage-3 record's `features_version` reads `"0.2"` on B and
      `"0.3"` on the tip. That is why AC15's footprint record excludes that
      row.
    - **The `.txt` report.** It still renders no `features_version` and no
      spacing value. A grep for `features_version` and `spacing` finds
      neither in the `clean_control` or `sequence_break` reports. It is
      byte-identical to B for `clean_control` and `displace`. **It differs
      for `sequence_break`** (corrected). The difference is a
      reference-backed change, not a version or spacing value (AC16's
      correction).
    - **Rule-read attribution.** Insight `2026-10-06-1935` records that the
      catalogue's static scan understates rule reads ("Read by >=1 rule"
      51), because several features share last segments. AC12's drift
      agreement compares the committed catalogue with a fresh build, so the
      understatement does not affect it. No evidence text claims that the
      reader attribution is complete.
- **A4 (pin, item 216, as specified 2026-10-05): addressability, the collapse
  and firing.** Read against item 216's A1–A4 and its D1, D5 and D8.
  - **The module.** It is
    `tests/test_216_neighbour_pair_and_case_level_migration.py`. Its AC1 is
    the addressability check: the catalogue's path set equals the new paths
    of all `kept`/`moved` rows, both owners, all 165 rows. AC10 recomputes
    the same equality in the clone. Its AC5 shows the collapse's rule-level
    effect on a constructed T13 variant of `fuse_adjacent`, not on a
    committed case.
  - **The survivor (maintainer decisions, 2026-10-05).** It is the new path
    both spacing rows share, item 214's AC8. `new(p)` and the resolver are
    item 216's terms, which this spec reuses.
    - **Label set and order.** It covers every label, in item-198 anatomical
      order, with unrecognised labels last.
    - **Where it is present.** It is present on every record that carries
      `relationships.neighbour_spacings_mm` today. It is `[]` only below two
      labels, and on coincident-centroid records it is computed as today.
    - **Stage-3-only fields.** Only the four derived statistics
      (`mean_spacing_mm`, `cv_spacing`, `deviations_mm[]`,
      `outlier_pairs[]`) stay Stage-3-only.
    - **`fused_label`** pairs each spacing with the two anatomically
      adjacent labels.
    - **Why AC15 holds.** Every committed case has at least two labels, no
      coincident centroids and no unrecognised label. So on every untouched
      case the survivor equals B's `spacings_mm[]` element for element, and
      AC15's equality is well posed.
  - **Firing (D8, a maintainer decision 2026-10-05).** No rule's firing
    changes on either committed corpus. Both manifests stay off item 216's
    May change. If the build would change firing, its builder hands back
    rather than re-expecting a case.
  - **The value footprint (its A5).** It is `sequence_break` only, with the
    statistics quoted in the Description.
  - **The unwired statistics.** If Answer 6 re-derives
    `stage3.per_label_neighbourhood[].stats.spacing_mm.*` from the survivor,
    that value change lands in item 216 too (its Left open). Those fields
    are unwired, so AC14 is unaffected. Because they lie outside the spacing
    family, AC15 does not compare them either.
  - **Version discriminators.** The batch rule is stated in A3. Checking
    that item 216 re-bumps nothing is item 216's own Validation step 4, a
    validator check, and this item does not repeat it.
  - **Regeneration (its step 8).** On top of item 215's set, item 216 also
    rewrites `tests/corpus/119_pre_119_digests.json`'s leaf-path-set digest,
    and `tests/report_format_fixture.py` with the format contract. AC3
    covers both.
  - **Its replay request.** It asks this item to replay its Validation steps
    2 and 5 from a clean clone. AC3 and AC16 do so.
  - *Re-checked at claim (2026-10-06, base `8a5ebed`; item 216 as merged, its
    claim corrections, D11–D18 and `## Review findings` read): corrected on
    five points, agrees on the rest.*
    - **The module (corrected).** Item 216's AC1 compares the catalogue with
      the 153 `kept`/`moved` new paths plus `case.sequence.order[]`. The
      catalogue lists 154 paths. AC10 and AC11 now count that path.
    - **The survivor (agrees).** It is `pairs.adjacent.spacings_mm[]` (item
      216's D11), in item-198 order over every label. `fused_label` gates on
      `pairs.adjacent.mean_spacing_mm` and pairs in that same order (its A12
      re-check, D15).
    - **What is measured (corrected).** D11 adds the record-wide anatomical
      order. The fit, the held-out offsets, the tangents, the curvature,
      both consistency extractors and the neighbourhood all take the
      anatomical sequence. `relationships` keeps integer input, so
      `out_of_order_labels[]` is unchanged. The authorised change therefore
      reaches every Stage 3 value wherever the orders disagree. Measured at
      claim, from B and the tip, over every `kept`/`moved` row except
      `features_version` and the container rows: only `sequence_break`
      resolves differently, in 37 rows. These are 25 per-label `curve`,
      `orientation` and `neighbourhood` rows, the curvature scalars and
      arrays, and the four spacing statistics. `u_values[]` differs by
      element order only. AC15's correction measures this whole footprint.
    - **Why AC15 holds (agrees).** Every committed case has at least two
      labels, no coincident centroids and no unrecognised label. Re-measured:
      on all 17 other cases `case.sequence.order[]` equals ascending integer
      order.
    - **Firing (agrees without a reference, corrected with one).** Without a
      reference, all 18 cases give identical `Finding.to_dict()` lists on B
      and the tip (A10's re-check). With the bundled VerSe19 reference,
      `sequence_break`'s `reference_delta` findings move (item 216's A5
      re-check and corrected Validation step 5, re-measured at claim). AC16
      is predicted not to hold there (its correction).
    - **The value footprint (corrected).** It is `sequence_break` only, and
      wider than the spacing family. The spacing family's values are in the
      Description's correction.
    - **The unwired neighbourhood statistics (settled).** They are
      re-derived over the anatomical sequence (item 216's A3 re-check), as
      part of D11. They now sit at item 215's paths
      `per_label.{label}.neighbourhood.stats.*`. They are among the 37 rows,
      and AC15's correction counts them.
    - **Versions (agrees).** Item 216 bumped none (its D11 and D15).
    - **Regeneration (agrees, with one addition).** Item 216 regenerated the
      eight `docs/aide/*.generated.*` files, `golden_evidence.generated.json`
      included at `(29, 95)` per case, plus the digest file and the format
      contract. AC3 already lists all of them. It also added one
      `WINDOWS_TESTS` entry to `.github/workflows/ci.yml`. That file is not
      generated, and no criterion here reads it.
    - **`path_u` (noted).** Its schema bounds were removed (item 216's
      `## Review findings`, D18) because Python 3.12 and later can yield
      `1.0000000000000002` (insight `2026-10-06-934c`). AC1's correction
      records the interpreter.
- **A5 (measured): what the collapse can move on the committed corpora.**
  - **Geometric label sets.** Every geometric case's label set lies in
    {19, …, 24} except `sequence_break`, whose set is {20, 21, 22, 23, 28}.
    Label 28 is TPTBox `T13`, which sits anatomically before label 20 (`L1`).
  - **Intensity label sets.** Every intensity case uses
    `clean_spine_seg.nii.gz`, whose set is {20, …, 24}.
  - **Where the arrays differ.** So `sequence_break` is the one case where
    integer and anatomical orders disagree, and the one case whose two stored
    arrays differ (values in the Description).
  - **Who reads the arrays.** Under `src/segfacet/heuristics/`, only
    `fused_label.py` names either array. No rule names `mean_spacing_mm`,
    `cv_spacing`, `deviations_mm` or `outlier_pairs`.
    `human_report.py` names only `neighbour_spacings_mm`, and the `.txt`
    report does not render it (A3).
  - **The reasons.** `sequence_break`'s findings are `mislabel/ordering` on
    {20, 28} and `sequence/shift` on {28}. Neither reason string contains a
    spacing value. So AC14's exact comparison needs no exception for it.
  - **Firing.** Item 216 measured `fused_label` on `sequence_break` read in
    anatomical order (its A5). Its spacing ratios rise to 4.0055 at T13 and
    2.5186 at L1, but no label's size ratio exceeds 1.0032, against a
    threshold of 1.5. So the rule cannot fire there.

  So the authorised retune is expected to move values on `sequence_break`
  and no finding anywhere. AC14 and AC15 measure both.
  - *Re-checked at claim (2026-10-06, base `8a5ebed`; Implementation Steps
    step 0): corrected on the readers and on "no finding anywhere", agrees
    on the label sets and the reasons.*
    - **Label sets (agrees).** Measured from each case's `per_label` keys:
      - every geometric case lies in {19, …, 24}, except `sequence_break`
        {20, 21, 22, 23, 28};
      - `split_own_label` carries 19 (T12), which sits in order before 20;
      - every intensity case is {20, …, 24}.

      The tip's `case.sequence.order[]` equals ascending integer order on
      every case but `sequence_break`, where it is `[28, 20, 21, 22, 23]`.
    - **Readers (corrected).** Under `src/segfacet/heuristics/`, only
      `fused_label.py` names the spacing family. It reads
      `pairs.adjacent.spacings_mm[]`, and it now also names
      `pairs.adjacent.mean_spacing_mm`, as its Stage-3 gate (a bookkeeping
      declaration, item 216's D15). No rule names `cv_spacing`,
      `deviations_mm` or `outlier_pairs`. `human_report.py` reads
      `pairs.adjacent.spacings_mm` in `render_feature_table`, which the
      `.txt` report does not render.
    - **Reasons (agrees).** Without a reference, `sequence_break`'s findings
      on B and the tip are the same two, with identical `to_dict()`. So
      AC14's exact comparison needs no exception.
    - **"No finding anywhere" (corrected).** That holds on AC14's path, which
      runs without a reference. It does not hold on AC16's path, which runs
      against the bundled VerSe19 reference. There, D11 moves
      `sequence_break`'s per-label `curve.offset_mm` values (item 216's A5
      re-check). Label 20 goes 0.0595 → 0.0038, and label 21 goes 0.1513 →
      0.2576. So `reference_delta`'s `spline_offset_mm` out-of-range finding
      passes from label 21 to label 20 (AC16's correction).
- **A6 (measured; engine 2.35.0, re-checked 2.39.0): B, the pre-migration commit.** B is the
  `aide/queue-029` commit whose subject is exactly `progress(aide): item 214
  -> done`. It is found in the working checkout with `git log --format=%H
  --grep="^progress(aide): item 214 -> done$" aide/queue-029`, which must
  print exactly one SHA. `aide merge` writes that subject when it lands an
  item, as it did for items 212 and 213 on `aide/queue-028`. Item 214 changes
  nothing under `src/segfacet/` (its Authorised paths). So B's code is the
  record as it stood before either migration item, and every later code
  change on the branch is item 215's or 216's. The base tree is a
  `git worktree`, not a second clone, for two reasons:
  - Detaching a clone's `HEAD` needs a repo-override git form, which §3
    blocks.
  - A worktree is made by a bare command in the working checkout. It still
    has its own venv, so the Gotcha's own-venv requirement holds, and it has
    git metadata, so insight `2026-10-05-dc87` holds.

  Nothing is run under pytest in the base tree.
  - *Re-checked at claim (2026-10-06, base `8a5ebed`): agrees.*
    - **B is found.** The `git log` prints exactly one SHA,
      `3be6c381e8c986754703d80a32e56cb7e68102d5`, committed 2026-10-05.
    - **B's code is pre-migration.** Item 214 changed nothing under `src/`
      (`git diff 2cbb24e 3be6c38 -- src/` is empty).
    - **Every later `src/` change is 215's or 216's.** Five commits touch
      `src/` after B, all `feat(215)`, `fix(215)`, `feat(216)` or
      `fix(216)`.
    - **The rig works.** A worktree at B, created and removed with bare
      commands, resolved its own `segfacet` at claim.
- **A7: "every generated artifact" is AC3–AC5's list.**
  - **Byte for byte (AC3).** Every committed file a module in the repo
    regenerates without a gated capability is compared byte for byte. That
    covers the five `docs/aide/*.generated.*` pairs and singles, the report
    format contract, and both corpora with every fixture they name.
  - **Two exceptions, checked their own documented way.**
    `src/segfacet/reference/reference_default.json` is compared under
    `assert_matches_committed_artifact`, because it carries a
    platform-sensitive PCA float (`tests/test_045_reference_artifact.py`,
    AC10). It is included because item 215 re-points `reference/ingest.py`,
    which builds it, and is predicted unchanged. `docs/aide/corpus_sheet.png`
    is checked by its embedded input digest, because its PNG bytes depend on
    the matplotlib, FreeType and zlib versions (`segfacet.synth.corpus_sheet`
    docstring).
  - **Excluded.**
    - `src/segfacet/reference/reference_verse_v1.json` needs the real VerSe19
      cohort, which a clean clone does not have.
    - `segfacet.synth.golden` writes snapshots only to a caller's directory,
      so nothing it produces is committed.
    - `docs/aide/status/` is the status-report skill's output, not a package
      artifact.

  `.gitattributes` already pins every compared text file `eol=lf` and every
  `.nii.gz` `binary`.
- **A8 (measured): "both corpora" are the two committed manifests.** They
  are `tests/corpus/manifest.json`, with 14 geometric cases, and
  `tests/corpus/intensity/manifest.json`, with 4 intensity cases. AC13–AC15
  read the case ids live from each tree's manifests.
- **A9 (maintainer decision, 2026-10-05): criterion 2's "every feature" is
  every leaf of a real report.** That covers the catalogue's paths and every
  leaf a bundled-reference pipeline record carries.
  - **The 20 report-only paths.** At `f5c79df` such a report carries 20
    leaf paths the catalogue does not list. They are
    `reference_delta.{label}.features.<f>.<s>`, for `extent_x_mm`,
    `extent_y_mm`, `extent_z_mm` and `spline_offset_mm`, five statistics
    each. The catalogue realises the delta block from one placeholder
    feature (item 214, A4).
  - **How the stage covers them.** Item 214's table gives them rows (165
    in all). Item 215 owns those rows and extends the catalogue's
    reference-delta driver to list them. So the catalogue-equals-table check
    (AC10, item 216's AC1) covers them.
  - **The direct evidence.** AC11 adds what the maintainer's reading asks
    for: on a real report, every leaf is a stored new path in the table,
    counted rather than inferred from the catalogue.
  - **Correction, 2026-10-05:** this assumption first defaulted to the
    catalogue's path set. Under that default, the 20 report-only paths were
    only recorded. The maintainer chose the wider reading, so that default
    was dropped.
  - *Re-checked at claim (2026-10-06, base `8a5ebed`): agrees on the
    coverage, with one addition.* Item 215 owns the 20 rows. Its extended
    driver lists them, and the catalogue and the `clean_control` report
    carry all 20 at their new paths. The addition: the report also carries
    `case.sequence.order[]`, a stored leaf with no table row (A4's
    re-check). AC11 compares against the table's new paths plus that path,
    so "every leaf of a real report" stays the reading. That path is named
    in the evidence, not dropped.
- **A10 (maintainer decision, 2026-10-05): the authorised retune covers
  measured values, and no corpus firing changes.** This is item 216's D8,
  now a decision. AC14 therefore holds
  every case's findings to exact equality, touched cases included. AC15
  holds the value change to the touched cases.
  - **Correction, 2026-10-05:** this assumption first read the 2026-10-05
    decision as also covering a change in `fused_label`'s findings on a
    touched case. Under that reading, touched cases' findings were recorded,
    not asserted. Item 216's spec, which landed the same day, measured that
    no such change occurs and made firing-unchanged its own D8. So the
    exception was dropped.
  - *Re-checked at claim (2026-10-06, base `8a5ebed`, item 216 merged):
    agrees on AC14's path, and leaves AC16's path open.*
    - **AC14's path.** Run without a reference, all 18 cases give identical
      `Finding.to_dict()` lists on B and the tip, reasons included. Item
      216's D8 held through its D11.
    - **What the decision covers.** The decision, and item 216's D8, are
      about the committed corpora's firing, and the ratchet measures that
      without a reference.
    - **AC16's path.** With the bundled VerSe19 reference, `sequence_break`'s
      `reference_delta` findings change: one out-of-range finding changes
      label, and four distances move (AC16's correction). Neither this
      decision nor D11 says whether that is authorised. It is recorded as
      **Left open**, and AC16 holds its bar.
- **A11 (default, seen by the maintainer 2026-10-05 and kept): "identity
  field" means the per-label `label` and `level_name`.** That is the known
  instance the roadmap names, and item 215's AC1 definition. Neighbour-pair
  identity (`overlaps[].{label_a, label_b, name_a, name_b}`, plus any pair
  keys item 216 introduces) is not counted by AC9. AC18's criterion-2
  evidence lists the pair-identity leaf paths the case report carries, as a
  measurement.
  - *Re-checked at claim (2026-10-06, base `8a5ebed`): agrees, with one
    addition to what is listed.*
    - **Pair identity.** Item 216 merged `overlaps[].name_a` and `.name_b`
      onto `per_label.{label}.level_name`. It kept `label_a` and `label_b`
      under `pairs.overlaps[]` and introduced no other pair key.
      `clean_control` has no overlaps, so its report carries only the
      container leaf `pairs.overlaps[]`.
    - **Label references.** `case.sequence.order[]` (item 216's A15) stores
      the labels again, as a list of integers. So do the existing
      `neighbourhood.window_labels[]` and
      `component_contacts[].neighbour_label`. These are references to labels,
      not an entity's own identity field. AC9's last-segment count does not
      see them.
    - **The addition.** AC18's criterion-2 text lists them beside the
      pair-identity paths, so a reader of the attestation sees them
      (AC18's correction).
- **A12 (engine 2.35.0, re-checked 2.39.0): bookkeeping verbs.** None of Stage 27's three boxes
  is ticked on 2026-10-05, so each takes `accept`. No verb writes an
  unticked-box annotation. The hand-written ` *(not attested …)*` suffix is
  the shape §1 allows beside an unticked box, and Stage 32's criterion 1
  carries one. `aide merge 217` flips this item's own deliverable bullet. No
  bullet is hand-edited.
  - *Re-checked at claim (2026-10-06, engine 2.39.0): agrees.* All three
    Stage 27 boxes are still unticked. §1 → progress.md still allows an
    annotation beside an unticked box ("say why in an annotation beside
    it"). The ` *(not attested …)*` shape is still carried in `progress.md`,
    by item 161 and item 169 among others. Item 217's bullet is still the
    one 📋 deliverable of Stage 27.
- **A13: no new human gate, no environment-gated capability, no new test.**
  Gate-0080 is the only decision this item needs. Under posture `prototype`
  no scaffolding is added beyond what the attestations need:
  - Criterion 1 is a gate read.
  - Criterion 2's two halves each have a merged in-suite check (A3, A4).
  - Criterion 3's standing halves are `test_104` and `test_163`. Its
    before/after half is a dated diff-time measurement, which §1 forbids as
    a suite assertion.

## Implementation Steps

0. **At claim (spec-author, before anything runs).** Items 214, 215 and 216
   have merged, and gate-0080 reads approved.
   *Done (2026-10-06, base `8a5ebed`).* Re-checks are appended to A1–A6 and
   A9–A11. Corrections are appended to the Description and to AC1, AC6, AC7,
   AC10, AC11, AC15, AC16 and AC18, with a new **Left open**. The claim-time
   measurements used a worktree at B on `PYTHONPATH` and the working venv.
   They are starting points only, and steps 2–10 re-measure everything on the
   clone rig.
   - Re-check A1–A4 against the merged specs and code, and append a dated
     re-check to each. That includes any amendment item 216's spec received
     at its own claim, such as Answer 6's settlements or a D8 hand-back.
   - Re-run A5's label-set, reader and reason measurements on the claim base,
     and append the result.
1. **Preconditions.** Run `python .aide/scripts/aide.py status` and confirm
   that items 214–216 are ✅. Record `aide check`'s output as the baseline.
2. **Rig (AC1, AC2).** Clone the claim branch. Find B (A6) and add the base
   worktree. Bootstrap both venvs, each with its own `aide env --bootstrap`,
   and print both resolution proofs. From here on:
   - every Python command runs with the venv of the tree it measures, and
     with `-P`;
   - every pytest run uses `-P`, `-c <clone>/pyproject.toml` and `--rootdir
     <clone>`, so the working checkout's `tests` package cannot shadow the
     clone's.
3. **Artifacts (AC3–AC5).** Run each generator through its module's own
   `--json` / `--md` / `--out` argument. Compare with
   `pathlib.Path.read_bytes`, and use `assert_matches_committed_artifact`
   for the reference. Scratch scripts live in the scratchpad only. Write no
   generator and no comparison helper into the repo.
4. **Criterion 1 (AC6, AC7).** Run the clone's `aide gate list`. Read the
   committer date of the `progress(aide): item 215 -> in-progress` commit
   with `git log --format=%H%x09%cs --grep="^progress(aide): item 215 ->
   in-progress$" aide/queue-029` in the working checkout, which must print
   exactly one line.
5. **Named checks (AC5, AC8, AC12, AC13).** Run each module or node id in the
   clone, in the foreground. Record exit codes, node counts and skip lists.
6. **Measurements (AC9–AC11, AC13–AC16).** Do the following in the clone,
   and in the base tree where an AC names it:
   - build the case report and count its leaf paths, reusing
     `segfacet.catalogue.iter_leaf_paths`;
   - read the table through `read_mapping`, and the catalogue's path set from
     the regenerated JSON;
   - read `build_matrix().conformance`;
   - run the findings script, the touched-case predicate and the
     spacing-family read in both trees. The clone resolves its spacing family
     through `new(...)` over the table;
   - run `segfacet run` for the three `.txt` comparisons.

   Record every value verbatim.
7. **Environment (AC17).** Run `aide env` and the three profile checks. Then
   read the gated table and the specs.
8. **Bookkeeping (AC18).** Run the three `accept` verbs in ascending order.
   For any criterion that does not hold, write the annotation and capture
   the `gap` line instead. Capture one `insights.md` line for each
   divergence the replay finds. Tick, reword or archive no existing entry.
9. **Check.** Re-run `aide check` and compare its output with step 1's
   baseline. A new error is a finding, and `aide merge` refuses on one (§4).
   The warning set is pinned nowhere.
10. **Suite (AC19).** Bring the clone up to the final commit and run the
    configured suite. Record the counts. Then delete the clone, and remove
    the base tree with `git worktree remove --force <scratch>/base217`. The
    `--force` is needed because the base tree holds an untracked venv.
11. Record everything in Decisions & Trade-offs.

No `src/segfacet/**` change, no test change, and no new dependency.

## Authorised paths

**May change:**

None. This item commits only `docs/aide/progress.md` (through `aide progress
accept`, or the hand annotation AC18 allows beside an unticked box),
`docs/aide/insights.md` (through `aide insights add`) and this spec's
Decisions record. All three are always authorised. Its replay writes only in
the scratchpad.

**Asserts against:**

- `src/segfacet/**` — the package the clone runs; read by every replay criterion, `reference/reference_default.json` included (AC4)
- `docs/feature-taxonomy.md` — the mapping table AC10 reads through item 214's reader
- `tests/feature_taxonomy_mapping.py` — the reader itself (AC10)
- `docs/aide/roadmap.md` — Stage 27's three criteria, quoted by AC18
- `docs/aide/feature_catalogue.generated.json` — regenerated and compared (AC3); its path set (AC10)
- `docs/aide/feature_catalogue.generated.md` — regenerated and compared (AC3)
- `docs/aide/failure_modes.generated.json` — regenerated and compared (AC3)
- `docs/aide/failure_modes.generated.md` — regenerated and compared (AC3)
- `docs/aide/traceability_matrix.generated.json` — regenerated and compared (AC3)
- `docs/aide/traceability_matrix.generated.md` — regenerated and compared (AC3)
- `docs/aide/golden_evidence.generated.json` — regenerated and compared (AC3)
- `docs/aide/rules.generated.md` — regenerated and compared (AC3)
- `docs/aide/corpus_sheet.png` — input digest checked (AC5)
- `tests/golden/report_format_contract.json` — recomputed and compared (AC3)
- `tests/report_format_fixture.py` — the contract's sole source (AC3)
- `tests/corpus/manifest.json` — regenerated and compared; geometric case ids (AC3, AC13–AC15)
- `tests/corpus/fixtures/**` — regenerated and compared (AC3); the AC16 inputs
- `tests/corpus/intensity/manifest.json` — regenerated and compared; intensity case ids (AC3, AC13–AC15)
- `tests/corpus/intensity/fixtures/**` — regenerated and compared (AC3)
- `tests/corpus/119_pre_119_digests.json` — its leaf-path-set digest recomputed and compared (AC3)
- `tests/test_104_feature_catalogue_drift.py` — named check (AC12)
- `tests/test_163_specificity_ratchet.py` — named check (AC13)
- `tests/test_178_corpus_sheet.py` — named check (AC5)
- `tests/test_214_feature_taxonomy_design.py` — named check (AC8)
- `tests/test_215_per_label_migration.py` — named check (AC8)
- `tests/test_216_neighbour_pair_and_case_level_migration.py` — named check (AC8)

## Testing Strategy

**No new test module.** Every criterion above is a replay whose evidence is
the output recorded in Decisions, which the validator re-executes (A13). The
standing checks behind the stage already exist:

- `test_104` and `test_163` cover criterion 3;
- item 215's AC1 test covers identity, and item 216's check covers
  addressability, for criterion 2;
- `test_214`'s answer and table checks back the design note behind
  criterion 1.

Adding a module that re-asserts them would duplicate them. A module asserting
the B-versus-clone comparison would pin a diff against a baseline (§1, §6).

**Adversarial cases:** none, since no test is written.

**What this item pins nowhere:** no `aide check` warning count, no suite
total, no `progress.md` text, no `insights.md` entry, no engine version. The
`progress.md` evidence strings are dated measurements the validator checks on
the branch.

**Existing tests to reconcile:** none. `tests/` and `.aide/scripts/tests`
were grepped on 2026-10-05 for `Stage 27`, `stage_section(27`, `_STAGE_27`
and `item 217`. The one hit is `tests/test_115_stage26_validation.py`, which
uses the `## Stage 27` heading only to end Stage 26's section. Ticking Stage
27's boxes moves no heading. `tests/test_aide_check_no_errors.py` asserts no
errors, and both an `accept` annotation and a hand ` *(not attested …)*`
suffix are shapes `aide check` accepts.

## Validation  <!-- OPTIONAL: how to OBSERVE this working, beyond the tests -->

This item **is** the stage validation. The validator re-executes the replay,
not only the suite. It checks each Decisions record against its own run:

- both rigs and both resolution proofs (AC1, AC2);
- each artifact comparison, the reference comparator and the sheet digest
  (AC3–AC5);
- the gate row and the two dates (AC6, AC7);
- the three item modules (AC8);
- the identity counts, the set equality and the real-report difference set
  (AC9–AC11);
- the drift test, the ratchet and the conformance read (AC12, AC13);
- the two trees' findings lists, the touched-case predicate, both trees'
  spacing families and the `.txt` comparisons (AC14–AC16);
- the profiles and the gated table (AC17);
- each `aide progress` command against the `progress.md` diff (AC18);
- the full-suite counts from a fresh clone of the final commit (AC19);
- `python .aide/scripts/aide.py scope 217 --base aide/queue-029`, which must
  show no path outside the always-authorised three.

**Environment gating.** No criterion depends on a `[validation]` profile.
`pyradiomics`, `docker` and `gpu` are evaluated and recorded only (AC17).
`intensity_pipeline_findings` runs with `enable_pyradiomics=False` by
default, so AC14 and AC15 do not depend on PyRadiomics.

**Honest downgrade.** A replay that cannot run is recorded as **not
performed**, naming what was missing, and its criterion stays unticked with
that reason. A skip-clean run is never evidence.

**Do not run `aide gate approve` or `aide gate decline`.**

## Dependencies

- **Item 214**: the signed design note `docs/feature-taxonomy.md`, its mapping
  table, the reader `tests/feature_taxonomy_mapping.py`, and the sign-off
  gate (A1, A2; AC6–AC8, AC10).
- **Item 215**: per-label fields migrated, identity stored once, the
  catalogue regenerated (A3; AC8, AC9, AC16).
- **Item 216**: neighbour-pair and case-level fields migrated, the spacing
  collapse, and the addressability check (A4; AC8, AC10, AC11, AC14, AC15).

Gate gate-0080 also holds this item — `Blocks: 215, 216, 217`.

**Downstream:** none in this queue. This item runs last, and its merge flips
Stage 27's last 📋 deliverable bullet.

## Decisions & Trade-offs

**Replay record (2026-10-06, builder).** Every AC1-AC18 below held against its
corrected bar. Nothing under `src/` or `tests/` was edited, and no generator or
comparison helper was written into the repo; the scratch scripts live in the
session scratchpad only. Interpreter for every byte comparison: CPython 3.11.15.

- **Preconditions (step 1).** `aide status` shows items 214-216 done, with
  queue-029 holding 1/4 items open (217). `aide check` printed `OK (7 warning(s))`
  before the replay (32 specs without Assumptions, two awaiting gates for stage
  16, four re-accepted Stage 20 retractions) and is re-run at step 9 below.
- **AC1.** Clone: `<scratchpad>/clone217`. Clone commit (every attestation
  cites it): `18609089bf27bda29ba16112ca1997859bc39fb2`, the claim branch's tip at
  clone time. `<clone>/.venv/bin/python -P` prints `segfacet.__file__` =
  `<scratchpad>/clone217/src/segfacet/__init__.py`, under the clone.
  `sys.version` = `3.11.15 (main, Jun 11 2026, 15:20:16) [GCC 14.3.0]`. The venv
  was built by `aide env --bootstrap` (unconstrained `pip install -e .[dev]`:
  numpy 2.4.6, scipy 1.17.1, nibabel 5.4.2, scikit-image 0.26.0).
- **AC2.** B = `3be6c381e8c986754703d80a32e56cb7e68102d5` (the single commit
  `git log --grep` printed for `progress(aide): item 214 -> done`). The base
  tree was made with `git worktree add --detach <scratchpad>/base217 <B>` and has
  its own bootstrapped venv, same interpreter. Its `segfacet.__file__` =
  `<scratchpad>/base217/src/segfacet/__init__.py`, under the base tree.
- **AC3 (all equal, `read_bytes()`).** `feature_catalogue.generated.json`
  (276196 B) and `.md` (62253 B); `failure_modes.generated.json` (63582 B) and
  `.md` (56261 B); `traceability_matrix.generated.json` (61032 B) and `.md`
  (34236 B); `golden_evidence.generated.json` (1470 B); `rules.generated.md`
  (11119 B); `tests/golden/report_format_contract.json` (4585 B, from
  `format_contract_text()` with the clone root first on `sys.path`);
  `tests/corpus/manifest.json` (16178 B) with all 18 files the generator wrote
  (manifest plus 17 fixtures, equal to every committed generated file under
  `tests/corpus/` except the two hand-kept JSON files `094_pre_migration_snapshot.json`
  and `119_pre_119_digests.json`); `tests/corpus/intensity/manifest.json`
  (4089 B) with all 6 files (manifest plus 5 fixtures). The catalogue's
  regenerated path set has 154 paths, and the SHA-256 of
  `"\n".join(sorted(paths))` is
  `2539cea973b6b1063401e8cfcc5f9fd4d8d15d32491fd58bad42098d9b15c467`, equal to
  `119_pre_119_digests.json`'s `catalogue_leaf_path_set_sha256`.
- **AC4.** `-m segfacet.reference.artifact --out` exit 0, and
  `assert_matches_committed_artifact(<fresh>, reference_default.json)` returned
  without raising.
- **AC5.** `tests/test_178_corpus_sheet.py::test_ac7_committed_sheet_is_current`:
  1 passed, no skips, exit 0.
- **AC6.** `gate list` in the clone prints exactly one gate containing `Stage 27
  feature-record taxonomy sign-off`: `✅ gate-0080`. The approval date, read
  from the clone's `progress.md` Status cell, is `✅ Approved (2026-10-06)`.
  Decision / evidence cell: "Signed 2026-10-06 after review: one anatomical
  element order stored as case.sequence.order[]; per-label values stored per
  label whatever computed them; intensity enters the persisted record (Option
  A). Scope axis unchanged, items 215/216 not re-cut. docs/feature-taxonomy.md @
  2364df4."
- **AC7.** The approval commit `00fe6f57259d8a642366d0dcb6c87725c00003f9`
  (`docs: human gate-0080 approved`, committed 2026-10-06T15:19:25+01:00) is the
  only match. The earliest `feat(215)` commit on `aide/queue-029`,
  `c09b07dc573c4b518c2cd3af10a3351ed1460697` (2026-10-06T16:08:55+01:00), is
  the only one. `git merge-base --is-ancestor <gate> <feat>` exited `0`. The
  `progress(aide): item 215 -> in-progress` commit is `54b1553` (2026-10-06,
  16:08:58), which also matched exactly once, so both date strings read
  2026-10-06 and the ancestry result is what orders the events.
- **AC8.** In the clone, foreground, `-n auto`, `-P`, `-c <clone>/pyproject.toml`,
  `--rootdir <clone>`, `-rs`: `test_214_feature_taxonomy_design.py` 11 passed,
  `test_215_per_label_migration.py` 6 passed,
  `test_216_neighbour_pair_and_case_level_migration.py` 15 passed. Exit 0 and no
  skips in each. `test_214` is unchanged.
- **AC9.** The case report is `segfacet run --scan base_scan --seg
  clean_control_seg --intensity` with no reference flag, from the clone. It has
  149 leaf paths (item 215's definition). Last segment `label`: 1 path,
  `per_label.{label}.label`. Last segment `level_name`: 1 path,
  `per_label.{label}.level_name`.
- **AC10.** Table: 165 rows, 80 `kept`, 73 `moved`, 12 `merged` (130 Moved by
  215, 35 by 216). The `kept`/`moved` new paths number 153, and adding
  `case.sequence.order[]` (the one stored path with no table row, the signed
  note's Deviation 11, settled by the maintainer ruling of 2026-10-06) gives
  154. The catalogue's path set has 154. The two sets are equal (both
  differences empty); the catalogue contains `case.sequence.order[]`.
- **AC11.** Recognisability: the leaf set is non-empty (149), and all 20
  report-only rows' new paths are among the leaves. Of the 149 leaf paths, 148
  lie among the `kept`/`moved` new paths. Against the table alone the
  difference is exactly `{case.sequence.order[]}`; with that path added the
  difference is `{}` (size 0).
  - Neighbour-pair identity leaf paths the report carries (A11, listed and not
    counted): `pairs.overlaps[]` only (the container leaf; `clean_control` has no
    overlaps, and `label_a`, `label_b`, `name_a`, `name_b` carry no leaf).
  - Label-reference leaf paths (listed, not counted): `case.sequence.order[]`,
    `per_label.{label}.components.component_contacts[].neighbour_label`,
    `per_label.{label}.neighbourhood.window_labels[]`.
- **AC12.** `tests/test_104_feature_catalogue_drift.py`: 53 passed, no skips,
  exit 0.
- **AC13.** `tests/test_163_specificity_ratchet.py`: 24 passed, no skips, exit
  0. `build_matrix().conformance` drives 18 cases: 14 geometric (clean_control,
  crop_at_border, crop_fov_si, displace, fragment, fuse_adjacent,
  fuse_separate, inject_islands, relabel_swap, remove_level,
  remove_level_relabel, sequence_break, split, split_own_label) and 4 intensity
  (clean_hu, degenerate_uniform, implausible_metal, implausible_soft_tissue).
  That set equals the union of the two manifests' `case_id` values. Cases with
  `agrees` False: 0 (agree 18, disagree 0, no unspecified case).
- **AC14.** The same script ran in B's tree and in the clone, each with its own
  venv and `-P`. The two trees' case-id sets are equal (18). Every case's
  `Finding.to_dict()` list is equal in order, reasons included. Finding counts,
  identical in both trees: clean_control 0, clean_hu 0, crop_at_border 3,
  crop_fov_si 0, degenerate_uniform 2, displace 1, fragment 1, fuse_adjacent 1,
  fuse_separate 2, implausible_metal 1, implausible_soft_tissue 1,
  inject_islands 1, relabel_swap 2, remove_level 2, remove_level_relabel 0,
  sequence_break 2, split 1, split_own_label 3. No exception was needed for
  the touched case.
- **AC15.** Touched cases (the base tree's two arrays differ): `sequence_break`
  alone. Spacing family on `sequence_break`:
  - base tree: survivor (`stage3.spacing_consistency.spacings_mm[]`)
    `[33.493976778181626, 32.695217722421916, 33.87239617123004,
    36.840004943124015]`, mean 34.2253989037394, cv 0.04582024664953334,
    deviations `[-0.7314221255577777, -1.530181181317488, -0.353002732509367,
    2.6146060393846113]`, `outlier_pairs` `[]`;
  - clone: survivor (`pairs.adjacent.spacings_mm[]`) `[134.1605001114509,
    33.493976778181626, 32.695217722421916, 33.87239617123004]`, mean
    58.55552269582112, cv 0.7454911250642116, deviations `[75.60497741562978,
    -25.061545917639492, -25.860304973399202, -24.68312652459108]`,
    `outlier_pairs` `[["T13", "L1"]]`.

  The set of cases whose spacing family differs is `{sequence_break}`, equal to
  the touched set. Whole footprint: 152 `kept`/`moved` rows were compared
  (153 less `features_version`), with mapping-valued resolutions skipped; the
  set of cases with any differing row is `{sequence_break}`, equal to the touched
  set, with 37 differing rows (old paths): the six `stage3.per_label_offsets[]`
  fields `closest_u`, `dy_mm`, `dz_mm`, `is_terminal`, `offset_mm`,
  `offset_voxel`; `stage3.curvature.` `coronal_curvature_deg`,
  `coronal_tangent_angles_deg[]`, `inter_tangent_angles_deg[]`,
  `sagittal_curvature_deg`, `sagittal_tangent_angles_deg[]`,
  `tangent_angles_deg[]`, `total_curvature_deg`; the four
  `stage3.per_label_orientations[]` fields `spline_closest_u`,
  `spline_tangent[]`, `spline_tangent_coronal_deg`,
  `spline_tangent_sagittal_deg`; `stage3.monotonic_consistency.u_values[]`
  (element order only); the four spacing statistics `cv_spacing`,
  `deviations_mm[]`, `mean_spacing_mm`, `outlier_pairs[]`; and 15
  `stage3.per_label_neighbourhood[]` fields (`deviation_score`, `is_outlier`,
  `window_labels[]`, and the `stats.{offset_mm, spacing_mm, volume_mm3}`
  `mean`, `median`, `std`, `z_score` rows). This matches the claim-time count.
- **AC16.** `segfacet run ... --intensity` from each tree, no reference flag:
  - `clean_control`: `segfacet_report.txt` byte-identical, 462 lines, 146
    findings in both trees.
  - `displace`: byte-identical, 378 lines, 118 findings in both trees.
  - `sequence_break`: 379 lines in both, 118 findings in both. `difflib.ndiff`
    over `splitlines()` gives a base-only list that equals the spec's 11 base-only
    lines, and a clone-only list that equals the 11 clone-only lines, each in
    order and compared exactly. No other line differs. Every differing line
    names a label in {20, 21, 22, 23} (the `reference_delta` reasons and `Labels:`
    lines). Recorded `(rule_id, labels)` multisets from each
    `segfacet_report.json`: identical except `reference_delta` on label 21 (8 in
    the base tree, 7 in the clone) and on label 20 (6 in the base tree, 7 in the
    clone). Base tree: bounds 4 on each of 20-23; intensity on 22, 23, 28;
    mislabel on (20, 28); sequence on (28); reference_delta 20:6 21:8 22:7 23:7;
    intensity_reference_delta 20:17 21:15 22:18 23:19. Clone: the same except
    reference_delta 20:7 21:7 22:7 23:7. Insight `2026-10-06-f318` is the
    reason the bundled reference sits out of step with the new order.
- **AC17.** No row of the Environment-Gated Capability Verification table names
  Stage 27, or any of items 209-217, in its "Introduced by" cell; none of those
  nine specs carries a `## Environment / Hardware Dependencies` heading. `aide env`
  exit 0 (`venv is Python 3.11; import segfacet succeeds; import pytest succeeds`).
  `env --profile pyradiomics` exit 1 (`No module named 'radiomics'`), `--profile
  docker` exit 1 (not satisfied), `--profile gpu` exit 1 (`No module named
  'cupy'`). Recorded only; the table is not edited.
- **AC18.** The three criteria were attested with `aide progress accept 27
  --criterion N`, N = 1, 2, 3 in order (the evidence is in `progress.md`).
- **AC18, as run.** Criteria 1, 2 and 3 were each accepted with `aide progress
  accept 27 --criterion N` in order, and each printed `accepted`. Every
  criterion's text names the clone commit (and B for criterion 3), the ACs
  behind it, the measured values and the items AC18's corrections require,
  `case.sequence.order[]` and the maintainer's two 2026-10-06 rulings included.
  No box was left unticked, so no `not attested` annotation and no `gap` line
  were written. Stage-criterion attestation was this item's own step 8, not the
  validator's.
- **Step 9 (`aide check`).** After the accepts and the `in-progress` flip it
  prints `OK (7 warning(s))`, the same seven warnings as step 1's baseline. No
  new error and no new warning.
- **AC19.** The clone was brought to `33a7dd7973775c07a5a5b96c6f12f66f5423c3d4`
  (the branch tip once every verb-written commit had landed) with `aide sync
  --item 217`, and `segfacet.__file__` re-printed under the clone. The
  configured suite (`testpaths = ["tests", ".aide/scripts/tests"]`) ran in the
  foreground with `-n auto -rs -P`: **11459 passed, 73 skipped, 0 failed**, exit
  0, in 436.93 s. The 73 skips, none counted as verification:
  - 22 Docker CLI/daemon not available (`test_066` 9, `test_069` 11, `test_070`
    2);
  - 33 CuPy/GPU not available (`test_073` 30, `test_075` 1, `test_072` 1,
    `test_074` 1);
  - 6 real VerSe GT / VerSe19 cohort not mounted (`test_084`, `test_088`,
    `test_091`, `test_118`, `test_125` x2);
  - 1 no real SPINEPS-output fixture (`test_097`);
  - 5 PyRadiomics not installed (`test_features_radiomics`);
  - 6 `test_108` cases with no pinned pre-098 shape (`fuse_adjacent`,
    `remove_level_relabel`, `split`, `split_own_label`, `crop_fov_si`,
    `fuse_separate`).

  The one commit after that tip is this record's own, which changes only this
  spec's Decisions text.

- **Left open:** whether a later stage counts neighbour-pair identity under
  "no identity field is stored more than once". The maintainer kept the
  per-label reading for Stage 27 (A11), so this item records pair identity
  and does not count it.
- **Left open (added at claim, 2026-10-06):** whether the maintainer's
  authorisation covers a changed reference-backed finding on a corpus case.
  The authorisation is item 216's D1 widened by D11, the record-wide
  anatomical order signed at gate-0080. The change in question is on
  `sequence_break` under the bundled VerSe19 reference: four
  distribution-distance values move, and the `spline_offset_mm` out-of-range
  finding passes from label 21 to label 20. That reference was built from
  integer-order fits and is stale for this T13 shape until a rebuild (insight
  `2026-10-06-f318`). D1 and D11 authorise measured values. A10 and item
  216's D8 decide firing on the committed corpora without a reference. None
  of them answers this question. It is the maintainer's to rule, so AC16
  keeps its byte-identical bar. Unless a ruling is recorded first, criterion
  3 stays unticked with that reason (AC16's and AC18's corrections).
  *Settled (2026-10-06; source: maintainer ruling, 2026-10-06, in the
  item-217 claim session):* yes, it is covered. The reference-backed change
  on `sequence_break` falls within the gate-0080 sign-off, as part of the
  authorised retune (D1 widened by D11). AC16's second correction pins the
  allowed difference exactly, line by line as measured at claim. Any other
  difference still fails it.
- **Settled (2026-10-06; source: maintainer ruling, 2026-10-06, in the
  item-217 claim session): `case.sequence.order[]` is counted** in AC10's
  and AC11's comparison set. It is a stored path that the signed note's
  Deviation 11 places in the structure. It has no table row only because it
  has no old path. This confirms the claim-time reading (A9's re-check).
