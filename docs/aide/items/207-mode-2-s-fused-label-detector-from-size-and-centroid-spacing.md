<!-- aide-template: item 3 -->
# Item 207 — Mode 2's fused-label detector, from size and centroid spacing

> **Created:** 2026-09-30 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (D5 re-plan)
> **Queue:** [`../queue/queue-027.md`](../queue/queue-027.md) · Item 207
> **Objectives:** G2, G8
> **Suggested branch:** `aide/207-mode-2-s-fused-label`

---

## Description

This item gives mode 2 (fused vertebra segments) a detector of its own for a
label that covers two whole vertebrae. It is one of the four re-plan items
(205–208) that must land before the at-the-bar sign-off of modes 2 and 3
under gate `gate-0133` (item 203; `queue-027.md`, "Re-plan").

**Why the detector is needed.** Mode 2 has three committed geometric cases.
`split` (the paired case) is decided by `neighbour_contact`'s
`stray_contact` detector. The other two are decided by nothing of mode 2's
own:

- `fuse_adjacent` (item 176): one connected label 22 over the L3 and L4
  bodies, disc gap bridged, L5 renumbered 23. It fires nothing.
- `fuse_separate` (item 206): label 22 over the L3 and L4 bodies with the
  gap unlabelled, L5 renumbered 23. It fires only `fragmentation` (mode 1's
  detector, a co-detection).

Both carry the same two signals, and neither signal decides mode 2 alone
(`insights.md`, item 198, 2026-09-29, the mode-6 spacing entry):

- **Size.** The fused label reads about twice a single level's volume. A
  label that is merely large reads large too: `split`'s label 24 (all of L5
  plus L4's cap) reads 1.53 times its larger neighbour.
- **Spacing.** The fused label's centroid falls between its two bodies, so
  the inter-centroid spacings on either side of it read about 1.5 times the
  pitch (`stage3.spacing_consistency.spacings_mm[]`). A missing or skipped
  level widens a spacing too, at normal size: `relabel_swap`'s label 20 reads
  1.79 times the case's other spacings.

**The detector.** A new rule, `fused_label`, in its own module
`src/segfacet/heuristics/fused_label.py`, with one detector, also
`fused_label`. It fires on a label that is **both** large relative to its
adjacent labels **and** flanked by wide spacing (A1–A5). It serves mode 2
alone. It follows the rule-engine architecture: the module self-registers
through `@register_rule` and one import line in `heuristics/__init__.py`;
its thresholds are read from `HeuristicConfig` under `rules.fused_label`;
`config.rule_enabled("fused_label")` gates it inside the unchanged runner.

**What this item changes.**

- `heuristics/fused_label.py` (new) and one import line in
  `heuristics/__init__.py`.
- `default_config.yaml`: a commented documentation block, no active section
  (A5).
- `failure_modes.py`, `_MODE_2`: a `fused_label` edge, both fuse cases'
  expected sets, their reasons, and the mechanism. Modes 6 and 10: the
  mechanism clause that says no rule reads the spacing path, and the
  `remove_level_relabel` reason that says the same (A10).
- `synth/component_shape.py`: the bridged and the unbridged-renumbered
  `FusePerturbation` forms' `Expectation`s designate `fused_label` (A9).
- `synth/coverage_border_overlap.py`: one docstring sentence (A10).
- The corpus manifest, the corpus sheet, and the generated specification,
  traceability, catalogue and rule-table documents are regenerated.
- `progress.md`: Stage 30 criterion 3's per-edge rung-count clause is
  amended with `aide progress amend` (A11).
- The existing tests listed under Testing Strategy are reconciled.

**Not in scope.**

- No feature, no fixture and no threshold of another rule. No existing
  corpus case other than `fuse_adjacent` and `fuse_separate` fires
  differently (A7).
- The default unbridged `fuse` form's `Expectation` (A9).
- Mode 3's own detector (item 208) and `MODE_SIGN_OFFS` (item 203).
- A spacing rule for modes 6 and 10 (Left open).

## Acceptance Criteria

Terms used below:

- **"The corpus cases"** are every entry of
  `segfacet.synth.corpus.load_manifest()["cases"]` (the geometric corpus)
  and every entry of
  `segfacet.synth.intensity.load_intensity_manifest()["cases"]` (the
  intensity corpus).
- **"A case's findings"** are
  `segfacet.synth.regression.pipeline_findings(case)` for a geometric case
  and `segfacet.synth.regression.intensity_pipeline_findings(case)` for an
  intensity case, each under the bundled default config. These are the
  functions `failure_modes.measured_firing` dispatches to.

- [ ] **AC1: `fused_label` fires on the two fused labels and nowhere else.**
  The set of `(corpus, case_id, label)` triples, over the corpus cases and
  over every finding of a case whose `rule_id == "fused_label"` and every
  label in that finding's `labels`, equals
  `{("geometric", "fuse_adjacent", 22), ("geometric", "fuse_separate", 22)}`.
- [ ] **AC2: the detector serves mode 2 alone.**
  `segfacet.failure_modes.modes_for_detector("fused_label", "fused_label") == (2,)`.

Why each is written:

- AC1 is the queue's "fires on `fuse_adjacent` and on item 206's case" and
  "stays silent on `clean_control` and on every other case in both corpora,
  across the lordotic base's normal spacing variation", as one equality over
  both corpora. The label is part of the triple, so a detector that fired on
  a neighbour of the fused label fails it. It also carries "neither signal
  decides alone": `split` (size 1.53, spacing 1.05) and `relabel_swap`
  (size 1.00, spacing 1.79) are in the silent set, and each passes one gate.
- AC2 is the queue's "it serves mode 2 alone". `modes_for_detector` is
  computed from every mode's edges, so an edge on another mode, or none on
  mode 2, fails it.

Not written, because something already fails without them:

