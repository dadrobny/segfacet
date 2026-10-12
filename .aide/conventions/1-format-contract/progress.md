### `progress.md` (the single source of truth for status)

`.aide/templates/progress.md` draws this document's shape; where it does, this
section names it rather than drawing it again, and fixes instead what a shape
cannot carry — what a cell may hold, and what is mandatory.

**Status is claimed here and nowhere else.** This is the only place the CLI
reads status. A status claim written anywhere else — a checklist in a spec, a "current
focus" heading, a summary in a README — is a second truth that will disagree
with the first. Move it, do not copy it.

Mandatory, in order (consumer in brackets):

1. **Stage summary table** — one row per stage; `Stage` is an integer,
   `Status` a single icon. The maintenance stage's `Objectives` cell reads
   `—`. *(aide check, status report, queue-planner)*
2. **Objective coverage table** — one row per vision objective; the objective
   cell starts with a `G<n>` code, `Status` a single icon. *(aide check, status
   report, validator)*
3. **One section per stage**, headed with the stage number, its title and its
   rolled-up icon. Inside it:
   - a **Deliverables** block of **flat** bullets, each
     `- <icon> <text>. *(Item NNN)*` — one status icon, one item ref, no nested
     status-bearing sub-bullets (keep rollup unambiguous). *(builder, validator,
     aide progress, status report)*
   - an **Acceptance** block of `- [ ]` / `- [x]` checkboxes, ticked only by
     `aide progress accept` — never derived. *(validator)*

   The maintenance stage (§1 → `roadmap.md`) is the one section without an
   Acceptance block, and its Deliverables block is empty until its first
   maintenance queue adds the bullets.

**The Stage summary table is complete.** Every stage section has its row, a
⏸️ or ❌ stage too: a ❌ summary row is what excludes a stage, and a ⏸️ one
records its deferral where the table is read. `aide check` warns on a section
with no row, as it does on a row with no section.

**A table row its reader cannot use is an `aide check` error** in each of the
four tables the engine reads: the two above, Outcome targets (below) and §1 →
human gates. Unusable means the wrong number of cells — a `|` inside a cell,
usually — a Stage cell that is not an integer, an objective cell not starting
`G<n>`, a summary or objective `Status` with no icon, or an empty Target cell.
The Environment-Gated Capability Verification table is the fifth, and gates
nothing, so an unusable row of it is a warning instead (§1 → environment-gated
capabilities).

**Item references on a deliverable bullet.** The `*(Item NNN)*` suffix is what
ties an item to the bullet whose status it moves — `aide progress set NNN` finds
the bullet by it, and `check`/`status`/`claim` derive queue state from it, so an
item no bullet references is untracked. **Suffix means suffix**: only the
trailing marker that ends the bullet (its last wrapped line) attributes. A
reference form earlier in the bullet's prose — "- ✅ Consolidate parsers,
absorbing *(Item 095)*'s scope *(Item 094)*" — is free text: here 094 is the
bullet's item and the mention of 095 moves nothing, so a ✅ bullet cannot mark a
live sibling complete just by naming it. A bullet whose references all sit
mid-prose tracks nothing, and `aide check` warns about it. These forms are all
accepted for the marker, and all mean the same thing to every command:

| Form | Reads as |
|---|---|
| `*(Item 006)*` | 6 |
| `*(Items 006, 044)*` | 6, 44 — one deliverable, several items |
| `*(Items 041, 053, 057)*` | 41, 53, 57 — a list is any length |
| `*(Items 089/090)*` | 89, 90 |
| `*(Items 071–075)*` | 71, 72, 73, 74, 75 — inclusive, hyphen or en-dash |
| `*(Items 006, 044–046)*` | 6, 44, 45, 46 — an element may be a range |

Spacing around a separator does not matter. Prefer the explicit list when the
items are not contiguous; a range is only shorthand for one.

**A marker naming several items is shorthand, never a shared status cell.**
`aide progress set` and `aide merge` **desugar** the bullet first, into one
bullet per item with the same text and one `*(Item NNN)*` each, and move only
the item named. Nothing is asked of the author — write the shared marker
freely; the file simply grows a row the first time its items diverge.

