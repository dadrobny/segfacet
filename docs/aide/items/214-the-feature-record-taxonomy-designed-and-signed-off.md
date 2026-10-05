<!-- aide-template: item 3 -->
# Item 214 — The feature-record taxonomy, designed and signed off

> **Created:** 2026-10-05 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 27 — Feature Schema Taxonomy & Coordinate System
> **Queue:** [`../queue/queue-029.md`](../queue/queue-029.md) · Item 214
> **Objectives:** G8
> **Suggested branch:** `aide/214-the-feature-record-taxonomy`

---

## Description

Roadmap Stage 27 D1: the feature record's structure is designed and written
down as **one short design note**, and a person signs it off before any field
moves. The note is the deliverable. No record shape, extractor, rule, report
or generated artifact changes here. Items 215 and 216 migrate the record, and
item 217 attests the stage.

The note is **`docs/feature-taxonomy.md`**, a sibling of
`docs/spinal-curve-model.md` (item 118), which is the precedent for a design
decision put to a human gate. It holds:

1. **The structure.** What the record's top-level organisation becomes, and
   the axes it is organised by.
2. **Its rationale.**
3. **The alternatives considered.**
4. **Every deviation from the maintainer's starting proposal, with its
   reason.** The starting proposal is scope (`per_label` /
   `per_neighbour-pair` / `per_case`) × kind (shape-geometry / intensity /
   label-identity / …). A grouping that falls out of which extractor module
   computed a field is not acceptable (roadmap Stage 27, Goal).
5. **Six answers** (pinned headings below):
   - the four known instances the roadmap names;
   - the two questions the open insight inbox raises: where per-component
     features live, and which path owns adjacent-pair spacing.

   An answer may be "left as is, for this reason".
6. **The mapping table.** One row per pre-migration leaf path, giving its new
   path and the migration item (215 or 216) that owns it. This is what items
   215, 216 and 217 read (shape pinned below). There are **165** pre-migration
   leaf paths, from two sources (A1):
   - the feature catalogue's 145 paths;
   - 20 `reference_delta` paths that a real report carries and the catalogue
     does not list (A4).

   Roadmap criterion 2's "every feature is addressable" covers every leaf of
   a real report, not only the catalogue's (maintainer decision, 2026-10-05).

The item's **human gate** over the note (roadmap Stage 27 D1, criterion 1)
is already raised by the time the item is claimed. Its row was added to
`progress.md`'s `## Human gates` table in the same commit as this spec, and
A7 quotes it verbatim. The builder adds nothing to `progress.md`. The gate's
reach is items 215, 216 and 217, so `aide claim` holds the migration until a
person approves. Item 214 itself is not held by it: the note has to exist
before anyone can sign it.

**Re-plan at the gate (queue 029).** Items 215 and 216 are cut along the
starting proposal's scope axis: per-label fields first, then neighbour-pair
and case-level fields. If the signed design departs from that axis, both are
re-cut at this gate to match it, as queue 027 was re-cut at `gate-51da`. A
decline keeps blocking all three. The change the maintainer names is
re-planned as new work, and nothing in 215–217 starts.

### The note's pinned shape (what consumers read)

These are the only parts of the note a test reads. Everything else is prose
for the maintainer.

**Answers.** A `## Answers` section holding exactly these six `###` headings,
verbatim, each once:

| # | Heading | Source |
|---|---------|--------|
| 1 | `### Identity fields stored in several containers` | known instance |
| 2 | `### stage3 and image_features beside per_label` | known instance |
| 3 | `### Image-axis-relative shape features` | known instance |
| 4 | `### The reference-delta's feature selection` | known instance |
| 5 | `### Where per-component features live` | insights `2026-10-02-3eba`, `2026-09-30-88a5` |
| 6 | `### Which path owns adjacent-pair spacing` | insight `2026-09-22-c151` |

Under each heading, before the next heading of any level, exactly one line
begins with `**Answer:**` and carries non-whitespace text after the marker.
That line is the verdict in one sentence. The reasoning follows it as
ordinary prose.

**Mapping table.** A `## Mapping table` section, appearing once. It holds a
single Markdown table with this header row, verbatim:

```
| Old path | New path | Change | Moved by |
```

It is followed by the separator row and then one data row per pre-migration
leaf path (165 rows), in this shape:

```
| `<old path>` | `<new path>` | <kept | moved | merged> | <215 | 216> |
```

- **Old path.** The path exactly as `segfacet.catalogue.iter_leaf_paths`
  yields it (A1):
  - For the 145 catalogue paths, this is the catalogue's `path` string,
    verbatim.
  - For the 20 report-only paths, the feature-name segment is the literal
    feature name, for example
    `reference_delta.{label}.features.extent_x_mm.value`. That is the form
    the walker produces, so the Old-path notation needs no new placeholder.
- **New path.** The same notation the catalogue uses, so that items 215 and
  216 can compare it directly with their regenerated catalogue: `{label}` for
  a per-label key, `[]` for a list element, `{radiomic}` for the PyRadiomics
  family (`segfacet.catalogue.normalise_leaf_path`). Any new placeholder
  segment, such as one for a neighbour pair or a reference-delta feature
  name, is defined in the note's structure section. The definition names the
  record key it stands for, because the migration item that introduces it
  must teach `normalise_leaf_path` to produce it.
