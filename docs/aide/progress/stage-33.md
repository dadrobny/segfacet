> Stage 33's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 33`, run on the main or queue branch, moves it back.

## Stage 33 — Corpus & Rule Re-grounding: modes 2 and 3 to the bar (G2, G7, G8) — ✅

**Goal.** Rebuild the geometric corpus base as a lordotic L1–L5, re-author the fixtures that
do not express their mode, re-home the rules the queue-022 review named (`insights.md`,
entries dated 2026-09-22), and bring **modes 2 and 3** to an **at-the-bar** sign-off. That
sign-off closes Stage 32's criterion 1 as well as this stage. Mode 6 is re-grounded but
not driven to the bar. Vertebra-local extents are Stage 27's. (Scoped on 2026-09-22 for
modes 3 and 4; re-targeted to 2 and 3 at `gate-51da`, 2026-09-30, when the mode 2/3
boundary was re-drawn and mode 4 left the stage. Title corrected 2026-10-03.)

**Deliverables.**

- ✅ **D0** Protective fix: session-scoped `aide check` and specification-regeneration
  fixtures, so the suite runs each once per session. *(Item 170)*
- ✅ **D0** Protective fix: literal negative controls rebuilt from live values, so a
  corpus change cannot make a "wrong" literal coincide with the live one. *(Item 171)*
- ✅ **D0** Protective fix: `UNUSED_OPERATOR_REASONS` entries validated against the
  operator registry and `CASE_RECIPE`. *(Item 172)*
- ✅ **D1** The lordotic geometric base (per-level sagittal tilts L1–L5), with both
  manifests and every generated artifact regenerated. *(Item 173)*
- ✅ **D1** A committed corpus rendering (`docs/aide/corpus_sheet.png`, stale-checked
  against the manifest and fixtures), with the 2026-09-22 prototype absorbed and
  deleted. *(Item 178)*
- ✅ **D1** The status report's corpus section re-keyed off the generated
  specification. *(Item 179)*
- ✅ **D2** `split` at a ~20 % cap, plus a new `split_own_label` case for mode 3's
  second sub-type. *(Item 174)*
- ✅ **D2** A new `crop_fov_si` case, a true S-I field-of-view crop of the volume; the
  legacy anterior `crop_at_border` case is kept unchanged for `border` coverage.
  *(Item 175)*
- ✅ **D2** `fuse_adjacent` bridged into one component and L5 renumbered.
  *(Item 176)*
- ✅ **D2** `displace` moves mostly left-right (14 voxels right, 5 anterior).
  *(Item 177)*
- ✅ **D2** `force_overlap` retired or declared multi-channel, and `fragment` parked.
  Resolved 2026-09-28: the fixture, operator and ladder were removed, and the `overlap`
  rule stays, declared to need multi-channel input; mode 15 derives `implemented`, with
  no fixture claiming it. `fragment` stays parked as mode 1's catch-all case. The
  2026-09-24 park was superseded by the maintainer on 2026-09-25. *(Item 195)*
- ✅ **D3** The expected level sequence admits per-section vertebra counts
  (`CANONICAL_ORDER` transitional variants).
  *(Item 186)*
- ✅ **D3** `neighbour_contact` becomes a rule of its own, serving mode 3.
  *(Item 187)*
- ✅ **D3** `coverage` re-homed from mode 6 to mode 10.
  *(Item 188)*
- ✅ **D3** `mislabel`'s `spline_offset` moves to a displaced-vertebra condition.
  *(Item 189)*
- ✅ **D3** A condition-keyed bucket in the eval harness.
  *(Item 190)*
- ✅ **D3** A condition-flagged label is excluded from every rule that does not opt in.
  *(Item 191)*
- ✅ **D3** `sequence` reports which sub-type it saw.
  *(Item 192)*
- ✅ **D3** `reference_delta` and `intensity_reference_delta` claim no mode as their own.
  *(Item 193)*
- ✅ **D3** Mode 1 attributed only as the catch-all, with the review's vocabulary.
  *(Item 194)*
