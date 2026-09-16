"""Severity-ladder monotonicity & cross-mode specificity harness (item 100;
re-keyed item 153).

Item 099 proved *isolation on nine fixed corpus cases*: each of its eight
per-mode metrics (:mod:`segfacet.eval.per_mode`) attains its largest
deviation from baseline on its own designated case. That is a **one-point**
result. This module builds the strictly stronger, **graded** counterpart
Stage 18's G2 acceptance actually asks for: for each of the eight metrics, a
**severity ladder** -- an ordered sequence of rungs, rung 0 the untouched
clean control and each later rung applying the ladder's perturbation
operator at a strictly greater severity -- run through item 099's
:func:`~segfacet.eval.per_mode.compute_per_mode_metrics` at *every* rung of
*every* ladder (the full ladder x metric response surface, not just the
diagonal), then scored for:

* **monotonicity** -- is the designated metric non-decreasing/non-increasing
  (per its declared :class:`~segfacet.eval.per_mode.MetricSpec.direction`)
  and does it strictly change at every rung transition (a plateau, which a
  purely-directional check would pass, is treated as a failure);
* **cross-mode specificity** -- how large is the designated metric's
  response to *this* ladder's severity relative to every *foreign* metric's
  response to the *same* ladder.

The eight ladders
------------------
========  ================================  ======================  ==================
operator  designated_metric                 severity knob           kind
========  ================================  ======================  ==================
displace         unanchored_foreground_fraction (up)   displacement_mm         continuous
fragment         min_dominant_component_fraction (down) n_pieces                continuous
inject_islands   rogue_island_count (up)               n_islands               continuous
relabel_swap     mislabelled_volume_fraction (up)      n_affected_labels       affected-label-count
remove_level     missing_level_count (up)              n_affected_labels       affected-label-count
crop_at_border   fov_clipped_label_count (up)          n_affected_labels       affected-label-count
sequence_break   out_of_order_label_count (up)         --                      degenerate (2-rung)
force_overlap    overlapping_voxel_count (up)          overlap_depth           continuous
========  ================================  ======================  ==================

Plus one **supplementary** ladder, outside the eight and outside the
cross-mode matrix: the ``fragment`` ladder's *fused* counterpart via
cumulative ``fuse`` steps (see below).

Why three ladders have no continuous knob
-------------------------------------------
``relabel_swap``, ``sequence_break`` and ``remove_level`` take only
target-label selectors (no continuous physical parameter). Two of the three
get a genuine ladder from the *count of affected labels*; the third cannot:

* **``relabel_swap``** -- 3 rungs. Each disjoint adjacent swap mislabels two
  whole bodies (``n_affected_labels`` steps 0 -> 2 -> 4 on the five-level
  base), so ``mislabelled_volume_fraction`` steps 0.0 -> 0.4 -> 0.8. Only two
  disjoint adjacent pairs exist among five labels, so the ladder is 3 rungs,
  not 4 -- recorded, not hidden.
* **``remove_level``** -- 4 rungs. The three interior levels (21, 22, 23)
  are removed one at a time; ``missing_level_count`` steps 0 -> 1 -> 2 -> 3.
* **``crop_at_border``** -- *its* metric (``fov_clipped_label_count``)
  is a **count of labels**, invariant to clip depth; ``crop_depth`` is
  therefore pinned at the corpus's ``5`` and the severity axis sweeps the
  *number of clipped labels* (20, then +21, then +22) instead.
* **``sequence_break``** -- **degenerate**, 2 rungs, not merely
  inconvenient. Under the default (TPTBox, item 093) convention
  ``rank(v) == v - 1`` for every value 1-24, so no in-block relabel can
  produce a rank descent. The one transitional label that can (28 == T13,
  rank 19) always sorts last, contributing at most one descent.
  ``out_of_order_label_count`` is capped at ``1.0`` on this base -- a second
  break cannot add a second out-of-order label. Declared via
  :data:`DEGENERATE_LADDERS`, never presented as graded.

The specificity bar
--------------------
For metric ``f`` on ladder ``L`` (rung 0 included)::

    span_f(L) = max_r v_f(r) - min_r v_f(r)

-- the *range* the ladder drives the metric through (its response to a
*change* in severity, not a deviation from baseline: a metric that jumps to
a fixed offset on a foreign ladder and then ignores that ladder's severity
*is* insensitive to that mode in the sense Stage 18 means). Then::

    response(m, f) = span_f(L_m) / span_f(L_f)     response(m, m) == 1.0
    margin(m)      = 1.0 / max_{f != m} response(m, f)   (inf when the max is 0)

A ladder is **strictly specific** when ``margin(m) > 1.0``. Pairs with
``response(m, f) >= COUPLING_THRESHOLD`` are **recorded couplings** --
measured, named, caused, frozen in :data:`KNOWN_CROSS_MODE_COUPLINGS` -- so a
real cross-mode leak is published rather than buried in a pass/fail bit.
:data:`RECORDED_MARGINS` freezes every ladder's measured margin. Both tables
act as a *ratchet*: a future rule retune or feature change that flattens a
metric, or makes it more responsive to a foreign ladder, must fail
(``measured_response <= recorded * 1.05``, ``measured_margin >= recorded *
0.95``) rather than quietly eroding the stage's claim.

Purity & determinism contract
------------------------------
Every function here is pure: no file I/O, no clock, no mutation of the base
image/array any rung is derived from. All randomness is banned by
construction -- every ladder step passes explicit target labels, so no
operator ever consults ``seeded_rng`` for a choice; :data:`LADDER_SEED` is
still threaded through every ``apply()`` call to honour the
``Perturbation`` signature. Every ``to_dict()`` returns a plain-JSON
structure that round-trips through ``json.dumps``/``json.loads`` unchanged.

Scope fence
-----------
This module does **not**:

* change any metric -- :mod:`segfacet.eval.per_mode` is untouched; the only
  route to a metric value is a call to
  :func:`~segfacet.eval.per_mode.compute_per_mode_metrics`;
* change any operator or the corpus -- :mod:`segfacet.synth` and
  ``tests/corpus/**`` are untouched; no new perturbation is registered; the
  missing ``fuse`` corpus case (item 099's insight) is not added here, it is
  measured in-memory via :data:`SUPPLEMENTARY_LADDERS` instead;
* change any rule, threshold, schema or CLI surface;
* aggregate over a real cohort or read a manifest (item 101's job);
* make a real-data claim -- every ladder here is synthetic.

Public API
----------
``LadderRungSpec``, ``LadderSpec``, ``LadderPoint``, ``LadderResult``,
``HarnessResult``, ``LadderVerdict``, ``HarnessVerdict``,
``CrossModeCoupling`` (all frozen dataclasses); ``SEVERITY_LADDERS``,
``SUPPLEMENTARY_LADDERS``, ``DEGENERATE_LADDERS``,
``KNOWN_CROSS_MODE_COUPLINGS``, ``RECORDED_MARGINS``, ``COUPLING_THRESHOLD``,
``LADDER_SEED``; ``evaluate_ladder``, ``run_severity_harness``,
``score_harness``.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional, Tuple

import numpy as np

from segfacet.config import bundled_default_config
from segfacet.eval.per_mode import PER_MODE_METRIC_SPECS, PerModeMetrics, compute_per_mode_metrics
from segfacet.feature_report import overlap_to_dict
from segfacet.features.overlap import detect_overlaps
from segfacet.io import FacetInputError
from segfacet.pipeline import extract_feature_record
from segfacet.synth.clean_gt import DEFAULT_LEVELS, build_clean_spine
from segfacet.synth.perturbation import get_perturbation

__all__ = [
    "LadderRungSpec",
    "LadderSpec",
    "LadderPoint",
    "LadderResult",
    "HarnessResult",
    "LadderVerdict",
    "HarnessVerdict",
    "CrossModeCoupling",
    "SEVERITY_LADDERS",
    "SUPPLEMENTARY_LADDERS",
    "DEGENERATE_LADDERS",
    "KNOWN_CROSS_MODE_COUPLINGS",
    "RECORDED_MARGINS",
    "COUPLING_THRESHOLD",
    "LADDER_SEED",
    "evaluate_ladder",
    "run_severity_harness",
    "score_harness",
]


# --------------------------------------------------------------------------- #
# Module constants
# --------------------------------------------------------------------------- #

#: Every ladder step passes explicit target labels, so no operator ever
#: consults ``seeded_rng`` for a choice -- this seed only honours the
#: ``Perturbation.apply(labelmap, seed)`` signature, matching the committed
#: corpus recipe's seed (item 040).
LADDER_SEED: int = 0

#: A foreign metric's response to a ladder counts as a *recorded coupling*
#: once its span-ratio reaches this fraction of the metric's own full swing.
COUPLING_THRESHOLD: float = 0.25

#: The one ladder whose operator is structurally incapable of more than two
#: rungs (see the module docstring's "why three ladders have no continuous
#: knob" section, ``sequence_break``).
DEGENERATE_LADDERS = frozenset({"sequence_break"})

#: The base :func:`~segfacet.synth.clean_gt.build_clean_spine` parameters
#: every ladder's rung 0 -- and every later rung's fresh copy -- derives
#: from. Identical to the committed corpus's ``_DEFAULT_BASE_PARAMS``
#: (``synth/corpus.py``), so item 099's measured baselines carry over
#: unchanged and the ``force_overlap`` ladder's AC19 cross-check against the
#: corpus's ``1950.0`` holds.
_BASE_PARAMS: Mapping[str, Any] = MappingProxyType(
    {
        "levels": tuple(DEFAULT_LEVELS),
        "spacing": (1.0, 1.0, 1.0),
        "curve_amplitude_mm": 6.0,
    }
)


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class LadderRungSpec:
    """One rung of a severity ladder: an ordered list of perturbation steps.

    Attributes
    ----------
    index:
        Rung position, ``0`` for the clean control.
    severity:
        The rung's severity value on the ladder's declared axis. ``0.0`` for
        rung 0; strictly increasing thereafter.
    label:
        Human-readable label for this rung (e.g. ``"displacement_mm=8.0"``).
    steps:
        ``((operator_name, kwargs), ...)`` applied in order to a **fresh
        copy** of the ladder's base image. Empty for rung 0.
    """

    index: int
    severity: float
    label: str
    steps: Tuple[Tuple[str, Mapping[str, Any]], ...]

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "severity": self.severity,
            "label": self.label,
            "steps": [[name, dict(kwargs)] for name, kwargs in self.steps],
        }


@dataclass(frozen=True)
class LadderSpec:
    """Static declaration of one severity ladder.

    Attributes
    ----------
    failure_mode:
        The specification mode id (:data:`segfacet.failure_modes.SPECIFICATION`
        key) this ladder is homed on by rule (b), or ``None`` when the
        ladder's operator case is instead owned by a condition (see
        ``condition``) or by neither.
    failure_mode_name:
        ``SPECIFICATION[failure_mode].name`` when ``failure_mode`` is not
        ``None``; otherwise ``None``.
    operator:
        The perturbation registry name every rung's step(s) use. This is
        the registry key of :data:`SEVERITY_LADDERS`.
    designated_metric:
        The :data:`~segfacet.eval.per_mode.PER_MODE_METRIC_SPECS` key this
        ladder is built to isolate.
    condition:
        The :data:`segfacet.failure_modes.CONDITIONS` id this ladder's
        operator case is owned by, when ``failure_mode`` is ``None`` and a
        condition claims the case; ``None`` otherwise.
    severity_parameter:
        The operator constructor keyword (or ``"n_affected_labels"``) the
        severity axis represents.
    severity_kind:
        One of ``"continuous"``, ``"affected-label-count"``, ``"degenerate"``.
    rungs:
        The ordered :class:`LadderRungSpec` sequence, rung 0 first.
    rationale:
        Free-text rationale; non-empty and names the transitional-label cap
        (contains ``"28"``) for the degenerate ``sequence_break`` ladder.
    overlap_reconstruction:
        ``(target_label, neighbour_label)`` when this ladder needs the
        reconstructed ``overlaps`` block (``force_overlap`` only); ``None``
        otherwise.
    """

    failure_mode: Optional[int]
    failure_mode_name: Optional[str]
    operator: str
    designated_metric: str
    condition: Optional[str]
    severity_parameter: str
    severity_kind: str
    rungs: Tuple[LadderRungSpec, ...]
    rationale: str
    overlap_reconstruction: Optional[Tuple[int, int]]

    def to_dict(self) -> dict:
        return {
            "failure_mode": self.failure_mode,
            "failure_mode_name": self.failure_mode_name,
            "operator": self.operator,
            "designated_metric": self.designated_metric,
            "condition": self.condition,
            "severity_parameter": self.severity_parameter,
            "severity_kind": self.severity_kind,
            "rungs": [r.to_dict() for r in self.rungs],
            "rationale": self.rationale,
            "overlap_reconstruction": (
                list(self.overlap_reconstruction)
                if self.overlap_reconstruction is not None
                else None
            ),
            "degenerate": self.severity_kind == "degenerate",
        }


@dataclass(frozen=True)
class LadderPoint:
    """One rung's measured result: all eight per-mode metrics at that rung."""

    index: int
    severity: float
    label: str
    metrics: PerModeMetrics

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "severity": self.severity,
            "label": self.label,
            "metrics": self.metrics.to_dict(),
        }


