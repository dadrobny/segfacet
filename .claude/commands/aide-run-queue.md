---
description: Iterate one AIDE queue to completion — `aide claim` claims each item, then /aide-run-item drives it (spec → tests → build → validate → merge) — looping until that queue is empty, then runs the queue-end step (mark the queue PR ready, wait for CI, read it; on red, a CI fix round through the items that caused it) and stops. Does NOT create the next queue. Pauses only for PRs and major structural changes.
argument-hint: "[queue number, e.g. 001 — optional; defaults to the lowest-numbered queue with open items]"
---

# Run one AIDE queue (iterator over /aide-run-item)

Drive the AIDE loop (`docs/aide/`) over **every remaining item in a single
queue**, then **stop**. This command is **queue-scoped**: it does *not* generate
the next queue — that is `/aide-run-roadmap`'s job (the loop *over* queues). This
session is only the orchestrator — do **not** author specs, write code, write
tests, or run tests yourself in the main thread. You **delegate each item to
`/aide-run-item`** and only handle claiming (via the `aide claim` CLI) and
approval gates between items.

Arguments: **$ARGUMENTS** — a queue number (if empty, the live queue: the
lowest-numbered `docs/aide/queue/queue-*.md` with open items).

**Orchestration model.** This dispatch-and-gate role is light — run it on
**Sonnet** (the heavy work is in the subagents, each on the model its agent
spec pins). A slash command can't pin the session model, so `/model sonnet`
first if you're on Opus.

**One session, one layer.** Per item, load `/aide-run-item NNN` **inline as a
skill in *this* session** — it is a prompt expansion, not a subprocess. The only
parallel/isolated contexts are the `Task` subagents (`spec-author`, `test-writer`,
`builder` or `builder-escalation`, `validator`, plus `reviewer` where `loop.review` turns it on) that do
the leaf work; claiming is a deterministic CLI
call, not a subagent. There is **no headless `claude -p` nesting** (an earlier
`--continuous` design tried it and was removed — see `/aide-run-roadmap` →
*Historical note*). The loop runs **in-place in the primary checkout**; for
parallel human work, isolate in a worktree per `/aide-run-roadmap` → *Working in
parallel*.

## Division of labour

| Concern | Owner | Notes |
|---|---|---|
| Claim the next 📋 item | `aide claim` (CLI) | `python .aide/scripts/aide.py claim [--queue NNN]` — syncs, checks `aide/*` branches, picks the first unclaimed unblocked 📋 item, creates + pushes `aide/NNN-*`; prints item number + branch + title, and the base when it is not `main`. Deterministic, no subagent. **Run it from the branch the queue's work belongs on**: claiming while a queue branch is checked out records that branch as each item's base, so `aide merge` returns the item to it and the whole queue still lands as one reviewed PR. |
| Run one item end-to-end | **`/aide-run-item NNN`** | spec-author → test-writer → builder → validator+merge, incl. the build↔validate cycle (≤`loop.validation_rounds` rounds). Under `loop.review = "background"` a `reviewer` reads the diff concurrently with the validator and the merge waits for both. See that command for the per-item detail. |
| Approval gates, looping | *orchestrator* | stays in the main thread |
| Generating the **next** queue | **not here** | only `/aide-run-roadmap` (or a manual `/aide-create-queue`) does that |

The per-item mechanics (which agent does what, the build↔validate cycle, when
a build fix escalates to `builder-escalation`) live in **`/aide-run-item`** — this command does not
restate them. Keeping a single source of truth for the item loop is the point of
the split.

**Command hygiene** applies to any git command you issue from this thread too.
The shapes are delivered by `.claude/rules/aide-command-hygiene.md` and stated
canonically in `.aide/conventions.md` §3; a `PreToolUse` hook
(`.claude/hooks/command_hygiene_guard.py`) enforces the mechanical ones.

## Pre-loop: resume in-flight branches

Before claiming new items, resume any interrupted ones. `aide claim` skips item
numbers that already have an `aide/*` branch, so an interrupted item would be
stranded otherwise.

**Orchestrator steps (run these yourself, not via a sub-agent):**

0. `python .aide/scripts/aide.py sync` — the deterministic preflight (fetch,
   clean-tree check). Do not improvise `git fetch`/`git status` instead.
