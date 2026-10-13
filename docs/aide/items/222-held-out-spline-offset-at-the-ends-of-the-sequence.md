<!-- aide-template: item 3 -->
# Item 222 — Held-out spline offset at the ends of the sequence

> **Created:** 2026-10-12 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-030.md`](../queue/queue-030.md) · Item 222
> **Objectives:** G3
> **Suggested branch:** `aide/222-terminal-spline-offset`

---

## Description

Item 123 stopped the `spline_offset` rule from judging the first and last
vertebra of a case's anatomical sequence (owner decision 2026-08-29). The
held-out estimator (`compute_leave_one_out_spline_offsets`,
`src/segfacet/features/spline_offset.py`) has to extrapolate past the end of
its own parameter domain there, so it reads artefacts: up to 26.87 mm on
VerSe19's caudal L5. That leaves a hole. A displaced terminal vertebra is
never looked at, and terminals are 41 of the 45 VerSe19 offsets of 6 mm or
more (insight `2026-10-09-ddc5` part (ii)). The owner wants it fixed next
(decision 2026-10-09).

**What this item builds.** The owner chose this design on 2026-10-12, from
the spec-time measurement in A2.

- **The measure.** A **one-sided straight-line extrapolation** for terminal
  vertebrae: the perpendicular distance from the terminal's centroid to the
  line through its two nearest neighbours. Any neighbour that item 221's
  outlier search withholds is skipped. This is the "curvature model that
  does not need both neighbours" the insight names.
- **Where it is stored.** A **new feature field**,
  `per_label.{label}.curve.terminal_offset_mm`. It is present on a terminal
  vertebra of a case with five or more levels, and absent everywhere else.
  `offset_mm`, `dx_mm`, `dy_mm`, `dz_mm`, `closest_u`, `offset_voxel` and
  `is_terminal` keep their current values for every label, terminals
  included.
- **How the rule reads it.** The `spline_offset` rule judges a terminal
  vertebra on `terminal_offset_mm` and an interior one on `offset_mm`. Both
  use the existing `spline_offset.max_offset_mm` (13.0 mm, inclusive). There
  is no new parameter.
- **Two corpus cases gain a finding.** The owner accepted both, and their
  expectations are re-measured:
  - `sequence_break`: L5 is relabelled T13 (label 28), which puts it first
    in anatomical order although it sits at the caudal end. It reads
    33.83 mm.
  - `split_own_label`: L5 (label 24) is extrapolated from a split fragment
    and its neighbour. It reads 17.27 mm.
- **The VerSe19 record.** The terminal false-positive count under the chosen
  method is re-measured at the build's commit and recorded in
  `src/segfacet/heuristics/spline_offset.py`'s module docstring (Validation).

**Not in scope.**

- **The interior threshold.** `spline_offset.max_offset_mm` stays 13.0 for
  interior levels; that value is `gate-fac1`'s to settle. The queue names
  it `mislabel.max_offset_mm`; it has lived in the `spline_offset` rule since
  item 189.
- **The reference.** `src/segfacet/reference/ingest.py` and
  `src/segfacet/reference/delta.py` keep excluding terminal entries, and
  `reference_verse_v1.json` is not rebuilt. Both read `offset_mm` and
  `is_terminal` only.
- **The held-out estimator itself.** No change to the curve or the
  withholding: that is item 221's (A1).
- **Direction for terminals.** A terminal finding's reason carries no
  ", predominantly <axis>" clause. `dx_mm`/`dy_mm`/`dz_mm` describe the
  held-out vector, not the line reading, so naming an axis from them would
  describe the wrong displacement.

## Acceptance Criteria

Terms used below:

- **"The lordotic base"** is `segfacet.synth.clean_gt.build_clean_spine()`,
  the corpus base: L1–L5, labels 20–24. Its centroids are
  `compute_centroid(spine.seg_img, label)` for each label in `spine.labels`
  order, which is also the anatomical order.
- **"The two-opposite case"** is item 221's: the 8-level spine
  `build_clean_spine(levels=("T1",…,"T8"), spacing=(1.0, 1.0, 1.0), curve_amplitude_mm=6.0)`,
  with index 2 displaced by +15.0 and index 5 by −15.0 on `centroid_mm[0]`.
  Item 221 AC3 pins its withheld set as `{2, 5}`.
- **"The line reading `L(p; a, b)`"** of a point `p` from neighbours `a`
  (nearer) and `b`, all `centroid_mm` as float arrays, is
  `‖d − (d·t) t‖`, where `t = (a − b) / ‖a − b‖` and `d = p − a`. Each test
  writes it out in numpy and never calls this item's helper.
- **"The records"** are `compute_leave_one_out_spline_offsets(<centroids>)`
  with its defaults.
- **"A hand-built record"** is the minimal per-case dict test_123's
  `_offset_entry` builds: `per_label` entries carrying `label`,
  `level_name` and a `curve` block. Unless an AC says otherwise:
  - the `curve` block has `dx_mm = 3.0`, `dy_mm = 1.0` and `dz_mm = 0.5`;
  - it is evaluated by `SplineOffsetRule().evaluate(record, bundled_default_config())`.

The criteria:

- [ ] **AC1: on a clean case a terminal reads the line through its two
  nearest neighbours.** On the lordotic base, with centroids `c0 … c4`:
  - `records[0].terminal_offset_mm == pytest.approx(L(c0; c1, c2), abs=1e-9)`;
  - `records[4].terminal_offset_mm == pytest.approx(L(c4; c3, c2), abs=1e-9)`.
- [ ] **AC2: a withheld neighbour is skipped.** On the two-opposite case,
  with centroids `c0 … c7`:
  - `records[0].terminal_offset_mm == pytest.approx(L(c0; c1, c3), abs=1e-9)`;
  - `records[7].terminal_offset_mm == pytest.approx(L(c7; c6, c4), abs=1e-9)`.
- [ ] **AC3: interior records carry no terminal reading.** On the lordotic
  base, every record whose `is_terminal` is `False` has
  `terminal_offset_mm is None`.
- [ ] **AC4: below five levels no record carries a terminal reading.** On
  `build_clean_spine(levels=("L1", "L2", "L3", "L4"))`, every one of the four
  records has `terminal_offset_mm is None`.
- [ ] **AC5: the item-221 fields are unchanged.** On the two-opposite case,
  for every index `i`, `dataclasses.replace(records[i], terminal_offset_mm=None)`
  equals item 221's "item-120 computation for withheld set S" at index `i`.
  `S` is the set `_withhold_outliers` returns. The computation is written
  out in the test exactly as item 221's AC terms define it.
- [ ] **AC6: the record stores a terminal's reading.** In
  `extract_feature_record(build_clean_spine().seg_img, bundled_default_config())`,
  `per_label["20"]["curve"]["terminal_offset_mm"]` equals
  `L(p20; p21, p22)` to `abs=1e-9`, and
  `per_label["24"]["curve"]["terminal_offset_mm"]` equals
  `L(p24; p23, p22)` to `abs=1e-9`. Here `pN` is that same record's
  `per_label[str(N)]["centroid"]["centroid_mm"]`.
- [ ] **AC7: the record stores nothing for an interior label.** In the same
  record, the `curve` blocks of labels 21, 22 and 23 have no
  `terminal_offset_mm` key.
- [ ] **AC8: a terminal fires at the threshold.** A hand-built record with
  one entry, label 24 / `L5`, whose `curve` has `is_terminal: True`,
  `offset_mm: 0.5` and `terminal_offset_mm: 13.0`, yields exactly one
  finding. That finding has:
  - `rule_id == "spline_offset"`;
  - `detector_id == "spline_offset"`;
  - `labels == frozenset({24})`;
  - a `reason` that starts with `"Vertebra misaligned from spinal curve:"`.
- [ ] **AC9: a terminal is not judged on its held-out offset.** A hand-built
  record with one entry, label 24 / `L5`, whose `curve` has
  `is_terminal: True`, `offset_mm: 40.0` and `terminal_offset_mm: 12.99`,
  yields no finding.
- [ ] **AC10: a terminal finding names no axis.** AC8's finding's `reason`
  contains `"terminal"` and does not contain `"predominantly"`.
- [ ] **AC11: a displaced terminal on a synthetic case is flagged.** Take
  `DisplacePerturbation(target_label=24, displacement_mm=15.0, ap_angle_deg=20.0).apply(build_clean_spine().seg_img, 0)`.
  This is the corpus `displace` recipe moved onto L5. Running
  `run_qc(<its labelmap>, bundled_default_config())` gives a findings list
  that contains a finding with `rule_id == "spline_offset"` and
  `labels == frozenset({24})`.
- [ ] **AC12: `sequence_break` fires `spline_offset` on T13.** `run_qc` over
  the committed `sequence_break` fixture, loaded the way
  `tests/test_041_regression_suite.py` loads it, under
  `bundled_default_config()`, gives findings that include one with
  `rule_id == "spline_offset"` and `labels == frozenset({28})`.
- [ ] **AC13: `split_own_label` fires `spline_offset` on L5.** The same, over
  the committed `split_own_label` fixture, includes a finding with
  `rule_id == "spline_offset"` and `labels == frozenset({24})`.

Why each is written:

- **AC1 and AC2** pin the measure and the neighbour rule the owner chose.
- **AC3, AC4, AC6 and AC7** pin present-only-when-judged. The rule reads it:
  an absent field is how it tells "not judged".
- **AC5** pins the owner's Q3 decision that the other fields stay unchanged.
  Without it, overwriting `offset_mm` would pass every other criterion.
- **AC8 and AC9** pin which field a terminal is judged on, and that the
  comparison is inclusive.
- **AC10** guards the wrong-vector reason. The direction code would
  otherwise run unchanged.
- **AC11** is the queue's "judged and flagged".
- **AC12 and AC13** pin the two firings the owner accepted. The expectation
  edits that record them are checked by the corpus-agreement tests below.

Not written, because an existing test already fails without it:

- **"Every corpus case's measured firing equals its expected set."**
  `tests/test_041_regression_suite.py` and
  `tests/test_147_specification_is_the_record.py::test_ac26_every_corpus_case_agrees_and_status_derives_correctly`
  assert it for every case. The `Expectation` and `CorpusCaseExpectation`
  edits (steps 6–7) are what keep them green.
- **"A terminal entry with no `terminal_offset_mm` fires nothing."**
  `tests/test_123_recalibrate_and_regenerate.py::test_ac39_terminal_entry_never_fires_even_at_forty_mm_over_a_thirteen_mm_threshold`
  and `test_adv_terminal_entry_with_astronomically_large_offset_never_fires`
  build exactly that entry. They stay green unedited, which is that
  contract.
- **"The schema admits the field."** `stage3OffsetEntry` (the per-label
  curve schema) sets `additionalProperties: false`. Every schema-validating
  test of a terminal-bearing report fails until step 4 lands.
- **"The catalogue documents the new path."**
  `build_catalogue(strict=True)` raises on a realised leaf with no
  `FEATURE_DOCS` entry, and `tests/test_104_feature_catalogue_drift.py`
  fails on a stale committed catalogue.

**Not written as a criterion: the VerSe19 terminal false-positive count.**
It is measured on a cohort the repository does not carry, so no suite test
can recompute it. The Validation section re-measures it and the validator
compares it with the recorded figure, as item 221 did with its commit and
gate facts.

No AC closes a Stage 34 criterion. This is a maintenance item.

## Assumptions

`loop.clarify` was forced to interactive for this batch. The owner answered
three questions on 2026-10-12:

- **Q1 (method):** one-sided straight-line extrapolation, judged at the
  existing 13.0 mm, with withheld neighbours skipped.
- **Q2:** accept the new terminal findings on `sequence_break` and
  `split_own_label`, and re-measure both expected sets.
- **Q3:** a new field, `curve.terminal_offset_mm`, with `offset_mm` and the
  direction components unchanged. Reference ingest and delta keep excluding
  terminals.

Every number below was measured 2026-10-12 on `aide/queue-030` at `9438bc4`
(source identical to `2a1491d`), with `.venv/bin/python`, by scratch probes
outside the repo. The probes ran before item 221 existed. They approximated
its withheld set by "interior held-out reading ≥ 13.0 mm" (A1). The builder
re-measures on the real change.

- **A1 (pins item 221's interface, as this item reads it).** Item 221 spec,
  A6. All four live in `src/segfacet/features/spline_offset.py`.
  - **`_withhold_outliers(centroids, first_pass, reference_fit, spacing_mm, backend) -> Tuple[FrozenSet[int], List[VertebralSplineOffset]]`.**
    It runs item 221's add-then-remove search (its A1 steps 2–6). This item
    reads only element 0, the final withheld set. It holds sequence indices,
    interior only (never 0 or `n-1`), and is empty when nothing survives.
  - **`_held_out_records(centroids, withheld, reference_fit, spacing_mm, backend)`.**
    Read only by AC5's test, through 221's AC-defined computation, never
    called.
  - **`_OUTLIER_CUTOFF_MM = 10.0`.** Not read directly.
  - **`compute_leave_one_out_spline_offsets`.** Same signature, record order
    and fallbacks. Above the five-level fallback it returns
    `_withhold_outliers(c, first, fit, …)[1]`.

  On 2026-10-12 the owner switched item 221 from a backward-only search to
  the add-then-remove search. The signatures did not change, and this item
  depends only on the set the search returns, so no criterion here moved.
  221's own pins still hold under the switch:
  - the two-opposite case's set is `{2, 5}` (its AC3), which AC2 relies on;
  - the L1–L5 case with indices 1, 2 and 3 displaced gives `{1, 2, 3}`
    (its `five-levels-every-interior-withheld` case);
  - corpus `displace` gives `{2}`;
  - VerSe19 sets are unchanged except `sub-verse406_split-verse261`'s `{T10}`
    (its A4).

  On VerSe19 and the corpus, the probe's approximate set gives the same
  sets item 221 records (`{2}` on `displace`, `{T10}` on verse406). So A2–A4
  are expected to hold within re-measurement.
- **A2 (measured: why this method).** The probe re-ran four candidates on
  the 80 VerSe19 GT masks:
  - **The cohort.** Centroids are taken in `anatomical_order`, as the
    pipeline does. 75 subjects have five or more levels, which gives 150
    terminal vertebrae; 26 of them touch an image face, so the
    `fov_truncation` gate drops a `spline_offset` finding on them.
  - **Detection.** Each terminal was also moved laterally by 8–18 mm.

  | Method | Clean non-face terminals ≥ 13.0 | Lateral detection at 13.0: 13 / 15 / 18 mm |
  |---|---|---|
  | **One-sided line (chosen)** | **0 of 124** (caudal max 12.29, cranial max 6.84) | **0.68 / 0.95 / 0.98** |
  | Held-out estimator, separate 17.5 mm threshold | 2 of 124 | 0.28 / 0.40 / 0.60 at 17.5 |
  | Local quadratic, three nearest neighbours | 2 of 124 | 0.68 / 0.83 / 0.98, with heavy corpus cross-talk (12–70 mm on four clean terminals) |
  | Extrapolation-aware spline tangent | 6 of 124 | 0.60 / 0.69 / 0.81; under-reads at about 60 % of the move |

  **Why the held-out estimator fails here.** On the 5-level corpus base it
  reads 0.23 mm for an 18 mm terminal move: the short-spine limitation its
  docstring records. So it could not meet AC11 on the committed base.
- **A3 (measured: VerSe19 under the chosen method, to be re-measured and
  recorded).**
  - **Counts.** 150 terminals judged; 1 at or above 13.0 mm
    (`sub-verse014`, caudal L5, 17.707 mm). That one touches an image face,
    so the `fov_truncation` gate drops it. That makes **0 false positives
    through the shipped pipeline**.
  - **Margin.** The largest non-face reading is 12.288 mm (`sub-verse107`,
    caudal L5), 0.71 mm under the threshold. This margin is narrow, and
    the record states it.
  - **Not judged.** The five subjects with fewer than five levels have no
    terminal reading.
- **A4 (measured: the corpus under the chosen method).** Clean terminal
  readings: `clean_control` 5.05 / 8.51 mm. `displace` reads 7.58 / 11.15,
  because the displaced L3 is skipped as withheld; with it as a neighbour
  L1 and L5 would read 13.19 / 13.95 and fire. `relabel_swap` reads
  5.05 / 11.15.
  - **New firings, the owner's Q2.**
    - `sequence_break` T13 (label 28): 33.83 mm.
    - `split_own_label` L5 (label 24): 17.27 mm.
  - **Not judged.** The four-level cases (`fuse_adjacent`, `fuse_separate`,
    `remove_level`, `remove_level_relabel`). Otherwise `fuse_adjacent` and
    `fuse_separate` would fire at their caudal L4 (14.24 / 13.74).
  - **The face-touching terminals.** `crop_at_border` L1 and `crop_fov_si`
    L5 read 3.25 and 9.86 mm, below the threshold either way.
  - **The intensity corpus.** `clean_spine_seg` reads 5.05 / 8.51 mm. No
    change.
  - **AC11's case.** L5 moved by the `displace` recipe (15 mm at 20°) reads
    14.466 mm with no face touched: 1.47 mm over the threshold, close to
    `displace`'s own 1.62 mm margin. Its held-out `offset_mm` reads
    0.262 mm.
- **A5 (decided: absent, not null, on a label not judged).** The key is
  present exactly where a terminal was judged, matching how `curve` blocks
  already omit what was not computed. The schema property is
  `{"type": "number", "minimum": 0}`, optional, with no null branch.
  - **Why absent.** The catalogue's observed-range pass, the schema and
    every consumer then need no null handling.
  - **Dataclass vs serialised form.**
    `VertebralSplineOffset.terminal_offset_mm` is `Optional[float] = None`.
    `spline_offset_to_dict` emits the key only when it is not `None`.
- **A6 (decided: the neighbour rule).** For terminal index `i` (0 or `n-1`)
  and withheld set `W`:
  - Walk the other indices `j ≠ i` in ascending `|j − i|`, skipping `j`
    in `W`. The other terminal is eligible. Take the first two: `a` is the
    nearer, `b` the second.
  - The reading is `L(c_i; c_a, c_b)`.
  - With fewer than two eligible indices, the field is `None`. For example,
    five levels with all three interior withheld.
  - Only cases at or above the five-level fallback are judged. Below it
    every record's field is `None`. The floor matches
    `_MIN_LEVELS_FOR_HELD_OUT` and leaves the four-level cases unjudged
    (A4).
- **A7: no human gate and no environment-gated capability.**
  - `gate-fac1` (the interior 13.0 mm) is untouched and stays ⏳.
  - VerSe19 is read only by the Validation replay, under the existing
    `SEGFACET_VERSE_COHORT` / `dataset-verse19training` convention. No test
    reads it, and no `[validation]` profile exists for it.

## Implementation Steps

1. **`src/segfacet/features/spline_offset.py`.**
   - Add `terminal_offset_mm: Optional[float] = None` to the frozen
     `VertebralSplineOffset`, last, with its docstring line.
   - Add a private `_terminal_line_offset(point, a, b) -> float`, the line
     reading `L` in numpy.
   - In `compute_leave_one_out_spline_offsets`, after item 221's
     `withheld, records = _withhold_outliers(...)`, pick each terminal's
     neighbours by A6. Set the reading with `dataclasses.replace`, which the
     module already uses.
   - The `n == 1` and below-five branches are untouched, so they return
     `None`.
   - Rewrite the module docstring's "Terminal-vertebra exclusion" section:
     the held-out reading still extrapolates and is still excluded from the
     reference, and the terminal is now judged on `terminal_offset_mm`. Keep
     the tokens `terminal` and `extrapolat`, which test_123 AC16 reads in
     the rule module, and every token item 221's step 5 lists.
2. **`src/segfacet/feature_report.py`, `spline_offset_to_dict`.** Emit
   `"terminal_offset_mm"` after `"is_terminal"`, only when the value is not
   `None`, and fix the "All nine fields" docstring. No other change: the
   `curve` block is filled from this dict.
3. **`src/segfacet/heuristics/spline_offset.py`.**
   - **The terminal branch.** Replace the terminal `continue` in
     `_detect_offset_outliers`. For a truthy `is_terminal`, read
     `terminal_offset_mm`:
     - absent or `None`: skip, as today;
     - otherwise compare it with `>=` against `max_offset`. A finding uses
       the same tag, rule and detector id. Its reason reads `label {label}
       ({name}) centroid lies {v:.1f} mm off the spinal curve extrapolated
       from its two nearest neighbours (terminal vertebra) (threshold
       {max:.1f} mm).`, with no direction clause.
   - **The interior branch** is unchanged and never reads
     `terminal_offset_mm`.
   - **The declaration.**
     - Add `ConsumedPath("per_label.{label}.curve.terminal_offset_mm", role="condition-signal", reason=…)`.
     - Re-word `is_terminal`'s reason: it now selects which offset a label
       is judged on.
     - Add the path to the `displaced_vertebra` `ConditionOptIn.paths`.
     - Re-word `fires_when` to name both fields.
   - **The module docstring.**
     - Rewrite the "Never fires on a terminal entry" bullet and the
       "Terminal vertebrae are excluded from this measurement and from this
       detector" paragraph. Terminals stay excluded from the threshold's
       calibration; the detector judges them on `terminal_offset_mm`.
     - Add the corpus terminal margins from A4.
     - Add a section `Terminal calibration (item 222, <date>)` stating:
       - the method;
       - the commit measured at;
       - subjects and terminals judged;
       - the face-touching count;
       - the count at or above 13.0 mm, how many the `fov_truncation` gate
         drops, and the resulting false-positive count;
       - the largest non-face reading and its margin.

       It is filled from the Validation replay.
4. **`src/segfacet/report_schema_v0.json`.**
   - Add `terminal_offset_mm` to `stage3OffsetEntry`'s `properties`
     as A5 gives, with a description. It is not required, and not in the
     six-field `dependencies` group.
   - Extend the entry's description by one clause.
5. **`src/segfacet/feature_docs.py`.**
   - Add the `per_label.{label}.curve.terminal_offset_mm` `FeatureDoc`
     (units `mm`, `scales with spacing`): what it measures, the neighbour
     rule, absent below five levels and on interior labels.
   - Re-word `is_terminal`'s computation: the rule now judges a terminal on
     `terminal_offset_mm`, and the reference still excludes it. Keep
     `first`, `last`, `spline_offset` and `extrapolat`, which test_123
     AC46 reads.
   - Adjust the Spline Offset group intro if it says terminals are not
     judged.
6. **Synthetic expectations.** Each is an *addition*, so it composes with
   items 218 and 219's edits to the same cases:
   - `src/segfacet/synth/identity_ordering_alignment.py`,
     `SequenceBreakPerturbation`: add `"spline_offset"` to
     `expected_rule_ids`. Label 28 is already in `expected_labels`. Extend
     `detail` by one sentence.
   - `src/segfacet/synth/component_shape.py`, the `split_own_label`
     operator: add `"spline_offset"` to `expected_rule_ids` and label 24 to
     `expected_labels`, with a dated comment.
7. **`src/segfacet/failure_modes.py`.**
   - Add `"spline_offset"` to `expected_firing` of the `sequence_break` and
     `split_own_label` `CorpusCaseExpectation`s, with a dated
     reason sentence. This records each as a co-detection, so
     `catalogue.rule_declaration_conflicts` stays clean.
   - Add `per_label.{label}.curve.terminal_offset_mm` to
     `_CONDITION_DISPLACED_VERTEBRA.candidate_features`.
   - Rewrite the `fov_truncation` mechanism sentence "spline_offset's
     detector skips terminal entries (per_label.{label}.curve.is_terminal)".
     The new sentence says it judges them on `terminal_offset_mm` instead.
     Keep the token `is_terminal`, which test_145 reads.
   - If the specification tests require the two cases to be listed under
     `displaced_vertebra`'s corpus cases, add them, and record that in
     Decisions.
8. **Regenerate, each twice into scratch and byte-compared, then onto the
   committed copy:**
   - `.venv/bin/python -m segfacet.synth.corpus`. The manifest moves; the
     fixtures must stay byte-identical, and a moved fixture is a hand-back.
   - `.venv/bin/python -m segfacet.catalogue`
   - `.venv/bin/python -m segfacet.traceability`
   - `.venv/bin/python -m segfacet.rule_table`
   - `.venv/bin/python -m segfacet.failure_modes`
   - `.venv/bin/python -m segfacet.synth.corpus_sheet`
9. **Run the Validation replay** and write step 3's calibration section from
   it.
10. **Reconcile the existing tests** (Testing Strategy), each with a dated
    `# Item 222 (YYYY-MM-DD): …` comment, the house style.
