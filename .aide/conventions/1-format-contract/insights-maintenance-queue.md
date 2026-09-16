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
