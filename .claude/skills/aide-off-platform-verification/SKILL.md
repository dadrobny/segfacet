---
name: aide-off-platform-verification
description: Load before reading a pushed branch's CI result — no role in this loop sees a non-Linux checkout or real CI status, so look at the gate that does, and read a red leg as portability (conventions §7).
user-invocable: false
paths:
  - "**/.github/workflows/*.yml"
---

<!-- generated-from: .aide/conventions/7-off-platform-verification.md
     Everything below the note is that file, down to its `Rationale` heading,
     written here by `install.py` at install time (issue #109). There is no
     hand-written copy of §7 to drift, so this file declares no `pins`
     block: that mechanism guards a restatement, and this is not one. Edit
     the section. -->

**Delivery, not a second source of truth.** What follows is
`.aide/conventions.md` §7 — `.aide/conventions/7-off-platform-verification.md`,
down to its `Rationale` heading — rendered here verbatim at install time, so it
cannot say anything the engine does not. The reasoning behind each rule is in
the section below that heading; `.aide/conventions.md` resolves any `§N`.

## 7. Verify on a platform this loop never runs on

Governs what a role does with a pushed branch's CI result, and how a red leg
is read. The validator acts on it once its push exists; §6 covers the leg it
can see, this section the one it cannot.

**No role in this loop
sees a non-Linux checkout, a different working directory, or real CI status**,
so the honest response is to look at the one gate that does:

- Once work is pushed, **check the real CI result** rather than inferring it
  from a green local suite. Report what CI actually said, including "no CI is
  configured here" or "it had not finished" — never let a local pass stand in
  for a platform the loop cannot reach.
- When CI is red on a leg that passed locally, treat it as a **portability
  finding first** (§6), not a flake, until the log says otherwise.