11. **Run `python .aide/scripts/aide.py scope 222` and
    `python .aide/scripts/aide.py check`.** Neither may report an error.

No dependency is added. `dataclasses.replace`, numpy and the existing
generators are reused.

## Authorised paths

**May change:**

- `src/segfacet/features/spline_offset.py` — the field, the line reading, the neighbour rule, the docstring (step 1).
- `src/segfacet/feature_report.py` — serialise the field when present (step 2).
- `src/segfacet/heuristics/spline_offset.py` — the terminal branch, declaration and docstring record (step 3).
- `src/segfacet/report_schema_v0.json` — the optional curve property (step 4).
- `src/segfacet/feature_docs.py` — the new `FeatureDoc`, `is_terminal`'s text (step 5).
- `src/segfacet/synth/identity_ordering_alignment.py` — `sequence_break` expectation (step 6).
- `src/segfacet/synth/component_shape.py` — `split_own_label` expectation (step 6).
- `src/segfacet/failure_modes.py` — co-detections, candidate feature, `fov_truncation` mechanism text (step 7).
- `tests/corpus/manifest.json` — regenerated expectations (step 8).
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 8).
- `docs/aide/feature_catalogue.generated.md` — regenerated (step 8).
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 8).
- `docs/aide/traceability_matrix.generated.md` — regenerated (step 8).
- `docs/aide/rules.generated.md` — regenerated (step 8).
- `docs/aide/failure_modes.generated.json` — regenerated (step 8).
- `docs/aide/failure_modes.generated.md` — regenerated (step 8).
- `docs/aide/corpus_sheet.png` — regenerated; it renders each case's expected rules (step 8).
- `tests/test_222_terminal_spline_offset.py` — **new**: this item's test module.
- `tests/test_120_leave_one_out_offset.py` — AC12's exact curve key set (reconcile).
- `tests/test_039_identity_ordering_alignment_perturbations.py` — the terminal-aware `displace` branch (reconcile).
- `tests/test_103_feature_catalogue.py` — the leaf-path count (reconcile).
- `tests/test_124_observed_range.py` — the leaf-path count (reconcile).
- `tests/test_132_monotonicity_against_traversal_order.py` — the leaf-path count and observed summary (reconcile).
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — `sequence_break`'s finding set (reconcile).
- `tests/test_116_ras_native_corpus.py` — `sequence_break`'s added findings against the golden (reconcile).
- `tests/test_174_split_sub_types.py` — `split_own_label`'s measured firing (reconcile).
- `tests/test_186_expected_level_sequence.py` — `split_own_label`'s measured firing (reconcile).
- `tests/test_220_collapsed_labels_rule.py` — item 220's corpus-wide firing check, if it pins `sequence_break`'s or `split_own_label`'s set (reconcile; Dependencies).

