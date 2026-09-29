"""Tests for item 202 -- the generated ``docs/aide/rules.generated.md``
(``segfacet.rule_table``, and the ``question`` / ``fires_when`` / ``params``
fields on ``RuleDetector``).

One test per Acceptance Criterion (AC1-AC11) plus exactly the two named
adversarial cases, ``code-default-drift`` and
``perturbed-row-names-new-value``. Every expected value is recomputed from the
rule registry, the bundled config and ``SPECIFICATION``, never typed as a
literal.
"""

import ast
import copy
import dataclasses
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED = REPO_ROOT / "docs" / "aide" / "rules.generated.md"
COMMITTED_REL = "docs/aide/rules.generated.md"
COLUMNS = ("Rule", "Detector", "Question", "Reads", "Fires when", "Default", "Modes")


def _registered():
    """{(rule_id, detector_id): (rule, detector)} over the live registry."""
    import segfacet.heuristics  # noqa: F401  (registers the rules)
    from segfacet.heuristics.rule import iter_rules

    out = {}
    for rule in iter_rules():
        for det in rule.mode_declaration.detectors:
            out[(rule.rule_id, det.detector_id)] = (rule, det)
    assert out, "no registered detectors found"
    return out


def _parse_rows(text):
    """Rows of the single table as {(rule_id, detector_id): {column: cell}}
    plus the ordered list of keys."""
    lines = text.splitlines()
    header = next(i for i, ln in enumerate(lines) if ln.startswith("| Rule "))
    rows, keys = {}, []
    for ln in lines[header + 2:]:
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", ln)[1:-1]]
        assert len(cells) == len(COLUMNS), ln
        row = dict(zip(COLUMNS, cells))
        key = (row["Rule"].strip("`"), row["Detector"].strip("`"))
        keys.append(key)
        rows[key] = row
    assert rows, "no table rows parsed"
    return rows, keys


@pytest.fixture(scope="module")
def committed_rows():
    rows, _ = _parse_rows(COMMITTED.read_text(encoding="utf-8"))
    return rows


def _default_cell(config, rule_id, det):
    if not det.params:
        return "(none)"
    return "; ".join(
        f"`{key}` = {json.dumps(config.rule_param(rule_id, key, default=code_default))}"
        for key, code_default in det.params
    )


def _perturbable(bundled):
    """(rule_id, key) declared by a detector and numeric (non-bool) in the
    bundled config."""
    for (rule_id, _), (_, det) in sorted(_registered().items()):
        for key, _default in det.params:
            value = bundled.rule_params(rule_id).get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return rule_id, key, value
    pytest.fail("no declared param is numeric in the bundled config")


def _perturbed_config(bundled, rule_id, key, value):
    rules = copy.deepcopy(bundled.rules)
    rules[rule_id]["params"][key] = value + 1
    return dataclasses.replace(bundled, rules=rules)


def test_ac1_one_row_per_registered_detector():
    _, keys = _parse_rows(COMMITTED.read_text(encoding="utf-8"))
    expected = Counter(_registered().keys())
    assert Counter(keys) == expected


def test_ac2_committed_file_is_fresh_render():
    from segfacet.rule_table import render_markdown

    assert COMMITTED.read_bytes() == render_markdown().encode("utf-8")


def test_ac3_main_writes_the_render(tmp_path):
    from segfacet.rule_table import main, render_markdown

    p = tmp_path / "sub" / "rules.md"
    assert main(["--md", str(p)]) == 0
    assert p.read_bytes() == render_markdown().encode("utf-8")


def test_ac4_changed_config_default_makes_committed_file_stale():
    from segfacet.config import bundled_default_config
    from segfacet.rule_table import render_markdown

    bundled = bundled_default_config()
    rule_id, key, value = _perturbable(bundled)
    config = _perturbed_config(bundled, rule_id, key, value)
    assert render_markdown(config).encode("utf-8") != COMMITTED.read_bytes()


def test_ac5_default_cell_is_the_effective_default(committed_rows):
    from segfacet.config import bundled_default_config

    bundled = bundled_default_config()
    registered = _registered()
    assert set(committed_rows) == set(registered)
    for key, row in committed_rows.items():
        rule, det = registered[key]
        assert row["Default"] == _default_cell(bundled, rule.rule_id, det), key


