---
name: aide-create-vision
description: Create a comprehensive vision document for a new project.
---

# Create Vision

Create the project vision document — Step 1 of the AIDE loop. The vision is the
foundation every subsequent step (roadmap, progress, queues, items) derives from.

## User Input

$ARGUMENTS

## Instructions

### Existing vision check

Before creating, check if `docs/aide/vision.md` already exists.
- If it exists, **warn the user** and show a brief summary of the existing vision.
- Ask for confirmation before overwriting.
- If the user wants to update rather than replace, incorporate their input as
  amendments to the existing document.

### Asking posture

Vision authoring is **interactive regardless of `loop.clarify`** — that setting
governs `spec-author` on queued items, nothing else (`.aide/conventions.md` §5).
This is the one step of the loop where a human is present by construction; its
whole purpose is to capture what only they know. Ask until the mandatory
sections are grounded in the human's answers — never fill **Guiding
principles**, **Out of scope**, or **Success criteria** from assumption. A
wrong assumption here has no Assumptions block to be audited in and propagates
into the roadmap and every queue derived from it.

### Creating the vision

Write `docs/aide/vision.md` from the template **`.aide/templates/vision.md`** —
it defines the required structure. The four sections it marks `MANDATORY` —
Guiding principles, Goals & objectives, Out of scope, Success criteria — are
never dropped; what each one is read for is `.aide/conventions.md`
§1 → vision.md.

### The build posture

The header blockquote carries one optional line, `> **Posture:** prototype` or
`> **Posture:** durable`, and it decides how much the roadmap, the queue and
every item spec downstream build (`.aide/conventions.md` §1 → vision.md). The
line is optional and the two values are the whole set, never a spectrum, and
**a vision carrying no posture line is read as `prototype`** — so ask which one
this project wants once the mandatory four are grounded, and write the answer
into the header rather than leaving the default to stand unspoken. Write one of
the two exactly: a value outside the two is an `aide check` warning naming the
line rather than a silent fall back to the default.

Then apply the answer to this document's own optional sections as you draft
them — Technical architecture and Non-functional requirements. **Under
`prototype`, a Technical architecture or Non-functional requirements section is
written only where the human has committed to something it would record, and is
otherwise left out rather than drafted**; under `durable`, the project earns
those sections as it earns any other narrative. An empty heading is not the
smaller answer: leave the section out.

Requirements:

1. **Cover the scope, not the ceiling** — every objective, exclusion and
   success criterion the project actually has. The vision is the floor a build
   must meet; how much to build on top of it is the posture above, not the
   length of this document.
2. **Explain reasoning** — justify what is included and why.
3. **Document exclusions** — state what is out of scope and why.
4. **Be specific** — technology choices, constraints, and assumptions.
5. **Concise but specific** — short declarative sections, no filler; specificity
   goes into objectives and constraints, not narrative length.

### Output

Save to `docs/aide/vision.md`. Vision changes are framework-level: they land via
a reviewed PR, never a direct merge.
