---
name: aide-review-insights
description: Triage the open insight inbox — route each entry by type, judge duplicates, decayed premises and wrong types, and hand `framework` entries over as issues.
---

# Review the insight inbox

Triage `docs/aide/insights.md`: read the open backlog, **route** each entry by
its type, **judge** the ones that no longer say what they used to, and hand
`framework` entries over to the framework repo. It is the boundary pass for
every type that lands in *this* project, and it runs on its own — before
authoring a queue, from `/aide-feedback-loop`, or whenever the inbox has grown.

A `framework` entry may already have been handed over on capture, so expect some
entries to be ticked before you arrive.

## Instructions

### 1. Read the backlog with the verb, not by opening the file

```
python .aide/scripts/aide.py insights list --open
```

The file interleaves closed and open entries, so reading it whole costs the
entire history to see a working set that is usually a dozen lines. Open the file
only when you need one entry's full context, and then only that entry.

### 2. Route each unchecked entry by its type

**Triage routes each unchecked entry by its type, and this table is the whole
rule** (`.aide/conventions.md` §1 → `insights-triage.md`, where it is written
once so that this pass and `/aide-create-queue` cannot hold different copies of
it):

| Type | Where it goes | Who ticks the entry |
|---|---|---|
| `knowledge` | the owning document — the smallest edit that preserves the fact | the triaging role, on the fold |
| `defect` | a candidate item on the **maintenance queue** | the queue that absorbs it |
| `gap` | a candidate item — maintenance queue, or the stage queue when the stage was going to fill it anyway | the queue that absorbs it |
| `automation` | a candidate item adding the script/CLI verb **and** the prose that mandates it | the queue that absorbs it |
| `framework` | an issue on `[framework] repo` from `aide.toml`; unset or offline, it stays pending | the filing role, on the hand-over |

**Routing a `defect`, `gap` or `automation` entry never ticks it.** You are
standing *at* the queue boundary, so the queue that would carry such an entry
does not exist yet: leaving it unchecked **is** the routing, and the open inbox
is what carries it to whoever authors that queue — which reads it with
`insights list --open` and either queues it or says why it passed it over.
Do not fix such an entry inline here either; that is the queue's work, reviewed
in the queue's PR. The exception is the entry you do **not** route — see
*decayed premise* in step 3, which closes one.

For an `automation` entry, both halves reach the queue or agents keep
improvising: the deterministic script/verb, *and* the prose edit that mandates
it. (Worked example: the `aide sync` / `aide gc` verbs replacing improvised git
recon.)

### 3. Judge the entry, and record the judgement as a trail line

Routing an entry as written is not the whole of triage. Three findings, one form
— **a dated trail line under the entry, never an edit to the claim**:

- **Duplicate** — the same claim as an earlier entry. Route the earlier one and
  point the later at it; both stay in the file, because two roles noticing the
  same thing independently is itself a fact about the project.
- **Decayed premise** — what the entry names no longer exists, or has already
  been fixed by work done since. **A decayed premise is ticked, because there is
  nothing left for a queue to carry** — the trail line says what closed it, and
  the claim remains the record of what was true when it was captured. This is
  the one tick you perform on a `defect`, `gap` or `automation` entry, and it is
  not a routing: nothing is being sent anywhere.
- **Wrong type** — the entry describes a defect and is filed as knowledge, or
  the reverse. Route it by what it *is* and say so in the trail; the type in the
  captured line is never rewritten.

**A ticked entry whose status is now stale gets a trail line too** — sweep the
recently-closed entries for one whose pointer you now know to be wrong. That is
triage as much as routing is, and it is what stops the next reader re-deriving
what you already know.

The verb writes a trail line when the entry is **already ticked**, which is why
you never edit the file by hand:

```
- [x] defect — <the original claim, never touched> *(item 117, 2026-08-20)*
  - **2026-09-02** → superseded: the fence it names was retired by item 121
```

### 4. Hand `framework` entries over as issues

A `framework` entry belongs to AIDE itself, not this project. If
`[framework] repo` is set in `aide.toml` and `gh` is available, file it:
`gh issue create --repo <owner/repo>` with a body carrying the observation and a
proposal. This stays `ask`-gated (§3) — a human confirms. Otherwise leave the
entry unchecked with a `(pending handover)` note.

**A `framework` issue body opens with the engine version the observation was
made under** — the body's first line, before the observation
(`.aide/conventions.md` §1 → `insights-triage.md`):

```
**Project:** <this repo> (consumer). **Observed under engine X.Y.Z**
(<item ref>, YYYY-MM-DD).
```

**Writing that header is the filing role's job; a form on the destination cannot
reach it** — `--body` bypasses any issue template the framework repo publishes,
and no template can reach a body composed here and passed on the command line.
It costs nothing, because **you already hold the fact**: the version is in the
entry's own marker (`*(item 042, 2026-08-29, engine 1.22.0)*`). If the entry
carries none, read `.aide/VERSION` and write it as *the version at triage time,
not at capture* — and say so in the body. The framework repo cannot see this
one, so an unmarked guess reads there as an observed fact.

### 5. Tick what you routed here, with the verb

A `knowledge` fold and a handed-over `framework` issue are routed *here*, so
they are ticked here — naming where each landed, never by editing the line,
which is how a claim gets silently reworded:

```
python .aide/scripts/aide.py insights tick 7 --pointer "docs/architecture.md"
```

That appends `→ docs/architecture.md` to the entry and flips its checkbox.
**Ticking the checkbox is the one in-place edit**, and the verb owns it.

Never reword, reorder or delete a captured claim — including one that turned out
to be wrong. The correction goes *beneath* it, in the trail.

### 6. Propose an archive when the closed history dominates

When the closed history has grown past the live working set, propose an
`insights archive --before <date>` to the human — it is a dry run until `--yes`,
and it **renumbers the entries that remain**, so it belongs at the *end* of a
triage pass, never the middle.

## Report

Say what you routed, in one block: the entries folded (with where), the ones
handed over (with issue numbers), the ones left open for the next queue and
which type each is, and every judgement you recorded. The count of entries left
open is what the next queue author is about to read.

## Command hygiene

The shapes are delivered by `.claude/rules/aide-command-hygiene.md` and stated
canonically in `.aide/conventions.md` §3. A `PreToolUse` hook
(`.claude/hooks/command_hygiene_guard.py`) enforces the mechanical ones.
