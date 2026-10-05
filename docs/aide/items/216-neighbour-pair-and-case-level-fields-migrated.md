<!-- aide-template: item 3 -->
# Item 216 — Neighbour-pair and case-level fields migrated under the signed taxonomy

> **Created:** 2026-10-05 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 27 — Feature Schema Taxonomy & Coordinate System
> **Queue:** [`../queue/queue-029.md`](../queue/queue-029.md) · Item 216
> **Objectives:** G8
> **Suggested branch:** `aide/216-neighbour-pair-and-case-level-fields`

---

## Description

Roadmap Stage 27 D2, second half. Every row that item 214's signed mapping
table gives **Moved by 216** is put at its new path, and every reader of
those paths is re-pointed in the same change. On top of item 215's tree, the
catalogue and the other generated artifacts are regenerated. After this item
the regenerated catalogue's paths are exactly the table's new paths, and no
top-level container is left that the signed table does not populate.

**This spec is written before both producers exist.** Item 214's design note
`docs/feature-taxonomy.md` and its mapping table are not built, and nor is
item 215's migrated record. So every criterion below is stated against the
table ("every row with Moved by 216", "the survivor"), never against a
guessed new path. The Authorised paths cover every reader that could need
re-pointing under any design that keeps the queue's scope axis. They are
re-checked at claim (Implementation Steps, step 0), once item 214 has merged,
gate-0080 is approved and item 215 has merged. If the signed design departs
from the scope axis, this item is re-cut at that gate (queue 029, "Re-plan at
the gate"), not amended here.

**What moves (A2).** The table has 165 rows: the catalogue's 145 paths plus
20 report-only `reference_delta.{label}.features.<name>.<stat>` paths, and
those 20 are item 215's. This item owns the 39 rows item 215 leaves:

- `relationships`, `relationships.*` (6 rows);
- `overlaps[]`, `overlaps[].*` (6 rows);
- `stage3.curvature.*` (8 rows). This is what the queue calls "spline fit":
  the record serialises no spline-fit block of its own;
- `stage3.spacing_consistency.*` (5 rows);
- `stage3.monotonic_consistency.*` (3 rows);
- `image_features.{available, backend, image_features_version,
  radiomics_available}` (4 rows, the case-level intensity fields);
- `reference_delta.{lower_pct, upper_pct, reference_delta_version,
  reference_schema_version, reference_source, stratum}` (6 rows);
- `features_version` (1 row).

**This item deliberately changes what is measured** (maintainer decisions
of 2026-10-05, D1, D9 and D10). The two stored adjacent-pair spacing arrays
collapse into one, **the survivor**. In the maintainer's words: *"the
integer-label order is anatomically meaningless"*.

- **Today there are two arrays.**
  - `relationships.neighbour_spacings_mm[]` is stored in anatomical order,
    over recognised levels only. It is present whenever the map has at least
    one label.
  - `stage3.spacing_consistency.spacings_mm[]` is stored in integer-label
    order, over every label. It is present only when Stage 3 runs.
- **Both end at one path.** Item 214's AC8 pins that exactly one of the two
  rows is `merged` onto the other's new path, and the note's Answer 6 names
  which.
- **What the survivor holds.** It is stored in anatomical order over every
  label, with unrecognised labels kept and placed last (the item-198
  ordering, D9). It is available exactly as `relationships` is today (D10):
  - present on every record with at least one label;
  - `[]` only below two labels;
  - computed on a coincident-centroid record too, as `relationships` is now.
- **What stays Stage-3-only.** The four derived statistics
  (`mean_spacing_mm`, `cv_spacing`, `deviations_mm[]`, `outlier_pairs[]`)
  stay Stage-3-only. They are derived from the survivor's sequence.
- **`fused_label`** judges the survivor in the same order (step 5).

Wherever the integer and anatomical orders disagreed, the survivor's values,
the four statistics and `fused_label`'s pairing change by decision. So do
`relationships.neighbour_spacings_mm`'s values on a record carrying an
unrecognised label, which that array dropped. **This is the one authorised
exception, in Stage 27, to criterion 3's "no rule's behaviour changes".**
Item 217 attests it as explicitly authorised, citing D1.

- On the committed corpora it changes the measured values of exactly one
  case, `sequence_break`.
- It changes no rule's firing anywhere in either corpus (A5, D8).
- AC5 is what shows the rule-level change.

**The insight rider (`2026-10-05-c980`).** The report schema's
`monotonic_consistency` descriptions are corrected in the same edit. Today
they still call `u` a spline parameter, but since item 210 `u` is the
normalised arc length along a label-free MST longest path (AC6). The change
is to description text only. The inbox entry is ticked when this queue
absorbs it, on the validator and merge side. The builder never edits
`docs/aide/insights.md` by hand.

**What it is NOT.**

- **No per-label row moves.** Those are item 215's, already merged (A4). That
  includes the 20 report-only rows and the extended reference-delta catalogue
  driver that lists them. The driver stays in place.
- **No field is dropped** (D2). The only paths that disappear are those the
  table marks `merged`: the spacing array that does not survive, and any
  pair-identity copy item 214's Answer 1 marks `merged`.
- **No other value changes.** Every `kept` or `moved` row outside the spacing
  family carries the same value at its new path.
- **No rule's firing changes on either committed corpus** (D8). No threshold
  or corpus manifest changes, and no reference artifact is rebuilt.
- **No extractor and no in-memory result type changes** (D4).
- **No re-bump of a version discriminator item 215 already bumped** (D5).
- **No attestation.** No criterion carries a *(closes Stage 27 criterion M)*
  annotation. Stage 27 criterion 2 has two halves: AC1 here is its
  addressability half, and item 215's AC1 is its identity half. Item 217
  attests criterion 2 from both, and criterion 3 from the corpus ratchet
  together with D1.

### The split with item 215

The split is the one item 215's spec states, and it holds without exception.

- **Ownership is by table row.** This item edits only the code, docs rows,
  schema definitions, path strings and test lines that name a row with Moved
  by 216. Generated artifacts are regenerated whole on top of item 215's
  output. That covers the catalogue path-set digest and every count pin item
  215 moved, each moved again from the value item 215 left.
- **Item 215's guarantees stay true unedited.**
  - Its AC1–AC3 and its `level-name-read-from-survivor` case, in
    `tests/test_215_per_label_migration.py`, must pass with no edit.
  - No leaf this item adds has the bare last segment `label` or `level_name`.
    Pair identity keeps distinct key names, as `overlaps[]`'s `label_a` and
    `name_a` do today.
  - So that file is not on May change.
- **Item 214's tests are untouched.** `tests/test_214_feature_taxonomy_design.py`
  is left as it stands through the stage. Its AC1 compares the table against
  a frozen literal.

## Acceptance Criteria

Terms used below:

- **The table** is the list of `(old, new, change, moved_by)` rows that
  `tests/feature_taxonomy_mapping.py::read_mapping()` returns from
  `docs/feature-taxonomy.md` (A1). **216's rows** are the rows with
  `moved_by == 216`. **`new(p)`** is the new path of the row whose old path is
  `p`.
- **The catalogue's path set** is the `path` of every entry under
  `groups[*].entries[*]` in `docs/aide/feature_catalogue.generated.json`,
  read live. `tests/test_104_feature_catalogue_drift.py` holds that file equal
  to a fresh build.
- **The survivor** is the shared new path of the two rows whose old paths are
  `relationships.neighbour_spacings_mm[]` and
  `stage3.spacing_consistency.spacings_mm[]` (item 214's AC8).
- **A case's report** is the `segfacet_report.json` that
  `segfacet.cli.main(["run", "--scan", <scan>, "--seg", <seg>, ...flags, "--out", <tmp_path>])`
  writes for the corpus manifest case with that `case_id`. `<seg>` and
  `<scan>` are resolved through `segfacet.synth.corpus.load_manifest()` and
  `CORPUS_DIR`.
  - **The clean-control report** is run with flag `--intensity` and no
    reference flag, so the bundled VerSe19 reference applies and every
    optional block is present (item 215's "case report").
  - **The sequence-break report** is run with flag `--no-reference`.
- **Resolving a catalogue-notation path `P` in a report** means walking `P`
  in `report["features"]` when its first key is there, and otherwise in the
  report's top level. A segment `{…}` iterates a mapping's values in key
  order. A trailing `[]` iterates a list. The values are returned in that
  record order.
- **A report's leaf paths** are item 215's definition:
  `segfacet.catalogue.iter_leaf_paths(content)`. `content` is the report
  without `schema_version`, `config_version`, `case_id`, `verdict`, `reasons`,
  `per_label`, `findings` and `run_manifest`. One leading `features.` segment
  is stripped from each path.
- **A path's container** is its text before the first `.`, with one trailing
  `[]` removed.
- **The anatomical sequence** of a report is all its labels, sorted by the
  item-198 key. The key is the `CANONICAL_ORDER` rank of the label's level
  name, with names outside `CANONICAL_ORDER` ranked last, then the integer
  label. Each label's level name and centroid are read by resolving
  `new("per_label.{label}.level_name")` and
  `new("per_label.{label}.centroid.centroid_mm[]")`.
- **The T13 variant** is the `fuse_adjacent` case's committed segmentation
  with every voxel of label 20 set to 28 (T13). It is read through
  `segfacet.synth.regression.loaded_seg_image` and rebuilt as a
  `Nifti1Image`. **The unknown-label variant** is the same with label 23 set
  to 99, a value the default convention leaves unnamed.
- **The monotonic descriptions** are the `description` strings in two places:
  - anywhere inside the schema definition `stage3MonotonicConsistency`
    (definition keys are kept, D6), including the definition's own;
  - on every property whose `$ref` is
    `#/definitions/stage3MonotonicConsistency`, wherever its new path puts
    it.

- [ ] **AC1: the catalogue's paths are exactly the table's stored paths.** The
      catalogue's path set equals the set of new paths of all 165 rows (215's
      and 216's) whose change is `kept` or `moved`.
- [ ] **AC2: every top-level container in the record is one the table
      populates.** The set of containers of the clean-control report's leaf
      paths equals the set of containers of the table's `kept`/`moved` new
      paths.
- [ ] **AC3: the survivor holds the anatomical-order spacings.** On the
      sequence-break report, the values found by resolving the survivor equal,
      to `abs=1e-9`, the Euclidean distances between consecutive centroids of
      the anatomical sequence.
- [ ] **AC4: the spacing deviations are derived from the survivor.** On the
      sequence-break report, the values found by resolving
      `new("stage3.spacing_consistency.deviations_mm[]")` equal, to
      `abs=1e-9`, `[s - mean(S) for s in S]`, where `S` is the survivor's
      resolved values.
- [ ] **AC5: `fused_label` pairs each spacing with anatomically adjacent
      labels.** For the T13 variant, the `fused_label` findings of
      `segfacet.pipeline.run_qc(variant, bundled_default_config())` have
      label sets equal to `[frozenset({22})]`. Before this item the list is
      empty, because integer order pairs T13 last (A6).
- [ ] **AC6: no monotonic description calls `u` a spline parameter.** None of
      the monotonic descriptions in `src/segfacet/report_schema_v0.json`
      matches `spline[ -]parameter`, compared case-insensitively.

These criteria close no stage acceptance criterion.

**Recognisability, asserted before each claim (§6):**

- **AC1.** 216's rows number 39, the table has rows of both owners, and the
  catalogue's path set is non-empty.
- **AC2.** The report's container set has at least two members.
- **AC3 and AC4.** The anatomical sequence differs from ascending integer
  order on this case, so the claim cannot pass on a case where the two orders
  agree. The resolved survivor has `len(labels) - 1` values.
- **AC5.** The T13 variant's integer and anatomical orders differ, and the
  unmodified `fuse_adjacent` case fires `fused_label` on label 22.
- **AC6.** The definition `stage3MonotonicConsistency` exists. At least one
  schema property references it. Its `u_values` property has a non-empty
  description.

The queue's other two *Testable* claims are not restated as criteria:

- **"The catalogue and its drift test agree"** is
  `tests/test_104_feature_catalogue_drift.py`, as reconciled.
- **"Every corpus case's measured firing equals its expected set, unchanged"**
  is
  `tests/test_163_specificity_ratchet.py::test_ac2_ratchet_measured_equals_expected`,
  unedited and over unedited manifests (D8).

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

Everything measured below was measured on 2026-10-05 at `f5c79df`
(`aide/queue-029`). The orchestrator ran clarify as interactive. The
maintainer's answers of 2026-10-05 are recorded under Decisions & Trade-offs
(D1–D3 and D8–D10), not here. A1–A4 pin unbuilt dependencies and are
re-checked at claim (step 0).

- **A1 (pin, item 214): the table is read through item 214's reader module
  only.**
  - `tests/feature_taxonomy_mapping.py` exposes `NOTE_PATH` and
    `read_mapping(text=None)`.
  - `read_mapping` returns a list of `(old, new, change, moved_by)` tuples in
    table order. `change` is in {`kept`, `moved`, `merged`}, and `moved_by` is
    an `int` in {215, 216}. A malformed row raises `ValueError`.
  - The old paths are the 165 pre-migration paths that item 214's AC1
    freezes: the catalogue's 145 plus 20 report-only `reference_delta` paths.
  - A new path uses the catalogue's notation (`{label}`, `[]`,
    `{radiomic}`), plus any placeholder segment the note's `## Structure`
    defines.
  - A `merged` row's new path is the new path of some `kept` or `moved` row.

  This spec never parses the note itself.
- **A2 (pin, item 214): 216's rows are the neighbour-pair and case-level
  scope.** They are exactly the 39 rows listed in the Description:
  6 + 6 + 8 + 5 + 3 + 4 + 6 + 1. That is the 165 rows minus item 215's 126,
  which are 106 catalogue rows plus the 20 report-only rows. Step 0 compares
  this against the signed table. A row assigned differently is re-cut at the
  gate.
- **A3 (pin, item 214): Answer 6 settles two things this spec cannot.**
  - **Which of the two spacing rows is the survivor.** Under item 214's AC8,
    exactly one is `merged` onto the other's new path. AC3–AC5 read the
    survivor through the table, so they hold either way. The label set and
    availability are not open: they are decided (D9, D10).
  - **Whether the per-element spacing copy is re-derived from the survivor.**
    That copy sits behind `stage3.per_label_neighbourhood[].stats.spacing_mm.*`.
    Its paths are item 215's, but a value change there would land here (Left
    open).

  Step 0 records both, dated, in Decisions.
- **A4 (pin, item 215): the tree this item builds on.**
  - Every 215 row is at its new path, and the catalogue lists the 20
    report-only rows through 215's extended reference-delta driver.
  - `per_label.{label}.level_name` and `per_label.{label}.centroid.*` are
    `kept` (215's A7 default). The anatomical sequence reads them through
    `new(...)` in any case.
  - `FEATURES_VERSION_STAGE3` is `"0.3"`, and the top-level report
    `schema_version` is `"0.1"` (215's D5). Whether 215 bumped the base
    `FEATURES_VERSION` is recorded at 215's step 0, and step 7 reads it.
  - `tests/test_215_per_label_migration.py` is green.
  - `tests/corpus/119_pre_119_digests.json` and the count pins hold item
    215's values.
  - Every `"stage3"` access that names a 215 row has been re-pointed.

  Step 0 re-runs the fence greps on that tree, because what is left of the
  `stage3` container after item 215 decides which of this item's listed
  files still need an edit.
- **A5 (measured): the collapse is visible on exactly one committed case, and
  changes no firing.** All 18 cases were run through `run_qc`: 14 geometric
  and 4 intensity. On 17 of them the integer and anatomical orders agree, no
  label is outside `CANONICAL_ORDER`, and the two stored arrays are equal.
  The exception is **`sequence_break`**, with labels 20–23 and 28, where 28
  is T13:
  - **integer order** is L1 L2 L3 L4 T13, and `spacings_mm[]` is
    [33.4940, 32.6952, 33.8724, 36.8400], with mean 34.2254, cv 0.0458 and
    `outlier_pairs` [];
  - **anatomical order** is T13 L1 L2 L3 L4, and `neighbour_spacings_mm[]` is
    [134.1605, 33.4940, 32.6952, 33.8724]. The statistics derived from it are
    mean ≈ 58.556, cv ≈ 0.746, deviations ≈ [75.605, −25.062, −25.860,
    −24.683] and `outlier_pairs` [["T13", "L1"]], because 134.16 ≥ 2 × mean.

  **Firing does not change there.**
  - Read in anatomical order, `fused_label`'s spacing ratios rise to 4.0055
    (T13) and 2.5186 (L1). But no label's size ratio exceeds 1.0032, against
    a `size_ratio_threshold` of 1.5, so the rule cannot fire on this case
    whatever the spacing.
  - No other rule reads the spacing family. `mislabel` reads
    `monotonic_consistency`, whose values this item does not change.
  - So the case keeps firing `mislabel` {20, 28} and `sequence` {28}, and its
    committed expectation (`expected_rule_ids` `["sequence"]`, labels `[28]`)
    is untouched.

  `relationships.neighbour_spacings_mm[]` already equals the survivor on all
  18 cases, because none carries an unrecognised label. So the value change
  is visible only in the `sequence_break` record's Stage 3 spacing family, and
  in the catalogue's observed range for the survivor: the base
  `spacings_mm[]` range is 32.6952–66.3769, and 134.161 joins it. AC5's
  variant is what shows a rule-level change.
- **A6 (measured): the two `fuse_adjacent` variants.** These are
  `fused_label` readings, in the form (size ratio, spacing ratio), against
  thresholds 1.5 and 1.25.
  - **T13 variant (20 → 28).**
    - Today the rule pairs in integer order (L2 L3 L4 T13). Label 22 reads
      (2.3248, 0.384), and nothing fires.
    - Paired in anatomical order (T13 L2 L3 L4), label 22 reads
      (2.3248, 1.538), and the rule fires on {22}.
  - **Unknown-label variant (23 → 99).**
    - Today the rule fires on {22}.
    - With the decided every-label survivor (L1 L2 L3, then the unknown
      label), label 22 reads (2.3248, 1.538) and fires.
    - If the survivor dropped the unrecognised label, as
      `relationships.neighbour_spacings_mm` does today, it would hold 2
      spacings against 4 labels. `fused_label`'s count check would then
      return `[]` with no error.
- **A7 (measured): the code facts behind step 1.**
  - **`relationships`** is computed for every record with at least one
    label (`pipeline.py` lines 130–133). `compute_spine_relationships`
    returns `neighbour_spacings_mm == []` for a single label.
  - **`compute_spacing_consistency`** raises `ValueError` below 2 centroids
    (`features/consistency.py` lines 250–256). It is called only in the
    branch with at least 2 labels and no coincident centroids
    (`pipeline.py` lines 169–232).
  - **The item-198 anatomical sort** is likewise built only inside that
    branch (lines 209–215).
  - **On a coincident-centroid record** the branch is skipped and
    `stage3_unavailable` is set. `relationships` is still computed.
- **A8 (measured): who reads 216's rows.** The grep under Authorised paths
  found these readers in `src/segfacet`. The extractors and `sequence.py`
  only mention the paths in dated history prose.
  - **Rules:**
    - `heuristics/coverage.py`, `border.py` (through `fov.py`'s
      `derive_fov_coverage`) and `fov.py` read `relationships.*`;
    - `heuristics/overlap.py` reads `overlaps[]`;
    - `heuristics/mislabel.py` reads `stage3.monotonic_consistency`;
    - `heuristics/fused_label.py` reads `stage3.spacing_consistency.spacings_mm`;
    - `heuristics/intensity.py` reads `image_features.available`;
    - `heuristics/reference_delta.py` and
      `heuristics/intensity_reference_delta.py` read `lower_pct` and
      `upper_pct`.

    Each also declares its paths as strings in `consumed_paths` and its mode
    declarations.
  - **Serialisers:**
    - `feature_report.py`: `relationships_to_dict`, `overlap_to_dict`,
      `curvature_to_dict`, `spacing_consistency_to_dict`,
      `monotonic_consistency_to_dict`, `build_features_block` (with its
      `features_version` promotion), and `build_image_features_block`'s
      case-level keys;
    - `reference/delta.py`: `reference_delta_to_dict`'s case-level keys.
  - **Other readers:**
    - `human_report.py`'s `render_feature_table` (overlaps, relationships,
      `features_version`, `image_features.available`);
    - `eval/per_mode.py` (`compute_per_mode_metrics`, which reads
      relationships and overlaps);
    - `reference/delta.py` (`image_features.get("available")`);
    - `catalogue.py` (`iter_driver_records`' overlaps record, and
      `normalise_leaf_path`);
    - `pipeline.py`, which attaches `image_features` and `reference_delta` to
      the transient rule record, and computes both spacing arrays.
  - **Path strings and docs:**
    - `feature_docs.py` and `failure_modes.py`;
    - `report_schema_v0.json`;
    - the `default_config.yaml` comment;
    - the docstrings of `synth/coverage_border_overlap.py`,
      `synth/clean_gt.py` and `heuristics/rule.py`.

  `synth/regression.py`, `eval/harness.py` and `cli.py` read no 216 path.
- **A9 (measured): which tests read either spacing array on a degenerate
  record.**
  - `test_016_features_json.py::test_ac7_single_label_map` (line 444) asserts
    the relationships array is `[]` on a single-label map. D10 keeps that
    value at the survivor's path.
  - `test_099_per_mode_metrics.py` (line 221) hand-builds `[]`.
  - No listed test reads either array on a coincident-centroid record:
    `test_129`, `test_130` and `test_135` assert only `stage3_unavailable`
    and Stage 3 absence.
  - `test_022_stage3_serialisation.py` calls `build_features_block` directly
    with a `SpineRelationships` and a `SpacingConsistency` built from
    all-recognised synthetic centroids.
- **A10 (measured): what committed data pins this item's values.**
  - No committed corpus file stores a record path or a spacing value: both
    manifests' and `094_pre_migration_snapshot.json`'s `spacing` keys are
    voxel spacing, and `golden_evidence.generated.json` names no 216 path.
  - No test pins a `sequence_break` spacing value or a spacing observed
    range. Searches for 134.16, 36.84, 34.22, 33.49, 66.37 and 32.69 found
    none.
  - Count pins this item moves again after item 215:
    - catalogue totals in `test_124`, `test_131`, `test_132`, `test_136`,
      `test_137` and `test_148`;
    - one record's leaf-path count of 101 in `test_103` (line 389);
    - `test_136`'s empty-evidence bucket of 89 (line 867);
    - `test_137`'s exhaustive `mode_evidence` distribution.
  - The catalogue path-set digest in `tests/corpus/119_pre_119_digests.json`
    is asserted by `test_119_curve_formulation.py`,
    `test_120_leave_one_out_offset.py` and `test_123`.
- **A11 (measured): `stage3_unavailable` has no row.**
  - The features block carries it only when two centroids coincide (item
    129), and the catalogue lists no path under it.
  - It is a pipeline diagnostic, not a feature, so the table cannot move it.
  - It keeps its name and shape (Left open), and AC2's clean-control report
    does not carry it.
- **A12 (default): `fused_label` still judges only records with Stage 3.**
  - Before this item the rule returned `[]` when `stage3.spacing_consistency`
    was absent, which is every record with fewer than two labels or
    coincident centroids.
  - Under D10 the survivor exists on such records, so reading the survivor
    alone would start judging coincident-centroid records. That is a
    behaviour change D1 does not name.
  - So the rule keeps its gate on the Stage-3-only spacing statistics being
    present, read at their new path (step 5, and the
    `stage3-unavailable-not-judged` case).
- **A13: no human gate beyond gate-0080, and no environment-gated
  capability.** The case-level `radiomics_available` and `backend` rows move
  like any other row.

## Implementation Steps

0. **At claim (spec-author, before any test is written).** Items 214 and 215
   have merged, and gate-0080 reads `✅ Approved`.
   - Re-check A1–A4 against `read_mapping()`, the note's `## Structure` and
     `## Answers`, and the post-215 tree. Append a dated re-check to each.
   - If 216's rows differ from A2, stop: that is the gate's re-cut.
   - Record Answer 6's two settlements (A3) in Decisions. If Answer 6
     re-derives the per-element neighbourhood copy, amend the spec with that
     value change and the one criterion it needs before any test is written.
   - Re-run the fence greps (Authorised paths) on the post-215 tree. Drop
     listed files whose only hit was a 215 row, and add any new hit. Also
     grep the record key behind any new placeholder segment the note
     defines.
1. **The survivor is computed with `relationships`, outside the Stage 3
   branch** (`pipeline.extract_feature_record`; D4, D9, D10).
   - **The ordering.** Build the item-198 anatomical sequence of every label
     once, right after the centroids, for every record with at least one
     label. Use the one shared ordering function (D7) that this step lifts
     out of the Stage 3 branch into `segfacet.labels`. The Stage 3 branch
     then reuses this sequence for monotonic consistency, as it does today.
   - **The survivor array.** Take the Euclidean distances between
     consecutive centroids of that sequence. It is `[]` for a single label,
     and has a 0.0 entry where two centroids coincide. Write it into the
     relationships object with
     `dataclasses.replace(relationships, neighbour_spacings_mm=survivor)`.
     So it travels exactly where `relationships` travels today: present for
     at least one label, absent (`relationships` is `None`) for none.
     - `compute_spine_relationships` and its dataclass are unchanged.
     - `compute_spacing_consistency` is never called for this. It raises
       below two centroids (A7).
   - **The statistics stay Stage-3-only.** Inside the existing
     two-or-more-labels, non-coincident branch, call the unchanged
     `compute_spacing_consistency` on the same anatomical sequence instead of
     `ordered_centroids`. Its `mean_spacing_mm`, `cv_spacing`, `deviations_mm`
     and `outlier_pairs` are then derived from the survivor's sequence. The
     branch's two-centroid guarantee is what keeps the extractor from ever
     receiving fewer.
   - **Serialisation.** The survivor is emitted once, at its new path, from
     `relationships.neighbour_spacings_mm`, whichever of the two rows the
     table makes the survivor. `spacing_consistency_to_dict` stops emitting
     `spacings_mm`. If `relationships.neighbour_spacings_mm` is the merged
     row, `relationships_to_dict` stops emitting it at the old path.
     `build_features_block`'s parameters are unchanged.
2. **Serialisers emit the new paths** for every `kept`/`moved` 216 row:
   - `feature_report.py`: the relationships, overlaps, curvature, spacing,
     monotonic and case-level image-features keys, and `features_version`;
   - `reference/delta.py`: `reference_delta_to_dict`'s case-level keys.

   **The promotion rule stays.** `features_version` is promoted when the
   Stage 3 objects are present, not when a `stage3` key exists. Each `merged`
   pair-identity copy (item 214's Answer 1, if any) is no longer emitted.

   **New placeholders.** If a new path uses a placeholder segment the note
   defines (for example a neighbour pair), extend
   `catalogue.normalise_leaf_path` to produce it, and update
   `iter_driver_records`' overlaps record. Leave item 215's extended
   reference-delta driver as it is.
3. **`pipeline.py` and `report.py` move a block, but only if a 216 row moves
   a field from one report block to another.** For example, the case-level
   image-features or reference-delta keys might move into the features
   block.
   - `run_qc`, `run_qc_with_reference` and `run_qc_with_intensity` keep their
     return arity and order. So `synth/regression.py`, `eval/harness.py` and
     `cli.py` need no edit.
   - The transient rule record gets each moved field where the rules now read
     it.
4. **Readers follow the table.** Re-point each reader A8 lists:
   - its read site, `consumed_paths` and mode-declaration path strings;
   - `human_report.render_feature_table`'s overlaps, relationships, version
     and availability reads;
   - `eval/per_mode.py`;
   - `feature_docs.py`'s `FEATURE_DOCS` keys, owner prefixes, steering rows
     and `STATUS_OVERRIDES`. A moved row keeps its documentation and its
     catalogue `status`. The merged spacing row's documentation, status and
     consumers are folded into the survivor's;
   - `failure_modes.py`'s path strings, for 216's rows only.

   **A reader of a merged path reads the survivor.** Every absence-tolerant
   `.get(…)` / `isinstance` guard keeps its tolerance, on the new path: an
   un-pointed guard is the silent failure this step exists to prevent. Each
   docstring, comment and declaration string in a file this item already
   edits is updated where it names a moved path, except dated history
   prose.
5. **`fused_label` pairs each spacing with anatomically adjacent labels**
   (D1, D7, D9, A12).
   - Judge only when the Stage-3-only spacing statistics are present at their
     new path (A12). Then read the survivor.
   - Order the `per_label` keys with the shared item-198 function over every
     label. Pair `spacings[i]` with the i-th and (i+1)-th label of that
     sequence. The size neighbours `i - 1` and `i + 1` follow the same
     sequence, never integer adjacency.
   - The count check compares `len(spacings)` with `len(sequence) - 1`.
     Under D9 the sequence is every label, so a survivor that dropped an
     unrecognised label is skipped visibly rather than mis-paired. The
     `unknown-label-still-judged` case guards that this never happens on a
     real record.
   - Every other absence tolerance stays as items 207 and 211 built it:
     - an absent or non-numeric survivor is not judged;
     - a non-integer or `None` `per_label` key is not judged;
     - a label lacking a numeric volume is not judged;
     - sacral and coccygeal levels are skipped.
   - Update the module docstring's ordering paragraph (item 211's A1 and A2)
     and the `consumed_paths` / `signal_paths`.
6. **The report schema** (`src/segfacet/report_schema_v0.json`).
   - Place every moved 216 property where its new path says.
   - **Keep the `definitions` keys** (D6). The `merged` key leaves its
     definition. The survivor's description names the anatomical order, the
     every-label set with unrecognised labels last, and its availability.
   - **The rider (AC6).** Rewrite the four `monotonic_consistency`
     descriptions (lines 479, 623, 627 and 640 at `f5c79df`):
     - `u` is the per-centroid normalised arc length in [0, 1] along the
       label-free MST longest path through the centroids (item 210);
     - `is_monotonic` is true iff `u` increases at every consecutive pair in
       anatomical order.

     This is description text only.
   - **Leave lines 497 and 522 as they are.** Those are `closest_u` in
     `stage3OffsetEntry` and `spline_closest_u` in `stage3OrientationEntry`.
     They are item 215's rows, and correct: each is the parameter of the
     closest point on the fitted spline.
   - `report.build_report` validates every report against this schema, so a
     stale definition fails loudly.
7. **Version discriminators (D5).**
   - Bump none that item 215 bumped. Read the post-215 values at step 0.
   - **The base `FEATURES_VERSION`** is the discriminator for a block without
     Stage 3. Bump it `"0.1"` → `"0.2"` unless item 215's step 0 recorded
     that 215 bumped it. This item reshapes `relationships` and `overlaps`,
     which every block carries, so if 215 did not reach a no-Stage-3 block,
     the bump is this item's.
   - Bump `IMAGE_FEATURES_VERSION` or `REFERENCE_DELTA_VERSION` (`"1.0"` →
     `"1.1"`) only if item 215 left it at `"1.0"` and this item reshapes its
     block.
   - The top-level `schema_version` stays `"0.1"`.
8. **Regenerate, in item 215's step-6 order.** Run each generator twice into
   a scratch directory first and compare the two runs byte for byte. Use
   `.venv/bin/python`. The generators:
   - `python -m segfacet.catalogue --json <tmp>/c.json --md <tmp>/c.md`;
   - `python -m segfacet.failure_modes --json … --md …`;
   - `python -m segfacet.traceability --json … --md …`;
   - `python -m segfacet.rule_table --md …`.

   Then:
   - Run each generator with its default outputs.
   - Edit `tests/report_format_fixture.py`'s hand-written record to the new
     shape. Regenerate `tests/golden/report_format_contract.json` with
     `.venv/bin/python -m tests.report_format_fixture`, never from a test.
   - **Rewrite `tests/corpus/119_pre_119_digests.json`** from the
     regenerated catalogue, exactly as item 215's step 6 states it: the
     sorted path list joined with `"\n"`, hashed with sha256 over its UTF-8
     bytes, and written with `write_bytes` in the file's present layout.
   - Every one of these files is already LF-pinned in `.gitattributes`, so
     no pin is added.
   - `docs/aide/golden_evidence.generated.json` is predicted byte-identical,
     and a difference is a hand-back.
9. **Reconcile the existing tests** under the fence below, after
   regeneration. Record every edited test in Decisions by node id, old →
   new.
10. **Run `python .aide/scripts/aide.py scope 216 --base aide/queue-029`** and
    confirm it exits 0.

No dependency is added.

## Authorised paths

**How the list was produced (2026-10-05, `f5c79df`), so step 0 can re-run
it.** It was derived by grep, not by a failing-test probe. A probe lists each
red test once, at its first failing assert, and a tree copy without `.git`
reports git-gated tests as passing because they skip (insights
`2026-10-05-da43`, `2026-10-05-dc87`).

Six searches were run over `tests/` (`*.py`, `*.json`, excluding
`tests/corpus/`) and `src/segfacet/`. Here `Q` is `["']`:

1. `Q(relationships|overlaps)Q|Q(relationships\.|overlaps\[)`
2. `Q(stage3\.)?(curvature|spacing_consistency|monotonic_consistency|stage3_unavailable)["'.\[]`
   `|(mean_spacing_mm|cv_spacing|deviations_mm|outlier_pairs|spacings_mm|non_monotonic_pairs|u_values|is_monotonic|tangent_angles_deg|total_curvature_deg|curvature_plane|coronal_curvature_deg|sagittal_curvature_deg)Q`
3. `Qstage3Q (not )?in|get\(Qstage3Q\)|\[Qstage3Q\]|Qstage3Q: *\{`
4. `image_features\.(available|backend|radiomics_available|image_features_version)`
   `|Q(radiomics_available|image_features_version|lower_pct|upper_pct|reference_delta_version|reference_schema_version|reference_source|stratum)Q`
   `|reference_delta\.(lower_pct|…|stratum)|IMAGE_FEATURES_VERSION|REFERENCE_DELTA_VERSION`
5. `features_version|FEATURES_VERSION`
6. `len\((cat\.)?entries\) == 145|leaf_count == 145|len\(paths\) == 145|_PRE_ITEM_TOTAL_LEAF_PATH_COUNT = 145|sum\(distribution\.values\(\)\) == 145`

**The value sweep, kept separate.** Spacing values and `fused_label` firing
change by decision rather than by re-pointing, so they were swept separately
with `fused_label|FusedLabelRule|spacing_ratio|neighbour_spacings_mm|spacings_mm|mean_spacing_mm|cv_spacing|outlier_pairs|deviations_mm`,
and with the `sequence_break` values in A10. Its hits pin firing on committed
cases, which D8 keeps unchanged: test_040 (fuse_adjacent fires on 22),
test_176, test_166, test_167, test_187, test_151, and test_207's AC1
(fused_label fires exactly on fuse_adjacent 22 and fuse_separate 22 across
both corpora). Those must pass **unedited**. Of the sweep's hits, only
test_211 re-points a path, and it is listed. Generated docs were searched
for 216 path tokens, and the hits are the seven `docs/aide/*.generated.*`
files below.

**A hit was dropped for one of four reasons.** First, it was an
extractor-dataclass field test, and the dataclasses are unchanged (D4):
test_014, test_019, test_020, test_042's tolerance helper, test_092's config
kwargs, test_features_radiomics, and test_aide_status_report's unrelated
stratum key. Second, every stage3 access in it names a 215 row (step 0
confirms): test_044, test_051, test_081, test_121, test_145, test_189 and
test_212. Third, it was a comment or docstring only: test_106, test_073,
test_174 and test_116. Fourth, it was a dated history or signed design
document: the item specs under docs/aide/items, the spinal-curve model note,
the golden decision table, and the item-192 measurement string in
heuristics/sequence.py.

**May change:**

- `src/segfacet/pipeline.py` — the survivor and anatomical sequence outside the Stage 3 branch, the statistics' sequence (step 1), and moved-field attachment (step 3).
- `src/segfacet/labels.py` — the shared item-198 ordering function (step 1, D7).
- `src/segfacet/feature_report.py` — the 216 serialisers, the `features_version` promotion and the base `FEATURES_VERSION` (steps 1, 2, 7).
- `src/segfacet/reference/delta.py` — `reference_delta_to_dict`'s case-level keys and the `image_features` availability read (steps 2, 4).
- `src/segfacet/report.py` — only if a 216 row moves a field between report blocks (step 3).
- `src/segfacet/catalogue.py` — `normalise_leaf_path` and the overlaps driver record (step 2).
- `src/segfacet/heuristics/fused_label.py` — Stage-3 gate, survivor read, anatomical pairing, count check (step 5).
- `src/segfacet/heuristics/mislabel.py` — monotonic-consistency reader and declared paths (step 4).
- `src/segfacet/heuristics/coverage.py` — relationships reader and declared paths (step 4).
- `src/segfacet/heuristics/border.py` — declared relationships path (step 4).
- `src/segfacet/heuristics/fov.py` — `derive_fov_coverage`'s relationships read (step 4).
- `src/segfacet/heuristics/overlap.py` — overlaps reader and declared paths (step 4).
- `src/segfacet/heuristics/intensity.py` — the case-level availability read and declared path (step 4).
- `src/segfacet/heuristics/reference_delta.py` — `lower_pct`/`upper_pct` read and declared paths (step 4).
- `src/segfacet/heuristics/intensity_reference_delta.py` — `lower_pct`/`upper_pct` read and declared paths (step 4).
- `src/segfacet/heuristics/rule.py` — the `evaluate` docstring naming the record's top-level keys (step 4).
- `src/segfacet/human_report.py` — `render_feature_table`'s overlaps, relationships, version and availability reads (step 4).
- `src/segfacet/eval/per_mode.py` — `compute_per_mode_metrics`' relationships and overlaps reads (step 4).
- `src/segfacet/feature_docs.py` — doc rows, owner prefixes, steering rows and status overrides of 216's rows (step 4).
- `src/segfacet/failure_modes.py` — signal and candidate path strings of 216's rows (step 4).
- `src/segfacet/report_schema_v0.json` — moved properties, survivor description, the rider (step 6).
- `src/segfacet/default_config.yaml` — the `fused_label` comment naming the spacing path (step 4).
- `src/segfacet/synth/coverage_border_overlap.py` — docstring naming the spacing and relationships paths (step 4).
- `src/segfacet/synth/clean_gt.py` — docstring naming `relationships.missing_levels` (step 4).
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 8).
- `docs/aide/feature_catalogue.generated.md` — regenerated (step 8).
- `docs/aide/failure_modes.generated.json` — regenerated (step 8).
- `docs/aide/failure_modes.generated.md` — regenerated (step 8).
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 8).
- `docs/aide/traceability_matrix.generated.md` — regenerated (step 8).
- `docs/aide/rules.generated.md` — regenerated (step 8).
- `tests/report_format_fixture.py` — the hand-written record's new shape (step 8).
- `tests/golden/report_format_contract.json` — regenerated from the fixture (step 8).
- `tests/corpus/119_pre_119_digests.json` — the catalogue path-set digest, regenerated (step 8, fence rule 4).
- `tests/test_216_neighbour_pair_and_case_level_migration.py` — **new**, this item's test module.
- `tests/test_016_features_json.py` — fence rule 1: relationships, overlaps, version (searches 1, 2, 5).
- `tests/test_022_stage3_serialisation.py` — fence rule 1: stage3 case-level shape and presence (searches 1–3, 5).
- `tests/test_026_rule_engine_core.py` — fence rule 1: hand-built relationships/overlaps (search 1).
- `tests/test_027_level_aware_bounds.py` — fence rule 1 (search 1).
- `tests/test_028_fragmentation_island.py` — fence rule 1 (search 1).
- `tests/test_029_coverage_missing_levels.py` — fence rule 1 (search 1).
- `tests/test_030_sequence_continuity.py` — fence rule 1 (search 1).
- `tests/test_031_border_partial_vertebra.py` — fence rule 1 (search 1).
- `tests/test_032_overlap.py` — fence rule 1 (search 1).
- `tests/test_033_mislabel.py` — fence rule 1: hand-built monotonic records (searches 1–3).
- `tests/test_035_default_config.py` — fence rule 1 (search 1).
- `tests/test_035_failure_modes.py` — fence rule 1 (searches 1–3).
- `tests/test_035_pipeline.py` — fence rules 1, 3: container presence and version (searches 1, 3, 5).
- `tests/test_038_coverage_border_overlap_perturbations.py` — fence rule 1 (search 1).
- `tests/test_039_identity_ordering_alignment_perturbations.py` — fence rule 1: monotonic record edits (searches 2, 3).
- `tests/test_046_reference_delta.py` — fence rule 1: case-level delta keys (search 4).
- `tests/test_047_reference_delta_rule.py` — fence rule 1: hand-built `lower_pct`/`upper_pct` (search 4).
- `tests/test_049_reference_integration.py` — fence rule 1 (search 4).
- `tests/test_061_image_features_fusion.py` — fence rules 1, 3 (searches 1, 4, 5).
- `tests/test_062_intensity_rule.py` — fence rule 1: hand-built availability flag (search 4).
- `tests/test_064_intensity_reference_delta_rule.py` — fence rule 1 (search 4).
- `tests/test_065_intensity_pipeline.py` — fence rule 1 (search 4).
- `tests/test_089_fov_aware_coverage_border.py` — fence rule 1 (search 1).
- `tests/test_090_reference_derived_defaults.py` — fence rule 1 (searches 1, 4).
- `tests/test_098_stray_components.py` — fence rule 1 (search 1).
- `tests/test_099_per_mode_metrics.py` — fence rule 1 (searches 1–3).
- `tests/test_103_feature_catalogue.py` — fence rules 1, 2: includes one record's leaf-path count (searches 1, 3–5).
- `tests/test_104_feature_catalogue_drift.py` — fence rule 1: path literals in its own cases; the drift assertions stay (searches 1, 5).
- `tests/test_110_neighbourhood_wiring.py` — fence rule 1: `"stage3"` presence assertions (search 3).
- `tests/test_115_stage26_validation.py` — fence rule 1: `"stage3"` presence assertion (search 3).
- `tests/test_119_curve_formulation.py` — fence rule 1: a curvature `FEATURE_DOCS` key (search 2).
- `tests/test_120_leave_one_out_offset.py` — fence rule 1: hand-built monotonic record (searches 2, 3).
- `tests/test_122_signed_curvature.py` — fence rule 1 (searches 2, 3).
- `tests/test_123_recalibrate_and_regenerate.py` — fence rule 1 (searches 2, 3).
- `tests/test_124_observed_range.py` — fence rules 1, 2: the path count; AC2/AC3 assertions unedited (searches 1, 2, 6).
- `tests/test_125_stage28_validation.py` — fence rule 1 (searches 2, 3).
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — fence rules 1, 3 (searches 1–3, 5).
- `tests/test_130_one_closest_point_search.py` — fence rule 1 (searches 2, 3).
- `tests/test_131_tangent_direction_normalisation.py` — fence rules 1, 2 (searches 2, 3, 6).
- `tests/test_132_monotonicity_against_traversal_order.py` — fence rules 1, 2 (searches 2, 3, 6).
- `tests/test_135_stage29_validation.py` — fence rule 1 (searches 2, 3).
- `tests/test_136_rule_mode_declarations.py` — fence rule 2: entry count and the empty-evidence bucket (search 6).
- `tests/test_137_mode_less_rule_disposition.py` — fence rule 2: entry count and the exhaustive evidence distribution (searches 4, 6).
- `tests/test_138_traceability_matrix.py` — fence rule 1 (search 1).
- `tests/test_143_s_axis_correction.py` — fence rule 1 (searches 2, 3).
- `tests/test_146_ninth_mode_and_first_proposed.py` — fence rule 1 (searches 2, 3, 5).
- `tests/test_147_specification_is_the_record.py` — fence rule 1 (search 1).
- `tests/test_148_per_path_mode_attribution.py` — fence rules 1, 2: the entry count (searches 1, 4, 6).
- `tests/test_149_conformance_report.py` — fence rule 1 (searches 1, 4).
- `tests/test_151_stage30_validation.py` — fence rule 1 (searches 1, 3).
- `tests/test_167_mode_3_detector.py` — fence rule 1 (search 1).
- `tests/test_186_expected_level_sequence.py` — fence rule 1 (search 1).
- `tests/test_187_neighbour_contact_rule.py` — fence rule 1 (search 1).
- `tests/test_192_sequence_sub_types.py` — fence rule 1 (search 1).
- `tests/test_198_ordering_along_expected_sequence.py` — fence rule 1 (searches 2, 3).
- `tests/test_211_fused_label_spacing_pair.py` — fence rule 1: the spacing path in `_with_pair` and its reads (searches 2, 3).
- `tests/test_heuristics_bounds_source.py` — fence rule 1 (search 1).