- "Both mode 2 cases' expected sets are updated to include it":
  `tests/test_163_specificity_ratchet.py` fails on any committed case whose
  measured firing differs from its expected set, and so do
  `tests/test_145_eight_hypothesised_modes.py`'s AC13 and
  `tests/test_146_ninth_mode_and_first_proposed.py`'s AC21.
- The manifest's designations for the two cases:
  `tests/test_040_synthetic_corpus.py`'s AC17 (manifest equals the
  operator's `Expectation`), `tests/test_041_regression_suite.py`'s AC4–AC6
  and `tests/test_110_neighbourhood_wiring.py`'s AC11 (`verify_case` over
  every case) cover them.
- "Mode 2 meets bar conditions 1–5 live":
  `tests/test_167_mode_3_detector.py::test_ac11_mode_2_meets_all_five_bar_conditions`
  and `tests/test_187_neighbour_contact_rule.py::test_ac13_mode_2_meets_all_five_bar_conditions`
  assert it and stay unedited in that assertion. Condition 3 is the one this
  item could break: it quantifies over every qualifying detector's signal
  paths, so a `fused_label` signal path the catalogue does not cover would
  fail it.
- The declaration mirrors the edge: `catalogue.rule_declaration_conflicts()`
  reports a declared mode with no edge, and
  `tests/test_136_rule_mode_declarations.py` asserts it returns `()`.
- The rule is registered and enabled by default:
  `tests/test_148_per_path_mode_attribution.py`'s AC16 requires its
  `_AC16_CASES` to cover every registered rule id, and AC1 above cannot
  pass through the pipeline unless the runner runs the rule.
- The rule-table row: `tests/test_202_rule_table.py` compares the committed
  `docs/aide/rules.generated.md` with a fresh render.

None of these closes a Stage 33 acceptance criterion. Criterion 1 is closed
by item 203's sign-off; criteria 2 and 3 are attested by item 204's
clean-clone replay.

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
measured value below was taken on this branch on 2026-09-30 with
`.venv/bin/python`, by scratch probes that registered a prototype of the
rule in memory (A1–A5 exactly), replaced `failure_modes.SPECIFICATION` with
a dict whose mode 2 carries the new edge and expected sets, and patched
`segfacet.synth.corpus.load_manifest` to return the committed manifest with
the two fuse cases re-designated as A9 says. No fixture's voxels change, so
the committed fixtures were read as they are. The builder re-measures each
value on the real change.

- **A1 (decided: what "large" is measured against).** A label's
  `size_ratio` is its `per_label.{label}.geometry.physical_volume_mm3`
  divided by the **larger** `physical_volume_mm3` of its adjacent labels.
  Adjacency is the order `stage3.spacing_consistency.spacings_mm[]` is
  computed in: the record's present labels in ascending integer order
  (`pipeline.extract_feature_record`, `ordered_centroids`), so
  `spacings_mm[i]` lies between the i-th and (i+1)-th label. This is
  relative to the neighbouring labels, as the queue prefers, and needs no
  reference. The larger neighbour is used, not the mean, so that a label
  beside an undersized neighbour (a cap, a truncated vertebra) does not read
  large: `split_own_label`'s label 22 reads 0.79 against its larger
  neighbour but would read 1.31 against the mean.
- **A2 (decided: the spacing gate).** A label's `spacing_ratio` is the
  **smaller** of the spacings adjacent to it (one or two), divided by the
  median (`statistics.median`) of the case's spacings that are **not**
  adjacent to it. A fused label's centroid sits between its two bodies, so
  both its spacings widen; the smaller one must still be wide. The baseline
  excludes the label's own spacings, so the label cannot widen its own
  baseline.
- **A3 (decided: first and last labels).** An end label has one adjacent
  label and one adjacent spacing, and it is judged on those. A label with no
  non-adjacent spacing to form a baseline is not judged: every label of a
  two-label map, and the middle label of a three-label map. Measured on the
  corpus base (`segfacet.synth.build_clean_spine()`), the bridged fuse of
  L5 (label 24) into L4 (label 23), `FusePerturbation(target_label=23,
  neighbour_label=24, bridged=True)`, leaves the fused label last and fires
  `fused_label` on label 23 alone: size 2.3317, spacing 1.5734.
- **A4 (decided: sacral and coccygeal labels are never candidates).** A
  label whose `level_name` starts with `"S"` (`labels.SACRUM`) or equals
  `"Cocc"` is not judged. They still count as adjacent labels and their
  spacings still count. A sacrum label covers several fused segments and
  sits last, so it would read large and widely spaced on every real scan
  that includes it.
- **A5 (decided: thresholds, comparison and config).** Fire when
  `size_ratio > size_ratio_threshold` **and**
  `spacing_ratio > spacing_ratio_threshold`, both strictly (item 027's
  convention). Defaults `DEFAULT_SIZE_RATIO = 1.5` and
  `DEFAULT_SPACING_RATIO = 1.25`: each is the midpoint between a single
  level (1.0) and the fused reading the queue predicts (2.0 for size, 1.5
  for spacing). Calibrated on the synthetic corpora only (Stage 21
  re-calibrates on real data). Read through
  `config.rule_param("fused_label", "size_ratio_threshold", default=...)`,
  `"spacing_ratio_threshold"` and `"severity"` (default
  `"flagged-for-review"`). No active `rules.fused_label` section is added to
  `default_config.yaml`: an active section would change the parsed `rules`
  dict and so `config_hash` in every report, which is why
  `neighbour_contact`, `spline_offset` and `intensity` ship section-less.
  `rule_enabled` returns `True` for an absent section.
