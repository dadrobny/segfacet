"""Label-sequence sub-type rule (item 030; rewritten item 192; narrowed item 219).

Item 192 retired the item-030/186 defect recorded in ``insights.md``
(2026-09-27): the rule used to fire on ``relationships.out_of_order_labels[]``,
which is built in **ascending integer-label order**, and TPTBox integer values
are not anatomical order (T13 is 28, after L1-L5). Item 192 replaced it with
four detectors (``swap``, ``shift``, ``skip``, ``transitional``) that sorted
centroids by ``centroid_mm[2]``.

Item 219 (2026-10-12) retired three of them. ``swap`` and ``shift`` duplicated
mode 9's check, which belongs to ``mislabel``'s ``ordering`` detector: that one
reads ``pairs.adjacent.non_monotonic_pairs[]``, position along the label-free
path (item 210), which is robust to curvature and pose. The z-sort is not: it
fired ``shift`` on L5 of a correctly labelled 210-degree arc, and ``shift`` (L5)
plus ``swap`` (L1, L4) on a reclined 90-degree arc, where the path reads
nothing. ``skip`` duplicated mode 10's ``coverage``/``missing_interior`` on the
same label gap. The rule now reads **level names only**, never a centroid.

What remains is ``transitional`` -- a non-default section count the field of
view does not corroborate (``segfacet.labels.resolve_section_counts``'s
``unaccepted``), or a kept level outside the resulting reading's expected
sequence (``segfacet.labels.expected_level_sequence``); mode 11 (unprompted
numbering variant). It skips every level named in
``pairs.adjacent.non_monotonic_pairs[]``: without that, ``sequence_break``'s
T13 (label 28, an uncorroborated thoracic count of 13) would fire
``transitional`` on a mode-9 case, against mode 11's own discriminator (a T13
below an L-level is out of order, not a variant). A record with no ``pairs`` or
no ``adjacent`` block excludes nothing.

Design decisions:
- An entry is kept when it is a mapping, its ``level_name`` is a recognised
  vertebra name, and its ``label`` is an integer.
- Unrecognised severity string raises ValueError before any per-record
  processing.
- The caller's record is never mutated.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from segfacet.heuristics.finding import Finding
from segfacet.heuristics.rule import (
    ConsumedPath,
    Rule,
    RuleDetector,
    RuleModeDeclaration,
    register_rule,
)
from segfacet.labels import (
    CANONICAL_ORDER,
    SACRUM,
    expected_level_sequence,
    resolve_section_counts,
)
from segfacet.verdict import Severity

__all__ = ["SequenceRule"]


# --------------------------------------------------------------------------- #
# Reason tag constants — stable, testable start-of-reason markers
# --------------------------------------------------------------------------- #

_TRANSITIONAL_TAG = "Transitional level label without field-of-view evidence:"


# --------------------------------------------------------------------------- #
# Severity helper (mirrors bounds.py / coverage.py / mislabel.py)
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
            f"Unknown severity label {label!r} in sequence rule config. "
            f"Known labels: {known}."
        )
    return sev


# --------------------------------------------------------------------------- #
# Rank model — CANONICAL_ORDER, with S1-S6 collapsed onto one rank (item 186:
# the sacrum is one element). Cocc keeps its own (last) rank.
# --------------------------------------------------------------------------- #

_BASE_RANK: Dict[str, int] = {name: i for i, name in enumerate(CANONICAL_ORDER)}
_SACRAL_NAMES: Tuple[str, ...] = tuple(f"S{i}" for i in range(1, 7))
_RANK: Dict[str, int] = dict(_BASE_RANK)
_S1_RANK = _RANK["S1"]
for _name in _SACRAL_NAMES:
    _RANK[_name] = _S1_RANK


def _element(name: str) -> str:
    """The expected-sequence element *name* stands for: SACRUM for any
    sacral name, else *name* itself."""
    return SACRUM if name in _SACRAL_NAMES else name


# --------------------------------------------------------------------------- #
# SequenceRule
# --------------------------------------------------------------------------- #


@register_rule
class SequenceRule(Rule):
    """Label-sequence sub-type rule (item 030; narrowed item 219).

    Runs one detector, ``transitional``, over the level names of kept
    ``per_label`` entries (module docstring)."""

    rule_id = "sequence"

    mode_declaration = RuleModeDeclaration(
        modes=(11,),
        evidence=(
            "analytic: no committed corpus case designates this rule. Mode 11 "
            "(a non-default section reading the field of view does not "
            "corroborate) has no corpus case. Item 219 (2026-10-12) retired "
            "swap, shift and skip, which duplicated mislabel's ordering "
            "(mode 9) and coverage's missing_interior (mode 10); measured "
            "then, without the pairs exclusion sequence_break fires "
            "transitional on T13 (label 28), and with it sequence fires on "
            "no corpus case.",
        ),
        consumed_paths=(
            ConsumedPath(
                path="pairs.adjacent.non_monotonic_pairs[]",
                role="bookkeeping",
                reason=(
                    "gate: levels mislabel's ordering detector names are "
                    "mode 9's, not a numbering variant"
                ),
            ),
            ConsumedPath(
                path="per_label",
                role="bookkeeping",
                reason="container: iterated to collect the present level names",
            ),
            ConsumedPath(
                path="per_label.{label}.label",
                role="bookkeeping",
                reason="identity: the integer label id a kept entry names",
            ),
            ConsumedPath(
                path="per_label.{label}.level_name",
                role="signal",
            ),
        ),
        detectors=(
            RuleDetector(
                detector_id="transitional",
                description=_TRANSITIONAL_TAG,
                question=(
                    "Does the level numbering use a non-default section "
                    "count the field of view does not corroborate?"
                ),
                fires_when=(
                    "a section count is unaccepted by the resolved reading, "
                    "or a present level lies outside that reading's expected "
                    "sequence (Cocc excepted), excluding levels named in "
                    "pairs.adjacent.non_monotonic_pairs[]"
                ),
                signal_paths=("per_label.{label}.level_name",),
            ),
        ),
    )

    def evaluate(self, record, config) -> List[Finding]:  # type: ignore[override]
        """Evaluate the ``transitional`` sub-type for *record*.

        Parameters
        ----------
        record:
            Per-case feature dict (read-only). Reads ``record["per_label"]``
            and ``record["pairs"]["adjacent"]["non_monotonic_pairs"]``.
        config:
            HeuristicConfig instance. Reads ``rules.sequence.params``.

        Returns
        -------
        list[Finding]
            Zero or one ``transitional`` finding.

        Raises
        ------
        ValueError
            If ``rules.sequence.params.severity`` is an unrecognised string
            (raised before any per-record processing).
        """
        # Read severity once up-front; raises immediately on a bad string.
        sev_label: str = config.rule_param(
            self.rule_id, "severity", default="flagged-for-review"
        )
        severity = _severity_from_param(sev_label)

        per_label = record.get("per_label")
        if not isinstance(per_label, dict):
            per_label = {}

        entries: List[Tuple[int, str]] = []
        for entry in per_label.values():
            if not isinstance(entry, dict):
                continue
            name = entry.get("level_name")
            if name not in _RANK:
                continue
            try:
                label_value = int(entry["label"])
            except (KeyError, TypeError, ValueError):
                continue
            entries.append((label_value, name))

        if not entries:
            return []

        # Levels mislabel's ordering detector names are mode 9's (item 219).
        pairs = record.get("pairs")
        adjacent = pairs.get("adjacent") if isinstance(pairs, dict) else None
        raw_pairs = (
            adjacent.get("non_monotonic_pairs") if isinstance(adjacent, dict) else None
        )
        ordering_names = set()
        for pair in raw_pairs or ():
            ordering_names.update(pair)

        present_names = [name for _, name in entries]
        transitional_names = self._transitional_names(present_names, ordering_names)
        if not transitional_names:
            return []
        names = ", ".join(transitional_names)
        return [
            Finding(
                rule_id=self.rule_id,
                severity=severity,
                reason=f"{_TRANSITIONAL_TAG} {names}.",
                labels=frozenset(
                    label for label, name in entries if name in transitional_names
                ),
                detector_id="transitional",
            )
        ]

    # -- transitional (A6) ------------------------------------------- #

    @staticmethod
    def _reading(present_names: List[str]):
        """The resolved section counts and their reading's expected sequence
        + rank map (A6: the resolved counts with each unaccepted reading
        substituted)."""
        resolved = resolve_section_counts(present_names)
        reading_counts = resolved.counts._replace(**resolved.unaccepted)
        reading = expected_level_sequence(reading_counts)
        reading_rank = {name: i for i, name in enumerate(reading)}
        return resolved, reading, reading_rank

    @classmethod
    def _transitional_names(
        cls, present_names: List[str], excluded_names: set
    ) -> Tuple[str, ...]:
        resolved, _, reading_rank = cls._reading(present_names)

        names = set()
        for section, observed in resolved.unaccepted.items():
            prefix = "T" if section == "thoracic" else "L"
            names.add(f"{prefix}{observed}")
        for name in set(present_names):
            if name == "Cocc":
                continue
            if _element(name) not in reading_rank:
                names.add(name)
        names -= excluded_names
        return tuple(sorted(names, key=lambda n: _BASE_RANK.get(n, len(CANONICAL_ORDER))))
