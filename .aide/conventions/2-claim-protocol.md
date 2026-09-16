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
   reaches, and that has no existing `aide/NNN-*` branch. The pick is
   mechanism the CLI owns, so `-h` is where it is stated; what matters here is
   that a role never chooses an item itself. With `loop.claim_scope = "all-open"` in
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
push fail the same way.

**`none left` means the ground checked was empty, and nothing else.** A queue
still open while nothing in it is offerable is a different answer, and `claim`
gives the reason per item — an unresolved gate, a claim already in flight, a
dependency not landed, an unpublished claim — or names the human-gates row it
cannot read, which holds every item (§1 → human gates). The first three are
ordinary and exit 0; the last two are defects and exit non-zero.

One person (or one loop) owns an item at a time. Abandoning an item means
deleting its remote branch so the item returns to the pool; `aide check` flags a
claim branch whose item is already ✅ (stale claim), and `aide gc` deletes such
branches — local and remote — deterministically (dry-run by default, `--yes` to
act; `--merged` also collects branches already merged into main).

**`gc` asks git, not the document.** A ✅ item whose branch still carries
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
- **Why `gc` asks git.** A ✅ is a claim made by a document that agents and
  humans both edit, and the action it triggers is `git branch -D` plus a remote
  delete — unrecoverable on a plain git host. So on the ✅ ground `gc` deletes
  a branch only when `git merge-tree --write-tree` says merging it into the
  base would change nothing: the merge-tree question is the content question,
  which (unlike `git branch --merged`) stays correct across a squash merge,
  and which also strengthens `--merged`. `merge-tree --write-tree` needs
  git ≥ 2.38, and on older git the ✅ ground refuses rather than falling back
  to a weaker test — old git is always *more* conservative, never less.
- **Why the preview is exact.** A dry run a human is asked to approve must not
  overstate, so every skip — checked out, unlanded, git too old — is decided
  before anything is printed and shown on both paths.
