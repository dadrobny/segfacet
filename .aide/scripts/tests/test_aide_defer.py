"""Deferring an item, and a stage that rolls up to ⏸️ (issue #281).

A project owner deferred a whole roadmap stage and nothing in the CLI could
record it: `aide progress set` took only in-progress, in-review and done, so ⏸️
on a bullet was a hand edit with no why on the record; the rollup never
yielded ⏸️, so a deferred stage read 📋 like one nobody had started; and a
hand-set ⏸️ summary row was skipped by `aide check` without a word.

`aide progress set NNN deferred --reason …` now flips the item's bullets to ⏸️
with a dated `deferred: <reason>` trail line under each, the rollup reads ⏸️
once nothing but deferred work is left open, and `check` warns where a ⏸️
cell and the rollup disagree. Since 2.33.0 (issue #380) a ⏸️ item resumes by
`set NNN resumed --reason …` alone, back to 📋 where `claim` offers it, and a
forward `set` over it is refused.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_defer", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


PROGRESS = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | Rules | G1 | ✅ |
| 2 | Reports | G2 | 🚧 |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 1 | ✅ |
| G2 Reports | Stage 2 | 🚧 |

## Stage 1 — Rules — ✅

**Deliverables.**
- ✅ Bounds. *(Item 027)*

**Acceptance.**
- [x] Rules fire.

## Stage 2 — Reports — 🚧

**Deliverables.**
- ✅ Summary. *(Item 030)*
- 🚧 Export, a deliverable long enough that its author
  wrapped it onto a second line. *(Item 031)*
- 📋 Charts. *(Item 032)*

**Acceptance.**
- [ ] Reports render.
"""

REASON = "owner deferred the reporting stage"


def _defer(text: str = PROGRESS, num: int = 31, reason: str = REASON,
           date: str = "2026-09-24") -> str:
    return aide.defer_item(text, num, reason, date)[0]


# --------------------------------------------------------------------------- #
# defer_item — the flip, the trail, the rollup
# --------------------------------------------------------------------------- #
def test_defer_flips_the_bullet_and_writes_the_reason_under_it():
    out = _defer().splitlines()
    i = out.index("- ⏸️ Export, a deliverable long enough that its author")
    assert out[i + 1] == "  wrapped it onto a second line. *(Item 031)*"
    assert out[i + 2] == f"  - **2026-09-24** → deferred: {REASON}"
    assert aide._parse_item_status(out)[2][31] == "deferred"


def test_defer_of_one_item_beside_open_work_rolls_the_stage_to_what_is_left():
    """🚧 031 deferred beside ✅ 030 and 📋 032: the stage is 🚧 still (a ✅
    bullet with 📋 work open), and nothing else in the file moves."""
    before = PROGRESS.splitlines()
    out = _defer().splitlines()
    assert [l for l in out if l not in before] == [
        "- ⏸️ Export, a deliverable long enough that its author",
        f"  - **2026-09-24** → deferred: {REASON}",
    ]


def test_deferring_every_open_item_moves_header_summary_and_objective_to_deferred():
    out = _defer(_defer(), 32)
    assert "## Stage 2 — Reports — ⏸️" in out
    assert "| 2 | Reports | G2 | ⏸️ |" in out
    # Every stage G2 names is ✅ or ⏸️, so the objective waits on deferred
    # work alone.
    assert "| G2 Reports | Stage 2 | ⏸️ |" in out
    # Stage 1 and its objective are untouched.
    assert "## Stage 1 — Rules — ✅" in out and "| G1 Rules | Stage 1 | ✅ |" in out


def test_a_stage_whose_last_open_item_merges_beside_a_deferred_one_reads_deferred():
    """✅ + ⏸️ is ⏸️, even though ⏸️ ranks below the 🚧 the stage held — the
    writer must follow it down, or `check` reports the drift."""
    text = _defer(PROGRESS.replace("- 📋 Charts. *(Item 032)*",
                                   "- 🚧 Charts. *(Item 032)*"))
    assert "## Stage 2 — Reports — 🚧" in text
    out = aide.set_item_status(text, 32, "complete")
    assert "## Stage 2 — Reports — ⏸️" in out
    assert "| 2 | Reports | G2 | ⏸️ |" in out
    # #173: never ✅ while a ⏸️ is held.
    assert "| 2 | Reports | G2 | ✅ |" not in out


def test_deferring_the_only_in_progress_item_rolls_the_stage_back_to_planned():
    only = PROGRESS.replace("- ✅ Summary. *(Item 030)*\n", "")
    out = _defer(only)
    assert "## Stage 2 — Reports — 📋" in out
    assert "| 2 | Reports | G2 | 📋 |" in out


def test_resuming_a_deferred_item_moves_the_stage_back_up():
    """Every open item deferred, the stage ⏸️; resuming one sends its bullet
    to 📋 under a `resumed:` line, and the stage, its row and its objective
    follow it down to 🚧 — ✅ 030 beside 📋 work."""
    deferred = _defer(_defer(), 32)
    out, message = aide.resume_item(deferred, 31, "owner wants it now",
                                    "2026-10-02")
    assert message == "item 031: resumed — owner wants it now"
    lines = out.splitlines()
    i = lines.index("- 📋 Export, a deliverable long enough that its author")
    # The trail stays: the deferral is history, and the resumption joins it.
    assert lines[i + 2:i + 4] == [
        f"  - **2026-09-24** → deferred: {REASON}",
        "  - **2026-10-02** → resumed: owner wants it now"]
    assert "## Stage 2 — Reports — 🚧" in out
    assert "| 2 | Reports | G2 | 🚧 |" in out
    assert "| G2 Reports | Stage 2 | 🚧 |" in out
    assert aide._parse_item_status(lines)[2][31] == "planned"
    assert aide.derived_cell_findings(lines) == ([], [], set())


def test_resuming_the_only_open_item_rolls_a_deferred_stage_back_to_planned():
    only = PROGRESS.replace("- ✅ Summary. *(Item 030)*\n", "").replace(
        "- 📋 Charts. *(Item 032)*\n", "")
    deferred = _defer(only)
    assert "## Stage 2 — Reports — ⏸️" in deferred
    out = aide.resume_item(deferred, 31, "now", "2026-10-02")[0]
    assert "## Stage 2 — Reports — 📋" in out
    assert "| 2 | Reports | G2 | 📋 |" in out
    assert aide.derived_cell_findings(out.splitlines()) == ([], [], set())


@pytest.mark.parametrize("icon,status", [
    ("🚧", "in-progress"), ("🔍", "in-review"), ("✅", "complete"),
    ("❌", "excluded")])
def test_resume_refuses_an_item_that_is_not_deferred_and_names_its_status(
        icon, status):
    text = PROGRESS.replace("- 📋 Charts. *(Item 032)*", f"- {icon} Charts. *(Item 032)*")
    with pytest.raises(ValueError, match=f"item 032 is {icon} {status}; only "
                                         f"a ⏸️ deferred item can be resumed"):
        aide.resume_item(text, 32, "x", "2026-10-02")


def test_resume_refuses_an_item_no_bullet_names():
    with pytest.raises(ValueError, match="nothing to resume"):
        aide.resume_item(PROGRESS, 99, "x", "2026-10-02")


def test_resuming_a_planned_item_is_no_change():
    out, message = aide.resume_item(PROGRESS, 32, "x", "2026-10-02")
    assert out == PROGRESS and "no change" in message


def test_resume_desugars_a_shared_marker_and_moves_only_the_named_item():
    shared = PROGRESS.replace("- 📋 Charts. *(Item 032)*",
                              "- ⏸️ Charts and tables. *(Items 032, 033)*")
    splits = []
    out, _ = aide.resume_item(shared, 33, "tables now", "2026-10-02", splits)
    lines = out.splitlines()
    assert "- ⏸️ Charts and tables. *(Item 032)*" in lines
    i = lines.index("- 📋 Charts and tables. *(Item 033)*")
    assert lines[i + 1] == "  - **2026-10-02** → resumed: tables now"
    assert len(splits) == 1


@pytest.mark.parametrize("status", ["in-review", "complete"])
def test_the_writer_still_moves_a_deferred_bullet_forward(status):
    """`set_item_status` itself still advances a ⏸️ bullet — it is `merge`'s
    tick too, and a merge records work that landed. The refusal of a forward
    status over a ⏸️ item is the `set` verb's (issue #380)."""
    out = aide.set_item_status(_defer(), 31, status)
    assert aide._parse_item_status(out.splitlines())[2][31] == status


def test_defer_desugars_a_shared_marker_and_moves_only_the_named_item():
    shared = PROGRESS.replace("- 📋 Charts. *(Item 032)*",
                              "- 📋 Charts and tables. *(Items 032, 033)*")
    splits = []
    out, _ = aide.defer_item(shared, 33, "tables later", "2026-09-24", splits)
    lines = out.splitlines()
    assert "- 📋 Charts and tables. *(Item 032)*" in lines
    i = lines.index("- ⏸️ Charts and tables. *(Item 033)*")
    assert lines[i + 1] == "  - **2026-09-24** → deferred: tables later"
    assert len(splits) == 1


@pytest.mark.parametrize("icon,status,hint", [
    ("✅", "complete", "reopen"), ("❌", "excluded", "")])
def test_defer_refuses_a_finished_item_and_names_its_status(icon, status, hint):
    text = PROGRESS.replace("- 📋 Charts. *(Item 032)*", f"- {icon} Charts. *(Item 032)*")
    with pytest.raises(ValueError, match=f"item 032 is {icon} {status}") as exc:
        aide.defer_item(text, 32, "x", "2026-09-24")
    assert hint in str(exc.value)


def test_defer_refuses_when_one_of_the_items_bullets_is_done():
    two = PROGRESS.replace("- 📋 Charts. *(Item 032)*",
                           "- 📋 Charts. *(Item 032)*\n- ✅ Axes. *(Item 031)*")
    with pytest.raises(ValueError, match="complete"):
        aide.defer_item(two, 31, "x", "2026-09-24")


def test_defer_refuses_an_item_no_bullet_names():
    with pytest.raises(ValueError, match="nothing to defer"):
        aide.defer_item(PROGRESS, 99, "x", "2026-09-24")


def test_deferring_a_deferred_item_again_is_no_change():
    once = _defer()
    again, message = aide.defer_item(once, 31, "again", "2026-09-30")
    assert again == once
    assert "no change" in message


@pytest.mark.parametrize("icon", ["📋", "🔍"])
def test_defer_takes_planned_and_in_review_items(icon):
    text = PROGRESS.replace("- 📋 Charts. *(Item 032)*", f"- {icon} Charts. *(Item 032)*")
    out = _defer(text, 32)
    assert "- ⏸️ Charts. *(Item 032)*" in out


