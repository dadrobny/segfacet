<!-- aide-template: item 1 -->
# Item 153 — Re-key the per-mode eval harness onto the signed-off catalogue

> **Created:** 2026-09-16 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update
> **Queue:** [`../queue/queue-021.md`](../queue/queue-021.md) · Item 153
> **Objectives:** G7, G8
> **Suggested branch:** `aide/153-re-key-the-per-mode`

---

## Description

Roadmap Stage 31 D3, first half. The Stage-18 eval harness
(`segfacet.eval.per_mode`, `segfacet.eval.severity_ladder`,
`segfacet.eval.per_mode_cohort`, and the comparison-report schema) is still
keyed by the pre-sign-off failure-mode ids 1–8. Their names are frozen in
`per_mode.LEGACY_STAGE18_MODE_NAMES`. The ids disagree with
`segfacet.failure_modes.SPECIFICATION` as signed off at item 150 (2026-09-14):
legacy "mode 1" is *label not aligned with the vertebra it names*, but the
specification's mode 1 is *Segmentation accuracy (over-/under-segmentation)*.

This item moves every key, id, name and schema field of that surface off the
legacy numbering and retires the legacy map. **It changes ids and names, not
numbers.** Every metric value, baseline, direction, rung, recorded margin and
recorded coupling response stays the same. Re-measuring them is item 154's job.

### Why the keys become metric and operator names, not specification ids

The eight Stage-18 metrics do not map one-to-one onto specification modes. Two
metrics measure mode 1, and one measures no failure mode at all (see the
re-homing table below). A registry keyed by specification id would have to drop
a metric or invent an id. So this item:

- keys each **metric** by its existing stable `metric_name`,
- keys each **ladder** by its perturbation `operator`,
- records a metric's or ladder's specification mode in a nullable
  `failure_mode` field, with an explicit `mode_disposition` value.

With this shape, "measures no mode" is a rendered value, not a missing key, and
every emitted mode id is either `null` or a specification id.

### The re-homing decision

Two derivation rules decide each home. Both are recomputed live by this item's
tests (AC5, AC15):

- **Rule (a): the specification cites the metric.** The metric is homed on mode
  *m* when exactly one `SPECIFICATION[m].candidate_features` entry has the path
  `eval.per_mode.<metric_name>`.
- **Rule (b): the specification owns the operator's corpus case.** Take the
  metric's ladder operator *O* (the primary ladder whose `designated_metric` is
  the metric). Find the one case in `tests/corpus/manifest.json` whose
  `perturbation == O`. If `SPECIFICATION[m].corpus_cases` lists that case id,
  the home is *m*. If a `CONDITIONS[c].corpus_cases` lists it instead, the metric
  measures no failure mode and its `condition` is *c*.

Rule (a) takes precedence over rule (b). A ladder's own `failure_mode` is
decided by rule (b) alone, from its operator.

| Old id | What it measured (metric, source) | Ladder operator | Rule (a) | Rule (b) | Home now |
|---|---|---|---|---|---|
| 1 | `unanchored_foreground_fraction`: candidate foreground over GT background, per GT-foreground voxel (candidate vs GT) | `displace` | mode 1 | mode 1 (`mode1_displace`) | **mode 1** |
| 2 | `min_dominant_component_fraction`: minimum per-label `fragmentation_index` (record) | `fragment` | none | mode 1 (`mode2_fragment`) | **mode 1** |
| 3 | `rogue_island_count`: maximum per-label count of stray components below `island_size_ratio` (record) | `inject_islands` | none | mode 4 (`mode3_inject_islands`) | **mode 4** |
| 4 | `mislabelled_volume_fraction`: fraction of GT foreground whose candidate label is another GT label (candidate vs GT) | `relabel_swap` | mode 8 | mode 9 (`mode4_relabel_swap`) | **mode 8** (rule (a)); ladder is mode 9 |
| 5 | `missing_level_count`: GT levels absent from the candidate and mostly background there (candidate vs GT) | `remove_level` | mode 6 | mode 6 (`mode5_remove_level`) | **mode 6** |
| 6 | `fov_clipped_label_count`: labels touching an image face the border rule calls an unexpected clip (record) | `crop_at_border` | none | condition `fov_truncation` (`mode6_crop_at_border`) | **no failure mode**, condition `fov_truncation` |
| 7 | `out_of_order_label_count`: `len(relationships.out_of_order_labels)` (record) | `sequence_break` | none | mode 9 (`mode7_sequence_break`) | **mode 9** |
| 8 | `overlapping_voxel_count`: sum of `overlaps[].overlap_voxels` (record) | `force_overlap` | none | mode 15 (`mode8_force_overlap`) | **mode 15** |
| supplementary ladder | designated metric `min_dominant_component_fraction` | `fuse` | n/a | mode 2 (`fuse_adjacent`) | ladder is **mode 2**; its designated metric is homed on mode 1 |

**What the specification does not decide.** The following are recorded here and
left for item 154. This item does not guess at them:

1. **The `relabel_swap` ladder disagrees with its own metric.** The ladder's
   operator case is a mode-9 case. Its designated metric is cited under mode 8.
   The specification does not say whether this ladder's response measures mode 8
   or mode 9. This item records both (`LadderSpec.failure_mode == 9`, metric
   `failure_mode == 8`) and picks neither.
2. **The supplementary `fuse` ladder disagrees with its own metric in the same
   way.** Its operator case is mode 2, but `min_dominant_component_fraction` is
   homed on mode 1. The specification cites no metric for mode 2.
