"""Tests for item 197 -- widening test_155's ``_zero_comparisons`` scanner to
report two more shapes that express the same forbidden test: bare truthiness
of a tracked ``failure_mode`` access in a test position, and ordering against
the zero boundary.

AC1-AC7 call the scanner directly on the exact snippet the spec gives.
AC8 (the live tree reports nothing) is the existing
``test_155_corpus_case_kind.py::
test_ac12_no_tree_wide_zero_comparison_of_failure_mode_remains`` -- no new
test is written for it (item 197 spec, AC8).

Imports the scanner from the module that owns it, as
``test_184_zero_comparison_shapes.py`` does, rather than copying it.
"""

from __future__ import annotations

import pytest

import test_155_corpus_case_kind as t155


def test_ac1_if_test_truthiness_is_reported():
    snippet = "def f(case):\n    if case.get('failure_mode'):\n        pass\n"
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


def test_ac2_while_test_truthiness_is_reported():
    snippet = "def f(case):\n    while case['failure_mode']:\n        break\n"
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


def test_ac3_ternary_test_truthiness_is_reported():
    snippet = "def f(case):\n    x = 1 if case.get('failure_mode') else 2\n"
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


def test_ac4_boolop_operand_truthiness_is_reported():
    snippet = (
        "def f(case):\n"
        "    ok = case['detection'] == 'pipeline' and case.get('failure_mode')\n"
    )
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


def test_ac5_comprehension_if_truthiness_is_reported():
    snippet = "def f(cs):\n    xs = [c for c in cs if c['failure_mode']]\n"
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


def test_ac6_greater_than_zero_is_reported():
    snippet = "def f(case):\n    if case['failure_mode'] > 0:\n        pass\n"
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


def test_ac7_greater_equal_one_is_reported():
    snippet = "def f(case):\n    if case['failure_mode'] >= 1:\n        pass\n"
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


# =========================================================================== #
# Named adversarial cases (item 197 Testing Strategy)
# =========================================================================== #


@pytest.mark.parametrize(
    "snippet, expected_count",
    [
        pytest.param(
            "def f(case):\n    m = case.get('failure_mode')\n    if m:\n        pass\n",
            1,
            id="local-name-truthiness",
        ),
        pytest.param(
            "def f(case):\n    return case.get('failure_mode')\n",
            0,
            id="value-use-not-reported",
        ),
        pytest.param(
            "def f(case):\n    assert case['detection'] and case['failure_mode']\n",
            0,
            id="assert-exempts-truthiness",
        ),
        pytest.param(
            "def f(case):\n    if 0 < case['failure_mode']:\n        pass\n",
            1,
            id="mirrored-ordering",
        ),
        pytest.param(
            "def f(case):\n    if case['failure_mode'] < 1:\n        pass\n",
            1,
            id="less-than-one",
        ),
        pytest.param(
            "def f(case):\n    if case['failure_mode'] > CLEAN_CONTROL_MODE:\n        pass\n",
            1,
            id="named-sentinel-ordering",
        ),
        pytest.param(
            "def f(case):\n    if case['failure_mode'] > 1:\n        pass\n",
            0,
            id="ordering-off-boundary",
        ),
        pytest.param(
            "def f(case):\n    if 0 < case['failure_mode'] < 99:\n        pass\n",
            1,
            id="chained-ordering",
        ),
    ],
)
def test_adv_scan_reports_exact_count(snippet, expected_count):
    violations = t155._zero_comparisons(snippet, "synthetic.py")
    assert len(violations) == expected_count