def test_a_hand_set_deferred_stage_is_left_alone_by_a_set_elsewhere():
    """⏸️ set by hand over a stage whose bullets say 🚧 is the owner's intent
    until a verb moves that stage's bullets; `check` names the disagreement."""
    hand = PROGRESS.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — ⏸️")
    hand = hand.replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | ⏸️ |")
    hand = hand.replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | ⏸️ |")
    other = hand.replace("- ✅ Bounds. *(Item 027)*", "- 🚧 Bounds. *(Item 027)*")
    other = other.replace("## Stage 1 — Rules — ✅", "## Stage 1 — Rules — 🚧")
    other = other.replace("| 1 | Rules | G1 | ✅ |", "| 1 | Rules | G1 | 🚧 |")
    out = aide.set_item_status(other, 27, "complete")
    assert "## Stage 2 — Reports — ⏸️" in out
    assert "| 2 | Reports | G2 | ⏸️ |" in out
    assert "| G2 Reports | Stage 2 | ⏸️ |" in out
    # A set on the stage's own bullet is the owner's next decision about it.
    moved = aide.set_item_status(out, 32, "in-progress")
    assert "## Stage 2 — Reports — 🚧" in moved
    assert "| 2 | Reports | G2 | 🚧 |" in moved
    assert "| G2 Reports | Stage 2 | 🚧 |" in moved


PRE_25 = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 2 | Reports | G1 | 🚧 |
| 4 | Charts | G1 | 📋 |
| 5 | Other | G2 | 📋 |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Reports | Stage 2, Stage 4 | {g1} |
| G2 Other | Stage 5 | 📋 |

## Stage 2 — Reports — 🚧

**Deliverables.**
- ✅ Summary. *(Item 030)*
- ⏸️ Export. *(Item 031)*

## Stage 4 — Charts — 📋

**Deliverables.**
- 📋 Charts. *(Item 040)*

## Stage 5 — Other — 📋

**Deliverables.**
- 📋 Other. *(Item 050)*
"""


def test_an_objective_follows_a_stage_that_self_heals_to_deferred():
    """PR #284 review: a pre-2.5.0 file with a ✅+⏸️ stage still under 🚧. A
    `set` for an unrelated stage's item heals that stage to ⏸️; the Objective
    row over it and a 📋 stage must follow down to what the rollup of those
    two says — 📋 — rather than stay 🚧 over stages that no longer say so."""
    out = aide.set_item_status(PRE_25.format(g1="🚧"), 50, "in-progress")
    assert "## Stage 2 — Reports — ⏸️" in out
    assert "| 2 | Reports | G1 | ⏸️ |" in out
    assert "| G1 Reports | Stage 2, Stage 4 | 📋 |" in out
    assert "| G2 Other | Stage 5 | 🚧 |" in out


def test_the_self_heal_leaves_a_hand_set_deferred_objective_alone():
    """The promotion frees the downgrade, not the hand-held ⏸️: no verb moved
    a bullet of stage 2 or 4, so the owner's ⏸️ on G1 stands."""
    out = aide.set_item_status(PRE_25.format(g1="⏸️"), 50, "in-progress")
    assert "## Stage 2 — Reports — ⏸️" in out
    assert "| G1 Reports | Stage 2, Stage 4 | ⏸️ |" in out


# --------------------------------------------------------------------------- #
# check — the ⏸️ rule (ask 3)
# --------------------------------------------------------------------------- #
AIDE_TOML = '[project]\nname = "Demo"\ndocs_dir = "docs/aide"\n'


