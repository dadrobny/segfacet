"""Mislabel / ordering rule (item 033, Detector A moved out at item 189).

Implements a **mislabel rule** with one detector, serving one mode of
``failure_modes.SPECIFICATION``:

- **Mode 9 — out-of-order label sequence** (a sub-mode of mode 8, semantic
  mislabelling / wrong vertebra identification).
  Detector B flags a vertebra whose physical position is inconsistent with
  its anatomical label's expected ordering relative to neighbours, via the
  monotonic-progression metric
  (``pairs.adjacent.non_monotonic_pairs``, items 020, 216).

Item 033's Detector A (spline-offset misalignment) moved to
``heuristics/spline_offset.py`` at item 189: it served no failure mode since
the item-150 sign-off (the spline offset is an anatomy-classification
signal, not a segmentation defect), and its firing is now the recording rule
of the ``displaced_vertebra`` CONDITION (``failure_modes.CONDITIONS``,
alongside ``fov_truncation``) -- see that module for its docstring,
threshold-calibration history and corpus margins.

It consumes two already-serialised sub-blocks of the per-case feature
record — ``pairs.adjacent.non_monotonic_pairs`` (items 020, 216) and ``per_label``
(item 016) — and never recomputes any geometry, spline, or ordering itself.

Design decisions (recorded per item 033 spec):
- Detector B fires on each ``non_monotonic_pairs`` entry, resolving both
  level names to integer labels via ``per_label``; an unresolvable name is
  omitted from ``labels`` but still named in the ``reason``.
- Order findings are emitted in ascending ``(level_a, level_b)`` name-pair
  order; the detector re-sorts defensively so output never depends on the
  input list order.
- Unrecognised severity string raises ValueError before any per-record
  processing.
- The caller's record is never mutated.
- This rule opts in to the ``displaced_vertebra`` condition (item 191,
  2026-09-28): a mislabelled vertebra can itself read as displaced
  (``spline_offset`` fires on it too), and the runner's condition gate would
  otherwise drop this rule's own ordering finding on that label, hiding a
  genuine segmentation defect behind an anatomy condition. The ordering
  signal is not spoiled by a moderate displacement: it is judged against the
  centroids' label-free geometric order (item 210), and a swapped label keeps
  its place in that order unless it moves past a neighbour -- which is exactly
  what this rule reports. A gross lateral displacement of about twice the
  level spacing can bend that order and add false pairs on undisplaced
  neighbours (item 210, Left open b).
- Item 198 (2026-09-29): the pairs are judged in ``CANONICAL_ORDER`` order
  (the pipeline hands ``compute_monotonic_consistency`` the centroids in
  anatomical order), so a correctly placed T13 or ``Cocc`` no longer reads
  as out of order.
"""

from __future__ import annotations

from typing import Dict, List, Optional

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

__all__ = ["MislabelRule"]


# --------------------------------------------------------------------------- #
# Reason tag constants — stable, testable start-of-reason markers
# --------------------------------------------------------------------------- #

_MISLABEL_TAG = "Vertebra ordering inconsistent with label:"


# --------------------------------------------------------------------------- #
# Severity helper (mirrors bounds.py / sequence.py / border.py / overlap.py)
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
            f"Unknown severity label {label!r} in mislabel rule config. "
            f"Known labels: {known}."
        )
    return sev


def _label_for_level(per_label: dict, level_name: str) -> Optional[int]:
    """Locate the integer label for *level_name* by scanning ``per_label``.

    ``per_label`` is keyed by integer label, not level name, so a direct key
    lookup is not possible (mirrors sequence.py's ``_label_for_level``).
    Returns ``None`` if no entry matches or *per_label* is not a mapping.
    """
    if not isinstance(per_label, dict):
        return None
    for entry in per_label.values():
        if isinstance(entry, dict) and entry.get("level_name") == level_name:
            return int(entry["label"])
    return None


# --------------------------------------------------------------------------- #
# MislabelRule
# --------------------------------------------------------------------------- #