1. `git branch | grep aide/` — list local `aide/*` branches.
2. If none, skip to the loop.
3. For each `aide/NNN-*` branch, read `docs/aide/progress.md`: if the item is
   already ✅/❌, skip it; if 🚧 or 📋, it is unfinished. Skip a ⏸️ item too:
   it waits on its owner, and once they resume it (`aide progress set NNN
   resumed --reason …`) it reads 📋 and is resumed here on the branch it
   kept. Skip a 🔍 item: its work is pushed and awaits a human's merge;
   step 0's `sync` names it once it has landed, with the `aide progress set
   NNN done` that records it.
4. For each unfinished item (item-number order), hand it to **`/aide-run-item NNN
   aide/NNN-short-name`**. `/aide-run-item` is itself resumable — its spec-author
   step returns an existing spec, re-checking a pinned dependency's interface
   first (that command's step 1, once per pin), and the validate/build cycle
   picks up from whatever is already committed — so just run it.
5. Process each resumed item to PASS+merge (or a user-stop) before claiming new
   work below.

**A queue branch with no PR gets its draft now.** When the checked-out branch
is a queue branch (`<prefix>queue-NNN`), find its `stack N:` line in
`python .aide/scripts/aide.py status` and read `pr=`:

- **`pr=none`** — open the draft before claiming the first item, so the queue
  end has a PR to mark ready:
  ```
  python .aide/scripts/aide.py queue pr --body "Work queue NNN. The plan is docs/aide/queue/queue-NNN.md on this branch; items merge into it as they pass validation."
  ```
  It pushes the branch first and titles the PR itself. On exit 1 relay its
  sentence and stop — above all a PR on the branch that was **closed or
  merged**, which a person decided and no second PR goes over.
- **`pr=#N/…` open or draft** (a draft may read `#N/draft(fixing)`, so match
  `/draft` as a prefix) — carry on.
- **`pr=-`** (`local` mode, or `[git] forge = "none"`) or **`pr=unknown`** — carry on, saying so for
  `unknown`; the queue-end step reports it again when it needs the PR.
- **`pr=#N/merged` or `#N/closed`** — stop and report it: this queue's batch
  was already decided.

## Loop

Repeat until `aide claim` reports no remaining unclaimed 📋 item **in this queue**:

1. **Claim → run the CLI** (orchestrator, not a subagent):
   ```
   python .aide/scripts/aide.py claim --queue NNN
   ```
   It syncs, checks `aide/*` branches, picks the first unclaimed 📋 item with no
   blocking dependency still 📋/🚧, creates + pushes `aide/NNN-short-name`, and
   prints the item number, branch name, and title. Prints `none left` when the
   queue is exhausted.

2. **Decide (orchestrator).**
   - **Item claimed** → go to step 3.
   - **`none left` alone on the line** → the queue is exhausted; go to
     **Queue end**.
   - **`none left — …` whose last line is `early ready: yes`**, exit 0 → every
     open item waits on a human gate and built work has landed. Relay the
     gate lines verbatim, run **Queue end** as an *early ready*, and stop:
     the gate is a person's, and its result is informational.
   - **`none left — …` followed by per-item reasons** → the queue is still open
     and nothing in it is offerable. This is **not** exhaustion. On exit 0 (a
     gate, a claim already in flight, a dependency not landed — the last line
     reads `early ready: no — …`) relay the reasons
     verbatim and stop. On a **non-zero** exit something is broken — an
     *unpublished claim* (an `aide claim` whose push failed), a claim branch
     origin has deleted (never re-push it), or a human-gates
     row `aide` cannot read, which holds every item — so surface it verbatim
     and stop: publishing or releasing that branch, or repairing that row, is
     the human's call.
   - **Any other non-zero exit** → surface the sentence and stop.

3. **Run the item** — load `/aide-run-item NNN aide/NNN-short-name` inline as a
   skill in this session. It drives the full per-item workflow (spec → tests →
   build → validate) and merges on PASS; **wait for it to finish** before looping.

4. **Checkpoint (orchestrator).** Relay a one- or two-line summary (item,
   merged/failed, key facts). If the item reported a **PR / force-push /
   structural** stop, **pause and ask the user**. Otherwise continue to step 1.

## Queue end

This is the queue-end step `.aide/README.md` → *The queue-end step* defines
(what triggers it, what each answer means); here is how this runtime runs it.
`/aide-run-roadmap` → **Queue end** runs this section too.

1. **Clean up.** `python .aide/scripts/aide.py gc` to preview, then re-run
   with `--yes` if the list is right. The preview is exactly the set `--yes`
   deletes, and `gc` deletes on the ✅ or ❌ ground only after asking git
   whether the work actually landed. **A `pr`-mode item awaiting its merge is 🔍, not
   ✅, so it is never in that list**; report those as awaiting review instead.