**The reconciliation fence** applies to the listed test files other than
this item's own module. The builder reconciles after regeneration. Five kinds
of edit are allowed, numbered 1 to 5.

1. A re-pointed path. A path string, key access, presence assertion, or
   hand-built input record that names the old path or container of a 216 row
   is rewritten to that row's new path or container. For a merged path, the
   hand-built copy is removed, and a read of it reads the survivor. A
   stage3-not-in-block assertion for a degenerate map is re-pointed to the
   container that now carries the Stage-3-only fields, not left vacuously
   true. The asserted value is unchanged.

2. A moved count. A count literal moves to its live value. This covers any
   count: catalogue paths overall or under a prefix, catalogue paths
   attributed to a mode or rule or held in one evidence bucket (an
   exhaustive bucket distribution included), and one record's leaf paths.
   The dated item-216 comment beside the edited literal accounts for the
   change row by row, and the arithmetic must close. It counts four kinds of
   row: each merged row that leaves the count's scope (minus one); each row
   moved into or out of the scope (plus or minus one, such as a field moved
   across report blocks); each row newly catalogued inside the scope (plus
   one); and each survivor that changed evidence bucket. The fourth kind
   happens here if the relationships spacing array survives. It has no
   evidence today and gains the fused_label consumer, so item 136's
   empty-evidence bucket and item 137's exhaustive distribution move,
   although the merged row was never in the empty bucket. A change the
   comment cannot attribute to a row of the table is not reconciled: it is a
   hand-back.

