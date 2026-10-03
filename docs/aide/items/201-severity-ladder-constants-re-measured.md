<!-- aide-template: item 3 -->
# Item 201 — Severity-ladder constants re-measured on the lordotic base

> **Created:** 2026-09-29 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (D4)
> **Queue:** [`../queue/queue-027.md`](../queue/queue-027.md) · Item 201
> **Objectives:** G2, G7
> **Suggested branch:** `aide/201-severity-ladder-constants-re-measured`

---

## Description

`segfacet.eval.severity_ladder` scores a set of severity ladders (one
perturbation operator at growing severity) against the per-mode metrics of
`segfacet.eval.per_mode`. It freezes what it measures in three ratchet
constants: `RECORDED_MARGINS`, `KNOWN_CROSS_MODE_COUPLINGS` and
`MODE_LADDER_DISPOSITIONS`. Roadmap Stage 33 D4 asks for those constants to be
re-measured on the lordotic base, covering the split operators. Two recorded
defects are routed here:

1. **No ladder covers mode 3's operators** (`insights.md`, insight
   2026-09-22-b0d2). Item 166 added `split`, and item 174 added
   `split_own_label`, after item 154 fixed the ladder set on 2026-09-16.
   `score_harness(run_severity_harness()).per_ladder` has neither key.
2. **Mode 1's disposition reads the pre-189 homing** (`insights.md`, insight
   2026-09-28-1abd). `MODE_LADDER_DISPOSITIONS[1].ladders` is derived from
   the designated metric's home. `displace` designates
   `unanchored_foreground_fraction`, a mode-1 metric, so it is still listed
   under mode 1. Since item 189 the `displace` ladder is homed on the
   `displaced_vertebra` condition (`_LADDER_HOMES["displace"] ==
   (None, "displaced_vertebra")`). The reason text still says "Mode 1 keeps
   both displace and fragment".

**The change.**

- Two primary ladders join `SEVERITY_LADDERS`, one per mode-3 sub-type.
  `split` sweeps `donated_fraction`. `split_own_label` sweeps the number of
  shifted labels. Both designate `mislabelled_volume_fraction`, and both are
  homed on mode 3 by rule (b).
- `score_harness` learns that one metric may be designated by more than one
  ladder. Until now it assumed one ladder per metric.
- Every ratchet constant is re-transcribed from one fresh run, which adds a
  `split` coupling.
- Mode 1's disposition is re-derived from the ladders' own homes
  (`LadderSpec.failure_mode`), so it lists `fragment` only.

**Measured on this tree (2026-09-29, scratch run, lordotic default base).**
The numbers below come from `run_severity_harness()` plus the two candidate
ladders, before any code change. The builder re-transcribes from its own run.

| ladder | designated metric | margin | coupling ≥ 0.25 |
|---|---|---|---|
| displace | unanchored_foreground_fraction | inf | — |
| fragment | min_dominant_component_fraction | inf | — |
| inject_islands | rogue_island_count | 118.4907 | — |
| relabel_swap | mislabelled_volume_fraction | inf | — |
| remove_level | missing_level_count | inf | — |
| crop_at_border | fov_clipped_label_count | 0.325301 | unanchored_foreground_fraction 3.07408 |
| sequence_break | out_of_order_label_count | inf | — |
| split *(new)* | mislabelled_volume_fraction | 1 / 0.389599 ≈ 2.5667 | min_dominant_component_fraction 0.389599 |
| split_own_label *(new)* | mislabelled_volume_fraction | inf | — |

The seven existing values match the recorded ones (118.4, 0.3253, 3.075), so
item 173's transcription of 2026-09-23 still holds. `split`'s rungs read
`mislabelled_volume_fraction` 0, 0.025264, 0.041573, 0.066837, 0.083786 and
`min_dominant_component_fraction` 1.0, 0.887624, 0.827586, 0.749100,
0.704289. `split_own_label`'s rungs read `mislabelled_volume_fraction` 0,
0.159898, 0.355932, 0.558363, and every other metric is flat.

**Not in scope.**

- No new per-mode metric. Mode 3 has no metric home, and its ladders designate
  an existing metric (A2).
- No ladder for `remove_level_relabel`, `crop_fov` or `identity`. `fuse`
  stays supplementary.
