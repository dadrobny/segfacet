"""Item 232: every report names the FACET revision that wrote it.

Tests for the ``facet_revision`` block in ``segfacet_report.json`` and
``eval_report.json`` and for the README's ``## Releasing`` section. Git calls
go through ``tests/run_process.run_utf8`` with no skip: the suite runs from a
git checkout, so a missing ``git`` must fail loudly.
"""

from __future__ import annotations

import functools
import json
import shutil
from pathlib import Path

import pytest

import segfacet
from segfacet import revision
from segfacet.cli import main
from segfacet.synth.corpus import CORPUS_DIR

from run_process import run_utf8

_PACKAGE_DIR = Path(segfacet.__file__).resolve().parent
_README = Path(__file__).resolve().parents[1] / "README.md"
_FIXTURES = CORPUS_DIR / "fixtures"


def _head(cwd):
    result = run_utf8(["git", "rev-parse", "HEAD"], cwd=cwd)
    assert result.returncode == 0
    sha = result.stdout.strip()
    assert len(sha) in (40, 64)
    return sha


def _run_report(out_dir):
    code = main(
        [
            "run",
            "--scan", str(_FIXTURES / "base_scan.nii.gz"),
            "--seg", str(_FIXTURES / "clean_control_seg.nii.gz"),
            "--out", str(out_dir),
            "--no-reference",
        ]
    )
    assert code in (0, 1)
    return json.loads((out_dir / "segfacet_report.json").read_text(encoding="utf-8"))


def _eval_report(tmp_path):
    shutil.copytree(_FIXTURES, tmp_path / "fixtures")
    manifest = tmp_path / "cohort.json"
    manifest.write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "cases": [
                    {
                        "case_id": "clean",
                        "gt": "fixtures/clean_control_seg.nii.gz",
                        "candidate": "fixtures/clean_control_seg.nii.gz",
                        "expected": {"expected_verdict": "pass"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "eval_out"
    code = main(
        [
            "evaluate",
            "--cohort", str(manifest),
            "--out", str(out_dir),
            "--build-date", "2026-07-12",
            "--cohort-id", "test",
        ]
    )
    assert code == 0
    return json.loads((out_dir / "eval_report.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def run_report(tmp_path_factory):
    return _run_report(tmp_path_factory.mktemp("run232"))


@pytest.fixture(scope="module")
def eval_report(tmp_path_factory):
    return _eval_report(tmp_path_factory.mktemp("eval232"))


@pytest.fixture
def untracked_package(monkeypatch, tmp_path):
    """Point the CLI's revision lookup at an empty, untracked directory."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    monkeypatch.setattr(
        revision,
        "facet_revision",
        functools.partial(revision.facet_revision, package_dir=pkg),
    )


def test_ac1_per_case_report_carries_checkout_commit(run_report):
    assert run_report["facet_revision"]["commit"] == _head(_PACKAGE_DIR)


def test_ac2_per_case_report_carries_package_version(run_report):
    assert run_report["facet_revision"]["package_version"] == segfacet.__version__


def test_ac3_eval_report_carries_checkout_commit(eval_report):
    assert eval_report["facet_revision"]["commit"] == _head(_PACKAGE_DIR)


def test_ac4_eval_report_carries_package_version(eval_report):
    assert eval_report["facet_revision"]["package_version"] == segfacet.__version__


def test_ac5_per_case_run_without_git_metadata_records_null_commit(
    untracked_package, tmp_path
):
    report = _run_report(tmp_path / "run")
    assert "facet_revision" in report
    assert report["facet_revision"]["commit"] is None


def test_ac6_eval_run_without_git_metadata_records_null_commit(
    untracked_package, tmp_path
):
    report = _eval_report(tmp_path)
    assert "facet_revision" in report
    assert report["facet_revision"]["commit"] is None


def test_ac7_readme_releasing_section_gives_tag_template_and_version_file():
    text = _README.read_text(encoding="utf-8")
    start = text.index("\n## Releasing")
    end = text.find("\n## ", start + 1)
    section = text[start : end if end != -1 else len(text)]
    assert "v<package_version>" in section
    assert "src/segfacet/__init__.py" in section
    init = (_PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
    assert f'__version__ = "{segfacet.__version__}"' in init


def test_cwd_independence(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    report = _run_report(tmp_path / "run")
    assert report["facet_revision"]["commit"] == _head(_PACKAGE_DIR)


def test_untracked_inside_a_work_tree(tmp_path):
    ident = ["-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"]
    for argv in (
        ["git", "init"],
        ["git", "add", "tracked.txt"],
        ["git", *ident, "commit", "-m", "init"],
    ):
        if argv[1] == "add":
            (tmp_path / "tracked.txt").write_text("x", encoding="utf-8")
        assert run_utf8(argv, cwd=tmp_path).returncode == 0
    # The repo has a commit, so an enclosing HEAD exists to be wrongly recorded.
    _head(tmp_path)
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    assert revision.facet_revision(package_dir=pkg)["commit"] is None


def test_no_git_on_path(monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", str(tmp_path))
    assert revision.facet_revision()["commit"] is None
