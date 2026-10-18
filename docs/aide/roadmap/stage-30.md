> Stage 30's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 30`, run on the main or queue branch, moves it back.

## Stage 30 — Failure-Mode Specification: the §6 catalogue as an authored source (G2, G7, G8)

> **⚠️ Annotated 2026-09-15 — read before the text below.** This stage is in progress
> (items 143–150 ✅, item 151 open), so its goal, deliverables and acceptance stand as
> written. D6's review did not confirm the catalogue it was shown; the maintainer
> re-organised it inside item 150 (recorded in
> [`items/150-maintainer-sign-off-of-the-specification.md`](../items/150-maintainer-sign-off-of-the-specification.md),
> "Stage-30 maintainer sign-off"). What the text below cannot carry:
>
> - **The catalogue is sixteen modes in a one-tier hierarchy plus one condition**, not
>   the eight §6 seed modes plus a ninth and a tenth. 1 segmentation accuracy › 2 fused,
>   3 split, 4 islands, 5 holes, 6 vertebra not segmented, 7 hallucinated vertebra;
>   8 semantic mislabelling › 9 out-of-order label sequence, 10 skipped level label,
>   11 unprompted numbering variant, 12 shifted label sequence, 13 collapsed labels,
>   14 duplicated label; 15 overlapping segments; 16 implausible tissue under a label.
>   The seed's "label not aligned with the vertebra it names" is retired, and "partial
>   vertebra at the image border" (seed mode 6) is the **FOV-truncation condition**, not a
>   mode. Ids are assigned by the specification; `ModeSpec` gained `parent` and `scope`,
>   `CONDITIONS` was added, and `validated` now needs a non-empty agreeing case that fires
>   one of the mode's own rules.
> - **Id mapping for the text below** (the first target of each arrow is that seed's
>   `VISION_SEED_DISPOSITION`). Seed mode 1 (misalignment) → retired; seed 2
>   (over-/under-segmentation) → mode 1, with 2 and 3 split from it; seed 3 (islands) → 4;
>   seed 4 (semantic
>   mislabelling) → 8; seed 5 (not all segmented) → 6; seed 6 (border) → the condition;
>   seed 7 (non-continuous sequence) → 9, with 10 and 11 split from it; seed 8 (overlap) →
>   15; D3's "ninth mode" →
>   16; D3's "collapsed or duplicated label set" → 13 and 14.
> - **How the acceptance bullets are read** (wording unchanged):
>   - *Criterion 2* — `mode6_crop_at_border` still expects `{border, mislabel}` with its
>     reason; it is carried by `CONDITIONS["fov_truncation"]` at `failure_mode` 0, and its
>     `mislabel` firing is the mode-less spline-offset detector, a recorded co-detection.
>   - *Criterion 3* — "mode 8's rung" is **mode 15's** (overlapping segments), still
>     `structurally-unobservable` with its single-channel mechanism.
>   - *Criterion 5* — "the ninth mode" is **mode 16**, `validated`, declared by both
>     intensity rules. "The eight seed names equal `vision.md` §6's list" is **replaced**
>     by `failure_modes.vision_seed_conflicts()`: every §6 seed title has a
>     `VISION_SEED_DISPOSITION` entry resolving to a mode, the condition or `retired`. The
>     names deliberately no longer match; §6's numbered list is re-issued in Stage 31.
>   - *D2's discriminator examples* ("mode 6 has a border-touching face and mode 1 has
>     none"; "modes 2 and 3 differ in whether the dominant body is intact") describe the
>     seed catalogue; the specification's `discriminator` fields are the record.
> - **What the review left behind** — the eval-harness re-key, the §6 re-issue, and the
>   detectors and fixtures the new sub-modes need — is owned by **Stages 31 and 32**, not
>   by item 151, which validates this stage against the readings above.

