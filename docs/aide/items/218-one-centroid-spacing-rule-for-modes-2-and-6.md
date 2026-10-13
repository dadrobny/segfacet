<!-- aide-template: item 3 -->
# Item 218 — One centroid-spacing rule for modes 2 and 6

> **Created:** 2026-10-12 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-030.md`](../queue/queue-030.md) · Item 218
> **Objectives:** G2, G3
> **Suggested branch:** `aide/218-centroid-spacing-rule`

---

## Description

Owner decision 2026-10-12 (insights `2026-09-22-c151` and `2026-09-22-d85a`,
with `2026-09-29-4562` a duplicate of the first): one rule over the
inter-centroid spacings serves both mode 2 (fused vertebra segments) and
mode 6 (vertebra not segmented).

Today `fused_label` (items 207, 211, `src/segfacet/heuristics/fused_label.py`)
serves mode 2 on spacing plus size. Mode 6 has had no detecting rule since
item 188, and the renumbered `remove_level_relabel` case has fired nothing
since item 143. A missed vertebra leaves one gap of about two pitches
between labels of normal size, whether or not the labels were renumbered.

This item makes three changes.

1. **The rule is renamed `centroid_spacing` and gets two detectors**
   (maintainer answer 2026-10-12):
   - `fused_label`, serving mode 2. This is today's detector, unchanged in
     what it fires on.
   - `missing_level`, serving mode 6. It is new.

   The module becomes `src/segfacet/heuristics/centroid_spacing.py`, the
   class becomes `CentroidSpacingRule`, and the config section becomes
   `rules.centroid_spacing`.
2. **The spacing the rule reads follows the spine curve, not the anatomical
   labels** (maintainer answer 2026-10-12).
   - Both detectors order the labels by `per_label.{label}.curve.path_u`,
     which is the position along item 210's label-free path.
   - They take each spacing as the Euclidean distance between the
     `per_label.{label}.centroid.centroid_mm[]` of consecutive labels in that
     order.
   - A swapped or relabelled vertebra still sits at a regular pitch along
     the curve, so an order break reads no gap. That is what keeps
     `relabel_swap` and `sequence_break` silent; no ordering gate is needed
     (A2).
   - The rule no longer reads `pairs.adjacent.spacings_mm[]`. That field
     stays in the record, in anatomical order, unchanged (A4).
3. **Mode 6 is declared against `missing_level`, and both remove-level cases
   designate the rule** (maintainer answer 2026-10-12).
   - `remove_level` and `remove_level_relabel` now fire `missing_level`.
   - `remove_level`'s designated rule moves from `coverage` to
     `centroid_spacing`.
   - `remove_level_relabel`'s expectation moves from "no rule, pass" to
     `centroid_spacing` and flagged-for-review.

**Not in scope.**

- No record field is added, removed or reordered, and `features/` is not
  touched (A4).
- This item changes none of `mislabel`, `sequence`, `coverage` or their
  detectors.
  Modes 9 and 10 are item 219's.
- `MODE_SIGN_OFFS` is not touched (A8). Mode 6's `observability`, its
  authored `status` and its candidate features are unchanged.
- `docs/feature-taxonomy.md`, a signed design record (item 214), keeps its
  `fused_label` mentions as written.
- No threshold of any other rule changes.

## Acceptance Criteria

Terms used below:

- **"Both corpora"** are `segfacet.synth.corpus.load_manifest()["cases"]`
  (geometric) and `segfacet.synth.intensity.load_intensity_manifest()["cases"]`.
  Each case's findings come from `segfacet.synth.regression.pipeline_findings`
  or `intensity_pipeline_findings` respectively.
- **"The rule"** is the registered rule whose `rule_id == "centroid_spacing"`.

- [ ] **AC1: the rule fires exactly where both detectors are expected.** Over
  both corpora, the set of `(case_id, detector_id, labels)` triples taken
  from every finding with `rule_id == "centroid_spacing"` equals:
  - `("fuse_adjacent", "fused_label", frozenset({22}))`
  - `("fuse_separate", "fused_label", frozenset({22}))`
  - `("remove_level", "missing_level", frozenset({21, 23}))`
  - `("remove_level_relabel", "missing_level", frozenset({21, 22}))`
- [ ] **AC2: `missing_level` is attributed to mode 6.**
  `segfacet.failure_modes.modes_for_detector("centroid_spacing", "missing_level") == (6,)`.
- [ ] **AC3: `fused_label` stays attributed to mode 2.**
  `segfacet.failure_modes.modes_for_detector("centroid_spacing", "fused_label") == (2,)`.
- [ ] **AC4: the rule declares modes 2 and 6.** The rule's
  `mode_declaration.modes == (2, 6)`.
- [ ] **AC5: no rule is registered as `fused_label`.** `"fused_label"` is not
  among the `rule_id`s of `segfacet.heuristics.rule.iter_rules()`.
- [ ] **AC6: mode 6 derives `validated`.**
  `segfacet.failure_modes.derive_status(segfacet.failure_modes.SPECIFICATION[6]) == "validated"`.
- [ ] **AC7: `remove_level` designates the rule.** The geometric manifest
  entry with `case_id == "remove_level"` has
  `expected_rule_ids == ["centroid_spacing"]`.
- [ ] **AC8: `remove_level_relabel` designates the rule.** The geometric
  manifest entry with `case_id == "remove_level_relabel"` has
  `expected_rule_ids == ["centroid_spacing"]`.
- [ ] **AC9: `remove_level_relabel` no longer passes.**
  `segfacet.synth.regression.pipeline_verdict_label(case) == "flagged-for-review"`
  for the `remove_level_relabel` manifest case.

Why each is written:

- **AC1** covers four of the queue's testable claims in one measured
  equality:
  - `remove_level_relabel` fires.
  - `fuse_adjacent` and `fuse_separate` still fire as mode 2.
  - `sequence_break` does not fire.
  - `relabel_swap` does not fire. It also reads as a two-pitch gap in label
    order (A2).

  Each fails today, because the rule id does not exist. `remove_level` is
  in the set because a missed vertebra reads the same whether or not the
  labels were renumbered.
- **AC2 and AC3** are "attributed to mode 6" and "still fire it as mode 2".
  A detector's mode comes from the specification, so it is pinned there and
  not on the finding.
- **AC4 and AC5** are the rename. AC5 catches a copy that leaves the old
  rule registered beside the new one.
- **AC6** is the evidence that mode 6 is now served. It derives `specified`
  today.
- **AC7–AC9** are the designation the maintainer chose (Q3) and the verdict
  change it implies.

Not written, because an existing test already fails without them:

- **"Every corpus case's measured firing equals its expected set."**
  `tests/test_147_specification_is_the_record.py::test_ac26_every_corpus_case_agrees_and_status_derives_correctly`
  asserts `case_agrees` for every mode's and condition's case. It is
  reconciled for mode 6's derived status (Testing Strategy).
- **"The manifest's expected labels and verdicts match the pipeline."**
  `tests/test_041_regression_suite.py` (`verify_case`, `offending_labels_match`)
  asserts this for every designated case.

No AC closes a Stage 34 criterion. This is a maintenance item.

## Assumptions

`loop.clarify` was forced to interactive for this batch. The maintainer
answered three questions on 2026-10-12: Q1 rename (B), Q2 spacing along
the spine curve, and Q3 re-designation (A). The remaining defaults are
recorded here.

Every number was measured on `aide/queue-030` at `2a1491d` on 2026-10-12
with `.venv/bin/python`. The scratch probes read `extract_feature_record`
for every case of both corpora and applied the rule as specified below. The
builder re-measures on the real change.

- **A1 (decided: the path-ordered spacing).** The rule computes the spacing
  from fields the record already carries.
  - Every label is sorted by `(per_label.{label}.curve.path_u, int(label))`;
    the integer label breaks ties.
  - Each spacing is `math.dist` between the first three components of
    consecutive labels' `per_label.{label}.centroid.centroid_mm[]`.
  - This needs no new field and no change to `features/consistency.py`.
  - Both detectors use this order for adjacency: neighbours for the size
    ratio, and adjacent spacings.
  - A record is not judged (the rule returns `[]`) when any of these hold:
    - `pairs.adjacent.mean_spacing_mm` is not numeric. This is the existing
      Stage-3 gate, kept as it is.
    - Any `per_label` key is not an integer.
    - Any label lacks a numeric `path_u`.
    - Any label lacks a `centroid_mm` with three numeric components.
    - Any label lacks a numeric `geometry.physical_volume_mm3`.
  - `path_u` is absent whenever Stage 3 is (for example under
    `stage3_unavailable`), so such a record is never judged.
  - **Re-checked 2026-10-13, after item 220 merged (`ef48313`): agrees.**
    Item 220 changed no extractor. It added the `collapsed_labels` rule and
    catalogued the five `stage3_unavailable.*` leaves. On the item-129
    coincident map (`tests/test_129_coincident_centroids_and_held_out_floor.py::_coincident_label_map`),
    `extract_feature_record` writes `stage3_unavailable`, and neither label
    carries `curve.path_u`. `pairs.adjacent` holds only `spacings_mm`, with
    no `mean_spacing_mm`. So this rule returns `[]` on every collapsed record,
    and `collapsed_labels` (mode 13) is the rule that judges it.
- **A2 (measured: the path order silences an order break).** The spacings
  below are in mm, in path order. Path order and anatomical order agree on
  every other case, and every other case reads a largest local gap ratio of
  1.14 or less.

  | Case | Path order | Spacings | Gap at local baseline |
  |---|---|---|---|
  | `relabel_swap` | L1, L3, L2, L4, L5 | 33.49, 32.70, 33.87, 36.84 | largest 1.088 |
  | `sequence_break` | L1, L2, L3, L4, T13 | 33.49, 32.70, 33.87, 36.84 | largest 1.088 |
  | `remove_level` | — | 33.49, 66.38, 36.84 | 1.887 at L2–L4 (labels 21, 23) |
  | `remove_level_relabel` | — | 33.49, 66.38, 36.84 | 1.887 at L2–L3 (labels 21, 22) |

  - In anatomical order `relabel_swap` read 66.0 / 32.7 / 66.38 / 36.84,
    and `sequence_break` read 134.16 at T13–L1. Both would fire a
    spacing-only reading.
  - The four intensity-corpus cases read clean spacing (largest 1.088).
  - **Re-checked 2026-10-13, after item 220 merged (`ef48313`): agrees.**
    The same scratch probe was re-run over both corpora on this branch. It
    gives the path orders, spacings and gap ratios in the table above,
    exactly. All four intensity cases read 1.088 at most. Item 220 pinned the
    manifest and every case's firing as unmoved, and the probe confirms that.
- **A3 (measured: `fused_label` holds on the path-ordered spacing).** With
  item 207/211's statistic unchanged, the detector fires on exactly the
  labels it fires on today:
  - `fuse_adjacent` label 22: size 2.3248, spacing 1.5380.
  - `fuse_separate` label 22: size 2.0016, spacing 1.5371.

  On these cases path order equals anatomical order. Highest silent
  readings:
  - Size: 4.8000 (`split_own_label` label 24, spacing 1.1631) and 1.5263
    (`split` label 24, spacing 1.0512).
  - Spacing: 1.5408 (`remove_level` and `remove_level_relabel`, size
    0.9984).

  `relabel_swap` label 20's 1.7915 under anatomical order disappears,
  because path order reads it 1.0999. The size gate's role is unchanged: it
  alone keeps a missed level's neighbours silent on `fused_label`, as item
  211 recorded.

  **Re-checked 2026-10-13, after item 220 merged (`ef48313`): agrees.** On
  both fuse cases the path order is still 20, 21, 22, 23, which equals
  anatomical order. The path-ordered spacings are 33.49 / 49.51 / 53.52
  (`fuse_adjacent`) and 33.49 / 49.46 / 53.50 (`fuse_separate`). Label 22's
  size ratios read 2.325 and 2.002. So the readings above stand.
- **A4 (decided: no record change).**
  - `pairs.adjacent.spacings_mm[]` keeps its item-216 meaning (anatomical
    order) and is no longer read by any rule.
  - `per_label.{label}.curve.path_u` gains its first consuming rule.
    `per_label.{label}.centroid.centroid_mm[]` gains a second; `sequence`
    reads it today.
  - `FEATURE_DOCS`, `STATUS_OVERRIDES`, `report_schema_v0.json` and
    `features/**` are unchanged. The catalogue's per-path consumers and
    modes move only through the rule's declaration (step 1), and the
    generated catalogue is regenerated (step 7).
  - The net count of paths read by at least one rule is unchanged: one
    leaves (`spacings_mm[]`) and one joins (`path_u`). The builder confirms
    this on the regenerated catalogue.
  - **Re-checked 2026-10-13, after item 220 merged (`ef48313`): corrected.**
    The original bullets above stand as written at `2a1491d`. Item 220 made
    `collapsed_labels` a signal consumer of
    `per_label.{label}.centroid.centroid_mm[]`. That path's consumers are now
    `sequence` and `collapsed_labels`, so this rule becomes its **third**
    consumer, not its second. After this item the entry is read as signal by
    `{centroid_spacing, collapsed_labels, sequence}`.
    - **Measured live on the committed catalogue (`build_catalogue(strict=True)`):**
      159 entries, 104 with empty `mode_evidence`.
    - `centroid_mm[]` carries modes (9, 10, 11, 13).
    - `pairs.adjacent.spacings_mm[]` is read by `fused_label` alone, as
      signal, with modes (2,).
    - `per_label.{label}.curve.path_u` is read by no rule, with modes ().
    - `case.sequence.missing_levels[]` carries (6, 10), and its evidence is
      `("rule_mode_map", "rule_declaration")`.
    - `case.sequence.present_levels[]` carries (6, 10). It is mode 6's only
      `MODE_ANCHOR_PATHS` entry.
    - 11 entries carry mode 2.
  - **What this item therefore moves in the catalogue.** This is predicted
    from the measurement above. The builder re-measures it on the
    regenerated catalogue.
    - The entry count stays 159, and the leaf-path set is unchanged. No
      leaf is added or renamed, because a rule's consumption does not
      create a leaf. So `tests/corpus/119_pre_119_digests.json` (test_119
      AC27, test_120 AC12, test_123 AC49), test_131's
      `_PRE_ITEM_TOTAL_LEAF_PATH_COUNT`, and test_124 / test_132's 159 stay.
    - The empty-evidence count stays 104: `spacings_mm[]` joins it and
      `path_u` leaves it.
    - `centroid_mm[]` gains modes 2 and 6. `path_u` and
      `geometry.physical_volume_mm3` gain mode 6. `missing_levels[]` loses
      mode 6, because no failure case designates `coverage` any more.
    - The mode-2 count goes 11 → 12: `spacings_mm[]` leaves, and `path_u`
      and `centroid_mm[]` join.
- **A5 (pins `features/consistency.py`, item 227's interface).** The rule
  reads `path_u` only to order labels. That needs three properties:
  - `path_u` is a number per label, written by
    `feature_report.build_features_block` from
    `compute_monotonic_consistency(...).u_values`.
  - Distinct path positions sort as the labels sit along the path.
  - `path_u` is absent when Stage 3 is.

  Item 227 changes `_path_positions`' normalisation: the end label's `u` is
  exactly 1.0, and the values are otherwise bit-identical on Python 3.11.
  That preserves the order, so it moves nothing here. The rule does not read
  `pairs.adjacent.non_monotonic_pairs[]`.
- **A6 (decided: the `missing_level` statistic).** For each gap `i` between
  path-consecutive labels `i` and `i+1`:
  - `gap_ratio = sp[i] / mean(sp[j] for j in (i-1, i+1) if 0 <= j < len(sp))`.
    This is the gap over the mean of the one or two spacings beside it (the
    local baseline).
  - It fires when **all three** hold:
    - `gap_ratio > gap_ratio_threshold`, with default `DEFAULT_GAP_RATIO = 1.5`.
    - Label `i`'s size ratio is at most `size_ratio_threshold`, default 1.5.
    - Label `i+1`'s size ratio is at most `size_ratio_threshold`.
  - The size ratio is the volume over the larger path neighbour's volume,
    the same as `fused_label`'s. Requiring both flanking labels to be of
    normal size keeps a fused label whose centroid sits on one body from
    also reading as a missed level (`fused-label-not-reported-as-missing`).
  - A gap with no neighbouring spacing (a two-label record) is not judged.
  - A non-positive baseline, or a non-positive neighbour volume, skips that
    gap.
  - There is no upper band, so a two-level miss (about three pitches)
    fires.
  - The finding's `labels` are the two flanking labels. Its `detector_id`
    is `missing_level`, its reason starts `Missing level:`, and its severity
    is the rule's `severity` param (default `flagged-for-review`, mode 6's
    severity).
  - Measured margins on both corpora:
    - Fires at 1.887 on both remove-level cases, with flanking size ratios
      0.997 and 0.998.
    - Highest silent gap: 2.269 on `split_own_label`'s L4–L5 gap (flanking
      sizes 0.208 and 4.800). The size gate silences it: label L5 reads
      4.8.
    - Highest silent gap that passes the size gate: 1.386
      (`split_own_label` L2–L3).
    - Both fuse cases read at most 1.138.
  - **Re-checked 2026-10-13, after item 220 merged (`ef48313`): agrees.**
    The re-run probe gives every margin above unchanged: 1.887 at
    0.997/0.998, 2.269 gated off by 4.800, 1.386, and 1.138.
    - **One interaction with item 220 was measured, and no AC rests on it.**
      Take a near-coincident pair with Stage 3 present: test_220's
      `_near_record()`. Its spacings are 0.80 and 15.24 mm, so the second
      gap reads 19.05 over its one-spacing baseline.
    - There, `missing_level` is silent only because the size gate fails.
      Label 22 reads 1000 / 600 = 1.667.
    - With equal volumes it would fire on the pair beyond the collapsed one,
      beside `collapsed_labels`. That reads as a co-detection: two labels on
      one body leave a level out of the label sequence. Neither corpus
      carries such a case, so AC1 is unaffected. test_220 runs that record
      through `collapsed_labels` alone (AC4, AC5), so it stays green.
      test_148 AC16's `planted_collapsed` row is a two-label record, which
      this rule does not judge.
- **A7 (measured: why the local baseline, on VerSe19 ground truth).**
  Measured 2026-10-12 on 157 VerSe19 ground-truth masks with at least three
  spacings, of 160 under
  `/mnt/data/spine/data/datasets/VerSe/VerSe19/*/derivatives`. Centroids
  were scipy centres of mass in voxel × zoom mm. These are clean
  segmentations, so any firing is a false positive.

  | Baseline | Max | p99 | Cases above 1.5 |
  |---|---|---|---|
  | Median of the case's other spacings, anatomical order | 1.561 | 1.519 | 6 |
  | Local, anatomical order | 1.378 | 1.269 | 0 |
  | Local, path order | 1.378 | 1.269 | 0 |

  - On all 157 masks the path order (A1, from
    `features.consistency._path_positions`) equals anatomical order, so the
    two local rows agree. The highest reading is `sub-verse207` (C1–T1).
    Only one case reads above 1.3 and none above 1.4.
  - The case-wide median fails because a scan spanning cervical to lumbar
    mixes short and long pitches.
  - The local baseline at 1.5 holds on every clean case. The synthetic
    misses read 1.887.
  - This is real-data evidence for the default only. Stage 21 re-calibrates
    on real data, and Validation step 2 replays it where the cohort exists.
- **A8 (decided: mode 2's at-the-bar sign-off stands).** `gate-0133` signed
  mode 2 at the bar on 2026-10-02. Over both corpora mode 2's firing is
  unchanged (A3), so bar conditions 1–5 still hold.
  - Condition 4's subject changes only in name, from
    `fused_label/fused_label` to `centroid_spacing/fused_label`.
  - `MODE_SIGN_OFFS[2].note` names "fused_label's centroid-spacing
    judgement". It is transcribed text and is left as written: the detector
    still carries that id.
  - No re-sign gate is raised.
  - Mode 6 has no sign-off and gets none here.
- **A9 (decided: expected labels).** The operator expectations name the two
  flanking labels:
  - `remove_level`: the present labels on either side of the target. For
    the corpus case (target 22) that is `{21, 23}`.
  - `remove_level_relabel`: the present label before the target and the
    target number itself, which the next label is renumbered to. For the
    corpus case that is `{21, 22}`.

  The operator computes both from its own label list, so a ladder rung with
  another target stays self-consistent.
- **A10: no human gate and no environment-gated capability.**
  - The VerSe19 cohort is read only by the optional Validation step 2, under
    the existing `SEGFACET_VERSE_COHORT` convention. No test reads it.
  - Queue-030 siblings this spec relies on or collides with are listed under
    Dependencies.

## Implementation Steps

1. **Rename the module.** `git mv src/segfacet/heuristics/fused_label.py src/segfacet/heuristics/centroid_spacing.py`.
   In the new module:
   - Rename the class to `CentroidSpacingRule` and set
     `rule_id = "centroid_spacing"`.
   - Keep `DEFAULT_SIZE_RATIO` and `DEFAULT_SPACING_RATIO`, and add
     `DEFAULT_GAP_RATIO = 1.5`.
   - Update `__all__`.
   - Replace the anatomical-order block with the path-order read of A1.
     `segfacet.labels.anatomical_order` is no longer imported.
   - Keep the `fused_label` loop: same statistic, sacral and coccygeal
     exclusion, and A3 end-label handling.
   - Add the `missing_level` loop (A6) over the same ordered spacings,
     volumes and size ratios.
   - Read the parameters through `config.rule_param(self.rule_id, ...)`:
     `size_ratio_threshold`, `spacing_ratio_threshold`,
     `gap_ratio_threshold` and `severity`.
   - The module and class docstrings say:
     - Both detectors share the A1 order.
     - The A2, A3 and A6 measurements.
     - The scope fence: no feature change, and modes 9 and 10 are not this
       rule's.
2. **The `mode_declaration`** of the renamed rule:
   - `modes=(2, 6)`.
   - Evidence naming `tests/corpus/manifest.json`'s two fuse cases (mode 2)
     and two remove-level cases (mode 6), with the A3 and A6 readings.
   - Consumed paths:
     - `pairs.adjacent.mean_spacing_mm`: bookkeeping, gate (as today).
     - `per_label`: bookkeeping, container.
     - `per_label.{label}.level_name`: bookkeeping, identity and sacral
       exclusion.
     - `per_label.{label}.geometry.physical_volume_mm3`: signal.
     - `per_label.{label}.centroid.centroid_mm[]`: signal.
     - `per_label.{label}.curve.path_u`: signal.

     `pairs.adjacent.spacings_mm[]` is dropped.
   - Two `RuleDetector`s, each with `signal_paths` naming the three signal
     paths:
     - `fused_label`: keep its question, and reword `fires_when` to say "path-ordered".
     - `missing_level`: question "Is there one gap between path-consecutive
       labels of normal size, about twice the spacing beside it, as one
       missed vertebra would leave?"; `fires_when` per A6; `params`
       `(("gap_ratio_threshold", DEFAULT_GAP_RATIO), ("size_ratio_threshold", DEFAULT_SIZE_RATIO))`.
3. **`src/segfacet/heuristics/__init__.py`**: the import line becomes
   `from segfacet.heuristics import centroid_spacing  # noqa: F401 — registers CentroidSpacingRule (items 207, 218)`.