- **A6 (decided: rule identity).** `rule_id = "fused_label"`, one
  `RuleDetector(detector_id="fused_label")` with the message tag
  `"Fused label:"`. One finding per firing label, `labels` that label alone,
  in ascending label order. `mode_declaration.modes == (2,)` with
  `evidence` led by `"corpus-manifest"`. `consumed_paths`: `per_label`
  (bookkeeping, the container iterated),
  `per_label.{label}.geometry.physical_volume_mm3` (signal),
  `per_label.{label}.level_name` (bookkeeping: names the level and excludes
  sacral labels), `stage3.spacing_consistency.spacings_mm[]` (signal). The
  detector's `signal_paths` are the two signal paths, and its `params` are
  `(("size_ratio_threshold", 1.5), ("spacing_ratio_threshold", 1.25))`. No
  `condition_opt_ins`, so the runner's gate drops a finding on a
  `fov_truncation` or `displaced_vertebra` label. Mode 2's new edge is
  `IntendedRule(rule_id="fused_label", detector_ids=("fused_label",),
  evidence_rung="synthetic-demonstrable")`.
- **A7 (measured: what fires).** With the prototype registered, over the
  corpus cases, `fused_label` fires exactly twice:
  - `fuse_adjacent`, label 22: volume 45043 mm³ against 19375 (label 21)
    and 19344 (label 23), size 2.3248; spacings `[33.49, 49.51, 53.52]`,
    spacing 49.51 / 33.49 = 1.4782. The case's findings become exactly one
    `("fused_label", "fused_label")` finding on label 22; verdict
    `flagged-for-review`.
  - `fuse_separate`, label 22: volume 38781 mm³, size 2.0016; spacings
    `[33.49, 49.46, 53.50]`, spacing 1.4768. Findings
    `("fragmentation", "components")` and `("fused_label", "fused_label")`,
    both on label 22; verdict `flagged-for-review` (unchanged).

  Every other case is silent. Highest readings among silent labels: size
  4.8000 (`split_own_label` label 24, beside the 4030 mm³ cap; spacing
  0.8885), 1.5263 (`split` label 24; spacing 1.0512); spacing 1.7915
  (`relabel_swap` label 20; size 1.0000), 1.2899 (`fuse_separate` label 23;
  size 0.4988), 1.2896 (`fuse_adjacent` label 23; size 0.4295). On
  `clean_control` and all four intensity cases the maxima are size 1.0032
  and spacing 1.0999. Over every rung of `SEVERITY_LADDERS` and
  `SUPPLEMENTARY_LADDERS` it fires only on the supplementary `fuse` ladder's
  rungs 1 and 2 (label 20). Over all 13 registered operators at seeds 0–5
  and spacings (1,1,1) and (1,1,3), only `fuse` fires it.