2. **No queue branch, no PR.** A legacy queue run from `main` has no queue
   PR: skip to the report.
3. **Mark it ready.** `python .aide/scripts/aide.py queue ready`. On exit 1
   relay its sentence and go to the report: `local` mode, no forge declared
   (`[git] forge = "none"`) or no origin (no forge exists — the merge gate
   already ran the suite), no PR, or a closed or merged one.
4. **Wait for CI, in this session.** Start the poll, then wait on its label
   until it answers:
   ```
   python .claude/scripts/await_run.py start ci
   python .claude/scripts/await_run.py wait <label> --for 540
   ```
   Give each `wait` Bash call `timeout: 600000`: the tool's default of
   120000 ms ends a 540-second wait as a timeout. Exit 75 is "still waiting":
   call `wait` again with the same label. Each call then stays under the Bash
   tool's ceiling, and the wait belongs to this
   orchestrator, never to a sub-agent or a backgrounded command: its cache
   outlives a 540-second wait, and a sub-agent that ends its turn to wait is
   never woken. The poll reads `aide status`, so it never asks the forge
   itself, and it does not take a first `checks=none` as the answer. Under
   `[git] ci = "none"` it answers at once (16).
5. **Read the exit code** `wait` returns once the poll has answered:

   | Code | `checks=` | Do |
   |---|---|---|
   | 0 | `success` | Report CI green, and stop for the merge — under `/aide-run-roadmap`, go back to its **Queue end** for the stack decision. |
   | 10 | `failure` | Every leg has finished (the poll waits out each `pending check:`). Report each `failing check:` line from the tail, then run the **CI fix round** below — unless this was an early ready (step 6). |
   | 11 | `none` | Report that no CI ran on the PR: no workflow, or a trigger that ignores it (`.aide/README.md` names the trigger to use). |
   | 12 | `unknown` | Report the `checks unknown:` reason and stop. |
   | 13 | — | No PR, a closed or merged one, or the branch is no longer an unmerged queue branch: report it. |
   | 15 | — | The PR is a draft. Plain `#N/draft`: `queue ready` did not take — run step 3 again, then restart the wait once; a second 15 is a stop. `#N/draft(fixing)`: a CI fix round is under way and its reopened items are still open — go back to **Loop** and claim them; a claim that offers none is reported, and the run stops. |
   | 14 | `pending` | CI was still running after an hour: report it; a re-run of this section waits again. When the tail already names a `failing check:` beside the `pending check:` legs, report those failing lines too: they are known, so the user can start the **CI fix round** on them now or re-run the wait for the rest. |
   | 16 | `-` | `aide.toml` declares no CI (`[git] ci = "none"`). Report "CI: none declared" — not a failure: the merge gate already ran the suite — and stop for the merge as for 0; under `/aide-run-roadmap`, go back to its **Queue end** for the stack decision. |
   | other | — | The poll itself broke (90 died, 91 stopped, 1 a crash): report the tail and stop. |

6. **After an early ready**, stop whatever the answer — a red one runs no
   fix round: the gated items land later, each merge pushes, and this
   section runs again when `aide claim` next prints a bare `none left`.
   That run's answer is the one that counts.

### CI fix round

`.aide/README.md` → *The CI fix round* defines it; this is how this runtime
runs it. You triage and dispatch; the fixing is `/aide-run-item`'s, through
the item's own spec.

1. **Count.** Read the `ci fix rounds: N` line from the wait's tail (none
   there: 0). Read `loop.validation_rounds` from `aide.toml` (5 when
   unset). At or past it, **stop**: report the failing checks and the
   last round's reopen reasons, and hand the findings to the user.
