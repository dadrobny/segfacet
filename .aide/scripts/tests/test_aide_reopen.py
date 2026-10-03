"""Reopening a ✅ item, and reading a correction back by its state today.

Issue #271 (enhancement): `aide progress set` only moves an item forward, so a
deliverable closed on merged code whose operator-run Validation never happened
had no verb back to 📋. A consumer hand-edited the bullet from ✅ to 📋 so
`aide claim` would offer the item again, and the edit left no trail.
`aide progress reopen NNN --reason …` is `retract` one level up: it flips the
bullet, writes the reason as a dated trail line under it, rolls the stage back
down, and routes the finding as a `gap` entry.

Issue #273 (bug): `retracted_criteria` read every `retracted:` trail line
without reading the box's tick, so a box re-accepted through `accept` — the
path the retraction itself names — was still reported as "open again",
forever. Both readers are now keyed on the latest correction and worded by
the state today.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_reopen", _MODULE_PATH)
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
- ✅ Bounds, a deliverable long enough that its author
  wrapped it onto a second line. *(Item 027)*
- ✅ Coverage. *(Item 028)*

**Acceptance.**
- [x] Rules fire. *(validator, 2026-07-01: eval run)*

## Stage 2 — Reports — 🚧

**Deliverables.**
- ✅ Summary. *(Item 030)*
- 🚧 Export. *(Item 031)*

**Acceptance.**
- [ ] Reports render.
"""

SOLE = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | Rules | G1 | ✅ |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 1 | ✅ |

## Stage 1 — Rules — ✅

**Deliverables.**
- ✅ Bounds. *(Item 027)*

**Acceptance.**
- [ ] Rules fire.
"""


def _reopen(text: str = PROGRESS, num: int = 27, reason: str = "operator run never happened",
            date: str = "2026-09-24") -> str:
    return aide.reopen_item(text, num, reason, date)[0]


# --------------------------------------------------------------------------- #
# reopen_item — the flip, the trail, the rollup
# --------------------------------------------------------------------------- #
def test_reopen_flips_the_bullet_and_writes_the_reason_under_it():
    out = _reopen().splitlines()
    i = out.index("- 📋 Bounds, a deliverable long enough that its author")
    # The bullet's own text and marker are untouched, the trail line goes
    # below its LAST wrapped line, and the item now reads as planned.
    assert out[i + 1] == "  wrapped it onto a second line. *(Item 027)*"
    assert out[i + 2] == "  - **2026-09-24** → reopened: operator run never happened"
    assert aide._parse_item_status(out)[2][27] == "planned"


def test_reopen_leaves_everything_but_the_item_as_it_was():
    before = PROGRESS.splitlines()
    out = _reopen().splitlines()
    changed = [l for l in out if l not in before]
    assert changed == [
        "| 1 | Rules | G1 | 🚧 |",
        "| G1 Rules | Stage 1 | 🚧 |",
        "## Stage 1 — Rules — 🚧",
        "- 📋 Bounds, a deliverable long enough that its author",
        "  - **2026-09-24** → reopened: operator run never happened",
    ]
    # Every acceptance box stays exactly as the author wrote it.
    assert [l for l in out if l.startswith("- [")] == [
        l for l in before if l.startswith("- [")]
    status = aide._parse_item_status(out)[2]
    assert (status[28], status[30], status[31]) == ("complete", "complete",
                                                    "in-progress")


def test_reopen_rolls_the_stage_and_its_objective_back_down():
    """A stage whose only item is reopened goes to 📋, header, summary row and
    Objective row alike — otherwise `aide check` reports drift on the spot."""
    out = _reopen(SOLE)
    assert "| 1 | Rules | G1 | 📋 |" in out
    assert "| G1 Rules | Stage 1 | 📋 |" in out
    assert "## Stage 1 — Rules — 📋" in out


def test_reopen_leaves_an_unrelated_stages_drift_alone():
    """The downgrade is scoped to the reopened item's stage: a hand-typed
    over-claim elsewhere is `aide check`'s to report, not this verb's to
    quietly rewrite."""
    drifted = PROGRESS.replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | ✅ |")
    drifted = drifted.replace("| G2 Reports | Stage 2 | 🚧 |",
                              "| G2 Reports | Stage 2 | ✅ |")
    out = _reopen(drifted)
    assert "| 2 | Reports | G2 | ✅ |" in out
    assert "| G2 Reports | Stage 2 | ✅ |" in out


def test_reopen_appends_after_an_existing_trail_newest_last():
    seeded = PROGRESS.replace(
        "- ✅ Coverage. *(Item 028)*",
        "- ✅ Coverage. *(Item 028)*\n"
        "    - **2026-09-01** → reopened: first time\n"
        "    - **2026-09-02** → a hand-written note")
    out = _reopen(seeded, num=28, reason="second time").splitlines()
    i = out.index("- 📋 Coverage. *(Item 028)*")
    assert out[i + 1:i + 4] == [
        "    - **2026-09-01** → reopened: first time",
        "    - **2026-09-02** → a hand-written note",
        "    - **2026-09-24** → reopened: second time",
    ]


def test_a_trail_line_is_never_read_as_a_deliverable_or_an_owner():
    """The trail sits where a nested bullet would, so every reader of the
    Deliverables block is asked: none of them sees a bullet, a nested status,
    a lost marker or a copy — and the item's ownership is still read from the
    bullet's last wrapped line, not from the trail below it."""
    lines = _reopen().splitlines()
    assert aide.nested_deliverable_warnings(lines) == []
    assert aide.identical_deliverable_warnings(lines) == []
    assert aide.unattributed_reference_warnings(lines) == []
    start, end, _ = aide.stage_sections(lines)[0]
    assert aide.stage_deliverable_statuses(lines, start, end) == [
        "planned", "complete"]
    spans = aide._deliverable_bullet_spans(lines)
    owners = [aide._bullet_marker_item_numbers(lines[last]) for _, last in spans]
    assert owners == [[27], [28], [30], [31]]
    # And a later `set` still finds the bullet by that marker.
    done = aide.set_item_status("\n".join(lines) + "\n", 27, "complete")
    assert "- ✅ Bounds, a deliverable long enough that its author" in done
    assert "  - **2026-09-24** → reopened: operator run never happened" in done


