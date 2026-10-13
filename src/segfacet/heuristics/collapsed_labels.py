"""Collapsed-labels rule (item 220), serving mode 13 (collapsed labels).

Two labels whose centroids coincide exactly make Stage 3 absent: the record
carries ``stage3_unavailable`` (item 129) instead of ``case.curve``, every
Stage-3 rule returns early and no finding names the collapse. This rule emits
one ``flagged-for-review`` finding per collapsed pair, through two detectors:

- ``coincident_centroids`` reads ``stage3_unavailable`` and fires once, on the
  pair the key names, quoting its ``reason`` and ``detail`` (A6: any reason).
- ``near_coincident_centroids`` reads every label's
  ``per_label.{label}.centroid.centroid_mm[]`` and fires on each pair within
  ``max_centroid_distance_mm`` (default 2.0 mm), except the pair already
  reported by the first detector (A5).

Design decisions (item 220 spec, A3-A7):
- **Absolute tolerance (A3)**, measured 2026-10-12 at ``2a1491d`` with
  ``features.centroids.compute_centroid``: closest legitimate pair 12.542 mm
  in the geometric corpus (``split_own_label`` L3-L4), 32.695 mm in the
  intensity corpus, 11.082 mm over 159 VerSe19 GT masks. Absolute, because the
  collapsed pair's own spacing is the one that shrinks and a two- or
  three-label record has no robust reference spacing.
- **All pairs (A4)**, visited in ascending ``(int, int)`` order; the test is
  ``math.dist <= tolerance`` over the physical-mm centroids.
- **fov_truncation opt-in (A7)**: a crop cannot bring two labels on different
  vertebrae within 2 mm, so a border-touching collapsed pair stays valid.
  No ``displaced_vertebra`` opt-in (left open).
- Absence-tolerant: a label whose centroid is absent or not a length-3
  numeric list is skipped; a non-dict ``per_label`` or non-integer key is not
  judged. Unrecognised severity raises ``ValueError`` before any work. The
  record is never mutated. No active ``rules.collapsed_labels`` section in
  ``default_config.yaml`` (it would move ``config_hash``).

Scope fence: no new feature, no corpus case, no other rule changes. A detector
on a fraction of the expected spacing is left open.
"""

from __future__ import annotations

import math
from typing import Dict, List

from segfacet.heuristics.finding import Finding
from segfacet.heuristics.rule import (
    ConditionOptIn,
    ConsumedPath,
    Rule,
    RuleDetector,
    RuleModeDeclaration,
    register_rule,
)
from segfacet.verdict import Severity

__all__ = ["CollapsedLabelsRule", "DEFAULT_MAX_CENTROID_DISTANCE_MM"]


DEFAULT_MAX_CENTROID_DISTANCE_MM: float = 2.0
"""Two labels whose centroids lie within this distance are collapsed (item
220). Measured 2026-10-12 at 2a1491d: closest legitimate pair 12.542 mm
(geometric corpus), 32.695 mm (intensity corpus), 11.082 mm (VerSe19 GT, 159
masks)."""

_TAG = "Collapsed labels:"

_LABEL_TO_SEVERITY: Dict[str, Severity] = {sev.label: sev for sev in Severity}


def _severity_from_param(label: str) -> Severity:
    """Map a severity label string to its Severity member (ValueError if unknown)."""
    sev = _LABEL_TO_SEVERITY.get(label)
    if sev is None:
        known = list(_LABEL_TO_SEVERITY.keys())
        raise ValueError(
            f"Unknown severity label {label!r} in collapsed_labels rule "
            f"config. Known labels: {known}."
        )
    return sev


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


