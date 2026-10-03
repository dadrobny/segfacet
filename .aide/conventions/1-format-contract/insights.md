### `insights.md` (optional, additive — the compound-engineering inbox)

Where out-of-scope learning goes so it is never lost *and* never acted on out
of scope. Every role captures into this file, so every role reads this section;
what happens to an entry *after* capture is two sections of its own, named at
the end. Any role, at any time, captures **one line** with `aide insights add`
and returns to its task:

```
python .aide/scripts/aide.py insights add <type> '<one line>' [--provenance 'item NNN']
```

which appends

```
- [ ] <type> — <one line> *(item NNN, YYYY-MM-DD, engine X.Y.Z)*
```

with `<type>` one of **knowledge** (document it), **defect** (fix it), **gap**
(plan it), **automation** (a recurring manual/agent action deterministic code
could replace — script it), **framework** (belongs to AIDE itself). One
entry is in scope by design: a review finding ranked *minor* (§9) that the
triaging role chose to defer rather than fix on the branch, filed as a
`defect` naming the item — it routes like any other `defect`, and it is the
only line here that a role could have acted on in place. A line that records
a review finding, in scope or out of it, opens its free text with the
finding's rank (§9) — a word inside the one line, not a change to the entry's
shape, and nothing parses it.

**The file exists before a role needs it — the engine puts it there.**
`aide check`, `aide claim`, `aide queue start`, `aide insights list` and
`aide insights add` each create a missing `insights.md` as a byte-exact copy of
`.aide/templates/insights.md`. No role copies the template by hand, and an
existing file — malformed or not — is never touched.

**Name where it came from, in whatever form is honest.** The provenance before
the date — `--provenance` — is free-form and optional: write `item NNN` from
inside an item, `queue-NNN` for planning or spec-authoring done before any item
exists, `items NNN-NNN` for a finding that genuinely spans several, or omit it
entirely from a role outside the loop. Those are the conventional spellings, not a
grammar the CLI enforces: **the ISO date is the only part that is
load-bearing**, since `archive` cuts on it. Never bend a provenance to fit a
shape — collapsing `items 099-101` to `item 099` is a rewording the immutability
rule below forbids.

**Name the engine you were running, after the date** — `engine X.Y.Z`, one read
of `.aide/VERSION`. `add` fills in both the date and this; the engine is
optional and unenforced like the provenance — and **never retrofitted**, since
the claim line below is immutable: an entry captured without one stays as
captured.

`aide check` shape-checks entries, and only the date strictly.

**Capture has a verb, and so does everything after it.** `add` refuses,
writing nothing, an input whose line would not read back as the entry given. A line of the same shape appended by hand is still an entry —
`check`, `list` and the ID read the line, not how it got there — but it is the
improvised form of `add`, as a hand-flipped `[x]` is of `tick`.

```
python .aide/scripts/aide.py insights add <type> '<one line>' [--provenance TEXT]
python .aide/scripts/aide.py insights list [N|ID] [--open] [--type T] [--trail]
python .aide/scripts/aide.py insights tick N|ID --pointer "<where it landed>" [--trail]
python .aide/scripts/aide.py insights archive --before YYYY-MM-DD [--yes]
python .aide/scripts/aide.py insights resolve [--dry-run]
```

`aide insights -h` states what each verb does. Two consequences an author
acts on: `tick` performs the one in-place edit below, and an archive renumbers
what remains, so re-run `list` after one.