**Asserts against:**

- `tests/corpus/fixtures/sequence_break_seg.nii.gz` — AC12 runs the pipeline over it; unchanged.
- `tests/corpus/fixtures/split_own_label_seg.nii.gz` — AC13 runs the pipeline over it; unchanged.
- `src/segfacet/reference/ingest.py` — terminals stay excluded from the reference (Q3); test_123 AC41 pins it, unedited.
- `src/segfacet/reference/delta.py` — terminals stay excluded from the delta (Q3); test_123 AC42 pins it, unedited.

## Testing Strategy

The test module is `tests/test_222_terminal_spline_offset.py`, with one test
per AC. Spines come from `build_clean_spine` and `compute_centroid`, exactly
as the AC terms define.

- **The line reading `L`** is written out in numpy in the test, never through
  `_terminal_line_offset`. Otherwise AC1, AC2 and AC6 would compare the
  helper with itself.
- **AC5's expected records** are built from `fit_centroid_spline` and
  `compute_spline_offsets`, as item 221's AC terms define. Only `S` comes
  from `_withhold_outliers`.
- **AC12 and AC13** load the committed fixtures the way
  `tests/test_041_regression_suite.py` does.

Adversarial cases, each with the failure mode it guards, and no others:

- `interior-entry-ignores-terminal-value`: a hand-built interior entry,
  `is_terminal: False`, with `offset_mm: 1.0` and `terminal_offset_mm: 40.0`,
  yields no finding. It guards a rule that reads `terminal_offset_mm`
  wherever the key is present instead of only on a terminal.
