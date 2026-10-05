"""Full-pipeline regression harness over the committed corpus (item 041).

Turns one manifest case dict (from :func:`segfacet.synth.corpus.load_manifest`)
into the observable facts the parametrised regression suite
(``tests/test_041_regression_suite.py``) asserts on: it loads the case's
committed seg fixture via the Stage 0 loader (:func:`segfacet.io.load_case`),
runs the real pipeline (:func:`segfacet.pipeline.run_qc`), and exposes pure
predicates that dispatch on the case's ``detection`` discriminator (item 040):

* ``detection == "pipeline"`` -- the failure mode is directly observable by
  the plain pipeline; assert straight against ``run_qc``'s output.
* ``detection == "reconstructed_record"`` -- the failure mode is structurally
  invisible to plain ``run_qc`` (item 040's documented limitation). No
  committed case uses this path any more -- item 120 promoted the displace
  case's held-out spline offset into the pipeline itself, item 132 did the
  same for the mode-9 relabel-swap case, and item 195 removed the
  ``force_overlap`` case (mode 15) outright, since a single-channel label
  map cannot express it. The path is kept for a future reconstructed case,
  asserting by feeding a reconstructed feature record directly to the
  designated rule (:class:`~segfacet.heuristics.mislabel.MislabelRule`).

This module is a small, importable verification library -- **not** a pytest
module itself -- so the parametrised suite and any future drift/meta-tests
call exactly the same comparison logic (DRY).

Public surface
--------------
``loaded_seg_image``, ``pipeline_findings``, ``pipeline_verdict_label``,
``reconstructed_findings``, ``designated_findings``, ``designated_rule_fired``,
``offending_labels_match``, ``pipeline_hides_designated_rule``, ``verify_case``,
and the ``RECONSTRUCTIONS`` technique registry -- plus, since item 146, the
**intensity** sibling pair ``loaded_intensity_case`` /
``intensity_pipeline_findings``, which drives a case from the second committed
corpus (``tests/corpus/intensity/``) through
:func:`segfacet.pipeline.run_qc_with_intensity`. The second corpus had no
public harness at all until item 146; every consumer that needs one (today
``segfacet.failure_modes.measured_firing``) composes it here rather than
privately, so there is exactly one intensity composition in production.
Additively re-exported from ``segfacet.synth``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import nibabel as nib

from segfacet.config import bundled_default_config
from segfacet.heuristics.mislabel import MislabelRule
from segfacet.io import load_case
from segfacet.pipeline import extract_feature_record, run_qc, run_qc_with_intensity
from segfacet.synth.corpus import CORPUS_DIR
from segfacet.synth.intensity import INTENSITY_CORPUS_DIR
from segfacet.synth.perturbation import CASE_KIND_CLEAN_CONTROL, corpus_case_kind

__all__ = [
    "RECONSTRUCTIONS",
    "loaded_seg_image",
    "pipeline_findings",
    "pipeline_verdict_label",
    "reconstructed_findings",
    "designated_findings",
    "designated_rule_fired",
    "offending_labels_match",
    "pipeline_hides_designated_rule",
    "verify_case",
    "loaded_intensity_case",
    "intensity_pipeline_findings",
]


# --------------------------------------------------------------------------- #
# Loading -- the Stage 0 path, same as ``segfacet run``
# --------------------------------------------------------------------------- #


def loaded_seg_image(case: dict, corpus_dir: Path = CORPUS_DIR) -> "nib.Nifti1Image":
    """Load *case*'s committed seg fixture via :func:`segfacet.io.load_case` and
    rebuild a fresh ``Nifti1Image`` from its loaded data/affine, suitable for
    ``run_qc`` / feature extraction.

    The explicit ``dtype=`` is mandatory: ``load_case`` returns an ``int64``
    label array and nibabel 5.3.3 hard-errors on
    ``Nifti1Image(int64_array, affine)`` without it (item 040's Decisions
    log).
    """
    corpus_dir = Path(corpus_dir)
    scan_path = corpus_dir / case["scan_fixture"]
    seg_path = corpus_dir / case["seg_fixture"]
    loaded = load_case(scan_path, seg_path)
    seg = loaded.seg
    return nib.Nifti1Image(seg.data, seg.affine, dtype=seg.data.dtype)


# --------------------------------------------------------------------------- #
# Plain-pipeline path
# --------------------------------------------------------------------------- #


def pipeline_findings(case: dict, config=None) -> Tuple:
    """``run_qc(loaded_seg_image(case), config).findings``."""
    config = config or bundled_default_config()
    case_result, _block = run_qc(loaded_seg_image(case), config)
    return case_result.findings


def pipeline_verdict_label(case: dict, config=None) -> str:
    """``run_qc(...).verdict.overall.label`` for a case's committed fixture."""
    config = config or bundled_default_config()
    case_result, _block = run_qc(loaded_seg_image(case), config)
    return case_result.verdict.overall.label


