"""Item 236 -- the status report and the repo's own documents survive
``aide progress archive``.

AC1-AC3 build two trees from the repository's own ``progress.md`` (and any
``progress/stage-N.md`` already present): the unarchived tree, every archived
section put back by the engine's ``unarchive_stage_text``, and the archived
tree, every stage ``archive_refusal`` accepts moved out by
``archive_stage_text``. They hold before and after the real archive run.
AC4-AC5 read the repository's documents directly. ``dangling-archive-link``
is the one adversarial case.

Retired by this item (2026-10-17, A5): the tests in other modules that pinned
the loop's own attestation state inside archived stage sections.
"""
from __future__ import annotations

import datetime as _dt
import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_AIDE_SCRIPT = _REPO_ROOT / ".aide" / "scripts" / "aide.py"
_DOCS = _REPO_ROOT / "docs" / "aide"
_NOW = _dt.datetime(2026, 7, 1, 12, 0, tzinfo=_dt.timezone.utc)

_spec = importlib.util.spec_from_file_location(
    "aide_status_report", _REPO_ROOT / "scripts" / "aide_status_report.py"
)
asr = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = asr
_spec.loader.exec_module(asr)  # type: ignore[union-attr]


def _aide_module():
    spec = importlib.util.spec_from_file_location("_aide_cli_236", _AIDE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _archive_files(root: Path):
    """``(N, text)`` per ``progress/stage-N.md`` under *root*, ascending N."""
    found = []
    for path in (root / "progress").glob("stage-*.md"):
        found.append((int(path.stem.split("-")[1]), path.read_text(encoding="utf-8")))
    return sorted(found)


def _model(root: Path):
    return asr.build_report_model(aide_dir=root, now=_NOW)


@pytest.fixture(scope="module")
def trees(tmp_path_factory):
    aide = _aide_module()
    text = (_DOCS / "progress.md").read_text(encoding="utf-8")
    for num, archive_text in _archive_files(_DOCS):
        text = aide.unarchive_stage_text(text, archive_text, num)
    unarchived = tmp_path_factory.mktemp("unarchived")
    (unarchived / "progress.md").write_text(text, encoding="utf-8")

    archived = tmp_path_factory.mktemp("archived")
    for _s, _e, num in sorted(aide.stage_sections(text.splitlines()),
                              key=lambda sec: int(sec[2])):
        (archived / "progress.md").write_text(text, encoding="utf-8")
        if aide.archive_refusal(archived, text.splitlines(), num, None, []) is not None:
            continue
        text, archive_text = aide.archive_stage_text(text, num)
        (archived / "progress").mkdir(exist_ok=True)
        (archived / "progress" / f"stage-{int(num)}.md").write_text(
            archive_text, encoding="utf-8")
    (archived / "progress.md").write_text(text, encoding="utf-8")

    assert _archive_files(archived), "no stage archived: AC1-AC3 would compare a tree with itself"
    return unarchived, archived


def test_ac1_archived_items_keep_their_status(trees):
    unarchived, archived = trees
    assert ({i.number: i.status for i in _model(archived).items}
            == {i.number: i.status for i in _model(unarchived).items})


def test_ac2_archiving_moves_no_item_to_another_stage(trees):
    unarchived, archived = trees
    assert ({i.number: i.stage for i in _model(archived).items}
            == {i.number: i.stage for i in _model(unarchived).items})


def test_ac3_stage_list_is_unchanged_by_archiving(trees):
    unarchived, archived = trees

    def tuples(root):
        return [(s.number, s.title, s.objectives, s.status) for s in _model(root).stages]

    assert tuples(archived) == tuples(unarchived)


def _stages_naming(item: int):
    aide = _aide_module()
    stages = set()
    lines = (_DOCS / "progress.md").read_text(encoding="utf-8").splitlines()
    for _s, _e, num in aide.stage_sections(lines):
        if item in aide.stage_item_numbers(lines, num):
            stages.add(int(num))
    for num, archive_text in _archive_files(_DOCS):
        if item in aide.stage_item_numbers(archive_text.splitlines(), str(num)):
            stages.add(num)
    return stages


def test_ac4_item_006_sits_in_one_stage():
    assert _stages_naming(6) == {0}


def test_ac5_item_204_sits_in_one_stage():
    assert _stages_naming(204) == {33}


def test_dangling_archive_link(tmp_path):
    (tmp_path / "progress.md").write_text(
        "# Progress\n\n"
        "| Stage | Title | Objectives | Status |\n"
        "|-------|-------|-----------|--------|\n"
        "| 3 | [Gone](progress/stage-3.md) | G1 | ✅ |\n",
        encoding="utf-8",
    )
    model = _model(tmp_path)
    assert [(s.number, s.title) for s in model.stages] == [("3", "Gone")]