@dataclass(frozen=True)
class LadderResult:
    """Raw per-rung measurements for one ladder -- no spans, no verdict."""

    spec: LadderSpec
    points: Tuple[LadderPoint, ...]

    def to_dict(self) -> dict:
        return {
            "spec": self.spec.to_dict(),
            "points": [p.to_dict() for p in self.points],
        }


@dataclass(frozen=True)
class HarnessResult:
    """The full ladder x metric response surface: all eight ladders plus the
    supplementary ``fuse`` ladder."""

    ladders: Tuple[LadderResult, ...]
    supplementary: Tuple[LadderResult, ...]
    base_params: Mapping[str, Any]

    def to_dict(self) -> dict:
        return {
            "ladders": [lr.to_dict() for lr in self.ladders],
            "supplementary": [lr.to_dict() for lr in self.supplementary],
            "base_params": _tuples_to_lists(dict(self.base_params)),
        }

    def by_operator(self, operator: str) -> LadderResult:
        """Return the primary ladder result for *operator*.

        Raises
        ------
        KeyError
            If no ladder in :attr:`ladders` has that ``operator``.
        """
        for lr in self.ladders:
            if lr.spec.operator == operator:
                return lr
        raise KeyError(operator)


@dataclass(frozen=True)
class CrossModeCoupling:
    """One measured, named, frozen cross-mode coupling entry.

    Attributes
    ----------
    ladder_operator:
        The ladder (by operator) driving the foreign metric.
    foreign_metric:
        The metric (by name) being driven (``!= `` the ladder's own
        ``designated_metric``).
    recorded_response:
        The measured ``response(ladder_operator, foreign_metric)``, rounded
        *up* to 4 significant figures.
    cause:
        Non-empty free-text naming the operator artefact responsible.
    """

    ladder_operator: str
    foreign_metric: str
    recorded_response: float
    cause: str


