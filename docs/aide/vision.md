<!-- aide-template: vision 1 -->
# FACET — Project Vision

> **Status:** v4 (draft 2026-09-16) · **Created:** 2026-06-24 · **Re-issued:** 2026-09-16
> Step 1 of the AIDE loop · the root document: [`roadmap.md`](roadmap.md),
> [`progress.md`](progress.md), every queue and every work item derive from this.
> Its guiding principles, out-of-scope list and success criteria are the mandatory
> core the validator checks implementations against.

> **Revision note (v4).** v3's §6 carried a numbered eight-item list as the
> interim record of the failure-mode catalogue. Stage 30's sign-off (item 150,
> 2026-09-15) made `segfacet.failure_modes.SPECIFICATION` the catalogue — ids
> assigned there, one seed title retired, one re-homed as a condition, entries
> split, two observability classes added — so the list no longer matched the
> record it seeded. v4 re-issues **§6 only**: principles plus a pointer to the
> specification, no numbered list, the five observability classes, the
> FOV-truncation **condition** as a first-class concept, the `validated` rung as
> the sign-off defined it, and the evidence-rungs example corrected from
> "two-descent" to the single rank descent it is (`insights.md`, item 147,
> 2026-09-04; item 150, 2026-09-14). Every other section, every G-code and the
> mandatory core are unchanged from v3. Roadmap Stage 31 D1.
>
> **Revision note (v3).** v2 (2026-07-02) described `Seg-QC-xnat`, an XNAT-deployed QC
> gate, and carried a supersession note (2026-07-25) that retyped the project as
> FACET while leaving the body as history. v3 rewrites the body to describe FACET
> directly and retires the note. v2 is in git history up to commit `c519608`;
> the objectives keep their G-numbers and are **never renumbered**, so every
> `G`-reference in [`roadmap.md`](roadmap.md), [`progress.md`](progress.md) and
> the item specs resolves unchanged. The reasons for the re-issue and the
> decisions it encodes are recorded in
> [`failure-mode-taxonomy-handover.md`](failure-mode-taxonomy-handover.md) §12
> and human gate 3 (approved 2026-09-03). The **full** re-vision v2 deferred —
> specifying Stages 22–25 — stays deferred: those stages depend on measurements
> of real segmenter failures that do not exist yet, and remain placeholders.

---

## 1. Project Overview

**FACET** (Failure Analysis, Characterisation & Evaluation Toolkit; Python package
`segfacet`) analyses **instance segmentations of spine imaging**. It reads a label
map (and, where intensity features are wanted, the scan it was made from),
extracts geometric, topological and intensity features, judges them against
reference distributions built from ground truth and against an explainable rule
set, and reports what it found — per case, and across a cohort.

Its product is a **characterisation of how a segmentation tool fails**: which
catalogued failure modes the tool actually produces, how often, with what
severity, and which measurable features isolate each one. A failure mode that is
characterised is addressable — by a correction rule, a training signal, a data
selection — rather than merely detectable. The per-case verdict that a QC gate
would stop at is, for FACET, evidence about the tool that produced the case.

Automatic spine segmentation tools fail in characteristic, often silent ways:
mislabelled vertebrae, fragmented or fused labels, rogue islands, missing levels,
partial vertebrae at the field-of-view border, implausible tissue. Downstream
work either trusts such output blindly or reviews every case by hand. FACET makes
those failures nameable, countable and traceable to the features that reveal
them.

FACET is a **library and CLI**, CPU-only by default, deterministic, and free of any
deep-learning framework. It is the torch-free half of a failure-mode-driven
segmentation-improvement programme; the GPU / SPINEPS / clinical-cohort half lives
in a separate private repository (`spine-failure-lab`) that consumes FACET's
findings, per-mode metrics and manifests as artefacts, not as a code dependency.
The two evolve independently, and that loose coupling is what lets FACET stay
general and deterministic.

### Guiding principles