# --------------------------------------------------------------------------- #
# Intensity path -- the second committed corpus (item 146)
# --------------------------------------------------------------------------- #


def loaded_intensity_case(
    case: dict, corpus_dir: Path = INTENSITY_CORPUS_DIR
) -> Tuple["nib.Nifti1Image", "nib.Nifti1Image"]:
    """Load one intensity-corpus manifest case's committed seg **and** scan
    fixtures via :func:`segfacet.io.load_case`, returning
    ``(seg_img, scan_img)`` rebuilt as fresh ``Nifti1Image`` objects.

    The intensity sibling of :func:`loaded_seg_image`, and the same
    contract: the explicit ``dtype=`` is mandatory, because ``load_case``
    returns an ``int64`` label array and nibabel 5.3.3 hard-errors on
    ``Nifti1Image(int64_array, affine)`` without it (item 040's Decisions
    log).
    """
    corpus_dir = Path(corpus_dir)
    scan_path = corpus_dir / case["scan_fixture"]
    seg_path = corpus_dir / case["seg_fixture"]
    loaded = load_case(scan_path, seg_path)
    seg = loaded.seg
    scan = loaded.scan
    seg_img = nib.Nifti1Image(seg.data, seg.affine, dtype=seg.data.dtype)
    scan_img = nib.Nifti1Image(scan.data, scan.affine, dtype=scan.data.dtype)
    return seg_img, scan_img


def intensity_pipeline_findings(
    case: dict,
    config=None,
    *,
    reference=None,
    enable_pyradiomics: bool = False,
    corpus_dir: Path = INTENSITY_CORPUS_DIR,
) -> Tuple:
    """``run_qc_with_intensity(*loaded_intensity_case(case), config,
    reference=..., enable_pyradiomics=...).findings`` for one intensity-corpus
    manifest case.

    ``enable_pyradiomics`` defaults to ``False``, **not** to
    :func:`segfacet.pipeline.run_qc_with_intensity`'s own ``True`` (item 146
    A2): a firing set measured here is committed into
    ``tests/corpus/intensity/manifest.json`` and into the failure-mode
    specification, and must not depend on whether the optional PyRadiomics
    backend happens to be installed. It stays a keyword so a caller can opt
    in deliberately.

    ``reference`` defaults to ``None`` (A3): the synthetic intensity corpus
    is not built against any reference distribution.

    Neither *case* nor any file on disk is mutated; two calls with the same
    case return equal findings in the same order.
    """
    config = config or bundled_default_config()
    seg_img, scan_img = loaded_intensity_case(case, corpus_dir)
    case_result, _block, _image_features, _delta, _intensity_delta = (
        run_qc_with_intensity(
            seg_img,
            scan_img,
            config,
            reference=reference,
            enable_pyradiomics=enable_pyradiomics,
        )
    )
    return case_result.findings


# --------------------------------------------------------------------------- #
# Reconstruction handlers -- verbatim technique from items 038/039's tests
# --------------------------------------------------------------------------- #


def _recon_monotonic_true_spatial_order(case: dict, config) -> List:
    """Mode 4 (``relabel_swap``): evaluate :class:`MislabelRule` on the record
    :func:`segfacet.pipeline.extract_feature_record` builds (item 210,
    2026-10-05). The monotonicity check is itself label-free now, so the
    technique once reconstructed here is the pipeline's own and the two
    paths cannot disagree."""
    record = extract_feature_record(loaded_seg_image(case), config)
    return MislabelRule().evaluate(record, config)


