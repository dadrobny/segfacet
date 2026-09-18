---
name: aide-create-queue
description: Generate a prioritized queue of the next batch of work items.
---

# Create Queue

Generate the next batch of prioritized work items — Step 4 of the AIDE loop,
repeated whenever the current queue is exhausted. The batch is **scoped to one
cohesive roadmap unit (a single stage, or a small phase), capped at
`loop.queue_cap` items from `aide.toml` (default ~10), whichever is smaller.**

## Prerequisites

- `docs/aide/vision.md`, `docs/aide/roadmap.md`, and `docs/aide/progress.md`
  must exist.

## Instructions

Read vision, roadmap, and progress, then write the queue from the template
**`.aide/templates/queue.md`**.

### Read the open insight inbox first

**The open inbox is an input to queue authoring, not only an output of triage**
(`.aide/conventions.md` §1 → `insights-maintenance-queue.md`). Read it with the
verb, never by opening the file — the file interleaves closed and open entries:

```
python .aide/scripts/aide.py insights list --open
```

Triage runs *at* the queue boundary, when the finished queue is closed and the
next one is unwritten, so a `defect`, `gap` or `automation` entry routed there
to "a candidate item" has been waiting for this run. Every open one is
**considered, and either queued or explicitly passed over — never silently
dropped**: an entry you queue becomes an item like any other and is ticked with
the item number it became (below), and one you pass over stays open — still a
candidate for the next queue — and is named, with why, at the end of your turn.

**Triage routes each unchecked entry by its type, and this table is the whole
rule** (§1 → `insights-triage.md`, where it is written once so that this skill
and `/aide-review-insights` cannot hold different copies of it):

| Type | Where it goes | Who ticks the entry |
|---|---|---|
| `knowledge` | the owning document — the smallest edit that preserves the fact | the triaging role, on the fold |
| `defect` | a candidate item on the **maintenance queue** | the queue that absorbs it |
| `gap` | a candidate item — maintenance queue, or the stage queue when the stage was going to fill it anyway | the queue that absorbs it |
| `automation` | a candidate item adding the script/CLI verb **and** the prose that mandates it | the queue that absorbs it |
| `framework` | an issue on `[framework] repo` from `aide.toml`; unset or offline, it stays pending | the filing role, on the hand-over |

Only the three middle rows are yours: a `knowledge` or `framework` entry still
open here was not triaged, so route it through `/aide-review-insights` rather
than folding or filing it mid-batch.

### Emit a maintenance queue first when there are fixes to batch

**When open `defect`, `gap` or `automation` entries exist at a queue boundary
they are batched into a maintenance queue, authored and merged before the stage
queue** (§1 → `insights-maintenance-queue.md`) — so one create call writes
**two** queue files:

1. `queue-NNN.md`, the **maintenance queue**, from those entries only.
2. `queue-(NNN+1).md`, the **stage queue**, from the roadmap as usual.

The maintenance queue is a normal queue in every respect — its own number, its
own items, ticking the entries it absorbs with the item numbers they became —
and it is not a second live queue: **the live queue is the lowest-numbered open
one**, so the maintenance queue is served first and the stage queue starts when
it empties. How the pair reaches a human is the caller's, below: push and PR are
never this step's. Number the items sequentially across both,
maintenance queue first, and wire every one of them into `progress.md`
(requirement 8) exactly as for a single queue.

Write only the stage queue when there is nothing to batch: no open `defect`,
`gap` or `automation` entry, or none that warrants a queue of its own. That
second judgement is yours — too small to be worth a branch, blocked on something
unbuilt, out of scope — and it is stated, never silent. A `gap` the upcoming
stage was going to fill anyway belongs in the stage queue, with that stage named
as the reason.

### Requirements

1. **Scope to one cohesive roadmap unit, capped at ~`loop.queue_cap` items**:
   - If the next stage's remaining items fit within the cap, queue **exactly that
     stage** and **stop at the stage boundary — even if that yields fewer items**.
     Do not pad from the following stage: a stage-sized queue keeps scope cohesive
     and makes the queue the checkpoint where one stage's lessons inform the next.
   - A small **phase** whose stages together fit within the cap may be queued
     whole.
   - A stage needing more than the cap spans multiple queues.
   The cap is a **context budget, not a target**. Prioritise by roadmap order and
   unblocked dependencies.

   **"Run alongside" in a roadmap means independence, not concurrency.** One
   queue is live at a time, by design — the queue boundary is the human
   checkpoint. So a roadmap saying two stages "should run alongside" or "in
   parallel" is telling you they do **not** depend on each other's results, and
   may therefore be queued in either order or merged into one batch if they fit
   the cap. It is not asking for two live queues, and you cannot produce them.
   **Queue next, sequentially, and say nothing about it** — do not spend a
   paragraph explaining why you are not honouring an instruction that was never
   given. (Item-level independence *within* one queue is a different thing and
   works already: `aide claim` offers any unblocked item, so noting that two
   items may be picked up in any order is useful and correct.)
2. **No duplicates** — check existing `docs/aide/queue/queue-*.md` to avoid
   re-queuing completed or already-queued items.
3. **Sequential numbering** — item numbers are sequential across **all** queues;
   find the highest existing number and continue from it. Never restart.
