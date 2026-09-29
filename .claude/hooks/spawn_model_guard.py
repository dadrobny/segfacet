#!/usr/bin/env python
"""Claude Code hook: a helper a role spawns runs on a model chosen, not inherited.

Registered on ``PreToolUse`` for ``Agent`` (and ``Task``, its earlier name) in
``.claude/settings.json``. Every role definition pins an exact model, so one
installed version means one model set. A helper the role spawns in turn sits
outside that pin: a built-in agent type (``Explore``, ``general-purpose``,
``Plan``) declares no model and inherits its caller's, so a strongest-tier
role that delegates a grep sweep runs the sweep on the strongest tier too —
issue #311, where one ``spec-author`` spawned 23 ``Explore`` helpers, all on
the role's model, the largest single consumer in the session. The per-call
``model`` parameter is the one place the choice can be made; this hook makes
the role make it.

Contract:
- Reads the PreToolUse hook JSON on stdin (``tool_name``, ``tool_input``,
  ``agent_id`` …).
- Denies the spawn when **all** of these hold, by writing a
  ``hookSpecificOutput`` with ``permissionDecision: "deny"`` to **stdout** and
  exiting 0 — the reason reaches the calling agent, which re-issues the call:

  * the caller is itself a sub-agent — the payload carries ``agent_id``, which
    the runtime sets only inside one, so the user's own session and the
    orchestrator it runs are never touched;
  * ``tool_input.model`` is absent, empty or ``inherit``;
  * the target type pins no model of its own. A type pins one when a
    definition under ``<project>/.claude/agents/`` declares it as its
    ``name:`` — the key the runtime dispatches on, which the file name need
    not match — and sets ``model:`` to anything but ``inherit``. Only when no
    definition declares the name is ``<type>.md`` read instead. A missing
    ``subagent_type`` is ``general-purpose``. The built-ins, a user-level or
    plugin agent, and any name that is not a plain file stem resolve to
    nothing, so they need an explicit model: a deny costs one re-issued call,
    an inherited model costs the whole helper's run.
- Otherwise writes nothing and exits 0 (no opinion).

Design rules:
- **Fail-open, like its companion hooks.** A parse error, an unexpected
  payload shape or an internal exception exits 0 in silence: a guard bug must
  never wedge a run, and the worst case is the inherited model this hook
  exists to prevent, never a blocked call.
- **The reason names the fix.** A deny with no way forward stalls a role; this
  one says which model to pass for which kind of helper.
"""

import json
import os
import re
import sys

#: The tool that spawns a sub-agent, under its current and its earlier name.
_SPAWN_TOOLS = ("Agent", "Task")

#: What the runtime dispatches when a spawn names no type.
_DEFAULT_TYPE = "general-purpose"

#: A type that can name a file under ``.claude/agents/`` — a plain stem. A
#: separator, a ``..`` or a plugin's ``plugin:agent`` form names no project
#: file, and must not be allowed to open one somewhere else.
_PLAIN_STEM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def _explicit_model(tool_input):
    """The model the call asks for, or ``None`` when it would inherit."""
    model = tool_input.get("model")
    if not isinstance(model, str):
        return None
    model = model.strip()
    if not model or model.lower() == "inherit":
        return None
    return model


def _project_dir(payload):
    """The project root the runtime names, else the session's cwd."""
    root = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd")
    return root if isinstance(root, str) and root else os.getcwd()


def _frontmatter(path):
    """The top-level scalar keys of a definition's frontmatter, quotes
    stripped, or ``None`` when the file has no frontmatter block."""
    try:
        with open(path, encoding="utf-8-sig") as fh:
            lines = fh.read().splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    if not lines or lines[0].strip() != "---":
        return None
    keys = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return keys
        if line[:1].isspace() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        keys.setdefault(key.strip(), value.strip().strip("\"'").strip())
    return None


def _definitions(agent_type, project_dir):
    """The frontmatter of every project definition *agent_type* dispatches to.

    The runtime resolves a type by the definition's ``name:``, and the file
    name need not agree, so every ``.claude/agents/*.md`` declaring that name
    is one. Only when none does is ``<agent_type>.md`` read, for a definition
    that leaves ``name:`` out.
    """
    agents_dir = os.path.join(project_dir, ".claude", "agents")
    try:
        entries = sorted(os.listdir(agents_dir))
    except OSError:
        return []
    parsed = []
    for entry in entries:
        path = os.path.join(agents_dir, entry)
        if entry.endswith(".md") and os.path.isfile(path):
            keys = _frontmatter(path)
            if keys is not None:
                parsed.append((entry[:-3], keys))
    named = [keys for _stem, keys in parsed if keys.get("name") == agent_type]
    if named:
        return named
    return [keys for stem, keys in parsed if stem == agent_type]


def pins_its_own_model(agent_type, project_dir):
    """Whether *agent_type* is a project definition that pins a model.

    Two definitions declaring one name are ambiguous, so both must pin one: a
    spawn that could land on either is safe only if neither inherits.
    """
    if not _PLAIN_STEM.match(agent_type) or ".." in agent_type:
        return False
    found = _definitions(agent_type, project_dir)
    return bool(found) and all(
        keys.get("model") and keys["model"].lower() != "inherit"
        for keys in found)


def _reason(agent_type):
    return (
        "Spawn refused: you are a sub-agent, and `" + agent_type + "` pins no "
        "model of its own, so this helper would run on your model by "
        "inheritance - outside the model set your role is pinned to. Re-issue "
        "the same call with an explicit `model`: \"haiku\" for a pure "
        "search/read sweep (grep, glob, reading files and reporting what is "
        "there), \"sonnet\" for a helper that has to judge or write, and "
        "\"opus\" only as a deliberate choice. Or do the work yourself: a "
        "search you can run in a few tool calls needs no helper."
    )


def decide(payload, project_dir=None):
    """The deny reason for *payload*, or ``None`` to have no opinion."""
    if not isinstance(payload, dict):
        return None
    if payload.get("tool_name") not in _SPAWN_TOOLS:
        return None
    agent_id = payload.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id.strip():
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    if _explicit_model(tool_input) is not None:
        return None
    agent_type = tool_input.get("subagent_type")
    if not isinstance(agent_type, str) or not agent_type.strip():
        agent_type = _DEFAULT_TYPE
    agent_type = agent_type.strip()
    if project_dir is None:
        project_dir = _project_dir(payload)
    if pins_its_own_model(agent_type, project_dir):
        return None
    return _reason(agent_type)


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return
    reason = decide(json.loads(raw))
    if reason is None:
        return
    # ASCII-only JSON (``ensure_ascii``), so a Windows console codepage cannot
    # change the bytes the runtime reads back.
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Fail-open: never let a guard bug block or wedge a real tool call.
        pass
    sys.exit(0)