**Goal.** Queue-019 produced three defects of one class in four items: a factual claim
about the failure modes authored as prose, shipped into a committed artifact, and
accepted by a check that tested the claim's *shape* rather than its *truth* (item 137's
evidence sentence past a length floor; four of eight `MODE_RUNGS` mechanisms past a
token-presence check; a `rule_to_mode: complete` flag derived from declaration state).
Each fix made the next check stronger, and two of the five corrected sentences were
provably not catchable by any such check, because the error was about *which of two
genuinely-read sibling fields* drives detection. **The root cause is that no document
defines the modes.** Today they exist as five partial sources that agree with each other
without any of them being a specification — `vision.md` §6's one-line list,
`synth/perturbation.py::FAILURE_MODE_NAMES`, `feature_docs.py::MODE_ANCHOR_PATHS`, the
`Expectation` literals in `synth/*.py`, and `traceability.py::MODE_RUNGS` — and the
generated matrix (item 138) cross-checks them without being able to adjudicate them.
Mode 6 is the proof: all three operational sources agree on `border`, and the measurement
shows `border` **and** `mislabel`.

This stage authors the specification `vision.md` v3 §6 describes — one authored source
per mode, from which every generated artifact becomes a **conformance report** — and
collapses the five partial sources onto it. It is an authoring stage with a human
checkpoint, in the sense Stages 19 and 27 are: the definitions and discriminators are the
ground truth every later check consults, so a person reads them before anything is
measured against them. It writes no new rules and adds no corpus cases beyond what the
ninth mode needs; a rule it finds wrong is recorded and handed back.

**Deliverables** (D0 lands first; D1–D5 are one critical path; D6 gates the remainder of
Stage 20; the carried defects and open `insights.md` entries each deliverable absorbs are
named inline, by originating item and date, so the queue that draws on this stage ticks
them):

- **D0 — correct the synthetic corpus's S-axis stacking before anything is measured.**
  `synth/clean_gt.py::build_clean_spine` stacks ascending labels along ascending axis 2, so
  every in-repo driver advances superiorly while real VerSe input advances caudally — the
  inversion that hid item 131's traversal-direction defect for nine items and that flips
  the sign of any future feature measured against +S (carried defect, item 131,
  2026-08-31). Correct the stacking, regenerate every committed corpus value and both
  reference artifacts, and only then record the expected firing sets D2 carries — so the
  specificity baseline Stage 20's ratchet later pins is measured on the corrected corpus,
  as that entry asks. This is a corpus-value change, not a rule change; a rule whose
  firing moves under it is a finding, recorded and handed back.
