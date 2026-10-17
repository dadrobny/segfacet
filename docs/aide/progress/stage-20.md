> Stage 20's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 20`, run on the main or queue branch, moves it back.

## Stage 20 — Failure-Mode ↔ Feature ↔ Rule Traceability & Specificity Harness (G2, G7) — ✅

**Goal.** Close the gap between "the suite is green" and "the rules are specific".
Measured 2026-07-25 on the committed corpus: **10 rules registered and enabled, 4 ever
fire**; `bounds`, `mislabel`, `overlap`, `intensity`, `reference_delta` and
`intensity_reference_delta` fire on **zero** cases. **3 of 9 cases fire nothing at all**
through `run_qc` — their intended rule is reachable only via a hand-reconstructed record
(item 040's documented limitation), so **3 of 8 failure modes are not detected
end-to-end** while the corpus reads as covering all eight. Separately, `verify_case`
never asserts that *no other* rule fires; cross-talk is 0/9 today, so the assertion is
free to adopt now and expensive later.

**Scope clarified 2026-08-11** (full statement in
[`roadmap.md`](../roadmap.md)). The matrix is read in three directions and only two must ever
be complete: **mode → rule** (complete, always — an uncovered §6 mode is a defect) and
**rule → mode** (complete, always — a rule targeting no catalogued mode is itself a
finding; four rules sit there today). **Feature → rule is deliberately incomplete**: the
record is an over-broad vector rules *select from*, so a leaf path no rule reads is
inventory (`unwired`), not a gap — 34 of 111 catalogued paths, and that is an expected
steady state, not a shortfall. Each mode also carries an **evidence rung**:
synthetic-demonstrable · needs real data · structurally unobservable in single-channel
input (mode 8). Modes, rules and features grow **in tandem** — a new mode arrives with its
rule(s) and any features they need; features may be added alone, modes and rules may not.

**Deliverables.**

- ✅ Traceability matrix, *generated* (not hand-maintained): 8 failure modes × 10 rules ×
  the features each rule consumes, scored in all three directions, every mode row carrying
  its evidence rung. *(Item 138)*
- ✅ Rule-layer declaration seam: every registered rule carries a `RuleModeDeclaration`
  stating its targeted §6 modes, its mode-less reason, or a pending reason. Six rules
  declared from corpus evidence; the four contested ones are **pending**, their disposition
  deliberately left to item 137. Does not itself close Stage 19's G8 shortfall. *(Item 136)*
- ✅ The four mode-less rules (`bounds`, `intensity`, `reference_delta`,
  `intensity_reference_delta`) mapped to §6 modes, or recorded as targeting none with a
  reason — the root close of Stage 19's G8 shortfall. *(Item 137)*
- ❌ Specificity assertion — no unintended rule may fire — adopted as a ratchet.
  ⚠️ **Deferred, 2026-09-03:** queue-019 was cut short after item 138. The ratchet's first
  real case is mode 6's corpus case firing `mislabel` alongside `border` (measured
  2026-09-03), and whether that is a true positive or cross-talk is not decidable before
  the §6 modes carry a definition and a discriminator. See
  [`failure-mode-taxonomy-handover.md`](../failure-mode-taxonomy-handover.md) §4.2.
  ❌ **Number retired, 2026-09-18:** the deliverable is re-queued as item 163. *(Item 140)*
- ✅ Specificity assertion — no unintended rule may fire — as a ratchet whose allowlist is
  each corpus case's `expected_firing` in the specification (Stage 32 D0). *(Item 163)*
- ✅ Reachability hole closed *with its mechanism named per mode*: mode 8 is
  single-channel-unobservable, mode 1's ladder is FOV-capped, mode 4's cause TBD. Made
  detectable where the mechanism allows, recorded where it does not. Not both silent.
  ⚠️ **Superseded in part, 2026-08-27:** modes 1 and 4 are **one** defect, the interpolating
  spline fit (`splprep(..., s=0)`), and are owned by **Stage 28**. `offset_mm` is zero on
  every committed golden (max `6.8e-04` mm vs a 15.0 mm threshold) and on real VerSe GT
  (mean `2.9e-05` mm), so no field of view produces a non-zero offset and the FOV-headroom
  remedy named here could not have worked. Mode 8 stays this stage's to record. *(Item 138)*
