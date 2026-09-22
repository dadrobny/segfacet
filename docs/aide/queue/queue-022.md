<!-- aide-template: queue 1 -->
# FACET — Work Queue 022

> **Created:** 2026-09-18
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).
> Opens **Stage 32** and closes it together with Stage 20's remainder;
> supersedes [`queue-021.md`](queue-021.md) (Stage 31, complete at item 161).

---

## Scope of this queue

Delivers roadmap **Stage 32 — Selected-Mode Refinement: one failure mode fully
specified end to end** (G2, G7, G8): eight items, under `loop.queue_cap = 10`,
covering **D0** (Stage 20's held exercise report and specificity ratchet — items 162, 163), **D1** (the MVP mode), **D2**
(one further selected mode) and **D3** (Stage 20's held validation, which also
validates this stage — item 169).

**Modes selected by the maintainer at this queue's planning (2026-09-18):**

- **Mode 4 — Islands (disconnected components)**, the MVP candidate. It derives
  `validated` today: `inject_islands` fires `fragmentation`'s `Rogue island(s):`
  detector and nothing else. What separates it from the roadmap's six-condition
  bar is condition 4 — *a detector decides the mode and serves no other mode*.
  `fragmentation` declares `modes=(1, 4)`, one detector per mode, but the
  detector is authored prose (`IntendedRule.detector`), so nothing mechanical
  can say the island detector serves mode 4 alone. Item 164 closes that.
- **Mode 3 — Split vertebra segment**, the D2 mode. It derives `implemented`
  with no corpus case and no detector of its own — only the `bounds` /
  `reference_delta` volume proxies at `needs-real-data`. It needs an operator,
  a fixture, a feature and a detector (items 166, 167), and may end at a
  recorded intermediate state rather than the bar; the roadmap accepts that.

**This queue closes the stage.** Stage 32's acceptance needs one mode at the
bar; further modes "belong to no stage" and may be refined in any later queue.
So item 169 runs here. If mode 4 does not reach the bar, item 169 records that
and the stage stays open — it is not forced.

**Items are interactive by design** (roadmap Stage 32, "How it runs"): each
mode's item spec is authored with the maintainer, whatever `loop.clarify`
says, and a change to a rule, threshold, fixture or expected firing set is
authored in `src/segfacet/failure_modes.py` first. Thresholds retuned here are
calibrated on the synthetic corpus only (Stage 21 re-calibrates on real GT).

**Prioritisation.** 162 → 163 lead, as the roadmap pins: from the first
refinement item on, every change in what fires is either authored in the
specification or fails the suite. 164 (detector ids) precedes both mode items,
which attribute per detector. 165 (mode 4) and the 166 → 167 chain (mode 3)
are independent of each other and may be claimed in either order. 168 is the
human gate over both modes' rendering; 169 validates last.

**Numbering.** Continues at the next free integer: **162–169**. Stage 20's
held items 139, 140 and 142 were to keep their numbers (progress.md, Stage 20,
note of 2026-09-03), but `aide check` reports an item number that appears in
two queues as an **error**, and they are declared in
[`queue-019.md`](queue-019.md). They are therefore re-queued under new
numbers — **139 → 162, 140 → 163, 142 → 169** — and their Stage 20 deliverable
bullets in `progress.md` are re-pointed to match. Item 139's preserved spec
file keeps its name as the provenance of the measurements item 162 re-measures.
Item 141 moved to Stage 31 and landed as item 154's work; it is not re-queued.

**Build posture (`prototype`).** Items 162 and 163 are justified siblings of
the first refinement item (roadmap Stage 32 D0). Item 139's preserved spec
([`../items/139-per-rule-and-per-operator.md`](../items/139-per-rule-and-per-operator.md),
33 acceptance criteria against the pre-sign-off catalogue) is **re-authored
from item template 2, not amended**: acceptance criteria for the deliverable
only, extra test cases named and labelled in the Testing Strategy.

---

## Work items

### Item 162: Per-rule and per-operator corpus-exercise report

Re-authored against the signed-off sixteen-mode specification. A generated
report, across both committed corpora (geometric and intensity), stating for
every registered rule and every registered perturbation operator which corpus
case exercises it, or recording it as unexercised with a reason drawn from the
specification (evidence rung, `proposed` mode, no harness attaches a
reference). The preserved spec's 2026-09-03 measurements (`fuse` generates no
case; 7 of 10 rules exercised; `intensity_reference_delta` driven by nothing)
are inputs to re-measure, not facts to copy. *Testable:* the report regenerates
byte-identically from a clean tree, and a rule or operator that is neither
exercised nor recorded fails the suite.

### Item 163: The specificity ratchet — no unintended rule may fire

For every corpus case across both corpora, the measured firing set must equal
the case's `expected_firing` in the specification — the allowlist is derived
from the specification, never authored beside it, so a co-detection is allowed
only where the specification records it (`crop_at_border`'s
`{border, mislabel}` is the worked example). Builds on the conformance report
item 149 shipped (`traceability.ConformanceReport`) rather than a second
measurement path. *Testable:* adding a finding to, or removing one from, any
case's measured firing without editing the specification fails one named test
that prints the case, the expected set and the measured set.

### Item 164: First-class detector ids on rules and in the specification