def _repo(tmp_path: Path, progress: str = PROGRESS, name: str = "repo") -> Path:
    repo = tmp_path / name
    ddir = repo / "docs" / "aide"
    ddir.mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (ddir / "progress.md").write_text(progress, encoding="utf-8")
    (ddir / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    return repo


def _checks(repo: Path):
    return aide.run_checks(repo, aide.load_config(repo), branches=[])


def test_a_hand_set_deferred_summary_over_open_bullets_is_a_warning(tmp_path: Path):
    """The issue's own file: a stage deferred by hand, its bullets still 📋 /
    🚧 — silently accepted until 2.5.0."""
    hand = PROGRESS.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — ⏸️")
    hand = hand.replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | ⏸️ |")
    errors, warnings = _checks(_repo(tmp_path, hand))
    assert errors == []
    hits = [w for w in warnings if w.startswith("stage 2:")]
    assert len(hits) == 1, warnings
    assert "summary ⏸️ deferred and header ⏸️ deferred" in hits[0]
    assert "roll up to 🚧 in-progress" in hits[0]
    assert "aide progress set NNN deferred --reason" in hits[0]


def test_a_stage_rolling_up_to_deferred_under_a_lesser_summary_is_a_warning(
        tmp_path: Path):
    """The reverse: bullets hand-edited to ⏸️, cells left 🚧."""
    hand = PROGRESS.replace("- 🚧 Export, a", "- ⏸️ Export, a")
    hand = hand.replace("- 📋 Charts.", "- ⏸️ Charts.")
    _, warnings = _checks(_repo(tmp_path, hand))
    hits = [w for w in warnings if w.startswith("stage 2:")]
    assert len(hits) == 1, warnings
    assert "summary 🚧 in-progress and header 🚧 in-progress" in hits[0]
    assert "roll up to ⏸️ deferred" in hits[0]


def test_an_excluded_summary_row_is_still_left_out(tmp_path: Path):
    hand = PROGRESS.replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | ❌ |")
    _, warnings = _checks(_repo(tmp_path, hand))
    assert not [w for w in warnings if w.startswith("stage 2:")], warnings


def test_a_file_the_verbs_wrote_raises_no_warning(tmp_path: Path, capsys):
    """Defer, merge the last open item beside it, resume: `check` says nothing
    about the stage at any step."""
    repo = _repo(tmp_path)
    path = repo / "docs" / "aide" / "progress.md"

    def stage_warnings():
        errors, warnings = _checks(repo)
        assert errors == []
        return [w for w in warnings if w.startswith("stage ")]

    base = ["--repo", str(repo), "progress", "set"]
    assert aide.main([*base, "31", "deferred", "--reason", REASON, "--no-commit"]) == 0
    assert stage_warnings() == []
    assert aide.main([*base, "32", "done", "--no-commit"]) == 0
    assert "## Stage 2 — Reports — ⏸️" in path.read_text(encoding="utf-8")
    assert stage_warnings() == []
    assert aide.main([*base, "31", "resumed", "--reason", "now",
                      "--no-commit"]) == 0
    # ✅ 030 and 032 beside a 📋 bullet: started work, so 🚧.
    assert "## Stage 2 — Reports — 🚧" in path.read_text(encoding="utf-8")
    assert stage_warnings() == []
    assert aide.main([*base, "31", "in-progress", "--no-commit"]) == 0
    assert "## Stage 2 — Reports — 🚧" in path.read_text(encoding="utf-8")
    assert stage_warnings() == []


# --------------------------------------------------------------------------- #
# check — every derived cell against the rollup (issue #285)
# --------------------------------------------------------------------------- #
def _stage2(text: str, icon: str) -> str:
    """Stage 2's header and summary row both typed *icon*."""
    text = text.replace("## Stage 2 — Reports — 🚧", f"## Stage 2 — Reports — {icon}")
    return text.replace("| 2 | Reports | G2 | 🚧 |", f"| 2 | Reports | G2 | {icon} |")


def _about(findings, prefix):
    return [f for f in findings if f.startswith(prefix)]


ALL_PLANNED = (PROGRESS.replace("- ✅ Summary. *(Item 030)*", "- 📋 Summary. *(Item 030)*")
               .replace("- 🚧 Export, a", "- 📋 Export, a")
               .replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | 📋 |"))


@pytest.mark.parametrize("text, cells, derived", [
    # 1: 🚧 cells over bullets that are all 📋.
    (ALL_PLANNED, "summary 🚧 in-progress and header 🚧 in-progress", "📋 planned"),
    # 2: 📋 cells over bullets rolling up to 🚧.
    (_stage2(PROGRESS, "📋"), "summary 📋 planned and header 📋 planned", "🚧 in-progress"),
    # 3: 🔍 cells — the rollup never yields 🔍; a 🔍 item holds its stage at 🚧.
    (_stage2(PROGRESS, "🔍"), "summary 🔍 in-review and header 🔍 in-review", "🚧 in-progress"),
], ids=["cells-over-planned", "planned-over-started", "in-review"])
def test_a_stage_cell_the_rollup_does_not_derive_is_one_warning(
        tmp_path: Path, text, cells, derived):
    errors, warnings = _checks(_repo(tmp_path, text))
    assert errors == []
    hits = _about(warnings, "stage 2:")
    assert len(hits) == 1, warnings
    assert hits[0].startswith(f"stage 2: {cells} but its deliverables roll up to {derived}")
    assert not _about(warnings, "objective "), warnings


def test_a_header_marked_done_with_no_summary_row_is_an_error(tmp_path: Path):
    """Case 4: the ✅ error and the header comparison both used to need a
    summary row to compare against."""
    text = PROGRESS.replace("| 2 | Reports | G2 | 🚧 |\n", "")
    text = text.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — ✅")
    errors, warnings = _checks(_repo(tmp_path, text))
    assert errors == ["stage 2: header marked ✅ but has non-complete deliverables "
                      "— they roll up to 🚧 in-progress"], errors
    assert not _about(warnings, "stage 2:"), warnings


def test_an_objective_marked_done_over_an_open_stage_is_an_error(tmp_path: Path):
    """Case 5: the ✅-summary over-claim, one table over."""
    text = PROGRESS.replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | ✅ |")
    errors, warnings = _checks(_repo(tmp_path, text))
    assert len(errors) == 1 and errors[0].startswith(
        "objective G2 marked ✅ but the stages it names (stage 2 🚧) roll up "
        "to 🚧 in-progress"), errors
    assert not _about(warnings, "objective "), warnings


@pytest.mark.parametrize("icon, name, fix", [
    ("📋", "planned", "set it to ✅"),
    ("⏸️", "deferred", "restore ✅"),
])
def test_an_objective_row_below_its_done_stage_is_a_warning(
        tmp_path: Path, icon, name, fix):
    """Case 6, and the hand-set ⏸️ Objective row: the writer leaves it
    standing (`_held_by_hand`), and check names it while it disagrees."""
    text = PROGRESS.replace("| G1 Rules | Stage 1 | ✅ |", f"| G1 Rules | Stage 1 | {icon} |")
    errors, warnings = _checks(_repo(tmp_path, text))
    assert errors == []
    hits = _about(warnings, "objective G1")
    assert len(hits) == 1, warnings
    assert hits[0].startswith(f"objective G1: {icon} {name} but the stages it "
                              f"names (stage 1 ✅) roll up to ✅ complete")
    assert hits[0].endswith(fix), hits[0]


def test_a_hand_set_deferred_objective_over_open_stages_is_a_warning(tmp_path: Path):
    text = PROGRESS.replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | ⏸️ |")
    assert aide.set_item_status(text, 27, "complete") == text  # left standing
    _, warnings = _checks(_repo(tmp_path, text))
    hits = _about(warnings, "objective G2")
    assert len(hits) == 1 and "roll up to 🚧 in-progress" in hits[0], warnings
    assert "aide progress set NNN deferred --reason" in hits[0]


def test_an_objective_naming_no_stage_section_is_a_warning(tmp_path: Path):
    """Case 7: `Stage 9` has no section, so nothing derives the row's ✅."""
    text = PROGRESS.replace("| G1 Rules | Stage 1 | ✅ |", "| G1 Rules | Stage 9 | ✅ |")
    errors, warnings = _checks(_repo(tmp_path, text))
    assert errors == []
    hits = _about(warnings, "objective G1")
    assert hits == ["objective G1: Delivered by 'Stage 9' names no stage with a "
                    "'## Stage N' section, so nothing derives its ✅ — name the "
                    "stage that delivers it"], warnings


TARGET_G1 = ("\n## Outcome targets\n\n"
             "| Target | Objective | Attempted by | Status | Evidence / follow-up |\n"
             "|--------|-----------|--------------|--------|----------------------|\n"
             "| Rules hold | G1 | Stage 1 | ❓ Unverified | — |\n")


def test_an_objective_held_by_its_target_is_compared_with_in_progress(tmp_path: Path):
    """The writer holds a ✅ derivation at 🚧 under a target not ✅ Met, so
    🚧 is what the row is compared with: 🚧 passes, 📋 is a warning, and a
    ✅ row is the target comparisons' alone (their warning, not ours)."""
    base = PROGRESS + TARGET_G1
    for icon, expect in (("🚧", None), ("📋", "roll up to 🚧 in-progress (held "
                                            "below ✅ by an Outcome target not ✅ Met)")):
        text = base.replace("| G1 Rules | Stage 1 | ✅ |", f"| G1 Rules | Stage 1 | {icon} |")
        errors, warnings = _checks(_repo(tmp_path, text, name=f"g1-{icon}"))
        hits = _about(warnings, "objective G1")
        assert errors == []
        if expect is None:
            assert hits == [], warnings
        else:
            assert len(hits) == 1 and expect in hits[0], warnings
    errors, warnings = _checks(_repo(tmp_path, base, name="g1-done"))
    assert errors == []
    g1 = [w for w in warnings if "G1" in w]
    assert len(g1) == 1 and "outcome target 'Rules hold' is not ✅ Met" in g1[0], g1


def test_an_excluded_header_or_objective_is_not_compared(tmp_path: Path):
    """❌ is a scope decision the bullets do not speak for: a ❌ Objective
    row over a ✅ stage is silent, and a ❌ header over 🚧 bullets meets only
    the header-against-summary comparison, never the rollup."""
    text = PROGRESS.replace("| G1 Rules | Stage 1 | ✅ |", "| G1 Rules | Stage 1 | ❌ |")
    text = text.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — ❌")
    errors, warnings = _checks(_repo(tmp_path, text))
    assert errors == []
    assert not _about(warnings, "objective "), warnings
    assert _about(warnings, "stage 2:") == [
        "stage 2: header excluded disagrees with summary in-progress"], warnings


def test_each_cell_gets_one_message(tmp_path: Path):
    """A ✅ summary row over bullets that roll up to ⏸️ is the error alone —
    until 2.6.0 it was the error and the ⏸️ warning. A ⏸️ header beside it is
    the header's own warning, and no header-against-summary warning joins
    them. A ✅ Objective row over an open stage and a ❌ Not met target is
    the derived-cell error alone, not the target's too."""
    text = PROGRESS.replace("- 🚧 Export, a", "- ⏸️ Export, a")
    text = text.replace("- 📋 Charts.", "- ⏸️ Charts.")
    text = text.replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | ✅ |")
    text = text.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — 🔍")
    text = text.replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | ✅ |")
    text += ("\n## Outcome targets\n\n"
             "| Target | Objective | Attempted by | Status | Evidence / follow-up |\n"
             "|--------|-----------|--------------|--------|----------------------|\n"
             "| Reports read | G2 | Stage 2 | ❌ Not met | — |\n")
    errors, warnings = _checks(_repo(tmp_path, text))
    assert _about(errors, "stage 2:") == [
        "stage 2: summary marked ✅ but has non-complete deliverables — they "
        "roll up to ⏸️ deferred"], errors
    assert len(_about(warnings, "stage 2:")) == 1, warnings
    assert _about(warnings, "stage 2:")[0].startswith(
        "stage 2: header 🔍 in-review but its deliverables roll up to ⏸️ deferred")
    g2 = [f for f in errors + warnings if "G2" in f]
    assert len(g2) == 1 and g2[0].startswith("objective G2 marked ✅ but the stages"), g2


MULTI = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | Rules | G1 | 📋 |
| 2 | Reports | G1, G2 | 📋 |
| 3 | Charts | G2 | 📋 |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules and reports | Stage 1, Stage 2 | 📋 |
| G2 Everything shown | Stages 2, 3 | 📋 |

## Stage 1 — Rules — 📋

**Deliverables.**
- 📋 Bounds. *(Item 010)*
- 📋 Limits. *(Item 011)*

## Stage 2 — Reports — 📋

**Deliverables.**
- 📋 Summary. *(Item 020)*

## Stage 3 — Charts — 📋

**Deliverables.**
- 📋 Charts. *(Item 030)*
"""


def test_a_multi_stage_file_the_verbs_wrote_trips_no_derived_cell(tmp_path: Path):
    """Objective rows over two stages each, driven by every verb that moves a
    bullet — forward, deferred, resumed, reopened — with the file checked
    after each step. The comparison is the writer's derivation, so a verb
    can never write what `check` then reports."""
    date = "2026-09-25"
    steps = [
        lambda t: aide.set_item_status(t, 10, "in-progress"),
        lambda t: aide.set_item_status(t, 20, "in-review"),
        lambda t: aide.defer_item(t, 11, "later", date)[0],
        lambda t: aide.set_item_status(t, 10, "complete"),
        lambda t: aide.set_item_status(t, 20, "complete"),
        lambda t: aide.defer_item(t, 30, "later", date)[0],
        lambda t: aide.reopen_item(t, 20, "regressed", date)[0],
        lambda t: aide.resume_item(t, 30, "wanted now", date)[0],
        lambda t: aide.set_item_status(t, 30, "in-progress"),
        lambda t: aide.set_item_status(t, 11, "complete"),
        lambda t: aide.set_item_status(t, 20, "complete"),
        lambda t: aide.set_item_status(t, 30, "complete"),
    ]
    text = MULTI
    assert aide.derived_cell_findings(text.splitlines()) == ([], [], set())
    for n, step in enumerate(steps):
        text = step(text)
        assert aide.derived_cell_findings(text.splitlines()) == ([], [], set()), (n, text)
    assert "| G1 Rules and reports | Stage 1, Stage 2 | ✅ |" in text
    assert "| G2 Everything shown | Stages 2, 3 | ✅ |" in text
    errors, warnings = _checks(_repo(tmp_path, text))
    assert errors == []
    assert not [w for w in warnings if w.startswith(("stage ", "objective "))], warnings


# --------------------------------------------------------------------------- #
# the CLI — refusals
# --------------------------------------------------------------------------- #
def test_set_deferred_refuses_without_a_stated_reason_and_writes_nothing(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    for extra in ([], ["--reason", "   "], ["--reason", "two\nlines"]):
        assert aide.main(["--repo", str(repo), "progress", "set", "31",
                          "deferred", *extra, "--no-commit"]) == 2, extra
    assert "--reason is required" in capsys.readouterr().err
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


def test_set_deferred_refuses_a_criterion_or_all_and_writes_nothing(
        tmp_path: Path):
    """An item is deferred whole, as it is reopened whole."""
    repo = _repo(tmp_path)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", "31", "deferred",
                      "--criterion", "1", "--reason", "x", "--no-commit"]) == 2
    assert aide.main(["--repo", str(repo), "progress", "set", "31", "deferred",
                      "--all", "--reason", "x", "--no-commit"]) == 2
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


def test_set_deferred_on_a_done_item_exits_one_and_writes_nothing(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", "30", "deferred",
                      "--reason", "x", "--no-commit"]) == 1
    err = capsys.readouterr().err
    assert "item 030 is ✅ complete" in err and "reopen" in err
    assert "NOT changed" in err
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before
    # No insight is captured by a deferral, refused or not.
    assert (repo / "docs" / "aide" / "insights.md").read_text(
        encoding="utf-8") == "# Insight Inbox\n"


def test_set_deferred_writes_no_insight(tmp_path: Path):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "progress", "set", "31", "deferred",
                      "--reason", REASON, "--date", "2026-09-24",
                      "--no-commit"]) == 0
    text = (repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")
    assert f"  - **2026-09-24** → deferred: {REASON}" in text
    assert (repo / "docs" / "aide" / "insights.md").read_text(
        encoding="utf-8") == "# Insight Inbox\n"


def test_set_rejects_an_unknown_status_naming_deferred(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "progress", "set", "31", "paused",
                      "--no-commit"]) == 2
    assert "'deferred'" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# set --stage N --deliverable K deferred — a bullet no marker names (#336)
# --------------------------------------------------------------------------- #
#: The issue's file: stage 3 deferred by hand before 2.5.0, header, summary
#: and objective ⏸️, its bullets never itemised and still 📋.
UNMARKED = PROGRESS.replace("| 2 | Reports | G2 | 🚧 |\n",
                            "| 2 | Reports | G2 | 🚧 |\n| 3 | Plugins | G3 | ⏸️ |\n"
                            ).replace(
    "| G2 Reports | Stage 2 | 🚧 |\n",
    "| G2 Reports | Stage 2 | 🚧 |\n| G3 Plugins | Stage 3 | ⏸️ |\n") + """
## Stage 3 — Plugins — Deferred — ⏸️

**Deliverables.**
- 📋 Plugin/registration API for new heuristics.
- 📋 Ingestion of human abnormality labels; a classification arm
  that informs the heuristics.

**Acceptance.**
- [ ] Plugins load.
"""


def _defer_at(text: str, stage: int, k: int, reason: str = "v2",
              date: str = "2026-09-29") -> str:
    return aide.defer_deliverable(text, stage, k, reason, date)[0]


def test_the_hand_deferred_stage_over_unmarked_bullets_names_the_positional_form(
        tmp_path: Path):
    _, warnings = _checks(_repo(tmp_path, UNMARKED))
    hits = _about(warnings, "stage 3:")
    assert len(hits) == 1, warnings
    assert "roll up to 📋 planned" in hits[0]
    assert ("its open deliverables carry no item marker, so defer them with "
            "'aide progress set --stage 3 --deliverable K deferred --reason …' "
            "(K = 1, 2) — or `dropped` in place of `deferred` for one the stage does not need, or restore 📋") in hits[0]
    assert "set NNN" not in hits[0]


def test_the_remedy_names_the_drop_only_where_the_drop_would_be_taken(
        tmp_path: Path):
    """A stage whose one bullet not ❌ is the open one: dropping it would leave
    the stage all ❌, which `drop_deliverable` refuses (issue #362), so the
    remedy names the deferral alone — for the stage and its Objective row."""
    last_open = UNMARKED.replace(
        "- 📋 Plugin/registration API for new heuristics.",
        "- ❌ Plugin/registration API for new heuristics.")
    _, warnings = _checks(_repo(tmp_path, last_open))
    for about in ("stage 3:", "objective G3"):
        hits = _about(warnings, about)
        assert len(hits) == 1, warnings
        assert "--stage 3 --deliverable K deferred --reason …' (K = 2)" in hits[0]
        assert "dropped" not in hits[0], hits[0]
    with pytest.raises(ValueError, match="last deliverable"):
        aide.drop_deliverable(last_open, 3, 2, "not needed", "2026-10-02")


def test_a_stage_with_marked_and_unmarked_open_bullets_names_both_forms(
        tmp_path: Path):
    mixed = UNMARKED.replace("- 📋 Plugin/registration API for new heuristics.",
                             "- 📋 Plugin/registration API for new heuristics. "
                             "*(Item 040)*")
    _, warnings = _checks(_repo(tmp_path, mixed))
    hits = _about(warnings, "stage 3:")
    assert len(hits) == 1, warnings
    assert "'aide progress set NNN deferred --reason …'" in hits[0]
    assert ("'aide progress set --stage 3 --deliverable K deferred --reason …' "
            "(K = 2) — or `dropped` in place of `deferred` for one the stage does not need") in hits[0]


def test_defer_deliverable_flips_the_bullet_and_writes_the_trail_under_its_last_line():
    out = _defer_at(UNMARKED, 3, 2).splitlines()
    i = out.index("- ⏸️ Ingestion of human abnormality labels; a classification arm")
    assert out[i + 1] == "  that informs the heuristics."
    assert out[i + 2] == "  - **2026-09-29** → deferred: v2"
    assert "- 📋 Plugin/registration API for new heuristics." in out


def test_deferring_every_unmarked_bullet_ends_the_drift_warning(tmp_path: Path):
    out = _defer_at(_defer_at(UNMARKED, 3, 1), 3, 2)
    assert "## Stage 3 — Plugins — Deferred — ⏸️" in out
    assert "| 3 | Plugins | G3 | ⏸️ |" in out
    assert "| G3 Plugins | Stage 3 | ⏸️ |" in out
    assert out.count("  - **2026-09-29** → deferred: v2") == 2
    assert aide.derived_cell_findings(out.splitlines()) == ([], [], set())
    errors, warnings = _checks(_repo(tmp_path, out))
    assert errors == []
    assert not _about(warnings, "stage 3:") and not _about(warnings, "objective G3"), warnings


def test_deferring_one_of_two_open_bullets_rolls_the_stage_to_what_is_left():
    """As `set NNN deferred` does: a ⏸️ beside a 📋 is 📋, and the verb moved a
    bullet of the stage, so the hand-set ⏸️ follows it down."""
    out = _defer_at(UNMARKED, 3, 1)
    assert "## Stage 3 — Plugins — Deferred — 📋" in out
    assert "| 3 | Plugins | G3 | 📋 |" in out
    assert aide.derived_cell_findings(out.splitlines()) == ([], [], set())


def test_defer_deliverable_again_is_no_change():
    once = _defer_at(UNMARKED, 3, 1)
    again, message = aide.defer_deliverable(once, 3, 1, "again", "2026-09-30")
    assert again == once
    assert message == "stage 3 deliverable 1: no change (already deferred)"


@pytest.mark.parametrize("stage, k, match", [
    (9, 1, r"no '## Stage 9' section"),
    (3, 3, "stage 3 has 2 deliverable bullets, numbered from 1"),
    (3, 0, "stage 3 has 2 deliverable bullets, numbered from 1"),
    (2, 2, r"itemised — its trailing marker names item 031, so defer it by "
           r"item with `aide progress set 031 deferred --reason …`"),
], ids=["unknown-stage", "past-the-end", "zero", "itemised"])
def test_defer_deliverable_refuses(stage, k, match):
    with pytest.raises(ValueError, match=match):
        aide.defer_deliverable(UNMARKED, stage, k, "x", "2026-09-29")


@pytest.mark.parametrize("icon, status", [("✅", "complete"), ("❌", "excluded")])
def test_defer_deliverable_refuses_a_finished_bullet(icon, status):
    text = UNMARKED.replace("- 📋 Plugin/registration", f"- {icon} Plugin/registration")
    with pytest.raises(ValueError, match=f"stage 3 deliverable 1 is {icon} {status}; "
                                         f"only a 📋, 🚧 or 🔍 deliverable can be deferred"):
        aide.defer_deliverable(text, 3, 1, "x", "2026-09-29")


def test_an_unmarked_deferred_bullet_resumes_by_place_then_is_itemised():
    """Issue #380: an item born on a ⏸️ bullet is ⏸️ from the start, so its
    queue reads done as soon as it is written. The bullet is resumed by its
    place first — 📋 under a `resumed:` line, its stage rolled back down —
    and the item wired onto it then moves forward under `set NNN`."""
    out = _defer_at(_defer_at(UNMARKED, 3, 1), 3, 2)
    resumed, message = aide.resume_deliverable(out, 3, 1, "owner queues it",
                                               "2026-10-02")
    assert message == "stage 3 deliverable 1: resumed — owner queues it"
    lines = resumed.splitlines()
    i = lines.index("- 📋 Plugin/registration API for new heuristics.")
    assert lines[i + 1:i + 3] == ["  - **2026-09-29** → deferred: v2",
                                  "  - **2026-10-02** → resumed: owner queues it"]
    # ⏸️ beside 📋 reads 📋: the stage is open work again.
    assert "## Stage 3 — Plugins — Deferred — 📋" in resumed
    assert "| 3 | Plugins | G3 | 📋 |" in resumed
    assert aide.derived_cell_findings(lines) == ([], [], set())
    itemised = resumed.replace("- 📋 Plugin/registration API for new heuristics.",
                               "- 📋 Plugin/registration API for new heuristics. "
                               "*(Item 040)*")
    assert aide._parse_item_status(itemised.splitlines())[2][40] == "planned"
    moved = aide.set_item_status(itemised, 40, "in-progress")
    assert "- 🚧 Plugin/registration API for new heuristics. *(Item 040)*" in moved
    assert "## Stage 3 — Plugins — Deferred — 🚧" in moved
    assert "| 3 | Plugins | G3 | 🚧 |" in moved
    assert aide.derived_cell_findings(moved.splitlines()) == ([], [], set())


def test_an_itemised_deferred_bullet_resumes_by_its_item():
    """The other order: a marker wired onto a ⏸️ bullet leaves a ⏸️ item,
    which `set NNN resumed` takes back to 📋."""
    out = _defer_at(_defer_at(UNMARKED, 3, 1), 3, 2)
    itemised = out.replace("- ⏸️ Plugin/registration API for new heuristics.",
                           "- ⏸️ Plugin/registration API for new heuristics. "
                           "*(Item 040)*")
    moved = aide.resume_item(itemised, 40, "queued", "2026-10-02")[0]
    assert "- 📋 Plugin/registration API for new heuristics. *(Item 040)*" in moved
    assert aide.derived_cell_findings(moved.splitlines()) == ([], [], set())


def test_resume_deliverable_again_is_no_change():
    once = aide.resume_deliverable(_defer_at(UNMARKED, 3, 1), 3, 1, "x",
                                   "2026-10-02")[0]
    again, message = aide.resume_deliverable(once, 3, 1, "y", "2026-10-03")
    assert again == once and "no change" in message


@pytest.mark.parametrize("icon,status", [
    ("🚧", "in-progress"), ("🔍", "in-review"), ("✅", "complete"),
    ("❌", "excluded")])
def test_resume_deliverable_refuses_a_bullet_that_is_not_deferred(icon, status):
    text = UNMARKED.replace("- 📋 Plugin/registration API",
                            f"- {icon} Plugin/registration API")
    with pytest.raises(ValueError, match=f"stage 3 deliverable 1 is {icon} "
                                         f"{status}; only a ⏸️ deferred "
                                         f"deliverable can be resumed"):
        aide.resume_deliverable(text, 3, 1, "x", "2026-10-02")


def test_resume_deliverable_refuses_an_itemised_bullet_naming_the_item_form():
    with pytest.raises(ValueError, match=r"resume it by item with `aide "
                                         r"progress set 031 resumed --reason …`"):
        aide.resume_deliverable(_defer(UNMARKED), 2, 2, "x", "2026-10-02")


def test_set_by_position_writes_through_the_cli_and_no_insight(tmp_path: Path, capsys):
    repo = _repo(tmp_path, UNMARKED)
    path = repo / "docs" / "aide" / "progress.md"
    for k in ("2", "1"):
        assert aide.main(["--repo", str(repo), "progress", "set", "--stage", "3",
                          "--deliverable", k, "deferred", "--reason", "v2",
                          "--date", "2026-09-29", "--no-commit"]) == 0
    assert path.read_text(encoding="utf-8") == _defer_at(_defer_at(UNMARKED, 3, 2), 3, 1)
    # The status word may come first as well.
    assert aide.main(["--repo", str(repo), "progress", "set", "deferred",
                      "--stage", "3", "--deliverable", "1", "--reason", "v2",
                      "--no-commit"]) == 0
    assert "no change" in capsys.readouterr().out
    assert (repo / "docs" / "aide" / "insights.md").read_text(
        encoding="utf-8") == "# Insight Inbox\n"


@pytest.mark.parametrize("argv, message", [
    (["--stage", "3", "--deliverable", "1", "deferred", "--reason", "  "],
     "--reason is required"),
    (["--stage", "3", "--deliverable", "1", "deferred"], "--reason is required"),
    (["--stage", "3", "--deliverable", "1", "deferred", "--reason", "a\nb"],
     "line break"),
    (["--stage", "3", "--deliverable", "1", "done"],
     "only `deferred`, `dropped`, `resumed` or `restored` is set by position"),
    (["--stage", "3", "--deliverable", "1"],
     "only `deferred`, `dropped`, `resumed` or `restored` is set by position"),
    (["--stage", "3", "deferred", "--reason", "x"], "go together"),
    (["--deliverable", "1", "deferred", "--reason", "x"], "go together"),
    (["31", "deferred", "--stage", "3", "--deliverable", "1", "--reason", "x"],
     "takes no item number"),
    (["--stage", "3", "--deliverable", "1", "deferred", "--criterion", "1",
      "--reason", "x"], "deferred whole"),
], ids=["blank-reason", "no-reason", "two-lines", "other-status", "no-status",
        "stage-alone", "deliverable-alone", "with-number", "with-criterion"])
def test_set_by_position_refuses_its_usage_errors_with_exit_2(
        tmp_path: Path, capsys, argv, message):
    repo = _repo(tmp_path, UNMARKED)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", *argv,
                      "--no-commit"]) == 2
    assert message in capsys.readouterr().err
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


@pytest.mark.parametrize("stage, k, message", [
    ("9", "1", "no '## Stage 9' section"),
    ("3", "5", "stage 3 has 2 deliverable bullets"),
    ("2", "2", "`aide progress set 031 deferred --reason …`"),
])
def test_set_by_position_refuses_what_it_cannot_defer_with_exit_1(
        tmp_path: Path, capsys, stage, k, message):
    repo = _repo(tmp_path, UNMARKED)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", "--stage", stage,
                      "--deliverable", k, "deferred", "--reason", "x",
                      "--no-commit"]) == 1
    err = capsys.readouterr().err
    assert message in err and "NOT changed" in err
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


def test_stage_and_deliverable_belong_to_set_alone(tmp_path: Path, capsys):
    repo = _repo(tmp_path, UNMARKED)
    assert aide.main(["--repo", str(repo), "progress", "accept", "3",
                      "--stage", "3", "--deliverable", "1", "--no-commit"]) == 2
    assert ("belong to `set … deferred`, `set … dropped`, `set … resumed` "
            "and `set … restored` alone" in capsys.readouterr().err)


def _progress_parser():
    """The `aide progress` subparser, as `build_parser` hands it to the verb."""
    return aide.build_parser().parse_args(["progress", "set", "1"]).progress_parser


def test_a_word_for_the_number_is_still_refused_without_the_positional_form(
        tmp_path: Path, capsys):
    """Byte for byte what `type=int` printed: the subparser's usage, then
    `aide progress: error: …`, exit 2."""
    repo = _repo(tmp_path, UNMARKED)
    with pytest.raises(SystemExit) as exc:
        aide.main(["--repo", str(repo), "progress", "set", "paused",
                   "--no-commit"])
    assert exc.value.code == 2
    assert capsys.readouterr().err == (
        _progress_parser().format_usage()
        + "aide progress: error: argument number: invalid int value: 'paused'\n")
    with pytest.raises(SystemExit) as exc:
        aide.main(["--repo", str(repo), "progress", "set", "31", "done",
                   "extra", "--no-commit"])
    assert exc.value.code == 2
    assert "unrecognized arguments: extra" in capsys.readouterr().err


def test_the_objective_warning_over_unmarked_bullets_names_the_positional_form(
        tmp_path: Path):
    _, warnings = _checks(_repo(tmp_path, UNMARKED))
    hits = _about(warnings, "objective G3")
    assert len(hits) == 1, warnings
    assert hits[0].endswith(
        "its open deliverables carry no item marker, so defer them with "
        "'aide progress set --stage 3 --deliverable K deferred --reason …' "
        "(K = 1, 2) — or `dropped` in place of `deferred` for one the stage does not need, or restore 📋"), hits[0]
    mixed = UNMARKED.replace("- 📋 Plugin/registration API for new heuristics.",
                             "- 📋 Plugin/registration API for new heuristics. "
                             "*(Item 040)*")
    _, warnings = _checks(_repo(tmp_path, mixed, name="mixed"))
    hits = _about(warnings, "objective G3")
    assert len(hits) == 1, warnings
    assert hits[0].endswith(
        "defer the open items with 'aide progress set NNN deferred --reason …' "
        "and the deliverables with no item marker with 'aide progress set "
        "--stage 3 --deliverable K deferred --reason …' (K = 2) — or `dropped` in place of `deferred` for one the stage does not need, "
        "or restore 📋")


def test_the_objective_warning_over_two_stages_names_each_stages_positions():
    two = UNMARKED.replace("| G3 Plugins | Stage 3 | ⏸️ |",
                           "| G3 Plugins | Stages 3, 4 | ⏸️ |") + """
## Stage 4 — Loaders — 📋

**Deliverables.**
- ✅ Loader. *(Item 050)*
- 📋 Loader cache.
"""
    two = two.replace("| 3 | Plugins | G3 | ⏸️ |",
                      "| 3 | Plugins | G3 | ⏸️ |\n| 4 | Loaders | G3 | 🚧 |"
                      ).replace("## Stage 4 — Loaders — 📋", "## Stage 4 — Loaders — 🚧")
    _, warnings, _ = aide.derived_cell_findings(two.splitlines())
    hits = _about(warnings, "objective G3")
    assert len(hits) == 1, warnings
    assert ("'aide progress set --stage N --deliverable K deferred --reason …' "
            "(stage 3: K = 1, 2; stage 4: K = 2) — or `dropped` in place of `deferred` for one the stage does not need") in hits[0], hits[0]


NESTED = PROGRESS.replace(
    "- 📋 Charts. *(Item 032)*",
    "- 📋 Charts. *(Item 032)*\n  - 📋 Axis labels, a nested deliverable.\n"
    "  - 📋 Legends. *(Item 033)*")


@pytest.mark.parametrize("defer", [
    lambda t: aide.defer_deliverable(t, 2, 4, "later", "2026-09-29")[0],
    lambda t: aide.defer_item(t, 33, "later", "2026-09-29")[0],
], ids=["by-position", "by-item"])
def test_a_trail_under_a_nested_bullet_is_indented_under_it(defer):
    out = defer(NESTED).splitlines()
    i = next(n for n, l in enumerate(out) if l.startswith("  - ⏸️ "))
    assert out[i + 1] == "    - **2026-09-29** → deferred: later"
    # A top-level bullet's trail is where it always was.
    top = aide.defer_item(NESTED, 32, "later", "2026-09-29")[0].splitlines()
    j = top.index("- ⏸️ Charts. *(Item 032)*")
    assert top[j + 1] == "  - **2026-09-29** → deferred: later"


def test_a_second_trail_line_follows_the_first_under_a_nested_bullet():
    once = aide.defer_item(NESTED, 33, "later", "2026-09-29")[0]
    back = aide.set_item_status(once, 33, "complete")
    again = aide.reopen_item(back, 33, "regressed", "2026-09-30")[0].splitlines()
    i = again.index("  - 📋 Legends. *(Item 033)*")
    assert again[i + 1:i + 3] == ["    - **2026-09-29** → deferred: later",
                                  "    - **2026-09-30** → reopened: regressed"]


# --------------------------------------------------------------------------- #
# set --stage N --deliverable K dropped — a bullet the stage does not need
# (issue #362)
# --------------------------------------------------------------------------- #
#: The issue's reproduction: a started stage whose two itemised bullets
#: shipped, every acceptance box ticked, and one optional bullet nobody
#: itemised still 📋.
ISSUE = PROGRESS.replace("| 2 | Reports | G2 | 🚧 |\n",
                         "| 2 | Reports | G2 | 🚧 |\n| 3 | Plugins | G3 | 🚧 |\n"
                         ).replace(
    "| G2 Reports | Stage 2 | 🚧 |\n",
    "| G2 Reports | Stage 2 | 🚧 |\n| G3 Plugins | Stage 3 | 🚧 |\n") + """
## Stage 3 — Plugins — 🚧

**Deliverables.**
- ✅ Plugin registry. *(Item 101)*
- ✅ Plugin loader. *(Item 102)*
- 📋 Optional plugin marketplace, a deliverable long enough that its
  author wrapped it.

**Acceptance.**
- [x] Plugins load.
"""

DROP_REASON = "the stage does not need a marketplace"


def _drop_at(text: str, stage: int = 3, k: int = 3, reason: str = DROP_REASON,
             date: str = "2026-10-02") -> str:
    return aide.drop_deliverable(text, stage, k, reason, date)[0]


def test_dropping_the_deferred_bullet_closes_the_issues_stage():
    """The issue: deferring bullet 3 holds the stage at ⏸️ for good (#173);
    dropping it lets the stage close ✅, header, summary and objective, with
    both decisions on the trail."""
    deferred = _defer_at(ISSUE, 3, 3, "later, maybe")
    assert "## Stage 3 — Plugins — ⏸️" in deferred
    assert "| 3 | Plugins | G3 | ⏸️ |" in deferred
    out = _drop_at(deferred)
    lines = out.splitlines()
    i = lines.index("- ❌ Optional plugin marketplace, a deliverable long enough that its")
    assert lines[i + 1] == "  author wrapped it."
    assert lines[i + 2:i + 4] == ["  - **2026-09-29** → deferred: later, maybe",
                                  f"  - **2026-10-02** → dropped: {DROP_REASON}"]
    assert "## Stage 3 — Plugins — ✅" in out
    assert "| 3 | Plugins | G3 | ✅ |" in out
    assert "| G3 Plugins | Stage 3 | ✅ |" in out
    # Boxes are attestations: the drop ticks or unticks nothing.
    assert "- [x] Plugins load." in out
    assert aide.derived_cell_findings(lines) == ([], [], set())


@pytest.mark.parametrize("icon", ["📋", "🚧", "🔍", "⏸️"])
def test_drop_deliverable_takes_every_open_bullet(icon):
    text = ISSUE.replace("- 📋 Optional plugin", f"- {icon} Optional plugin")
    out, message = aide.drop_deliverable(text, 3, 3, DROP_REASON, "2026-10-02")
    assert message == f"stage 3 deliverable 3: dropped — {DROP_REASON}"
    lines = out.splitlines()
    i = lines.index("- ❌ Optional plugin marketplace, a deliverable long enough that its")
    assert lines[i + 2] == f"  - **2026-10-02** → dropped: {DROP_REASON}"
    assert "## Stage 3 — Plugins — ✅" in out
    assert aide.derived_cell_findings(lines) == ([], [], set())


def test_dropping_the_only_in_progress_bullet_rolls_the_stage_back_down():
    """A drop moves the cells down where the bullets now say less, as a
    deferral does: 🚧 came from the dropped bullet alone."""
    text = UNMARKED.replace("- 📋 Plugin/registration", "- 🚧 Plugin/registration"
                            ).replace("## Stage 3 — Plugins — Deferred — ⏸️",
                                      "## Stage 3 — Plugins — 🚧"
                            ).replace("| 3 | Plugins | G3 | ⏸️ |",
                                      "| 3 | Plugins | G3 | 🚧 |"
                            ).replace("| G3 Plugins | Stage 3 | ⏸️ |",
                                      "| G3 Plugins | Stage 3 | 🚧 |")
    out = _drop_at(text, 3, 1)
    assert "- ❌ Plugin/registration API for new heuristics." in out
    assert "## Stage 3 — Plugins — 📋" in out
    assert "| 3 | Plugins | G3 | 📋 |" in out
    assert "| G3 Plugins | Stage 3 | 📋 |" in out
    assert aide.derived_cell_findings(out.splitlines()) == ([], [], set())


def test_a_drop_releases_a_header_held_at_deferred_by_hand():
    """A ⏸️ typed over the issue's stage stands under a `set` elsewhere, and
    follows the bullets once a verb moves one of its own."""
    hand = (ISSUE.replace("## Stage 3 — Plugins — 🚧", "## Stage 3 — Plugins — ⏸️")
            .replace("| 3 | Plugins | G3 | 🚧 |", "| 3 | Plugins | G3 | ⏸️ |")
            .replace("| G3 Plugins | Stage 3 | 🚧 |", "| G3 Plugins | Stage 3 | ⏸️ |"))
    elsewhere = aide.set_item_status(hand, 32, "complete")
    assert "## Stage 3 — Plugins — ⏸️" in elsewhere
    out = _drop_at(elsewhere)
    assert "## Stage 3 — Plugins — ✅" in out
    assert "| 3 | Plugins | G3 | ✅ |" in out
    assert "| G3 Plugins | Stage 3 | ✅ |" in out


def test_drop_deliverable_again_is_no_change():
    once = _drop_at(ISSUE)
    again, message = aide.drop_deliverable(once, 3, 3, "again", "2026-10-03")
    assert again == once
    assert message == "stage 3 deliverable 3: no change (already dropped)"


def test_drop_deliverable_refuses_a_shipped_bullet():
    text = ISSUE.replace("- 📋 Optional plugin", "- ✅ Optional plugin")
    with pytest.raises(ValueError, match="stage 3 deliverable 3 is ✅ complete; "
                                         "it shipped, so there is nothing to drop"):
        aide.drop_deliverable(text, 3, 3, "x", "2026-10-02")


@pytest.mark.parametrize("stage, k, match", [
    (9, 1, r"no '## Stage 9' section"),
    (3, 4, "stage 3 has 3 deliverable bullets, numbered from 1"),
    (3, 0, "stage 3 has 3 deliverable bullets, numbered from 1"),
    (3, 1, r"itemised — its trailing marker names item 101, so drop it by "
           r"item with `aide progress set 101 dropped --reason …`"),
], ids=["unknown-stage", "past-the-end", "zero", "itemised"])
def test_drop_deliverable_refuses(stage, k, match):
    with pytest.raises(ValueError, match=match):
        aide.drop_deliverable(ISSUE, stage, k, "x", "2026-10-02")


def test_drop_by_position_writes_through_the_cli_and_no_insight(
        tmp_path: Path, capsys):
    """The status word after the flags goes through `main`'s one-leftover-word
    route, as `deferred` does; it may come first as well."""
    repo = _repo(tmp_path, ISSUE)
    path = repo / "docs" / "aide" / "progress.md"
    assert aide.main(["--repo", str(repo), "progress", "set", "--stage", "3",
                      "--deliverable", "3", "dropped", "--reason", DROP_REASON,
                      "--date", "2026-10-02", "--no-commit"]) == 0
    assert path.read_text(encoding="utf-8") == _drop_at(ISSUE)
    assert ("stage 3 deliverable 3: dropped — "
            f"{DROP_REASON}") in capsys.readouterr().out
    assert aide.main(["--repo", str(repo), "progress", "set", "dropped",
                      "--stage", "3", "--deliverable", "3", "--reason", "x",
                      "--no-commit"]) == 0
    assert "no change (already dropped)" in capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == _drop_at(ISSUE)
    assert (repo / "docs" / "aide" / "insights.md").read_text(
        encoding="utf-8") == "# Insight Inbox\n"


@pytest.mark.parametrize("argv, message", [
    (["--stage", "3", "--deliverable", "3", "dropped"],
     "dropped: --reason is required"),
    (["--stage", "3", "--deliverable", "3", "dropped", "--reason", " "],
     "dropped: --reason is required"),
    (["--stage", "3", "--deliverable", "3", "dropped", "--reason", "a\nb"],
     "line break"),
    (["--stage", "3", "--deliverable", "3", "dropped", "--all",
      "--reason", "x"], "a deliverable is dropped whole"),
    (["--stage", "3", "dropped", "--reason", "x"], "go together"),
], ids=["no-reason", "blank-reason", "two-lines", "with-all", "stage-alone"])
def test_drop_by_position_refuses_its_usage_errors_with_exit_2(
        tmp_path: Path, capsys, argv, message):
    repo = _repo(tmp_path, ISSUE)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", *argv,
                      "--no-commit"]) == 2
    assert message in capsys.readouterr().err
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


@pytest.mark.parametrize("text, stage, k, message", [
    (ISSUE.replace("- 📋 Optional plugin", "- ✅ Optional plugin"), "3", "3",
     "nothing to drop"),
    (ISSUE, "3", "2", "item 102, so drop it by item with `aide progress set "
                      "102 dropped --reason …`"),
    (ISSUE, "3", "4", "stage 3 has 3 deliverable bullets"),
], ids=["shipped", "itemised", "no-kth-bullet"])
def test_drop_by_position_refuses_what_it_cannot_drop_with_exit_1(
        tmp_path: Path, capsys, text, stage, k, message):
    repo = _repo(tmp_path, text)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", "--stage", stage,
                      "--deliverable", k, "dropped", "--reason", "x",
                      "--no-commit"]) == 1
    err = capsys.readouterr().err
    assert message in err and "NOT changed" in err
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


def test_a_drop_that_would_leave_every_bullet_dropped_is_refused():
    """The review's case: a hand-⏸️ stage of two unmarked 📋 bullets, both
    dropped, would roll up 📋 under a stale "Deferred" header with nothing
    left to deliver. The second drop is refused, writing nothing; withdrawing
    a stage whole is its ❌ summary row's job."""
    once = _drop_at(UNMARKED, 3, 1)
    assert "- ❌ Plugin/registration API for new heuristics." in once
    with pytest.raises(ValueError, match=(
            "stage 3 deliverable 2 is the last deliverable of stage 3 not ❌.*"
            "marking its row in the Stage summary table ❌")):
        aide.drop_deliverable(once, 3, 2, "x", "2026-10-02")
    # A stage of one unmarked bullet: that bullet is the last as well.
    sole = UNMARKED.replace(
        "- 📋 Plugin/registration API for new heuristics.\n", "")
    with pytest.raises(ValueError, match="is the last deliverable of stage 3"):
        aide.drop_deliverable(sole, 3, 1, "x", "2026-10-02")


def test_one_shipped_bullet_beside_the_dropped_one_still_closes_the_stage():
    text = ISSUE.replace("- ✅ Plugin loader. *(Item 102)*\n", "")
    out = _drop_at(text, 3, 2)
    assert "## Stage 3 — Plugins — ✅" in out
    assert "| 3 | Plugins | G3 | ✅ |" in out
    assert "| G3 Plugins | Stage 3 | ✅ |" in out


def test_the_cli_refuses_dropping_the_last_bullet_and_writes_nothing(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path, _drop_at(UNMARKED, 3, 1))
    path = repo / "docs" / "aide" / "progress.md"
    before = path.read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", "--stage", "3",
                      "--deliverable", "2", "dropped", "--reason", "x",
                      "--no-commit"]) == 1
    err = capsys.readouterr().err
    assert "is the last deliverable of stage 3 not ❌" in err
    assert "NOT changed" in err
    assert path.read_bytes() == before


def test_an_item_number_on_the_drop_form_is_refused_in_its_own_words(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path, ISSUE)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", "31", "dropped",
                      "--stage", "3", "--deliverable", "3", "--reason", "x",
                      "--no-commit"]) == 2
    err = capsys.readouterr().err
    assert ("takes no item number — an itemised bullet is dropped with "
            "`aide progress set NNN dropped --reason …`") in err
    assert "deferred with" not in err
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


