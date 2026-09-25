"""Tests for item 155 -- a corpus case is a clean control or a condition
case, never ``failure_mode == 0`` alone.

Covers Acceptance Criteria AC1-AC8 and AC11-AC19 per the item spec's Testing
Strategy, one focused test per AC. AC9/AC10 (byte-identical regeneration of
each manifest) are already met by the existing
``test_040::test_ac16_regeneration_is_byte_identical_across_runs_and_vs_committed``
and
``test_058::test_ac19_regeneration_is_byte_identical_across_runs_and_vs_committed``
-- this module does not duplicate them.

AC12/AC13 pin one scanner, ``_zero_comparisons``, written once here per the
spec's Testing Strategy pseudocode: it walks the module body and every
function body of a parsed source file separately, flags any ``Eq``/``NotEq``/
``Is``/``IsNot`` comparison or ``not`` test whose operand is a manifest-case
``failure_mode`` access (``x["failure_mode"]``, ``x.get("failure_mode")``, or
a local name bound from either in the same scope) against the literal ``0``
or a ``CLEAN_CONTROL_MODE``/``_CLEAN_MODE_ID`` name, exempting anything
inside an ``assert`` and the body of ``case_kind`` itself (the one place
literally required to make that comparison). Item 184 widened the scan to
report three more shapes expressing the same test: membership against a
zero-sentinel-containing ``Tuple``/``Set``/``List`` literal (``in``/``not
in``), a zero comparison inside a chained comparison
(``lo <= x["failure_mode"] == 0``), and ``bool(...)`` truthiness of a
tracked access.

AC14/AC15 build their probes from the *committed* clean-control geometric
case, selected by ``kind == "clean_control"`` (never by ``case_id``, which
item 157 renames) -- so, like AC7/AC8, they read ``case["kind"]`` and fail
loudly, not silently, until the manifest is regenerated with the field.
"""

from __future__ import annotations

import ast
import copy
import shutil
from pathlib import Path

import pytest

from run_process import run_utf8

from segfacet import failure_modes
from segfacet import traceability as traceability_module
from segfacet.synth import corpus as corpus_module
from segfacet.synth import intensity as intensity_module
from segfacet.synth.perturbation import (
    CASE_KIND_CLEAN_CONTROL,
    CASE_KIND_CONDITION,
    CASE_KIND_FAILURE,
    CASE_KINDS,
    case_kind,
    corpus_case_kind,
)
from segfacet.synth.regression import verify_case

_REPO_ROOT = Path(__file__).resolve().parent.parent
_GEOMETRIC_MANIFEST_PATH = _REPO_ROOT / "tests" / "corpus" / "manifest.json"
_INTENSITY_MANIFEST_PATH = _REPO_ROOT / "tests" / "corpus" / "intensity" / "manifest.json"


# =========================================================================== #
# AC1-AC3: case_kind and the closed vocabulary
# =========================================================================== #


def test_ac1_case_kind_derives_clean_control():
    assert case_kind(0, "") == "clean_control"


def test_ac1_case_kind_derives_condition():
    assert case_kind(0, "fov_truncation") == "condition"


@pytest.mark.parametrize("mode_id", sorted(failure_modes.SPECIFICATION))
def test_ac1_case_kind_derives_failure_for_every_specification_mode(mode_id):
    assert case_kind(mode_id, "") == "failure"


@pytest.mark.parametrize("mode_id", sorted(failure_modes.SPECIFICATION))
def test_ac2_case_kind_refuses_mode_with_condition(mode_id):
    with pytest.raises(ValueError):
        case_kind(mode_id, "fov_truncation")


def test_ac3_case_kinds_vocabulary_is_closed():
    from segfacet.synth import perturbation as perturbation_module

    assert perturbation_module.CASE_KINDS == frozenset(
        {"clean_control", "condition", "failure"}
    )


# =========================================================================== #
# AC4-AC6: corpus_case_kind
# =========================================================================== #


@pytest.mark.parametrize("kind", sorted(CASE_KINDS))
def test_ac4_corpus_case_kind_returns_the_recorded_kind(kind):
    assert corpus_case_kind({"kind": kind}) == kind


def test_ac5_corpus_case_kind_refuses_a_case_with_no_kind():
    with pytest.raises(ValueError):
        corpus_case_kind({"failure_mode": 0, "condition": ""})


