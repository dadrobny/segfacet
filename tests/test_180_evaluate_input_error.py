"""Tests for item 180 -- ``segfacet evaluate`` reports a ``FacetInputError``
raised during ``evaluate_cohort`` (e.g. a candidate/GT shape mismatch) as a
clean ``Error: <message>`` on stderr with exit code 1, the way ``_handle_run``
already reports ``load_case`` errors and ``_handle_evaluate`` already reports
``load_cohort_manifest`` errors -- instead of letting the exception escape as
an uncaught traceback (``docs/aide/items/180-segfacet-evaluate-reports-an-input-error.md``).

The cohort below has two cases: case 1 (``clean``) pairs a candidate with a
GT of the same shape and evaluates cleanly; case 2 (``mismatched``) pairs a
candidate with a GT of a different shape, which fails inside
``compute_overlap`` after case 1 has already been evaluated -- the position
where a partially built report could otherwise leak out.
"""

from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from synthetic import make_labelmap, write_nifti

from segfacet.io import FacetInputError

_BLOCKS = {1: ((2, 6), (2, 6), (2, 6))}
_SAME_SHAPE = (16, 16, 16)
_DIFFERENT_SHAPE = (12, 16, 16)


def _write_manifest(tmp_path: Path) -> Path:
    """Write the two-case cohort manifest and its four label maps under
    ``tmp_path``, and return the manifest path."""
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()

    write_nifti(make_labelmap(_SAME_SHAPE, _BLOCKS), fixtures / "case1_gt_seg.nii.gz")
    write_nifti(
        make_labelmap(_SAME_SHAPE, _BLOCKS), fixtures / "case1_candidate_seg.nii.gz"
    )
    write_nifti(make_labelmap(_SAME_SHAPE, _BLOCKS), fixtures / "case2_gt_seg.nii.gz")
    write_nifti(
        make_labelmap(_DIFFERENT_SHAPE, _BLOCKS),
        fixtures / "case2_candidate_seg.nii.gz",
    )

    manifest = {
        "manifest_version": 1,
        "cases": [
            {
                "case_id": "clean",
                "gt": "fixtures/case1_gt_seg.nii.gz",
                "candidate": "fixtures/case1_candidate_seg.nii.gz",
                "expected": {"expected_verdict": "pass"},
            },
            {
                "case_id": "mismatched",
                "gt": "fixtures/case2_gt_seg.nii.gz",
                "candidate": "fixtures/case2_candidate_seg.nii.gz",
                "expected": {"expected_verdict": "pass"},
            },
        ],
    }
    manifest_path = tmp_path / "cohort.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def _expected_compute_overlap_message(tmp_path: Path) -> str:
    """Recompute the exact message ``compute_overlap`` raises on case 2's
    candidate/GT arrays, so the test never hand-copies the message text."""
    from segfacet.eval.overlap import compute_overlap

    fixtures = tmp_path / "fixtures"
    candidate_arr = np.asanyarray(
        nib.load(str(fixtures / "case2_candidate_seg.nii.gz")).dataobj
    )
    gt_arr = np.asanyarray(nib.load(str(fixtures / "case2_gt_seg.nii.gz")).dataobj)

    with pytest.raises(FacetInputError) as excinfo:
        compute_overlap(candidate_arr, gt_arr)
    return str(excinfo.value)


# =========================================================================== #
# AC1: exit code 1
# =========================================================================== #


def test_ac1_exit_code_one(tmp_path):
    from segfacet import cli

    manifest_path = _write_manifest(tmp_path)
    out_dir = tmp_path / "out"

    exit_code = cli.main(
        ["evaluate", "--cohort", str(manifest_path), "--out", str(out_dir)]
    )

    assert exit_code == 1


# =========================================================================== #
# AC2: the error message on stderr
# =========================================================================== #


def test_ac2_error_message_on_stderr(tmp_path, capsys):
    from segfacet import cli

    manifest_path = _write_manifest(tmp_path)
    out_dir = tmp_path / "out"
    expected_message = _expected_compute_overlap_message(tmp_path)

    cli.main(["evaluate", "--cohort", str(manifest_path), "--out", str(out_dir)])

    captured = capsys.readouterr()
    assert f"Error: {expected_message}" in captured.err


# =========================================================================== #
# AC3: no report written
# =========================================================================== #


def test_ac3_no_report_written(tmp_path):
    from segfacet import cli

    manifest_path = _write_manifest(tmp_path)
    out_dir = tmp_path / "out"

    cli.main(["evaluate", "--cohort", str(manifest_path), "--out", str(out_dir)])

    assert not (out_dir / "eval_report.json").exists()
    assert not (out_dir / "eval_report.txt").exists()


# =========================================================================== #
# Adversarial case: a non-input error still propagates as a traceback
# =========================================================================== #


def test_non_input_error_propagates(tmp_path, monkeypatch):
    from segfacet import cli
    import segfacet.eval.harness as harness_module

    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    write_nifti(make_labelmap(_SAME_SHAPE, _BLOCKS), fixtures / "gt_seg.nii.gz")
    manifest = {
        "manifest_version": 1,
        "cases": [
            {
                "case_id": "only",
                "gt": "fixtures/gt_seg.nii.gz",
                "expected": {"expected_verdict": "pass"},
            }
        ],
    }
    manifest_path = tmp_path / "cohort.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    out_dir = tmp_path / "out"

    def _raise_runtime_error(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(harness_module, "evaluate_cohort", _raise_runtime_error)

    with pytest.raises(RuntimeError):
        cli.main(["evaluate", "--cohort", str(manifest_path), "--out", str(out_dir)])
