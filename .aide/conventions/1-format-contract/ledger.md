### `ledger.md` (optional, additive — the run ledger)

Governs `docs/aide/ledger.md`, the record of *how* each item was worked: what
it cost in build↔validate rounds, and what it added. Two verbs write it —
`aide merge` and `aide ledger abandon` — and **no role reads it at spawn**: its
readers are the person standing at a queue boundary, who asks what the batch
cost, and the feedback-loop pass over a finished queue, which reads the
project's own ratios and their trend.

- **One row per item, appended where the ✅ is.** `aide merge` adds the row in
  the commit that ticks the item, so a row exists exactly for an item the
  engine landed; an item stopped at the validation-round cap never reaches a
  merge and takes its row from `aide ledger abandon` instead. One item, one
  row, whatever it took to get there — a re-dispatched builder, a second
  validator and a third round all land in the same row. An item `aide progress
  reopen` sends back is worked again, and its next merge appends a second
  row. *(aide merge, ledger abandon)*
- **The engine puts the file there, from `.aide/templates/ledger.md`.** The
  first row to be written creates the document as a byte-exact copy of that
  template; an existing file is only ever appended to, and `aide check` never
  creates one. *(aide merge, ledger abandon)*
- **The template draws the row.** Its header row fixes which columns exist and
  the order they are written in, and every row carries one cell per column;
  `aide check` reads the shape and reports — never fails — a row no reader can
  use. **A row written under `ledger template 2` stops at `Date`**, fourteen
  cells, and is still a whole row: every reader takes the columns after it as
  blank, so an old row needs no edit, and one padded with two empty cells
  reads the same. *(aide merge, ledger
  abandon, check)*
- **What the verb can derive, it derives; the round and finding counts are the
  caller's.** The item, its queue, its stage, its kind, how many acceptance
  criteria the spec carries, how many test functions and files the branch
  added against its recorded base, the engine version and the date are all
  read from the documents, the branch and `.aide/VERSION`. **A test the
  branch reconciled in another item's test file is that item's and is not
  counted** — exactly the tests `aide scope` reports as reconciled (§6); one
  there that traces to neither spec still counts. The number of
  build↔validate rounds and the counts of findings by rank are passed in by
  the role that held them: the orchestrator counted the rounds to enforce the
  cap and classified each finding as it triaged it, and neither number exists
  anywhere the engine can read. *(aide merge, ledger abandon)*
- **An absent or unmeasurable value is an empty cell, never a zero.** A count
  nobody passed, a criterion count no spec was found for, a diff no branch is
  left to take: each is blank, because a zero is a measurement and a blank is
  the absence of one. A count typed by an agent is a claim; recording nothing
  as `0` would turn an unrecorded run into a clean one. *(aide merge, ledger
  abandon, check)*
- **The three finding counts are in-scope findings only, and `-` says no
  review ran.** A finding outside the running item is carried by its
  `insights.md` line rather than by this row (§9), so it is never counted
  here. And where the writing verb runs under `loop.review = "off"` and the
  caller passed no counts, it writes `-` in the Blocking, Minor and Nit cells
  instead of leaving them empty — the engine reads that setting from
  `aide.toml`, so no caller supplies it — which leaves a blank in those three
  meaning one thing only: a count that should have been passed and was not.
  *(aide merge, ledger abandon, check)*
- **`Suite s` and `Inherited` are the merge's own test run.** `Suite s` is
  the post-merge run's wall time in whole seconds; `Inherited` is how many of
  that run's failures the gate admitted as failing on the base too (§4), `0`
  for a green run it could have compared. `Suite s` is blank where no run
  happened — `--no-test`, an abandoned item — and `Inherited` wherever no
  comparison was possible. **Where the merge took the run validation recorded
  instead of running the suite (§4), `Suite s` is that run's seconds followed
  by ` (reused)`** — `41 (reused)` — the one cell that may hold more than an
  integer or a blank. *(aide merge, ledger abandon, check)*
- **`outcome` is `merged` or `abandoned`** — how the item left the loop, which
  is the one thing a row cannot be read without: an item that cost three
  rounds and landed and one that cost three rounds and was dropped are
  opposite facts about the same counts. It is the writing verb's own answer,
  never a judgement. *(aide merge, ledger abandon, check)*
- **`kind` is `normal`, `maintenance` or `validate-stage`.** An item whose
  title opens `Validate stage N` is test-heavy by design, and an
  insight-derived fix (§1 → the maintenance queue) is small by design, so a
  reading of tests per criterion treats each by kind rather than pooling the
  three. The engine derives it, so the vocabulary is closed. *(aide merge,
  ledger abandon)*
