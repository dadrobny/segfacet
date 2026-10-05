"""The Windows CI leg runs a pinned OS-sensitive subset (item 213).

Covers AC1, AC2, AC5-AC8 (AC3, AC4 and AC9 were withdrawn by the queue-028
spec review). The module parses the committed ``.github/workflows/ci.yml``
and every ``tests/test_*.py`` source; it spawns nothing.

The rule. A test module is OS-sensitive, and so runs on ``windows-latest``,
when a walk of its ``ast`` tree finds at least one of five signals:

1. it spawns a subprocess (``subprocess`` / ``run_process`` imports,
   ``sys.executable``);
2. it invokes the ``segfacet`` CLI (``segfacet.cli`` imports or target strings);
3. it reads bytes or newlines (``.read_bytes``, a ``newline=`` keyword, a
   ``.gitattributes`` string, the session fixtures that read committed bytes);
4. it handles path text (``.as_posix``, ``os.sep``, ``PureWindowsPath`` ...);
5. it loads the AIDE engine in-process (the ``aide_check_result`` fixture).

Floating-point behaviour is deliberately **not** a signal: a machine or OS
float difference is absorbed by a tolerance, and a fresh-vs-committed
comparison already has one through
``segfacet.synth.golden.assert_matches_committed_artifact``, enforced over
every ``tests/*.py`` by
``test_127_committed_artifact_tolerance.py::test_ac15_classifier_reports_zero_violations_on_tests_tree``.

``WINDOWS_EXTRA`` holds the OS-sensitive modules the signals cannot see, one
reason per entry. ``ci.yml``'s ``jobs.test.env.WINDOWS_TESTS`` must equal the
classifier's set joined with these keys.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"
CI_YML_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"

# Module -> why no signal sees it.
WINDOWS_EXTRA: dict[str, str] = {
    "tests/test_086_datasets.py": (
        "compares dataset-descriptor path text (descriptor_dir == "
        "str(tmp_path.resolve())), calls is_absolute() on a POSIX-rooted "
        "Path, and writes str(tmp_path) into descriptor YAML"
    ),
}

EXPECTED_TEST_STEP_RUN = (
    "python -m pytest -n 4 --durations=30 "
    "${{ runner.os == 'Windows' && env.WINDOWS_TESTS || '' }}"
)


# =========================================================================== #
# The classifier
# =========================================================================== #

_SUBPROCESS_MODULES = ("subprocess", "run_process")
_CLI_MODULE = "segfacet.cli"
_ARG_SIGNALS = {
    "regenerated_failure_modes": "bytes",
    "regenerated_traceability": "bytes",
    "aide_check_result": "engine",
}


def _is_module(name: str | None, target: str) -> bool:
    return name is not None and (name == target or name.startswith(target + "."))


def _signals(source: str) -> set[str]:
    """Names of the OS-sensitivity signals found by walking ``source``'s AST."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(_is_module(alias.name, m) for m in _SUBPROCESS_MODULES):
                    found.add("subprocess")
                if _is_module(alias.name, _CLI_MODULE):
                    found.add("cli")
        elif isinstance(node, ast.ImportFrom):
            if any(_is_module(node.module, m) for m in _SUBPROCESS_MODULES):
                found.add("subprocess")
            if _is_module(node.module, _CLI_MODULE) or (
                node.module == "segfacet" and any(a.name == "cli" for a in node.names)
            ):
                found.add("cli")
        elif isinstance(node, ast.Attribute):
            base = node.value
            if node.attr == "executable" and isinstance(base, ast.Name) and base.id == "sys":
                found.add("subprocess")
            elif node.attr == "read_bytes":
                found.add("bytes")
            elif node.attr == "as_posix":
                found.add("path")
            elif node.attr == "sep" and (
                (isinstance(base, ast.Name) and base.id == "os")
                or (
                    isinstance(base, ast.Attribute)
                    and base.attr == "path"
                    and isinstance(base.value, ast.Name)
                    and base.value.id == "os"
                )
            ):
                found.add("path")
        elif isinstance(node, ast.Name):
            if node.id in ("PureWindowsPath", "PurePosixPath"):
                found.add("path")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.startswith(_CLI_MODULE):
                found.add("cli")
            if ".gitattributes" in node.value:
                found.add("bytes")
        elif isinstance(node, ast.keyword):
            if node.arg == "newline":
                found.add("bytes")
        elif isinstance(node, ast.arg):
            if node.arg in _ARG_SIGNALS:
                found.add(_ARG_SIGNALS[node.arg])
    return found


