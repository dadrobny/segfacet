### Status icons (the only six)

Governs the vocabulary every status cell, stage header and deliverable bullet
carries, and how the parsers rank and read it. Every role that writes a status
document uses it; ✅ is the CLI's to write.

| Icon | Meaning | Rank |
|------|---------|------|
| 📋 | Planned | 0 |
| 🚧 | In Progress | 3 |
| 🔍 | In Review | 4 |
| ✅ | Complete | 5 |
| ⏸️ | Deferred | 2 |
| ❌ | Excluded | 1 |

Rank is used when one item is referenced on several lines: the most-advanced
status wins.

**✅ means merged — in every `git.mode`.** It is written by `aide merge` when
the merge actually happens, not by an agent ahead of one. 🔍 is the state
between: the work is pushed and awaiting a human's merge. The mode never
changes what a status asserts.

A 🔍 item **holds its stage at 🚧** (an open PR has not shipped) and **holds its
queue open**, and its claim branch is live, not stale. Because in `pr` mode
nothing inside the loop ever observes the merge, `aide sync` and `aide status`
name any 🔍 item whose work has since landed in the base and print the `aide
progress set NNN done` that closes it — **that command is what closes a 🔍
item**, never an agent reading the merge off the forge.

A ⏸️ item **is work postponed, not work done**: it never lets its stage reach
✅, and a stage whose only open bullets are ⏸️ reads ⏸️. `aide progress set
NNN deferred --reason …` writes it, and any forward `aide progress set`
resumes it (§1 → `progress.md`).

**Structural positions only.** The parsers read icons *only* at structural
positions: a table row's **Status (last) cell**, a stage header's **trailing**
`— <icon>`, and the **leading** icon of a deliverable bullet. An icon anywhere
else — prose, mid-bullet, a title — is plain text and is never read as status,
so authors need not avoid the icon vocabulary in free text. `aide check` still
*warns* on an icon in a heading anywhere but its trailing slot, in the
status-bearing documents (`progress.md`, queue files), where a reader could
take it for the header's status; other documents are not scanned.

#### Rationale

- **Why ✅ is mode-independent.** It used to mean two different things depending
  on the mode — merged under `auto-merge`, *pushed and awaiting review* under
  `pr` — while everything downstream read it as "done", including `aide gc`,
  whose default ground is "the item is ✅" and whose action is `git branch -D`
  plus a remote delete. The exhaustion sweep therefore offered to delete the
  head branch of an open PR, and the line a human was asked to approve read
  like confirmation. A run must be stable under either mode, so 🔍 was added
  and ✅ narrowed to the merge itself.
- **Why ⏸️ became a stage state.** Until issue #281 the rollup never
  produced ⏸️, so a stage an owner had deferred read 📋 or 🚧 and could not be
  told from one nobody had started, or one in flight. It is computed now,
  from bullets a verb writes with a reason.
- **Why the landed-🔍 check is a content check.** `sync` and `status` use the
  same merge-tree comparison `gc` uses, so closing a 🔍 item needs no forge
  call that could silently degrade to "no open PRs found".
