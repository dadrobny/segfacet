> Stage 10's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 10`, run on the main or queue branch, moves it back.

## Stage 10 — Portable Compute: GPU Acceleration Path (G6) — ✅

**Goal.** Optional GPU acceleration equivalent to the CPU path; GPU never required.

**Deliverables.**

- ✅ Runtime backend selection (CuPy/cuCIM when present, NumPy/SciPy fallback). *(Item 071)*
- ✅ Backend-aware feature extraction (Stage 2/3 geometric/topological compute routed through the abstraction). *(Item 072)*
- ✅ Equivalence tests: CPU vs GPU produce identical verdicts. *(Item 073)*
- ✅ Performance benchmark. *(Item 074)*
- ✅ CLI/pipeline integration + Stage-10 acceptance closure. *(Item 075)*
- ✅ GPU-present-host verification hardening: fixed the CuPy/NumPy-2.5 (NEP-50) regression in `compute_edt_centroids` (the GPU path passed a Python `int` to `cupy.unravel_index`, which `numpy.can_cast` now rejects — `centroids.py:339`), and guarded the inverse-condition GPU tests to self-skip cleanly on a CuPy-**present** host (mirroring the siblings using `if cupy_available(): pytest.skip(...)`), so the Stage-10 GPU-gated suite runs green on a GPU-enabled host with the CPU/GPU equivalence tests actually **executing** (verified on a Quadro P6000, sm_61). Closes the "GPU-accelerated feature extraction" verification row and corrects `docs/gpu-verification.md`. *(Item 085)*

**Acceptance.**

- [X] GPU path optional + auto-detected; CPU/GPU verdict-equivalence tests pass. *(Item 075)*
- [X] The tool runs fully CPU-only (**G6**). *(Item 075)*
- [X] On a CuPy-present GPU host the GPU-gated suite is green: the CPU/GPU equivalence tests execute (not skip) and pass; the inverse-condition tests skip cleanly and are allow-listed by `assert_no_skips.py`. *(Item 085; verified 2026-07-16 on a Quadro P6000 sm_61 — 155 passed, 16 allow-listed skips, 0 failed)*
