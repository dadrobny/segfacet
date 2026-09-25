"""Tests for item 182 -- the corpus-derived rule->mode map read from the
committed cases, replacing the AST scan of ``synth/*.py``'s ``Expectation(...)``
literals.

Covers Acceptance Criteria AC1-AC6:

- AC1: ``catalogue.scan_synth_rule_mode_map()`` equals the dict recomputed
  live from ``segfacet.synth.corpus.load_manifest()``'s failure-kind cases.
- AC2: dropping a committed case's only expected rule removes that
  ``(rule_id, mode)`` pair.
- AC3: an ``Expectation`` literal in synth source that no committed case
  applies adds no pair -- the map no longer reads synth source at all.
- AC4: the same planted literal (the shape of ``fuse``'s pre-item-176
  unbridged literal) causes no ``rule_declaration_conflicts`` entry.
- AC5: ``rule_declaration_conflicts`` reads the manifest-derived map -- an
  appended failure-kind case designates a conflict.
- AC6: ``build_catalogue``'s mechanism C reads the manifest-derived map --
  emptying every case's ``expected_rule_ids`` drops ``"rule_mode_map"``
  evidence everywhere.

Adversarial case named by the spec's Testing Strategy:

- ``missing-kind-raises``: a planted case with no ``kind`` key (but carrying
  ``expected_rule_ids``) makes ``scan_synth_rule_mode_map()`` raise
  ``ValueError`` naming that case's id (A3's malformed-case guard).
"""

from __future__ import annotations

import ast
import copy
from collections import defaultdict

import pytest

import segfacet.catalogue as catalogue_module
import segfacet.failure_modes as failure_modes_module
from segfacet.heuristics.rule import iter_rule_declarations
from segfacet.synth import corpus as corpus_module
from segfacet.synth.perturbation import CASE_KIND_FAILURE, corpus_case_kind

_FUSE_LITERAL_SOURCE = (
    "from segfacet.synth.perturbation import Expectation\n"
    "\n"
    "_PLANTED = Expectation(\n"
    "    failure_mode=2,\n"
    "    expected_rule_ids=frozenset({'coverage', 'fragmentation'}),\n"
    ")\n"
)


def _expected_rule_mode_map(cases):
    """Recompute the AC1 map straight from manifest cases: every failure-kind
    case's ``expected_rule_ids``, each mapped to the sorted tuple of distinct
    ``failure_mode`` values across the cases that designate it."""
    accum: dict = defaultdict(set)
    for case in cases:
        if corpus_case_kind(case) != CASE_KIND_FAILURE:
            continue
        for rule_id in case.get("expected_rule_ids", ()):
            accum[rule_id].add(case["failure_mode"])
    return {rule_id: tuple(sorted(modes)) for rule_id, modes in accum.items()}


def _plant_fuse_literal(tmp_path, monkeypatch):
    """Plant a temporary ``segfacet.synth``-shaped directory holding a module
    with the unbridged ``fuse`` literal shape, and point
    ``segfacet.synth.__file__`` at it."""
    import segfacet.synth as synth_pkg

    (tmp_path / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "fake_fuse.py").write_text(_FUSE_LITERAL_SOURCE, encoding="utf-8")
    monkeypatch.setattr(synth_pkg, "__file__", str(tmp_path / "__init__.py"))


def test_ac1_map_equals_committed_manifest_recomputation():
    manifest = corpus_module.load_manifest()
    expected = _expected_rule_mode_map(manifest["cases"])

    assert catalogue_module.scan_synth_rule_mode_map() == expected


def test_ac2_dropping_only_designating_case_removes_pair(monkeypatch):
    committed = corpus_module.load_manifest()

    # (rule_id, mode) -> the case_ids of the failure cases that designate it.
    contributors: dict = defaultdict(list)
    for case in committed["cases"]:
        if corpus_case_kind(case) != CASE_KIND_FAILURE:
            continue
        for rule_id in case.get("expected_rule_ids", ()):
            contributors[(rule_id, case["failure_mode"])].append(case["case_id"])

    singly_designated = sorted(
        pair for pair, case_ids in contributors.items() if len(case_ids) == 1
    )
    assert singly_designated, (
        "need at least one (rule_id, mode) pair the committed manifest "
        "designates from exactly one failure case"
    )
    rule_id, mode = singly_designated[0]
    target_case_id = contributors[(rule_id, mode)][0]

    patched = copy.deepcopy(committed)
    for case in patched["cases"]:
        if case["case_id"] == target_case_id:
            case["expected_rule_ids"] = [
                r for r in case["expected_rule_ids"] if r != rule_id
            ]

    monkeypatch.setattr(corpus_module, "load_manifest", lambda *a, **k: patched)

    assert mode not in catalogue_module.scan_synth_rule_mode_map().get(rule_id, ())