- **D1 — the specification module and its rendering.** One frozen declaration per mode
  in a module under `src/segfacet/` (the spec-author names it; the shape follows
  `RuleModeDeclaration`), carrying vision §6's fields: `id`, `name`, `definition`,
  `discriminator`, `observability` (single-channel-observable · needs-paired-scan ·
  structurally-unobservable), `candidate_features` (hypothesised feature paths, with the
  Stage-18 per-mode *metric*'s anchor path labelled as exactly that), `intended_rules`
  (naming the detector where a rule has several), `corpus_cases` with an **expected**
  firing set per case, `severity`, `status`, `provenance` (hypothesised · discovered). The
  lifecycle `status` is authored only for `proposed` and `specified`; `implemented` (≥1
  registered rule declares the mode) and `validated` (a corpus case's measured firing
  equals its expected firing) are **derived**, and a hand-set value that disagrees with
  live state is a test failure. Rendered to `docs/aide/failure_modes.generated.{md,json}`
  by zero-argument regeneration, byte-reproducible, written with `\n` bytes and pinned
  `text eol=lf` (CLAUDE.md Gotchas) — the rendering is the review surface for D6.
- **D2 — the eight hypothesised modes, specified.** Every one of vision §6's eight modes
  entered with every field, each `discriminator` naming its nearest neighbours: mode 6 has
  a border-touching face and mode 1 has none; modes 2 and 3 differ in whether the dominant
  body is intact; modes 1 and 4 differ in whether the label's *identity* or its *position*
  is wrong. Gate `gate-0fdd`'s decisions encoded as data, not prose: `mode6_crop_at_border` expects
  `{border, mislabel}` with its reason (the crop displaces the centroid by a measured
  17.5 mm off the curve); the evidence rung is authored **per mode ↔ rule edge**
  (synthetic-demonstrable · needs-real-data · structurally-unobservable) and the mode's
  rung is derived as its strongest edge, so `reference_delta` on modes 1 and 2 and
  `bounds` on mode 2 — analytic edges no corpus case demonstrates — are visibly weaker
  than the demonstrated ones; mode 8 stays structurally-unobservable with its
  single-channel mechanism; mode 7's rung records its single-rank-descent cap.
- **D3 — the ninth mode enters through the lifecycle.** *Implausible tissue under a
  label* (soft tissue or air, metal or implant, a degenerate uniform region) — the mode
  `insights.md` recorded as missing on 2026-09-02 and the mode the `intensity` and
  `intensity_reference_delta` rules already serve — is added as a specification entry
  with `observability = needs-paired-scan` and a stated modality (CT), those two rules'
  `RuleModeDeclaration`s move from mode-less to declaring it, and
  `tests/corpus/intensity/manifest.json`'s four cases gain the `failure_mode` and expected
  firing fields the geometric manifest already carries. It is expected to land at
  `implemented` or `validated` on live state, and it is the test of vision §6's claim
  that a mode can be added without everything being rebuilt. Driving those four cases
  needs the intensity sibling of `synth/regression.py::pipeline_findings` that has never
  existed (`insights.md`, item 139, 2026-09-03 — item 139 re-composed it privately inside
  `traceability.py`); build it in `synth/regression.py`, where the geometric one lives.
  Alongside, the catalogue gains its first **`proposed`** entry — *collapsed or
  duplicated label set*, the silent case where two labels share an exact centroid, Stage 3
  degrades, every `stage3`-reading rule short-circuits and no finding of any kind is
  raised (carried defect, item 129, 2026-08-31) — with `candidate_features =
  (features.stage3_unavailable,)` and no rule, so the conformance report shows a listed,
  unimplemented mode for the first time. The rule itself is not this stage's.
- **D4 — collapse the five partial sources.** `FAILURE_MODE_NAMES` is derived from the
  specification or retired; `MODE_RUNGS` is retired in favour of D2's per-edge rungs;
  `MODE_ANCHOR_PATHS` stays, documented as the Stage-18 metric path and referenced from
  `candidate_features`, never presented as what a rule reads; `traceability.py`'s
  parse of `vision.md` §6 and the tests that hand-transcribe that list re-point at the
  specification as the primary record, with one conformance check kept in the other
  direction — the eight seed entries' names equal `vision.md` §6's list — so the vision
  stays the seed and the specification the truth. `Expectation` and `RuleModeDeclaration`
  remain the two operational claims, now checked against the specification in both
  directions (a declared mode the specification does not list; a specification
  `intended_rule` that declares no such mode; a corpus case the specification does not
  carry, or that carries a different expected set). Three located defects in that seam
  close here because the specification is what replaces the mechanism they sit in
  (`insights.md`, item 136, 2026-09-02, all three): the `"corpus"` evidence tag is an
  exact-element membership test over an unvalidated tuple, so a near-miss silently
  disables the declaration-to-corpus check; `RuleModeDeclaration.__post_init__` never
  checks that `evidence` and `modes` are tuples, so a bare string binds the tag by
  substring accident and a list stays mutable; and the corpus-to-declaration direction
  iterates registered rules, so a corpus case designating a `rule_id` no rule registers is
  never reported. With per-edge rungs in the specification the free-form `"corpus"` tag is
  retired rather than hardened, and both remaining checks are rewritten against the
  specification. Item 136's **rule-granular** mode attribution (`insights.md`, item 138,
  2026-09-02 — bookkeeping paths such as `reference_delta.lower_pct` inherit a rule's full
  mode tuple) is addressed at the same seam: `intended_rules` names the detector, and the
  declaration gains a per-detector or per-path attribution the catalogue can render, so
  `docs/aide/feature_catalogue.generated.md` no longer paints bookkeeping paths with modes
  they cannot evidence.