- **Change.**
  - `kept`: the path does not move.
  - `moved`: the field moves to a new path.
  - `merged`: the field's own path is dropped, and what it measured is stored
    at its new path, which is some other row's new path. It has two licensed
    cases and no others:
    - **A stored copy of the same value.** These are the identity duplicates
      (A2).
    - **The adjacent-pair spacing collapse.** The maintainer decided this on
      2026-10-05 (A6). The dropped array is the same quantity measured in a
      different order, so its values are **not** equal to the survivor's
      wherever the two orders disagree.

    A `merged` row whose values differ from its target's, other than the
    spacing row, is a deviation the note must record with its reason in
    `## Deviations from the starting proposal`.
- **Moved by.** `215` or `216`, on every row, `kept` rows included. The
  migration items therefore partition the table between them. For a `kept`
  row, the owner is the item whose regenerated catalogue verifies that the
  path is still produced, and which re-points that area's readers. The 20
  report-only `reference_delta` rows are per-label, like the rest of
  `reference_delta.{label}`, so they are owned by `215`.

No row deletes a field (A5). The table has no other columns and no rows
outside this shape.

### What this item is NOT

- **Not the decision.** No agent runs `aide gate approve` or
  `aide gate decline`.
- **Not the migration.** Nothing under `src/segfacet/` changes, the catalogue
  is not regenerated, and the report schema is not touched.
- **Not a vertebra coordinate system, and not a generalised reference-delta.**
  If the note concludes the taxonomy cannot be stated without one, it says so.
  Building it is then re-planned at the gate (queue 029, Build posture).
- **Not work on the three design-input insights.** `2026-10-02-3eba`,
  `2026-09-30-88a5` and `2026-09-22-c151` are answered in the note, and none
  is ticked or acted on.
- **Not an attestation.** No criterion carries a *(closes Stage 27 criterion
  M)* annotation, so none closes a stage criterion. Item 217 attests
  criterion 1 from the gate row.

## Acceptance Criteria

"The table" means the rows `tests/feature_taxonomy_mapping.py::read_mapping`
returns from `docs/feature-taxonomy.md` (Testing Strategy). Only AC8 asserts
what the design decides, and what it asserts is the maintainer's own
2026-10-05 decision (A6). The rest of the design's adequacy is the gate's to
judge.

- [ ] **AC1: the table's old paths are exactly the pre-migration path set.**
      Let `old` be the sorted list of the table's old paths. The pair
      `(len(old), sha256("\n".join(old).encode("utf-8")).hexdigest())`
      equals the frozen literal
      `(165, "488221662105adf220e4b35dbc541acda4b21f1f2ed994ac0098bf34bc067667")`.
      That literal is held in `tests/test_214_feature_taxonomy_design.py`.
      It is computed over a list, not a set, so a path mapped twice changes
      both values.
      The literal is a frozen record of the pre-migration set. It is read
      from no file the migration changes, so the criterion stays true after
      items 215 and 216 (maintainer decision, 2026-10-05; A1). That it equals
      the live sources at this item's merge is the validator's check
      (Validation, step 1).
- [ ] **AC2: every new path that stores a value is unique.** Among rows whose
      Change is `kept` or `moved`, no two have the same new path.
- [ ] **AC3: every merged row lands on a stored field.** Each `merged` row's
      new path is among the new paths of the `kept` and `moved` rows.
- [ ] **AC4: a row is kept exactly when its path does not change.** For every
      row, `Change == "kept"` equals `new path == old path`.
- [ ] **AC5: each of the four known instances has a recorded answer.** In
      `docs/feature-taxonomy.md`'s `## Answers` section, each of headings 1–4
      (Description, pinned table) occurs exactly once, with exactly one
      non-empty `**Answer:**` line before the next heading.
- [ ] **AC6: each of the two inbox questions has a recorded answer.** The
      same predicate as AC5, for headings 5 and 6.
- [ ] **AC7: the sign-off gate is raised over items 215, 216 and 217.**
      `docs/aide/progress.md` is parsed through the CLI's `human_gates()`.
      Exactly one `## Human gates` row's Gate cell contains
      `Stage 27 feature-record taxonomy sign-off`. That gate's parsed
      `blocks` equals `[215, 216, 217]`, its `stage` is `None` and its
      `blocks_all` is `False`.
- [ ] **AC8: one stored spacing array is merged into the other.** Take the
      two rows whose old paths are `relationships.neighbour_spacings_mm[]`
      and `stage3.spacing_consistency.spacings_mm[]`. Exactly one of them is
      `merged`, and its new path equals the other row's new path. The other
      row, the survivor, is therefore `kept` or `moved`. This rules out
      both arrays merging onto a third path.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

Everything below was measured on 2026-10-05 at `05eef1d` (`aide/queue-029`).
The second-round figures (the 20 report-only paths and the frozen AC1 value)
were measured on `f5c79df`. Between those two commits only `insights.md`
changed, and `src/` and the catalogue were untouched.