@register_rule
class MislabelRule(Rule):
    """Mislabel / ordering rule (item 033; Detector A moved to
    ``spline_offset`` at item 189).

    Runs one config-gated detector: monotonic-progression inconsistencies
    (Detector B, specification mode 9, out-of-order label sequence) in
    ascending name-pair order.
    """

    rule_id = "mislabel"

    # This rule opts in to displaced_vertebra (item 191): a mislabelled
    # vertebra can itself read as displaced, and the ordering signal is not
    # spoiled by a moderate displacement (see module docstring).
    condition_opt_ins = (
        ConditionOptIn(
            condition="displaced_vertebra",
            paths=("pairs.adjacent.non_monotonic_pairs[]",),
            reason=(
                "a mislabelled vertebra can read as displaced "
                "(spline_offset fires on it too), but the ordering is "
                "judged against the centroids' label-free geometric order "
                "(item 210), which a moderate displacement does not spoil"
            ),
        ),
    )

    # Specification mode 9 (out-of-order label sequence):
    # RelabelSwapPerturbation designates mode 9
    # (src/segfacet/synth/identity_ordering_alignment.py) via
    # Expectation(..., expected_rule_ids={"mislabel"}). Item 189 moved the
    # former mode-less Detector A (spline offset) to its own rule,
    # heuristics.spline_offset; this rule now declares only mode 9.
    mode_declaration = RuleModeDeclaration(
        modes=(9,),
        evidence=(
            "corpus-manifest",
            "tests/corpus/manifest.json's relabel_swap designates "
            "this rule for mode 9 (out-of-order label sequence) of the "
            "catalogue signed off at item 150 (2026-09-14, revised "
            "2026-09-15) via Detector B (ordering). Item 189 (2026-09-28) "
            "moved the former Detector A (spline offset), which served no "
            "failure mode, to heuristics.spline_offset -- see that "
            "module's declaration for its evidence.",
        ),
        consumed_paths=(
            ConsumedPath(
                path="pairs.adjacent.non_monotonic_pairs[]",
                role="signal",
            ),
            ConsumedPath(
                path="per_label",
                role="bookkeeping",
                reason=(
                    "container: scanned by _label_for_level to resolve a "
                    "non-monotonic pair's level names back to integer label "
                    "ids for the finding's labels set; "
                    "non_monotonic_pairs[] carries the evidence"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.label",
                role="bookkeeping",
                reason=(
                    "the integer id a resolved non-monotonic pair reports "
                    "in the finding's labels"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.level_name",
                role="bookkeeping",
                reason=(
                    "matched against a pair's level names by "
                    "_label_for_level"
                ),
            ),
        ),
        detectors=(
            RuleDetector(
                detector_id="ordering",
                description=_MISLABEL_TAG,
                question=(
                    "Do two labels sit in the wrong order along the "
                    "label-free path through the vertebra centroids?"
                ),
                fires_when=(
                    "`flag_order_inconsistency` and "
                    "`pairs.adjacent.non_monotonic_pairs` lists "
                    "a level pair; one finding per pair"
                ),
                params=(("flag_order_inconsistency", True),),
                signal_paths=(
                    "pairs.adjacent.non_monotonic_pairs[]",
                ),
            ),
        ),
    )

    def evaluate(self, record, config) -> List[Finding]:  # type: ignore[override]
        """Evaluate mislabel / ordering signals for *record*.

        Parameters
        ----------
        record:
            Per-case feature dict (read-only). Reads
            ``record["pairs"]["adjacent"]["non_monotonic_pairs"]`` and
            ``record["per_label"]``.
        config:
            HeuristicConfig instance. Reads ``rules.mislabel.params``.

        Returns
        -------
        list[Finding]
            Zero or more order findings (ascending name-pair order).

        Raises
        ------
        ValueError
            If ``rules.mislabel.params.severity`` is an unrecognised string
            (raised before any per-record processing, AC16).
        """
        # Read severity once up-front; raises immediately on a bad string.
        sev_label: str = config.rule_param(
            self.rule_id, "severity", default="flagged-for-review"
        )
        severity = _severity_from_param(sev_label)

        flag_order = bool(
            config.rule_param(
                self.rule_id, "flag_order_inconsistency", default=True
            )
        )

        pairs = record.get("pairs")
        adjacent = pairs.get("adjacent") if isinstance(pairs, dict) else None
        if not isinstance(adjacent, dict):
            adjacent = {}

        if not flag_order:
            return []

        return self._detect_order_inconsistency(adjacent, record, severity)

    @staticmethod
    def _detect_order_inconsistency(
        adjacent: dict, record: dict, severity: Severity
    ) -> List[Finding]:
        """Detector B: monotonic-progression inconsistency (mislabelling,
        specification mode 9)."""
        pairs = adjacent.get("non_monotonic_pairs")
        if not isinstance(pairs, list):
            return []

        per_label = record.get("per_label")
        if not isinstance(per_label, dict):
            per_label = {}

        normalised = []
        for pair in pairs:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                continue
            level_a, level_b = pair[0], pair[1]
            la = _label_for_level(per_label, level_a)
            lb = _label_for_level(per_label, level_b)
            normalised.append((level_a, level_b, la, lb))

        normalised.sort(key=lambda t: (t[0], t[1]))

        findings: List[Finding] = []
        for level_a, level_b, la, lb in normalised:
            findings.append(
                Finding(
                    rule_id="mislabel",
                    severity=severity,
                    reason=(
                        f"{_MISLABEL_TAG} labels {la} ({level_a}) and "
                        f"{lb} ({level_b}) are out of expected order along "
                        f"the spine (position along the label-free path "
                        f"through the centroids does not advance)."
                    ),
                    labels=frozenset(
                        {x for x in (la, lb) if x is not None}
                    ),
                    detector_id="ordering",
                )
            )
        return findings