- **A8 (measured: what the derivations move).**
  - `specification_conflicts()`, `catalogue.rule_declaration_conflicts()`,
    `catalogue.path_classification_conflicts()` and
    `traceability.operator_reason_conflicts()` all return `()`.
  - Conformance: 18 cases (14 geometric plus 4 intensity), all agree.
  - `bar_conditions(2)`: conditions 1–5 all met, before and after.
    Condition 2's subjects `("split",)` → `("fuse_adjacent", "split",
    "fuse_separate")`. Condition 3's subjects gain
    `per_label.{label}.geometry.physical_volume_mm3` and
    `stage3.spacing_consistency.spacings_mm[]`. Condition 4's subjects
    `("neighbour_contact/stray_contact",)` →
    `("fused_label/fused_label", "neighbour_contact/stray_contact")`.
  - `bar_conditions(3)` is unchanged: 1, 2 and 5 met; 3 and 4 not.
  - Derived status and derived mode rung are unchanged for every mode.
    Counts over 16 modes: validated 6, implemented 3, specified 2, proposed
    5; rungs synthetic-demonstrable 5, needs-real-data 3,
    structurally-unobservable 1, none 7; validated through a
    pipeline-detected case 6, through a reconstructed record only 0.
  - **Per-edge rung counts move**: 13 edges (synthetic-demonstrable 5,
    needs-real-data 7, structurally-unobservable 1) → 14 edges
    (synthetic-demonstrable 6, needs-real-data 7, structurally-unobservable
    1).
  - `catalogue.scan_synth_rule_mode_map()` gains `"fused_label": (2,)`.
    The catalogue keeps 145 entries. `stage3.spacing_consistency.spacings_mm[]`
    goes from `failure_modes ()`, `mode_evidence ()`, no consuming rule, to
    `(2,)`, `("rule_mode_map", "rule_declaration")`, `("fused_label",)`.
    `per_label`, `per_label.{label}.geometry.physical_volume_mm3` and
    `per_label.{label}.level_name` gain `fused_label` as a consuming rule
    with their modes unchanged. So entries carrying mode 2 go 10 → 11, the
    `()` bucket 91 → 90, and the `("rule_mode_map", "rule_declaration")`
    bucket 10 → 11.
  - Traceability: one new rule row and one new exercise row (`fused_label`,
    exercised by `geometric/fuse_adjacent` and `geometric/fuse_separate`);
    mode 2's row gains the edge and the read path; "Read by >=1 rule" 52 →
    53.
  - `docs/aide/golden_evidence.generated.json` does not move (its unwired
    count reads catalogue status, and `spacings_mm[]` keeps its authored
    `retune` status).
  - Cohort evaluation over the geometric corpus (the shape
    `tests/test_057_acceptance_stage7.py` and `tests/test_120_leave_one_out_offset.py`
    build): `fuse_adjacent` becomes an expected-failure record and a true
    positive. Sensitivity 1.0, false-positive rate 0.0, mode 2 `n_cases`
    2 → 3, sum of `n_cases` 10 → 11. `calibrate_thresholds` over modes
    `(1, 2, 3, 4, 6, 9)` with test_057's AC13 axis is feasible.
- **A9 (decided: which `Expectation`s move).** `FusePerturbation`'s bridged
  form (`fuse_adjacent`) designates `expected_rule_ids={"fused_label"}`,
  `expected_labels={target}`, `expected_verdict="flagged-for-review"`. The
  unbridged-renumbered form (`fuse_separate`) designates
  `{"fragmentation", "fused_label"}`, labels and verdict unchanged. Both
  `detail` strings stop saying mode 2's signal is read by no rule. The
  default unbridged form (the supplementary ladder's, not a committed case)
  keeps `{"coverage", "fragmentation"}`, although it now also fires
  `fused_label`. Its designation already omits `sequence`, which it also
  fires, so it is not an exact firing set, and
  `tests/test_037_component_shape_perturbations.py`'s AC10 and
  `tests/test_206_fuse_separate_fixture.py`'s
  `default-unbridged-form-unchanged` case pin it.
- **A10 (constraint: the mechanisms that name the spacing path).**
  `tests/test_138_traceability_matrix.py::test_ac31_named_feature_path_is_consumed_by_one_of_the_modes_declared_rules`
  checks every catalogue path a non-proposed mode's `mechanism` names from
  the set of rule-consumed paths: some rule of that mode, or some rule its
  cases co-detect, must consume it. Today no rule consumes
  `stage3.spacing_consistency.spacings_mm[]`, so no mechanism naming it is
  checked. Once `fused_label` consumes it, modes 6 and 10 fail the check:
  both mechanisms name it, and neither mode's rules (`coverage`, `sequence`)
  consume it. Measured by replaying the check over the probe's matrix. So
  modes 6's and 10's mechanisms must describe the doubled spacing in words
  without writing the dotted path, and must stop saying no rule reads it.
  Mode 2's mechanism may name the path (its own rule reads it). Proposed
  modes 7 and 13 also name it; the check skips proposed modes, and neither
  sentence claims no rule reads it, so both stay.
- **A11 (defensible default: Stage 30 criterion 3 is amended).**
  `tests/test_151_stage30_validation.py::test_ac35_rung_counts_note_matches_live_derivation`
  compares the last `per-edge rung counts over N edges` clause in Stage
  30's section with a live recount; today's last clause is item 194's (13
  edges: 5, 7, 1). The builder amends criterion 3 with `aide progress
  amend`, as items 167, 188, 192, 193 and 194 did. No status-count clause
  and no Stage 20 clause moves (A8), so criterion 1 of Stage 30 and
  `tests/test_169_stage32_validation.py`'s AC6, AC7 and AC8 need nothing.
- **A12: no human gate, and no environment-gated capability.**

## Implementation Steps

1. **`src/segfacet/heuristics/fused_label.py` (new)**, modelled on
   `heuristics/neighbour_contact.py`:
   - Module docstring: the item, the two signals and why neither decides
     alone, the design decisions A1–A6 with their measured values (A7), and
     a scope fence (no feature, no other rule, modes 6 and 10's spacing rule
     is not this rule).
   - `DEFAULT_SIZE_RATIO: float = 1.5` and `DEFAULT_SPACING_RATIO: float =
     1.25`, each with a docstring giving the rationale and the measured
     margins (A5, A7).
   - A module-level `_severity_from_param`, as each of the twelve rule
     modules defines its own (its message names the rule).
   - `@register_rule class FusedLabelRule(Rule)` with the A6 declaration.
   - `evaluate(record, config)`:
     - read `severity` first, so a bad string raises `ValueError` before any
       work, then both thresholds via `config.rule_param`;
     - read `record.get("stage3")`, its `spacing_consistency` and its
       `spacings_mm` **before** touching `per_label`; return `[]` when any
       of them is absent, is not the expected type, or when
       `len(spacings_mm) != len(per_label) - 1` (the record's labels are
       not the ones the spacings were computed over);
     - order `per_label`'s keys by `int` (they are strings in a serialised
       record, ints in some test records); return `[]` if any entry is not
       a dict carrying a numeric `geometry.physical_volume_mm3` (the case is
       then not judged);
     - per label, skip it under A3 and A4, compute `size_ratio` and
       `spacing_ratio` (A1, A2) with `statistics.median`, and emit one
       finding when both exceed their thresholds.
   - The reason names the label, its level, both ratios, the larger
     neighbour's label and both thresholds. Read the record exactly as the
     prototype did (`.get` / subscript on the paths A6 declares and no
     others), so the catalogue's access trace and AST scan attribute to it
     exactly the declared paths: `catalogue.path_classification_conflicts()`
     must return `()`.
   - Never mutate the record.
2. **`src/segfacet/heuristics/__init__.py`.** One import line after
   `spline_offset`'s: `from segfacet.heuristics import fused_label  # noqa:
   F401 — registers FusedLabelRule (item 207)`. The runner is not touched.
3. **`src/segfacet/default_config.yaml`.** A commented block after
   `neighbour_contact`'s, in its shape: what the rule reads, why it is
   section-less, and the two defaults and severity as comments only.
4. **`src/segfacet/failure_modes.py`, `_MODE_2`.**
   - `intended_rules`: append the A6 edge.
   - `corpus_cases`: `fuse_adjacent` `expected_firing=("fused_label",)`,
     `fuse_separate` `expected_firing=("fragmentation", "fused_label")`.
     Rewrite both reasons: pipeline-detected, measured live via
     `segfacet.synth.regression.pipeline_findings` (date, item 207), the
     two ratios with the volumes and spacings they come from (A7), and for
     `fuse_separate` that `fragmentation` stays a co-detection.
   - `mechanism`: rewrite the absorbed and separate-bodies sentences around
     `fused_label` (both ratios, both thresholds, strictly above). Keep the
     paired-case sentence. It may name
     `stage3.spacing_consistency.spacings_mm[]` and
     `per_label.{label}.geometry.physical_volume_mm3`. Keep a whole-word
     `split`, `fuse_adjacent` or `fuse_separate` (test_138's AC31 token
     check). Do not use the `(measured: findings == [...])` idiom.
   - `candidate_features`: unchanged; both signal paths are already there.
5. **`src/segfacet/failure_modes.py`, modes 6 and 10 and the module
   docstring (A10).**
   - Mode 6 `mechanism`: the sentence on `remove_level_relabel`'s doubled
     spacing names the spacing in words, without the dotted path, and says
     that no mode-6 rule reads it; `fused_label` reads spacing only beside
     a doubled size, so it is silent there.
   - Mode 6's `remove_level_relabel` `reason`: re-point "no shipped rule
     reads stage3.spacing_consistency.spacings_mm[]" the same way. The
     measurement date stays.
   - Mode 10 `mechanism`: the last sentence likewise.
   - Append an item-207 paragraph to the module docstring's history.
   - Nothing else in any mode changes; `MODE_SIGN_OFFS` is not touched.
6. **`src/segfacet/synth/component_shape.py`.** In `FusePerturbation.apply`,
   the bridged and unbridged-renumbered branches' `rule_ids`,
   `offending`, `verdict` and `detail` as A9 says; update the class
   docstring. The default unbridged branch and all voxel logic are
   unchanged.
7. **`src/segfacet/synth/coverage_border_overlap.py`.**
   `RemoveLevelRelabelPerturbation`'s docstring: "which no shipped rule
   reads" becomes that no rule reads it for this mode. Docstring only.
8. **Regenerate.** Run each generator twice into temp paths, byte-compare,
   then once with no flags to write the committed copies:
   - `.venv/bin/python -m segfacet.synth.corpus`. Only `manifest.json` may
     change (the two fuse cases' `expected_rule_ids`, `expected_labels`,
     `expected_verdict` and `detail`). If a fixture's bytes change, hand
     back;
   - `.venv/bin/python -m segfacet.synth.corpus_sheet` (its `Source` digest
     covers the manifest);
   - `.venv/bin/python -m segfacet.failure_modes`;
   - `.venv/bin/python -m segfacet.traceability`;
   - `.venv/bin/python -m segfacet.catalogue`;
   - `.venv/bin/python -m segfacet.rule_table`.

   Do **not** regenerate `golden_evidence`: a fresh
   `python -m segfacet.golden_evidence --out <tmp>` must be byte-identical
   to the committed copy (A8); if not, hand back.
9. **Amend Stage 30 criterion 3** (A11), re-measuring every number live
   first:
   `python .aide/scripts/aide.py progress amend 30 --criterion 3 --evidence "Item 207 (<date>): mode 2 gains fused_label's synthetic-demonstrable edge, adding one edge. Re-measured live: derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7; per-edge rung counts over 14 edges: synthetic-demonstrable 6, needs-real-data 7, structurally-unobservable 1."`
10. **Reconcile** the tests listed under Testing Strategy, each edit with a
    dated item-207 comment.
11. Run `python .aide/scripts/aide.py scope 207` and
    `python .aide/scripts/aide.py check`. Neither may report an error.

No dependency is added. `statistics` is the standard library.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/fused_label.py` — **new**: the rule (step 1).
- `src/segfacet/heuristics/__init__.py` — one import line (step 2).
- `src/segfacet/default_config.yaml` — one comment block (step 3).
- `src/segfacet/failure_modes.py` — mode 2's edge, cases and mechanism; modes 6 and 10's spacing clauses; the docstring (steps 4–5).
- `src/segfacet/synth/component_shape.py` — two `FusePerturbation` `Expectation`s and the class docstring (step 6).
- `src/segfacet/synth/coverage_border_overlap.py` — one docstring sentence (step 7).
- `tests/corpus/manifest.json` — regenerated; the two fuse cases' designations (step 8).
- `docs/aide/corpus_sheet.png` — regenerated; two panel titles and the input digest (step 8).
- `docs/aide/failure_modes.generated.json` — regenerated (step 8).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 8).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 8).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `docs/aide/rules.generated.md` — regenerated; one new row (step 8).
- `tests/test_207_fused_label_rule.py` — **new**: this item's test module.
- `tests/test_040_synthetic_corpus.py` — `fuse_adjacent`'s manifest and pipeline pins.
- `tests/test_103_feature_catalogue.py` — `_RULE_MODE_MAP` gains `fused_label`.
- `tests/test_120_leave_one_out_offset.py` — AC24's `n_cases` sum 10 → 11.
- `tests/test_136_rule_mode_declarations.py` — two rule counts and `stayed_empty`.
- `tests/test_137_mode_less_rule_disposition.py` — the rule count, `mode2_count` and two distribution buckets.
- `tests/test_145_eight_hypothesised_modes.py` — AC13's co-detection probe (the one structural edit).
- `tests/test_148_per_path_mode_attribution.py` — two counts and one `_AC16_CASES` row.
- `tests/test_151_stage30_validation.py` — the edge count 13 → 14.
- `tests/test_167_mode_3_detector.py` — mode 2's condition 4 subjects.
- `tests/test_176_fuse_bridged.py` — AC10's measured firing.
- `tests/test_187_neighbour_contact_rule.py` — the rule count and mode 2's condition 4 subjects.

