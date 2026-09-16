<!--
  AIDE roadmap template. Step 2. Breaks the vision into incremental,
  demonstrable, locally-deployable stages (~1 week each), numbered from 0.
  Derived from vision.md.
  Mandatory core:
    - Objective -> stage coverage table   -> progress.md mirrors it; every G-code mapped
    - One "## Stage N" section per stage with Goal / Deliverables / Dependencies /
      Validation-acceptance                -> the queues are cut from these sections, and
                                              progress.md is generated from them
  Which stages may still be edited once the loop starts is
  `.aide/conventions.md` §1 → roadmap.md. Concise and specific.

  Fill-in conventions: `{{slot}}` = literal value; _italic line_ = guidance to
  read then replace. Delete this comment in the generated file,
  and keep the aide-template line below it.
-->
<!-- aide-template: roadmap 1 -->
# {{project-name}} — Development Roadmap

> **Status:** Draft v1 · **Created:** {{yyyy-mm-dd}}
> Step 2 of the AIDE loop · derived from [`vision.md`](vision.md) · its stages
> are mirrored by [`progress.md`](progress.md) and scoped into the queues.

---

## Strategy

_The sequencing logic: what is built first and why; where the phase boundaries
are; which objectives each phase prioritises._

### Objective → stage coverage  <!-- MANDATORY: every vision G-code maps to a stage -->

_One row per vision objective._

| Objective | Delivered by |
|-----------|--------------|
| G1 {{short}} | Stage {{n}} |

### Stage dependency graph

_Optional ASCII graph of stage dependencies._

```
0 ─► 1 ─► 2 ─► …
```

---

## Stage 0 — {{title}}  <!-- MANDATORY shape: one section per stage -->

**Goal.** {{one paragraph: the demonstrable capability this stage delivers}}

**Deliverables.**

_One bullet per concrete artifact or capability._

- {{deliverable}}

**Dependencies.** {{blocking stage numbers, or "None"}}

_The slot holds **blocking** stages only: what must be complete before this
stage can start. Anything about *ordering without blocking* is a separate sentence
after it, e.g. `**Dependencies.** None. Independent of Stage 17 — may be queued
in either order.`_

_Two phrasings a planner can act on, and one it cannot:_

- _**Independence** — "independent of Stage N; may be queued in either order."
  Tells the planner the two need nothing from each other, so it may queue them
  in any order, or as one batch if they fit the cap._
- _**Ordering without blocking** — "queue before Stage N, whose retuning is
  safer once this exists." A preference the planner can honour, with its reason._
- _**Avoid "run alongside" / "in parallel"** for stages. One queue is live at a
  time (the queue boundary is the human checkpoint), so a planner cannot act on
  it and will queue sequentially regardless — the phrase only makes the roadmap
  and the queues look like they disagree. Note this is about **stages**; saying
  two *items within one queue* may be worked in parallel is accurate and useful._

**Human gate.** _OPTIONAL — delete unless this stage's work waits on a
decision or an out-of-band prerequisite a person must supply (data access, a
sign-off, an authorised spend). Name what must be decided; the authoritative
row goes in `progress.md`'s `## Human gates` table, usually with
`Blocks: stage N`. A gate written only here blocks nothing._

**Validation / acceptance.**

_One bullet per observable check **of the built thing** — these become the
progress.md acceptance boxes for this stage. A measured outcome the stage
cannot guarantee (conventions.md §1 → progress.md says what counts) is not an
acceptance bullet: prefix it `Target:` and mirror it into progress.md's
"Outcome targets" table._

- {{observable check that the stage is done}}
- Target: {{measured result the stage aims for}}  <!-- optional -->

---

_Repeat "## Stage N — Title" per stage. Group stages into phases with a
`# Phase N — name` header above the first stage of the phase, if useful._
