> Stage 0's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 0`, run on the main or queue branch, moves it back.

## Stage 0 — Project Scaffolding & I/O Foundation

**Goal.** A runnable, cross-platform Python package + CLI that loads a scan and an
instance label map, normalises labels via a documented convention, and exits
cleanly. Establishes the skeleton every later stage plugs into.

**Deliverables.**

- Python package `segqc/` targeting **Python 3.9+**; `pyproject.toml` with pinned
  core deps (NumPy, SciPy, scikit-image, NiBabel and/or SimpleITK).
- CLI entry point: `segqc run --scan <nii> --seg <nii> --out <dir>`.
- NIfTI loader for scan + label map, preserving spacing/affine and handling
  anisotropy.
- **Label convention module**: integer label ↔ anatomical vertebra
  (C1–C7, T1–T12(+T13), L1–L5(+L6), S…), configurable, with a default
  TotalSegmentator/VerSe mapping.
- Structured logging and a versioned **heuristic config** scaffold (YAML/JSON).
- `pytest` harness + a couple of tiny synthetic NIfTI fixtures.

**Dependencies.** None.

**Validation / acceptance.**

- `segqc run` on a fixture loads both volumes, prints the label inventory with
  anatomical names, and writes a stub JSON.
- Unit tests for the loader and label mapping pass.
- Runs CPU-only on Windows, macOS, and Linux.
