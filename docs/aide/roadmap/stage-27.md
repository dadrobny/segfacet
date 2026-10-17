> Stage 27's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 27`, run on the main or queue branch, moves it back.

## Stage 27 — Feature Schema Taxonomy & Coordinate System (G8)

> **Build posture, 2026-09-18 (maintainer decision): the stage stays, and stays
> lean.** The deliverables and acceptance below are unchanged. What the `prototype`
> posture bounds is how much is built to meet them. The taxonomy is one short design
> note, not a survey. The migration moves the record to the new shape and regenerates
> the catalogue, with the existing drift test as its safety net and no new test
> scaffolding beyond what the acceptance bullets need. Of the "known instances", the
> design must *answer* each one, and an answer may be "left as is, for this reason". A
> vertebra coordinate system and a generalised reference-delta are built here only if
> the design shows the taxonomy cannot be stated without them. Nothing is built for
> Stages 23 or 24, which are placeholders.

**Goal.** Give the feature record a **deliberately designed structure** in place of the
current one, which groups fields by *which extractor module happened to compute them*.
Item 106's full 111-entry steering review found this to be the single recurring theme behind
roughly two-thirds of its per-field `retune` verdicts: those verdicts are symptoms of one
structural problem, and executing them one field at a time would entrench the same shape.

**This stage designs the taxonomy; it does not inherit one.** The maintainer's framing —
group by **scope** (`per_label` / `per_neighbour-pair` / `per_scan`-or-case-level) crossed
with **kind** (shape/geometry · intensity · label-identity · …) — is the **starting
proposal and the standard of quality**, not a specification to implement literally. The
stage is expected to evaluate it against the real 111-entry record, and **may deviate where
it has a recorded reason to**: a different axis, an extra dimension, or a flat scheme for
part of the record are all acceptable outcomes *provided the deviation and its rationale are
written down* alongside the design. What is not acceptable is another grouping that happens
to fall out of module provenance.

**Deliverables.**

- **The taxonomy itself**, written down as a design with its rationale, the alternatives
  considered, and every deviation from the scope×kind starting proposal justified — reviewed
  with the maintainer before migration begins. This is a human-checkpoint stage in the same
  sense Stage 19 was.
- **The migration**, applied to the record shape, with item 104's drift test as the safety
  net and item 103's catalogue regenerated against the new schema.
- **Known instances the design must have an answer for** (evidence, not a to-do list):
  identity fields (`label` / `level_name`) independently duplicated across
  `stage3.per_label_offsets[]`, `stage3.per_label_orientations[]`, `image_features.per_label`
  and `reference_delta.{label}`; `stage3.*` / `image_features.*` sitting as top-level
  containers parallel to the `per_label.{label}.*` structure that already holds
  geometry/components/centroid; image-axis-relative shape features (axis-aligned
  bbox/extent, `principal_axis`) flagged for re-expression in a **vertebra coordinate
  system** that does not yet exist — the same axis-semantics problem Stage 26's D2 fixes for
  `touches_*`; and the reference-delta machinery being hardcoded to one tracked feature
  (`physical_volume_mm3`) when it should take any requested feature — which only becomes
  coherent once the record is organised well enough to *select a feature set* from.

**Dependencies.** Stages 19 (the catalogue is the map of what moves) and 20 (the matrix says
which features are load-bearing before any of them are renamed). Should land **before**
Stages 23/24, which both consume the feature vector as a vector. This stage renames leaf
paths wholesale, so it is the natural moment to execute item 105's golden retire
dispositions if Stage 21 has not already. *(Superseded 2026-08-30: Stage 29 D1 owns the
retirement and runs before both.)*

**Validation / acceptance.**

- The taxonomy is documented with its rationale and every deviation from the
  starting proposal justified, and is signed off by the maintainer before
  migration (**G8**).
- Every feature is addressable under it; no identity field is stored more than
  once.
- The regenerated catalogue and the drift test agree; no rule's behaviour
  changes on the corpus except where a retune is explicitly authorised.
