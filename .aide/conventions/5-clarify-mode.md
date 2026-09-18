## 5. Clarify mode (`loop.clarify` in `aide.toml`)

Controls how `spec-author` resolves an ambiguous queued item:

- **`interactive`** — ask ≤3 targeted questions before writing the spec.
- **`assume`** (unattended default) — pick the most defensible default and record
  each choice in the spec's mandatory **Assumptions** block, which the validator
  surfaces so a human can audit at the queue boundary. Nothing ever hangs.

A spec written before its dependencies are *implemented* must pin their interfaces
as Assumptions; the builder/validator hand back if reality diverged.

**A contradiction between the spec and the tests written from it comes back
here.** The test-writer encodes the Acceptance Criteria; when the encoding and
the prose disagree, one of the two is wrong, and `builder` — the first role that
reads both — is the first position from which that is visible. **It hands the
item back to `spec-author`**, naming the criterion, the test, and what the two
disagree about. The spec is corrected first; the tests are then re-derived from
the corrected criteria; only then does the builder implement.

This is the same resolution the mode already governs, arriving from downstream
rather than from a queue line: `spec-author` corrects the criterion under
whatever `loop.clarify` says — `interactive` asks the human which side is wrong,
`assume` takes the most defensible reading and records it in the spec's
Assumptions block for the queue boundary to audit. The builder does not read the
setting; it has one move, and the setting decides what the role it hands to does
next.

The correction is an **amendment, never a rewrite** (§1 → items.md): a dated
correction appended to the spec, the way an in-flight scope repair already is,
because the original criterion is the record of what the item was built from.

**A Decisions entry is not this hand-back.** Recording "these two assertions are
unsatisfiable under any implementation" and shipping anyway is a durable, honest
note — and nothing downstream reads it as a signal. The hand-back is a
distinguished outcome the driver can route on; the Decisions entry records what
was decided once a role with standing has decided it.

**The setting governs `spec-author` and nothing else.** It is not a global
posture on asking-versus-assuming.

**Root documents are authored through their loop entry point, interactively —
whatever `loop.clarify` says.** `vision.md` and `roadmap.md` are Steps 1 and 2
of the loop, and the adapter's create-vision / create-roadmap entry points carry
the safeguards a free-hand file write skips. Do not write a root document
directly, however well the template shape is known. Ask until the mandatory
sections are grounded in the human's answers, and never fill **Guiding
principles**, **Out of scope**, or **Success criteria** from assumption.
Present the result as a draft.

**The duty runs both ways, and it pins at the level a consumer reads.** When
several specs are authored before any is built, the *producing* spec pins what
its declared consumers read, **in the form they read it, and nothing more**. A
consumer reads through the producer's function, or through a fixture the
producer's item ships, wherever one exists; a **serialised layout** — the JSON
layout, which tiers or records appear in a walk, what a strict mode rejects —
is pinned only where a consumer genuinely parses the file. A consumer that
needs one field does not pin the layout around it.

**A pinned interface is re-checked at claim once its dependency has merged.**
An item whose Assumptions pin the interface of an item under its
`## Dependencies` has those Assumptions re-checked against the real code when
it is claimed — by `spec-author`, **before** any test is written from them —
as the append-only amendment above: a re-check that agrees is appended to the
assumption, and one that does not corrects it, dated, with the original left
standing. **The pin itself is the signal**: a spec pins a dependency's
interface only when written before that dependency was built, and a claim
happens only once it has merged, so no date is compared. Three shapes are
not that signal: an Assumption recording a defensible default, or naming an
engine version, is an audit entry and not an interface pin; an Assumption
already carrying a re-check is not re-checked again; and a dependency that
left the queue's way as ❌ or ⏸️ has no code to check against, so the
re-check records the interface as absent, corrects the assumption, and the
divergence is raised in the return rather than agreed to. A spec whose
Assumptions pin no dependency is not re-checked. `aide claim` names the pins
it finds as it claims (`aide claim -h`).

### Rationale

- **Why the builder has no standing.** The tests are its oracle, the criteria
  are what the tests were derived from, and picking either side ships one
  reading of a defect.
- **Why a Decisions entry is not a signal.** The validator checks that the
  tests pass and that the item stayed in scope, and both are true of a
  defective criterion faithfully implemented; the entry is a note that the
  loop reached a state it should not be able to reach silently, and nothing
  routes on it.
- **Why the setting reads as global, and is not.** It sits under `[loop]`, is
  named generically, and is the only such statement in `aide.toml`; the roles
  it does not govern have one move each, and the setting decides what the
  role they hand to does next.
- **Why `assume` is defensible for an item and not for a root document.** A
  queued item's trade is audited: every choice lands in the spec's mandatory
  Assumptions block, a human reads it at the queue boundary, and a wrong item
  is one unit of a batch, cheap to redo. A wrong assumption at the root has no
  Assumptions block to be audited in, no queue boundary to be caught at, and
  propagates into the roadmap and every queue and item derived from it.
  Root-document authoring is the one part of the loop where a human is
  present by construction — the step exists to capture what only they know.
- **What the entry points guard.** The existing-document check (a vision is
  overwritten only after explicit confirmation; a roadmap is updated
  incrementally, never regenerated), and the draft hand-off the rule above
  names — a draft is what a human can decline without unpicking anything.
- **Why the producer pins, and why only at the consumer's level.** Left
  unpinned, each consumer independently codes defensively around the
  interface — a tolerant reader plus a hand-back clause where a straight
  assertion belonged — and one of them eventually pins an assertion against a
  shape no code path produces. That defect earned the producer's duty, and the
  first version of the rule fixed it by pinning *more*: the whole serialised
  form, whether or not anyone parsed it. Measured across consumers on engine
  ≤ 1.54.1 (issue #243), that is what turned every change to a producer into
  a red test in a consumer that had read one field — the consumer's tests
  had hand-built the producer's layout from the pin. Pinning once, in the
  spec that owns it, is still cheaper than every consumer guessing; pinning
  what is read, in the form it is read, is what stops the pin from breaking
  the readers it was written for. §6 holds the test-side half: a consumer test
  obtains the producer's form from its code or fixture, never by hand.
- **Why the re-check runs at claim.** A batch pins before any dependency is
  built, so the pin is a prediction; per-item authoring reads the interface
  from code, so it is not. The moment the two converge is the claim of the
  dependent item, after the dependency has merged, and the loop already
  resolves that status there for blocking. Re-checking then turns "test
  invalidated" into "assumption amended", in the document that owns the
  claim, before a test has encoded the stale one.