3. A bumped version literal. A pinned value of a discriminator step 7 bumps
   moves to the bumped value.

4. The path-set digest file is regenerated by step 8. It is never
   hand-edited, and the tests that read it are not edited for it.

5. A value changed by decision (D1). A test pinning a value of the spacing
   family, or the fused_label pairing, on an input where the integer and
   anatomical orders disagree, or one carrying an unrecognised label, moves
   to the re-measured value. The edit gains a dated item-216 comment citing
   D1. A10 found no such test at f5c79df, so any use of this rule is
   recorded in Decisions with its node id.

**Nothing else is allowed.** No other measured expected value changes: no
firing set, rendered human-report row, or finding reason. No test is
skipped, marked expected-to-fail, loosened in tolerance, renamed or retired.
Item 214's and item 215's test modules stay off May change. A red test in a
file not listed here is a hand-back to spec-author, not an edit. **Re-run
each listed test after editing it, until it is green.** A test can hold a
second stale path behind its first failing assert (insight 2026-10-05-da43).

**Asserts against:**

- `docs/feature-taxonomy.md` — AC1–AC5 read the mapping table through item 214's reader.
- `tests/feature_taxonomy_mapping.py` — the reader module (A1), imported, never edited.
- `tests/corpus/manifest.json` — resolves every case's fixtures; must stay unedited so firing cannot be re-expected (D8).
- `tests/corpus/fixtures/sequence_break_seg.nii.gz` — AC3 and AC4's segmentation.
- `tests/corpus/fixtures/fuse_adjacent_seg.nii.gz` — the source segmentation for AC5 and both adversarial cases.
- `tests/corpus/fixtures/clean_control_seg.nii.gz` — AC2's segmentation.
- `tests/corpus/fixtures/base_scan.nii.gz` — every case's scan.
- `src/segfacet/reference/reference_verse_v1.json` — the default reference behind AC2's report; not rebuilt.

