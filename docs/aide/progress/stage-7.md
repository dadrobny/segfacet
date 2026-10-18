> Stage 7's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 7`, run on the main or queue branch, moves it back.

## Stage 7 — Evaluation, Calibration & Metrics (G3, G7) *(Phase 1 complete)* — ✅

**Goal.** Quantify performance and calibrate thresholds against VerSe GT,
TotalSegmentator output, and the synthetic corpus.

**Deliverables.**

- ✅ Segmentation-overlap metrics — per-label & aggregate DICE / Jaccard vs GT. *(Item 050)*
- ✅ Feature-set match / divergence by vertebra label. *(Item 051)*
- ✅ QC-verdict comparison & per-case outcome classification. *(Item 052)*
- ✅ Evaluation harness *accepts* VerSe GT (positive control), TotalSegmentator outputs, and synthetic failures through one cohort-manifest shape — exercised in tests over the **synthetic corpus only**; item 053 scoped itself to require "no VerSe/TotalSegmentator download", and no TotalSegmentator output has ever been run through it (see the verification table). *(Item 053)*
- ✅ Metrics: FPR on GT, sensitivity per failure mode, DICE-vs-flag correlation. *(Item 054)*
- ✅ Threshold-calibration loop; chosen thresholds + metrics recorded here / evaluation report. *(Items 055, 056)*
- ✅ Stage-7 integration into a reproducible `segqc evaluate` entry point + acceptance suite
  (GT low-FPR, injected failures caught, DICE-vs-flag correlation) closing Phase 1;
  calibrated thresholds + metrics recorded. *(Item 057)*

**Acceptance.** *(All three were assessed against the **synthetic** corpus — the
only data available when this stage closed. The boxes stay ticked because the
stage's code and its synthetic validation are genuinely complete; the two marked
**superseded** are claims real data has since overturned or left open. Objective
status now lives in the Objective coverage table, not here.)*

- [X] GT passes at a high rate (low FPR) (**G3**) — **on the synthetic
  `clean_control` GT: FPR 0.0.** ⚠️ **Superseded on real data (2026-07-17):** the
  same thresholds flag real held-out VerSe19 GT at **0.925 / 0.975**. This box
  records what Stage 7 verified; it does **not** evidence G3, which is now 🚧
  pending Stage 14.
- [X] Injected failures caught; flag rate / feature divergence correlates with DICE (**G7**) — **on synthetic injected failures** (5/8 modes detectable through the plain pipeline) and a **synthetic** graded-quality cohort (DICE-vs-flag **-0.943**). ⚠️ **Not yet shown on real failures or real graded data** — see Stage 16.
- [X] Calibrated thresholds + metrics recorded; evaluation reproducible. *(Genuinely met — the harness is reproducible and is exactly what made the real-data measurement possible.)*

**Calibrated metrics (to be filled at completion).** *(Item 057 acceptance run
over the committed §6 synthetic corpus cohort — GT = `clean_control`,
candidate = each perturbed seg — plus the purpose-built graded-quality
correlation cohort per the Assumptions; `bundled_default_config()`,
uncalibrated.)*

- FPR on GT (`clean_control`): **0.0** (`metrics.false_positive_rate`, AC8).
- Sensitivity per §6 failure mode (`metrics.per_mode[*].sensitivity`, AC9):
  pipeline-detectable modes 2 (fragment), 3 (inject islands), 5 (remove
  level), 6 (crop at border), 7 (sequence break) — **1.0** each; modes 1
  (displace), 4 (relabel swap), 8 (force overlap) — **0.0**, structurally
  invisible to the plain pipeline (`detection == "reconstructed_record"`,
  documented in the item 057 Assumptions, mirrors item 049). Overall corpus
  sensitivity 5/8, not over-claimed as 1.0.
- DICE-vs-flag correlation: **-0.943** (graded-quality cohort,
  `metrics.dice_vs_flag.coefficient`, AC10 — negative sign as expected: lower
  DICE ⇔ more likely flagged); feature-divergence-vs-flag: **+0.585**
  (`metrics.feature_divergence_vs_flag.coefficient`, AC11 — positive sign as
  expected). The full 9-case §6 corpus does not yield a cleanly-signed
  DICE-vs-flag correlation (some flagged modes barely move DICE while some
  unflagged reconstructed modes move it a lot — see Assumptions), which is
  why AC10/AC11 use the dedicated graded-quality cohort.
