<!-- aide-template: queue 1 -->
# FACET — Work Queue 027

> **Created:** 2026-09-29
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).
> Closes **Stage 33**. Runs after the maintenance queue
> [`queue-026.md`](queue-026.md).

---

## Scope of this queue

Roadmap **Stage 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar**.
This queue covers the stage's last three deliverables: D4 (the bar checker,
the ladder constants and the rule table), D5 (the at-the-bar sign-off of
modes 3 and 4, a human gate) and D6 (stage validation). D6 also re-runs
Stage 32's D3 on the re-grounded corpus and attests Stage 32's criterion 1.
Five items. This queue completes the stage, so it ends with the validation
item.

**Prioritisation.** Items 200–202 are D4 and are independent of one another.
Item 203 (the sign-off) needs all three, because the maintainer reads the rule
table and signs against the bar checker's live verdict. Item 204 (validation)
runs last. Item 198 in the maintenance queue re-measures expected sets, so the
bar checker is measured after it.

**Build posture (`prototype`).** Items 200–202 are named D4 deliverables.
Stage 33's first and third acceptance criteria need them, and item 203's gate
needs the rule table. Item 203 is D5, and item 204 is the stage-validation
item that requirement 5 of queue authoring asks for.

**Numbering.** Continues at the next free integer: **200–204**.

**Re-plan (2026-09-30, gate `gate-51da` declined).** The maintainer declined
the at-the-bar sign-off of modes 3 and 4 and re-drew the mode 2/3 boundary.
Mode 2 (fused vertebra segments) keeps the paired case: one label covering its
own vertebra and part or all of a neighbour. Mode 3 (split vertebra segment)
becomes the fragment case only: part of a vertebra carrying a label of its own
and covering no other vertebra. The label that is left covering only the
remainder of the encroached vertebra, which is the complement to mode 2, gets
no mode yet (deferred, `insights.md` 2026-09-30). The selected modes for the
bar become **2 and 3**. Mode 4 leaves the selection, and its `gate-bb24`
intermediate-state sign-off stands as its record. Four items are added,
**205–208**. Item 203 is re-scoped to modes 2 and 3 over the new sign-off gate
`gate-0133`, and it runs after 205–208. Item 204 still runs last.

Order: 205 first. 206 and 208 each need 205, and 207 needs 206.

---

## Work items

### Item 200: The bar checker's condition 2 made existential and detector-granular

`traceability.bar_conditions`' condition 2 is computed as every corpus case
attached to the mode agreeing, AND at least one case whose `expected_firing`
intersects the mode's own rule ids. The roadmap words it existentially: at
least one committed fixture expresses the mode. So a case attached to the mode
that does not express it can hold condition 2 down (insight 2026-09-20-74f1).
That every attached case agrees is the specificity ratchet's job, and item 163
already enforces it. Condition 2 is also rule-id-granular, while condition 4
is detector-granular. So a mode can meet condition 2 on a firing that its own
deciding detector never produced (insight 2026-09-20-8462).

Read condition 2 existentially. Make it intersect `(rule_id, detector_id)`
pairs drawn from the case's measured findings (`Finding.detector_id`, since
item 164) with the mode's own intended detectors. *Testable:* a mode with one
expressing case and one agreeing, non-expressing case meets condition 2. A
case whose own rule fires only through another mode's detector does not meet
it. Modes 3 and 4 are re-measured live, and the result is recorded in the
spec.

### Item 201: Severity-ladder constants re-measured on the lordotic base

`segfacet.eval.severity_ladder`'s `RECORDED_MARGINS` and
`KNOWN_CROSS_MODE_COUPLINGS` were measured by item 154 on 2026-09-16, before
item 166 added `split`. `run_severity_harness()`'s `per_ladder` still has no
`split` key (insight 2026-09-22-b0d2), and no ladder covers
`split_own_label`'s operator. `MODE_LADDER_DISPOSITIONS[1]` still derives mode
1's ladders as (`displace`, `fragment`), and its reason text reads the
pre-189 homing. Since item 189, `displace` is a `displaced_vertebra`
condition case (insight 2026-09-28-1abd). Re-measure every constant on the
lordotic base. Add ladders for the split operators, and re-derive each
disposition from the ladders' current homes. *Testable:* `per_ladder` covers
every registered operator that designates a metric. Each recorded margin
equals a fresh measurement within the harness's tolerance. Mode 1's
disposition names no condition-homed ladder.

### Item 202: A generated `docs/aide/rules.generated.md`

No document states what each rule *decides*. The failure-mode rendering and
the traceability matrix say which mode a rule serves. The decision logic
lives only in the module docstrings under `src/segfacet/heuristics/` and in
`src/segfacet/default_config.yaml` (insight 2026-09-22-b3de). Every fact is
already machine-readable: `Rule.mode_declaration` carries the detector ids
and their message tags, and the config carries the defaults. Generate one row
per detector beside `failure_modes.py`'s generator, stale-checked the same
way. Each row gives the question the detector asks, the path it reads, when
it fires, its default threshold and the modes it serves. *Testable:* every
registered detector has exactly one row. The committed file is byte-identical
to a fresh render. A changed default in the config makes the committed file
stale.

### Item 205: The mode 2/3 boundary re-drawn

