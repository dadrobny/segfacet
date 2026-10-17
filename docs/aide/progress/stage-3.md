> Stage 3's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 3`, run on the main or queue branch, moves it back.

## Stage 3 — Spinal Curve: Spline Fit & Geometric Deviation Features — ✅

**Goal.** Centroid-spline and deviation features powering alignment, ordering, and
mislabelling heuristics.

**Deliverables.**

- ✅ Spline fit through ordered vertebra centroids, robust to missing levels. *(Item 017)*
- ✅ Per-vertebra offset from the spline. *(Item 018)*
- ✅ Orientation / rotation estimate per vertebra + global curvature descriptors. *(Item 019)*
- ✅ Neighbour-consistency metrics (spacing regularity, monotonic progression). *(Item 020)*
- ✅ Optional sagittal projection of centroids + spline for the human report; retired by owner decision 2026-10-09. *(Item 021)*
- ✅ Stage 3 feature serialisation & GT-vs-perturbed regression tests. *(Item 022)*
- ✅ Local vertebra neighbourhood comparison (sliding window, n=3–5): per-vertebra deviation from neighbourhood mean/median of centroid spacing, spline offset, and volume, plus a deviation score and outlier flag. *(Item 024)* ⚠️ **Correction, 2026-08-11:** the module (`features/neighbourhood.py`) was implemented in full but **wired into nothing** — absent from `pipeline.py`, `feature_report.py` and all 10 rules, which is why it never appeared in item 103's 111-entry catalogue. ✅ **Wired, 2026-08-14 (Item 110):** the module was generalised to an arbitrary named-feature API and wired into `extract_feature_record`/`feature_report.py` as `stage3.per_label_neighbourhood[]` (computed and serialised for every case with ≥ 2 labels). It is **consumed by no rule** — `status == "unwired"` in the regenerated feature catalogue, confirmed by Item 110's AC11 (every corpus case's verdict and findings are unchanged by the wiring). No outlier this module computes is ever flagged to a verdict; that remains Stage 20's call, same as any other unwired feature. *(Item 024)*

**Acceptance.**

- [X] Spline fits cleanly on GT fixtures; offsets near-zero for GT, large for displaced/mislabelled.
- [X] Robust to a deliberately missing level (no crash, sensible fit).
- [X] Orientation / curvature features in JSON; tests pass. *(Item 019)*
- [X] Neighbour-consistency features in JSON. *(Item 020)* *(Item 024: neighbourhood-comparison module generalised and wired into pipeline as of Item 110 — `stage3.per_label_neighbourhood[]` is computed and serialised for every ≥2-label case, but consumed by no rule; status "unwired" in the feature catalogue.)*
- [X] Regression tests over GT + perturbed cases pass. *(Item 022)*
