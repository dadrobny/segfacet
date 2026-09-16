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
