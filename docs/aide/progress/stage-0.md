> Stage 0's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 0`, run on the main or queue branch, moves it back.

## Stage 0 — Project Scaffolding & I/O Foundation — ✅

**Goal.** A runnable, cross-platform Python package + CLI that loads a scan and an
instance label map, normalises labels, and exits cleanly.

**Deliverables.**

- ✅ Python package `segqc/` targeting Python 3.9+; `pyproject.toml` with pinned
  core deps (NumPy, SciPy, scikit-image, NiBabel and/or SimpleITK). *(Item 001)*
- ✅ CLI entry point: `segqc run --scan <nii> --seg <nii> --out <dir>`. *(Item 006)*
- ✅ NIfTI loader for scan + label map, preserving spacing/affine, handling anisotropy. *(Item 003)*
- ✅ Label-convention module: integer label ↔ anatomical vertebra, configurable,
  with a default TotalSegmentator/VerSe mapping. *(Item 004)*
- ✅ Structured logging + versioned heuristic-config scaffold (YAML/JSON). *(Item 005)*
- ✅ `pytest` harness + tiny synthetic NIfTI fixtures. *(Item 002)*

**Acceptance.**

- [X] `segqc run` on a fixture loads both volumes, prints labelled inventory, writes a stub JSON. *(Items 006, 010; `test_cli_run.py`, `test_010_pipeline.py`)*
- [X] Unit tests for loader and label mapping pass. *(`test_io.py`, `test_labels.py`)*
- [X] Runs CPU-only on Windows, macOS, and Linux. *(NumPy/SciPy CPU-only deps; suite green on Windows)*