4. **`src/segfacet/failure_modes.py`**:
   - `_MODE_2`:
     - The `IntendedRule` becomes `rule_id="centroid_spacing"`,
       `detector_ids=("fused_label",)`.
     - Both fuse cases' `expected_firing` become `("centroid_spacing",)` and
       `("centroid_spacing", "fragmentation")`.
     - The mechanism and the two reasons name the rule `centroid_spacing`
       (detector `fused_label`) and the path-ordered spacing over
       `per_label.{label}.centroid.centroid_mm[]` and
       `per_label.{label}.curve.path_u`.
   - `_MODE_6`:
     - Add `IntendedRule(rule_id="centroid_spacing", detector_ids=("missing_level",), evidence_rung="synthetic-demonstrable")`.
     - Rewrite the mechanism. Keep the two whole-word case ids, name the
       rule, the detector and its dotted signal paths. Record whatever the
       other rules fire on `remove_level`, re-measured on the tree as built,
       as co-detections. Do not name a rule there that the re-measurement
       does not show; item 219 retires `sequence`'s `skip` and may land
       first. This is the form `tests/test_138_traceability_matrix.py` AC31
       checks.
     - Add `centroid_spacing` to `remove_level`'s `expected_firing`, kept
       ascending, beside whatever rules the tree's set already holds. Then
       re-measure the whole set with `measured_firing`; it must equal the
       result.
     - `remove_level_relabel`'s becomes `("centroid_spacing",)`.
     - Both reasons quote A2/A6, measured 2026-10-12, item 218.
   - Replace every other prose mention of `fused_label` as a *rule*
     (`_MODE_10`'s mechanism and the module docstring's item-207 paragraph)
     with `centroid_spacing`. Add one docstring paragraph for item 218.
   - Leave `MODE_SIGN_OFFS` alone (A8).