# --------------------------------------------------------------------------- #
# set NNN resumed / set --stage N --deliverable K resumed (issue #380)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("status", ["in-progress", "in-review", "done"])
def test_a_forward_set_over_a_deferred_item_is_refused_naming_the_resume(
        tmp_path: Path, capsys, status):
    """`set NNN in-progress` on a ⏸️ item never claimed left it 🚧 with no
    branch, which `claim` never offers. Every forward status is refused now,
    writing nothing, and the message names the one way back."""
    repo = _repo(tmp_path, _defer())
    path = repo / "docs" / "aide" / "progress.md"
    before = path.read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", "31", status,
                      "--no-commit"]) == 1
    err = capsys.readouterr().err
    assert "item 031 is ⏸️ deferred" in err
    assert "`aide progress set 031 resumed --reason …`" in err
    assert "NOT changed" in err
    assert path.read_bytes() == before


def test_a_forward_set_still_moves_an_item_resumed_would_refuse(
        tmp_path: Path, capsys):
    """A ⏸️ bullet beside a ✅ one (a hand edit, or a pre-2.33.0 file) is an
    item `resumed` refuses, so the forward set is not held there: refusing
    both would leave only typing over the icons."""
    text = _defer().replace("- ✅ Summary. *(Item 030)*",
                            "- ✅ Summary. *(Item 031)*")
    repo = _repo(tmp_path, text)
    assert aide.main(["--repo", str(repo), "progress", "set", "31", "resumed",
                      "--reason", "x", "--no-commit"]) == 1
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "progress", "set", "31", "done",
                      "--no-commit"]) == 0
    assert aide._item_bullet_statuses((repo / "docs" / "aide" / "progress.md")
                                      .read_text(encoding="utf-8").splitlines(),
                                      31) == ["complete", "complete"]


