"""Tests for item 200 -- the bar checker's condition 2
(``segfacet.traceability.bar_conditions``) made existential and
detector-granular, built on the new public
``segfacet.failure_modes.measured_detector_firing``.

One test per Acceptance Criterion (AC1-AC5) plus the one adversarial case the
Testing Strategy names, ``expressing-case-that-disagrees-is-not-a-subject``.
One module-scoped fixture builds ``build_catalogue(strict=True)`` once; every
``bar_conditions`` call passes it.
"""

from __future__ import annotations

import dataclasses as dc

import pytest


@pytest.fixture(scope="module")
def cat():
    from segfacet.catalogue import build_catalogue

    return build_catalogue(strict=True)


def _c2(mode_id, cat):
    import segfacet.traceability as traceability

    matches = [r for r in traceability.bar_conditions(mode_id, catalogue=cat) if r.number == 2]
    assert len(matches) == 1
    return matches[0]


def _case(mode_id, case_id):
    import segfacet.failure_modes as fm

    matches = [c for c in fm.SPECIFICATION[mode_id].corpus_cases if c.case_id == case_id]
    assert len(matches) == 1
    return matches[0]


def _own(mode_id):
    import segfacet.failure_modes as fm

    return {
        (e.rule_id, d)
        for e in fm.SPECIFICATION[mode_id].intended_rules
        for d in e.detector_ids
    }


def _findings(case):
    """Findings of *case* through the regression helper its manifest entry's
    ``detection`` names."""
    from segfacet.synth import regression
    from segfacet.synth.corpus import load_manifest
    from segfacet.synth.intensity import load_intensity_manifest

    manifest = load_manifest() if case.corpus == "geometric" else load_intensity_manifest()
    entries = [c for c in manifest["cases"] if c["case_id"] == case.case_id]
    assert len(entries) == 1
    helper = {
        "pipeline": regression.pipeline_findings,
        "reconstructed_record": regression.reconstructed_findings,
        "intensity_pipeline": regression.intensity_pipeline_findings,
    }[entries[0]["detection"]]
    return helper(entries[0])


def _patch_mode_4(monkeypatch, cases):
    import segfacet.failure_modes as fm

    patched = dict(fm.SPECIFICATION)
    patched[4] = dc.replace(fm.SPECIFICATION[4], corpus_cases=cases)
    monkeypatch.setattr(fm, "SPECIFICATION", patched)


def test_ac1_measured_detector_firing_returns_measured_pairs():
    import segfacet.failure_modes as fm

    checked = 0
    for mode_id in (3, 4, 16):
        for case in fm.SPECIFICATION[mode_id].corpus_cases:
            expected = tuple(sorted({(f.rule_id, f.detector_id) for f in _findings(case)}))
            assert fm.measured_detector_firing(case) == expected
            checked += 1
    assert checked


def test_ac2_condition_2_is_existential(monkeypatch, cat):
    isl = _case(4, "inject_islands")
    frag = _case(1, "fragment")
    _patch_mode_4(monkeypatch, (isl, dc.replace(frag, expected_firing=())))

    assert _c2(4, cat).met is True


def test_ac3_other_modes_detector_case_is_not_a_subject(monkeypatch, cat):
    import segfacet.failure_modes as fm

    isl = _case(4, "inject_islands")
    frag = _case(1, "fragment")
    # Preconditions from the primary source, so the test cannot pass vacuously.
    assert fm.case_agrees(frag)
    assert set(fm.measured_firing(frag)) & {e.rule_id for e in fm.SPECIFICATION[4].intended_rules}
    assert not _own(4) & set(fm.measured_detector_firing(frag))

    _patch_mode_4(monkeypatch, (isl, frag))

    assert _c2(4, cat).subjects == ("inject_islands",)


def test_ac4_other_modes_detector_case_alone_does_not_meet(monkeypatch, cat):
    import segfacet.failure_modes as fm

    frag = _case(1, "fragment")
    assert fm.case_agrees(frag)
    assert set(fm.measured_firing(frag)) & {e.rule_id for e in fm.SPECIFICATION[4].intended_rules}
    assert not _own(4) & set(fm.measured_detector_firing(frag))

    _patch_mode_4(monkeypatch, (frag,))

    assert _c2(4, cat).met is False


def test_ac5_condition_2_equals_live_recomputation_for_every_mode(cat):
    import segfacet.failure_modes as fm

    assert fm.SPECIFICATION
    for m, mode in fm.SPECIFICATION.items():
        own = _own(m)
        expected = tuple(
            c.case_id
            for c in mode.corpus_cases
            if fm.case_agrees(c) and own & set(fm.measured_detector_firing(c))
        )
        record = _c2(m, cat)
        assert record.subjects == expected, m
        assert record.met == bool(record.subjects), m


def test_expressing_case_that_disagrees_is_not_a_subject(monkeypatch, cat):
    isl = _case(4, "inject_islands")
    _patch_mode_4(monkeypatch, (dc.replace(isl, expected_firing=()),))

    record = _c2(4, cat)
    assert record.met is False
    assert record.subjects == ()
