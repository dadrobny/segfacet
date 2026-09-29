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
  `110, 111`, `106–108`), `stage N`, `stage N+`, `stage N–M`, or `all`.
- **Status** — table-local vocabulary, like Outcome targets': `⏳ Awaiting`,
  then `✅ Approved (date)` or `❌ Declined (date)`.

**Reach is per gate, and never a queue.** Blocking is tied to the units that
mean something:

| Blocks | Reaches | Use when |
|---|---|---|
| `106`, `110, 111`, `106–108` | exactly those items | the decision affects one thread; the queue keeps producing other work |
| `stage N` | every item that stage's deliverables reference, resolved live | the decision could *invalidate* a stage's work, so racing ahead is waste to throw away |
| `stage N+` | the same over stage N and every stage numbered after it, including a stage added later | the decision gates everything from a milestone on; `all` would also hold the stages before it |
| `stage N–M` | the same over every stage numbered N to M | the decision affects a bounded run of stages |
| `all` | every item, everywhere | a programme-level stop — sign-off, budget, legal |

A stage reach resolves through `progress.md` each time it is read, so a gate's
reach follows the roadmap as the stages' contents change rather than freezing a
list written when the gate was raised. The person raising the gate chooses the
reach.

- **"After" is by stage number**, never by position in `progress.md`: the
  number is a stage's identity, so a renumbered stage is a different stage.
- **The range forms are written loosely.** `stage` or `stages`, any case, an
  en dash or a hyphen, spaces around the dash or not: `stage 6+`,
  `stages 6-8`, `stage 6 – 8`. `stage N–N` is `stage N`.
- **A stage reach holding nothing is armed or a mistake, and `aide check`
  says which.** Armed: a `stage N+` whose stages hold no item yet, or do not
  exist yet — the form exists to cover stages not yet written — and a
  `stage N–M` or `stage N` whose stages exist with nothing queued. A mistake,
  holding nothing ever: a `stage N` or `stage N–M` naming no stage that exists,
  and a range whose first stage is after its last (`stage 8–6`).

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

**Three things stop the loop for a person, and only one is a row.**

- **A gate row is serial by nature, over its reach.** What it blocks waits for
  the decision; everything else keeps flowing.
- **A framework or process edit is serial by nature, and is not a row.** It
  cascades into every later queue, so it stops the run for a reviewed PR
  (`README.md` → Merge policy).
- **The queue-end merge is serial only up to the cap, and is never a gate
  row.** Every queue's PR is reviewed before it reaches `main_branch`;
  `[loop] max_open_queues` says how many may await that review while the loop
  builds the next queue on top of them (§4).