def test_a_back_filled_bullet_lands_below_the_last_bullets_trail():
    """`progress set`'s self-heal appends after the stage's last bullet. Put
    between that bullet and its `reopened:` line, the new bullet would take
    the line as its own: the reopened item would stop being reported, and
    the healed one would be reported as reopened, with no lint to see it
    (PR #278 review)."""
    reopened = _reopen(num=28)
    healed = aide.insert_item_reference(reopened, 99, "1", "New deliverable")
    assert ("- 📋 Coverage. *(Item 028)*\n"
            "  - **2026-09-24** → reopened: operator run never happened\n"
            "- 📋 New deliverable. *(Item 099)*\n") in healed
    assert [r.item for r in aide.reopened_items(healed.splitlines())] == [28]


def test_a_trail_carrying_an_item_reference_attributes_nothing():
    """A reason naming another item is prose on a line that is not a bullet."""
    lines = _reopen(reason="blocked on *(Item 031)*").splitlines()
    assert aide._parse_item_status(lines)[2][31] == "in-progress"
    assert aide.unattributed_reference_warnings(lines) == []


def test_reopen_desugars_a_shared_marker_and_moves_only_the_named_item():
    shared = SOLE.replace("- ✅ Bounds. *(Item 027)*",
                          "- ✅ Bounds and coverage. *(Items 027, 028)*")
    splits = []
    out, _ = aide.reopen_item(shared, 28, "coverage unmeasured", "2026-09-24", splits)
    lines = out.splitlines()
    assert "- ✅ Bounds and coverage. *(Item 027)*" in lines
    i = lines.index("- 📋 Bounds and coverage. *(Item 028)*")
    assert lines[i + 1] == "  - **2026-09-24** → reopened: coverage unmeasured"
    assert len(splits) == 1
    assert "| 1 | Rules | G1 | 🚧 |" in lines


@pytest.mark.parametrize("icon,status", [("🚧", "in-progress"), ("📋", "planned"),
                                         ("🔍", "in-review"), ("⏸️", "deferred"),
                                         ("❌", "excluded")])
def test_reopen_refuses_an_item_that_is_not_done_and_names_its_status(icon, status):
    text = PROGRESS.replace("- ✅ Coverage. *(Item 028)*", f"- {icon} Coverage. *(Item 028)*")
    with pytest.raises(ValueError, match=f"item 028 is .*{status}, not ✅"):
        aide.reopen_item(text, 28, "x", "2026-09-24")