**Kept off May change on purpose**, so that `aide scope` refuses an edit to
any of them. No extractor needs an edit (D4): every module under features/,
including relationships.py and consistency.py. Step 3 keeps the pipeline's
tuples, so cli.py, synth/regression.py and eval/harness.py stay off. The
traceability and rule-table generators, observed_range.py and
heuristics/sequence.py read no 216 path. Firing cannot be re-expected: both
corpus manifests stay off, and the specificity-ratchet and item-207
fused_label tests must pass unedited. Item 214's and item 215's test modules
stay off, so their guarantees hold unedited.

## Testing Strategy

**The new module is `tests/test_216_neighbour_pair_and_case_level_migration.py`**,
with one test per AC.

- **The table** is read only through
  `from feature_taxonomy_mapping import read_mapping` (A1).
- **The reports** are built by two module-scoped fixtures that call
  `segfacet.cli.main` in-process into `tmp_path_factory` directories. They
  are read with `json.loads(...read_text(encoding="utf-8"))`. AC2 uses the
  clean-control report, and AC3 and AC4 use the sequence-break report.
- **One small resolver**, written in the module, walks a catalogue-notation
  path through a report as the AC terms define it. AC3 and AC4 never hard-code
  a new path: each comes from `new(...)` over the table.
- **AC5 and the two adversarial cases** build their records in memory from
  `segfacet.synth.regression.loaded_seg_image(case)`. They set the label's
  voxels with NumPy, rebuild the image as `nib.Nifti1Image(data, affine,
  dtype=data.dtype)`, and run `segfacet.pipeline.run_qc` or
  `extract_feature_record` with `bundled_default_config()`. Nothing is
  written to disk.
