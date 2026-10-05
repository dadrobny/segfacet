### `queue-NNN.md`

Governs the queue file — the next batch of items, one file per queue under
`docs/aide/queue/`. `queue-planner` writes it, `aide claim` reads the live
one, `aide check` and `aide queue tidy` keep its declared status honest, and
`spec-author` expands its items.

- **Queue state is derived, not declared.** A queue is **open** iff any of its
  items is 📋/🚧 in `progress.md`, else **done**; the live queue is the
  lowest-numbered open one (`aide claim`'s default). A 📋 item every bullet of
  which sits in a withdrawn stage keeps no queue open, since `claim` never
  offers it (§2); a 🚧 one there still does. A `> **Status:**` line is
  optional decoration for human readers — `aide queue tidy` stamps a completion
  note on superseded queues, and `aide check` warns only when a declared status
  contradicts the derived state. *(aide check, claim, queue tidy)*
- **Work items as `### Item NNN: Short Title` + a description paragraph.** Item
  numbers are **globally sequential across all queues** — never restart. *(aide
  check, claim, spec-author)*
- **One queue is live at a time, deliberately.** The loop builds one queue
  at a time; the model offers no concurrency above the item level, and a
  roadmap cannot ask for it. An unmerged queue below the live one — built
  out, its PR awaiting review, the live queue stacked on its branch (§4) — is
  a batch awaiting review, not a second live queue. Three
  senses of "parallel" get confused here — the first two are real and useful,
  the third is the one the model does not offer:
  - **Item independence within a queue** — supported: `aide claim` offers any
    unblocked item, so items may be worked in any order. Say this freely.
  - **Stage independence** — a scheduling *fact* ("Stage 19 needs nothing from
    Stage 17"), which tells a planner the two may be queued in either order, or
    merged into one batch if they fit the cap. Write it as independence, not as
    "run alongside": the planner will queue sequentially either way.
  - **Concurrent live queues** — not offered. `loop.claim_scope = "all-open"`
    widens *claiming* across every open queue, but nothing creates a second live
    queue.

  *(aide claim, queue-planner)*
- **A queue-end item is planned only when the engine reports a need for
  one.** It is the one place for queue-level judgement that produces
  committed artefacts — a spec reviewable at the plan gate, tests that stay
  in the suite, an independent validator — and it is the queue's final item.
  Wherever the file lists it, it runs last: `aide claim` holds it until every
  other item on its queue that is not a queue-end item has left the way, bar
  one whose dependencies lead back to it and a 📋 one of a withdrawn stage,
  and `aide check --queue NNN` warns when open work that does not depend on
  it is listed after it, so an item added after planning goes above it. Stage validation is its only trigger
  today, so it is planned only on a queue that closes a roadmap stage, and
  only when `aide check --queue NNN` warns that the stage still has work for
  one. The planner reads that warning and never works the need out itself; with no such warning, the queue ends
  with its last deliverable. The same check warns on a planned queue-end item
  with nothing to do. What closes a stage, and what counts as a need, is
  `aide check -h`. The stage variant is titled `Validate stage N: <stage
  title>`: it attests the stage criteria no item's AC annotates, replays the
  stage's use cases end-to-end, and updates the capability table (§1 →
  environment-gated capabilities). *(aide check, claim, queue-planner,
  spec-author, aide merge)*

#### Rationale

- **Why one live queue.** The queue boundary is the human checkpoint — one
  review per batch — so the one-queue scope *is* the checkpoint boundary, and a
  second live queue would be a second batch built unreviewed beside the first.
  An unmerged queue below the live one does not break that: it is built, it
  waits for its own review, and it reaches `main_branch` only through that
  review. What stacking changes is when a batch is reviewed, never whether
  (#258, #302).
- **Why "independence" and not "alongside".** The softer phrasing changes
  nothing the planner does and only makes the roadmap and the queues appear to
  contradict each other.
- **Why the queue-end item is conditional.** Until 2.22.0 every queue closing
  a stage ended with a `Validate stage N` item, and it ran the full item
  pipeline every time — one consumer's cost 19 criteria, 11 tests and two
  rounds. Where every criterion is annotated by an item's AC, no capability
  row is open and nothing gated was introduced, it re-attests what the
  validators already attested; the progress rollup and the coverage and
  capability-table warnings are already mechanical (#333).
- **Why claim holds it rather than trusting the order.** An item added after
  planning was numbered and listed after `Validate stage N`, and neither had
  a spec: with no `## Dependencies` to read, the queue-end item counted as
  unblocked and was claimed first, validating a stage whose last deliverable
  had not been built. The title is the one thing the engine knows the item
  by, so the hold is read from it and from `progress.md` alone, never from a
  spec that may not exist yet; queue-end items do not hold each other, or a
  queue ending on two would start neither. The file is still made to say
  so, because a person reads the queue in its listed order (#347).
- **Why a withdrawn stage's 📋 item neither opens a queue nor holds its
  end.** 2.35.0 taught `claim` to skip it, but the open-state reading and
  the hold still counted it: a queue left with only such items stayed the
  live one and `claim` reported them held instead of moving on, and a
  queue-end item waited on an item nothing would ever offer, so an
  unattended run stalled (#389). A 🚧 one there still counts for both, on
  the line §2 draws for the stale ground: started work is live until its
  owner drops it.
- **Why the engine decides and not the planner.** The need is read from
  `progress.md`, the queue files and the specs, so the same tree always gives
  the same answer. At plan time no spec exists, so every unticked criterion is
  unannotated and a closing queue is told it needs the item; once the specs
  annotate the criteria, the mirror warning names the item as idle. The error
  runs toward planning validation that turns out unneeded, never toward
  skipping validation that was.
- **Why use cases are not read.** The issue named a roadmap stage declaring
  use cases or a validation block to replay as a third trigger, and nothing in
  the roadmap declares one: every stage's Validation / acceptance block is
  mandatory, and its bullets are the criteria already counted. Reading use
  cases would take a new roadmap block, which is a change to the document's
  shape, not to this check.
- **Why no queue-end item on a queue that closes no stage.** A maintenance
  queue, or a queue carrying part of a stage, has no trigger today, and a rule
  implying a general item nobody plans would be one nobody follows. CI
  findings that trace to no item go to a queue-end item where the queue has
  one and to a person where it has none (#332); they remain the candidate
  second trigger.
- **Why the title stays `Validate stage N`.** It is the one place the engine
  learns what an item is: the ledger's `validate-stage` kind and this check
  both read it, and consumers' existing specs and ledger rows keep parsing.