- No change to any operator, metric, rule, the corpus, or `per_mode.py`.
- No new `MODE_LADDER_DISPOSITIONS` entry (see Left open).

## Acceptance Criteria

- [ ] **AC1: the split operators are scored.** The key set of
  `score_harness(run_severity_harness()).per_ladder` contains both `"split"`
  and `"split_own_label"`, as one subset check against the live harness.
- [ ] **AC2: the `split` ladder passes.** In that live verdict,
  `per_ladder["split"].failures == ()`. This covers monotonicity, strict
  change at every rung, being the designated metric's own driver, and both
  ratchets.
- [ ] **AC3: the `split_own_label` ladder passes.** In that live verdict,
  `per_ladder["split_own_label"].failures == ()`.
- [ ] **AC4: every recorded margin is a fresh measurement.** For every operator
  in `SEVERITY_LADDERS`, `RECORDED_MARGINS[operator]` is the live verdict's
  `margin`, rounded down to 4 significant figures. An infinite margin is
  recorded as exactly `math.inf`, and only an infinite margin is.
- [ ] **AC5: the coupling set is what is measured.** The set of
  `(ladder_operator, foreign_metric)` pairs in `KNOWN_CROSS_MODE_COUPLINGS`
  equals the set of `(operator, metric)` pairs in the live verdict where
  `metric` is not the ladder's designated metric and
  `per_ladder[operator].responses[metric] >= COUPLING_THRESHOLD`.
- [ ] **AC6: every recorded coupling is a fresh measurement.** Each
  `KNOWN_CROSS_MODE_COUPLINGS` entry's `recorded_response` is the live
  verdict's `per_ladder[ladder_operator].responses[foreign_metric]`, rounded
  up to 4 significant figures.
- [ ] **AC7: mode 1's disposition follows the ladders' homes.**
  `MODE_LADDER_DISPOSITIONS[1].ladders` equals the tuple of `SEVERITY_LADDERS`
  operators, in registry order, whose `LadderSpec.failure_mode == 1`. On
  this tree that tuple is `("fragment",)`, so the condition-homed `displace`
  is not listed.

## Assumptions

