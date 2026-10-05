<!-- aide-template: queue 1 -->
# FACET — Work Queue 029

> **Created:** 2026-10-03
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).
> Opens and closes **Stage 27**. Runs after the maintenance queue
> [`queue-028.md`](queue-028.md).

---

## Scope of this queue

Roadmap **Stage 27 — Feature Schema Taxonomy & Coordinate System**, next in
the run order (33 → **27** → 21 → 16). The stage has three deliverables: the
taxonomy as a signed-off design, the migration, and answers for the four
known instances. The answers are part of the design. The migration is split
by the scope axis of the maintainer's starting proposal: per-label fields
first, then neighbour-pair and case-level fields. Each half is one atomic
change to the record and every reader of it, so the suite is green at each
merge. The queue completes the stage, so it ends with the validation item.

**Prioritisation.** Item 214 runs first and ends in a human gate. The
migration may not start before the maintainer signs the design off (roadmap
Stage 27, criterion 1). Item 215 then item 216, because the case-level move
reads per-label paths that item 215 has already settled. Item 217
(validation) runs last.

**Re-plan at the gate.** The two migration items follow the starting
proposal's scope axis. If the signed design departs from that axis, the
migration items are re-cut to match it at item 214's gate, as queue 027 was
re-cut at `gate-51da`.

**Build posture (`prototype`).** Items 214–216 are named Stage 27
deliverables, and item 217 is the stage-validation item that requirement 5
of queue authoring asks for (`aide check --queue 029`, 2026-10-03). The
roadmap's 2026-09-18 annotation bounds the first three. The design is one
short note, not a survey. A vertebra coordinate system and a
generalised reference-delta are built only if the design shows the taxonomy
cannot be stated without them; otherwise each known instance is answered
"left as is, for this reason". Nothing is built for Stages 23 or 24.

**Insights folded in (inbox read 2026-10-05, after queue 028 closed).** One
entry is absorbed: `2026-10-05-c980` (stale `monotonic_consistency`
descriptions in the report schema) rides on item 216, which rewrites those
lines anyway. Three stay open and are design inputs to item 214, which builds
nothing for them: `2026-10-02-3eba` and `2026-09-30-88a5` (both need a
per-component scope) and `2026-09-22-c151` (adjacent-pair spacing is stored
in two containers). Two knowledge entries bind the migration items' spec
authors: `2026-10-05-da43` (a scratch-copy probe lists each failing test
once, at its first failing assert) and `2026-10-05-dc87` (a probe run without
`.git` reports git-gated tests as passing because they skip). Every other
open entry is passed over as unrelated to the taxonomy; retiring the
duplicate ordering checks (`2026-09-29-a832`) would change rule behaviour,
which Stage 27 criterion 3 forbids.

**Numbering.** Continues at the next free integer: **214–217**.

---

## Work items

### Item 214: The feature-record taxonomy, designed and signed off

Write the taxonomy as one design note: the structure, its rationale, the
alternatives considered, and every deviation from the maintainer's
scope × kind starting proposal (`per_label` / `per_neighbour-pair` /
`per_case` × shape-geometry / intensity / label-identity / …) justified in
writing. A grouping that falls out of extractor-module provenance is not
acceptable. The note answers each of the four known instances. Identity
fields (`label` / `level_name`) are stored in four containers:
`stage3.per_label_offsets[]`, `stage3.per_label_orientations[]`,
`image_features.per_label` and `reference_delta.{label}`. `stage3.*` and
`image_features.*` sit beside `per_label.{label}.*`. Image-axis-relative
shape features (bbox and extent, `principal_axis`) await a vertebra
coordinate system. The reference-delta is hardcoded to `physical_volume_mm3`.
An answer may be "left as is, for this reason". The note also answers two
questions the open insight inbox raises. Where per-component features live:
the record already holds `per_label.{label}.components.component_contacts[]`,
the starting proposal's scope axis has no per-component level, and insights
`2026-10-02-3eba` and `2026-09-30-88a5` both ask for each connected component
to be assessed on its own. And which path owns adjacent-pair spacing:
`relationships.neighbour_spacings_mm[]` and
`stage3.spacing_consistency.spacings_mm[]` both store it (insight
`2026-09-22-c151` names the second as the signal a future rule reads). The
note carries a mapping
table from every leaf path in `docs/aide/feature_catalogue.generated.md` to
its new path, and names which migration item moves it. The item raises a
human gate over the note (roadmap Stage 27 D1, criterion 1). *Testable:* the
mapping table's old-path set equals the catalogue's leaf-path set, and every
new path is unique; each known instance has a recorded answer; the gate is
raised.

### Item 215: Per-label fields migrated under the signed taxonomy

Move every per-label field to the place item 214's mapping table assigns it,
with the label's identity stored once. This covers the
`stage3.per_label_offsets[]` and `stage3.per_label_orientations[]` entries,
`image_features.per_label`, and the transient `reference_delta.{label}`.
Re-point every reader in the same change: rules, `feature_report`,
`human_report`, `report`, `eval/`, `reference/` and `synth/regression`.
Regenerate the feature catalogue, and bump the report schema where its shape
changes. *Testable:* no identity field is stored more than once per label
(criterion 2's identity half); the regenerated catalogue and
`tests/test_104_feature_catalogue_drift.py` agree; every corpus case's
measured firing equals its expected set, unchanged from before the item
(criterion 3).

### Item 216: Neighbour-pair and case-level fields migrated under the signed taxonomy

Move the remaining fields — neighbour-pair relationships and overlaps,
spline fit, spacing and monotonic consistency, and case-level intensity — to
the places item 214's mapping table assigns them, re-pointing every reader
in the same change. After this item, no top-level container exists only
because one extractor module computed its contents. The report schema's
`monotonic_consistency` descriptions are corrected in the same edit: they
still say "spline parameter", and since item 210 the value is normalised arc
length along a label-free path (insight `2026-10-05-c980`). *Testable:* every leaf
path in the regenerated catalogue appears as a new path in item 214's mapping
table (criterion 2's addressability half); the catalogue and its drift test
agree; every corpus case's measured firing equals its expected set, unchanged
from before the item (criterion 3).

### Item 217: Validate stage 27: Feature Schema Taxonomy & Coordinate System

Replay the stage from a clean clone. Every generated artifact must regenerate
byte-identically, and every corpus case's measured firing must equal its
expected set across both corpora. Attest each of Stage 27's three acceptance
criteria against live state: the maintainer's sign-off of item 214's design
(its gate ID and date); every catalogue leaf path addressable under the
taxonomy, with no identity field stored more than once, counted on a
pipeline record of a corpus case; and the regenerated catalogue agreeing
with its drift test, with no rule's behaviour changed on either corpus
unless a retune was explicitly authorised. Stage 27 introduces no
Environment-Gated Capability Verification row, and the item confirms that.
*Testable:* each attestation cites the clean-clone commit and the test or
measurement behind it. A criterion that does not hold is left unticked, with
the measured reason.
