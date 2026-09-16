---
name: aide-feedback-loop
description: Analyze issues and suggest improvements to the process and documents.
---

# Feedback Loop

Analyze what went wrong and identify improvements — Step 7 of the AIDE loop,
available at any point. Use whenever work didn't go smoothly: human intervention
needed, unclear requirements, process breakdown.

## Instructions

Analyze the current state of the project documents and recent work.

### The modular passes this loop may call

Four passes are skills of their own, because each is useful without the rest of
the retrospective and each costs a whole loop to reach otherwise. Call the ones
this run needs; none of them is restated below.

| Pass | What it does | When |
|---|---|---|
| `/aide-review-insights` | triages the open inbox — routes by type, judges duplicates and decayed premises, files `framework` issues | at every queue boundary; always, if the inbox has unchecked entries |
| `/aide-review-permissions` | ranks the auto-logged permission prompts an unattended run stalls on | when a run needed a human to approve a command |
| `/aide-review-instructions` | reports which instruction files actually reached which sessions | when a rule looks like it never bound |
| `/aide-status-report` | regenerates the living HTML status page | when the visible snapshot has gone stale |

Triage is the one that always runs, and it runs *first*: what it routes is the
raw material for everything below.

### 1. Document gaps

- What should have been in `docs/aide/vision.md` but wasn't?
- What should have been in `docs/aide/roadmap.md` (dependencies, prerequisites)?
- What should have been in `docs/aide/progress.md` for tracking?
- Was the work item specification missing critical information? Were its
  **Assumptions** wrong or missing?

### 2. Process issues

- Did the human need to intervene? Why?
- Were requirements unclear (would `loop.clarify = "interactive"` have helped)?
- Were dependencies not identified upfront?
- Did scope expand unexpectedly?

### 3. Framework adaptations needed

The framework surface is: `.aide/` (conventions, templates, `aide.py`, loop),
`aide.toml`, `.claude/skills/aide-*`, `.claude/commands/aide-*`,
`.claude/agents/`. Consider:

- Should a template in `.aide/templates/` gain/lose a section for this project's
  needs? (Add project-specific blocks via the item template's guidance, not
  boilerplate.)
- Should an `aide.toml` value change (queue cap, clarify mode, git mode)?
- Should a deterministic step move into `aide.py` rather than agent prose?
- What worked well that should be kept?

Framework/process changes land via a **reviewed PR**, never a direct merge.

### 4. Consistency, permission bottlenecks & instruction delivery

- Run `python .aide/scripts/aide.py check` — fix any format-contract errors it
  reports (they break the scripts the loop depends on).
- **Permission bottlenecks and instruction delivery are queue-boundary questions
  too**, and both have a pass of their own (table above): run
  `/aide-review-permissions` for the prompts an unattended run stalled on, and
  `/aide-review-instructions` for which rules reached which sessions. Act on
  what each reports and rotate its log.

### 5. Recommendations

Provide specific, actionable suggestions: updates to vision/roadmap/progress,
template changes, `aide.toml` changes, new skills, process improvements.

### Important notes

- **Routine decisions** during smooth implementation belong in the work item's
  "Decisions" section, not here.
- This loop is for **systemic issues** needing process/document/framework change.
- **Be minimal** — the smallest set of changes that prevents recurrence.
