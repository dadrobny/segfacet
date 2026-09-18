### `items/NNN-*.md`

Governs the item spec — one file per item, the single source of truth the
test-writer, builder and validator build against. `spec-author` writes it,
`spec-reviewer` reads a queue's against each other, and `aide check` reads its
header and its `## Dependencies`.

- **Filename begins with the zero-padded number.** First `#` heading is
  `# Item NNN — Title`. *(status report title parse)*
- **No status field** in the header — status lives only in `progress.md`. The
  header carries `Created`, Stage, Queue, Objectives, Suggested branch, and a
  mandatory **Assumptions** block (see the item template). *(spec-author,
  validator)*
- **An assumption that pins engine behaviour names the engine it was true
  for** — `- **A3 (engine 1.28.1):** …`, the marker `insights.md` provenance
  already carries, in the bold label beside the assumption's own code. `aide
  check` warns when the engine has since moved past a marked assumption.
  Clear it the way
  every other durable record in this loop is corrected — **append**: a
  re-check goes into the marker, `(engine 1.28.1, re-checked 1.36.0)`, and the
  newest version named is the one the claim stands on. A merged spec is never
  rewritten to agree with a later engine. An unmarked assumption is not warned
  about — the marker is what makes the claim checkable. *(spec-author,
  validator, `aide check`)*
- **`## Dependencies` blocks `aide claim`.** Every item number named in this
  section (any of the accepted forms in the table above) is read as something
  this item is blocked on until that item is **merged** (✅), or leaves the
  queue's way as ❌ excluded or ⏸️ deferred. 🚧 and 🔍 both still block.
  `aide claim` therefore skips a `📋` item while any of its dependencies is
  still open. Text at or after a literal
  `**Downstream` marker is excluded from that scan, so a forward-looking aside
  ("**Downstream:** item 099 depends on this item's CI job") does not register
  as a backward blocker — put such asides after the marker, never before it.
  The rest of any line from a backticked or bold `Blocks:` label on is
  excluded too, so quoting a human-gate row's reach ("waits on Gate 3 —
  `Blocks: items 119, 120, 121`") does not turn the gate's whole reach into
  dependency edges. The markup is what makes it a marker: plain-prose
  "blocks:" excludes nothing, so an English sentence naming real blockers is
  never silently dropped. Keep a reach quote on one line — the exclusion does
  not extend past it. *(aide claim)*

**An acceptance criterion is an invariant over the resulting content — never a
bound on the diff that produced it, and never a premise about a sibling item's
schedule.** *(spec-author, test-writer, validator)* The criterion outlives its
item: its test is still in the suite long after the branch is gone, so a
criterion that cannot be re-checked then is not one the suite can keep. **And
it is a claim about the world, not about its own wording: a criterion that
asserts a fact about live state is a measured equality against that state, and
a criterion that closes a stage acceptance criterion names which one.** Four
shapes fail that:

- **A bounded diff against a pre-item baseline.** Assert the property the
  edit was supposed to produce instead. The diff-time half of such a claim —
  "this item did not touch X" — is `aide scope`'s job on the claim
  branch, declared under `## Asserts against`; §1 → authorised-paths-proof
  says what not to write, and `aide check` warns on the two literal shapes.
- **A premise about a sibling item's schedule.** "Item NNN has not landed yet"
  is guaranteed to become false. Where an earlier item's test must change when
  a later one lands, the later item's spec lists that test file under **May
  change** from the start, and the earlier item declares what it pins under
  **Asserts against**.
- **A shape check standing in for the fact it was supposed to measure.** An
  AC that asserts a fact about live state — a field set, a firing set, a
  consumed path, a count — is met only by a test that **recomputes that fact
  from the primary source and compares**. A test that its subject can satisfy
  without the claim being true is not evidence of the claim: a sentence's
  length, a token in it that resolves against live state, a completeness flag
  derived from the declarations rather than from what they describe. Word the
  criterion as the equality — "the artifact's per-label field set is exactly
  {…}" — and the test that satisfies it has nowhere to be vacuous. Where the
  fact genuinely cannot be recomputed, the criterion is not one this suite can
  keep, and saying so beats attesting a proxy.