- `every-interior-withheld-leaves-no-terminal-reading`: item 221's
  `five-levels-every-interior-withheld` case. That is the lordotic L1–L5
  `build_clean_spine` with indices 1, 2 and 3 displaced by +15, −15 and +15
  on `centroid_mm[0]`.
  - First check the precondition: `_withhold_outliers` returns `{1, 2, 3}`.
  - Then both terminals' `terminal_offset_mm` is `None`, and nothing
    raises.
  - It guards a neighbour walk that runs out of eligible indices: it would
    index past the sequence, reuse a withheld level, or read one point as a
    line.
- `cranial-terminal-flagged`: as AC11, with `target_label=20`. The finding
  carries `labels == frozenset({20})`. Measured: L1 reads 14.000 mm under
  this recipe. It guards a neighbour walk that is right for the caudal end
  and wrong for the cranial one.

**Existing tests to reconcile.** They were found by grepping `tests/` for
`is_terminal`, the two case ids, and the catalogue leaf counts. This is a
lower bound: a spec-time grep lists each failure once, at its first assert
(`CLAUDE.md`, "A spec-time probe … is a lower bound").

- **`tests/test_120_leave_one_out_offset.py::test_ac12_per_label_offsets_entry_field_set_exact`.**
  The exact eight-key set now holds for interior entries only. Terminal
  entries (labels 20 and 24) carry `terminal_offset_mm` as a ninth key.
