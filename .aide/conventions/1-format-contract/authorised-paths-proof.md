### Proving an item's scope — the diff, the queue check, and what the suite may not claim

The other half of §1 → `authorised-paths.md`: the declaration is the
spec-author's, and this is every role that *proves* it. The validator runs
`aide scope` on the claim branch, the spec-reviewer reads one queue's
declarations against each other before any item is built, and the role writing
a test reads the declaration to tell a diff-time scope claim — which belongs on
the branch — from an assertion the suite may keep.

**Scope is proved by the diff, not by a hash.** The declaration is checked
against the branch's changed files:

```
python .aide/scripts/aide.py scope [NNN] [--base <ref>]
```

It diffs against the **merge-base with the item's base** (`--base`, else the
recorded base, else `main_branch` — §4; `scope -h` says how the item and the
base are resolved). On stacked work the base is the **queue branch**, not
`main`. Exit `0` in scope · `1` something changed outside it · `2` could not
check. A spec with no section cannot be read as an unconstrained one.

A path declared under **Asserts against** and then changed is reported
separately from an unauthorised one: it means an assertion in this very item now
pins state the item moved. The three always-authorised paths (§1 → authorised
paths) are in scope on every item without appearing in either list.

**One queue's specs are checked against each other before any is built**, in the
window `/aide-spec-queue` creates — N specs on one branch, every cross-item
conflict still cheap to fix:

```
python .aide/scripts/aide.py check --queue NNN [--report <path>]
```

It reports the collisions between two declarations and a dependency graph that
cannot be satisfied, and discounts a pair that a spent item or a declared
dependency already settles — `check -h` states the findings and how far each
discount reaches. `--report` writes them as JSON for a reviewer pass to pick
up. The remedies the message offers are the spec author's, and
§1 → authorised paths states them.

A test that hashes some *other* file's bytes against a hardcoded literal to
prove this item did not touch it — a **scope fence** — is a fallback for cases
with no diff to check against, not the norm:

- **It inverts on the next legitimate edit.** The moment a later item is
  authorised to touch the pinned file, the earlier item's test goes red for
  doing exactly what the loop asked. Declare the file under **Asserts against**
  instead, so the conflict surfaces at spec time rather than at first pytest.
- **Never fence a whole tree.** A digest over `src/**` collides with any future
  edit anywhere beneath it. Fence per file, or exclude the paths later items
  name.
- **Never walk untracked or ignored paths.** A tree walk that picks up
  `__pycache__/*.pyc` hashes bytes that embed source mtimes: the "pin" is not
  reproducible even against an unchanged tree.
- **It is platform-fragile, in the two ways §6 rules on.** A digest takes path
  components and committed bytes — exactly what the separator rule and the
  line-ending pin govern — so a fence is subject to both, and §6 states them
  once, for the role that writes the test.

**Re-pinning.** When a later item is deliberately authorised to change a file an
earlier item pinned, update the earlier constant in the same commit, with a
comment naming the authorising item — do not delete the assertion silently and
do not leave it red. Distinguish the two things a pin can mean: a *diff-time
scope claim* ("item N did not touch X") belongs in **Asserts against** and
should be retired when its item merges, while an *artifact-integrity invariant*
("this released artifact must never change silently") is legitimate and durable
— but then it belongs in a test named for the artifact, living beside it, not
inside an unrelated item's regression module under a `_PRE_NNN_` name.

**A diff-time scope claim is never a suite assertion.** It is decided on the
branch, by `aide scope`, against the declaration — which is what these two
sections fix. The rest of the rule is §6's, stated there once for the role that
writes the test: the two shapes written instead, what `aide check` warns on, why
neither a skip guard nor a base taken from the verb repairs them, and the one
base computation that is deliberately not reported.

**Auditing fences goes by shape, not by name.** The distinguishing feature is a
digest compared against a **hardcoded literal**; a digest compared against a
value computed in the same run is a determinism check and must stay.

#### Rationale

- **Why a queue branch is skipped.** Per-item scope is checked on each claim
  branch as it merges, and a queue branch legitimately aggregates many items'
  lists — there is no one declaration to prove.
- **Why the derived base prefers `origin/`.** A local ref on a checkout sitting
  behind the work has itself as the merge-base, so every file the earlier
  items touched would be reported against this item's spec; and diffing a
  stacked item against `main` would report every sibling already merged into
  the queue branch. Whether the per-item check is ever reachable from CI, as
  opposed to only from the validator in-loop, depends on `git.mode` (§4).
- **Why fences are a fallback.** Each of the four failure modes above has cost
  a real CI break; §6's Rationale records what the suite-side shapes of a
  diff-time claim cost, since that is where those shapes are ruled on.
- **Why the discounts.** A merged item's claim can neither be harmed by a
  later writer nor harm one, and an excluded item is never offered. The
  dependency discount is the whole shape of a stage-validation item, which
  exists to pin what its stage produced — built against a tree that already
  holds the edit, so the edit landing cannot break its pin; an undeclared
  ordering is exactly what the check is for, so a pair without one keeps the
  error. A deferred blocker's edit is dormant, not spent, and still
  ahead of the pin, so it earns no exemption — and deferred items stay in the
  path comparisons because a conflict with one is worth surfacing while
  re-planning is cheap. A cycle whose members all merged proved its order
  satisfiable.
- **Why fences are audited by shape.** A sweep for constants named after item
  numbers misses every fence named anything else.