- **A stage acceptance criterion closed by positional coincidence.** An item's
  ACs and its stage's acceptance criteria are two independent lists; that they
  are the same length is arithmetic, not a mapping. An AC closes a stage
  criterion only when the spec says so — the optional *(closes Stage N
  criterion M)* annotation in the item template — and only when the item's
  deliverable **is** that criterion's subject, not when it touches the same
  area. An AC that names none closes none. `aide progress accept` is
  per-criterion for this reason — the evidence
  string must name the check that closes *that* criterion, and an index is not
  a check. Under a spec authored with the annotation available, silence is an
  answer: no annotation means no stage criterion is closed, and there is
  nothing for the validator to work out.

  **One transitional exception, and it declares itself.** A merged spec
  predating the annotation is never rewritten to carry it — §1 keeps merged
  specs as records — and its stage does not thereby stop being attestable. For
  such a spec only, a stage criterion may be attested on its **own subject**,
  verified in this run, where the evidence both names the check that closed it
  and says the mapping was made at attestation time. The index is never the
  mapping under either, and a criterion whose check the evidence cannot name
  is one nobody has yet closed.

**An acceptance criterion is written only when something fails without it:
the item's own deliverable, or a declared consumer in the batch that reads what
it pins.** *(spec-author, spec-reviewer)* One test per criterion is the floor
and the ceiling of what the item's tests cover (§6), so a criterion that
neither the deliverable nor a consumer needs buys a test and nothing else. A
criterion with neither is not written. **Under `durable` (§1 → vision.md) a
consumer a later stage will have counts as one; under `prototype`, the
default, only a consumer declared in the batch does.** The posture changes
which consumers count, never what a criterion may claim. **What was
deliberately left undecided goes in one short `Left open` note under Decisions
& Trade-offs** — one line, `- **Left open:** <the question, and why this item
did not settle it>` — so the next item finds the decision deferred rather than
forgotten. The queue is bounded the same way, by the posture table's
`queue-planner` row.

#### Rationale

- **Why an assumption names its engine.** A spec outlives its branch and the
  engine moves under it: three merged specs in one consumer asserted `aide
  check` warnings that a later release had deliberately removed, one calling
  their presence "expected output", and nothing detected it — `install.py
  --update` copies a new engine and says nothing about the claims it has just
  falsified. Rewriting a merged spec to agree with a later engine is the
  failure mode, not the fix; and inventing a version for an unmarked
  assumption is worse than leaving it unclaimed, which is why the unmarked
  case is not warned about. A patch release cannot falsify a claim about
  behaviour, which is why the lint is silent across one.
- **Why 🚧 and 🔍 block.** Work in progress is not in the base a dependent
  would branch from, and neither is work whose PR is still open.
- **Why a bounded diff fails on arrival.** Once the item merges into the
  branch its baseline is derived from, the two sides of the comparison are the
  same tree: the test is then either vacuous — green while asserting nothing —
  or red, a fixture-sanity guard correctly refusing to compare. Which of the
  two it becomes depends only on whether the author happened to write the
  fixture guard, and under a stacked queue it arrives on the very next claim,
  since the queue branch tip *is* the post-item state.
- **Why a schedule premise is expensive.** It breaks in a file the later item's
  Authorised paths do not cover — so the repair needs a spec amendment before
  it can be made at all. Declaring the pin under **Asserts against** is what
  makes the collision visible at spec time rather than at first pytest.
- **Why the equality wording.** Three shape-check criteria passed three false
  factual claims into merged artifacts in one queue, each fix making the next
  check stronger and the next false claim still slipping past it, all three
  found by a human reading the merged text.
- **Why the annotation, and why the exception says so.** One validator mapped
  a five-AC item onto a five-criterion stage by index and attested four
  criteria against tests that measured something else entirely; all four were
  retracted the same day. The annotation moves the decision to spec time,
  where the author who knows the deliverable is; inferring it at attestation
  time, from two lists and nothing else, is the move that produced those
  retractions. An AC that names none is the ordinary case and costs nothing: a
  stage criterion nobody has attested stays open, which is true. The
  transitional exception's required phrase puts the weaker
  basis into `progress.md` permanently, so a reader can tell the two apart,
  and it is a sentence nobody writes by accident on a spec that could have
  carried the annotation.
- **Why a criterion needs a reason.** Every gate in the item loop pushes
  toward more and none toward less: the validator FAILs an uncovered
  criterion, and a superfluous one — an AC the deliverable never needed, a
  shape pinned that no consumer reads — fails nothing. Measured across
  consumers on engine ≤ 1.54.1 (issue #242), that asymmetry produced item
  specs whose criteria outran the deliverable and suites in the thousands
  within a few queues. Stating the justification where the criterion is
  written is the counter-gate; the `Left open` note is what keeps "not
  written" from reading as "not considered" — the choice was made, and it is
  on record where the builder of the next item looks.
