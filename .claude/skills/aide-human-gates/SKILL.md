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
Validation or Assumptions block, implying `Blocks: NNN`; `progress.md` holds
the **authoritative row**, always — a gate that exists only as prose in a
roadmap or a spec blocks nothing. **A declined gate keeps blocking.** The
remedy is to re-plan: drop the blocked items, or change what the gate asks.

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
