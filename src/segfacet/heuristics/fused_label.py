"""Fused-label rule (item 207), serving mode 2 (fused vertebra segments).

Mode 2's two unpaired corpus cases -- ``fuse_adjacent`` (item 176, bridged)
and ``fuse_separate`` (item 206, disc gap unlabelled) -- put one label over
two whole vertebrae. Neither ``neighbour_contact`` nor any other rule reads
that. This rule fires on a label that is **both** large relative to its
adjacent labels **and** flanked by wide centroid spacing. Neither signal
decides alone: ``split``'s label 24 is large (1.53x its larger neighbour)
at normal spacing (1.05), and ``relabel_swap``'s label 20 is widely spaced
(1.79) at normal size (1.00).

Design decisions (item 207 spec, A1-A6):
- **size_ratio (A1)**: the label's ``physical_volume_mm3`` divided by the
  *larger* ``physical_volume_mm3`` of its adjacent labels. Adjacency is the
  ascending-integer label order ``stage3.spacing_consistency.spacings_mm[]``
  is computed in (``spacings_mm[i]`` lies between the i-th and (i+1)-th
  label). The larger neighbour, not the mean, so a label beside an
  undersized cap does not read large.
- **spacing_ratio (A2, item 211)**: the *mean* of the spacings adjacent to
  the label, divided by the median of the case's spacings not adjacent to
  it. The pair is judged together because a fused label adds about one
  pitch to the pair's sum however its centroid splits it between the two
  sides (``min`` missed a centroid on one body). An end label has one
  spacing, so its reading is unchanged.
- **End labels (A3)** are judged on their one neighbour and one spacing. A
  label with no non-adjacent spacing to form a baseline is not judged.
- **Sacral and coccygeal labels (A4)** are never candidates (they still
  count as neighbours and their spacings still count).
- **Fired strictly above both thresholds (A5)**, calibrated on the synthetic
  corpora only (Stage 21 re-calibrates on real data). No active
  ``rules.fused_label`` section in ``default_config.yaml``: it would move
  ``config_hash`` in every report.
- **Measured (A7, 2026-09-30; spacing re-measured as the mean, item 211,
  2026-10-05)**: fires on ``fuse_adjacent`` label 22 (size 2.3248, spacing
  1.5380) and ``fuse_separate`` label 22 (2.0016, 1.5371) only. Highest
  silent readings: size 4.8000 (``split_own_label`` label 24, spacing
  0.8885), 1.5263 (``split``, spacing 1.0512); spacing 1.7915
  (``relabel_swap`` label 20, size 1.0). Interior labels beside a missed
  level now pass the spacing gate (``remove_level_relabel`` label 22, mean
  1.5408) and only the size gate (0.9984) keeps them silent.
- Absence-tolerant: a record without ``stage3.spacing_consistency.
  spacings_mm``, with a spacing count other than ``len(per_label) - 1``, or
  with a label lacking a numeric volume, or with a non-integer ``per_label``
  key (item 211) is not judged (returns ``[]``).
- Unrecognised severity raises ``ValueError`` before any work. The record is
  never mutated.

Scope fence: no feature, no other rule's threshold; a spacing rule for modes
6 and 10 (a missed or skipped level widens one spacing at normal size) is
not this rule.
"""

from __future__ import annotations

import statistics
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

__all__ = ["FusedLabelRule", "DEFAULT_SIZE_RATIO", "DEFAULT_SPACING_RATIO"]


DEFAULT_SIZE_RATIO: float = 1.5
"""Fire when size_ratio strictly exceeds this value (item 207). The midpoint
between a single level (1.0) and a fused label's reading (2.0). Measured
2026-09-30: fires at 2.3248 (fuse_adjacent) and 2.0016 (fuse_separate); the
highest silent reading beside a size-only label is 1.5263 (split label 24),
which is why the spacing gate is also needed. Synthetic corpora only."""

DEFAULT_SPACING_RATIO: float = 1.25
"""Fire when spacing_ratio strictly exceeds this value (item 207). The
midpoint between normal spacing (1.0) and a fused label's reading (1.5).
Measured 2026-10-05 (mean of the adjacent spacings, item 211): fires at
1.5380 and 1.5371; the highest silent reading
beside a spacing-only label is 1.7915 (relabel_swap label 20, size 1.0).
Synthetic corpora only."""

_FUSED_TAG = "Fused label:"

_LABEL_TO_SEVERITY: Dict[str, Severity] = {sev.label: sev for sev in Severity}


def _severity_from_param(label: str) -> Severity:
    """Map a severity label string to its Severity member.

    Raises ValueError if *label* is not a recognised Severity label string.
    """
    sev = _LABEL_TO_SEVERITY.get(label)
    if sev is None:
        known = list(_LABEL_TO_SEVERITY.keys())
        raise ValueError(
            f"Unknown severity label {label!r} in fused_label rule "
            f"config. Known labels: {known}."
        )
    return sev


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


