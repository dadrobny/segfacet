### `roadmap.md` (the staged plan the queues are cut from)

Governs `docs/aide/roadmap.md`: what it must contain and which of its stages
may still change. **It has two writers, both the owner's.** The create-roadmap
entry point (§5) authors it, and re-stages it from a changed vision; an
amendment the owner agrees to — a stage added, a 📋 Planned stage reworded, a
Backlog bullet — is applied in the owner's own session instead, the feedback
loop's included, with no need for that entry point. Both are held to the
started-stage freeze below, and both land through the merge policy's reviewed
PR (`.aide/README.md`). `queue-planner` and `spec-author` read it, and
`aide check` and `aide progress reword` parse it. `.aide/templates/roadmap.md`
draws its shape; this section names that shape and fixes what the template
cannot carry.

Mandatory (consumer in brackets):

1. **Objective → stage coverage table** — one row per vision objective, its
   first cell opening with the `G<n>` code; every G-code in `vision.md` maps
   to at least one stage. *(aide check, create-progress)*
2. **One `## Stage N — Title` section per stage**, numbered from 0, each with
   its Goal, Deliverables, Dependencies and Validation / acceptance blocks.
   The acceptance bullets are the ones `progress.md` mirrors as its boxes; a
   measured outcome is a `Target:` bullet instead, and §1 → `progress.md`
   says which is which. The maintenance stage (below) is the one whose
   Deliverables list nothing and which has no acceptance bullets. *(aide
   check, aide progress reword, create-progress, queue-planner, spec-author)*

**The coverage table is complete both ways.** Every G-code in `vision.md` has
a row — an objective withdrawn from scope too, for as long as the vision lists
its code — and every stage a row names has a `## Stage N` section of its own
here. A stage held only as a bullet under a grouped heading has none: the
objective is then mapped to a stage the plan does not lay out. `aide check`
warns on a G-code with no row and on a named stage with no section.

**An existing roadmap is updated, never regenerated.** Read `progress.md`
first: it is the only record of which stages have started.

**A started stage is not re-edited.** A stage is started once `progress.md`
shows it at anything but 📋 Planned — ✅, 🚧, 🔍, ⏸️ and ❌ alike. Its goal,
deliverables, dependencies and acceptance criteria stay exactly as written;
only a 📋 Planned stage may be edited freely.

**One change reaches a started stage, and only through its verb.** An
acceptance criterion nothing has yet been claimed against is reworded with
`aide progress reword`, never by hand: the verb keeps this file and
`progress.md` in step, and §1 → `progress.md` states when it refuses.

**New or changed scope enters as a new stage, appended after the last.** Work a
started stage turns out to need arrives the same way, or through the queue as
§1 → `progress.md` routes a `❌ Not met` target — never as a bullet added to
the stage that has started. The maintenance stage (below) is the one
exception, and only in `progress.md`: its bullets are the maintenance
queues' items, added under it after it has started.

**A stage's blocking Dependencies name only earlier-numbered stages.** Stages
close in number order, so a stage waiting on a later one cannot close when its
turn comes. Reorder the 📋 Planned stages involved so the dependency comes
first; where a started stage stands in the way, since it keeps its number and
its text, defer the dependent stage instead — ⏸️ in `progress.md`, the one
forward dependency tolerated. The rule binds the blocking slot only: a later
sentence about ordering without blocking may name any stage. `aide check`
warns on a forward dependency whose stage is not ⏸️.

**A blocking dependency on an earlier stage is met only once that stage is
✅.** A 📋, 🚧 or 🔍 earlier stage still has work to land, so the dependent
stage is queued behind it — after its queue, or in the same one where a phase
fits the cap. A ⏸️ earlier stage does not meet the dependency either, and its
deferred work waits on its owner's decision, not on the next queue: the
dependent stage waits until the owner resumes the deferred bullets, or drops
those the stage turns out not to need (§1 → `progress.md`), and the earlier
stage closes ✅. The ⏸️ that excuses a
*forward* dependency above excuses the dependent stage, never the stage it
waits on.