def test_ac6_corpus_case_kind_refuses_an_unknown_kind():
    with pytest.raises(ValueError):
        corpus_case_kind({"kind": "clean"})


# =========================================================================== #
# AC7/AC8: every committed manifest case records its derived kind
# =========================================================================== #


def test_ac7_every_geometric_manifest_case_records_its_derived_kind():
    manifest = corpus_module.load_manifest()
    cases = manifest["cases"]
    assert cases, "expected a non-empty geometric manifest"
    for case in cases:
        assert case["kind"] == case_kind(case["failure_mode"], case["condition"]), (
            case["case_id"]
        )


def test_ac8_every_intensity_manifest_case_records_its_derived_kind():
    manifest = intensity_module.load_intensity_manifest()
    cases = manifest["cases"]
    assert cases, "expected a non-empty intensity manifest"
    for case in cases:
        assert case["kind"] == case_kind(
            case["failure_mode"], case.get("condition", "")
        ), case["case_id"]


# AC9/AC10 are met by test_040::test_ac16_regeneration_is_byte_identical_...
# and test_058::test_ac19_regeneration_is_byte_identical_..., not duplicated
# here.


# =========================================================================== #
# AC11: both manifests stay LF-pinned
# =========================================================================== #


@pytest.mark.parametrize(
    "rel_path",
    ["tests/corpus/manifest.json", "tests/corpus/intensity/manifest.json"],
)
def test_ac11_manifest_is_lf_pinned_in_gitattributes(rel_path):
    if shutil.which("git") is None:
        pytest.skip("git not on PATH")
    result = run_utf8(["git", "check-attr", "eol", "--", rel_path], cwd=_REPO_ROOT)
    assert result.returncode == 0, result.stderr
    output = result.stdout
    assert output.strip(), "git check-attr produced no output"
    assert f"{rel_path}: eol: lf" in output, output


# =========================================================================== #
# AC12/AC13: the tree-wide zero-comparison scan
# =========================================================================== #

_ZERO_SENTINEL_NAMES = frozenset({"CLEAN_CONTROL_MODE", "_CLEAN_MODE_ID"})
_EXEMPT_FILE = "src/segfacet/synth/perturbation.py"
_EXEMPT_FUNCTION = "case_kind"


def _is_failure_mode_access(node: ast.AST) -> bool:
    if isinstance(node, ast.Subscript):
        key = node.slice
        if isinstance(key, ast.Index):  # pragma: no cover -- py<3.9 shim
            key = key.value
        return isinstance(key, ast.Constant) and key.value == "failure_mode"
    if isinstance(node, ast.Call):
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "failure_mode"
        ):
            return True
    return False


