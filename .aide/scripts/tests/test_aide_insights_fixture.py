"""Tests for the live-inbox fixture lint — conventions.md §6, issue #295.

The recorded defect (issue #276): merged tests read `docs/aide/insights.md`
itself to assert properties of specific ticked entries, so a measured
`insights archive` turned six of them red, and a test that pinned an entry's
checkbox as unticked blocked every merge the moment triage ticked it. The lint
reports a path to the live inbox rooted at the repository, and stays quiet on
the same path built under `tmp_path` — which is the fix.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_insights_fixture", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


def _repo(tmp_path: Path, docs_dir: str = "docs/aide") -> Path:
    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    (repo / "aide.toml").write_text(
        f'[project]\nname = "Demo"\ntests_dir = "tests"\ndocs_dir = "{docs_dir}"\n',
        encoding="utf-8")
    return repo


def _warn(repo: Path, source: str):
    (repo / "tests" / "test_thing.py").write_text(source, encoding="utf-8")
    return aide.insights_fixture_test_warnings(repo, aide.load_config(repo))


ROOT = "ROOT = Path(__file__).resolve().parents[1]\n"


@pytest.mark.parametrize("source", [
    ROOT + 'INBOX = ROOT / "docs" / "aide" / "insights.md"\n',
    ROOT + 'text = (ROOT / "docs/aide/insights.md").read_text()\n',
    ROOT + 'text = (ROOT / r"docs\\aide\\insights.md").read_text()\n',
    ROOT + 'text = (ROOT / "docs\\\\aide" / "insights.md").read_text()\n',
    ROOT + 'DOCS = ROOT / "docs" / "aide"\nINBOX = DOCS / "insights.md"\n',
    # Written in the other order: the bindings are resolved to a fixpoint.
    'def inbox():\n    return DOCS / "insights.md"\n'
    'DOCS = ROOT / "docs/aide"\n' + ROOT,
    ROOT + 'p = os.path.join(ROOT, "docs", "aide", "insights.md")\n',
    ROOT + 'p = ROOT.joinpath("docs", "aide", "insights.md")\n',
    'p = Path.cwd() / "docs" / "aide" / "insights.md"\n',
    'text = Path("docs/aide/insights.md").read_text()\n',
    'with open("docs/aide/insights.md") as f:\n    pass\n',
], ids=["pieces", "one-literal", "raw-backslash", "escaped-backslash",
        "through-a-name", "bound-later", "os-path-join", "joinpath", "cwd",
        "relative-literal", "open"])
def test_a_repo_rooted_read_of_the_inbox_is_reported(tmp_path: Path, source: str):
    warnings = _warn(_repo(tmp_path), source)
    assert len(warnings) == 1
    assert warnings[0].startswith("tests/test_thing.py:")
    assert "conventions.md §6" in warnings[0]


@pytest.mark.parametrize("source", [
    # The fix itself: the inbox built where the test owns it.
    'def test_x(tmp_path):\n'
    '    inbox = tmp_path / "docs" / "aide" / "insights.md"\n',
    'def _repo(tmp_path):\n    repo = tmp_path / "repo"\n'
    '    (repo / "docs" / "aide" / "insights.md").write_text("")\n',
    # A helper argument is indistinguishable from tmp_path, so it is left alone.
    'def helper(repo):\n    return repo / "docs/aide/insights.md"\n',
    # A string no path call receives: a docstring, an assertion message.
    '"""Reads nothing from docs/aide/insights.md."""\n'
    'def test_x():\n    assert True, "see docs/aide/insights.md"\n',
    # Another document under docs_dir, and another inbox elsewhere.
    ROOT + 'P = ROOT / "docs" / "aide" / "progress.md"\n',
    ROOT + 'P = ROOT / "fixtures" / "insights.md"\n',
], ids=["tmp_path", "tmp_path-helper", "argument", "prose", "other-document",
        "other-directory"])
def test_what_is_not_a_repo_rooted_read_is_not_reported(tmp_path: Path, source: str):
    assert _warn(_repo(tmp_path), source) == []


_MODULE_ROOT = ("from pathlib import Path\n"
                "ROOT = Path(__file__).resolve().parents[1]\n"
                "TARGET = ROOT / 'core' / 'scripts' / 'aide.py'\n")


@pytest.mark.parametrize("source", [
    # A local assignment shadows the module's ROOT for the whole function.
    _MODULE_ROOT + "\ndef test_builds_its_own_inbox(tmp_path):\n"
    "    ROOT = tmp_path\n"
    "    inbox = ROOT / 'docs' / 'aide' / 'insights.md'\n",
    # So does a parameter of the same name.
    _MODULE_ROOT + "\ndef helper(ROOT):\n"
    "    return ROOT / 'docs' / 'aide' / 'insights.md'\n",
    # A nested function inherits its enclosing function's shadow.
    _MODULE_ROOT + "\ndef test_x(tmp_path):\n"
    "    ROOT = tmp_path\n"
    "    def inbox():\n"
    "        return ROOT / 'docs' / 'aide' / 'insights.md'\n",
], ids=["local-assignment", "parameter", "nested-inherits-shadow"])
def test_a_function_that_shadows_the_module_root_is_not_reported(
        tmp_path: Path, source: str):
    assert _warn(_repo(tmp_path), source) == []


@pytest.mark.parametrize("source, line", [
    (_MODULE_ROOT + "\ndef test_reads_the_live_inbox(tmp_path):\n"
     "    other = tmp_path\n"
     "    inbox = ROOT / 'docs' / 'aide' / 'insights.md'\n", 7),
    (_MODULE_ROOT + "\ndef test_x(tmp_path):\n"
     "    def inbox():\n"
     "        return ROOT / 'docs' / 'aide' / 'insights.md'\n", 7),
], ids=["module-name-unshadowed", "nested-reaches-module"])
def test_a_function_using_the_module_root_is_still_reported(
        tmp_path: Path, source: str, line: int):
    warnings = _warn(_repo(tmp_path), source)
    assert len(warnings) == 1 and warnings[0].startswith(f"tests/test_thing.py:{line}:")


_READ = "    inbox = ROOT / 'docs' / 'aide' / 'insights.md'\n"


@pytest.mark.parametrize("source", [
    # A comprehension's target is local to the comprehension: it must not
    # shadow the module's ROOT for the function around it.
    _MODULE_ROOT + "\ndef test_x(tmp_path):\n" + _READ +
    "    names = [str(ROOT) for ROOT in ['a', 'b']]\n",
    _MODULE_ROOT + "\ndef test_x(tmp_path):\n" + _READ +
    "    names = list(str(ROOT) for ROOT in ['a', 'b'])\n",
], ids=["listcomp-target", "genexp-target"])
def test_a_comprehension_target_does_not_shadow_the_enclosing_scope(
        tmp_path: Path, source: str):
    warnings = _warn(_repo(tmp_path), source)
    assert len(warnings) == 1
    assert warnings[0].startswith("tests/test_thing.py:6:")


def test_a_walrus_inside_a_comprehension_shadows_in_the_enclosing_function(
        tmp_path: Path):
    """A walrus in a comprehension binds in the function around it, as
    Python does — so it shadows the module's ROOT there."""
    source = (_MODULE_ROOT + "\ndef test_x(tmp_path):\n"
              "    found = [(ROOT := tmp_path) for _ in [0]]\n" + _READ)
    assert _warn(_repo(tmp_path), source) == []


