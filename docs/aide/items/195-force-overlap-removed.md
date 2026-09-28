<!-- aide-template: item 2 -->
# Item 195 — `force_overlap` removed

> **Created:** 2026-09-28 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-025.md`](../queue/queue-025.md) · Item 195
> **Objectives:** G2, G7
> **Suggested branch:** `aide/195-force-overlap-removed`

---

## Description

This item implements roadmap Stage 33 D2's `force_overlap` bullet. The
maintainer decided on 2026-09-25 to remove the case rather than leave it
parked (queue-025, superseding the 2026-09-24 park recorded in `progress.md`).
The reason is Stage 33's second acceptance criterion: no committed corpus case
may be attributed to a mode its label map does not express. Its sources are
the `gap` entry in `docs/aide/insights.md` dated 2026-09-22 (queue-022 review,
already routed here) and the `knowledge` entry dated 2026-09-23 (item 173).

**Why.** A single-channel integer label map cannot hold an overlap, because
each voxel carries exactly one label. The committed `force_overlap` fixture is
a label map with label 20 shifted toward label 21. Its overlap exists only in
a two-channel record that `synth.regression._recon_overlap_mask_stack`
rebuilds (`detection="reconstructed_record"`). So the fixture does not express
mode 15 (overlapping segments), the mode it is attributed to.

**The decision the queue left to this spec (A1): the `overlap` rule stays**,
as a rule declared to need multi-channel input. The fixture goes. The roadmap
allows either this or removing both. The rule stays because:

- it is correct: it reads `overlaps[].overlap_voxels`, which the pipeline
  extracts for every case, and that value is 0 on single-channel input;
- mode 15 keeps its one `IntendedRule` edge at rung
  `structurally-unobservable`, so the derived mode-rung counts and the
  12-rule registry do not move;
- the rule-exercise direction derives the reason `structurally-unobservable`
  for it from that edge, with no authored entry needed (measured).

**What this item changes.**

- The `force_overlap` operator, its corpus case and fixture, its severity
  ladder, margin, coupling and ladder home, and mode 15's corpus attribution
  are removed.
- The operator-specific reconstruction is also removed: the
  `overlap_mask_stack` technique and `LadderSpec.overlap_reconstruction`
  field. Nothing else uses them (A4).
- `score_harness` stops scoring a metric that no ladder designates (A2).
  Without this change, every ladder's margin reads 0.0 and the harness fails
  (measured).
- Mode 15 gains the candidate feature `eval.per_mode.overlapping_voxel_count`
  (`hypothesised`). This keeps the metric's home derivable now that no ladder
  names the metric (A3).
- Mode 15's mechanism and the rule's evidence are rewritten to state the
  multi-channel requirement.
- The corpus and every generated artifact are regenerated. The Stage 30 and
  Stage 20 count clauses are amended. The test pins listed under Testing
  Strategy are reconciled.

**Not in scope.**

- The `overlap` rule's `evaluate`, threshold, detector and
  `default_config.yaml` entry do not change. Nor do `features/overlap.py`,
  `feature_report.overlap_to_dict` or the pipeline's `overlaps` block.
- The metric `overlapping_voxel_count` stays in `eval.per_mode`, with home
  mode 15.
- The generic `reconstructed_record` dispatch stays, with the
  `monotonic_true_spatial_order` technique that no case has used since item
  132 (Left open).
- `RENAMED_CASE_IDS` keeps its `mode8_force_overlap` → `force_overlap` pair
  (A5).
- Frozen dated records are not edited: `docs/corpus-s-axis-correction.md`, the
  signed rows of `docs/aide/golden-decision-table.md`, and history lines in
  `progress.md` and `roadmap.md`.
- No multi-channel input path.

## Acceptance Criteria

- [ ] **AC1: no manifest case is `force_overlap`.** Neither the `case_id`
  values nor the `perturbation` values of `tests/corpus/manifest.json`
  contain `"force_overlap"`.
- [ ] **AC2: the operator registry has no `force_overlap`.**
  `"force_overlap"` is not in `segfacet.synth.perturbation.perturbation_names()`.
- [ ] **AC3: the ladder registry has no `force_overlap`.** `"force_overlap"`
  is not a key of `segfacet.eval.severity_ladder.SEVERITY_LADDERS`.
- [ ] **AC4: margins are recorded for exactly the registered ladders.**
  `set(RECORDED_MARGINS) == set(SEVERITY_LADDERS)`.
- [ ] **AC5: every recorded coupling names a registered ladder.** Every
  `KNOWN_CROSS_MODE_COUPLINGS` entry's `ladder_operator` is a key of
  `SEVERITY_LADDERS`.
- [ ] **AC6: the severity harness passes.**
  `score_harness(run_severity_harness()).passed is True`.
- [ ] **AC7: responses are scored only for the laddered metrics.** For every
  verdict in `score_harness(run_severity_harness()).per_ladder`,
  `set(verdict.responses)` equals
  `{spec.designated_metric for spec in SEVERITY_LADDERS.values()}`.
- [ ] **AC8: mode 15 carries no corpus case.**
  `failure_modes.SPECIFICATION[15].corpus_cases == ()`.
- [ ] **AC9: the rule-exercise report records `overlap` with a derived
  reason.** In `traceability.build_matrix().exercise.rules`, the `overlap`
  record has `state == "unexercised"`,
  `reason == failure_modes.derive_mode_rung(SPECIFICATION[15])` and
  `reason_modes == (15,)`.
- [ ] **AC10: the `overlap` rule's declaration says it needs multi-channel
  input.** Some element of `OverlapRule.mode_declaration.evidence` contains
  the substring `multi-channel`.
- [ ] **AC11: mode 15's mechanism says the same.**
  `SPECIFICATION[15].mechanism` contains the substring `multi-channel`.
- [ ] **AC12: every committed geometric fixture is referenced by the
  manifest.** The set of file names in `tests/corpus/fixtures/` equals the set
  of basenames of every case's `seg_fixture` and `scan_fixture` in
  `tests/corpus/manifest.json`.

Why each is written:

- AC1–AC3 are the queue line's first *Testable* sentence, one registry each.
  Each fails on the pre-item tree.
- AC4 and AC5 guard a partial removal. `score_harness` reads
  `RECORDED_MARGINS.get(op)` only for ladders that are present, so a
  leftover margin or coupling for a removed ladder fails nothing else. Both
  hold on the pre-item tree, and both fail if the ladder goes and its ratchet
  entries stay.
- AC6 and AC7 are the harness half of the removal. Measured on the prototype:
  with the ladder gone and `score_harness` unchanged, `overlapping_voxel_count`
  has no owning ladder, its response is `inf` on every ladder, and all seven
  margins read 0.0 (`passed=False`). AC7 fixes which metrics are scored.
- AC8 is "its mode-15 corpus attribution" removed.
- AC9 is the queue line's "the exercise report ... agree[s] with the reduced
  case set", for the one rule whose record moves. The ratchet half is
  `tests/test_163_specificity_ratchet.py`, which is derived from both
  manifests and needs no edit.
- AC10 and AC11 are the roadmap's "declared to need multi-channel input", on
  the rule and on the specification entry. Each is a claim about wording, so
  each is checked against the wording.
- AC12 guards the orphan fixture. `write_corpus` writes and never deletes, so
  a stale `force_overlap_seg.nii.gz` survives regeneration (measured). The
  existing `tests/test_040_synthetic_corpus.py::test_ac10_every_referenced_fixture_file_exists`
  checks only the other direction.
- The queue line's "Both corpora regenerate byte-identically" is already
  asserted by
  `tests/test_040_synthetic_corpus.py` (AC16) and
  `tests/test_116_ras_native_corpus.py` (AC11). Both are fresh-vs-committed,
  so no new criterion repeats them.

None of these closes a Stage 33 acceptance criterion. Criterion 2 is checked
across every case by D6's stage validation.

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`, engine
2.1.0.