def _expected() -> set[str]:
    flagged = {
        f"tests/{p.name}"
        for p in sorted(TESTS_DIR.glob("test_*.py"))
        if _signals(p.read_text(encoding="utf-8"))
    }
    assert flagged, "the classifier flagged no module under tests/; the glob or classifier is broken"
    return flagged | set(WINDOWS_EXTRA)


# =========================================================================== #
# Workflow helpers
# =========================================================================== #


def _normalize_run(cmd: str) -> str:
    cmd = cmd.replace("\\\n", " ")
    return " ".join(cmd.split())


def _workflow() -> dict:
    return yaml.safe_load(CI_YML_PATH.read_text(encoding="utf-8"))


def _test_step_run(workflow: dict) -> str:
    for step in workflow["jobs"]["test"]["steps"]:
        if step.get("name") == "Test":
            return step["run"]
    raise AssertionError("the test job has no step named 'Test'")


def _assert_test_step_run(run: str) -> None:
    assert _normalize_run(run) == EXPECTED_TEST_STEP_RUN, (
        f"the Test step must run exactly {EXPECTED_TEST_STEP_RUN!r}; got {run!r}"
    )


def _env_definitions(workflow: dict) -> list[str]:
    """Where ``WINDOWS_TESTS`` is defined, as dotted locations."""
    where = []
    if "WINDOWS_TESTS" in (workflow.get("env") or {}):
        where.append("env")
    for job_name, job in workflow["jobs"].items():
        if "WINDOWS_TESTS" in (job.get("env") or {}):
            where.append(f"jobs.{job_name}.env")
        for i, step in enumerate(job.get("steps", [])):
            if "WINDOWS_TESTS" in (step.get("env") or {}):
                where.append(f"jobs.{job_name}.steps[{i}].env")
    return where


def _assert_single_definition(workflow: dict) -> None:
    where = _env_definitions(workflow)
    assert where == ["jobs.test.env"], (
        f"WINDOWS_TESTS must be defined only at jobs.test.env; found {where}"
    )


def _check_listed(listed: set[str], expected: set[str]) -> None:
    missing = sorted(expected - listed)
    stray = sorted(listed - expected)
    assert not missing and not stray, (
        f"flagged but not listed: {missing}; "
        f"listed but not OS-sensitive (neither flagged nor in WINDOWS_EXTRA): {stray}"
    )


# =========================================================================== #
# AC1, AC2
# =========================================================================== #


def test_ac1_ubuntu_runs_whole_suite_windows_the_named_list():
    _assert_test_step_run(_test_step_run(_workflow()))


def test_ac2_windows_tests_has_one_definition():
    _assert_single_definition(_workflow())


# =========================================================================== #
# AC5: the list is exactly the OS-sensitive set
# =========================================================================== #


def test_ac5_list_is_exactly_the_os_sensitive_set():
    listed = set(_workflow()["jobs"]["test"]["env"]["WINDOWS_TESTS"].split())
    assert listed, "jobs.test.env.WINDOWS_TESTS holds no paths"
    _check_listed(listed, _expected())


# =========================================================================== #
# AC6: each signal shape is detected (one shape per case)
# =========================================================================== #

