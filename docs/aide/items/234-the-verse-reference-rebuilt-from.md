<!-- aide-template: item 3 -->
# Item 234 — The VerSe reference rebuilt from the development role only

> **Created:** 2026-10-18 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 35 — Programme Interface: the SegFACET Side
> **Queue:** [`../queue/queue-031.md`](../queue/queue-031.md) · Item 234
> **Objectives:** G3, G7
> **Suggested branch:** `aide/234-the-verse-reference-rebuilt-from`

---

## Description

Stage 35's fifth deliverable. The bundled production reference
`src/segfacet/reference/reference_verse_v1.json` is today built from the 80
VerSe19 training-split cases only. Its Stage-3-derived statistics were fitted
in ascending-integer order, so they are stale for any subject whose integer and
anatomical orders disagree, such as one carrying T13 (insight
`2026-10-06-f318`). `spine-failure-lab`'s `docs/project/facet-interface.md`
(adopted at `7436b0f`) splits every cohort into `development`, `calibration`
and `test` roles, and only the `development` role may build a reference.

This item delivers:

- **A development-role rebuild tool.** `scripts/rebuild_verse_reference.py`
  stops discovering masks by a recursive glob under one root and staging them.
  It resolves the `development` subset of the bundled `verse19.yaml` and
  `verse20.yaml` descriptors (item 229) against two release roots. It refuses
  to build when any development case also resolves in a `calibration` or
  `test` role.
- **A record of the cases that built it.** The artifact's `provenance` carries
  a sorted `case_ids` list.
- **The `gate-fac1` exclusion.** The `spline_offset_mm` reading of
  `sub-verse406_split-verse261` T10 (label 17) is withheld from the reference
  before aggregation. That label is a rare wedge vertebra, and its 18.51 mm
  offset is an anatomical outlier (owner decision 2026-10-16).
- **The rebuilt artifact**, committed in place under its existing name, from
  141 development cases: 80 VerSe19 training and 61 VerSe20 training.
- **`spline_offset.max_offset_mm` re-derived** from the rebuilt artifact with
  the unchanged item-123 rule (`derive_max_offset_mm`). At spec time it
  measures **8.0 mm**, down from 13.0 mm (Assumption A9). The re-derivation
  covers **interior** readings only, the readings the reference holds. A
  terminal vertebra keeps item 222's calibrated 13.0 mm, now as its own
  parameter, `max_terminal_offset_mm` (Assumption A10).
- **Two enabling fixes.** `verse19.yaml` resolves a split subject's CT, so
  the 25 VerSe19 split cases keep their intensity statistics (A8). The tool
  can ingest cases in parallel (`--jobs`). A serial rebuild takes about 19
  CPU-hours (A14).
- **The downstream moves.** That means the regenerated catalogue, rule table
  and failure-mode rendering, the reconciled tests, and the re-measured
  default-reference CLI firing on the corpus.

**Not in scope.** No change to `derive_max_offset_mm`'s rule. No change to
the `segfacet build-reference` CLI. No MSKGSTT reference, and no rename to
`reference_verse_v2.json` (A7). No re-measurement of terminal readings against
a new threshold, because the terminal threshold does not move. No calibration-
or test-role measurement of the new interior threshold; that is Stage 16's.

## Acceptance Criteria

- [ ] **AC1: A descriptor role mix-up is refused with every overlapping case
  named.** The tool's `development_cohort(sources)` is given one in-memory
  `DatasetDescriptor` whose `development` and `calibration` subsets are both
  `{"root": "split-a"}`, over a stand-in root whose `split-a` holds two cases.
  It raises `RoleOverlapError`, and the message contains both case ids.
- [ ] **AC2: A rebuild whose inputs mix roles writes no artifact.** A
  stand-in VerSe19 root holds the same case id under both
  `dataset-verse19training` and `dataset-verse19validation`, beside a valid
  stand-in VerSe20 root. `main(["--out", <out>, "--verse-cohort", <v19>,
  "--verse20-cohort", <v20>])` returns `1`, and `<out>/reference_verse_v1.json`
  does not exist.
- [ ] **AC3: The rebuilt artifact records exactly the development cases.**
  Stand-in roots hold two development, one calibration and one test case per
  release. After `main` over both roots, `load_artifact(<out>/reference_verse_v1.json).provenance.case_ids`
  equals the sorted tuple of the four development case ids.
- [ ] **AC4: The excluded label contributes no offset.** Stand-in VerSe19
  development cases `A`, `B` and `sub-verse406_split-verse261` each have an
  interior T10, with levels `("T9", "T10", "T11", "T12", "L1")`. Run 1 builds
  over all three cases. Run 2 builds over `A` and `B` only. Run 1's T10
  `spline_offset_mm` `FeatureStats` equals run 2's, and run 1's `calibration.excluded_offsets` lists
  exactly `{"case_id": "sub-verse406_split-verse261", "level_name": "T10"}`
  with its measured `offset_mm`.
- [ ] **AC5: A rebuild from the same inputs is byte-identical.** Two `main`
  runs over the same stand-in roots into two output directories write
  `reference_verse_v1.json` files with equal bytes.
- [ ] **AC6: A missing release root builds nothing.** With
  `SEGFACET_VERSE20_COHORT` unset and no `--verse20-cohort`, `main` given a
  valid stand-in `--verse-cohort` returns `0`. It writes a summary whose
  `cohort.status` is `"skipped"` and whose `cohort.reason` names
  `SEGFACET_VERSE20_COHORT`. It writes no `reference_verse_v1.json`.
- [ ] **AC7: A VerSe19 split case resolves its own CT.** In a stand-in VerSe19
  root, `dataset-verse19training` holds
  `derivatives/sub-verse900/sub-verse900_split-verse901_seg-vert_msk.nii.gz`
  and `rawdata/sub-verse900/sub-verse900_split-verse901_ct.nii.gz`. For case
  `sub-verse900_split-verse901`,
  `resolve(load_descriptor(bundled_descriptor_path("verse19.yaml")), data_root=<root>, subset="development")`
  gives a `scan_path` equal to `str(<that CT>.resolve())`.
- [ ] **AC8: A terminal vertebra is judged against its own threshold.** A
  record holds one terminal entry (`is_terminal: True`) with
  `terminal_offset_mm` 10.0. Under `bundled_default_config()`,
  `SplineOffsetRule().evaluate` returns no finding for it.
