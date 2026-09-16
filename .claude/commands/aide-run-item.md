---
description: Drive a single AIDE work item end-to-end — author spec (Opus), write tests, implement, validate, merge — via fresh sub-agents. The reusable unit that /aide-run-queue loops over. Pauses only for PRs and major structural changes.
argument-hint: "<item number, e.g. 014> [branch name — optional; defaults to the existing aide/NNN-* branch]"
---

# Run one AIDE work item (sub-agent orchestrator)

Take **one** already-claimed work item from `docs/aide/` through the full
workflow — **spec → tests → implementation → validation → merge** — and stop.
**This session is only the orchestrator:** do not author the spec, write code,
write tests, or run tests yourself in the main thread. **Spawn a fresh sub-agent
for each distinct task** so every task runs in its own isolated context.

Item: **$ARGUMENTS** (first token = item number NNN; optional second token =
branch name, else the existing `aide/NNN-*` branch).

> **Prerequisite:** the item must already be **claimed** — an `aide/NNN-*` branch
> created by `python .aide/scripts/aide.py claim` (or by you). This command does
> *not* claim items; the queue loop does. If no branch exists, stop and tell the
> caller to claim it first.

**Orchestration model.** This dispatch-and-gate role is light — run it on
**Sonnet** (the heavy work is in the Opus/Sonnet subagents). A slash command can't
pin the session model, so `/model sonnet` first if you're on Opus.

## Task → sub-agent mapping

| Step | Task | Sub-agent | Model | Notes |
|---|---|---|---|---|
| 0 | **Author the item spec** | `spec-author` | **Opus** | writes `docs/aide/items/NNN-*.md` (Description, atomic AC, steps, testing strategy, deps, decisions), commits. **No code, no tests.** Skip only if the spec file already exists and is complete. |
| 1 | **Write tests** for the item | `test-writer` | Sonnet | reads spec + AC + existing test style, writes tests for every AC + adversarial cases, commits. **No production code, no pytest.** |
| 2 | **Implement** production code | `builder` | Sonnet (→ Opus on 3rd attempt) | checkout branch, implement `source_dir` per every AC, record decisions, set progress in-progress (`aide progress set NNN in-progress`), commit. **No tests, no pytest.** |
| 2b | **Review** the diff | `reviewer` | Sonnet | **only when `aide.toml` sets `loop.review = "background"`** (default `"off"`). Dispatched in the background the moment builder returns, concurrent with step 3 over the same branch. Reads the diff adversarially and reports findings; writes nothing, merges nothing. |
| 3 | **Validate** (+ merge, unless held) | `validator` | Sonnet | a **different** agent: runs pytest, checks AC coverage + scope + vision fit, then on PASS reconciles via the CLI (`aide progress set NNN in-review`) and merges (`aide merge NNN` — `merge` writes the ✅ itself once the merge lands). **Under `loop.review = "background"` the merge is held**: it stops after the reconcile, reports PASS (merge held), and *you* merge once the review is discharged. **No new tests.** |

**Spec authoring, testing, implementation, and validation are always separate
agents.** No agent signs off its own work. Spawn a **new** instance of each per
item — never reuse across items. Pass only the **minimum** between agents: the
item number, the branch name, and (from spec-author) the list of AC.

**Validation and review are two different reads of one diff** (`.aide/conventions.md`
§9), so neither stands in for the other. Read `loop.review` from
`aide.toml` before dispatching the builder: `"off"` (the default) runs the
validator alone — no `reviewer` is spawned, and the validator merges as it
always has; `"background"` runs both, and **the merge waits for both** — a
review whose findings arrive after the merge gates nothing. Under
`"background"` the validator stops at PASS with the merge held, and you run
`aide merge NNN` yourself once its findings are triaged.

**Command hygiene.** Sub-agents (and you) emit git/CLI commands in the
allow-list-friendly shape delivered by `.claude/rules/aide-command-hygiene.md`
and stated canonically in `.aide/conventions.md` §3. A `PreToolUse` hook
(`.claude/hooks/command_hygiene_guard.py`) enforces the mechanical ones.

