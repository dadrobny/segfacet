---
name: aide-queue-and-inbox
description: Load before authoring a queue — the queue file's derived state and item shape, and the insight inbox it is planned from: capture, the verbs, and how an open entry is routed (conventions §1).
user-invocable: false
paths:
  - "**/queue/*.md"
  - "**/insights.md"
---

# Queue files and the insight inbox

`.aide/conventions.md` §1 → `queue-NNN.md`, §1 → `insights.md` and §1 →
`insights-maintenance-queue.md` are the sources of truth; this file is how the
three reach `queue-planner`, preloaded at spawn, since a queue is planned from
the inbox and no shape here is one the role can look up mid-write. It is
**delivery, not a second source of truth**. The immutability of a captured
claim and the entry shape itself are on the floor, in `AGENT-CONTEXT.md`,
already in this context; routing an entry by type is triage's, §1 →
`insights-triage.md`, and `/aide-create-queue` carries the rows you queue
from.

**Queue state is derived, not declared.** A queue is **open** iff any of its
items is 📋/🚧 in `progress.md`, else **done**; the live queue is the
lowest-numbered open one. A `> **Status:**` line is optional decoration for
human readers — `aide queue tidy` stamps a completion note on superseded
queues, and `aide check` warns only when a declared status contradicts the
derived state. Never type the stamp by hand; run the verb.

**Work items as `### Item NNN: Short Title` + a description paragraph.** Item
numbers are **globally sequential across all queues** — never restart.

**One queue is live at a time, deliberately.** Item independence *within* a
queue is real — `aide claim` offers any unblocked item, so say it freely — and
so is stage independence, a scheduling fact that tells a planner two stages may
be queued in either order. Write it as independence, not as "run alongside":
the planner queues sequentially either way. Concurrent live queues — not
offered; `loop.claim_scope = "all-open"` widens *claiming* across every open
queue, but nothing creates a second live queue.

**The file exists before a role needs it — the engine puts it there** (§1 →
`insights.md`): `aide check`, `aide claim`, `aide queue start` and
`aide insights list` each create a missing `insights.md` from the template. No
role copies the template by hand.

**Capture is a plain append; everything after it has a verb** (§1 →
`insights.md`): `aide insights list --open` reads the backlog without the
closed history around it, `aide insights tick N --pointer "<where it landed>"`
closes an entry — **ticking the checkbox is the one in-place edit**, and the
verb owns it, so a hand-flipped `[x]` is the improvised form of `tick` — and
`aide insights archive --before <date> --yes` moves closed entries out (a dry
run without `--yes`); an archive renumbers what remains, so re-run `list`
after one. Reading the file raw costs the whole closed history to see a
working set of a dozen lines; editing it by hand is the failure `tick` exists
to prevent.

The fourth verb covers the one moment the whole file is in front of something
willing to rewrite it. Append-only means two branches that each captured an
insight conflict on every merge, and `aide insights resolve [--dry-run]`
writes the union of a conflicted inbox — shared history, then each side's new
entries, ticks and trails merged — instead of a hand retyping the block. **It
refuses anything that is not a pure append** (a reworded, reordered or deleted
claim, or a side that archived) and writes nothing when it does, because each
of those is a change to an immutable line that a human must see. Do not
resolve this file's conflict by hand: a conflict marker left in the file is an
`aide check` **error**, not a warning, and the message names this verb.

**The open inbox is an input to queue authoring, not only an output of triage**
(§1 → `insights-maintenance-queue.md`). Triage happens *at* the queue boundary,
when the next queue does not exist yet, so a `defect`, `gap` or `automation`
entry routed there to "a candidate item" waits in the inbox for whoever authors
that queue: `aide insights list --open` is one of its inputs, beside vision,
roadmap and progress. Every open entry of those three types is **considered,
and either queued or explicitly passed over — never silently dropped**; a
queued one is ticked with the item number it became, and a passed-over one
stays open, because **an unchecked entry is still a candidate**.

**Insight-derived fixes get a queue of their own, ahead of the stage queue**
(§1 → `insights-maintenance-queue.md`). When those open entries warrant it they
are batched into **a maintenance queue, authored and merged before the stage
queue** — its own number, its own items, ticking what it absorbs — and the
stage queue is the next number up. It is not a second live queue: the live
queue is the lowest-numbered open one, so the fixes are simply served first.
Whether an entry warrants one is yours to decide and never silent: too small
to be worth a branch, blocked on something unbuilt, out of scope, or a `gap`
the upcoming stage was going to fill anyway — say which, where the queue is
reviewed.
