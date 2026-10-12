"""`aide progress rollup`, and the maintenance stage recognised — issue #459.

Two halves of one issue. A bullet added by hand under a ✅ stage — every
maintenance batch does it (issue #454) — left the stage's header and Stage
summary row ✅ over the new 📋 bullet, and `aide check` errored on both until
the next verb moved a bullet of the stage; the queue's author wrote the 🚧 by
hand. `aide progress rollup [--stage N]` writes the rollup instead.

And the maintenance stage is the stage titled exactly `Maintenance`, so §1 →
roadmap.md's prose rules about it — at most one, no Objective row, no
blocking dependency either way, no acceptance criteria — are warnings.

Document-tree tests, bar two that commit — the verb's commit, and its
put-back on a failed one, which `tests/test_fixture_consumer.py` also drives
against a real install.
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_maintenance", _MODULE_PATH)
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
| 3 | Maintenance | — | ✅ |

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
- 📋 Charts. *(Item 032)*

**Acceptance.**
- [ ] Reports render.

## Stage 3 — Maintenance — ✅

**Deliverables.**
- ✅ Fix 040. *(Item 040)*
"""

#: The batch's hand edit: a new 📋 bullet under the ✅ maintenance stage.
REOPENED = PROGRESS + "- 📋 Fix 041. *(Item 041)*\n"

AIDE_TOML = '[project]\nname = "Demo"\ndocs_dir = "docs/aide"\n'