- ❌ Per-rule **and per-operator** corpus-exercise reporting (the registered `fuse` operator
  generates no corpus case at all).
  ⚠️ **Deferred, 2026-09-03:** queue-019 was cut short after item 138. The item's spec was
  authored and is preserved at [`items/139-per-rule-and-per-operator.md`](../items/139-per-rule-and-per-operator.md),
  including its measurements: the `fuse` claim above holds, 7 of 10 rules are exercised
  across both corpora, and `intensity_reference_delta` is driven by nothing because no
  harness attaches a reference. Its "unexercised, with reason" records need a mode
  specification first. See
  [`failure-mode-taxonomy-handover.md`](../failure-mode-taxonomy-handover.md) §9.
  ❌ **Number retired, 2026-09-18:** the deliverable is re-queued as item 162. *(Item 139)*
- ✅ Per-rule and per-operator corpus-exercise report across both corpora, re-authored
  against the signed-off specification (Stage 32 D0). *(Item 162)*
- ❌ The mode-1 severity-ladder base (`tests/test_100_severity_ladder.py`, Stage 18)
  widened so mode 1's metric swing is set by the
  perturbation rather than the fixture's FOV walls — the recorded root cause of mode 6's
  Stage-18 specificity shortfall.
  ⚠️ **Deferred, 2026-09-03:** queue-019 was cut short after item 138. This turns on
  mode-1-vs-mode-6 semantics, which is the discriminator field the §6 modes do not yet
  carry. See
  [`failure-mode-taxonomy-handover.md`](../failure-mode-taxonomy-handover.md) §4.1.
  **Landed as item 154, 2026-09-22 (item 169):** the ladder margins and mode-1 anchor
  were re-measured in [item 154](../items/154-re-measure-the-ladders-and-mode-1s-anchor.md)
  as Stage 31's eval-harness re-key, so this bullet is superseded rather than shipped
  under its own number. *(Item 141)*
- ❌ Stage 20 end-to-end validation: traceability artifact regenerated from a clean tree,
  the specificity assertion driven over every corpus case, the cross-mode margins
  re-measured, and the end-to-end detection count stated honestly here.
  ⚠️ **Deferred, 2026-09-03:** queue-019 was cut short after item 138. Stating the
  detection count honestly requires a mode↔rule story that is not yet defined. See
  [`failure-mode-taxonomy-handover.md`](../failure-mode-taxonomy-handover.md).
  ❌ **Number retired, 2026-09-18:** the deliverable is re-queued as item 169. *(Item 142)*
- ✅ Stage 20 end-to-end validation, run with Stage 32's own at the close of queue-022
  (Stage 32 D3). *(Item 169)*

> **Why those four now read ⏸️ rather than 📋** *(queue-020 boundary,
> 2026-09-03)*. Their prose had said Deferred since 2026-09-03 while their status
> icon still said Planned, so queue-019 stayed derived-open and
> `aide claim --dry-run` offered item 139 — the very item held pending Stage 30's
> sign-off. The icon now agrees with the prose. **Items 139–142 keep their
> numbers**; they are re-specified against Stage 30's specification and return to
> 📋 in the queue that follows item 150's sign-off. Stage 20 itself stays 🚧.
>
> **The flip adds one expected `aide check` warning**: *"stage 20: all
> deliverables ✅ but summary shows in-progress — … close the stage"*.
> `rollup_status` counts ⏸️ as terminal alongside ✅ and ❌, so a stage paused
> mid-flight reads as shipped. **Do not act on that advice** — Stage 20 is not
> complete, and its summary row stays 🚧. Captured as a `framework` insight
> (`insights.md`, queue-020, 2026-09-03) for hand-over to `aide-loop`; it is
> part of the warning baseline from this date, not a new finding for an item to
> chase.
>
> **2026-09-16, engine 1.52.1** — the `rollup_status` defect was fixed upstream in
> engine 1.41.0 (aide-loop#173): a ⏸️ deliverable no longer rolls its stage up. The
> summary row and this section's heading, which `aide progress set 143` had flipped
> to ✅ on 2026-09-03, are restored to 🚧 (Stage 31 D0), and the warning above is no
> longer part of the baseline — under the new engine that mis-shape is an error.

> **Where the four held items go after Stage 30's sign-off** *(roadmap v3.1,
> 2026-09-15)*. Stage 20's remainder is not re-queued as a stage of its own:
> items **139** (exercise reporting) and **140** (specificity ratchet, allowlist
> derived from the specification's expected firing sets) are re-specified and
> built at the **start of Stage 32**; item **141** (mode-1 ladder base) moves to
> **Stage 31**'s eval-harness re-key; item **142** (this stage's validation) runs
> at **Stage 32's close**, stating the detection count as of that date. The four
> bullets above keep ⏸️ until their items are queued. "Every §6 failure mode"
> in the acceptance below is read as every specification entry at `implemented`
> or above, with `proposed` entries reported as unimplemented; mode numbers in
> this section's text are the pre-sign-off ids (mapping in Stage 30's note).

