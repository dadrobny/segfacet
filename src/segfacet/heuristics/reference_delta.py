"""Delta-to-reference rule family (item 047).

A Stage 4 rule that thresholds item 046's per-vertebra **delta-to-reference**
metrics, read from ``record["reference_delta"]`` (the
``segfacet.reference.reference_delta_to_dict`` shape). It fires a ``Finding``
when a vertebra is out-of-distribution vs the bundled VerSe reference,
realising the vision's §5.4 "delta to reference" rule input.

Scope
-----
This module computes **no** statistic itself — z-score, robust-z,
percentile-rank, out-of-range, and distribution-distance are all already
computed and serialised by item 046. This rule only *thresholds* those
already-computed numbers. It imports nothing from ``segfacet.reference``, loads
no reference artifact, and is stateless / I/O-free, exactly like its Stage 4
siblings (``bounds``, ``fragmentation``, ``coverage``, ``sequence``,
``border``, ``overlap``, ``mislabel``).

It does **not** touch ``segfacet.pipeline``, ``segfacet.cli``, ``segfacet.config``,
``default_config.yaml``, ``segfacet.report``, or ``segfacet.aggregate`` — wiring
the ``reference_delta`` block into the record fed to ``run_rules`` is item
049's remit. Until that wiring lands, ``record.get("reference_delta")`` is
absent by default, so this rule is silently a no-op and existing pipeline
output is unaffected by its addition.

Three independent, config-toggleable firing conditions per available label:

1. **Distribution-distance outlier** (label-level) — fires when
   ``distribution_distance >= max_distribution_distance`` (default ``3.0``).
2. **Out-of-range feature** (per feature) — fires for each feature name in
   the block's ``out_of_range_features`` list.
3. **Robust-z outlier** (per feature) — fires for each feature whose
   ``abs(robust_z) >= max_robust_z`` (default ``3.5``).

A label whose entry is ``available: false`` (or an absent/non-mapping
``reference_delta`` block) contributes no findings — reference-grounded
judgement is silent where there is no reference.

Determinism / non-mutation contract: ``evaluate`` never mutates ``record``,
and two calls with the same ``(record, config)`` return equal finding lists
in the same order. Findings are emitted ascending by integer label; within a
label, in fixed condition order (distribution-distance -> out-of-range ->
robust-z), with per-feature findings in ascending feature-name order.

Mode-less (item 193, 2026-09-28): this rule declared modes 1 (segmentation
accuracy), 2 (fused), 3 (split), 4 (islands) and 8 (semantic mislabelling) in
``failure_modes.SPECIFICATION`` as a cohort proxy from item 137 (corrected
2026-09-02, re-keyed at the item-150 sign-off) until item 193. It is a
general outlier detector -- it thresholds a label's deviation from its
level's cohort reference distribution, which is no failure mode's own
signal -- so it now declares no mode (roadmap Stage 33 D3). It still runs
and fires exactly as before: no threshold, condition, severity or
``evaluate`` line changed. See ``ReferenceDeltaRule.mode_declaration``.
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

__all__ = ["ReferenceDeltaRule"]


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

DEFAULT_MAX_ROBUST_Z = 3.5
DEFAULT_MAX_DISTRIBUTION_DISTANCE = 3.0

_OUT_OF_RANGE_TAG = "Reference out-of-range:"
_ROBUST_Z_TAG = "Reference robust-z outlier:"
_DISTANCE_TAG = "Reference distribution-distance outlier:"


# --------------------------------------------------------------------------- #
# Severity helper (mirrors bounds.py / mislabel.py)
# --------------------------------------------------------------------------- #

_LABEL_TO_SEVERITY: Dict[str, Severity] = {sev.label: sev for sev in Severity}


def _severity_from_param(label: str) -> Severity:
    """Map a severity label string to its ``Severity`` member.

    Raises
    ------
    ValueError
        If *label* is not a recognised ``Severity`` label string.
    """
    sev = _LABEL_TO_SEVERITY.get(label)
    if sev is None:
        known = list(_LABEL_TO_SEVERITY.keys())
        raise ValueError(
            f"Unknown severity label {label!r} in reference_delta rule config. "
            f"Known labels: {known}."
        )
    return sev


# --------------------------------------------------------------------------- #
# ReferenceDeltaRule
# --------------------------------------------------------------------------- #


@register_rule
class ReferenceDeltaRule(Rule):
    """Delta-to-reference rule (item 047).

    Reads ``record["reference_delta"]`` (item 046's
    ``reference_delta_to_dict`` shape) and emits a ``Finding`` per fired
    condition. Returns ``[]`` when the block is absent/non-mapping or every
    available label is in-distribution.
    """

    rule_id = "reference_delta"

    # Disposition (item 193, 2026-09-28, superseding item 137's
    # modes-1/2/3/4/8 declaration corrected 2026-09-02 and re-keyed at the
    # item-150 sign-off): mode-less. This rule is a general outlier
    # detector -- it thresholds a label's deviation from its level's cohort
    # reference distribution, which is no failure mode's own signal
    # (roadmap Stage 33 D3). failure_modes.SPECIFICATION no longer carries an
    # IntendedRule edge naming this rule for any mode.
    mode_declaration = RuleModeDeclaration(
        mode_less_reason=(
            "general outlier detector, not a failure mode's own signal: "
            "this rule thresholds a label's deviation from its level's "
            "cohort reference distribution (item 193, 2026-09-28,"
            " superseding item 137's modes-1/2/3/4/8 declaration). The "
            "rule still runs and fires exactly as before -- no threshold, "
            "condition, severity or evaluate line changed. "
            "failure_modes.SPECIFICATION carries no IntendedRule edge "
            "naming this rule for any mode."
        ),
        consumed_paths=(
            ConsumedPath(
                path="per_label",
                role="not-read",
                reason=(
                    "mechanism B last-path-segment match only: the container "
                    "is not itself a feature -- this rule reads the "
                    "identity of record['per_label'][key] and the "
                    "per-label entries of record['reference_delta']"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.level_name",
                role="bookkeeping",
                reason=(
                    "identity and message interpolation: names the level "
                    "in the finding"
                ),
            ),
            ConsumedPath(
                path="reference_delta.lower_pct",
                role="bookkeeping",
                reason=(
                    "message interpolation: the band's lower percentile, "
                    "printed in the finding; the firing decision is "
                    "out_of_range_features[]'s membership"
                ),
            ),
            ConsumedPath(
                path="reference_delta.upper_pct",
                role="bookkeeping",
                reason=(
                    "message interpolation: the band's upper percentile, "
                    "printed in the finding"
                ),
            ),
            ConsumedPath(
                path="reference_delta.{label}.available",
                role="bookkeeping",
                reason=(
                    "gate: skips a label the reference distribution does "
                    "not cover; availability is not a deviation"
                ),
            ),
            ConsumedPath(
                path="reference_delta.{label}.distribution_distance",
                role="bookkeeping",
                reason=(
                    "this mode-less rule's own firing value (item 193, "
                    "2026-09-28): a signal path needs a mode, and this "
                    "rule declares none"
                ),
            ),
            ConsumedPath(
                path="reference_delta.{label}.features.extent_x_mm.robust_z",
                role="bookkeeping",
                reason=(
                    "this mode-less rule's own firing value (item 193, "
                    "2026-09-28): a signal path needs a mode, and this "
                    "rule declares none"
                ),
            ),
            ConsumedPath(
                path="reference_delta.{label}.features.extent_y_mm.robust_z",
                role="bookkeeping",
                reason=(
                    "this mode-less rule's own firing value (item 193, "
                    "2026-09-28): a signal path needs a mode, and this "
                    "rule declares none"
                ),
            ),
            ConsumedPath(
                path="reference_delta.{label}.features.extent_z_mm.robust_z",
                role="bookkeeping",
                reason=(
                    "this mode-less rule's own firing value (item 193, "
                    "2026-09-28): a signal path needs a mode, and this "
                    "rule declares none"
                ),
            ),
            ConsumedPath(
                path="reference_delta.{label}.features.physical_volume_mm3.robust_z",
                role="bookkeeping",
                reason=(
                    "this mode-less rule's own firing value (item 193, "
                    "2026-09-28): a signal path needs a mode, and this "
                    "rule declares none"
                ),
            ),
            ConsumedPath(
                path="reference_delta.{label}.features.spline_offset_mm.robust_z",
                role="bookkeeping",
                reason=(
                    "this mode-less rule's own firing value (item 193, "
                    "2026-09-28): a signal path needs a mode, and this "
                    "rule declares none"
                ),
            ),
            ConsumedPath(
                path="reference_delta.{label}.out_of_range_features[]",
                role="bookkeeping",
                reason=(
                    "this mode-less rule's own firing value (item 193, "
                    "2026-09-28): a signal path needs a mode, and this "
                    "rule declares none"
                ),
            ),
        ),
        detectors=(
            RuleDetector(
                detector_id="distance",
                description=_DISTANCE_TAG,
                question=(
                    "Is the label's overall geometry far from its level's "
                    "cohort reference distribution?"
                ),
                fires_when=(
                    "`flag_distribution_distance` and the label's "
                    "`distribution_distance` >= `max_distribution_distance` "
                    "(inclusive), on a label the reference covers"
                ),
                params=(
                    ("flag_distribution_distance", True),
                    ("max_distribution_distance", DEFAULT_MAX_DISTRIBUTION_DISTANCE),
                ),
                mode_less_reason=(
                    "records this mode-less rule's own firing value (item "
                    "193, 2026-09-28) -- same disposition as the rule "
                    "overall"
                ),
            ),
            RuleDetector(
                detector_id="out_of_range",
                description=_OUT_OF_RANGE_TAG,
                question=(
                    "Does a geometric feature of the label fall outside its "
                    "level's reference percentile band?"
                ),
                fires_when=(
                    "`flag_out_of_range` and the feature is listed in the "
                    "label's `out_of_range_features`, on a label the "
                    "reference covers; one finding per listed feature"
                ),
                params=(("flag_out_of_range", True),),
                mode_less_reason=(
                    "records this mode-less rule's own firing value (item "
                    "193, 2026-09-28) -- same disposition as the rule "
                    "overall"
                ),
            ),
            RuleDetector(
                detector_id="robust_z",
                description=_ROBUST_Z_TAG,
                question=(
                    "Is a geometric feature of the label many robust "
                    "standard deviations from its level's reference median?"
                ),
                fires_when=(
                    "`flag_robust_z` and |`robust_z`| >= `max_robust_z` "
                    "(inclusive) for a feature, on a label the reference "
                    "covers; one finding per feature"
                ),
                params=(
                    ("flag_robust_z", True),
                    ("max_robust_z", DEFAULT_MAX_ROBUST_Z),
                ),
                mode_less_reason=(
                    "records this mode-less rule's own firing value (item "
                    "193, 2026-09-28) -- same disposition as the rule "
                    "overall"
                ),
            ),
        ),
    )

    def evaluate(self, record, config) -> List[Finding]:  # type: ignore[override]
        """Evaluate delta-to-reference signals for *record*.

        Parameters
        ----------
        record:
            Per-case feature dict (read-only). Reads
            ``record["reference_delta"]`` and each label's ``level_name``
            from ``record["per_label"]``.
        config:
            HeuristicConfig instance. Reads ``rules.reference_delta.params``.

        Returns
        -------
        list[Finding]
            Zero or more findings, ascending by integer label; within a
            label, in fixed condition order (distribution-distance ->
            out-of-range -> robust-z), with per-feature findings ascending
            by feature name.

        Raises
        ------
        ValueError
            If ``rules.reference_delta.params.severity`` is an unrecognised
            string (raised before any per-record processing, AC12).
        """
        # Read severity once up-front; raises immediately on a bad string,
        # independently of whether the block is even present (AC12).
        sev_label: str = config.rule_param(
            self.rule_id, "severity", default="flagged-for-review"
        )
        severity = _severity_from_param(sev_label)

        flag_out_of_range = bool(
            config.rule_param(self.rule_id, "flag_out_of_range", default=True)
        )
        flag_robust_z = bool(
            config.rule_param(self.rule_id, "flag_robust_z", default=True)
        )
        flag_distribution_distance = bool(
            config.rule_param(
                self.rule_id, "flag_distribution_distance", default=True
            )
        )
        max_robust_z = float(
            config.rule_param(
                self.rule_id, "max_robust_z", default=DEFAULT_MAX_ROBUST_Z
            )
        )
        max_distribution_distance = float(
            config.rule_param(
                self.rule_id,
                "max_distribution_distance",
                default=DEFAULT_MAX_DISTRIBUTION_DISTANCE,
            )
        )

        block = record.get("reference_delta")
        if not isinstance(block, dict):
            return []

        lower_pct = block.get("lower_pct")
        upper_pct = block.get("upper_pct")

        per_label = block.get("per_label")
        if not isinstance(per_label, dict):
            return []

        # Identity is stored once, on the record's own per-label entry
        # (item 215): the delta entry is keyed by the label and carries no
        # copy of the label or its level name.
        identity = record.get("per_label")
        if not isinstance(identity, dict):
            identity = {}

        normalised = []
        for key, entry in per_label.items():
            if not isinstance(entry, dict):
                continue
            if not entry.get("available"):
                continue
            try:
                label = int(key)
            except (TypeError, ValueError):
                continue
            normalised.append((label, key, entry))
        normalised.sort(key=lambda t: t[0])

        findings: List[Finding] = []
        for label, key, entry in normalised:
            label_entry = identity.get(key)
            level_name = (
                label_entry.get("level_name")
                if isinstance(label_entry, dict)
                else None
            )
            features = entry.get("features")
            if not isinstance(features, dict):
                features = {}

            if flag_distribution_distance:
                distance = entry.get("distribution_distance")
                if distance is not None and distance >= max_distribution_distance:
                    findings.append(
                        Finding(
                            rule_id=self.rule_id,
                            severity=severity,
                            reason=(
                                f"{_DISTANCE_TAG} label {label} ({level_name}) "
                                f"distribution distance {distance:.2f} exceeds "
                                f"threshold {max_distribution_distance:.2f}."
                            ),
                            labels=frozenset({label}),
                            detector_id="distance",
                        )
                    )

            if flag_out_of_range:
                out_of_range_features = entry.get("out_of_range_features")
                if isinstance(out_of_range_features, list):
                    for name in sorted(out_of_range_features):
                        feat = features.get(name)
                        if not isinstance(feat, dict):
                            feat = {}
                        value = feat.get("value")
                        percentile_rank = feat.get("percentile_rank")
                        findings.append(
                            Finding(
                                rule_id=self.rule_id,
                                severity=severity,
                                reason=(
                                    f"{_OUT_OF_RANGE_TAG} label {label} "
                                    f"({level_name}) feature {name!r} value "
                                    f"{value} falls outside the reference "
                                    f"range (percentile_rank={percentile_rank}, "
                                    f"band=({lower_pct}, {upper_pct}))."
                                ),
                                labels=frozenset({label}),
                                detector_id="out_of_range",
                            )
                        )

            if flag_robust_z:
                for name in sorted(features):
                    feat = features.get(name)
                    if not isinstance(feat, dict):
                        continue
                    robust_z = feat.get("robust_z")
                    if robust_z is None:
                        continue
                    if abs(robust_z) >= max_robust_z:
                        findings.append(
                            Finding(
                                rule_id=self.rule_id,
                                severity=severity,
                                reason=(
                                    f"{_ROBUST_Z_TAG} label {label} "
                                    f"({level_name}) feature {name!r} "
                                    f"robust_z={robust_z:.2f} exceeds "
                                    f"threshold {max_robust_z:.2f}."
                                ),
                                labels=frozenset({label}),
                                detector_id="robust_z",
                            )
                        )

        return findings