- **`tests/test_039_identity_ordering_alignment_perturbations.py::_designated_rule_fires_reconstructed`,
  the `displace` branch.** Today a terminal target must *not* fire (item
  123 AC55). Now a terminal target fires exactly when the reconstructed
  record's `curve.terminal_offset_mm` is at least the configured
  `max_offset_mm`. Measured: the default 18 mm diagonal reads 15.22 on L1
  and 13.65 on L5. It feeds `test_ac23_unspecified_target_is_seed_deterministic_and_self_consistent[displace]`
  and `test_adv_different_seeds_unspecified_target_stay_self_consistent[displace]`.
- **The catalogue leaf counts**, +1 each for the new path, over whatever the
  base reads at claim (item 220 may also move them):
  - `tests/test_103_feature_catalogue.py`: `len(paths) == 95`. Keep the
    comment line that contains `94`, which test_123 AC48 reads.
  - `tests/test_124_observed_range.py`: `len(paths) == 154`.
  - `tests/test_132_monotonicity_against_traversal_order.py::test_ac29_catalogue_measured_content_unchanged`:
    `leaf_count == 154`, and `_PRE_ITEM_OBSERVED_SUMMARY` gains one in
    whichever verdict the new path takes.
- **`tests/test_129_coincident_centroids_and_held_out_floor.py`.**
  `sequence_break`'s pinned finding set gains `("spline_offset", (28,))`.
