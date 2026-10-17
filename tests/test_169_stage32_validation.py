"""Tests for item 169 -- validate Stage 32 (selected-mode refinement) and
close Stage 20's deferred end-to-end validation deliverable.

Item 169's own Description explains the split: every stage-level claim
already has an in-suite check merged with the item that made it true
(``test_162``, ``test_163``, ``test_165``, ``test_168``, ``test_151``), and
the item's replay runs those by node id from a clean clone. This module
holds only what no merged test covers -- the live-state invariants behind
the numbers written into ``progress.md``, and the Stage 20 bullet sweep.

Per the item spec's Testing Strategy, this module once carried AC6, AC7 and
AC13 plus the named adversarial cases; item 236 retired them, as dated below.
AC1-AC5, AC11, AC12 and AC14-AC17 are Replay criteria: executed by the
builder and re-executed by the validator, their evidence recorded in the item's
Decisions log, not tested here. AC8, AC9 and AC10 are retired, as dated below.

2026-10-02 (item 203): ``test_ac8_...``, ``test_adv_refined_clause_...``,
``test_ac9_...`` and ``test_adv_bar_predicate_...`` are retired, with their
helpers and fixtures. Modes 2 and 3 are now signed at the bar, so the dated
Stage 20 clause and the empty at-the-bar set they compared against live state
are false by design; evidence in ``progress.md`` is a dated measurement and is
not rewritten.

2026-10-02 (item 204): ``test_ac10_stage32_criterion1_box_unticked_with_dated_reason``
is retired, with ``_STAGE_32``, ``_ANNOTATION_RE``, ``_TRAIL_LINE_RE`` and
``_box_text``. Item 204 ticks Stage 32's criterion 1 once modes 2 and 3 are
attested at the bar, so the assertion that the box stays unticked is false by
design.

2026-10-17 (item 236): ``test_ac6_status_count_clause_equals_live_derivation``,
``test_ac7_rung_count_clause_equals_live_derivation`` and
``test_ac13_no_stage20_bullet_deferred_and_item141_points_to_154`` are retired,
with ``test_adv_status_clause_missing_yields_no_match``,
``test_adv_status_clause_off_by_one_disagrees_with_live``,
``test_adv_deferred_bullet_anywhere_is_flagged`` and every helper left with no
caller. They pinned dated counts and a bullet's wording in the Stage 20 section
of ``progress.md``, which ``aide progress archive`` moves out (the 2026-09-16
precedent). The module now holds no test.

Discipline followed while it had them (Testing Strategy):

- Stage-section and acceptance-box location goes entirely through
  ``.aide/scripts/aide.py``'s own ``stage_section`` / ``acceptance_boxes``,
  loaded in-process (the ``test_150`` / ``test_161`` idiom). The one helper
  this module writes for that is continuation-line gathering, since neither
  of those functions returns box or bullet *text*, only line indices.
- No integer, mode id or rung name is written into this module as a literal
  expectation -- every comparison is derived from ``SPECIFICATION``,
  ``MODE_SIGN_OFFS``, ``derive_status`` and ``derive_mode_rung``, recomputed
  live.
- No ``aide check`` warning count, suite total, engine version or
  severity-ladder constant is pinned here -- those are dated measurements
  that legitimately move and live in ``progress.md``'s evidence and in the
  item's Decisions log.
- No ``insights.md`` entry is pinned.
- No git history, clone, network access or environment profile is needed.
- Every adversarial case is an in-memory ``progress.md`` text or a
  constructed sign-off mapping passed to the same in-process helpers; none
  writes a file or touches the shipped ``MODE_SIGN_OFFS``.
"""
