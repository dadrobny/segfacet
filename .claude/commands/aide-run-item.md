---
description: Drive a single AIDE work item end-to-end — author spec, write tests, implement, validate, merge — via fresh sub-agents. The reusable unit that /aide-run-queue loops over. Pauses only for PRs and major structural changes.
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
**Sonnet** (the heavy work is in the subagents, each on the model its agent
spec pins). A slash command can't pin the session model, so `/model sonnet`
first if you're on Opus.

## Task → sub-agent mapping

| Step | Task | Sub-agent | Notes |
|---|---|---|---|
| 1 | **Author the item spec** | `spec-author` | writes `docs/aide/items/NNN-*.md` (Description, atomic AC, steps, testing strategy, deps, decisions), commits. **No code, no tests.** Skip only if the spec file already exists and is complete — and its Assumptions pin no dependency's interface; if they do, it re-checks them (step 1). |
| 2 | **Write tests** for the item | `test-writer` | reads spec + AC + existing test style, writes one test per AC plus the cases the Testing Strategy names, commits. **No production code, no pytest.** |
| 3 | **Implement** production code | `builder` (`builder-escalation` once escalated, step 6) | checkout branch, implement `source_dir` per every AC, record decisions, set progress in-progress (`aide progress set NNN in-progress`), commit. **No tests, no pytest.** |
| 4 | **Review** the diff | `reviewer` | **only when `aide.toml` sets `loop.review = "background"`** (default `"off"`). Dispatched **once per run** (§9), in the background, the moment builder first returns, concurrent with the first step 5 over the same branch — never again after a fix round. Reads the diff adversarially and reports findings; writes nothing, merges nothing. |
| 5 | **Validate** (+ merge, unless held) | `validator` | a **different** agent: runs pytest, checks AC coverage + scope + vision fit, then on PASS reconciles via the CLI (`aide progress set NNN in-review`) and merges (`aide merge NNN` — `merge` writes the ✅ itself once the merge lands). **Under `loop.review = "background"` the merge is held**: it stops after the reconcile, reports PASS (merge held), and *you* merge once the review is discharged. **No new tests.** |

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
`aide merge NNN` yourself once its findings are triaged. The reviewer reads
the diff as the run first built it, once per run; its findings are triaged at the first
verdict, PASS or FAIL, and a fix round is followed by a fresh validator
alone, handed the blocking findings fixed on the branch to check each left a
traced test or said why not — never to judge the fix. Scope and vision fit
are the validator's checks either way.

**Command hygiene.** Sub-agents (and you) emit git/CLI commands in the
allow-list-friendly shape delivered by `.claude/rules/aide-command-hygiene.md`
and stated canonically in `.aide/conventions.md` §3. A `PreToolUse` hook
(`.claude/hooks/command_hygiene_guard.py`) enforces the mechanical ones.

## A reopened item

`aide progress reopen` sends a ✅ item back to 📋 with a reason, and the queue
offers it like any other; `aide status` prints `reopened: item NNN (…) — <the
reason>` for it. Its owner reopens one when a gap turns up after the merge;
`/aide-run-queue` → *CI fix round* reopens one whose change broke the queue
PR's CI, with a reason starting `CI `. Either way its spec and tests are
already merged, and its **findings** are what the reopening found: the
owner's reason, or the CI failures the orchestrator triaged. So the steps run
with four differences:

- **Step 1** (`spec-author`) returns the existing spec, as for any item
  whose spec exists.
- **Step 2** (`test-writer`) **is skipped** unless a finding is in a test or
  is an owner's reason about behaviour. For a CI finding in a test, brief a
  fresh `test-writer` with that finding in place of step 2's brief — fix the
  named test, add none — and the builder still follows for any finding in
  production code. An owner's reason is dispatched as the last bullet says.
