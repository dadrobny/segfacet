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
   `Status` a single icon. *(aide check, status report, queue-planner)*
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
over a derived cell is drift `aide check` reports.

**Deferral is recorded on the item, with its reason, and the stage follows.**
Postpone an item with `aide progress set NNN deferred --reason …`, never by
typing ⏸️ over a bullet or a stage: the verb keeps the why on the bullet's
trail, and a stage whose only open work is deferred rolls up to ⏸️ by itself —
never to ✅. Deferred work resumes through any forward `aide progress set`. A
bullet no item marker names is deferred by its place instead, with `aide
progress set --stage N --deliverable K deferred --reason …`, K counting the
stage's deliverable bullets from 1; it resumes once it is itemised. A
⏸️ stage header, summary row or Objective row the rollup does not compute is a
hand edit that stands until a verb moves a bullet of that stage, and `aide
check` warns on it for as long as it disagrees, as it does on a stage that
rolls up to ⏸️ under a cell that says otherwise. Defer the stage's open
bullets, each by the form that addresses it, or restore the icon the rollup
computes, and the warning ends. A ❌ cell is outside the
comparison, and a ❌ summary row takes its stage's header with it: its bullets
no longer speak for the stage.

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
- Marking a target `❌ Not met` is a *finding*, so route it like one: append a
  `- [ ] gap — …` line to `insights.md` in the same edit. The follow-on
  deliverables then enter through the queue, never by retro-editing a closed
  stage's deliverable list.

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
  trail. Only ⏸️ is written that way: an unmarked bullet has no item for work
  to resume under, and itemising it is the queue-planner's step, not a status.
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