The orchestrator ran clarify as interactive. The maintainer answered three
questions on 2026-10-05, and made four further decisions the same day after
the cross-spec review of queue 029. A1, A3, A4, A5 and A6 record them as
**maintainer decisions**, not defaults. None of A1–A6 pins an unbuilt
dependency's interface.

- **A1 (measured 2026-10-05):** the catalogue holds **145** entries with 145
  distinct paths, all of `origin` `record`. Three of them are container
  entries realised as leaves only on a degenerate record: `per_label`,
  `relationships` and `overlaps[]`. They get rows like every other path. The
  roadmap's "111-entry" figure is item 106's count from Stage 19.
  By prefix:

  | Prefix | Paths |
  |--------|-------|
  | `per_label.{label}.*` | 44 |
  | `stage3.per_label_neighbourhood[]` | 17 |
  | `image_features.per_label.*` | 17 |
  | `reference_delta.*` | 16 |
  | `stage3.per_label_offsets[]` | 9 |
  | `stage3.curvature` | 8 |
  | `stage3.per_label_orientations[]` | 8 |
  | `relationships` | 6 |
  | `overlaps` | 6 |
  | `stage3.spacing_consistency` | 5 |
  | `stage3.monotonic_consistency` | 3 |
  | `image_features` (case level) | 4 |
  | `features_version` | 1 |
  | `per_label` | 1 |

  **The pre-migration path set is 165 paths, and AC1 freezes it
  (maintainer decision, 2026-10-05).** It is the 145 catalogue paths plus
  the 20 report-only `reference_delta` paths that A4 enumerates. Each source
  as measured on `f5c79df`:
  - **The 145:** the `path` of every `groups[*].entries[*]` entry in
    `docs/aide/feature_catalogue.generated.json`.
  - **The 20:** `segfacet.catalogue.iter_leaf_paths({"reference_delta":
    reference_delta_to_dict(compute_reference_delta(record, ref))})`, minus
    the 145. Here `record` is `extract_feature_record` over
    `build_clean_spine()` under `bundled_default_config()`, and `ref` is
    `reference.artifact.bundled_production_reference()`.

  The frozen pair `(165, "4882216621…bc067667")`, in full in AC1, is
  `len` and SHA-256 over `"\n".join(sorted(...))` of their union. For
  comparison, the catalogue's 145 alone hash to
  `477a4be8e34d7f669ec1bdb49cc5386ca21096bf76f53c7ba1d070e49ce77798`.

  The value is a literal, and deliberately not read from
  `tests/corpus/119_pre_119_digests.json` or the catalogue. Item 215
  rewrites both, and AC1 is meant to stay true after the migration.
- **A2 (measured 2026-10-05): identity is duplicated in five containers, not
  four.** The four the queue names exist as named:
  - `stage3.per_label_offsets[].{label, level_name}`;
  - `stage3.per_label_orientations[].{label, level_name}`;
  - `image_features.per_label.{label}.label`, which has no `level_name`;
  - `reference_delta.{label}.{label, level_name}`.

  A fifth holds the same pair: `stage3.per_label_neighbourhood[].{label,
  level_name}`, which also carries `window_labels[]`. The canonical copy is
  `per_label.{label}.{label, level_name}`. Separately, neighbour-pair
  identity is stored as both integer and name: `overlaps[].{label_a,
  label_b, name_a, name_b}`. The note's identity answer covers all of these.
- **A3 (maintainer decision, 2026-10-05): `stage3.per_label_neighbourhood[]`
  is moved by item 215.** Every row whose old path starts with it carries
  Moved by `215`. Its entries are per-label, one per focal vertebra, and
  carry duplicated identity. So item 215's testable, "no identity field
  stored more than once per label", cannot hold while the container stands.
  Neither the queue's item 215 text nor its item 216 text named this
  container.