def test_reopen_refuses_when_one_of_the_items_bullets_is_not_done():
    two = PROGRESS.replace("- 🚧 Export. *(Item 031)*",
                           "- 🚧 Export. *(Item 031)*\n- 🚧 More bounds. *(Item 027)*")
    with pytest.raises(ValueError, match="in-progress, not ✅"):
        aide.reopen_item(two, 27, "x", "2026-09-24")


def test_reopen_refuses_an_item_no_bullet_names():
    with pytest.raises(ValueError, match="nothing to reopen"):
        aide.reopen_item(PROGRESS, 99, "x", "2026-09-24")


# --------------------------------------------------------------------------- #
# reading a reopening back — keyed on the item's status today
# --------------------------------------------------------------------------- #
def test_a_reopened_item_is_read_back_as_open():
    (r,) = aide.reopened_items(_reopen().splitlines())
    assert (r.item, r.date, r.reason, r.status, r.completed) == (
        27, "2026-09-24", "operator run never happened", "planned", False)
    said = aide.reopening_summary(r)
    assert "item 027 was reopened on 2026-09-24 (operator run never happened)" in said
    assert "📋 again" in said


def test_an_item_completed_again_is_never_reported_as_open():
    done = aide.set_item_status(_reopen(), 27, "complete")
    (r,) = aide.reopened_items(done.splitlines())
    assert r.completed and r.completed_on is None
    said = aide.reopening_summary(r)
    assert "reopened on 2026-09-24 (operator run never happened) and completed again since" in said
    assert "again, and the trail" not in said


def test_completed_again_names_the_newest_dated_line_since_when_there_is_one():
    done = aide.set_item_status(_reopen(), 27, "complete").replace(
        "  - **2026-09-24** → reopened: operator run never happened",
        "  - **2026-09-24** → reopened: operator run never happened\n"
        "  - **2026-09-30** → operator run done on the rig")
    (r,) = aide.reopened_items(done.splitlines())
    assert "and completed again on 2026-09-30" in aide.reopening_summary(r)


def test_the_latest_reopening_is_the_one_reported():
    once = aide.set_item_status(_reopen(date="2026-09-01", reason="first"), 27, "complete")
    twice = _reopen(once, date="2026-09-24", reason="second")
    (r,) = aide.reopened_items(twice.splitlines())
    assert (r.date, r.reason, r.completed) == ("2026-09-24", "second", False)


def test_reopen_raises_no_check_error(tmp_path: Path):
    repo = _repo(tmp_path, SOLE)
    assert aide.main(["--repo", str(repo), "progress", "reopen", "27",
                      "--reason", "operator run never happened", "--no-commit"]) == 0
    errors, warnings = aide.run_checks(repo, aide.load_config(repo), branches=[])
    assert errors == []
    assert [w for w in warnings if "reopened" in w] == [
        f"progress.md: item 027 was reopened on {_today()} (operator run "
        f"never happened) — it is 📋 again, and the trail under its bullet "
        f"keeps the earlier ✅ on record"]
    # Nothing else the reopen wrote is reported: no drift, no nested bullet.
    assert not any("disagrees" in w or "nested" in w or "summary shows" in w
                   for w in warnings), warnings


def _today() -> str:
    import datetime
    return datetime.date.today().isoformat()


# --------------------------------------------------------------------------- #
# the CLI — refusals, routing, status
# --------------------------------------------------------------------------- #
AIDE_TOML = '[project]\nname = "Demo"\ndocs_dir = "docs/aide"\n'


