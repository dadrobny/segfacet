> Stage 13's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 13`, run on the main or queue branch, moves it back.

## Stage 13 — Dataset Ingestion Adapters & Harmonization Schema (G3, G7 enabler)

**Goal.** Decouple the pipeline from any single dataset's on-disk layout, naming
convention, and label scheme by introducing a **dataset-agnostic `Cohort`/`Case`
interface** plus **declarative, per-dataset adapters** that map arbitrary datasets
onto it. Today ingestion (`segqc.reference.ingest.ingest_cohort`) is flat,
non-recursive, and hardcodes a `<id>_scan.nii.gz` sibling, so a nested/varied real
dataset (e.g. VerSe's `derivatives/…_seg-vert_msk.nii.gz` + `rawdata/…_ct.nii.gz`)
can't be read without manual copy/symlink staging. This stage removes that friction
so real cohorts are ingested directly and uniformly — and it is the prerequisite for
doing Stage 12's real-VerSe build/evaluation through a clean interface rather than a
throwaway staging hack.

**Design principle — keep the framework dataset-agnostic.** The framework's three
operations (`run` a case, `build-reference` from a GT cohort, `evaluate` a cohort or
a build+held-out pair) consume **only** a `Cohort` (an ordered, deterministic
iterable of `Case`s). Everything dataset-specific — folder structure, filename
conventions, label mapping, and *how a subset of cases is selected* — lives in the
adapter. A train/val/test "split" is just **one kind of subset** an adapter can
produce; the framework must **not** expect or rely on pre-split datasets (another
dataset might select a subset via a CSV / id-list / glob). This preserves the clean
separation between (1) code/function testing on synthetic fixtures, (2) building a
real-GT reference/heuristic knowledge base, and (3) applying the tool to score new
automatic segmentations (TotalSegmentator, SPINEPS, …).

**Deliverables.**

- **`Cohort` / `Case` interface** (framework side, dataset-agnostic): `Case`
  carries `case_id`, `seg_path`, `scan_path | None`, `role` (`gt` | `candidate`),
  resolved `label_convention`, and optional metadata; `Cohort` is an ordered,
  deterministic collection of `Case`s.
- **Declarative per-dataset descriptor** (YAML/JSON): configurable `data_root`;
  recursive `seg` glob; `scan` template/glob (or none); `case_id` extraction
  (incl. split-subject infixes); `label_convention`; `role`; and optional named
  **`subsets`** (folder / CSV / id-list / glob) — adapter-only, never a framework
  concept.
- **Resolver** (`segqc.datasets`): `resolve(descriptor, *, data_root, subset, role) -> Cohort`, deterministic ordering; the existing flat `ingest_cohort` /
  `build_gt_pass_manifest` gain a `Cohort`-driven discovery path **alongside** the
  flat one (retained for the synthetic determinism fixtures).
- **CLI surface:** `run` / `build-reference` / `evaluate` accept
  `--dataset-schema <descriptor> [--data-root <dir>] [--subset <name|csv>]`, so a
  nested dataset is ingested with **no manual staging**.
- **First committed descriptor:** a **VerSe19** descriptor validated against a
  mounted cohort, reconciling the documented layout/naming drift (nested
  `derivatives/`+`rawdata/` root; `_seg-vb_ctd.json`).

**Dependencies.** Stages 6, 7 (✅ — ingestion + evaluation surfaces exist).
Independent of Stages 8–11. **Unblocks the real-data half of Stage 12.**

**Validation / acceptance.**

- The VerSe19 descriptor resolves a mounted cohort to the expected
  `(case_id, seg_path, scan_path)` triples — including split subjects — with **no
  manual staging**; ordering is deterministic.
- `segqc build-reference` / `evaluate` / `run` accept `--dataset-schema` /
  `--data-root` / `--subset` and produce correct output over a nested dataset.
- The framework operates only on `Cohort`/`Case`; no dataset-specific concept leaks
  into it, and asking the adapter for two disjoint subsets (e.g. VerSe19 train vs
  validation) drives a held-out build-vs-evaluate flow the framework treats as two
  plain cohorts.
- Existing synthetic tests stay green (the flat ingestion path is retained).