**The reconciliation fence.** Every edit to an existing test is a moved
literal (a count, a rule id added to a map or a case table, a subjects
tuple, an expected set, a verdict), with a dated item-207 comment. No test
is retired, skipped, `xfail`-marked or loosened. The fence is widened for
one named edit that is not a moved literal:
`tests/test_145_eight_hypothesised_modes.py`'s co-detection probe (Testing
Strategy). A red test in a file not listed here is a hand-back to
spec-author.

**Asserts against:**

- `tests/corpus/fixtures/**` — every fixture must regenerate byte-identical; `tests/test_040_synthetic_corpus.py`'s AC15/AC16 compare them, and AC1 reads them.
- `tests/corpus/intensity/manifest.json` — AC1 reads the intensity cases through it.
- `docs/aide/golden_evidence.generated.json` — must not move (A8).
- `tests/test_163_specificity_ratchet.py` — must stay green unedited; it drives both fuse cases' firing against their expected sets.
- `tests/test_041_regression_suite.py` — must stay green unedited; it drives both fuse cases' verdict, designation and labels.
- `tests/test_138_traceability_matrix.py` — must stay green unedited; its AC31 is what A10's mechanism edits satisfy.

`tests/test_169_stage32_validation.py` is listed under neither heading: no
clause it reads moves (A11), but item 203, which runs later, may edit it.