5. **`src/segfacet/synth/coverage_border_overlap.py`**: change the two
   operators' `Expectation`s and class docstrings.
   - `RemoveLevelPerturbation`: `expected_rule_ids=frozenset({"centroid_spacing"})`,
     with `expected_labels` the two flanking labels (A9). The verdict stays
     `flagged-for-review`.
   - `RemoveLevelRelabelPerturbation`: `expected_rule_ids=frozenset({"centroid_spacing"})`,
     `expected_labels` per A9 and `expected_verdict="flagged-for-review"`.
     Its `detail` no longer says "not detected".

   In `src/segfacet/synth/component_shape.py`, the two fuse expectations'
   `rule_ids` become `{"centroid_spacing"}` and
   `{"fragmentation", "centroid_spacing"}`. Their detail strings name the
   rule.
6. **Stale descriptions.**
   - `src/segfacet/heuristics/coverage.py`, the comment above
     `mode_declaration` only: `remove_level` now designates
     `centroid_spacing`, and mode 6 carries a rule. The evidence string's
     claim that `remove_level` co-detects coverage stays true and is left
     alone.
   - `src/segfacet/labels.py`: the `anatomical_order` docstring stops naming
     `heuristics.fused_label` as a reader.
   - `src/segfacet/default_config.yaml`: the commented `fused_label` block
     becomes `centroid_spacing`, with `gap_ratio_threshold: 1.5` documented.
     It stays commented, so `config_hash` does not move.
