"""Neighbour-contact rule (item 187), serving mode 3 (split vertebra segment).

Item 167 added a mode-3 detector to ``fragmentation.py`` reading the absolute
``stray_contact_area_mm2`` field. This item gives mode 3 a rule of its own,
because ``fragmentation``'s other two detectors (``components``, ``islands``)
read one label split into several parts, which is not mode 3 (one vertebra
under several labels): after this item ``fragmentation`` declares modes
``(1, 4)`` and this rule alone declares ``(3,)``.

**Why the measure changes.** ``stray_contact_area_mm2`` is an absolute area,
so a small stray component shows little absolute contact even when most of
its surface touches a neighbour. This rule instead reads the *relative*
measure item 187 added to ``ComponentsInfo``/the serialised record: each
stray component's ``contact_fraction`` -- its contact area with its
most-contacted neighbour, divided by its own surface area.

Design decisions (recorded per item 187 spec, A5-A7):
- **Stray components only.** The rule reads
  ``components.component_contacts[1:]`` -- never index 0 (the label's
  largest component) and never ``label_contact_fraction``. Measured
  2026-09-29 on both committed corpora, the only labels whose largest
  component or whole label touches a neighbour are ``split`` label 23 (the
  donor: 0.186 at both scopes), ``split`` label 24 (largest component 0.0,
  but 0.102 at label scope, because the stray piece touches), and
  ``split_own_label`` labels 22 (0.186) and 23 (0.332) at both scopes. So
  reading the largest component or the label scope would fire on
  ``split_own_label``, outside mode 3's split-vertebra-segment sub-type (a);
  ``split`` label 24's label-scope reading sits barely above the threshold.
  The stray-only scope is what keeps ``split_own_label`` out; on ``split``
  the wider readings would fire too, so they are not what separates it.
- **One finding per stray component above threshold**, not one per label:
  a label with more than one over-threshold stray component names each.
- **Fired strictly above** the threshold (item 027's convention, also
  ``fragmentation``'s), never ``>=``.
- **Absence-tolerant**: a label whose ``components`` block lacks
  ``component_contacts`` (a legacy, pre-item-187 record shape) is skipped,
  never raises.
- **No active ``rules.neighbour_contact`` config section.** The threshold is
  documented as a comment in ``default_config.yaml``, like ``intensity`` and
  ``intensity_reference_delta`` -- an active section would move
  ``config_hash`` in every report. ``rule_enabled`` defaults to ``True`` for
  an absent section.
- Unrecognised severity string raises ``ValueError`` before any per-label
  work, mirroring ``fragmentation``.
- The caller's record is never mutated.

Scope fence: no new corpus case or fixture change (this item); no change to
``fragmentation``'s ``components``/``islands`` detectors, their thresholds,
or modes 1 and 4; mode 3 sub-type (b) (``split_own_label``, the cap is its
own label's only component, so it has no stray component) is not detected by
this rule (Left open, item 187 spec).
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

__all__ = ["NeighbourContactRule", "DEFAULT_CONTACT_FRACTION"]


# --------------------------------------------------------------------------- #
# Shipped hand-set default
# --------------------------------------------------------------------------- #

DEFAULT_CONTACT_FRACTION: float = 0.1
"""Fire when a stray component's contact_fraction strictly exceeds this value
(item 187, mode 3 -- split vertebra segment). Calibrated on the synthetic
corpus only (Stage 21 re-calibrates on real ground truth): measured
2026-09-27 on both committed corpora, the only firing value is the split
case's label-24 stray component, 0.3317 (806.0 mm^2 against label 23, over
2430.0 mm^2 of surface, 4030 voxels), +0.2317 above threshold (3.3x); every
other stray component measures 0.0, 0.1 below it. Documented as a comment
only in ``default_config.yaml`` -- a new parsed key would move
``config_hash`` in every report (item 048/090's house pattern, also
``fragmentation``'s)."""


# --------------------------------------------------------------------------- #
# Reason tag constant — stable, testable start-of-reason marker
# --------------------------------------------------------------------------- #

_CONTACT_TAG = "Neighbour contact:"


# --------------------------------------------------------------------------- #
# Severity helper (mirrors fragmentation.py / sequence.py)
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
            f"Unknown severity label {label!r} in neighbour_contact rule "
            f"config. Known labels: {known}."
        )
    return sev


# --------------------------------------------------------------------------- #
# NeighbourContactRule
# --------------------------------------------------------------------------- #


