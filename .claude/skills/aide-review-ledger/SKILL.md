---
name: aide-review-ledger
description: Read the run ledger back by engine version and kind, annotate each cohort boundary with the framework releases and aide.toml changes behind it, and route what the readings suggest into the channels that already exist.
---

# Review the run ledger

Read `docs/aide/ledger.md` back as numbers, put each change in those numbers
beside what changed under it — a framework release, a project setting — and
hand whatever that suggests to the channel that already carries it. It runs on
its own, after a queue has closed, or from `/aide-feedback-loop`; nothing in
the item loop calls it.

**This pass proposes and edits nothing.** It writes no document, marks no row
as reviewed and never touches the ledger, which only the verbs write. What it
produces is a report to the person and, where one is warranted, an inbox line.

## Instructions

### 1. Read the report with the verb, not the file

```
python .aide/scripts/aide.py ledger report --json
```

Add `--queue NNN` to read one queue. No ledger means no item has been merged
or abandoned through the engine yet: say so and stop.

What each reading counts, and which cells it leaves out and why, is stated by
`python .aide/scripts/aide.py ledger -h`; what a cell means is
`.aide/conventions.md` §1 → `ledger.md`. Read both before interpreting a
number, and do not re-derive a ratio from the file — the verb is what applies
the cell rules, and a hand count is where a blank turns into a zero.

### 2. Size the evidence before reading a trend

Every reading carries its `n`. **Say plainly when a group holds fewer than
about ten rows: a per-version comparison over it is an anecdote**, and the
report describes it rather than drawing a trend from it. A kind present in one
cohort only has nothing to compare with. Withheld finding readings stay
withheld — do not fill them in from the raw cells.

### 3. Annotate each cohort boundary

Cohorts are ordered by engine version. For each boundary between two adjacent
ones, collect what changed between them, from two sources pulled on demand —
nothing is stored for next time.

**Framework releases.** Read `[framework] repo` from `aide.toml`. List the
releases and read every one after the earlier cohort's version, up to and
including the later one's:

```
gh release list --repo <owner/repo> --limit 200
gh release view v<X.Y.Z> --repo <owner/repo>
```

Keep what can move a reading: a role's model or effort, the review or
validation flow, how a ledger cell is derived, how tests are counted. If the
key is unset, `gh` is unavailable or offline, say the framework half was
skipped — never fill it in from memory.

**Project settings.**

```
git log -p --date=short --format="%h %ad %s" -- aide.toml
```

Place each change by its date against the groups' `first_date` and
`last_date`. A changed `[loop]` key matters most: the round cap is read
against the rounds distribution *as it stood when those rows were written*,
and `review` changes what the finding cells can hold.

A boundary with neither kind of change is worth saying too: whatever moved
there moved with the work, not the configuration.

### 4. Route what the readings suggest

One reading, one destination, each an existing channel:

- **An `aide.toml` change** — a suggestion to the person, naming the setting,
  the readings that motivate it and their `n`. The person edits the file.
- **A reading that points at the framework** — a change that follows an
  engine release across more than one kind or queue — one `framework` line in
  the insight inbox, captured as §1 → `insights.md` says. Triage hands it over
  (`/aide-review-insights`).
- **A reading about this project's own process** — one line in the inbox of
  whichever type fits it.
- **Something the next queue's planner should weigh** — a note in your
  report, addressed to whoever authors that queue.

A reading that suggests nothing is left as a reading.

## Report

One block: each group with its `n`; each boundary with the releases and
setting changes found there, or the source that was skipped; what was routed
where; and the small-sample caveat wherever it applies.
