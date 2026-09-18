<!--
  AIDE work-item template. Step 5. One spec per item — what test-writer,
  builder and validator build against. It carries NO status field: status
  lives in progress.md. Sections, in order (who reads each in brackets):
    - Header: Created + pointer to progress.md, Stage, Queue, Objectives, branch
    - Description                     [builder, test-writer]
    - Acceptance Criteria             [test-writer, validator]
    - Assumptions                     [validator, at the queue boundary]
    - Implementation Steps            [builder]
    - Authorised paths                [builder, validator, aide scope]
    - Testing Strategy                [test-writer]
    - Dependencies                    [aide claim]
    - Decisions & Trade-offs          [spec-author: Left open; builder, as it goes]
  Optional: Validation (how to observe the work beyond the tests; the
  validator executes it when present), and Environment / Hardware
  Dependencies (only for an item introducing an environment-gated capability
  — conventions.md §1 → Environment-gated capabilities). What each section
  must hold is conventions.md §1 → items and §1 → Authorised paths; for the
  two optional ones, §1 → Environment-gated capabilities, which names both.

  Fill-in conventions: `{{slot}}` = literal value; _italic line_ = guidance to
  read then replace. Delete this comment in the generated file,
  and keep the aide-template line below it.
-->
<!-- aide-template: item 2 -->
# Item {{nnn}} — {{title}}

> **Created:** {{yyyy-mm-dd}} · status tracked in [`progress.md`](../progress.md)
> **Stage:** {{n}} — {{stage title}}
> **Queue:** [`../queue/queue-{{nnn}}.md`](../queue/queue-{{nnn}}.md) · Item {{nnn}}
> **Objectives:** {{g-codes this item advances}}
> **Suggested branch:** `aide/{{nnn}}-descriptive-name`

---

## Description

_Scope and deliverables, bounded to this one item — what it is and, briefly,
what it is NOT (to fence scope)._

## Acceptance Criteria

_Each criterion atomic, observable, and directly testable — one test per AC,
no guessing. Split any compound "and/or" criterion. Write a criterion only
where the deliverable, or a consumer in the batch, would fail without it;
conventions.md §1 → items says why, and where a deferred question goes
instead (the `Left open` note below)._

_A criterion about live state is worded as an equality its test can recompute
from the primary source — the shapes that fail that bar, and why, are
conventions.md §1 → items._

_An AC that closes one of this stage's acceptance criteria says so by
appending `*(closes Stage 20 criterion 3)*` to the criterion line. Most ACs
close none, and one without the annotation closes nothing; when the
annotation is earned is conventions.md §1 → items._

- [ ] **AC1: {{short name}}.** {{observable statement}}

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

_Under clarify mode `assume`, record each defensible default taken here (the
validator surfaces them for audit). A spec written before a dependency is
*implemented* pins that interface here as an assumption — at the level this
item reads it, through the producer's function or fixture where one exists
(conventions.md §5); the builder/validator hand back if reality diverged, and
the pin is re-checked at claim once the dependency has merged. Write "None."
if the item was fully specified._

_Name, in the bold label, the engine an assumption about **engine** behaviour
was true for: `- **A3 (engine 1.28.1):** ...`. A merged spec is a record: a
later re-check is appended to that marker, never written over the assumption
— conventions.md §1 → items states the form._

- {{assumption, and the interface/behaviour it pins}}

## Implementation Steps

_The intended code path in `source_dir` (see `aide.toml`). Ordered, specific,
and naming what it reuses: the existing helper a step calls rather than
re-implements, and that no dependency is added._

## Authorised paths

_The files this item may change, and the ones its tests pin without changing —
repo-relative, one per bullet, narrowest form that covers the work. Recognised:
an exact path, `dir/**` (whole subtree), `dir/*.ext` (one extension in one
directory). See conventions.md §1 — scope is proved by the diff against this
list, not by hashing another file's bytes._

**May change:**

- `{{path or glob}}` — {{why this item needs it}}

**Asserts against:**

_Paths this item's tests pin — read, never changed — including a derived
artifact recomputed live. Write "None." if the item pins nothing outside what
it changes. Two things never go here, an always-authorised path and the same
path listed again under May change; conventions.md §1 → Authorised paths says
why, where each belongs instead, and why pinning one file inside a May-change
glob is the carve-out rather than a double-listing._

- `{{path}}` — {{which AC pins it, and how}}

## Testing Strategy

_Name the test module. One test per AC is written without being asked for;
beyond that, list each adversarial case this item needs, as a label and the
failure mode it guards — `empty-input: the walker yields nothing rather than
raising`. The test-writer writes the AC tests and the cases listed here, and
no others (conventions.md §6), so a case with no failure mode behind it is
left out. A test of a producer's output reads that output through the
producer's code or fixture, never a hand-built copy._

## Validation  <!-- OPTIONAL: how to OBSERVE this working, beyond the tests -->

_Only when meaningful observation goes beyond the test suite: a command to
run, output to inspect, a dataset slice to process, a use case to replay. The
validator must EXECUTE this section, not just re-run the tests. If it needs an
environment the loop's machine may lack, name the `[validation]` profile
(checked via `python .aide/scripts/aide.py env --profile <name>`) and the
honest downgrade when absent (record `❓ Unverified`, never a silent pass).
Delete the section if the tests alone genuinely demonstrate the behaviour._

## Dependencies

_Other item numbers this relies on, and what each provides. A queue-mate
still 📋 is a legitimate entry — `aide claim` simply holds this item until it
lands — and declaring one is how an item that pins what a sibling produces
records that order: the cross-spec check reads the declaration and stops
reporting that sibling's authorised edit as a break of this item's pin.
Write "None." if there are none. `aide claim` reads this section to decide
whether the item is blocked, so every "Item NNN" mentioned here (in any of
the accepted forms — see conventions.md §1) is read as a blocker UNLESS it
appears after a literal `**Downstream` marker. If you want to note that a
*later* item depends on this one (a forward reference, not a blocker), put
it after that marker, e.g.:_

    **Downstream:** item 099 (stage validation) depends on this item's CI job.

_Item numbers before the marker are blockers; item numbers after it are not
— never write a forward reference before the marker, or it will incorrectly
block this item on something that hasn't happened yet. A quoted human-gate
reach is also safe when the `Blocks:` label keeps its markup: item numbers
after a backticked or bold `Blocks:` on the same line are not read as
blockers, so "waits on Gate 3 — `Blocks: items 119, 120, 121`" names the
gate's reach without creating three dependency edges. Keep the quote on one
line, and never let plain prose carry the word — unmarked "blocks:" excludes
nothing._

## Environment / Hardware Dependencies  <!-- OPTIONAL: delete if not applicable -->

_Only for an item introducing an environment-gated capability
(conventions.md §1 → Environment-gated capabilities). One row per
capability:_

- **{{package/tool name}}** — declared via {{pyproject optional-dependencies
  extra name, or "external tool (not a pip dependency)"}}. Required fallback:
  {{what happens when absent — must degrade gracefully, e.g. skip cleanly,
  never fail, never silently no-op as if the path were exercised}}.
  **Full-capability verification:** not yet exercised with the dependency
  present; tracked as `❓ Unverified` in `progress.md`'s Environment-Gated
  Capability Verification table until the gated path runs for real —
  conventions.md §1 → Environment-gated capabilities says what counts, and
  which item keeps the row.

## Decisions & Trade-offs

To be updated during implementation.

_A question this item deliberately did not settle is one `**Left open:**`
line here — the question and why it waits — so the next item finds it
deferred rather than forgotten (conventions.md §1 → items)._