@register_rule
class NeighbourContactRule(Rule):
    """Neighbour-contact rule (item 187), serving mode 3 (split vertebra
    segment).

    For each vertebra label present in the feature record, reads its stray
    components' (``component_contacts[1:]``) relative contact measure. Any
    stray component whose ``contact_fraction`` strictly exceeds the
    configured threshold emits one ``Finding`` naming the label, the
    component's rank and voxel count, its contact fraction, and its
    ``neighbour_label`` as the merge candidate.
    """

    rule_id = "neighbour_contact"

    # Specification mode 3 (split vertebra segment): SplitPerturbation
    # (src/segfacet/synth/component_shape.py) designates this rule via
    # Expectation(expected_rule_ids={"neighbour_contact"}).
    mode_declaration = RuleModeDeclaration(
        modes=(3,),
        evidence=(
            "corpus-manifest",
            "tests/corpus/manifest.json's split designates this rule "
            "for mode 3 (split vertebra segment) of the catalogue signed "
            "off at item 150 (2026-09-14, revised 2026-09-15). Item 187 "
            "moved the detector here from fragmentation.py and re-expressed "
            "the threshold on the relative measure: measured 2026-09-27, "
            "the split case's label-24 stray component reads a "
            "contact_fraction of 0.3317, +0.2317 above the 0.1 threshold "
            "(3.3x), and every other stray component in either corpus "
            "measures 0.0 -- the stray_contact detector. The mode 3 <-> "
            "neighbour_contact evidence claim is the per-edge rung in "
            "segfacet.failure_modes.SPECIFICATION[3].",
        ),
        consumed_paths=(
            ConsumedPath(
                path="per_label",
                role="bookkeeping",
                reason=(
                    "container: iterated to reach each label's components "
                    "block"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.components.component_contacts[].contact_fraction",
                role="signal",
            ),
            ConsumedPath(
                path="per_label.{label}.components.component_contacts[].neighbour_label",
                role="bookkeeping",
                reason=(
                    "identity: names the merge-candidate neighbour label in "
                    "the finding's reason; contact_fraction is the mode-3 "
                    "evidence"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.components.component_sizes[]",
                role="bookkeeping",
                reason=(
                    "identity: names the stray component's voxel count in "
                    "the finding's reason, same order as component_contacts"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.level_name",
                role="bookkeeping",
                reason=(
                    "identity and message interpolation: names the level "
                    "in the finding; component_contacts carries the mode-3 "
                    "evidence"
                ),
            ),
        ),
        detectors=(
            RuleDetector(
                detector_id="stray_contact",
                description=_CONTACT_TAG,
                question=(
                    "Does a stray component of this label press against a "
                    "neighbouring label over a large share of its own surface?"
                ),
                fires_when=(
                    "`contact_fraction` > `contact_fraction_threshold`, "
                    "strictly, per stray component (never index 0, the "
                    "largest component)"
                ),
                params=(("contact_fraction_threshold", DEFAULT_CONTACT_FRACTION),),
                signal_paths=(
                    "per_label.{label}.components.component_contacts[].contact_fraction",
                ),
            ),
        ),
    )

    def evaluate(self, record, config) -> List[Finding]:  # type: ignore[override]
        """Evaluate neighbour-contact for every label in *record*.

        Parameters
        ----------
        record:
            Per-case feature dict (read-only). Reads ``record["per_label"]``.
        config:
            HeuristicConfig instance. Reads ``rules.neighbour_contact.params``.

        Returns
        -------
        list[Finding]
            Zero or more findings; empty when no stray component exceeds the
            threshold, or when a label's ``components`` block carries no
            ``component_contacts`` (absence-tolerant, A7).

        Raises
        ------
        ValueError
            If ``rules.neighbour_contact.params.severity`` is an unrecognised
            string, raised before any per-label processing.
        """
        # Read severity once up-front; raises immediately on a bad string.
        sev_label: str = config.rule_param(
            self.rule_id, "severity", default="flagged-for-review"
        )
        severity = _severity_from_param(sev_label)

        threshold: float = config.rule_param(
            self.rule_id,
            "contact_fraction_threshold",
            default=DEFAULT_CONTACT_FRACTION,
        )

        findings: List[Finding] = []
        per_label = record.get("per_label", {})

        # Ascending integer-label order for determinism (mirrors fragmentation.py).
        for label_key in sorted(per_label.keys(), key=int):
            entry = per_label[label_key]
            label_int = int(label_key)
            level_name: str = entry.get("level_name", "unknown")

            comp = entry.get("components")
            if not isinstance(comp, dict):
                continue

            contacts = comp.get("component_contacts")
            if not contacts:
                # Absence-tolerant (A7): no component_contacts key, or an
                # empty list -- nothing to read.
                continue

            sizes = comp.get("component_sizes") or []

            for rank, contact in enumerate(contacts[1:], start=1):
                fraction = contact.get("contact_fraction", 0.0)
                if fraction is None or fraction <= threshold:
                    continue
                neighbour = contact.get("neighbour_label", 0)
                voxel_count = sizes[rank] if rank < len(sizes) else "?"
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=severity,
                        reason=(
                            f"{_CONTACT_TAG} Label {label_int} ({level_name}): "
                            f"stray component rank {rank} "
                            f"({voxel_count} voxels) has contact_fraction="
                            f"{fraction:.6g}, strictly above threshold "
                            f"{threshold:.6g}. Label {neighbour} is the merge "
                            f"candidate."
                        ),
                        labels=frozenset({label_int}),
                        detector_id="stray_contact",
                    )
                )

        return findings
