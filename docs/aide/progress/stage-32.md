> Stage 32's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 32`, run on the main or queue branch, moves it back.

## Stage 32 — Selected-Mode Refinement: one failure mode fully specified end to end (G2, G7, G8) — ✅

**Goal.** The specification documents all sixteen modes without committing to implement
them (2026-09-15: validated 1, 4, 6, 9, 15, 16; implemented 2, 3, 8; proposed 5, 7,
10–14). This stage refines **maintainer-selected** modes, interactively, until **at least
one** is fully specified end to end — the pipeline's MVP. A mode counts when its entry is
complete and confirmed, a committed synthetic fixture expresses it with an agreeing
expected set naming one of its own rules, the features that detector reads are extracted
and catalogued, a detector deciding it serves no other mode (`bounds` / `reference_delta`
do not count), its status derives `validated`, and the maintainer has signed it off. Every
other mode stays documented at its derived status and may be refined individually, when and
where wanted, in any later queue. The per-mode menu of known inputs is in
[`roadmap.md`](../roadmap.md) and is not a commitment.

**Deliverables.**

- ❌ **D0** Stage 20's deferred exercise-reporting (per rule and per operator) and
  specificity-ratchet deliverables (allowlist derived from each case's `expected_firing`)
  re-specified against the specification and built at the head of the first queue; they
  stay tracked by their Stage 20 bullets. *(2026-10-02, resolved by hand: the work shipped as #162 and #163, both ✅ under Stage 20, so this bullet tracks nothing of its own.)*
- ✅ First-class detector ids on multi-detector rules, referenced by the
  specification's intended-rule edges, so "a detector serves no other mode" is
  checked mechanically (prerequisite of D1's condition 4). *(Item 164)*
- ✅ **D1** The MVP mode: at least one maintainer-selected mode brought to the
  fully-specified bar and signed off. Selected 2026-09-18: mode 4 (islands). *(Item 165)*
- ✅ **D2** Further selected modes, optional: refined as far as wanted and signed off at their
  queue's checkpoint, to the bar or to a recorded intermediate state. Selected
  2026-09-18: mode 3 (split) — its split operator and corpus case. *(Item 166)*
- ✅ **D2** Mode 3's own feature and detector, or its recorded intermediate state. *(Item 167)*
- ✅ **D1/D2** Maintainer sign-off of modes 3 and 4 at the queue's human gate, recorded
  with date and outcome in the specification module. *(Item 168)*
- ✅ **D3** Stage 20 closed (its deferred validation deliverable) and this stage validated
  at the end of the last queue: artifacts regenerated from a clean tree, the specificity assertion driven over
  every corpus case, the detection count recorded per status and rung, naming the modes
  refined and those left as documented drafts.
  - **2026-10-17** → item 204 taken off this bullet's marker by item 236: item 204 delivered this re-run as Stage 33's D6 bullet, which carries its marker.

**Acceptance.**

- [x] At least one mode in the specification meets all six conditions of "fully specified
  end to end" in [`roadmap.md`](../roadmap.md), each checked against live state: the committed
  fixture's measured firing agrees with its expected set, the deciding detector serves no
  other mode, and the status derives `validated` (**G2**). *(not attested 2026-09-22, item 169: modes 3 and 4 both carry a maintainer sign-off dated 2026-09-22 at outcome="intermediate-state", not "at-the-bar"; conditions 1-5 hold live for both (recomputed via `traceability.bar_conditions`), but condition 6 requires an "at-the-bar" sign-off, so no mode meets all six conditions and the set of modes at the bar is empty)* *(Item 204 AC3 supersedes the not-attested-2026-09-22 note on this box: recomputed in a fresh clone at commit e0c17ab3ad292735280e26f9251146c3a87bc4d8 (own venv, segfacet.__file__ resolves under the clone), modes 2 and 3 each meet all six conditions. traceability.bar_conditions(mode_id) returns met True for conditions 1-5 of both (mode 2 condition 4 subjects: fused_label/fused_label, neighbour_contact/stray_contact; mode 3 condition 4 subject: split_fragment/split_fragment; neither names a PROXY_RULE_IDS rule), and mode_sign_off gives date=2026-10-02, outcome=at-the-bar for both (gate-0133, item 203). Recomputed over all 16 modes in SPECIFICATION, the set at the bar is exactly 2 and 3. tests/test_203_modes_2_and_3_signed_at_the_bar.py and tests/test_168_maintainer_sign_off.py::test_ac9_at_the_bar_claims_are_cross_checked_against_live_state pass in the clone (7 passed with the sheet-digest check, 0 skipped).)*
- [x] Every mode this stage refined carries a maintainer sign-off with date and outcome in
  the specification module (**G8**). *(Item 169 AC11: tests/test_168_maintainer_sign_off.py and tests/test_165_mode_4_at_the_bar.py pass in full in the clean clone (18 + 11 = 29 passed), clone commit 2c4b62bcf2dcad5f37ec88273a74eae432b06df2. sorted(MODE_SIGN_OFFS) == [3, 4], matching the modes queue-022 selected for refinement (mode 3 split, mode 4 islands). Mode 3: date=2026-09-22, outcome=intermediate-state. Mode 4: date=2026-09-22, outcome=intermediate-state.)*
- [x] Every mode not refined keeps a complete specification entry and is reported at its
  derived status in `docs/aide/failure_modes.generated.md`; a mode left at `proposed`,
  `specified` or `implemented` is an accepted end state, and a mode with no entry or no
  status is not (**G2**). *(Item 169 AC12: tests/test_151_stage30_validation.py::test_ac3_every_mode_row_title_authored_status_and_edge_rungs_match_specification and ::test_ac18_status_matches_independent_recomputation_and_committed_rendering pass in the clean clone (2 passed), clone commit 2c4b62bcf2dcad5f37ec88273a74eae432b06df2. Every one of the 16 SPECIFICATION modes appears in docs/aide/failure_modes.generated.md at its derived status (validated 7, implemented 2, proposed 7); none renders without a status.)*
- [x] The specificity assertion is enforced for every corpus case across both corpora, and
  every registered rule and operator is exercised by a case or recorded as unexercised with
  a reason (**G2**, Stage 20 criteria 3–4). *(Item 169 AC3/AC4: tests/test_163_specificity_ratchet.py (22 passed) and tests/test_162_corpus_exercise_report.py (18 passed) pass in full in the clean clone, clone commit 2c4b62bcf2dcad5f37ec88273a74eae432b06df2. Specificity: 16/16 committed corpus cases (12 geometric + 4 intensity) agree, 0 disagreements. Exercise: 10 registered rules -- 7 exercised, 3 unexercised with reason (bounds, reference_delta, intensity_reference_delta, all needs-real-data); 12 registered operators, all used; both DirectionReports read complete=True, holes=().)*
- [x] The end-to-end detection count is recorded here per lifecycle status and per evidence
  rung, as measured numbers with what they were measured on, naming the modes refined and
  the modes left as documented drafts (**G7**, Stage 20 criterion 5). *(Item 169 AC6-AC8, measured live from segfacet.failure_modes in the clean clone, clone commit 2c4b62bcf2dcad5f37ec88273a74eae432b06df2: derived status counts over 16 modes: validated 7, implemented 2, specified 0, proposed 7. derived mode rung counts: synthetic-demonstrable 6, needs-real-data 2, structurally-unobservable 1, none 7. modes refined by stage 32: 3, 4; at the fully-specified bar: none; left as documented drafts: 14.)*
  - **2026-10-02** → Item 204 AC10 re-runs Stage 32 D3 on the re-grounded corpus, read live from segfacet.failure_modes in a fresh clone at commit e0c17ab3ad292735280e26f9251146c3a87bc4d8 (the 2026-09-22 clause above stands as the record of that date): derived status counts over 16 modes: validated 6, implemented 3, specified 2, proposed 5. derived mode rung counts: synthetic-demonstrable 6, needs-real-data 2, structurally-unobservable 1, none 7. modes refined by stages 32 and 33: 2, 3, 4; at the fully-specified bar: 2, 3; left as documented drafts: 13.

> **Criterion 1 moves with Stage 33** *(2026-09-22)*. Gate `gate-bb24` signed modes 3 and 4 off at a
> recorded intermediate state, and the review behind that outcome is Stage 33's scope.
> Stage 33's closing validation re-runs D3 on the re-grounded corpus and attests criterion
> 1 here. So D3 stays 📋 until then, even though item 169 ran it once on queue-022's
> corpus. A ✅ on D3 would roll this stage up to ✅ with criterion 1 unmet.
