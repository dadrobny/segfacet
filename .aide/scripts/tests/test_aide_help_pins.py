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
  separately"* (`progress`), *"the stage is deferred or dropped, so its bullets
  no longer speak for it"* (`check`) — rationale for a rule pinned beside them,
  not a second rule.
* *"since the row is dropped from every check it would have fed"*, *"the
  goal-level mirror of that over-claim"*, *"a normal state rather than a
  defect"* (twice), *"a satisfied profile under an unverified row is a row
  this machine can verify now"* (`status`), *"that would be recommending the deletion of an open PR's
  head branch"*, *"Because in `pr` mode nothing inside the loop observes the
  merge"*, *"so none of them lives only in one commit's diff"*, *"since what it
  blocks is unknown"* — same: the reason a pinned behaviour is what it is.
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

        # `run_checks`: `has_stage_table` / `has_obj_table` / `sections`, each
        # appending to `errors`.
        ("a missing stage summary table, objective coverage table or stage "
         "section",
         "test_aide_help_pins::"
         "test_check_errors_on_each_missing_table_and_on_missing_stage_sections"),
        # `if summ == "complete" and derived and derived != "complete"` — the
        # measure is `rollup_status`, under which a ❌ bullet counts toward ✅.
        ("a stage summary row marked ✅ over a stage whose deliverables do "
         "not roll up to ✅",
         "test_aide_help_pins::test_the_summary_over_claim_is_measured_by_the_rollup"),
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
        # `if derived == "complete" and summ and summ != "complete"` — the
        # mirror of the error above, and the same measure.
        ("a stage whose deliverables roll up to ✅ under a summary row "
         "that is not",
         "test_aide_help_pins::"
         "test_a_rolled_up_stage_under_a_lesser_summary_row_is_a_warning"),
        # `if header_status and summ and header_status != summ`.
        ("a stage header disagreeing with its summary row",
         "test_aide_help_pins::"
         "test_a_stage_header_disagreeing_with_its_summary_row_is_a_warning"),
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
        # `if summ in ("deferred", "excluded"): continue` — before all three
        # of the comparisons above, not just the warning.
        ("A summary row marked \u23f8\ufe0f or \u274c is left out of all three "
         "stage comparisons above, deliverables and header alike",
         "test_aide_help_pins::"
         "test_a_rolled_up_stage_under_a_lesser_summary_row_is_a_warning"),
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
        # …and deliberately does not match a glob against a literal.
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
        # `for stg, cn, cdate, creason in retracted_criteria(lines)` in
        # run_checks, appending to `warnings`.
        ("every retracted acceptance criterion",
         "test_aide_help_pins::test_a_retracted_criterion_reaches_check_as_a_warning"),
        # `insight_warnings` -> `_INSIGHT_FULL_LOOSE_RE` around a strict `_DATE_RE`.
        ("an insights entry whose shape is off — loose either side of the "
         "date, strict about the date",
         "test_aide_insights::test_the_date_stays_strict_where_the_provenance_relaxed"),
        # `insight_warnings` reads insights.md only; archive-*.md is skipped.
        ("never applied to an archived entry",
         "test_aide_insights::test_an_archive_is_frozen_and_not_shape_checked"),
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
        # Neither is in the `("complete", "excluded")` set of the ✅ rule.
        ("\U0001f50d and \u23f8\ufe0f are both kept out of the \u2705 rule",
         ("test_aide_core::test_a_deferred_deliverable_keeps_its_stage_open",
          "test_aide_git::test_in_review_rolls_a_stage_up_to_in_progress_not_complete")),
        # 🔍 *is* in the `("complete", "in-progress", "in-review")` set of the
        # 🚧 rule; ⏸️ is in neither, which is the whole difference.
        ("\U0001f50d also satisfies the \U0001f6a7 rule, so a stage holding "
         "one is always \U0001f6a7",
         "test_aide_git::test_in_review_rolls_a_stage_up_to_in_progress_not_complete"),
        ("a stage whose bullets are only \u23f8\ufe0f, \U0001f4cb and \u274c "
         "reads \U0001f4cb",
         "test_aide_core::test_a_deferred_deliverable_keeps_its_stage_open"),
        # `_set_stage_header`, `_set_summary_row`, `_apply_objective_rollup`.
        ("The stage header, its summary-table row, and any Objective row "
         "delivered solely by \u2705 stages follow",
         ("test_aide_core::test_set_item_done_completes_stage_without_touching_acceptance",
          "test_aide_core::test_met_target_does_not_block_objective")),
        # `_apply_objective_rollup` consults `outcome_targets` first.
        ("an objective linked to an Outcome target that is not \u2705 Met "
         "never rolls up",
         "test_aide_core::test_unmet_target_blocks_objective_rollup_not_stage"),
        # `RANK` guards the write: a lower-ranked status is not applied.
        ("A status is never downgraded",
         "test_aide_core::test_set_item_never_downgrades"),
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
        ("the one in-place edit — tick entry N with --pointer",
         "test_aide_insights::test_tick_flips_the_box_and_records_where_it_landed"),
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
         "label its ## Testing Strategy names",
         ("test_aide_traceability::test_scope_warns_on_a_test_naming_neither",
          "test_aide_traceability::test_scope_is_silent_when_every_added_test_is_traced")),
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
    # The ledger row (issue #244); everything else `merge` does is stated in
    # its option help, which this register does not read.
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

    The second half is `if summ in ("deferred", "excluded"): continue`, which
    sits above **all three** stage comparisons rather than above this one: a
    ⏸️ or ❌ summary row is a stage deferred or dropped, and its bullets no
    longer speak for it, so neither the warning, the error, nor the
    header-disagreement warning is raised over it.
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


def test_a_stage_header_disagreeing_with_its_summary_row_is_a_warning(
        tmp_path: Path):
    """Two records of one status, and nothing else compares them."""
    text = PROGRESS.replace("## Stage 1 — Rules — 🚧", "## Stage 1 — Rules — 📋")
    _, warnings = _checks(_repo(tmp_path, progress=text))
    assert any("header planned disagrees with summary in-progress" in w
               for w in warnings), warnings


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
