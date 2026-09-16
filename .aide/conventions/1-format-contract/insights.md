### `insights.md` (optional, additive — the compound-engineering inbox)

Where out-of-scope learning goes so it is never lost *and* never acted on out
of scope. Every role captures into this file, so every role reads this section;
what happens to an entry *after* capture is two sections of its own, named at
the end. Any role, at any time, appends **one line** and returns to its task:

```
- [ ] <type> — <one line> *(item NNN, YYYY-MM-DD, engine X.Y.Z)*
```

with `<type>` one of **knowledge** (document it), **defect** (fix it), **gap**
(plan it), **automation** (a recurring manual/agent action deterministic code
could replace — script it), **framework** (belongs to AIDE itself).

**The file exists before a role needs it — the engine puts it there.**
`aide check`, `aide claim`, `aide queue start` and `aide insights list` each
create a missing `insights.md` as a byte-exact copy of
`.aide/templates/insights.md`. No role copies the template by hand, and an
existing file — malformed or not — is never touched.

**Name where it came from, in whatever form is honest.** The provenance before
the date is free-form and optional — write `item NNN` from inside an item,
`queue-NNN` for planning or spec-authoring done before any item exists,
`items NNN-NNN` for a finding that genuinely spans several, or omit it entirely
from a role outside the loop. Those are the conventional spellings, not a
grammar the CLI enforces: **the ISO date is the only part that is
load-bearing**, since `archive` cuts on it. Never bend a provenance to fit a
shape — collapsing `items 099-101` to `item 099` is a rewording the immutability
rule below forbids.

**Name the engine you were running, after the date** — `engine X.Y.Z`, one read
of `.aide/VERSION`. Optional and unenforced like the provenance — and **never
retrofitted**, since the claim line below is immutable: an entry captured
without one stays as captured.

`aide check` shape-checks entries, and only the date strictly.

**Capture is a plain append; everything after it has a verb.**

```
python .aide/scripts/aide.py insights list [--open] [--type T] [--trail]
python .aide/scripts/aide.py insights tick N --pointer "<where it landed>"
python .aide/scripts/aide.py insights archive --before YYYY-MM-DD [--yes]
python .aide/scripts/aide.py insights resolve [--dry-run]
```

`aide insights -h` states what each verb does. Two consequences an author
acts on: `tick` performs the one in-place edit below, and an archive renumbers
what remains, so re-run `list` after one.

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
and what an entry whose premise decayed needs.

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
- **Why capture is its own section.** Every role in the loop appends here and
  almost none of them triages: capture is on the always-on floor, while
  routing reaches the one pass that routes and the queue rules reach the one
  role that plans a batch. Splitting them by reader is what lets each be
  delivered whole to the roles that act on it, instead of one file three
  quarters of which is somebody else's job (issue #191).
