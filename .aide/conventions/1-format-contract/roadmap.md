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