- **A4 (measured 2026-10-05): the reference-delta is not hardcoded to
  `physical_volume_mm3`. Only the catalogue's view of it is.** Two things
  are true:
  - **Where the single feature comes from.** `catalogue.iter_driver_records`
    realises the block from one placeholder `FeatureDelta` for
    `physical_volume_mm3`. That is why the catalogue lists only
    `reference_delta.{label}.features.physical_volume_mm3.*`.
  - **What the code scores.** `reference.delta.compute_reference_delta`
    scores every feature the loaded reference tracks
    (`tuple(sorted(reference.features))`). Those features come from three
    fixed vocabularies: `INGESTED_FEATURES` (`physical_volume_mm3`, the three
    extents and `spline_offset_mm`), `INGESTED_INTENSITY_FEATURES` and
    `INGESTED_MORPHOLOGY_FEATURES` (`largest_component_fraction`,
    `component_count`, `eigenvalue_ratio`). Each vocabulary is read through
    its own hand-coded path (`_case_features_for_label`,
    `_intensity_case_values`, `_morphology_case_values`).

  So the limitation known instance 4 points at is real, but it is a fixed
  vocabulary with per-family read paths, not a single feature. The serialised
  key `features.<feature name>` already varies by feature. The note answers
  the real limitation, and its new path for those rows uses a
  feature-name placeholder only if the structure section defines one.

  **Measured on `f5c79df`: a report built against the bundled reference
  carries 20 `reference_delta` leaf paths the catalogue does not list.**
  - **What the reference tracks.** The bundled production reference
    (`reference_verse_v1.json`) tracks 21 features: the five
    `INGESTED_FEATURES`, 13 `intensity_*` features and the three morphology
    features.
  - **What gets scored.** `compute_reference_delta` scores only those it
    finds case values for. `_case_features_for_label` supplies the geometry
    scalars and `spline_offset_mm`, so only those five are scored.
  - **The 20 paths.** Four of those five features are absent from the
    catalogue, and each carries five statistics. Every path has the form
    `reference_delta.{label}.features.<f>.<s>`, where:
    - `<f>` is one of `extent_x_mm`, `extent_y_mm`, `extent_z_mm` and
      `spline_offset_mm`;
    - `<s>` is one of `out_of_range`, `percentile_rank`, `robust_z`, `value`
      and `z_score`.

  These 20 get rows, written with the literal feature name, and are owned by
  item 215 (maintainer decision, 2026-10-05: criterion 2 covers every leaf
  of a real report).

  **Two blocks are out of the table, each for a stated reason.**
  - **`intensity_reference_delta` is out.** It shares
    `reference_delta_to_dict`, but it is a transient rule-record key that
    `run_qc_with_intensity` attaches only for the `intensity_reference_delta`
    rule. `cli.py` writes only `reference_delta` into a report, and
    `report.py` and `report_schema_v0.json` have no key for it. So no report
    leaf of it exists, and none of its paths is in the catalogue. Answer 4
    must still say where the block sits structurally. It carries `label` and
    `level_name` per label, so the identity answer (Answer 1) names it too.
    It gets no rows.
  - **The morphology delta is out.** `compute_morphology_reference_delta` has
    no caller in the pipeline, so no record carries it, and it gets no rows.
- **A5 (maintainer decision, 2026-10-05): no row deletes a field.** The catalogue's
  `retire` status marks eight paths: `component_volumes_mm3[]`,
  `fragmentation_index`, `centroid_voxel[]`, `offset_voxel`,
  `small_fragments[]`, `image_features_version`, `reference_delta_version`
  and `reference_schema_version`. That status is item 106's steering verdict,
  not an authorisation to drop fields in this stage, and roadmap criterion 3
  forbids rule-behaviour changes. Each of those paths gets a `kept` or
  `moved` row. None of them is `merged`, because `merged` is only for the two
  cases the Change definition licenses.
- **A6 (measured 2026-10-05; maintainer decision 2026-10-05): adjacent-pair
  spacing is computed three times, and the two stored arrays collapse into
  one.**
  - `relationships.neighbour_spacings_mm[]` is in canonical-rank order over
    recognised level names only (`features/relationships.py`, via
    `_CANONICAL_RANK`).
  - `stage3.spacing_consistency.spacings_mm[]` is in ascending-integer label
    order over every label (`pipeline.extract_feature_record` passes
    `ordered_centroids` to `compute_spacing_consistency`).
  - The pipeline computes a third, per-element copy that feeds
    `stage3.per_label_neighbourhood[].stats.spacing_mm.*`.

  The two stored arrays diverge wherever integer order and anatomical order
  disagree: TPTBox `T13` is 28 and `Cocc` is 27. Their observed catalogue
  ranges differ (32.6952–134.161 mm against 32.6952–66.3769 mm). Only
  `spacings_mm[]` is read by a rule (`fused_label`), and insight
  `2026-09-22-c151` names it as the signal a future mode-6 rule reads.

  **The decision.** The two stored arrays collapse into one. The maintainer's
  reason, verbatim: *"the integer-label order is anatomically meaningless"*.
  Two further maintainer decisions, also 2026-10-05, fix what survives:
  - **Label set and order.** The survivor covers **every label**, in
    anatomical order, with unrecognised labels kept and placed last. This is
    the item-198 ordering the pipeline already builds as
    `anatomical_centroids`. It is not `relationships`' ordering, which drops
    level names outside the canonical vocabulary.
  - **Presence, as today.** The survivor exists on every record that has
    `relationships.neighbour_spacings_mm` today, which is every record with
    at least one label. The aim is that no existing test's asserted presence
    changes. It is `[]` only below two labels.
    - On coincident-centroid records, where Stage 3 is unavailable, it is
      computed exactly as `relationships.neighbour_spacings_mm` is today,
      over the decided label set and order.
    - Only the derived statistics (`mean_spacing_mm`, `cv_spacing`,
      `deviations_mm[]`, `outlier_pairs[]`) stay Stage-3-only.
    - Corrected 2026-10-05: an earlier wording made the survivor `[]` on
      coincident-centroid records. That was never authorised.

  The note therefore does four things:
  - It names the single surviving path, its order, its label set and the
    records it is present on, as decided above.
  - It records the collapse in `## Deviations from the starting proposal`.
    The gate signs it there.
  - Its table marks the other array's row `merged` onto the survivor's new
    path. The survivor's own row is `moved` or `kept` (AC8). Both rows carry
    Moved by `216`, which owns neighbour-pair fields.
  - It says, for each consumer below, what that consumer reads afterwards.

  **Item 216 carries a deliberate change to what is measured.** Wherever
  integer order and anatomical order disagreed, the surviving array's values,
  pairs and length differ from what `spacings_mm[]` held. This is the retune
  "explicitly authorised" that roadmap criterion 3 admits, and item 217
  attests it as such. These are the consumers of
  `stage3.spacing_consistency.*` verified on `05eef1d`:
  - **`heuristics/fused_label.py`** reads `spacings_mm[]` (`FusedLabelRule.evaluate`,
    the `sc.get("spacings_mm")` read). It pairs `spacings_mm[i]` with the i-th
    and (i+1)-th label in ascending-integer order. It is absence-tolerant
    when the spacing count is not `len(per_label) - 1`. The survivor covers
    every label, so the count still matches. What changes is the pairing:
    the rule must pair each spacing with the anatomically adjacent labels,
    not the integer-adjacent ones.
  - **The in-record statistics `compute_spacing_consistency` derives from the
    same array** (`features/consistency.py`): `mean_spacing_mm`,
    `cv_spacing`, `deviations_mm[]` and `outlier_pairs[]`. Each changes value
    wherever the pairs change.
  - **`failure_modes.py`** names `stage3.spacing_consistency.spacings_mm[]`
    as a signal or candidate path in several mode entries. These path
    strings are re-pointed, and the specification artifacts regenerated.
  - **`report_schema_v0.json`, `feature_docs.py` (`FEATURE_DOCS`, the owner
    rows), the `default_config.yaml` comment and the
    `synth/coverage_border_overlap.py` docstring** each name the path.

  `relationships.neighbour_spacings_mm[]` itself has one reader in `src/`:
  `human_report.render_feature_table` renders it. Its only caller in `src/`
  is the catalogue's consumer trace (`catalogue._mechanism_d_consumers`), so
  nothing in `segfacet_report.txt` shows the array. Corrected 2026-10-05: an
  earlier wording of this spec said `human_report` renders it, which was
  true only of that uncalled function. The array is also described in
  `report_schema_v0.json`.

  **The third, per-element copy is not one of the two stored arrays, so the
  collapse does not reach it by itself.** The pipeline computes it from
  `ordered_centroids`, in ascending-integer order, and stores it only through
  `stage3.per_label_neighbourhood[].stats.spacing_mm.{mean, median, std,
  z_score}`. All four are `unwired`: no rule reads them. The maintainer's
  reason indicts its order too. So Answer 6 says whether it is re-derived
  from the surviving anatomical-order array, or left as is with a reason.
  - **If re-derived:** that is a further value change, to unwired fields
    only, recorded in Deviations. It lands in item 216, because it depends on
    the survivor, even though the container's paths are moved by item 215
    (A3).
  - **If left as is:** its paths move with the container and its values do
    not change.
