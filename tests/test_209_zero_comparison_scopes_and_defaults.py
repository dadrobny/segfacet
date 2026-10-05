"""Tests for item 209 -- test_155's ``_zero_comparisons`` scanner: nested
scopes scanned once, walrus / ``match``-guard / float-bound shapes reported,
and a zero value default not reported.

AC1-AC5 call the scanner directly on the exact snippet the spec gives.
AC6 (the live tree reports nothing) is the existing
``test_155_corpus_case_kind.py::
test_ac12_no_tree_wide_zero_comparison_of_failure_mode_remains`` -- no new
test is written for it (item 209 spec, AC6).

Imports the scanner from the module that owns it, as
``test_184_zero_comparison_shapes.py`` does, rather than copying it.
"""

from __future__ import annotations

import pytest

import test_155_corpus_case_kind as t155


def test_ac1_nested_function_violation_is_reported_once():
    snippet = "def f(c):\n    def g(d):\n        if d['failure_mode'] == 0:\n            pass\n"
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 3)]


def test_ac2_walrus_test_is_reported():
    snippet = "def f(c):\n    if (m := c['failure_mode']):\n        pass\n"
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


def test_ac3_match_guard_is_reported():
    snippet = (
        "def f(c, x):\n"
        "    match x:\n"
        "        case 1 if c['failure_mode']:\n"
        "            pass\n"
    )
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 3)]


def test_ac4_float_lower_bound_is_reported():
    snippet = "def f(c):\n    if c['failure_mode'] >= 1.0:\n        pass\n"
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


def test_ac5_zero_value_default_is_not_reported():
    snippet = "def f(c):\n    x = c.get('failure_mode') or 0\n"
    assert t155._zero_comparisons(snippet, "synthetic.py") == []


@pytest.mark.parametrize(
    "snippet, expected",
    [
        pytest.param(
            "def f(c):\n    m = c['failure_mode']\n    def g():\n        if m == 0:\n            pass\n",
            [("synthetic.py", 4)],
            id="closure-name",
        ),
        pytest.param(
            "def f(c):\n    class K:\n        def g(self, d):\n"
            "            if d['failure_mode'] == 0:\n                pass\n",
            [("synthetic.py", 4)],
            id="method-in-nested-class",
        ),
        pytest.param(
            "def f(c):\n    if (m := c['failure_mode']) == 0:\n        pass\n",
            [("synthetic.py", 2)],
            id="walrus-compare",
        ),
        pytest.param(
            "def f(c):\n    x = c.get('failure_mode') or None\n",
            [("synthetic.py", 2)],
            id="or-none-default",
        ),
        pytest.param(
            "def f(c):\n    x = c.get('failure_mode') or CLEAN_CONTROL_MODE\n",
            [],
            id="or-named-sentinel-default",
        ),
        pytest.param(
            "def f(c, o):\n    x = c.get('failure_mode') or o or 0\n",
            [("synthetic.py", 2)],
            id="or-not-second-to-last",
        ),
    ],
)
def test_adversarial_cases(snippet, expected):
    assert t155._zero_comparisons(snippet, "synthetic.py") == expected


@pytest.mark.parametrize(
    "snippet",
    [
        pytest.param(
            "def f(c):\n    if (c.get('failure_mode') or 0) == 0:\n        pass\n",
            id="eq-operand",
        ),
        pytest.param(
            "def f(c):\n    if (c.get('failure_mode') or 0) > 0:\n        pass\n",
            id="gt-operand",
        ),
        pytest.param(
            "def f(c):\n    if not (c['failure_mode'] or 0):\n        pass\n",
            id="not-operand",
        ),
        pytest.param(
            "def f(c):\n    if bool(c['failure_mode'] or 0):\n        pass\n",
            id="bool-operand",
        ),
    ],
)
def test_review_zero_default_in_operand_position_is_reported(snippet):
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


@pytest.mark.parametrize(
    "snippet",
    [
        pytest.param(
            "def f(c):\n    def g(x=(c['failure_mode'] == 0)): pass\n",
            id="argument-default",
        ),
        pytest.param(
            "def f(c):\n    @deco(c['failure_mode'] == 0)\n    def g(): pass\n",
            id="decorator",
        ),
        pytest.param(
            "def f(c):\n    def g(x: c['failure_mode'] == 0 = 1): pass\n",
            id="annotation",
        ),
    ],
)
def test_review_nested_def_header_is_scanned(snippet):
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]