3. **Some homes are not exclusive.** A home says which mode a metric is
   *designated* for. It does not say that no other mode moves the metric. By the
   definitions, `unanchored_foreground_fraction` also rises under mode 7
   (hallucinated vertebra). `min_dominant_component_fraction` reads
   `fragmentation_index`, which mode 14 also cites, and its fallback
   `largest_component_fraction` is cited by mode 4. `mislabelled_volume_fraction`
   also rises under modes 3, 9 and 12. Which of these responses counts as
   "foreign" is part of item 154's re-measurement.
4. **Mode 1 now has two metrics and two ladders** (`displace`, `fragment`).
   Whether both stay, and what mode 1's ladder base is, belongs to item 154
   (which absorbs item 141).

**The roadmap's premise about the `displace` ladder does not match the code.**
Roadmap Stage 31 D3 says the `displace` ladder "measures the spline-offset
signal, which after item 150 serves no mode". Measured 2026-09-16, it does not.
The ladder's designated metric is `unanchored_foreground_fraction`, which both
rules home on mode 1. The spline-offset path `stage3.per_label_offsets[].offset_mm`
is `feature_docs.MODE_ANCHOR_PATHS[1]`, the catalogue anchor of that metric, and
re-anchoring it is item 154's. So under this item's rules the `displace` ladder
is re-homed to mode 1, not recorded as measuring no mode. That conclusion rests
on rule (a) and rule (b), both recomputed from live state.

### Not in scope

- **No number changes.** This covers metric arithmetic, baselines, directions,
  sources, rungs, `COUPLING_THRESHOLD`, the values of `RECORDED_MARGINS`,
  `recorded_response`, and `MODE_SCALE_SPECS` scales. Re-measuring them is item
  154's.
- **No change to the margin arithmetic.** "Foreign" still means every other
  metric, so a margin keyed by operator equals the value previously keyed by
  legacy id (A5).
- **Left for item 154:** the `rank(v) == v - 1` passages in
  `severity_ladder.py`'s docstring and the degenerate ladder's `rationale`, the
  values of `feature_docs.MODE_ANCHOR_PATHS`, and the mode-1 ladder base.
- **Unchanged:** `segfacet.eval.metrics.PerModeSensitivity`. It is the
  detection-rate surface, keyed by the manifest's `failure_mode`, and those are
  already specification ids.
