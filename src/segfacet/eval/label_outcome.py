"""Per-label, several-modes-per-case expectation for the harness (item 230).

An ``EvaluationCase.expected`` mapping may carry ``label_modes``: a sequence of
``[label, mode]`` pairs, mode 0 meaning "reviewed and found clean". This module
builds that expectation (:func:`label_mode_expectation`), scores a case result
against it per pair (:func:`classify_label_outcomes`) and aggregates the pairs
over a cohort (:func:`compute_label_metrics`).

Attribution (A1): a counted finding (``severity >= positive_severity``) falls
on label L when ``L in finding.labels`` and serves mode m when
``m in failure_modes.modes_for_detector(rule_id, detector_id)``. A failure pair
is *detected* when a counted finding on its label serves its mode; any pair is
*flagged* when any counted finding falls on its label. A finding on a label no
pair names is ignored (A3); a case-level finding (no labels) falls on none.

Scope fence: no review-label table reading, no CLI, no report rendering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional, Sequence, Tuple

from segfacet.io import FacetInputError
from segfacet.verdict import Severity

__all__ = [
    "LabelOutcome",
    "LabelModeSensitivity",
    "LabelMetrics",
    "label_mode_expectation",
    "classify_label_outcomes",
    "compute_label_metrics",
]


@dataclass(frozen=True)
class LabelOutcome:
    """One ``(label, mode)`` pair's outcome; ``detected`` is None for mode 0."""

    label: int
    failure_mode: int
    flagged: bool
    detected: Optional[bool]


@dataclass(frozen=True)
class LabelModeSensitivity:
    """Per-mode label sensitivity: detected failure pairs out of all of them."""

    failure_mode: int
    n_labels: int
    n_detected: int
    sensitivity: Optional[float]


@dataclass(frozen=True)
class LabelMetrics:
    """Cohort-level label metrics (per-mode sensitivity, clean-label FPs)."""

    per_mode: Tuple[LabelModeSensitivity, ...]
    n_clean_labels: int
    n_clean_labels_flagged: int
    clean_label_false_positive_rate: Optional[float]


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _validated_label_modes(raw: Any) -> Tuple[Tuple[int, int], ...]:
    """Validate, deduplicate and sort ``[label, mode]`` pairs."""
    from segfacet.failure_modes import SPECIFICATION

    pairs = set()
    try:
        items = [tuple(p) for p in raw]
    except TypeError as exc:
        raise FacetInputError(
            "label_modes must be a sequence of [label, mode] pairs."
        ) from exc
    for p in items:
        if len(p) != 2 or not all(_is_int(v) for v in p):
            raise FacetInputError(
                f"label_modes entry {p!r} is not a [label, mode] pair of ints."
            )
        label, mode = p
        if mode != 0 and mode not in SPECIFICATION:
            raise FacetInputError(
                f"label_modes: unknown failure mode id {mode!r} for label {label!r}."
            )
        pairs.add((label, mode))
    clean = {l for l, m in pairs if m == 0}
    failed = {l for l, m in pairs if m != 0}
    both = sorted(clean & failed)
    if both:
        raise FacetInputError(
            f"label_modes: label {both[0]!r} is paired with both mode 0 "
            "(clean) and a non-zero mode."
        )
    return tuple(sorted(pairs))


def label_mode_expectation(pairs: Iterable[Sequence[int]]) -> dict:
    """Build an ``EvaluationCase.expected`` mapping from ``(label, mode)`` pairs."""
    valid = _validated_label_modes(pairs)
    all_clean = all(m == 0 for _, m in valid)
    return {
        "expected_verdict": (Severity.PASS if all_clean else Severity.FLAG).label,
        "label_modes": [[l, m] for l, m in valid],
    }


def classify_label_outcomes(
    expected: Any, actual: Any, *, positive_severity: Severity = Severity.FLAG
) -> Optional[Tuple[LabelOutcome, ...]]:
    """Score each ``label_modes`` pair; ``None`` when *expected* has none."""
    if "label_modes" not in expected:
        return None
    from segfacet.failure_modes import modes_for_detector

    pairs = _validated_label_modes(expected["label_modes"])
    counted = [
        (f, modes_for_detector(f.rule_id, getattr(f, "detector_id", "")))
        for f in tuple(actual.findings)
        if f.severity >= positive_severity
    ]
    out = []
    for label, mode in pairs:
        on_label = [(f, served) for f, served in counted if label in f.labels]
        detected = None
        if mode != 0:
            detected = any(mode in served for _, served in on_label)
        out.append(
            LabelOutcome(
                label=label,
                failure_mode=mode,
                flagged=bool(on_label),
                detected=detected,
            )
        )
    return tuple(out)


def compute_label_metrics(records: Iterable[Any]) -> Optional[LabelMetrics]:
    """Aggregate records' ``label_outcomes``; ``None`` if none carry any."""
    from segfacet.eval.metrics import _safe_rate

    outcomes = []
    seen = False
    for r in records:
        lo = getattr(r, "label_outcomes", None)
        if lo is not None:
            seen = True
            outcomes.extend(lo)
    if not seen:
        return None
    modes = sorted({o.failure_mode for o in outcomes if o.failure_mode != 0})
    per_mode = []
    for m in modes:
        group = [o for o in outcomes if o.failure_mode == m]
        n_det = sum(1 for o in group if o.detected)
        per_mode.append(
            LabelModeSensitivity(m, len(group), n_det, _safe_rate(n_det, len(group)))
        )
    clean = [o for o in outcomes if o.failure_mode == 0]
    n_flagged = sum(1 for o in clean if o.flagged)
    return LabelMetrics(
        per_mode=tuple(per_mode),
        n_clean_labels=len(clean),
        n_clean_labels_flagged=n_flagged,
        clean_label_false_positive_rate=_safe_rate(n_flagged, len(clean)),
    )
