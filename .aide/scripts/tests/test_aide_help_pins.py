"""The `-h` description blocks, pinned to the code that makes them true.

`aide <verb> -h` is the **authoritative** statement of what a verb does: the
sections stopped restating verb mechanism and point here instead
(`conventions.md` §1, and the copies rule's rung 1 — "the text is mechanism the
code owns"). An authoritative statement with nothing holding it to the code is
the shape that shipped a two-release-stale rollup in a template header, so a
prose statement of behaviour the code owns is pinned by a test that **exercises
the code**, never by a second prose copy to quote against.

`test_progress_help_states_the_rollup_the_code_applies` (issue #192) is the
model and the seventh entry below: it transcribes the help sentence as a
predicate and compares it to `rollup_status` over the whole input space.
`HELP_PINS` is the register for all seven verbs. Each entry is
``(sentence, "module::function")``:

* the **sentence** is a load-bearing clause quoted from the help `argparse`
  renders, compared after a normalisation that absorbs reflow, emphasis and
  case (`_normalise`, a local minimal copy of `tests/_delivered.normalise` —
  this directory ships to consumers, where `tests/` does not exist). A reword
  that drops the clause fails `test_every_pinned_sentence_is_still_in_the_help`,
  which is what makes it a pin and not a comment.
* the **guard** names the test that exercises the claim. A deleted or renamed
  guard fails `test_every_guard_resolves`. Each one was read before it was
  named: a guard that merely sits near the behaviour proves nothing, so where
  no existing test exercised a claim, one was written — in this module where a
  document tree is enough, in the verb's own module where git is.

The pins were audited against the code as they were written, and seven help
sentences across four blocks were corrected in 1.49.4 rather than pinned as
they stood. Those are in `CHANGELOG.md` under *Fixed*; the comment on each pin
below names the code that makes the sentence true.

A guard is chosen by reading it, and where the reading was not obvious it was
**mutation-checked**: break the behaviour, and the named test must go red. Two
pins moved on that evidence — `scope`'s "read from the current claim branch",
which had been guarded by a test that passes an explicit number and so
exercised the other branch, and `archive`'s three-claim sentence, whose one
guard asserted only that moved lines were unchanged and survived a selection
that moved everything.

**Deliberately unpinned**, and why — the rest of all seven blocks is here:

* *"a finding against one is an error no later item can clear"* (`check`),
  *"an excluded item is never offered"*, *"whichever builds second inherits the
  first's edits"*, *"an item awaiting review or deferred has not shipped"* and
  *"each attestation was made separately and is corrected or withdrawn
  separately"* and *"a deferral is a decision about order, not a finding"*
  (`progress`), *"the stage is dropped, so its bullets no longer speak for
  it"* (`check`), *"roadmap.md's deliverables carry no item marker, so there
  is no bullet of the item to mirror"* (`progress`) — rationale for a rule
  pinned beside them, not a second rule.
* *"reopen a ✅ item first"* (`progress`) — a pointer at another action, the
  refusal it follows being pinned.
* *"since the row is dropped from every check it would have fed"*, *"the
  goal-level mirror of that over-claim"*, *"a normal state rather than a
  defect"* (twice), *"a satisfied profile under an unverified row is a row
  this machine can verify now"* (`status`), *"that would be recommending the deletion of an open PR's
  head branch"*, *"Because in `pr` mode nothing inside the loop observes the
  merge"*, *"so none of them lives only in one commit's diff"*, *"since what it
  blocks is unknown"* — same: the reason a pinned behaviour is what it is.
* *"It reads git and never a pull request: a PR closed without merging looks
  exactly like one still open, so a caller checks for a closed PR before it
  restacks"* (`queue`) — what the verb does not read, which a test cannot
  observe as an absence, and the obligation that leaves its caller.
* *"left for `aide scope` to judge"*, *"`aide progress -h` states the rollup"*,
  *"(like `aide sync`)"*, *"the same merge-tree comparison `gc` uses"*, *"The
  rollup, applied by set and read by `aide check`"* — pointers at another verb,
  rung 1. A pointer names where the rule is; it states none of its own. The
  rule each of these points at is pinned where it is written.
* *"the wrong cell count (a '|' inside a cell, usually), a Stage cell that is
  not an integer, an objective coverage row not starting G<n>, an empty Target
  cell, a summary or objective Status cell with no icon"* (`check`) — the
  enumeration of `_summary_row_problem` / `_objective_row_problem` /
  `_target_row_problem`, each already pinned row-shape by row-shape in
  `test_aide_table_rows.py`'s `CASES` table. Pinning the list here would be a
  third copy of the same list, not a second guard.
* *"the report names that gate, what it blocks and who may resolve it, rather
  than an unexplained 'none left'"* (`claim`) — the *wording* of a report,
  which `test_aide_gates.py` holds phrase by phrase; the behaviour half ("it
  will not offer a blocked item") is pinned.
* *"a blank in them means a count that should have been passed and was not"*
  and *"since a count is a claim its caller made"* (`merge`) — the reading of
  a cell and the reason for a pinned behaviour, not a second behaviour; both
  sit beside claims pinned above. *"The counts are of in-scope findings; one
  outside the item is an insights.md line and no cell here"* is §9's rule
  about what the caller counts, which no cell the engine writes can measure —
  the engine records the number it is handed.
* The `-h` **option** help (`--queue`, `--base`, `--yes`, …). Argparse prints
  those below the description; this row is the description blocks, and an
  option line is one clause about one flag rather than a statement of what the
  verb does.

Stdlib + pytest only, and Windows-safe: no subprocess, no POSIX paths, and the
guard modules are located beside this file rather than by an import path.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

_HERE = Path(__file__).resolve().parent
_MODULE_PATH = _HERE.parent / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_help_pins", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


# --------------------------------------------------------------------------- #
# reading the help, and comparing a quotation with it
# --------------------------------------------------------------------------- #
_MARKERS = str.maketrans("", "", "*_`")


def _normalise(text: str) -> str:
    """The comparable form of a passage — what it says, not how it is set.

    `tests/_delivered.normalise` is the same four transforms over the same
    reasons, and is deliberately not imported: `core/scripts/tests/` is
    installed into every consumer as `.aide/scripts/tests/`, where `tests/`
    does not exist. The table-row transform of that module is dropped rather
    than copied — no `-h` block contains a markdown table — and what remains is
    reflow, emphasis and case, which is what separates a rewrapped help string
    from a reworded one.
    """
    return " ".join(text.translate(_MARKERS).split()).casefold()


def _help_for(verb: str) -> str:
    """The help text `argparse` renders for *verb* — the authoritative copy.

    Reached through the `_SubParsersAction` the way the model test reaches it,
    so the pins read exactly the string a consumer sees, line wrapping and all,
    rather than the source literals it was assembled from.
    """
    parser = aide.build_parser()
    return next(action.choices[verb].format_help()
                for action in parser._actions
                if isinstance(action, argparse._SubParsersAction))


# --------------------------------------------------------------------------- #
# the register
# --------------------------------------------------------------------------- #
#: verb -> [(sentence quoted from `aide <verb> -h`, guard)], where a guard is
#: "module::function" or a tuple of them. A tuple is for a sentence whose halves
#: are exercised by different tests — the register asserts every one of them, so
#: a claim is never half-guarded by a test that covers the easier half.
HELP_PINS: Dict[str, List[Tuple[str, str]]] = {

    # ---------------------------------------------------------------- check --
    "check": [
        # `queue_spec_findings`, row 1: severity "warning", kind
        # "may-change-overlap", and `bookkeeping` excluded from it.
        ("two items claiming one path under May change (warning)",
         "test_aide_queue_specs::test_reports_two_items_claiming_the_same_path"),
        # Same function, rows 2+3: severity "error", kind "changes-pinned-state".
        ("one item changing a path another pins under Asserts against (error)",
         "test_aide_queue_specs::test_changing_a_siblings_pinned_path_is_an_error"),
        # `_dependency_cycles(graph)` -> kind "dependency-cycle", severity error.
        ("a dependency cycle",
         "test_aide_queue_specs::test_dependency_cycle_is_an_error"),
        # The typo pass: `not has_spec and not in_a_queue` -> "unknown-dependency".
        ("a dependency on an item that exists nowhere",
         "test_aide_queue_specs::test_unknown_dependency_is_a_warning"),
        # `spent = {n for n in numbers if item_status... in ("complete",
        # "excluded")}`, then `ordered = sorted(n for n in declared if n not in
        # spent)` — the filter runs before the pair loop, so both sides go.
        ("Spent items (✅ merged or ❌ excluded in progress.md) are "
         "discounted on both sides of every comparison",
         "test_aide_queue_specs::"
         "test_a_spent_item_is_discounted_on_both_sides_of_every_comparison"),
        # `if a in built_after.get(b, ())` — a's edit is excused against b's
        # pin, never b's against a's.
        ("A declared dependency is discounted in one direction",
         "test_aide_queue_specs::test_the_dependency_exemption_is_directional"),
        # `_built_after(ordering_edges)` closes the relation transitively.
        ("when the pinning item names the changing one under ## Dependencies, "
         "directly or through a chain of items on the same queue, the edit "
         "landing cannot break its pin",
         "test_aide_queue_specs::test_a_transitive_dependency_exempts_the_pair"),
        # `ordering_edges` keeps only deps whose status is in BLOCKING_STATUSES
        # ("planned", "in-progress", "in-review") — so ✅/❌/⏸️ edges are dropped.
        ("a dependency claim no longer waits for (✅, ❌, ⏸️) "
         "earns no exemption",
         "test_aide_queue_specs::test_a_deferred_dependency_earns_no_exemption"),
        # The filter is on edges, not pairs, so an intermediate settles it too.
        ("neither does a chain whose middle item no longer blocks",
         "test_aide_queue_specs::"
         "test_a_chain_through_a_deferred_link_earns_no_exemption"),
        # `graph = {... if item_status.get(num) in BLOCKING_STATUSES}`.
        ("The cycle check keeps only items whose status still blocks a claim",
         "test_aide_queue_specs::test_a_deferred_item_drops_out_of_the_cycle_graph"),
        # ⏸️ is absent from `spent`, so a deferred item is still in `ordered`.
        ("deferred items stay in the path comparisons",
         "test_aide_queue_specs::test_a_deferred_item_stays_in_the_path_comparison"),
        # `queue_end_findings`, called by `cmd_check` beside the cross-spec
        # findings and written into the same `--report` (issue #333).
        ("--queue NNN also warns on whether the queue needs a queue-end item",
         "test_aide_queue_specs::test_the_need_reaches_check_as_a_warning_and_the_report"),
        # `queue_closed_stages`: `touches` over the bullets not ⏸️, and
        # `closes` over the 📋/🚧/🔍 bullets — no reference, or an item on a
        # later queue or none.
        ("The queue closes stage N when an item it lists is referenced by a "
         "stage N deliverable not ⏸️ and every stage N deliverable that is "
         "📋, 🚧 or 🔍 names only items listed on this queue or an earlier one",
         ("test_aide_queue_specs::"
          "test_a_queue_that_leaves_stage_work_to_a_later_queue_closes_nothing",
          "test_aide_queue_specs::"
          "test_a_queue_whose_only_open_work_in_the_stage_is_deferred_closes_nothing")),
        # `closes = closes and bool(refs)`; the `continue` over ✅ ❌ ⏸️.
        ("Such a bullet with no item reference keeps the stage open; ✅, ❌ "
         "and ⏸️ bullets never do",
         ("test_aide_queue_specs::test_an_unreferenced_open_bullet_keeps_the_stage_open",
          "test_aide_queue_specs::test_a_deferred_bullet_never_holds_closure",
          "test_aide_queue_specs::test_an_excluded_bullet_is_skipped")),
        # The three reasons: `unannotated` over the `[ ]` boxes and
        # `spec_closed_criteria`; `rows`; `envs` — `env_items` of any status
        # but ❌, intersected with `stage_item_numbers`, less those a row
        # in `stage_rows` covers.
        ("A stage it closes needs one when it has an unticked acceptance box "
         "no item spec's Acceptance Criteria annotate as `closes Stage N "
         "criterion M`, a ❓ Unverified capability row whose Introduced by "
         "cell names it, or an item the stage's own deliverables reference, "
         "whatever its status but ❌ or ⏸️, whose spec has an Environment / "
         "Hardware Dependencies section and which no capability row covers",
         ("test_aide_queue_specs::"
          "test_a_stage_closing_queue_with_an_unannotated_criterion_needs_a_queue_end_item",
          "test_aide_queue_specs::test_every_criterion_annotated_or_ticked_is_no_need",
          "test_aide_queue_specs::test_an_annotation_outside_acceptance_criteria_closes_nothing",
          "test_aide_queue_specs::test_an_unverified_capability_row_is_a_need",
          "test_aide_queue_specs::"
          "test_an_item_declaring_an_environment_gated_capability_is_a_need",
          "test_aide_queue_specs::test_a_merged_env_item_with_no_row_is_still_a_need",
          "test_aide_queue_specs::test_an_env_item_outside_the_stage_is_not_its_need",
          "test_aide_queue_specs::test_an_excluded_env_item_is_no_need",
          "test_aide_queue_specs::test_a_deferred_env_item_is_no_need")),
        # `referenced` is every row's `items`, whatever its stages; the
        # `stage_only` count slices that many off the uncovered, sorted list.
        ("a row whose Introduced by cell references the item covers it, "
         "whatever stage the cell names, and each row naming the stage and no "
         "item covers one more, lowest item number first",
         ("test_aide_queue_specs::test_a_merged_env_item_with_a_verified_row_is_no_need",
          "test_aide_queue_specs::test_an_item_only_row_covers_its_item",
          "test_aide_queue_specs::test_a_row_naming_another_item_does_not_cover_it",
          "test_aide_queue_specs::test_a_stage_only_row_covers_the_stages_env_items",
          "test_aide_queue_specs::test_one_stage_only_row_covers_one_env_item")),
        # `queue_end_stages` on the title; the spec loop skips excluded items
        # and queue-end items before reading an annotation.
        ("A queue-end item is one titled `Validate stage N`, and neither its "
         "own spec nor an excluded item's annotates anything here",
         ("test_aide_queue_specs::test_queue_end_stages_reads_the_title",
          "test_aide_queue_specs::"
          "test_a_queue_end_items_own_annotation_does_not_retire_its_need")),
        # `trailing` — the suffix of the queue's items that are queue-end items.
        ("The check warns when a stage with a need has no queue-end item for "
         "it among the queue's final items, naming each reason",
         ("test_aide_queue_specs::test_a_queue_end_item_among_the_final_items_meets_the_need",
          "test_aide_queue_specs::"
          "test_a_queue_end_item_that_is_not_final_does_not_meet_the_need")),
        # The `queue-end-idle` loop: no stage, not closed, empty reasons.
        ("and when a queue-end item not ✅, ❌ or ⏸️ names no stage, a stage "
         "the queue does not close, or one with no need",
         ("test_aide_queue_specs::test_a_queue_end_title_naming_no_stage_is_reported",
          "test_aide_queue_specs::"
          "test_a_queue_end_item_for_a_stage_the_queue_does_not_close_is_reported",
          "test_aide_queue_specs::test_a_queue_end_item_with_nothing_to_do_is_reported",
          "test_aide_queue_specs::test_a_spent_queue_end_item_is_never_reported_idle",
          "test_aide_queue_specs::test_a_deferred_queue_end_item_is_never_reported_idle")),
        # `back`: reopened items still open, skipped by the idle loop (#332).
        ("unless `aide progress reopen` sent it back and it is still open",
         "test_aide_queue_specs::"
         "test_a_queue_end_item_a_fix_round_reopened_is_never_reported_idle"),
        # The early `return []` when every listed item is spent.
        ("A queue whose items are all ✅, ❌ or ⏸️ gets neither warning",
         ("test_aide_queue_specs::test_a_spent_queue_is_reported_neither_way",
          "test_aide_queue_specs::"
          "test_a_queue_whose_only_open_work_in_the_stage_is_deferred_closes_nothing")),

        # `run_checks`: `has_stage_table` / `has_obj_table` / `sections`, each
        # appending to `errors`.
        ("a missing stage summary table, objective coverage table or stage "
         "section",
         "test_aide_help_pins::"
         "test_check_errors_on_each_missing_table_and_on_missing_stage_sections"),
        # `derived_cell_findings`' `over` list — the measure is
        # `rollup_status`, under which a ❌ bullet counts toward ✅.
        ("a stage summary row marked ✅ over a stage whose deliverables do "
         "not roll up to ✅",
         "test_aide_help_pins::test_the_summary_over_claim_is_measured_by_the_rollup"),
        # The same list for the header, and the Objective loop's
        # `current == "complete"` error (issue #285).
        ("and a stage header or Objective row so marked over a rollup that "
         "is not ✅",
         ("test_aide_defer::test_a_header_marked_done_with_no_summary_row_is_an_error",
          "test_aide_defer::test_an_objective_marked_done_over_an_open_stage_is_an_error")),
        # `objective_rollup`: `rollup_status` over `stage_rollups` of the
        # numbers `_objective_row_stages` reads — the writer's derivation too.
        ("an Objective row's rollup being the same rule over the rollups of "
         "the stages its Delivered by cell names",
         ("test_aide_defer::test_an_objective_marked_done_over_an_open_stage_is_an_error",
          "test_aide_defer::test_a_multi_stage_file_the_verbs_wrote_trips_no_derived_cell")),
        # `if t.kind == "not-met"` under an objective whose status is complete.
        ("an objective marked ✅ over an Outcome target that is ❌ Not met",
         "test_aide_core::test_check_flags_objective_complete_over_unmet_target"),
        # `unreadable_row_errors` over the `_PROGRESS_TABLES` with `error=True`.
        # …whose `CASES` cover three of the four tables, so the gate table
        # — the one whose unreadable row also holds every item — is pinned
        # alongside it rather than assumed.
        ("a row of the stage summary, objective coverage, Outcome targets or "
         "Human gates table that its reader cannot use",
         ("test_aide_table_rows::"
          "test_a_mis_shaped_row_trades_its_error_for_an_unreadable_row_error",
          "test_aide_table_rows::"
          "test_a_mis_shaped_gate_row_is_an_error_under_the_same_rule")),
        # `_table_rows`: the heading's section, plus — for an `anywhere` table
        # whose section holds no readable row — every block a row is taken from.
        ("Each table is read under its template heading, or, for a summary or "
         "objective table without one, wherever its rows are found",
         "test_aide_table_rows::"
         "test_a_summary_under_another_heading_is_still_checked_row_by_row"),
        # `cmd_check`: `return 1` iff `errors`; warnings are only printed.
        ("a warning never moves the exit code — only an error does",
         "test_aide_help_pins::test_a_warning_alone_still_exits_zero"),
        # `derived_cell_findings`' `rest` list with a ✅ rollup — the mirror
        # of the error above, and the same measure.
        ("a stage whose deliverables roll up to ✅ under a summary row "
         "that is not",
         "test_aide_help_pins::"
         "test_a_rolled_up_stage_under_a_lesser_summary_row_is_a_warning"),
        # The `off` lists against `rollup_status` / `objective_rollup`, with
        # no `downgrade_stages` and no `_held_by_hand` (issue #285).
        ("any other stage header, summary row or Objective row whose status "
         "is not its rollup",
         ("test_aide_defer::test_a_stage_cell_the_rollup_does_not_derive_is_one_warning",
          "test_aide_defer::test_an_objective_row_below_its_done_stage_is_a_warning")),
        # 🚧 over 📋 is a cell `set` never downgrades; the ⏸️ Objective row is
        # one `_held_by_hand` leaves standing through a `set` elsewhere.
        ("a cell `aide progress set` would leave as it reads, one it never "
         "downgrades or a ⏸️ set by hand, is named all the same",
         ("test_aide_defer::test_a_stage_cell_the_rollup_does_not_derive_is_one_warning",
          "test_aide_defer::test_a_hand_set_deferred_objective_over_open_stages_is_a_warning")),
        # `held` in the Objective loop: a ✅ derivation over a blocked G-code
        # is compared as 🚧.
        ("an Objective row whose Outcome target is not ✅ Met is compared "
         "with 🚧 where its stages roll up to ✅",
         "test_aide_defer::test_an_objective_held_by_its_target_is_compared_with_in_progress"),
        # `if not off and header_status and summ and header_status != summ`.
        ("a stage header disagreeing with its summary row, where neither was "
         "named against the rollup",
         "test_aide_help_pins::"
         "test_a_stage_header_disagreeing_with_its_summary_row_is_a_warning"),
        # `if nums and not any(n in section_nums for n in nums)`.
        ("an Objective row whose Delivered by cell names no stage with a "
         "section",
         "test_aide_defer::test_an_objective_naming_no_stage_section_is_a_warning"),
        # `for num in summary_status: if num not in section_nums`.
        ("a summary row with no stage section",
         "test_aide_help_pins::test_a_summary_row_with_no_stage_section_is_a_warning"),
        # `elif t.kind != "met"` — unverified, or unrecognised.
        ("an objective marked ✅ over a target not yet ✅ Met",
         "test_aide_core::test_check_warns_objective_complete_over_unverified_target"),
        # `if t.kind is None` in run_checks, and `gate_warnings`'s vocabulary
        # branch: one sentence, two tables, so one test crosses both.
        ("an Outcome target or human gate whose Status is not one of its "
         "table's marks",
         "test_aide_help_pins::test_an_unrecognised_status_in_either_table_is_a_warning"),
        # `gate_warnings` over `blocking_gates` — every gate that is not ✅,
        # and `run_checks` extends `warnings` with it. The unit test alone
        # would survive the call being dropped from `run_checks`, so a test
        # that runs `aide check` over a blocking gate is the second half.
        ("every human gate still blocking",
         ("test_aide_gates::test_awaiting_gate_warns_with_its_reach",
          "test_aide_help_pins::test_a_warning_alone_still_exits_zero")),
        # `if summ == "excluded": continue` — before every stage comparison
        # in `derived_cell_findings`, not just the warning.
        ("A summary row marked \u274c is left out of every "
         "stage comparison above, deliverables and header alike",
         ("test_aide_help_pins::"
          "test_a_rolled_up_stage_under_a_lesser_summary_row_is_a_warning",
          "test_aide_defer::test_an_excluded_summary_row_is_still_left_out")),
        # `st != "excluded"` in the stage `off` list, `current == "excluded"`
        # in the Objective loop.
        ("a header or Objective row marked \u274c is not compared with its "
         "rollup either",
         "test_aide_defer::test_an_excluded_header_or_objective_is_not_compared"),
        # The `off` list in `run_checks` (issue #281): a ⏸️ cell the rollup
        # does not compute, or a computed ⏸️ under a cell that is not.
        ("A summary row or header marked \u23f8\ufe0f over deliverables that "
         "do not roll up to \u23f8\ufe0f is a warning, and so is a stage whose "
         "deliverables roll up to \u23f8\ufe0f under a summary row or header "
         "that is not",
         ("test_aide_defer::test_a_hand_set_deferred_summary_over_open_bullets_is_a_warning",
          "test_aide_defer::test_a_stage_rolling_up_to_deferred_under_a_lesser_summary_is_a_warning")),
        # `over` / `rest` partition the off cells; `not off` gates the
        # header-against-summary warning; `named_objectives` is skipped by
        # the Outcome target loop in `run_checks` (issue #285).
        ("Each cell is named once: a ✅ cell over a rollup that is not ✅ is "
         "its error alone, a stage's other off cells share one warning, and "
         "an Objective row named against its rollup is not compared with its "
         "Outcome targets",
         ("test_aide_defer::test_each_cell_gets_one_message",
          "test_aide_help_pins::"
          "test_a_rolled_up_stage_under_a_lesser_summary_row_is_a_warning")),
        # `_CAPABILITIES` is `error=False`: `unreadable_row_warnings` reports
        # its rows, and `unreadable_row_errors` leaves them out (issue #207).
        ("warnings only, since no other check gates on it: a row its reader "
         "cannot use",
         ("test_aide_capabilities::"
          "test_a_mis_shaped_capability_row_is_a_warning_not_an_error",
          "test_aide_table_rows::test_a_mis_shaped_environment_gated_row_is_no_error")),
        # `if c.kind is None` in `capability_warnings`.
        ("a Status that is neither ✅ Verified nor ❓ Unverified",
         "test_aide_capabilities::test_an_unrecognised_capability_status_is_a_warning"),
        # `if name not in profiles` over `_PROFILE_LINK_RE` matches.
        ("a profile named in the Package / Tool cell that [validation] does "
         "not define",
         "test_aide_capabilities::test_an_undefined_profile_is_a_warning"),
        # `c.kind == "unverified" and closed and not c.noted`, `closed` from
        # `_introducing_stages` against the summary rows `_reads` accepts.
        ("a row still ❓ Unverified with an empty or dash-only Notes cell "
         "whose introducing stage — the first `Stage N` run in its "
         "Introduced by cell — is ✅ in the stage summary",
         ("test_aide_capabilities::test_a_closed_stage_row_with_no_reason_is_a_warning",
          "test_aide_capabilities::"
          "test_a_reason_an_open_stage_or_a_verified_row_is_not_that_warning",
          "test_aide_capabilities::test_the_introducing_stages_are_the_first_stage_run")),

        # `item_spec_number` confirms a name against `item_spec_paths`' own
        # glob; `item_spec_warnings` appends `_unfindable_spec_warning` and
        # `continue`s past every other lint for a None.
        ("a file under items/ not named NNN-<slug>.md, which `aide scope`, "
         "`aide claim` and `aide check --queue` never find, reported in place "
         "of every other spec lint",
         ("test_aide_doc_shape::test_a_spec_no_lookup_finds_is_one_warning_and_nothing_else",
          "test_aide_naming::test_item_spec_number_agrees_with_the_lookup")),
        # `item_spec_warnings` -> the dropped-span lint, one warning per span.
        ("an Authorised paths bullet whose second backtick span or "
         "continuation line is silently dropped, named span by span",
         "test_aide_doc_shape::test_the_lint_names_exactly_what_the_parser_drops"),
        # The double-listing lint compares the two sub-lists by exact path.
        ("one path listed under both May change and Asserts against",
         "test_aide_doc_shape::test_double_listing_a_path_is_reported"),
        # `pattern_covers(pin, m)` — a pin glob swallowing a May change entry.
        ("or an Asserts-against glob covering a May-change path",
         "test_aide_doc_shape::test_a_pin_glob_covering_a_may_change_path_is_reported"),
        # …and deliberately not the other direction.
        ("a literal pin under a May-change glob is the legitimate carve-out",
         "test_aide_doc_shape::test_a_literal_pin_under_a_may_change_glob_is_silent"),
        # `_always_authorised_paths(ddir_rel)` matched against Asserts against.
        ("an always-authorised path pinned under Asserts against",
         "test_aide_doc_shape::test_pinning_an_always_authorised_path_is_reported"),
        # `_stale_assumption_pins(text, engine)` — `_feature_line` compares
        # major.minor, so a patch release falsifies nothing.
        ("a marked assumption pinning an engine whose feature line predates "
         "the installed one",
         "test_aide_doc_shape::test_an_assumption_pinned_to_an_older_engine_is_reported"),
        # `forward_dependency_warnings` (issue #282), called from run_checks
        # on the warnings side; `blocking_dependency_stages` cuts the slot at
        # `_DEPS_SLOT_END_RE` and reads numbers by `_DEPS_STAGE_LIST_RE` or
        # `_DEPS_BARE_LIST_RE`; the ⏸️ exemption reads header and summary row.
        ("a roadmap.md stage whose Dependencies name a later-numbered stage "
         "in the blocking slot",
         ("test_aide_forward_deps::"
          "test_a_forward_dependency_is_a_warning_naming_stage_and_later_stage",
          "test_aide_forward_deps::test_check_reports_it_as_a_warning_and_never_an_error")),
        ("the text up to its first semicolon, spaced dash, sentence end, "
         "'independent of' or 'queue before', where a stage number is one after the word Stage or Stages, or a "
         "slot of bare numbers",
         "test_aide_forward_deps::test_the_blocking_slot_is_read_and_nothing_after_it"),
        ("unless progress.md shows that stage \u23f8\ufe0f on its header or "
         "summary row",
         ("test_aide_forward_deps::test_a_deferred_stage_is_exempt",
          "test_aide_forward_deps::test_any_other_status_is_not_exempt")),
        # `coverage_completeness_warnings` (issue #289), called from
        # run_checks on the warnings side. Case 1 takes every row
        # `_table_rows(_STAGE_SUMMARY)` yields, an unusable one by the number
        # in its Stage cell; case 2 reads roadmap rows by
        # `_COVERAGE_CODES_RE`; case 3 reads the cell by
        # `named_stage_numbers`, which `blocking_dependency_stages` calls too.
        ("a progress.md stage section with no Stage summary row, ⏸️ "
         "and ❌ stages included, where a row the reader cannot use still "
         "counts for the stage its Stage cell names",
         ("test_aide_coverage_completeness::"
          "test_a_stage_section_with_no_summary_row_is_named",
          "test_aide_coverage_completeness::"
          "test_an_unreadable_summary_row_still_counts_for_its_stage",
          "test_aide_coverage_completeness::"
          "test_check_reports_each_case_as_a_warning_and_never_an_error")),
        ("a vision.md G-code with no row in roadmap.md's coverage table, whose "
         "rows are read by the G-codes opening their first cell, past one "
         "leading parenthetical",
         ("test_aide_coverage_completeness::"
          "test_a_vision_g_code_with_no_coverage_row_is_named",
          "test_aide_coverage_completeness::"
          "test_a_coverage_row_is_read_by_the_codes_opening_its_first_cell",
          "test_aide_coverage_completeness::"
          "test_the_codes_run_joins_g_codes_and_nothing_else",
          "test_aide_coverage_completeness::"
          "test_a_g_code_later_in_the_first_cell_is_not_a_coverage_row")),
        ("a stage a roadmap.md coverage row names with no '## Stage N' "
         "section in roadmap.md, the Delivered by cell read as the "
         "Dependencies slot is, by number after the word Stage or Stages or "
         "from a cell of bare numbers",
         ("test_aide_coverage_completeness::"
          "test_a_named_stage_with_no_section_is_named",
          "test_aide_coverage_completeness::"
          "test_the_delivered_by_cell_is_read_as_the_dependencies_slot_is",
          "test_aide_coverage_completeness::"
          "test_a_bare_number_cell_naming_a_missing_stage_is_read")),
        # `for stg, cn, cdate, creason in retracted_criteria(lines)` in
        # run_checks, appending to `warnings`.
        ("every retracted acceptance criterion",
         "test_aide_help_pins::test_a_retracted_criterion_reaches_check_as_a_warning"),
        # `for reopening in reopened_items(lines)` beside it (issue #271).
        ("and every reopened item",
         "test_aide_reopen::test_reopen_raises_no_check_error"),
        # `_latest_trail_note` takes the last prefixed line of a trail, and
        # both readers emit one entry per box / per item (issue #273).
        ("each reported once, by its latest retraction or reopening",
         ("test_aide_reopen::test_a_box_retracted_again_is_open_and_keyed_on_the_second_retraction",
          "test_aide_reopen::test_the_latest_reopening_is_the_one_reported")),
        # `Retraction.reaccepted` reads the box's mark, `Reopening.completed`
        # the item's status; `*_summary` never says "open" for either.
        ("never as open once the box is ticked or the item \u2705 again "
         "\u2014 then as re-accepted or completed again, with the newest "
         "trail date since when there is one",
         ("test_aide_reopen::test_a_re_accepted_box_is_reported_as_re_accepted_not_open",
          "test_aide_reopen::test_a_box_re_accepted_with_no_dated_line_says_since",
          "test_aide_reopen::test_completed_again_names_the_newest_dated_line_since_when_there_is_one",
          "test_aide_reopen::test_an_item_completed_again_is_never_reported_as_open")),
        # `insight_warnings` -> `_INSIGHT_FULL_LOOSE_RE` around a strict `_DATE_RE`.
        ("an insights entry whose shape is off — loose either side of the "
         "date, strict about the date",
         "test_aide_insights::test_the_date_stays_strict_where_the_provenance_relaxed"),
        # `insight_warnings` reads insights.md only; archive-*.md is skipped.
        ("never applied to an archived entry",
         "test_aide_insights::test_an_archive_is_frozen_and_not_shape_checked"),
        # `insight_reference_findings` (issue #276): `_citation_files` leaves
        # the inbox and its archives out; `_INSIGHT_ID_CITATION_RE` requires
        # the word; an unresolved ID goes to `errors`.
        ("Over insight citations in docs/aide and tests_dir, the inbox and "
         "its archives excepted",
         "test_aide_insights::test_the_inbox_and_its_archives_are_not_swept"),
        ("an insight ID written after the word insight, or after entry on a "
         "line that says insight or inbox, that resolves to no entry in "
         "insights.md or insights/archive-*.md is an ERROR",
         ("test_aide_insights::test_a_dangling_insight_id_is_an_error_in_docs_and_in_tests",
          "test_aide_insights::test_a_date_shaped_token_without_the_word_is_not_a_citation",
          "test_aide_insights::test_a_bare_entry_before_a_date_shaped_token_is_not_a_citation",
          "test_aide_insights::test_a_citation_that_resolves_is_clean_even_once_archived")),
        # Same function: more than one claim hash among the hits.
        ("one that matches two different claims is a warning naming their "
         "longer IDs",
         "test_aide_insights::test_a_short_id_two_claims_share_is_a_warning"),
        # Same function: `_positional_citations` over docs and test files
        # alike (issue #295).
        ("a citation by position \u2014 insight 28, insights.md entry 28, or "
         "entry 28 on a line that says insight or inbox \u2014 is a warning "
         "naming the ID that position holds today, in a test as in a document",
         ("test_aide_insights::test_a_positional_citation_is_a_warning_naming_the_id",
          "test_aide_insights::test_a_positional_citation_in_a_test_is_a_warning_too")),
        # `gate_reference_findings` (issue #293): `_citation_files`' docs half
        # only; an unresolved `gate-<hex>` goes to `errors`.
        ("a gate-<hex> token that names no row of progress.md's Human gates "
         "table is an ERROR",
         ("test_aide_gates::test_check_errors_on_a_citation_naming_no_gate",
          "test_aide_gates::test_check_accepts_a_citation_that_resolves")),
        # Same function: more than one Gate-cell hash among the hits.
        ("one that matches two different Gate cells is a warning naming "
         "their longer IDs",
         "test_aide_gates::test_check_warns_on_an_ambiguous_gate_id"),
        # Same function: `_GATE_POSITION_RE`, gated on a gate row existing.
        ("a citation by position \u2014 gate 3, human gate #3 \u2014 is a "
         "warning naming the ID that row holds today, read only while "
         "progress.md's Human gates table has a row",
         ("test_aide_gates::test_check_warns_on_a_positional_citation_and_names_the_id",
          "test_aide_gates::test_positional_reading_needs_a_gates_section",
          "test_aide_gates::test_an_empty_gates_table_reads_no_positions")),
        # `_GATE_ID_CITATION_RE`'s look-arounds.
        ("A token inside a path, a file name, a URL or a heading anchor is "
         "not a citation",
         "test_aide_gates::test_a_path_a_file_name_or_an_anchor_is_not_a_citation"),
        # `gate_reference_findings` reads the docs half of `_citation_files`.
        ("tests_dir is not read",
         "test_aide_gates::test_tests_dir_is_not_swept_for_gate_ids"),
        # `ledger_warnings` over `ledger_rows`: the cell count, the Item cell
        # and each of `LEDGER_INTEGER_COLUMNS`, appended to `warnings` and
        # never to `errors`.
        ("a ledger row no reader can use \u2014 the wrong cell count, an Item "
         "cell that is not an item number, an Outcome that is neither merged "
         "nor abandoned, or a count cell that is neither an integer nor blank",
         "test_aide_ledger::"
         "test_a_row_no_reader_can_use_is_a_warning_and_never_an_error"),
        # `ledger_warnings` returns [] for a missing file, and no check writes
        # one: `ensure_insights_inbox` has no counterpart here.
        ("reported only where ledger.md exists, since a check never creates it",
         "test_aide_ledger::test_check_never_creates_the_ledger"),
        # `template_drift_warnings`: `version < current` and `version >
        # current` each append, and `current is None` names the template; the
        # CLI test is the half that proves `run_checks` still calls it.
        ("a document whose aide-template line above its title records a "
         "version other than "
         "the installed template's, names a template this engine does not "
         "ship, or cannot be read",
         ("test_aide_template_markers::"
          "test_a_document_behind_its_template_is_a_warning_naming_the_changelog",
          "test_aide_template_markers::test_a_document_newer_than_the_install_is_a_warning",
          "test_aide_template_markers::"
          "test_an_unknown_template_and_an_unreadable_line_are_warnings",
          "test_aide_template_markers::"
          "test_check_reports_drift_as_a_warning_and_still_exits_zero")),
        # `targets`: the five root documents, `queue_is_open` over the queue
        # files, and the item specs minus ✅/❌ by `item_status`.
        ("read on vision.md, roadmap.md, progress.md, insights.md and "
         "ledger.md",
         "test_aide_ledger::"
         "test_a_ledger_from_an_older_template_is_reported_like_every_document"),
        ("on a queue while it is open and on an item spec until its item is "
         "✅ or ❌",
         "test_aide_template_markers::"
         "test_a_finished_items_spec_and_a_closed_queue_are_not_read"),
        # `if marker is None: … continue` — only a mis-shaped opener speaks.
        ("never on a document with no such line",
         ("test_aide_template_markers::test_a_document_without_a_marker_is_silent",
          "test_aide_template_markers::test_a_marker_below_the_title_is_not_read")),
        # The stale-claim-branch warning skips an item whose status is
        # "in-review": its PR is open, and its branch is not litter.
        ("A \U0001f50d item's claim branch is not reported stale",
         "test_aide_git::test_check_does_not_call_a_branch_awaiting_review_stale"),
    ],

    # ------------------------------------------------------------- progress --
    # The block #192 pinned one sentence of. The rest of it is code-owned
    # guarantee too — what `set` desugars, what `reword` refuses, what neither
    # `amend` nor `retract` will do — and each clause here names the test that
    # exercises it, at the same bar as the other six blocks.
    "progress": [
        # `set_item_status` flips the bullet, then `rollup_status` over the
        # stage's bullets writes the header and the summary row.
        ("flip an item's deliverable bullet and roll its stage up",
         "test_aide_core::test_set_item_done_completes_stage_without_touching_acceptance"),
        # `_cmd_progress_defer` -> `defer_item`: the flip, and the
        # `_DEFERRED_PREFIX` line through `_insert_trail_line` (issue #281).
        ("`set NNN deferred --reason TEXT` flips it to \u23f8\ufe0f and writes "
         "a dated `deferred: <reason>` line under it",
         ("test_aide_defer::test_defer_flips_the_bullet_and_writes_the_reason_under_it",
          "test_aide_defer::test_set_deferred_writes_no_insight")),
        # `_split_multi_item_bullets` runs first, then only `num` is flipped.
        ("a marker naming several items is desugared into one bullet per item "
         "first, and only the named item moves \u2014 the others keep the "
         "status they had",
         ("test_aide_core::test_the_split_keeps_every_item_of_the_marker",
          "test_aide_core::test_completing_one_item_does_not_complete_its_marker_siblings")),
        # `criteria = None if args.all_criteria else [args.criterion]`, and
        # `cmd_progress` refuses neither-or-both.
        ("tick one acceptance criterion (--criterion N) or every one in the "
         "stage (--all), with --evidence",
         ("test_aide_core::test_accept_criteria_ticks_only_the_named_index",
          "test_aide_core::test_accept_criteria_all_and_evidence",
          "test_aide_core::test_cli_progress_accept_rejects_criterion_and_all_together")),
        # `amend_criterion` -> `_append_trail`: a dated line BELOW the box,
        # with the box and its original annotation untouched.
        ("append a dated correction under a ticked box; the tick stands",
         ("test_aide_acceptance_amend::test_amend_appends_a_dated_trail_line_below_the_box",
          "test_aide_acceptance_amend::test_amend_never_touches_the_original_attestation")),
        # `retract_criterion` unticks and appends `retracted: <reason>`;
        # `_route_retraction_to_insights` writes the `gap` line.
        ("untick a box, keep the original attestation visible, and capture a "
         "`gap` insight",
         ("test_aide_acceptance_amend::test_retract_unticks_the_box_and_keeps_the_original_annotation",
          "test_aide_help_pins::test_retract_routes_its_finding_into_the_inbox")),
        # `reword_criterion` + `reword_roadmap_bullet`, written together or
        # not at all.
        ("change a criterion's text in progress.md and roadmap.md, or in "
         "neither",
         ("test_aide_acceptance_amend::test_reword_mirrors_into_the_matching_roadmap_bullet",
          "test_aide_acceptance_amend::test_a_roadmap_that_cannot_be_lined_up_writes_nothing_and_says_why")),
        # The third outcome (issue #216): `reword_roadmap_bullet` returns
        # `(None, None)` for a stage with no block, and the command writes
        # progress.md without it. The two guards above cover the other two
        # branches only, which is how the sentence stood incomplete.
        ("where roadmap.md has no acceptance block for the stage, in "
         "progress.md alone",
         "test_aide_help_pins::test_reword_with_nothing_to_mirror_writes_progress_alone"),
        # Three separate refusals, and the third is the one a survey misses:
        # a box unticked by `retract` still carries its correction trail.
        ("refuses over a ticked, annotated or corrected box",
         ("test_aide_acceptance_amend::test_reword_refuses_a_ticked_criterion",
          "test_aide_acceptance_amend::test_reword_refuses_an_annotated_criterion_even_once_unticked",
          "test_aide_acceptance_amend::test_reword_refuses_a_criterion_carrying_a_correction_trail")),
        # The bullet form (issue #320): `reword_deliverable` finds the bullet
        # by `_bullet_marker_item_numbers`, and has no status check at all.
        ("rewrites the prose of the one deliverable bullet whose trailing "
         "marker names the item, whatever its status, keeping its icon and "
         "marker",
         ("test_aide_reword_deliverable::test_a_done_bullet_is_reworded_and_keeps_its_icon_and_marker",
          "test_aide_reword_deliverable::test_a_planned_bullet_is_reworded_and_its_twin_left_alone")),
        # `candidate = lines[:start] + [rewritten] + lines[last + 1:]`: the
        # span is the bullet alone, so what hangs under it is outside the cut.
        ("writes the new prose on the bullet's first line, in place of all of "
         "its wrapped lines, and leaves every line under the bullet as it was",
         ("test_aide_reword_deliverable::test_a_wrapped_bullet_is_written_back_on_one_line",
          "test_aide_reword_deliverable::test_lines_under_the_bullet_are_left_as_they_were")),
        # `_cmd_progress_reword_deliverable` opens progress.md only.
        ("It writes progress.md alone",
         "test_aide_reword_deliverable::test_the_cli_writes_progress_alone_and_leaves_roadmap_alone"),
        # One `raise ValueError` per clause, each before anything is written.
        ("It refuses, writing nothing, when no bullet or more than one names "
         "the item, when the bullet's marker names several items, or when the "
         "text is empty, starts with a status icon or ends with an item "
         "reference",
         ("test_aide_reword_deliverable::test_an_item_no_bullet_names_is_refused",
          "test_aide_reword_deliverable::test_an_item_two_bullets_name_is_refused",
          "test_aide_reword_deliverable::test_a_shared_marker_is_refused_and_says_what_to_do",
          "test_aide_reword_deliverable::test_text_that_would_change_the_bullet_is_refused",
          "test_aide_reword_deliverable::test_a_refusal_through_the_cli_writes_nothing")),

        # The model (issue #192), and the reason this module exists: the
        # sentence is transcribed as a predicate and compared with
        # `rollup_status` over every combination of the six statuses.
        ("a stage is \u2705 when every deliverable bullet in it is \u2705 or "
         "\u274c and at least one is \u2705",
         "test_aide_core::test_progress_help_states_the_rollup_the_code_applies"),
        # The other arm of the same function, and the same whole-input-space
        # comparison: the model test's predicate encodes both.
        ("\U0001f6a7 when any bullet is \u2705, \U0001f6a7 or \U0001f50d; "
         "otherwise \U0001f4cb",
         "test_aide_core::test_progress_help_states_the_rollup_the_code_applies"),
        # The ⏸️ arm (issue #281), in the same predicate.
        ("\u23f8\ufe0f when every bullet is \u2705, \u274c or \u23f8\ufe0f "
         "and at least one is \u23f8\ufe0f",
         ("test_aide_core::test_progress_help_states_the_rollup_the_code_applies",
          "test_aide_core::test_a_deferred_deliverable_keeps_its_stage_open")),
        # Neither is in the `("complete", "excluded")` set of the ✅ rule.
        ("\U0001f50d and \u23f8\ufe0f are both kept out of the \u2705 rule",
         ("test_aide_core::test_a_deferred_deliverable_keeps_its_stage_open",
          "test_aide_git::test_in_review_rolls_a_stage_up_to_in_progress_not_complete")),
        # 🔍 *is* in the `("complete", "in-progress", "in-review")` set of the
        # 🚧 rule; ⏸️ is in neither, which is the whole difference.
        ("\U0001f50d also satisfies the \U0001f6a7 rule, so a stage holding "
         "one is always \U0001f6a7",
         "test_aide_git::test_in_review_rolls_a_stage_up_to_in_progress_not_complete"),
        # The ⏸️ arm requires every bullet ✅/❌/⏸️, so any 📋 fails it.
        ("\u23f8\ufe0f gives way to any open bullet \u2014 a stage holding "
         "\u23f8\ufe0f and \U0001f4cb reads \U0001f4cb",
         "test_aide_core::test_a_deferred_deliverable_keeps_its_stage_open"),
        # `_set_stage_header`, `_set_summary_row`, `_apply_objective_rollup`.
        ("The stage header, its summary-table row, and any Objective row "
         "delivered solely by \u2705 stages follow",
         ("test_aide_core::test_set_item_done_completes_stage_without_touching_acceptance",
          "test_aide_core::test_met_target_does_not_block_objective")),
        # `_apply_objective_rollup` consults `outcome_targets` first.
        # `_apply_objective_rollup`'s all-✅-or-⏸️ branch, written from any
        # status (issue #281).
        ("as does an Objective row whose stages are all \u2705 or "
         "\u23f8\ufe0f, which reads \u23f8\ufe0f",
         "test_aide_defer::test_deferring_every_open_item_moves_header_summary_and_objective_to_deferred"),
        # `_held_by_hand`, and `set_item_status`'s touched stages.
        ("A header, summary row or Objective row marked \u23f8\ufe0f by hand "
         "stays as it reads until a verb moves a bullet of its stage",
         "test_aide_defer::test_a_hand_set_deferred_stage_is_left_alone_by_a_set_elsewhere"),
        ("an objective linked to an Outcome target that is not \u2705 Met "
         "never rolls up",
         "test_aide_core::test_unmet_target_blocks_objective_rollup_not_stage"),
        # `RANK` guards the write: a lower-ranked status is not applied.
        ("Apart from deferring, set never downgrades a status",
         ("test_aide_core::test_set_item_never_downgrades",
          "test_aide_defer::test_deferring_the_only_in_progress_item_rolls_the_stage_back_to_planned")),
        # ⏸️ ranks below 🚧, 🔍 and ✅ in `RANK`, so the forward flip applies.
        ("a \u23f8\ufe0f item resumes under any other status set names",
         ("test_aide_defer::test_a_deferred_item_resumes_under_any_forward_status",
          "test_aide_defer::test_resuming_a_deferred_item_moves_the_stage_back_up")),
        # `reopen_item` refuses any bullet not ✅, and is the one caller that
        # passes `downgrade_stages` to `_recompute_rollups` (issue #271).
        ("only reopen moves one back, and only from \u2705",
         ("test_aide_reopen::test_reopen_refuses_an_item_that_is_not_done_and_names_its_status",
          "test_aide_reopen::test_reopen_rolls_the_stage_and_its_objective_back_down")),
        # `stage_deliverable_statuses` skips `_CHECKBOX_RE` lines, and nothing
        # on the rollup path writes one — the attestation is a person's.
        ("no rollup ever ticks an acceptance box",
         ("test_aide_core::test_set_item_never_reticks_a_deliberately_unticked_box",
          "test_aide_core::test_set_item_done_completes_stage_without_touching_acceptance")),

        # `roadmap_acceptance_bullets` drops `_ROADMAP_TARGET_RE` bullets
        # before the Nth is taken.
        ("reword matches the Nth box to the Nth non-`Target:` bullet of the "
         "roadmap stage's Validation / acceptance block",
         "test_aide_acceptance_amend::test_roadmap_acceptance_bullets_skip_a_target_bullet"),
        ("if the two cannot be lined up, nothing is written and the message "
         "says which counts disagreed",
         "test_aide_acceptance_amend::test_a_roadmap_that_cannot_be_lined_up_writes_nothing_and_says_why"),
        # `if args.all_criteria: ... return 2` in both `_cmd_progress_amend`
        # and `_cmd_progress_retract`, before anything is read.
        ("Neither amend nor retract takes --all",
         "test_aide_help_pins::test_amend_and_retract_refuse_all_and_refuse_a_missing_reason"),
        # `--evidence` for amend, `--reason` for retract: both `.strip()`ped,
        # so a blank string is not a stated reason either.
        ("Both refuse without a stated reason",
         "test_aide_help_pins::test_amend_and_retract_refuse_all_and_refuse_a_missing_reason"),
        # The two surfacing rules `retracted_criteria` feeds — pinned from the
        # `check` and `status` blocks as well, and the same guards.
        ("`aide check` warns on every retracted criterion and `aide status` "
         "prints it",
         ("test_aide_help_pins::test_a_retracted_criterion_reaches_check_as_a_warning",
          "test_aide_help_pins::test_status_prints_the_four_states_it_promises")),

        # `reopen_item` (issue #271): the flip, the `_REOPENED_PREFIX` trail
        # line through `_insert_trail_line`, `_recompute_rollups` with the
        # item's stages allowed down, and `_route_gap_to_insights`.
        ("send a \u2705 item back to \U0001f4cb \u2014 its deliverable "
         "bullet flips, a dated `reopened: <reason>` line goes under it, its "
         "stage rolls back down, and a `gap` insight is captured",
         ("test_aide_reopen::test_reopen_flips_the_bullet_and_writes_the_reason_under_it",
          "test_aide_reopen::test_reopen_rolls_the_stage_and_its_objective_back_down",
          "test_aide_reopen::test_reopen_routes_its_finding_into_the_inbox")),
        # The all-✅ precondition over every owned bullet, raised before any
        # write, and `cmd` printing "NOT changed" with the file untouched.
        # `_cmd_progress_reopen`: `reason.startswith(_CI_REASON_PREFIX)` then
        # `next_ci_round` over `_ci_round_scope` (issue #332).
        ("A reason starting `CI ` is a CI reopening, the queue-end step's fix "
         "round, and reopen appends its round to it as `[CI round N]`",
         ("test_aide_reopen::"
          "test_a_ci_reopening_begins_a_round_the_next_one_joins_and_a_later_one_begins_another",
          "test_aide_reopen::test_a_reopening_that_is_not_ci_is_neither_stamped_nor_counted")),
        # `_ci_round_scope`: `_branch_queue_items` at HEAD with a recorded base,
        # else the queue files listing the item.
        ("The count is kept over one set of items: those of every queue the "
         "checked-out queue branch carries, where it has a recorded base, and "
         "else those of the queue file listing the item",
         ("test_aide_queue_pr::"
          "test_a_ci_reopening_on_a_queue_branch_counts_every_queue_it_carries",
          "test_aide_reopen::test_the_round_is_counted_over_the_queue_listing_the_item_only")),
        # `next_ci_round`: `top if (live and top) else top + 1`, `live` read
        # from each item's latest reopening and its status today.
        ("N is the highest round stamped on a CI reopening of one of them "
         "while an item of them whose latest reopening is a CI one is still "
         "\U0001f4cb, \U0001f6a7 or \U0001f50d, and one more than that when "
         "none is",
         ("test_aide_reopen::"
          "test_a_ci_reopening_begins_a_round_the_next_one_joins_and_a_later_one_begins_another",
          "test_aide_reopen::test_a_reopening_that_is_not_ci_is_neither_stamped_nor_counted")),
        # `re.match(r"CI[:\-]", reason)` -> 2, before anything is read.
        ("and so is one starting `CI:` or `CI-`, which would silently not be "
         "a CI reopening; any other reason, `CI/CD \u2026` or a bare `CI` "
         "included, is an ordinary one",
         ("test_aide_reopen::test_a_reason_naming_ci_without_the_space_is_refused",
          "test_aide_reopen::test_a_reason_merely_mentioning_ci_is_an_ordinary_reopening")),
        # `_CI_ROUND_RE.search(reason)` -> 2, before anything is read.
        ("A reason that already ends in such a stamp is refused, exit 2",
         "test_aide_reopen::test_a_reason_carrying_its_own_round_stamp_is_refused"),
        ("reopen refuses, writing nothing, unless every deliverable bullet "
         "whose trailing marker names the item is \u2705",
         ("test_aide_reopen::test_reopen_refuses_when_one_of_the_items_bullets_is_not_done",
          "test_aide_reopen::test_reopen_of_an_item_not_done_exits_one_and_writes_nothing")),
        # `.strip()`ped, exit 2, before anything is read.
        ("and refuses without a stated reason",
         "test_aide_reopen::test_reopen_refuses_without_a_stated_reason_and_writes_nothing"),
        ("The reason goes on the trail line under each flipped bullet and "
         "into the `gap` entry",
         "test_aide_reopen::test_reopen_routes_its_finding_into_the_inbox"),
        # Only the owned bullets' icons and the rollup cells of their stage
        # move; the wrapped text, the marker and every box are compared.
        ("the bullet's text and marker, other items and every acceptance box "
         "are left as they were",
         ("test_aide_reopen::test_reopen_leaves_everything_but_the_item_as_it_was",
          "test_aide_reopen::test_reopen_desugars_a_shared_marker_and_moves_only_the_named_item")),
        # `reopened_items` feeds both `run_checks` and `cmd_status`.
        ("`aide check` warns on every reopened item and `aide status` prints it",
         ("test_aide_reopen::test_reopen_raises_no_check_error",
          "test_aide_reopen::test_status_prints_a_reopened_item_by_its_status_today")),
        # `Reopening.completed` is the item's status today, read by
        # `_parse_item_status`, and `reopening_summary` words by it.
        ("one \u2705 again since reads as reopened and completed again, never "
         "as open",
         "test_aide_reopen::test_an_item_completed_again_is_never_reported_as_open"),

        # `_cmd_progress_defer` / `defer_item` (issue #281).
        ("set NNN deferred refuses, writing nothing, without a stated reason, "
         "or when a deliverable bullet whose trailing marker names the item "
         "is \u2705 or \u274c",
         ("test_aide_defer::test_set_deferred_refuses_without_a_stated_reason_and_writes_nothing",
          "test_aide_defer::test_set_deferred_on_a_done_item_exits_one_and_writes_nothing",
          "test_aide_defer::test_defer_refuses_a_finished_item_and_names_its_status",
          "test_aide_defer::test_defer_refuses_when_one_of_the_items_bullets_is_done")),
        ("Each \U0001f4cb, \U0001f6a7 or \U0001f50d bullet it flips gets the "
         "reason on a trail line, and its stage rolls up again, moving down "
         "where its bullets now say less",
         ("test_aide_defer::test_defer_takes_planned_and_in_review_items",
          "test_aide_defer::test_defer_flips_the_bullet_and_writes_the_reason_under_it",
          "test_aide_defer::test_deferring_the_only_in_progress_item_rolls_the_stage_back_to_planned")),
        ("an item already \u23f8\ufe0f throughout is no change",
         "test_aide_defer::test_deferring_a_deferred_item_again_is_no_change"),
        ("No insight is captured",
         ("test_aide_defer::test_set_deferred_writes_no_insight",
          "test_aide_defer::test_set_deferred_on_a_done_item_exits_one_and_writes_nothing")),
    ],

    # ------------------------------------------------------------- insights --
    "insights": [
        # `_cmd_insights_list`: `shown` filters only on --open/--type, and the
        # ordinal is the entry's position in the file.
        ("number the entries by position and print them all, ticked ones included",
         "test_aide_insights::test_list_prints_every_entry_with_its_number"),
        # `not args.open_only or not e.ticked`.
        ("--open narrows to the untriaged",
         "test_aide_insights::test_list_open_hides_the_closed_history"),
        # `tick_insight_text` — the only function in the CLI that rewrites an
        # existing entry's line.
        # ... and `live_ordinal_for_ref` turns an ID into that position.
        ("the one in-place edit — tick entry N (or ID) with --pointer",
         ("test_aide_insights::test_tick_flips_the_box_and_records_where_it_landed",
          "test_aide_insights::test_tick_by_id_ticks_that_entry_and_the_commit_names_the_id")),
        # `insight_claim_hash` over `InsightEntry.text`, `insight_ids` for the
        # printed form, `_render_insight` for the listing (issue #276).
        ("Each entry is printed with its ID \u2014 the capture date and the "
         "leading hex of a SHA-256 of the claim text, whitespace collapsed",
         ("test_aide_insights::test_an_id_is_the_capture_date_and_four_hex_of_the_claim",
          "test_aide_insights::test_the_id_survives_a_rewrap_but_not_a_reword",
          "test_aide_insights::test_list_prints_each_entry_with_its_id")),
        # The hash reads the claim alone: the checkbox, pointer and trail are
        # outside it, and archive/resolve move lines without retyping them.
        ("which no tick, trail, archive or merge changes",
         ("test_aide_insights::test_the_id_is_blind_to_everything_triage_writes",
          "test_aide_insights::test_an_archived_entry_keeps_its_id_and_list_finds_it")),
        # `insight_ids`: lengthened only against a different hash of one date.
        ("four hex digits, more only where two different claims of one date "
         "would share them",
         ("test_aide_insights::test_two_different_claims_sharing_four_hex_are_printed_longer",
          "test_aide_insights::test_the_same_claim_captured_twice_shares_one_id")),
        # `_cmd_insights_list_one`: a position reads the live file, an ID the
        # whole pool `load_insight_pool` returns.
        ("list N or list ID prints that one entry with its trail, and an ID "
         "is found in the archives too",
         ("test_aide_insights::test_list_one_by_position_prints_that_entry_with_its_trail",
          "test_aide_insights::test_an_archived_entry_keeps_its_id_and_list_finds_it")),
        # Same function, the `entry.ticked` branch: `_append_trail`-shaped line.
        ("on an entry already ticked, append a dated trail line instead",
         "test_aide_insights::"
         "test_ticking_an_already_ticked_entry_appends_a_dated_trail_line"),
        # Same function, `trail_only`: the line goes under an OPEN entry and the
        # checkbox is left alone (issue #236).
        ("with --trail, append the dated line under entry N and leave its "
         "checkbox as it is",
         "test_aide_insights::test_tick_trail_appends_a_dated_line_and_leaves_the_box_open"),
        # Three claims in one sentence, and one test covers only the third:
        # `test_archive_moves_lines_byte_for_byte` asserts that every moved
        # line was in the original, so a selection that moved every dated entry
        # would still pass it. Selection, destination and fidelity are
        # therefore pinned apart.
        # `archive_insight_text`: ticked, and dated before `--before`.
        ("move closed entries older than --before",
         "test_aide_insights::test_archive_moves_only_closed_entries_older_than_the_date"),
        # `insight_quarter(date)` names the file the entries land in.
        ("into insights/archive-YYYY-QN.md",
         ("test_aide_insights::test_archive_yes_moves_entries_into_a_quarter_file",
          "test_aide_insights::test_archive_groups_by_the_entry_quarter")),
        # The entry's lines are moved, not re-rendered, trail included.
        ("each with its trail, line for line",
         ("test_aide_insights::test_archive_carries_the_status_trail_with_its_entry",
          "test_aide_insights::test_archive_moves_lines_byte_for_byte")),
        # The undatable closed entries come back as the second return value.
        ("an entry it cannot date is named and left behind",
         "test_aide_insights::test_archive_names_the_entry_it_had_to_leave_behind"),
        # `insight_warnings` never opens an archive file.
        ("the archive is frozen and no longer shape-checked",
         "test_aide_insights::test_an_archive_is_frozen_and_not_shape_checked"),
        # `parse_insights` numbers by position, so a move renumbers the rest.
        ("what remains is renumbered, so re-run list",
         "test_aide_insights::test_archive_says_the_numbers_have_shifted"),
        # `_print_invalidated_citations` (issue #295): `insight_position_citations`
        # filtered to the positions `archive_position_map` says change, printed
        # before the dry-run return and before any write; exit stays 0.
        ("Every citation by position in docs/aide or tests_dir whose number "
         "the move changes is listed before anything moves, dry run or not, "
         "with the ID that position holds before the move and whether it is "
         "archived or renumbered; the archive still proceeds",
         ("test_aide_insights::"
          "test_a_dry_run_archive_lists_each_positional_citation_with_its_id_before",
          "test_aide_insights::test_an_archive_that_moves_lists_them_and_still_proceeds",
          "test_aide_insights::test_an_archive_lists_no_citation_whose_number_it_leaves_alone",
          "test_aide_insights::test_the_position_map_names_what_moves_and_what_shifts")),
        # `resolve_insights_text`: shared prefix, then each side's tail.
        ("write the union of a conflicted inbox — the shared history, then "
         "each side's new entries in capture order",
         "test_aide_insights::"
         "test_the_union_appends_each_sides_new_entries_after_the_shared_history"),
        # `_merge_entry_block` keeps a tick and its pointer from either side.
        ("a tick on either side stands and keeps its pointer",
         "test_aide_insights::test_a_pointer_is_never_dropped_when_only_one_tick_carries_one"),
        # `_merge_trail` sorts on `_TRAIL_DATE_RE`.
        ("trail lines merge in date order",
         "test_aide_insights::test_both_sides_trail_lines_are_kept_in_date_order"),
        # Two pointers are kept and the run says which entry to arbitrate.
        ("two ticks with different pointers keep both and say so",
         "test_aide_insights::test_two_ticks_with_two_pointers_keep_both_and_flag_it_for_a_human"),
        # The prefix check refuses before anything is written.
        ("Refuses, writing nothing, anything that is not a pure append",
         "test_aide_insights::test_a_refusal_leaves_the_markers_exactly_where_they_were"),
        # The shared history must be a prefix of both sides, so anything that
        # rewrote it — a reword, a reorder, a deletion — fails the same check.
        ("a claim reworded, reordered or deleted on one side",
         "test_aide_insights::"
         "test_a_reworded_claim_at_the_tail_is_refused_only_against_the_merge_base"),
        # An archived side is exactly a side whose shared history shrank.
        ("or a side that archived",
         "test_aide_insights::test_an_archive_on_one_side_is_refused_by_the_prefix_check_alone"),
        # `ensure_insights_inbox(..., verb="insights")` on the `list` branch.
        ("A missing insights.md is created from .aide/templates/insights.md by list",
         "test_aide_insights::test_list_on_a_missing_inbox_creates_it_and_reports_an_empty_backlog"),
        # `_commit_created_file` returns the reason; the notice carries it.
        ("committed when git can — on a branch, with an identity; "
         "otherwise it is left untracked and the notice says why",
         "test_aide_insights::test_a_commit_git_refuses_leaves_the_inbox_untracked_not_staged"),
    ],

    # ---------------------------------------------------------------- claim --
    "claim": [
        # `_pick_item` walks `queue_item_numbers(queue_text)`, which is
        # document order — the help said "lowest-numbered" until 1.49.4.
        ("Picks the first \U0001f4cb item the queue lists — its own order, "
         "not the item numbers",
         "test_aide_git::test_claim_offers_the_first_planned_item_the_queue_lists"),
        # `if any(item_status.get(d) in BLOCKING_STATUSES for d in deps)` —
        # the complement of BLOCKING_STATUSES is exactly {✅, ❌, ⏸️}.
        ("whose dependencies have all left the way (✅, ❌ or "
         "⏸️)",
         "test_aide_git::test_pick_item_waits_only_for_a_dependency_that_still_blocks"),
        # `gate_blocked_items` -> `if num in gate_blocked: continue`.
        ("that no unresolved human gate reaches",
         "test_aide_gates::test_claim_skips_a_gated_item_and_offers_the_next"),
        # The "none left" report is built from the gates that actually apply.
        ("It will not offer a blocked item",
         "test_aide_gates::test_none_left_names_only_the_gates_that_apply"),
        # `_early_ready`, printed last on both exit-0 paths of
        # `_report_nothing_claimable` — the queue-end step's early trigger,
        # decided here so the runner never reads it from reason prose (#331).
        ("Every \"none left \u2014 \u2026\" report that exits 0 ends with an "
         "`early ready:` line, yes or no before an em dash",
         ("test_aide_gates::test_early_ready_is_yes_when_every_open_item_waits_on_a_gate",
          "test_aide_gates::test_early_ready_is_no_when_no_gate_explains_the_hold")),
        # The clauses of the `yes`, each broken by one test: the fixed point
        # over dependencies (in any listing order), the claimed item, the ✅
        # clause.
        ("yes when every gate holding the queue is still \u23f3 awaiting its "
         "decision, every open item waits on one \u2014 one reaches it, or it "
         "waits only on items that do \u2014 no open item is claimed, and at "
         "least one item of the queues checked is \u2705",
         ("test_aide_gates::test_early_ready_is_yes_when_every_open_item_waits_on_a_gate",
          "test_aide_gates::test_an_item_waiting_only_on_a_gated_item_is_held_by_the_gate",
          "test_aide_gates::test_a_chain_listed_before_the_gated_item_it_hangs_off_is_held",
          "test_aide_gates::test_a_landed_dependency_does_not_loosen_a_held_item",
          "test_aide_gates::test_early_ready_is_no_while_an_open_item_is_claimed",
          "test_aide_gates::test_a_claimed_gated_item_is_work_in_flight",
          "test_aide_gates::test_early_ready_is_no_before_any_item_has_landed")),
        # `settled` in `_early_ready`: any relevant gate not "awaiting".
        ("A \u274c declined gate makes it no",
         "test_aide_gates::test_a_declined_gate_is_no_early_ready"),
        # `elif not open_ordered:` — its own wording.
        ("An `all` gate over a queue with nothing left open is read the same "
         "way, a yes in words of its own",
         "test_aide_gates::test_an_all_gate_over_a_queue_with_nothing_open_says_so"),
        # `if stranded:` inside `if relevant:` returns 1 before `early`.
        ("An unpublished claim \u2014 a claim branch origin has never seen "
         "\u2014 exits 1 with how to publish or release it, whether or not a "
         "gate holds the rest",
         "test_aide_gates::test_an_unpublished_claim_behind_a_gate_exits_1_with_no_early_line"),
        # `if not relevant and not open_items: print("none left")` returns
        # before `_early_ready` is printed.
        ("A bare \"none left\" (nothing open, no gate) carries no such line",
         "test_aide_git::test_an_empty_queue_still_says_only_none_left"),
        # `if block_everything or unreadable_gate_rows(plines): return None`,
        # and `cmd_claim` exits 1 naming the row.
        ("A human-gates row it cannot read holds every item",
         "test_aide_gates::test_claim_holds_every_item_behind_an_unreadable_gate_row"),
        # A defect rather than a normal hold, so not the "none left" exit.
        ("the report names the row and exits 1",
         "test_aide_gates::test_claim_holds_every_item_behind_an_unreadable_gate_row"),
        # `ensure_insights_inbox(repo_root, config, verb="claim")` in `cmd_claim`.
        ("A missing insights.md is created from the template on the way through",
         "test_aide_git::test_claim_creates_the_missing_inbox_on_the_way_through"),
        # `_interface_pin_report` -> `interface_pins` over the Assumptions
        # bullets that reference a `## Dependencies` item (issue #243).
        ("the claim names that assumption as pinning a dependency's interface",
         "test_aide_traceability::test_claim_names_the_assumptions_that_pin_a_dependency"),
        # The three exclusions of `interface_pins`, in the order §5 lists them.
        ("an engine-marked assumption and one already carrying a re-check are "
         "not named, and a dependency that left the queue as ❌ or ⏸️ is named "
         "as having no code to check against",
         ("test_aide_traceability::test_interface_pins_skip_the_three_shapes_that_are_not_the_signal",
          "test_aide_traceability::test_claim_names_the_assumptions_that_pin_a_dependency")),
    ],

    # ------------------------------------------------------------------- gc --
    "gc": [
        # `cmd_gc`: `item_status.get(num) == "complete"` -> `branch -D` plus
        # `push origin --delete`, the latter skipped in `local` mode.
        ("Deletes claim branches, local and remote, whose item is ✅ in "
         "progress.md",
         "test_aide_git::test_gc_yes_deletes_local_and_remote"),
        # `_merged_prefixed_branches(repo_root, main, prefix)`.
        ("with --merged also branches already merged into the base",
         "test_aide_git::test_gc_merged_deletes_merged_branch"),
        # `_branch_content_landed` is `merge-tree --write-tree` + a tree
        # comparison, so a squash merge reads as landed where ancestry does not.
        ("On the ✅ ground a branch goes only when `git merge-tree "
         "--write-tree` says merging it into the base would change nothing",
         "test_aide_git::test_gc_deletes_a_single_commit_squash_merge"),
        # `landed is False` -> `skips[br]`, naming `main`.
        ("a branch that still carries unlanded content is skipped with the "
         "base named",
         "test_aide_git::test_gc_refuses_a_tick_whose_branch_has_unlanded_content"),
        # `if args.abandon: targets[br] = reason + "; --abandon"` — checked
        # before the oracle runs at all.
        ("unless --abandon",
         "test_aide_git::test_gc_abandon_deletes_an_unlanded_tick_on_purpose"),
        # `_has_merge_tree` -> `_MERGE_TREE_MIN_GIT = (2, 38)`; `not
        # can_measure` skips rather than falling back to `branch --merged`.
        ("merge-tree --write-tree needs git >= 2.38: on older git the ✅ "
         "ground refuses rather than falling back to a weaker test",
         "test_aide_git::test_gc_refuses_the_tick_ground_on_git_too_old"),
        # The `protected` sweep moves branches out of `targets` before the
        # first `print`, so the preview cannot overstate.
        ("Every skip \u2014 checked out, unlanded, unmeasurable (a ref the "
         "oracle could not read), git too old \u2014 is decided before "
         "anything is printed",
         ("test_aide_git::test_gc_preview_does_not_promise_to_delete_the_checked_out_branch",
          "test_aide_git::test_a_gc_skip_says_so_when_the_landing_could_not_be_measured")),
        # `print(f"skipping {br} ({_where(br)}): {skips[br]}")`, above the
        # `--yes` branch, so both paths print it.
        ("shown as `skipping <branch> (local | remote | local+remote): "
         "<reason>` on both paths",
         "test_aide_git::test_a_gc_skip_names_the_branch_where_it_lives_and_why"),
        # One `targets` dict, printed as "would delete" or "deleted".
        ("the dry run is exactly the set --yes deletes",
         "test_aide_git::test_gc_preview_and_yes_report_the_same_set"),
    ],

    # --------------------------------------------------------------- status --
    "status": [
        # `elif st == "in-review"` — the note says "awaiting review" and the
        # `run 'aide gc'` string belongs to the `complete` branch only.
        ("A \U0001f50d item's claim branch is reported as awaiting review, "
         "never as stale and never with a `gc` recommendation",
         "test_aide_git::test_status_does_not_recommend_gc_for_a_branch_awaiting_review"),
        # `_landed_review_items(...)`, printed with the `aide sync: ` prefix
        # stripped — the same `_branch_content_landed` oracle `gc` uses.
        ("names any \U0001f50d item whose work has since landed in the base",
         "test_aide_git::test_status_names_a_review_item_whose_work_has_landed"),
        # `resolve_base(repo_root, config, explicit, br)` per claim inside
        # `_landed_review_items` — not `main_branch`, and not the current
        # branch's base (issue #213).
        ("landed in the base that claim recorded (or `--base`)",
         "test_aide_git::test_status_names_stacked_review_work_landed_in_its_recorded_base"),
        # `_branch_content_landed(repo_root, b, ref)` with `b` the bare base
        # name — no `_remote_or_local`, so `origin/<base>` is never consulted.
        ("Those bases are the local branches, never origin/<base>: a merge "
         "made on the forge is seen once that branch is pulled, not by the "
         "fetch alone",
         "test_aide_git::test_status_sees_a_forge_merge_only_once_the_base_is_pulled"),
        # The four loops over `human_gates`, `_unreadable_rows`,
        # `outcome_targets` and `retracted_criteria` in `cmd_status`.
        ("Every human gate still blocking, every Outcome target not yet ✅ "
         "Met, every retracted acceptance criterion and every progress.md "
         "table row no reader can use is printed too",
         "test_aide_help_pins::test_status_prints_the_four_states_it_promises"),
        # The `reopened_items` loop in `cmd_status` (issue #271), and the
        # `; re-accepted` / `; completed again` suffix both loops carry (#273).
        ("So is every item `aide progress reopen` sent back",
         "test_aide_reopen::test_status_prints_a_reopened_item_by_its_status_today"),
        ("a retracted criterion or reopened item that has since been "
         "re-accepted or completed again says so",
         ("test_aide_reopen::test_check_and_status_word_a_re_accepted_box_by_its_tick",
          "test_aide_reopen::test_status_prints_a_reopened_item_by_its_status_today")),
        # The `gated_capabilities` loop in `cmd_status`: the profile named
        # always, `evaluate_profile` called only under `args.profiles` and
        # `c.kind == "unverified"`, memoised per profile.
        ("So is every environment-gated capability not yet ✅ Verified, with "
         "the [validation] profile its Package / Tool cell names",
         "test_aide_capabilities::"
         "test_status_lists_unverified_capabilities_without_evaluating_profiles"),
        ("With --profiles, each profile a ❓ Unverified row names is evaluated "
         "once, as `aide env --profile` evaluates it (the expression only, "
         "never the gated tests), and reported satisfied or not",
         ("test_aide_capabilities::"
          "test_status_profiles_evaluates_the_profiles_of_unverified_rows",
          "test_aide_capabilities::test_status_evaluates_each_profile_once")),
        # `evaluate_profile`'s `TimeoutExpired` and `OSError` branches.
        ("one that times out or cannot start is not satisfied",
         ("test_aide_capabilities::"
          "test_a_profile_that_outlives_its_timeout_is_not_satisfied",
          "test_aide_capabilities::"
          "test_a_profile_whose_interpreter_cannot_start_is_not_satisfied")),
        # `queue_stack_facts` (issue #303): `_unmerged_queue_branches`,
        # ordered by `depth` along recorded bases.
        ("The stack of unmerged queue branches — the ones `aide queue "
         "start` counts against [loop] max_open_queues — is printed "
         "bottom first",
         ("test_aide_status_stack::test_a_two_queue_stack_is_printed_bottom_first",
          "test_aide_status_stack::test_a_landed_lower_reads_landed_and_never_orphans")),
        ("base= is the branch's recorded base, ? where none is recorded",
         ("test_aide_status_stack::test_a_two_queue_stack_is_printed_bottom_first",
          "test_aide_status_stack::test_a_branch_with_no_recorded_base_reads_unknown")),
        # `_branch_pr_facts`: `isDraft` asked for, an OPEN draft is "draft"; open
        # or draft wins, else `max(found)`; `prs[b] = "unknown"` once `_gh`
        # fails; `look = mode != "local"`.
        ("pr= is its pull request as #N/open, #N/draft (open but not yet "
         "marked ready), #N/merged or #N/closed (an open or draft one first, "
         "else the newest), none where gh found none, unknown "
         "where gh could not be asked, and - in local mode, which asks no forge",
         ("test_aide_status_stack::test_a_reopened_pr_is_answered_by_its_open_one",
          "test_aide_status_stack::test_a_merged_pr_alone_reads_merged_and_orphans_nothing",
          "test_aide_status_stack::test_a_draft_reads_draft_and_awaits_no_review_until_marked_ready",
          "test_aide_status_stack::test_a_draft_is_preferred_over_a_closed_pr_and_orphans_nothing",
          "test_aide_status_stack::test_the_forge_is_asked_whether_a_pr_is_a_draft",
          "test_aide_status_stack::test_a_two_queue_stack_is_printed_bottom_first",
          "test_aide_status_stack::test_could_not_look_is_unknown_and_never_none",
          "test_aide_status_stack::test_local_mode_asks_no_forge_about_the_stack")),
        # `_queue_branch_ci` over `_branch_queue_items` and the branch's
        # own progress.md, asked only for a PR that reads `draft` (#330).
        ("A draft reads #N/draft(fixing) when an item of the queues the "
         "branch carries (its own queue file and every queue file it adds "
         "over its base) was sent back by `aide progress reopen` and is still "
         "open, read from the branch's own progress.md",
         ("test_aide_queue_pr::test_a_draft_with_a_reopened_item_still_open_reads_fixing",
          "test_aide_queue_pr::test_fixing_is_read_from_each_branch_and_only_for_its_own_queues",
          "test_aide_queue_pr::test_an_open_pr_with_a_reopened_item_is_not_marked_fixing")),
        # `queue_stack_facts` asks `_queue_branch_ci` for a draft or a failing
        # PR only; `cmd_status` prints the count when above 0 (issue #332).
        ("For a draft or a PR whose checks= is failure, a `ci fix rounds: N` "
         "line below those counts the CI fix rounds the queues the branch "
         "carries have begun: the highest `[CI round N]` `aide progress "
         "reopen` stamped on a CI reopening of one of their items, read from "
         "the branch's own progress.md; no line where none has begun",
         "test_aide_queue_pr::test_a_draft_or_failing_pr_names_the_ci_fix_rounds_begun"),
        # `running_checks`, asked only under failure; one `pending check:`
        # line each in `cmd_status` (#332).
        ("Under failure, each check still running is named on a `pending "
         "check:` line below the failing ones",
         "test_aide_queue_pr::test_a_failure_with_legs_still_running_names_each_as_pending"),
        # `checks_state`: failing first, then pending, then any SUCCESS;
        # `_CHECK_IGNORED` neither; the `failing check:` lines in cmd_status.
        ("checks= is the CI state of that PR's head commit: failure when any "
         "check failed, each failing check then named on a `failing check:` "
         "line below it; else pending while any has not finished; else "
         "success when any passed; else none",
         ("test_aide_queue_pr::test_the_rollup_reads_as_one_ci_state",
          "test_aide_queue_pr::test_status_reports_each_prs_checks_and_names_the_failing_ones",
          "test_aide_queue_pr::test_status_reads_pending_and_success")),
        ("no check at all, or only skipped and neutral ones, which is what a "
         "CI that skips drafts reports",
         ("test_aide_queue_pr::test_the_rollup_reads_as_one_ci_state",
          "test_aide_queue_pr::test_status_reports_each_prs_checks_and_names_the_failing_ones")),
        # `_CHECK_FAILED`.
        ("A cancelled, timed-out or stale check is a failed one",
         "test_aide_queue_pr::test_the_rollup_reads_as_one_ci_state"),
        # `checks()` in `queue_stack_facts`: `why_not` where the forge
        # failed, `checks_why` where the rollup did not read; `-` otherwise.
        # `_branch_pr_facts`: `rollup_why`, then `ask` without the rollup.
        ("could be asked only without checks (pr= is then read without them)",
         "test_aide_queue_pr::test_a_forge_that_will_not_report_checks_still_answers_pr"),
        # `checks_state([])` is "none": nothing tells not-yet from never.
        ("Just after a push or `aide queue ready`, none can also mean CI has "
         "not registered a run yet",
         "test_aide_queue_pr::test_checks_read_none_right_after_ready_before_ci_registers"),
        ("the reason on a `checks unknown:` line below it, and - where there "
         "is no PR and in local mode",
         ("test_aide_queue_pr::test_checks_are_unknown_with_the_reason_where_the_forge_cannot_be_asked",
          "test_aide_queue_pr::test_checks_are_unknown_where_the_rollup_cannot_be_read",
          "test_aide_queue_pr::test_a_rollup_status_cannot_read_is_unknown_with_a_reason",
          "test_aide_queue_pr::test_checks_are_a_dash_with_no_pr_and_in_local_mode")),
        # `lower_state`: `_is_ancestor(newest(base), newest(b))`, origin's
        # tip where it is ahead.
        ("lower= is moved when the queue branch below has commits this one "
         "lacks, so `aide queue restack` is due, and current when it has none",
         ("test_aide_status_stack::test_a_lower_with_commits_the_upper_lacks_reads_moved_until_restacked",
          "test_aide_status_stack::test_a_lower_moved_on_origin_reads_moved")),
        ("landed or gone when the recorded lower is no longer unmerged and is "
         "still a branch, or is not",
         ("test_aide_status_stack::test_a_landed_lower_reads_landed_and_never_orphans",
          "test_aide_status_stack::test_a_closed_and_deleted_lower_still_orphans_the_branch_above")),
        # `orphaned`: the walk down recorded bases, `break` on a landed lower.
        ("orphaned= is yes when a PR below it in the stack was closed without "
         "merging, and a lower git says landed never orphans",
         ("test_aide_status_stack::test_a_closed_lower_orphans_every_branch_above_and_stops_the_loop",
          "test_aide_status_stack::test_a_closed_and_deleted_lower_still_orphans_the_branch_above",
          "test_aide_status_stack::test_a_landed_lower_reads_landed_and_never_orphans")),
        ("unknown when one below it could not be looked up or has no "
         "recorded base; - in local mode",
         ("test_aide_status_stack::test_could_not_look_is_unknown_and_never_none",
          "test_aide_status_stack::test_a_branch_with_no_recorded_base_reads_unknown",
          "test_aide_status_stack::test_local_mode_asks_no_forge_about_the_stack")),
        # `runnable` in `queue_stack_facts`: closed/orphaned first, then
        # `live_work` (📋/🚧 only), then `len(branches) < cap`.
        ("runnable: is no when a queue PR in the stack was closed without "
         "merging or a branch is orphaned; otherwise yes when the live queue "
         "has a \U0001f4cb or \U0001f6a7 item or the stack is below [loop] "
         "max_open_queues, and no when neither",
         ("test_aide_status_stack::test_a_closed_lower_orphans_every_branch_above_and_stops_the_loop",
          "test_aide_status_stack::test_live_work_is_runnable_while_prs_await_review",
          "test_aide_status_stack::test_with_no_live_work_runnable_is_room_below_the_cap",
          "test_aide_status_stack::test_an_item_awaiting_review_is_not_live_work")),
        # `awaiting` in `queue_stack_facts`: `/open` only, never `/draft`.
        ("awaiting review: is yes when a queue branch's PR is open and ready "
         "for review — a draft is the loop's own PR still being built, and "
         "counts for nothing — unknown when none was seen ready but gh could "
         "not be asked, and no otherwise — in local mode always",
         ("test_aide_status_stack::test_live_work_is_runnable_while_prs_await_review",
          "test_aide_status_stack::test_a_draft_reads_draft_and_awaits_no_review_until_marked_ready",
          "test_aide_status_stack::test_could_not_look_is_unknown_and_never_none",
          "test_aide_status_stack::test_an_empty_stack_awaits_no_review_without_asking",
          "test_aide_status_stack::test_local_mode_asks_no_forge_about_the_stack")),
        # `_gh` returns a reason on every failure; the open-PR block prints it.
        ("The open-PR list says it could not look, and gh's reason, rather "
         "than going silent",
         ("test_aide_status_stack::test_could_not_look_is_unknown_and_never_none",
          "test_aide_status_stack::test_gh_missing_from_path_is_a_reason",
          "test_aide_status_stack::test_gh_exiting_non_zero_is_a_reason_naming_the_exit")),
    ],

    # ---------------------------------------------------------------- scope --
    "scope": [
        # `git merge-base base HEAD` then `git diff --name-only <mb>`, fed to
        # `scope_findings` against the spec's May-change list.
        ("Diffs the branch against the merge-base with the item's base and "
         "reports every changed path outside the spec's ## Authorised paths",
         "test_aide_scope::test_scope_uses_merge_base_not_the_branch_tip"),
        # `scope_findings` returns `(unauthorised, contradictions)`, printed
        # under two different messages.
        ("a path listed under Asserts against and then changed is reported "
         "separately",
         "test_aide_scope::test_findings_separate_unauthorised_from_contradiction"),
        # `_branch_item_number(branch, prefix)` when `args.number is None`.
        # The guard must RUN `aide scope` with no argument: a test that passes
        # a number exercises the other branch, and leaves `number = None` a
        # mutation the register cannot see.
        ("With no number the item is read from the current claim branch",
         ("test_aide_scope::test_scope_ok_when_every_change_is_authorised",
          "test_aide_scope::test_scope_cannot_guess_the_item_off_an_unrecognised_branch")),
        # `_is_queue_branch(branch, prefix)` -> message and `return 0`.
        ("a queue branch resolves to no item and is skipped",
         "test_aide_scope::test_scope_skips_a_queue_branch"),
        # `_scope_base_ref` -> `resolve_base`: explicit > recorded > main_branch.
        ("The base is --base if given, else the branch's recorded base, else "
         "main_branch",
         "test_aide_base::test_scope_diffs_against_the_recorded_base"),
        # `_remote_or_local`, applied to the derived answer only.
        ("the two derived answers prefer origin/<base> over the local ref",
         "test_aide_base::test_a_derived_base_prefers_its_origin_counterpart"),
        # `return 0` after "OK", and the queue-branch branch above.
        ("Exit 0: in scope, or nothing to check (a queue branch)",
         "test_aide_scope::test_scope_ok_when_every_change_is_authorised"),
        # `if total: ... return 1`.
        ("1: something changed outside it",
         "test_aide_scope::test_scope_flags_a_file_outside_the_list"),
        # The three `return 2` paths: no spec, `declares_nothing`, no merge-base.
        ("2: could not check (no spec, no section, or no base to diff against)",
         "test_aide_scope::test_scope_reports_a_missing_section_rather_than_passing"),
        # `traceability_warnings` over `added_test_functions` (issue #242).
        ("every test function the branch added under tests_dir must name an AC "
         "number the spec's ## Acceptance Criteria carries (ac3) or a case "
         "label its ## Testing Strategy or its optional ## Review findings "
         "names",
         ("test_aide_traceability::test_scope_warns_on_a_test_naming_neither",
          "test_aide_traceability::test_scope_is_silent_when_every_added_test_is_traced",
          "test_aide_traceability::"
          "test_scope_traces_a_parametrised_test_and_a_review_finding",
          "test_aide_traceability::"
          "test_review_findings_labels_share_the_bullet_shape_and_are_optional")),
        # `_CASE_LABEL_RE` / `_STOP_LABEL_RE`: `:`, or `.` on a wrapped word
        # followed by text (#315).
        ("the first word of a bullet, closed by a colon, or by a full stop when "
         "the word is in bold or backticks and text follows",
         ("test_aide_traceability::test_a_label_closed_by_a_full_stop_is_a_label_too",
          "test_aide_traceability::"
          "test_a_full_stop_with_nothing_after_it_or_inside_a_word_is_prose")),
        # `_parametrize_ids` over the AST, `_traces_to`'s id branch (#314).
        ("A parametrised test also traces through its literal "
         "pytest.mark.parametrize ids — a string argvalue, the strings of a "
         "tuple argvalue, a pytest.param id and each string in ids=[...], read "
         "without running anything — where the label or acN stands as a whole "
         "word of the id",
         ("test_aide_traceability::test_parametrize_ids_are_read_statically",
          "test_aide_traceability::"
          "test_an_id_matches_a_label_or_an_ac_as_a_whole_word_only",
          "test_aide_traceability::test_a_parametrised_test_traces_through_its_ids")),
        # Warns, never fails: exit 0 with warnings printed.
        ("Also warns, never fails, on traceability",
         "test_aide_traceability::test_the_warning_never_turns_a_pass_into_a_fail"),
        # `added_test_functions` subtracts the names at `merge_base`.
        ("A function present in the file at the base is an edit, not an "
         "addition, and is not checked",
         "test_aide_traceability::test_scope_ignores_an_edited_existing_test"),
        # `renamed_paths` feeds the old name to `git show`.
        ("a renamed file being read under its old name",
         "test_aide_traceability::test_a_renamed_test_file_is_read_under_its_old_name"),
        # `if _AC_HEADING_RE.search(spec_text) is None: notice`.
        ("a spec with no ## Acceptance Criteria heading is a notice and no "
         "warnings",
         "test_aide_traceability::test_a_spec_without_criteria_is_one_notice_not_n_warnings"),
        # `owning_item` -> `split_reconciled_tests`, which traces the file's
        # tests against the owner's spec alone (issue #262).
        ("A test file named test_NNN_<topic>.py for an item other than the "
         "one scoped is item NNN's",
         "test_aide_traceability::test_a_test_file_is_owned_by_the_item_its_name_carries"),
        ("its added tests trace against item NNN's spec instead, and the "
         "scoped spec is not read for them",
         "test_aide_traceability::"
         "test_a_coincident_ac_number_is_not_credited_to_the_scoped_item"),
        # `others[N].reconciled` -> one `notice:` per owner, not in `traced`.
        ("The ones that trace are reported as reconciled, in one notice per "
         "item, and not warned on; the rest warn, naming item NNN's spec",
         ("test_aide_traceability::"
          "test_a_rename_inside_another_items_file_is_reconciled_not_warned",
          "test_aide_traceability::"
          "test_an_owner_label_traces_and_an_untraced_test_warns_naming_the_owner")),
        # `specs[owner] is None` -> the test stays in `own`.
        ("Where item NNN has no spec, or none with an ## Acceptance Criteria "
         "heading, the file is read as the scoped item's own",
         ("test_aide_traceability::"
          "test_an_owner_with_no_spec_leaves_the_file_to_the_scoped_spec",
          "test_aide_traceability::"
          "test_an_owner_spec_without_criteria_leaves_the_file_to_the_scoped_spec")),
    ],

    # ---------------------------------------------------------------- merge --
    # The ledger row (issue #244) and the inherited-failure gate (issue
    # #275); everything else `merge` does is stated in its option help, which
    # this register does not read.
    "merge": [
        # `pending_row` -> `append_ledger_row`, one row, `ledger_path(ddir)`.
        ("The row is one per item, in docs/aide/ledger.md",
         "test_aide_ledger::"
         "test_merge_writes_the_row_in_the_commit_that_ticks_the_item"),
        # `append_ledger_row`: `path.write_bytes(template.read_bytes())`.
        ("created from .aide/templates/ledger.md the first time there is a "
         "row to write",
         "test_aide_ledger::test_the_first_row_creates_the_ledger_from_the_template"),
        # `_promote_item_to_complete(..., extra_rels=...)` -> one
        # `_commit_docs_files` over both paths.
        ("committed together with the \u2705 so the two can never disagree",
         "test_aide_ledger::"
         "test_merge_writes_the_row_in_the_commit_that_ticks_the_item"),
        # `_ledger_diff_cells`: `added_test_functions(..., ref=branch)` and
        # the changed-path count, both against `merge-base(main, branch)`.
        ("how many test functions and files the branch added against the base "
         "this run resolved",
         "test_aide_ledger::"
         "test_merge_writes_the_row_in_the_commit_that_ticks_the_item"),
        # `_ledger_diff_cells` counts `split_reconciled_tests`'s own plus
        # untraced, never `others[N].reconciled` (issue #262).
        ("less the tests `aide scope` reports as reconciled in another item's "
         "test file, which are that item's",
         "test_aide_ledger::"
         "test_a_test_reconciled_in_another_items_file_is_not_counted"),
        # `item_kind`: the title regex, then the inbox pointers, else normal.
        ("its kind \u2014 validate-stage from an item titled `Validate stage "
         "N`, maintenance from an inbox entry ticked with this item's number, "
         "else normal",
         ("test_aide_ledger::test_a_validate_stage_item_is_its_own_kind",
          "test_aide_ledger::test_an_item_an_insight_was_routed_to_is_maintenance")),
        # `ledger_cells`: `"" if rounds is None else str(rounds)`, and the same
        # for each rank — so a rank passed as 0 stays a 0.
        ("A count nobody passed is a blank cell and never a 0",
         ("test_aide_ledger::"
          "test_a_count_nobody_passed_is_a_blank_cell_never_a_zero",
          "test_aide_ledger::"
          "test_merge_without_the_flags_writes_the_row_with_blank_counts")),
        # Every derivation in `ledger_cells` degrades to "".
        ("a cell nothing could measure is blank for the same reason, so an "
         "item whose spec or branch has gone still gets its row",
         "test_aide_ledger::"
         "test_a_cell_nothing_could_measure_is_blank_and_costs_only_itself"),
        # The `mode == "pr"` arm returns before both writes.
        ("Under pr mode this verb pushes and stops, so it writes neither the "
         "tick nor a row",
         "test_aide_ledger::test_pr_mode_writes_neither_the_tick_nor_a_row"),
        # `append_ledger_row` prints and returns None; the merge has already
        # landed and `cmd_merge` reads no return code from it.
        ("A ledger write that fails is reported after the merge and never "
         "changes the exit code",
         "test_aide_ledger::"
         "test_a_ledger_that_cannot_be_written_does_not_fail_the_merge"),
        # `_promote_item_to_complete` -> `_commit_or_put_back` over the
        # snapshot `cmd_merge` took before the row; a reason there takes
        # `_restore_claim_branch` and `return 1` ahead of the push (#312).
        ("A commit of what was written that git does not make is another "
         "matter: the run pushes nothing, puts the claim branch back with its "
         "base, leaves progress.md, the ledger and insights.md as they were "
         "before the tick, and exits 1",
         ("test_aide_ledger::"
          "test_a_tick_whose_commit_fails_refuses_the_push_and_puts_everything_back",
          "test_aide_ledger::"
          "test_the_re_run_after_a_failed_tick_lands_the_item_with_one_row")),
        ("so the re-run writes the row once",
         "test_aide_ledger::"
         "test_the_re_run_after_a_failed_tick_lands_the_item_with_one_row"),
        # `tick_ci_reopening_gap`, its rel added to the tick's `extra_rels`
        # under the snapshot `cmd_merge` took before any write (#332).
        ("Where the item's latest reopening is a CI one (a reason `aide "
         "progress reopen` stamped `[CI round N]`), the open `gap` entry that "
         "reopening captured is ticked with the pointer `re-merged into <base> "
         "in CI round N` and committed with the tick",
         "test_aide_ledger::"
         "test_a_merge_back_ticks_only_its_ci_reopenings_gap_in_the_ticks_commit"),
        # `cmd_merge` returns in pr mode before the tick; `set done` never
        # calls `tick_ci_reopening_gap`.
        ("not in pr mode, where this verb writes no tick: the gap stays open, "
         "as the row stays unwritten, and `aide progress set NNN done` ticks "
         "neither",
         "test_aide_ledger::test_pr_mode_leaves_a_ci_reopenings_gap_open"),
        ("no other entry is touched, an earlier round's included",
         ("test_aide_ledger::"
          "test_a_merge_back_ticks_only_its_ci_reopenings_gap_in_the_ticks_commit",
          "test_aide_ledger::"
          "test_a_merge_back_of_an_item_whose_latest_reopening_is_not_ci_ticks_nothing")),
        ("A commit that is not made puts insights.md back with the rest",
         "test_aide_ledger::"
         "test_a_failed_tick_commit_leaves_the_ci_gap_open_and_the_re_run_ticks_it_once"),
        # `committed` (HEAD moved) keeps the commit, same refusal.
        ("A commit that is made but whose replay onto origin stops is kept, "
         "and refuses the push the same way",
         "test_aide_ledger::"
         "test_a_tick_whose_replay_stopped_keeps_its_commit_and_pushes_nothing"),
        # `review_is_off(config)` -> `_ledger_count_cells(no_review=...)`,
        # which renders `LEDGER_NO_REVIEW_CELL` for every rank the caller left
        # out. Both guards, because the marker would be unconditional and the
        # first alone would still pass.
        ("Where it is off no reviewer ran, so the three of them are written "
         "as `-` rather than left blank",
         ("test_aide_ledger::test_merge_under_review_off_marks_the_finding_cells",
          "test_aide_ledger::"
          "test_merge_under_review_on_leaves_the_finding_cells_blank")),
        # `_ledger_count_cells`: `absent` is the marker only where `findings`
        # is empty, so any count passed takes the whole row back to blanks.
        ("--findings passed anyway under off wins over the mark",
         "test_aide_ledger::test_findings_passed_under_review_off_win_over_the_mark"),
        # `cmd_merge` prints before deriving the row and changes no exit code.
        ("Where review is on and --findings is absent the run warns on "
         "stderr, writes the row and still exits 0",
         ("test_aide_ledger::"
          "test_merge_with_review_on_and_no_findings_warns_and_still_lands",
          "test_aide_ledger::"
          "test_merge_with_review_off_and_no_findings_does_not_warn")),
        # `recorded_suite_run` -> `run_test_suite`'s `seconds`, rounded into
        # `suite_seconds`; `inherited` is `()` for a green comparable run.
        ("the post-merge suite run's wall time in whole seconds and how many "
         "inherited failures it admitted",
         "test_aide_merge_inherited::"
         "test_a_green_run_records_its_time_and_zero_inherited"),

        # The inherited-failure gate (issue #275). `failure_identity_refusal`
        # is `None` only for `<python> -m pytest`; `run_test_suite` then adds
        # `--junitxml` and reads it.
        ("A red post-merge run is compared with the base where the test "
         "command runs pytest as a module",
         ("test_aide_merge_inherited::test_only_pytest_run_as_a_module_is_comparable",
          "test_aide_merge_inherited::test_a_tests_failed_exit_reads_the_report")),
        # `_judge_red_run` ->
        # `base_suite_run`: `git switch --detach <pre_merge>`, the run, then
        # `git switch --discard-changes <base>` in a `finally`.
        ("the same command is then run on the base as it stood before this "
         "merge, in this checkout",
         ("test_aide_merge_inherited::"
          "test_failures_the_base_already_had_are_admitted_and_recorded",
          "test_aide_merge_inherited::"
          "test_a_retried_fast_forward_finds_its_base_in_the_reflog")),
        # `base_suite_run` reads `read_suite_result` for the base's tree first.
        ("or its result reused where this repository already recorded a run "
         "of that tree",
         "test_aide_merge_inherited::test_a_retry_reuses_the_base_run_it_stored"),
        # `_judge_red_run`: no id outside the base's set -> `tuple(old)`;
        # `cmd_merge` prints the report and writes `len(inherited)`.
        ("When every failure after the merge also fails at the base, the "
         "failures are inherited rather than this item's: the merge is "
         "admitted, both sets are printed, the row's Inherited cell counts "
         "them",
         "test_aide_merge_inherited::"
         "test_failures_the_base_already_had_are_admitted_and_recorded"),
        # `route_inherited_failures` -> `inherited_failures_entry`, which
        # drops ids `_names_id` finds in an open entry; the path joins
        # `extra_rels` for the tick's one commit.
        ("one defect entry naming those no open insights.md entry names yet "
         "is committed with the tick",
         ("test_aide_merge_inherited::"
          "test_failures_the_base_already_had_are_admitted_and_recorded",
          "test_aide_merge_inherited::"
          "test_a_second_item_over_the_same_red_base_adds_no_second_entry",
          "test_aide_merge_inherited::"
          "test_the_entry_skips_ids_an_open_entry_names_and_caps_its_list")),
        # `_judge_red_run`: `new` non-empty -> `None`, with both lists.
        ("A failure the base does not have refuses the tick and the push, "
         "listed apart from the inherited ones",
         "test_aide_merge_inherited::"
         "test_a_failure_the_base_does_not_have_is_refused_and_listed_apart"),
        # `failure_identity_refusal`, `run_test_suite`'s exit check and
        # `landed_pre_merge_base` returning None each set `why`.
        ("Any other runner, an order-dependent flag (-x, --maxfail, --lf, "
         "--ff, --sw), a pytest exit other than 1 and a base that cannot be "
         "identified keep the plain gate, where any red run refuses",
         ("test_aide_merge_inherited::"
          "test_a_command_that_cannot_be_compared_keeps_the_plain_gate",
          "test_aide_merge_inherited::"
          "test_an_order_dependent_flag_is_found_and_a_value_is_not_one",
          "test_aide_merge_inherited::"
          "test_a_pytest_exit_other_than_one_names_no_failures",
          "test_aide_merge_inherited::"
          "test_a_fast_forward_the_reflog_does_not_record_is_not_guessed")),
        # `suite_seconds` stays None under `args.no_test`; `inherited` stays
        # None wherever `failure_identity_refusal` answered.
        ("The Suite s cell is blank under --no-test, and Inherited is blank "
         "wherever no comparison could be made",
         ("test_aide_merge_inherited::"
          "test_no_test_leaves_both_suite_cells_blank",
          "test_aide_merge_inherited::"
          "test_a_green_run_nothing_could_compare_leaves_inherited_blank")),
        # `validated_suite_run` before `recorded_suite_run`; its `why` is
        # printed where it finds nothing to take. `--no-test` skips both.
        ("Before running the suite it looks for a run `aide test` recorded "
         "of the same tree on the claim branch, and takes that run in place "
         "of its own where `aide test -h` says it may",
         ("test_aide_merge_inherited::"
          "test_a_fast_forward_merge_takes_the_validated_run",
          "test_aide_merge_inherited::"
          "test_no_test_takes_no_recorded_run_either")),
        ("Any other merge runs the suite, and prints why it could not reuse "
         "one",
         ("test_aide_merge_inherited::"
          "test_a_merge_over_a_moved_base_runs_the_suite",
          "test_aide_merge_inherited::"
          "test_a_run_from_before_a_code_change_is_not_taken")),
    ],

    # ----------------------------------------------------------------- test --
    "test": [
        # `cmd_test` returns `run.returncode` from `recorded_suite_run`.
        ("exits with the command's own exit code",
         ("test_aide_merge_inherited::"
          "test_aide_test_records_its_run_with_the_branch_and_commit",
          "test_aide_merge_inherited::"
          "test_aide_test_over_a_dirty_tree_records_nothing_and_says_so")),
        # `recorded_suite_run(by=SUITE_RECORDED_BY_TEST)` writes `by`,
        # `branch` and `commit` beside PR A's fields, under the same key.
        ("the branch and commit it ran at, in the same store under the git "
         "directory that `aide merge` keeps its base runs in",
         "test_aide_merge_inherited::"
         "test_aide_test_records_its_run_with_the_branch_and_commit"),
        # `recorded_suite_run`: `tree_is_clean` before the run, and
        # `_head_commit` compared before and after it.
        ("The result is recorded where the tree has no tracked change and "
         "HEAD does not move during the run",
         ("test_aide_merge_inherited::"
          "test_aide_test_over_a_dirty_tree_records_nothing_and_says_so",
          "test_aide_merge_inherited::"
          "test_a_run_whose_head_moved_is_not_recorded",
          "test_aide_merge_inherited::"
          "test_a_run_whose_tree_changed_is_not_recorded")),
        # `tree_is_clean` is false -> `tree` None -> nothing written, and
        # `cmd_test` prints NOT recorded on stderr.
        ("A run over a tree with tracked changes is not recorded, and says so "
         "on stderr",
         "test_aide_merge_inherited::"
         "test_aide_test_over_a_dirty_tree_records_nothing_and_says_so"),
        # `validated_suite_run`: HEAD's tree == the tip's tree, else the
        # base-had-moved reason and `recorded_suite_run`.
        ("`aide merge` takes a recorded run in place of its own suite run "
         "when the post-merge tree is the claim branch's tip tree",
         ("test_aide_merge_inherited::"
          "test_a_fast_forward_merge_takes_the_validated_run",
          "test_aide_merge_inherited::"
          "test_a_merge_over_a_moved_base_runs_the_suite")),
        # `data["by"] == "aide test"`, `data["branch"] == branch` and
        # `data["checkout"] == _checkout_id(repo_root)`.
        ("the run was recorded by this verb on that claim branch in the same "
         "checkout",
         ("test_aide_merge_inherited::"
          "test_a_run_recorded_on_another_branch_is_not_taken",
          "test_aide_merge_inherited::"
          "test_a_run_recorded_in_another_checkout_is_not_taken")),
        # `_contains(commit, tip)`, then `git diff --name-only commit tip`
        # minus progress.md must be empty.
        ("at a commit the tip contains, with nothing but the progress "
         "document changed since",
         ("test_aide_merge_inherited::"
          "test_a_fast_forward_merge_takes_the_validated_run",
          "test_aide_merge_inherited::"
          "test_a_run_from_before_a_code_change_is_not_taken")),
        # `cmd_merge`: `post = validated.run`, then the unchanged green /
        # `_judge_red_run` branches.
        ("judges the run exactly as one of its own",
         ("test_aide_merge_inherited::"
          "test_a_red_validated_run_still_meets_the_base",
          "test_aide_merge_inherited::"
          "test_a_red_validated_run_with_a_new_failure_is_refused")),
        # `suite_cell` + `LEDGER_REUSED_SUFFIX`; `ledger_warnings` accepts it
        # in Suite s alone.
        ("writes the row's Suite s cell as the recorded run's seconds "
         "followed by (reused)",
         ("test_aide_merge_inherited::"
          "test_a_fast_forward_merge_takes_the_validated_run",
          "test_aide_merge_inherited::"
          "test_a_reused_suite_cell_reads_and_nothing_else_does")),
    ],

    # --------------------------------------------------------------- ledger --
    "ledger": [
        # `cmd_ledger`: `if args.rounds is None: … return 2`, before any write.
        ("--rounds is required and the verb exits 2 without it",
         "test_aide_ledger::"
         "test_abandon_without_rounds_exits_two_and_writes_nothing"),
        # `_ledger_diff_cells` returns ("", "") with no branch; every other
        # cell is read from the documents.
        ("a branch already gone costs the two diff cells and nothing else on "
         "the row",
         "test_aide_ledger::"
         "test_abandon_with_no_branch_left_blanks_the_two_diff_cells"),
        # `ledger_cells`: a rank absent from `findings` renders "".
        ("--findings is optional, and a rank left out of it is a blank cell",
         "test_aide_ledger::"
         "test_abandon_records_the_round_count_and_leaves_progress_alone"),
        # `cmd_ledger` scans `ledger_rows` for an abandoned row of this item
        # before deriving anything, and returns 0 without appending.
        ("An item already recorded as abandoned with the same counts is not "
         "recorded twice: a re-run appends nothing and exits 0, while a "
         "different count is a new abandonment and a new row",
         ("test_aide_ledger::test_abandon_run_twice_records_the_item_once",
          "test_aide_ledger::"
          "test_abandon_with_different_counts_is_a_second_abandonment")),
        # `cmd_ledger` calls neither `set_item_status` nor `_promote_…`.
        ("It writes the ledger and nothing else: progress.md keeps whatever "
         "status the run left it",
         "test_aide_ledger::"
         "test_abandon_records_the_round_count_and_leaves_progress_alone"),
        # `append_ledger_row`, shared with `merge`.
        ("The file is created from .aide/templates/ledger.md when this is the "
         "first row",
         "test_aide_ledger::test_the_first_row_creates_the_ledger_from_the_template"),
        # `cmd_ledger` reads `review_is_off` and hands it to the same renderer
        # `merge` uses — including for the duplicate check, which compares the
        # cells it is about to write.
        ("except under a project whose [loop] review is off, where the three "
         "finding cells carry the same `-` mark `merge` writes",
         ("test_aide_ledger::test_abandon_under_review_off_marks_the_finding_cells",
          "test_aide_ledger::"
          "test_abandon_run_twice_under_review_off_still_records_the_item_once")),
    ],

    # ---------------------------------------------------------------- queue --
    # The description block states `start`'s cap and stack shape and `gate`
    # (issue #302), then `restack` (issue #301); `tidy` is stated in its
    # option help, which this row does not cover.
    "queue": [
        # `_unmerged_queue_branches` -> `_stack_own_landing`, the verdict
        # `_queue_restack`'s plan loop reads too.
        ("A queue branch is unmerged until its own work has landed in "
         "main_branch, judged exactly as restack judges it",
         ("test_aide_queue_stack::test_a_queue_whose_work_landed_no_longer_counts",
          "test_aide_queue_stack::test_below_the_cap_a_queue_stacks_on_the_top_and_records_it")),
        # `remote` in `_unmerged_queue_branches`, judged as `origin/<b>`.
        ("off local mode, over origin's queue branches as last fetched too",
         "test_aide_queue_stack::test_a_queue_only_origin_has_counts_as_unmerged"),
        # `_stack_own_landing` -> None is kept in the dict, and counted.
        ("one git cannot judge counts as unmerged",
         "test_aide_queue_stack::test_a_queue_git_cannot_judge_counts_as_unmerged"),
        # `len(unmerged) >= cap` -> `return 3`, before `--dry-run` returns.
        ("start refuses, exit 3, when [loop] max_open_queues (default 1) "
         "queue branches are already unmerged, naming them and the key",
         ("test_aide_queue_stack::test_the_default_cap_refuses_a_second_queue_while_the_first_is_unmerged",
          "test_aide_queue_stack::test_below_the_cap_a_queue_stacks_on_the_top_and_records_it")),
        # `if not args.specs:` around the whole block; `_is_stack_branch`
        # never matches `specs-queue-`.
        ("--specs creates <prefix>specs-queue-NNN instead, which is never "
         "counted or stacked",
         "test_aide_queue_stack::test_a_specs_queue_branch_is_neither_counted_nor_capped"),
        # `_stack_top_refusal`: `base not in unmerged`, then the chain walk.
        ("--base names an unmerged queue branch, and walking recorded bases "
         "down from it reaches every unmerged queue branch",
         ("test_aide_queue_stack::test_a_base_beside_the_stack_is_refused",
          "test_aide_queue_stack::test_a_base_that_would_fork_the_stack_is_refused")),
        ("A base beside the stack (main_branch included), a base another "
         "unmerged branch is already stacked on, and an unmerged branch "
         "outside that walk are refused, exit 1",
         ("test_aide_queue_stack::test_a_base_beside_the_stack_is_refused",
          "test_aide_queue_stack::test_a_base_that_would_fork_the_stack_is_refused")),
        ("--dry-run runs every check and changes nothing",
         ("test_aide_queue_stack::test_the_cap_is_checked_by_a_dry_run_too",
          "test_aide_queue_stack::test_a_dry_run_refuses_a_bad_stack_shape_and_creates_nothing")),
        # The cap refusal's remedies, each followed by a test until the
        # refusal clears (PR #308 review: `restack` was printed as one, and
        # has no stack to read when only main is behind).
        # `remedy` branches on `mode != "local" and _has_origin`.
        ("A branch whose PR merged counts until this checkout's main_branch "
         "holds its work, so updating main_branch is what clears it: a pull "
         "from origin where there is one",
         "test_aide_queue_stack::test_a_pr_merged_on_origin_clears_once_main_is_updated_from_origin"),
        ("and in local mode or with no origin, merging the queue branch into "
         "main_branch",
         "test_aide_queue_stack::test_the_cap_refusal_in_local_mode_names_a_local_merge_and_it_clears"),
        ("one git cannot judge is cleared by `aide gc --merged --yes` if it "
         "landed, or by `aide queue restack NNN --base main_branch`, which "
         "records its start, if it is open",
         ("test_aide_queue_stack::test_a_landed_branch_git_cannot_judge_clears_once_gc_deletes_it",
          "test_aide_queue_stack::test_an_open_branch_git_cannot_judge_is_read_once_its_start_is_recorded")),
        # `max_open_queues(config)` -> `return 1` before any branch exists.
        ("an invalid max_open_queues",
         "test_aide_queue_stack::test_an_unusable_cap_refuses_the_start_and_fails_the_check"),
        # `_queue_gate`, setting "queue": one row, `item_ranges(items)`.
        ("\"queue\" writes one row, Gate cell `Queue NNN plan reviewed before "
         "build` (`Queues NNN–MMM plan reviewed before build` for a range), "
         "blocking every item those queue files list",
         ("test_aide_queue_stack::test_queue_raises_one_gate_over_the_queue_s_items_and_commits_it",
          "test_aide_queue_stack::test_queue_through_raises_one_gate_over_both_queues")),
        # `queue_opened_stages`.
        ("the queues open stage N when one of their items is referenced by a "
         "stage N deliverable in progress.md and no item stage N's "
         "deliverables reference is listed in a queue file numbered below NNN",
         "test_aide_queue_stack::test_stage_raises_a_stage_gate_only_for_a_queue_that_opens_one"),
        ("\"none\" writes nothing and says so",
         "test_aide_queue_stack::test_none_raises_nothing_and_exits_zero"),
        # `present` holds every row's gate hash, whatever its Status.
        ("A row whose Gate cell the table already holds is not written again, "
         "whatever its status, so a re-run raises nothing new",
         ("test_aide_queue_stack::test_a_second_run_raises_nothing_new",
          "test_aide_queue_stack::test_an_approved_gate_is_not_raised_again")),
        # `add_gate_rows`; `_commit_docs_files` unless `--no-commit`.
        ("appended to the ## Human gates table (made at the end of "
         "progress.md when the section is absent) and committed on the "
         "current branch like every document verb, unless --no-commit",
         ("test_aide_queue_stack::test_queue_raises_one_gate_over_the_queue_s_items_and_commits_it",
          "test_aide_queue_stack::test_a_progress_file_with_no_gates_section_gets_one")),
        ("Every other row is left as it is",
         "test_aide_queue_stack::test_stage_raises_a_stage_gate_only_for_a_queue_that_opens_one"),
        ("1: a queue file missing or listing no items, no progress.md, an "
         "invalid plan_review, or a failed commit",
         ("test_aide_queue_stack::test_gate_refusals_and_usage",
          "test_aide_queue_stack::test_a_queue_listing_no_items_is_refused",
          "test_aide_queue_stack::test_gate_without_a_progress_file_is_refused",
          "test_aide_queue_stack::test_an_unusable_plan_review_refuses_and_fails_the_check",
          "test_aide_queue_stack::test_gate_whose_commit_fails_changes_nothing_and_a_retry_commits")),
        # `ppath.write_bytes(original)` when HEAD did not move.
        ("where no commit was made, progress.md is put back byte for byte, "
         "so a re-run raises and commits the gate",
         "test_aide_queue_stack::test_gate_whose_commit_fails_changes_nothing_and_a_retry_commits"),
        # `_queue_pr` (issue #330): `_recorded_branch_base`, `gh pr create
        # --draft --base <base> --head <branch>`, nothing else asked to change.
        ("pr [NNN] opens the draft pull request of queue branch "
         "<prefix>queue-NNN (default: the current branch, which must be one) "
         "against the base `queue start` recorded, and does nothing else",
         ("test_aide_queue_pr::test_pr_pushes_first_and_opens_a_draft_against_the_recorded_base",
          "test_aide_queue_pr::test_pr_on_a_stacked_queue_targets_the_queue_below")),
        # `_queue_pr_title` over `_branch_queue_files`.
        ("Its title is `aide: work queue NNN`, or `aide: work queues NNN-MMM` "
         "when the branch also adds queue file MMM",
         ("test_aide_queue_pr::test_pr_pushes_first_and_opens_a_draft_against_the_recorded_base",
          "test_aide_queue_pr::test_pr_titles_a_maintenance_and_stage_pair_by_both_numbers")),
        # `(args.body is None) == (args.body_file is None)` -> 2.
        ("its body is exactly one of --body or --body-file",
         ("test_aide_queue_pr::test_pr_takes_exactly_one_body",
          "test_aide_queue_pr::test_pr_on_a_stacked_queue_targets_the_queue_below")),
        # `_push_if_ahead` before `pr create` and before `pr ready`.
        ("It pushes the branch first where origin lacks commits the branch has",
         ("test_aide_queue_pr::test_pr_pushes_first_and_opens_a_draft_against_the_recorded_base",
          "test_aide_queue_pr::test_ready_pushes_first_then_marks_the_draft_ready")),
        ("A branch that already has an open or draft PR is left alone, exit 0",
         "test_aide_queue_pr::test_pr_names_the_open_pr_and_opens_nothing"),
        # `_queue_pr_branch`, then the base, ahead and PR-state refusals.
        ("It refuses, exit 1: a branch that is not a queue branch, local mode "
         "or no origin, no recorded base, no commits ahead of that base, a PR "
         "on the branch that was closed or merged (no second one is opened "
         "over it), a forge that could not be asked, and a failed push or "
         "create",
         ("test_aide_queue_pr::test_off_a_queue_branch_both_refuse_and_ask_nothing",
          "test_aide_queue_pr::test_local_mode_and_no_origin_both_refuse_and_ask_nothing",
          "test_aide_queue_pr::test_pr_refuses_a_branch_with_nothing_ahead_of_its_base",
          "test_aide_queue_pr::test_pr_opens_no_second_pr_over_a_closed_or_merged_one",
          "test_aide_queue_pr::test_pr_refuses_where_the_forge_cannot_be_asked",
          "test_aide_queue_pr::test_pr_that_the_forge_refuses_exits_1")),
        # `_queue_ready`: `gh pr ready N` on a draft, nothing on an open PR.
        ("ready [NNN] marks that branch's pull request ready for review, and "
         "does nothing else",
         ("test_aide_queue_pr::test_ready_pushes_first_then_marks_the_draft_ready",
          "test_aide_queue_pr::test_ready_names_its_queue_from_another_branch")),
        ("A PR already ready is left alone, exit 0, and says so",
         "test_aide_queue_pr::test_ready_leaves_a_ready_pr_alone_and_exits_0"),
        # `args.undo`: `gh pr ready N --undo`, returned before `_push_if_ahead`.
        ("--undo turns the PR back into a draft for a fix round, and pushes "
         "nothing; one already a draft is left alone, exit 0",
         ("test_aide_queue_pr::test_undo_turns_a_ready_pr_back_to_draft_and_pushes_nothing",
          "test_aide_queue_pr::test_undo_leaves_a_draft_alone_and_exits_0")),
        # `_queue_stray_options`, first thing in `cmd_queue`.
        ("An option the action does not read is refused, exit 2, before "
         "anything is done",
         ("test_aide_queue_pr::test_an_option_the_action_does_not_read_is_refused",
          "test_aide_queue_pr::test_the_older_actions_refuse_the_pr_options")),
        ("Both refuse, exit 1: a branch that is not a queue branch, local mode "
         "or no origin, a branch with no PR (`queue pr` opens it), a PR closed "
         "or merged, a forge that could not be asked, and a failed push or "
         "change",
         ("test_aide_queue_pr::test_off_a_queue_branch_both_refuse_and_ask_nothing",
          "test_aide_queue_pr::test_local_mode_and_no_origin_both_refuse_and_ask_nothing",
          "test_aide_queue_pr::test_ready_refuses_a_branch_with_no_pr_to_mark",
          "test_aide_queue_pr::test_ready_refuses_where_the_forge_cannot_be_asked",
          "test_aide_queue_pr::test_ready_that_the_forge_refuses_exits_1")),
        # `_queue_restack` reads `_recorded_branch_base` for every
        # `_is_stack_branch`, which matches `queue-NNN` and not `specs-queue-`.
        ("The stack is read from the base each queue branch recorded at "
         "`queue start`",
         ("test_aide_restack::test_a_moved_lower_branch_is_merged_forward_and_never_rebased",
          "test_aide_restack::test_an_unrecorded_queue_branch_is_listed_and_never_chained")),
        ("a specs-queue branch is never part of one",
         "test_aide_restack::test_a_specs_queue_branch_is_never_part_of_a_stack"),
        # The plan loop: `lower in changed or not _is_ancestor(lower, b)`.
        ("Bottom up, each lower branch is merged into the one above it "
         "wherever the upper does not already contain it",
         ("test_aide_restack::test_a_moved_lower_branch_is_merged_forward_and_never_rebased",
          "test_aide_restack::test_a_merge_propagates_up_a_stack_of_three")),
        # `_restack_merge` writes a two-parent commit or fast-forwards; no
        # `rebase`, and `_push_new_branch` is `push -u`, never `--force`.
        # `_restack_merge`: `-S` when `commit.gpgSign`, on `commit-tree`;
        # `git merge` honours it natively and takes `--no-verify`.
        ("Its merge commits honour commit.gpgSign and run no commit hook, on "
         "every git version",
         ("test_aide_restack::test_a_signing_failure_stops_the_run_with_nothing_moved",
          "test_aide_restack::test_no_commit_hook_runs_on_either_path")),
        ("It merges and never rebases, so nothing is ever force-pushed",
         ("test_aide_restack::test_a_moved_lower_branch_is_merged_forward_and_never_rebased",
          "test_aide_restack::test_review_edits_on_origin_are_fetched_merged_forward_and_pushed")),
        # The plan loop judges `b` itself first — `_stack_branch_landed` on
        # its own tip, before `lower in landed` is looked at.
        ("Each stack branch's own landing is judged at its own step, whatever "
         "lies below it",
         ("test_aide_restack::test_a_middle_branch_landed_over_an_open_empty_bottom_hands_on_its_upper",
          "test_aide_restack::test_two_lowers_squash_landed_before_any_restack")),
        # `_stack_branch_landed`, then the `squashed` merge base and the
        # `record` step; the landed branch gets no step at all.
        ("is left alone, and main_branch is merged into the branch above it "
         "with the landed branch's tip as the merge base, so a squash merge "
         "does not conflict with the commits it squashed; that branch's "
         "recorded base becomes main_branch",
         ("test_aide_restack::test_a_squash_merged_bottom_hands_its_upper_to_main",
          "test_aide_restack::test_a_merge_commit_landed_bottom_hands_its_upper_to_main",
          "test_aide_restack::test_two_lowers_squash_landed_before_any_restack")),
        # `_on_first_parent_chain`, then the start: past it is a
        # fast-forward landing.
        ("or by a fast-forward past the commit it started from",
         ("test_aide_restack::test_a_bottom_landed_by_fast_forward_past_its_start_hands_on_its_upper",
          "test_aide_restack::test_a_middle_branch_landed_over_an_open_empty_bottom_hands_on_its_upper")),
        # `starts.get(b) or _rev(eff(lower))`; `_is_ancestor(b, lower)` ->
        # False, then the landed-lower arm.
        ("Where a branch started is the start commit `queue start` recorded "
         "for it, or, above another branch, that branch's tip; a branch with "
         "no commits beyond its lower is not judged on its own, and is handed "
         "main_branch when its lower has landed",
         ("test_aide_restack::test_queue_start_records_the_commit_it_started_from",
          "test_aide_restack::test_a_middle_branch_landed_over_an_open_empty_bottom_hands_on_its_upper")),
        ("A branch whose tip is on main_branch's first-parent history and "
         "still at its start has no commits of its own, and is open; an open "
         "branch beneath one that landed keeps its record and is left alone, "
         "and once the branch above it is handed to main_branch it holds no "
         "stack",
         ("test_aide_restack::test_a_lower_with_no_commits_of_its_own_is_not_read_as_landed",
          "test_aide_restack::test_a_middle_branch_landed_over_an_open_empty_bottom_hands_on_its_upper")),
        # `_stack_branch_landed` -> None for a bottom only; `blocked`, `held`
        # for each upper not landed itself, `return 1`.
        ("Only a bottom branch can go unjudged: with no start recorded (one "
         "started before 2.14.0, or on another machine) git cannot tell a "
         "fast-forward landing from a branch with no commits of its own, so "
         "each branch above it that has not itself landed is left as it is, "
         "the run exits 1 and never reports the stack consistent, and the "
         "message names both remedies",
         ("test_aide_restack::test_a_fast_forwarded_bottom_with_no_start_record_is_a_stop_not_consistent",
          "test_aide_restack::test_an_empty_bottom_with_no_start_record_is_resolved_by_recording_it",
          "test_aide_restack::test_a_middle_branch_landed_over_an_open_empty_bottom_hands_on_its_upper")),
        # `_branch_content_landed` is None below 2.38 -> `_is_ancestor`.
        ("On git older than 2.38 only an ancestry merge is seen, so a "
         "squash-merged branch reads as still open",
         "test_aide_restack::test_on_old_git_a_squash_merged_bottom_reads_as_still_open"),
        # `_MERGE_BASE_OPTION_MIN_GIT` gates `--merge-base`.
        ("before 2.40 main_branch is merged over git's own merge base",
         "test_aide_restack::test_between_git_2_38_and_2_40_main_is_merged_over_git_s_own_base"),
        # `unread`: no record and not landed -> listed on stderr, no step.
        ("A queue branch with no recorded base (this checkout did not start "
         "it) is not read into any stack, and is listed with the remedy",
         "test_aide_restack::test_an_unrecorded_queue_branch_is_listed_and_never_chained"),
        # The `args.number` block: `branch --track`, then `forced`, whose
        # base is merged in and recorded as planned steps, in that order.
        ("`restack NNN --base REF` records REF as queue NNN's base, creating "
         "the local branch from origin where only origin has it, and merges "
         "REF in unless the branch has nothing REF lacks; the base is written "
         "after that merge, so a run that stops keeps the record it found",
         ("test_aide_restack::test_base_records_a_branch_s_base_and_restacks_it",
          "test_aide_restack::test_base_creates_a_branch_only_origin_has",
          "test_aide_restack::test_a_forced_base_whose_merge_conflicts_keeps_the_old_record",
          "test_aide_restack::test_an_empty_bottom_with_no_start_record_is_resolved_by_recording_it")),
        # `_record_branch_start(target, merge-base(target, REF))` when unset.
        ("Where no start is recorded it records one, the branch's merge base "
         "with REF",
         "test_aide_restack::test_an_empty_bottom_with_no_start_record_is_resolved_by_recording_it"),
        # `broken` -> `return 1` before any fast-forward or merge.
        ("A recorded base naming a queue branch this checkout does not have, "
         "or a cycle, refuses the run before anything changes",
         ("test_aide_restack::test_a_recorded_base_this_checkout_lacks_refuses",
          "test_aide_restack::test_a_cycle_of_recorded_bases_refuses",
          "test_aide_restack::test_an_unrecorded_base_below_is_not_called_a_cycle")),
        # `remote_on`: fetch, `behind` -> `_advance_branch`, `diverged` -> 1.
        ("Off local mode it fetches first, fast-forwards each stack branch "
         "origin is ahead on, refuses a branch that has diverged from origin",
         ("test_aide_restack::test_review_edits_on_origin_are_fetched_merged_forward_and_pushed",
          "test_aide_restack::test_a_branch_diverged_from_origin_is_refused")),
        # `to_push`: `changed` or `ahead`, after the execute loop finished.
        ("once every merge has succeeded pushes, without force, each stack "
         "branch it merged into or that is ahead of origin",
         ("test_aide_restack::test_review_edits_on_origin_are_fetched_merged_forward_and_pushed",
          "test_aide_restack::test_a_stack_branch_ahead_of_origin_is_pushed_by_a_re_run")),
        ("local mode never fetches or pushes",
         "test_aide_restack::test_local_mode_never_fetches_or_pushes"),
        # `_unsafe_tree_state` -> `return 1`.
        ("It needs a clean tree, and refuses a stack branch checked out in "
         "another worktree",
         ("test_aide_restack::test_an_unclean_tree_is_refused",
          "test_aide_restack::test_a_stack_branch_checked_out_in_another_worktree_refuses")),
        # `stopped` -> `return 1` before the push loop; the `finally` aborts
        # a half-merge and switches back to `start`.
        ("A conflict aborts that merge, leaves the tree clean and HEAD where "
         "it started, pushes nothing, and names both branches",
         ("test_aide_restack::test_a_conflict_stops_with_the_tree_clean_and_head_restored",
          "test_aide_restack::test_a_conflict_pushes_nothing",
          "test_aide_restack::test_a_detached_head_start_is_restored")),
        ("Merges made before it stay local, and a re-run pushes them",
         "test_aide_restack::test_a_stack_branch_ahead_of_origin_is_pushed_by_a_re_run"),
        # `if dry:` prints every step and push, writes none.
        ("--dry-run prints the merges, base records and pushes it would make "
         "and changes nothing",
         "test_aide_restack::test_dry_run_prints_the_merges_and_changes_nothing"),
        # `if not steps and not to_push: ... return 0`.
        ("Exit 0: the stack is consistent, whether or not this run merged "
         "anything; a re-run with nothing moved merges nothing and says so",
         "test_aide_restack::test_a_second_run_with_nothing_moved_merges_nothing"),
        ("1: stopped",
         ("test_aide_restack::test_a_conflict_stops_with_the_tree_clean_and_head_restored",
          "test_aide_restack::test_a_branch_diverged_from_origin_is_refused",
          "test_aide_restack::test_a_failed_push_exits_one_with_the_merge_kept_local")),
        # `(args.number is None) != (args.base is None)` -> 2.
        ("2: usage (NNN without --base, or --base without NNN)",
         "test_aide_restack::test_number_and_base_go_together"),
    ],
}

def _guards(guard) -> Tuple[str, ...]:
    return (guard,) if isinstance(guard, str) else tuple(guard)


#: one entry per pinned sentence — what `test_every_pinned_sentence...` reads.
_PINS = [(verb, sentence, _guards(guard))
         for verb, pins in HELP_PINS.items() for sentence, guard in pins]
#: one entry per (sentence, guard) pair — what `test_every_guard_resolves` reads.
_GUARD_PAIRS = [(verb, sentence, g) for verb, sentence, gs in _PINS for g in gs]
_IDS = [f"{verb}:{sentence[:48]}" for verb, sentence, _ in _PINS]
_GUARD_IDS = [f"{verb}:{g.rpartition('::')[2][:56]}"
              for verb, _, g in _GUARD_PAIRS]


# --------------------------------------------------------------------------- #
# the two obligations of a pin
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("verb,sentence,guards", _PINS, ids=_IDS)
def test_every_pinned_sentence_is_still_in_the_help(verb, sentence, guards):
    """Half one: the quotation is still what `argparse` renders.

    Without this the register is a comment — a help block could be reworded out
    from under a guard that keeps passing, which is exactly how a copy goes
    stale while its test stays green. Reflow the sentence freely; change what
    it says and fix the guard, the pin and the code together.
    """
    assert _normalise(sentence) in _normalise(_help_for(verb)), (
        f"`aide {verb} -h` no longer states: {sentence}\n"
        f"Either restore the clause, or reword the pin and re-read "
        f"{', '.join(guards)} to confirm it still exercises what the new "
        f"wording claims.")


@pytest.mark.parametrize("verb,sentence,guard", _GUARD_PAIRS, ids=_GUARD_IDS)
def test_every_guard_resolves(verb, sentence, guard):
    """Half two: the named test still exists.

    A pin whose guard was deleted or renamed proves nothing, and nothing else
    in the suite would notice — the guard is named in a string. Resolution is
    by import rather than by a text search, so a function moved out of the
    module it is named in fails here too.
    """
    module_name, _, func_name = guard.partition("::")
    assert func_name, f"guard '{guard}' is not 'module::function'"
    module = _guard_module(module_name)
    assert hasattr(module, func_name), (
        f"`aide {verb} -h`'s pin — {sentence} — names "
        f"{guard}, which no longer exists. Point it at the test that exercises "
        f"the claim today, or write one; do not delete the pin.")


_GUARD_CACHE: Dict[str, object] = {}


def _guard_module(name: str):
    """Import a sibling test module under a private name, once.

    A private name, because pytest has already imported these under their own:
    loading them again as `test_aide_git` would replace the collected module
    object mid-run. The file is located beside this one rather than through
    `sys.path`, so the lookup works the same in this repository and in the
    `.aide/scripts/tests/` copy an install ships.
    """
    if name not in _GUARD_CACHE:
        path = _HERE / f"{name}.py"
        assert path.is_file(), f"no guard module {name} beside {_HERE.name}/"
        spec = importlib.util.spec_from_file_location(f"_help_pin_{name}", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        _GUARD_CACHE[name] = module
    return _GUARD_CACHE[name]


def test_the_normaliser_still_sees_a_reword():
    """The register is only a pin while `_normalise` can fail.

    `tests/test_rule_pins.py` holds the same line for the adapter's copies: a
    normaliser loose enough to let a reworded sentence through turns every
    assertion above into one that cannot fail. Reflow, emphasis and case are
    absorbed; a changed word is not.
    """
    assert _normalise("a **stage**\nis  ✅") == _normalise("A stage is ✅")
    assert _normalise("`aide gc`") == _normalise("aide gc")
    assert _normalise("a stage is ✅") != _normalise("a stage is 🚧")
    assert _normalise("all ✅") != _normalise("not all ✅")


def test_every_verb_with_a_description_block_is_registered():
    """Seven blocks, seven entries — the register is the whole row, not a
    sample of it. A verb that grows a description block and no pin would be a
    copy of engine text with nobody deciding anything about it, which is the
    state issue #205 exists to end."""
    described = {verb for verb in _verbs() if _described(verb)}
    assert described == set(HELP_PINS), (
        f"described but unpinned: {sorted(described - set(HELP_PINS))}; "
        f"pinned but no longer described: {sorted(set(HELP_PINS) - described)}")
    # An empty list is a key, not a decision: without this, registering
    # `"newverb": []` satisfies the equality above while pinning nothing.
    assert all(HELP_PINS.values()), (
        f"registered with no pins: "
        f"{sorted(v for v, pins in HELP_PINS.items() if not pins)}")