SIGNAL_SHAPES = {
    "import-subprocess": "import subprocess\n",
    "from-subprocess": "from subprocess import run\n",
    "import-run_process": "import run_process\n",
    "from-run_process": "from run_process import run\n",
    "sys-executable": "import sys\nx = sys.executable\n",
    "import-segfacet-cli": "import segfacet.cli\n",
    "from-segfacet-cli": "from segfacet.cli import main\n",
    "from-segfacet-import-cli": "from segfacet import cli\n",
    "cli-target-string": "t = 'segfacet.cli.main'\n",
    "read_bytes": "p.read_bytes()\n",
    "newline-keyword": "f(newline='')\n",
    "gitattributes-string": "s = 'tests/x text eol=lf in .gitattributes'\n",
    "param-regenerated_failure_modes": "def test_x(regenerated_failure_modes):\n    pass\n",
    "param-regenerated_traceability": "def test_x(regenerated_traceability):\n    pass\n",
    "as_posix": "p.as_posix()\n",
    "os-sep": "import os\nx = os.sep\n",
    "os-path-sep": "import os\nx = os.path.sep\n",
    "PureWindowsPath": "from pathlib import PureWindowsPath\nx = PureWindowsPath('a')\n",
    "PurePosixPath": "from pathlib import PurePosixPath\nx = PurePosixPath('a')\n",
    "param-aide_check_result": "def test_x(aide_check_result):\n    pass\n",
}


@pytest.mark.parametrize("source", SIGNAL_SHAPES.values(), ids=SIGNAL_SHAPES.keys())
def test_ac6_signal_shape_is_detected(source):
    assert _signals(source)


# =========================================================================== #
# AC7: a pure module is not flagged
# =========================================================================== #


def test_ac7_pure_module_is_not_flagged():
    source = (
        '"""Pure checks; nothing here spawns a subprocess."""\n'
        "import numpy as np\n"
        "import pytest\n"
        "from segfacet.features import geometry\n"
    )
    assert _signals(source) == set()


# =========================================================================== #
# AC8: every hand-listed module exists
# =========================================================================== #


@pytest.mark.parametrize("key", sorted(WINDOWS_EXTRA))
def test_ac8_every_windows_extra_module_exists(key):
    path = REPO_ROOT / key
    assert path.is_file(), f"{key} does not exist"
    assert path.parent == TESTS_DIR, f"{key} is not directly under tests/"
    assert path.match("test_*.py"), f"{key} does not match test_*.py"
    assert path.relative_to(REPO_ROOT).as_posix() == key


# =========================================================================== #
# Adversarial cases named by the Testing Strategy
# =========================================================================== #


def test_missing_module():
    expected = _expected()
    dropped = sorted(expected)[0]
    with pytest.raises(AssertionError) as exc:
        _check_listed(expected - {dropped}, expected)
    message = str(exc.value)
    flagged_part = message.split("listed but not OS-sensitive")[0]
    assert "flagged but not listed" in message
    assert dropped in flagged_part


def test_stray_module():
    expected = _expected()
    stray = "tests/test_999_not_os_sensitive.py"
    assert stray not in expected
    with pytest.raises(AssertionError) as exc:
        _check_listed(expected | {stray}, expected)
    message = str(exc.value)
    assert "listed but not OS-sensitive" in message
    assert stray in message.split("listed but not OS-sensitive")[1]


def test_step_env_override():
    workflow = _workflow()
    workflow["jobs"]["test"]["steps"][0].setdefault("env", {})["WINDOWS_TESTS"] = "tests/x.py"
    with pytest.raises(AssertionError):
        _assert_single_definition(workflow)


def test_unguarded_list():
    with pytest.raises(AssertionError):
        _assert_test_step_run("python -m pytest -n 4 --durations=30 ${{ env.WINDOWS_TESTS }}")


@pytest.mark.parametrize(
    "source",
    [
        "import subprocess as sp\n",
        "from segfacet.cli import main as cli_main\n",
    ],
)
def test_aliased_import(source):
    assert _signals(source)
