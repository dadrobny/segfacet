"""Overlap rule (item 032).

Implements an **overlap rule** targeting failure mode 15 (overlapping
segments) in ``failure_modes.SPECIFICATION``: voxels assigned to more than one vertebra label, or labels whose
masks intersect. It consumes the pre-computed overlap-detection results (item
015, exposed at the per-case feature record's ``pairs.overlaps`` key (item
216; formerly the top-level ``overlaps`` key), assembled by
``build_features_block`` / ``overlap_to_dict``, item 016). It does
not re-derive overlaps and never touches a mask stack or label map.

Design decisions (recorded per item 032 spec):
- The rule reads ``record["pairs"]["overlaps"]`` and, for the level names it
  prints (merged onto ``per_label.{label}.level_name`` by item 216), each
  overlapping label's ``per_label`` entry -- never ``case.sequence``,
  ``geometry``, or any mm/spacing/extent/volume field -- so it is inherently
  spacing-agnostic.
- Any non-list ``pairs.overlaps`` (absent, ``None``, or a non-list placeholder
  such as ``{}``) is treated as "no overlaps" and yields no finding.
- One finding per overlapping pair, label-attributed with
  ``frozenset({label_a, label_b})`` (both offenders are present, real
  labels — unlike item 029's case-level missing-level findings).
- A config-driven minimum-overlap threshold (``min_overlap_voxels``, default
  ``1``) gates each finding: a pair fires iff ``overlap_voxels >=
  min_overlap_voxels``.
- Findings are emitted in ascending ``(label_a, label_b)`` order, re-sorted
  defensively regardless of input order, for determinism.
- Unrecognised severity string raises ValueError before any per-record
  processing.
- The caller's record is never mutated.
"""

from __future__ import annotations

from typing import Dict, List

from segfacet.heuristics.finding import Finding
from segfacet.heuristics.rule import (
    ConsumedPath,
    Rule,
    RuleDetector,
    RuleModeDeclaration,
    register_rule,
)
from segfacet.verdict import Severity

__all__ = ["OverlapRule"]


_OVERLAP_TAG = "Overlapping segments:"
_DEFAULT_MIN_OVERLAP_VOXELS = 1


# --------------------------------------------------------------------------- #
# Severity helper (mirrors bounds.py / coverage.py / sequence.py / border.py)
# --------------------------------------------------------------------------- #

_LABEL_TO_SEVERITY: Dict[str, Severity] = {sev.label: sev for sev in Severity}


def _severity_from_param(label: str) -> Severity:
    """Map a severity label string to its Severity member.

    Raises
    ------
    ValueError
        If *label* is not a recognised Severity label string.
    """
    sev = _LABEL_TO_SEVERITY.get(label)
    if sev is None:
        known = list(_LABEL_TO_SEVERITY.keys())
        raise ValueError(
            f"Unknown severity label {label!r} in overlap rule config. "
            f"Known labels: {known}."
        )
    return sev


def _level_name(per_label: dict, label: int) -> str:
    """The level name of *label* from its ``per_label`` entry (item 216: the
    merged ``overlaps[].name_a``/``name_b``); the label itself when absent."""
    entry = per_label.get(str(label), per_label.get(label))
    name = entry.get("level_name") if isinstance(entry, dict) else None
    return name if isinstance(name, str) else str(label)


def _sort_key(item):
    """Sort normalised overlap entries by ascending (label_a, label_b), with
    None sorted last."""
    label_a, label_b, _voxels, _name_a, _name_b = item
    a_key = (0, label_a) if label_a is not None else (1, 0)
    b_key = (0, label_b) if label_b is not None else (1, 0)
    return (a_key, b_key)


# --------------------------------------------------------------------------- #
# OverlapRule
# --------------------------------------------------------------------------- #


