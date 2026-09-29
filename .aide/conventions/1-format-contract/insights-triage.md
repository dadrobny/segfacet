### Insight triage — routing an entry, and judging it

How an entry captured in `insights.md` (§1 → `insights.md`) leaves the inbox.
It governs the pass that triages the backlog and the role that hands a
`framework` entry over — the insight-review pass, and whatever orchestrates it.
The routing table has a second reader: the queue's author, who queues what
triage left open and needs the same table to know which types are theirs
(§1 → `insights-maintenance-queue.md`). A role that only captures performs
none of this.

#### The routing table

**Triage routes each unchecked entry by its type, and this table is the whole
rule.**

| Type | Where it goes | Who ticks the entry |
|---|---|---|
| `knowledge` | the owning document — the smallest edit that preserves the fact | the triaging role, on the fold |
| `defect` | a candidate item on the **maintenance queue** | the queue that absorbs it |
| `gap` | a candidate item — maintenance queue, or the stage queue when the stage was going to fill it anyway | the queue that absorbs it |
| `automation` | a candidate item adding the script/CLI verb **and** the prose that mandates it | the queue that absorbs it |
| `framework` | an issue on `[framework] repo` from `aide.toml`; unset or offline, it stays pending | the filing role, on the hand-over |

**Routing a `defect`, `gap` or `automation` entry never ticks it.** Triage
stands *at* the queue boundary, so the queue that would carry such an entry does
not exist yet: leaving it unchecked **is** the routing, and the open inbox is
what carries it to whoever authors that queue. The exception is the entry triage
does **not** route — see *decayed premise* below, which closes one.

#### Triage judges the entry; the judgement is a trail line

Routing an entry as written is not the whole of triage. An entry may repeat one
already captured, its premise may have decayed, or it may be filed under a type
that does not fit what it describes. Three findings, one form — **a dated trail
line under the entry, never an edit to the claim**:

- **Duplicate** — the same claim as an earlier entry. Route the earlier one and
  point the later at it by its ID (`duplicate of insight <ID>`); both stay in
  the file.
- **Decayed premise** — what the entry names no longer exists, or has already
  been fixed by work done since. **A decayed premise is ticked, because there is
  nothing left for a queue to carry** — the trail line says what closed it, and
  the claim remains the record of what was true when it was captured. This is
  the one tick triage performs on a `defect`, `gap` or `automation` entry, and
  it is not a routing: nothing is being sent anywhere.
- **Wrong type** — the entry describes a defect and is filed as knowledge, or
  the reverse. Route it by what it *is* and say so in the trail; the type in the
  captured line is never rewritten.

**A ticked entry whose status is now stale gets a trail line too** — that is
triage as much as routing is.

#### Handing a `framework` entry over

**A `framework` issue body opens with the engine version the observation was
made under** — first line, before the observation:

```
**Project:** <`owner/repo` (consumer), or "a private consumer">. **Observed
under engine X.Y.Z** (insight <ID>).
```

Take the version from the entry; if the entry has none, read the consumer's
current `.aide/VERSION` and say in the body that it is *the version at triage
time, not at capture* — an unmarked fallback is worse than none, because it
reads as an observed fact. **Writing that header is the filing role's job; a
form on the destination cannot reach it.**

**The body carries what the framework can act on and nothing that identifies
the consumer.** The test is one sentence: the issue reads the same had any
other consumer raised it.

- **Name the consumer by the least triage needs** — a public repo as
  `owner/repo`, a private one as *a private consumer*: never its name, its
  organisation, its URL, or a path that contains any of them.
- **Speak in framework terms** — the verb, the lint, the `§N` section, the
  template, the installed paths (`.aide/…`, `docs/aide/…`); those are the same
  in every install.
- **Describe consumer-owned material by shape, never by copy** — source paths,
  module and item titles, domain vocabulary, people, branch names, hostnames,
  commit hashes.
- **Never abstract the evidence** — the verb's output, the error text, the
  document line that tripped a lint go in verbatim; a redacted error cannot be
  acted on. **The shape rule still applies inside the evidence, token by
  token**: the line's structure is what is verbatim, and each consumer-owned
  token in it is replaced by a placeholder that keeps its shape, so
  `docs/aide/queue-018.md:42: item title "Migrate billing-importer to
  Postgres" exceeds 80 chars` is filed as `docs/aide/queue-018.md:42: item
  title "<action> <module> to <store>" exceeds 80 chars`.
- **Prefer a fixture reproduction** — a minimal `docs/aide/*` shape of a few
  lines — over "run it on our repo", which the framework cannot do.
- **One observation per issue**; a second finding is a second issue.
- **Provenance is the insight entry's ID** (§1 → `insights.md`), not its
  position and not a URL into the consumer.
- **The title is framework-facing** — the verb or section, then the symptom;
  no consumer name.
- **A human confirms the hand-over and sees the composed body whole before it
  is filed.** That confirmation is the last point a leak can be caught, so it
  is the redaction check, and a summary of the body is not it.

**When triage happens depends on the destination.** `knowledge`, `defect`,
`gap` and `automation` all land in this project — a document it owns, or a
candidate item — so they wait for the queue boundary, where the insight-review
pass runs and whoever reviews the next queue sees its routing. `framework`
leaves for an issue on another repo, and nothing about that destination needs a
queue, so a `framework` entry may be triaged **on capture or on demand**.

#### Rationale

- **Why the routing table is written once, here.** Two roles read it — the pass
  that triages the inbox and the one that authors the next queue — and a rule
  each of them keeps its own copy of is a rule that has already drifted.
- **Why an unchecked entry is honest.** The next queue's author is bound to
  read the open inbox (§1 → `insights-maintenance-queue.md`), which is what
  makes leaving an entry unchecked at triage a routing rather than a hope.
- **Why the version leads a `framework` issue.** Triage at the destination
  begins by checking the claim against that engine's history: a report triaged
  against the wrong version is closed as already-fixed when it is not, or
  re-fixed when it is. The issue is triaged in a repo that cannot see this one,
  and "which engine was this?" is otherwise answered by hand, per issue. An
  issue template cannot supply it: a template binds a human composing in a
  browser and is silently bypassed when the body is composed by the role and
  passed on the command line (`gh issue create --body …`), which is how this
  handover files. The cost of writing it is nothing, because the consumer
  already holds the fact — in the entry's own marker, or one read of
  `.aide/VERSION` away.
- **Why the body carries no consumer identity.** The issue outlives the
  consumer and is triaged in a repo that cannot see it, so a name in the body
  has no reader who needs it — and the consumers that have run the loop so far
  are private repositories. A filing role holds the whole insight entry, the
  item spec and the working tree in context, and copies what it sees unless
  told which half is the framework's; before this rule the header shape itself
  asked for the repo's name. The redaction test is not `vision.md`'s test of
  whether a fix is the engine's — whether the next consumer, on a different
  codebase, hits the same thing — but it is what lets that test be applied
  from the issue alone: a body that reads the same from any consumer is one
  the framework can judge without knowing which consumer it came from.
- **Why the ID is the provenance.** An entry number was the provenance until
  issue #276: the consumer's next archive or merge renumbers it, so the issue
  pointed at a different claim, or none, by the time anyone followed it back.
  The ID is the same in the inbox and in the archive the entry later moves to.
- **Why the `(consumer)` label sits inside the public alternative.** It marks a
  named repository as a consumer of the framework; after "a private consumer"
  it only repeated the value, and a filing role fills the header literally
  (issue #283).
- **Why `framework` entries need not wait.** Routing them through the boundary
  too means the inbox accumulates for exactly as long as a queue runs, and a
  long queue is normal.
