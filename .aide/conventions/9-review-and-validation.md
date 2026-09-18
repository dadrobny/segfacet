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

**Findings triage the way insights do (§1 → insights-triage.md), and scope is
a question about the change, not about the path.** A finding about this item's
diff is in scope whatever file it lands in, and an in-scope finding is a fix on
the branch, dispatched back to the role that owns the file. A diff that touched
a path the spec's `## Authorised paths` never authorised is itself such a
finding — in scope, *blocking*, and fixed by reverting that part of the branch.
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

**Neither read signs off its own work.** The role that wrote the code performs
neither, and the reviewer writes no code, modifies no tests, does not merge,
and does not touch `progress.md` — its output is findings for another role to
act on. A reviewer that fixes what it finds has destroyed the evidence for the
call.

### Rationale

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
- **Why concurrent review costs nothing and still gates.** A full suite run is
  the long pole and a read of the diff fits inside it. Findings collected after
  the item has landed gate nothing, and the loop is entitled to treat
  "reviewed" as meaning the findings were available while the decision was
  still open.
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
  a file nobody authorised would be "out of scope", so the finding that says
  the branch overstepped would be filed as an inbox line and the overstep
  would merge. The diff is what the item did, so the diff is what a finding
  about the item is measured against, and the authorised paths stay what they
  were — a bound on what may be changed, not a filter on what may be reported.
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