def _verbs() -> List[str]:
    parser = aide.build_parser()
    return [v for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
            for v in action.choices]


def test_the_usage_block_names_every_verb_the_parser_has():
    """The ``Subcommands::`` block at the top of ``aide -h`` is typed by hand,
    and 1.58.0 added ``ledger`` to the parser without adding it there."""
    listed = set(re.findall(r"^    python \.aide/scripts/aide\.py (\S+)",
                            aide.__doc__, flags=re.M))
    assert listed == set(_verbs()), (
        f"in the parser, not the usage block: {sorted(set(_verbs()) - listed)}; "
        f"in the usage block, not the parser: {sorted(listed - set(_verbs()))}")


def _described(verb: str) -> bool:
    """Whether *verb* carries a description block, not just option help."""
    parser = aide.build_parser()
    sub = next(action.choices[verb] for action in parser._actions
               if isinstance(action, argparse._SubParsersAction))
    return bool((sub.description or "").strip())


# --------------------------------------------------------------------------- #
# the guards written for this row — document-tree checks, no git needed
# --------------------------------------------------------------------------- #
AIDE_TOML = """\
[project]
name = "Demo"
docs_dir = "docs/aide"
"""

PROGRESS = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | Rules | G1 | 🚧 |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 1 | 🚧 |

