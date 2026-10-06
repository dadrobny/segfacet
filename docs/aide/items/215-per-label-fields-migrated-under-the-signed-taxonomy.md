<!-- aide-template: item 3 -->
# Item 215 — Per-label fields migrated under the signed taxonomy

> **Created:** 2026-10-05 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 27 — Feature Schema Taxonomy & Coordinate System
> **Queue:** [`../queue/queue-029.md`](../queue/queue-029.md) · Item 215
> **Objectives:** G8
> **Suggested branch:** `aide/215-per-label-fields-migrated`

---

## Description

Roadmap Stage 27 D2, first half. Every feature-catalogue row that item 214's
signed mapping table gives **Moved by 215** is put at its new path. Every
reader of those paths is re-pointed in the same change, and the label's
identity is stored once. The catalogue and the other generated artifacts are
regenerated, and the version discriminator of each block whose shape changes
is bumped.

**This spec is written before its producer exists.** Item 214's design note
`docs/feature-taxonomy.md` and its mapping table are not built yet. So every
criterion below is stated against the table ("every row with Moved by 215"),
never against a guessed new path. The Authorised paths cover every reader
that could need re-pointing under any design that keeps the queue's scope
axis. They are re-checked at claim (Implementation Steps, step 0), once item
214 has merged and gate-0080 is approved. If the signed design departs from
the scope axis, this item is re-cut at that gate (queue 029, "Re-plan at the
gate"), not amended here.

**What moves (by the scope axis, A2).** Every row whose old path lies in one
of the five containers that duplicate per-label identity, plus every
`per_label.{label}.*` row:

- `stage3.per_label_offsets[]` (9 rows);
- `stage3.per_label_orientations[]` (8 rows);
- `stage3.per_label_neighbourhood[]` (17 rows; maintainer decision, D1);
- `image_features.per_label.{label}.*` (17 rows);
- `reference_delta.{label}.*` (10 catalogue rows, plus the 20 report-only
  rows below). It reaches the rules only on the transient rule-evaluation
  record, but it is also embedded in the written report.

**The 20 report-only rows (maintainer decision, 2026-10-05).** Stage 27
criterion 2 is read over every leaf of a real report. So the table also
carries 20 paths that a report built against the bundled reference carries
but the catalogue does not list. Each has the form
`reference_delta.{label}.features.<f>.<s>`, written with the literal feature
name:
- `<f>` is `extent_x_mm`, `extent_y_mm`, `extent_z_mm` or `spline_offset_mm`;
- `<s>` is `out_of_range`, `percentile_rank`, `robust_z`, `value` or
  `z_score`.

All 20 are this item's. Step 5 brings them into the catalogue (D8).

**What it is NOT.**

- **No measured value changes.** A moved field carries the same value at its
  new path. The neighbour-pair spacing collapse, a deliberate change to what
  is measured, is item 216's. If the signed design re-derives
  `stage3.per_label_neighbourhood[].stats.spacing_mm.*` from the surviving
  spacing array, item 215 moves those four paths with their values unchanged
  and the value change lands in item 216 (D3).
- **No field is dropped** (D2). The eight `retire`-status paths keep their
  rows. The only paths that disappear are the identity copies the table marks
  `merged`.
- **No neighbour-pair or case-level row moves here.** Those are the rows with
  Moved by 216: `relationships.*`, `overlaps[]*`, `stage3.curvature.*`,
  `stage3.spacing_consistency.*`, `stage3.monotonic_consistency.*`,
  `image_features.{available, backend, image_features_version,
  radiomics_available}`, `reference_delta.{lower_pct, upper_pct,
  reference_delta_version, reference_schema_version, reference_source,
  stratum}` and `features_version`.
  *Corrected at claim (2026-10-06):* four `stage3.curvature.*` /
  `stage3.monotonic_consistency.*` rows are this item's, not 216's: the
  three per-label tangent-angle arrays and `u_values[]` (the note's
  Deviation 5; A2's re-check). Every other row in this bullet is still
  item 216's.
- **No rule behaviour changes**, no threshold, no corpus case, no reference
  artifact rebuild (A5).
- **No in-memory result type changes.** The extractors' dataclasses and
  `reference.delta`'s `ReferenceDelta`, `LabelDelta` and `FeatureDelta` are not
  the record. The move happens where they are serialised and where the
  serialised record is read (D4).
- **No attestation.** No criterion carries a *(closes Stage 27 criterion M)*
  annotation. AC1 is criterion 2's identity half only. Item 217 attests
  criterion 2 from this item's AC1 together with item 216's addressability
  check, and criterion 3 from the corpus ratchet.

### The split with item 216 on shared files

Both migration items edit many of the same files. The rule is **ownership by
row**:

- Each item edits only the code, docs rows, schema definitions, path strings
  and test lines that name one of **its own** rows (Moved by 215 or 216).
- Generated artifacts are regenerated whole by each item, from its own tree.
  Item 216 regenerates on top of item 215's output. That includes the
  catalogue path-set digest `tests/corpus/119_pre_119_digests.json`: item 215
  rewrites it first, and item 216 rewrites it again from its own catalogue.
  The same order holds for the count pins in the reconciliation fence:
  item 216 moves each count again from the value item 215 left.
- Item 216 declares a dependency on item 215. So `aide check --queue 029`
  reports the shared May-change paths only as warnings, and 216 is authored
  knowing what 215 pins.
- **Version discriminators are bumped once per stage** (D5). Item 215 bumps
  each one whose block it reshapes. Item 216 bumps only a discriminator item
  215 left unchanged and whose block item 216 then reshapes.
- **What item 216 must keep true:**
  - this item's AC1: no new leaf whose last segment is bare `label` or
    `level_name` (pair identity keeps distinct key names, as `overlaps[]`'s
    `label_a` / `name_a` do today);
  - AC2 and AC3, which hold after 216 because the table fixes 215's new
    paths;
  - the `level-name-read-from-survivor` case.

  If item 216 must change any of these, its spec lists
  `tests/test_215_per_label_migration.py` under May change.
- **Item 216's AC1 can hold over all 165 rows.** That check is the
  catalogue's path set equalling the table's `kept`/`moved` new paths.
  - It can hold because this item's step 5 makes the catalogue list the new
    paths of the 20 report-only rows (D8).
  - Item 216 needs no catalogue machinery of its own for them. It only keeps
    the extended reference-delta driver in place.
  - Item 214's frozen AC1 test is left alone by both items.
- **The base `FEATURES_VERSION` (`"0.1"`)** is the discriminator of a
  features block without Stage 3. Whichever item first changes that block's
  shape bumps it, once (step 4, D5).

## Acceptance Criteria

Terms used below:

- **The table** is the list of `(old, new, change, moved_by)` rows that
  `tests/feature_taxonomy_mapping.py::read_mapping()` returns from
  `docs/feature-taxonomy.md` (A1). **215's rows** are the rows with
  `moved_by == 215`.
- **The catalogue's path set** is the `path` of every entry under
  `groups[*].entries[*]` in `docs/aide/feature_catalogue.generated.json`, read
  live. `tests/test_104_feature_catalogue_drift.py` holds that file equal to
  a fresh build. After step 5 it also covers the 20 report-only rows, so AC2
  and AC3 are checked against it for all 126 of 215's rows.
  *Corrected at claim (2026-10-06):* 215's rows in the signed table are
  130, not 126: A2's 126 plus the four Deviation-5 rows (A2's re-check).
  AC2 and AC3 are checked against the catalogue for all 130.
- **The case report** is the `segfacet_report.json` that
  `segfacet.cli.main(["run", "--scan", <scan>, "--seg", <seg>, "--intensity", "--out", <tmp_path>])`
  writes for the corpus case whose `case_id` is `"clean_control"`. `<seg>` and
  `<scan>` are that manifest entry's `seg_fixture` and `scan_fixture`,
  resolved through `segfacet.synth.corpus.load_manifest()` and `CORPUS_DIR`.
  No reference flag is passed, so the bundled real-VerSe19 reference applies
  (item 090) and the report carries every optional block.
- **Its leaf paths** are `segfacet.catalogue.iter_leaf_paths(content)`, where
  `content` is the case report without the keys `schema_version`,
  `config_version`, `case_id`, `verdict`, `reasons`, `per_label`, `findings`
  and `run_manifest`. The top-level `per_label` is the verdict's per-label
  reasons, not a feature. Each path has one leading `features.` segment
  removed, so it is in the catalogue's notation.
- **A path's last segment** is the text after its last `.`, with one trailing
  `[]` removed.

- [ ] **AC1: each identity key is stored at exactly one path.** For each `k`
      in (`label`, `level_name`), exactly one of the case report's leaf paths
      has last segment `k`. On `05eef1d` there are six for `label` and five
      for `level_name` (A3).
- [ ] **AC2: every path this item keeps or moves is produced.** The set of
      new paths of 215's rows whose change is `kept` or `moved`, minus the
      catalogue's path set, is empty.
      *Correction at claim (2026-10-06):* the wording stands, and its row
      set is 130 rows, not 126 (A2's re-check). It now also requires the
      four per-label new paths `per_label.{label}.curve.path_u` and
      `per_label.{label}.orientation.{tangent_angle_deg,
      tangent_coronal_unwrapped_deg, tangent_sagittal_unwrapped_deg}` in the
      catalogue.
- [ ] **AC3: no path this item moves or merges away is still produced.** The
      set of old paths of 215's rows whose change is `moved` or `merged`,
      minus every new path in the table, intersected with the catalogue's
      path set, is empty.
      *Correction at claim (2026-10-06):* the wording stands, and its row
      set is 130 rows, not 126 (A2's re-check). It now also requires the
      four old array paths `stage3.monotonic_consistency.u_values[]` and
      `stage3.curvature.{tangent_angles_deg, coronal_tangent_angles_deg,
      sagittal_tangent_angles_deg}[]` to be gone from the catalogue.

These criteria close no stage acceptance criterion.

The queue's third *Testable* ("every corpus case's measured firing equals
its expected set, unchanged") is not restated as a criterion. The existing
`tests/test_163_specificity_ratchet.py::test_ac2_ratchet_measured_equals_expected`
already compares every case of both corpora against its committed manifest
entry. Neither manifest is on May change, and the ratchet must pass unedited.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

Everything measured below was measured on 2026-10-05 at `05eef1d`
(`aide/queue-029`). The orchestrator ran clarify as interactive. Decisions
the maintainer already made are recorded under Decisions & Trade-offs (D1–D3),
not here. A1–A3 pin item 214's unbuilt output and are re-checked at claim
(step 0).

- **A1 (pin, item 214): the table is read through item 214's reader module
  only.** `tests/feature_taxonomy_mapping.py` exposes `NOTE_PATH` and
  `read_mapping(text=None)`. `read_mapping` returns a list of
  `(old, new, change, moved_by)` tuples in table order, with `change` in
  {`kept`, `moved`, `merged`} and `moved_by` an `int` in {215, 216}. It raises
  `ValueError` on a malformed row. The table's old paths are the 165-path
  pre-migration set that item 214's AC1 freezes:
  - the catalogue's 145 paths;
  - the 20 report-only `reference_delta.{label}.features.<f>.<s>` paths
    (Description), written with the literal feature name.

  A new path uses the catalogue's notation (`{label}`, `[]`, `{radiomic}`),
  plus any placeholder segment the note's `## Structure` section defines. A
  `merged` row's new path is the new path of some `kept` or `moved` row. Item
  214's AC2 requires the `kept`/`moved` new paths to be unique, so the 20
  report-only rows keep distinct new paths. This spec never parses the note
  itself.
  - *Re-checked at claim (2026-10-06, base `00fe6f5`: item 214 merged,
    note as of `2364df4`, gate-0080 ✅ Approved): agrees.* The module
    exposes `NOTE_PATH` and `read_mapping(text=None)`, plus a third name,
    `answer_lines`, which this item does not use. `read_mapping` returns
    `(old, new, change, moved_by)` tuples in table order, with `moved_by`
    an `int`. Its row regex admits only `kept`/`moved`/`merged` and
    215/216, and it raises `ValueError` on an unparseable row and when the
    `## Mapping table` heading does not occur exactly once. Measured: 165
    rows with 165 distinct old paths. The `kept`/`moved` new paths are
    unique, and every `merged` new path is a `kept`/`moved` new path. The
    note's `## Structure` says "No new placeholder is introduced", so new
    paths use only `{label}`, `[]` and `{radiomic}`.
- **A2 (pin, item 214): 215's rows are the per-label scope.** The queue cut
  the migration by scope, and gate-0080 re-cuts it if the signed design does
  not. So 215's rows are expected to be exactly the rows whose old path is
  `per_label`, or starts with one of:
  - `per_label.{label}.`
  - `stage3.per_label_offsets[]`
  - `stage3.per_label_orientations[]`
  - `stage3.per_label_neighbourhood[]` (D1)
  - `image_features.per_label.{label}.`
  - `reference_delta.{label}.`

  That is 1 + 44 + 9 + 8 + 17 + 17 + 30 = 126 rows. The 30 under
  `reference_delta.{label}.` are 10 catalogue rows and the 20 report-only
  rows. Step 0 compares this against the signed table. A row assigned differently is re-cut at the gate.
  - *Re-checked at claim (2026-10-06, base `00fe6f5`): corrected.* 215's
    rows in the signed table are **130**: 73 `kept`, 48 `moved`, 9 `merged`.
    Every row in the six prefixes above carries 215, with the per-prefix
    counts A2 gives (1, 44, 9, 8, 17, 17, 30). Four more rows carry 215
    and lie outside them:
    - `stage3.curvature.tangent_angles_deg[]` →
      `per_label.{label}.orientation.tangent_angle_deg`;
    - `stage3.curvature.coronal_tangent_angles_deg[]` →
      `per_label.{label}.orientation.tangent_coronal_unwrapped_deg`;
    - `stage3.curvature.sagittal_tangent_angles_deg[]` →
      `per_label.{label}.orientation.tangent_sagittal_unwrapped_deg`;
    - `stage3.monotonic_consistency.u_values[]` →
      `per_label.{label}.curve.path_u`.

    All four are `moved`. The note's Deviation 5 (maintainer decision,
    2026-10-06) assigns them to this item: a field sits at the scope of
    the entity it measures, whatever computed it. **This is not the
    gate's re-cut, so step 0's "stop" does not apply.** The gate row
    approved the design on 2026-10-06 with "Scope axis unchanged, items
    215/216 not re-cut". The four rows are per-label values, so they fall
    on the per-label side of that axis. A2's prefix list approximated the
    per-label scope and missed values that sit in a case-level container.

    What the four rows add:
    - **A record-shape change, with no value change.** Each array becomes
      one scalar per label. The element-to-label mapping follows the
      sequence each array is computed over today (`pipeline.py`):
      - the three tangent arrays use ascending integer label order
        (`ordered_centroids`), the same order as the
        `stage3.per_label_offsets[]` entries;
      - `u_values` uses `anatomical_centroids` (`CANONICAL_ORDER` rank,
        item 198).

      The record-wide anatomical reorder in the note's "Element order" is
      item 216's.
    - **No rule reader.** A grep of `src` finds only the serialisers in
      `feature_report.py`, the `feature_docs.py` rows and the
      `report_schema_v0.json` definitions, all already on May change.
      `stage3.curvature.inter_tangent_angles_deg[]` and the rest of
      `stage3.curvature` / `stage3.monotonic_consistency` stay item 216's.
    - **Two new test files** under the fence (Authorised paths, fifth
      pass).

    Also settled by the signed note, and recorded at step 0 (D10): the
    `image_features.per_label` rows land in the persisted features record
    (Option A, decided at the gate). Step 3 therefore applies, and step 4's
    base `FEATURES_VERSION` bump is this item's.
- **A3 (measured, and pinned against item 214): the identity copies.** In the
  case report's leaf paths:
  - `label` ends six paths: `per_label.{label}`, `stage3.per_label_neighbourhood[]`,
    `stage3.per_label_offsets[]`, `stage3.per_label_orientations[]`,
    `image_features.per_label.{label}` and `reference_delta.{label}`;
  - `level_name` ends five paths, the same minus `image_features`.

  That is nine copies beyond the canonical pair. Item 214's A2 names
  `per_label.{label}.{label, level_name}` as canonical, and its A5 rules out
  dropping a field. So the table is expected to mark the nine copies `merged`
  onto one surviving pair. Nothing else in the record ends in a bare `label`
  or `level_name`: `component_contacts[].neighbour_label`,
  `stray_contact_label`, `window_labels[]` and `overlaps[].{label_a, label_b,
  name_a, name_b}` are references to other labels, and AC1 does not count
  them.
  - *Re-checked at claim (2026-10-06, base `00fe6f5`): agrees.* The signed
    table marks exactly nine 215 rows `merged`, each onto a `kept`
    survivor:
    - `per_label.{label}.label` absorbs the `label` of
      `stage3.per_label_offsets[]`, `stage3.per_label_orientations[]`,
      `stage3.per_label_neighbourhood[]`,
      `image_features.per_label.{label}` and `reference_delta.{label}`;
    - `per_label.{label}.level_name` absorbs the `level_name` of the same
      containers except `image_features`.

    Of the `kept`/`moved` new paths in the whole table, only these two end
    in a bare `label` or `level_name`. Item 216's three `merged` rows
    (`overlaps[].name_a`, `overlaps[].name_b`,
    `stage3.spacing_consistency.spacings_mm[]`) add no such leaf. The
    note's Answer "Identity fields stored in several containers" and its
    rule 1 state the same design.
- **A4 (measured): who reads the five containers.** The grep under
  Authorised paths found these readers in `src/segfacet`:
  - **Rules.** `heuristics/spline_offset.py` reads `per_label_offsets`
    entries, including `level_name` for its finding reason.
    `heuristics/intensity.py` reads `image_features.per_label`.
    `heuristics/reference_delta.py` and
    `heuristics/intensity_reference_delta.py` read the per-label delta
    entries, including `level_name` for their reasons. All four also declare
    the paths as strings in their mode declarations.
  - **Serialisers.** `feature_report.py` (`build_features_block`,
    `build_image_features_block`) and `reference/delta.py`
    (`_label_delta_to_dict`, `reference_delta_to_dict`).
  - **Other readers.** `eval/feature_match.py` (offsets), `reference/ingest.py`
    (offsets, orientations), `reference/delta.py`'s three `compute_*`
    functions (offsets, orientations, `image_features.per_label`),
    `human_report.py` (`image_features.per_label`), `observed_range.py` (rule
    2's `image_features.per_label.{label}.first_order` target) and
    `catalogue.py` (driver records, and `normalise_leaf_path` rule (d) for
    `reference_delta.per_label.<int>`).
  - **Path strings and docs rows.** `feature_docs.py` (`FEATURE_DOCS` keys,
    the block-owner prefixes, item 106's steering rows, `PATH_ALIASES`'s
    `spline_offset_mm`), `failure_modes.py` (mode signal paths) and
    `report_schema_v0.json`.

  The queue also names `synth/regression`. The grep finds no path read
  there: it only unpacks `run_qc_with_intensity`'s five-tuple, which step 3
  keeps. `heuristics/mislabel.py` and `heuristics/fused_label.py` read
  `stage3.monotonic_consistency` and `stage3.spacing_consistency`, which are
  item 216's rows.
- **A5 (measured): no reference artifact stores a record path.**
  `src/segfacet/reference/reference_verse_v1.json` keys its statistics by 21
  feature names (`spline_offset_mm`, `eigenvalue_ratio`, `intensity_*`, …).
  `reference/ingest.py` and `reference/delta.py` map those names to record
  paths in code. So neither bundled artifact is migrated or rebuilt: a
  rebuild needs the VerSe19 data, and once the readers are re-pointed it
  would give the same values. Today
  `observed_range.resolve_reference_features` resolves all 21 names against
  the catalogue's path set. `tests/test_124_observed_range.py::test_ac2_every_reference_feature_resolves_uniquely`
  keeps that true, and must pass with its assertions unedited.
- **A6 (measured): the transient `intensity_reference_delta` block.** It is
  built by the same `reference_delta_to_dict` as `reference_delta`, lives
  only on the rule-evaluation record, and is not in the catalogue or the
  written report. So it takes whatever per-label shape this item gives
  `reference_delta`. No criterion counts its identity keys, because nothing
  stores it. Its rule's finding reasons are covered by the
  `level-name-read-from-survivor` case.
- **A7 (default, re-checked at claim): `per_label.{label}.*` rows are
  `kept`.** The starting proposal's per-label scope is that container, and
  item 214's A2 calls it canonical. If the signed table marks any
  `per_label.{label}.*` row `moved`, every reader of the canonical container
  is in scope. That is every rule and about sixty more test files. Step 0
  then re-runs the fence grep with that row's old path and amends Authorised
  paths before any test is written.
  - *Re-checked at claim (2026-10-06, base `00fe6f5`): agrees.* All 45
    rows with old path `per_label` or `per_label.{label}.*` are `kept`,
    each with new path equal to old. The fence is not widened to every
    reader of the canonical container. Rows move *into* that container
    from elsewhere: the `curve`, `orientation`, `neighbourhood` and
    `intensity` kinds. That is not this assumption's trigger. Its effect
    on the canonical entry's shape falls to `report_schema_v0.json`'s
    `labelFeatures`, which has `additionalProperties: false` and is already
    on May change. A grep of `tests` finds no test pinning that entry's
    key set.
- **A8 (measured): the reasons are clean today.** The case report holds 146
  findings: `intensity_reference_delta` 88, `reference_delta` 35, `bounds` 20
  and `intensity` 3. Both corpora's pipeline findings hold 23 more. No reason
  in either set contains `None`.
- **A9: no human gate beyond gate-0080, and no environment-gated
  capability.** PyRadiomics' `extended.{radiomic}` rows move like any other
  row. Their tests already skip cleanly without the package.

## Implementation Steps

0. **At claim (spec-author, before any test is written).** Item 214 has
   merged and gate-0080 reads `✅ Approved`.
   - Re-check A1–A3 and A7 against `read_mapping()` and the note's
     `## Structure`. Append a dated re-check to each.
   - If 215's rows differ from A2, stop: that is the gate's re-cut.
   - Re-run the fence grep (Authorised paths) and, for any new placeholder
     segment, grep its record key. Amend Authorised paths with any hit not
     listed.
   - Write down which `merged` rows land on which survivor, and which blocks
     change shape (step 4).
1. **Serialisers emit the new paths.**
   - `feature_report.build_features_block`: the three `stage3` per-label
     lists, and `per_label.{label}`.
   - `feature_report.build_image_features_block`: the per-label entries.
   - `reference/delta.py`, `_label_delta_to_dict` and
     `reference_delta_to_dict`: the per-label entries.

   Each `merged` identity copy is no longer emitted. The extractors and the
   delta dataclasses are unchanged (D4). If a placeholder segment the note
   defines appears in a new path, extend `catalogue.normalise_leaf_path` to
   produce it, and adjust its rule (d) if `reference_delta`'s per-label keys
   move.
2. **Readers follow the table.** Re-point each reader A4 lists:
   - each rule's `evaluate`, and its mode-declaration path strings;
   - `eval/feature_match.py`;
   - `reference/ingest.py`, and `reference/delta.py`'s three `compute_*`
     readers;
   - `human_report._render_image_features_section`;
   - `observed_range.resolve_reference_features` rule 2;
   - `catalogue.iter_driver_records`, only if a block it realises changes
     shape;
   - `feature_docs.py`'s `FEATURE_DOCS` keys, owner prefixes, steering rows
     and `PATH_ALIASES`. A moved row keeps its documentation and its
     catalogue `status`;
   - `failure_modes.py`'s path strings, for 215's rows only.

   **A reader of a merged identity copy reads the survivor.** For example,
   `spline_offset` and both delta rules take `level_name` from the surviving
   copy, so their reasons render unchanged and never say `None`. Every
   absence-tolerant `.get(…, [])` / `isinstance` guard keeps its tolerance,
   but now on the new path: an un-pointed guard is the silent failure this
   step exists to prevent.
3. **`pipeline.py` and `report.py`, only if a 215 row moves a field from one
   report block to another** (for example, image intensity into
   `features.per_label.{label}`). `run_qc`, `run_qc_with_reference` and
   `run_qc_with_intensity` keep their return arity and order, so
   `synth/regression.py`, `eval/harness.py` and `cli.py` need no edit (D6).
   Their docstrings are updated where they name a moved path.
4. **Version discriminators (D5).**
   - Bump `feature_report.FEATURES_VERSION_STAGE3` from `"0.2"` to `"0.3"`.
     The Stage-3-bearing features block changes shape.
   - Bump `IMAGE_FEATURES_VERSION` (`"1.0"` → `"1.1"`) if
     `image_features`' shape changes, and `REFERENCE_DELTA_VERSION`
     (`"1.0"` → `"1.1"`) if `reference_delta`'s does.
   - The base `FEATURES_VERSION` (`"0.1"`, for a block without Stage 3) is
     bumped by whichever of items 215 and 216 first changes that block's
     shape, once. This item changes it only if the table moves a field into
     `per_label.{label}`. Under A7 the canonical container's own rows are
     `kept`, and the three `stage3` lists are absent without Stage 3. So the
     only way this item reaches such a block is the table moving an
     `image_features` or `reference_delta` per-label field into it. Then a
     single-label run with `--intensity` or a reference changes shape, and
     this item bumps `"0.1"` → `"0.2"`. Otherwise it does not, and item 216,
     which reshapes `relationships` and `overlaps` (present in every block),
     owns the bump. Step 0 records which case holds.
   - The top-level report `schema_version` stays `"0.1"`, following the
     precedent that Stages 2–8 added blocks without bumping it.
   - Update `report_schema_v0.json`'s definitions for every moved container,
     and its `features_version` description. `report.build_report` validates
     every report against this schema, so a stale definition fails loudly.
5. **The catalogue covers the 20 report-only rows (D8).**
   - In `catalogue.iter_driver_records`, the reference-delta driver's single
     placeholder `FeatureDelta`, for `physical_volume_mm3`, becomes one
     placeholder per name in `segfacet.reference.ingest.INGESTED_FEATURES`.
     That constant is reused, not restated. It names exactly the five
     features `compute_reference_delta` scores from a record.
   - The driver still goes through `reference_delta_to_dict`, so the
     catalogue lists the 20 paths at whatever new path step 1's serialiser
     gives them.
   - Add one `FEATURE_DOCS` entry per new path in `feature_docs.py`, so the
     drift test's documented-path check holds. Give each the `status` of its
     `physical_volume_mm3` counterpart (`retune`, or the steering verdict at
     claim).
   - Nothing else about the driver changes. The intensity and morphology
     vocabularies are not scored from the record by `compute_reference_delta`,
     so they never reach a report's `reference_delta` block and get no rows.
6. **Regenerate, each twice into a scratch directory first and compared
   byte for byte, in this order:**
   - `python -m segfacet.catalogue --json <tmp>/c.json --md <tmp>/c.md`;
   - `python -m segfacet.failure_modes --json … --md …`;
   - `python -m segfacet.traceability --json … --md …`;
   - `python -m segfacet.rule_table --md …`.

   Run each with `.venv/bin/python`. Then run each with its default outputs.
   Then edit `tests/report_format_fixture.py`'s hand-written record to the
   new shape, and regenerate `tests/golden/report_format_contract.json` with
   `.venv/bin/python -m tests.report_format_fixture` (CLAUDE.md "Common
   commands"; never from a test).
   - **After the catalogue, rewrite `tests/corpus/119_pre_119_digests.json`.**
     Take the regenerated catalogue JSON's `groups[*].entries[*].path`
     values, sort them, and join them with `"\n"`. The new value is the
     sha256 hex digest of the UTF-8 bytes. This is the computation
     `tests/test_119_curve_formulation.py::test_ac27_catalogue_leaf_path_set_unchanged_from_pre_119`
     and `tests/test_123_recalibrate_and_regenerate.py` both make. Write the
     file with `write_bytes`, as `json.dumps({"catalogue_leaf_path_set_sha256": <hex>}, indent=2) + "\n"`,
     which is its present byte layout: a two-space indent, LF line endings
     and a trailing newline.
   - Every regenerated file is already LF-pinned in `.gitattributes`
     (`docs/aide/*.generated.*` by name, `tests/golden/*.json`,
     `tests/corpus/119_pre_119_digests.json`), so no pin is added.
   - `docs/aide/golden_evidence.generated.json` holds no moved path. It is
     predicted to regenerate byte-identical, and a difference is a
     hand-back.
7. **Reconcile the existing tests** under the fence below. Record every
   edited test in Decisions by node id, old → new.
8. **Run `python .aide/scripts/aide.py scope 215 --base aide/queue-029`** and
   confirm it exits 0.

No dependency is added.

## Authorised paths

**How the list was produced (2026-10-05, `05eef1d`), so step 0 can re-run
it.** It was derived by grep, not by a failing-test probe. A probe lists each
red test once, at its first failing assert, and a copy without `.git` skips
git-gated tests (insights `2026-10-05-da43`, `2026-10-05-dc87`). Three
searches over `src tests`:

1. `grep -rlE "per_label_offsets|per_label_orientations|per_label_neighbourhood"`
2. `grep -rlE "image_features" src tests | xargs grep -lE "per_label"`
3. `grep -rlE "reference_delta\.\{label\}|reference_delta\.per_label|\[\"(intensity_)?reference_delta\"\]\[\"per_label\"\]|delta(_dict|_block)?\[\"per_label\"\]|reference_delta_to_dict|\"(intensity_)?reference_delta\": ?\{"`

Two further greps covered the rest. For the generated docs, search 1's
tokens plus `image_features\.per_label` and `reference_delta\.\{label\}` were
run over the `*.generated.*` files in `docs/aide`. For version pins,
`features_version|FEATURES_VERSION|IMAGE_FEATURES_VERSION|REFERENCE_DELTA_VERSION`
was run over the tests.

**A fourth pass, added 2026-10-05 after item 216's author found two holes,
looks for pins that name no path token.** These are counts of the
catalogue's entries or a record's leaf paths, written as bare integers, and
digests of the catalogue's path set:

- `grep -rnE "len\((cat|catalogue|full_catalogue)\.entries\)|len\([a-z_]*entries\)\s*==\s*[0-9]+|len\(paths\)\s*==\s*[0-9]+|leaf_count|LEAF_PATH_COUNT"` over the tests;
- `grep -rlE "sha256|hexdigest|_digests\.json"` over the tests, then reading each hit for what it hashes.

The first pass added three count pins (131, 132 and 136). The second added
`tests/corpus/119_pre_119_digests.json`. That file is a sha256 of the
catalogue's sorted path set, asserted by 119, 120 and 123. Every other
digest hit hashes something this item does not touch: NIfTI data, source
bytes, the corpus sheet, the reference artifact or a ladder table.

A hit was dropped only for one of four reasons. It was a dated history
docstring (the identity-ordering-alignment operators' module). It was a
signed design or history document (the spinal-curve model note, the golden
decision table). It named only item 216's case-level rows (the calibrate
test, the item-090 reference-default test). Or it was a hand-built rule
input carrying a version literal that no reader checks (items 047, 062 and
064's rule tests keep theirs).

**A fifth pass, at claim (2026-10-06, base `00fe6f5`), covers the four
Deviation-5 rows** (A2's re-check):
`grep -rnE '\["(curvature|monotonic_consistency)"\]|stage3\.(curvature|monotonic_consistency)\.(u_values|tangent_angles|coronal_tangent|sagittal_tangent)|"(u_values|tangent_angles_deg|coronal_tangent_angles_deg|sagittal_tangent_angles_deg)"' tests`.

- **Added to May change:** `tests/test_122_signed_curvature.py` and
  `tests/test_143_s_axis_correction.py`.
- **Widened from fence (b) to fence (a) and (b):** `tests/test_131_tangent_direction_normalisation.py`
  and `tests/test_132_monotonicity_against_traversal_order.py`, which read
  the arrays and name their paths.
- **Already listed:** the hits in 022, 033, 119, 120, 123, 124 and 130, the
  format fixture and its contract.
- **Dropped:** every other hit reads an extractor dataclass, not the
  record (D4: 017, 019, 020, 072, 121, 210), or holds an unrelated
  identifier (058 and `test_features_intensity.py`'s `hu_values`).
- **No `src` hit beyond May change.** The step-0 search for the record key
  of a new placeholder segment was not needed, because the note introduces
  none.

**May change:**

- `src/segfacet/feature_report.py` — the features and image-features serialisers (step 1), `FEATURES_VERSION_STAGE3` and `IMAGE_FEATURES_VERSION` (step 4).
- `src/segfacet/reference/delta.py` — the per-label delta serialiser (step 1), the three `compute_*` readers (step 2), `REFERENCE_DELTA_VERSION` (step 4).
- `src/segfacet/reference/ingest.py` — the offsets and orientations reader (step 2).
- `src/segfacet/heuristics/spline_offset.py` — reader, level-name source and declared paths (step 2).
- `src/segfacet/heuristics/intensity.py` — reader and declared paths (step 2).
- `src/segfacet/heuristics/reference_delta.py` — reader, level-name source and declared paths (step 2).
- `src/segfacet/heuristics/intensity_reference_delta.py` — reader, level-name source and declared non-signal paths (step 2).
- `src/segfacet/eval/feature_match.py` — the offsets reader (step 2).
- `src/segfacet/human_report.py` — the intensity-section reader (step 2).
- `src/segfacet/observed_range.py` — rule 2's intensity target path (step 2).
- `src/segfacet/catalogue.py` — `normalise_leaf_path`, the driver records, and the reference-delta driver's five placeholder features (steps 1, 2, 5).
- `src/segfacet/feature_docs.py` — doc rows, owner prefixes, steering rows, `PATH_ALIASES`, and the 20 new report-only doc rows (steps 2, 5).
- `src/segfacet/failure_modes.py` — signal and candidate path strings of 215's rows (step 2).
- `src/segfacet/report_schema_v0.json` — moved container definitions and the `features_version` description (step 4).
- `src/segfacet/pipeline.py` — only if a 215 row moves a field between report blocks (step 3).
- `src/segfacet/report.py` — only if a 215 row moves a field between report blocks (step 3).
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 6).
- `docs/aide/feature_catalogue.generated.md` — regenerated (step 6).
- `docs/aide/failure_modes.generated.json` — regenerated (step 6).
- `docs/aide/failure_modes.generated.md` — regenerated (step 6).
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 6).
- `docs/aide/traceability_matrix.generated.md` — regenerated (step 6).
- `docs/aide/rules.generated.md` — regenerated (step 6).
- `tests/report_format_fixture.py` — the hand-written record's new shape (step 6).
- `tests/golden/report_format_contract.json` — regenerated from the fixture (step 6).
- `tests/test_215_per_label_migration.py` — **new**, this item's test module.
- `tests/test_022_stage3_serialisation.py` — fence (a), (c): stage3 list shape and the `"0.2"` literal (search 1).
- `tests/test_033_mislabel.py` — fence (a): hand-built offsets records (search 1).
- `tests/test_035_failure_modes.py` — fence (a): hand-built offsets records fed to `run_rules` (search 1).
- `tests/test_039_identity_ordering_alignment_perturbations.py` — fence (a): live offsets read (search 1).
- `tests/test_044_reference_ingestion.py` — fence (a) (search 1).
- `tests/test_046_reference_delta.py` — fence (a) (searches 1, 3).
- `tests/test_047_reference_delta_rule.py` — fence (a): hand-built delta entries (search 3).
- `tests/test_049_acceptance_stage6.py` — fence (a) (search 3).
- `tests/test_049_reference_integration.py` — fence (a) (search 3).
- `tests/test_051_feature_match.py` — fence (a), (c) (search 1).
- `tests/test_061_image_features_fusion.py` — fence (a) (search 2).
- `tests/test_062_intensity_rule.py` — fence (a): hand-built image-features entries (search 2).
- `tests/test_064_intensity_reference_delta_compute.py` — fence (a) (searches 2, 3).
- `tests/test_064_intensity_reference_delta_rule.py` — fence (a): hand-built delta entries (search 3).
- `tests/test_065_acceptance_stage8.py` — fence (a) (search 2).
- `tests/test_065_cli_intensity.py` — fence (a) (search 2).
- `tests/test_065_intensity_pipeline.py` — fence (a) (searches 2, 3).
- `tests/test_081_reference_morphology.py` — fence (a) (searches 1, 2).
- `tests/test_103_feature_catalogue.py` — fence (a), (b) (searches 1–3).
- `tests/test_104_feature_catalogue_drift.py` — fence (a): path literals in its own cases; the drift assertions themselves stay as they are (search 1).
- `tests/test_106_stage19_validation.py` — fence (a), (b) (search 2).
- `tests/test_110_neighbourhood_wiring.py` — fence (a), (b) (search 1).
- `tests/test_115_stage26_validation.py` — fence (a): `per_label_neighbourhood` membership (search 1).
- `tests/test_119_curve_formulation.py` — fence (a) (search 1).
- `tests/test_120_leave_one_out_offset.py` — fence (a) (search 1).
- `tests/test_121_tangent_orientation.py` — fence (a): the orientations entry key set (search 1).
- `tests/test_123_recalibrate_and_regenerate.py` — fence (a) (search 1).
- `tests/test_124_observed_range.py` — fence (a), (b): the 145-path count; AC2 and AC3's assertions unedited (A5) (searches 1–3).
- `tests/test_125_stage28_validation.py` — fence (a) (search 1).
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — fence (a) (search 1).
- `tests/test_130_one_closest_point_search.py` — fence (a) (search 1).
- `tests/test_131_tangent_direction_normalisation.py` — fence (b): `_PRE_ITEM_TOTAL_LEAF_PATH_COUNT` (145) (count pass, 2026-10-05).
- `tests/test_132_monotonicity_against_traversal_order.py` — fence (b): the `leaf_count == 145` pin (count pass, 2026-10-05).
- `tests/test_136_rule_mode_declarations.py` — fence (b): the `len(entries) == 145` pin (count pass, 2026-10-05).
- `tests/corpus/119_pre_119_digests.json` — fence (d): the catalogue path-set digest, regenerated (step 6; digest pass, 2026-10-05).
- `tests/test_137_mode_less_rule_disposition.py` — fence (a) (searches 1, 2).
- `tests/test_138_traceability_matrix.py` — fence (a) (search 1).
- `tests/test_145_eight_hypothesised_modes.py` — fence (a) (search 1).
- `tests/test_146_ninth_mode_and_first_proposed.py` — fence (a) (search 2).
- `tests/test_148_per_path_mode_attribution.py` — fence (a), (b): the 145-entry count (searches 2, 3).
- `tests/test_149_conformance_report.py` — fence (a) (search 3).
- `tests/test_151_stage30_validation.py` — fence (a) (search 1).
- `tests/test_154_ladder_remeasurement.py` — fence (a): an offset path literal (search 1).
- `tests/test_189_spline_offset_condition.py` — fence (a) (search 1).
- `tests/test_191_condition_gate.py` — fence (a) (search 1).
- `tests/test_212_crop_at_border_volume_crop.py` — fence (a): AC4's live offsets read (search 1).
- `tests/test_122_signed_curvature.py` — fence (a): the per-plane tangent arrays' paths and serialised reads (fifth pass, added at claim 2026-10-06).
- `tests/test_143_s_axis_correction.py` — fence (a): live `tangent_angles_deg` reads (fifth pass, added at claim 2026-10-06).

**The reconciliation fence** applies to the listed `tests/test_*.py` files
other than this item's own module. The builder reconciles after
regeneration. Four kinds of edit are allowed.

**(a) A re-pointed path.** A path string, key access, or hand-built input
record that names the old path of a 215 row is rewritten to that row's new
path. For a `merged` identity copy, the copy is removed from a hand-built
input, and a read of it reads the survivor. The asserted value is unchanged.
*Amended at claim (2026-10-06):* there are also the four Deviation-5 rows,
each an array that becomes one scalar per label (A2's re-check). A read of
one of those arrays reads the per-label scalars in the order the array was
computed in, and compares the same values. That order is ascending integer
label for the three tangent arrays, and anatomical order for the path
positions (`CANONICAL_ORDER` rank, then integer label). In a hand-built
input the array key is removed, as the empty path-position list is in
hand-built monotonic-consistency blocks.

**(b) A moved path count.** A count literal moves to its live value. This
covers any count: catalogue paths overall or under a prefix, catalogue paths
attributed to a mode or rule or held in one evidence bucket (including an
exhaustive bucket distribution), and one record's leaf paths.

The dated item-215 comment beside the edited literal accounts for the change
row by row, and the arithmetic must close. It counts four kinds of row:

1. each merged row that leaves the count's scope (−1);
2. each row moved into or out of the scope (+1 or −1). A field moved across
   report blocks is one example: it raises item 103's record leaf-path
   count;
3. each of the 20 report-only rows newly catalogued inside the scope (+1);
4. each survivor that changed evidence bucket.

For the fourth kind: the canonical per-label label is in the bookkeeping
bucket today. It gains the mode-less source once the spline-offset and
reference-delta rules read it. That moves one entry between buckets in item
137's exhaustive evidence table, and can move item 136's empty bucket.

A change the comment cannot attribute to a row of the table is not
reconciled. It is a hand-back.

**(c) A bumped version literal.** A pinned value of a discriminator step 4
bumps moves to the bumped value.

**(d) The path-set digest**, `tests/corpus/119_pre_119_digests.json`, is
regenerated by step 6. It is never hand-edited, and the three tests that
read it are not edited for it. Items 120, 121, 123, 167 and 187 each moved it
the same way.

Nothing else is allowed. No measured expected value changes: no number,
firing set, rendered human-report row or finding reason. No test is skipped,
marked expected-to-fail, loosened in tolerance, renamed or retired.
`tests/test_214_feature_taxonomy_design.py` stays off May change. Its AC1
compares the table against a frozen literal and holds through the
migration. A red test in a file not listed here is a
hand-back to spec-author, not an edit. **Re-run each listed test after
editing it, until it is green.** A test can hold a second stale path behind
its first failing assert (insight 2026-10-05-da43).

**Asserts against:**

- `docs/feature-taxonomy.md` — AC1's precondition, AC2 and AC3 read the mapping table through item 214's reader.
- `tests/feature_taxonomy_mapping.py` — the reader module (A1), imported, never edited.
- `src/segfacet/reference/reference_verse_v1.json` — the default reference the case report is built against; not rebuilt (A5).
- `tests/corpus/fixtures/clean_control_seg.nii.gz` — the case report's segmentation.
- `tests/corpus/fixtures/base_scan.nii.gz` — the case report's scan.
- `tests/corpus/fixtures/displace_seg.nii.gz` — read by the `level-name-read-from-survivor` case.

**Kept off May change on purpose**, so that `aide scope` refuses an edit to
any of them. The CLI, the regression helpers and the eval harness stay off
because step 3 keeps the pipeline's tuples. The traceability and rule-table
generators and every `features/` extractor read no moved path. The mislabel
and fused-label rules are item 216's. Both corpus manifests stay off so that
firing cannot be re-expected, and the specificity ratchet must pass
unedited. The synthetic default reference and the golden-evidence companion
are predicted unchanged.

## Testing Strategy

**The new module is `tests/test_215_per_label_migration.py`**, with one test
per AC.

- **The table** is read only through
  `from feature_taxonomy_mapping import read_mapping`, as item 214's tests
  import it (A1).
- **The case report** is built once, by a module-scoped fixture that calls
  `segfacet.cli.main` in-process into a `tmp_path_factory` directory. It is
  read with `json.loads(...read_text(encoding="utf-8"))`. It is shared by AC1
  and the adversarial case.
- **AC1 asserts its input is recognisable first** (§6). For each of the five
  container prefixes in A2 (`stage3.per_label_offsets[]`,
  `stage3.per_label_orientations[]`, `stage3.per_label_neighbourhood[]`,
  `image_features.per_label.{label}.`, `reference_delta.{label}.`), at least
  one 215 row with that old-path prefix, whose change is `kept` or `moved`,
  has its new path among the case report's leaf paths. A run that lost a
  block therefore fails, rather than passing with fewer copies to count.
  The test is then parametrised over `k`.
- **AC2 and AC3 assert their row sets are recognisable first.** 215's rows
  include at least one row from each of those five prefixes, and at least
  one `merged` row.
- Last segments are computed in the test as the AC defines them. The test
  never calls `catalogue._last_segment` or `observed_range._last_segment`,
  which differ on `[]`.

**Adversarial case, the only one.** The test-writer writes it and no
others.

- **`level-name-read-from-survivor`.** No finding `reason` contains the
  substring `None`, over either source:
  - the case report's `findings`;
  - `segfacet.synth.regression.pipeline_findings(case)` for the manifest case
    whose `case_id` is `"displace"`, which fires `spline_offset`.

  A8 measured zero such reasons. This guards a reader that still takes
  `level_name` from a merged identity copy, gets `None`, and renders
  `(None)` in every reason it writes:
  - `spline_offset` on `per_label_offsets`;
  - `reference_delta` and `intensity_reference_delta` on the delta
    entries.

  The ratchet compares rule ids and labels only. And the corpora run with no
  reference, so the delta rules never fire there. The ratchet would stay
  green.

*Amended at claim (2026-10-06): a second adversarial case*, added by A2's
re-check. The test-writer writes it as well, and still no others.

- **`path-u-mapped-in-anatomical-order`.** The input is the
  `clean_control` corpus segmentation relabelled
  `{20: 28, 21: 20, 22: 21, 23: 22, 24: 23}`, which runs head-to-tail as
  T13, L1, L2, L3, L4. `tests/test_198_ordering_along_expected_sequence.py`
  builds it the same way. Its record comes from
  `segfacet.pipeline.extract_feature_record` with the bundled default
  config. Two things are asserted:
  - its `stage3.monotonic_consistency.is_monotonic` is `True`;
  - `per_label.{label}.curve.path_u`, read in label order 28, 20, 21, 22,
    23, is strictly increasing.
- **The failure it guards.** `u_values` is the one Stage-3 array computed
  in anatomical order. Every other array is in ascending integer order. A
  serialiser that zips all four arrays with one integer-ordered label list
  gives every label another label's path position. Label 28 then gets the
  last value, and the sequence read head-to-tail is no longer increasing.
- **Why nothing else catches it.** On `clean_control` the two orders
  coincide, so the mismatch never shows. AC2 and AC3 compare paths only.
  Validation step 3 compares observed ranges, which do not record which
  label holds which value. The ratchet compares firing only.

**What else carries the queue's *Testable* claims:**

- "the regenerated catalogue and the drift test agree" is
  `tests/test_104_feature_catalogue_drift.py`, run as reconciled;
- "every corpus case's measured firing equals its expected set" is
  `tests/test_163_specificity_ratchet.py::test_ac2_ratchet_measured_equals_expected`,
  unedited, over unedited manifests;
- that every reference feature still resolves to a catalogue path is
  `tests/test_124_observed_range.py` AC2 and AC3, unedited (A5);
- report-schema conformance is `report.build_report`'s own
  `jsonschema.validate` on every report any test writes.

**Existing tests to reconcile:** the files under the fence in Authorised
paths, found by the recorded greps. That list is a floor, not a guarantee. A
grep finds a file that names a moved path. It does not find a test that
breaks because a value was read from an un-pointed guard. The full suite run
and the Validation section are what close that gap.

## Validation  <!-- OPTIONAL: how to OBSERVE this working, beyond the tests -->

No `[validation]` profile is needed. The validator runs:

1. `python .aide/scripts/aide.py scope 215 --base aide/queue-029`, which must
   exit 0.
2. **Byte-identical regeneration.** Run each step-6 generator twice into
   scratch and compare the bytes. Then diff scratch against the committed
   files. There must be no difference.
3. **No moved value changed, row by row.** Read the base catalogue with
   `git show <claim base>:docs/aide/feature_catalogue.generated.json`. For
   every 215 row whose change is `kept` or `moved`, compare the base entry at
   the old path with the branch entry at the new path. Their `status` and
   their observed-range values must be equal. A `merged` row has no branch
   entry. Its survivor's entry must hold the same identity values. The 20
   report-only rows have no base entry. For each, check only that the branch
   entry exists and carries its `physical_volume_mm3` counterpart's `status`.
4. **The human report does not move.** Run
   `.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg <seg> --intensity --out <tmp>`
   for `<seg>` in `clean_control_seg.nii.gz` and `displace_seg.nii.gz`. Run it
   once on the claim base and once on the branch. The base run comes from a
   separate clone with its own venv (CLAUDE.md "Gotchas"). Each
   `segfacet_report.txt` must be byte-identical across the two runs.

   It renders every finding reason (146 on the clean control, with values
   and level names) and the intensity table. So it catches:
   - a delta reader left on an old path, which silently drops a feature from
     scoring;
   - an un-pointed intensity renderer, which prints `(unavailable)`;
   - a level name read from a merged copy.
5. `python .aide/scripts/aide.py check`, which must report no errors.

## Dependencies

- **Item 214** — the signed design note `docs/feature-taxonomy.md`, its
  mapping table, and the reader `tests/feature_taxonomy_mapping.py` (A1, A2).
  Its gate also holds this item: gate-0080 — `Blocks: items 215, 216, 217`.

**Downstream:** item 216 declares a dependency on this item and builds on
its tree, under the split stated in the Description. Item 217 attests Stage
27 criterion 2's identity half from this item's AC1, and criterion 3 from the
ratchet. It also replays Validation steps 2 and 4 from a clean clone.

## Decisions & Trade-offs

To be updated during implementation.

- **D1 (maintainer decision, 2026-10-05): five identity containers, not
  four.** Identity is duplicated in `stage3.per_label_offsets[]`,
  `stage3.per_label_orientations[]`, `image_features.per_label`, the
  transient `reference_delta.{label}` and `stage3.per_label_neighbourhood[]`.
  This item moves all five, and every `stage3.per_label_neighbourhood[]` row
  carries Moved by 215.
- **D2 (maintainer decision, 2026-10-05): no field is dropped in this
  stage.** The eight `retire`-status paths each keep a row.
- **D3 (maintainer decision, 2026-10-05): this item changes no measured
  value.** Item 216 carries the adjacent-pair spacing collapse. The
  per-element statistics under
  `stage3.per_label_neighbourhood[].stats.spacing_mm.*` are moved by this
  item. If the design re-derives them from the surviving array, their value
  change lands in item 216. Criterion 3 for this item is "every corpus case's
  measured firing equals its expected set, unchanged".
- **D4: the migration happens at the serialisers and the readers, not in the
  result types.** The record is the serialised dict. Leaving the extractors'
  dataclasses and the delta dataclasses alone keeps every value identical by
  construction. It also leaves tests that use `compute_reference_delta(...)`'s
  in-memory result, such as `test_093` and `test_097`, outside the fence.
- **D5 (default, standing since the 2026-10-05 batch review): version
  discriminators, once per stage.**
  - `FEATURES_VERSION_STAGE3` is the features block's own discriminator,
    the one its schema description says Stage 3 bumped. This item bumps it,
    and bumps the image-features and reference-delta discriminators where
    their blocks change.
  - The base `FEATURES_VERSION` goes to whichever item first changes a
    no-Stage-3 block's shape, once (step 4). Item 216 owns it unless this
    item's table moves an image or reference field into `per_label.{label}`.
  - The top-level `schema_version` stays `"0.1"`. Stages 2–8 never bumped it
    when they added blocks.
  - Item 216 does not re-bump a discriminator this item already bumped. Both
    items reach `main` in one queue PR, so no consumer ever sees the
    intermediate shape.
- **D6: the pipeline's return tuples keep their arity and order.** That keeps
  `cli.py`, `synth/regression.py` and `eval/harness.py` out of scope (A4),
  whichever block a moved field lands in.
- **D7: queue-029 batch reconciliation (2026-10-05).** Item 216's author
  found two holes in the first fence, and both are now closed:
  - count pins written as bare integers, in `test_131`, `test_132` and
    `test_136`;
  - the catalogue path-set digest in `tests/corpus/119_pre_119_digests.json`.

  The token greps could not see either, because neither names a moved path.
  So a fourth, count-and-digest pass was added (Authorised paths), and fence
  rule (b) was widened to any path count. Rule (d) (then lettered (e)) and step 6's digest
  regeneration are new.
- **D8 (2026-10-05, batch review): the catalogue lists what a real report
  carries.** The 20 report-only `reference_delta` rows are brought into the
  catalogue by step 5: the reference-delta driver yields one placeholder per
  `INGESTED_FEATURES` name, not just `physical_volume_mm3`.
  - **Why this and not checking those rows against the report.** It is the
    least machinery under which item 216's AC1 can be true over all 165
    rows. That check is the catalogue's path set equal to the table's
    `kept`/`moved` new paths. Checking the 20 rows against AC1's report
    instead would leave them permanently outside the catalogue, so item
    216's equality could never hold.
  - **What it costs.** A loop over an existing constant, plus 20 doc rows.
    The catalogue then answers criterion 2 for every leaf a report built
    against the bundled reference carries.
  - **For item 217.** Criterion 2's addressability half can be read off the
    catalogue against the table, and the identity half off this item's AC1.
- **D9 (2026-10-05, batch review): item 214's AC1 now holds a frozen
  literal.** The maintainer reshaped it: it compares the table's old paths
  with a frozen `(165, sha256)` pair, so this item's regeneration does not
  falsify it. The first draft of this spec retired that test, and those
  parts are withdrawn: the retirement step, the fence kind that allowed it,
  `tests/test_214_feature_taxonomy_design.py` on May change, the assumption
  about the cross-spec pin error, and the successor paragraph. Fence rule (b)
  was reworded per the cross-spec review, because the first wording could
  not express:
  - a survivor changing evidence bucket (`test_137`'s exhaustive table,
    `test_136`'s `()` bucket);
  - a cross-block move raising a record's leaf count (`test_103`);
  - newly catalogued rows.
- **D10 (step 0 record, 2026-10-06, base `00fe6f5`).** Read against the
  signed note as of `2364df4`, with gate-0080 approved the same day.
  - **Merged rows and their survivors:** as in A3's re-check. Nine identity
    copies merge onto `per_label.{label}.label` (five) and
    `per_label.{label}.level_name` (four).
  - **Step 1 also covers the curvature and monotonic serialisers** in
    `feature_report.py`. The three tangent arrays and `u_values` leave
    `stage3` and become per-label scalars, in the orders A2's re-check
    gives. `inter_tangent_angles_deg[]` and the case-level scalars stay
    where they are, for item 216.
  - **Step 3 applies (Option A, maintainer decision at the gate).**
    - `run_qc_with_intensity` builds `per_label.{label}.intensity.*` into
      the features block. That is the record that is persisted and
      embedded as the report's `features`.
    - The image-features element of its 5-tuple, and the report's
      top-level `image_features` key, keep only the four case-level fields
      (`available`, `backend`, `image_features_version`,
      `radiomics_available`). Those are item 216's rows. Item 216 moves
      them to `case.intensity` and removes the key.
    - The tuple's arity and order are unchanged (D6). `pipeline.py` and
      `report.py` are edited under their existing May-change bullets.
    - The rule record and `compute_intensity_reference_delta` read
      per-label intensity from the features block.
  - **Blocks that change shape (step 4).**
    - The Stage-3-bearing features block: `FEATURES_VERSION_STAGE3`
      `"0.2"` → `"0.3"`.
    - `image_features` loses `per_label`: `IMAGE_FEATURES_VERSION` `"1.0"`
      → `"1.1"`.
    - `reference_delta.{label}` loses `label` and `level_name`:
      `REFERENCE_DELTA_VERSION` `"1.0"` → `"1.1"`.
    - **The base `FEATURES_VERSION` is bumped by this item, `"0.1"` →
      `"0.2"`.** The table moves the `image_features` per-label fields into
      `per_label.{label}`, and Option A persists them, so a block without
      Stage 3 that is built with `--intensity` changes shape. This is step
      4's first case. Item 216's step 7 reads this record and does not bump
      it again. The new `"0.2"` reuses the pre-215 Stage-3 value. Item
      216's spec records that collision as Left open, on the ground that no
      in-repo reader branches on the value, and this item follows the same
      batch rule.
  - **`catalogue.normalise_leaf_path`** needs no placeholder extension,
    because the note introduces none. Rule (d) is unchanged, because
    `reference_delta` stays keyed by `{label}`.
- **D11 (implementation record, 2026-10-06).** What was built, and the
  calls the spec did not pin.
  - **Where the migration happens.** `feature_report.build_features_block`
    distributes the extractors' unchanged converters' output: each Stage 3
    per-label dataclass lands in its label's `curve` / `orientation` /
    `neighbourhood` block with the `label` / `level_name` copies stripped
    (`_without_identity`). The `*_to_dict` converters themselves keep their
    legacy shape (D4), so their direct tests need no edit. A Stage 3
    dataclass whose label has no Stage 2 map still gets a `per_label` entry,
    its identity taken from the dataclass; only a label in neither source
    raises `KeyError`, as before.
  - **The four Deviation-5 arrays.** The three tangent arrays are zipped with
    `sorted(all_labels)` (ascending integer label, the order they were
    computed in). `u_values` is zipped with the labels sorted by
    `(CANONICAL_ORDER rank, label)`, derived in the serialiser from each
    entry's `level_name` -- the same key `pipeline.py` sorts
    `anatomical_centroids` by, so the two cannot disagree. The
    `path-u-mapped-in-anatomical-order` case passes with label 28 first.
  - **Intensity (Option A).** `feature_report.build_intensity_entries`
    builds `{key: {first_order, extended}}`; `add_intensity_kind` returns a
    copy of a features block with them attached; `pipeline.run_qc_with_intensity`
    attaches them to the block it returns. `build_image_features_block` now
    takes only the four case-level fields (`backend`, `radiomics_available`,
    `available`, `image_features_version`); its former `intensity` and
    `extended` parameters are gone. `reference.delta.compute_intensity_reference_delta`
    keeps its signature: `image_features` is now only the `available` gate,
    and the statistics are read from the block's `per_label[*].intensity`.
  - **Report schema.** `labelFeatures` requires only `label` and
    `level_name`; every kind block is optional because each has its own
    source (the Stage 3 kinds and a stage3-only hand-built block would
    otherwise be unrepresentable). `stage3OffsetEntry` (now the `curve`
    kind) keeps the six offset fields required and gains optional `path_u`;
    `stage3OrientationEntry` keeps no required key and gains the three
    `tangent_*` scalars. The definition names are kept so the tests that
    read them (test_121, test_123, test_131) re-point only their assertions.
    `stage3Curvature` loses the three arrays from `required` and
    `properties`, `stage3MonotonicConsistency` loses `u_values`,
    `referenceLabelDelta` loses `label` / `level_name`, and `imageFeatures`
    loses `per_label`.
  - **Rule declarations the grep could not predict.** Once the identity keys
    are unique last segments, the catalogue's static scan attributes
    `per_label.{label}.label` and `per_label.{label}.level_name` to every
    rule module that names `"label"` / `"level_name"`, and
    `path_classification_conflicts()` reports each undeclared pair. So
    `heuristics/border.py` (adds `per_label.{label}.label`, bookkeeping) and
    `heuristics/coverage.py` (adds `per_label.{label}.level_name`,
    bookkeeping) had to be edited, and **neither is on May change**: see
    "Hand-backs" below. The same ambiguity runs the other way for the 20
    report-only rows: five features now share `percentile_rank`, `value` and
    `robust_z` as last segments, so `physical_volume_mm3`'s `percentile_rank`
    and `value` lose their static attribution (`reference_delta` and
    `intensity_reference_delta` drop those declarations) and `robust_z` is
    declared for all five features (`reference_delta`, observed).
  - **Docs rows.** `FEATURE_DOCS` and `STATUS_OVERRIDES` keys were renamed
    mechanically from the table: a moved row keeps its prose and its
    `(status, rationale)` verbatim; a merged row's entries were deleted; the
    20 report-only rows copy their `physical_volume_mm3` counterpart's
    entries (key only changed). `features_version`'s doc row still reads
    `"0.1"` / `"0.2"`: that row is item 216's (Moved by 216), and the code
    value is bumped here per D10.
  - **Observed in the generated artifacts.** Validation 3's row-by-row
    comparison holds for `status` and `observed` over every kept and moved
    row; only `computation` prose naming a moved path changed (six rows).
    The human report is byte-identical to the claim base on `clean_control`
    and `displace` (compared from a tree extracted at the base commit). The
    findings of every corpus case, geometric and intensity, with the default
    and production references, are identical to the base.
  - **Counts.** The catalogue goes 145 -> 156 (-9 merged, +20 report-only);
    `clean_control`'s record 101 -> 95 (-6 merged, no other change);
    `observed_summary` `placeholder` 12 -> 26 and `varies` 84 -> 81;
    `mode_evidence` buckets as item 137's table records. The path-set digest
    is `64bde66b...4fd4620`.
  - **Hand-backs (not authorised by this spec).**
    1. `src/segfacet/heuristics/border.py` and
       `src/segfacet/heuristics/coverage.py` (one `ConsumedPath` each, see
       above). `aide scope 215` exits 1 on exactly these two.
    2. `docs/aide/golden_evidence.generated.json`: Authorised paths predicted
       it byte-identical, and step 6 makes a difference a hand-back. It is
       not: every case's `total_leaf_paths` goes 101 -> 95 and
       `unwired_leaf_paths` 30 -> 28 (it counts record leaf paths, which the
       six merged copies leave). `tests/test_134_decision_table_evidence_companion.py`
       AC4 compares it to a fresh build. It is regenerated on this branch so
       the tree is consistent, and needs authorising.
  - **Tests reconciled, by node id, old -> new** (fence (a), (b), (c);
    no assertion's expected value, tolerance, name or skip state changed;
    pytest was not run by the builder):
    - 022: every `block["stage3"]["per_label_offsets" | "per_label_orientations"]`
      read -> `_kind_entries(block, "curve" | "orientation")` (a helper that
      reads identity from the `per_label` entry); `test_ac2_all_stage3_subkeys_present`,
      `test_ac2_curvature_has_required_keys`, `test_ac2_monotonic_consistency_has_required_keys`
      now check the per-label kinds for the moved keys; `test_ac2_u_values_length_in_monotonic_consistency`
      and `test_adv_all_u_values_in_unit_interval` read `curve.path_u`;
      `test_adv_only_spline_offsets_supplied` and `test_adv_schema_rejects_missing_offset_mm`
      re-pointed; `test_ac9_stage3_key_order_and_key_set_explicit` drops the
      two lists from the stage3 key set; `test_ac9_features_version_is_02_when_stage3_present`
      `"0.2"` -> `"0.3"`, `test_ac9_features_version_is_01_when_stage3_absent`
      `"0.1"` -> `"0.2"`, `test_ac9_features_version_in_serialised_report`
      `"0.2"` -> `"0.3"`.
    - 033, 035, 120, 123: hand-built records place each offset at
      `per_label.{label}.curve` (`_make_record`, `_mode1_record`,
      `_gt_pass_record`, `_mislabel_record`, `_offset_record`); the
      `per_label_offsets` None / `{}` placeholders of
      `test_ac18_per_label_offsets_none_no_raise` and
      `test_ac18_per_label_offsets_non_list_no_raise` become a `curve`
      of `None` / `[]`; the `u_values` key is removed from hand-built
      monotonic blocks. 039, 044, 125, 129, 130, 145, 151, 189, 212: live
      offset reads -> `per_label[*].curve`. 123's `_well_formed_offset_entry_instance`
      drops `label` / `level_name`; its `per_label_offsets[].is_terminal`
      path strings are re-pointed.
    - 046, 047, 064 (rule), 064 (compute), 081, 062, 061, 065 (three
      files): hand-built delta entries lose `label` / `level_name`
      (`_block`, `_record`, `_features_block`), identity moves to the
      record's `per_label`; per-label intensity moves to `per_label[*].intensity`
      (`_scored`, `_record`, `_corpus_record`, `_with_intensity`); 061's
      `build_image_features_block({...})` calls are re-pointed to
      `build_intensity_entries` / the case-level call.
    - 051: `_block` places offsets at `curve`; version literals `"0.2"`/`"0.1"`
      -> `"0.3"`/`"0.2"`.
    - 110, 115: `_neighbourhood_entries` helper; the five/four expected new
      leaf paths drop the two merged identity copies and move under
      `per_label.{label}.neighbourhood`.
    - 121, 122, 131, 132, 143: the per-label arrays are read as
      `per_label[*].orientation.tangent_*` (ascending label) and
      `per_label[*].curve.path_u` (anatomical order); `test_ac11_schema_descriptions_state_convention`
      now parametrised by (definition, key); `test_ac16_schema_defines_all_five_new_keys`
      checks the two arrays on `stage3OrientationEntry`.
    - 103, 124, 131, 132, 136, 137, 148: count and digest pins moved, each
      with a dated comment whose arithmetic closes: 103 `101 -> 95`
      (`test_ac4_clean_control_leaf_paths`); 124 / 131 / 132 / 136 / 137 / 148
      `145 -> 156`; 136 `stayed_empty` `89 -> 103`; 137's `mode_evidence`
      table `()` `89 -> 103`, `("rule_bookkeeping",)` `10 -> 8`,
      `("rule_mode_less", "rule_bookkeeping")` `9 -> 11`,
      `("rule_mode_less", "rule_bookkeeping", "rule_not_read")` `8 -> 5`;
      132's `_PRE_ITEM_OBSERVED_SUMMARY` `placeholder` `12 -> 26`, `varies`
      `84 -> 81`. `test_ac11_three_bookkeeping_paths_empty_signal_path_still_shows`
      (148) re-points `reference_delta.{label}.label` to its survivor and
      `.level_name` to `reference_delta.{label}.available` (the level name's
      survivor carries `sequence`'s signal modes).
    - 104, 106, 119, 138, 149, 154, 191: path strings re-pointed.
    - `tests/report_format_fixture.py` and `tests/golden/report_format_contract.json`,
      `tests/corpus/119_pre_119_digests.json`: regenerated per steps 6.
- **Left open:** whether `per_label.{label}.*` rows move. A7 assumes not.
  *Settled at claim (2026-10-06):* none moves (A7's re-check).
  If the signed table moves any, step 0 widens the fence, rather than this
  spec pre-authorising every canonical-container reader on speculation.
- **Left open:** whether the transient `intensity_reference_delta` block
  belongs in the catalogue. It is uncatalogued today (A6), and the taxonomy
  stage does not add rows.
