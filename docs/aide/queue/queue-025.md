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
exist. Items 191–195 are independent and can be claimed in any order after
186. Item 194 (mode-1 attribution) is best run late, so it sees the other
re-homings.

**Build posture (`prototype`).** Every item is a named D3 deliverable, or an
insight entry that D3 absorbs. Stage 33's acceptance criteria 2–4 need them.

**Numbering.** Continues at the next free integer: **186–195**.

---

## Work items

### Item 186: `CANONICAL_ORDER` admits every numbering variant as continuous

`relationships.missing_levels` walks `labels.CANONICAL_ORDER`, where the
transitional T13 sits between T12 and L1, and L6 sits between L5 and S1. So
`coverage` reports T13 as absent on any label map that holds T12 and L1. That
is the common thoraco-lumbar case (`insights.md`, queue-022 review,
2026-09-22, the defect entry). Make T12→L1 continuous with or without T13, and
L5→S1 with or without L6. A transitional level counts as missing only when the
case is configured to expect it. `split_own_label`'s expected set loses the
`coverage` co-detection. *Testable:* a label map holding T12 and L1–L5 and no
T13 yields no missing level and no finding (Stage 33 criterion 4). A map that
skips L3 still reports L3.

### Item 187: `neighbour_contact` becomes a rule of its own, serving mode 3

`fragmentation`'s `components` and `islands` detectors read one label in
several parts, which is not mode 3. `neighbour_contact` is mode 3's signal, so
it moves out of `fragmentation` into its own rule, and `fragmentation` stops
declaring mode 3 (`insights.md`, queue-022 review, 2026-09-22). The threshold
comment in `src/segfacet/default_config.yaml` is re-measured with the move. It
still quotes the split case's contact as 750.0 mm², and the lordotic base
reads 775.0 (`insights.md`, item 173, 2026-09-23). The rule-count pin
(`test_136`) and the rule-id enumerations are updated once, here. *Testable:*
the new rule fires on `split` and on no other corpus case. `fragmentation`
declares no mode 3 edge. The rule count is 11.

### Item 188: `coverage` re-homed from mode 6 to mode 10

`coverage` detects a missing *label* in the sequence, not a missing vertebra,
so it serves mode 10 (skipped level label), not mode 6 (`insights.md`,
queue-022 review, 2026-09-22). Mode 10 gains its first rule edge. Mode 6 loses
its only synthetic-demonstrable edge, and `remove_level` is re-attributed or
recorded as a co-detection. Mode 6's own spacing rule is not in this stage
(roadmap Stage 33, scope decisions). *Testable:* `coverage`'s declaration
names mode 10 and not mode 6. Both modes' derived status and rung match an
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

### Item 191: Size features gated on a border-touch flag

`bounds`, and `reference_delta`'s size features, are suppressed on a label
that carries a border-touch flag, because a truncated vertebra is small by
construction. Verified 2026-09-22: `heuristics/bounds.py` reads no `touches_*`
flag (`insights.md`, queue-022 review, 2026-09-22, the `bounds` decision).
Vertebra-local extents are Stage 27's. `crop_fov_si` is the fixture the gating
is measured on. *Testable:* `crop_fov_si`'s L5 remnant fires no size finding.
The same volume on an interior label still fires. The expected set is
re-authored.

### Item 192: `sequence` reports which sub-type it saw

An out-of-sequence label can express any of modes 8–11, so `sequence` serves
that family and reports the sub-type in its finding: a swap, a skip, a
transitional label, or a shift. Mode 12 (shifted sequence) cannot be
identified without external context and stays out (`insights.md`, queue-022
review, 2026-09-22, the `sequence` decision). *Testable:* each sub-type,
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
