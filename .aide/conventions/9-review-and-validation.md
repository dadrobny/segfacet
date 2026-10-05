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
is measured by that validation like any other fix, and counts against the
round cap the same way. A finding about code a fix round removed or rewrote
before it was fixed is dropped, and not counted: the code it describes no
longer exists.

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

### Rationale

- **Why a red suite waits for the merge.** Validation ran the same whole suite
  the merge's gate runs, so a failure already on the base failed every item
  at validation, before the merge could tell an inherited failure from the
  item's own. A consumer's item met all sixteen of
  its criteria and was held on nine failures identical at the merge-base
  (issue #275). The validator cannot make that comparison without running the
  base itself, and the merge already does, so the verdict on a red suite
  moves to the one step that can separate the two. Under `pr` nothing in the
  loop compares, so the old rule stands there.

- **Why the suite goes through a verb.** A bare run leaves nothing the engine
  can read, so the merge re-ran the whole suite over a tree validation had
  tested minutes earlier — under `auto-merge`, every fast-forward merge paid
  for the suite twice, and the second wait is the one that outlasts a
  waiting agent's cache (issues #274, #275). Recording the run where the
  engine keeps its base runs is what lets the merge see it.

- **Why delivered.** A role that has not been told the difference will collapse
  the two, and the collapse is silent — both reads end in a report that says
  the item is fine.
- **Why neither covers for the other.** A spec cannot enumerate in advance the
  enumeration that drops an input, the guard that passes while the thing it
  checks is absent, or the contract an earlier item established and a later
  one quietly reworked. Equally, a reviewer reading for defects is not counting
  Acceptance Criteria, running the suite, or comparing the diff against the
  authorised paths.
- **Why findings route like insights.** The two questions — in scope, or not —
  are the same ones every role already answers about an out-of-scope
  observation, so the answer is the same shape.
- **Why each read owns its questions.** Both reads once reported an edit
  outside the authorised paths — validation as a FAIL measured by
  `aide scope`, review as a blocking finding judged by reading — so one overstep
  could cost two dispatches and be counted twice, and with review off by
  default the check could never have depended on the reviewer anyway. The
  scope check and the vision read are measured against documents, which is
  validation's question; review's is what no document anticipated. The
  separation pays without a second provider: in one consumer's ledger of 52
  items, with builder, validator and reviewer all on the same model, 31
  carried at least one in-scope review finding — 68 findings in all: 8
  blocking, 23 minor, 37 nits (issue #357).
- **Why concurrent review costs nothing and still gates.** A full suite run is
  the long pole — about three to seven minutes in the recorded runs — and a
  read of the diff fits inside it. Only the first validation has a review
  beside it, and the first validation usually passes: at most 9 of those 52
  items took an extra round with no blocking or minor finding behind it, so a
  review is rarely read against a diff that then changes. Findings collected
  after the item has landed gate nothing, and the loop is entitled to treat
  "reviewed" as meaning the findings were available while the decision was
  still open.
- **Why one review, and why its findings join the first fix round.** The
  runner said nothing about a review whose validation failed, so a finding
  either waited for a later PASS and paid a round of its own or was read
  again over a changed diff. Sending it with the validation failures costs the
  round that was being paid anyway. A second review after each fix round would
  be a second build↔review cycle inside the build↔validate one, unbounded by
  the cap that exists to bound exactly that; the fix is measured by the next
  validation instead, as every other fix is. A finding about code that a fix
  has since removed describes nothing that will merge, so counting it would
  charge the item for code it no longer has.
- **Why a rank at all, and why three.** The ledger records findings by rank
  (§1 → ledger.md) and the contract had no scale to record them on: this
  section asked only whether a finding was in scope, and a project's own review
  contract ranks for its own pull requests rather than for the loop. A count on
  an undefined scale is a claim nobody can read back — two runs each reporting
  three minor findings say nothing to one another unless the word is fixed
  here. Three is the number of distinct decisions the loop makes about a
  finding it keeps: hold the merge for it, choose about it, or fix it without
  paying a round for it. A minor finding captured rather than fixed is the one
  in-scope entry the inbox
  carries — deferred for cost, not out of scope — and §1 → insights.md names
  that exception so the file's own definition stays true.
- **Why scope is the change and not the path.** Reading scope off the
  authorised paths inverts the one case that matters most: a diff that edited
  a file nobody authorised would be "out of scope", so a note that the branch
  overstepped would be filed as an inbox line and the overstep would merge.
  The diff is what the item did, so the diff is what a finding about the item
  is measured against, and the authorised paths stay what they were — a bound
  on what may be changed, which validation enforces, not a filter on what may
  be reported.
- **Why a nit never costs a round.** A validation round measures the branch
  against the spec's Acceptance Criteria, and a nit moves none of them: the
  round would re-run the suite to observe nothing, at the price of the cap the
  cap exists to protect. Where the merge runs the suite itself, the change is
  re-measured anyway before it lands. The risk this accepts is a mis-ranked
  finding riding through unvalidated, which is why the rank is defined by
  behaviour changed rather than by how small the edit looks.
- **Why the ledger counts only in-scope findings.** The counts are read as
  what an item cost, and an out-of-scope observation cost it nothing — it was
  never dispatched, never validated and never fixed here. It is not lost: the
  inbox line carries it, with the item that found it, which is the reading the
  queue boundary wants it in.
- **Why the reviewer writes nothing.** A reviewer that fixes what it finds has
  reviewed its own work by the time it is done.
- **Why a long command is waited on in bounded waits.** A validator in a
  consumer outlived its tool call on a hung suite and fell back to polling the
  process every two seconds for 24 minutes — about 450 calls, each re-reading
  its whole context — while the role above it sat waiting on a verdict that
  never came (issue #274). Ending the turn to await a notification is no
  better: the caller receives the placeholder as the agent's final report, the
  agent is not woken again, and the command dies with the session. One wait
  longer than the idle bound costs the agent its cached context on the next
  request, where a wait inside it keeps the context warm. A limit with a hand
  back turns a hung run into a report someone can act on.
