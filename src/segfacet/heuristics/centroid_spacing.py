"""Centroid-spacing rule (items 207, 218), serving modes 2 and 6.

One rule over the inter-centroid spacings, with two detectors:

- ``fused_label`` (item 207, mode 2): a label **both** large relative to its
  neighbours **and** flanked by wide centroid spacing -- one label over two
  whole vertebrae (``fuse_adjacent``, ``fuse_separate``).
- ``missing_level`` (item 218, mode 6): one gap of about two pitches between
  two labels of normal size -- one vertebra not segmented, whether or not the
  labels were renumbered (``remove_level``, ``remove_level_relabel``).

Shared order (item 218, A1): both detectors order the labels by
``per_label.{label}.curve.path_u`` (item 210's label-free path position, ties
broken by the integer label) and take each spacing as ``math.dist`` of the
first three components of consecutive labels'
``per_label.{label}.centroid.centroid_mm[]``. A swapped or relabelled
vertebra still sits at a regular pitch along the curve, so an order break
reads no gap and ``relabel_swap`` / ``sequence_break`` stay silent with no
ordering gate (A2). The rule no longer reads ``pairs.adjacent.spacings_mm[]``
(still in the record, in anatomical order). A record is not judged (``[]``)
when ``pairs.adjacent.mean_spacing_mm`` is not numeric (the Stage-3 gate), a
``per_label`` key is not an integer, or any label lacks a numeric ``path_u``,
a three-component ``centroid_mm`` or a numeric ``physical_volume_mm3``
(``path_u`` is absent whenever Stage 3 is).

``fused_label`` (A3, unchanged statistic): ``size_ratio`` is the label's
volume over its *larger* path neighbour's; ``spacing_ratio`` is the *mean* of
the spacings adjacent to the label over the *median* of the case's other
spacings. End labels use their one neighbour; a label with no baseline is not
judged; sacral and coccygeal labels are never candidates. Fired strictly
above both thresholds. Measured 2026-10-12: fires on ``fuse_adjacent`` label
22 (size 2.3248, spacing 1.5380) and ``fuse_separate`` label 22 (2.0016,
1.5371) only; highest silent size 4.8000 (``split_own_label`` label 24,
spacing 1.1631) and 1.5263 (``split``); highest silent spacing 1.5408
(``remove_level``, size 0.9984).

``missing_level`` (A6): for each gap ``i`` between path-consecutive labels,
``gap_ratio = sp[i] / mean(sp[i-1], sp[i+1])`` (the one or two spacings
beside it). Fires when ``gap_ratio > gap_ratio_threshold`` (default 1.5) and
**both** flanking labels' size ratios are at most ``size_ratio_threshold``
(default 1.5): that keeps a fused label whose centroid sits on one body from
also reading as a missed level. A gap with no neighbouring spacing, or a
non-positive baseline or neighbour volume, is not judged. No upper band, so a
two-level miss fires. Measured: 1.887 on both remove-level cases (flanking
sizes 0.997 / 0.998); highest silent 2.269 (``split_own_label`` L4-L5, gated
off by size 4.800); highest silent past the size gate 1.386; VerSe19 ground
truth reads at most 1.378 on 157 masks (A7).

Known blind spot: two misses with exactly one vertebra between them read about
1.33 (each gap is the other's baseline: 2p / 1.5p), below the default 1.5, so
neither fires.

Absence-tolerant; an unrecognised severity raises ``ValueError`` before any
work; the record is never mutated. No active ``rules.centroid_spacing``
section in ``default_config.yaml`` (it would move ``config_hash``).

Scope fence: no feature change; modes 9 and 10 are not this rule's.
"""

from __future__ import annotations

import math
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

__all__ = [
    "CentroidSpacingRule",
    "DEFAULT_SIZE_RATIO",
    "DEFAULT_SPACING_RATIO",
    "DEFAULT_GAP_RATIO",
]


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

