<!-- aide-template: queue 1 -->
# FACET — Work Queue 023

> **Created:** 2026-09-23
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).
> Opens **Stage 33**; supersedes [`queue-022.md`](queue-022.md) (Stage 32,
> complete at item 169).

---

## Scope of this queue

Opens roadmap **Stage 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the
bar** (G2, G7, G8). It holds ten items, which is `loop.queue_cap`, and covers
**D0** (protective fixes), **D1** (the lordotic geometric base, the corpus
rendering and the status report's corpus section) and **D2** (fixtures that
express their mode), except `force_overlap`.

**Stage 33 spans three queues.** Its deliverables come to roughly 25 items
against a cap of 10. This queue re-grounds the **corpus**. The next queue
re-homes the **rules** (D3), and `force_overlap` goes with it, because its
disposition is a joint decision about the fixture and the `overlap` rule. The
queue after that holds D4 (the bar checker, the ladder re-measurement and the
generated rule table), D5 (the at-the-bar sign-off gate) and D6 (the
stage-validation item, which also closes Stage 32's criterion 1). This queue
does not close the stage, so it has no validation item.

**Expected sets are recorded as measured, and they move again later.** Each
fixture item authors its case's `expected_firing` in
`src/segfacet/failure_modes.py` from the firing measured under **today's**
rules. Where the review has already found that today's rules are wrong for the
case, the case records that honestly: `split_own_label` fires `coverage` on a
"missing" T13, and `crop_at_border` fires `bounds` on the L5 remnant. The rule
changes, and the expected-set edits they bring, are the next queue's work. The
specificity ratchet (item 163) holds every step to what the specification
says.

**Prioritisation.** D0 leads, as the roadmap pins. Item 170 (the
session-scoped fixtures) makes each later regeneration cheaper to test. Item
171 (the literal negative controls) keeps a moved corpus value from turning a
control green. Item 172 (validated `UNUSED_OPERATOR_REASONS`) comes before any
operator falls out of use. Item 173 (the lordotic base) comes next, because
every D2 fixture is authored on it. Items 174–177 are independent of each
other and can be claimed in any order after 173. Item 178 (the corpus
rendering) runs after them so the sheet shows the finished fixtures. It is the
last item that draws on the prototype directory, so it deletes it. Item 179
(the status report) needs only 173 and may run whenever it is unblocked.

**Every corpus item carries the reconciliation risk the roadmap names.** A
corpus change reaches tests that pin corpus *values* without naming any corpus
file. So each item's sweep asks what new values the change emits, and greps
for assertions that compare fresh output against a literal set. Each item also
follows the LF-pin gotcha for the regenerated manifests. Every value a spec
quotes is re-measured on the new base, never carried over.

**Build posture (`prototype`).** D0's three items are justified siblings of
the corpus regeneration: each makes it cheaper, or stops it from passing
silently (roadmap Stage 33 D0). Items 178 and 179 are D1 deliverables, and the
sheet is one of D5's inputs.

**Numbering.** Continues at the next free integer: **170–179**.

---

## Work items

### Item 170: Session-scoped `aide check` and specification-regeneration fixtures

About twelve tests each run the whole `aide check` (11–13 s apiece), and
about fifteen regenerate the failure-mode specification or traceability
artifacts from scratch (7–27 s apiece). One session-scoped `run_checks`
result, and one session-scoped regeneration fixture that is run twice for the
run-to-run comparison, serve all of them (`insights.md`, 2026-09-18). A test
that pins the warning set of `aide check`, rather than asserting no errors, is
the per-item shape retired on 2026-09-16. It is removed, not ported. Changes
no assertion's meaning. *Testable:* every migrated test still fails on the
defect it guards, which the Testing Strategy shows by name for one
representative per cluster. `--durations` names none of the migrated tests
among its slowest entries.

### Item 171: Literal negative controls rebuilt from live values

A negative control whose "wrong" input is a literal stops being a control as
soon as live state drifts onto that literal, and it reports green when that
happens. `test_151`'s `test_adv_ac35_status_counts_parser_rejects_wrong_n`
(the literal `15 modes`) is the known remaining instance (`insights.md`, item
167, 2026-09-20). Rebuild it from the live value plus a constructed
perturbation. Then grep `tests/` for the class: a "must differ / must reject"
assertion whose wrong input is a literal compared against a live-derived
value. Each hit is rebuilt the same way or recorded with why it cannot drift.
*Testable:* each rebuilt control still rejects its perturbed input when the
live value is monkeypatched to equal the old literal.

### Item 172: `UNUSED_OPERATOR_REASONS` entries validated

`traceability._build_exercise` reads `UNUSED_OPERATOR_REASONS.get(name, "")`,
so a stale or contradictory entry is silently accepted as a legitimate record
(`insights.md`, item 162, 2026-09-20). Two cases become conformance conflicts
the module reports: an entry naming an operator that is not registered, and
an entry naming an operator that is registered and used by a corpus case.
This lands before the fixture items, because re-authoring `crop_at_border`
(item 175) may take the current translate-and-clip operator out of use, and
that would be the first entry. *Testable:* each of the two seeded conflicts
fails the check with a message naming the operator. The empty mapping on this
tree reports nothing.

### Item 173: The lordotic geometric base

Replace `synth/clean_gt.py`'s five axis-aligned boxes with a lordotic L1–L5:
an 8 mm inter-body gap, and per-level sagittal tilts of −8°, 0°, +8°, +18° and
+35° (L1…L5, positive meaning the anterior edge is lower). The A-P centroid
path is the integral of the tilts, and there is no lateral curve
(`insights.md`, 2026-09-22). Absorb the base builder from
`scripts/prototypes/2026-09-22-lordotic-corpus/lordotic_spine.py` into
`src/segfacet/synth/`. Regenerate both committed manifests and every
downstream generated artifact. Every operator that assumes axis-aligned bodies
is made to work on the tilted base: `fragment` and `split` cut along array
axis 2. `fragment` is parked as mode 1's catch-all case, regenerated on the
new base with no further change. A case whose measured firing changes has its
`expected_firing` re-authored in the specification from the new measurement,
with the reason stated. *Testable:* the clean control fires nothing under the
bundled default config (one component per label, no finding). Both corpora
regenerate byte-identically. The specificity ratchet is green.

### Item 174: Mode 3's two sub-types: `split` at a 20 % cap, and `split_own_label`

Re-author `split` on the lordotic base so that a caudal cap of L4, about 20 %
of the body and cut below an S-I level, is relabelled L5. Add a new operator
and case, `split_own_label`: the same cap under an independent label, with
the labels cranial to it shifted up (L5 stays, the cap becomes L4, the rest
of L4 becomes L3, and so on upward) (`insights.md`, 2026-09-22, the mode-3
sub-types and the split fraction). Both are attributed to mode 3.
`neighbour_contact`'s threshold is re-examined against the contact areas the
tilted base actually produces. Each case's `expected_firing` is authored from
the measured firing, including `split_own_label`'s known `coverage`
T13 finding, which is recorded as a co-detection that the next queue's
`CANONICAL_ORDER` item removes. *Testable:* both operators are deterministic
under their seed and carry the machine-readable record. The corpus
regenerates byte-identically. The ratchet and the exercise report pick up the
new case and operator without being edited.

### Item 175: `crop_at_border` as a crop of the volume

Replace the operator that translates one vertebra past the anterior face with
a crop of the clean-control **volume**. The inferior field-of-view cut removes
65 % of L5 (L5 remnant ≈ 7 719 mm³ on the prototype, flagged
`touches_inferior`) (`insights.md`, 2026-09-22, the crop and its settled
depth). The case stays `fov_truncation`'s fixture. Its expected set records
what fires today (`bounds` on the remnant's volume, with `border` suppressing
the expected end), because it is the fixture the next queue's border gating of
the size rules is measured on. If the old operator falls out of use, it gets
the first `UNUSED_OPERATOR_REASONS` entry (item 172) or is deleted.
*Testable:* the cropped case's L5 volume and extent differ from the clean
control's, and the image face, not a translation, cuts it. The corpus
regenerates byte-identically. The ratchet is green.

### Item 176: `fuse_adjacent` bridged and renumbered

Today `fuse_adjacent` relabels L4 as L3 and leaves the gap between them, which
yields two components and a hole in the sequence. Re-author it as one
connected label: the L3–L4 gap is bridged under L3, and L5 is renumbered to L4,
so the sequence stays continuous (`insights.md`, 2026-09-22, the fused case).
On the prototype the result fires nothing under the shipped rules. That empty
expected set is authored honestly, with the reason that mode 2's own signal
(the inter-centroid-spacing rule) belongs to a later per-mode queue. *Testable:*
the fused label is one connected component spanning both bodies, and the
present labels are a continuous run. The measured firing equals the authored
expected set. The corpus regenerates byte-identically.

### Item 177: `displace` moves mostly left-right

Re-author `displace` so its translation is mostly left-right, with a reduced
anterior-posterior component. Today it moves 13 voxels along both non-stacking
axes (`insights.md`, 2026-09-22, the `displace` case). Its expected set and its
severity ladder are re-measured on the new base. Its re-attribution to a
displaced-vertebra condition is the next queue's work (D3), not this item's.
*Testable:* the recorded displacement vector's L-R component dominates its A-P
component. The corpus regenerates byte-identically. The ratchet is green.

### Item 178: A committed corpus rendering

One sheet shows every geometric corpus case as a sagittal and a coronal
max-label projection, with the voxels changed against `clean_control`
outlined. It is regenerated from the committed manifest (`insights.md`,
queue-022, 2026-09-21, ticked into roadmap Stage 33 D1). Absorbs
`corpus_sheet.py` from the prototype directory. This is the last item that
draws on `scripts/prototypes/2026-09-22-lordotic-corpus/`, so it deletes the
directory once nothing absorbed from it is still missing. The rendering is an
input to D5's gate. *Testable:* the sheet regenerates from the manifest without
error and holds one panel pair per case. The changed-voxel outline of
`clean_control` is empty. The prototype directory no longer exists and nothing
imports from it.

### Item 179: The status report's corpus section re-keyed off the generated specification

`scripts/aide_status_report.py`'s Synthetic Failure Corpus section still
carries a hand-typed eight-mode `FAILURE_MODES_LEGEND`, the "eight catalogued
modes" prose, an `N/8` card and a "modes 1/4/8" footnote. The manifest rows it
tabulates carry the sixteen-mode numbering, so the legend mislabels its own
table (`insights.md`, queue-022, 2026-09-21). Re-key the section off the
committed `docs/aide/failure_modes.generated.json` and
`traceability_matrix.generated.json`, read with stdlib `json` only, as the
Feature Catalog section already reads its JSON. *Testable:* the rendered
section's mode titles and count come from the generated JSON. Mutating a
title in a copy of that JSON changes the rendering. No hand-typed mode legend
remains in the script.