7. **Regenerate.** Run each generator twice into scratch paths, byte-compare
   the two runs, then write the committed copies:
   - `.venv/bin/python -m segfacet.synth.corpus`: the manifest only. The
     fixtures must not change; hand back if one does.
   - `-m segfacet.failure_modes`
   - `-m segfacet.traceability`
   - `-m segfacet.catalogue`
   - `-m segfacet.rule_table`
   - `-m segfacet.golden_evidence`
   - `.venv/bin/python -m segfacet.synth.corpus_sheet`, after the manifest.
     `docs/aide/corpus_sheet.png` embeds a digest of the manifest bytes and
     fixtures, which `tests/test_178_corpus_sheet.py` AC7 compares.

   `golden_evidence` may be byte-identical.
8. **Reconcile the existing tests** listed under Testing Strategy. Add a
   dated `# Item 218 (YYYY-MM-DD): ...` line beside each changed value, the
   house style.
9. **Amend the count clauses.** Use
   `python .aide/scripts/aide.py progress amend` in the shape item 220's
   step 9 uses (the item-208 format), re-measuring every number live first.
   - This item moves the counts again:
     - Mode 6's derived status goes from `specified` to `validated`.
     - Its derived rung goes from none to `synthetic-demonstrable`.
     - One edge is added (`centroid_spacing/missing_level`, at
       `synthetic-demonstrable`).
     - The validated split shifts.
   - The three amends:
     - `amend 30 --criterion 1`: derived status counts over 16 modes, plus
       the validated split.
     - `amend 30 --criterion 3`: derived mode rung counts, plus per-edge
       rung counts over N edges.
     - `amend 20 --criterion 5`: derived status counts and derived mode rung
       counts.
   - Each `--evidence` starts `Item 218 (<date>): mode 6 gains
     centroid_spacing's missing_level edge (synthetic-demonstrable) and
     derives validated. Re-measured live:`.
   - These clauses are what `tests/test_151_stage30_validation.py` AC35 and
     `tests/test_169_stage32_validation.py` AC6/AC7 compare with the live
     derivation.