2. **Triage** every failing check before reopening anything. List them with
   `gh pr checks <prefix>queue-NNN`, whose links carry each run's ID, and
   read each failed log with `gh run view <run-id> --log-failed`; a check
   that is not a GitHub Actions run has no run ID, so pass its link to the
   user instead of reading it. Split a
   check into findings, one per failing test or step; rank each on the §9
   scale and triage it in scope (the queue's change caused it) or out of
   scope (one `insights.md` line, opening with its rank word, and nothing
   dispatched). A leg that failed here and passed locally is a portability
   finding first (§7). Red from the platform itself (a broken image, a
   network drop, a cancelled job) is no finding: name that check for the
   user to re-run. **With no in-scope finding left, stop here**
   and report, before the undo: the PR stays ready and no round is
   counted.
3. **Trace** every in-scope finding to its item:
   - `test_NNN_*` failing → item NNN;
   - otherwise the branch's history, `<base>` being the stack line's
     `base=`. This lists what landed, each item's work closed by its
     `progress(aide): item NNN -> done` commit:
     ```
     git log --first-parent --format="%h %s" <base>..HEAD
     ```
     and this the commits that touched a failing path:
     ```
     git log --format="%h %s" <base>..HEAD -- <path>
     ```
   - several items' changes in one finding → each of them; a failure only
     their combination produces → the later-merged of the two, its reason
     naming the other item;
   - no item at all (CI configuration, a runner image) → the queue's
     `Validate stage N` item if the queue file lists one; if not, **stop**
     with the findings, nothing reopened and the PR left ready.
4. **Back to draft**, before the first reopening:
   `python .aide/scripts/aide.py queue ready --undo`. On exit 1 relay its
   sentence and stop. A session that dies after this and before the first
   reopening leaves a plain draft; a resume finds the queue exhausted and
   marks it ready again at **Queue end** step 3, without counting a round
   — accepted, since it costs CI minutes only.
5. **Reopen** every traced item, one call each, all before the first claim:
   ```
   python .aide/scripts/aide.py progress reopen K --reason "CI <check>: <failing test or step>"
   ```
   Keep the `CI ` prefix: the engine stamps the round from it. Several
   findings on one item go in one reason, separated by `; `.
6. **Fix.** Go back to **Loop**. `aide claim --queue NNN` offers each
   reopened item as it offers any 📋 one, and `/aide-run-item K` runs it
   with the findings in its builder's brief (that command, *An item a CI fix
   round reopened*). Pass them on from your triage; in a fresh session they
   are the item's `reopened:` reason in `aide status`. Its merge ticks the
   `gap` the reopening captured; nothing is left to close on green.
7. When `aide claim` prints a bare `none left` again, **Queue end** runs
   again from its step 1; the `aide queue ready` there is what sets off
   this round's CI run.

Then **report**: items completed, items awaiting review, branches
merged/cleaned, the CI answer, and final test status. Point the user at the
next move (do **not** generate the next queue yourself):

- **On a queue branch**, the PR now carries the whole batch and is marked
  ready: review and merge it. The next queue is planned only after that PR
  merges, unless `[loop] max_open_queues` lets it start on top of this
  branch.
- **Driving the whole roadmap?** Run **`/aide-run-roadmap`** — it plans the
  next queue on its own branch behind a draft PR and a plan gate, and re-enters
  this command on that branch once the gate is approved.
- **Working a single batch manually?** Start a fresh chat and run
  `/aide-create-queue` for the next batch.

Permission prompts hit during the batch are auto-logged (`docs/aide/permissions/`);
suggest the user run **`/aide-review-permissions`** to promote recurring safe
prompts (it also **rotates** the log). Instruction loads are logged the same way
(`docs/aide/instructions/`); **`/aide-review-instructions`** says which rules
reached the batch's sessions, and rotates that log.

## When the orchestrator must stop and ask the user

- **`aide claim` reports an unresolved human gate.** Stop and surface it verbatim —
  do not prompt an unattended run for a decision nobody is there to make, and
  never run `aide gate approve` yourself. A gate exists because the decision is
  not derivable from the work; resolving it destroys the thing it protects. A
  gate naming items — directly or via a stage reach — skips only those, so the queue
  may keep going; an `all` gate stops everything. A queue's own plan gate, raised by
  `aide queue gate` when `/aide-run-roadmap` planned it, holds every item in the
  queue — or every item of the stage it opens — so the whole queue waits on it:
  the human reviews the queue's draft PR and approves it. When the report's
  last line is `early ready: yes`, run **Queue end** before stopping.
- **Queue end** answers anything but CI `success` or `failure` (the table in
  its step 5), or `aide queue pr` / `aide queue ready` refuses.
- A **CI fix round** reaches `loop.validation_rounds`, finds no in-scope
  finding (every red check infrastructure, flaky or out of scope), or traces
  a finding to no item on a queue with no `Validate stage N` item.
- `/aide-run-item` hands back needing a **PR**, **force-push**, or history rewrite.
- An item needs a **major structural change** or an edit to a framework/process
  file (`CLAUDE.md`, `aide.toml`, `.aide/**`, `vision.md`, `roadmap.md`,
  `.claude/skills|commands|agents/**`) — needs a reviewed PR, never a direct merge.
- A validator hands back **INCOMPLETE** (a run reached its limit; `/aide-run-item` step 6).
- The build↔validate cycle for an item stops (`/aide-run-item` step 6), or an item is blocked /
  contradictory — document the blocker and suggest `/aide-feedback-loop`.