def _is_zero_sentinel(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and node.value == 0 and not isinstance(
        node.value, bool
    ):
        return True
    if isinstance(node, ast.Name) and node.id in _ZERO_SENTINEL_NAMES:
        return True
    if isinstance(node, ast.Attribute) and node.attr in _ZERO_SENTINEL_NAMES:
        return True
    return False


def _zero_comparisons(source: str, filename: str) -> list:
    """AC12/AC13: every forbidden zero-comparison of a manifest case's
    ``failure_mode``, scanning the module body and each function body as its
    own scope. See the module docstring for the exact shape matched. Item 184
    widened the match to also report membership (``in``/``not in`` a
    zero-sentinel-containing ``Tuple``/``Set``/``List``), a zero comparison
    inside a chained comparison, and ``bool(...)`` truthiness of a tracked
    access."""
    tree = ast.parse(source, filename=filename)

    exempt_test_ids = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            for sub in ast.walk(node.test):
                exempt_test_ids.add(id(sub))

    violations = []

    def scan_scope(stmts):
        local_names = set()
        for stmt in stmts:
            for node in ast.walk(stmt):
                if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                    if _is_failure_mode_access(node.value):
                        targets = (
                            node.targets if isinstance(node, ast.Assign) else [node.target]
                        )
                        for target in targets:
                            if isinstance(target, ast.Name):
                                local_names.add(target.id)

        def is_tracked(node: ast.AST) -> bool:
            return _is_failure_mode_access(node) or (
                isinstance(node, ast.Name) and node.id in local_names
            )

        for stmt in stmts:
            for node in ast.walk(stmt):
                if id(node) in exempt_test_ids:
                    continue
                if isinstance(node, ast.Compare):
                    operands = [node.left] + list(node.comparators)
                    matched = False
                    for i, op in enumerate(node.ops):
                        left, right = operands[i], operands[i + 1]
                        if isinstance(op, (ast.Eq, ast.NotEq, ast.Is, ast.IsNot)):
                            if (is_tracked(left) and _is_zero_sentinel(right)) or (
                                is_tracked(right) and _is_zero_sentinel(left)
                            ):
                                matched = True
                        elif isinstance(op, (ast.In, ast.NotIn)):
                            if is_tracked(left) and isinstance(
                                right, (ast.Tuple, ast.Set, ast.List)
                            ):
                                if any(_is_zero_sentinel(elt) for elt in right.elts):
                                    matched = True
                    if matched:
                        violations.append((filename, node.lineno))
                elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                    if is_tracked(node.operand):
                        violations.append((filename, node.lineno))
                elif isinstance(node, ast.Call):
                    func = node.func
                    if (
                        isinstance(func, ast.Name)
                        and func.id == "bool"
                        and len(node.args) == 1
                        and is_tracked(node.args[0])
                    ):
                        violations.append((filename, node.lineno))

    module_level = [
        stmt
        for stmt in tree.body
        if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    scan_scope(module_level)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if filename == _EXEMPT_FILE and node.name == _EXEMPT_FUNCTION:
                continue
            scan_scope(node.body)

    return violations


def _iter_scanned_files():
    for root_name in ("src/segfacet", "tests"):
        root = _REPO_ROOT / root_name
        for path in sorted(root.rglob("*.py")):
            yield path.relative_to(_REPO_ROOT).as_posix()


def test_ac12_no_tree_wide_zero_comparison_of_failure_mode_remains():
    violations = []
    for rel_path in _iter_scanned_files():
        source = (_REPO_ROOT / rel_path).read_text(encoding="utf-8")
        violations.extend(_zero_comparisons(source, rel_path))
    assert violations == []


@pytest.mark.parametrize(
    "snippet,expected_count",
    [
        (
            "def f(case, cs, c, mode):\n"
            "    if case['failure_mode'] != 0:\n"
            "        pass\n",
            1,
        ),
        (
            "def f(case, cs, c, mode):\n"
            "    xs = [c for c in cs if c.get('failure_mode') == 0]\n",
            1,
        ),
        (
            "def f(case, cs, c, mode):\n"
            "    m = case.get('failure_mode')\n"
            "    if m == 0:\n"
            "        pass\n",
            1,
        ),
        (
            "def f(case, cs, c, mode):\n"
            "    if not case['failure_mode']:\n"
            "        pass\n",
            1,
        ),
        (
            "def f(case, cs, c, mode):\n"
            "    if case['failure_mode'] == CLEAN_CONTROL_MODE:\n"
            "        pass\n",
            1,
        ),
        (
            "def f(case, cs, c, mode):\n"
            "    assert case['failure_mode'] == 0\n",
            0,
        ),
        (
            "def f(case, cs, c, mode):\n"
            "    if c.get('failure_mode') == mode:\n"
            "        pass\n",
            0,
        ),
    ],
)
def test_ac13_scan_detects_each_forbidden_shape(snippet, expected_count):
    violations = _zero_comparisons(snippet, "synthetic.py")
    assert len(violations) == expected_count, violations


def test_ac13_scan_exempts_case_kind_body_in_perturbation_module():
    # The one place the comparison is required: case_kind's own body,
    # identified by file path + function name, not merely by name alone.
    # Dict-style access, since that is the only shape _is_failure_mode_access
    # recognises (A6) -- a bare scalar comparison is never tracked, exempt or
    # not, so it cannot demonstrate the exemption.
    snippet = (
        "def case_kind(case):\n"
        "    if case['failure_mode'] != 0:\n"
        "        raise ValueError('no')\n"
        "    return 'clean_control'\n"
    )
    assert _zero_comparisons(snippet, _EXEMPT_FILE) == []
    # The exemption is keyed on the file path: the identical body elsewhere
    # is still reported.
    assert _zero_comparisons(snippet, "src/segfacet/synth/other.py") != []


# =========================================================================== #
# AC14-AC19: verify_case / specification_conflicts / _build_conformance
# dispatch on kind, and refuse a case with none
# =========================================================================== #


def _committed_clean_control_case() -> dict:
    manifest = corpus_module.load_manifest()
    candidates = [c for c in manifest["cases"] if c["kind"] == CASE_KIND_CLEAN_CONTROL]
    assert len(candidates) == 1, candidates
    return candidates[0]


def _ac14_condition_probe() -> dict:
    probe = copy.deepcopy(_committed_clean_control_case())
    probe["kind"] = CASE_KIND_CONDITION
    probe["condition"] = "fov_truncation"
    probe["expected_rule_ids"] = ["border"]
    assert probe["failure_mode"] == 0
    assert probe["expected_verdict"] == "pass"
    return probe


def _ac15_no_kind_probe() -> dict:
    probe = copy.deepcopy(_committed_clean_control_case())
    del probe["kind"]
    return probe


def test_ac14_verify_case_classifies_condition_case_by_kind():
    probe = _ac14_condition_probe()
    assert verify_case(probe) is False


def test_ac14_verify_case_follows_kind_over_raw_fields():
    # Decisions log: verify_case dispatches on corpus_case_kind(case) -- the
    # recorded "kind" field, read verbatim -- as the first thing it does with
    # the case, never re-derived from failure_mode/condition. A probe that
    # lies about kind while leaving the real injected defect (failure_mode,
    # expected_rule_ids, expected_verdict) untouched shows the dispatch
    # follows the lie: labelled "clean_control", it expects no findings from
    # a case that genuinely carries a designated, firing rule, so it fails.
    manifest = corpus_module.load_manifest()
    failure_cases = [c for c in manifest["cases"] if c["kind"] == CASE_KIND_FAILURE]
    assert failure_cases, "expected at least one failure case in the geometric manifest"
    probe = copy.deepcopy(failure_cases[0])
    assert probe["kind"] != CASE_KIND_CLEAN_CONTROL
    probe["kind"] = CASE_KIND_CLEAN_CONTROL
    assert verify_case(probe) is False


def test_ac15_verify_case_refuses_a_case_with_no_kind():
    probe = _ac15_no_kind_probe()
    with pytest.raises(ValueError):
        verify_case(probe)


def test_ac16_specification_check_classifies_condition_case_by_kind(monkeypatch):
    probe = _ac14_condition_probe()
    monkeypatch.setattr(
        corpus_module, "load_manifest", lambda *a, **k: {"cases": [probe]}
    )
    conflicts = failure_modes.specification_conflicts()
    assert any(
        probe["case_id"] in msg and "fov_truncation" in msg for msg in conflicts
    ), conflicts


def test_ac17_specification_check_refuses_a_case_with_no_kind(monkeypatch):
    probe = _ac15_no_kind_probe()
    monkeypatch.setattr(
        corpus_module, "load_manifest", lambda *a, **k: {"cases": [probe]}
    )
    with pytest.raises(ValueError):
        failure_modes.specification_conflicts()


def test_ac18_conformance_report_classifies_condition_case_by_kind(monkeypatch):
    probe = _ac14_condition_probe()
    monkeypatch.setattr(
        corpus_module, "load_manifest", lambda *a, **k: {"cases": [probe]}
    )
    report = traceability_module._build_conformance(failure_modes)
    key = ("geometric", probe["case_id"])
    matches = [c for c in report.cases if (c.corpus, c.case_id) == key]
    assert len(matches) == 1, report.cases
    conformance_case = matches[0]
    assert conformance_case.expected_source == "unspecified"
    assert conformance_case.agrees is False
    assert key in report.unspecified_cases


def test_ac19_conformance_report_refuses_a_case_with_no_kind(monkeypatch):
    probe = _ac15_no_kind_probe()
    monkeypatch.setattr(
        corpus_module, "load_manifest", lambda *a, **k: {"cases": [probe]}
    )
    with pytest.raises(ValueError):
        traceability_module._build_conformance(failure_modes)


# =========================================================================== #
# Adversarial / edge cases
# =========================================================================== #


def test_adv_case_kind_does_not_validate_condition_ids():
    # case_kind's job is only the discriminator; an unknown condition id is
    # not its concern (that's _condition_case_conflicts').
    assert case_kind(0, "not_a_real_condition_id") == "condition"


def test_adv_corpus_case_kind_none_kind_raises():
    with pytest.raises(ValueError):
        corpus_case_kind({"kind": None})


def test_adv_corpus_case_kind_does_not_mutate_its_input():
    case = {"kind": "clean_control", "case_id": "probe"}
    original = copy.deepcopy(case)
    corpus_case_kind(case)
    assert case == original