- **`tests/test_116_ras_native_corpus.py`.** The added-findings table
  against the `aeb2f55` golden gains `sequence_break`'s
  `("spline_offset", (28,))`.
- **`tests/test_174_split_sub_types.py:235`** and
  **`tests/test_186_expected_level_sequence.py:268`.**
  `measured_firing(split_own_label)` becomes
  `{"bounds", "split_fragment", "spline_offset"}`.

Checked and expected to stay green unedited:

- **`test_123`:** AC16 (tokens kept), AC35–AC42 (no `terminal_offset_mm`
  in their hand-built entries), AC46 (tokens kept) and AC51.
- **`test_145`:** the `fov_truncation` mechanism keeps `is_terminal`, and
  `spline_offset` still neither records nor opts in to `fov_truncation`.
- **`test_189`:** AC12.
- **`test_022`:** the subset key checks.
- **`tests/golden/report_format_contract.json`:** its fixture carries no
  terminal key.

## Validation

1. **The VerSe19 terminal replay.** Where `SEGFACET_VERSE_COHORT` or the
   `dataset-verse19training` symlink reaches the cohort, run a scratch
   script, not committed, over every `*_seg-vert_msk.nii.gz`:
   - load it with `segfacet.io.load_volume(…, integer_labels=True)`;
   - take centroids with `compute_centroid` per label, ordered by
     `segfacet.labels.anatomical_order`, as
     `pipeline.extract_feature_record` does;
   - call `compute_leave_one_out_spline_offsets(<those centroids>)`;
   - record each terminal's `terminal_offset_mm`, and whether its label
     appears on any of the six boundary slices of the RAS array. That is
     `border_touching_labels`' membership: a true `touches_*` on any face.