@register_rule
class CollapsedLabelsRule(Rule):
    """Collapsed-labels rule (item 220), serving mode 13."""

    rule_id = "collapsed_labels"

    condition_opt_ins = (
        ConditionOptIn(
            condition="fov_truncation",
            paths=(
                "per_label.{label}.centroid.centroid_mm[]",
                "stage3_unavailable.labels[]",
                "stage3_unavailable.reason",
            ),
            reason=(
                "a crop shifts a label's centroid within its own vertebra "
                "and cannot bring two labels on different vertebrae within "
                "the tolerance, so a collapsed pair stays valid evidence on "
                "a border-touching label"
            ),
        ),
    )

    mode_declaration = RuleModeDeclaration(
        modes=(13,),
        evidence=(
            "analytic",
            "item 220 (2026-10-12). The coincident map of item 129 "
            "(labels 21 and 22 as concentric boxes, both centroids at "
            "(9.5, 9.5, 19.5) mm) makes Stage 3 absent. Closest legitimate "
            "centroid pairs: 12.542 mm (geometric corpus), 32.695 mm "
            "(intensity corpus), 11.082 mm (VerSe19 GT), against the 2.0 mm "
            "default tolerance. No committed corpus case expresses the mode.",
        ),
        consumed_paths=(
            ConsumedPath(
                path="per_label",
                role="bookkeeping",
                reason="container: iterated to reach each label's centroid",
            ),
            ConsumedPath(
                path="per_label.{label}.centroid.centroid_mm[]",
                role="signal",
            ),
            ConsumedPath(
                path="per_label.{label}.level_name",
                role="bookkeeping",
                reason="identity: names the levels in the near finding",
            ),
            ConsumedPath(
                path="stage3_unavailable.detail",
                role="bookkeeping",
                reason="message interpolation: quoted in the finding's reason",
            ),
            ConsumedPath(
                path="stage3_unavailable.labels[]",
                role="bookkeeping",
                reason="identity: the pair the finding is attributed to",
            ),
            ConsumedPath(
                path="stage3_unavailable.reason",
                role="signal",
            ),
        ),
        detectors=(
            RuleDetector(
                detector_id="coincident_centroids",
                description=_TAG,
                question=(
                    "Is Stage 3 unavailable because two labels' centroids "
                    "coincide exactly?"
                ),
                fires_when="the record carries a `stage3_unavailable` block",
                signal_paths=("stage3_unavailable.reason",),
            ),
            RuleDetector(
                detector_id="near_coincident_centroids",
                description=_TAG,
                question=(
                    "Do two labels' centroids lie on essentially one point, "
                    "although Stage 3 was computed?"
                ),
                fires_when=(
                    "the distance between two labels' centroids is at most "
                    "`max_centroid_distance_mm`"
                ),
                params=(
                    ("max_centroid_distance_mm", DEFAULT_MAX_CENTROID_DISTANCE_MM),
                ),
                signal_paths=("per_label.{label}.centroid.centroid_mm[]",),
            ),
        ),
    )

    def evaluate(self, record, config) -> List[Finding]:  # type: ignore[override]
        """Judge the coincident block, then every pair of centroids.

        Raises ValueError on an unrecognised severity, before any work.
        """
        severity = _severity_from_param(
            config.rule_param(self.rule_id, "severity", default="flagged-for-review")
        )
        tol: float = config.rule_param(
            self.rule_id,
            "max_centroid_distance_mm",
            default=DEFAULT_MAX_CENTROID_DISTANCE_MM,
        )

        findings: List[Finding] = []
        reported = None

        unavailable = record.get("stage3_unavailable")
        if isinstance(unavailable, dict):
            try:
                reported = frozenset(int(x) for x in unavailable.get("labels", ()))
            except (TypeError, ValueError):
                reported = frozenset()
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=severity,
                    reason=(
                        f"{_TAG} {unavailable.get('detail', '')} "
                        f"Reason: {unavailable.get('reason', '')!r}."
                    ),
                    labels=reported,
                    detector_id="coincident_centroids",
                )
            )

        per_label = record.get("per_label")
        if not isinstance(per_label, dict):
            return findings
        try:
            keys = sorted(per_label.keys(), key=int)
        except (TypeError, ValueError):
            return findings

        cents = {}  # int label -> (level_name, centroid)
        for k in keys:
            entry = per_label[k]
            c = entry.get("centroid") if isinstance(entry, dict) else None
            mm = c.get("centroid_mm") if isinstance(c, dict) else None
            if isinstance(mm, (list, tuple)) and len(mm) == 3 and all(map(_is_num, mm)):
                cents[int(k)] = (entry.get("level_name", "unknown"), mm)

        labels = sorted(cents)
        for i, a in enumerate(labels):
            for b in labels[i + 1:]:
                pair = frozenset((a, b))
                if pair == reported:
                    continue
                dist = math.dist(cents[a][1], cents[b][1])
                if dist <= tol:
                    findings.append(
                        Finding(
                            rule_id=self.rule_id,
                            severity=severity,
                            reason=(
                                f"{_TAG} Labels {a} ({cents[a][0]}) and {b} "
                                f"({cents[b][0]}) have centroids {dist:.4g} mm "
                                f"apart, within {tol:.6g} mm: the levels "
                                f"are placed on (nearly) one point."
                            ),
                            labels=pair,
                            detector_id="near_coincident_centroids",
                        )
                    )
        return findings
