<!-- aide-template: item 3 -->
# Item 205 — The mode 2/3 boundary re-drawn

> **Created:** 2026-09-30 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (D5 re-plan)
> **Queue:** [`../queue/queue-027.md`](../queue/queue-027.md) · Item 205
> **Objectives:** G2, G8
> **Suggested branch:** `aide/205-the-mode-2-3-boundary`

---

## Description

This item re-draws the boundary between mode 2 (fused vertebra segments) and
mode 3 (split vertebra segment) as the maintainer decided when declining
human gate `gate-51da` on 2026-09-30 (`progress.md`, Human gates;
`queue-027.md`, "Re-plan"). It is the first of the four re-plan items
(205–208) that must land before the at-the-bar sign-off of modes 2 and 3
under gate `gate-0133` (item 203).

**Why the re-draw.** Today the two entries in `segfacet.failure_modes`
claim the same error twice. Mode 3's sub-type (a) is "a part of a vertebra
carrying a neighbouring vertebra's label", and mode 2 is "a label extending
across the intervertebral space onto its neighbour". Those describe one
label map. Each discriminator calls the other mode "the converse" and says
the two co-occur. So the `split` corpus case, whose label 24 (L5) covers
all of L5 plus L4's caudal cap, is today attributed to mode 3, and the
detector that decides it (`neighbour_contact`'s `stray_contact`) serves
mode 3.

**The decided boundary.**

- **Mode 2** is one label covering its own vertebra plus part or all of a
  neighbour. This is the paired case, and today's mode-3 sub-type (a) is an
  instance of it. The sacralised-L5 sub-type stays with mode 2.
- **Mode 3** is the fragment case: part of a vertebra carrying a label of its
  own, where that label covers no other vertebra. This is today's sub-type
  (b), plus the lumbarised-S1 sub-type.
- **The label left covering only the remainder of an encroached vertebra**
  (label 23 in `split`: L4 minus its 20 % cap) has no mode yet. The
  maintainer deferred it (`insights.md`, queue-027, 2026-09-30, the `gap`
  entry on the complement to mode 2). Both discriminators say so.

**What this item changes.**

- `failure_modes.py`, `_MODE_2` and `_MODE_3`: the definitions,
  discriminators and mechanisms are rewritten to the decided boundary. The
  `neighbour_contact` edge (`stray_contact`, `synthetic-demonstrable`) and the
  `split` corpus case move from mode 3 to mode 2. The candidate feature
  `per_label.{label}.components.component_contacts[].contact_fraction` moves
  with the edge. `split_own_label` stays as mode 3's only case.
- `failure_modes.py`, other entries: every discriminator clause and case
  reason that sends "a part of a vertebra carrying a neighbour's label" to
  mode 3 is re-pointed at mode 2 (A4).
- `heuristics/neighbour_contact.py`: `mode_declaration.modes` becomes `(2,)`,
  and its evidence and prose are re-pointed at mode 2.
- `synth/component_shape.py`: `SplitPerturbation`'s `Expectation` names
  mode 2, so the committed manifest's `split` case carries `failure_mode` 2.
- `eval/severity_ladder.py`: the `split` ladder's home moves to mode 2.
- The corpus manifest, the corpus sheet, and the generated specification,
  traceability, catalogue and rule-table documents are regenerated.
- The derived-status count clauses `progress.md` attests for Stages 20 and 30
  are amended with `aide progress amend`.

**Not in scope.**

- No detector, no fixture and no threshold. No finding moves: every corpus
  case fires exactly what it fires today (A5).
- No mode for the remainder label (Left open).
- `MODE_SIGN_OFFS` is not touched. Mode 3's `gate-bb24` record stands as the
  record of that sign-off, and mode 2 has none. Item 203 writes both.
- Mode 2's fused-label detector (item 207), the second mode-2 fixture
  (item 206) and mode 3's own detector (item 208).

## Acceptance Criteria

Terms used below:

- **"Mode N"** is `segfacet.failure_modes.SPECIFICATION[N]`.
- **"The modes carrying case C"** is the set of mode ids `m` over every
  entry of `SPECIFICATION` such that some element of mode `m`'s
  `corpus_cases` has `case_id == C`. The test computes it over all modes.

- [ ] **AC1: `split` is attributed to mode 2 alone.** The modes carrying
  case `"split"` equal `{2}`.
- [ ] **AC2: `stray_contact` serves mode 2 alone.**
  `segfacet.failure_modes.modes_for_detector("neighbour_contact", "stray_contact") == (2,)`.
- [ ] **AC3: mode 3's only corpus case is `split_own_label`.**
  `{c.case_id for c in SPECIFICATION[3].corpus_cases} == {"split_own_label"}`.

Why each is written:

- AC1 is the queue line's first *Testable* sentence. Without it the case
  could be left on mode 3 while every other check still passed: the manifest
  and the specification would simply agree on the old attribution.
- AC2 is the queue's second *Testable* sentence. It also carries the third
  ("mode 3's intended rules no longer name `neighbour_contact`") at detector
  granularity, since `modes_for_detector` is computed from every mode's
  edges: a mode-3 edge carrying `stray_contact` makes it `(2, 3)`. The
  rule-granular wording is not used, because item 208 may add mode 3's own
  detector to the `neighbour_contact` rule (Decisions).
- AC3 is the queue's "keep `split_own_label` as mode 3's case". Without it
  the move could take both split cases to mode 2, leaving mode 3 with no
  case at all.

Not written, because something already fails without them:

- "`split` agrees with its expected set": `tests/test_163_specificity_ratchet.py`
  and the conformance tests already require every corpus case to agree, and
  nothing in this item moves a finding (A5).
- The committed manifest carrying `failure_mode` 2 for `split`:
  `failure_modes.specification_conflicts()` reports a manifest case whose
  mode's `corpus_cases` does not carry it (measured on the in-memory probe,
  A6), and `tests/test_146_ninth_mode_and_first_proposed.py`'s AC31 asserts
  it returns `()`. `tests/test_040_synthetic_corpus.py`'s AC17 requires the
  manifest to equal `SplitPerturbation`'s `Expectation`.
