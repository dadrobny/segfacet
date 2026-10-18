<!-- aide-template: progress 2 -->
# FACET — Progress Tracker

> **Status:** v3.2 · **Created:** 2026-06-24 · **Re-issued:** 2026-09-22 against
> [`roadmap.md`](roadmap.md) v3.2 (incremental: Stage 33 added, every existing status
> carried over unchanged; v3.1 of 2026-09-15 added Stages 31–32, Stages 20 and 30
> annotated after item 150's sign-off, every existing status and attestation carried over
> unchanged; v3 of 2026-09-03 added Stage 30 and summary rows for Stages 28–30)
> Step 3 of the AIDE loop. Derived from [`vision.md`](vision.md) and
> [`roadmap.md`](roadmap.md). **Single source of truth for implementation
> status** per stage, deliverable, and acceptance criterion — machine-parsed per
> `.aide/conventions.md` §1 and edited via `python .aide/scripts/aide.py progress set`. Update **incrementally** — never reset a non-planned status back to 📋.

---

## Status legend

| Icon | Meaning     |
| ---- | ----------- |
| 📋   | Planned     |
| 🚧   | In Progress |
| 🔍   | In Review   |
| ✅   | Complete    |
| ⏸️ | Deferred    |
| ❌   | Excluded    |

## Stage summary

| Stage | Title                                                                   | Objectives      | Status |
| ----- | ----------------------------------------------------------------------- | --------------- | ------ |
| 0     | [Project Scaffolding & I/O Foundation](progress/stage-0.md)                                    | (foundation)    | ✅     |
| 1     | [End-to-End Thin Slice: Empty Detection + Report](progress/stage-1.md)                         | G1, G4          | ✅     |
| 2     | [Geometric & Topological Feature Extraction](progress/stage-2.md)                              | (feature core)  | ✅     |
| 3     | [Spinal Curve: Spline Fit & Deviation Features](progress/stage-3.md)                           | (feature core)  | ✅     |
| 4     | [Heuristic Rule Engine over Failure Modes](progress/stage-4.md)                                | G2              | ✅     |
| 5     | [Synthetic Failure Corpus & Regression Suite](progress/stage-5.md)                             | G7, G2          | ✅     |
| 6     | [VerSe Reference Distributions & Delta Rules](progress/stage-6.md)                             | G3              | ✅     |
| 7     | [Evaluation, Calibration & Metrics*(Phase 1 complete)*](progress/stage-7.md)                 | G3, G7          | ✅     |
| 8     | [Image-Based / Radiomics Features](progress/stage-8.md)                                        | (Phase 2)       | ✅     |
| 9     | [Containerisation & XNAT Command](progress/stage-9.md)                                         | G5              | ✅     |
| 10    | [Portable Compute: GPU Acceleration Path](progress/stage-10.md)                                 | G6              | ✅     |
| 11    | Extensibility & Abnormality Classification Arm                          | G8              | ⏸️   |
| 12    | [Real-VerSe Grounding & Reference Feature Expansion](progress/stage-12.md)                      | G3, G7          | ✅     |
| 13    | [Dataset Ingestion Adapters & Harmonization Schema](progress/stage-13.md)                       | (G3/G7 enabler) | ✅     |
| 14    | [Real-Data Grounding & Heuristic Recalibration](progress/stage-14.md)                           | G3, G7          | ✅     |
| 15    | Real-XNAT Deployment Validation                                         | G5              | ❌     |
| 16    | Real Failure Corpus & Sensitivity Validation*(retargeted to SPINEPS)* | G2, G7          | ⏸️     |
| 17    | Foreign-Convention Interop & Orientation-Safe Image Layer               | G2, G6          | ✅     |
| 18    | [Failure-Mode-Specific Metric Surface](progress/stage-18.md)                                    | G2, G7          | ✅     |
| 19    | [Generated Feature & Rule Catalogue + Steering Review](progress/stage-19.md)                    | G7, G8          | ✅     |
| 20    | [Failure-Mode ↔ Feature ↔ Rule Traceability & Specificity Harness](progress/stage-20.md)      | G2, G7          | ✅     |
| 21    | Real-GT Perturbation Corpus                                             | G3, G7          | ⏸️     |
| 22    | *(placeholder)* Unified `(scan, seg)` Extraction                    | —              | 📋     |
| 23    | *(placeholder)* Multivariate Normative Model                          | G3              | 📋     |
| 24    | *(placeholder)* Failure-Mode Discovery & Typed Reference Set          | G8              | 📋     |
| 25    | *(placeholder)* Segmenter-Native Perturbations                        | G2              | 📋     |
| 26    | Carried-Defect Remediation (pre-real-data)*(runs next)*               | G2, G7          | ✅     |
| 27    | [Feature Schema Taxonomy & Coordinate System](progress/stage-27.md)                             | G8              | ✅     |
| 28    | [Spinal Curve Model: Formulation, Offset & Orientation](progress/stage-28.md)                   | G2, G7          | ✅     |
| 29    | Golden Retirement & Test-Artifact Hygiene                               | G2, G7          | ✅     |
| 30    | [Failure-Mode Specification: the §6 catalogue as an authored source *(runs next)*](progress/stage-30.md) | G2, G7, G8 | ✅     |
| 31    | [Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update](progress/stage-31.md) | G7, G8 | ✅     |
| 32    | [Selected-Mode Refinement: one failure mode fully specified end to end](progress/stage-32.md)   | G2, G7, G8      | ✅     |
| 33    | [Corpus & Rule Re-grounding: modes 2 and 3 to the bar](progress/stage-33.md)                    | G2, G7, G8      | ✅     |
| 34    | Maintenance                                                             | —               | ✅     |
| 35    | Programme Interface: the SegFACET Side                                  | G2, G3, G7      | 🚧     |

> **Supersession 2026-07-25.** Stages 0–14 are history and are not reopened. Stage 15 is
> `❌ Excluded` (deployment left scope — see [`vision.md`](vision.md) §0). Stages 17–21
> are the live work; 22–25 are placeholders authored at the full re-vision. Item
> numbering continues from **093** — never restart, `*(Item NNN)*` references are global.

> **Feedback loop 2026-08-11.** Stages **26** and **27** were scoped from triaged
> [`insights.md`](insights.md) entries that had accumulated no owner. They are numbered
> after the placeholders so numbering stays stable, but **run earlier than their numbers
> suggest**: Stage 26 runs **next, ahead of Stage 20** (it fixes surfaces Stage 20 audits),
> and Stage 27 runs after Stage 20 and before Stages 23/24. The same loop reworded Stage
> 19's G8 criterion and clarified what Stage 20's traceability matrix must prove — see
> [`roadmap.md`](roadmap.md).

> **Stage 28 scoped 2026-08-27.** Numbered after Stage 27 so numbering stays stable, but
> **runs before Stage 20** — it changes which rules fire on which cases, and Stage 20 both
> audits that and pins a specificity baseline against it. It also supersedes part of Stage
> 20's reachability deliverable: modes 1 and 4 are one defect (the interpolating spline
> fit), not two, and the FOV-headroom remedy Stage 20 proposed for mode 1 is measurably
> not the cause. Run order from here: **28 → 20 → 27 → 21 → 16**.

> **Stage 29 scoped 2026-08-30** (queue-017 boundary triage), the same construction as
> Stages 26–28: numbered for stability, **runs next, ahead of Stage 20**. It executes the
> maintainer-signed golden retirement (pulled forward from Stages 21/27), makes
> committed-artifact comparisons tolerance-by-construction, and sweeps the located defects
> queue 017 recorded — including `consistency.py`'s mode-4 monotonicity, which closes
> Stage 28's one unticked non-adjudication acceptance half. Run order from here:
> **29 → 20 → 27 → 21 → 16**.

> **Stage 30 scoped 2026-09-03** (queue-019 boundary feedback loop; human gate `gate-0fdd`), the
> same construction as Stages 26–29: numbered for stability, **runs next, ahead of the
> remainder of Stage 20**. Queue-019 was cut after item 138 because its remaining items
> each rested on a definition of the §6 failure modes that existed in five partial sources
> and no specification. Stage 30 authors that specification per [`vision.md`](vision.md)
> v3 §6 and re-points the generated matrix at it as a conformance report; Stage 20's
> items 139–142 are re-specified against it and re-queued after its maintainer sign-off.
> Full statement in [`roadmap.md`](roadmap.md), which also states the run order once at
> its top: **30 → 20 (remainder) → 27 → 21 → 16**.