> **Items 139, 140 and 142 re-queued under new numbers** *(queue-022,
> 2026-09-18)*. The deliverables return to 📋 as the 2026-09-03 note above said
> they would, but not under the old numbers — the old bullets read ❌ (number
> retired, not deliverable dropped) and a new 📋 bullet follows each: `aide check` reports an item
> number declared in two queues as an error, and all three are declared in
> queue-019. So **139 → 162** and **140 → 163** lead
> [`queue/queue-022.md`](../queue/queue-022.md), and **142 → 169** closes it. This
> supersedes "keep their numbers" above.
> Item 141's bullet was resolved ❌ on 2026-09-22 by item 169 — its work landed
> in Stage 31 as [item 154](../items/154-re-measure-the-ladders-and-mode-1s-anchor.md)
> and is not re-queued.

**Acceptance.**

- [x] Every §6 failure mode has ≥1 rule **and** a recorded evidence rung — never silent *(Full suite run 2026-09-02 (.venv/bin/python -m pytest -q): 6900 passed, 60 skipped (all pre-known env-gated), 0 failed; test_ac1_all_ten_rules_declared_and_not_pending passed)* *(Validation round 2, 2026-09-02: .venv/bin/python -m pytest -q -> 7006 passed, 60 skipped (all pre-known env-gated), 0 failed. Verified mode->rule direction directly: json.load(traceability_matrix.generated.json)['directions']['mode_to_rule'] == {complete: True, holes: []}; every one of the 8 mode rows in the generated markdown carries a rung (synthetic-demonstrable x6, structurally-unobservable for mode 8). Covered by test_ac10_mode_to_rule_direction_complete_and_every_mode_has_a_rule, test_ac11_mode_rule_lists_are_derived_from_shipped_declarations, test_ac12_mode_rung_is_member_of_closed_vocabulary, test_ac13_mode8_rung_and_mechanism_name_the_single_channel_mechanism, test_ac14_mode8_not_pipeline_detected_names_reconstructed_case, test_ac15_rung_and_pipeline_detected_cross_check, test_ac16_modes_one_and_four_are_synthetic_demonstrable, test_ac17_mode7_rung_records_its_own_cap (item 138).)*
  - **2026-09-02** → retracted: Retracting an attestation-mapping error: this criterion (every mode has >=1 rule and a recorded evidence rung) requires the mode->rule direction with evidence rungs, which is Item 138's traceability-matrix deliverable (still open, marked pending in this stage's Deliverables); item 137 only disposed the four previously-undeclared rules, it did not build the evidence-rung matrix.
  - **2026-09-03** → Correction (code review): the rung enumeration omitted mode 7's needs-real-data rung from the 8-mode accounting -- it read 8 modes as (synthetic-demonstrable x6, structurally-unobservable for mode 8) = 7 accounted, not 8. Corrected reading: synthetic-demonstrable x6 (modes 1-6), needs-real-data x1 (mode 7), structurally-unobservable x1 (mode 8) = 8. The underlying claim (every mode has >=1 rule and a recorded evidence rung) is unaffected and remains true; only the evidence note's own arithmetic was wrong.
  (**G2**).
