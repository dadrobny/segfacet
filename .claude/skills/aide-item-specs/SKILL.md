---
name: aide-item-specs
description: Load before writing an item spec — its header and Dependencies, what an acceptance criterion may claim, the Authorised paths aide scope proves, gated capabilities, and clarify mode (conventions §1, §5).
user-invocable: false
paths:
  - "**/items/*.md"
---

# Item specs

`.aide/conventions.md` §1 → `items.md`, §1 → authorised paths, §1 →
environment-gated capabilities and §5 are the sources of truth; this file is
how the four reach `spec-author`, preloaded at spawn, because they fix the
parts of the one document it writes. It is **delivery, not a second source of
truth**. Proving a declaration once the branch exists is §1 →
authorised-paths-proof, another role's job and not delivered here — only the
handful of its statements you decide against while writing the spec.

**An item spec's filename begins with the zero-padded number, and its first
`#` heading is `# Item NNN — Title`.** **No status field in the header —
status lives only in `progress.md`.** The header carries `Created`, Stage,
Queue, Objectives, Suggested branch, and a mandatory **Assumptions** block.
**An assumption that pins engine behaviour names the engine it was true for** —
`- **A3 (engine 1.28.1):** …` — and is corrected by append: a re-check goes
into the marker, `(engine 1.28.1, re-checked 1.36.0)`, and the newest version
named is the one the claim stands on. A merged spec is never rewritten to
agree with a later engine.

**`## Dependencies` blocks `aide claim`**: every item number named there is
read as something this item is blocked on until that item is merged (✅), or
leaves the queue's way as ❌ excluded or ⏸️ deferred — 🚧 and 🔍 both still
block. Text at or after a literal `**Downstream` marker is excluded from that
scan, so put such asides after the marker, never before it. The rest of any
line from a backticked or bold `Blocks:` label on is excluded too, so quoting a
gate row's reach adds no edges; keep a reach quote on one line — the exclusion
does not extend past it.

**An acceptance criterion is an invariant over the resulting content** — never
a bound on the diff that produced it, and never a premise about a sibling
item's schedule. Its test outlives the branch it was written on: a criterion
that cannot be re-checked once the item has merged is not one the suite can
keep. The diff-time half of such a claim ("this item did not touch X") is
`aide scope`'s, declared under `## Asserts against`; a premise that a sibling
has not landed yet is guaranteed to become false, so the later item's spec lists
that test file under **May change** from the start.

**And it is a claim about the world, not about its own wording: a criterion
that asserts a fact about live state is a measured equality against that
state, and a criterion that closes a stage acceptance criterion names which
one.** A factual AC — a field set, a firing set, a consumed path, a count — is
met only by a test that **recomputes that fact from the primary source and
compares**; a check its subject can satisfy while the claim is false (a
sentence's length, a token in it that resolves, a completeness flag derived
from the declarations rather than from what they describe) is not evidence, and
three of those passed three false claims into merged artifacts in one queue.
And an item's ACs are not positionally mapped onto its stage's acceptance
criteria: an AC closes one only where the spec's optional *(closes Stage N
criterion M)* annotation says so, and **an AC that names none closes none**.
`aide progress accept` is per-criterion for this reason: the evidence names the
check that closes *that* criterion, and an index is not a check. Under a spec
authored with the annotation available, silence is an answer: no annotation
means no stage criterion is closed. The one transitional exception declares
itself — a merged spec predating the annotation is not rewritten to carry it,
and its stage may still be attested on the criterion's own subject where the
evidence names the check and says the mapping was made at attestation time.

## Authorised paths

**An item spec declares the files it may change, and `aide scope` proves the
declaration by the diff** (§1 → authorised paths). The section is **expected
but not required** — it ships in the item template, and a tool that does not
find it reports that rather than reading the spec as unconstrained. Two lists
of repo-relative paths, one path per bullet, each in backticks with a short
reason:

```
## Authorised paths

**May change:**

- `src/pkg/extract.py` — the new extractor

**Asserts against:**

- `docs/aide/catalogue.generated.json` — AC7 recomputes its counts live
```

**One path per bullet is a contract, not a style note**: a bullet declares the
**first backtick span before its reason** and nothing else, so a second path
in that position is dropped, and so is a list that wraps onto a continuation
line — `aide check` warns at spec time. **May
change** — every path this item is authorised to modify, in one of three
recognised forms: an exact path, `dir/**`, or a single-star `dir/*.ext`.
Prefer the narrowest form that covers the work. **Asserts against** — files or
derived artifacts this item's tests read and **pin** without changing. Include
derived artifacts recomputed live, not just files compared byte-for-byte.

