> Stage 5's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 5`, run on the main or queue branch, moves it back.

## Stage 5 — Synthetic Failure Corpus & Regression Suite (G7)

**Goal.** A reproducible corpus and automated tests covering every failure mode.

**Deliverables.**

- **Synthetic-failure generator** that perturbs a GT label map: relabel,
  remove/add segment, inject islands, fuse/fragment, swap order, crop at border,
  overlap.
- Small committed **fixture set** spanning all 8 failure modes.
- **Regression suite**: runs the full pipeline and asserts the expected verdict +
  which heuristic fired per case.
- **Golden-file JSON snapshots** for stability/determinism.

**Dependencies.** Stage 4.

**Validation / acceptance.**

- Every §6 failure mode has ≥1 synthetic case and is detected (**G7**, **G2**).
- Full-pipeline regression suite green; golden JSON stable across repeated runs.
