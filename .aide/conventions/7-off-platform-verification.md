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

### Rationale

- **Why §6 is not enough.** Test hygiene reduces the odds; it does not close
  the gap.
- **Why a portability finding first.** Every recorded instance of a red leg
  that passed locally looked like a content problem and was a platform one.
