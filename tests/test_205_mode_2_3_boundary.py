"""Tests for item 205 -- the mode 2/3 boundary re-drawn: the paired case
(``split``, decided by ``neighbour_contact``'s ``stray_contact``) belongs to
mode 2 alone, and mode 3 keeps ``split_own_label`` as its only corpus case.

One test per Acceptance Criterion (AC1-AC3), each recomputed live from
``segfacet.failure_modes``.
"""

from __future__ import annotations

import segfacet.failure_modes as fm


def test_ac1_split_is_attributed_to_mode_2_alone():
    carrying = {
        mode_id
        for mode_id, spec in fm.SPECIFICATION.items()
        if any(c.case_id == "split" for c in spec.corpus_cases)
    }
    assert carrying == {2}


def test_ac2_stray_contact_serves_mode_2_alone():
    assert fm.modes_for_detector("neighbour_contact", "stray_contact") == (2,)


def test_ac3_mode_3_only_corpus_case_is_split_own_label():
    assert {c.case_id for c in fm.SPECIFICATION[3].corpus_cases} == {
        "split_own_label"
    }