def test_set_resumed_writes_through_the_cli_and_no_insight(tmp_path: Path, capsys):
    repo = _repo(tmp_path, _defer())
    path = repo / "docs" / "aide" / "progress.md"
    assert aide.main(["--repo", str(repo), "progress", "set", "31", "resumed",
                      "--reason", "owner wants it now", "--date", "2026-10-02",
                      "--no-commit"]) == 0
    assert "item 031: resumed — owner wants it now" in capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == aide.resume_item(
        _defer(), 31, "owner wants it now", "2026-10-02")[0]
    assert (repo / "docs" / "aide" / "insights.md").read_text(
        encoding="utf-8") == "# Insight Inbox\n"
    # Resumed, the item moves forward again.
    assert aide.main(["--repo", str(repo), "progress", "set", "31",
                      "in-progress", "--no-commit"]) == 0


@pytest.mark.parametrize("argv, code, message", [
    (["31", "resumed"], 2, "--reason is required"),
    (["31", "resumed", "--reason", "  "], 2, "--reason is required"),
    (["31", "resumed", "--reason", "a\nb"], 2, "line break"),
    (["31", "resumed", "--criterion", "1", "--reason", "x"], 2, "resumed whole"),
    (["30", "resumed", "--reason", "x"], 1, "only a ⏸️ deferred item can be resumed"),
], ids=["no-reason", "blank-reason", "two-lines", "with-criterion", "done-item"])
def test_set_resumed_refuses_and_writes_nothing(tmp_path: Path, capsys, argv,
                                                code, message):
    repo = _repo(tmp_path, _defer())
    path = repo / "docs" / "aide" / "progress.md"
    before = path.read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", *argv,
                      "--no-commit"]) == code
    assert message in capsys.readouterr().err
    assert path.read_bytes() == before