2. **Count and compare.** Report:
   - subjects with five or more levels;
   - terminals judged (`terminal_offset_mm` not `None`);
   - face-touching terminals;
   - readings at or above 13.0;
   - how many of those touch a face;
   - false positives, meaning non-face readings at or above 13.0;
   - the largest non-face reading.

   Expected near A3: 75 / 150 / 26 / 1 / 1 / 0 / 12.288 mm. A difference is
   recorded, not tuned away. Any non-zero false-positive count is a
   **hand-back**: the owner chose the method on a measured 0.
3. **Read the record.** The calibration section in
   `src/segfacet/heuristics/spline_offset.py`'s docstring:
   - states step 2's numbers;
   - names a commit on this branch that `git cat-file -t` resolves to a
     commit;
   - says the interior `max_offset_mm` stays 13.0 and `gate-fac1` is
     unchanged.

   Where the cohort is absent, record **❓ Unverified (VerSe19 absent)**
   against steps 1–2 in Decisions & Trade-offs, rather than a pass. Step 3's
   record cannot then be written from a measurement, so **hand back**.

## Dependencies

- **Item 221.** It replaces the estimator's withholding with the
  add-then-remove search and provides `_withhold_outliers`, whose returned set this item's
  neighbour rule skips (A1). Its measured readings are the base this item's
  numbers are re-measured on.
