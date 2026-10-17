> Stage 4's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 4`, run on the main or queue branch, moves it back.

## Stage 4 — Heuristic Rule Engine over the Failure Modes (G2) — ✅

**Goal.** Explainable, configurable rule engine detecting each §6 failure mode.

**Deliverables.**

- ✅ Config-driven rule engine: each rule emits flag + human-readable reason + offending labels. *(Item 026)*
- ✅ Rule family — min/max bounds (volume, extent), level-aware. *(Item 027)*
- ✅ Rule family — connected-components → fragmentation / island flags. *(Item 028)*
- ✅ Rule family — incomplete coverage / missing levels (count vs expected sequence). *(Item 029)*
- ✅ Rule family — label-sequence continuity (e.g. L1→T12→L2→L5). *(Item 030)*
- ✅ Rule family — border-partial-vertebra flag. *(Item 031)*
- ✅ Rule family — overlap flag. *(Item 032)*
- ✅ Rule family — mislabel / misalignment (centroid vs expected level ordering / spline). *(Item 033)*
- ✅ Verdict aggregation: combine flags → pass / flag / fail with severity. *(Item 034)*
- ✅ Heuristic thresholds in a documented, versioned config file; pipeline/report integration & per-failure-mode tests. *(Item 035)*

**Acceptance.**

- [X] Each of the 8 §6 failure modes has ≥1 heuristic firing on a crafted example (**G2**).
- [X] Every flag carries a reason + offending labels; thresholds live in config.
- [X] Tests assert correct firing **and** non-firing per rule.
