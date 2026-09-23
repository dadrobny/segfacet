#!/usr/bin/env python3
"""aide — the AIDE framework CLI.

A single, stdlib-only command-line tool for the deterministic parts of the AIDE
loop, so agents don't spend reasoning tokens on mechanical git/document surgery.
It is **venv-independent** (it must run before/without the project venv) and
**project-agnostic** — every project fact comes from ``aide.toml``.

Subcommands::

    python .aide/scripts/aide.py check [--queue NNN]   # consistency gate over docs/aide
    python .aide/scripts/aide.py scope [NNN]           # branch diff vs the item's authorised paths
    python .aide/scripts/aide.py progress set NNN <in-progress|in-review|done>
    python .aide/scripts/aide.py gate list|approve|decline [N]  # human gates in progress.md
    python .aide/scripts/aide.py queue start NNN       # create the queue branch (--specs for specs-)
    python .aide/scripts/aide.py queue tidy NNN        # mark a superseded queue as completed
    python .aide/scripts/aide.py insights list|tick|archive|resolve  # the insight inbox
    python .aide/scripts/aide.py ledger abandon NNN --rounds N  # the ledger row for an item that never merged
    python .aide/scripts/aide.py claim [--queue NNN]   # pick + claim the next 📋 item
    python .aide/scripts/aide.py merge NNN [--base R]  # merge a validated item per git.mode
    python .aide/scripts/aide.py env                   # venv existence / import check + bootstrap
    python .aide/scripts/aide.py sync [--item NNN]     # preflight: fetch, clean-tree check, right branch
    python .aide/scripts/aide.py gc [--merged] [--yes] # delete claim branches whose work landed
    python .aide/scripts/aide.py status                # one-call roadmap-state report

The parsing/editing helpers are pure functions so they can be unit-tested without
touching git or the real filesystem (see ``.aide/scripts/tests``).
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import fnmatch
import json
import os
import re
import shlex
import signal
import subprocess
import sys
from pathlib import Path, PurePosixPath, PurePath
from typing import Callable, Dict, Iterator, List, NamedTuple, Optional, Set, Tuple

# --------------------------------------------------------------------------- #
# Status icons (the format contract — see .aide/conventions.md)
# --------------------------------------------------------------------------- #
STATUS_TO_ICON = {
    "planned": "📋",
    "in-progress": "🚧",
    "in-review": "🔍",
    "complete": "✅",
    "deferred": "⏸️",
    "excluded": "❌",
}
ICON_TO_STATUS = {v: k for k, v in STATUS_TO_ICON.items()}
#: `in-review` sits between 🚧 and ✅ because it is strictly more advanced than
#: in-progress and strictly less than merged. It exists because ✅ used to mean
#: two different things depending on `git.mode`: under `auto-merge` the item was
#: merged, under `pr` it was pushed and awaiting a human — and everything
#: downstream read ✅ as "done", including the destructive sweep, which then
#: offered to delete the head branch of an open PR. **✅ now means merged, in
#: every mode**, and is set by `aide merge` when the merge actually happens.
RANK = {"planned": 0, "excluded": 1, "deferred": 2, "in-progress": 3,
        "in-review": 4, "complete": 5}
#: The statuses that still hold a dependent back. A dependency leaves the way
#: only by being merged (✅) or by leaving the queue's path (❌ excluded,
#: ⏸️ deferred) — 🚧 and 🔍 both block, because work in progress and work whose
#: PR is still open are alike missing from the base a dependent would branch
#: from. Named once because two separate decisions turn on it being the same
#: set: which item `aide claim` may offer, and whether a declared dependency
#: actually orders two specs (`queue_spec_findings`).
BLOCKING_STATUSES = ("planned", "in-progress", "in-review")

# Icons may be multi-codepoint (⏸️ = U+23F8 U+FE0F), so match by alternation
# (longest first), never a character class.
_ICON_ALT = "(?:" + "|".join(re.escape(i) for i in sorted(ICON_TO_STATUS, key=len, reverse=True)) + ")"
_ICON_RE = re.compile(_ICON_ALT)
# A deliverable bullet: leading "- " then a status icon.
_BULLET_RE = re.compile(r"^(?P<indent>\s*[-*]\s*)(?P<icon>" + _ICON_ALT + r")")
_CHECKBOX_RE = re.compile(r"^(?P<pre>\s*[-*]\s*\[)(?P<mark>[ xX])(?P<post>\].*)$")
_STAGE_HEADER_RE = re.compile(r"^##\s+Stage\s+(\d+)\b(.*)$")
_ANY_HEADER_RE = re.compile(r"^#{1,2}\s+")
# A stage header's status icon is the TRAILING icon only (the "— <icon>" tail);
# an icon inside the title text is plain text.
_TRAILING_ICON_RE = re.compile(r"(" + _ICON_ALT + r")\s*$")


# Every file this CLI reads is project-owned and hand-editable — aide.toml and the
# docs/aide/ living documents. Windows editors (Notepad, PowerShell's Out-File,
# "Save as UTF-8" in several IDEs) prepend a BOM, and a leading U+FEFF breaks
# first-line parsing *silently*: on the 3.9 fallback parser a BOM'd aide.toml loses
# only its FIRST table, because "^\[table\]$" fails on that one line while every
# later table still matches. [project] vanishes (source_dir back to its default)
# while [git] is honoured — a half-correct config, no error, every command
# reporting success. On 3.11 the same file raises an uncaught TOMLDecodeError.
# "utf-8-sig" strips a BOM when present and is byte-identical to "utf-8" when
# absent, so it is the correct default for anything a human may have touched.
_ENCODING = "utf-8-sig"


#: The accepted item-reference forms, as ONE definition (see conventions.md §1):
#:   *(Item 006)*            a single item
#:   *(Items 006, 044)*      a list — what create-queue tells authors to write
#:   *(Items 089/090)*       a list, slash-separated
#:   *(Items 071–075)*       an inclusive range, hyphen or en-dash
#: Everything that asks "does this line reference item NNN" goes through
#: _referenced_item_numbers, so the answer cannot differ between callers. It did
#: once: the status parse read only the FIRST number of a list, while the
#: progress-set matcher read any number literally present. Items after the first
#: were then orphaned — planned forever on a ✅ bullet, holding their queue open
#: and (since the live queue is the lowest-numbered open one) stranding
#: `aide claim` on a finished queue, while `aide progress set` acted on them
#: happily.
#: A number that opens a `YYYY-MM-DD` date is not an item number, and this is
#: the guard that says so. Without it the provenance shape AGENT-CONTEXT.md
#: itself prescribes — `*(item NNN, YYYY-MM-DD, engine X.Y.Z)*` — parsed as the
#: list `NNN, 2026, -08, -30`, and the unguarded `int()` below raised. The blast
#: radius was the whole verb, not the line: `aide progress set` reads every line
#: of progress.md, so four evidence annotations written in the documented
#: convention took `progress set` down for EVERY item repo-wide until a human
#: approved rewording them (issue #120).
#:
#: Two alternatives on purpose. `-\d{1,2}-\d{1,2}` recognises the date tail;
#: the bare `\d` forbids the backtrack that would otherwise let `\d+` give back
#: digits ("2026" → "202") until the tail no longer starts at the cursor and
#: the lookahead passed anyway. A range keeps working: "-092" carries one
#: hyphen group, not two.
_ITEM_REF_NOT_A_DATE = r"(?!\d|-\d{1,2}-\d{1,2})"
_ITEM_REF_NUM = r"0*\d+" + _ITEM_REF_NOT_A_DATE
_ITEM_REF_GROUP_RE = re.compile(
    r"[Ii]tems?\s+(" + _ITEM_REF_NUM + r"(?:\s*[,/–-]\s*" + _ITEM_REF_NUM + r")*)")
_ITEM_REF_SPLIT_RE = re.compile(r"\s*[,/]\s*")
_ITEM_REF_RANGE_RE = re.compile(r"^0*(\d+)\s*[–-]\s*0*(\d+)$")
#: The second, independent hardening: what the split hands back must LOOK like
#: an item number before it is read as one. Either fix alone stops the crash;
#: both are kept because the regex is a statement about one known prose shape
#: while this is the invariant — a part that is not a number is provenance
#: prose to skip, never a traceback out of an unrelated verb.
_ITEM_REF_NUMBER_RE = re.compile(r"^0*\d+$")

#: An inclusive range wider than this is treated as a typo and contributes only
#: its endpoints, so a stray "Items 6-9999" cannot invent thousands of items.
_ITEM_RANGE_MAX_SPAN = 50


def _referenced_item_numbers(text: str) -> List[int]:
    """Every item number referenced in ``text``, ranges expanded inclusively."""
    nums: List[int] = []
    for group in _ITEM_REF_GROUP_RE.finditer(text):
        for part in _ITEM_REF_SPLIT_RE.split(group.group(1)):
            part = part.strip()
            if not part:
                continue
            rng = _ITEM_REF_RANGE_RE.match(part)
            if rng is None:
                if _ITEM_REF_NUMBER_RE.match(part):
                    nums.append(int(part))
                continue
            lo, hi = int(rng.group(1)), int(rng.group(2))
            if lo <= hi <= lo + _ITEM_RANGE_MAX_SPAN:
                nums.extend(range(lo, hi + 1))
            else:
                nums.extend((lo, hi))
    return nums


def _has_typo_range(text: str) -> bool:
    """Does ``text`` carry a range so wide the reader treats it as a typo?

    `_referenced_item_numbers` keeps only such a range's ENDPOINTS, so what it
    hands back is deliberately not what the author wrote — `Items 044-999` reads
    as {44, 999}, and 999 is an artifact of the typo, not an item. That is a
    safe misreading while it stays in memory. It is not safe for a caller that
    writes the numbers back into the document, which is why the desugar asks.
    """
    for group in _ITEM_REF_GROUP_RE.finditer(text):
        for part in _ITEM_REF_SPLIT_RE.split(group.group(1)):
            rng = _ITEM_REF_RANGE_RE.match(part.strip())
            if rng is None:
                continue
            lo, hi = int(rng.group(1)), int(rng.group(2))
            if not lo <= hi <= lo + _ITEM_RANGE_MAX_SPAN:
                return True
    return False


def _references_item(text: str, num: int) -> bool:
    """Does ``text`` reference item ``num`` in any accepted form?"""
    return num in _referenced_item_numbers(text)


#: The item-reference MARKER that closes a deliverable bullet —
#: `- 📋 <text>. *(Item 006)*` — the `*(…)*` suffix the templates prescribe
#: (§1 → progress.md calls it "the *(Item NNN)* suffix"). Only this trailing
#: marker ties items to the bullet: a reference elsewhere in the bullet's prose
#: ("absorbing *(Item 095)*'s scope") is free text and attributes nothing
#: (issue #99). Several adjacent markers at the end all count, and a trailing
#: period after the last one is tolerated.
_BULLET_MARKER_RE = re.compile(
    r"(?:\*\(\s*[Ii]tems?\s+[^)\n]*\)\*[ \t.]*)+$")


def _bullet_marker_item_numbers(last_line: str) -> List[int]:
    """Item numbers in the trailing marker of a bullet's final line, if any."""
    m = _BULLET_MARKER_RE.search(last_line)
    return _referenced_item_numbers(m.group(0)) if m else []


def _deliverable_bullet_spans(lines: List[str]) -> List[Tuple[int, int]]:
    """``(first, last)`` line indices of each deliverable bullet.

    A deliverable bullet is a ``_BULLET_RE`` line plus its wrapped continuation
    lines — indented text carrying no bullet marker of its own. A blank line, a
    non-deliverable bullet, or an unindented new block ends the span. This is
    the ONE definition of a bullet's extent; ``_parse_item_status`` (read) and
    ``set_item_status`` (write) both build on it, so "which bullet owns item
    NNN" cannot differ between the two directions.
    """
    spans: List[Tuple[int, int]] = []
    open_span = False
    for i, line in enumerate(lines):
        if _BULLET_RE.match(line):
            spans.append((i, i))
            open_span = True
        elif not line.strip() or re.match(r"^\s*[-*]\s", line) or not re.match(r"^\s+\S", line):
            open_span = False
        elif open_span:
            spans[-1] = (spans[-1][0], i)
    return spans


# --------------------------------------------------------------------------- #
# TOML config (tomllib on 3.11+, tiny fallback for the aide.toml subset on 3.9)
# --------------------------------------------------------------------------- #
DEFAULT_CONFIG: Dict[str, Dict[str, object]] = {
    "project": {"name": "project", "source_dir": "src", "tests_dir": "tests", "docs_dir": "docs/aide"},
    # `interpreter` names what `env --bootstrap` builds the venv from — a
    # command on PATH ("python3.12", "py -3.12") or an absolute path. Empty
    # means the Python running the CLI, which is whatever launched it: a
    # consumer whose dependency closure only resolves on 3.12 got a 3.14 venv
    # from an ambient conda, a source build that failed on cmake, and an
    # `env` that still said OK (issue #166).
    "python": {"venv": ".venv", "bootstrap": "pip install -e .[dev]",
               "test_command": "python -m pytest", "import_check": "",
               "interpreter": ""},
    "git": {"mode": "auto-merge", "main_branch": "main", "branch_prefix": "aide/"},
    # `review` names whether the item loop runs an adversarial read of the diff
    # alongside the spec-relative one (conventions.md §9). Prose-consumed by the
    # orchestrator, the way `clarify` is: "off" (default) runs the validator
    # alone; "background" also dispatches a reviewer concurrently with it, and
    # the merge waits for both. Off by default because a review round costs
    # tokens on every item, and a consumer with CI and hosted reviewers may
    # reasonably decline it (issue #151).
    "loop": {"queue_cap": 10, "validation_rounds": 3, "clarify": "assume",
             "claim_scope": "live-queue", "review": "off"},
    "framework": {"repo": ""},
    # [validation] — named environment profiles for stage-validation items:
    # <name> = <python expression>, true iff the environment provides the
    # capability (e.g. gpu = "__import__('torch').cuda.is_available()").
    "validation": {},
}


# Escape sequences this reader decodes inside a basic (double-quoted) string. TOML
# also defines \b \t \n \f \r \uXXXX \UXXXXXXXX; rather than half-implement them and
# quietly disagree with tomllib, an unlisted escape is a ConfigError (see below).
_BASIC_ESCAPES = {'"': '"', "\\": "\\"}


def _read_quoted_value(key: str, stripped: str, lineno: int) -> str:
    """Decode the quoted string at the start of ``stripped``, or raise ``ConfigError``.

    Finding where a string ENDS and extracting what it CONTAINS are the same scan, so
    they live in one function. Splitting them is what produced the bug this replaces:
    the validator walked the value escape-aware while the extractor used a naive
    ``split(quote, 1)[0]``, so ``msg = "he said \\"hi\\""`` passed validation and was
    then silently truncated to ``he said \\``.

    Single-quoted strings are TOML *literal* strings: no escapes, backslash is itself.
    Double-quoted are *basic* strings, where a backslash escapes the next character.
    """
    quote = stripped[0]
    out: List[str] = []
    i = 1
    while i < len(stripped):
        ch = stripped[i]
        if quote == '"' and ch == "\\":
            nxt = stripped[i + 1] if i + 1 < len(stripped) else ""
            if not nxt:
                raise ConfigError(
                    f"line {lineno}: unterminated escape in the value for key {key!r} — "
                    "a backslash at the end of a basic string escapes nothing"
                )
            if nxt not in _BASIC_ESCAPES:
                raise ConfigError(
                    f"line {lineno}: unsupported escape '\\{nxt}' in the value for "
                    f"key {key!r} — this minimal reader decodes only \\\\ and \\\"; "
                    f"use a single-quoted 'literal string' (backslashes are literal "
                    f"there) or forward slashes"
                )
            out.append(_BASIC_ESCAPES[nxt])
            i += 2
            continue
        if ch == quote:
            tail = stripped[i + 1:].lstrip()
            if tail and not tail.startswith("#"):
                raise ConfigError(
                    f"line {lineno}: trailing characters after the quoted value for "
                    f"key {key!r}: {tail!r}"
                )
            return "".join(out)
        out.append(ch)
        i += 1

    raise ConfigError(
        f"line {lineno}: unterminated string for key {key!r} — "
        f"the value opens with {quote} but never closes it"
    )


class ConfigError(Exception):
    """``aide.toml`` cannot be trusted — malformed, so its facts are unknowable.

    Raised instead of guessing. Every project fact the framework acts on comes from
    that file, so silently falling back to defaults would scope the builder at the
    wrong directory, pick the wrong git mode, or run the wrong test command while
    reporting success. ``main`` catches this and prints it as a plain error.
    """


def _parse_toml(text: str) -> Dict[str, Dict[str, object]]:
    """Minimal TOML reader for the flat ``[table] key = value`` shape of aide.toml.

    Supports string/int/float/bool scalars and ``#`` comments. Used only when the
    stdlib ``tomllib`` (Python 3.11+) is unavailable, so the CLI and its tests run
    on the project's 3.9 venv too.

    Deliberately lenient about what it *ignores* (unknown lines, blank tables) but
    strict about what it would otherwise *misread*, because a wrong-but-plausible
    value is worse than a refusal: an unterminated quoted string used to yield the
    truncated text, so a typo became a believable answer on 3.9 while 3.11's tomllib
    rejected the same file. Quoted values are decoded by ``_read_quoted_value``,
    which raises ``ConfigError`` rather than guess — so both parser paths agree on
    which files are readable.
    """
    data: Dict[str, Dict[str, object]] = {}
    table: Optional[Dict[str, object]] = None
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^\[([A-Za-z0-9_.]+)\]$", line)
        if m:
            table = data.setdefault(m.group(1), {})
            continue
        if table is None or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # A quoted value owns everything up to its closing quote — a '#' inside it is
        # data, not a comment — so it is scanned before any comment stripping. Only
        # an UNquoted value is truncated at '#'.
        if value and value[0] in "\"'":
            table[key] = _read_quoted_value(key, value, lineno)
            continue
        token = value.split("#", 1)[0].strip()
        if not token:
            raise ConfigError(f"line {lineno}: missing value for key {key!r}")
        if token.lower() in ("true", "false"):
            table[key] = token.lower() == "true"
        else:
            try:
                table[key] = int(token)
            except ValueError:
                try:
                    table[key] = float(token)
                except ValueError:
                    table[key] = token
    return data


def _config_error(path: Path, what: str, exc: object) -> "ConfigError":
    """One phrasing for every way ``aide.toml`` can fail, so they cannot drift.

    ``what`` distinguishes the causes a reader would act on differently: a file that
    ``is malformed`` needs an edit, one that ``cannot be read`` needs permissions or
    disk attention. The rest — naming the path, and why defaults are not an
    acceptable fallback — is identical in every case.
    """
    return ConfigError(
        f"{path} {what}: {exc}\n"
        f"  aide.toml states this project's facts (source_dir, git mode, test "
        f"command); refusing to continue with defaults that would be silently wrong."
    )


def load_config(repo_root: Path) -> Dict[str, Dict[str, object]]:
    """Load ``aide.toml`` merged over defaults.

    A *missing* file is fine — defaults apply, which is what an unconfigured repo
    means. A *malformed* file is not: it states project facts that cannot be read,
    so this raises ``ConfigError`` naming the file rather than falling back to
    defaults that would silently be wrong.
    """
    merged = {k: dict(v) for k, v in DEFAULT_CONFIG.items()}
    path = repo_root / "aide.toml"
    if path.is_file():
        try:
            text = path.read_text(encoding=_ENCODING)
        except UnicodeDecodeError as exc:
            raise _config_error(path, "is malformed", exc) from exc
        except OSError as exc:
            # Present but unreadable (permissions, a device error, a dangling
            # link). The file may be perfectly well-formed — say so accurately
            # rather than sending the reader to hunt for a syntax mistake.
            raise _config_error(path, "cannot be read", exc) from exc
        try:
            import tomllib  # type: ignore
        except ModuleNotFoundError:
            detail_source = _parse_toml
        else:
            # tomllib.TOMLDecodeError subclasses ValueError; catching ValueError
            # keeps this working if that relationship ever changes.
            detail_source = tomllib.loads
        try:
            parsed = detail_source(text)
        except (ConfigError, ValueError) as exc:
            # Both parsers report line/column but neither knows the path, and the
            # path is the one thing a reader needs to go fix it.
            raise _config_error(path, "is malformed", exc) from exc
        for section, values in parsed.items():
            merged.setdefault(section, {})
            if isinstance(values, dict):
                merged[section].update(values)
    return merged


def find_repo_root(start: Optional[Path] = None) -> Path:
    """Walk up from ``start`` (default cwd) to the directory holding aide.toml."""
    start = (start or Path.cwd()).resolve()
    for candidate in (start, *start.parents):
        if (candidate / "aide.toml").is_file():
            return candidate
    return start


def docs_dir(repo_root: Path, config: Dict[str, Dict[str, object]]) -> Path:
    return repo_root / str(config["project"].get("docs_dir", "docs/aide"))


# --------------------------------------------------------------------------- #
# progress.md — parsing helpers
# --------------------------------------------------------------------------- #
def _icon_status(text: str) -> Optional[str]:
    m = _ICON_RE.search(text)
    return ICON_TO_STATUS[m.group(0)] if m else None


def _header_status(line: str) -> Optional[str]:
    """A stage header's status — its trailing icon only."""
    m = _TRAILING_ICON_RE.search(line)
    return ICON_TO_STATUS[m.group(1)] if m else None


def _split_row(line: str) -> List[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _structural_status(line: str) -> Optional[str]:
    """Status conveyed by a line's STRUCTURAL icon position only.

    Structural positions (the format contract, conventions.md §1): the leading
    icon of a deliverable bullet, a table row's Status (last) cell, and a stage
    header's trailing icon. An icon anywhere else on a line is plain text and
    is never read as status — prose stays free of the icon vocabulary.
    """
    m = _BULLET_RE.match(line)
    if m:
        return ICON_TO_STATUS[m.group("icon")]
    if line.strip().startswith("|"):
        cells = _split_row(line)
        return _icon_status(cells[-1]) if cells else None
    if _STAGE_HEADER_RE.match(line):
        return _header_status(line)
    return None


def stage_sections(lines: List[str]) -> List[Tuple[int, int, str]]:
    """Return ``(start_index, end_index_exclusive, stage_number)`` per stage section."""
    out: List[Tuple[int, int, str]] = []
    starts: List[Tuple[int, str]] = []
    for i, line in enumerate(lines):
        m = _STAGE_HEADER_RE.match(line)
        if m:
            starts.append((i, m.group(1)))
    for idx, (start, num) in enumerate(starts):
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if _ANY_HEADER_RE.match(lines[j]):
                end = j
                break
        out.append((start, end, num))
    return out


def stage_deliverable_statuses(lines: List[str], start: int, end: int) -> List[str]:
    """Statuses of the flat deliverable bullets within a stage section."""
    statuses: List[str] = []
    for line in lines[start:end]:
        if _CHECKBOX_RE.match(line):
            continue
        m = _BULLET_RE.match(line)
        if m:
            statuses.append(ICON_TO_STATUS[m.group("icon")])
    return statuses


def rollup_status(statuses: List[str]) -> Optional[str]:
    """Derive a stage status from its deliverable statuses (None if no bullets)."""
    if not statuses:
        return None
    if all(s in ("complete", "excluded") for s in statuses) and any(
        s == "complete" for s in statuses
    ):
        return "complete"
    # 🔍 is deliberately absent from the set above: an item awaiting review has
    # not landed, so a stage holding one is 🚧, never ✅. That is the whole point
    # of the state — a `pr`-mode run must not roll a stage up to "shipped" on
    # work that is still an open PR.
    #
    # ⏸ is absent for the stronger version of the same reason (issue #173): a
    # deferred deliverable has landed even less than a reviewed one — it is a
    # decision to do the work *later*, so a stage still holding one has not
    # shipped. ❌ stays terminal because an excluded deliverable is a decision
    # not to do the work at all, and there is nothing left to wait for. This is
    # the distinction `scope` already draws one layer down, where the spent set
    # is `{complete, excluded}` and the comment says ⏸ claims are "dormant, not
    # dead"; the two read the same icon the same way now.
    if any(s in ("complete", "in-progress", "in-review") for s in statuses):
        return "in-progress"
    return "planned"


# --------------------------------------------------------------------------- #
# Outcome targets (optional table — see conventions.md §1)
# --------------------------------------------------------------------------- #
_TARGETS_HEADING_RE = re.compile(r"^#{1,2}\s+Outcome targets\b", re.IGNORECASE)
#: Table-local status vocabulary (like the env-gated verification table's):
#: the cell's LEADING mark decides, the rest is evidence/notes for humans.
_TARGET_STATUS_KIND = {"✅": "met", "❌": "not-met", "❓": "unverified"}


class OutcomeTarget(NamedTuple):
    lineno: int              # 1-based line number in progress.md
    text: str                # the Target cell
    objectives: List[str]    # G-codes named in the Objective cell
    kind: Optional[str]      # "met" | "not-met" | "unverified" | None (unrecognised)


#: The optional Environment-Gated Capability Verification table (§1 →
#: environment-gated capabilities). Outside the rollup like Outcome targets,
#: but gating nothing at all: its reader surfaces state, and warns.
_CAPABILITIES_HEADING_RE = re.compile(
    r"^#{1,2}\s+Environment-Gated Capability Verification\b", re.IGNORECASE)
_CAPABILITY_STATUS_KIND = {"✅": "verified", "❓": "unverified"}
#: A row's link to the `[validation]` profile that would verify it, written in
#: its Package / Tool cell as `` `gpu` profile `` or `` profile `gpu` ``.
_PROFILE_LINK_RE = re.compile(
    r"`([A-Za-z0-9_-]+)`\s+profile\b|\bprofile\s+`([A-Za-z0-9_-]+)`", re.IGNORECASE)
#: The introducing stage(s): the first `Stage N` / `Stages N, M` / `Stage 3 / 4`
#: / `Stages 5–7` run in the Introduced by cell. A later "closed by Stage 12"
#: names a different stage, which is why only the first run counts.
_INTRODUCED_BY_RE = re.compile(
    r"\bStages?\s+(\d+(?:\s*(?:,|/|&|\band\b|[-–])\s*\d+)*)", re.IGNORECASE)
#: A Notes cell holding only a dash records nothing.
_EMPTY_CELL = {"", "-", "—", "–"}


class GatedCapability(NamedTuple):
    lineno: int              # 1-based line number in progress.md
    text: str                # the Capability cell
    profiles: List[str]      # [validation] profiles the Package / Tool cell names
    stages: List[int]        # the stage(s) the Introduced by cell names first
    kind: Optional[str]      # "verified" | "unverified" | None (unrecognised)
    noted: bool              # the Notes cell records something


#: The optional `## Human gates` table — a decision only a person can make,
#: blocking work until they make it. Kept separate from acceptance boxes
#: deliberately: conventions.md §1 defines those as observable checks OF THE
#: BUILT THING, which a steering decision is not. Same reasoning that gave
#: Outcome targets their own table rather than overloading the checkboxes.
_GATES_HEADING_RE = re.compile(r"^#{1,2}\s+Human gates\b", re.IGNORECASE)
#: Table-local vocabulary, like Outcome targets': the LEADING mark decides.
_GATE_STATUS_KIND = {"⏳": "awaiting", "✅": "approved", "❌": "declined"}
#: A gate whose Blocks cell says this halts every item, everywhere — for a
#: programme-level decision ("no work proceeds until sign-off").
_GATE_BLOCKS_ALL = "all"
#: `stage N` — every item the named stage's deliverables reference. Blocking is
#: tied to a STAGE, never to a queue: a queue is an incidental batch boundary
#: (part of a stage, a stage, or several small ones), so "the live queue" names
#: different work from one week to the next while the decision has not changed.
#: A stage is the roadmap's own unit and means the same thing over time.
_GATE_BLOCKS_STAGE_RE = re.compile(r"^stage\s+0*(\d+)$", re.IGNORECASE)


class HumanGate(NamedTuple):
    lineno: int              # 1-based line number in progress.md
    text: str                # the Gate cell
    blocks: List[int]        # item numbers named directly (empty for stage/all)
    stage: Optional[str]     # stage number when the cell reads "stage N"
    blocks_all: bool         # True when the cell reads "all"
    kind: Optional[str]      # "awaiting" | "approved" | "declined" | None

    @property
    def reach(self) -> str:
        """How far this gate reaches, for a human-readable report."""
        if self.blocks_all:
            return "all items"
        if self.stage is not None:
            return f"stage {self.stage}"
        return ("items " + ", ".join(f"{i:03d}" for i in self.blocks)
                if self.blocks else "nothing named")


def stage_section(lines: List[str], stage: str) -> Optional[Tuple[int, int, str]]:
    """The stage section numbered *stage*, or None if no such section exists.

    The single place the "which section is stage N" lookup lives. Callers need
    to tell "no such stage" from "the stage is there and empty" — an absent
    section is a typo, an empty one is a stage nobody has queued work for yet —
    and a helper that collapses both into a falsy return makes that
    indistinguishable at every call site.
    """
    return next((sec for sec in stage_sections(lines)
                 if _same_stage(sec[2], stage)), None)


def stage_item_numbers(lines: List[str], stage: str) -> List[int]:
    """Item numbers referenced by *stage*'s deliverable bullets in progress.md.

    Reuses the §1 rule that only a deliverable bullet (and its wrapped
    continuation lines) carries an item reference, so a Notes cell or an
    acceptance checkbox naming an item does not widen a stage gate's reach.

    Empty for a stage that does not exist *and* for one whose deliverables name
    no item yet; ``stage_section`` is what separates the two.
    """
    section = stage_section(lines, stage)
    if section is None:
        return []
    start, end, _ = section
    return sorted(_parse_item_status(lines[start:end])[2])


def _blocked_item_numbers(cell: str) -> List[int]:
    """Item numbers in a gate's ``Blocks`` cell.

    Accepts the §1 reference forms (``Items 106, 110–112``) *and* the bare
    numbers an author naturally writes in a column already headed "Blocks"
    (``106``, ``110, 111``). The shared extractor keys off the word "Item", so
    a bare list would parse as **nothing** — and a gate blocking nothing is a
    gate that silently does not work, the one failure mode this table exists to
    prevent. Normalising the cell first reuses that extractor's list/range
    handling rather than growing a second dialect.
    """
    text = cell if re.search(r"\bitems?\b", cell, re.IGNORECASE) else f"Items {cell}"
    return _referenced_item_numbers(text)


# --------------------------------------------------------------------------- #
# progress.md tables — the rows a reader can use, and the rows it cannot
# --------------------------------------------------------------------------- #
_SUMMARY_HEADING_RE = re.compile(r"^#{1,2}\s+Stage summary\b", re.IGNORECASE)
_OBJECTIVES_HEADING_RE = re.compile(r"^#{1,2}\s+Objective coverage\b", re.IGNORECASE)


class _ProgressTable(NamedTuple):
    """One of the five ``progress.md`` tables the engine reads."""
    name: str                # how a finding names the table
    heading: "re.Pattern"    # the section the template puts the table under
    width: int               # cells in a data row
    header: str              # the header row's first cell, lower-cased
    #: Why a row of the right width is still unusable, or None.
    cell_problem: Callable[[List[str]], Optional[str]]
    #: What stops being checked while such a row is dropped.
    loses: str
    #: True for a table whose reader takes rows by shape from anywhere in the
    #: document rather than from under its heading — see ``_table_rows``.
    anywhere: bool = False
    #: False for a table no other check gates on, whose unusable row is
    #: therefore a warning: dropping it takes no error with it (issue #207).
    error: bool = True


def _summary_row_problem(cells: List[str]) -> Optional[str]:
    if not re.fullmatch(r"\d+", cells[0]):
        return "has a Stage cell that is not an integer"
    if not _icon_status(cells[3]):
        return "has no status icon in its Status cell"
    return None


def _objective_row_problem(cells: List[str]) -> Optional[str]:
    if not re.match(r"G\d+", cells[0]):
        return "has an Objective cell that does not start with a G<n> code"
    if not _icon_status(cells[2]):
        return "has no status icon in its Status cell"
    return None


def _target_row_problem(cells: List[str]) -> Optional[str]:
    """An Objective cell naming no ``G<n>`` is read: such a target gates no
    objective, which a measured cost or runtime target may mean to (`—`)."""
    return None if cells[0] else "has an empty Target cell"


_STAGE_SUMMARY = _ProgressTable(
    "stage summary", _SUMMARY_HEADING_RE, 4, "stage", _summary_row_problem,
    "its stage's ✅ is never checked against the deliverables under it",
    anywhere=True)
_OBJECTIVE_COVERAGE = _ProgressTable(
    "objective coverage", _OBJECTIVES_HEADING_RE, 3, "objective",
    _objective_row_problem,
    "its objective's ✅ is never checked against its Outcome targets",
    anywhere=True)
_OUTCOME_TARGETS = _ProgressTable(
    "Outcome targets", _TARGETS_HEADING_RE, 5, "target", _target_row_problem,
    "no objective is checked against it")
#: An unrecognised Status is read, and blocks — a typo in the mark must not
#: open a gate — so width is the only thing that makes a gate row unusable.
_HUMAN_GATES = _ProgressTable(
    "human-gate", _GATES_HEADING_RE, 4, "gate", lambda cells: None,
    "what it blocks is unknown, and `aide claim` holds every item until it "
    "is fixed")
_CAPABILITIES = _ProgressTable(
    "capability", _CAPABILITIES_HEADING_RE, 5, "capability",
    lambda cells: None if cells[0] else "has an empty Capability cell",
    "`aide status` never lists it and no closed stage is checked against it",
    error=False)
_PROGRESS_TABLES = (_STAGE_SUMMARY, _OBJECTIVE_COVERAGE, _OUTCOME_TARGETS,
                    _HUMAN_GATES, _CAPABILITIES)


def _reads(table: _ProgressTable, cells: List[str]) -> bool:
    """Whether *table*'s reader can use a row — the one test every reader of
    these tables applies, and the one the check reports the failures of."""
    return len(cells) == table.width and table.cell_problem(cells) is None


def _is_separator_row(cells: List[str]) -> bool:
    """The ``|---|:---:|`` row: every non-empty cell a delimiter, and one at least.

    Every cell, not the first: a gate titled ``-`` is data. And a NON-EMPTY
    one: `set("") <= set("-: ")` is true, so an empty first cell used to read
    as a separator, and a mis-shaped row like `| | 028 | ⏳ Awaiting | a | pipe |`
    was skipped without a word.
    """
    return (any(cells)
            and all(re.fullmatch(r":?-+:?", c) for c in cells if c))


def _is_table_furniture(cells: List[str], header: str) -> bool:
    """True for a table's header or separator row — never for data.

    A header is recognised by its first cell alone. Markdown's own rule — the
    row above the separator — would read the only row of a table written
    without a header as its header, and drop it unreported: an ``all`` gate
    raised by hand in a project whose optional section was deleted would
    then hold nothing.
    """
    return _is_separator_row(cells) or bool(cells) and cells[0].lower() == header


def _pipe_blocks(lines: List[str]) -> List[List[int]]:
    """Indices of each run of consecutive ``|`` lines — each markdown table."""
    blocks: List[List[int]] = []
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        if blocks and blocks[-1][-1] == i - 1:
            blocks[-1].append(i)
        else:
            blocks.append([i])
    return blocks


def _table_rows(lines: List[str], table: _ProgressTable
                ) -> Iterator[Tuple[int, List[str], Optional[str]]]:
    """``(index, cells, problem)`` for each data row of *table* in *lines*.

    *problem* is None for a row the table's reader can use (``_reads``), and
    otherwise says why it cannot. The rows are every ``|`` line in the section
    under the table's template heading — a second table there is read as part
    of this one, and fails closed. An ``anywhere`` table whose section holds
    no readable row — the heading missing, or the table under another one,
    where its reader still finds it by shape — also takes in every markdown
    table the reader takes a row from, so it is checked row by row all the
    same. (Not always: with a readable table under the heading, a table of the
    author's own elsewhere that happens to hold one summary-shaped row would
    have its every other row reported.) "Skipped" and "reported" are thereby
    one decision rather than two that can drift: issue #202 found three
    behaviours for the one situation, and the rows silently dropped were the
    ones taking an error with them.
    """
    scope: List[int] = []
    in_section = False
    for i, line in enumerate(lines):
        if table.heading.match(line):
            in_section = True
        elif in_section and _ANY_HEADER_RE.match(line):
            break  # next section — the table is over
        elif in_section and line.strip().startswith("|"):
            scope.append(i)
    if table.anywhere and not any(_reads(table, _split_row(lines[i])) for i in scope):
        scope = sorted(set(scope).union(
            i for block in _pipe_blocks(lines)
            if any(_reads(table, _split_row(lines[j])) for j in block)
            for i in block))
    for i in scope:
        cells = _split_row(lines[i])
        if _is_table_furniture(cells, table.header):
            continue
        yield i, cells, (f"has {len(cells)} cells, not {table.width}"
                         if len(cells) != table.width else table.cell_problem(cells))


def unreadable_row_errors(lines: List[str]) -> List[str]:
    """One error per row of a read table that its reader cannot use.

    An error, not a warning, because the row's cells cannot be trusted to be in
    position — the usual cause is a `|` that shifted them — so there is no
    telling whether it was a ✅ a check exists to catch. The check it would
    have fed cannot run, so the check fails on the row instead: the only
    reading of an unreadable row that cannot pass an over-claim.

    A table no check gates on (``error=False``) is the exception, reported by
    ``unreadable_row_warnings``: its dropped row carries no over-claim away.
    """
    return _unreadable_row_findings(lines, error=True)


def unreadable_row_warnings(lines: List[str]) -> List[str]:
    """``unreadable_row_errors``'s findings for the tables that gate nothing."""
    return _unreadable_row_findings(lines, error=False)


def _unreadable_row_findings(lines: List[str], error: bool) -> List[str]:
    out: List[str] = []
    for table, i, cells, problem in _unreadable_rows(lines):
        if table.error is not error:
            continue
        below = lines[i + 1] if i + 1 < len(lines) else ""
        if below.strip().startswith("|") and _is_separator_row(_split_row(below)):
            # Header position: most likely a retitled header, possibly the
            # only row of a table written without one. Say both.
            out.append(
                f"progress.md:{i + 1}: {table.name} row {problem}, above the "
                f"separator — a header row's first cell reads "
                f"'{table.header.capitalize()}'; as data, it is not read, so "
                f"{table.loses}.")
            continue
        hint = (" A '|' inside a cell is the usual cause."
                if len(cells) != table.width else "")
        out.append(f"progress.md:{i + 1}: {table.name} row {problem} — it "
                   f"is not read, so {table.loses}.{hint}")
    return out


def _unreadable_rows(lines: List[str]
                     ) -> List[Tuple[_ProgressTable, int, List[str], str]]:
    """``(table, index, cells, problem)`` for every row no reader can use."""
    return [(table, i, cells, problem) for table in _PROGRESS_TABLES
            for i, cells, problem in _table_rows(lines, table)
            if problem is not None]


def unreadable_gate_rows(lines: List[str]) -> List[Tuple[int, str]]:
    """``(line number, problem)`` for each ``## Human gates`` row no reader can use.

    ``aide claim`` holds every item while one exists: what the row blocks is
    unknown, so any item released could be one it was written to hold — the
    same fail-closed reading that makes an unrecognised Status block.
    """
    return [(i + 1, problem) for i, _, problem in _table_rows(lines, _HUMAN_GATES)
            if problem is not None]


def human_gates(lines: List[str]) -> List[HumanGate]:
    """Rows of the optional ``## Human gates`` table in progress.md.

    A gate is a decision only a person can make — approving a direction,
    signing off an irreversible change, confirming an out-of-band prerequisite
    arrived. It blocks work until resolved, and **no agent may resolve one**:
    that is the entire point, and the reason the state lives in a CLI-written
    table rather than a checkbox any role could tick.

    ``Blocks`` accepts the item-reference forms of §1 (``106``, ``106, 107``,
    ``106–108``), ``stage N`` for every item that stage's deliverables
    reference, or ``all`` for a programme-level stop.

    A row of the wrong width is not a gate; ``unreadable_gate_rows`` reports
    it, and ``aide claim`` holds everything while it stands.
    """
    out: List[HumanGate] = []
    for i, cells, problem in _table_rows(lines, _HUMAN_GATES):
        if problem is not None:
            continue
        kind = next((k for icon, k in _GATE_STATUS_KIND.items()
                     if cells[2].startswith(icon)), None)
        blocks_cell = cells[1].strip()
        blocks_all = blocks_cell.lower() == _GATE_BLOCKS_ALL
        sm = _GATE_BLOCKS_STAGE_RE.match(blocks_cell)
        stage = sm.group(1) if sm else None
        blocks = [] if (blocks_all or stage) else _blocked_item_numbers(blocks_cell)
        out.append(HumanGate(i + 1, cells[0], blocks, stage, blocks_all, kind))
    return out


def blocking_gates(lines: List[str]) -> List[HumanGate]:
    """Gates still holding work up — every gate that is not ``✅ Approved``.

    **A declined gate keeps blocking.** It is *resolved* — a person decided —
    but the decision was "no", so releasing the work it guards would run
    exactly what was refused. The remedy is to re-plan (drop the item, or
    change what the gate asks), not to let the loop proceed. Only approval
    opens a gate.

    An unrecognised status also blocks: a typo in the mark must not silently
    open one.
    """
    return [g for g in human_gates(lines) if g.kind != "approved"]


def gate_blocked_items(lines: List[str]) -> Tuple[set, List[HumanGate]]:
    """``(blocked item numbers, block-everything gates)`` from the blocking gates.

    A ``stage N`` gate resolves through progress.md to the items that stage's
    deliverables reference, so its reach follows the roadmap as the stage's
    contents change — which is the whole reason reach is anchored to a stage
    rather than to whichever queue happens to be live.
    """
    blocked, everything = set(), []
    for g in blocking_gates(lines):
        if g.blocks_all:
            everything.append(g)
        elif g.stage is not None:
            blocked.update(stage_item_numbers(lines, g.stage))
        else:
            blocked.update(g.blocks)
    return blocked, everything


def outcome_targets(lines: List[str]) -> List[OutcomeTarget]:
    """Rows of the optional ``## Outcome targets`` table in progress.md.

    An outcome target is a MEASURED result the roadmap commits to (an error
    rate, a benchmark) — something shipped work can enable but never guarantee,
    so it is deliberately outside the stage rollup: a stage's ✅ keeps meaning
    "the planned work shipped", and goal truth lives here, gating the
    OBJECTIVE rows instead (an objective linked to a target that is not
    ``✅ Met`` cannot roll up to ✅).

    A row of the wrong width, or with an empty Target cell, is not read;
    ``unreadable_row_errors`` reports it.
    """
    out: List[OutcomeTarget] = []
    for i, cells, problem in _table_rows(lines, _OUTCOME_TARGETS):
        if problem is not None:
            continue
        kind = next((k for icon, k in _TARGET_STATUS_KIND.items()
                     if cells[3].startswith(icon)), None)
        out.append(OutcomeTarget(i + 1, cells[0], re.findall(r"G\d+", cells[1]), kind))
    return out


def _introducing_stages(cell: str) -> List[int]:
    """Stage numbers in the first ``Stage N`` run of an Introduced by cell."""
    m = _INTRODUCED_BY_RE.search(cell)
    if not m:
        return []
    stages: List[int] = []
    for part in re.split(r"\s*(?:,|/|&|\band\b)\s*", m.group(1), flags=re.IGNORECASE):
        bounds = re.split(r"\s*[-–]\s*", part)
        lo, hi = int(bounds[0]), int(bounds[-1])
        stages.extend(range(lo, hi + 1) if lo <= hi else [lo, hi])
    return stages


def gated_capabilities(lines: List[str]) -> List[GatedCapability]:
    """Rows of the optional Environment-Gated Capability Verification table.

    A row records whether a capability only some environments can exercise has
    had its gated path run for real — which a skip-clean suite and a ✅ stage
    never show. The table gates no stage, objective or claim, so every finding
    about it is a warning (issue #207).

    A row of the wrong width, or with an empty Capability cell, is not read;
    ``unreadable_row_warnings`` reports it.
    """
    out: List[GatedCapability] = []
    for i, cells, problem in _table_rows(lines, _CAPABILITIES):
        if problem is not None:
            continue
        kind = next((k for icon, k in _CAPABILITY_STATUS_KIND.items()
                     if cells[3].startswith(icon)), None)
        profiles = [a or b for a, b in _PROFILE_LINK_RE.findall(cells[1])]
        out.append(GatedCapability(
            i + 1, cells[0], list(dict.fromkeys(profiles)),
            _introducing_stages(cells[2]), kind,
            cells[4].strip() not in _EMPTY_CELL))
    return out


def capability_warnings(lines: List[str], profiles: Dict[str, object]) -> List[str]:
    """``aide check``'s findings over the capability table — warnings, all.

    *profiles* is ``[validation]`` from aide.toml: a row linking to a profile
    that is not there cannot be evaluated by ``aide status --profiles``.
    """
    summary: Dict[int, Optional[str]] = {}
    for line in lines:
        cells = _split_row(line) if line.strip().startswith("|") else []
        if cells and _reads(_STAGE_SUMMARY, cells):
            summary[int(cells[0])] = _icon_status(cells[3])
    out = unreadable_row_warnings(lines)
    for c in gated_capabilities(lines):
        where = f"progress.md:{c.lineno}: capability '{c.text}'"
        if c.kind is None:
            out.append(f"{where} has an unrecognised Status (expected "
                       f"'✅ Verified' or '❓ Unverified')")
        for name in c.profiles:
            if name not in profiles:
                out.append(f"{where} names profile '{name}', which [validation] "
                           f"in aide.toml does not define")
        closed = [s for s in c.stages if summary.get(s) == "complete"]
        if c.kind == "unverified" and closed and not c.noted:
            out.append(f"{where} is still ❓ Unverified under stage {closed[0]}, "
                       f"which is ✅, and its Notes cell records no reason")
    return out


# --------------------------------------------------------------------------- #
# progress.md — editing
# --------------------------------------------------------------------------- #
def _replace_first_icon(line: str, status: str) -> str:
    return _ICON_RE.sub(STATUS_TO_ICON[status], line, count=1)


def _sub_status_cell(line: str, status: str) -> str:
    """Replace the icon in a table row's Status (last) cell only.

    Icons in other cells (a title, an objective description) are plain text and
    must survive the edit untouched.
    """
    head, sep, tail = line.rpartition("|")
    if sep:
        body, sep2, cell = head.rpartition("|")
        if sep2:
            return body + "|" + _ICON_RE.sub(STATUS_TO_ICON[status], cell, count=1) + "|" + tail
    return _ICON_RE.sub(STATUS_TO_ICON[status], line, count=1)


def _set_summary_row(lines: List[str], stage_num: str, status: str) -> None:
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = _split_row(line)
        if len(cells) == 4 and cells[0] == stage_num and _icon_status(cells[3]):
            current = _icon_status(cells[3])
            if current in ("deferred", "excluded"):
                return
            if RANK[status] >= RANK[current]:
                lines[i] = _sub_status_cell(line, status)
            return


def _set_stage_header(lines: List[str], start: int, status: str) -> None:
    line = lines[start]
    current = _header_status(line)
    if current in ("deferred", "excluded"):
        return
    if current is None:
        lines[start] = line.rstrip() + f" — {STATUS_TO_ICON[status]}"
    elif RANK[status] >= RANK[current]:
        lines[start] = _TRAILING_ICON_RE.sub(STATUS_TO_ICON[status], line)


def _same_stage(a: str, b: str) -> bool:
    """Compare two stage numbers, ignoring zero-padding when both are numeric."""
    sa, sb = str(a).strip(), str(b).strip()
    if sa.isdigit() and sb.isdigit():
        return int(sa) == int(sb)
    return sa == sb


def acceptance_boxes(lines: List[str], start: int, end: int) -> List[int]:
    """Line indices of the acceptance checkboxes in one stage section, in order.

    An acceptance box is an *attestation*: a human states that an observable
    criterion holds. It is deliberately not derived from anything — the rollup
    skips checkbox lines (see ``stage_deliverable_statuses``), no ``aide check``
    rule gates a ✅ stage on them, and nothing else reads them. That is why
    ``set_item_status`` no longer ticks them as a side effect of a status
    change: a rollup cannot attest, and auto-ticking made the honest state
    "shipped, but this criterion is not met" impossible to keep — the same
    state Outcome targets exist to express at the objective level.

    Ticking now goes through ``aide progress accept``, which is deliberate,
    logged, and cannot be undone by an unrelated item's status change.
    """
    return [i for i in range(start, end) if _CHECKBOX_RE.match(lines[i])]


def accept_criteria(text: str, stage: str, criteria: Optional[List[int]],
                    evidence: Optional[str] = None) -> Tuple[str, List[str]]:
    """Tick acceptance boxes in *stage*; return (updated text, messages).

    ``criteria`` is a list of 1-based box indices, or None for every box in the
    stage. An already-ticked box is reported and left alone rather than being
    silently counted as newly accepted. Raises ``ValueError`` when the stage or
    an index does not exist — a typo'd stage must not pass as a no-op.

    The stage is matched numerically, so ``accept 6`` finds a section headed
    ``## Stage 06`` — ``stage_sections`` reports the header text verbatim, and
    a caller typing the correct number should not have to guess its padding.
    """
    lines = text.splitlines()
    section = stage_section(lines, stage)
    if section is None:
        raise ValueError(f"no Stage {stage} section in progress.md")
    start, end, _ = section
    boxes = acceptance_boxes(lines, start, end)
    if not boxes:
        raise ValueError(f"Stage {stage} has no acceptance checkboxes")
    wanted = list(range(1, len(boxes) + 1)) if criteria is None else criteria
    for n in wanted:
        if not 1 <= n <= len(boxes):
            raise ValueError(
                f"Stage {stage} has {len(boxes)} acceptance criteria; {n} is out of range")
    messages: List[str] = []
    for n in wanted:
        i = boxes[n - 1]
        m = _CHECKBOX_RE.match(lines[i])
        if m.group("mark") != " ":
            messages.append(f"criterion {n}: already ticked, unchanged")
            continue
        lines[i] = m.group("pre") + "x" + m.group("post")
        if evidence:
            # On the box's LAST line, which is its first only when it does not
            # wrap: an annotation dropped mid-criterion splits the sentence it
            # attests (issue #237).
            last = acceptance_box_last(lines, i, end)
            lines[last] = lines[last].rstrip() + f" *({evidence})*"
        messages.append(f"criterion {n}: accepted")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), messages


#: A correction line under an acceptance box: same shape as an insights.md
#: status trail (§1), and for the same reason — the attestation above it is
#: never reworded, so everything said *about* it afterwards goes underneath,
#: dated, newest last. Indentation is what separates a trail line from the next
#: box, so leading whitespace is required where `_CHECKBOX_RE` forbids it.
_ACCEPT_TRAIL_RE = re.compile(
    r"^(?P<indent>\s+)[-*]\s+\*\*(?P<date>\d{4}-\d{2}-\d{2})\*\*\s*→\s*(?P<text>.*)$")
#: The one trail prefix the tooling reads back. A correction is prose nobody
#: parses; a retraction changes what the box claims, so `check` and `status`
#: have to find it again after the fact.
_RETRACTED_PREFIX = "retracted: "
#: An attestation annotation, as `accept --evidence` writes it: a trailing
#: `*(…)*`. `reword` refuses over one — see `reword_criterion`. The body is
#: greedy and the close anchored at end of line, because evidence carrying its
#: own parentheses is ordinary ("(4 cores)", "(see §6)"): a `[^)]*` body
#: stopped at the first `)` and then matched nothing at all, so the guard
#: opened on exactly the annotations most worth keeping (#143).
_ACCEPT_EVIDENCE_RE = re.compile(r"\*\(.*\)\*\s*$")


#: A continuation line of a wrapped box: indented, non-blank, and not a bullet
#: — a bullet under a box is its trail (or a malformed one), never its text.
_BOX_CONTINUATION_RE = re.compile(r"^\s+(?![-*+]\s)\S")


def acceptance_box_last(lines: List[str], box: int, end: int) -> int:
    """Index of the last physical line of the acceptance box at *box*.

    A criterion is one sentence, and a hand- or template-authored file wraps
    it at a column: the box is its checkbox line **plus** every indented
    non-bullet line that follows, up to the next box, trail line, blank or
    section end (issue #237). Every writer that appends to a box or inserts
    under it starts from here — `accept --evidence`, `amend`, `retract`,
    `reword` — so a wrapped criterion keeps its sentence in one piece.
    """
    last = box
    for i in range(box + 1, end):
        if _BOX_CONTINUATION_RE.match(lines[i]) and not _ACCEPT_TRAIL_RE.match(lines[i]):
            last = i
            continue
        break
    return last


def acceptance_box_trail(lines: List[str], box: int, end: int) -> List[int]:
    """Line indices of the correction trail under the acceptance box at *box*.

    A box owns every indented trail line between it and the next box, header,
    or the end of its section. Returned in file order, so the last element is
    where the newest correction goes after. The scan starts below the box's
    last wrapped line, so a trail under a wrapped box is found, not mistaken
    for prose that ends it.
    """
    out: List[int] = []
    for i in range(acceptance_box_last(lines, box, end) + 1, end):
        if _ACCEPT_TRAIL_RE.match(lines[i]):
            out.append(i)
            continue
        if not lines[i].strip():
            # A blank line inside the trail is tolerated, but only if more
            # trail follows: a blank then prose ends the box.
            if any(_ACCEPT_TRAIL_RE.match(lines[j]) for j in range(i + 1, end)
                   if lines[j].strip()):
                continue
        break
    return out


def _resolve_box(text: str, stage: str, n: int) -> Tuple[List[str], int, int]:
    """``(lines, section_end, box_line_index)`` for criterion *n* of *stage*.

    The shared front half of amend/retract/reword: every one of them resolves
    exactly one box and refuses the same way when it cannot, so the error text
    a consumer sees does not depend on which verb they reached for.
    """
    lines = text.splitlines()
    section = stage_section(lines, stage)
    if section is None:
        raise ValueError(f"no Stage {stage} section in progress.md")
    start, end, _ = section
    boxes = acceptance_boxes(lines, start, end)
    if not boxes:
        raise ValueError(f"Stage {stage} has no acceptance checkboxes")
    if not 1 <= n <= len(boxes):
        raise ValueError(
            f"Stage {stage} has {len(boxes)} acceptance criteria; {n} is out of range")
    return lines, end, boxes[n - 1]


def _append_trail(lines: List[str], box: int, end: int, date: str, note: str) -> str:
    """Insert a dated trail line after the box at *box*; return the line written.

    Indentation follows an existing trail line when there is one, so a file
    that indents by four spaces keeps doing so.
    """
    trail = acceptance_box_trail(lines, box, end)
    indent = "  "
    if trail:
        last = lines[trail[-1]]
        indent = last[: len(last) - len(last.lstrip())]
    written = f"{indent}- **{date}** → {note}"
    lines.insert((trail[-1] if trail else acceptance_box_last(lines, box, end)) + 1,
                 written)
    return written


def amend_criterion(text: str, stage: str, n: int, note: str,
                    date: str) -> Tuple[str, str]:
    """Correct the evidence on a **ticked** acceptance box, append-only.

    The attestation stands; what was recorded about it was wrong or thin. The
    original line is never touched — that is the whole guard, and it is the
    same one insights.md's immutability rule buys: a verb that can only add
    cannot be used to make an inconvenient attestation agree with a shipped
    stage. Over-using it costs verbosity, never truth.

    Refuses on an unticked box, which has no attestation to correct: that is
    `accept` (to make one) or `reword` (to fix the criterion's wording).
    """
    lines, end, box = _resolve_box(text, stage, n)
    m = _CHECKBOX_RE.match(lines[box])
    if m.group("mark") == " ":
        raise ValueError(
            f"Stage {stage} criterion {n} is not ticked, so there is no "
            f"attestation to amend — `accept` records one, `reword` fixes the "
            f"criterion's wording")
    _append_trail(lines, box, end, date, note)
    return ("\n".join(lines) + ("\n" if text.endswith("\n") else ""),
            f"criterion {n}: amended ({date}) — {note}")


def retract_criterion(text: str, stage: str, n: int, reason: str,
                      date: str) -> Tuple[str, str]:
    """Untick a **ticked** acceptance box, keeping the original attestation.

    The sharp half of the pair: the criterion does not hold after all. The box
    goes back to `- [ ]` and both the original annotation and the retraction
    stay visible, so the record reads as "this was claimed, then withdrawn,
    for this reason" rather than as a box that was never ticked.

    A retraction is a *finding*, so `aide progress retract` routes it like one
    — an insights.md `gap` entry in the same commit (§1's Outcome-target rule,
    applied one level down). That is what keeps it cheap to be honest.
    """
    lines, end, box = _resolve_box(text, stage, n)
    m = _CHECKBOX_RE.match(lines[box])
    if m.group("mark") == " ":
        raise ValueError(
            f"Stage {stage} criterion {n} is already unticked — nothing to retract")
    written = _append_trail(lines, box, end, date, _RETRACTED_PREFIX + reason)
    # The trail was inserted below the box, so the box index still addresses it.
    lines[box] = m.group("pre") + " " + m.group("post")
    return ("\n".join(lines) + ("\n" if text.endswith("\n") else ""),
            f"criterion {n}: retracted — {reason}")


def reword_criterion(text: str, stage: str, n: int, new_text: str) -> Tuple[str, str]:
    """Reword an **unticked, unevidenced** acceptance criterion in place.

    The one amendment that edits rather than appends, and it is safe for
    exactly one reason: nothing has been claimed yet. The precondition is
    mechanical, so no instruction has to carry it — a box that is ticked, or
    annotated, or already carries a correction trail, has an attestation
    hanging off its wording, and rewording it would silently re-point that
    attestation at a different criterion.
    """
    if "\n" in new_text or "\r" in new_text:
        raise ValueError(
            "the criterion text may not contain a line break — it is written "
            "into a single checkbox line, and a break would split one "
            "criterion into two and renumber every box below it")
    lines, end, box = _resolve_box(text, stage, n)
    m = _CHECKBOX_RE.match(lines[box])
    last = acceptance_box_last(lines, box, end)
    # The wording is the whole box, continuation lines included: an annotation
    # sits on its last line, and the rewrite replaces every line of it.
    body = " ".join([m.group("post")[1:].strip()]
                    + [lines[i].strip() for i in range(box + 1, last + 1)])
    if m.group("mark") != " ":
        raise ValueError(
            f"Stage {stage} criterion {n} is ticked; its wording is what an "
            f"attestation was made against. Retract it first (`aide progress "
            f"retract`) if the criterion itself was wrong")
    annotation = _ACCEPT_EVIDENCE_RE.search(body)
    if annotation:
        raise ValueError(
            f"Stage {stage} criterion {n} carries an annotation "
            f"({annotation.group(0).strip()}), so "
            f"something has already been recorded against this wording")
    if acceptance_box_trail(lines, box, end):
        raise ValueError(
            f"Stage {stage} criterion {n} carries a correction trail, so "
            f"something has already been recorded against this wording")
    old = body.strip()
    lines[box] = m.group("pre") + m.group("mark") + "] " + new_text.strip()
    del lines[box + 1:last + 1]
    return ("\n".join(lines) + ("\n" if text.endswith("\n") else ""), old)


def retracted_criteria(lines: List[str]) -> List[Tuple[str, int, str, str]]:
    """``(stage, criterion_index, date, reason)`` per retracted acceptance box.

    Read back out of the trail so `check` and `status` can surface it: a
    retraction that only ever appeared in one commit's diff is exactly the
    quiet the append-only rule exists to prevent.
    """
    out: List[Tuple[str, int, str, str]] = []
    for start, end, num in stage_sections(lines):
        for n, box in enumerate(acceptance_boxes(lines, start, end), start=1):
            for i in acceptance_box_trail(lines, box, end):
                tm = _ACCEPT_TRAIL_RE.match(lines[i])
                note = tm.group("text")
                if note.startswith(_RETRACTED_PREFIX):
                    out.append((num, n, tm.group("date"),
                                note[len(_RETRACTED_PREFIX):].strip()))
    return out


#: The roadmap block whose bullets become a stage's acceptance boxes, and the
#: prefix that marks a bullet as an Outcome target instead (§1 → progress.md:
#: a measured outcome is deliberately NOT an acceptance box, so it must not
#: consume a box index when the two files are lined up).
_ROADMAP_ACCEPTANCE_RE = re.compile(r"^\*\*Validation\s*/\s*acceptance\.?\*\*", re.I)
_ROADMAP_BLOCK_END_RE = re.compile(r"^\*\*\S")
_ROADMAP_TARGET_RE = re.compile(r"^\s*[-*]\s+Target:", re.I)
#: Authoring guidance in the template — `_italic line_`, read then replaced.
#: It sits inside the block and is not a criterion.
_GUIDANCE_RE = re.compile(r"^\s*_.*_\s*$")


def roadmap_acceptance_bullets(lines: List[str], stage: str) -> Optional[List[int]]:
    """Line indices of *stage*'s acceptance bullets in roadmap.md, in order.

    ``None`` when the stage has no Validation / acceptance block at all — a
    roadmap that never mirrored the criteria, which is a different situation
    from one whose block disagrees with progress.md and must not be treated
    the same way (see ``_cmd_progress_reword``).

    ``Target:`` bullets are skipped: §1 routes a measured outcome to the
    Outcome-targets table precisely so it is not an acceptance box, so
    counting one here would slide every index below it by one.
    """
    section = stage_section(lines, stage)
    if section is None:
        return None
    start, end, _ = section
    head = next((i for i in range(start, end)
                 if _ROADMAP_ACCEPTANCE_RE.match(lines[i])), None)
    if head is None:
        return None
    out: List[int] = []
    for i in range(head + 1, end):
        line = lines[i]
        if _ROADMAP_BLOCK_END_RE.match(line):
            break
        if not line.strip() or _GUIDANCE_RE.match(line):
            continue
        if _ROADMAP_TARGET_RE.match(line):
            continue
        if re.match(r"^\s*[-*]\s+\S", line):
            out.append(i)
    return out


def reword_roadmap_bullet(text: str, stage: str, n: int, new_text: str,
                          expected: int) -> Tuple[Optional[str], Optional[str]]:
    """Mirror a reworded criterion into roadmap.md; ``(new_text, error)``.

    Returns ``(None, None)`` when the stage has no acceptance block to mirror —
    nothing to keep in step — and ``(None, <reason>)`` when there is one but it
    cannot be lined up with progress.md's *expected* box count. The caller
    writes neither file in that case: a rewording that lands in one document
    and not the other leaves exactly the two-file drift this verb exists to
    prevent.
    """
    lines = text.splitlines()
    bullets = roadmap_acceptance_bullets(lines, stage)
    if bullets is None:
        return None, None
    if len(bullets) != expected:
        return None, (
            f"roadmap.md stage {stage} lists {len(bullets)} acceptance "
            f"bullet{'' if len(bullets) == 1 else 's'} but progress.md has "
            f"{expected} box{'' if expected == 1 else 'es'}, so criterion {n} "
            f"cannot be matched across the two. Line them up by hand, then "
            f"re-run — nothing was written")
    i = bullets[n - 1]
    m = re.match(r"^(?P<pre>\s*[-*]\s+)(?P<body>.*)$", lines[i])
    lines[i] = m.group("pre") + new_text.strip()
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), None


def acceptance_drift_warnings(ddir: Path, plines: List[str]) -> List[str]:
    """Stages whose acceptance box count disagrees with roadmap.md's mirror.

    §1 → progress.md says the Acceptance boxes come "from the matching roadmap
    stage", and `templates/roadmap.md` says the Validation / acceptance bullets
    become those boxes — the one mirror in §1 nothing enforced (issue #142).
    The observed drift: a consumer's stage carried a fourth, load-bearing box
    its roadmap never grew, and there was no moment at which anything would
    have said so. Since 1.35.0 the silence also has teeth: `aide progress
    reword` matches boxes to bullets by index and refuses on a drifted stage,
    so a consumer met a refusal with no tool that would say which stages drift
    or where.

    Counts, not text: comparing wording would fire on every honest tightening
    of a criterion's prose, which is exactly what `reword` exists to make
    cheap. The count is the signal that a criterion was *added or dropped* on
    one side only.

    A warning, never an error — a stage may legitimately be mid-replan, and a
    document set that was fine yesterday must not start failing today. Silent
    when roadmap.md is absent, when a stage has no roadmap section, and when
    its section has no Validation / acceptance block at all: no mirror is a
    different situation from a mirror that disagrees, and
    ``roadmap_acceptance_bullets`` keeps the two apart for `reword` already.
    """
    rpath = ddir / "roadmap.md"
    if not rpath.is_file():
        return []
    rlines = rpath.read_text(encoding=_ENCODING).splitlines()
    out: List[str] = []
    for start, end, stage in stage_sections(plines):
        bullets = roadmap_acceptance_bullets(rlines, stage)
        if bullets is None:
            continue
        boxes = len(acceptance_boxes(plines, start, end))
        if boxes != len(bullets):
            out.append(
                f"stage {stage}: progress.md has {boxes} acceptance "
                f"box{'' if boxes == 1 else 'es'} but roadmap.md's Validation "
                f"/ acceptance block lists {len(bullets)} "
                f"bullet{'' if len(bullets) == 1 else 's'} — a criterion was "
                f"added or dropped on one side only; line the two up by hand "
                f"('aide progress reword' refuses on this stage until they "
                f"agree)")
    return out


def _objective_stages(delivered_by: str) -> List[str]:
    return re.findall(r"\bStage[s]?\s+([\d,\s]+)", delivered_by)


def _apply_objective_rollup(lines: List[str], stage_status: Dict[str, str]) -> None:
    # An objective linked to an outcome target that is not ✅ Met can never
    # roll up to ✅: its stages shipping is necessary but not sufficient.
    blocked = {g for t in outcome_targets(lines) if t.kind != "met"
               for g in t.objectives}
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = _split_row(line)
        gm = re.match(r"G\d+", cells[0]) if len(cells) == 3 else None
        if gm and _icon_status(cells[2]):
            nums: List[str] = []
            for chunk in re.findall(r"\d+", cells[1]):
                nums.append(chunk)
            if not nums:
                continue
            current = _icon_status(cells[2])
            if current in ("deferred", "excluded"):
                continue
            statuses = [stage_status.get(n) for n in nums if stage_status.get(n)]
            if statuses and all(s == "complete" for s in statuses):
                derived = "complete"
            elif any(s in ("complete", "in-progress", "in-review") for s in statuses):
                derived = "in-progress"
            else:
                derived = current
            if derived == "complete" and gm.group(0) in blocked:
                derived = "in-progress"
            if RANK[derived] >= RANK[current]:
                lines[i] = _sub_status_cell(line, derived)


def _spec_stage_and_title(repo_root: Path, config, number: int) -> Tuple[Optional[str], Optional[str]]:
    """(stage, title) from the item's spec header, best effort."""
    idir = docs_dir(repo_root, config) / "items"
    specs = item_spec_paths(idir, number)
    if not specs:
        return None, None
    text = specs[0].read_text(encoding=_ENCODING)
    tm = re.search(r"^#\s+Item\s+0*" + str(number) + r"\s*[—–-]\s*(.+?)\s*$", text, re.MULTILINE)
    sm = re.search(r"\*\*Stage:\*\*\s*(\d+)", text)
    return (sm.group(1) if sm else None), (tm.group(1) if tm else None)


def insert_item_reference(text: str, number: int, stage: str, title: str) -> Optional[str]:
    """Append a planned deliverable bullet for item ``number`` to the given
    stage's Deliverables block (used when a queue back-fill was missed, so
    ``progress set`` can self-heal instead of hard-erroring). Returns the
    updated text, or None when the stage section / Deliverables block is
    missing — that stays a loud error."""
    lines = text.splitlines()
    for start, end, snum in stage_sections(lines):
        if snum != str(stage):
            continue
        insert_at = next((i + 1 for i in range(start, end)
                          if lines[i].strip().startswith("**Deliverables")), None)
        # After the last bullet's WHOLE span, continuations included. Icon
        # line + 1 used to split a wrapped bullet in two — cosmetic while any
        # reference on any line attributed, but under the trailing-marker rule
        # (issue #99) the split strands the new bullet's marker mid-span and
        # hands the wrapped bullet's marker to the wrong owner.
        spans = _deliverable_bullet_spans(lines[start:end])
        if spans:
            insert_at = start + spans[-1][1] + 1
        if insert_at is None:
            return None
        lines.insert(insert_at, f"- 📋 {title}. *(Item {number:03d})*")
        return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return None


class BulletSplit(NamedTuple):
    """One shared-marker bullet ``_split_multi_item_bullets`` desugared.

    ``marker`` is the marker the bullet carried (``*(Items 044, 045)*``);
    ``copies`` is one ``(item number, 1-based line)`` per bullet it became,
    the line being the copy's first line in the text the split produced. The
    copies all carry the prose the shared bullet had, which described N items
    at once and now stands under each of them alone — the caller's job is to
    say so, since the file cannot (issue #169).
    """

    marker: str
    copies: List[Tuple[int, int]]


def _split_multi_item_bullets(lines: List[str], num: int, status: str,
                              splits: Optional[List[BulletSplit]] = None) -> List[str]:
    """One bullet, one item: desugar a bullet that owns ``num`` *and* siblings.

    A trailing marker may name several items — ``*(Items 016, 017)*``, the form
    §1 → progress.md blesses and `/aide-create-queue` step 8 recommends — but a
    bullet carries ONE icon, and that icon is the status cell. So flipping the
    bullet for 016 also completed 017: never specced, never built, thereafter
    read as ✅ by everything that parses the file, and silently discounted from
    its queue's open count (issue #131). The engine's own writer had already
    modelled one item per bullet — `insert_item_reference` appends a singular
    marker — so the shape it told authors to write was one its status machinery
    could not represent.

    The form stays legal and desugars here: the bullet becomes one bullet per
    item, same text, one ``*(Item NNN)*`` each, in the marker's order. The item
    being flipped then moves alone and its siblings keep the status they had —
    the sibling protection issue #99 gave a prose mention, given to the list
    form that actually attributes.

    Only a flip that would ADVANCE the bullet splits it. A `progress set` that
    changes nothing must rewrite nothing: re-running one, or setting a status
    the bullet already holds, is not a reason to reshape a consumer's file.

    What the split writes is the shared prose, verbatim, N times. It cannot be
    otherwise — the bullet had one sentence for N items, and the engine has no
    other — but that leaves N−1 copies whose text describes work that is not
    the item named on them, and once one is ticked the file states something
    undone as done (issue #169: a consumer's ✅ line for item 045 described
    items 046/047's still-open work). So every split is *recorded* in
    ``splits``, and the callers print the copies as a chore that the author
    now owes; ``identical_deliverable_warnings`` keeps reporting them from
    `aide check` until each copy's prose is its own.
    """
    for start, last in reversed(_deliverable_bullet_spans(lines)):
        marker = _BULLET_MARKER_RE.search(lines[last])
        if marker is None:
            continue
        nums = list(dict.fromkeys(_referenced_item_numbers(marker.group(0))))
        if num not in nums or len(nums) < 2:
            continue
        # A range wider than the typo limit contributes only its endpoints, so
        # `nums` is not what the author wrote: `*(Items 044-999)*` would grow a
        # bullet for a phantom item 999, indistinguishable from a real one and
        # thereafter counted by `check`, `claim` and every queue rollup. Writing
        # fiction into the tracked document is worse than the shared cell this
        # function exists to remove, so a malformed marker keeps the old
        # behaviour and this leaves it exactly as the author typed it.
        #
        # Whole-bullet, deliberately: in `*(Items 006, 044-999)*` the sound half
        # keeps the shared cell too. Splitting the good elements while preserving
        # the malformed one is a lot of machinery for a marker whose own author
        # has already mistyped it, and the loud version — refusing the flip — is
        # worse, since it would strand a real item behind a typo in prose.
        if _has_typo_range(marker.group(0)):
            continue
        current = ICON_TO_STATUS[_BULLET_RE.match(lines[start]).group("icon")]
        if not current or RANK[status] <= RANK[current]:
            continue
        head = lines[last][:marker.start()]
        # Whatever followed the last `)*` — the sentence-ending period the
        # marker regex tolerates — belongs to every copy, not just the first.
        matched = marker.group(0)
        tail = matched[len(matched.rstrip(" \t.")):]
        block: List[str] = []
        copies: List[Tuple[int, int]] = []
        span = last + 1 - start
        for n in nums:
            copy = lines[start:last + 1]
            copy[-1] = f"{head}*(Item {n:03d})*{tail}"
            copies.append((n, start + len(block) + 1))
            block.extend(copy)
        lines[start:last + 1] = block
        if splits is not None:
            # Spans are walked from the bottom, so a split here shifts every
            # copy already recorded below it by the lines this one grew.
            grown = len(block) - span
            splits[:] = [BulletSplit(s.marker, [(n, ln + grown if ln > start else ln)
                                                for n, ln in s.copies])
                         for s in splits]
            splits.append(BulletSplit(matched.rstrip(" \t."), copies))
    return lines


def set_item_status(text: str, num: int, status: str,
                    splits: Optional[List[BulletSplit]] = None) -> str:
    """Flip item NNN's deliverable bullet(s) to ``status`` and roll stages up.

    ``status`` is ``in-progress``, ``in-review`` or ``complete``. Updates summary/header/
    objective rows only for stages that fully complete. Never downgrades an
    existing status (additive log), and never touches an acceptance checkbox —
    those are human attestations, ticked only by ``aide progress accept``.

    A bullet whose marker names several items is split into one bullet per item
    first (see ``_split_multi_item_bullets``), so no sibling is carried along by
    a flip it did not earn. Each such split is appended to ``splits`` when the
    caller passes a list: the copies carry prose written for all the items at
    once, and the caller is the one who can say so (issue #169).
    """
    lines = text.splitlines()
    # A marker naming several items is one status cell for all of them, so the
    # bullet is desugared into one bullet per item BEFORE anything flips
    # (issue #131). After this the flip below can only move `num`.
    lines = _split_multi_item_bullets(lines, num, status, splits)
    # Flip the icon of every bullet whose trailing marker names this item —
    # the same ownership rule `_parse_item_status` reads by (issue #99), so a
    # bullet that merely mentions the item in prose is never flipped.
    for start, last in _deliverable_bullet_spans(lines):
        if num not in _bullet_marker_item_numbers(lines[last]):
            continue
        current = ICON_TO_STATUS[_BULLET_RE.match(lines[start]).group("icon")]
        if current and RANK[status] > RANK[current]:
            lines[start] = _replace_first_icon(lines[start], status)

    # Recompute rollups for every stage (never downgrading).
    stage_status: Dict[str, str] = {}
    for start, end, stage_num in stage_sections(lines):
        derived = rollup_status(stage_deliverable_statuses(lines, start, end))
        if derived is None:
            continue
        stage_status[stage_num] = derived
        _set_stage_header(lines, start, derived)
        _set_summary_row(lines, stage_num, derived)
    _apply_objective_rollup(lines, stage_status)

    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


# --------------------------------------------------------------------------- #
# Item & queue file naming — the filename half of the branch helpers
# --------------------------------------------------------------------------- #
#: Item numbers and queue numbers share one namespace with no syntactic marker
#: between them. `_branch_item_number`/`_is_queue_branch` centralise that hazard
#: for BRANCH names (and their docstrings record what it cost to learn); these
#: four do the same for FILE names, which were previously re-derived as raw
#: globs and f-strings at thirteen call sites. Nothing here fixes a live bug —
#: every one of those sites was correct. The point is that the convention is now
#: written down once, so the 1.13.0 class of misread has one place to reappear
#: and one place to be tested, and a change to the convention is a change here.


#: The literal tokens every queue name is built from — the file stem, both
#: branch shapes, and the regexes that read them back. Written once so that a
#: change to the convention is a change *here* and everything moves with it;
#: restating "queue-" in a constructor and again in a recogniser is exactly the
#: drift 1.15.0 removed for filenames and this block removes for branches.
_QUEUE_TOKEN = "queue-"
_SPECS_TOKEN = "specs-"


def queue_name(number: int) -> str:
    """``queue-NNN`` — the stem a queue file and its status prose both use."""
    return f"{_QUEUE_TOKEN}{number:03d}"


def queue_number(path: Path) -> Optional[int]:
    """Queue number named by *path*, or None when it names no queue.

    Anchored at the start of the stem, for the same reason the branch helpers
    are: an unanchored digit search reads ``specs-queue-015.md`` or a consumer's
    ``notes-on-queue-016.md`` as a queue file. Tolerates a trailing slug
    (``queue-016-stage-27.md``) so the deferred naming harmonisation does not
    have to touch the parser, and unpadded digits on read.
    """
    m = re.match(re.escape(_QUEUE_TOKEN) + r"0*(\d+)(?:-|$)", path.stem)
    return int(m.group(1)) if m else None


def iter_queue_paths(qdir: Path) -> List[Path]:
    """Every queue file under *qdir*, in queue-number order ([] if no dir).

    Ordered by the parsed number rather than lexicographically, so the order
    stays the number's even once a name carries a slug after it.
    """
    if not qdir.is_dir():
        return []
    numbered = [(n, p.name, p) for p, n in
                ((p, queue_number(p)) for p in qdir.glob(f"{_QUEUE_TOKEN}*.md"))
                if n is not None]
    return [p for _, _, p in sorted(numbered)]


def queue_path(qdir: Path, number: int) -> Optional[Path]:
    """The queue file for *number*, or None when it does not exist.

    **Resolves by glob, never by construction.** Constructing
    ``qdir / f"queue-{n:03d}.md"`` hardcodes the assumption that the number is
    the whole name; resolving means a slugged queue file is found by the same
    call, and a caller that wants a name for an error message asks
    `queue_name` for one instead of half-building a path it may not have.
    """
    matches = [p for p in iter_queue_paths(qdir) if queue_number(p) == number]
    return matches[0] if matches else None


def item_spec_paths(idir: Path, number: int) -> List[Path]:
    """Spec files for item *number* under *idir* — ``items/NNN-*.md``, sorted.

    Returns a list because the convention permits only one and the filesystem
    does not; every caller takes ``[0]`` and the extras are a consumer's
    problem, not something to raise over here.
    """
    if not idir.is_dir():
        return []
    return sorted(idir.glob(_item_spec_glob(number)))


def _item_spec_glob(number: int) -> str:
    return f"{number:03d}-*.md"


def item_spec_number(path: Path) -> Optional[int]:
    """The item number whose `item_spec_paths` lookup returns *path*, or None.

    A file under ``items/`` is a spec only if a lookup can find it, so the
    number is read off the filename's leading digits and then **confirmed
    against the lookup's own glob**, never a second pattern: ``12-foo.md`` and
    ``0012-foo.md`` both read as 12 and neither answers ``012-*.md``, so both
    are None, exactly as ``notes.md`` is (issue #228). `PurePath.match` applies
    the platform's case rule, as the glob does.
    """
    m = re.match(r"\d+", path.name)
    if not m:
        return None
    number = int(m.group(0))
    return number if PurePath(path.name).match(_item_spec_glob(number)) else None


def _unfindable_spec_warning(path: Path) -> str:
    """`aide check`'s warning for a file under ``items/`` no lookup returns."""
    m = re.match(r"(\d+)[-_ ]*(.*)$", path.name)
    if m and m.group(2).lower() not in ("", ".md"):
        fix = f"rename it to {int(m.group(1)):03d}-{m.group(2)}"
    else:
        fix = "rename it NNN-<slug>.md, NNN its item number zero-padded to three digits"
    return (f"items/{path.name}: not named NNN-<slug>.md, so `aide scope`, "
            f"`aide claim` and `aide check --queue` never find it and no other "
            f"spec lint reads it — {fix}")


# --------------------------------------------------------------------------- #
# queue.md helpers
# --------------------------------------------------------------------------- #
_QUEUE_STATUS_RE = re.compile(r"^>\s*\*\*Status:\*\*\s*(.*)$")
_QUEUE_ITEM_RE = re.compile(r"^###\s+Item\s+0*(\d+)\b", re.MULTILINE)


def queue_status(text: str) -> Optional[str]:
    for line in text.splitlines():
        m = _QUEUE_STATUS_RE.match(line)
        if m:
            return m.group(1).strip()
    return None


def is_live_queue(text: str) -> bool:
    status = queue_status(text) or ""
    return status.lower().startswith("live")


def queue_item_numbers(text: str) -> List[int]:
    return [int(m.group(1)) for m in _QUEUE_ITEM_RE.finditer(text)]


def queue_is_open(text: str, item_status: Dict[int, str]) -> bool:
    """Derived queue state: open iff any item is 📋/🚧/🔍 per progress.md.

    🔍 counts as open: an item whose PR is still awaiting review is not work the
    queue is finished with, and marking the queue completed over it would strand
    the review.

    Queue state is DERIVED, never declared — a ``> **Status:**`` line in a
    queue file is decorative (kept for human readers), and the "live" queue is
    simply the lowest-numbered open one. An item progress.md doesn't know yet
    counts as planned, so a freshly wired queue is open.
    """
    return any(item_status.get(n, "planned") in ("planned", "in-progress", "in-review")
               for n in queue_item_numbers(text))


def _progress_item_status(repo_root: Path, config) -> Dict[int, str]:
    path = docs_dir(repo_root, config) / "progress.md"
    if not path.is_file():
        return {}
    _, _, item_status = _parse_item_status(path.read_text(encoding=_ENCODING).splitlines())
    return item_status


def tidy_queue_text(text: str, superseded_by: int, date: str) -> str:
    """Rewrite a queue's Status line to 'Completed — superseded by queue-NNN'."""
    new_status = (f"> **Status:** ✅ Completed — superseded by "
                  f"{queue_name(superseded_by)} ({date}).")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if _QUEUE_STATUS_RE.match(line):
            lines[i] = new_status
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    # No status line: insert after the H1.
    for i, line in enumerate(lines):
        if line.startswith("# "):
            lines.insert(i + 1, new_status)
            break
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


# --------------------------------------------------------------------------- #
# check
# --------------------------------------------------------------------------- #
#: An AIDE slot is a bare ``{{name}}``. The negative lookbehind exempts a `$`
#: immediately before the braces — GitHub Actions expression syntax, which is
#: foreign syntax a living document may legitimately quote when it documents a
#: workflow. Without it, an item spec explaining what a CI step runs, or an
#: insight recording a workflow's arguments, turns `aide check` red on prose
#: that is correct as written, and the only remedy is to stop naming the real
#: syntax — making the documentation worse exactly where accuracy matters.
#:
#: Suppressing matches inside backtick code spans would be the wrong fix: the
#: item template's own `Suggested branch` line carries a genuine slot inside a
#: code span (``aide/{{nnn}}-descriptive-name``), so that rule would make a
#: real unfilled slot invisible. AIDE slots are never `$`-prefixed, so keying
#: on the `$` is precise in both directions.
_TEMPLATE_SLOT_RE = re.compile(r"(?<!\$)\{\{[^}]*\}\}")


def template_residue_errors(ddir: Path) -> List[str]:
    """Flag unfilled ``{{slot}}`` template markers left in generated documents.

    Templates use ``{{slot-name}}`` for values an author must fill in (see
    ``.aide/templates/``); a real ``docs/aide/`` document should never contain
    one. Scanning for the literal ``{{`` is deterministic and cheap — the
    format contract's answer to "did someone forget to fill in the template".
    """
    errors: List[str] = []
    if not ddir.is_dir():
        return errors
    for path in sorted(ddir.rglob("*.md")):
        text = path.read_text(encoding=_ENCODING)
        for lineno, line in enumerate(text.splitlines(), start=1):
            for m in _TEMPLATE_SLOT_RE.finditer(line):
                errors.append(
                    f"{path.relative_to(ddir).as_posix()}:{lineno}: "
                    f"unfilled template slot {m.group(0)}"
                )
    return errors


_INSIGHT_TYPES = ("knowledge", "defect", "gap", "automation", "framework")
#: What may stand between ``*(`` and the date: anything but a close-paren or a
#: line break, or nothing at all.
#:
#: Deliberately a slug and not a grammar. Only the **date** is load-bearing —
#: ``archive`` cuts on it and ``list`` prints it; nothing routes on the item
#: number — while the frame around the provenance already pins the checkbox, a
#: known type, the dash, a non-empty claim and an ISO date. A provenance that
#: fails an enumerated shape inside that frame names no defect anyone can act
#: on.
#:
#: Enumerating the accepted forms means predicting what an author will write,
#: and the cost of predicting wrong is not the usual one: conventions.md §1
#: makes the captured line immutable, so a rejected provenance is a warning
#: that can never be cleared, on an entry ``archive`` then declines to move
#: (see ``archive_insight_text``). Until 1.21.0 the shape was ``item NNN``
#: alone, which rejected two provenances the loop produces routinely —
#: ``queue-NNN`` for planning done before any item exists, and
#: ``items NNN-NNN`` for a finding that genuinely spans several. Both were
#: unfixable in place, since collapsing a range to one item is a rewording
#: *and* destroys the provenance the marker exists to record.
#:
#: Canonical forms are still documented (conventions.md §1, and the template's
#: header) so captures converge — guidance, which the reader can follow, rather
#: than enforcement, which the immutability rule makes permanent.
#:
#: It must still end in a non-blank character, so a stray comma — ``*(   ,
#: 2026-01-01)*`` — is a shape warning rather than a silently accepted
#: provenance that says nothing. Free-form is not the same as empty.
_INSIGHT_SOURCE = r"[^)\n]*[^\s)\n]"
#: What may stand **after** the date, in the same marker: the conditions the
#: observation was made under, conventionally ``engine X.Y.Z`` — one read of
#: ``.aide/VERSION`` at capture time (conventions.md §1).
#:
#: The date cannot proxy for it: a project runs an engine for as long as it
#: likes after a release, so two entries captured the same week may sit either
#: side of a restructure. It matters most on a ``framework`` entry, which is
#: triaged in another repo, months later, by someone with no other way to know.
#:
#: Free-form for the same reason the provenance is, and the reason is sharper
#: here: this component arrived after entries already existed, so a grammar
#: (``engine`` plus a SemVer triple, say) would reject a consumer's own honest
#: spelling permanently — the claim line is immutable, and the warning could
#: never be cleared. Conventional, not grammatical.
#:
#: Free-form everywhere except one character: ``)`` closes the marker, so a note
#: containing one — ``engine 1.2.3 (rc1)`` — does not parse, drawing a permanent
#: shape warning and losing the date that ``archive`` and ``tick`` read. Write
#: the note without parentheses.
_INSIGHT_NOTE = r"[^)\n]*[^\s)\n]"
#: A provenance naming exactly one item — the only form that yields an item
#: *number*. A range, a queue, or anything else leaves ``item`` ``None``, as a
#: bare date always has.
_INSIGHT_ONE_ITEM_RE = re.compile(r"^[Ii]tems? (\d+)$")
# "- [ ] <type> — <one line> *(item NNN, YYYY-MM-DD, engine X.Y.Z)*"; the
# provenance and the trailing note are both free-form and optional, and ticked
# entries append " → <where it landed>".
_INSIGHT_RE = re.compile(
    r"^- \[[ xX]\] (?:" + "|".join(_INSIGHT_TYPES) + r") [—–-] .+"
    r"\*\((?:" + _INSIGHT_SOURCE + r", )?\d{4}-\d{2}-\d{2}"
    r"(?:, " + _INSIGHT_NOTE + r")?\)\*"
)


def insight_warnings(ddir: Path) -> List[str]:
    """Shape-check ``insights.md`` (the compound-engineering inbox), if present.

    Non-blocking: capture must stay cheap, so a malformed entry is a warning,
    never an error. Every ``- `` bullet in the file is expected to be an entry.

    **The live file only.** ``aide insights archive`` moves closed entries into
    ``insights/archive-YYYY-QN.md``, and those are deliberately not re-checked
    here: an archived claim is frozen, so a warning on one names a defect no
    one may fix — the immutability rule forbids rewording the line. (Unfilled
    ``{{slot}}`` markers *are* still caught in archives, because
    ``template_residue_errors`` walks the whole tree; that one is a genuine
    error wherever it appears.)
    """
    path = ddir / "insights.md"
    if not path.is_file():
        return []
    out: List[str] = []
    for lineno, line in enumerate(path.read_text(encoding=_ENCODING).splitlines(), start=1):
        if not line.startswith("- "):
            continue
        if not _INSIGHT_RE.match(line):
            out.append(
                f"insights.md:{lineno}: entry does not match "
                f"'- [ ] <{'|'.join(_INSIGHT_TYPES)}> — <one line> "
                f"*(<where it came from>, YYYY-MM-DD, engine X.Y.Z)*' — the "
                f"provenance and the trailing engine version are free-form "
                f"and may be omitted; the ISO date may not"
            )
    return out


#: The three git conflict markers that can never be legitimate markdown at the
#: start of a line, and so are safe to lint on. ``=======`` is deliberately
#: **not** among them: it is also a setext heading underline, and a lint that
#: fires on a heading is a lint a reader learns to skim. A real conflict always
#: carries an opener and a closer, so nothing is missed by leaving it out.
_CONFLICT_OPEN_RE = re.compile(r"^<{7}(?: |$)")
_CONFLICT_BASE_RE = re.compile(r"^\|{7}(?: |$)")
_CONFLICT_SEP_RE = re.compile(r"^={7}$")
_CONFLICT_CLOSE_RE = re.compile(r"^>{7}(?: |$)")
_CONFLICT_LINT_RES = (_CONFLICT_OPEN_RE, _CONFLICT_BASE_RE, _CONFLICT_CLOSE_RE)


def conflict_marker_errors(ddir: Path) -> List[str]:
    """Flag git conflict markers committed into ``insights.md`` — an error.

    The inbox is append-only by contract (conventions.md §1 → ``insights.md``),
    so two branches that each captured an insight conflict on every merge, and
    the conflict is always the same trivial shape. That makes a *committed*
    marker a format-contract error rather than the usual warning. `parse_insights`
    skips the marker lines themselves — they do not start with ``- `` — which
    is worse than misreading them: **both sides' entries land in one numbered
    list**, so ``list`` numbers straight across the halves and the ``N`` a
    reader takes from it points ``tick`` at a different claim than the one they
    read. ``archive`` will happily move an entry out from between the markers
    and leave them behind.

    An error, unlike the shape warnings above, because it is always fixable —
    ``aide insights resolve`` is the fix, and the message says so. The live
    file only, for the reason ``insight_warnings`` gives: the resolver works on
    the file the loop appends to, and an archive is frozen.
    """
    path = ddir / "insights.md"
    if not path.is_file():
        return []
    out: List[str] = []
    for lineno, line in enumerate(path.read_text(encoding=_ENCODING).splitlines(), start=1):
        if any(rx.match(line) for rx in _CONFLICT_LINT_RES):
            out.append(
                f"insights.md:{lineno}: an unresolved git conflict marker "
                f"({line.split(' ')[0]}) — the inbox is append-only, so this "
                f"merge is a union of entries; resolve it with "
                f"`python .aide/scripts/aide.py insights resolve` (add "
                f"--dry-run to see it first) rather than by hand, which is "
                f"where a captured claim gets reworded"
            )
    return out


#: An entry's full shape, parsed rather than merely validated: the claim, its
#: provenance, and the optional " → <where it landed>" pointer a tick appends.
#: ``text`` is non-greedy up to the provenance so a claim may itself contain
#: parentheses; ``tail`` is whatever follows it, which is the pointer or "".
#: The pointer separator, written by `tick` and by hand before it existed.
_INSIGHT_POINTER = " → "
#: ``source`` is the provenance verbatim (``None`` for a bare date), because a
#: listing that re-derives it from an item number can print nothing else back.
_INSIGHT_ENTRY_HEAD = (
    r"^- \[(?P<mark>[ xX])\] (?P<type>" + "|".join(_INSIGHT_TYPES) + r") [—–-] "
    r"(?P<text>.+?)\*\((?:(?P<source>" + _INSIGHT_SOURCE + r"), )?"
    r"(?P<date>\d{4}-\d{2}-\d{2})(?:, (?P<note>" + _INSIGHT_NOTE + r"))?\)\*"
)
#: Which marker is the provenance, when a line carries more than one.
#:
#: ``text`` is non-greedy, so it stops at the *first* ``*(…, date)*`` — and a
#: free-form provenance means an aside inside the claim can wear that shape:
#: ``… default is *(prod, 2020-01-01)* not *(item 099, 2026-07-26)*`` would take
#: the aside's date and file the entry in the wrong archive quarter, silently,
#: since the line still parses. Greedy is not the answer either — it takes the
#: *last* marker, which a pointer may equally carry (``→ see *(note, …)*``).
#:
#: So neither position decides it: the provenance is the marker that leaves a
#: **well-formed tail** — nothing, or the ``→`` pointer `tick` writes. That is
#: the strict pattern, and it resolves both cases above. A tail matching
#: neither is a hand-written entry predating `tick` (``*(…)* — landed in X``);
#: the loose pattern accepts it exactly as before, so widening the provenance
#: costs no entry its parse.
_INSIGHT_FULL_RE = re.compile(_INSIGHT_ENTRY_HEAD + r"(?P<tail>\s*(?:→.*)?)$")
_INSIGHT_FULL_LOOSE_RE = re.compile(_INSIGHT_ENTRY_HEAD + r"(?P<tail>.*)$")
#: A status-trail line: indented under its entry, newest last (conventions.md
#: §1). Indentation is what distinguishes it from the next entry, so this must
#: require leading whitespace where the entry pattern forbids it.
_INSIGHT_TRAIL_RE = re.compile(r"^\s+[-*]\s")
#: An ISO date, validated rather than trusted: `archive --before` compares it
#: lexicographically against every entry's date, which is only equivalent to
#: comparing dates while both sides are known to be YYYY-MM-DD.
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class InsightEntry(NamedTuple):
    """One inbox entry: the parsed claim plus where it sits in the file.

    ``ordinal`` is 1-based position in the live file and is the identity every
    verb here takes, because an entry has no number of its own. That is sound
    only because the file is append-only by contract — a claim is "never
    reworded, reordered or deleted" — so an entry's position is stable for as
    long as it lives in the file. ``archive`` is the one thing that moves
    entries out, and it therefore renumbers what remains; it says so when it
    runs, and ``tick`` refuses to invent a pointer on a number it cannot
    resolve.

    A malformed entry (one ``aide check`` warns about) still gets an ordinal.
    Skipping it would make ``insights list`` number entries differently from
    the file itself, so the one number a reader can act on would be wrong for
    every entry after the first typo.
    """

    ordinal: int
    lineno: int                 # 1-based, of the entry line itself
    raw: str                    # the entry line, verbatim
    ticked: bool
    type: Optional[str]         # None when the line does not parse
    text: str                   # the claim, without provenance or pointer
    date: Optional[str]
    source: Optional[str]       # the provenance verbatim; None for a bare date
    note: Optional[str]         # what follows the date, verbatim — by
                                # convention "engine X.Y.Z"; None when absent
    item: Optional[int]         # only when `source` names exactly one item
    pointer: Optional[str]      # what follows " → ", when ticked in place
    trail: List[str]            # raw status-trail lines, in file order
    end_lineno: int             # 1-based, of the entry's last trail line


def parse_insights(text: str) -> List[InsightEntry]:
    """Parse ``insights.md`` into entries, malformed ones included.

    Pure: it takes the file's text, never a path, so the shape rules are
    testable without a filesystem (the module convention — see
    ``.aide/scripts/tests``).
    """
    lines = text.splitlines()
    entries: List[InsightEntry] = []
    for lineno, line in enumerate(lines, start=1):
        if not line.startswith("- "):
            if entries and _INSIGHT_TRAIL_RE.match(line):
                # A trail line belongs to the entry above it; NamedTuple is
                # immutable, so grow the list it holds rather than rebuilding.
                entries[-1].trail.append(line)
                entries[-1] = entries[-1]._replace(end_lineno=lineno)
            continue
        m = _INSIGHT_FULL_RE.match(line) or _INSIGHT_FULL_LOOSE_RE.match(line)
        if m is None:
            entries.append(InsightEntry(
                ordinal=len(entries) + 1, lineno=lineno, raw=line,
                ticked=line.startswith("- [x]") or line.startswith("- [X]"),
                type=None, text=line[2:].strip(), date=None, source=None,
                note=None, item=None, pointer=None, trail=[],
                end_lineno=lineno))
            continue
        tail = m.group("tail")
        pointer = (tail.split(_INSIGHT_POINTER, 1)[1].strip()
                   if _INSIGHT_POINTER in tail else None)
        source = m.group("source")
        one_item = _INSIGHT_ONE_ITEM_RE.match(source) if source else None
        entries.append(InsightEntry(
            ordinal=len(entries) + 1, lineno=lineno, raw=line,
            ticked=m.group("mark") in ("x", "X"),
            type=m.group("type"), text=m.group("text").strip(),
            date=m.group("date"), source=source, note=m.group("note"),
            item=int(one_item.group(1)) if one_item else None,
            pointer=pointer, trail=[], end_lineno=lineno))
    return entries


def _find_entry(entries: List[InsightEntry], ordinal: int) -> InsightEntry:
    for e in entries:
        if e.ordinal == ordinal:
            return e
    raise ValueError(
        f"no entry {ordinal} — the file holds {len(entries)} "
        f"entr{'y' if len(entries) == 1 else 'ies'}; run `insights list` for "
        f"current numbers (an archive renumbers what remains)")


def tick_insight_text(text: str, ordinal: int, pointer: str,
                      date: str, trail_only: bool = False) -> Tuple[str, str]:
    """Tick entry *ordinal*, or append a dated trail line if already ticked.

    The two halves of conventions.md §1's lifecycle, chosen by the entry's own
    state rather than by a flag: the **first** routing flips the checkbox and
    records where the claim landed on the entry line; **everything after** it —
    a re-route, a resolution, a premise that decayed — is bookkeeping and goes
    in the appendable status trail underneath.

    *trail_only* is the third case §1 → insights-triage.md names — a judgement
    that leaves the entry **open** (a duplicate, a reason it stays untriaged)
    and is still recorded as a dated trail line under it (issue #236). The
    checkbox is not touched; on an entry already ticked it is the ordinary
    second-update path.

    The captured claim is never touched by either path. Returns
    ``(new_text, message)``; raises ``ValueError`` if the ordinal does not
    resolve or the entry is too malformed to edit safely.
    """
    if "\n" in pointer or "\r" in pointer:
        raise ValueError(
            "the pointer may not contain a line break — it is written into a "
            "single entry line, so a break would split one claim into two and "
            "renumber everything below it")
    entries = parse_insights(text)
    entry = _find_entry(entries, ordinal)
    lines = text.splitlines()
    trailing_newline = text.endswith("\n")

    if entry.ticked or trail_only:
        if not entry.ticked and entry.type is None:
            raise ValueError(
                f"entry {ordinal} does not parse as an inbox entry, so there "
                f"is no entry to write a trail line under safely: "
                f"{entry.raw!r}. Fix the line's shape first (`aide check` "
                f"names the rule)")
        # end_lineno is 1-based, so as a 0-based list index it is the slot
        # just past the entry's last line — where the next trail line goes.
        insert_at = entry.end_lineno
        indent = "  "
        if entry.trail:
            indent = entry.trail[-1][: len(entry.trail[-1]) - len(entry.trail[-1].lstrip())]
        lines.insert(insert_at, f"{indent}- **{date}** {_INSIGHT_POINTER.strip()} {pointer}")
        if entry.ticked:
            message = f"entry {ordinal}: already ticked — appended a {date} trail line"
        else:
            message = f"entry {ordinal}: left open — appended a {date} trail line"
    else:
        if entry.type is None:
            raise ValueError(
                f"entry {ordinal} does not parse as an inbox entry, so there "
                f"is no checkbox to tick safely: {entry.raw!r}. Fix the line's "
                f"shape first (`aide check` names the rule)")
        line = entry.raw.replace("- [ ]", "- [x]", 1)
        if entry.pointer is None:
            line = line + _INSIGHT_POINTER + pointer
            message = f"entry {ordinal}: ticked → {pointer}"
        else:
            # A pointer written by hand before the tick: keep it, and record
            # this routing where a second one belongs.
            lines[entry.lineno - 1] = line
            # 1-based end_lineno as a 0-based index = just past the entry.
            lines.insert(entry.end_lineno,
                         f"  - **{date}** {_INSIGHT_POINTER.strip()} {pointer}")
            return ("\n".join(lines) + ("\n" if trailing_newline else ""),
                    f"entry {ordinal}: ticked; existing pointer kept, "
                    f"added a {date} trail line")
        lines[entry.lineno - 1] = line

    return ("\n".join(lines) + ("\n" if trailing_newline else "")), message


def insight_quarter(date: str) -> str:
    """``"2026-08-24"`` → ``"2026-Q3"`` — the archive file an entry belongs to."""
    year, month = int(date[:4]), int(date[5:7])
    return f"{year}-Q{(month - 1) // 3 + 1}"


def archive_insight_text(
    text: str, before: str,
) -> Tuple[str, Dict[str, List[str]], List[InsightEntry]]:
    """Split closed entries dated before *before* out of the live file.

    Returns ``(remaining_text, {quarter: [lines]}, undatable)``, where
    ``undatable`` holds the **closed entries this pass could not date** and so
    could not consider. An entry too malformed to yield a date is excluded from
    every ``--before`` cut however old and however closed it is, and reporting
    it here is what keeps that from being silent: the same pass that declines
    to move it says which lines they were, so the operator can fix a shape
    instead of wondering why the live file will not shrink. It is returned
    rather than logged because this helper is pure — the caller prints.

    **Only ticked entries move**: an open entry is the live working set whatever its date, and
    archiving one would hide exactly the backlog this verb exists to surface.
    An entry travels with its whole status trail, so the archive stays readable
    on its own.

    Pure, and it never rewrites a claim: each line's *text* is carried across
    unchanged, which is what keeps the immutability rule true through the move.
    Line endings are not carried — like every writer in this module, it rebuilds
    the text with ``\n`` — so the promise is the claim, not the bytes around it.
    """
    lines = text.splitlines()
    entries = parse_insights(text)
    moving = {e.ordinal for e in entries
              if e.ticked and e.date is not None and e.date < before}
    # Closed, so it was a candidate; undated, so no cut can ever reach it.
    undatable = [e for e in entries if e.ticked and e.date is None]
    moved: Dict[str, List[str]] = {}
    drop: set = set()
    for e in entries:
        if e.ordinal not in moving:
            continue
        block = lines[e.lineno - 1:e.end_lineno]
        moved.setdefault(insight_quarter(e.date), []).extend(block)
        drop.update(range(e.lineno - 1, e.end_lineno))
    kept = [ln for i, ln in enumerate(lines) if i not in drop]
    return _collapse_blank_runs(kept, text.endswith("\n")), moved, undatable


def _collapse_blank_runs(lines: List[str], trailing_newline: bool) -> str:
    """Join *lines*, leaving at most one blank line where entries were removed.

    Lifting entries out of a blank-separated list otherwise leaves the gaps
    behind, and a file that grows whitespace every time it is tidied is not
    tidied.
    """
    out: List[str] = []
    for line in lines:
        if not line.strip() and out and not out[-1].strip():
            continue
        out.append(line)
    return "\n".join(out) + ("\n" if trailing_newline else "")


# --------------------------------------------------------------------------- #
# insights resolve — an entry-level union of a conflicted inbox
# --------------------------------------------------------------------------- #
#: A checkbox left at the front of a line too malformed to parse as an entry.
#: Stripped before an identity is taken, so a tick on such a line does not make
#: it look like a *different* claim and get appended twice.
_CONFLICT_CHECKBOX_RE = re.compile(r"^\[[ xX]\]\s*")
#: The date a trail line carries, written by `tick` as ``- **YYYY-MM-DD** → …``.
_TRAIL_DATE_RE = re.compile(r"\*\*(\d{4}-\d{2}-\d{2})\*\*")


def split_conflict_sides(text: str) -> Tuple[str, str, int]:
    """Split a conflicted file into its two whole documents.

    Returns ``(ours, theirs, blocks)`` — each side reconstructed as a complete
    file (the common regions plus that side's half of every conflict block),
    and how many blocks there were. Whole documents rather than the hunks
    alone, because the entry numbering that gives an inbox entry its identity
    is positional: a hunk read on its own has no idea which entry it starts at.

    ``diff3``/``zdiff3`` conflict style is understood and its ``|||||||`` base
    section discarded — it belongs to neither side, and appending it to both
    would duplicate every entry the merge base already had.

    Raises ``ValueError`` on a malformed block (nested, unterminated, or a
    closer with no opener). That is a refusal, not a repair: a file whose
    markers do not nest is not a file this verb can reason about.
    """
    ours: List[str] = []
    theirs: List[str] = []
    state = "common"
    blocks = 0
    for lineno, line in enumerate(text.splitlines(), start=1):
        if state == "common":
            if _CONFLICT_OPEN_RE.match(line):
                state = "ours"
            elif _CONFLICT_CLOSE_RE.match(line) or _CONFLICT_BASE_RE.match(line):
                raise ValueError(
                    f"insights.md:{lineno}: {line.split(' ')[0]} outside a "
                    f"conflict block — the markers do not nest")
            else:
                ours.append(line)
                theirs.append(line)
        elif state == "ours":
            if _CONFLICT_BASE_RE.match(line):
                state = "base"
            elif _CONFLICT_SEP_RE.match(line):
                state = "theirs"
            elif _CONFLICT_OPEN_RE.match(line) or _CONFLICT_CLOSE_RE.match(line):
                raise ValueError(
                    f"insights.md:{lineno}: {line.split(' ')[0]} inside an "
                    f"open conflict block — the markers do not nest")
            else:
                ours.append(line)
        elif state == "base":
            if _CONFLICT_SEP_RE.match(line):
                state = "theirs"
            elif (_CONFLICT_OPEN_RE.match(line) or _CONFLICT_CLOSE_RE.match(line)
                    or _CONFLICT_BASE_RE.match(line)):
                raise ValueError(
                    f"insights.md:{lineno}: {line.split(' ')[0]} inside the "
                    f"merge-base section of a conflict block")
            # else: the base's own lines, which belong to neither side.
        else:  # theirs
            if _CONFLICT_CLOSE_RE.match(line):
                state = "common"
                blocks += 1
            elif (_CONFLICT_OPEN_RE.match(line) or _CONFLICT_BASE_RE.match(line)
                    or _CONFLICT_SEP_RE.match(line)):
                raise ValueError(
                    f"insights.md:{lineno}: {line.split(' ')[0]} inside the "
                    f"second half of a conflict block — the markers do not nest")
            else:
                theirs.append(line)
    if state != "common":
        raise ValueError("the last conflict block is never closed — no "
                         "'>>>>>>>' line, so half the file has no second side")
    end = "\n" if text.endswith("\n") else ""
    return ("\n".join(ours) + (end if ours else ""),
            "\n".join(theirs) + (end if theirs else ""), blocks)


def insight_identity(entry: InsightEntry) -> Tuple[str, ...]:
    """What makes two entries the *same* captured claim across two branches.

    The immutable half of an entry and nothing else (conventions.md §1 →
    ``insights.md``): its type, claim text, date and provenance. The checkbox,
    the ``→`` pointer and the status trail are bookkeeping, so an entry ticked
    on one branch and untouched on the other is one entry here — which is what
    lets the tick be merged instead of the claim being appended twice.

    A line too malformed to parse has only itself, minus any checkbox.
    """
    if entry.type is None:
        return ("", _CONFLICT_CHECKBOX_RE.sub("", entry.text).strip())
    return (entry.type, entry.text, entry.date or "", entry.source or "",
            entry.note or "")


def _entry_blocks(text: str) -> Tuple[List[str], List[Tuple[InsightEntry, List[str]]],
                                     List[str]]:
    """``(head, [(entry, its lines)], tail)`` — the file cut at entry boundaries.

    An entry's block runs from its own line to just before the next entry's, so
    whatever sits between two entries (the blank line an archive can leave)
    travels with the entry above it and no line is dropped by a rebuild.
    """
    lines = text.splitlines()
    entries = parse_insights(text)
    if not entries:
        return lines, [], []
    head = lines[:entries[0].lineno - 1]
    blocks: List[Tuple[InsightEntry, List[str]]] = []
    for i, e in enumerate(entries):
        stop = (entries[i + 1].lineno - 1) if i + 1 < len(entries) else e.end_lineno
        blocks.append((e, lines[e.lineno - 1:stop]))
    return head, blocks, lines[entries[-1].end_lineno:]


def _strip_trailing_blanks(lines: List[str]) -> List[str]:
    out = list(lines)
    while out and not out[-1].strip():
        out.pop()
    return out


def _merge_trail(ours: List[str], theirs: List[str]) -> List[str]:
    """Both sides' trail lines, deduplicated, in date order (§1 — newest last).

    The sort is stable and an undated line inherits the date of the line above
    it, so a hand-written continuation stays under the line it continues
    instead of being hoisted to the top of the trail.
    """
    seen = set()
    merged: List[str] = []
    for line in list(ours) + list(theirs):
        key = line.strip()
        if key in seen:
            continue
        seen.add(key)
        merged.append(line)
    keys: List[str] = []
    last = ""
    for line in merged:
        m = _TRAIL_DATE_RE.search(line)
        if m:
            last = m.group(1)
        keys.append(last)
    return [line for _, line in sorted(zip(keys, merged), key=lambda p: p[0])]


def _merge_entry_block(ours: InsightEntry, ours_lines: List[str],
                       theirs: InsightEntry, theirs_lines: List[str],
                       date: str) -> Tuple[List[str], Optional[str]]:
    """Merge one entry both sides hold. Returns ``(lines, flag)``.

    The claim line is taken whole from the side that ticked it, never rebuilt —
    that is how the immutability rule survives a merge. Trails are unioned.
    Two ticks with two different pointers is the one case a machine may not
    decide: both are kept, the second as a dated trail line, and the flag says
    a human must pick.
    """
    if ours_lines == theirs_lines:
        return ours_lines, None
    # Which side's claim line survives, in the order that loses least: the side
    # that ticked, then — when both did — the side carrying a routing pointer.
    # Preferring ours unconditionally dropped `theirs`' pointer whenever ours
    # was ticked without one, and a routing record is the whole reason a tick
    # is worth merging.
    if ours.ticked != theirs.ticked:
        kept, other = (ours, theirs) if ours.ticked else (theirs, ours)
    elif ours.pointer or not theirs.pointer:
        kept, other = ours, theirs
    else:
        kept, other = theirs, ours
    flag = None
    extra: List[str] = []
    if other.pointer and other.pointer != kept.pointer:
        # Two pointers, one per side: the one case a machine may not decide, so
        # it decides nothing and keeps both. Not conditioned on the other side
        # having *ticked* — a pointer written by hand before a tick is a
        # routing record like any other, and dropping it is the silent loss
        # this whole branch exists to prevent.
        extra.append(f"  - **{date}** {_INSIGHT_POINTER.strip()} {other.pointer} "
                     f"(second pointer, from the other side of the merge)")
        flag = (f"entry {ours.ordinal} carries a different pointer on each side "
                f"of the merge ({kept.pointer!r} and {other.pointer!r}); both "
                f"are kept — the entry line carries the first and the second is "
                f"a trail line, so a human must decide which is true")
    trail = _merge_trail(ours.trail, theirs.trail) + extra
    # Anything the block held that is neither the claim nor a trail line, from
    # BOTH sides — ours first. Taking it from ours alone dropped whatever sat
    # under the entry on the other side and still called the merge clean.
    # Blank separators are not among them: the caller strips those and puts
    # each entry's own back.
    rest = [ln for ln in ours_lines[1:] if ln not in ours.trail]
    rest += [ln for ln in theirs_lines[1:]
             if ln not in theirs.trail and ln not in rest]
    return [kept.raw] + trail + rest, flag


def resolve_insights_text(text: str, date: str,
                          base_text: Optional[str] = None,
                          ) -> Tuple[str, List[str], List[str]]:
    """Union the two sides of a conflicted inbox. ``(merged, notes, refusals)``.

    Non-empty ``refusals`` means nothing was merged and the caller must not
    write: the conflict is not the append shape this verb exists for, and the
    only safe thing to do with a claim this code cannot align is leave it in
    front of a human.

    **What "pure append" means here.** Both sides must start with the same
    entries, in the same order, differing only in bookkeeping; everything past
    that point is new on one side or the other and is concatenated, ours then
    theirs. Positional ordinals need no renumbering because nothing moves.

    *base_text* — the merge base, which a conflicted index can supply — makes
    that check exact rather than inferred: the shared history is the base, so a
    rewritten prefix is caught even when the rewrite is at the tail, where the
    two sides alone cannot tell a reworded claim from a second capture. Without
    it the check falls back to the longest common prefix of the two sides,
    which still catches every reorder, deletion and archive: an archive cuts
    closed entries out of the middle, so entries survive on both sides *past*
    the common prefix, and that overlap is a refusal.
    """
    refusals: List[str] = []
    try:
        ours_text, theirs_text, blocks = split_conflict_sides(text)
    except ValueError as exc:
        return text, [], [str(exc)]
    if not blocks:
        return text, [], []

    head_o, blocks_o, tail_o = _entry_blocks(ours_text)
    head_t, blocks_t, tail_t = _entry_blocks(theirs_text)
    if _strip_trailing_blanks(head_o) != _strip_trailing_blanks(head_t):
        refusals.append(
            "the two sides differ above the first entry — the conflict reaches "
            "the file's header, which is not an append; resolve it by hand")
    if _strip_trailing_blanks(tail_o) != _strip_trailing_blanks(tail_t):
        refusals.append(
            "the two sides differ below the last entry — the conflict reaches "
            "past the entry list, which is not an append; resolve it by hand")
    if refusals:
        return text, [], refusals

    ids_o = [insight_identity(e) for e, _ in blocks_o]
    ids_t = [insight_identity(e) for e, _ in blocks_t]
    if base_text is not None:
        ids_b = [insight_identity(e) for e in parse_insights(base_text)]
        n = len(ids_b)
        rewritten = [side for side, ids in (("HEAD", ids_o), ("the other side", ids_t))
                     if ids[:n] != ids_b]
        if rewritten:
            return text, [], [
                f"{' and '.join(rewritten)} rewrote the {n} entr"
                f"{'y' if n == 1 else 'ies'} the two branches share — a claim "
                f"was reworded, reordered, deleted or archived, and §1 makes "
                f"every one of those something a human must see. Resolve this "
                f"one by hand."]
        common = n
    else:
        common = 0
        while (common < len(ids_o) and common < len(ids_t)
               and ids_o[common] == ids_t[common]):
            common += 1

    overlap = set(ids_o[common:]) & set(ids_t[common:])
    if overlap:
        return text, [], [
            f"{len(overlap)} entr{'y' if len(overlap) == 1 else 'ies'} appear"
            f"{'s' if len(overlap) == 1 else ''} on both sides after the "
            f"history they share — the file was reordered or an archive cut "
            f"entries out of the middle of it, so the two sides are not one "
            f"append on top of a common prefix. Resolve this one by hand "
            f"(first: {' | '.join(x[1] for x in sorted(overlap))[:120]})"]

    # A blank line between two entries belongs to neither entry, and only a
    # *last* entry can lack one — its blanks went to the file's tail instead.
    # So the two sides can disagree about an entry neither of them touched,
    # purely by where it sits. Each entry is therefore split into its own lines
    # and its own trailing blanks: the lines are merged, and the blanks are
    # carried through untouched, so an entry nobody edited is re-emitted with
    # exactly the spacing it had. Only a *join* the append newly created — an
    # entry that was last on its side and now has one behind it — needs a
    # separator supplied, and the one it had is the one its own side's tail is
    # still holding.
    strip = _strip_trailing_blanks

    def own(block: List[str]) -> List[str]:
        return block[len(strip(block)):]

    def leading_blanks(lines: List[str]) -> List[str]:
        out: List[str] = []
        for line in lines:
            if line.strip():
                break
            out.append(line)
        return out

    last_o = len(blocks_o) - 1
    last_t = len(blocks_t) - 1
    # What each side's final entry would have been followed by, had anything
    # followed it. Empty for a file whose entries sit on consecutive lines.
    end_o = leading_blanks(tail_o)
    end_t = leading_blanks(tail_t)

    def spacing(*candidates: List[str]) -> List[str]:
        for c in candidates:
            if c:
                return c
        return []

    # (block, what followed it, whether it ended its side). A block that ended
    # its side and was followed by nothing has no observed spacing at all —
    # that is the join the append newly created, and the only place a
    # separator may be *invented*. Everywhere else an empty `after` is a fact
    # about the file, and re-spacing entries neither side touched on the
    # strength of a blank line somewhere else in the file is a reformat.
    merged_blocks: List[Tuple[List[str], List[str], bool]] = []
    flags: List[str] = []
    ticks = 0
    for i, ((eo, lo), (et, lt)) in enumerate(
            zip(blocks_o[:common], blocks_t[:common])):
        block, flag = _merge_entry_block(eo, strip(lo), et, strip(lt), date)
        if strip(lo) != strip(lt):
            # A shared claim whose bookkeeping the two sides disagreed on —
            # counted whichever side won, since the decision is the news.
            ticks += 1
        if flag:
            flags.append(flag)
        merged_blocks.append((block, spacing(
            own(lo), own(lt),
            end_o if i == last_o else [], end_t if i == last_t else []),
            i == last_o or i == last_t))
    for i, (_, blk) in enumerate(blocks_o[common:], start=common):
        merged_blocks.append((strip(blk),
                              spacing(own(blk), end_o if i == last_o else []),
                              i == last_o))
    for i, (_, blk) in enumerate(blocks_t[common:], start=common):
        merged_blocks.append((strip(blk),
                              spacing(own(blk), end_t if i == last_t else []),
                              i == last_t))

    out: List[str] = list(head_o)
    previous: List[str] = []
    for i, (block, after, ended_a_side) in enumerate(merged_blocks):
        out.extend(block)
        if i == len(merged_blocks) - 1:     # the last entry's blanks are the tail's
            break
        # Inherit from the entry above only where there is nothing to inherit
        # *from* the entry itself, which is exactly the newly created join.
        after = after or (previous if ended_a_side else [])
        out.extend(after)
        previous = after
    out.extend(tail_o)

    notes = [f"{common} entr{'y' if common == 1 else 'ies'} shared, "
             f"{len(blocks_o) - common} added on HEAD, "
             f"{len(blocks_t) - common} added on the other side, "
             f"{ticks} merged in place"]
    notes.extend(flags)
    merged_text = "\n".join(out) + ("\n" if text.endswith("\n") else "")
    return merged_text, notes, []


def absolute_path_test_warnings(repo_root: Path,
                                config: Dict[str, Dict[str, object]]) -> List[str]:
    """Warn on a test file containing the repository's own absolute path.

    The one portability rule of conventions.md §6 a script can decide, and the
    one whose recorded instance was invisible to every other gate for weeks: a
    test pinned the authoring sandbox's own filesystem path instead of
    resolving relative to the test file. Because that path *is* where the
    project sits on that machine, it passed the builder's run, both validator
    rounds, and even a fresh clone into a different directory — an absolute
    path ignores where the process runs from. On every CI runner the glob
    matched nothing, the digest collapsed to SHA-256 of empty input, and all
    four legs failed.

    Matching the repo root literally keeps this exact: a test that hardcodes
    the path of the repository it lives in is wrong on any other machine, with
    no judgement call and no false positive to argue about.
    """
    tests_dir = repo_root / str(config["project"].get("tests_dir", "tests"))
    if not tests_dir.is_dir():
        return []
    # Three spellings, because the offending literal is whatever the authoring
    # platform wrote and this check must fire wherever it runs. On POSIX all
    # three collapse to one string; on Windows they are genuinely different:
    #   as_posix()  C:/path/to/repo    — a forward-slash literal
    #   str()       C:\path\to\repo    — a raw string, r"C:\path\to\repo"
    #   escaped     C:\\path\\to\\repo — an ordinary literal, the COMMON form
    # Omitting the third would make this portability lint miss the most likely
    # Windows spelling of the very defect it exists to catch.
    root = repo_root.resolve()
    needles = {root.as_posix(), str(root), str(root).replace("\\", "\\\\")}
    out: List[str] = []
    for path in sorted(tests_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding=_ENCODING)
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if any(n in line for n in needles):
                rel = _rel_display(path, repo_root)
                out.append(
                    f"{rel}:{lineno}: contains this repository's absolute path — "
                    f"it passes here and matches nothing on any other checkout; "
                    f"resolve from the test file instead "
                    f"(Path(__file__).resolve().parents[N]). See conventions.md §6")
                break   # one warning per file is enough to act on
    return out


def _reach_with_breadth(lines: List[str], g: HumanGate) -> str:
    """*g*'s reach with the held items resolved and counted.

    A ``stage N`` reach reads plausibly right while holding items its author
    never meant to hold — the observed case gated the very deliberation that
    was to produce the gate's evidence. ``aide claim`` already names what it
    holds, but that surfaces only when a runner stalls; the check computes the
    same breadth (``stage_item_numbers``) and used to throw it away, so the
    contradiction was invisible at authoring time. Only the stage form needs
    resolving: an item-list reach already names its items, and ``all`` is its
    own answer.

    The count covers the items the gate still sits in front of: a ✅ item has
    merged and a ❌ one is out, so "holding" either would overstate the reach
    against the very enforcement this message mirrors. (``claim``'s stall
    report narrows further, to the claimable subset of one queue — that is
    the runtime view; this is the authoring-time view of the same fact, and a
    stage whose every item merged falls back to the bare reach.)
    """
    if g.stage is None:
        return g.reach
    _, _, item_status = _parse_item_status(lines)
    items = [i for i in stage_item_numbers(lines, g.stage)
             if item_status.get(i, "planned") not in ("complete", "excluded")]
    if not items:
        return g.reach
    return (f"stage {g.stage} — holding {len(items)} item(s): "
            + ", ".join(f"{i:03d}" for i in items))


def gate_warnings(lines: List[str]) -> List[str]:
    """One warning per unresolved human gate.

    A warning, never an error: an outstanding gate is a normal state — work is
    waiting on a person, which is what it is for. The point is that the state
    is *visible* rather than buried in an item spec's prose. A row too
    mis-shaped to be a gate is not a state but a defect, and is an error in
    ``unreadable_row_errors``.
    """
    out: List[str] = []
    for n, g in enumerate(human_gates(lines), start=1):
        if g.kind == "approved":
            continue
        if g.kind is None:
            out.append(
                f"progress.md:{g.lineno}: human gate {n} ({g.text}) has an "
                f"unrecognised status — use ⏳ Awaiting, ✅ Approved or ❌ Declined; "
                f"until it reads one of those the gate counts as unresolved")
            continue
        if g.kind == "declined":
            out.append(
                f"progress.md:{g.lineno}: human gate {n} ({g.text}) was DECLINED "
                f"and still blocks {_reach_with_breadth(lines, g)} — a refusal does not release the "
                f"work it guards; drop those items or change what the gate asks")
            continue
        if g.stage is not None and not stage_item_numbers(lines, g.stage):
            # An empty reach has two causes and only one is a mistake.
            if stage_section(lines, g.stage) is None:
                # No such section: a typo, invisible otherwise — the gate looks
                # like it guards a stage while holding nothing at all, ever.
                reach = (f"stage {g.stage} — which has no deliverable "
                         f"referencing any item, so this gate holds NOTHING; "
                         f"check the stage number")
            else:
                # The section is there and simply has nothing queued for it
                # yet. Raising a gate before the work exists is the cheapest
                # time to raise one, and `stage N` reach re-resolves through
                # progress.md on every read — so this gate is armed and will
                # hold that stage's items as they appear. Calling the feature's
                # own happy path a typo trains the reader to ignore the check.
                reach = (f"stage {g.stage} — which has no items queued yet, so "
                         f"it holds nothing today and will block that stage's "
                         f"items as they are created")
        elif g.blocks or g.stage or g.blocks_all:
            reach = _reach_with_breadth(lines, g)
        else:
            reach = ("nothing named — the Blocks cell names no item, no "
                     "'stage N', and is not 'all', so this gate holds nothing")
        out.append(f"progress.md:{g.lineno}: human gate {n} ({g.text}) is "
                   f"awaiting a decision — blocks {reach}")
    return out


#: A deliverable bullet must be FLAT (conventions.md §1). `_BULLET_RE` allows
#: leading whitespace, so a nested bullet is read as a **full deliverable** —
#: not ignored. That is the hazard: nesting implies subordination to a reader
#: while the rollup counts it as a peer, so a `📋` child silently drags its ✅
#: parent's stage to 🚧. Verified: ['complete', 'planned'] -> in-progress.
_NESTED_DELIVERABLE_RE = re.compile(r"^\s+[-*]\s*(?P<icon>" + _ICON_ALT + r")")

#: Documents whose template carries a header blockquote. Not every file under
#: docs_dir: a generated artifact or a project note is not a living document,
#: and insights.md's template deliberately opens with a comment instead.
_BLOCKQUOTE_DOCS = ("vision.md", "roadmap.md", "progress.md")

#: A status FIELD in an item header: `**Status:** x` or `**Status**: x`. The
#: colon is required, so bold emphasis on the word in prose is not a match.
_ITEM_STATUS_FIELD_RE = re.compile(
    r"\*\*\s*(?P<name>Status|Completed)\s*(?::\s*\*\*|\*\*\s*:)")


#: Calls that spawn a process. Matched through the AST, never by line text: the
#: one occurrence in the consumer measured against was a DOCSTRING explaining
#: why the author had removed a subprocess — a line-based lint flags the file
#: documenting the correct practice.
_SUBPROCESS_FUNCS = frozenset({"run", "Popen", "check_output", "check_call", "call"})


def _rel_display(path: Path, repo_root: Path) -> str:
    """*path* relative to the repo for a message, falling back to absolute.

    `tests_dir` may be configured absolute or resolve outside the repo via a
    symlink, and `relative_to` raises then. Shared by every test-hygiene lint:
    fixing this once in `absolute_path_test_warnings` and then hand-writing the
    same call in two new ones is exactly how it came back.
    """
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _test_files(repo_root: Path, config: Dict[str, Dict[str, object]]) -> List[Path]:
    tests_dir = repo_root / str(config["project"].get("tests_dir", "tests"))
    if not tests_dir.is_dir():
        return []
    return [p for p in sorted(tests_dir.rglob("*.py"))
            if "__pycache__" not in p.parts]


def separator_dependent_test_warnings(repo_root: Path,
                                      config: Dict[str, Dict[str, object]]) -> List[str]:
    """Tests stringifying a relative `Path` into a value that gets compared.

    conventions.md §6: any `Path` entering a hash, comparison or match must be
    `.as_posix()`. Narrowed to `.relative_to(`, the shape all four recorded
    CI-only failures took, reached two ways — an explicit `str(...)` and an
    f-string, which calls `str()` for you.

    Matched through the AST, because a regex cannot tell an f-string's `{...}`
    from a dict or set literal: `{p.relative_to(root): 1}` never stringifies the
    Path and must not be flagged. A lint that cries wolf stops being read.
    """
    out: List[str] = []
    for path in _test_files(repo_root, config):
        try:
            tree = ast.parse(path.read_text(encoding=_ENCODING))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        def _ends_in_relative_to(node) -> bool:
            """True when the OUTERMOST call of *node* is `.relative_to(...)`.

            Deliberately the outermost, not anywhere in the subtree: searching
            the subtree flags `str(p.relative_to(root).as_posix())`, which is
            already separator-stable and is exactly what the rule asks for.
            Flagging compliant code is how a lint stops being read, so this
            errs narrow — it reports the recorded shape and stays quiet on
            anything already normalised.
            """
            return (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "relative_to")

        for node in ast.walk(tree):
            hit = False
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "str" and len(node.args) == 1):
                hit = _ends_in_relative_to(node.args[0])
            elif isinstance(node, ast.JoinedStr):
                hit = any(_ends_in_relative_to(v.value) for v in node.values
                          if isinstance(v, ast.FormattedValue))
            if hit:
                out.append(
                    f"{_rel_display(path, repo_root)}:{node.lineno}: a relative "
                    f"Path rendered with str() carries the OS separator, so this "
                    f"value differs on Windows — use .as_posix() "
                    f"(conventions.md §6)")
                break
    return out


def cli_subprocess_test_warnings(repo_root: Path,
                                 config: Dict[str, Dict[str, object]]) -> List[str]:
    """Tests shelling out to `aide.py` instead of calling its function.

    conventions.md §6: prefer calling the function over shelling out to the
    command that calls it. The logic is importable and returns structured data;
    the subprocess adds stdout encoding, platform quirks, and a re-parse of what
    was structured a moment earlier. The recorded instance returned
    ``stdout is None`` on a Windows runner — and had it returned ``""`` the test
    would have passed while checking nothing.

    **No exemption for the self-referential case**, asked for and declined
    (issue #123). A test whose whole job is to replay `aide check`'s literal
    stdout trips this rule, which reads like the verb flagging itself. It is
    not: `cmd_check` calls `run_checks`, that function returns
    ``(errors, warnings)`` as structured data, and asserting on it in-process
    is both the fix and the better test — which is what the reporting consumer
    did. Exempting the shape would license the worse test in the one place the
    argument for it sounds strongest.

    What the report actually found is a *measurement* defect, and it belongs to
    the spec, not to this lint: a module that shells out to the CLI raises the
    warning count by one the moment it is committed, so any baseline count
    recorded before it existed is falsified by the act of adding it. Measured:
    a spec recorded 3, the base commit already carrying the module reported 4,
    and the 4th was the module. §6 now says never to pin a count that way.
    """
    out: List[str] = []
    for path in _test_files(repo_root, config):
        try:
            tree = ast.parse(path.read_text(encoding=_ENCODING))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name not in _SUBPROCESS_FUNCS:
                continue
            if any(isinstance(c, ast.Constant) and isinstance(c.value, str)
                   and "aide.py" in c.value for c in ast.walk(node)):
                rel = _rel_display(path, repo_root)
                out.append(
                    f"{rel}:{node.lineno}: shells out to aide.py — call the "
                    f"function instead (e.g. run_checks); a subprocess adds a "
                    f"stdout/encoding surface that has failed on Windows only, "
                    f"and can pass while checking nothing (conventions.md §6)")
                break
    return out


#: Branch names a hardcoded diff range is written against. The configured
#: `main_branch` is the honest one; `main` and `master` ride along because this
#: shape is copied between projects — a consumer whose base is `develop` and
#: whose test says `main...HEAD` has written the same wrong assertion, and the
#: lint that only knew its own config would stay silent on it.
_CONVENTIONAL_BASES = ("main", "master")


def _scope_range_re(config: Dict[str, Dict[str, object]]) -> "re.Pattern":
    names = {str(config["git"].get("main_branch", "main")), *_CONVENTIONAL_BASES}
    alt = "|".join(re.escape(n) for n in sorted(names))
    return re.compile(rf"\b(?:origin/)?(?:{alt})\.{{2,3}}HEAD\b"
                      rf"|\bHEAD\.{{2,3}}(?:origin/)?(?:{alt})\b")


def scope_claim_test_warnings(repo_root: Path,
                              config: Dict[str, Dict[str, object]]) -> List[str]:
    """Diff-time scope claims written as suite assertions.

    §1 → authorised-paths-proof says a *diff-time scope claim* — "item N did
    not touch X" — belongs under **Asserts against** and is retired when its
    item merges, and `cmd_scope` exists precisely so the claim is not
    "enshrined as a suite assertion that outlives its truth". Both statements were already written
    down, and reached neither the spec-author writing the criterion nor the
    test-writer implementing it: two independent items in one consumer wrote the
    same `git diff main...HEAD` guard (issue #132), which is the signature of a
    missing check rather than a careless author.

    The shape fails in the direction that wastes the most time. Under a stacked
    queue the item's base is the **queue branch**, so `main` is stale by the
    whole queue and every sibling item's legitimate change is reported as this
    item's scope violation. The obvious repair is wrong too: deriving the base
    from `aide scope` makes the assertion pass only while the suite runs on the
    item's own claim branch, and `aide merge` re-runs that suite from the merge
    target — so it fails by construction inside the loop's own post-merge run.
    Skip-guarding is not an escape either: once the claim branch is deleted the
    test is skipped forever, which §6 ("tests that can actually fail") forbids.

    **Two literal shapes, deliberately, and no attempt at the general one.** A
    hardcoded `<base>...HEAD` range, and a shell-out to `aide scope`. A test
    that diffs the branch against a base it computes — `git merge-base HEAD
    origin/main`, then `diff` — is NOT reported, and this framework's own
    `tests/test_repo_versioning.py` is why: it is that shape, it is legitimate,
    and it is a claim about the branch rather than about an item's scope. No
    lint can tell those apart from the source, so this one decides only what is
    literal, and §6's rule holds where it cannot look. An interpolated range
    (`f"{base}...HEAD"`) is missed for the same reason.

    The `aide scope` half also trips `cli_subprocess_test_warnings`, which says
    "call the function instead". That advice is right about the boundary and
    wrong about the fix — the assertion should not be in the suite at all — so
    this warning is worth its line beside it.
    """
    out: List[str] = []
    rng = _scope_range_re(config)
    for path in _test_files(repo_root, config):
        try:
            tree = ast.parse(path.read_text(encoding=_ENCODING))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        rel = _rel_display(path, repo_root)
        hit = next((n for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)
                    and rng.search(n.value)), None)
        if hit is not None:
            out.append(
                f"{rel}:{hit.lineno}: a hardcoded '{rng.search(hit.value).group(0)}' "
                f"range makes this test a diff-time scope claim — it asserts "
                f"what an item did NOT touch, which stops being true the moment "
                f"that item merges into the base, and is red by construction on "
                f"a stacked queue where the real base is the queue branch. "
                f"Declare the pinned file under '## Asserts against' in the item "
                f"spec and let 'aide scope' decide it on the claim branch "
                f"(conventions.md §1 → authorised-paths-proof, §6)")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name not in _SUBPROCESS_FUNCS:
                continue
            consts = [c.value for c in ast.walk(node)
                      if isinstance(c, ast.Constant) and isinstance(c.value, str)]
            if not any("aide.py" in c for c in consts):
                continue
            if not any(c == "scope" or c.endswith(" scope") or " scope " in c
                       for c in consts):
                continue
            out.append(
                f"{rel}:{node.lineno}: shells out to 'aide scope' from the "
                f"suite — the verb resolves its base from the CURRENT branch's "
                f"recorded base, so this passes only while the suite runs on "
                f"the item's own claim branch and fails by construction in "
                f"the post-merge run of 'aide merge', from the merge target. "
                f"Scope is "
                f"checked on the branch, not asserted in the suite: declare the "
                f"pinned file under '## Asserts against' instead "
                f"(conventions.md §1 → authorised-paths-proof, §6)")
            break
    return out


#: The subprocess entry points that can hand *decoded* text back to the caller.
#: `call` and `check_call` return an exit status and never a capture, so a
#: `text=` on one of those decodes nothing and flagging it would be exactly the
#: false positive that stops a lint being read.
_DECODING_SUBPROCESS_FUNCS = frozenset({"run", "Popen", "check_output"})

#: Both spellings of "decode this for me". `universal_newlines=` is the pre-3.7
#: name and is still accepted, so a lint that knows only `text=` sees half the
#: shape — and the older spelling is the one an author copies from an old
#: answer, which is where this class comes from in the first place.
_TEXT_MODE_KWARGS = frozenset({"text", "universal_newlines"})


def _subprocess_names(tree: ast.AST) -> Tuple[set, Dict[str, str]]:
    """How this module spells `subprocess`: `(module aliases, name -> real)`.

    Matching on the method name alone flags `Runner().run(text=True)`, which has
    nothing to do with `subprocess` — caught in review, and the reason the
    docstring below can claim precision it would otherwise only assert. Both
    import forms are followed, aliases included:

        import subprocess              -> {"subprocess"}
        import subprocess as sp        -> {"sp"}
        from subprocess import run     -> {"run": "run"}
        from subprocess import run as r-> {"r": "run"}

    A star import binds every name at once and is treated as binding exactly
    the ones this lint cares about — caught in review, where resolving imports
    had turned `from subprocess import *` from a reported call into a silent
    one. Trading a false positive for a false negative is the wrong direction
    here, and this section says why.

    A binding made any other way — `run = subprocess.run`, or the module object
    re-exported through a sibling (`from helpers import subprocess`) — is not
    followed, and the lint stays quiet on it rather than guessing.
    """
    modules: set = set()
    funcs: Dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    modules.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                if alias.name == "*":
                    funcs.update({f: f for f in _DECODING_SUBPROCESS_FUNCS})
                    continue
                funcs[alias.asname or alias.name] = alias.name
    return modules, funcs


def _asks_for_text(node: ast.Call) -> bool:
    """Does this call ask for decoded output, as far as the source can say?

    `text=False` and `universal_newlines=None` ask for bytes and are not the
    defect. Anything else — `True`, a name, an expression — is treated as
    asking, because a call that may decode and names no codec is wrong in
    exactly the way a call that certainly decodes is.
    """
    for kw in node.keywords:
        if kw.arg not in _TEXT_MODE_KWARGS:
            continue
        if isinstance(kw.value, ast.Constant) and not kw.value.value:
            continue
        return True
    return False


def subprocess_encoding_test_warnings(repo_root: Path,
                                      config: Dict[str, Dict[str, object]]) -> List[str]:
    """Tests decoding subprocess output with whatever codec the platform guesses.

    conventions.md §6: a test that captures subprocess output as text passes
    `encoding="utf-8"`. Without it Python decodes with
    `locale.getpreferredencoding()` — UTF-8 on a Linux runner, **cp1252** on a
    Windows one — so the same bytes become different strings on the two legs of
    the same CI run.

    The recorded instance is the reason this is a lint and not advice. Six
    items in one consumer queue independently wrote
    `subprocess.run(..., capture_output=True, text=True)`; all six passed the
    Linux-only validator, and `windows-latest` returned a `KeyError` on a
    cp1252-mangled em-dash heading in one test and — worse — an **emoji-diff
    guard that matched nothing and reported PASS** in another. The second is a
    false negative: a gate that reports green having verified nothing, which is
    the worst outcome this loop has available and is invisible to every gate
    inside it (§7). Six independent authors reproducing one shape in one queue
    is the signature of a missing rule, not of a careless author.

    Decidable by AST, in the same shape as the eol-pin lint next door: a call
    to `run` / `Popen` / `check_output` carrying a `text=` or
    `universal_newlines=` keyword and no `encoding=` keyword. Three narrowings
    put together mean every warning this emits names a call that really would
    decode — the function set above, a literal-false `text=`, and the call
    having to reach `subprocess` through an import this module actually makes
    (`_subprocess_names`), without which `Runner().run(text=True)` is reported
    for sharing a method name.

    **The limit, stated rather than left to be discovered:** only a direct
    call is seen. A project that has wrapped its subprocess calls in a helper
    — which is the fix a consumer reached for — presents one call site to this
    lint and silence for the rest, and a `**kwargs` spread hides the keyword
    entirely. Silence here means "no call of the recorded shape", never "this
    suite decodes safely".
    """
    out: List[str] = []
    for path in _test_files(repo_root, config):
        try:
            tree = ast.parse(path.read_text(encoding=_ENCODING))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        modules, funcs = _subprocess_names(tree)
        if not modules and not funcs:
            continue                      # this module never imports subprocess
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                # `subprocess.run(...)`, or whatever this module called it.
                if not (isinstance(func.value, ast.Name)
                        and func.value.id in modules):
                    continue
                name = func.attr
            elif isinstance(func, ast.Name):
                name = funcs.get(func.id, "")
            else:
                continue
            if name not in _DECODING_SUBPROCESS_FUNCS:
                continue
            if any(kw.arg == "encoding" for kw in node.keywords):
                continue
            if not _asks_for_text(node):
                continue
            out.append(
                f"{_rel_display(path, repo_root)}:{node.lineno}: captures "
                f"subprocess output as text with no encoding= — Python then "
                f"decodes with the platform's locale codec, UTF-8 here and "
                f"cp1252 on a Windows runner, which mangles non-ASCII and has "
                f"defeated a guard silently rather than failing. Pass "
                f'encoding="utf-8". See conventions.md §6')
            break
    return out


def _gitattributes_no_rewrite_patterns(repo_root: Path) -> Optional[List[str]]:
    """Every pattern in `.gitattributes` that stops the CRLF rewrite.

    ``None`` (not ``[]``) when the file is absent, so the caller can tell "no
    pins" from "no file" and say the more useful of the two.

    **Three spellings, not one.** `eol=lf` is the one §6 names, but `binary`
    (git's macro for `-text -diff`) and a bare `-text` both switch the
    conversion off outright, and a file under either is exactly as safe. Only
    accepting `eol=lf` made the lint warn about a `*.png binary` fixture and
    tell its author to add a pin that would be wrong for it — a wolf-cry on
    code that had already done the right thing, which is how a lint stops being
    read.
    """
    path = repo_root / ".gitattributes"
    if not path.is_file():
        return None
    out: List[str] = []
    try:
        text = path.read_text(encoding=_ENCODING)
    except (OSError, UnicodeDecodeError):
        return None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        # `eol=lf` alone is enough: `text eol=lf` and a bare `eol=lf` both stop
        # core.autocrlf rewriting the file, which is the whole point here — as
        # do `binary` and an unsetting `-text`. A bare `text` is NOT in the
        # list: it *enables* the conversion.
        if len(parts) > 1 and any(a in ("eol=lf", "binary", "-text")
                                  for a in parts[1:]):
            out.append(parts[0])
    return out


def _gitattributes_matches(rel_posix: str, pattern: str) -> bool:
    """Does a `.gitattributes` pattern cover this repo-relative path?

    Git's pattern rules, not `fnmatch`'s: a `*` stops at a `/` (so
    `tests/*.json` must not match `tests/a/b.json`, which `fnmatch` would),
    `**` crosses separators, and a pattern with **no** slash matches at any
    depth — which is how `*.json` covers the whole tree.
    """
    pattern = pattern.strip().rstrip("/")
    if not pattern:
        return False
    if pattern.startswith("/"):
        pattern = pattern[1:]
    if "/" not in pattern:
        # basename match at any depth, per gitattributes(5)
        return _glob_segment(rel_posix.rsplit("/", 1)[-1], pattern)
    return _glob_path(rel_posix, pattern)


def _glob_segment(name: str, pattern: str) -> bool:
    """`fnmatch` on a single path component (no separators involved)."""
    return fnmatch.fnmatchcase(name, pattern)


def _glob_path(rel_posix: str, pattern: str) -> bool:
    """Match a path against a slash-aware glob, honouring `**`."""
    regex = []
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if pattern.startswith("**/", i):
            regex.append("(?:.*/)?")     # zero or more leading directories
            i += 3
            continue
        if pattern.startswith("**", i):
            regex.append(".*")
            i += 2
            continue
        if ch == "*":
            regex.append("[^/]*")        # a single `*` never crosses a `/`
        elif ch == "?":
            regex.append("[^/]")
        elif ch == "/":
            regex.append("/")
        else:
            regex.append(re.escape(ch))
        i += 1
    return re.fullmatch("".join(regex), rel_posix) is not None


class _LiteralPathResolver(ast.NodeVisitor):
    """Module-level names whose value is a path built only from literals.

    Deliberately narrow. It follows exactly two roots — ``Path(__file__)``
    walked up with ``.parent`` / ``.parents[N]``, and a name this same module
    already resolved — joined with string literals via ``/``. Anything built at
    run time (a ``tmp_path`` fixture, a function argument, a constant imported
    from another package) resolves to nothing and is skipped, which is the
    point: those are not committed files, and guessing at them is how a lint
    starts crying wolf.
    """

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.names: Dict[str, Path] = {}

    def visit_Assign(self, node: ast.Assign) -> None:
        resolved = self._resolve(node.value)
        if resolved is not None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.names[target.id] = resolved

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        # `GOLDEN: Path = REPO_ROOT / "x.json"` — annotated, same shape.
        if node.value is None or not isinstance(node.target, ast.Name):
            return
        resolved = self._resolve(node.value)
        if resolved is not None:
            self.names[node.target.id] = resolved

    def _resolve(self, node: ast.AST) -> Optional[Path]:
        if isinstance(node, ast.Name):
            return self.names.get(node.id)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            left = self._resolve(node.left)
            if left is None:
                return None
            right = node.right
            if isinstance(right, ast.Constant) and isinstance(right.value, str):
                return left / right.value
            return None
        if isinstance(node, ast.Attribute) and node.attr == "parent":
            base = self._resolve(node.value)
            return None if base is None else base.parent
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) \
                and node.value.attr == "parents":
            base = self._resolve(node.value.value)
            index = node.slice
            if base is None or not isinstance(index, ast.Constant) \
                    or not isinstance(index.value, int):
                return None
            try:
                return base.parents[index.value]
            except IndexError:
                return None
        if isinstance(node, ast.Call):
            func = node.func
            # `.resolve()` / `.absolute()` are identity here: the file path this
            # walks from is already absolute.
            if isinstance(func, ast.Attribute) and func.attr in ("resolve", "absolute"):
                return self._resolve(func.value)
            if isinstance(func, ast.Name) and func.id == "Path" and len(node.args) == 1:
                arg = node.args[0]
                if isinstance(arg, ast.Name) and arg.id == "__file__":
                    return self.file_path
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    candidate = Path(arg.value)
                    return candidate if candidate.is_absolute() else None
        return None


#: Attribute calls that read a file's exact bytes, or text that a byte-exact
#: golden comparison is one edit away from. `read_text()` is included because
#: its universal-newline translation only *hides* an unpinned CRLF checkout —
#: the consumer instance that prompted this had two such comparisons sitting
#: latent until someone switched them to `read_bytes()`.
_BYTE_EXACT_READS = ("read_bytes", "read_text")


def _read_call_name(node: ast.AST,
                    readers: Tuple[str, ...] = _BYTE_EXACT_READS
                    ) -> Optional[Tuple[str, int]]:
    """`(name, lineno)` if *node* is `NAME.read_bytes()` / `NAME.read_text()`.

    *readers* narrows which of the two counts. The comparison and hash sites
    pass `("read_text",)`: `read_bytes()` is collected unconditionally a few
    lines below, so letting them match it too appended every such read twice.
    Harmless downstream — the caller dedupes by resolved path — but the two
    rules are disjoint by construction and the code should say so.
    """
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr in readers \
            and isinstance(func.value, ast.Name):
        return func.value.id, func.lineno
    return None


def _byte_exact_reads(tree: ast.AST) -> List[Tuple[str, int]]:
    """`(name, lineno)` for reads whose bytes are actually *compared*.

    The narrowing that keeps this lint worth reading. An earlier draft flagged
    every `NAME.read_text()` in the tests tree and, run against a real consumer,
    produced twenty-odd warnings of which the overwhelming majority were plain
    helper reads --

        def _read_progress() -> str:
            return _PROGRESS_PATH.read_text(encoding="utf-8")

    -- whose callers go on to assert a *substring*. Universal-newline
    translation makes those immune to the CRLF rewrite, so a pin buys them
    nothing and the warning is pure noise. Requiring the read to sit directly
    inside an equality comparison, or to be fed to a hash, is what separates
    `a.read_bytes() == golden.read_bytes()` from reading a file to look inside
    it. A read stored in a local and compared later is missed on purpose: that
    indirection is the shape of a determinism check between two generated
    files, which needs no pin at all.

    **The two readers are not equally safe, and the split above is drawn on
    exactly that** (issue #124). `read_text()` applies universal-newline
    translation, so a CRLF-rewritten file arrives with `\n` either way: a
    *parsed* text read — `json.loads`, a Markdown table walked cell by cell —
    is immune to the rewrite, and covering it would be wrong rather than merely
    noisy. `read_bytes()` translates nothing, so that immunity does not exist
    for it and **any** use of it on a committed path is byte-sensitive; the
    `\r` survives into whatever parses the result. Hence: `read_bytes()`
    anywhere counts, `read_text()` only where its result is compared or hashed.

    Review caught the earlier version of this docstring claiming the immunity
    for the whole "parses rather than byte-compares" class. It is a property of
    `read_text()`, not of parsing — measured: `p.read_bytes().decode()` on a
    CRLF checkout leaves `' value\r'` in the last cell of a Markdown row where
    `read_text()` leaves `' value'`.

    What stays silent is a `read_text()` parse, and that silence is still not
    coverage: the file may need a pin for a byte-reproducibility claim asserted
    somewhere this lint cannot see — a regenerate-and-diff, a digest kept
    elsewhere — and that claim is the project's to assert directly.
    """
    # Reads sitting directly under a membership or ordering test — `b"{" in
    # p.read_bytes()`. Kept exempt from the blanket `read_bytes()` rule below:
    # the needle is what decides there, and a literal one carrying no newline
    # is immune to the rewrite. Collected first because `ast.walk` reaches the
    # inner call without the Compare that gives it its meaning.
    loose_operands: set = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        sides = [node.left, *node.comparators]
        for i, side in enumerate(sides):
            # `a == b < c` is one node meaning `a == b and b < c`, so an
            # operand is exempt only when *neither* comparison it takes part
            # in is an equality. Judging the node as a whole exempted `b` here,
            # which really is on one side of an `==`.
            adjacent = [op for j, op in enumerate(node.ops) if j in (i - 1, i)]
            if not any(isinstance(op, (ast.Eq, ast.NotEq)) for op in adjacent):
                loose_operands.add(id(side))

    out: List[Tuple[str, int]] = []
    for node in ast.walk(tree):
        # `read_bytes()` in any other position. It translates nothing, so there
        # is no context in which the CRLF rewrite passes through it harmlessly
        # — the `\r` survives into whatever parses the result.
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "read_bytes"
                and isinstance(node.func.value, ast.Name)
                and id(node) not in loose_operands):
            out.append((node.func.value.id, node.func.lineno))
            continue
        if isinstance(node, ast.Compare):
            # Only `==` / `!=`: an ordering or membership test on file contents
            # is not a byte-exactness claim.
            if not all(isinstance(op, (ast.Eq, ast.NotEq)) for op in node.ops):
                continue
            for side in [node.left, *node.comparators]:
                found = _read_call_name(side, ("read_text",))
                if found is not None:
                    out.append(found)
        elif isinstance(node, ast.Call):
            func = node.func
            # `h.update(p.read_bytes())` and `hashlib.sha256(p.read_bytes())` --
            # a digest is a byte-exact claim by another name, and the recorded
            # whole-tree-hash failures took exactly this shape.
            is_hash_sink = (
                (isinstance(func, ast.Attribute)
                 and (func.attr == "update"
                      or func.attr.startswith(("sha", "md5", "blake"))))
                or (isinstance(func, ast.Name)
                    and func.id.startswith(("sha", "md5", "blake")))
            )
            if not is_hash_sink:
                continue
            for arg in node.args:
                found = _read_call_name(arg, ("read_text",))
                if found is not None:
                    out.append(found)
    return out


def gitattributes_eol_pin_warnings(repo_root: Path,
                                   config: Dict[str, Dict[str, object]]) -> List[str]:
    """Warn on a committed fixture compared byte-for-byte with no `eol=lf` pin.

    conventions.md §6 states the rule — *"a committed byte-exact fixture needs a
    `.gitattributes` `text eol=lf` pin"* — and until now nothing checked it.
    Without the pin, `core.autocrlf` rewrites the file on a Windows checkout and
    every byte comparison against it fails **on Windows only**, which is exactly
    the platform §7 says no gate in this loop ever sees. The recorded instance
    cost 13 red tests across three modules, invisible to every local run.

    **Precision over recall, deliberately.** The resolver follows only paths
    built from literals — `Path(__file__)` walked up, joined with string
    constants — so a fixture whose path arrives from a `tmp_path` fixture, a
    function argument or a constant imported from another package resolves to
    nothing and is skipped in silence. That is not a gap to be closed later by
    guessing: the overwhelming majority of `read_bytes()` calls in a real suite
    compare two *freshly generated* files to each other (a determinism check),
    and those need no pin at all. Flagging them would make the lint noise, and a
    lint that cries wolf stops being read. What remains — a literal path or an
    obvious glob beside a `read_bytes()` — is every instance recorded so far.

    A resolved path is only reported if it **exists** in the checkout, which is
    the cheap proxy for "committed": a path that resolves but is not there is a
    generated artifact, not a fixture.

    **Two causes of silence, and only one of them is the one above.** The first
    is resolution: a path this lint cannot follow is skipped. The second is
    shape, in `_byte_exact_reads` — a committed artifact whose tests
    `read_text()` and *parse* draws no warning whether or not it is pinned,
    because universal newlines make that read immune. The second is the one
    that misleads, because such a file looks exactly like the kind this lint
    exists for. Recorded (issue #124): a spec wrote "the eol-pin lint passes"
    as an acceptance criterion for a committed generated JSON artifact its
    tests `json.loads`; the criterion was vacuous by construction, and the pin
    had to be asserted by a project-side test instead. Read a warning here as
    authoritative and silence as *no reading taken*.
    """
    files = _test_files(repo_root, config)
    if not files:
        return []
    patterns = _gitattributes_no_rewrite_patterns(repo_root)
    out: List[str] = []
    seen: set = set()
    root = repo_root.resolve()
    for path in files:
        try:
            source = path.read_text(encoding=_ENCODING)
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        resolver = _LiteralPathResolver(path.resolve())
        resolver.visit(tree)
        if not resolver.names:
            continue
        for name, lineno in _byte_exact_reads(tree):
            target = resolver.names.get(name)
            if target is None:
                continue
            try:
                rel = target.resolve().relative_to(root)
            except ValueError:
                continue                      # outside the repo: not ours to pin
            if not target.exists():
                continue                      # generated, not committed
            rel_posix = rel.as_posix()
            key = (_rel_display(path, repo_root), rel_posix)
            if key in seen:
                continue
            seen.add(key)
            if patterns is None:
                out.append(
                    f"{_rel_display(path, repo_root)}:{lineno}: compares "
                    f"{rel_posix} byte-for-byte, but this repo has no "
                    f".gitattributes — on a Windows checkout core.autocrlf "
                    f"rewrites it and the comparison fails there and nowhere "
                    f"else. Add `{rel_posix} text eol=lf`. See conventions.md §6")
                continue
            if any(_gitattributes_matches(rel_posix, p) for p in patterns):
                continue
            out.append(
                f"{_rel_display(path, repo_root)}:{lineno}: compares "
                f"{rel_posix} byte-for-byte, but no .gitattributes `eol=lf` "
                f"pin covers it — on a Windows checkout core.autocrlf rewrites "
                f"it and the comparison fails there and nowhere else. Add "
                f"`{rel_posix} text eol=lf`. See conventions.md §6")
    return out


def nested_deliverable_warnings(lines: List[str]) -> List[str]:
    """Status-bearing bullets nested anywhere inside a stage section.

    The parser matches indented bullets, so a nested one counts as a full
    deliverable in the rollup and in item-status parsing. The nesting says
    "subordinate" to a reader while the tooling says "peer" — so a `📋` child
    quietly holds its ✅ parent's stage open, and nothing reconciles the two
    readings.

    **Scanned across the whole stage section, deliberately, not just the
    Deliverables block.** `stage_deliverable_statuses` reads `lines[start:end]`
    — every leading-icon bullet in the section, skipping only checkboxes — so an
    indented status bullet under **Acceptance** drags the stage exactly the same
    way. Verified: such a bullet turns `['complete']` into
    `['complete', 'planned']` and a ✅ stage into 🚧. Narrowing this to the
    Deliverables block would under-report a bullet that really does break the
    rollup.
    """
    out: List[str] = []
    for start, end, num in stage_sections(lines):
        for i in range(start, end):
            m = _NESTED_DELIVERABLE_RE.match(lines[i])
            if m:
                out.append(
                    f"progress.md:{i + 1}: stage {num} has a nested status bullet "
                    f"({m.group('icon')}) — the rollup counts it as a full "
                    f"deliverable despite the indent, so it can hold the stage "
                    f"open while reading as subordinate. Flatten it, or drop "
                    f"its icon.")
    return out


def _bullet_prose(lines: List[str], start: int, last: int) -> str:
    """A deliverable bullet's text with its icon and trailing marker removed,
    whitespace-normalised — the part an author wrote about the work."""
    body = lines[start:last + 1]
    # Tail first, then head: on a one-line bullet both cuts land on the same
    # string, and the marker's offset is only right before the icon is gone.
    marker = _BULLET_MARKER_RE.search(body[-1])
    if marker is not None:
        body[-1] = body[-1][:marker.start()]
    first = _BULLET_RE.match(lines[start])
    if first:
        body[0] = body[0][first.end():]
    return " ".join(part.strip() for part in body).strip()


def identical_deliverable_warnings(lines: List[str]) -> List[str]:
    """Single-item deliverable bullets in one stage with the same prose.

    That shape is what `_split_multi_item_bullets` leaves behind: a shared
    ``*(Items …)*`` marker desugared into one bullet per item, every copy
    carrying the sentence written for all of them. It is correct the moment
    it is written and wrong the moment one copy is ticked — the ✅ then
    describes the siblings' work as done — and rewording is invisible to every
    other check, so an un-reworded copy simply stood (issue #169). Reported
    per stage and per prose, naming the items, until each copy says what its
    own item delivers. A consumer that genuinely ships two identical
    deliverables in one stage sees the same warning; the remedy is the same
    sentence either way.
    """
    out: List[str] = []
    for start, end, num in stage_sections(lines):
        groups: Dict[str, List[Tuple[int, int]]] = {}
        for s, last in _deliverable_bullet_spans(lines[start:end]):
            s, last = s + start, last + start
            items = _bullet_marker_item_numbers(lines[last])
            if len(items) != 1:
                continue
            prose = _bullet_prose(lines, s, last)
            if prose:
                groups.setdefault(prose, []).append((items[0], s + 1))
        for prose, hits in groups.items():
            if len(hits) < 2:
                continue
            listed = ", ".join(f"{n:03d}" for n, _ in hits)
            out.append(
                f"progress.md:{hits[0][1]}: stage {num} has {len(hits)} "
                f"deliverable bullets with identical prose, attributed to "
                f"items {listed} — the shape a split of a shared *(Items …)* "
                f"marker leaves behind, so a ✅ on one describes the others' "
                f"work too. Reword each copy to say what its own item "
                f"delivers.")
    return out


def unattributed_reference_warnings(lines: List[str]) -> List[str]:
    """Deliverable bullets that reference items but attribute none of them.

    Only a bullet's trailing ``*(Item NNN)*`` marker ties items to it (§1,
    issue #99). A bullet whose references all sit mid-prose therefore tracks
    nothing: the items it names stay planned, hold their queue open, and
    `aide progress set` cannot find the bullet — a silent gap unless it is
    reported where the author can fix it. A bullet that has a trailing marker
    is fine, whatever else its prose mentions: the prose is free text by
    design, not a mistake.
    """
    out: List[str] = []
    for start, last in _deliverable_bullet_spans(lines):
        if _bullet_marker_item_numbers(lines[last]):
            continue
        span_text = "\n".join(lines[start:last + 1])
        nums = sorted(set(_referenced_item_numbers(span_text)))
        if nums:
            listed = ", ".join(f"{n:03d}" for n in nums)
            out.append(
                f"progress.md:{start + 1}: deliverable bullet references "
                f"item(s) {listed} but ends with no *(Item NNN)* marker — only "
                f"the trailing marker ties an item to a bullet, so this bullet "
                f"tracks nothing and those items read as untracked. End it "
                f"with the marker (e.g. '. *(Item {nums[0]:03d})*').")
    return out


def _line_after_title(lines: List[str]) -> str:
    """The first content line after the `#` title, or "" if there is none.

    Two subtleties. A multi-line HTML comment must be skipped **whole** — only
    its opening line starts with `<!--`, so testing line-by-line lets its body
    read as content. And the search stops at the first line after the title
    rather than skipping further headings: "opens with a blockquote" means the
    next thing, so `# Title` / `## Intro` / `> …` does not satisfy it.
    """
    in_comment = False
    seen_title = False
    for line in lines:
        stripped = line.strip()
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                in_comment = True
            continue
        if not stripped:
            continue
        if not seen_title:
            if stripped.startswith("#"):
                seen_title = True
            continue
        return stripped
    return ""


def header_blockquote_warnings(ddir: Path) -> List[str]:
    """Living documents that do not open with their header blockquote.

    The blockquote carries the document's place in the loop and what it derives
    from — structural facts a reader landing anywhere needs (conventions.md §1).
    """
    out: List[str] = []
    targets = [ddir / name for name in _BLOCKQUOTE_DOCS]
    for sub in ("queue", "items"):
        if (ddir / sub).is_dir():
            targets.extend(sorted((ddir / sub).glob("*.md")))
    for path in targets:
        if not path.is_file():
            continue
        first = _line_after_title(path.read_text(encoding=_ENCODING).splitlines())
        if not first.startswith(">"):
            # Relative to docs_dir, matching `progress.md:12` and `items/…`.
            rel = path.relative_to(ddir).as_posix()
            out.append(f"{rel}: no header blockquote — the line after the title "
                       f"should carry this document's place in the loop and what "
                       f"it derives from")
    return out


#: The vision sections `templates/vision.md` marks `MANDATORY`, minus Goals &
#: objectives, whose mandatory substance is the G-code table checked separately
#: — a heading over an empty section would satisfy a heading check while giving
#: the roadmap nothing to trace. Each entry: (heading text, why it is needed).
_VISION_MANDATORY_SECTIONS = (
    ("Guiding principles", "the validator checks implementation against these"),
    ("Out of scope", "the validator flags work that contradicts this"),
    ("Success criteria", "they define when the project is done"),
)


def _has_g_code_row(lines: List[str]) -> bool:
    """True when any table row's first cell names a vision G-code (`G1 …`).

    The shape both mandatory tables share: vision's objectives table and the
    roadmap's objective → stage coverage table each open every row with the
    G-code. Cell counts differ (3 and 2), so the first cell is the invariant.
    """
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        cells = _split_row(line)
        if cells and re.match(r"G\d+\b", cells[0]):
            return True
    return False


#: The two build postures `vision.md`'s optional header line may name
#: (conventions.md §1 → vision.md, issue #241). A closed set: the line says how
#: much to build, and a value nobody defined is a value no role can apply.
_VISION_POSTURES = ("prototype", "durable")


#: The separators a header blockquote line folds several labelled fields with.
#: `templates/vision.md` writes `**Status:** … · **Created:** …` on one line, so
#: a posture folded onto it is a field of that line rather than a line of its
#: own — read by field, or an explicit `durable` reads as no posture at all.
_HEADER_FIELD_SEP_RE = re.compile(r"[\u00b7|]")


def vision_posture(text: str) -> Optional[str]:
    """The value of `vision.md`'s optional `**Posture:** …` header field, or ``None``.

    The scan window is every line above the first `##` heading that starts with
    `>`; each such line is split into fields on `·` and `|`, and each field has
    its quote marker and emphasis removed before its label is read. So the line
    of its own the template writes, the plain `> Posture: durable`, and a
    posture folded onto the `**Status:** … · **Created:** …` line with the
    template's own separator are one shape. The first field labelled `posture`
    wins. The value is returned exactly as written, including an unknown or
    empty one: deciding what it means is the caller's, and the check below
    warns rather than correcting it.

    ``None`` means the document carries no such field, which §1 → vision.md
    reads as ``prototype``. This returns ``None`` rather than that default so
    the two states stay distinguishable — the check must not warn about an
    absent line, and a role that wants the default applies it itself.
    """
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("##"):
            break
        if not stripped.startswith(">"):
            continue
        for field in _HEADER_FIELD_SEP_RE.split(stripped[1:]):
            plain = field.replace("*", "").replace("`", "").strip()
            if plain.lower().startswith("posture:"):
                return plain.split(":", 1)[1].strip()
    return None


def root_document_warnings(ddir: Path) -> List[str]:
    """Root documents missing the sections their templates mark MANDATORY.

    `templates/vision.md` annotates four sections `MANDATORY: validator
    checks…` and `templates/roadmap.md` two, and until issue #86 nothing
    verified any of them: a hand-written vision with none of the sections
    passed `aide check`, so the promise the annotations make was kept by no
    code. The observed failure is exactly that — a vision authored free-hand
    in a consumer, structurally plausible, checked by nobody.

    Headings are matched tolerantly (any level, the template's `2.` numbering
    optional, case-insensitive): the lint is for a *dropped* section, and a
    renumbered heading is not a dropped section.

    The vision's optional build posture is read here too (issue #241): a value
    that is neither `prototype` nor `durable` is warned about by name, while an
    absent line is not — absence is the default, and warning about it would ask
    every vision to state the value it already has.

    Warnings, not errors, matching the item specs' mandatory-Assumptions lint:
    root documents predating this check exist in real consumers, and an
    unattended run must not start failing over a document none of its items
    touch — the queue-boundary human reads warnings. A missing file is silent:
    a repo may adopt the CLI without the root documents (issue #57), and
    `create-progress` onward is where `progress.md` becomes a hard error.
    """
    out: List[str] = []
    vpath = ddir / "vision.md"
    if vpath.is_file():
        vtext = vpath.read_text(encoding=_ENCODING)
        for title, why in _VISION_MANDATORY_SECTIONS:
            if not re.search(rf"^#{{1,6}}\s*(?:\d+\.\s*)?{title}\b", vtext,
                             re.MULTILINE | re.IGNORECASE):
                out.append(f"vision.md: no '{title}' section — the template "
                           f"marks it MANDATORY: {why}")
        posture = vision_posture(vtext)
        if posture is not None and posture.lower() not in _VISION_POSTURES:
            # Named, not corrected, and never silently defaulted: a typo that
            # meant `durable` would otherwise build less than the human asked
            # for and say nothing. An absent line is the default and is silent.
            out.append(f"vision.md: the header's Posture line reads "
                       f"'{posture}', which is neither 'prototype' nor "
                       f"'durable' — no role applies an unknown posture, and "
                       f"a vision with no Posture line at all is read as "
                       f"'prototype'")
        if not _has_g_code_row(vtext.splitlines()):
            out.append("vision.md: no G-code objectives table (rows opening "
                       "'| G1 |…') — the template marks it MANDATORY: the "
                       "roadmap and progress.md trace every stage back to "
                       "these codes")
    rpath = ddir / "roadmap.md"
    if rpath.is_file():
        rtext = rpath.read_text(encoding=_ENCODING)
        if not _has_g_code_row(rtext.splitlines()):
            out.append("roadmap.md: no objective → stage coverage rows "
                       "(opening '| G1 …|') — the template marks the table "
                       "MANDATORY: it is what shows every vision G-code "
                       "mapped to a stage")
        if not re.search(r"^#{1,6}\s*Stage\s+\d+", rtext,
                         re.MULTILINE | re.IGNORECASE):
            out.append("roadmap.md: no '## Stage N — Title' sections — the "
                       "template marks the shape MANDATORY: queues are scoped "
                       "to a stage and progress.md is generated from these "
                       "sections")
    return out


#: The line every template carries after its header comment, and every document
#: created from one keeps: ``<!-- aide-template: progress 1 -->``. The name is
#: the template's file stem and the number its own integer version, which moves
#: only when the template changes in a way a document built from the old one
#: would want to follow — independent of ``VERSION`` (issue #164).
_TEMPLATE_MARKER_RE = re.compile(
    r"^<!--\s*aide-template:\s*(?P<name>[a-z][a-z0-9-]*)\s+(?P<version>\d+)\s*-->\s*$",
    re.MULTILINE)
#: A line that opens like the marker, so one the regex above rejects is reported
#: rather than taken for a document with no marker at all.
_TEMPLATE_MARKER_OPENER_RE = re.compile(r"^<!--\s*aide-template:", re.MULTILINE)


def _above_title(text: str) -> str:
    """The part of *text* before its first heading line — where the marker lives.

    Every template puts the line between its header comment and its title, and a
    document whose header comment was deleted keeps it above the title. Reading
    only that far means a marker quoted in a document's body — an example in an
    item spec, a note about a template change — is never taken for the
    document's own.
    """
    m = re.search(r"^#", text, re.MULTILINE)
    return text[:m.start()] if m else text


def template_marker(text: str) -> Optional[Tuple[str, int]]:
    """``(name, version)`` from the marker line above *text*'s title, or ``None``."""
    m = _TEMPLATE_MARKER_RE.search(_above_title(text))
    return (m.group("name"), int(m.group("version"))) if m else None


def installed_template_versions() -> Dict[str, int]:
    """``name -> version`` for every template installed beside this script.

    A template without a readable marker is left out, so a document naming it
    is reported as naming a template this engine does not ship — the truthful
    reading of an install that lost the line.
    """
    versions: Dict[str, int] = {}
    if not _TEMPLATES_DIR.is_dir():
        return versions
    for path in sorted(_TEMPLATES_DIR.glob("*.md")):
        marker = template_marker(path.read_text(encoding=_ENCODING))
        if marker and marker[0] == path.stem:
            versions[marker[0]] = marker[1]
    return versions


def template_drift_warnings(ddir: Path, item_status: Dict[int, str],
                            installed: Optional[Dict[str, int]] = None) -> List[str]:
    """Documents whose template marker disagrees with the installed template.

    Rung 4 of the copies rule (``ADAPTER-SPEC.md``, *Copies of engine text*):
    ``docs/aide/**`` is the project's, so the engine *reports* a document that
    predates its template and never fails a run over one. A template gaining a
    section reaches the next document created from it and no earlier one;
    before the marker, nothing recorded which template a document was built
    from, and the only signal was a changelog entry nobody was pointed at.

    Which documents are read, and why:

    * ``vision.md``, ``roadmap.md``, ``progress.md``, ``insights.md`` and
      ``ledger.md`` — long-lived, appended to or edited for the life of the
      project, so a newer template is something their author may still act on.
    * A queue while it is open, and an item spec while its item is not ✅ or
      ❌ — the same measure ``--queue`` uses for "spent". A finished item's
      spec is a record, and a warning on every one of them each time a template
      moves is permanent noise over files nobody should edit.

    Only the marker above the title counts (``_above_title``). A document
    **without** one is silent. Every document written before
    the marker existed has none, and the engine cannot say which template it
    came from; a warning that asks the author to guess a version names no
    action, and repeating it on every run is how a real warning gets tuned out.
    A line that opens like the marker but does not parse is reported, since
    that one the author wrote and can fix.
    """
    if installed is None:
        installed = installed_template_versions()
    targets = [ddir / name for name in
               ("vision.md", "roadmap.md", "progress.md", "insights.md",
                "ledger.md")]
    qdir = ddir / "queue"
    if qdir.is_dir():
        for qpath in iter_queue_paths(qdir):
            if queue_is_open(qpath.read_text(encoding=_ENCODING), item_status):
                targets.append(qpath)
    idir = ddir / "items"
    if idir.is_dir():
        for ipath in sorted(idir.glob("*.md")):
            n = item_spec_number(ipath)
            if n is not None and item_status.get(n, "planned") in (
                    "complete", "excluded"):
                continue
            targets.append(ipath)

    out: List[str] = []
    for path in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding=_ENCODING)
        rel = path.relative_to(ddir).as_posix()
        marker = template_marker(text)
        if marker is None:
            if _TEMPLATE_MARKER_OPENER_RE.search(_above_title(text)):
                out.append(f"{rel}: unreadable aide-template line — expected "
                           f"'<!-- aide-template: <name> <N> -->'")
            continue
        name, version = marker
        current = installed.get(name)
        if current is None:
            out.append(f"{rel}: names template '{name}', which this engine "
                       f"does not ship")
        elif version < current:
            out.append(f"{rel}: created from {name} template {version}; the "
                       f"installed template is {current} — the framework "
                       f"CHANGELOG entry naming '{name} template {current}' "
                       f"says what changed and what, if anything, to edit; "
                       f"then set the line to {current}")
        elif version > current:
            out.append(f"{rel}: created from {name} template {version}, newer "
                       f"than the installed {current} — this checkout runs an "
                       f"older engine than the document was written under")
    return out


#: An assumption bullet that names the engine it was true for — the §1 marker
#: ``- **A8 (engine 1.28.1):** …``. The engine version goes in the bold label,
#: beside the assumption's own code, because that is where a reader looking for
#: "which claim is this?" already is; a version buried in the assumption's prose
#: is not read, so a claim about engine behaviour written without the marker
#: goes unchecked rather than wrongly checked.
#:
#: The marker is free-form apart from the word ``engine`` and a SemVer triple:
#: it may carry a re-check — ``(engine 1.28.1, re-checked 1.35.0)`` — and the
#: **newest** version it names is the one the claim currently stands on.
#: The **label run** of an assumption bullet: the bold opener the template
#: writes. Two real spellings, and the marker has to survive both — the closing
#: `**` may sit right after the label (`- **A8 (engine 1.28.1):** …`) or at the
#: end of the whole sentence (`- **A8 (engine 1.28.1): the CLI warns …**`),
#: which is what one consumer's 112 specs actually use. An unbolded bullet
#: falls back to the text before its first colon, so `- A8 (engine 1.28.1): …`
#: is read too; without that boundary the marker would be hunted through the
#: assumption's whole prose, where a version is being discussed rather than
#: pinned.
_ASSUMPTION_LABEL_RE = re.compile(r"^\s*[-*]\s+(?:\*\*(?P<bold>.+?)\*\*|(?P<plain>[^:*]*):)")
#: A parenthesised marker naming the engine, anywhere in that label run.
_ENGINE_MARKER_RE = re.compile(r"\(([^)]*engine[^)]*)\)", re.IGNORECASE)
#: A SemVer triple anywhere in that marker. Prerelease and build suffixes are
#: not read: the comparison below is on `major.minor` alone, and a consumer
#: running `1.29.0-rc1` is on 1.29 for the purpose of "has the engine moved".
_SEMVER_RE = re.compile(r"\b(\d+)\.(\d+)\.(\d+)\b")


def _feature_line(version: str) -> Optional[Tuple[int, int]]:
    """``(major, minor)`` of *version*, or ``None`` if it is not SemVer.

    Deliberately drops the patch. This repo's own bump policy defines patch as
    "a fix with no interface change", so a patch release cannot falsify a claim
    about what a verb does or what `check` reports — warning on one would be
    noise the consumer cannot act on, on a record it is not allowed to rewrite.
    """
    m = _SEMVER_RE.search(version)
    return (int(m.group(1)), int(m.group(2))) if m else None


def assumption_engine_pin(line: str) -> Optional[Tuple[str, str]]:
    """``(label, version)`` for an engine-marked assumption bullet, else None.

    *version* is the newest SemVer triple in the marker, so a re-check note
    supersedes the original pin: that is how a stale marker is cleared without
    rewriting the assumption itself — the claim stands, and what was learned
    about it afterwards is appended, exactly as `progress amend` and an
    insights status trail already work (§1).
    """
    m = _ASSUMPTION_LABEL_RE.match(line)
    if not m:
        return None
    run = m.group("bold") or m.group("plain") or ""
    versions = [f"{a}.{b}.{c}"
                for marker in _ENGINE_MARKER_RE.findall(run)
                for a, b, c in _SEMVER_RE.findall(marker)]
    if not versions:
        return None
    newest = max(versions, key=lambda v: tuple(int(x) for x in v.split(".")))
    # The label is what stands before the marker — "A8" out of "A8 (engine
    # 1.28.1): the CLI warns …" — so the warning names the assumption the way
    # the spec's own cross-references do.
    label = run.split("(", 1)[0].strip().rstrip(":").strip()
    return (label or "assumption"), newest


def _assumption_bullets(text: str) -> List[str]:
    """The bullets of the ``## Assumptions`` block, each joined onto one line.

    Joining is the whole point: a real spec's assumption runs to a paragraph,
    so its bold label routinely opens on the bullet line and closes two lines
    down — two of the three specs issue #144 was filed over are written that
    way. A line-at-a-time reader sees an unterminated `**`, matches nothing,
    and the check silently never fires.

    A blank line ends a bullet, a `## ` heading ends the block, and a `### `
    sub-heading does not: it is still inside Assumptions.
    """
    out: List[str] = []
    current: Optional[str] = None
    in_block = False
    for line in text.splitlines():
        if re.match(r"^##\s+", line):
            if current:
                out.append(current)
                current = None
            in_block = bool(re.match(r"^##\s+Assumptions\b", line))
            continue
        if not in_block:
            continue
        if re.match(r"^\s*[-*]\s+\S", line):
            if current:
                out.append(current)
            current = line.strip()
        elif current is not None:
            if line.strip():
                current += " " + line.strip()
            else:
                out.append(current)
                current = None
    if current:
        out.append(current)
    return out


def _stale_assumption_pins(text: str, engine: str) -> List[Tuple[str, str]]:
    """Engine-marked assumptions in *text* whose engine predates *engine*.

    Reads the ``## Assumptions`` block only. An assumption is a durable record
    that outlives its branch and can legitimately pin **engine** behaviour —
    what `aide check` warns about, what a verb does — and `install.py --update`
    says nothing about the specs whose assumptions it has just falsified
    (issue #144). One consumer carried three merged specs asserting warnings a
    later release had deliberately removed, one of them calling their presence
    "expected output"; nothing detected it, and the specs are records, so the
    repair is not to edit them.
    """
    installed = _feature_line(engine)
    if installed is None:
        return []
    out: List[Tuple[str, str]] = []
    for bullet in _assumption_bullets(text):
        pin = assumption_engine_pin(bullet)
        if pin is None:
            continue
        pinned = _feature_line(pin[1])
        if pinned is not None and pinned < installed:
            out.append(pin)
    return out


def item_spec_warnings(ddir: Path, ddir_rel: str = "docs/aide",
                       engine: Optional[str] = None) -> List[str]:
    """Item specs that break the shapes §1 and §5 fix.

    Four rules: the `# Item NNN — Title` heading must agree with the filename
    (the status report parses the title from it); the header must carry NO
    status field (status lives only in progress.md, and a duplicate has no
    owner and only drifts); the **Assumptions** block is mandatory, since it
    is what the validator surfaces for audit; and no always-authorised path
    may sit under **Asserts against** — the loop itself edits those on every
    item (the mandatory status flip alone touches progress.md), so the pin can
    never hold and `aide scope` would fail the item on its routine
    bookkeeping. Pinning progress.md is the natural way to write an AC that
    reads a gate row, which is exactly why it needs a spec-time warning.

    A fifth is advisory rather than structural: an assumption marked with the
    engine it was true for — `- **A8 (engine 1.28.1):** …` — whose engine
    predates the installed one. See `_stale_assumption_pins`.

    None of them reads a file that no lookup finds: one whose name
    `item_spec_number` rejects gets a single warning naming the rename instead
    (issue #228), since every verb that reads a spec treats its item as having
    none, and a number printed off the filename would disagree with them.

    *ddir_rel* is the docs dir as specs spell it in their repo-relative paths;
    `run_checks` passes the configured value, and the default matches the
    scaffolded `aide.toml`. *engine* is the installed engine version, as
    `.aide/VERSION` holds it; `None` (the default, and what a script copied
    away from its VERSION file gets) skips the assumption check entirely.

    The missing-Assumptions finding is reported as ONE aggregated line. Specs
    predating the rule are common — 32 of 112 in the consumer this was measured
    against — and 32 separate warnings would bury the substantive ones, which is
    the failure mode issue #13 was filed for.
    """
    idir = ddir / "items"
    if not idir.is_dir():
        return []
    always = _always_authorised_paths(ddir_rel)
    out: List[str] = []
    missing_assumptions: List[str] = []
    stale_pins: List[str] = []
    for path in sorted(idir.glob("*.md")):
        num = item_spec_number(path)
        if num is None:
            out.append(_unfindable_spec_warning(path))
            continue
        text = path.read_text(encoding=_ENCODING)
        if not re.search(rf"^#\s+Item\s+0*{num}\s*[—–-]\s*\S", text, re.MULTILINE):
            out.append(f"items/{path.name}: no '# Item {num:03d} — Title' heading "
                       f"matching the filename")
        head = text.split("\n---", 1)[0]
        # A FIELD, not bold emphasis. Two conditions keep this precise: the line
        # is part of the header blockquote, and a colon sits beside the bold —
        # inside it (`**Status:**`, the template's own spelling) or right after
        # (`**Status**:`). Matching bare `**Status**` anywhere would flag prose
        # that merely emphasises the word.
        sm = next((m for line in head.splitlines() if line.lstrip().startswith(">")
                   for m in [_ITEM_STATUS_FIELD_RE.search(line)] if m), None)
        if sm:
            out.append(f"items/{path.name}: header carries a '{sm.group('name')}' field — "
                       f"status lives only in progress.md; a duplicate has no owner "
                       f"and only drifts")
        if not re.search(r"^##\s+Assumptions", text, re.MULTILINE):
            missing_assumptions.append(f"{num:03d}")
        elif engine:
            stale_pins.extend(f"{num:03d} {label} (engine {version})"
                              for label, version in _stale_assumption_pins(text, engine))
        parsed = parse_authorised_paths(text)
        for pin in (parsed.asserts_against if parsed else []):
            if any(patterns_overlap(pin, a) for a in always):
                out.append(
                    f"items/{path.name}: '{pin}' is pinned under Asserts "
                    f"against, but every item is authorised to edit it — the "
                    f"status flip and the insight append are loop bookkeeping "
                    f"— so the pin can never hold and `aide scope` will report "
                    f"a contradiction on every run; put the read-only content "
                    f"check in an acceptance criterion's test instead")
        # Asserts against means pinned-NOT-changed — `aide scope` prints
        # exactly that — so a path the spec also authorises itself to change
        # is a contradiction authored into the spec: the moment the item uses
        # the authorisation, scope fails it with no spec-side fix visible
        # (issue #94). Exact double-listing only: a literal pin under a May
        # change glob is the legitimate carve-out shape ("I may edit docs/**
        # but not docs/api.md") and scope stays the judge of whether it held.
        # Silent narrowing, made loud where it is authored (issue #119): the
        # spans after a bullet's first are dropped, and so is anything on a
        # continuation line, so the item is authorised for less than its spec
        # says and only an `aide scope` FAIL much later reveals it.
        for declared, dropped in dropped_bullet_spans(text):
            shown = ", ".join(f"'{d}'" for d in dropped)
            out.append(
                f"items/{path.name}: the Authorised paths bullet for "
                f"'{declared}' also names {shown}, and `aide scope` reads none "
                f"of them — a bullet declares ONE path, the first backtick "
                f"span of its opening line, and a continuation line is not "
                f"read at all. Give each path its own bullet, or the item is "
                f"authorised for less than its spec says")
        may_normalised = {_strip_dot_slash(p.strip())
                         for p in (parsed.may_change if parsed else [])}
        for pin in (parsed.asserts_against if parsed else []):
            if _strip_dot_slash(pin.strip()) in may_normalised:
                out.append(
                    f"items/{path.name}: '{pin}' is listed under both May "
                    f"change and Asserts against — Asserts against means "
                    f"pinned-not-changed, so `aide scope` will report every "
                    f"change to it as a contradiction. If the item writes the "
                    f"file and its tests assert against the final state, list "
                    f"it only under May change and say so in prose")
    if missing_assumptions:
        shown = ", ".join(missing_assumptions[:8])
        more = (f" (+{len(missing_assumptions) - 8} more)"
                if len(missing_assumptions) > 8 else "")
        out.append(f"{len(missing_assumptions)} item spec(s) have no mandatory "
                   f"'## Assumptions' block: {shown}{more} — it is what the "
                   f"validator surfaces for audit at the queue boundary")
    if stale_pins:
        shown = "; ".join(stale_pins[:6])
        more = f" (+{len(stale_pins) - 6} more)" if len(stale_pins) > 6 else ""
        out.append(f"{len(stale_pins)} assumption(s) pin an engine older than "
                   f"the installed {engine}: {shown}{more} — the engine has "
                   f"moved under the claim, so re-check it before a reader "
                   f"trusts it. The spec is a record: append the outcome to "
                   f"the marker (`(engine 1.28.1, re-checked {engine})`) "
                   f"rather than rewriting the assumption")
    return out


def _stray_icons_in_line(line: str) -> List[str]:
    """Status icons on this line that sit where one could plausibly be
    mistaken for a structural status declaration.

    conventions.md §1 is explicit that icons are read *only* at structural
    positions — a deliverable bullet's leading icon, a table row's last cell,
    a stage header's trailing icon — and that "an icon anywhere else […] is
    plain text and is never read as status, so authors need not avoid the
    icon vocabulary in free text." A bullet with no leading icon, or an
    ordinary paragraph, therefore has *no* structural position at all, and
    any icon it contains is exactly that free text — never stray. Only a
    heading, whose sole structural slot is the trailing icon, can still carry
    a status-shaped icon somewhere a reader would misread as the header's
    status.
    """
    icons = list(_ICON_RE.finditer(line))
    if not icons:
        return []
    if _QUEUE_STATUS_RE.match(line):
        return []  # "> **Status:** …" lines legitimately carry an icon
    if line.strip().startswith("|"):
        return []  # table rows: parsers read specific cells only, never prose
    if _BULLET_RE.match(line):
        return []  # bullets: only the leading icon is structural; the rest is free prose
    if re.match(r"^#{1,6}\s", line):  # any heading level may carry a trailing icon
        t = _TRAILING_ICON_RE.search(line)
        allowed = t.span(1) if t else None
        return [i.group(0) for i in icons if i.span() != allowed]
    return []  # ordinary paragraph text: no structural position exists here at all


def stray_icon_warnings(ddir: Path) -> List[str]:
    """Warn on status icons outside structural positions in the status-bearing
    documents (``progress.md`` and queue files).

    The parsers only ever read icons at structural positions (conventions.md
    §1), so a stray icon is never *misread* — this lint surfaces near-misses so
    the status documents stay unambiguous to human readers too. Other documents
    (vision, roadmap, item specs) are not scanned: nothing parses icons there,
    so their prose is free.
    """
    out: List[str] = []
    paths: List[Path] = []
    progress = ddir / "progress.md"
    if progress.is_file():
        paths.append(progress)
    paths.extend(iter_queue_paths(ddir / "queue"))
    for path in paths:
        for lineno, line in enumerate(path.read_text(encoding=_ENCODING).splitlines(), start=1):
            for icon in _stray_icons_in_line(line):
                out.append(
                    f"{path.relative_to(ddir).as_posix()}:{lineno}: status icon {icon} outside a "
                    f"structural status position (parsers treat it as plain text; move "
                    f"or remove it if status was intended)"
                )
    return out


def run_checks(repo_root: Path, config: Dict[str, Dict[str, object]],
               branches: Optional[List[str]] = None) -> Tuple[List[str], List[str]]:
    """Return ``(errors, warnings)``. Empty errors == pass.

    The first thirteen checks all run before, and survive, the two early returns
    below, but for two different reasons. Six of them —
    `absolute_path_test_warnings`, `separator_dependent_test_warnings`,
    `cli_subprocess_test_warnings`, `subprocess_encoding_test_warnings`,
    `gitattributes_eol_pin_warnings`, `scope_claim_test_warnings` — read
    `tests_dir` and never touch `docs_dir`, so they are the ones that make this
    function worth calling in a repo with no document set. The other seven *are* document checks; they
    simply find nothing to say when `docs_dir` is absent, so keeping them costs
    nothing and they still report on a `docs_dir` that exists but has no
    `progress.md`.

    Three cases, kept apart: a repo with **no `docs_dir` at all** gets the
    test-hygiene lints and passes; a `docs_dir` that **exists but is not a
    directory** is a misconfigured `aide.toml` and an error; and a `docs_dir`
    that is a directory but has **lost its `progress.md`** is the error it
    always was.
    """
    errors: List[str] = []
    warnings: List[str] = []
    ddir = docs_dir(repo_root, config)
    progress_path = ddir / "progress.md"

    errors.extend(template_residue_errors(ddir))
    errors.extend(conflict_marker_errors(ddir))
    warnings.extend(stray_icon_warnings(ddir))
    warnings.extend(insight_warnings(ddir))
    warnings.extend(ledger_warnings(ddir))
    warnings.extend(absolute_path_test_warnings(repo_root, config))
    warnings.extend(separator_dependent_test_warnings(repo_root, config))
    warnings.extend(cli_subprocess_test_warnings(repo_root, config))
    warnings.extend(subprocess_encoding_test_warnings(repo_root, config))
    warnings.extend(gitattributes_eol_pin_warnings(repo_root, config))
    warnings.extend(scope_claim_test_warnings(repo_root, config))
    warnings.extend(header_blockquote_warnings(ddir))
    warnings.extend(root_document_warnings(ddir))
    # A docs_dir outside the repo falls back to its absolute spelling, which
    # cannot appear in a spec's repo-relative paths — the always-authorised
    # pin lint then has nothing to match; the other spec-shape lints still
    # apply.
    warnings.extend(item_spec_warnings(ddir, _rel_display(ddir, repo_root),
                                       installed_engine_version()))
    if ddir.exists() and not ddir.is_dir():
        # `docs_dir` pointing at something that is not a directory is a
        # misconfiguration, and a third case again: it is neither "no document
        # set" nor "a document set missing its progress.md". Left folded into
        # the partial-adoption branch below it would report "this repo has no
        # AIDE document set" and exit 0 — a typo in aide.toml passing as a
        # deliberate choice not to adopt the loop.
        errors.append(
            f"{_rel_display(ddir, repo_root)} is configured as docs_dir but is "
            f"not a directory — fix [project] docs_dir in aide.toml")
        return errors, warnings
    if not ddir.is_dir():
        # Two different situations used to produce one error. A repo with no
        # document set at all is not a broken loop repo — it is a repo that
        # adopted the conventions and the CLI without the roadmap documents,
        # and the document checks simply do not apply to it. Everything above
        # has already run and is kept: three of those lints read `tests_dir`,
        # not `docs_dir`, and conflating the two cases made them unreachable
        # for any such repo — this framework's own repository included, which
        # is where they were written (issue #57).
        return errors, warnings
    if not progress_path.is_file():
        # `docs_dir` exists but its central document does not: a real error.
        return [f"missing {progress_path}"], warnings
    # One read, reused: two reads can disagree if the file changes between them.
    text = progress_path.read_text(encoding=_ENCODING)
    lines = text.splitlines()
    # Before anything reads the tables: a row no reader can use is dropped by
    # every check below, including the ones that would have errored on it.
    errors.extend(unreadable_row_errors(lines))
    warnings.extend(gate_warnings(lines))
    warnings.extend(capability_warnings(lines, config.get("validation") or {}))
    # A withdrawn attestation is normal, not a defect — the point is that it
    # stays visible. Retracting is append-only, so without a surfacing rule the
    # withdrawal would live only in one commit's diff, which is exactly the
    # quiet the trail exists to prevent.
    for stg, cn, cdate, creason in retracted_criteria(lines):
        warnings.append(
            f"progress.md: stage {stg} criterion {cn} was retracted on "
            f"{cdate} ({creason}) — the box is open again, and the original "
            f"attestation is kept above the correction")
    warnings.extend(nested_deliverable_warnings(lines))
    warnings.extend(identical_deliverable_warnings(lines))
    warnings.extend(unattributed_reference_warnings(lines))
    warnings.extend(acceptance_drift_warnings(ddir, lines))
    warnings.extend(template_drift_warnings(ddir, _parse_item_status(lines)[2]))

    # Mandatory sections. Rows are taken by shape from anywhere in the file,
    # with the one test `unreadable_row_errors` reports the failures of.
    # A table whose every row is unreadable is present, and already reported
    # row by row; "missing" on top of that would send the author looking for
    # a table that is there. One written without leading `|` is missing: no
    # reader or writer here has ever taken a row from it.
    table_rows = [_split_row(l) for l in lines if l.strip().startswith("|")]
    reported = {t.name for t, *_ in _unreadable_rows(lines)}
    has_stage_table = (any(_reads(_STAGE_SUMMARY, c) for c in table_rows)
                       or _STAGE_SUMMARY.name in reported)
    has_obj_table = (any(_reads(_OBJECTIVE_COVERAGE, c) for c in table_rows)
                     or _OBJECTIVE_COVERAGE.name in reported)
    sections = stage_sections(lines)
    if not has_stage_table:
        errors.append("progress.md: missing Stage summary table")
    if not has_obj_table:
        errors.append("progress.md: missing Objective coverage table")
    if not sections:
        errors.append("progress.md: no '## Stage N' sections")

    # Summary row status vs. section header + rollup consistency.
    summary_status: Dict[str, str] = {}
    for cells in table_rows:
        if _reads(_STAGE_SUMMARY, cells):
            summary_status[cells[0]] = _icon_status(cells[3])

    section_nums = set()
    for start, end, num in sections:
        section_nums.add(num)
        header_status = _header_status(lines[start])
        derived = rollup_status(stage_deliverable_statuses(lines, start, end))
        summ = summary_status.get(num)
        if summ in ("deferred", "excluded"):
            continue
        if derived == "complete" and summ and summ != "complete":
            warnings.append(
                f"stage {num}: all deliverables ✅ but summary shows {summ} — "
                f"if the work shipped but the stage's goal is unmet, record the "
                f"goal as an Outcome target (❌ Not met) and close the stage; "
                f"stages track shipped work, targets track measured outcomes")
        if summ == "complete" and derived and derived != "complete":
            errors.append(f"stage {num}: summary marked ✅ but has non-complete deliverables")
        if header_status and summ and header_status != summ:
            warnings.append(f"stage {num}: header {header_status} disagrees with summary {summ}")

    for num in summary_status:
        if num not in section_nums:
            warnings.append(f"stage {num}: in summary table but has no '## Stage {num}' section")

    # Outcome targets: goal truth gates the OBJECTIVE rows. Claiming an
    # objective ✅ over an unmet target is the goal-level over-claim this
    # table exists to prevent (issue #14) — the mirror of the deliverable-level
    # error above.
    obj_status: Dict[str, str] = {}
    for cells in table_rows:
        if _reads(_OBJECTIVE_COVERAGE, cells):
            obj_status[re.match(r"G\d+", cells[0]).group(0)] = _icon_status(cells[2])
    for t in outcome_targets(lines):
        if t.kind is None:
            warnings.append(
                f"progress.md:{t.lineno}: outcome target '{t.text}' has an "
                f"unrecognised Status (expected '✅ Met', '❌ Not met' or "
                f"'❓ Unverified')")
        for g in t.objectives:
            if obj_status.get(g) != "complete":
                continue
            if t.kind == "not-met":
                errors.append(
                    f"objective {g} marked ✅ but outcome target '{t.text}' "
                    f"is ❌ Not met")
            elif t.kind != "met":
                warnings.append(
                    f"objective {g} marked ✅ but outcome target '{t.text}' "
                    f"is not ✅ Met")

    # Queues: state is DERIVED from progress.md (open = any 📋/🚧 item); a
    # declared "> **Status:**" line is decorative — warn only when it lies.
    qdir = ddir / "queue"
    seen: Dict[int, str] = {}
    if qdir.is_dir():
        _, _, istat = _parse_item_status(lines)
        for qpath in iter_queue_paths(qdir):
            qtext = qpath.read_text(encoding=_ENCODING)
            derived_open = queue_is_open(qtext, istat)
            declared = queue_status(qtext)
            if declared:
                declared_live = declared.lower().startswith("live")
                if declared_live and not derived_open:
                    warnings.append(
                        f"{qpath.name}: declares 'Live' but every item is finished — "
                        f"state is derived from progress.md; run 'aide queue tidy' "
                        f"or drop the decorative Status line")
                elif not declared_live and derived_open:
                    warnings.append(
                        f"{qpath.name}: marked completed but still has open items "
                        f"in progress.md")
            for n in queue_item_numbers(qtext):
                if n in seen and seen[n] != qpath.name:
                    errors.append(f"item {n:03d} appears in both {seen[n]} and {qpath.name}")
                seen[n] = qpath.name

    # Item spec files: no duplicate numbers.
    idir = ddir / "items"
    if idir.is_dir():
        spec_nums: Dict[int, str] = {}
        for ipath in sorted(idir.glob("*.md")):
            n = item_spec_number(ipath)
            if n is None:
                continue  # item_spec_warnings names it
            if n in spec_nums:
                errors.append(f"duplicate item spec number {n:03d}: {spec_nums[n]} and {ipath.name}")
            spec_nums[n] = ipath.name

    # Claim-branch <-> status agreement (best effort).
    prefix = str(config["git"].get("branch_prefix", "aide/"))
    if branches is None:
        branches = _list_claim_branches(repo_root, prefix)
    _, _, item_status = _parse_item_status(lines)
    unpublished = (set(_unpublished_branches(repo_root, config, prefix))
                   if branches else set())
    for br in branches:
        n = _branch_item_number(br, prefix)
        if br in unpublished:
            # Read against the last fetch, like every other remote question
            # here, and a warning rather than an error for that reason.
            warnings.append(
                f"unpublished branch {br}: this checkout has it and origin "
                f"does not, so it is invisible to every other checkout — a "
                f"failed 'aide claim' or 'aide queue start' push is the usual "
                f"cause. Publish it ('git push -u origin {br}') or delete it.")
        if n is None:
            # Not a claim branch. A queue branch is expected and silent; anything
            # else carrying the prefix is reported rather than ignored, so a real
            # stale claim named unconventionally cannot hide behind the anchor.
            if not _is_queue_branch(br, prefix):
                warnings.append(
                    f"unrecognised branch {br}: carries the claim prefix but is "
                    f"not '{prefix}NNN-short-name' (conventions.md §4), so no "
                    f"item status is tracked for it — rename it to the claim "
                    f"shape, or once it is merged run 'aide gc --merged' to "
                    f"delete it")
            continue
        # 🔍 is deliberately NOT reported: a claim branch whose item is awaiting
        # review is a normal, correct state, and warning about it on every run
        # until the human merges is how a real warning gets tuned out.
        if item_status.get(n) == "complete":
            warnings.append(f"stale claim branch {br}: item {n:03d} is already ✅")

    return errors, warnings


def _parse_item_status(lines: List[str]) -> Tuple[List[str], List[str], Dict[int, str]]:
    """Map item number -> most-advanced status found on its deliverable bullets.

    The only structural status declaration (conventions.md §1) is a deliverable
    bullet's leading icon — a line matching ``_BULLET_RE`` — together with any
    of its wrapped continuation lines (indented text carrying no bullet marker
    of its own). A reference anywhere else — a table cell, an acceptance
    checkbox, an ordinary paragraph — is free text and is never read as status,
    however many item numbers it happens to name (issue #15): a verification
    table's Notes column narrating what went wrong with several items, or a
    checkbox that merely cites the item that satisfies it, must not pull that
    item's tracked status backwards.

    Within a bullet, only the trailing ``*(Item NNN)*`` marker attributes — §1
    already calls it "the suffix [that] ties an item to the bullet". A
    reference form elsewhere in the bullet's prose is as free as one in a
    table cell: a ✅ bullet whose text mentions a live sibling ("absorbing
    *(Item 095)*'s scope") used to mark that sibling complete, overriding its
    own 📋 bullet — and once spent items were discounted from the cross-spec
    checks, the mis-attribution silenced exactly the pre-build errors the
    checks exist to raise (issue #99).
    """
    item_status: Dict[int, str] = {}
    for start, last in _deliverable_bullet_spans(lines):
        bullet_status = ICON_TO_STATUS[_BULLET_RE.match(lines[start]).group("icon")]
        for num in _bullet_marker_item_numbers(lines[last]):
            if num not in item_status or RANK[bullet_status] > RANK[item_status[num]]:
                item_status[num] = bullet_status
    return [], [], item_status


# --------------------------------------------------------------------------- #
# git plumbing
# --------------------------------------------------------------------------- #
def git(args: List[str], repo_root: Path, check: bool = True) -> subprocess.CompletedProcess:
    """Run git and hand back its output decoded as UTF-8, never as the locale.

    conventions.md §6, applied to the engine that states it. `text=True` alone
    decodes with `locale.getpreferredencoding()` — cp1252 on a Windows
    consumer — so a branch name, a changed path or a commit subject carrying a
    non-ASCII character came back as different characters there than here, and
    a prefix match against it quietly stopped matching. Git speaks UTF-8 for
    refs and paths, so this says so.

    `errors="replace"` rather than strict: a stray byte in one branch name must
    not raise out of `aide claim`. The replacement character fails the same
    match a mangled one did, and does it identically on every platform.
    """
    return subprocess.run(
        ["git", *args], cwd=str(repo_root), check=check,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8", errors="replace",
    )


def _push_new_branch(repo_root: Path, branch: str) -> Optional[str]:
    """``git push -u origin <branch>``: None on success, else a sentence.

    Three verbs publish a branch they have just created — `queue start`,
    `claim`, and `merge` under `pr` mode — and all three pushed with git()'s
    default `check=True`, so every cause of a failed push (no remote at all,
    origin unreachable, expired credentials, a rejecting server-side hook)
    left `main()` on a `CalledProcessError`: a raw traceback in a flow whose
    whole point is to run unattended. `cmd_queue_start` guarded exactly one
    cause in prose — the branch already on origin — and let the rest crash.

    The push is the *last* thing each of those verbs does, so its local half is
    already on disk when it fails. Handing back git's own words lets each
    caller say what survives and how to finish it by hand, which is the
    difference between a stall a person can act on and a stack trace.
    """
    res = git(["push", "-u", "origin", branch], repo_root, check=False)
    if res.returncode == 0:
        return None
    detail = (res.stderr.strip() or res.stdout.strip()
              or f"git exited {res.returncode} without a message")
    return f"pushing {branch} to origin FAILED:\n{detail}"


def _list_claim_branches(repo_root: Path, prefix: str) -> List[str]:
    if not (repo_root / ".git").exists():
        return []
    try:
        out_local = git(["branch", "--format=%(refname:short)"], repo_root, check=False).stdout
        out_remote = git(["branch", "-r", "--format=%(refname:short)"], repo_root, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    names: List[str] = []
    for line in (out_local + out_remote).splitlines():
        name = line.strip()
        short = name.split("/", 1)[1] if name.startswith("origin/") else name
        if short.startswith(prefix):
            names.append(short)
    return sorted(set(names))


# --------------------------------------------------------------------------- #
# command handlers
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Cross-spec queue check — do a queue's specs conflict, before any is built?
# --------------------------------------------------------------------------- #
class SpecFinding(NamedTuple):
    """One cross-item conflict between the specs on a queue."""

    severity: str          # "error" | "warning"
    kind: str              # machine-readable class, for the --report seam
    items: Tuple[int, ...]
    message: str


def patterns_overlap(a: str, b: str) -> bool:
    """True when two ``## Authorised paths`` patterns can cover the same file.

    Deliberately decides only the cases a script *can* decide: an identical
    pattern, a subtree wildcard swallowing the other, and a literal path
    covered by the other's glob. Two unrelated globs that would happen to
    intersect on some file neither spec has thought of are not modelled —
    reporting those would mean guessing at a future tree, and this check exists
    to be trusted, not to be argued with.
    """
    a = _strip_dot_slash(a.strip())
    b = _strip_dot_slash(b.strip())
    if a == b:
        return True
    for x, y in ((a, b), (b, a)):
        if x.endswith("/**"):
            prefix = x[: -len("/**")]
            if y == prefix or y.startswith(prefix + "/"):
                return True
    if not any(c in a for c in "*?[") and path_matches(a, b):
        return True
    if not any(c in b for c in "*?[") and path_matches(b, a):
        return True
    return False


def _built_after(graph: Dict[int, List[int]]) -> Dict[int, Set[int]]:
    """For each item, every item it is built *after* — its declared
    dependencies and theirs, transitively.

    The ordering `## Dependencies` actually promises. Direct listing is not
    enough on its own: an item that names one sibling which in turn names
    another is built after both, and the pair the caller is about to judge may
    be the far end of that chain.

    Cycle-safe by the `in out` guard rather than by trusting the graph — a
    mutual pair is a real shape here (`_dependency_cycles` reports it as the
    error it is) and must not hang the check that discovers it.
    """
    closure: Dict[int, Set[int]] = {}
    for node in graph:
        out: Set[int] = set()
        stack = list(graph.get(node, []))
        while stack:
            dep = stack.pop()
            if dep in out:
                continue
            out.add(dep)
            stack.extend(graph.get(dep, []))
        out.discard(node)
        closure[node] = out
    return closure


def _dependency_cycles(graph: Dict[int, List[int]]) -> List[List[int]]:
    """Every dependency cycle in *graph*, each reported once.

    A cycle deadlocks `aide claim` outright: every item in it is blocked by
    another item in it, so none is ever claimable and the queue silently stops
    producing work rather than failing.
    """
    cycles: List[List[int]] = []
    seen: set = set()
    state: Dict[int, int] = {}   # 0 = visiting, 1 = done

    def walk(node: int, stack: List[int]) -> None:
        state[node] = 0
        stack.append(node)
        for nxt in graph.get(node, []):
            if state.get(nxt) == 0:
                cycle = stack[stack.index(nxt):]
                key = tuple(sorted(cycle))
                if key not in seen:
                    seen.add(key)
                    cycles.append(cycle)
            elif nxt not in state and nxt in graph:
                walk(nxt, stack)
        stack.pop()
        state[node] = 1

    for node in sorted(graph):
        if node not in state:
            walk(node, [])
    return cycles


def queue_spec_findings(repo_root: Path, config: Dict[str, Dict[str, object]],
                        number: int) -> Tuple[List[SpecFinding], List[int]]:
    """``(findings, unspecced)`` for every spec on queue *number*.

    Runs in the window `/aide-spec-queue` creates and currently leaves
    unguarded: N specs authored on one branch before any is built, where every
    cross-item conflict is both possible and cheap to fix. The invariant it
    enforces is the one a consumer's post-mortem arrived at — *predicting the
    one collision a spec happens to name is not the same as proving no sibling
    assertion depends on state this item's authorised edit changes.*
    """
    ddir = docs_dir(repo_root, config)
    qdir = ddir / "queue"
    qpath = queue_path(qdir, number)
    if qpath is None:
        return ([SpecFinding("error", "missing-queue", (),
                             f"no {queue_name(number)} file under "
                             f"{_rel_display(qdir, repo_root)}")],
                [])

    numbers = queue_item_numbers(qpath.read_text(encoding=_ENCODING))
    idir = ddir / "items"
    findings: List[SpecFinding] = []
    unspecced: List[int] = []
    declared: Dict[int, AuthorisedPaths] = {}

    # A finding against a SPENT item — merged (✅) or excluded (❌) — is an
    # error no later item can clear: the spec is a record nobody may edit, a
    # merged May-change claim can neither be harmed by a later writer nor harm
    # one, and an excluded item is never offered. Such findings are reported
    # for the rest of the queue's life, which teaches a reader to skim the run
    # where one is real — so spent items are discounted below, on both sides
    # of every comparison. Deferred (⏸️) items are NOT spent: their claims are
    # dormant, not dead, and a conflict with one is worth surfacing while
    # re-planning is still cheap.
    item_status = _progress_item_status(repo_root, config)
    spent = {n for n in numbers
             if item_status.get(n, "planned") in ("complete", "excluded")}

    for num in numbers:
        specs = item_spec_paths(idir, num)
        if not specs:
            # Normal mid-queue state, not a conflict: /aide-spec-queue exists to
            # fill these. Counted and reported, never silently dropped.
            unspecced.append(num)
            continue
        parsed = parse_authorised_paths(specs[0].read_text(encoding=_ENCODING))
        rel = _rel_display(specs[0], repo_root)
        if declares_nothing(parsed):
            if num not in spent:
                # A spent spec with no scope section merged (or was dropped)
                # regardless; the remedy the message names is no longer
                # available, so the warning would be pure unclearable noise.
                findings.append(SpecFinding(
                    "warning", "undeclared-scope", (num,),
                    f"item {num:03d} ({rel}) declares no '## Authorised paths' — its "
                    f"scope cannot be compared with its siblings'. Add the section "
                    f"(conventions.md §1); until then this item needs a human scope "
                    f"review, and `aide scope` cannot check it either"))
            continue
        declared[num] = parsed

    # Read once, used twice: the declared ordering exempts pinned-state pairs
    # below, and the same edges are the cycle graph further down. Reading each
    # spec's Dependencies section twice would be the only alternative.
    deps_by_item = {num: _item_dependencies(repo_root, config, num)
                    for num in numbers if num not in unspecced}
    # An item is built after everything it declares a dependency on, and after
    # what those declare in turn — but only along edges that still ORDER the
    # two items. A dependency `aide claim` no longer waits for does not hold
    # its dependent back: a ⏸️ deferred blocker is skipped by `_pick_item`, so
    # the dependent is claimable today and would pin a tree the deferred item
    # has not touched yet. Filtering the edges rather than the pairs also
    # settles the transitive case, where the link that fails to hold is an
    # intermediate: `b → c (⏸️) → a` leaves b free to build before a.
    ordering_edges = {num: [d for d in deps
                            if item_status.get(d, "planned") in BLOCKING_STATUSES]
                      for num, deps in deps_by_item.items()}
    built_after = _built_after(ordering_edges)

    # The loop bookkeeping every item writes anyway (`aide scope` authorises
    # these without them being listed). Specs often list them redundantly, and
    # two items "conflicting" over progress.md is not a conflict — it is the
    # claim protocol working. Excluded from the overlap check, never from the
    # pinned-state check: pinning progress.md would be a real assertion.
    ddir_rel = _rel_display(ddir, repo_root)
    bookkeeping = set(_always_authorised_paths(ddir_rel))

    ordered = sorted(n for n in declared if n not in spent)
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            # Row 1 — two items claim edit rights on the same file.
            for pa in declared[a].may_change:
                if pa in bookkeeping:
                    continue
                for pb in declared[b].may_change:
                    if patterns_overlap(pa, pb):
                        findings.append(SpecFinding(
                            "warning", "may-change-overlap", (a, b),
                            f"items {a:03d} and {b:03d} both claim '{pa}'"
                            + (f" / '{pb}'" if pa != pb else "")
                            + " under May change — whichever builds second "
                              "inherits the first's edits; confirm that is intended"))
        # Rows 2+3 — one item may change what another pins. Under the
        # `## Authorised paths` vocabulary these are one check: an "Asserts
        # against" entry covers a byte-hash pin and a live recomputation alike,
        # which is the point — the live-recomputed case is the one a survey
        # hunting fragile-looking hashes missed.
        for b in ordered:
            if a == b:
                continue
            if a in built_after.get(b, ()):
                # Item a still holds item b back — b declares a dependency on
                # it, directly or through a chain, along links that all still
                # order (`ordering_edges`). So b is authored and built against
                # a tree that already holds a's edit: a landing cannot break a
                # pin b writes afterwards, by construction. This is the whole shape
                # of a `Validate stage N` item — it exists to pin the artifacts
                # its stage's items produce, and it names them as dependencies
                # — which made the error fire against every such item, with
                # neither remedy the message offers available: widening the pin
                # drops what the item exists to observe, and narrowing the
                # earlier edits removes the stage's whole point. A pair with no
                # declared dependency keeps the error: an undeclared ordering
                # is exactly what this check exists to find.
                continue
            for pa in declared[a].may_change:
                for pb in declared[b].asserts_against:
                    if patterns_overlap(pa, pb):
                        findings.append(SpecFinding(
                            "error", "changes-pinned-state", (a, b),
                            f"item {a:03d} may change '{pa}', which item {b:03d} "
                            f"pins as '{pb}' under Asserts against — item {b:03d}'s "
                            f"assertion breaks when item {a:03d} lands. Decide now "
                            f"which side is wrong: widen the pin, narrow the edit, "
                            f"or — if item {b:03d} is meant to be built after item "
                            f"{a:03d} and to pin what it produced — say so under "
                            f"item {b:03d}'s '## Dependencies', which both orders "
                            f"the queue and retires this finding"))

    # Row 5 — the dependency graph. A cycle deadlocks `aide claim`: every item
    # in it is blocked by another in it, so the queue silently stops producing
    # work rather than failing. The graph holds only items that can still
    # block a claim — the same status set `_pick_item` treats as blocking: a
    # complete, excluded or deferred dependency does not block, and such an
    # item is never offered, so no cycle through one can deadlock (a cycle
    # whose members all merged has PROVED its order was satisfiable). The typo
    # pass below shares the filter: a mistyped dependency in a spent or
    # deferred item's spec blocks nothing today, and the warning about it
    # would be unclearable.
    graph = {num: deps for num, deps in deps_by_item.items()
             if item_status.get(num, "planned") in BLOCKING_STATUSES}
    for cycle in _dependency_cycles(graph):
        chain = " → ".join(f"{n:03d}" for n in cycle + [cycle[0]])
        findings.append(SpecFinding(
            "error", "dependency-cycle", tuple(cycle),
            f"dependency cycle {chain} — every item in it is blocked by another "
            f"in it, so `aide claim` will never offer any of them"))

    known = set(numbers)
    for num, deps in graph.items():
        for dep in deps:
            if dep in known:
                continue
            has_spec = bool(item_spec_paths(idir, dep))
            in_a_queue = any(dep in queue_item_numbers(p.read_text(encoding=_ENCODING))
                             for p in iter_queue_paths(ddir / "queue"))
            if not has_spec and not in_a_queue:
                findings.append(SpecFinding(
                    "warning", "unknown-dependency", (num, dep),
                    f"item {num:03d} depends on item {dep:03d}, which has no spec "
                    f"and appears in no queue — a typo here blocks the item forever"))

    return findings, unspecced


def _write_findings_report(path: Path, number: int,
                           findings: List[SpecFinding],
                           unspecced: List[int]) -> None:
    """Write the machine-readable report — the seam a reviewer pass consumes as
    its worklist rather than re-deriving what this check already decided."""
    payload = {
        "queue": number,
        "unspecced_items": unspecced,
        "findings": [
            {"severity": f.severity, "kind": f.kind,
             "items": list(f.items), "message": f.message}
            for f in findings
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    # Plain utf-8, NOT `_ENCODING`: that is utf-8-sig, which writes a BOM. A BOM
    # is right for the markdown documents (Windows editors add one and the
    # parsers must tolerate it) and wrong here — `json.loads` rejects a leading
    # BOM outright, so the seam would be unreadable by the very consumer it
    # exists for.
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def cmd_check(args: argparse.Namespace) -> int:
    """The consistency gate over the document set — and two writes.

    One is asked for by flag: ``--report PATH`` writes the cross-spec findings
    file for `spec-reviewer`. The other is ``ensure_insights_inbox``: a
    ``docs_dir`` that exists but has no ``insights.md`` gets one, byte-exact
    from the template, committed where git allows, and the run says so in a
    ``notice:``. It is the engine keeping §1's promise that capture is a plain
    append to a file that exists, placed in the verb every consumer is told to
    run before its first unattended run. The exit code never depends on it:
    the creation cannot fail a run — a commit that git refuses, or a ``git``
    that cannot be run, is a sentence in the notice, not an error — and a
    document set whose inbox already exists is reported exactly as before.
    """
    queue = getattr(args, "queue", None)
    if getattr(args, "report", None) and queue is None:
        # Silently ignoring it would be worse than refusing: the caller asked
        # for a file that would never appear, and only the missing file would
        # ever say so.
        print("aide check: --report needs --queue; there are no cross-spec "
              "findings to report without one", file=sys.stderr)
        return 2

    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    ddir = docs_dir(repo_root, config)
    # Before the checks, so the file they then shape-check is the one that
    # exists — a run that created the inbox and warned about its absence in
    # the same breath would be reporting on two different repositories.
    ensure_insights_inbox(repo_root, config, verb="check")
    errors, warnings = run_checks(repo_root, config)

    if not ddir.exists() and queue is None:
        # A notice, not a warning: nothing is wrong, but the reader must not
        # read "OK" as "the documents were checked and are fine".
        #
        # Only on a non-`--queue` run. `--queue` sends `queue_spec_findings`
        # looking for a queue file under the same absent directory, so it runs
        # and errors — and "only the repo-agnostic checks ran" would be false
        # next to that error. The notice exists to stop a *pass* being
        # over-read; a run that fails needs no such guard.
        print(f"notice: no {_rel_display(ddir, repo_root)}/ — this repo has no "
              f"AIDE document set, so only the repo-agnostic checks ran")

    if queue is not None:
        findings, unspecced = queue_spec_findings(repo_root, config, queue)
        for f in findings:
            (errors if f.severity == "error" else warnings).append(f.message)
        if unspecced:
            listed = ", ".join(f"{n:03d}" for n in unspecced)
            print(f"aide check: queue {queue:03d} — {len(unspecced)} item(s) "
                  f"not yet specced, so not compared: {listed}")
        report = getattr(args, "report", None)
        if report:
            _write_findings_report(Path(report), queue, findings, unspecced)
            print(f"aide check: wrote {report}")

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    if errors:
        print(f"aide check: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1
    print(f"aide check: OK ({len(warnings)} warning(s))")
    return 0


def set_gate_status(text: str, index: int, kind: str,
                    note: Optional[str] = None, today: Optional[str] = None) -> str:
    """Resolve the *index*-th (1-based) row of the ``## Human gates`` table.

    Writes the decision and the date into the Status cell, and *note* into the
    last cell. Raises ``ValueError`` for a missing table or an out-of-range
    index — a typo must not pass as a silent no-op, which is exactly how a
    hand-edited gate went wrong before there was a verb for it.
    """
    lines = text.splitlines()
    gates = human_gates(lines)
    if not gates:
        raise ValueError("no '## Human gates' table in progress.md")
    if not 1 <= index <= len(gates):
        raise ValueError(f"there are {len(gates)} human gate(s); {index} is out of range")
    gate = gates[index - 1]
    if note and ("|" in note or "\n" in note or "\r" in note):
        raise ValueError(
            "the note may not contain '|' or a line break — either breaks the "
            "row's shape, and a gate row the parser cannot read stops being a "
            "gate: `aide check` fails and `aide claim` holds every item until "
            "someone repairs it")
    icon = {"approved": "✅ Approved", "declined": "❌ Declined"}[kind]
    import datetime as _dt
    stamp = today or _dt.date.today().isoformat()
    i = gate.lineno - 1
    cells = _split_row(lines[i])
    cells[2] = f"{icon} ({stamp})"
    if note:
        cells[3] = note
    lines[i] = "| " + " | ".join(cells) + " |"
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def cmd_gate(args: argparse.Namespace) -> int:
    """List or resolve the human gates in progress.md.

    Resolving a gate is a **person's** act. No agent may run `approve` or
    `decline`: a gate exists precisely because the decision is not derivable
    from the work, so an agent resolving one destroys the only thing it was
    protecting.
    """
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    ppath = docs_dir(repo_root, config) / "progress.md"
    if not ppath.is_file():
        print(f"aide gate: missing {ppath}", file=sys.stderr)
        return 2
    text = ppath.read_text(encoding=_ENCODING)
    gates = human_gates(text.splitlines())
    unreadable = unreadable_gate_rows(text.splitlines())

    if args.action == "list":
        if not gates and not unreadable:
            print("aide gate: no '## Human gates' table (nothing gated)")
            return 0
        for n, g in enumerate(gates, start=1):
            reach = g.reach
            mark = {"approved": "✅", "declined": "❌", "awaiting": "⏳"}.get(g.kind, "⚠")
            print(f"  {n}. {mark} {g.text} — blocks {reach}")
        # Unnumbered: `approve <n>` counts readable gates only, and a row the
        # parser cannot read is not one a verb should write into.
        for lineno, problem in unreadable:
            print(f"  ⚠ progress.md:{lineno}: a row that {problem} — not a "
                  f"gate, and holds every item until it is fixed")
        outstanding = len(blocking_gates(text.splitlines()))
        print(f"aide gate: {len(gates)} gate(s), {outstanding} still blocking"
              + (f", {len(unreadable)} unreadable row(s) holding everything"
                 if unreadable else ""))
        return 0

    if args.number is None:
        print(f"aide gate: '{args.action}' needs a gate number — see `aide gate list`",
              file=sys.stderr)
        return 2
    kind = "approved" if args.action == "approve" else "declined"
    try:
        updated = set_gate_status(text, args.number, kind, args.note)
    except ValueError as exc:
        print(f"aide gate: {exc}", file=sys.stderr)
        return 2
    # NOT _ENCODING: "utf-8-sig" *strips* a BOM on read but *writes* one, so
    # passing it here made every gate decision prepend U+FEFF to progress.md —
    # manufacturing the exact hazard that constant exists to absorb. Every
    # other writer in this module already writes plain "utf-8"; this was the
    # one outlier. Read tolerantly, write clean.
    ppath.write_text(updated, encoding="utf-8")
    print(f"gate {args.number}: {kind}")
    if not args.no_commit:
        _commit_progress_file(repo_root, config,
                              f"docs: human gate {args.number} {kind}")
    return 0


#: What `aide progress set` accepts, and the tracked status each records.
#: `done` stays the word for ✅ — a consumer's muscle memory and every existing
#: runbook use it — and `in-review` is additive.
_SET_STATUS_MAP = {"in-progress": "in-progress", "in-review": "in-review",
                   "done": "complete"}


def _report_bullet_splits(number: int, lines: List[str],
                          splits: List[BulletSplit]) -> None:
    """Print the copies a flip's split wrote, as the chore they are.

    The split is the engine's edit, made with no author present, and it
    produces N bullets carrying one bullet's prose — text that described the
    shared deliverable and now stands, unchanged, under each item alone. The
    engine cannot write the right words; it can refuse to be silent about the
    wrong ones (issue #169). ``lines`` is the text *after* the flip, so the
    copies print with the icons they ended up with.
    """
    for split in sorted(splits, key=lambda s: s.copies[0][1]):
        print(f"item {number:03d}: split the shared bullet {split.marker} into "
              f"one bullet per item. Every copy still carries the SHARED "
              f"prose — reword each to describe its own item's work, or "
              f"`aide check` keeps reporting them as identical:")
        for _, lineno in split.copies:
            print(f"  progress.md:{lineno}: {lines[lineno - 1].strip()}")


def cmd_progress(args: argparse.Namespace) -> int:
    #: The acceptance verbs, in the order §1 describes them: make an
    #: attestation, correct its evidence, withdraw it, or reword a criterion
    #: nobody has attested yet.
    if args.action == "accept":
        return _cmd_progress_accept(args)
    if args.action == "amend":
        return _cmd_progress_amend(args)
    if args.action == "retract":
        return _cmd_progress_retract(args)
    if args.action == "reword":
        return _cmd_progress_reword(args)
    if args.action != "set":
        print("usage: aide progress set NNN <in-progress|in-review|done>", file=sys.stderr)
        return 2
    if args.status is None:
        print("usage: aide progress set NNN <in-progress|in-review|done>", file=sys.stderr)
        return 2
    if args.status not in _SET_STATUS_MAP:
        print("status must be 'in-progress', 'in-review' or 'done'", file=sys.stderr)
        return 2
    status_map = _SET_STATUS_MAP
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    progress_path = docs_dir(repo_root, config) / "progress.md"
    if not progress_path.is_file():
        print(f"error: {progress_path} not found", file=sys.stderr)
        return 1
    text = progress_path.read_text(encoding=_ENCODING)
    original = text
    # An item is only trackable if some deliverable bullet's trailing marker
    # names it — the ownership rule set_item_status flips by — otherwise the
    # set would be a silent no-op. A prose mention on someone else's bullet
    # does not count (issue #99). When the queue back-fill was missed,
    # self-heal deterministically from the item spec's own Stage/title header;
    # only when that context is missing too does this stay a loud, blocking
    # error.
    healed_note: Optional[str] = None
    if args.number not in _parse_item_status(text.splitlines())[2]:
        stage, title = _spec_stage_and_title(repo_root, config, args.number)
        healed = insert_item_reference(text, args.number, stage, title) if stage and title else None
        if healed is None:
            print(
                f"item {args.number:03d}: ERROR — no deliverable in progress.md "
                f"references 'Item {args.number:03d}', and no item spec with a "
                f"Stage header was found to insert one from; status NOT "
                f"recorded. Add the reference to the owning stage's deliverable "
                f"bullet (e.g. '- 📋 <deliverable>. *(Item {args.number:03d})*'), "
                f"then re-run.",
                file=sys.stderr,
            )
            return 1
        text = healed
        # Announced only after the guard below confirms the back-fill took —
        # a success-flavoured line right before "NOT changed" reads as a
        # contradiction in an unattended log.
        healed_note = (f"item {args.number:03d}: back-filled missing "
                       f"deliverable reference under Stage {stage} "
                       f"(from the item spec)")
    splits: List[BulletSplit] = []
    updated = set_item_status(text, args.number, status_map[args.status], splits)
    if args.number not in _parse_item_status(updated.splitlines())[2]:
        # Belt to the heal's braces: if the back-fill (or anything else) left
        # no bullet whose trailing marker names this item, the set recorded
        # nothing — say so and write nothing, instead of printing success over
        # a silent no-op (the failure shape a review of issue #99 found).
        print(
            f"item {args.number:03d}: ERROR — after the back-fill, no "
            f"deliverable bullet's trailing *(Item {args.number:03d})* marker "
            f"names this item, so the status could not be recorded; progress.md "
            f"NOT changed. Add the marker to the owning bullet's last line, "
            f"then re-run.",
            file=sys.stderr,
        )
        return 1
    if healed_note:
        print(healed_note)
    if updated == original:
        print(f"item {args.number:03d}: no change (already >= {args.status})")
    else:
        progress_path.write_text(updated, encoding="utf-8")
        print(f"item {args.number:03d}: set to {args.status}")
        _report_bullet_splits(args.number, updated.splitlines(), splits)
    if not args.no_commit and (repo_root / ".git").exists():
        _commit_progress(repo_root, config, args.number, args.status)
    return 0


def _cmd_progress_accept(args: argparse.Namespace) -> int:
    """``aide progress accept STAGE --criterion N`` — tick an acceptance box.

    The explicit counterpart to the auto-tick ``set_item_status`` used to
    perform. An acceptance criterion is attested by a human who checked it, so
    it takes a deliberate command that records what was accepted and, with
    ``--evidence``, on what basis.
    """
    if args.criterion is None and not args.all_criteria:
        print("usage: aide progress accept STAGE (--criterion N | --all) "
              "[--evidence TEXT]", file=sys.stderr)
        return 2
    if args.criterion is not None and args.all_criteria:
        print("aide progress accept: pass --criterion or --all, not both", file=sys.stderr)
        return 2
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    progress_path = docs_dir(repo_root, config) / "progress.md"
    if not progress_path.is_file():
        print(f"error: {progress_path} not found", file=sys.stderr)
        return 1
    text = progress_path.read_text(encoding=_ENCODING)
    criteria = None if args.all_criteria else [args.criterion]
    try:
        updated, messages = accept_criteria(text, str(args.number), criteria, args.evidence)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for msg in messages:
        print(f"stage {args.number}: {msg}")
    if updated == text:
        return 0
    progress_path.write_text(updated, encoding="utf-8")
    if not args.no_commit and (repo_root / ".git").exists():
        what = "all criteria" if args.all_criteria else f"criterion {args.criterion}"
        _commit_progress_file(
            repo_root, config, f"progress(aide): stage {args.number} accept {what}")
    return 0


#: ``.aide/VERSION`` beside this script, for the engine stamp a captured
#: insight carries (§1). One directory up from ``scripts/``, which is the
#: layout in a consumer *and* in the framework's own tree (``core/VERSION``),
#: so one relative step serves both — the same reasoning ``_TEMPLATES_DIR``
#: is built on. Missing only where the script has been copied away from its
#: siblings, and that is not an error: the note is free-form and optional, so
#: the entry is written without it.
_VERSION_FILE = Path(__file__).resolve().parents[1] / "VERSION"


def installed_engine_version() -> Optional[str]:
    """The engine version this script belongs to, or None if it cannot be read.

    Two readers: the stamp a captured insight carries (§1), and the assumption
    marker check in `item_spec_warnings`. Both treat a missing file as "say
    nothing" rather than as an error — the script may have been copied away
    from its siblings, and neither reader is load-bearing enough to fail over.
    """
    try:
        v = _VERSION_FILE.read_text(encoding=_ENCODING).strip()
    except OSError:
        return None
    return v or None


def _engine_stamp() -> Optional[str]:
    v = installed_engine_version()
    return f"engine {v}" if v else None


def _route_retraction_to_insights(repo_root: Path, config, stage: str, n: int,
                                  reason: str, date: str) -> Tuple[Optional[str], str]:
    """Append the ``gap`` entry a retraction *is*; ``(rel_path, message)``.

    §1 already says a `❌ Not met` outcome target is a finding and must be
    routed like one. A withdrawn acceptance box is the same event one level
    down, so the verb does the routing itself rather than asking the caller to
    remember: the honest path has to be the cheap one, or the quiet path wins.
    """
    ddir = docs_dir(repo_root, config)
    path = insights_path(ddir)
    if not path.is_file():
        return None, ("notice: no insights.md, so the retraction was not "
                      "routed — capture it wherever this project keeps findings")
    stamp = _engine_stamp()
    source = f"stage {stage} criterion {n}"
    marker = f"*({source}, {date}" + (f", {stamp}" if stamp else "") + ")*"
    entry = f"- [ ] gap — acceptance criterion retracted: {reason} {marker}"
    text = path.read_text(encoding=_ENCODING)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + entry + "\n", encoding="utf-8")
    rel = str(config["project"].get("docs_dir", "docs/aide")) + "/insights.md"
    return rel, f"insights.md: captured a gap entry for the retraction"


def _cmd_progress_amend(args: argparse.Namespace) -> int:
    """``aide progress amend STAGE --criterion N --evidence TEXT`` — append-only.

    The correction path for an attestation whose *evidence* was wrong, which
    before this verb had no CLI route at all: `accept` reports an already-ticked
    box as "unchanged", so the only remedy was the hand edit of `progress.md`
    every role is otherwise forbidden from making (issue #118).
    """
    if args.all_criteria:
        print("aide progress amend: --all is not offered — an attestation is "
              "corrected one at a time, or the correction says nothing about "
              "any of them", file=sys.stderr)
        return 2
    if args.criterion is None:
        print("usage: aide progress amend STAGE --criterion N --evidence TEXT",
              file=sys.stderr)
        return 2
    if not (args.evidence or "").strip():
        print("aide progress amend: --evidence is required — a correction "
              "with no stated basis is not one", file=sys.stderr)
        return 2
    return _apply_criterion_edit(
        args, lambda text, date: amend_criterion(
            text, str(args.number), args.criterion, args.evidence.strip(), date),
        f"stage {args.number} amend criterion {args.criterion}")


def _cmd_progress_retract(args: argparse.Namespace) -> int:
    """``aide progress retract STAGE --criterion N --reason TEXT``.

    Unticks, keeps the original attestation visible, and captures the finding.
    """
    if args.all_criteria:
        print("aide progress retract: --all is not offered — each attestation "
              "was made separately and is withdrawn separately", file=sys.stderr)
        return 2
    if args.criterion is None:
        print("usage: aide progress retract STAGE --criterion N --reason TEXT",
              file=sys.stderr)
        return 2
    if not (args.reason or "").strip():
        print("aide progress retract: --reason is required — the reason is "
              "what the record keeps", file=sys.stderr)
        return 2
    reason = args.reason.strip()
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    progress_path = docs_dir(repo_root, config) / "progress.md"
    if not progress_path.is_file():
        print(f"error: {progress_path} not found", file=sys.stderr)
        return 1
    import datetime as _dt
    date = args.date or _dt.date.today().isoformat()
    text = progress_path.read_text(encoding=_ENCODING)
    try:
        updated, message = retract_criterion(
            text, str(args.number), args.criterion, reason, date)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    progress_path.write_text(updated, encoding="utf-8")
    print(f"stage {args.number}: {message}")
    rel_insights, note = _route_retraction_to_insights(
        repo_root, config, str(args.number), args.criterion, reason, date)
    print(note)
    # The retraction warning `aide check` now emits is permanent by design, and
    # a consumer that pins the tolerated warning set discovers that at its
    # merge gate rather than here — a suite reddened by honest self-correction,
    # with nothing at retraction time having said so (issue #152). Say it here,
    # so the widening lands in the same change as the retraction.
    print(f"notice: `aide check` will warn about this retraction from now on — "
          f"the record is permanent, not a defect to clear. A test that pins "
          f"the tolerated warning set needs widening for stage {args.number} "
          f"criterion {args.criterion}; do it in this change, not at the merge "
          f"gate")
    if not args.no_commit and (repo_root / ".git").exists():
        rels = [str(config["project"].get("docs_dir", "docs/aide")) + "/progress.md"]
        if rel_insights:
            rels.append(rel_insights)
        _commit_docs_files(
            repo_root, config,
            f"progress(aide): stage {args.number} retract criterion {args.criterion}",
            rels)
    return 0


def _cmd_progress_reword(args: argparse.Namespace) -> int:
    """``aide progress reword STAGE --criterion N --text TEXT``.

    Both files or neither wherever the roadmap mirrors the stage. The roadmap
    mirrors the criteria, so a rewording that lands in one document is the
    drift the verb exists to remove; when the two cannot be lined up, nothing is
    written and the message says so. A stage with no roadmap acceptance block —
    or no roadmap.md at all — has no mirror to drift from, so progress.md alone
    is written and the message says that too (issue #216).
    """
    if args.all_criteria:
        print("aide progress reword: --all is not offered — criteria are "
              "reworded one at a time", file=sys.stderr)
        return 2
    if args.criterion is None:
        print("usage: aide progress reword STAGE --criterion N --text TEXT",
              file=sys.stderr)
        return 2
    if not (args.text or "").strip():
        print("aide progress reword: --text is required", file=sys.stderr)
        return 2
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    ddir = docs_dir(repo_root, config)
    progress_path = ddir / "progress.md"
    roadmap_path = ddir / "roadmap.md"
    if not progress_path.is_file():
        print(f"error: {progress_path} not found", file=sys.stderr)
        return 1
    text = progress_path.read_text(encoding=_ENCODING)
    try:
        updated, old = reword_criterion(
            text, str(args.number), args.criterion, args.text)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    # How many boxes the stage has, for lining the roadmap up against it.
    plines = text.splitlines()
    psec = stage_section(plines, str(args.number))
    box_count = len(acceptance_boxes(plines, psec[0], psec[1]))
    road_updated: Optional[str] = None
    if roadmap_path.is_file():
        road_updated, err = reword_roadmap_bullet(
            roadmap_path.read_text(encoding=_ENCODING), str(args.number),
            args.criterion, args.text, box_count)
        if err:
            print(f"error: {err}", file=sys.stderr)
            return 1
    progress_path.write_text(updated, encoding="utf-8")
    rels = [str(config["project"].get("docs_dir", "docs/aide")) + "/progress.md"]
    print(f"stage {args.number}: criterion {args.criterion} reworded")
    print(f"  was: {old}")
    print(f"  now: {args.text.strip()}")
    if road_updated is not None:
        roadmap_path.write_text(road_updated, encoding="utf-8")
        rels.append(str(config["project"].get("docs_dir", "docs/aide")) + "/roadmap.md")
        print("  roadmap.md: mirrored")
    else:
        print("  roadmap.md: no acceptance block for this stage — nothing to mirror")
    if not args.no_commit and (repo_root / ".git").exists():
        _commit_docs_files(
            repo_root, config,
            f"progress(aide): stage {args.number} reword criterion {args.criterion}",
            rels)
    return 0


def _apply_criterion_edit(args: argparse.Namespace, edit, message: str) -> int:
    """Read progress.md, apply *edit*, write and commit — the amend path."""
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    progress_path = docs_dir(repo_root, config) / "progress.md"
    if not progress_path.is_file():
        print(f"error: {progress_path} not found", file=sys.stderr)
        return 1
    import datetime as _dt
    date = args.date or _dt.date.today().isoformat()
    text = progress_path.read_text(encoding=_ENCODING)
    try:
        updated, msg = edit(text, date)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    progress_path.write_text(updated, encoding="utf-8")
    print(f"stage {args.number}: {msg}")
    if not args.no_commit and (repo_root / ".git").exists():
        _commit_progress_file(repo_root, config, f"progress(aide): {message}")
    return 0


def _commit_progress(repo_root: Path, config, number: int, status: str) -> None:
    _commit_progress_file(
        repo_root, config, f"progress(aide): item {number:03d} -> {status}")


def _commit_progress_file(repo_root: Path, config, message: str) -> None:
    rel = str(config["project"].get("docs_dir", "docs/aide")) + "/progress.md"
    _commit_docs_files(repo_root, config, message, [rel])


def _commit_docs_files(repo_root: Path, config, message: str,
                       rels: List[str], pull: bool = True) -> Optional[str]:
    """Commit exactly *rels* — repo-relative paths — with *message*.

    Returns ``None`` when every named path is in a new commit on this
    branch, otherwise a one-line reason — so a caller that announces a commit
    announces what happened, not what it intended. Two things are reasons:
    the commit did not happen (a refused tree, a failed ``git commit``, a
    path the commit left out), and the commit happened but replaying it onto
    the upstream stopped mid-rebase, since the branch no longer carries it
    until that rebase is finished. A rebase that was skipped or never started
    is **not** a reason: the commit is complete and local, and that case is a
    printed notice, never a return. "Exactly" is enforced by pathspec: ``git commit -- <rels>``
    commits the named paths and nothing else, so a builder's staged work
    sitting in the index stays staged and out of the bookkeeping commit; a
    bare ``git commit`` would have swept it in, which is why ``git add <rel>``
    alone was never enough.

    A commit that fails — no ``user.name`` on a fresh clone, a hook, a path
    ``.gitignore`` reaches — leaves *rels* unstaged again, so the tree degrades
    to "modified" or "untracked" rather than "staged": ``aide sync`` refuses
    either, but a caller can say which and why. A ``git`` that cannot be run
    at all is a reason, not a traceback; ``check`` in particular must keep
    passing in a repo whose ``git`` is off PATH, as it did before 1.26.0.

    *pull* rebases the new commit onto the upstream **afterwards**, which is
    right for an edit to a file other machines also edit (a tick, an archive)
    and wrong for a file that did not exist a moment ago —
    ``ensure_insights_inbox`` passes ``False`` so that ``check``, a gate,
    never fetches on the caller's behalf. The order is the whole point: every
    caller has already written its edit to the worktree, and ``git pull
    --rebase`` refuses over an unstaged change before it starts, so a pull
    *ahead* of the commit never ran in the ordinary path and two machines
    ticking the same inbox diverged until push time (issue #180). Committing
    first leaves a clean tree in the common case, the rebase is real, and a
    conflict then stops **inside** a rebase — a state with a marker, which
    `_stalled_pull` names and routes the same way `aide merge` does.

    A tree already stopped in an earlier operation is refused *before* the
    commit, and for every caller, *pull* or not — git lets a commit through
    once the conflicts are staged, and a bookkeeping commit in the middle of
    someone's rebase is the state this exists to prevent (issue #178); the
    guard reads the git directory and fetches nothing, so ``check`` stays a
    gate. Two shapes the pull itself deliberately does not touch. Under
    ``git.mode = "local"``, or with no ``origin``, there is nothing to rebase
    onto and the other sites skip it too. And a ``HEAD`` carrying a merge
    commit origin has not seen is never rebased by a bookkeeping verb: the
    rebase drops the merge and replays both parents, bringing back every
    conflict resolved inside it (issue #133) — and `aide merge` reaches here
    with exactly that commit on ``HEAD``, having integrated origin itself a
    moment earlier, so the skip is silent there by design.
    """
    joined = ", ".join(rels)
    try:
        what = _interrupted_op(repo_root)
        if what is not None:
            # Refused, and refused HERE rather than left to `git commit`: with
            # the conflicts staged git accepts a commit mid-rebase, and the
            # callers that reach this discard the reason, so a verb would
            # print its success line over a tick sitting in the middle of an
            # unfinished operation. Unconditional on `pull`: the one caller
            # that passes False (`ensure_insights_inbox`) is creating a file,
            # and a new file committed mid-rebase is the same misplaced commit.
            reason = (f"the repository is stopped in an earlier operation "
                      f"— {_stopped_state(repo_root, config, what)}")
            print(f"aide: could not commit {joined} — {reason}", file=sys.stderr)
            return reason
        for rel in rels:
            git(["add", "--", rel], repo_root, check=False)
        res = git(["commit", "-m", message, "--", *rels], repo_root, check=False)
        if res.returncode != 0:
            git(["reset", "-q", "--", *rels], repo_root, check=False)
            text = (res.stdout + res.stderr).strip()
            if "nothing to commit" in text or "no changes added" in text:
                return "nothing to commit"
            first = next((l.strip() for l in text.splitlines() if l.strip()),
                         "git commit failed")
            print(f"aide: could not commit {joined} — {first}", file=sys.stderr)
            return first
        # One path per line, never whitespace-split: a `docs_dir` with a space
        # in it must match its own entry. `core.quotepath=false` keeps a
        # non-ASCII path literal rather than octal-escaped and quoted.
        out = git(["-c", "core.quotepath=false", "show", "--name-only",
                   "--format=", "HEAD"], repo_root, check=False).stdout
        shown = [line.strip() for line in out.splitlines() if line.strip()]
        missing = [r for r in rels if r not in shown]
        if missing:
            # `add` was refused (an ignored path, say) and `commit -- <path>`
            # then committed the rest of the list: a commit happened, the file
            # is not in it, and "committed" would be a lie about the one path
            # that matters. Printed as well as returned, like every other
            # arm: the callers discard the return, and `insights archive`
            # reaches this with the archive file it just created.
            reason = f"{', '.join(missing)} is not in the commit (ignored by .gitignore?)"
            print(f"aide: {reason}", file=sys.stderr)
            return reason
        mode = str(config["git"].get("mode", "auto-merge"))
        if not pull or mode == "local" or not _has_origin(repo_root):
            return None
        if _has_unpushed_merge(repo_root):
            return None
        pulled = git(["pull", "--rebase"], repo_root, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        # Loud here, not only in the return: three callers (`progress set`,
        # `tick`, `archive`) discard the reason, and a verb that prints its
        # success line over an uncommitted edit is the failure this names.
        why = f"git could not be run ({exc.__class__.__name__}: {exc})"
        print(f"aide: could not commit {joined} — {why}", file=sys.stderr)
        return why
    stalled = _stalled_pull(repo_root, config, pulled)
    if stalled is not None:
        # The commit exists and is being replayed; the tree is now mid-rebase
        # and the next verb will meet it. Said in full, because the callers
        # discard the return and the one verb that ends the usual case
        # (`insights resolve`) is named inside `stalled`.
        print(f"aide: {joined} is committed here, but replaying that commit "
              f"onto origin stopped: {stalled}", file=sys.stderr)
        return stalled
    if pulled.returncode != 0:
        # Non-zero with the tree untouched: unstaged changes beside the tick
        # (git refuses to start over ANY of them), an origin that cannot be
        # reached, a branch with no upstream. The commit is complete and
        # local, so this is a notice rather than a reason — but a silent one
        # would have the docstring promising a convergence that did not
        # happen, which is the state issue #180 was filed on.
        why = next((l.strip() for l in (pulled.stderr + pulled.stdout).splitlines()
                    if l.strip()), "git gave no reason")
        print(f"aide: {joined} is committed here but NOT rebased onto origin — "
              f"{why}. The commit is in this repository only until a later "
              f"pull or push settles it.", file=sys.stderr)
    return None


def insights_path(ddir: Path) -> Path:
    """The live inbox. One name, one place — see ``queue_name``/``item_spec_paths``."""
    return ddir / "insights.md"


#: The engine's own templates — installed as ``.aide/templates/`` beside
#: ``.aide/scripts/``, and laid out the same way in the framework's source tree,
#: so one relative step serves both. Module-level so a test can point it at a
#: directory with no template in it.
_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


def ensure_insights_inbox(repo_root: Path, config: Dict[str, Dict[str, object]],
                          verb: str, commit: bool = True) -> Optional[Path]:
    """Create ``insights.md`` from the template when the document set has none.

    Returns the path when a file was created, ``None`` otherwise. Idempotent
    and deliberately narrow: an existing file is never touched (not even a
    malformed one — the immutability rule, conventions.md §1), and a repo with
    no ``docs_dir`` gets nothing, since a project may adopt the CLI without
    the loop and the directory itself is project-owned.

    This is the engine's side of the §1 guarantee that capture is a plain
    append to a file that exists. Before it, every agent spec told the role to
    copy the template by hand the first time an insight needed a home — six
    restatements of one step, and the one that made every spec name
    ``templates/`` (issue #85). The copy is byte-exact: ``read_bytes`` /
    ``write_bytes`` carries a BOM or CRLF the installer may have written
    through unchanged.

    The file is committed (named path, no pull) when *commit* is set and the
    repo is one: ``aide sync`` refuses a dirty tree, so a creation left
    untracked would stall the next preflight of the very loop it serves.
    Two cases decline the commit and say so in the notice rather than
    pretend: a detached ``HEAD``, where the commit would dangle and the file
    vanish on the next checkout; and a commit git refuses or cannot run (no
    identity on a fresh clone, ``git`` off PATH) — the file then stays
    untracked and the reason is printed, for the next write verb to carry.
    In a repository with no commits yet the inbox becomes the root commit;
    that is the scaffold-time ``check`` the quickstart mandates, and a root
    commit is a fine place for a file the loop owns.
    """
    ddir = docs_dir(repo_root, config)
    if not ddir.is_dir():
        return None
    path = insights_path(ddir)
    if path.exists():
        return None
    template = _TEMPLATES_DIR / "insights.md"
    rel = _rel_display(path, repo_root)
    if not template.is_file():
        print(f"aide {verb}: {rel} is missing and could not be created — "
              f"{_rel_display(template, repo_root)} is not there, so the install "
              f"is incomplete (`python install.py --into . --check` from a "
              f"framework checkout says how)", file=sys.stderr)
        return None
    path.write_bytes(template.read_bytes())
    fate = ""
    if not commit:
        fate = ", left uncommitted (--no-commit)"
    elif (repo_root / ".git").exists():
        why = _commit_created_file(repo_root, config, rel)
        fate = (" and committed it" if why is None
                else f" but NOT committed — {why}; commit it with the next work")
    print(f"notice: created {rel} from .aide/templates/insights.md{fate} — the "
          f"insight inbox, so a capture is a plain append (conventions.md §1)")
    return path


def _commit_created_file(repo_root: Path, config, rel: str) -> Optional[str]:
    """Commit the inbox `ensure_insights_inbox` just wrote — or say why not.

    ``None`` on success, else the reason, in the same shape
    ``_commit_docs_files`` returns. The detached-``HEAD`` check lives here and
    not in the shared committer because it is a policy for a *new* file: a
    commit would succeed, dangle, and take the file with it on the next
    checkout while every message reported success.
    """
    try:
        on_branch = git(["symbolic-ref", "-q", "HEAD"], repo_root,
                        check=False).returncode == 0
    except (OSError, subprocess.SubprocessError) as exc:
        return f"git could not be run ({exc.__class__.__name__}: {exc})"
    if not on_branch:
        return "HEAD is detached, so the commit would dangle"
    return _commit_docs_files(repo_root, config, "docs(aide): create the insight inbox",
                              [rel], pull=False)


def insight_archive_path(ddir: Path, quarter: str) -> Path:
    """``docs/aide/insights/archive-2026-Q3.md`` — one file per quarter.

    A directory sibling to the live file, not a suffix on it, so the live file
    keeps the exact name every role appends to and the archive can grow without
    that name ever changing.
    """
    return ddir / "insights" / f"archive-{quarter}.md"


_ARCHIVE_HEADER = (
    "# Insight Archive — {quarter}\n\n"
    "_Closed entries moved out of `insights.md` by `aide insights archive`._\n"
    "_Frozen: the claims are immutable and, unlike the live file, this one is_\n"
    "_not shape-checked — see `insight_warnings`._\n"
)


def cmd_insights(args: argparse.Namespace) -> int:
    """Read and maintain ``insights.md`` — the one living document with no verb.

    Every other document has the CLI doing its mechanical work; this one made
    each triage pass an agent reading and hand-parsing the whole file, which is
    the cost that kept triage getting deferred. ``list`` answers "what is
    outstanding" without loading the archive with it, ``tick`` performs the one
    in-place edit the immutability rule permits, ``archive`` keeps the live
    file the size of its working set, and ``resolve`` merges the file's one
    recurring conflict — two branches that each appended — without a hand ever
    retyping a claim.
    """
    import datetime as _dt
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    ddir = docs_dir(repo_root, config)
    path = insights_path(ddir)
    if args.action == "list":
        # An empty backlog is an answer, not an error: `list` on a repo whose
        # document set has no inbox yet creates the inbox — the same way
        # `check` does — and reports it empty. The other two verbs edit an
        # entry, and there is no entry to edit in a file that does not exist.
        if not ddir.is_dir():
            print(f"aide insights: no {_rel_display(ddir, repo_root)}/ — this "
                  f"repo has no AIDE document set, so there is no inbox to list",
                  file=sys.stderr)
            return 2
        ensure_insights_inbox(repo_root, config, verb="insights",
                              commit=not args.no_commit)
    if not path.is_file():
        print(f"aide insights {args.action}: no {_rel_display(path, repo_root)} "
              f"— nothing to {args.action}; `aide check` creates the inbox "
              f"(conventions.md §1)", file=sys.stderr)
        return 2
    text = path.read_text(encoding=_ENCODING)
    ddir_rel = ddir.relative_to(repo_root).as_posix()

    if args.action == "list":
        return _cmd_insights_list(parse_insights(text), args)
    if args.action == "tick":
        return _cmd_insights_tick(path, text, ddir_rel, repo_root, config, args,
                                  _dt.date.today().isoformat())
    if args.action == "resolve":
        return _cmd_insights_resolve(path, text, ddir_rel, repo_root, args,
                                     _dt.date.today().isoformat())
    return _cmd_insights_archive(path, text, ddir, ddir_rel, repo_root, config, args)


def _cmd_insights_list(entries: List[InsightEntry], args: argparse.Namespace) -> int:
    if args.type and args.type not in _INSIGHT_TYPES:
        print(f"aide insights: --type must be one of {', '.join(_INSIGHT_TYPES)}",
              file=sys.stderr)
        return 2
    shown = [e for e in entries
             if (not args.open_only or not e.ticked)
             and (not args.type or e.type == args.type)]
    for e in shown:
        if e.type is None:
            # Nothing parsed, so render the line as it stands rather than
            # dressing it in fields this listing only guessed at.
            print(f"  {e.ordinal:>3}. ?? {e.raw}")
            continue
        # The whole marker is reprinted verbatim: "where did this come from"
        # is half of what triage routes on, and a listing that drops it — or
        # re-derives it from the item number, which can only print back the
        # single-item form — sends the reader to the file it exists to replace.
        # The trailing note is reprinted for the same reason: it carries the
        # engine version a `framework` entry is triaged against, and triage
        # reads this listing rather than the file.
        prov = (f" *({e.source + ', ' if e.source else ''}{e.date}"
                f"{', ' + e.note if e.note else ''})*") if e.date else ""
        mark = "x" if e.ticked else " "
        print(f"  {e.ordinal:>3}. [{mark}] {e.type:<10} — {e.text}{prov}"
              f"{_INSIGHT_POINTER + e.pointer if e.pointer else ''}")
        if args.trail:
            for line in e.trail:
                print(f"        {line.strip()}")
    open_entries = [e for e in entries if not e.ticked]
    by_type = {t: sum(1 for e in open_entries if e.type == t) for t in _INSIGHT_TYPES}
    breakdown = ", ".join(f"{n} {t}" for t, n in by_type.items() if n)
    malformed = sum(1 for e in entries if e.type is None)
    print(f"aide insights: {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}, "
          f"{len(open_entries)} open"
          f"{' (' + breakdown + ')' if breakdown else ''}"
          f"{f'; {malformed} malformed — see `aide check`' if malformed else ''}")
    if len(shown) != len(entries):
        print(f"aide insights: {len(shown)} shown by the filters given")
    return 0


def _cmd_insights_tick(path: Path, text: str, ddir_rel: str, repo_root: Path,
                       config, args: argparse.Namespace, today: str) -> int:
    if args.number is None:
        print("usage: aide insights tick N --pointer TEXT", file=sys.stderr)
        return 2
    if not (args.pointer or "").strip():
        print("aide insights tick: --pointer says where the claim landed — a "
              "doc, an item, an issue. A tick without one records that triage "
              "happened and loses what it decided.", file=sys.stderr)
        return 2
    try:
        updated, message = tick_insight_text(text, args.number, args.pointer.strip(),
                                             args.date or today,
                                             trail_only=args.trail)
    except ValueError as exc:
        print(f"aide insights tick: {exc}", file=sys.stderr)
        return 1
    path.write_text(updated, encoding="utf-8")
    print(message)
    if not args.no_commit and (repo_root / ".git").exists():
        _commit_docs_files(repo_root, config, f"docs(aide): triage insight {args.number}",
                           [f"{ddir_rel}/insights.md"])
    return 0


def _cmd_insights_archive(path: Path, text: str, ddir: Path, ddir_rel: str,
                          repo_root: Path, config, args: argparse.Namespace) -> int:
    if not _DATE_RE.match(args.before or ""):
        print("usage: aide insights archive --before YYYY-MM-DD", file=sys.stderr)
        return 2
    remaining, moved, undatable = archive_insight_text(text, args.before)
    # Before the early return: an operator whose file will not shrink needs
    # this most in the run where nothing moved at all.
    for e in undatable:
        print(f"aide insights archive: entry {e.ordinal} "
              f"(insights.md:{e.lineno}) is closed but carries no readable "
              f"date, so no --before cut can move it: {e.raw!r}", file=sys.stderr)
    if undatable:
        print(f"aide insights archive: {len(undatable)} closed entr"
              f"{'y' if len(undatable) == 1 else 'ies'} could not be dated and "
              f"stay in the live file; `aide check` names the shape rule",
              file=sys.stderr)
    if not moved:
        print(f"aide insights: nothing closed before {args.before} to archive")
        return 0
    total = 0
    for quarter in sorted(moved):
        entries = sum(1 for ln in moved[quarter] if ln.startswith("- "))
        total += entries
        print(f"  {insight_archive_path(ddir, quarter).relative_to(repo_root).as_posix()}"
              f" ← {entries} closed entr{'y' if entries == 1 else 'ies'}")
    if not args.yes:
        print(f"aide insights archive: dry run — {total} entr"
              f"{'y' if total == 1 else 'ies'} would move; re-run with --yes")
        return 0

    rels = [f"{ddir_rel}/insights.md"]
    for quarter in sorted(moved):
        apath = insight_archive_path(ddir, quarter)
        apath.parent.mkdir(parents=True, exist_ok=True)
        body = "\n".join(moved[quarter]) + "\n"
        if apath.is_file():
            existing = apath.read_text(encoding=_ENCODING)
            apath.write_text(existing.rstrip("\n") + "\n" + body, encoding="utf-8")
        else:
            apath.write_text(_ARCHIVE_HEADER.format(quarter=quarter) + "\n" + body,
                             encoding="utf-8")
        rels.append(apath.relative_to(repo_root).as_posix())
    path.write_text(remaining, encoding="utf-8")
    print(f"aide insights archive: moved {total} entr{'y' if total == 1 else 'ies'}; "
          f"{len(parse_insights(remaining))} remain — their list numbers have shifted")
    if not args.no_commit and (repo_root / ".git").exists():
        _commit_docs_files(repo_root, config,
                           f"docs(aide): archive insights closed before {args.before}",
                           rels)
    return 0


def _is_unmerged(repo_root: Path, rel: str) -> bool:
    """Does git hold *rel* unmerged in the index — i.e. is it still conflicted?

    Kept apart from `_merge_base_text` because the two questions have different
    answers on an **add/add** conflict, where both branches created the file:
    the index then holds stages 2 and 3 and **no stage 1**, so the merge base
    is genuinely absent while the path is very much unmerged. That shape is
    routine here — `check`, `claim` and `queue start` each create the inbox
    from the template when it is missing — and conflating the two made the
    verb decline to stage exactly the conflict a consumer hits first.
    """
    if not (repo_root / ".git").exists():
        return False
    try:
        out = git(["ls-files", "-u", "--", rel], repo_root, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return out.returncode == 0 and bool(out.stdout.strip())


def _merge_base_text(repo_root: Path, rel: str) -> Optional[str]:
    """Stage 1 of *rel* — the merge base of a stalled merge or rebase, or None.

    What turns the resolver's append check from an inference into a fact.
    ``None`` covers every way it can be absent: no repository, no conflict, an
    add/add conflict that has no base at all, or git off PATH. The resolver
    falls back to comparing the two sides alone.
    """
    if not _is_unmerged(repo_root, rel):
        return None
    try:
        out = git(["show", f":1:{rel}"], repo_root, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def _cmd_insights_resolve(path: Path, text: str, ddir_rel: str, repo_root: Path,
                          args: argparse.Namespace, today: str) -> int:
    """Resolve a conflicted inbox as the union of both sides' entries.

    The verb exists because the alternative is an agent retyping the block, and
    that is exactly where conventions.md §1's "never reword a captured claim"
    gets broken — the merge conflict is the one moment the whole file is in
    front of something willing to rewrite it.
    """
    rel = f"{ddir_rel}/insights.md"
    if not any(rx.match(line) for line in text.splitlines()
               for rx in _CONFLICT_LINT_RES):
        if not _is_unmerged(repo_root, rel):
            print(f"aide insights resolve: no conflict markers in {rel} — "
                  f"nothing to resolve")
            return 0
        # Markers gone but the path still unmerged: someone resolved the file
        # by hand and stopped short of staging it. Finishing that is the same
        # end state this verb reaches on its own, and leaving it undone is how
        # an unattended run stalls on `git commit` with nothing in the message
        # naming the cause.
        add = git(["add", "--", rel], repo_root, check=False)
        if add.returncode != 0:
            print(f"aide insights resolve: {rel} has no conflict markers but "
                  f"git still holds it unmerged, and staging it failed "
                  f"({add.stderr.strip()}) — `git add {rel}` before continuing",
                  file=sys.stderr)
            return 1
        print(f"aide insights resolve: no conflict markers in {rel}, but git "
              f"still held it unmerged — staged it as it stands, so the merge "
              f"or rebase can continue. Nothing was rewritten; if a claim was "
              f"reworded resolving it by hand, §1 says that is the thing to "
              f"look at.")
        return 0
    base = _merge_base_text(repo_root, rel)
    merged, notes, refusals = resolve_insights_text(text, args.date or today, base)
    if refusals:
        for why in refusals:
            print(f"aide insights resolve: {why}", file=sys.stderr)
        print(f"aide insights resolve: {rel} left exactly as it is — the "
              f"markers are still in place and the claims are still both "
              f"there", file=sys.stderr)
        return 1
    for note in notes:
        print(f"  {note}")
    if args.dry_run:
        # The union itself, not just the counts: reviewing the merge before it
        # is written is the whole of what --dry-run is for, and every place
        # that documents the flag says it prints what would be written.
        print(f"--- {rel} would become ---")
        print(merged, end="" if merged.endswith("\n") else "\n")
        print(f"aide insights resolve: dry run — {rel} not written")
        return 0
    path.write_text(merged, encoding="utf-8")
    staged = ""
    # Asked again rather than inferred from `base`: an add/add conflict has no
    # merge base and is still unmerged, and writing the file does not touch the
    # index, so this is the same answer it would have given a moment ago.
    if _is_unmerged(repo_root, rel):
        add = git(["add", "--", rel], repo_root, check=False)
        staged = (" and staged it, so the conflict is marked resolved; finish "
                  "the merge or rebase as usual"
                  if add.returncode == 0 else
                  f" but could NOT stage it ({add.stderr.strip()}) — `git add "
                  f"{rel}` before continuing")
    print(f"aide insights resolve: wrote {rel} as the union of both sides"
          f"{staged}")
    return 0


# --------------------------------------------------------------------------- #
# ledger — one row per item worked (§1 → ledger.md)
# --------------------------------------------------------------------------- #
#: The row, in the order `.aide/templates/ledger.md` draws it. The template is
#: the shape's executable statement (§1) and this tuple is what writes it, so
#: the two move together: a column added here is a column added there, and
#: `test_aide_ledger.py` holds the pair.
LEDGER_COLUMNS = ("Item", "Queue", "Stage", "Kind", "Outcome", "ACs", "Tests",
                  "Files", "Rounds", "Blocking", "Minor", "Nit", "Engine",
                  "Date")
#: Cells whose value is an integer or nothing at all — what `ledger_warnings`
#: reads, and the blank-cell rule's whole surface.
LEDGER_INTEGER_COLUMNS = ("ACs", "Tests", "Files", "Rounds", "Blocking",
                          "Minor", "Nit")
#: The three ranks `--findings` accepts, in the order they are written.
LEDGER_FINDING_RANKS = ("blocking", "minor", "nit")
#: What the three finding cells hold where the project runs with no reviewer
#: at all (§1 → `ledger.md`): not a count, and not the absence of one either.
#: It is the engine's own answer, read from `[loop] review`, so a blank in
#: those three columns means exactly one thing — a count that should have been
#: passed and was not.
LEDGER_NO_REVIEW_CELL = "-"
#: How an item left the loop: `merge` writes one, `ledger abandon` the other.
LEDGER_OUTCOMES = ("merged", "abandoned")
#: An item cell: the zero-padded number the verbs write, and anything a reader
#: can resolve to an item.
_LEDGER_ITEM_RE = re.compile(r"^0*\d+$")
#: A `Validate stage N` item — test-heavy by design, so it is its own `kind`
#: (§1 → ledger.md). Read off the item's title, which is the only place the
#: engine ever learns what an item is: the spec's `# Item NNN — <title>` line,
#: or the queue's `### Item NNN: <title>` where no spec is left.
_VALIDATE_STAGE_TITLE_RE = re.compile(r"^\s*validate\s+stage\b", re.IGNORECASE)
#: The three insight types that become a maintenance item (§1 → the
#: maintenance queue); a `knowledge` or `framework` entry never does.
_LEDGER_MAINTENANCE_TYPES = ("defect", "gap", "automation")


def ledger_path(ddir: Path) -> Path:
    """The run ledger. One name, one place — see ``insights_path``."""
    return ddir / "ledger.md"


def review_is_off(config: Dict[str, Dict[str, object]]) -> bool:
    """Whether `[loop] review` leaves this project with no reviewer at all.

    The one reader of that key in the engine (§9 is prose the orchestrator
    consumes), and the one thing the ledger needs from it: anything other than
    the default `"off"` means some adversarial read runs, so a blank finding
    cell is a count that was not passed rather than a review that never
    happened.
    """
    return str(config.get("loop", {}).get("review", "off")).strip().lower() == "off"


def parse_findings(value: str) -> Dict[str, int]:
    """``"blocking=1,minor=2"`` -> ``{"blocking": 1, "minor": 2}``.

    Strict, and strict on purpose: the counts are a claim the caller makes
    about work the engine cannot see (§1 → `ledger.md`), so the one thing this
    must never do is guess. Every rank is optional and the order is free; an
    unknown rank, a repeated one, a missing `=` and a value that is not a
    non-negative integer are each a usage error naming what was wrong, because
    a mistyped rank silently dropped would record a blank where a count was
    passed. Raises ``ValueError``; the parser turns it into argparse's usage
    error.
    """
    counts: Dict[str, int] = {}
    ranks = ", ".join(LEDGER_FINDING_RANKS)
    for part in value.split(","):
        part = part.strip()
        if not part:
            raise ValueError(
                f"empty entry in '{value}' — write <rank>=<count> pairs "
                f"separated by commas, with the ranks you have ({ranks})")
        rank, sep, count = part.partition("=")
        rank = rank.strip().lower()
        if not sep:
            raise ValueError(f"'{part}' is not <rank>=<count>")
        if rank not in LEDGER_FINDING_RANKS:
            raise ValueError(f"unknown rank '{rank}' — one of {ranks}")
        if rank in counts:
            raise ValueError(f"rank '{rank}' given twice")
        count = count.strip()
        if not re.fullmatch(r"[0-9]+", count):
            raise ValueError(
                f"'{rank}={count}' is not a non-negative integer")
        counts[rank] = int(count)
    return counts


def _findings_argument(value: str) -> Dict[str, int]:
    try:
        return parse_findings(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def _non_negative_argument(value: str) -> int:
    if not re.fullmatch(r"[0-9]+", value.strip()):
        raise argparse.ArgumentTypeError(
            f"'{value}' is not a non-negative integer")
    return int(value.strip())


def _item_queue_number(repo_root: Path, config, number: int) -> Optional[int]:
    """The queue whose file lists item *number*, or ``None``."""
    qdir = docs_dir(repo_root, config) / "queue"
    if not qdir.is_dir():
        return None
    for qpath in iter_queue_paths(qdir):
        try:
            text = qpath.read_text(encoding=_ENCODING)
        except (OSError, UnicodeDecodeError):
            continue
        if number in queue_item_numbers(text):
            return queue_number(qpath)
    return None


def _queue_item_title(repo_root: Path, config, number: int) -> Optional[str]:
    """The item's title as its queue file writes it, or ``None``."""
    qdir = docs_dir(repo_root, config) / "queue"
    if not qdir.is_dir():
        return None
    for qpath in iter_queue_paths(qdir):
        try:
            title = _queue_titles(qpath.read_text(encoding=_ENCODING)).get(number)
        except (OSError, UnicodeDecodeError):
            continue
        if title:
            return title
    return None


def _insight_derived_item(repo_root: Path, config, number: int) -> bool:
    """Did an insight become item *number*?

    §1 → the maintenance queue: the author who queues an open `defect`, `gap`
    or `automation` entry ticks it with the item number it became
    (`insights tick N --pointer "item NNN"`), so the inbox is where the engine
    can read that an item is insight-derived. The pointer and the entry's trail
    are read; its **provenance** deliberately is not — that names the item the
    insight was captured *in*, which is the opposite claim.
    """
    path = insights_path(docs_dir(repo_root, config))
    if not path.is_file():
        return False
    try:
        entries = parse_insights(path.read_text(encoding=_ENCODING))
    except (OSError, UnicodeDecodeError):
        return False
    for entry in entries:
        if entry.type not in _LEDGER_MAINTENANCE_TYPES:
            continue
        for text in ([entry.pointer] if entry.pointer else []) + list(entry.trail):
            if _references_item(text, number):
                return True
    return False


def item_kind(repo_root: Path, config, number: int,
              title: Optional[str] = None) -> str:
    """The item's `kind` cell: one of `validate-stage`, `maintenance`, `normal`.

    `validate-stage` wins over `maintenance`, because it is the reading that
    changes how every other cell on the row is read: such an item exists to
    add tests, so its tests-per-criterion is not comparable with anything
    else's whatever else the item also is.
    """
    if title is None:
        title = (_spec_stage_and_title(repo_root, config, number)[1]
                 or _queue_item_title(repo_root, config, number))
    if title and _VALIDATE_STAGE_TITLE_RE.match(title):
        return "validate-stage"
    if _insight_derived_item(repo_root, config, number):
        return "maintenance"
    return "normal"


def _ledger_diff_cells(repo_root: Path, config, number: int,
                       branch: Optional[str],
                       base: Optional[str]) -> Tuple[str, str]:
    """``(tests added, files changed)`` for item *number*'s *branch* against
    *base*.

    Both blank when the diff cannot be taken — no branch left, no base
    recorded, a ref git cannot resolve. The counting is `aide scope`'s
    (`added_test_functions`), read from the branch tip rather than the working
    tree so the answer does not depend on what happens to be checked out; and
    so is the split — a test `aide scope` reports as reconciled in another
    item's test file (`split_reconciled_tests`) is that item's, not a test
    this one added.
    """
    if not branch or not base:
        return "", ""
    mb = git(["merge-base", base, branch], repo_root, check=False)
    if mb.returncode != 0:
        return "", ""
    merge_base = mb.stdout.strip()
    diff = git(["-c", "core.quotePath=false", "diff", "--name-only",
                merge_base, branch], repo_root, check=False)
    if diff.returncode != 0:
        return "", ""
    changed = [line.strip() for line in diff.stdout.splitlines() if line.strip()]
    added = added_test_functions(repo_root, config, changed, merge_base,
                                 renamed_paths(repo_root, merge_base), ref=branch)
    own, others = split_reconciled_tests(repo_root, config, added, number)
    tests = len(own) + sum(len(o.untraced) for o in others.values())
    return str(tests), str(len(changed))


def ledger_cells(repo_root: Path, config, number: int, outcome: str,
                 rounds: Optional[int] = None,
                 findings: Optional[Dict[str, int]] = None,
                 branch: Optional[str] = None,
                 base: Optional[str] = None,
                 date: Optional[str] = None,
                 no_review: bool = False) -> List[str]:
    """One row's cells, in `LEDGER_COLUMNS` order.

    Everything but *rounds* and *findings* is derived here, from the documents,
    the branch and `.aide/VERSION`; those two are the caller's, and an absent
    one is a blank cell rather than a zero (§1 → `ledger.md`). Every derivation
    degrades to a blank: a spec that is gone, a queue that never listed the
    item, a stage the spec header does not name and a diff with no branch to
    take it from each cost one cell, never the row.
    """
    import datetime as _dt
    findings = findings or {}
    stage, title = _spec_stage_and_title(repo_root, config, number)
    specs = item_spec_paths(docs_dir(repo_root, config) / "items", number)
    criteria = ""
    if specs:
        try:
            spec_text = specs[0].read_text(encoding=_ENCODING)
        except (OSError, UnicodeDecodeError):
            spec_text = ""
        if _AC_HEADING_RE.search(spec_text):
            criteria = str(len(spec_acceptance_numbers(spec_text)))
    queue = _item_queue_number(repo_root, config, number)
    tests, files = _ledger_diff_cells(repo_root, config, number, branch, base)
    cells = {
        "Item": f"{number:03d}",
        "Queue": f"{queue:03d}" if queue is not None else "",
        "Stage": stage or "",
        "Kind": item_kind(repo_root, config, number, title),
        "Outcome": outcome,
        "ACs": criteria,
        "Tests": tests,
        "Files": files,
        "Engine": installed_engine_version() or "",
        "Date": date or _dt.date.today().isoformat(),
    }
    cells.update(zip(LEDGER_COUNT_COLUMNS,
                     _ledger_count_cells(rounds=rounds, findings=findings,
                                         no_review=no_review)))
    return [cells[column] for column in LEDGER_COLUMNS]


#: The caller-supplied cells, in the order `_ledger_count_cells` renders them.
LEDGER_COUNT_COLUMNS = ("Rounds",) + tuple(r.capitalize() for r in LEDGER_FINDING_RANKS)
#: Those of them that count findings — the three that may carry the no-review
#: marker, named once so `ledger_warnings` and the renderer cannot disagree.
LEDGER_FINDING_COLUMNS = tuple(r.capitalize() for r in LEDGER_FINDING_RANKS)


def _ledger_count_cells(rounds: Optional[int],
                        findings: Optional[Dict[str, int]],
                        no_review: bool = False) -> List[str]:
    """Render the caller's counts — a count nobody passed is `""`, never `0`.

    *no_review* is the project's `[loop] review` read as "off": with no
    reviewer in the loop there are no findings to count, so the three rank
    cells carry `LEDGER_NO_REVIEW_CELL` instead of the blank that would read
    as a count somebody forgot. Counts passed anyway win over it, whole — a
    count is a claim its caller made, and the engine records claims rather
    than correcting them from the configuration.
    """
    findings = findings or {}
    absent = LEDGER_NO_REVIEW_CELL if (no_review and not findings) else ""
    out = ["" if rounds is None else str(rounds)]
    for rank in LEDGER_FINDING_RANKS:
        got = findings.get(rank)
        out.append(absent if got is None else str(got))
    return out


def ledger_row(cells: List[str]) -> str:
    """The cells as the one line appended to the ledger."""
    return "| " + " | ".join(cells) + " |"


def append_ledger_row(repo_root: Path, config, cells: List[str],
                      verb: str) -> Optional[str]:
    """Append one row, creating the ledger from the template if it is missing.

    Returns the repo-relative path of the file written, so the caller can put
    it in the commit that records the item — or ``None`` when there is nowhere
    to write: a repo with no ``docs_dir`` (a project may adopt the CLI without
    the loop) or an install whose template is gone. Both say why. Raises
    nothing else on purpose: every caller is a verb whose real work has
    already succeeded.
    """
    ddir = docs_dir(repo_root, config)
    if not ddir.is_dir():
        print(f"aide {verb}: no {_rel_display(ddir, repo_root)} directory, so "
              f"no ledger row was recorded", file=sys.stderr)
        return None
    path = ledger_path(ddir)
    rel = _rel_display(path, repo_root)
    if not path.exists():
        template = _TEMPLATES_DIR / "ledger.md"
        if not template.is_file():
            print(f"aide {verb}: {rel} is missing and could not be created — "
                  f"{_rel_display(template, repo_root)} is not there, so the "
                  f"install is incomplete (`python install.py --into . --check` "
                  f"from a framework checkout says how)", file=sys.stderr)
            return None
        path.write_bytes(template.read_bytes())
        print(f"notice: created {rel} from .aide/templates/ledger.md — the run "
              f"ledger, one row per item worked (conventions.md §1)")
    text = path.read_text(encoding=_ENCODING)
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text + ledger_row(cells) + "\n", encoding="utf-8")
    return rel


def ledger_rows(text: str) -> List[Tuple[int, List[str]]]:
    """``(lineno, cells)`` for every data row of a ledger — the one reader.

    Table furniture is skipped, and so is **everything inside an HTML
    comment**: the document is created as a byte-exact copy of the template,
    whose header comment draws the row it is about to write, so a reader that
    took any `|` line for data would read that example as an item. The
    comment is the author's to delete and most never do, which makes this the
    ordinary case rather than the odd one.
    """
    out: List[Tuple[int, List[str]]] = []
    in_comment = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        rest = line
        while rest:
            if in_comment:
                _, sep, rest = rest.partition("-->")
                if not sep:
                    rest = ""
                in_comment = bool(not sep)
            else:
                before, sep, rest = rest.partition("<!--")
                if not sep:
                    rest = ""
                else:
                    in_comment = True
                if before.strip().startswith("|"):
                    cells = _split_row(before)
                    if not _is_table_furniture(cells, LEDGER_COLUMNS[0].lower()):
                        out.append((lineno, cells))
                if not sep:
                    break
    return out


def ledger_warnings(ddir: Path) -> List[str]:
    """Rows of `ledger.md` no reader can use — warnings, never errors.

    Capture has to stay cheap: the file records work that is already finished,
    so a mis-shaped row is worth reporting and never worth failing a run over
    — and a row nobody can fix without rewriting a record is exactly the kind
    of finding that teaches a reader to skim (§1 → `ledger.md`, and rung 4 of
    the copies rule: `docs/aide/**` is the project's). An absent file is
    silent: a project that has not merged an item through the engine has no
    ledger, and that is not a defect.
    """
    path = ledger_path(ddir)
    if not path.is_file():
        return []
    out: List[str] = []
    for lineno, cells in ledger_rows(path.read_text(encoding=_ENCODING)):
        if len(cells) != len(LEDGER_COLUMNS):
            out.append(f"ledger.md:{lineno}: {len(cells)} cell(s), not "
                       f"{len(LEDGER_COLUMNS)} — the columns "
                       f"`.aide/templates/ledger.md` draws")
            continue
        row = dict(zip(LEDGER_COLUMNS, cells))
        if not _LEDGER_ITEM_RE.match(row["Item"]):
            out.append(f"ledger.md:{lineno}: Item cell '{row['Item']}' is not "
                       f"an item number")
        if row["Outcome"] not in LEDGER_OUTCOMES:
            out.append(f"ledger.md:{lineno}: Outcome cell "
                       f"'{row['Outcome']}' is not one of "
                       f"{', '.join(LEDGER_OUTCOMES)}")
        for column in LEDGER_INTEGER_COLUMNS:
            value = row[column]
            # The three finding columns may also carry the no-review marker,
            # which the writing verbs put there themselves (§1 → ledger.md).
            if (value == LEDGER_NO_REVIEW_CELL
                    and column in LEDGER_FINDING_COLUMNS):
                continue
            if value and not re.fullmatch(r"[0-9]+", value):
                out.append(f"ledger.md:{lineno}: {column} cell '{value}' is "
                           f"neither an integer nor blank")
    return out


def cmd_ledger(args: argparse.Namespace) -> int:
    """Write a ledger row for an item no merge will ever write one for."""
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    if args.rounds is None:
        print(f"aide ledger {args.action}: --rounds is required — the round "
              f"count is why this row exists, and an abandoned item with no "
              f"count recorded is indistinguishable from one nobody wrote "
              f"down.", file=sys.stderr)
        return 2
    no_review = review_is_off(config)
    ddir = docs_dir(repo_root, config)
    path = ledger_path(ddir)
    if path.is_file():
        counts = _ledger_count_cells(rounds=args.rounds,
                                     findings=args.findings,
                                     no_review=no_review)
        for lineno, cells in ledger_rows(path.read_text(encoding=_ENCODING)):
            row = dict(zip(LEDGER_COLUMNS, cells))
            if (row.get("Item") == f"{args.number:03d}"
                    and row.get("Outcome") == "abandoned"
                    and [row.get(c) for c in LEDGER_COUNT_COLUMNS] == counts):
                # A retried orchestrator step is the ordinary way to arrive
                # here twice; a second row would count one abandonment as
                # two in every ratio read from the file. Different counts are
                # a different abandonment — an item resumed after the cap and
                # stopped again — and that row is appended like any other.
                print(f"aide ledger {args.action}: item {args.number:03d} is "
                      f"already recorded as abandoned with these counts "
                      f"({path.name}:{lineno}); nothing appended")
                return 0
    prefix = str(config["git"].get("branch_prefix", "aide/"))
    branch = _find_claim_branch(repo_root, prefix, args.number)
    base = _recorded_branch_base(repo_root, branch) if branch else None
    cells = ledger_cells(repo_root, config, args.number, "abandoned",
                         rounds=args.rounds, findings=args.findings,
                         branch=branch, base=base, no_review=no_review)
    rel = append_ledger_row(repo_root, config, cells, f"ledger {args.action}")
    if rel is None:
        return 1
    print(f"aide ledger {args.action}: item {args.number:03d} recorded in {rel} "
          f"as abandoned after {args.rounds} round(s)")
    if not args.no_commit and (repo_root / ".git").exists():
        # No pull: this is an append to a file the loop owns, on whatever
        # branch the cap was hit on, and a verb that only records must not
        # fetch on the caller's behalf (`ensure_insights_inbox` reasons the
        # same way).
        _commit_docs_files(repo_root, config,
                           f"docs(aide): ledger row for item {args.number:03d} "
                           f"(abandoned)", [rel], pull=False)
    print(f"aide ledger {args.action}: progress.md is untouched — this verb "
          f"records what the run cost and decides nothing about the item's "
          f"status")
    return 0


def cmd_queue(args: argparse.Namespace) -> int:
    if args.action == "start":
        return _queue_start(args)
    if args.action != "tidy":
        print("usage: aide queue {start|tidy} NNN", file=sys.stderr)
        return 2
    import datetime as _dt
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    qdir = docs_dir(repo_root, config) / "queue"
    target = queue_path(qdir, args.number)
    if target is None:
        print(f"error: no {queue_name(args.number)} file under {qdir}", file=sys.stderr)
        return 1
    # Supersede by the highest-numbered queue after this one.
    later = [n for n in (queue_number(p) for p in iter_queue_paths(qdir))
             if n > args.number]
    superseded_by = max(later) if later else args.number + 1
    date = args.date or _dt.date.today().isoformat()
    text = target.read_text(encoding=_ENCODING)
    target.write_text(tidy_queue_text(text, superseded_by, date), encoding="utf-8")
    print(f"{queue_name(args.number)}: marked completed "
          f"(superseded by {queue_name(superseded_by)})")
    return 0


def _queue_start(args: argparse.Namespace) -> int:
    """Create (and, off ``local`` mode, push) a queue or specs-queue branch.

    The branch half of what `claim` does for an item. It exists because
    conventions.md §3 says a raw git form is wrong wherever a verb covers it,
    and until 1.20.0 two of the three branch shapes the engine recognises were
    covered by no verb at all: the framework's own prose told an agent to type
    `git switch -c <prefix>queue-NNN`, and the regex that must later parse that
    name never saw it until something had already gone wrong. A typo did not
    fail loudly — it made `claim` infer `main_branch` as the base and merge the
    item past the queue branch, silently.

    Recording the base is the second half. `_record_branch_base` ran only at
    claim, so a queue branch had no recorded base of its own; a queue branched
    off something other than `main_branch` had to be given `--base` at every
    later call that cared.
    """
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    prefix = str(config["git"].get("branch_prefix", "aide/"))
    mode = str(config["git"].get("mode", "auto-merge"))
    branch = (specs_queue_branch_name(prefix, args.number) if args.specs
              else queue_branch_name(prefix, args.number))

    base = args.base or str(config["git"].get("main_branch", "main"))
    if not _local_branch_exists(repo_root, base):
        print(f"aide queue start: base '{base}' is not a local branch — a queue "
              f"branch is branched from its base and merged back into it, so "
              f"the base must be a branch this checkout can update",
              file=sys.stderr)
        return 1
    if _local_branch_exists(repo_root, branch):
        print(f"aide queue start: {branch} already exists — switch to it rather "
              f"than recreating it", file=sys.stderr)
        return 1
    # Also on origin: another machine (or another session) already started this
    # queue. Creating it locally would succeed and the `push -u` would then fail
    # — an uncaught CalledProcessError, i.e. a raw traceback in what is meant to
    # be an unattended flow. Fail as a sentence instead.
    if mode != "local" and _has_origin(repo_root) and branch in _remote_branches(repo_root):
        print(f"aide queue start: {branch} already exists on origin — someone "
              f"has started this queue; fetch and switch to it rather than "
              f"recreating it", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"would start {branch}; base {base}")
        return 0
    # Branch FROM the base explicitly, for the reason `claim` does: with no
    # start point `switch -c` uses HEAD, which lets the branch's actual origin
    # disagree with the base it records.
    git(["switch", "-c", branch, base], repo_root)
    _record_branch_base(repo_root, branch, base)
    # `/aide-run-roadmap` (queue-planner) and `/aide-spec-queue` (spec-author,
    # spec-reviewer) start here and reach a role before any `check` runs, so
    # the inbox is guaranteed at the same point `claim` guarantees it.
    ensure_insights_inbox(repo_root, config, verb="queue start")
    if mode != "local":
        failure = _push_new_branch(repo_root, branch)
        if failure is not None:
            print(f"aide queue start: {failure}\n"
                  f"{branch} exists locally, branched from {base}, and is "
                  f"checked out — nothing is lost. Publish it with "
                  f"'git push -u origin {branch}' once the remote is "
                  f"reachable, or start over with 'git switch {base} && "
                  f"git branch -D {branch}'.", file=sys.stderr)
            return 1
    note = "" if base == str(config["git"].get("main_branch", "main")) else f" (base {base})"
    print(f"started {branch}{note}")
    return 0


# --------------------------------------------------------------------------- #
# git layer — claim / merge / env
# --------------------------------------------------------------------------- #
def venv_python(repo_root: Path, config: Dict[str, Dict[str, object]]) -> Path:
    """Resolve the venv interpreter path (Windows Scripts vs. posix bin)."""
    venv = repo_root / str(config["python"].get("venv", ".venv"))
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def resolve_test_command(repo_root: Path, config: Dict[str, Dict[str, object]]) -> List[str]:
    """The configured test command, with a leading ``python`` bound to the venv."""
    raw = str(config["python"].get("test_command", "python -m pytest")).split()
    vpy = venv_python(repo_root, config)
    if raw and raw[0] == "python" and vpy.exists():
        return [str(vpy), *raw[1:]]
    return raw


#: Written beside the venv's own files by `env --bootstrap`, read by
#: `env_report`: the exit status of the install that populated the venv. A
#: `pip install -e .[dev]` that aborts partway leaves the editable project
#: importable and the dependency closure unfinished, so an import check alone
#: reads a half-install as healthy (issue #166). The record is the one thing
#: that distinguishes them.
_BOOTSTRAP_RECORD = "aide-bootstrap.json"


def _venv_dir(repo_root: Path, config: Dict[str, Dict[str, object]]) -> Path:
    return repo_root / str(config["python"].get("venv", ".venv"))


def _configured_interpreter(config: Dict[str, Dict[str, object]]) -> List[str]:
    """The command `--bootstrap` builds the venv with, else the Python running
    this CLI.

    `[python] interpreter` is either a path or a command line. A value that
    names an existing file is the whole command, spaces and all — Windows's
    own default install lives under `Program Files`, and splitting that is
    what turned a valid key into "cannot be run". Anything else is a command
    line (`py -3.12`, `"C:\\Some Dir\\python.exe" -X utf8`), split the way
    the platform's shell would: shlex on POSIX; on Windows in non-POSIX mode,
    which keeps backslashes and leaves the quotes on a quoted token for this
    to strip.
    """
    raw = str(config["python"].get("interpreter", "") or "").strip()
    if not raw:
        return [sys.executable]
    if Path(raw).is_file():
        return [raw]
    if os.name == "nt":
        return [token.strip('"') for token in shlex.split(raw, posix=False)]
    return shlex.split(raw)


def _test_runner_module(config: Dict[str, Dict[str, object]]) -> Optional[str]:
    """The module `test_command` runs with ``python -m``, if that is its shape.

    Only that shape is answerable from inside the venv: `resolve_test_command`
    binds a leading `python` to the venv, so `python -m pytest` runs *the
    venv's* pytest and its absence is the venv's fault. A bare `pytest` or a
    `make test` resolves on PATH, and whether PATH has it is not a property
    of the venv this reports on.
    """
    raw = str(config["python"].get("test_command", "python -m pytest")).split()
    if len(raw) >= 3 and raw[0] == "python" and raw[1] == "-m":
        return raw[2]
    return None


def _python_version(command: List[str], cwd: Path) -> Optional[str]:
    """``major.minor`` of the interpreter *command* starts, or None when it
    cannot be run at all."""
    try:
        res = subprocess.run(
            [*command, "-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
            cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace")
    except OSError:
        return None
    if res.returncode != 0:
        return None
    return res.stdout.strip() or None


def _read_bootstrap_record(venv: Path) -> Optional[Dict[str, object]]:
    path = venv / _BOOTSTRAP_RECORD
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def env_report(repo_root: Path, config: Dict[str, Dict[str, object]]) -> Tuple[str, str]:
    """``(status, detail)`` for the project venv: 'ok', 'missing' or 'stale'.

    'ok' is a claim the loop acts on — the validator reads it and runs the
    suite — so it is only made when every question this can ask of the venv
    is answered: the venv exists; the last `--bootstrap` that built it
    finished; it is the Python `[python] interpreter` names, where that is
    set and runnable; `import_check` imports; and the module `test_command`
    runs with `-m` imports too. A venv with no `pytest` cannot report OK
    (issue #166). The detail is one sentence for the report line.
    """
    vpy = venv_python(repo_root, config)
    venv = _venv_dir(repo_root, config)
    if not vpy.exists():
        return "missing", f"no venv at {venv}"
    record = _read_bootstrap_record(venv)
    if record is not None and record.get("exit") not in (0, None):
        return "stale", (f"the last `env --bootstrap` exited "
                         f"{record.get('exit')}, so its install did not finish")
    facts: List[str] = []
    actual = _python_version([str(vpy)], repo_root)
    if actual is None:
        return "stale", f"{vpy} cannot be run"
    facts.append(f"venv is Python {actual}")
    configured = str(config["python"].get("interpreter", "") or "").strip()
    if configured:
        wanted = _python_version(_configured_interpreter(config), repo_root)
        if wanted is None:
            facts.append(f"[python] interpreter '{configured}' cannot be run "
                         f"on this machine, so the venv was judged on its own")
        elif wanted != actual:
            return "stale", (f"venv is Python {actual} but [python] interpreter "
                             f"'{configured}' is {wanted} — rebuild it")
        else:
            facts[-1] += f" ({configured})"
    for what, module in (("import_check", str(config["python"].get("import_check", "") or "").strip()),
                         ("test_command", _test_runner_module(config))):
        if not module:
            continue
        res = subprocess.run([str(vpy), "-c", f"import {module}"], cwd=str(repo_root),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            why = ("its test runner is not installed, so `python -m "
                   f"{module}` cannot run" if what == "test_command"
                   else f"`import {module}` fails")
            return "stale", why
        facts.append(f"`import {module}` succeeds")
    return "ok", "; ".join(facts)


def env_status(repo_root: Path, config: Dict[str, Dict[str, object]]) -> str:
    """Return 'ok', 'missing', or 'stale' for the project venv."""
    return env_report(repo_root, config)[0]


#: Seconds a ``[validation]`` expression may run. Generous — importing a GPU
#: stack and initialising its driver takes seconds — but finite: a profile is
#: evaluated inside unattended runs, where a hang stalls the loop silently.
PROFILE_TIMEOUT = 120


def evaluate_profile(repo_root: Path, config: Dict[str, Dict[str, object]],
                     expr: str, timeout: float = PROFILE_TIMEOUT
                     ) -> Tuple[bool, str]:
    """``(satisfied, detail)`` for a ``[validation]`` expression, evaluated in
    the project venv (this interpreter when there is none).

    It evaluates the expression and nothing else: whether this machine
    provides the capability, never whether the gated path works. *detail* is
    the last stderr line, or why the expression could not be evaluated.

    An expression that times out, or an interpreter that cannot be started, is
    **not satisfied**: the reading under which validation records
    ``❓ Unverified`` rather than passing. The one evaluation
    ``aide env --profile`` and ``aide status --profiles`` share, so the two can
    never disagree about whether this machine has a capability.
    """
    vpy = venv_python(repo_root, config)
    interpreter = str(vpy) if vpy.exists() else sys.executable
    code = f"import sys\nsys.exit(0 if ({expr}) else 1)"
    try:
        # §6: name the codec — a traceback carrying a non-ASCII path decodes
        # differently under a Windows locale, and this text is reported to a user.
        res = subprocess.run([interpreter, "-c", code], cwd=str(repo_root),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout:g}s"
    except OSError as exc:
        return False, f"interpreter '{interpreter}' cannot be run: {exc}"
    detail = (res.stderr or "").strip().splitlines()
    return res.returncode == 0, detail[-1] if detail else ""


def cmd_env(args: argparse.Namespace) -> int:
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)

    if getattr(args, "profile", None):
        # Evaluate a named [validation] environment profile deterministically.
        profiles = {k: str(v) for k, v in (config.get("validation") or {}).items()}
        expr = profiles.get(args.profile)
        if expr is None:
            known = ", ".join(sorted(profiles)) or "(none defined)"
            print(f"aide env: unknown profile '{args.profile}' — [validation] defines: {known}",
                  file=sys.stderr)
            return 2
        satisfied, detail = evaluate_profile(repo_root, config, expr)
        if satisfied:
            print(f"aide env: profile '{args.profile}' satisfied")
            return 0
        suffix = f" ({detail})" if detail else ""
        print(f"aide env: profile '{args.profile}' NOT satisfied{suffix} — "
              f"validation gated on it must record '❓ Unverified', never a silent pass")
        return 1

    status, detail = env_report(repo_root, config)
    if status == "ok":
        print(f"aide env: OK ({detail})")
        return 0
    if not args.bootstrap:
        print(f"aide env: {status} — {detail}; run "
              f"'python .aide/scripts/aide.py env --bootstrap' to build it")
        return 1
    venv = _venv_dir(repo_root, config)
    bootstrap = str(config["python"].get("bootstrap", "pip install -e .[dev]")).split()
    interpreter = _configured_interpreter(config)
    # A stale venv is rebuilt from nothing: `-m venv` over an existing tree
    # re-points the scripts and pyvenv.cfg at the new interpreter and keeps
    # the old site-packages beside them, which is neither venv.
    venv_args = ["-m", "venv", *(["--clear"] if venv.exists() else []), str(venv)]
    print(f"aide env: bootstrapping {venv} with {' '.join(interpreter)} …")
    try:
        made = subprocess.run([*interpreter, *venv_args], cwd=str(repo_root), check=False)
    except OSError as exc:
        print(f"aide env: [python] interpreter '{' '.join(interpreter)}' cannot "
              f"be run ({exc}) — nothing was built. Install it, or name one "
              f"this machine has in aide.toml.", file=sys.stderr)
        return 1
    if made.returncode != 0:
        print(f"aide env: '{' '.join(interpreter)} -m venv' exited "
              f"{made.returncode} — nothing was built.", file=sys.stderr)
        return 1
    vpy = venv_python(repo_root, config)
    cmd = [str(vpy), "-m", *bootstrap] if bootstrap and bootstrap[0] == "pip" else [str(vpy), *bootstrap]
    installed = subprocess.run(cmd, cwd=str(repo_root), check=False)
    # The record is what lets a later `env` tell a finished install from one
    # that aborted after the editable project landed (issue #166). Written
    # on both outcomes, so a completed rebuild clears an earlier failure.
    (venv / _BOOTSTRAP_RECORD).write_text(json.dumps({
        "exit": installed.returncode, "command": cmd,
        "interpreter": interpreter,
        "python": _python_version([str(vpy)], repo_root)}, indent=2) + "\n",
        encoding="utf-8")
    if installed.returncode != 0:
        print(f"aide env: bootstrap FAILED — '{' '.join(cmd)}' exited "
              f"{installed.returncode}. The venv exists but its install did "
              f"not finish, and `env` reports it stale until a bootstrap "
              f"completes.", file=sys.stderr)
        return 1
    final, detail = env_report(repo_root, config)
    print(f"aide env: bootstrap done ({final}: {detail})")
    return 0 if final == "ok" else 1


def _slug(title: str, max_words: int = 5) -> str:
    words = re.findall(r"[A-Za-z0-9]+", title.lower())
    return "-".join(words[:max_words]) or "item"


def _queue_titles(text: str) -> Dict[int, str]:
    titles: Dict[int, str] = {}
    for line in text.splitlines():
        m = re.match(r"^###\s+Item\s+0*(\d+)\s*:\s*(.+?)\s*$", line)
        if m:
            titles[int(m.group(1))] = m.group(2)
    return titles


#: Marks the start of a **forward-looking** aside inside a Dependencies section
#: — later items that depend on THIS one, not items this one depends on (e.g.
#: "**Downstream:** item 099 depends on this item's CI job"). Item numbers
#: after this marker are never read as blocking dependencies: extracting every
#: "Item NNN" mention in the section without it would misread "X depends on
#: this" as "this depends on X" and block on a backward reference to a later,
#: still-open item. Authors: put such asides after this exact marker so the
#: parser (and a human skimming the section) can tell the two apart.
_DEPENDENCIES_DOWNSTREAM_MARKER_RE = re.compile(r"\*\*Downstream\b", re.IGNORECASE)

#: Marks a quoted human-gate reach ("waits on Gate 3 — `Blocks: items 119,
#: 120, 121`"). Transcribing the gate row's cell is the natural way to say
#: which gate holds this item, and the numbers in the quote are the GATE's
#: reach, not items this one depends on — read as blockers they grew edges
#: (and cycles) nobody authored. Like ``**Downstream``, the marker must be
#: DELIBERATE markup — a backticked or bold ``Blocks:`` label, the forms a
#: quoted table cell actually takes — never bare prose: "hard blocks: Items
#: 027 and 028 must land first" states real blockers, and an exclusion plain
#: English could trip would silently drop them. The pattern consumes to the
#: end of the line and no further: the quote opens no subsection, so a
#: dependency bullet on the next line must still be read (which also means a
#: reach quote must not wrap — keep it on one line, as the template says).
_DEPENDENCIES_BLOCKS_QUOTE_RE = re.compile(
    r"(?:`|\*\*)blocks\*{0,2}\s*:[^\n]*", re.IGNORECASE)


def _item_dependencies(repo_root: Path, config, number: int) -> List[int]:
    """Item numbers named in the spec's Dependencies section (best effort).

    Uses the same multi-item/range-aware, case-insensitive extraction as every
    other "does this reference item NNN" call site (`_referenced_item_numbers`)
    — a naive first-number-only regex here previously left every number after
    the first in "Items 093, 094, 095" unrecognised as a blocker. Text at or
    after a "**Downstream" marker is excluded (see
    `_DEPENDENCIES_DOWNSTREAM_MARKER_RE`), so a forward-looking "item 099
    depends on this" aside does not register as a backward blocker; likewise
    the rest of any line from a backticked or bold "Blocks:" marker on (see
    `_DEPENDENCIES_BLOCKS_QUOTE_RE`), so a quoted gate reach does not either.
    """
    idir = docs_dir(repo_root, config) / "items"
    specs = item_spec_paths(idir, number)
    if not specs:
        return []
    text = specs[0].read_text(encoding=_ENCODING)
    m = re.search(r"^##\s+Dependencies\s*$(.*?)(^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    section = m.group(1) if m else ""
    downstream = _DEPENDENCIES_DOWNSTREAM_MARKER_RE.search(section)
    if downstream is not None:
        section = section[: downstream.start()]
    section = _DEPENDENCIES_BLOCKS_QUOTE_RE.sub("", section)
    deps = set(_referenced_item_numbers(section))
    deps.discard(number)
    return sorted(deps)


def _pick_item(repo_root: Path, config, queue_text: str,
               claim_branches: List[str]) -> Optional[Tuple[int, str]]:
    """First queue item that is planned, unclaimed, and unblocked. (number, title).

    "Unblocked" covers three things: its `## Dependencies` are all under way,
    no claim branch exists for it, and **no unresolved human gate holds it**. A
    gate naming items (directly, or via `stage N`) skips just those, so the
    queue keeps producing other work; an `all` gate stops everything, which is
    the point of declaring one — a pending decision that could invalidate what
    comes next must not have the loop racing ahead of it. A gates row too
    mis-shaped to read stops everything too, since what it holds is unknown.
    """
    ppath = docs_dir(repo_root, config) / "progress.md"
    plines = ppath.read_text(encoding=_ENCODING).splitlines() if ppath.is_file() else []
    _, _, item_status = _parse_item_status(plines) if plines else ([], [], {})
    gate_blocked, block_everything = gate_blocked_items(plines)
    if block_everything or unreadable_gate_rows(plines):
        return None
    # Anchored resolution, like every other branch->item call site since 1.5.0.
    # The old unanchored search read `aide/queue-016` as item 016 and
    # `aide/specs-queue-015` as item 015, marking those items permanently
    # "claimed" and therefore unclaimable — a queue branch is not an item claim.
    # This call site was missed when the shared helper landed.
    prefix = str(config["git"].get("branch_prefix", "aide/"))
    claimed_nums = {n for n in (_branch_item_number(br, prefix) for br in claim_branches)
                    if n is not None}
    titles = _queue_titles(queue_text)
    for num in queue_item_numbers(queue_text):
        if item_status.get(num, "planned") != "planned":
            continue
        if num in claimed_nums:
            continue
        if num in gate_blocked:
            continue
        deps = _item_dependencies(repo_root, config, num)
        # 🔍 blocks like 🚧 does: an item whose PR is still open is work that is
        # not in the base, so claiming a dependent off that base would branch
        # from a tree missing the very thing the dependency provides. Under
        # `auto-merge` this window is milliseconds; under `pr` it is however
        # long the human takes, which is exactly when it matters.
        if any(item_status.get(d, "planned") in BLOCKING_STATUSES for d in deps):
            continue
        return num, titles.get(num, f"item {num}")
    return None


def _open_queue_texts(repo_root: Path, config) -> List[str]:
    """Texts of the open queues, lowest-numbered first (derived state)."""
    qdir = docs_dir(repo_root, config) / "queue"
    if not qdir.is_dir():
        return []
    item_status = _progress_item_status(repo_root, config)
    out: List[str] = []
    for path in iter_queue_paths(qdir):
        text = path.read_text(encoding=_ENCODING)
        if queue_is_open(text, item_status):
            out.append(text)
    return out


def _live_queue_text(repo_root: Path, config, number: Optional[int]) -> Optional[str]:
    """The queue to work: an explicit number, else the lowest-numbered OPEN
    queue (state derived from progress.md). Falls back to the highest queue
    declaring ``Status: Live`` only when progress.md is missing (legacy)."""
    qdir = docs_dir(repo_root, config) / "queue"
    if number is not None:
        path = queue_path(qdir, number)
        return path.read_text(encoding=_ENCODING) if path is not None else None
    if not qdir.is_dir():
        return None
    if (docs_dir(repo_root, config) / "progress.md").is_file():
        open_texts = _open_queue_texts(repo_root, config)
        return open_texts[0] if open_texts else None
    for path in sorted(iter_queue_paths(qdir), reverse=True):
        text = path.read_text(encoding=_ENCODING)
        if is_live_queue(text):
            return text
    return None


def _report_nothing_claimable(repo_root: Path, config, prefix: str,
                              candidates: List[str],
                              claim_branches: List[str]) -> int:
    """Say why `claim` found nothing, and exit non-zero when that is a defect.

    "none left" is a claim about the ground checked, not the repository
    (conventions.md §2), and `/aide-run-queue` reads it as "the queue is
    finished — stop and report". Every reason a queue can be open while
    nothing in it is offerable therefore has to be said out loud, because the
    alternative is a run that ends reporting success over work it never
    started: issue #137, where a failed push left a claim branch behind and
    the next run called the queue exhausted.

    Two of the reasons are ordinary — a claim in flight, a dependency not
    landed — and keep exit 0. An **unpublished** claim is not: it is a `claim`
    whose push failed, holding an item on evidence no other checkout can see,
    so it exits 1 and says how to finish or release it. Nor is an
    **unreadable gate row**, which holds every item on a gate nobody can read:
    exit 1, naming the row.
    """
    ppath = docs_dir(repo_root, config) / "progress.md"
    plines = ppath.read_text(encoding=_ENCODING).splitlines() if ppath.is_file() else []
    _, _, item_status = _parse_item_status(plines) if plines else ([], [], {})

    unreadable = unreadable_gate_rows(plines)
    if unreadable:
        print("none left — every item is held by a human-gate row aide cannot "
              "read, since what it blocks is unknown:")
        for lineno, problem in unreadable:
            print(f"  progress.md:{lineno}: a row that {problem}")
        print("  Repair the row — a '|' inside a cell is the usual cause — and "
              "claim again. `aide check` names it too.")
        return 1
    # Queue scan order, not numeric order: `_pick_item` walks the candidate
    # queues in order and each queue in its own order, so a report that
    # renumbered the items it rejected would not be describing the same walk.
    # It shows under `loop.claim_scope = "all-open"`, where sorting numerically
    # interleaves two queues that were scanned one after the other.
    scan_order: List[int] = []
    seen = set()
    titles: Dict[int, str] = {}
    for qt in candidates:
        titles.update(_queue_titles(qt))
        for n in queue_item_numbers(qt):
            if n not in seen:
                seen.add(n)
                scan_order.append(n)
    open_items = {n for n in seen
                  if item_status.get(n, "planned") == "planned"}
    open_ordered = [n for n in scan_order if n in open_items]

    # Attribute the empty result to a gate ONLY when a gate actually explains
    # it: an `all` gate, or a gate reaching an item that is still open in a
    # queue we just scanned. A gate holding unrelated items — or naming
    # nothing — is not why this run found no work, and blaming it would be a
    # false explanation, which is worse than none.
    def _reached(g):
        if g.blocks_all:
            return set(open_items)
        if g.stage is not None:
            return set(stage_item_numbers(plines, g.stage)) & open_items
        return set(g.blocks) & open_items

    relevant = [(n, g) for n, g in enumerate(human_gates(plines), start=1)
                if g.kind != "approved" and (g.blocks_all or _reached(g))]
    if relevant:
        print("none left — held by an unresolved human gate:")
        for n, g in relevant:
            held = sorted(_reached(g))
            where = "everything" if g.blocks_all else (
                f"{g.reach} — holding " + ", ".join(f"{i:03d}" for i in held))
            print(f"  gate {n}: {g.text} — blocks {where}")
        print("  A person decides these, never an agent. Once decided: "
              "aide gate approve <n> --evidence \"…\" (or gate decline <n>).")
        return 0

    if not open_items:
        print("none left")
        return 0

    # Open items, none offered. Give the reason per item, in the order
    # `_pick_item` rejects them, so the two cannot drift into disagreeing
    # about why an item was skipped.
    claimed: Dict[int, str] = {}
    for br in claim_branches:
        num = _branch_item_number(br, prefix)
        if num is not None:
            claimed.setdefault(num, br)
    stranded = {n: br for n, br
                in _unpublished_claim_branches(repo_root, config, prefix).items()
                if n in open_items}

    print(f"none left — {len(open_ordered)} item(s) still open, none claimable:")
    for num in open_ordered:
        head = f"  {num:03d} {titles.get(num, 'item ' + str(num))} —"
        br = claimed.get(num)
        if num in stranded:
            print(f"{head} claimed by {stranded[num]}, WHICH ORIGIN HAS NEVER "
                  f"SEEN — the claim's push did not land, so this item is held "
                  f"by a claim no other checkout can see")
        elif br is not None:
            print(f"{head} claimed by {br}, already in flight")
        else:
            blockers = [d for d in _item_dependencies(repo_root, config, num)
                        if item_status.get(d, "planned") in BLOCKING_STATUSES]
            if blockers:
                print(f"{head} waiting on "
                      + ", ".join(f"{d:03d} ({item_status.get(d, 'planned')})"
                                  for d in blockers))
            else:
                print(f"{head} open and unblocked, yet not offered — please "
                      f"report this")

    if stranded:
        print("  An unpublished claim is a failed 'aide claim' push, not work "
              "in flight. Publish it ('git push -u origin <branch>') or "
              "release the item ('git branch -D <branch>'), then claim again.")
        return 1
    return 0


def cmd_claim(args: argparse.Namespace) -> int:
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    prefix = str(config["git"].get("branch_prefix", "aide/"))
    mode = str(config["git"].get("mode", "auto-merge"))
    scope = str(config["loop"].get("claim_scope", "live-queue"))
    if mode != "local":
        git(["fetch", "--all", "--prune"], repo_root, check=False)

    if args.queue is None and scope == "all-open":
        # Cross-queue claiming (opt-in): scan every open queue in number order.
        candidates = _open_queue_texts(repo_root, config)
    else:
        queue_text = _live_queue_text(repo_root, config, args.queue)
        candidates = [queue_text] if queue_text is not None else []
    if not candidates:
        print("aide claim: no open queue found", file=sys.stderr)
        return 1
    branches = _list_claim_branches(repo_root, prefix)
    pick = None
    for queue_text in candidates:
        pick = _pick_item(repo_root, config, queue_text, branches)
        if pick is not None:
            break
    if pick is None:
        return _report_nothing_claimable(repo_root, config, prefix,
                                         candidates, branches)
    number, title = pick
    branch = claim_branch_name(prefix, number, title)

    # What this claim branches off, and what its `merge` will return it to.
    # `switch -c` already branches from whatever is checked out, so claiming
    # from a queue branch has always branched correctly — only the merge target
    # was fixed. Inferring the base from a *recognised queue branch* (never from
    # an arbitrary branch, which would silently retarget a merge) closes that
    # half without asking every caller to pass a flag it cannot know.
    current = _current_branch(repo_root)
    base = args.base or (current if _is_queue_branch(current, prefix)
                         else str(config["git"].get("main_branch", "main")))

    if not _local_branch_exists(repo_root, base):
        print(f"aide claim: base '{base}' is not a local branch — an item is "
              f"branched from its base and merged back into it, so the base "
              f"must be a branch this checkout can update", file=sys.stderr)
        return 1

    pin_report = _interface_pin_report(repo_root, config, number)
    if args.dry_run:
        print(f"would claim item {number:03d} -> {branch} ({title}); base {base}")
        if pin_report:
            print(pin_report)
        return 0
    # Branch FROM the base, explicitly. `switch -c` with no start point uses
    # HEAD, which would let the branch's actual starting point disagree with
    # the base it records — claiming with `--base main` while a queue branch is
    # checked out would start from the queue branch and then merge the whole of
    # it into main. Naming the start point makes the two agree by construction.
    git(["switch", "-c", branch, base], repo_root)
    _record_branch_base(repo_root, branch, base)
    # `/aide-run-queue` reaches its roles through `sync` and this verb, never
    # through `check`, so the §1 guarantee is kept here too: on the new branch,
    # before the push, so the inbox lands with the item and the claim's own
    # base is left exactly as it was.
    ensure_insights_inbox(repo_root, config, verb="claim")
    if mode != "local":
        failure = _push_new_branch(repo_root, branch)
        if failure is not None:
            # The branch is KEPT, not rolled back. The push may have reached
            # origin before the client gave up, and deleting here would then
            # leave a remote claim branch blocking the item with nothing local
            # left to explain it. What must not happen is the half-claim
            # reading as a claim: `_pick_item` skips any item with a claim
            # branch, so before this the next run said "none left" and an
            # unattended loop finished, successfully, having built nothing.
            # `claim`, `status` and `check` all name an unpublished
            # claim now, so it cannot pass for work in flight.
            print(f"aide claim: {failure}\n"
                  f"Item {number:03d} is claimed LOCALLY ONLY: {branch} exists "
                  f"here (base {base}) and origin has never seen it, so no "
                  f"other checkout can see the claim. Publish it with "
                  f"'git push -u origin {branch}' once the remote is "
                  f"reachable, or release the item with 'git switch {base} && "
                  f"git branch -D {branch}'.", file=sys.stderr)
            return 1
    note = "" if base == str(config["git"].get("main_branch", "main")) else f" (base {base})"
    print(f"claimed item {number:03d}: {branch} — {title}{note}")
    if pin_report:
        print(pin_report)
    return 0


def interface_pins(spec_text: str, deps: List[int],
                   item_status: Dict[int, str]) -> List[Tuple[int, str, int, str]]:
    """``(bullet index, label, dependency, status)`` for each Assumption that
    pins a dependency's interface — the re-check signal of conventions.md §5.

    An Assumption naming an item under ``## Dependencies`` was written before
    that item was built, and a claim happens only once it has left the way, so
    the pin is what says "re-check me". Three shapes are not the signal and
    are skipped here exactly as §5 lists them: an engine-marked audit entry
    (`assumption_engine_pin`), a bullet already carrying a re-check, and —
    reported rather than skipped — a dependency that left the queue as ❌/⏸️,
    which has no code to check against.
    """
    out: List[Tuple[int, str, int, str]] = []
    for index, bullet in enumerate(_assumption_bullets(spec_text), 1):
        named = [d for d in _referenced_item_numbers(bullet) if d in deps]
        if not named or assumption_engine_pin(bullet) is not None:
            continue
        # A *recorded* re-check carries a version or a date somewhere in the
        # bullet; "to be re-checked before tests" carries neither, and is
        # exactly the bullet to surface.
        if (re.search(r"re-?checked", bullet, re.IGNORECASE)
                and re.search(r"\d+\.\d+\.\d+|\d{4}-\d{2}-\d{2}", bullet)):
            continue
        m = re.match(r"^\s*[-*]\s+\**\s*([^:*]{1,40}?)\s*(?:\(|:|\*\*)", bullet)
        label = m.group(1).strip() if m else f"assumption #{index}"
        for dep in named:
            out.append((index, label, dep, item_status.get(dep, "unknown")))
    return out


def _interface_pin_report(repo_root: Path, config, number: int) -> Optional[str]:
    idir = docs_dir(repo_root, config) / "items"
    specs = item_spec_paths(idir, number)
    if not specs:
        return None
    deps = _item_dependencies(repo_root, config, number)
    if not deps:
        return None
    pins = interface_pins(specs[0].read_text(encoding=_ENCODING), deps,
                          _progress_item_status(repo_root, config))
    if not pins:
        return None
    absent = {"excluded", "deferred"}
    parts = [f"{label} (item {dep:03d}"
             + (", no code to check against" if st in absent else "") + ")"
             for _, label, dep, st in pins]
    distinct = len({index for index, _, _, _ in pins})
    return (f"aide claim: {distinct} assumption(s) pin a dependency's interface "
            f"— re-check before tests are written (conventions.md §5): "
            + "; ".join(parts))


def _find_claim_branch(repo_root: Path, prefix: str, number: int) -> Optional[str]:
    for br in _list_claim_branches(repo_root, prefix):
        if _branch_item_number(br, prefix) == number:
            return br
    return None


def _git_dir(repo_root: Path) -> Path:
    """The repository's git directory, resolved.

    Not ``repo_root / ".git"``: that is a *file* in a linked worktree or a
    submodule, so probing `.git/MERGE_HEAD` there answers "no in-progress
    merge" for every such consumer — the exact reading the caller below must
    not get wrong.
    """
    out = git(["rev-parse", "--git-dir"], repo_root, check=False).stdout.strip()
    if not out:
        return repo_root / ".git"
    path = Path(out)
    return path if path.is_absolute() else repo_root / path


#: In-progress git operations, and how git names each one's marker in the git
#: directory. `switch` and `pull --rebase` on top of any of them either refuse
#: (leaving a half-merge the loop cannot read) or rewrite commits the human is
#: mid-way through authoring.
_INTERRUPTED_OPS: Tuple[Tuple[str, str], ...] = (
    ("rebase-merge", "a rebase is in progress"),
    ("rebase-apply", "a rebase or 'git am' is in progress"),
    ("MERGE_HEAD", "a merge is in progress with conflicts unresolved"),
    ("CHERRY_PICK_HEAD", "a cherry-pick is in progress"),
    ("REVERT_HEAD", "a revert is in progress"),
)


def _unmerged_paths(repo_root: Path) -> List[str]:
    """Every path git currently holds unmerged, repo-relative, sorted."""
    try:
        out = git(["diff", "--name-only", "--diff-filter=U"], repo_root, check=False)
    except (OSError, subprocess.SubprocessError):
        return []
    if out.returncode != 0:
        return []
    return sorted({line.strip() for line in out.stdout.splitlines() if line.strip()})


def _interrupted_op(repo_root: Path) -> Optional[str]:
    """The in-progress git operation this tree is stopped in, or ``None``.

    One reading of `_INTERRUPTED_OPS`, shared by the callers that ask the
    question for different reasons: `_unsafe_tree_state` asks it *before*
    acting, `_stalled_pull` asks it *after* a `pull --rebase` came back
    non-zero. The second is what tells a failed pull that stopped on a
    conflict apart from one that never started — no upstream configured, an
    unreachable origin — since only the former leaves a marker behind.
    """
    gdir = _git_dir(repo_root)
    for marker, what in _INTERRUPTED_OPS:
        if (gdir / marker).exists():
            return what
    return None


def _continue_command(repo_root: Path) -> str:
    """What finishes the operation this tree is stopped in, once staged."""
    gdir = _git_dir(repo_root)
    if (gdir / "rebase-merge").exists() or (gdir / "rebase-apply").exists():
        return "git rebase --continue"
    if (gdir / "CHERRY_PICK_HEAD").exists():
        return "git cherry-pick --continue"
    if (gdir / "REVERT_HEAD").exists():
        return "git revert --continue"
    return "git commit --no-edit"


def _abort_command(repo_root: Path) -> str:
    """What throws away the operation this tree is stopped in.

    The mirror of `_continue_command`, and derived the same way rather than
    written as a fixed pair: `_stalled_pull` reaches this with a cherry-pick or
    a revert marker whenever the pull refused because one was *already* in
    progress, and `git rebase --abort` is not merely unhelpful there — it fails.
    """
    gdir = _git_dir(repo_root)
    if (gdir / "rebase-merge").exists() or (gdir / "rebase-apply").exists():
        return "git rebase --abort"
    if (gdir / "CHERRY_PICK_HEAD").exists():
        return "git cherry-pick --abort"
    if (gdir / "REVERT_HEAD").exists():
        return "git revert --abort"
    return "git merge --abort"


def _inbox_conflict_hint(repo_root: Path,
                         config: Dict[str, Dict[str, object]]) -> Optional[str]:
    """Name `insights resolve` when the stalled operation is stuck on the inbox.

    The verb is useless to the role that needs it unless the thing that stalls
    says so. `insights.md` is append-only and every role captures into it
    (`_ALWAYS_AUTHORISED`), so two open branches conflict here as a matter of
    course — while the agent that runs `aide merge` is the `validator`, which
    preloads a different skill and has read nothing about the inbox. A message
    at the point of the stall reaches every role, every runtime, and a human,
    without any of them having had to read anything first.

    It also says whether the inbox is the *only* unmerged path, because that
    decides whether the verb finishes the job or is merely one of the steps.
    """
    ddir = docs_dir(repo_root, config)
    try:
        rel = (ddir / "insights.md").relative_to(repo_root).as_posix()
    except ValueError:          # a docs_dir outside the repo: no relative name
        return None
    unmerged = _unmerged_paths(repo_root)
    if rel not in unmerged:
        return None
    verb = "python .aide/scripts/aide.py insights resolve"
    warn = (f"Do NOT resolve {rel} by hand — it is append-only, so the "
            f"conflict is a union of entries, and retyping the block is where "
            f"a captured claim gets reworded (conventions.md §1).")
    others = [p for p in unmerged if p != rel]
    if not others:
        return (f"{rel} is the ONLY unmerged path. {warn} `{verb}` writes the "
                f"union and stages it (add --dry-run to read it first), then "
                f"`{_continue_command(repo_root)}` finishes this.")
    return (f"{rel} is one of {len(unmerged)} unmerged paths. {warn} `{verb}` "
            f"settles that one; the rest are yours: {', '.join(others)}.")


def _stalled_pull(repo_root: Path, config: Dict[str, Dict[str, object]],
                  res: "subprocess.CompletedProcess") -> Optional[str]:
    """One line for a ``pull --rebase`` that stopped mid-way, else ``None``.

    ``git pull --rebase`` comes back non-zero for two unrelated reasons and
    only one of them is a state the caller must not act on. A pull that never
    started — no upstream for this branch, an origin that cannot be reached, a
    refused fetch — leaves the repository byte-for-byte as it was, and every
    call site below has always continued past it into a local operation that
    is still correct; making that a refusal would stall an unattended run over
    a missing remote. A pull that stopped **inside** the rebase leaves
    conflicts in the index and a marker in the git directory, and there the
    next `merge`, `commit` or `switch` cannot run at all — git refuses, naming
    that second operation rather than the rebase that caused it, so the
    operator reads a failure of something they did not ask for while the tree
    sits in a state neither message describes (issue #178).

    So the discriminator is the marker, not the exit code — and the message
    names the operation git reports rather than assuming a rebase, since a
    pull that refused because a cherry-pick or a merge was already under way
    lands here with that marker and no rebase of its own. The message names
    `insights resolve` when the inbox is what stopped it: `insights.md` is
    append-only and every role captures into it, which makes it the conflict
    this loop produces as a matter of course, and none of the three roles that
    reach these call sites has read anything about it.
    """
    if res.returncode == 0:
        return None
    what = _interrupted_op(repo_root)
    if what is None:
        return None
    return f"git pull --rebase could not complete — {_stopped_state(repo_root, config, what)}"


def _stopped_state(repo_root: Path, config: Dict[str, Dict[str, object]],
                   what: str) -> str:
    """*what* is in progress, and the two ways out of it — one sentence.

    Shared by `_stalled_pull` (a pull that stopped, or refused because *what*
    was already under way) and the guard `_commit_docs_files` runs before it
    commits, so both name the same state the same way. Never "the rebase
    stopped": *what* is whichever of `_INTERRUPTED_OPS` is in progress, and a
    cherry-pick ALREADY under way is the reachable case at the committer.
    Naming the operation git reports, and the abort that matches it, is the
    whole point — a message that guessed `git rebase --abort` there would hand
    the reader a command that fails. `insights resolve` is named when the
    inbox is what stopped it.
    """
    hint = _inbox_conflict_hint(repo_root, config)
    return (f"{what}."
            + (f" {hint}" if hint else "")
            + f" Finish that state — resolve and stage, then "
              f"`{_continue_command(repo_root)}` — or abort it "
              f"(`{_abort_command(repo_root)}`), then re-run.")


def _dirty_paths(repo_root: Path) -> List[str]:
    """Tracked paths carrying uncommitted changes, as git reports them.

    `-z`, not plain `--porcelain`: without it git **quotes and escapes** a path
    holding a space or a non-ASCII byte — `"docs/h\303\251llo/progress.md"` —
    which is neither the path on disk nor anything a caller can compare one
    against. NUL-terminated records never quote and never escape, so a consumer
    whose docs directory has a space in it reads the same as everyone else.

    Paths are relative to the git **worktree top level**, not to the cwd and not
    to `repo_root` — git is consistent about that, and a caller resolving them
    must be too.
    """
    out = git(["status", "--porcelain", "-z"], repo_root, check=False).stdout
    fields = out.split("\0")
    paths: List[str] = []
    i = 0
    while i < len(fields):
        record, i = fields[i], i + 1
        if len(record) < 4:                     # the empty tail after the last NUL
            continue
        code, path = record[:2], record[3:]
        if code[0] in "RC":
            i += 1                              # a rename/copy's SOURCE is its own field
        if code == "??":                        # untracked — see _unsafe_tree_state
            continue
        paths.append(path)
    return paths


def _unsafe_tree_state(repo_root: Path,
                       tick_path: Optional[Path] = None) -> Optional[str]:
    """Why this tree must not be switched/pulled/merged, or None if it may be.

    `aide merge` exists so that agents do not improvise git (§3), which means a
    consumer obeying §3 has no remaining place to be careful: whatever the verb
    does unconditionally is what happens. It already refuses one adjacent
    footgun with a precise diagnosis — a base that resolves but is not a local
    branch — and this is the same class, an operation that silently produces a
    wrong result while reporting success (issue #133).

    Untracked files are deliberately NOT dirty here. They survive `switch` and
    `pull` untouched, a loop leaves them around constantly, and a merge that
    genuinely collides with one aborts with git's own message through the merge
    path below. Refusing on them would block the common case to catch nothing.
    """
    interrupted = _interrupted_op(repo_root)
    if interrupted:
        return interrupted
    paths = _dirty_paths(repo_root)
    if not paths:
        return None
    # The one dirty tree this verb is likely to have caused itself: `--no-commit`
    # (on `merge` or on `progress set`) writes the tick and deliberately leaves
    # it uncommitted, and the NEXT merge — of any item — then meets this check.
    # The state is genuinely unsafe (git refuses `pull --rebase` over ANY
    # unstaged change, not merely a conflicting one), so it is still a refusal;
    # what it must not be is a mystery.
    #
    # Compared as resolved paths against the worktree top, never as strings
    # against `repo_root`: `aide.toml` may sit BELOW git's top level, and there
    # git's `docs/aide/progress.md` is this repo's `sub/docs/aide/progress.md`.
    if tick_path is not None and len(paths) == 1:
        top = git(["rev-parse", "--show-toplevel"], repo_root, check=False).stdout.strip()
        try:
            is_tick = (Path(top or repo_root) / paths[0]).resolve() == tick_path.resolve()
        except OSError:                          # an unresolvable path is not the tick
            is_tick = False
        if is_tick:
            return (f"{paths[0]} carries an uncommitted status tick — a "
                    f"`--no-commit` run wrote it and left committing to you. It "
                    f"is the only change in the tree; commit or discard it")
    shown = ", ".join(paths[:3])
    more = f" (+{len(paths) - 3} more)" if len(paths) > 3 else ""
    return f"the working tree has uncommitted changes: {shown}{more}"


def _has_unpushed_merge(repo_root: Path, upstream: str = "@{u}") -> bool:
    """Does HEAD carry a merge commit its upstream has not seen?

    The one shape `git pull --rebase` must not run over: rebasing DROPS the
    merge and replays both parents' commits individually, so a conflict a human
    resolved by hand inside that merge comes back (issue #133). No upstream
    means nothing to rebase against, which is not this shape. *upstream* names
    the ref to compare against when the branch has no tracking ref of its own
    — `sync --item` pulls `origin/<claim>` by name, so it asks about that ref
    (issue #235).
    """
    res = git(["rev-list", "--merges", f"{upstream}..HEAD"], repo_root, check=False)
    return res.returncode == 0 and bool(res.stdout.strip())


class _Terminated(BaseException):
    """Raised in place of a terminating signal, so a `finally` can run.

    Deliberately a `BaseException`: it is not an error the surrounding code
    should ever catch and continue past, exactly like the `KeyboardInterrupt`
    it stands beside.
    """


@contextlib.contextmanager
def _restore_on_signal(signals: Tuple[str, ...] = ("SIGTERM", "SIGHUP")):
    """Context manager: turn terminating signals into `_Terminated` inside it.

    `KeyboardInterrupt` already unwinds the stack, so a `try` arm covers Ctrl-C
    for free. `SIGTERM` does not — Python's default handler ends the process
    where it stands, no `finally`, no `except` — and SIGTERM is exactly how the
    unattended cases in issue #174 arrive: a CI job's timeout, a runner's wall
    clock, a supervisor tearing down a stuck step. Without this, the crash-safe
    restore below would cover only the case a human is present to watch.

    `SIGKILL` and a hard OOM kill remain uncoverable by construction, which is
    why the refusal in `cmd_merge` (issue #174, half 2) exists as well: this
    makes the interrupted run tidy up, that makes the *next* run safe whether
    or not it did.

    Best effort about where it can be installed: `signal.signal` is main-thread
    only and not every name exists on every platform (Windows has no SIGHUP).
    A signal it cannot claim is simply left alone.
    """
    def _raise(signum, _frame):
        raise _Terminated(signum)

    previous = []
    for name in signals:
        sig = getattr(signal, name, None)
        if sig is None:
            continue
        try:
            previous.append((sig, signal.signal(sig, _raise)))
        except (ValueError, OSError, RuntimeError):
            continue
    try:
        yield
    finally:
        for sig, old in previous:
            try:
                signal.signal(sig, old)
            except (ValueError, OSError, RuntimeError):
                pass


def _restore_claim_branch(repo_root: Path, branch: str, tip: str,
                          base: Optional[str] = None) -> None:
    """Put back a claim branch deleted ahead of a step that then failed.

    `merge` deletes the claim branch BEFORE the post-merge test run (so the run
    sees the refs a fresh clone would). Every exit after that point must
    therefore be re-runnable: without the ref, `_find_claim_branch` finds
    nothing and the retry dies at "no claim branch found" — with the work
    merged, un-ticked and unpushed, which is the state a human least wants to
    meet a refusal in.

    Re-runnable means *against the same base*, not merely runnable. `git
    branch -d` takes the branch's config section with the ref, and
    `branch.<claim>.aide-base` is the only input `resolve_base` has beyond
    `--base` — so a retry that found the ref put back resolved its base to
    `main_branch` and said nothing. A consumer's invited re-run fast-forwarded
    a whole queue branch onto `main` and pushed it, past its
    one-reviewed-PR-per-queue gate, with nothing in the output naming `main`
    (issue #167). *base* is the base THIS run resolved to and merged into —
    not what the branch recorded beforehand: a run given `--base` landed
    somewhere the record did not say, and a retry must land there again. It
    is written unconditionally, so a `branch -d` that refused (record intact,
    and possibly stale against `--base`) is corrected the same way as one
    that succeeded.
    """
    if tip and branch not in _local_branches(repo_root):
        git(["branch", branch, tip], repo_root, check=False)
    if base:
        _record_branch_base(repo_root, branch, base)


def _promote_item_to_complete(repo_root: Path, config, number: int,
                              no_commit: bool = False,
                              extra_rels: Tuple[str, ...] = ()) -> None:
    """Record item *number* as ✅ in progress.md — best effort, never fatal.

    Deliberately quiet about a no-op: the item may already be ✅ (a re-run, or a
    consumer still driving the old `progress set NNN done` ordering), and the
    merge itself is the thing that succeeded. It is *not* quiet about a missing
    progress.md, which is a real misconfiguration — but even that must not fail
    a merge that has already landed.

    Since 1.53.0 `cmd_merge`'s document gate reaches a lost progress.md first:
    with `docs_dir` present it is an `aide check` error, and the merge is
    refused before this runs (issue #232). The branch below is left for a repo
    with no document set at all, where the check passes and there is nothing
    to tick.

    *extra_rels* are paths the same commit carries — the ledger row `merge`
    has just appended (§1 → `ledger.md`). One commit, because the row and the
    ✅ are one fact about one item: two would let a run land the tick and lose
    the row, leaving a ledger a reader has to reconcile against progress.md.
    They are committed even where the tick itself is a no-op (a re-run over an
    item already ✅), since the row is new either way.
    """
    progress_path = docs_dir(repo_root, config) / "progress.md"
    rels = list(extra_rels)
    if not progress_path.is_file():
        print(f"aide merge: item {number:03d} merged, but {progress_path} was "
              f"not found, so its status was NOT recorded", file=sys.stderr)
    else:
        text = progress_path.read_text(encoding=_ENCODING)
        splits: List[BulletSplit] = []
        updated = set_item_status(text, number, "complete", splits)
        if updated != text:
            progress_path.write_text(updated, encoding="utf-8")
            print(f"item {number:03d}: set to done (merged)")
            _report_bullet_splits(number, updated.splitlines(), splits)
            rels.insert(0, str(config["project"].get("docs_dir", "docs/aide"))
                        + "/progress.md")
    if rels and not no_commit and (repo_root / ".git").exists():
        _commit_docs_files(repo_root, config,
                           f"progress(aide): item {number:03d} -> done", rels)


def cmd_merge(args: argparse.Namespace) -> int:
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    prefix = str(config["git"].get("branch_prefix", "aide/"))
    mode = str(config["git"].get("mode", "auto-merge"))
    branch = args.branch or _find_claim_branch(repo_root, prefix, args.number)
    if not branch:
        print(f"aide merge: no claim branch found for item {args.number:03d}", file=sys.stderr)
        return 1

    # Where this item lands: --base > what the claim recorded > main_branch.
    # Hard-wiring main_branch is what forced a consumer to merge every item of a
    # queue by hand — the queue file, a roadmap deliverable and nine item specs
    # lived only on the queue branch and had to land as one reviewed PR, so each
    # item needed to merge *back into* that branch.
    recorded_base = _recorded_branch_base(repo_root, branch)
    main = resolve_base(repo_root, config, args.base, branch)
    # Named on every run, whatever chose it. The fallback to main_branch is
    # right for a branch this machine never claimed, and it is exactly the
    # case a retargeted merge hides in: the one run that quietly landed a
    # queue on `main` reported nothing a transcript could catch (issue #167).
    if args.base:
        chosen = "from --base"
    elif recorded_base:
        chosen = f"recorded for {branch} at claim, or by an earlier merge run"
    else:
        # Refused, not defaulted (issue #174). `claim` records a base for every
        # branch it creates, so a claim branch with none is a branch whose
        # record was LOST — most often with the ref itself, by the `branch -d`
        # below in a run that was then killed before it could put either back.
        # `resolve_base` cannot tell that apart from "this machine never
        # claimed it"; `merge` can, because it is the verb that does the
        # deleting, and the two readings differ by a force-push: a consumer's
        # re-run took the silent `main_branch` fallback and fast-forwarded a
        # whole queue branch onto `main`, past its one-reviewed-PR-per-queue
        # gate, with nothing in the output naming `main`.
        #
        # A first merge onto `main` from a hand-made branch is the legitimate
        # shape this refuses, and `--base` is what it passes — one word, said
        # once, in exchange for the fallback never being taken by accident.
        print(f"aide merge: no base is recorded for {branch}, so this run "
              f"cannot tell where item {args.number:03d} is meant to land. "
              f"Guessing would mean the [git] main_branch default "
              f"('{main}'), and a claim branch reaches this state by losing "
              f"its record — typically to an interrupted earlier merge — so "
              f"the guess is exactly as likely to be a queue branch's work "
              f"pushed onto {main}. Re-run with the base named: "
              f"'merge {args.number:03d} --base <branch>'.", file=sys.stderr)
        return 1
    print(f"aide merge: item {args.number:03d} lands on {main} ({chosen})")
    if not _local_branch_exists(repo_root, main):
        detail = ("it resolves, but not to a local branch — `git switch` would "
                  "detach HEAD, and a merge into a detached HEAD updates no "
                  "branch while still reporting success"
                  if _ref_exists(repo_root, main) else "no such local branch")
        print(f"aide merge: base '{main}' cannot be merged into: {detail}. "
              f"Pass a local branch as --base.", file=sys.stderr)
        return 1

    if mode == "pr":
        failure = _push_new_branch(repo_root, branch)
        if failure is not None:
            print(f"aide merge (pr mode): {failure}\n"
                  f"Nothing else was done — item {args.number:03d} is NOT "
                  f"ticked, and no PR can be opened over a branch origin does "
                  f"not have. The work is intact on {branch}. Resolve the "
                  f"push, then re-run 'aide merge {args.number:03d}'.",
                  file=sys.stderr)
            return 1
        print(f"aide merge (pr mode): pushed {branch}. Open a PR against {main} "
              f"to land it (e.g. 'gh pr create'); merge is left to the human "
              f"review gate. Item {args.number:03d} stays 🔍 until it merges — "
              f"then run 'aide progress set {args.number:03d} done'.")
        return 0

    unsafe = _unsafe_tree_state(repo_root, docs_dir(repo_root, config) / "progress.md")
    if unsafe:
        # Resolution before abortion, and only when there is something to
        # resolve: an agent that reads "abort" literally aborts, re-runs, and
        # meets the identical conflict — a loop, and one this verb can end.
        hint = _inbox_conflict_hint(repo_root, config)
        print(f"aide merge: refusing to merge item {args.number:03d} — {unsafe}. "
              f"`git switch` and `git pull --rebase` from here rewrite or "
              f"discard work this process did not create."
              + (f"\naide merge: {hint}" if hint else "")
              + f"\naide merge: finish that state — resolve and stage, then "
                f"`{_continue_command(repo_root)}` — or abort it "
                f"(`git rebase --abort` / `git merge --abort`, or commit the "
                f"changes), then re-run. Aborting a conflict you have not "
                f"resolved brings it back on the next attempt.",
              file=sys.stderr)
        return 1

    # The ledger's derived cells, taken while the claim branch still exists:
    # the run is about to merge it and delete it, and the row's counts are a
    # diff of that branch against the base this run resolved (§1 →
    # `ledger.md`). Derived here, written after the tick — a row records a
    # merge that happened, so nothing is written where nothing lands. A
    # failure to derive costs the row and never the merge.
    findings = getattr(args, "findings", None)
    no_review = review_is_off(config)
    if not no_review and findings is None:
        # A reviewer ran and its triage reached no flag: the row lands with
        # three blanks that read as "counts nobody passed", which is exactly
        # what happened. Said once, on stderr, because the row is still worth
        # writing and the merge is still worth landing (§1 → `ledger.md`).
        print(f"aide merge: [loop] review is on and no --findings was passed, "
              f"so item {args.number:03d}'s row records no finding counts. "
              f"The row is still written; pass "
              f"'--findings {','.join(r + '=N' for r in LEDGER_FINDING_RANKS)}' "
              f"from the role that triaged them to record what the review "
              f"cost.", file=sys.stderr)
    pending_row: Optional[List[str]] = None
    try:
        pending_row = ledger_cells(
            repo_root, config, args.number, "merged",
            rounds=getattr(args, "rounds", None),
            findings=findings,
            branch=branch, base=main, no_review=no_review)
    except (OSError, UnicodeDecodeError, subprocess.SubprocessError) as exc:
        print(f"aide merge: the ledger row could not be derived "
              f"({type(exc).__name__}: {exc}), so item {args.number:03d} "
              f"will land with no row in the ledger", file=sys.stderr)

    git(["switch", main], repo_root)

    # Already an ancestor? Then the merge is not the missing step, and doing it
    # again can only churn. This is the case that bit a consumer: a conflict
    # resolved by hand left a merge commit on the base that had not been
    # pushed, and the re-run's `pull --rebase` linearised it — dropping the
    # merge, replaying both parents, and reintroducing the very conflict the
    # human had just resolved (issue #133). Asking git first costs one call and
    # is what makes the verb re-runnable, which a loop needs it to be.
    landed = git(["merge-base", "--is-ancestor", branch, main],
                 repo_root, check=False).returncode == 0
    if landed:
        print(f"aide merge: {branch} is already merged into {main} — skipping "
              f"the merge; the tick, the push and the cleanup still run.")
    else:
        if mode != "local":
            # `--rebase` is right for a linear local divergence and WRONG over
            # an unpushed merge commit (above). `--ff-only` integrates origin
            # where it can and refuses instead of rewriting where it cannot.
            if _has_unpushed_merge(repo_root):
                ff = git(["pull", "--ff-only"], repo_root, check=False)
                if ff.returncode != 0:
                    print(f"aide merge: {main} carries a merge commit origin "
                          f"has not seen, and origin has moved on. Rebasing "
                          f"over it would linearise the merge and bring back "
                          f"the conflicts it resolved, so this verb stops "
                          f"rather than choosing for you: push that merge "
                          f"('git push'), or integrate origin by hand, then "
                          f"re-run.\n{ff.stdout}{ff.stderr}", file=sys.stderr)
                    return 1
            else:
                pulled = git(["pull", "--rebase"], repo_root, check=False)
                stalled = _stalled_pull(repo_root, config, pulled)
                if stalled is not None:
                    # The sharpest of the three: `git merge` refuses outright
                    # while a rebase is in progress, so without this the
                    # operator reads the MERGE's failure for a stall the pull
                    # caused, on a base branch that is now mid-rebase.
                    print(f"aide merge: {stalled}\n"
                          f"aide merge: nothing was merged and item "
                          f"{args.number:03d} is NOT ticked — the work is "
                          f"intact on {branch}. Re-run once {main} is settled.",
                          file=sys.stderr)
                    return 1
        merge_res = git(["merge", "--no-edit", branch], repo_root, check=False)
        if merge_res.returncode != 0:
            # The one conflict this loop produces as a matter of course gets
            # named here rather than left in git's output, because this is
            # where it lands and the role standing here has read nothing about
            # the inbox.
            hint = _inbox_conflict_hint(repo_root, config)
            print(f"aide merge: merge of {branch} failed:\n"
                  f"{merge_res.stdout}{merge_res.stderr}"
                  + (f"\naide merge: {hint}\n" if hint else ""),
                  file=sys.stderr)
            return 1

    # The claim branch goes BEFORE the test run, so the run sees the refs a
    # fresh clone would (issue #125). With it still present, a consumer whose
    # test command includes `aide check` got "stale claim branch … item NNN is
    # already ✅" — a failure class the item's acceptance baseline had never
    # seen, produced by nothing but this ordering. Its tip is remembered so any
    # later exit can put the branch back exactly as it was — with the base
    # this run merged into as its record, since `branch -d` discards the old
    # one with the ref and a retry must land where this run did (issue #167).
    branch_tip = git(["rev-parse", branch], repo_root, check=False).stdout.strip()
    branch_base = main
    # `-d` can refuse even though the work landed (e.g. `pull --rebase` rewrote
    # main so the branch tip is no longer an ancestor); this process just
    # established that the branch is merged, so escalating to -D is safe. VERIFY
    # the outcome, never assume it.
    del_res = git(["branch", "-d", branch], repo_root, check=False)
    if del_res.returncode != 0:
        del_res = git(["branch", "-D", branch], repo_root, check=False)
    local_gone = branch not in _local_branches(repo_root)

    # Every exit from here to the push must put the branch back, not just the
    # two this function writes out longhand: the window covers a whole test
    # suite, and a run killed inside it (Ctrl-C, a CI timeout, an unattended
    # runner's wall clock) left the item merged into its base with the claim
    # branch gone and nothing to say where it had been. The next run's
    # `resolve_base` then fell back to `main_branch` and a consumer's queue was
    # fast-forwarded onto `main` and pushed, past its one-reviewed-PR-per-queue
    # gate (issue #174). The `except` arm is what covers the killed run; the
    # two explicit calls inside stay, because each carries a message about the
    # specific failure it is reporting.
    #
    # It ends at the push on purpose. Past that the merge has left this
    # repository and the retry has nothing left to do, so putting the branch
    # back would leave a stale claim branch behind a ✅ item — the very state
    # deleting it before the tests avoids.
    with _restore_on_signal():
        try:
            if not args.no_test:
                cmd = resolve_test_command(repo_root, config)
                test_res = subprocess.run(cmd, cwd=str(repo_root))
                if test_res.returncode != 0:
                    _restore_claim_branch(repo_root, branch, branch_tip, branch_base)
                    print(f"aide merge: the post-merge test run FAILED, so item "
                          f"{args.number:03d} is NOT ✅ and nothing was pushed — the "
                          f"tick and the push are what this run refuses, not the merge "
                          f"itself. {branch} is merged into {main} in THIS repository "
                          f"only, and the claim branch is back with its base. Fix the "
                          f"failures on {main}, commit, then re-run "
                          f"'merge {args.number:03d} --base {main}': the merge is "
                          f"already an ancestor, so the retry only re-tests, ticks and "
                          f"pushes.", file=sys.stderr)
                    return 1

            # The document gate, beside the test run and refusing the same two
            # things: the tick and the push, so the item stays 🔍. Nothing else
            # in the loop ran `aide check` mechanically — a consumer's ✅ stage
            # over ⏸️ deliverables sat on its base for two weeks until an
            # engine update surfaced it, and one without its own test pinning
            # `run_checks` would never have seen it (issue #232). In-process,
            # and not skipped by --no-test: it is not the project's tests.
            doc_errors, doc_warnings = run_checks(repo_root, config)
            if doc_errors:
                _restore_claim_branch(repo_root, branch, branch_tip, branch_base)
                listed = "".join(f"\nerror: {e}" for e in doc_errors)
                print(f"aide merge: `aide check` reports {len(doc_errors)} "
                      f"error(s) after the merge, so item {args.number:03d} "
                      f"is NOT ✅ and nothing was pushed. {branch} is merged "
                      f"into {main} in THIS repository only, and the claim "
                      f"branch is back with its base. The check reads the "
                      f"whole document set, so an error may predate this "
                      f"item. Fix the documents on {main}, commit, then re-run "
                      f"'merge {args.number:03d} --base {main}'.{listed}",
                      file=sys.stderr)
                return 1
            if doc_warnings:
                print(f"aide merge: `aide check` reports {len(doc_warnings)} "
                      f"warning(s), which do not block a merge; "
                      f"'python .aide/scripts/aide.py check' lists them.")

            # ✅ is set HERE, by the process that just did the merge, so it always means
            # "merged" — not "an agent said so before attempting one". The validator
            # marks the item 🔍 before this call; whether it becomes ✅ is a fact about
            # git, and in `pr` mode the return above leaves it 🔍 for the human's merge.
            #
            # It must precede the push: the tick is a commit like any other, and the
            # single `git push` below is the only one that carries `main` to origin.
            # Recording it afterwards stranded it locally, so origin's progress.md
            # under-reported — and on a queue's last item nothing would ever push it.
            # Beside the tick and in the same commit as it: one item, one
            # row, whatever it took to get there (§1 → `ledger.md`). A ledger
            # write that fails is a warning after the merge and never an exit
            # code — capture is worth a sentence, never a landed item.
            ledger_rel = None
            if pending_row is not None:
                try:
                    ledger_rel = append_ledger_row(repo_root, config,
                                                   pending_row, "merge")
                except (OSError, UnicodeDecodeError) as exc:
                    print(f"aide merge: item {args.number:03d} merged, but its "
                          f"ledger row could not be written "
                          f"({type(exc).__name__}: {exc})", file=sys.stderr)
            _promote_item_to_complete(repo_root, config, args.number,
                                      getattr(args, "no_commit", False),
                                      (ledger_rel,) if ledger_rel else ())

            remote_gone = True
            if mode != "local":
                push_res = git(["push"], repo_root, check=False)
                if push_res.returncode != 0:
                    # Reported, not swallowed: a silent failure here leaves ✅ on a
                    # merge origin never received, which is the same class of lie as
                    # ticking an item whose tests fail. The remote claim branch is
                    # deliberately NOT deleted, so the work still exists somewhere
                    # other than this checkout.
                    _restore_claim_branch(repo_root, branch, branch_tip, branch_base)
                    print(f"aide merge: item {args.number:03d} is merged and ✅ here, "
                          f"but pushing {main} to origin FAILED, so neither the merge "
                          f"nor the tick has left this repository and the claim branch "
                          f"is kept, with its base. Resolve the push, then re-run "
                          f"'merge {args.number:03d} --base {main}'.\n"
                          f"{push_res.stdout}{push_res.stderr}", file=sys.stderr)
                    return 1
                del_remote = git(["push", "origin", "--delete", branch], repo_root, check=False)
                remote_gone = (del_remote.returncode == 0
                               or "remote ref does not exist" in (del_remote.stderr or ""))
        except BaseException as exc:
            # BaseException, so `KeyboardInterrupt` and `_Terminated` are caught
            # alongside an ordinary bug. Nothing is swallowed: the restore is a
            # side effect on the way out and the original exception continues to
            # unwind, so an interrupted run still exits as interrupted.
            #
            # The restore is owed either way; the WORDING is not. A test
            # command that is not on PATH raises `FileNotFoundError` here, and
            # a run that reported itself "interrupted" would send a human
            # hunting for a signal nobody sent — the same failure the
            # `--no-commit` message was fixed for in issue #133. So the cause
            # is named, and the traceback that follows says the rest.
            _restore_claim_branch(repo_root, branch, branch_tip, branch_base)
            cause = ("interrupted"
                     if isinstance(exc, (KeyboardInterrupt, _Terminated))
                     else f"failed with {type(exc).__name__}")
            print(f"aide merge: {cause} after {main} took the merge of "
                  f"{branch} but before it was pushed, so {branch} has been "
                  f"put back with {main} recorded as its base. The merge is "
                  f"in THIS repository only. Re-run "
                  f"'merge {args.number:03d} --base {main}'.", file=sys.stderr)
            raise

    if local_gone and remote_gone:
        print(f"aide merge: item {args.number:03d} merged to {main} and claim branch {branch} deleted")
    else:
        where = [] if local_gone else ["local"]
        if not remote_gone:
            where.append("remote")
        print(f"aide merge: item {args.number:03d} merged to {main}, but the "
              f"{'/'.join(where)} claim branch {branch} could NOT be deleted:\n"
              f"{(del_res.stderr or '').strip()}\n"
              f"Run 'python .aide/scripts/aide.py gc' to sweep it up.", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------- #
# sync / gc — the scripted git workflow (no exploratory git needed)
# --------------------------------------------------------------------------- #
def _local_branches(repo_root: Path) -> List[str]:
    out = git(["branch", "--format=%(refname:short)"], repo_root, check=False).stdout
    return [l.strip() for l in out.splitlines() if l.strip()]


def _remote_branches(repo_root: Path) -> List[str]:
    out = git(["branch", "-r", "--format=%(refname:short)"], repo_root, check=False).stdout
    names = []
    for l in out.splitlines():
        name = l.strip()
        if name.startswith("origin/") and "HEAD" not in name:
            names.append(name.split("/", 1)[1])
    return names


def _unpublished_branches(repo_root: Path, config, prefix: str) -> List[str]:
    """Branches under *prefix* that this checkout has and origin has not.

    Read against the remote-tracking refs, so it reports what the last fetch
    saw — `claim` fetches first and `status` does too unless asked not to.

    No origin at all is deliberately *not* an exemption. Off ``local`` mode
    the engine pushes every branch it creates, so a repository with no remote
    fails every push; issue #137's own reproduction is exactly that, and a
    claim branch there is unpublished in the strongest sense — there is
    nowhere for it to have gone. ``local`` mode is the one configuration where
    an unpushed claim branch is the design rather than a failure.
    """
    if str(config["git"].get("mode", "auto-merge")) == "local":
        return []
    remote = set(_remote_branches(repo_root))
    out = [line.strip() for line
           in git(["branch", "--format=%(refname:short)"],
                  repo_root, check=False).stdout.splitlines()]
    return sorted(br for br in out if br.startswith(prefix) and br not in remote)


def _unpublished_claim_branches(repo_root: Path, config,
                                prefix: str) -> Dict[int, str]:
    """Item number -> a claim branch this checkout has that origin has not.

    Off ``local`` mode a claim is published by construction: `claim` creates
    the branch and pushes it in the same breath, and refuses out loud when the
    push does not land. So a claim branch origin has never seen is a claim
    that did not finish — visible here, invisible to every other checkout, and
    counted as a claim by `_pick_item` regardless. That is the half-claim of
    issue #137, and naming it is what stops it reading as work in flight.

    ``local`` mode is the one configuration that reports nothing: there, an
    unpushed claim branch is the design. A repository with no origin at all is
    *not* an exemption — see `_unpublished_branches`, which this narrows.
    """
    out: Dict[int, str] = {}
    for br in _unpublished_branches(repo_root, config, prefix):
        num = _branch_item_number(br, prefix)
        if num is not None:
            out.setdefault(num, br)
    return out


def _branch_item_number(branch: str, prefix: str) -> Optional[int]:
    """Item number claimed by *branch*, or None when it is not a claim branch.

    A claim branch is ``<branch_prefix>NNN-short-name`` (conventions.md §4), so
    the number must sit *immediately* after the prefix. Anchoring is what makes
    this correct: queue numbers and item numbers share one namespace with no
    syntactic marker between them, so an unanchored digit search reads
    ``aide/queue-016`` as item 016 — an unrelated, usually long-finished work
    item — and ``aide/specs-queue-015`` likewise.

    That misread is not cosmetic. ``gc`` targets any branch whose item is ✅ and
    deletes it with ``git branch -D`` plus a remote delete, independently of
    ``--merged``; under the old unanchored match that destroyed an in-flight
    queue branch, and the unreviewed queue file and item specs living only on it.
    """
    m = re.match(re.escape(prefix) + r"0*(\d+)(?:-|$)", branch)
    return int(m.group(1)) if m else None


#: Branches the framework itself tells authors to create that are deliberately
#: NOT item claims: `/aide-create-queue`'s hand-off and `/aide-run-roadmap` name
#: `<prefix>queue-NNN`, `/aide-spec-queue` names `<prefix>specs-queue-NNN`.
#: Recognised positively so they are reported as what they are, rather than
#: lumped in with a branch nothing can parse.
#:
#: Built from `_QUEUE_TOKEN`/`_SPECS_TOKEN` — the same literals the constructors
#: below and `queue_name` use — so the recogniser cannot drift from the names
#: actually produced. 1.13.0 centralised branch *parsing*; until 1.20.0 two of
#: the three shapes had no constructor at all and were typed by an agent copying
#: a string out of a markdown file, which is why the round-trip test that now
#: pins this could not previously be written.
_QUEUE_BRANCH_RE = re.compile(
    "(?:" + re.escape(_SPECS_TOKEN) + ")?" + re.escape(_QUEUE_TOKEN) + r"\d+$")


def claim_branch_name(prefix: str, number: int, title: str) -> str:
    """``<prefix>NNN-short-name`` — the branch `aide claim` creates for an item."""
    return f"{prefix}{number:03d}-{_slug(title)}"


def queue_branch_name(prefix: str, number: int) -> str:
    """``<prefix>queue-NNN`` — the branch a queue is planned and run on."""
    return f"{prefix}{queue_name(number)}"


def specs_queue_branch_name(prefix: str, number: int) -> str:
    """``<prefix>specs-queue-NNN`` — the branch a queue's specs are authored on."""
    return f"{prefix}{_SPECS_TOKEN}{queue_name(number)}"


def _is_queue_branch(branch: str, prefix: str) -> bool:
    """True when *branch* is a queue/specs-queue branch rather than a claim."""
    return (branch.startswith(prefix)
            and _QUEUE_BRANCH_RE.match(branch[len(prefix):]) is not None)


def _has_origin(repo_root: Path) -> bool:
    out = git(["remote"], repo_root, check=False).stdout
    return "origin" in out.split()


# --------------------------------------------------------------------------- #
# Base refs — what a claim branched from, and what its merge returns to
# --------------------------------------------------------------------------- #
#: Where a claim branch remembers its base. A git-config key under the branch's
#: own section, so it travels with the branch through switch/rebase and needs no
#: file in the repo. It is deliberately *local* config: the base is a fact about
#: this checkout's branching, not something to commit and share. A machine that
#: never ran the `claim` falls back to `main_branch`, and `--base` is always
#: available — nothing silently merges somewhere unexpected.
_BASE_CONFIG_KEY = "aide-base"


def _record_branch_base(repo_root: Path, branch: str, base: str) -> None:
    git(["config", f"branch.{branch}.{_BASE_CONFIG_KEY}", base],
        repo_root, check=False)


def _recorded_branch_base(repo_root: Path, branch: str) -> Optional[str]:
    if not branch:
        return None
    res = git(["config", "--get", f"branch.{branch}.{_BASE_CONFIG_KEY}"],
              repo_root, check=False)
    value = res.stdout.strip()
    return value or None


def _current_branch(repo_root: Path) -> str:
    return git(["rev-parse", "--abbrev-ref", "HEAD"],
               repo_root, check=False).stdout.strip()


def _ref_exists(repo_root: Path, ref: str) -> bool:
    return git(["rev-parse", "--verify", "--quiet", ref],
               repo_root, check=False).returncode == 0


def _local_branch_exists(repo_root: Path, ref: str) -> bool:
    """True only for an existing **local branch**, not any resolvable ref.

    A base must be a local branch, and merely resolving is not enough: `git
    switch` on a tag, a raw commit or a remote-tracking ref like `origin/main`
    detaches HEAD. A merge into a detached HEAD updates no branch at all, yet
    still reports success and lets the claim branch be deleted — the work
    survives only as an unreferenced commit. So the check is on the ref's
    *kind*, not its existence.
    """
    return git(["show-ref", "--verify", "--quiet", f"refs/heads/{ref}"],
               repo_root, check=False).returncode == 0


def _remote_or_local(repo_root: Path, ref: str) -> str:
    """``origin/<ref>`` when it resolves, else *ref* unchanged.

    Used where the question is "what has this branch actually diverged from" —
    the remote-tracking ref is what CI compares against and what the branch will
    merge into, and a local ref sitting behind the work answers that wrongly.
    """
    if _has_origin(repo_root):
        remote = f"origin/{ref}"
        if _ref_exists(repo_root, remote):
            return remote
    return ref


def resolve_base(repo_root: Path, config: Dict[str, Dict[str, object]],
                 explicit: Optional[str] = None,
                 branch: Optional[str] = None) -> str:
    """The base ref for a branch: explicit ``--base`` > recorded > config.

    ``main_branch`` stays the default and is never removed as one — this only
    adds the two ways a branch can legitimately have a *different* base, which
    is what stacked work produces: a queue branch's items branch off it and must
    merge back into it, so the whole queue lands as one reviewed PR.
    """
    if explicit:
        return explicit
    if branch is None:
        branch = _current_branch(repo_root)
    recorded = _recorded_branch_base(repo_root, branch)
    if recorded:
        return recorded
    return str(config["git"].get("main_branch", "main"))


# --------------------------------------------------------------------------- #
# Scope check — a branch's diff against its item's `## Authorised paths`
# --------------------------------------------------------------------------- #
_AUTHORISED_HEADING = "## Authorised paths"
#: The two sub-lists of that section (conventions.md §1), matched case- and
#: punctuation-insensitively so `**May change:**`, `**May change**` and
#: `May change:` all read the same.
_MAY_CHANGE_LABEL = "may change"
_ASSERTS_LABEL = "asserts against"

#: Loop bookkeeping the `aide` CLI and the agent roles are mandated to write on
#: *any* item, whatever that item is about — so a change to one is never
#: evidence of scope creep, and listing them would force every spec to repeat
#: the same boilerplate bullets just to pass. Kept explicit and wildcard-free so
#: the set cannot silently grow into a scope hole:
#:
#: - ``progress.md`` — rewritten by ``aide progress set`` on every item.
#: - ``insights.md`` — the compound-engineering inbox; conventions.md §1 names
#:   appending to it as the one write allowed outside an agent's edit scope, so
#:   flagging it would punish exactly the behaviour the framework requires.
#: - ``insights/archive-*.md`` — where ``aide insights archive`` moves closed
#:   entries. The one pattern here, added deliberately rather than by widening
#:   the rule: it is bounded to a single directory *and* a single filename
#:   shape, and ``path_matches`` anchors a bare ``*`` per path segment, so it
#:   cannot reach a subdirectory or a second name. It buys nothing an attacker
#:   or a careless agent wants — only the file the verb above it writes.
#:
#: The item's own spec is authorised separately, by number, in ``cmd_scope`` —
#: the builder records Decisions & Trade-offs there on every item.
_ALWAYS_AUTHORISED = ("progress.md", "insights.md", "insights/archive-*.md")


def _always_authorised_paths(ddir_rel: str) -> Tuple[str, ...]:
    """The always-authorised names as repo-relative patterns, the spelling item
    specs use. One joiner for the three enforcement sites — the pin lint in
    `item_spec_warnings`, the overlap exclusion in `queue_spec_findings`, and
    `cmd_scope` — so what counts as loop bookkeeping cannot drift between
    them."""
    return tuple(f"{ddir_rel}/{name}" for name in _ALWAYS_AUTHORISED)


class AuthorisedPaths(NamedTuple):
    """The two lists of an item spec's ``## Authorised paths`` section."""

    may_change: List[str]
    asserts_against: List[str]


def _strip_dot_slash(path: str) -> str:
    """Drop a leading ``./``, and only that.

    Never ``lstrip("./")``, which strips leading *characters* from that set and
    so silently renames the dotfiles specs routinely authorise —
    ``.gitattributes`` to ``gitattributes``, ``.github/workflows/ci.yml`` to
    ``github/workflows/ci.yml`` — turning a declared path into one that matches
    nothing git ever reports.
    """
    while path.startswith("./"):
        path = path[2:]
    return path


def _sub_list_label(line: str) -> Optional[str]:
    """The normalised sub-list label on *line*, or None if it is not one."""
    text = line.strip().strip("*_").strip().rstrip(":").strip().lower()
    if text == _MAY_CHANGE_LABEL:
        return _MAY_CHANGE_LABEL
    if text == _ASSERTS_LABEL:
        return _ASSERTS_LABEL
    return None


def _bullet_path(line: str) -> Optional[str]:
    """The repo-relative path a section bullet declares, or None.

    A bullet is ``- `path` — why``: the path is the FIRST backtick span, never
    the whole body, because the reason that follows it is prose. Falls back to
    the text before the first dash/colon separator for a bullet written without
    backticks. Returns None for a bullet that declares no path — an unfilled
    ``{{slot}}`` (``aide check`` already errors on those, so failing here as
    well would report one authoring slip twice) or a literal "None."
    """
    stripped = line.strip()
    if not stripped or stripped[0] not in "-*+":
        return None
    body = stripped[1:].strip()
    if not body or "{{" in body:
        return None
    m = re.search(r"`([^`]+)`", body)
    if m:
        candidate = m.group(1)
    else:
        candidate = _BULLET_REASON_RE.split(body, maxsplit=1)[0]
    candidate = candidate.strip().strip("`").strip()
    if not candidate or candidate.rstrip(".").lower() == "none":
        return None
    return _strip_dot_slash(candidate)


#: Every backtick span on a line, and where a bullet's reason starts. The two
#: together locate the bullet's PATH POSITION — the run before the reason
#: separator — which is the only place a span is a path claim. `_bullet_path`
#: splits on the same separator for a bullet written without backticks, so the
#: two readings of "where the path ends" cannot drift apart.
_BACKTICK_SPAN_RE = re.compile(r"`([^`]+)`")
#: The dash may END the line — `- `path` —` with the reason wrapped below is a
#: common way to write a long one, and reading it as "no reason yet" would take
#: the whole reason for more path position.
_BULLET_REASON_RE = re.compile(r"\s+[—–-](?:\s+|$)|:")

#: A Markdown list marker, which `_bullet_path` tests only by its first
#: character. The lint needs the stricter form: a continuation line opening
#: `**not** in the project group …` is emphasis, not a bullet, and reading it
#: as one attributes the reason's own spans to a path it invented. The parser
#: is left alone — its looser test yields a junk pattern that matches no file,
#: while a lint that reports MORE than the parser reads is a lint nobody
#: believes twice.
_LIST_MARKER_RE = re.compile(r"[-*+]\s")


def _authorised_section_lines(text: str) -> Optional[List[str]]:
    """The lines under ``## Authorised paths``, or None when it is absent.

    One slicer for the parser and the spec-time lint below, so the lint cannot
    warn about a bullet the parser never looked at, or stay silent about one it
    did — the whole point of the warning is to describe what `aide scope` will
    actually do with the section.
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == _AUTHORISED_HEADING:
            start = i + 1
            break
    if start is None:
        return None

    end = len(lines)
    for i in range(start, len(lines)):
        if _ANY_HEADER_RE.match(lines[i]) and lines[i].strip() != _AUTHORISED_HEADING:
            end = i
            break
    return lines[start:end]


def _path_position(line: str) -> Tuple[str, bool]:
    """The run of *line* before its reason separator, and whether one was seen.

    Everything after the separator is the reason, and a bullet is required to
    carry one — so a backticked name there is prose about the work, not a path
    claim. Measured on two real consumers, treating it as a path claim produced
    82 and 224 findings, almost all of them identifiers and TOML keys quoted in
    reasons; the spec that *reported* issue #119 would have raised six.
    """
    m = _BULLET_REASON_RE.search(line)
    return (line[: m.start()], True) if m else (line, False)


def dropped_bullet_spans(text: str) -> List[Tuple[str, List[str]]]:
    """``(path read, spans dropped)`` for each over-full Authorised-paths bullet.

    The contract is one path per bullet (conventions.md §1 → authorised-paths),
    and until issue #119 the two ways to break it were both silent: a bullet
    listing several comma-separated `` `path` `` spans authorised only the
    first, and a path list wrapped onto a continuation line lost everything
    below the first line, since the parser only ever inspects bullet lines. The
    narrowing surfaced much later as an `aide scope` FAIL naming paths the
    spec's own prose plainly authorised — three of one item's four bullets had
    that shape.

    Only the **path position** is read: the bullet's opening line up to its
    reason separator, plus the continuation lines while no separator has been
    seen yet, which is exactly the wrapped-list shape. That limit is what makes
    the lint worth reading rather than a source of noise to page past, and it
    is a limit: a path named after the separator is not distinguishable from a
    reason that mentions a file, so a second path written there stays silent.
    The bullet is closed by a blank line, a sub-list label, or the next bullet
    — the same shape a Markdown reader sees, so an author can predict what the
    lint attributes where.

    Silently narrowing an authorisation is the worst of the three behaviours
    available, so what IS found is reported where it is authored. A *warning*,
    not an error: the bullet is legible to a human, existing specs carry the
    shape, and the remedy (split the bullet) is the author's to apply.
    """
    section = _authorised_section_lines(text)
    if section is None:
        return []
    found: List[Tuple[str, List[str]]] = []
    open_bullet: Optional[Tuple[str, List[str]]] = None
    for line in section:
        stripped = line.strip()
        if not stripped or _sub_list_label(line) is not None:
            open_bullet = None
            continue
        if _LIST_MARKER_RE.match(stripped):
            open_bullet = None
            path = _bullet_path(line)
            # A bullet the parser declines — an unfilled `{{slot}}`, a literal
            # "None." — is somebody else's finding (`aide check` errors on the
            # slot), and nothing under it was going to be read anyway.
            if path is None:
                continue
            head, reason = _path_position(stripped[1:].strip())
            entry = (path, _BACKTICK_SPAN_RE.findall(head)[1:])
            found.append(entry)
            if not reason:
                open_bullet = entry
        elif open_bullet is not None:
            head, reason = _path_position(line)
            open_bullet[1].extend(_BACKTICK_SPAN_RE.findall(head))
            if reason:
                open_bullet = None
    return [(path, dropped) for path, dropped in found if dropped]


def declares_nothing(parsed: Optional[AuthorisedPaths]) -> bool:
    """True when a spec's scope cannot be compared with anything.

    An **empty May change is not the same as nothing declared**: a
    stage-validation item legitimately changes only the loop bookkeeping every
    item may write, while still pinning the tree it validates under *Asserts
    against*. Treating that as undeclared would drop exactly the specs whose
    whole purpose is to assert — so the test is that *both* lists are empty.
    """
    return parsed is None or not (parsed.may_change or parsed.asserts_against)


def parse_authorised_paths(text: str) -> Optional[AuthorisedPaths]:
    """Parse an item spec's ``## Authorised paths`` section.

    Returns None when the section is absent — distinct from a present-but-empty
    section (``AuthorisedPaths([], [])``), because the two need different
    remedies and neither may be read as "unconstrained" (conventions.md §1).

    Bullets appearing before either sub-list label are read as **May change**,
    which is what makes the flat single-list form — the shape consumers wrote
    before the labels existed — parse correctly rather than silently empty.
    """
    section = _authorised_section_lines(text)
    if section is None:
        return None

    may_change: List[str] = []
    asserts_against: List[str] = []
    current = may_change
    for line in section:
        label = _sub_list_label(line)
        if label is not None:
            current = may_change if label == _MAY_CHANGE_LABEL else asserts_against
            continue
        path = _bullet_path(line)
        if path is not None:
            current.append(path)
    return AuthorisedPaths(may_change, asserts_against)


def path_matches(changed: str, pattern: str) -> bool:
    """True when repo-relative *changed* is covered by *pattern*.

    Three forms, per conventions.md §1:

    - ``dir/**`` — the directory and anything at any depth below it.
    - any other pattern containing ``*``, ``?`` or ``[`` — an ordinary shell
      glob matched **per path segment**, so ``tests/golden/*.json`` covers a
      JSON file in that directory but not one a level deeper. Anchoring per
      segment is the point: ``fnmatch``'s ``*`` crosses ``/`` and would quietly
      widen every glob a spec writes into a subtree wildcard.
    - anything else — an exact path.
    """
    pattern = _strip_dot_slash(pattern.strip())
    if pattern.endswith("/**"):
        prefix = pattern[: -len("/**")]
        return changed == prefix or changed.startswith(prefix + "/")
    if any(ch in pattern for ch in "*?["):
        pat_parts = pattern.split("/")
        path_parts = changed.split("/")
        if len(pat_parts) != len(path_parts):
            return False
        return all(fnmatch.fnmatchcase(p, g) for p, g in zip(path_parts, pat_parts))
    return changed == pattern


def scope_findings(changed: List[str], authorised: AuthorisedPaths,
                   always: Tuple[str, ...] = ()) -> Tuple[List[str], List[str]]:
    """``(unauthorised, contradictions)`` for a branch's *changed* paths.

    A contradiction is a path the spec declared under **Asserts against** — "my
    tests pin this without changing it" — and then changed anyway. It is
    reported separately from an unauthorised path because the remedy differs:
    one widens a list, the other means an assertion in this very item is now
    asserting against state the item moved.
    """
    unauthorised = [p for p in changed
                    if not any(path_matches(p, a) for a in always)
                    and not any(path_matches(p, g) for g in authorised.may_change)]
    contradictions = [p for p in changed
                      if any(path_matches(p, g) for g in authorised.asserts_against)]
    return unauthorised, contradictions


#: `AC3`, `ac3` — the criterion number a test name carries. Not `mac3` or
#: `ac30` for AC3: the token is bounded on both sides.
_AC_TOKEN_RE = re.compile(r"(?<![a-z0-9])ac(\d+)(?![0-9])")
_AC_HEADING_RE = re.compile(r"^##\s+Acceptance Criteria\b", re.MULTILINE | re.IGNORECASE)
_TESTING_HEADING_RE = re.compile(r"^##\s+Testing Strategy\b", re.MULTILINE | re.IGNORECASE)
#: A case label: the first token of a Testing Strategy **bullet**, closed by a
#: colon — `- empty-input: the walker yields nothing`, with or without
#: backticks or bold around the token. One word, so "existing tests to
#: reconcile:" and a `tests/test_x.py:` module name are prose, not labels;
#: and a bullet, so a prose "Note: …" line in the section is not one either
#: (a generic label would silence every test whose name contains it).
_CASE_LABEL_RE = re.compile(r"^\s*[-*]\s+[`*_]*([A-Za-z][A-Za-z0-9_-]*)[`*_]*\s*:")


_FENCE_RE = re.compile(r"^[ \t]*(```|~~~).*?^[ \t]*\1[^\n]*$", re.MULTILINE | re.DOTALL)


def _section_text(text: str, heading: "re.Pattern") -> str:
    """The body under *heading*, up to the next `## `, with every fenced block
    inside that slice removed — a fence is code, not a bullet list. The slice
    is cut first, so a fence left open in an earlier section cannot swallow
    this one."""
    m = heading.search(text)
    if m is None:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s", rest, re.MULTILINE)
    section = rest if nxt is None else rest[: nxt.start()]
    return _FENCE_RE.sub("", section)


def spec_acceptance_numbers(text: str) -> List[int]:
    """The criterion numbers a spec's ``## Acceptance Criteria`` names."""
    return sorted({int(n) for n in re.findall(r"\bAC(\d+)\b",
                                             _section_text(text, _AC_HEADING_RE))})


def testing_strategy_labels(text: str) -> List[str]:
    """The case labels a spec's ``## Testing Strategy`` names, in order."""
    out: List[str] = []
    for line in _section_text(text, _TESTING_HEADING_RE).splitlines():
        m = _CASE_LABEL_RE.match(line)
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def _test_function_names(source: str) -> List[str]:
    try:
        tree = ast.parse(source.lstrip("\ufeff"))
    except SyntaxError:
        return []
    return [n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name.startswith("test")]


def _under_dir(rel: str, directory: str) -> bool:
    """*rel* (a posix path git printed) sits under *directory* (whatever
    `aide.toml` spelled: `tests`, `./tests`, `tests\\unit`, `.`)."""
    root = tuple(p for p in PurePosixPath(directory.replace("\\", "/")).parts
                 if p not in (".", ""))
    return PurePosixPath(rel).parts[: len(root)] == root


def _tests_dir_rel(repo_root: Path, config) -> Optional[str]:
    """`tests_dir` as a path relative to the repo, whatever `aide.toml`
    spelled; None when an absolute value points outside the repository, where
    no git-relative path can match it."""
    raw = str(config["project"].get("tests_dir", "tests"))
    path = Path(raw)
    if not path.is_absolute():
        return raw
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return None


def renamed_paths(repo_root: Path, merge_base: str) -> Dict[str, str]:
    """``{new path: old path}`` for every rename git detects vs *merge_base*."""
    # `core.quotePath=false`: with the default, a non-ASCII OLD path comes back
    # quoted and octal-escaped, and `git show <mb>:"…"` then finds nothing.
    status = git(["-c", "core.quotePath=false", "diff", "--name-status", "-M",
                  merge_base], repo_root, check=False)
    out: Dict[str, str] = {}
    if status.returncode != 0:
        return out
    for line in status.stdout.splitlines():
        cells = line.split("\t")
        if len(cells) == 3 and cells[0][:1] in ("R", "C"):
            out[cells[2].strip()] = cells[1].strip()
    return out


def added_test_functions(repo_root: Path, config, changed: List[str],
                         merge_base: str,
                         renamed: Optional[Dict[str, str]] = None,
                         ref: Optional[str] = None) -> List[Tuple[str, str]]:
    """``(path, name)`` for every test function the branch added.

    A test file among *changed* is read from the working tree and compared to
    its version at *merge_base* — under its old name where *renamed* says the
    branch moved it; a name present in both is an edit to an existing test (a
    reconcile the spec listed, §6) and is not the item's own. A file that did
    not exist at the base contributes every test in it.

    *ref* reads the new side from a ref instead of the working tree, for a
    caller that must count a branch it is not standing on — `aide merge`
    writing a ledger row (§1 → `ledger.md`) is about to merge the branch and
    delete it, and a count that depended on the checkout would be a different
    number on either side of that. A path the ref does not carry contributes
    nothing, exactly as a path missing from the working tree does.
    """
    tests_dir = _tests_dir_rel(repo_root, config)
    renamed = renamed or {}
    out: List[Tuple[str, str]] = []
    if tests_dir is None:
        return out
    for rel in changed:
        if not rel.endswith(".py") or not _under_dir(rel, tests_dir):
            continue
        if ref is None:
            path = repo_root / rel
            if not path.is_file():
                continue
            try:
                new = _test_function_names(path.read_text(encoding=_ENCODING))
            except (OSError, UnicodeDecodeError):
                continue
        else:
            at_ref = git(["show", f"{ref}:{rel}"], repo_root, check=False)
            if at_ref.returncode != 0:
                continue
            new = _test_function_names(at_ref.stdout)
        shown = git(["show", f"{merge_base}:{renamed.get(rel, rel)}"], repo_root, check=False)
        old = set(_test_function_names(shown.stdout)) if shown.returncode == 0 else set()
        out.extend((rel, name) for name in new if name not in old)
    return out


def _traces_to(name: str, ac_numbers: List[int], labels: List[str]) -> bool:
    """*name* carries one of *ac_numbers* (`ac3`) or one of *labels*."""
    low = name.lower()
    if any(int(n) in set(ac_numbers) for n in _AC_TOKEN_RE.findall(low)):
        return True
    return any(lbl.lower().replace("-", "_") in low for lbl in labels)


def traceability_warnings(added: List[Tuple[str, str]], ac_numbers: List[int],
                          labels: List[str], rel_spec: str,
                          owner: Optional[int] = None) -> List[str]:
    """§6: a test the item adds names the criterion (`ac3`) or the Testing
    Strategy case it covers; one that names neither is a test nobody asked
    for. A warning, never a FAIL: the rule is new and a consumer lives with
    the report before it gates anything.

    *owner* is set when the tests sit in another item's test file and
    *rel_spec* is that item's spec (`split_reconciled_tests`), and the warning
    then says whose file it is — the branch carries it, the spec it is read
    against is not the one being scoped."""
    where = (f" — in item {owner:03d}'s test file, which this branch changed"
             if owner is not None else "")
    return [f"warning: {rel}::{name} names no AC number and no Testing "
            f"Strategy case of {rel_spec}{where} — a test the spec did not ask "
            f"for (conventions.md §6)"
            for rel, name in added if not _traces_to(name, ac_numbers, labels)]


#: `test_007_walker.py` — a test file named for the item that owns it. The
#: digits are confirmed against the spec filename's own zero-padding
#: (`_item_spec_glob`), so `test_7_x.py` and `test_0007_x.py` name no item,
#: exactly as `7-x.md` and `0007-x.md` name no spec (`item_spec_number`).
_OWNED_TEST_FILE_RE = re.compile(r"test_(\d+)_")


def owning_item(rel: str) -> Optional[int]:
    """The item number a test file's name says owns it, or None."""
    m = _OWNED_TEST_FILE_RE.match(PurePosixPath(rel).name)
    if not m:
        return None
    number = int(m.group(1))
    return number if f"{number:03d}" == m.group(1) else None


class ReconciledTests(NamedTuple):
    """The added tests in one other item's test files, split against its spec."""
    spec: str                          # that item's spec, repo-relative
    reconciled: List[Tuple[str, str]]  # traced to its criteria or cases
    untraced: List[Tuple[str, str]]    # traced to neither


def split_reconciled_tests(repo_root: Path, config,
                           added: List[Tuple[str, str]], number: int,
                           ) -> Tuple[List[Tuple[str, str]], Dict[int, ReconciledTests]]:
    """``(own, others)``: *added* split by the item whose test file each sits in.

    A test in ``test_NNN_…py`` for an item other than *number* was reconciled
    there by this branch — a rename or edit this item's spec prescribed — and
    its criterion number is that item's (§6). So it is traced against **that
    item's spec**, never *number*'s: tracing it against the scoped spec both
    reported a prescribed reconcile as unrequested and silently credited an
    ``ac2`` to whichever item happened to have an AC2 too (issue #262). The
    traced ones are ``others[N].reconciled``; the rest still name nothing
    anyone asked for and are ``others[N].untraced``.

    A file whose owner has no spec, one that cannot be read, or one with no
    ``## Acceptance Criteria`` heading is not resolved to that owner and
    stays in *own* — today's reading, against the scoped spec. An owner
    whose spec cannot be checked is not one to credit a test to, and staying
    in *own* keeps the test counted by the ledger and warned on by `scope`.
    `aide scope` and the ledger's tests-added cell both read this split, so
    the tests one reports as reconciled are exactly the ones the other does
    not count.
    """
    idir = docs_dir(repo_root, config) / "items"
    specs: Dict[int, Optional[Tuple[str, List[int], List[str]]]] = {}
    own: List[Tuple[str, str]] = []
    others: Dict[int, ReconciledTests] = {}
    for rel, name in added:
        owner = owning_item(rel)
        if owner is None or owner == number:
            own.append((rel, name))
            continue
        if owner not in specs:
            specs[owner] = None
            found = item_spec_paths(idir, owner)
            if found:
                try:
                    text = found[0].read_text(encoding=_ENCODING)
                except (OSError, UnicodeDecodeError):
                    text = ""
                if _AC_HEADING_RE.search(text):
                    specs[owner] = (found[0].relative_to(repo_root).as_posix(),
                                    spec_acceptance_numbers(text),
                                    testing_strategy_labels(text))
        if specs[owner] is None:
            own.append((rel, name))
            continue
        rel_spec, acs, labels = specs[owner]
        bucket = others.setdefault(owner, ReconciledTests(rel_spec, [], []))
        traced = _traces_to(name, acs, labels)
        (bucket.reconciled if traced else bucket.untraced).append((rel, name))
    return own, others


def _scope_base_ref(repo_root: Path, config, explicit: Optional[str]) -> str:
    """The ref ``scope`` diffs against: ``--base`` > the branch's recorded base
    > ``main_branch``.

    An explicit ``--base`` is used **verbatim** — the caller named a ref, so
    silently substituting ``origin/`` for it would make ``--base main`` mean
    something the caller did not write, and leave no way to ask for the local
    ref at all. The two *derived* answers do prefer their ``origin/``
    counterpart, since neither was chosen by anyone.

    The remote-tracking preference is the footgun this exists to avoid: on a
    checkout whose local ``main`` sits behind the work, the merge-base with it
    *is* it, so every file the earlier items touched gets reported against the
    current item's spec. Consulting the recorded base first is what makes the
    verb correct on stacked work — an item claimed from a queue branch has
    diverged from *that*, not from ``main``, and diffing against ``main`` would
    report every sibling item already merged into the queue.
    """
    if explicit:
        return explicit
    return _remote_or_local(repo_root, resolve_base(repo_root, config))


def cmd_scope(args: argparse.Namespace) -> int:
    """Check that this branch's changed files stay inside the item's spec.

    The diff-time counterpart to a byte-hash "scope fence": it asserts the
    claim the fence encoded — "item N changed only these files" — once, on the
    branch, instead of enshrining it as a suite assertion that outlives its
    truth and goes red the moment a later item is authorised to touch the
    pinned file (conventions.md §1).

    Exit 0 in scope · 1 something changed outside it · 2 could not check.
    """
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    prefix = str(config["git"].get("branch_prefix", "aide/"))

    number = args.number
    if number is None:
        branch = _current_branch(repo_root)
        if _is_queue_branch(branch, prefix):
            print(f"aide scope: {branch} is a queue branch, not an item claim — "
                  "per-item scope is checked on each claim branch as it merges "
                  "here, and a queue branch legitimately aggregates many items' "
                  "authorised paths. Nothing to check.")
            return 0
        number = _branch_item_number(branch, prefix)
        if number is None:
            print(f"aide scope: cannot tell which item to check — branch "
                  f"'{branch}' is not {prefix}NNN-short-name. Name the item "
                  f"explicitly: aide scope NNN", file=sys.stderr)
            return 2

    idir = docs_dir(repo_root, config) / "items"
    specs = item_spec_paths(idir, number)
    if not specs:
        print(f"aide scope: no spec for item {number:03d} under {idir}",
              file=sys.stderr)
        return 2
    spec = specs[0]
    rel_spec = spec.relative_to(repo_root).as_posix()

    spec_text = spec.read_text(encoding=_ENCODING)
    authorised = parse_authorised_paths(spec_text)
    if declares_nothing(authorised):
        what = ("has no '## Authorised paths' section" if authorised is None
                else "declares no path under '## Authorised paths'")
        print(f"aide scope: {rel_spec} {what} — cannot check scope. This is "
              "reported, never passed silently: an undeclared spec is not an "
              "unconstrained one. Add the section (see conventions.md §1) and "
              "re-run.", file=sys.stderr)
        return 2

    base = _scope_base_ref(repo_root, config, args.base)
    mb = git(["merge-base", base, "HEAD"], repo_root, check=False)
    if mb.returncode != 0:
        print(f"aide scope: could not resolve a merge-base with '{base}' — "
              f"{mb.stderr.strip()}", file=sys.stderr)
        return 2
    diff = git(["diff", "--name-only", mb.stdout.strip()], repo_root, check=False)
    if diff.returncode != 0:
        print(f"aide scope: git diff failed — {diff.stderr.strip()}",
              file=sys.stderr)
        return 2

    changed = [ln.strip() for ln in diff.stdout.splitlines() if ln.strip()]
    ddir_rel = docs_dir(repo_root, config).relative_to(repo_root).as_posix()
    always = _always_authorised_paths(ddir_rel) + (rel_spec,)
    unauthorised, contradictions = scope_findings(changed, authorised, always)

    traced: List[str] = []
    added = added_test_functions(repo_root, config, changed, mb.stdout.strip(),
                                 renamed_paths(repo_root, mb.stdout.strip()))
    own, others = split_reconciled_tests(repo_root, config, added, number)
    if _tests_dir_rel(repo_root, config) is None:
        print("notice: tests_dir lies outside the repository — traceability "
              "not checked")
    elif own and _AC_HEADING_RE.search(spec_text) is None:
        print(f"notice: {rel_spec} has no '## Acceptance Criteria' heading — "
              "traceability not checked")
    elif own:
        traced = traceability_warnings(
            own, spec_acceptance_numbers(spec_text),
            testing_strategy_labels(spec_text), rel_spec)
    for owner, split in sorted(others.items()):
        if split.reconciled:
            print(f"notice: reconciled {len(split.reconciled)} test(s) in item "
                  f"{owner:03d}'s test files ({split.spec})")
        traced += traceability_warnings(split.untraced, [], [], split.spec, owner)
    for line in traced:
        print(line)
    note = f", {len(traced)} traceability warning(s)" if traced else ""

    for path in contradictions:
        print(f"error: {path} changed, but {rel_spec} lists it under "
              "'Asserts against' as pinned-not-changed")
    for path in unauthorised:
        print(f"error: {path} not authorised by {rel_spec}")

    total = len(unauthorised) + len(contradictions)
    if total:
        print(f"aide scope: FAIL (item {number:03d}, {total} of {len(changed)} "
              f"changed file(s) outside scope, vs {base}{note})")
        return 1
    print(f"aide scope: OK (item {number:03d}, {len(changed)} changed file(s) "
          f"all authorised, vs {base}{note})")
    return 0


def _landed_review_items(repo_root: Path, config, prefix: str,
                         explicit: Optional[str] = None) -> List[str]:
    """Lines naming every 🔍 item whose branch has since landed in its base.

    Each claim is measured against its own base, resolved the way every other
    verb resolves one — *explicit* (``--base``) > the base that claim recorded >
    ``main_branch`` (issue #213). Measuring every claim against ``main_branch``
    meant stacked work never came home: an item merged into its queue branch is
    not in main until the queue lands, so it stayed 🔍 with nothing saying why.

    ``main_branch`` is still measured when that base does not report the work
    landed. A queue branch is deleted once it lands (`gc --merged` collects it),
    and `merge-tree` against a ref that no longer exists exits 1 exactly as a
    conflict does — so without the second measurement a 🔍 item whose queue
    had landed *and been cleaned up* was never reported again, though its work
    was in main. Work in main has landed wherever it was first merged.

    In `pr` mode nothing inside the loop ever observes the merge — the human
    does it on the forge, hours or days later — so 🔍 needs a way home or it is
    a state items enter and never leave. This is that way home, and it needs no
    knowledge of what a PR is: the same content oracle `gc` uses answers "has
    this work landed?" without a forge call that would silently degrade to
    "no open PRs found" when `gh` is missing or unauthenticated.

    Reports rather than edits. `sync` is a preflight, and a preflight that
    rewrites a tracked document as a side effect is not one.
    """
    item_status = _progress_item_status(repo_root, config)
    reviewing = {n for n, st in item_status.items() if st == "in-review"}
    if not reviewing or not _has_merge_tree(repo_root):
        return []
    local = _local_branches(repo_root)
    main = str(config["git"].get("main_branch", "main"))
    lines: List[str] = []
    for br in sorted(_list_claim_branches(repo_root, prefix)):
        num = _branch_item_number(br, prefix)
        if num not in reviewing:
            continue
        ref = _gc_ref(br, local)
        base = resolve_base(repo_root, config, explicit, br)
        candidates = [base] if base == main else [base, main]
        landed = next((b for b in candidates
                       if _branch_content_landed(repo_root, b, ref) is True), None)
        if landed is not None:
            base = landed
            lines.append(f"aide sync: item {num:03d} is 🔍 but its work is now in "
                         f"{base} — run 'python .aide/scripts/aide.py progress "
                         f"set {num:03d} done'")
    return lines


def cmd_sync(args: argparse.Namespace) -> int:
    """Deterministic preflight: fetch, verify a clean start point, land on the
    right branch. Replaces the exploratory ``git status``/``git branch``/
    ``git fetch`` sequence agents otherwise improvise before starting work.
    Exit 0 == safe to start; exit 1 prints the one reason work must not start.
    """
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    prefix = str(config["git"].get("branch_prefix", "aide/"))
    mode = str(config["git"].get("mode", "auto-merge"))
    main = str(config["git"].get("main_branch", "main"))

    if mode != "local" and _has_origin(repo_root):
        res = git(["fetch", "--all", "--prune"], repo_root, check=False)
        if res.returncode != 0:
            print(f"aide sync: fetch failed — {res.stderr.strip()}", file=sys.stderr)
            return 1

    dirty = git(["status", "--porcelain"], repo_root, check=False).stdout.strip()
    if dirty:
        print("aide sync: working tree not clean — commit or stash before starting:",
              file=sys.stderr)
        print(dirty, file=sys.stderr)
        return 1

    branch = git(["rev-parse", "--abbrev-ref", "HEAD"], repo_root, check=False).stdout.strip()

    # Bring main up to date when we're on it (safe fast-forward only).
    if branch == main and mode != "local" and _has_origin(repo_root):
        counts = git(["rev-list", "--left-right", "--count", f"{main}...origin/{main}"],
                     repo_root, check=False).stdout.split()
        if len(counts) == 2:
            ahead, behind = int(counts[0]), int(counts[1])
            if behind and not ahead:
                git(["merge", "--ff-only", f"origin/{main}"], repo_root, check=False)
                print(f"aide sync: fast-forwarded {main} ({behind} commit(s))")
            elif behind:
                print(f"aide sync: {main} has diverged from origin/{main} "
                      f"({ahead} ahead / {behind} behind) — reconcile first", file=sys.stderr)
                return 1

    if args.item is not None:
        claim = _find_claim_branch(repo_root, prefix, args.item)
        if not claim:
            print(f"aide sync: no claim branch for item {args.item:03d} — run "
                  f"'python .aide/scripts/aide.py claim' first", file=sys.stderr)
            return 1
        if branch != claim:
            res = git(["switch", claim], repo_root, check=False)
            if res.returncode != 0:
                print(f"aide sync: could not switch to {claim}:\n{res.stderr}", file=sys.stderr)
                return 1
            branch = claim
        if mode != "local" and _has_origin(repo_root) and claim in _remote_branches(repo_root):
            if _has_unpushed_merge(repo_root, f"origin/{claim}"):
                # The same guard the bookkeeping and post-merge pulls have
                # (issue #235): `pull --rebase` over a local merge commit
                # linearises it silently, or stops mid-rebase on the conflict
                # the merge resolved — on a checkout other roles may share.
                # `--ff-only` refuses instead of rewriting.
                ff = git(["pull", "--ff-only", "origin", claim], repo_root, check=False)
                if ff.returncode != 0:
                    print(f"aide sync: {claim} carries a merge commit origin "
                          f"has not seen, and origin/{claim} has moved on. "
                          f"Rebasing over it would linearise the merge and "
                          f"bring back the conflicts it resolved, so this verb "
                          f"stops rather than choosing for you: push the claim "
                          f"branch first ('git push origin {claim}'), or "
                          f"integrate origin by hand, then re-run.\n"
                          f"{ff.stdout}{ff.stderr}", file=sys.stderr)
                    return 1
                pulled = ff
            else:
                pulled = git(["pull", "--rebase", "origin", claim], repo_root, check=False)
            stalled = _stalled_pull(repo_root, config, pulled)
            if stalled is not None:
                print(f"aide sync: {stalled}\n"
                      f"aide sync: this verb exists to say the start point is "
                      f"safe, and it is not — work must not start here.",
                      file=sys.stderr)
                return 1
            if pulled.returncode != 0:
                # Non-zero, but the tree is untouched: origin unreachable, the
                # ref gone. Not a reason to refuse — the branch is checked out
                # and clean, which is what this verb promises — but the success
                # line below says "remotes fetched", and that would overclaim.
                why = next((l.strip() for l in
                            (pulled.stderr + pulled.stdout).splitlines()
                            if l.strip()), "git gave no reason")
                print(f"aide sync: {claim} was NOT refreshed from origin — "
                      f"{why}. The branch is clean and work can start; it may "
                      f"be behind origin.", file=sys.stderr)

    for line in _landed_review_items(repo_root, config, prefix):
        print(line)

    print(f"aide sync: OK — on '{branch}', tree clean"
          + ("" if mode == "local" else ", remotes fetched"))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """One-call roadmap-state report: branch + divergence, derived queue
    states, claim branches, and (best effort) open PRs — replacing the several
    manual git/gh round-trips a resuming orchestrator otherwise makes."""
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    prefix = str(config["git"].get("branch_prefix", "aide/"))
    mode = str(config["git"].get("mode", "auto-merge"))

    if not args.no_fetch and mode != "local" and _has_origin(repo_root):
        git(["fetch", "--all", "--prune"], repo_root, check=False)

    branch = _current_branch(repo_root)
    # Report divergence from the base this branch actually has, not always from
    # main — on stacked work the interesting distance is to the queue branch.
    main = resolve_base(repo_root, config, args.base, branch)
    line = f"branch: {branch or '(unknown)'}"
    if mode != "local" and _has_origin(repo_root):
        counts = git(["rev-list", "--left-right", "--count", f"{main}...origin/{main}"],
                     repo_root, check=False).stdout.split()
        if len(counts) == 2:
            ahead, behind = counts
            line += f" · {main}: {ahead} ahead / {behind} behind origin/{main}"
    print(f"aide status — {repo_root.name}")
    print(f"  {line}")

    dirty = git(["status", "--porcelain"], repo_root, check=False).stdout.strip()
    print(f"  tree: {'dirty (' + str(len(dirty.splitlines())) + ' path(s))' if dirty else 'clean'}")

    item_status = _progress_item_status(repo_root, config)
    qdir = docs_dir(repo_root, config) / "queue"
    live_seen = False
    if iter_queue_paths(qdir):
        for path in iter_queue_paths(qdir):
            nums = queue_item_numbers(path.read_text(encoding=_ENCODING))
            open_nums = [n for n in nums
                         if item_status.get(n, "planned")
                         in ("planned", "in-progress", "in-review")]
            if open_nums:
                tag = " (live)" if not live_seen else ""
                live_seen = True
                listed = ", ".join(f"{n:03d}" for n in open_nums)
                print(f"  {path.name}: open{tag} — {len(open_nums)}/{len(nums)} items open ({listed})")
            else:
                print(f"  {path.name}: done")
    else:
        print("  queues: none")

    # Outcome targets not yet ✅ Met — the goal-level state a summary table's
    # stage icons deliberately do not carry (conventions.md §1).
    ppath = docs_dir(repo_root, config) / "progress.md"
    if ppath.is_file():
        plines = ppath.read_text(encoding=_ENCODING).splitlines()
        for n, g in enumerate(human_gates(plines), start=1):
            if g.kind == "approved":
                continue
            reach = g.reach
            label = {"declined": "❌ declined", "awaiting": "⏳ awaiting a decision"}.get(
                g.kind, "⚠ unrecognised status")
            print(f"  gate {n}: {g.text} [blocks {reach}] — {label}")
        # Every table, not only gates: a row no reader can use is missing
        # from the lines above, and would otherwise be missing from here.
        for table, i, _, problem in _unreadable_rows(plines):
            held = (" — holding every item until it is fixed"
                    if table is _HUMAN_GATES else "")
            print(f"  unreadable: progress.md:{i + 1}: {table.name} row "
                  f"{problem}{held}")
        for t in outcome_targets(plines):
            if t.kind == "met":
                continue
            label = {"not-met": "❌ not met", "unverified": "❓ unverified"}.get(
                t.kind, "⚠ unrecognised status")
            objs = f" [{', '.join(t.objectives)}]" if t.objectives else ""
            print(f"  target: {t.text}{objs} — {label}")
        # Capabilities not yet ✅ Verified (issue #207). Profiles run only on
        # request, and only for a ❓ Unverified row: an expression is project
        # code that may import a GPU stack, and a row with any other Status —
        # `⏸️ Out of scope` — is not one to be told it can be verified now.
        profiles = {k: str(v) for k, v in (config.get("validation") or {}).items()}
        verdicts: Dict[str, Tuple[bool, str]] = {}
        for c in gated_capabilities(plines):
            if c.kind == "verified":
                continue
            label = "❓ unverified" if c.kind == "unverified" else "⚠ unrecognised status"
            for name in c.profiles:
                if name not in profiles:
                    label += f"; profile '{name}' is not defined in [validation]"
                    continue
                if not (args.profiles and c.kind == "unverified"):
                    label += f"; profile '{name}'"
                    continue
                if name not in verdicts:
                    verdicts[name] = evaluate_profile(repo_root, config, profiles[name])
                satisfied, detail = verdicts[name]
                label += (f"; profile '{name}' is satisfied here — the gated path "
                          f"can be run and the row verified" if satisfied
                          else f"; profile '{name}' is not satisfied here"
                          + (f" ({detail})" if detail else ""))
            stages = (f" [stage {', '.join(map(str, c.stages))}]"
                      if c.stages else "")
            print(f"  capability: {c.text}{stages} — {label}")
        for stg, cn, cdate, creason in retracted_criteria(plines):
            print(f"  retracted: stage {stg} criterion {cn} ({cdate}) — {creason}")

    branches = _list_claim_branches(repo_root, prefix)
    # Guarded the way `run_checks` guards it: two git spawns are not worth
    # paying on every `status` in the common "claims: none" case, and the
    # windows leg spends ~13x on a spawn (issue #74).
    unpublished = (set(_unpublished_branches(repo_root, config, prefix))
                   if branches else set())
    if branches:
        for br in branches:
            num = _branch_item_number(br, prefix)
            if num is None:
                kind = "queue branch" if _is_queue_branch(br, prefix) else "unrecognised"
                extra = " — NOT on origin" if br in unpublished else ""
                print(f"  branch: {br} ({kind} — not an item claim){extra}")
                continue
            st = item_status.get(num, "planned")
            note = ""
            if st == "complete":
                note = " — STALE (item ✅; run 'aide gc')"
            elif st == "in-review":
                # Recommending `gc` here would be recommending the deletion of
                # an open PR's head branch. It is awaiting a human, not stale.
                note = " — awaiting review (merge the PR, then 'aide progress "
                note += f"set {num:03d} done')"
            # Composes with the status note rather than replacing it: a branch
            # can be both stale and unpublished, and a reader needs both.
            if br in unpublished:
                note += (f" — NOT on origin: the claim's push did not land, so "
                         f"no other checkout can see this claim "
                         f"('git push -u origin {br}' to publish it)")
            print(f"  claim: {br} (item {num:03d}: {st}){note}")
    else:
        print("  claims: none")

    for line in _landed_review_items(repo_root, config, prefix, args.base):
        print("  " + line.replace("aide sync: ", ""))

    # Open PRs, best effort — informative only, silently skipped without `gh`.
    try:
        # §6: PR titles are arbitrary UTF-8 and are printed straight through.
        res = subprocess.run(["gh", "pr", "list", "--state", "open"],
                             cwd=str(repo_root), stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, encoding="utf-8",
                             errors="replace", timeout=20)
        if res.returncode == 0:
            prs = res.stdout.strip()
            if prs:
                print("  open PRs:")
                for l in prs.splitlines():
                    print(f"    {l}")
            else:
                print("  open PRs: none")
    except (OSError, subprocess.SubprocessError):
        pass
    return 0


def _merged_prefixed_branches(repo_root: Path, main: str, prefix: str) -> List[str]:
    """Prefixed local branches already merged into *main*, per git itself.

    Ancestry-based, so it misses **every** squash merge — which is the shape
    GitHub's "Squash and merge" produces. `_branch_content_landed` is the
    stronger oracle and is preferred wherever git is new enough; this remains
    the fallback on git < 2.38, where being conservative means deleting *less*.
    """
    out = git(["branch", "--merged", main, "--format=%(refname:short)"],
              repo_root, check=False).stdout
    return [l.strip() for l in out.splitlines() if l.strip().startswith(prefix)]


#: `git merge-tree --write-tree` landed in git 2.38 (Oct 2022). As of Aug 2026
#: the only realistic holdout is Ubuntu 22.04 LTS (git 2.34.1, in standard
#: support until April 2027); 24.04, Debian 12, Git for Windows, macOS CLT and
#: this repo's CI are all past it. There is deliberately **no fallback oracle**:
#: on older git `gc` refuses to delete on the ✅ ground rather than degrading to
#: a weaker test, so old git is always *more* conservative and there is one
#: oracle to keep honest rather than two.
_MERGE_TREE_MIN_GIT = (2, 38)


def _git_version(repo_root: Path) -> Optional[Tuple[int, int]]:
    """(major, minor) of the git on PATH, or None when it cannot be read."""
    out = git(["--version"], repo_root, check=False).stdout
    m = re.search(r"(\d+)\.(\d+)", out)
    return (int(m.group(1)), int(m.group(2))) if m else None


def _has_merge_tree(repo_root: Path) -> bool:
    version = _git_version(repo_root)
    return version is not None and version >= _MERGE_TREE_MIN_GIT


def _branch_content_landed(repo_root: Path, base: str,
                           branch_ref: str) -> Optional[bool]:
    """True when merging *branch_ref* into *base* would change *base* not at all.

    The question `gc` actually needs answered before force-deleting: is this
    branch's work already in the base? `git branch --merged` answers a *different*
    question (is the tip an ancestor) and so misses every squash merge, which is
    why `gc` reaches for `-D` in the first place. `git cherry` gets a
    single-commit squash right and a multi-commit squash wrong — a false alarm on
    the exact shape "Squash and merge" produces. Measured against fixtures of all
    three shapes:

    ======================  ===============  ============  =================
    branch                  branch --merged  git cherry    merge-tree
    ======================  ===============  ============  =================
    1 commit, squashed      misses           correct       no-op
    2 commits, squashed     misses           false alarm   no-op
    genuinely unmerged      correct          correct       would change base
    ======================  ===============  ============  =================

    Comparing the merged tree to the base's own tree also stays correct after the
    base advances with unrelated work, since that work is in both sides.

    Returns None when the answer cannot be established (unreadable ref, git too
    old, unexpected output) — a caller must treat that as "do not delete", never
    as "landed".
    """
    if not _has_merge_tree(repo_root):
        return None
    # Resolve first, so an unreadable ref is reported as unmeasurable rather than
    # as content: `merge-tree` exits 1 for a bad ref exactly as it does for a
    # conflict, and mapping both to False made `gc` skip for the right reason but
    # state the wrong one — "has content not in main" about a ref it never read.
    if not _ref_exists(repo_root, branch_ref):
        return None
    res = git(["merge-tree", "--write-tree", base, branch_ref], repo_root, check=False)
    if res.returncode == 1:
        return False  # conflicts: the branch certainly carries content the base lacks
    if res.returncode != 0:
        return None
    merged = res.stdout.strip().splitlines()
    base_tree = git(["rev-parse", f"{base}^{{tree}}"], repo_root, check=False).stdout.strip()
    if not merged or not base_tree:
        return None
    return merged[0].strip() == base_tree


def _checked_out_branches(repo_root: Path) -> set:
    """Branch names `gc` must never delete because a checkout is sitting on them.

    Three ways that happens, and the guard has to cover all three or the preview
    promises a delete `--yes` cannot perform:

    - **This worktree, on a branch.** The original case.
    - **This worktree, detached.** `git rev-parse --abbrev-ref HEAD` returns the
      literal string `HEAD`, and no branch is ever equal to that — so the guard
      silently protected nothing. Detached, the thing to protect is every branch
      at the checked-out commit.
    - **Another worktree.** `git branch -D` refuses these (git's own check), so
      without asking `git worktree list` the preview lists a branch the delete
      then bounces off.
    """
    protected = set()
    # `worktree list --porcelain` names the branch of every attached worktree —
    # including this one when it is not detached — as `branch refs/heads/<name>`.
    out = git(["worktree", "list", "--porcelain"], repo_root, check=False).stdout
    for line in out.splitlines():
        if line.startswith("branch refs/heads/"):
            protected.add(line[len("branch refs/heads/"):].strip())

    name = _current_branch(repo_root)
    if name and name != "HEAD":
        protected.add(name)
        return protected
    head = git(["rev-parse", "HEAD"], repo_root, check=False).stdout.strip()
    if not head:
        return protected
    points_at = git(["branch", "--points-at", head, "--format=%(refname:short)"],
                    repo_root, check=False).stdout
    protected.update(l.strip() for l in points_at.splitlines() if l.strip())
    return protected


def _plural(n: int, one: str, many: str) -> str:
    return f"{n} {one}" if n == 1 else f"{n} {many}"


def _gc_empty_notes(repo_root: Path, prefix: str, main: str,
                    merged_flag: bool, local: List[str],
                    remote: List[str]) -> List[str]:
    """Why an empty ``gc`` result may still leave cleanup available.

    Two things the bare message hides. First, the default invocation checks
    only the item ground, so a branch that no longer resolves to an item —
    every queue and specs-queue branch — is structurally invisible to it while
    ``--merged`` would take it. Second, `gc` only ever looks at branches under
    ``prefix``, so a merged branch named anything else is never considered on
    either ground.

    Returns [] when there is genuinely nothing further to say, so the common
    case stays a single terse line. The ``--merged`` probe runs only on this
    empty path, never in the normal one.
    """
    notes: List[str] = []
    if not merged_flag and (local or remote):
        extra = _merged_prefixed_branches(repo_root, main, prefix)
        if extra:
            notes.append(
                f"{_plural(len(extra), 'branch', 'branches')} under '{prefix}' "
                f"{'is' if len(extra) == 1 else 'are'} merged into {main} — "
                f"'aide gc --merged' will take {'it' if len(extra) == 1 else 'them'}")
    others = [b for b in _local_branches(repo_root)
              if not b.startswith(prefix) and b != main]
    if others:
        notes.append(
            f"{_plural(len(others), 'local branch', 'local branches')} outside "
            f"the '{prefix}' scope {'was' if len(others) == 1 else 'were'} not "
            f"considered — gc only ever manages claim branches")
    return notes


def _gc_ref(branch: str, local: List[str]) -> str:
    """The ref to measure *branch* by: the local branch, else its remote copy."""
    return branch if branch in local else f"origin/{branch}"


def cmd_gc(args: argparse.Namespace) -> int:
    """Delete claim branches whose work has landed (item ✅ in progress.md, or
    ``--merged`` branches already merged into main). Dry-run by default; pass
    ``--yes`` to delete. The one destructive verb in the CLI, so it is never
    implicit."""
    repo_root = find_repo_root(args.repo)
    config = load_config(repo_root)
    prefix = str(config["git"].get("branch_prefix", "aide/"))
    mode = str(config["git"].get("mode", "auto-merge"))
    # The `--merged` ground is "already merged into <base>", so it takes a base
    # like everything else: on stacked work the branches that have landed have
    # landed into the queue branch, and asking about `main` finds none of them.
    main = resolve_base(repo_root, config, args.base)

    if mode != "local" and _has_origin(repo_root):
        git(["fetch", "--all", "--prune"], repo_root, check=False)

    progress_path = docs_dir(repo_root, config) / "progress.md"
    item_status: Dict[int, str] = {}
    if progress_path.is_file():
        _, _, item_status = _parse_item_status(
            progress_path.read_text(encoding=_ENCODING).splitlines())

    local = [b for b in _local_branches(repo_root) if b.startswith(prefix)]
    remote = [b for b in _remote_branches(repo_root) if b.startswith(prefix)]

    # The content oracle is what makes `-D` on the ✅ ground safe; without it
    # that ground refuses outright (see `_MERGE_TREE_MIN_GIT`).
    can_measure = _has_merge_tree(repo_root)

    merged_local: List[str] = []
    if args.merged:
        merged_local = _merged_prefixed_branches(repo_root, main, prefix)

    targets: Dict[str, str] = {}  # branch -> reason
    skips: Dict[str, str] = {}    # branch -> why it is NOT acted on
    protected = _checked_out_branches(repo_root)
    for br in sorted(set(local) | set(remote)):
        # Only a positively-identified item claim is deletable on the "item is
        # ✅" ground. A queue branch shares the number namespace but not the
        # lifecycle: it aggregates many items and lands as one reviewed PR, so
        # deleting it because some same-numbered item finished would discard
        # unreviewed work. It stays eligible under --merged, where the ground
        # is "already merged into main" and is checked against git itself.
        num = _branch_item_number(br, prefix)
        if num is not None and item_status.get(num) == "complete":
            reason = f"item {num:03d} is ✅"
            # `progress.md` is a document, edited by agents and humans; git is
            # the authority on whether the commits landed, and until 1.20.0 it
            # was never asked. A ✅ can outrun the merge easily — a commit added
            # after the validator marked it done, a hand-edit, the `pr`-mode
            # window — and the action here is `git branch -D` plus a remote
            # delete, where the remote half is unrecoverable on a plain git host.
            if args.abandon:
                targets[br] = reason + "; --abandon"
            elif not can_measure:
                skips[br] = (f"{reason}, but this git cannot verify the work "
                             f"landed (needs "
                             f"{_MERGE_TREE_MIN_GIT[0]}.{_MERGE_TREE_MIN_GIT[1]}+ "
                             f"for 'merge-tree --write-tree'); use --merged or "
                             f"--abandon")
            else:
                landed = _branch_content_landed(repo_root, main, _gc_ref(br, local))
                if landed is True:
                    targets[br] = reason
                elif landed is False:
                    skips[br] = (f"{reason} but the branch has content not in "
                                 f"{main}; re-check it, or pass --abandon to "
                                 f"delete it anyway")
                else:
                    # Not the same statement, and this is the one destructive
                    # verb: say the measurement failed, not that the branch
                    # carries work it may not carry.
                    skips[br] = (f"{reason}, but whether its work is in {main} "
                                 f"could not be determined (ref "
                                 f"'{_gc_ref(br, local)}' unreadable); not "
                                 f"deleting — pass --abandon to delete anyway")
        elif br in merged_local:
            targets[br] = f"merged into {main}"
        elif (args.merged and can_measure
              and _branch_content_landed(repo_root, main, _gc_ref(br, local)) is True):
            # `--merged` is built on `git branch --merged`, which is ancestry-
            # based and so misses every squash merge — the very shape `-D` was
            # reached for. The same oracle that guards the ✅ ground closes that.
            targets[br] = f"content already in {main}"

    if not targets and not skips:
        # "Nothing to clean" is a claim about the ground and the scope this run
        # actually checked, not about the repository — say which. The default
        # invocation checks only the item ground, and every invocation ignores
        # branches outside `prefix` (deliberately: gc is the one destructive
        # verb and must not delete branches it does not own). Left unqualified,
        # the message reads as "no cleanup is available here" and the next
        # reach is the raw `git branch -d` the CLI exists to replace.
        print("aide gc: nothing to clean")
        for note in _gc_empty_notes(repo_root, prefix, main, args.merged, local, remote):
            print(f"  {note}")
        return 0

    # Every skip is decided BEFORE anything is printed, so the preview is the
    # set `--yes` acts on rather than a promise it then quietly narrows. A dry
    # run that overstates trains the reader to skim it, and this is the one
    # destructive verb — the list a human is asked to approve must be exact.
    for br in [b for b in targets if b in protected]:
        del targets[br]
        skips[br] = ("checked out (here or in another worktree) — git refuses to "
                     "delete a branch a checkout is sitting on")

    def _where(br: str) -> str:
        return ("local+remote" if br in local and br in remote
                else "local" if br in local else "remote")

    for br in sorted(skips):
        print(f"skipping {br} ({_where(br)}): {skips[br]}")
    for br, reason in targets.items():
        if not args.yes:
            print(f"would delete {br} ({_where(br)}; {reason})")
            continue
        failures: List[str] = []
        if br in local:
            # -D: a ✅/merged item's branch may have landed via squash/PR, so
            # git's ancestry-based -d safety check can refuse a branch whose
            # work is in fact on main. Safe here only because the content check
            # above already asked git whether the work landed.
            res = git(["branch", "-D", br], repo_root, check=False)
            if res.returncode != 0:
                failures.append(f"local ({(res.stderr or '').strip()})")
        if br in remote and mode != "local":
            res = git(["push", "origin", "--delete", br], repo_root, check=False)
            if res.returncode != 0:
                failures.append(f"remote ({(res.stderr or '').strip()})")
        # Report what git did, not what was asked of it. `-D` still refuses a
        # branch checked out in ANOTHER worktree, which `_checked_out_branches`
        # cannot see from here — and printing "deleted" over a refusal makes the
        # report the very thing this verb was just fixed to stop being: a claim
        # that does not match what happened.
        if failures:
            print(f"could NOT delete {br} ({_where(br)}; {reason}): "
                  f"{'; '.join(failures)}", file=sys.stderr)
        else:
            print(f"deleted {br} ({_where(br)}; {reason})")
    if not targets:
        print("aide gc: nothing to delete")
    if not args.yes and targets:
        print("aide gc: dry run — re-run with --yes to delete")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aide", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", type=Path, default=None, help="repo root (default: search up for aide.toml)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser(
        "check", help="consistency gate over docs/aide, "
        "plus the test-hygiene lints over tests_dir, which "
        "run with a notice even in a repo with no docs_dir "
        "(writes only a missing insights.md, from the "
        "template, and the file --report names)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "--queue NNN checks one queue's specs against each other: two items "
            "claiming one path under May change (warning), one item changing a "
            "path another pins under Asserts against (error), a dependency "
            "cycle, and a dependency on an item that exists nowhere.\n"
            "\n"
            "Three discounts apply. Spent items (\u2705 merged or \u274c excluded in "
            "progress.md) are discounted on both sides of every comparison, and "
            "a finding against one is an error no later item can clear. A "
            "declared dependency is discounted in one direction: when the "
            "pinning item names the changing one under ## Dependencies, "
            "directly or through a chain of items on the same queue, the edit "
            "landing cannot break its pin. Only links that still order count: a "
            "dependency claim no longer waits for (\u2705, \u274c, \u23f8\ufe0f) earns no "
            "exemption, and neither does a chain whose middle item no longer "
            "blocks. The cycle check keeps only items whose status still blocks "
            "a claim; deferred items stay in the path comparisons.\n"
            "\n"
            "Over progress.md's tables, ERRORS: a missing stage summary "
            "table, objective coverage table or stage section; a stage "
            "summary row marked \u2705 over a stage whose deliverables do not "
            "roll up to \u2705 (`aide progress -h` states the rollup); an "
            "objective marked \u2705 over an "
            "Outcome target that is \u274c Not met \u2014 the goal-level "
            "mirror of that over-claim; and a row of the stage summary, "
            "objective coverage, Outcome targets or Human gates table that "
            "its reader cannot use \u2014 the wrong cell count (a '|' inside "
            "a cell, usually), a Stage cell that is not an integer, an "
            "objective coverage row not starting G<n>, an empty Target cell, "
            "a summary or objective Status cell with no "
            "icon \u2014 since the row is dropped from every check it would "
            "have fed. Each table is read under its template heading, or, "
            "for a summary or objective table without one, wherever its rows "
            "are found. Warnings, and a warning never moves the exit "
            "code \u2014 only an error does: a stage whose deliverables roll "
            "up to \u2705 under a summary row that is not, a stage header "
            "disagreeing with its summary row, a summary row with no stage "
            "section, an objective marked \u2705 over a target not yet \u2705 "
            "Met, an Outcome target or human gate whose Status is not one of "
            "its table's marks, and every human gate still blocking \u2014 a "
            "normal state rather than a defect. A summary row marked "
            "\u23f8\ufe0f or \u274c is left out of all three stage comparisons "
            "above, deliverables and header alike: the stage is deferred or "
            "dropped, so its bullets no longer speak for it.\n"
            "\n"
            "Over the Environment-Gated Capability Verification table, "
            "warnings only, since no other check gates on it: a row its "
            "reader cannot use (the wrong cell count, or an empty Capability "
            "cell); a Status that is neither \u2705 Verified nor \u2753 "
            "Unverified; a profile named in the Package / Tool cell that "
            "[validation] does not define; and a row still \u2753 Unverified "
            "with an empty or dash-only Notes cell whose introducing stage "
            "\u2014 the first `Stage N` run in its Introduced by cell \u2014 "
            "is \u2705 in the stage summary.\n"
            "\n"
            "Among the other lints over docs/aide, these are warnings: a "
            "file under items/ not named NNN-<slug>.md, which `aide scope`, "
            "`aide claim` and `aide check --queue` never find, reported in "
            "place of every other spec lint; an Authorised paths bullet whose "
            "second backtick span or continuation line is silently dropped, "
            "named span by span; one path listed under both May change and "
            "Asserts against (the exact double-listing only \u2014 a literal "
            "pin under a May-change glob is the legitimate carve-out, left "
            "for `aide scope` to judge); an always-authorised path pinned "
            "under Asserts against; a marked assumption pinning an engine "
            "whose feature line predates the installed one; every "
            "retracted acceptance criterion, a normal state rather than a "
            "defect; and an insights entry whose shape is off \u2014 loose "
            "either side of the date, strict about the date, and never "
            "applied to an archived entry; a ledger row no reader can "
            "use \u2014 the wrong cell count, an Item cell that is not an "
            "item number, an Outcome that is neither merged nor abandoned, "
            "or a count cell that is neither an integer nor "
            "blank \u2014 reported only where ledger.md exists, since a "
            "check never creates it; and a document whose aide-template "
            "line above its title records a version other than the installed template's, "
            "names a template this engine does not ship, or cannot be read "
            "\u2014 read on vision.md, roadmap.md, progress.md, "
            "insights.md and ledger.md, on a queue while it is open and on an "
            "item spec "
            "until its item is \u2705 or \u274c, and never on a document with "
            "no such line. A \U0001f50d item's claim branch "
            "is not reported stale."))
    p_check.add_argument("--queue", type=int, default=None,
                         help="also check this queue's specs against each other "
                              "(scope overlaps, pinned state, dependency graph)")
    p_check.add_argument("--report", default=None,
                         help="with --queue: write the findings as JSON to this path")
    p_check.set_defaults(func=cmd_check)

    p_prog = sub.add_parser(
        "progress", help="edit progress.md status / acceptance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "set:     flip an item's deliverable bullet and roll its stage "
            "up; a marker naming several items is desugared into one bullet "
            "per item first, and only the named item moves \u2014 the others "
            "keep the status they had\n"
            "accept:  tick one acceptance criterion (--criterion N) or every "
            "one in the stage (--all), with --evidence\n"
            "amend:   append a dated correction under a ticked box; the tick "
            "stands (--evidence required)\n"
            "retract: untick a box, keep the original attestation visible, "
            "and capture a `gap` insight (--reason required)\n"
            "reword:  change a criterion's text in progress.md and roadmap.md, "
            "or in neither; where roadmap.md has no acceptance block for the "
            "stage, in progress.md alone; refuses over a ticked, annotated or "
            "corrected box\n"
            "\n"
            "The rollup, applied by set and read by `aide check`: a stage is "
            "\u2705 when every deliverable bullet in it is \u2705 or \u274c "
            "and at least one is \u2705; \U0001f6a7 when any bullet is "
            "\u2705, \U0001f6a7 or \U0001f50d; otherwise \U0001f4cb. "
            "\U0001f50d and \u23f8\ufe0f are both kept out of the \u2705 "
            "rule \u2014 an item awaiting review or deferred has not shipped. "
            "They differ below it: \U0001f50d also satisfies the \U0001f6a7 "
            "rule, so a stage holding one is always \U0001f6a7, while "
            "\u23f8\ufe0f does not \u2014 a stage whose bullets are only "
            "\u23f8\ufe0f, \U0001f4cb and \u274c reads \U0001f4cb. "
            "The stage header, its summary-table "
            "row, and any Objective row delivered solely by \u2705 stages "
            "follow; an objective linked to an Outcome target that is not "
            "\u2705 Met never rolls up. A status is never downgraded, and no "
            "rollup ever ticks an acceptance box.\n"
            "\n"
            "reword matches the Nth box to the Nth non-`Target:` bullet of the "
            "roadmap stage's Validation / acceptance block; if the two cannot "
            "be lined up, nothing is written and the message says which counts "
            "disagreed.\n"
            "\n"
            "Neither amend nor retract takes --all: each attestation was made "
            "separately and is corrected or withdrawn separately. Both refuse "
            "without a stated reason. `aide check` warns on every retracted "
            "criterion and `aide status` prints it."))
    p_prog.add_argument("action",
                        choices=["set", "accept", "amend", "retract", "reword"])
    p_prog.add_argument("number", type=int,
                        help="item number (set) | stage number (every other action)")
    p_prog.add_argument("status", nargs="?", default=None,
                        help="set: in-progress | in-review | done "
                             "(in-review = pushed, awaiting a human's merge)")
    p_prog.add_argument("--criterion", type=int, default=None,
                        help="1-based acceptance-criterion index within the stage")
    p_prog.add_argument("--all", action="store_true", dest="all_criteria",
                        help="accept: every acceptance criterion in the stage "
                             "(amend/retract/reword act on one criterion only)")
    p_prog.add_argument("--evidence", default=None,
                        help="accept: annotation appended to the ticked criterion; "
                             "amend: the corrected evidence, appended as a dated line")
    p_prog.add_argument("--reason", default=None,
                        help="retract: why the attestation is withdrawn (required)")
    p_prog.add_argument("--text", default=None,
                        help="reword: the criterion's new wording (required)")
    p_prog.add_argument("--date", default=None,
                        help="amend/retract: ISO date for the trail line (default: today)")
    p_prog.add_argument("--no-commit", action="store_true", help="edit only, do not git commit")
    p_prog.set_defaults(func=cmd_progress)

    p_gate = sub.add_parser("gate", help="list / resolve human gates in progress.md")
    p_gate.add_argument("action", choices=["list", "approve", "decline"])
    p_gate.add_argument("number", type=int, nargs="?", default=None,
                        help="1-based gate row (approve/decline); see `aide gate list`")
    p_gate.add_argument("--evidence", "--reason", dest="note", default=None,
                        help="decision note written into the gate's last cell")
    p_gate.add_argument("--no-commit", action="store_true", help="edit only, do not git commit")
    p_gate.set_defaults(func=cmd_gate)

    p_queue = sub.add_parser("queue", help="queue branch creation / maintenance")
    p_queue.add_argument("action", choices=["start", "tidy"])
    p_queue.add_argument("number", type=int)
    p_queue.add_argument("--specs", action="store_true",
                         help="start: create the specs-queue branch instead")
    p_queue.add_argument("--base", default=None,
                         help="start: branch from this ref (default: main_branch)")
    p_queue.add_argument("--dry-run", action="store_true",
                         help="start: print what would be created, create nothing")
    p_queue.add_argument("--date", default=None, help="tidy: override the supersede date (YYYY-MM-DD)")
    p_queue.set_defaults(func=cmd_queue)

    p_ins = sub.add_parser(
        "insights", help="list / tick / archive / resolve the insight inbox",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "list:    number the entries by position and print them all, "
            "ticked ones included; --open narrows to the untriaged, and an "
            "archived entry is in neither\n"
            "tick:    the one in-place edit — tick entry N with --pointer; on "
            "an entry already ticked, append a dated trail line instead; "
            "with --trail, append the dated line under entry N and leave "
            "its checkbox as it is, which is how a judgement that keeps an "
            "entry open (a duplicate, a reason it stays) is recorded\n"
            "archive: move closed entries older than --before into "
            "insights/archive-YYYY-QN.md, each with its trail, line for line; "
            "an entry it cannot date is named and left behind; the archive is "
            "frozen and no longer shape-checked; what remains is renumbered, "
            "so re-run list\n"
            "resolve: write the union of a conflicted inbox — the shared "
            "history, then each side's new entries in capture order; a tick "
            "on either side stands and keeps its pointer, trail lines merge "
            "in date order, and two ticks with different pointers keep both "
            "and say so. Refuses, writing nothing, anything that is not a "
            "pure append: a claim reworded, reordered or deleted on one side, "
            "or a side that archived.\n"
            "\n"
            "A missing insights.md is created from .aide/templates/insights.md "
            "by list (and by check, claim and queue start) and committed when "
            "git can — on a branch, with an identity; otherwise it is left "
            "untracked and the notice says why."))
    p_ins.add_argument("action", choices=["list", "tick", "archive", "resolve"])
    p_ins.add_argument("number", type=int, nargs="?", default=None,
                       help="tick: the entry number from `insights list`")
    p_ins.add_argument("--open", action="store_true", dest="open_only",
                       help="list: only entries still untriaged")
    p_ins.add_argument("--type", default=None,
                       help="list: one of " + ", ".join(_INSIGHT_TYPES))
    p_ins.add_argument("--trail", action="store_true",
                       help="list: also print each entry's status trail; "
                            "tick: append the dated --pointer line under entry N "
                            "without ticking it")
    p_ins.add_argument("--pointer", default=None,
                       help="tick: where the claim landed (a doc, item, or issue)")
    p_ins.add_argument("--before", default=None,
                       help="archive: move entries closed before this date (YYYY-MM-DD)")
    p_ins.add_argument("--date", default=None,
                       help="tick, resolve: override the trail-line date "
                            "(default: today)")
    p_ins.add_argument("--dry-run", action="store_true",
                       help="resolve: print what the union would be, write nothing")
    p_ins.add_argument("--yes", action="store_true",
                       help="archive: actually move (default: dry run)")
    p_ins.add_argument("--no-commit", action="store_true", help="edit only, do not git commit")
    p_ins.set_defaults(func=cmd_insights)

    p_ledger = sub.add_parser(
        "ledger", help="record what an item cost where no merge will "
        "(one row per item, docs/aide/ledger.md)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "abandon: the row for an item that never merged \u2014 one "
            "stopped at the validation-round cap, which is exactly the item a "
            "reader at a queue boundary is looking for and the one `aide "
            "merge` never sees.\n"
            "\n"
            "The cells are derived as `merge` derives them, from the "
            "documents and \u2014 where the claim branch is still there "
            "\u2014 a diff against the base it recorded; a branch already "
            "gone costs the two diff cells and nothing else on the row. "
            "--rounds is required and the verb exits 2 without it: the round "
            "count is why the row exists, and an abandoned item recorded "
            "without one says nothing a reader can use. --findings is "
            "optional, and a rank left out of it is a blank cell \u2014 "
            "except under a project whose [loop] review is off, where the "
            "three finding cells carry the same `-` mark `merge` writes. An "
            "item "
            "already recorded as abandoned with the same counts is not "
            "recorded twice: a re-run appends nothing and exits 0, while a "
            "different count is a new abandonment and a new row.\n"
            "\n"
            "It writes the ledger and nothing else: progress.md keeps "
            "whatever status the run left it, since what becomes of an "
            "abandoned item is a decision, not a record. The file is created "
            "from .aide/templates/ledger.md when this is the first row, and "
            "committed on the branch the run is standing on, with no pull."))
    p_ledger.add_argument("action", choices=["abandon"])
    p_ledger.add_argument("number", type=int)
    p_ledger.add_argument("--rounds", type=_non_negative_argument, default=None,
                          help="build\u2194validate rounds the item took "
                               "before it was abandoned (required)")
    p_ledger.add_argument("--findings", type=_findings_argument, default=None,
                          help="findings by rank: blocking=A,minor=B,nit=C "
                               "\u2014 any subset, any order")
    p_ledger.add_argument("--no-commit", action="store_true",
                          help="write the row, do not git commit")
    p_ledger.set_defaults(func=cmd_ledger)

    register_git_subcommands(sub)  # claim / merge / env (git layer)
    return parser


def register_git_subcommands(sub) -> None:
    """Attach the claim / merge / env subparsers (git layer)."""
    p_claim = sub.add_parser(
        "claim", help="pick + claim the next unclaimed 📋 item",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Picks the first 📋 item the queue lists \u2014 its own "
            "order, not the item numbers \u2014 whose dependencies have all "
            "left the way (\u2705, \u274c or "
            "\u23f8\ufe0f) and that no unresolved human gate reaches. It "
            "will not offer a blocked item: where a gate holds the pick, the "
            "report names that gate, what it blocks and who may resolve it, "
            "rather than an unexplained \"none left\". A human-gates row it "
            "cannot read holds every item, since what it blocks is unknown: "
            "the report names the row and exits 1. A missing insights.md "
            "is created from the template on the way through. When the "
            "item's spec exists and an Assumption names an item under its "
            "## Dependencies, the claim names that assumption as pinning a "
            "dependency's interface, to be re-checked before tests are "
            "written; an engine-marked assumption and one already carrying a "
            "re-check are not named, and a dependency that left the queue as "
            "\u274c or \u23f8\ufe0f is named as having no code to check "
            "against."))
    p_claim.add_argument("--queue", type=int, default=None,
                         help="queue number (default: the lowest-numbered open queue)")
    p_claim.add_argument("--base", default=None,
                         help="branch this claim off, and merge it back into "
                              "(default: the current branch when it is a queue "
                              "branch, else main_branch)")
    p_claim.add_argument("--dry-run", action="store_true", help="print the pick, do not create/push a branch")
    p_claim.set_defaults(func=cmd_claim)

    p_merge = sub.add_parser(
        "merge", help="merge a validated item per git.mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Lands the item's claim branch on its base per git.mode, re-runs "
            "the suite and `aide check`, writes the \u2705 and appends one "
            "ledger row.\n"
            "\n"
            "The row is one per item, in docs/aide/ledger.md \u2014 created "
            "from .aide/templates/ledger.md the first time there is a row to "
            "write, and committed together with the \u2705 so the two can "
            "never disagree. Every cell is derived here: the item, its queue, "
            "its stage, its kind \u2014 validate-stage from an item titled "
            "`Validate stage N`, maintenance from an inbox entry ticked with "
            "this item's number, else normal \u2014 how many acceptance "
            "criteria its spec "
            "carries, how many test functions and files the branch added "
            "against the base this run resolved \u2014 less the tests "
            "`aide scope` reports as reconciled in another item's test file, "
            "which are that item's \u2014 the engine version and "
            "today's date. The exceptions are --rounds and --findings, which "
            "no document holds and only the caller has.\n"
            "\n"
            "A count nobody passed is a blank cell and never a 0 \u2014 an "
            "unrecorded run must not read as a cheap one \u2014 and a cell "
            "nothing could measure is blank for the same reason, so an item "
            "whose spec or branch has gone still gets its row. Under pr mode "
            "this verb pushes and stops, so it writes neither the tick nor a "
            "row. A ledger write that fails is reported after the merge and "
            "never changes the exit code: the merge landed, and capture is "
            "worth a sentence rather than an item. An item stopped at the "
            "validation-round cap never reaches this verb, and "
            "`aide ledger abandon` writes its row instead.\n"
            "\n"
            "The finding cells read [loop] review, from aide.toml. Where it "
            "is off no reviewer ran, so the three of them are written as `-` "
            "rather than left blank, and a blank in them means a count that "
            "should have been passed and was not. --findings passed anyway "
            "under off wins over the mark, since a count is a claim its "
            "caller made. Where review is on and --findings is absent the "
            "run warns on stderr, writes the row and still exits 0. The "
            "counts are of in-scope findings; one outside the item is an "
            "insights.md line and no cell here."))
    p_merge.add_argument("number", type=int)
    p_merge.add_argument("branch", nargs="?", default=None, help="claim branch (default: found from number)")
    p_merge.add_argument("--base", default=None,
                         help="merge into this ref (default: what the claim "
                              "recorded, else main_branch)")
    p_merge.add_argument("--no-test", action="store_true",
                         help="skip the post-merge test run; the aide check "
                              "gate beside it still runs, and an error in it "
                              "still refuses the tick and the push")
    p_merge.add_argument("--no-commit", action="store_true",
                         help="do not commit the progress.md status the merge "
                              "records, nor the ledger row beside it")
    p_merge.add_argument("--rounds", type=_non_negative_argument, default=None,
                         help="build\u2194validate rounds this item took, for "
                              "the ledger row (absent: a blank cell)")
    p_merge.add_argument("--findings", type=_findings_argument, default=None,
                         help="review findings by rank for the ledger row: "
                              "blocking=A,minor=B,nit=C \u2014 any subset, "
                              "any order")
    p_merge.set_defaults(func=cmd_merge)

    p_env = sub.add_parser("env", help="venv health (exists, bootstrap finished, "
                                        "interpreter matches, imports, test runner) + bootstrap")
    p_env.add_argument("--bootstrap", action="store_true",
                       help="create + populate the venv if missing/stale, from "
                            "[python] interpreter when set")
    p_env.add_argument("--profile", default=None,
                       help="evaluate a named [validation] environment profile "
                            "(exit 0 iff satisfied; one that runs past "
                            f"{PROFILE_TIMEOUT}s or cannot start is not satisfied)")
    p_env.set_defaults(func=cmd_env)

    p_sync = sub.add_parser("sync", help="preflight: fetch, verify clean tree, land on the right branch")
    p_sync.add_argument("--item", type=int, default=None,
                        help="verify/switch to this item's claim branch")
    p_sync.set_defaults(func=cmd_sync)

    p_gc = sub.add_parser(
        "gc", help="delete claim branches whose work has landed (dry-run by default)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Deletes claim branches, local and remote, whose item is \u2705 in "
            "progress.md, and with --merged also branches already merged into "
            "the base. On the \u2705 ground a branch goes only when "
            "`git merge-tree --write-tree` says merging it into the base would "
            "change nothing; a branch that still carries unlanded content is "
            "skipped with the base named, unless --abandon. merge-tree "
            "--write-tree needs git >= 2.38: on older git the \u2705 ground "
            "refuses rather than falling back to a weaker test.\n"
            "\n"
            "Every skip \u2014 checked out, unlanded, unmeasurable (a ref the "
            "oracle could not read), git too old \u2014 is decided "
            "before anything is printed and shown as `skipping <branch> "
            "(local | remote | local+remote): <reason>` on both paths, so the "
            "dry run is exactly the set --yes "
            "deletes."))
    p_gc.add_argument("--merged", action="store_true",
                      help="also delete claim branches already merged into the base")
    p_gc.add_argument("--base", default=None,
                      help="ref --merged is measured against (default: the "
                           "current branch's recorded base, else main_branch)")
    p_gc.add_argument("--abandon", action="store_true",
                      help="delete a ✅ item's branch even though its content "
                           "is not in the base — for a genuinely abandoned claim")
    p_gc.add_argument("--yes", action="store_true", help="actually delete (default: dry run)")
    p_gc.set_defaults(func=cmd_gc)

    p_status = sub.add_parser(
        "status", help="one-call roadmap-state report (branch, queues, "
        "claims, PRs, open gates, unmet targets, unverified capabilities, "
        "retracted criteria)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "A \U0001f50d item's claim branch is reported as awaiting review, "
            "never as stale and never with a `gc` recommendation \u2014 that "
            "would be recommending the deletion of an open PR's head branch. "
            "Because in `pr` mode nothing inside the loop observes the merge, "
            "status (like `aide sync`) also names any \U0001f50d item whose "
            "work has since landed in the base that claim recorded (or "
            "`--base`), or in main_branch, by the same merge-tree "
            "comparison `gc` uses, and prints the `aide progress set NNN done` "
            "that closes it. Those bases are the local branches, never "
            "origin/<base>: a merge made on the forge is seen once that branch "
            "is pulled, not by the fetch alone. Every human gate still "
            "blocking, every Outcome "
            "target not yet \u2705 Met, every retracted acceptance "
            "criterion and every progress.md table row no reader can use is "
            "printed too, so none of them lives only in one commit's diff. "
            "So is every environment-gated capability not yet ✅ "
            "Verified, with the [validation] profile its Package / Tool cell "
            "names. With --profiles, each profile a ❓ Unverified row names "
            "is evaluated once, as `aide env --profile` evaluates it (the "
            "expression only, never the gated tests), and reported satisfied "
            "or not; one that times out or cannot start is not satisfied — "
            "a satisfied profile under an unverified row is a row this "
            "machine can verify now."))
    p_status.add_argument("--no-fetch", action="store_true", help="skip the fetch --all --prune preflight")
    p_status.add_argument("--profiles", action="store_true",
                          help="evaluate the [validation] profile each "
                               "❓ Unverified capability row names (each "
                               f"bounded by {PROFILE_TIMEOUT}s)")
    p_status.add_argument("--base", default=None,
                          help="ref to report ahead/behind against, and to "
                               "measure every \U0001f50d claim's landed work "
                               "against before main_branch (default: the current "
                               "branch's recorded base for ahead/behind, each "
                               "claim's own for landed work; else main_branch)")
    p_status.set_defaults(func=cmd_status)

    p_scope = sub.add_parser(
        "scope", help="check this branch's diff against the item's authorised paths",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Diffs the branch against the merge-base with the item's base and "
            "reports every changed path outside the spec's ## Authorised paths; "
            "a path listed under Asserts against and then changed is reported "
            "separately. With no number the item is read from the current "
            "claim branch, and a queue branch resolves to no item and is "
            "skipped. The base is --base if given, else the branch's recorded "
            "base, else main_branch; the two derived answers prefer "
            "origin/<base> over the local ref.\n"
            "\n"
            "Also warns, never fails, on traceability: every test function the "
            "branch added under tests_dir must name an AC number the spec's "
            "## Acceptance Criteria carries (ac3) or a case label its "
            "## Testing Strategy names (the first word of a bullet, closed by a "
            "colon: `empty-input: ...`); a test naming neither is reported as "
            "one the spec did not ask for. A function present in the file at "
            "the base is an edit, not an addition, and is not checked, a "
            "renamed file being read under its old name; a spec with no "
            "## Acceptance Criteria heading is a notice and no warnings.\n"
            "\n"
            "A test file named test_NNN_<topic>.py for an item other than the "
            "one scoped is item NNN's, changed here to reconcile it: its added "
            "tests trace against item NNN's spec instead, and the scoped spec "
            "is not read for them. The ones that trace are reported as "
            "reconciled, in one notice per item, and not warned on; the rest "
            "warn, naming item NNN's spec. Where item NNN has no spec, or none "
            "with an ## Acceptance Criteria heading, the file is read as the "
            "scoped item's own.\n"
            "\n"
            "Exit 0: in scope, or nothing to check (a queue branch). 1: "
            "something changed outside it. 2: could not check (no spec, no "
            "section, or no base to diff against)."))
    p_scope.add_argument("number", type=int, nargs="?", default=None,
                         help="item number (default: read from the current claim branch)")
    p_scope.add_argument("--base", default=None,
                         help="base ref to diff against (default: the branch's "
                              "recorded base, else <main_branch>; derived answers "
                              "prefer origin/<base>, falling back to the local ref)")
    p_scope.set_defaults(func=cmd_scope)


def main(argv: Optional[List[str]] = None) -> int:
    # Windows consoles often default to a non-UTF-8 codepage (cp1252), where
    # printing a status icon raises UnicodeEncodeError and kills the command
    # instead of reporting. Reconfigure once here so no caller ever needs the
    # PYTHONIOENCODING env-var dance.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ConfigError as exc:
        # A broken aide.toml is a user-fixable state, not a crash. Every
        # subcommand loads the config, so catching it once here keeps the
        # traceback off the screen for all of them.
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
