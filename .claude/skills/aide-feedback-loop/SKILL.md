---
name: aide-feedback-loop
description: Analyze issues and suggest improvements to the process and documents, then apply the project-document amendments the user agrees to.
---

# Feedback Loop

Analyze what went wrong and identify improvements — Step 7 of the AIDE loop,
available at any point. Use whenever work didn't go smoothly: human intervention
needed, unclear requirements, process breakdown.

## Instructions

Analyze the current state of the project documents and recent work.

### The modular passes this loop may call

Five passes are skills of their own, because each is useful without the rest
of the retrospective and each costs a whole loop to reach otherwise. Call the
ones this run needs; none of them is restated below.

| Pass | What it does | When |
|---|---|---|
| `/aide-review-insights` | triages the open inbox — routes by type, judges duplicates and decayed premises, proposes declines, puts each long-waiting entry to the owner, files `framework` issues | at every queue boundary; always, if the inbox has unchecked entries |
| `/aide-review-permissions` | ranks the auto-logged permission prompts an unattended run stalls on | when a run needed a human to approve a command |
| `/aide-review-instructions` | reports which instruction files actually reached which sessions | when a rule looks like it never bound |
| `/aide-status-report` | regenerates the living HTML status page | when the visible snapshot has gone stale |
| `/aide-review-ledger` | reads the run ledger back by engine version and kind, and annotates each cohort boundary with the releases and `aide.toml` changes behind it | when a queue has just closed and `docs/aide/ledger.md` exists; skipped without it |

Triage is the one that always runs, and it runs *first*: what it routes is the
raw material for everything below.

### Orchestration model

The retrospective is this session's own work; the reading behind it mostly is
not. Which pass runs where:

| Work | Runs | Model |
|---|---|---|
| `/aide-review-insights` — judging the open entries | the `insights-triager` sub-agent that pass spawns; its plan is applied here | the one its agent spec pins |
| `/aide-review-permissions`, `/aide-review-instructions`, `/aide-review-ledger`, `/aide-status-report` | here — each runs a script or a verb and reads its output | this session's |
| a measurement a finding needs — re-running a fixture, reading CI timings, reading a sibling repository's workflow | a read-only `Explore` sub-agent per question, fanned out in parallel | named at the spawn: `"haiku"` for a search or read sweep, `"sonnet"` where the helper must judge |
| steps 1–6 below — the gaps, the process, the framework, the recommendations, and the edits agreed to | here | this session's |

Name the model on every spawn you make here. `spawn_model_guard` refuses an
unnamed one only from inside a sub-agent, so in this session nothing stops an
`Explore` helper inheriting your model — and a sweep on the strongest tier
costs that tier for reading files. A slash command cannot pin the session
model: choose it for the retrospective, since that is what it is spent on.

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
  reports (they break the scripts the loop depends on). A `this machine:`
  error is reported to the human, never fixed by editing `aide.toml`.
- **Permission bottlenecks and instruction delivery are queue-boundary questions
  too**, and both have a pass of their own (table above): run
  `/aide-review-permissions` for the prompts an unattended run stalled on, and
  `/aide-review-instructions` for which rules reached which sessions. Act on
  what each reports and rotate its log.

### 5. Recommendations

Provide specific, actionable suggestions: updates to vision/roadmap/progress,
template changes, `aide.toml` changes, new skills, process improvements.

Each one falls on one side of a line, and say which:

- **A project document** — `docs/aide/vision.md`, `roadmap.md`,
  `progress.md`. This loop applies it (step 6) once the user agrees.
- **The framework surface** (step 3's list, `aide.toml` included) — it stays a
  recommendation. It lands through a reviewed PR, or goes upstream as a
  `framework` insight or issue; this loop edits none of it.

### 6. Apply the agreed document amendments

Propose each project-document amendment as the edit itself — the file, the
place, the text — and apply it only once the user agrees to it. Apply it
here: do not send the user to `/aide-create-vision`, `/aide-create-roadmap`
or `/aide-create-progress` for an amendment. Those author a document from
scratch, and are the route only when one needs rebuilding rather than
amending — it is missing, or its shape no longer holds what the project now
is.

- **Read the shape before editing.** The section for the document — §1 →
  `vision.md`, `roadmap.md` or `progress.md` — and its template in
  `.aide/templates/`. The edit keeps every shape the scripts parse.
- **Where a verb owns the edit, use the verb.** A status, a deferral, a drop,
  a criterion's wording, a correction to a ticked box, a reopened item:
  `aide progress` (`python .aide/scripts/aide.py progress -h` lists them).
  Never hand-edit what a verb writes; hand-edit only the prose no verb
  reaches.
- **The user's agreement is not an attestation or a resolution.** Ticking an
  acceptance box takes a check this session actually ran, passed as its
  evidence through `aide progress accept --evidence` (§1 → `progress.md`);
  agreeing to the recommendation is not one.
  A human gate may be raised here, but only a person resolves one (§1 →
  human gates) — leave `aide gate approve`/`decline` to them.
- **A decline or Backlog move the triage pass proposed is the user's to
  decide** (§1 → `insights-triage.md`), and so is every entry it brought
  back after three or more queues — whether to queue it, decline it, or
  move a `gap` to the Backlog. Put each to them with its reason,
  and apply only the ones they agree to: a decline with
  `aide insights tick N --pointer "declined: <reason>"`; a `gap` moved to
  the roadmap's `# Backlog` as a `roadmap.md` amendment, its bullet citing
  `insight <ID>`, then ticked `--pointer "roadmap Backlog"`.
- **Make the smallest edit that carries the agreed change**, and leave the
  rest of the document as it reads.
- **Finish with `python .aide/scripts/aide.py check`**, and clear any error
  the edit introduced before committing.
- **Commit on the current branch.** The verbs commit their own edits;
  commit a hand edit with the recommendation it applies. How that branch
  reaches `main_branch` is the merge policy's (`.aide/README.md`), not this
  loop's — and that policy puts `vision.md` and `roadmap.md` behind a
  reviewed PR. So when the current branch *is* `main_branch`, an amendment to
  either goes on a branch of its own, cut from `main_branch`, for that PR —
  not onto `main_branch` — and tell the user which branch the session is now
  on.

### Important notes

- **Routine decisions** during smooth implementation belong in the work item's
  "Decisions" section, not here.
- This loop is for **systemic issues** needing process/document/framework change.
- **Be minimal** — the smallest set of changes that prevents recurrence.