- **Explainable over opaque.** Every finding carries a reason a person can
  inspect and argue with; rules and thresholds are documented and inspectable.
  A black-box score is not a substitute, because a score cannot say *which*
  failure occurred.
- **Tool-agnostic input.** FACET reads standard label-map formats (NIfTI) under a
  documented, overridable label convention — never one segmenter's internals.
- **Variation-aware.** Distinguish *failure* from legitimate variation: vertebral
  level, subject size, spinal curvature, pathology, post-operative state. What
  is abnormal is not thereby wrong.
- **Reference-grounded.** Expected feature distributions come from trusted
  ground truth (VerSe), stratified by the variation factors, rather than from
  hand-guessed constants wherever a reference can be built.
- **Validated on reality, not just tested.** Synthetic fixtures prove the code
  does what was meant; only real cohorts prove what was meant is right. Every
  claim is worded to say which of the two backs it, on the realism ladder of §8.
- **The failure-mode catalogue is an authored specification.** Each mode is
  defined once, in one authored source, with its definition, discriminator,
  observability, intended rules and corpus cases (§6). Every generated artifact
  — catalogue, traceability matrix, exercise report — is a **conformance
  report** against that specification, never the primary record. Prose that
  restates a mode is a transcription, and transcriptions drift.
- **A claim about live state is measured, never transcribed.** An acceptance
  check on a factual claim about code or a committed artifact compares the
  claim with the state it is about — the artifact's actual field set, the
  pipeline's actual firing set. A check that only proves the sentence has a
  shape (a length, a resolvable token, a flag the code set) is not a check.
- **Modality-explicit.** Shape and topology rules are modality-agnostic because
  they read only the label map. An intensity rule states the modality its
  thresholds hold for; CT is the default and the only modality calibrated today.
- **Portable, deterministic, torch-free.** CPU is the reference path and the GPU
  path (CuPy) is optional acceleration that must give equivalent results. No
  training stack is ever imported.
- **Extensible.** A foundation that new modes, new rules, new features and
  human-labelled abnormalities extend without re-architecture, along the growth
  contract in §6.

---

## 2. Goals & Objectives

| # | Objective | Measurable outcome |
|---|-----------|--------------------|
| G1 | Detect empty / trivially-failed segmentations | 100% of empty or near-empty label maps flagged |
| G2 | Detect the catalogued failure modes (§6) | Every mode at lifecycle status `implemented` or above has ≥1 rule declaring it; every `validated` mode is demonstrated end-to-end at its recorded evidence rung; on a **real** automatic-segmentation failure corpus, ≥1 rule detects each mode without per-mode sensitivity regression against the synthetic baseline |
| G3 | Distinguish failure from legitimate variation | **The open research question**, not a shipping gate: false-positive rate ≤ 0.10 on real, held-out VerSe GT *without* regressing failure-mode sensitivity below the recorded baseline. Carried by Stage 23 |
| G4 | Produce clear reports | Per case: JSON + human-readable, every finding with a reason. Per cohort — the **primary artifact**: per-mode frequency, severity and the isolating features, traceable to the rules and features that produced them |
| G5 | *Removed from scope 2026-07-25* — Deploy on XNAT | Not pursued. Row retained so the number is never reused; the retained XNAT artefacts are legacy pending relocation |
| G6 | Portable execution | Identical verdicts CPU-only; optional GPU acceleration path with equivalence tests |
| G7 | Be evaluable & regression-testable | Automated suite over synthetic fixtures **and** real cohorts, with each claim tagged by its realism rung (§8); no real-GT sensitivity regression against the recorded synthetic baseline |
| G8 | Be extensible | A documented, exercised path to add a failure mode (specification → rule → corpus case), a feature, or a human-labelled abnormality class, with the conformance artifacts regenerated |

**An objective is achieved only when its measurable outcome is demonstrated on
the kind of data the outcome names.** Several outcomes say *real* — real VerSe GT
(G3, G7), real segmentation failures (G2). Building and testing the machinery that
measures such an outcome is a prerequisite for achieving it, never a substitute:
code verified against synthetic fixtures is evidence about the code, not about the
world. Implementation status is tracked per stage in [`progress.md`](progress.md);
objective status is tracked separately, against the outcome, with real-data
evidence recorded in that document's verification and outcome-target tables.

