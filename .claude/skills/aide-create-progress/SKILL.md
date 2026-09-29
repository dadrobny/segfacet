---
name: aide-create-progress
description: Create a progress tracking file from the vision and roadmap.
---

# Create Progress File

Create the progress tracker — Step 3 of the AIDE loop and **the single source of
truth for implementation status** (item specs carry no status field).

## Prerequisites

- `docs/aide/vision.md` and `docs/aide/roadmap.md` must exist.

## Instructions

Read both documents. If `docs/aide/progress.md` already exists, **update it
incrementally** — do not regenerate from scratch. If it does not exist, create it
from the template **`.aide/templates/progress.md`**.

### Format contract (machine-parsed — follow exactly)

`progress.md` is parsed and edited by `python .aide/scripts/aide.py`
(`check`, `progress set`) and the status report. **`.aide/templates/progress.md`
is the model** — its header comment states the shapes (the two tables, the stage
sections, the flat deliverable bullets and their `*(Item NNN)*` markers, the
acceptance checkboxes) and its `## Status legend` table carries the status
vocabulary. Copy them from the open template rather than retyping them from
memory; `.aide/conventions.md` §1 → `progress.md` and §1 → status icons fix what
the cells may hold. **Re-read the template on an incremental update too** — that
path does not otherwise open it.

One rule the shape cannot carry, so it is stated here: if any roadmap stage
carries a `Target:` bullet (a measured outcome the work cannot guarantee — an
error rate, a benchmark), mirror it as a row of the optional
`## Outcome targets` table, **not** as an acceptance checkbox — targets gate
objectives, never stages (`.aide/conventions.md` §1 → `progress.md`).

Run `python .aide/scripts/aide.py check` after writing — it must pass.

### Updating an existing progress file

1. **Preserve all existing statuses** — never reset a non-planned status to 📋.
2. **Add new rows** for stages/deliverables that appear in the roadmap but are
   not yet tracked.
3. **Do not remove rows** — postpone a tracked item instead, with
   `python .aide/scripts/aide.py progress set NNN deferred --reason "…"`; the
   reason is the note, and its stage turns ⏸️ on its own once nothing else in
   it is open.
4. **Never uncheck** an already-checked acceptance box.

### Output

Save to `docs/aide/progress.md`.
