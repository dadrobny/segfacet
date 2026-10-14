"""Tests for item 225 -- three test guards that see only half of what they guard.

AC1-AC3 and the committed-artifact adversarial cases call
``committed_artifact_guard.classify_module`` on planted module sources.
AC4 (the live ``tests/`` tree is guard-clean) is the existing
``test_127_committed_artifact_tolerance.py::
test_ac15_classifier_reports_zero_violations_on_tests_tree`` -- no new test.
AC5-AC10 are regression pins on ``test_155_corpus_case_kind._zero_comparisons``
(they pass on the base). AC11-AC15 and the decision-table cases call
``test_105_golden_decision_table._unnamed_golden_readers``.
"""

from __future__ import annotations

from pathlib import Path

import committed_artifact_guard as guard
import test_105_golden_decision_table as t105
import test_155_corpus_case_kind as t155

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REF = '"src/segfacet/reference/reference_default.json"'
_REF_PATH = "src/segfacet/reference/reference_default.json"
_DIGESTS = "tests/corpus/119_pre_119_digests.json"
_HEADER = "import json\nfrom pathlib import Path\n"


def _classify(body: str):
    return guard.classify_module(_HEADER + body, "tests/test_synthetic.py")


def _one_violation(violations):
    assert len(violations) == 1
    assert violations[0].committed_path == _REF_PATH


# --------------------------------------------------------------------------- #
# Committed-artifact guard
# --------------------------------------------------------------------------- #


def test_ac1_inline_parsed_read_is_flagged():
    body = (
        "def test_x():\n"
        "    fresh = 1\n"
        f"    assert json.loads(Path({_REF}).read_text())[\"x\"] == fresh\n"
    )
    _one_violation(_classify(body))


def test_ac2_function_local_name_bound_to_parsed_read_is_flagged():
    body = (
        "def test_x():\n"
        f"    data = json.loads(Path({_REF}).read_text())\n"
        "    assert data[\"x\"] == 1\n"
    )
    _one_violation(_classify(body))


def test_ac3_module_level_name_bound_to_parsed_read_is_flagged():
    body = (
        f"DATA = json.loads(Path({_REF}).read_text())\n"
        "def test_x():\n"
        "    assert DATA[\"x\"] == 1\n"
    )
    _one_violation(_classify(body))


def test_get_chain():
    body = (
        "def test_x():\n"
        f"    assert json.loads(Path({_REF}).read_text()).get(\"x\") == 1\n"
    )
    _one_violation(_classify(body))


def test_parsed_read_bytes():
    body = (
        "def test_x():\n"
        f"    assert json.loads(Path({_REF}).read_bytes())[\"x\"] == 1\n"
    )
    _one_violation(_classify(body))


def test_module_level_raw_read():
    body = (
        f"RAW = Path({_REF}).read_bytes()\n"
        "def test_x():\n"
        "    assert RAW == b\"\"\n"
    )
    _one_violation(_classify(body))


def test_both_sides_parsed_same_path():
    read = f"json.loads(Path({_REF}).read_text())"
    body = f"def test_x():\n    assert {read}[\"a\"] == {read}[\"b\"]\n"
    assert _classify(body) == []


def test_local_rebind_shadows_module_read():
    body = (
        f"DATA = json.loads(Path({_REF}).read_text())\n"
        "def test_x():\n"
        "    DATA = {}\n"
        "    assert DATA[\"x\"] == 1\n"
    )
    assert _classify(body) == []


def test_parameter_shadows_module_read():
    body = (
        f"DATA = json.loads(Path({_REF}).read_text())\n"
        "def test_x(DATA):\n"
        "    assert DATA[\"x\"] == 1\n"
    )
    assert _classify(body) == []


def test_allowlisted_parsed_read():
    body = (
        "def test_x():\n"
        "    fresh = 1\n"
        "    assert json.loads(Path(\"tests/corpus/manifest.json\").read_text())[\"x\"] == fresh\n"
    )
    assert _classify(body) == []


def test_live_idiom_non_vacuity(monkeypatch):
    monkeypatch.setattr(
        guard,
        "ALLOWLIST",
        tuple(e for e in guard.ALLOWLIST if e.path != _DIGESTS),
    )
    violations = list(guard.iter_violations(_REPO_ROOT / "tests"))
    assert any(v.committed_path == _DIGESTS for v in violations)


# --------------------------------------------------------------------------- #
# Zero-comparison scanner (test-only pins)
# --------------------------------------------------------------------------- #


def _zero(snippet: str):
    return t155._zero_comparisons(snippet, "synthetic.py")


def test_ac5_module_level_def_default_is_reported():
    assert _zero("def g(x=(c['failure_mode'] == 0)):\n    pass\n") == [("synthetic.py", 1)]


def test_ac6_module_level_def_decorator_is_reported():
    assert _zero("@deco(c['failure_mode'] == 0)\ndef g():\n    pass\n") == [("synthetic.py", 1)]


