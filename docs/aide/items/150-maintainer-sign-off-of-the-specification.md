# Item 150 — Maintainer sign-off of the failure-mode specification

> **Created:** 2026-09-04 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 30 — Failure-Mode Specification: the §6 catalogue as an authored source
> **Queue:** [`../queue/queue-020.md`](../queue/queue-020.md) · Item 150
> **Objectives:** G2 (detect the catalogued failure modes), G8 (extensible — the
> specification is the authored source every conformance artifact reports against)
> **Suggested branch:** `aide/150-maintainer-sign-off-of-the`

---

## Description

Stage 30 **D6**. Items 144–149 authored the failure-mode specification
(`src/segfacet/failure_modes.SPECIFICATION`), collapsed the five partial sources
onto it, and re-pointed the generated artifacts at it as conformance reports.
Nothing in that chain asked a **person** whether the resulting catalogue is
right. This item is that question, and it is the stage's **human checkpoint** in
the sense Stage 19's item-106 steering review was one: the maintainer reads
[`../failure_modes.generated.md`](../failure_modes.generated.md) **entry by
entry** — all ten entries, eight `vision.md` §6 seed modes plus mode 9
(implausible tissue, derived `validated`) and mode 10 (the first `proposed`
entry) — and either accepts the rendering or names the entries to change. The
date and the outcome are then recorded in the specification module's **own
docstring**, exactly where `feature_docs.py`'s `STATUS_OVERRIDES` comment records
the Stage-19 steering review's date and outcome, and the walkthrough itself is
transcribed into this spec under `### Stage-30 maintainer sign-off`.

**This item is a checkpoint, not a build.** It ships no new rule, no new mode, no
schema change and no new behaviour. Its whole deliverable is (a) a human gate in
[`../progress.md`](../progress.md) and (b) the recorded sign-off. The catalogue's
content changes **only** where the maintainer's reading says it must, and such a
change is an edit to an authored `ModeSpec` field followed by a regeneration —
never a new field, a new mode, or a new derivation.

### What is agent work and what is the human's

The split is the point of the item, so it is stated before anything else.

| Step | Who | What |
|---|---|---|
| 1 | agent | Prepare the review surface: regenerate both artifacts, confirm they are byte-identical to the committed copies, and assemble the review pack (below). |
| 2 | agent | Raise the human gate in `../progress.md`'s `## Human gates` table with `Blocks: 139, 140, 141, 142`, `⏳ Awaiting`. |
| 3 | agent | **STOP.** Hand back. Nothing further on this item is agent work until the gate is resolved. |
| 4 | **human** | Read the ten entries and decide. Resolve the gate with `python .aide/scripts/aide.py gate approve <n> --evidence "…"` (or `gate decline`) — see `aide gate list` for `<n>`. |
| 5 | agent | Only after ✅ Approved: apply the changes the maintainer named, regenerate both artifacts, write the `Signed off:` record into the module docstring, transcribe the walkthrough into this spec, append any out-of-scope observation to `../insights.md`, commit. |

**No agent may approve or decline the gate.** Not the builder, not the validator,
not an orchestrator, not a subagent, and not this item's own author. `aide gate
approve` / `aide gate decline` are the maintainer's commands and only the
maintainer's; the gate exists precisely because the decision is not derivable
from the work (`.aide/conventions.md` §1 → Human gates). Resolving it by
hand-editing the table is equally forbidden — AC2 tests the Status cell against
the exact string `set_gate_status()` writes, so a hand edit is detectable and
fails.

**If the gate is declined**, no sign-off is recorded, this item does **not**
complete, and the loop hands back for re-planning. A decline keeps blocking
(`.aide/conventions.md` §1); it is not a route to a green suite.

### The review pack the maintainer is handed

Assembled by step 1, all of it already in-tree:

1. [`../failure_modes.generated.md`](../failure_modes.generated.md) — the review
   surface proper, one `## Mode N` section per entry.
2. [`../traceability_matrix.generated.md`](../traceability_matrix.generated.md) —
   the conformance report item 149 re-pointed at the specification, so the
   maintainer sees expected-vs-measured firing beside each entry.
3. Three **open** `insights.md` entries whose own text defers a decision to this
   item, which the maintainer must be shown rather than left to find:
   - the `derive_status` vacuous-agreement half (`item 145, 2026-09-03`): the
     declaring-rule precondition landed in item 146, but an authored
     `expected_firing=()` on a case that fires nothing still agrees vacuously
     and can validate. Whether that is acceptable lifecycle semantics is
     explicitly *"a lifecycle-semantics call for the maintainer at item 150"*.
   - the `dx_mm` / `dy_mm` / `dz_mm` classification (`item 148, 2026-09-04`):
     classified `signal` for `mislabel` while the firing decision reads
     `offset_mm` alone; the entry records the reclassification as *"a decision
     for item 149/150 rather than a review fix"*.
   - the geometric-only rule-attribution scan (`item 148, 2026-09-04`): the
     matrix's attribution column covers only the geometric corpus, *"leaving the
     seam undocumented at the artifact item 150 signs off"*.
4. Per entry, the eight facets the queue line names: **definition,
   discriminator, expected firing sets, severity, observability, per-edge
   evidence rungs, lifecycle status, provenance**.

### Scope fence

This item does **not**: write or change a rule, threshold, extractor or verdict;
add or remove a mode; change the `ModeSpec` schema, any derivation
(`derive_status`, `derive_mode_rung`, `measured_firing`) or either renderer; add
a corpus case; edit `vision.md` or `roadmap.md`; or tick a Stage-30 acceptance
criterion (see **D1** in Decisions & Trade-offs — the stage acceptance replay is
item 151's, and it requires a clean-tree run this item does not perform).

> **Fence widened 2026-09-14 by the maintainer, during the review itself.**
> The entry-by-entry read did not confirm the catalogue; it re-organised it
> (one mode retired, one split, one re-homed as a condition, one added, ids
> re-assigned in a one-tier hierarchy, two observability classes added, the
> `validated` semantics tightened). Offered the choice between capturing the
> rework for a later queue, widening this item, or declining the gate, the
> maintainer chose to **widen this item and apply the rework now**, with the
> eval-harness re-key deferred to a follow-up item. So this item *did*: change
> the `ModeSpec` schema (`parent`), add `ConditionSpec`/`CONDITIONS`, change
> `derive_status`, both renderers and `specification_conflicts`; move every
> rule's `RuleModeDeclaration` (no `evaluate` body or threshold changed); add
> the `condition-signal` path role; add one synthetic operator and two corpus
> cases and regenerate both manifests; re-key `feature_docs.MODE_ANCHOR_PATHS`;
> and reconcile the tests that pinned the old catalogue. It still did not edit
> `vision.md` or `roadmap.md`, tick any Stage-30 criterion, or change a rule's
> behaviour. The walkthrough below records what each entry became and why.
> On 2026-09-15, with the gate still awaiting, the maintainer continued the
> same review inside the same widened fence: paired sub-modes split into
> single defects (sixteen modes), the schema gained `scope`, and the rule
> declarations, case `failure_mode` values and anchors moved again.

## Acceptance Criteria

_Every criterion below is an invariant over the resulting content, re-checkable
after merge. **The AC block is expected to be red until the maintainer resolves
the gate** — that redness is the checkpoint working, not a defect to route
around._

- [ ] **AC1: the gate exists, is unique, and reaches the four held items.**
  Parsing `docs/aide/progress.md` with `.aide/scripts/aide.py`'s
  `human_gates()` (imported in-process, the
  `test_114_documentation_corrections.py` idiom) yields **exactly one** row whose
  Gate cell contains the literal `Stage 30 failure-mode specification sign-off`.
  That row's `blocks` list equals `[139, 140, 141, 142]` exactly (measured
  equality, not containment), its `stage` is `None`, its `blocks_all` is `False`,
  and its `kind` is one of `"awaiting"`, `"approved"`, `"declined"` — never
  `None`, which is how the engine reports an unrecognised status cell.