---

## 3. Target Users

Two audiences, designed for equally:

- **The segmentation-improvement programme** (`spine-failure-lab`, private): the
  primary *consumer* of FACET's findings, per-mode metrics, manifests and
  characterisations. It routes each characterised failure class into training
  signal for the segmenter under improvement (SPINEPS). The coupling is at the
  artefact level — feature records, findings, metrics, manifests — never an
  import in either direction.
- **Segmentation-method developers and imaging researchers** characterising *any*
  spine segmenter: which failure modes it produces on a cohort, at what rate, and
  what distinguishes its failures from anatomy.

And, inside those, the roles the use cases name:

- **Dataset curators** assembling a clean research cohort (Use Case C).
- **Reviewers** who triage findings, accept or reject them, and feed that back
  into thresholds and rules (Use Case A).
- **Annotators / method developers** who label new abnormality classes (post-op,
  pathology) to extend FACET's coverage (Use Case B).

---

## 4. Use Cases

### Use Case E — Characterise a segmenter on a cohort *(the headline)*
Run a segmenter's output over a cohort; obtain, per catalogued failure mode, its
frequency, severity distribution, the cases exhibiting it, and the features that
isolate it. Compare two runs of the same segmenter (a post-processing step on
versus off, a fine-tune versus its base) and attribute the difference per mode.
This is what makes a failure mode addressable rather than merely detectable.

### Use Case A — Refinement of decision making
Use the current rules to flag cases; a human accepts or rejects each finding; the
feedback tunes thresholds and rules. Does not cover abnormalities not yet
modelled.

### Use Case B — Build annotations that extend the catalogue
Process segmentations automatically, assess the flagged cases by hand, and
**label new abnormalities** (e.g. post-operative changes) not yet in the rules.
Use those labels to extend the rules — and, as a later extension, a classical
feature-based classification arm that informs them.

### Use Case C — Build a curated research dataset
Determine which segmentations are successful and meet additional requirements
(field-of-view coverage, spinal segment, vertebra count, presence or absence of
abnormality) to assemble a clean dataset.

The v2 *Use Case D* — a QC gate that **blocks** failed segmentations in an
automated pipeline — is no longer a design target (§11). FACET still emits a
per-case verdict; whether a consumer gates on it is the consumer's policy.

---

## 5. Core Features

### 5.1 Segmentation input & label handling
- Consume vertebra **instance** segmentations (one label per vertebra) as NIfTI
  label maps, plus the original scan when intensity features are wanted.
- Tool-agnostic: a documented label convention mapping integer labels →
  anatomical vertebra (C1…C7, T1…T12(+T13), L1…L5(+L6), sacrum, …), overridable
  per tool (TotalSegmentator, SPINEPS/TPTBox conventions are the worked examples).
- Handle real-world quirks: anisotropic spacing, varying field of view, partial
  vertebrae at image borders, transitional anatomy, foreign orientations.
- **Dataset-agnostic ingestion:** cohorts in varied on-disk layouts and naming
  conventions (VerSe19/20, TotalSegmentator or SPINEPS outputs, …) through one
  internal `Cohort`/`Case` interface via declarative per-dataset adapters, so no
  dataset's folder structure is hard-wired into the pipeline.

### 5.2 Feature extraction
The feature record is a deliberately **over-broad vector** that rules select
from; a feature no rule reads is inventory, not a defect.

**Segmentation-based (geometric / topological, modality-agnostic):**
- Volume, extent and bounding box per label.
- Connected components per label (count, sizes) and a **fragmentation index** —
  the largest component's share of the label — separating a dominant body with
  noise fragments from a truly split label.
- **Vertebra centroid** in three tiers (simple centre of mass; smooth centre over
  the EDT-thresholded mask; strict centre at the EDT peak), level-aware, with C1
  and C2 handled specially; plus **centroid depth** to the nearest surface.