A rule with more than one detector (`fragmentation`: `Fragmentation:` and
`Rogue island(s):`; `mislabel`: offset and ordering; `coverage`: its
interior-gap detector) declares each detector under a stable id with the
mode(s) that detector serves, and `IntendedRule.detector` references that id
instead of carrying prose — joining a mechanical check on authored prose is
the retired `"corpus"`-tag defect. A conformance check reports a specification
edge naming a detector id no rule declares, and a declared detector no edge
names. Per-path `signal` attribution (item 148) narrows from the rule's modes
to the detector's. Also corrects the `reference_delta` mode-1 comment at
`src/segfacet/heuristics/reference_delta.py` whose premise (the spline-offset
path as mode 1's anchor) item 154 removed; the declaration then rests on
`SPECIFICATION[1].intended_rules` alone, and says so. Changes no firing.
*Testable:* the two conformance directions each fail on a seeded mismatch;
every multi-detector rule's findings carry their detector id; the ratchet
(item 163) stays green with no specification edit to any expected set.

### Item 165: Mode 4 (islands) brought to the fully-specified bar

The MVP mode. With the maintainer: confirm the specification entry
(definition, discriminator, scope, observability, severity, candidate
features, intended rules, corpus cases); decide whether
`island_distance_from_main_body_mm` — which the definition says grades the
finding — is extracted, catalogued and read by the detector now, or stays a
`hypothesised` candidate path; and check the roadmap's conditions 1–5 against
live state: `inject_islands` expects and measures `[fragmentation]`, every path
the `Rogue island(s):` detector reads is in the generated feature catalogue,
that detector id (item 164) serves mode 4 and no other, and the status derives
`validated`. Condition 6, the sign-off, is item 168's. *Testable:* one test
per bar condition 1–5 against live state; if the distance feature is built, a
near and a far island fixture grade differently and the ratchet records the
authored expected sets.

### Item 166: A split operator and mode 3's corpus case

A `synth` perturbation operator that reassigns a substantial part of one
label's voxels to its adjacent neighbour (mode 3's definition; the roadmap
menu's "split operator"), carrying the machine-readable record of what was
broken, plus one committed geometric corpus case generated from it with its
`expected_firing` authored in the specification from the measured firing.
Whatever fires today is recorded as found — including an empty set, or
co-detections by `bounds` / `reference_delta` / mode 2's proxy, each stated in
the case's reason. Follows the LF-pin gotcha for the regenerated
`tests/corpus/manifest.json`. *Testable:* the operator is deterministic under
its seed and refuses a label with no adjacent neighbour; the corpus
regenerates byte-identically; the ratchet and the exercise report (items 163,
162) pick the new case and operator up without being edited.

### Item 167: Mode 3's own feature and detector

With the maintainer, choose the signal that decides a split from the label map
alone among the entry's `hypothesised` candidate paths (neighbour-label contact
area, leave-one-out spline shape change, metric change under a merge
candidate) — it must separate mode 3 from mode 2 (the converse, which
co-occurs), mode 1 (part left as background) and mode 4 (small own-label
islands). Extract and catalogue the feature in the current record shape (Stage
27 renames later), add a detector with a first-class id (item 164) serving
mode 3 alone, threshold calibrated on the synthetic corpus, and author the
edge and item 166's case's new expected set in the specification. If no
candidate separates the modes on the corpus, record mode 3 at its reached
state with the measurements and stop — not reaching the bar is an accepted
outcome. *Testable:* the detector fires on item 166's case and on no other
corpus case, including the clean control and `fuse_adjacent`; the feature is in
the generated catalogue; mode 3's status derives `validated`, or the recorded
intermediate state is asserted instead.

### Item 168: Maintainer sign-off of modes 3 and 4

Raises the queue's human gate over modes 3 and 4 as rendered in
`docs/aide/failure_modes.generated.md`, and, once a person has resolved it,
records each mode's sign-off — date and outcome (at the bar, or the recorded
intermediate state) — in `src/segfacet/failure_modes.py`, the same shape item
150 used for the catalogue sign-off. No agent resolves the gate. Blocks item
169. *Testable:* the specification carries a dated sign-off for modes 3 and 4,
the rendering regenerates byte-identically with it, and a mode claimed "at the
bar" whose live state fails any of conditions 1–5 fails the suite.

### Item 169: Validate stage 32: Selected-Mode Refinement, and close Stage 20

Replays both stages' use cases end to end from a clean clone with its own
venv (CLAUDE.md gotcha, item 135's rig): every generated artifact
(`failure_modes.generated.md`, the traceability matrix, the feature catalogue,
the exercise report, both corpus manifests) regenerates byte-identically; the
specificity assertion is driven over every corpus case of both corpora; the
cross-mode margins are re-measured; and the end-to-end detection count is
written into `progress.md` per lifecycle status and per evidence rung, as
measured numbers with what they were measured on, naming modes 3 and 4 as
refined, which met the bar, and the modes left as documented drafts.
Attests Stage 32's acceptance and Stage 20's criteria 3–5 (which carry
retraction trails) through `aide progress accept`, with evidence. Stage 20's
ladder-base bullet (item 141) still reads ⏸️ although its work landed in Stage
31 as item 154; a ⏸️ bullet keeps a stage from rolling up to ✅, so closing
Stage 20 includes resolving that bullet with a pointer to item 154. Introduces
no environment-gated capability, so no verification-table row flips.
*Testable:* the clean-clone replay is green, and each attested number is
reproduced by a test reading live state rather than pinned as a literal.