10. Run `python .aide/scripts/aide.py scope 218` and
    `python .aide/scripts/aide.py check`. Neither may report an error.

No dependency is added. `math.dist` and `statistics.mean` are stdlib. The
size-ratio and severity helpers already in the module are reused.

**Correction (2026-10-13, re-check after item 220 merged at `ef48313`).**
The steps above stand. This adds the figures item 220 moved and one stale
string the original list missed.

- **Step 9's base, measured live on this branch.** Item 220's amends are
  already in `progress.md` (Stage 20 criterion 5, Stage 30 criteria 1 and
  3).
  - Derived status over 16 modes: validated 6, implemented 4, specified 2,
    proposed 4. Validated through a pipeline-detected case 6, through a
    reconstructed record only 0.
  - Mode rungs: synthetic-demonstrable 6, needs-real-data 3,
    structurally-unobservable 1, none 6.
  - Edges: 16, of which synthetic-demonstrable 7, needs-real-data 8,
    structurally-unobservable 1.
- **What this item should leave, before the step-9 re-measurement.**
  - Derived status: validated 7, implemented 4, specified 1, proposed 4.
    The validated split is 7 through a pipeline-detected case and 0 through
    a reconstructed record.
  - Mode rungs: synthetic-demonstrable 7, needs-real-data 3,
    structurally-unobservable 1, none 5.
  - Edges: 17, of which synthetic-demonstrable 8, needs-real-data 8,
    structurally-unobservable 1.
  - The amends use the live numbers, not these.