def test_resume_by_position_writes_through_the_cli(tmp_path: Path, capsys):
    deferred = _defer_at(UNMARKED, 3, 1)
    repo = _repo(tmp_path, deferred)
    path = repo / "docs" / "aide" / "progress.md"
    assert aide.main(["--repo", str(repo), "progress", "set", "--stage", "3",
                      "--deliverable", "1", "resumed", "--reason", "queued",
                      "--date", "2026-10-02", "--no-commit"]) == 0
    assert path.read_text(encoding="utf-8") == aide.resume_deliverable(
        deferred, 3, 1, "queued", "2026-10-02")[0]
    assert (repo / "docs" / "aide" / "insights.md").read_text(
        encoding="utf-8") == "# Insight Inbox\n"


@pytest.mark.parametrize("argv, code, message", [
    (["--stage", "3", "--deliverable", "1", "resumed"], 2,
     "--reason is required"),
    (["31", "resumed", "--stage", "3", "--deliverable", "1", "--reason", "x"],
     2, "an itemised bullet is resumed with `aide progress set NNN resumed"),
    (["--stage", "3", "--deliverable", "2", "resumed", "--reason", "x"], 0,
     "no change"),
    (["--stage", "2", "--deliverable", "2", "resumed", "--reason", "x"], 1,
     "`aide progress set 031 resumed --reason …`"),
], ids=["no-reason", "with-number", "planned-bullet", "itemised"])
def test_resume_by_position_refuses_and_writes_nothing(tmp_path: Path, capsys,
                                                       argv, code, message):
    repo = _repo(tmp_path, _defer_at(UNMARKED, 3, 1))
    path = repo / "docs" / "aide" / "progress.md"
    before = path.read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", *argv,
                      "--no-commit"]) == code
    captured = capsys.readouterr()
    assert message in captured.err + captured.out
    assert path.read_bytes() == before


