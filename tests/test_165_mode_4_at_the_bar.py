"""Tests for item 165 -- mode 4 (islands) brought to the fully-specified bar
(``segfacet.traceability.bar_conditions(mode_id)``: conditions 1-5 of
``roadmap.md`` Stage 32's "fully specified end to end" bar, each recomputed
live from ``segfacet.failure_modes.SPECIFICATION``, the rule registry and
``segfacet.catalogue.build_catalogue``). Condition 6 (maintainer sign-off) is
item 168's and is never attempted here.

Covers Acceptance Criteria AC1-AC7 per the item spec's Testing Strategy: one
test per AC, each recomputing its predicate from the primary source
(``failure_modes`` and the live catalogue) and asserting the
``bar_conditions(4, ...)`` record agrees -- never a literal. Plus exactly the
four adversarial cases the Testing Strategy names:
``proxy-detector-never-decides-the-mode``,
``uncatalogued-detector-path-fails-condition-3``,
``co-detection-alone-fails-condition-2`` and ``unknown-mode-id-raises``.

Shape (module-scoped-drive idiom of ``test_149``/``test_162``/``test_163``):
one module-scoped fixture builds ``build_catalogue(strict=True)`` once, one
module-scoped fixture holds ``bar_conditions(4, catalogue=<that catalogue>)``.
No ``build_catalogue()`` call in any test body -- the adversarial cases below
re-call ``bar_conditions`` inside their own patch, passing the same cached
catalogue.
"""

from __future__ import annotations

import dataclasses as dc

import pytest


# =========================================================================== #
# Module-scoped drive fixtures (no second build_catalogue() call anywhere).
# =========================================================================== #


@pytest.fixture(scope="module")
def cached_catalogue():
    from segfacet.catalogue import build_catalogue

    return build_catalogue(strict=True)


@pytest.fixture(scope="module")
def bar(cached_catalogue):
    import segfacet.traceability as traceability

    return traceability.bar_conditions(4, catalogue=cached_catalogue)


def _record(bar_result, number):
    matches = [record for record in bar_result if record.number == number]
    assert len(matches) == 1, f"expected exactly one record numbered {number}, got {matches}"
    return matches[0]


# =========================================================================== #
# AC1: exactly conditions 1-5, ascending, no 6.
# =========================================================================== #


def test_ac1_bar_enumerates_exactly_conditions_one_through_five(bar):
    numbers = tuple(record.number for record in bar)
    assert numbers == (1, 2, 3, 4, 5)
    assert 6 not in numbers


# =========================================================================== #
# AC2: condition 1 -- the specification entry's eight roadmap-named fields.
# =========================================================================== #


def test_ac2_condition_1_entry_completeness_recomputed(bar):
    import segfacet.failure_modes as failure_modes

    mode = failure_modes.SPECIFICATION[4]
    fields = (
        "definition",
        "discriminator",
        "scope",
        "observability",
        "severity",
        "candidate_features",
        "intended_rules",
        "corpus_cases",
    )
    recomputed_met = all(bool(getattr(mode, field)) for field in fields)

    record = _record(bar, 1)
    assert record.met is recomputed_met
    assert recomputed_met is True


# =========================================================================== #
# AC3: condition 2 -- a committed fixture expresses the mode.
# =========================================================================== #


def test_ac3_condition_2_fixture_expresses_mode_recomputed(bar):
    import segfacet.failure_modes as failure_modes

    mode = failure_modes.SPECIFICATION[4]
    own_rules = {edge.rule_id for edge in mode.intended_rules}

    all_agree = all(failure_modes.case_agrees(case) for case in mode.corpus_cases)
    intersecting_case_ids = tuple(
        case.case_id
        for case in mode.corpus_cases
        if case.expected_firing and own_rules.intersection(case.expected_firing)
    )
    recomputed_met = all_agree and bool(intersecting_case_ids)

    record = _record(bar, 2)
    assert record.met is recomputed_met
    assert record.subjects == intersecting_case_ids
    assert recomputed_met is True