## Steps

1. **Spec → spawn `spec-author` (Opus).** Brief:
   > Author the work-item spec for AIDE item NNN on branch `aide/NNN-short-name`.
   > If `docs/aide/items/NNN-*.md` already exists and is complete, just return its
   > Acceptance Criteria. Otherwise read the queue line, roadmap stage, progress
   > rows, and vision; write the full spec with atomic, testable AC; commit it.
   > **Do NOT write code or tests; do NOT run pytest.**
   > Return: spec path + the list of Acceptance Criteria.

2. **Write tests → spawn a fresh `test-writer`.** Brief:
   > Write tests for AIDE item NNN on branch `aide/NNN-short-name`. The spec
   > (`docs/aide/items/NNN-*.md`) is committed. Read it for all Acceptance
   > Criteria and Decisions; read `tests/` for style. Write tests covering every
   > AC (named clearly) plus adversarial edge cases. Commit to the branch.
   > **Do NOT touch `src/` and do NOT run pytest.**
   > Return: bullet list of AC → test-name mappings and adversarial scenarios.

3. **Implement → spawn a fresh `builder`.** Brief:
   > Implement AIDE item NNN on branch `aide/NNN-short-name`. Spec and tests are
   > committed. `git switch aide/NNN-short-name`, implement `source_dir` (from
   > `aide.toml`) per every AC, record decisions in the spec, then
   > `python .aide/scripts/aide.py progress set NNN in-progress`, commit.
   > **Do NOT write tests and do NOT run pytest.**
   > STOP and hand back if a PR, force-push, or framework change is needed.
   > If the spec and the tests contradict each other, do NOT pick a side —
   > return the contradiction instead, naming the criterion and the test.
   > Return: **implemented** (one-paragraph summary) or **spec/test
   > contradiction** (the criterion, the test, and what they disagree about).

   **If builder returns a spec/test contradiction, route it to `spec-author`,
   not back to builder** (`.aide/conventions.md` §5). The builder read both and
   has no standing to arbitrate; the spec is corrected first. Brief a fresh
   `spec-author`:
   > AIDE item NNN, branch `aide/NNN-short-name`. The builder found the spec and
   > the committed tests in contradiction: <criterion>, <test>, <the
   > disagreement>. Decide which side is wrong and correct the spec — an
   > **appended, dated correction**, never a rewrite of the original criterion
   > (§1 → items.md). Resolve it under `loop.clarify`, as §5 in your context
   > says. Commit.
   > Return: which side was wrong, and the corrected criterion.

   Then re-derive: a fresh `test-writer` (step 2) against the corrected
   criteria, then a fresh `builder` (this step). This is a **spec correction,
   not a validation round** — it does not count against `loop.validation_rounds`,
   which bounds the build↔validate cycle. Cap it at **one** correction per item:
   a second contradiction on the same item means the criteria are not
   arbitrable by this loop, so stop and ask the user.

4. **Review (only when `loop.review = "background"`) → spawn a `reviewer` in
   the background**, immediately after builder returns **implemented** and
   before you dispatch step 5, so it reads while the validator's suite runs.
   Brief:
   > Review the diff for AIDE item NNN on branch `aide/NNN-short-name`. The spec
   > is `docs/aide/items/NNN-*.md`. Read the diff adversarially for defects the
   > spec never anticipated. **Do NOT write code or tests, do NOT run pytest, do
   > NOT merge or touch progress.md.** Findings in scope for this item are for
   > the orchestrator to dispatch; out-of-scope ones are one `insights.md` line
   > each.
   > Return: findings, most-severe first, each with file, line, and the input or
   > state that triggers it, and each triaged in scope / out of scope.

   Hand it the contents of the repo's `REVIEW.md` in the prompt if one exists —
   a sub-agent inherits `CLAUDE.md`, not the review contract.