def test_ac3_unbridged_expectation_literal_adds_no_pair(tmp_path, monkeypatch):
    # Premise check: the planted file really does contain an Expectation(...)
    # call carrying a literal failure_mode=2 and a literal frozenset of the
    # two rule ids -- the shape fuse's pre-item-176 unbridged literal had.
    tree = ast.parse(_FUSE_LITERAL_SOURCE)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Expectation"
    ]
    assert len(calls) == 1
    keywords = {kw.arg: kw.value for kw in calls[0].keywords}
    assert isinstance(keywords["failure_mode"], ast.Constant)
    assert keywords["failure_mode"].value == 2
    assert isinstance(keywords["expected_rule_ids"], ast.Call)
    assert keywords["expected_rule_ids"].func.id == "frozenset"
    elts = keywords["expected_rule_ids"].args[0].elts
    assert {elt.value for elt in elts} == {"coverage", "fragmentation"}

    _plant_fuse_literal(tmp_path, monkeypatch)

    committed = corpus_module.load_manifest()
    expected = _expected_rule_mode_map(committed["cases"])
    assert catalogue_module.scan_synth_rule_mode_map() == expected


def test_ac4_planted_fuse_literal_causes_no_conflict(tmp_path, monkeypatch):
    baseline = catalogue_module.rule_declaration_conflicts()

    _plant_fuse_literal(tmp_path, monkeypatch)

    assert catalogue_module.rule_declaration_conflicts() == baseline


def test_ac5_conflicts_reads_manifest_derived_map(monkeypatch):
    declarations = dict(iter_rule_declarations())
    specification = failure_modes_module.SPECIFICATION

    chosen = None
    for rule_id, decl in sorted(declarations.items()):
        if decl is None:
            continue
        declared_modes = set(decl.modes)
        for mode_id, mode_spec in sorted(specification.items()):
            if mode_id in declared_modes:
                continue
            if any(
                rule_id in case.expected_firing for case in mode_spec.corpus_cases
            ):
                continue
            chosen = (rule_id, mode_id)
            break
        if chosen is not None:
            break

    assert chosen is not None, (
        "need a registered, declared rule and a SPECIFICATION mode it "
        "neither declares nor co-detects in any of that mode's corpus_cases"
    )
    rule_id, mode_id = chosen

    committed = corpus_module.load_manifest()
    patched = copy.deepcopy(committed)
    patched["cases"].append(
        {
            "case_id": "planted-ac5-case",
            "kind": CASE_KIND_FAILURE,
            "failure_mode": mode_id,
            "expected_rule_ids": [rule_id],
        }
    )
    monkeypatch.setattr(corpus_module, "load_manifest", lambda *a, **k: patched)

    messages = catalogue_module.rule_declaration_conflicts()
    assert any(
        repr(rule_id) in message and f"corpus designates failure mode {mode_id}" in message
        for message in messages
    )


def test_ac6_build_catalogue_reads_manifest_derived_map(monkeypatch):
    committed = corpus_module.load_manifest()
    patched = copy.deepcopy(committed)
    for case in patched["cases"]:
        case["expected_rule_ids"] = []
    monkeypatch.setattr(corpus_module, "load_manifest", lambda *a, **k: patched)

    result = catalogue_module.build_catalogue(strict=True)

    assert result.entries
    assert all("rule_mode_map" not in entry.mode_evidence for entry in result.entries)


def test_missing_kind_raises(monkeypatch):
    committed = corpus_module.load_manifest()
    patched = copy.deepcopy(committed)
    patched["cases"].append(
        {
            "case_id": "planted-missing-kind",
            "failure_mode": 1,
            "expected_rule_ids": ["mislabel"],
        }
    )
    monkeypatch.setattr(corpus_module, "load_manifest", lambda *a, **k: patched)

    with pytest.raises(ValueError, match="planted-missing-kind"):
        catalogue_module.scan_synth_rule_mode_map()
