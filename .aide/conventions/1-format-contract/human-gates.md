### Human gates (optional, additive)

A **decision only a person can make**, blocking work until they make it. The
template's optional `## Human gates` section in `progress.md`, one row per
gate, four cells in this order:

```
| Gate | Blocks | Status | Decision / evidence |
|------|--------|--------|---------------------|
```

**A row of any other width is not read as a gate at all.** `aide check` fails
and names the row, and until it is fixed `aide claim` holds **every** item:
what the row blocks is unknown, so any item released could be one it was
written to hold.

Two of the cells have a fixed vocabulary:

- **Blocks** — item numbers (any §1 reference form, or bare: `106`,
  `110, 111`, `106–108`), `stage N`, or `all`.
- **Status** — table-local vocabulary, like Outcome targets': `⏳ Awaiting`,
  then `✅ Approved (date)` or `❌ Declined (date)`.

**Reach is per gate, and never a queue.** Blocking is tied to the units that
mean something:

| Blocks | Reaches | Use when |
|---|---|---|
| `106`, `110, 111`, `106–108` | exactly those items | the decision affects one thread; the queue keeps producing other work |
| `stage N` | every item that stage's deliverables reference, resolved live | the decision could *invalidate* a stage's work, so racing ahead is waste to throw away |
| `all` | every item, everywhere | a programme-level stop — sign-off, budget, legal |

`stage N` resolves through `progress.md` each time it is read, so a gate's reach
follows the roadmap as the stage's contents change rather than freezing a list
written when the gate was raised. The person raising the gate chooses the reach.

**Where a gate is raised, and where it lives.** Same split as Outcome targets:
raised wherever it is noticed, recorded in one place.

- **`roadmap.md`** — a stage whose work needs a decision or an out-of-band
  prerequisite says so in its own section. This is the usual home for a gate
  known at planning time, and it naturally implies `Blocks: stage N`.
- **`items/NNN-*.md`** — a gate discovered while specifying one item is noted
  in its Validation or Assumptions block, implying `Blocks: NNN`.
- **`progress.md`** — the **authoritative row**, always. It is the single source
  of truth for status and the only place the CLI reads, so a gate that exists
  only as prose in a roadmap or a spec blocks nothing.

**Any role may raise a gate; only a person may resolve one.** An agent noticing
that a decision is needed adds the row and says so. No agent may run `aide gate
approve`/`decline`.

**A declined gate keeps blocking.** It is resolved — someone decided — but the
decision was "no". The remedy is to re-plan: drop the blocked items, or change
what the gate asks. Only `✅ Approved` opens a gate; an unrecognised status
blocks too.

Semantics *(aide claim, check, status, gate)*:

- **`aide claim` will not offer a blocked item**, and names the gate as the
  reason.
- **`aide check` warns** on every gate still blocking — a normal state, not a
  defect.
- **Resolving is a CLI operation**, never a hand edit:
  ```
  aide gate (list | approve <n> | decline <n>) [--evidence "…"]
  ```

Agents *read* gates — to know why they must stop — and stop.

#### Rationale

- **Why not an acceptance box.** Those are observable checks *of the built
  thing* — something completing the deliverables can guarantee. A steering
  decision is not that, and overloading the checkboxes would repeat exactly the
  conflation Outcome targets were introduced to avoid. Gates get their own
  table for the same reason.
- **Why never a queue.** A queue is an *incidental* batch boundary — part of a
  stage, one stage, or several small ones — so "the live queue" names different
  work from one week to the next while the decision has not changed. And only
  the person who knows what the pending decision might change can judge which
  reach applies, which is why the table asks them.
- **Why raising is open and resolving is not.** Creating a blocker is safe —
  the worst case is work pausing for a human. Removing one is not: a gate
  exists precisely because the decision is not derivable from the work, so an
  agent resolving it destroys the only thing it was protecting. And releasing
  work behind a declined gate would run exactly what was refused. An
  unrecognised status blocks for the same reason: a typo in the mark must not
  silently open a gate. Nor may a typo in the shape: a row too mis-shaped to
  read holds everything, because the only unsafe guess at what it blocks is
  "nothing" — and until #202 that was the guess, with a warning that stopped
  nothing.
- **Why the shape is stated here and not left to the template.** A gate row is
  the one `progress.md` row a role adds by hand to a file another role wrote,
  often in a project whose optional section was deleted, so the author has no
  table above it to copy — and a mis-shaped one halts every item until someone
  repairs it. The header row costs a line; the mistake costs the programme.
  The error itself is one rule across the four `progress.md` tables a check
  gates on (§1 → `progress.md`).
- **Why `check` warns and `status` prints.** A gate that is still blocking is
  visible on every run instead of buried in a spec's prose; `aide status -h`
  names open gates among what it reports.
