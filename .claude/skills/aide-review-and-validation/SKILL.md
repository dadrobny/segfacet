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
suite has no failure the item caused, every AC has a test that measures it,
the diff is inside the authorised paths, the Assumptions still hold. Every term is measured against
the item spec, the verdict is PASS/FAIL — or none, when a run outlasts its
limit (below) — and it **gates the merge**. Review
asks *is this code correct, and does it fit the codebase* — it reads the diff
adversarially for what the spec never anticipated, and it **produces findings**,
not a verdict.

**Each read owns its questions, and neither re-asks the other's.** Validation
owns the suite, Acceptance Criteria coverage, the authorised-paths check
(`aide scope`), the Assumptions, the spec's Validation section, and vision fit
— the implementation against the vision and its Out-of-scope list. Review owns the
correctness of the diff and its fit to the codebase. It does not re-judge the
diff against the authorised paths or the vision — those stay validation's
whether review runs or not — and a reviewer that notices an edit to a path the
spec never authorised names it in its report, unranked and uncounted, for
validation to decide.

**Where the merge compares a red run with its base, the merge decides a red
suite.** Under a `git.mode` whose merge runs the test gate (§4: `auto-merge`,
`local`), a failing test is not by itself a FAIL: validation records the
failing tests, completes every other check, and when those pass it runs the
merge as usual. The merge's gate is the arbiter. A refusal that names failures
the item caused is a FAIL, returned to the builder with those failures, and so
is a refusal that could not compare the failures with the base at all; an
admission of inherited failures is a PASS that names them. Under `pr`, where
the merge runs no gate, a red suite is a FAIL. A validation whose merge is
held for review reports its PASS with the failing tests listed, and says that
the later merge's gate decides them.

**Validation runs the whole suite through `aide test`, never as the bare test
command.** The verb runs the configured command as the merge runs it, exits
with its exit code, and records the result, so a merge that lands exactly the
tree validation ran takes that result instead of a second run (§4). A narrower
run — one file, one case, while diagnosing — is run directly: it is not the
suite, and nothing takes it in the suite's place.

**A green validator is not a review, and a clean review does not discharge
validation.** The two fail in opposite directions and neither covers for the
other: a check measured against the spec cannot find what the spec never
anticipated, and a review that reported nothing has said nothing about whether
the item did what it was specified to do.

**Findings triage the way insights do (§1 → insights-triage.md), and scope is
a question about the change, not about the path.** A finding about this item's
diff is in scope whatever file it lands in, and an in-scope finding is a fix on
the branch, dispatched back to the role that owns the file; a test that fix
adds is traced to the finding the way §6 says. An edit to a path the spec
never authorised is about this diff too, so it is never an out-of-scope line;
validation fails it (above), and the fix reverts that part of the branch.
A finding about code this diff did not touch is out of scope: a single line in
`insights.md`, for the feedback loop to triage at the queue boundary — never a
widening of the item's authorised paths, and never acted on in place.

**Every finding carries a rank as well as a scope: blocking, minor or nit.**
The scope question is the one above; the rank says what the loop does with the
finding. *Blocking* — in scope, and the merge waits for the fix. *Minor* — in
scope too, and the triaging role chooses between fixing it on the branch now
and capturing it as one `insights.md` line — a `defect` entry naming the item,
so the maintenance queue picks it up (§1 → insights-triage.md). *Nit* — in
scope, and it never earns a validation round of its own: it rides along in
whatever dispatch a blocking or minor finding has already caused, and where it
is the only thing left it goes to a builder on its own — a fresh one, or the
same one resumed, whichever the adapter has — which fixes it and returns, with
no validator and no reviewer behind it and nothing added to the round count. A
nit changes no behaviour by definition, and one that changes behaviour was
ranked wrong. Scope is answered first and it wins: a finding outside the
running item is one `insights.md` line whatever its rank, since a severe
observation is no licence to widen the authorised paths — and the rank is the
first word of that line's free text, so the entry carries it without any change
to the entry's shape (§1 → insights.md). The rank belongs to the role that
triages, not to the one that reports — a reviewer proposes a rank, and a
project's own review contract re-ranks where it speaks, exactly as
it already decides what is worth flagging at all. Counts by rank are what the
run ledger records (§1 → ledger.md), **and they count in-scope findings
only** — an out-of-scope one is carried by the inbox line instead, with the
item that found it — so a finding is ranked as it is triaged and never
reconstructed afterwards.

**A review that lands after the merge is a report, not a review.** Wherever an
adapter runs the reviewer concurrently with validation, the merge still waits
for both.

**One review per item, of the diff as first built.** The reviewer is
dispatched once, when the build first returns, concurrent with the first
validation, and never again for the same item. Its findings are triaged at that
validation's verdict whichever way it goes: on a FAIL, the triaging role waits
for the review and sends every in-scope finding it is fixing in the same fix
round as the validation failures — one round for both reads. After any fix
round, a fresh validation runs and no second review; a fix made for a finding
is measured by that validation like any other fix — a blocking one through
the test traced to it (below) — and counts against the round cap the same
way. A finding about code a fix round removed or rewrote
before it was fixed is dropped, and not counted: the code it describes no
longer exists.

**A blocking finding about behaviour is fixed together with a test traced to
it, and every validation after a fix round checks the trace.** The validation
is handed every blocking finding fixed on the branch so far whose code a later
round has not removed, and fails the round where one has no bullet in the
spec's `## Review findings`, or a bullet naming neither a test traced to it
nor why it has none (§6) — a finding about a document or a name changes
nothing a test could measure, and says so there. It checks an artifact, not
the fix: that the bullet is there and that the test it names is in the suite
the validation runs, which judges that test as it judges any other. Whether
the code now answers the finding is review's question, and the validation does
not ask it — it reads no diff for it, exactly as it re-asks nothing else
review owns. A minor finding fixed on the branch and a nit carry no such
requirement, though a test added for one still traces the way §6 says. A
finding read from the queue's CI is not a review finding here: it names the
failing test or step that is its check, and the next CI run re-runs that.

**Neither read signs off its own work.** The role that wrote the code performs
neither, and the reviewer writes no code, modifies no tests, does not merge,
and does not touch `progress.md` — its output is findings for another role to
act on. A reviewer that fixes what it finds has destroyed the evidence for the
call.

**A command that can outlast the runtime's bound on one tool call, or on how
long an agent may sit idle, is run detached and waited on in bounded waits.**
Its output goes to a file, and the agent waits on it inside its own turn, each
wait shorter than that bound — never in a tight polling loop, and never by
ending the turn to await a notification. The suite is the usual such command,
and a merge that re-runs it is the second. At the overall limit the adapter
states, stop waiting and hand back the command, the elapsed time and its last
output in place of a verdict.