# --------------------------------------------------------------------------- #
# set NNN dropped / set NNN restored / set --stage N --deliverable K restored
# (issue #381)
# --------------------------------------------------------------------------- #
DROP_ITEM_REASON = "the owner decided against charts"


def _drop(text: str = PROGRESS, num: int = 32, reason: str = DROP_ITEM_REASON,
          date: str = "2026-10-02") -> str:
    return aide.drop_item(text, num, reason, date)[0]


def test_drop_item_flips_its_bullet_and_writes_the_reason_under_it():
    out, message = aide.drop_item(PROGRESS, 31, DROP_ITEM_REASON, "2026-10-02")
    assert message == f"item 031: dropped — {DROP_ITEM_REASON}"
    lines = out.splitlines()
    i = lines.index("- ❌ Export, a deliverable long enough that its author")
    assert lines[i + 1] == "  wrapped it onto a second line. *(Item 031)*"
    assert lines[i + 2] == f"  - **2026-10-02** → dropped: {DROP_ITEM_REASON}"
    assert aide._parse_item_status(lines)[2][31] == "excluded"
    # ✅ 030 beside 📋 032: the stage is still 🚧.
    assert "## Stage 2 — Reports — 🚧" in out
    assert aide.derived_cell_findings(lines) == ([], [], set())


def test_dropping_every_open_item_lets_the_stage_close():
    """❌ counts toward ✅, so with 030 shipped and 031, 032 dropped the stage,
    its row and its objective close — the item form of #362's drop."""
    out = _drop(_drop(), 31)
    assert "## Stage 2 — Reports — ✅" in out
    assert "| 2 | Reports | G2 | ✅ |" in out
    assert "| G2 Reports | Stage 2 | ✅ |" in out
    assert "- [ ] Reports render." in out  # no box is ticked by a drop
    assert aide.derived_cell_findings(out.splitlines()) == ([], [], set())


@pytest.mark.parametrize("icon", ["📋", "🚧", "🔍", "⏸️"])
def test_drop_item_takes_every_open_bullet(icon):
    text = PROGRESS.replace("- 📋 Charts. *(Item 032)*", f"- {icon} Charts. *(Item 032)*")
    out = _drop(text)
    assert "- ❌ Charts. *(Item 032)*" in out
    assert aide.derived_cell_findings(out.splitlines()) == ([], [], set())


def test_drop_item_refuses_a_shipped_item_naming_reopen():
    with pytest.raises(ValueError, match=r"item 030 is ✅ complete; it shipped, "
                                         r"so there is nothing to drop — send it "
                                         r"back with `aide progress reopen` first"):
        aide.drop_item(PROGRESS, 30, "x", "2026-10-02")


def test_drop_item_refuses_an_item_no_bullet_names():
    with pytest.raises(ValueError, match="nothing to drop"):
        aide.drop_item(PROGRESS, 99, "x", "2026-10-02")


def test_drop_item_refuses_leaving_a_stage_all_dropped():
    """The item form of #362's refusal: a stage whose every bullet is ❌ rolls
    up 📋, a stage still to plan, so it is withdrawn whole instead."""
    only = PROGRESS.replace("- ✅ Summary. *(Item 030)*\n", "").replace(
        "- 📋 Charts. *(Item 032)*\n", "")
    with pytest.raises(ValueError, match=(
            r"dropping item 031 would leave every deliverable of stage 2 ❌.*"
            r"marking its row in the Stage summary table ❌")):
        aide.drop_item(only, 31, "x", "2026-10-02")


def test_dropping_a_dropped_item_is_no_change():
    once = _drop()
    again, message = aide.drop_item(once, 32, "again", "2026-10-03")
    assert again == once and message == "item 032: no change (already dropped)"


def test_drop_item_desugars_a_shared_marker_and_moves_only_the_named_item():
    shared = PROGRESS.replace("- 📋 Charts. *(Item 032)*",
                              "- 📋 Charts and tables. *(Items 032, 033)*")
    splits = []
    out = aide.drop_item(shared, 33, "no tables", "2026-10-02", splits)[0]
    lines = out.splitlines()
    assert "- 📋 Charts and tables. *(Item 032)*" in lines
    i = lines.index("- ❌ Charts and tables. *(Item 033)*")
    assert lines[i + 1] == "  - **2026-10-02** → dropped: no tables"
    assert len(splits) == 1


def test_restoring_a_dropped_item_reopens_the_stage_it_let_close():
    """Dropped work wanted after all goes back to 📋 under a `restored:` line
    beside the drop's, and the stage the drop let close follows it down."""
    closed = _drop(_drop(), 31)
    out, message = aide.restore_item(closed, 32, "charts are wanted after all",
                                     "2026-10-03")
    assert message == "item 032: restored — charts are wanted after all"
    lines = out.splitlines()
    i = lines.index("- 📋 Charts. *(Item 032)*")
    assert lines[i + 1:i + 3] == [
        f"  - **2026-10-02** → dropped: {DROP_ITEM_REASON}",
        "  - **2026-10-03** → restored: charts are wanted after all"]
    assert "## Stage 2 — Reports — 🚧" in out
    assert "| 2 | Reports | G2 | 🚧 |" in out
    assert "| G2 Reports | Stage 2 | 🚧 |" in out
    assert aide._parse_item_status(lines)[2][32] == "planned"
    assert aide.derived_cell_findings(lines) == ([], [], set())


@pytest.mark.parametrize("icon,status", [
    ("🚧", "in-progress"), ("🔍", "in-review"), ("✅", "complete"),
    ("⏸️", "deferred")])
def test_restore_refuses_an_item_that_is_not_dropped_and_names_its_status(
        icon, status):
    text = PROGRESS.replace("- 📋 Charts. *(Item 032)*", f"- {icon} Charts. *(Item 032)*")
    with pytest.raises(ValueError, match=f"item 032 is {icon} {status}; only "
                                         f"a ❌ dropped item can be restored"):
        aide.restore_item(text, 32, "x", "2026-10-02")


def test_restore_names_the_resume_for_a_deferred_item():
    with pytest.raises(ValueError, match=r"a ⏸️ item is resumed with `aide "
                                         r"progress set 031 resumed --reason …`"):
        aide.restore_item(_defer(), 31, "x", "2026-10-02")


def test_restoring_a_planned_item_is_no_change():
    out, message = aide.restore_item(PROGRESS, 32, "x", "2026-10-02")
    assert out == PROGRESS and "no change" in message


def test_restore_deliverable_takes_a_dropped_bullet_back_to_planned():
    """The positional way back from `drop_deliverable`: the stage the drop
    closed is open work again."""
    dropped = _drop_at(ISSUE)
    assert "## Stage 3 — Plugins — ✅" in dropped
    out, message = aide.restore_deliverable(dropped, 3, 3, "wanted", "2026-10-03")
    assert message == "stage 3 deliverable 3: restored — wanted"
    lines = out.splitlines()
    i = lines.index("- 📋 Optional plugin marketplace, a deliverable long enough that its")
    assert lines[i + 2:i + 4] == [f"  - **2026-10-02** → dropped: {DROP_REASON}",
                                  "  - **2026-10-03** → restored: wanted"]
    assert "## Stage 3 — Plugins — 🚧" in out
    assert "| 3 | Plugins | G3 | 🚧 |" in out
    assert "| G3 Plugins | Stage 3 | 🚧 |" in out
    assert aide.derived_cell_findings(lines) == ([], [], set())
    again, message = aide.restore_deliverable(out, 3, 3, "y", "2026-10-04")
    assert again == out and "no change" in message


@pytest.mark.parametrize("icon,status", [
    ("🚧", "in-progress"), ("🔍", "in-review"), ("✅", "complete"),
    ("⏸️", "deferred")])
def test_restore_deliverable_refuses_a_bullet_that_is_not_dropped(icon, status):
    text = ISSUE.replace("- 📋 Optional plugin", f"- {icon} Optional plugin")
    with pytest.raises(ValueError, match=f"stage 3 deliverable 3 is {icon} "
                                         f"{status}; only a ❌ dropped "
                                         f"deliverable can be restored"):
        aide.restore_deliverable(text, 3, 3, "x", "2026-10-02")


def test_restore_deliverable_refuses_an_itemised_bullet_naming_the_item_form():
    with pytest.raises(ValueError, match=r"restore it by item with `aide "
                                         r"progress set 101 restored --reason …`"):
        aide.restore_deliverable(ISSUE, 3, 1, "x", "2026-10-02")


@pytest.mark.parametrize("status", ["in-progress", "in-review", "done"])
def test_a_forward_set_over_a_dropped_item_is_refused_naming_the_restore(
        tmp_path: Path, capsys, status):
    """`RANK` puts ❌ lowest, so a forward set cleared a drop silently — no
    reason, no trail line. Refused now, writing nothing, naming the way back."""
    repo = _repo(tmp_path, _drop())
    path = repo / "docs" / "aide" / "progress.md"
    before = path.read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", "32", status,
                      "--no-commit"]) == 1
    err = capsys.readouterr().err
    assert "item 032 is ❌ dropped" in err
    assert "`aide progress set 032 restored --reason …`" in err
    assert "NOT changed" in err
    assert path.read_bytes() == before


def test_a_forward_set_still_moves_an_item_restored_would_refuse(
        tmp_path: Path, capsys):
    """A ❌ bullet beside a ✅ one (a hand edit) is an item `restored`
    refuses, so the forward set is not held there: refusing both would leave
    only typing over the icons."""
    text = _drop().replace("- ✅ Summary. *(Item 030)*",
                           "- ✅ Summary. *(Item 032)*")
    repo = _repo(tmp_path, text)
    assert aide.main(["--repo", str(repo), "progress", "set", "32", "restored",
                      "--reason", "x", "--no-commit"]) == 1
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "progress", "set", "32", "done",
                      "--no-commit"]) == 0
    assert aide._item_bullet_statuses((repo / "docs" / "aide" / "progress.md")
                                      .read_text(encoding="utf-8").splitlines(),
                                      32) == ["complete", "complete"]


