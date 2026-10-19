"""Tests for item 231 -- the ``rl1`` review-label table read against a pinned
schema (``segfacet.eval.review_labels``), the test-role refusal in
``calibrate_thresholds``, and ``segfacet evaluate --review-labels``.

One test per AC, named ``test_acN_*``, and one per adversarial case the item
spec's Testing Strategy names, named for its label. Tables are written under
``tmp_path`` with the field list read from the vendored schema (AC3's subject
is the transcription itself, so it alone re-types the fields). Expected
expectations and metrics are recomputed from the live library calls.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import nibabel as nib
import pytest

from segfacet.cli import main
from segfacet.config import bundled_default_config
from segfacet.datasets import load_descriptor, resolve
from segfacet.eval.calibrate import (
    ThresholdAxis,
    calibrate_thresholds,
    default_calibration_axes,
)
from segfacet.eval.harness import EvaluationCase, evaluate_cohort
from segfacet.eval.label_outcome import label_mode_expectation
from segfacet.eval.metrics import compute_cohort_metrics
from segfacet.eval.review_labels import (
    apply_review_labels,
    load_rl1_schema,
    read_review_label_table,
)
from segfacet.failure_modes import SPECIFICATION
from segfacet.io import FacetInputError
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.corpus import build_corpus
from segfacet.synth.intensity import paint_clean_scan

_MODES = sorted(SPECIFICATION)
_MODE_A, _MODE_B = _MODES[0], _MODES[1]
_UNKNOWN_MODE = max(SPECIFICATION) + 1000


# =========================================================================== #
# Fixtures
# =========================================================================== #


def _field_names():
    return [f["name"] for f in load_rl1_schema()["fields"]]


def _row(**overrides):
    row = {
        "schema": "rl1",
        "case_id": "case-a",
        "run_id": "run-1",
        "mask_hash": "abc123",
        "label_id": 20,
        "mode_id": 0,
        "call": "pathology",
        "call_provenance": "",
        "reviewer": "rev-1",
        "role": "development",
    }
    row.update(overrides)
    return row


def _write_table(path, rows, *, header=None, eol="\n"):
    header = _field_names() if header is None else header
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator=eol)
        writer.writerow(header)
        for row in rows:
            writer.writerow([row.get(name, "x") for name in header])
    return path


def _valid_rows():
    return [
        _row(case_id="case-a", label_id=20, mode_id=_MODE_A, call_provenance="note"),
        _row(case_id="case-a", label_id=21, mode_id=0),
        _row(case_id="case-b", label_id=22, mode_id=0, role="test"),
    ]


def _case(case_id, **kwargs):
    return EvaluationCase(
        case_id=case_id,
        gt="placeholder.nii.gz",
        expected={"expected_verdict": "pass"},
        **kwargs,
    )


# =========================================================================== #
# Acceptance criteria
# =========================================================================== #


def test_ac1_schema_names_its_source():
    assert load_rl1_schema()["source"] == {
        "repository": "spine-failure-lab",
        "path": "docs/project/facet-interface.md",
        "table": "review-label-fields",
        "commit": "7436b0f250dd413c2358600d9ea4d1adcace8696",
    }


def test_ac2_schema_tag():
    assert load_rl1_schema()["schema"] == "rl1"


def test_ac3_schema_fields():
    fields = [(f["name"], f["type"]) for f in load_rl1_schema()["fields"]]
    assert fields == [
        ("schema", "string"),
        ("case_id", "string"),
        ("run_id", "string"),
        ("mask_hash", "string"),
        ("label_id", "integer"),
        ("mode_id", "integer"),
        ("call", "string"),
        ("call_provenance", "string or null"),
        ("reviewer", "string"),
        ("role", "string"),
    ]


def test_ac4_valid_table_read_row_by_row(tmp_path):
    rows = _valid_rows()
    got = read_review_label_table(_write_table(tmp_path / "t.csv", rows))
    assert len(rows) == 3
    assert len(got) == len(rows)
    assert [r["case_id"] for r in got] == [r["case_id"] for r in rows]
    assert all(set(r) == set(_field_names()) for r in got)


def test_ac5_integer_fields_are_ints(tmp_path):
    rows = _valid_rows()
    got = read_review_label_table(_write_table(tmp_path / "t.csv", rows))
    assert len(got) == len(rows)
    for want, read in zip(rows, got):
        assert type(read["label_id"]) is int and read["label_id"] == want["label_id"]
        assert type(read["mode_id"]) is int and read["mode_id"] == want["mode_id"]


def test_ac6_null_cell_is_none(tmp_path):
    rows = _valid_rows()
    got = read_review_label_table(_write_table(tmp_path / "t.csv", rows))
    assert [r["call_provenance"] for r in got] == ["note", None, None]
    for want, read in zip(rows, got):
        for name in ("schema", "case_id", "run_id", "mask_hash", "call", "reviewer", "role"):
            assert read[name] == want[name]


def test_ac7_another_schema_tag_refused(tmp_path):
    path = _write_table(tmp_path / "t.csv", [_row(), _row(schema="rl2")])
    with pytest.raises(FacetInputError) as err:
        read_review_label_table(path)
    assert "rl2" in str(err.value)
    assert "rl1" in str(err.value)


def test_ac8_unlisted_field_refused(tmp_path):
    path = _write_table(
        tmp_path / "t.csv", [_row(bogus_col="v")], header=_field_names() + ["bogus_col"]
    )
    with pytest.raises(FacetInputError, match="bogus_col"):
        read_review_label_table(path)


def test_ac9_missing_field_refused(tmp_path):
    header = [n for n in _field_names() if n != "reviewer"]
    assert len(header) == len(_field_names()) - 1
    path = _write_table(tmp_path / "t.csv", [_row()], header=header)
    with pytest.raises(FacetInputError, match="reviewer"):
        read_review_label_table(path)


@pytest.mark.parametrize("field", ["label_id", "mode_id"])
def test_ac10_non_integer_cell_refused(tmp_path, field):
    path = _write_table(tmp_path / "t.csv", [_row(**{field: "twenty"})])
    with pytest.raises(FacetInputError, match=field):
        read_review_label_table(path)


def test_ac11_unknown_role_refused(tmp_path):
    path = _write_table(tmp_path / "t.csv", [_row(role="Test")])
    with pytest.raises(FacetInputError, match="Test"):
        read_review_label_table(path)


def test_ac12_reviewed_case_gets_the_tables_expectation():
    rows = [
        _row(case_id="case-a", label_id=20, mode_id=_MODE_A),
        _row(case_id="case-a", label_id=21, mode_id=0),
        _row(case_id="case-b", label_id=22, mode_id=0),
    ]
    out = apply_review_labels([_case("case-a"), _case("case-b")], rows)
    assert len(out) == 2
    for case in out:
        pairs = [(r["label_id"], r["mode_id"]) for r in rows if r["case_id"] == case.case_id]
        assert case.expected == label_mode_expectation(pairs)


def test_ac13_reviewed_case_carries_its_role():
    rows = [
        _row(case_id="case-a", role="calibration"),
        _row(case_id="case-a", label_id=21, role="calibration"),
        _row(case_id="case-b", role="test"),
    ]
    out = apply_review_labels([_case("case-a"), _case("case-b")], rows)
    assert {c.case_id: c.metadata["role"] for c in out} == {
        "case-a": "calibration",
        "case-b": "test",
    }


def test_ac14_unreviewed_case_dropped():
    cases = [_case("c0"), _case("case-a"), _case("c2"), _case("case-b")]
    rows = [_row(case_id="case-b"), _row(case_id="case-a")]
    out = apply_review_labels(cases, rows)
    assert [c.case_id for c in out] == ["case-a", "case-b"]


def test_ac15_case_with_two_roles_refused():
    rows = [
        _row(case_id="case-a", label_id=20, role="development"),
        _row(case_id="case-a", label_id=21, role="test"),
    ]
    with pytest.raises(FacetInputError, match="case-a"):
        apply_review_labels([_case("case-a")], rows)


def test_ac16_calibration_refuses_test_role_case():
    cases = [_case("held-out", metadata={"role": "test"})]
    with pytest.raises(FacetInputError, match="held-out"):
        calibrate_thresholds(cases, bundled_default_config(), default_calibration_axes())


# --- AC17: the CLI scores the table ---------------------------------------- #


def _write_dataset(root: Path, subjects):
    """A VerSe-shaped tree: one subset folder holding the nested layout."""
    base = root / "dataset-verse19training"
    for i, sub in enumerate(subjects):
        spine = build_clean_spine(
            levels=("L1", "L2", "L3", "L4", "L5"),
            spacing=(1.0, 1.0, 1.0),
            curve_amplitude_mm=4.0 + i,
        )
        scan = paint_clean_scan(spine.seg_img, seed=i)
        d = base / "derivatives" / sub
        r = base / "rawdata" / sub
        d.mkdir(parents=True, exist_ok=True)
        r.mkdir(parents=True, exist_ok=True)
        nib.save(spine.seg_img, str(d / f"{sub}_seg-vert_msk.nii.gz"))
        nib.save(scan, str(r / f"{sub}_ct.nii.gz"))


def _write_descriptor(path: Path, data_root: Path) -> Path:
    # as_posix(): a native Windows path in a double-quoted YAML scalar is
    # parsed for backslash escapes.
    path.write_text(
        f'data_root: "{data_root.as_posix()}"\n'
        'seg: "derivatives/sub-*/**/*_seg-vert_msk.nii.gz"\n'
        'case_id: "(?P<id>sub-verse\\\\d+(?:_split-verse\\\\d+)?)_seg-vert_msk\\\\.nii\\\\.gz$"\n'
        'scan: "rawdata/{id}/{id}_ct.nii.gz"\n'
        'subsets:\n  training:\n    root: "dataset-verse19training"\n',
        encoding="utf-8",
    )
    return path


def test_ac17_cli_scores_the_table(tmp_path):
    subjects = ("sub-verse004", "sub-verse005", "sub-verse006")
    _write_dataset(tmp_path / "verse", subjects)
    desc = _write_descriptor(tmp_path / "d.yaml", tmp_path / "verse")
    table = _write_table(
        tmp_path / "labels.csv",
        [
            _row(case_id=subjects[0], label_id=20, mode_id=_MODE_A),
            _row(case_id=subjects[0], label_id=21, mode_id=0),
            _row(case_id=subjects[1], label_id=22, mode_id=0),
        ],
    )
    out = tmp_path / "eval"
    rc = main(
        [
            "evaluate", "--dataset-schema", str(desc), "--subset", "training",
            "--review-labels", str(table), "--out", str(out),
            "--cohort-id", "ac17", "--build-date", "2026-10-18",
        ]
    )
    assert rc == 0

    resolved = resolve(load_descriptor(desc), subset="training", role="gt")
    cases = [
        EvaluationCase(
            case_id=c.case_id, gt=c.seg_path, expected={"expected_verdict": "pass"}
        )
        for c in resolved
    ]
    assert len(cases) == len(subjects)
    scored = apply_review_labels(cases, read_review_label_table(table))
    assert [c.case_id for c in scored] == list(subjects[:2])
    want = compute_cohort_metrics(
        evaluate_cohort(scored, bundled_default_config())
    ).to_dict()["label_metrics"]
    assert want is not None

    report = json.loads((out / "eval_report.json").read_text(encoding="utf-8"))
    assert report["metrics"]["label_metrics"] == json.loads(json.dumps(want))


# =========================================================================== #
# Adversarial cases named by the Testing Strategy
# =========================================================================== #


def test_duplicate_column(tmp_path):
    path = _write_table(
        tmp_path / "t.csv", [_row()], header=_field_names() + ["mode_id"]
    )
    with pytest.raises(FacetInputError, match="mode_id"):
        read_review_label_table(path)


def test_crlf_table(tmp_path):
    rows = _valid_rows()
    lf = read_review_label_table(_write_table(tmp_path / "lf.csv", rows))
    crlf = read_review_label_table(_write_table(tmp_path / "crlf.csv", rows, eol="\r\n"))
    assert len(lf) == len(rows)
    assert crlf == lf


def test_empty_table(tmp_path):
    assert read_review_label_table(_write_table(tmp_path / "t.csv", [])) == []
    assert apply_review_labels([_case("case-a"), _case("case-b")], []) == []


def test_unknown_mode_row():
    rows = [_row(case_id="case-a", mode_id=_UNKNOWN_MODE)]
    with pytest.raises(FacetInputError, match="case-a"):
        apply_review_labels([_case("case-a")], rows)


def test_conflicting_reviews():
    rows = [
        _row(case_id="case-a", label_id=20, mode_id=0),
        _row(case_id="case-a", label_id=20, mode_id=_MODE_A),
    ]
    with pytest.raises(FacetInputError, match="case-a"):
        apply_review_labels([_case("case-a")], rows)


def test_row_outside_cohort():
    cases = [_case("case-a")]
    rows = [_row(case_id="case-a", label_id=20, mode_id=_MODE_B)]
    base = apply_review_labels(cases, rows)
    with_stray = apply_review_labels(cases, rows + [_row(case_id="elsewhere")])
    assert [c.case_id for c in base] == ["case-a"]
    assert with_stray == base


def test_metadata_kept():
    (out,) = apply_review_labels(
        [_case("case-a", metadata={"source": "x"})],
        [_row(case_id="case-a", role="calibration")],
    )
    assert out.metadata["source"] == "x"
    assert out.metadata["role"] == "calibration"


def test_calibration_role_allowed():
    corpus_case = build_corpus()[0]
    case = EvaluationCase(
        case_id=corpus_case.case_id,
        gt=corpus_case.seg_img,
        expected=corpus_case.expectation.to_dict(),
        metadata={"role": "calibration"},
    )
    axis = ThresholdAxis(
        name="lumbar_max_volume",
        rule_id="bounds",
        param_path=("lumbar", "max_volume_mm3"),
        values=(50000.0,),
    )
    result = calibrate_thresholds([case], bundled_default_config(), (axis,))
    assert result.n_candidates == 1


# =========================================================================== #
# Review finding: the CLI's error branches and the reader's hardening
# =========================================================================== #

_SUBJECTS = ("sub-verse004", "sub-verse005")


def _run_review_cli(tmp_path, rows, *extra):
    _write_dataset(tmp_path / "verse", _SUBJECTS)
    desc = _write_descriptor(tmp_path / "d.yaml", tmp_path / "verse")
    table = _write_table(tmp_path / "labels.csv", rows)
    out = tmp_path / "eval"
    rc = main(
        [
            "evaluate", "--dataset-schema", str(desc), "--subset", "training",
            "--review-labels", str(table), "--out", str(out),
            "--cohort-id", "rf", "--build-date", "2026-10-18", *extra,
        ]
    )
    return rc, out


def test_review_cli_no_matching_rows(tmp_path, capsys):
    rc, _ = _run_review_cli(tmp_path, [_row(case_id="elsewhere")])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error: no cohort case has a row in the --review-labels table." in err


def test_review_cli_calibrate_refuses_test_role(tmp_path, capsys):
    rc, out = _run_review_cli(
        tmp_path, [_row(case_id=_SUBJECTS[0], role="test")], "--calibrate"
    )
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error: threshold calibration: test-role case(s) [" in err
    assert _SUBJECTS[0] in err
    assert not (out / "eval_report.json").exists()


def test_review_reader_non_utf8_table(tmp_path):
    path = _write_table(tmp_path / "t.csv", [_row(reviewer="Zoë")])
    path.write_bytes(path.read_bytes().decode("utf-8").encode("latin-1"))
    with pytest.raises(FacetInputError):
        read_review_label_table(path)


def test_review_reader_bom_table(tmp_path):
    path = _write_table(tmp_path / "t.csv", _valid_rows())
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    assert len(read_review_label_table(path)) == len(_valid_rows())


@pytest.mark.parametrize("delta", ["extra", "short"])
def test_review_reader_ragged_row(tmp_path, delta):
    path = _write_table(tmp_path / "t.csv", [_row()])
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[1] = lines[1] + ",x" if delta == "extra" else lines[1].rsplit(",", 1)[0]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(FacetInputError, match="cell count differs from the header"):
        read_review_label_table(path)