**The plan gate is raised by `aide queue gate`, as often as `[loop]
plan_review` says.** It holds a newly planned queue's items until a person
has reviewed the plan: `"queue"` (the default) raises one over every queue,
`"stage"` one `stage N` gate when a queue opens stage N, and `"none"` none,
leaving the plan to be reviewed in the queue's PR with the code. The verb
writes the row and prints its ID; no role types a plan gate by hand. A gate
the roadmap declares applies whatever the setting says. `aide queue -h`
states which rows the verb writes.

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
  aide gate (list | approve <n|ID> | decline <n|ID>) [--evidence "…"]
  ```

Agents *read* gates — to know why they must stop — and stop.

**Cite a gate by its ID, never by its position.** Every gate has an ID —
`gate-` and the leading hex of a hash of its Gate cell, as in `gate-3fa1` —
which `aide gate list` prints and no one writes: the row keeps its four cells.
The ID is computed from the Gate cell alone, so approving, declining,
re-planning what it blocks and a merge that renumbers the rows all leave it
where it was. Wherever a durable artifact names a gate — an item spec, a queue
file, a roadmap stage, another `progress.md` row — write its ID. A position
(`gate list`'s `n`) is for the session that just ran `list`, and nowhere else.

- **The Gate cell is the gate's identity.** Rewording it — including to
  "change what the gate asks" after a decline — makes a different gate with a
  different ID, and every citation of the old one stops resolving. Re-point
  each at the new ID, or drop it.
- **A longer ID is the same ID.** `list` prints four hex digits, and more only
  where two different Gate cells would share them; any longer prefix of the
  same hash names the same gate. Two rows asking the same question share an
  ID, and a verb takes a position for them.
- **`aide check` holds citations to the table.** Over `docs_dir`, the inbox
  and its archives excepted: a cited gate ID that names no row is an
  **error** — it blocks a merge, like every check error. A cited ID matching
  two different Gate cells, and a citation by position (`gate 3`, `human gate
  #3`) while the `## Human gates` table has a row, are warnings naming the
  ID to write. A record is not read for positions, and a zero-padded number
  is an item number, never a position, as for insights (§1 → insights.md).

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
- **Why `stage N+` and `stage N–M`.** A milestone decision — hold everything
  from stage 6 on — took one `stage N` row per stage, and a stage added to the
  roadmap later was not covered, which defeats a reach that resolves live;
  `all` over-reached into the stages before the milestone (#304). The closed
  range ships beside it for a decision about a bounded run. "After" by stage
  number, not document order, because the number is what every engine read
  of a stage keys on; a stage moved in the file is the same stage. A reversed
  range is reported rather than swapped: guessing which end the author meant
  is a guess at what the gate holds, the one guess a gate must not make.
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
- **Why the queue-end merge is never a gate row.** A row blocks items, and a
  built-out queue has none left to block. What its review bounds is rework:
  a queue built on one a person has not accepted is wasted if that one is
  rejected, and `max_open_queues` caps the waste at `max_open_queues − 1`
  queues. A row would instead block the next queue's items, which is the
  one thing the cap exists to allow (#258). Relaxing *when* a batch is
  reviewed is in scope; no batch reaches `main_branch` unreviewed.
- **Why the plan gate has a verb.** From #300 the planner typed the row
  from a paragraph, which left the choice `plan_review` now makes — which
  gate, if any — to an agent's reading of prose, and a row typed by hand is
  one a mis-shape turns into a hold on every item. The verb makes the choice
  from the documents and writes the shape (#302).
- **Why an approved plan gate stays in the table.** The row is the record
  that the plan was reviewed, and when; nothing folds it away after its
  queue merges. At `"queue"` that is a row per queue — about one per ten
  items — which `aide check` does not warn on; `"stage"` and `"none"`
  raise fewer, and are the setting for a project that finds the table long.
- **Why the shape is stated here and not left to the template.** A gate row is
  the one `progress.md` row a role adds by hand to a file another role wrote,
  often in a project whose optional section was deleted, so the author has no
  table above it to copy — and a mis-shaped one halts every item until someone
  repairs it. The header row costs a line; the mistake costs the programme.
  The error itself is one rule across the four `progress.md` tables a check
  gates on (§1 → `progress.md`).
- **Why an ID, and why over the Gate cell alone.** A position was the only
  handle a durable artifact had, and it moves: a long-lived queue branch took
  `main` in, the merge renumbered a gate, and items went on citing it under
  its new number with nothing to check that the number still named the gate
  meant (aide-loop #276's second incident; #293). The inbox's fix carried over
  with one change. An insight's claim is immutable, so the whole claim is
  hashed; a gate row is not — Status and evidence are what `approve` and
  `decline` write, and Blocks is re-planned while the question stands — so
  only the question is hashed. An explicit slug cell was rejected: a fifth
  cell is a row of the wrong width in every existing table, which holds every
  item. "Never cite by number" alone was rejected: a quoted question has no
  resolvability check, which is the gap that let the renumbering pass.
- **Why a reworded Gate cell is a new gate.** Its citations cited the
  question it asked, and that question is no longer asked; a check that kept
  them resolving would let an item go on waiting for — or be released by — a
  decision about something else.
- **Why the check reads `docs_dir` only.** Gates are cited by the documents
  that plan work. `gate-` and hex is ordinary vocabulary in a test suite,
  where an error would block a merge over a word that was never a citation.
- **Why `check` warns and `status` prints.** A gate that is still blocking is
  visible on every run instead of buried in a spec's prose; `aide status -h`
  names open gates among what it reports.
