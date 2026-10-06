"""Tests for item 216 -- neighbour-pair and case-level fields migrated.

Covers Acceptance Criteria AC1-AC9 from
``docs/aide/items/216-neighbour-pair-and-case-level-fields-migrated.md``, one
test each, plus its four named adversarial cases:
``unknown-label-still-judged``, ``stage3-unavailable-not-judged``,
``tangent-arrays-on-their-own-label`` and ``out-of-order-labels-unchanged``.
The mapping table is read only through ``tests/feature_taxonomy_mapping.py``.
The module drives the CLI in-process and reads its output back from disk.
"""

from __future__ import annotations

import copy
import json
import re
import statistics
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
from feature_taxonomy_mapping import read_mapping

import segfacet
from segfacet.catalogue import iter_leaf_paths
from segfacet.cli import main
from segfacet.config import bundled_default_config
from segfacet.features.centroids import compute_centroid
from segfacet.features.relationships import compute_spine_relationships
from segfacet.heuristics.fused_label import FusedLabelRule
from segfacet.labels import CANONICAL_ORDER
from segfacet.heuristics.overlap import OverlapRule
from segfacet.pipeline import extract_feature_record, run_qc
from segfacet.report import serialize_report
from segfacet.synth.corpus import CORPUS_DIR, load_manifest
from segfacet.synth.regression import loaded_seg_image

_CATALOGUE_JSON = (
    CORPUS_DIR.parent.parent / "docs" / "aide" / "feature_catalogue.generated.json"
)
_SCHEMA_JSON = Path(segfacet.__file__).resolve().parent / "report_schema_v0.json"

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

_MONOTONIC_NAMES = ("is_monotonic", "non_monotonic_pairs", "path_u")


def _case(case_id: str) -> dict:
    return next(c for c in load_manifest()["cases"] if c["case_id"] == case_id)


def _new(old: str) -> str:
    matches = [new for o, new, _, _ in read_mapping() if o == old]
    assert len(matches) == 1, old
    return matches[0]


def _catalogue_paths() -> set:
    cat = json.loads(_CATALOGUE_JSON.read_text(encoding="utf-8"))
    return {e["path"] for g in cat["groups"] for e in g["entries"]}