- **Two rows appended at one tail are a union: keep both.** Every pair of
  branches that each landed an item conflicts here, exactly as the inbox does
  (§1 → `insights.md`), and the resolution is always the same — both rows
  stand, in either order. Nothing reads the rows as a sequence, so there is no
  ordering to restore and no row to drop; a row is a record of one item and no
  other row can say the same thing. *(aide check)*

#### Rationale

- **Why a row per item and not an event per verdict.** A validator FAIL, a
  re-dispatched builder and a triaged finding are all facts, and recording
  each as its own row was considered and dropped (2026-09-17): an item with
  two rounds and three findings becomes six rows, so the file grows per retry
  rather than per item and the reading a queue boundary wants — rounds per
  item, tests per criterion — has to be re-aggregated before it can be read.
  One row per item is also the one shape a verb that already runs once per
  item can write without any new bookkeeping.
- **Why a reopened item takes a second row.** The first row records a merge
  that happened, with what it cost, and a row is never edited; the reopen
  exists because that merge was not the end of the item (issue #271), so the
  second run is a second record rather than a correction of the first.
- **Why nothing about a run survived it.** Rounds lived in the orchestrator's
  session and died with it, `progress.md` records status and no history — one
  consumer's 69 items carry exactly one `-> in-progress` commit each, since a
  re-dispatched builder never re-sets a row that is already 🚧 — and review
  findings existed only in the reviewer's returned text. So the questions a
  human asks at a queue boundary had no answer: not because the facts were
  private, but because nothing wrote them down.
- **Why the counts are supplied rather than derived.** They are the two
  numbers the engine cannot see: the rounds are the orchestrator's own loop
  and the ranks are its judgement of what a reviewer returned. Passing them at
  the merge is the one moment both are still in hand and a verb is running
  anyway.
- **Why the suite's wall time is here.** Merge runs the suite itself, so it
  has the number; a row is committed, shared across machines and read at the
  queue boundary, where a timing history kept under `.git` would be invisible
  and never cleaned up. It is what sizes a validator's waits on the first
  suite run of a dispatch (issue #274). **Why the inherited count is.** A
  merge admitted over a red base is a different fact from a green one, and
  the row is the one place a queue's reader sees both without re-running
  anything (issue #275).
- **Why a reused run keeps its seconds and says so.** The time is still the
  suite's wall time over this item's tree, which is what a validator sizing
  its waits reads; a blank would claim no run gated the merge. The mark keeps
  a reader from taking the row for a second run, and it lives in the cell
  rather than a new column, so no row already written needs to change.
- **Why a fourteen-cell row still reads.** A row is never edited, so a
  reader that demanded sixteen cells would warn on every row written before
  2.7.0 for the life of the project. A missing trailing cell read as blank
  loses nothing, since those runs recorded no timing; padding one with empty
  cells changes no value, which is why it is allowed and never asked for.
- **Why a reconciled test is not counted.** Until 2.1.0 the Tests cell
  counted every test function new at the base, so an item that renamed a test
  in an earlier item's file, as its spec prescribed, was charged with a test
  that covers the earlier item's criterion — and tests per criterion, the
  reading the cell exists for, was inflated for exactly the items that
  reconcile. The cell and `aide scope` read one split, so the test a notice
  calls reconciled is the test the row leaves out.
- **Why `-` rather than a fourth reading of a blank.** With the marker
  absent, a project that never switched review on and a run whose reviewer's
  findings were dropped on the floor wrote the identical row — and they are
  the two rows a reader at a queue boundary most needs to tell apart, since
  one is a policy and the other is a defect in the run. The marker costs one
  character and is the engine's own answer rather than a fourth thing for a
  caller to type, because a caller that can type it can mistype it. A count
  passed anyway under review off is still written: a count is a claim someone
  made, and the engine does not overwrite a claim with its own reading of the
  configuration.
- **Why a blank and not a zero.** The ledger is read as a trend, so a run
  whose caller passed nothing must not read as a run that cost nothing: the
  two are opposite claims and averaging them together silently flatters every
  ratio drawn from the file.
- **Why the reviewer writes nothing here.** It returns findings and merges
  nothing (§9); the counts reach the file through the role that triaged them,
  which is the role that decided what each one was. A reviewer appending its
  own rows would record the same finding twice — once as it saw it, once as it
  was triaged — with no way to tell the two apart.
- **Why no role reads it at spawn.** Every row is about work that is already
  finished, so nothing an agent decides depends on it; putting it on any
  role's read-set would cost a growing file per spawn and change no decision.
