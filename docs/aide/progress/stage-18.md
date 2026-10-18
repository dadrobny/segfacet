> Stage 18's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 18`, run on the main or queue branch, moves it back.

## Stage 18 — Failure-Mode-Specific Metric Surface (G2, G7) — ✅

**Goal.** Measure per failure mode. "Foreground beyond the main connected component" is
currently recomputed privately inside `heuristics/fragmentation.py` rather than existing
as a named field, so nothing else can read it.

**Deliverables.**

- ✅ Promote stray-component metrics to first-class fields in `features/components.py`
  (stray volume mm³, count, fraction); fragmentation rule reads rather than recomputes. *(Item 098)*
- ✅ Per-mode metric API, reusing `eval/overlap.py::compute_overlap` for Dice/Jaccard and
  its aggregates — no new overlap code. *(Item 099)*
- ✅ Severity-ladder monotonicity + cross-mode specificity harness (the **G2** acceptance):
  graded ladders per §6 mode from the existing perturbation-operator constructor knobs. *(Item 100)*
- ✅ Cohort-level per-mode report supporting run-vs-run comparison of a segmentation tool. *(Item 101)*
- ✅ Stage 18 end-to-end validation: CLI-level replay + verification-row closure. *(Item 102)*

**Acceptance.**

- [x] Each §6 mode has ≥1 named metric moving monotonically with injected severity of that
  mode, and comparatively insensitive to the others (**G2**). *(a) All eight modes have a
  named metric that is monotone and strictly changing across its own ladder (item 100,
  replayed by item 102). (b) Seven of eight ladders clear the strict-specificity bar
  (`margin > 1.0`); **mode 6** does not — measured margin `0.3585`, its ladder driving
  mode 1's `unanchored_foreground_fraction` `2.79×` harder than mode 1's own FOV-capped
  ladder, recorded in `KNOWN_CROSS_MODE_COUPLINGS`. (c) **Mode 7** carries a declared
  two-rung degenerate ladder (metric structurally capped at 1 by the label convention).
  (d) All of it is measured on synthetic ladders only.*
- [x] The fragmentation rule's behaviour is unchanged by the refactor (**G7**). *Evidenced
  at report level by item 102's AC5: nine CLI `segfacet run --no-reference` invocations
  whose `verdict` + `findings` equal the frozen pre-098 snapshot — above item 098's
  rule-level regression.*
