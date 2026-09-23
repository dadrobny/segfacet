<!-- aide-template: item 1 -->
# Item 154 — Re-measure the ladders, the cross-mode constants and mode 1's anchor

> **Created:** 2026-09-16 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update
> **Queue:** [`../queue/queue-021.md`](../queue/queue-021.md) · Item 154
> **Objectives:** G7, G8
> **Suggested branch:** `aide/154-re-measure-the-ladders-the`

---

## Description

Roadmap Stage 31 D3, second half. Item 153 re-keyed the Stage-18 severity-ladder
harness (`segfacet.eval.severity_ladder`) by metric name and operator, and moved
every number over unchanged. This item re-measures those numbers, records what
each was measured on, and settles what item 153 recorded but did not decide.

It has five parts.

### 1. Re-measured constants, with provenance

`KNOWN_CROSS_MODE_COUPLINGS` (two entries) and `RECORDED_MARGINS` (eight
entries, five of them `inf`) are **re-measured from a clean tree, never carried
over**. The builder runs `run_severity_harness()` and `score_harness()` and
transcribes the result with the module's own rounding rule: responses rounded
**up** to 4 significant figures, margins rounded **down** to 4 significant
figures, `inf` kept as `inf`. The numbers may come out the same as before. What
matters is that each is transcribed from a fresh run, and the tests prove it
(AC8–AC10).

Each entry now carries a `MeasurementProvenance` record: the corpus the base
belongs to, the base-fixture parameters, and the ISO date of the measurement.
The harness has no manifest to point at. Every ladder is built in memory from
`build_clean_spine(**_BASE_PARAMS)`, which is the geometric corpus's default
base. So the provenance names `"geometric"` and carries the base parameters,
and a test checks those parameters against the corpus recipe's own
(`synth.corpus._DEFAULT_BASE_PARAMS`).

### 2. What "foreign" means now that homes are not exclusive

Item 153 recorded that one mode can have two metrics (mode 1:
`unanchored_foreground_fraction`, `min_dominant_component_fraction`), and asked
whether a metric sharing the ladder's mode still counts as foreign in the margin.
**Decision (A2): "foreign" stays "every metric other than the ladder's designated
metric".** The margin measures how well a ladder isolates *its metric*. That is
defined without any mode home, so it cannot drift when Stage 32 moves a home.

The finding that goes with the decision: on this base, leaving out same-home
metrics changes **no** margin. Only `displace` and `fragment` share a home
(mode 1), and both have margin `inf`. AC12 measures this, so if a later change
makes the choice matter, the suite says so.

Other overlaps that item 153 noted cannot be measured on this harness.
`unanchored_foreground_fraction` also rises under mode 7,
`mislabelled_volume_fraction` under modes 3 and 12, and
`min_dominant_component_fraction` reads a path mode 14 also cites. None of
modes 3, 7, 12 and 14 has a ladder, so there is no response to measure. This is
recorded, not guessed.

### 3. A ladder's home versus its metric's home