- **D5 — the traceability matrix becomes the conformance report.** Item 138's
  `build_matrix` reads the specification as its primary source: per mode, the derived
  status, the per-edge rungs, and per corpus case the **expected** set beside the
  **measured** set with agreement scored — a disagreement is a failure, which is the
  check none of queue-019's shape tests could express. The metric anchor path and the
  rule's read paths render as two separately labelled columns. The exercise columns item
  139 specified are **not** built here; they are Stage 20's, re-specified against this
  output. Two test-hygiene entries are settled while the builder is open rather than after
  a third extension: `tests/test_138_traceability_matrix.py` calls `build_matrix()` 42
  times with no shared fixture, and every extension multiplies across the module
  (`insights.md`, item 139, 2026-09-03) — set the call-count discipline now, as one
  fixture per monkeypatch group, never a cache inside the generator that would defeat the
  adversarial tests; and `tests/committed_artifact_guard.py`'s closed `GROUNDS` vocabulary
  has no member for a **float-free** derived artifact (`insights.md`, item 138,
  2026-09-02), which is exactly what D1's rendering and the matrix are — add the sixth
  ground (`no-float-leaf`, discharged by the artifact's own no-float-leaf test) so both
  make the byte-exact claim under the guard instead of beside it.
- **D6 — the human sign-off checkpoint.** The maintainer reads
  `failure_modes.generated.md` entry by entry — definition, discriminator, expected
  firing sets, severities — and signs it, with the date and outcome recorded in the
  specification module's own docstring the way Stage 19's steering review was recorded
  in `feature_docs.py::STATUS_OVERRIDES`. Until the sign-off is recorded, the remainder of
  Stage 20 is not queued.
- **D7 — stage validation.** Regenerate both artifacts from a clean tree, drive every
  corpus case across both committed corpora and confirm expected equals measured, confirm
  the derived statuses against live state, and record the resulting per-status,
  per-rung count in `progress.md` as a measured number.

**Dependencies.** Stage 20's items 136–138 (the declaration seam, the disposition and the
matrix this stage re-points) — all ✅. **Runs before the remainder of Stage 20** (items
139–142, re-specified against D1–D5) and therefore before Stages 27, 21 and 16. Edits
neither `vision.md` nor `roadmap.md`: vision v3 §6 already carries the principles this
stage implements, and a finding that the principles are wrong is recorded and handed
back.

**Validation / acceptance.**

- Every mode in the specification carries every schema field, a status from the
  four-state vocabulary and a provenance; `implemented` and `validated` are derived
  from live state, and a hand-set status that disagrees with the registry or the corpus
  fails a test naming the mode (**G8**).
- For every corpus case across both committed corpora, the measured firing set equals
  the specification's expected firing set, and `mode6_crop_at_border` expects
  `{border, mislabel}` with a recorded reason (**G2**).
- Every mode ↔ rule edge carries an authored evidence rung and every mode's rung is
  derived from its edges; the analytic-only edges are rendered as such, and mode 8's
  rung names the single-channel mechanism (**G2**).
- `failure_modes.generated.{md,json}` and the traceability matrix regenerate
  byte-identically from a clean tree, name the specification as their primary source,
  and render the metric anchor path and the rule's read paths as separately labelled
  columns.
- The ninth mode (implausible tissue) is present at `implemented` or `validated`, with
  `intensity` and `intensity_reference_delta` declaring it and the intensity corpus
  cases carrying expected firing sets; `FAILURE_MODE_NAMES` and `MODE_RUNGS` are
  derived from or replaced by the specification, and the eight seed names equal
  `vision.md` §6's list (**G8**).
- The specification's rendering is signed off by the maintainer, with the date and
  outcome recorded in the module (**G8**).
- `build_clean_spine` stacks labels caudally along +S like real VerSe input, every
  committed corpus value and both reference artifacts were regenerated after the
  correction, and no expected firing set in the specification predates it (**G7**).