- **Spline fit** through the centroid sequence (the spinal curve model, with a
  human-approved deformity envelope), per-vertebra **offset** from it, and
  orientation / curvature estimates.
- Inter-vertebra relationships: spacing, ordering, monotonicity, continuity,
  neighbour consistency; **local-neighbourhood** deviations over a sliding window
  of anatomical neighbours.
- Border contact per face, and overlap between labels where the input can
  express it.

**Image-based (modality-explicit):**
- First-order intensity statistics over each labelled region, and PyRadiomics
  features when the optional dependency is present, with a builtin fallback.

### 5.3 Reference feature set
- **Reference distributions** of features built from ground-truth (VerSe)
  cohorts, stratified by anatomical level and the variation factors in §5.4,
  versioned as an artifact so every delta-to-reference is traceable to the
  reference that produced it.

### 5.4 Decision making / heuristics
An explainable rule set that accounts for **expected variation** — spinal
segment and level, subject size, spine shape (lordosis / kyphosis / scoliosis
within the approved envelope), pathology (fracture, compression), post-operative
state (implants, resections).

Rule families:
- **min/max bounds** (volume, extent, …), level-aware;
- **consistency with neighbouring vertebrae**;
- **delta to reference** (spline offset, distribution distance);
- **tissue plausibility** over the labelled region's intensity distribution,
  modality-declared.

Every registered rule **declares** the §6 failure mode(s) it targets, or declares
that it targets none with the reason; a rule with several detectors names which
detector serves which mode. The corpus-derived mapping corroborates the
declaration; disagreement is a test failure in both directions.

Optional **classification arm** (Use Case B): classical, feature-based classifiers
over human-provided abnormality labels that adjust the rules; never a
deep-learning head.

### 5.5 Reporting
- Per-case **verdict** (pass / flagged-for-review / fail) with per-vertebra
  detail and **explicit reasons** for each finding, as JSON and as a
  human-readable report.
- **Cohort characterisation** — the primary artifact: per-mode frequency and
  severity, run-vs-run attribution, the cases and features behind each mode,
  and a clean-control baseline (cohort false-positive rate).
- **Conformance artifacts**, generated and byte-reproducible: the feature
  catalogue, the failure-mode ↔ rule ↔ feature traceability matrix with its
  exercise columns, each reporting agreement or disagreement with the authored
  specification (§6).

### 5.6 Synthetic failure corpus
Perturbation operators that fabricate deliberately broken label maps from clean
ones — fragmentation, fusion, stray islands, missing levels, border truncation,
overlap, displacement, relabelling, sequence breaks — each case carrying a
machine-readable record of *what was broken* and which rules are expected to
fire. Applied to hand-crafted fixtures (rung 1) and to real ground truth (rung 2)
per §8.

### 5.7 Evaluation harness
A cohort-level harness comparing verdicts, overlap (Dice) against ground truth and
feature divergence, with per-mode metrics and threshold calibration, so every
detection and specificity claim is a measured number with the corpus it was
measured on.

---

## 6. Segmentation Failure Modes (to be detected)

The catalogue of failure modes is the organising object of FACET: a mode is what
a rule targets, what a corpus case demonstrates, what a cohort characterisation
counts. This section states the **principles** the catalogue obeys. The catalogue
itself — one entry per mode with its full definition — is the **authored
specification** `segfacet.failure_modes.SPECIFICATION` (modes) and
`segfacet.failure_modes.CONDITIONS` (conditions) in
[`src/segfacet/failure_modes.py`](../../src/segfacet/failure_modes.py), signed
off by the maintainer on 2026-09-15 (roadmap Stage 30, item 150) and rendered
as [`failure_modes.generated.md`](failure_modes.generated.md). Every generated
artifact is a conformance report against it. **This section carries no list of
modes, no ids and no count**: a mode named here would be a transcription, and
transcriptions drift. The numbered list this section carried in v1–v3 was the
*seed* the specification started from, never its ids; what became of each seed
title is recorded in the specification module's seed-disposition record and in
item 150's sign-off transcript.

