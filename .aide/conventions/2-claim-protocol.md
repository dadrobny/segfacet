## 2. Claim protocol — how "in progress" is signalled

Governs how one run learns that another has taken an item, and how a spent
claim is collected. `aide claim`, `aide queue start` and `aide gc` act on it;
a role picking or abandoning an item goes through them and is pointed here.

The shared "this item is taken" signal is the **pushed `<branch_prefix>NNN-*`
branch** (config `git.branch_prefix`, default `aide/`) — not `progress.md`'s
`🚧`, which lives on a feature branch. `aide claim` owns this:

1. `git fetch --all --prune`; list remote `aide/*` branches.
2. Read the live queue (§1 → `queue-NNN.md`) + `progress.md`; pick the item
   the rule in `aide claim -h` names — the **first** 📋 item the queue lists
   whose dependencies have all left the way, that no unresolved human gate
   reaches, and that has no existing `aide/NNN-*` branch. **Withdrawn work is
   never offered**: a dropped item is ❌, not 📋, and an item whose every
   bullet sits in a stage whose summary row is ❌ is skipped and named. The
   pick is mechanism the CLI owns, so `-h` is where it is stated; what matters
   here is that a role never chooses an item itself. With `loop.claim_scope = "all-open"` in
   `aide.toml`, claiming scans **every** open queue in number order instead —
   opt-in, because the one-queue scope is also the human-checkpoint boundary.
3. Create and push `aide/NNN-short-name` (push depends on `git.mode`; `local`
   mode does not push and so has no multi-machine claim signal).

**The two branch shapes that are not claims** — `<prefix>queue-NNN` (a queue is
planned and run on it) and `<prefix>specs-queue-NNN` (its specs are authored on
it) — are created by `aide queue start NNN [--specs]`, never typed by hand. The
engine both *constructs* and *recognises* all three shapes from one definition,
so a name it produces is a name it can parse; `aide claim` infers an item's base
only from a **recognised** queue branch, so a hand-typed name that misses the
shape sends every item's merge to `main_branch` instead of the queue branch,
silently. `queue start` also records the branch's own base, which `claim` alone
could not do.

**A push that does not land is not a claim.** The signal is the branch *on
origin*, so `claim` fails when it cannot publish one — as a sentence naming the
branch, the remote and git's own words, never a traceback — and leaves the local
branch for you to push or delete. Off `local` mode a claim branch origin has
never seen is reported as an **unpublished claim** by `claim`, `status` and
`check`, never counted as work in flight. `queue start` and `merge`'s `pr`-mode
push fail the same way. With no remote named `origin` at all there is nothing
to publish to, and each of them refuses before it changes anything (§4).

**A branch origin deleted is not one origin never saw.** A branch whose
upstream `origin/<branch>` is gone was published, and is never advised a push
— that would recreate a branch deleted on purpose. The same three verbs name it
as **stale** when everything on it is already in its base or `main_branch`
(`aide gc --merged` deletes it, a queue branch only against `main_branch`),
and otherwise as work **not found** there.
Not found is what was measured, not that the work never landed: a squash
merge the base has since changed over the same lines, or any squash merge
under git older than 2.38, reads the same way. So check whether its work merged
before deleting it, and land its work first if it did not. Either kind on a
claim branch holds its item without being work in flight, so `claim` exits
non-zero on it as on an unpublished claim.

**`none left` means the ground checked was empty, and nothing else.** A queue
still open while nothing in it is offerable is a different answer, and `claim`
gives the reason per item — an unresolved gate, a claim already in flight, a
dependency not landed, a withdrawn stage, an unpublished or deleted claim — or
names the human-gates row it cannot read, which holds every item (§1 → human
gates). The first four are ordinary and exit 0; the last two are defects and
exit non-zero.

One person (or one loop) owns an item at a time. Abandoning an item means
deleting its remote branch so the item returns to the pool; `aide check` flags a
claim branch whose item is already ✅ or ❌ (stale claim, the ❌ ground below),
and `aide gc` deletes such branches — local and remote — deterministically (dry-run by default, `--yes` to
act; `--merged` also collects branches already merged into the base, and a
queue branch only when that base is `main_branch`).

**A ❌ item's claim is spent as a ✅ one is.** An item dropped by its own
bullets, or a 📋 one whose every bullet sits in a withdrawn stage, will never
be merged — `aide merge` refuses both — so its claim branch is stale on the
same ground: `check` and `status` name it, and `gc` collects it. A 🚧 or ⏸️
item in a withdrawn stage is live or owner-held work, not stale until its
owner drops it (`aide progress set NNN dropped`), and `merge` takes it. A 🔍
item's branch is never stale, however its stage is marked — it is an open
PR's head.