# =========================================================================== #
# AC4: condition 3 -- every signal path the deciding detector(s) read is
# extracted and catalogued.
# =========================================================================== #


def test_ac4_condition_3_detector_paths_extracted_and_catalogued(bar, cached_catalogue):
    from segfacet.heuristics.rule import iter_rules

    condition_4_record = _record(bar, 4)
    catalogue_paths = {entry.path: entry for entry in cached_catalogue.entries}

    checked_paths = set()
    for pair in condition_4_record.subjects:
        rule_id, detector_id = pair.split("/", 1)
        rule = next(r for r in iter_rules() if r.rule_id == rule_id)
        detector = next(
            d for d in rule.mode_declaration.detectors if d.detector_id == detector_id
        )
        checked_paths.update(detector.signal_paths)

    assert checked_paths, "expected at least one signal path to check"
    recomputed_met = all(
        path in catalogue_paths and catalogue_paths[path].observed.corpus.covered is True
        for path in checked_paths
    )

    record = _record(bar, 3)
    assert record.met is recomputed_met
    assert record.subjects == tuple(sorted(checked_paths))
    assert recomputed_met is True


# =========================================================================== #
# AC5: condition 4 -- a single, non-proxy detector decides the mode.
# =========================================================================== #


def test_ac5_condition_4_single_non_proxy_detector_decides(bar):
    import segfacet.failure_modes as failure_modes
    import segfacet.traceability as traceability

    mode = failure_modes.SPECIFICATION[4]
    qualifying = tuple(
        sorted(
            f"{edge.rule_id}/{detector_id}"
            for edge in mode.intended_rules
            if edge.rule_id not in traceability.PROXY_RULE_IDS
            for detector_id in edge.detector_ids
            if failure_modes.modes_for_detector(edge.rule_id, detector_id) == (4,)
        )
    )

    record = _record(bar, 4)
    assert record.subjects == ("fragmentation/islands",)
    assert record.subjects == qualifying
    assert record.met is bool(qualifying)
    assert record.met is True


# =========================================================================== #
# AC6: condition 5 -- status derives validated.
# =========================================================================== #


def test_ac6_condition_5_status_derives_validated(bar):
    import segfacet.failure_modes as failure_modes

    mode = failure_modes.SPECIFICATION[4]
    recomputed_met = failure_modes.derive_status(mode) == "validated"

    record = _record(bar, 5)
    assert record.met is recomputed_met
    assert recomputed_met is True


# =========================================================================== #
# AC7: every record's subjects occur in its own detail -- the anti-vacuity
# criterion.
# =========================================================================== #


def test_ac7_every_record_names_its_subjects_in_detail(bar):
    checked = 0
    for record in bar:
        assert record.subjects, f"condition {record.number} carries no subjects"
        assert record.detail, f"condition {record.number} carries no detail"
        for subject in record.subjects:
            assert isinstance(subject, str) and subject, (
                f"condition {record.number} has a non-string or empty subject: {subject!r}"
            )
            assert subject in record.detail, (
                f"condition {record.number}'s detail does not name subject {subject!r}: "
                f"{record.detail!r}"
            )
            checked += 1
    assert checked, "expected at least one subject to have been checked"


# =========================================================================== #
# Adversarial case: proxy-detector-never-decides-the-mode.
# =========================================================================== #


