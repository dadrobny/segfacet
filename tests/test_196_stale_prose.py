"""Tests for item 196 -- stale prose after items 189, 190 and 195.

Covers Acceptance Criterion AC1: the float-leaf count quoted in the
``ALLOWLIST`` reason for the pre-migration snapshot equals the count recomputed
live from the committed snapshot.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SNAPSHOT = "tests/corpus/094_pre_migration_snapshot.json"


def _count_floats(node) -> int:
    if isinstance(node, float):
        return 1
    if isinstance(node, dict):
        return sum(_count_floats(v) for v in node.values())
    if isinstance(node, list):
        return sum(_count_floats(v) for v in node)
    return 0


def test_ac1_allowlist_count_equals_live_float_count():
    import committed_artifact_guard as guard

    entries = [e for e in guard.ALLOWLIST if e.path == SNAPSHOT]
    assert len(entries) == 1
    match = re.match(r"\s*(\d+)\b", entries[0].reason)
    assert match is not None, entries[0].reason

    root = Path(__file__).resolve().parent.parent
    snapshot = json.loads((root / SNAPSHOT).read_text(encoding="utf-8"))

    assert int(match.group(1)) == _count_floats(snapshot)