- [ ] **AC2: the gate's Status cell is byte-equal to what `aide gate` writes, so
  a hand edit fails.** Let `d` be the ISO date parsed out of the live Status
  cell. Calling `set_gate_status(text, <this row's 1-based index>, <this row's
  kind>, today=d)` on the committed `progress.md` text reproduces the live line's
  Status cell **character for character**. The Decision cell is non-empty after
  `.strip()`, contains no `|` and no line break, and is not one of the
  placeholders `""`, `"TBD"`, `"n/a"`, `"pending"`. `d` is not in the future
  (`<= datetime.date.today()`).

- [ ] **AC3: the gate is resolved approved, and the block is released only
  there.** The row's `kind` is `"approved"`, and the gate is absent from
  `blocking_gates()` over the same lines. Adversarially: the same lines with only
  this row's Status cell replaced by `⏳ Awaiting` put the gate **back** into
  `blocking_gates()`, and with `❌ Declined` likewise — a declined gate still
  blocks. The adversarial variants are built in memory; `progress.md` is not
  written.

- [ ] **AC4: `aide check` reports the gate's state and warns about no unfilled
  slot.** `run_checks(repo_root, load_config(repo_root))` returns `errors == []`.
  No returned warning matches `unfilled template slot`, and the `## Human gates`
  section of `progress.md` contains no `{{` sequence at all. Classifying every
  returned warning by the shape idiom of
  `test_145_eight_hypothesised_modes.py::_classify_warning`, no warning falls
  outside the recorded baseline classes (`assumptions-block`,
  `awaiting-a-decision`, `branch-state`, `retracted-criterion`). Adversarially:
  with this row's Status cell set to `⏳ Awaiting` in a temporary copy, exactly
  one warning names this gate and it classifies as `awaiting-a-decision` — the
  engine reports the gate's state rather than staying silent about it.