- **Step 4 addition: `src/segfacet/traceability.py` `_NOTE`.** It says
  "modes 6 and 8 are the two such entries" (specified with no rule). It is
  rendered into both committed traceability documents. After this item only
  mode 8 is such an entry. Reword that clause to name mode 8 alone, with a
  dated item-218 mention in the module's own style, then regenerate in step
  7. The two code comments that say the same (near L1043 and L1309) get the
  same edit. No test pins the clause. test_146 checks only that `_NOTE` contains
  `complete` and `holes`.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/fused_label.py` — removed by the rename (step 1).
- `src/segfacet/heuristics/centroid_spacing.py` — the renamed rule with both detectors (steps 1–2).
- `src/segfacet/heuristics/__init__.py` — the registering import (step 3).
- `src/segfacet/failure_modes.py` — modes 2, 6 and 10 text, edges and expected sets; the docstring (step 4).
- `src/segfacet/synth/coverage_border_overlap.py` — the two remove-level expectations (step 5).
- `src/segfacet/synth/component_shape.py` — the two fuse expectations' rule id (step 5).
- `src/segfacet/heuristics/coverage.py` — one stale comment (step 6).
- `src/segfacet/labels.py` — one stale docstring line (step 6).
- `src/segfacet/default_config.yaml` — the commented rule block (step 6).
- `tests/corpus/manifest.json` — regenerated (step 7).
- `docs/aide/failure_modes.generated.json` — regenerated (step 7).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 7).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 7).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `docs/aide/rules.generated.md` — regenerated (step 7).
- `docs/aide/golden_evidence.generated.json` — regenerated if it moves (step 7).
- `docs/aide/corpus_sheet.png` — regenerated after the manifest; it embeds the manifest digest (step 7).
- `tests/test_218_centroid_spacing_rule.py` — **new**: this item's test module.
- `tests/test_207_fused_label_rule.py` — reconcile (rename).
- `tests/test_211_fused_label_spacing_pair.py` — reconcile (rename; spacing edits on centroids).
- `tests/test_216_neighbour_pair_and_case_level_migration.py` — reconcile (rename).
- `tests/test_040_synthetic_corpus.py` — reconcile (rename; remove_level_relabel now fires).
- `tests/test_038_coverage_border_overlap_perturbations.py` — reconcile (remove-level expectations).
- `tests/test_041_regression_suite.py` — reconcile (no undetected case left).
- `tests/test_098_stray_components.py` — reconcile (remove_level's finding list).
- `tests/test_103_feature_catalogue.py` — reconcile (corpus rule-mode map).
- `tests/test_120_leave_one_out_offset.py` — reconcile (mode 6 case count).
- `tests/test_126_golden_retirement.py` — reconcile only if step 7 moves its counts.
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — reconcile (remove_level's finding set).
- `tests/test_136_rule_mode_declarations.py` — reconcile (co-detections; catalogue buckets).
- `tests/test_137_mode_less_rule_disposition.py` — reconcile (catalogue counts).
- `tests/test_138_traceability_matrix.py` — reconcile (mode 6 leaves the rule-less set).
- `tests/test_144_failure_mode_specification.py` — reconcile (mode 6 exemption).
- `tests/test_145_eight_hypothesised_modes.py` — reconcile (rule-less set; derived status; rename).
- `tests/test_146_ninth_mode_and_first_proposed.py` — reconcile (mode 6 exemptions).
- `tests/test_147_specification_is_the_record.py` — reconcile (mode 6 derived status).
- `tests/test_148_per_path_mode_attribution.py` — reconcile (rename; per-path modes).
- `tests/test_149_conformance_report.py` — reconcile (rule-less set).
- `tests/test_151_stage30_validation.py` — reconcile (edge count); AC35 only if red after step 9's amends.
- `tests/test_169_stage32_validation.py` — only if red after step 9's amends (AC6/AC7 read the count clauses).
- `tests/test_166_split_operator.py` — reconcile (mode 2 edge rule ids).
- `tests/test_167_mode_3_detector.py` — reconcile (mode 2 condition-4 subject).
- `tests/test_176_fuse_bridged.py` — reconcile (measured firing).
- `tests/test_187_neighbour_contact_rule.py` — reconcile (mode 2 condition-4 subject).
- `tests/test_188_coverage_rehomed.py` — reconcile (its mode-6-has-no-rule ACs are superseded).
- `tests/test_220_collapsed_labels_rule.py` — only if red: item 220 pins the manifest and test_129 as unmoved, and this item, landing after it, moves both (Dependencies).

**Correction (2026-10-13, re-check after item 220 merged at `ef48313`).**
The list above stands. Item 220's round 1 went red in tests whose catalogue
pins moved. This item adds no leaf, so the leaf-path pins do not move (A4
re-check), and those files are declared under Asserts against below. It does
move `centroid_mm[]`'s consumers and the corpus rule-mode map. The pins that
follow from that, and the line numbers that moved since 2026-10-12, are named
in Testing Strategy's correction. Every file they touch is already listed
above, except this one:

- `src/segfacet/traceability.py` — `_NOTE`'s "modes 6 and 8" clause and two comments (step 4 correction).

`tests/test_220_collapsed_labels_rule.py` is expected to stay green unedited.
Item 220 pinned the manifest and test_129 only as diff-time claims of its
own branch. Its tests read neither file's content, and nothing this item
changes reaches them: every collapsed record lacks `path_u` (A1 re-check).

**Asserts against:**

- `tests/corpus/fixtures/**` — AC1, AC9 and every adversarial case read the committed fixtures; step 7 must not change them.
- `tests/corpus/intensity/manifest.json` — AC1 drives the intensity cases; no intensity case may fire the rule.
- `tests/test_163_specificity_ratchet.py` — must stay green unedited: no case fires a rule it does not expect.
- `tests/test_202_rule_table.py` — must stay green unedited once step 7 regenerates `rules.generated.md`.
- `tests/test_104_feature_catalogue_drift.py` — must stay green unedited once step 7 regenerates the catalogue.

Added 2026-10-13 by the re-check after item 220. These are the leaf-path
pins item 220 had to bump. This item adds no leaf, so they hold unedited.

- `tests/corpus/119_pre_119_digests.json` — `catalogue_leaf_path_set_sha256` stays `82f9a70d…f21`; test_119 AC27, test_120 AC12 and test_123 AC49 read it.
- `tests/test_131_tangent_direction_normalisation.py` — `_PRE_ITEM_TOTAL_LEAF_PATH_COUNT` stays 159.
- `tests/test_124_observed_range.py` — L566's catalogue entry count stays 159.
- `tests/test_132_monotonicity_against_traversal_order.py` — L739's leaf count stays 159, and `_PRE_ITEM_OBSERVED_SUMMARY` does not move.

## Testing Strategy

The test module is `tests/test_218_centroid_spacing_rule.py`, with one test
per AC. Records come from committed corpus cases through
`extract_feature_record(loaded_seg_image(case), bundled_default_config())`.
Edits are made to a `copy.deepcopy` of a record, never to a hand-built one.

Adversarial cases, each with the failure mode it guards, and no others:

- `distant-relabel-silent`: in the clean-control fixture, exchange labels 20
  and 23 voxel-wise and run `run_qc`. The run has no `centroid_spacing`
  finding. It guards a spacing taken in label order. The exchange puts
  three-pitch gaps into anatomical order, but none into path order.
- `fused-label-not-reported-as-missing`: in the fuse_separate record, move
  label 22's `centroid_mm` onto label 21's side, to 1.0 × the L1–L2 pitch
  beyond label 21 along the 21→23 direction. Its two spacings then read
  about one and two pitches, and `path_u` is unchanged. The rule returns a
  `fused_label` finding on 22 and no `missing_level` finding. It guards the
  flanking-size gate (A6): without it, a fused label whose centroid sits on
  one body also reads as a missed level.
- `end-gap-judged-on-one-neighbour`: in the clean-control record, move label
  24's `centroid_mm` one L4–L5 pitch further along the L4→L5 direction, so
  the last gap reads about two pitches. The rule returns one
  `missing_level` finding with `labels == frozenset({23, 24})`. It guards an
  end gap skipped or mis-indexed, because the baseline has one spacing
  there.
- `two-labels-not-judged`: a record reduced to two labels, built by deleting
  every other `per_label` entry from a deep copy of the clean-control
  record. The rule returns `[]` and raises nothing. It guards `mean([])` and
  a division by an empty baseline.
- `missing-path-u-not-judged`: delete one label's `curve.path_u` from the
  remove_level_relabel record. The rule returns `[]` and raises nothing. It
  guards a `KeyError` on a partial Stage-3 record (A1).
- `gap-threshold-read-from-own-section`: run `remove_level_relabel` with
  `config.rules["centroid_spacing"]["params"]["gap_ratio_threshold"] = 1000.0`.
  No `missing_level` finding results. It guards the parameter being read
  from another section or name after the rename.

**Existing tests to reconcile.** These were found 2026-10-12 by grepping
`tests/` for `fused_label`, `FusedLabelRule`, `remove_level_relabel`,
`mode 6`, the rule-less mode sets and the per-path catalogue counts. They
are a lower bound (`CLAUDE.md`, "A spec-time probe ... is a lower bound").
The validator reconciles any further hit the same way.

- **Rename only** (rule id, import, config section, or the
  `rule/detector` subject string):
  - `test_207`: import; the rule-id filter becomes `centroid_spacing` and
    detector `fused_label`, so AC1's triple set stays the two fuse cases;
    `modes_for_detector("centroid_spacing", "fused_label")`; the config
    section.
  - `test_216`: import and the rule-id filter (detector `fused_label`).
  - `test_166` L396: the mode-2 rule-id set.
  - `test_167` L440 and `test_187` L359: `"centroid_spacing/fused_label"`.
  - `test_176` L252: `measured_firing == ("centroid_spacing",)`.
  - `test_148` L883: the `fuse_adjacent` expected tuple.
- **`test_211`**: the rename, plus every `_with_pair` edit. The rule no
  longer reads `pairs.adjacent.spacings_mm`, so each pair `(a·p, b·p)`
  becomes a centroid edit.
  - Place label 22's centroid at `c21 + a·p·d̂` and label 23's at
    `c21 + (a+b)·p·d̂`. Here `p` is the 20→21 spacing, `d̂` is the unit
    vector from label 21's centroid to label 23's original one, and the
    `path_u` values are left as they are.
  - Each case's expected outcome is unchanged.
  - In `test_missing_vertebra_not_fused`, filter findings to
    `detector_id == "fused_label"`, because `missing_level` now fires on
    that case.
- **`test_040`**:
  - L515: `["centroid_spacing"]`.
  - L523: `("centroid_spacing", "fused_label", [22])`.
  - `test_remove_level_relabel_case_records_mode_6_and_honestly_fires_nothing`
    is re-stated: the case fires the rule, with verdict flagged-for-review.
- **`test_038`**:
  - L232–233: `remove_level`'s rule ids and expected labels (A9).
  - L241–250: the docstring and assertion that `expected_labels` stays
    empty.
  - L352–354: `remove_level_relabel`'s expectation.
  - `_designated_rule_fires`: both branches now check a `centroid_spacing`
    `missing_level` finding on the expected labels.
- **`test_041`**: `_UNDETECTED_PIPELINE_CASES` becomes empty, so
  `test_ac5_undetected_failure_case_fires_nothing_and_verifies` collects
  nothing. Retire it, with a dated comment naming item 218.
- **`test_098`**: `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS["remove_level"]`
  gains the `centroid_spacing` finding at its sorted position. Item 224
  also edits this module.
- **`test_129`**: `_PRE_129_FINDINGS["remove_level"]` gains
  `("centroid_spacing", (21, 23))`.
- **`test_120`**: the per-mode `n_cases` sum goes 11 → 12, and
  `mode_six.n_cases` goes 1 → 2.
- **`test_103`**: `_RULE_MODE_MAP` drops `"coverage": (6,)` (no failure case
  designates coverage any more), and `"fused_label": (2,)` becomes
  `"centroid_spacing": (2, 6)`.
- **`test_136`**:
  - `expected_co_detections` drops `("coverage", 6)`.
  - The catalogue bucket counts are re-measured from the regenerated
    catalogue (L870–895).
- **`test_137`**: `mode2_count`, plus any distribution bucket the
  regenerated catalogue moves.
- **`test_126`** L1077: only if its counts move.
- **Mode 6 leaves the rule-less set:**
  - `test_138` `RULELESS_SPECIFIED_MODES`: `{6, 8}` → `{8}`.
  - `test_145`:
    - `_RULELESS_SPECIFIED_MODE_IDS`: `(6, 8)` → `(8,)`.
    - L131: mode 6 → `"validated"`.
    - L909: the rule-id filter.
  - `test_144` L1271 and `test_146` L1231, L1868: the `(6, 8)` exemptions
    → `(8,)`.
  - `test_147` L1239: mode 6 → `"validated"`.
  - `test_149` L582: the rule-less set.
- **`test_151`** L485: the specification edge count gains one (mode 6's).
  Item 220 also changes it.
- **`test_188`**: AC3 (mode 6 carries no edge), AC5 (no rule declares mode
  6), AC7 (mode 6 derives `specified`) and AC8 (mode 6's rung is `None`)
  are superseded. Re-state each as today's fact, with a dated note:
  - The edge is `centroid_spacing/missing_level`.
  - `centroid_spacing` declares mode 6.
  - Mode 6 derives `validated`.
  - Its rung is `synthetic-demonstrable`.

  AC6 (both remove-level cases stay on mode 6) holds unchanged.

Red until step 7's regeneration lands, with no test edit: the drift tests
that compare a committed generated document with a fresh render. These are
the ones item 211 lists, plus `test_104` and `test_202`.

Stale prose that asserts nothing is left alone: comments naming
`fused_label` in `test_120`, `test_136`, `test_137`, `test_145` and
`test_151`.

**Correction (2026-10-13, re-check after item 220 merged at `ef48313`).**
The list above stands. Item 220 moved several of its literals and line
numbers, and its own test_103 reconciliation goes red again under this item.
Each file below is already under May change, and the same fence holds: a
moved literal, a re-pointed exemplar, or a row in an existing table's own
shape, each with a dated item-218 comment, and none retired, skipped,
`xfail`ed or loosened (test_041 AC5's retirement above is the one stated
exception).

- **test_103, `test_ac13_rule_mode_map_effect_on_failure_modes[sequence]`
  (new; red without this edit).**
  - Item 220 widened the match set to signal entries whose
    `consuming_rules` are a subset of `{rule_id, "collapsed_labels"}`
    (L689–697). After this item, `centroid_mm[]` is consumed by
    `{centroid_spacing, collapsed_labels, sequence}`. `sequence`'s match set
    is then empty again, and the precondition fails.
  - Widen the subset to `{rule_id, "collapsed_labels", "centroid_spacing"}`.
  - Where `centroid_spacing` consumes the entry as signal, add its declared
    modes to `expected`, beside item 220's `collapsed_labels` addition
    (L705–708).
  - Equality stays exact. `sequence`'s expected set should become the
    entry's live `failure_modes`, predicted `{2, 6, 9, 10, 11, 13}`.
  - The new `centroid_spacing` parametrisation's match set should be
    `{per_label.{label}.curve.path_u}`. No other rule reads it, and
    `centroid_mm[]` and `physical_volume_mm3` are shared.
  - The `_RULE_MODE_MAP` edit above is unchanged.
- **test_147.**
  - L1240: `_EXPECTED_DERIVED_STATUS[6]` becomes `"validated"`. That is the
    line the original list gave as L1239.
  - **AC8 at L496 (new):** the edgeless-mode set goes
    `{5, 6, 7, 8, 12, 14}` → `{5, 7, 8, 12, 14}`. Mode 6 gains its edge.
    Item 220 had already dropped 13.
- **test_149 L594** (was L582): `_DEGENERATE_MODES` goes
  `(5, 6, 7, 8, 12, 14)` → `(5, 7, 8, 12, 14)`.
- **test_151 L493** (was L485): `total_edges == 16` → `17`. Item 220 moved
  it 15 → 16.
- **test_146:**
  - L1239: `(6, 8)` → `(8,)`. That is the "L1231" above.
  - L1883: `proposed_mode_ids + [6, 8]` → `+ [8]`. That is the "L1868"
    above.
  - L1234's authored `specified_ids` list is unchanged, because mode 6's
    authored status stays `specified` (A8).
- **test_148 L886** (was L883): `fuse_adjacent`'s row becomes
  `("centroid_spacing",)`. Item 220's `planted_collapsed` row and the
  `remove_level` row's `("coverage",)` hold. AC16 checks containment, and
  `coverage` still co-detects on `remove_level`.
- **test_137 `test_adv_measured_artifact_movement_counts_from_spec`.**
  These are predicted from the A4 re-check. Re-measure them on the
  regenerated catalogue.
  - `mode2_count` goes 11 → 12.
  - `("rule_mode_map", "rule_declaration")` goes 12 → 11. `spacings_mm[]`
    leaves, `path_u` joins, and `case.sequence.missing_levels[]` leaves.
  - `("rule_declaration",)` goes 3 → 4, as `missing_levels[]` joins.
  - `case.sequence.present_levels[]` leaves the five-source bucket, which
    goes 1 → 0 and is removed from the exhaustive table. It enters a new
    bucket, `("per_mode_metric", "rule_declaration", "rule_mode_less", "rule_bookkeeping")`,
    which gets a row of 1. Its mode 6 now comes from its anchor alone, and
    no failure case designates `coverage`.
  - `()` stays 104, and the total stays 159.
- **test_136 L894:** `stayed_empty` is predicted to stay 104. L884's 159 and
  the rule counts of 15 (L198, L261) hold, because this is a rename.
- **Unmoved by this item, despite item 220 having moved them:**
  - test_137 L242, test_148 L366 / L1137 and test_187 L252: the rule count
    of 15.
  - test_189 L190: `fov_truncation`'s `opting_in_rules`. `fused_label` opts
    in to no condition, and this item adds none.
  - test_138 AC20's analytic-edge witness: the new mode-6 edge is
    corpus-designated by `remove_level`.
  - test_216 AC1's `stored` set: no leaf moves.
  - The leaf-path pins under Asserts against.

## Validation

1. Replay the two remove-level cases and one fuse case through the CLI:

   ```
   .venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/remove_level_relabel_seg.nii.gz --out <tmp1> --no-reference
   .venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/remove_level_seg.nii.gz --out <tmp2> --no-reference
   .venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/fuse_adjacent_seg.nii.gz --out <tmp3> --no-reference
   ```

   `--no-reference` is needed for the reason `CLAUDE.md` gives.
   - `<tmp1>`: one `centroid_spacing` finding with reason starting
     `Missing level:` on labels 21 and 22, and verdict `flagged-for-review`.
   - `<tmp2>`: the same finding on 21 and 23. Any other rule's findings
     there are co-detections; compare them with `remove_level`'s re-measured
     expected set.
   - `<tmp3>`: `centroid_spacing`'s `Fused label:` finding on 22.
2. Where `SEGFACET_VERSE_COHORT` points at a VerSe19 checkout, replay A7's
   path-order measurement with the rule itself. Run `run_qc` (no reference)
   over every ground-truth mask, count `missing_level` findings, and record
   the count and the commit in Decisions & Trade-offs. Expected: 0. Where
   the cohort is absent, record **❓ Unverified (VerSe19 absent)** rather
   than a pass. No `[validation]` profile exists for it.

## Dependencies

- Item 220: it pins `tests/corpus/manifest.json` and
  `tests/test_129_coincident_centroids_and_held_out_floor.py` as unedited
  ("no case's firing may move"), and this item changes both. This item lands
  after it.

**Downstream:**

- Item 219 also edits `src/segfacet/failure_modes.py` (modes 9 and 10, and
  `remove_level`'s expected set, from which it retires `sequence`'s `skip`).
  Step 4 adds `centroid_spacing` to that set rather than writing a literal,
  so either order works. It also keeps
  `per_label.{label}.curve.path_u` and `centroid.centroid_mm[]`, which this
  rule reads. Whichever of the two lands later re-measures the shared
  expected sets and the mode-10 mechanism.
- Item 223 re-attributes catalogue reads, and its "Read by ≥1 rule" bound
  sees this item's net-zero change (A4).
- Item 224 edits `tests/test_098_stray_components.py`.
- Item 227 changes `_path_positions` within the order-preserving bound A5
  pins.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** mode 6's `observability` stays `needs-ground-truth`. The
  rule sees an interior miss from the label map alone, but a miss at either
  end of the field of view leaves no gap. Whether the mode's class should
  change is a taxonomy question for the maintainer, not this item's.
- **Left open:** a vertebra missed at either end of the scan is not
  detected. There is no spacing beyond the last label, and the two
  hypothesised end signals in mode 6's mechanism (extrapolating to the image
  face, an untouched scan boundary) stay unbuilt.
- **Left open:** two misses with one vertebra between them make two adjacent
  gaps of about two pitches. Each gap is the other's local baseline, so
  their ratio reads about 1.0 and neither fires. No corpus or ladder case
  expresses it.