- **Step 3's brief — the `builder`'s — carries the findings**, as a
  blocking review finding is carried in step 6. Add to it:
  > This item was reopened, and these findings are why: <each: what was
  > found, and for a CI one the check, the failing test or step and the log
  > lines that show it>. Fix them within the spec's authorised paths.

  They come from the orchestrator's triage, or, in a fresh session, from the
  item's `reopened:` reason. A reason that names nothing to change — a
  check that was never run, say — or asks for behaviour the spec does not
  specify is not a build: stop and ask the user.
- **An owner's reason leaves a test traced to it, or says why it has none**
  (§9), as a blocking review finding does: the spec's checks passed while
  its gap was there, so they cannot be what measures the fix. It is
  blocking because its owner reopened the item for it — do not re-rank it —
  and you decide only whether it is about behaviour, as *Blocking, in
  scope* (step 6) decides. If it is, a fresh `test-writer` follows the
  builder before step 5, briefed with the reason to write the test that
  answers it and record its `## Review findings` bullet, the finding
  quoting the reason; for a reason about a test, that `test-writer` is the
  whole test-side dispatch, and the test it fixes or adds is the one traced to it —
  the builder still follows for any part of it in production code. If
  it is not — a document or a name — add to the builder's brief that it
  records the bullet, ending with why there is no test, in the commit with
  the fix. Collect the label from the return: step 5's blocking-findings
  paragraph names it from the run's first validator on. It is still not a
  review finding, so no `--findings` total counts it. A CI finding needs
  none of this: the failing test or step it names is its check, and the
  next CI run re-runs that (§9).

Steps 4–6 run as for any item: a reopened item is a new run (§9), so under
`"background"` its `reviewer` reads the diff this run builds, beside its first
validator, and its findings are triaged and counted like any run's. Its
rounds count against this run's own `loop.validation_rounds`, apart from the
CI round the queue counts for a CI reopening.

## An item awaiting its evidence gate

A 🔍 item whose last validator reported **PASS (awaiting gate-<hex>)** (step 6)
resumes once `python .aide/scripts/aide.py gate list` shows that gate's
verdict:

- **✅ Approved** → skip steps 1–4 and dispatch a fresh `validator` (step 5)
  with the round number its last PASS had: nothing was fixed, so the check is
  not a round. It re-runs every check, finds the AC covered and merges —
  under `loop.review = "background"` it stops at PASS (merge held) as usual,
  and you merge with the totals you kept, or without `--findings` in a
  session that no longer has them (the merge says so).
- **❌ Declined** → a FAIL of that AC: a fresh builder with the person's
  decision note, then a fresh `validator`, counted against the cap as any
  round. The rebuilt item needs the check asked again, so brief a fresh
  `spec-author` before that validator to re-ask it as a new Gate cell and
  re-point the AC's annotation at the new ID (§1 → human gates).
- **⏳ still** → nothing to do; report it and stop.

## Steps

1. **Spec → spawn `spec-author`.** Brief:
   > Author the work-item spec for AIDE item NNN on branch `aide/NNN-short-name`.
   > If `docs/aide/items/NNN-*.md` already exists and is complete, just return its
   > Acceptance Criteria. Otherwise read the queue line, roadmap stage, progress
   > rows, and vision; write the full spec with atomic, testable AC; commit it.
   > **Do NOT write code or tests; do NOT run pytest.**
   > Return: spec path + the list of Acceptance Criteria.

   **A spec that already exists may be stale on one point** (`.aide/conventions.md`
   §5): an Assumption that pins the interface of an item under
   `## Dependencies`. Such a pin was written before that item was built (the
   batch-authored case), and the item is claimed now, so the dependency has
   merged since — the pin is the whole signal, and no date is compared. `aide
   claim` printed the pins when the item was claimed (a later `aide claim
   --dry-run` picks the next unclaimed item, not this one, so it cannot
   reprint the line — read the spec's Assumptions and Dependencies yourself
   if the claim output is gone); where one names the other, brief the
   `spec-author` to re-check instead of returning the criteria unread:
   > The spec for AIDE item NNN exists on branch `aide/NNN-short-name` and its
   > Assumptions pin item(s) <MMM>, which have since merged. Re-check every
   > Assumption that pins their interface against the real code now on the
   > base branch. Append a dated re-check to each — agreeing, or correcting it
   > with the original left standing (§1 → items.md); never rewrite. Commit.
   > Return: the Acceptance Criteria, and which Assumptions changed.

   This runs **before** step 2, so no test is written from a stale pin. §5
   names what is not a pin — an audit Assumption (a defensible default, an
   engine version), one already re-checked, a dependency that left the queue
   as ❌/⏸️ — so a resumed item is not re-checked twice.

