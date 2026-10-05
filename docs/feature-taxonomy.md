# Feature-record taxonomy

**Status: proposed, pending the Stage 27 sign-off gate.** This note (item 214) is
the design the maintainer reads at the `Stage 27 feature-record taxonomy sign-off`
row of the Human gates table in [`aide/progress.md`](aide/progress.md). Until a
person resolves that gate it is a proposal. Nothing in `src/segfacet/`, the
catalogue or the report schema has changed. Items 215 and 216 migrate the record
to this shape and item 217 attests the stage. The table at the end covers the
**165** leaf paths a real report carries before the migration: the feature
catalogue's 145 plus 20 `reference_delta` paths the catalogue does not list (see
Answer 4). Precedent for a design put to a gate:
[`spinal-curve-model.md`](spinal-curve-model.md).

## Structure

A path is addressed by **scope** first (what entity the number describes), then
**kind** (what is measured about it). Four top-level keys remain, three of them
scopes.

| Top-level key | Scope | Holds |
|---|---|---|
| `features_version` | record | schema stamp (unchanged) |
| `per_label.{label}` | one vertebra label | `label`, `level_name` (the only copy), then kind blocks: `geometry`, `components`, `centroid`, `curve`, `orientation`, `neighbourhood`, `intensity` |
| `pairs` | two labels | `pairs.adjacent` (the anatomically adjacent pairs: spacings, their deviations, summary statistics, pair lists) and `pairs.overlaps[]` (labels whose masks share voxels) |
| `case` | the whole label map | `case.sequence` (level inventory and order, from today's `relationships`), `case.curve` (curvature, monotonicity), `case.intensity` (availability and backend of the intensity features) |
| `reference_delta` | overlay, keyed by `{label}` | the comparison of a case to a reference distribution (see Deviations) |

Kinds, by what the field measures and not by which module computes it:

- `geometry`: size, extent and bounding box in the image frame, and which image
  faces the label touches.
- `components`: connected-piece topology, including per-component arrays.
- `centroid`: where the label is.
- `curve`: where the label sits relative to the fitted spinal curve (offset,
  closest parameter, whether it is a terminal level).
- `orientation`: which way the vertebral body points (principal axis, spline
  tangent).
- `neighbourhood`: how the label compares with the labels around it.
- `intensity`: scan-intensity statistics. Present only when a scan was supplied.

Placeholders in the table's new paths: `{label}` (a key of `per_label`), `[]` (a
list element) and `{radiomic}` (the PyRadiomics family), exactly as
`segfacet.catalogue.normalise_leaf_path` produces them. **No new placeholder is
introduced.** Pairs are list elements, so `[]` covers them. The reference-delta
feature names are written literally, as in the old paths, because collapsing them
to a placeholder would give the five old `physical_volume_mm3` rows and the 20
report-only rows colliding new paths.

Two rules hold throughout:

1. **Identity is stored once**, at `per_label.{label}.label` and
   `per_label.{label}.level_name`. Everything else that names a label carries
   either the integer key or nothing.
2. **A field sits at the scope of the entity it measures.** A per-pair number
   (spacing, deviation) is at pair scope, a whole-spine summary at case scope.

The migration items are cut along the same axis: **item 215** owns the
`per_label` scope and `reference_delta.{label}`, **item 216** owns the `pairs`
and `case` scopes, `features_version` and the case-level `reference_delta`
fields.

## Rationale

The current record groups fields by the extractor that produced them: `stage3.*`
holds everything Stage 3 computed, `image_features.*` everything Stage 8
computed, and each of those restates the label identity per element. Item 106's
steering review traced about two thirds of its `retune` verdicts to that one
cause. Scope-first addressing fixes that at its source:

- a field's path says what entity it describes, so a consumer selecting "every
  per-label feature" or "every pair feature" selects by prefix, not by knowing
  module history;
- identity has one home, so a join never has to choose between five copies;
- a kind is a property of the measurement, so a new extractor that measures an
  existing kind lands in the existing block.

Cost, stated once: paths move wholesale, so every reader of `stage3.*`,
`image_features.*`, `relationships.*` and `overlaps[]` is re-pointed by items 215
and 216. The existing drift test and the regenerated catalogue are the safety
net; no rule's behaviour changes except the spacing collapse in Deviations.

## Alternatives considered

- **Keep module provenance** (`stage3`, `image_features` as they are).
  Rejected: it is the status quo this stage exists to remove.
- **Kind first, scope second** (`geometry.per_label.{label}.*`). Rejected:
  consumers almost always start from a label, and identity would still be
  repeated per kind.
- **Fully flat record with a tag per field** (`scope`, `kind` as attributes, one
  list of fields). Rejected: it loses the self-describing path and forces every
  reader through a lookup; for a record this size a nested path is simpler.
