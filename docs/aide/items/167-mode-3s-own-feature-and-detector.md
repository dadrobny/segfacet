<!-- aide-template: item 2 -->
# Item 167 — Mode 3's own feature and detector

> **Created:** 2026-09-20 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 32 — Selected-Mode Refinement: one failure mode fully specified end to end
> **Queue:** [`../queue/queue-022.md`](../queue/queue-022.md) · Item 167
> **Objectives:** G2, G7, G8
> **Suggested branch:** `aide/167-mode-3-s-own-feature`

---

## Description

Mode 3 (*split vertebra segment*) is the **D2** mode of roadmap Stage 32. Item 166
gave it a `split` operator and one committed geometric corpus case; what it did
**not** give it is a detector of its own. Measured on this tree (2026-09-20,
`.venv/bin/python`):

- `segfacet.traceability.bar_conditions(3)` returns `(True, False, False, False, False)`
  — condition 1 (entry completeness) met, conditions 2–5 unmet.
- `SPECIFICATION[3].corpus_cases[0]` (`split`) measures `("fragmentation",)`, which
  is `fragmentation`'s **`components`** detector — mode 1's — co-detecting on the
  *receiving* label 23, not mode 3's own signal.
- `SPECIFICATION[3].intended_rules` names only `bounds` and `reference_delta`, both
  at `needs-real-data`, and the roadmap's bar condition 4 excludes exactly those two
  as generic volume proxies (`traceability.PROXY_RULE_IDS`).

This item gives mode 3 a feature and a detector, and takes it to the bar.

**The signal, chosen by measurement.** The queue lists three `hypothesised`
candidates (neighbour-label contact area, leave-one-out spline shape change, metric
change under a merge candidate). Neighbour-label contact area was measured first
because it is the cheapest, and the measurement disqualified the *naive* form and
pointed at the right one:

- **Bare inter-label contact area** does **not** separate mode 3. Measured over all
  twelve committed geometric cases, only two carry any inter-label face contact at
  all: `split` (labels 22↔23, **750.0 mm²**) and `force_overlap` (mode 15, labels
  20↔21, **725.0 mm²**). A threshold on that scalar would sit 25 mm² away from a
  different mode's case.
- **Contact restricted to a label's non-largest connected component** separates it
  exactly. On `force_overlap` both contacting components are each label's *largest*;
  on `split` the contact is carried by label 23's **second** component — the slab
  donated by label 22. Measured over **all sixteen** committed corpus cases
  (both manifests, every label): the value is `750.0` mm² for exactly one
  (case `split`, label 23, contacting label 22) and **`0.0` for every other label of
  every other case**, including `fuse_adjacent` (mode 2, mode 3's converse, whose
  label 22 *does* carry an 18 750-voxel detached component — contacting nothing),
  `fragment` (mode 1, detached own-label pieces), `inject_islands` (mode 4, a
  27-voxel island) and the clean controls.

That is mode 3's definition read off the label map: *a substantial part of one
vertebra is carried by a neighbour's label*, and the part shows up as a detached
piece of the neighbour pressed against the donor. It separates mode 3 from its
three near neighbours by construction — mode 2 (detached but not contacting),
mode 1 (own-label, and the missing part is background), mode 4 (own-label islands,
and far below the area threshold).

**What is built.** Two new leaf fields on the existing per-label `components` block
(`segfacet.features.components.ComponentsInfo`, which already receives the whole
label map and its own connected-component labelling, so nothing new is computed
twice), one new **detector** on the existing `fragmentation` rule under the
first-class id `neighbour_contact` (item 164), one new `IntendedRule` edge on mode 3
naming that detector, and the regenerated artifacts. **No new rule module, no new
operator, no new fixture, no corpus regeneration**: the committed manifest's
`expected_rule_ids`, `expected_labels` and `expected_verdict` for the `split` case
are all unchanged by this item (see A3 and AC8).

**Where this leaves mode 3 against the roadmap's bar.** Expected after this item,
and asserted by AC11 rather than claimed here:

| Condition | Before | After | Why |
|---|---|---|---|
| 1 — entry complete | met | met | unchanged (item 166 filled `corpus_cases`) |
| 2 — a fixture expresses it via one of its own rules | unmet | **met** | `fragmentation` becomes one of mode 3's own `intended_rules`, and `split`'s expected set names it and agrees |
| 3 — every signal path the deciding detector reads is extracted and catalogued | unmet | **met** | the new path enters `FEATURE_DOCS` and the generated catalogue with `observed.corpus.covered is True` |
| 4 — a non-proxy detector serves this mode alone | unmet | **met** | `modes_for_detector("fragmentation", "neighbour_contact") == (3,)`; `fragmentation` is not in `PROXY_RULE_IDS` |
| 5 — status derives `validated` | unmet (`implemented`) | **met** | `derive_status(SPECIFICATION[3])` → `"validated"` |

Condition 6 (maintainer sign-off) is **item 168's** and is never computed here.

**Not in scope.** No new rule id, no new perturbation operator, no new corpus case
or fixture, no change to any existing threshold, no change to any other mode's
entry, nothing touching the intensity corpus's content, no sign-off (item 168's),
and **no stage attestation** — item 169 attests Stage 32 and Stage 20 from a clean
clone with its own venv, after item 163's tick from the working checkout was
retracted on 2026-09-20.