def test_set_dropped_and_restored_write_through_the_cli_and_no_insight(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    path = repo / "docs" / "aide" / "progress.md"
    base = ["--repo", str(repo), "progress", "set", "32"]
    assert aide.main([*base, "dropped", "--reason", DROP_ITEM_REASON,
                      "--date", "2026-10-02", "--no-commit"]) == 0
    assert f"item 032: dropped — {DROP_ITEM_REASON}" in capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == _drop()
    assert aide.main([*base, "restored", "--reason", "wanted", "--date",
                      "2026-10-03", "--no-commit"]) == 0
    assert "item 032: restored — wanted" in capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == aide.restore_item(
        _drop(), 32, "wanted", "2026-10-03")[0]
    assert (repo / "docs" / "aide" / "insights.md").read_text(
        encoding="utf-8") == "# Insight Inbox\n"
    # Restored, the item moves forward again.
    assert aide.main([*base, "in-progress", "--no-commit"]) == 0


@pytest.mark.parametrize("argv, code, message", [
    (["32", "dropped"], 2, "--reason is required"),
    (["32", "restored", "--reason", "  "], 2, "--reason is required"),
    (["32", "dropped", "--reason", "a\nb"], 2, "line break"),
    (["32", "dropped", "--criterion", "1", "--reason", "x"], 2, "dropped whole"),
    (["30", "dropped", "--reason", "x"], 1, "nothing to drop"),
    (["32", "restored", "--reason", "x"], 0, "no change"),
    (["31", "restored", "--reason", "x"], 1,
     "only a ❌ dropped item can be restored"),
], ids=["no-reason", "blank-reason", "two-lines", "with-criterion",
        "done-item", "planned-item", "in-progress-item"])
def test_set_dropped_and_restored_refuse_and_write_nothing(
        tmp_path: Path, capsys, argv, code, message):
    repo = _repo(tmp_path)
    path = repo / "docs" / "aide" / "progress.md"
    before = path.read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", *argv,
                      "--no-commit"]) == code
    captured = capsys.readouterr()
    assert message in captured.err + captured.out
    assert path.read_bytes() == before


def test_restore_by_position_writes_through_the_cli(tmp_path: Path, capsys):
    dropped = _drop_at(ISSUE)
    repo = _repo(tmp_path, dropped)
    path = repo / "docs" / "aide" / "progress.md"
    assert aide.main(["--repo", str(repo), "progress", "set", "--stage", "3",
                      "--deliverable", "3", "restored", "--reason", "wanted",
                      "--date", "2026-10-03", "--no-commit"]) == 0
    assert path.read_text(encoding="utf-8") == aide.restore_deliverable(
        dropped, 3, 3, "wanted", "2026-10-03")[0]
    before = path.read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", "101", "restored",
                      "--stage", "3", "--deliverable", "1", "--reason", "x",
                      "--no-commit"]) == 2
    assert ("an itemised bullet is restored with `aide progress set NNN "
            "restored --reason …`") in capsys.readouterr().err
    assert path.read_bytes() == before


# --------------------------------------------------------------------------- #
# a ❌-withdrawn stage and the objective rollup (issue #382)
# --------------------------------------------------------------------------- #
#: G1 is delivered by stages 1 and 2; stage 2 is withdrawn whole — its
#: summary row ❌ — with its bullets left as they were.
WITHDRAWN = (PROGRESS
             .replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | ❌ |")
             .replace("| G1 Rules | Stage 1 | ✅ |", "| G1 Rules | Stages 1, 2 | ✅ |")
             .replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | ❌ |"))


def test_a_withdrawn_stage_is_left_out_of_the_objective_rollup():
    lines = WITHDRAWN.splitlines()
    assert aide.withdrawn_stages(lines) == {"2"}
    status = aide.stage_rollups(lines)
    assert status["2"] == "in-progress"  # its bullets still say 🚧
    assert aide.objective_rollup(["1", "2"], status, {"2"}) == "complete"
    assert aide.objective_rollup(["2"], status, {"2"}) == "excluded"
    # Read from the bullets alone, as before #382.
    assert aide.objective_rollup(["1", "2"], status) == "in-progress"


def test_check_reads_an_objective_from_the_stages_still_in_scope(tmp_path: Path):
    """Stage 1 ✅ and stage 2 withdrawn: G1 ✅ is what the stages in scope
    say, not the error it was, and a G1 left 🚧 is the warning."""
    errors, warnings = _checks(_repo(tmp_path, WITHDRAWN))
    assert errors == [] and not _about(warnings, "objective "), (errors, warnings)
    stale = WITHDRAWN.replace("| G1 Rules | Stages 1, 2 | ✅ |",
                              "| G1 Rules | Stages 1, 2 | 🚧 |")
    errors, warnings = _checks(_repo(tmp_path, stale, "stale"))
    assert errors == []
    assert _about(warnings, "objective G1:") == [
        "objective G1: 🚧 in-progress but the stages it names (stage 1 ✅, "
        "2 ❌ withdrawn) roll up to ✅ complete — an Objective row follows "
        "its stages, so set it to ✅"], warnings


@pytest.mark.parametrize("icon, status, where", [
    ("📋", "planned", "warnings"), ("🚧", "in-progress", "warnings"),
    ("✅", "complete", "errors")])
def test_an_objective_whose_every_stage_is_withdrawn_reads_excluded(
        tmp_path: Path, icon, status, where):
    text = WITHDRAWN.replace("| G2 Reports | Stage 2 | ❌ |",
                             f"| G2 Reports | Stage 2 | {icon} |")
    errors, warnings = _checks(_repo(tmp_path, text))
    found = {"errors": errors, "warnings": warnings}[where]
    assert _about(found, "objective G2:") == [
        f"objective G2: {icon} {status} but every stage it names (stage 2) "
        f"is withdrawn — ❌ in the Stage summary table — so set it to ❌"], found


def test_the_writer_follows_a_withdrawn_stage_and_check_stays_silent():
    """A verb over stage 1 rolls G1 up to ✅ past the withdrawn stage 2, and
    writes ❌ on G2, which only withdrawn stages deliver."""
    text = (WITHDRAWN.replace("- ✅ Bounds. *(Item 027)*", "- 🚧 Bounds. *(Item 027)*")
            .replace("## Stage 1 — Rules — ✅", "## Stage 1 — Rules — 🚧")
            .replace("| 1 | Rules | G1 | ✅ |", "| 1 | Rules | G1 | 🚧 |")
            .replace("| G1 Rules | Stages 1, 2 | ✅ |", "| G1 Rules | Stages 1, 2 | 🚧 |")
            .replace("| G2 Reports | Stage 2 | ❌ |", "| G2 Reports | Stage 2 | 🚧 |"))
    out = aide.set_item_status(text, 27, "complete")
    assert "| G1 Rules | Stages 1, 2 | ✅ |" in out
    assert "| G2 Reports | Stage 2 | ❌ |" in out
    assert "| 2 | Reports | G2 | ❌ |" in out  # the withdrawal stands
    assert aide.derived_cell_findings(out.splitlines()) == ([], [], set())


# --------------------------------------------------------------------------- #
# PR #386 review: the ❌-beside-📋 item, and a stage already withdrawn
# --------------------------------------------------------------------------- #
#: Item 032 with one ❌ bullet and one 📋 bullet — a hand edit, but one
#: `restored` can take, so a forward set holds it.
MIXED_DROP = PROGRESS.replace(
    "- 📋 Charts. *(Item 032)*",
    "- 📋 Charts. *(Item 032)*\n- ❌ Chart export. *(Item 032)*")


def test_an_item_with_a_dropped_and_a_planned_bullet_is_held_and_restored(
        tmp_path: Path, capsys):
    """`held_from_forward` holds an item whose bullets are all ❌ or 📋, not
    only all ❌: the forward set refuses it, and `restored` takes the ❌
    bullet to 📋 and leaves the 📋 one as it was."""
    assert aide.held_from_forward(MIXED_DROP.splitlines(), 32) == "excluded"
    repo = _repo(tmp_path, MIXED_DROP)
    path = repo / "docs" / "aide" / "progress.md"
    before = path.read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "set", "32",
                      "in-progress", "--no-commit"]) == 1
    assert "`aide progress set 032 restored --reason …`" in capsys.readouterr().err
    assert path.read_bytes() == before
    assert aide.main(["--repo", str(repo), "progress", "set", "32", "restored",
                      "--reason", "export wanted", "--date", "2026-10-03",
                      "--no-commit"]) == 0
    lines = path.read_text(encoding="utf-8").splitlines()
    i = lines.index("- 📋 Charts. *(Item 032)*")
    assert lines[i + 1:i + 3] == ["- 📋 Chart export. *(Item 032)*",
                                  "  - **2026-10-03** → restored: export wanted"]
    assert aide._item_bullet_statuses(lines, 32) == ["planned", "planned"]
    assert aide.main(["--repo", str(repo), "progress", "set", "32",
                      "in-progress", "--no-commit"]) == 0


def test_a_withdrawn_stage_lets_its_last_bullet_drop_by_either_form():
    """The all-❌ refusal sends the owner to the ❌ summary row; where that row
    already reads ❌ there is nothing to send them to, so the last bullet
    drops like any other, by its item or by its place."""
    only = (PROGRESS.replace("- ✅ Summary. *(Item 030)*\n", "")
            .replace("- 📋 Charts. *(Item 032)*\n", "")
            .replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | ❌ |"))
    out = _drop(only, 31)
    assert "- ❌ Export, a deliverable long enough that its author" in out
    assert "| 2 | Reports | G2 | ❌ |" in out
    assert "| G2 Reports | Stage 2 | ❌ |" in out
    assert aide.derived_cell_findings(out.splitlines()) == ([], [], set())
    # Not withdrawn, the same drop is refused (the rule this narrows).
    with pytest.raises(ValueError, match="would leave every deliverable"):
        aide.drop_item(only.replace("| 2 | Reports | G2 | ❌ |",
                                    "| 2 | Reports | G2 | 🚧 |"), 31, "x",
                       "2026-10-02")

    withdrawn = UNMARKED.replace("| 3 | Plugins | G3 | ⏸️ |",
                                 "| 3 | Plugins | G3 | ❌ |")
    out = _drop_at(_drop_at(withdrawn, 3, 1), 3, 2)
    assert "- ❌ Ingestion of human abnormality labels; a classification arm" in out
    assert "| G3 Plugins | Stage 3 | ❌ |" in out
    assert aide.derived_cell_findings(out.splitlines()) == ([], [], set())
    with pytest.raises(ValueError, match="is the last deliverable of stage 3"):
        aide.drop_deliverable(_drop_at(UNMARKED, 3, 1), 3, 2, "x", "2026-10-02")
