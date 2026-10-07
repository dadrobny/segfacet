"""Reader of ``docs/feature-taxonomy.md``'s mapping table and answers (item 214).

Not collected; imported as ``from feature_taxonomy_mapping import ...`` the
way tests import ``synthetic``. Items 215, 216 and 217 read the note through
this module, so its three names are the interface: ``NOTE_PATH``,
``read_mapping`` and ``answer_lines``.
"""

from __future__ import annotations

import re
from pathlib import Path

NOTE_PATH = Path(__file__).resolve().parent.parent / "docs" / "feature-taxonomy.md"

_MAPPING_HEADING = "## Mapping table"
_ANSWERS_HEADING = "## Answers"
_HEADER_ROW = "| Old path | New path | Change | Moved by |"
_SEPARATOR_ROW = re.compile(r"^\|[\s:|-]+\|$")
_ROW = re.compile(r"^\| `([^`]+)` \| `([^`]+)` \| (kept|moved|merged) \| (215|216) \|$")
_ANSWER_MARKER = "**Answer:**"


def _lines(text):
    if text is None:
        text = NOTE_PATH.read_text(encoding="utf-8")
    return text.splitlines()


def _section(lines, heading):
    """Lines between ``heading`` and the next ``## `` heading; the heading
    must occur exactly once."""
    starts = [i for i, line in enumerate(lines) if line.strip() == heading]
    if len(starts) != 1:
        raise ValueError(f"{heading!r} occurs {len(starts)} times, expected once")
    body = []
    for line in lines[starts[0] + 1:]:
        if line.startswith("## "):
            break
        body.append(line)
    return body


def read_mapping(text=None):
    """``(old, new, change, moved_by)`` tuples, ``moved_by`` an ``int``, in
    table order, read only from the ``## Mapping table`` section."""
    rows = []
    for line in _section(_lines(text), _MAPPING_HEADING):
        if not line.startswith("|"):
            continue
        if line.strip() == _HEADER_ROW or _SEPARATOR_ROW.match(line.strip()):
            continue
        match = _ROW.match(line)
        if match is None:
            raise ValueError(f"unparseable mapping row: {line!r}")
        old, new, change, moved_by = match.groups()
        rows.append((old, new, change, int(moved_by)))
    return rows


def answer_lines(heading, text=None):
    """The ``**Answer:**`` lines under one ``###`` heading inside
    ``## Answers``, up to the next heading of any level."""
    body = _section(_lines(text), _ANSWERS_HEADING)
    starts = [i for i, line in enumerate(body) if line.strip() == heading]
    if len(starts) != 1:
        raise ValueError(f"{heading!r} occurs {len(starts)} times, expected once")
    found = []
    for line in body[starts[0] + 1:]:
        if line.startswith("#"):
            break
        if line.startswith(_ANSWER_MARKER):
            found.append(line)
    return found
