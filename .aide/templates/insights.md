<!--
  AIDE insight inbox. Any role appends ONE line here, at any time, when it
  learns something true but out of scope for its task, and returns to that
  task. The engine creates docs/aide/insights.md from this file, byte for
  byte, the first time `aide check`, `claim`, `queue start` or `insights
  list` finds it missing; nobody copies it by hand.
  The rules — what is captured, what is immutable, what each verb does — are
  conventions.md §1 → insights.md and `python .aide/scripts/aide.py insights
  -h`. This comment is the shapes; the aide-template line below it names
  the template version this inbox was created from.

  Entry:
    - [ ] <type> — <one line> *(<provenance>, YYYY-MM-DD, engine X.Y.Z)*
  The date is required; the provenance before it and the engine version
  after it are free-form and optional. Conventional provenance spellings:
    *(item 099, 2026-07-26)*           one item
    *(items 099-101, 2026-07-27)*      a finding that spans several
    *(queue-014, 2026-07-26)*          planning or spec-authoring, before any item
    *(2026-07-26)*                     no item or queue to name
    *(item 099, 2026-07-26, engine 1.22.0)*   with the engine it was observed under
  Types:
    knowledge  — true fact worth documenting
    defect     — something is wrong and needs a fix item
    gap        — something is missing and needs planning
    automation — a recurring manual/agent action that code could replace
    framework  — belongs to AIDE itself, not this project

  A triaged entry, ticked in place with a pointer:
    - [x] <type> — <one line> *(item NNN, YYYY-MM-DD, engine X.Y.Z)* → <where it landed>
  A status trail, appended under an entry after triage, newest last:
    - [x] framework — <the original claim, never touched> *(2026-08-20)*
      - **2026-08-20** → aide-loop issue #50
      - **2026-10-11** → resolved in engine 1.16.0
-->
<!-- aide-template: insights 1 -->
# Insight Inbox

_Entries below, newest last._
