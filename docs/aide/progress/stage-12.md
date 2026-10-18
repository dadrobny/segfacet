> Stage 12's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 12`, run on the main or queue branch, moves it back.

## Stage 12 — Real-VerSe Grounding & Reference Feature Expansion (G3, G7) — ✅

**Goal.** Finish Stages 6/7 against reality: widen the reference distributions
to the full discriminative per-level feature set the engine already computes,
ground them in real VerSe GT, and quantify the false-positive rate on real GT.
Stages 6/7 shipped on a synthetic VerSe stand-in (see the "Real VerSe GT" row in
the Environment-Gated Capability Verification table).

**Deliverables.**

- ✅ Expanded reference feature vocabulary — add fragmentation index, largest-component
  fraction, component count, centroid depth, orientation, and spacing/neighbour-consistency
  deviations through ingest → aggregation → delta rules → config; regenerate the synthetic default. *(Item 081)*
- ✅ Real-VerSe acquisition & versioned artifact build recipe (derived artifact committed, raw scans never). *(Item 082)*
- ✅ One-command reference-refresh wrapper (rebuild + re-evaluate) that degrades gracefully when the uncommitted VerSe cohort is absent. *(Item 083)*
- ✅ Real-VerSe evaluation quantifying the G3 false-positive rate; verification-table closure. *(Item 084)*

**Acceptance.**

- [X] Expanded features appear in the rebuilt reference artifact and are consumed by the delta-to-reference rules; existing synthetic tests stay green.
- [X] The real-VerSe artifact builds reproducibly from a mounted cohort; the refresh wrapper skips the real-VerSe steps cleanly when the cohort is absent.
- [X] The pipeline's false-positive rate on real VerSe GT is quantified and recorded (**G3**, **G7**); the "Real VerSe GT" verification-table row reads Verified. *(Item 084)*
