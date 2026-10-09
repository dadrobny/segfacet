## 4. Git modes (`git.mode` in `aide.toml`)

Governs what the mode changes — where a claim branch goes, how an item lands,
and what kind of CI gate can see it. The human who sets it reads this; the
validator's merge step is pointed here, and `aide claim` and `aide merge`
carry it out.

`auto-merge` and `pr` differ **only** in how an item lands, inside
`aide claim` / `aide merge`. `local` also turns off every fetch, pull and push
any verb makes, not only those of `claim` and `merge`, and every question to
the forge. Agent instructions are identical across modes. Any other value is
an `aide check` error.

- **`auto-merge`** (default) — claim branch pushed; on validator PASS `aide merge`
  direct-merges to `main`, deletes the claim branch, then re-runs the test
  command and `aide check`. Both are a **gate**: green earns the ✅ and the
  push, red leaves the merge local, the item 🔍 and the claim branch back where
  it was, and says so. For `aide check` only an error is red; a warning is
  reported and never blocks.
- **`pr`** — claim identical; on PASS `aide merge` pushes the branch and **stops**
  ("open a PR"). The human opens the PR (`gh pr create` stays `ask`-gated).
- **`local`** — no fetch, pull or push at all (offline). Claim is a local
  branch only (no multi-machine signal); merge is local into `main`, behind
  the same gate.

**Whether the project has a forge, and whether CI runs on its queue PR, are
declared, never inferred.** `[git] forge` is `"github"` (default) or
`"none"`; `[git] ci` is `"pr"` — CI runs on the queue PR — or `"none"`, and
defaults to `"pr"` with a forge and `"none"` without one. With no forge, no
verb asks one anything: `aide queue pr` and `aide queue ready` refuse, `aide
status` reads every forge field as `-`, and the queue-end step reports that no
forge exists and ends, as in `local` mode; `auto-merge` still pushes. With no
CI, `aide status` reads `checks=` as `-`, and the queue-end step goes from
marking the PR ready to stopping for the merge. `mode = "pr"` with no forge
is an `aide check` error — under `pr` a person opens each item's PR on the
forge — and so is `ci = "pr"` with no forge, or any value outside these.
`"github"` is the one forge the engine can ask.

**A mode this machine cannot meet is refused, never adapted.** Every mode but
`local` needs a remote named `origin`, and the forge's CLI, `gh`, logged in
unless `[git] forge = "none"` declares no forge. A
requirement the configuration needs and the machine lacks is a refusal that
names the setting needing it and the two ways out: meet it, or change the
setting. No verb and no role lowers the mode or rewrites `test_command` to
fit the machine; a refusal goes to a person. A verb that would push refuses
a missing `origin` before it creates, runs or writes anything, so the refusal
leaves nothing to clean up. `aide env` reports every
requirement. A plain `aide check` errors on the part decided offline, each
error marked `this machine:`; `aide check --queue` judges documents only.
`aide env -h` and `aide check -h` state each line.

**A red test run is compared with the base before it refuses.** Where the
test command's report names each failing test — pytest, run as a module —
`aide merge` runs the same command on the base as it stood before the merge,
in the same checkout, or reuses a run this repository already recorded for
that tree. When every failure after the merge also fails there, the failures
are **inherited**, and the gate admits the merge: it prints both sets, counts
them in the ledger row (§1 → `ledger.md`), and appends one `defect` entry to
`insights.md` naming each inherited test no open entry already names,
committed with the ✅. A failure the base does not have is the item's, and
refuses the ✅ and the push as before, listed apart from the inherited ones.
A run that cannot be compared — another runner, a command whose failures
depend on the run rather than the tree, an incomplete run, a base the
history does not identify — refuses on any failure. No flag and no
`aide.toml` key admits a failure the comparison did not, and `--no-test`
still skips the whole run. The role that started the merge does not capture
the inherited failures itself: the entry is the engine's. `aide merge -h`
states which options and exits keep the plain gate.

