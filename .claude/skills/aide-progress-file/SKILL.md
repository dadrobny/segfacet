---
name: aide-progress-file
description: Load before writing progress.md — deliverable bullets and their item markers, and the attestation verbs that correct an acceptance box without editing it (conventions §1).
user-invocable: false
paths:
  - "**/progress.md"
---

# `progress.md`

`.aide/conventions.md` §1 → `progress.md` is the source of truth; this file is
how it reaches the two roles that move the file — `queue-planner`, which writes
the deliverable bullets item numbers are born on, and `validator`, which runs
the verbs over them. It is **delivery, not a second source of truth**. That
status lives in one place is on the floor, in `AGENT-CONTEXT.md`, already in
this context; the icon vocabulary is in `aide-document-format`.

**A stage section's work is a Deliverables block of flat bullets, each
`- <icon> <text>. *(Item NNN)*` — one status icon, one item ref, no nested
status-bearing sub-bullets.** The `*(Item NNN)*` suffix is what ties an item to
the bullet whose status it moves, so an item no bullet references is untracked.
**Suffix means suffix**: only the trailing marker that ends the bullet (its
last wrapped line) attributes; a bullet whose references all sit mid-prose
tracks nothing, and `aide check` warns about it. The marker forms, all read the
same way by every command:

| Form | Reads as |
|---|---|
| `*(Item 006)*` | 6 |
| `*(Items 006, 044)*` | 6, 44 — one deliverable, several items |
| `*(Items 089/090)*` | 89, 90 |
| `*(Items 071–075)*` | 71, 72, 73, 74, 75 — inclusive, hyphen or en-dash |
| `*(Items 006, 044–046)*` | 6, 44, 45, 46 — an element may be a range |

Prefer the explicit list when the items are not contiguous; a range is only
shorthand for one. **A marker naming several items is shorthand, never a shared
status cell** — write the shared marker freely; the file simply grows a row the
first time its items diverge. **A split copy's prose is reworded with its
verb, whatever its icon**: each copy carries the shared sentence until someone
says what each item delivers with `aide progress reword --item NNN`, never by
hand — over a ✅ bullet as readily as a 📋 one, since a deliverable bullet
carries no attestation. Follow-on deliverables enter through the queue, never
by retro-editing a closed stage's deliverable list.

**Prefer the verb to a hand edit**: `aide progress set`, `aide progress
accept`, `aide queue tidy`. Acceptance boxes are **ticked only by
`aide progress accept` — never derived**, and no rollup ever ticks one. **A
box is ticked only by a human — or by an agent acting on a check it actually
performed** — via `aide progress accept`, whose flags `aide progress -h`
states.

**Deferral is recorded on the item, with its reason, and the stage follows.**
Postpone an item with `aide progress set NNN deferred --reason …`, never by
typing ⏸️ over a bullet or a stage. A bullet no item marker names is deferred
by its place instead, with `aide progress set --stage N --deliverable K
deferred --reason …`, K counting the stage's deliverable bullets from 1.

**Deferred work resumes with its own verb, back to 📋, with its reason.**
Resume an item with `aide progress set NNN resumed --reason …`, and a bullet no
item marker names with `aide progress set --stage N --deliverable K resumed
--reason …`; a resumed item is claimable again. A forward `aide progress set`
refuses an item whose bullets are all ⏸️ or 📋. Resuming is the owner's decision, and the reason says why
the work is wanted now. A ⏸️ or ❌ bullet is never itemised as it stands: a ⏸️
one is resumed first, and a ❌ one was decided against, so it is not queued
until it is restored.

**A deliverable the stage turns out not to need is dropped, with its reason,
and the stage can close.** Drop a bullet no item marker names with `aide
progress set --stage N --deliverable K dropped --reason …`, never by typing ❌
over it: the bullet reads ❌, which counts toward its stage's ✅ where a ⏸️
bullet never does — a ⏸️ bullet included, once its owner decides the stage
does not need it at all. Defer what the stage needs later, drop what it does
not need. Drop an item with `aide progress set NNN dropped --reason …` — a
shipped item is reopened first. A drop that would leave every deliverable
bullet of the stage ❌ is refused: a stage with nothing left to deliver is
withdrawn whole, by a ❌ on its summary row and on any Objective row only it
delivers; a stage already withdrawn that way refuses no drop.

**Dropped work is restored with its own verb, back to 📋, with its reason.**
Restore an item with `aide progress set NNN restored --reason …`, and a bullet
no item marker names with `aide progress set --stage N --deliverable K
restored --reason …`. A forward `aide progress set`, and `aide merge`, refuse
an item whose bullets are all ❌ or 📋. Restoring is the owner's decision, and
the reason says why the work is wanted after all.

**A withdrawn stage speaks for no objective**: an Objective row reads ❌ only
when every stage it names is withdrawn, and is otherwise derived from the
stages still in scope.

**A stage may be ✅ with an unticked box; say why in an annotation beside it.**

**What a box may claim.** Stage status tracks exactly one thing — the planned
work shipped. **An Acceptance box is therefore an observable check of the built
thing** (the CLI runs, the artifact validates), something completing the
deliverables can guarantee. **A measured outcome the work aims for but cannot
guarantee by construction (an error-rate target, a benchmark result) must NOT
be an Acceptance box**: it belongs in the `## Outcome targets` table, one row
per goal, **its Target cell never empty and its Objective cell naming the
`G<n>` objectives it gates — one naming none gates none**. **A target never
blocks its stage** — the stage
closes when its work ships, and the target gates the Objective coverage rows
instead. **Marking a target `❌ Not met` is a *finding*, so route it like one:
capture a `gap` with `aide insights add` alongside the edit.** Write the
row with care: **a table row its reader cannot use is an `aide check`
error** — a `|` inside a cell, usually.

**Correcting an attestation has verbs too, so it is never a hand edit either.**
**The attestation is immutable; what is recorded about it is not** — the rule
`insights.md` already runs on. **Three verbs, and none of them edits the
original line**: `aide progress amend` appends a dated correction to a ticked
box, `retract` unticks one while keeping the original visible, and `reword`
fixes a criterion's wording. **`amend` appends, and only to a ticked
box** — the guard is structural, not advisory: **a verb that can only add
cannot be used to make an inconvenient attestation agree with a shipped
stage.** **`retract` unticks, and keeps the original attestation visible**;
**a retraction is a finding, so the verb routes it like one** into
`insights.md`. **`reword` is the one amendment that edits rather than
appends**, so it **refuses over a box that is ticked, annotated, or already
carries a correction trail**, and it **writes both documents or neither
wherever `roadmap.md` mirrors the stage** — **a stage with no Validation /
acceptance block in `roadmap.md` has no mirror to drift from**, so there it
writes `progress.md` alone.