- **The anatomical key** is computed in the test from
  `segfacet.labels.CANONICAL_ORDER` as the AC terms define it. The test never
  imports the shared function step 1 adds, so it cannot agree with the code
  by construction.
- **Each AC asserts its recognisability first**, as listed under the
  criteria.

**Adversarial cases, exactly two.** The test-writer writes these and no
others.

- **`unknown-label-still-judged`.** For the unknown-label variant, the
  `fused_label` findings of `run_qc` have label sets equal to
  `[frozenset({22})]` (A6).

  It guards a survivor built from `relationships`' existing recognised-only
  array, against D9. Such a survivor drops label 99, and `fused_label`'s
  count check then skips every case carrying an unrecognised label with no
  error. The specificity ratchet would stay green, because no committed case
  carries one (A5).
- **`stage3-unavailable-not-judged`.** Take the `extract_feature_record`
  record of the unmodified `fuse_adjacent` case. Assert first that
  `FusedLabelRule().evaluate` fires on {22}. Then delete, in a deep copy, the
  container holding the Stage-3-only spacing statistics. The container is the
  one holding `new("stage3.spacing_consistency.mean_spacing_mm")`. The
  survivor is left in place, and `evaluate` must return `[]`.

  It guards A12. Under D10 the survivor now exists on coincident-centroid
  records, where Stage 3 is unavailable. A rule that judged on the survivor
  alone would start firing on records it never judged before, a behaviour
  change D1 does not authorise.

