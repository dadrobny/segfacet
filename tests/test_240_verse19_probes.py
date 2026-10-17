"""Tests for item 240 -- VerSe19 probes behind items 218 and 220.

One test per Acceptance Criterion (``test_ac1`` .. ``test_ac5``) plus exactly
the four adversarial cases the Testing Strategy names: ``cocc-flank-excluded``,
``upper-flank-excluded``, ``l6-flank-still-judged`` and
``verse19-root-without-splits-skips``.

AC3 and AC4 are gated on the VerSe19 cohort: they skip unless
``SEGFACET_VERSE_COHORT`` names a directory holding all three VerSe19 splits.
"""

from __future__ import annotations

import ast
import copy
import itertools
import math
import os
import re
from pathlib import Path
from typing import Optional

import nibabel as nib
import numpy as np
import pytest

import segfacet.synth  # noqa: F401 -- triggers self-registration of every operator
from segfacet import failure_modes
from segfacet.config import bundled_default_config, default_config_path
from segfacet.features.centroids import compute_centroid
from segfacet.heuristics import collapsed_labels
from segfacet.heuristics.centroid_spacing import CentroidSpacingRule
from segfacet.pipeline import extract_feature_record
from segfacet.synth.corpus import load_manifest
from segfacet.synth.intensity import INTENSITY_CORPUS_DIR, load_intensity_manifest
from segfacet.synth.regression import loaded_seg_image

_SPLITS = ("training", "validation", "test")


def real_verse19_root() -> Optional[Path]:
    """The VerSe19 root from ``SEGFACET_VERSE_COHORT`` iff it is a directory
    holding all three ``dataset-verse19<split>`` directories, else ``None``."""
    raw = os.environ.get("SEGFACET_VERSE_COHORT")
    if not raw:
        return None
    root = Path(raw)
    if not root.is_dir():
        return None
    if not all((root / f"dataset-verse19{s}").is_dir() for s in _SPLITS):
        return None
    return root


requires_verse19 = pytest.mark.skipif(
    real_verse19_root() is None,
    reason=(
        "VerSe19 cohort not mounted: set SEGFACET_VERSE_COHORT to a directory "
        "holding all three splits (dataset-verse19training, "
        "dataset-verse19validation, dataset-verse19test)"
    ),
)


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _min_pair(img) -> Optional[float]:
    """Smallest pairwise ``math.dist`` between the image's label centroids,
    or ``None`` when it has fewer than two labels."""
    labels = [int(v) for v in np.unique(np.asanyarray(img.dataobj)) if v != 0]
    if len(labels) < 2:
        return None
    centroids = {l: compute_centroid(img, l).centroid_mm for l in labels}
    return min(math.dist(centroids[a], centroids[b]) for a, b in itertools.combinations(labels, 2))


def _corpus_minimum(cases, corpus_dir=None) -> float:
    values = []
    for case in cases:
        img = loaded_seg_image(case) if corpus_dir is None else loaded_seg_image(case, corpus_dir)
        value = _min_pair(img)
        if value is not None:
            values.append(value)
    assert values
    m = min(values)
    assert math.isfinite(m) and m > 0
    return m


def _constant_docstring() -> str:
    tree = ast.parse(Path(collapsed_labels.__file__).read_text(encoding="utf-8"))
    for stmt, nxt in itertools.pairwise(tree.body):
        names = []
        if isinstance(stmt, ast.AnnAssign):
            names = [stmt.target]
        elif isinstance(stmt, ast.Assign):
            names = stmt.targets
        if any(isinstance(t, ast.Name) and t.id == "DEFAULT_MAX_CENTROID_DISTANCE_MM" for t in names):
            assert isinstance(nxt, ast.Expr) and isinstance(nxt.value, ast.Constant), nxt
            return nxt.value.value
    raise AssertionError("DEFAULT_MAX_CENTROID_DISTANCE_MM assignment not found")


def _collapsed_sites() -> list[str]:
    evidence = collapsed_labels.CollapsedLabelsRule.mode_declaration.evidence
    return [
        _squash(collapsed_labels.__doc__),
        _squash(_constant_docstring()),
        _squash(" ".join(evidence)),
    ]


