<!--
  AIDE queue template. Step 4. The next batch of work items, one file per
  queue. Parsed by aide.py (check, claim, queue tidy) and the status report.
  Mandatory shapes:
    - Each item: "### Item NNN: Short Title" + a description paragraph.
  Queue state is DERIVED from progress.md and never declared here; a
  "> **Status:**" note is decoration for human readers. What one queue may
  scope is step 4 of .aide/README.md; its cap is `loop.queue_cap` in
  aide.toml; item numbering and which queue is live are conventions.md §1 →
  queue-NNN.md.

  Fill-in conventions: `{{slot}}` = literal value; _italic line_ = guidance to
  read then replace. Delete this comment in the generated file,
  and keep the aide-template line below it.
-->
<!-- aide-template: queue 1 -->
# {{project-name}} — Work Queue {{nnn}}

> **Created:** {{yyyy-mm-dd}}
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).

---

## Scope of this queue

_Which roadmap stage/phase this batch delivers, and the milestone it completes._

**Prioritisation.** {{why these items, in this order; the critical path and
what is parallelisable}}

**Numbering.** Continues at the next free integer: **{{nnn}}–{{mmm}}**.

---

## Work items

_One "### Item NNN: Title" section per item — add as many as this batch needs
(see `loop.queue_cap` in `aide.toml`)._

### Item {{nnn}}: {{short title}}

{{one paragraph: scope and deliverables for this item}}. *Testable:*
{{how it is verified locally}}.