## Acceptance Criteria

- [ ] **AC1: the feature measures the split.** For the committed fixture
      `tests/corpus/fixtures/split_seg.nii.gz`,
      `segfacet.features.components.compute_components(img, label=23, config=bundled_default_config()).stray_contact_area_mm2`
      equals a face-contact area recomputed independently in the test from the
      fixture's own array and `img.header.get_zooms()` — the maximum, over every
      connected component of label 23 **other than its largest**, of that
      component's 6-neighbour face-contact area with any single other non-zero
      label. (Measured 2026-09-20: `750.0` mm². The test compares against its own
      recomputation, not against that literal.)

- [ ] **AC2: the feature names the label that claimed the part.** For the same
      fixture and label, `stray_contact_label` equals the other label id carrying
      that maximal interface, recomputed the same way (measured: `22`); and for a
      label whose `stray_contact_area_mm2` is `0.0` it is `0` — the background
      sentinel, so the field is always numeric.

- [ ] **AC3: the feature is silent everywhere else in both committed corpora.**
      Sweeping every case of `segfacet.synth.corpus.load_manifest()` and
      `segfacet.synth.intensity.load_intensity_manifest()` and every non-zero label
      of each fixture, the set of `(corpus, case_id, label)` triples with
      `stray_contact_area_mm2 > 0.0` equals exactly
      `{("geometric", "split", 23)}` — recomputed from the committed fixtures, not
      from any authored list.

- [ ] **AC4: the detector is declared with a first-class id.**
      `segfacet.heuristics.fragmentation.FragmentationRule.mode_declaration.detectors`
      contains exactly one `RuleDetector` with `detector_id == "neighbour_contact"`,
      and its `signal_paths` equals
      `("per_label.{label}.components.stray_contact_area_mm2",)`.

- [ ] **AC5: the deciding detector serves mode 3 and no other mode.**
      `segfacet.failure_modes.modes_for_detector("fragmentation", "neighbour_contact")`
      equals `(3,)`, recomputed from `SPECIFICATION`.

- [ ] **AC6: the detector fires on mode 3's corpus case.** The findings
      `segfacet.synth.regression.pipeline_findings` produces for the committed
      `split` manifest case contain exactly one finding with
      `(rule_id, detector_id) == ("fragmentation", "neighbour_contact")`, and its
      `label` is `23`.

- [ ] **AC7: the detector fires on no other corpus case.** Over every case of both
      committed manifests, driven through the detection path each case's manifest
      entry names (as `segfacet.failure_modes.measured_firing` dispatches it), the
      set of `(corpus, case_id)` pairs producing any finding with
      `detector_id == "neighbour_contact"` from rule `fragmentation` equals
      `{("geometric", "split")}`.

- [ ] **AC8: no committed case's expected firing moved.**
      `SPECIFICATION[3].corpus_cases` still holds exactly one case, `split`, whose
      `expected_firing` is `("fragmentation",)` and equals
      `set(segfacet.failure_modes.measured_firing(case))` recomputed live — the new
      detector belongs to a rule the case already fired, so the rule-id-granular
      ratchet set is unchanged (A3).

- [ ] **AC9: the deciding detector's signal path is extracted and catalogued.**
      `segfacet.catalogue.build_catalogue(strict=True)` carries an entry whose
      `path` is `per_label.{label}.components.stray_contact_area_mm2` and whose
      `observed.corpus.covered` is `True`.

- [ ] **AC10: mode 3 owns the edge.** `SPECIFICATION[3].intended_rules` contains
      exactly one edge with `rule_id == "fragmentation"`, and that edge's
      `detector_ids` equals `("neighbour_contact",)` and its `evidence_rung` equals
      `"synthetic-demonstrable"`.

- [ ] **AC11: mode 3 stands at the fully-specified bar's conditions 1–5.**
      `tuple(c.met for c in segfacet.traceability.bar_conditions(3))` equals
      `(True, True, True, True, True)`, and condition 4's `subjects` equals
      `("fragmentation/neighbour_contact",)`. Closes **no** stage criterion:
      condition 6 is item 168's maintainer sign-off, and Stage 32's and Stage 20's
      acceptance are attested by **item 169**, from a clean clone with its own venv.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Each defensible
default taken while specifying the queued one-liner is recorded here for audit at
the queue boundary. Every measurement below was **run on this tree** on 2026-09-20
with `.venv/bin/python`; each names what was measured.

