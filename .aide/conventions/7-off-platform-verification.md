## 7. Verify on a platform this loop never runs on

Governs what a role does with a pushed branch's CI result, and how a red leg
is read. Its readers are the queue-end step, which reads CI once the queue's
PR is marked ready, and the builder dispatched with the CI findings it
reports; §6 covers the leg a role can see, this section the one it cannot.

**No role in this loop
sees a non-Linux checkout, a different working directory, or real CI status**,
so the honest response is to look at the one gate that does:

- Once work is pushed, **check the real CI result** rather than inferring it
  from a green local suite. Report what CI actually said, including "no CI is
  configured here" or "it had not finished" — never let a local pass stand in
  for a platform the loop cannot reach.
- When CI is red on a leg that passed locally, treat it as a **portability
  finding first** (§6), not a flake, until the log says otherwise.
- A red check on the queue's PR is fixed through **the item whose change it
  traces to**: that item is reopened, rebuilt within its own spec and
  authorised paths, validated and merged back, and CI runs again once the
  queue is exhausted. The round, its cap and what traces to no item are the
  queue-end step's (`.aide/README.md`).

### Rationale

- **Why §6 is not enough.** Test hygiene reduces the odds; it does not close
  the gap.
- **Why a portability finding first.** Every recorded instance of a red leg
  that passed locally looked like a content problem and was a platform one.
- **Why the queue end, not the validator.** Until 2.20.2 the validator read
  CI per item, and no CI run of the item's work could exist when it did:
  under `auto-merge` nothing pushes the item's commits before the merge that
  follows validation, under `pr` the claim branch is pushed only after a
  PASS, and under `local` nothing is pushed at all. The check reported
  nothing or a stale run, at the cost of a step on every item (issue #329).
- **Why the item that introduced it.** A fix is judged against the spec of
  the item whose change broke CI, and reopening keeps that bound while
  reusing claim, the item runner, the validator, the merge gate and the
  ledger's second row unchanged. A new verb adding a fix item to the queue
  was rejected: it needs a spec, authorised paths and a number of its own,
  and loses the one bound that matters (issue #332).
- **Why the PR goes back to draft.** Each CI run costs minutes, and a ready
  PR re-runs on every push, so a round fixes all of its findings before the
  push that re-runs CI. Holding `aide merge`'s push while a reopened item is
  open was rejected: it works whatever the CI trigger, but changes `aide
  merge` and leaves merged, unpushed work in one checkout for the length of
  the round.
- **Why the round is stamped, not derived.** A merge flips an icon and
  writes no trail line, so whether one item merged back before another was
  reopened — what separates two rounds from one — is not on record
  afterwards; the engine writes the round when it writes the reopening, and
  a runner never counts it across sessions.
- **Why the gap closes at the merge back, not on green.** Only CI knows the
  check is green again, but a tick made after reading it is a commit of its
  own, and pushing it to the ready PR costs one more CI run over a tree
  changed in `insights.md` alone. `aide merge` ticks the reopening's gap in
  the commit it already makes; a check still red reopens the item again,
  and that reopening captures a gap of its own.