5. **Validate → spawn a fresh `validator`** (a *different* agent). Brief:
   > Independently validate AIDE item NNN on branch `aide/NNN-short-name`.
   > Run the full pytest suite. Check every AC in `docs/aide/items/NNN-*.md` has a
   > test; check builder's `source_dir` changes are in scope; check alignment with
   > `docs/aide/vision.md` and the spec's Assumptions. **Do NOT write or modify
   > tests.**
   > PASS: reconcile + merge via the CLI —
   > `python .aide/scripts/aide.py progress set NNN in-review` then
   > `python .aide/scripts/aide.py merge NNN` (honours git.mode: direct-merge +
   > branch cleanup + re-test for auto-merge, where a red re-test blocks the ✅
   > and the push and exits non-zero; push-and-stop for pr; local merge for
   > local). **`in-review`, never `done`** — ✅ means merged and is written by
   > `merge` itself, so under `pr` the item stays 🔍 until a human merges the PR;
   > marking it done here is what once let the exhaustion sweep target an open
   > PR's head branch. FAIL: report which check failed and whether builder or test-writer
   > must fix it. Do not merge.

   **Under `loop.review = "background"`, add to that brief:**
   > A `reviewer` is reading this same diff concurrently. **The merge is held**:
   > do every check and the attestation as usual, run
   > `python .aide/scripts/aide.py progress set NNN in-review`, then **stop and
   > report PASS (merge held)** — do NOT run `aide merge`. The orchestrator
   > merges once the review findings are discharged.

6. **Build/test ↔ validate cycle (orchestrator).** Read the verdict:
   - **FAIL — suite red (code bug)** → fresh `builder` on the same branch with the
     reproduce steps; then a fresh `validator`.
   - **FAIL — missing AC coverage** → fresh `test-writer`; then a fresh `validator`.
   - **FAIL — out-of-scope / vision conflict** → fresh `builder` to revert/fix;
     then a fresh `validator`.
   - Cap at **3 validation rounds**. Still failing after round 3 → stop, document
     the blocker in the item file, ask the user.
   - **Round-3 builder** (validator FAILed twice): spawn with `model: opus` and say
     "attempt 3, validator failed twice — hard defect, deeper analysis on Opus."
   - **PASS**, `loop.review = "off"` → the validator has reconciled progress and
     merged. Done.
   - **PASS (merge held)**, `loop.review = "background"` → wait for the reviewer
     if it has not returned, then triage its findings (§9):
     - **In-scope findings** → a fresh `builder` (production code) or
       `test-writer` (tests) with the finding, then a fresh `validator`, merge
       still held. These are validation rounds and count against the cap.
     - **Out-of-scope findings** → the reviewer already appended them to
       `insights.md`. Nothing to dispatch.
     - **Nothing in scope left** → the review is discharged and both gates have
       passed, so merge deterministically yourself:
       ```
       python .aide/scripts/aide.py merge NNN
       ```
       It honours `git.mode` and writes the ✅ itself. **A non-zero exit means
       the item did not land** — under `auto-merge` it re-runs the full suite and
       a red re-run leaves the item 🔍 with nothing pushed; report it and stop
       rather than ticking anything by hand. Under `pr` it pushes and stops:
       leave the item 🔍 and report that it awaits review.

7. **Report.** Return a one- or two-line summary (item, merged/failed, key facts).
   If any agent reported a **PR / force-push / structural** stop, surface it so the
   caller can pause for the user.

## When to stop and ask the user

- **A human gate blocks this item** (`aide check` warns; `aide gate list` shows
  it). Report it and stop. Never run `aide gate approve` — a person decides.
- A `spec-author`, `builder`, or `validator` hands back needing a **PR**,
  **force-push**, or history rewrite.
- The item needs a **major structural change** or an edit to a framework/process
  file (`CLAUDE.md`, `aide.toml`, `.aide/**`, `vision.md`, `roadmap.md`,
  `.claude/skills|commands|agents/**`) — needs a reviewed PR, never a direct merge.
- The **build↔validate cycle exceeds 3 rounds**, or the item is blocked /
  contradictory. Document the blocker and suggest `/aide-feedback-loop`.
