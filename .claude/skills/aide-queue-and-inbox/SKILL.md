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

**One queue is live at a time, deliberately.** The loop builds one queue at
a time; an unmerged queue below the live one — built out, its PR awaiting
review, the live queue stacked on its branch (§4) — is a batch awaiting
review, not a second live queue. Item independence *within* a
queue is real — `aide claim` offers any unblocked item, so say it freely — and
so is stage independence, a scheduling fact that tells a planner two stages may
be queued in either order. Write it as independence, not as "run alongside":
the planner queues sequentially either way. Concurrent live queues — not
offered; `loop.claim_scope = "all-open"` widens *claiming* across every open
queue, but nothing creates a second live queue.

**A queue-end item is planned only when the engine reports a need for one**
(§1 → `queue-NNN.md`) — queue-level judgement that produces committed
artefacts, as the queue's final item. **Stage validation is its only trigger
today**: on a queue that closes a roadmap stage, `aide check --queue NNN`
warns when the stage still has work for one, and names why. **The planner
reads that warning and never works the need out itself** — with no such
warning, the queue ends with its last deliverable. **The same check warns on
a planned queue-end item with nothing to do.** **Wherever the file lists it,
it runs last**: `aide claim` holds it until the rest of its queue has left
the way, bar an item whose dependencies lead back to it, and `aide check
--queue NNN` warns when open work that does not depend on it is listed after
it, so an item added after planning goes above it. **The stage variant is
titled `Validate stage N: <stage title>`**; `/aide-create-queue` says when to run the
check and what to write.

**The file exists before a role needs it — the engine puts it there** (§1 →
`insights.md`): `aide check`, `aide claim`, `aide queue start`,
`aide insights list` and `aide insights add` each create a missing
`insights.md` from the template. No role copies the template by hand.

**Capture has a verb, and so does everything after it** (§1 →
`insights.md`): `aide insights add <type> '<one line>' --provenance queue-NNN`
captures an entry and prints its ID, `aide insights list --open` reads the
backlog without the
closed history around it, `aide insights tick N|ID --pointer "<where it landed>"`
closes an entry — **ticking the checkbox is the one in-place edit**, and the
verb owns it, so a hand-flipped `[x]` is the improvised form of `tick` — and
`aide insights archive --before <date> --yes` moves closed entries out (a dry
run without `--yes`); an archive renumbers what remains, so re-run `list`
after one. Reading the file raw costs the whole closed history to see a
working set of a dozen lines; editing it by hand is the failure `add` and
`tick` exist to prevent.

**Cite an entry by its ID, never by its position** (§1 → `insights.md`). The
queue file routing an entry into an item, and the item spec it charters, name
it as `insight <ID>` — the date-plus-hex handle `insights list` prints, computed
from the immutable claim, so no archive or merge moves it. `N` is for the
`tick` you run straight after `list`. **A longer ID is the same ID**: `list`
lengthens one only where two claims of one date would share it, and
`aide check` errors on a cited ID that names no entry, archives included.

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