- **A1 (measured 2026-09-20):** the signal is **inter-label face-contact area
  restricted to a label's non-largest connected components**, not bare
  inter-label contact area. Measured over all twelve committed geometric cases,
  bare pairwise contact is non-zero on exactly two: `split` (22↔23, 750.0 mm², 750
  faces) and `force_overlap` (mode 15, 20↔21, 725.0 mm², 725 faces) — 25 mm² apart,
  so no threshold on the bare scalar separates mode 3 from mode 15. Restricting to
  non-largest components moves `force_overlap` to `0.0` (both its contacting
  components are their labels' largest) and leaves `split` at `750.0`. The other
  two candidate paths (`spline_leave_one_out_shape_change`,
  `metric_change_under_merge_candidate`) were **not** built: the first measured
  candidate separates the corpus completely, and under `prototype` posture the
  ladder stops there. Both remain in `candidate_features` as `hypothesised`.

- **A2 (measured 2026-09-20):** the detector is a **third detector on the existing
  `fragmentation` rule**, not a new rule module. Three reasons, in order of weight.
  (i) Item 164 made the *detector* the unit of mode attribution precisely so a rule
  may serve several modes; `bar_conditions`' condition 4 reads
  `modes_for_detector(rule_id, detector_id)` and excludes only
  `PROXY_RULE_IDS == ("bounds", "reference_delta")`, so `fragmentation` qualifies.
  (ii) The signal is a property of the label's connected components, which is the
  block `fragmentation` already owns and already reads. (iii) Cost: a new rule id
  would move `len(iter_rules()) == 10` (pinned twice in
  `tests/test_136_rule_mode_declarations.py`), the rule-id enumerations in fourteen
  test modules, the `split` case's `expected_rule_ids` in the committed manifest
  (forcing a corpus regeneration), and the per-rule exercise report — for no gain
  this item's acceptance criteria can measure. **The cost of the choice is that
  bar condition 2 is rule-id-granular and cannot see which detector fired**; AC6
  and AC7 close that at the detector level within this item, and the checker's
  granularity gap is captured in `docs/aide/insights.md` rather than fixed here.

- **A3 (measured 2026-09-20):** **no corpus case's `expected_firing` moves, and the
  committed corpus is not regenerated.** `failure_modes.measured_firing` returns the
  set of `rule_id`s (not detector ids) a case's findings carry; the `split` case
  already fires `fragmentation` through the `components` detector, so adding a
  second `fragmentation` detector that also fires on it leaves the set at
  `{"fragmentation"}`. The new detector fires on no other case (A1's sweep), so no
  other case's set moves either. The manifest's `expected_labels` for `split` stays
  `{23}` (item 166's A4: `offending_labels_match` is an exact equality, and the new
  finding is on label 23), and `expected_verdict` stays `flagged-for-review`.
  **How this was determined: by measuring the feature over every label of every case
  of both committed manifests, not by reasoning about which cases "look like"
  splits.** The build re-runs that sweep as AC3/AC7; a case that measures otherwise
  is a contradiction with this spec and comes back to `spec-author` as a dated
  correction, never reconciled by editing the ratchet.

- **A4 (measured 2026-09-20):** the threshold is a **code-side default**,
  `DEFAULT_NEIGHBOUR_CONTACT_AREA_MM2 = 100.0` mm², fired on strictly `>` (item
  027's inclusive convention, which `fragmentation` already follows), and is
  documented in `src/segfacet/default_config.yaml` as a **comment only** — the house
  pattern items 048 and 090 used for the `bounds`/`fragmentation` source switches,
  because a new key under `rules.fragmentation.params` changes the parsed config
  dict and hence `config_hash` in every report. **Margins, measured over both
  committed corpora:** the only firing value is `750.0` mm² (**+650.0** above the
  threshold, 7.5×) and every non-firing label measures exactly `0.0`
  (**−100.0** below it). There is no fixture value anywhere near the threshold —
  deliberately, after item 166 had to record a zero-margin threshold
  (`extent_z_mm == 15.0` against `DEFAULT_BOUNDS["lumbar"]["min_extent_z_mm"] ==
  15.0`) only once the build had happened. 100.0 mm² also carries the physical
  reading the bare `> 0` form lacks: at 1 mm isotropic it is 100 voxel faces, far
  above an incidental few-voxel touch and far above the total surface of mode 4's
  27-voxel island. Calibrated on the synthetic corpus only; roadmap Stage 21
  re-calibrates thresholds on real GT.

- **A5 (measured 2026-09-20):** the two new fields are added to the components
  block's JSON schema (`src/segfacet/report_schema_v0.json`) under `properties`
  but **not** under `required`. The block declares
  `"additionalProperties": false`, so `properties` is mandatory — a fresh report
  would fail `jsonschema.validate` without it. `required` is deliberately left
  alone: nine test modules hand-build a `components` instance
  (`tests/test_061_image_features_fusion.py`, `tests/test_081_reference_morphology.py`,
  `tests/test_090_reference_derived_defaults.py`, `tests/report_format_fixture.py`
  and others), and the detector reads the path through `.get(..., 0.0)` so a record
  predating the field is silent rather than raising. Making it required would buy a
  stricter schema and cost nine edits this item does not need.

- **A6 (measured 2026-09-20, engine 1.59.2):** this item must **amend Stage 30's
  attestation in `progress.md`**. `tests/test_151_stage30_validation.py`'s three
  AC35 tests parse Stage 30's evidence notes and compare them against a **live**
  derivation: `derived status counts over 16 modes: validated 6, implemented 3,
  specified 0, proposed 7`, `validated through a pipeline-detected case 5, through a
  reconstructed record only 1`, and `derived mode rung counts:
  synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7;
  per-edge rung counts over 17 edges: synthetic-demonstrable 5, needs-real-data 11,
  structurally-unobservable 1` — all four clauses verified live today. Mode 3 moving
  to `validated`, its derived rung moving to `synthetic-demonstrable`, and the new
  `synthetic-demonstrable` edge make every one of them false. `progress.md` is an
  always-authorised path and the amendment is made with the CLI
  (`aide progress amend 30 --criterion N --evidence "…"`), which **appends** a dated
  correction under the ticked box; `test_151` reads the section with `re.search`,
  which finds the *first* clause, so its three consumers are reconciled to read the
  **last** match — the current attestation rather than the superseded one. That is a
  narrowing, not a weakening: the test still asserts the recorded numbers equal the
  live derivation.

- **A7 (measured 2026-09-20):** this item **does not** add a second corpus case for
  mode 3, so the divergence recorded in `docs/aide/insights.md` (item 165,
  2026-09-20) — `bar_conditions`' condition 2 being implemented **universally**
  (`all(case_agrees(c) …)` plus an intersection requirement) where the roadmap's
  prose is **existential** — still does not bite: mode 3 keeps exactly one corpus
  case (`split`), and for a single-case mode the two readings coincide. AC8 pins the
  case count at one, so a later item that adds a second case meets the divergence
  deliberately rather than by accident.

- **A8 (engine 1.59.2):** `aide scope` proves this item's diff against the
  **Authorised paths** list below; a path listed there and left unchanged is not a
  scope violation, so the conditional reconciliations named below are declared
  whether or not the suite run turns out to need them.

## Implementation Steps

1. **Extend `ComponentsInfo` in `src/segfacet/features/components.py`** with two new
   fields, **appended after** `stray_volume_fraction` so the pre-098 field order
   `tests/test_098_stray_components.py::test_ac1_existing_five_fields_still_present_and_ordered_first`
   pins is untouched:
   `stray_contact_area_mm2: float` and `stray_contact_label: int`. Document both in
   the class docstring's `Attributes` block, in the house style already used there.

2. **Compute them inside the existing `compute_components` body**, reusing what is
   already in hand — `data` (the full label map, already read), `mask`, the
   `backend.ndimage.label` result `labelled`, the descending `counts` ordering and
   the voxel spacings already resolved for `component_volumes_mm3`. No second
   labelling pass, no new module, no new dependency. For every component **other
   than the largest**, compute its 6-neighbour face contact with each other non-zero
   label as `face_count × the per-axis face area`, and keep the maximum over
   (component, other label); `stray_contact_area_mm2` is that maximum and
   `stray_contact_label` the other label at it. A single-component label short-
   circuits to `(0.0, 0)`. Face adjacency must use the same 6-connectivity the
   module already documents as `CONNECTIVITY`, and the per-axis face area must come
   from the header zooms — never a hardcoded axis or an assumed isotropic voxel.

3. **Serialise both** in `segfacet.feature_report.components_to_dict`, in field
   order, and name them in that function's docstring beside the item-098 four.

4. **Add both to the `components` block of `src/segfacet/report_schema_v0.json`** —
   `stray_contact_area_mm2` as `{"type": "number", "minimum": 0}` and
   `stray_contact_label` as `{"type": "integer", "minimum": 0}` — under
   `properties` only, **not** under `required` (A5). The block's
   `"additionalProperties": false` makes this step load-bearing: without it every
   freshly generated report fails schema validation.

5. **Add a `FEATURE_DOCS` entry for each path** in `src/segfacet/feature_docs.py`
   (`build_catalogue(strict=True)` raises `FeatureDocMissing` for a realised leaf
   path with no entry): `measures`, `computation`, `units` (`"mm^2"` / `""`) and
   `scale_sensitivity` (`"scales with spacing"` / `"identifier"`). Do **not** touch
   `MODE_ANCHOR_PATHS` — that map is item 099's per-mode *eval metric* anchor, and
   mode 3 gains no per-mode metric here.

6. **Add the detector to `src/segfacet/heuristics/fragmentation.py`.** Reuse the
   module's existing machinery rather than adding a parallel path:
   - a module-level `DEFAULT_NEIGHBOUR_CONTACT_AREA_MM2: float = 100.0` beside the
     two existing default constants, and a `_NEIGHBOUR_CONTACT_TAG` beside
     `_FRAGMENTATION_TAG` / `_ISLAND_TAG`;
   - one `ConsumedPath(path="per_label.{label}.components.stray_contact_area_mm2",
     role="signal")` and one
     `ConsumedPath(path="per_label.{label}.components.stray_contact_label",
     role="bookkeeping", reason=...)` in `consumed_paths`;
   - one `RuleDetector(detector_id="neighbour_contact",
     description=_NEIGHBOUR_CONTACT_TAG,
     signal_paths=("per_label.{label}.components.stray_contact_area_mm2",))` —
     and **only** that path, so item 148's per-path narrowing attributes the new
     path to mode 3 alone and leaves the existing five components paths on modes
     1 and 4. `RuleModeDeclaration.__post_init__` already enforces that every
     `signal_paths` member is a `signal`-role `ConsumedPath` of the same
     declaration, and that the union across detectors equals the full signal set;
   - `modes=(1, 3, 4)` on the declaration, with its `evidence` tuple extended to
     name the `split` manifest case as mode 3's designation;
   - the check itself in `evaluate`, appended **after** the fragmentation and
     island findings so within-label output order stays deterministic: read
     `components.get("stray_contact_area_mm2", 0.0)` (absence-tolerant, per A5),
     fire when it is strictly greater than
     `config.rule_param(self.rule_id, "neighbour_contact_area_mm2_threshold",
     default=DEFAULT_NEIGHBOUR_CONTACT_AREA_MM2)`, and emit one `Finding` carrying
     `detector_id="neighbour_contact"`, the existing shared
     `rules.fragmentation.params.severity`, the offending label, and a reason
     naming the contact area, the threshold and the label that claimed the part
     (from `stray_contact_label`). Add **no** new config key and no new severity
     parameter.

7. **Document the threshold in `src/segfacet/default_config.yaml` as a comment
   only**, in the block that already documents the source switch the same way, with
   the one-line reason (config-hash stability) the surrounding comments give.

8. **Author mode 3's edge and correct its prose** in `src/segfacet/failure_modes.py`:
   - append `IntendedRule(rule_id="fragmentation",
     detector_ids=("neighbour_contact",), evidence_rung="synthetic-demonstrable")`
     to `SPECIFICATION[3].intended_rules`;
   - replace the `CandidateFeature(path="neighbour_label_contact_area_mm2",
     role="hypothesised")` placeholder with the real record path
     `per_label.{label}.components.stray_contact_area_mm2`, still `hypothesised`
     (the `stage18-metric-anchor` role would require a `MODE_ANCHOR_PATHS[3]` entry
     and mode 3 has no per-mode metric — step 5);
   - rewrite `SPECIFICATION[3].mechanism`, whose first clause currently reads
     "*No detector of its own (item 167's)*", to state the detector, the feature it
     reads, the threshold and its measured margins, and that the `fragmentation`
     firing on the receiving label is now **two** findings — mode 1's `components`
     co-detection and mode 3's own `neighbour_contact`;
   - extend the `split` corpus case's `reason` with the same distinction, keeping
     its `expected_firing` at `("fragmentation",)` (A3) and the original
     2026-09-20 measurement sentence intact.

9. **Amend Stage 30's attestation** (A6) with the CLI, never by hand:
   `python .aide/scripts/aide.py progress amend 30 --criterion 1 --evidence "…"`
   and `… --criterion 3 --evidence "…"`, each carrying the re-measured clause in the
   exact wording `tests/test_151_stage30_validation.py`'s regexes parse
   (`derived status counts over 16 modes: validated …`,
   `validated through a pipeline-detected case …`,
   `derived mode rung counts: … per-edge rung counts over … edges: …`). Re-measure
   the numbers; do not transcribe the predictions in A6.

10. **Regenerate every derived artifact** through its own entry point, none of them
    hand-edited: `docs/aide/feature_catalogue.generated.{json,md}` (two new leaf
    paths, and the observed-verdict summary moves),
    `docs/aide/failure_modes.generated.{json,md}` (mode 3's new edge, rung and
    derived status), `docs/aide/traceability_matrix.generated.{json,md}` (the new
    detector, edge and rung), and `docs/aide/golden_evidence.generated.json` (the
    `split` case gains a finding).

11. **Reconcile the tests named under "existing tests to reconcile"**, then **run
    the full suite** and reconcile whatever else it names. A file the suite names
    that is not declared under **Authorised paths** is a dated correction to this
    spec, not a silent edit.

## Authorised paths

**May change:**

- `src/segfacet/features/components.py` — the two new `ComponentsInfo` fields and their computation (steps 1–2)
- `src/segfacet/feature_report.py` — `components_to_dict` serialises them (step 3)
- `src/segfacet/report_schema_v0.json` — the components block's `additionalProperties: false` rejects the new keys without this (step 4)
- `src/segfacet/feature_docs.py` — a `FEATURE_DOCS` entry per new leaf path; `build_catalogue(strict=True)` raises without them (step 5)
- `src/segfacet/heuristics/fragmentation.py` — the `neighbour_contact` detector, its consumed paths, threshold constant and finding (step 6)
- `src/segfacet/default_config.yaml` — the threshold documented as a comment only, no new parsed key (step 7)
- `src/segfacet/failure_modes.py` — mode 3's new edge, corrected candidate-feature path, `mechanism` and case `reason` (step 8)
- `docs/aide/feature_catalogue.generated.json` — regenerated; two new leaf paths
- `docs/aide/feature_catalogue.generated.md` — regenerated; same
- `docs/aide/failure_modes.generated.json` — regenerated; mode 3's edge, rung and derived status move
- `docs/aide/failure_modes.generated.md` — regenerated; same, and this is the rendering item 168's gate reads
- `docs/aide/traceability_matrix.generated.json` — regenerated; the new detector and edge
- `docs/aide/traceability_matrix.generated.md` — regenerated; same
- `docs/aide/golden_evidence.generated.json` — regenerated; the `split` case gains a finding
- `tests/test_167_mode_3_detector.py` — this item's own test module
- `tests/report_format_fixture.py` — the hand-written components block gains both keys, or the format contract no longer matches the emitted key set
- `tests/golden/report_format_contract.json` — regenerated from the fixture above, only via `.venv/bin/python -m tests.report_format_fixture`
- `tests/test_124_observed_range.py` — the `len(paths) == 138` leaf-path pin and its AC18 docstring
- `tests/test_131_tangent_direction_normalisation.py` — `_PRE_ITEM_TOTAL_LEAF_PATH_COUNT`
- `tests/test_132_monotonicity_against_traversal_order.py` — the `leaf_count == 138` pin and `_PRE_ITEM_OBSERVED_SUMMARY`
- `tests/test_136_rule_mode_declarations.py` — `_CORROBORATED["fragmentation"]`, `expected_co_detections`, and the module comment naming fragmentation's modes
- `tests/test_137_mode_less_rule_disposition.py` — `len(entries) == 138`, the distribution total, and the per-mode path counts
- `tests/test_145_eight_hypothesised_modes.py` — `_EXPECTED_DERIVED_STATUS[3]`
- `tests/test_148_per_path_mode_attribution.py` — `len(cat.entries) == 138`
- `tests/test_151_stage30_validation.py` — the three AC35 consumers read the last counts clause in the Stage 30 section, not the first
- `tests/test_166_split_operator.py` — item 166's AC9 pin of `bar_conditions(3)`
- `tests/test_061_image_features_fusion.py` — only if the suite names it; its hand-built components dict is validated against the schema
- `tests/test_098_stray_components.py` — only if the suite names it; its assertions over the components key set are subset-shaped and are expected to stay green
- `tests/test_103_feature_catalogue.py` — only if the suite names it; its `_RULE_MODE_MAP` is corpus-derived and this item changes no `Expectation`
- `tests/test_149_conformance_report.py` — only if the suite names it; its case counts are unchanged, no case being added

**Asserts against:**

- `tests/corpus/manifest.json` — AC3/AC7/AC8 read the committed geometric manifest and it must not move; no operator or `Expectation` is edited here
- `tests/corpus/fixtures/split_seg.nii.gz` — AC1/AC2 recompute the feature from the committed fixture's own bytes
- `tests/corpus/intensity/manifest.json` — AC3/AC7 sweep the intensity corpus unchanged
- `src/segfacet/traceability.py` — AC11 recomputes `bar_conditions(3)` live; this item adds no reader and changes no scorer

## Testing Strategy

**Test module:** `tests/test_167_mode_3_detector.py`.

One test per acceptance criterion (AC1–AC11), written without being asked. Every
test of the committed corpora reads them through `segfacet.synth.corpus.load_manifest`
/ `segfacet.synth.intensity.load_intensity_manifest` /
`segfacet.synth.regression.pipeline_findings` /
`segfacet.failure_modes.measured_firing` / `segfacet.traceability.bar_conditions`,
never a hand-built copy of a case, and AC1–AC3 recompute the contact area in the
test from the fixture array and header rather than comparing against a literal.

Beyond those, exactly these cases:

- `threshold-margin-on-the-committed-corpora`: recomputed over every label of every case of both manifests, the single firing value exceeds the default threshold by at least 100.0 mm² and every non-firing value is at least 100.0 mm² below it — a threshold set near a fixture value inverts on an unrelated retune, which is the defect item 166 had to record after the fact (`extent_z_mm == 15.0` against a `15.0` bound).
- `force-overlap-stays-silent`: on the committed `force_overlap` case, whose labels 20 and 21 share 725.0 mm² of interface between their **largest** components, `stray_contact_area_mm2` is 0.0 for both labels — a feature defined over all components rather than non-largest ones would fire mode 3's detector on mode 15's case at a value 25 mm² from the split's, and no threshold could separate them.
- `fuse-adjacent-stays-silent`: on the committed `fuse_adjacent` case, label 22's non-largest component (the absorbed neighbour) measures 0.0 — mode 2 is mode 3's converse and its case carries a large detached component, so detachment alone must not decide the mode; contact must.
- `inject-islands-stays-silent`: on the committed `inject_islands` case, mode 4's 27-voxel island measures 0.0 — mode 3's discriminator separates a claimed slab from a small own-label island, and a detector keyed on detachment alone would claim mode 4's case.
- `single-component-label-is-the-sentinel`: a label with `component_count == 1` yields `stray_contact_area_mm2 == 0.0` and `stray_contact_label == 0` — a maximum over an empty set must be the numeric sentinel, not `None` or an exception, or the schema's numeric type and the catalogue's corpus population both break.
- `absence-tolerant-detector`: the detector emits no finding for a record whose `components` block carries neither new key, and does not raise — A5 leaves both keys out of the schema's `required`, so a record predating them must stay readable.
- `existing-detectors-unchanged`: the committed `split` case still produces exactly one `("fragmentation", "components")` finding and no `("fragmentation", "islands")` finding — the three detectors share a rule and a severity parameter, and an edit to the shared body would move mode 1's and mode 4's detectors silently.
- `record-is-not-mutated`: evaluating the rule over the `split` case's feature record leaves that record equal to a fresh extraction — the house invariant `fragmentation`'s docstring already states for its two existing detectors.
- `spacing-is-read-from-the-header`: the contact area computed for a synthetic two-label map at anisotropic spacing equals the face count times the correct per-axis face area, recomputed in the test — a hardcoded isotropic face area passes on the whole committed corpus (1 mm isotropic) and is wrong on every real scan.

**What new values this change emits, and the sweep for them.** The lesson item 166
paid twice for (`docs/aide/insights.md`, item 166, 2026-09-20) is that a
reconciliation sweep must ask what new **values** a change emits, not only which
files it touches. This change emits: two new leaf paths into every report
(`stray_contact_area_mm2`, `0.0` everywhere except one label at `750.0`;
`stray_contact_label`, `0` everywhere except one label at `22`), one new finding on
one corpus case, one new detector id in the findings stream, two new catalogue
entries, one new specification edge, and a changed derived status and rung for mode
3. Swept for assertions comparing freshly computed output against a literal set:
`tests/test_126_golden_retirement.py::test_adv_format_fixture_floats_do_not_appear_in_any_fresh_corpus_report`
was checked directly — its `distinctive_floats` excludes `0.0`/`0.5`/`1.0` and the
post-166 fixture set is `{-84.62037195428361, 1e-12, 27.31460592837104,
53.47129068415773, 106.98418277680141}`, none of which the new fields can emit, so
**no edit is expected there**; the catalogue's `observed_summary` distribution and
the leaf-path counts are the value surfaces that do move, and are listed below.

**Existing tests to reconcile.** Each surface was found by reading it, then
confirmed against this tree on 2026-09-20. Every file is declared under
**Authorised paths → May change** with its edit named. The first group goes **red**
without the edit:

1. `tests/test_166_split_operator.py` — its AC9 test pins
   `tuple(c.met for c in bar_conditions(3)) == (True, False, False, False, False)`.
   Narrow it to the item-166 half that still holds (condition 1 met, its eight
   completeness subjects) and hand the five-tuple to this item's AC11, with a dated
   item-167 comment; do **not** delete item 166's provenance.
2. `tests/test_145_eight_hypothesised_modes.py` — `_EXPECTED_DERIVED_STATUS[3]`
   moves from `"implemented"` to `"validated"`, with a dated item-167 comment.
   `_GEOMETRIC_CORPUS_MODE_IDS` already carries `3` from item 166 and does not move.
3. `tests/test_136_rule_mode_declarations.py` — `_CORROBORATED["fragmentation"]`
   moves from `(1, 4)` to `(1, 3, 4)`; `expected_co_detections` **loses**
   `("fragmentation", 3)`, because mode 3 is now declared rather than a recorded
   co-detection; the module comment naming fragmentation's modes is corrected.
4. `tests/test_151_stage30_validation.py` — the three AC35 consumers
   (`_STATUS_COUNTS_RE`, `_RUNG_COUNTS_RE`, `_VALIDATED_SPLIT_RE`) use
   `re.search` over the Stage 30 section and so read the **first**, now superseded,
   clause. Switch each to the **last** match, so the test reads the current
   attestation the step-9 amend appends. The two negative-control tests that build
   their own text keep `search`.
5. `tests/test_124_observed_range.py` — `assert len(paths) == 138` and the AC18
   docstring naming 138.
6. `tests/test_131_tangent_direction_normalisation.py` —
   `_PRE_ITEM_TOTAL_LEAF_PATH_COUNT = 138`.
7. `tests/test_132_monotonicity_against_traversal_order.py` — `leaf_count == 138`,
   and `_PRE_ITEM_OBSERVED_SUMMARY` (the new all-zero paths land in one of its
   verdict buckets). Re-measure both; do not transcribe a prediction.
8. `tests/test_137_mode_less_rule_disposition.py` — `len(entries) == 138`,
   `sum(distribution.values()) == 138`, and the per-mode path counts in the same
   test. Re-measure each.
9. `tests/test_148_per_path_mode_attribution.py` — `len(cat.entries) == 138`.
10. `tests/report_format_fixture.py` and `tests/golden/report_format_contract.json`
    — the fixture's hand-written `components` block gains both keys (use `0.0` and
    `0`, which are outside the distinctive-float set the item-166 invariant
    protects), and the contract is regenerated with
    `.venv/bin/python -m tests.report_format_fixture`, never by hand and never from
    a test.

Conditional — declared so a surprise is not a scope violation, with no edit
expected:

11. `tests/test_061_image_features_fusion.py` — hand-builds a `components` dict and
    validates it; stays green while the new keys are outside the schema's `required`
    (A5).
12. `tests/test_098_stray_components.py` — its components key-set assertions are
    subset-shaped (`<=`, `in`) and its field-order pin covers the first five fields
    only, so appending the new fields keeps it green.
13. `tests/test_103_feature_catalogue.py` — `_RULE_MODE_MAP` is derived from the
    `synth` `Expectation`s, which this item does not touch.
14. `tests/test_149_conformance_report.py` — its case counts are unchanged; no
    corpus case is added or removed.

Covered automatically — no edit and no new test:

- **Item 163's specificity ratchet.** `test_163::test_ac2_ratchet_measured_equals_expected`
  is parametrised from the live conformance report and compares rule-id sets; A3
  keeps every case's set where it is, so the ratchet stays green **without being
  widened or weakened**. AC8 states that as a claim rather than leaving it implicit.
- **Item 164's two conformance directions.** The new detector is named by a new
  edge, and the new edge names only a declared detector, so both `detector_to_edge`
  and `edge_to_detector` stay empty; `test_164` derives its expected holes live.
- **Item 162's exercise report.** It is per-rule and per-operator, and
  `fragmentation` is already exercised; the operator direction is unchanged.
- **Corpus sensitivity.** The `split` case was already a caught expected-failure
  record, so `test_057`'s and `test_120`'s cohort ratios do not move.

## Validation

Beyond the suite, observe the two things this item exists to produce, from the repo
root with the bootstrapped venv:

1. **The detector explains the split.**
   `.venv/bin/python -m segfacet.cli run --seg tests/corpus/fixtures/split_seg.nii.gz --no-reference --out <tmp>`
   (`--no-reference` is required — CLAUDE.md's gotcha on the real-VerSe default).
   Read the human-readable report: label 23 must carry **two** findings — the
   pre-existing `Fragmentation:` one and the new neighbour-contact one naming the
   contact area, the threshold and label **22** as the label that claimed the part —
   and label 22 must carry none.
2. **Mode 3's rendering is honest and at the bar.** Read mode 3's section in the
   regenerated `docs/aide/failure_modes.generated.md`: it must show the new
   `fragmentation` / `neighbour_contact` edge at `synthetic-demonstrable`, derive
   `validated`, and no longer claim the mode has no detector of its own. This is the
   rendering item 168's human gate puts in front of the maintainer.

No `[validation]` profile is needed: everything above runs CPU-only in the default
venv.

## Dependencies

- **Item 162** (per-rule and per-operator exercise report) — the new detector must land in it without editing the report's code; merged.
- **Item 163** (specificity ratchet) — the ratchet must stay green with no widening; AC8 is the claim that it does. Merged.
- **Item 164** (first-class detector ids) — supplies `RuleDetector`, `IntendedRule.detector_ids` and `modes_for_detector`, which AC4/AC5/AC10 read; merged.
- **Item 165** (mode 4 at the bar) — supplies `traceability.bar_conditions`, which AC11 reads, and `PROXY_RULE_IDS`; merged.
- **Item 166** (the split operator and mode 3's corpus case) — supplies the committed `split` fixture and manifest case every measurement here is taken on, and its own test module carries the `bar_conditions(3)` pin this item narrows; merged.

**Downstream:** item 168 raises the queue's human gate over modes 3 and 4 as
rendered in `docs/aide/failure_modes.generated.md`, and records each mode's sign-off
in `src/segfacet/failure_modes.py`. **What this item must leave ready for it:** mode
3's specification entry complete and its five computable bar conditions met and
asserted (AC11); a `mechanism` that states the detector, the feature it reads, the
threshold and its measured margins; a corpus case whose `reason` distinguishes mode
1's co-detection from mode 3's own firing; and a regenerated
`failure_modes.generated.md` in which all of that reads correctly to someone who was
not here. Item 169 then attests Stage 32 and Stage 20 from a clean clone with its
own venv.

**What only a person can decide, and is therefore not an acceptance criterion
here.** Two things, both for item 168's gate. First, condition 6 itself — whether
mode 3 as built is an acceptable end state for the mode; no agent resolves that, and
nothing in this spec asserts an outcome for it. Second, **whether mode 3's detector
belongs on the `fragmentation` rule at all**, rather than on a rule named for the
mode: A2 takes the cheaper, item-164-shaped default and records what it costs, but
"does this rule make sense for this mode" is exactly the judgement the roadmap says
is not derivable from the code, and the maintainer may reverse it. Reversing it is a
later item, not a correction to this one.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether the two unbuilt candidate paths
  (`spline_leave_one_out_shape_change`, `metric_change_under_merge_candidate`) should
  ever be built for mode 3. The first candidate measured separates the corpus
  completely (A1), so under `prototype` posture this item stops there; both stay in
  `candidate_features` as `hypothesised` so the question is deferred, not forgotten.
- **Left open:** the detector misses a split in which the **donated** part is larger
  than the receiving label's own body — the contacting component would then be that
  label's largest and the feature reads `0.0`. Not expressible on the synthetic
  corpus as it stands (item 166's `split` donates 0.4 of the donor), and inventing a
  fixture for it is a new corpus case, which this item deliberately does not add
  (A7). A later item that adds a second mode-3 case meets both this gap and the
  universal-versus-existential divergence in condition 2 at the same time.
- **Left open:** whether `stray_contact_area_mm2` and `stray_contact_label` should
  join the report schema's `required` list. A5 leaves them optional to keep nine
  hand-built test fixtures valid and to let the detector read a pre-item record;
  tightening the schema is a separate, mechanical item.
- **Left open:** whether `100.0` mm² survives real data. It is calibrated on the
  synthetic corpus alone, where the nearest competing value is `0.0`; roadmap Stage
  21 re-calibrates thresholds on real GT, and a real segmentation's facet-joint
  contact is the case that will test it.
