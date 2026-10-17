> Stage 18's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 18`, run on the main or queue branch, moves it back.

## Stage 18 — Failure-Mode-Specific Metric Surface (G2, G7)

**Goal.** You cannot improve what you cannot measure per mode. Today the pipeline emits
a verdict and findings, but the quantities that *isolate* a specific failure mode are
either unexposed or recomputed privately inside a rule — e.g. "foreground beyond the main
connected component" is calculated inside `heuristics/fragmentation.py` rather than
existing as a named field anything else can read.

**Deliverables.**

- **Promote stray-component metrics to first-class fields** in `features/components.py`
  (stray volume mm³, count, fraction) and have the fragmentation rule *read* them instead
  of recomputing.
- **A per-mode metric API** mapping each §6 failure mode to the metric that isolates it,
  reusing `eval/overlap.py::compute_overlap` for Dice/Jaccard and its
  `mean_dice`/`volume_weighted_dice` aggregates — no new overlap code.
- **A cohort-level, per-mode report** suitable for comparing two runs of a segmentation
  tool against each other (e.g. with a post-processing step on vs off), so a change in
  behaviour is attributable to a specific failure mode rather than to aggregate Dice.

**Dependencies.** Stage 17 (level names must be right before per-level metrics mean
anything).

**Validation / acceptance.**

- Each §6 mode has ≥1 named metric that moves monotonically with injected
  severity of that mode and is comparatively insensitive to the others (**G2**).
- The fragmentation rule's behaviour is unchanged by the refactor (**G7**).