**Each mode is specified, not described.** An entry carries: a stable `id` and
`name`, assigned in the specification and never renumbered; a `scope` — whether
the finding is about one vertebra or about the set and sequence of labels along
the spine; an optional `parent`, placing the mode in a one-tier
generic-to-specific hierarchy; a `definition` in clinical/geometric terms; a
`discriminator` — what separates the mode from its nearest neighbours (fused
and split segments are converses: one label covering more than one vertebra
versus one vertebra covered by more than one label; accuracy versus the
FOV-truncation condition turns on whether the missing part lies beyond an image
face); its `observability` class; `candidate_features` — feature paths
hypothesised to evidence it, distinct from the paths a rule is measured to
consume; `intended_rules`, naming the detector where a rule has several;
`corpus_cases`, each with its **expected** firing set (the measured set is never
authored, only compared); a `severity` — what a detection should mean for the
verdict; a lifecycle `status`; and a `provenance`. The Stage-18 per-mode
*metric*'s anchor path and the rule's read path are carried as two separately
labelled columns, never conflated.

**One defect per mode.** A sub-mode names one defect, never a pair of converse
defects, so every shipped detector serves at most one mode. A case that meets a
parent's definition but no sub-mode's rule is classified at the parent; the
parent is the catch-all, not a duplicate.

**Observability classes.** *Single-channel-observable* (the label map alone
carries the evidence); *needs the paired scan* (intensity-based);
*needs ground truth* (the defect is defined relative to a ground-truth label
map the per-case pipeline never sees — over-/under-segmentation and a vertebra
not segmented are the archetypes — so what a rule reads on the label map alone
is a proxy, such as a per-level volume or extent range, and each proxy edge is
recorded as such); *needs an external classifier* (the label map is internally
valid and no label-map feature distinguishes the failure from a correct
labelling — a whole sequence shifted by one level is the archetype — so only an
external vertebra-level identifier or ground truth decides it); *structurally
unobservable in the supported input* — overlapping segments cannot occur in a
single-channel integer label map, where a voxel holds exactly one label, and are
detectable only on a record deliberately corrupted to violate that invariant.

**Conditions are not failure modes.** A **condition** is a state of the case
that gates the rules — it is not a defect of the segmentation, and a rule may
legitimately decline to judge a vertebra under it. FOV truncation is the one
condition specified today: a vertebra at the edge of the field of view is only
partially captured, its geometry is impacted to a varying degree and its
measured centroid displaced, so many rules cannot be applied to it. A condition
carries the rule(s) that *record* it, the rule(s) that *exempt* under it, and
its own corpus case(s) with an expected firing set, so a condition case is never
a silent hole in the conformance report. A recording rule declares no failure
mode. A clean control and a condition-only case are two different kinds of
non-failure case; no consumer may tell them apart by the absence of a
failure-mode id alone.

**Evidence rungs.** "A rule covers this mode" and "we have demonstrated it
end-to-end" are different claims. Each mode ↔ rule **edge** carries an authored
rung — *synthetic-demonstrable* (a rung-1 fixture drives the rule end-to-end
today), *needs-real-data* (the rule exists but hand-crafted geometry cannot
express the input; the out-of-order sequence `L1 → T12 → L2 → L5` — a single
rank descent, since `T13` ranks between `T12` and `L1` in the canonical order —
is detected on a fixture, but the fixture generator cannot express a
multi-relabel scramble, so that edge stays at this rung), or
*structurally-unobservable* — and a mode's rung is derived as the strongest of
its edges, so an analytic-only edge is visibly weaker than a demonstrated one.
A mode recorded at *needs-real-data* or *structurally-unobservable* is an
acceptable state. A mode that is **silent** is not.

**Lifecycle.** A mode is listed long before it is built. Its `status` says how
far it has got — set by hand for the first two states, derived from live state
for the last two, and the ladder is cumulative:

- `proposed` — named and defined; no features, rules or corpus yet. Appears in
  the catalogue and every conformance report as unimplemented, which is an
  expected hole, not a defect.
- `specified` — definition, discriminator, observability and candidate features
  settled; rules named but not written.
- `implemented` — at least one registered rule declares the mode.
- `validated` — `implemented`, and a corpus case demonstrates detection
  end-to-end: every one of the mode's corpus cases has a measured firing set
  equal to its expected set, and at least one of those expected sets names one
  of the mode's **own** intended rules. A case detected only by another mode's
  rule, or by a mode-less detector, is a recorded co-detection and validates
  nothing; an empty expected set records "not detected today" and never
  validates.

The evidence rung is orthogonal to the lifecycle: a mode can be `validated` at
rung *needs-real-data*.

**Growth contract.** The catalogue is open. A mode is **claimed as covered** only
together with the rule(s) that detect it, plus any new feature(s) those rules
need when the existing pool does not already carry them. Listing a mode as
`proposed` is not a claim of coverage and does not breach this. What must hold
at all times is coverage in two directions — every mode at `implemented` or
above has a rule, every rule names a mode or records why it names none — which
the traceability matrix makes visible and enforceable. The mode → rule direction
is **scored**, not asserted complete: a `proposed` mode is an expected hole.
The third direction, feature → rule, is **deliberately incomplete**: features
may be added alone and sit unwired until a rule draws on them.

**Provenance.** A mode is either *hypothesised* — written in advance from
literature and experience, with features and rules nominated by hand, as every
mode signed off in 2026 is — or *discovered* by clustering the feature space
(Stage 24). The field keeps the two distinguishable, so a discovered mode is
never silently merged into a hypothesised one, and a hypothesised mode that
clustering fails to corroborate is visibly still hypothesised. The lifecycle's
claim that a mode can be added without everything being rebuilt has been
tested once: the tissue-plausibility mode (implausible tissue under a label)
entered through the specification's own schema rather than through any list in
this document, and neither the existing entries, the schema, the rule engine
nor the corpus had to change for it.

**Co-detection is recorded, not suppressed.** Where a corpus case for one mode
legitimately fires a second mode's rule, or a mode-less detector — cropping a
vertebra at the border displaces its centroid off the fitted curve, so the
FOV-truncation case also fires the spline-offset detector — the specification
records both in the case's expected firing set with the reason, and the
discriminator says which mode explains the other. Whether a later rule lets one
mode explain the other away is a rule change, decided on its own evidence.

---

## 7. Technical Architecture

### 7.1 Language & runtime
- **Python 3.9+** (3.9 is the floor); Windows, macOS and Linux for development
  and use.
- Library-first, with a `segfacet` CLI (`run`, `build-reference`, `evaluate`)
  whose handlers defer heavy imports so `--help` stays fast.

### 7.2 Processing stack (CPU / GPU dual path)
- Core: NumPy, SciPy, scikit-image, NiBabel; PyRadiomics as an optional extra
  with a builtin first-order fallback.
- **Optional GPU acceleration** via CuPy, resolved at runtime (`cpu` / `gpu` /
  `auto`), with the CPU path as the reference and equivalence tests between
  the two. Never required.
- **No deep-learning framework**, ever: FACET reads label maps that other tools
  produced.

### 7.3 Packaging
- A pip-installable package with `[dev]`, `[radiomics]` and `[gpu]` extras; a
  constraints lockfile for reproducible installs.
- Reference distributions and heuristic configuration versioned and shipped
  with the package; **no dataset is bundled** — cohorts arrive through the
  adapters in §5.1.
- The Docker image and XNAT command definition from v2 are retained as legacy
  artefacts pending relocation to the programme repository; nothing depends on
  them.

### 7.4 Data formats
- Input: NIfTI scans + NIfTI instance label maps; documented, overridable label
  convention; cohort manifests.
