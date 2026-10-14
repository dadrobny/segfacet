"""Item 226 -- two owner-decided retirements (2026-10-09).

``segfacet.features.sagittal_projection`` (item 021) and the CI ``scope-check``
job (items 107/117) are retired, and the live text that described them is
corrected. AC3 (the status-report QC placeholder) lives in
``tests/test_aide_status_report.py`` beside the other ``render_html`` tests.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CI_YML = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
_CLAUDE_MD = _REPO_ROOT / "CLAUDE.md"
_REVIEW_MD = _REPO_ROOT / "REVIEW.md"

_MODULE = "segfacet.features.sagittal_projection"


def _imports_module(source: str) -> bool:
    """True if ``source`` imports ``_MODULE`` in any absolute form."""
    package, _, leaf = _MODULE.rpartition(".")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            if any(a.name == _MODULE for a in node.names):
                return True
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if node.module == _MODULE:
                return True
            if node.module == package and any(a.name == leaf for a in node.names):
                return True
    return False


def _scope_verb_steps(workflow: dict) -> list[str]:
    """Every step ``run`` value, in any job, that invokes ``aide.py scope``."""
    hits = []
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            run = step.get("run", "")
            if "aide.py scope" in run:
                hits.append(run)
    return hits


def _load_ci() -> dict:
    return yaml.safe_load(_CI_YML.read_text(encoding="utf-8"))


def test_ac1_the_module_is_gone():
    assert importlib.util.find_spec(_MODULE) is None


def test_ac2_nothing_imports_it():
    files = [
        p
        for top in ("src", "tests", "scripts")
        for p in sorted((_REPO_ROOT / top).rglob("*.py"))
    ]
    assert files, "expected python files under src/, tests/ and scripts/"
    hits = [str(p) for p in files if _imports_module(p.read_text(encoding="utf-8"))]
    assert not hits, f"modules still import {_MODULE}: {hits}"


def test_import_from_package_form_is_reported_by_the_sweep():
    assert _imports_module("from segfacet.features import sagittal_projection")


def test_ac4_the_workflow_has_no_scope_check_job():
    jobs = _load_ci()["jobs"]
    assert jobs, "expected at least one job in ci.yml"
    assert "scope-check" not in jobs


def test_ac5_no_ci_step_runs_the_scope_verb():
    assert _scope_verb_steps(_load_ci()) == []


def test_renamed_job_is_reported_by_the_step_scan():
    planted = {
        "jobs": {
            "scope-gate": {"steps": [{"run": "python .aide/scripts/aide.py scope 042"}]}
        }
    }
    assert _scope_verb_steps(planted) == ["python .aide/scripts/aide.py scope 042"]


def test_ac6_claude_md_no_longer_describes_the_job():
    text = _CLAUDE_MD.read_text(encoding="utf-8")
    assert text, "CLAUDE.md unexpectedly empty"
    assert "scope-check" not in text
    assert "item scope check" not in text


def test_ac7_claude_md_names_the_in_loop_scope_gate():
    text = _CLAUDE_MD.read_text(encoding="utf-8")
    match = re.search(r"^## Branching.*?(?=^## |\Z)", text, re.DOTALL | re.MULTILINE)
    assert match, "no '## Branching' section in CLAUDE.md"
    paragraphs = re.split(r"\n\s*\n", match.group(0))
    assert any("aide scope" in p and "validator" in p for p in paragraphs)


def test_ac8_review_md_no_longer_names_the_job():
    text = _REVIEW_MD.read_text(encoding="utf-8")
    assert text, "REVIEW.md unexpectedly empty"
    assert "scope-check" not in text
