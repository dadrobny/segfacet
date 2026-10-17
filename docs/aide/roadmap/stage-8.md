> Stage 8's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 8`, run on the main or queue branch, moves it back.

## Stage 8 — Image-Based / Radiomics Features

**Goal.** Add intensity/radiomics features over labelled regions to strengthen
heuristics and seed abnormality detection.

**Deliverables.**

- Intensity features over each labelled region (+ original scan); optional
  **PyRadiomics** integration.
- Feature fusion into the report + at least one intensity-based heuristic
  (e.g. implausible-intensity flag).
- Reference distributions extended with intensity features.

**Dependencies.** Stages 2, 6.

**Validation / acceptance.**

- Image features computed on fixtures; ≥1 intensity-based heuristic fires
  appropriately; tests pass.