**Cite an entry by its ID, never by its position.** Every entry has an ID —
its capture date and the leading hex of a hash of its claim, as in
`2026-09-24-3fa1` — which `insights add` and `insights list` print and no one
writes: capture stays one line. The ID is computed from the claim alone, which
is immutable, so no tick, trail line, archive or merge changes it, and it names
an archived entry as well as a live one. Wherever a durable artifact names an entry — an
item spec, a queue file, `progress.md`, a trail line, a test, a commit message,
another entry's claim — write `insight <ID>`; the word before it is what
`aide check` reads a citation by. A position (`list`'s `N`) is for the session
that just ran `list`, and nowhere else.

- **A longer ID is the same ID.** `list` prints four hex digits, and more only
  where two different claims of one date would share them; any longer prefix
  of the same hash names the same entry, so an ID once written keeps
  resolving. Two captures of the *same* claim on one date share an ID, and
  `tick` takes a position for them.
- **`aide check` holds citations to the inbox.** A cited ID that names no
  entry in `insights.md` or its archives is an **error** — it blocks a merge,
  like every check error. A cited ID matching two different claims, and a
  citation by position in `docs/aide/**` or `tests_dir`, are warnings naming
  the ID to write — for a position, the entry it named in the commit that last
  wrote the citing line, read from git history, and today's only for a line
  not yet committed or where there is no history (the warning says which).
  The inbox and its archives are not swept, and a **record**
  is not read for positions: the spec of an item `progress.md` shows ✅, ❌ or
  ⏸️, and a queue naming items none of which is still open. An ID in a record
  that resolves to nothing is still an error. A position is never
  zero-padded — `037` is an item number, not a citation. `insights
  archive` lists the positional citations it is about to renumber, each with
  the ID its position holds before the move — rewrite them from that list.
- **Human gates have IDs of their own.** A gate is cited by the `gate-<hex>`
  ID `aide gate list` prints, under the same resolvability check (§1 → human
  gates).

**`resolve` writes the union of a conflicted inbox**, so this file's conflict
is never resolved by hand. **It refuses anything that is not a pure append** —
the immutability rule below, enforced where two branches meet — and a refusal
writes nothing. A conflict marker left in the file is an `aide check`
**error**, not a warning, and the message names this verb.

**The claim is immutable; its status is not.** The captured line is never
reworded, reordered, or deleted. Ticking the checkbox is the one in-place edit.
Status *about* a claim is bookkeeping: an entry may carry an **appendable
status trail** — dated lines, indented under the entry, newest last:

```
- [x] framework — <the original claim, never touched> *(item 117, 2026-08-20)*
  - **2026-08-20** → aide-loop issue #50
  - **2026-09-02** → issue rewritten; the original framing overstated the finding
  - **2026-10-11** → resolved in engine 1.16.0
```

A single routing pointer may still be appended to the entry line itself
(`- [x] … → <where it landed>`); the trail is what a *second* update goes in,
and what an entry whose premise decayed needs. An entry that **stays open**
can carry a trail too — `tick N --trail --pointer` writes the dated line and
leaves the checkbox alone, which is how a judgement that routes nothing (a
duplicate, a reason it stays) is recorded without a hand edit.

**What happens to a captured entry is two sections, read by the roles that
perform them.** §1 → `insights-triage.md` fixes how an entry is routed and
judged; §1 → `insights-maintenance-queue.md` fixes what a routed `defect`,
`gap` or `automation` entry becomes, and who reads the open inbox to find it.
Neither changes a byte of what is written here: capture is the same one line
whichever of them the entry is heading for.

#### Rationale

- **Why the engine version, and why after the date.** The date cannot stand in
  for it: a project runs an engine for as long as it likes after a release, so
  two entries captured the same week may sit either side of a restructure, and a
  reader who has only the date must re-derive which. It earns the most on a
  `framework` entry, which leaves for another repo and is triaged there months
  later by someone with no other way to know; it costs the same nothing on the
  rest.
- **Why the shape check is loose everywhere but the date.** A warning on a
  captured line can never be cleared, so a check that rejects an honest capture
  produces permanent noise, and permanent noise is what teaches a reader to
  skim the one run where a warning was real. Archived entries stop being
  checked for the same reason: immutability leaves no way to act on a warning
  about one.
- **Why the engine creates the file.** A role that copies the template by
  hand is a role writing outside its scope; the verbs commit the file when git
  can — on a branch, with an identity to commit as — and otherwise leave it
  untracked and say why in the notice, for the next commit to carry.
- **Why everything after capture has a verb.** Reading and triaging the file by
  hand is what made triage expensive enough to defer. An archive carries each
  entry and its trail across line for line and says so; an entry too malformed
  to yield a date can be moved by no cut at all, so `archive` names each one it
  left behind rather than dropping it silently.
- **Why capture has a verb.** Capture was a hand edit, and an unattended role
  stalled on a permission prompt for every one — eleven in one consumer queue
  (issue #363). Pre-approving edits of the file was the rejected alternative:
  it would have waved through every hand edit of a file whose claims are
  immutable, where a prompt is the right answer. The verb also guarantees the
  line's shape and fills the date and engine, so the shape check has nothing
  to warn about on a captured line; the round-trip refusal exists because a
  warning on a captured line can never be cleared.
- **Why `resolve` exists, and why it refuses.** Append-only means every pair of
  branches conflicts here, and the conflict is always a union: two branches
  that each captured an insight added lines at the same position, so a merge or
  rebase stops on this file routinely, and resolving it by hand is where "never
  reword a captured claim" gets broken, because whoever resolves it retypes the
  block. A conflict marker is an error rather than a warning because the
  markers are skipped rather than misread — they are not entry lines — which
  is worse: both sides' entries land in one numbered list, so `list` numbers
  straight across the halves and the `N` a reader takes from it points `tick`
  at a different claim than the one they read. The union needs no renumbering
  because nothing moves; a tick on either side stands and keeps its pointer,
  and two ticks with two different pointers are kept together and said so,
  because that one needs a human. A side that archived is refused because an
  archive cuts closed entries out of the middle and renumbers what remains, so
  the two sides no longer share a prefix — and each refused shape is a change
  to an immutable line, which is precisely what a human must see.
- **Why the claim is immutable.** That is what protects provenance, and it is
  load-bearing precisely when an entry turns out to be *wrong*: the wrongness
  is the record, and a correction written beneath it teaches what a silent
  rewrite would erase. Freezing the bookkeeping about a claim would buy
  nothing; without a trail there is nowhere to record that half a claim has
  since been fixed, so the next reader re-derives all of it. Two independent
  captures of one claim both stay because two roles noticing the same thing is
  itself a fact about the project.
- **Why entries have an ID, computed rather than written.** A position is
  stable only until an archive (which renumbers what remains) or a merge of
  two branches that each appended (one side's entries land after the
  other's) — and the inbox is *meant* to be archived, and branches that
  capture are *meant* to merge. One consumer paid for it three ways (issue
  #276): a spec and a test cited an entry number the inbox had never held,
  found only by accident; one merge renumbered forty entries, whose citations
  in a queue file, a gate row and two specs were rewritten by hand — and one
  immutable claim now points at the wrong entry forever; and tests that
  located entries in the live file turned red the moment an archive was
  measured. Two alternatives were weighed. Citing by date plus the claim's
  opening phrase needs no machinery, but is verbose, still ambiguous between
  two same-day entries that open alike, and uncheckable. A **counter** assigned
  at capture collides whenever two branches capture concurrently, the normal
  case with queue branches, so capture would need a verb or a merge-time
  renumbering — the problem again. A hash of the immutable claim collides only
  on the same claim captured the same day, which *is* the same claim; it needs
  no counter and no state on the writing side — `add` computes nothing another
  branch could also have taken — so two branches capturing at once never
  collide, and capture stays an append.
- **Why only the claim is hashed.** It is exactly the part no one may edit.
  The checkbox, the pointer and the trail are written by triage, so hashing
  them would change the ID on the first tick; whitespace is collapsed so an
  editor's rewrap is not a new claim. The type and provenance are immutable
  too but add nothing a date and a claim do not already separate.
- **Why a citation needs the word before it.** A dangling ID is an error, and
  since `merge` runs the checks (issue #232) an error blocks a merge; a bare
  `YYYY-MM-DD-<hex>` token is also a timestamp (`2026-09-24-1530`), a slug or
  a file name, and a false error there would block a merge on prose. The
  word costs the author nothing and makes a match a citation by construction.
  A positional citation is only a warning, because what a number meant when
  written cannot be recovered from the file alone. The archive run still knows
  what every number meant, so it prints the mapping before the move rather
  than refusing — the listing preserves it, and the move already waits on
  `--yes` (issue #295). After it, the check recovers the meaning from history
  (issue #361): the commit that last wrote the citing line, and the inbox as
  it stood in that commit. It once named what the number held *today*, and
  after an archive that is a different claim — following the hint rewrote the
  citation to point at something its author never meant. Today's holder is
  right only for a line not yet committed, and is offered, labelled, only
  where there is no history to read.
- **Why a record is not read for positions.** A record is never rewritten, so
  the warning could not be cleared — one consumer carried 394 warnings, about
  330 of them on merged specs and finished queues (issue #338) — and on a
  record written before an archive, the warning's hint then named whatever
  moved into that number since, which is a wrong answer offered as a fix. The
  archive listing still names a record's positions: it is printed by the one
  run that knows what the number meant. A dangling ID stays an error there, because
  no reader can follow it whoever wrote it.
- **Why tests are read for positions too.** A test comment or assertion
  message naming "insight 28" goes stale on the next archive or merge exactly
  as a spec does, and it is the test, not the spec, that the next author
  trusts (issue #295).
- **Why the inbox and its archives are not swept.** Their claims are immutable,
  so a finding on one could never be cleared — the same reason archived
  entries are not shape-checked.
- **Why capture is its own section.** Every role in the loop appends here and
  almost none of them triages: capture is on the always-on floor, while
  routing reaches the one pass that routes and the queue rules reach the one
  role that plans a batch. Splitting them by reader is what lets each be
  delivered whole to the roles that act on it, instead of one file three
  quarters of which is somebody else's job (issue #191).
