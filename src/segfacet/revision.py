"""FACET revision resolver (item 232).

``facet_revision()`` names the code that wrote a report:
``{"commit": <hex SHA or None>, "package_version": segfacet.__version__}``.
The commit is ``HEAD`` of the git work tree that *tracks the imported
package's own source* (not the process cwd), and ``None`` when no work tree
tracks it, ``git`` is absent, or a git call fails. It never raises.

Scope fence: no tagging, no dirty-tree detection, no wall clock. stdlib only.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import segfacet

__all__ = ["facet_revision"]

_SHA = re.compile(r"^([0-9a-f]{40}|[0-9a-f]{64})$")


def _git(args: list, cwd: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            encoding="utf-8",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def facet_revision(package_dir: Optional["os.PathLike"] = None) -> dict:
    """Return the ``facet_revision`` report block (see module docstring)."""
    pkg = Path(package_dir) if package_dir is not None else Path(segfacet.__file__).resolve().parent
    commit = None
    if _git(["ls-files", "--error-unmatch", "__init__.py"], pkg) is not None:
        sha = _git(["rev-parse", "HEAD"], pkg)
        if sha is not None and _SHA.match(sha):
            commit = sha
    return {"commit": commit, "package_version": segfacet.__version__}