def test_a_read_inside_a_comprehension_whose_target_shadows_root_is_not_reported(
        tmp_path: Path):
    source = (_MODULE_ROOT + "\ndef test_x(tmp_path):\n"
              "    inboxes = [ROOT / 'docs' / 'aide' / 'insights.md'\n"
              "               for ROOT in [tmp_path]]\n")
    assert _warn(_repo(tmp_path), source) == []


@pytest.mark.skipif(sys.version_info < (3, 10), reason="match needs Python 3.10")
@pytest.mark.parametrize("pattern", ["[ROOT]", "[*ROOT]", "{'k': 1, **ROOT}",
                                     "ROOT"])
def test_a_match_capture_shadows_the_module_root(tmp_path: Path, pattern: str):
    # Built as a string so this module still parses on Python 3.9.
    source = (_MODULE_ROOT + "\ndef helper(value):\n"
              "    match value:\n"
              f"        case {pattern}:\n"
              "            return ROOT / 'docs' / 'aide' / 'insights.md'\n")
    assert _warn(_repo(tmp_path), source) == []


def test_the_configured_docs_dir_is_the_one_read(tmp_path: Path):
    repo = _repo(tmp_path, docs_dir="documentation/loop")
    assert _warn(repo, ROOT + 'P = ROOT / "docs" / "aide" / "insights.md"\n') == []
    assert len(_warn(repo, ROOT + 'P = ROOT / "documentation" / "loop" / '
                              '"insights.md"\n')) == 1


def test_one_warning_per_file_on_the_first_read(tmp_path: Path):
    warnings = _warn(_repo(tmp_path), ROOT + "\n"
                     'A = ROOT / "docs/aide/insights.md"\n'
                     'B = ROOT / "docs/aide/insights.md"\n')
    assert len(warnings) == 1 and warnings[0].startswith("tests/test_thing.py:3:")


def test_an_unparseable_file_does_not_crash_the_check(tmp_path: Path):
    assert _warn(_repo(tmp_path), "def broken(:\n") == []


def test_reaches_run_checks(tmp_path: Path):
    """No docs_dir at all: the test-hygiene lints still run."""
    repo = _repo(tmp_path)
    (repo / "tests" / "test_thing.py").write_text(
        ROOT + 'INBOX = ROOT / "docs" / "aide" / "insights.md"\n', encoding="utf-8")
    errors, warnings = aide.run_checks(repo, aide.load_config(repo))
    assert errors == []
    assert [w for w in warnings if "live docs/aide/insights.md" in w]