**A blocking dependency on a withdrawn stage is never met** — a stage whose
`progress.md` summary row is ❌ never becomes ✅ — **so the dependent stage is
re-planned, not queued.** While it is 📋 Planned, its Dependencies are
reworded here to drop the withdrawn stage, or name what replaces it; started,
it is frozen, so it is withdrawn too, or what it still needs enters as a new
stage. Either is the owner's decision; the queue planner hands back rather
than queue the dependent stage.

`aide check` warns on a stage under way — 🚧 in `progress.md`, or with a 📋
item in an open queue — while an earlier stage its blocking Dependencies name
is ⏸️ or withdrawn: the two states no queue ends. A 📋, 🚧 or 🔍 earlier stage
is the ordinary wait, and is not named.

**A roadmap holds at most one maintenance stage, and needs none.** It is the
home of the maintenance queues' items (§1 → `insights-maintenance-queue.md`):
a `## Stage N — Title` section like any other, added once by either of the
file's two writers (the opening of this section) and frozen once started,
which differs from a feature stage in what it carries.

**The maintenance stage is the stage titled exactly `Maintenance`** — its
heading reads `## Stage N — Maintenance`, the template's, here and in
`progress.md` — and no other stage takes that title. Nothing else marks it:
a stage that holds repairs under any other title is a feature stage.
**A started stage already run as a standing maintenance stage becomes the
maintenance stage by one retitle to `Maintenance`**, the owner's, made by
either of the file's two writers, in its heading here and in its `progress.md` header and
Stage summary row; it is the one edit the freeze allows a started stage's
heading, and it changes nothing else in the stage.

**A stage queue never takes the maintenance stage as its next stage.** It
has no roadmap deliverable to queue, so the queue's author choosing the next
stage passes over it; only a maintenance queue writes under it. A stage
appended after it is an ordinary stage, queued in its turn.

What it carries:

- **Its Deliverables are the maintenance queues' items, so the roadmap lists
  none.** Each maintenance queue adds one `progress.md` bullet per item under
  the stage's section. It is the one stage whose `progress.md` bullets keep
  growing after it has started; its text here does not.
- **It has no blocking Dependencies, and no stage's blocking slot names it.**
  A stage that reopens at every batch would never meet a dependency on it.
- **No Objective row names it.** Maintenance repairs shipped work and
  delivers no objective, and a row naming the stage would flip to 🚧 at every
  reopen.
- **It has no acceptance criteria of its own.** Each maintenance item's spec
  carries its own. With no box at stage level nothing goes stale between
  batches, and `aide check --queue` never reports a queue-end need for the
  stage: a stage with no unticked box has none.
- **It reopens and closes by rollup.** It reads 🚧 while a maintenance
  queue's items are open and ✅ once they ship; the batch that adds its
  bullets rolls it up with its verb (§1 → `insights-maintenance-queue.md`).

A maintenance stage written earlier with acceptance criteria of its own, and
retitled so, keeps them, since it is frozen: its boxes record its first close, and nothing
re-attests them per batch.

`aide check` warns on a second stage titled `Maintenance`, on a coverage row
or `progress.md` Objective row naming the maintenance stage, on a stage's
blocking slot naming it and on its own blocking slot naming any stage, and
on acceptance bullets under it while `progress.md` shows it at nothing but
📋 Planned — a started one may be one retitled with its criteria, so it is
never named.

**An optional `# Backlog` section, after the last stage, holds scope not yet
ready to plan.** It is not a stage: its heading is `# Backlog`, never a
`## Stage N`, so it ends the last stage's section and no reader takes a
bullet of it for that stage's. It is edited as the rest of this file is,
by either of its two writers, and the started-stage freeze does not reach it.