**What else carries the queue's *Testable* claims, and item 215's
guarantees:**

- "The catalogue and its drift test agree" is
  `tests/test_104_feature_catalogue_drift.py`, as reconciled.
- "Every corpus case's measured firing equals its expected set" is
  `tests/test_163_specificity_ratchet.py::test_ac2_ratchet_measured_equals_expected`,
  unedited and over unedited manifests.
- That `fused_label` fires exactly on `fuse_adjacent` 22 and `fuse_separate`
  22 is `tests/test_207_fused_label_rule.py::test_ac1_fused_label_fires_on_the_two_fused_labels_and_nowhere_else`,
  unedited.
- That the survivor is `[]` on a single-label map (D10) is
  `tests/test_016_features_json.py::test_ac7_single_label_map`, re-pointed
  only.
- Identity stored once, and 215's moved paths still produced, are
  `tests/test_215_per_label_migration.py`, unedited.
- Every reference feature still resolving to one catalogue path is
  `tests/test_124_observed_range.py`'s AC2 and AC3, with their assertions
  unedited.
- Report-schema conformance is `report.build_report`'s own
  `jsonschema.validate`, run on every report any test writes.

**Existing tests to reconcile:** the files under the fence in Authorised
paths, found by the recorded greps. That list is a floor, not a guarantee. A
grep finds a file that names a moved path. It does not find a test that
breaks because a value was read from an un-pointed guard. The full suite run
and the Validation section close that gap.