- Output: JSON findings (primary, machine-readable), human-readable report,
  cohort-level JSON metrics and manifests; generated conformance artifacts
  (Markdown + JSON) committed in the repository.

### 7.5 Data flow
```
scan (optional) + instance segmentation
        │
        ▼
 [ I/O, orientation & label normalisation ]  ◀── per-dataset adapters
        │
        ▼
 [ feature extraction ]  ──(CPU | GPU)        ──► feature catalogue (generated)
        │
        ▼
 [ reference comparison + rule engine ]  ◀── reference distributions (VerSe)
        │        rules declare their modes  ◀── failure-mode specification (§6)
        ▼
 [ per-case verdict + report ]  ──► JSON + human report
        │
        ▼
 [ cohort harness: per-mode metrics, run-vs-run attribution, calibration ]
        │
        ▼
 [ cohort characterisation ]  ──► the programme repo / the researcher
                                 ──► traceability matrix (generated conformance)
```

---

## 8. Evaluation & Testing Strategy

**Three rungs of realism, never conflated.** Every detection, specificity and
calibration claim names its rung:

| Rung | Corpus | Role |
|---|---|---|
| 1 | hand-crafted fixtures (`synth/clean_gt.py`, `tests/synthetic.py`) | fast unit-test scaffolding **only** |
| 2 | real ground truth + scripted perturbation | threshold calibration, regression, sensitivity |
| 3 | real segmenter failures | validation of the objectives that say *real* |

Rung 2 needs only real VerSe GT and is available. Rung 3 and the curated
challenging cases arrive by hand-off from the programme repository and are
tracked as human gates in [`progress.md`](progress.md).

**Corpora and expectations.**
- **VerSe ground truth** — builds the reference feature set and is the positive
  control: GT should pass at a high rate, measured as a cohort false-positive
  rate on held-out subjects disjoint from calibration.
- **Perturbed ground truth** — the synthetic failure corpus (§5.6) applied to
  real GT, covering every mode the fixtures can express, each case recording
  its expected firing set; the specificity assertion (no unintended rule fires)
  holds on it, with every declared co-detection carrying a reason.
- **Real segmenter output** — SPINEPS and/or TotalSegmentator on real CT; Dice
  against GT as a divergence proxy, verdicts and feature divergence expected to
  track it.
- **Curated challenging cases** — real pathology, post-operative changes,
  atypical anatomy, border effects.

**Three levels of comparison** between a segmenter's output and ground truth:
verdict, segmentation overlap (Dice), and feature sets matched by label.

**Test hygiene.** Run-to-run byte comparisons are determinism checks; fresh-vs-
committed comparisons of generated artifacts go through a tolerance-by-
construction guard, so a dependency change is tolerated and a genuine change
(a verdict, a finding, a feature value) is caught. Capabilities gated on an
optional dependency or an external dataset skip cleanly when it is absent and
are recorded as unverified until exercised for real; a separate CI job installs
the optional dependencies and fails if a gated test merely skipped.

Success at this level: GT passes, injected failures are caught, verdicts track
segmentation quality, and every number is recorded with the corpus and rung it
was measured on.

---

## 9. Non-Functional Requirements

- **Portability:** CPU-only on any development host; optional GPU path.
- **Determinism:** CPU and GPU paths produce equivalent verdicts; generated
  artifacts regenerate byte-identically run-to-run.
- **Explainability:** every finding carries a human-readable reason; thresholds
  are documented and inspectable; every rule names its mode(s).
- **Modality-explicitness:** every intensity threshold states the modality it
  holds for; shape rules carry no modality assumption.
- **Robustness:** tolerant of varying field of view, spacing, anisotropy,
  orientation, partial or border vertebrae and missing levels, without crashing.
- **Performance:** per-case runtime acceptable for batch processing of
  thousand-session cohorts on a workstation.
- **Reproducibility:** pinned dependencies, versioned reference data, versioned
  heuristic configuration; every result traceable to tool + config + reference
  version; cohort manifests reproduce a corpus without committing bulk data.