2. **Write tests → spawn a fresh `test-writer`.** Brief:
   > Write tests for AIDE item NNN on branch `aide/NNN-short-name`. The spec
   > (`docs/aide/items/NNN-*.md`) is committed. Read it for all Acceptance
   > Criteria, the Testing Strategy's named cases, and Decisions; read `tests/`
   > for style. Write one test per AC (named for it) and one per named case
   > (named for its label) — no others. An AC whose line carries an
   > *(evidence: gate-…)* annotation gets no test: list it as gate-covered.
   > Commit to the branch.
   > **Do NOT touch `src/` and do NOT run pytest.**
   > Return: bullet list of AC / case → test-name mappings.

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
   the background, once per run**, immediately after builder first returns
   **implemented** and before you dispatch step 5, so it reads while the
   validator's suite runs. Never re-spawn it after a fix round (step 6).
   Brief:
   > Review the diff for AIDE item NNN on branch `aide/NNN-short-name`. The spec
   > is `docs/aide/items/NNN-*.md`. Read the diff adversarially for defects the
   > spec never anticipated. **Do NOT write code or tests, do NOT run pytest, do
   > NOT merge or touch progress.md.**
   > In scope means the finding is about what this diff did, in any file it
   > touched. Those are for the orchestrator to dispatch. Anything about code
   > this diff left alone is out of scope: one `insights.md` line each, opening
   > with the rank word. The authorised paths and the vision are the
   > validator's checks: if you notice an edit to a path the spec never
   > authorised, name it apart from your findings, unranked.
   > Return: findings, most-severe first, each with file, line, and the input or
   > state that triggers it, each triaged in scope / out of scope, and each
   > carrying a proposed rank on the §9 scale — blocking, minor or nit.

   Hand it the contents of the repo's `REVIEW.md` in the prompt if one exists —
   a sub-agent inherits `CLAUDE.md`, not the review contract.