@register_rule
class OverlapRule(Rule):
    """Overlap rule (item 032).

    Emits one label-attributed finding per overlapping label pair whose
    shared-voxel count meets the configured minimum, in ascending
    ``(label_a, label_b)`` order.
    """

    rule_id = "overlap"

    # Specification mode 15 (overlapping segments): this rule is kept and
    # declared to need multi-channel input, which no committed corpus case
    # can express (item 195, 2026-09-28) -- see the per-edge rung in
    # segfacet.failure_modes.SPECIFICATION[15].
    mode_declaration = RuleModeDeclaration(
        modes=(15,),
        evidence=(
            "analytic",
            "needs multi-channel input: pairs.overlaps[] is non-empty only when two "
            "labels claim one voxel, which a single-channel integer label map "
            "cannot express, so the pipeline's one-hot mask stack yields no "
            "overlap on any input FACET accepts today. Mode 15 (overlapping "
            "segments) of the catalogue signed off at item 150; the per-edge "
            "rung in segfacet.failure_modes.SPECIFICATION[15] is "
            "structurally-unobservable, and no committed corpus case designates "
            "this rule (item 195, 2026-09-28).",
        ),
        consumed_paths=(
            ConsumedPath(
                path="pairs.overlaps[]",
                role="bookkeeping",
                reason=(
                    "container: iterated to reach each pair's voxel count"
                ),
            ),
            ConsumedPath(
                path="pairs.overlaps[].label_a",
                role="bookkeeping",
                reason=(
                    "identity: one side of the overlapping pair, carried "
                    "into the finding's labels set"
                ),
            ),
            ConsumedPath(
                path="pairs.overlaps[].label_b",
                role="bookkeeping",
                reason=(
                    "identity: the other side of the overlapping pair"
                ),
            ),
            ConsumedPath(
                path="pairs.overlaps[].overlap_voxels",
                role="signal",
            ),
            ConsumedPath(
                path="per_label",
                role="bookkeeping",
                reason=(
                    "container: looked up by label to reach each side's "
                    "level name"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.level_name",
                role="bookkeeping",
                reason=(
                    "message interpolation: each side's level name printed "
                    "in the finding (the merged overlaps[].name_a/name_b)"
                ),
            ),
        ),
        detectors=(
            RuleDetector(
                detector_id="overlapping_segments",
                description=_OVERLAP_TAG,
                question=(
                    "Do two labels claim the same voxels?"
                ),
                fires_when=(
                    "a pair's `overlap_voxels` >= `min_overlap_voxels` "
                    "(inclusive); one finding per pair"
                ),
                params=(("min_overlap_voxels", _DEFAULT_MIN_OVERLAP_VOXELS),),
                signal_paths=("pairs.overlaps[].overlap_voxels",),
            ),
        ),
    )

    def evaluate(self, record, config) -> List[Finding]:  # type: ignore[override]
        """Evaluate overlap findings for *record*.

        Parameters
        ----------
        record:
            Per-case feature dict (read-only). Reads
            ``record["pairs"]["overlaps"]`` and ``record["per_label"]``.
        config:
            HeuristicConfig instance. Reads ``rules.overlap.params``.

        Returns
        -------
        list[Finding]
            Zero or more findings, one per offending pair, in ascending
            ``(label_a, label_b)`` order.

        Raises
        ------
        ValueError
            If ``rules.overlap.params.severity`` is an unrecognised string
            (raised before any per-record processing, AC11).
        """
        # Read severity and threshold once up-front; raises immediately on a
        # bad severity string.
        sev_label: str = config.rule_param(
            self.rule_id, "severity", default="flagged-for-review"
        )
        severity = _severity_from_param(sev_label)

        min_overlap = int(
            config.rule_param(
                self.rule_id, "min_overlap_voxels", default=_DEFAULT_MIN_OVERLAP_VOXELS
            )
        )

        findings: List[Finding] = []

        pairs = record.get("pairs")
        overlaps = pairs.get("overlaps") if isinstance(pairs, dict) else None
        per_label = record.get("per_label")
        if not isinstance(per_label, dict):
            per_label = {}
        if not isinstance(overlaps, list):
            return findings  # AC2, AC13 — absent / None / non-list placeholder

        normalised = []
        for entry in overlaps:
            if not isinstance(entry, dict):
                continue
            raw_a = entry.get("label_a")
            raw_b = entry.get("label_b")
            if raw_a is None or raw_b is None:
                continue  # AC13 — both labels required to attribute a finding
            label_a = int(raw_a)
            label_b = int(raw_b)
            voxels = int(entry.get("overlap_voxels", 0) or 0)
            name_a = _level_name(per_label, label_a)
            name_b = _level_name(per_label, label_b)
            normalised.append((label_a, label_b, voxels, name_a, name_b))

        normalised.sort(key=_sort_key)

        for label_a, label_b, voxels, name_a, name_b in normalised:
            if voxels < min_overlap:
                continue
            labels = frozenset(l for l in (label_a, label_b) if l is not None)
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=severity,
                    reason=(
                        f"{_OVERLAP_TAG} labels {label_a} ({name_a}) and "
                        f"{label_b} ({name_b}) share {voxels} voxel(s)."
                    ),
                    labels=labels,
                    detector_id="overlapping_segments",
                )
            )

        return findings
