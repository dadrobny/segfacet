> Stage 3's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 3`, run on the main or queue branch, moves it back.

## Stage 3 — Spinal Curve: Spline Fit & Geometric Deviation Features

**Goal.** Add the centroid-spline and deviation features that power alignment,
ordering, and mislabelling heuristics.

**Deliverables.**

- **Spline fit** through the ordered vertebra centroids, robust to missing levels.
- Per-vertebra **offset from the spline**.
- **Orientation / rotation** estimate per vertebra + global curvature descriptors.
- **Neighbour-consistency** metrics (spacing regularity, monotonic progression
  along the curve).
- **Local neighbourhood comparison** (sliding window, n=3–5 vertebrae): for each
  vertebra compute its deviation from the local neighbourhood mean/median of
  centroid spacing, spline offset, volume, and other per-label features; emit a
  per-vertebra deviation score and flag anatomical outliers within an otherwise-
  consistent spine segment.
- Optional sagittal projection of centroids + spline for the human report.

**Dependencies.** Stage 2.

**Validation / acceptance.**

- Spline fits cleanly on GT fixtures; offsets near-zero for GT, large for
  displaced/mislabelled fixtures.
- Robust to a deliberately missing level (no crash, sensible fit).
- Orientation / curvature features in JSON; tests pass.
- Neighbour-consistency features in JSON.
- Regression tests over GT + perturbed cases pass.
