<!-- aide-template: queue 1 -->
# FACET — Work Queue 031

> **Created:** 2026-10-12
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).
> Opens and closes **Stage 35**. Runs after the maintenance queue
> [`queue-030.md`](queue-030.md).

---

## Scope of this queue

Roadmap **Stage 35 — Programme Interface: the SegFACET Side**, next in the
run order (35 → 16). The stage is this repository's side of
`spine-failure-lab`'s `docs/project/facet-interface.md`, adopted at commit
`7436b0f` ([`../vision.md`](../vision.md) §7.5). It has five deliverables.
Two are split here, because each has two independently testable halves: the
real-label expectation (the evaluation harness's new expectation shape, then
the `rl1` reader that fills it) and artefact versioning (what a report
carries, then when its schema version moves). The queue completes the
stage, so it ends with the validation item, item 235, which
`aide check --queue 031` asked for (2026-10-12).

**Prioritisation.** Items 228, 230, 232 and 233 are independent and can be
claimed in any order. Item 229 builds on 228's list form only if the spec
chooses to express the VerSe role subsets that way; VerSe's split
directories already serve as roots. Item 231 needs 230's expectation shape.
Item 234 needs 229's role subsets and runs after queue 030's items 221 and
222, which change the held-out offset the reference records. Item 235
(validation) runs last.

**Build posture (`prototype`).** Items 228–234 are each a named Stage 35
deliverable or half of one, and item 235 is the stage validation. Nothing is built for MSKGSTT beyond what the deliverables
name: the descriptor list form serves its roles, but no MSKGSTT descriptor
is written here, since `spinelab` writes the candidate descriptors (the
interface's hand-off bundle).

**Insights folded in.** `2026-10-06-f318` (the VerSe reference's
Stage-3-derived statistics are stale for any subject whose integer and
anatomical orders disagree) is absorbed by item 234, the rebuild the
roadmap names it in. `2026-10-12-76ac` (whether sacralised or fused L5
levels count as mode 2, mode 11 or exclusions) is passed over. It is a
scoring decision Stage 16 needs, and item 231 reads `mode_id` as the table
states it.

**Numbering.** Continues at the next free integer: **228–235**.

---

## Work items

### Item 228: Descriptor subsets as explicit case-id lists

A dataset descriptor's `subsets` today name a directory root only
(`segfacet.datasets`, Stage 13). Let a subset be an explicit list of case
ids as well, resolved against the descriptor's root and `case_id` regex, so
a split manifest's roles can be named for a cohort whose roles are not
directories (roadmap Stage 35, first deliverable). An id the list names
that the root does not hold is reported, not skipped. *Testable:* a subset
given as a list resolves exactly those cases and no others; a listed id
with no matching mask raises an error naming it; a subset given as a root
resolves as before; `--subset` selects either form from the CLI.

### Item 229: VerSe20 ground-truth descriptor and dataset-role subsets

Add `src/segfacet/datasets/verse20.yaml` beside `verse19.yaml`, with a
`case_id` regex that yields the same identifiers `spinelab`'s candidate
descriptors will (`sub-verseNNN`, `_split-verseMMM` infix kept). Give both
descriptors `development`, `calibration` and `test` subsets over the
release's training, validation and test splits (the interface's
dataset-roles table), so `segfacet evaluate` can pair VerSe20 candidates by
case id and select cases by role. The committed descriptor names no
machine-local path that cannot be overridden with `--data-root`. Whether the
existing `training`/`validation`/`test` names stay as aliases is the spec's
call, given what reads them today. *Testable:* each role subset of each
descriptor resolves the cases of its release split and no other; no case
resolves in two roles; with the VerSe20 data present, every VerSe20
ground-truth mask resolves to one case id (environment-gated on the data,
skipping cleanly without it).

### Item 230: A per-label, several-modes-per-case expectation in the evaluation harness

The evaluation cohort expects one failure mode per case
(`segfacet.synth.perturbation.Expectation`), built for scripted
perturbation. Real review labels name several labels per case, each with
its own mode, and a level reviewed and found clean (mode 0). Add an
expectation of that shape and score the harness against it: a label's
expected mode is detected when a finding on that label is attributed to
that mode, and a clean label is a false positive when any finding falls on
it. The synthetic corpora's one-mode expectation keeps working unchanged
(roadmap Stage 35, third deliverable, its harness half). *Testable:* a case
with two labels at two different modes and one clean label is scored per
label; per-mode sensitivity and per-label false positives come out of the
harness for it; every existing synthetic-corpus evaluation produces the
same metrics as before.

