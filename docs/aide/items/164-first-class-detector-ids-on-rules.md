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

To be updated during implementation.

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
