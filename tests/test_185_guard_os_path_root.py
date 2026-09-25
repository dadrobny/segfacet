"""Tests for item 185 -- the committed-artifact guard resolves the
``os.path.dirname(os.path.abspath(__file__))`` repo-root idiom.

``tests/committed_artifact_guard.py``'s resolver (item 127, extended by item
158) recognised a committed-path root built as a ``pathlib`` chain rooted at
``Path(__file__)``. A third spelling -- the ``os.path`` string form used by
``test_019_vertebra_orientation_curvature.py`` and three sibling modules --
still resolved to nothing and was skipped without a report. This item teaches
``_file_root_parent_count`` that ``os.path.dirname``/``os.path.abspath`` over
``__file__``, optionally wrapped in ``Path(...)``, carries a depth just like
the existing ``.parent`` chain.

Every synthetic module below goes through
``committed_artifact_guard.classify_module`` with an in-memory source string
-- never written into the real ``tests/`` tree. ``ARTIFACT`` here is the
committed path ``src/segfacet/reference/reference_default.json``,
deliberately off-allowlist, so a recognised root that resolves to it always
produces exactly one ``Violation``.
"""

from __future__ import annotations

from pathlib import Path

import committed_artifact_guard as guard

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent

ARTIFACT = "src/segfacet/reference/reference_default.json"
MODULE_PATH = "tests/test_zz_synthetic_185.py"

_JOIN = '"src" / "segfacet" / "reference" / "reference_default.json"'


def _build_module(root_lines: str) -> str:
    """One synthetic module: *root_lines* binds ``_ROOT``, then a single test
    function compares a fresh read against ``_ROOT / ... / ARTIFACT``, the
    shape the spec's Acceptance Criteria section fixes."""
    return (
        "import os\n"
        "from pathlib import Path\n"
        f"{root_lines}"
        "\n\n"
        "def test_x(tmp_path):\n"
        '    fresh = tmp_path / "fresh.json"\n'
        f"    assert fresh.read_bytes() == (_ROOT / {_JOIN}).read_bytes()\n"
    )


def _one_violation(violations, committed_path=ARTIFACT):
    assert len(violations) == 1, violations
    assert violations[0].committed_path == committed_path, violations


# =========================================================================== #
# AC1: the inline os.path repo root is resolved
# =========================================================================== #


def test_ac1_inline_os_path_repo_root_is_resolved():
    source = _build_module(
        "_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
    )
    violations = guard.classify_module(source, MODULE_PATH)
    _one_violation(violations)


# =========================================================================== #
# AC2: the live _tests_dir binding, stepped up with Path(...).parent
# =========================================================================== #


def test_ac2_live_tests_dir_stepped_up_with_parent_is_resolved():
    source = _build_module(
        "_tests_dir = os.path.dirname(os.path.abspath(__file__))\n"
        "_ROOT = Path(_tests_dir).parent\n"
    )
    violations = guard.classify_module(source, MODULE_PATH)
    _one_violation(violations)


# =========================================================================== #
# AC3: the live _tests_dir binding, stepped up with os.path.dirname
# =========================================================================== #


def test_ac3_live_tests_dir_stepped_up_with_os_path_dirname_is_resolved():
    source = _build_module(
        "_tests_dir = os.path.dirname(os.path.abspath(__file__))\n"
        "_ROOT = Path(os.path.dirname(_tests_dir))\n"
    )
    violations = guard.classify_module(source, MODULE_PATH)
    _one_violation(violations)


# =========================================================================== #
# Adversarial / named cases
# =========================================================================== #


def test_one_step_os_path_root():
    """A depth-1 os.path root (the idiom itself, with no further step up) is
    not the repo root -- a resolver that counted the idiom as the repo root
    whatever its depth would read a tests/-relative path as repo-relative."""
    source = _build_module(
        "_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))\n"
    )
    assert guard.classify_module(source, MODULE_PATH) == []


def test_dirname_off_a_non_file_base():
    """dirname steps off a base that is not __file__ must not be counted --
    a resolver that counted dirname steps without checking the chain starts
    at __file__ would report a Violation that is not real."""
    source = _build_module(
        "_ROOT = Path(os.path.dirname(os.path.dirname(os.getcwd())))\n"
    )
    assert guard.classify_module(source, MODULE_PATH) == []


def test_live_binding_alone_is_not_a_root():
    """The real source of test_019_vertebra_orientation_curvature.py, read
    from disk, records _tests_dir at depth 1 via _module_level_paths, and
    does not treat it as a resolved repo root (`known` carries no
    _tests_dir key)."""
    path = TESTS_DIR / "test_019_vertebra_orientation_curvature.py"
    source = path.read_text(encoding="utf-8")
    tree = guard.ast.parse(source)
    known, depths = guard._module_level_paths(tree)
    assert depths.get("_tests_dir") == 1
    assert "_tests_dir" not in known