## Validation  <!-- OPTIONAL: how to OBSERVE this working, beyond the tests -->

No `[validation]` profile is needed. The validator runs:

1. `python .aide/scripts/aide.py scope 216 --base aide/queue-029`, which must
   exit 0.
2. **Byte-identical regeneration.** Run each step-8 generator twice into
   scratch and compare the bytes. Then diff scratch against the committed
   files. There must be no difference.
3. **No unauthorised value changed, row by row.** Read the base catalogue
   with `git show <claim base>:docs/aide/feature_catalogue.generated.json`.
   For every 216 row whose change is `kept` or `moved`, compare the base entry
   at the old path with the branch entry at the new path. Their `status`,
   their evidence (`consuming_rules`, `mode_evidence`) and their
   observed-range values must be equal.
   - **The spacing family is the exception.** That is the survivor, the four
     statistics, and the merged spacing row.
   - The survivor's `status`, documentation and evidence may take the merged
     row's, under step 4's fold. Its observed range and the statistics'
     ranges may differ only by the `sequence_break` values A5 lists.
   - A `merged` row has no branch entry.
4. **No version discriminator re-bumped (D5).** Run
   `git diff <claim base> -- src/segfacet/feature_report.py src/segfacet/reference/delta.py`.
   It must show no change to a `*_VERSION*` constant item 215 already moved,
   and at most the one base `FEATURES_VERSION` bump step 7 allows.
