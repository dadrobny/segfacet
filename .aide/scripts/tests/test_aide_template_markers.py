"""Issue #164: a document records the template version it was created from.

Every template carries ``<!-- aide-template: <name> <N> -->`` after its header
comment, and a document created from it keeps the line. `aide check` compares
the line with the installed template's and warns — never errors, since
`docs/aide/**` is the project's (rung 4 of the copies rule) — when they differ.
These tests drive `run_checks` over a document tree, with the installed
versions passed in or read from the templates beside the script, so they run
the same in this repository and in the `.aide/scripts/tests/` copy an install
ships.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_template_markers", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


AIDE_TOML = """\
[project]
name = "Demo"
docs_dir = "docs/aide"
"""

PROGRESS = """\
# Demo — Progress

> Step 3.

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
- ✅ Bounds. *(Item 001)*
- 📋 Coverage. *(Item 002)*

**Acceptance.**
- [ ] Rules fire.
"""

QUEUE = """\
# Demo — Work Queue 001

> Step 4.

### Item 001: Bounds
Set them.

### Item 002: Coverage
Measure it.
"""


def _marker(name: str, version: int) -> str:
    return f"<!-- aide-template: {name} {version} -->\n"


def _repo(tmp_path: Path, progress_marker: str = "") -> Path:
    repo = tmp_path / "repo"
    ddir = repo / "docs" / "aide"
    (ddir / "items").mkdir(parents=True)
    (ddir / "queue").mkdir()
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (ddir / "progress.md").write_text(progress_marker + PROGRESS, encoding="utf-8")
    (ddir / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    return repo


def _drift(repo: Path, installed):
    ddir = repo / "docs" / "aide"
    lines = (ddir / "progress.md").read_text(encoding="utf-8").splitlines()
    return aide.template_drift_warnings(
        ddir, aide._parse_item_status(lines)[2], installed)


# --------------------------------------------------------------------------- #
# the templates themselves
# --------------------------------------------------------------------------- #
_TEMPLATES = sorted(aide._TEMPLATES_DIR.glob("*.md"))


def test_there_are_templates():
    assert len(_TEMPLATES) >= 6, [p.name for p in _TEMPLATES]


@pytest.mark.parametrize("path", _TEMPLATES, ids=lambda p: p.name)
def test_every_template_carries_a_marker_naming_itself(path: Path):
    """The name is the file stem, so a marker copied into a document names the
    template `check` then reads — and a template that lost its line would make
    every document built from it read as naming a template nobody ships."""
    marker = aide.template_marker(path.read_text(encoding="utf-8"))
    assert marker is not None, f"{path.name}: no aide-template line"
    assert marker[0] == path.stem and marker[1] >= 1, marker
    assert aide.installed_template_versions()[path.stem] == marker[1]


@pytest.mark.parametrize("path", _TEMPLATES, ids=lambda p: p.name)
def test_the_marker_sits_after_the_header_comment(path: Path):
    """Four templates tell the author to delete their header comment. A marker
    inside it, or before it, would go with the comment — or, before it, would
    be read as the header by every guard that takes the leading comment."""
    text = path.read_text(encoding="utf-8")
    assert text.startswith("<!--"), path.name
    end = text.index("-->") + len("-->")
    assert text[end:].lstrip("\r\n").startswith("<!-- aide-template:"), path.name


# --------------------------------------------------------------------------- #
# what `check` reports
# --------------------------------------------------------------------------- #
def test_a_document_behind_its_template_is_a_warning_naming_the_changelog(tmp_path: Path):
    repo = _repo(tmp_path, progress_marker=_marker("progress", 1))
    warnings = _drift(repo, {"progress": 2})
    assert warnings == [w for w in warnings if w.startswith("progress.md:")]
    assert len(warnings) == 1
    assert "created from progress template 1" in warnings[0]
    assert "'progress template 2'" in warnings[0]


def test_a_current_document_is_silent(tmp_path: Path):
    repo = _repo(tmp_path, progress_marker=_marker("progress", 2))
    assert _drift(repo, {"progress": 2}) == []


def test_a_document_without_a_marker_is_silent(tmp_path: Path):
    """Every document written before the marker existed has none, and the
    engine cannot tell which template it came from."""
    repo = _repo(tmp_path)
    assert _drift(repo, {"progress": 5}) == []


def test_a_marker_below_the_title_is_not_read(tmp_path: Path):
    """An item spec quoting the line as an example, or a note about a template
    change, must not be taken for the document's own record — above the title
    is the one place the line is read, so the real marker still wins."""
    repo = _repo(tmp_path)
    ddir = repo / "docs" / "aide"
    quoted = "\n## Notes\n\n<!-- aide-template: item 1 -->\n"
    (ddir / "items" / "002-coverage.md").write_text(
        "# Item 002 — Coverage\n" + quoted, encoding="utf-8")
    assert _drift(repo, {"item": 2}) == []

    (ddir / "items" / "002-coverage.md").write_text(
        _marker("item", 2) + "# Item 002 — Coverage\n" + quoted, encoding="utf-8")
    assert _drift(repo, {"item": 2}) == []

    (ddir / "items" / "002-coverage.md").write_text(
        "# Item 002 — Coverage\n\n<!-- aide-template: item one -->\n",
        encoding="utf-8")
    assert _drift(repo, {"item": 2}) == []


def test_a_document_newer_than_the_install_is_a_warning(tmp_path: Path):
    repo = _repo(tmp_path, progress_marker=_marker("progress", 3))
    [warning] = _drift(repo, {"progress": 2})
    assert "newer than the installed 2" in warning


def test_an_unknown_template_and_an_unreadable_line_are_warnings(tmp_path: Path):
    repo = _repo(tmp_path, progress_marker=_marker("roadmapp", 1))
    (repo / "docs" / "aide" / "vision.md").write_text(
        "<!-- aide-template: vision one -->\n# Demo — Vision\n", encoding="utf-8")
    warnings = _drift(repo, {"progress": 1, "vision": 1})
    assert any(w.startswith("progress.md:") and "'roadmapp'" in w
               for w in warnings), warnings
    assert any(w.startswith("vision.md:") and "unreadable aide-template line" in w
               for w in warnings), warnings


def test_a_finished_items_spec_and_a_closed_queue_are_not_read(tmp_path: Path):
    """Item 001 is ✅, so its spec is a record; item 002 is 📋, so its spec is
    still being built against. A queue is read while any of its items is open,
    and not once every one of them is finished."""
    repo = _repo(tmp_path)
    ddir = repo / "docs" / "aide"
    (ddir / "items" / "001-bounds.md").write_text(
        _marker("item", 1) + "# Item 001 — Bounds\n", encoding="utf-8")
    (ddir / "items" / "002-coverage.md").write_text(
        _marker("item", 1) + "# Item 002 — Coverage\n", encoding="utf-8")
    (ddir / "queue" / "queue-001.md").write_text(
        _marker("queue", 1) + QUEUE, encoding="utf-8")
    (ddir / "queue" / "queue-000.md").write_text(
        _marker("queue", 1) + "# Demo — Work Queue 000\n\n### Item 001: Bounds\nx\n",
        encoding="utf-8")

    warnings = _drift(repo, {"item": 2, "queue": 2, "progress": 1})
    named = sorted(w.split(":", 1)[0] for w in warnings)
    assert named == ["items/002-coverage.md", "queue/queue-001.md"], warnings


def test_check_reports_drift_as_a_warning_and_still_exits_zero(
        tmp_path: Path, capsys, monkeypatch):
    """The whole path a consumer runs: `main`, the installed templates read from
    disk, and the exit code a warning never moves."""
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "progress.md").write_text(
        "<!-- header -->\n" + _marker("progress", 2) + "# {{project-name}}\n",
        encoding="utf-8")
    monkeypatch.setattr(aide, "_TEMPLATES_DIR", templates)
    repo = _repo(tmp_path, progress_marker=_marker("progress", 1))

    assert aide.main(["--repo", str(repo), "check"]) == 0
    out = capsys.readouterr().out
    assert "warning: progress.md: created from progress template 1" in out
    assert "aide check: OK (" in out
