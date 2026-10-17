> Stage 12's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 12`, run on the main or queue branch, moves it back.

## Stage 12 — Real-VerSe Grounding & Reference Feature Expansion (G3, G7)

**Goal.** Finish what Stages 6/7 started against a *synthetic* stand-in: widen
the reference distributions to the full set of discriminative per-level
features the engine already computes, ground them in **real VerSe** ground
truth, and quantify the pipeline's false-positive rate on real GT. Stages 6/7
shipped their machinery on a 5-subject synthetic VerSe-shaped cohort
(`reference_default.json` → `provenance.source == "synthetic-verse-cohort"`);
this stage closes the gap between "the pipeline can do this" and "the pipeline
has been grounded in and evaluated on real VerSe."

**Deliverables.**

- **Expanded reference feature vocabulary.** Widen the ingested/aggregated
  per-level feature set beyond the current 5 geometric + 13 intensity scalars
  to include the discriminative Stage-2/3 scalars the engine already computes
  but the reference ignores — fragmentation index, largest-component fraction,
  component count, centroid depth (EDT), per-label orientation, and
  spacing/neighbour-consistency deviations — threaded through ingest →
  aggregation → the delta-to-reference rules → the switchable config.
- **Real-VerSe acquisition & versioned artifact build recipe.** Documented,
  scripted process to mount a real VerSe GT cohort and produce a separately
  **versioned** reference artifact (`reference_verse_vN.json`, `provenance.source == "verse-vN"`); commit the *derived distributions artifact*, never the raw
  VerSe scans (large / licensed). Keep the synthetic default for reproducible
  tests.
- **One-command refresh wrapper.** A re-runnable script/target that rebuilds
  the reference artifact and re-runs the Stage-7 evaluation, so "we added a
  feature / changed config → refresh everything" is a single invocation. It
  must **degrade gracefully when real VerSe data is absent** (not committed):
  rebuild the synthetic default and evaluate the synthetic corpus, and clearly
  skip — never fail — the real-VerSe steps, mirroring the environment-gated
  capability pattern.
- **Real-VerSe evaluation & verification.** Run `segqc evaluate` over real
  VerSe GT to quantify the G3 target (GT passes QC at a high rate / low FPR);
  record the metrics and flip the "Real VerSe GT" row in `progress.md`'s
  Environment-Gated Capability Verification table to ✅ Verified.

**Dependencies.** Stages 6, 7 (✅). Independent of Stages 8–11; may be
prioritised ahead of them.

**Validation / acceptance.**

- The expanded features appear in a rebuilt reference artifact and are consumed
  by the delta-to-reference rules; existing synthetic tests stay green.
- The real-VerSe artifact builds reproducibly from a mounted VerSe cohort
  (verified where data is available); the refresh wrapper skips the real-VerSe
  steps cleanly when the cohort is absent.
- The pipeline's false-positive rate on real VerSe GT is quantified and
  recorded (**G3**, **G7**); the verification-table row reads Verified.
