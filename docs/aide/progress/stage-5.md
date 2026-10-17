> Stage 5's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 5`, run on the main or queue branch, moves it back.

## Stage 5 — Synthetic Failure Corpus & Regression Suite (G7) — ✅

**Goal.** Reproducible corpus + automated tests covering every failure mode.

**Deliverables.**

- ✅ Synthetic-failure generator: clean-GT spine builder & perturbation
  framework (item 036); component/shape perturbations — fragment, fuse,
  inject islands (item 037); coverage/border/overlap perturbations — remove
  level, crop at border, force overlap (item 038); identity/ordering/
  alignment perturbations — displace, relabel/swap, sequence-break (item 039).
  *(Items 036–039)*
- ✅ Small committed fixture set spanning all 8 failure modes. *(Item 040)*
- ✅ Regression suite asserting expected verdict + which heuristic fired per case. *(Item 041)*
- ✅ Golden-file JSON snapshots for stability/determinism. *(Item 042)*
- ✅ Cross-platform golden comparison: fresh-vs-committed via numeric tolerance (item 042's byte-identity of asymmetric-geometry floats was only reproducible on the goldens' origin platform; found via CI). *(Item 078)*

**Acceptance.**

- [X] Every §6 failure mode has ≥1 synthetic case and is detected (**G7**, **G2**).
- [X] Full-pipeline regression suite green; golden JSON stable across repeated runs.