- **A7 (engine 2.35.0): how the gate is raised and read.**
  - **The row.** The gate is the row below, in `progress.md`'s
    `## Human gates` table. It is four cells wide with no `|` inside a cell.
    The orchestrator added it by hand in the same commit as this spec, so it
    exists before the item is claimed, and the builder adds nothing to
    `progress.md`. Resolving it is `aide gate approve|decline <gate-ID>
    --evidence "…"`, by a person only.
  - **The gate ID.** It is `gate-` plus a prefix of the SHA-256 of the
    whitespace-normalised Gate cell (`gate_hash`). Rewording the cell makes a
    different gate. So this spec selects the gate by the substring
    `Stage 27 feature-record taxonomy sign-off`, and cites no ID until
    `aide gate list` prints one.
  - **Which verbs read the table.** `aide claim` consults the table, through
    `_pick_item` and `gate_blocked_items`, and skips 215–217 while the gate
    is not `✅ Approved`. `aide merge` does not consult it.
  - **Substring collisions.** The substring collides with no selector an
    existing test uses: `Stage 32 selected-mode sign-off`,
    `Stage 30 failure-mode specification sign-off`, `spinal curve model`,
    `Stage 33 at-the-bar sign-off of modes`. The existing gate cell that
    mentions "failure-mode taxonomy" does not contain it.

  ```
  | Stage 27 feature-record taxonomy sign-off — after item 214 has merged, the maintainer reads the design note [`../feature-taxonomy.md`](../feature-taxonomy.md): the record's structure and its rationale, the alternatives considered, every deviation from the scope × kind starting proposal with its reason, the answers to the four known instances (identity fields in several containers, stage3 and image_features beside per_label, image-axis-relative shape features, the reference-delta's feature selection) and to the two inbox questions (where per-component features live, which path owns adjacent-pair spacing), and the mapping table from every feature-catalogue leaf path to its new path and owning migration item. Roadmap Stage 27 D1, criterion 1. Approval releases the per-label migration (item 215), the neighbour-pair and case-level migration (item 216) and the stage validation (item 217). If the signed design departs from the scope axis, items 215 and 216 are re-cut to match it at this gate, as queue 027 was re-cut at gate-51da | 215, 216, 217 | ⏳ Awaiting | — |
  ```

## Implementation Steps

The builder writes one Markdown file, and no code. This is a design, so read
before writing. The prose sections stay short (posture `prototype`, roadmap
2026-09-18 annotation): the mapping table is long by necessity, and nothing
else needs to be.