def _run_report(tmp_path_factory, case_id: str, *flags: str) -> dict:
    case = _case(case_id)
    out = tmp_path_factory.mktemp(f"report_216_{case_id}")
    main(
        [
            "run",
            "--scan",
            str(CORPUS_DIR / case["scan_fixture"]),
            "--seg",
            str(CORPUS_DIR / case["seg_fixture"]),
            *flags,
            "--out",
            str(out),
        ]
    )
    return json.loads((out / "segfacet_report.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def clean_report(tmp_path_factory):
    return _run_report(tmp_path_factory, "clean_control", "--intensity")


@pytest.fixture(scope="module")
def break_report(tmp_path_factory):
    return _run_report(tmp_path_factory, "sequence_break", "--no-reference")


def _resolve(doc: dict, path: str, label=None) -> list:
    """Walk a catalogue-notation path through a report or a features record."""
    first = path.split(".")[0].removesuffix("[]")
    root = doc["features"] if "features" in doc and first in doc["features"] else doc
    nodes = [root]
    for seg in path.split("."):
        many = seg.endswith("[]")
        key = seg[:-2] if many else seg
        nxt = []
        for node in nodes:
            if key == "{label}":
                nxt.extend([node[str(label)]] if label is not None else node.values())
            elif many:
                nxt.extend(node[key])
            else:
                nxt.append(node[key])
        nodes = nxt
    return nodes


def _anatomical_sequence(doc: dict) -> list:
    features = doc["features"] if "features" in doc else doc
    labels = [int(k) for k in features["per_label"]]

    def key(label):
        (name,) = _resolve(doc, _new("per_label.{label}.level_name"), label)
        rank = CANONICAL_ORDER.index(name) if name in CANONICAL_ORDER else len(
            CANONICAL_ORDER
        )
        return (rank, label)

    return sorted(labels, key=key)


def _centroid(doc: dict, label: int) -> np.ndarray:
    path = _new("per_label.{label}.centroid.centroid_mm[]")
    return np.array(_resolve(doc, path, label), dtype=float)


def _variant(case_id: str, remap: dict) -> nib.Nifti1Image:
    base = loaded_seg_image(_case(case_id))
    data = np.asarray(base.dataobj)
    out = data.copy()
    for src, dst in remap.items():
        out[data == src] = dst
    return nib.Nifti1Image(out, base.affine, base.header, dtype=out.dtype)


def _fused_label_sets(img) -> list:
    result, _ = run_qc(img, bundled_default_config())
    return [f.labels for f in result.findings if f.rule_id == "fused_label"]


def _containers(paths) -> set:
    return {p.split(".")[0].removesuffix("[]") for p in paths}


def _delete(record: dict, path: str) -> None:
    parts = [p.removesuffix("[]") for p in path.split(".")]
    node = record
    for part in parts[:-1]:
        node = node[part]
    del node[parts[-1]]


def _wrapped_diff(a: float, b: float) -> float:
    return abs(((a - b + 180) % 360) - 180)


# =========================================================================== #
# AC1-AC9
# =========================================================================== #


def test_ac1_catalogue_paths_are_exactly_the_tables_stored_paths():
    rows = read_mapping()
    assert len([r for r in rows if r[3] == 216]) == 35
    assert {r[3] for r in rows} == {215, 216}
    catalogue = _catalogue_paths()
    assert catalogue
    stored = {new for _, new, change, _ in rows if change in ("kept", "moved")}
    stored.add("case.sequence.order[]")
    assert catalogue == stored


def test_ac2_every_top_level_container_is_one_the_table_populates(clean_report):
    content = {k: v for k, v in clean_report.items() if k not in _NON_CONTENT_KEYS}
    leaves = {
        p[len("features.") :] if p.startswith("features.") else p
        for p in iter_leaf_paths(content)
    }
    report_containers = _containers(leaves)
    assert len(report_containers) >= 2
    table_containers = _containers(
        new for _, new, change, _ in read_mapping() if change in ("kept", "moved")
    )
    assert report_containers == table_containers


def test_ac3_survivor_holds_anatomical_order_spacings(break_report):
    sequence = _anatomical_sequence(break_report)
    assert sequence != sorted(sequence)
    expected = [
        float(np.linalg.norm(_centroid(break_report, b) - _centroid(break_report, a)))
        for a, b in zip(sequence, sequence[1:])
    ]
    survivor = _resolve(break_report, _new("relationships.neighbour_spacings_mm[]"))
    assert len(survivor) == len(sequence) - 1
    assert survivor == pytest.approx(expected, abs=1e-9)


def test_ac4_spacing_deviations_are_derived_from_the_survivor(break_report):
    sequence = _anatomical_sequence(break_report)
    assert sequence != sorted(sequence)
    survivor = _resolve(break_report, _new("relationships.neighbour_spacings_mm[]"))
    assert len(survivor) == len(sequence) - 1
    mean = statistics.fmean(survivor)
    deviations = _resolve(
        break_report, _new("stage3.spacing_consistency.deviations_mm[]")
    )
    assert deviations == pytest.approx([s - mean for s in survivor], abs=1e-9)


def test_ac5_fused_label_pairs_each_spacing_with_anatomically_adjacent_labels():
    t13_variant = _variant("fuse_adjacent", {20: 28})
    record = extract_feature_record(t13_variant, bundled_default_config())
    assert _anatomical_sequence(record) != sorted(int(k) for k in record["per_label"])
    unmodified = loaded_seg_image(_case("fuse_adjacent"))
    assert frozenset({22}) in _fused_label_sets(unmodified)
    assert _fused_label_sets(t13_variant) == [frozenset({22})]


def test_ac6_no_monotonic_description_calls_u_a_spline_parameter():
    schema = json.loads(_SCHEMA_JSON.read_text(encoding="utf-8"))
    described = set()
    descriptions = []

    def walk(node, name):
        if isinstance(node, dict):
            props = node.get("properties")
            owns = name in _MONOTONIC_NAMES or (
                isinstance(props, dict) and set(props) & set(_MONOTONIC_NAMES)
            )
            text = node.get("description")
            if isinstance(text, str) and owns:
                descriptions.append(text)
            for key, value in node.items():
                if key == "properties" and isinstance(value, dict):
                    for prop_name, prop in value.items():
                        if isinstance(prop, dict) and prop.get("description"):
                            described.add(prop_name)
                        walk(prop, prop_name)
                else:
                    walk(value, None)
        elif isinstance(node, list):
            for item in node:
                walk(item, None)

    walk(schema, None)
    assert set(_MONOTONIC_NAMES) <= described
    assert descriptions
    for text in descriptions:
        assert not re.search(r"spline[ -]parameter", text, re.IGNORECASE), text


def test_ac7_record_stores_its_one_element_order(break_report):
    sequence = _anatomical_sequence(break_report)
    assert sequence != sorted(sequence)
    assert len(sequence) == len(break_report["features"]["per_label"])
    assert _resolve(break_report, "case.sequence.order[]") == sequence


def test_ac8_in_sample_fit_is_fed_the_anatomical_sequence(break_report):
    sequence = _anatomical_sequence(break_report)
    assert sequence != sorted(sequence)
    path = _new("stage3.per_label_orientations[].spline_closest_u")
    u = []
    for label in sequence:
        (value,) = _resolve(break_report, path, label)
        u.append(value)
    assert len(u) == len(sequence)
    assert all(b > a for a, b in zip(u, u[1:])), u


def test_ac9_neighbourhood_windows_follow_the_anatomical_sequence(break_report):
    sequence = _anatomical_sequence(break_report)
    assert sequence != sorted(sequence)
    path = _new("stage3.per_label_neighbourhood[].window_labels[]")
    differs = False
    for i, label in enumerate(sequence):
        expected = sequence[max(0, i - 1) : i + 2]
        assert _resolve(break_report, path, label) == expected
        ascending = sorted(sequence)
        j = ascending.index(label)
        differs = differs or expected != ascending[max(0, j - 1) : j + 2]
    assert differs


# =========================================================================== #
# Named adversarial cases
# =========================================================================== #


def test_unknown_label_still_judged():
    assert _fused_label_sets(_variant("fuse_adjacent", {23: 99})) == [frozenset({22})]


def test_stage3_unavailable_not_judged():
    img = loaded_seg_image(_case("fuse_adjacent"))
    record = extract_feature_record(img, bundled_default_config())
    config = bundled_default_config()
    assert [f.labels for f in FusedLabelRule().evaluate(record, config)] == [
        frozenset({22})
    ]
    stripped = copy.deepcopy(record)
    for old in (
        "stage3.spacing_consistency.mean_spacing_mm",
        "stage3.spacing_consistency.cv_spacing",
        "stage3.spacing_consistency.deviations_mm[]",
        "stage3.spacing_consistency.outlier_pairs[]",
    ):
        _delete(stripped, _new(old))
    assert _resolve(stripped, _new("relationships.neighbour_spacings_mm[]"))
    assert FusedLabelRule().evaluate(stripped, config) == []


def test_tangent_arrays_on_their_own_label():
    img = loaded_seg_image(_case("sequence_break"))
    record = extract_feature_record(img, bundled_default_config())
    sequence = _anatomical_sequence(record)
    assert sequence != sorted(sequence)
    for axis in ("coronal", "sagittal"):
        array_path = _new(f"stage3.curvature.{axis}_tangent_angles_deg[]")
        own_path = _new(f"stage3.per_label_orientations[].spline_tangent_{axis}_deg")
        for label in sequence:
            (a,) = _resolve(record, array_path, label)
            (b,) = _resolve(record, own_path, label)
            assert _wrapped_diff(a, b) <= 1.0, (axis, label, a, b)


def test_out_of_order_labels_unchanged():
    img = loaded_seg_image(_case("sequence_break"))
    record = extract_feature_record(img, bundled_default_config())
    labels = sorted(int(v) for v in np.unique(np.asarray(img.dataobj)) if v != 0)
    expected = compute_spine_relationships(
        [compute_centroid(img, label) for label in labels]
    ).out_of_order_labels
    assert expected
    assert (
        _resolve(record, _new("relationships.out_of_order_labels[]")) == expected
    )


# =========================================================================== #
# Review findings
# =========================================================================== #


def test_review_path_u_not_bounded_by_schema():
    img = loaded_seg_image(_case("sequence_break"))
    config = bundled_default_config()
    result, features = run_qc(img, config)
    features = copy.deepcopy(features)
    low, high = sorted(features["per_label"])[:2]
    features["per_label"][low]["curve"]["path_u"] = -(2.0**-52)
    features["per_label"][high]["curve"]["path_u"] = 1.0 + 2.0**-52
    report = serialize_report(
        result.verdict, "case", config, features=features
    )
    assert report["features"]["per_label"][low]["curve"]["path_u"] < 0
    assert report["features"]["per_label"][high]["curve"]["path_u"] > 1


def test_review_overlap_level_name_from_per_label():
    config = bundled_default_config()
    pair = {"label_a": 20, "label_b": 21, "overlap_voxels": 5}
    named = {
        "pairs": {"overlaps": [pair]},
        "per_label": {"20": {"level_name": "L1"}, "21": {"level_name": "L2"}},
    }
    (finding,) = OverlapRule().evaluate(named, config)
    assert "labels 20 (L1) and 21 (L2)" in finding.reason
    (bare,) = OverlapRule().evaluate({"pairs": {"overlaps": [pair]}}, config)
    assert "labels 20 (20) and 21 (21)" in bare.reason
