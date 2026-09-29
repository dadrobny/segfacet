"""Label-sequence sub-type rule (item 030; rewritten item 192, 2026-09-28).

Item 192 retires the item-030/186 defect recorded in ``insights.md``
(2026-09-27): the rule used to fire on ``relationships.out_of_order_labels[]``,
which ``segfacet.pipeline.extract_feature_record`` builds by walking the
per-case centroids in **ascending integer-label order**. TPTBox integer
values are not anatomical order -- T13 is 28, after L1-L5 (20-24), and
``Cocc`` is 27, before S2-S6 (29-33) -- so the old rule fired on a correct T13
or ``Cocc`` and never saw a real swap (``relabel_swap`` exchanges L2 and L3,
two adjacent integers, and the old rule stayed silent).

The rewritten rule stops reading ``relationships`` altogether. It orders each
kept ``per_label`` entry head-to-tail by ``centroid.centroid_mm`` (item 192
A4), ranks that order by ``segfacet.labels.CANONICAL_ORDER`` (S1-S6 sharing
one rank, item 186's sacrum-is-one-element decision), and reports what it
sees as one of four independent sub-types/detectors:

- ``swap`` -- two labels exchanged (a 2-cycle of the rank permutation).
- ``shift`` -- one or more labels moved several places, the labels between
  them each displaced by one (a longer cycle; only the most-displaced
  member(s) of each such cycle are named).
- ``skip`` -- a level absent between two present elements of the expected
  sequence (``segfacet.labels.expected_level_sequence``), case-level.
- ``transitional`` -- a non-default section count the field of view does not
  corroborate (``segfacet.labels.resolve_section_counts``'s ``unaccepted``),
  or a kept level outside the resulting reading's expected sequence.

``swap``/``shift`` serve mode 9 (out-of-order label sequence, a sub-mode of
mode 8), ``skip`` serves mode 10 (skipped level label) and ``transitional``
serves mode 11 (unprompted numbering variant); mode 8 itself gets no direct
edge (a mode-8 mislabelling that keeps the sequence valid cannot be seen by a
rule that reads the sequence), and mode 12 (a whole-sequence shift, internally
valid) stays out.

**The traversal direction is chosen, not fixed** (A4's 2026-09-28
correction). The record's ``centroid_mm`` is world RAS mm, so a purely
anatomical head-to-tail walk is descending ``centroid_mm[2]``; several unit
fixtures stack ascending labels at ascending z, though, and a fixed
descending direction would misread every one of them as reversed. The rule
therefore sorts the kept entries both ways (descending and ascending
``centroid_mm[2]``, ties broken by ascending label) and counts each order's
rank inversions, taking the ascending order only when it has strictly fewer
inversions -- otherwise the descending (anatomical) order stands. Two costs
follow, both Left open in the item-192 spec: a full reversal reads as
in-order (never reported), and a swap of the two end labels reads as a swap
of the middle pair.

This rule opts in to the ``displaced_vertebra`` condition (item 191): a label
swap puts a centroid off the curve fitted in label order, so ``spline_offset``
reads the swapped label as displaced too, and the runner's condition gate
would otherwise drop this rule's own ``swap``/``shift`` finding on that label.
The head-to-tail order survives a displacement that does not pass a
neighbour, which is exactly the case a swap creates.

Design decisions:
- At most one finding per detector, emitted in ascending ``detector_id``
  order (``shift``, ``skip``, ``swap``, ``transitional``): every 2-cycle of
  the rank permutation is folded into one ``swap`` finding and every longer
  cycle's most-displaced member(s) into one ``shift`` finding, rather than a
  finding per cycle.
- An entry is kept only when it is a mapping, its ``level_name`` is a
  recognised vertebra name, and its ``centroid.centroid_mm`` carries at least
  three numbers -- a hand-built record with no centroids therefore yields no
  finding (the defect this item removes would have fallen back to
  ``out_of_order_labels[]``; this rule no longer reads that path at all).
- Unrecognised severity string raises ValueError before any per-record
  processing.
- The caller's record is never mutated.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from segfacet.heuristics.finding import Finding
from segfacet.heuristics.rule import (
    ConditionOptIn,
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

_ORDER_TAG = "Non-continuous label sequence:"
_SKIP_TAG = "Skipped level label:"
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
    """Label-sequence sub-type rule (item 030; rewritten item 192).

    Runs four independent detectors over the head-to-tail order of kept
    ``per_label`` entries: ``shift``, ``skip``, ``swap`` and ``transitional``
    (module docstring)."""

    rule_id = "sequence"

    # This rule opts in to displaced_vertebra (item 191, 2026-09-28): a
    # label swap puts a centroid off the curve fitted in label order, so
    # spline_offset reads the swapped label as displaced too, but the
    # head-to-tail order this rule reads survives a displacement that does
    # not pass a neighbour -- exactly what a swap or shift creates.
    condition_opt_ins = (
        ConditionOptIn(
            condition="displaced_vertebra",
            paths=(
                "per_label.{label}.centroid.centroid_mm[]",
                "per_label.{label}.level_name",
            ),
            reason=(
                "a label swap reads as displaced (spline_offset fires on it "
                "too), but the head-to-tail order is judged by rank, which "
                "survives a displacement that does not pass a neighbour"
            ),
        ),
    )

    mode_declaration = RuleModeDeclaration(
        modes=(9, 10, 11),
        evidence=(
            "corpus-manifest",
            "tests/corpus/manifest.json's relabel_swap designates this rule "
            "for mode 9 (swap of two adjacent labels) and sequence_break for "
            "mode 9 (a single-label tail shift); remove_level co-detects "
            "this rule's skip on mode 10 beside coverage; mode 11 (a "
            "non-default section reading the field of view does not "
            "corroborate) has no committed corpus case, so that edge is "
            "analytic. Re-measured live, item 192 (2026-09-28), after the "
            "rule stopped reading relationships.out_of_order_labels[] "
            "(ascending integer-label order, item 186's defect) in favour "
            "of per_label centroids ranked by CANONICAL_ORDER.",
        ),
        consumed_paths=(
            ConsumedPath(
                path="per_label",
                role="bookkeeping",
                reason="container: iterated to build the head-to-tail order",
            ),
            ConsumedPath(
                path="per_label.{label}.centroid.centroid_mm[]",
                role="signal",
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
                detector_id="shift",
                description=_ORDER_TAG,
                question=(
                    "Are one or more labels moved several places along the "
                    "head-to-tail order of their levels?"
                ),
                fires_when=(
                    "the rank permutation of the centroid-ordered levels has "
                    "a cycle longer than two; names its most-displaced "
                    "member(s)"
                ),
                signal_paths=(
                    "per_label.{label}.centroid.centroid_mm[]",
                    "per_label.{label}.level_name",
                ),
            ),
            RuleDetector(
                detector_id="skip",
                description=_SKIP_TAG,
                question=(
                    "Is a level absent between two present levels of the "
                    "expected sequence?"
                ),
                fires_when=(
                    "an expected level lies between the first and last "
                    "present sequence elements and no present label carries it"
                ),
                signal_paths=("per_label.{label}.level_name",),
            ),
            RuleDetector(
                detector_id="swap",
                description=_ORDER_TAG,
                question=(
                    "Are two labels exchanged in the head-to-tail order of "
                    "their levels?"
                ),
                fires_when=(
                    "the rank permutation of the centroid-ordered levels has "
                    "a 2-cycle; names both members"
                ),
                signal_paths=(
                    "per_label.{label}.centroid.centroid_mm[]",
                    "per_label.{label}.level_name",
                ),
            ),
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
                    "sequence (Cocc excepted), excluding levels already named "
                    "by swap or shift"
                ),
                signal_paths=("per_label.{label}.level_name",),
            ),
        ),
    )

    def evaluate(self, record, config) -> List[Finding]:  # type: ignore[override]
        """Evaluate the four label-sequence sub-types for *record*.

        Parameters
        ----------
        record:
            Per-case feature dict (read-only). Reads ``record["per_label"]``
            only.
        config:
            HeuristicConfig instance. Reads ``rules.sequence.params``.

        Returns
        -------
        list[Finding]
            Zero to four findings (``shift``, ``skip``, ``swap``,
            ``transitional``, ascending), one per detector that fires.

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

        entries: List[Tuple[int, str, float]] = []
        for entry in per_label.values():
            if not isinstance(entry, dict):
                continue
            name = entry.get("level_name")
            if name not in _RANK:
                continue
            centroid = entry.get("centroid")
            centroid_mm = (
                centroid.get("centroid_mm") if isinstance(centroid, dict) else None
            )
            if not isinstance(centroid_mm, (list, tuple)) or len(centroid_mm) < 3:
                continue
            try:
                z = float(centroid_mm[2])
                label_value = int(entry["label"])
            except (KeyError, TypeError, ValueError):
                continue
            entries.append((label_value, name, z))

        if not entries:
            return []

        ordered = self._head_to_tail(entries)
        swap_named, shift_named = self._swaps_and_shifts(ordered)
        named_names = {name for _, name, _ in swap_named} | {
            name for _, name, _ in shift_named
        }

        present_names = [name for _, name, _ in entries]
        skip_names = self._skip_names(present_names)
        transitional_names = self._transitional_names(present_names, named_names)

        findings: List[Finding] = []
        if shift_named:
            names = ", ".join(name for _, name, _ in shift_named)
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=severity,
                    reason=f"{_ORDER_TAG} shift of {names}.",
                    labels=frozenset(label for label, _, _ in shift_named),
                    detector_id="shift",
                )
            )
        if skip_names:
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=severity,
                    reason=(
                        f"{_SKIP_TAG} {', '.join(skip_names)} absent between "
                        f"present levels."
                    ),
                    labels=frozenset(),
                    detector_id="skip",
                )
            )
        if swap_named:
            names = ", ".join(name for _, name, _ in swap_named)
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=severity,
                    reason=f"{_ORDER_TAG} swap of {names}.",
                    labels=frozenset(label for label, _, _ in swap_named),
                    detector_id="swap",
                )
            )
        if transitional_names:
            names = ", ".join(transitional_names)
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=severity,
                    reason=f"{_TRANSITIONAL_TAG} {names}.",
                    labels=frozenset(
                        label
                        for label, name, _ in entries
                        if name in transitional_names
                    ),
                    detector_id="transitional",
                )
            )
        return findings

    # -- head-to-tail order (A4, corrected direction) ---------------------- #

    @staticmethod
    def _inversions(order: List[Tuple[int, str, float]]) -> int:
        """Count rank inversions in *order* (pairs i<j with rank(i) > rank(j))."""
        n = len(order)
        count = 0
        for i in range(n):
            rank_i = _RANK[order[i][1]]
            for j in range(i + 1, n):
                if rank_i > _RANK[order[j][1]]:
                    count += 1
        return count

    @classmethod
    def _head_to_tail(
        cls, entries: List[Tuple[int, str, float]]
    ) -> List[Tuple[int, str, float]]:
        """The chosen head-to-tail order: descending ``centroid_mm[2]``
        unless the ascending order has strictly fewer rank inversions."""
        descending = sorted(entries, key=lambda t: (-t[2], t[0]))
        if len(entries) < 2:
            return descending
        ascending = sorted(entries, key=lambda t: (t[2], t[0]))
        if cls._inversions(ascending) < cls._inversions(descending):
            return ascending
        return descending

    # -- swap / shift (A5) -------------------------------------------------- #

    @staticmethod
    def _swaps_and_shifts(
        ordered: List[Tuple[int, str, float]]
    ) -> Tuple[List[Tuple[int, str, float]], List[Tuple[int, str, float]]]:
        """Decompose the rank permutation of *ordered* into cycles: every
        2-cycle names both members (``swap``); every longer cycle names its
        member(s) of largest |displacement| (``shift``). Both lists are in
        ascending position (head-to-tail) order."""
        n = len(ordered)
        expected = sorted(ordered, key=lambda t: _RANK[t[1]])
        expected_index = {label: i for i, (label, _, _) in enumerate(expected)}
        perm = [expected_index[label] for label, _, _ in ordered]

        seen = [False] * n
        swap_positions: List[int] = []
        shift_positions: List[int] = []
        for i in range(n):
            if seen[i] or perm[i] == i:
                continue
            cycle = []
            j = i
            while not seen[j]:
                seen[j] = True
                cycle.append(j)
                j = perm[j]
            if len(cycle) == 2:
                swap_positions.extend(cycle)
            else:
                displacement = {k: abs(perm[k] - k) for k in cycle}
                largest = max(displacement.values())
                shift_positions.extend(k for k in cycle if displacement[k] == largest)

        swap_named = [ordered[k] for k in sorted(swap_positions)]
        shift_named = [ordered[k] for k in sorted(shift_positions)]
        return swap_named, shift_named

    # -- skip / transitional (A6) ------------------------------------------- #

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
    def _skip_names(cls, present_names: List[str]) -> Tuple[str, ...]:
        _, reading, reading_rank = cls._reading(present_names)
        elems = {
            _element(name) for name in present_names if _element(name) in reading_rank
        }
        if len(elems) < 2:
            return ()
        ranks = sorted(reading_rank[e] for e in elems)
        lo, hi = ranks[0], ranks[-1]
        return tuple(name for name in reading[lo : hi + 1] if name not in elems)

    @classmethod
    def _transitional_names(
        cls, present_names: List[str], named_names: set
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
        names -= named_names
        return tuple(sorted(names, key=lambda n: _BASE_RANK.get(n, len(CANONICAL_ORDER))))
