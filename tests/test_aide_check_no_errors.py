"""``aide check`` must report zero errors, always -- the one standing
mechanical guard over the living AIDE documents this suite keeps.

Nothing else in CI plays this role: the `scope-check` job only runs
`aide scope`, and `aide merge` never calls `run_checks` itself. So without
this test, a document malformed badly enough for `run_checks` to hard-error
(an unparseable acceptance box, a broken cross-reference, ...) has no gate at
all between a bad edit and `main`.

This asserts on **errors only**, never on warnings, per
``.aide/conventions/6-test-hygiene.md`` §6 ("Never pin an exact warning or
error count from a module that itself trips the lint being counted" and "A
scope claim about a diff belongs on the branch, not in the suite"). A
warning-set claim ("this item added no new warning") is true only at the
moment an item's diff was written; the documents it describes keep moving
under the loop's own verbs (`aide progress accept`, `aide insights archive`,
`aide gate approve`, ...), so pinning the warning set in the standing suite
turns every legitimate document edit into a red test for a class of reasons
the module never changed. An error is different: `run_checks` treats a
hard error as a defect regardless of when it is observed, so it is safe to
assert as a durable, non-diff-time property.

This module replaced four per-item warning-baseline tests retired on
2026-09-16: ``test_114_documentation_corrections.py``'s AC8,
``test_135_stage29_validation.py``'s AC27,
``test_147_specification_is_the_record.py``'s AC27, and
``test_148_per_path_mode_attribution.py``'s AC21 (plus AC24's equivalent in
``test_145_eight_hypothesised_modes.py``) -- each of which pinned a
snapshot of `aide check`'s warning set (by exact text, or by a hand-maintained
warning-class taxonomy) as a per-item acceptance claim, and each of which
became a source of recurring, unrelated red tests as the documents it pinned
kept moving. This test carries forward only the part of those tests that is
actually durable: `aide check` reports no error.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AIDE_SCRIPT = REPO_ROOT / ".aide" / "scripts" / "aide.py"


def _aide_check_errors() -> list:
    """Return `aide check`'s errors as a list of strings.

    Calls ``run_checks`` in-process rather than shelling out to
    ``aide.py check`` and parsing stdout -- the same in-process pattern
    ``test_114_documentation_corrections.py``'s retired ``_aide_check_warnings``
    used, and for the same reason: a subprocess capture is a platform-specific
    failure mode (the Windows CI runner returned ``proc.stdout is None``
    despite ``capture_output=True``) that a structured, in-process call simply
    has no surface for. ``run_checks`` is the same function ``cmd_check``
    calls, and it returns ``(errors, warnings)`` as structured data -- no
    stdout, no encoding, nothing to re-parse.
    """
    spec = importlib.util.spec_from_file_location("_aide_cli_no_errors", AIDE_SCRIPT)
    aide = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(aide)  # type: ignore[union-attr]
    repo_root = aide.find_repo_root(REPO_ROOT)
    errors, _warnings = aide.run_checks(repo_root, aide.load_config(repo_root))
    return list(errors)


def test_aide_check_reports_no_errors():
    errors = _aide_check_errors()
    assert errors == [], f"aide check reported error(s): {errors}"