**A merge that lands exactly the tree validation ran does not run the suite
again.** Validation runs the suite through `aide test`, which records the
result against the tree, the command, the claim branch and the commit. Where
the post-merge tree is the claim branch's own and that branch changed nothing
but the progress document after the recorded run, `aide merge` takes the
recorded result in place of a second run — through the same gate, so a red one
still meets the base — says so, and marks the ledger row's `Suite s` cell as
reused. Every other merge runs the suite as above: a base that moved, a
commit after the run, a tree with tracked changes, a run recorded on another
branch, in another checkout or by anything but `aide test`. Taking a recorded run is not an
override, and `--no-test` takes none. `aide test -h` states the conditions
exactly.

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

- **`aide claim` records what it branched off.** Without `--base` it infers
  the base from what is checked out, creates the branch from that base and
  remembers it as the item's base. Inference is deliberately narrow — only a
  *recognised* queue branch (`<prefix>queue-NNN`, `<prefix>specs-queue-NNN`),
  or a claim branch (`<prefix>NNN-…`), which stands for the base it recorded
  and is refused when it recorded none; never an arbitrary checked-out
  branch.
- **`aide merge` returns the item to its recorded base**, so the validator's
  documented `aide merge NNN` step is correct on a queue branch with no change.

`--base <ref>` overrides on `claim`, `merge`, `gc` (which ref `--merged` is
measured against), `status` (what ahead/behind is reported from) and `scope`
(what the diff is taken against). Resolution is always **`--base` > recorded >
`main_branch`**. The record is local git config, not a committed file, so a
different machine falls back to `main_branch` and passes `--base` explicitly.
`queue start` and `queue restack` take `--base` too, naming the branch a queue
is stacked on (below).