- `NeighbourContactRule.mode_declaration.modes == (2,)`:
  `catalogue.rule_declaration_conflicts()` reports both a corpus-designated
  `(neighbour_contact, 2)` pair the declaration lacks and a declared mode 3
  with no mirroring edge, and `tests/test_136_rule_mode_declarations.py`
  asserts it returns `()`.
- "Both generated specification artifacts are regenerated": the existing
  fresh-versus-committed tests for each generated document fail on a stale
  copy.
- The discriminators' sentence that the remainder label has no mode yet:
  that is prose, and a test could only look for a token in it, which is the
  shape check §1 → items rules out. The validator reads the rendering
  (Validation step 1), and the maintainer reads it at gate `gate-0133`.
- `bar_conditions` for modes 2 and 3: recorded in Decisions, not pinned.
  Items 206–208 move both modes' conditions, so a pin here would be a
  premise about their schedule.

None of these closes a Stage 33 acceptance criterion. Criterion 1 is closed
by item 203's sign-off, and criterion 2 by item 204's clean-clone replay.

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
measured value below was taken on this branch on 2026-09-30 with
`.venv/bin/python`, by a scratch probe that applied the edge move, the case
move and the declaration change in memory (`dataclasses.replace` on both
`ModeSpec`s and on `NeighbourContactRule.mode_declaration`, and
`failure_modes.SPECIFICATION` replaced by the patched dict), then re-ran
every derivation. The builder re-measures each value on the real change.

- **A1 (decided at `gate-51da`: the paired case is mode 2).** The `split`
  label map has label 24 covering all of L5 plus L4's caudal cap: one label
  over its own vertebra plus part of a neighbour. That is mode 2 under the
  decided boundary. So the case, and the detector that decides it, move to
  mode 2. `fuse_adjacent` stays mode 2's, and `split_own_label` stays
  mode 3's.