## Testing Strategy

The test module is `tests/test_207_fused_label_rule.py`, with one test per
AC.

- AC1 iterates both manifests through `pipeline_findings` and
  `intensity_pipeline_findings` (never a hand-built record) and compares
  the triple set with the literal. It never filters to the two fuse cases
  first.
- AC2 calls `modes_for_detector` live.

Adversarial cases, each with the failure mode it guards, and no others:

- `caudal-end-fuse-fires`: on `segfacet.synth.build_clean_spine().seg_img`,
  `FusePerturbation(target_label=23, neighbour_label=24,
  bridged=True).apply(..., seed=0)` then `run_qc` under the bundled config
  gives exactly one `fused_label` finding, on label 23. It guards A3: a
  detector that skipped end labels would miss a fused L4/L5, the commonest
  lumbar position, and neither corpus case puts the fused label last.
- `sacral-label-not-judged`: `fuse_separate`'s record from
  `extract_feature_record`, deep-copied with label 22's `level_name` set to
  `"S1"`, gives `FusedLabelRule().evaluate(record, config) == []`, while
  the unmodified record gives one finding on label 22 (so the control is
  not vacuous). It guards A4: a sacrum label reads large and widely spaced
  on every real scan that includes it.
- `size-threshold-read-from-own-section`: with
  `rules.fused_label.params.size_ratio_threshold` set to 1000.0 (built as
  `tests/test_189_spline_offset_condition.py::test_threshold_read_from_own_section`
  builds its config), `run_qc` on `fuse_separate` gives no `fused_label`
  finding. It guards the size gate being hard-coded or read from another
  key.
- `spacing-threshold-read-from-own-section`: the same with
  `spacing_ratio_threshold` set to 1000.0. It guards the spacing gate the
  same way.

**Existing tests to reconcile.** Found on 2026-09-30 by applying the change
in memory (Assumptions, preamble), replaying the derivations and the
suites' own helper computations, and by two read-only sweeps of every test
module that runs the rule registry, reads its metadata, or pins a corpus
case's firing, verdict or designation.

Moved literals, each with a dated item-207 comment:

- `tests/test_040_synthetic_corpus.py::test_fuse_adjacent_case_records_mode_2_bridged_and_fires_nothing`
  (L496): `expected_rule_ids == []` → `["fused_label"]`,
  `expected_labels == []` → `[22]`, `expected_verdict == "pass"` →
  `"flagged-for-review"`; `list(case_result.findings) == []` becomes the
  findings' `(rule_id, detector_id, sorted(labels))` list equal to
  `[("fused_label", "fused_label", [22])]`; `Severity.PASS` →
  `Severity.FLAGGED_FOR_REVIEW` (whichever member name `segfacet.verdict`
  uses for that label). The name keeps its old wording; append one dated
  sentence to the docstring.
- `tests/test_176_fuse_bridged.py::test_ac10_nothing_fires` (L251):
  `== ()` → `== ("fused_label",)`. The name stays; one dated comment.
- `tests/test_103_feature_catalogue.py`: `_RULE_MODE_MAP` (L597–618) gains
  `"fused_label": (2,)` with a comment naming `fuse_adjacent` and
  `fuse_separate`.
- `tests/test_120_leave_one_out_offset.py::test_ac24_corpus_pipeline_detection_is_nine_of_nine`:
  L816 `sum(m.n_cases ...) == 10` → `== 11` (`fuse_adjacent` becomes an
  expected-failure record; mode 2 `n_cases` 3). Append a dated sentence to
  the docstring, which says `fuse_adjacent` expects "pass".
- `tests/test_136_rule_mode_declarations.py`: L197 `len(pairs) == 12` →
  `13`; L259 `len(list(iter_rules())) == 12` → `13`; L855
  `stayed_empty == 91` → `90`, with a `Reconciled again (item 207,
  2026-09-30)` paragraph in that test's docstring: `spacings_mm[]` leaves
  the `()` bucket because `fused_label` consumes it.
- `tests/test_137_mode_less_rule_disposition.py`: L242
  `len(rules) == 12` → `13`; L951 `mode2_count == 10` → `11`; in the
  distribution table (L959–997), `(): 91` → `90` and
  `("rule_mode_map", "rule_declaration"): 10` → `11`. Append a
  `Re-measured (item 207, 2026-09-30)` docstring paragraph in the shape of
  items 205's and 206's. `len(entries)` stays 145, `mode1_count` 5,
  `mode16_count` 2.
- `tests/test_148_per_path_mode_attribution.py`: L366 `checked == 12` →
  `13` (AC4, one per declaring rule); L1102 `checked == 12` → `13` (AC18,
  one per matrix rule row); `_AC16_CASES` (L855–874) gains
  `("fuse_adjacent", "geo", ("fused_label",))` after the `split` row, since
  AC16 requires the table to cover every registered rule id. L1066 stays
  12: it counts the modules of `_EXPECTED_THRESHOLD_CONSTANTS`, which this
  item does not extend.