def _config_text() -> str:
    return _squash(default_config_path().read_text(encoding="utf-8"))


def _assert_sites(m: float) -> None:
    for site in _collapsed_sites():
        assert f"{m:.3f} mm" in site
    assert f"{m:.2f} mm" in _config_text()


# --------------------------------------------------------------------------- #
# VerSe19 discovery (AC3, AC4)
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def verse19_minima() -> list[float]:
    """Smallest pairwise centroid distance per mask with two or more labels."""
    root = real_verse19_root()
    assert root is not None
    out = []
    for path in sorted(root.rglob("*_seg-vert_msk.nii.gz")):
        loaded = nib.load(str(path))
        # In-memory copy: each mask is decompressed once, not once per label.
        img = nib.Nifti1Image(np.asanyarray(loaded.dataobj), loaded.affine, loaded.header)
        value = _min_pair(img)
        if value is not None:
            out.append(value)
    assert out
    return out


# =========================================================================== #
# AC1-AC5
# =========================================================================== #


def test_ac1_geometric_corpus_figure_matches_every_site():
    _assert_sites(_corpus_minimum(load_manifest()["cases"]))


def test_ac2_intensity_corpus_figure_matches_every_site():
    _assert_sites(_corpus_minimum(load_intensity_manifest()["cases"], INTENSITY_CORPUS_DIR))


@requires_verse19
def test_ac3_verse19_figure_matches_every_site(verse19_minima):
    m = min(verse19_minima)
    assert math.isfinite(m) and m > 0
    for site in _collapsed_sites():
        assert f"{m:.3f} mm" in site
    assert f"{m:.3f} mm" in _squash(failure_modes.SPECIFICATION[13].mechanism)
    assert f"{m:.2f} mm" in _config_text()


@requires_verse19
def test_ac4_verse19_mask_count_matches_cited_count(verse19_minima):
    n = len(verse19_minima)
    assert n > 0
    assert f"{n} VerSe19 GT masks" in _squash(collapsed_labels.__doc__)
    assert f"{n} masks" in _squash(_constant_docstring())


def _remove_level_record() -> dict:
    matches = [c for c in load_manifest()["cases"] if c["case_id"] == "remove_level"]
    assert len(matches) == 1, matches
    return extract_feature_record(loaded_seg_image(matches[0]), bundled_default_config())


def _missing(record: dict) -> list:
    findings = CentroidSpacingRule().evaluate(record, bundled_default_config())
    return [f for f in findings if f.detector_id == "missing_level"]


def _with_level(record: dict, label: int, level_name: str) -> dict:
    copied = copy.deepcopy(record)
    keys = [k for k in copied["per_label"] if int(k) == label]
    assert len(keys) == 1, (label, list(copied["per_label"]))
    copied["per_label"][keys[0]]["level_name"] = level_name
    return copied


def _assert_control(record: dict) -> None:
    control = _missing(record)
    assert len(control) == 1, control
    assert control[0].labels == frozenset({21, 23})


def test_ac5_missing_level_not_judged_beside_a_sacral_label():
    record = _remove_level_record()
    _assert_control(record)
    assert _missing(_with_level(record, 23, "S1")) == []


# =========================================================================== #
# Adversarial cases
# =========================================================================== #


def test_cocc_flank_excluded():
    record = _remove_level_record()
    _assert_control(record)
    assert _missing(_with_level(record, 23, "Cocc")) == []


def test_upper_flank_excluded():
    record = _remove_level_record()
    _assert_control(record)
    assert _missing(_with_level(record, 21, "S1")) == []


def test_l6_flank_still_judged():
    record = _remove_level_record()
    _assert_control(record)
    still = _missing(_with_level(record, 23, "L6"))
    assert len(still) == 1, still
    assert still[0].labels == frozenset({21, 23})


def test_verse19_root_without_splits_skips(monkeypatch, tmp_path):
    (tmp_path / "dataset-verse19training").mkdir()
    monkeypatch.setenv("SEGFACET_VERSE_COHORT", str(tmp_path))
    assert real_verse19_root() is None