DEFAULT_GAP_RATIO: float = 1.5
"""Fire ``missing_level`` when gap_ratio strictly exceeds this value (item
218, A6). Synthetic misses read 1.887; the highest clean VerSe19 reading is
1.378 (157 masks). Synthetic corpora plus that one cohort; Stage 21
re-calibrates."""

_FUSED_TAG = "Fused label:"
_MISSING_TAG = "Missing level:"

_LABEL_TO_SEVERITY: Dict[str, Severity] = {sev.label: sev for sev in Severity}


def _severity_from_param(label: str) -> Severity:
    """Map a severity label string to its Severity member.

    Raises ValueError if *label* is not a recognised Severity label string.
    """
    sev = _LABEL_TO_SEVERITY.get(label)
    if sev is None:
        known = list(_LABEL_TO_SEVERITY.keys())
        raise ValueError(
            f"Unknown severity label {label!r} in centroid_spacing rule "
            f"config. Known labels: {known}."
        )
    return sev


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


_SIGNAL_PATHS = (
    "per_label.{label}.centroid.centroid_mm[]",
    "per_label.{label}.curve.path_u",
    "per_label.{label}.geometry.physical_volume_mm3",
)


@register_rule
class CentroidSpacingRule(Rule):
    """Centroid-spacing rule (items 207, 218), serving modes 2 and 6.

    Emits ``fused_label`` findings (mode 2) and ``missing_level`` findings
    (mode 6) over the path-ordered inter-centroid spacings; see the module
    docstring.
    """

    rule_id = "centroid_spacing"

    mode_declaration = RuleModeDeclaration(
        modes=(2, 6),
        evidence=(
            "corpus-manifest",
            "tests/corpus/manifest.json's fuse_adjacent and fuse_separate "
            "designate this rule for mode 2 (detector fused_label; item 207, "
            "2026-09-30): label 22 reads size 2.3248 / spacing 1.5380 and "
            "2.0016 / 1.5371 against thresholds 1.5 / 1.25. Its "
            "remove_level and remove_level_relabel designate it for mode 6 "
            "(detector missing_level; item 218, 2026-10-12): the gap reads "
            "1.887x its local baseline with flanking sizes 0.997 / 0.998, "
            "against 1.5. Every other case in both corpora is silent.",
        ),
        consumed_paths=(
            ConsumedPath(
                path="pairs.adjacent.mean_spacing_mm",
                role="bookkeeping",
                reason=(
                    "gate: the survivor spacing array exists on records "
                    "without Stage 3 too (item 216, D10), but only a record "
                    "carrying the Stage-3-only statistics is judged (A12)"
                ),
            ),
            ConsumedPath(
                path="per_label",
                role="bookkeeping",
                reason="container: iterated to reach each label's fields",
            ),
            ConsumedPath(
                path="per_label.{label}.centroid.centroid_mm[]",
                role="signal",
            ),
            ConsumedPath(
                path="per_label.{label}.curve.path_u",
                role="signal",
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
                    "strictly, over the path-ordered centroid spacings"
                ),
                params=(
                    ("size_ratio_threshold", DEFAULT_SIZE_RATIO),
                    ("spacing_ratio_threshold", DEFAULT_SPACING_RATIO),
                ),
                signal_paths=_SIGNAL_PATHS,
            ),
            RuleDetector(
                detector_id="missing_level",
                description=_MISSING_TAG,
                question=(
                    "Is there one gap between path-consecutive labels of "
                    "normal size, about twice the spacing beside it, as one "
                    "missed vertebra would leave?"
                ),
                fires_when=(
                    "`gap_ratio` > `gap_ratio_threshold` and both flanking "
                    "labels' `size_ratio` <= `size_ratio_threshold`"
                ),
                params=(
                    ("gap_ratio_threshold", DEFAULT_GAP_RATIO),
                    ("size_ratio_threshold", DEFAULT_SIZE_RATIO),
                ),
                signal_paths=_SIGNAL_PATHS,
            ),
        ),
    )

    def evaluate(self, record, config) -> List[Finding]:  # type: ignore[override]
        """Evaluate both detectors over the path-ordered spacings of *record*.

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
        gap_thr: float = config.rule_param(
            self.rule_id, "gap_ratio_threshold", default=DEFAULT_GAP_RATIO
        )

        pairs = record.get("pairs")
        sc = pairs.get("adjacent") if isinstance(pairs, dict) else None
        if not isinstance(sc, dict) or not _is_num(sc.get("mean_spacing_mm")):
            return []  # A12: judged only with the Stage-3-only statistics

        per_label = record.get("per_label", {})
        if not isinstance(per_label, dict) or len(per_label) < 2:
            return []
        try:
            keys = sorted(per_label, key=int)  # tie-break order, then path_u
        except (TypeError, ValueError):
            return []  # item 211 A3: a non-integer key is not judged
        rows = []  # (path_u, int label, key, volume, centroid)
        for k in keys:
            entry = per_label[k]
            if not isinstance(entry, dict):
                return []
            geom, cen, curve = (
                entry.get(n) for n in ("geometry", "centroid", "curve")
            )
            vol = geom.get("physical_volume_mm3") if isinstance(geom, dict) else None
            c = cen.get("centroid_mm") if isinstance(cen, dict) else None
            u = curve.get("path_u") if isinstance(curve, dict) else None
            if not (
                _is_num(vol)
                and _is_num(u)
                and isinstance(c, (list, tuple))
                and len(c) >= 3
                and all(_is_num(x) for x in c[:3])
            ):
                return []
            rows.append((u, int(k), k, vol, c[:3]))
        rows.sort(key=lambda r: (r[0], r[1]))
        keys = [r[2] for r in rows]
        volumes = [r[3] for r in rows]
        spacings = [math.dist(a[4], b[4]) for a, b in zip(rows, rows[1:])]

        def size_ratio(i: int):
            """Volume over the larger path neighbour's, with that neighbour."""
            nb = [j for j in (i - 1, i + 1) if 0 <= j < len(keys)]
            big = max(nb, key=lambda j: volumes[j])
            if volumes[big] <= 0:
                return None, big
            return volumes[i] / volumes[big], big

        findings: List[Finding] = []
        for i, k in enumerate(keys):
            level_name = per_label[k].get("level_name", "unknown")
            if str(level_name).startswith("S") or level_name == "Cocc":
                continue  # A4
            adj_sp = [spacings[j] for j in (i - 1, i) if 0 <= j < len(spacings)]
            base = [s for j, s in enumerate(spacings) if j not in (i - 1, i)]
            if not base:
                continue  # A3: no baseline
            ratio, big = size_ratio(i)
            base_med = statistics.median(base)
            if ratio is None or base_med <= 0:
                continue
            spacing_ratio = statistics.mean(adj_sp) / base_med
            if ratio > size_thr and spacing_ratio > spacing_thr:
                label_int = int(k)
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=severity,
                        reason=(
                            f"{_FUSED_TAG} Label {label_int} ({level_name}) "
                            f"reads {ratio:.4g}x the volume of its "
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

        for i, sp in enumerate(spacings):
            beside = [spacings[j] for j in (i - 1, i + 1) if 0 <= j < len(spacings)]
            if not beside:
                continue  # a two-label record has no baseline
            baseline = statistics.mean(beside)
            if baseline <= 0:
                continue
            gap_ratio = sp / baseline
            if not gap_ratio > gap_thr:  # NaN-safe: NaN compares False, so skip
                continue
            ratios = [size_ratio(j)[0] for j in (i, i + 1)]
            if any(r is None or r > size_thr for r in ratios):
                continue
            a, b = int(keys[i]), int(keys[i + 1])
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=severity,
                    reason=(
                        f"{_MISSING_TAG} The gap between label {a} and label "
                        f"{b} reads {gap_ratio:.4g}x the spacing beside it, "
                        f"strictly above {gap_thr:.6g}, between labels of "
                        f"normal size (at most {size_thr:.6g}x their larger "
                        f"neighbour): a vertebra may be missing."
                    ),
                    labels=frozenset({a, b}),
                    detector_id="missing_level",
                )
            )
        return findings