def _repo(tmp_path: Path, progress: str = PROGRESS, roadmap: str = "") -> Path:
    repo = tmp_path / "repo"
    ddir = repo / "docs" / "aide"
    ddir.mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (ddir / "progress.md").write_text(progress, encoding="utf-8")
    (ddir / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    if roadmap:
        (ddir / "roadmap.md").write_text(roadmap, encoding="utf-8")
    return repo


def _findings_about(text: str, stage: str):
    errors, warnings, _ = aide.derived_cell_findings(text.splitlines())
    return [f for f in errors + warnings if f.startswith(f"stage {stage}:")]


# --------------------------------------------------------------------------- #
# rollup_progress
# --------------------------------------------------------------------------- #
def test_a_reopened_stage_rolls_down_to_in_progress_and_check_is_clean():
    """The issue's window: ✅ over a new 📋 bullet is an error until rolled."""
    assert any("marked ✅ but has non-complete deliverables" in f
               and "'aide progress rollup --stage 3'" in f
               for f in _findings_about(REOPENED, "3"))
    out, messages = aide.rollup_progress(REOPENED, 3)
    assert "## Stage 3 — Maintenance — 🚧" in out
    assert "| 3 | Maintenance | — | 🚧 |" in out
    assert messages == ["stage 3: summary row ✅ → 🚧 in-progress",
                        "stage 3: header ✅ → 🚧 in-progress"]
    assert _findings_about(out, "3") == []


def test_a_stage_already_at_its_rollup_is_no_change():
    out, messages = aide.rollup_progress(PROGRESS, 3)
    assert out == PROGRESS and messages == []
    out, messages = aide.rollup_progress(PROGRESS)
    assert out == PROGRESS and messages == []


def test_stage_n_writes_its_own_cells_and_leaves_every_other_as_it_reads():
    """A drifted cell of another stage, and an Objective row naming none of
    the stage rolled up, are left exactly as they read."""
    text = REOPENED.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — ✅")
    text = text.replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | 📋 |")
    out, _ = aide.rollup_progress(text, 3)
    assert "## Stage 2 — Reports — ✅" in out
    assert "| G2 Reports | Stage 2 | 📋 |" in out
    assert "## Stage 3 — Maintenance — 🚧" in out


def test_with_no_stage_every_stage_and_objective_row_follows_its_rollup():
    text = REOPENED.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — ✅")
    text = text.replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | 📋 |")
    out, messages = aide.rollup_progress(text)
    assert "## Stage 2 — Reports — 🚧" in out
    assert "| G2 Reports | Stage 2 | 🚧 |" in out
    assert "## Stage 3 — Maintenance — 🚧" in out
    assert "objective G2 📋 → 🚧 in-progress" in messages
    errors, warnings, _ = aide.derived_cell_findings(out.splitlines())
    assert errors == [] and warnings == []


def test_an_objective_row_naming_the_stage_follows_it_down():
    text = PROGRESS.replace("- 📋 Charts. *(Item 032)*", "- ✅ Charts. *(Item 032)*")
    text = text.replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | ✅ |")
    text = text.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — ✅")
    text = text.replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | ✅ |")
    text = text.replace("**Acceptance.**\n- [ ] Reports render.",
                        "- 📋 Tables, added by hand.\n\n"
                        "**Acceptance.**\n- [ ] Reports render.")
    out, messages = aide.rollup_progress(text, 2)
    assert "| G2 Reports | Stage 2 | 🚧 |" in out
    assert messages == ["stage 2: summary row ✅ → 🚧 in-progress",
                        "objective G2 ✅ → 🚧 in-progress",
                        "stage 2: header ✅ → 🚧 in-progress"]


def test_an_objective_row_follows_every_stage_it_names():
    """`--stage 3` rolls G2's row, which names stages 2 and 3, from both:
    stage 3 is ✅, stage 2 rolls up to 🚧, so the row reads 🚧 — while
    stage 2's own cells, not rolled up, are left as they read."""
    text = PROGRESS.replace("| G2 Reports | Stage 2 | 🚧 |",
                            "| G2 Reports | Stages 2, 3 | ✅ |")
    text = text.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — ✅")
    out, messages = aide.rollup_progress(text, 3)
    assert "| G2 Reports | Stages 2, 3 | 🚧 |" in out
    assert "## Stage 2 — Reports — ✅" in out
    assert messages == ["objective G2 ✅ → 🚧 in-progress"]
    errors, _, _ = aide.derived_cell_findings(out.splitlines())
    assert not [e for e in errors if "G2" in e]


PADDED = """\
## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 07 | Maintenance | — | ✅ |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 07 | ✅ |
| G2 Reports | Stage 7 | ✅ |

## Stage 07 — Maintenance — ✅

**Deliverables.**
- ✅ Fix 040. *(Item 040)*
- 📋 Fix 041. *(Item 041)*
"""


def test_a_zero_padded_stage_rolls_up_as_check_reads_it(tmp_path: Path, capsys):
    """`--stage 7` and `--stage 07` are one stage, and so are a section
    headed `07` and a row naming `Stage 07`. A row naming `Stage 7` under a
    section headed `07` names no section as `aide check` reads it, so the
    rollup derives nothing for it and leaves it, as check does."""
    out, messages = aide.rollup_progress(PADDED, 7)
    assert "## Stage 07 — Maintenance — 🚧" in out
    assert "| 07 | Maintenance | — | 🚧 |" in out
    assert "| G1 Rules | Stage 07 | 🚧 |" in out
    assert "| G2 Reports | Stage 7 | ✅ |" in out
    _, warnings, _ = aide.derived_cell_findings(out.splitlines())
    assert any(w.startswith("objective G2: Delivered by 'Stage 7' names no "
                            "stage") for w in warnings)
    printed = []
    for i, stage in enumerate(("7", "07")):
        repo = _repo(tmp_path / str(i), PADDED)
        assert _rollup(repo, "--stage", stage) == 0
        printed.append(capsys.readouterr().out)
        assert (repo / "docs" / "aide" / "progress.md").read_text(
            encoding="utf-8") == out
    assert printed[0] == printed[1] == "".join(m + "\n" for m in messages)


def test_a_deferred_cell_set_by_hand_is_written_over():
    """The decision: rollup writes what the bullets say, a hand-set ⏸️ too —
    once a bullet is added a computed ⏸️ and a typed one read the same."""
    text = PROGRESS.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — ⏸️")
    text = text.replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | ⏸️ |")
    text = text.replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | ⏸️ |")
    out, messages = aide.rollup_progress(text, 2)
    assert "## Stage 2 — Reports — 🚧" in out
    assert "| 2 | Reports | G2 | 🚧 |" in out
    assert "| G2 Reports | Stage 2 | 🚧 |" in out
    assert "stage 2: header ⏸️ → 🚧 in-progress" in messages


def test_a_reopened_stage_holding_a_deferred_bullet_reaches_its_rollup():
    """Why the ⏸️ is not held: a maintenance stage that rolled up to ⏸️
    reopens to what its rollup computes — 📋 over ⏸️ and 📋 alone, 🚧 once a
    bullet has shipped."""
    text = PROGRESS.replace("- ✅ Fix 040. *(Item 040)*", "- ⏸️ Fix 040. *(Item 040)*")
    text = text.replace("| 3 | Maintenance | — | ✅ |", "| 3 | Maintenance | — | ⏸️ |")
    text = text.replace("## Stage 3 — Maintenance — ✅", "## Stage 3 — Maintenance — ⏸️")
    out, _ = aide.rollup_progress(text + "- 📋 Fix 041. *(Item 041)*\n", 3)
    assert "## Stage 3 — Maintenance — 📋" in out
    assert "| 3 | Maintenance | — | 📋 |" in out
    assert _findings_about(out, "3") == []
    shipped = text + "- ✅ Fix 039. *(Item 039)*\n- 📋 Fix 041. *(Item 041)*\n"
    out, _ = aide.rollup_progress(shipped, 3)
    assert "## Stage 3 — Maintenance — 🚧" in out
    assert "| 3 | Maintenance | — | 🚧 |" in out
    assert _findings_about(out, "3") == []


def test_a_withdrawn_stage_and_an_excluded_cell_are_left_as_they_read():
    text = PROGRESS.replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | ❌ |")
    text = text.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — ✅")
    out, messages = aide.rollup_progress(text, 2)
    assert out.count("## Stage 2 — Reports — ✅") == 1
    assert "| 2 | Reports | G2 | ❌ |" in out
    header = REOPENED.replace("## Stage 3 — Maintenance — ✅", "## Stage 3 — Maintenance — ❌")
    out, _ = aide.rollup_progress(header, 3)
    assert "## Stage 3 — Maintenance — ❌" in out
    assert "| 3 | Maintenance | — | 🚧 |" in out


def test_a_stage_with_no_bullet_derives_nothing():
    text = PROGRESS.replace("- ✅ Fix 040. *(Item 040)*\n", "")
    out, messages = aide.rollup_progress(text, 3)
    assert out == text and messages == []


def test_a_stage_with_no_section_is_refused():
    with pytest.raises(ValueError, match=r"no '## Stage 9' section"):
        aide.rollup_progress(PROGRESS, 9)


# --------------------------------------------------------------------------- #
# every drift remedy that names the verb is cleared by running it
# --------------------------------------------------------------------------- #
_NAMED = re.compile(r"'aide progress rollup --stage (\d+)'")

_DONE_2 = (PROGRESS.replace("- 📋 Charts. *(Item 032)*", "- ✅ Charts. *(Item 032)*"))


@pytest.mark.parametrize("text, about", [
    # A stage header below its rollup, and a summary row above one.
    (PROGRESS.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — 📋"),
     "stage 2:"),
    (PROGRESS.replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | 🔍 |"),
     "stage 2:"),
    # Every open bullet deferred under cells that say otherwise.
    (PROGRESS.replace("- 📋 Charts. *(Item 032)*", "- ⏸️ Charts. *(Item 032)*"),
     "stage 2:"),
    # Every bullet ✅ under cells that are not — the Outcome-target arm.
    (_DONE_2.replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | ✅ |"),
     "stage 2:"),
    # An Objective row off its stages, both ways.
    (PROGRESS.replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | 📋 |"),
     "objective G2:"),
    (_DONE_2.replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | ✅ |")
     .replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — ✅"),
     "objective G2:"),
    # One naming two stages, below and above: the first is the one named.
    (PROGRESS.replace("| G1 Rules | Stage 1 | ✅ |", "| G1 Rules | Stages 1, 2 | 📋 |"),
     "objective G1"),
    (PROGRESS.replace("| G1 Rules | Stage 1 | ✅ |", "| G1 Rules | Stages 1, 2 | ✅ |"),
     "objective G1"),
    # The stage named is the first live one: not a withdrawn stage ahead of
    # it, which rollup skips, nor one with no deliverable, which derives none.
    (PROGRESS.replace("| 1 | Rules | G1 | ✅ |", "| 1 | Rules | G1 | ❌ |")
     .replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stages 1, 2 | ✅ |"),
     "objective G2"),
    (PROGRESS.replace("| 3 | Maintenance | — | ✅ |",
                      "| 3 | Maintenance | — | ✅ |\n| 4 | Later | G2 | 📋 |")
     .replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stages 4, 2 | ✅ |")
     + "\n## Stage 4 — Later — 📋\n\n**Deliverables.**\n",
     "objective G2"),
])
def test_a_drift_warning_names_the_rollup_and_running_it_clears_it(text, about):
    errors, warnings, _ = aide.derived_cell_findings(text.splitlines())
    hits = [f for f in errors + warnings if f.startswith(about)]
    assert len(hits) == 1, errors + warnings
    named = _NAMED.search(hits[0])
    assert named, hits[0]
    out, messages = aide.rollup_progress(text, int(named.group(1)))
    assert messages, hits[0]
    errors, warnings, _ = aide.derived_cell_findings(out.splitlines())
    assert not [f for f in errors + warnings if f.startswith(about)]


@pytest.mark.parametrize("text", [
    # A ⏸️ typed over open work: the remedy is the deferral (§1 → progress.md).
    PROGRESS.replace("## Stage 2 — Reports — 🚧", "## Stage 2 — Reports — ⏸️"),
    PROGRESS.replace("| G2 Reports | Stage 2 | 🚧 |", "| G2 Reports | Stage 2 | ⏸️ |"),
    # An objective every stage of which is withdrawn: rollup skips the stage.
    PROGRESS.replace("| 2 | Reports | G2 | 🚧 |", "| 2 | Reports | G2 | ❌ |"),
])
def test_a_deferred_or_withdrawn_remedy_does_not_name_the_rollup(text):
    errors, warnings, _ = aide.derived_cell_findings(text.splitlines())
    assert errors + warnings
    assert not [f for f in errors + warnings if _NAMED.search(f)], errors + warnings


# --------------------------------------------------------------------------- #
# the verb, outside git — the commit is test_fixture_consumer's
# --------------------------------------------------------------------------- #
def _rollup(repo: Path, *argv: str) -> int:
    return aide.main(["--repo", str(repo), "progress", "rollup", *argv,
                      "--no-commit"])


def test_the_verb_writes_the_rollup_and_prints_each_cell(tmp_path: Path, capsys):
    repo = _repo(tmp_path, REOPENED)
    assert _rollup(repo, "--stage", "3") == 0
    out = capsys.readouterr().out
    assert "stage 3: header ✅ → 🚧 in-progress" in out
    text = (repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")
    assert "## Stage 3 — Maintenance — 🚧" in text
    assert _findings_about(text, "3") == []


def test_the_verb_is_a_no_op_exit_0_when_nothing_changes(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert _rollup(repo) == 0
    assert "every stage: no change" in capsys.readouterr().out
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


def test_the_verb_refuses_a_stage_with_no_section(tmp_path: Path, capsys):
    repo = _repo(tmp_path, REOPENED)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert _rollup(repo, "--stage", "9") == 1
    assert "no '## Stage 9' section" in capsys.readouterr().err
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


@pytest.mark.parametrize("argv", [
    ["3"], ["--stage", "3", "extra"], ["--stage", "3", "--deliverable", "1"],
    ["--reason", "why"], ["--criterion", "1"], ["--all"], ["--item", "41"],
    ["--text", "new prose"], ["--evidence", "seen"], ["--date", "2026-10-09"],
    ["3", "done"],
])
def test_the_verb_refuses_any_argument_but_stage_and_no_commit(
        tmp_path: Path, capsys, argv):
    repo = _repo(tmp_path, REOPENED)
    before = (repo / "docs" / "aide" / "progress.md").read_bytes()
    assert _rollup(repo, *argv) == 2
    assert "takes --stage N and --no-commit alone" in capsys.readouterr().err
    assert (repo / "docs" / "aide" / "progress.md").read_bytes() == before


def _git(args, repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True,
                          text=True, encoding="utf-8", check=True)


def _committed_repo(tmp_path: Path) -> Path:
    repo = _repo(tmp_path, REOPENED)
    (repo / "aide.toml").write_text(
        AIDE_TOML + '\n[git]\nmode = "local"\nmain_branch = "main"\n',
        encoding="utf-8")
    _git(["init", "-q", "-b", "main"], repo)
    _git(["config", "user.name", "t"], repo)
    _git(["config", "user.email", "t@example.com"], repo)
    _git(["config", "core.autocrlf", "false"], repo)
    _git(["add", "-A"], repo)
    _git(["commit", "-qm", "init"], repo)
    return repo


def test_the_verb_commits_progress_alone(tmp_path: Path):
    repo = _committed_repo(tmp_path)
    head = _git(["rev-parse", "HEAD"], repo).stdout
    argv = ["--repo", str(repo), "progress", "rollup", "--stage", "3"]
    assert aide.main(argv) == 0
    assert _git(["log", "-1", "--format=%s"], repo).stdout.strip() == (
        "progress(aide): roll up stage 3")
    assert _git(["status", "--porcelain"], repo).stdout == ""
    assert "## Stage 3 — Maintenance — 🚧" in _git(
        ["show", "HEAD:docs/aide/progress.md"], repo).stdout
    assert _git(["rev-parse", "HEAD~1"], repo).stdout == head
    assert aide.main(argv) == 0                    # nothing left: no commit
    assert _git(["rev-parse", "HEAD~1"], repo).stdout == head


def test_a_rollup_whose_commit_fails_is_put_back_and_exits_1(tmp_path: Path):
    """Issue #309's rule, as every recording verb keeps it: a held index lock
    fails the commit on every platform, and the edit goes back byte for byte."""
    repo = _committed_repo(tmp_path)
    path = repo / "docs" / "aide" / "progress.md"
    before, head = path.read_bytes(), _git(["rev-parse", "HEAD"], repo).stdout
    lock = repo / ".git" / "index.lock"
    lock.write_bytes(b"")
    try:
        assert aide.main(["--repo", str(repo), "progress", "rollup"]) == 1
    finally:
        lock.unlink()
    assert path.read_bytes() == before
    assert _git(["rev-parse", "HEAD"], repo).stdout == head


# --------------------------------------------------------------------------- #
# maintenance_stage_warnings
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("line, title", [
    ("## Stage 3 — Maintenance", "Maintenance"),
    ("## Stage 3 — Maintenance — ✅", "Maintenance"),
    ("## Stage 3 — **Maintenance**", "Maintenance"),
    ("## Stage 3 — Maintenance  <!-- OPTIONAL: at most one -->", "Maintenance"),
    ("## Stage 3: Maintenance", "Maintenance"),
    ("## Stage 3 — Maintenance batch 2", "Maintenance batch 2"),
    ("## Stage 3 — Hardening — 🚧", "Hardening"),
    ("Stage 3 — Maintenance", None),
])
def test_the_title_is_read_past_the_icon_comment_and_emphasis(line, title):
    assert aide.stage_title(line) == title


ROADMAP = """\
# R

| Objective | Delivered by |
|---|---|
| G1 Rules | Stage 1 |
| G2 Reports | Stage 2 |

## Stage 1 — Rules

**Dependencies.** None.

**Validation / acceptance.**

- Rules fire.

## Stage 2 — Reports

**Dependencies.** Stage 1. Independent of Stage 3 — may be queued in either
order.

**Validation / acceptance.**

- Reports render.

## Stage 3 — Maintenance

**Goal.** Repairs to shipped work.

**Deliverables.** Added to `progress.md` by each maintenance queue.

**Dependencies.** None.
"""


def _maint(tmp_path: Path, roadmap: str = ROADMAP, progress: str = PROGRESS):
    return aide.maintenance_stage_warnings(_repo(tmp_path, progress, roadmap)
                                           / "docs" / "aide")


def test_the_template_shape_is_silent(tmp_path: Path):
    """An ordering sentence after the blocking slot names it and is silent."""
    assert _maint(tmp_path) == []


def test_a_second_maintenance_stage_is_named(tmp_path: Path):
    roadmap = ROADMAP + "\n## Stage 4 — Maintenance\n\n**Dependencies.** None.\n"
    progress = PROGRESS + "\n## Stage 4 — Maintenance — 📋\n\n**Deliverables.**\n"
    out = _maint(tmp_path, roadmap, progress)
    assert [w[:56] for w in out] == [
        "roadmap.md: stages 3, 4 are all titled 'Maintenance' — a",
        "progress.md: stages 3, 4 are all titled 'Maintenance' — "]
    assert all(w.endswith("— §1 → roadmap.md") for w in out)
    # The remedy names the route the owner takes: an amendment, not the
    # create-roadmap entry point (issue #461).
    assert all("the owner keeps one, by an amendment to roadmap.md — " in w
               for w in out)


def test_a_stage_titled_otherwise_is_not_the_maintenance_stage(tmp_path: Path):
    roadmap = ROADMAP + "\n## Stage 4 — Maintenance batch 2\n\n**Dependencies.** None.\n"
    assert _maint(tmp_path, roadmap) == []


def test_a_coverage_row_naming_it_is_named(tmp_path: Path):
    roadmap = ROADMAP.replace("| G2 Reports | Stage 2 |", "| G2 Reports | Stages 2, 3 |")
    out = _maint(tmp_path, roadmap)
    assert len(out) == 1
    assert out[0].startswith("roadmap.md: the coverage row for G2 names stage 3, "
                             "the maintenance stage")


def test_a_progress_objective_row_naming_it_is_named(tmp_path: Path):
    progress = PROGRESS.replace("| G2 Reports | Stage 2 | 🚧 |",
                                "| G2 Reports | Stages 2, 3 | 🚧 |")
    out = _maint(tmp_path, progress=progress)
    assert len(out) == 1
    assert out[0].startswith("progress.md: objective G2's Delivered by cell "
                             "names stage 3, the maintenance stage")


def test_a_blocking_slot_naming_it_is_named(tmp_path: Path):
    roadmap = ROADMAP.replace("**Dependencies.** Stage 1. Independent of Stage 3",
                              "**Dependencies.** Stages 1 and 3. Independent of Stage 3")
    out = _maint(tmp_path, roadmap)
    assert len(out) == 1
    assert out[0].startswith("roadmap.md: stage 2's Dependencies name stage 3, "
                             "the maintenance stage, in the blocking slot")


def test_its_own_blocking_slot_naming_a_stage_is_named(tmp_path: Path):
    roadmap = ROADMAP.replace("**Deliverables.** Added to `progress.md` by each "
                              "maintenance queue.\n\n**Dependencies.** None.",
                              "**Deliverables.** Added to `progress.md` by each "
                              "maintenance queue.\n\n**Dependencies.** Stage 1.")
    out = _maint(tmp_path, roadmap)
    assert len(out) == 1
    assert out[0].startswith("roadmap.md: stage 3, the maintenance stage, names "
                             "stage 1 in its Dependencies' blocking slot")


_CRITERIA = ROADMAP + "\n**Validation / acceptance.**\n\n- Repairs land.\n- Target: p95 < 1s.\n"


def test_criteria_on_a_maintenance_stage_not_started_are_named(tmp_path: Path):
    planned = PROGRESS.replace("| 3 | Maintenance | — | ✅ |", "| 3 | Maintenance | — | 📋 |")
    planned = planned.replace("## Stage 3 — Maintenance — ✅", "## Stage 3 — Maintenance — 📋")
    planned = planned.replace("- ✅ Fix 040. *(Item 040)*\n", "")
    out = _maint(tmp_path, _CRITERIA, planned)
    assert out == [
        "roadmap.md: stage 3, the maintenance stage, has 1 Validation / "
        "acceptance bullet and has not started — it has no acceptance "
        "criteria of its own: each maintenance item's spec carries its own, "
        "so remove the block — §1 → roadmap.md"]


def test_criteria_with_no_progress_section_are_named(tmp_path: Path):
    no_section = PROGRESS.split("## Stage 3 — Maintenance")[0].replace(
        "| 3 | Maintenance | — | ✅ |\n", "")
    assert len(_maint(tmp_path, _CRITERIA, no_section)) == 1


@pytest.mark.parametrize("icon", ["✅", "🚧", "⏸️"])
def test_criteria_on_a_started_maintenance_stage_are_grandfathered(
        tmp_path: Path, icon: str):
    """A started stage is frozen, and one retitled to `Maintenance` keeps
    the criteria it was written with: the two cannot be told apart, and
    neither can be edited, so neither is named."""
    started = PROGRESS.replace("| 3 | Maintenance | — | ✅ |",
                               f"| 3 | Maintenance | — | {icon} |")
    assert _maint(tmp_path, _CRITERIA, started) == []


def test_check_reports_them_as_warnings_and_never_errors(tmp_path: Path):
    roadmap = ROADMAP.replace("| G2 Reports | Stage 2 |", "| G2 Reports | Stages 2, 3 |")
    repo = _repo(tmp_path, PROGRESS, roadmap)
    errors, warnings = aide.run_checks(repo, aide.load_config(repo), branches=[])
    assert errors == []
    assert any(w.startswith("roadmap.md: the coverage row for G2 names stage 3")
               for w in warnings)
