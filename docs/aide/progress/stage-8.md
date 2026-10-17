> Stage 8's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 8`, run on the main or queue branch, moves it back.

## Stage 8 — Image-Based / Radiomics Features — ✅

**Goal.** Intensity/radiomics features to strengthen heuristics and seed abnormality detection.

**Deliverables.**

- ✅ Intensity features over each labelled region (+ original scan); optional PyRadiomics integration. *(Items 059, 060)*
- ✅ Feature fusion into the report + ≥1 intensity-based heuristic (e.g. implausible-intensity flag). *(Items 061, 062)*
- ✅ Reference distributions extended with intensity features. *(Items 063, 064)*
- ✅ Intensity-bearing synthetic scan fixtures (HU-painted GT + implausible-intensity variants) enabling local testing of image features. *(Item 058)*
- ✅ Stage 8 integration into `segqc run` + acceptance suite (image features on fixtures; ≥1 intensity heuristic fires; tests pass). *(Item 065)*
- ✅ PyRadiomics present-path robustness: graceful degrade (not a raw exception) when PyRadiomics itself rejects a mask as too small/degenerate for shape/GLCM extraction. *(Item 076)*

**Acceptance.**

- [X] Image features computed on fixtures; ≥1 intensity-based heuristic fires appropriately; tests pass. *(Item 065)*