- [ ] **AC9: The committed artifact lists the development roles of both
  releases.** The committed artifact's `provenance.case_ids` equals the sorted
  union of `resolve(..., subset="development").case_ids` over `verse19.yaml`
  at `SEGFACET_VERSE_COHORT` and `verse20.yaml` at `SEGFACET_VERSE20_COHORT`.
  The test is gated on both variables naming three-split roots, and it skips
  cleanly otherwise. *(closes Stage 35 criterion 4)*
- [ ] **AC10: No committed case is a calibration or test case of either
  release.** The test has the same gate as AC9. The committed
  `provenance.case_ids` is disjoint from the union of the `calibration` and
  `test` case ids of both descriptors.
- [ ] **AC11: The committed artifact holds no offset from the excluded
  label.** The test is gated on `SEGFACET_VERSE_COHORT`. It reads the
  `spline_offset_mm` of `sub-verse406_split-verse261`'s T10 live, by ingesting
  that one development case with `segfacet.reference.ingest.ingest_dataset_cohort`.
  The committed artifact's T10 `spline_offset_mm` `max` is strictly less than
  that reading. *(closes Stage 35 criterion 5)*
- [ ] **AC12: The shipped interior threshold is the one derived from the
  committed artifact.** `segfacet.heuristics.spline_offset._DEFAULT_MAX_OFFSET_MM`
  equals `derive_max_offset_mm(bundled_production_reference())`. This AC's test
  already exists and is not duplicated:
  `tests/test_123_recalibrate_and_regenerate.py::test_ac12_shipped_default_equals_derived_value_from_committed_artifact`.

Why each AC is here. AC1 and AC2 are the queue line's "a descriptor role
mix-up that puts a calibration case in its inputs fails the build". AC1
covers the guard's semantics. AC2 covers the build actually failing, since a
caught error that let the build continue would pass AC1. AC3 is "the rebuilt
artefact lists only development-role case ids". It is an equality, so a
dropped development case fails it too. AC4 is "the excluded label
contributes no offset to the threshold derivation", run through the tool's
own path. `derive_max_offset_mm` reads the distribution, and the distribution
never holds the offset. AC5 is "a rebuild from the same inputs is
byte-identical". AC6 guards the one failure the two-root design adds: a
VerSe19-only artifact written silently when the VerSe20 root is not
configured. AC7 keeps intensity statistics for the 25 VerSe19 split cases
(A8). AC8 keeps item 222's terminal calibration in force while the interior
threshold moves (A10). With one shared parameter, `clean_control`'s terminal
L5 (8.513 mm) would fire.

AC9–AC11 measure the committed file against the real releases, which is what
the stage criteria are about. A stand-in proves the tool, and only the real
data proves the committed artifact. AC9 closes criterion 4's "draws only on
development-role cases". Its second half, "no calibration-role or test-role
case contributes", is AC10 across releases, together with item 229's AC6 and
AC7 within each release. AC11 closes criterion 5's "the excluded wedge-vertebra label
contributes nothing". This holds because that reading (18.51 mm) is above
every other development T10 reading (A11). AC12 is criterion 5's "re-derived
from the rebuilt distribution". Item 235 attests criterion 5 against AC11
and AC12 together.

## Assumptions

- **A1:** Item 229's interface, read on the base branch at `985ee0d0`
  (2026-10-18; the item has merged, so this is a reading, not a pin).
  `verse19.yaml` and `verse20.yaml` each carry `development`, `calibration`
  and `test` subsets as `{"root": <split dir>}`. A three-split root is the
  directory that holds the split directories. Resolution is
  `segfacet.datasets.resolve(load_descriptor(bundled_descriptor_path(name)), data_root=<root>, subset=<role>)`.
  Measured on the project host at spec time: VerSe19 80 / 40 / 40 cases,
  VerSe20 61 / 80 / 73 cases (development / calibration / test). VerSe20 was
  presented under its release split names by symlinks, since the local copy
  names them `01_training` / `02_validation` / `03_test` (item 229 A1).
- **A2:** The tool's cohort half is rewritten, not extended. Recursive
  discovery plus staging (`discover_masks`, `stage_cohort`, `_link_or_copy`,
  `_subject_id_for_mask`, the `staging` summary block, `--staging-dir` and
  `--seg-suffix`) exists because `ingest_cohort` was flat. The Stage-13
  resolver removed that need. Kept alongside the descriptor path, it
  would also still mix roles. Set `SEGFACET_VERSE_COHORT` to a three-split
  root, as tests 088, 091, 229 and 240 expect, and it ingests all 160 VerSe19
  masks, calibration and test included. That is the exact defect this item guards
  against (see also insight `2026-10-17-e94a`). The constants
  `VERSE_SEG_SUFFIX` and `VERSE_CT_SUFFIX` stay, because
  `tests/test_133_tptbox_pin_and_verse_retirement.py` builds its stand-in from them.
  `derive_max_offset_mm`, `_p99_by_level`, `_calibration_block` and
  `_terminal_interior_counts` stay, because tests 123, 129 and 221 call them.
- **A3:** Root resolution per release: the CLI flag, else the environment
  variable, else unresolved. VerSe19 uses `--verse-cohort` /
  `SEGFACET_VERSE_COHORT`. VerSe20 uses the new `--verse20-cohort` /
  `SEGFACET_VERSE20_COHORT`. Each names a three-split root, as for tests 229
  and 240. **Both** roots are required. With either unresolved, missing, or
  resolving an empty development role, the run is a structured skip: exit
  `0`, summary written, no artifact. A one-release build would not be the
  reference the stage describes.
- **A4:** `development_cohort(sources)` takes a sequence of
  `(DatasetDescriptor, data_root)` pairs. For every pair it resolves the
  `development`, `calibration` and `test` subsets. It collects every
  development case id that appears in any pair's calibration or test cohort,
  and raises `RoleOverlapError` (a `ValueError` subclass defined in the tool)
  naming all of them, sorted. A development case id resolved by two
  sources is the same error, because a cross-release duplicate cannot be a
  single case. Otherwise it returns one `segfacet.datasets.Cohort` of the
  merged development cases, sorted by case id. `run_rebuild` lets the error
  propagate. `main` catches it, prints `Error: <message>` to stderr, writes the
  summary with `cohort.status == "error"`, and returns `1`.
- **A5:** The case list is `Provenance.case_ids: Optional[Tuple[str, ...]] = None`
  in `src/segfacet/reference/schema.py`. `to_dict` emits the key only when
  it is not `None`, and `from_dict` reads it when present. So
  `reference_default.json` and every other artifact keep their bytes, and
  `schema_version` stays `"1.2"`. The key is additive. `from_dict` already
  ignores unknown provenance keys, so an older reader still loads the new
  file. No test pins the exact provenance key set (sweep 2026-10-18). Only the
  tool sets it. `build_reference` / `build_reference_from_cohort` and the CLI
  are unchanged.
