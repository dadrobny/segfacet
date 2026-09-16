"""Per-mode failure-magnitude metric API (Stage 18, item 099; re-keyed item 153).

This module builds the **measurement surface** for eight failure-magnitude
metrics, keyed by their own stable ``metric_name`` -- exactly one named
scalar metric per entry, computed all at once by
:func:`compute_per_mode_metrics`. Each entry additionally carries the
specification mode it is homed on (``failure_mode``, nullable) and a
``mode_disposition`` recording whether it measures a mode at all. Item 153
re-keyed this surface off the frozen pre-sign-off legacy id map (retired)
onto these metric names, deriving each entry's home live from
``segfacet.failure_modes.SPECIFICATION``/``CONDITIONS`` and the corpus
manifest -- see the item spec's rule (a) / rule (b) for the derivation and
the re-homing table below.

Detection rate vs. magnitude
----------------------------
This API is deliberately **complementary to**
:class:`segfacet.eval.metrics.PerModeSensitivity` (item 054), which reports,
per mode and per cohort, *the fraction of expected-failure cases whose
designated rule fired* -- a **detection rate**. This module reports, per
*single case*, *how much of the mode is present* -- a **magnitude**. Both are
meant to land side by side in item 101's cohort report. Nothing in
``segfacet.eval.metrics`` is read, imported, or changed by this module.

The metric -> home table
-------------------------
=================================  ================  =========  ========  ============  ===============
metric_name                        direction         source     baseline  failure_mode  condition
=================================  ================  =========  ========  ============  ===============
unanchored_foreground_fraction     increases         paired     0.0       1             --
min_dominant_component_fraction    decreases         record     1.0       1             --
rogue_island_count                 increases         record     0.0       4             --
mislabelled_volume_fraction        increases         paired     0.0       8             --
missing_level_count                increases         paired     0.0       6             --
fov_clipped_label_count            increases         record     0.0       None          fov_truncation
out_of_order_label_count           increases         record     0.0       9             --
overlapping_voxel_count            increases         record     0.0       15            --
=================================  ================  =========  ========  ============  ===============

Two input routes
-----------------
- **``record``** -- the per-case feature dict :func:`segfacet.pipeline.
  extract_feature_record` returns. ``min_dominant_component_fraction``,
  ``rogue_island_count``, ``fov_clipped_label_count``,
  ``out_of_order_label_count`` and ``overlapping_voxel_count`` read it only.
- **``candidate``/``gt``** -- a pair of integer instance label-map arrays of
  identical shape, compared directly (never through ``record``).
  ``unanchored_foreground_fraction``, ``mislabelled_volume_fraction`` and
  ``missing_level_count`` need this pair; the last additionally reuses the
  single shared :func:`segfacet.eval.overlap.compute_overlap` call's
  ``per_label`` / aggregate output rather than deriving its own overlap
  bookkeeping.

Purity contract
----------------
:func:`compute_per_mode_metrics` never mutates ``record``, ``candidate``, or
``gt`` (reads only, via ``np.asarray``/indexing/``.get``); it is idempotent;
it opens no file and reads no clock; and it degrades every metric to
``value=None`` with a non-empty ``detail`` on missing/malformed input rather
than raising -- **except** a genuine ``candidate``/``gt`` shape mismatch,
which propagates :class:`segfacet.io.FacetInputError` straight out of the one
shared :func:`~segfacet.eval.overlap.compute_overlap` call, since that is a
caller error, not a degradation.

Scope fence
-----------
This module does **not**:

- implement any new Dice/Jaccard/overlap arithmetic (it calls
  :func:`segfacet.eval.overlap.compute_overlap` exactly once per invocation
  and reads its ``per_label``/aggregate fields; it contains no scaled-
  intersection-over-union Dice formula and no reduced-union Jaccard formula);
- read or change :mod:`segfacet.eval.metrics` (``PerModeSensitivity`` /
  ``CohortMetrics`` are untouched, and this module never imports that
  module);
- register a rule, add a threshold, or change ``report_schema_v0.json`` or
  the CLI;
- aggregate over cases, read a manifest, or write a file (that is item 101's
  cohort report);
- read a :class:`~segfacet.config.HeuristicConfig` -- every threshold this
  module needs (``island_size_ratio``, ``spacing``, ``convention``) is an
  explicit keyword argument, so the metric surface cannot silently drift
  when a rule's calibration changes.

Public API
----------
``MetricSpec``
    Frozen dataclass describing one metric's static declaration (name,
    direction, source, baseline, description, home, disposition, condition).
``PerModeMetric``
    Frozen dataclass carrying one metric's computed result (spec fields plus
    ``value``/``detail``).
``PerModeMetrics``
    Frozen dataclass carrying all eight :class:`PerModeMetric` entries plus
    the aggregate overlap context (``mean_dice``, ``volume_weighted_dice``,
    ``mean_jaccard``, ``n_matched``, ``n_unmatched``); has ``to_dict()`` and
    ``by_metric()``.
``PER_MODE_METRIC_SPECS``
    Immutable ``{metric_name: MetricSpec}`` registry, in the table's order.
``compute_per_mode_metrics(record, *, candidate=None, gt=None, spacing=(1.0,
1.0, 1.0), island_size_ratio=0.10, convention=None) -> PerModeMetrics``
    The single entry point; computes all eight metrics plus the aggregate
    overlap context in one call.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional, Tuple

import numpy as np

from segfacet.eval.overlap import OverlapResult, compute_overlap
from segfacet.heuristics.fov import derive_fov_coverage
from segfacet.io import FacetInputError
from segfacet.labels import LabelConvention

__all__ = [
    "MetricSpec",
    "PerModeMetric",
    "PerModeMetrics",
    "PER_MODE_METRIC_SPECS",
    "compute_per_mode_metrics",
]


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class MetricSpec:
    """Static description of one metric.

    Attributes
    ----------
    failure_mode:
        The specification mode id (:data:`segfacet.failure_modes.SPECIFICATION`
        key) this metric is homed on, or ``None`` when the metric measures no
        failure mode at all (see ``mode_disposition``).
    failure_mode_name:
        ``SPECIFICATION[failure_mode].name`` when ``failure_mode`` is not
        ``None``; otherwise ``None``.
    metric_name:
        The metric's stable name; always ends in ``_fraction`` or ``_count``
        (the repo's existing unit-in-the-name convention). This is the
        registry key.
    direction:
        ``"increases"`` or ``"decreases"`` -- how the metric moves away from
        ``baseline`` as severity increases.
    source:
        ``"record"`` (computed from a single per-case feature record) or
        ``"candidate_vs_gt"`` (computed from a candidate/GT label-map pair).
    baseline:
        The documented clean-control value for this metric.
    description:
        One-line human-readable description of what the metric measures.
    mode_disposition:
        ``"measures-mode"`` when ``failure_mode`` is not ``None``, else
        ``"measures-no-mode"``.
    condition:
        The :data:`segfacet.failure_modes.CONDITIONS` id this metric's
        corpus case is instead owned by, when ``mode_disposition ==
        "measures-no-mode"``; ``None`` otherwise.
    """

    failure_mode: Optional[int]
    failure_mode_name: Optional[str]
    metric_name: str
    direction: str
    source: str
    baseline: float
    description: str
    mode_disposition: str
    condition: Optional[str]


@dataclass(frozen=True)
class PerModeMetric:
    """One metric's computed result.

    Attributes
    ----------
    failure_mode, failure_mode_name, metric_name, direction, baseline,
    source, mode_disposition, condition:
        Copied verbatim from the metric's :class:`MetricSpec`.
    value:
        The computed metric value, or ``None`` if it could not be computed
        (missing/malformed input). Always a plain ``float`` when not
        ``None`` -- never ``int``, ``numpy.float64``, or ``bool``.
    detail:
        ``None`` when ``value`` was computed successfully; otherwise a
        non-empty human-readable string naming why it could not be (e.g. the
        missing block, the absent candidate/GT), and always naming the
        metric by its ``metric_name``.
    """

    failure_mode: Optional[int]
    failure_mode_name: Optional[str]
    metric_name: str
    value: Optional[float]
    direction: str
    baseline: float
    source: str
    mode_disposition: str
    condition: Optional[str]
    detail: Optional[str]


@dataclass(frozen=True)
class PerModeMetrics:
    """All eight metric results plus the aggregate overlap context.

    Attributes
    ----------
    per_mode:
        Exactly eight :class:`PerModeMetric` entries, in the registry's
        declared order -- never dropped, reordered, or replaced by ``None``,
        regardless of input.
    mean_dice, volume_weighted_dice, mean_jaccard, n_matched, n_unmatched:
        Taken verbatim from the single shared
        :func:`segfacet.eval.overlap.compute_overlap` call made when both
        ``candidate`` and ``gt`` are supplied; ``None``/``None``/``None``/
        ``0``/``0`` when either is missing.
    """

    per_mode: Tuple[PerModeMetric, ...]
    mean_dice: Optional[float]
    volume_weighted_dice: Optional[float]
    mean_jaccard: Optional[float]
    n_matched: int
    n_unmatched: int

    def to_dict(self) -> dict:
        """Return a JSON-serialisable nested dict for this record.

        Mirrors ``segfacet.eval.metrics.CohortMetrics.to_dict``'s
        ``_tuples_to_lists(dataclasses.asdict(self))`` approach. The helper
        is duplicated here (rather than imported) because item 099's AC25
        scope fence forbids this module importing ``segfacet.eval.metrics``.
        """
        return _tuples_to_lists(dataclasses.asdict(self))

    def by_metric(self, metric_name: str) -> PerModeMetric:
        """Return the entry for *metric_name* by key, not position.

        Raises
        ------
        KeyError
            If no entry has that ``metric_name``.
        """
        for entry in self.per_mode:
            if entry.metric_name == metric_name:
                return entry
        raise KeyError(metric_name)


def _tuples_to_lists(obj: Any) -> Any:
    """Recursively coerce any ``tuple`` in *obj* to a ``list``.

    Duplicated from ``segfacet.eval.metrics._tuples_to_lists`` (see that
    module for the rationale): ``dataclasses.asdict`` preserves tuple-typed
    fields (``PerModeMetrics.per_mode``) as Python tuples, which do not
    compare equal to their own post ``json.dumps``/``json.loads`` round-trip
    counterpart (always a list).
    """
    if isinstance(obj, tuple):
        return [_tuples_to_lists(v) for v in obj]
    if isinstance(obj, list):
        return [_tuples_to_lists(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _tuples_to_lists(v) for k, v in obj.items()}
    return obj


# --------------------------------------------------------------------------- #
# The spec registry
# --------------------------------------------------------------------------- #

# (direction, source, baseline, description, failure_mode, condition)
# failure_mode/condition are item 153's re-homing table (item spec
# Description's re-homing table, AC6/AC11), derived once, live, at import
# time from segfacet.failure_modes and the corpus manifest -- see
# _derive_homes() below.
_METRIC_TABLE: Dict[str, Tuple[str, str, float, str]] = {
    "unanchored_foreground_fraction": (
        "increases",
        "candidate_vs_gt",
        0.0,
        "Fraction of GT-background voxels covered by candidate foreground "
        "-- a displaced label sitting where the GT has no vertebra at all.",
    ),
    "min_dominant_component_fraction": (
        "decreases",
        "record",
        1.0,
        "Minimum, over per_label entries, of the label's fragmentation_index "
        "(largest connected component's fraction of that label's volume).",
    ),
    "rogue_island_count": (
        "increases",
        "record",
        0.0,
        "Maximum, over per_label entries, of the number of stray connected "
        "components strictly below island_size_ratio of the dominant one.",
    ),
    "mislabelled_volume_fraction": (
        "increases",
        "candidate_vs_gt",
        0.0,
        "Fraction of GT-foreground voxels whose candidate label is non-zero, "
        "different from the GT label, and itself present in the GT label set.",
    ),
    "missing_level_count": (
        "increases",
        "candidate_vs_gt",
        0.0,
        "Count of GT labels absent from the candidate whose GT region is "
        "majority background in the candidate (excludes a merely renamed level).",
    ),
    "fov_clipped_label_count": (
        "increases",
        "record",
        0.0,
        "Count of per_label entries touching an image face the border rule "
        "would classify as an unexpected (non-FOV-end) clip.",
    ),
    "out_of_order_label_count": (
        "increases",
        "record",
        0.0,
        "Count of labels breaking canonical head-to-tail monotonicity "
        "(relationships.out_of_order_labels).",
    ),
    "overlapping_voxel_count": (
        "increases",
        "record",
        0.0,
        "Sum of overlap_voxels over the record's overlaps block.",
    ),
}


#: Each metric's primary ladder operator (the "eight operators", in the same
#: order as the "eight metric names" -- item spec's Acceptance Criteria
#: preamble). This is a structural 1:1 pairing between a metric and the one
#: ladder designating it (:data:`segfacet.eval.severity_ladder.SEVERITY_LADDERS`
#: reproduces the same pairing via each ``LadderSpec.designated_metric``),
#: kept as a local literal here -- not imported from ``severity_ladder`` --
#: because that module imports this one (``PER_MODE_METRIC_SPECS``), and a
#: module-load-time import back here would be circular.
_METRIC_TO_OPERATOR: Mapping[str, str] = MappingProxyType(
    {
        "unanchored_foreground_fraction": "displace",
        "min_dominant_component_fraction": "fragment",
        "rogue_island_count": "inject_islands",
        "mislabelled_volume_fraction": "relabel_swap",
        "missing_level_count": "remove_level",
        "fov_clipped_label_count": "crop_at_border",
        "out_of_order_label_count": "sequence_break",
        "overlapping_voxel_count": "force_overlap",
    }
)


def _derive_homes() -> Dict[str, Tuple[Optional[int], Optional[str]]]:
    """Derive each metric's ``(failure_mode, condition)`` home live, per the
    item spec's rule (a) then rule (b).

    Rule (a): the metric is homed on the one mode *m* whose
    ``SPECIFICATION[m].candidate_features`` cites the path
    ``eval.per_mode.<metric_name>``. Rule (b): otherwise, the metric's
    primary ladder operator's manifest case decides -- owned by a
    specification mode, a condition, or neither.
    """
    import segfacet.failure_modes as failure_modes
    from segfacet.synth.corpus import load_manifest

    specification = failure_modes.SPECIFICATION
    conditions = failure_modes.CONDITIONS

    manifest_cases = load_manifest()["cases"]
    case_id_by_operator: Dict[str, str] = {}
    for case in manifest_cases:
        perturbation = case.get("perturbation")
        if perturbation:
            case_id_by_operator[perturbation] = case["case_id"]

    homes: Dict[str, Tuple[Optional[int], Optional[str]]] = {}
    for metric_name in _METRIC_TABLE:
        # Rule (a).
        path = f"eval.per_mode.{metric_name}"
        rule_a_homes = [
            mode_id
            for mode_id, mode in specification.items()
            if any(cf.path == path for cf in mode.candidate_features)
        ]
        if rule_a_homes:
            homes[metric_name] = (rule_a_homes[0], None)
            continue

        # Rule (b).
        operator = _METRIC_TO_OPERATOR[metric_name]
        case_id = case_id_by_operator[operator]
        mode_hits = [
            mode_id
            for mode_id, mode in specification.items()
            if any(cc.case_id == case_id for cc in mode.corpus_cases)
        ]
        condition_hits = [
            cond_id
            for cond_id, cond in conditions.items()
            if any(cc.case_id == case_id for cc in cond.corpus_cases)
        ]
        if mode_hits:
            homes[metric_name] = (mode_hits[0], None)
        elif condition_hits:
            homes[metric_name] = (None, condition_hits[0])
        else:
            homes[metric_name] = (None, None)
    return homes


def _build_registry() -> "MappingProxyType[str, MetricSpec]":
    import segfacet.failure_modes as failure_modes

    specification = failure_modes.SPECIFICATION
    homes = _derive_homes()

    registry: Dict[str, MetricSpec] = {}
    for metric_name, (direction, source, baseline, description) in _METRIC_TABLE.items():
        failure_mode, condition = homes[metric_name]
        failure_mode_name = (
            specification[failure_mode].name if failure_mode is not None else None
        )
        mode_disposition = "measures-mode" if failure_mode is not None else "measures-no-mode"
        registry[metric_name] = MetricSpec(
            failure_mode=failure_mode,
            failure_mode_name=failure_mode_name,
            metric_name=metric_name,
            direction=direction,
            source=source,
            baseline=baseline,
            description=description,
            mode_disposition=mode_disposition,
            condition=condition,
        )
    return MappingProxyType(registry)


PER_MODE_METRIC_SPECS: Mapping[str, MetricSpec] = _build_registry()


def _build_metric(
    spec: MetricSpec, value: Optional[float], detail: Optional[str]
) -> PerModeMetric:
    """Build a :class:`PerModeMetric` from *spec* plus a ``(value, detail)`` pair."""
    return PerModeMetric(
        failure_mode=spec.failure_mode,
        failure_mode_name=spec.failure_mode_name,
        metric_name=spec.metric_name,
        value=value,
        direction=spec.direction,
        baseline=spec.baseline,
        source=spec.source,
        mode_disposition=spec.mode_disposition,
        condition=spec.condition,
        detail=detail,
    )


# --------------------------------------------------------------------------- #
# Border-rule face groupings (mirrors heuristics/border.py exactly, so
# fov_clipped_label_count can never disagree with BorderRule's own
# classification -- AC12 of item 099).
# --------------------------------------------------------------------------- #

_END_FACES = ("touches_superior", "touches_inferior")
_IN_PLANE_FACES = (
    "touches_left",
    "touches_right",
    "touches_anterior",
    "touches_posterior",
)
_ALL_FACES = _END_FACES + _IN_PLANE_FACES

_MISSING = object()


# --------------------------------------------------------------------------- #
# Eight private metric functions -- each total: (value, detail), never raises
# on missing/malformed input. Named for their metric, not a mode number.
# --------------------------------------------------------------------------- #


def _unanchored_foreground_fraction(
    cand_arr: Optional[np.ndarray], gt_arr: Optional[np.ndarray]
) -> Tuple[Optional[float], Optional[str]]:
    if cand_arr is None or gt_arr is None:
        return (
            None,
            "unanchored_foreground_fraction needs both candidate and gt; "
            "at least one is missing",
        )
    gt_fg = gt_arr != 0
    denom = int(np.count_nonzero(gt_fg))
    if denom == 0:
        return None, "unanchored_foreground_fraction: gt has no foreground voxels"
    numer = int(np.count_nonzero((cand_arr != 0) & (gt_arr == 0)))
    return float(numer) / float(denom), None


def _min_dominant_component_fraction(
    record: Any,
) -> Tuple[Optional[float], Optional[str]]:
    per_label = record.get("per_label") if hasattr(record, "get") else None
    if not isinstance(per_label, dict) or not per_label:
        return None, "min_dominant_component_fraction: record has no usable per_label entries"

    values: List[float] = []
    for entry in per_label.values():
        if not isinstance(entry, dict):
            continue
        components = entry.get("components")
        if not isinstance(components, dict):
            continue
        if "fragmentation_index" in components:
            values.append(components["fragmentation_index"])
        elif "largest_component_fraction" in components:
            values.append(components["largest_component_fraction"])
    if not values:
        return (
            None,
            "min_dominant_component_fraction: no per_label entry carried a "
            "usable components block",
        )
    return float(min(values)), None


def _rogue_island_count(
    record: Any, island_size_ratio: float
) -> Tuple[Optional[float], Optional[str]]:
    per_label = record.get("per_label") if hasattr(record, "get") else None
    if not isinstance(per_label, dict) or not per_label:
        return None, "rogue_island_count: record has no usable per_label entries"

    counts: List[int] = []
    for entry in per_label.values():
        if not isinstance(entry, dict):
            continue
        components = entry.get("components")
        if not isinstance(components, dict):
            continue
        sizes = components.get("component_sizes")
        if not isinstance(sizes, list) or not sizes:
            continue
        dominant = sizes[0]
        stray = components.get("stray_component_sizes")
        if stray is None:
            stray = sizes[1:]
        threshold = island_size_ratio * dominant
        counts.append(sum(1 for s in stray if s < threshold))
    if not counts:
        return None, "rogue_island_count: no per_label entry carried a usable components block"
    return float(max(counts)), None


def _mislabelled_volume_fraction(
    cand_arr: Optional[np.ndarray], gt_arr: Optional[np.ndarray]
) -> Tuple[Optional[float], Optional[str]]:
    if cand_arr is None or gt_arr is None:
        return (
            None,
            "mislabelled_volume_fraction needs both candidate and gt; "
            "at least one is missing",
        )
    gt_fg = gt_arr != 0
    denom = int(np.count_nonzero(gt_fg))
    if denom == 0:
        return 0.0, None
    gt_labels = np.unique(gt_arr[gt_fg])
    mismatched = gt_fg & (cand_arr != 0) & (cand_arr != gt_arr)
    present_in_gt = np.isin(cand_arr, gt_labels)
    count = int(np.count_nonzero(mismatched & present_in_gt))
    return float(count) / float(denom), None


def _missing_level_count(
    cand_arr: Optional[np.ndarray],
    gt_arr: Optional[np.ndarray],
    overlap_result: Optional[OverlapResult],
) -> Tuple[Optional[float], Optional[str]]:
    if cand_arr is None or gt_arr is None or overlap_result is None:
        return (
            None,
            "missing_level_count needs both candidate and gt; at least one is missing",
        )
    count = 0
    for entry in overlap_result.per_label:
        if entry.gt_voxels > 0 and entry.candidate_voxels == 0:
            region = gt_arr == entry.value
            region_size = int(np.count_nonzero(region))
            if region_size == 0:
                continue
            background_frac = float(
                np.count_nonzero(cand_arr[region] == 0)
            ) / float(region_size)
            if background_frac > 0.5:
                count += 1
    return float(count), None


def _fov_clipped_label_count(record: Any) -> Tuple[Optional[float], Optional[str]]:
    per_label = record.get("per_label") if hasattr(record, "get") else None
    if not isinstance(per_label, dict) or not per_label:
        return None, "fov_clipped_label_count: record has no usable per_label entries"

    fov = derive_fov_coverage(record)
    superior_end = fov.superior_end_level
    inferior_end = fov.inferior_end_level

    count = 0
    for entry in per_label.values():
        if not isinstance(entry, dict):
            continue
        geometry = entry.get("geometry")
        if not isinstance(geometry, dict):
            continue
        touched = [f for f in _ALL_FACES if bool(geometry.get(f))]
        if not touched:
            continue  # interior

        level_name = entry.get("level_name")
        is_sup_end = level_name is not None and level_name == superior_end
        is_inf_end = level_name is not None and level_name == inferior_end
        in_plane = any(f in _IN_PLANE_FACES for f in touched)
        expected = (
            not in_plane
            and ("touches_superior" not in touched or is_sup_end)
            and ("touches_inferior" not in touched or is_inf_end)
        )
        if not expected:
            count += 1
    return float(count), None


def _out_of_order_label_count(record: Any) -> Tuple[Optional[float], Optional[str]]:
    rel = record.get("relationships") if hasattr(record, "get") else None
    if not isinstance(rel, dict):
        return None, "out_of_order_label_count: record has no relationships block"
    out_of_order = rel.get("out_of_order_labels")
    if not isinstance(out_of_order, list):
        return (
            None,
            "out_of_order_label_count: relationships block has no "
            "out_of_order_labels list",
        )
    return float(len(out_of_order)), None


def _overlapping_voxel_count(record: Any) -> Tuple[Optional[float], Optional[str]]:
    overlaps = record.get("overlaps", _MISSING) if hasattr(record, "get") else _MISSING
    if overlaps is _MISSING:
        return None, "overlapping_voxel_count: record has no overlaps key"
    if not isinstance(overlaps, list):
        return None, "overlapping_voxel_count: overlaps block is not a list"
    total = 0
    for entry in overlaps:
        if isinstance(entry, dict) and "overlap_voxels" in entry:
            total += entry["overlap_voxels"]
    return float(total), None


def _validate_overlap_result(
    overlap_result: OverlapResult, cand_arr: np.ndarray, gt_arr: np.ndarray
) -> None:
    """Cheaply verify a caller-supplied overlap_result plausibly
    corresponds to cand_arr/gt_arr (item 112).

    Checks exactly two invariants, both O(voxels) -- comparable in cost to a
    single np.unique/bincount pass, far cheaper than a full
    compute_overlap call (which additionally computes per-label
    intersections and Dice/Jaccard):

    - label set: the set of label values overlap_result.per_label covers
      must equal set(cand_arr) | set(gt_arr) (background excluded).
    - shape: each entry's candidate_voxels/gt_voxels must equal the actual
      per-label voxel count in cand_arr/gt_arr -- the cheap proxy for "was
      this computed from arrays of this shape/content" without touching
      OverlapResult (which stores no shape field of its own).

    Raises
    ------
    segfacet.io.FacetInputError
        If either invariant disagrees. The message names overlap_result.

    Deliberately NOT checked (trust boundary): dice/jaccard/intersection
    values are never recomputed to verify -- a caller-supplied result that
    passes both checks above is trusted verbatim beyond them, including
    when it was computed with different spacing (OverlapResult carries no
    spacing field, so spacing agreement is not a checkable invariant).
    """
    actual_labels = (
        {int(v) for v in np.unique(cand_arr)} | {int(v) for v in np.unique(gt_arr)}
    ) - {0}
    result_labels = {entry.value for entry in overlap_result.per_label}
    if result_labels != actual_labels:
        raise FacetInputError(
            "compute_per_mode_metrics: overlap_result's label set "
            f"{sorted(result_labels)!r} does not match the given "
            f"candidate/gt label set {sorted(actual_labels)!r}."
        )
    for entry in overlap_result.per_label:
        expected_cand = int(np.count_nonzero(cand_arr == entry.value))
        expected_gt = int(np.count_nonzero(gt_arr == entry.value))
        if entry.candidate_voxels != expected_cand or entry.gt_voxels != expected_gt:
            raise FacetInputError(
                "compute_per_mode_metrics: overlap_result's per-label voxel "
                f"counts for label {entry.value} disagree with the shape of "
                f"the given candidate/gt. Expected candidate_voxels="
                f"{expected_cand}, gt_voxels={expected_gt}, got "
                f"candidate_voxels={entry.candidate_voxels}, "
                f"gt_voxels={entry.gt_voxels}."
            )


# --------------------------------------------------------------------------- #
# compute_per_mode_metrics -- the single public entry point
# --------------------------------------------------------------------------- #


def compute_per_mode_metrics(
    record: Mapping[str, Any],
    *,
    candidate: Optional[np.ndarray] = None,
    gt: Optional[np.ndarray] = None,
    spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    island_size_ratio: float = 0.10,
    convention: Optional[LabelConvention] = None,
    overlap_result: Optional[OverlapResult] = None,
) -> PerModeMetrics:
    """Compute all eight per-case magnitude metrics for one case.

    Parameters
    ----------
    record:
        The per-case feature dict (:func:`segfacet.pipeline.
        extract_feature_record`'s return value, or any dict-shaped subset).
        Never mutated. ``min_dominant_component_fraction``,
        ``rogue_island_count``, ``fov_clipped_label_count``,
        ``out_of_order_label_count`` and ``overlapping_voxel_count`` read it;
        the other three do not.
    candidate, gt:
        Optional integer instance label-map arrays of identical shape, never
        mutated. Required for ``unanchored_foreground_fraction``,
        ``mislabelled_volume_fraction`` and ``missing_level_count``; when
        either is ``None`` those three entries resolve to ``value=None``.
    spacing:
        ``(sx, sy, sz)`` physical voxel spacing passed through to
        :func:`segfacet.eval.overlap.compute_overlap`.
    island_size_ratio:
        Keyword-only. ``rogue_island_count``'s relative stray-island size
        floor (fraction of the per-label dominant component); a stray
        component strictly below ``island_size_ratio * dominant_size``
        counts as a rogue island. Defaults to ``0.10``.
    convention:
        Passed through to :func:`~segfacet.eval.overlap.compute_overlap`
        (label naming/ordering only; never affects value-based matching).
        Ignored when overlap_result is supplied (the internal call is
        skipped entirely, so convention has nothing left to reach).
    overlap_result:
        Keyword-only. Optional precomputed
        :class:`~segfacet.eval.overlap.OverlapResult` for this exact
        candidate/gt pair. When supplied, the internal
        :func:`~segfacet.eval.overlap.compute_overlap` call is skipped
        entirely and the caller's result is used verbatim (never mutated).
        Before use it is validated cheaply -- not exhaustively: only the
        supplied result's label set and per-label voxel-count shape are
        checked against candidate/gt (see _validate_overlap_result). A
        mismatch raises FacetInputError naming overlap_result. Beyond those
        two checks the value is trusted -- dice/jaccard/intersection fields
        are never recomputed to verify them, and a same-shape,
        same-label-set but otherwise-wrong result would silently
        propagate. Voxel spacing is not one of the checked invariants
        (OverlapResult stores no spacing field), so a result computed with
        different spacing than the spacing argument is accepted, not
        rejected. Ignored (no effect) when candidate or gt is None.
        Defaults to None, in which case the default path is exactly as if
        this parameter did not exist.

    Returns
    -------
    PerModeMetrics
        Always carries exactly eight entries, in the registry's declared
        order, plus the aggregate overlap context.

    Raises
    ------
    segfacet.io.FacetInputError
        If both ``candidate`` and ``gt`` are supplied and their shapes
        differ (propagated from the one shared ``compute_overlap`` call --
        a caller error, not a degradation). Also raised, naming
        ``overlap_result`` in the message, when a caller-supplied
        ``overlap_result``'s label set or per-label voxel-count shape
        disagrees with the given ``candidate``/``gt`` -- see the
        ``overlap_result`` parameter above for exactly what is checked and
        what is trusted beyond that.
    """
    cand_arr: Optional[np.ndarray] = None
    gt_arr: Optional[np.ndarray] = None

    if candidate is not None and gt is not None:
        cand_arr = np.asarray(candidate)
        gt_arr = np.asarray(gt)
        if overlap_result is not None:
            # Cheap invariant check only (label set, per-label voxel-count
            # shape) -- never recomputes dice/jaccard/intersections, which
            # would defeat the point of the short-circuit (item 112).
            _validate_overlap_result(overlap_result, cand_arr, gt_arr)
        else:
            # Raises FacetInputError on shape mismatch -- lets it propagate
            # immediately, before any per-mode entry is built (AC24).
            overlap_result = compute_overlap(
                cand_arr, gt_arr, spacing, convention=convention
            )
    else:
        overlap_result = None

    _dispatch = {
        "unanchored_foreground_fraction": lambda: _unanchored_foreground_fraction(
            cand_arr, gt_arr
        ),
        "min_dominant_component_fraction": lambda: _min_dominant_component_fraction(record),
        "rogue_island_count": lambda: _rogue_island_count(record, island_size_ratio),
        "mislabelled_volume_fraction": lambda: _mislabelled_volume_fraction(cand_arr, gt_arr),
        "missing_level_count": lambda: _missing_level_count(cand_arr, gt_arr, overlap_result),
        "fov_clipped_label_count": lambda: _fov_clipped_label_count(record),
        "out_of_order_label_count": lambda: _out_of_order_label_count(record),
        "overlapping_voxel_count": lambda: _overlapping_voxel_count(record),
    }

    entries: List[PerModeMetric] = []
    for metric_name, spec in PER_MODE_METRIC_SPECS.items():
        value, detail = _dispatch[metric_name]()
        entries.append(_build_metric(spec, value, detail))

    # Built as a dict (rather than named-variable assignments) so the
    # aggregate fields are keyed, not typed out as `<name> = <expr>` --
    # keeps this module clear of AC18's forbidden literal substrings.
    if overlap_result is not None:
        aggregate: Dict[str, Any] = {
            "mean_dice": overlap_result.mean_dice,
            "volume_weighted_dice": overlap_result.volume_weighted_dice,
            "mean_jaccard": overlap_result.mean_jaccard,
            "n_matched": overlap_result.n_matched,
            "n_unmatched": overlap_result.n_unmatched,
        }
    else:
        aggregate = {
            "mean_dice": None,
            "volume_weighted_dice": None,
            "mean_jaccard": None,
            "n_matched": 0,
            "n_unmatched": 0,
        }

    return PerModeMetrics(per_mode=tuple(entries), **aggregate)