- **Item 220.** Its Asserts against pins `tests/corpus/manifest.json` and
  `tests/test_129_coincident_centroids_and_held_out_floor.py`. This item
  moves both, by adding `spline_offset` to `sequence_break`. So item 220
  builds first, and this item lists
  `tests/test_220_collapsed_labels_rule.py` under May change, in case its
  corpus-wide firing check pins a set this item moves.

**Downstream:**

- Items 218 and 219 also edit `sequence_break`'s expectation and regenerate
  `tests/corpus/manifest.json`. This item's edits are additions, so they
  compose in either order. Whichever lands later re-measures on top.
- Stage 35's development-role reference rebuild (queue 031) decides whether
  terminal readings ever enter the reference.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether `sequence_break`'s and `split_own_label`'s new
  findings are the condition or cross-talk.
  - On `sequence_break`, the reading comes from a label-order defect.
  - On `split_own_label`, it comes from a split fragment used as a
    neighbour.
  - The owner accepted both (Q2), so the corpus records them. Narrowing
    them needs a guard the owner did not choose, such as skipping a
    terminal named in `pairs.adjacent.non_monotonic_pairs` or a neighbour
    pair far below the case's pitch.
- **Left open:** the non-face VerSe19 margin is 0.71 mm (A3). One more
  ordinary caudal L5 in a larger cohort could fire. The Stage 35
  VerSe19 + VerSe20 development cohort is the place to re-measure it.
- **Left open:** a face-touching terminal is still never judged, because
  the `fov_truncation` gate drops the finding. That is the gate's design
  (item 191), not this item's.
