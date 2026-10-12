### The maintenance queue — insight-derived fixes, ahead of the stage queue

What a `defect`, `gap` or `automation` entry routed to "a candidate item"
(§1 → `insights-triage.md`) becomes, and who goes looking for it. It governs
the role that authors the next queue and nobody else: triage leaves such an
entry open precisely because the queue that would carry it does not exist yet.

**The open inbox is an input to queue authoring, not only an output of
triage.** An entry routed to "a candidate item" is routed to a queue that does
not exist yet, so the inbox is where such an entry waits, and whoever authors
the next queue reads it before choosing the batch:

```
python .aide/scripts/aide.py insights list --open
```

Every open `defect`, `gap` or `automation` entry is **considered, and either
queued or explicitly passed over — never silently dropped**. Queueing one is a
routing like any other, so the author who queued it ticks it with the item
number it became (`aide insights tick N --pointer "item NNN"`, which commits the
file when git can); a pass-over leaves the entry open and is stated where the queue
is reviewed, rather than left for the next reader to re-derive. **An unchecked
entry is still a candidate**, and the next queue's author sees it.

**That tick is the one record that an item is insight-derived** (the ledger's
`kind`, §1 → `ledger.md`), on the entry's line or on a dated trail line,
which is where `tick` writes it on an entry already ticked. **The pointer
opens with the item references** — `item NNN`, or several — and only those
count: a gloss may follow them, as in `item NNN (what it fixed)`, and a
number in it is never an item. Several are written `items NNN, MMM`,
`items NNN-MMM` or `item NNN and item MMM`; after a singular `item NNN` a
bare number is gloss. A pointer that opens with prose and only
mentions an item does not count: a decline's reason, or a decayed premise's
"fixed by item NNN", where the item fixed the entry without being queued as
it.

**Insight-derived fixes get a queue of their own, ahead of the stage queue.**
When open `defect`, `gap` or `automation` entries exist at a queue boundary they
are batched into a **maintenance queue, authored and merged before the stage
queue** — a normal queue in every respect: its own number, its own items, and it
ticks the entries it absorbs with the item numbers they became. It is not a
second live queue: which queue is live falls out of the numbering (§1 →
`queue-NNN.md`), so a maintenance queue numbered ahead of the stage queue is
served first, with no new state anywhere and nothing for a role to choose
between.

The queue's author still decides. An entry that does not warrant a queue of its
own — too small to be worth a branch, blocked on something unbuilt, out of scope
— is passed over with the reason stated, exactly as on a stage queue; and a
`gap` the upcoming stage was going to fill anyway belongs in the stage queue,
with that stage named as the reason. What is never allowed is silence.

**A pass-over may carry a proposal for the owner, never a decision.** An
entry passed over again and again is named with what the owner might do
instead: decline it, with its reason, or, for a `gap` that is scope not
ready to plan, move it to the roadmap's Backlog. Both are the owner's (§1 →
`insights-triage.md`); the queue's author makes neither, and the entry stays
open until the owner does. **An entry open across three or more queues is
already the owner's decision** (§1 → `insights-triage.md`): the author does
not pass it over again, and queues it once the owner says to. **Until the
owner has said, the author puts the decision to the owner where the queue is
reviewed** — queue it, decline it, or, for a `gap`, move it to the roadmap's
Backlog — with the one it would take and why. An author running with nobody
watching cannot learn the answer, so the queue's review is where the owner
gives it.

**A maintenance item's deliverable bullet goes under the maintenance stage**
(§1 → `roadmap.md`), **never under the feature stage whose module it
touches**: placing it there would reopen a closed stage. A `gap` routed to
the stage queue is not a maintenance item, and its bullet goes under that
stage as the stage queue's do.

**When a maintenance queue is warranted and the roadmap has no maintenance
stage, the queue's author hands back**, before writing either queue, as for
any answer that changes `roadmap.md`, and the owner adds the stage once, as
an amendment to `roadmap.md` (§1 → `roadmap.md`). Nothing else triggers it: a
boundary with no entry that warrants a maintenance queue writes its stage
queue as before, whether or not the roadmap has the stage.

**A maintenance batch rolls the maintenance stage up with its verb, after
wiring its bullets.** No verb runs when a bullet is added, so a ✅ stage
reopened by the new 📋 bullets still reads ✅ on its section header and its
Stage summary row, and `aide check` errors on both. Once the bullets are
under the stage, N being its number:

```
python .aide/scripts/aide.py progress rollup --stage N --no-commit
```

**Commit what it writes in the same commit as the bullets.** It writes the
rollup into both cells — the 🚧 a reopened ✅ stage now computes — and
nothing where they already read it (`aide progress -h`). No stage cell is
written by hand (§1 → `progress.md`).

#### Rationale

- **Why a maintenance queue, and not the stage batch.** A one-line fix that
  rides a ten-item stage waits for the whole stage to merge, and every other
  branch picks it up only after that. The split costs one more queue to carry
  and buys a small, fast, clean merge the rest of the work can build on.
- **Why the ordering, and not the checkpoint.** How a maintenance queue and
  its stage queue reach a human is the caller's business: the ordering falls
  out of the numbering alone, so it holds whether the two plans go up as one
  review or two — or as neither, in a project whose `git.mode` pushes nothing
  (§4). What the engine fixes is that the fixes are queued *ahead*, never the
  shape of the checkpoint around them.
- **Why a proposal, and not a decline.** Before issue #455 an entry the
  owner had decided against had no way out, and the queue's author passed it
  over at every boundary, re-deriving the same reason each time. A decline
  ends that, and is a scope decision; the queue's author is the role that
  sees the repeat, so it proposes, and the owner, reading the queue, decides.
- **Why a waited entry is not passed over again.** A proposal made with a
  pass-over can be passed over too, and "again and again" had no count, so
  nothing marked the boundary where proposing should stop (issue #456). The
  wait gives it one, and triage brings the entry to the owner there; a
  further pass-over by the queue's author would undo that. An unattended
  author has no owner to ask, and a line in a summary nobody is asked to
  answer is the silent pass-over again, so the decision goes where a person
  reviews the queue.
- **Why the maintenance stage, and not the stage the repair touches.** A
  repair is to work already shipped, so the stage whose module it touches is
  usually ✅, and a 📋 bullet under it reopens a stage whose acceptance was
  attested against the work as first delivered. One consumer did exactly
  that, filing a repair under an unrelated feature stage so as not to reopen
  its maintenance stage without a planned validation (issue #453); with no
  criteria on the maintenance stage (§1 → `roadmap.md`), reopening it plans
  nothing, so the incentive is gone.
- **Why a hand-back, and not a stage the planner adds.** The queue's author
  never edits `roadmap.md`, and the maintenance stage is authored once, so
  the hand-back is paid once per roadmap rather than once per batch — the
  cost that made a stage per batch the rejected alternative.
- **Why a verb, and not the icon by hand.** Issue #454 needed no engine
  change, so the batch wrote the computed 🚧 into the two cells itself: a
  bullet added under a ✅ stage is the one write no other verb rolls up. That
  made a rule every planner run had to keep, and a planner that missed it
  stalled on `aide check` — its own `check --queue` ran inside the window
  (issue #459). The verb writes the same value with nothing to work out, and
  running it always, rather than only over a ✅ stage, leaves nothing to
  judge either.
- **Why `--no-commit`.** The bullets and their rollup land in one commit, so
  no committed state has a ✅ over an open bullet; and a committing verb
  replays its commit onto the upstream, which the batch's other uncommitted
  edits would stop.
