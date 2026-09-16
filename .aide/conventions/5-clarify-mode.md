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

**The duty runs both ways.** When several specs are authored before any is built,
the *producing* spec must enumerate the shape its declared consumers read — not
only the API it exposes but the **serialised form**: the JSON layout, which tiers
or records appear in a walk, what a strict mode rejects.

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
- **Why the producer pins the serialised form.** Left unpinned, each consumer
  independently codes defensively around it — a tolerant reader plus a
  hand-back clause where a straight assertion belonged — and one of them
  eventually pins an assertion against a shape no code path produces. Pinning
  it once, in the spec that owns it, is cheaper than every consumer guessing
  separately.