### Item 231: The `rl1` review-label table read against a pinned schema

Read `spinelab`'s review-label table (schema tag `rl1`) into item 230's
expectation. Vendor its schema from the field table of
`docs/project/facet-interface.md` at the pinned `spinelab` commit, record
that commit beside it, and refuse a table whose schema tag differs from the
pinned one. Mode 0 rows are reviewed-clean labels. Each row's `role` is
carried through, and a test-role row is never used to fit or calibrate (the
interface's rule that a label's use follows its case's role). `mode_id` is
read as the table states it: how a transitional L5 is scored is Stage 16's
decision (insight `2026-10-12-76ac`). Roadmap Stage 35, third deliverable,
its reader half. *Testable:* a table at the pinned version becomes the
expectation, with several modes per case and mode 0 as clean; a table with
any other schema tag, or a field the vendored schema does not list, is
refused with a message naming the difference; a calibration run refuses
test-role rows; the vendored schema records the `spinelab` commit it was
copied at.

### Item 232: Every report names the FACET revision that wrote it

Write the FACET commit, and the package version, into every per-case report
(`segfacet run`) and every evaluation report (`segfacet evaluate`), so
`spinelab` can pin a report to the revision that produced it. A tree with
no git metadata (an installed wheel) records that the commit is unknown
rather than failing. Define how a revision `spinelab` consumes is tagged,
and tag nothing from inside the item: pushing a tag is the owner's. The
interface leaves FACET's versioning scheme to the owner, so the spec asks
for it (roadmap Stage 35, fourth deliverable, its revision half).
*Testable:* a per-case report and an evaluation report each carry the
commit of the checkout that wrote them and the package version; a run with
no git metadata writes a report that says so; the tagging procedure is
written where a person running a release will find it.

### Item 233: The report schema version moves whenever a feature path moves

The report `schema_version` stayed at "0.1" through items 215 and 216, which
moved nearly every feature path. Bump it once now, and make the suite fail
when the set of feature leaf paths changes without a schema-version change:
pin the leaf-path set the catalogue already generates to the version that
describes it (roadmap Stage 35, fourth deliverable, its schema half).
*Testable:* the regenerated catalogue's leaf-path set and the report's
`schema_version` agree with the pinned pair; adding or renaming one feature
path without a version change fails the suite; renaming it with a version
change and a re-pinned set passes.

### Item 234: The VerSe reference rebuilt from the development role only

Rebuild the bundled VerSe reference from the `development` role of both
releases (VerSe19 and VerSe20 training splits, item 229), replacing today's
VerSe19-training-only `reference_verse_v1.json`. Its Stage-3-derived
statistics were built from ascending-integer-order fits and are stale for
any subject whose integer and anatomical orders disagree, such as one
carrying T13 (insight `2026-10-06-f318`). Record in the artefact which
cases built it, and assert that none is from the calibration or test role.
Runs after queue 030's items 221 and 222, which change the held-out offset
the reference records. Re-measure what the default-reference CLI fires on
the corpora, as the item-125 gotcha in `CLAUDE.md` describes it. *Testable:*
the rebuilt artefact lists only development-role case ids; a descriptor
role mix-up that puts a calibration case in its inputs fails the build; a
rebuild from the same inputs is byte-identical; with the VerSe data absent
the rebuild test skips cleanly.

### Item 235: Validate stage 35: Programme Interface: the SegFACET Side

Replay the stage from a clean clone and attest each of Stage 35's four
acceptance criteria against live state. Case-id-list subsets resolve exactly
the cases named, and both VerSe descriptors resolve the three role subsets
over the release splits. An `rl1` table at the pinned version is scored by
the harness as a per-label, several-modes-per-case expectation, and a table
at any other version is refused. Every per-case and evaluation report
carries the FACET commit and a schema version, and a feature path moved
without a version change fails the suite. The rebuilt reference draws only
on development-role cases. Run the stage's use case end to end, not just the
unit suite: `segfacet evaluate` over a VerSe role subset with a table-backed
expectation, and `segfacet build-reference` from the development role, where
the VerSe data is present. Stage 35 adds no Environment-Gated Capability
Verification row unless an item does; for any row an item adds, flip it to
`✅ Verified` where the environment allows, or record in its Notes cell why
it stays `❓ Unverified`. *Testable:* each attestation cites the clean-clone
commit and the test or measurement behind it; a criterion that does not
hold is left unticked, with the measured reason.
