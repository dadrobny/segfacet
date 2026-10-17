> Stage 6's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 6`, run on the main or queue branch, moves it back.

## Stage 6 — VerSe Reference Distributions & Delta-to-Reference Rules (G3) — ✅

**Goal.** Ground heuristics in VerSe-derived expected distributions.

**Deliverables.**

- ✅ VerSe GT ingestion → per-level feature aggregation into reference distributions
  (mean/percentiles), stratified by level (+ subject-size proxy where feasible). *(Items 043, 044)*
- ✅ Versioned reference-data artifact (committed or mounted) + builder script. *(Item 045)*
- ✅ Delta-to-reference rules: per-vertebra distribution distance / out-of-range vs reference. *(Items 046, 047)*
- ✅ Heuristic config can switch from hand-set bounds to reference-derived bounds. *(Item 048)*
- ✅ Reference artifact + delta rules wired into `segqc run`; Stage-6 acceptance suite
  (GT in-range, perturbations out-of-range). *(Item 049)*

**Acceptance.** *(Assessed against a 5-subject **synthetic** VerSe-shaped stand-in
— `reference_default.json`, `provenance.source == "synthetic-verse-cohort"` — as
recorded in Stage 12's goal. Real VerSe grounding arrived with Stages 12/13.)*

- [X] Reference artifact builds reproducibly from VerSe and is versioned. *(Synthetic stand-in at the time; since 2026-07-17 also from **real** VerSe19 training — `reference_verse_v1.json`, 25 per-level distributions C1…S. See Stage 13 and the verification table.)*
- [X] GT fixtures fall within reference ranges; perturbed cases fall outside (**G3**) — **on synthetic fixtures**. ⚠️ **Does not hold for real GT:** real VerSe19 GT falls *outside* these ranges often enough to yield a 0.925 FPR, which is the gap Stage 14 closes.
- [X] Tests cover reference loading + delta rules.