- **A1 (reading of the queue's "every registered operator that designates a
  metric"):** this means the two split operators the queue names become primary
  ladders, so they appear in `per_ladder`. It does not mean every
  perturbation-registry name gets a ladder. `identity` has nothing to
  measure. `fuse` stays supplementary, because it shares `fragment`'s metric
  and was deliberately kept out of the cross-mode matrix by item 100.
  `remove_level_relabel` and `crop_fov` were not named by the queue (see
  Left open).
- **A2 (designated metric):** both split ladders designate
  `mislabelled_volume_fraction`. Both sub-types put part of one vertebra
  under another label, and that is what this metric counts. It is also the
  only laddered metric `split_own_label` moves (every other span is 0.0,
  measured 2026-09-29). `split` also moves `min_dominant_component_fraction`,
  because the donated cap is a second body of the neighbour label. That
  response (0.389599 against `fragment`'s span) is at or above
  `COUPLING_THRESHOLD`, so it is recorded as a coupling, not hidden.
  Designating `min_dominant_component_fraction` for `split` instead was
  rejected for two reasons. It would split mode 3's two sub-types across two
  metrics. It would also make `min_dominant_component_fraction`'s rule-(b)
  home derivation in `tests/test_153_eval_harness_rekey.py`
  (`_metric_to_operator`) ambiguous, because that metric has no rule-(a)
  citation. `mislabelled_volume_fraction` has one (mode 8), so rule (b) is
  never consulted for it.
- **A3 (`split` axis):** the ladder uses the corpus's own pair, target 23
  (L4) → neighbour 24 (L5), with `donated_fraction` at 0.1, 0.2, 0.3 and 0.4.
  The corpus case sits at 0.2. The designated metric strictly increases over
  those rungs (values under Description).
- **A4 (`split_own_label` axis):** the severity axis is the number of shifted
  present labels (`target_label` 21, 22, 23 → 2, 3, 4 labels at or below the
  target shift down by one), at the default `donated_fraction` 0.2. It is
  kind `"affected-label-count"`. A `donated_fraction` axis was rejected
  because, measured on target 23 at 0.1/0.2/0.3/0.4,
  `mislabelled_volume_fraction` *decreases* (0.574672, 0.558363, 0.533099,
  0.516150). The metric counts the shifted remainder, which shrinks as the
  cap grows, so that axis is non-monotone in the metric's declared direction.
  A `target_label=20` rung was rejected because it reads 0.0: the shifted
  label 19 (T12) is not a GT label, so that rung would plateau with rung 0.
- **A5 (scoring a shared designated metric):** the fix is in
  `score_harness`, not in the ladder set. Each ladder's response to **its own
  spec-designated metric** (`SEVERITY_LADDERS[op].designated_metric`) uses
  that ladder's own span as the denominator, so it is exactly 1.0, as the
  module docstring already defines `response(m, m)`. A **foreign** metric's
  denominator is its *reference ladder's* span. The reference ladder is the
  first ladder in `harness.ladders` order that designates the metric, so the
  seven existing ladders keep their denominators. An `assignment` override
  that maps a ladder to a metric other than its spec-designated one still
  uses the reference ladder's span. That keeps the best-driver check, which
  is what item 100's AC18 swap negative control relies on, exactly as it
  was.
- **A6 (disposition derivation):** the queue says "re-derive each
  disposition from the ladders' current homes". This is read as
  `LadderSpec.failure_mode`, the rule-(b) ladder home, and no longer the
  designated metric's home. Item 154 A3 kept the two apart: a *response*
  still speaks to the metric home. The disposition records which ladders
  measure a mode, and since item 189 a condition-homed ladder measures a
  condition, not mode 1. Only the one existing entry (mode 1) is
  re-derived.
- **A7:** the dependencies (items 166, 173, 174, 189) are all merged (✅).
  Nothing here pins an unbuilt interface, so there is no claim-time
  re-check.

## Implementation Steps

All in `src/segfacet/eval/severity_ladder.py`. No dependency is added, and
every measurement goes through the existing `run_severity_harness` /
`score_harness` / `_apply_steps`.

1. **Homes.** Add `"split": (3, None)` and `"split_own_label": (3, None)` to
   `_LADDER_HOMES` (rule (b): `SPECIFICATION[3].corpus_cases` holds cases
   `split` and `split_own_label`, measured 2026-09-29).
2. **`_split_ladder()`.** Build it the same way as `_displace_ladder`. Rung 0
   plus four rungs of `("split", {"target_label": 23, "neighbour_label": 24,
   "donated_fraction": f})` for f in 0.1, 0.2, 0.3, 0.4. Set
   `designated_metric="mislabelled_volume_fraction"`,
   `severity_parameter="donated_fraction"` and `severity_kind="continuous"`.
   The rationale names the corpus pair.
3. **`_split_own_label_ladder()`.** Rung 0 plus three rungs of
   `("split_own_label", {"target_label": t})` for t in 21, 22, 23, at
   severities 2.0, 3.0 and 4.0. Set
   `designated_metric="mislabelled_volume_fraction"`,
   `severity_parameter="n_shifted_labels"` and
   `severity_kind="affected-label-count"`. The rationale records A4's two
   rejections with their measured values.
4. **Register** both in `SEVERITY_LADDERS`, after `sequence_break`, so the
   seven existing ladders stay first and keep their reference-ladder role
   (A5).
5. **`score_harness`.** Build `owning_operator` first-wins (`setdefault` over
   `ladders`). When computing `responses`, use the ladder's own span as the
   denominator for `f == lr.spec.designated_metric`. Every other `f` keeps
   the reference ladder's span. Replace the "total and one-to-one" comment
   with the shared-metric rule.
6. **Re-measure.** Run `score_harness(run_severity_harness())` once, then:
   - Transcribe every `RECORDED_MARGINS` value, rounded down to 4 s.f.
     (inf as inf), adding `split` and `split_own_label`.
   - Transcribe every coupling, rounded up to 4 s.f.
   - Add `CrossModeCoupling(ladder_operator="split",
     foreign_metric="min_dominant_component_fraction", ...)`. Its cause
     says the donated cap leaves the neighbour label as two disconnected
     bodies.
   - Set `_MEASUREMENT_PROVENANCE.measured_on` to the run's date.
   - Update the transcription comment block to name item 201's run.
   - Re-check the "~20.5 mm max displacement_mm for label 22" figure in the
     `crop_at_border` coupling's cause and comment against the current
     `displace` operator (item 177 changed its direction). Correct it, or
     drop the number if it cannot be re-measured. Never carry it over
     unverified.
   - Record the printed run under Decisions & Trade-offs.
7. **Mode 1's disposition.** Derive `ladders` as `tuple(op for op in
   SEVERITY_LADDERS if SEVERITY_LADDERS[op].failure_mode == 1)`. Rewrite
   `reason` to cover three points:
   - Mode 1 is measured by `fragment` alone.
   - `displace` moved to the `displaced_vertebra` condition (item 189).
   - Item 141's base-widening question stays answered "not widened".
   Update `ModeLadderDisposition.ladders`' docstring (ladder home, not metric
   home).
8. **Prose in the same file.** Update these docstrings and comments to the
   nine ladders and the shared-metric rule:
   - the module docstring's ladder table ("The seven ladders"),
   - the "Why three ladders have no continuous knob" section (add
     `split_own_label`),
   - "Ladder home vs. metric home" (now also `displace`, `split` and
     `split_own_label`),
   - "Foreign metrics",
   - "Mode 1's ladders",
   - `HarnessResult`'s docstring,
   - the `SEVERITY_LADDERS` comment.

## Authorised paths

**May change:**

- `src/segfacet/eval/severity_ladder.py` — the ladders, `score_harness`, the constants and their prose
- `tests/test_201_severity_ladder_remeasured.py` — this item's AC tests
- `tests/test_100_severity_ladder.py` — reconcile the "exactly seven operators" pins (AC2, AC16)
- `tests/test_153_eval_harness_rekey.py` — reconcile `_OPERATORS` (AC17) and the one-to-one designated-metric assertion (AC18)
- `tests/test_154_ladder_remeasurement.py` — reconcile the metric-home disposition derivation (AC14 and its adversarial)
- `tests/test_171_literal_negative_controls.py` — reconcile the helper that recomputes the disposition from metric homes (AC6 and its pre-item body)

**Asserts against:**

- `src/segfacet/eval/per_mode.py` — AC1–AC6 measure every metric through `compute_per_mode_metrics` and its declared directions
- `src/segfacet/synth/component_shape.py` — AC2/AC3 measure the `split` and `split_own_label` operators' output

## Testing Strategy

New module `tests/test_201_severity_ladder_remeasured.py`. It uses one
module-scoped fixture holding `score_harness(run_severity_harness())`, because
the harness run is expensive. That module has one test each for **AC1, AC2,
AC3 and AC7**.

- AC7 recomputes the expected tuple live from `SEVERITY_LADDERS` and
  `LadderSpec.failure_mode`. Under the old metric-home derivation it would
  read `("displace", "fragment")` and fail.

**AC4, AC5 and AC6 are already tested, and no new test is written for
them.** Those tests iterate `SEVERITY_LADDERS` and
`KNOWN_CROSS_MODE_COUPLINGS` live, so they cover the split ladders once the
ladders are registered:

- AC4 → `tests/test_154_ladder_remeasurement.py::test_ac10_each_margin_is_a_fresh_transcription`
- AC5 → `tests/test_154_ladder_remeasurement.py::test_ac8_coupling_set_is_what_is_measured`
- AC6 → `tests/test_154_ladder_remeasurement.py::test_ac9_each_coupling_value_is_a_fresh_transcription`

Writing them again in this module would add a second harness run for claims
the suite already recomputes.

**Adversarial cases.** None new. The one failure mode A5 introduces is
guarded by the existing
`tests/test_100_severity_ladder.py::test_ac18_negative_control_swapping_modes_2_and_3_fails`.
That failure mode would be the own-span denominator being applied to an
`assignment` override instead of only to the spec-designated metric, which
would make the best-driver check vacuous and let a swapped assignment pass.
The existing test must still fail the swapped assignment.

**Existing tests to reconcile** (stale-assumption sweep of `tests/`,
2026-09-29). Each one pins the old ladder set or the old derivation:

- `tests/test_100_severity_ladder.py::test_ac2_key_set_is_exactly_the_seven_operators`
  and `::test_ac16_recorded_margins_has_all_seven_ladders` compare against the
  seven legacy operators. Keep `_LADDER_OPERATORS` (the legacy-int helpers use
  it) and compare against it plus `{"split", "split_own_label"}`.
- `tests/test_153_eval_harness_rekey.py::test_ac17_ladders_are_keyed_by_operator`
  (`_OPERATORS`, seven entries): add the two split operators.
  `::test_ac18_designated_metrics_cover_the_registry` asserts
  `len(designated) == len(set(designated))`. Drop the uniqueness half (A5),
  and keep the coverage half.
- `tests/test_154_ladder_remeasurement.py::test_ac14_disposition_ladders_are_derived_from_the_homes`
  derives from metric homes. Derive it from `LadderSpec.failure_mode`.
  `::test_adv_ac14_rehoming_a_metric_changes_the_derived_tuple` re-homes a
  metric, which no longer moves the disposition. Re-point it to re-home a
  **ladder** (patch a non-mode-1 `LadderSpec.failure_mode` to 1) so it stays
  non-vacuous.
- `tests/test_171_literal_negative_controls.py`: `_patch_rogue_island_home_to_1`,
  `test_ac6_h6_survives_rogue_island_count_already_in_mode_1` and
  `_h6_pre_item_body` recompute mode 1's disposition from metric homes, and
  AC6 runs test_154's adversarial. Reconcile them together with test_154's
  adversarial so the H6 control still has a defect to detect.

Checked and **not** stale: `tests/test_102_stage18_validation.py` (iterates
its own seven), `tests/test_195_force_overlap_removed.py` (laddered-metric
set unchanged), `tests/test_189_spline_offset_condition.py` and
`tests/test_112_overlap_short_circuit.py` (read the `displace` ladder only).

## Validation

Print the harness summary and read it:

```
.venv/bin/python -c "from segfacet.eval.severity_ladder import run_severity_harness, score_harness; print(score_harness(run_severity_harness()).summary())"
```

Expected: `passed=True`, and nine ladders listed. `split` is listed as
COUPLED with `min_dominant_component_fraction`, and `split_own_label` as
strict with `margin=inf`. No profile is needed.

## Dependencies

- Item 166 — the `split` operator and its mode-3 corpus case (✅).
- Item 173 — the lordotic base the constants are measured on (✅).
- Item 174 — `split_own_label` and the re-authored `split` (✅).
- Item 189 — `displace` re-homed onto the `displaced_vertebra` condition (✅).

**Downstream:** item 203's maintainer brief and item 204's stage validation
read the re-measured constants. Neither pins a value from this item.

## Decisions & Trade-offs

- **Re-measurement run (2026-09-29, `score_harness(run_severity_harness())`,
  `passed=True`, nine ladders).** Margins: displace inf, fragment inf,
  inject_islands 118.49074, relabel_swap inf, remove_level inf,
  crop_at_border 0.3253006, sequence_break inf, split 2.5667396,
  split_own_label inf. Couplings >= 0.25: crop_at_border ->
  unanchored_foreground_fraction 3.0740799, split ->
  min_dominant_component_fraction 0.3895993. Transcribed: margins rounded down
  to 4 s.f. (118.4, 0.3253, split 2.566), couplings rounded up (3.075,
  0.3896). The seven existing values are unchanged from item 173's.
- **"~20.5 mm" displace figure dropped.** It was not re-measured against the
  item 177 `displace` operator; the `crop_at_border` coupling's cause now
  cites the measured top-rung value instead (`unanchored_foreground_fraction`
  0.132 at `displacement_mm=16`).
- **`score_harness`** uses the ladder's own span for its spec-designated
  metric and the first-registered designating ladder's span for foreign
  metrics (A5), as implemented via `owning_operator.setdefault`.

- **Left open:** whether mode 3 (and the `displaced_vertebra` /
  `fov_truncation` conditions) get their own `MODE_LADDER_DISPOSITIONS`
  entry. The table has only ever recorded mode 1's base-widening decision.
  No consumer in this queue reads a disposition for any other mode, and the
  prototype posture adds none ahead of need.
- **Left open:** ladders for `remove_level_relabel` and `crop_fov`. The queue
  names only the split operators. Both operators' metrics already have
  ladders (`missing_level_count`, `fov_clipped_label_count`), so they would
  be further sharers under A5's rule. They are a later measurement item if
  one is wanted.
