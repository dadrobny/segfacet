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

# The in-process `run_checks` call this test used to make directly now runs
# at most once per pytest worker, behind the `aide_check_result` session
# fixture (tests/session_artifacts.py, item 170, insight 2026-09-18).


def test_aide_check_reports_no_errors(aide_check_result):
    errors = aide_check_result.errors
    assert errors == (), f"aide check reported error(s): {errors}"