- **A6:** The exclusion is the tool constant
  `EXCLUDED_OFFSETS = frozenset({("sub-verse406_split-verse261", "T10")})`,
  keyed by case id and level name. T10 is label 17 under
  `LabelConvention.default()`. Before `aggregate_reference`, the tool drops the
  `spline_offset_mm` key from each matching `FeatureRecord`, and the case's
  other features and levels stay. Each drop is listed in the summary's
  `calibration.excluded_offsets` as `{case_id, level_name, offset_mm}`. The
  reading is removed from the distribution itself, not only from the
  derivation. The derivation reads the committed artifact (AC12), and
  `reference_delta` then judges cases against a distribution without the
  outlier, which is what "to be ignored" (gate-fac1) asks. The rule still
  judges that label in a run: the exclusion is from the population, not from
  the detector.
- **A7:** The file stays `reference_verse_v1.json` with
  `provenance.source == "verse-v1"`, rebuilt in place as item 123 did.
  `PRODUCTION_ARTIFACT_NAME`, the CLI default, `reference.artifact_path`
  configs, `committed_artifact_guard.ALLOWLIST` and the test_128 pin all name
  that file. `provenance.case_ids` now carries the build's identity, which a
  version number in the filename only implied. `docs/reference-build.md`'s
  "increment N on each new real build" policy line is reworded to say an
  in-place rebuild records its cohort in `provenance.case_ids`.
- **A8:** `verse19.yaml`'s case-id regex gains a `sub` group,
  `(?P<id>(?P<sub>sub-verse\d+)(?:_split-verse\d+)?)_seg-vert_msk\.nii\.gz$`,
  and its scan template becomes `rawdata/{sub}/{id}_ct.nii.gz`. A split
  subject's CT lives under its parent's `rawdata/` directory, for example
  `rawdata/sub-verse406/sub-verse406_split-verse261_ct.nii.gz`. Under today's
  `rawdata/{id}/{id}_ct.nii.gz` it resolves `None`, which would drop intensity
  statistics for 25 of the 80 VerSe19 training cases. That is the undercount
  `docs/reference-build.md`'s item-123 record already called out. On the
  host, the training split holds 80 masks and 80 CTs. Case ids do not change.
  `tests/test_088_stage13_acceptance.py::test_standin_resolve_subsets_and_triples`
  still sees `scan_path is None` for its split case, which has no CT file.
  `verse20.yaml` needs no change (no split infix in the release, item 229 A4).
- **A9:** The spec-time measurement, a probe at `985ee0d0`, 2026-10-18. It
  ingested geometry only from the 141 development cases with the bundled
  config (`segfacet.reference.ingest.ingest_subject`), then ran
  `aggregate_reference` and `derive_max_offset_mm`.
  - **Threshold.** P = 7.915787852893431 mm at L4 (count 106), so
    `derive_max_offset_mm` gives **8.0 mm**, with or without the exclusion.
  - **What the exclusion moves.** It moves T10's p99 from 7.388 mm (count 73)
    to 2.977 mm (count 72), and it does not move P.
  - **Why 13.0 mm was set.** The 37-value VerSe19 T10 sample let the 18.51 mm
    reading set its p99 to 12.906 mm. With the outlier excluded and the
    cohort doubled, the derivation falls to the bulk.
  - **Interior development readings at or above 8.0 mm.** Four: verse406 T10
    18.510 (already firing at 13.0), `sub-verse111` L4 8.848, `sub-verse586`
    L5 8.143 and `sub-verse107` L4 8.033.
  - **Corpus window.** 8.0 mm lies inside it. It is above every non-firing
    interior corpus reading: `displace`'s neighbours 6.919 (label 21) and
    6.562 (label 23), and `relabel_swap`'s 5.624555 (label 23). It is at or
    below `displace`'s firing 14.615923 (label 22).
  - **The rule the builder applies.** Apply the re-derived value only if it
    lies in that window. Outside it, set nothing, record the measurement in
    Decisions, and hand back, as item 123 did on 2026-08-29.
  - **Owner decision, 2026-10-18.** The owner reviewed this spec and accepted
    the threshold result as specced: interior `spline_offset` 8.0 mm, derived
    from the development role. The window rule above still binds the builder.
    The decision accepts the spec-time value, and a rebuild that lands outside
    the window is still a hand-back.
  - **Correction, 2026-10-18 (validation round 1, owner decision).** The
    corpus window above was taken from the corpus cases only. Validation
    round 1 found two operator-default fixtures outside the corpus where
    8.0 mm also fires on the interior neighbour label 21 (L2): 8.528 mm in
    `CropAtBorderPerturbation(target_label=22, face="anterior")` over
    `_clean()` (`tests/test_038_coverage_border_overlap_perturbations.py`),
    and 8.368 mm in `DisplacePerturbation(target_label=22)` at its 18 mm
    default (`tests/test_039_identity_ordering_alignment_perturbations.py`).
    The corpus `displace` case's label 21 still reads 6.919 mm, and no corpus
    firing set changes. The owner kept 8.0 mm and accepted both label-21
    `spline_offset` findings as real behaviour. The window now covers the
    operator-default fixtures as well, with these two neighbour findings
    accepted inside it. The tests that pinned their absence are reconciled
    (Testing Strategy).
- **A10:** The re-derivation is from the interior distribution; the
  reference excludes terminal readings (`reference/ingest.py`, item 123). So
  it moves `max_offset_mm` for **interior** entries only. A terminal entry is
  judged against a new parameter, `rules.spline_offset.params.max_terminal_offset_mm`,
  with code default `_DEFAULT_MAX_TERMINAL_OFFSET_MM = 13.0`. That is the
  value item 222 calibrated terminals at: 150 VerSe19 terminals and 0 false
  positives, measured 2026-10-14. Two reasons:
  - **Nothing derives a terminal threshold.** The derivation never sees a
    terminal reading.
  - **One shared value breaks the corpus.** At 8.0 mm it fires on the corpus
    terminals `clean_control` L5 8.513, `fragment` 8.507, `inject_islands`
    8.536, `crop_at_border` 8.608, `displace` L5 11.153 and `relabel_swap`
    L5 11.153 mm (measured 2026-10-18 through `extract_feature_record`).
    That would break the clean control's pass and four cases' expected firing
    sets.

  The terminal finding's reason text keeps its `threshold 13.0 mm` clause. The
  rule's declared `params` gains `("max_terminal_offset_mm", 13.0)`.

  **Owner decision, 2026-10-18.** The owner accepted this as specced:
  terminals stay at 13.0 mm under the new `max_terminal_offset_mm`, and
  interior entries take the derived 8.0 mm (A9).