@dataclass(frozen=True)
class LadderVerdict:
    """The scored verdict for one ladder.

    Attributes
    ----------
    operator:
        This ladder's operator (:data:`SEVERITY_LADDERS` key).
    failure_mode:
        This ladder's home, copied from its :class:`LadderSpec` (nullable).
    status:
        ``"strict"`` (uncoupled, ``margin > 1.0``) or ``"coupled"`` (carries
        a :data:`KNOWN_CROSS_MODE_COUPLINGS` entry).
    responses:
        ``{metric_name: response(this_ladder, metric_name)}`` over all eight
        metrics; ``responses[this_ladder.designated_metric] == 1.0``.
    margin:
        ``1.0 / max_{f != designated_metric} responses[f]`` (``math.inf`` if
        that max is ``0.0``).
    coupled_metrics:
        Foreign metrics this ladder is recorded as coupled to (empty when
        ``status == "strict"``).
    failures:
        Human-readable failure reasons; empty iff this ladder passed.
    monotone:
        Whether the designated metric moved monotonically in its declared
        direction.
    strictly_changed:
        Whether the designated metric changed strictly at every rung
        transition.
    """

    operator: str
    failure_mode: Optional[int]
    status: str
    responses: Mapping[str, float]
    margin: float
    coupled_metrics: Tuple[str, ...]
    failures: Tuple[str, ...]
    monotone: bool
    strictly_changed: bool

    def to_dict(self) -> dict:
        return {
            "operator": self.operator,
            "failure_mode": self.failure_mode,
            "status": self.status,
            "responses": dict(self.responses),
            "margin": self.margin,
            "coupled_metrics": list(self.coupled_metrics),
            "failures": list(self.failures),
            "monotone": self.monotone,
            "strictly_changed": self.strictly_changed,
        }


@dataclass(frozen=True)
class HarnessVerdict:
    """The full scored verdict over every primary ladder.

    Attributes
    ----------
    passed:
        ``False`` iff any ladder is non-monotone, plateaus, or violates its
        recorded coupling/margin ratchet. A *recorded* coupling is a fact,
        not a failure.
    per_ladder:
        ``{operator: LadderVerdict}``.
    """

    passed: bool
    per_ladder: Mapping[str, LadderVerdict]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "per_ladder": {k: v.to_dict() for k, v in self.per_ladder.items()},
        }

    def summary(self) -> str:
        """A one-page, human-readable summary naming every coupled and every
        degenerate ladder -- the Stage-18 G2 claim in one page."""
        lines = [f"Severity-ladder harness verdict: passed={self.passed}"]
        for operator in sorted(self.per_ladder):
            lv = self.per_ladder[operator]
            if lv.status == "coupled":
                foreign = ", ".join(lv.coupled_metrics)
                lines.append(
                    f"  ladder {operator}: COUPLED with metric(s) {foreign} "
                    f"(margin={lv.margin:.4g})"
                )
            else:
                lines.append(f"  ladder {operator}: strict (margin={lv.margin:.4g})")
            if operator in DEGENERATE_LADDERS:
                rationale = (
                    SEVERITY_LADDERS[operator].rationale if operator in SEVERITY_LADDERS else ""
                )
                lines.append(f"    DEGENERATE ladder (2 rungs): {rationale}")
            for f in lv.failures:
                lines.append(f"    FAILURE: {f}")
        return "\n".join(lines)