Three paths are authorised for every item without being listed —
`progress.md`, `insights.md`, and the item's own spec — and **never list an
always-authorised path under Asserts against**. **Asserts against means
pinned-not-changed**, so never list the same path under both **May change** and
**Asserts against**.

**Scope is proved by the diff, not by a hash** (§1 → authorised-paths-proof):
the validator runs `aide scope` on the claim branch against what you wrote
here, so a list that is honest at spec time is the whole of it — write the
narrowest form the work actually needs, not the one that will pass. Two
consequences are yours while the spec is still cheap to change. Where a sibling
in the same batch changes what this item pins, `aide check --queue` errors
unless the ordering is declared: **a pair with no declared dependency keeps the
error, and saying so under `## Dependencies` is the third remedy the message
offers**. And **a diff-time scope claim is never a suite assertion** — "this
item did not touch X" is decided on the branch, so declare the file under
**Asserts against** rather than specifying a test that hashes its bytes against
a literal, which **inverts on the next legitimate edit** (§6 names the two
shapes `aide check` warns on).

## Environment-gated capabilities

**A capability only some environments can exercise must degrade gracefully**
(§1 → environment-gated capabilities): its tests skip cleanly (never fail,
never silently pass as if exercised) when the dependency is absent. That
graceful-fallback bar is enough for a stage to reach ✅ under the rollup rule,
so two additive mechanisms record whether the gated path was ever run for
real — the item template's optional **Environment / Hardware Dependencies**
section, naming the package or tool, its declaration and the required fallback;
and `progress.md`'s optional verification table, one row per capability,
starting `❓ Unverified` and flipped to `✅ Verified (date, host/CI)` only when
something that actually has the dependency has run the gated path, **never
inferred from the stage's own ✅ status**. **A stage-closing item's
Implementation Steps must add/update the row(s) for any capability its stage
introduced.** Both mechanisms are opt-in. A named `[validation]` profile in
`aide.toml` makes the check deterministic (`aide env --profile <name>`), and
**item specs may also carry an optional Validation section (see the item
template) that the validator must execute**. The stage's own replay is an item
like any other: **a queue that closes a roadmap stage ends with a `Validate
stage N` item that replays the stage's use cases end-to-end and updates the
capability table** — ✅ Verified where the profile is satisfied, else an
explicit ❓ Unverified with the reason: **a row still `❓ Unverified` once its
stage is ✅ records why in its Notes cell**, and **a row names the
`[validation]` profile that would verify it in its Package / Tool cell, as
`` `<name>` profile ``**. `queue-planner` names it; this role writes its
spec.

## Clarify mode

**`loop.clarify` controls how `spec-author` resolves an ambiguous queued item**
(`.aide/conventions.md` §5): **`interactive`** — ask ≤3 targeted questions
before writing the spec; **`assume`** (unattended default) — pick the most
defensible default and record each choice in the spec's mandatory
**Assumptions** block, which the validator surfaces so a human can audit at
the queue boundary. Nothing ever hangs. A spec written before its dependencies
are *implemented* must pin their interfaces as Assumptions; the
builder/validator hand back if reality diverged. **The setting governs
`spec-author` and nothing else.**

**A contradiction between the spec and the tests written from it comes back
here**: `builder` hands the item back naming the criterion, the test, and what
the two disagree about, and `spec-author` corrects the criterion under
whatever `loop.clarify` says. The spec is corrected first; the tests are then
re-derived from the corrected criteria; only then does the builder implement.
The correction is an **amendment, never a rewrite** (§1 → `items.md`): a
dated correction appended to the spec, because the original criterion is the
record of what the item was built from.

**The duty runs both ways.** When several specs are authored before any is
built, the *producing* spec must enumerate the shape its declared consumers
read — not only the API it exposes but the **serialised form**: the JSON
layout, which tiers or records appear in a walk, what a strict mode rejects.

**Root documents are authored through their loop entry point, interactively —
whatever `loop.clarify` says** (`.aide/conventions.md` §5); here that entry point
is `/aide-create-vision` / `/aide-create-roadmap`, which carries the
existing-document check and the draft-for-review hand-off. **Do not write a root
document directly, however well the template shape is known** — ask until the
mandatory sections are grounded in the human's answers, and never fill **Guiding
principles**, **Out of scope**, or **Success criteria** from assumption.
