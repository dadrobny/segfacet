> Stage 6's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 6`, run on the main or queue branch, moves it back.

## Stage 6 — VerSe Reference Distributions & Delta-to-Reference Rules (G3)

**Goal.** Ground the heuristics in VerSe-derived expected distributions rather
than hand-guessed constants.

**Deliverables.**

- VerSe GT ingestion → per-level feature aggregation into **reference
  distributions** (mean/percentiles), stratified by level (and a subject-size
  proxy where feasible).
- **Versioned reference-data artifact** (committed or mounted) + a builder script.
- **Delta-to-reference rules**: per-vertebra distribution distance / out-of-range
  vs reference.
- Heuristic config can switch from hand-set bounds to reference-derived bounds
  where available.

**Dependencies.** Stages 2–4 (parallelisable with Stage 5).

**Validation / acceptance.**

- Reference artifact builds reproducibly from VerSe and is versioned.
- GT fixtures fall within reference ranges; perturbed cases fall outside (**G3**).
- Tests cover reference loading + delta rules.