- [x] Every registered rule maps to ≥1 §6 mode or is recorded as mode-less with a reason. *(Full suite run 2026-09-02: test_ac2_ac3_analytic_rule_declares_mode_two_only[bounds] passed)*
  - **2026-09-02** → Full suite run 2026-09-02 (.venv/bin/python -m pytest -q): 6900 passed, 0 failed. Combined with item 136's six corpus-derived declarations, item 137 disposes the remaining four rules (bounds, reference_delta -> mode 2 analytic; intensity, intensity_reference_delta -> mode-less with recorded reason), verified by test_ac1_all_ten_rules_declared_and_not_pending, test_ac2_ac3_analytic_rule_declares_mode_two_only[bounds/reference_delta], and test_ac5_mode_less_rule_declares_no_modes_not_pending[intensity/intensity_reference_delta] — every registered rule now maps to >=1 mode or is recorded mode-less with a reason.
- [x] Every registered rule is exercised by ≥1 case or recorded as unexercised with a *(Full suite run 2026-09-02: test_ac2_ac3_analytic_rule_declares_mode_two_only[reference_delta] passed)* *(Item 169 AC4: tests/test_162_corpus_exercise_report.py passes in full in the clean clone (18 passed), clone commit 2c4b62bcf2dcad5f37ec88273a74eae432b06df2. Live measurement from segfacet.traceability.build_matrix().exercise in the clone: 10 registered rules -- 7 exercised (border, coverage, fragmentation, intensity, mislabel, overlap, sequence), 3 unexercised with reason needs-real-data (bounds: modes 1,2,3,4; reference_delta: modes 1,2,3,4,8; intensity_reference_delta: mode 16); 12 registered operators, all used (crop_at_border, displace, force_overlap, fragment, fuse, identity, inject_islands, relabel_swap, remove_level, remove_level_relabel, sequence_break, split). Both DirectionReports read complete=True, holes=().)*
  - **2026-09-02** → retracted: Retracting an attestation-mapping error: this criterion (every registered rule exercised by >=1 case or recorded unexercised with reason) was mistakenly ticked by positional mismapping to item 137's AC3 test; per-rule corpus-exercise reporting is Item 139's future deliverable, not verified by item 137's tests.
  reason (**G2**).