- `tests/test_151_stage30_validation.py`: L485 `total_edges == 13` → `14`,
  with a `13 -> 14: item 207` line in the comment above it.
- `tests/test_167_mode_3_detector.py::test_ac11_mode_2_meets_all_five_bar_conditions`:
  L437 condition 4 subjects `("neighbour_contact/stray_contact",)` →
  `("fused_label/fused_label", "neighbour_contact/stray_contact")`. The
  all-five assertion above it stays unedited.
- `tests/test_187_neighbour_contact_rule.py`: L252
  `len(list(iter_rules())) == 12` → `13`; L356 (AC14) the same condition 4
  subjects change as `test_167`. AC13 stays unedited.

The one structural edit, which the fence is widened for:

- `tests/test_145_eight_hypothesised_modes.py::test_ac13_co_detection_alone_does_not_validate`
  (L884). It pins the `derive_status` branch where every case agrees but
  none fires one of the mode's own rules. Its probe is mode 2 restricted to
  `fuse_adjacent`, which now fires `fused_label`, a mode-2 rule, so the
  probe derives `validated` and the disjointness assertion fails.
  **Decision:** the probe also drops the `fused_label` edge,
  `intended_rules=tuple(e for e in live.intended_rules if e.rule_id != "fused_label")`,
  so `fuse_adjacent`'s one firing is by a rule the probe mode does not
  own. The loop, the disjointness assertion and `derive_status(probe) ==
  "implemented"` stay unedited. Measured on the prototype: `case_agrees` is
  `True` and `derive_status` is `"implemented"` (mode 2 is still declared
  by `bounds` and `neighbour_contact`). The docstring gains a dated
  item-207 sentence.

Red until the spec edit and step 8's regeneration land, with no test edit:

- expected sets against measured firing:
  `tests/test_145_eight_hypothesised_modes.py`'s
  `test_ac13_every_expected_firing_equals_a_fresh_measurement` and
  `test_ac13_derived_status_is_the_signed_off_ladder`,
  `tests/test_146_ninth_mode_and_first_proposed.py`'s AC21,
  `tests/test_147_specification_is_the_record.py`'s AC26,
  `tests/test_151_stage30_validation.py`'s AC8 and AC9 (the count stays
  18), `tests/test_149_conformance_report.py`'s AC16,
  `tests/test_163_specificity_ratchet.py`;
- the manifest's designation of `fuse_adjacent` (measured after: verdict
  `flagged-for-review`, `verify_case` `True`, FPR 0.0):
  `tests/test_040_synthetic_corpus.py`'s AC15–AC17,
  `tests/test_041_regression_suite.py`'s AC4 and AC5 (the case moves from
  the undetected set to the designated set, whose AC6 labels `{22}` it
  meets), `tests/test_110_neighbourhood_wiring.py::test_ac11_corpus_verify_case_unchanged`,
  `tests/test_120_leave_one_out_offset.py::test_ac22_every_corpus_case_verifies`,
  `tests/test_057_acceptance_stage7.py::test_ac8_false_positive_rate_is_zero`
  (an expected-"pass" case that flags would be a false positive);
- failure_modes: `test_144` AC19/AC20, `test_145` AC23, `test_146`
  (L132–137, L1331), `test_147` AC24, `test_151` AC4/AC14/AC18, `test_157`
  AC16;
- catalogue: `test_103` AC19, `test_106` AC7, `test_119` (L820–840),
  `test_120` AC30, `test_123` AC47, `test_124` AC17/AC18, `test_129` AC20,
  `test_130` (L747–761), `test_136` AC13, `test_137` AC15, `test_148` AC14;
- traceability: `test_138` AC4, `test_143` AC12/AC15, `test_148` AC18,
  `test_149` AC19/AC20, `test_157` AC17, `test_162` AC9/AC10, `test_164`
  AC9;
- rule table: `test_202`;
- corpus sheet: `test_178` AC7 (the `Source` digest).

