"""Tests for item 215 -- per-label fields migrated under the signed taxonomy.

Covers Acceptance Criteria AC1-AC3 from
``docs/aide/items/215-per-label-fields-migrated-under-the-signed-taxonomy.md``,
one test each, plus its two named adversarial cases:
``level-name-read-from-survivor`` and ``path-u-mapped-in-anatomical-order``.
The mapping table is read only through ``tests/feature_taxonomy_mapping.py``.
"""

from __future__ import annotations

import json

import nibabel as nib
import numpy as np
import pytest
from feature_taxonomy_mapping import read_mapping

from segfacet.catalogue import iter_leaf_paths
from segfacet.cli import main
from segfacet.config import bundled_default_config
from segfacet.pipeline import extract_feature_record
from segfacet.synth.corpus import CORPUS_DIR, load_manifest
from segfacet.synth.regression import loaded_seg_image, pipeline_findings

_CATALOGUE_JSON = (
    CORPUS_DIR.parent.parent / "docs" / "aide" / "feature_catalogue.generated.json"
)

_CONTAINER_PREFIXES = (
    "stage3.per_label_offsets[]",
    "stage3.per_label_orientations[]",
    "stage3.per_label_neighbourhood[]",
    "image_features.per_label.{label}.",
    "reference_delta.{label}.",
)

_NON_CONTENT_KEYS = (
    "schema_version",
    "config_version",
    "case_id",
    "verdict",
    "reasons",
    "per_label",
    "findings",
    "run_manifest",
)


def _case(case_id: str) -> dict:
    return next(c for c in load_manifest()["cases"] if c["case_id"] == case_id)


def _rows_215():
    return [r for r in read_mapping() if r[3] == 215]


def _catalogue_paths() -> set:
    cat = json.loads(_CATALOGUE_JSON.read_text(encoding="utf-8"))
    return {e["path"] for g in cat["groups"] for e in g["entries"]}


def _last_segment(path: str) -> str:
    tail = path.rsplit(".", 1)[-1]
    return tail[:-2] if tail.endswith("[]") else tail


@pytest.fixture(scope="module")
def case_report(tmp_path_factory):
    case = _case("clean_control")
    out = tmp_path_factory.mktemp("case_report_215")
    main(
        [
            "run",
            "--scan",
            str(CORPUS_DIR / case["scan_fixture"]),
            "--seg",
            str(CORPUS_DIR / case["seg_fixture"]),
            "--intensity",
            "--out",
            str(out),
        ]
    )
    return json.loads((out / "segfacet_report.json").read_text(encoding="utf-8"))


def _leaf_paths(report: dict) -> set:
    content = {k: v for k, v in report.items() if k not in _NON_CONTENT_KEYS}
    paths = iter_leaf_paths(content)
    return {p[len("features.") :] if p.startswith("features.") else p for p in paths}


# =========================================================================== #
# AC1-AC3
# =========================================================================== #


@pytest.mark.parametrize("key", ["label", "level_name"])
def test_ac1_each_identity_key_is_stored_at_exactly_one_path(case_report, key):
    leaves = _leaf_paths(case_report)
    assert leaves
    for prefix in _CONTAINER_PREFIXES:
        assert any(
            old.startswith(prefix) and change in ("kept", "moved") and new in leaves
            for old, new, change, _ in _rows_215()
        ), prefix
    assert len([p for p in leaves if _last_segment(p) == key]) == 1


def _assert_rows_recognisable(rows):
    for prefix in _CONTAINER_PREFIXES:
        assert any(old.startswith(prefix) for old, *_ in rows), prefix
    assert any(change == "merged" for _, _, change, _ in rows)


def test_ac2_every_path_this_item_keeps_or_moves_is_produced():
    rows = _rows_215()
    _assert_rows_recognisable(rows)
    new_paths = {new for _, new, change, _ in rows if change in ("kept", "moved")}
    assert new_paths
    assert new_paths - _catalogue_paths() == set()


def test_ac3_no_path_this_item_moves_or_merges_away_is_still_produced():
    rows = _rows_215()
    _assert_rows_recognisable(rows)
    all_new = {new for _, new, _, _ in read_mapping()}
    gone = {old for old, _, change, _ in rows if change in ("moved", "merged")}
    assert gone - all_new
    assert (gone - all_new) & _catalogue_paths() == set()


# =========================================================================== #
# Named adversarial cases
# =========================================================================== #


def test_level_name_read_from_survivor(case_report):
    report_reasons = [f["reason"] for f in case_report["findings"]]
    displace_reasons = [f.reason for f in pipeline_findings(_case("displace"))]
    assert report_reasons
    assert any(
        f.rule_id == "spline_offset" for f in pipeline_findings(_case("displace"))
    )
    for reason in report_reasons + displace_reasons:
        assert "None" not in reason, reason


def test_path_u_mapped_in_anatomical_order():
    clean = loaded_seg_image(_case("clean_control"))
    data = np.asarray(clean.dataobj)
    out = data.copy()
    # T13, L1, L2, L3, L4 head-to-tail.
    for src, dst in {20: 28, 21: 20, 22: 21, 23: 22, 24: 23}.items():
        out[data == src] = dst
    img = nib.Nifti1Image(out, clean.affine, clean.header, dtype=out.dtype)

    record = extract_feature_record(img, bundled_default_config())

    assert record["case"]["curve"]["is_monotonic"] is True
    per_label = {int(k): v for k, v in record["per_label"].items()}
    assert sorted(per_label) == [20, 21, 22, 23, 28]
    path_u = [per_label[label]["curve"]["path_u"] for label in (28, 20, 21, 22, 23)]
    assert all(b > a for a, b in zip(path_u, path_u[1:])), path_u
