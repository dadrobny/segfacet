### `vision.md` (the root document every other one derives from)

Governs `docs/aide/vision.md`: the four sections the loop reads, and what each
one is read for. It is authored only through the create-vision entry point,
interactively (§5); `validator`, `spec-author` and `queue-planner` read it, and
`aide check` lints it. `.aide/templates/vision.md` draws its shape and marks
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
