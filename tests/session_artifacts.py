"""Session-scoped work helpers behind the ``aide_check_result``,
``regenerated_failure_modes`` and ``regenerated_traceability`` fixtures in
``tests/conftest.py`` (item 170).

A plain module, not ``conftest.py`` itself: ``testpaths`` also collects
``.aide/scripts/tests``, so ``import conftest`` from a test is ambiguous
(item 170's spec, Assumption A3). The precedents for a plain helper module
are ``tests/run_process.py`` and ``tests/committed_artifact_guard.py``.

Both types are ``NamedTuple``s so a consumer cannot mutate the shared result
that other requesters of the same session fixture read, and so
tuple-vs-list equality (``False`` in Python) also pins the type.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Callable, NamedTuple, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AIDE_SCRIPT = REPO_ROOT / ".aide" / "scripts" / "aide.py"


class AideCheckResult(NamedTuple):
    errors: Tuple[str, ...]
    warnings: Tuple[str, ...]


def load_aide_check_result(aide_script: Path = DEFAULT_AIDE_SCRIPT) -> AideCheckResult:
    """Run ``run_checks`` once, in-process, against ``aide_script``.

    Loads the script with ``importlib.util.spec_from_file_location`` under a
    module name no test uses -- the same in-process pattern
    ``test_aide_check_no_errors._aide_check_errors`` used before this item
    took over its loading lines.
    """
    spec = importlib.util.spec_from_file_location("_aide_session_artifacts", aide_script)
    aide = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(aide)  # type: ignore[union-attr]
    repo_root = aide.find_repo_root(REPO_ROOT)
    errors, warnings = aide.run_checks(repo_root, aide.load_config(repo_root))
    return AideCheckResult(errors=tuple(errors), warnings=tuple(warnings))


class Regeneration(NamedTuple):
    json_a: Path
    md_a: Path
    json_b: Path
    md_b: Path
    exit_codes: Tuple[int, int]
    committed_json_before: bytes
    committed_md_before: bytes


def regenerate(
    main: Callable[[Optional[Sequence[str]]], int],
    committed_json: Path,
    committed_md: Path,
    out_dir: Path,
) -> Regeneration:
    """Read the committed pair's bytes, then call ``main`` twice into ``out_dir``.

    The two runs write to four distinct paths (``a.json``/``a.md`` and
    ``b.json``/``b.md``) so a run-to-run comparison never compares a file
    with itself.
    """
    committed_json_before = committed_json.read_bytes()
    committed_md_before = committed_md.read_bytes()

    json_a, md_a = out_dir / "a.json", out_dir / "a.md"
    json_b, md_b = out_dir / "b.json", out_dir / "b.md"

    exit_a = main(["--json", str(json_a), "--md", str(md_a)])
    exit_b = main(["--json", str(json_b), "--md", str(md_b)])

    return Regeneration(
        json_a=json_a,
        md_a=md_a,
        json_b=json_b,
        md_b=md_b,
        exit_codes=(exit_a, exit_b),
        committed_json_before=committed_json_before,
        committed_md_before=committed_md_before,
    )