5. **Validate → spawn a fresh `validator`** (a *different* agent). Brief:
   > Independently validate AIDE item NNN on branch `aide/NNN-short-name`.
   > Run the full suite with `aide test`, as your spec's step 1 says; a red
   > one is judged as that step says (§9), by `git.mode`. Check every AC in `docs/aide/items/NNN-*.md` has a
   > test; check builder's `source_dir` changes are in scope; check alignment with
   > `docs/aide/vision.md` and the spec's Assumptions. **Do NOT write or modify
   > tests.**
   > PASS: reconcile + merge via the CLI —
   > `python .aide/scripts/aide.py progress set NNN in-review` then
   > `python .aide/scripts/aide.py merge NNN --rounds R`, started and waited on
   > through `.claude/scripts/await_run.py` as your spec says (honours git.mode: direct-merge +
   > branch cleanup + re-test for auto-merge, where a red re-test blocks the ✅
   > and the push and exits non-zero unless every failure was already failing
   > on the base; push-and-stop for pr; local merge for
   > local). **`in-review`, never `done`** — ✅ means merged and is written by
   > `merge` itself, so under `pr` the item stays 🔍 until a human merges the PR;
   > marking it done here is what once let the exhaustion sweep target an open
   > PR's head branch. FAIL: report which check failed, what it showed (the
   > failing test or criterion and its output), and whether builder or
   > test-writer must fix it. Do not merge.

   Substitute **R** with this dispatch's round number — 1 the first time,
   and the count you are already keeping for the cap in step 6 on every
   re-dispatch. The flag is what puts the round count in the ledger row
   (`merge -h`); a brief that leaves R unsubstituted is a brief the validator
   cannot act on. The validator never passes `--findings`: where it merges at
   all, `loop.review` was `"off"` and no reviewer ran, so the engine marks
   those three cells itself — they read `-`, not blank (§1 → ledger.md).

   **Under `loop.review = "background"`, add to that brief** — the first
   sentence on the first dispatch only, since no reviewer runs beside a later
   one:
   > A `reviewer` is reading this same diff concurrently. **The merge is held**:
   > do every check and the attestation as usual, run
   > `python .aide/scripts/aide.py progress set NNN in-review`, then **stop and
   > report PASS (merge held)** — do NOT run `aide merge`. The orchestrator
   > merges once the review findings are discharged.

   **When a fix round in this run has carried blocking review findings, or
   the run is an owner's reopen (*A reopened item*), add to that brief** —
   the owner's reason from the first dispatch on, and every review finding
   fixed so far, not only the last round's, so a trace a red suite kept a
   validator from reaching is still checked — less any whose code a later
   round removed or rewrote, together with the test that measured it: that
   finding stays counted, and is checked no more. A session that resumes
   mid-cycle takes them from the spec's `## Review findings` bullets ranked
   blocking; re-checking a trace costs a read:
   > This branch fixed blocking findings — review findings, or the reason
   > its owner reopened it: <each: its label in the spec's
   > `## Review findings`, and the finding in one line>. Check each as your
   > spec's check 7 says: its bullet is there, and names a test traced to it
   > or why it has none. Do not judge the fixes themselves.

