### Insight triage — routing an entry, and judging it

How an entry captured in `insights.md` (§1 → `insights.md`) leaves the inbox.
It governs the pass that triages the open inbox and the role that hands a
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
| `gap` | a candidate item — maintenance queue, or the stage queue when the stage was going to fill it anyway; or the roadmap's Backlog, by the owner, when it is scope not ready to plan | the queue that absorbs it; the owner, ticked `→ roadmap Backlog` |
| `automation` | a candidate item adding the script/CLI verb **and** the prose that mandates it | the queue that absorbs it |
| `framework` | an issue on `[framework] repo` from `aide.toml`; unset or offline, it stays pending | the filing role, on the hand-over |

**Routing a `defect`, `gap` or `automation` entry never ticks it.** Triage
stands *at* the queue boundary, so the queue that would carry such an entry does
not exist yet: leaving it unchecked **is** the routing, and the open inbox is
what carries it to whoever authors that queue. The exceptions are not
triage's routings: the entry triage does **not** route — see *decayed premise*
below, which closes one — and the two closes only the owner makes, a decline
and a `gap` moved to the roadmap's Backlog.

**`defect` and `automation` entries never go to the Backlog.** A defect is a
fix to shipped work, and it stays open in the inbox until an item fixes it or
the owner declines it; an `automation` entry likewise stays open until an item
carries it or the owner declines it. The Backlog holds scope not yet ready to
plan (§1 → `roadmap.md`), so a `gap` that is such scope is the one entry it
takes. **The owner moves it there**, as an amendment to `roadmap.md`: the
bullet cites the entry as `insight <ID>`, and the entry is ticked with
`--pointer "roadmap Backlog"` in the same pass. A roadmap with no `# Backlog`
yet gets one in the same edit, in the roadmap template's shape.

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
  the one tick triage makes on its own judgement on a `defect`, `gap` or
  `automation` entry — a decline it applies is the owner's decision (below) —
  and it is not a routing: nothing is being sent anywhere.
- **Wrong type** — the entry describes a defect and is filed as knowledge, or
  the reverse. Route it by what it *is* and say so in the trail; the type in the
  captured line is never rewritten.

**A fourth judgement closes an entry without a queue: the owner's decline.**

- **Declined** — the owner decides a `defect`, `gap` or `automation` entry
  will not be pursued. It is ticked with `--pointer "declined: <reason>"`, and
  the claim stays the record of what was observed.
- **Only the owner declines.** The triage pass and the queue's author may
  propose a decline, with its reason, where a person reads it; neither makes
  one. A decline is a scope decision, and it is made at the queue boundary,
  where a person reviews what the next queue carries.

**A ticked entry whose status is now stale gets a trail line too** — that is
triage as much as routing is.

#### An entry that has waited is the owner's decision

**An entry's wait is the number of queues it has stayed open across.** `aide
insights list --open` prints it beside each open entry, and `aide status`
counts the entries that have reached three; how it is counted is `aide
insights -h`.

- **Triage brings each entry open across three or more queues to the owner
  as a decision, and does not pass it over again.** The decision is one of
  three: queue it; decline it; or, for a `gap`, move it to the roadmap's
  Backlog. Triage proposes the one it would take, with its reason, where a
  person reads; the owner makes it.
- **An entry the owner says to queue is queued by the next queue's author**,
  who then has no pass-over left to give it.
- **Three is a convention, not a setting.** No `aide.toml` key changes it.

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
- **Why a `defect` never goes to the Backlog.** One consumer ticked nine
  bullets out of the inbox into a `Carried defects` list in its roadmap. Six
  weeks later three had been fixed without the list recording it, one had
  been absorbed, and five were still open but invisible to
  `insights list --open`. A defect outside the inbox is lost to the one read
  the queue's author is bound to make; a decline is the honest way out of
  it.
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
- **Why an owner's decline.** Before issue #455 an open `defect`, `gap` or
  `automation` entry closed only through an item, a decayed premise or a
  hand-over, so an entry the owner had decided against stayed open for
  ever. In one consumer 62 entries were open, and 21 of them had been passed
  over in six or seven queues: the queue's author re-derived the same
  pass-overs at every boundary, and a real defect stopped being noticed among
  them. No verb was needed — `tick` takes any pointer.
- **Why only the owner declines.** Triage and the queue's author both judge
  an entry already (since 2.41.0 the triager judges and the caller writes),
  but not pursuing a reported defect is a decision about the project's
  scope, and the queue boundary is where a person reads. A role that
  declined by itself would make an unreviewed scope decision.
- **Why a wait, and a decision at three.** Each pass-over was recorded in a
  queue file and never on the entry, so in one consumer 21 gaps captured
  over two weeks sat through six or seven maintenance queues, and `insights
  list --open` showed a date but no measure of how many boundaries had gone
  by (issue #456). A decline and the Backlog (issue #455) gave the owner a
  way out; the count makes the moment to use it visible. Three is one
  boundary past "the next queue had no room": late enough to spare an entry
  the next queue will absorb, early enough to stop the seventh pass-over. It
  stays a convention until a consumer needs another number.
- **Why a count, and not a trail line per pass-over.** A line under each
  entry at each boundary is exact, but at sixty open entries it is sixty
  lines a boundary, written by hand or by a verb that has to know which
  entries a queue considered. The number of queues created since the
  capture is derivable from what already exists, needs no new state and no
  trail grammar.
- **Why a queue's `Created` line, and not its first commit.** The planner
  writes `**Created:**` from the queue template, so the date is in the file
  in every clone: shallow, in `local` mode, and with no git at all, and
  reading it costs no spawn. A first-commit date was the rejected
  alternative: it needs history (a shallow clone dates every old queue to the
  clone's tip), it moves under a rebase or squash, a queue being planned has
  none yet, and it is one `git log` per queue file on a platform where a
  spawn is slow. A queue file written without the line — one consumer's
  earliest queues were — counts when it is numbered after one that does,
  because numbering follows creation, and never otherwise.
- **Why a queue created on the capture day does not count.** Both dates are
  days, and an entry captured on the day a queue was created may have been
  captured after that queue was planned, so counting it would count a
  boundary the entry never waited at. Not counting it undercounts by at most
  one, and only on that day's queue.
- **Why no `aide check` warning on age.** A warning that only a decision can
  clear is noise to an unattended run, which cannot make the decision. The
  decision belongs at the boundary, where `status` and triage are read by a
  person.
- **Why `framework` entries need not wait.** Routing them through the boundary
  too means the inbox accumulates for exactly as long as a queue runs, and a
  long queue is normal.