- **Extensibility:** new modes, rules, features and abnormality classes without
  re-architecting; configuration-driven thresholds.
- **Maintainability:** library-first, tested, documented; `pytest` is the only
  gate.

---

## 10. Constraints & Assumptions

**Constraints**
- Python **3.9+**; runs CPU-only; no GPU may ever be required.
- **No deep-learning framework** is imported, in the package or its tests.
- No dataset is bundled and **no patient data enters git**; cohorts are
  supplied by path and manifest.
- Real segmenter output and clinical cohorts reach this repository only by a
  human's hand-off (human gates in [`progress.md`](progress.md)); the loop
  cannot fetch them.

**Assumptions**
- Input segmentations are **vertebra instance** label maps with a known or
  derivable label → anatomy convention.
- The original scan is available alongside the segmentation when intensity
  features are wanted; it is not needed for shape and topology.
- **VerSe** is available and suitable as ground truth for reference
  distributions and as the evaluation positive control.
- Modality is primarily spine **CT**; the shape rules transfer to MR unchanged,
  the intensity rules do not without their own calibration.
- Reviewers and annotators are available over time (Use Cases A and B).

---

## 11. Out of Scope

- **Correcting or editing segmentations** — FACET assesses and characterises;
  repair belongs to the segmenter or to the programme repository.
- **Training a model, or importing a training stack** — segmentation is
  consumed, not developed; fine-tuning and the SPINEPS runner are the programme
  repository's, and FACET must stay deterministic and torch-free to serve it.
- **Deployment** as an XNAT command, a service or a required container — FACET
  is a library and CLI; the retained XNAT artefacts are legacy pending
  relocation and nothing may come to depend on them.
- **A pipeline QC gate as a product** (v2's Use Case D) — the verdict is
  emitted; a blocking policy over it is the consumer's decision, not a FACET
  feature to design for.
- **A bespoke reviewer GUI** — reporting targets standard formats; interactive
  review tooling beyond reports is not a commitment.
- **A supervised abnormality classifier from day one, or any deep
  classification head** — the classification arm is a classical, feature-based
  extension layered on the rules (Use Case B), not an initial deliverable.
- **Non-spine anatomy** and non-vertebra structures.
- **Real-time or clinical-decision use** — a research tool, not a certified
  device.
- **Re-implementing what the programme repository owns** — supervision signals,
  loss terms, model runners.

**MR is not excluded — it is lower priority.** The shape and topology
assessments read only the label map and are modality-agnostic. Intensity rules
are framed per modality (§1 principles); their CT defaults stay valid, and an
MR calibration is an addition, not a redesign.

---

## 12. Success Criteria

The project is successful when FACET can **automatically**:

1. **Characterise a segmenter on a real cohort** — for a real segmenter's output
   on a real cohort, report per catalogued failure mode its frequency, its
   severity distribution, the cases exhibiting it and the features that isolate
   it, with every number traceable to the rules and features that produced it.
2. **Detect empty or trivially failed segmentations.**
3. **Highlight wrong segmentation labels** — misaligned or mislabelled
   vertebrae.
4. **Highlight out-of-distribution labels** — including cases not yet modelled
   (post-operative changes, pathologies), as the basis for extending the
   catalogue with manual labels.
5. **Be robust to explicitly handled abnormalities** — fractures, compression,
   scoliosis within the approved envelope, implants — accounting for them rather
   than naively flagging them.
6. **Pass ground truth** — held-out real VerSe GT passes at a false-positive
   rate ≤ 0.10 without sensitivity regression.
7. **Track segmentation quality** — flag rate and feature divergence correlate
   with Dice against ground truth.
8. **Conform to its own catalogue** — every mode at `implemented` or above has
   a declared rule, every `validated` mode is demonstrated at its recorded
   evidence rung, every rule names a mode or its reason, the generated
   traceability matrix agrees with the authored specification, and no factual
   claim in any of them was accepted on its shape.
9. **Run CPU-only**, with an optional, equivalent GPU-accelerated path.