def _rule_param_key_literals(module_source):
    keys = set()
    for node in ast.walk(ast.parse(module_source)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "rule_param"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            keys.add(node.args[1].value)
    return keys


def test_ac6_declared_keys_are_the_keys_the_rule_reads():
    import inspect

    from segfacet.heuristics.rule import iter_rules

    _registered()
    checked = 0
    for rule in iter_rules():
        module = sys.modules[type(rule).__module__]
        read = {
            k
            for k in _rule_param_key_literals(inspect.getsource(module))
            if not k.endswith("severity")
        }
        declared = {
            key
            for det in rule.mode_declaration.detectors
            for key, _ in det.params
        }
        assert declared == read, rule.rule_id
        checked += 1
    assert checked > 0


def test_ac7_modes_cell_is_the_modes_the_detector_serves(committed_rows):
    from segfacet import failure_modes

    assert committed_rows
    for (rule_id, detector_id), row in committed_rows.items():
        modes = failure_modes.modes_for_detector(rule_id, detector_id)
        expected = ", ".join(str(m) for m in modes) if modes else "none"
        assert row["Modes"] == expected, (rule_id, detector_id)


def test_ac8_reads_cell_is_the_detectors_declared_paths(committed_rows):
    registered = _registered()
    assert set(committed_rows) == set(registered)
    for key, row in committed_rows.items():
        rule, det = registered[key]
        paths = list(det.signal_paths) or [
            cp.path
            for cp in rule.mode_declaration.consumed_paths
            if cp.role == "condition-signal"
        ]
        expected = ", ".join(f"`{p}`" for p in paths) if paths else "(none declared)"
        assert row["Reads"] == expected, key


def test_ac9_question_cell_is_the_authored_question(committed_rows):
    from segfacet import failure_modes

    registered = _registered()
    assert set(committed_rows) == set(registered)
    for key, row in committed_rows.items():
        _, det = registered[key]
        assert row["Question"], key
        assert row["Question"] == failure_modes._md_escape(det.question), key


def test_ac10_fires_when_cell_is_the_authored_condition(committed_rows):
    from segfacet import failure_modes

    registered = _registered()
    assert set(committed_rows) == set(registered)
    for key, row in committed_rows.items():
        _, det = registered[key]
        assert row["Fires when"], key
        assert row["Fires when"] == failure_modes._md_escape(det.fires_when), key


def test_ac11_committed_file_is_pinned_lf():
    result = subprocess.run(
        ["git", "check-attr", "eol", "--", COMMITTED_REL],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert f"{COMMITTED_REL}: eol: lf" in result.stdout


def _default_nodes(module_source, key):
    """The ``default`` expression nodes of every ``rule_param(..., key, ...)``
    call for *key*."""
    nodes = []
    for node in ast.walk(ast.parse(module_source)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "rule_param"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == key
        ):
            kw = {k.arg: k.value for k in node.keywords}
            if "default" in kw:
                nodes.append(kw["default"])
            elif len(node.args) >= 3:
                nodes.append(node.args[2])
    return nodes


def _norm(value):
    return tuple(value) if isinstance(value, list) else value


def test_code_default_drift():
    import inspect

    checked = 0
    for (rule_id, detector_id), (rule, det) in _registered().items():
        module = sys.modules[type(rule).__module__]
        source = inspect.getsource(module)
        for key, code_default in det.params:
            nodes = _default_nodes(source, key)
            assert nodes, (rule_id, detector_id, key)
            for node in nodes:
                try:
                    actual = ast.literal_eval(node)
                except ValueError:
                    actual = eval(ast.unparse(node), vars(module))  # noqa: S307
                assert _norm(actual) == _norm(code_default), (
                    rule_id,
                    detector_id,
                    key,
                )
                checked += 1
    assert checked > 0


def test_perturbed_row_names_new_value():
    from segfacet.config import bundled_default_config
    from segfacet.rule_table import render_markdown

    bundled = bundled_default_config()
    rule_id, key, value = _perturbable(bundled)
    config = _perturbed_config(bundled, rule_id, key, value)
    rows, _ = _parse_rows(render_markdown(config))
    declaring = [
        det.detector_id
        for (rid, _), (_, det) in _registered().items()
        if rid == rule_id and any(k == key for k, _ in det.params)
    ]
    assert declaring
    needle = f"`{key}` = {json.dumps(value + 1)}"
    for detector_id in declaring:
        assert needle in rows[(rule_id, detector_id)]["Default"], detector_id