- **A11:** AC11's inequality proves the exclusion only because the
  verse406 T10 reading is the largest development T10 reading. At spec time
  it is 18.510 mm, and no other T10 reading reaches the top 20 development
  interior readings (all ≥ 4.549 mm). If a later estimator change reorders
  this, AC11 must be re-derived, not loosened.
- **A12:** The two unread `mislabel` keys `max_offset_mm` and
  `flag_offset_outliers` are removed from `default_config.yaml`. Their
  comment defers removal "to that rebuild", meaning this one. Left in place,
  the 13.0 would contradict the shipped 8.0, and tests 035 and 123 pin it
  equal to the code default. Removing them moves `config_hash`. So the
  config edit goes **first**, then `reference_default.json` is regenerated
  (`python -m segfacet.reference.artifact`), and then the real rebuild runs,
  so both artifacts carry the new hash. The threshold itself lives in code,
  and comments are not hashed, so applying 8.0 afterwards moves nothing
  further.
- **A13:** The rebuilt artifact gains level `T13`, from 2 VerSe20 cases, so
  it has 26 levels: C1–C7, T1–T13, L1–L6. VerSe20 training contributes L6 in
  13 cases. VerSe20 training holds no S1, Cocc or S2 label (label census of
  the 61 masks, 2026-10-18). `subject_count` becomes 141.
- **A14:** Cost. The probe used 24 worker processes and took about 19
  CPU-hours, and the slowest single case took over 90 minutes. The tool
  gains `--jobs N` (default 1): `ingest_dataset_cohort` gains `jobs: int = 1`
  and, above 1, maps a module-level worker over the cases with
  `concurrent.futures.ProcessPoolExecutor`, keeping case order. The worker
  is module-level in `segfacet.reference.ingest`, so a spawn-start platform
  (Windows) can import it. The tool's own module is path-loaded, so its
  functions cannot be pickled. No dependency is added.
- **A15:** No Environment-Gated Capability Verification row is added. VerSe
  ground truth falls under the existing "Real VerSe GT reference
  distributions" row (item 229 A7), and AC9–AC11 are real-data checks of it.
  No `[validation]` profile is added; `aide.toml` is a process file.

## Implementation Steps