- ✅ **D3** `force_overlap` removed: operator, corpus case, ladder entries and mode-15
  corpus attribution (maintainer, 2026-09-25, superseding the 2026-09-24 park).
  *(Item 195)*
- ✅ **Maintenance** `segfacet evaluate` reports a `FacetInputError` as an error, not a
  traceback. *(Item 180)*
- ✅ **Maintenance** Vacuous reference-backed tests in `test_049` and `test_090` made
  discriminating on the lordotic base. *(Item 181)*
- ✅ **Maintenance** The catalogue's corpus-derived rule→mode map read from the committed
  cases. *(Item 182)*
- ✅ **Maintenance** Bridged `fuse` fills each column in its own order. *(Item 183)*
- ✅ **Maintenance** `test_155`'s zero-comparison scan covers membership, chained and
  `bool(...)` shapes. *(Item 184)*
- ✅ **Maintenance** `committed_artifact_guard` resolves the `dirname(abspath(__file__))`
  root idiom. *(Item 185)*
- ✅ **Maintenance** Stale prose after items 189, 190 and 195 brought up to date.
  *(Item 196)*
- ✅ **Maintenance** `test_155`'s zero-comparison scan covers truthiness and ordering
  shapes. *(Item 197)*
- ✅ **Maintenance** `mislabel`'s `ordering` detector judges order along the expected
  sequence. *(Item 198)*
- ✅ **Maintenance** Positional gate and insight citations in the records rewritten to
  IDs. *(Item 199)*
- ✅ **D4** The bar checker's condition 2 made existential and detector-granular.
  *(Item 200)*
- ✅ **D4** The severity-ladder constants re-measured, including the split operators.
  *(Item 201)*
- ✅ **D4** A generated `docs/aide/rules.generated.md`. *(Item 202)*
- ✅ **D5 re-plan** The mode 2/3 boundary re-drawn: mode 2 keeps the paired case,
  mode 3 becomes the own-label fragment, and `stray_contact` and `split` move to
  mode 2. *(Item 205)*
- ✅ **D5 re-plan** A geometric corpus case for one label over two full, separate
  vertebrae. *(Item 206)*
- ✅ **D5 re-plan** Mode 2's fused-label detector, from size and centroid spacing.
  *(Item 207)*
- ✅ **D5 re-plan** Mode 3's own detector, from whole-label contact fraction and small
  size. *(Item 208)*
- ✅ **D5** Modes 2 and 3 signed by the maintainer at the bar (human gate gate-0133, re-scoped from modes 3 and 4 when gate-51da was declined on 2026-09-30), with the outcome written to `MODE_SIGN_OFFS`. *(Item 203)*
- ✅ **D6** Stage validation from a clean clone, re-running Stage 32's D3 and attesting
  Stage 32's criterion 1. *(Item 204)*

**Acceptance.**

