# Item 151 — Validate stage 30: Failure-Mode Specification — the §6 catalogue as an authored source

> **Created:** 2026-09-15 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 30 — Failure-Mode Specification: the §6 catalogue as an authored source
> **Queue:** [`../queue/queue-020.md`](../queue/queue-020.md) · Item 151
> **Objectives:** G2, G7, G8
> **Suggested branch:** `aide/151-validate-stage-30-failure-mode`

---

## Description

Stage 30 **D7**. Close Stage 30 by **replaying its acceptance end to end from a
clean tree**, not by re-running the unit suite. Items 143–150 each proved their
own deliverable against their own tests; this item asks the question the
stage's acceptance section poses — *does the shipped tree now behave the way
the stage claimed it would* — and records the answer in `progress.md` whether or
not it is the answer the stage hoped for. It is the only item authorised to
tick Stage 30's acceptance criteria (item 150's spec, Decision D1).

Five obligations are specific to this stage.

**The replay validates the signed-off catalogue, not the one the queue line
describes.** Queue-020's item-151 paragraph was written on 2026-09-03, before
item 150's maintainer review re-organised the catalogue (human gate 5, approved
2026-09-15; commits `3cb522f` and `ce0c6ec`). The specification now carries
**sixteen modes in a one-tier hierarchy plus one condition**
(`segfacet.failure_modes.SPECIFICATION`, `CONDITIONS["fov_truncation"]`), not
eight seed modes plus a ninth and a tenth. Stage 30's acceptance text in
`roadmap.md` is immutable, and roadmap v3.1's post-sign-off annotation at the
head of Stage 30 (mirrored in `progress.md`'s Stage 30 note) states how each
criterion is read. Every acceptance criterion below is grounded in the current
`src/segfacet/failure_modes.py`, the committed
`docs/aide/failure_modes.generated.{md,json}`, and that annotation. The mapping
from the queue's wording to what is actually checked is recorded in Decisions
& Trade-offs (D1–D9), and every `progress.md` evidence note names the reading
it relied on.

**"From a clean tree" means a fresh clone with its own venv.** The item-149
validator ticked criteria 2 and 4 on in-tree evidence, and both ticks were
reverted (`4502119`, `5f94b2f`) because the queue line asks for a clean-tree
replay. This item regenerates every Stage 30 artifact inside a `git clone` of
this branch, with a venv built there, and compares against the committed copies.
It never uses a second tree pointed at by `PYTHONPATH`: CLAUDE.md's Gotchas
record that the editable install's meta-path finder silently shadows it.

**Criterion 7 is already ticked, and this item re-verifies it rather than
reading the tick as settled.** Item 143's validator ticked it on 2026-09-03
(commit `5a663d0`), before the specification module existed. Its clause "no
expected firing set in the specification predates it" could not be measured
then (`insights.md`, item 143, 2026-09-03: "Item 151 must re-verify criterion 7
against the built specification and not read the existing tick as settled").
The attestation is immutable, so the result goes into a correction trail:
`aide progress amend` if the replay confirms it, `aide progress retract` if it
does not.

**Counts are recorded split by what they measure.** Queue-020 requires the
per-status and per-rung counts as measured numbers, "never one number over a
list that mixes hypothesised and demonstrated modes". Measured 2026-09-15 on
this branch's base `7e4bb5c`, from the committed rendering:

| Derived status | Modes | Count |
|---|---|---|
| validated | 1, 4, 6, 9, 15, 16 | 6 |
| implemented | 2, 3, 8 | 3 |
| specified | — | 0 |
| proposed | 5, 7, 10, 11, 12, 13, 14 | 7 |

| Derived mode rung | Modes | Count |
|---|---|---|
| synthetic-demonstrable | 1, 4, 6, 9, 16 | 5 |
| needs-real-data | 2, 3, 8 | 3 |
| structurally-unobservable | 15 | 1 |
| none (no edges) | 5, 7, 10, 11, 12, 13, 14 | 7 |

Per-edge rungs over the 17 `IntendedRule` edges: synthetic-demonstrable 5,
needs-real-data 11, structurally-unobservable 1. Of the 6 `validated` modes, 5
are demonstrated by a pipeline-detected case (`pipeline` or
`intensity_pipeline`), and one, mode 15, only by a `reconstructed_record` case.
All 16 modes carry `provenance = hypothesised`. The item re-measures every one
of these numbers. The numbers above are where it starts, not what it must find.

**Stage 30 changes no Environment-Gated row, and the replay says why.** The
intensity harness pins `enable_pyradiomics=False` by default
(`segfacet.synth.regression.intensity_pipeline_findings`, item 146 A2), so no
measured firing set depends on PyRadiomics. No criterion needs Docker, a GPU or
the real VerSe19 cohort.

**In scope.** The clean-clone replay, the scratch mutations that prove the
derived statuses are live, the measurements, the evidence notes and acceptance
bookkeeping in `progress.md` through the `aide progress` verbs, and an in-suite
module pinning the mechanically checkable half.

**Not in scope.** Fixing anything found: a divergence is a finding, logged to
`insights.md` and reported, never remediated here. No failure mode, rule,
threshold, corpus case or generated artifact changes. Anything left behind by
the item-150 review (the eval-harness re-key, the `vision.md` §6 re-issue, the
detectors and fixtures the new sub-modes need) belongs to Stages 31 and 32 (see
roadmap v3.1). Deliverable bullets and item statuses are written by
`aide progress set` / `aide merge`, never by hand. Triaging the open insight
backlog is the queue boundary's job. This item ticks exactly one insight entry,
the one addressed to it (AC39).

## Acceptance Criteria

_Two kinds of criterion sit below, the item-135 precedent. **In-suite**
criteria are pinned by `tests/test_151_stage30_validation.py`. **Replay**
criteria are executed by the validator and recorded verbatim in Decisions &
Trade-offs. The Testing Strategy says which is which. A criterion annotated
*(closes Stage 30 criterion M)* is part of the evidence for that criterion. A
criterion without the annotation closes none._

### The clean-tree rig

- [ ] **AC1: the replay runs in a fresh clone whose code is the clone's own.**
  (Replay.) Clone this repository into the scratchpad with
  `git clone --branch aide/151-validate-stage-30-failure-mode`, bootstrap a venv
  there with `python <clone>/.aide/scripts/aide.py --repo <clone> env --bootstrap`
  (the §3 explicit-root form), and
  run Python from that venv with `-P`, so the working checkout's cwd is never on
  `sys.path`. Record: the clone path; the clone's `HEAD` SHA, which must equal
  this branch's tip at replay start; and the printed `segfacet.__file__` and
  `tests.__file__`, both of which must resolve under the clone. A resolution
  under the working checkout invalidates every clone result, and the replay is
  redone.

### Criterion 4 — regeneration, primary source, labelled columns

- [ ] **AC2: the four conformance artifacts regenerate byte-identically from the
  clean tree.** (Replay.) In the clone,
  `python -P -m segfacet.failure_modes --json <scratch>/fm.json --md <scratch>/fm.md`
  and `python -P -m segfacet.traceability --json <scratch>/tm.json --md <scratch>/tm.md`
  produce four files. `cmp` against the clone's committed
  `docs/aide/failure_modes.generated.json`, `failure_modes.generated.md`,
  `traceability_matrix.generated.json` and `traceability_matrix.generated.md`
  exits `0` for each. A second regeneration into a different scratch path is
  `cmp`-identical to the first. The result is recorded per artifact.
  *(closes Stage 30 criterion 4)*
- [ ] **AC3: the matrix names the specification as its primary source, and its
  content comes from that source.** (In-suite.) The committed matrix JSON's
  `primary_source` equals `"src/segfacet/failure_modes.py"`. That path resolves
  to the module `segfacet.failure_modes` is loaded from. The Markdown carries
  the line ``Primary source: `src/segfacet/failure_modes.py`.``. For every mode
  id, the matrix row's `title` equals `SPECIFICATION[id].name`, `authored_status`
  equals `SPECIFICATION[id].status`, `edge_rungs` equals that mode's
  `intended_rules` as `(rule_id, detector, evidence_rung)` triples in order, and
  the row's key set equals `set(SPECIFICATION)` exactly.
  *(closes Stage 30 criterion 4)*
- [ ] **AC4: the specification rendering names the module it is rendered
  from.** (In-suite.) The committed `failure_modes.generated.json`'s `note` and
  the Markdown's note paragraph both name `src/segfacet/failure_modes.py`. The
  JSON's `modes` list is equal, entry for entry, to
  `specification_to_dict()["modes"]` computed live. Its `conditions` list is
  equal to the live `conditions`. *(closes Stage 30 criterion 4)*
- [ ] **AC5: the metric anchor path and the rule read paths are separate,
  separately labelled columns in the matrix.** (In-suite.) The matrix Markdown's
  modes table header contains both `Stage-18 metric anchor paths` and
  `Rule signal read paths` as distinct cells. For every mode row,
  `anchor_paths` equals `feature_docs.MODE_ANCHOR_PATHS.get(id, ())`. For at
  least one mode the two columns differ (measured 2026-09-15: modes 6, 8, 9 and
  16, among others), and for every such mode both columns render non-identical
  cell contents in the Markdown row.
  *(closes Stage 30 criterion 4)*
- [ ] **AC6: the specification rendering labels anchor paths as metric anchors
  and never as rule reads.** (In-suite.) In `failure_modes.generated.md`, every
  `CandidateFeature` with role `stage18-metric-anchor` renders under the literal
  label `Stage-18 metric anchor path`. Every other candidate path renders with
  its role label, and the rendering carries no rule read path under the anchor
  label. *(closes Stage 30 criterion 4, the rendering's half, under reading D4)*
- [ ] **AC7: the feature catalogue regenerates from the clean tree.** (Replay.)
  In the clone, `python -P -m segfacet.catalogue --json <scratch>/fc.json --md <scratch>/fc.md`
  produces a Markdown that is `cmp`-identical to the committed
  `docs/aide/feature_catalogue.generated.md`, and a JSON that
  `segfacet.synth.golden.assert_matches_committed_artifact` accepts against the
  committed `feature_catalogue.generated.json`. The JSON is float-bearing, so
  whether it is also byte-identical is recorded, not required. Stage 30's
  acceptance does not name this artifact, so this AC closes no criterion
  (reading D6).

### Criterion 2 — expected equals measured, across both corpora

- [ ] **AC8: every corpus case in both committed manifests measures its
  expected firing set.** (In-suite, and replayed in the clone.) For every case in
  `tests/corpus/manifest.json` and `tests/corpus/intensity/manifest.json`,
  enumerated from the manifests and never from a hardcoded list, the set of
  `rule_id`s measured through the public `segfacet.synth.regression` harness
  for that case's `detection` value equals the expected set. The expected set
  is the carrying `ModeSpec` or `ConditionSpec` `corpus_cases` entry's
  `expected_firing`. For a `failure_mode == 0` case with no `condition`, it is
  the empty set (reading D2). The number of cases compared equals the summed
  manifest case count (measured 2026-09-15: 11 + 4 = 15), and the replay
  records each case's measured set. *(closes Stage 30 criterion 2)*
- [ ] **AC9: no committed corpus case is unspecified.** (In-suite.) Every case
  whose manifest `failure_mode` is non-zero is carried by exactly one
  `SPECIFICATION[failure_mode].corpus_cases` entry. Every case carrying a
  `condition` is carried by exactly one `CONDITIONS[condition].corpus_cases`
  entry. `build_matrix()`'s conformance section has an empty
  `unspecified_cases` and an empty `disagreements`, and `agree_count` equals
  AC8's case count. *(closes Stage 30 criterion 2)*
- [ ] **AC10: `mode6_crop_at_border` expects exactly `{border, mislabel}` with a
  recorded reason, as the FOV-truncation condition's fixture.** (In-suite.)
  `CONDITIONS["fov_truncation"].corpus_cases` carries `mode6_crop_at_border`
  with `set(expected_firing) == {"border", "mislabel"}` and a non-empty `reason`.
  Its manifest entry has `failure_mode == 0` and `condition == "fov_truncation"`.
  No `SPECIFICATION` entry carries the case. *(closes Stage 30 criterion 2,
  under reading D3)*
- [ ] **AC11: the recorded reason's two causal claims hold when measured.**
  (In-suite.) On the committed `mode6_crop_at_border` fixture,
  `extract_feature_record(..., bundled_default_config())` reads
  `per_label["22"].geometry.touches_anterior is True`. The same record's
  `stage3.per_label_offsets` entry for label 22 has `is_terminal is False` and
  an `offset_mm` above the bundled `mislabel` `max_offset_mm` (13.0 mm at
  writing). Measured 2026-09-15: 17.507 mm, the value item 145's queue line
  asked to be re-measured on the corrected corpus. On `clean_control`, label 22
  reads `touches_anterior is False`. The replay records the measured offset.
  *(closes Stage 30 criterion 2)*

### Criterion 3 — per-edge rungs, derived mode rungs, analytic edges, mode 15

- [ ] **AC12: every mode ↔ rule edge carries an authored rung from the closed
  vocabulary.** (In-suite.) Every `IntendedRule` in every `SPECIFICATION` entry
  has `evidence_rung in EVIDENCE_RUNGS`. The total edge count is derived live
  (measured 2026-09-15: 17). *(closes Stage 30 criterion 3)*
- [ ] **AC13: every mode's rung is derived from its edges.** (In-suite.) For
  every mode, an independent recomputation (the strongest rung by position in
  `EVIDENCE_RUNGS` among the mode's edges, or `None` with no edges, written in
  the test and not delegated to `derive_mode_rung`) equals
  `derive_mode_rung(mode)`, the committed rendering's `derived_rung`, and the
  matrix row's `rung`, where `None` renders as `""` in the matrix. For one mode
  with at least two distinct edge rungs, an in-memory copy with its strongest
  edge weakened changes the derived rung. *(closes Stage 30 criterion 3)*
- [ ] **AC14: the analytic-only edges are rendered as such.** (In-suite.) For
  every `(mode, rule)` pair in the matrix's `rule_attribution`, the attribution
  is `"analytic"` exactly when the rule is absent from the **measured** firing
  set of every one of that mode's corpus cases (AC8's measurement, not the
  authored `expected_firing`), and `"corpus"` otherwise. No edge attributed
  `"analytic"` carries the rung `synthetic-demonstrable`. The analytic edge
  list is recorded (measured 2026-09-15: `bounds` and `reference_delta` on
  modes 1–4, `reference_delta` on mode 8, and `intensity_reference_delta` on
  mode 16). *(closes Stage 30 criterion 3)*
- [ ] **AC15: mode 15's rung is structurally-unobservable and its mechanism names
  the single-channel invariant.** (In-suite.) `derive_mode_rung(SPECIFICATION[15])
  == "structurally-unobservable"`. `SPECIFICATION[15].mechanism` states that a
  single-channel integer label map cannot assign two labels to one voxel.
  Mode 15 is what criterion 3's "mode 8" means after the sign-off (reading D3).
  *(closes Stage 30 criterion 3)*
- [ ] **AC16: the single-channel mechanism holds when measured.** (In-suite.) On
  the committed `mode8_force_overlap` fixture, the case carried by mode 15,
  `extract_feature_record` yields `overlaps == []` and
  `synth.regression.pipeline_findings` yields no `overlap` finding. The same
  case's `reconstructed_findings` yields an `overlap` finding, and its manifest
  `detection` is `reconstructed_record`. Measured 2026-09-15: pipeline findings
  `[]`, reconstructed `['overlap']`. *(closes Stage 30 criterion 3)*

### Criterion 1 — schema, vocabularies, derived statuses

- [ ] **AC17: every mode carries every schema field with a valid value.**
  (In-suite.) For every `SPECIFICATION` entry, every name in
  `dataclasses.fields(ModeSpec)` is an attribute. `name`, `short_name`, `scope`,
  `definition`, `discriminator`, `mechanism`, `observability`, `severity`,
  `status` and `provenance` are non-empty strings. `status in AUTHORED_STATUSES`,
  `provenance in PROVENANCE`, `observability in OBSERVABILITY` and
  `scope in SCOPES`. `parent` is `None` or a top-level `SPECIFICATION` key. The
  three tuple fields `candidate_features`, `intended_rules` and `corpus_cases`
  are tuples whose elements are `CandidateFeature`, `IntendedRule` and
  `CorpusCaseExpectation` respectively. No tuple field is required to be
  non-empty, whatever the authored status (reading D5): `ModeSpec.__post_init__`
  enforces no emptiness, and the one status consequence of an empty
  `corpus_cases` (the mode cannot derive `validated`) is AC18's
  at-least-one-corpus-case clause, not this AC's. *(closes Stage 30 criterion 1)*
- [ ] **AC18: the derived statuses equal an independent live derivation.**
  (In-suite.) The test recomputes each mode's status without calling
  `derive_status`:
  - `validated` iff a registered rule's declaration lists the mode, the mode has
    at least one corpus case, every case's measured set equals its expected set,
    and at least one case has a non-empty expected set naming one of the mode's
    own `intended_rules`;
  - otherwise `implemented` iff a registered declaration lists the mode;
  - otherwise the authored status.

  The recomputation equals `derive_status(mode)`, the committed rendering's
  `status_derived`, and the matrix row's `status`, for every mode, and every
  derived value is in `STATUSES`. *(closes Stage 30 criterion 1)*
- [ ] **AC19: a hand-set status in the source fails, naming the mode.** (Replay,
  in the clone, only after AC2, AC7, AC8 and AC31–AC33 are recorded.) Edit
  `_MODE_2`'s authored `status` in the clone's `src/segfacet/failure_modes.py` to
  `"validated"`. Mode 2 derives `implemented`, so this is a hand-set value that
  disagrees with live state. Then run
  `python -P -m pytest <clone>/tests/test_144_failure_mode_specification.py -x -q`.
  The run fails, and the failure text names mode 2 (`ModeSpec 2`). Record the
  text verbatim, then restore the file and confirm with `cmp` against the
  working checkout's copy. *(closes Stage 30 criterion 1)*
- [ ] **AC20: a status that disagrees with the registry fails, naming the
  mode.** (Replay, in the clone.) In the clone's `src/segfacet/heuristics/overlap.py`,
  change the declaration's `modes=(15,)` to `modes=(5, 15)` (strictly ascending,
  as `RuleModeDeclaration` requires). Mode 5 is authored `proposed` and has no
  declaring rule. Then run
  `test_144_failure_mode_specification.py::test_ac11_shipped_specification_has_no_conflicts`.
  The run fails, and `specification_conflicts()` output names mode 5 as authored
  `proposed` but deriving `implemented`. Record the text verbatim, then restore
  the file and confirm with `cmp`. *(closes Stage 30 criterion 1)*
- [ ] **AC21: a hand-edited derived status in the committed rendering fails.**
  (Replay, in the clone.) Change mode 16's `status_derived` in the clone's
  `docs/aide/failure_modes.generated.json` from `validated` to `implemented`,
  then run that artifact's committed-comparison tests in
  `test_144_failure_mode_specification.py` and
  `test_150_maintainer_sign_off.py`. At least one fails. Record the failure text
  verbatim, and record whether it names mode 16 or only a JSON position. If it
  names only a position, that is logged as a finding: AC19 and AC20 already
  establish criterion 1's "naming the mode" clause. Restore the file and confirm
  with `cmp`. The mutation clone is deleted after AC19–AC21. No mutation is ever
  made in the working checkout. *(closes Stage 30 criterion 1)*

### Criterion 5 — mode 16, the retired partial sources, the seed disposition

- [ ] **AC22: mode 16 is present at `implemented` or `validated`.** (In-suite.)
  `SPECIFICATION[16].name == "Implausible tissue under a label"`,
  `observability == "needs-paired-scan"`, and `derive_status(SPECIFICATION[16])`
  is `implemented` or `validated` (measured 2026-09-15: `validated`). Mode 16 is
  criterion 5's "ninth mode" (reading D3). *(closes Stage 30 criterion 5)*
- [ ] **AC23: both intensity rules declare mode 16.** (In-suite.) Among
  `heuristics.rule.iter_rule_declarations()`, the declarations of `intensity`
  and `intensity_reference_delta` are both non-`None` and both list `16` in
  `modes`. `SPECIFICATION[16].intended_rules` names both rule ids.
  *(closes Stage 30 criterion 5)*
- [ ] **AC24: the intensity corpus cases carry expected firing sets.**
  (In-suite.) Every case in `tests/corpus/intensity/manifest.json` has a
  `failure_mode` key and an `expected_firing` key whose value is a list. Each
  case with a non-empty `expected_firing` has `failure_mode == 16`. The
  `failure_mode == 0` cases have an empty `expected_firing`. Measured
  2026-09-15: `implausible_metal`, `implausible_soft_tissue` and
  `degenerate_uniform` at 16 with `["intensity"]`; `clean_hu` at 0 with `[]`.
  *(closes Stage 30 criterion 5)*
- [ ] **AC25: `FAILURE_MODE_NAMES` is derived from the specification.**
  (In-suite.) `segfacet.synth.perturbation.FAILURE_MODE_NAMES ==
  dict(segfacet.failure_modes.failure_mode_names())`. Parsing
  `src/segfacet/synth/perturbation.py` with `ast` shows the module-level binding
  of `FAILURE_MODE_NAMES` is not a `Dict` literal.
  *(closes Stage 30 criterion 5)*
- [ ] **AC26: `MODE_RUNGS` is replaced by the specification.** (In-suite.) No
  module under `src/segfacet/`, parsed with `ast`, has a module-level assignment
  (`Assign` or `AnnAssign`) whose target is `MODE_RUNGS`, `ModeRung` or `RUNGS`.
  `hasattr(segfacet.traceability, "MODE_RUNGS") is False`.
  *(closes Stage 30 criterion 5)*
- [ ] **AC27: every `vision.md` §6 seed title resolves through
  `VISION_SEED_DISPOSITION`.** (In-suite.)
  `segfacet.failure_modes.vision_seed_conflicts() == ()`. This is the
  replacement roadmap v3.1's annotation names for criterion 5's "the eight seed
  names equal `vision.md` §6's list" (reading D3). Separately, the replay records
  how many of the live `vision_seed_titles()` values equal some
  `SPECIFICATION[*].name`, so the literal wording's status is on the record
  (measured 2026-09-15: 2 of 8, `Semantic mislabelling (wrong vertebra
  identification)` and `Overlapping segments`). That count is recorded, not
  pinned. *(closes Stage 30 criterion 5, under reading D3)*

### Criterion 6 — the sign-off

- [ ] **AC28: the module's sign-off record agrees with the resolved gate.**
  (In-suite.) The anchored `Signed off: YYYY-MM-DD -- …` line in
  `segfacet.failure_modes.__doc__`, the shape item 150's AC5 pins, carries a
  date equal to the ISO date in the Status cell of the `progress.md` gate row
  whose Gate cell contains `Stage 30 failure-mode specification sign-off`, as
  parsed by `.aide/scripts/aide.py`'s `human_gates()`. That row's kind is
  `approved`. *(closes Stage 30 criterion 6)*
- [ ] **AC29: the sign-off record's entry count matches the specification.**
  (In-suite.) The count the outcome sentence states (`sixteen entries` at
  writing), parsed from the number word or numeral immediately before
  `entries`, equals `len(SPECIFICATION)`. *(closes Stage 30 criterion 6)*

### Criterion 7 — the S-axis correction, re-verified

- [ ] **AC30: `build_clean_spine` stacks ascending labels caudally along +S.**
  (In-suite.) On the array and affine `build_clean_spine` returns, the world
  S coordinate of each label's voxel centroid, where the S axis is resolved from
  the affine through `segfacet.synth.axes.si_axis` and never hardcoded, is
  strictly decreasing in ascending label order. *(closes Stage 30 criterion 7)*
- [ ] **AC31: both committed corpora regenerate from the clean tree.** (Replay.)
  In the clone, `python -P -m segfacet.synth.corpus --out <scratch>/geo` and
  `python -P -m segfacet.synth.intensity --out <scratch>/int` regenerate both
  corpora. Each regenerated manifest is accepted by
  `assert_matches_committed_artifact` against its committed copy. Every
  regenerated `*.nii.gz` fixture is `cmp`-identical to the committed fixture of
  the same relative path, and the two fixture sets are equal as path sets. The
  per-file result is recorded. *(closes Stage 30 criterion 7)*
- [ ] **AC32: the synthetic reference artifact regenerates from the clean tree.**
  (Replay.) In the clone,
  `python -P -m segfacet.reference.artifact --out <scratch>/reference_default.json`
  produces a JSON that `assert_matches_committed_artifact` accepts against
  `src/segfacet/reference/reference_default.json`. Whether it is also
  byte-identical is recorded. *(closes Stage 30 criterion 7)*
- [ ] **AC33: the real-cohort reference artifact is unmoved by construction,
  and recorded as such.** (Replay.)
  `tests/test_128_reference_verse_v1_integrity.py` passes in the clone.
  `docs/corpus-s-axis-correction.md`'s `reference_verse_v1.json` row reads
  `unmoved` with its no-synthetic-input reason. The replay does not rebuild the
  artifact from the real cohort (reading D7). *(closes Stage 30 criterion 7,
  under reading D7)*
- [ ] **AC34: no expected firing set in the specification predates the
  correction.** (In-suite; skips cleanly, never fails, on a shallow clone or
  without `git`.) Resolve item 143's correction commit fresh by its subject
  `fix(143): correct the synthetic corpus's S-axis stacking` (`513f50b` at
  writing). Every commit in `git rev-list HEAD -- src/segfacet/failure_modes.py`
  is also in `git rev-list <correction>..HEAD -- src/segfacet/failure_modes.py`,
  and the second list is non-empty (measured 2026-09-15: 8 and 8). AC8's
  agreement on the regenerated corpus is the other half: every expected set is
  true of the corrected corpus. *(closes Stage 30 criterion 7)*

### Recording, environment, suite, check

- [ ] **AC35: the per-status and per-rung counts in `progress.md` match a fresh
  derivation.** (In-suite.) Stage 30's criterion-1 evidence note contains a
  clause of the exact shape
  `derived status counts over N modes: validated A, implemented B, specified C, proposed D`,
  and criterion 3's note contains
  `derived mode rung counts: synthetic-demonstrable A, needs-real-data B, structurally-unobservable C, none D; per-edge rung counts over E edges: synthetic-demonstrable F, needs-real-data G, structurally-unobservable H`.
  Criterion 1's note also contains
  `validated through a pipeline-detected case A, through a reconstructed record only B`.
  Every integer equals the value recomputed live from `SPECIFICATION`,
  `derive_status`, `derive_mode_rung` and the manifests' `detection` fields,
  and `N` equals `len(SPECIFICATION)`. Each note also names the commit SHA and
  the clone the counts were measured on. *(Dated claim: see Dependencies →
  Downstream.)*
- [ ] **AC36: every Stage 30 acceptance box is ticked with evidence or unticked
  with a reason.** (In-suite.) Parse `progress.md`'s Stage 30 section. Each of
  the seven boxes is either `[x]` and carries a non-empty `*(…)*` annotation or
  a dated correction trail, or `[ ]` and carries a non-empty reason, which is
  the tick-implies-evidence biconditional items 106/115/125/135 pinned. Each
  ticked box among criteria 1–6 ends in the single trailing `*(…)*` annotation
  `aide progress accept 30 --criterion N --evidence "…"` writes, and that note
  names the check it rests on: the AC numbers above and the replay's clone
  commit. The notes for criteria 2, 3 and 5 name the reading they
  used (reading D2 or D3: `mode 15`, `mode 16`, `vision_seed_conflicts`, clean
  controls against the empty set). A criterion the replay does not establish
  stays `[ ]` with an annotation giving the reason, as §1 allows ("say why in an
  annotation beside it").
- [ ] **AC37: criterion 7 carries this item's dated correction trail, and its
  original attestation line survives.** (In-suite.) Stage 30's seventh box has a
  trail line (`  - **YYYY-MM-DD** → …`) dated on or after 2026-09-15 that names
  item 151. The box line's text up to and including item 143's `*(…)*`
  annotation is still present verbatim. The trail comes from
  `aide progress amend 30 --criterion 7` if AC30–AC34 hold, or from
  `aide progress retract 30 --criterion 7` if any fails. If the trail is a
  `retracted: ` line, `docs/aide/insights.md` carries a `gap` entry whose
  provenance names `stage 30 criterion 7`.
- [ ] **AC38: the full suite is green in the clean clone.** (Replay.)
  `python -P -m pytest <clone>/tests -n auto`, run in the foreground and split
  into chunks if a single call would exceed the tool timeout, passes on a fresh
  clone of this item's final commit, with its own venv and the AC1 resolution
  proof. That clone is separate from the mutation clone, because it has to
  carry this item's own commits. Record pass/skip/fail counts, the commit,
  and the skip reasons of any environment-gated skips. A skip is never recorded
  as verification.
- [ ] **AC39: the criterion-7 re-verification insight is ticked with a
  pointer.** (In-suite.) The `insights.md` gap entry dated 2026-09-03 with
  provenance `item 143` that begins `Stage 30 acceptance criterion 7 was ticked
  by item 143's validator` is present verbatim and ticked, in
  `docs/aide/insights.md` or any `docs/aide/insights/archive-*.md` (CLAUDE.md's
  archive gotcha). It was ticked through `aide insights tick <n> --pointer …`
  with a pointer naming item 151, where `<n>` is resolved from
  `aide insights list --open` at the time and not taken from this spec.
- [ ] **AC40: the environment-gated conclusion rests on a checked mechanism.**
  (In-suite, and replayed.) In-suite: `inspect.signature(
  segfacet.synth.regression.intensity_pipeline_findings).parameters["enable_pyradiomics"].default
  is False`. Replay: record the output of `python .aide/scripts/aide.py env` and
  of `env --profile pyradiomics`, `--profile docker` and `--profile gpu`. The
  Environment-Gated Capability Verification table is left unchanged, with the
  reason recorded in Decisions: Stage 30 introduces no gated capability, and no
  measured firing set depends on one.
- [ ] **AC41: `aide check` reports no error and no warning outside the recorded
  baseline.** (Replay.) After this item's `progress.md` and `insights.md` edits,
  `python .aide/scripts/aide.py check` returns no error. Every warning falls in
  a baseline class, classified by the shape idiom of
  `tests/test_145_eight_hypothesised_modes.py::_classify_warning`. The warning
  multiset equals the baseline, except that a `stage 30 criterion 7 was
  retracted` warning is expected if and only if AC37 recorded a retraction.
  Baseline measured 2026-09-15 on this branch, engine 1.37.0: `OK (7 warning(s))`,
  which is 1 assumptions-block, 2 awaiting-a-decision (gates 1 and 2) and 4
  retracted-criterion (Stage 20 criteria 1, 3, 4, 5).

## Assumptions

- **A1: items 143–150 are all complete and human gate 5 is approved before this
  item starts** (both measured 2026-09-15). If either is not, the item halts and
  reports rather than validating a partial stage, the posture items 106, 115, 125
  and 135 took.
- **A2: roadmap v3.1's Stage 30 annotation is the authority on how the immutable
  acceptance text is read.** It landed through a reviewed PR (#74, merge
  `7e4bb5c`) and is mirrored in `progress.md`'s Stage 30 note. Readings D2–D7 in
  Decisions apply it and add nothing it does not say, except where Decisions
  flags a reading as this spec's own (D2 clean controls, D4 the rendering's
  columns, D5 empty tuple fields on any mode, D7 the real-cohort artifact). If
  a human disagrees with any of those four, the matching criterion stays
  unticked with that disagreement as its reason. No new gate is raised for them,
  because each is a record-keeping reading and not a decision the work cannot
  proceed without.
- **A3 (engine 1.37.0, re-checked 1.52.1, re-checked 1.59.0):** `aide progress accept <stage> --criterion N --evidence
  "<text>"` ticks one unticked box and appends ` *(<text>)*` to its line. It
  reports an already-ticked box as `already ticked, unchanged` and writes
  nothing. It commits `progress.md` unless `--no-commit` is given. AC36/AC37 rest
  on this.
- **A4 (engine 1.37.0, re-checked 1.52.1, re-checked 1.59.0):** `aide progress amend` appends
  `  - **YYYY-MM-DD** → <text>` under a ticked box and refuses an unticked one.
  `aide progress retract` unticks, appends a `retracted: ` trail line, and
  writes an `insights.md` `gap` entry. `aide check` then warns
  `stage 30 criterion 7 was retracted on …`. No verb records a reason beside an
  unticked box, so that one annotation is a hand edit, as §1 permits ("say why in
  an annotation beside it") and as Stage 29's third box did.
- **A5 (engine 1.37.0, re-checked 1.52.1, re-checked 1.59.0):** `aide check` at this branch's base reports
  `OK (7 warning(s))` in the classes AC41 lists. `aide insights tick <n>
  --pointer` ticks by the number `insights list` prints. `aide env --profile
  <name>` evaluates `aide.toml`'s `[validation]` expression and exits `0` iff
  it is satisfied.
- **A6: `python -P` keeps the working checkout off `sys.path`.** The clone's venv
  is Python 3.11 or later (item 095's environment migration), where `-P` stops
  the interpreter from prepending cwd. The replay prints `segfacet.__file__` and
  `tests.__file__` to prove resolution (AC1). If a hygiene hook or the runtime
  blocks a clone invocation shape, the replay records the shape used instead
  and the resolution proof, and never falls back to `PYTHONPATH` (CLAUDE.md
  Gotchas).
- **A7: every number in this spec is a starting point.** Values were measured
  2026-09-15 at `7e4bb5c` from the committed artifacts, plus one live probe
  (label 22's crop offset 17.507 mm, `mode8_force_overlap`'s pipeline and
  reconstructed firing). The item re-measures them. Where one has moved, the
  measured value wins and the divergence is recorded in Decisions.
- **A8: `aide check --queue 020` pin-versus-edit reports naming this item are
  inert.** This is the structural collision items 125 and 135 recorded: a
  stage-validation item pins what its stage's items produced, and every one of
  them is merged. AC41 covers `aide check`, not `aide check --queue`. A report of
  any other shape is a finding for Decisions.
- **A9: the working checkout's `tests/` needs no change beyond the new module.**
  Ticking Stage 30 boxes breaks no existing test: a sweep on 2026-09-15 found no
  test parsing Stage 30's acceptance boxes. A Stage 30 retraction would add a
  warning that `tests/test_114_documentation_corrections.py::test_ac8_no_new_aide_check_warning_beyond_pinned_baseline`'s
  pinned multiset does not carry, so that file is under **May change** for that
  case only.

## Implementation Steps

1. **Preconditions.** Confirm items 143–150 are complete in `progress.md` and
   gate 5 is approved (`aide gate list`). Record `aide check`'s baseline (AC41).
2. **Build the rig (AC1).** Clone into the scratchpad, bootstrap its venv, and
   print the module resolution proof. Record the clone path and `HEAD`.
3. **Clean-tree regeneration (AC2, AC7, AC31, AC32, AC33).** Run the six
   generators into scratch paths from the clone's venv. `cmp` and
   `assert_matches_committed_artifact` each output against the clone's committed
   copy. Run the integrity pin test. Record per file.
4. **Live measurements (AC8, AC11, AC14, AC16, AC27).** In the clone, drive every
   manifest case through the `synth.regression` harness. Record the measured
   sets, label 22's crop offset, the pipeline-versus-reconstructed firing on
   `mode8_force_overlap`, the analytic edge list and the literal seed-name
   equality count.
5. **Mutation replays (AC19, AC20, AC21)**, only after steps 3–4. Apply each
   mutation to the clone, run the named tests, record the failure text verbatim,
   restore, and confirm with `cmp`. Then delete the clone.
6. **Environment (AC40).** Run `aide env` and the three `--profile` checks.
   Record the output.
7. **Write `tests/test_151_stage30_validation.py`** (Testing Strategy).
8. **Counts.** Derive the per-status, per-rung, per-edge and validated-split
   counts fresh, in the exact AC35 shapes.
9. **Acceptance bookkeeping (AC36, AC37).** For each of criteria 1–6 the replay
   establishes, run `python .aide/scripts/aide.py progress accept 30 --criterion
   N --evidence "<one line: the checks, the reading if any, the clone commit;
   for 1 and 3 the AC35 count clauses>"`. For criterion 7, run `amend`, or
   `retract` if AC30–AC34 do not all hold. For a criterion not established, add
   the reason annotation by hand beside the unticked box.
10. **Insights (AC39).** Resolve the criterion-7 entry's number with `aide
    insights list --open` and tick it with a pointer to this item. Append every
    out-of-scope finding as a new one-line entry.
11. **Check (AC41).** Re-run `aide check` and compare it against the baseline.
    Record both. Run the working checkout's `tests/test_151_stage30_validation.py`.
12. **Suite (AC38).** Once every commit of this item has landed, clone the final
    commit afresh, bootstrap its venv, print the resolution proof, and run the
    full suite in the foreground. Record the counts, then delete the clone.

## Authorised paths

**May change:**

- `tests/test_151_stage30_validation.py` — this item's in-suite module.
- `docs/aide/progress.md` — Stage 30's seven acceptance boxes only: ticks via
  `aide progress accept`, criterion 7's trail via `amend`/`retract`, and a
  hand-written reason annotation beside any box left unticked. No deliverable
  bullet, status icon, summary row or Environment-Gated row is edited.
- `docs/aide/insights.md` — appended findings, a retraction's gap entry, and the
  one `aide insights tick` of the criterion-7 entry (AC39).
- `docs/aide/items/151-validate-stage30.md` — this spec's Decisions log.
- `tests/test_114_documentation_corrections.py` — only if AC37 records a
  retraction, to add that warning to AC8's pinned baseline (A9).

**Asserts against:**

- `src/segfacet/failure_modes.py` — `SPECIFICATION`, `CONDITIONS`, the
  vocabularies, `derive_status`, `derive_mode_rung`, `measured_firing`,
  `specification_to_dict`, `vision_seed_conflicts`, `failure_mode_names` and the
  sign-off docstring (AC3–AC6, AC8–AC30, AC34, AC35). It is also the clone-side
  mutation target of AC19, which is never changed in this item's diff.
- `src/segfacet/traceability.py` — `build_matrix` and the absent `MODE_RUNGS`
  binding (AC3, AC5, AC9, AC13, AC14, AC18, AC26).
- `src/segfacet/catalogue.py` — the feature catalogue generator (AC7).
- `src/segfacet/feature_docs.py` — `MODE_ANCHOR_PATHS` (AC5).
- `src/segfacet/heuristics/*.py` — every registered rule's `RuleModeDeclaration`
  (AC14, AC18, AC23), and the clone-side mutation target of AC20.
- `src/segfacet/synth/perturbation.py` — `FAILURE_MODE_NAMES` (AC25).
- `src/segfacet/synth/regression.py` — the measurement harness and
  `intensity_pipeline_findings`' signature (AC8, AC11, AC16, AC40).
- `src/segfacet/synth/clean_gt.py` — `build_clean_spine` (AC30).
- `src/segfacet/synth/axes.py` — `si_axis` (AC30).
- `src/segfacet/synth/corpus.py` — the geometric corpus generator (AC31).
- `src/segfacet/synth/intensity.py` — the intensity corpus generator (AC31).
- `src/segfacet/reference/artifact.py` — the default reference generator (AC32).
- `src/segfacet/reference/reference_default.json` — AC32's committed comparand.
- `src/segfacet/reference/reference_verse_v1.json` — AC33's integrity-pinned
  artifact, never rebuilt here.
- `src/segfacet/default_config.yaml` — the `mislabel` `max_offset_mm` AC11
  compares against.
- `docs/aide/failure_modes.generated.json` — AC2, AC4, AC13, AC18, and AC21's
  clone-side mutation target.
- `docs/aide/failure_modes.generated.md` — AC2, AC4, AC6.
- `docs/aide/traceability_matrix.generated.json` — AC2, AC3, AC5.
- `docs/aide/traceability_matrix.generated.md` — AC2, AC3, AC5.
- `docs/aide/feature_catalogue.generated.json` — AC7.
- `docs/aide/feature_catalogue.generated.md` — AC7.
- `tests/corpus/manifest.json` — AC8–AC11, AC16, AC31, AC35.
- `tests/corpus/fixtures/*.nii.gz` — AC8, AC11, AC16, AC31. Recomputed live, never
  modified.
- `tests/corpus/intensity/manifest.json` — AC8, AC24, AC31.
- `tests/corpus/intensity/fixtures/*.nii.gz` — AC8, AC31.
- `docs/corpus-s-axis-correction.md` — AC33 reads the `reference_verse_v1.json`
  row.
- `docs/aide/vision.md` — read live through `vision_seed_titles()` (AC27).
  Framework-gated.
- `docs/aide/roadmap.md` — Stage 30's acceptance text and v3.1 annotation, read
  for the readings. Framework-gated.
- `docs/aide/queue/queue-020.md` — the item-151 paragraph reconciled in
  Decisions. Read only.
- `docs/aide/items/150-maintainer-sign-off-of-the-specification.md` — the
  sign-off transcript AC28/AC29 cross-check. Read only.
- `.aide/scripts/aide.py` — `human_gates()` imported in-process (AC28), and the
  verbs AC36/AC37/AC39/AC41 run.
- `tests/test_144_failure_mode_specification.py` — run by AC19–AC21 in the
  clone. Read, never edited.
- `tests/test_145_eight_hypothesised_modes.py` — `_classify_warning` idiom reused
  by AC41. Read only.
- `tests/test_150_maintainer_sign_off.py` — run by AC21 in the clone. Its
  sign-off parse idiom is reused by AC28. Read only.
- `tests/test_128_reference_verse_v1_integrity.py` — run by AC33. Read only.
- `tests/committed_artifact_guard.py` — the in-suite module must classify clean
  under it: no byte-exact comparison against a committed artifact (see Testing
  Strategy). Read only.
- `aide.toml` — `[validation]` profile names (AC40). Framework-gated.

## Testing Strategy

New module `tests/test_151_stage30_validation.py`, in the shape of
`tests/test_135_stage29_validation.py`. It pins the half of this validation that
is mechanically checkable, so a later change cannot move it silently. The
replays belong to the Validation section and are recorded in Decisions, not
asserted in the suite. Every test is deterministic and environment-independent:
no network, no clone, no cohort.

**In-suite:** AC3, AC4, AC5, AC6, AC8, AC9, AC10, AC11, AC12, AC13, AC14, AC15,
AC16, AC17, AC18, AC22, AC23, AC24, AC25, AC26, AC27 (the conflicts half), AC28,
AC29, AC30, AC34, AC35, AC36, AC37, AC39, AC40 (the signature half).

**Replay-only, recorded in Decisions:** AC1, AC2, AC7, AC19, AC20, AC21, AC31,
AC32, AC33, AC38, AC40 (the profile half), AC41, plus AC8's per-case measured
sets and AC27's literal equality count.

Discipline the module must follow:

- **No byte-exact comparison against a committed artifact.** Byte identity is
  AC2/AC7/AC31's replay (`cmp` in the clone). Items 144, 149 and 150 already pin
  run-to-run determinism and committed-copy agreement under
  `tests/committed_artifact_guard.py`'s grounds. AC4 compares parsed JSON
  structures, never bytes. That keeps the module outside the guard's allowlist,
  which this item may not edit.
- **Measure once per module.** AC8, AC9, AC14 and AC18 need the measured firing
  set per case and one `build_matrix()`. Compute each once in a module-scoped
  fixture, the one-fixture-per-group discipline item 149 set for
  `test_138_traceability_matrix.py`, never a cache in production code.
- **Independent recomputation.** AC13 and AC18 re-derive rung and status in the
  test body from primary inputs (the registry declarations, the manifests, the
  measured sets) and compare against the production derivation. A test that only
  calls `derive_status` and compares it to itself is not evidence (§1 →
  `items.md`).
- **Parsed, not eyeballed.** AC35–AC37 parse `progress.md`'s Stage 30 section by
  its `## Stage 30 — ` header and its checkbox lines. AC28 imports
  `.aide/scripts/aide.py` in-process for `human_gates()`, the
  `test_150_maintainer_sign_off.py` idiom.
- **Git-reading tests skip cleanly.** AC34 skips, never fails and never passes,
  when the repository is shallow or `git` is unavailable (the `test_116` /
  `test_135` precedent).
- **Archive-aware.** AC39 searches `docs/aide/insights.md` and every
  `docs/aide/insights/archive-*.md` (CLAUDE.md Gotchas).

**Adversarial and edge cases:**

- AC35's parser must reject a count clause that is missing, a count off by one
  (checked by feeding the parser an in-memory altered note), and an `N` that
  disagrees with `len(SPECIFICATION)`.
- AC36's parser must fail on an in-memory Stage 30 section with a box ticked
  without an annotation, and on one left unticked without a reason.
- AC37 must fail on an in-memory variant whose criterion-7 original annotation
  was reworded, and on one with no trail line naming item 151.
- AC14 must fail on an in-memory matrix copy with one `analytic` attribution
  flipped to `corpus`.
- AC13's weakened-edge variant must change the derived rung (proving the
  derivation is live). A mode with no edges must derive `None` and render `""`
  in the matrix.
- AC18 must fail on an in-memory copy of a mode whose one agreeing case's
  expected set is emptied: `validated` must not be recomputed.
- AC9 must fail when a synthetic manifest case with a non-zero `failure_mode`
  not carried by the specification is injected in memory (the manifest loader is
  monkeypatched through the module object, the item-147 idiom).
- AC11 must fail if label 22's offset in a monkeypatched record is set to the
  threshold exactly (`>` not `>=`), so the claim is "above", as the rule's
  firing requires.
- Immutability: no test writes a committed file. Every variant is built in
  memory.

**Existing tests to reconcile.** This item changes no production behaviour and
no committed artifact, so no existing assertion should move. Swept 2026-09-15:
no test under `tests/` parses Stage 30's acceptance boxes, so accepting criteria
1–6 and amending 7 breaks nothing. The one conditional hit is
`tests/test_114_documentation_corrections.py::test_ac8_no_new_aide_check_warning_beyond_pinned_baseline`,
whose exact warning multiset would gain a `stage 30 criterion 7 was retracted`
entry if AC37 records a retraction. It is listed under **May change** for that
case only. `tests/test_145_eight_hypothesised_modes.py::test_ac24_…` and
`tests/test_146_ninth_mode_and_first_proposed.py::test_ac36_…` classify by
shape, and `retracted-criterion` is already a class, so they are safe either way.

## Validation

This item **is** the validation, and the validator must execute it, not just
re-run the suite. Record each of the following in Decisions as observed output,
not as a claim:

- the rig: clone path, `HEAD`, the bootstrap result, and the module resolution
  proof (AC1);
- per artifact, the `cmp` exit code for the four conformance artifacts, two runs
  each (AC2), and the catalogue's Markdown `cmp` plus its JSON tolerance result
  (AC7);
- per case, the measured firing set for all manifest cases, label 22's crop
  offset, `mode8_force_overlap`'s pipeline versus reconstructed firing, the
  analytic edge list, and the literal seed-name equality count (AC8, AC11, AC14,
  AC16, AC27);
- the three mutation replays: each mutation, the command, the verbatim failure
  text, the restore `cmp`, and the clone's deletion (AC19–AC21);
- both corpora's per-file regeneration results, the default reference's
  tolerance and byte result, and the integrity pin result (AC31–AC33);
- the commit ancestry counts (AC34);
- the full-suite counts and gated skip reasons (AC38);
- `aide env` and the three profile results (AC40);
- `aide check` before and after (AC41);
- per criterion, the exact `accept`/`amend`/`retract` command run and the
  evidence text written (AC36, AC37).

**Environment gating.** No criterion depends on a `[validation]` profile.
`pyradiomics`, `docker` and `gpu` are evaluated and recorded (AC40) but gate
nothing, because the intensity harness pins `enable_pyradiomics=False`. The real
VerSe19 cohort is not required (reading D7). The one external need is `git` plus
disk for one clone and a venv. On this machine the `aide` CLI runs as
`python3 .aide/scripts/aide.py`, since `python` is not on `PATH`.

**Honest downgrade.** A replay that cannot be performed is recorded as not
performed, naming the missing input. The criterion it would have closed stays
unticked with that reason, and Stage 30's acceptance stays open on that
criterion. Stage 30's rollup is unaffected, because acceptance boxes never gate a
stage's status. A skip-clean suite is never evidence that a replay ran.

## Dependencies

- **Item 143** — the S-axis correction and its moved/unmoved record (AC30–AC34).
  Merged.
- **Item 144** — the specification module, schema, derivations and rendering.
  Merged.
- **Item 145** — the hypothesised modes and per-edge rungs. Merged.
- **Item 146** — mode 16 (entered as the ninth mode), the intensity harness and
  intensity manifest fields. Merged.
- **Item 147** — the five partial sources collapsed onto the specification.
  Merged.
- **Item 148** — per-path attribution in the catalogue (AC7). Merged.
- **Item 149** — the matrix as conformance report (AC2, AC3, AC5, AC9, AC14).
  Merged.
- **Item 150** — the maintainer sign-off and the catalogue re-organisation this
  replay validates against (AC28, AC29). Merged. Human gate 5 approved
  2026-09-15, quoted with its reach intact: `Blocks: items 139, 140, 141, 142`.

**Downstream:** several in-suite pins are **dated claims** about the signed-off
catalogue. They are true now and are expected to change with the stages that
follow, the item-150 D3 precedent. The first item that makes one false must list
`tests/test_151_stage30_validation.py` under its **May change** and update the
pin:

- AC35's recorded counts change when Stage 32 (selected-mode refinement) moves
  a derived status or rung.
- AC27's `vision_seed_conflicts()` changes when Stage 31 D2 re-points or retires
  the seed-conformance check after the §6 re-issue.
- AC10, AC11 and AC16 name corpus case ids that Stage 31 D4 may rename.

Stage 31 (post-sign-off maintenance) is planned only after this item closes
Stage 30.

## Decisions & Trade-offs

### Reconciling queue-020's pre-sign-off wording (recorded at spec time, 2026-09-15)

Queue-020's item-151 paragraph predates item 150's review. Each mapping below
follows roadmap v3.1's Stage 30 annotation (merge `7e4bb5c`), the sign-off
transcript in `docs/aide/items/150-maintainer-sign-off-of-the-specification.md`
(section "Stage-30 maintainer sign-off"), and commits `3cb522f` / `ce0c6ec`. The
queue text and the roadmap's acceptance text are not edited.

**D1 — "ten entries / eight seed modes plus a ninth and a proposed tenth" →
sixteen modes plus one condition.** Every count in this spec is derived live from
`SPECIFICATION` / `CONDITIONS` and never hardcoded as 8, 9 or 10. The queue's
per-status and per-rung count requirement stands, and is recorded split
(AC35).

**D2 — "every corpus case across both committed corpora" includes the two clean
controls, which have no specification entry.** The specification defines no
mode 0. The matrix scores `clean_control` and `clean_hu` against the empty set
under `expected_source == "manifest-clean-control"` (item 149). This spec reads
criterion 2's "the specification's expected firing set" for a
`failure_mode == 0`, condition-less case as the empty set: the specification's
statement, by omission, that a clean control is expected to fire nothing. That
reading is this spec's own and not the annotation's, so the criterion-2 evidence
names it. The two cases item 150 added (`fuse_adjacent`, `remove_level_relabel`)
are covered because AC8 enumerates the manifests. `remove_level_relabel`'s empty
expected set ("not detected today") is compared exactly like any other.

**D3 — criterion readings taken verbatim from the roadmap v3.1 annotation.**
- Criterion 2: `mode6_crop_at_border` is the FOV-truncation condition's fixture
  (`failure_mode` 0, `condition` `fov_truncation`), still expecting
  `{border, mislabel}`. Its `mislabel` firing is the mode-less spline-offset
  detector, a recorded co-detection. It is no longer gate 3's "true co-detection
  of mode 6", because seed mode 6 is retired into the condition.
- Criterion 3: "mode 8's rung" is mode 15's (Overlapping segments).
- Criterion 5: "the ninth mode" is mode 16. "The eight seed names equal
  `vision.md` §6's list" is replaced by `vision_seed_conflicts() == ()` over
  `VISION_SEED_DISPOSITION`. The literal wording no longer holds by design (2 of
  8 titles equal a current `name`). AC27 records that count, so the tick visibly
  rests on the annotation's replacement and not on the words.
- Queue item 145's "mode 7's single-rank-descent cap" belongs to no Stage 30
  criterion. After the sign-off it lives in mode 9's `sequence` edge mechanism
  (the fixture generator's single-relabel cap) and is not asserted here.

**D4 — criterion 4's "separately labelled columns" for the specification
rendering.** `failure_modes.generated.md` is a per-mode bullet document, not a
table, and renders no rule read paths at all. Rule read paths are the matrix's.
This spec reads the clause as: the matrix renders the two columns separately
(AC5), and the specification rendering labels every anchor path as a Stage-18
metric anchor and never as a rule read (AC6). "Names the specification as their
primary source" is read, for the specification's own rendering, as its note
naming `src/segfacet/failure_modes.py` plus its content equalling the live
`specification_to_dict()` (AC4). For the matrix it is read literally, through the
`primary_source` field (AC3). This spec's own reading, named in the evidence.

**D5 — criterion 1's "every schema field" and empty tuple fields.** Several
modes carry an empty tuple field by design. The seven `proposed` modes (5, 7,
10–14) have empty `intended_rules` and `corpus_cases` (item 146's first
`proposed` entry, extended at the sign-off). Two `specified` modes have an empty
`corpus_cases`: mode 3 (*Split vertebra segment*), whose split fixture is not
yet authored, and mode 8 (*Semantic mislabelling*), whose swap case and ordering
detector item 150's sign-off moved to mode 9. Both still derive `implemented`
through their declaring rules. "Carries every field" is read as: every dataclass
field is present with a valid value, required strings are non-empty, and each
tuple field is a tuple of its element type, which may be empty on any mode. An
empty `corpus_cases` bounds the derived status below `validated` (AC18), not
below `implemented`. This spec's own reading.
- **2026-09-15** → Corrected after validation round 1. The earlier reading said
  the three tuple fields may be empty only on a `proposed` mode, and that the
  `proposed` modes' empty fields included `candidate_features`. The committed
  specification contradicts both. Modes 3 and 8 are authored `specified` with
  `corpus_cases=()` (`src/segfacet/failure_modes.py`, `_MODE_3` and `_MODE_8`),
  and every one of the sixteen modes, `proposed` included, carries a non-empty
  `candidate_features`. The new reading holds because it is exactly what the
  module enforces. `ModeSpec.__post_init__` checks each tuple field's type, its
  element type and duplicate `rule_id`/`case_id` values, and never its emptiness.
  Its only status `ValueError` rejects authoring `implemented` or `validated`.
  `derive_status` requires at least one corpus case for `validated` but none for
  `implemented`. So a narrower reading, that an empty `corpus_cases` keeps a mode
  at `specified`, would also be false: modes 3 and 8 derive `implemented`.

**D6 — the queue asks that `feature_catalogue.generated.md` also "names the
specification as its primary source".** It does not: its note names
`src/segfacet/feature_docs.py`, and Stage 30's criterion 4 names only
`failure_modes.generated.{md,json}` and the matrix. The catalogue's clean-tree
regeneration is replayed (AC7) because item 148's deliverable feeds it, but it
closes no criterion and its note is not asserted. The queue's item-148 wording
(`reference_delta` bookkeeping paths "no longer carry `failure_modes == (1, 2)`")
names pre-sign-off ids and is not replayed.

**D7 — criterion 7's "both reference artifacts were regenerated after the
correction", for the real-cohort artifact.** `reference_verse_v1.json` is built
from real VerSe19 data that neither `build_clean_spine` nor any synthetic corpus
feeds. Queue-020's item-143 paragraph states that such an artifact not moving
"is the expected result and is evidence, not an omission", and
`docs/corpus-s-axis-correction.md` records it `unmoved`. The replay does not
rebuild it: a rebuild would test item 129's and item 123's rebuild decisions, not
the S-axis correction, and it needs `SEGFACET_VERSE_COHORT`. AC33 therefore
establishes "unmoved by construction, integrity pin holding", and the
criterion-7 amendment names that reading. If a reviewer holds that "regenerated"
requires a rebuild, criterion 7 is retracted with that reason instead.

**D8 — criterion 7 is amended, not re-accepted.** The box was ticked by item
143's validator (`5a663d0`). `accept` would report it unchanged (A3). The
attestation is immutable (§1 → `progress.md`), so the replay's result goes into
a dated trail: `amend` when it holds, `retract` (which routes its own gap entry)
when it does not. The existing evidence sentence is not reworded.

**D9 — the queue's "flip any Environment-Gated row this stage affects".** No row
is affected. Stage 30 introduces no gated capability. The intensity harness pins
`enable_pyradiomics=False`, so mode 16's measured firing is identical with and
without PyRadiomics. No criterion reads the real cohort (D7). AC40 checks that
mechanism in-suite rather than asserting the conclusion.

### Other spec-time decisions

**D10 — no new human gate.** Every criterion is agent-establishable. The four
readings that are this spec's own (D2, D4, D5, D7) are record-keeping
interpretations named in each evidence note, and each has a stated fallback of
leaving the criterion unticked or retracting it. None is a decision the work
cannot proceed without (A2).

**D11 — the in-suite module makes no byte-exact comparison.** Clean-tree byte
identity is a replay property (a fresh clone, its own venv), which a test running
in the working checkout cannot establish. Items 144, 149 and 150 already pin
in-tree determinism under the committed-artifact guard. Repeating it here would
either add a guard allowlist entry this item may not make, or duplicate those
tests.

**D12 — observations noted while specifying, not acted on.** The first two are
captured in `insights.md` at spec time (item 151, 2026-09-15), so the validator
does not re-log them.
- The open `insights.md` gap entry dated 2026-09-04 (item 148) says the matrix's
  rule-attribution column renders mode 9's (now mode 16's) `intensity` edge
  `analytic`. The committed matrix at `7e4bb5c` renders
  `intensity (corpus), intensity_reference_delta (analytic)`, because item 149's
  Decision D2 re-derived attribution from the specification's corpus cases.
  Roadmap v3.1's Stage 31 D4 still lists the defect. AC14 measures the current
  state, and the entry itself is left for the queue boundary to triage.
- The sign-off transcript's entry-by-entry Mode 2 line attributes
  `fuse_adjacent`'s `coverage` co-detection to "10's detectors". After the
  2026-09-15 revision that detector serves mode 6, and both the mode-2
  `mechanism` and the `fuse_adjacent` reason already say mode 6. The transcript
  line is the only stale copy.
- `src/segfacet/failure_modes.py`'s docstring section "Becoming the record (item
  147)" still says "the one kept conformance check in that direction is that
  modes 1-8's `name` fields still equal §6's list". That is superseded by
  `vision_seed_conflicts()`, and roadmap v3.1's Stage 31 D2 owns it.

### Builder: no production change (2026-09-15)

**D13 — this item ships no `src/segfacet` change.** The "Authorised paths"
section lists every `src/segfacet/**` path under **Asserts against**, never
**May change**: this item's whole job, per the Description and Implementation
Steps, is to replay Stage 30's acceptance against the tree items 143–150
already merged, not to alter that tree. **May change** is limited to the new
in-suite test module, `progress.md`'s seven Stage 30 boxes, `insights.md`, this
spec's own Decisions log, and conditionally `tests/test_114_...py` (A9, only if
AC37 retracts). No Acceptance Criterion asks for a behavioural change; every AC
is phrased as a measurement, a comparison, or a mutation-and-restore replay
(AC19–AC21 mutate a *clone*, never the working checkout, and are reverted with
`cmp`). Builder therefore made no `src/segfacet` edit.

### Validator: replay record (2026-09-15, round 2)

**D14 — the clean-clone replay, recorded as observed output.** Round 1's three
test-authoring defects (AC9's adversarial fixture, AC29's parser, AC17's
tuple-emptiness clause) and the portability warning were confirmed fixed by
commit `6464b2e`: `tests/test_151_stage30_validation.py -q` gave `95 passed`
with only AC35/AC36/AC37/AC39 red (the expected bookkeeping-not-written state)
before this replay wrote that bookkeeping.

- **AC1, the rig.** Cloned `aide/151-validate-stage-30-failure-mode` into the
  scratchpad (`.../scratchpad/clone-mutation`); clone `HEAD` =
  `6464b2ea3a7d5b537adeeea210a6441ce0047cd8`, equal to the branch tip at
  replay start. Bootstrapped via
  `python <clone>/.aide/scripts/aide.py --repo <clone> env --bootstrap`
  (`aide env: bootstrap done (ok)`). Resolution proof, run with `-P` plus an
  explicit `sys.path` insert of the clone root (needed for `tests`, a
  namespace package with no `__init__.py`, since `-P` disables the implicit
  cwd prepend): `segfacet.__file__` =
  `<clone>/src/segfacet/__init__.py`; `tests.__path__` = `['<clone>/tests']`.
  Both resolve under the clone, never the working checkout.
- **AC2, the four conformance artifacts.** Two independent regenerations
  (`gen1`, `gen2`) of `failure_modes.generated.{json,md}` and
  `traceability_matrix.generated.{json,md}`: all 4 `cmp` exit 0 against the
  clone's committed copies, and `gen1` `cmp` exit 0 against `gen2` (8 `cmp`
  calls total, all silent/exit 0).
- **AC7, the feature catalogue.** `segfacet.catalogue` regenerated into
  scratch: `fc.md` `cmp` exit 0 against the committed copy; `fc.json` accepted
  by `assert_matches_committed_artifact` and additionally byte-identical
  (`filecmp.cmp(..., shallow=False)` True).
- **AC8, per-case measured firing sets (clone `6464b2e`).** 15 cases (11
  geometric + 4 intensity), every measured set equal to expected:
  `clean_control []=[]`, `mode1_displace ['mislabel']`,
  `mode2_fragment ['fragmentation']`, `mode3_inject_islands ['fragmentation']`,
  `mode4_relabel_swap ['mislabel']`, `mode5_remove_level ['coverage']`,
  `mode6_crop_at_border ['border','mislabel']`, `mode7_sequence_break
  ['sequence']`, `mode8_force_overlap ['overlap']`,
  `fuse_adjacent ['coverage','fragmentation']`, `remove_level_relabel []=[]`,
  `clean_hu []=[]`, `implausible_metal ['intensity']`,
  `implausible_soft_tissue ['intensity']`, `degenerate_uniform ['intensity']`.
  `matrix.conformance`: `unspecified_cases=()`, `disagreements=()`,
  `agree_count=15`.
- **AC11, label 22's crop offset.** On `mode6_crop_at_border`:
  `touches_anterior=True`, `is_terminal=False`,
  `offset_mm=17.507444781475748` (> `max_offset_mm=13.0`). On
  `clean_control`: `touches_anterior=False`.
- **AC14, the analytic edge list.** Measured from `matrix.modes[*].rule_attribution`:
  `[(1,'bounds'),(1,'reference_delta'),(2,'bounds'),(2,'reference_delta'),
  (3,'bounds'),(3,'reference_delta'),(4,'bounds'),(4,'reference_delta'),
  (8,'reference_delta'),(16,'intensity_reference_delta')]` — 10 edges,
  matching D12's recorded list exactly.
- **AC16, mode8_force_overlap.** `extract_feature_record(...).overlaps == []`;
  `pipeline_findings` rule ids `[]`; `reconstructed_findings` rule ids
  `['overlap']`; manifest `detection == "reconstructed_record"`.
- **AC27, the seed-title equality count.** `vision_seed_conflicts() == ()`.
  `vision_seed_titles()` (a `Dict[int, str]`) has 8 entries; exactly 2 equal a
  current `SPECIFICATION[*].name`: seed 4 → `Semantic mislabelling (wrong
  vertebra identification)`, seed 8 → `Overlapping segments` — matching the
  spec's measured 2/8.
- **AC19–AC21, the three mutation replays, in `clone-mutation`.**
  - AC19: `_MODE_2.status` set to `"validated"` in the clone's
    `src/segfacet/failure_modes.py`. `python -P -m pytest
    tests/test_144_failure_mode_specification.py -x -q` failed at import
    (`ModuleNotFoundError`-free; a `ValueError` from `ModeSpec.__post_init__`):
    `ValueError: ModeSpec 2: 'status' may only be authored as one of
    AUTHORED_STATUSES ('proposed', 'specified'); 'validated' is derived
    exclusively by derive_status(), never hand-authored past construction.`
    — names mode 2 (`ModeSpec 2`). Restored; `cmp` against the working
    checkout's copy exit 0.
  - AC20: `overlap.py`'s `RuleModeDeclaration(modes=(15,), ...)` changed to
    `modes=(5, 15)`.
    `test_144_failure_mode_specification.py::test_ac11_shipped_specification_has_no_conflicts`
    failed: `assert fm.specification_conflicts() == ()` →
    `"mode 5: authored status 'proposed' but derive_status() now returns
    'implemented' -- a proposed (listed, unimplemented) entry has acquired a
    declaring rule or a demonstrating corpus case, and wants re-authoring as
    'specified'."` — names mode 5. Restored; `cmp` exit 0.
  - AC21: mode 16's `status_derived` in the clone's committed
    `docs/aide/failure_modes.generated.json` changed from `validated` to
    `implemented`.
    `test_144_failure_mode_specification.py` and
    `test_150_maintainer_sign_off.py` run together: 2 failed, 169 passed.
    `test_ac19_committed_json_parses_to_a_fresh_build` failed on a structural
    JSON diff (no mode named in the truncated pytest summary — the modes list
    differs, printed without an index). `test_ac11_artifacts_are_byte_identical_to_a_fresh_regeneration`
    failed with `AssertionError: fresh structure does not match committed
    artifact ... at /modes/15/status_derived: fresh='validated'
    committed='implemented'` — names only the JSON pointer position
    (`/modes/15`, mode 16's list index), never "mode 16" by name. Per the
    AC21 text this is logged as a finding rather than a re-run: AC19 and
    AC20 already establish criterion 1's "naming the mode" clause with an
    explicit mode number in the failure text; AC21's own two committed-artifact
    comparison tests report by structural pointer instead. Restored; `cmp`
    exit 0. The mutation clone was deleted after AC19–AC21.
- **AC31, both corpora.** `segfacet.synth.corpus` and `segfacet.synth.intensity`
  regenerated into scratch. Both manifests accepted by
  `assert_matches_committed_artifact` and additionally byte-identical. All 12
  geometric + 5 intensity `*.nii.gz` fixtures byte-identical (`filecmp.cmp`,
  `shallow=False`); the two fixture path sets equal.
- **AC32, the default reference artifact.** `segfacet.reference.artifact`
  regenerated; accepted by `assert_matches_committed_artifact` and additionally
  byte-identical against `src/segfacet/reference/reference_default.json`.
- **AC33, the real-cohort artifact.**
  `tests/test_128_reference_verse_v1_integrity.py` passed (2 passed) in the
  clone. `docs/corpus-s-axis-correction.md`'s `reference_verse_v1.json` row
  reads `unmoved`, reason "no synthetic input feeds this artifact". Not
  rebuilt (reading D7).
- **AC34, commit ancestry.** Correction commit resolved fresh by subject
  `fix(143): correct the synthetic corpus's S-axis stacking` →
  `513f50b2edc8b6a083f1910225c842f446e65f7e`, matching the spec's `513f50b` at
  writing. `git rev-list HEAD -- src/segfacet/failure_modes.py` = 8 commits;
  `git rev-list 513f50b..HEAD -- src/segfacet/failure_modes.py` = the same 8
  commits — every commit touching the module postdates the correction.
- **AC40, environment.** `aide env`: `OK (venv present, import succeeds)`.
  `aide env --profile pyradiomics`: NOT satisfied (`ModuleNotFoundError: No
  module named 'radiomics'`). `--profile docker`: NOT satisfied. `--profile
  gpu`: NOT satisfied (`ModuleNotFoundError: No module named 'cupy'`). None
  gates any criterion (D9): the intensity harness pins
  `enable_pyradiomics=False`, and AC8's measured firing sets confirm mode 16
  fires identically without it.
- **AC35–AC37, AC39 bookkeeping.** `progress accept 30 --criterion N` run for
  N=1..6 (each `accepted`); `progress amend 30 --criterion 7` run once (AC30–
  AC34 all held, so amended rather than retracted). `insights list --open`
  resolved the criterion-7 entry to number 29 at replay time; ticked via
  `insights tick 29 --pointer "item 151: ..."`. Re-running
  `tests/test_151_stage30_validation.py -q` after the bookkeeping:
  `101 passed` (was `95 passed, 6 failed` before).
- **AC41, `aide check`.** Baseline (before this item's edits, at commit
  `6464b2e`): `OK (7 warning(s))` — 1 assumptions-block, 2 awaiting-a-decision
  (gates 1, 2), 4 retracted-criterion (Stage 20 criteria 1, 3, 4, 5). After
  this item's `progress.md`/`insights.md` edits (criterion 7 amended, not
  retracted): `OK (7 warning(s))`, same multiset — no `stage 30 criterion 7
  was retracted` warning, as expected since AC30–AC34 held.
- **AC38, the full suite on a fresh clone of the final commit.** Performed
  after every commit of this item landed (final commit `c839974`), on a
  separate clone from the mutation clone: `python -P -m pytest <clone>/tests
  -n auto -q` (module resolution proof as in AC1) → `7156 passed, 66 skipped,
  0 failed` in ~227s. All 66 skips are environment-gated (docker, CuPy/GPU,
  PyRadiomics, real VerSe19 cohort not mounted) or clone-relative (a queue-018
  base ref unavailable in a shallow single-branch clone; a pre-098 pinned
  shape absent) — none is a failure. A first background run of the same
  command was interrupted by a monitor-tooling wake-up loss (not a test
  failure) and was independently repeated end to end, reproducing the same
  `7156 passed, 66 skipped, 0 failed`. Separately, the working checkout's own
  full suite (`aide.toml`'s `test_command`, `python -m pytest -n auto -q`,
  run from the repo root with no path argument) gives `7946 passed, 66
  skipped, 0 failed` in ~214s — the ~790-test difference from AC38's number is
  `.aide/scripts/tests/` (the aide-loop framework's own stdlib test suite),
  which the bare root invocation additionally collects and AC38's
  `<clone>/tests`-scoped invocation does not; both counts are internally
  consistent with `--collect-only` (8012 total in the working checkout, no
  path restriction) and both runs are green.