> **Stages 31 and 32 scoped 2026-09-15** (item 150's close; human gate `gate-fb64` approved), the
> same construction: numbered for stability, **both run before Stages 27, 21 and 16**.
> Item 150's review re-organised the catalogue to sixteen modes plus the FOV-truncation
> condition. **Stage 31** clears what that left behind — the eval-harness re-key (absorbing
> Stage 20's item 141), the `vision.md` §6 re-issue, prerequisite `insights.md` defects and
> the AIDE engine update — without changing any mode. **Stage 32** refines
> **maintainer-selected** modes until at least one is fully specified end to end (the
> pipeline's MVP); every other mode stays documented at its derived status and can be
> refined individually later. Stage 20's items 139 and 140 are built at Stage 32's start
> and item 142 at its close. Run order, stated once at the top of
> [`roadmap.md`](roadmap.md): **30 (item 151) → 31 → 32 (with Stage 20's remainder) → 27
> → 21 → 16**.

> **Stage 33 scoped 2026-09-22** (queue-022 boundary feedback loop, after gate `gate-bb24` signed
> modes 3 and 4 off at an intermediate state). Queue-022's review found the geometric
> corpus cannot express what the rules decide: five non-touching axis-aligned boxes,
> fixtures that do not express their mode, and rules serving a mode by another's signal.
> Stage 33 rebuilds the base as a lordotic L1–L5, re-authors those fixtures, re-homes the
> rules, and re-signs **modes 3 and 4 at the bar**. Its close attests Stage 32's
> criterion 1, so Stage 32 stays 🚧 until then. Run order, stated once at the top of
> [`roadmap.md`](roadmap.md): **33 → 27 → 21 → 16**.
> **Re-targeted 2026-09-30** at gate `gate-51da`: the selected modes became **2 and 3**
> (mode 4 left the stage at its `gate-bb24` intermediate state), signed at the bar at
> `gate-0133` on 2026-10-02. The stage title was corrected on 2026-10-03.

> **Stage 21 deferred 2026-10-07** (queue-029 boundary feedback loop, after Stage 27
> closed). The maintainer decided to go straight to rung 3 — Stage 16, real SPINEPS output
> on real VerSe CT — under the prototype posture, and not to build the rung-2 perturbed
> real-GT corpus first. Stage 21's four deliverables are ⏸️ with the reason on each; Stage
> 16's dependency on Stage 21 is lifted in [`roadmap.md`](roadmap.md). Run order, stated
> once at the top of [`roadmap.md`](roadmap.md): **16 → (21 when needed)**. Stage 16's
> items are gated by `gate-ae46` (SPINEPS output handed over) and, for its curated
> challenging-case deliverable only, `gate-2f91`.

## Two kinds of "done" — implementation vs. validation

This tracker separates two claims that are easy to conflate:

1. **A stage is ✅ when its *code* is built and verified** — against synthetic
   fixtures, golden files, and unit/integration tests. That is evidence about the
   code, not about the world.
2. **An objective is ✅ only when its *measurable outcome*
   ([`vision.md`](vision.md) §2) is demonstrated — on real data wherever the
   outcome says "real".** Building the machinery that *can* measure an outcome is
   not the same as having measured it, and measuring it is not the same as
   *achieving* it.

**Objective status is therefore not derived from stage status.** 🚧 never means
the code is missing — only that the real-world outcome is not yet *demonstrated*.
An objective stays 🚧 for either reason: a **planned** validating stage still
open, or a **shipped** one whose measured goal is not met. Both are captured in
the two tables below — real-run evidence in **Environment-Gated Capability
Verification**, measured-outcome bars in **Outcome targets** — and the `aide`
rollup caps an objective below ✅ while any linked outcome target is not `✅ Met`.

## Objective coverage

_Status = the objective's **measurable outcome** is achieved (not "the code
shipped"). See "Two kinds of done" above._

| Objective                                    | Delivered by                                             | Status |
| -------------------------------------------- | -------------------------------------------------------- | ------ |
| G1 Detect empty / trivially-failed           | Stage 1                                                  | ✅     |
| G2 Detect catalogued failure modes (§6)     | Stages 4, 5, 18, 28*(specification: Stage 30; MVP mode end to end: Stages 32–33; traceability and specificity: Stage 20, interleaved into 32; synthetic only — real failures: Stage 16, read through the programme interface of Stage 35)* | 🚧     |
| G3 Distinguish failure from variation        | Stages 6, 7, 12*(real grounding: Stage 14; development-role reference: Stage 35)* | 🚧     |
| G4 Per-case and cohort reports               | Stage 1 (ext. 2–4); cohort characterisation: Stage 18   | ✅     |
| G5 Deploy on XNAT*(removed from scope 2026-07-25)* | Stage 9 shipped the artefacts; validation was Stage 15 ❌ | ❌     |
| G6 Portable / GPU*(deferred)*              | Stage 10                                                 | ✅     |
| G7 Evaluable & regression-testable           | Stages 5, 7, 29, 32, 33*(eval-harness re-key: Stage 31; real data: Stages 14, 16; dataset roles and artefact versioning: Stage 35)* | 🚧     |
| G8 Extensible / classification               | Stages 19, 27, 30 (the add-a-mode path), 31 (§6 re-issue), 32–33 (per-mode sign-off); classification arm: Stage 11*(deferred)* | ⏸️     |

**Why each 🚧 objective is not yet ✅** _(one line each — the detail lives in the
linked row/stage, not here):_

- **G2** — real-world per-mode sensitivity is unmeasured; no real failure corpus
  has ever run. → [Outcome targets](#outcome-targets) (❓) · Stage 16.
- **G3** — the held-out real-GT **FPR ≤ 0.10** target is **❌ Not met**. →
  [Outcome targets](#outcome-targets) · Stage 14.
- **G5** — never installed/run on a real XNAT server (a binary check, not a
  measured bar, so it is verification rather than an outcome target). → the
  "XNAT … real server" verification row · Stage 15.
- **G7** — the real-GT **sensitivity** target is **❌ Not met**, *and* the curated
  challenging-case corpus is unbuilt. → [Outcome targets](#outcome-targets) ·
  Stages 14 (sensitivity) / 16 (corpus).
- **G8** — the catalogue is generated (Stage 19 ✅), but the add-a-mode path — an
  authored specification a new mode enters through, with the conformance artifacts
  regenerated — is Stage 30's, and the schema taxonomy is Stage 27's; neither has
  shipped. The classification arm (Stage 11) stays deferred and is not what holds
  this at 🚧.

## Environment-Gated Capability Verification

_One row per capability gated behind an optional package, external tool, **or
real-world dataset / environment**. Status is `❓ Unverified` until the gated path
has actually been exercised with the real dependency/data present (a skip-clean
pytest run, or a synthetic stand-in, does not count as verification — see
`.aide/conventions.md`'s "Environment-gated capabilities" rule), then
`✅ Verified (date, host/CI)`. This table is separate from stage completion
above: a stage reaches ✅ on its graceful-fallback / synthetic-stand-in path
alone; this tracks whether the real dependency/data has ever been exercised._

_`✅ Verified` means the gated path **ran for real** — not that the objective's
outcome was **achieved**; that is the [Outcome targets](#outcome-targets) table's
job. The "Real VerSe GT" row is ✅ because the real cohort ran end-to-end, yet its
G3 FPR target is ❌ Not met. Absence of a row is not verification. Keep the
**Evidence / references** column to one line — a pointer to the CI job, stage,
item, or doc where the detail already lives, not a prose copy of it._

| Capability                                      | Package / Tool / Data                                                                    | Introduced by                                                                                                                     | Status                                                                                       | Evidence / references                                                                                                                                                                                                                                                                                                                  |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Real VerSe GT reference distributions | VerSe ground-truth cohort (external dataset) | Stage 6*(Items 044, 045)*; closed by Stage 12 *(Item 084)* + Stage 13 adapter; recalibration by Stage 14 *(Items 089–092)* | ✅ Verified (2026-07-19, real VerSe19 via`segqc.datasets` adapter, no manual staging) | see trail |
| Radiomics feature extraction | `pyradiomics` (extra: `segqc[radiomics]`) | Stage 8*(Item 060)* | ✅ Verified (2026-07-14, GitHub Actions CI) | see trail |
| Containerised pipeline (Docker build + run) | Docker (external tool, no pip dependency) | Stage 9*(Items 066, 069, 070)* | ✅ Verified (2026-07-14, GitHub Actions CI) | see trail |
| XNAT Container Service command on a real server | XNAT server + Container Service (external environment) | Stage 9*(Items 067, 068, 070)*; **Stage 15 ❌ Excluded** | ❓ Unverified (out of scope since 2026-07-25) | see trail |
| Real automatic-segmentation failure corpus | **SPINEPS** outputs on real CT (external tool + data) | Stages 5, 7*(Items 041, 053, 057)*; to be closed by Stage 16 | ❓ Unverified | see trail |
| GPU-accelerated feature extraction | `cupy` (extra: `segqc[gpu]`) | Stage 10*(Items 071–075)*; closed by *(Item 085)* | ✅ Verified (2026-07-16, Quadro P6000 sm_61, CuPy`cupy-cuda12x` 14.1.1, driver 580.159.04) | see trail |
| Real SPINEPS-output label-convention round-trip | Real SPINEPS-produced label map (external tool + data), via `SEGFACET_SPINEPS_FIXTURE` | Stage 17 (Item 097) | ❓ Unverified | see trail |
| Real segmentation-tool run-vs-run per-mode comparison | Two real runs of a real segmenter over the same cohort (e.g. a post-processing step on vs. off), external tool + data | Stage 18 *(Items 101, 102)* | ❓ Unverified | see trail |

- Real VerSe GT reference distributions — 80 real VerSe19 training subjects →`src/segqc/reference/reference_verse_v1.json`. This row attests only that the real cohort **ran** end-to-end; the measured FPR/sensitivity **outcome** (❌ Not met) and the deferred `reference_delta` rework live in [Outcome targets](#outcome-targets) and the Stage 14 section.
- Radiomics feature extraction — CI`verify-environment-gated` (`ci.yml`) installs the extra and runs the radiomics tests, failing on any skip (`assert_no_skips.py`). First real run found + fixed a degenerate-mask bug (item 076); green since PR #33.
- Containerised pipeline (Docker build + run) — Same CI job does a real`docker build` + `docker run` smoke test (`test_066/069/070`); item 080 gated it to a Linux daemon (skip, not error, on Windows-container hosts).
- XNAT Container Service command on a real server — The container itself is verified (Docker row). Installing`command.json` on a real XNAT server never happened and now never will *here*: deployment left scope in [`vision.md`](vision.md) §0 and G5 was removed. Row retained so the artefacts' unverified status stays on the record rather than vanishing with the stage.
- Real automatic-segmentation failure corpus — §6 modes are detected only on synthetically perturbed GT; no real-failure output has run, so item 057's per-mode sensitivities are synthetic-only. Curated challenging cases ([`vision.md`](vision.md) §8) unbuilt. → Stage 16 (rung 3); its dependency on Stage 21 (rung 2) was lifted 2026-10-07, Stage 21 deferred.
- GPU-accelerated feature extraction — Verified on a Pascal sm_61 workstation (2× P6000) with the CPU/GPU equivalence tests executing; first CuPy run found + fixed a NEP-50 regression (item 085). Install`cupy-cuda12x` (**not** `cupy-cuda13x` — drops Pascal). No CI GPU coverage — see [`docs/gpu-verification.md`](../gpu-verification.md).
- Real SPINEPS-output label-convention round-trip — No committed real-SPINEPS fixture; requires `SEGFACET_SPINEPS_FIXTURE` pointing at a directory of real SPINEPS output. Narrower than the "Real automatic-segmentation failure corpus" row above (Stage 16 sensitivity/DICE scope) — this row is level-**naming** correctness only. Mechanics unconditionally covered by a committed synthetic TPTBox-labeled fixture (`tests/test_097_stage17_validation.py::test_ac4_*`); the real-data path (`test_ac6_real_spineps_fixture_level_names_correct`) is a genuine, cleanly-skipping `skipif` not yet exercised for real.
- Real segmentation-tool run-vs-run per-mode comparison — Only ever exercised on the synthetic corpus and on in-memory perturbed clean spines (item 101's API tests, item 102's CLI replay); no two real segmenter runs exist in this repo. Narrower than the "Real automatic-segmentation failure corpus" row above (that row is Stage 16's per-mode **sensitivity** scope; this row is run-vs-run **attribution** scope).

## Outcome targets

_One row per **measured outcome** the roadmap commits to — an empirical result
(an error rate, a sensitivity floor) that shipped work *enables* but cannot
*guarantee* by construction. Distinct from the Environment-Gated table above,
which asks "did the real path ever run?"; this asks "did the number meet the
bar?" The two are orthogonal: the "Real VerSe GT" row there is `✅ Verified`
(it ran and returned a number) while the G3 target here is `❌ Not met` (that
number missed the bar). Per `.aide/conventions.md` §1, a target **never blocks
its stage** — a stage's ✅ means its planned work shipped — it gates the
**Objective coverage** rows: an objective linked to a target that is not
`✅ Met` cannot roll up to ✅, and `aide check` errors on an objective claimed ✅
over a `❌ Not met` target. `aide status` prints every target not yet Met._

| Target                                                                                                                                                 | Objective | Attempted by                                                        | Status        | Evidence / follow-up                                                                                                                                                                                                                                                                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ | --------- | ------------------------------------------------------------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ≥1 heuristic detects each §6 failure mode on a**real** automatic-segmentation failure corpus (no per-mode sensitivity regression vs synthetic) | G2 | Stage 16 | ❓ Unverified | see trail |
| Held-out real VerSe19 GT (validation + test, disjoint from calibration) yields**FPR ≤ 0.10** | G3 | Stage 14*(Items 089–092)*; **carried forward to Stage 23** | ❌ Not met | see trail |
| No real-GT sensitivity regression vs item 057's synthetic baseline (5/8 pipeline-detectable modes at 1.0) | G7 | Stage 14*(Item 091)*; **carried forward to Stage 23** | ❌ Not met | see trail |

- ≥1 heuristic detects each §6 failure mode on a**real** automatic-segmentation failure corpus (no per-mode sensitivity regression vs synthetic) — No real failure corpus has ever run, so real per-mode sensitivity is unmeasured (item 057's numbers are synthetic-only). Measured when Stage 16 builds/runs the corpus — see the "Real failure corpus" verification row.
- Held-out real VerSe19 GT (validation + test, disjoint from calibration) yields**FPR ≤ 0.10** — **0.90** (validation) / **0.95** (test) after a training-fitted `reference_delta` calibration — far from ≤ 0.10, and a threshold-only fix breaks the G7 target below. Diagnosis: the Stage 14 section. The rework is now **Stage 23** (multivariate normative model), which absorbs the `reference_delta` percentile-derived-threshold insight.
- No real-GT sensitivity regression vs item 057's synthetic baseline (5/8 pipeline-detectable modes at 1.0) — Synthetic corpus: no regression; but real-GT perturbations drop`fragment` to **0.90** and `sequence_break` to **0.8125** (below the 1.0 floor). Closes with the FPR target when Stage 23 reworks the rule mechanism.

---

## Human gates

_One row per decision only a person can make, blocking work until they make it.
Not an acceptance box (those are observable checks of the built thing) and not
an Environment-Gated row (that asks "did the real path ever run?", after the
fact). This asks "may the work start yet?", and the answer is out-of-band._

_Both rows below are the same **kind** of gate: an external-data prerequisite
this repo cannot satisfy from inside itself. Per the 2026-07-25 pivot, the GPU
/ SPINEPS / GSTT half of the programme lives in a separate private repo — so
every real-segmenter and real-clinical input arrives here as a hand-off, on
someone's decision, not as something a loop can go and fetch._

_Resolved only by a person, only via `aide gate approve <n> --evidence "…"`
(or `gate decline`). A decline **keeps blocking** — re-plan instead. No agent
may resolve one._

| Gate | Blocks | Status | Decision / evidence |
|------|--------|--------|---------------------|
| Has spinelab handed over the four-part bundle (candidate descriptor, run manifest, rl1 review labels, split manifest) for the SPINEPS VerSe passes? | stage 16 | ⏳ Awaiting | see trail |
| Is access approved for the curated challenging-case source data (vision.md §8), including clinical cohorts needing ethics or data-sharing sign-off? | stage 16 | ⏳ Awaiting | see trail |
| §6 failure-mode taxonomy — the modes need a specification before the rest of Stage 20 can be built. Six decisions are owed, listed in [`failure-mode-taxonomy-handover.md`](failure-mode-taxonomy-handover.md) §10: the anchor semantics for modes 4 and 7, whether mode 6's `mislabel` firing is a true positive or cross-talk, whether the evidence rung attaches to the mode or the edge, the per-mode schema and lifecycle, whether this becomes a new stage or a Stage 20 rescope, and the `vision.md` §6 wording that currently forbids a `proposed` mode | 139, 140, 141, 142 | ✅ Approved (2026-09-03) | see trail |
| Spinal curve model — the deformity envelope the fit must represent without flagging it. How much scoliotic / kyphotic curvature is normal anatomy the model must follow, versus deviation it must report; and the accepted false-negative cost of a stiffer fit | 119, 120, 121, 123, 125 | ✅ Approved (2026-08-27) | see trail |
| Stage 30 failure-mode specification sign-off — the maintainer reads [`failure_modes.generated.md`](failure_modes.generated.md) entry by entry (raised over the ten-entry item-149 rendering; the review re-organised it on 2026-09-14 and 2026-09-15 into sixteen modes plus the FOV-truncation condition, and all sixteen are what is signed; definition, discriminator, expected firing sets, severity, observability, per-edge evidence rungs, lifecycle status, provenance) and either accepts the rendering or names the entries to change. The date and outcome are then recorded in `src/segfacet/failure_modes.py`'s own docstring, the `feature_docs.py::STATUS_OVERRIDES` precedent | 139, 140, 141, 142 | ✅ Approved (2026-09-15) | see trail |
| Stage 31 D1 — `vision.md` §6 re-issued as v4: the maintainer reads the draft (PR #77, branch `docs/vision-v4-section-6`) and either accepts it or names the passages to change. What it asks: §6 as principles plus a pointer to `segfacet.failure_modes.SPECIFICATION` with no numbered list, the five observability classes, the FOV-truncation condition as a first-class concept, `validated` as the item-150 sign-off defined it, `scope` / `parent` / one defect per mode, the mode → rule direction scored, and the evidence-rungs example corrected to a single rank descent | 152 | ✅ Approved (2026-09-16) | Accepted the v4 section 6 at 7d800a2 on PR #77 |
| Stage 32 selected-mode sign-off — the maintainer reads modes 3 (split vertebra segment) and 4 (islands, disconnected components) as rendered in [`failure_modes.generated.md`](failure_modes.generated.md) and, for each, either signs it off at the fully-specified bar, signs it off at a recorded intermediate state, or names what must change first. Roadmap Stage 32's bar condition 6. The decision brief is in [`items/168-maintainer-sign-off-of-modes-3-and-4.md`](items/168-maintainer-sign-off-of-modes-3-and-4.md): both modes clear `traceability.bar_conditions` 1–5 live (measured 2026-09-20), and the open judgements are whether `fragmentation` is the right home for mode 3's `neighbour_contact` detector, the rule-id-granular co-detection on the `split` case, mode 4's unbuilt `island_distance_from_main_body_mm` grading, and item 167's four `Left open` notes. The date and outcome are then recorded as one `ModeSignOff` per mode in `src/segfacet/failure_modes.py`'s `MODE_SIGN_OFFS` | 168, 169 | ✅ Approved (2026-09-22) | see trail |
| Stage 33 at-the-bar sign-off of modes 3 and 4 — the maintainer re-reads modes 3 (split vertebra segment) and 4 (islands) on the lordotic corpus, as rendered in [`failure_modes.generated.md`](failure_modes.generated.md), with the corpus sheet [`corpus_sheet.png`](corpus_sheet.png) and the rule table [`rules.generated.md`](rules.generated.md), and for each either signs it off at the bar, signs it off at a recorded intermediate state with the reason, or names what must change first. Roadmap Stage 33 D5. The decision brief is in [`items/203-modes-3-and-4-re-signed-at-the-bar.md`](items/203-modes-3-and-4-re-signed-at-the-bar.md): both modes clear `traceability.bar_conditions` 1–5 live (measured 2026-09-29), and the open judgements are that mode 3's `split_own_label` sub-type is expressed only through the `bounds` proxy, that no committed value lies near `neighbour_contact`'s 0.1 contact-fraction threshold because the lordotic base's bodies never touch, and that mode 4's distance grading (`island_distance_from_main_body_mm`), the reason given at gate-bb24, is still unbuilt. The outcome and reason per mode are then recorded as one `ModeSignOff` each in `src/segfacet/failure_modes.py`'s `MODE_SIGN_OFFS`, replacing gate-bb24's two intermediate-state records | — | ❌ Declined (2026-09-30) | see trail |
| Stage 33 at-the-bar sign-off of modes 2 and 3 after the mode 2/3 boundary re-draw — raised when gate-51da was declined (2026-09-30), which moved the selected modes from 3 and 4 to 2 and 3. After items 205–208 have landed, the maintainer reads mode 2 (fused vertebra segments: one label covering its own vertebra plus part or all of a neighbour) and mode 3 (split vertebra segment, re-drawn as the own-label fragment) as rendered in [`failure_modes.generated.md`](failure_modes.generated.md), with the corpus sheet [`corpus_sheet.png`](corpus_sheet.png) and the rule table [`rules.generated.md`](rules.generated.md). For each mode, they either sign it off at the bar, sign it off at a recorded intermediate state with the reason, or name what must change first. Roadmap Stage 33 D5. The decision brief is written into [`items/203-modes-3-and-4-re-signed-at-the-bar.md`](items/203-modes-3-and-4-re-signed-at-the-bar.md) when item 203 is re-specified. The outcome and reason per mode are recorded as one `ModeSignOff` each in `src/segfacet/failure_modes.py`'s `MODE_SIGN_OFFS` | 203, 204 | ✅ Approved (2026-10-02) | modes 2 and 3 are at the bar |
| Stage 27 feature-record taxonomy sign-off — after item 214 has merged, the maintainer reads the design note [`../feature-taxonomy.md`](../feature-taxonomy.md): the record's structure and its rationale, the alternatives considered, every deviation from the scope × kind starting proposal with its reason, the answers to the four known instances (identity fields in several containers, stage3 and image_features beside per_label, image-axis-relative shape features, the reference-delta's feature selection) and to the two inbox questions (where per-component features live, which path owns adjacent-pair spacing), and the mapping table from every feature-catalogue leaf path to its new path and owning migration item. Roadmap Stage 27 D1, criterion 1. Approval releases the per-label migration (item 215), the neighbour-pair and case-level migration (item 216) and the stage validation (item 217). If the signed design departs from the scope axis, items 215 and 216 are re-cut to match it at this gate, as queue 027 was re-cut at gate-51da | 215, 216, 217 | ✅ Approved (2026-10-06) | see trail |
| Adjudicate `sub-verse406_split-verse261` T10 (label 17): is its 18.51 mm held-out spline offset genuine scoliotic anatomy the deformity envelope must accommodate, or a ground-truth labelling artefact? It is the single value that set the shipped `mislabel.max_offset_mm = 13.0` (interior-only p99 12.91 mm, item 123) and the one real scoliotic VerSe19 subject of the 17 selected that fires `mislabel` through the shipped pipeline (item 125, 2026-08-30), which keeps Stage 28's G3 criterion "a real scoliotic curve in the VerSe cohort is not flagged as an offset outlier" unticked. Anatomy means 13.0 mm flags a real curve and the threshold or envelope is revisited before Stage 16 measures `mislabel` sensitivity on real segmenter output; artefact means 13.0 mm stands and the criterion's open state is recorded with that reason. Needs a person looking at the case in a viewer, not more measurement. Moved from the roadmap Backlog 2026-10-09 (insight 2026-08-29-8f8a) | stage 16 | ✅ Approved (2026-10-16) | see trail |

- gate-ae46 — **What satisfies it (restated 2026-10-12):** the four-part hand-off bundle in `spine-failure-lab`'s `docs/project/facet-interface.md` (adopted at `7436b0f`). It holds a `role: candidate` descriptor written by `spinelab` from a run manifest, that run manifest, this repository's ground-truth descriptors (unchanged), and the `spinelab` commit the descriptor and the `rl1` review-label table were written at. SPINEPS alone satisfies it, and TotalSegmentator is no longer sought. Blocks the whole of Stage 16, and transitively Stage 25, whose deliverables are "deliberately unspecified until Stage 16 has characterised real failures". Closes the "Real automatic-segmentation failure corpus" Environment-Gated row and the G2 Outcome target. Not the same prerequisite as the Stage 21 rung-2 corpus, which needs only real VerSe GT — already ✅ Verified and **not** gated.
- gate-2f91 — Independent of the row above: real *segmenter output* does not supply the *challenging cases*, and either arriving alone leaves a Stage 16 deliverable unbuildable. Kept a separate row so approving one does not silently read as approving both.
- gate-0fdd — Adopted failure-mode-taxonomy-handover.md section 12 (2026-09-03) in full. (1) Modes 4 and 7 keep the Stage-18 metric path as anchor and the rule's read path as a separate, separately-labelled column. (2) Mode 6 firing mislabel is a true co-detection: expected_firing = {border, mislabel} for mode6_crop_at_border, with the mode-1 / mode-6 discriminator (a border-touching face) written into the specification. (3) The evidence rung attaches to each mode-to-rule edge, authored; the mode's rung is derived as the strongest edge. (4) The section 6 schema and four-state lifecycle are adopted, with expected_firing authored per corpus case and implemented / validated derived from live state. (5) A new Stage 30 authors the specification and runs before the remainder of Stage 20; items 139-142 are re-specced against it in the queue after Stage 30's. (6) vision.md section 6 is reworded as part of a re-issued vision v3 now, not a point edit: a mode is claimed covered only with the rule(s) that detect it, and a proposed mode is not a claim of coverage. Items 139-142 remain held until Stage 30's specification is signed off.
- gate-2765 — Adopt item 118's proposal: smoothing_spline at s = n_points, chord-length u, leave-one-out evaluation, and max_offset_mm raised 15.0 -> 25.0. Envelope set above the 21.073357 mm leave-one-out ceiling measured across VerSe19 GT including the most coronally-deviated cases, and below the ~5 mm leave-one-out separation a small displacement produces. Accepted cost: a genuine displacement smaller than the envelope may be missed. Expected to be revised into separate normal and scoliotic envelopes later -- see docs/spinal-curve-model.md. *(Superseded 2026-08-29 by a second human decision during item 123: terminal vertebrae (first/last of each subject's ordered sequence) are excluded from the mislabel rule and threshold derivation, and the shipped threshold is `max_offset_mm = 13.0` (interior-only p99 12.91 mm at T10, real 80-subject VerSe19 cohort). Full record in `docs/reference-build.md`'s rebuild records and item 123's spec Decisions log.)*
- gate-fb64 — Reviewed and approved the 16-mode failure-mode catalogue (item 150, revised 2026-09-15, commit ce0c6ec); walkthrough in docs/aide/items/150-maintainer-sign-off-of-the-specification.md
- gate-bb24 — Both modes signed off at a recorded intermediate state, not at the bar. Modes 3 and 4 clear bar conditions 1-5 live (measured 2026-09-20) but the maintainer review of 2026-09-22 (insights.md entries dated 2026-09-22) names what must change before either is signed at the bar: the geometric corpus base is five non-touching axis-aligned boxes, so mode 3's neighbour_contact threshold has no evidence (the only firing value is the fixture's maximum cross-section, every other reading is structurally 0.0); neighbour_contact moves out of fragmentation into its own rule; the split case is re-authored at ~20 percent on a lordotic base with a second own-label sub-type; mode 4's island_distance_from_main_body_mm grading is described but unbuilt. These land as queue 023. Item 169 attests Stage 32 with criterion 1 open and closes Stage 20.
- gate-51da — Neither yet (2026-09-30). Mode 2/3 boundary re-drawn: mode 2 keeps the paired case (a label overreaching onto a neighbour, sub-type (a) today); mode 3 becomes the own-label fragment case only (sub-type (b)). Mode 3 needs its own detector: high label contact fraction plus small volume. Mode 4 needs re-definition: more than one connected component, with small components, or larger components further from the main body; to be refined. Re-planned as new queue-027 items before a fresh sign-off gate.
- gate-0080 — Signed 2026-10-06 after review: one anatomical element order stored as case.sequence.order[]; per-label values stored per label whatever computed them; intensity enters the persisted record (Option A). Scope axis unchanged, items 215/216 not re-cut. docs/feature-taxonomy.md @ 2364df4.
- gate-fac1 — 2026-10-16: neither scoliotic curve anatomy nor a GT labelling error. T10 (label 17) of sub-verse406_split-verse261 is a rare wedge vertebra: its body is minuscule and posterior only, so the neighbouring bodies touch anteriorly. Its 18.51 mm held-out offset is a genuine anatomical outlier and is to be ignored.
- gate-9776 — reworded 2026-10-16, was: Real segmenter output on real CT handed over to this repo — SPINEPS (primary) and/or TotalSegmentator label maps + manifest, produced in the programme repo, sufficient to build the real candidate-vs-GT cohort
- gate-90d9 — reworded 2026-10-16, was: Access approved for the curated challenging-case source data — real pathology / post-op / atypical anatomy ([`vision.md`](vision.md) §8), `VerSe_fracture_grading.xlsx` a natural seed, plus any clinical cohort requiring an ethics/data-sharing sign-off
- gate-6596 — reworded 2026-10-16, was: Is access approved for the curated challenging-case source data (vision.md §8), including any clinical cohort needing an ethics or data-sharing sign-off?

---

# Phase 1 — Complete MVP Pipeline

# Phase 2 — Extensions (after the pipeline is complete)

## Stage 11 — Extensibility & Abnormality Classification Arm (G8) — Deferred — ⏸️

> **Deferred 2026-07-17** (explicit user instruction): prioritise the Phase-3
> real-data validation arm (Stages 14+) ahead of the deferred G8 extensibility
> objective. Not blocked technically — Stage 7 is its only dependency — simply
> not queued. Revisit after Stage 14 (and as needed 15/16) close.

**Goal.** Documented extension path + optional classification arm so handled
abnormalities are accounted for rather than naively flagged.

**Deliverables.**

- ⏸️ Plugin/registration API for new heuristics + abnormality classes.
  - **2026-09-29** → deferred: Stage 11 deferred 2026-07-17 by explicit user instruction: Phase-3 real-data arm (Stages 14+) prioritised; revisit after Stage 14 closes
- ⏸️ Ingestion of human abnormality labels (post-op, fracture, implant); a classification arm
  that informs the heuristics.
  - **2026-09-29** → deferred: Stage 11 deferred 2026-07-17 by explicit user instruction: Phase-3 real-data arm (Stages 14+) prioritised; revisit after Stage 14 closes
- ⏸️ Developer docs: add a heuristic / abnormality class end-to-end.
  - **2026-09-29** → deferred: Stage 11 deferred 2026-07-17 by explicit user instruction: Phase-3 real-data arm (Stages 14+) prioritised; revisit after Stage 14 closes

**Acceptance.**

- [ ] A new heuristic + abnormality class can be added via the documented path in a test.
- [ ] Explicitly-handled abnormalities are not naively flagged (Vision Success Criterion 4) (**G8**).

---

## Stage 15 — Real-XNAT Deployment Validation (G5) — Excluded — ❌

> **❌ Excluded (2026-07-25). Reason:** deployment left this project's scope in the
> [`vision.md`](vision.md) §0 supersession — FACET is a library and CLI, not a deployed
> service, and G5 was **removed from scope**, not deferred. No work was ever started, so
> nothing is lost; the Stage 9 artefacts (`command.json`, `docker/`,
> `docs/deployment.md`) are retained as legacy pending relocation out of this repo.
> **Not reopened.** The deliverables below are the original text, kept as provenance.

**Goal.** Execute what Stage 9 documented: install the container's `command.json`
on a **real XNAT server** and run it on **real session data**, which is what G5's
measurable outcome actually requires. Scoped 2026-07-17 by the over-claim audit.

**Deliverables.**

- 📋 A reachable XNAT instance with the Container Service enabled (test/staging
  acceptable) — **an external prerequisite this project does not currently have**.
- 📋 `command.json` installed + enabled on that server; image pushed/loaded to a
  registry it can pull from.
- 📋 One real XNAT session (scan + segmentation resource) run end-to-end, with QC
  reports landing back as session resources.
- 📋 Deployment doc corrected against whatever the real install actually required
  (Stage 9's steps are written from the XNAT docs, never executed).
- 📋 Verification row flipped with server version + date.

**Acceptance.**

- [ ] The command is installed on a real XNAT server and runs on a real session,
  producing JSON + human reports as session resources (**G5**).
- [ ] The documented install steps match what was actually done (drift corrected).
- [ ] The "XNAT Container Service command on a real server" verification row reads
  ✅ Verified.

---

## Stage 16 — Real Failure Corpus & Sensitivity Validation (G2, G7) — ⏸️

**Goal.** Establish that the heuristics catch failures **that a real segmenter
actually makes**, and build the curated challenging-case corpus
[`vision.md`](vision.md) §8 has always specified but that has never existed.
Scoped 2026-07-17 by the over-claim audit. Depends on Stage 14 (calibrate first,
then measure sensitivity against the calibrated rules).

> **Restated 2026-10-12** against the programme interface the owner adopted
> (`spine-failure-lab`'s `docs/project/facet-interface.md` at `7436b0f`;
> [`roadmap.md`](roadmap.md) Stage 16 and Stage 35):
> - SPINEPS is the only reference segmenter.
> - The candidate descriptor and the `rl1` review labels arrive from `spinelab` as
>   gate `gate-ae46`'s bundle.
> - This repository's side of the interface is Stage 35, a forward dependency, so
>   this stage is ⏸️ until Stage 35 closes.

**Deliverables.**

- ⏸️ **Real candidate cohort**: the SPINEPS VerSe passes, ingested through
  `spinelab`'s candidate descriptor at a recorded `spinelab` commit, and scored
  against real GT.
  - **2026-10-12** → deferred: Waits for Stage 35 (this repository's side of the programme interface, a forward dependency) and for gate-ae46's hand-off bundle from spine-failure-lab; owner decision 2026-10-12. Resumed when Stage 35 closes
- ⏸️ **Modes 2 and 3 against review**: per-level sensitivity and specificity
  against the `rl1` labels on calibration-role cases, reported separately for the
  ranked and random sampling streams. Test-role labels are read once, at the stage
  validation.
  - **2026-10-12** → deferred: Waits for Stage 35 (this repository's side of the programme interface, a forward dependency) and for gate-ae46's hand-off bundle from spine-failure-lab; owner decision 2026-10-12. Resumed when Stage 35 closes
- ⏸️ **Dice-vs-flag correlation** on per-mode findings, which replaces the
  synthetic-only figures in Stage 7's metrics block. The verdict-level figure is
  reported beside it and labelled as dominated by `reference_delta`.
  - **2026-10-12** → deferred: Waits for Stage 35 (this repository's side of the programme interface, a forward dependency) and for gate-ae46's hand-off bundle from spine-failure-lab; owner decision 2026-10-12. Resumed when Stage 35 closes
- ⏸️ A documented account of **which §6 modes SPINEPS produces**, and at what rate,
  with each mode labelled adjudicated, fired but not adjudicated, or untested.
  - **2026-10-12** → deferred: Waits for Stage 35 (this repository's side of the programme interface, a forward dependency) and for gate-ae46's hand-off bundle from spine-failure-lab; owner decision 2026-10-12. Resumed when Stage 35 closes
- ⏸️ **Interface asserted on this side**: a test reads `spinelab`'s committed
  descriptor and `rl1` table at the pinned commit and refuses on version drift.
  - **2026-10-12** → deferred: Waits for Stage 35 (this repository's side of the programme interface, a forward dependency) and for gate-ae46's hand-off bundle from spine-failure-lab; owner decision 2026-10-12. Resumed when Stage 35 closes
- ⏸️ **Curated challenging-case corpus** (behind `gate-2f91`) — real pathology /
  post-op / atypical anatomy (`VerSe_fracture_grading.xlsx` is a natural seed),
  with expected verdicts, to test failure-vs-variation on the cases that actually
  matter.
  - **2026-10-12** → deferred: Waits for gate-2f91 (curated challenging-case source data) and for Stage 35, a forward dependency; owner decision 2026-10-12. Resumed when both are in place
- ⏸️ Verification row flipped with tool version + cohort + date.
  - **2026-10-12** → deferred: Waits for Stage 35 (this repository's side of the programme interface, a forward dependency) and for gate-ae46's hand-off bundle from spine-failure-lab; owner decision 2026-10-12. Resumed when Stage 35 closes

**Acceptance.**

- [ ] ≥1 heuristic fires on a **real** instance of each §6 failure mode that the
  real cohort actually contains; modes absent from real data are recorded as such
  rather than silently credited (**G2**).
- [ ] Real Dice-vs-flag correlation is measured on per-mode findings and correctly signed, with the verdict-level figure reported beside it and labelled as dominated by reference_delta (**G7**, Success Criterion 6).
- [ ] Curated challenging cases run through the pipeline with recorded outcomes;
  legitimate variation is not flagged at the Stage-14 FPR bar.
- [ ] The "Real automatic-segmentation failure corpus" verification row reads
  ✅ Verified.

---

## Stage 17 — Foreign-Convention Interop & Orientation-Safe Image Layer (G2, G6) — ✅

**Goal.** Read another tool's output correctly. `segfacet.labels` currently defines
**25 = `S`, 26 = `Cocygis`, 29 = `L6`**; the TPTBox convention SPINEPS emits reads
**25 = `L6`, 26 = `S1`, 29 = `S2`**. Only 28 (`T13`) agrees, so ingesting SPINEPS output
with today's defaults **silently misreads the sacrum as L6** — no error, plausible
numbers, wrong. Must land before any real-segmenter number is computed.

**Deliverables.**

- ✅ Adopt the TPTBox vertebra standard as the default (`DEFAULT_LABEL_MAP`,
  `CANONICAL_ORDER`); retire the legacy table; keep `LabelConvention` overridable. *(Item 093)*
- ✅ Back `segfacet.io`'s `Volume`/`Case` with TPTBox `NII` (orientation-safe load,
  `reorient`, `rescale`/`resample_from_to`, mm-space, `zoom`/`affine`), replacing the
  hand-rolled `_spacing_from_affine` and keeping the public shape stable. *(Item 094)*
- ✅ Environment migration: `requires-python = ">=3.11"`, numpy as a **range**
  (`>=1.26,<3`), regenerated `constraints.txt`, CI leg per numpy major. *(Item 095)*
- ✅ Run-manifest schema (segmenter version/SHA, weights hash, post-processing toggles,
  seed, dataset id, resolved `numpy`/`TPTBox` versions). *(Item 096)*
- ✅ Stage 17 end-to-end validation: real-segmenter round-trip check + verification-row
  closure. *(Item 097)*

**Acceptance.**

- [x] A regression test asserts labels 25/26/29 match the TPTBox table (**G2**).
  *(Item 093 unit-level; re-confirmed end-to-end via a full `segfacet run` by
  item 097's AC1.)*
- [x] `reference_verse_v1.json` (keyed by vertebra **name**) loads and scores unchanged —
  no re-fit of the 80-subject VerSe19 distribution was required.
  *(Item 093 AC5/AC7; re-confirmed by item 097's AC2.)*
- [x] The suite is green on both numpy majors (**G6**).
  *(Item 095's `test-numpy-majors` CI job runs both legs on every push/PR
  including this item's changes; not independently re-observed by a live CI
  run from this execution environment — no `gh` CLI / CI access available
  here. See item 097's Decisions log.)*
- [ ] A real segmenter output round-trips with correct level names. *(Unticked
  because no real SPINEPS output is available in this execution environment
  — `SEGFACET_SPINEPS_FIXTURE` is unset. The round-trip **mechanics** are
  unconditionally verified via a committed synthetic TPTBox-labeled fixture
  (item 097 AC4); the real-SPINEPS check is a genuine, cleanly-skipping
  `skipif` (item 097 AC5) that has not yet run for real. See the "Real
  SPINEPS-output label-convention round-trip" row in [Environment-Gated
  Capability Verification](#environment-gated-capability-verification).)*

---

## Stage 21 — Real-GT Perturbation Corpus (G3, G7) — ⏸️

**Goal.** Move calibration off hand-crafted geometry. The corpus is built from synthetic
fixtures (five stacked lumbar blocks, 1 mm isotropic); thresholds fitted to it are fitted
to a shape no real spine has, and as the rule set grows, hand-crafted cases increasingly
trip rules they were never meant to exercise. Three rungs of realism, no longer conflated:
**1** hand-crafted fixtures (unit-test scaffolding only) · **2** real GT + scripted
perturbation (*this stage* — calibration, regression, sensitivity) · **3** real segmenter
failures (Stage 16 — validation).

**Deliverables.**

- ⏸️ Existing `Perturbation` operators re-sourced from **real VerSe GT**, with a manifest
  of subject IDs, seeds and operator parameters so the corpus reproduces without
  committing bulk data.
  - **2026-10-07** → deferred: Maintainer decision 2026-10-07 at the queue-029 boundary: under the prototype posture the project moves straight to rung 3 (Stage 16, real SPINEPS output on real VerSe CT) and does not build the rung-2 perturbed-real-GT corpus first; resumed when a Stage 16 measurement needs it
- ⏸️ A real clean-control baseline — a *cohort* false-positive rate, not one synthetic
  pass case.
  - **2026-10-07** → deferred: Maintainer decision 2026-10-07: Stage 16 runs before Stage 21; a cohort false-positive baseline on real GT already exists from Stage 14 (held-out VerSe19, Outcome targets), so this is not a Stage 16 prerequisite
- ⏸️ Threshold calibration and all sensitivity claims moved to rung 2.
  - **2026-10-07** → deferred: Maintainer decision 2026-10-07: Stage 16 runs before Stage 21; calibration claims stay at rung 1 and are labelled so until this stage resumes
- ⏸️ Stage 19's golden decision acted on: retire corpus-snapshot goldens as their cases
  are superseded; do **not** regenerate the nine snapshots against the new corpus.
  - **2026-10-07** → deferred: Maintainer decision 2026-10-07: Stage 16 runs before Stage 21; the golden retirement itself was already executed by Stage 29 D1, so nothing of this bullet is pending today

**Acceptance.**

- [ ] Every threshold-bearing rule is calibrated against rung 2, not rung 1 (**G3**).
- [ ] Stage 20's specificity assertion holds on the new corpus, or each violation is
  recorded with a reason (**G7**).
- [ ] The corpus regenerates reproducibly from its manifest.

---

# Placeholders — authored at the full re-vision

> Stages 22–25 are recorded so numbering stays stable and dependencies can be named.
> **Deliberately not specified** — each depends on measurements that do not exist yet,
> and a stage written before its evidence would be speculation.

---

## Stage 22 — Unified `(scan, seg)` Extraction — 📋

**Goal.** One entry point over the paired scan and segmentation, replacing the current
split between the label-map-only and intensity-aware paths.

**Deliverables.** 📋 *Deliberately unspecified until Stages 17–21 land.*

---

## Stage 23 — Multivariate Normative Model (G3) — 📋

**Goal.** Replace the univariate per-level percentile z-scores aggregated by RMS with a
model that accounts for covariance between features.

**Carries forward** the two `❌ Not met` Outcome targets (held-out real-GT FPR ≤ 0.10; no
real-GT sensitivity regression) and absorbs the open insight that `reference_delta`'s
threshold should derive from the training cohort's own percentiles rather than a hand-set
constant — the fixed-constant mechanism is what cannot clear the FPR target without
sacrificing sensitivity.

**Deliverables.** 📋 *Deliberately unspecified until real-segmenter measurements exist.*

---

## Stage 24 — Failure-Mode Discovery & Typed Reference Set (G8) — 📋

**Goal.** Cluster the feature space to surface failure modes absent from the §6 catalogue;
curate per-class exemplars a new case can be assigned against.

**Deliverables.** 📋 *Deliberately unspecified until Stage 21's corpus exists.*

---

## Stage 25 — Segmenter-Native Perturbations (G2) — 📋

**Goal.** Rung 3's generator — perturbations derived from what a real segmenter actually
does wrong, rather than from a catalogue written in advance.

**Deliverables.** 📋 *Deliberately unspecified until Stage 16 has characterised real
failures.*

---

# Stages scoped 2026-08-11

> Numbered after the placeholders so numbering stays stable; both run earlier than their
> numbers suggest. Full statements in [`roadmap.md`](roadmap.md).

---

## Stage 26 — Carried-Defect Remediation (pre-real-data) (G2, G7) — ✅

**Goal.** Clear the defects Stages 17–19 recorded but were (correctly) forbidden from
fixing in scope, **before** Stage 20 audits those surfaces and before Stage 21 produces
real-data numbers. Every deliverable is a diagnosed defect with a named location — no
discovery.

**Deliverables.**

- ✅ **D1** `normalised_delta` saturates to ±1.0 whenever one run sits on baseline (7 of 8
  metric baselines are `0.0`), so Stage 18's run-vs-run attribution is decided by the
  lowest-mode tie-break rather than by magnitude. `eval/per_mode_cohort.py`. *(Item 109)*
- ✅ **D2** `touches_*` face mapping is anatomically wrong under RAS since item 094
  (`x == 0 → touches_inferior` names the left-right axis) — every `border`/`fov` finding on
  data read through `segfacet.io` is mislabelled. Must land before real data. *(Item 108)*
- ✅ **D3** Golden-fixture test hygiene: `tests/golden/*.json` unpinned in `.gitattributes`
  (latent Windows-CI break); `test_022_stage3_serialisation.py::test_ac8_golden_snapshot`
  writes its own golden and skips when missing, so deleting the file makes it pass.
  *(Item 111)*
- ✅ **D4** `compute_per_mode_metrics` gains an optional `overlap_result=` (halves the
  overlap work of a cohort-scale per-mode run). *(Item 112)*
- ✅ **D5** `test-numpy-majors` scoped off the Docker/PyRadiomics-gated modules. *(Item 113)*
- ✅ **D6** `heuristics/bounds.py` comments still name the retired `S` / `Cocygis` labels.
  *(Item 114)*
- ✅ **D7** Stage 17's acceptance box contradicts its own annotation — maintainer's call
  between untick / reword / third state. *(Item 114)*
- ✅ **D8** `features/neighbourhood.py` is dead wiring: implemented in full, referenced by
  nothing, yet Stage 3 claims it "flags isolated anatomical outliers" ✅. Wire it or retire
  it and correct the claim. Generalised to a named-feature API and wired into
  `extract_feature_record`/`feature_report.py` as `stage3.per_label_neighbourhood[]`
  (status "unwired" — computed and serialised, consumed by no rule); the Stage 3 claim is
  corrected above. *(Item 110)*
- ✅ **D9** The `_PRE_NNN_*` byte-hash scope fences (items 099/100/101/103/105, plus item
  106's `progress.md` row digests) encode a diff-time property as a permanent runtime
  invariant: six documented failures, no recorded true positive, and a re-pin toll on every
  later item that edits source. Retire them and land the deterministic diff-based scope
  check they were reaching for. *(Item 107)*
- ✅ **D10** `synth/` implements a documented array-axis convention (axis 0 = superior-
  inferior) that D2's affine-derived mapping replaces; migrate the synthetic corpus
  RAS-native (bodies along axis 2, truthful affine, load as array-identity) and
  regenerate fixtures, manifest and goldens. *(Item 116)*
- ✅ Stage 26 end-to-end validation: per-defect red-then-green replay, fresh-clone suite
  run, fence-retirement audit, and verification-row closure. *(Item 115)*

**Acceptance.**

- [x] Each defect has a regression test that fails before its fix (**G7**).
  *(Item 115: the pinning test for each of items 107-114/116 is named in a
  table in item 115's Decisions log; red-then-green was directly observed in
  a scratch tree, then reverted, for items 108/109/111 — the three
  cheapest-to-stage defects per the item's Assumptions — and items
  107/110/112/113/114/116 were verified by inspection of their own committed
  tests, per the same Assumptions' documented trade-off.)*
- [x] `border`/`fov` findings carry anatomically correct face names under RAS (**G2**).
  *(Item 115: a real `segfacet run` on `tests/corpus/fixtures/mode6_crop_at_border_seg.nii.gz`
  emitted "Partial vertebra clipped by FOV: label 22 (L3) touches image
  face(s): anterior", matching the perturbation's actual crop face.)*
- [x] Per-mode attribution distinguishes a large move from a small one on a fixture built
  to have both.
  *(Item 115: a real `compare_runs()` call with mode 1 = 0.1 / mode 4 = 0.9
  attributed mode 4; reversing to mode 1 = 0.9 / mode 4 = 0.1 attributed
  mode 1 — attribution followed magnitude both ways, not mode number.)*
- [x] `neighbourhood.py` is reachable from `extract_feature_record` and present in the
  regenerated catalogue, or removed with Stage 3's deliverable reworded.
  *(Item 115: `extract_feature_record` populates `stage3.per_label_neighbourhood`
  and `catalogue.build_catalogue()` lists those entries with `status: "unwired"`,
  confirmed by `tests/test_115_stage26_validation.py`'s AC7 tests, 4/4 passing.)*
- [ ] No `_PRE_NNN_*` byte-hash fence remains, and the diff-based scope check that replaces
  it flags a deliberately out-of-scope edit on a scratch branch (**G7**).
  *(Unticked because one `_PRE_NNN_*`-named byte-hash fence still remains --
  `tests/test_098_stray_components.py`'s `_PRE_098_REFERENCE_VERSE_V1_SHA256`,
  outside this item's authorised paths to retire -- even though the diff-based
  checker's out-of-scope-detection half is independently verified live on a
  scratch branch (AC10). See item 115's Decisions log for the full AC8 audit
  and why this box is left honestly unticked rather than ticked around.)*
  *(2026-09-01, from insights.md's item-128 entry of 2026-08-31: the box's `_PRE_NNN_*`
  naming-pattern wording is no longer a faithful key — item 128 renamed
  `_PRE_098_REFERENCE_VERSE_V1_SHA256` to `_RELEASED_REFERENCE_VERSE_V1_SHA256`, so no
  `_PRE_NNN_*`-shaped name survives in `tests/` while the digest-literal fence itself is
  intact. The box is judged by the mechanism —
  `tests/test_115_stage26_validation.py::test_ac8_no_hardcoded_literal_fence_remains`
  classifies by AST shape and still reports one fence, legitimate because
  `reference_verse_v1.json` is not regenerable in CI and its digest is the only guard — and
  stays unticked on that reading, not on the name.)*

---

## Stage 29 — Golden Retirement & Test-Artifact Hygiene (G2, G7) — ✅

**Goal.** Execute the maintainer-signed retirement of the 11 whole-record snapshot goldens
(`golden-decision-table.md`, dispositioned *retire* 2026-07-28, execution pulled forward
from Stages 21/27), make committed-artifact comparisons reach for numeric tolerance by
construction, and sweep the located defects the queue-017 triage routed to
[`roadmap.md`](roadmap.md)'s Stage 29 — see there for the full deliverable list and
per-deliverable provenance.

**Deliverables.**

- ✅ **D1** The golden retirement executed: nine `tests/corpus/golden/*.json` and two
  `tests/golden/` snapshots gone, the four per-row replacements in place, nothing
  regenerated on the way out. *(Item 126)*
- ✅ **D2** Tolerance by construction: shared committed-artifact comparison helper plus an
  enforcing guard extending `tests/test_111_golden_guard.py`'s byte-exact allowlist.
  *(Item 127)*
- ✅ **D3** The `reference_verse_v1` integrity pin relocated to a test named for the
  artifact (its `.gitattributes` pin carried across) and the `test_102` fence header
  renamed to say what it checks. *(Item 128)*
- ✅ **D4 + D5** Coincident centroids degrade to a report instead of a traceback at the
  pipeline level (the fit's descriptive error already exists — item 119 AC16), and the
  4-centroid held-out fallback boundary moves to `< 5` with the affected reference
  distributions rebuilt. *(Item 129)*
- ✅ **D6** Spline plumbing consolidation: one closest-point search, one in-sample fit per
  case. *(Item 130)*
- ✅ **D7** `tangent_angles_deg[]` traversal-direction normalisation to item 122's
  convention. *(Item 131)*
- ✅ **D8** `consistency.py` monotonicity judged against the smoothed fit so mode 4 fires.
  *(Item 132)*
- ✅ **D9 + D10** The `tptbox` ≥ 0.7.6 pin (non-AGPL metadata), and
  `refresh_reference.py --verse-cohort` delegated to `rebuild_verse_reference.py` or
  retired. *(Item 133)*
- ✅ **D11** The decision table's live `N/M leaf paths unwired` counts split into a
  generated, byte-reproducible companion the signed document references. *(Item 134)*
- ✅ Stage 29 end-to-end validation: retirement audit, guard replay on a scratch branch,
  mode-4 replay closing Stage 28's unticked acceptance half, fails-before-the-fix
  verification per defect, fresh-clone suite. *(Item 135)*

**Acceptance.**

- [x] All 11 retired snapshots are gone with their named replacements in place, and no
  snapshot was regenerated on the way out; the guard fails a deliberately added byte-exact
  comparison against a committed float-carrying artifact (**G7**). *(Item 135's 2026-08-31
  replay: all eleven paths — nine `tests/corpus/golden/{clean_control,mode1_displace,
  mode2_fragment,mode3_inject_islands,mode4_relabel_swap,mode5_remove_level,
  mode6_crop_at_border,mode7_sequence_break,mode8_force_overlap}.json` plus
  `tests/golden/016_features_report.json` and `tests/golden/022_stage3_report.json` — are
  absent from the tree, and `git log --follow --name-status` over `69e5cf5..HEAD` shows
  each path's most recent history entry is a single `D` at commit `cafd4cc`, with no later
  `A`/`M`. The four named replacements resolve to live code: intra-run determinism in
  `test_042`/`test_098`/`test_016`/`test_022` (none reads a `tests/corpus/golden` path);
  `test_126_golden_retirement.py::test_ac3_fresh_report_validates_against_schema`;
  `test_098_stray_components.py::test_ac15_golden_verdict_and_findings_unchanged`; and the
  shared `tests/golden/report_format_contract.json` built by `tests/report_format_fixture.py`,
  the sole survivor under `tests/golden/`. On a scratch branch in a throwaway clone,
  deleting that fixture made `test_016_features_json.py::test_ac5_golden_snapshot` fail
  with a `FileNotFoundError` naming the missing file rather than self-healing; on the same
  scratch branch, adding a real `dest.read_bytes() == Path("src/segfacet/reference/
  reference_default.json").read_bytes()` comparison under `tests/` made
  `test_127_committed_artifact_tolerance.py::test_ac15_classifier_reports_zero_violations_on_tests_tree`
  fail, its message naming `assert_matches_committed_artifact`; the scratch branch was
  discarded afterward and the working checkout was never touched. Committed whole-record
  snapshot inventory: 11 → 0, with one shared, feature-value-free format fixture surviving
  under `tests/golden/`.)*
- [x] `mode4_relabel_swap` yields `is_monotonic == False` through `extract_feature_record`,
  closing Stage 28's unticked mode-4 acceptance half (**G2**). *(Item 135's 2026-08-31
  replay: `extract_feature_record` on the committed `mode4_relabel_swap` fixture reads
  `stage3.monotonic_consistency.is_monotonic == False` with
  `non_monotonic_pairs == [["L2", "L3"]]`; a real `segfacet run --scan
  tests/corpus/fixtures/base_scan.nii.gz --seg
  tests/corpus/fixtures/mode4_relabel_swap_seg.nii.gz --out <scratch> --no-reference` exits
  `0` and its `segfacet_report.json` carries the same reading plus a `mislabel` finding
  naming labels 21/22. `clean_control` reads `is_monotonic == True` with empty
  `non_monotonic_pairs` and fires zero findings through both paths, so the tick is not
  bought at the clean control's expense. `tests/corpus/manifest.json`'s pipeline-detected
  mode count is now **7 of 8** (mode 4 moved in at item 132; mode 8 remains
  `reconstructed_record`), agreeing with `test_040`'s and `test_057`'s mode-set constants —
  up from 6 of 8 at Stage 28's close.)*
- [ ] A 4-level field of view yields non-degenerate held-out offsets; `pip show tptbox`
  reports a non-AGPL licence; each fixed defect carries a regression test that fails
  before the fix (**G7**). *(Unticked — item 135's 2026-08-31 replay: the `pip show tptbox`
  clause and the fails-before-the-fix clause are both **verified**, and this box is
  unticked **solely** on the four-level clause below, not on either of those two. `pip show
  tptbox` in the project venv reports `Version: 0.7.6` and `License: Apache License Version
  2.0, January 2004` (neither `agpl` nor `affero`), matching both `pyproject.toml`'s and
  `constraints.txt`'s `tptbox==0.7.6` pins. In a throwaway clone, all eight designated
  regression-test nodes for items 129/131/132/133 fail at each implementation commit's
  immediate parent (`1466b8b`←`021f0bc`, `8b94e62`←`5efd27d`, `628f673`←`cc22bfd`,
  `26b5cf5`←`8586772`) — confirmed by execution, not assumed. The four-level clause itself
  is re-measured and remains **unmeetable**: a synthetic 4-level curve with an interior
  level displaced 15 mm reproduces item 129's exact degenerate array `[7.348609152784843e-05,
  5.330684370393181e-06, 5.740531122353952e-06, 3.782179445898854e-05]` mm (all `< 0.001`
  mm), while the same displacement at 5 and 6 levels separates well above that floor — at
  exactly four points a cubic (`k = 3`) spline has exactly four coefficients and
  interpolates all four points regardless of weights, so the "held-out" curve is
  numerically the in-sample curve. Closing this needs the fit's degree clamped below
  `n − 1` at small `n`, which changes the formulation the 2026-08-27 "Spinal curve model —
  the deformity envelope" human gate approved (`✅ Approved`, blocking nothing today); see
  `docs/aide/items/129-coincident-centroids-in-the-pipeline.md`'s Decisions log and
  `src/segfacet/features/spline_offset.py`'s docstring limitation block for the standing
  evidence. No agent resolves that gate.)*

---

# Stage scoped 2026-09-03 (queue-019 boundary feedback loop)

> Same construction as Stages 26–29: numbered for stability, **runs next, ahead of the
> remainder of Stage 20**. Full statement in [`roadmap.md`](roadmap.md).

---

# Stages scoped 2026-09-15 (after Stage 30's sign-off)

> Numbered for stability; **both run before Stages 27, 21 and 16**. Full statement in
> [`roadmap.md`](roadmap.md).

---

# Stage scoped 2026-09-22 (after queue-022's maintainer review)

> Numbered for stability; **runs before Stages 27, 21 and 16**. Full statement in
> [`roadmap.md`](roadmap.md).

---

# Stage scoped 2026-10-09 (queue-029 boundary roadmap triage)

> The one standing maintenance stage. Full statement in [`roadmap.md`](roadmap.md).

---

## Stage 34 — Maintenance — ✅

**Goal.** Repair shipped work by closing insight-derived `defect`, `gap` and
`automation` entries in maintenance queues.

**Deliverables.** Each maintenance queue adds one bullet per item.

- ✅ One inter-centroid-spacing rule for modes 2 and 6. *(Item 218)*
- ✅ One check per failure mode for label order and label-set gaps. *(Item 219)*
- ✅ A collapsed label set no longer passes silently. *(Item 220)*
- ✅ Held-out spline offset with every outlier withheld. *(Item 221)*
- ✅ Held-out spline offset at the ends of the sequence. *(Item 222)*
- ✅ Path-aware rule-read attribution in the catalogue. *(Item 223)*
- ✅ Platform-sensitive comparisons tolerant, determinism checks exact. *(Item 224)*
- ✅ Three test guards that see only half of what they guard. *(Item 225)*
- ✅ Two owner-decided retirements: `sagittal_projection` and the CI `scope-check` job. *(Item 226)*
- ✅ Stale descriptions of shipped behaviour, and the path-position end clamp. *(Item 227)*
- ✅ Stage archive made safe, then run. *(Item 236)*
- ✅ Dead code and stale comments left by items 210, 223 and 227. *(Item 237)*
- ✅ Threshold literals in pinned reasons compared exactly. *(Item 238)*
- ✅ The corpus sheet regenerated with the manifest. *(Item 239)*
- ✅ VerSe19 probes behind items 218 and 220. *(Item 240)*

---

## Stage 35 — Programme Interface: the SegFACET Side (G2, G3, G7) — 🚧

**Goal.** FACET can read everything the programme repository will hand it for
Stage 16, and writes reports that repository can pin. Scoped 2026-10-12, when the
owner adopted `spine-failure-lab`'s `docs/project/facet-interface.md` at
`7436b0f`. It needs no hand-off and runs before Stage 16.

**Deliverables.**

- ✅ **Case-id-list subsets**: descriptor `subsets` can be an explicit list of case
  ids as well as a directory root. *(Item 228)*
- 🔍 **VerSe20 ground-truth descriptor** beside `verse19.yaml`, and both descriptors
  carry `development`, `calibration` and `test` subsets over the release splits. *(Item 229)*
- 📋 **Real-label expectation**: the evaluation cohort accepts a per-label
  expectation with several modes per case, read from `spinelab`'s `rl1` table
  against a vendored schema pinned at a `spinelab` commit. Any other version is
  refused. *(Items 230, 231)*
- 📋 **Artefact versioning**: a release tag on every revision `spinelab` consumes,
  the FACET commit written into every per-case and evaluation report, and a
  report `schema_version` that moves whenever a feature path moves. *(Items 232, 233)*
- 📋 **Development-role reference**: the VerSe reference rebuilt from the VerSe19
  and VerSe20 training splits, and `spline_offset.max_offset_mm` re-derived from it
  with the wedge-vertebra outlier `sub-verse406_split-verse261` T10 excluded
  (`gate-fac1`). *(Item 234)*
- 📋 Stage validation from a clean clone. *(Item 235)*

**Acceptance.**

- [ ] A descriptor whose subsets are case-id lists resolves exactly those cases,
  and the VerSe19 and VerSe20 descriptors resolve the three role subsets over the
  release splits (**G7**).
- [ ] An `rl1` table at the pinned version becomes a per-label,
  several-modes-per-case expectation the evaluation harness scores against, and a
  table at any other version is refused (**G2**).
- [ ] Every per-case and evaluation report carries the FACET commit and a schema
  version, and a feature path that moves without a schema-version change fails
  the suite (**G7**).
- [ ] The rebuilt reference draws only on development-role cases, and no
  calibration-role or test-role case contributes to it (**G3**).
- [ ] `spline_offset.max_offset_mm` is re-derived from the rebuilt distribution, and
  the excluded wedge-vertebra label contributes nothing to it (**G3**).