- **A2 (defensible default: the candidate feature moves with the edge).**
  `per_label.{label}.components.component_contacts[].contact_fraction` is the
  signal path of `stray_contact`, so it leaves mode 3's `candidate_features`
  and joins mode 2's, with role `hypothesised` as every other candidate.
  `per_label.{label}.components.stray_contact_area_mm2`, the absolute measure
  no rule reads since item 187, moves with it: it measures the same paired
  contact. Mode 3 keeps `physical_volume_mm3`, its `reference_delta` z-score,
  `spline_leave_one_out_shape_change` and `metric_change_under_merge_candidate`.
  It gains `per_label.{label}.components.label_contact_fraction` as
  `hypothesised`: that is the signal the queue names for item 208 (0.3317 on
  `split_own_label`'s cap, read by no rule).
- **A3 (constraint the mechanisms must meet).** `tests/test_138_traceability_matrix.py`'s
  AC31 requires every catalogue path a mode's `mechanism` names to be consumed
  by one of that mode's declared rules, by a co-detecting rule, or by no rule.
  After the move `neighbour_contact` serves mode 2 only, and `split_own_label`
  does not fire it. So **mode 3's mechanism must not name
  `component_contacts[].contact_fraction`**. It may name
  `label_contact_fraction` (no rule reads it) and `physical_volume_mm3`
  (`bounds` declares mode 3). Mode 2's mechanism may name
  `component_contacts[].contact_fraction`, `physical_volume_mm3` and
  `stage3.spacing_consistency.spacings_mm[]`, and its mechanism must name
  `split` or `fuse_adjacent` as a whole word (AC31's token check). Item 187
  lost a validation round to this check.
- **A4 (defensible default: other entries' clauses are re-pointed, not
  rewritten).** Four discriminators and one case reason send "a part of a
  vertebra carrying a neighbour's label" to mode 3 under the old boundary:
  mode 1's discriminator ("mode 3 when a substantial part of the vertebra
  carries another label"), mode 4's ("modes 2 and 3 when the extra region is
  a substantial part of a neighbouring vertebra"), mode 5's ("mode 3 when the
  missing region carries a neighbour's label"), mode 13's ("mode 3 when one
  of the labels still covers its own vertebra and takes only part of the
  other") and the `fragment` case's reason ("carry no neighbour's label (not
  mode 3)"). Each clause is re-pointed at mode 2, and mode 1's also names
  mode 3 for a part carrying a label of its own. Nothing else in those
  entries changes. Mode 10's "mode 2 when the skipped level's vertebra was
  absorbed by a neighbour's label" is already right and stays.
- **A5 (measured: no finding moves).** Neither the operators' voxel output
  nor any rule's `evaluate` changes. `split` still fires
  `(neighbour_contact, stray_contact)` alone (contact fraction 0.3317 on
  label 24's stray component) and `split_own_label` still fires
  `(bounds, metric_out_of_range)` alone. So:
  - every corpus fixture under `tests/corpus/fixtures/` regenerates
    byte-identical, and only `tests/corpus/manifest.json` moves (`split`'s
    `failure_mode` 3 → 2 and `failure_mode_name` "split vertebra segment" →
    "fused vertebra segments");
  - `docs/aide/golden_evidence.generated.json` does not move, because it
    records no mode;
  - `RECORDED_MARGINS` and `KNOWN_CROSS_MODE_COUPLINGS` do not move, because
    `score_harness` reads no ladder's `failure_mode`. Only the `split`
    ladder's `failure_mode` and `failure_mode_name` change.
- **A6 (measured: what the derivations move).**
  - Mode 2: derived status `implemented` → `validated`; derived rung
    `needs-real-data` → `synthetic-demonstrable`. `bar_conditions(2)`: before,
    condition 1 only; after, conditions 1–5 all met. Condition 2's subjects
    are `("split",)`, condition 3's
    `("per_label.{label}.components.component_contacts[].contact_fraction",)`,
    condition 4's `("neighbour_contact/stray_contact",)`, condition 5's
    `("validated",)`.
  - Mode 3: derived status stays `validated` (`bounds` declares mode 3, and
    `split_own_label` agrees and fires `bounds`); derived rung
    `synthetic-demonstrable` → `needs-real-data`. `bar_conditions(3)`:
    before, 1–5 all met; after, conditions 1, 2 and 5 met, 3 and 4 not.
    Condition 2's subjects become `("split_own_label",)`, reached through the
    `bounds` proxy pair, and conditions 3 and 4 have no subjects. This is the
    loss the queue expects until item 208 lands.
  - `modes_for_detector("neighbour_contact", "stray_contact")`: `(3,)` →
    `(2,)`.
  - `specification_conflicts()` stays `()` only once the manifest is
    regenerated. The probe, with the manifest unregenerated, returned the one
    conflict naming `split` (`failure_mode 3`, not carried by mode 3).
  - Counts over 16 modes: derived status validated 5 → 6, implemented 4 → 3,
    specified 2, proposed 5; validated through a pipeline-detected case 5 → 6,
    through a reconstructed record only 0. Derived mode rung counts are
    unchanged (synthetic-demonstrable 5, needs-real-data 3,
    structurally-unobservable 1, none 7), because modes 2 and 3 swap rungs.
    Per-edge rung counts are unchanged (synthetic-demonstrable 5,
    needs-real-data 7, structurally-unobservable 1), because the edge moves
    whole.
  - The catalogue's corpus-derived rule → mode map gives
    `neighbour_contact → (2,)`, and the `contact_fraction` leaf's
    `failure_modes` move from 3 to 2. The rule table's `stray_contact` row
    serves mode 2.
- **A7 (defensible default: the Stage 20 and 30 status clauses are
  amended).** `tests/test_151_stage30_validation.py`'s AC35 and
  `tests/test_169_stage32_validation.py`'s AC6/AC7 re-measure the counts live
  and compare them with the last attested clause, as items 188, 192, 193 and
  195 found. So the builder amends Stage 30 criterion 1 and Stage 20
  criterion 5 with `aide progress amend`, as those items did. The rung clause
  (Stage 30 criterion 3) does not move and is not amended.
- **A8: no human gate, and no environment-gated capability.** The decision
  this item implements is already recorded at `gate-51da`.

## Implementation Steps

1. **`src/segfacet/failure_modes.py`, `_MODE_2`.**
   - `definition`: one label covers its own ground-truth vertebra plus part
     or all of an adjacent one, extending across the intervertebral space or
     absorbing the neighbour whole. Keep the sacralised-L5 sub-type and its
     disc-label signal.
   - `discriminator`: drop "Mode 3 is the converse". Say mode 3 when the part
     carries a label of its own that covers no other vertebra. Say that the
     label left covering only the remainder of the encroached vertebra has no
     mode yet (deferred at `gate-51da`, 2026-09-30). Keep the mode 1, 4, 6
     and 14 clauses.
   - `mechanism`: rewrite around the two ways the mode is expressed: the
     `stray_contact` detector on the paired case (`split`, contact fraction
     0.3317, re-measured), and the proxy and spacing signal on the absorbed
     case (`fuse_adjacent`, which fires nothing). Respect A3.
   - `candidate_features`: add the two contact paths (A2).
   - `intended_rules`: append the `neighbour_contact` edge exactly as mode 3
     carries it today.
   - `corpus_cases`: append the `split` `CorpusCaseExpectation` with
     `expected_firing=("neighbour_contact",)`. Rewrite its `reason` to call
     it mode 2's paired case, re-measured and dated.
2. **`src/segfacet/failure_modes.py`, `_MODE_3`.**
   - `definition`: part of a vertebra carries a label of its own, and that
     label covers no other vertebra. Keep the lumbarised-S1 sub-type. Drop
     the sub-type (a)/(b) lettering.
   - `discriminator`: mode 2 when the label on the part also covers its own
     vertebra; the remainder-label sentence, as in mode 2's; keep the mode 1,
     4, 8 and 13 clauses.
   - `mechanism`: the mode is seen today only by the `bounds` proxy on
     `split_own_label` (volume 4030 mm³ below the lumbar minimum of 8000,
     `extent_z` 9 mm below 15, re-measured). Its own signal is the whole-label
     contact fraction plus small size, read by no rule yet. Respect A3.
   - `candidate_features`: as A2.
   - `intended_rules`: the `bounds` edge alone.
   - `corpus_cases`: `split_own_label` alone. Re-word its `reason` where it
     says "mode 3 sub-type (b)".
3. **`src/segfacet/failure_modes.py`, other prose.**
   - Re-point the four discriminator clauses and the `fragment` reason
     named in A4.
   - Append an item-205 paragraph to the module docstring's history. The
     item-194 paragraph stays as the record of that revision.
   - Leave `MODE_SIGN_OFFS` untouched.
4. **`src/segfacet/heuristics/neighbour_contact.py`.** Set
   `mode_declaration.modes=(2,)`. Re-point the evidence sentence, the module
   docstring's first line and the class docstring and comment at mode 2
   (fused vertebra segments), and record that item 205 moved the rule. The
   detectors, consumed paths, threshold and `evaluate` do not change. Cite
   `failure_modes.SPECIFICATION`, never vision.md §6
   (`tests/test_161_stage31_validation.py` scans module prose).
5. **`src/segfacet/synth/component_shape.py`.** In
   `SplitPerturbation.apply`, set `failure_mode=2` and
   `failure_mode_name=FAILURE_MODE_NAMES[2]`. Re-point the class docstring.
   `SplitOwnLabelPerturbation` keeps mode 3, and its docstring loses the
   "sub-type (b)" wording. The voxel logic does not change.
6. **`src/segfacet/eval/severity_ladder.py`.** `_LADDER_HOMES["split"]`
   becomes `(2, None)`, with a dated item-205 comment. Update the module
   docstring's "``split`` and ``split_own_label``: ladder mode 3" sentence.
   No recorded value changes (A5).
7. **Prose that calls stray contact mode 3's signal.** A comment edit only
   in each place:
   - `src/segfacet/default_config.yaml`: the `neighbour_contact` comment
     block's "mode 3 (split vertebra segment)";
   - `src/segfacet/feature_docs.py`: the `stray_contact_area_mm2` entry's
     `measures` text;
   - `src/segfacet/features/components.py` and `src/segfacet/feature_report.py`:
     the docstrings naming it mode 3's signal.
8. **Regenerate.** Run each generator twice into temp paths, byte-compare,
   then once with no flags to write the committed copies:
   - `.venv/bin/python -m segfacet.synth.corpus` (writes
     `tests/corpus/`). Only `manifest.json` may change. If a fixture's bytes
     change, hand back (A5);
   - `.venv/bin/python -m segfacet.synth.corpus_sheet` (its `Source` digest
     covers the manifest bytes);
   - `.venv/bin/python -m segfacet.failure_modes`;
   - `.venv/bin/python -m segfacet.traceability`;
   - `.venv/bin/python -m segfacet.catalogue`;
   - `.venv/bin/python -m segfacet.rule_table`.

   Do **not** regenerate `golden_evidence`. If a fresh
   `python -m segfacet.golden_evidence --out <tmp>` differs from the
   committed copy, hand back (A5).
9. **Record the bar.** Run `traceability.bar_conditions(2)` and
   `bar_conditions(3)` on the real change and write both results, per
   condition with its subjects, into Decisions & Trade-offs with the date.
   This is the queue's "re-measured live and recorded in the spec".
10. **Amend the count clauses** with `python .aide/scripts/aide.py progress amend`.
    Re-measure every number live first; A6 gives the expected ones. Each
    `--evidence` starts `Item 205 (<date>): mode 2/3 boundary re-drawn at
    gate-51da; split and neighbour_contact's stray_contact moved to mode 2,
    which derives validated. Re-measured live:` and continues with the
    clause in the shape of item 195's:
    - `amend 30 --criterion 1`: `derived status counts over 16 modes: validated 6, implemented 3, specified 2, proposed 5; validated through a pipeline-detected case 6, through a reconstructed record only 0.`
    - `amend 20 --criterion 5`: `derived status counts over 16 modes: validated 6, implemented 3, specified 2, proposed 5. derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7.`
11. **Reconcile** the tests listed under Testing Strategy, each edit with a
    dated item-205 comment.
12. Run `python .aide/scripts/aide.py scope 205` and
    `python .aide/scripts/aide.py check`. Neither may report an error.

No dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/failure_modes.py` — modes 2 and 3, four other discriminators, the `fragment` reason, the module docstring (steps 1–3).
- `src/segfacet/heuristics/neighbour_contact.py` — the declaration and its prose (step 4).
- `src/segfacet/synth/component_shape.py` — `SplitPerturbation`'s `Expectation` and two docstrings (step 5).
- `src/segfacet/eval/severity_ladder.py` — `_LADDER_HOMES["split"]` and one docstring sentence (step 6).
- `src/segfacet/default_config.yaml` — one comment block (step 7).
- `src/segfacet/feature_docs.py` — one `measures` string (step 7).
- `src/segfacet/features/components.py` — docstrings only (step 7).
- `src/segfacet/feature_report.py` — one docstring only (step 7).
- `tests/corpus/manifest.json` — regenerated; `split`'s mode (step 8).
- `docs/aide/corpus_sheet.png` — regenerated; `split`'s panel title and the input digest (step 8).
- `docs/aide/failure_modes.generated.json` — regenerated (step 8).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 8).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 8).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `docs/aide/rules.generated.md` — regenerated; `stray_contact`'s modes column (step 8).
- `tests/test_205_mode_2_3_boundary.py` — **new**: this item's test module.
- `tests/test_103_feature_catalogue.py` — `_RULE_MODE_MAP["neighbour_contact"]` `(3,)` → `(2,)` and its comment.
- `tests/test_136_rule_mode_declarations.py` — co-detection witness and item-187 comments naming mode 3.
- `tests/test_145_eight_hypothesised_modes.py` — `_EXPECTED_DERIVED_STATUS[2]` → `"validated"`, and mode 2/3 rung or edge pins.
- `tests/test_147_specification_is_the_record.py` — `_EXPECTED_DERIVED_STATUS[2]` → `"validated"` and its comments.
- `tests/test_149_conformance_report.py` — any per-mode case grouping that places `split` under mode 3.
- `tests/test_166_split_operator.py` — `split` read from mode 3's cases and mode 3's rule ids.
- `tests/test_167_mode_3_detector.py` — `modes_for_detector(...) == (3,)`, `split` read from mode 3, mode 3's edge count.
- `tests/test_174_split_sub_types.py` — `split` read from mode 3's cases, and the operator's `failure_mode`.
- `tests/test_176_fuse_bridged.py` — only if it pins mode 2's case set or status.
- `tests/test_186_expected_level_sequence.py` — a split case read from mode 3's cases.
- `tests/test_187_neighbour_contact_rule.py` — `modes_for_detector(...) == (3,)` and `split` read from mode 3.
- `tests/test_194_mode_1_catch_all.py` — the mode 2 and mode 3 `definition` prefixes and `split` read from mode 3.
- `tests/test_200_bar_condition_2.py` — any mode 2/3 condition subjects pinned from the old attribution.
- `tests/test_201_severity_ladder_remeasured.py` — the `split` ladder's `failure_mode`.
- `tests/test_100_severity_ladder.py` — the `split` ladder's home, if pinned.
- `tests/test_202_rule_table.py` — the `stray_contact` row's modes, if pinned as a literal.

**The reconciliation fence.** Every edit to an existing test is a moved
literal (mode 3 → 2 for `split` and `stray_contact`, a derived status or
rung, a count, a prefix), with a dated item-205 comment. No test is retired,
skipped, `xfail`-marked or loosened. `tests/test_151_stage30_validation.py`
and `tests/test_169_stage32_validation.py` are **not** edited: step 10's
amendments make them green. A red test in a file not listed here is a
hand-back to spec-author.

**Asserts against:**

- `tests/corpus/fixtures/**` — every fixture must regenerate byte-identical (A5); `tests/test_040_synthetic_corpus.py`'s regeneration tests compare them.
- `docs/aide/golden_evidence.generated.json` — no finding moves, so it must not move (A5).
- `tests/test_163_specificity_ratchet.py` — must stay green unedited (no firing moves).
- `tests/test_151_stage30_validation.py` — its AC35 reads step 10's Stage 30 amendment, and AC13/AC18 recompute both modes' status and rung.
- `tests/test_169_stage32_validation.py` — its AC6/AC7 read step 10's Stage 20 amendment.

**Correction (2026-09-30, validation round 1: spec-author, on the fence's
hand-back).** Three red tests fell outside the lists above. Each is a
consequence of the re-draw, not of a defect in the change, and each is
authorised below with the one edit it takes. The fence stands for every other
file. It is widened for two named edits that are not moved literals:
`tests/test_168_maintainer_sign_off.py`'s helper, and
`tests/test_145_eight_hypothesised_modes.py`'s co-detection test (Decisions,
2026-09-30). Values were measured on this branch on 2026-09-30 with the
builder's change in place.

- `tests/test_125_stage28_validation.py::test_ac15_agrees_with_test_057_pipeline_detectable_modes`
  and `tests/test_135_stage29_validation.py::test_ac25_agrees_with_test_057_pipeline_detectable_modes`
  compare `test_057`'s constant with the manifest's pipeline-detected modes
  that designate a rule, now `{1, 2, 3, 4, 6, 9}` (`split` designates
  `neighbour_contact` under mode 2). **Decision:** the constant is wrong, and
  the two comparisons are right. `tests/test_057_acceptance_stage7.py:94`'s
  `_PIPELINE_DETECTABLE_MODES` becomes `(1, 2, 3, 4, 6, 9)`, and one dated
  item-205 sentence is appended to its comment (L78–93) saying mode 2 rejoined
  through `split`. The earlier sentences stay. `test_125` and `test_135` are
  not edited. Measured consequences: `test_057`'s `test_ac9` for mode 2 reads
  `n_cases` 1 and sensitivity 1.0. `calibrate_thresholds` over
  `(1, 2, 3, 4, 6, 9)` with the AC13 axis returns a best candidate that is
  feasible.
- `tests/test_137_mode_less_rule_disposition.py::test_adv_measured_artifact_movement_counts_from_spec`:
  `mode2_count` is 5, not 4. The catalogue leaf
  `per_label.{label}.components.component_contacts[].contact_fraction` moves
  its `failure_modes` from `(3,)` to `(2,)`, joining the four `geometry.*`
  paths `(2, 3, 4)`. `len(entries)` stays 145. **Decision:** L935 becomes
  `assert mode2_count == 5`, with a dated item-205 comment beside item 193's.
  A `Re-measured (item 205, 2026-09-30)` paragraph is appended to the
  docstring, in the shape of the item 193 and item 194 paragraphs, recording
  mode2_count 4 → 5 and the reason. The L897 and L915 sentences are not
  rewritten: they record what items 193 and 194 measured.
- `tests/test_168_maintainer_sign_off.py::test_at_the_bar_claim_over_a_failing_mode`:
  `_first_non_qualifying_mode` returned 2 before this item. It now returns 3,
  the first mode failing `bar_conditions`, because modes 1 and 2 now clear
  the bar and 3 does not (A6). Mode 3 carries a shipped `MODE_SIGN_OFFS`
  record (`intermediate-state`, 2026-09-22), so the test's guard
  `claim.mode_id not in fm.MODE_SIGN_OFFS` fails. **Decision:**
  `_first_non_qualifying_mode` skips every mode id present in
  `fm.MODE_SIGN_OFFS`. The docstring and a dated item-205 comment say why: a
  constructed claim must never shadow a shipped record. The guard assertion
  stays unedited, and so does the `assert False` fallback. The first mode
  measured to fail the bar with no shipped record is 5. `MODE_SIGN_OFFS` is
  not touched (`gate-0133` owns it). AC9 is unaffected, because both shipped
  records are `intermediate-state`, not `at-the-bar`.

**May change:**

- `tests/test_057_acceptance_stage7.py` — `_PIPELINE_DETECTABLE_MODES` gains 2, plus one appended comment sentence.
- `tests/test_137_mode_less_rule_disposition.py` — `mode2_count` 4 → 5, a dated comment, and an appended docstring paragraph.
- `tests/test_168_maintainer_sign_off.py` — `_first_non_qualifying_mode` skips modes carrying a shipped sign-off.

**Asserts against:**

- `tests/test_125_stage28_validation.py` — its AC15 must go green unedited once `test_057`'s constant carries mode 2.
- `tests/test_135_stage29_validation.py` — its AC25 must go green unedited, for the same reason.

## Testing Strategy

The test module is `tests/test_205_mode_2_3_boundary.py`, with one test per
AC. AC1 computes the modes carrying `split` over every entry of
`SPECIFICATION`, never from mode 2 alone. AC2 calls `modes_for_detector`
live.

No adversarial cases: each AC is an equality over live state, so a test that
recomputes it has no vacuous branch to guard.

**Existing tests to reconcile.** A grep of `tests/` on 2026-09-30 for
`SPECIFICATION[2]`, `SPECIFICATION[3]`, `modes_for_detector("neighbour_contact"`,
`_EXPECTED_DERIVED_STATUS`, `_RULE_MODE_MAP` and `"neighbour_contact": (3,)`
found the files listed under May change. Known hits:

- `tests/test_103_feature_catalogue.py:615`: `"neighbour_contact": (3,)` → `(2,)`.
- `tests/test_145_eight_hypothesised_modes.py:127`: `2: "implemented"` → `"validated"`.
- `tests/test_147_specification_is_the_record.py:1233`: `2: "implemented"` → `"validated"`.
- `tests/test_167_mode_3_detector.py:334`, `tests/test_187_neighbour_contact_rule.py:275`:
  `== (3,)` → `== (2,)`.
- `tests/test_167_mode_3_detector.py:379`, `tests/test_187_neighbour_contact_rule.py:321`,
  `tests/test_166_split_operator.py:71`, `tests/test_174_split_sub_types.py:230`,
  `tests/test_186_expected_level_sequence.py:263`, `tests/test_194_mode_1_catch_all.py:273`:
  a `split` case looked up in `SPECIFICATION[3].corpus_cases` is looked up in
  `SPECIFICATION[2]`, where the test means `split` (a `split_own_label`
  lookup stays on mode 3).
- `tests/test_167_mode_3_detector.py:412`, `tests/test_166_split_operator.py:394`:
  mode 3's edges no longer include `neighbour_contact`; the pin moves to mode 2.
- `tests/test_194_mode_1_catch_all.py:228` and `:233`: the `definition`
  prefixes follow step 1's and step 2's new opening words.
- `tests/test_136_rule_mode_declarations.py` (~lines 330–356): the
  co-detection witness, re-measured.

The sweep was a grep, not a run. The builder treats any other red test that
pins `split`, `stray_contact` or `neighbour_contact` to mode 3, or mode 2's
old status or rung, as a hand-back to spec-author (the fence above).

**Correction (2026-09-30, validation round 1).** The hit list above is wrong
on one line. `tests/test_186_expected_level_sequence.py:263`
(`test_ac16_split_own_label_no_longer_fires_coverage`) looks up
`split_own_label`, not `split`, so it stays on `SPECIFICATION[3]`, as
`tests/test_174_split_sub_types.py:230` does. The list's own parenthesis
already said a `split_own_label` lookup stays on mode 3. The round-1 edit that
moved it to `SPECIFICATION[2]` is reverted, together with its item-205
comment. After the revert the file carries no item-205 change. The three
tests added under Authorised paths (same date) extend the list:
`tests/test_057_acceptance_stage7.py:94`,
`tests/test_137_mode_less_rule_disposition.py:935` and
`tests/test_168_maintainer_sign_off.py`'s `_first_non_qualifying_mode`.
`tests/test_145_eight_hypothesised_modes.py`'s
`test_ac13_co_detection_alone_does_not_validate` is reconciled as Decisions
records (2026-09-30), because it is not a moved literal.

## Validation

1. Regenerate (step 8), then read `docs/aide/failure_modes.generated.md`:
   - mode 2 reads `Status, derived (live): validated`, with the `bounds` and
     `neighbour_contact` edges and the cases `fuse_adjacent` and `split`;
   - mode 3 reads `validated` at rung `needs-real-data`, with the `bounds`
     edge alone and the case `split_own_label` alone;
   - both discriminators say that the label left covering only the remainder
     of an encroached vertebra has no mode yet, and neither calls the other
     mode "the converse".
2. In `docs/aide/rules.generated.md`, the `stray_contact` row's modes column
   reads `2`.
3. Open `docs/aide/corpus_sheet.png` and check that the `split` panel's title
   reads `failure / 2`.
4. Replay `split` through the CLI:

   ```
   .venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/split_seg.nii.gz --out <tmp> --no-reference
   ```

   `--no-reference` is needed for the reason `CLAUDE.md` gives: the bundled
   VerSe reference is not calibrated for the synthetic corpus. Check that
   `<tmp>/segfacet_report.json`'s `findings` hold exactly one
   `neighbour_contact` finding on label 24, unchanged by this item.
5. Run `python .aide/scripts/aide.py status` and confirm that Stages 20 and
   30 show step 10's amendments.

No environment profile is needed.

## Dependencies

- Item 200: made `bar_conditions`' condition 2 existential and
  detector-granular, which step 9 records (✅).
- Item 202: the generated rule table that step 8 regenerates (✅).

**Downstream:**

- Items 206 and 208 each need this item. Item 206 adds a second full-body
  mode-2 fixture, and item 208 adds mode 3's own detector, which moves
  `bar_conditions(3)` conditions 3 and 4. If item 208 puts that detector on
  the `neighbour_contact` rule, it moves `NeighbourContactRule`'s declared
  modes to `(2, 3)`; AC2 here stays true, because it is detector-granular.
- Item 203 re-measures `bar_conditions(2)` and `(3)` for its decision brief
  after items 205–208.

## Decisions & Trade-offs

Implemented 2026-09-30.

- **Bar conditions, re-measured live on the real change (2026-09-30).**
  - Mode 2: conditions 1-5 all met. Condition 2 subjects `("split",)`;
    condition 3 `("per_label.{label}.components.component_contacts[].contact_fraction",)`;
    condition 4 `("neighbour_contact/stray_contact",)`; condition 5
    `("validated",)`.
  - Mode 3: conditions 1, 2 and 5 met; 3 and 4 not met. Condition 2 subjects
    `("split_own_label",)` (through the `bounds` proxy pair); condition 3 and
    4 subjects `()`; condition 5 `("validated",)`. The loss is expected until
    item 208.
  - `specification_conflicts()` returns `()` after regeneration; every corpus
    fixture regenerated byte-identical (only `manifest.json` moved) and a
    fresh `golden_evidence` run is byte-identical to the committed copy.
- **Mode 2 and 3 `definition` openings** (pinned by
  `tests/test_194_mode_1_catch_all.py`, reconciled): mode 2 opens "One label
  covers its own ground-truth vertebra plus part or all of an adjacent one:",
  mode 3 opens "Part of a ground-truth vertebra carries a label of its own,".
- **Reconciled beyond the spec's hit list**: `tests/test_167_mode_3_detector.py`
  AC11 read mode 3's bar conditions 1-5; it now reads mode 2's, the mode that
  owns the edge (inside the listed file, a moved literal). `tests/test_174_split_sub_types.py`
  and `tests/test_176_fuse_bridged.py` needed no edit.

- **The queue's rule-granular testable is kept at detector granularity.**
  "Mode 3's intended rules no longer name `neighbour_contact`" would forbid
  item 208 from adding mode 3's own detector to that rule, which the queue
  leaves open. AC2 says what the re-draw needs: `stray_contact` serves
  mode 2 alone.
- **Left open:** a mode for the label left covering only the remainder of an
  encroached vertebra, and how it would be labelled. The maintainer deferred
  it at `gate-51da` as outside the prototype goal (`insights.md`, queue-027,
  2026-09-30). Until then the only trace of that label is `stray_contact`'s
  message, which names it as the merge candidate.
- **`test_145`'s co-detection test is re-pointed onto a probe (spec-author,
  2026-09-30, validation round 1).**
  `tests/test_145_eight_hypothesised_modes.py::test_ac13_co_detection_alone_does_not_validate`
  pins the `derive_status` branch where every case agrees but none fires the
  mode's own rules, so the mode reads `implemented`, not `validated`. Live
  mode 2 carried that branch through `fuse_adjacent`. `split` now lifts it to
  `validated`. No live mode carries the branch, as measured on this branch on
  2026-09-30: modes 10, 11 and 15 are `implemented` with no corpus case, and
  mode 6 is `specified`, with no intended rule. So the test asserts over a probe,
  `dataclasses.replace(SPECIFICATION[2], corpus_cases=<mode 2's cases whose case_id is "fuse_adjacent">)`,
  with its existing loop and disjointness assertions unchanged. It then asserts
  `fm.derive_status(probe) == "implemented"`, and a guard that the probe holds
  exactly one case. Measured: `"implemented"`, one case. The docstring gains a
  dated item-205 sentence saying why the probe replaced the live mode. The
  suggested extra assertion that live mode 2 is `validated` is not added:
  `_EXPECTED_DERIVED_STATUS[2]`, reconciled to `"validated"` in the same file,
  already pins it. This is the one edit to `test_145` that is not a moved
  literal. The fence is widened for it here, and for `test_168`'s helper under
  Authorised paths (same date). Nothing else in the fence changes.