5. **Reports do not move where values did not.** Run
   `.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg <seg> --intensity --out <tmp>`
   for `<seg>` in `clean_control_seg.nii.gz` and `sequence_break_seg.nii.gz`.
   Run it once on the claim base and once on the branch. The base run comes
   from a separate clone with its own venv (CLAUDE.md "Gotchas").
   - Each `segfacet_report.txt` must be byte-identical across the two runs.
     It renders the verdict and every finding reason, so this checks that
     firing and reasons did not move. It does not render the feature table.
   - Also call `segfacet.human_report.render_feature_table` on each run's
     JSON features block, with its `image_features`. The output must be
     identical across the two runs. The neighbour-spacings line holds
     `relationships`' anatomical array on the base, which equals the
     survivor on both cases (A5).
6. `python .aide/scripts/aide.py check`, which must report no errors.

## Dependencies

- **Item 214** — the signed design note `docs/feature-taxonomy.md`, its
  mapping table, and the reader `tests/feature_taxonomy_mapping.py` (A1–A3).
  Its gate also holds this item: gate-0080 — `Blocks: items 215, 216, 217`.
- **Item 215** — the per-label migration this item builds on (A4).

**Downstream:** item 217 attests from this item:

- Stage 27 criterion 2's addressability half, from AC1 together with item
  215's AC1;
- criterion 3, from the specificity ratchet together with D1. D1 is the
  explicitly authorised measured change, whose corpus footprint is
  `sequence_break`'s Stage 3 spacing values only, with no firing change
  (A5, D8), and whose rule-level effect AC5 shows.

Item 217 also replays Validation steps 2 and 5 from a clean clone.

## Decisions & Trade-offs

To be updated during implementation.

- **D1 (maintainer decision, 2026-10-05): the two stored adjacent-pair spacing
  arrays collapse into one, in anatomical order.** The maintainer's reason,
  verbatim: *"the integer-label order is anatomically meaningless"*.
  - The survivor, the four derived statistics, and `fused_label`'s pairing
    change wherever the integer and anatomical orders disagreed, or where an
    unrecognised label was present.
  - This is the one authorised exception to Stage 27 criterion 3 in this
    stage, and item 217 attests it as such.
- **D2 (maintainer decision, 2026-10-05): no field is dropped in this
  stage.** The `retire`-status paths among 216's rows keep their rows:
  `image_features_version`, `reference_delta_version` and
  `reference_schema_version`.
- **D3 (maintainer decision, 2026-10-05): identity is stored once (item
  215).** This item keeps item 215's AC1–AC3 and its adversarial case true,
  unedited. No new leaf is named bare `label` or `level_name`.
- **D4: no extractor or result type changes.**
  - The survivor is assembled in the pipeline from the existing centroids.
    It is written into the existing `SpineRelationships` value with
    `dataclasses.replace`, so it travels where `relationships` travels. The
    statistics come from the unchanged `compute_spacing_consistency`, called
    on the anatomical sequence inside the existing Stage 3 branch.
  - Neither `compute_spine_relationships` nor `compute_spacing_consistency`
    changes, and `build_features_block` keeps its parameters. Tests that
    call those functions directly keep working, and need only fence rule 1.
- **D5 (batch rule): version discriminators, once per stage.**
  - This item re-bumps nothing item 215 bumped.
  - The base `FEATURES_VERSION` (`"0.1"`, for a block without Stage 3) goes
    to whichever item first changes a no-Stage-3 block's shape, once. Item
    215 bumps it only if the table moves an `image_features` or
    `reference_delta` per-label field into `per_label.{label}`. Otherwise
    this item owns it, because it reshapes `relationships` and `overlaps`,
    which every block carries.
  - The top-level `schema_version` stays `"0.1"`.
- **D6: the schema's `definitions` keys are not renamed.** They are internal
  `$ref` names, not record paths, and tests address them (`test_121`,
  `test_122`). AC6 names `stage3MonotonicConsistency` for the same reason.
- **D7: one ordering function, shared by the producer and the reader.** The
  survivor's order and `fused_label`'s label sequence must agree by
  construction. So the item-198 key moves into `segfacet.labels` once,
  rather than being written twice.
- **D8 (maintainer decision, 2026-10-05): no rule's firing changes on either
  committed corpus.** It is measured unchanged in A5. If the build shows any
  corpus firing change, the builder stops and hands back. The builder does
  not re-expect a manifest, edit `failure_modes.py`'s expected firing, or
  change the ratchet's inputs.
- **D9 (maintainer decision, 2026-10-05): the survivor covers every label.**
  It is stored in anatomical order, with unrecognised labels kept and placed
  last, which is the item-198 ordering.
- **D10 (maintainer decision, 2026-10-05): the survivor is available as
  `relationships.neighbour_spacings_mm` is today.**
  - It is present on every record with at least one label, and `[]` below
    two labels.
  - On a coincident-centroid record it is computed as `relationships`
    computes it today.
  - Only the four derived statistics stay Stage-3-only.
  - The aim is that no existing test's asserted value or presence changes
    outside the authorised collapse.
- **Left open:** whether the per-element spacing copy behind
  `stage3.per_label_neighbourhood[].stats.spacing_mm.*` is re-derived from
  the survivor. Item 214's Answer 6 decides it. Step 0 amends this spec if it
  is, because that value change lands here even though item 215 moves the
  paths.
- **Left open:** `stage3_unavailable` keeps its name even once no `stage3`
  container remains (maintainer, 2026-10-05). It has no catalogue row (A11),
  so the table cannot move it, and renaming it would change the report
  schema and item 129's tests for no feature reader.
- **Left open:** the base `FEATURES_VERSION` bump to `"0.2"` (D5, step 7)
  reuses the value that meant "Stage 3 present" before item 215 moved that
  meaning to `"0.3"`. No in-repo reader branches on the value, so this item
  follows the batch rule as written.