- [ ] **AC5: the module records a sign-off, and the item-144 placeholder is
  gone.** `segfacet.failure_modes.__doc__` contains a `Sign-off` section
  (underlined heading, the shape the module's other sections use) whose body
  contains **exactly one** line matching, anchored,
  `^Signed off: (\d{4}-\d{2}-\d{2}) -- (.+)$`. The literal sentence `No
  maintainer sign-off is recorded yet.` appears nowhere in the module source.
  The docstring still carries item 146's record intact — the literal `item 146`
  and at least one `src/segfacet/*.py` path that resolves to a real file — so the
  edit is additive (this is what `test_146…::test_ac35_…` already pins).

- [ ] **AC6: the recorded date is real and not in the future.**
  `datetime.date.fromisoformat()` parses group 1 of AC5's match; the result is
  `<= datetime.date.today()` **and** `>= date(2026, 9, 4)` — the day item 149
  landed, i.e. the earliest date on which the reviewed rendering existed. A date
  outside either bound fails, naming the bound and the value.

- [ ] **AC7: the recorded outcome is substantive and drawn from the disposition
  vocabulary.** Group 2 of AC5's match, after `.strip()`, is non-empty, is at
  least 40 characters, contains exactly one of the two literals
  `accepted as rendered` / `accepted with changes`, and is not any of
  `"TBD"`, `"n/a"`, `"see review"`, `"pending"`, `"signed off"`, or a bare repeat
  of either disposition literal with nothing else. It also contains the literal
  relative path of this spec, `docs/aide/items/150-maintainer-sign-off-of-the-specification.md`,
  and that path resolves to a real file — the transcript pointer, the
  `STATUS_OVERRIDES` comment's precedent.

- [ ] **AC8: the walkthrough covers every entry, re-derived from the primary
  source.** This spec contains the heading `### Stage-30 maintainer sign-off`.
  The set of integers `N` for which a line matching `^- Mode (\d+) — ` appears
  under that heading (up to the next `###` or `##`) equals
  `set(segfacet.failure_modes.SPECIFICATION)` **exactly** — no missing entry, no
  entry for an id the specification does not carry, and the count is read from
  `SPECIFICATION`, never hardcoded as 10.

- [ ] **AC9: every entry line carries a disposition, and a changed entry names
  what changed.** Each `- Mode N — ` line contains exactly one of the literals
  `confirmed` / `changed`. Every line reading `changed` additionally names at
  least one real authored field: a token drawn from the union of
  `{f.name for f in dataclasses.fields(ModeSpec)}`,
  `{f.name for f in dataclasses.fields(IntendedRule)}` and
  `{f.name for f in dataclasses.fields(CorpusCaseExpectation)}`, recomputed live
  rather than listed by hand. A line reading `changed` that names no such field
  fails, naming the mode id.

- [ ] **AC10: the eight review facets are declared and each resolves onto a real
  field.** The preamble under `### Stage-30 maintainer sign-off` (above the first
  `- Mode ` line) contains all eight facet words verbatim — `definition`,
  `discriminator`, `expected firing`, `severity`, `observability`, `evidence
  rung`, `status`, `provenance` — and a mapping in that preamble binds each to a
  dataclass field name that exists in the live field union of AC9. A facet whose
  named field does not exist fails, naming the facet.

- [ ] **AC11: both artifacts are byte-identical to a fresh regeneration.**
  `segfacet.failure_modes.main(["--json", <tmp>, "--md", <tmp>])` into a tmp
  directory produces a JSON that `segfacet.synth.golden.assert_matches_committed_artifact`
  accepts against `docs/aide/failure_modes.generated.json`, and a Markdown whose
  UTF-8-decoded text equals the committed
  `docs/aide/failure_modes.generated.md`'s. Both committed files contain no
  `\r`, end with exactly one `\n`, and are non-empty. Two successive
  regenerations into different paths agree byte-for-byte (the run-to-run
  determinism half).

- [ ] **AC12: every entry the review changed is present in both artifacts.** For
  every mode in `SPECIFICATION` and every authored string field the renderers
  emit (`name`, `short_name`, `definition`, `discriminator`, `observability`,
  `severity`, `provenance`, `mechanism`), the live value appears in that mode's
  `## Mode N` section of the committed `.md` **and** at the matching key of the
  committed `.json` entry — recomputed from `SPECIFICATION`, never from a
  fixture, so an authored field the maintainer changed and a regeneration that
  was skipped cannot both pass. Empty-string fields are skipped explicitly, and
  the test asserts that at least one field per mode was actually compared, so the
  loop cannot pass vacuously.

- [ ] **AC13: the four held Stage-20 items are still ⏸️ Deferred.** In
  `docs/aide/progress.md`'s Stage 20 section, the deliverable bullet carrying
  `*(Item 139)*`, and likewise 140, 141 and 142, each has `⏸️` as its **leading**
  bullet icon (the structural status position of `.aide/conventions.md` §1 →
  status-icons). Read by locating the four bullets, not by scanning the file for
  the icon. _This is a **dated** claim about the world, true while Stage 20's
  remainder is unqueued and guaranteed to become false when it is queued: the
  first item that lands any of 139–142 **must** list `tests/test_150_maintainer_sign_off.py`
  under its **Authorised paths → May change** and update this test. Recorded here
  so that item's author does not discover it as a red suite._

- [ ] **AC14: every insight this item raised is well-formed and honestly dated.**
  Every line in `docs/aide/insights.md` (and every
  `docs/aide/insights/archive-*.md`, per CLAUDE.md's archive gotcha) whose
  provenance names `item 150` matches the §1 grammar
  `- [ ] <knowledge|defect|gap|automation|framework> — <text> *(item 150, YYYY-MM-DD, engine X.Y.Z)*`,
  carries a date `<= datetime.date.today()`, and carries an engine token equal to
  the contents of `.aide/VERSION` stripped. No pre-existing line is reworded,
  reordered or deleted — the count of non-`item 150` lines is `>=` its value at
  this item's base.

- [ ] **AC15: the zero case is stated, not left silent.** The transcript's
  preamble contains **either** at least one out-of-scope observation whose text
  appears verbatim in `docs/aide/insights.md` (or an archive file), **or** the
  literal words `no out-of-scope observation recorded`. Both being absent fails.
  This is item 106's `no override recorded` discipline: a review that legitimately
  raises nothing passes, and a review that skipped the step does not.

## Assumptions

- **A1 (engine 1.37.0, re-checked 1.52.1, re-checked 1.59.0):** `aide gate approve|decline <n> --evidence "…"` writes
  the Status cell as exactly `f"{icon} ({YYYY-MM-DD})"` with icon
  `✅ Approved` / `❌ Declined`, and writes the note into the row's fourth cell,
  rejecting a note containing `|` or a newline (`set_gate_status`,
  `.aide/scripts/aide.py`). AC2 is written against that shape. If a later engine
  changes the rendering, AC2's test re-derives the expected cell by calling
  `set_gate_status` rather than pinning the literal, so it tracks the engine
  instead of breaking on it.
- **A2 (engine 1.37.0, re-checked 1.52.1, re-checked 1.59.0):** a `## Human gates` row is four cells
  (`Gate | Blocks | Status | Decision`), the Blocks cell accepts bare item
  numbers, and `blocking_gates()` treats every kind other than `approved` —
  including `declined` — as still blocking. AC1/AC3 rest on this.
- **A3 (engine 1.37.0, re-checked 1.52.1, re-checked 1.59.0):** `run_checks` emits the human-gate warning
  `progress.md:<n>: human gate <k> (…) is awaiting a decision — blocks …` for an
  unresolved gate and nothing for a resolved one; the unfilled-slot lint
  (`template_residue_errors`) scans every `*.md` under `docs/aide/` for a bare
  doubled-brace slot marker and reports it as an **error**, not a warning. AC4 asserts `errors ==
  []` for that reason and additionally checks the warning list for the literal
  text, so it holds whichever severity a later engine uses.
- **A4:** the gate index is **5** as of this spec's writing (four rows exist).
  The index is positional and shifts if a row is inserted above, so both the
  human instructions and AC2's test resolve it by matching the Gate cell's
  literal text through `human_gates()`, never by the constant 5. `aide gate list`
  is the authority at the moment of approval.
- **A5:** the sign-off record is read from `segfacet.failure_modes.__doc__`, not
  from the source file's text. The suite is never run under `python -OO`, which
  strips docstrings and would make AC5–AC7 fail for a reason unrelated to the
  claim. This matches `test_146…::test_ac35_…`, which already reads `__doc__`.
- **A6:** the maintainer approves. The docstring record, the transcript and
  AC5–AC12 all presuppose an approval; a decline produces none of them and the
  item hands back unfinished rather than recording a negative sign-off.
- **A7:** the reviewed rendering is the one committed at this item's base — ten
  entries, nine deriving `validated`, mode 10 deriving `proposed` (measured
  2026-09-04 on `aide/queue-020`). If a change the maintainer calls for moves a
  derived status, AC11/AC12 still hold because both sides are recomputed; only
  the transcript's own prose needs to say so.
- **A8:** `.gitattributes` already pins both artifacts `text eol=lf` (lines 60
  and 61), so this item adds no pin and `aide check`'s `.gitattributes` lint has
  nothing new to say. Verified 2026-09-04. Any regeneration must still be written
  with `write_bytes` and `\n` — which `failure_modes.main` already does; this
  item changes no writer.

## Implementation Steps

1. **Confirm the review surface is current.** Regenerate into a scratch
   directory and confirm byte-identity with the committed pair (AC11's
   mechanism). Do **not** rewrite the committed files if they already match.
2. **Assemble the review pack** as listed in the Description: the two generated
   Markdown artifacts plus the three named open `insights.md` entries. Read them
   with `python .aide/scripts/aide.py insights list --open`; do not hand-parse the
   file.
3. **Add the gate row** to `docs/aide/progress.md`'s `## Human gates` table —
   the one hand edit to that document any role may make. Four cells:
   - Gate: `Stage 30 failure-mode specification sign-off — the maintainer reads
     docs/aide/failure_modes.generated.md entry by entry (all ten entries;
     definition, discriminator, expected firing sets, severity, observability,
     per-edge evidence rungs, lifecycle status, provenance) and either accepts
     the rendering or names the entries to change. Date and outcome are recorded
     in src/segfacet/failure_modes.py's own docstring, the
     feature_docs.py::STATUS_OVERRIDES precedent`
   - Blocks: `139, 140, 141, 142`
   - Status: `⏳ Awaiting`
   - Decision: the pointer to this spec's transcript heading and the explicit
     statement that no agent may resolve it.
   No `|` and no line break in any cell.
4. **Verify** with `python .aide/scripts/aide.py gate list` and
   `python .aide/scripts/aide.py check` that the row parses, reaches items
   139–142, and produces exactly one new warning of the `awaiting-a-decision`
   class and no error.
5. **STOP and hand back.** Report the gate's index and the review pack. Do not
   write the docstring record, do not write the transcript, do not run
   `aide gate approve`, and do not attempt to complete the item.

   --- everything below runs only after the human has resolved the gate ---

6. **Read the resolution.** `aide gate list`. If ❌ Declined: stop, record the
   decline's reason in this spec's Decisions log, and hand back — the item does
   not complete.
7. **Apply the changes the maintainer named**, if any: edit the authored
   `ModeSpec` fields in `src/segfacet/failure_modes.py` only — no schema change,
   no new mode, no derivation change, no rule change.
8. **Regenerate** both artifacts:
   `.venv/bin/python -m segfacet.failure_modes`. If step 7 changed a field the
   traceability matrix renders, regenerate that pair too
   (`.venv/bin/python -m segfacet.traceability`) and confirm the two conformance
   artifacts agree.
9. **Write the sign-off record** into the module docstring's `Sign-off` section,
   replacing the item-144 placeholder sentence. One anchored line, then prose:

       Sign-off
       --------
       Signed off: <YYYY-MM-DD> -- <outcome sentence containing exactly one of
       "accepted as rendered" / "accepted with changes", the entry count, and
       the path docs/aide/items/150-maintainer-sign-off-of-the-specification.md
       where the full walkthrough is transcribed>.

       <one paragraph: what the maintainer changed, or that nothing changed.>

10. **Transcribe the walkthrough** into this spec under a new
    `### Stage-30 maintainer sign-off` heading in Decisions & Trade-offs: the
    date; the facet-to-field mapping (AC10); the zero-case sentence or the
    out-of-scope observations (AC15); then one `- Mode N — ` line per entry, each
    reading `confirmed` or `changed`, and a `changed` line naming the field.
11. **Append** any out-of-scope observation as one line each in
    `docs/aide/insights.md`, in the §1 grammar with provenance `item 150` and the
    engine read from `.aide/VERSION`. Append only; reword, reorder and delete
    nothing.
12. **Re-run** `python .aide/scripts/aide.py check` — no error, and the gate
    warning is gone now that the gate is resolved.

## Authorised paths

> **Rewritten 2026-09-14 when the maintainer widened the item** (see the
> Scope fence amendment above and the "Stage-30 maintainer sign-off"
> transcript). The original list — the module docstring's `Sign-off` section,
> the two generated artifacts, the gate row, this spec, its tests and appended
> insight lines — is a strict subset of the list below.

**May change:**

- `src/segfacet/catalogue.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/eval/per_mode.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/eval/severity_ladder.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/failure_modes.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/feature_docs.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/heuristics/border.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/heuristics/bounds.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/heuristics/coverage.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/heuristics/fragmentation.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/heuristics/intensity.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/heuristics/intensity_reference_delta.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/heuristics/mislabel.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/heuristics/overlap.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/heuristics/reference_delta.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/heuristics/rule.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/heuristics/sequence.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/synth/__init__.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/synth/component_shape.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/synth/corpus.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/synth/coverage_border_overlap.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/synth/identity_ordering_alignment.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/synth/intensity.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/synth/perturbation.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/synth/regression.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `src/segfacet/traceability.py` — the signed-off taxonomy applied: schema, declarations, operators, harnesses, anchors, legacy eval names (no rule's `evaluate` body or threshold changed)
- `tests/corpus/fixtures/fuse_adjacent_seg.nii.gz` — both manifests regenerated by their generators; two new fixtures
- `tests/corpus/fixtures/remove_level_relabel_seg.nii.gz` — both manifests regenerated by their generators; two new fixtures
- `tests/corpus/intensity/manifest.json` — both manifests regenerated by their generators; two new fixtures
- `tests/corpus/manifest.json` — both manifests regenerated by their generators; two new fixtures
- `docs/aide/failure_modes.generated.json` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `docs/aide/failure_modes.generated.md` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `docs/aide/feature_catalogue.generated.json` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `docs/aide/feature_catalogue.generated.md` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `docs/aide/golden-decision-table.md` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `docs/aide/golden_evidence.generated.json` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `docs/aide/insights.md` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `docs/aide/items/150-maintainer-sign-off-of-the-specification.md` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `docs/aide/progress.md` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `docs/aide/queue/queue-020.md` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `docs/aide/traceability_matrix.generated.json` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `docs/aide/traceability_matrix.generated.md` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `docs/corpus-s-axis-correction.md` — regenerated artifacts, the sign-off transcript, the queue's dated scope-fence annotation, appended insight lines, the gate row and whatever the `aide` CLI writes; the decision table and the item-143 record gain rows for the two new fixtures
- `tests/test_036_perturbation_framework.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_037_component_shape_perturbations.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_038_coverage_border_overlap_perturbations.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_039_identity_ordering_alignment_perturbations.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_040_synthetic_corpus.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_041_regression_suite.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_042_golden_determinism.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_057_acceptance_stage7.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_091_stage14_acceptance.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_099_per_mode_metrics.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_100_severity_ladder.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_101_compare_runs_cli.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_102_stage18_validation.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_103_feature_catalogue.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_105_golden_decision_table.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_106_stage19_validation.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_116_ras_native_corpus.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_120_leave_one_out_offset.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_121_tangent_orientation.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_125_stage28_validation.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_126_golden_retirement.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_131_tangent_direction_normalisation.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_132_monotonicity_against_traversal_order.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_134_decision_table_evidence_companion.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_135_stage29_validation.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_136_rule_mode_declarations.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_137_mode_less_rule_disposition.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_138_traceability_matrix.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_143_s_axis_correction.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_144_failure_mode_specification.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_145_eight_hypothesised_modes.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_146_ninth_mode_and_first_proposed.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_147_specification_is_the_record.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_148_per_path_mode_attribution.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_149_conformance_report.py` — reconciled to the signed-off catalogue (item-150 tests are new)
- `tests/test_150_maintainer_sign_off.py` — reconciled to the signed-off catalogue (item-150 tests are new)

**Asserts against:**

- `.aide/scripts/aide.py` — `human_gates`, `blocking_gates`, `set_gate_status`,
  `run_checks` and `load_config` are imported in-process and read live by
  AC1–AC4. Unchanged.
- `.aide/VERSION` — the engine token AC14 compares each `item 150` insight
  against. Unchanged.
- `docs/aide/vision.md` — §6's numbered seed titles, read live through
  `failure_modes.vision_seed_titles()` during regeneration (AC11). Unchanged,
  and framework/process-gated regardless; its re-issue is a recorded follow-up.
- `docs/aide/roadmap.md` — unchanged.
- Every rule's `evaluate` body and thresholds (the rule modules are listed
  under May change for their declarations only) — no behaviour moved:
  `run_rules` on a fixed record is unchanged, which the regenerated corpus
  manifests' measured firing sets attest.
- `.gitattributes` — the `text eol=lf` pins AC11's LF assertions rest on
  (**A8**). Unchanged.

## Testing Strategy

One focused test per AC in a new `tests/test_150_maintainer_sign_off.py`,
grouped into the five blocks the ACs form (gate, sign-off record, walkthrough,
artifacts, housekeeping).

**Adversarial and edge cases to cover explicitly:**

- **Hand-edited gate.** AC2's test must fail on a Status cell that reads
  `✅ Approved` with no date, `✅ approved (2026-09-05)` (wrong case), or a date
  in a non-ISO shape — all built as in-memory variants, never written to
  `progress.md`.
- **A declined gate still blocks.** AC3's `❌ Declined` variant is the case a
  reader most often assumes is "resolved, therefore released".
- **Future and pre-history dates.** AC6 must reject `date.today() +
  timedelta(days=1)` and `2026-09-03` (before item 149 landed) when fed to the
  same parser the live assertion uses — test the parser, not only the live value.
- **A placeholder outcome.** AC7 must reject each of the placeholder strings and
  a bare `accepted as rendered` with nothing else.
- **A vacuous walkthrough.** AC8's set equality must fail both directions: a
  transcript missing mode 10, and one carrying a `- Mode 11 — ` line. AC12 must
  fail if the comparison loop ran zero comparisons.
- **Determinism / immutability.** AC11's two-regeneration comparison, plus a
  check that `specification_to_dict()` called twice returns equal but not
  identical objects (the module's own determinism contract).
- **Empty and degenerate reads.** Every parse (docstring section, transcript
  section, gate row) must fail loudly on "not found" rather than passing over an
  empty match — the failure mode this stage exists to remove.

**Existing tests to reconcile — swept 2026-09-04 on `aide/queue-020`; the sweep
found nothing that breaks, and the evidence is recorded here so the next author
does not re-derive it:**

- `tests/test_114_documentation_corrections.py::test_ac8_no_new_aide_check_warning_beyond_pinned_baseline`
  — **safe.** `_GATE_DECISION_WARNING_RES` excludes every
  `^progress\.md:\d+: human gate \d+ \(` warning from the pinned baseline, so a
  new gate row adds nothing the multiset can see.
- `tests/test_145_eight_hypothesised_modes.py::test_ac24_…` and
  `tests/test_146_ninth_mode_and_first_proposed.py::test_ac36_…` — **safe, and
  deliberately so.** Both classify warnings by *shape* rather than count, and
  both carry a comment naming this item: *"item 150 raising its sign-off gate
  would turn it red for an eighth warning that is the stage working as designed"*.
  Neither needs an edit.
- `tests/test_146_ninth_mode_and_first_proposed.py::test_ac35_module_docstring_records_the_change_with_resolvable_paths`
  — **safe if the docstring edit is additive.** It requires the literal
  `item 146`, a `2026-09-0\d` date and at least one resolvable
  `src/segfacet/…\.py` path to survive. Step 9 replaces only the `Sign-off`
  section's placeholder sentence; it must not touch the item-146 record.
- Every `test_14N_*.py` committed-artifact test — **safe unless step 7 changes a
  field.** If it does, the artifacts regenerate and those tests compare against
  the regenerated copies, which is the intended behaviour; a stale committed
  artifact is what they exist to catch.
- `tests/committed_artifact_guard.py` — both `failure_modes.generated.{md,json}`
  are already allowlisted under `no-float-leaf` (item 149). No new ground, no new
  allowlist entry.

## Validation

The human review **is** this item's validation, and it cannot be performed by the
validator agent. What the validator must do instead:

1. Run `python .aide/scripts/aide.py gate list` and confirm the Stage-30 sign-off
   row reads `✅ Approved (<date>)` with a non-empty evidence note. If it reads
   `⏳ Awaiting`, the item is **not** complete: hand back, do not resolve it.
2. Run `python .aide/scripts/aide.py check` and confirm no error and no warning
   naming this gate.
3. Regenerate by hand — `.venv/bin/python -m segfacet.failure_modes --json
   <tmp>/a.json --md <tmp>/a.md` — and diff against the committed pair; the diff
   must be empty.
4. Open `docs/aide/failure_modes.generated.md` and confirm the ten `## Mode N`
   sections are present and that each one the transcript marks `changed` shows
   the changed value.
5. Read the module's `Sign-off` section and confirm the date it names is not in
   the future and matches the gate row's date, or that the transcript explains a
   divergence.

No `[validation]` environment profile is needed: nothing here requires
PyRadiomics, Docker or a GPU. The one prerequisite is a person, and its absence
is not a downgrade to `❓ Unverified` — it is the gate, and the item waits.

## Dependencies

- **Item 144** — the specification module, its schema, `main()` and the two
  generated artifacts. Merged.
- **Item 145** — the eight hypothesised modes, discriminators and per-edge
  evidence rungs. Merged.
- **Item 146** — the ninth mode and the first `proposed` entry; also the
  `Sign-off` docstring section this item fills, and the `test_ac35` docstring pin
  it must not break. Merged.
- **Item 147** — the five partial sources collapsed onto the specification.
  Merged.
- **Item 148** — the per-path mode attribution the review reads. Merged.
- **Item 149** — the traceability matrix as conformance report; the second half
  of the review pack, and the reason the review surface is current. Merged.
- Human gate 3 (`§6 failure-mode taxonomy`, ✅ Approved 2026-09-03) — its
  decision text is what holds items 139–142 pending this sign-off. Quoted here
  with its reach intact: `Blocks: items 139, 140, 141, 142`.

**Downstream:** item 151 replays Stage 30's acceptance from a clean tree and is
the only item authorised to tick this stage's acceptance criteria, including the
sign-off criterion this item makes true. Stage 20's remainder (items 139–142) is
re-queued only after this item completes.

## Decisions & Trade-offs

**D1 — this item ticks no Stage-30 acceptance criterion, and its ACs carry no
`(closes Stage 30 criterion M)` annotation.** Stage 30 has, at this item's base,
**five** recorded instances of one error class: an item's AC positionally mapped
onto a stage acceptance criterion it does not close. Four are visible as
`retracted:` entries in `aide status` (Stage 20 criteria 1, 3, 4 and 5, retracted
2026-09-02); the fifth happened during item 149, when a validator ticked Stage-30
acceptance criteria 2 and 4 on **in-tree** evidence and both were reverted
(`4502119`, `5f94b2f` on `aide/queue-020`) because both are item 151's
deliverables and item 151's queue line requires a **clean-tree** replay. Item 150
does not repeat it. Its deliverable is the gate and the recorded sign-off,
nothing more; the stage acceptance replay — including criterion 6, *"the
specification's rendering is signed off by the maintainer, with the date and
outcome recorded in the module"* — is item 151's to attest, from a clean tree,
against this item's recorded result. Per `.aide/conventions.md` §1 → `items.md`,
**an AC that names no stage criterion closes none**, and the silence above is the
answer, not an omission.

**D2 — the sign-off lives in the module docstring, not in a module constant.**
A constant (`SIGN_OFF_DATE = "…"`) would be easier to parse but would create a
second source of truth about a fact the docstring already has to state for a
human reader, and the queue line names the docstring specifically. The precedent
settles it: Stage 19 recorded its steering review in a **comment** above
`feature_docs.STATUS_OVERRIDES`, with the full transcript in item 106's spec.
This item follows the same two-place shape — a short anchored record where the
code is read, the walkthrough where specs are read — and pays for it with an
anchored regex (AC5) rather than an attribute lookup. Cost: the record is
invisible under `python -OO` (**A5**).

**D3 — AC13 is a dated claim and says so.** "Items 139–142 are still ⏸️ at the
point the gate is raised" is, by construction, a premise about a sibling's
schedule, and `.aide/conventions.md` §1 → `items.md` is explicit that such a
premise is guaranteed to become false. Two options were weighed. A *conditional*
form ("⏸️ unless the gate is approved") is durable but goes vacuous the moment
this item completes — it would pass while the claim it stands for is false, the
exact defect class Stage 30 exists to remove. The *unconditional* form asserts
something real today and breaks honestly later, so it is the one adopted, with
the hand-off written into the AC itself: the item that first lands any of 139–142
lists `tests/test_150_maintainer_sign_off.py` under **May change**. A test that
fails loudly at a known, documented moment beats one that passes forever without
meaning anything.

**D4 — the three deferred insights are review *inputs*, not this item's work.**
Insights 35, 53 and 54 in `docs/aide/insights.md` each name item 150 as the point
of decision. Acting on them is not authorised here (they are code changes to
`derive_status`, to item 148's path classification, and to the corpus scan in
`catalogue.py`); *showing them to the maintainer* is, because a sign-off taken
without them is a sign-off over a catalogue with three known open questions. If
the maintainer decides one, the decision is recorded in the transcript and the
insight is ticked with a pointer by whichever later item implements it — not
here.

**D5 — no doubled-brace template slot anywhere in this spec.** `aide check`'s
`template_residue_errors` scans every `*.md` under `docs/aide/` and reports a
a bare doubled-brace slot marker as an **error**, which would fail AC4's `errors == []`. The
to-be-filled placeholders above are written as `<angle brackets>` for that
reason.

To be updated during implementation.

### Stage-30 maintainer sign-off

**Date:** 2026-09-14, continued 2026-09-15. **Outcome:** accepted with
changes — the maintainer read all ten entries of the item-149 rendering
(`docs/aide/failure_modes.generated.md` as committed at `a27d083`) with the
agent, one mode at a time, and re-organised the catalogue (applied in
`3cb522f`); on 2026-09-15 the maintainer revised that rendering once more,
splitting every paired sub-mode into single defects (ten entries became
sixteen). The disposition literal recorded in the module docstring is
`accepted with changes`.

**Facets reviewed per entry, and the `ModeSpec` / `IntendedRule` /
`CorpusCaseExpectation` field each resolves onto:** definition → `definition`;
discriminator → `discriminator`; expected firing → `expected_firing`; severity
→ `severity`; observability → `observability`; evidence rung →
`evidence_rung`; status → `status`; provenance → `provenance`.

**Cross-cutting decisions** (each a maintainer answer, recorded once here):

1. Ids are assigned in the specification and are stable from this sign-off on;
   `vision.md` §6 provides provenance, never ids (`VISION_SEED_DISPOSITION`).
   The tree runs generic to specific with one tier of sub-modes (`parent`), and
   a case that meets a parent's definition but no sub-mode's rule is classified
   at the parent. Integer ids plus a `parent` field were chosen over dotted
   string ids because every consumer (manifests, declarations, Stage-18
   metrics, eval ladders) is integer-typed.
2. Two observability classes are added: `needs-ground-truth` (modes 1 and 4)
   and `needs-external-classifier` (mode 7).
3. `validated` requires a declaring rule, every corpus case agreeing, and at
   least one case with a non-empty expected set that fires one of the mode's
   **own** intended rules. An empty expected set never validates (the vacuous-
   agreement half of insight 35 — decided here); a co-detection never validates.
4. The spline offset from the fitted curve is a spondylolisthesis / scoliosis
   classification signal with no clear failure mode, so `mislabel`'s Detector
   A serves no mode and its read paths are `bookkeeping` (this also settles
   insight 53's `dx_mm`/`dy_mm`/`dz_mm` question).
5. `bounds` and `reference_delta` are declared for every mode their
   volume/extent signal can proxy — modes 1, 2, 3 (and, per level, 5 for
   `reference_delta`) — each edge `needs-real-data`.
6. A partial vertebra at the image border is a **condition** of the case that
   gates other rules, not a failure mode; it is recorded as
   `CONDITIONS["fov_truncation"]`, the `border` rule is mode-less, and the crop
   fixture is the condition's.
7. Corpus case ids keep their historical `modeN_` prefixes as stable
   identifiers (43 test modules name them); the manifest's `failure_mode`
   field is the authority.
8. The Stage-18/29 eval harness stays on the pre-sign-off ids for one more
   queue (`eval.per_mode.LEGACY_STAGE18_MODE_NAMES`), documented as a known
   divergence — re-keying it needs re-measured ladder constants.
9. *(2026-09-15)* A sub-mode names one defect, never a pair of converse
   defects, so that every shipped detector serves at most one mode: fused /
   split, islands / holes, not segmented / hallucinated, and collapsed /
   duplicated each become two ids, and the implausible label sequence becomes
   three (out-of-order and skipped level label, both severity `fail`;
   unprompted numbering variant, `flagged-for-review`). A gap in the label
   sequence left by a vertebra that was not segmented is mode 6's, never
   mode 10's: mode 10 is only a skipped label on segmented vertebrae. The
   generic
   volume proxies `bounds` and `reference_delta` necessarily stay declared on
   several modes. Ids were re-assigned once more; the review had not closed,
   so the "stable from this sign-off on" rule of decision 1 starts at the
   revised ids.
10. *(2026-09-15)* Fused and split are defined by a substantial part of a
    vertebra under a neighbour's label; islands and holes by small same-label
    topology defects near the vertebra (rarely a larger distant blob, such as
    background or a device). A vertebra cut into large same-label pieces by a
    missing slab of its own body (`mode2_fragment`) is neither, so it and
    `fragmentation`'s `Fragmentation:` detector sit at the parent, mode 1. A
    duplicated label is the same label on non-adjacent vertebrae anywhere in
    the sequence; adjacent vertebrae sharing a label are a fusion.
11. *(2026-09-15)* `ModeSpec.scope` (and `ConditionSpec.scope`) records
    whether a finding is about one `vertebra` or about the labels along the
    `spine` (`failure_modes.SCOPES`); schema version 2.1.

**Out-of-scope observations** — each appended verbatim to `docs/aide/insights.md`
with provenance `item 150`, dated the day it was raised (the entries raised on
2026-09-14 name that pass's mode ids):

- knowledge — the per-label spline offset (`stage3.per_label_offsets[].offset_mm`) is an anatomy-classification signal (spondylolisthesis, scoliosis grading), not a failure signal: after the item-150 sign-off `mislabel`'s Detector A serves no failure mode, its read paths are classified `bookkeeping`, and the feature belongs in a clinical-descriptor group when Stage 27 re-taxonomises the feature schema
- gap — the Stage-18/29 eval harness (`segfacet.eval.per_mode`, `severity_ladder`, `per_mode_cohort`, their JSON schemas and the `test_099`-`test_102`/`test_109`/`test_125`/`test_135` pins) is still keyed by the pre-sign-off mode ids 1-8, frozen as `eval.per_mode.LEGACY_STAGE18_MODE_NAMES`; re-keying it to the signed-off catalogue needs re-measured ladder constants (`KNOWN_CROSS_MODE_COUPLINGS`, `RECORDED_MARGINS`), and the `displace` ladder then corresponds to no mode at all. One follow-up item, after the vision §6 re-issue
- gap — `docs/aide/vision.md` §6's numbered eight-item list no longer matches the catalogue (`segfacet.failure_modes.SPECIFICATION` now assigns the ids, in a one-tier hierarchy, with one seed title retired and one re-homed as a condition); §6 must be re-issued through `/aide-create-vision` as principles plus a pointer to the specification, never a numbered list, and until then `failure_modes.VISION_SEED_DISPOSITION` carries the seed-to-record provenance
- gap — three detectors the sign-off asked for that no shipped rule provides: a spacing-gap detector over `stage3.spacing_consistency.spacings_mm[]` for mode 4 (its fixture `remove_level_relabel` fires nothing today), an unprompted-transitional-label detector over `relationships.present_levels[]` plus a configuration flag for mode 6 (T13/L6 in a scan not configured for them), and a centroid-based collapsed/duplicated detector for mode 8 that needs per-component centroids the feature layer does not extract. Each is a rule item, not a specification edit
- gap — mode 2's lumbosacral transitional-anatomy sub-type (sacralised L5, lumbarised S1) wants an intervertebral-disc label channel -- disc labels lying inside the sacrum label are the hypothesised signal -- which `segfacet.labels.DEFAULT_LABEL_MAP` does not carry; needs a decision on a second label channel before any rule can read it
- knowledge — `synth.component_shape.FusePerturbation` fuses unbridged (the absorbed neighbour's voxels keep their gap), so `fuse_adjacent` is detected only by co-detections (fragmentation on two bodies under one label, coverage on the absorbed level); a bridged fuse operator that fills the inter-body gap is the honest fixture for mode 2's own bounds / reference_delta volume proxy, and would let mode 2 validate
- gap — per-detector attribution is now a live need, not a nicety: `mislabel` has one detector serving mode 6 and one serving no mode, and the only way item 148's per-path schema can say so is to classify Detector A's `offset_mm`/`dx_mm`/`dy_mm`/`dz_mm` as `bookkeeping`, so the catalogue renders a detector's firing signal under `rule_bookkeeping`. The rule-side detector ids insight 50 asks for would replace that workaround
- knowledge — the item-150 insight lines dated 2026-09-14 name mode ids of that day's catalogue, which the 2026-09-15 revision of the same review re-assigned: old 1 → 1, old 2 (fused or split) → 2 fused and 3 split, old 3 (islands) → 4, old 4 (not segmented) → 6, old 5 (mislabelling) → 8, old 6 (implausible sequence) → 9 out-of-order, 10 missing interior level and 11 unprompted variant, old 7 (shifted) → 12, old 8 (collapsed or duplicated) → 13 collapsed and 14 duplicated, old 9 (overlap) → 15, old 10 (tissue) → 16; new are 5 (holes) and 7 (hallucinated vertebra). `mode2_fragment` moved from old 3 to mode 1. Read those lines through this map
- gap — detectors and fixtures the 2026-09-15 split asked for that nothing provides: an enclosed-cavity count/volume or Euler-characteristic feature for mode 5 (holes), an above-expected-count check for mode 7 (hallucinated vertebra; `coverage`'s count check tests only a shortfall), and a split operator that reassigns part of one label to its neighbour so mode 3 (split vertebra segment) has a corpus case. Each is a feature, rule or corpus item, not a specification edit
- knowledge — mode 10 (missing interior level) sits under semantic mislabelling (mode 8) but, unlike its siblings, need not contain a mislabelling: a missed vertebra with correct labels leaves the same gap. The one-tier hierarchy has no label-sequence parent to hold it, so its discriminator records the exception; a top-level label-sequence mode is the alternative if more sequence modes without a mislabelling appear
- knowledge — superseding the entry above: the maintainer resolved it the same day by narrowing mode 10 to a skipped level label on segmented vertebrae (renamed *Skipped level label*, severity `fail`, `proposed`), so it always contains a mislabelling; a label gap left by a missed vertebra is mode 6's, which now carries `coverage`'s interior-gap detector and `mode5_remove_level`. What separates the two from the label map is the centroid spacing across the gap, which no rule reads; a skip-relabel fixture and a spacing-aware detector are owed to mode 10

**Entry-by-entry** (one line per `SPECIFICATION` key, under the ids of the
2026-09-15 revision; `changed` lines name the authored fields that moved
relative to the item-149 rendering):

- Mode 1 — changed: name, scope, definition, discriminator, observability, candidate_features, intended_rules, corpus_cases, mechanism. The seed entry "label not aligned with the vertebra it names" is **retired** (covered by semantic mislabelling; its signal is not a failure signal) and id 1 is re-used for the new catch-all *Segmentation accuracy (over-/under-segmentation)*: GT-relative, `needs-ground-truth`, sub-analysis (boundary-band thickness, local blob volume, spatial distribution) recorded as hypothesised features. `mode1_displace` stays as a co-detection by the mode-less offset detector; on 2026-09-15 `mode2_fragment` and `fragmentation`'s `Fragmentation:` detector moved here (a vertebra cut into large same-label pieces is neither a split nor an island), so the mode derives `validated`.
- Mode 2 — changed: name, scope, definition, discriminator, observability, candidate_features, intended_rules, corpus_cases, parent, mechanism. *Fused vertebra segments*, sub-mode of 1: one segment covers a substantial part of two or more adjacent vertebrae, with the sacralised-L5 sub-type. Observable via the over-range `bounds`/`reference_delta` proxies (to be proven). Fixture `fuse_adjacent` expects `{coverage, fragmentation}` — co-detections by modes 1's and 10's detectors, so the mode derives `implemented`.
- Mode 3 — changed: id, name, scope, definition, discriminator, candidate_features, intended_rules, corpus_cases, parent, mechanism. New entry *Split vertebra segment* (split from fused on 2026-09-15): a substantial part of one vertebra carries a neighbour's label, with the lumbarised-S1 sub-type; under-range `bounds`/`reference_delta` proxies, no corpus case yet; derives `implemented`.
- Mode 4 — changed: id, name, scope, definition, discriminator, candidate_features, corpus_cases, parent, mechanism. *Islands (disconnected components)* (was seed mode 3): typically small islands near the vertebra from image noise, rarely larger distant blobs (background, devices); island distance from the main body grades the finding. `mode3_inject_islands` and the `Rogue island(s):` detector; derives `validated`.
- Mode 5 — changed: id, name, scope, definition, discriminator, observability, candidate_features, status, parent, mechanism. New entry *Holes (enclosed background)* (2026-09-15): background enclosed inside a segment where the vertebra is bone, beyond the vertebral foramen; `proposed`, no rule and no extracted feature.
- Mode 6 — changed: id, name, scope, definition, discriminator, observability, candidate_features, intended_rules, corpus_cases, parent, mechanism. *Vertebra not segmented* (was seed mode 5), `needs-ground-truth`, sub-mode of 1, scope `spine`. Covers a missed vertebra whether the remaining labels are kept or renumbered: `coverage`'s interior-gap detector with `mode5_remove_level` (vertebra deleted, labels kept) drives it end-to-end, so the mode derives `validated`; the opt-in span/count checks stay `needs-real-data`, and `remove_level_relabel` (labels renumbered to stay continuous) is detected by no shipped rule — expected set empty, recorded as "not detected today".
- Mode 7 — changed: id, name, scope, definition, discriminator, observability, candidate_features, status, parent, mechanism. New entry *Hallucinated vertebra* (2026-09-15): a segment with its own vertebra label where no vertebra exists (rib, ilium, device, background), the converse of mode 6; `proposed`.
- Mode 8 — changed: id, scope, definition, discriminator, observability, candidate_features, intended_rules, corpus_cases, mechanism. *Semantic mislabelling* (was seed mode 4) covers any number of vertebrae and a still-valid sequence; single-channel-observable only through the per-level geometry proxy (`reference_delta`). The swap case and `mislabel`'s ordering detector are mode 9's, so this mode has no corpus case and derives `implemented`.
- Mode 9 — changed: id, name, scope, definition, discriminator, severity, intended_rules, corpus_cases, evidence_rung, parent, mechanism. *Out-of-order label sequence*, sub-mode of 8, severity `fail` (a label is certainly wrong): `sequence` and `mislabel`'s ordering detector, fixtures `mode4_relabel_swap` and `mode7_sequence_break`; the `sequence` edge stays `needs-real-data` for the fixture generator's single-relabel cap. Split from the implausible label sequence on 2026-09-15.
- Mode 10 — changed: id, name, scope, definition, discriminator, candidate_features, status, severity, parent, mechanism. New entry *Skipped level label* (split from the implausible label sequence on 2026-09-15): every vertebra segmented but the labels skip a level, so every label past the skip is wrong — severity `fail`. A missed vertebra is mode 6's, so `coverage`'s interior-gap detector (which cannot tell the two apart) and `mode5_remove_level` serve mode 6; this mode is `proposed`, awaiting a spacing-aware detector and a skip-relabel fixture.
- Mode 11 — changed: id, name, scope, definition, discriminator, candidate_features, status, parent, mechanism. New entry *Unprompted numbering variant* (split from the implausible label sequence on 2026-09-15): a transitional label such as T13 or L6 in canonical order in a scan not configured for it; `proposed`, flagged.
- Mode 12 — changed: id, name, scope, definition, discriminator, observability, candidate_features, status, parent, mechanism. New entry *Shifted label sequence*: every label offset by a constant, sequence internally valid, decidable only with an external vertebra classifier (spine section, rib attachment, C2/sacrum counting reference) — `needs-external-classifier`, `proposed`, sub-mode of 8.
- Mode 13 — changed: id, name, scope, definition, discriminator, candidate_features, parent, mechanism. *Collapsed labels* (split on 2026-09-15 from the seed-10 "collapsed or duplicated label set"): two or more labels' centroids closer than a fraction of the expected spacing (the "exact centroid" wording relaxed), with the item-129 silent-pass defect recorded; `proposed`.
- Mode 14 — changed: id, name, scope, definition, discriminator, candidate_features, parent, mechanism. *Duplicated label* (split on 2026-09-15 from the same seed-10 entry): one label on two or more non-adjacent vertebrae anywhere in the sequence, typically more than one spacing apart — adjacent vertebrae sharing a label are a fusion (mode 2); `proposed`, per-component centroids named as the missing feature.
- Mode 15 — changed: id, scope, discriminator. *Overlapping segments* (was seed mode 8): content confirmed as rendered; the id moved and the discriminator now spans modes 1-14.
- Mode 16 — changed: id, scope, short_name, discriminator. *Implausible tissue under a label* (was mode 9): content confirmed as rendered; the id moved, the manifest paraphrase is lower-cased to match its siblings, and the discriminator now spans modes 1-15.
- Condition fov_truncation — new: the seed mode 6 "partial vertebra at the image border" retired into `CONDITIONS`: a vertebra at the FOV edge touches an image face, its geometry and centroid are impacted to a varying degree, and many rules cannot be applied to it. `border` records it (mode-less, paths `condition-signal`); `mode6_crop_at_border` is its fixture, still measuring `{border, mislabel}`. Scope `vertebra`.

**Measured on 2026-09-15** (`segfacet.synth.regression.pipeline_findings` /
`reconstructed_findings` / `intensity_pipeline_findings` over the regenerated
manifests): every one of the 15 corpus cases agrees with its recorded expected
set; derived statuses are modes 1, 4, 6, 9, 15, 16 `validated`, modes 2, 3,
8 `implemented`, modes 5, 7, 10, 11, 12, 13, 14 `proposed`;
all four conformance checks (`specification_conflicts`,
`vision_seed_conflicts`, `rule_declaration_conflicts`,
`path_classification_conflicts`) return `()`.