**`progress.md` count clauses.** Only Stage 30 criterion 3's per-edge
rung counts move (A8): `tests/test_151_stage30_validation.py::test_ac35_rung_counts_note_matches_live_derivation`
reads it, and step 9's amendment makes it green. Stage 30 criterion 1's
status and validated-split clauses (`test_151` AC35's other two tests), and
Stage 20's status, rung and refined/bar/drafts clauses
(`tests/test_169_stage32_validation.py` AC6, AC7, AC8) do not move.

Checked and unaffected (measured or read):

- `tests/test_037_component_shape_perturbations.py`: the default unbridged
  `fuse` now also fires `fused_label` on the surviving label (seeds 1, 3,
  42 and the explicit (20, 21) pair, both spacings), but every assertion
  holds: the verdict was already `flagged-for-review`, finding labels stay
  within the survivor, and `_flagged_present_labels == expected_labels`.
  AC10's `Expectation` pin holds because A9 leaves that form's designation.
- `tests/test_206_fuse_separate_fixture.py`: AC1–AC3 read attribution and
  voxels; `default-unbridged-form-unchanged` holds under A9.
- `tests/test_057_acceptance_stage7.py`: sensitivity 1.0, FPR 0.0,
  calibration feasible; `_PIPELINE_DETECTABLE_MODES` already carries 2.
- `tests/test_125_stage28_validation.py` AC15 and
  `tests/test_135_stage29_validation.py` AC25: the pipeline-detected modes
  that designate a rule stay `{1, 2, 3, 4, 6, 9}`.
- `tests/test_138_traceability_matrix.py`: `RULE_IDS` only parametrises
  per-rule checks; AC18 compares the matrix with the live registry. It is
  not extended. AC31 holds once A10's edits land.
- Partial and hand-built records run through the full registry: AC16's
  planted `{"overlaps": [...]}` record in `test_148`; `run_rules({}, cfg)`
  and the `reference_delta`-only records in `test_047` and `test_064` (the
  rule sorts before `reference_delta`, so a raise here would pre-empt
  their expected `ValueError`); `test_035_failure_modes`'s int-keyed
  records with `geometry: {}`, including
  `test_adv_gt_record_is_not_accidentally_flagged_by_any_single_rule`'s
  three-label record and the mode-8 record with an empty `per_label`;
  `test_089`'s records with no `physical_volume_mm3`; and the records of
  `test_026`, `test_027`, `test_029`, `test_031`, `test_033`, `test_062`,
  `test_186`, `test_198` and `test_heuristics_bounds_source`. None carries
  `stage3.spacing_consistency.spacings_mm`, so the rule returns `[]` before
  reading `per_label` (step 1). `test_062` plants a non-dict `per_label`
  entry, and `test_033` plants `spacing_consistency` as `None` and as
  `{"a": 1}`; step 1's early returns cover them.
- `tests/test_090_reference_derived_defaults.py` AC16: `config_hash` of the
  bundled config equals both bundled references' provenance hash, and no
  active section is added (A5). An active `rules.fused_label` section would
  fail it permanently, because the real-data production reference cannot be
  rebuilt here.
- `tests/test_138_traceability_matrix.py` AC20's analytic-edge witness: the
  new edge is attributed `corpus`, because both fuse cases' expected sets
  name `fused_label`.
- Clean-spine maps probed silent (L1–L5 at three spacings, thoracic T5–T10,
  C3–C5, L1–L4, L1–L3 including at 20 mm pitch, L1–L2, one level) and every
  perturbed map in `test_038` and `test_039`: `test_036`, `test_038`,
  `test_039`, `test_049`, `test_087` and `test_cli_run` hold.
- `tests/test_100_severity_ladder.py`, `tests/test_154_ladder_remeasurement.py`
  and `tests/test_201_severity_ladder_remeasured.py`: the ladders measure
  per-mode metrics, not findings, and `score_harness` ignores the
  supplementary `fuse` ladder.
- `tests/test_200_bar_condition_2.py`: its mode 2 and mode 3 subjects are
  computed live.
- `tests/test_134_decision_table_evidence_companion.py` and
  `tests/test_126_golden_retirement.py`'s AC22: golden evidence does not
  move (A8).
- `tests/test_065_config_intensity.py`: `_SEVEN_RULE_IDS` is compared with
  the config's active sections, and no section is added (A5).

Comments that go stale but assert nothing, left alone:
`tests/test_057_acceptance_stage7.py` L92 and L204 (`fuse_adjacent`
"designates no rule"), `tests/test_125_stage28_validation.py` L496,
`tests/test_135_stage29_validation.py` L792,
`tests/test_137_mode_less_rule_disposition.py` L852.

## Validation

1. Replay both fuse cases through the CLI:

   ```
   .venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/fuse_adjacent_seg.nii.gz --out <tmp1> --no-reference
   .venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/fuse_separate_seg.nii.gz --out <tmp2> --no-reference
   ```

   `--no-reference` is needed for the reason `CLAUDE.md` gives: the bundled
   VerSe reference is not calibrated for the synthetic corpus. In
   `<tmp1>/segfacet_report.json` the `findings` hold exactly one
   `fused_label` finding, on label 22, and the verdict is
   `flagged-for-review`. In `<tmp2>` they hold that finding plus the
   `fragmentation` one, both on label 22. Each reason reads as A7's ratios.
2. Replay `clean_control_seg.nii.gz` the same way: no findings, verdict
   `pass`.
3. Read `docs/aide/rules.generated.md`: one `fused_label` row, its question,
   both paths, both defaults, modes column `2`. Read
   `docs/aide/failure_modes.generated.md`: mode 2 lists the `fused_label`
   edge at `synthetic-demonstrable`, and `fuse_adjacent` and
   `fuse_separate` with their new expected sets; modes 6 and 10 no longer
   say no rule reads the spacing.
4. Run `python .aide/scripts/aide.py status` and confirm Stage 30 shows
   step 9's amendment.

No environment profile is needed.

## Dependencies

- Item 206: the `fuse_separate` case and its fixture, read by case id (✅).
- Item 205: re-homed `split` and `stray_contact` to mode 2, which is the
  state of mode 2's other edge and case this item builds on (✅).
- Item 176: the bridged `fuse_adjacent` case (✅).
- Item 200: `bar_conditions`' detector-granular condition 2 that A8 records
  (✅).
- Item 202: the rule table step 8 regenerates (✅).

**Downstream:**

- Item 208 adds mode 3's own detector. It does not touch mode 2's edges, so
  mode 2's condition 4 subjects stay as A8 records.
- Item 203 re-measures `bar_conditions(2)` for its decision brief after
  items 205–208.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** a spacing rule for modes 6 and 10. A missed vertebra with
  the labels renumbered (mode 6's `remove_level_relabel`) and a skipped
  label on a segmented vertebra (mode 10) both widen one spacing at normal
  size. `fused_label` reads the same path but requires a doubled size, so
  it is silent on both by design. Their own rule stays with a later
  per-mode queue (roadmap Stage 33, scope decisions).
- **Left open:** adjacency by ascending integer label. `spacings_mm[]` is
  computed in that order, so the rule uses it too. For TPTBox labels whose
  integers are not anatomical (T13 = 28, L6 = 25; item 198) the adjacency is
  wrong, as it already is for every Stage 3 spacing feature. Neither corpus
  holds such a map with a fused label.
- **Left open:** `feature_docs.STATUS_OVERRIDES["stage3.spacing_consistency.spacings_mm[]"]`
  keeps its `retune` status and its rationale that no rule reads the path.
  The catalogue's dispositions are Stage 19's record and are re-taxonomised
  by Stage 27; changing one here would move `golden_evidence` and every
  status count for a wording fix.