@register_rule
class FusedLabelRule(Rule):
    """Fused-label rule (item 207), serving mode 2 (fused vertebra segments).

    Emits one ``Finding`` per label whose volume exceeds its larger adjacent
    label's by more than ``size_ratio_threshold`` and whose mean adjacent
    spacing exceeds the median non-adjacent spacing by more than
    ``spacing_ratio_threshold``.
    """

    rule_id = "fused_label"

    mode_declaration = RuleModeDeclaration(
        modes=(2,),
        evidence=(
            "corpus-manifest",
            "tests/corpus/manifest.json's fuse_adjacent and fuse_separate "
            "designate this rule for mode 2 (fused vertebra segments); item "
            "207 (2026-09-30). Measured: label 22 reads size 2.3248 / "
            "spacing 1.5380 on fuse_adjacent and 2.0016 / 1.5371 on "
            "fuse_separate, against thresholds 1.5 / 1.25; every other "
            "case in both corpora is silent.",
        ),
        consumed_paths=(
            ConsumedPath(
                path="per_label",
                role="bookkeeping",
                reason="container: iterated to reach each label's volume",
            ),
            ConsumedPath(
                path="per_label.{label}.geometry.physical_volume_mm3",
                role="signal",
            ),
            ConsumedPath(
                path="per_label.{label}.level_name",
                role="bookkeeping",
                reason=(
                    "identity: names the level in the finding and excludes "
                    "sacral and coccygeal labels from judgement"
                ),
            ),
            ConsumedPath(
                path="stage3.spacing_consistency.spacings_mm[]",
                role="signal",
            ),
        ),
        detectors=(
            RuleDetector(
                detector_id="fused_label",
                description=_FUSED_TAG,
                question=(
                    "Is this label about twice the size of its neighbours "
                    "and flanked by wide centroid spacing, as one label "
                    "over two vertebrae would be?"
                ),
                fires_when=(
                    "`size_ratio` > `size_ratio_threshold` and "
                    "`spacing_ratio` > `spacing_ratio_threshold`, both "
                    "strictly"
                ),
                params=(
                    ("size_ratio_threshold", DEFAULT_SIZE_RATIO),
                    ("spacing_ratio_threshold", DEFAULT_SPACING_RATIO),
                ),
                signal_paths=(
                    "per_label.{label}.geometry.physical_volume_mm3",
                    "stage3.spacing_consistency.spacings_mm[]",
                ),
            ),
        ),
    )

    def evaluate(self, record, config) -> List[Finding]:  # type: ignore[override]
        """Evaluate the fused-label test for every label in *record*.

        Raises ValueError on an unrecognised severity, before any work.
        """
        severity = _severity_from_param(
            config.rule_param(self.rule_id, "severity", default="flagged-for-review")
        )
        size_thr: float = config.rule_param(
            self.rule_id, "size_ratio_threshold", default=DEFAULT_SIZE_RATIO
        )
        spacing_thr: float = config.rule_param(
            self.rule_id, "spacing_ratio_threshold", default=DEFAULT_SPACING_RATIO
        )

        stage3 = record.get("stage3")
        if not isinstance(stage3, dict):
            return []
        sc = stage3.get("spacing_consistency")
        if not isinstance(sc, dict):
            return []
        spacings = sc.get("spacings_mm")
        if not isinstance(spacings, (list, tuple)) or not all(
            _is_num(s) for s in spacings
        ):
            return []

        per_label = record.get("per_label", {})
        if not isinstance(per_label, dict) or len(spacings) != len(per_label) - 1:
            return []
        try:
            keys = sorted(per_label.keys(), key=int)
        except (TypeError, ValueError):
            return []  # item 211 A3: a non-integer key is not judged
        volumes = []
        for k in keys:
            entry = per_label[k]
            geom = entry.get("geometry") if isinstance(entry, dict) else None
            vol = geom.get("physical_volume_mm3") if isinstance(geom, dict) else None
            if not _is_num(vol):
                return []
            volumes.append(vol)

        findings: List[Finding] = []
        for i, k in enumerate(keys):
            level_name = per_label[k].get("level_name", "unknown")
            if str(level_name).startswith("S") or level_name == "Cocc":
                continue  # A4
            adj_sp = [spacings[j] for j in (i - 1, i) if 0 <= j < len(spacings)]
            base = [s for j, s in enumerate(spacings) if j not in (i - 1, i)]
            if not base:
                continue  # A3: no baseline
            neighbours = [j for j in (i - 1, i + 1) if 0 <= j < len(keys)]
            big = max(neighbours, key=lambda j: volumes[j])
            if volumes[big] <= 0:
                continue
            base_med = statistics.median(base)
            if base_med <= 0:
                continue
            size_ratio = volumes[i] / volumes[big]
            spacing_ratio = statistics.mean(adj_sp) / base_med
            if size_ratio > size_thr and spacing_ratio > spacing_thr:
                label_int = int(k)
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=severity,
                        reason=(
                            f"{_FUSED_TAG} Label {label_int} ({level_name}) "
                            f"reads {size_ratio:.4g}x the volume of its "
                            f"larger neighbour (label {int(keys[big])}), "
                            f"strictly above {size_thr:.6g}, and its "
                            f"adjacent centroid spacings average "
                            f"{spacing_ratio:.4g}x the case's other "
                            f"spacings, strictly above {spacing_thr:.6g}: "
                            f"it may cover two vertebrae."
                        ),
                        labels=frozenset({label_int}),
                        detector_id="fused_label",
                    )
                )
        return findings