Item 153 left two ladders whose home (rule (b): the specification mode that owns
the operator's corpus case) differs from the home of their designated metric:

- `relabel_swap`: ladder mode 9, metric `mislabelled_volume_fraction` mode 8.
- `fuse`: ladder mode 2, metric `min_dominant_component_fraction` mode 1.

**Decision (A3): both fields stay, and they answer different questions.**
`LadderSpec.failure_mode` says which mode the operator's corpus case is
designated to produce. The mode a ladder's *measured response* speaks to is its
designated metric's home, `PER_MODE_METRIC_SPECS[designated_metric].failure_mode`.
Every number the ratchet scores is a metric response, so the harness's mode
claims are read off the metric. Neither value changes. The module docstring and
the `LadderSpec` docstring say this in so many words. No acceptance criterion
covers it: it is a definition, not a fact about live state.

### 4. Mode 1's ladder base (absorbs item 141)

Stage 20's deferred item 141 was to widen the mode-1 ladder base so that the
metric's swing is set by the perturbation, not the fixture's FOV walls. Under
the old ids, "mode 1" was the `displace` ladder, and the aim was to clear old
mode 6's (`crop_at_border`) specificity shortfall. After the item-150 sign-off,
mode 1 is *Segmentation accuracy*, and two ladders measure it: `displace`
(rigid translation, which is over-segmentation plus under-segmentation) and
`fragment` (a body cut into same-label pieces, which the mode-1 definition names
explicitly). `crop_at_border` is homed on the `fov_truncation` **condition**, not
on a mode.

**Decision (A4): mode 1 keeps both ladders on the shared corpus base, and the
base is not widened.** The record is `MODE_LADDER_DISPOSITIONS[1]`, with
disposition `"re-derived"`. The reasoning:

- The shortfall item 141 aimed at is `crop_at_border` → `unanchored_foreground_fraction`.
  That is now a **condition** ladder moving a mode-1 metric.
- Mode 1's own discriminator separates the FOV-truncation condition from mode 1
  by the image face.
- The coupling's recorded cause is an operator artefact: `crop_at_border`
  translates each cropped body.
- Widening the `displace` base would enlarge the denominator of every response
  onto `unanchored_foreground_fraction`, but would change nothing that
  `crop_at_border` does. It would improve a ratio without improving a claim.

The coupling stays a recorded coupling, with a re-measured value.

### 5. Two corrections: the rank premise and mode 1's anchor

**The rank premise.** `severity_ladder.py`'s module docstring and the
`sequence_break` ladder's `rationale` claim that ``rank(v) == v - 1`` for every
value 1–24. That is false: `labels.CANONICAL_ORDER` puts `T13` at index 19, so
`L1`–`L5` (values 20–24, the ladder base) have rank equal to their value. The
harness orders centroids by ascending label value (`pipeline.py`, "Ascending-label
order"), and `features/relationships.py` flags a label whose rank is below the
running maximum.

With the premise corrected, two things follow (the finding, AC17):

- **Part of the conclusion survives.** Rank is still *strictly increasing* over
  values 1–24 (ranks 0–18, then 20–24), so no relabel that stays inside 1–24 can
  create a descent.
- **"Structurally capped at 1.0" does not survive.** `sequence_break` takes
  `target_label` and `new_label`. After value 27 (`Cocc`, rank 32), both 28
  (`T13`, rank 19) and 29–33 (`S2`–`S6`, ranks 27–31) are descents. So the
  cumulative relabels 24→28, 23→27, 22→29 give the value sequence
  20, 21, 27, 28, 29, with ranks 20, 21, 32, 19, 27, which is **two**
  out-of-order labels (derived by hand from `labels.py`; AC17 measures it).

The ladder has 2 rungs because it has one step with the default `new_label=28`,
not because of a structural limit. This item **records** that finding and
**does not re-grade the ladder**: `DEGENERATE_LADDERS` and the 2-rung shape stay
as they are (A5). A graded `sequence_break` ladder is an option for Stage 32 and
is captured as an insight.

**Mode 1's anchor.** `feature_docs.MODE_ANCHOR_PATHS[1]` lists
`stage3.per_label_offsets[].offset_mm`. At the item-150 sign-off, `mislabel`'s
spline-offset detector was classified as serving no mode, and the only rule
that consumes that path is `mislabel`. So mode 1's anchor and mode 1's mechanism
disagree. (`mislabel` itself declares the path `bookkeeping`.) The re-anchor
drops that path:
`MODE_ANCHOR_PATHS[1] == ("per_label.{label}.components.fragmentation_index",)`.
That is the record path `min_dominant_component_fraction` reads, and
`fragmentation`, one of mode 1's intended rules, consumes it as `signal`.
`unanchored_foreground_fraction` is computed candidate-vs-GT and reads no record
path, so it has no anchor, and that is stated in the comment.

`ModeSpec.__post_init__` requires every `stage18-metric-anchor` candidate
feature to be listed in `MODE_ANCHOR_PATHS[mode.id]`. So the re-anchor **forces**
one field change in `_MODE_1`: the `offset_mm` candidate feature's `role` goes
from `"stage18-metric-anchor"` to `"hypothesised"`. The path stays in the list.
This is the only `ModeSpec` edit, and A6 explains why it is inside the queue's
scope fence.

### Not in scope

- **No mode content changes.** A `ModeSpec`'s definition, discriminator,
  mechanism, severity, observability, authored status, intended rules, corpus
  cases and `expected_firing` do not move. No mode is added or removed. No rule
  declaration changes (`reference_delta`'s declared mode 1 included; see the
  insight captured with this spec). A re-measurement that contradicts a
  signed-off mode is recorded in `insights.md` and handed back.
- **No re-grading of the `sequence_break` ladder, and no widened base** (A4, A5).
- **No change to the margin or response arithmetic, `COUPLING_THRESHOLD` or the
  ratchet tolerances.**
- **No new operator, corpus case or manifest field.**
- **Recording the constants in `progress.md`** is item 161's job.
- **Production reads nothing under `tests/`**, at import time or otherwise. The
  provenance and dispositions are literals (the item-153 reviewer finding;
  AC22).

## Acceptance Criteria

"The harness run" means `score_harness(run_severity_harness())` together with
the `HarnessResult` it scored, computed fresh in the test session. "A home"
means the pair `(PER_MODE_METRIC_SPECS[m].failure_mode, PER_MODE_METRIC_SPECS[m].condition)`.
"Every provenance" means the `provenance` of each `KNOWN_CROSS_MODE_COUPLINGS`
entry, each value of `RECORDED_MARGIN_PROVENANCE`, and the `provenance` of each
value of `MODE_LADDER_DISPOSITIONS`. `sl` is `segfacet.eval.severity_ladder`.

No AC below closes a Stage 31 acceptance criterion on its own. Criterion 3
combines item 153's keying claim with this item's re-measured constants, and
item 161 attests it against both. So no AC carries a *(closes …)* annotation.

### Provenance

- [ ] **AC1: Couplings carry provenance.** Every `sl.KNOWN_CROSS_MODE_COUPLINGS` entry has a `provenance` attribute that is an instance of `sl.MeasurementProvenance`.
- [ ] **AC2: Every margin has provenance.** `set(sl.RECORDED_MARGIN_PROVENANCE) == set(sl.RECORDED_MARGINS)`, and every value is an instance of `sl.MeasurementProvenance`.
- [ ] **AC3: The corpus is named.** Every provenance has `corpus == "geometric"`.
- [ ] **AC4: The base fixture is the harness's base.** For every provenance, `base_params`, with each sequence value converted to a tuple, equals `sl._BASE_PARAMS` converted the same way.
- [ ] **AC5: The harness base is the geometric corpus base.** `sl._BASE_PARAMS`, with sequence values converted to tuples, equals `segfacet.synth.corpus._DEFAULT_BASE_PARAMS` converted the same way.
- [ ] **AC6: Each measurement is dated after the carry-over.** Every provenance's `measured_on` parses with `datetime.date.fromisoformat`, is on or after `2026-09-16`, and is on or before `datetime.date.today()`.

### Re-measured values

- [ ] **AC7: The re-measured ratchet passes.** The harness run's verdict has `passed is True`.
- [ ] **AC8: The coupling set is what is measured.** The set of `(ladder_operator, foreign_metric)` pairs in `sl.KNOWN_CROSS_MODE_COUPLINGS` equals the set of `(operator, metric)` pairs in the harness run where `metric` is not the ladder's designated metric and `per_ladder[operator].responses[metric] >= sl.COUPLING_THRESHOLD`.
- [ ] **AC9: Each coupling value is a fresh transcription.** For every coupling, let `r` be the measured `per_ladder[ladder_operator].responses[foreign_metric]`. Then `r <= recorded_response`, and `recorded_response - r < 10 ** (floor(log10(r)) - 3)` (the gap is under one unit of the 4th significant figure).
- [ ] **AC10: Each margin is a fresh transcription.** For every operator, let `g` be the measured `per_ladder[operator].margin`. Then `g` is `inf` exactly when `sl.RECORDED_MARGINS[operator]` is `inf`. When `g` is finite, `RECORDED_MARGINS[operator] <= g` and `g - RECORDED_MARGINS[operator] < 10 ** (floor(log10(g)) - 3)`.
- [ ] **AC11: Couplings are not self-couplings.** For every coupling, `foreign_metric != sl.SEVERITY_LADDERS[ladder_operator].designated_metric`.

### Foreign-set decision

- [ ] **AC12: Excluding same-home metrics changes no margin.** For every operator in the harness run, compute the margin a second way: `1 / max` of the responses over metrics whose home differs from the designated metric's home (`inf` if that max is `0`). The result equals `per_ladder[operator].margin`, where `inf` equals `inf` and finite values agree to `rel=1e-12`.

### Mode 1's ladder disposition (item 141)

- [ ] **AC13: One disposition, for mode 1.** `set(sl.MODE_LADDER_DISPOSITIONS) == {1}`.
- [ ] **AC14: Its ladders are derived from the homes.** `sl.MODE_LADDER_DISPOSITIONS[1].ladders` equals the tuple, in `SEVERITY_LADDERS` order, of every operator whose designated metric has `PER_MODE_METRIC_SPECS[...].failure_mode == 1`.
- [ ] **AC15: The disposition is "re-derived".** `sl.MODE_LADDER_DISPOSITIONS[1].disposition == "re-derived"`, and that value is in `sl.MODE_LADDER_DISPOSITION_VALUES == ("re-derived", "no-ladder")`.

### The rank premise

- [ ] **AC16: The false literal is gone from production.** No `*.py` file under `src/` contains the substring `rank(v) == v - 1`. The test builds the needle by concatenation so it does not match its own source.
- [ ] **AC17: The finding is measured.** Apply the steps `sequence_break(target_label=24, new_label=28)`, then `(target_label=23, new_label=27)`, then `(target_label=22, new_label=29)`, cumulatively, to `build_clean_spine(**sl._BASE_PARAMS).seg_img`. Put the result through `extract_feature_record` and `compute_per_mode_metrics`. The resulting `out_of_order_label_count` equals the number of descents counted independently: take the present label values in ascending order, map each through `DEFAULT_LABEL_MAP` to its `CANONICAL_ORDER` index, and count the entries that fall below the running maximum. That count is `>= 2`.
- [ ] **AC18: The "structural" claim is withdrawn.** Neither `sl.SEVERITY_LADDERS["sequence_break"].rationale` nor `sl.__doc__` contains the case-insensitive substring `structural`.

### Mode 1's anchor

- [ ] **AC19: The anchor is non-empty.** `len(feature_docs.MODE_ANCHOR_PATHS[1]) >= 1`.
- [ ] **AC20: Mode 1's rules consume its anchor.** For every path in `feature_docs.MODE_ANCHOR_PATHS[1]`, at least one rule named in `failure_modes.SPECIFICATION[1].intended_rules` declares it, through `heuristics.rule.iter_rule_declarations()`, as a `ConsumedPath` with `role == "signal"`.
- [ ] **AC21: Candidate-feature anchor roles mirror the anchor map.** The set of `SPECIFICATION[1].candidate_features` paths with `role == "stage18-metric-anchor"` equals `set(feature_docs.MODE_ANCHOR_PATHS[1])`.

### Import hygiene

- [ ] **AC22: No test tree read at import.** For each of `segfacet.eval.severity_ladder`, `segfacet.eval.per_mode` and `segfacet.feature_docs`, importing the module in a fresh `sys.executable` subprocess records no `open` audit event (`sys.addaudithook`, installed before the import) whose path has a component equal to `tests`.

## Assumptions

- **A1 (provenance shape).** `MeasurementProvenance` is a frozen dataclass
  `(corpus: str, base_params: Mapping[str, Any], measured_on: str)`, exported
  from `severity_ladder` and re-exported from `segfacet.eval`. It is a required
  field of `CrossModeCoupling`, with no default, so a coupling without one cannot
  be built. `RECORDED_MARGINS` keeps its `Mapping[str, float]` type, because
  `score_harness`, `test_100` and `test_102` read it as floats. Its provenance
  lives in a parallel `RECORDED_MARGIN_PROVENANCE: Mapping[str, MeasurementProvenance]`.
  The queue asks for a "provenance string naming corpus and date". A structured
  record is used instead, so that AC3–AC6 compare each field with its source
  rather than looking for tokens in a sentence.
- **A2 (foreign set).** Margins and responses keep item 153's definition:
  foreign means every metric except the designated one. AC12 records that
  excluding same-home metrics is immaterial on this base today. If AC12 goes red
  after a legitimate change, the decision must be re-opened in a spec. The test
  must not be edited to agree.
- **A3 (ladder home vs metric home).** `LadderSpec.failure_mode` stays rule (b).
  The mode a ladder's response measures is its designated metric's home.
  Nothing new is stored. `relabel_swap` (9 vs 8) and `fuse` (2 vs 1) are the two
  ladders where the two differ. That is documented, not resolved in code.
- **A4 (item 141 disposition).** Mode 1 keeps `displace` and `fragment` on
  `_BASE_PARAMS`. There is no widened or per-ladder base, for the reasons in the
  Description. `ModeLadderDisposition` is a frozen dataclass
  `(mode: int, ladders: Tuple[str, ...], disposition: str, reason: str, provenance: MeasurementProvenance)`.
  `MODE_LADDER_DISPOSITIONS` is keyed only by mode 1. Other modes get an entry
  only when a later item decides their ladder.
- **A5 (sequence_break not re-graded).** The queue asks for the finding to be
  *recorded*. Re-grading would change rung counts, `DEGENERATE_LADDERS`, and
  pins in `test_100`/`test_102`, which goes beyond correcting a claim. The
  rationale keeps the substring `28`, which `test_100` AC12 reads, and states
  both halves: rank is strictly increasing over 1–24; relabels to 27–33 produce
  more than one descent; the 2 rungs follow from the single default step.
  Measured by hand from `labels.py` on 2026-09-16. If AC17 measures fewer than 2,
  hand back: the premise analysis is wrong.
- **A6 (the one ModeSpec edit).** The queue fence lists the protected `ModeSpec`
  fields as definition, discriminator, mechanism, severity, observability and
  authored status, plus modes, rules and `expected_firing`. A candidate
  feature's `role` is not among them. It is bookkeeping that `ModeSpec`
  validates against `MODE_ANCHOR_PATHS`, and the queue's own re-anchor mandate
  cannot be met without changing it. So `_MODE_1`'s `offset_mm` candidate
  feature goes to `role="hypothesised"`, and the path stays listed. The
  regenerated `failure_modes.generated.*` diff must be exactly that one role
  (Validation step 3). If a human reads the role as signed-off content, this
  assumption is where to veto it.
- **A7 (re-anchor target).** The re-anchor is to
  `per_label.{label}.components.fragmentation_index` alone, not to a
  volume/extent path. The item-150 insight suggested `physical_volume_mm3`, but
  no Stage-18 metric reads a volume path. An anchor there would claim a metric
  anchor that does not exist, and it would need a second role flip, from
  hypothesised to anchor. `fragmentation_index` is already listed as an anchor
  and is what `min_dominant_component_fraction` reads.
- **A8 (downstream artifacts regenerate).** Removing `offset_mm` from
  `MODE_ANCHOR_PATHS[1]` changes the committed
  `traceability_matrix.generated.{json,md}` (mode 1's `anchor_paths`) and
  `feature_catalogue.generated.{json,md}` (that path's anchor-derived mode and
  `per_mode_metric` evidence). They are regenerated through each module's
  `main()`, written with `\n`, and the existing fresh-vs-committed tests keep
  holding.
- **A9 (engine 1.52.1, re-checked 1.59.0, re-checked 2.1.0).** Item 153 is merged (✅), so nothing blocks the claim.
  `aide scope` proves the authorised paths below.

## Implementation Steps

1. **`src/segfacet/eval/severity_ladder.py`**
   - Add `MeasurementProvenance` and `ModeLadderDisposition` (frozen), and
     `MODE_LADDER_DISPOSITION_VALUES = ("re-derived", "no-ladder")`.
   - Add a required `provenance` field to `CrossModeCoupling`.
   - Add `RECORDED_MARGIN_PROVENANCE` and `MODE_LADDER_DISPOSITIONS`, all
     literal. No manifest or `tests/` read.
   - Extend `__all__`.
2. **Re-measure from a clean tree.** On the committed item branch with a clean
   worktree, run `run_severity_harness()` and `score_harness()` from the venv.
   - Transcribe each coupling response rounded up to 4 s.f., and each margin
     rounded down to 4 s.f. (`inf` stays `inf`).
   - Set every `measured_on` to the run date.
   - Replace the "Item 153 (A5): every value below moved verbatim" comments with
     the measured run, recorded in this spec's Decisions section: every raw
     value, plus the coupling set at `COUPLING_THRESHOLD`.
   - Re-word the coupling `cause` strings only if the measurement contradicts
     them.
3. **Rewrite the docstrings in `severity_ladder.py`:**
   - the `sequence_break` bullet and the ladder's `rationale`, with the corrected
     rank premise and the two-descent finding, no `rank(v) == v - 1` literal, and
     no "structural" wording (keep `28`);
   - a short "Homes" paragraph for A3;
   - a "Foreign metrics" paragraph for A2;
   - a "Mode 1's ladders (item 141)" paragraph for A4.
4. **`src/segfacet/eval/__init__.py`**: re-export `MeasurementProvenance`,
   `ModeLadderDisposition`, `RECORDED_MARGIN_PROVENANCE`,
   `MODE_LADDER_DISPOSITIONS` and `MODE_LADDER_DISPOSITION_VALUES`.
5. **`src/segfacet/feature_docs.py`**
   - Set `MODE_ANCHOR_PATHS[1] = ("per_label.{label}.components.fragmentation_index",)`.
   - Rewrite the comment block to say:
     - mode 1's anchor is the record path its fragment metric reads;
     - `unanchored_foreground_fraction` is candidate-vs-GT and has no record
       anchor;
     - the spline-offset path was dropped because its only consumer, `mislabel`,
       serves no mode (item-150 sign-off).
6. **`src/segfacet/failure_modes.py`**: in `_MODE_1.candidate_features`, change
   the `stage3.per_label_offsets[].offset_mm` entry's `role` to
   `"hypothesised"`. Change nothing else in the module.
7. **Regenerate the committed artifacts**, in this order:
   - `.venv/bin/python -m segfacet.failure_modes`
   - `.venv/bin/python -m segfacet.catalogue`
   - `.venv/bin/python -m segfacet.traceability`

   Use default output paths. Then confirm the diffs match A6 and A8.
8. **Reconcile the existing tests** listed under Testing Strategy.
9. **Capture a `knowledge` insight** with the measured AC17 count, the relabel
   sequence that produced it, and "a graded `sequence_break` ladder is a Stage 32
   option". Take it from the actual measurement.

## Authorised paths

**May change:**

- `src/segfacet/eval/severity_ladder.py` — provenance, dispositions, re-measured constants, corrected docstrings
- `src/segfacet/eval/__init__.py` — re-exports of the new names
- `src/segfacet/feature_docs.py` — `MODE_ANCHOR_PATHS[1]` and its comment
- `src/segfacet/failure_modes.py` — the one `_MODE_1` candidate-feature role (A6)
- `docs/aide/failure_modes.generated.json` — regenerated for the role change
- `docs/aide/failure_modes.generated.md` — regenerated for the role change
- `docs/aide/traceability_matrix.generated.json` — regenerated for mode 1's anchor paths
- `docs/aide/traceability_matrix.generated.md` — regenerated for mode 1's anchor paths
- `docs/aide/feature_catalogue.generated.json` — regenerated for the offset path's anchor mode
- `docs/aide/feature_catalogue.generated.md` — regenerated for the offset path's anchor mode
- `tests/test_154_ladder_remeasurement.py` — this item's tests
- `tests/test_100_severity_ladder.py` — `CrossModeCoupling` construction and rationale pins, if any break
- `tests/test_102_stage18_validation.py` — `_EXPECTED_MARGINS` if a re-measured margin moves
- `tests/test_103_feature_catalogue.py` — offset-path anchor pins
- `tests/test_104_feature_catalogue_drift.py` — offset-path pin in the drift list
- `tests/test_137_mode_less_rule_disposition.py` — `1 in required_modes` rests on the offset anchor
- `tests/test_138_traceability_matrix.py` — AC32's `1 in required_modes` rests on the offset anchor

**Asserts against:**

- `src/segfacet/synth/corpus.py` — AC5 reads `_DEFAULT_BASE_PARAMS`
- `src/segfacet/labels.py` — AC17 counts descents from `CANONICAL_ORDER` and `DEFAULT_LABEL_MAP`
- `src/segfacet/heuristics/fragmentation.py` — AC20 reads its `consumed_paths`
- `src/segfacet/heuristics/mislabel.py` — AC20's positive control reads its `consumed_paths` (offset path, `bookkeeping`)
- `src/segfacet/eval/per_mode.py` — AC12/AC14 read the metric homes; unchanged
- `src/segfacet/synth/identity_ordering_alignment.py` — AC17 applies `sequence_break`

## Testing Strategy

New module: **`tests/test_154_ladder_remeasurement.py`**, one test per AC, named
`test_acN_*`. AC7–AC12 share one module-scoped harness run. AC22 uses one
subprocess per module (parametrised), and the child prints the opened paths as
JSON on stdout.

**Adversarial and edge cases:**

- **AC1:** constructing `CrossModeCoupling` without `provenance` raises
  `TypeError`.
- **AC6:** a monkeypatched provenance dated `2026-09-15` fails the check, and so
  does `"16/09/2026"`.
- **AC9/AC10 positive controls:** a copy of a coupling with `recorded_response`
  one 4th-significant-figure unit *too high* fails, and so does one below the
  measured value. A finite margin recorded above its measurement fails. A margin
  recorded `inf` against a finite measurement fails.
- **AC12:** on a synthetic `responses` table where a same-home metric carries the
  largest foreign response, the two margins differ. This proves the check can
  fail.
- **AC14:** a monkeypatched `PER_MODE_METRIC_SPECS` that re-homes
  `rogue_island_count` to mode 1 makes the derived tuple differ from the
  recorded one.
- **AC16:** a planted `tmp_path` file containing the needle is flagged by the
  same scanner.
- **AC17:** the independent descent counter returns `0` for `[20, 21, 22, 23, 24]`
  and `1` for `[20, 21, 22, 23, 28]`.
- **AC20 positive control:** the same check applied to
  `stage3.per_label_offsets[].offset_mm` fails. Its only consumer is `mislabel`,
  which declares it `bookkeeping` (not `signal`) and is not among mode 1's
  intended rules.
- **AC21:** building a `ModeSpec` copy of mode 1 whose anchor-role paths are not
  in `MODE_ANCHOR_PATHS[1]` raises `ValueError`. This confirms the coupling A6
  relies on.
- **AC22 positive control:** a child that runs `open("tests/…")` after installing
  the hook is reported.
- Do not hard-code corpus case ids. Item 157 renames them.

**Existing tests to reconcile.** Each pins the old anchor, the old wording or the
carried-over constants:

- `tests/test_137_mode_less_rule_disposition.py` (around L244–288): derives
  `required_modes` from `MODE_ANCHOR_PATHS` and asserts `1 in required_modes`
  via `spline_offset_mm`. After the re-anchor no tracked feature anchors mode 1.
  Drop that assertion and keep the derivation. Record in the docstring that
  `reference_delta`'s mode-1 declaration is no longer justified by an anchor
  path.
- `tests/test_138_traceability_matrix.py` (around L2163–2190, AC32): the same
  `1 in required_modes` pin. Reconcile the same way. The loop over
  `required_modes` stays.
- `tests/test_103_feature_catalogue.py` (L322, L362, L529): the offset path
  appears in expected-entry lists. Check each against the regenerated catalogue.
  Only the anchor-derived mode and evidence for that path should move.
- `tests/test_104_feature_catalogue_drift.py` (L120): the offset path in the
  drift list. Reconcile only if the drift assertion depends on its anchor status.
- `tests/test_100_severity_ladder.py`: any positional `CrossModeCoupling`
  construction gains `provenance`. The AC12 rationale pin (`"28"`) must still
  hold.
- `tests/test_102_stage18_validation.py` (L779–784): `_EXPECTED_MARGINS`. Update
  a value only if the re-measurement moved it. Keep the test's own tolerance.
- `tests/test_147_specification_is_the_record.py` (L569–573): the comment says
  `severity_ladder.py` still carries the false claim. Leave it, since it is a
  dated record in a test outside this list. AC16 supersedes it.

Do not run the suite as part of spec authoring. The validator runs it.

## Validation

1. **Clean-tree re-measurement.** On the claim branch with `git status` clean,
   run `.venv/bin/python -c "from segfacet.eval.severity_ladder import run_severity_harness, score_harness; v = score_harness(run_severity_harness()); print(v.summary()); print({k: (lv.margin, dict(lv.responses)) for k, lv in v.per_ladder.items()})"`.
   Confirm every recorded coupling and margin is the 4-significant-figure
   transcription of the printed value. Record the output in Decisions.
2. **Diff check.** Run
   `git diff aide/queue-021...HEAD -- src/segfacet/failure_modes.py`. Confirm the
   only change is the one `role=` line in `_MODE_1` (A6). Any other `ModeSpec`
   line is a FAIL.
3. **Artifact diff.** Run
   `git diff aide/queue-021...HEAD -- docs/aide/failure_modes.generated.json docs/aide/failure_modes.generated.md`.
   Confirm it is exactly mode 1's `offset_mm` role, in the JSON and in the
   rendered bullet.
4. **Anchor diff.** Confirm the `traceability_matrix.generated.*` and
   `feature_catalogue.generated.*` diffs are confined to mode 1's anchor paths
   and the offset path's anchor-derived mode and evidence.
5. Run `python .aide/scripts/aide.py scope`.

No `[validation]` profile is needed. Everything runs on the loop's CPU host.

## Dependencies

- Item 153 — keyed the harness by metric and operator, and recorded the four
  undecided questions this item settles.

**Downstream:** item 161 records the re-measured constants in `progress.md` and
attests Stage 31 criterion 3. Item 159 counts the `src/segfacet/` files that
mention `MODE_ANCHOR_PATHS`. This item adds no such file and removes none,
because `heuristics/reference_delta.py` is deliberately left untouched. Item 159
also edits `tests/test_103_feature_catalogue.py` (its AC13 `overlap`
parametrisation), on different lines from this item's reconcile. Item 157
renames corpus case ids, and this item's tests hard-code none.

## Decisions & Trade-offs

- **2026-09-16 — A6 confirmed by the maintainer.** Asked directly before
  implementation: changing the `role` of `_MODE_1`'s
  `stage3.per_label_offsets[].offset_mm` candidate feature from
  `"stage18-metric-anchor"` to `"hypothesised"` (the path stays listed) is
  allowed. The re-anchor criteria AC19–AC21 therefore stay as written.

- **2026-09-16 — Re-measured from a clean tree (builder).** On the claim
  branch, tree clean, before any code change:
  `.venv/bin/python -c "from segfacet.eval.severity_ladder import
  run_severity_harness, score_harness; v =
  score_harness(run_severity_harness()); print(v.summary()); print({k:
  (lv.margin, dict(lv.responses)) for k, lv in v.per_ladder.items()})"`.
  Printed verdict: `passed=True`. Per-ladder margins (measured, unrounded):
  `displace=inf`, `fragment=inf`,
  `inject_islands=112.03703703703704`, `relabel_swap=inf`,
  `remove_level=inf`, `crop_at_border=0.3585185185185185`,
  `sequence_break=inf`, `force_overlap=1.03862660944206`. Foreign responses
  at or above `COUPLING_THRESHOLD=0.25` (excluding each ladder's own
  designated metric): `crop_at_border -> unanchored_foreground_fraction =
  2.7892561983471076`; `force_overlap -> unanchored_foreground_fraction =
  0.9628099173553719`. No other (ladder, foreign metric) pair reached the
  threshold, so the coupling set is unchanged: exactly these two pairs.
  Transcribed per the module's rounding rule (responses rounded **up**,
  margins rounded **down**, both to 4 significant figures): `2.79`
  (`2.7892...` -> 4 s.f. `2.789`, remainder nonzero -> round up to `2.790`,
  which equals the stored `2.79`), `0.9629` (`0.96281...` -> `0.9629`),
  `112.0` (`112.037...` -> truncate to `112.0`), `0.3585`
  (`0.358518...` -> truncate to `0.3585`), `1.038` (`1.038626...` ->
  truncate to `1.038`). **Every re-measured value is numerically identical
  to item 153's carried-over one** — expected per the Description ("the
  numbers may come out the same as before"); AC9/AC10 verify this is a
  fresh transcription regardless, via the coupling/margin recomputation the
  test performs at import, not by trusting this note. `MeasurementProvenance
  (corpus="geometric", base_params=dict(_BASE_PARAMS), measured_on
  ="2026-09-16")` is attached to both `KNOWN_CROSS_MODE_COUPLINGS` entries,
  every `RECORDED_MARGIN_PROVENANCE` value and `MODE_LADDER_DISPOSITIONS[1]`.

- **2026-09-16 — AC17's two-descent finding (builder).** Applying
  `sequence_break(target_label=24, new_label=28)`, then `(23, 27)`, then
  `(22, 29)` cumulatively to `build_clean_spine(**_BASE_PARAMS).seg_img`
  leaves present labels `[20, 21, 27, 28, 29]` with `labels.CANONICAL_ORDER`
  ranks `[20, 21, 32, 19, 27]` — 2 descents by the independent hand count
  (running-maximum check), and `compute_per_mode_metrics(...)
  .by_metric("out_of_order_label_count").value == 2.0` from the live
  pipeline, matching. Confirms A5's by-hand analysis (`>= 2`, not the old
  "capped at 1" claim). Captured as a `knowledge` insight
  (`docs/aide/insights.md`, 2026-09-16) with the relabel sequence and the
  Stage-32 graded-ladder option, per Implementation Step 9.

- **2026-09-16 — Regenerated artifact diffs (builder).** `git diff
  aide/queue-021...HEAD -- src/segfacet/failure_modes.py` is exactly the one
  `_MODE_1` candidate-feature `role="stage18-metric-anchor"` ->
  `role="hypothesised"` line (A6). The three regenerated artifact pairs
  (`failure_modes.generated.{json,md}`, `traceability_matrix.generated.
  {json,md}`, `feature_catalogue.generated.{json,md}`) each diff exactly at
  mode 1's dropped `stage3.per_label_offsets[].offset_mm` anchor entry and
  that path's anchor-derived `failure_modes`/`mode_evidence` fields — no
  other mode, rule, or path changes (A8).
