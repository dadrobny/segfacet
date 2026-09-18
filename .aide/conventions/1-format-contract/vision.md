### `vision.md` (the root document every other one derives from)

Governs `docs/aide/vision.md`: the four sections the loop reads, what each one
is read for, and the optional build posture. It is authored only through the
create-vision entry point, interactively (§5); the create-roadmap entry point,
`queue-planner`, `spec-author` and `validator` read it, and `aide check` lints
it. `.aide/templates/vision.md` draws its shape and marks
the four `MANDATORY`; everything else in it is project narrative.

Mandatory — a vision without any of these gives a downstream role nothing to
check against (consumer in brackets):

1. **Guiding principles** — one bullet per principle, each saying what it
   constrains. The validator checks every implementation against them, and an
   item that contradicts one fails validation. *(aide check, validator,
   spec-author)*
2. **Goals & objectives** — a table whose rows open with a `G<n>` code. The
   codes are the identities `roadmap.md`'s coverage table and `progress.md`'s
   objective rows trace to. *(aide check, create-roadmap, create-progress)*
3. **Out of scope** — one bullet per exclusion, with its reason. The validator
   fails an item whose work contradicts it. *(aide check, validator)*
4. **Success criteria** — observable statements of when the project is done.
   Every roadmap stage traces back to at least one. *(aide check,
   create-roadmap)*

**A missing mandatory section is an `aide check` warning**, named per section,
and so is an objectives table with no `G<n>` row. A warning, not an error: a
repository may carry a vision older than the check.

**The mandatory sections are never filled from assumption.** §5 states the
asking posture; a section the human has not grounded stays open and is asked
about, not drafted.

**The header blockquote may carry a build posture — `> **Posture:** prototype`
or `> **Posture:** durable`.** The line is optional and the two values are the
whole set, never a spectrum; **a vision carrying no posture line is read as
`prototype`**, and a value outside the two is an `aide check` warning naming
the line rather than a silent fall back to the default. The create-vision entry
point asks for it once the mandatory four are grounded. *(aide check,
create-vision, create-roadmap, queue-planner, spec-author, spec-reviewer)*

**The posture also bounds the vision's own optional sections.** Under
`prototype`, a Technical architecture or Non-functional requirements section is
written only where the human has committed to something it would record, and is
otherwise left out rather than drafted; under `durable`, the project earns those
sections as it earns any other narrative. This one is the vision's own rule
rather than a row of the table below: the create-vision entry point asks for the
posture, it does not read one.

**The posture says how much to build, and the roles that apply it are the
three that author a document from the vision.** `spec-reviewer` reads the line
too, only to hold a batch of specs it did not write to the `spec-author` row.
It is not a guiding principle and no verb branches on it: the validator's vision-fit check measures against Guiding
principles and Out of scope, so it is unchanged, and `builder` and `test-writer`
never read the posture at all — the item spec carries its consequences. Each of
the three applies its own row and nothing beyond it:

| Role | `prototype` (the default) | `durable` |
|---|---|---|
| create-roadmap | fewer stages: a stage only where a success criterion needs one | stages and sections as the vision earns them |
| queue-planner | no preparatory or "for later" items: an item is queued only where a success criterion, a deliverable, or a justified sibling in the same queue needs it | foundations a later stage will use may be queued |
| spec-author | acceptance criteria for the item's own deliverable only, adversarial cases only where the Testing Strategy names a failure mode, and Implementation Steps that reuse an existing helper before writing one and add no dependency | interfaces may be pinned ahead of need, and broader cases named |

What the `spec-author` row means for a single criterion — which consumers
count under each value — is §1 → items.md, read with this table, not beyond it.

#### Rationale

- **Why these four and not the rest.** They are the only sections a role reads
  as a *test*: the validator's vision-fit check is Guiding principles plus Out
  of scope, and the roadmap's traceability is the G-codes and Success
  criteria. Overview, users, architecture and the rest inform a reader and
  gate nothing. Before issue #217 that split was stated only by the template's
  `MANDATORY` annotations and the create-vision skill, so a vision authored
  anywhere else had no rule saying the four were required.
- **Why a warning.** Root documents predating the check exist in real
  consumers, and an unattended run must not start failing over a document
  none of its items touch — the queue-boundary human reads warnings.
- **Why a posture line at all.** Nothing in the loop said *how much* to build,
  so every downstream role read the vision as a ceiling to reach rather than a
  floor to meet. Measured across consumers on engine ≤ 1.54.1 (issue #241):
  exhaustive visions, item specs whose acceptance criteria pinned more than the
  deliverable needed, and suites in the thousands within a few queues. The
  create-vision entry point asked to *be exhaustive*, and the template invited
  an architecture and a non-functional-requirements section whatever the
  project was, so the pressure was in the loop's own text. One line in the
  document every other one derives from is where a role already looks.
- **Why the optional sections are the vision's own rule.** The sections the
  posture bounds — architecture, non-functional requirements — exist only in
  this document, so a row of the table would name a reader that has none: the
  three roles in it read a vision they did not write. The restraint has to bind
  where the section is authored, and drafting one nobody committed to is the
  same defect as filling a mandatory section from assumption, two paragraphs up.
- **Why two values, and why `prototype` is the default.** Current behaviour is
  effectively `durable`, so absence had to mean the other value for the default
  to do any work: a consumer whose vision carries no line gets the smaller
  build on its next update, through prose alone — no verb changes behaviour,
  and adding the line restores what it had. A spectrum, or a third value, is a
  number each role would read differently; two values map onto rows a role can
  act on, which is the only thing the posture is for.
- **Why an unknown value is a warning and an absent line is not.** A typo
  silently meaning `prototype` would build less than the human asked for and
  say nothing, which is the one failure the line itself cannot show; absence is
  the default and warning about it would ask every vision to state the value it
  already has.
