# AIDE — rules that bind before anything points at them

**Framework-owned**: the installer maintains this file; edits here are lost on
the next update. It carries only what must bind *before* anything points
anywhere.

The rest of the contract is [`conventions.md`](conventions.md), an **index** — a
pointer to `§N` resolves to `conventions/N-*.md`. Each heading below names the
section carrying its full treatment; when a decision is not obvious, go read it.

## Durable artifacts must read cold — §1

Item specs, `insights.md` entries, commit messages and issue bodies outlive the
session that produced them. Write for the reader who opens one months from now
with none of the conversation.

1. **No chat-local identifiers.** A label coined for one conversation's
   convenience resolves only for someone who was there. Name a thing by what it
   is; title a change by the change.
2. **Cross-reference by resolvable identity** — an issue number, a file path, a
   commit, a stage number, a dated `insights.md` entry. Never "the companion PR"
   or "as discussed above" pointing outside the artifact.
3. **Record the decision and why it holds, not the route to it.** "My earlier
   lean was wrong", "agreed direction", "settled while drafting" narrate a
   process the reader was not part of.

## Out-of-scope learning is captured, never acted on — §1 → `insights.md`

Out-of-scope learning goes to `docs/aide/insights.md` so it is never lost *and*
never acted on out of scope. Any role, at any time, appends **one line** and
returns to its task:

```
- [ ] <knowledge|defect|gap|automation|framework> — <one line> *(item NNN, YYYY-MM-DD, engine X.Y.Z)*
```

The ISO date is the only part that is load-bearing. What precedes it is
free-form provenance and says where the insight came from: `item NNN` from
inside an item, `queue-NNN` from planning done before any item exists,
`items NNN-NNN` for a finding spanning several, or nothing at all. What follows
it is `engine X.Y.Z`, one read of `.aide/VERSION`.

A captured claim is **immutable**: never reworded, reordered, or deleted, not
even when it turns out to be wrong. Ticking the checkbox is the one in-place
edit, and `aide insights tick N --pointer` owns it; anything that happens to it
afterwards goes in dated lines, indented under the entry, newest last.

## Status lives in one place — §1 → `progress.md`

`docs/aide/progress.md` is the single source of truth for status, and the only
place the CLI reads. A status claim written anywhere else — a checklist in a
spec, a "current focus" heading, a summary in a README — is a second truth that
will disagree with the first. Move it, do not copy it.

## Each loop step ends in its own session — [`README.md`](README.md)

The step sequence is in `README.md`, and the run-* orchestrators drive it; a step
does not restate it. **Close a step by saying what it produced, not by naming the
next one**, and start the next step in a **fresh session**: each step derives
from the *written* document the last one produced, and a session still holding
the conversation that drafted it reproduces those assumptions instead of reading
the artefact.

## Root documents go through their entry point — §5

`vision.md` and `roadmap.md` are authored via the loop's create-vision /
create-roadmap entry points, which carry the safeguards a free-hand file write
skips. **Do not write a root document directly, however well the template shape
is known.** Authoring them is interactive whatever `loop.clarify` says: ask
until the mandatory sections are grounded in the human's answers, and present
the result as a draft. A wrong assumption at the root propagates into every
queue and item derived from it.

## Mechanical actions go through the CLI — §2, §4, [`README.md`](README.md)

```
python .aide/scripts/aide.py check | status | env | sync | claim | scope
    | merge | gc | progress set/accept | gate list/approve/decline
    | insights list/tick/archive | queue start/tidy
```

Prefer the verb to hand-editing a document or improvising git: it is what keeps
the documents parseable and an unattended run reproducible.

## Command hygiene — §3

One command per call — never chain with `&&`, `||` or `;`. No `cd` prefix and
no directory-changing wrapper, unless the repo is declared (§3); no `2>&1` or
other redirections. A long unattended run stalls on a permission prompt for any
command shape nothing pre-approved.

## Only a person resolves a human gate — §1 → Human gates

Any role may raise a gate; only a person may resolve one — the worst case of
raising one is work pausing. No agent may run `aide gate approve`/`decline`;
resolving is a CLI operation, never a hand edit. A gate exists precisely
because the decision is not derivable from the work.

## Another repository's instructions bind before you edit it — §8

A repository's own instructions bind for work inside it. A runtime loads
instruction files for the working directory's repo only; a declared sibling
(`.aide/loop/loop.local.toml`) — the framework clone included — gets nothing,
and nothing announces the gap. So read that repo's instruction file first,
before editing, committing to, or otherwise acting on it. Where two repos' rules
disagree about a file, the repo that owns the file wins.