- **A fourth scope for individual components.** Rejected, see Answer 5.
- **Literal scope x kind with `identity` as a kind block.** Rejected: identity
  is the key of the per-label entry, not one more measurement beside geometry.
  See Deviations.
- **Move `reference_delta` under `per_label`.** Rejected, see Deviations.

## Deviations from the starting proposal

The starting proposal is scope (`per_label` / `per_neighbour-pair` / `per_case`)
by kind (shape-geometry / intensity / label-identity / ...). The design follows
it in outline. Every point where it does not:

1. **Identity is not a kind block.** `label` and `level_name` are fields of the
   per-label entry itself, stored once. Reason: identity is what the entry is
   keyed by and what every other copy duplicates, so treating it as a sibling of
   geometry recreates the duplication the stage removes. This also makes
   "no identity field stored more than once" (roadmap Stage 27, criterion 2) a
   property of the shape.
2. **The kinds are finer than shape / intensity / identity.** Seven per-label
   kinds, listed in Structure. Reason: the "shape-geometry" kind of the proposal
   would hold both the image-frame size fields and the spline-relative fields,
   and those differ in what they need (the image frame alone, against a fitted
   curve over several labels). Each kind is defined by the quantity measured. The
   boundary between `orientation` and `curve`, and the placement of
   `neighbourhood`, are the least clean calls: both are "relative to something
   other than the label alone" and could be one block. They stay separate
   because their values are computed from different inputs (a body axis against
   the curve's tangent, against a window of neighbours).
3. **`reference_delta` stays a top-level overlay, keyed by `{label}`.** The
   proposal would put per-label kinds under `per_label`. The reference-delta is a
   comparison of measured features to an external artifact: it is absent without a
   reference, carries its own version stamps and case-level fields (`stratum`,
   `lower_pct`, `upper_pct`), and its `features.<name>` selects from the measured
   per-label features rather than adding a measurement. Splitting it would scatter
   one cohesive block across two scopes. Only its identity copies are merged.
4. **`pairs` holds both pair lists and the pair statistics.** The summary
   statistics of the adjacent spacings (`mean_spacing_mm`, `cv_spacing`) and the
   lists naming pairs (`outlier_pairs[]`, `non_monotonic_pairs[]`) sit in
   `pairs.adjacent` beside the spacings they are computed from, although a
   statistic over pairs is case-shaped. Reason: they are meaningless apart from
   the pair array and are read with it.
5. **`case.curve.u_values[]` is a per-label sequence stored at case scope.** It
   holds the cumulative path position of each centroid, as evidence for
   `is_monotonic`. Reason: it is meaningful only as the whole sequence (the
   monotonicity check compares neighbours), and it is a different quantity from
   `curve.closest_u`, so it is not folded into `per_label`.
6. **The adjacent-pair spacing collapse (maintainer decision, 2026-10-05).** Two
   stored arrays hold the same quantity: `relationships.neighbour_spacings_mm[]`
   and `stage3.spacing_consistency.spacings_mm[]`. They collapse into one,
   `pairs.adjacent.spacings_mm[]`, in anatomical order. The maintainer's reason:
   *"the integer-label order is anatomically meaningless"*. This is not a copy:
   wherever integer and anatomical order disagree (TPTBox `T13` is 28 and `Cocc`
   is 27) the surviving array's values, pairs and length differ from what
   `stage3.spacing_consistency.spacings_mm[]` held. It is the one retune this
   stage authorises, and item 216 carries it. Its consumers are in Answer 6.
7. **The neighbour-pair identity `name_a` / `name_b` is merged.** The integers
   `label_a` / `label_b` stay as the pair's keys into `per_label`; the two names
   are copies of `per_label.{label}.level_name` and merge onto it. The values are
   equal, and the roadmap forbids a stored second copy.
8. **`stage3.per_label_neighbourhood[]` is owned by item 215**, not 216, because
   its elements are per-label and carry duplicated identity; the queue text named
   neither item for it.
9. **No field is deleted.** The eight paths the catalogue marks `retire`
   (`component_volumes_mm3[]`, `fragmentation_index`, `centroid_voxel[]`,
   `offset_voxel`, `small_fragments[]`, `image_features_version`,
   `reference_delta_version`, `reference_schema_version`) each keep a stored row.
   That status is a steering verdict, not an authorisation to drop a field in this
   stage.

The cut of items 215 and 216 along the scope axis (per-label first, then pair and
case) is unchanged by this design, so the gate need not re-cut them. What would:
changing the axis itself, or moving rows across the line between `per_label` and
the other scopes (for example folding `reference_delta` into `per_label`).

## Answers

### Identity fields stored in several containers

**Answer:** Identity is stored once, at `per_label.{label}.label` and `per_label.{label}.level_name`, and every other copy is merged onto it.

The five containers that restate the pair are `stage3.per_label_offsets[]`,
`stage3.per_label_orientations[]`, `stage3.per_label_neighbourhood[]` (which
also carries `window_labels[]`), `reference_delta.{label}` (both fields) and
`image_features.per_label.{label}` (`label` only). The transient
`intensity_reference_delta` block, which shares `reference_delta`'s shape, carries
them per label too, and follows `reference_delta`'s rule; it has no rows because
no report carries it. Pair identity in `overlaps[]` is stored as both integer and
name: `label_a` and `label_b` stay as keys, `name_a` and `name_b` merge onto
`level_name`. Once the per-label containers fold into `per_label.{label}` the
copies have nowhere left to live, which is why item 215 owns
`stage3.per_label_neighbourhood[]`.

### stage3 and image_features beside per_label

**Answer:** Both stop being top-level containers: their per-label fields fold into `per_label.{label}` as the `curve`, `orientation`, `neighbourhood` and `intensity` kinds, and their pair-level and case-level fields move to `pairs` and `case`.

Nothing in them is a new scope; each field already describes a label, a pair or the
whole map, and only its container hid which. The mapping table gives every
field's destination. `image_features` keeps one case-level block,
`case.intensity`, for the availability and backend flags. The `intensity` kind
stays optional: it exists only when a scan was supplied, as today.

### Image-axis-relative shape features

**Answer:** Left as is, in the image frame, and the taxonomy does not need a vertebra coordinate system to be stated.

`extent_x_mm`, `bbox_*`, the `touches_*` flags and `principal_axis[]` are measured
against the image's axes. That is a property of each field, documented in its
description, and not a structural axis of the record: re-expressing them in a
vertebra frame would change values, not where they live, and the path would be the
same either way. A vertebra coordinate system is therefore not built here. If the
maintainer wants those fields re-expressed, that is new work to be re-planned at
the gate, and it would not move any row in the table.

### The reference-delta's feature selection

**Answer:** The taxonomy does not need a generalised reference-delta: the block stays as an overlay with its fixed three-vocabulary feature set, with its identity copies merged away.

The limitation is real but narrower than "hardcoded to `physical_volume_mm3`".
`compute_reference_delta` scores every feature the loaded reference tracks, drawn
from three fixed vocabularies (`INGESTED_FEATURES`, `INGESTED_INTENSITY_FEATURES`,
`INGESTED_MORPHOLOGY_FEATURES`), each read through its own hand-coded path. Only
the catalogue's driver is limited to one feature. Against the bundled reference
the report carries 20 further paths (`extent_x_mm`, `extent_y_mm`, `extent_z_mm`
and `spline_offset_mm`, each with `out_of_range`, `percentile_rank`, `robust_z`,
`value`, `z_score`); they get rows in the table, with the literal feature name,
owned by item 215. Because the record's per-label features now sit at addressable
`per_label.{label}.<kind>.<name>` paths, a later generalisation could select by
path; that is not required to state or migrate the taxonomy. The transient
`intensity_reference_delta` block is attached to the rule-evaluation record only,
sits beside `reference_delta` as the same kind of overlay, and is out of the
table because no report writes it. The morphology delta has no caller in the
pipeline and likewise gets no rows.

### Where per-component features live

**Answer:** Left as is: per-component data stays under `per_label.{label}.components`, and the scope axis gains no per-component level.

Components have no stable identity across cases, only an ordinal in descending-size
order, so they are not an entity a path can key by. The data is parallel arrays in
`component_sizes[]` order (`component_sizes[]`, `component_volumes_mm3[]`,
`component_contacts[]`) beside the label-level aggregates, and it is complete at
its current location for a per-component assessment (insights `2026-10-02-3eba`,
`2026-09-30-88a5`). Consolidating the parallel arrays into one array of records
is possible later and changes no path ordering decision; it is not done here, and
no insight is acted on.

### Which path owns adjacent-pair spacing

**Answer:** `pairs.adjacent.spacings_mm[]` owns it, in anatomical order over every label with unrecognised labels last; `stage3.spacing_consistency.spacings_mm[]` merges onto it and `relationships.neighbour_spacings_mm[]` moves to it.

Per the maintainer's 2026-10-05 decision (Deviations, point 6):

- **Order and label set.** Every label, in anatomical order, unrecognised labels
  kept and placed last. This is the order the pipeline already builds as
  `anatomical_centroids`, not `relationships`' ordering, which drops level names
  outside the canonical vocabulary.
- **Presence.** Present on every record that has `relationships.neighbour_spacings_mm`
  today, which is every record with at least one label; `[]` only below two
  labels. On coincident-centroid records, where Stage 3 is unavailable, it is
  computed exactly as `relationships.neighbour_spacings_mm` is today, over the
  decided label set and order. Only the derived statistics stay Stage-3-only.
- **What the consumers read afterwards.** `heuristics/fused_label.py` reads
  `pairs.adjacent.spacings_mm[]` and must pair each spacing with the
  anatomically adjacent labels, not the integer-adjacent ones (item 216 stores
  the label order beside the array, as `pairs.adjacent.order[]`, so the pairing is
  stated in the record). The four statistics derived from the same array
  (`mean_spacing_mm`, `cv_spacing`, `deviations_mm[]`, `outlier_pairs[]`) read it
  too and change value wherever the pairs change. `failure_modes.py`,
  `report_schema_v0.json`, `feature_docs.py`, the `default_config.yaml` comment and
  the `synth/coverage_border_overlap.py` docstring name the old path and are
  re-pointed. The single `src/` reader of the `relationships` array,
  `human_report.render_feature_table`, is re-pointed too. A future mode-6 rule
  (insight `2026-09-22-c151`) reads the survivor; none is built here.
- **The per-element copy is left as is.** The pipeline computes a third spacing
  copy, per element, feeding `per_label.{label}.neighbourhood.stats.spacing_mm.*`,
  in ascending-integer order. It is not re-derived from the survivor. Reason: all
  four fields are unwired, and the neighbourhood's `window_labels[]` are
  themselves taken in integer order, so re-deriving the spacing alone would make
  those statistics disagree with their own window. Re-ordering the whole
  neighbourhood container anatomically is new work, left open. Its paths move
  with the container (item 215) and its values do not change.

## Mapping table

| Old path | New path | Change | Moved by |
|---|---|---|---|
| `per_label.{label}.geometry.bbox_physical.x_max` | `per_label.{label}.geometry.bbox_physical.x_max` | kept | 215 |
| `per_label.{label}.geometry.bbox_physical.x_min` | `per_label.{label}.geometry.bbox_physical.x_min` | kept | 215 |
| `per_label.{label}.geometry.bbox_physical.y_max` | `per_label.{label}.geometry.bbox_physical.y_max` | kept | 215 |
| `per_label.{label}.geometry.bbox_physical.y_min` | `per_label.{label}.geometry.bbox_physical.y_min` | kept | 215 |
| `per_label.{label}.geometry.bbox_physical.z_max` | `per_label.{label}.geometry.bbox_physical.z_max` | kept | 215 |
| `per_label.{label}.geometry.bbox_physical.z_min` | `per_label.{label}.geometry.bbox_physical.z_min` | kept | 215 |
| `per_label.{label}.geometry.bbox_voxel.x_max` | `per_label.{label}.geometry.bbox_voxel.x_max` | kept | 215 |
| `per_label.{label}.geometry.bbox_voxel.x_min` | `per_label.{label}.geometry.bbox_voxel.x_min` | kept | 215 |
| `per_label.{label}.geometry.bbox_voxel.y_max` | `per_label.{label}.geometry.bbox_voxel.y_max` | kept | 215 |
| `per_label.{label}.geometry.bbox_voxel.y_min` | `per_label.{label}.geometry.bbox_voxel.y_min` | kept | 215 |
| `per_label.{label}.geometry.bbox_voxel.z_max` | `per_label.{label}.geometry.bbox_voxel.z_max` | kept | 215 |
| `per_label.{label}.geometry.bbox_voxel.z_min` | `per_label.{label}.geometry.bbox_voxel.z_min` | kept | 215 |
| `per_label.{label}.geometry.extent_x_mm` | `per_label.{label}.geometry.extent_x_mm` | kept | 215 |
| `per_label.{label}.geometry.extent_y_mm` | `per_label.{label}.geometry.extent_y_mm` | kept | 215 |
| `per_label.{label}.geometry.extent_z_mm` | `per_label.{label}.geometry.extent_z_mm` | kept | 215 |
| `per_label.{label}.geometry.physical_volume_mm3` | `per_label.{label}.geometry.physical_volume_mm3` | kept | 215 |
| `per_label.{label}.geometry.touches_anterior` | `per_label.{label}.geometry.touches_anterior` | kept | 215 |
| `per_label.{label}.geometry.touches_inferior` | `per_label.{label}.geometry.touches_inferior` | kept | 215 |
| `per_label.{label}.geometry.touches_left` | `per_label.{label}.geometry.touches_left` | kept | 215 |
| `per_label.{label}.geometry.touches_posterior` | `per_label.{label}.geometry.touches_posterior` | kept | 215 |
| `per_label.{label}.geometry.touches_right` | `per_label.{label}.geometry.touches_right` | kept | 215 |
| `per_label.{label}.geometry.touches_superior` | `per_label.{label}.geometry.touches_superior` | kept | 215 |
| `per_label.{label}.geometry.voxel_count` | `per_label.{label}.geometry.voxel_count` | kept | 215 |
| `per_label.{label}.components.component_contacts[].contact_area_mm2` | `per_label.{label}.components.component_contacts[].contact_area_mm2` | kept | 215 |
| `per_label.{label}.components.component_contacts[].contact_fraction` | `per_label.{label}.components.component_contacts[].contact_fraction` | kept | 215 |
| `per_label.{label}.components.component_contacts[].neighbour_label` | `per_label.{label}.components.component_contacts[].neighbour_label` | kept | 215 |
| `per_label.{label}.components.component_contacts[].surface_area_mm2` | `per_label.{label}.components.component_contacts[].surface_area_mm2` | kept | 215 |
| `per_label.{label}.components.component_count` | `per_label.{label}.components.component_count` | kept | 215 |
| `per_label.{label}.components.component_sizes[]` | `per_label.{label}.components.component_sizes[]` | kept | 215 |
| `per_label.{label}.components.component_volumes_mm3[]` | `per_label.{label}.components.component_volumes_mm3[]` | kept | 215 |
| `per_label.{label}.components.fragmentation_index` | `per_label.{label}.components.fragmentation_index` | kept | 215 |
| `per_label.{label}.components.label_contact_fraction` | `per_label.{label}.components.label_contact_fraction` | kept | 215 |
| `per_label.{label}.components.largest_component_fraction` | `per_label.{label}.components.largest_component_fraction` | kept | 215 |
| `per_label.{label}.components.small_fragments[]` | `per_label.{label}.components.small_fragments[]` | kept | 215 |
| `per_label.{label}.components.stray_component_count` | `per_label.{label}.components.stray_component_count` | kept | 215 |
| `per_label.{label}.components.stray_component_sizes[]` | `per_label.{label}.components.stray_component_sizes[]` | kept | 215 |
| `per_label.{label}.components.stray_contact_area_mm2` | `per_label.{label}.components.stray_contact_area_mm2` | kept | 215 |
| `per_label.{label}.components.stray_contact_label` | `per_label.{label}.components.stray_contact_label` | kept | 215 |
| `per_label.{label}.components.stray_volume_fraction` | `per_label.{label}.components.stray_volume_fraction` | kept | 215 |
| `per_label.{label}.components.stray_volume_mm3` | `per_label.{label}.components.stray_volume_mm3` | kept | 215 |
| `per_label.{label}.centroid.centroid_mm[]` | `per_label.{label}.centroid.centroid_mm[]` | kept | 215 |
| `per_label.{label}.centroid.centroid_voxel[]` | `per_label.{label}.centroid.centroid_voxel[]` | kept | 215 |
| `per_label.{label}.label` | `per_label.{label}.label` | kept | 215 |
| `per_label.{label}.level_name` | `per_label.{label}.level_name` | kept | 215 |
| `relationships` | `case.sequence` | moved | 216 |
| `relationships.is_continuous` | `case.sequence.is_continuous` | moved | 216 |
| `relationships.missing_levels[]` | `case.sequence.missing_levels[]` | moved | 216 |
| `relationships.neighbour_spacings_mm[]` | `pairs.adjacent.spacings_mm[]` | moved | 216 |
| `relationships.out_of_order_labels[]` | `case.sequence.out_of_order_labels[]` | moved | 216 |
| `relationships.present_levels[]` | `case.sequence.present_levels[]` | moved | 216 |
| `overlaps[]` | `pairs.overlaps[]` | moved | 216 |
| `overlaps[].label_a` | `pairs.overlaps[].label_a` | moved | 216 |
| `overlaps[].label_b` | `pairs.overlaps[].label_b` | moved | 216 |
| `overlaps[].name_a` | `per_label.{label}.level_name` | merged | 216 |
| `overlaps[].name_b` | `per_label.{label}.level_name` | merged | 216 |
| `overlaps[].overlap_voxels` | `pairs.overlaps[].overlap_voxels` | moved | 216 |
| `stage3.per_label_offsets[].closest_u` | `per_label.{label}.curve.closest_u` | moved | 215 |
| `stage3.per_label_offsets[].dx_mm` | `per_label.{label}.curve.dx_mm` | moved | 215 |
| `stage3.per_label_offsets[].dy_mm` | `per_label.{label}.curve.dy_mm` | moved | 215 |
| `stage3.per_label_offsets[].dz_mm` | `per_label.{label}.curve.dz_mm` | moved | 215 |
| `stage3.per_label_offsets[].is_terminal` | `per_label.{label}.curve.is_terminal` | moved | 215 |
| `stage3.per_label_offsets[].label` | `per_label.{label}.label` | merged | 215 |
| `stage3.per_label_offsets[].level_name` | `per_label.{label}.level_name` | merged | 215 |
| `stage3.per_label_offsets[].offset_mm` | `per_label.{label}.curve.offset_mm` | moved | 215 |
| `stage3.per_label_offsets[].offset_voxel` | `per_label.{label}.curve.offset_voxel` | moved | 215 |
| `stage3.curvature.coronal_curvature_deg` | `case.curve.coronal_curvature_deg` | moved | 216 |
| `stage3.curvature.coronal_tangent_angles_deg[]` | `case.curve.coronal_tangent_angles_deg[]` | moved | 216 |
| `stage3.curvature.curvature_plane` | `case.curve.curvature_plane` | moved | 216 |
| `stage3.curvature.inter_tangent_angles_deg[]` | `case.curve.inter_tangent_angles_deg[]` | moved | 216 |
| `stage3.curvature.sagittal_curvature_deg` | `case.curve.sagittal_curvature_deg` | moved | 216 |
| `stage3.curvature.sagittal_tangent_angles_deg[]` | `case.curve.sagittal_tangent_angles_deg[]` | moved | 216 |
| `stage3.curvature.tangent_angles_deg[]` | `case.curve.tangent_angles_deg[]` | moved | 216 |
| `stage3.curvature.total_curvature_deg` | `case.curve.total_curvature_deg` | moved | 216 |
| `stage3.per_label_orientations[].eigenvalue_ratio` | `per_label.{label}.orientation.eigenvalue_ratio` | moved | 215 |
| `stage3.per_label_orientations[].label` | `per_label.{label}.label` | merged | 215 |
| `stage3.per_label_orientations[].level_name` | `per_label.{label}.level_name` | merged | 215 |
| `stage3.per_label_orientations[].principal_axis[]` | `per_label.{label}.orientation.principal_axis[]` | moved | 215 |
| `stage3.per_label_orientations[].spline_closest_u` | `per_label.{label}.orientation.spline_closest_u` | moved | 215 |
| `stage3.per_label_orientations[].spline_tangent[]` | `per_label.{label}.orientation.spline_tangent[]` | moved | 215 |
| `stage3.per_label_orientations[].spline_tangent_coronal_deg` | `per_label.{label}.orientation.spline_tangent_coronal_deg` | moved | 215 |
| `stage3.per_label_orientations[].spline_tangent_sagittal_deg` | `per_label.{label}.orientation.spline_tangent_sagittal_deg` | moved | 215 |
| `stage3.monotonic_consistency.is_monotonic` | `case.curve.is_monotonic` | moved | 216 |
| `stage3.monotonic_consistency.non_monotonic_pairs[]` | `pairs.adjacent.non_monotonic_pairs[]` | moved | 216 |
| `stage3.monotonic_consistency.u_values[]` | `case.curve.u_values[]` | moved | 216 |
| `stage3.spacing_consistency.cv_spacing` | `pairs.adjacent.cv_spacing` | moved | 216 |
| `stage3.spacing_consistency.deviations_mm[]` | `pairs.adjacent.deviations_mm[]` | moved | 216 |
| `stage3.spacing_consistency.mean_spacing_mm` | `pairs.adjacent.mean_spacing_mm` | moved | 216 |
| `stage3.spacing_consistency.outlier_pairs[]` | `pairs.adjacent.outlier_pairs[]` | moved | 216 |
| `stage3.spacing_consistency.spacings_mm[]` | `pairs.adjacent.spacings_mm[]` | merged | 216 |
| `stage3.per_label_neighbourhood[].deviation_score` | `per_label.{label}.neighbourhood.deviation_score` | moved | 215 |
| `stage3.per_label_neighbourhood[].is_outlier` | `per_label.{label}.neighbourhood.is_outlier` | moved | 215 |
| `stage3.per_label_neighbourhood[].label` | `per_label.{label}.label` | merged | 215 |
| `stage3.per_label_neighbourhood[].level_name` | `per_label.{label}.level_name` | merged | 215 |
| `stage3.per_label_neighbourhood[].stats.offset_mm.mean` | `per_label.{label}.neighbourhood.stats.offset_mm.mean` | moved | 215 |
| `stage3.per_label_neighbourhood[].stats.offset_mm.median` | `per_label.{label}.neighbourhood.stats.offset_mm.median` | moved | 215 |
| `stage3.per_label_neighbourhood[].stats.offset_mm.std` | `per_label.{label}.neighbourhood.stats.offset_mm.std` | moved | 215 |
| `stage3.per_label_neighbourhood[].stats.offset_mm.z_score` | `per_label.{label}.neighbourhood.stats.offset_mm.z_score` | moved | 215 |
| `stage3.per_label_neighbourhood[].stats.spacing_mm.mean` | `per_label.{label}.neighbourhood.stats.spacing_mm.mean` | moved | 215 |
| `stage3.per_label_neighbourhood[].stats.spacing_mm.median` | `per_label.{label}.neighbourhood.stats.spacing_mm.median` | moved | 215 |
| `stage3.per_label_neighbourhood[].stats.spacing_mm.std` | `per_label.{label}.neighbourhood.stats.spacing_mm.std` | moved | 215 |
| `stage3.per_label_neighbourhood[].stats.spacing_mm.z_score` | `per_label.{label}.neighbourhood.stats.spacing_mm.z_score` | moved | 215 |
| `stage3.per_label_neighbourhood[].stats.volume_mm3.mean` | `per_label.{label}.neighbourhood.stats.volume_mm3.mean` | moved | 215 |
| `stage3.per_label_neighbourhood[].stats.volume_mm3.median` | `per_label.{label}.neighbourhood.stats.volume_mm3.median` | moved | 215 |
| `stage3.per_label_neighbourhood[].stats.volume_mm3.std` | `per_label.{label}.neighbourhood.stats.volume_mm3.std` | moved | 215 |
| `stage3.per_label_neighbourhood[].stats.volume_mm3.z_score` | `per_label.{label}.neighbourhood.stats.volume_mm3.z_score` | moved | 215 |
| `stage3.per_label_neighbourhood[].window_labels[]` | `per_label.{label}.neighbourhood.window_labels[]` | moved | 215 |
| `image_features.per_label.{label}.first_order.entropy` | `per_label.{label}.intensity.first_order.entropy` | moved | 215 |
| `image_features.per_label.{label}.first_order.iqr` | `per_label.{label}.intensity.first_order.iqr` | moved | 215 |
| `image_features.per_label.{label}.first_order.max` | `per_label.{label}.intensity.first_order.max` | moved | 215 |
| `image_features.per_label.{label}.first_order.mean` | `per_label.{label}.intensity.first_order.mean` | moved | 215 |
| `image_features.per_label.{label}.first_order.median` | `per_label.{label}.intensity.first_order.median` | moved | 215 |
| `image_features.per_label.{label}.first_order.min` | `per_label.{label}.intensity.first_order.min` | moved | 215 |
| `image_features.per_label.{label}.first_order.n_nonfinite_excluded` | `per_label.{label}.intensity.first_order.n_nonfinite_excluded` | moved | 215 |
| `image_features.per_label.{label}.first_order.p05` | `per_label.{label}.intensity.first_order.p05` | moved | 215 |
| `image_features.per_label.{label}.first_order.p25` | `per_label.{label}.intensity.first_order.p25` | moved | 215 |
| `image_features.per_label.{label}.first_order.p50` | `per_label.{label}.intensity.first_order.p50` | moved | 215 |
| `image_features.per_label.{label}.first_order.p75` | `per_label.{label}.intensity.first_order.p75` | moved | 215 |
| `image_features.per_label.{label}.first_order.p95` | `per_label.{label}.intensity.first_order.p95` | moved | 215 |
| `image_features.per_label.{label}.first_order.range` | `per_label.{label}.intensity.first_order.range` | moved | 215 |
| `image_features.per_label.{label}.first_order.std` | `per_label.{label}.intensity.first_order.std` | moved | 215 |
| `image_features.per_label.{label}.first_order.voxel_count` | `per_label.{label}.intensity.first_order.voxel_count` | moved | 215 |
| `image_features.per_label.{label}.extended.{radiomic}` | `per_label.{label}.intensity.extended.{radiomic}` | moved | 215 |
| `image_features.available` | `case.intensity.available` | moved | 216 |
| `image_features.backend` | `case.intensity.backend` | moved | 216 |
| `image_features.image_features_version` | `case.intensity.image_features_version` | moved | 216 |
| `image_features.per_label.{label}.label` | `per_label.{label}.label` | merged | 215 |
| `image_features.radiomics_available` | `case.intensity.radiomics_available` | moved | 216 |
| `reference_delta.lower_pct` | `reference_delta.lower_pct` | kept | 216 |
| `reference_delta.reference_delta_version` | `reference_delta.reference_delta_version` | kept | 216 |
| `reference_delta.reference_schema_version` | `reference_delta.reference_schema_version` | kept | 216 |
| `reference_delta.reference_source` | `reference_delta.reference_source` | kept | 216 |
| `reference_delta.stratum` | `reference_delta.stratum` | kept | 216 |
| `reference_delta.upper_pct` | `reference_delta.upper_pct` | kept | 216 |
| `reference_delta.{label}.available` | `reference_delta.{label}.available` | kept | 215 |
| `reference_delta.{label}.distribution_distance` | `reference_delta.{label}.distribution_distance` | kept | 215 |
| `reference_delta.{label}.features.physical_volume_mm3.out_of_range` | `reference_delta.{label}.features.physical_volume_mm3.out_of_range` | kept | 215 |
| `reference_delta.{label}.features.physical_volume_mm3.percentile_rank` | `reference_delta.{label}.features.physical_volume_mm3.percentile_rank` | kept | 215 |
| `reference_delta.{label}.features.physical_volume_mm3.robust_z` | `reference_delta.{label}.features.physical_volume_mm3.robust_z` | kept | 215 |
| `reference_delta.{label}.features.physical_volume_mm3.value` | `reference_delta.{label}.features.physical_volume_mm3.value` | kept | 215 |
| `reference_delta.{label}.features.physical_volume_mm3.z_score` | `reference_delta.{label}.features.physical_volume_mm3.z_score` | kept | 215 |
| `reference_delta.{label}.label` | `per_label.{label}.label` | merged | 215 |
| `reference_delta.{label}.level_name` | `per_label.{label}.level_name` | merged | 215 |
| `reference_delta.{label}.out_of_range_features[]` | `reference_delta.{label}.out_of_range_features[]` | kept | 215 |
| `features_version` | `features_version` | kept | 216 |
| `per_label` | `per_label` | kept | 215 |
| `reference_delta.{label}.features.extent_x_mm.out_of_range` | `reference_delta.{label}.features.extent_x_mm.out_of_range` | kept | 215 |
| `reference_delta.{label}.features.extent_x_mm.percentile_rank` | `reference_delta.{label}.features.extent_x_mm.percentile_rank` | kept | 215 |
| `reference_delta.{label}.features.extent_x_mm.robust_z` | `reference_delta.{label}.features.extent_x_mm.robust_z` | kept | 215 |
| `reference_delta.{label}.features.extent_x_mm.value` | `reference_delta.{label}.features.extent_x_mm.value` | kept | 215 |
| `reference_delta.{label}.features.extent_x_mm.z_score` | `reference_delta.{label}.features.extent_x_mm.z_score` | kept | 215 |
| `reference_delta.{label}.features.extent_y_mm.out_of_range` | `reference_delta.{label}.features.extent_y_mm.out_of_range` | kept | 215 |
| `reference_delta.{label}.features.extent_y_mm.percentile_rank` | `reference_delta.{label}.features.extent_y_mm.percentile_rank` | kept | 215 |
| `reference_delta.{label}.features.extent_y_mm.robust_z` | `reference_delta.{label}.features.extent_y_mm.robust_z` | kept | 215 |
| `reference_delta.{label}.features.extent_y_mm.value` | `reference_delta.{label}.features.extent_y_mm.value` | kept | 215 |
| `reference_delta.{label}.features.extent_y_mm.z_score` | `reference_delta.{label}.features.extent_y_mm.z_score` | kept | 215 |
| `reference_delta.{label}.features.extent_z_mm.out_of_range` | `reference_delta.{label}.features.extent_z_mm.out_of_range` | kept | 215 |
| `reference_delta.{label}.features.extent_z_mm.percentile_rank` | `reference_delta.{label}.features.extent_z_mm.percentile_rank` | kept | 215 |
| `reference_delta.{label}.features.extent_z_mm.robust_z` | `reference_delta.{label}.features.extent_z_mm.robust_z` | kept | 215 |
| `reference_delta.{label}.features.extent_z_mm.value` | `reference_delta.{label}.features.extent_z_mm.value` | kept | 215 |
| `reference_delta.{label}.features.extent_z_mm.z_score` | `reference_delta.{label}.features.extent_z_mm.z_score` | kept | 215 |
| `reference_delta.{label}.features.spline_offset_mm.out_of_range` | `reference_delta.{label}.features.spline_offset_mm.out_of_range` | kept | 215 |
| `reference_delta.{label}.features.spline_offset_mm.percentile_rank` | `reference_delta.{label}.features.spline_offset_mm.percentile_rank` | kept | 215 |
| `reference_delta.{label}.features.spline_offset_mm.robust_z` | `reference_delta.{label}.features.spline_offset_mm.robust_z` | kept | 215 |
| `reference_delta.{label}.features.spline_offset_mm.value` | `reference_delta.{label}.features.spline_offset_mm.value` | kept | 215 |
| `reference_delta.{label}.features.spline_offset_mm.z_score` | `reference_delta.{label}.features.spline_offset_mm.z_score` | kept | 215 |