def test_ac7_module_level_def_annotation_is_reported():
    assert _zero("def g(x: (c['failure_mode'] == 0)):\n    pass\n") == [("synthetic.py", 1)]


def test_ac8_method_default_is_reported():
    snippet = "class K:\n    def g(self, x=(c['failure_mode'] == 0)):\n        pass\n"
    assert _zero(snippet) == [("synthetic.py", 2)]


def test_ac9_method_decorator_is_reported():
    snippet = "class K:\n    @deco(c['failure_mode'] == 0)\n    def g(self):\n        pass\n"
    assert _zero(snippet) == [("synthetic.py", 2)]


def test_ac10_method_annotation_is_reported():
    snippet = "class K:\n    def g(self, x: (c['failure_mode'] == 0)):\n        pass\n"
    assert _zero(snippet) == [("synthetic.py", 2)]


# --------------------------------------------------------------------------- #
# Decision-table reverse check
# --------------------------------------------------------------------------- #

_FIXTURE = "tests/golden/x.json"
_HELPER = (
    "from pathlib import Path\n"
    "GOLDEN_PATH = Path(__file__).parent / \"golden\" / \"x.json\"\n"
)


def _row(asserted_by: str = "tests/test_901_named.py", fixture: str = _FIXTURE) -> dict:
    return {"fixture": fixture, "asserted by": asserted_by}


def _plant(tmp_path: Path, modules: dict, *, fixture_on_disk: bool = True) -> Path:
    tests = tmp_path / "tests"
    (tests / "golden").mkdir(parents=True)
    if fixture_on_disk:
        (tests / "golden" / "x.json").write_text("{}", encoding="utf-8")
    for name, source in modules.items():
        (tests / name).write_text(source, encoding="utf-8")
    return tmp_path


def test_ac11_every_reader_of_live_golden_fixture_is_named():
    text = t105._DOC_PATH.read_text(encoding="utf-8")
    section = t105._split_sections(text)["Section 1 — Committed test fixtures"]
    _, rows = t105._parse_first_pipe_table(section, where="Section 1")
    assert rows
    assert t105._unnamed_golden_readers(rows, _REPO_ROOT) == []


def test_ac12_string_constant_reader_is_reported(tmp_path):
    root = _plant(
        tmp_path,
        {
            "test_900_reader.py": (
                "from pathlib import Path\n"
                "P = Path(__file__).parent / \"golden\" / \"x.json\"\n"
            )
        },
    )
    assert t105._unnamed_golden_readers([_row()], root) == [
        (_FIXTURE, "tests/test_900_reader.py")
    ]


def test_ac13_shared_attribute_reader_is_reported(tmp_path):
    root = _plant(
        tmp_path,
        {
            "helper_mod.py": _HELPER,
            "test_902_attr.py": (
                "import helper_mod\n"
                "def test_x():\n"
                "    helper_mod.GOLDEN_PATH.read_text()\n"
            ),
        },
    )
    assert t105._unnamed_golden_readers([_row()], root) == [
        (_FIXTURE, "tests/test_902_attr.py")
    ]


def test_ac14_setattr_reader_is_reported(tmp_path):
    root = _plant(
        tmp_path,
        {
            "helper_mod.py": _HELPER,
            "test_903_setattr.py": (
                "import helper_mod\n"
                "def test_x(monkeypatch, tmp_path):\n"
                "    monkeypatch.setattr(helper_mod, \"GOLDEN_PATH\", tmp_path)\n"
            ),
        },
    )
    assert t105._unnamed_golden_readers([_row()], root) == [
        (_FIXTURE, "tests/test_903_setattr.py")
    ]


def test_ac15_docstring_only_mention_is_not_a_reader(tmp_path):
    root = _plant(
        tmp_path,
        {"test_904_doc.py": '"""Mentions x.json only here."""\n\nVALUE = 1\n'},
    )
    assert t105._unnamed_golden_readers([_row()], root) == []


def test_retired_golden_row_skipped(tmp_path):
    root = _plant(
        tmp_path,
        {"test_900_reader.py": "NEEDLE = \"x.json\"\n"},
        fixture_on_disk=False,
    )
    assert t105._unnamed_golden_readers([_row()], root) == []


def test_qualified_name_counts_as_named(tmp_path):
    root = _plant(
        tmp_path,
        {"test_900_reader.py": "NEEDLE = \"x.json\"\n"},
    )
    row = _row("tests/test_900_reader.py::test_x")
    assert t105._unnamed_golden_readers([row], root) == []


def test_unnumbered_module_not_a_reader(tmp_path):
    root = _plant(
        tmp_path,
        {
            "test_aide_x.py": "NEEDLE = \"x.json\"\n",
            "helper_mod.py": "NEEDLE = \"x.json\"\n",
        },
    )
    assert t105._unnamed_golden_readers([_row()], root) == []
