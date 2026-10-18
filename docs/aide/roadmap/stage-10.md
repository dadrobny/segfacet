> Stage 10's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 10`, run on the main or queue branch, moves it back.

## Stage 10 — Portable Compute: GPU Acceleration Path (G6)

**Goal.** Optional GPU acceleration that yields results equivalent to the CPU
path; GPU never required.

**Deliverables.**

- Runtime backend selection (CuPy/cuCIM when present, NumPy/SciPy fallback).
- **Equivalence tests**: CPU vs GPU produce identical verdicts.
- Performance benchmark.

**Dependencies.** Stage 7.

**Validation / acceptance.**

- GPU path is optional + auto-detected; CPU/GPU verdict-equivalence tests pass.
- The tool runs fully CPU-only (**G6**).
- On a CuPy-present GPU host the GPU-gated suite is green: the equivalence tests
  execute rather than skip, and the inverse-condition tests skip cleanly.
