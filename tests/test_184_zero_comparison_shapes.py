"""Tests for item 184 -- widening test_155's ``_zero_comparisons`` scanner to
report three more shapes that express the same forbidden test: membership,
chained comparison, and ``bool(...)`` truthiness.

AC1-AC3 call the scanner directly on the exact snippet the spec gives.
AC4 (the live tree still reports nothing under the widened scan) is the
existing ``test_155_corpus_case_kind.py::
test_ac12_no_tree_wide_zero_comparison_of_failure_mode_remains`` -- no new
test is written for it (item 184 spec, AC4).

Imports the scanner from the module that owns it, as
``test_159_prerequisite_test_and_import_defects.py`` imports
``test_143_s_axis_correction``, rather than copying it.
"""

from __future__ import annotations

import pytest

import test_155_corpus_case_kind as t155


def test_ac1_membership_against_zero_literal_is_reported():
    snippet = "def f(case):\n    if case['failure_mode'] in (0,):\n        pass\n"
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


def test_ac2_chained_comparison_with_zero_comparison_is_reported():
    snippet = (
        "def f(case, lo):\n    if lo <= case['failure_mode'] == 0:\n        pass\n"
    )
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


def test_ac3_bool_truthiness_of_tracked_access_is_reported():
    snippet = "def f(case):\n    flag = bool(case.get('failure_mode'))\n"
    assert t155._zero_comparisons(snippet, "synthetic.py") == [("synthetic.py", 2)]


# =========================================================================== #
# Adversarial cases (Testing Strategy)
# =========================================================================== #


@pytest.mark.parametrize(
    "label,snippet,expected_count",
    [
        (
            "not-in-membership",
            "def f(case):\n    if case['failure_mode'] not in (0,):\n        pass\n",
            1,
        ),
        (
            "list-literal-membership",
            "def f(case):\n    if case['failure_mode'] in [0]:\n        pass\n",
            1,
        ),
        (
            "membership-without-zero",
            "def f(case):\n    if case['failure_mode'] in (1, 2):\n        pass\n",
            0,
        ),
        (
            "local-name-membership",
            "def f(case):\n    m = case['failure_mode']\n    if m in {0}:\n        pass\n",
            1,
        ),
        (
            "assert-exempts-new-shapes",
            "def f(case):\n    assert case['failure_mode'] in (0,)\n",
            0,
        ),
    ],
)
def test_adv_widened_shapes(label, snippet, expected_count):
    violations = t155._zero_comparisons(snippet, "synthetic.py")
    assert len(violations) == expected_count, (label, violations)