- **Ideas only.** A bullet is a piece of scope in a sentence or two — never a
  defect, a status icon, a trail, a date, an owner or an annotation such as
  `→ Stage N`. A defect stays in the inbox (§1 → `insights-triage.md`); a
  policy belongs in `vision.md`'s guiding principles; a decision about a stage belongs in that
  stage.
- **A bullet that came from the inbox cites its entry as `insight <ID>`**,
  which `aide check` resolves like any citation (§1 → `insights.md`). Only a
  `gap` entry arrives this way, moved by the owner.
- **The queue planner never queues from it.** A queue is cut from stages; a
  Backlog bullet reaches a queue only once it is a stage.
- **A bullet leaves in one of two ways**: promoted into a new stage appended
  after the last, as any new scope enters (above), or deleted by the owner.
  Promotion deletes the bullet in the same edit, so nothing reads in two
  places.

#### Rationale

- **Why two writers, and one rule over both.** This section once said the
  file was authored and updated only through the create-roadmap entry point,
  while the feedback loop, since 2.41.0 (issues #392, #359), applied an
  agreed amendment in the session and told the user not to rebuild a
  document to amend it; the owner edits added in 2.44.0 and 2.45.0 — the
  maintenance stage, its retitle, a Backlog move — were routed through the
  entry point and so inherited the contradiction (issue #461). The entry
  point exists for what an amendment does not need: staging a plan from a
  vision, asking until each stage is grounded. A one-stage edit the owner has
  already agreed to needs none of that. What protects the plan is the freeze
  and the reviewed PR, so those bind both routes alike.
- **Why a started stage is frozen.** Queues were cut from it, items were
  specified against its deliverables, and `progress.md` mirrors its criteria;
  editing it re-points all of that at a plan nobody built to, and a shipped
  stage whose deliverables grew after the fact reads as incomplete work that
  never existed. Before issue #217 the rule lived only in the template header
  and the create-roadmap skill, so a reader of neither — a runtime without
  that skill, a human editing the file — met no statement of it.
- **Why every non-Planned icon counts as started.** A ⏸️ or ❌ stage may carry
  items that were claimed before it stopped, and the icon alone cannot say
  whether any were; freezing on the icon costs one new stage where editing
  might have been safe, and never the other way round.
- **Why `reword` is the exception.** A criterion no attestation has been made
  against records nothing yet, so rewording it rewrites no history; the verb
  exists so that the edit lands in both mirrors at once or in neither.
- **Why a forward dependency is named at all.** In one consumer a stage's
  Dependencies read `Depends on Stage N+2; … may be delivered after it`, and a
  queue cut from it said outright that it did not close the stage: the work
  was queued toward a closure that could not happen in number order. Nothing
  said so until the owner swept the roadmap by hand, deferring that stage and
  removing every other forward dependency (issue #282).
- **Why a warning, not an error.** Roadmaps written before this rule exist,
  and a started stage is frozen, so an error would fail a document whose only
  remaining fix is a deferral — a decision about scope for the human at the
  queue boundary, who reads warnings, and not one a check may force on an
  unattended run that passed the day before.
- **Why ⏸️ exempts the stage.** A deferred stage is out of the number order
  already: nothing expects it to close in its turn, so the reason for the rule
  does not reach it. The consumer's own swept roadmap kept exactly one forward
  dependency, on a stage it had deferred. 🚧 and 📋 are not exempt — a stage in
  either is still expected to close in its turn.
- **Why a ⏸️ earlier stage does not meet a dependency.** Issue #362: in a
  consumer on 2.25.0 a started stage's two items had shipped and its one
  optional, never-itemised deliverable was deferred, so the stage read ⏸️ —
  and a later stage's Dependencies named it. The section tolerated a ⏸️ stage
  as a forward dependency and said nothing about a ⏸️ earlier one, and the
  queue planner had no rule for reading it. A ⏸️ stage is one whose remaining
  work is still wanted, later, so a stage that depends on it would build on
  work not yet done; reading it as met would let the plan run ahead of the
  stage it names. A 📋, 🚧 or 🔍 earlier stage is the ordinary case — a queue
  lands its work, the next one or the same one for a phase — so queueing
  behind it is all the rule asks; ⏸️ is the one state that waits on a
  decision rather than a queue, which is why it needs the owner. The owner's
  remedy for a deliverable never needed is the drop route, which closes the
  stage ✅.
- **Why a dependency on a withdrawn stage re-plans its dependent.** Issue
  #382: the ✅-only rule above left a stage whose dependency had been
  withdrawn blocked for good, and no rule said so — a ❌ stage has nothing
  left to land, so neither waiting for a queue nor an owner's resume can
  meet it. The dependency was written against work that will not exist, so
  only the plan can answer what the dependent stage needs instead; a 📋 stage
  is the one the roadmap lets be edited, which is why rewording is offered
  there and withdrawal or a new stage past it. The planner hands back
  because the answer changes `roadmap.md`, which it never edits.
- **Why the check names a stage under way over an unmet dependency.** Issue
  #384: the two rules above bound the planner, which hands back on them, but
  nothing checked them, so a queue cut over a ⏸️ or withdrawn dependency by
  hand, or by a runtime without the planner's rule, built on work that was not
  coming and `aide check` passed it clean. Under way, not merely named: a 📋
  stage queued nowhere is doing what the rule asks — waiting — and warning on
  it would fire on every roadmap with a deferral in it. A warning, for the
  forward-dependency reason above: a started stage is frozen, and what follows
  is the owner's decision.
- **Why an item reads a ⏸️ dependency the other way.** An item's
  `## Dependencies` are met by a ⏸️ item, which "leaves the queue's way"
  (§1 → `items.md`), while a stage's are not met by a ⏸️ stage. The two act
  at different moments. The item rule orders claims inside a queue already
  planned and approved, during an unattended run with no owner to ask; a
  deferred item that still blocked would stall every item behind it until the
  queue ends. The stage rule acts when the next queue is planned, before any
  item is built, so waiting on the owner's decision costs one hand-back
  rather than a stalled run. A dependent item built past a
  deferred one is the price, paid in the open: the deferral's reason is on
  the deferred item's trail.
- **Why the coverage table is checked for completeness.** The check said
  only that the table existed, so a G-code no row mapped — an objective no
  stage was planned to deliver — and a row naming a stage the roadmap never
  laid out both passed clean. Both were found in the audit for issue #285,
  whose Objective-row check is the `progress.md` counterpart of the second,
  and filed as issue #289. A warning, because a missing row under-reports
  rather than over-claims.
- **Why a withdrawn objective keeps its row.** Its code is never reused, and
  the row is where the roadmap says which stage delivered what it did before
  it left scope; a code the vision lists and the roadmap does not is
  indistinguishable from one it forgot.
- **Why the blocking slot only.** The template keeps the slot to blocking
  stages and puts ordering without blocking in a sentence after it
  (`None. Independent of Stage 17 — may be queued in either order.`); reading
  the whole block would flag exactly the phrasing the template recommends.
- **Why one standing maintenance stage.** Before issue #454 the maintenance
  queue had no stage to put its bullets under, and two consumers improvised
  opposite answers. One ran a single standing stage through six closes with
  no `aide check` warning. The other created a new stage per maintenance
  batch, and each needed an owner amendment to the roadmap — the
  planner cannot write a stage — and was mapped to objectives it did not
  deliver. A stage per batch is the rejected alternative for both reasons,
  and for inflating the plan. So is a `## Maintenance` section of
  `progress.md` that is not a stage: rollup, `set`, `claim`, `merge`,
  `check`, `status`, gate reach and the ledger's stage cell all key on stage
  sections, so it would be a large engine change for the same behaviour.
- **Why an exact title identifies it, and the stage queue passes it over.**
  The roadmap is frozen once a stage starts and the engine reads no marker
  for it, so the title is the one thing every role reads the same way with
  no judgement: the template writes it, and a planner comparing it decides
  nothing. Without the pass-over, a feature stage appended after the
  maintenance stage leaves it as the lowest unfinished stage, and a planner
  queueing "exactly the next stage" would find no deliverable to queue
  there.
- **Why a retitle, and not a looser match.** A title only starting with
  `Maintenance`, or matched by meaning, would count a project's several
  per-batch maintenance stages as several, and would ask a planner to judge
  a title. A consumer that already runs one standing stage under another
  title would otherwise have to add a second one beside it and split the
  repair history across two stages; one retitle by the owner keeps the
  history in one place and changes nothing the freeze protects.
- **Why the maintenance stage has no criteria.** The standing stage above
  carried four acceptance boxes. They were attested at its first two closes
  and never again, so from the third batch on they asserted nothing about
  the work under them. And one repair was filed under an unrelated feature
  stage, so as not to reopen the maintenance stage without a planned
  validation. Criteria on the item, where they are checked when the item is
  built, remove both: nothing at stage level to go stale, and no queue-end
  item to plan for.
- **Why no Objective row and no dependency.** Both would read the stage's
  status, and its status moves at every batch. An Objective row would report
  a delivered objective as 🚧 whenever a repair is open; a blocking
  dependency on it would be met only between batches, by accident.
- **Why the engine recognises the stage, and only to warn.** Its behaviour
  needs nothing new: a stage section with no acceptance box raises no
  queue-end need, its rollup is any stage's, and the ledger's `maintenance`
  kind comes from the insight tick. Issue #454 left the prose rules above
  unchecked, since a warning would need the engine to tell the stage apart,
  until drift was seen. The exact title it fixed is that key, so issue #459
  turned the rules into warnings rather than wait. A warning, for the
  forward-dependency reason: a started stage is frozen, and the fix is the
  owner's. The blocking slot is the one #282 reads, so an ordering sentence
  after `None.` names the stage freely. Criteria are named only on a stage
  not yet started: a started one may be one retitled with its criteria,
  which keeps them, and nothing in the file tells that one from a stage
  given criteria by mistake.
- **Why a stage written earlier keeps its criteria.** A started stage is
  frozen, and its ticked boxes are attestations of its first close; dropping
  them would rewrite history, and re-attesting them per batch is the drift
  the rule above removes.
- **Why a Backlog, and why ruled.** Scope the owner wants recorded but is
  not ready to plan had no home but a stage, and a stage is planned the moment
  it is written. One consumer invented a backlog section without rules, and
  it drifted: a settled project-wide policy that belongs in `vision.md`'s
  guiding principles, a vision question, and an adjudication tied to a stage
  that has since closed all sat in it (issue #455). The rules keep it a list
  of unplanned scope and nothing else.
- **Why ideas only, and never a defect.** The same consumer's `Carried
  defects` list shows what a ruleless holding list becomes for defects: of
  nine entries ticked out of the inbox into it, three were fixed without the
  list saying so, one was absorbed, and five were still open six weeks later
  but invisible to `insights list --open` (§1 → `insights-triage.md`). A
  status or a `→ Stage N` annotation is the same drift in another form: it is
  a second record of what `progress.md` records.
- **Why not a tracker.** The framework is deliberately not a
  project-management or issue-tracking product, so the section carries no
  status, order, assignment or burndown: it is unplanned scope, kept in the
  document that owns scope. A forge's tracker is the alternative, and a
  project with no forge (§4) has none.
- **Why the `# Backlog` heading needs no engine change.** Every reader of a
  stage section ends it at the next `#` or `##` heading, so the last stage's
  Validation / acceptance block never takes in a Backlog bullet; one consumer
  carried such a section for two months with no `aide check` warning.
