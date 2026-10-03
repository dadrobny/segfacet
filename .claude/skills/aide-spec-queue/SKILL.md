---
name: aide-spec-queue
description: Batch-author work-item specs for every unspecced item in a queue, interactively, on the queue's own branch — front-loading the human so execution can then run unattended.
---

# Spec a whole queue (batch, interactive)

Author the item specs for **all unspecced items in one queue** in a single
interactive sitting, committing them on **one branch** — the queue's own
`<prefix>queue-NNN` where it exists, so plan, specs and code land in the one
PR and the specs are reviewed with the plan, before its gate is approved.
Rationale ("front-load the human"): spec authoring is where human input pays
most, so answer the clarify questions while a human is present, then let
implementation (`/aide-run-queue`) run unattended, and review the merged
results afterwards.

`/aide-run-item` already skips spec-authoring when a complete spec exists, so
pre-authored specs make the execution loop composable as-is.

## User Input

$ARGUMENTS — a queue number (optional; defaults to the live queue — the
lowest-numbered one with open items).

## Instructions

1. **Identify the queue** (`docs/aide/queue/queue-NNN.md`, the Live one if no
   argument) and list its items that have **no** spec file in `docs/aide/items/`.
   If none, report "queue fully specced" and stop. A queue planned on its own
   branch has its file there and nowhere else, so read it after step 2's
   switch.
2. **One branch for the whole batch** — not per-item claim branches (those are
   created later, at execution time, by `aide claim`). Never compose the name
   by hand: one `aide claim` does not recognise as a queue branch retargets
   the merge silently.
   - **The queue has a queue branch** — the usual case, where
     `/aide-run-roadmap` or `aide queue start NNN` planned it: switch to that
     branch, with its name exactly as `python .aide/scripts/aide.py status`
     lists it (or as the head of the queue's draft PR), then `git pull` —
     skipped in `local` mode (§4) or with no origin, where
     `python .aide/scripts/aide.py env`'s `origin` line reads `not needed`
     or `none`. The specs join the plan there. Do **not** start a specs-queue branch beside it — that splits the
     queue's review across two PRs.
   - **The queue file is already on `main`** — a queue planned before this
     flow, with no queue branch — let the CLI create a specs-queue branch:
     ```
     python .aide/scripts/aide.py queue start NNN --specs
     ```
3. **Loop over the unspecced items in queue order.** For each, author the spec
   per the `aide-create-item` skill and `.aide/templates/item.md`, with clarify
   mode forced to **`interactive`** regardless of `loop.clarify`: ask the user
   up to 3 targeted questions per ambiguous item (batch related questions
   together to respect the user's time), and encode the answers. When run as an
   orchestrator, spawn a fresh `spec-author` per item with "clarify mode:
   interactive" in its brief and relay its questions to the user.
4. **Pin cross-item interfaces as Assumptions — from both ends, at the level
   the consumer reads.** These specs are written before their dependencies are
   *implemented*, so every interface a spec relies on from an earlier (unbuilt)
   item goes into its **Assumptions** block, and the producing spec pins what
   its consumers read at the level they read it — through its function or
   fixture where one exists, the file layout only for a consumer that parses
   the file. `.aide/conventions.md` §5 states both duties, the divergence
   hand-back, and the re-check at claim once the dependency has merged; the
   two defects it was earned by pull opposite ways (a tolerant reader where an
   assertion belonged; a layout hand-built by a consumer of one field), which
   is why the level matters. This keeps spec-first optional, not load-bearing.
5. **Reconcile the batch before landing it.** Every spec is visible at once,
   which is the one moment a cross-item collision is cheap to fix. Run the
   check rather than reading N specs against each other by eye:
   ```
   python .aide/scripts/aide.py check --queue NNN
   ```
   It reports two specs claiming **May change** on the same path, one spec's
   **May change** overlapping another's **Asserts against** (the collision that
   reliably reaches CI as a red test in the *earlier* item, for doing exactly
   what the loop asked), and dependency cycles or dependencies on items that
   exist nowhere. Fix each by amending a spec, naming which side changed.

   It also reports `queue-end-needed` and `queue-end-idle` warnings, which no
   spec amendment of yours settles: relay them to the user for the plan gate —
   a stage whose need no planned queue-end item meets, or a planned one with
   nothing left to do, which is theirs to drop. What each means is
   `aide check -h`, and the rule behind them is `/aide-create-queue`
   requirement 5.

   Then spawn the **`spec-reviewer`** agent once, for what the check cannot
   decide, because it turns on what a criterion *means* rather than what a spec
   declares — an AC that cannot be satisfied without touching a path its own
   spec never authorised or its Assumptions bar; a consumer asserting against a
   shape its producer never pinned; a dependency aside pointing the wrong way.
   Write the report first so the agent starts from it instead of re-deriving
   it, substituting this project's `docs_dir` (shown at its `docs/aide`
   default):
   ```
   python .aide/scripts/aide.py check --queue NNN --report docs/aide/status/queue-NNN-specs.json
   ```
   Give the agent the queue number and that path. It **reviews**, it does not
   fix: relay its findings to the user and let them arbitrate — every recorded
   instance needed a human call on which side was wrong (correct the AC, or
   widen the authorised paths). Apply the decisions to the specs yourself, then
   re-run the check. The report is derived output under `<docs_dir>/status/`;
   do not commit it. The installer's `.gitignore` block covers the default
   location only, so if this project moved `docs_dir`, confirm the directory is
   actually ignored before writing there.
6. **Commit per spec** on the batch branch (separate Bash calls):
   ```
   git add docs/aide/items/NNN-*.md
   git commit -m "docs(NNN): work item spec for <short title>"
   ```
7. **Land the batch.** Push the specs — the branch already tracks its
   upstream, so this types no branch name either:
   ```
   git push
   ```
   In `local` mode or with no origin (`aide env`'s `origin` line reads
   `not needed` or `none`), skip every push here: the specs stay committed
   on the branch.
   - **On the queue branch**, that is all: the specs join the queue's draft PR,
     and no second PR is opened. Tell the user to read them with the plan and
     then, where the queue has a plan gate, approve it on that branch
     (`python .aide/scripts/aide.py gate approve <gate-ID>`, then `git push`) —
     never approve it yourself. Execution then runs on the queue branch
     (`/aide-run-roadmap`, or `/aide-run-queue NNN` with the branch checked
     out), claiming per-item branches as usual.
   - **On a specs-queue branch**, stop and tell the user to open a PR for
     human review of the whole spec set. `aide queue pr` opens only a queue
     branch's PR, so this one is theirs to open (§3). After it merges, run
     `/aide-run-queue NNN` from `main` — execution proceeds unattended,
     claiming per-item branches as usual.

## Hard limits

- Specs only: no production code, no tests, no `pytest`, no `progress.md` edits.
- Do not create per-item `aide/NNN-*` claim branches — execution does that.

## Command hygiene

The shapes are delivered by `.claude/rules/aide-command-hygiene.md` and stated
canonically in `.aide/conventions.md` §3. A `PreToolUse` hook
(`.claude/hooks/command_hygiene_guard.py`) enforces the mechanical ones.