1. **Config first (A12).** In `src/segfacet/default_config.yaml`, delete
   `rules.mislabel.params.max_offset_mm` and `flag_offset_outliers` and the
   block comment's deferral sentences. In the commented `spline_offset`
   documentation block, write `max_offset_mm` as the re-derived value with a
   one-line provenance ("item 234, development-role VerSe19+VerSe20
   reference") and add `max_terminal_offset_mm: 13.0` ("item 222's terminal
   calibration"). Regenerate `src/segfacet/reference/reference_default.json`
   with `.venv/bin/python -m segfacet.reference.artifact`.
2. **`src/segfacet/reference/schema.py` (A5).** Add the optional
   `Provenance.case_ids` field. `to_dict` emits `"case_ids": list(...)` only
   when not `None`, and `from_dict` reads it when present, as a tuple of
   `str`.
3. **`src/segfacet/reference/ingest.py` (A14).** Add `jobs: int = 1` to
   `ingest_dataset_cohort`, with a module-level per-case worker that calls the
   existing `ingest_subject`. `jobs == 1` keeps the current sequential loop
   unchanged.
4. **`src/segfacet/datasets/verse19.yaml` (A8).** Change the `case_id` regex
   and `scan` template, and the header comment's split-subject sentence.
5. **`scripts/rebuild_verse_reference.py` (A2–A4, A6).**
   - Replace discovery and staging with `development_cohort(sources)` over
     the two bundled descriptors.
   - Keep `run_rebuild(*, out_dir, verse_cohort=None, verse20_cohort=None,
     build_date=..., max_cases=None, jobs=1)`. `max_cases` truncates the merged
     development cohort in id order, for smoke runs only.
   - Ingest with `ingest_dataset_cohort(cohort, config=bundled_default_config(),
     with_size_proxy=False, with_intensity=True, with_morphology=True, jobs=jobs)`.
   - Drop the `EXCLUDED_OFFSETS` readings, then `aggregate_reference` with
     `Provenance(source="verse-v1", ..., case_ids=cohort.case_ids)`.
   - `write_artifact`, then `derive_max_offset_mm`.
   - Summary blocks:
     - `cohort`: `status`, `reason`, `roots` `{"verse19", "verse20"}`,
       `role_counts` per release and role, `case_ids`, and
       `subjects_without_scan` (development case ids whose `scan_path` is
       `None`).
     - `build`: unchanged keys.
     - `calibration`: the existing block plus `excluded_offsets`. Its
       interior statistics are computed after the exclusion.
   - CLI: `--verse-cohort`, `--verse20-cohort`, `--out`, `--build-date`,
     `--max-cases`, `--jobs`. Exit `0` on a run or a skip, `1` on
     `RoleOverlapError`. Rewrite the module docstring.
6. **Rebuild against the real data.** Use
   `.venv/bin/python scripts/rebuild_verse_reference.py --out <scratch> --verse-cohort <VerSe19 root> --verse20-cohort <VerSe20 three-split root> --build-date <the build day> --jobs <n>`.
   A VerSe20 copy with renamed splits is presented through a scratch
   directory of symlinks named `dataset-01training`, `dataset-02validation`
   and `dataset-03test`. Copy `<scratch>/reference_verse_v1.json` over
   `src/segfacet/reference/reference_verse_v1.json`. Keep the summary for the
   rebuild record.
7. **Threshold (A9, A10).** Read P and the derived value from the
   **committed** artifact (`_p99_by_level`, `derive_max_offset_mm`), and
   check the A9 window.
   - In `src/segfacet/heuristics/spline_offset.py`, set
     `_DEFAULT_MAX_OFFSET_MM` to the derived value. Add
     `_DEFAULT_MAX_TERMINAL_OFFSET_MM = 13.0`, read from
     `rules.spline_offset.params.max_terminal_offset_mm`, and use it for
     terminal entries in `_detect_offset_outliers`.
   - Add the parameter to the declared `params`.
   - Rewrite the docstring's "Threshold calibration" section with the
     141-case measurement and the exclusion. Its "Corpus margins" section
     keeps the literals `5.624555`, `0.226480` and `14.615923`, which
     `tests/test_123_recalibrate_and_regenerate.py::test_ac16_docstring_records_the_margins_and_the_artifact_name`
     reads, and adds `displace`'s 6.919 mm neighbour. Its "Terminal
     calibration" section names `max_terminal_offset_mm`.
8. **Prose that states the shipped interior threshold.** In
   `src/segfacet/failure_modes.py`, three passages say "13.0 mm threshold"
   and one says "1.62 mm above". Recompute the margin from 14.615923. In
   `src/segfacet/synth/identity_ordering_alignment.py`, update the "13.0 mm
   since" comment. In `src/segfacet/reference/artifact.py`, change
   `bundled_production_reference_path`'s "VerSe19 training-split subjects"
   docstring to the development roles of both releases. Dated records
   (`docs/spinal-curve-model.md`, earlier rebuild records, item specs) are
   history and stay.
9. **Regenerate** with `.venv/bin/python -m segfacet.catalogue`,
   `.venv/bin/python -m segfacet.rule_table` and
   `.venv/bin/python -m segfacet.failure_modes`. Then confirm with
   `git status` that only the generated files listed under Authorised paths
   moved. `python -m segfacet.traceability`, `segfacet.golden_evidence` and
   `segfacet.synth.corpus` read no reference and no threshold the corpus
   crosses, so they must move nothing. Run them and confirm.
10. **Documents.**
    - **`docs/reference-build.md`.** Add a dated "Rebuild record — <date>
      (item 234, development role)" section. Record:
      - the tool command and the cohort counts;
      - P, its level and count, and the derived threshold, read from the
        committed artifact;
      - the exclusion and its offset;
      - the four interior development readings at or above the threshold;
      - the role-overlap check passing;
      - `subjects_without_scan`;
      - the intensity coverage (each level's `intensity_mean` count against
        its `record_count`);
      - the run's wall time and `--jobs`.

      Update the "Staging the cohort" section and the storage policy line
      (A7) for the descriptor-driven tool. Keep the strings
      `scripts/rebuild_verse_reference.py`, `SEGFACET_VERSE_COHORT`,
      `--verse-cohort` and `80`, which test_123 AC31 and AC32 read. Leave the
      item-221 record unchanged.
    - **`docs/aide/dataset-verse19.md`.** Rewrite the reproduce paragraph:
      the root is the directory holding the three split directories, and the
      nested-wrapper layout is no longer supported. Keep the words
      `SEGFACET_VERSE_COHORT` and "recursive" (the descriptor's
      `derivatives/sub-*/**` glob), which test_123 AC30 reads.
    - **`CLAUDE.md`, the item-090 gotcha.** It claims "~40
      `bounds`/`reference_delta` findings". Replace it with the measurement
      from Validation step 2. At spec time it was already 55.

      **Correction, 2026-10-18 (owner decision):** this bullet is withdrawn.
      This item does not edit `CLAUDE.md`. The stale count is recorded in
      `docs/aide/insights.md` (provenance item 234) and will be fixed in a
      separate reviewed edit after this item merges.
11. **The integrity pin.** Set the new sha256 in
    `tests/test_128_reference_verse_v1_integrity.py`'s
    `_RELEASED_REFERENCE_VERSE_V1_SHA256` (test-writer, below). Every other
    digest check imports that constant, except
    `tests/test_128_relocation_checks.py`'s `_RELEASED_DIGEST`.

## Authorised paths

**May change:**

- `scripts/rebuild_verse_reference.py` — the development-role rebuild tool
- `src/segfacet/reference/schema.py` — `Provenance.case_ids`
- `src/segfacet/reference/ingest.py` — `ingest_dataset_cohort(jobs=...)`
- `src/segfacet/reference/artifact.py` — production-reference docstring
- `src/segfacet/reference/reference_verse_v1.json` — the rebuilt artifact
- `src/segfacet/reference/reference_default.json` — regenerated for the new `config_hash` (A12)
- `src/segfacet/datasets/verse19.yaml` — split-subject CT resolution (A8)
- `src/segfacet/heuristics/spline_offset.py` — re-derived interior threshold, terminal parameter, calibration docstring
- `src/segfacet/default_config.yaml` — unread mislabel keys removed, documentation block (A12)
- `src/segfacet/failure_modes.py` — prose naming the interior threshold
- `src/segfacet/synth/identity_ordering_alignment.py` — comment naming the interior threshold
- `docs/aide/feature_catalogue.generated.json` — regenerated observed reference ranges
- `docs/aide/feature_catalogue.generated.md` — regenerated observed reference ranges
- `docs/aide/rules.generated.md` — regenerated rule parameters
- `docs/aide/failure_modes.generated.json` — regenerated from `failure_modes.py`
- `docs/aide/failure_modes.generated.md` — regenerated from `failure_modes.py`
- `docs/reference-build.md` — rebuild record, tool recipe, storage policy line
- `docs/aide/dataset-verse19.md` — the cohort-root contract for the tool
- `tests/test_234_development_role_reference.py` — this item's tests
- `tests/test_123_recalibrate_and_regenerate.py` — reconcile (Testing Strategy)
- `tests/test_128_reference_verse_v1_integrity.py` — new digest, docstring
- `tests/test_128_relocation_checks.py` — new digest literal
- `tests/test_035_default_config.py` — retire the unread-key test
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — reconcile AC32
- `tests/test_090_reference_derived_defaults.py` — level set and uncovered-level tests
- `tests/test_093_tptbox_label_convention.py` — retire the L6 byte-for-byte pin
- `tests/test_125_stage28_validation.py` — subject count
- `tests/test_221_withhold_every_outlier.py` — retire the dated-record pin
- `tests/test_039_identity_ordering_alignment_perturbations.py` — terminal judgement reads the terminal parameter
- `.github/workflows/ci.yml` — `jobs.test.env.WINDOWS_TESTS` gains the new module (it reads bytes, a `tests/test_213_windows_ci_subset.py` signal)
- `tests/test_038_coverage_border_overlap_perturbations.py` — reconcile `test_ac15_crop_at_border_leaves_other_present_labels_unflagged` only (A9 correction, 2026-10-18)
- `tests/test_148_per_path_mode_attribution.py` — reconcile the `spline_offset` entry of `test_ac17_threshold_constants_hold_pre_item_values` only (A9 correction, 2026-10-18)

**Asserts against:**

- `src/segfacet/datasets/verse20.yaml` — AC2, AC3, AC5, AC6, AC9 and AC10 resolve through it unchanged

**Correction, 2026-10-18 (owner decision):** `CLAUDE.md` is removed from
**May change**. As first written, that list had a bullet reading "`CLAUDE.md`
— the item-090 gotcha's measured finding count (Validation step 2)". The
bullet is taken out of the list, not struck through, because `aide scope`
reads every bullet in this section as a grant. This item does not edit
`CLAUDE.md`. Implementation Step 10's `CLAUDE.md` bullet and Validation step
2's `CLAUDE.md` instruction are withdrawn with it.

**Correction, 2026-10-18 (validation round 1, owner decision):** the last two
**May change** bullets, test_038 and test_148, are added for the A9
correction. Each is scoped to the one test it names. The existing test_039
grant also covers `test_ac5_displace_run_qc_surfaces_mislabel_finding`, on the
same correction. None of the three grants covers any other test in its module.

## Testing Strategy

New module `tests/test_234_development_role_reference.py`, one test per
AC1–AC11. AC12's test already exists (named in the AC). Load the tool the way
test_123 does (`importlib.util.spec_from_file_location`). Clear
`SEGFACET_VERSE_COHORT` and `SEGFACET_VERSE20_COHORT` with an autouse
`monkeypatch` fixture in every stand-in test.

**Stand-ins (AC1–AC7).**
- **Masks.** Write masks with `segfacet.synth.clean_gt.build_clean_spine`.
  Paint CTs with `segfacet.synth.intensity.paint_clean_scan`, so ingestion
  takes the intensity path the real build takes.
- **Layout.** Lay them out exactly as the bundled descriptors expect:
  `<root>/dataset-verse19{training,validation,test}/derivatives/<sub>/<id>_seg-vert_msk.nii.gz`
  and `rawdata/<sub>/<id>_ct.nii.gz`, and the VerSe20 equivalent under
  `dataset-01training` / `dataset-02validation` / `dataset-03test`.
- **Helper.** Copy one small stand-in helper into the module. Do not import
  one from another test module.
- **AC4.** Use the same spine parameters for `A` and `B` in both runs, and
  compare the T10 `FeatureStats` by `==` on the loaded artifacts. Both runs
  are in one session, so this is a determinism comparison.
- **AC5.** Compare `read_bytes()`. That makes the module a `read_bytes`
  signal for `tests/test_213_windows_ci_subset.py`, so list it in
  `.github/workflows/ci.yml`'s `WINDOWS_TESTS` in sorted position.

**Real data (AC9–AC11).**
- **Gate.** `skipif`-gate each test on a module-level helper that returns the
  root only when the variable names a directory holding all three split
  directories. Copy the shape of `tests/test_229_verse_role_subsets.py::_real_root`,
  and name the variable and the directories in the skip reason.
- **AC11.** Ingest with `with_intensity=False, with_morphology=False` to keep
  the test short.

Adversarial cases (the test-writer writes these and no others):

- **cross-release duplicate:** the same case id under VerSe19 and VerSe20
  development raises `RoleOverlapError`. It guards two masks merged into one
  reference subject.
- **test-role overlap:** a development case id also present in the `test`
  role, not `calibration`, raises. It guards a guard that checks calibration
  only.
- **excluded case at a non-excluded level:** in AC4's run 1, the
  verse406 case's T11 `spline_offset_mm` still reaches the T11 statistics
  (run 1's T11 count is run 2's plus one). It guards an exclusion that drops
  the whole case, or every level, instead of one reading.
- **parallel equals serial:** `--jobs 2` writes bytes equal to `--jobs 1`
  over the same stand-in. It guards result ordering under
  `ProcessPoolExecutor`.
- **terminal threshold read from its own section:** a config setting
  `rules.spline_offset.params.max_terminal_offset_mm: 9.0` makes AC8's 10.0 mm
  terminal fire, and the reason names `threshold 9.0 mm`. It guards a
  hard-coded 13.0.
- **interior still follows `max_offset_mm`:** under the bundled config an
  interior entry at 10.0 mm fires. It guards the split being applied to both
  branches.

**Existing tests to reconcile** (sweep of `tests/` 2026-10-18, run against the
rebuild's measured consequences: 141 subjects, +T13, VerSe20 L6, new digest,
`config_hash` moved, interior threshold 8.0, mislabel keys removed, the tool's
cohort half rewritten):

- **`tests/test_123_recalibrate_and_regenerate.py`.**
  - **Tool tests, reconciled to the two-root descriptor tool.**
    - The rewritten tests: AC1 (`test_ac1_*`), AC2 (`test_ac2_*`, two
      variables), AC3 (`test_ac3_*`), AC6, AC7 (`test_ac7_*`), AC8 (now
      `cohort.subjects_without_scan`), AC17 (`test_ac17_*`) and the
      run-driving adversarial tests: `test_adv_symlinked_cohort_root_is_discovered`,
      `test_adv_single_label_mask_does_not_crash`,
      `test_adv_exactly_four_level_mask_yields_zero_offsets_not_a_crash`,
      `test_adv_rerun_into_same_out_overwrites_cleanly`,
      `test_adv_out_dir_under_not_yet_existing_nested_parent_is_created`,
      `test_adv_empty_string_env_var_treated_as_unset`,
      `test_adv_env_var_restored_after_monkeypatch_teardown` and
      `test_adv_two_standin_runs_produce_equal_cohort_and_calibration_blocks`.
    - The shared helpers `_write_standin_subject` and `_build_standin_cohort`
      move to the split layout and gain a VerSe20 root.
    - The autouse fixture also clears `SEGFACET_VERSE20_COHORT`.
    - The module docstring's summary-shape block loses `staging`.
  - **Retired, because the staging behaviour they test is deleted:**
    `test_ac4_nested_and_flat_layouts_yield_same_case_list`,
    `test_ac5_staged_directory_is_flat_with_scan_siblings`,
    `test_ac5_subject_id_matches_ingest_cohorts_stem_rule` and
    `test_adv_subject_id_collision_after_suffix_stripping_is_recorded_not_overwritten`.
    The resolver raises on a duplicate id within one role, which test_086
    covers.
  - **Changed or retired outright.**
    - `test_ac19_artifact_identity_preserved`: `subject_count == 141`, and the
      level set gains `T13` (26 levels).
    - `test_ac13_config_yaml_agrees_with_code_default`: retire (the key is
      removed, A12).
    - `test_ac43_l5_below_qualifying_count_or_absent`: retire. L5 now has 16
      interior readings, and the test pinned item 123's 80-case consequence.
    - `test_ac44_default_max_offset_mm_is_thirteen`: retire. It is a literal
      duplicate of AC12, which carries the equality.
  - **Follow with no edit:** `test_ac12_*` (AC12 of this item),
    `test_ac14_*`, `test_ac15_*`, `test_ac16_*`, `test_ac20_*`,
    `test_ac21_*` (after step 1's regeneration), `test_ac30_*`–`test_ac32_*`
    (after step 10) and `test_ac33_*` (imports test_128's constant).
- `tests/test_035_default_config.py::test_ac3_max_offset_mm_matches_code_default`:
  retire (key removed, A12).
- `tests/test_129_coincident_centroids_and_held_out_floor.py::test_ac32_calibrated_max_offset_mm_unchanged`:
  delete the `== 13.0` literal and the `"max_offset_mm: 13.0" in config_text`
  assert, and keep the equality with `derive_max_offset_mm`. `test_ac30_*`
  and `test_ac20_*` follow (imported digest, regenerated catalogue).
- `tests/test_128_reference_verse_v1_integrity.py`: set the new digest in
  `_RELEASED_REFERENCE_VERSE_V1_SHA256`, and update the docstring's "built
  from mounted VerSe19 ground truth". Keep the module-level `_ARTIFACT` chain
  and the literal-compare shape that `tests/test_115_stage26_validation.py::test_ac8_no_hardcoded_literal_fence_remains`
  and `tests/test_128_relocation_checks.py` enforce.
  `test_reference_verse_v1_still_loads_and_scores_a_case` may break if
  `clean_control` label 22 stops drawing a `bounds` finding. Validation step
  2 shows whether it does. If it breaks, hand back rather than loosen it.
- `tests/test_128_relocation_checks.py`: set the same new digest in
  `_RELEASED_DIGEST`.
- `tests/test_090_reference_derived_defaults.py`:
  - `test_ac1_bundled_production_reference_is_verse_v1`: the 26-level set
    with `T13`.
  - `test_ac10_uncovered_level_falls_back_to_hand_set_and_fires`,
    `test_ac11_uncovered_level_falls_back_to_hand_set_index_threshold` and
    `test_ac11_uncovered_level_applies_hand_set_island_min_voxels_floor`
    used T13 (label 28) as the level the reference does not cover. Re-point
    them at a recognised level the rebuilt artifact does not cover, `S1`
    (label 26) or `Cocc` (27), chosen by reading the artifact's level set in
    the test. If that level's hand-set path differs, retire the test and say
    why in its place.
- `tests/test_093_tptbox_label_convention.py::test_ac5_l6_feature_stats_byte_for_byte_identical_to_pre_rename_s`:
  retire. It proved item 093's re-key-not-refit of the 80-case file, and
  VerSe20 now contributes L6 in 13 cases. Its siblings
  `test_ac5_fourteen_features_are_the_only_byte_for_byte_exclusions` and
  `test_ac5_no_other_level_or_top_level_field_changed` read the same
  snapshot. Reconcile or retire each one only if it goes red.
- `tests/test_125_stage28_validation.py::test_ac12_reference_verse_v1_subject_count_is_80`:
  141.
- `tests/test_221_withhold_every_outlier.py::test_ac7_reverified_verse19_ceiling_is_recorded`:
  retire. It pins the dated item-221 record's P against the live artifact,
  which this rebuild legitimately moves. That record is history and is not
  edited. The live P is AC12's to carry.
- `tests/test_039_identity_ordering_alignment_perturbations.py` (line ~183,
  the terminal branch): read `max_terminal_offset_mm` with default
  `_DEFAULT_MAX_TERMINAL_OFFSET_MM`, not `max_offset_mm` with a literal 13.0.
  It passes either way today, but it describes the wrong parameter.
- **Byte or tolerance comparisons of the regenerated catalogue, which follow
  step 9 with no edit:**
  - `tests/test_103_feature_catalogue.py::test_ac19_committed_docs_match_fresh_regeneration`;
  - `tests/test_106_stage19_validation.py` AC5–AC7;
  - the catalogue regeneration tests in modules 119, 120, 130, 132, 136,
    137, 146, 147 and 148;
  - `tests/test_123_recalibrate_and_regenerate.py::test_ac47_*`;
  - `tests/test_124_observed_range.py::test_ac17_committed_docs_match_fresh_regeneration`;
  - `tests/test_131_tangent_direction_normalisation.py::test_ac15_*`;
  - `tests/test_143_s_axis_correction.py::test_ac12_feature_catalogue_json_matches_committed`
    and `::test_ac15_*`.

  The `rules.generated.md` and `failure_modes.generated.*` drift tests
  likewise follow step 9.

**Correction, 2026-10-18 (validation round 1, owner decision; A9
correction).** The sweep above missed four tests, and these are added to it.
Each reconciliation keeps its test's original intent.

- `tests/test_038_coverage_border_overlap_perturbations.py::test_ac15_crop_at_border_leaves_other_present_labels_unflagged`:
  exempt exactly one finding from the `f.labels <= {22}` assertion, a
  `spline_offset` finding whose labels are `{21}`. Every other finding keeps
  the assertion. The test is about where the crop's own findings land
  (`border`, coverage), not about the spline threshold, so the test does not
  require the label-21 finding to be present. Say in the docstring that the
  exemption is the accepted label-21 reading of 8.528 mm at 8.0 mm (A9
  correction).
- `tests/test_039_identity_ordering_alignment_perturbations.py::test_ac5_displace_run_qc_surfaces_mislabel_finding`:
  the union of `spline_offset` finding labels becomes `== {21, 22}`, a
  measured equality, and `22` is still required. This test is about
  `spline_offset` itself, so the finding cannot be excluded. It is expected
  instead. Add a dated docstring line naming the accepted label-21 reading
  of 8.368 mm. AC6's `expected_labels == {22}` is the expectation record, and
  it does not change.
- `tests/test_148_per_path_mode_attribution.py::test_ac17_threshold_constants_hold_pre_item_values[spline_offset]`:
  the `spline_offset` entry of `_EXPECTED_THRESHOLD_CONSTANTS` takes
  `_DEFAULT_MAX_OFFSET_MM`'s new derived value of 8.0, with a dated comment
  naming item 234 in the style of the item-189 comments beside it. The other
  modules' entries do not change.
- `tests/test_234_development_role_reference.py`, the case-id parse that
  `tests/test_157_case_id_rename.py::test_ac11_no_real_module_parses_a_mode_out_of_a_case_id`
  flags: the stand-in helpers derive the subject directory with
  `case_id.split("_")[0]` (around lines 104 and 149). Pass the subject
  directory to the helper as its own argument, or keep the ids in a
  `(subject, case_id)` mapping, so nothing in the module subscripts or splits
  a case id. Do not rename the variable just to get past the scan. test_157
  is not edited.

## Validation

1. **The real rebuild (step 6).** Record its command, wall time and `--jobs`
   in `docs/reference-build.md`.
   - **Determinism.** On the same host, re-run the tool into a second
     scratch directory over the same roots. The two `reference_verse_v1.json`
     files must compare equal through
     `segfacet.synth.golden.assert_matches_committed_artifact`.
   - **Committed copy.** The committed copy must equal the first run's
     output byte for byte.
   - **Too slow for a second run.** If the host cannot spare a second full
     run, record the second comparison as not run, not as passed.
2. **The corpus through the default-reference CLI.** Run
   `segfacet run --scan <scan> --seg <seg> --out <dir>` with no reference
   flag over every case of `tests/corpus/manifest.json`. A case's scan is its
   `scan_fixture`, else `tests/corpus/fixtures/base_scan.nii.gz`. Record the
   verdict and the finding count by rule per case, against this baseline
   measured at `985ee0d0` on 2026-10-18:

   | case | verdict | findings (by rule) |
   |---|---|---|
   | clean_control | flagged-for-review | 55 (bounds 20, reference_delta 35) |
   | displace | flagged-for-review | 46 (bounds 16, reference_delta 29, spline_offset 1) |
   | fragment | flagged-for-review | 56 (bounds 20, fragmentation 1, reference_delta 35) |
   | inject_islands | flagged-for-review | 56 (bounds 20, fragmentation 1, reference_delta 35) |
   | relabel_swap | flagged-for-review | 55 (bounds 20, mislabel 1, reference_delta 34) |
   | remove_level | flagged-for-review | 46 (bounds 16, centroid_spacing 1, coverage 1, reference_delta 28) |
   | crop_at_border | flagged-for-review | 25 (border 3, bounds 8, reference_delta 14) |
   | sequence_break | flagged-for-review | 46 (bounds 16, mislabel 1, reference_delta 28, spline_offset 1) |
   | fuse_adjacent | flagged-for-review | 41 (bounds 14, centroid_spacing 1, reference_delta 26) |
   | remove_level_relabel | flagged-for-review | 45 (bounds 16, centroid_spacing 1, reference_delta 28) |
   | split | flagged-for-review | 52 (bounds 18, fragmentation 1, neighbour_contact 1, reference_delta 32) |
   | split_own_label | flagged-for-review | 54 (bounds 20, reference_delta 32, spline_offset 1, split_fragment 1) |
   | crop_fov_si | flagged-for-review | 43 (bounds 16, reference_delta 27) |
   | fuse_separate | flagged-for-review | 44 (bounds 15, centroid_spacing 1, fragmentation 1, reference_delta 27) |

   Put the clean-control figure into `CLAUDE.md`'s item-090 gotcha, and the
   table into the rebuild record. The `spline_offset` column must not change.
   Interior corpus readings all sit below 8.0 mm except `displace` label 22,
   and terminals stay at 13.0 mm (A9, A10). A change in that column is a
   hand-back, not a record.

   **Correction, 2026-10-18 (owner decision):** do not put the clean-control
   figure into `CLAUDE.md`. Record it in the rebuild record only. The update
   to `CLAUDE.md` is a separate reviewed edit (insight, provenance item 234).
3. **The gated tests.** Set `SEGFACET_VERSE_COHORT` to the VerSe19
   three-split root and `SEGFACET_VERSE20_COHORT` to the VerSe20 three-split
   root (release names, symlinked if renamed). Then run
   `.venv/bin/python -m pytest tests/test_234_development_role_reference.py tests/test_229_verse_role_subsets.py -ra`,
   and confirm that AC9–AC11 and item 229's AC5–AC7 ran and did not skip.
   - **Do not run the whole suite with the variables set.**
     `tests/test_088_stage13_acceptance.py::test_real_verse_clause_is_genuine_skip`
     fails whenever `SEGFACET_VERSE_COHORT` is set (insight
     `2026-10-18-62a6`). `tests/test_125_stage28_validation.py`'s AC10
     expects a training-only root (insight `2026-10-17-e94a`).
   - **The full suite** runs with both variables unset.
   - **No host with the data.** Record AC9–AC11 as skipped and unverified in
     Decisions, never as passed.

## Dependencies

- Item 229 — the `development` / `calibration` / `test` subsets of
  `verse19.yaml` and `verse20.yaml` this item resolves (merged).
- Item 221 — the held-out estimator that withholds every interior outlier,
  whose offsets the reference records (merged).
- Item 222 — the terminal reading and its 13.0 mm calibration, which
  `max_terminal_offset_mm` keeps (merged).

**Downstream:** item 235 replays AC9–AC11 and Validation steps 1–3, and
attests Stage 35 criteria 4 and 5.

## Decisions & Trade-offs

Code half implemented 2026-10-18. The real-data rebuild, the artifact commit,
the digests, the catalogue and rule-table regeneration, and the rebuild record
in `docs/reference-build.md` follow the rebuild.

- **Interior default set to the spec-time 8.0 mm ahead of the rebuild.**
  `_DEFAULT_MAX_OFFSET_MM = 8.0` and the calibration docstring carry A9's
  probe figures (P 7.916 mm at L4, count 106). The committed artifact still has
  to confirm it (`derive_max_offset_mm`) and the A9 window.
- **`ingest_dataset_cohort(jobs=...)` ships plain data to its workers.**
  `LabelConvention` holds `mappingproxy` maps and does not pickle, so the
  module-level worker `_ingest_case` receives the seg and scan paths, the case
  id and `dict(value_to_name)`, and rebuilds the convention with
  `LabelConvention.from_mapping`. `jobs == 1` keeps the sequential loop.
- **The tool's skip/error summaries share one shape** (`_empty_summary`): a
  role overlap writes `cohort.status == "error"` and the overlap message as
  `cohort.reason`.
- **Raw `build_date` default is `2026-10-18`** in the tool; the real rebuild
  passes `--build-date` explicitly.

- **Left open:** whether the interior threshold of 8.0 mm suits real segmenter output. The
  four development readings at or above it are anatomy, so on ground truth
  they are false positives of the `displaced_vertebra` condition. The
  calibration and test roles are unmeasured. Stage 16 measures it on SPINEPS
  output. This item applies the owner's derivation rule as decided
  (gate-fac1, roadmap Stage 35).
- **Left open:** whether terminals should get a derived threshold of their
  own. Item 222 calibrated 13.0 mm by measurement, and nothing in the
  reference holds terminal readings to derive one from.
- **Left open:** renaming to `reference_verse_v2.json`. The in-place rebuild
  keeps every consumer's selection key, and `provenance.case_ids` now
  identifies the build (A7).
- **Left open:** `verse19.yaml`'s absolute `data_root` (insight
  `2026-10-18-4313`). The tool passes both roots explicitly and does not
  read it.
