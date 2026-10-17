<!-- aide-template: roadmap 3 -->
# FACET — Development Roadmap

> **Status:** v3.5 (2026-10-12: programme interface adopted against
> [`vision.md`](vision.md) v4.2, Stage 35 added for this repository's side of it, and
> Stage 16 restated as the real measurement behind it; v3.4 2026-10-12: Stage 34 and the
> Backlog conformed to roadmap template 2, engine 2.47.3; v3.3 2026-10-09: Stage 34 — Maintenance added as the one standing
> maintenance stage, the Carried defects section removed with its live entries returned to
> `insights.md`, the Backlog pruned to ideas only; v3.2 2026-09-22: Stage 33 added after queue-022's review, Stage 32 annotated;
> v3.1 approved 2026-09-15: Stages 31–32 added, Stages 20 and 30 annotated after
> item 150's sign-off; v3 approved 2026-09-03) · **Created:** 2026-06-24 · **Re-issued:** 2026-09-03 against
> [`vision.md`](vision.md) v3 (incremental update; every completed or in-progress stage is
> carried over unchanged). Stages 0–14 are history and are not reopened; Stage 15 is
> `❌ Excluded`; Stage 16 was retargeted in place; Stages 22–25 remain placeholders,
> deliberately unspecified until real segmenter failures have been measured.
> Step 2 of the AIDE loop. Derived from [`vision.md`](vision.md). Breaks the
> vision into incremental, demonstrable, locally-deployable stages (~1 week each).

> **Run order from here (2026-10-12): 35 → 16 → (21 when a Stage 16 measurement needs it).**
> The owner adopted the programme interface (`spine-failure-lab`'s
> `docs/project/facet-interface.md` at `7436b0f`). This repository's side of it is Stage 35,
> which needs no hand-off and runs first. Stage 16 keeps the real measurement and waits, ⏸️,
> for Stage 35 and for gate `gate-ae46`'s bundle. The reasons for going straight to rung 3,
> given below, still hold.
>
> **Run order 2026-10-07 (superseded): 16 → (21 when a Stage 16 measurement needs it).**
> Stage 27 closed with queue 029 on 2026-10-06. At that boundary the maintainer decided,
> under the prototype posture, to go straight to rung 3 — real SPINEPS output on real VerSe
> CT, Stage 16 — and **defer Stage 21** (rung 2, real GT + scripted perturbation) rather
> than build it first. The reasons: the SPINEPS passes over VerSe19 and VerSe20 already
> exist in the programme repository (gate `gate-ae46`'s prerequisite), rung 2 adds nothing
> a rung-3 measurement cannot say more directly about what real segmenters produce, and a
> cohort false-positive baseline on real GT already exists from Stage 14. Stage 16's
> *Dependencies* on Stage 21 is therefore lifted: it now rests on Stages 13, 14, 18 and 20
> only, and every calibration claim stays labelled rung 1 until Stage 21 resumes. The
> curated-challenging-case deliverable of Stage 16 stays behind gate `gate-2f91` and is
> queued only once that gate is approved.
>
> **Run order 2026-09-22 (superseded): 33 (closing Stage 32's criterion 1) → 27 → 21 → 16.** Stages are numbered for stability and
> several run earlier than their numbers suggest — Stages 26, 28 and 29 ran before Stage 20
> because they changed what it audits, and Stage 30 does the same; Stages 31 and 32 run
> before Stage 27 because the catalogue item 150 signed off must settle, mode by mode,
> before the feature schema is re-taxonomised or real data is measured against it. This
> line is the one place the order is stated; each stage's *Dependencies* names what blocks
> it, and [`progress.md`](progress.md) records what has actually landed.
>
> Stage 33 runs next because queue-022's review found the corpus Stage 32 measured on
> cannot express what its rules decide; it re-grounds that corpus before any mode is
> signed at the bar.
>
> *(Superseded run orders: 2026-09-15, 30 (item 151) → 31 → 32 with Stage 20's remainder
> → 27 → 21 → 16; 2026-09-03, 30 → 20 (remainder) → 27 → 21 → 16.)*

> **Build posture (2026-09-18).** [`vision.md`](vision.md) carries
> `**Posture:** prototype` from engine 1.59.0 on (`.aide/conventions.md` §1 →
> vision.md): a stage is built only where a success criterion needs it, a queue holds
> no preparatory or "for later" items, and an item spec carries acceptance criteria
> for its own deliverable only. The planned stages were written before the line
> existed and are read through it. The run order above is unchanged. What the posture
> changes is recorded as a dated annotation at the top of each stage it touches:
> Stage 21, Stages 22–25, Stage 27 and Stage 32's D0. Started stages are untouched.

> **Reading older annotations.** Sections below that cite `vision.md` §0 refer to v2's
> supersession note of 2026-07-25, which v3 retired; that text is recoverable from git
> history (v2 at commit `c519608`). A stage's supersession is marked **both** in the
> superseding stage and, from 2026-09-03, as a dated annotation at the top of the
> superseded stage — so a stage read top-down no longer yields a stale plan.

---

## Strategy

1. **MVP first, complete the pipeline, then extend.** Phase 1 builds a thin
   end-to-end slice and grows it into the *complete local QC pipeline*
   (I/O → features → heuristics → verdict → report → evaluation). Phase 2 only
   begins once that pipeline is complete and calibrated.
2. **Initial focus = image processing + simple heuristics.** The feature-
   extraction core (geometric/topological processing of the label maps) and the
   explainable rule engine are the heart of Phase 1.
3. **Containerisation comes after** the pipeline is complete — XNAT/Docker (G5),
   GPU acceleration (G6), and the extensibility/classification arm (G8) are
   **Phase 2** extensions.
4. **Prioritised objectives: G1, G2, G3, G4, G7.** Phase 1 delivers all five.

> **Scope decision (confirmed 2026-06-24):** "image processing" in Phase 1 means
> the **geometric/topological feature engine** (volumes, components, centroids,
> spline) that the §6 failure-mode heuristics actually need. **Richer image-based
> / radiomics intensity features** are a Phase 2 enhancement (Stage 8), since the
> catalogued failure modes are predominantly geometric and the MVP stays minimal.

### Objective → stage coverage

| Objective                                       | Delivered by                                                                                                             |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| G1 Detect empty / trivially-failed              | Stage 1                                                                                                                  |
| G2 Detect catalogued failure modes (§6)        | Stages 4, 5, 18, 28 (specification: **Stage 30**; per-mode refinement: **Stage 32**, re-grounded and taken to the bar by **Stage 33**; traceability and specificity: **Stage 20**, interleaved into 32; real failures: **Stage 16**, read through the programme interface of **Stage 35**) |
| G3 Distinguish failure from variation           | Stages 6, 7 (real-VerSe grounding: Stage 12;**recalibration: Stage 14**; development-role reference: **Stage 35**; normative model: the multivariate-normative-model placeholder, not yet specified)                |
| G4 Per-case and cohort reports                  | Stage 1 (extended by 2–4); cohort characterisation: Stage 18                                                          |
| G7 Evaluable & regression-testable              | Stages 5, 7 (real-VerSe evaluation: Stage 12;**real data: Stages 14, 16**; corpus rework: **Stages 19–21, 29, 32, 33**; eval-harness re-key: **Stage 31**; dataset roles and artefact versioning: **Stage 35**) |
| *(out of scope 2026-07-25)* G5 Deploy on XNAT | Stage 9 shipped the artefacts;**Stage 15 `❌ Excluded`** — see `vision.md` v3 §11                             |
| *(deferred)* G6 Portable / GPU                | Stage 10                                                                                                                 |
| G8 Extensible / classification                  | Stages 19, 27, **30** (the add-a-mode path), **31** (§6 re-issue), **32**, **33** (per-mode sign-off); classification arm: Stage 11 *(deferred)* |

> **Stages 14–16 exist because building ≠ validating.** Stages 0–13 deliver and
> synthetically verify the whole pipeline, but several objectives' measurable
> outcomes name **real** data or environments — real VerSe GT (G3, G7), real
> session data (G5), real segmentation failures (G2) — and are demonstrated only
> where real data has judged them. On real held-out VerSe GT the pipeline's
> false-positive rate is **0.925** (against a synthetic 0.0), so G3 is not yet
> met. Stages 14/15/16 are the real-data validation arm for G3, G5, and G2/G7
> respectively — see [`progress.md`](progress.md)'s "Two kinds of done" section.
> These stages do not reopen any earlier stage's code; they validate outcomes the
> earlier stages' synthetic tests could not.

### Stage dependency graph

```
0 ─► 1 ─► 2 ─► 3 ─► 4 ─► 5 ─► 7        (Phase 1: complete MVP pipeline)
              └────────► 6 ─┘
                              
Phase 2 (after 7):  8 (img features) · 9 (XNAT) · 10 (GPU) · 11 (extensibility)
                    12 (real-VerSe grounding & reference feature expansion)
                    13 (dataset ingestion adapters & harmonization schema)

Phase 3 — real-data validation (the outcome arm; needs real data/environments):
                    12 ─► 13 ─► 14 (recalibrate on real GT)  ─► 16 (real failures)
                                 9 ─► 15 (real XNAT server)
```

> **Stage 12** deepens Stages 6/7 (G3, G7): it was scoped after those stages
> shipped on a *synthetic* VerSe stand-in. It depends only on Stage 7 and is
> independent of Stages 8–11, so it may be prioritised ahead of the GPU (10) /
> extensibility (11) extensions.

> **Stage 13** generalises dataset ingestion behind a dataset-agnostic
> `Cohort`/`Case` interface plus declarative per-dataset adapters, so real
> cohorts in varied on-disk layouts / naming conventions (VerSe19/20,
> TotalSegmentator or SPINEPS outputs, …) are ingested through one interface
> rather than hand-staged. It depends on Stages 6/7 and **unblocks the
> real-data half of Stage 12** (building `reference_verse_vN` from real GT and
> evaluating held-out real GT through the clean interface). Scoped 2026-07-16
> after Stage 10 was verified on real GPU hardware and real VerSe data was
> mounted.

---

# Phase 1 — Complete MVP Pipeline (priority: G1–G4, G7)

## Stage 0 — Project Scaffolding & I/O Foundation

Archived in [roadmap/stage-0.md](roadmap/stage-0.md).

---

## Stage 1 — End-to-End Thin Slice: Empty Detection + Report (G1, G4)

Archived in [roadmap/stage-1.md](roadmap/stage-1.md).

---

## Stage 2 — Geometric & Topological Feature Extraction (image-processing core)

Archived in [roadmap/stage-2.md](roadmap/stage-2.md).

---

## Stage 3 — Spinal Curve: Spline Fit & Geometric Deviation Features

Archived in [roadmap/stage-3.md](roadmap/stage-3.md).

---

## Stage 4 — Heuristic Rule Engine over the Failure Modes (G2)

Archived in [roadmap/stage-4.md](roadmap/stage-4.md).

---

## Stage 5 — Synthetic Failure Corpus & Regression Suite (G7)

Archived in [roadmap/stage-5.md](roadmap/stage-5.md).

---

## Stage 6 — VerSe Reference Distributions & Delta-to-Reference Rules (G3)

Archived in [roadmap/stage-6.md](roadmap/stage-6.md).

---

## Stage 7 — Evaluation, Calibration & Metrics (G3, G7) — *Phase 1 complete*

Archived in [roadmap/stage-7.md](roadmap/stage-7.md).

---

# Phase 2 — Extensions (after the pipeline is complete)

## Stage 8 — Image-Based / Radiomics Features

Archived in [roadmap/stage-8.md](roadmap/stage-8.md).

---

## Stage 9 — Containerisation & XNAT Container Service Command (G5)

Archived in [roadmap/stage-9.md](roadmap/stage-9.md).

---

## Stage 10 — Portable Compute: GPU Acceleration Path (G6)

Archived in [roadmap/stage-10.md](roadmap/stage-10.md).

---

## Stage 11 — Extensibility & Abnormality Classification Arm (G8)

**Goal.** A documented extension path plus an optional classification arm so
handled abnormalities are accounted for rather than naively flagged.

**Deliverables.**

- Plugin/registration API for new heuristics + abnormality classes.
- Ingestion of human abnormality labels (post-op, fracture, implant); a
  classification arm that informs the heuristics.
- Developer docs: add a heuristic / abnormality class end-to-end.

**Dependencies.** Stage 7 (and Stage 8 for image features).

**Validation / acceptance.**

- A new heuristic + abnormality class can be added via the documented path in a
  test.
- Explicitly-handled abnormalities are not naively flagged (Vision Success
  Criterion 4) (**G8**).

---

## Stage 12 — Real-VerSe Grounding & Reference Feature Expansion (G3, G7)

Archived in [roadmap/stage-12.md](roadmap/stage-12.md).

---

## Stage 13 — Dataset Ingestion Adapters & Harmonization Schema (G3, G7 enabler)

Archived in [roadmap/stage-13.md](roadmap/stage-13.md).

---

# Phase 3 — Real-Data Validation (the outcome arm)

> Stages 0–13 answer *"did we build it correctly?"* — on synthetic fixtures,
> goldens, and unit tests. Phase 3 answers *"does it work on reality?"*, which
> is what [`vision.md`](vision.md) §2's measurable outcomes actually ask. These
> stages are gated on **real data and real environments**, not on more code, and
> each one closes a specific objective that is currently 🚧.

## Stage 14 — Real-Data Grounding & Heuristic Recalibration (G3, G7)

Archived in [roadmap/stage-14.md](roadmap/stage-14.md).

---

## Stage 15 — Real-XNAT Deployment Validation (G5) — ❌ Excluded

> **❌ Excluded (2026-07-25). Reason:** deployment left this project's scope in the
> `vision.md` §0 supersession — FACET is a library and CLI, not a deployed service, and
> G5 was removed from scope rather than deferred. Nothing here was attempted, so no work
> is lost; the Stage 9 artefacts (`command.json`, `docker/`, `docs/deployment.md`) are
> retained as legacy pending relocation out of this repo. **This stage is not reopened.**
> Everything below is the original text, kept as the provenance trail.

**Goal.** Do what Stage 9 documented. G5's measurable outcome is *"Runs as an
XNAT Container Service command on **real session data**"*; Stage 9 shipped a
validating `command.json`, an entry script, deployment docs, and a CI-verified
`docker build`/`docker run` — but nothing has ever touched an XNAT server. The
install steps were written from the XNAT documentation and never executed.

**Deliverables.**

- A reachable XNAT instance with the Container Service enabled (test/staging is
  fine). **This is an external prerequisite the project does not currently
  have** — the stage is blocked on access, not on engineering.
- Image published where that server can pull it; `command.json` installed +
  enabled.
- One real session (scan + segmentation resource) run end-to-end, reports landing
  back as session resources.
- Deployment docs reconciled with what the real install actually required.

**Dependencies.** Stage 9 (✅). Blocked on XNAT server access.

**Validation / acceptance.**

- The command runs on a real XNAT session, producing JSON + human reports as
  session resources (**G5**).
- The documented install steps match what was actually done.
- The "XNAT Container Service command on a real server" verification row reads
  ✅ Verified.

---

## Stage 16 — Real Failure Corpus & Sensitivity Validation (G2, G7)

**Goal.** Show the heuristics catch the failures a **real segmenter actually
makes**, and build the curated challenging-case corpus §8 of the vision has
always required but which has never existed. Today every §6 failure mode is
detected only on *synthetically perturbed* GT: the corpus proves each mode is
*detectable in principle*, not that real tools produce it or that we catch it
when they do.

**Deliverables.**

- **Real candidate cohort**: the SPINEPS VerSe passes, ingested through
  `spinelab`'s candidate descriptor at a recorded `spinelab` commit, and scored
  against real GT.
- **Modes 2 and 3 against review**: per-level sensitivity and specificity
  against the `rl1` labels on calibration-role cases. They are reported
  separately for the ranked and random sampling streams, and only the random
  stream supports a rate. Test-role labels are read once, at the stage
  validation, after the rules are frozen.
- **Dice-vs-flag correlation** on per-mode findings, which supersedes the
  synthetic-only figures in Stage 7's metrics block (Success Criterion 6). The
  verdict-level figure is reported beside it and labelled as dominated by
  `reference_delta`.
- **Which §6 modes SPINEPS produces**, and at what rate, in a recorded account
  that labels each mode in one of three ways:
  - **adjudicated**: a review looked for it;
  - **fired, not adjudicated**: a rule fired, but no review looked for the mode;
  - **untested**: absent from the data.
- **Interface asserted on this side**: a test reads `spinelab`'s committed
  descriptor and `rl1` table at the pinned commit and refuses on version
  drift. `spinelab` asserts the other direction.
- **Curated challenging-case corpus** (behind `gate-2f91`) — real pathology /
  post-op / atypical anatomy, with expected verdicts
  (`VerSe_fracture_grading.xlsx` is a natural seed) — the direct test of
  failure-vs-variation on cases that matter.

**Dependencies.**
- **In this repository:** Stages 13, 14, 17, 18, 20 and 35. Stage 35 is a
  forward dependency, tolerated while this stage is ⏸️.
- **Out of band:** gate `gate-ae46`'s bundle. `spine-failure-lab` must deliver
  its Stage 9 item 119 (the candidate descriptor and split subsets) and its
  `rl1` label table.
- **Feeds:** Stage 11's abnormality arm.

**Validation / acceptance.**

- ≥1 heuristic fires on a **real** instance of each §6 mode the cohort actually
  contains; modes absent from real data are recorded as such rather than
  silently credited (**G2**).
- Real Dice-vs-flag correlation is measured on per-mode findings and correctly signed, with the verdict-level figure reported beside it and labelled as dominated by reference_delta (**G7**, Success Criterion 6).
- Curated challenging cases run with recorded outcomes, and legitimate variation
  is not flagged at Stage 14's FPR bar.
- The "Real automatic-segmentation failure corpus" verification row reads
  ✅ Verified.

---

# Post-supersession stages (2026-07-25)

> Stages 17–21 are the live work following [`vision.md`](vision.md) §0. Stages 17 and 18
> unblock work on real segmenter output; 19–21 audit what was built while the framework
> itself was the priority. **19 and 20 are pure audit — they touch no production
> behaviour and should run alongside 17/18**, because every later stage that adds or
> retunes a rule is safer once the catalogue and the specificity ratchet exist.

---

## Stage 17 — Foreign-Convention Interop & Orientation-Safe Image Layer (G2, G6)

**Goal.** Make FACET read another tool's output correctly. Today `segfacet.labels`
defines its own vertebra numbering in which **25 = `S`, 26 = `Cocygis`, 29 = `L6`**,
while the TPTBox convention that SPINEPS emits reads **25 = `L6`, 26 = `S1`, 29 = `S2`**.
Only 28 (`T13`) agrees. Feeding SPINEPS output in with the current defaults **silently
misreads the sacrum as L6** — no error, plausible-looking numbers, wrong. Every
downstream measurement would be quietly invalid, so this stage must land before any
real-segmenter number is computed.

**Deliverables.**

- **Adopt the TPTBox vertebra standard as the default** (`DEFAULT_LABEL_MAP`,
  `CANONICAL_ORDER`), retiring the legacy table. `LabelConvention` stays overridable for
  genuinely foreign inputs. Note TPTBox's `v_idx2name` also carries subregion names from
  `Location` (≥ 40, plus `0: Unknown`) — the 1–33 vertebra range is clean, but filter
  rather than consume the mapping wholesale.
- **TPTBox-backed image layer**: back `segfacet.io`'s `Volume`/`Case` with TPTBox `NII` —
  orientation-safe load, `reorient`, `rescale`/`resample_from_to`, mm-space conversion,
  `zoom`/`affine` — replacing the hand-rolled `_spacing_from_affine`. Keep `Volume`/`Case`
  as the public shape so the ~22 modules importing nibabel migrate behind one seam.
- **Environment migration**: `requires-python = ">=3.11"`, a numpy **range**
  (`>=1.26,<3`) rather than a pin, regenerated `constraints.txt`, and a CI leg on each
  numpy major so the library stays major-agnostic.
- **Run-manifest schema** — the provenance record carried alongside every number:
  segmenter version/SHA, weights hash, post-processing toggles, seed, dataset id, and
  the resolved `numpy`/`TPTBox` versions.

**Dependencies.** None blocking; supersedes nothing.

**Validation / acceptance.**

- A regression test asserts labels 25/26/29 match the TPTBox table (**G2**).
- The reference artifact (`reference_verse_v1.json`, keyed by vertebra **name**)
  loads and scores unchanged, proving no re-fit was needed.
- The suite is green on both numpy majors (**G6**).
- A real segmenter output round-trips with correct level names.

---

## Stage 18 — Failure-Mode-Specific Metric Surface (G2, G7)

Archived in [roadmap/stage-18.md](roadmap/stage-18.md).

---

## Stage 19 — Generated Feature & Rule Catalogue + Steering Review (G7, G8)

Archived in [roadmap/stage-19.md](roadmap/stage-19.md).

---

## Stage 20 — Failure-Mode ↔ Feature ↔ Rule Traceability & Specificity Harness (G2, G7)

Archived in [roadmap/stage-20.md](roadmap/stage-20.md).

---

## Stage 21 — Real-GT Perturbation Corpus (G3, G7)

**Goal.** Move calibration off hand-crafted geometry. The current corpus is built from
synthetic fixtures (`synth/clean_gt.py`) — five stacked lumbar blocks at 1 mm isotropic.
Thresholds fitted against that geometry are fitted against a shape no real spine has, and
as the rule set grows, hand-crafted cases increasingly trip rules they were never meant
to exercise. Real ground truth is the natural base: the perturbation operators already
take label maps, so the change is largely one of input sourcing.

Make the **three rungs of realism** explicit, and stop conflating them:

| Rung | Corpus                                                                | Role                                           |
| ---- | --------------------------------------------------------------------- | ---------------------------------------------- |
| 1    | hand-crafted fixtures (`synth/clean_gt.py`, `tests/synthetic.py`) | fast unit-test scaffolding**only**       |
| 2    | **real GT + scripted perturbation** *(this stage)*            | threshold calibration, regression, sensitivity |
| 3    | real segmenter failures (**Stage 16**)                          | validation                                     |

**Deliverables.**

- The existing `Perturbation` operators re-sourced from **real VerSe GT**, with a manifest
  recording subject IDs, seeds and operator parameters so the corpus is reproducible
  without committing bulk data.
- **A real clean-control baseline** — a *cohort* false-positive rate rather than a single
  synthetic pass case, which is the only honest baseline for G3.
- Threshold calibration and every sensitivity claim moved to rung 2; rung 1 retained for
  fast unit tests only.
- **Act on Stage 19's golden decision** — retire the corpus-snapshot goldens as their
  cases are superseded. Do **not** regenerate the nine snapshots against the new corpus;
  that recreates the same problem one rung up. *(Pulled forward into Stage 29 D1 on
  2026-08-30 — by the time this stage runs, the retirement should already be executed.)*

**Dependencies.** Stages 13 (VerSe adapter), 19 (golden decision), 20 (specificity
harness — the new corpus is exactly what the ratchet is there to police).

**Validation / acceptance.**

- Every threshold-bearing rule is calibrated against rung 2, not rung 1 (**G3**).
- Stage 20's specificity assertion holds on the new corpus, or each violation is
  recorded with a reason (**G7**).
- The corpus regenerates reproducibly from its manifest.

---

## Stages 22–25 — placeholders (authored at the full re-vision)

> **Build posture, 2026-09-18.** Not queueable. These four hold numbers and name
> dependencies, nothing more. Under the `prototype` posture none of them is staged,
> queued or prepared for until a success criterion or an unmet Outcome target needs
> it and the measurements it depends on exist. An item whose only justification is
> one of these stages is a "for later" item and is not queued.

> Recorded so numbering is stable and dependencies can be named. **Deliberately not
> specified**: each depends on measurements that do not exist yet, and a stage written
> before its evidence would be speculation.

- **Stage 22 — Unified `(scan, seg)` extraction.** One entry point over the paired scan
  and segmentation, replacing the current split between label-map-only and
  intensity-aware paths.
- **Stage 23 — Multivariate normative model.** Replaces the univariate per-level
  percentile z-scores aggregated by RMS. **Carries forward the two `❌ Not met` Outcome
  targets** (held-out real-GT FPR ≤ 0.10; no real-GT sensitivity regression), and absorbs
  the open insight that `reference_delta`'s threshold should derive from the training
  cohort's own percentiles rather than a hand-set constant — the fixed-constant mechanism
  is what cannot clear the FPR target without sacrificing sensitivity.
- **Stage 24 — Failure-mode discovery & typed reference set.** Cluster the feature space
  to surface modes not in the §6 catalogue; curate per-class exemplars.
- **Stage 25 — Segmenter-native perturbations.** Rung 3's generator: perturbations derived
  from what a real segmenter actually does wrong, rather than from a catalogue written in
  advance.

---

# Stages scoped 2026-08-11 (after Stage 19)

> Numbered after the placeholders so numbering stays stable; **both run earlier than their
> numbers suggest** — see each stage's Dependencies. Scoped from triaged
> [`insights.md`](insights.md) entries that had accumulated no owner.

---

## Stage 26 — Carried-Defect Remediation (pre-real-data) (G2, G7)

**Goal.** Clear the defects that Stages 17–19 recorded but were forbidden (correctly) from
fixing in scope, **before** Stage 20 audits the surfaces they sit on and before Stage 21
starts producing numbers from real data. Every item here is a known, diagnosed defect with
a named location — this stage does no discovery.

**Deliverables** (each a candidate item; D1–D3 and D8 are the load-bearing ones):

- **D1 — `normalised_delta` saturation** (`eval/per_mode_cohort.py`). `delta / max(|a −
  baseline|, |b − baseline|)` saturates to exactly ±1.0 whenever one run sits on baseline —
  and 7 of 8 `PER_MODE_METRIC_SPECS` baselines are `0.0`, so any two modes that both return
  to baseline tie at 1.0 and AC13's lowest-mode tie-break decides attribution, blind to
  actual magnitude. Stage 18's run-vs-run **attribution** deliverable does not work as
  specified today; two of its own tests demonstrate the trap.
- **D2 — RAS `touches_*` face mapping** (`features/geometry.py:251-256`, consumed by
  `heuristics/border.py` and `heuristics/fov.py`). Item 094 now reorients every loaded
  volume to RAS, so `x == 0 → touches_inferior` names the **left-right** axis: every
  `border`/`fov` finding on data read through `segfacet.io` is anatomically mislabelled.
  Must land before real data, or Stage 21's findings inherit the error.
- **D3 — golden-fixture test hygiene.** `tests/golden/*.json` is the only committed
  byte-reproducible text fixture family absent from `.gitattributes` (latent Windows-CI
  break, three prior instances documented); and
  `test_022_stage3_serialisation.py::test_ac8_golden_snapshot` **writes its own golden and
  skips** when the file is missing, so deleting the golden makes the check pass. Both
  goldens are dispositioned *retire* by item 105, so "fix or retire" — whichever comes
  first.
- **D4 —** `eval/per_mode.py::compute_per_mode_metrics` gains an optional
  `overlap_result=` so the Stage-7 harness stops paying for a second full overlap pass per
  case.
- **D5 —** scope `test-numpy-majors` (`.github/workflows/ci.yml`) off the Docker- and
  PyRadiomics-gated modules; it exists to test numpy-major agnosticism and currently
  doubles the repo's exposure to Docker Hub rate-limiting for no verification value.
- **D6 —** refresh `heuristics/bounds.py`'s comments, which still name the retired `S` /
  `Cocygis` labels (behaviour is correct; the comment is not).
- **D7 —** resolve `progress.md`'s Stage 17 acceptance box, whose `- [x]` contradicts its
  own annotation (*"Not ticked: no real SPINEPS output is available…"*). Maintainer's call
  between untick / reword / a third state.
- **D8 — `features/neighbourhood.py` is dead wiring.** Stage 3's ✅ deliverable claims local
  vertebra-neighbourhood comparison "flags isolated anatomical outliers"; the module is
  implemented in full and referenced by **nothing** — not `pipeline.py`, not
  `feature_report.py`, not any of the 10 rules — so it never reached item 103's catalogue
  and no verdict has ever been influenced by it. Wire it (deciding whether it needs a
  consuming rule, and reconciling its mean/std deviation score with the percentile-based
  `robust_z` machinery), or retire it and correct the Stage 3 claim.
- **D9 — the byte-hash scope fences are the wrong instrument, and are now a tax on every
  item in this stage.** Five items (099, 100, 101, 103, 105) pin SHA-256 digests of
  committed source as "untouched" fences, and item 106 extends the pattern to individual
  `progress.md` rows. A fence encodes a **diff-time** property (*"item N did not modify file
  X"*) as a **permanent runtime invariant** (*"X equals these bytes forever"*) — a different
  and false claim as soon as a later item is legitimately authorised to edit X, which is the
  normal case. Record to date: **six documented failures** — three Windows-CI-only and
  invisible to every local gate, one where the pinned digest was never reproducible even on
  an unchanged tree (`rglob("*")` swept `__pycache__`), two collisions with a later item's
  authorised edit — and **no recorded true positive**. Item 104's Decisions log already
  reached this verdict and made its equivalents "git-diff obligations on the validator, not
  pytests"; 104 and 106 use that pattern, the rest are legacy. Retire the fences and land
  the deterministic check they were reaching for: a spec-declared authorised-path list
  diffed against `git diff --name-only $(git merge-base main HEAD)`. **The check belongs to
  the branch, never to pytest** — a diff-scope assertion has nothing to assert once merged,
  and forgetting that is what produced the fences. Preserve what is *not* a fence: intra-run
  determinism assertions, item 104's drift test, item 098's expected-value baselines. The
  durable home for the check is the framework (`aide-loop`); this stage prototypes it here
  so the upstream change is a port of something proven rather than a design sketch.

**Dependencies.** None. **Runs next, ahead of Stage 20** — D1/D2/D8 change surfaces Stage
20 audits, so auditing first records findings that are about to move. D2 is additionally a
prerequisite for any real-data claim (Stages 16/21).

**Validation / acceptance.**

- Each defect has a regression test that fails before its fix (**G7**).
- `border`/`fov` findings carry anatomically correct face names under RAS
  (**G2**).
- Per-mode attribution distinguishes a large move from a small one on a fixture
  built to have both.
- `neighbourhood.py` is either reachable from `extract_feature_record` and
  present in the regenerated catalogue, or removed with the Stage 3 deliverable
  reworded.
- No `_PRE_NNN_*` byte-hash fence remains, and the diff-based scope check that
  replaces it flags a deliberately out-of-scope edit on a scratch branch
  (**G7**).

---

## Stage 27 — Feature Schema Taxonomy & Coordinate System (G8)

Archived in [roadmap/stage-27.md](roadmap/stage-27.md).

---

## Stage 28 — Spinal Curve Model: Formulation, Offset & Orientation (G2, G7)

Archived in [roadmap/stage-28.md](roadmap/stage-28.md).

---

# Stage scoped 2026-08-30 (queue-017 boundary triage)

> Same construction as Stages 26–28: numbered after the placeholders so numbering stays
> stable, **runs earlier than its number suggests**. Scoped from the carried defects the
> queue-017 triage routed to this file plus the two surviving 2026-08-25 entries — every
> deliverable is a known, located defect or an already-signed decision awaiting execution;
> this stage does no discovery.

## Stage 29 — Golden Retirement & Test-Artifact Hygiene (G2, G7)

**Goal.** Execute the maintainer-signed retirement of the whole-record snapshot goldens and
make "comparing against a committed artifact" reach for numeric tolerance by construction —
then sweep the small located defects that queue 017 recorded but was (correctly) forbidden
from fixing in scope. The motivating cost is measured, not speculative: items 119/120/123
each regenerated nine snapshot goldens plus both reference artifacts and touched ~8 pinning
test files, and three of those items' test-writing passes reintroduced byte-exact
comparisons against committed float-carrying artifacts that only PR #56's CI matrix caught
(~1 ULP float drift across numpy versions and platforms).

**Deliverables** (each a candidate item; D1–D2 are the load-bearing ones, D3–D5 batch
naturally, and D1 should land first so D5/D7/D8's regeneration surface is already smaller):

- **D1 — execute the golden retirement.** All 11 snapshot rows of
  [`golden-decision-table.md`](golden-decision-table.md) (the nine `tests/corpus/golden/*.json`
  whole-record reports and the two `tests/golden/` snapshots, items 016/022) are
  maintainer-dispositioned **retire** (signed 2026-07-28, item 106), with the four
  replacements specified per row: (i) intra-run determinism survives via the existing
  run-to-run tests; (ii) schema validity re-points at a freshly built report; (iii) the
  load-bearing "verdict/findings unchanged" use moves to a narrow verdict+findings shape
  expectation that pins no feature values and so survives a feature retune; (iv) Stage 21's
  real-GT corpus takes over the snapshot role. Execution was assigned to Stage 21 (or 27,
  whichever first) and is pulled forward here — it needs no new corpus, and every queue
  meanwhile pays the regeneration cascade. Do **not** regenerate the snapshots on the way
  out; that is the exact move the disposition forbids.
- **D2 — tolerance by construction.** A shared comparison helper whose name makes
  "fresh output vs committed artifact" go through `reports_close`-style numeric tolerance,
  plus a guard test extending `tests/test_111_golden_guard.py`'s hand-surveyed
  `_KNOWN_BYTE_EXACT_FIXTURE_FAMILIES` into an enforced allowlist: a new byte-exact
  comparison of freshly generated output against a committed float-carrying artifact fails
  with a message naming the helper. The spec carries item 124's emission-clamp rule for
  what legitimately stays byte-compared: an artifact reporting a raw float measurement
  alongside its own "meaningfully nonzero" threshold must clamp sub-threshold noise to a
  fixed sentinel at the serialisation boundary (`segfacet.observed_range.emission_range`
  is the shipped example — quantisation cannot stabilise cancellation-scale noise), and
  a spec that changes a feature the reference artifact aggregates must survey every
  consumer mechanically (`grep -l build_and_write_default tests/`), not by hand-listing.
- **D3 — relocate the surviving artifact-integrity pin, rename the mislabelled fence.**
  `tests/test_098_stray_components.py::test_ac18_reference_verse_v1_bytes_unchanged` pins
  `reference_verse_v1.json`'s bytes under an item-098 scope-fence name; the invariant is
  legitimate (a released production artifact must not change silently) but belongs in a
  test named for the artifact beside `reference/artifact.py` — carrying its
  `.gitattributes` pin across deliberately, since engine 1.19.0's lint cannot see a path
  reached through a helper function. And `tests/test_102_stage18_validation.py`'s
  `# AC24: the scope fence` header sits over a legitimate intra-run determinism assertion —
  renaming the header to say what it checks is the whole fix. *(Both routed 2026-08-25.)*
- **D4 — `fit_centroid_spline` degenerate input.** `features/spline.py` propagates SciPy's
  bare `ValueError: Invalid inputs.` when all supplied centroids are exactly coincident;
  degrade gracefully or raise a descriptive error naming the cause, and let item 122's
  substituted 1e-6 mm adversarial fixture become the real all-coincident case.
- **D5 — the 4-centroid silent zero.** `compute_leave_one_out_spline_offsets`'s `< 4`
  in-sample fallback boundary is one too low: at `k = 3` with four points the held-out
  refit interpolates and every offset reads exactly `0.0` (measured on real
  `sub-verse065`), so a 4-level field of view cannot raise a `mislabel` offset finding.
  Move the boundary to `< 5` and regenerate the affected reference distributions.
- **D6 — spline plumbing consolidation.** The coarse-scan-plus-`minimize_scalar`
  closest-point search exists three times (`features/spline_offset.py`,
  `features/consistency.py`, `scripts/compare_curve_candidates.py`) with no link between
  them, and the pipeline fits the identical in-sample spline twice per case (`pipeline.py`'s
  curvature fit and `spline_offset.py`'s internal reference refit). One implementation,
  one fit.
- **D7 — `tangent_angles_deg[]` traversal-direction normalisation.** The unsigned angle to
  `+S` reads ~175° per level on a cranial-first centroid sequence and ~5° on a caudal-first
  one — same spine, two readings, latent only because every committed fixture happens to
  advance superiorly. Normalise to the convention item 122 already established for its
  signed per-plane arrays, so the record carries one tangent-angle convention.
- **D8 — give the mode-4 acceptance an owner.** Stage 28 asserts a smoothed fit detects
  the mode-4 swap via `is_monotonic == False`, but no queue-017 item owned
  `features/consistency.py`, and the criterion is measured unmet (item 125's replay pins
  `is_monotonic == True` on `mode4_relabel_swap`). Make the monotonicity check judge the
  smoothed fit so the swap fires, closing Stage 28's unticked mode-4 acceptance half.
- **D9 — bump `tptbox` to ≥ 0.7.6.** The 0.7.5 wheel's published metadata declares AGPL
  v3.0 while TPTBox's `LICENSE` is Apache-2.0; upstream fixed the metadata in v0.7.6
  (TPTBox PR #119). A dependency bump's regression surface is the golden corpus — smaller
  after D1, which is why this sits here and not in a drive-by edit.
- **D10 — `scripts/refresh_reference.py --verse-cohort` has never worked.** It hands the
  cohort root to `ingest_cohort`, which lists one directory non-recursively and hardcodes
  `_scan.nii.gz` siblings — incompatible with VerSe's layout, so the wrapper records
  `verse-build: failed` by construction. Delegate to item 123's
  `scripts/rebuild_verse_reference.py` or retire the mode.
- **D11 — split the decision table's live counts from its signed judgement.**
  `golden-decision-table.md`'s `N/M leaf paths unwired` cells are live values off
  `build_catalogue()`, so every feature-adding item (106, 110, 122) edits a human-signed
  document to refresh a count while asserting no judgement moved. Generate the measured
  counts into a small companion artifact the signed document references, so a count
  refresh never touches signed text.

**Dependencies.** None. **Runs next, ahead of Stage 20** — D1/D7/D8 change the surfaces
Stage 20 audits and the specificity baseline it pins, and D8 closes a Stage 28 acceptance
line Stage 20 would otherwise re-record as a reachability hole. The Stage 21 deliverable
"Act on Stage 19's golden decision" and Stage 27's "natural moment to execute item 105's
golden retire dispositions" are both superseded by D1.

**Validation / acceptance.**

- All 11 retired snapshots — the nine corpus snapshot goldens and both
  `tests/golden/` snapshots — are gone with their four named replacements in
  place and no snapshot regenerated on the way out; the D2 guard fails a
  deliberately added byte-exact comparison against a committed float-carrying
  artifact on a scratch branch (**G7**).
- `mode4_relabel_swap` yields `is_monotonic == False` through
  `extract_feature_record`, closing Stage 28's mode-4 acceptance half (**G2**).
- A 4-level field of view yields non-degenerate held-out offsets; `pip show
  tptbox` reports a non-AGPL licence; each fixed defect carries a regression
  test that fails before the fix (**G7**).

---

# Stage scoped 2026-09-03 (queue-019 boundary feedback loop)

> Same construction as Stages 26–29: numbered after the placeholders so numbering stays
> stable, **runs earlier than its number suggests** — before the remainder of Stage 20.
> Scoped from [`failure-mode-taxonomy-handover.md`](failure-mode-taxonomy-handover.md)
> and the six decisions human gate `gate-0fdd` recorded on 2026-09-03; the schema, lifecycle and
> growth contract it implements are [`vision.md`](vision.md) v3 §6.

## Stage 30 — Failure-Mode Specification: the §6 catalogue as an authored source (G2, G7, G8)

Archived in [roadmap/stage-30.md](roadmap/stage-30.md).

---

# Stages scoped 2026-09-15 (after Stage 30's sign-off)

> Numbered after Stage 30 so numbering stays stable; **both run before Stages 27, 21 and
> 16** — see the run-order line at the top. Scoped from the maintainer's decisions at item
> 150's close: follow-up changes and prerequisite defects go to a **maintenance stage**
> that runs first; then **selected** failure modes are refined interactively, with Stage
> 20's remainder interleaved, until at least one mode is fully specified end to end — the
> pipeline's MVP. Every other mode stays documented in the specification at its derived
> status and is refined individually, when and where wanted, in any later queue.

---

## Stage 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update (G7, G8)

Archived in [roadmap/stage-31.md](roadmap/stage-31.md).

---

## Stage 32 — Selected-Mode Refinement: one failure mode fully specified end to end (G2, G7, G8)

Archived in [roadmap/stage-32.md](roadmap/stage-32.md).

---

## Stage 33 — Corpus & Rule Re-grounding: modes 2 and 3 to the bar (G2, G7, G8)

Archived in [roadmap/stage-33.md](roadmap/stage-33.md).

---

# Stage scoped 2026-10-09 (queue-029 boundary roadmap triage)

> One standing stage for insight-derived maintenance, replacing the earlier practice of
> scoping a new stage per maintenance batch (Stages 26, 29 and 31, which stay as written,
> ✅, as history). The roadmap's former "Carried defects" list is gone: its live entries
> were returned to `insights.md` as open entries (2026-10-09-ed9b, 2026-10-09-bc75,
> 2026-10-09-2c9f, 2026-10-09-9de3, 2026-10-09-7e82, 2026-10-09-c1b7) and the rest were
> already fixed. A known defect, gap or automation lives in `insights.md`, open, until
> the item that fixes it ticks it. The framework formalised this arrangement in engine
> 2.44.0–2.46.0 (aide-loop issue #453); what the stage and the Backlog below may carry
> is `.aide/conventions.md` §1 → roadmap.md.

---

## Stage 34 — Maintenance

**Goal.** Repair shipped work by closing insight-derived `defect`, `gap` and
`automation` entries in maintenance queues.

**Deliverables.** Added to [`progress.md`](progress.md) by each maintenance queue.

**Dependencies.** None.

---

# Stage scoped 2026-10-12 (programme interface adopted)

> The owner adopted `spine-failure-lab`'s `docs/project/facet-interface.md` at commit
> `7436b0f` ([`vision.md`](vision.md) v4.2, §7.5 and §8). That file lists what crosses
> between the two repositories: a candidate descriptor, a run manifest, the `rl1`
> review-label table and a split manifest coming in, and FACET's reports going out.
> Stage 16's real measurement reads all of them. This repository's side of that
> interface needs no out-of-band input, so it is a stage of its own and runs before
> Stage 16.

---

## Stage 35 — Programme Interface: the SegFACET Side (G2, G3, G7)

**Goal.** FACET can read everything the programme repository will hand it for Stage
16, and writes reports that repository can pin. Each cohort is split by dataset role,
real review labels are an expectation the evaluation harness understands, every
report names the revision that wrote it, and the reference is built from the
development role only.

**Deliverables.**

- **Case-id-list subsets**: descriptor `subsets` can be an explicit list of case
  ids as well as a directory root, so the split manifest's roles can be named for
  any cohort.
- **VerSe20 ground-truth descriptor** beside `verse19.yaml`, and both descriptors
  carry `development`, `calibration` and `test` subsets over the release's
  training, validation and test splits. This lets `segfacet evaluate` pair VerSe20
  candidates by case id and select cases by role.
- **Real-label expectation**: the evaluation cohort accepts a per-label
  expectation with several modes per case, read from `spinelab`'s `rl1`
  review-label table. The table is checked against a vendored schema, taken from
  the field table of `facet-interface.md` at the pinned `spinelab` commit, and a
  table at any other version is refused. Mode 0 means a level that was reviewed
  and found clean.
- **Artefact versioning**:
  - a release tag on every revision `spinelab` consumes;
  - the FACET commit written into every per-case and evaluation report;
  - a report `schema_version` that moves whenever a feature path moves.
- **Development-role reference**: the VerSe reference rebuilt from the VerSe19
  and VerSe20 training splits. This replaces today's VerSe19-training-only
  `reference_verse_v1.json`, which is out of date for any subject with a T13
  (insight 2026-10-06-f318). `spline_offset.max_offset_mm` is re-derived from the
  rebuilt offset distribution with `sub-verse406_split-verse261` T10 (label 17)
  excluded. That label is a rare wedge vertebra, and its 18.51 mm offset is an
  anatomical outlier that set today's 13.0 mm (owner decision 2026-10-16,
  `gate-fac1`).

**Dependencies.** Stages 13, 14, 17 and 27.

**Validation / acceptance.**

- A descriptor whose subsets are case-id lists resolves exactly those cases, and
  the VerSe19 and VerSe20 descriptors resolve the three role subsets over the
  release splits (**G7**).
- An `rl1` table at the pinned version becomes a per-label, several-modes-per-case
  expectation the evaluation harness scores against, and a table at any other
  version is refused (**G2**).
- Every per-case and evaluation report carries the FACET commit and a schema
  version, and a feature path that moves without a schema-version change fails the
  suite (**G7**).
- The rebuilt reference draws only on development-role cases, and no
  calibration-role or test-role case contributes to it (**G3**).
- `spline_offset.max_offset_mm` is re-derived from the rebuilt distribution, and
  the excluded wedge-vertebra label contributes nothing to it (**G3**).

---

# Backlog

> Ideas only: scope not yet ready to plan. What a bullet may say, and how one leaves the
> list, is `.aide/conventions.md` §1 → roadmap.md.

- **Leave-one-out / counterfactual sensitivity feature** (insight 2026-07-28-56f4). For a
  given vertebra, measure how much a scan-level shape metric (for example spline
  smoothness or curvature) changes when that vertebra is ablated, by dropping its label or
  merging it into its largest bordering neighbour, as a measure of its structural
  influence on the whole spine. An ablation, distinct from both the population reference
  (`reference_delta`) and the local-neighbourhood comparison.
- **How the synthetic fallback reference should be generated** (insight
  2026-07-28-bc8a). `reference_default.json` is built from a five-subject synthetic
  cohort (`build_clean_spine` plus `paint_clean_scan(seed=0)`) and kept as a fixed
  fallback and synthetic-regression fixture; the CLI default is the real
  `reference_verse_v1.json`. The idea: derive it from published anatomical value ranges
  instead of synthesised geometry, or adopt a realistic synthetic-data toolkit.
- **Multichannel / probabilistic segmentation input.** The precondition that would make
  the overlap mode observable on real data at all.
- **A real-data demonstrator for the Stage 18 thesis** (insight 2026-08-14-bb93). A real
  corpus case where an unbounded per-mode metric's magnitude dramatically beats aggregate
  Dice. Item 109's demonstrator rested on a saturation artefact, so today only a
  hand-built synthetic fixture shows it; a real case needs genuinely large per-case
  magnitude, the kind a perturbation corpus could supply.
- **A retirement path for `feature_docs.STATUS_OVERRIDES`** (insight 2026-08-27-2a03).
  The overrides are a verbatim transcript of the item-106 maintainer walkthrough, so an
  item that fixes a recorded concern cannot rewrite the recorded human call. Either a
  dated append-trail convention like `insights.md`'s, or a queue-boundary pass that
  re-asks the maintainer.
- **A refutation harness for `signal` path classifications** (insight 2026-09-04-4caf).
  Today a `signal` classification is an authored claim nothing can refute. One
  threshold-crossing mutation per signal path would assert that the reading rule's
  findings move. Above that, rule-side first-class detector IDs would attribute each path
  to the one mode it serves (`mislabel`'s offset vs monotonicity detectors,
  `fragmentation`'s two branches) rather than to every mode of its rule.
- **Per-component scope** (insights 2026-10-06-2119, 2026-09-30-88a5, 2026-10-02-3eba).
  A connected component as a feature region beside scan, label and pair, so each piece
  of a multi-component label is judged on its own. The cheapest route found at the
  Stage 27 review: a temporary sub-segmentation that relabels components as sub-labels
  (1.1, 1.2, …), so the existing per-label extractors absorb them unchanged. Two modes
  wait on it. Mode 4 (islands) needs re-defining first: a piece counts as an island if
  it is small, or larger but far from the main body, and how size and distance combine
  is still to be refined with the maintainer. Mode 2's `stray_contact` would also read
  contact from the neighbour's side, which is maintainer feedback at the `gate-0133`
  sign-off.
- **A mode for the label that lost part of its vertebra** (insight 2026-09-30-7d74).
  When a mode-2 label overreaches onto its neighbour, the neighbour's own label is left
  covering only the remainder of its vertebra, and nothing names it. Owner position
  (2026-10-12): such a label falls into mode 1, is fixed by fixing its mode-2
  counterpart, and is sometimes recorded as a QC comment for future reference. Not the
  focus for now.
