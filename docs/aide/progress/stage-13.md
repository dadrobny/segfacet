> Stage 13's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 13`, run on the main or queue branch, moves it back.

## Stage 13 — Dataset Ingestion Adapters & Harmonization Schema (G3/G7 enabler) — ✅

**Goal.** Decouple the pipeline from any single dataset's on-disk layout, naming,
and label scheme via a dataset-agnostic `Cohort`/`Case` interface + declarative
per-dataset adapters, so real cohorts in varied layouts (VerSe19/20,
TotalSegmentator / SPINEPS outputs) are ingested through one interface with no
manual staging. Prerequisite for doing Stage 12's real-VerSe build/evaluation
through a clean interface. Scoped + built 2026-07-16 (queue-011, items 086–088).

**Deliverables.**

- ✅ Dataset-agnostic `Cohort`/`Case` interface (framework side): `Case` =
  `case_id`, `seg_path`, `scan_path|None`, `role` (`gt`|`candidate`),
  `label_convention`, metadata; `Cohort` = ordered, deterministic collection. *(Item 086)*
- ✅ Declarative per-dataset descriptor (data_root, recursive seg/scan globs,
  case-id extraction incl. split subjects, label convention, role, optional
  adapter-only `subsets` = folder/CSV/id-list/glob). *(Item 086)*
- ✅ Resolver (`segqc.datasets.resolve`) materialising a `Cohort`; `ingest_cohort`
  gains a `Cohort`-driven sibling (`ingest_dataset_cohort`) +
  `build_reference_from_cohort`, alongside the retained flat path. *(Item 087)*
- ✅ CLI: `run`/`build-reference`/`evaluate` accept
  `--dataset-schema`/`--data-root`/`--subset` (run = batch mode). *(Item 087)*
- ✅ First committed descriptor: `src/segqc/datasets/verse19.yaml`, validated
  against the mounted cohort (resolved real VerSe19 train 80 / val 40 / test 40,
  split-subjects handled). *(Item 088)*

**Acceptance.**

- [X] The VerSe19 descriptor resolves a mounted cohort to the expected
  `(case_id, seg, scan)` triples (incl. split subjects), deterministically, with
  no manual staging. *(Item 088; verified 2026-07-16 on real VerSe19)*
- [X] `build-reference`/`evaluate`/`run` accept `--dataset-schema`/`--data-root`/
  `--subset` and produce correct output over the nested dataset. *(Item 087)*
- [X] The framework operates only on `Cohort`/`Case`; two disjoint adapter subsets
  (VerSe19 train vs validation) drive a held-out build-vs-evaluate flow the
  framework treats as two plain cohorts.
- [X] Existing synthetic tests stay green (flat ingestion path retained).