1. **Read the record as it is.** Sources:
   - the catalogue, `docs/aide/feature_catalogue.generated.{json,md}`;
   - one live record, from `segfacet.pipeline.extract_feature_record` over
     `segfacet.synth.clean_gt.build_clean_spine()`, in a scratch session
     only;
   - the module docstrings of `features/`, `feature_report.py`,
     `reference/delta.py` and `catalogue.normalise_leaf_path`;
   - item 106's steering review, for the `retune` verdicts this stage exists
     to absorb (roadmap Stage 27, Goal).

   A1–A6 are the facts already measured. Re-measure any the note quotes.
2. **Write `docs/feature-taxonomy.md`** with these sections, in this order:
   - a one-paragraph header stating that the note is proposed and pending the
     Stage 27 sign-off gate in `docs/aide/progress.md`'s Human gates table;
   - `## Structure`;
   - `## Rationale`;
   - `## Alternatives considered`;
   - `## Deviations from the starting proposal`;
   - `## Answers`;
   - `## Mapping table`.

   The note must not claim the gate is approved, resolved or signed off. That
   is true only once a person runs `aide gate approve`, and item 217 reads it
   from `progress.md`, not from the note.
3. **Write the six answers** under the pinned headings, each with its one
   `**Answer:**` line:
   - **Answer 1** covers all five identity containers and the pair identity
     in `overlaps[]` (A2).
   - **Answer 4** answers the limitation A4 measured, and says whether the
     taxonomy needs a generalised reference-delta to be stated.
   - **Answer 3** says whether it needs a vertebra coordinate system. Either
     "needed" becomes new work re-planned at the gate.
   - **Answer 5** places per-component data, and says whether the scope axis
     gains a per-component level. Today that data is parallel arrays in
     `component_sizes[]` order (`component_sizes[]`,
     `component_volumes_mm3[]`, `component_contacts[]`) beside label-level
     aggregates, all under `per_label.{label}.components`.
   - **Answer 4** also says where the transient `intensity_reference_delta`
     block sits (A4), even though it has no rows.
   - **Answer 6** follows the maintainer's collapse decision (A6). It must:
     - name the single surviving path;
     - state its order: anatomical, with unrecognised labels last, as decided;
     - state its label set: every label, as decided;
     - state the records it is present on, as decided:
       - every record with at least one label;
       - `[]` only below two labels;
       - on coincident-centroid records, computed as
         `relationships.neighbour_spacings_mm` is today;
     - state what `fused_label` and the four derived spacing statistics read
       afterwards;
     - say whether the per-element neighbourhood copy is re-derived from the
       survivor, or left as is, and give the reason either way.

     The collapse is also written into `## Deviations from the starting
     proposal`, quoting the maintainer's reason.
4. **Write the mapping table** in the pinned shape:
   - One row per pre-migration path, 165 rows in all (A1):
     - the 145 catalogue paths, in the catalogue's own row order, so the
       maintainer can read them beside `feature_catalogue.generated.md`;
     - then the 20 report-only `reference_delta` paths (A4), each written
       with its literal feature name and Moved by `215`.
   - Before committing, recompute AC1's pair over the drafted old paths, and
     check that it equals the frozen literal.
   - A throwaway script in the scratchpad may draft the rows. No generator is
     committed, and no module is added.
   - Moved by follows the scope axis. It is `215` for every
     `stage3.per_label_neighbourhood[]` row (A3), and `216` for both spacing
     rows (A6). Any other row that departs from the queue's split gets its
     reason in `## Deviations from the starting proposal`.
   - Mark `merged` only in the two licensed cases (Description, pinned
     shape): the identity copies, and the spacing array that does not
     survive (AC8).
   - Define any new placeholder segment in `## Structure` (Description,
     pinned shape).
5. **Do not touch** `src/segfacet/**`, any generated artifact,
   `docs/aide/insights.md` entries or `docs/aide/progress.md`. The gate row
   already exists (A7), and resolving it is a person's.
6. **Append to Decisions & Trade-offs** below: what the structure is, in two
   lines, and which axis departures (if any) would trigger the gate's re-cut
   of items 215 and 216.

## Authorised paths

**May change:**

- `docs/feature-taxonomy.md` — the design note, this item's deliverable.
- `tests/feature_taxonomy_mapping.py` — the one reader of the note's mapping table and answers, shared with items 215–217's tests.
- `tests/test_214_feature_taxonomy_design.py` — this item's test module.

**Asserts against:**

None. AC1 compares against a literal held in this item's own test module,
and reads no file the migration changes (maintainer decision, 2026-10-05).
The catalogue is checked against that literal once, at merge (Validation,
step 1). That check is diff-time, not a suite pin. `docs/aide/progress.md`
(AC7) is always authorised, so it is not listed.

## Testing Strategy

**Reader module: `tests/feature_taxonomy_mapping.py`**, not collected, and
imported as `from feature_taxonomy_mapping import …`, the way tests import
`synthetic`. It exposes:

- **`NOTE_PATH`**: the repo-relative `docs/feature-taxonomy.md`, resolved
  from the module's own location.