Today the two modes claim the same error twice. Mode 3's sub-type (a) is a
part of a vertebra carrying a neighbour's label, and mode 2 is a label
extending onto its neighbour. Each discriminator calls the other "the
converse" and says the two co-occur. Re-draw the boundary as the maintainer
decided at `gate-51da` (2026-09-30). Mode 2 is one label covering its own
vertebra plus part or all of a neighbour. Mode 3 is the fragment case: part of
a vertebra carrying a label of its own that covers no other vertebra (today's
sub-type (b), plus lumbarised S1). Rewrite both entries' definitions,
discriminators and mechanisms in `segfacet.failure_modes`. Both discriminators
must say that the label left covering only the remainder of an encroached
vertebra has no mode yet. Move `neighbour_contact`'s `stray_contact` detector
from mode 3 to mode 2, together with its `IntendedRule` edge. Re-home the
`split` corpus case to mode 2, and keep `split_own_label` as mode 3's case.
This item adds no detector and no fixture, and moves no threshold.
*Testable:* `split` is attributed to mode 2 and agrees with its expected set.
`stray_contact` serves mode 2 alone. Mode 3's intended rules no longer name
`neighbour_contact`. Both generated specification artifacts are regenerated.
`bar_conditions` is re-measured live for modes 2 and 3 and recorded in the
spec. Mode 3 is expected to lose conditions 3 and 4 until item 208 lands.

### Item 206: A fixture for one label over two full, separate vertebrae

Contact cannot see a mode 2 case in which one label covers two complete
vertebrae that do not touch: the second body is a stray component with no
contact. The bridged `fuse_adjacent` (item 176) covers only the connected
variant. Add a geometric corpus case on the lordotic base in which one label
covers two adjacent full vertebral bodies with the disc gap between them
unlabelled, and the labels caudal to it are renumbered so the sequence stays
continuous (as `fuse_adjacent` does). Attribute it to mode 2. Its expected
set records what fires today, measured live.
*Testable:* the case is in the committed manifest and the corpus sheet. It is
attributed to mode 2. Its measured firing equals its expected set. The fused
label has exactly two components, each one a full vertebral body.

### Item 207: Mode 2's fused-label detector, from size and centroid spacing

Neither signal decides mode 2 alone. A fused label's centroid falls between
its two bodies, so the inter-centroid spacings around it read about 1.5× the
pitch (`stage3.spacing_consistency.spacings_mm[]`). A skipped label (mode 10)
or a missing vertebra (mode 6) also widens the spacing, but at normal size
(`insights.md`, item 198, 2026-09-29, the mode-6 spacing entry). The same
label also reads about twice a single level's size. A large vertebra reads
large too, but at normal spacing. A new detector fires on a label that is
both large and flanked by wide spacing, and it serves mode 2 alone. The spec
settles two things. First, what "large" is measured against: relative to the
neighbouring labels is preferred, because it needs no reference. Second, how
to treat the first and last labels, which have spacing on one side only.
*Testable:* the detector fires on `fuse_adjacent` and on item 206's case. It
stays silent on `clean_control` and on every other case in both corpora,
across the lordotic base's normal spacing variation. Both mode 2 cases' expected
sets are updated to include it. Mode 2 meets bar conditions 1–5 live.

### Item 208: Mode 3's own detector, from contact fraction and small size

After item 205, mode 3 (the own-label fragment) is expressed only through the
`bounds` proxy. Its signal is already extracted: the cap in
`split_own_label` reads a whole-label `label_contact_fraction` of about 0.33,
and no rule reads it (item 187). A new detector fires on a label that has a
high whole-label contact fraction and is small, and it serves mode 3 alone.
The spec settles what "small" is measured against: the level's `bounds`
minimum, a ratio to the neighbouring labels, or the reference.
*Testable:* the detector fires on `split_own_label` and on nothing else in
either corpus. `split_own_label`'s expected set is updated to include it.
Mode 3 meets bar conditions 1–5 live.

### Item 203: Modes 3 and 4 re-signed by the maintainer at the bar

**Re-scoped 2026-09-30:** now the sign-off of **modes 2 and 3**, over gate
`gate-0133`, after items 205–208. The paragraph below is the item as it was
planned.

The maintainer reads both modes' rendering in
`docs/aide/failure_modes.generated.md`, the corpus sheet
(`docs/aide/corpus_sheet.png`) and the rule table (item 202). For each mode,
they either sign it off at the bar or record why not (roadmap Stage 33 D5).
The decision brief states each of the six bar conditions as measured live on
the lordotic corpus, and what has changed since gate `gate-bb24`'s
intermediate-state sign-off of 2026-09-22. The item raises a human gate over
that brief. The outcome is written to `MODE_SIGN_OFFS` as one `ModeSignOff`
per mode, with its date. *Testable:* both modes carry a sign-off dated after
2026-09-22. A mode at `outcome="at-the-bar"` meets all six conditions under
`traceability.bar_conditions`. A mode at any other outcome carries its
recorded reason.

### Item 204: Validate stage 33: Corpus & Rule Re-grounding: modes 3 and 4 to the bar

This item replays the stage from a clean clone. Every generated artifact must
regenerate byte-identically, and every corpus case's measured firing must
equal its expected set across both corpora. It attests each of Stage 33's
five acceptance criteria against live state. That includes the T12/L1
no-missing-level map and the detection count per lifecycle status and per
rung, stated as measured numbers with what they were measured on. It also
re-runs Stage 32's D3 on the re-grounded corpus and attests Stage 32's
criterion 1 from item 203's outcome (insight 2026-09-22-2025). Stage 33
introduces no Environment-Gated Capability Verification row, and the item
confirms that. *Testable:* each attestation cites the clean-clone commit and
the test or measurement behind it. A criterion that does not hold is left
unticked, with the measured reason.
