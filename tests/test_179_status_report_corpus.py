"""Tests for item 179 -- the status report's Synthetic Failure Corpus section
re-keyed off the generated specification (``failure_modes.generated.json``)
and the traceability matrix (``traceability_matrix.generated.json``), instead
of the hand-typed eight-mode legend.

Covers Acceptance Criteria AC1-AC6. Each committed JSON file is read directly
with ``json.loads`` here, never through the script's own loader, so the
expected values are recomputed from the primary source rather than mirrored
from it.
"""
from __future__ import annotations

import ast
import html
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = _REPO_ROOT / "scripts" / "aide_status_report.py"
_FM_PATH = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.json"
_TM_PATH = _REPO_ROOT / "docs" / "aide" / "traceability_matrix.generated.json"
_MANIFEST_PATH = _REPO_ROOT / "tests" / "corpus" / "manifest.json"


@pytest.fixture(scope="module")
def asr():
    spec = importlib.util.spec_from_file_location("aide_status_report_179", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _real_model(asr):
    return asr.ReportModel(
        generated_at="now",
        corpus=asr.parse_corpus_manifest(_MANIFEST_PATH),
    )


def _fm_json():
    return json.loads(_FM_PATH.read_text(encoding="utf-8"))


def _tm_json():
    return json.loads(_TM_PATH.read_text(encoding="utf-8"))


# =========================================================================== #
# AC1: the legend is the specification's mode list
# =========================================================================== #


def test_ac1_legend_matches_failure_mode_spec(asr):
    fm = _fm_json()
    expected = [
        f'<li><strong>{m["id"]}</strong> — {html.escape(m["name"])} '
        f'<span class="b-pill">{html.escape(m["status_derived"])}</span></li>'
        for m in fm["modes"]
    ]
    doc = asr.render_html(_real_model(asr))
    match = re.search(r'<ul class="legend">(.*?)</ul>', doc, re.S)
    assert match is not None, "expected a <ul class=\"legend\"> block in the rendered report"
    items = re.findall(r"<li>.*?</li>", match.group(1), re.S)
    assert items == expected


# =========================================================================== #
# AC2: the coverage card counts the specification's modes
# =========================================================================== #


def test_ac2_coverage_card_counts_spec_modes(asr):
    fm = _fm_json()
    total = len(fm["modes"])
    covered = sum(1 for m in fm["modes"] if m.get("corpus_cases"))
    doc = asr.render_html(_real_model(asr))
    assert (
        f'<div class="n">{covered}/{total}</div>'
        '<div class="l">Failure modes with a committed case</div>'
    ) in doc


# =========================================================================== #
# AC3: the conformance card reads the traceability matrix
# =========================================================================== #


def test_ac3_conformance_card_reads_traceability_matrix(asr):
    tm = _tm_json()
    a = tm["conformance"]["agree_count"]
    d = tm["conformance"]["disagree_count"]
    doc = asr.render_html(_real_model(asr))
    assert (
        f'<div class="n">{a}/{a + d}</div>'
        '<div class="l">Cases whose measured firing equals the expected set</div>'
    ) in doc


# =========================================================================== #
# AC4: a title edited in a copy of the JSON changes the rendering
# =========================================================================== #


def test_ac4_edited_title_in_copy_changes_rendering(asr, tmp_path: Path):
    fm_copy = tmp_path / "failure_modes.generated.json"
    tm_copy = tmp_path / "traceability_matrix.generated.json"
    shutil.copy(_FM_PATH, fm_copy)
    shutil.copy(_TM_PATH, tm_copy)

    data = json.loads(fm_copy.read_text(encoding="utf-8"))
    for mode in data["modes"]:
        if mode["id"] == 3:
            mode["name"] = "Sentinel title 179"
    fm_copy.write_text(json.dumps(data), encoding="utf-8")

    spec = asr.load_failure_mode_spec(fm_copy, tm_copy)
    section = asr._render_corpus_section(_real_model(asr), spec)
    assert "<strong>3</strong> — Sentinel title 179 " in section


# =========================================================================== #
# AC5: no hand-typed mode title remains in the script
# =========================================================================== #


def test_ac5_no_hand_typed_mode_title_in_script(asr):
    source = _MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    fm = _fm_json()
    mode_names = [m["name"].casefold() for m in fm["modes"]]
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            folded = node.value.casefold()
            for name in mode_names:
                assert name not in folded, (
                    f"mode name {name!r} found in string constant {node.value!r}"
                )


# =========================================================================== #
# AC6: no eight-mode wording remains in the script
# =========================================================================== #


def test_ac6_no_eight_mode_wording_in_script(asr):
    source = _MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    pattern = re.compile(r"(?i)\beight\b|1/4/8")
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert not pattern.search(node.value), (
                f"eight-mode wording found in string constant {node.value!r}"
            )


# =========================================================================== #
# Named adversarial cases
# =========================================================================== #


def test_mode_count_follows_the_json(asr, tmp_path: Path):
    fm_copy = tmp_path / "failure_modes.generated.json"
    data = _fm_json()
    total = len(data["modes"])
    data["modes"] = data["modes"][:-1]
    fm_copy.write_text(json.dumps(data), encoding="utf-8")

    spec = asr.load_failure_mode_spec(fm_copy, _TM_PATH)
    section = asr._render_corpus_section(_real_model(asr), spec)
    assert f"/{total - 1}</div>" in section
    assert section.count("<li><strong>") == total - 1


def test_conformance_disagreement_shows(asr, tmp_path: Path):
    tm_copy = tmp_path / "traceability_matrix.generated.json"
    data = _tm_json()
    a = data["conformance"]["agree_count"]
    d = data["conformance"]["disagree_count"]
    data["conformance"]["agree_count"] = a - 1
    data["conformance"]["disagree_count"] = d + 1
    tm_copy.write_text(json.dumps(data), encoding="utf-8")

    spec = asr.load_failure_mode_spec(_FM_PATH, tm_copy)
    section = asr._render_corpus_section(_real_model(asr), spec)
    assert f"{a - 1}/{a + d}" in section


def test_missing_json_degrades(asr, tmp_path: Path):
    spec = asr.load_failure_mode_spec(tmp_path / "absent.json", _TM_PATH)
    assert spec is None

    section = asr._render_corpus_section(_real_model(asr), None)
    assert "clean_control" in section
    assert "python -m segfacet.failure_modes" in section


def test_legend_name_is_escaped(asr, tmp_path: Path):
    fm_copy = tmp_path / "failure_modes.generated.json"
    data = _fm_json()
    for mode in data["modes"]:
        if mode["id"] == 3:
            mode["name"] = "<b>x</b>"
    fm_copy.write_text(json.dumps(data), encoding="utf-8")

    spec = asr.load_failure_mode_spec(fm_copy, _TM_PATH)
    section = asr._render_corpus_section(_real_model(asr), spec)
    assert "&lt;b&gt;x&lt;/b&gt;" in section
    assert "<b>x</b>" not in section