- **`read_mapping(text=None)`**: returns a list of `(old, new, change,
  moved_by)` tuples, with `moved_by` an `int`, in table order. It reads the
  note when `text` is `None`. It reads only lines between the `## Mapping
  table` heading and the next `## ` heading. Within them, every line starting
  with `|`, other than the pinned header and the separator, must match
  ``^\| `([^`]+)` \| `([^`]+)` \| (kept|moved|merged) \| (215|216) \|$``.
  A line that does not match raises `ValueError` naming the line, and so does
  a missing or repeated `## Mapping table` heading.
- **`answer_lines(heading, text=None)`**: returns the `**Answer:**` lines
  found under one `###` heading inside `## Answers`, up to the next heading
  of any level. It raises `ValueError` when the heading occurs other than
  exactly once.

This module is the interface items 215, 216 and 217 read the table through.
Its name and these three names are the pin.

**Module: `tests/test_214_feature_taxonomy_design.py`.** One test per AC
(AC1–AC8). AC7 loads `.aide/scripts/aide.py` in process and calls
`human_gates()`, following `tests/test_168_maintainer_sign_off.py`
(`_aide_module`, `_progress_lines`). It never uses a hand-written table
parser and never writes to `progress.md`.

**Adversarial cases, each with the failure mode it guards.** The test-writer
writes these and no others.

- `section-bounded:` a note text with a well-formed four-column row under
  `## Answers`, and none under `## Mapping table`, must yield no rows from
  `read_mapping`. This guards a reader that scans the whole file and counts
  an illustrative table elsewhere in the note as mapping rows.
- `duplicate-old-path-fails-ac1:` AC1's predicate, run over the live rows
  with one row appended that repeats an existing old path with a different
  new path, must fail. This guards two things:
  - a de-duplicating comparison (`set()` before hashing) that hides a path
    given two destinations, which would leave item 215 or 216 with an
    ambiguous move;
  - a hash computed without the count.

  The appended row changes both the list's length and its digest.
- `heading-without-answer-fails-ac5:` AC5's predicate, run over the live
  note text with heading 1's `**Answer:**` line removed in memory, must fail.
  This guards a check that is satisfied by the heading's presence alone.

**Existing tests to reconcile:** none. This item changes no code, default or
artifact. Adding a gate row moves no existing selector (A7), and
`tests/test_aide_check_no_errors.py` stays green on a four-cell row.

**Downstream (recorded here for the specs that follow).** All of AC1–AC8
keep holding after both migrations. They read only the note, the gate row and
AC1's frozen literal. No later item retires or edits this module (maintainer
decision, 2026-10-05, which superseded an earlier wording that had item 215
retire AC1's test).

The test-writer writes the literal exactly as AC1 states it. They do not
recompute it from the catalogue.

Item 216 carries the spacing collapse, which deliberately changes measured
values (A6). Its spec owns the sweep for tests pinning
`stage3.spacing_consistency.*` or `relationships.neighbour_spacings_mm[]`
values. It also owns the corpus-firing comparison for `fused_label` on any
case whose integer and anatomical orders disagree.

## Validation  <!-- OPTIONAL: how to OBSERVE this working, beyond the tests -->

This needs no `[validation]` profile. The validator runs:

1. **The merge-time check that AC1's frozen literal is the live
   pre-migration set.** It is diff-time, so it is not a suite test. Recompute
   the pair from the claim branch with `.venv/bin/python` over a scratch
   script. The pair is `len` and SHA-256 over `"\n".join(sorted(S))`, and `S`
   is the union of:
   - the `path` of every `groups[*].entries[*]` entry in
     `docs/aide/feature_catalogue.generated.json`;
   - the `reference_delta` leaf paths, by A1's recipe.

   Confirm the pair equals AC1's
   `(165, "488221662105adf220e4b35dbc541acda4b21f1f2ed994ac0098bf34bc067667")`.
   It was computed on `f5c79df`. A mismatch means the catalogue or the
   extraction moved after this spec was written. Hand back; do not edit the
   literal.
2. `python .aide/scripts/aide.py gate list`. The `Stage 27 feature-record
   taxonomy sign-off` gate reads `⏳ Awaiting` and blocks items 215, 216 and
   217. Status `✅` or `❌` is also acceptable if a person has already
   decided.
3. Read `docs/feature-taxonomy.md` as the maintainer will at the gate:
   - every deviation from the scope × kind proposal carries a reason;
   - no grouping is justified by which module computes a field;
   - each `**Answer:**` line is a verdict, with any "left as is" answer giving
     its reason;
   - the note nowhere claims the gate is resolved.
4. `python .aide/scripts/aide.py check`: no errors.

**Do not run `aide gate approve` or `aide gate decline`.**

## Dependencies

None. Everything this item reads is already built and merged on
`aide/queue-029`.

This item's gate names its reach without creating dependency edges —
`Blocks: 215, 216, 217`.

**Downstream:** items 215 and 216 move fields according to the mapping table
and read it through `tests/feature_taxonomy_mapping.py`. Neither edits this
item's test module. Item 217 attests Stage 27 criterion 1 from the
gate row's Status cell. All three are held by `aide claim` until the gate is
approved.

## Decisions & Trade-offs

To be updated during implementation.

- **The structure (as written in `docs/feature-taxonomy.md`).** Scope first,
  then kind: `per_label.{label}` (identity once, kinds `geometry`, `components`,
  `centroid`, `curve`, `orientation`, `neighbourhood`, `intensity`), `pairs`
  (`adjacent`, `overlaps[]`) and `case` (`sequence`, `curve`, `intensity`), with
  `reference_delta` kept as an overlay keyed by `{label}`. The table has 80
  `kept`, 73 `moved` and 12 `merged` rows; item 215 owns 126 and item 216 owns 39.
- **No axis departure, so no re-cut of 215 and 216.** They stay cut along scope
  (215: `per_label` and `reference_delta.{label}`; 216: `pairs`, `case`,
  `features_version`, case-level `reference_delta`). Changing the axis, or moving
  rows across the `per_label` / non-`per_label` line (for example folding
  `reference_delta` into `per_label`), would trigger a re-cut at the gate.
- **Spacing survivor is `relationships.neighbour_spacings_mm[]`**, moved to
  `pairs.adjacent.spacings_mm[]`; `stage3.spacing_consistency.spacings_mm[]` is
  the `merged` row. The per-element neighbourhood spacing copy is left as is
  (unwired, and its `window_labels[]` are integer-ordered).
- **`overlaps[].name_a` / `name_b` are `merged`** onto
  `per_label.{label}.level_name`, a licensed identity copy. The new-path
  placeholders stay `{label}`, `[]`, `{radiomic}`; reference-delta feature names
  are literal in new paths, since a placeholder would collide the 20 report-only
  rows with the five catalogued ones (AC2).
- **Item 216 is told to store `pairs.adjacent.order[]`** (label order beside the
  spacing array). It is a new field with no old path, so it has no table row.

- **The mapping table lives in the note as Markdown, read by one shared
  test-side reader.** A JSON companion would make the maintainer read the
  mapping in one file and sign the prose in another, so the two could drift.
  The queue asks for the table in the note. A Markdown table with backticked
  paths and two closed vocabularies is parsed by one regular expression.
  Putting that expression in a single helper module means items 215–217 do
  not each grow a copy.
- **Moved by partitions the whole table, `kept` rows included.** Every path
  has exactly one migration item answerable for it still being produced
  after the move. That is what lets item 215 and item 216 each check their
  own rows, with no row owned by nobody.
- **`merged` names a path change, not a value guarantee (maintainer decision,
  2026-10-05).** The spacing collapse merges two arrays whose values differ,
  so `merged` cannot mean "an equal copy". The vocabulary stays three values.
  The definition names its two licensed cases, and AC8 pins the one that
  changes values. A fourth value for "re-measured" was not added: AC8 already
  identifies the only such row, and a value-change flag would be a claim no
  test can check before the migration runs.
- **AC1 pins a frozen pre-migration set, not the live catalogue (maintainer
  decision, 2026-10-05).** Comparing against the live catalogue made AC1
  true at this item's merge and false from item 215 on. That is a claim
  about one diff, and it put the catalogue under this item's Asserts against
  while items 215 and 216 change it. So the set is frozen as a
  `(count, SHA-256)` literal in the test module. Its equality to the live
  sources at merge is checked once, by the validator.
- **The table covers every leaf of a real report, not only the catalogue's
  (maintainer decision, 2026-10-05).** The 20 report-only `reference_delta`
  paths are rows in the same table. They use the literal feature name, which
  is what `iter_leaf_paths` produces, so neither the reader nor the Old-path
  notation changed. Teaching the catalogue to list them is not this item's
  work. Whether a migration item extends the catalogue's reference-delta
  driver is the 215 spec's call.
- **The gate cell still says "every feature-catalogue leaf path".** It was
  written before the 20 report-only paths were added. It is not reworded,
  because the cell is the gate's identity and rewording it would mint a
  different gate. The note itself states the 165-path scope.
- **Left open:** whether the record gains a vertebra coordinate system, or a
  reference-delta that takes any requested feature. The note answers whether
  the taxonomy needs either. Building one is re-planned at the gate, because
  neither migration item's scope includes it.
- **Left open:** retiring the eight `retire`-status catalogue paths. The
  maintainer ruled on 2026-10-05 that none is dropped in this stage (A5).
  Whether a later stage drops them is not decided here.
- **Left open:** acting on insights `2026-10-02-3eba`, `2026-09-30-88a5` and
  `2026-09-22-c151`. The note answers where the data they need lives. A
  per-component assessment, mode 4's re-definition and a mode-6 spacing rule
  are each new work, and the entries stay open. The spacing collapse (A6)
  changes which path a future mode-6 rule would read. It builds no rule, so
  `2026-09-22-c151` is not ticked.
- **Review fixes to the note (2026-10-05).** The prose of
  `docs/feature-taxonomy.md` gained, with no change to the mapping table: an
  open question for the gate on whether `image_features` is persisted into the
  features record or only merged into the transient rule record (recommended
  default: runtime merge only, report keeps its own `image_features` key in the
  new layout); Deviations 10 and 11 recording the case-scope sequence fields,
  `is_monotonic`'s placement, and `pairs.adjacent.order[]`; a per-array element
  order table (mixed anatomical and integer orders left as is); the survivor
  spacing array's value difference from `relationships.neighbour_spacings_mm[]`;
  the top-level key count; and the name-to-path map a generalised
  reference-delta would need. The gate remains unresolved.