- **No mode content changes.** No `ModeSpec`/`ConditionSpec` field, rule, corpus
  case or `expected_firing` moves (queue-021's scope fence).
- **No module renames.** The `per_mode` names stay (A9).

## Acceptance Criteria

"The registry" means `segfacet.eval.per_mode.PER_MODE_METRIC_SPECS`. "The eight
metric names" are, in this order: `unanchored_foreground_fraction`,
`min_dominant_component_fraction`, `rogue_island_count`,
`mislabelled_volume_fraction`, `missing_level_count`, `fov_clipped_label_count`,
`out_of_order_label_count`, `overlapping_voxel_count`. "The eight operators" are
`displace`, `fragment`, `inject_islands`, `relabel_swap`, `remove_level`,
`crop_at_border`, `sequence_break`, `force_overlap`. Rules (a) and (b) are as
defined in the Description.

No AC below closes a Stage 31 acceptance criterion on its own. Criterion 3
combines this item's retirement and keying claim with item 154's re-measured
constants, and item 161 attests it. So no AC carries a *(closes …)* annotation.

### Legacy map retired

- [ ] **AC1: The legacy map is gone.** `hasattr(segfacet.eval.per_mode, "LEGACY_STAGE18_MODE_NAMES")` is `False`.
- [ ] **AC2: No source or test names it.** A scan of every `*.py` and `*.json` file under `src/` and `tests/` finds zero files containing the token `LEGACY_STAGE18_MODE_NAMES`. The test builds the needle by concatenation so that it does not match itself.
- [ ] **AC3: No hand-typed mode names in the harness.** The string literals of `src/segfacet/eval/per_mode.py`, `severity_ladder.py` and `per_mode_cohort.py` contain no `SPECIFICATION[m].name` or `.short_name` value for any *m*. The walker is the one used by `test_147`'s AC1.
- [ ] **AC4: No section-6 numbering wording.** None of `src/segfacet/eval/per_mode.py`, `severity_ladder.py`, `per_mode_cohort.py`, `eval/__init__.py`, `per_mode_comparison_schema_v0.json` or `eval_report_schema_v0.json` contains the substring `§6`, `Section 6` or `Section-6`.

### The metric registry

- [ ] **AC5: Homes are derived from the specification.** For each registry entry, `spec.failure_mode` equals the value that rule (a), else rule (b), computes live from `SPECIFICATION`, `CONDITIONS`, `SEVERITY_LADDERS` and `tests/corpus/manifest.json`. The test fails if a metric resolves under neither rule, or under rule (a) to more than one mode.
- [ ] **AC6: The recorded re-homing table holds.** Mapping each metric name to `failure_mode` gives exactly `{unanchored_foreground_fraction: 1, min_dominant_component_fraction: 1, rogue_island_count: 4, mislabelled_volume_fraction: 8, missing_level_count: 6, fov_clipped_label_count: None, out_of_order_label_count: 9, overlapping_voxel_count: 15}`.
- [ ] **AC7: The registry is keyed by metric name.** `list(PER_MODE_METRIC_SPECS)` equals the eight metric names in the stated order.
- [ ] **AC8: Each key matches its entry.** For every key `k`, `PER_MODE_METRIC_SPECS[k].metric_name == k`.
- [ ] **AC9: Mode names come from the specification.** For every entry with `failure_mode` not `None`, `failure_mode_name == SPECIFICATION[failure_mode].name`. For the entry with `failure_mode` `None`, `failure_mode_name` is `None`.
- [ ] **AC10: The disposition follows the home.** `mode_disposition == "measures-mode"` for every entry whose `failure_mode` is not `None`. `mode_disposition == "measures-no-mode"` for every entry whose `failure_mode` is `None`.
- [ ] **AC11: The condition is recorded.** `PER_MODE_METRIC_SPECS["fov_clipped_label_count"].condition` equals the id of the `CONDITIONS` entry whose `corpus_cases` lists the manifest case with `perturbation == "crop_at_border"`. Measured 2026-09-16, that id is `fov_truncation`.
- [ ] **AC12: Only that entry has a condition.** Every registry entry other than `fov_clipped_label_count` has `condition is None`.
- [ ] **AC13: Specification citations resolve to the registry.** Every `SPECIFICATION[m].candidate_features` path of the form `eval.per_mode.<name>` has `<name>` as a registry key, and `PER_MODE_METRIC_SPECS[<name>].failure_mode == m`.

### Emitted per-case records

- [ ] **AC14: The per-case record carries the disposition.** Take `compute_per_mode_metrics(record, candidate=gt, gt=gt).to_dict()["per_mode"]` on the clean-control fixture. Each entry's `failure_mode`, `failure_mode_name`, `mode_disposition` and `condition` equal the registry entry named by its `metric_name`.
- [ ] **AC15: Lookup by metric name.** `PerModeMetrics.by_metric(name)` returns the entry whose `metric_name == name` for each of the eight names, and raises `KeyError` for an unknown name.
- [ ] **AC16: Degradation details name no legacy id.** With `candidate=None, gt=None`, each entry whose `value is None` has a non-empty `detail` that contains its own `metric_name` and matches no `\bmode [0-9]` pattern.

### Ladders

- [ ] **AC17: Ladders are keyed by operator.** `set(SEVERITY_LADDERS)` equals the eight operators, and `SEVERITY_LADDERS[k].operator == k` for every key.
- [ ] **AC18: Designated metrics cover the registry.** The `designated_metric` values of the eight primary ladders are distinct, and together they equal the registry's key set.
- [ ] **AC19: Ladder homes are derived from the specification.** For every ladder in `SEVERITY_LADDERS` and `SUPPLEMENTARY_LADDERS`, `failure_mode` equals rule (b) computed live for its `operator`, and `condition` equals the condition id rule (b) yields, or `None`. Measured 2026-09-16: `relabel_swap` → 9, `crop_at_border` → `None`/`fov_truncation`, `fuse` → 2.
- [ ] **AC20: Margins are keyed by operator.** `set(RECORDED_MARGINS) == set(SEVERITY_LADDERS)`.
- [ ] **AC21: Couplings name a ladder and a foreign metric.** Every `KNOWN_CROSS_MODE_COUPLINGS` entry has `ladder_operator` in `SEVERITY_LADDERS`, has `foreign_metric` in the registry, and has `foreign_metric != SEVERITY_LADDERS[ladder_operator].designated_metric`.
- [ ] **AC22: The degenerate set follows the severity kind.** `DEGENERATE_LADDERS` equals `{k for k, s in SEVERITY_LADDERS.items() if s.severity_kind == "degenerate"}`.
- [ ] **AC23: The re-keyed ratchet still passes.** `score_harness(run_severity_harness()).passed is True`.
- [ ] **AC24: Verdict responses are keyed by metric.** For every `LadderVerdict` in that verdict's `per_ladder` (keyed by operator), `set(responses)` equals the registry's key set.
- [ ] **AC25: Unknown assignments are rejected.** `score_harness(harness, assignment={...})` raises `FacetInputError` when any value in `assignment` is not a registry key.

### Cohort summary, comparison, schema

- [ ] **AC26: Cohort aggregates follow the registry.** For a `RunPerModeSummary` built by `summarise_run_per_mode`, the sequence of `per_mode[i].metric_name` equals the registry's key order. Each entry's `failure_mode` and `mode_disposition` equal that registry entry's.
- [ ] **AC27: Scale specs are keyed by metric.** `set(MODE_SCALE_SPECS)` equals the registry's key set.
- [ ] **AC28: The attributed mode is looked up, not stored separately.** For every `RunComparison` produced by `compare_runs` in the test module, `attributed_mode` equals `PER_MODE_METRIC_SPECS[attributed_metric_name].failure_mode` when `attributed_metric_name` is not `None`, and is `None` otherwise.
- [ ] **AC29: Exclusions are named by metric.** `RunComparison.to_dict()` has the key `excluded_metric_names`, a list of registry keys in registry order, and does not have the key `excluded_modes`.
- [ ] **AC30: Every emitted mode id is valid.** A recursive walk over `PerModeMetrics.to_dict()`, `HarnessResult.to_dict()`, `HarnessVerdict.to_dict()`, `RunPerModeSummary.to_dict()` and `RunComparison.to_dict()` finds no value under a key named `failure_mode` or `attributed_mode` that is neither `None` nor a key of `SPECIFICATION`.
- [ ] **AC31: Pre-re-key blocks are rejected.** `RunPerModeSummary.from_dict` raises `FacetInputError` on a `per_mode_magnitude` block whose entries carry no `mode_disposition` key (the pre-item shape).
- [ ] **AC32: Comparison reports validate.** The dict returned by `build_run_comparison_report` for two summaries validates against `src/segfacet/eval/per_mode_comparison_schema_v0.json` under `jsonschema`.
- [ ] **AC33: The comparison schema declares metric-name exclusions.** `per_mode_comparison_schema_v0.json`'s `comparison.required` contains `excluded_metric_names` and does not contain `excluded_modes`.
- [ ] **AC34: The comparison schema version is bumped.** The schema's `schema_version.const` equals `segfacet.eval.report.PER_MODE_COMPARISON_SCHEMA_VERSION`, which equals `"0.2"`.

### Human-readable text

- [ ] **AC35: No-mode metrics are named as such in the comparison text.** `render_run_comparison` output contains the line fragment `no failure mode (fov_truncation condition) (fov_clipped_label_count)`.
- [ ] **AC36: The evaluation text names each re-homed mode.** The per-mode magnitudes section of `render_evaluation_report` (with a per-mode summary) contains `SPECIFICATION[m].name` for every *m* in `{1, 4, 6, 8, 9, 15}`.

### End to end

- [ ] **AC37: `evaluate --per-mode` still runs.** `segfacet evaluate --per-mode` on the two-case cohort fixture used by `tests/test_101_compare_runs_cli.py` exits 0. The written report's `per_mode_magnitude.per_mode` metric names equal the registry's key order.
- [ ] **AC38: `compare-runs` still runs.** `segfacet compare-runs` on two such reports exits 0, and the JSON it writes validates against `per_mode_comparison_schema_v0.json`.

## Assumptions

- **A1 (keying).** Metrics are keyed by `metric_name` and ladders by `operator`.
  Specification ids are carried in a nullable `failure_mode` field. Keying by
  specification id cannot work, because two metrics share mode 1 and one metric
  has no mode. The queue asks for keys "moved onto `SPECIFICATION`'s ids". Under
  `loop.clarify = "assume"`, this item reads that as "no key or id field carries
  a value outside the specification" (AC30), not as "specification ids are the
  dictionary keys".
- **A2 (derivation rules).** A metric's home comes from rule (a), then rule (b).
  A ladder's home comes from rule (b). Rule (a) wins because it is the
  specification's direct citation of the metric. Rule (b) is only what the
  metric's perturbation is designated to produce.
- **A3 (unresolved disagreements).** The `relabel_swap` ladder (8 vs 9), the
  `fuse` ladder (2 vs 1), the non-exclusive homes, and mode 1 having two ladders
  are recorded, not resolved. They go to item 154 unchanged.
- **A4 (roadmap premise).** Roadmap Stage 31 D3's statement that the `displace`
  ladder measures the spline-offset signal is not what `severity_ladder.py` does
  (Description). The ladder is re-homed to mode 1 by both rules. The roadmap is
  not edited from this item. The finding is captured in `docs/aide/insights.md`.
- **A5 (numbers carried verbatim).** Each value moves to its new key unchanged.
  Legacy `RECORDED_MARGINS[n]` becomes `RECORDED_MARGINS[<operator of old ladder n>]`.
  The coupling `(6 → 1, 2.79)` becomes `(crop_at_border → unanchored_foreground_fraction, 2.79)`
  and `(8 → 1, 0.9629)` becomes `(force_overlap → unanchored_foreground_fraction, 0.9629)`.
  `MODE_SCALE_SPECS` entries move the same way. The margin's "foreign" set stays
  "every other metric", so re-keying changes no computed margin. Whether metrics
  that share a mode should count as foreign is item 154's re-measurement
  question. Coupling `cause` prose is reworded to operator and metric names only.
- **A6 (item 154's surface).** Item 154 corrects the `rank(v) == v - 1` wording
  in `severity_ladder.py` (module docstring and degenerate-ladder `rationale`).
  This item may relabel the headings around it ("Mode 7 (`sequence_break`)" →
  "`sequence_break`") but must leave the literal in place. Item 154 also owns
  the values of `feature_docs.MODE_ANCHOR_PATHS`; this item only rewrites the
  comment block above them that describes the legacy ids.
- **A7 (schema versions).** The comparison schema's required field
  `excluded_modes` is renamed to `excluded_metric_names`, and
  `PER_MODE_COMPARISON_SCHEMA_VERSION` goes `"0.1"` → `"0.2"`. The file name
  `per_mode_comparison_schema_v0.json` stays, because `test_105` names it. The
  evaluation-report schema does not enumerate `per_mode_magnitude` leaves, so
  its version stays `"0.1"`. A pre-re-key block is instead rejected by
  `RunPerModeSummary.from_dict` (AC31), which `compare-runs` already surfaces as
  exit 1 with no traceback.
- **A8 (test_125 / test_135).** The queue names both as pins of the legacy map.
  Measured 2026-09-16, neither references a per-mode eval symbol. Their "mode 4"
  and `failure_mode != 0` mentions are the rule engine's Detector B history and
  the manifest's specification ids. They are authorised below only for any prose
  pin the builder finds. No change to them is expected.
- **A9 (no module renames).** Module, class and field names that say "per mode"
  (`per_mode.py`, `PerModeMetrics`, `per_mode`, `PER_MODE_METRIC_SPECS`,
  `ModeAggregate`, `ModeDelta`) stay. They name a per-failure-mode *metric*
  surface, not an id scheme. Renaming them would churn every consumer and change
  no id.
- **A10 (API renames, no compatibility aliases).**
  - `by_mode` → `by_metric` on `PerModeMetrics`, `RunPerModeSummary` and
    `RunComparison`; `HarnessResult.by_mode` → `by_operator`.
  - `DEGENERATE_LADDER_MODES` → `DEGENERATE_LADDERS`.
  - `CrossModeCoupling.ladder_mode`/`foreign_mode` → `ladder_operator`/`foreign_metric`.
  - `LadderVerdict` gains `operator`, and its `failure_mode` becomes nullable.
    `coupled_modes` → `coupled_metrics`.
  - `LadderSpec` gains `designated_metric` and `condition`.
  - `MetricSpec`/`PerModeMetric`/`ModeAggregate`/`ModeDelta` gain
    `mode_disposition` and `condition`.
  - `score_harness(assignment=)` becomes `{operator: metric_name}`.

  Every consumer is in-tree, so no deprecated alias is kept.
- **A11 (tie-break).** Before this item, `compare_runs` broke an exact
  normalised-delta tie by the lowest legacy mode id. It now breaks the tie by
  registry order. The registry keeps the legacy order, so every tie resolves to
  the same metric as before.
- **A12 (rendering literal).** A no-mode metric renders in the human text as
  `no failure mode (<condition> condition)`, in the place where a mode's
  `failure_mode_name` appears.
- **A13 (engine 1.52.1).** `aide scope` proves the authorised paths below.
  Item 152 is merged (✅ in `progress.md`), so nothing blocks the claim.

## Implementation Steps

1. **`src/segfacet/eval/per_mode.py`**
   - Delete `LEGACY_STAGE18_MODE_NAMES` and the `_MappingProxyType` alias
     import.
   - Re-key `_METRIC_TABLE` by metric name, keeping legacy order. Add
     `failure_mode` (per AC6) and `condition` (`"fov_truncation"` for the FOV
     metric) to each row.
   - Add `mode_disposition` and `condition` to `MetricSpec` and `PerModeMetric`,
     with `failure_mode: Optional[int]` and
     `failure_mode_name: Optional[str]`.
   - Build `failure_mode_name` from
     `segfacet.failure_modes.SPECIFICATION[id].name`. `failure_modes` is
     stdlib-only, so importing it is cheap.
   - Replace `by_mode` with `by_metric`.
   - Rename the private `_modeN_*` functions to their metric names, and reword
     their `detail` strings to name the metric (AC16).
   - Iterate the registry in `compute_per_mode_metrics` instead of
     `range(1, 9)`.
   - Rewrite the module docstring table: metric, home, source, baseline.
     Remove `§6` wording.
2. **`src/segfacet/eval/severity_ladder.py`**
   - Remove the legacy import.
   - Give `LadderSpec` `designated_metric`, a nullable `failure_mode`,
     `failure_mode_name` read from `SPECIFICATION`, and `condition`, with values
     per AC19.
   - Re-key `SEVERITY_LADDERS` and `RECORDED_MARGINS` by operator, with values
     unchanged.
   - Rename `DEGENERATE_LADDER_MODES` → `DEGENERATE_LADDERS = frozenset({"sequence_break"})`.
   - Change the `CrossModeCoupling` fields per A10, with values unchanged.
   - In `score_harness`, compute spans and responses over registry keys, key
     `per_ladder` by operator, default `assignment` to
     `{op: spec.designated_metric}`, and validate `assignment` values against
     the registry.
   - Change `HarnessResult.by_mode` → `by_operator`.
   - Update `HarnessVerdict.summary()` to name ladders by operator.
   - Reword the docstrings and table to operators and homes. Leave every
     `rank(v) == v - 1` occurrence untouched (A6).
3. **`src/segfacet/eval/per_mode_cohort.py`**
   - Key `ModeAggregate`/`ModeDelta` by `metric_name`, carrying
     `failure_mode` (nullable), `failure_mode_name`, `mode_disposition` and
     `condition`.
   - Key `MODE_SCALE_SPECS` by metric name.
   - Change `by_mode` → `by_metric`.
   - Attribute by metric: `attributed_metric_name` is primary, and
     `attributed_mode`/`attributed_mode_name` are looked up from the registry.
   - Change `excluded_modes` → `excluded_metric_names`, and break ties by
     registry order.
   - Make `from_dict` raise `FacetInputError` on entries lacking
     `mode_disposition`.
   - Update `summary()` and the docstrings.
4. **`src/segfacet/eval/report.py`**
   - Set `PER_MODE_COMPARISON_SCHEMA_VERSION = "0.2"`.
   - In `render_run_comparison`, decide whether attribution happened from
     `attributed_metric_name`, not `attributed_mode`.
   - Look up the top entry with `by_metric`.
   - Render a no-mode entry per A12, and name exclusions by metric.
   - Apply the same no-mode label in `render_evaluation_report`'s per-mode
     magnitudes section.
5. **`src/segfacet/eval/per_mode_comparison_schema_v0.json`**
   - Set the `const` to `"0.2"`.
   - Replace `excluded_modes` with `excluded_metric_names` (a string array)
     in `required` and `properties`.
   - Update the descriptions.
6. **`src/segfacet/eval/eval_report_schema_v0.json`**: rewrite the
   `per_mode_magnitude` description only (no `Section-6`, no "eight modes").
7. **`src/segfacet/eval/__init__.py`**: update the re-exports for the renamed
   symbols, and update the docstring.
8. **`src/segfacet/cli.py`**: make sure the `compare-runs` error path reports an
   `from_dict` `FacetInputError` as exit 1 with no traceback, if it does not
   already. Update help text that names eight §6 modes.
9. **`src/segfacet/failure_modes.py`**: rewrite the module-docstring paragraph
   headed "Known divergence…", which names the legacy map, to say the harness is
   keyed by metric and operator with nullable specification ids. Change nothing
   else. The generated specification artifacts must not change.
10. **`src/segfacet/feature_docs.py`**: rewrite the `MODE_ANCHOR_PATHS` comment
    and docstring passages that describe "legacy 1–8" so they refer to the
    registry's metric names. Values unchanged (A6).
11. **Reconcile the existing tests** listed under Testing Strategy onto the new
    keys. Keep every numeric expectation as it is.
12. Nothing to capture for A4. The spec author already recorded the
    roadmap-premise finding in `docs/aide/insights.md` (knowledge entry, item
    153, 2026-09-16).

## Authorised paths

**May change:**

- `src/segfacet/eval/per_mode.py` — metric registry re-key; retire the legacy map
- `src/segfacet/eval/severity_ladder.py` — ladder/margin/coupling re-key
- `src/segfacet/eval/per_mode_cohort.py` — cohort aggregate/comparison re-key
- `src/segfacet/eval/report.py` — comparison schema version; no-mode rendering; attribution by metric
- `src/segfacet/eval/__init__.py` — re-exports of renamed symbols
- `src/segfacet/eval/per_mode_comparison_schema_v0.json` — `excluded_metric_names`, version const
- `src/segfacet/eval/eval_report_schema_v0.json` — `per_mode_magnitude` description text
- `src/segfacet/cli.py` — compare-runs legacy-block error path and help text
- `src/segfacet/failure_modes.py` — the "Known divergence" docstring paragraph only
- `src/segfacet/feature_docs.py` — the `MODE_ANCHOR_PATHS` comment/docstring only
- `tests/test_153_eval_harness_rekey.py` — this item's tests
- `tests/test_099_per_mode_metrics.py` — legacy-name and 1..8 key pins
- `tests/test_100_severity_ladder.py` — ladder/margin/coupling key pins
- `tests/test_101_per_mode_cohort.py` — aggregate/comparison key pins
- `tests/test_101_compare_runs_cli.py` — legacy-name text pin, eight-entry block
- `tests/test_102_stage18_validation.py` — legacy-name text pins
- `tests/test_109_attribution_scale.py` — `excluded_modes`/`attributed_mode` pins
- `tests/test_112_overlap_short_circuit.py` — `SEVERITY_LADDERS[1]`
- `tests/test_147_specification_is_the_record.py` — AC1's `per_mode.py` offender allowance
- `tests/test_125_stage28_validation.py` — named by the queue; no change expected (A8)
- `tests/test_135_stage29_validation.py` — named by the queue; no change expected (A8)

**Asserts against:**

- `tests/corpus/manifest.json` — AC5/AC11/AC19 read each operator's case id live
- `docs/aide/feature_catalogue.generated.md` — the traced record paths `compute_per_mode_metrics` reads must not change; the drift test recomputes it
- `docs/aide/failure_modes.generated.json` — the specification artifacts must regenerate byte-identically; the docstring edit must not reach them

## Testing Strategy

New module: **`tests/test_153_eval_harness_rekey.py`**, with one test per AC,
named `test_acN_*`. AC23, AC37 and AC38 run the real harness and CLI. Share one
module-scoped `run_severity_harness()` result across AC23, AC24 and AC30. Build
the AC37/AC38 cohort with the same fixture helper `test_101_compare_runs_cli.py`
uses. Do not hard-code corpus case ids in AC5/AC11/AC19. Item 157 renames them,
so resolve each through the manifest's `perturbation` field.

**Adversarial and edge cases:**

- **AC2 positive control.** A planted file under `tmp_path` containing the token
  is flagged by the same scanner.
- **AC5 negative controls.** A monkeypatched registry entry with a wrong home
  fails the derivation. A fake specification citing
  `eval.per_mode.<metric>` under two modes is reported as not derivable, not
  silently resolved.
- **AC13 negative control.** A candidate-feature path naming a non-existent
  metric is reported.
- **AC25.** Pass an assignment value that is an int (`1`), a legacy-looking
  string (`"1"`), and an unknown name. All three raise.
- **AC30 walker positive control.** A dict with `failure_mode: 99` nested two
  levels deep is flagged.
- **AC31.** Feed `from_dict` a block shaped exactly as a pre-item report: int
  `failure_mode` 1..8 and no `mode_disposition`. Also run `compare-runs` on such
  a report file and expect exit 1 with no traceback on stderr.
- **AC32.** Validate a comparison dict carrying `excluded_modes: [3]` instead of
  `excluded_metric_names`. It must fail validation.
- **AC16.** Check every degraded entry, not just the first.
- **Determinism.** `PER_MODE_METRIC_SPECS`, `SEVERITY_LADDERS` and
  `RECORDED_MARGINS` iteration order is the same across two imports (subprocess
  not required, since the dicts are literals).

**Existing tests to reconcile.** Each pins the old keys or names. Re-key them
and keep every numeric expectation:

- `tests/test_099_per_mode_metrics.py` — around L321–325: the
  `failure_mode_name == LEGACY_STAGE18_MODE_NAMES[mode]` pin; plus every
  `by_mode(n)`, `PER_MODE_METRIC_SPECS[n]` and `range(1, 9)` use.
- `tests/test_100_severity_ladder.py` — around L328–332: the legacy-name pin;
  `SEVERITY_LADDERS[n]`, `RECORDED_MARGINS[n]`, `DEGENERATE_LADDER_MODES`, the
  `ladder_mode`/`foreign_mode` fields, `by_mode`, and `per_ladder[n]`.
- `tests/test_101_per_mode_cohort.py` — `by_mode`, `attributed_mode`
  assertions, `excluded_modes`, and `MODE_SCALE_SPECS[n]`.
- `tests/test_101_compare_runs_cli.py` — around L194–197: legacy names asserted
  in the text output; the eight-entry `per_mode_magnitude` block's keys.
- `tests/test_102_stage18_validation.py` — around L502–509: legacy names
  asserted in the text.
- `tests/test_109_attribution_scale.py` — `excluded_modes`, `attributed_mode`
  and lowest-mode tie-break expectations. Keep them as registry-order
  expectations, with the same attributed metric.
- `tests/test_112_overlap_short_circuit.py` — around L553:
  `SEVERITY_LADDERS[1]` → `SEVERITY_LADDERS["displace"]`.
- `tests/test_147_specification_is_the_record.py` — around L258–283: AC1's
  expected offender set drops `src/segfacet/eval/per_mode.py`, and the
  `LEGACY_STAGE18_MODE_NAMES` subset assertion is removed with it. The
  `rank(v) == v - 1` comment near L585 is item 154's and stays.

Do not run a suite as part of spec authoring. The validator runs the full suite.

## Validation

The suite proves the new keys. It cannot prove that **no number changed**, which
is a diff-time claim, so the validator also checks the diff:

1. Run `git diff aide/queue-021...HEAD -- src/segfacet/eval/severity_ladder.py src/segfacet/eval/per_mode.py src/segfacet/eval/per_mode_cohort.py`.
   Confirm that every float or int literal in `RECORDED_MARGINS`, in each
   `recorded_response` of `KNOWN_CROSS_MODE_COUPLINGS`, in `COUPLING_THRESHOLD`,
   in the `_METRIC_TABLE` baselines, in the rung severities, and in the
   `MODE_SCALE_SPECS` scales appears on both sides of the diff under the A5
   correspondence. Record any literal that moved as a FAIL.
2. Run `.venv/bin/python -m segfacet.cli evaluate --per-mode` (or the `segfacet`
   entry point) on the two-case cohort from `tests/test_101_compare_runs_cli.py`,
   written to a scratch directory. Then run `segfacet compare-runs` on two such
   reports. Inspect `eval_report.txt` and the comparison text, and confirm:
   - mode names are the specification's,
   - `fov_clipped_label_count` renders as
     `no failure mode (fov_truncation condition)`,
   - no `mode 1`–`mode 8` legacy wording appears.

   Record the measured lines in the Decisions section.
3. Run `python .aide/scripts/aide.py scope` against this spec.

No `[validation]` profile is needed. Everything runs on the loop's CPU host.

## Dependencies

None.

**Downstream:** item 154 re-measures the constants this item re-keys, and
resolves the four disagreements recorded under "What the specification does not
decide". Item 161 attests Stage 31 criterion 3 over both items. Item 157 renames
corpus case ids and fixture file names that `tests/test_101_compare_runs_cli.py`
also references; the two edits touch different lines.

## Decisions & Trade-offs

- **`_METRIC_TO_OPERATOR` is a local literal in `per_mode.py`, not read from
  `severity_ladder.SEVERITY_LADDERS`.** `severity_ladder.py` imports
  `per_mode.PER_MODE_METRIC_SPECS` at module load time, so having
  `per_mode._derive_homes()` import `severity_ladder` back (to read each
  ladder's `designated_metric`) would be circular -- `severity_ladder`'s own
  module body would still be executing (before `SEVERITY_LADDERS` exists)
  when `per_mode` tried to import it. The eight-entry metric-name ->
  operator table is a fixed structural pairing (the item spec's own "eight
  metric names" / "eight operators" lists, matched positionally), so it is
  declared once as a private constant in `per_mode.py` and cross-checked
  live by the test file's own independent `_metric_to_operator()` (which
  *does* read `severity_ladder.SEVERITY_LADDERS`, since the test module has
  no such circularity constraint).
- **`score_harness`'s per-(ladder, metric) span lookup needed a real fix, not
  just a re-key.** The legacy implementation read `spans[f][f]` to get "metric
  f's own full swing on its own ladder", which worked only because a
  ladder's dict key and its designated metric's dict key were the same
  integer (`mode`). Under the re-keyed scheme (`spans` keyed by operator,
  metric identity is a separate string), that lookup has to go through an
  explicit `owning_operator = {designated_metric: operator}` map built from
  the ladders actually present in the harness, then `spans[owning_operator[f]][f]`.
  Without this fix every response inflated to `math.inf` or `0.0`-denominator
  and the ratchet failed universally on first measurement -- caught before
  commit by re-running `run_severity_harness()` + `score_harness()` and
  comparing against `RECORDED_MARGINS`/`KNOWN_CROSS_MODE_COUPLINGS` (below).
- **`score_harness(assignment=...)` now merges onto the default rather than
  requiring a complete mapping.** AC25's adversarial cases pass a
  single-operator override (`{op: bad_value}`) and expect the *non-vacuity*
  companion call (`{op: valid}`) to succeed without needing every other
  operator's entry supplied. The resolved assignment is therefore
  `{op: spec.designated_metric for ...}` updated in place by any
  caller-supplied partial mapping, and every *resolved* value (not just the
  caller-supplied ones) is validated against the registry. This drops the
  previous `KeyError`-on-missing-entry behaviour, which the pre-153 code
  never exercised with a partial dict either (`score_harness(assignment=)`
  had no test passing anything but a full identity/negative-control mapping
  before this item).
- **`ModeDelta` gained a `condition: Optional[str]` field** (not enumerated
  in A10's list) so `render_run_comparison`'s no-mode rendering (A12) can
  read the excluded metric's condition without a second registry lookup.
  Copied verbatim from `PER_MODE_METRIC_SPECS[metric_name].condition` in
  `compare_runs`; no test in this item or the reconciled suite constructs a
  `ModeDelta` positionally, so the added field is additive.
- **Measured harness run (2026-09-16), confirming every constant moved
  verbatim (A5):** `run_severity_harness()` + `score_harness()` on the
  re-keyed registries reproduces `passed=True` and exactly the recorded
  margins: `displace`=inf, `fragment`=inf, `inject_islands`=112.0370...
  (>= `112.0 * 0.95`), `relabel_swap`=inf, `remove_level`=inf,
  `crop_at_border`=0.35852... (>= `0.3585 * 0.95`, status `coupled`),
  `sequence_break`=inf, `force_overlap`=1.03863... (>= `1.038 * 0.95`,
  status `coupled`). The two recorded couplings
  (`crop_at_border`→`unanchored_foreground_fraction`=2.79,
  `force_overlap`→`unanchored_foreground_fraction`=0.9629) both hold under
  the `measured <= recorded * 1.05` ratchet. A line-level diff of
  `per_mode.py`/`severity_ladder.py`/`per_mode_cohort.py` against the branch
  base confirms every float/int literal in `RECORDED_MARGINS`, the
  `KNOWN_CROSS_MODE_COUPLINGS` `recorded_response`s, `COUPLING_THRESHOLD`,
  the `_METRIC_TABLE` baselines, the rung severities, and `MODE_SCALE_SPECS`
  appears with the identical multiset of numeric literals on both sides of
  the diff (checked file-by-file with a literal-extraction script) -- no
  number moved.
- **CLI end-to-end (2026-09-16):** `segfacet evaluate --per-mode` on the
  `test_101_compare_runs_cli` two-case cohort fixture exits 0 and
  `eval_report.json`'s `per_mode_magnitude.per_mode` metric names equal the
  registry's key order; `segfacet compare-runs` on two such reports exits 0
  and the written `per_mode_comparison.json` validates against the bumped
  (`"0.2"`) schema. A pre-item-shaped `per_mode_magnitude` block (int
  `failure_mode`, no `mode_disposition`) fed to `compare-runs` exits 1 with
  no traceback on stderr and writes nothing to `--out` (AC31).
- **`aide scope`** confirms this branch's 20 changed files are all
  authorised, measured against `origin/aide/queue-021`.
- **(2026-09-16) Reviewer-found production defect fixed: homes are literal,
  not derived at import time.** `per_mode._derive_homes()` and
  `severity_ladder._ladder_home()` called `segfacet.synth.corpus.
  load_manifest()`, reading `tests/corpus/manifest.json`, from module-level
  code (`PER_MODE_METRIC_SPECS = _build_registry()` / `SEVERITY_LADDERS =
  {...}` both execute at import time). `pyproject.toml` packages only
  `src/segfacet`, so a non-editable install ships no `tests/` tree, and
  merely `import segfacet.eval.per_mode` (or `severity_ladder`) raised a raw
  `FileNotFoundError` -- breaking every `evaluate --per-mode`/`compare-runs`
  run outside an editable checkout. Neither module touched the test tree
  before this item. Fixed by replacing both live derivations with literal
  `_METRIC_HOMES` / `_LADDER_HOMES` tables transcribed from this item's
  measured re-homing table (Description, AC6/AC11/AC19) -- the same pattern
  already used for `_METRIC_TO_OPERATOR` (now removed as unused: the test
  file's own independent `_metric_to_operator()` in
  `tests/test_153_eval_harness_rekey.py` covers what it existed for).
  Re-verified this does not contradict any test: `test_ac5_*`, `test_ac13_*`
  and `test_ac19_*` compare production's *stored* `failure_mode`/`condition`
  against a value the test module derives live, independently, from
  `SPECIFICATION`/`CONDITIONS`/the manifest (`_derived_home`, `_rule_a_home`,
  `_rule_b_home` in the test file) -- none reads or monkeypatches
  production's derivation function or expects a changed `SPECIFICATION` to
  move a registry/ladder value at runtime, so literals in production,
  checked against a live re-derivation in the test, satisfy every AC. AC11's
  "derived live from CONDITIONS" reads the same way: the test derives live
  and asserts the literal `condition` matches. Sanity-imported both modules
  after the fix (`.venv/bin/python -c "import segfacet.eval.per_mode,
  segfacet.eval.severity_ladder"`) and printed every metric's/ladder's
  `(failure_mode, condition)`; all nine ladder homes (eight plus `fuse`) and
  all eight metric homes match this item's recorded table exactly.
  **Reviewer's minor finding (production's derivation lacked the test
  mirror's uniqueness guards) is moot**: there is no longer a
  production-side derivation to guard -- the values are literal, and the
  uniqueness/ambiguity checks live entirely in the test's own
  `_rule_a_home`/`_rule_b_home` helpers, which is where the item spec's
  adversarial cases (AC5/AC13 negative controls) already exercise them.