def test_proxy_detector_never_decides_the_mode(monkeypatch, cached_catalogue):
    import segfacet.failure_modes as failure_modes
    import segfacet.traceability as traceability

    original = failure_modes.SPECIFICATION
    patched = dict(original)

    for mode_id in (1, 2, 3):
        mode = original[mode_id]
        patched[mode_id] = dc.replace(
            mode,
            intended_rules=tuple(
                edge
                for edge in mode.intended_rules
                if not (edge.rule_id == "bounds" and "metric_out_of_range" in edge.detector_ids)
            ),
        )

    mode4 = original[4]
    patched[4] = dc.replace(
        mode4,
        intended_rules=tuple(edge for edge in mode4.intended_rules if edge.rule_id != "fragmentation"),
    )

    monkeypatch.setattr(failure_modes, "SPECIFICATION", patched)

    assert failure_modes.modes_for_detector("bounds", "metric_out_of_range") == (4,)

    result = traceability.bar_conditions(4, catalogue=cached_catalogue)
    condition_4 = _record(result, 4)
    assert condition_4.met is False
    assert condition_4.subjects == ()


# =========================================================================== #
# Adversarial case: uncatalogued-detector-path-fails-condition-3.
# =========================================================================== #


def test_uncatalogued_detector_path_fails_condition_3(monkeypatch, cached_catalogue):
    import segfacet.traceability as traceability
    from segfacet.heuristics.rule import ConsumedPath, RuleDetector, iter_rules

    fragmentation_rule = next(r for r in iter_rules() if r.rule_id == "fragmentation")
    bogus_path = "per_label.{label}.components.zzz_uncatalogued_165"
    new_detectors = tuple(
        dc.replace(detector, signal_paths=detector.signal_paths + (bogus_path,))
        if detector.detector_id == "islands"
        else detector
        for detector in fragmentation_rule.mode_declaration.detectors
    )
    # item 164's cross-validation requires every signal_paths element to be
    # the path of a role=='signal' ConsumedPath in the same declaration, so
    # widening the detector alone raises before bar_conditions() is ever
    # reached. Add a matching ConsumedPath -- ascending by path, alongside
    # the existing entries -- to keep the declaration internally valid. The
    # bogus path still names no catalogue entry, so build_catalogue(strict=
    # True) does not cover it and condition 3 must still report it unmet.
    new_consumed_paths = tuple(
        sorted(
            fragmentation_rule.mode_declaration.consumed_paths
            + (ConsumedPath(path=bogus_path, role="signal"),),
            key=lambda cp: cp.path,
        )
    )
    new_declaration = dc.replace(
        fragmentation_rule.mode_declaration,
        consumed_paths=new_consumed_paths,
        detectors=new_detectors,
    )
    monkeypatch.setattr(fragmentation_rule, "mode_declaration", new_declaration)

    result = traceability.bar_conditions(4, catalogue=cached_catalogue)
    condition_3 = _record(result, 3)
    assert condition_3.met is False
    assert bogus_path in condition_3.subjects


# =========================================================================== #
# Adversarial case: co-detection-alone-fails-condition-2.
# =========================================================================== #


def test_co_detection_alone_fails_condition_2(monkeypatch, cached_catalogue):
    import segfacet.failure_modes as failure_modes
    import segfacet.traceability as traceability

    original = failure_modes.SPECIFICATION
    mode4 = original[4]
    patched_mode4 = dc.replace(
        mode4,
        intended_rules=tuple(edge for edge in mode4.intended_rules if edge.rule_id != "fragmentation"),
    )
    patched = dict(original)
    patched[4] = patched_mode4
    monkeypatch.setattr(failure_modes, "SPECIFICATION", patched)

    # The fixture still agrees -- fragmentation still fires, just no longer
    # named among mode 4's own intended_rules.
    assert any(failure_modes.case_agrees(case) for case in patched_mode4.corpus_cases)

    result = traceability.bar_conditions(4, catalogue=cached_catalogue)
    condition_2 = _record(result, 2)
    assert condition_2.met is False


# =========================================================================== #
# Adversarial case: unknown-mode-id-raises.
# =========================================================================== #


def test_unknown_mode_id_raises(cached_catalogue):
    import segfacet.traceability as traceability

    with pytest.raises(KeyError):
        traceability.bar_conditions(99, catalogue=cached_catalogue)