**A base the loop writes to is always a local branch.** `claim` records it and
*branches from* it, `merge` merges into it and pushes it, and `queue start` and
`queue restack` stack a queue branch on it — only a branch moves forward, so
those four refuse a tag, a raw commit or a remote-tracking ref (`origin/main`).
A claim's starting point and its recorded base are the same commit by
construction, so an item can never merge back somewhere it did not come from.
A verb that only *measures* — `scope` (the diff) and `status` (where a 🔍
claim's work has landed) — takes any commit-ish as `--base`, and a
remote-tracking ref is often the right one there: a PR-context CI job on a
detached checkout has no local base branch and passes `--base origin/<base>`.
`gc --merged` measures and then deletes, so it fails safe on a non-local base:
`origin/<main_branch>` counts as `main_branch`, a base named `origin/<branch>`
is still that branch and never a target, and under any other base a queue
branch is not collected.

**At most `[loop] max_open_queues` queue branches are unmerged at once, and
they form one stack.** At the default of 1 a queue starts only once the one
before it has landed. Above it, the next queue starts on the top of the
stack — `aide queue start M --base <prefix>queue-N` — and its PR is opened
against that branch, so each PR's diff is one batch. `aide queue start`
enforces both: it counts a queue branch until the branch's own work has
landed in `main_branch`, judged the way `aide queue restack` judges it, and
refuses a start that would pass the cap or begin a second stack. A
specs-queue branch is neither counted nor stacked. `aide queue -h` states the
mechanism.

**A stack of queue branches is kept consistent by merging forward, never by
rebasing.** A queue started on the queue branch below it — `aide queue start M
--base <prefix>queue-N` — makes a stack, `main` ← queue N ← queue M, each
queue one PR against the branch below. `aide queue restack` merges a moved
lower branch into every branch above it, bottom up; once any branch of the
stack has landed in `main_branch` it merges `main_branch` into the next
branch up and records `main_branch` as that branch's base, so `merge`,
`scope` and `status` resolve against the right ref — whatever lies below the
landed branch, and an open branch left beneath it is not touched. A branch
may land by a merge commit, a squash or a rebase merge, or by a
fast-forward, which is told from a branch with no commits of its own by
where the branch started: the commit `aide queue start` records, or the tip
of the branch below it. A bottom with no such record (started before
2.14.0, or on another machine) whose tip is on `main_branch`'s first-parent
history stops the run until a person says which it was. Whether a branch
landed is judged from git; the verb reads no pull request, so a PR closed
without merging looks open to it and its caller checks for one first. A conflict stops the
run with nothing resolved, for a person. `aide queue restack -h` states the
mechanism.

**A stack is built bottom up: the lowest queue branch with work left is the
one built.** That is the top, except when a person adds an item to a lower
queue's PR in review. `restack` then carries the item into every branch
above, where the live queue — the lowest-numbered open one — is that lower
queue again, so a claim on an upper branch would take the item and land it
in the upper's PR. It is built on the lower queue's own branch instead, and
restacked forward from there.

**`aide status` reports the stack, and keeps two facts apart.** It prints
each unmerged queue branch bottom first — its base, its PR's state where the
forge can be asked, whether the branch below has moved since the last
restack, and whether a PR below it was closed without merging, which orphans
it — then **runnable** (the loop has work it could start) and **awaiting
review** (a queue PR is open and marked ready — a draft is the loop's own
PR still being built) on lines of their own. A repo can be both. A
caller deciding whether the loop is blocked reads those two lines rather than
its own reading of the branches, and takes "could not look" as an answer of
its own, never as "no PR". `aide status -h` states each field and value.

**A queue's own PR is opened and marked ready by the engine.** `aide queue
pr` opens the queue branch's draft PR against the base `aide queue start`
recorded; `aide queue ready` marks it ready for review, and `--undo` turns it
back into a draft. Each acts on the PR whose head is the queue branch and on
nothing else, and refuses in `local` mode, with no forge declared, or with
no remote. `aide status`
reports that PR's CI state on its stack line, and tells a draft sent back for
a fix round from one never marked ready. A caller waiting on CI reads it
there, never by asking the forge itself, and does not take a first "no
checks" just after a push as the answer: CI may not have started yet.
`aide queue -h` and `aide status -h` state the mechanism.

### Rationale

- **Why `local` is stated apart from the landing modes.** The opener used to
  say the mode was enforced only inside `aide claim` / `aide merge`, while
  `local` had long been skipping the network in `sync`, `status`, `gc`,
  `queue start`, `queue restack` and the commit behind `gate`, `progress` and
  `insights` — a reader choosing a mode was told less than it changes (issue
  #307). The rule names what `local` turns off, not a list of verbs: a list
  goes stale the next time a verb learns to fetch, and "every fetch, pull and
  push" stays true of it. The forge was named later (issue #352): `aide
  status` still asked `gh` for its open-PR line in `local` mode, and printed
  "could not look (gh is not on PATH)" on a machine meant to be offline.
- **Why a mode the machine cannot meet is refused.** Nothing reported whether
  a machine could run what the configuration asked, so a missing requirement
  was found mid-run by whichever verb met it first. The worst case was
  `auto-merge` with no `origin`: `merge` did all of its local work, ticked ✅,
  then failed at the push on every retry. The installer scaffolded
  `auto-merge` into a target with no remote, or one that was no repository at
  all (issue #354); it now reports the offline part after it writes, and its
  interactive prompt offers `local` on a target with no `origin`. `merge`
  itself still found out last until the verbs that push asked first (issue
  #377): each pushes as its last step, so `claim` and `queue start` left a
  branch with its base recorded, `queue restack` its merges, and `merge`
  under `auto-merge` a ✅ origin never received, after a full suite run per
  retry. Lowering the mode to `local` instead would silently keep every item
  on one machine for an owner who chose to publish — the failure an unknown
  mode already had.
- **Why the check judges only part of the machine, and only when plain.** The
  offline part is git, the repository, `origin` and the test command. `gh`'s
  login is left out because asking needs the network, and the check runs
  where there may be none; the venv because `aide env --bootstrap` is what
  builds it. `--queue` is the planner's and the spec-reviewer's run, and a
  machine error there would read as a document to fix — the edit of `[git]
  mode` or `test_command` this rule forbids. The `this machine:` mark keeps
  the plain run's errors apart for the same reason.
- **Why the printed interpreter is a note.** It decides only what a suggested
  command says, not what any verb runs, so a host with only `python3` is told
  the `[tools] python` that fixes the suggestion and fails nothing.
- **Why an unknown mode is an error.** Every verb compares the value against
  `local` or `pr`, so anything else — a `"Local"` — ran as `auto-merge`,
  pushing from a checkout its owner had set offline, and nothing said so
  (issue #352).
- **Why the forge and CI are declared.** Both were inferred: "no forge" only
  as `local` mode or no `origin`, an absent `gh` read as `unknown` rather
  than `none`, and "no CI" was found by waiting — the queue-end poll held
  `checks=none` for its grace at every queue end, then reported that no CI
  ran, failure-shaped, about a project that never had any. A consumer
  pushing to a non-GitHub remote under `auto-merge` got a permanent `aide
  env` refusal for a `gh` it would never use (issue #355). They are facts
  about the project and its process, not the machine, so they sit in the
  committed `aide.toml` beside the mode; the defaults are the behaviour
  before the keys existed.
- **Why there is no push-triggered `ci` value.** The queue end reads CI from
  the queue PR's head commit and nowhere else, so a workflow that runs on a
  push but not on the PR has nothing the step could wait on; a value naming
  it would promise a reading the engine never makes.
- **Why `pr` with no forge is an error, and `auto-merge` is not.** Under
  `pr` the merge stops for a person to open the item's PR, which needs a
  forge to open it on; with none the mode has no meaning. `auto-merge` lands
  items itself and only pushes, which any remote takes.
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
- **Why a red run is compared with the base.** The gate refused on any red
  test anywhere, so one failure the item never touched blocked every item
  behind it. A consumer on engine 1.38.0 had an item pass all sixteen of its
  acceptance criteria with every changed file authorised, and the merge still
  exited 1 on nine failures proven identical at the merge-base — stale
  environment-gated capability rows and an unrelated adapter gap. A second
  time, a test pinning an inbox entry's checkbox went red when a triage commit
  on `main` ticked it, and every item merging into the queue branch was
  blocked until a fix landed. The only override was `--no-test`, which drops
  the gate rather than scoping it (issue #275).
- **Why in place, not in a separate worktree.** The post-merge run saw this
  checkout's untracked and ignored inputs — data, a built extension, the
  venv. A fresh worktree lacks them, so the base fails *more* there, and every
  extra base failure is a regression the subset rule would admit as
  inherited. The base is only run when the merge is red, so a green merge
  costs nothing extra.
- **Why a subset, and why automatic.** A
  `--accept-inherited <nodeid>…` flag was proposed and not taken: the subset
  is a fact the two runs establish, and a flag would stop an unattended run
  for a person to type what the engine already knows. A key to switch the
  comparison off was not taken either — it would switch off the one check that
  separates an item's regression from its base's. An item that renames an
  inherited failing test, or fails one differently, is still refused, since
  identity is by test id: the rule errs towards refusing.
- **Why the engine writes the inbox entry.** An admitted failure that leaves
  no trace makes a red base look normal to the next item over it. The verb
  holding the ids writes one line, and skips ids an open entry already names,
  so a queue landing ten items over the same red base carries one entry and
  not ten; the role that ran the merge writing its own would be the same
  finding twice.
- **Why only pytest.** Comparison needs a report naming each failure, and a
  test command is otherwise free-form; guessing failure identity from another
  runner's output would admit on a misreading. An order-dependent option
  (`-x`, `--maxfail`, `--lf`, `--ff`, `--sw`) makes the set a property of the
  run, and an exit other than "tests failed" means the report is not the whole
  suite — both would compare two partial pictures. Order set in the project's
  own configuration — a random-order plugin enabled by default, say — is not
  visible in the command, and is not detected: such a suite's failure set is
  as much the run's as the tree's, and a comparison over it can admit an
  order-sensitive regression by coincidence.
- **Why the base run is stored.** A retried merge — after a fix commit, or a
  failed push — would otherwise re-run the base it has already run. Results
  are kept under git's own directory, keyed by tree and exact command, never
  committed, and pruned after seven days; a run over a tree with tracked
  changes, or one that leaves a tracked change behind, is never stored, since
  it belongs to no tree — a base run's included, so a suite that rewrites a
  tracked file re-runs its base on every retry.
- **Why a validated tree is not run twice.** Under `auto-merge` validation ran
  the whole suite on the claim branch and the merge ran it again, and when the
  base had not moved the merge is a fast-forward: the second run was over a
  byte-identical tree and could prove nothing the first had not. It was the
  loop's second long wait, which on a runtime with a short idle cache also
  costs the waiting agent its context (issues #274, #275). One store serves
  both reads, the base run and the validated run, so there is one record of
  what ran where.
- **Why the progress document may differ.** Validation writes its verdict
  after its suite run — `progress set in-review` and each attested criterion
  are commits on the claim branch — so a rule demanding the identical tree
  would never be met by the loop it was built for. The progress document is
  the one file allowed to differ because the merge's own `aide check` reads it
  in full beside the gate, and what validation writes there is the engine's
  bookkeeping. Anything else, `insights.md` included, forces a run: a
  consumer's test has already gone red on an inbox checkbox (above).
- **Why the claim branch and its commit, not only the tree.** A tree key alone
  would let a run recorded for an earlier item, or on the base before this
  claim existed, stand for this one whenever the trees happened to agree. The
  recorded branch and a commit the tip contains tie the run to this claim, so
  a reused result is always one this item's own validation produced.
- **Why tracked changes refuse and untracked files do not.** A run over a tree
  with a tracked change is a run of no commit, so it is neither recorded nor
  taken. Untracked and ignored inputs — data, a built extension, the venv — are
  not in the tree at all, so a run is taken only in the checkout that
  recorded it: there the validated run and the merge saw the same ones, and
  the base run's rationale (above) is why the merge does not try to see fewer.
- **Why a CI gate can decay silently.** With no PR a PR-context scope job
  either never triggers, or triggers on a branch whose name yields no item
  number and correctly skips — so a gate can decay from a mode change alone,
  long after it was correctly built.
- **Why base inference is narrow.** Inferring a base from an arbitrary
  checked-out branch would silently retarget a merge.
- **Why a claim branch stands for its recorded base.** A validator ending
  PASS (awaiting gate-…) leaves its item 🔍 on its claim branch with HEAD
  still there, and a person approves that gate there, so the next claim is
  routinely run from one. Read as an arbitrary branch it fell back to
  `main_branch`, and the next item of a queue was branched off and merged
  into `main` instead of the queue branch (issue #433). One with no record is
  refused rather than read as `main_branch`, the guess that misrouted it.
- **Why the record is local.** The base is a fact about this checkout's
  branching, not about the project.
- **Why a base the loop writes to must be a local branch.** `git switch` to a
  tag, a commit or a remote-tracking ref would detach HEAD, and a merge into a
  detached HEAD updates no branch while still reporting success.
- **Why a measuring verb takes any ref.** The rule once read "a base is always
  a local branch", for every verb, while `scope`, `status` and `gc` passed
  `--base` through verbatim (issue #407). A consumer's PR-context scope job
  runs `aide scope NNN --base origin/<base>` on a detached `pull_request`
  checkout with no local base branch — the case the CI paragraph above tells
  such a job to handle itself. Refusing a non-local base everywhere was
  rejected: it would turn every item PR red there to protect a diff that
  writes nothing. `gc --merged` keeps its narrower reading because it deletes
  on the answer (issue #403).
- **Why a cap, and why one stack.** Stacked queues de-serialise *review*:
  the loop goes on building while earlier batches wait for a person. Parallel
  stacks off `main_branch` would bring back every contention point of
  parallel *execution* — item numbers, `progress.md` and `insights.md`
  conflicts, `claim_scope` — while one stack keeps numbering and document
  edits linear. The cap bounds what a rejected lower costs: at worst
  `max_open_queues − 1` queues built on it (#258). It is enforced by the verb
  that creates the branch, so an unattended run cannot pass it by misreading
  prose (#302).
- **Why "unmerged" is restack's judgement.** Two readings of "landed" would
  let `start` count a branch `restack` has already handed on, or the
  reverse. A branch git cannot judge is counted: guessing it landed would let
  the stack grow past the cap.
- **Why a stack merges and never rebases.** Rebasing an upper branch onto its
  moved lower rewrites commits its open PR already shows, and publishing that
  takes a force-push — a §3 stop in an unattended run. A merge only adds
  commits, so a plain push publishes it (issue #301).
- **Why landed is judged from git.** Pull-request state needs the host's CLI,
  which is best effort and absent in `local` mode. That a branch's work is in
  `main_branch` is a fact git establishes from content — the oracle `gc`
  already trusts before a force-delete. That a PR was closed unmerged is not:
  the branch simply stays, so the caller that can read PRs checks, and the
  verb does not guess.
- **Why runnable and awaiting review are two facts.** At a cap of 1 an open
  queue PR meant the loop was blocked; above it the loop builds while PRs
  wait, so one "blocked" state misreports both halves (#258). The roadmap
  command's stop table and a scheduler polling for readiness (#257) would
  each define "blocked" in their own prose and drift, so the engine derives
  it once and both read it (#303). "Could not look" stays apart from "no PR"
  because a caller that reads a missing `gh` as an empty review queue
  relaunches into a blocked repo.
- **Why orphaning is reported by `status`, not `restack`.** `restack` reads
  git only, and a PR closed without merging leaves nothing git can see. The
  forge is asked in the one place that reads it best effort already, and a
  lower git says landed is never called orphaned, whatever its PR says —
  content stays git's to judge.
- **Why these merge styles may land a branch.** Measured in the fixture:
  after a squash merge `main_branch` holds the bottom's changes as one commit
  while the branch above holds the originals, so git's own merge base is the
  stack's fork point and the bottom's changes meet themselves. That merge is
  clean when the upper touched nothing near them and conflicts when it did —
  and queues tick adjacent lines of `progress.md`. The landed tip is an
  ancestor of the upper and its content is in `main_branch`, so as the merge
  base it yields `main_branch` plus the upper's own changes, cleanly; a
  merge-commit rule for the human was the alternative, and is not needed.
- **Why the start commit is recorded.** A branch with no commits of its own
  has nothing `main_branch` lacks, which the content check reads as landed;
  handing the branch above it to `main_branch` would then drop the lower's
  later commits from the stack. A branch `main_branch` was fast-forwarded to —
  how `local` mode lands a linear queue — has the same shape in git, so the
  first review round of #301 found such a landing reported as "consistent"
  and never handed on. Only where the branch started tells the two apart; above
  another branch that branch's tip says it, so only a bottom with no record is
  undecidable, and the run stops rather than guess either way.
- **Why each branch's own landing is judged.** Asking only whether the branch
  below had landed missed a middle queue fast-forwarded onto `main_branch`
  above an empty, open bottom — "consistent", with the top queue never handed
  `main_branch` (the second review round of #301). A branch that landed holds
  everything beneath it that it contains, so the branch above is owed
  `main_branch` whatever the bottom is; the open bottom gets nothing, since
  `main_branch` already holds all of it, and with nothing stacked on it any
  more it no longer holds a stack.
- **Why no commit hook runs and signing is honoured.** The merge-tree path
  writes its commit with `commit-tree`, which runs no hook and ignores
  `commit.gpgSign`; the fallback's `git merge` did both. One behaviour on
  every git version: no hook on either (a restack adds no content of its own
  to check), and a signature wherever the repository asks for one, whose
  failure stops the run.
- **Why no record means no stack.** The records are local git config, and
  queue branches from before stacking sit beside a stack; chaining them by
  number would merge unrelated queues. `--base` records one, bottom up.
- **Why a reopened lower queue is built on its own branch.** Built on the
  upper one, the fix lands in the PR that did not ask for it, and the lower
  queue's PR could be merged with the item still 📋 in it.
- **Why the engine owns the queue PR.** `gh pr create` and `gh pr ready` can
  touch any pull request, so they stay behind a person's approval, and an
  unattended run could neither open its queue's draft PR nor start CI by
  marking it ready (issue #330). A verb that can touch only the queue's own
  PR is narrow enough to pre-approve, the way `aide claim` makes its own
  push. CI state comes from `status` for the same reason `pr=` does: the
  command and the engine must not disagree about the forge.
