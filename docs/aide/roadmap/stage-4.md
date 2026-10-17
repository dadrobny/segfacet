> Stage 4's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 4`, run on the main or queue branch, moves it back.

## Stage 4 — Heuristic Rule Engine over the Failure Modes (G2)

**Goal.** An explainable, configurable rule engine that detects each §6 failure
mode — the "simple heuristics" focus of the MVP.

**Deliverables.**

- Config-driven **rule engine**: each rule emits a flag + human-readable reason +
  offending labels.
- Rule families covering §6:
  - **min/max bounds** (volume, extent), level-aware;
  - **connected-components** → fragmentation / island flags;
  - **incomplete coverage / missing levels** (count vs expected sequence);
  - **label-sequence continuity** (e.g. L1→T12→L2→L5);
  - **border-partial-vertebra** flag;
  - **overlap** flag;
  - **mislabel / misalignment** (centroid vs expected level ordering / spline).
- **Verdict aggregation**: combine flags → pass / flag / fail with severity.
- Heuristic thresholds in a documented, versioned config file.

**Dependencies.** Stages 2, 3.

**Validation / acceptance.**

- Each of the 8 failure modes in §6 has ≥1 heuristic that fires on a crafted
  example (**G2**).
- Every flag carries a reason + offending labels; thresholds live in config.
- Tests assert correct firing **and** non-firing per rule.
