<!-- aide-template: queue 1 -->
# FACET — Work Queue 025

> **Created:** 2026-09-25
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).
> Continues **Stage 33**. Runs after the maintenance queue
> [`queue-024.md`](queue-024.md).

---

## Scope of this queue

Roadmap **Stage 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar**,
deliverable **D3**: rules re-homed to the signal they read (`insights.md`,
entries dated 2026-09-22). It also removes `force_overlap`. The maintainer
decided on 2026-09-25 to remove it rather than leave it parked, because
Stage 33's second acceptance criterion forbids a case that claims a mode its
label map does not express. Ten items, which is `loop.queue_cap`.

**Stage 33's last queue comes after this one.** It holds D4 (the bar checker
made existential and detector-granular, the ladder constants re-measured, and
a generated `rules.generated.md`), D5 (the at-the-bar sign-off gate) and D6
(stage validation, which also closes Stage 32's criterion 1). This queue does
not close the stage, so it has no validation item.

**Every item re-authors expected sets from measurement.** A rule that moves
changes what fires on the corpus. So each item re-measures the affected cases,
re-authors their `expected_firing` in `src/segfacet/failure_modes.py` with the
reason stated, and keeps the specificity ratchet (item 163) green. Each item's
reconciliation sweep greps for tests that pin a rule id, a rule count or a
rule→mode pair as a literal.

**Prioritisation.** Item 186 (`CANONICAL_ORDER`) leads, because it removes
`split_own_label`'s spurious `coverage` firing, and items 187 and 188 would
otherwise re-author around it. Item 187 (the `neighbour_contact` rule) pays
the rule-count pins once. Item 189 (the displaced-vertebra condition) precedes
item 190 (the condition-keyed eval bucket), which needs a second condition to
exist. Item 191 (condition-flagged labels excluded by default) follows 189,
because its mechanism covers both conditions. Item 192 (`sequence`
sub-types) follows 186, because it checks against 186's expected sequence.
Items 193–195 are independent and can be claimed in any order after 186.
Item 194 (mode-1 attribution) is best run late, so it sees the other
re-homings.

**Build posture (`prototype`).** Every item is a named D3 deliverable, or an
insight entry that D3 absorbs. Stage 33's acceptance criteria 2–4 need them.

**Numbering.** Continues at the next free integer: **186–195**.

---

## Work items

### Item 186: The expected level sequence admits per-section vertebra counts

`relationships.missing_levels` walks `labels.CANONICAL_ORDER`, where the
transitional T13 sits between T12 and L1, and L6 sits between L5 and S1. So
`coverage` reports T13 as absent on any label map that holds T12 and L1. That
is the common thoraco-lumbar case (`insights.md`, queue-022 review,
2026-09-22, the defect entry). `split_own_label`'s expected set loses the
`coverage` co-detection.

The fix is per-section counts, not two special-cased transitional labels
(maintainer feedback, 2026-09-25):

- **Counts per section.** Cervical 7. Thoracic 11–13. Lumbar 4–6. The sacrum
  is not split into levels: some models label S1's body separately and the
  rest of the sacrum as a second label, so neither form counts as a gap. Any
  combination of section counts is valid. The default is (7, 12, 5). The
  expected sequence for a case is C1–C7, T1–T*n*, L1–L*m*, S, and it is
  walked in that order. T11→L1 is continuous when the thoracic count is 11.
  L5→S is continuous when the lumbar count is 5.
- **The order must be monotonic** along the spine.
- **A non-default count must be indicated by the scan.** The whole section
  must be in the field of view, plus the first vertebra on either side of
  it. So L1 preceded by T11 or T13 requires C7 in the field of view, so that
  every thoracic level is counted. S preceded by L4 or L6 requires the last
  thoracic level in the field of view, so that every lumbar level is
  counted. When the field of view does not show that, the non-default
  reading is not accepted, and item 192's transitional sub-type reports it.
- **Prior knowledge may set the counts instead.** A case may be given its
  section counts as input, for example from the subject's other scans. A
  supplied count is accepted without the field-of-view requirement.

*Testable:* a label map holding T12 and L1–L5 and no T13 yields no missing
level and no finding (Stage 33 criterion 4). A map that skips L3 still
reports L3. T1–T11 then L1, with C7 in the field of view, yields no missing
level. The same map without C7 does not accept the 11-level reading. A
supplied count of 13 thoracic levels makes an absent T13 missing. Each
section's count range, and one mixed combination such as (7, 13, 4), is
exercised.

### Item 187: `neighbour_contact` becomes a rule of its own, serving mode 3

`fragmentation`'s `components` and `islands` detectors read one label in
several parts, which is not mode 3. `neighbour_contact` is mode 3's signal, so
it moves out of `fragmentation` into its own rule, and `fragmentation` stops
declaring mode 3 (`insights.md`, queue-022 review, 2026-09-22). The threshold
comment in `src/segfacet/default_config.yaml` is re-measured with the move. It
still quotes the split case's contact as 750.0 mm², and the lordotic base
reads 775.0 (`insights.md`, item 173, 2026-09-23). The rule-count pin
(`test_136`) and the rule-id enumerations are updated once, here.

The contact measure changes with the move (maintainer feedback, 2026-09-25).
Today `components.stray_contact_area_mm2` is an absolute area. A small
component shows little absolute contact even when a large part of its surface
touches a neighbour. So contact is also measured relative to the component's
own surface: the contact area divided by the component's surface area. It is
reported at two scopes:

- **Per connected component**, naming the neighbour each part touches. This
  is what decides which parts of a fragmented label may need merging, and
  into which neighbour.
- **Per whole label**, whether or not the label is fragmented.

The threshold is re-expressed on the relative measure and re-measured.

*Testable:* the new rule fires on `split` and on no other corpus case. A small
component that touches a neighbour over most of its surface reaches a higher
contact fraction than a large component with the same absolute contact area.
Each component's record names the neighbour it touches. An unfragmented label
carries a label-level contact fraction. `fragmentation` declares no mode 3
edge. The rule count is 11.

### Item 188: `coverage` re-homed from mode 6 to mode 10

`coverage` detects a missing *label* in the sequence, not a missing vertebra,
so it serves mode 10 (skipped level label), not mode 6 (`insights.md`,
queue-022 review, 2026-09-22). Mode 10 gains its first rule edge. Mode 6 loses
its only synthetic-demonstrable edge.

`remove_level` and `remove_level_relabel` stay attributed to mode 6. Mode 6
should fire on both, and that is its detection target (maintainer feedback,
2026-09-25). `coverage` firing on `remove_level` is recorded as a mode-10
co-detection, not as mode 6's detection. Mode 6's own rule is to be decided
later: the spacing rule is not in this stage (roadmap Stage 33, scope
decisions). So mode 6's status and rung record that no rule detects it yet.
Neither case is moved to another mode to fill the gap.

*Testable:* `coverage`'s declaration names mode 10 and not mode 6. Both
`remove_level` cases are still attributed to mode 6. Mode 6's status records
that no rule detects it. Both modes' derived status and rung match an
independent recomputation. The ratchet is green.

### Item 189: `mislabel`'s `spline_offset` moves to a displaced-vertebra condition

`mislabel` keeps its `ordering` detector, extended to any out-of-sequence
label. Its `spline_offset` detector moves to a new `failure_modes.CONDITIONS`
entry beside `fov_truncation`: a displaced vertebra, which is a property of
the case and not a segmentation defect. `displace` becomes that condition's
fixture, and its severity ladder is re-homed with it (`insights.md`,
queue-022 review, 2026-09-22, the `mislabel` and displaced-vertebra
decisions). `mislabel.py`'s docstring still quotes box-base offset margins,
and `test_123` pins them. Both are rewritten with the move (`insights.md`,
item 173, 2026-09-23). *Testable:* `displace` is a condition case, and no mode
claims it. `mislabel` fires on no displaced-only case. `crop_at_border`'s
expected set is re-measured and re-authored.

### Item 190: A condition-keyed bucket in the eval harness

`segfacet.eval.metrics._compute_per_mode` groups corpus cases by
`CaseOutcome.failure_mode`. So a condition case lands in the mode-0 bucket
beside the clean control, and is reported under the clean-control name
(`insights.md`, item 155, 2026-09-16). With two conditions after item 189,
each condition gets its own bucket. `test_116`'s
`test_ac8_mode6_crop_at_border_sensitivity_is_restored_to_one` stops pinning
`failure_mode == 0`. *Testable:* each condition case is reported under its
condition's name. The clean control's bucket holds only clean controls.

### Item 191: A condition-flagged label is excluded from every rule that does not opt in

`bounds`, and `reference_delta`'s size features, fire on a label that touches
the image border, because a truncated vertebra is small by construction.
Verified 2026-09-22: `heuristics/bounds.py` reads no `touches_*` flag
(`insights.md`, queue-022 review, 2026-09-22, the `bounds` decision).

Size is not the only feature a border touch spoils. The maintainer ruled
that the gate belongs to the condition, not to each feature (maintainer
feedback, 2026-09-25). A border-touching label is in the `fov_truncation`
condition, and a label in any condition is excluded from every rule unless
that rule explicitly opts in to the condition. Today the relationship is the
other way round: `ConditionSpec.exempting_rules` lists the rules that
exempt a condition's labels (`mislabel`, `coverage`), and every other rule
applies. This item inverts it. A rule that opts in says which of its
features stay valid on a truncated label. That choice is made for each rule
when the rule uses the feature, and not in advance for every feature. The
mechanism covers item 189's displaced-vertebra condition too, so this item
runs after 189. Vertebra-local extents are Stage 27's. `crop_fov_si` is the
fixture the gating is measured on.

*Testable:* `crop_fov_si`'s L5 remnant fires no size finding. The same
volume on an interior label still fires. A rule that opts in to
`fov_truncation` still fires on a border-touching label. The existing
exemptions (`mislabel`'s terminal skip, `coverage`'s border-aware span) hold
under the new default. The expected sets of `crop_fov_si` and
`crop_at_border` are re-authored.

### Item 192: `sequence` reports which sub-type it saw

An out-of-sequence label can express any of modes 8–11, so `sequence` serves
that family and reports the sub-type in its finding: a swap, a skip, a
transitional label, or a shift. Mode 12 (shifted sequence) cannot be
identified without external context and stays out (`insights.md`, queue-022
review, 2026-09-22, the `sequence` decision). Item 186 sets the expected
sequence this rule checks against: section counts, monotonic order, and when
a non-default count is accepted. A non-default count that the field of view
does not show, and no supplied count backs, is reported as the transitional
sub-type. *Testable:* each sub-type,
constructed as a label map, yields a finding that names it.
`sequence_break`'s finding names its sub-type. No mode-12 edge is declared.

### Item 193: `reference_delta` and `intensity_reference_delta` claim no mode as their own

Both stay as general outlier detectors and are no mode's own detector (roadmap
Stage 33 D3). `intensity_reference_delta` declares `modes=(16,)` with zero
`signal`-role consumed paths, and `catalogue.path_classification_conflicts()`
cannot see that state, because it only refuses an empty `consumed_paths`
(`insights.md`, item 164, 2026-09-20). Resolve the mode-16 claim, and make the
check report a non-empty mode set with no signal path. *Testable:* a planted
declaration with modes and no signal path is reported. The live registry
reports nothing. Neither rule is counted toward bar condition 4 for any mode.

