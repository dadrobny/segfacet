---
name: aide-human-gates
description: Load before raising a human gate — the row in progress.md that blocks work until a person decides, its Blocks and Status vocabulary, and how far a gate reaches (conventions §1).
user-invocable: false
paths:
  - "**/progress.md"
  - "**/roadmap.md"
---

# Human gates

`.aide/conventions.md` §1 → human gates is the source of truth; this file is
how it reaches the two roles that raise one — `queue-planner` and
`spec-author`, preloaded at spawn, since adding the row is the one
`progress.md` edit either may make and a gate noticed and not recorded blocks
nothing. It is **delivery, not a second source of truth**. That any role may
raise a gate and only a person may resolve one is on the floor, in
`AGENT-CONTEXT.md`, already in this context.

**A human gate is a decision only a person can make, blocking work until they
make it** — one row in `progress.md`'s `## Human gates` table, **four cells in
this order** (**a row of any other width is not read as a gate at all** —
`aide check` fails, and **until it is fixed `aide claim` holds every item**,
since what the row blocks is unknown):

```
| Gate | Blocks | Status | Decision / evidence |
|------|--------|--------|---------------------|
| Golden-file retirement approved | 106 | ⏳ Awaiting | — |
```

**Blocks** — item numbers (any §1 reference form, or bare: `106`, `110, 111`,
`106–108`), `stage N`, `stage N+`, `stage N–M`, or `all`. **Status** —
`⏳ Awaiting`, then `✅ Approved (date)` or `❌ Declined (date)`. **Reach is per
gate, and never a queue**: exactly those items when the decision affects one
thread and the queue keeps producing other work; `stage N` when the decision
could *invalidate* a stage's work; `stage N+` for that stage and every one
numbered after it, a stage added later included — everything from a milestone
on, where `all` would also hold the stages before it; `stage N–M` for a bounded
run of stages; `all` for a programme-level stop. Every stage reach resolves
live through `progress.md`, and "after" is by stage number, never by position
in `progress.md`. The person raising the gate chooses the reach.

A gate known at planning time is stated in the `roadmap.md` stage and implies
`Blocks: stage N`; one discovered while specifying an item is noted in its
Validation or Assumptions block, implying `Blocks: NNN` — an evidence gate
excepted, below; `progress.md` holds the **authoritative row**, always — a gate that exists only as prose in a
roadmap or a spec blocks nothing. **A declined gate keeps blocking.** The
remedy is to re-plan: drop the blocked items, or change what the gate asks.
**A declined gate whose reach holds nothing open is re-planned** — its Blocks
cell names nothing (`—`), or only items and stages that are already ✅ or ❌.
The row stays as the record of the decision. `all` and `stage N+` reach work
not yet written, so a declined one is never re-planned this way. A stage not
yet written, or with nothing queued, is not spent.

**An evidence gate records a person's check of the built item, and blocks
nothing** — the gate an acceptance criterion names as its evidence, when no
loop-run test can measure it (§1 → items.md, delivered to `spec-author` in
`aide-item-specs`). Its Gate cell asks the by-hand question and its Blocks
cell is `—`. **It must not block its own item**: `aide claim` would never offer
the item, and nothing would be built to check. Its dependents wait anyway — a
dependency is met only once ✅, and `aide merge` refuses the item until the
gate is ✅ Approved. **The spec-author writes the row by hand** — no verb adds
one — beside the spec it writes, and cites the row's ID on the criterion; a
person checks the built item on its claim branch and decides there. **A
declined evidence gate is not re-planned while a live spec still cites it**: a
re-check is re-asked as a new Gate cell, so a new ID, and the annotation is
re-pointed at it.

**Cite a gate by its ID, never by its position** — the `gate-<hex>` that
`aide gate list` prints, in an item spec, a queue file, a roadmap stage or
another `progress.md` row; a merge renumbers the rows, and `aide check` errors
on a cited ID that names no gate. **The Gate cell is the gate's identity**:
the ID is a hash of it, so rewording it makes a different gate, and every
citation of the old one must be re-pointed.

**The plan gate is raised by `aide queue gate`**, as often as `[loop]
plan_review` says — over every queue, over a queue that opens a stage, or
never — so no role types a plan gate by hand: the verb writes the row and
prints its ID. A gate the roadmap declares applies whatever the setting says,
and is still yours to add.

Adding any other row is a hand edit because it has no verb. Everything after it does:
**resolving is a CLI operation, never a hand edit** (`aide gate` only lists,
approves and declines), and no agent runs it.
