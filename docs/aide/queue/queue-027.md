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

### Item 203: Modes 3 and 4 re-signed by the maintainer at the bar

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
