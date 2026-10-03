### `roadmap.md` (the staged plan the queues are cut from)

Governs `docs/aide/roadmap.md`: what it must contain and which of its stages
may still change. It is authored and updated only through the create-roadmap
entry point (§5); `queue-planner` and `spec-author` read it, and `aide check`
and `aide progress reword` parse it. `.aide/templates/roadmap.md` draws its
shape; this section names that shape and fixes what the template cannot carry.

Mandatory (consumer in brackets):

1. **Objective → stage coverage table** — one row per vision objective, its
   first cell opening with the `G<n>` code; every G-code in `vision.md` maps
   to at least one stage. *(aide check, create-progress)*
2. **One `## Stage N — Title` section per stage**, numbered from 0, each with
   its Goal, Deliverables, Dependencies and Validation / acceptance blocks.
   The acceptance bullets are the ones `progress.md` mirrors as its boxes; a
   measured outcome is a `Target:` bullet instead, and §1 → `progress.md`
   says which is which. *(aide check, aide progress reword, create-progress,
   queue-planner, spec-author)*

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
the stage that has started.

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
stage. Either is the owner's decision, made through the create-roadmap entry
point (§5); the queue planner hands back rather than queue the dependent
stage.

`aide check` warns on a stage under way — 🚧 in `progress.md`, or with a 📋
item in an open queue — while an earlier stage its blocking Dependencies name
is ⏸️ or withdrawn: the two states no queue ends. A 📋, 🚧 or 🔍 earlier stage
is the ordinary wait, and is not named.

#### Rationale

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