**`gc` asks git, not the document.** A ✅ or ❌ item whose branch still carries
unlanded content is **skipped** with the base named; `--abandon` deletes it
anyway, for the genuinely abandoned claim. **The preview is the set `--yes`
acts on** (`gc -h` says what it asks git, and what it refuses).

### Rationale

- **Why the branch and not the document.** A `🚧` edit to `progress.md` is
  invisible on `main` until merge, so it cannot be the mid-flight signal
  between concurrent runs.
- **Why an unpublished claim is an error.** It holds an item on evidence no
  other checkout can see, and a run that reads it as exhaustion finishes
  reporting success over work it never started.
- **Why the upstream decides, and not ancestry.** The engine reported every
  branch origin lacked as unpublished and advised `git push -u` for a queue
  branch its PR had merged and hosting had deleted (issue #364). Every engine
  push sets the upstream, so a gone upstream is git's own record that a push
  landed. Ancestry alone cannot be the test: a claim whose push just failed
  sits at its base's tip, already "in" main, and is the half-claim above. A
  landed claim branch still exits non-zero because an empty one is also what an
  abandoned claim leaves, and only a person knows whether to tick the item or
  release it.
- **Why "not found" and never "deleted before it landed".** The first cut
  said the latter, and review of it (PR #367) reproduced landed work reading
  so: squash-merged, then `main` changed the same lines, so `merge-tree`
  conflicts and the content question cannot answer. Hosting squash merges are
  common, so the verdict would have been a frequent false alarm. No cheap
  probe closes the gap — patch-id matching breaks on a squash whose context
  moved or whose conflicts were resolved on the host — so the report states
  the measurement and sends a person to the PR. It stays louder than the
  stale case because the other reading is that this checkout holds the only
  copy of the work.
- **Why `gc` asks git.** A ✅ is a claim made by a document that agents and
  humans both edit, and the action it triggers is `git branch -D` plus a remote
  delete — unrecoverable on a plain git host. So on the ✅ ground `gc` deletes
  a branch only when `git merge-tree --write-tree` says merging it into the
  base would change nothing: the merge-tree question is the content question,
  which (unlike `git branch --merged`) stays correct across a squash merge,
  and which also strengthens `--merged`. `merge-tree --write-tree` needs
  git ≥ 2.38, and on older git the ✅ ground refuses rather than falling back
  to a weaker test — old git is always *more* conservative, never less.
- **Why a queue branch needs `main_branch` as the base.** On a stack of
  queue branches each one below the base is an ancestor of it, so git calls
  every one merged into it — into its successor, not into `main_branch`.
  Collected on that answer, `gc --merged --base <queue branch> --yes` deleted
  them on origin, and deleting a PR's head branch closes the PR, unreviewed
  (issue #403). A claim branch merged into a queue base is not that shape: it
  landed where it was meant to, and the queue branch's PR carries its work. An
  open-PR check was the rejected alternative: it needs a forge, and `local`
  mode and `forge = "none"` have none.
- **Why ❌ is a stale ground, and not only ✅.** 2.34.0 gave ❌ two routes —
  `aide progress set NNN dropped` for an item, a ❌ summary row for a stage —
  and `merge` began refusing a ❌ item, but the stale ground stayed ✅ alone:
  a 🚧 item dropped at the round cap kept its claim branch with nothing
  pointing at it, and `claim` still handed out a withdrawn stage's 📋 items
  one by one until each was dropped (issue #387). The ❌ ground goes through
  the same oracle as the ✅ one, so a dropped item's branch carrying work is
  kept until `--abandon` says to discard it; the document's ❌ decides only
  that the branch is a candidate, never that its work may go. A withdrawn
  stage spends only its 📋 items: a 🚧 or ⏸️ one there is work someone is
  doing or holding, and reading the stage's ❌ as their drop would let `gc`
  take a fresh claim branch from under its builder — the owner's own drop is
  the signal. A builder mid-run whose stage is withdrawn on `main` still sees
  its item 📋 there, so `check` names its branch stale; that is accepted,
  because `gc` asks git first and takes the branch only once its work has
  landed.
- **Why `merge` refuses only the 📋 item of a withdrawn stage.** Issue #389:
  `merge` read no summary row, so an item `claim` would no longer offer
  could still be ticked ✅, undoing the withdrawal. The refusal takes the
  stale ground's line, not the stage's: a 🚧 item there is work someone is
  doing, and refusing it would discard a build its owner has not dropped.
  The builder records 🚧 on its claim branch and the base never sees it
  until the merge, so `merge` reads the branch's copy for the item's status
  beside the working tree's and the base's, and refuses only when none of
  them shows it started.
- **Why the preview is exact.** A dry run a human is asked to approve must not
  overstate, so every skip — checked out, unlanded, git too old — is decided
  before anything is printed and shown on both paths.