**How the numbers here were measured.**

- Every value was measured on 2026-09-28 on a scratch copy of this branch's
  tree (`git archive HEAD`), run with `.venv/bin/python` and `PYTHONPATH`
  pointing at the copy's `src/`. The import was checked to resolve to the
  copy, per the CLAUDE.md gotcha on the editable install.
- The Implementation Steps below were applied to the copy.
- The corpus, intensity corpus, three document pairs, golden evidence and
  corpus sheet were regenerated in the copy and diffed against this branch.
- "Before" values come from the working tree.
- The builder re-measures each value on the real change.

- **A1 (defensible default: the `overlap` rule stays, declared multi-channel).**
  - Measured with the case removed and the rule kept:
    - `rule_declaration_conflicts()`, `specification_conflicts()` and
      `path_classification_conflicts()` stay `()`.
    - The exercise record for `overlap` becomes `unexercised`, with reason
      `structurally-unobservable` and reason_modes `(15,)`, and
      `rule_exercise` stays complete with no holes. `_build_exercise` derives
      this from the edge.
    - The rule count stays 12.
  - Removing the rule instead would move the rule-count and rule-id pins
    item 187 paid once. It would also empty the `structurally-unobservable`
    rung, which Stage 30 criterion 3 attests. The overlap rule's first
    evidence element becomes `"analytic"`: no committed case designates it
    any more.
- **A2 (defensible default: `score_harness` scores only laddered metrics).**
  - The change: `metric_names` becomes the `PER_MODE_METRIC_SPECS` keys that
    some `SEVERITY_LADDERS` entry designates. So a metric no ladder designates
    gets no response, is not in the margin's foreign set, and is not reported.
    The set is read from the module registry, not from the harness passed in,
    so a partial harness keeps today's behaviour (a registered ladder's metric
    whose ladder is absent still reads `inf`).
  - Why not keep reporting `inf` for the unowned metric: measured, that
    breaks `tests/test_154_ladder_remeasurement.py`.
    - `test_ac8_coupling_set_is_what_is_measured` would read
      `(op, "overlapping_voxel_count")` as a coupling on all seven ladders.
    - `test_ac12_excluding_same_home_metrics_changes_no_margin` would read an
      alternate margin of 0.0 against `inf`.
  - With the change (measured):
    - `passed=True` over 7 ladders, each with 7 responses.
    - Margins: displace, fragment, relabel_swap, remove_level and
      sequence_break `inf`; inject_islands 118.49074; crop_at_border 0.32530
      (coupled). These equal `RECORDED_MARGINS`.
    - The measured coupling set is
      `{("crop_at_border", "unanchored_foreground_fraction")}`, response
      3.0741, against the recorded 3.075.
    - test_154's AC8 and AC12 stay green unedited.
  - Pre-item, `overlapping_voxel_count`'s response on each of the other seven
    ladders was 0.0, so no margin moves.
- **A3 (defensible default: the metric's home stays mode 15, via rule (a)).**
  - `per_mode._METRIC_HOMES["overlapping_voxel_count"] == (15, None)`
    stays.
  - `tests/test_153_eval_harness_rekey.py`'s `_derived_home` derives it by
    rule (a), a mode citing `eval.per_mode.<metric>`, else rule (b), the
    metric's ladder's corpus case. Rule (b) raises a `KeyError` once the
    ladder is gone.
  - Adding `CandidateFeature(path="eval.per_mode.overlapping_voxel_count",
    role="hypothesised")` to mode 15 resolves rule (a) to 15. Modes 1, 6 and 8
    already cite their metrics this way.
  - Measured: `specification_conflicts()` stays `()`, and test_153's AC13
    citation check resolves to home 15. The catalogue has no `eval.per_mode.*`
    paths, so it is unaffected. `failure_modes.generated.md` gains one
    candidate-feature line.
- **A4 (defensible default: the operator-specific reconstruction goes).**
  - Removed:
    - `_recon_overlap_mask_stack` and its `RECONSTRUCTIONS` entry;
    - `LadderSpec.overlap_reconstruction`, with its eight `=None` keyword
      arguments, its `to_dict` key and `_measure`'s branch;
    - the imports that only those used.
  - Each rebuilds `force_overlap`'s two-mask stack from the operator's
    parameters, so each is dead once the operator goes.
  - The generic `reconstructed_record` dispatch stays (`reconstructed_findings`,
    `designated_findings`, `failure_modes._measured_firing_geometric`) with the
    `monotonic_true_spatial_order` technique, as item 132 left it.
  - The three test_041 and two test_042 tests parametrised over
    reconstructed cases would collect zero cases and skip, so they are
    deleted. test_041's `test_ac12_unknown_reconstruction_technique_raises_value_error`
    still exercises the dispatch.
  - Measured: `LadderSpec.to_dict()` keys become `condition, degenerate,
    designated_metric, failure_mode, failure_mode_name, operator, rationale,
    rungs, severity_kind, severity_parameter`. No test pins
    `overlap_reconstruction` except test_100's two constructor calls.
- **A5 (defensible default: `RENAMED_CASE_IDS` keeps the `mode8_force_overlap`
  pair).** It is a frozen history record: "never extended by later renames",
  and "nothing in `src/` reads it at runtime". Three consumers rebuild retired
  paths through it:
  - `test_105`'s AC9 (nine retired golden rows);
  - `test_126`'s AC4 and AC18 (retired paths and row digests);
  - `test_143`'s AC16 (the frozen `docs/corpus-s-axis-correction.md` path
    set, built at import).

  Its two live-resolution checks in `test_157` (AC3, A8) exempt ids of
  removed cases instead, and assert that each such id resolves to **zero**
  cases.
- **A6 (defensible default: `golden-decision-table.md` gets one appended
  execution-log paragraph, and no signed row is edited).**
  - Section 1's `keep` row for `tests/corpus/fixtures/force_overlap_seg.nii.gz`
    (line 181) and its Divergences bullet (lines 294–295) are the
    maintainer's signed disposition, from item 105 (2026-07-28).
  - The table's own "Retirement execution log" states that signed rows are
    never rewritten there; executions are recorded as dated lines. The
    maintainer's 2026-09-25 decision is what removes the fixture, so this
    item records the execution and makes no new judgement. No human gate is
    raised.
  - `tests/test_105_golden_decision_table.py::test_ac3_section1_fixture_set_equals_filesystem_walk_both_directions`
    accepts a documented-but-absent path only when the log names it. That is
    the mechanism item 126 used.
  - Measured: with the fixture deleted and no log line, that test reports the
    path.