4. **Testable, justified items** — each item must be testable locally, and
   each is queued for a reason the vision's posture row admits (§1 →
   vision.md; a vision carrying no posture line is read as `prototype`):
   under `prototype`, no preparatory or "for later" items: an item is queued
   only where a success criterion, a deliverable, or a justified sibling in
   the same queue needs it; under `durable`, foundations a later stage will
   use may be queued. A justified sibling is one the row admits, itself or
   through a sibling in turn, so a chain of dependencies of any length ends at
   a criterion, a deliverable or a foundation, never at an unjustified item.
   A candidate the row does
   not admit is not queued, and the pass-over is named in the summary
   (below), like an inbox entry passed over.
5. **A stage-closing queue ends with a stage-validation item** — when this
   queue completes a roadmap stage, its final item must be
   `Validate stage N: <stage title>`: replay the stage's use cases end-to-end
   (not just the unit suite), and flip any Environment-Gated Capability
   Verification rows the stage introduced to `✅ Verified` where the
   environment allows (`aide env --profile <name>`), else record in the row's
   Notes cell why it stays `❓ Unverified`. Validation is planned, numbered work — never an implicit
   hope.
6. **Consistent format** (parsed by `aide claim` / `aide check`):
   ```
   ### Item NNN: Short Title
   Brief description of the scope and deliverables for this item.
   ```
7. **No status field** — queue state (open/done) is **derived** from
   `progress.md` (a queue is open while any of its items is 📋/🚧), and
   `aide claim` picks the lowest-numbered open queue by default. Do not write a
   `> **Status:** Live` line; the only decorative status note is the completion
   stamp `aide queue tidy` adds to superseded queues.
8. **Wire every item into `progress.md`** — this is where item numbers are born,
   so it is also where they must be recorded in the progress tracker. For each
   `### Item NNN` you add, ensure the number appears as an `*(Item NNN)*`
   reference on the matching **deliverable bullet** under that item's roadmap
   **stage section** in `docs/aide/progress.md`:
   - Append to an existing reference when a deliverable maps to several items
     (`… *(Items 006, NNN)*`); add the reference to the bullet that has none; or,
     if the item delivers something not yet listed, add a new
     `- 📋 <deliverable>. *(Item NNN)*` bullet under the right stage. A shared
     marker is shorthand, not a shared status cell: the first status change to
     any of its items splits the bullet into one per item, so the siblings keep
     📋 rather than being completed alongside.
   - **Never change a deliverable's status icon** — leave it 📋. This step only
     makes the item *trackable*; status transitions (📋→🚧→✅) are
     `aide progress set`'s job during execution.
   - Why: `aide progress set NNN` finds the bullet to flip by its `*(Item NNN)*`
     reference. An item with no reference is untracked, and `progress set` now
     hard-errors on it (engine ≥ 1.0.1) rather than silently no-op'ing — so a
     future stage's deliverables, authored (step 3) before this queue assigned
     numbers, must be back-filled here.

### Tidy the previous queue first

Mark the superseded queue NNN-1 completed with the CLI:

```
python .aide/scripts/aide.py queue tidy <NNN-1>
```

Then, if any of its item lines still read 📋, reflect their final `progress.md`
state (✅ done, ⏸️/❌ if carried or dropped). Skip if this is the first queue.

### Output

Save to `docs/aide/queue/queue-NNN.md` (next sequential number) — and, when this
run split off a maintenance queue, `queue-(NNN+1).md` for the stage batch
alongside it.

### Commit the queues immediately (do not leave them untracked)

A queue is a shared project document; `aide claim` reads the committed file.
Commit the new queue (or both), the `progress.md` item-reference back-fill
(requirement 8), and the tidy-up on the current branch, each a separate Bash
call:

```
git add docs/aide/queue/queue-NNN.md docs/aide/queue/queue-<NNN-1>.md docs/aide/progress.md
git commit -m "docs(aide): add work queue NNN"
```

**Wrote two queues? Stage both**, in that one command —
`docs/aide/queue/queue-NNN.md` *and* `docs/aide/queue/queue-<NNN+1>.md` — and
commit them together, titled `docs(aide): add work queues NNN-<NNN+1>`. One
commit, not two: `progress.md` carries the item references for both queues and
cannot be split between them, so a first commit staging only the maintenance
queue would reference items no committed queue declares. The pair lands in one
PR anyway.

**Push/PR is the caller's job, not this step's:**

- **Run standalone (manual)** — also `git pull --rebase` then `git push`.
- **Invoked as the `queue-planner` subagent inside `/aide-run-roadmap`** — commit
  only; the orchestrator pushes the `aide/queue-NNN` branch and opens the
  human-reviewed queue PR. Say in your summary that you wrote two queues, so it
  knows there is a second batch behind the one it is about to open a PR for.

### Tick every inbox entry you queued

The verb owns that edit and commits the file when git can; `N` is the entry
number `insights list --open` printed:

```
python .aide/scripts/aide.py insights tick N --pointer "item NNN"
```

Never flip the checkbox or reword the line by hand: **the claim is immutable and
ticking the checkbox is the one in-place edit**. An entry passed over is left
exactly as it stands.

## Absorbed and passed-over entries

Close your turn by naming, in chat and in the queue-PR body if one is opened:

- the queues you wrote — the maintenance queue and the stage queue, or just the
  stage queue and why there was nothing to batch;
- the inbox entries each queue absorbed, with the item numbers they became;
- the ones you passed over, with why — **a pass-over leaves the entry open and
  is stated where the queue is reviewed**, rather than left for the next reader
  to re-derive. That is what makes leaving an entry unchecked an honest routing
  rather than a hope.