def _repo(tmp_path: Path, progress: str = PROGRESS) -> Path:
    repo = tmp_path / "repo"
    ddir = repo / "docs" / "aide"
    ddir.mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (ddir / "progress.md").write_text(progress, encoding="utf-8")
    (ddir / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    return repo


def test_reopen_refuses_without_a_stated_reason_and_writes_nothing(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    for extra in ([], ["--reason", "   "], ["--reason", "two\nlines"]):
        assert aide.main(["--repo", str(repo), "progress", "reopen", "27",
                          *extra, "--no-commit"]) == 2, extra
    assert "--reason is required" in capsys.readouterr().err
    # An item is reopened whole: no status, no criterion, no --all.
    assert aide.main(["--repo", str(repo), "progress", "reopen", "27", "done",
                      "--reason", "x", "--no-commit"]) == 2
    assert aide.main(["--repo", str(repo), "progress", "reopen", "27",
                      "--criterion", "1", "--reason", "x", "--no-commit"]) == 2
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


def test_reopen_of_an_item_not_done_exits_one_and_writes_nothing(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert aide.main(["--repo", str(repo), "progress", "reopen", "31",
                      "--reason", "x", "--no-commit"]) == 1
    err = capsys.readouterr().err
    assert "item 031 is 🚧 in-progress, not ✅" in err and "NOT changed" in err
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before
    assert (repo / "docs" / "aide" / "insights.md").read_text(
        encoding="utf-8") == "# Insight Inbox\n"


def test_reopen_routes_its_finding_into_the_inbox(tmp_path: Path, capsys):
    """A reopened item is a finding, routed as `retract` routes one."""
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "progress", "reopen", "27",
                      "--reason", "operator run never happened",
                      "--date", "2026-09-24", "--no-commit"]) == 0
    out = capsys.readouterr().out
    assert "captured a gap entry for the reopening" in out
    assert "will warn about this reopening from now on" in out
    inbox = (repo / "docs" / "aide" / "insights.md").read_text(encoding="utf-8")
    assert "- [ ] gap — item reopened: operator run never happened *(item 027, 2026-09-24" in inbox
    progress = (repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")
    assert "  - **2026-09-24** → reopened: operator run never happened" in progress
    # The entry is one `aide check` reads as well-shaped.
    _, warnings = aide.run_checks(repo, aide.load_config(repo), branches=[])
    assert not any("insights.md" in w for w in warnings), warnings


def test_status_prints_a_reopened_item_by_its_status_today(tmp_path: Path, capsys):
    repo = _repo(tmp_path, _reopen())
    _git_init(repo)
    assert aide.main(["--repo", str(repo), "status", "--no-fetch"]) == 0
    out = capsys.readouterr().out
    assert "reopened: item 027 (2026-09-24) — operator run never happened" in out
    assert "completed again" not in out

    (repo / "docs" / "aide" / "progress.md").write_text(
        aide.set_item_status(_reopen(), 27, "complete"), encoding="utf-8")
    assert aide.main(["--repo", str(repo), "status", "--no-fetch"]) == 0
    assert ("reopened: item 027 (2026-09-24) — operator run never happened; "
            "completed again since") in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# issue #273 — a retracted box is read by its tick today
# --------------------------------------------------------------------------- #
RETRACTED = SOLE.replace(
    "- [ ] Rules fire.",
    "- [x] Rules fire. *(validator, 2026-07-01)*\n"
    "  - **2026-07-02** → retracted: the host was misread\n"
    "  - **2026-07-03** → accepted: re-run on the GPU host")


def test_a_re_accepted_box_is_reported_as_re_accepted_not_open():
    """The issue's own fixture: retracted, then accepted with a dated line."""
    (r,) = aide.retracted_criteria(RETRACTED.splitlines())
    assert r == aide.Retraction("1", 1, "2026-07-02", "the host was misread",
                                True, "2026-07-03")
    said = aide.retraction_summary(r)
    assert said == ("stage 1 criterion 1 was retracted on 2026-07-02 (the "
                    "host was misread) and re-accepted on 2026-07-03 — the "
                    "box is ticked again, and the retraction is kept in its "
                    "trail")
    assert "open again" not in said


def test_a_box_re_accepted_with_no_dated_line_says_since():
    """`accept --evidence` annotates the box line, not the trail."""
    text = SOLE.replace(
        "- [ ] Rules fire.",
        "- [ ] Rules fire. *(validator, 2026-07-01)*\n"
        "  - **2026-07-02** → retracted: the host was misread")
    ticked, _ = aide.accept_criteria(text, "1", [1], evidence="re-run")
    (r,) = aide.retracted_criteria(ticked.splitlines())
    assert r.reaccepted and r.reaccepted_on is None
    assert "and re-accepted since — the box is ticked again" in aide.retraction_summary(r)


def test_a_box_retracted_again_is_open_and_keyed_on_the_second_retraction():
    again, _ = aide.retract_criterion(RETRACTED, "1", 1, "the rig drifted", "2026-08-01")
    (r,) = aide.retracted_criteria(again.splitlines())
    assert r == aide.Retraction("1", 1, "2026-08-01", "the rig drifted", False, None)
    assert aide.retraction_summary(r) == (
        "stage 1 criterion 1 was retracted on 2026-08-01 (the rig drifted) — "
        "the box is open again, and the original attestation is kept above "
        "the correction")


def test_check_and_status_word_a_re_accepted_box_by_its_tick(tmp_path: Path, capsys):
    repo = _repo(tmp_path, RETRACTED)
    _, warnings = aide.run_checks(repo, aide.load_config(repo), branches=[])
    hits = [w for w in warnings if "retracted" in w]
    assert len(hits) == 1 and "re-accepted on 2026-07-03" in hits[0], warnings
    assert "open again" not in hits[0]
    _git_init(repo)
    assert aide.main(["--repo", str(repo), "status", "--no-fetch"]) == 0
    assert ("retracted: stage 1 criterion 1 (2026-07-02) — the host was "
            "misread; re-accepted on 2026-07-03") in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# issue #332 — a CI reopening is stamped with its fix round
# --------------------------------------------------------------------------- #
QUEUE_1 = "# Demo — Work Queue 001\n\n### Item 027: Bounds\n### Item 028: Coverage\n"
QUEUE_2 = "# Demo — Work Queue 002\n\n### Item 030: Summary\n### Item 031: Export\n"


def _queued(tmp_path: Path, progress: str = PROGRESS) -> Path:
    """A repo with no git — the scope is then the queue file listing the item."""
    repo = _repo(tmp_path, progress)
    qdir = repo / "docs" / "aide" / "queue"
    qdir.mkdir()
    (qdir / "queue-001.md").write_text(QUEUE_1, encoding="utf-8")
    (qdir / "queue-002.md").write_text(QUEUE_2, encoding="utf-8")
    return repo


def _reopen_cli(repo: Path, num: int, reason: str) -> int:
    return aide.main(["--repo", str(repo), "progress", "reopen", str(num),
                      "--reason", reason, "--date", "2026-09-29", "--no-commit"])


def _trail(repo: Path, num: int) -> List[str]:
    lines = (repo / "docs" / "aide" / "progress.md").read_text(
        encoding="utf-8").splitlines()
    for _, last in aide._deliverable_bullet_spans(lines):
        if num in aide._bullet_marker_item_numbers(lines[last]):
            return [lines[i].strip() for i in aide.deliverable_bullet_trail(lines, last)]
    raise AssertionError(f"no bullet for item {num}")


def _merge_back(repo: Path, *nums: int) -> None:
    path = repo / "docs" / "aide" / "progress.md"
    text = path.read_text(encoding="utf-8")
    for n in nums:
        text = aide.set_item_status(text, n, "complete")
    path.write_text(text, encoding="utf-8")


def test_a_ci_reopening_begins_a_round_the_next_one_joins_and_a_later_one_begins_another(
        tmp_path: Path, capsys):
    repo = _queued(tmp_path)
    assert _reopen_cli(repo, 27, "CI build (ubuntu): test_027_bounds") == 0
    assert "[CI round 1]" in capsys.readouterr().out
    assert _trail(repo, 27) == [
        "- **2026-09-29** → reopened: CI build (ubuntu): test_027_bounds [CI round 1]"]
    inbox = (repo / "docs" / "aide" / "insights.md").read_text(encoding="utf-8")
    assert ("- [ ] gap — item reopened: CI build (ubuntu): test_027_bounds "
            "[CI round 1] *(item 027, 2026-09-29") in inbox
    # 027 is still open: a second item traced in the same round joins it.
    assert _reopen_cli(repo, 28, "CI lint: step ruff") == 0
    assert _trail(repo, 28)[-1].endswith("[CI round 1]")
    # Both merged back: the queue was exhausted and marked ready since, so
    # the next red check's reopening begins round 2 — even for an item the
    # first round never touched.
    _merge_back(repo, 27, 28)
    assert _reopen_cli(repo, 28, "CI build (windows): test_028_paths") == 0
    assert _trail(repo, 28)[-1].endswith("[CI round 2]")
    assert aide.ci_fix_rounds(
        (repo / "docs/aide/progress.md").read_text(encoding="utf-8").splitlines(),
        {27, 28}) == (2, True)


def test_a_reopening_that_is_not_ci_is_neither_stamped_nor_counted(tmp_path: Path):
    repo = _queued(tmp_path)
    assert _reopen_cli(repo, 27, "operator run never happened") == 0
    assert _trail(repo, 27) == ["- **2026-09-29** → reopened: operator run never happened"]
    # An open non-CI reopening does not hold a round open either.
    assert _reopen_cli(repo, 28, "CI build: test_028") == 0
    assert _trail(repo, 28)[-1].endswith("[CI round 1]")
    lines = (repo / "docs/aide/progress.md").read_text(encoding="utf-8").splitlines()
    assert aide.next_ci_round(lines, {27}) == 1


def test_the_round_is_counted_over_the_queue_listing_the_item_only(tmp_path: Path):
    """Queue 002's items carry round 3; queue 001's first CI reopening is
    still its round 1."""
    other = PROGRESS.replace(
        "- ✅ Summary. *(Item 030)*",
        "- ✅ Summary. *(Item 030)*\n"
        "  - **2026-09-20** → reopened: CI build: t [CI round 3]")
    repo = _queued(tmp_path, other)
    assert _reopen_cli(repo, 27, "CI build: test_027") == 0
    assert _trail(repo, 27)[-1].endswith("[CI round 1]")
    lines = (repo / "docs/aide/progress.md").read_text(encoding="utf-8").splitlines()
    assert aide.ci_fix_rounds(lines, {30, 31}) == (3, False)


def test_a_reason_carrying_its_own_round_stamp_is_refused(tmp_path: Path, capsys):
    repo = _queued(tmp_path)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert _reopen_cli(repo, 27, "CI build: t [CI round 4]") == 2
    assert "the engine writes the round" in capsys.readouterr().err
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


@pytest.mark.parametrize("reason", ["CI: build failed", "CI-build: t"])
def test_a_reason_naming_ci_without_the_space_is_refused(tmp_path: Path, capsys,
                                                         reason: str):
    """`CI:` would silently not be a CI reopening: no stamp, no count."""
    repo = _queued(tmp_path)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert _reopen_cli(repo, 27, reason) == 2
    assert "`CI <check>: <failing test or step>`" in capsys.readouterr().err
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


def test_a_reason_merely_mentioning_ci_is_an_ordinary_reopening(tmp_path: Path):
    """Only `CI:` / `CI-` is refused: these are reasons about CI, not CI
    reopenings, and are neither refused nor stamped."""
    repo = _queued(tmp_path)
    for num, reason in ((27, "CI/CD workflow never ran"),
                        (28, "CI's config was never reviewed"), (30, "CI")):
        assert _reopen_cli(repo, num, reason) == 0, reason
        assert _trail(repo, num)[-1] == f"- **2026-09-29** → reopened: {reason}"


ATTESTED = PROGRESS.replace(
    "- ✅ Coverage. *(Item 028)*",
    "- ✅ Coverage. *(Item 028)*\n- ✅ Validate stage 1. *(Item 029)*")


def test_a_fix_round_through_an_attested_stage_reads_as_no_regression(tmp_path: Path):
    """Issue #332's stage-rollup question. Reopening 027 turns stage 1 — every
    box ticked — from ✅ to 🚧 until it merges back; nothing reads the brief
    🚧 as a regression. `check` reports the reopening and nothing else the
    reopen wrote, and the merge back restores the stage and its objective."""
    repo = _queued(tmp_path, ATTESTED)
    cfg = aide.load_config(repo)
    _, clean = aide.run_checks(repo, cfg, branches=[])
    assert _reopen_cli(repo, 27, "CI build: test_027") == 0
    text = (repo / "docs/aide/progress.md").read_text(encoding="utf-8")
    assert "## Stage 1 — Rules — 🚧" in text and "- [x] Rules fire." in text
    errors, during = aide.run_checks(repo, cfg, branches=[])
    assert errors == []
    assert [w for w in during if w not in clean] == [
        "progress.md: item 027 was reopened on 2026-09-29 (CI build: test_027 "
        "[CI round 1]) — it is 📋 again, and the trail under its bullet keeps "
        "the earlier ✅ on record"]
    _merge_back(repo, 27)
    text = (repo / "docs/aide/progress.md").read_text(encoding="utf-8")
    assert "## Stage 1 — Rules — ✅" in text
    assert "| 1 | Rules | G1 | ✅ |" in text and "| G1 Rules | Stage 1 | ✅ |" in text
    errors, after = aide.run_checks(repo, cfg, branches=[])
    assert errors == []
    assert [w for w in after if w not in clean] == [
        "progress.md: item 027 was reopened on 2026-09-29 (CI build: test_027 "
        "[CI round 1]) and completed again since — the reopening is kept in "
        "the trail under its bullet"]


def _git_init(path: Path) -> None:
    """`aide status` refuses outside a repository (issue #352)."""
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