- [x] The specificity assertion is enforced for every corpus case. *(Full suite run 2026-09-02: test_ac4_mode_two_declaration_is_analytic_with_named_mechanism passed for both rules)* *(Validated 2026-09-20: .venv/bin/python -m pytest -n auto -> 8967 passed, 63 skipped (all pre-known env-gated), 0 failed, full suite. tests/test_163_specificity_ratchet.py -v run standalone -> 21 passed: AC2 (test_ac2_ratchet_measured_equals_expected, parametrised over all 15 committed corpus cases: 11 geometric + 4 intensity, ids confirmed by --collect-only) asserts set(measured_firing)==set(expected_firing) per case via traceability.build_matrix().conformance.cases, one test per case id -- the specificity assertion enforced for every corpus case. AC4/AC6 confirm the comparison actually catches an unintended firing and a silenced rule (not vacuous); AC1 confirms no case is exempt from the loop. (closes Stage 20 criterion 4, item 163 AC2 annotation).)* *(Item 169 AC3: tests/test_163_specificity_ratchet.py passes in full in the clean clone (22 passed), clone commit 2c4b62bcf2dcad5f37ec88273a74eae432b06df2. Live measurement from segfacet.traceability.build_matrix().conformance in the clone: 16 cases driven -- 12 geometric (clean_control, crop_at_border, displace, force_overlap, fragment, fuse_adjacent, inject_islands, relabel_swap, remove_level, remove_level_relabel, sequence_break, split) and 4 intensity (clean_hu, degenerate_uniform, implausible_metal, implausible_soft_tissue); 0 cases disagree. The driven case-id set equals the union of both committed manifests' case_id values.)*
  - **2026-09-02** → retracted: Retracting an attestation-mapping error: this criterion (specificity assertion enforced for every corpus case) was mistakenly ticked by positional mismapping to item 137's AC4 test; the specificity assertion is Item 140's future deliverable, not yet built, so this criterion does not hold.
  - **2026-09-20** → retracted: Attested from inside item 163, but item 163's own spec assigns this attestation elsewhere: its Dependencies section records that item 169 'drives it from a clean clone and attests Stage 20 criteria 3-5'. AC2's *(closes Stage 20 criterion 4)* annotation marks which deliverable makes the criterion true, not permission for this item to tick it -- item 162 carried the identical *(closes Stage 20 criterion 3)* annotation one item earlier in this same queue and deliberately left criterion 3 unticked for the same reason. The substance now holds (tests/test_163_specificity_ratchet.py drives set(measured_firing)==set(expected_firing) over all 15 committed corpus cases, with AC4/AC6 proving the comparison is not vacuous), but it was measured in the working checkout, not the clean-clone replay this stage's attestations are routed through after the 2026-09-02 mismapping retractions. Leaving criterion 4 ticked while 3 and 5 stay open would also make the stage's record incoherent.
- [x] The end-to-end detection count is stated honestly here rather than implied (**G7**). *(Full suite run 2026-09-02: test_ac5_mode_less_rule_declares_no_modes_not_pending passed for both rules)* *(Item 169 AC6-AC8, measured live from segfacet.failure_modes in the clean clone, clone commit 2c4b62bcf2dcad5f37ec88273a74eae432b06df2: derived status counts over 16 modes: validated 7, implemented 2, specified 0, proposed 7. derived mode rung counts: synthetic-demonstrable 6, needs-real-data 2, structurally-unobservable 1, none 7. modes refined by stage 32: 3, 4; at the fully-specified bar: none; left as documented drafts: 14.)*
  - **2026-09-02** → retracted: Retracting an attestation-mapping error: this criterion (end-to-end detection count stated honestly) was mistakenly ticked using item 137's AC5 test as evidence by positional mismapping; that test verifies mode-less declarations, not this stage-level claim, which remains open (Item 142).
  - **2026-09-28** → Item 188 (2026-09-28): coverage re-homed from mode 6 to mode 10; mode 6 derives specified with no rule, mode 10 implemented at needs-real-data. Re-measured live: derived status counts over 16 modes: validated 6, implemented 3, specified 1, proposed 6. derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7.
  - **2026-09-28** → Item 192 (2026-09-28): sequence serves modes 9-11 by sub-type; mode 11 derives implemented at needs-real-data, mode 10 gains a second edge. Re-measured live: derived status counts over 16 modes: validated 6, implemented 4, specified 1, proposed 5. derived mode rung counts: synthetic-demonstrable 5, needs-real-data 4, structurally-unobservable 1, none 6.
  - **2026-09-28** → Item 193 (2026-09-28): reference_delta and intensity_reference_delta made mode-less; mode 8 derives specified with no rule, mode 16 keeps its intensity edge. Re-measured live: derived status counts over 16 modes: validated 6, implemented 3, specified 2, proposed 5. derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7.
  - **2026-09-28** → Item 195 (2026-09-28): force_overlap removed; mode 15 derives implemented. Re-measured live: derived status counts over 16 modes: validated 5, implemented 4, specified 2, proposed 5. derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7.
  - **2026-09-30** → Item 205 (2026-09-30): mode 2/3 boundary re-drawn at gate-51da; split and neighbour_contact's stray_contact moved to mode 2, which derives validated. Re-measured live: derived status counts over 16 modes: validated 6, implemented 3, specified 2, proposed 5. derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7.
  - **2026-09-30** → Item 208 (2026-09-30): mode 3 gains split_fragment's synthetic-demonstrable edge, moving its derived rung from needs-real-data to synthetic-demonstrable and adding one edge. Re-measured live: derived status counts over 16 modes: validated 6, implemented 3, specified 2, proposed 5. derived mode rung counts: synthetic-demonstrable 6, needs-real-data 2, structurally-unobservable 1, none 7.
  - **2026-10-13** → Item 220 (2026-10-13): mode 13 gains collapsed_labels' needs-real-data edge and derives implemented. Re-measured live: derived status counts over 16 modes: validated 6, implemented 4, specified 2, proposed 4. derived mode rung counts: synthetic-demonstrable 6, needs-real-data 3, structurally-unobservable 1, none 6.
  - **2026-10-13** → Item 218 (2026-10-13): mode 6 gains centroid_spacing's missing_level edge (synthetic-demonstrable) and derives validated. Re-measured live: derived status counts over 16 modes: validated 7, implemented 4, specified 1, proposed 4. derived mode rung counts: synthetic-demonstrable 7, needs-real-data 3, structurally-unobservable 1, none 5.

> **Not required:** feature→rule completeness. Unwired features are a designed state.