- [x] Modes 2 and 3 each meet all six conditions of Stage 32's "fully specified end to end", checked against live state on the lordotic corpus. Each carries a maintainer sign-off at `outcome="at-the-bar"`, or a recorded reason why it does not (**G2**). Re-targeted from modes 3 and 4 when gate-51da was declined (2026-09-30); mode 4 keeps its gate-bb24 intermediate-state sign-off. *(Item 204 AC3, replayed in a fresh clone at commit e0c17ab3ad292735280e26f9251146c3a87bc4d8: modes 2 and 3 each return met True for all five records of traceability.bar_conditions (conditions 1-5), and each carries mode_sign_off outcome at-the-bar dated 2026-10-02 (gate-0133, item 203), which is condition 6. Mode 4 keeps its 2026-09-22 intermediate-state sign-off and is not asked for here. tests/test_203_modes_2_and_3_signed_at_the_bar.py and tests/test_168_maintainer_sign_off.py::test_ac9_at_the_bar_claims_are_cross_checked_against_live_state pass in the clone.)*
- [x] No committed corpus case is attributed to a mode or condition that its label map does
  not express, and every case's measured firing equals its expected set, across both
  corpora (**G2**, **G7**). *(Item 204 AC4 and AC5, replayed in a fresh clone at commit e0c17ab3ad292735280e26f9251146c3a87bc4d8. AC4: tests/test_163_specificity_ratchet.py passes in full (24 passed); traceability.build_matrix().conformance drives 18 cases (14 geometric, 4 intensity), equal to the union of both committed manifests case_id values, with 18 agreeing and 0 whose agrees is False, unspecified_cases (). AC5, read as item 204 A1 defines it (a judgement nothing computes, so attested on three facts): failure_modes.specification_conflicts() returns (); each 2026-09-22 review finding is resolved live (crop_at_border is a fov_truncation condition case, item 175; fuse_adjacent fused label is one connected component, item 176; force_overlap is absent from both manifests, item 195; split is attributed to mode 2 and split_own_label to mode 3, item 205); and every committed case has a dated decision record behind its attribution, tabulated in the item 204 spec. tests/test_175_crop_fov_si.py, test_176_fuse_bridged.py, test_195_force_overlap_removed.py, test_205_mode_2_3_boundary.py and test_206_fuse_separate_fixture.py pass in the clone (58 passed). The legacy crop_at_border remains a translate-then-clip (item 175 Left open), attributed to fov_truncation by the maintainer's 2026-09-24 decision.)*
- [x] No rule declares a mode through a detector that reads another mode's signal. Condition
  4 of the bar is checked mechanically at detector granularity (**G2**, **G8**). *(Item 204 AC6, replayed in a fresh clone at commit e0c17ab3ad292735280e26f9251146c3a87bc4d8, read as item 204 A2 defines it (no computed predicate for reads another mode's signal, so attested against the detectors the review re-homed). tests/test_164, 187, 188, 189, 192, 193, 194, 200, 202 and 205 pass in the clone (125 passed). modes_for_detector over all 27 registered detectors: fragmentation/components (1) and fragmentation/islands (4), neither serving 2 or 3; neighbour_contact/stray_contact (2), re-drawn from mode 3 by gate-51da; fused_label/fused_label (2); split_fragment/split_fragment (3); the three coverage detectors (10); mislabel/ordering (9); sequence/swap and sequence/shift (9); sequence/skip (10); sequence/transitional (11), no sequence detector serving 12; spline_offset/spline_offset (); every reference_delta and intensity_reference_delta detector (). bounds/metric_out_of_range serves 2, 3 and 4 as a recorded proxy. Condition 4 subjects are fused_label/fused_label and neighbour_contact/stray_contact for mode 2, split_fragment/split_fragment for mode 3; none names a PROXY_RULE_IDS rule. The regenerated rules.generated.md equals the committed file byte for byte.)*
- [x] A label map holding both T12 and L1, and no T13, produces no missing-level finding
  (**G2**). *(item 186 AC2 (test_ac2_t12_map_no_coverage_finding, tests/test_186_expected_level_sequence.py): full suite run 2026-09-27, 9330 passed, 72 env-gated skips; T12 map produces no coverage finding)*
  - **2026-10-02** → Item 204 AC7 and AC8, replayed in a fresh clone at commit e0c17ab3ad292735280e26f9251146c3a87bc4d8: tests/test_204_stage33_validation.py and tests/test_186_expected_level_sequence.py::test_ac2_t12_map_no_coverage_finding pass (3 passed). The six-block T12, L1-L5 map (labels 19-24, no 28) has relationships.missing_levels == [] and run_rules under bundled_default_config returns six findings, all (border, unexpected_clip); none comes from a detector serving mode 6 or 10 (the three coverage detectors and sequence/skip, derived from the live registry), so no missing-level finding.
- [x] The detection count is re-stated in `progress.md` per lifecycle status and per rung,
  as measured numbers with what they were measured on (**G7**). *(Item 204 AC9, measured in a fresh clone at commit e0c17ab3ad292735280e26f9251146c3a87bc4d8 from segfacet.failure_modes (SPECIFICATION, derive_status, derive_mode_rung, a rung of None counted as none): derived status counts over 16 modes: validated 6, implemented 3, specified 2, proposed 5. derived mode rung counts: synthetic-demonstrable 6, needs-real-data 2, structurally-unobservable 1, none 7.)*
