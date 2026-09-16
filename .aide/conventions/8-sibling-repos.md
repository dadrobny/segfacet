## 8. Reaching into another repository

Governs work inside a repository that is not the working directory's — a
declared sibling. Every role and a person too act on it; the always-on page
points here, and a runtime may automate the pointer.

A project may legitimately span more than one repo — a library and a sibling
programme repo, or a consumer and the framework clone it updates from. `aide.toml`
never records where those live; `[framework] local_path` and `[hygiene] extra_repos`
in the personal, gitignored `.aide/loop/loop.local.toml` do (§3, and the file's own
comments).

Acting on a declared sibling has approved command shapes and needs no `cd`:
git via a repo-override flag on the declared path (§3's carve-out), and the
`aide` CLI via the sibling's own install with an explicit root —
`python <sibling>/.aide/scripts/aide.py --repo <sibling> <cmd>` (§3, which
also says why it is the sibling's install and why `--repo` is not optional).

**A repository's own instructions bind for work inside it.** A runtime loads
instruction files for the working directory's repo only; a declared sibling —
the framework clone included — gets nothing, and nothing announces the gap. So
read that repo's instruction file first, before editing, committing to, or
otherwise acting on a repo that is not the working directory's. Where two
repos' rules disagree about a file, the repo that owns the file wins. The rule
holds for a person too, and for an interactive session with no agent spec in
play.

**A runtime may automate this.** Where one can inject context on demand, an
adapter should **point** a session at a declared sibling's instruction file the
first time it touches a path inside it — lazily, so a session that never reaches
across pays nothing. A pointer and not the file's contents. That is a delivery
mechanism and therefore adapter-local (`ADAPTER-SPEC.md` §8); the rule above is
what binds when a runtime has no such mechanism.

### Rationale

- **Why a rule and not good manners.** The failure is silent and the cost is
  real. The loading stated above is the whole of the runtime's rule — the
  working directory's root file, and any subdirectory files as it reaches into
  them; *"declared as an additional working directory"* does not imply
  *"instructions loaded"*. So an agent editing a sibling is
  working without rules that were written down, that it would have followed,
  and whose absence nothing announces. What is lost is exactly the material
  that cannot be inferred from the code — a versioning rule enforced by that
  repo's own suite, a merge policy, a path convention that looks like a typo
  and is not.
- **The case that hits hardest** is the framework's own maintenance: the
  documented update workflow edits the framework clone from a consumer's
  checkout, which is precisely a session with the framework's instructions
  unloaded.
- **Why a pointer, not the contents.** The reader then opens the file as it is
  *now*, which matters most in the case that motivates the rule, where the
  session is editing that very file. A runtime without the mechanism falls
  back on the rule being read — the same graceful degradation §3's hygiene
  guard already relies on.
