<!--
  AIDE vision template. Step 1 of the loop. The single source of truth the
  roadmap, progress tracker, and every work item derive from.
  Mandatory core: the four sections marked MANDATORY below. What each is read
  for is `.aide/conventions.md` §1 → vision.md, which also fixes the optional
  `**Posture:**` line of the header blockquote — `prototype` or `durable`, and
  what each one asks of the roles downstream. Everything else is project
  narrative: keep it concise and specific, no filler.

  Two fill-in conventions (both keep the rendered file readable AND let
  `aide check` catch anything left unfilled):
    - `{{slot}}`     — a literal value to substitute (title, date, a number).
    - _italic line_  — authoring guidance to read, then replace with real prose.
  Delete this comment block in the generated file, and keep the
  aide-template line below it; the inline MANDATORY annotations further down
  are for framework maintainers and agents, not readers of the finished
  vision — leave those in place.
-->
<!-- aide-template: vision 2 -->
# {{project-name}} — Project Vision

> **Status:** Draft v1 · **Created:** {{yyyy-mm-dd}}
> **Posture:** prototype
> Step 1 of the AIDE loop · the root document: [`roadmap.md`](roadmap.md),
> [`progress.md`](progress.md), every queue and every work item derive from this.

_Delete this line. Posture: `prototype` or `durable`, or omit the line;
`.aide/conventions.md` §1 → vision.md says what each asks of the roadmap, the
queues and the item specs._

---

## 1. Overview

_What is being built and why, in a few sentences — the problem it solves._

## 2. Guiding principles  <!-- MANDATORY: validator checks implementation against these -->

_One bullet per principle. Add as many as the project needs._

- **{{principle name}}.** {{what it constrains, and why}}

## 3. Goals & objectives  <!-- MANDATORY: each G-code is traced by roadmap + progress -->

_One row per objective._

| # | Objective | Measurable outcome |
|---|-----------|--------------------|
| G1 | {{objective}} | {{how it is measured}} |

## 4. Users & use cases

_Who uses it and the concrete workflows they need._

## 5. Core features

_The capabilities that deliver the objectives. Group by area; be specific._

## 6. Technical architecture

_Language/runtime, key libraries, packaging/deployment, data formats, the
high-level data flow. Whether this section is written at all follows the
Posture above — `.aide/conventions.md` §1 → vision.md._

## 7. Non-functional requirements

_Portability, determinism, performance, reproducibility, maintainability —
whichever the project actually commits to. Written or omitted per the Posture
above — `.aide/conventions.md` §1 → vision.md._

## 8. Constraints & assumptions

**Constraints** — {{hard limits: platforms, versions, dependencies}}

**Assumptions** — {{what must hold for the design to work}}

## 9. Out of scope  <!-- MANDATORY: validator flags work that contradicts this -->

_One bullet per exclusion, each with a one-line reason._

- {{excluded item}} — {{one-line reason}}

## 10. Success criteria  <!-- MANDATORY: the project is "done" when these hold -->

_Observable, testable statements — one per criterion._

1. {{success criterion}}