- **A7 (defensible default: the 094 loader snapshot drops the removed
  fixture's key).**
  - `tests/test_094_tptbox_image_layer.py::test_ac3_fixture_loads_byte_identically_to_pre_migration_snapshot`
    loads every key's file.
  - Removing key `corpus/fixtures/force_overlap_seg.nii.gz|seg` from
    `tests/corpus/094_pre_migration_snapshot.json` round-trips exactly under
    `json.dumps(obj, indent=2, sort_keys=True) + "\n"`: a pure 42-line
    deletion, keys 18 → 17.
  - The file is not re-captured: every other entry's digest is unchanged,
    because no other fixture moves.
- **A8 (measured: what moves).**
  - **Corpus.**
    - The regenerated `tests/corpus/manifest.json` equals the committed one
      minus the `force_overlap` entry: 13 cases, a pure 41-line deletion.
    - Every other fixture is byte-identical.
    - The intensity corpus regenerates byte-identical.
    - `force_overlap_seg.nii.gz` is left on disk by `write_corpus` and needs
      `git rm`.
    - `.gitattributes` needs no change: fixtures are pinned by the glob
      `tests/corpus/fixtures/*.nii.gz binary`.
  - **Registries.**
    - Operators: 14 → 13.
    - Rules: 12, unchanged.
    - `SEVERITY_LADDERS`: 8 → 7.
    - `RECORDED_MARGINS`: 8 → 7 keys.
    - `KNOWN_CROSS_MODE_COUPLINGS`: 2 → 1.
    - `RECONSTRUCTIONS`: `{"monotonic_true_spatial_order"}`.
  - **Derived state.**
    - Mode 15's derived status: `validated` → `implemented`. It is still
      declared by `overlap`, but has no corpus case.
    - Status counts: validated 6 → 5, implemented 3 → 4, specified 2,
      proposed 5.
    - Validated split: pipeline-detected 5, reconstructed-only 1 → 0.
    - Mode rung counts are unchanged: synthetic-demonstrable 5,
      needs-real-data 3, structurally-unobservable 1, none 7.
    - 13 edges, unchanged: 5 / 7 / 1.
  - **Conformance and bars.**
    - Conformance: 18 → 17 cases (13 geometric, 4 intensity), conformant,
      with no disagreement.
    - `bar_conditions` for modes 3 and 4 are unchanged.
  - **Eval cohort** (test_057's and test_120's corpus cohort).
    - Overall sensitivity 9/10 → 1.0 (9/9).
    - Per-mode entries with cases:
      - (1, 1, 1.0)
      - (3, 2, 1.0)
      - (4, 1, 1.0)
      - (6, 1, 1.0)
      - (9, 2, 1.0)
      - `displaced_vertebra` (1, 1.0)
      - `fov_truncation` (1, 1.0)
    - The mode-15 entry has `n_cases` 0 and sensitivity `None`.
    - Sum of `n_cases`: 10 → 9.
    - Outcomes: 9 true positive, 4 true negative.
  - **Catalogue.**
    - Still 145 entries.
    - `overlaps[].overlap_voxels` loses `rule_mode_map` from its
      `mode_evidence`. Bucket `("per_mode_metric", "rule_mode_map",
      "rule_declaration")` goes 3 → 2, and a new bucket
      `("per_mode_metric", "rule_declaration")` holds 1.
    - Mode 1, 2 and 16 entry counts stay 5, 4 and 2.
    - `_scan_synth_rule_mode_map()` loses `"overlap"`: `{fragmentation: (1,
      4), mislabel: (9,), coverage: (6,), sequence: (9,), neighbour_contact:
      (3,), bounds: (3,)}`.
  - **Test inventory.** Non-`.py` files under `tests/`: 26 → 25.
  - **Documents.**
    - These move: `failure_modes.generated.{json,md}`,
      `traceability_matrix.generated.{json,md}`,
      `feature_catalogue.generated.json`, `golden_evidence.generated.json`
      (its `force_overlap` entry drops) and `docs/aide/corpus_sheet.png`
      (80825 → 75350 bytes).
    - `feature_catalogue.generated.md` regenerates byte-identical.
  - **Plain pipeline.** Measured over the 13 remaining geometric cases:
    - every `extract_feature_record(...)["overlaps"] == []`;
    - `overlap` fires on none of them through `pipeline_findings`.
- **A9 (mechanism constraints, checked on the prototype).**
  - Mode 15's mechanism must contain each of:
    - `single-channel` and `label map` (test_138 AC13, test_151 AC15);
    - `voxel` (test_151 AC15, test_145 AC12 as reconciled);
    - `exactly one` or `one label` (test_145 AC12 as reconciled);
    - the whole word `overlap` (test_138 AC31, test_147 AC9).
  - It may name `overlaps[].overlap_voxels`, which `overlap` consumes
    (test_138 AC31 real check (1)).
  - It must not use the `(measured: findings == [...])` idiom, and must name
    no case id.
  - The draft in Implementation Step 5 meets all of these.
  - Mode 3's mechanism loses its "including force_overlap (mode 15)..." clause
    and keeps every token its checks need.
  - No authored string in `src/` may equal a rung name or a mode
    `name`/`short_name` exactly (test_147 AC1/AC2).
- **A10: no human gate, and no environment-gated capability.** The
  maintainer's 2026-09-25 decision is the authority for the removal. A6
  records the one signed document this item touches, and how.

## Implementation Steps

1. **Remove the operator** from `src/segfacet/synth/coverage_border_overlap.py`:
   - Delete the `ForceOverlapPerturbation` class and its section banner.
   - Delete `_choose_adjacent_pair` and `_label_bbox`, which only that class
     used, and drop `si_axis` from the `segfacet.synth.axes` import.
   - Delete its `__all__` entry, and its bullet in the module docstring.
   - Line 1–2 of the docstring becomes "Coverage & border perturbations:
     remove_level, remove_level_relabel, crop_at_border, crop_fov (item 038;
     `force_overlap` removed by item 195, 2026-09-28)". Its count sentence
     names the four operators left.
   - In `src/segfacet/synth/__init__.py`, delete the `ForceOverlapPerturbation`
     import and its `__all__` entry.
2. **Remove the corpus case** from `src/segfacet/synth/corpus.py`:
   - Delete the `force_overlap` `_RecipeEntry`.
   - The module docstring's "fourteen canonical cases" becomes "thirteen".
     Its operator list drops `force_overlap`. The paragraph starting "One of
     the fourteen cases (mode 15 -- `force_overlap`)" is replaced by a dated
     item-195 sentence: no committed case is `reconstructed_record` any more,
     since the overlap case was removed on 2026-09-28 because a
     single-channel label map cannot express it.
   - The `#: The fourteen canonical cases` comment becomes thirteen.
   - `RENAMED_CASE_IDS` and its docstring list stay (A5).
3. **Remove the operator-specific reconstruction** (A4):
   - In `src/segfacet/synth/regression.py`, delete `_recon_overlap_mask_stack`
     and its `RECONSTRUCTIONS` entry. Delete the four imports only it used:
     `detect_overlaps`, `overlap_to_dict`, `OverlapRule` and
     `build_clean_spine`.
   - The module docstring's `reconstructed_record` bullet now says no
     committed case uses the path. It is kept for a future reconstructed
     case, and `MislabelRule`'s technique is the one registered.
   - In `src/segfacet/catalogue.py`, reword the comment at lines 462–467 so it
     no longer names `_recon_overlap_mask_stack`. The catalogue's own
     synthetic overlap driver is unchanged.
4. **Remove the ladder** from `src/segfacet/eval/severity_ladder.py`:
   - Delete `_force_overlap_ladder`, its `SEVERITY_LADDERS` entry, its
     `_LADDER_HOMES` entry, `RECORDED_MARGINS["force_overlap"]` and the
     `force_overlap` `CrossModeCoupling`.
   - Delete the `LadderSpec.overlap_reconstruction` field, its docstring
     entry, its `to_dict` key, every `overlap_reconstruction=None` keyword and
     `_measure`'s overlap branch. Delete the now-unused `overlap_to_dict` and
     `detect_overlaps` imports.
   - In `score_harness`, replace `metric_names = list(PER_MODE_METRIC_SPECS)`
     with the laddered subset (A2):
     ```python
     laddered = {spec.designated_metric for spec in SEVERITY_LADDERS.values()}
     metric_names = [f for f in PER_MODE_METRIC_SPECS if f in laddered]
     ```
     Rewrite the comment above `owning_operator`: coverage is total over the
     scored (laddered) metrics. `overlapping_voxel_count` has no ladder since
     item 195 and is not scored.
   - Prose:
     - The module docstring's "eight ladders" table loses its
       `force_overlap` row and says seven, adding one dated sentence that
       `overlapping_voxel_count` has no ladder and is not scored (item 195).
     - The `_BASE_PARAMS` comment drops its `force_overlap` AC19 clause.
     - The `KNOWN_CROSS_MODE_COUPLINGS` preamble drops its `force_overlap`
       half: "Two measured couplings" becomes "One measured coupling".
     - `_fuse_ladder`'s rationale "Excluded from the eight-ladder cross-mode
       matrix so that matrix stays a square 8x8." becomes "Excluded from the
       primary ladders' cross-mode matrix." No test pins either string
       (checked in test_100, test_102, test_153, test_154).
     - `run_severity_harness`'s docstring "the eight ladders" becomes "the
       primary ladders".
   - Re-measure the harness. If any margin or coupling response differs from
     A2, hand back.
5. **The specification**, in `src/segfacet/failure_modes.py`:
   - `_MODE_15.corpus_cases=()`.
   - Append `CandidateFeature(path="eval.per_mode.overlapping_voxel_count",
     role="hypothesised")` to `_MODE_15.candidate_features` (A3).
   - `_MODE_15.mechanism` becomes exactly:
     > A single-channel integer label map holds exactly one label per voxel,
     > so overlaps[].overlap_voxels can be non-zero only on a multi-channel
     > input, which no FACET input path supplies: the pipeline builds its
     > mask stack from the one label map. The overlap rule reads that path, is
     > correct and fully wired, and is declared to need multi-channel input.
     > No committed corpus case expresses this mode, because a single-channel
     > fixture cannot hold an overlap (item 195, 2026-09-28).
   - In `_MODE_3.mechanism`, "-- including force_overlap (mode 15), whose
     contacting components are each label's largest, and fuse_adjacent" becomes
     "-- including fuse_adjacent".
   - `_MODE_15.status` stays `"specified"`. It derives `"implemented"`.
   - Append a dated item-195 paragraph to the module docstring's history,
     after item 194's. Cite `failure_modes.SPECIFICATION`, never vision.md
     §6: `tests/test_161_stage31_validation.py` rejects `§6 mode N` lines
     under `src/segfacet/`.
6. **The rule's declaration**, in `src/segfacet/heuristics/overlap.py`:
   - `mode_declaration.evidence` becomes:
     ```python
     (
         "analytic",
         "needs multi-channel input: overlaps[] is non-empty only when two "
         "labels claim one voxel, which a single-channel integer label map "
         "cannot express, so the pipeline's one-hot mask stack yields no "
         "overlap on any input FACET accepts today. Mode 15 (overlapping "
         "segments) of the catalogue signed off at item 150; the per-edge "
         "rung in segfacet.failure_modes.SPECIFICATION[15] is "
         "structurally-unobservable, and no committed corpus case designates "
         "this rule (item 195, 2026-09-28).",
     )
     ```
   - Reword the comment above `mode_declaration`. It no longer cites
     `ForceOverlapPerturbation`; it says the rule is kept, declared
     multi-channel (item 195).
   - `modes`, `consumed_paths`, `detectors` and `evaluate` are unchanged.
   - In `src/segfacet/heuristics/rule.py`, the `RuleModeDeclaration` docstring
     example becomes
     `modes=(3,), evidence=("corpus-manifest", "tests/corpus/manifest.json's split ...")`.
7. **Comments and prose that the removal makes false:**
   - `src/segfacet/traceability.py`: the `_PIPELINE_DETECTIONS` comment
     (lines 467–471) no longer names "mode 15's overlap case". It says no
     committed case is `reconstructed_record` since item 195.
   - `src/segfacet/synth/axes.py`: the docstring's operator list drops
     `ForceOverlapPerturbation`.
   - `src/segfacet/eval/per_mode_cohort.py`: "each proven monotone in its own
     severity ladder (item 100)" becomes "each laddered metric proven
     monotone in its own severity ladder (item 100;
     `overlapping_voxel_count` has had no ladder since item 195)".
   - `src/segfacet/eval/__init__.py`: the harness sentence "runs item 099's
     eight metrics over a graded synthetic-severity stimulus per mode" says
     "every laddered metric" instead.
   - `README.md` line 27: drop "overlap, " from the Perturb bullet.
8. **Regenerate**, in this order:
   1. `.venv/bin/python -m segfacet.synth.corpus`, then
      `git rm tests/corpus/fixtures/force_overlap_seg.nii.gz`.
   2. `.venv/bin/python -m segfacet.synth.intensity` must leave
      `tests/corpus/intensity/` byte-identical. Hand back if it does not.
   3. `.venv/bin/python -m segfacet.failure_modes`,
      `.venv/bin/python -m segfacet.traceability` and
      `.venv/bin/python -m segfacet.catalogue`. Run each twice with
      `--json <tmp> --md <tmp>`, byte-compare, then once with no flags.
   4. `.venv/bin/python -m segfacet.golden_evidence`.
   5. `.venv/bin/python -m segfacet.synth.corpus_sheet`.

   The expected diffs are A8's. `feature_catalogue.generated.md` must come
   out byte-identical.
9. **The 094 loader snapshot** (A7): load
   `tests/corpus/094_pre_migration_snapshot.json`, pop
   `"corpus/fixtures/force_overlap_seg.nii.gz|seg"`, and write
   `json.dumps(obj, indent=2, sort_keys=True) + "\n"` with `write_bytes`. The
   diff must be a pure deletion.
10. **`docs/aide/golden-decision-table.md`** (A6): append at the end of the
    "## Retirement execution log" section, after its last paragraph, and
    write LF only:

    > Item 195 records one removal outside that shared disposition. The
    > signed `keep` row for the fixture below is not rewritten. The
    > maintainer's 2026-09-25 decision to remove the `force_overlap` corpus
    > case (a single-channel label map cannot express mode 15; roadmap
    > Stage 33 D2) took its fixture with it.
    >
    > - `tests/corpus/fixtures/force_overlap_seg.nii.gz` removed <ISO date of
    >   the commit>, item 195.

    Edit no other line of the file.
11. **Amend the attested count clauses** with
    `python .aide/scripts/aide.py progress amend`. Re-measure every number
    live first; the values below are A8's. Use the run's ISO date where
    2026-09-28 appears.
    - `amend 30 --criterion 1`:
      `Item 195 (2026-09-28): force_overlap removed; mode 15 keeps the overlap rule's declaration and carries no corpus case, so it derives implemented. Re-measured live: derived status counts over 16 modes: validated 5, implemented 4, specified 2, proposed 5; validated through a pipeline-detected case 5, through a reconstructed record only 0.`
    - `amend 20 --criterion 5`:
      `Item 195 (2026-09-28): force_overlap removed; mode 15 derives implemented. Re-measured live: derived status counts over 16 modes: validated 5, implemented 4, specified 2, proposed 5. derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7.`
    - `amend 30 --criterion 3`, a note with no count clause:
      `Item 195 (2026-09-28): force_overlap removed. Mode 15 keeps its overlap edge at structurally-unobservable and carries no corpus case; the AC15/AC16 force_overlap evidence above is history. test_151's AC16 now asserts that mode 15 carries no corpus case and that no committed geometric case yields an overlap through the pipeline.`

    How the tests read these:
    - `test_151`'s AC35 reads the **last** status-counts and validated-split
      matches in `## Stage 30`.
    - `test_169`'s AC6 and AC7 read the last matches in `## Stage 20`.
    - The criterion-3 note must not contain the text `derived mode rung
      counts`, so that item 194's rung clause stays the last match.
12. Leave `tests/` alone, apart from the `git rm` and the snapshot edit
    above. The test-writer owns every test edit listed under Testing
    Strategy.
13. Run `python .aide/scripts/aide.py scope 195` and
    `python .aide/scripts/aide.py check`. Both must report no error.

## Authorised paths

**May change:**

- `src/segfacet/synth/coverage_border_overlap.py` — operator and its helpers removed (step 1).
- `src/segfacet/synth/__init__.py` — re-export removed (step 1).
- `src/segfacet/synth/corpus.py` — recipe entry and docstring (step 2).
- `src/segfacet/synth/regression.py` — overlap reconstruction removed (step 3).
- `src/segfacet/catalogue.py` — one comment (step 3).
- `src/segfacet/eval/severity_ladder.py` — ladder, ratchet entries, field, score_harness, prose (step 4).
- `src/segfacet/failure_modes.py` — mode 15 cases, candidate feature, mechanism; mode 3 clause; docstring (step 5).
- `src/segfacet/heuristics/overlap.py` — evidence and comment (step 6).
- `src/segfacet/heuristics/rule.py` — docstring example (step 6).
- `src/segfacet/traceability.py` — one comment (step 7).
- `src/segfacet/synth/axes.py` — docstring operator list (step 7).
- `src/segfacet/eval/per_mode_cohort.py` — docstring clause (step 7).
- `src/segfacet/eval/__init__.py` — docstring clause (step 7).
- `README.md` — Perturb bullet (step 7).
- `tests/corpus/manifest.json` — regenerated (step 8).
- `tests/corpus/fixtures/force_overlap_seg.nii.gz` — deleted with `git rm` (step 8).
- `tests/corpus/094_pre_migration_snapshot.json` — one key removed (step 9).
- `docs/aide/failure_modes.generated.json` — regenerated (step 8).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 8).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 8).
- `docs/aide/golden_evidence.generated.json` — regenerated (step 8).
- `docs/aide/corpus_sheet.png` — regenerated (step 8).
- `docs/aide/golden-decision-table.md` — one appended execution-log paragraph (step 10).
- `tests/test_195_force_overlap_removed.py` — **new**: this item's test module.
- `tests/test_038_coverage_border_overlap_perturbations.py` — force_overlap operator tests removed.
- `tests/test_040_synthetic_corpus.py` — reconstruction sets, AC9 removed.
- `tests/test_041_regression_suite.py` — reconstructed-case tests removed, technique set.
- `tests/test_042_golden_determinism.py` — reconstructed-case tests removed.
- `tests/test_057_acceptance_stage7.py` — reconstructed mode test removed, sensitivity 1.0.
- `tests/test_098_stray_components.py` — two frozen-table keys.
- `tests/test_099_per_mode_metrics.py` — mode-8 record helper, AC14, isolation matrix.
- `tests/test_100_severity_ladder.py` — seven ladders, response mirror, AC19 removed.
- `tests/test_102_stage18_validation.py` — seven ladders, AC17.
- `tests/test_103_feature_catalogue.py` — `_RULE_MODE_MAP`.
- `tests/test_105_golden_decision_table.py` — inventory 25, live golden ids.
- `tests/test_120_leave_one_out_offset.py` — AC21 technique set, AC24 cohort.
- `tests/test_121_tangent_orientation.py` — exception set.
- `tests/test_126_golden_retirement.py` — live case ids, `_RE_POINTED`.
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — frozen-table key.
- `tests/test_131_tangent_direction_normalisation.py` — four frozen-table keys.
- `tests/test_132_monotonicity_against_traversal_order.py` — frozen key, AC20–AC22.
- `tests/test_134_decision_table_evidence_companion.py` — inventory removal set.
- `tests/test_137_mode_less_rule_disposition.py` — bucket table.
- `tests/test_138_traceability_matrix.py` — AC14, AC20 witness, typo adversarial.
- `tests/test_143_s_axis_correction.py` — frozen-table key, snapshot length.
- `tests/test_144_failure_mode_specification.py` — overlap-case adversarial removed.
- `tests/test_145_eight_hypothesised_modes.py` — mode 15 status, AC11, AC12.
- `tests/test_147_specification_is_the_record.py` — mode 15 status.
- `tests/test_148_per_path_mode_attribution.py` — AC16 overlap row.
- `tests/test_149_conformance_report.py` — AC13 counts, AC18 overlap mode.
- `tests/test_151_stage30_validation.py` — AC8, AC9, AC16.
- `tests/test_153_eval_harness_rekey.py` — operators, AC18, AC24.
- `tests/test_157_case_id_rename.py` — AC3 and A8 exemptions.
- `tests/test_167_mode_3_detector.py` — force_overlap silence test removed.