## Stage 1 — Rules — 🚧

**Deliverables.**
- 📋 Bounds. *(Item 027)*
- 📋 Coverage. *(Item 028)*

**Acceptance.**
- [ ] Rules fire.
"""


def _repo(tmp_path: Path, progress: str = PROGRESS, name: str = "repo") -> Path:
    repo = tmp_path / name
    ddir = repo / "docs" / "aide"
    ddir.mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (ddir / "progress.md").write_text(progress, encoding="utf-8")
    # A loop repo has an inbox, so nothing below is reporting on a file the
    # run itself created.
    (ddir / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    return repo


def _checks(repo: Path):
    return aide.run_checks(repo, aide.load_config(repo), branches=[])


def test_check_errors_on_each_missing_table_and_on_missing_stage_sections(
        tmp_path: Path):
    """The help names three missing things; the existing test named one.

    Each is a separate `errors.append` in `run_checks`, and a document with no
    tables and no stage sections must produce all three — a check that reports
    only the first would leave a reader hunting a second document problem the
    run never mentioned.
    """
    errors, _ = _checks(_repo(tmp_path, progress="# Demo\n\nNo tables, no stages.\n"))
    assert any("missing Stage summary table" in e for e in errors), errors
    assert any("missing Objective coverage table" in e for e in errors), errors
    assert any("no '## Stage N' sections" in e for e in errors), errors


def test_the_summary_over_claim_is_measured_by_the_rollup(tmp_path: Path):
    """The error fires on the rollup, not on "every bullet is ✅".

    Until 1.49.4 the help said "deliverables not all ✅", which predicts an
    error over a stage of ✅ and ❌ — where `rollup_status` says ✅ and the
    check is silent. That is the same falsehood #205 found in the
    `progress.md` template header, one copy over.
    """
    done = PROGRESS.replace("| 1 | Rules | G1 | 🚧 |", "| 1 | Rules | G1 | ✅ |")
    done = done.replace("## Stage 1 — Rules — 🚧", "## Stage 1 — Rules — ✅")

    over_claim = done.replace("- 📋 Coverage. *(Item 028)*",
                              "- 🚧 Coverage. *(Item 028)*")
    over_claim = over_claim.replace("- 📋 Bounds. *(Item 027)*",
                                    "- ✅ Bounds. *(Item 027)*")
    errors, _ = _checks(_repo(tmp_path, progress=over_claim, name="over"))
    assert any("summary marked ✅ but has non-complete deliverables" in e
               for e in errors), errors

    excluded = done.replace("- 📋 Bounds. *(Item 027)*", "- ✅ Bounds. *(Item 027)*")
    excluded = excluded.replace("- 📋 Coverage. *(Item 028)*",
                                "- ❌ Coverage. *(Item 028)*")
    errors, _ = _checks(_repo(tmp_path, progress=excluded, name="excluded"))
    assert not any("non-complete deliverables" in e for e in errors), errors


def test_a_rolled_up_stage_under_a_lesser_summary_row_is_a_warning(tmp_path: Path):
    """The mirror of the error above, and the same measure — plus the carve-out.

    ❌ counts toward the rollup here too: a stage of ✅ and ❌ under a 🚧
    summary row is the warning, and the pre-1.49.4 wording ("deliverables are
    all ✅") predicted silence.

    The second half is `if summ == "excluded": continue`, which sits above
    **all three** stage comparisons rather than above this one: a ❌ summary
    row is a stage dropped, and its bullets no longer speak for it, so
    neither the warning, the error, nor the header-disagreement warning is
    raised over it. A ⏸️ row was left out the same way until issue #281; the
    rollup computes ⏸️ now, so a ⏸️ row over bullets that roll up to ✅ gets
    the one warning that says so, and the other two are not raised.
    """
    text = PROGRESS.replace("- 📋 Bounds. *(Item 027)*", "- ✅ Bounds. *(Item 027)*")
    text = text.replace("- 📋 Coverage. *(Item 028)*", "- ❌ Coverage. *(Item 028)*")
    _, warnings = _checks(_repo(tmp_path, progress=text))
    assert any("all deliverables ✅ but summary shows" in w for w in warnings), warnings

    for icon, name in (("⏸️", "deferred"), ("❌", "excluded")):
        # Same rolled-up stage, and a header that disagrees with the row as
        # well, so all three comparisons would have something to say.
        left_alone = text.replace("| 1 | Rules | G1 | 🚧 |",
                                  f"| 1 | Rules | G1 | {icon} |")
        errors, warnings = _checks(
            _repo(tmp_path, progress=left_alone, name=f"repo-{name}"))
        assert not any("all deliverables ✅ but summary shows" in w
                       for w in warnings), (icon, warnings)
        assert not any("disagrees with summary" in w for w in warnings), (icon, warnings)
        assert not any("non-complete deliverables" in e for e in errors), (icon, errors)
        deferred_rule = [w for w in warnings
                         if "but its deliverables roll up to" in w]
        if name == "deferred":
            # One message for the stage, naming both off cells (#285: the
            # 🚧 header is compared with the rollup too, not just with ⏸️).
            assert deferred_rule == [
                "stage 1: summary ⏸️ deferred and header 🚧 in-progress but "
                "its deliverables roll up to ✅ complete — nothing is left "
                "open to defer, so restore ✅"], warnings
        else:
            assert deferred_rule == [], warnings


def test_a_stage_header_disagreeing_with_its_summary_row_is_a_warning(
        tmp_path: Path):
    """Two records of one status, and on a stage with no deliverable bullet
    nothing else compares them. Where there are bullets, each cell is
    compared with their rollup instead (#285), and the cell that is off is
    named once — the header-against-summary warning is not raised beside it."""
    bare = PROGRESS.replace("- 📋 Bounds. *(Item 027)*\n- 📋 Coverage. *(Item 028)*\n", "")
    bare = bare.replace("## Stage 1 — Rules — 🚧", "## Stage 1 — Rules — 📋")
    _, warnings = _checks(_repo(tmp_path, progress=bare, name="bare"))
    assert any("header planned disagrees with summary in-progress" in w
               for w in warnings), warnings

    text = PROGRESS.replace("## Stage 1 — Rules — 🚧", "## Stage 1 — Rules — 📋")
    _, warnings = _checks(_repo(tmp_path, progress=text))
    stage = [w for w in warnings if w.startswith("stage 1:")]
    assert stage == [
        "stage 1: summary 🚧 in-progress but its deliverables roll up to 📋 "
        "planned — a stage's cells follow its bullets, so set the summary "
        "to 📋, or move the bullets with 'aide progress set'"], warnings


def test_a_summary_row_with_no_stage_section_is_a_warning(tmp_path: Path):
    """A row promising a stage the document does not carry: the deliverables
    behind its status cannot be read, so nothing checks the status at all."""
    text = PROGRESS.replace(
        "| 1 | Rules | G1 | 🚧 |",
        "| 1 | Rules | G1 | 🚧 |\n| 2 | Reporting | G2 | 📋 |")
    _, warnings = _checks(_repo(tmp_path, progress=text))
    assert any("stage 2" in w and "has no '## Stage 2' section" in w
               for w in warnings), warnings


def test_an_unrecognised_status_in_either_table_is_a_warning(tmp_path: Path):
    """One sentence, two tables — so one guard has to cross both.

    A mark neither table recognises is a typo, and in the gates table it also
    keeps blocking: `blocking_gates` is "not ✅ Approved", so an unreadable
    decision is never read as an approval.
    """
    text = PROGRESS + """
## Outcome targets

| Target | Objective | Baseline | Current | Status |
|--------|-----------|----------|---------|--------|
| p95 under 200ms | G1 | 400ms | 250ms | 🤷 Dunno |

## Human gates

| Gate | Blocks | Status | Notes |
|------|--------|--------|-------|
| Sign off the schema | all | 🤷 Maybe | — |
"""
    _, warnings = _checks(_repo(tmp_path, progress=text))
    assert any("unrecognised Status" in w and "p95" in w for w in warnings), warnings
    assert any("Sign off the schema" in w for w in warnings), warnings


def test_a_retracted_criterion_reaches_check_as_a_warning(tmp_path: Path):
    """Retracting is append-only, so without this the withdrawal would live
    only in one commit's diff — which is the quiet the trail exists to prevent.
    A warning, not an error: a withdrawn attestation is a normal state."""
    text = PROGRESS.replace(
        "- [ ] Rules fire.",
        "- [ ] Rules fire. *(verified 2026-07-01)*\n"
        "  - **2026-07-02** → retracted: the host was misread")
    errors, warnings = _checks(_repo(tmp_path, progress=text))
    assert any("was retracted on 2026-07-02" in w for w in warnings), warnings
    assert not any("retracted" in e for e in errors), errors


def test_a_warning_alone_still_exits_zero(tmp_path: Path, capsys):
    """`cmd_check` returns 1 iff `errors` — the whole meaning of the split.

    A run with warnings and no errors exits 0 and prints them, so a consumer
    with a known-normal state (a blocking gate, a retracted criterion) is not
    stopped by it, and an unattended loop does not stall on a report.
    """
    text = PROGRESS + """
## Human gates

| Gate | Blocks | Status | Notes |
|------|--------|--------|-------|
| Sign off the schema | all | ⏳ Awaiting | — |
"""
    repo = _repo(tmp_path, progress=text)
    assert aide.main(["--repo", str(repo), "check"]) == 0
    out = capsys.readouterr().out
    # The warning this planted, not merely "some warning" — which is also what
    # makes this the CLI half of `check -h`'s "every human gate still
    # blocking": `gate_warnings` passing in isolation says nothing about
    # `run_checks` still calling it.
    assert "warning: " in out and "Sign off the schema" in out
    # OK, not FAIL: the run counted warnings and still returned 0.
    assert "aide check: OK (" in out and "aide check: FAIL" not in out


PROGRESS_TICKED = PROGRESS.replace(
    "- [ ] Rules fire.", "- [x] Rules fire. *(validator, 2026-07-01: eval run)*")


def test_amend_and_retract_refuse_all_and_refuse_a_missing_reason(
        tmp_path: Path, capsys):
    """Two refusals `aide progress -h` states and nothing else exercised.

    `--all` is offered by `accept` and by no other action: each attestation was
    made separately, so a correction or a withdrawal that named all of them
    would be saying nothing about any of them. And both refuse an empty reason
    — `.strip()`ped, so whitespace is not a stated basis either. Exit 2, the
    usage code, and `progress.md` untouched on every path.
    """
    repo = _repo(tmp_path, progress=PROGRESS_TICKED)
    before = (repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")

    for action, flag in (("amend", "--evidence"), ("retract", "--reason")):
        assert aide.main(["--repo", str(repo), "progress", action, "1", "--all",
                          flag, "why", "--no-commit"]) == 2
        assert "--all is not offered" in capsys.readouterr().err

        assert aide.main(["--repo", str(repo), "progress", action, "1",
                          "--criterion", "1", flag, "   ", "--no-commit"]) == 2
        assert f"{flag} is required" in capsys.readouterr().err

    assert (repo / "docs" / "aide" / "progress.md").read_text(
        encoding="utf-8") == before


def test_retract_routes_its_finding_into_the_inbox(tmp_path: Path, capsys):
    """A withdrawn attestation is a finding, and the verb routes it itself.

    §1 already says a `❌ Not met` outcome target must be routed to
    `insights.md`; a retracted acceptance box is the same event one level down.
    The verb appends the `gap` line rather than asking the caller to remember,
    because the honest path has to be the cheap one or the quiet path wins.
    """
    repo = _repo(tmp_path, progress=PROGRESS_TICKED)
    assert aide.main(["--repo", str(repo), "progress", "retract", "1",
                      "--criterion", "1", "--reason", "the host was misread",
                      "--date", "2026-07-02", "--no-commit"]) == 0
    assert "captured a gap entry" in capsys.readouterr().out

    inbox = (repo / "docs" / "aide" / "insights.md").read_text(encoding="utf-8")
    assert "- [ ] gap — acceptance criterion retracted: the host was misread" in inbox
    assert "stage 1 criterion 1, 2026-07-02" in inbox
    # And the box really did open again, so the entry is not describing a
    # retraction that never happened.
    progress = (repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")
    assert "- [ ] Rules fire." in progress


def test_reword_with_nothing_to_mirror_writes_progress_alone(
        tmp_path: Path, capsys):
    """The outcome `reword`'s both-or-neither sentence left out (issue #216).

    A roadmap stage written as prose, and a repo with no roadmap.md at all,
    have no acceptance block to drift from: the verb succeeds, changes
    progress.md, leaves roadmap.md byte for byte, and says there was nothing
    to mirror — rather than refusing, or implying roadmap.md moved.
    """
    prose = "# R\n\n## Stage 1 — Rules\n\nProse only, no acceptance block.\n"
    for name, roadmap in (("prose", prose), ("absent", None)):
        repo = _repo(tmp_path, name=name)
        road = repo / "docs" / "aide" / "roadmap.md"
        if roadmap is not None:
            road.write_text(roadmap, encoding="utf-8")
        assert aide.main(["--repo", str(repo), "progress", "reword", "1",
                          "--criterion", "1", "--text", "Every rule fires.",
                          "--no-commit"]) == 0, name
        out = capsys.readouterr().out
        assert "nothing to mirror" in out and "mirrored" not in out, (name, out)
        progress = (repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")
        assert "- [ ] Every rule fires." in progress, name
        assert "- [ ] Rules fire." not in progress, name
        if roadmap is None:
            assert not road.exists(), name
        else:
            assert road.read_text(encoding="utf-8") == roadmap, name


def test_status_prints_the_four_states_it_promises(tmp_path: Path, capsys):
    """`aide status -h` names four, and each has its own loop in `cmd_status`.

    They are one sentence because they share one reason: each is a state
    `progress.md` records and no other line of the report would surface, so a
    reader who never re-opens the document would never learn of it.
    """
    text = PROGRESS + """
## Outcome targets

| Target | Objective | Baseline | Current | Status |
|--------|-----------|----------|---------|--------|
| p95 under 200ms | G1 | 400ms | 250ms | ❌ Not met |

## Human gates

| Gate | Blocks | Status | Notes |
|------|--------|--------|-------|
| Sign off the schema | all | ⏳ Awaiting | — |
| Confirm the budget | 027 | ⏳ Awaiting | a | stray pipe |
"""
    text = text.replace(
        "- [ ] Rules fire.",
        "- [ ] Rules fire. *(verified 2026-07-01)*\n"
        "  - **2026-07-02** → retracted: the host was misread")
    repo = _repo(tmp_path, progress=text)
    assert aide.main(["--repo", str(repo), "status", "--no-fetch"]) == 0
    out = capsys.readouterr().out
    assert "gate 1: Sign off the schema" in out
    assert "target: p95 under 200ms" in out
    assert "retracted: stage 1 criterion 1" in out
    assert "unreadable: progress.md:" in out and "human-gate row" in out
