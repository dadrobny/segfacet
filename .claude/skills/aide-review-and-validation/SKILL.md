---
name: aide-review-and-validation
description: Load before reading an item's diff to judge it — what validation answers, what review answers, why neither covers for the other, and how a finding triages (conventions §9).
user-invocable: false
paths:
  - "**/REVIEW.md"
---

<!-- generated-from: .aide/conventions/9-review-and-validation.md
     Everything below the note is that file, down to its `Rationale` heading,
     written here by `install.py` at install time (issue #109). There is no
     hand-written copy of §9 to drift, so this file declares no `pins`
     block: that mechanism guards a restatement, and this is not one. Edit
     the section. -->

**Delivery, not a second source of truth.** What follows is
`.aide/conventions.md` §9 — `.aide/conventions/9-review-and-validation.md`, down
to its `Rationale` heading — rendered here verbatim at install time, so it
cannot say anything the engine does not. The reasoning behind each rule is in
the section below that heading; `.aide/conventions.md` resolves any `§N`.

## 9. Review and validation (two reads, one diff)

Runtime-general, like §3 and §6. An adapter **delivers** this section to the
roles that perform either read rather than pointing at it.

**Validation and review answer different questions.** Validation asks *does
this branch meet the Acceptance Criteria of the spec it was built from* — the
suite is green, every AC has a test that measures it, the diff is inside the
authorised paths, the Assumptions still hold. Every term is measured against
the item spec, the verdict is PASS/FAIL, and it **gates the merge**. Review
asks *is this code correct, and does it fit the codebase* — it reads the diff
adversarially for what the spec never anticipated, and it **produces findings**,
not a verdict.

**A green validator is not a review, and a clean review does not discharge
validation.** The two fail in opposite directions and neither covers for the
other: a check measured against the spec cannot find what the spec never
anticipated, and a review that reported nothing has said nothing about whether
the item did what it was specified to do.

**Findings triage the way insights do (§1 → insights-triage.md).** A review finding
in scope for the running item is a fix on its branch, dispatched back to the
role that owns the file. One outside it is a single line in `insights.md`, for
the feedback loop to triage at the queue boundary — never a widening of the
item's authorised paths, and never acted on in place.

**A review that lands after the merge is a report, not a review.** Wherever an
adapter runs the reviewer concurrently with validation, the merge still waits
for both.

**Neither read signs off its own work.** The role that wrote the code performs
neither, and the reviewer writes no code, modifies no tests, does not merge,
and does not touch `progress.md` — its output is findings for another role to
act on. A reviewer that fixes what it finds has destroyed the evidence for the
call.