**A split copy's prose is reworded with its verb, whatever its icon.** Each
copy the desugar writes carries the sentence the shared bullet had, and `aide
check` warns while two single-item bullets of one stage read the same. Say what
each item delivers with `aide progress reword --item NNN`, never by hand: it
rewrites that one bullet's prose and keeps its icon and marker, over a ✅ bullet
as readily as a 📋 one. A deliverable bullet carries no attestation, so the
immutability rule below binds an acceptance box, never a bullet's sentence.

**Stage status is rolled up from the bullets, never hand-written.** A stage's
icon, its summary-table row, its section header and the Objective rows it
delivers are all derived from the Deliverables bullets under it, by one
deterministic rule `aide progress` and `aide check` both apply — `aide progress
-h` states the rule. Write the bullets and let the stage follow; an icon typed
over a derived cell is drift `aide check` reports. **A bullet added by hand
moves no stage cell until a verb rolls the stage up**, and `aide progress
rollup --stage N` is the verb that does it without moving a bullet: a batch
that adds bullets under the maintenance stage runs it (§1 →
`insights-maintenance-queue.md`).

**Deferral is recorded on the item, with its reason, and the stage follows.**
Postpone an item with `aide progress set NNN deferred --reason …`, never by
typing ⏸️ over a bullet or a stage: the verb keeps the why on the bullet's
trail, and a stage whose only open work is deferred rolls up to ⏸️ by itself —
never to ✅. A bullet no item marker names is deferred by its place instead,
with `aide progress set --stage N --deliverable K deferred --reason …`, K
counting the stage's deliverable bullets from 1. A
⏸️ stage header, summary row or Objective row the rollup does not compute is a
hand edit that stands until a verb moves a bullet of that stage or `aide
progress rollup` rolls the stage up, and `aide
check` warns on it for as long as it disagrees, as it does on a stage that
rolls up to ⏸️ under a cell that says otherwise. Defer the stage's open
bullets, each by the form that addresses it, or write the icon the rollup
computes with `aide progress rollup --stage N`, and the warning ends. A ❌ cell is outside the
comparison, and a ❌ summary row takes its stage's header with it: its bullets
no longer speak for the stage.

**Deferred work resumes with its own verb, back to 📋, with its reason.**
Resume an item with `aide progress set NNN resumed --reason …`, and a bullet no
item marker names with `aide progress set --stage N --deliverable K resumed
--reason …`: each ⏸️ bullet flips to 📋 under a dated trail line beside the
deferral's, and the stage follows. A resumed item is claimable again — `aide
claim` offers it, or the runner picks it up on a claim branch it still has. A
forward `aide progress set` refuses an item whose bullets are all ⏸️ or 📋.
Resuming is the owner's decision, and the reason says why the work is wanted
now. A ⏸️ or ❌ bullet is never itemised as it stands: a ⏸️ one is resumed
first, and a ❌ one was decided against, so it is not queued until it is
restored.

**A deliverable the stage turns out not to need is dropped, with its reason,
and the stage can close.** Drop a bullet no item marker names with `aide
progress set --stage N --deliverable K dropped --reason …`, never by typing ❌
over it: the verb keeps the why on the bullet's trail, and the bullet reads ❌,
which counts toward its stage's ✅ where a ⏸️ bullet never does. A ⏸️ bullet
is dropped the same way once its owner decides the stage does not need it at
all — defer what the stage needs later, drop what it does not need. An
itemised bullet is not dropped by its place: its status is its item's. Drop
an item with `aide progress set NNN dropped --reason …` — one abandoned at
the validation-round cap, or one its owner decides against — once it is not
✅; a shipped item is reopened first. A drop that would leave every
deliverable bullet of the stage ❌ is refused: a stage
with nothing left to deliver is withdrawn whole, by a ❌ on its summary row
and on any Objective row only it delivers; a stage already withdrawn that way
refuses no drop. The deliverable stays in `roadmap.md` as written.

**Dropped work is restored with its own verb, back to 📋, with its reason.**
Restore an item with `aide progress set NNN restored --reason …`, and a
bullet no item marker names with `aide progress set --stage N --deliverable K
restored --reason …`: each ❌ bullet flips to 📋 under a dated trail line
beside the drop's, and the stage follows. A forward `aide progress set`, and
`aide merge`, refuse an item whose bullets are all ❌ or 📋. Restoring is the
owner's decision, and the reason says why the work is wanted after all.

**A withdrawn stage speaks for no objective.** An Objective row is derived
from the stages it names whose summary row is not ❌, and reads ❌ only when
every stage it names is withdrawn; `aide progress` writes it so and `aide
check` compares it so.

**Acceptance boxes are attestations, and no rollup ever ticks one.** They are
outside the derivation entirely: the rollup skips checkbox lines, `aide check`
never gates a ✅ stage on them, and `aide progress set` leaves them exactly as
the author wrote them. A box is ticked only by a human — or by an agent acting
on a check it actually performed — via `aide progress accept`, whose flags
`aide progress -h` states.

A stage may be ✅ with an unticked box; say why in an annotation beside it.

**The attestation is immutable; what is recorded about it is not.** The
criterion line is never reworded once anything has been claimed against it, and
every later statement about it goes in an appendable **correction trail** —
dated lines indented under the box, newest last:

```
- [ ] Benchmark run end to end. *(validator, 2026-08-29: on this CPU-only machine)*
  - **2026-09-01** → the host has four GPUs; the CPU-only basis was misread
  - **2026-09-02** → retracted: re-run pending on a host we have identified
