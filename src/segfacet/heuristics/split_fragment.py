"""Split-fragment rule (item 208), serving mode 3 (split vertebra segment).

Mode 3 is the fragment case: part of a vertebra carries a label of its own,
and that label covers no other vertebra. Its one committed case,
``split_own_label``, keeps the caudal 20 % cap of L4 as label 23. Only the
``bounds`` proxy sees it. This rule fires on a label that **both** touches a
neighbouring label over more than a tenth of its own surface **and** is less
than half the median volume of its neighbouring labels. Neither signal decides
alone: the remainder of an encroached vertebra touches its neighbour too
(``split`` label 23 reads contact 0.1859, ``split_own_label`` label 22 reads
0.1859), and a label cropped by the field of view is small and touches nothing
(``crop_fov_si`` label 24 reads 6758 mm^3, contact 0.0).

Design decisions (item 208 spec, A1-A6):
- **size_ratio (A1)**: the label's ``physical_volume_mm3`` over the
  ``statistics.median`` of the same field across its *window*: the judged
  labels within two places of it on either side, in ascending integer label
  order, excluding itself (up to four, fewer at the ends). A median, not the
  larger adjacent label, so that the remainder of an encroached vertebra
  beside its enlarged receiver does not read small (0.6619 at a 30 %
  donation, 0.5774 at 40 %, against 0.4982 / 0.4086 on the larger neighbour).
- **Contact gate (A2)**: the whole-label
  ``components.label_contact_fraction`` (item 187), not the per-component
  contacts.
- **End labels and small maps (A3)**: an end label is judged on the labels on
  its one side; a label with an empty window is not judged.
- **Sacral and coccygeal labels (A4)** are neither judged nor counted in any
  window.
- **Fired strictly (A5)**: contact above ``contact_fraction_threshold`` and
  size ratio below ``size_ratio_threshold``. Calibrated on the synthetic
  corpora only (Stage 21 re-calibrates on real data). No active
  ``rules.split_fragment`` section in ``default_config.yaml``: it would move
  ``config_hash`` in every report.
- **Measured (A7, 2026-09-30)**: fires once, on ``split_own_label`` label 23
  (contact 0.3317, volume 4030 mm^3 against a window median of 19344, size
  0.2083). Highest silent contact readings: 0.1859 (``split`` 23,
  ``split_own_label`` 22) and 0.1021 (``split`` 24); every other label reads 0.
- Absence-tolerant: a record whose ``per_label`` is not a dict, has a
  non-integer key, a non-dict entry, or a judged label without a numeric
  volume is not judged (returns ``[]``); a label without a numeric contact
  fraction is skipped. Unrecognised severity raises ``ValueError`` before any
  work. The record is never mutated.

Scope fence: no new feature and no other rule changes. The label left
covering only the remainder of an encroached vertebra is not a target: the
rule fires on that label from about a 50 % donation upward (0.4944; label 23
at f=0.5 and 0.6, silent at 0.3 and 0.4), which is deferred and left open
(gate-51da). The lumbarised-S1 sub-type of mode 3 is not this rule.
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

__all__ = ["SplitFragmentRule", "DEFAULT_CONTACT_FRACTION", "DEFAULT_SIZE_RATIO"]


DEFAULT_CONTACT_FRACTION: float = 0.1
"""Fire when label_contact_fraction strictly exceeds this value (item 208).
The value ``neighbour_contact`` applies to the same relative measure at
component scope; kept as this rule's own constant so re-tuning one never moves
the other. Measured 2026-09-30: the cap reads 0.3317; the donor labels read
up to 0.1859, which only the size gate separates. Synthetic corpora only."""

DEFAULT_SIZE_RATIO: float = 0.5
"""Fire when size_ratio is strictly below this value (item 208): less than
half a neighbouring level. Measured 2026-09-30: the cap reads 0.2083; the
lowest silent reading among labels with contact above 0.1 is 0.7879 (``split``
label 23). Synthetic corpora only."""

_SPLIT_TAG = "Split fragment:"

_LABEL_TO_SEVERITY: Dict[str, Severity] = {sev.label: sev for sev in Severity}


def _severity_from_param(label: str) -> Severity:
    """Map a severity label string to its Severity member.

    Raises ValueError if *label* is not a recognised Severity label string.
    """
    sev = _LABEL_TO_SEVERITY.get(label)
    if sev is None:
        known = list(_LABEL_TO_SEVERITY.keys())
        raise ValueError(
            f"Unknown severity label {label!r} in split_fragment rule "
            f"config. Known labels: {known}."
        )
    return sev


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


@register_rule
class SplitFragmentRule(Rule):
    """Split-fragment rule (item 208), serving mode 3.

    Emits one ``Finding`` per label whose whole-label contact fraction
    exceeds ``contact_fraction_threshold`` and whose volume is below
    ``size_ratio_threshold`` times the median volume of its window.
    """

    rule_id = "split_fragment"

    mode_declaration = RuleModeDeclaration(
        modes=(3,),
        evidence=(
            "corpus-manifest",
            "tests/corpus/manifest.json's split_own_label designates this "
            "rule for mode 3 (split vertebra segment); item 208 "
            "(2026-09-30). Measured: label 23 reads contact 0.3317 and size "
            "0.2083 on split_own_label, against thresholds 0.1 / 0.5; every "
            "other case in both corpora is silent.",
        ),
        consumed_paths=(
            ConsumedPath(
                path="per_label",
                role="bookkeeping",
                reason="container: iterated to reach each label's signals",
            ),
            ConsumedPath(
                path="per_label.{label}.components.label_contact_fraction",
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
                detector_id="split_fragment",
                description=_SPLIT_TAG,
                question=(
                    "Is this label small beside its neighbours and in "
                    "contact with one of them, as a fragment of a vertebra "
                    "given a label of its own would be?"
                ),
                fires_when=(
                    "`label_contact_fraction` > `contact_fraction_threshold` "
                    "and `size_ratio` < `size_ratio_threshold`, both "
                    "strictly"
                ),
                params=(
                    ("contact_fraction_threshold", DEFAULT_CONTACT_FRACTION),
                    ("size_ratio_threshold", DEFAULT_SIZE_RATIO),
                ),
                signal_paths=(
                    "per_label.{label}.components.label_contact_fraction",
                    "per_label.{label}.geometry.physical_volume_mm3",
                ),
            ),
        ),
    )

    def evaluate(self, record, config) -> List[Finding]:  # type: ignore[override]
        """Evaluate the split-fragment test for every label in *record*.

        Raises ValueError on an unrecognised severity, before any work.
        """
        severity = _severity_from_param(
            config.rule_param(self.rule_id, "severity", default="flagged-for-review")
        )
        contact_thr: float = config.rule_param(
            self.rule_id,
            "contact_fraction_threshold",
            default=DEFAULT_CONTACT_FRACTION,
        )
        size_thr: float = config.rule_param(
            self.rule_id, "size_ratio_threshold", default=DEFAULT_SIZE_RATIO
        )

        per_label = record.get("per_label", {})
        if not isinstance(per_label, dict):
            return []
        try:
            keys = sorted(per_label.keys(), key=int)
        except (TypeError, ValueError):
            return []  # non-integer key: not judged
        if not all(isinstance(per_label[k], dict) for k in keys):
            return []

        judged = []  # (key, level_name, volume)
        for k in keys:
            entry = per_label[k]
            level_name = entry.get("level_name", "unknown")
            if str(level_name).startswith("S") or level_name == "Cocc":
                continue  # A4
            geom = entry.get("geometry")
            vol = geom.get("physical_volume_mm3") if isinstance(geom, dict) else None
            if not _is_num(vol):
                return []
            judged.append((k, level_name, vol))

        findings: List[Finding] = []
        for i, (k, level_name, vol) in enumerate(judged):
            comps = per_label[k].get("components")
            contact = (
                comps.get("label_contact_fraction") if isinstance(comps, dict) else None
            )
            if not _is_num(contact):
                continue
            window = [
                judged[j][2]
                for j in range(max(0, i - 2), min(len(judged), i + 3))
                if j != i
            ]
            if not window:
                continue  # A3
            med = statistics.median(window)
            if med <= 0:
                continue
            size_ratio = vol / med
            if contact > contact_thr and size_ratio < size_thr:
                label_int = int(k)
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=severity,
                        reason=(
                            f"{_SPLIT_TAG} Label {label_int} ({level_name}) "
                            f"touches a neighbouring label over "
                            f"{contact:.4g} of its surface, strictly above "
                            f"{contact_thr:.6g}, and its volume is "
                            f"{size_ratio:.4g}x the median of its "
                            f"neighbouring labels ({med:.6g} mm^3), strictly "
                            f"below {size_thr:.6g}: it may be a fragment of "
                            f"a vertebra."
                        ),
                        labels=frozenset({label_int}),
                        detector_id="split_fragment",
                    )
                )
        return findings
