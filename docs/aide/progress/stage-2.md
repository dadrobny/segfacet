> Stage 2's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 2`, run on the main or queue branch, moves it back.

## Stage 2 — Geometric & Topological Feature Extraction — ✅

**Goal.** The feature engine the heuristics depend on — the MVP image-processing core.

**Deliverables.**

- ✅ Per-label features: voxel & physical volume; extent (x/y/z); bounding box; border-contact flags. *(Item 011)*
- ✅ Connected-components per label: component count + sizes. *(Item 012)*
- ✅ Centroid / centre-of-mass per label, level-aware (C1, C2, S). *(Item 013)*
- ✅ Inter-vertebra relationships: ordered centroid sequence, neighbour spacing, sequence continuity. *(Item 014)*
- ✅ Overlap detection between labels. *(Item 015)*
- ✅ Features serialised into JSON (`features` block) + per-case feature table. *(Item 016)*
- ✅ EDT-based centroid variants (smooth-centre via EDT-threshold CoM; strict-centre via EDT peak) + centroid depth (distance from centroid to nearest label surface). C1/C2 handled as special anatomy. *(Item 023)*
- ✅ Fragmentation index per label (largest connected component / total label volume), extending the JSON features block. *(Item 025)*

**Acceptance.**

- [X] Features computed deterministically; values verified against hand-computed expectations.
- [X] Anisotropic-spacing fixture yields correct physical volumes/extents.
- [X] `features` block emitted in JSON; tests cover each feature.
- [X] EDT-based centroid variants computed; centroid depth available per label. *(Item 023)*
- [X] Fragmentation index computed per label and serialised in JSON features block. *(Item 025)*