RECONSTRUCTIONS: Dict[str, Callable] = {
    "monotonic_true_spatial_order": _recon_monotonic_true_spatial_order,
}


def reconstructed_findings(case: dict, config=None) -> List:
    """Dispatch on ``case["reconstruction"]`` to the matching technique in
    :data:`RECONSTRUCTIONS`, feed the reconstructed record to the designated
    rule, and return its findings.

    Raises
    ------
    ValueError
        If ``case["reconstruction"]`` names no known technique -- a future
        reconstructed case without a handler must fail loudly, never be
        silently skipped (AC12).
    """
    config = config or bundled_default_config()
    technique = case["reconstruction"]
    handler = RECONSTRUCTIONS.get(technique)
    if handler is None:
        raise ValueError(
            f"reconstructed_findings: unrecognised reconstruction technique "
            f"{technique!r} for case {case.get('case_id')!r}; known "
            f"techniques are {sorted(RECONSTRUCTIONS)}."
        )
    return handler(case, config)


# --------------------------------------------------------------------------- #
# Dispatch on detection + shared predicates
# --------------------------------------------------------------------------- #


def designated_findings(case: dict, config=None) -> List:
    """Findings whose ``rule_id`` is in ``case["expected_rule_ids"]``, taken
    from the ``run_qc`` path for ``"pipeline"`` cases and from
    :func:`reconstructed_findings` for ``"reconstructed_record"`` cases."""
    config = config or bundled_default_config()
    expected_rule_ids = set(case["expected_rule_ids"])

    if case["detection"] == "pipeline":
        findings = pipeline_findings(case, config)
    elif case["detection"] == "reconstructed_record":
        findings = reconstructed_findings(case, config)
    else:
        raise ValueError(
            f"designated_findings: unrecognised detection {case['detection']!r} "
            f"for case {case.get('case_id')!r}."
        )

    return [f for f in findings if f.rule_id in expected_rule_ids]


def designated_rule_fired(case: dict, config=None) -> bool:
    """``True`` iff :func:`designated_findings` is non-empty."""
    return len(designated_findings(case, config)) > 0


def offending_labels_match(case: dict, config=None) -> bool:
    """``True`` iff the union of :func:`designated_findings`' ``labels``
    equals ``set(case["expected_labels"])``."""
    findings = designated_findings(case, config)
    union: set = set()
    for f in findings:
        union |= set(f.labels)
    return union == set(case["expected_labels"])


def pipeline_hides_designated_rule(case: dict, config=None) -> bool:
    """``True`` iff plain ``run_qc`` emits NO finding whose ``rule_id`` is in
    ``expected_rule_ids`` (the documented limitation for
    ``reconstructed_record`` cases)."""
    config = config or bundled_default_config()
    expected_rule_ids = set(case["expected_rule_ids"])
    findings = pipeline_findings(case, config)
    return not any(f.rule_id in expected_rule_ids for f in findings)


def verify_case(case: dict, config=None) -> bool:
    """The whole per-case check, dispatched on ``detection``:

    * ``pipeline``: verdict label matches, and (``kind == "clean_control"`` ->
      no findings) or (a case designating no rule -> no findings; "not
      detected today") or (``kind in {"condition", "failure"}`` -> designated
      rule fires and offending labels match).
    * ``reconstructed_record``: plain pipeline hides the designated rule,
      the reconstruction fires it, and the offending labels match.
    """
    config = config or bundled_default_config()

    if case["detection"] == "pipeline":
        if pipeline_verdict_label(case, config) != case["expected_verdict"]:
            return False
        if corpus_case_kind(case) == CASE_KIND_CLEAN_CONTROL:
            return pipeline_findings(case, config) == ()
        if not case["expected_rule_ids"]:
            # A failure-mode case no shipped rule detects yet (item 150:
            # remove_level_relabel) -- honest only if nothing fires.
            return pipeline_findings(case, config) == ()
        return designated_rule_fired(case, config) and offending_labels_match(
            case, config
        )

    if case["detection"] == "reconstructed_record":
        return (
            pipeline_hides_designated_rule(case, config)
            and designated_rule_fired(case, config)
            and offending_labels_match(case, config)
        )

    raise ValueError(
        f"verify_case: unrecognised detection {case['detection']!r} for case "
        f"{case.get('case_id')!r}."
    )
