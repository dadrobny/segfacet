<!-- aide-template: item 2 -->
# Item 164 — First-class detector ids on rules and in the specification

> **Created:** 2026-09-20 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 32 — Selected-Mode Refinement: one failure mode fully specified end to end (prerequisite of D1's condition 4)
> **Queue:** [`../queue/queue-022.md`](../queue/queue-022.md) · Item 164
> **Objectives:** G2 (a detector, not a rule, is what decides a mode, and which modes it serves is derived not asserted), G8 (the add-a-mode path gains the granularity mode 3's and mode 4's refinement needs)
> **Suggested branch:** `aide/164-first-class-detector-ids-on`

---

## Description

A rule is not a detector. `fragmentation` carries two independent checks —
`Fragmentation:` for a vertebra cut into large same-label pieces (mode 1) and
`Rogue island(s):` for small disconnected blocks (mode 4) — and the
specification records which of the two serves which mode only as **authored
prose** in `IntendedRule.detector`. Nothing mechanical joins that string to the
rule that emits it, so the Stage 32 bar's condition 4 — *at least one detector
decides the mode and serves no other mode* — cannot be answered by code at all.
Joining a mechanical check onto authored prose is exactly the defect item 147
retired when it removed the reserved `"corpus"` tag from
`RuleModeDeclaration.evidence`, so this item does not build one.

Instead, **a detector becomes a declared thing with a stable id.** Each
registered rule declares, beside its `mode_declaration`, the detectors it
actually ships: a rule-local id, a one-line description, and the subset of the
rule's own `signal`-classified leaf paths that detector reads. Every
`IntendedRule` edge names one or more of those ids rather than a message
fragment, every `Finding` carries the id of the detector that produced it, and
**which modes a detector serves is derived from the specification's edges, never
authored a second time** on the rule.

That last point is the whole design. `modes_for_detector(rule_id, detector_id)`
reads `SPECIFICATION[*].intended_rules` and nothing else, so "the
`Rogue island(s):` detector serves mode 4 and no other mode" becomes a
one-expression, one-source fact that item 165 checks against live state rather
than a sentence a reader has to trust. Two new conformance directions in
`segfacet.traceability` score the join in both directions: an edge naming a
detector id no rule declares, and a declared detector no edge names (and which
carries no `mode_less_reason` of its own).

### Why this changes no firing, and why the ratchet stays green

Item 163's spec states the constraint on this item directly: *"item 164
(detector ids) must keep this ratchet green with no specification edit to any
expected set."* It does, structurally, because **every edit here is on a
different axis from the one the ratchet measures**:

- The ratchet compares `set(measured_firing)` against `set(expected_firing)`,
  and both are sets of **`rule_id`s**. This item adds a *second*, finer
  attribute beside `rule_id`; it removes, renames or re-routes none.
- No rule's `evaluate` gains, loses or moves a branch, a threshold, a read path
  or a condition. The only edit inside a rule body is the `detector_id=` keyword
  added to each existing `Finding(...)` construction — a field no rule reads, on
  an object whose `rule_id` is unchanged.
- No `CorpusCaseExpectation` is touched. `SPECIFICATION[*].corpus_cases` —
  every `case_id`, `corpus`, `expected_firing` and `reason` — is byte-unchanged;
  the edit inside `failure_modes.py` is confined to `IntendedRule`, whose edges
  the ratchet never reads.
- No corpus case, manifest, operator, fixture or reference artifact is added,
  removed or regenerated.

So `measured_firing` returns the same tuple for all 15 committed cases after this
item as before it, and `tests/test_163_specificity_ratchet.py` passes untouched.
If a regeneration would move any `expected_firing`, that is a contradiction to
hand back, not a file to commit.

### What a detector id *is*, concretely

For a rule that has none today, a detector is **one branch of `evaluate` that
decides independently whether to emit a finding**, identified by the message tag
constant that branch interpolates. Measured on this tree, 2026-09-20, by reading
every `_*_TAG` constant and every `Finding(...)` construction in
`src/segfacet/heuristics/`: **21 detectors across the 10 registered rules**, of
which **7 rules are multi-detector**:

| Rule | Detectors (declared id ← message tag) | Multi? |
| --- | --- | --- |
| `border` | `expected_end` ← `Partial vertebra at FOV end (expected):` · `unexpected_clip` ← `Partial vertebra clipped by FOV:` | **yes (2)** |
| `bounds` | `metric_out_of_range` ← the below-min / above-max pair over `_METRICS` (one decision, two directions, no tag constant) | no (1) |
| `coverage` | `count_shortfall` ← `Below expected count:` · `incomplete_span` ← `Incomplete coverage (span):` · `missing_interior` ← `Missing interior level(s):` | **yes (3)** |
| `fragmentation` | `components` ← `Fragmentation:` · `islands` ← `Rogue island(s):` | **yes (2)** |
| `intensity` | `degenerate` · `too_high` · `too_low` ← the three `Implausible intensity (...)` tags | **yes (3)** |
| `intensity_reference_delta` | `distance` · `out_of_range` · `robust_z` ← the three `Level-aware intensity ...` tags | **yes (3)** |
| `mislabel` | `ordering` ← `Vertebra ordering inconsistent with label:` · `spline_offset` ← `Vertebra misaligned from spinal curve:` | **yes (2)** |
| `overlap` | `overlapping_segments` ← `Overlapping segments:` | no (1) |
| `reference_delta` | `distance` · `out_of_range` · `robust_z` ← the three `Reference ...` tags | **yes (3)** |
| `sequence` | `discontinuity` ← `Non-continuous label sequence:` | no (1) |

The queue line named three multi-detector rules (`fragmentation`, `mislabel`,
`coverage`); measurement finds seven. All ten declare, single-detector rules
included, so the conformance directions are **total** and no caller has to ask
"is this rule multi-detector?" before reading an id.

Ids are **rule-local slugs**, joined as the pair `(rule_id, detector_id)`. They
are deliberately not globally qualified: `reference_delta` and
`intensity_reference_delta` both ship an `out_of_range`, and keeping the join
per-rule is what stops one rule's edge being satisfied by another rule's
detector (a named adversarial case below).

Three detectors serve no mode **by design**, and say so in a `mode_less_reason`
of their own rather than being silently exempt: `border`'s two (the
`fov_truncation` condition's detectors — `border` declares a mode-less
`RuleModeDeclaration` today) and `mislabel`'s `spline_offset`, whose disposition
the item-150 sign-off settled ("the offset from the spinal curve is an
anatomy-classification signal … Detector A serves NO failure mode").

### What this item is NOT

- **Not a mode refinement.** No mode's specification entry gains or loses a
  rule, a candidate feature, a corpus case or a status. Items 165 and 167 do
  that.
- **Not a narrowing of item 162's exercise report.** Item 162's spec notes
  downstream that "item 164 narrows this report's per-rule rows to per-detector
  ones". **This item deliberately leaves it per-rule** (see Left open): no
  consumer in queue-022 reads a per-detector exercise row, and narrowing it
  means re-deriving the unexercised *reason* per detector — a second authored
  judgement over the same evidence rungs — for a report that would then change
  schema twice in three items.
- **Not a narrowing of the feature catalogue.** `RuleDetector.signal_paths`
  ships the per-detector path attribution item 165 reads directly, but
  `segfacet.catalogue`'s per-path `failure_modes` attribution is **not**
  re-derived through it and neither committed catalogue artifact regenerates
  (see Left open).
- **Not a rule, threshold, extractor, verdict, CLI or corpus change**, and no
  dependency is added.
- **Closes no stage criterion.** No acceptance criterion below carries a
  *(closes Stage N criterion M)* annotation, and under item template 2 that
  silence is the answer: this item builds the mechanism, item 165 checks mode 4
  against it, and **item 169 performs the attestation from a clean clone**.
  Item 163's validator ticked Stage 20 criterion 4 from the working checkout on
  2026-09-20 and the tick was retracted the same day for exactly that reason.

## Acceptance Criteria

- [ ] **AC1: Every registered rule declares at least one detector.** The set of
  `rule.rule_id` for every rule in `segfacet.heuristics.iter_rules()` whose
  `mode_declaration.detectors` is non-empty equals the set of `rule.rule_id`
  over all of `iter_rules()`, read live in the test from the registry — no
  literal rule list. (10 rules, 21 detectors on this tree, measured 2026-09-20;
  both counts are recomputed, never pinned.)

- [ ] **AC2: A declaration rejects a malformed or duplicated detector id.**
  `RuleModeDeclaration` raises `ValueError` naming the field `'detectors'` and
  the offending id when constructed with a detector whose `detector_id` is
  empty, does not match `^[a-z][a-z0-9_]*$`, duplicates another detector's id,
  or is out of ascending order.

- [ ] **AC3: A declaration rejects a `signal_paths` element the same
  declaration does not classify `signal`.** `RuleModeDeclaration` raises
  `ValueError` naming the detector id and the offending path when a
  `RuleDetector.signal_paths` element is not the `path` of a `ConsumedPath` in
  the same declaration carrying `role == "signal"`.

- [ ] **AC4: Every `signal` path of a rule is claimed by at least one of its
  detectors.** For every rule in `iter_rules()`, the set of `ConsumedPath.path`
  values its declaration classifies `"signal"` equals the union of its
  detectors' `signal_paths`, recomputed live from the registry in the test.
  (19 signal paths across 8 rules on this tree, measured 2026-09-20; `border`
  and `intensity_reference_delta` classify none, so their union is empty on
  both sides.)

- [ ] **AC5: Every specification edge names only declared detector ids, and
  names at least one.** For every mode in `segfacet.failure_modes.SPECIFICATION`
  and every `IntendedRule` edge it carries, `edge.detector_ids` is a non-empty
  tuple and every element is a `detector_id` declared by the registered rule
  whose `rule_id` equals `edge.rule_id` — both sides read live in the test, the
  edges from `SPECIFICATION` and the declared ids from `iter_rules()`.

- [ ] **AC6: A detector's modes are derived from the specification, not
  authored.** For every rule in `iter_rules()` and every detector it declares,
  `segfacet.failure_modes.modes_for_detector(rule_id, detector_id)` equals the
  ascending tuple of mode ids `m` for which `SPECIFICATION[m]` carries an
  `IntendedRule` with that `rule_id` whose `detector_ids` contains that id —
  recomputed by the test directly from `SPECIFICATION`, not read back from any
  field on the rule.

- [ ] **AC7: The edge → detector direction's holes are exactly the edges naming
  an undeclared id.** `segfacet.traceability.build_matrix().edge_to_detector`
  reports `holes` equal to the sorted `(mode_id, rule_id, detector_id)` triples
  recomputed live in the test for which `detector_id` is not declared by the
  registered rule named by `rule_id` (or for which `detector_ids` is empty),
  and `complete` equal to `not holes`.

- [ ] **AC8: The detector → edge direction's holes are exactly the declared
  detectors no edge names and no `mode_less_reason` excuses.**
  `build_matrix().detector_to_edge` reports `holes` equal to the sorted
  `(rule_id, detector_id)` pairs recomputed live in the test for every declared
  detector whose `mode_less_reason` is empty and which appears in the
  `detector_ids` of no `SPECIFICATION` edge, and `complete` equal to
  `not holes`. (Non-vacuous on this tree: three detectors carry a
  `mode_less_reason` — `border`'s two and `mislabel`'s `spline_offset` — and
  are excluded by it, not by having no edge.)

- [ ] **AC9: Both new directions reach the committed matrix artifact.**
  `json.loads(Path("docs/aide/traceability_matrix.generated.json").read_text())["directions"]`
  has a key set equal to
  `{"mode_to_rule", "rule_to_mode", "rule_exercise", "operator_exercise", "edge_to_detector", "detector_to_edge"}`,
  and each new entry's `complete` and `holes` equal the values a fresh
  `build_matrix()` produces in the same test session.

- [ ] **AC10: Every finding a committed corpus case produces carries a detector
  id its own rule declares.** For every finding collected by driving all cases
  of both committed manifests through the entry points
  `segfacet.failure_modes.measured_firing` dispatches to, `finding.detector_id`
  is non-empty and is a `detector_id` declared by the registered rule whose
  `rule_id` equals `finding.rule_id` — the declared ids read live from
  `iter_rules()` in the same test.

- [ ] **AC11: `detector_id` round-trips losslessly.** For a `Finding`
  constructed with a non-empty `detector_id`,
  `Finding.from_dict(f.to_dict()) == f`, and for a dict carrying no
  `detector_id` key at all, `Finding.from_dict(d).detector_id == ""` — so a
  report written before this item still loads.

- [ ] **AC12: The report schema admits `detector_id` and requires nothing
  new.** In `segfacet.report._SCHEMA`, the finding definition's `properties`
  contains `"detector_id"` typed `"string"`, its `additionalProperties` is
  still `False`, and its `required` set is still
  `{"rule_id", "severity", "reason", "labels"}`.

- [ ] **AC13: An edge naming an undeclared detector id is caught.** With one
  `SPECIFICATION` mode patched so that one of its edges carries a
  `detector_ids` element no rule declares, a fresh `build_matrix()` reports
  `edge_to_detector.complete is False` and `edge_to_detector.holes` containing
  exactly that `(mode_id, rule_id, detector_id)` triple and no other.

- [ ] **AC14: A declared detector no edge names is caught.** With one
  registered rule's `mode_declaration` patched to add a detector carrying no
  `mode_less_reason` and named by no edge, a fresh `build_matrix()` reports
  `detector_to_edge.complete is False` and `detector_to_edge.holes` containing
  exactly that `(rule_id, detector_id)` pair and no other.

## Assumptions

- **A1 (a detector declares no modes; modes are derived):** the queue line asks
  for "each detector under a stable id **with the mode(s) that detector
  serves**". That is delivered as the derived accessor
  `modes_for_detector(rule_id, detector_id)` over `SPECIFICATION`, **not** as a
  `modes` field on `RuleDetector`. Defensible default taken under
  `loop.clarify = "assume"`: authoring the mode set on the rule *and* on the
  edge recreates the five-partial-sources shape item 147 collapsed, and it would
  make AC7/AC8 — the two directions the queue asks for — a check of one authored
  copy against another rather than of the declaration against the specification.
  If the maintainer wants the rule to state its own claim so the two can
  disagree, that is a third direction and a separate item.

- **A2 (the ten edges that carried `detector=""` name all of their rule's
  detectors):** `bounds` on modes 1–4, `reference_delta` on modes 1–4 and 8, and
  `intensity_reference_delta` on mode 16 carry an empty `detector` string today,
  which reads as "the rule as a whole". Defensible default: each such edge's
  `detector_ids` names **every** detector that rule declares —
  `("metric_out_of_range",)` for `bounds`, `("distance", "out_of_range",
  "robust_z")` for the two delta rules. Grounds: each of those rules' detectors
  is a different statistical view of the *same* per-label magnitude delta the
  edge's mechanism sentence describes, none of them is mode-selective, and the
  rule's own `mode_declaration` already claims the whole mode set with no
  per-detector split. The consequence is the honest one: `modes_for_detector`
  returns 4 modes for `bounds.metric_out_of_range` and 5 for each
  `reference_delta` detector, so those detectors **fail** the Stage 32 bar's
  condition 4 mechanically — which is precisely what the roadmap asserts in
  prose ("the generic volume proxies (`bounds`, `reference_delta`) do not
  count"). No evidence rung, mechanism sentence or expected firing set moves.
  Surfaced here for the maintainer to audit at the queue boundary.

- **A3 (a detector is a branch, identified by its message tag):** the 21
  detectors in the Description's table were measured 2026-09-20 by reading the
  `_*_TAG` constants and the 23 `Finding(...)` construction sites in
  `src/segfacet/heuristics/`. The one judgement is `bounds`, which ships no tag
  constant and whose below-minimum and above-maximum branches are two directions
  of one per-metric bound test; they are declared as **one** detector,
  `metric_out_of_range`. Splitting them would create two detectors with
  identical mode sets and identical read paths.

- **A4 (`RuleDetector.tag` is not declared):** the tag constants are named in
  this spec's table as the *derivation* of the id set, not carried on the
  declaration. Carrying a tag would invite a `reason.startswith(tag)` join —
  the mechanical-check-on-prose shape this item exists to remove. Findings are
  attributed by the `detector_id` field the rule sets explicitly (AC10).

- **A5 (`Finding.detector_id` defaults to `""` and is serialised):** the field
  is added with a default so every existing `Finding(...)` in `tests/` still
  constructs, and it is added to `to_dict`/`from_dict` and to the finding
  definition in `src/segfacet/report_schema_v0.json` as an **optional**
  property. Omitting it from serialisation would make `from_dict(to_dict(f))`
  lossy, which `tests/test_026_rule_engine_core.py`'s AC5 round-trip tests
  already assert against. `required` is unchanged, so item 035's schema
  assertions hold.

- **A6 (the traceability schema version bumps 1.1 → 1.2):** `edge_rungs`'
  middle element changes from `str` to `Tuple[str, ...]` and two directions are
  added, which is a schema change of the same class as item 148's catalogue bump.
  `tests/test_149_conformance_report.py::test_ac2_schema_version_bumped_to_1_1`
  pins `"1.1"` and is reconciled (Testing Strategy).

- **A7 (AC10 pays one corpus drive, in one module-scoped fixture):** driving
  both committed manifests costs 7–27 s (`insights.md`, 2026-09-18, the suite
  wall-clock entry). AC10 therefore collects every case's findings **once**, in
  a module-scoped fixture, through the same `segfacet.synth.regression` entry
  points `measured_firing` dispatches to (`pipeline_findings`,
  `reconstructed_findings`, `intensity_pipeline_findings`) — so the path proved
  is the one the ratchet measures, and no test body drives a case a second time.

- **A8 (the status flip lands on the wrong `progress.md` bullet, and this item
  does not repair it):** `progress.md`'s Stage 32 deliverable bullets attribute
  item numbers two below queue-022's — the detector-ids bullet (this item's
  deliverable) reads *(Item 162)* and is already ✅, while the bullet reading
  *(Item 164)* is mode 3's split operator, which is item 166's. Captured
  verbatim in `insights.md` (item 162, 2026-09-18, the Stage 32 deliverable
  bullet entry) and recorded as item 163's A6. The repair is not assigned by
  queue-022 and is not attempted here.

- **A9 (no human gate):** every input is committed state on this tree. A2 is the
  one authored judgement and it moves no rung, no mechanism and no expected
  firing set; the queue's own human gate over mode rendering is item 168's. No
  row is added to `progress.md`'s `## Human gates` table.

- **A10 (engine 1.59.2):** `aide scope`'s §6 check reports a test naming neither
  an acceptance criterion nor a Testing-Strategy case, and `_CASE_LABEL_RE` reads
  a case label only on a bullet closed by a **colon** — so the three cases below
  are written as `` - `label`: description `` and nothing else is written.

## Implementation Steps

1. **Add `RuleDetector` to `src/segfacet/heuristics/rule.py`**, beside
   `ConsumedPath` and following its shape exactly: a frozen dataclass with
   `detector_id: str`, `description: str`, `signal_paths: Tuple[str, ...] = ()`
   and `mode_less_reason: str = ""`. Export it from `__all__`. No `modes` field
   (A1), no `tag` field (A4).

2. **Add `detectors: Tuple[RuleDetector, ...] = ()` to `RuleModeDeclaration`**
   and validate it inside the existing `__post_init__`, in the same style as the
   `consumed_paths` loop already there (every message names the field
   `'detectors'` and the offending detector id): outer tuple type; each element a
   `RuleDetector`; `detector_id` non-empty and matching `^[a-z][a-z0-9_]*$`;
   ascending and unique by `detector_id`; and every `signal_paths` element the
   `path` of a `ConsumedPath` in the same declaration whose `role` is
   `"signal"`. Reuse the existing `previous_path` ascending-and-unique idiom
   rather than sorting.

3. **Declare the 21 detectors** on the ten `mode_declaration`s in
   `src/segfacet/heuristics/{border,bounds,coverage,fragmentation,intensity,
   intensity_reference_delta,mislabel,overlap,reference_delta,sequence}.py`,
   using the Description's table for ids and the module's existing `_*_TAG`
   constant's wording for `description`. Partition each rule's existing
   `signal`-role `ConsumedPath` paths across its detectors (a path read by two
   detectors is claimed by both; the union must be total, AC4). Give
   `border`'s two detectors and `mislabel`'s `spline_offset` a
   `mode_less_reason` citing the item-150 sign-off. Change no `modes`, no
   `evidence` string, no `ConsumedPath` and no threshold.

4. **Add `detector_id: str = ""` to `Finding`** in
   `src/segfacet/heuristics/finding.py`: include it in `to_dict` after
   `rule_id`, read it in `from_dict` with `d.get("detector_id", "")` (A5), and
   document it in the class docstring. Add the matching optional `"detector_id"`
   property to the finding definition in
   `src/segfacet/report_schema_v0.json`, leaving `required` and
   `additionalProperties: false` as they are.

5. **Pass `detector_id=` at all 23 `Finding(...)` construction sites** in the
   ten rule modules — the one id the branch's tag already identifies. Touch
   nothing else in any `evaluate` body: no branch, threshold, read path or
   emission order moves (the "changes no firing" constraint).

6. **Rename `IntendedRule.detector: str` to `detector_ids: Tuple[str, ...]`** in
   `src/segfacet/failure_modes.py` and extend the existing
   `ModeSpec._validate_intended_rules` loop: `detector_ids` must be a tuple of
   non-empty, unique, ascending strings. The cross-module "is this id declared"
   check stays out of `__post_init__` — it is the conformance direction's job
   (step 8), which is how every other cross-module claim in this module is
   scored rather than raised.

7. **Re-point all 17 edges** to declared ids: the seven that carry prose become
   the matching id tuple (`fragmentation` mode 1 → `("components",)`, mode 4 →
   `("islands",)`; `coverage` mode 6 → `("count_shortfall",
   "incomplete_span", "missing_interior")`; `sequence` → `("discontinuity",)`;
   `mislabel` mode 9 → `("ordering",)`; `overlap` → `("overlapping_segments",)`;
   `intensity` mode 16 → `("degenerate", "too_high", "too_low")`), and the ten
   that carry `""` follow A2. Add
   `modes_for_detector(rule_id: str, detector_id: str) -> Tuple[int, ...]`
   deriving its answer from `SPECIFICATION` alone. Update the `intended_rules`
   serialiser (`"detector"` → `"detector_ids"`, a list) and the renderer's
   `detector = rule["detector"] or "(none)"` line to render the id tuple.
   **Touch no `CorpusCaseExpectation`.**

8. **Add the two directions to `src/segfacet/traceability.py`**, following the
   `mode_to_rule` / `rule_to_mode` pattern exactly: two `DirectionReport` fields
   `edge_to_detector` and `detector_to_edge` on `TraceabilityMatrix`, built in
   `build_matrix`, serialised under `"directions"` in `matrix_to_dict`, and
   rendered in `render_markdown` beside the existing direction sections. Widen
   `ModeRecord.edge_rungs`' middle element to the id tuple. Bump
   `SCHEMA_VERSION` to `"1.2"` (A6).

9. **Re-point the scope fence** in `traceability.py`'s module docstring: the
   clause "It adopts no detector ids (item 164), and does not touch
   ``eval/severity_ladder.py``" now describes the module wrongly. Replace the
   detector-ids half with what the module does — score the edge ↔ detector join
   in both directions over `RuleModeDeclaration.detectors` and
   `SPECIFICATION[*].intended_rules` — leaving the `eval/severity_ladder.py`
   clause and item 163's ratchet clause exactly as they stand.

10. **Correct the stale mode-1 premise** in the disposition comment above
    `ReferenceDeltaRule.mode_declaration`
    (`src/segfacet/heuristics/reference_delta.py`, the "and also
    spline_offset_mm, read from stage3.per_label_offsets[].offset_mm" clause).
    Item 154 re-anchored mode 1 onto
    `per_label.{label}.components.fragmentation_index`
    (`feature_docs.MODE_ANCHOR_PATHS`) and the item-150 sign-off reclassified
    `mislabel`'s offset paths as `bookkeeping` serving no mode, so the clause
    cites a premise that no longer holds. Drop it and say the declaration rests
    on `SPECIFICATION[1].intended_rules` alone. **Comment only** — the
    `evidence` strings, which render verbatim into the committed matrix, are
    unchanged, so this edit regenerates nothing.

11. **Regenerate the four committed artifacts** the shape changes move —
    `docs/aide/failure_modes.generated.{json,md}` and
    `docs/aide/traceability_matrix.generated.{json,md}` — through their existing
    generators, never from a test. Confirm that the `corpus_cases` blocks and
    every `expected_firing` list inside them are byte-unchanged; if any moved,
    stop and hand back.

12. **Regenerate the report format contract** —
    `.venv/bin/python -m tests.report_format_fixture`, never from a test
    (CLAUDE.md, and `tests/committed_artifact_guard.py` enforces it statically) —
    so `tests/golden/report_format_contract.json`'s single synthetic finding
    carries the new key. It is pinned `text eol=lf` in `.gitattributes` already.

13. **Add no dependency**, no new module, no CLI change, no corpus case.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/rule.py` — `RuleDetector` and the `detectors` field plus its validation (steps 1–2).
- `src/segfacet/heuristics/finding.py` — the `detector_id` field and its serialisation (step 4).
- `src/segfacet/report_schema_v0.json` — the optional `detector_id` property on the finding definition (step 4).
- `src/segfacet/heuristics/border.py` — declares 2 detectors, both mode-less; passes `detector_id=` at 2 sites.
- `src/segfacet/heuristics/bounds.py` — declares 1 detector; passes `detector_id=` at 2 sites.
- `src/segfacet/heuristics/coverage.py` — declares 3 detectors; passes `detector_id=` at 3 sites.
- `src/segfacet/heuristics/fragmentation.py` — declares 2 detectors; passes `detector_id=` at 3 sites.
- `src/segfacet/heuristics/intensity.py` — declares 3 detectors; passes `detector_id=` at 3 sites.
- `src/segfacet/heuristics/intensity_reference_delta.py` — declares 3 detectors; passes `detector_id=` at 3 sites.
- `src/segfacet/heuristics/mislabel.py` — declares 2 detectors, one mode-less; passes `detector_id=` at 2 sites.
- `src/segfacet/heuristics/overlap.py` — declares 1 detector; passes `detector_id=` at 1 site.
- `src/segfacet/heuristics/reference_delta.py` — declares 3 detectors, passes `detector_id=` at 3 sites, and carries step 10's comment correction.
- `src/segfacet/heuristics/sequence.py` — declares 1 detector; passes `detector_id=` at 1 site.
- `src/segfacet/failure_modes.py` — `IntendedRule.detector_ids`, its validation, the 17 re-pointed edges, `modes_for_detector`, the serialiser and the renderer (steps 6–7).
- `src/segfacet/traceability.py` — the two directions, the widened `edge_rungs`, the schema bump and the scope fence (steps 8–9).
- `docs/aide/failure_modes.generated.json` — regenerated by step 11 (edge shape).
- `docs/aide/failure_modes.generated.md` — regenerated by step 11 (rendered detector ids).
- `docs/aide/traceability_matrix.generated.json` — regenerated by step 11 (two directions, schema 1.2).
- `docs/aide/traceability_matrix.generated.md` — regenerated by step 11.
- `tests/golden/report_format_contract.json` — regenerated by step 12; the finding block gains `detector_id`.
- `tests/report_format_fixture.py` — its hand-built finding literal gains `detector_id` so the contract it writes carries the key.
- `tests/test_164_detector_ids.py` — this item's own tests (AC1–AC14 plus the three named cases).
- `tests/test_144_failure_mode_specification.py` — reconciliation: ~15 `IntendedRule(detector="")` constructions and the `test_ac13_detector_may_be_empty` fence (see Testing Strategy).
- `tests/test_147_specification_is_the_record.py` — reconciliation: two `IntendedRule(detector="")` constructions.
- `tests/test_149_conformance_report.py` — reconciliation: the `edge_rungs` normaliser reading `entry["detector"]`, the `rule.detector` read, and the `schema_version == "1.1"` pin.
- `tests/test_151_stage30_validation.py` — reconciliation: the `edge_rungs` equality and the `(rule_id, detector, evidence_rung)` unpack.
- `tests/test_026_rule_engine_core.py` — reconciliation: the `from_dict` "reconstructs all fields" round-trip, which must now cover `detector_id`.
- `tests/test_035_report_integration.py` — reconciliation sweep of the finding-definition assertions against the new optional property.
- `tests/test_145_eight_hypothesised_modes.py` — reconciliation (added 2026-09-20, Correction 1): constructs `IntendedRule(detector="")` and reads `edge.detector` at 8 sites, two of which join the edge's prose to a finding's `reason` and one of which rests on the retired empty-detector state.
- `tests/test_146_ninth_mode_and_first_proposed.py` — reconciliation (added 2026-09-20, Correction 1): one `IntendedRule(detector="")` construction.
- `tests/test_136_rule_mode_declarations.py` — reconciliation (added 2026-09-20, Correction 2): pins `RuleModeDeclaration`'s **closed field set**, which step 2's `detectors` field widens.
- `tests/test_148_per_path_mode_attribution.py` — reconciliation (added 2026-09-20, Correction 2): pins the same closed field set, and builds an AC7 fixture by `dataclasses.replace` over a live declaration, which step 2's `signal_paths` cross-validation now constrains.
- `tests/test_089_fov_aware_coverage_border.py` — reconciliation (added 2026-09-20, Correction 2): pins whole coverage/border **finding dicts** against a shared literal, which step 4's `detector_id` key widens.
- `tests/test_098_stray_components.py` — reconciliation (added 2026-09-20, Correction 2): defines `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`, the pinned finding-dict literal the entry above compares against.

**Asserts against:**

- `tests/corpus/manifest.json` — the eleven geometric cases AC10 drives; read-only, no case added, removed or regenerated.
- `tests/corpus/intensity/manifest.json` — the four intensity cases AC10 drives; same terms.
- `src/segfacet/feature_docs.py` — `MODE_ANCHOR_PATHS[1]`, the re-anchored mode-1 path step 10's corrected comment now defers to; read, never changed.
- `docs/aide/feature_catalogue.generated.json` — pinned-not-changed: this item does **not** narrow per-path mode attribution (Left open), so the catalogue's `failure_modes` attributions are byte-unchanged and item 148's byte comparison stays green untouched.

## Testing Strategy

**Module:** `tests/test_164_detector_ids.py`.

**Shape.** Two module-scoped fixtures and no others that cost a drive: one
`build_matrix()` (the idiom `tests/test_149_conformance_report.py`,
`tests/test_162_corpus_exercise_report.py` and
`tests/test_163_specificity_ratchet.py` share), and one that collects
`(corpus, case_id, Finding)` triples across both committed manifests exactly
once for AC10 (A7). **No `build_matrix()` call and no corpus drive in any test
body.** AC13 and AC14 perturb inside a snapshot-and-restore fixture (item 162's
`_isolated_rule_registry` idiom for the registry, item 149's patched-
`SPECIFICATION` idiom for the edges) and read the resulting directions from a
fresh `build_matrix()` built inside that fixture.

**One test per AC.** AC1, AC4, AC5, AC6 and AC10 iterate live registry/
specification state; AC2 and AC3 are `pytest.raises` over deliberately-invalid
constructions; AC7–AC9 and AC11–AC14 are single tests.

**Adversarial cases beyond the AC tests — exactly three:**

- `detector-id-collides-across-rules`: with a temporary edge added to a
  `reference_delta` mode naming `out_of_range`, the `edge_to_detector`
  direction still resolves that id against `reference_delta`'s own declared set
  and not against `intensity_reference_delta`'s identically-named detector.
  Guards the failure mode that makes rule-local ids unsafe: a join keyed on the
  bare slug, under which one rule's edge is satisfied by a different rule's
  detector and "serves no other mode" silently answers about the wrong rule.
  Both rules genuinely ship `distance`, `out_of_range` and `robust_z` on this
  tree, so the collision is live, not hypothetical.
- `empty-detector-ids-on-an-edge-is-a-hole`: with one edge patched to
  `detector_ids=()`, the `edge_to_detector` direction reports it as a hole
  rather than skipping it. Guards the failure mode that would let the retired
  `detector=""` state back in unnoticed, leaving Stage 32's condition 4
  unanswerable for that mode while the direction still reads `complete: true`.
- `mode-less-reason-is-what-excuses-a-detector`: with `mislabel`'s
  `spline_offset` detector patched to drop its `mode_less_reason` and nothing
  else changed, it becomes a hole in the `detector_to_edge` direction. Guards
  the failure mode where the exemption is keyed on "this detector happens to
  have no edges" instead of on a recorded reason, under which every
  yet-to-be-wired detector silently excuses itself.

**Existing tests to reconcile** (grepped 2026-09-20 across `tests/` for
`detector`, `edge_rungs`, `schema_version`, `Finding(` and the finding schema
definition). Each is an expired pin on a shape this item's own ACs change, not
a claim this item contradicts:

1. `tests/test_144_failure_mode_specification.py::test_ac13_detector_may_be_empty`
   — asserts `IntendedRule(detector="")` constructs and
   `mode.intended_rules[0].detector == ""`. **Narrowed**, not deleted: the field
   is `detector_ids`, and the empty case is now a scored hole (AC7), so the test
   becomes the assertion that an empty tuple constructs and is reported. The
   same file carries ~15 further `IntendedRule(..., detector="", ...)`
   constructions (around lines 151, 936, 948, 959, 970, 979–980, 1059–1061,
   1071–1073, 1079–1081) — a keyword rename each.
2. `tests/test_147_specification_is_the_record.py` — two
   `IntendedRule(detector="")` constructions (around lines 671 and 686); keyword
   rename.
3. `tests/test_149_conformance_report.py` — the `edge_rungs` normaliser reading
   `entry["detector"]` (around lines 100–110), the `rule.detector` read (around
   line 526), and `test_ac2_schema_version_bumped_to_1_1`, which pins `"1.1"`
   against A6's bump to `"1.2"`.
4. `tests/test_151_stage30_validation.py` — the `row.edge_rungs ==
   expected_edges` equality (around line 228) and the
   `for rule_id, detector, evidence_rung in row.edge_rungs` unpack (around line
   542): the triple stays a triple, but its middle element is now a tuple.
5. `tests/test_026_rule_engine_core.py` — AC5's `from_dict reconstructs all
   fields` test, which must cover `detector_id` for the round-trip claim to stay
   true.
6. `tests/test_035_report_integration.py` — the finding-definition assertions
   (the `required` set and `additionalProperties is False` around line 103) are
   expected to pass unchanged under A5; sweep the file for any assertion over
   the definition's **properties** key set, which would not.
7. `tests/test_145_eight_hypothesised_modes.py` *(added 2026-09-20, Correction
   1)* — 8 sites, and **three of them need more than the keyword rename**. In
   file order:
   - **Line ~221, `_detector_alternatives(detector)`** — a helper that splits
     an `IntendedRule.detector` prose string on `" / "` so a `reason` prefix
     test can ask "one of these". **Delete the helper**: `detector_ids` is
     already a tuple, so there is nothing to split, and its only caller (the
     AC20 test below) stops joining on prose.
   - **Lines ~1071–1075, `test_ac18_mislabel_detector_leading_tags_differ`,
     catalogue half only** — asserts
     `mislabel_edges[0].detector.startswith(_MISLABEL_TAG.rstrip())` and
     `_MISALIGN_TAG.strip() not in mislabel_edges[0].detector`. This is a
     **semantic** claim (mode 9's edge names the ordering detector and not the
     spline-offset one) expressed as a prose-tag prefix join — the exact shape
     this item retires. **Narrow to the id join**: assert
     `mislabel_edges[0].detector_ids == ("ordering",)` and
     `"spline_offset" not in mislabel_edges[0].detector_ids`, dropping the two
     tag imports from that half only. The first half of the same test — the
     four `f.reason.startswith(_MISALIGN_TAG / _MISLABEL_TAG)` assertions over
     findings from the `displace` and `relabel_swap` cases (lines ~1035–1058) —
     is about a finding's **reason** text, which this item does not touch, and
     **stays exactly as it is**.
   - **Lines ~1166–1167,
     `test_ac20_detector_names_the_detector_that_actually_fired`** —
     `assert edge.detector` becomes `assert edge.detector_ids`, and the
     `any(f.reason.startswith(alternative) ...)` join over
     `_detector_alternatives(edge.detector)` becomes
     `any(f.detector_id in edge.detector_ids for f in matching)`. Same claim,
     keyed on the declared id this item ships instead of on the message tag.
     Update the docstring's first reconciliation bullet (the `" / "` composite
     paragraph) to say the edge carries ids; leave its second bullet (the
     named-but-unfired opt-in detectors) standing, since that premise is
     unchanged.
   - **Line ~1206,
     `test_ac20_an_empty_detector_never_belongs_to_a_rule_that_fired`** — its
     premise is **retired by this item, not renamed**. It skips every edge with
     a truthy `detector` and ends `assert checked, "expected >=1 edge authored
     with no detector name"`; step 7 re-points all ten `detector=""` edges to
     non-empty id tuples (A2), so `checked` would be 0 and the test goes red on
     its own guard. **Narrow, not delete**, to the stronger post-164 state it
     becomes: rename it
     `test_ac20_no_edge_is_authored_without_a_detector_id`, drop the `corpus`
     fixture parameter and the per-case drive entirely (it no longer needs
     either), and assert `edge.detector_ids` for every edge of every mode in
     `_GEOMETRIC_CORPUS_MODE_IDS`, keeping the `checked` counter and retitling
     its message. Its docstring records the date, that item 164 retired the
     empty-detector state, and that AC5/AC7 above are where the claim now lives
     in full.
   - **Line ~1465,
     `test_adv_intended_rule_for_a_rule_not_declaring_the_mode_fails_ac5_check`**
     — `IntendedRule(rule_id="border", detector="", ...)` → `detector_ids=()`.
     Mechanical. The edge is a deliberately-broken copy fed to the AC5
     predicate, which reads `rule_id` only, so an empty tuple is the faithful
     translation and must still construct (step 6 permits it; emptiness is a
     scored hole, not a construction error).
8. `tests/test_146_ninth_mode_and_first_proposed.py` *(added 2026-09-20,
   Correction 1)* — **1 site, purely mechanical**. Line ~1615, in
   `test_adv_mode13_with_intended_rules_is_legal_at_construction_but_flagged`:
   `IntendedRule(rule_id="__item146_adv_mode13_edge__", detector="", ...)` →
   `detector_ids=()`. Same reasoning as item 7's last bullet. The file's other
   `detector` occurrences (a docstring at ~1069, the fake rule id
   `"__item146_fake_mode13_detector__"` at ~1177) are not the field and are
   left alone.
9. `tests/test_136_rule_mode_declarations.py::test_ac1_field_names`
   *(added 2026-09-20, Correction 2)* — asserts
   `{f.name for f in dataclasses.fields(RuleModeDeclaration)}` equals the
   **closed** set `{"modes", "evidence", "mode_less_reason", "pending_reason",
   "consumed_paths"}`. Step 2 adds a sixth field. **Widen the set to include
   `"detectors"`** and nothing else, and extend the docstring's existing
   reconciliation note (it already records item 148's `consumed_paths`) with
   the same sentence for item 164's `detectors`. The claim is *closed field
   set* — "these fields and no others" — and it survives intact: the set stays
   exhaustive and a seventh field still fails it.
10. `tests/test_148_per_path_mode_attribution.py` *(added 2026-09-20,
    Correction 2)* — **two tests, and the second is not mechanical**:
    - `test_ac2_field_set_and_default_and_backward_compatible_construction`
      (~line 210) carries the identical closed field-set pin. **Same widening
      as entry 9**, for the same reason; the three backward-compatible
      constructions below it are unaffected (`detectors` defaults to `()`).
    - `test_ac7_not_read_cannot_hide_an_observed_path` (~line 429) builds its
      adversarial fixture with
      `dataclasses.replace(decl, consumed_paths=new_paths)`, flipping one
      demonstrably-read path to `role="not-read"`. `replace` carries the
      original `detectors` across unchanged, so the rebuilt declaration now
      trips step 2's cross-validation — measured on this tree the target pair
      is `bounds` / an `extent_*_mm` path, and construction raises
      *"'metric_out_of_range' signal_paths element '…extent_x_mm' is not the
      path of a ConsumedPath … role=='signal'"*. **The shipped `bounds`
      declaration is correct; the fixture is what must be repaired.** Pass
      **`detectors=()`** in that one `dataclasses.replace` call, and say so in
      a one-line comment naming why. Rationale, and why the test's own claim
      is carried across rather than weakened: AC7's subject is
      `segfacet.catalogue.path_classification_conflicts()`, which reads a
      declaration's `consumed_paths` roles and the catalogue's per-rule
      evidence and **reads no detector at all** (measured 2026-09-20: no
      occurrence of `detector` in `src/segfacet/catalogue.py`). Dropping the
      detectors from the *probe* declaration therefore changes nothing the
      checker observes; the probe still classifies an `observed` path
      `not-read`, and the assertion that a conflict naming both the rule and
      the path is reported is unchanged. The alternative — rebuilding each
      detector with the flipped path filtered out of its `signal_paths` —
      produces the same observable at the cost of code that re-derives a
      declaration the test never inspects.
    - **Do not touch `test_ac6_extra_classified_path_and_both_directions_...`**
      (~line 409), which uses the same `replace` idiom: it is measured green on
      the built branch and is outside this reconciliation.
11. `tests/test_089_fov_aware_coverage_border.py::test_ac16_committed_corpus_coverage_and_border_findings_unchanged`
    *(added 2026-09-20, Correction 2)* — compares **whole finding dicts**
    (`fresh == pinned`) for the `coverage`/`border` subset of every committed
    corpus case, against `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`, imported from
    `tests/test_098_stray_components.py`. Step 4 adds `detector_id` to
    `Finding.to_dict()`, so the fresh dicts carry a key the literal does not
    (measured: `'detector_id': 'missing_interior'` on `remove_level`).
    **Update the pinned literal, not the comparison** — the same shape as this
    item's already-correct `tests/golden/report_format_contract.json`
    reconciliation, where the hand-built finding literal gains the key rather
    than the assertion learning to ignore it. Add a `"detector_id"` entry to
    **every** finding in the constant, each taken from the `Finding(...)` site
    that emits that reason tag (verified in
    `src/segfacet/heuristics/` 2026-09-20): `displace` → `"spline_offset"`;
    `fragment` → `"components"`; `inject_islands` → `"islands"`;
    `relabel_swap` → `"ordering"`; `remove_level` → `"missing_interior"`;
    `crop_at_border` → `"unexpected_clip"` (border) and `"spline_offset"`
    (mislabel). All seven, not only the two a raw-dict comparison reads, so the
    snapshot stays a faithful record of what the pipeline emits and the next
    raw-dict reader does not meet a half-updated literal. Record the change as
    a dated `#:` note above the constant, in the convention the file already
    uses for its item-120 and item-132 amendments. The test's claim — *the
    FOV-restriction alters no committed case's coverage/border output* — is
    carried across exactly: the comparison stays whole-dict equality, now over
    a key the emitting rule genuinely sets, so a changed verdict, label set,
    reason **or detector attribution** still fails it.
    **No other reader of that literal moves** (measured 2026-09-20): the
    remaining consumers project it through `_finding_summary`
    (rule_id/severity/labels/reason) in `test_098` and `test_132`, through
    `_face_insensitive_findings` (rule_id/severity/labels triples) in
    `test_108`, or compare `verdict` only (`test_090`, `test_094`);
    `test_105` and `test_135` assert only that the constant's **name** appears
    in the source. All are immune to an added key.

**Untouched and must stay green:** `tests/test_163_specificity_ratchet.py`.
Nothing in this item edits an `expected_firing`, a corpus case or a rule's
firing decision, so its 15 per-case parametrisations pass without an edit. A red
run there is a contradiction to hand back, not a test to reconcile.

## Validation

Read the mechanism the item exists to create, against live state:

```
.venv/bin/python -c "import segfacet.failure_modes as f; print(f.modes_for_detector('fragmentation','islands'), f.modes_for_detector('fragmentation','components'), f.modes_for_detector('reference_delta','out_of_range'))"
```

Expect `(4,) (1,) (1, 2, 3, 4, 8)` — mode 4's deciding detector serving exactly
one mode, which is what item 165 checks the Stage 32 bar's condition 4 against,
beside a generic volume proxy that serves five and so cannot.

Then confirm by eye that
`docs/aide/failure_modes.generated.md`'s "Intended rules" bullets render
detector **ids** rather than message fragments, and that its "Corpus cases"
bullets are unchanged from the previous revision (`git diff` on that file should
show no line inside a corpus-case bullet).

No `[validation]` profile is needed: everything here runs on the committed tree
with no optional dependency.

## Dependencies

- **Item 136** — `RuleModeDeclaration` and the module-level rule registry that
  `detectors` extends.
- **Item 148** — `ConsumedPath` and the `"signal"` role, the vocabulary
  `RuleDetector.signal_paths` is validated against (AC3, AC4).
- **Item 149** — `traceability.build_matrix` and the `DirectionReport` pattern
  the two new directions follow.
- **Item 150** — the maintainer-signed-off specification: the `IntendedRule`
  edges this item re-points, and the disposition that makes `mislabel`'s
  spline-offset detector mode-less.
- **Item 154** — the mode-1 re-anchor onto
  `per_label.{label}.components.fragmentation_index`, the premise step 10's
  comment correction defers to.
- **Item 162** — merged immediately before this item on `aide/queue-022`; it
  owns the `exercise` block and the rewritten scope fence in
  `src/segfacet/traceability.py`, so step 9's docstring edit lands on top of its
  text rather than reinstating an older revision.
- **Item 163** — merged immediately before this item; its scope-fence clause and
  its ratchet are the two things step 9 must leave intact and step 11 must not
  move.

**Downstream:** item 165 reads `modes_for_detector('fragmentation', 'islands')`
for the Stage 32 bar's condition 4 and `RuleDetector.signal_paths` for its
condition 3; item 167 declares mode 3's new detector with a first-class id and
asserts per-detector firing through `Finding.detector_id`; item 169 replays both
generated artifacts from a clean clone and performs every Stage 20 / Stage 32
attestation.

## Decisions & Trade-offs

- **2026-09-20 — implementation notes.** Built exactly per the Implementation
  Steps, with two small judgement calls not otherwise pinned by the spec:
  - **`fragmentation`'s detector `signal_paths` overlap.** Both `components`
    and `islands` declare all five of the rule's signal paths
    (`component_count`, `component_sizes[]`, `fragmentation_index`,
    `largest_component_fraction`, `stray_component_sizes[]`) rather than a
    strict partition, because `evaluate()`'s island branch reads
    `fragmentation_index`/`largest_component_fraction` for its message and
    the fragmentation branch reads `component_count`/`component_sizes` for
    its message — each detector genuinely reads what it declares. AC4 asks
    only that the *union* equal the rule's signal-path set, which permits
    overlap ("a path read by two detectors is claimed by both", Description).
  - **`RuleModeDeclaration.detectors` validation order.** The per-detector
    `signal_paths` check runs after the existing `consumed_paths` loop (so
    the signal-path set it validates against is already built), and the
    outer-tuple-type check gained `"detectors"` alongside `"modes"`/
    `"evidence"`/`"consumed_paths"` for the same "reject a bare str/list
    before the element loop" reason those three already had.
  - Traceability's two new directions (`edge_to_detector`/`detector_to_edge`)
    reuse the existing `DirectionReport` dataclass rather than a new type:
    Python dataclasses do not enforce field type annotations at runtime, and
    the item spec's step 8 says to follow the `mode_to_rule`/`rule_to_mode`
    pattern "exactly" — introducing a second report shape for two more
    directions would be exactly the kind of unrequested variation that
    pattern warns against.
  - Verified against live state (not just re-derived by eye): `modes_for_detector`
    reproduces the spec's own worked example exactly —
    `('fragmentation','islands') -> (4,)`, `('fragmentation','components') -> (1,)`,
    `('reference_delta','out_of_range') -> (1,2,3,4,8)` — and a fresh
    `build_matrix()` reports both new directions `complete=True, holes=()` on
    the unperturbed tree (10 rules, 21 detectors, 3 excused by
    `mode_less_reason`). All three named adversarial scenarios and AC13/AC14
    were also exercised by hand against live `build_matrix()` calls before
    committing, confirming the exact hole tuples the spec's tests assert.

- **2026-09-20 — the reconciliation surface widened; the deliverable did not.**
  The "existing tests to reconcile" list authored above missed two files
  (`tests/test_145_eight_hypothesised_modes.py`,
  `tests/test_146_ninth_mode_and_first_proposed.py`); Correction 1 below adds
  them. Caught by the test-writer **before any build**, which is where a
  reconciliation gap is cheap — the alternative was a red suite on validation
  round 1 with the diff already written. No acceptance criterion, implementation
  step, assumption or `Asserts against` entry changes: the item still delivers
  exactly the mechanism AC1–AC14 describe. What widened is the set of files that
  must be carried across the rename with it.

- **2026-09-20 — the reconciliation surface widened a second time; the
  deliverable still did not.** Validation round 1 on the built branch found
  three further files red, in four tests; Correction 2 below adds them. The
  list is now **empirically complete**: a full suite run on the built branch
  yields exactly those four failures and no others, so the reconciliation set
  is measured rather than inferred. Still no acceptance criterion,
  implementation step, assumption or `Asserts against` entry changes.
  **The lesson, for the next item that renames or extends a shared type.**
  Correction 1 was derived by grepping for `IntendedRule.detector`, and a
  keyword grep could not have found any of these three: they break on two
  *other* surfaces this item changes — a new **field** on a shared dataclass
  (`RuleModeDeclaration.detectors`, which closed field-set pins assert
  against, and which cross-validates a fixture built by
  `dataclasses.replace`) and a new **key** in a serialised dict
  (`Finding.to_dict()`, which pinned finding-dict literals assert against).
  Neither surface mentions the renamed name anywhere. So: **when an item adds
  a field to a shared dataclass or a key to a serialised dict, the
  reconciliation surface is every test that pins that type's field set or that
  type's serialised output — and it is found by running the suite, not by
  grepping the renamed name.**

- **Left open:** whether item 162's `exercise` report narrows from per-rule rows
  to per-detector ones. Item 162's spec notes it downstream of this item, but no
  consumer in queue-022 reads a per-detector exercise row, and narrowing it
  requires re-deriving the *unexercised reason* per detector — a second authored
  judgement over the same `EVIDENCE_RUNGS` evidence — and a third schema change
  to the same artifact in three items. Deferred whole; `modes_for_detector` and
  `Finding.detector_id` are the two pieces a later item would need, and both
  ship here.
- **Left open:** whether `segfacet.catalogue`'s per-path `failure_modes`
  attribution narrows from the rule's mode set to the union over the detectors
  claiming that path. It would change exactly `fragmentation`'s five `signal`
  paths (the only multi-mode rule whose detectors split its modes), regenerating
  `docs/aide/feature_catalogue.generated.*` and reopening item 148's
  byte-identity and `mode_evidence` assertions plus item 154's ladder
  measurements — out of proportion to what queue-022 needs, since item 165 reads
  the detector's paths from `RuleDetector.signal_paths` directly. The mechanism
  ships; the catalogue's adoption of it does not.
- **Left open:** whether `RuleDetector` should also carry the rule's own claim
  about which modes its detector serves, so the declaration and the
  specification can be checked against each other (A1 takes the derived route
  instead). That is a third conformance direction with its own reconciliation
  burden, and it is a maintainer's call about where a detector's mode claim is
  authored, not one this item should settle from inside.

## Correction — 2026-09-20

**Appended, not a rewrite.** Everything above stands as authored on 2026-09-20;
this section records one completeness defect found **before any build**, by the
test-writer while deriving the tests from the criteria above, and what it adds.
No acceptance criterion, implementation step, assumption or `Asserts against`
entry is changed by it.

### 1. Two more files read `IntendedRule.detector` and were in neither list

**The gap.** The Testing Strategy's "existing tests to reconcile" block named
six files; a re-grep of `tests/` for `detector=` and `.detector` on this tree on
2026-09-20 returns **two more** —
`tests/test_145_eight_hypothesised_modes.py` (8 sites) and
`tests/test_146_ninth_mode_and_first_proposed.py` (1 site). Neither was listed
for reconciliation and neither appeared under **Authorised paths → May change**,
so the builder would have been unauthorised to touch the very files step 6's
rename turns red. (The six originally listed have since been updated by the
test-writer in commit `c344226`, which is why the grep now returns exactly these
two.) Both go red the moment step 6 lands: the rename removes the field they
construct and read.

**The resolution.** Both files are added under **Authorised paths → May
change**, and entries 7 and 8 of the "existing tests to reconcile" block state
each edit site by site. Three of the nine sites need **more than the mechanical
`detector=""` → `detector_ids=()` / `.detector` → `.detector_ids` rename**, and
the reconcile entries prescribe each so the builder decides nothing:

- **`_detector_alternatives`** (`test_145`, ~line 221) exists only to split an
  `IntendedRule.detector` prose string on `" / "`. A tuple needs no splitting —
  **the helper is deleted** along with its single caller's use of it.
- **`test_ac18_mislabel_detector_leading_tags_differ`'s catalogue half**
  (`test_145`, ~lines 1071–1075) joins the mode-9 edge to `mislabel`'s message
  tag constants by prefix (`edge.detector.startswith(_MISLABEL_TAG.rstrip())`).
  That is the same class of defect as `test_144`'s
  `test_ac13_detector_may_be_empty` — a semantic claim carried on prose — and it
  is **narrowed to the id join** `detector_ids == ("ordering",)` plus
  `"spline_offset" not in detector_ids`. The test's other half, four
  `f.reason.startswith(...)` assertions over findings, is about a finding's
  reason text, is untouched by this item, and **stays as authored**.
- **`test_ac20_an_empty_detector_never_belongs_to_a_rule_that_fired`**
  (`test_145`, ~line 1206) is the one whose **premise this item retires**, and
  the one a keyword rename would silently break: it skips every edge with a
  truthy detector and then asserts it checked at least one, but step 7 leaves
  **no** edge with an empty `detector_ids` (A2 gives each of the ten
  `detector=""` edges its rule's full detector set), so the counter reaches its
  guard at zero. It is **narrowed, not deleted**, into the stronger state that
  replaces it — every edge names at least one detector id — losing its corpus
  drive in the process.

The remaining six sites (`test_145`'s AC20 main test at ~1166–1167 beyond its
join, and its construction at ~1465; `test_146`'s construction at ~1615) are the
mechanical rename.

**Insight inbox.** The `gap` entry the test-writer appended to
`docs/aide/insights.md` (item 164, 2026-09-20) records this same finding; it is
left verbatim and unticked as a captured claim, and is **resolved in-item** by
this correction.

## Correction 2 — 2026-09-20

**Appended, not a rewrite.** Everything above stands as authored — the original
acceptance criteria, the original **Authorised paths** entries, and Correction 1
included. This section records a **second** completeness defect in the same
place Correction 1 widened (the set of files this item must carry across its own
change), found by **validation round 1 on the built branch**, plus one minor
review finding on a reconciliation Correction 1 already prescribed. **No
acceptance criterion is in dispute and the deliverable does not change.**

### 1. Three more files break, on two surfaces a grep cannot reach

**The gap.** A full suite run on the built branch gives **exactly four failures
in three files** — the whole remaining breakage, measured rather than grepped:

| Test | Surface it pins |
| --- | --- |
| `tests/test_136_rule_mode_declarations.py::test_ac1_field_names` | `RuleModeDeclaration`'s closed field set |
| `tests/test_148_per_path_mode_attribution.py::test_ac2_field_set_and_default_and_backward_compatible_construction` | the same closed field set |
| `tests/test_148_per_path_mode_attribution.py::test_ac7_not_read_cannot_hide_an_observed_path` | a `dataclasses.replace` fixture over a live declaration |
| `tests/test_089_fov_aware_coverage_border.py::test_ac16_committed_corpus_coverage_and_border_findings_unchanged` | whole `coverage`/`border` finding dicts |

**Why Correction 1 missed them, and the general lesson.** Correction 1 was
derived by grepping `tests/` for `IntendedRule.detector`. None of these three
files mentions that field. They break on two *other* surfaces this item changes:

- a new **field** on a shared dataclass — step 2's
  `RuleModeDeclaration.detectors` — which any test pinning that dataclass's
  **field set** asserts against, and whose new `signal_paths` cross-validation
  constrains any fixture rebuilt with `dataclasses.replace` over a live
  declaration; and
- a new **key** in a serialised dict — step 4's `detector_id` in
  `Finding.to_dict()` — which any test pinning a **finding-dict literal**
  asserts against.

A keyword grep for the renamed name cannot find either. Stated plainly for the
next item: **when an item adds a field to a shared dataclass or a key to a
serialised dict, the reconciliation surface is every test that pins that type's
field set or that type's serialised output, and it is found by running the
suite, not by grepping the renamed name.**

**The resolution.** Four files are added under **Authorised paths → May
change** — the three that fail, plus
`tests/test_098_stray_components.py`, which is where the fourth failure's fix
actually lands: `test_089`'s AC16 compares against
`_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`, a literal **defined in `test_098` and
imported**, so the authorised list must name the file the diff will touch.
Entries 9–11 of the Testing Strategy's "existing tests to reconcile" block
prescribe each edit site by site, so the test-writer decides nothing. Two of the
four need more than a set-widening:

- **`test_148`'s AC7 fixture** is repaired by passing **`detectors=()`** to its
  one `dataclasses.replace(decl, consumed_paths=new_paths)` call. **The claim is
  carried across, not weakened**, and that matters here specifically: AC7 exists
  to prove that classifying a path `not-read` cannot hide a path the rule
  demonstrably reads. Its subject is
  `segfacet.catalogue.path_classification_conflicts()`, which reads a
  declaration's `consumed_paths` roles and the catalogue's per-rule evidence
  and **reads no detector at all** (measured 2026-09-20: `detector` does not
  occur in `src/segfacet/catalogue.py`). So the probe still flips an `observed`
  path to `not-read` on a live declaration, and still asserts the conflict
  naming both the rule and that path is reported — nothing about the hiding
  claim is relaxed. What `detectors=()` removes is only an unrelated
  cross-field constraint that the *probe's* rebuilt declaration would otherwise
  have to satisfy. The shipped `bounds` declaration is correct and is not
  touched.
- **`test_089`'s AC16** is repaired by updating the **pinned literal**, not the
  comparison — every finding in `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS` gains its
  emitting site's `detector_id`. The comparison stays whole-dict equality, so a
  changed verdict, label set, reason or detector attribution still fails it. No
  other reader of that literal moves; entry 11 records the measurement.

### 2. The `checked` counter on `test_145`'s AC20 replacement, restated

Correction 1's entry 7 prescribed narrowing
`test_ac20_an_empty_detector_never_belongs_to_a_rule_that_fired` into
`test_ac20_no_edge_is_authored_without_a_detector_id`, **"keeping the `checked`
counter and retitling its message"**. The replacement landed **without** the
counter and without its terminal guard: it is now a bare nested loop over
`_GEOMETRIC_CORPUS_MODE_IDS`, which would pass having asserted nothing if that
id set were ever narrowed or emptied — this repo's number-one defect class per
[`REVIEW.md`](../../../REVIEW.md), and the very guard the predecessor carried.

**Restated unambiguously.** `tests/test_145_eight_hypothesised_modes.py::test_ac20_no_edge_is_authored_without_a_detector_id`
initialises `checked = 0` before the loop, increments it once per edge asserted,
and ends with a terminal guard whose message now describes what it counts rather
than the retired empty-detector premise:

```
assert checked, "expected >=1 intended-rule edge across the geometric-corpus modes"
```

Everything else about the landed test — its name, its docstring, the dropped
`corpus` fixture parameter, the per-edge `assert edge.detector_ids` — stands as
Correction 1 prescribed.