**The reconciliation fence.** Every edit to an existing test is one of these:

- a moved literal;
- a key or row dropped for the removed case, operator or ladder;
- a premise re-pointed to a subject that still carries it, with the premise
  asserted;
- a test deleted because its subject is the removed case, operator, ladder or
  technique;
- a test renamed so its name states what it now checks.

Each edit carries a dated item-195 comment. No test is skipped,
`xfail`-marked or loosened. A red test in a file not listed here is a
hand-back to spec-author.

**Asserts against:**

- `tests/corpus/intensity/manifest.json` — regenerates byte-identical (step 8; test_040/test_116's fresh-vs-committed).
- `docs/aide/feature_catalogue.generated.md` — regenerates byte-identical (A8).
- `docs/corpus-s-axis-correction.md` — frozen record test_143's AC16 reads through `RENAMED_CASE_IDS` (A5).
- `tests/test_094_tptbox_image_layer.py` — stays green unedited against the edited snapshot (A7).
- `tests/test_154_ladder_remeasurement.py` — AC8/AC12 stay green unedited (A2).
- `tests/test_163_specificity_ratchet.py` — derived from both manifests; stays green unedited.
- `tests/test_169_stage32_validation.py` — AC6/AC7 go green through step 11, unedited.
- `tests/test_178_corpus_sheet.py` — stale check passes on the regenerated sheet, unedited.
- `tests/test_125_stage28_validation.py` — AC15 follows test_040's reconciled sets, unedited.

## Testing Strategy

The test module is `tests/test_195_force_overlap_removed.py`, with one test
per AC.

- **AC1–AC5** read the live registries and the committed manifest, never a
  literal case list.
- **AC4 and AC5** are written over helpers that take the three tables as
  arguments, so the adversarial cases below can pass planted ones.
- **AC6, AC7 and AC9** share one module-scoped
  `score_harness(run_severity_harness())` result, and one `build_matrix()`
  respectively.
- **AC9** compares `reason` against `failure_modes.derive_mode_rung(...)`,
  never a rung literal (test_147 AC2's single-source rule holds for tests by
  the same discipline).
- **AC12** is written over a helper taking a fixtures directory and a
  manifest dict.

Named adversarial cases, and no others:

- **planted-stale-margin:** `RECORDED_MARGINS` monkeypatched to carry an
  extra `"force_overlap": 1.741` makes AC4's helper report exactly
  `{"force_overlap"}`. It guards a check that compares only the ladder side,
  or reads `SEVERITY_LADDERS` twice.
- **planted-stale-coupling:** a `CrossModeCoupling(ladder_operator="force_overlap", ...)`
  appended to the table makes AC5's helper report exactly `{"force_overlap"}`.
  It guards a check that iterates ladders instead of couplings.
- **second-unowned-metric:** with `SEVERITY_LADDERS` monkeypatched to drop
  `"inject_islands"`, `score_harness(run_severity_harness())` still passes.
  Every verdict carries 6 responses, none of them `rogue_island_count`, and
  the six remaining margins equal those of the unpatched run. Measured: passed
  True, margins inf ×5 and crop_at_border 0.32530. On the pre-item code the
  same patch fails every ladder at margin 0.0. It guards a fix that
  special-cases the name `overlapping_voxel_count` instead of deriving the
  laddered set.
- **planted-orphan-fixture:** a `tmp_path` fixtures directory holding the
  manifest's files plus one extra `orphan_seg.nii.gz` makes AC12's helper
  report exactly `{"orphan_seg.nii.gz"}`. It guards a one-directional
  comparison (referenced ⊆ on disk only).

**Existing tests to reconcile.**

- Three read-only sweeps over `tests/`, `src/`, scripts and `docs/aide/`
  found these, and a fourth sweep over `docs/aide/` confirmed the progress
  clauses. Every literal below was measured on the prototype (A8).
- "Delete" means the test's only subject is the removed case, operator,
  ladder or technique. Line numbers are the pre-item tree's.

- **`tests/test_038_coverage_border_overlap_perturbations.py`:**
  - Drop the `ForceOverlapPerturbation` import. Without that, collection
    fails.
  - Drop the `force_overlap` branch of the AC27 input helper (lines 86–91).
  - Drop its entries in `_EXPLICIT_TARGET_FACTORIES` (113),
    `_UNSPECIFIED_TARGET_FACTORIES` (122) and `_OPERATOR_IDS` (129), and its
    branch in `_designated_rule_fires` (157–162).
  - Delete `test_ac18`–`test_ac23` (the "C. force_overlap" group),
    `test_adv_force_overlap_explicit_target_absent_raises_clear_error`,
    `test_adv_force_overlap_explicit_neighbour_absent_raises_clear_error` and
    `test_adv_force_overlap_anisotropic_spacing_still_yields_shared_voxels`.
  - Update the module docstring's AC list.
- **`tests/test_040_synthetic_corpus.py`:**
  - `_VALID_RECONSTRUCTIONS = {"monotonic_true_spatial_order"}`.
  - `_RECONSTRUCTED_MODES = set()`. `_PIPELINE_ONLY_MODES` stays
    `{0, 1, 2, 3, 4, 6, 9}`.
  - Delete `test_ac9_reconstructed_record_fixtures_hide_mode_from_run_qc`:
    it asserts a non-empty reconstructed set.
- **`tests/test_041_regression_suite.py`:**
  - `test_ac2_every_case_routes_to_exactly_one_handled_path`'s technique set
    becomes `{"monotonic_true_spatial_order"}`.
  - Delete `test_ac7_plain_pipeline_hides_designated_rule_for_reconstructed_cases`,
    `test_ac8_reconstruction_fires_designated_rule_with_expected_labels` and
    `test_adv_reconstructed_case_hidden_rule_matches_reconstruction_fired_rule`.
    Each would collect zero cases.
  - `test_ac12_unknown_reconstruction_technique_raises_value_error` stays.
- **`tests/test_042_golden_determinism.py`:** delete
  `test_ac16_reconstructed_golden_is_pipeline_blind` and
  `test_adv_reconstructed_golden_blindness_is_checked_via_rule_ids_not_empty_findings`.
  Drop `_RECONSTRUCTED_CASES`.
- **`tests/test_057_acceptance_stage7.py`:**
  - Delete `_RECONSTRUCTED_RECORD_MODES` and
    `test_reconstructed_record_modes_are_not_over_claimed_as_caught`.
  - Rename `test_overall_corpus_sensitivity_is_nine_of_ten_not_over_claimed`
    to `test_overall_corpus_sensitivity_is_nine_of_nine`, asserting
    `metrics.sensitivity == pytest.approx(9.0 / 9.0)`. Add a dated line: every
    expected-failure record is now pipeline-detected, 9 of 9.
- **`tests/test_098_stray_components.py`:** drop the `"force_overlap"` keys
  of `_PRE_098_HAND_SET_FRAGMENTATION_FINDINGS` (line 690) and
  `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS` (line 1011). This also fixes
  test_102's AC5 and test_143's AC9.
- **`tests/test_099_per_mode_metrics.py`:**
  - Delete `_mode8_record_with_overlaps`, `_MODE8_RECORD`, `_record_for`'s
    `force_overlap` branch and `test_ac14_mode8_reconstructed_overlaps_is_1950`.
    Without that, collection fails.
  - Re-point `test_ac14_mode8_matches_hand_formula` at `clean_control`'s
    record with `overlaps` set to two entries of `overlap_voxels` 3 and 4.
    Assert `_value(result, 8) == 7.0`, and that the value equals the sum of
    the entries (measured 7.0).
  - `_OWN_CASE` drops `overlapping_voxel_count`.
  - `_EXPECTED_ISOLATION_MATRIX` drops its `overlapping_voxel_count` row and
    the `force_overlap` column of every other row.
  - `_build_actual_matrix` builds rows only for `_OWN_CASE`'s metrics.
  - `test_ac14_mode8_plain_extract_feature_record_is_zero`,
    `..._absent_overlaps_key_is_none` and `..._present_but_empty_list_is_zero`
    stay.
- **`tests/test_100_severity_ladder.py`:**
  - `_LEGACY_TO_OPERATOR` drops key 8. Add `_LADDER_MODES = range(1, 8)`.
  - Every ladder-axis `range(1, 9)` becomes `_LADDER_MODES`: lines 154, 427,
    436, 453, 474, 488, 503, 516, 554, 569, 620, 644, 665, 715 and 860.
  - Every response-axis loop becomes `_LADDER_MODES`, mirroring A2's
    laddered subset: `_margin`'s `f` at 173, and the `f` loops at 623, 647
    and 666.
  - `_spans_table`'s metric loop (156) keeps `range(1, 9)`, because spans of
    values exist for all eight metrics.
  - The value loops at 440, 456 and 464 keep `range(1, 9)`: the metric is
    still computed on every rung, measured 0.0 at every point.
  - `_EXPECTED_SEVERITY_KIND` and `_EXPECTED_SEVERITY_PARAMETER` drop key 8.
    `test_ac11_severity_parameter_matches_the_spec_table`'s parameter list
    (line 558) becomes `[1, 2, 3, 4, 5, 6]`.
  - `test_ac2_key_set_is_exactly_the_eight_operators` becomes
    `..._the_seven_operators`. `test_ac16_recorded_margins_has_all_eight_modes`
    becomes `..._seven_ladders`.
  - Delete `test_ac19_mode8_overlap_depth_three_rung_reproduces_corpus_1950`.
  - `test_ac20_mode8_metric_is_zero_on_every_other_ladder` parametrises over
    `_LADDER_MODES`.
  - Drop `overlap_reconstruction=None` at lines 992 and 1017.
  - Update the module docstring's AC1/AC19/AC20 lines.
- **`tests/test_102_stage18_validation.py`:**
  - `_LADDER_OPERATORS` drops `force_overlap`.
  - `_EXPECTED_RUNG_COUNTS` values become `(5, 5, 5, 3, 4, 4, 2)`.
  - `_EXPECTED_SEVERITY_KINDS` and `_EXPECTED_MARGINS` drop their eighth
    values. The other seven are unchanged (measured).
  - `test_ac17_the_two_shortfall_modes_are_asserted_as_such` drops its `lv8`
    block and is renamed `test_ac17_the_shortfall_ladder_is_asserted_as_such`.
  - `test_ac14_..._for_all_eight_modes` is renamed `..._for_all_seven_ladders`.
- **`tests/test_103_feature_catalogue.py`:** `_RULE_MODE_MAP` drops
  `"overlap": (15,)`. The measured scan is in A8.
- **`tests/test_105_golden_decision_table.py`:**
  - `test_ac3_current_tree_has_30_non_py_fixtures` asserts `== 25`.
  - `test_adv_ac3_empty_header_only_table_fails_with_full_missing_list`
    asserts `len(missing) == 25`.
  - Add `_LIVE_GOLDEN_CASE_IDS = tuple(c for c in _GOLDEN_CASE_IDS if c != "force_overlap")`.
    `test_ac7_golden_row_evidence_is_measured_not_transcribed` parametrises
    over it.
  - `_GOLDEN_CASE_IDS` and `_RETIRED_GOLDEN_FIXTURE_IDS` keep nine ids for
    AC9.
  - AC3's both-directions check goes green through step 10.
- **`tests/test_120_leave_one_out_offset.py`:**
  - `test_ac21_leave_one_out_reconstruction_retired`:
    `set(regression_mod.RECONSTRUCTIONS) == {"monotonic_true_spatial_order"}`.
  - `test_ac24_corpus_pipeline_detection_is_nine_of_ten` is renamed
    `test_ac24_corpus_pipeline_detection_is_nine_of_nine`, with these
    changes:
    - `sensitivity == pytest.approx(1.0)`;
    - `expected_sensitivity` drops `15: 0.0`;
    - `sum(m.n_cases ...) == 9`;
    - `mode_six.n_cases == 1` stays.
- **`tests/test_121_tangent_orientation.py`:** the exception set at line 446
  drops `"force_overlap"`.
- **`tests/test_126_golden_retirement.py`:**
  - Add `_LIVE_CASE_IDS = tuple(c for c in _CASE_IDS if c != "force_overlap")`.
    `test_ac3_fresh_report_validates_against_schema` and
    `test_ac22_documented_2694_evidence_still_verifies_unchanged`
    parametrise over it.
  - `_CASE_IDS` stays nine, for `_RETIRED_PATHS`.
  - `_RE_POINTED` drops the two deleted test_042 rows. The pin becomes
    `len(_RE_POINTED) == 32`, with the message "32 = 22 individually-listed
    re-point rows plus the 10 test_111 functions ...".
- **`tests/test_129_coincident_centroids_and_held_out_floor.py`:**
  `_PRE_129_FINDINGS` drops `"force_overlap"` (line 734).
- **`tests/test_131_tangent_direction_normalisation.py`:** drop the
  `"force_overlap"` key of `_PRE_ITEM_TANGENT_ANGLES_DEG` (356),
  `_PRE_ITEM_NET_ADVANCE_S_MM` (373), `_PRE_ITEM_INTER_TANGENT_ANGLES_DEG`
  (423) and `_PRE_ITEM_OTHER_CURVATURE_FIELDS` (863).
- **`tests/test_132_monotonicity_against_traversal_order.py`:**
  - `_PRE_ITEM_U_VALUES` drops `"force_overlap"`.
  - `test_ac20_test_040_detection_partition_reconciled` asserts
    `t040._RECONSTRUCTED_MODES == set()`.
  - `test_ac21_test_057_swap_case_claimed_caught_at_full_sensitivity` drops
    its `_RECONSTRUCTED_RECORD_MODES` line.
  - Delete `test_ac22_overall_corpus_sensitivity_is_not_over_claimed`. Its
    premise, that sensitivity is below 1.0, is false by construction once no
    case is reconstructed: the overall number is 9/9 and is owned by
    test_057. Add a dated line to the section header saying why.
- **`tests/test_134_decision_table_evidence_companion.py`:** add
  `_INVENTORY_REMOVED_AFTER_126 = {"tests/corpus/fixtures/force_overlap_seg.nii.gz"}`.
  `test_ac18_test105_inventory_unchanged_by_this_item` asserts that set is
  disjoint from the inventory, and
  `len(inventory) == _ITEM_126_INVENTORY_COUNT + len(_INVENTORY_ADDED_AFTER_126) - len(_INVENTORY_REMOVED_AFTER_126)`
  (25).
- **`tests/test_137_mode_less_rule_disposition.py`:**
  `test_adv_measured_artifact_movement_counts_from_spec`'s bucket table sets
  `("per_mode_metric", "rule_mode_map", "rule_declaration"): 2` and adds
  `("per_mode_metric", "rule_declaration"): 1`. The total stays 145, and
  `mode1_count`, `mode2_count` and `mode16_count` stay 5, 4 and 2.
- **`tests/test_138_traceability_matrix.py`:**
  - `test_ac14_overlap_mode_not_pipeline_detected_names_reconstructed_case` is
    renamed `test_ac14_overlap_mode_not_pipeline_detected_names_no_case`. It
    asserts:
    - mode 15's `pipeline_detected is False`;
    - `cases == []`;
    - no geometric manifest case has `failure_mode == 15`.
  - `test_ac20_..._never_designates_corpus`'s `witness` adds
    `(15, "overlap")`, with a dated item-195 line.
  - `test_adv_ac31_stale_mechanism_one_character_off_the_real_case_id_is_detectable`
    is renamed `..._off_the_real_rule_id_is_detectable`:
    - its premise becomes `"overlap" in record["rules"]`;
    - the `matrix_overlap_mode_typo_mechanism` fixture text becomes
      `"The mechanism names overlapp, one character off the real rule id, on purpose, for a test."`.
  - The `_OVERLAP_MODE` comment (lines 159–162) drops its case-id sentence.
- **`tests/test_143_s_axis_correction.py`:**
  - `_PRE_ITEM_NET_ADVANCE_S_MM_MAGNITUDE` drops `"force_overlap"` (line 331).
  - `test_ac19_snapshot_covers_all_15_entries_across_both_corpora` asserts
    `len(snapshot) == 17`.
  - `_FROZEN_RENAMED_CASE_IDS` (line 700) stays (A5).
- **`tests/test_144_failure_mode_specification.py`:** delete
  `test_adv_overlap_mode_corpus_case_is_reconstructed_and_measured_live`.
- **`tests/test_145_eight_hypothesised_modes.py`:**
  - `_EXPECTED_DERIVED_STATUS[15] = "implemented"`.
  - `test_ac11_overlap_mode_structural_unobservability_holds_live` keeps its
    rung assertion, and asserts `mode.corpus_cases == ()` in place of the
    case half.
  - `test_ac12_overlap_mode_records_the_single_channel_mechanism` reads
    `mode.mechanism` in place of the removed case's `reason`. Its five
    substring checks are unchanged, and A9's draft meets them.
- **`tests/test_147_specification_is_the_record.py`:**
  `_EXPECTED_DERIVED_STATUS[15] = "implemented"` (line 1250).
- **`tests/test_148_per_path_mode_attribution.py`:**
  - The `_AC16_CASES` row becomes `("planted_overlap", "overlap", ("overlap",))`.
  - `_overlap_reconstructed_record` returns the hand-built record
    `{"overlaps": [{"label_a": 20, "label_b": 21, "name_a": "L1", "name_b": "L2", "overlap_voxels": 7}]}`,
    with its docstring saying why.
  - The `"overlap"` branch of `_ac16_findings` ignores `geo_by_id` for that
    key.
  - Measured: `run_rules` on it yields one `overlap` finding (detector
    `overlapping_segments`, labels {20, 21}). So `covered_rule_ids ==
    all_rule_ids` still holds.
- **`tests/test_149_conformance_report.py`:**
  - `test_ac13_...`: `len(cases) == 17` and `len(geometric) == ... == 13`.
  - `test_ac18_overlap_mode_pipeline_detected_stays_false` asserts
    `pipeline_detected is False` and `mode9["cases"] == []`.
- **`tests/test_151_stage30_validation.py`:**
  - `test_ac8_case_count_equals_summed_manifest_case_count` and
    `test_ac9_no_unspecified_case_and_matrix_is_fully_conformant`: 18 → 17.
  - Delete `test_ac16_overlap_case_yields_overlap_through_the_reconstruction`
    and `test_ac16_manifest_detection_is_reconstructed_record`.
  - Re-point `test_ac16_overlap_case_yields_no_overlap_through_the_pipeline`
    over every geometric manifest case: each record's `overlaps == []`, and
    `overlap` is not among its `pipeline_findings`. Measured true for all 13.
    Rename it `test_ac16_no_committed_case_yields_an_overlap_through_the_pipeline`.
  - `test_ac16_mode15_carries_the_case` becomes
    `test_ac16_mode15_carries_no_corpus_case`, asserting
    `SPECIFICATION[15].corpus_cases == ()`.
  - The two AC35 tests go green through step 11.
- **`tests/test_153_eval_harness_rekey.py`:**
  - `_OPERATORS` drops `"force_overlap"`.
  - `test_ac18_designated_metrics_cover_the_registry` asserts
    `set(designated) == set(per_mode.PER_MODE_METRIC_SPECS) - {"overlapping_voxel_count"}`,
    with a dated line: the one metric without a ladder since item 195.
  - `test_ac24_verdict_responses_are_keyed_by_metric` asserts
    `set(verdict.responses) == {s.designated_metric for s in severity_ladder.SEVERITY_LADDERS.values()}`.
  - `_metric_to_operator`'s docstring drops "covers every registry key".
  - `test_ac5_homes_are_derived_from_the_specification` goes green through
    A3's candidate feature.
- **`tests/test_157_case_id_rename.py`:** add
  `_REMOVED_NEW_IDS = frozenset({"force_overlap"})`.
  - `test_ac3_every_new_id_is_exactly_one_live_case` asserts count 1 for
    every new id not in the set, and count **0** for each id in it.
  - `test_a8_each_new_id_resolves_to_exactly_one_manifest_case` does the
    same, against the manifest.
- **`tests/test_167_mode_3_detector.py`:** delete
  `test_force_overlap_stays_silent`.

**Green without an edit** once steps 8–11 run:

- every fresh-vs-committed artifact test the sweeps listed:
  - test_103/104 (catalogue drift);
  - test_134's AC4/AC5 (golden evidence);
  - test_136's AC13;
  - test_137's AC15;
  - test_138's AC2–AC6/AC28;
  - test_143's AC11/AC12/AC15;
  - test_144's AC17–AC21;
  - test_147's AC24;
  - test_148's AC14;
  - test_149's AC16/AC19/AC20;
  - test_150's AC11;
  - test_157's AC16–AC18;
- test_040's AC16 and test_116's AC11 (corpus fresh-vs-committed);
- test_094 and test_178;
- test_125's AC15;
- test_154;
- test_163;
- test_169's AC6/AC7;
- `tests/test_aide_status_report.py`, whose `force_overlap` is an in-memory
  fixture.

## Validation

1. Run
   `.venv/bin/python -c "from segfacet.eval import severity_ladder as s; v = s.score_harness(s.run_severity_harness()); print(v.passed, {k: round(l.margin, 4) for k, l in v.per_ladder.items()})"`
   and confirm it prints `True` with seven ladders and A2's margins.
2. Open `docs/aide/traceability_matrix.generated.md` and check:
   - the mode 15 row reads `implemented` and `overlap (analytic)`;
   - the conformance line reads `Agree: 17`;
   - the rule-exercise row for `overlap` reads `unexercised` with
     `structurally-unobservable` and mode 15;
   - no row names `force_overlap`.
3. Look at `docs/aide/corpus_sheet.png` and confirm 13 case panels, none
   labelled `force_overlap`.
4. Run `python .aide/scripts/aide.py status` and confirm Stage 30 and
   Stage 20 show step 11's amendments.

No environment profile is needed.

## Dependencies

- Item 194: last regenerated the three document pairs and amended Stage 30
  criterion 3's rung clause, which this item's note must not supersede (✅).
- Item 193: last amended Stage 30 criterion 1 and Stage 20 criterion 5, the
  clauses step 11 re-amends (✅).
- Item 190: added the condition-keyed eval bucket that test_120's AC24 map
  reads (✅).

**Downstream:**

- Stage 33 D4 re-measures the severity-ladder constants. It inherits seven
  ladders and A2's scored-metric rule.
- D6's stage validation checks Stage 33 criterion 2 across both corpora.

## Decisions & Trade-offs

Implemented per the Assumptions and Implementation Steps above, with no
deviation. Every measured value matched its A8/A9 literal on the real
change: `score_harness(run_severity_harness())` passes with margins
`{displace: inf, fragment: inf, inject_islands: 118.4907, relabel_swap:
inf, remove_level: inf, crop_at_border: 0.3253, sequence_break: inf}`;
`traceability.build_matrix().conformance` reads `Agree: 17, Disagree: 0`;
mode 15 derives `implemented`; derived status counts over 16 modes:
validated 5, implemented 4, specified 2, proposed 5, validated through a
pipeline-detected case 5 and through a reconstructed record only 0;
derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3,
structurally-unobservable 1, none 7. The corpus, intensity corpus and
`feature_catalogue.generated.md` regenerated byte-identical; the intensity
corpus, `feature_catalogue.generated.md` and `docs/corpus-s-axis-correction.md`
were left untouched by the regeneration, as predicted. `corpus_sheet.png`
regenerated at 75350 bytes, matching A8.

- **Left open:** retiring the `reconstructed_record` path altogether.
  - No committed case has used it since this item. `monotonic_true_spatial_order`
    has been unused since item 132.
  - The dispatch in `synth.regression`, `failure_modes._measured_firing_geometric`
    and `traceability._PIPELINE_DETECTIONS` stays for a future reconstructed
    case, such as a real multi-channel input.
  - Retiring it is its own item: it moves the manifest schema's `detection`
    vocabulary, which test_040, test_041 and test_147 pin.
- **Left open:** the `⏸️ D2` bullet in `progress.md`'s Stage 33 section still
  reads "`force_overlap` retired or declared multi-channel, and `fragment`
  parked". The `force_overlap` half is this item's D3 bullet. Rewording a
  deferred deliverable bullet is a progress-document decision for the stage's
  owner, not this item's.
- **Left open:** `scripts/aide_status_report.py`'s corpus section still
  carries a reconstructed-record paragraph, which now counts 0 cases. It
  renders honestly, so no consumer in this batch needs the change.