### Item 194: Mode 1 attributed only as the catch-all, with the review's vocabulary

Mode 1 is the catch-all accuracy mode. A case, or a mode→rule edge, is
attributed to it only when no other mode applies, and the rendering says so
rather than listing mode 1 beside the others. The vocabulary is applied as the
review defined it: a mode describes the vertebra (mode 2 is fused segments,
mode 3 a split segment), and "fragmentation" means one label in several parts
(`insights.md`, queue-022 review, 2026-09-22, the presentation and naming
decision). *Testable:* no case carries mode 1 beside another mode. The
rendering states mode 1's catch-all rule. Mode 2's and mode 3's definitions
use the vertebra wording.

### Item 195: `force_overlap` removed

A single-channel label map cannot hold an overlap. `force_overlap`'s overlap
exists only in a reconstructed two-channel record, and on the lordotic base
the operator overlaps only two of its four pairs (`insights.md`, queue-022
review, 2026-09-22, and item 173, 2026-09-23). Remove the operator, its corpus
case, its `severity_ladder` entries and its mode-15 corpus attribution. Mode
15 stays in the specification as documented, with no fixture. Whether the
`overlap` rule stays, as a declared multi-channel rule, or goes with the
fixture is decided in the spec (`insights.md`, queue-022 review, 2026-09-22).
*Testable:* no manifest, operator registry or ladder names `force_overlap`.
Both corpora regenerate byte-identically. The exercise report and the ratchet
agree with the reduced case set.