```

Three verbs, and **none of them edits the original line**, their flags in
`aide progress -h`:

- **`amend` appends, and only to a ticked box.** The attestation stands; what
  was recorded about it was wrong or thin. **A verb that can only add cannot be
  used to make an inconvenient attestation agree with a shipped stage.**
- **`retract` unticks, and keeps the original attestation visible.** The
  criterion does not hold after all, so the box reads as *claimed, then
  withdrawn, for this reason* — not as one nobody ever ticked. **A retraction
  is a finding, so the verb routes it like one**: an `insights.md` `- [ ] gap`
  entry in the same commit, exactly as a `❌ Not met` outcome target does.
- **`reword` is the one amendment that edits rather than appends**, and it is
  safe for exactly one reason: nothing has been claimed yet. It **refuses over
  a box that is ticked, annotated, or already carries a correction trail** —
  the precondition is mechanical, so no role has to remember it.

**`reword` writes both documents or neither wherever `roadmap.md` mirrors the
stage.** `roadmap.md` mirrors a stage's criteria, so a rewording that lands in
one file is precisely the two-file drift the verb exists to remove. The two
blocks are matched **by position**, so keep them in the same order; where they
cannot be lined up the verb writes nothing rather than guessing. **A stage with
no Validation / acceptance block in `roadmap.md` has no mirror to drift from**,
so there the verb writes `progress.md` alone and says so.

**What a stage's ✅ means — and what it deliberately does not.** The rollup
makes stage status track exactly one thing: *the planned work shipped*. An
Acceptance box is therefore an observable check **of the built thing** (the
CLI runs, the artifact validates) — something completing the deliverables can
guarantee. A **measured outcome** the work aims for but cannot guarantee by
construction (an error-rate target, a benchmark result) must NOT be an
Acceptance box. Such goals go in the **Outcome targets** table below.

**Outcome targets (optional, additive).** The template's optional
`## Outcome targets` section, one row per measured goal, its Target cell never
empty and its Objective cell naming the `G<n>` objectives it gates — one
naming none gates none. Status is table-local (like the env-gated verification table's): `❓ Unverified` until
measured, then `✅ Met (date, evidence)` or `❌ Not met (result → follow-up)`.
Semantics
*(aide progress, aide check, aide status)*:

- A target **never blocks its stage** — the stage closes when its work ships.
  It gates the **Objective coverage rows** instead: an objective linked to a
  target that is not `✅ Met` cannot roll up to ✅. What `aide check` then says
  about an objective claimed ✅ over one is graded, and `aide check -h` states
  it: an error over a `❌ Not met` target, a warning over any other non-Met.
- Marking a target `❌ Not met` is a *finding*, so route it like one: capture
  a `gap` with `aide insights add` alongside the edit. The follow-on
  deliverables then enter through the queue, never by retro-editing a closed
  stage's deliverable list; a maintenance queue adding its items under the
  maintenance stage (§1 → `roadmap.md`) is that route, not a retro-edit.

#### Rationale

- **Why a status claim is moved and never copied.** Nothing reconciles a second
  copy: no verb reads it, so it ages against the document `aide check`, `aide
  status` and `aide claim` all derive from, and a reader who finds the stale one
  first acts on a state that stopped holding several items ago. The rule sits on
  the always-on page for the reason the reading-cold rules do (§1) — it binds a
  session with no agent spec in play, and a human writing a README as much as a
  role writing a spec.
- **Why an unreadable row is an error, not a skip or a warning.** Every check
  that reads the table drops the row, and its cells cannot be trusted to be in
  position — a stray `|` shifts every one after it — so nothing can tell
  whether it held the ✅ a check exists to catch. Before #202 three of these
  tables dropped such a row without a word, and the check it would have fed
  went with it: a ✅ summary row over unfinished work, or a ✅ objective over a
  ❌ target, passed clean. Failing on the row, and naming its line, is the only
  reading that cannot pass an over-claim, and its cost is one edit.
- **Why deferral has a verb, and ⏸️ a rollup.** Issue #281: a project owner
  deferred a whole roadmap stage, and nothing could record it. `progress set`
  took no ⏸️, so the icon was a hand edit with no reason on the record; the
  rollup never produced ⏸️, so a deferred stage read 📋 like one nobody had
  started — in the file, in `aide status` and in the queue-planner's input;
  and `aide check` skipped a hand-set ⏸️ summary row without a word, a
  deliberate but unstated exemption. The verb now keeps the reason the way
  `reopen` does, the rollup yields ⏸️ once nothing else is open (still never
  ✅ over a ⏸️ bullet, which is #173's rule), and the silent skip became a
  warning. A hand-set ⏸️ is left standing rather than overwritten by the next
  unrelated `set`, because it is an owner's intent: `check` names it and a
  person resolves it, where a rewrite would have erased it unseen. No insight
  is captured on a deferral, unlike a reopening — postponing work is a
  decision about order, not a finding about the work.
- **Why a bullet with no marker is deferred by position.** Issue #336: a
  stage deferred by hand before 2.5.0, its bullets never itemised, warned for
  good. `set NNN deferred` addresses a bullet by its marker, typing ⏸️ over the
  bullet is the hand edit this section forbids, and restoring 📋 would have
  undone a real, dated deferral — so no remedy the warning named applied.
  Addressing the bullet by its place in the stage gives it the same write and
  trail. Only ⏸️, ❌ and the resume from ⏸️ are written that way, the
  decisions an owner makes about the bullet itself: an unmarked bullet has no
  item for work to move forward under, and itemising it is the
  queue-planner's step, not a status.
- **Why an unmarked bullet can be dropped.** Issue #362, from a consumer on
  2.25.0: a started stage held two shipped items, every acceptance box
  ticked, and one optional deliverable nobody had itemised. Deferring it —
  the one verb that reached it — held the stage at ⏸️ for good, since ⏸️
  stays out of the ✅ rule (#173), and nothing said whether the next stage,
  whose Dependencies named it, could be queued (§1 → `roadmap.md` now does).
  A deferral says the work is still wanted; the owner's decision was that it
  was not, and ❌ is the icon for that — there is nothing left to wait for, so
  the stage closes. The reason is required for the reason a deferral's is:
  the decision has to read cold. No insight is captured, as on a deferral — a
  drop is a decision about scope, not a finding about the work. `roadmap.md`
  is not touched, because a started stage is frozen there and its
  deliverables carry no status to mirror. A drop that would leave the stage
  all ❌ is refused because the rollup reads such a stage as 📋: two drops
  over a hand-deferred stage of two unmarked bullets (issue #362) left a
  stage the planner would queue, under a header still saying it was
  deferred, and `check` silent. Withdrawing a stage already has its cell —
  the ❌ summary row, which no rollup overwrites. The Objective row was named
  with it because an objective's rollup read its stages' bullets, not their
  summary rows, so a hand-held ⏸️ objective over the withdrawn stage still
  warned; since issue #382 the rollup reads the summary row, and an
  objective only withdrawn stages deliver derives to ❌ itself.
- **Why resuming has a verb, and a forward set refuses ⏸️.** Issue #380,
  from the status-model review alongside #362: the section said deferred work
  resumed "through any forward `aide progress set`" and an unmarked ⏸️ bullet
  "once it is itemised", and neither route led back into the loop. `aide
  claim` hands out 📋 items alone, so `set NNN in-progress` on a ⏸️ item never
  claimed left it 🚧 with no branch — `claim` said "none left" and exited 0,
  which a runner reads as the queue exhausted, while `aide status` counted an
  item to build and `aide sync --item` asked for a claim first. Three verbs
  disagreed, and the only way out was typing 📋 over the bullet. Itemising a
  ⏸️ bullet failed the other way: the planner's wiring never changes an icon,
  so the item was ⏸️ from birth, its queue counted done as it was written,
  `claim` found no open queue, and `check` was silent — and since 2.32.0 the
  same held for a ❌ bullet. 📋 is the one status every verb agrees is
  unstarted work, so resuming lands there, and the claim — or the runner's
  resume of a branch the item still has — takes it on. The reason is required
  for the reason a deferral's is: the decision has to read cold, beside the
  why of the deferral it undoes. A forward set is refused rather than taught
  to resume, because only `claim` makes the branch a 🚧 item is built on, and
  an item is held there only while its bullets are ⏸️ or 📋 — one with a ⏸️
  bullet beside started or settled work, which only a hand edit makes, is
  one `resumed` refuses, so the forward set stays its way out. The
  resume reaches ⏸️ only: leaving ❌ is a reversal of a decision against the
  work, not a postponement ended, and has its own verb (below). `aide
  merge` still ticks a ⏸️ item ✅ — a merge records work that landed.
- **Why an item is dropped by its verb, and leaves ❌ by another.** Issue
  #381, from the same review: 2.32.0 let an owner drop an un-itemised
  bullet, and nothing wrote ❌ on an item. An item abandoned at the
  validation-round cap stayed 🚧 after `aide ledger abandon`, an item carried
  to the next queue was hand-typed ❌, and one its owner decided against was a
  hand edit — the edit this section forbids. The other way was silent: ❌
  ranks lowest, so `set NNN in-progress` on a ❌ item, or `aide merge`'s
  tick, cleared a drop with no reason and no trail line, while `set NNN
  deferred` refused the same item. The drop verb is the positional one
  addressed by marker, refusing ✅ and an all-❌ stage for the same reasons.
  The forward set and the merge are refused rather than given a reason
  flag, as #380 refused them over ⏸️: only `claim` makes the branch a 🚧
  item is built on, so the way back lands on 📋, and the refusal is held to
  the items `restored` can take — one whose bullets are all ❌ or 📋 — so a
  ❌ bullet beside started or settled work, which only a hand edit makes,
  keeps the forward set as its way out. The restore is the owner's for the
  reason the drop is: it reverses a decision about scope, and the reason has
  to read cold beside the drop's. It has a positional form because the drop
  does; no insight is captured by either.
- **Why a withdrawn stage speaks for no objective.** Issue #382: a ❌ summary
  row excluded its stage from every stage comparison, but an Objective row
  was derived from its stages' bullets, so stage 1 ✅ beside a withdrawn
  stage 2 whose bullets still read 📋 held an objective both delivered at 🚧
  for good, and a ✅ typed there was an error — no verb and no hand edit of a
  derived cell could close it. Reading the summary row is what the stage
  comparisons already did; an objective every stage of which is withdrawn
  has nothing left to deliver it, which is ❌, the icon the drop rule above
  already asked for by hand.
- **Why every derived cell is compared, with none of the writer's restraint.**
  Issue #285: the sentence that a typed-over derived cell is drift `aide check`
  reports held for ✅ and ⏸️ only. A 🚧 over bullets all 📋, a 🔍 the rollup
  never yields, a ✅ header on a stage with no summary row and every Objective
  row — a ✅ one over an open stage included — passed clean. Diffing against
  the writer would not have closed it: the writer never downgrades a cell
  outside a reopen or a deferral and leaves a hand-set ⏸️ standing, both rules
  about when a verb may *write*, not about what a cell should say. So `check`
  takes the same derivation with neither, which is also why no sequence of
  verbs can write a file it then reports.
- **Why a rollup verb, and no hand-written cell.** Issue #454 gave the
  maintenance queues one standing stage that reopens at every batch, and
  asked for no engine change: a bullet added under a ✅ stage is the one
  write no verb rolled up, so the stage's cells stayed ✅ until the next
  `aide progress set`, and the batch wrote the computed 🚧 by hand — the one
  stage cell this section let a role write. Issue #459 retired that
  exception with `aide progress rollup`: the value is the same, and no role
  has to compute it. The alternatives were `check` reading a ✅ over a new
  📋 bullet as derivable, which would have left the file saying ✅ over open
  work, and a verb for wiring a bullet, which the planner's other edits to
  the same block would have had to go through too.
- **Why rollup writes over a hand-set ⏸️.** Once a bullet is added under a
  stage, a ⏸️ the rollup computed before it and one typed by hand read the
  same, and a maintenance stage that rolled up to ⏸️ over a deferred repair
  must reach the icon its rollup computes when the next batch reopens it —
  🚧 once any bullet has shipped or is in flight, else 📋; holding the ⏸️
  would leave that stage deferred over open work. The ⏸️ typed by hand is drift `aide
  check` already names, the deferral it stands for is recorded on the
  bullets or nowhere, and the verb prints each cell it writes. ❌ is a scope
  decision, not a rollup, so it stays.
- **Why the maintenance stage's section is shaped so.** The empty
  Deliverables block and the missing Acceptance block follow from §1 →
  `roadmap.md`, which gives the stage neither, and `—` in its Objectives
  cell from its delivering no objective.
- **Why a stage section needs its summary row.** Since issue #285 a stage's
  header and bullets are compared whatever the summary says, so a stage the
  summary left out was still checked — but the summary row is the one cell
  `aide check` reads a ❌ exclusion from, and the one it reads a stage's ✅
  from before holding a capability row to it, so a table that left a stage
  out silently under-reported a stage the file tracks.
  Found in the #285 audit and filed as issue #289; a warning, because a
  missing row under-reports rather than over-claims.
- **Why a shared marker is desugared.** One bullet carries one icon, so while
  items share a marker they share a status — and the first flip would
  otherwise carry the siblings with it.
- **Why a split copy has a verb, and why it rewords a ✅.** Issue #320: since
  #169 `aide check` reported the copies a split leaves and asked for each to be
  reworded, but no verb changed a bullet's words — `reword` took a criterion
  only — so the one repair was a hand edit of `progress.md`, the edit every
  role is steered away from. The criterion form refuses over a ticked box
  because its wording is what an attestation was made against. A bullet's icon
  is the item's status, written by `set` and `merge` from the item's state and
  not from the sentence beside it, so rewording the prose re-points nothing —
  and the ✅ copy is the one whose words describe a sibling's open work as
  done, so a verb that refused it would leave standing the one line that lies.
  `roadmap.md` is not mirrored: its deliverables carry no item marker, since
  items are born after it, in the queue.
- **Why no rollup ticks a box.** A derived tick is not an attestation. While
  `progress set` auto-ticked, a box deliberately left `[ ]` in a ✅ stage — the
  honest record of a criterion that shipped unmet — was silently flipped back
  on the next status change for *any* item in *any* stage, converting a
  recorded shortfall into a false claim that nobody had made.
- **Why the attestation is immutable.** The same rule `insights.md` runs on,
  and load-bearing for the same reason: an attestation that turns out to be
  wrong is the record, and a correction written beneath it teaches what a
  silent rewrite would erase. `amend`'s guard is structural rather than
  advisory — over-using it costs verbosity, never truth — and `retract`'s
  routing is what keeps the honest path the cheap one. `reword` refuses over a
  claimed box because rewording a criterion an attestation was made against
  would silently re-point that attestation at a different claim.
- **Why a measured outcome is not an Acceptance box.** It would hold the
  stage's honest record hostage to a result the work cannot promise. Needing
  more work than planned to hit a goal is normal; a `❌ Not met` target routed
  as a gap is how that work is planned explicitly. `aide status` prints every
  target not yet `✅ Met`, so the state stays visible even though the stage
  summary table does not carry it.
- **Why neither `amend` nor `retract` takes `--all`.** Each attestation was
  made separately and is corrected or withdrawn separately, and both refuse
  without a stated reason. `aide check` warns on every retracted criterion
  while `aide status` prints it, so a withdrawal stays visible instead of
  living only in one commit's diff. `aide progress -h` states all of this.
- **A range spanning more than 50** is read as a typo and contributes only
  its endpoints.