def _tuples_to_lists(obj: Any) -> Any:
    """Recursively coerce any ``tuple`` in *obj* to a ``list``.

    Duplicated from :mod:`segfacet.eval.per_mode` (itself duplicated from
    ``segfacet.eval.metrics`` -- see that module for the rationale):
    ``dataclasses.asdict`` preserves tuple-typed fields as Python tuples,
    which do not compare equal to their own post ``json.dumps``/``json.loads``
    round-trip counterpart (always a list).
    """
    if isinstance(obj, tuple):
        return [_tuples_to_lists(v) for v in obj]
    if isinstance(obj, list):
        return [_tuples_to_lists(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _tuples_to_lists(v) for k, v in obj.items()}
    return obj


# --------------------------------------------------------------------------- #
# Ladder homes -- derived live from the specification/conditions/manifest,
# per the item spec's rule (b) (a ladder's home is rule (b) alone -- it has
# no candidate_features citation of its own to apply rule (a) against).
# --------------------------------------------------------------------------- #


def _ladder_home(operator: str) -> Tuple[Optional[int], Optional[str]]:
    """``(failure_mode, condition)`` for *operator*'s manifest case, per rule (b)."""
    import segfacet.failure_modes as failure_modes
    from segfacet.synth.corpus import load_manifest

    specification = failure_modes.SPECIFICATION
    conditions = failure_modes.CONDITIONS

    cases = load_manifest()["cases"]
    matches = [c["case_id"] for c in cases if c.get("perturbation") == operator]
    case_id = matches[0]

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
        return mode_hits[0], None
    if condition_hits:
        return None, condition_hits[0]
    return None, None


def _mode_name(failure_mode: Optional[int]) -> Optional[str]:
    if failure_mode is None:
        return None
    import segfacet.failure_modes as failure_modes

    return failure_modes.SPECIFICATION[failure_mode].name


# --------------------------------------------------------------------------- #
# The ladder registry -- the declarative table
# --------------------------------------------------------------------------- #


def _rung0(label: str = "clean control") -> LadderRungSpec:
    return LadderRungSpec(index=0, severity=0.0, label=label, steps=())


def _rung(index: int, severity: float, label: str, steps) -> LadderRungSpec:
    return LadderRungSpec(index=index, severity=float(severity), label=label, steps=tuple(steps))


def _displace_ladder() -> LadderSpec:
    rungs = [_rung0()]
    for i, s in enumerate((4.0, 8.0, 12.0, 16.0), start=1):
        rungs.append(
            _rung(
                i,
                s,
                f"displacement_mm={s}",
                [("displace", {"target_label": 22, "displacement_mm": s})],
            )
        )
    failure_mode, condition = _ladder_home("displace")
    return LadderSpec(
        failure_mode=failure_mode,
        failure_mode_name=_mode_name(failure_mode),
        operator="displace",
        designated_metric="unanchored_foreground_fraction",
        condition=condition,
        severity_parameter="displacement_mm",
        severity_kind="continuous",
        rungs=tuple(rungs),
        rationale="",
        overlap_reconstruction=None,
    )


def _fragment_ladder() -> LadderSpec:
    rungs = [_rung0()]
    for i, s in enumerate((2.0, 3.0, 4.0, 5.0), start=1):
        rungs.append(
            _rung(
                i,
                s,
                f"n_pieces={int(s)}",
                [("fragment", {"target_label": 22, "n_pieces": int(s)})],
            )
        )
    failure_mode, condition = _ladder_home("fragment")
    return LadderSpec(
        failure_mode=failure_mode,
        failure_mode_name=_mode_name(failure_mode),
        operator="fragment",
        designated_metric="min_dominant_component_fraction",
        condition=condition,
        severity_parameter="n_pieces",
        severity_kind="continuous",
        rungs=tuple(rungs),
        rationale="",
        overlap_reconstruction=None,
    )


def _inject_islands_ladder() -> LadderSpec:
    rungs = [_rung0()]
    for i, s in enumerate((1.0, 2.0, 3.0, 4.0), start=1):
        rungs.append(
            _rung(
                i,
                s,
                f"n_islands={int(s)}",
                [
                    (
                        "inject_islands",
                        {"target_label": 22, "n_islands": int(s), "island_voxels": 27},
                    )
                ],
            )
        )
    failure_mode, condition = _ladder_home("inject_islands")
    return LadderSpec(
        failure_mode=failure_mode,
        failure_mode_name=_mode_name(failure_mode),
        operator="inject_islands",
        designated_metric="rogue_island_count",
        condition=condition,
        severity_parameter="n_islands",
        severity_kind="continuous",
        rungs=tuple(rungs),
        rationale="",
        overlap_reconstruction=None,
    )


def _relabel_swap_ladder() -> LadderSpec:
    # Two disjoint adjacent swaps: (20, 21) then (22, 23); label 24 untouched.
    # Five labels admit only two disjoint adjacent pairs -- 3 rungs, not 4.
    swap1 = ("relabel_swap", {"target_label": 20, "neighbour_label": 21})
    swap2 = ("relabel_swap", {"target_label": 22, "neighbour_label": 23})
    rungs = [
        _rung0(),
        _rung(1, 2.0, "n_affected_labels=2", [swap1]),
        _rung(2, 4.0, "n_affected_labels=4", [swap1, swap2]),
    ]
    failure_mode, condition = _ladder_home("relabel_swap")
    return LadderSpec(
        failure_mode=failure_mode,
        failure_mode_name=_mode_name(failure_mode),
        operator="relabel_swap",
        designated_metric="mislabelled_volume_fraction",
        condition=condition,
        severity_parameter="n_affected_labels",
        severity_kind="affected-label-count",
        rungs=tuple(rungs),
        rationale=(
            "Only 2 disjoint adjacent label pairs exist among the 5-level "
            "base, so this ladder is 3 rungs (not 4)."
        ),
        overlap_reconstruction=None,
    )


def _remove_level_ladder() -> LadderSpec:
    # Cumulative interior removals: 21, then +22, then +23.
    rem21 = ("remove_level", {"target_label": 21})
    rem22 = ("remove_level", {"target_label": 22})
    rem23 = ("remove_level", {"target_label": 23})
    rungs = [
        _rung0(),
        _rung(1, 1.0, "n_affected_labels=1", [rem21]),
        _rung(2, 2.0, "n_affected_labels=2", [rem21, rem22]),
        _rung(3, 3.0, "n_affected_labels=3", [rem21, rem22, rem23]),
    ]
    failure_mode, condition = _ladder_home("remove_level")
    return LadderSpec(
        failure_mode=failure_mode,
        failure_mode_name=_mode_name(failure_mode),
        operator="remove_level",
        designated_metric="missing_level_count",
        condition=condition,
        severity_parameter="n_affected_labels",
        severity_kind="affected-label-count",
        rungs=tuple(rungs),
        rationale="Removes the 3 interior levels (21, 22, 23) one at a time.",
        overlap_reconstruction=None,
    )


def _crop_at_border_ladder() -> LadderSpec:
    # Cumulative crops (anterior face, crop_depth pinned at the corpus's 5):
    # 20, then +21, then +22 -- fov_clipped_label_count is a count of labels,
    # invariant to crop_depth, so the severity axis is the number cropped.
    crop20 = ("crop_at_border", {"target_label": 20, "face": "anterior", "crop_depth": 5})
    crop21 = ("crop_at_border", {"target_label": 21, "face": "anterior", "crop_depth": 5})
    crop22 = ("crop_at_border", {"target_label": 22, "face": "anterior", "crop_depth": 5})
    rungs = [
        _rung0(),
        _rung(1, 1.0, "n_affected_labels=1", [crop20]),
        _rung(2, 2.0, "n_affected_labels=2", [crop20, crop21]),
        _rung(3, 3.0, "n_affected_labels=3", [crop20, crop21, crop22]),
    ]
    failure_mode, condition = _ladder_home("crop_at_border")
    return LadderSpec(
        failure_mode=failure_mode,
        failure_mode_name=_mode_name(failure_mode),
        operator="crop_at_border",
        designated_metric="fov_clipped_label_count",
        condition=condition,
        severity_parameter="n_affected_labels",
        severity_kind="affected-label-count",
        rungs=tuple(rungs),
        rationale=(
            "fov_clipped_label_count is a count of labels, invariant to "
            "crop_depth (pinned at the corpus's 5); the severity axis is "
            "the number of clipped labels instead."
        ),
        overlap_reconstruction=None,
    )


def _sequence_break_ladder() -> LadderSpec:
    # Degenerate: out_of_order_label_count is capped at 1.0 on this base --
    # 28 (T13) is the only value whose canonical rank (19) falls below its
    # integer position, and it always sorts last, contributing at most one
    # descent. A second break cannot add a second out-of-order label.
    rungs = [
        _rung0(),
        _rung(1, 1.0, "sequence_break", [("sequence_break", {})]),
    ]
    failure_mode, condition = _ladder_home("sequence_break")
    return LadderSpec(
        failure_mode=failure_mode,
        failure_mode_name=_mode_name(failure_mode),
        operator="sequence_break",
        designated_metric="out_of_order_label_count",
        condition=condition,
        severity_parameter="n/a",
        severity_kind="degenerate",
        rungs=tuple(rungs),
        rationale=(
            "Structurally capped at 1 rung of severity: under the default "
            "(TPTBox) convention, rank(v) == v - 1 for every value 1-24, so "
            "no in-block relabel produces a rank descent. The one label "
            "that can -- 28 (T13), rank 19 -- always sorts last and "
            "contributes at most one descent, so out_of_order_label_count "
            "is capped at 1.0 and a second break cannot add a second "
            "out-of-order label."
        ),
        overlap_reconstruction=None,
    )


def _force_overlap_ladder() -> LadderSpec:
    rungs = [_rung0()]
    for i, s in enumerate((1.0, 2.0, 3.0, 4.0), start=1):
        rungs.append(
            _rung(
                i,
                s,
                f"overlap_depth={int(s)}",
                [
                    (
                        "force_overlap",
                        {"target_label": 20, "neighbour_label": 21, "overlap_depth": int(s)},
                    )
                ],
            )
        )
    failure_mode, condition = _ladder_home("force_overlap")
    return LadderSpec(
        failure_mode=failure_mode,
        failure_mode_name=_mode_name(failure_mode),
        operator="force_overlap",
        designated_metric="overlapping_voxel_count",
        condition=condition,
        severity_parameter="overlap_depth",
        severity_kind="continuous",
        rungs=tuple(rungs),
        rationale="",
        overlap_reconstruction=(20, 21),
    )


def _fuse_ladder() -> LadderSpec:
    # Cumulative fuse absorptions: 21 into 20, then +22, then +23 -- the
    # fused counterpart of the fragment ladder's designated metric
    # (fragment covers the fragmented half), measured in memory rather than
    # as a tenth corpus recipe entry (see the item's Assumptions).
    fuse21 = ("fuse", {"target_label": 20, "neighbour_label": 21})
    fuse22 = ("fuse", {"target_label": 20, "neighbour_label": 22})
    fuse23 = ("fuse", {"target_label": 20, "neighbour_label": 23})
    rungs = [
        _rung0(),
        _rung(1, 1.0, "n_fused_neighbours=1", [fuse21]),
        _rung(2, 2.0, "n_fused_neighbours=2", [fuse21, fuse22]),
        _rung(3, 3.0, "n_fused_neighbours=3", [fuse21, fuse22, fuse23]),
    ]
    failure_mode, condition = _ladder_home("fuse")
    return LadderSpec(
        failure_mode=failure_mode,
        failure_mode_name=_mode_name(failure_mode),
        operator="fuse",
        designated_metric="min_dominant_component_fraction",
        condition=condition,
        severity_parameter="n_fused_neighbours",
        severity_kind="affected-label-count",
        rungs=tuple(rungs),
        rationale=(
            "Supplementary: closes the fragment ladder's designated "
            "metric's fused half (fragment itself covers the fragmented "
            "half). Excluded from the eight-ladder cross-mode matrix so "
            "that matrix stays a square 8x8."
        ),
        overlap_reconstruction=None,
    )


#: The eight severity ladders, keyed by operator.
SEVERITY_LADDERS: Mapping[str, LadderSpec] = MappingProxyType(
    {
        "displace": _displace_ladder(),
        "fragment": _fragment_ladder(),
        "inject_islands": _inject_islands_ladder(),
        "relabel_swap": _relabel_swap_ladder(),
        "remove_level": _remove_level_ladder(),
        "crop_at_border": _crop_at_border_ladder(),
        "sequence_break": _sequence_break_ladder(),
        "force_overlap": _force_overlap_ladder(),
    }
)

#: The supplementary ``fuse`` ladder closing the fragment ladder's designated
#: metric's fused half -- outside the eight-ladder cross-mode matrix
#: (``score_harness`` ignores it entirely).
SUPPLEMENTARY_LADDERS: Tuple[LadderSpec, ...] = (_fuse_ladder(),)


# --------------------------------------------------------------------------- #
# Case construction & per-rung measurement
# --------------------------------------------------------------------------- #


def _apply_steps(base_img, steps: Tuple[Tuple[str, Mapping[str, Any]], ...]):
    """Apply *steps* in order to a fresh derivation of *base_img*.

    Never mutates *base_img* -- every registered operator already copies its
    input array before writing, and this function itself never writes to
    ``base_img``'s array.

    Raises
    ------
    KeyError
        If a step names an unregistered operator (propagated from
        :func:`~segfacet.synth.perturbation.get_perturbation`).
    segfacet.io.FacetInputError
        If any operator rejects its parameters/state (e.g. an
        out-of-FOV displacement) -- propagates immediately, never truncating
        the ladder.
    """
    current = base_img
    for name, kwargs in steps:
        operator_cls = get_perturbation(name)
        operator = operator_cls(**dict(kwargs))
        result = operator.apply(current, LADDER_SEED)
        current = result.labelmap
    return current


def _measure(
    base_arr: np.ndarray,
    perturbed_img,
    spec: LadderSpec,
    rung: LadderRungSpec,
    config,
) -> LadderPoint:
    """Build the :class:`LadderPoint` for one already-perturbed rung."""
    perturbed_arr = np.asanyarray(perturbed_img.dataobj)
    record = extract_feature_record(perturbed_img, config)

    if spec.overlap_reconstruction is not None:
        target, neighbour = spec.overlap_reconstruction
        stack = np.stack([perturbed_arr == target, base_arr == neighbour])
        pairs = detect_overlaps(stack, np.array([target, neighbour]))
        record = dict(record)
        record["overlaps"] = [overlap_to_dict(p) for p in pairs]

    spacing = tuple(float(z) for z in perturbed_img.header.get_zooms()[:3])
    metrics = compute_per_mode_metrics(
        record,
        candidate=perturbed_arr,
        gt=base_arr,
        spacing=spacing,
    )
    return LadderPoint(index=rung.index, severity=rung.severity, label=rung.label, metrics=metrics)


# --------------------------------------------------------------------------- #
# evaluate_ladder
# --------------------------------------------------------------------------- #


def evaluate_ladder(spec: LadderSpec, *, base=None, config=None) -> LadderResult:
    """Run every rung of *spec* and return the raw per-rung measurements.

    Parameters
    ----------
    spec:
        The :class:`LadderSpec` to evaluate.
    base:
        A :class:`~segfacet.synth.clean_gt.CleanSpine` to derive every rung
        from. Defaults to ``build_clean_spine(**_BASE_PARAMS)`` -- the same
        default L1-L5 base the committed corpus uses.
    config:
        A :class:`~segfacet.config.HeuristicConfig`. Defaults to
        :func:`~segfacet.config.bundled_default_config`.

    Returns
    -------
    LadderResult
        Carries raw data only: no spans, no responses, no verdict --
        scoring is a pure function of the result (see :func:`score_harness`).

    Raises
    ------
    KeyError
        If a rung names an unregistered operator.
    segfacet.io.FacetInputError
        If any rung's operator rejects its parameters/state.
    """
    if base is None:
        base = build_clean_spine(**_BASE_PARAMS)
    if config is None:
        config = bundled_default_config()

    base_seg = base.seg_img
    base_arr = np.array(np.asanyarray(base_seg.dataobj), copy=True)

    points: List[LadderPoint] = []
    for rung in spec.rungs:
        perturbed_img = _apply_steps(base_seg, rung.steps)
        points.append(_measure(base_arr, perturbed_img, spec, rung, config))
    return LadderResult(spec=spec, points=tuple(points))


# --------------------------------------------------------------------------- #
# run_severity_harness
# --------------------------------------------------------------------------- #


def run_severity_harness(*, base=None, config=None) -> HarnessResult:
    """Evaluate the eight ladders plus the supplementary one.

    Parameters
    ----------
    base, config:
        As in :func:`evaluate_ladder`.

    Returns
    -------
    HarnessResult
    """
    if base is None:
        base = build_clean_spine(**_BASE_PARAMS)
    if config is None:
        config = bundled_default_config()

    base_seg = base.seg_img
    base_arr = np.array(np.asanyarray(base_seg.dataobj), copy=True)
    spacing = tuple(float(z) for z in base_seg.header.get_zooms()[:3])

    # Rung 0 is the same clean base for every ladder (its reconstructed
    # overlaps block is empty regardless), so it is computed once and shared
    # -- see the item spec's Implementation Steps.
    shared_rung0_record = extract_feature_record(base_seg, config)
    shared_rung0_metrics = compute_per_mode_metrics(
        shared_rung0_record,
        candidate=base_arr,
        gt=base_arr,
        spacing=spacing,
    )
    shared_rung0 = LadderPoint(
        index=0, severity=0.0, label="clean control", metrics=shared_rung0_metrics
    )

    def _build(spec: LadderSpec) -> LadderResult:
        points: List[LadderPoint] = [shared_rung0]
        for rung in spec.rungs[1:]:
            perturbed_img = _apply_steps(base_seg, rung.steps)
            points.append(_measure(base_arr, perturbed_img, spec, rung, config))
        return LadderResult(spec=spec, points=tuple(points))

    ladders = tuple(_build(SEVERITY_LADDERS[op]) for op in SEVERITY_LADDERS)
    supplementary = tuple(_build(spec) for spec in SUPPLEMENTARY_LADDERS)

    return HarnessResult(
        ladders=ladders,
        supplementary=supplementary,
        base_params=dict(_BASE_PARAMS),
    )


# --------------------------------------------------------------------------- #
# score_harness
# --------------------------------------------------------------------------- #


def _span(values: List[float]) -> float:
    return max(values) - min(values)


def score_harness(
    harness: HarnessResult, *, assignment: Optional[Mapping[str, str]] = None
) -> HarnessVerdict:
    """Score *harness*'s response surface: monotonicity, specificity, ratchets.

    Parameters
    ----------
    harness:
        A :class:`HarnessResult`, typically from :func:`run_severity_harness`.
        Only :attr:`HarnessResult.ladders` is read -- ``supplementary`` is
        ignored entirely (AC21).
    assignment:
        ``{operator: metric_name}``, applied as an override on top of the
        default ``{op: spec.designated_metric for op, spec in
        SEVERITY_LADDERS.items()}`` -- a caller may supply a partial mapping
        naming only the operator(s) it wants to override; every operator it
        omits keeps its own designated metric. Maps each ladder to the
        metric scored as its "designated" one for monotonicity/strict-change
        purposes; the response/margin surface itself is
        assignment-independent (a ladder's response to every metric is
        always reported).

    Returns
    -------
    HarnessVerdict

    Raises
    ------
    segfacet.io.FacetInputError
        If the resolved assignment maps an operator to a value that is not a
        :data:`~segfacet.eval.per_mode.PER_MODE_METRIC_SPECS` key.
    """
    resolved_assignment = {op: spec.designated_metric for op, spec in SEVERITY_LADDERS.items()}
    if assignment is not None:
        resolved_assignment.update(assignment)
    assignment = resolved_assignment

    ladders = harness.ladders
    if not ladders:
        return HarnessVerdict(passed=True, per_ladder=MappingProxyType({}))

    metric_names = list(PER_MODE_METRIC_SPECS)

    # Each metric's own ladder -- the operator whose designated_metric is
    # that metric (AC18 guarantees this is total and one-to-one over the
    # ladders present). Needed because operators and metric names are
    # different key spaces here (unlike the legacy scheme, where a ladder's
    # own mode number doubled as its metric's identity).
    owning_operator = {lr.spec.designated_metric: lr.spec.operator for lr in ladders}

    # Spans over every (ladder_operator, metric_name) pair -- assignment-independent.
    spans: Dict[str, Dict[str, float]] = {}
    for lr in ladders:
        op = lr.spec.operator
        spans[op] = {}
        for f in metric_names:
            values = [pt.metrics.by_metric(f).value for pt in lr.points]
            spans[op][f] = _span(values)

    per_ladder: Dict[str, LadderVerdict] = {}
    for lr in ladders:
        op = lr.spec.operator
        designated = assignment[op]
        if designated not in PER_MODE_METRIC_SPECS:
            raise FacetInputError(
                f"score_harness: assignment[{op!r}]={designated!r} is not a "
                "valid metric name."
            )

        responses: Dict[str, float] = {}
        for f in metric_names:
            denom_operator = owning_operator.get(f)
            if denom_operator is None or denom_operator not in spans:
                responses[f] = math.inf
                continue
            denom = spans[denom_operator][f]
            responses[f] = math.inf if denom == 0.0 else spans[op][f] / denom

        others = [responses[f] for f in metric_names if f != designated]
        mx = max(others) if others else 0.0
        margin = math.inf if mx == 0.0 else 1.0 / mx

        failures: List[str] = []
        n_points = len(lr.points)
        if n_points < 2:
            failures.append(
                f"ladder {op}: only {n_points} rung(s) -- cannot assess "
                "monotonicity or strict change (zero-span guard, not a "
                "division by zero)."
            )
            monotone = True
            strictly_changed = False
        else:
            direction = PER_MODE_METRIC_SPECS[designated].direction
            values = [pt.metrics.by_metric(designated).value for pt in lr.points]
            if direction == "increases":
                monotone = all(a <= b for a, b in zip(values, values[1:]))
            else:
                monotone = all(a >= b for a, b in zip(values, values[1:]))
            strictly_changed = all(abs(b - a) > 1e-9 for a, b in zip(values, values[1:]))

            if not monotone:
                failures.append(
                    f"ladder {op} scored against metric {designated}: not "
                    f"monotone in the declared direction ({direction}): {values!r}."
                )
            if not strictly_changed:
                failures.append(
                    f"ladder {op} scored against metric {designated}: "
                    f"plateaus somewhere across rungs: {values!r}."
                )

            # A designated metric can happen to move monotonically and
            # non-trivially on the WRONG ladder too (a small, real,
            # deterministic side-effect) without that ladder actually being
            # the metric's best/most-specific driver. Require this ladder's
            # response to the designated metric to be at least as large as
            # the response the metric's own true ladder achieves for itself
            # (which is exactly 1.0) -- true by construction for an honest
            # (identity) assignment, and the criterion a mis-assignment
            # (AC18's negative control) must fail.
            own_response = responses.get(designated, math.inf)
            if own_response < 1.0 - 1e-9:
                failures.append(
                    f"ladder {op} scored against metric {designated}: this "
                    f"ladder is not that metric's best/most-specific driver "
                    f"(response={own_response!r} < 1.0, the response metric "
                    f"{designated}'s own true ladder achieves for itself)."
                )

        coupling_entries = [c for c in KNOWN_CROSS_MODE_COUPLINGS if c.ladder_operator == op]
        if coupling_entries:
            status = "coupled"
            coupled_metrics = tuple(sorted(c.foreign_metric for c in coupling_entries))
            for c in coupling_entries:
                measured = responses.get(c.foreign_metric, math.inf)
                if measured > c.recorded_response * 1.05:
                    failures.append(
                        f"ladder {op}: coupling ratchet violated for foreign "
                        f"metric {c.foreign_metric}: measured response "
                        f"{measured!r} exceeds recorded "
                        f"{c.recorded_response!r} * 1.05."
                    )
        else:
            status = "strict"
            coupled_metrics = ()

        recorded_margin = RECORDED_MARGINS.get(op)
        if recorded_margin is not None and not (margin >= recorded_margin * 0.95):
            failures.append(
                f"ladder {op}: margin ratchet violated: measured margin "
                f"{margin!r} is below recorded {recorded_margin!r} * 0.95."
            )

        per_ladder[op] = LadderVerdict(
            operator=op,
            failure_mode=lr.spec.failure_mode,
            status=status,
            responses=MappingProxyType(responses),
            margin=margin,
            coupled_metrics=coupled_metrics,
            failures=tuple(failures),
            monotone=monotone,
            strictly_changed=strictly_changed,
        )

    passed = all(len(lv.failures) == 0 for lv in per_ladder.values())
    return HarnessVerdict(passed=passed, per_ladder=MappingProxyType(per_ladder))


# --------------------------------------------------------------------------- #
# Frozen ratchet constants -- filled by running the harness once and
# transcribing the measured values (recorded responses rounded UP, recorded
# margins rounded DOWN, both to 4 significant figures, so the ratchet has no
# float-equality knife edge). See the item's Decisions log for the measured
# run this was transcribed from. Item 153 (A5): every value below moved
# verbatim to its new key; none was recomputed or changed.
# --------------------------------------------------------------------------- #

#: Two measured cross-mode couplings. ``crop_at_border`` ->
#: ``unanchored_foreground_fraction`` was anticipated by item 099 (see the
#: module docstring and the item's Assumptions): ``crop_at_border``,
#: ``displace`` and ``force_overlap`` all translate a body rigidly, so all
#: three put candidate foreground over GT background -- and the ``displace``
#: ladder is FOV-capped (~19.8 mm max ``displacement_mm`` on this base) while
#: ``crop_at_border``'s scales linearly with the number of cropped labels, so
#: it *exceeds* the strict bar (response > 1.0), exactly as predicted.
#: ``force_overlap`` -> ``unanchored_foreground_fraction`` was **not**
#: anticipated by item 099 (whose Assumptions named only the crop coupling)
#: and is recorded here per the item's instruction to call out any
#: additional measured coupling in the Decisions log: ``force_overlap``
#: shifts the whole target body by ``gap + overlap_depth`` voxels along the
#: stacking axis, and the constant 15 mm inter-body gap dominates that
#: shift, so most of ``force_overlap``'s ``unanchored_foreground_fraction``
#: response is a rigid-translation artefact largely independent of
#: ``overlap_depth`` -- its span nearly matches the ``displace`` ladder's own
#: full swing (measured response 0.9629, margin only ~1.039), even though
#: ``force_overlap``'s own designated metric (``overlapping_voxel_count``)
#: remains a clean, strictly specific isolator.
KNOWN_CROSS_MODE_COUPLINGS: Tuple[CrossModeCoupling, ...] = (
    CrossModeCoupling(
        ladder_operator="crop_at_border",
        foreign_metric="unanchored_foreground_fraction",
        recorded_response=2.79,
        cause=(
            "crop_at_border rigidly translates each cropped body toward the "
            "FOV face (like displace/force_overlap), placing candidate "
            "foreground over GT background; crop_at_border's "
            "n_affected_labels axis scales this linearly across 3 rungs "
            "while the displace ladder is capped by the FOV (~19.8mm max "
            "displacement_mm on this base)."
        ),
    ),
    CrossModeCoupling(
        ladder_operator="force_overlap",
        foreign_metric="unanchored_foreground_fraction",
        recorded_response=0.9629,
        cause=(
            "force_overlap shifts the whole target body by gap + "
            "overlap_depth voxels along the stacking axis; the constant "
            "15mm inter-body gap dominates that shift, so most of the "
            "unanchored-foreground signal is a rigid-translation artefact "
            "largely independent of overlap_depth, nearly matching the "
            "displace ladder's own full swing."
        ),
    ),
)

#: Every ladder's measured margin (``1.0 / max_{f != designated} response``),
#: rounded down to 4 significant figures (``math.inf`` kept as-is where the
#: measured max foreign response is exactly ``0.0``). Item 153: values moved
#: verbatim to their new operator key.
RECORDED_MARGINS: Mapping[str, float] = MappingProxyType(
    {
        "displace": math.inf,
        "fragment": math.inf,
        "inject_islands": 112.0,
        "relabel_swap": math.inf,
        "remove_level": math.inf,
        "crop_at_border": 0.3585,
        "sequence_break": math.inf,
        "force_overlap": 1.038,
    }
)