6. **Build/test ↔ validate cycle (orchestrator).** A **round** is one build
   or test fix followed by a fresh `validator` — never a fresh `reviewer`: a
   run is reviewed once, as it first built the diff (§9). Read `loop.validation_rounds`
   from `aide.toml` (5 when unset): it is the ceiling on rounds per run. Read
   the verdict:
   - **Any FAIL of the first validator, `loop.review = "background"`** →
     before dispatching the fix, wait for the reviewer you spawned in step 4
     if it has not returned and triage and rank its findings exactly as *PASS (merge held)* below
     says, keeping the same running totals. Send the in-scope blocking
     findings, the minor ones you choose to fix and any nits **in the same
     fix round** as the validator's failures, by owner of the file — builder
     for production code, `test-writer` for tests, one after the other on
     the one branch, never both at once: one fix pass for both reads, one
     round. A blocking finding is dispatched as *Blocking, in scope* below
     says, traced test included. Then a fresh `validator`, merge still
     held, and no `reviewer`. The bullets below say which builder and which
     failure goes where.
   - **FAIL — suite red (code bug)** → fresh builder on the same branch with the
     reproduce steps; then a fresh `validator`. Under `auto-merge` or `local`
     this is the merge refusing failures the item caused (§9): brief the
     builder with those tests, not the inherited ones listed beside them.
   - **FAIL — missing AC coverage** → fresh `test-writer`; then a fresh `validator`.
   - **FAIL — a blocking finding left no trace (check 7)** → the dispatch
     *Blocking, in scope* below names for it, with the finding again: a fresh
     `test-writer` for one about behaviour, the role that fixed it for one
     about no behaviour, to add the bullet and its reason. Then a fresh
     `validator`. It is a round like any other.
   - **FAIL — out-of-scope / vision conflict** → fresh builder to revert/fix;
     then a fresh `validator`.
   - **Which builder — escalation is a judgement, not a round number.** A quick
     fix to a *newly found* failure goes to `builder`, round after round.
     Dispatch `builder-escalation` instead when either
     - a failure has **survived** a round: the same failure, or the same root
       cause, is reported again after a fix aimed at it; or
     - the first FAIL already shows a **serious** defect — a wrong approach or
       a missing mechanism rather than a slip: several criteria failing
       together, or a design-level mismatch with the spec.

     Once escalated, every later build dispatch for this item — review fixes
     and nits included — goes to `builder-escalation`. Brief it as step 3,
     adding "escalated: <the failure and the fix it survived, or why it is
     serious>". A `test-writer` fix never escalates.
   - **Stop** when a failure survives an escalated round — this loop cannot fix
     it — or when the item has used `loop.validation_rounds` rounds. Record
     what the item cost, document the blocker in the item file, ask the user:
     ```
     python .aide/scripts/aide.py ledger abandon NNN --rounds R
     ```
     R is the rounds actually run; under `loop.review = "background"` add
     `--findings` with the totals you kept. No merge will ever write a row
     for this item, and this is the one a reader at the queue boundary is
     looking for (`ledger -h`). It records; it decides nothing about the item's status.
     That is the user's call: if they decide against the work, record it
     with `python .aide/scripts/aide.py progress set NNN dropped --reason
     "<their decision>"` — never a ❌ typed over the bullet — and if they
     want it later, with `deferred` the same way.
   - **INCOMPLETE — a run hit the validator's 50-minute dispatch budget, hung,
     or died** → not a FAIL and not a round: nothing failed for a builder to
     fix. Do not re-dispatch a validator into the same wait — report the
     command, elapsed time and log tail to the user and stop, like a blocked
     item. Under `loop.review = "background"`, wait for the reviewer first,
     if step 4 spawned one, and put its findings in that report: they are the run's one review,
     still untriaged, and whoever resumes the item triages them. The validator has already stopped the run; what hung is for a
     person to look at. For a merge, pass on the log tail, which holds
     `aide merge`'s own word on the base, the claim branch and what to
     re-run — and if the validator reports the merge **still running**
     (`stop` exited 93), say that first.
   - **PASS (awaiting gate-<hex>)** → every check held, and an AC's evidence
     is a person's check that has not been approved yet (§9). The item is 🔍
     and unmerged — `aide merge` refuses it until the gate is ✅ — and that is
     not a round. Under `loop.review = "background"` triage the first
     validator's review as *PASS (merge held)* below says, and dispatch any
     fix first: the person checks what will land. Then tell the user which
     gate to check, for which AC, on which claim branch — they check the
     built item there and run `python .aide/scripts/aide.py gate approve
     <ID>` (or `decline`) on that branch — and stop for this item. See *An
     item awaiting its evidence gate* above `## Steps` for what follows.
   - **PASS**, `loop.review = "off"` → the validator has reconciled progress and
     merged. Done. A PASS may name inherited failures the merge admitted; the
     merge has already put them in `insights.md`.
   - **PASS (merge held)**, `loop.review = "background"` → on the first
     validator, wait for the reviewer, if step 4 spawned one and it has not
     returned, then triage its
     findings (§9). A path the reviewer named apart from its findings, as
     one the spec never authorised, is not a finding: the validator's
     `aide scope` has passed, so it is answered — never rank or count it.
     After a fix round there is no new review: the findings were triaged at
     the first verdict, so drop any the round did not fix whose code it
     removed or rewrote anyway — and take it off your totals — and go on with
     what is left, usually nothing. A finding the round fixed stays counted.
     If the validator
     listed failing tests, the merge you run below decides them: a refusal
     naming failures the item caused is a FAIL, handled like the first bullet
     above, and counts as a round. Rank every one of
     them as you triage it: the reviewer's rank is a proposal, this call is
     yours, and where the repo's `REVIEW.md` ranks differently it wins. Keep a
     running total per rank — it is what you pass to the merge.
     - **Blocking, in scope** → a fresh builder of the item's tier
       (`builder-escalation` once escalated) for production code, or
       `test-writer` (tests) with the finding, then a fresh `validator`, merge
       still held, and no `reviewer`. These are validation rounds and count
       against the cap. **Each one leaves a test traced to it, or says why
       it has none** (§9): decide as you rank it whether it is about
       behaviour. If it is, a fresh `test-writer` follows the builder in the
       same round, briefed with the finding to write the test that answers
       it and record its bullet; for a finding in a test, that `test-writer`
       is the whole dispatch, and the test it fixes or adds is the one
       traced to it. If it is not — a document or a name — brief the role that
       fixes it to add the finding's `## Review findings` bullet, ending
       with why it has no test, in the commit with the fix. Collect each
       finding's label from the returns: the next validator's brief names
       them (step 5).
     - **Minor, in scope** → your call: the same dispatch (a validation
       round, counted against the cap like any other), or one `insights.md`
       `defect` line instead of it. Say which you chose and why.
     - **Nit, in scope** → counted, and never worth a validation round of its
       own. Fold it into whatever build dispatch a blocking or minor
       finding is already causing. If nits are all that is left, send them on
       their own to a builder of the item's tier — a fresh one, or the one you
       last used if it is still around — and when it returns, **merge: no `validator` and no
       `reviewer` behind it, and nothing added to the round count.** A nit
       that would change behaviour was ranked wrong; re-rank it and pay the
       round.
     - **Out-of-scope findings** → the reviewer already appended them to
       `insights.md`, whatever rank they carry. Nothing to dispatch.
     - **Nothing in scope left** → the review is discharged and both gates have
       passed — after a fix round, on the fresh validator's PASS alone, with
       no second review to wait for — so merge deterministically yourself:
       ```
       python .claude/scripts/await_run.py start merge NNN --rounds <rounds this run took> \
           --findings blocking=A,minor=B,nit=C
       python .claude/scripts/await_run.py wait <label>
       ```
       That is `python .aide/scripts/aide.py merge NNN` with those flags, run
       detached the way the validator runs it (§9): `wait` in its default
       240 s calls, each a Bash call with `timeout: 600000` (the 120000 ms
       default cuts it short), never a turn ended to await it, and at 50 minutes
       `python .claude/scripts/await_run.py stop <label>` and report the
       command, elapsed time and log tail to the user instead of sitting on
       the run — the tail normally carries the merge's own restore message (with none,
       check the base for an unticked, unpushed merge whose claim branch is
       gone), and a
       `stop` that exits 93 means the merge is still running. It honours `git.mode` and writes the ✅ itself; `--rounds` is the
       count you kept for the cap and `--findings` the totals you kept while
       triaging, and the two are what put those cells in the ledger row
       (`merge -h`). A, B and C are in-scope review findings only: one you
       sent to `insights.md` is carried by that line and by no cell here,
       and an owner's reopen reason is no review finding (§9). Substitute
       them with your counts — a command left with its placeholders in it is
       not a command. **A non-zero exit means
       nothing was pushed** — under `auto-merge` it re-runs the full suite and
       `aide check`, and a red re-run, a document error or a tick it cannot
       commit leaves the item 🔍 (a tick committed but not replayed onto
       origin leaves it ✅ here only, and it says so); report it and stop
       rather than ticking anything by hand. A red re-run whose failures all
       predate the merge is admitted with exit 0 (§4); `merge` records those
       in `insights.md` itself, so report them and capture nothing more. Under `pr` it pushes and stops:
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
- A validator reports **PASS (awaiting gate-<hex>)** (step 6): an AC waits on
  a person's check. Name the gate, the AC and the claim branch, and stop.
- A validator hands back **INCOMPLETE** (step 6): a run hit its budget, hung,
  or died, and was stopped. Report the command, elapsed time and log tail; do
  not re-dispatch.
- The **build↔validate cycle stops** (step 6: a failure survived an escalated
  round, or `loop.validation_rounds` was reached), or the item is blocked /
  contradictory. Document the blocker and suggest `/aide-feedback-loop`.
