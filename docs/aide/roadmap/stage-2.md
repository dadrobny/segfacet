> Stage 2's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 2`, run on the main or queue branch, moves it back.

## Stage 2 — Geometric & Topological Feature Extraction (image-processing core)

**Goal.** Build the feature engine the heuristics depend on — the core
"image processing" focus of the MVP.

**Deliverables.**

- Per-label features: voxel & physical **volume**; **extent** (x/y/z); **bounding
  box**; image-border-contact flags.
- **Connected-components** per label: component count + sizes (inputs for
  fragmentation / island detection).
- **Fragmentation index** per label: ratio of largest connected component to
  total label volume — a scalar summarising how split the label is.
- **Vertebra centroid** per label, with level-aware special handling (C1, C2, S):
  - Simple CoM (baseline).
  - EDT-based *smooth centre* (CoM of EDT-thresholded mask) and *strict centre*
    (smoothed EDT peak) for more robust localisation within the vertebral body.
- **Centroid depth**: distance from the chosen centroid to the nearest label
  surface (reuses the EDT from the centroid step).
- **Inter-vertebra relationships**: ordered centroid sequence, neighbour spacing,
  label-sequence continuity.
- **Overlap detection** between labels.
- Features serialised into the JSON report (`features` block) + a per-case
  feature table.

**Dependencies.** Stage 0 (extends Stage 1 report model).

**Validation / acceptance.**

- Features computed deterministically on fixtures; values verified against
  hand-computed expectations.
- An anisotropic-spacing fixture yields correct physical volumes/extents.
- `features` block emitted in JSON; tests cover each feature.
- EDT-based centroid variants computed; centroid depth available per label.
- Fragmentation index computed per label and serialised in the `features` block.
