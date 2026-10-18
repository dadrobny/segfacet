<!-- aide-template: item 3 -->
# Item 229 — VerSe20 ground-truth descriptor and dataset-role subsets

> **Created:** 2026-10-18 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 35 — Programme Interface: the SegFACET Side
> **Queue:** [`../queue/queue-031.md`](../queue/queue-031.md) · Item 229
> **Objectives:** G7
> **Suggested branch:** `aide/229-verse20-ground-truth-descriptor-and`

---

## Description

Stage 35's second deliverable. `spine-failure-lab`'s
`docs/project/facet-interface.md` (adopted at `7436b0f`) splits every cohort
into three dataset roles: `development`, `calibration` and `test`. For VerSe
they are the training, validation and test splits of both releases
(the interface's "Dataset roles" table). FACET reads the roles as descriptor
`subsets` with those names. Today FACET has a VerSe19 descriptor only, and its
subsets carry the release's split names (`training`, `validation`, `test`).

This item delivers two things:

- **`src/segfacet/datasets/verse20.yaml`**, the VerSe20 ground-truth
  descriptor. Its `case_id` regex gives the same id the SPINEPS candidate
  masks carry. VerSe20 ground-truth masks are named
  `sub-<label>[_dir-<ax|iso|sag>]_seg-vert_msk.nii.gz`, with `<label>` either
  `verseNNN` or `glNNN`. The SPINEPS candidate for the same scan is
  `sub-<label>_mod-ct_seg-vert_msk.nii.gz`, with no `dir-` entity
  (`spine-failure-lab`'s `docs/project/data-layout.md`, "Artefacts"). So the
  case id is `sub-<label>`: the `dir-` entity is dropped, and a
  `_split-verseMMM` infix is kept wherever a mask has one. CTs resolve from
  `rawdata/<id>/`, with or without the `dir-` entity.
- **Role subsets on both descriptors.** `development`, `calibration` and
  `test` are directory-root subsets over each release's training, validation
  and test split directories. On `verse19.yaml` these names replace
  `training`, `validation` and `test`. No aliases are kept (Assumption A3).

**Not in scope.** No resolver code changes: `segfacet.datasets.resolve`
already handles a `root` subset, a `case_id` regex with optional groups, and a
globbed `scan` template. There is no candidate descriptor (the interface
assigns it to `spinelab`), no MSKGSTT descriptor, and no change to how
`segfacet evaluate` pairs a candidate cohort with a ground-truth cohort. The
reference rebuild from the `development` role is item 234.

## Acceptance Criteria

- [ ] **AC1: Each VerSe19 role subset resolves exactly its release split.**
  The test builds a stand-in VerSe19 root with distinct subjects under each of
  `dataset-verse19training`, `dataset-verse19validation` and
  `dataset-verse19test`, in the layout `verse19.yaml` expects. For each pair
  (`development`, training), (`calibration`, validation) and (`test`, test),
  `resolve(load_descriptor(bundled_descriptor_path("verse19.yaml")),
  data_root=<stand-in>, subset=<role>).case_ids` equals the sorted ids of the
  masks placed under that split directory.
- [ ] **AC2: Each VerSe20 role subset resolves exactly its release split.**
  The test builds a stand-in VerSe20 root with distinct subjects under each of
  `dataset-01training`, `dataset-02validation` and `dataset-03test`. For each
  pair (`development`, `dataset-01training`), (`calibration`,
  `dataset-02validation`) and (`test`, `dataset-03test`),
  `resolve(load_descriptor(bundled_descriptor_path("verse20.yaml")),
  data_root=<stand-in>, subset=<role>).case_ids` equals the sorted ids of the
  masks placed under that split directory.
- [ ] **AC3: A VerSe20 case id is the subject entity, with any split infix
  kept and the `dir-` entity dropped.** One stand-in VerSe20 split holds the
  masks
  `sub-verse500_dir-ax_seg-vert_msk.nii.gz`,
  `sub-verse501_dir-iso_seg-vert_msk.nii.gz`,
  `sub-verse502_dir-sag_seg-vert_msk.nii.gz`,
  `sub-verse503_seg-vert_msk.nii.gz`,
  `sub-gl004_dir-ax_seg-vert_msk.nii.gz` and
  `sub-verse504_split-verse600_dir-ax_seg-vert_msk.nii.gz`, each in its own
  `derivatives/<sub>/` directory. Resolving that split's role subset gives
  `case_ids` equal to `("sub-gl004", "sub-verse500", "sub-verse501",
  "sub-verse502", "sub-verse503", "sub-verse504_split-verse600")`.
- [ ] **AC4: A VerSe20 case resolves its CT with or without the `dir-`
  entity.** One stand-in VerSe20 split holds `sub-verse500`, whose CT is
  `rawdata/sub-verse500/sub-verse500_dir-ax_ct.nii.gz`, and `sub-verse503`,
  whose CT is `rawdata/sub-verse503/sub-verse503_ct.nii.gz`. Each resolved
  case's `scan_path` equals `str(<its CT path>.resolve())`.
- [ ] **AC5: On the real VerSe20 release, every ground-truth mask resolves to
  one case.** This test is gated on `SEGFACET_VERSE20_COHORT` naming a
  directory that holds all three VerSe20 split directories, and skips cleanly
  otherwise. The sum of `len(resolve(..., subset=<role>))` over the three
  roles equals the number of `*_seg-vert_msk.nii.gz` files that
  `Path.rglob` finds under the three split directories' `derivatives/`
  subtrees.
- [ ] **AC6: On the real VerSe20 release, no case id resolves in two roles.**
  This test has the same gate as AC5. The case-id sets of the three VerSe20
  role cohorts are pairwise disjoint.
- [ ] **AC7: On the real VerSe19 release, no case id resolves in two roles.**
  This test is gated on `SEGFACET_VERSE_COHORT` naming a directory that holds
  all three VerSe19 split directories, and skips cleanly otherwise. The
  case-id sets of the three VerSe19 role cohorts are pairwise disjoint.

Why each AC is here. AC1 and AC2 are the queue line's "each role subset of
each descriptor resolves the cases of its release split and no other". AC3 is
what lets `segfacet evaluate` pair a VerSe20 candidate with its ground truth
by id. AC4 keeps intensity features available to item 234's rebuilt
reference, since `reference_verse_v1.json` carries per-level intensity
statistics. AC5 is the queue line's "every VerSe20 ground-truth mask resolves
to one case id" against the real data: a regex that left a mask out, or
merged two masks into one id, changes the count. The resolver already raises
on a duplicate id within one role, so AC5 and AC6 together give one distinct
id per mask. AC6 and AC7 are the queue line's "no case resolves in two
roles". Item 234 relies on that when it asserts that no calibration or test
case built the reference. It is measured on the real releases because a
stand-in's disjointness is true by construction.

No AC carries a stage annotation. Stage 35 criterion 1 joins item 228's
list-form subsets with this item's role subsets, so neither item closes it
alone. Item 235 attests it against both items' tests.

## Assumptions

- **A1:** The VerSe20 split directories are named as the release distributes
  them: `dataset-01training`, `dataset-02validation` and `dataset-03test`.
  `spine-failure-lab`'s `spinelab.verse_adapter.RELEASE_LAYOUTS["verse20"]`
  declares the same three names. A local copy that was renamed is presented
  under these names through `--data-root`, for example with symlinks. It is
  not described in the committed descriptor.
- **A2:** `verse20.yaml`'s `data_root` is the relative placeholder `VerSe20`,
  not a machine path. The interface says a committed descriptor names no
  machine path. A descriptor resolved without `--data-root` from a directory
  that has no `VerSe20/` resolves an empty cohort, as `verse19.yaml` does
  when resolved with no subset. `verse19.yaml`'s absolute `data_root` is left
  unchanged (see Decisions & Trade-offs).
- **A3:** The VerSe19 subsets `training` and `validation` are renamed to
  `development` and `calibration`, with no aliases kept. `test` keeps its
  name. The old names are read only by `tests/test_088_stage13_acceptance.py`,
  by the gated `tests/test_091_stage14_acceptance.py::test_ac12_real_verse_recalibration_and_sensitivity_guard`
  and by `verse19.yaml`'s own header comment. No production code, script or
  user document passes `--subset training`. Two names for one directory would
  let a caller select the calibration split without naming its role, and the
  interface's point is that a role is named for what it is used for.
- **A4:** The VerSe20 `case_id` regex is
  `(?P<id>sub-[a-z]+\d+(?:_split-verse\d+)?)(?:_dir-[a-z]+)?_seg-vert_msk\.nii\.gz$`.
  It covers both subject families of the release (`verse`, `gl`). The
  release copy the programme uses holds 214 masks (61 training,
  80 validation, 73 test, measured 2026-10-18), all with distinct
  `sub-<label>` ids, and none with a `_split-verse` infix. The infix group is
  kept because the interface requires the infix to be kept wherever a
  release has one.
- **A5:** The VerSe20 `scan` template is `rawdata/{id}/{id}*_ct.nii.gz`.
  Because it contains a glob, `_resolve_scan` takes the first sorted match.
  Every VerSe20 `rawdata/<sub>/` directory of the release copy holds exactly
  one `*_ct.nii.gz` (measured 2026-10-18). A split-infixed id has no
  `rawdata/<id>/` directory and resolves `scan_path = None`, which is what
  `verse19.yaml` does for its split subjects.
- **A6:** The real-data gates are environment variables, matching the
  existing VerSe19 gate. `SEGFACET_VERSE_COHORT` (already used by tests 088,
  091 and 240) names the VerSe19 root. The new `SEGFACET_VERSE20_COHORT`
  names a directory holding the three VerSe20 split directories. Neither
  variable is committed anywhere with a value. No `[validation]` profile is
  added: `aide.toml` is a process file, and the existing gate works without
  one.
- **A7:** No Environment-Gated Capability Verification row is added. VerSe20
  ground truth falls under the existing "Real VerSe GT reference
  distributions" row (Package / Tool / Data: "VerSe ground-truth cohort
  (external dataset)"). AC5–AC7 are real-data checks of that same capability.

## Implementation Steps

No Python changes and no new dependency.

1. **`src/segfacet/datasets/verse19.yaml`.** Rename the subset keys:
   `training` becomes `development` and `validation` becomes `calibration`.
   `test` is unchanged, and each `root` value is unchanged. Update the header
   comment's usage line to `--subset development|calibration|test`, and add
   one line naming the three roles and pointing to `facet-interface.md`'s
   "Dataset roles" table.
2. **`src/segfacet/datasets/verse20.yaml` (new).** Model it on
   `verse19.yaml`. The header comment describes the release layout, the case
   id (the `dir-` entity is dropped so that the id equals the SPINEPS
   candidate's, and the split infix is kept) and the role mapping. Keys:
   `data_root: VerSe20` (A2);
   `seg: "derivatives/sub-*/**/*_seg-vert_msk.nii.gz"`; `case_id` as in A4,
   double-quoted with escaped backslashes as in `verse19.yaml`;
   `scan: "rawdata/{id}/{id}*_ct.nii.gz"` (A5); `label_convention: default`;
   `role: gt`; and `subsets` with `development: {root: dataset-01training}`,
   `calibration: {root: dataset-02validation}` and
   `test: {root: dataset-03test}`. Hatchling's wheel target already ships
   every file under `src/segfacet`, and `.gitattributes` already pins
   `src/segfacet/**/*.yaml` to LF, so neither file changes.
3. **Reconcile existing tests** (test-writer, listed under Testing Strategy).
   Rename `training` to `development` and `validation` to `calibration` where
   they name a `verse19.yaml` subset.

## Authorised paths

**May change:**

- `src/segfacet/datasets/verse20.yaml` — the new VerSe20 descriptor
- `src/segfacet/datasets/verse19.yaml` — role subsets replace split-named subsets
- `tests/test_229_verse_role_subsets.py` — this item's tests
- `tests/test_088_stage13_acceptance.py` — reconcile subset names (`training` → `development`, `validation` → `calibration`)
- `tests/test_091_stage14_acceptance.py` — reconcile the gated test's subset names
- `.github/workflows/ci.yml` — `jobs.test.env.WINDOWS_TESTS`, only if the new test module trips a `tests/test_213_windows_ci_subset.py` signal

**Asserts against:**

None.

## Testing Strategy

New module `tests/test_229_verse_role_subsets.py`, one test per AC.

- **AC1–AC4** build stand-in trees in `tmp_path` with empty files.
  `resolve` reads only the filesystem layout, never voxels. Copy the
  few-line `_touch` helper shape from `tests/test_086_datasets.py`, and do not
  import from another test module. Load the committed descriptors through
  `bundled_descriptor_path`, never a hand-built copy. Pass the stand-in root as
  `data_root`. For AC4, compare `scan_path` to `str(path.resolve())`. No
  `as_posix()` is needed. If the module ends up using `as_posix()` or another
  `test_213` signal, list it in `ci.yml`'s `WINDOWS_TESTS` in sorted position.
- **AC5–AC7** are each `skipif`-gated on a module-level helper that returns
  the root only when the environment variable is set and the directory holds
  all three split directories. `tests/test_240_verse19_probes.py::real_verse19_root`
  is the model: copy it, do not import it. The skip reason names the
  variable and the three directory names. In AC5, count masks with
  `Path.rglob("*_seg-vert_msk.nii.gz")` under each split's `derivatives/`.
  This is deliberately a different walk from the resolver's `glob.glob`, so
  the count is an independent measurement.

Adversarial cases are part of the AC tests and need no separate tests:

- AC3's `sub-verse504_split-verse600_dir-ax` mask guards a regex that drops
  the split infix together with the `dir-` entity. Such a regex would merge
  a split scan into its parent subject's id.
- AC3's `sub-gl004` mask guards a regex written for `sub-verse` only. Such a
  regex makes `resolve` raise "case_id regex did not match" on the release's
  `gl` subjects.
- AC4's two CT shapes guard a `scan` template that names one shape only.
  Such a template silently gives `scan_path = None`, and the case then
  contributes no intensity to item 234's reference.

**Existing tests to reconcile** (a sweep of `tests/` for the `verse19.yaml`
subset names, 2026-10-18):

- `tests/test_088_stage13_acceptance.py::test_committed_verse19_descriptor_shape`
  asserts `set(d.subsets) == {"training", "validation", "test"}` and
  `d.subsets["training"] == {"root": "dataset-verse19training"}`. Change these
  to `{"development", "calibration", "test"}` and `d.subsets["development"]`.
- `tests/test_088_stage13_acceptance.py::test_standin_resolve_subsets_and_triples`
  uses `subset="training"` and `subset="validation"`. Change them to
  `"development"` and `"calibration"`.
- `tests/test_088_stage13_acceptance.py::test_standin_build_reference_and_evaluate_cli`
  passes `--subset training` twice. Change it to `--subset development`.
- `tests/test_088_stage13_acceptance.py::test_real_verse_resolves_training_split`
  (gated) uses `subset="training"`. Change it to `"development"`.
- `tests/test_091_stage14_acceptance.py::test_ac12_real_verse_recalibration_and_sensitivity_guard`
  (gated) uses `subset="training"` and `subset="validation"`. Change them to
  `"development"` and `"calibration"`.

Tests that use the names `training` and `validation` in their own in-memory
or `tmp_path` descriptors are unaffected and stay unmodified: tests 086,
087 and 228. So does `tests/test_240_verse19_probes.py`, whose `_SPLITS`
names directories, not subsets.

## Validation

On a host that holds the VerSe releases, run the gated tests for real. Set
`SEGFACET_VERSE_COHORT` to the VerSe19 root and `SEGFACET_VERSE20_COHORT` to
a directory holding `dataset-01training`, `dataset-02validation` and
`dataset-03test`. Then run
`.venv/bin/python -m pytest tests/test_229_verse_role_subsets.py tests/test_088_stage13_acceptance.py -ra`
and confirm that AC5–AC7 and `test_real_verse_resolves_training_split` ran
and were not skipped. Also record the per-role VerSe20 case counts. On the
release copy measured for A4 they are 61 / 80 / 73. If no host holds the
data, record the gated tests as skipped and AC5–AC7 as unverified in the
item's Decisions log. Never record them as passed.

## Dependencies

None.

**Downstream:** item 234 reads the `development` subset of both descriptors
through `bundled_descriptor_path("verse19.yaml")` /
`bundled_descriptor_path("verse20.yaml")`, and the real VerSe20 data through
`SEGFACET_VERSE20_COHORT`. Item 235 replays this item's gated tests.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** how `segfacet evaluate` pairs a candidate-role cohort with a
  ground-truth cohort by case id. Today, with `--dataset-schema`, it evaluates
  each ground-truth case against itself. Pairing two descriptors is Stage 16's
  consumer work. This item supplies only the id equality it will join on.
- **Left open:** whether `verse19.yaml`'s absolute `data_root` should become
  a placeholder like `verse20.yaml`'s. That would change the default every
  existing VerSe19 command on the project's host relies on. Neither the queue
  line nor the role subsets need it.
