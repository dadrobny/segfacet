## 4. Git modes (`git.mode` in `aide.toml`)

Governs what the mode changes — where a claim branch goes, how an item lands,
and what kind of CI gate can see it. The human who sets it reads this; the
validator's merge step is pointed here, and `aide claim` and `aide merge`
carry it out.

Enforced **only** inside `aide claim` / `aide merge`; agent instructions are
identical across modes.

- **`auto-merge`** (default) — claim branch pushed; on validator PASS `aide merge`
  direct-merges to `main`, deletes the claim branch, then re-runs the test
  command and `aide check`. Both are a **gate**: green earns the ✅ and the
  push, red leaves the merge local, the item 🔍 and the claim branch back where
  it was, and says so. For `aide check` only an error is red; a warning is
  reported and never blocks.
- **`pr`** — claim identical; on PASS `aide merge` pushes the branch and **stops**
  ("open a PR"). The human opens the PR (`gh pr create` stays `ask`-gated).
- **`local`** — no pushes at all (offline). Claim is a local branch only (no
  multi-machine signal); merge is local into `main`, behind the same gate.

**The mode also decides what kind of CI gate can see a claim branch — pick it for
that too.** Per-item scope is checked as each claim branch merges (§1). Whether a
CI job can run that check depends on what the mode leaves behind for CI to
trigger on:

| `git.mode` | Claim branch pushed | PR opened | Per-item scope gate in CI |
|---|---|---|---|
| `auto-merge` | yes | no | **push-triggered only** — and see the caveats below |
| `pr` | yes | yes, by the human | **works**, in PR context |
| `local` | no | no | **unreachable** — nothing leaves the machine |

The distinction that matters is **PR context**, not visibility. `auto-merge`
pushes the claim branch like `pr` does, so a push-triggered workflow matching
`<branch_prefix>**` (§2 — default `aide/**`) can see it — but there is no pull
request, so no `github.base_ref` to diff against: the job must supply `--base`
itself, and it races the in-loop merge, which deletes the branch as soon as the
item lands. Under `pr` the PR carries both refs — head `aide/NNN-…`, base the
item's recorded base — which is exactly the diff `aide scope` wants, with no
branch-name parsing at all.

So the trade is real in both directions. `auto-merge` buys unattended throughput
and, unless a push workflow is deliberately built for it, leaves the gate
enforced **only** by the validator running `aide scope` in-loop: same machine,
same platform, same checkout that built the item — the §7 blind spot exactly.
`pr` buys the independent, second-platform signal back and costs one human PR
open per item. Choose deliberately rather than inheriting the default: **a
scope job written for PR context is green forever under `auto-merge` while
checking nothing**.

The branch *shape* is an independent axis and does not decide this: under the
stacked queue-branch model below, `pr` still works, since the PR's head is the
`aide/NNN-` claim branch and its base is the pushed queue branch.

**Where "`main`" above actually means "the base".** `main_branch` is the default
and is never removed as one, but real work stacks: a queue branch carries the
queue file, a roadmap deliverable and every item spec, and lands as **one**
reviewed PR — so each of its items must branch off *and merge back into* that
branch, not `main`. Two things make that work without a flag at every call site:

- **`aide claim` records what it branched off.** It creates the branch from
  whatever is checked out and remembers that as the item's base. Inference is
  deliberately narrow — only a *recognised* queue branch (`<prefix>queue-NNN`,
  `<prefix>specs-queue-NNN`), never an arbitrary checked-out branch.
- **`aide merge` returns the item to its recorded base**, so the validator's
  documented `aide merge NNN` step is correct on a queue branch with no change.

`--base <ref>` overrides on `claim`, `merge`, `gc` (which ref `--merged` is
measured against), `status` (what ahead/behind is reported from) and `scope`
(what the diff is taken against). Resolution is always **`--base` > recorded >
`main_branch`**. The record is local git config, not a committed file, so a
different machine falls back to `main_branch` and passes `--base` explicitly.

**A base is always a local branch**, and a claim always *branches from* it — the
branch's starting point and its recorded base are the same commit by
construction, so an item can never merge back somewhere it did not come from. A
tag, a raw commit or a remote-tracking ref (`origin/main`) is refused.

### Rationale

- **Why the claim branch goes before the gate run.** So the run sees what a
  fresh clone sees.
- **Why `aide check` is part of the gate.** Nothing else in the loop ran it
  mechanically: a consumer's ✅ stage over ⏸️ deliverables — an error — sat on
  its base for two weeks until an engine update surfaced it, and a consumer
  without its own test pinning the check would never have seen it (issue
  #232). The merge is the one seam every item crosses whether or not a
  validator ran. It reads the whole document set rather than the item's diff,
  so an error already on the base blocks too; telling the two apart would mean
  checking the base as well, and an unattended run that lands items over a
  broken document set is the failure being fixed. Warnings never block,
  because some are permanent by design (a retracted criterion, issue #152).
- **Why a CI gate can decay silently.** With no PR a PR-context scope job
  either never triggers, or triggers on a branch whose name yields no item
  number and correctly skips — so a gate can decay from a mode change alone,
  long after it was correctly built.
- **Why base inference is narrow.** Inferring a base from an arbitrary
  checked-out branch would silently retarget a merge.
- **Why the record is local.** The base is a fact about this checkout's
  branching, not about the project.
- **Why a base must be a local branch.** `git switch` to a tag, a commit or a
  remote-tracking ref would detach HEAD, and a merge into a detached HEAD
  updates no branch while still reporting success.
