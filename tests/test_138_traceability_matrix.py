"""Tests for item 138 -- the generated failure-mode <-> rule <-> feature
traceability matrix (``segfacet.traceability`` and its two committed
artifacts, ``docs/aide/traceability_matrix.generated.{json,md}``).

Covers Acceptance Criteria AC1-AC33 (AC12/AC15/AC24/AC31 parametrised over
the catalogue's modes, AC18/AC23 over the ten registered rules), plus adversarial
coverage for the three fail-loudly directions (AC25-AC27), a stale rung, a
stale mechanism, a re-narrowed ``reference_delta`` declaration (AC32), a
mode-to-rule hole, and edge cases for a singleton-rule mode and a
zero-feature rule.

This module reads the corrected spec (docs/aide/items/138-...md, including
its "Correction (2026-09-02, before implementation)" Decisions entry):
``reference_delta`` declares modes ``(1, 2)``, mode 1's rule list therefore
contains both ``mislabel`` and ``reference_delta``, and the analytic edge set
is three edges over two rules -- ``(1, reference_delta)``, ``(2, bounds)``,
``(2, reference_delta)`` -- not the pre-correction two-edge shape.

Reconciled (item 150, 2026-09-14) to the maintainer-signed-off taxonomy. The
catalogue is sixteen modes plus one condition (ten at the 2026-09-14 pass;
the 2026-09-15 revision split every paired sub-mode), the ids are re-assigned, and
``vision.md`` §6's eight titles are provenance (``VISION_SEED_DISPOSITION``)
rather than the id-bearing list -- so the mode roll call is derived from
``failure_modes.SPECIFICATION`` (``MODES``) instead of ``range(1, 9)``, mode
titles are ground-truthed against the hand-transcribed
``SIGNED_OFF_MODE_TITLES``, and the ``proposed`` modes (``PROPOSED_MODES``,
derived; seven since the 2026-09-15 revision) carry a ``None`` derived rung -- legal for them alone, rendered
``(none)`` in the Markdown. Four further consequences are recorded on the
tests that carry them: attribution is per-edge, not per-rule (on the 2026-09-14
sign-off ``coverage`` mixed an analytic and a corpus edge); a mechanism may name a
co-detecting rule's path (modes 1 and 2 are authored to say exactly that); no
shipped mechanism uses the ``(measured: findings == [...])`` idiom any more,
so that checker is exercised against a live measurement instead of a shipped
sentence; and dates now appear in authored prose, so AC28 requires every date
in an artifact to be findable in the authored source rather than banning
dates outright.

AC31 -- no character-count threshold, and no shape-only substitute for it
either. Item 137's own defect (recorded in ``docs/aide/insights.md``,
2026-09-02) was a mechanism sentence held to a character floor rather than
to its content; item 138 repeated the same failure shape one level up
(0db0fca, 2026-09-03): four of eight authored mechanism sentences were
false despite each naming a token that resolves against live state (a code
review, not this suite, caught them), because token-presence alone proves
only that the token exists, never that the claim built around it is true.
This module now checks, beyond mere resolvability: (1) a mechanism naming a
feature path is verified against the catalogue's own ``consuming_rules``
derivation for the mode's *declared* rule(s), never against
``MODE_ANCHOR_PATHS`` (``test_ac31_named_feature_path_is_consumed_by_one_of_
the_modes_declared_rules``); (2) a mechanism carrying the machine-checkable
``(measured: findings == [...])`` idiom the fix introduced is verified
against a fresh ``run_qc`` over the named corpus case, via the same public
harness ``tests/test_041_regression_suite.py`` drives
(``test_ac31_measured_findings_claim_matches_the_live_pipeline_firing_set``).
Both are demonstrated adversarially against the two defects they would have
caught (modes 4 and 1/2 respectively); modes 5 and 6's pre-fix defects named
a real, genuinely-consumed sibling path of the correctly-named rule, a
distinction neither check -- nor anything else this codebase can measure --
can decide, so that part is deliberately left unasserted rather than faked.
A dedicated test (``test_ac31_no_character_count_threshold_assertions``)
inspects this module's own source to confirm no length-threshold floor (any
operand order, any of ``==``/``>=``/``<=``/``>``/``<``) crept back in for
any of these prose fields. A separate adversarial test reproduces 0db0fca's
other fix: a rule declaring only a mode outside ``MODE_ANCHOR_PATHS``' key
set must make ``rule_to_mode`` report a hole, not ``complete: true``.

Field-name note: the item spec pins the JSON's *content* precisely (per-AC)
but leaves several container shapes unstated (e.g. whether ``modes``/
``rules`` are JSON objects keyed by mode/rule-id, or lists of records). This
module's ``_mode_records``/``_rule_records`` helpers accept either shape;
the field *names* it reads (``rung``, ``mechanism``, ``rules``,
``rule_attribution``, ``pipeline_detected``, ``cases``, ``anchor_paths``,
``read_paths``, ``granularity``, ``modes``, ``declaration_state``,
``mode_less_reason``, ``read_paths_qualifier``) are this test module's own
executable statement of the contract, derived from the spec's prose and
Implementation Steps.

Reconciled (item 149, 2026-09-04): the mode record's conflated
``feature_paths`` field (anchors unioned with every leaf path every
declaring rule consumed, regardless of classification) is retired --
``anchor_paths`` and ``read_paths`` are now two separate, separately
labelled fields, and ``granularity`` moves from ``"rule"`` to ``"signal"``.
The rule-level record's own ``feature_paths`` field (a rule's full
catalogue-derived consumption set, AC23) is unaffected -- item 149 touches
only the mode record's conflated union, not the rule record.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent

RUNGS = ("synthetic-demonstrable", "needs-real-data", "structurally-unobservable")


def _specification_mode_ids():
    """The signed-off catalogue's mode ids, live.

    Reconciled (item 150, 2026-09-14): ``MODES`` was ``range(1, 9)`` -- vision
    .md §6's eight hypothesised modes, which were also the ids. The sign-off
    made §6 provenance and moved the id-bearing catalogue to
    ``segfacet.failure_modes.SPECIFICATION``, so the roll call is derived from
    it rather than re-hardcoded at a new number. Importing the module at
    collection time is cheap by its own determinism contract (every NumPy /
    SciPy / NiBabel import is deferred into a function body)."""
    import segfacet.failure_modes as failure_modes_module

    return tuple(sorted(failure_modes_module.SPECIFICATION))


def _proposed_mode_ids():
    """The live-derived ``proposed`` modes -- the ones with no declaring rule,
    no corpus case, and therefore (item 150) a ``None`` derived rung."""
    import segfacet.failure_modes as failure_modes_module

    return frozenset(
        mode_id
        for mode_id, spec in failure_modes_module.SPECIFICATION.items()
        if failure_modes_module.derive_status(spec) == "proposed"
    )


MODES = _specification_mode_ids()
PROPOSED_MODES = _proposed_mode_ids()

#: The mode used by the "named anchor path is not consumed by any declared
#: rule" adversarial pair (fixture + test). Mode 8 (semantic mislabelling)
#: after the item-150 sign-off's 2026-09-15 revision; see
#: ``matrix_anchor_not_consumed_bogus_mechanism``. The test asserts the
#: fixture assumption (anchor present, declared rules do not consume it) rather
#: than trusting this constant.
_ANCHOR_NOT_CONSUMED_MODE = 8

#: "Overlapping segments" -- mode 15 after the item-150 sign-off's 2026-09-15
#: revision (it was 8 before item 150, 9 at the 2026-09-14 pass). Its one
#: corpus case keeps the historical id ``mode8_force_overlap``.
_OVERLAP_MODE = 15
RULE_IDS = (
    "border",
    "bounds",
    "coverage",
    "fragmentation",
    "intensity",
    "intensity_reference_delta",
    "mislabel",
    "overlap",
    "reference_delta",
    "sequence",
)

_COMMITTED_JSON = _REPO_ROOT / "docs" / "aide" / "traceability_matrix.generated.json"
_COMMITTED_MD = _REPO_ROOT / "docs" / "aide" / "traceability_matrix.generated.md"

#: AC28/AC29 (item 149, 2026-09-04): every ``build_matrix()`` call site in
#: this module must sit lexically inside a function decorated
#: ``@pytest.fixture`` -- see the "House fixtures / helpers" section below --
#: and the AST-counted total must equal this constant and be ``<= 20``
#: (down from the 47 uncached call sites measured at this item's base). The
#: budget is asserted by ``test_ac28_ac29_...`` near the bottom of this
#: module.
_BUILD_MATRIX_CALL_SITE_BUDGET = 16


# =========================================================================== #
# House fixtures / helpers
# =========================================================================== #


@pytest.fixture
def isolated_registry():
    """Snapshot/restore the rule registry (house pattern from
    ``tests/test_026_rule_engine_core.py`` / ``test_136`` / ``test_137``), so
    a stub rule registered for an adversarial case cannot leak into another
    test."""
    from segfacet.heuristics.rule import _RULES

    snapshot = dict(_RULES)
    yield
    _RULES.clear()
    _RULES.update(snapshot)


def _mode_records(payload: dict) -> dict:
    """Normalise the JSON's ``modes`` direction to ``{mode_int: record}``,
    accepting either a dict keyed by mode (string or int) or a list of
    records each carrying a ``mode`` field."""
    modes = payload["modes"]
    if isinstance(modes, dict):
        return {int(k): v for k, v in modes.items()}
    return {int(r["mode"]): r for r in modes}


def _rule_records(payload: dict) -> dict:
    """Normalise the JSON's ``rules`` direction to ``{rule_id: record}``."""
    rules = payload["rules"]
    if isinstance(rules, dict):
        return dict(rules)
    return {r["rule_id"]: r for r in rules}


def _mode_record(payload: dict, mode: int) -> dict:
    records = _mode_records(payload)
    assert mode in records, (mode, sorted(records))
    return records[mode]


def _manifest_cases() -> list:
    payload = json.loads((_REPO_ROOT / "tests" / "corpus" / "manifest.json").read_text(encoding="utf-8"))
    cases = payload["cases"]
    assert cases, "expected a non-empty corpus manifest"
    return cases


def _manifest_detection_by_case_id() -> dict:
    return {c["case_id"]: c.get("detection") for c in _manifest_cases()}


# Reconciled (item 147, 2026-09-04): the local ``_vision_mode_titles()``
# parse is retired. Reconciled again (item 152): ``failure_modes.
# vision_seed_titles()`` is itself now retired -- the vision §6 parse has no
# live home. What survives is provenance only, frozen in
# ``failure_modes.VISION_SEED_DISPOSITION`` (spec A6); no module re-parses
# ``vision.md`` §6 at runtime.


def _token_in_mechanism(token: str, mechanism: str) -> bool:
    """Whole-token containment: ``token`` must appear in ``mechanism`` at a
    word boundary on both sides, so a one-character-off near-miss (e.g.
    ``mode8_force_overlaps`` for the real ``mode8_force_overlap``) does not
    count as a match."""
    return re.search(r"\b" + re.escape(token) + r"\b", mechanism) is not None


def _md_lines() -> list:
    text = _COMMITTED_MD.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines, "expected a non-empty committed markdown file"
    return lines


def _row_for_mode(lines: list, mode: int):
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0] == str(mode):
            return line
    return None


def _row_for_rule(lines: list, rule_id: str):
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0] == rule_id:
            return line
    return None


def _patch_specification_mode(monkeypatch, failure_modes_module, mode: int, **replacements):
    """Reconciled (item 147, 2026-09-04): ``MODE_RUNGS`` is retired --
    the matrix's per-mode rung and mechanism now come from
    ``failure_modes.SPECIFICATION``. Replace ``SPECIFICATION[mode]`` with a
    ``dataclasses.replace`` of its current entry carrying *replacements*,
    via ``monkeypatch.setattr`` on the whole mapping (never a container
    mutation) so ``build_matrix``'s live read picks it up regardless of
    ``MappingProxyType`` immutability."""
    original_map = failure_modes_module.SPECIFICATION
    original_entry = original_map[mode]
    patched_map = dict(original_map)
    patched_map[mode] = dataclasses.replace(original_entry, **replacements)
    monkeypatch.setattr(failure_modes_module, "SPECIFICATION", patched_map)


def _patch_derive_mode_rung(monkeypatch, failure_modes_module, mode: int, rung):
    """Override ``derive_mode_rung()``'s return for *mode* only.

    Used where the old ``_patch_mode_rungs`` helper injected an
    out-of-vocabulary rung string directly: ``ModeSpec`` validates every
    ``IntendedRule.evidence_rung`` against the closed ``EVIDENCE_RUNGS``
    vocabulary at construction (including inside ``dataclasses.replace``,
    which re-runs ``__post_init__``), so an invalid rung can only be
    injected by patching the derivation function itself."""
    original = failure_modes_module.derive_mode_rung

    def _patched(mode_spec):
        if mode_spec.id == mode:
            return rung
        return original(mode_spec)

    monkeypatch.setattr(failure_modes_module, "derive_mode_rung", _patched)


# =========================================================================== #
# build_matrix() call-site fixtures (item 149 AC28/AC29): one module-scoped
# unpatched fixture, and one function-scoped fixture per monkeypatch group.
# No ``build_matrix()`` call appears in a test body anywhere in this module
# -- every call site below sits inside a function decorated
# ``@pytest.fixture``. Never a cache inside the generator itself (AC30) --
# each adversarial fixture below calls ``build_matrix()`` fresh.
# =========================================================================== #


@pytest.fixture(scope="module")
def raw_matrix():
    """One unpatched ``build_matrix()`` call, shared module-wide."""
    import segfacet.traceability as traceability

    return traceability.build_matrix()


@pytest.fixture(scope="module")
def matrix(raw_matrix):
    """``matrix_to_dict()`` of the shared unpatched build -- no additional
    ``build_matrix()`` call site (``matrix_to_dict`` never calls it)."""
    import segfacet.traceability as traceability

    return traceability.matrix_to_dict(raw_matrix)


@pytest.fixture
def matrix_overlap_mode_rung_stale(monkeypatch):
    import segfacet.failure_modes as failure_modes_module
    import segfacet.traceability as traceability

    _patch_derive_mode_rung(monkeypatch, failure_modes_module, _OVERLAP_MODE, "not-a-real-rung")
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_overlap_mode_rung_synthetic(monkeypatch):
    import segfacet.failure_modes as failure_modes_module
    import segfacet.traceability as traceability

    _patch_derive_mode_rung(
        monkeypatch, failure_modes_module, _OVERLAP_MODE, "synthetic-demonstrable"
    )
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_unregistered_designated_rule(monkeypatch):
    """Reconciled (item 156, 2026-09-16): after item 156's Step 3,
    ``build_matrix()`` no longer reads ``scan_synth_rule_mode_map()`` for
    ``corpus_designated_unregistered_rule_ids`` -- it derives that field from
    the two committed manifests directly. Patching the scan here would leave
    this fixture silently inert. Re-pointed to
    ``segfacet.synth.corpus.load_manifest``: a deep copy that appends
    ``"boundary"`` to one failure case's ``expected_rule_ids``, picked by
    ``synth.perturbation.corpus_case_kind`` (item 155) rather than by case id,
    since item 157 renames corpus case ids."""
    import copy

    import segfacet.synth.corpus as corpus_module
    import segfacet.synth.perturbation as perturbation_module
    import segfacet.traceability as traceability

    real_manifest = corpus_module.load_manifest()
    patched = copy.deepcopy(real_manifest)
    for case in patched.get("cases", []):
        if perturbation_module.corpus_case_kind(case) == perturbation_module.CASE_KIND_FAILURE:
            case["expected_rule_ids"].append("boundary")
            break
    else:
        raise AssertionError(
            "matrix_unregistered_designated_rule: no failure case found in the "
            "geometric manifest to append 'boundary' to."
        )

    monkeypatch.setattr(corpus_module, "load_manifest", lambda *a, **k: patched)
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_overlap_mode_less(monkeypatch):
    from segfacet.heuristics.rule import _RULES
    import segfacet.heuristics.rule as rule_mod
    import segfacet.traceability as traceability

    rule = _RULES["overlap"]
    replacement = rule_mod.RuleModeDeclaration(
        mode_less_reason="AC138-adversarial: overlap-mode hole test, overlap made mode-less"
    )
    monkeypatch.setattr(rule, "mode_declaration", replacement)
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_undeclared_rule_registered(isolated_registry):
    from segfacet.heuristics.rule import Rule, register_rule
    import segfacet.traceability as traceability

    class _NoDeclarationRule(Rule):
        rule_id = "__item138_no_declaration__"

        def evaluate(self, record, config):
            return []

    register_rule(_NoDeclarationRule)  # must not raise
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def raw_matrix_bounds_bare_evidence(monkeypatch):
    """Reconciled (item 147, 2026-09-04): ``RuleModeDeclaration``'s
    ``__post_init__`` now rejects a bare-str ``evidence`` at construction, so
    the item-136 weakness this fixture reproduces can no longer be reached
    through normal construction. The defence-in-depth coverage stays: force
    the malformed value past ``__post_init__`` with ``object.__setattr__``
    (the frozen dataclass's own escape hatch) so
    ``traceability._normalise_evidence``'s own guard against a bare str
    stays exercised. Returns the **raw** (non-dict) matrix, for
    ``render_markdown``."""
    from segfacet.heuristics.rule import _RULES
    import segfacet.heuristics.rule as rule_mod
    import segfacet.traceability as traceability

    rule = _RULES["bounds"]
    replacement = rule_mod.RuleModeDeclaration(modes=(2,), evidence=("placeholder",))
    object.__setattr__(replacement, "evidence", "corpus-derived")
    monkeypatch.setattr(rule, "mode_declaration", replacement)
    return traceability.build_matrix()


@pytest.fixture
def matrix_bounds_mistagged_evidence(monkeypatch):
    from segfacet.heuristics.rule import _RULES
    import segfacet.heuristics.rule as rule_mod
    import segfacet.traceability as traceability

    rule = _RULES["bounds"]
    replacement = rule_mod.RuleModeDeclaration(modes=(2,), evidence=("mistagged-note",))
    monkeypatch.setattr(rule, "mode_declaration", replacement)
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_overlap_mode_bogus_mechanism(monkeypatch):
    import segfacet.failure_modes as failure_modes_module
    import segfacet.traceability as traceability

    bogus_mechanism = (
        "This sentence is deliberately long and describes nothing that "
        "lives in the codebase or the corpus at all, on purpose, for a test."
    )
    _patch_specification_mode(
        monkeypatch, failure_modes_module, _OVERLAP_MODE, mechanism=bogus_mechanism
    )
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_overlap_mode_typo_mechanism(monkeypatch):
    import segfacet.failure_modes as failure_modes_module
    import segfacet.traceability as traceability

    typo_mechanism = (
        "The mechanism names mode8_force_overlaps, one character off the "
        "real case id, on purpose, for a test."
    )
    _patch_specification_mode(
        monkeypatch, failure_modes_module, _OVERLAP_MODE, mechanism=typo_mechanism
    )
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_anchor_not_consumed_bogus_mechanism(monkeypatch, matrix):
    """Reproduces the pre-fix mode-4 defect: names the mode's own anchor
    path (which none of its declared rules consumes) from ``matrix``'s
    already-built record, then re-derives with the mechanism patched to name
    it.

    Re-pointed (item 150, 2026-09-14) from the old mode 4 to mode 5, and
    again (2026-09-15) to mode 8. The defect's shape needs a mode whose
    anchor path its declared rules do not consume, and the sign-off moved
    exactly that configuration: the anchor
    ``stage3.monotonic_consistency.is_monotonic`` belongs to semantic
    mislabelling (mode 8 since the 2026-09-15 revision), whose only declared
    rule is ``reference_delta``, which never reads it. The old mode 4 no
    longer exhibits it -- its anchor ``relationships.present_levels[]`` (now
    mode 6's) is genuinely consumed by ``coverage``."""
    import segfacet.failure_modes as failure_modes_module
    import segfacet.traceability as traceability

    before = _mode_record(matrix, _ANCHOR_NOT_CONSUMED_MODE)
    bogus_path = before["anchor_paths"][0]
    bogus_mechanism = f"caught by reference_delta via {bogus_path}, on purpose, for a test."
    _patch_specification_mode(
        monkeypatch, failure_modes_module, _ANCHOR_NOT_CONSUMED_MODE, mechanism=bogus_mechanism
    )
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_uncatalogued_mode_rule_registered(isolated_registry):
    """Reconciled (item 146, 2026-09-03): the stub moves to a mode absent
    from both ``SPECIFICATION`` and ``MODE_ANCHOR_PATHS``, derived live
    rather than assumed by literal. Returns ``(d, uncatalogued_mode)``."""
    import segfacet.failure_modes as failure_modes_module
    import segfacet.feature_docs as feature_docs_module
    from segfacet.heuristics.rule import Rule, RuleModeDeclaration, register_rule
    import segfacet.traceability as traceability

    uncatalogued_mode = 1
    while (
        uncatalogued_mode in failure_modes_module.SPECIFICATION
        or uncatalogued_mode in feature_docs_module.MODE_ANCHOR_PATHS
    ):
        uncatalogued_mode += 1

    class _UncataloguedModeRule(Rule):
        rule_id = "__item138_uncatalogued_mode__"
        mode_declaration = RuleModeDeclaration(
            modes=(uncatalogued_mode,),
            evidence=("analytic", "AC-adjacent: this mode is outside the catalogue"),
        )

        def evaluate(self, record, config):
            return []

    register_rule(_UncataloguedModeRule)
    d = traceability.matrix_to_dict(traceability.build_matrix())
    return d, uncatalogued_mode


@pytest.fixture
def matrix_reference_delta_renarrowed(monkeypatch):
    from segfacet.heuristics.rule import _RULES
    import segfacet.heuristics.rule as rule_mod
    import segfacet.traceability as traceability

    rule = _RULES["reference_delta"]
    narrowed = rule_mod.RuleModeDeclaration(
        modes=(2,), evidence=("analytic", "AC32 adversarial: re-narrowed back to modes=(2,)")
    )
    monkeypatch.setattr(rule, "mode_declaration", narrowed)
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_zero_read_rule_registered(isolated_registry):
    from segfacet.heuristics.rule import Rule, RuleModeDeclaration, register_rule
    import segfacet.traceability as traceability

    class _ZeroReadRule(Rule):
        rule_id = "__item138_zero_read__"
        mode_declaration = RuleModeDeclaration(
            modes=(1,), evidence=("analytic", "AC-adjacent: consumes no catalogued path")
        )

        def evaluate(self, record, config):
            return []

    register_rule(_ZeroReadRule)
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def inertness_probe():
    """AC30's whole mechanism in one fixture: ``run_rules`` before and after
    two fresh, unpatched ``build_matrix()`` calls -- proving both inertness
    (the rule engine is unaffected) and determinism (the two builds agree)
    without either build call sitting in a test body."""
    from segfacet.config import bundled_default_config
    from segfacet.heuristics.runner import run_rules
    from segfacet.pipeline import extract_feature_record
    from segfacet.synth.clean_gt import build_clean_spine
    import segfacet.traceability as traceability

    config = bundled_default_config()
    clean = build_clean_spine()
    record = extract_feature_record(clean.seg_img, config)

    before = run_rules(record, config)
    matrix_one = traceability.build_matrix()
    d1 = traceability.matrix_to_dict(matrix_one)
    after = run_rules(record, config)
    matrix_two = traceability.build_matrix()
    d2 = traceability.matrix_to_dict(matrix_two)
    return before, after, d1, d2


# =========================================================================== #
# AC1: stable public surface
# =========================================================================== #


def test_ac1_public_surface_and_zero_argument_build_matrix(raw_matrix):
    import segfacet.traceability as traceability

    for name in ("build_matrix", "matrix_to_dict", "render_markdown", "main"):
        assert hasattr(traceability, name), name
        assert name in traceability.__all__, name
        assert callable(getattr(traceability, name)), name

    assert raw_matrix is not None


# =========================================================================== #
# AC2: zero-argument regeneration, and redirectable
# =========================================================================== #


def test_ac2_main_redirects_writes_and_leaves_committed_artifacts_unchanged(tmp_path):
    import segfacet.traceability as traceability

    before_json = _COMMITTED_JSON.read_bytes()
    before_md = _COMMITTED_MD.read_bytes()
    assert before_json, "expected a non-empty committed JSON artifact"
    assert before_md, "expected a non-empty committed markdown artifact"

    json_dest = tmp_path / "out.json"
    md_dest = tmp_path / "out.md"
    traceability.main(["--json", str(json_dest), "--md", str(md_dest)])

    assert json_dest.exists()
    assert md_dest.exists()

    after_json = _COMMITTED_JSON.read_bytes()
    after_md = _COMMITTED_MD.read_bytes()
    assert after_json == before_json
    assert after_md == before_md


def test_ac2_default_output_paths_are_the_committed_docs_aide_paths(monkeypatch):
    import segfacet.traceability as traceability

    calls = []

    def _fake_write_bytes(self, data):
        calls.append(self)
        return len(data)

    monkeypatch.setattr(Path, "write_bytes", _fake_write_bytes)
    traceability.main([])

    assert calls, "expected main() with no args to attempt at least one write"
    written = {p.as_posix() for p in calls}
    assert any(p.endswith("docs/aide/traceability_matrix.generated.json") for p in written), written
    assert any(p.endswith("docs/aide/traceability_matrix.generated.md") for p in written), written


# =========================================================================== #
# AC3: byte-reproducible run-to-run
# =========================================================================== #


def test_ac3_artifacts_are_byte_reproducible_run_to_run(tmp_path):
    import segfacet.traceability as traceability

    json_a, md_a = tmp_path / "a.json", tmp_path / "a.md"
    json_b, md_b = tmp_path / "b.json", tmp_path / "b.md"

    traceability.main(["--json", str(json_a), "--md", str(md_a)])
    traceability.main(["--json", str(json_b), "--md", str(md_b)])

    bytes_a_json, bytes_b_json = json_a.read_bytes(), json_b.read_bytes()
    bytes_a_md, bytes_b_md = md_a.read_bytes(), md_b.read_bytes()
    assert bytes_a_json, "expected non-empty JSON output"
    assert bytes_a_md, "expected non-empty markdown output"

    assert bytes_a_json == bytes_b_json
    assert bytes_a_md == bytes_b_md


# =========================================================================== #
# AC4: the committed JSON is a fresh build (parsed comparison, A7)
# =========================================================================== #


def test_ac4_committed_json_parses_to_a_fresh_build(matrix):
    committed_text = _COMMITTED_JSON.read_text(encoding="utf-8")
    committed_payload = json.loads(committed_text)
    assert committed_payload, "expected a non-empty committed JSON payload"

    normalised_fresh = json.loads(json.dumps(matrix, sort_keys=True))
    assert normalised_fresh == committed_payload


# =========================================================================== #
# AC5: the committed Markdown agrees with the committed JSON
# =========================================================================== #


def test_ac5_markdown_rows_agree_with_json_for_every_mode_and_rule():
    committed_payload = json.loads(_COMMITTED_JSON.read_text(encoding="utf-8"))
    lines = _md_lines()

    modes = _mode_records(committed_payload)
    assert modes, "expected at least one mode record in committed JSON"
    for mode, record in modes.items():
        row = _row_for_mode(lines, mode)
        assert row is not None, mode
        # Reconciled (item 146, 2026-09-04): a bare non-empty-rules
        # requirement pinned the pre-146 shape, where every catalogued mode
        # declared >=1 rule. Mode 10 (the first `proposed` entry) legitimately
        # declares none (AC27) -- completeness of the rules a mode *does*
        # carry is AC10's claim, not this row-agreement one, so this loop
        # only asserts what it is actually about: every rule the JSON lists
        # for a mode is also present in that mode's markdown row.
        for rule_id in record["rules"]:
            assert rule_id in row, (mode, rule_id)
        # Reconciled (item 147, 2026-09-04): an absent rung is `null` in the
        # JSON and `(none)` in the markdown -- mode 10, the first `proposed`
        # entry, has no edges to derive a rung from, and both serialisers now
        # say so explicitly rather than writing a blank indistinguishable
        # from a failed lookup (AC8). The agreement this test is about is
        # unchanged; only the pair of tokens it compares.
        assert (record["rung"] or "(none)") in row, mode

    rules = _rule_records(committed_payload)
    assert rules, "expected at least one rule record in committed JSON"
    for rule_id, record in rules.items():
        row = _row_for_rule(lines, rule_id)
        assert row is not None, rule_id
        for mode in record["modes"]:
            assert str(mode) in row, (rule_id, mode)
        assert record["declaration_state"] in row, rule_id


# =========================================================================== #
# AC6: LF bytes, one trailing newline
# =========================================================================== #


def test_ac6_both_artifacts_are_lf_bytes_with_one_trailing_newline():
    for path in (_COMMITTED_JSON, _COMMITTED_MD):
        data = path.read_bytes()
        assert data, path
        assert b"\r" not in data, path
        assert data.endswith(b"\n"), path
        assert not data.endswith(b"\n\n"), path


# =========================================================================== #
# AC7: .gitattributes pins both new paths eol=lf
# =========================================================================== #


def test_ac7_gitattributes_pins_both_new_paths_eol_lf():
    text = (_REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
    for rel_path in (
        "docs/aide/traceability_matrix.generated.json",
        "docs/aide/traceability_matrix.generated.md",
    ):
        pattern = re.compile(re.escape(rel_path) + r"[^\n]*eol=lf")
        assert pattern.search(text), rel_path


# =========================================================================== #
# AC8: the mode set is §6's, taken from code
# =========================================================================== #


def test_ac8_mode_set_equals_mode_anchor_paths_keys(matrix):
    """Reconciled (item 146, 2026-09-04): before this item, ``build_matrix``
    enumerated modes from ``feature_docs.MODE_ANCHOR_PATHS``' key set (then
    exactly the mode set), so the two were trivially equal. Item 146's
    round-2 fix moves the enumeration to ``failure_modes.SPECIFICATION``'s
    key set (1-10, ``feature_docs.py``'s Asserts-against entry) while
    ``MODE_ANCHOR_PATHS`` itself deliberately stays at 1-8. The live claim
    this test now makes is the correct superset relationship: the matrix's
    mode set equals the specification's keys, and every anchor-paths key is
    one of them."""
    import segfacet.failure_modes as failure_modes_module
    import segfacet.feature_docs as feature_docs_module

    d = matrix
    modes = _mode_records(d)
    assert modes, "expected at least one mode record"
    assert set(modes.keys()) == set(failure_modes_module.SPECIFICATION.keys())
    assert set(feature_docs_module.MODE_ANCHOR_PATHS.keys()) <= set(modes.keys())


# =========================================================================== #
# AC9: mode titles transcribed from vision.md §6
# =========================================================================== #

# Hand-transcribed from docs/aide/vision.md §6 "Segmentation Failure Modes"
# (lines 279-286 as of this writing), independently of any parser --
# ``failure_modes.vision_seed_titles()`` is retired (item 152); the v3 §6
# text survives only as frozen provenance in
# ``failure_modes.VISION_SEED_DISPOSITION`` (spec A6). Comparing these
# literals against that frozen copy still catches a hand-transcription slip
# on either side, since neither is derived from the other.
# These literals are the trailing-period-stripped,
# whitespace-normalised title text exactly as §6 states it, preserving its
# em dashes and arrows. If §6's wording changes, these must be updated by
# hand to match -- there is no automated way to keep them in sync.
VISION_SECTION_SIX_MODE_TITLES = {
    1: "Label not aligned with the anatomical vertebra it names",
    2: "Over-/under-segmentation — fused or fragmented vertebra segments",
    3: "Disconnected components / islands, especially tiny rogue segments",
    4: "Semantic mislabelling (wrong vertebra identification)",
    5: "Not all vertebrae in the image are segmented",
    6: "Partial vertebra at the image border whose appearance changes",
    7: "Non-continuous label sequence (e.g. L1 → T12 → L2 → L5)",
    8: "Overlapping segments",
}

#: Reconciled (item 150, 2026-09-14): the sign-off severed title from seed.
#: §6's numbered list above is provenance -- each title's fate is recorded in
#: ``failure_modes.VISION_SEED_DISPOSITION`` (one retired, one re-homed as the
#: ``fov_truncation`` condition, six re-pointed at re-assigned ids) -- and a
#: mode's title is its ``SPECIFICATION[id].name``. The hand-transcription
#: discipline the AC9 ground-truth check rests on moves with it: these are the
#: sixteen signed-off names (2026-09-15 revision: every paired sub-mode split
#: into single defects), typed out by hand from the "Taxonomy as signed off"
#: table in ``src/segfacet/failure_modes.py``'s module docstring, so that an
#: edit to a ``ModeSpec.name`` literal that is not mirrored in the docstring
#: table (or vice versa) fails here rather than flowing silently into both
#: committed artifacts. Do not derive this dict from ``SPECIFICATION`` -- that
#: is exactly the self-comparison this check exists to avoid.
SIGNED_OFF_MODE_TITLES = {
    1: "Segmentation accuracy (over-/under-segmentation)",
    2: "Fused vertebra segments",
    3: "Split vertebra segment",
    4: "Islands (disconnected components)",
    5: "Holes (enclosed background)",
    6: "Vertebra not segmented",
    7: "Hallucinated vertebra",
    8: "Semantic mislabelling (wrong vertebra identification)",
    9: "Out-of-order label sequence",
    10: "Skipped level label",
    11: "Unprompted numbering variant",
    12: "Shifted label sequence",
    13: "Collapsed labels",
    14: "Duplicated label",
    15: "Overlapping segments",
    16: "Implausible tissue under a label",
}


def test_ac9_mode_titles_match_the_hand_transcribed_vision_literals(matrix):
    """Independent ground truth: compares the built titles directly against
    literals transcribed by hand from vision.md §6, not against another
    parse of the same section -- this is the assertion that can actually
    catch a parser bug shared by the builder and this test module.

    Reconciled (item 146, 2026-09-04): rescoped to the eight seed modes,
    which is what this hand-transcribed-literals dict has ever covered --
    §6 was not and is not edited to add modes 9/10 (A13/A4: mode 9 is
    deliberately *not* one of §6's numbered eight, and mode 10 is the first
    `proposed` entry). Modes 9 and 10 entered through the specification
    instead, so their ground-truth name lives in
    ``failure_modes.SPECIFICATION[id].name``.

    Reconciled again (item 147, 2026-09-04): the matrix's title field now
    sources from ``SPECIFICATION[mode].name`` for every mode, including 9
    and 10, which render an empty title no longer -- asserted here as the
    live equality it now is, not the deliberate absence it used to be.

    Reconciled again (item 150, 2026-09-14): the sign-off severed title from
    §6 seed entirely, so the hand-transcribed ground truth moves to
    ``SIGNED_OFF_MODE_TITLES`` (transcribed from the taxonomy table in
    ``failure_modes``' module docstring, not from ``SPECIFICATION`` -- the
    point of this check is to be a second, independent copy). The §6 literals
    above are kept: they are what ``VISION_SEED_DISPOSITION`` is keyed by, and
    the live-document guard below still reads them."""
    d = matrix
    modes = _mode_records(d)
    assert modes
    assert set(modes) == set(SIGNED_OFF_MODE_TITLES), sorted(
        set(modes) ^ set(SIGNED_OFF_MODE_TITLES)
    )
    for mode, expected_title in SIGNED_OFF_MODE_TITLES.items():
        assert modes[mode]["title"] == expected_title, mode


def test_ac9_vision_section_six_titles_are_dispositioned_provenance(matrix):
    """Complementary derived check, re-targeted twice: first at the item-150
    sign-off (2026-09-14, §6 severed from the id-bearing catalogue), then at
    item 152 (2026-09-16), which retired ``failure_modes.vision_seed_titles()``
    and ``vision_seed_conflicts()`` -- vision.md v4 re-issues §6 as principles
    plus a pointer, with no numbered list left to parse. The live-document
    guard this test carries now compares two independent transcriptions of
    v3's §6 instead of a live parse: ``VISION_SECTION_SIX_MODE_TITLES`` above
    (this module's own hand transcription) against
    ``failure_modes.VISION_SEED_DISPOSITION`` (the frozen provenance map),
    and recomputes disposition resolution itself rather than calling the
    retired ``vision_seed_conflicts()``.

    The mode-title ground truth this test used to carry is
    ``SIGNED_OFF_MODE_TITLES`` above, asserted by
    ``test_ac9_mode_titles_match_the_hand_transcribed_vision_literals``."""
    import segfacet.failure_modes as failure_modes_module

    d = matrix
    modes = _mode_records(d)
    assert modes

    dispositions = failure_modes_module.VISION_SEED_DISPOSITION
    assert set(dispositions) == set(VISION_SECTION_SIX_MODE_TITLES.values()), (
        set(dispositions) ^ set(VISION_SECTION_SIX_MODE_TITLES.values())
    )

    seen = {"mode": 0, "condition": 0, "retired": 0}
    for seed_id, title in sorted(VISION_SECTION_SIX_MODE_TITLES.items()):
        assert title in dispositions, (seed_id, title)
        disposition = dispositions[title]
        kind, _sep, target = disposition.partition(":")
        if disposition == "retired":
            seen["retired"] += 1
            continue
        if kind == "mode":
            assert target.isdigit() and int(target) in modes, (seed_id, disposition)
            assert modes[int(target)]["title"], (seed_id, disposition)
            seen["mode"] += 1
        elif kind == "condition":
            assert target in failure_modes_module.CONDITIONS, (seed_id, disposition)
            seen["condition"] += 1
        else:
            raise AssertionError((seed_id, disposition))

    # All three dispositions are exercised on this tree, so none of the three
    # branches above can rot into dead code unnoticed.
    assert all(seen.values()), seen


# =========================================================================== #
# AC10: mode -> rule is complete and reported complete
# =========================================================================== #


def test_ac10_mode_to_rule_direction_complete_and_every_mode_has_a_rule(matrix):
    """Reconciled (item 146, 2026-09-04): mode 10 is the catalogue's first
    `proposed` entry -- listed, defined, deliberately unimplemented (AC27) --
    so it legitimately carries zero rules and is now the direction's one
    hole. Which mode(s) that is stays live-derived from
    ``failure_modes.derive_status`` (never hardcoded to "10" alone): every
    mode whose live-derived status is not "proposed" must still carry >=1
    rule, exactly as before."""
    import segfacet.failure_modes as failure_modes_module

    d = matrix
    modes = _mode_records(d)
    assert modes

    proposed_mode_ids = {
        str(mode_id)
        for mode_id, spec in failure_modes_module.SPECIFICATION.items()
        if failure_modes_module.derive_status(spec) == "proposed"
    }
    assert proposed_mode_ids, "expected >=1 live-derived proposed mode on this tree"

    for mode, record in modes.items():
        if str(mode) in proposed_mode_ids:
            assert record["rules"] == [], mode
        else:
            assert record["rules"], mode

    direction = d["directions"]["mode_to_rule"]
    assert direction["complete"] is False
    assert set(direction["holes"]) == proposed_mode_ids
    # Witness (item 150, 2026-09-15 revision): the sign-off's seven proposed
    # entries -- 5 holes, 7 hallucinated vertebra, 10 skipped level label
    # (label-only; a missed vertebra is mode 6), 11 unprompted numbering
    # variant, 12 shifted label sequence (needs an external classifier), 13
    # collapsed labels and 14 duplicated label (no detector exists for any).
    assert proposed_mode_ids == {"5", "7", "10", "11", "12", "13", "14"}


# =========================================================================== #
# AC11: mode rule lists derived from the shipped declarations
# =========================================================================== #


def test_ac11_mode_rule_lists_are_derived_from_shipped_declarations(matrix):
    from segfacet.heuristics.rule import iter_rules

    expected_by_mode: dict = {}
    for rule in iter_rules():
        decl = rule.mode_declaration
        if decl is None:
            continue
        for mode in decl.modes:
            expected_by_mode.setdefault(mode, set()).add(rule.rule_id)
    assert expected_by_mode, "expected at least one rule to declare at least one mode"

    d = matrix
    modes = _mode_records(d)
    for mode, record in modes.items():
        expected = sorted(expected_by_mode.get(mode, set()))
        assert record["rules"] == expected, mode


# =========================================================================== #
# AC12: every mode row carries a rung from the closed vocabulary
# =========================================================================== #


@pytest.mark.parametrize("mode", MODES)
def test_ac12_mode_rung_is_member_of_closed_vocabulary_or_none_when_proposed(mode, matrix):
    """Reconciled (item 150, 2026-09-14): a rung is derived from the mode's
    per-edge ``evidence_rung`` values, so a ``proposed`` mode -- no declaring
    rule, hence no edge -- derives ``None`` rather than a vocabulary member.
    ``None`` is therefore legal for exactly the proposed modes and illegal for
    every other one; the Markdown rendering of that ``None`` is pinned by
    ``test_ac12_proposed_mode_rung_renders_as_none_in_the_markdown``."""
    record = _mode_record(matrix, mode)
    if mode in PROPOSED_MODES:
        assert record["rung"] is None, (mode, record["rung"])
    else:
        assert record["rung"] in RUNGS, (mode, record["rung"])


def test_ac12_proposed_mode_rung_renders_as_none_in_the_markdown():
    """The committed Markdown's rung column for a ``None``-rung mode: the
    generator writes the literal ``(none)`` placeholder it uses for every
    empty cell, never an empty cell or the Python ``None`` repr."""
    assert PROPOSED_MODES, "expected at least one proposed mode on this tree"
    lines = _md_lines()
    for mode in sorted(PROPOSED_MODES):
        row = _row_for_mode(lines, mode)
        assert row is not None, mode
        cells = [c.strip() for c in row.strip("|").split("|")]
        rung_cell = cells[6]
        assert rung_cell.startswith("(none) -- "), (mode, rung_cell)
        assert "None" not in rung_cell, (mode, rung_cell)


def test_adv_ac12_stale_rung_outside_vocabulary_is_detectable(matrix_overlap_mode_rung_stale):
    record = _mode_record(matrix_overlap_mode_rung_stale, _OVERLAP_MODE)
    assert record["rung"] not in RUNGS, record["rung"]


# =========================================================================== #
# AC13: the overlapping-segments mode's rung names the single-channel
# mechanism. Re-pointed (item 150): "Overlapping segments" is mode 15 after
# the sign-off's 2026-09-15 revision re-assigned the ids; nothing about the
# claim changed.
# =========================================================================== #


def test_ac13_overlap_mode_rung_and_mechanism_name_the_single_channel_mechanism(matrix):
    overlap_mode = _mode_record(matrix, _OVERLAP_MODE)
    assert overlap_mode["title"] == "Overlapping segments"
    assert overlap_mode["rung"] == "structurally-unobservable"
    assert "single-channel" in overlap_mode["mechanism"]
    assert "label map" in overlap_mode["mechanism"]


# =========================================================================== #
# AC14: the overlapping-segments mode is not pipeline-detected, from the
# manifest. Re-pointed (item 150) from mode 8 to mode 15 (2026-09-15
# revision); the fixture case id (``mode8_force_overlap``) is historical and
# unchanged.
# =========================================================================== #


def test_ac14_overlap_mode_not_pipeline_detected_names_reconstructed_case(matrix):
    manifest_detection = _manifest_detection_by_case_id()
    assert "mode8_force_overlap" in manifest_detection

    mode8 = _mode_record(matrix, _OVERLAP_MODE)
    assert mode8["pipeline_detected"] is False

    cases = mode8["cases"]
    assert cases, "expected the overlap mode to name at least one corpus case"
    case_ids = {c["case_id"] for c in cases}
    assert "mode8_force_overlap" in case_ids
    named = next(c for c in cases if c["case_id"] == "mode8_force_overlap")
    assert named["detection"] == manifest_detection["mode8_force_overlap"]
    assert named["detection"] == "reconstructed_record"


# =========================================================================== #
# AC15: rung and corpus detection are cross-checked
# =========================================================================== #


@pytest.mark.parametrize("mode", MODES)
def test_ac15_rung_and_pipeline_detected_cross_check(mode, matrix):
    record = _mode_record(matrix, mode)
    if record["rung"] == "synthetic-demonstrable":
        assert record["pipeline_detected"] is True, mode
    elif record["rung"] == "structurally-unobservable":
        assert record["pipeline_detected"] is False, mode


def test_adv_ac15_cross_check_violation_when_overlap_mode_rung_monkeypatched_synthetic(
    matrix_overlap_mode_rung_synthetic,
):
    mode8 = _mode_record(matrix_overlap_mode_rung_synthetic, _OVERLAP_MODE)
    # AC15 requires pipeline_detected True whenever rung is
    # synthetic-demonstrable; the overlap mode (15 since item 150's
    # 2026-09-15 revision) is still (correctly) reconstructed, so the two
    # facts below jointly demonstrate the cross-check now fails.
    assert mode8["rung"] == "synthetic-demonstrable"
    assert mode8["pipeline_detected"] is False


# =========================================================================== #
# AC16: the two modes the committed geometric corpus demonstrates end-to-end
# are recorded synthetic-demonstrable. Re-pointed (item 150, 2026-09-14):
# item 138's pair was modes 1 and 4 under the pre-sign-off ids; the sign-off
# re-homed both of those cases (mode1_displace is now a mode-1 co-detection
# that deliberately does NOT validate, and mode4_relabel_swap moved to the
# label-sequence mode), leaving modes 3 and 6 as the two the corpus
# demonstrates with their own intended rules. Re-pointed again (2026-09-15
# revision): mode2_fragment and fragmentation's Fragmentation: detector moved
# to the parent mode 1, and the relabel swap sits under mode 9 (out-of-order
# label sequence) -- same two cases, same claim.
# =========================================================================== #


@pytest.mark.parametrize("mode, case_id", [(1, "mode2_fragment"), (9, "mode4_relabel_swap")])
def test_ac16_fragment_and_swap_modes_are_synthetic_demonstrable(mode, case_id, matrix):
    manifest_detection = _manifest_detection_by_case_id()
    assert case_id in manifest_detection

    record = _mode_record(matrix, mode)
    assert record["rung"] == "synthetic-demonstrable"
    assert record["pipeline_detected"] is True

    cases = record["cases"]
    assert cases, mode
    case_ids = {c["case_id"] for c in cases}
    assert case_id in case_ids
    named = next(c for c in cases if c["case_id"] == case_id)
    assert named["detection"] == manifest_detection[case_id]
    assert named["detection"] == "pipeline"


def test_adv_ac16_rung_unmoved_by_weaker_rules_joining_a_modes_rule_list(matrix):
    """A rung is a property of the mode, not a count of how many rules
    declare it -- and, specifically, a weaker edge joining the list must not
    drag the mode down. Item 138 demonstrated this on mode 1 gaining
    ``reference_delta`` (b1c593c). Re-pointed (item 150, 2026-09-14) to mode
    3, which is the same shape under the signed-off ids: ``fragmentation``
    demonstrates it on two committed corpus cases (synthetic-demonstrable),
    while ``bounds`` and ``reference_delta`` joined at needs-real-data as
    volume/extent proxies. The mode keeps the strongest edge's rung.
    Re-pointed again (2026-09-15 revision) to mode 4 (islands), which keeps
    that shape: ``fragmentation``'s Rogue island(s): edge is demonstrated on
    mode3_inject_islands, and ``bounds``/``reference_delta`` sit below it."""
    import segfacet.failure_modes as failure_modes_module

    record = _mode_record(matrix, 4)
    assert set(record["rules"]) == {"bounds", "fragmentation", "reference_delta"}, record["rules"]
    assert record["rung"] == "synthetic-demonstrable"
    assert record["pipeline_detected"] is True

    # The two weaker edges really are weaker -- otherwise this asserts nothing.
    edge_rungs = {
        edge.rule_id: edge.evidence_rung
        for edge in failure_modes_module.SPECIFICATION[4].intended_rules
    }
    assert edge_rungs["fragmentation"] == "synthetic-demonstrable", edge_rungs
    assert edge_rungs["bounds"] == "needs-real-data", edge_rungs
    assert edge_rungs["reference_delta"] == "needs-real-data", edge_rungs


# =========================================================================== #
# AC17: mode 7's rung records its own cap
# =========================================================================== #


def test_ac17_label_sequence_mode_mechanism_records_the_corrected_rank_claim(matrix):
    """Reconciled (item 147, 2026-09-04): this test pinned the claim
    ``rank(v) == v - 1``, which is **false** across exactly the lumbar range
    §6.7's example uses (``docs/aide/insights.md``, item 145, 2026-09-03) --
    ``segfacet.labels.CANONICAL_ORDER`` inserts ``T13`` at index 19, so a
    lumbar label's rank equals its value. Item 147 corrects the sentence in
    its one home, ``failure_modes.SPECIFICATION[7].mechanism``, and forbids
    the false literal anywhere under ``src/segfacet/``; the corrected
    claim's *measurement* is
    ``tests/test_147_specification_is_the_record.py::test_ac10_...``. What
    stays here is this module's own claim: the row records its rung and a
    mechanism naming the live tokens the correction rests on.

    Re-pointed (item 150, 2026-09-14): "non-continuous label sequence" is
    mode 6 after the sign-off. Two things about it moved with the ids and are
    restated rather than dropped. Its *mode* rung is now
    synthetic-demonstrable (``mislabel``'s and ``coverage``'s edges are
    demonstrated on committed cases), so the needs-real-data cap this test is
    named for is recorded where it now lives -- on the ``sequence`` edge
    alone, which the mechanism says in words and the specification carries as
    data, asserted here as both. §6.7's ``L1 → T12 → L2 → L5`` example is no
    longer quoted in the sentence (the corrected claim is about
    ``CANONICAL_ORDER``'s ranking of ``T13``, and the example illustrated the
    false one), so that literal is not asserted; the §6 title carrying it is
    still pinned, as provenance, in ``VISION_SECTION_SIX_MODE_TITLES``.
    Re-pointed again (2026-09-15 revision): the implausible label sequence
    split three ways, and the order-breaking sub-mode carrying ``sequence``
    and ``mislabel``'s ordering detector is mode 9."""
    import segfacet.failure_modes as failure_modes_module

    record = _mode_record(matrix, 9)
    assert record["rung"] == "synthetic-demonstrable"
    assert "rank(v) == v - 1" not in record["mechanism"]
    for token in ("CANONICAL_ORDER", "T13"):
        assert token in record["mechanism"], (token, record["mechanism"])

    # The cap itself, on the one edge that still carries it.
    edge_rungs = {
        edge.rule_id: edge.evidence_rung
        for edge in failure_modes_module.SPECIFICATION[9].intended_rules
    }
    assert edge_rungs["sequence"] == "needs-real-data", edge_rungs
    assert "needs-real-data" in record["mechanism"], record["mechanism"]


# =========================================================================== #
# AC18: rule -> mode is complete and reported complete
# =========================================================================== #


def test_ac18_rule_to_mode_direction_complete_with_one_record_per_rule(matrix):
    from segfacet.heuristics.rule import iter_rules

    rule_ids = {r.rule_id for r in iter_rules()}
    assert rule_ids

    d = matrix
    rules = _rule_records(d)
    assert set(rules.keys()) == rule_ids

    direction = d["directions"]["rule_to_mode"]
    assert direction["complete"] is True
    assert direction["holes"] == []


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_ac18_rule_record_carries_modes_xor_mode_less_reason(rule_id, matrix):
    record = _rule_records(matrix)[rule_id]
    has_modes = bool(record["modes"])
    has_reason = bool(record.get("mode_less_reason"))
    assert has_modes != has_reason, (rule_id, record)


# =========================================================================== #
# AC19: every mode -> rule edge is attributed corpus or analytic, from the
# corpus map
# =========================================================================== #


def test_ac19_every_mode_to_rule_edge_is_attributed_from_the_specification(matrix):
    """Reconciled (item 149, 2026-09-04, D2): attribution moved from
    ``catalogue.scan_synth_rule_mode_map()`` (a geometric-corpus-only AST
    scan) to ``failure_modes.SPECIFICATION``'s own ``corpus_cases``, which
    span both corpora by construction (AC19). A ``(mode, rule)`` edge is
    ``"corpus"`` iff at least one of that mode's ``corpus_cases`` lists the
    rule in its ``expected_firing``, else ``"analytic"``. Mode 10 (the first
    `proposed` entry) still declares no rules, so it carries zero edges and
    zero read paths. Mode 9's ``intensity`` now attributes ``"corpus"``
    (three intensity-corpus cases list it in ``expected_firing``);
    ``intensity_reference_delta`` stays ``"analytic"`` (no committed case
    designates it -- A9/A1's analytic-only class). This is the **one** cell
    D2 measures moving; every mode 1-8 attribution is unchanged from the
    base artifact."""
    import segfacet.failure_modes as failure_modes_module

    d = matrix
    modes = _mode_records(d)
    assert modes

    # Re-pointed (item 150, 2026-09-15 revision): the rule-less `proposed`
    # entries are modes 5, 7, 11, 12, 13 and 14, and the intensity pair's
    # mode is 16.
    assert PROPOSED_MODES == {5, 7, 10, 11, 12, 13, 14}, PROPOSED_MODES
    for proposed_mode in sorted(PROPOSED_MODES):
        record = modes[proposed_mode]
        assert record["rules"] == [], record
        assert record["rule_attribution"] == {}, record
        assert record["read_paths"] == [], record

    intensity_mode = modes[16]
    assert intensity_mode["rule_attribution"] == {
        "intensity": "corpus",
        "intensity_reference_delta": "analytic",
    }, intensity_mode

    expected_corpus_edges = set()
    for mode_id, mode_spec in failure_modes_module.SPECIFICATION.items():
        for case in mode_spec.corpus_cases:
            for rule_id in case.expected_firing:
                expected_corpus_edges.add((mode_id, rule_id))
    assert expected_corpus_edges, "expected at least one specification-designated edge"

    checked = False
    for mode, record in modes.items():
        if mode in PROPOSED_MODES:
            continue
        attribution = record["rule_attribution"]
        assert attribution, mode
        for rule_id, tag in attribution.items():
            checked = True
            assert tag in ("corpus", "analytic"), (mode, rule_id, tag)
            expected = "corpus" if (mode, rule_id) in expected_corpus_edges else "analytic"
            assert tag == expected, (mode, rule_id, tag, expected)
    assert checked, "expected at least one mode-to-rule edge"


# =========================================================================== #
# AC20: the analytic edges are exactly the edges of rules the corpus map
# never designates
# =========================================================================== #


def test_ac20_analytic_edges_equal_edges_the_specification_never_designates_corpus(matrix):
    """Reconciled (item 149, 2026-09-04, D2): the total edge count and the
    corpus/analytic split are both derived here from ``iter_rules()`` (edges)
    and ``failure_modes.SPECIFICATION`` (corpus designation) directly -- the
    same sources ``build_matrix`` now reads -- never pinned as a bare
    integer. ``witness`` stays as a dated, human-readable record of what the
    derivation currently evaluates to -- informative, not the assertion.
    D2 measures exactly one cell moving from the pre-149 witness: mode 9's
    ``intensity`` from ``analytic`` to ``corpus``."""
    from segfacet.heuristics.rule import iter_rules
    import segfacet.failure_modes as failure_modes_module

    corpus_designated = set()
    for mode_id, mode_spec in failure_modes_module.SPECIFICATION.items():
        for case in mode_spec.corpus_cases:
            for rule_id in case.expected_firing:
                corpus_designated.add((mode_id, rule_id))

    expected_total_edges = set()
    expected_analytic = set()
    for rule in iter_rules():
        decl = rule.mode_declaration
        if decl is None:
            continue
        for mode in decl.modes:
            edge = (mode, rule.rule_id)
            expected_total_edges.add(edge)
            if edge not in corpus_designated:
                expected_analytic.add(edge)

    d = matrix
    modes = _mode_records(d)
    actual_all_edges = set()
    actual_analytic = set()
    for mode, record in modes.items():
        for rule_id, tag in record["rule_attribution"].items():
            actual_all_edges.add((mode, rule_id))
            if tag == "analytic":
                actual_analytic.add((mode, rule_id))

    assert actual_all_edges, "expected at least one mode-to-rule edge"
    assert actual_all_edges == expected_total_edges
    assert actual_analytic == expected_analytic

    # 2026-09-15, item 150 (revision of the 2026-09-14 sign-off): what the
    # derivation above currently evaluates to on this tree -- a dated
    # witness, not a floor a future change must match. The revision split
    # the paired sub-modes and re-assigned the ids: bounds declares 1-4,
    # reference_delta 1-4 and 8. (6, "coverage") is a corpus edge: mode 6
    # ("vertebra not segmented") carries mode5_remove_level, which expects
    # coverage to fire, alongside remove_level_relabel, which expects nothing.
    # Mode 10 ("skipped level label") is proposed and declares no rule.
    witness = {
        (1, "bounds"),
        (1, "reference_delta"),
        (2, "bounds"),
        (2, "reference_delta"),
        (3, "bounds"),
        (3, "reference_delta"),
        (4, "bounds"),
        (4, "reference_delta"),
        (8, "reference_delta"),
        (16, "intensity_reference_delta"),
    }
    assert actual_analytic == witness

    expected_corpus = expected_total_edges - expected_analytic
    assert actual_all_edges - actual_analytic == expected_corpus

    # Attribution is a property of the EDGE, not of the rule. Item 138
    # asserted per-rule uniformity, which held only incidentally: while every
    # rule declared modes the corpus either designated for it throughout or
    # never at all. The 2026-09-14 sign-off briefly broke that (`coverage`
    # declared one analytic and one corpus mode), so the invariant is
    # restated as the per-edge derivation it always was. On the 2026-09-15
    # revision (mode 10 narrowed to a label-only, rule-less proposed mode;
    # coverage declares only mode 6, which mode5_remove_level designates) no
    # rule is mixed again -- asserted as a dated witness so a rule that
    # becomes mixed is noticed here rather than passing silently.
    by_rule: dict = {}
    for mode, rule_id in actual_analytic:
        by_rule.setdefault(rule_id, set()).add("analytic")
    for mode, rule_id in actual_all_edges - actual_analytic:
        by_rule.setdefault(rule_id, set()).add("corpus")
    for rule_id, tags in by_rule.items():
        assert tags <= {"analytic", "corpus"}, (rule_id, tags)
    mixed = {rule_id for rule_id, tags in by_rule.items() if len(tags) == 2}
    assert mixed == set(), by_rule


def test_adv_ac20_mistagged_corpus_evidence_changes_no_attribution(matrix_bounds_mistagged_evidence):
    """A6: attribution is derived from the specification's corpus cases,
    never from the declaration's own free-form evidence tag -- retagging
    bounds' evidence leaves the (2, bounds) edge attributed 'analytic'
    regardless of the tag's text (no committed corpus case designates bounds
    for mode 2).

    Reconciled (item 147, 2026-09-04): the reserved ``"corpus"`` literal is
    retired (AC20) -- any non-reserved evidence string demonstrates the
    same "attribution ignores the tag" claim just as well."""
    mode2 = _mode_record(matrix_bounds_mistagged_evidence, 2)
    assert "bounds" in mode2["rule_attribution"], mode2["rule_attribution"]
    assert mode2["rule_attribution"]["bounds"] == "analytic"


# =========================================================================== #
# AC21: the feature direction reports its counts against the live catalogue
# =========================================================================== #


def test_ac21_feature_direction_counts_match_a_fresh_catalogue(matrix):
    import segfacet.catalogue as catalogue_module

    cat = catalogue_module.build_catalogue(strict=True)
    assert cat.entries, "expected a non-empty catalogue"

    total = len(cat.entries)
    read_by_rule = sum(1 for e in cat.entries if e.consuming_rules)
    read_by_no_rule = total - read_by_rule
    unwired = sum(1 for e in cat.entries if e.status == "unwired")

    d = matrix
    features = d["features"]
    assert features["total_paths"] == total
    assert features["read_by_rule"] == read_by_rule
    assert features["read_by_no_rule"]["count"] == read_by_no_rule
    assert features["unwired"] == unwired


# =========================================================================== #
# AC22: the "inventory, not a gap" qualifier sits with the count
# =========================================================================== #


def test_ac22_inventory_not_a_gap_qualifier_sits_with_the_count(matrix):
    read_by_no_rule = matrix["features"]["read_by_no_rule"]
    assert isinstance(read_by_no_rule, dict)
    assert "count" in read_by_no_rule
    assert read_by_no_rule["required"] is False
    qualifier = read_by_no_rule["qualifier"]
    assert "inventory" in qualifier
    assert "not a gap" in qualifier


def test_ac22_committed_markdown_prints_qualifier_beside_the_count():
    md_text = _COMMITTED_MD.read_text(encoding="utf-8")
    committed_payload = json.loads(_COMMITTED_JSON.read_text(encoding="utf-8"))

    idx = md_text.find("inventory")
    assert idx != -1, "expected the inventory qualifier in the committed markdown"
    window = md_text[max(0, idx - 400) : idx + 400]

    count = committed_payload["features"]["read_by_no_rule"]["count"]
    assert str(count) in window, (count, window)


# =========================================================================== #
# AC23: per-rule feature sets derived from the catalogue
# =========================================================================== #


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_ac23_rule_feature_paths_are_derived_from_the_catalogue(rule_id, matrix):
    import segfacet.catalogue as catalogue_module

    cat = catalogue_module.build_catalogue(strict=True)
    assert cat.entries

    expected = sorted(e.path for e in cat.entries if rule_id in e.consuming_rules)

    record = _rule_records(matrix)[rule_id]
    assert record["feature_paths"] == expected, rule_id


# =========================================================================== #
# AC24: reconciled (item 149, 2026-09-04, AC8/AC10) -- the conflated
# ``feature_paths`` union (anchors unioned with every leaf path every
# declaring rule consumes, regardless of classification) is gone from the
# mode record. In its place: ``anchor_paths`` and ``read_paths`` are two
# separate, separately-labelled fields, and neither one is ever unioned with
# the other. ``read_paths`` is the sorted union, over the mode's declaring
# rules, of the leaf paths each rule classifies "signal" -- item 149's own
# ``tests/test_149_conformance_report.py`` carries the full per-rule
# derivation proof (its own AC10); this reconciliation asserts the shape
# survives here: the field exists, is disjoint in *purpose* from
# anchor_paths (never unioned), and mode 10 -- the one mode with zero
# declaring rules -- carries an empty read_paths.
# =========================================================================== #


@pytest.mark.parametrize("mode", MODES)
def test_ac24_mode_read_paths_and_anchor_paths_are_two_separate_fields(mode, matrix):
    modes = _mode_records(matrix)
    record = modes[mode]
    # Reconciled (item 150, 2026-09-14): a `proposed` mode legitimately
    # declares no rule, so the "has rules" precondition is scoped to the
    # modes that do -- the field-shape claim below holds for every mode.
    if mode in PROPOSED_MODES:
        assert record["rules"] == [], mode
        assert record["read_paths"] == [], mode
    else:
        assert record["rules"], mode
    assert "feature_paths" not in record, record
    assert "anchor_paths" in record, record
    assert "read_paths" in record, record
    assert isinstance(record["read_paths"], list), record["read_paths"]


# =========================================================================== #
# AC25: a corpus-designated rule id that no rule registers is reported
# =========================================================================== #


def test_ac25_no_unregistered_designated_rule_id_on_this_tree(matrix):
    assert matrix["corpus_designated_unregistered_rule_ids"] == []


def test_ac25_unregistered_designated_rule_id_is_reported_and_fails_completeness(
    matrix_unregistered_designated_rule,
):
    d = matrix_unregistered_designated_rule
    assert "boundary" in d["corpus_designated_unregistered_rule_ids"]
    assert d["directions"]["mode_to_rule"]["complete"] is False


def test_adv_mode_to_rule_hole_when_a_declaration_is_monkeypatched_mode_less(matrix_overlap_mode_less):
    """Adversarial -- mode -> rule hole. Monkeypatching the live declaration
    of ``overlap`` to a mode-less one makes the overlap mode (15 since item
    150's 2026-09-15 revision) a hole naming the mode, with complete: false.
    The unpatched tree already carries holes (the proposed modes), so the
    membership is exact, never a substring match another id could satisfy."""
    d = matrix_overlap_mode_less
    assert d["directions"]["mode_to_rule"]["complete"] is False
    holes = d["directions"]["mode_to_rule"]["holes"]
    assert holes, "expected at least one hole"
    assert str(_OVERLAP_MODE) in {str(hole) for hole in holes}, holes
    assert str(_OVERLAP_MODE) not in {str(mode) for mode in PROPOSED_MODES}

    mode8 = _mode_record(d, _OVERLAP_MODE)
    assert mode8["rules"] == []


# =========================================================================== #
# AC26: an undeclared registered rule makes rule -> mode fail loudly
# =========================================================================== #


def test_ac26_undeclared_registered_rule_makes_rule_to_mode_fail_loudly(matrix_undeclared_rule_registered):
    d = matrix_undeclared_rule_registered
    assert d["directions"]["rule_to_mode"]["complete"] is False
    holes = d["directions"]["rule_to_mode"]["holes"]
    assert holes, "expected at least one hole"
    assert any("__item138_no_declaration__" in str(hole) for hole in holes), holes


# =========================================================================== #
# AC27: a malformed evidence renders as one cell, not one per character
# =========================================================================== #


def test_ac27_bare_string_evidence_renders_as_one_cell_not_per_character(raw_matrix_bounds_bare_evidence):
    """Reconciled (item 147, 2026-09-04): ``RuleModeDeclaration``'s
    ``__post_init__`` now rejects a bare-str ``evidence`` at construction
    (AC18), so the item-136 weakness this test reproduced can no longer be
    reached through normal construction. The defence-in-depth coverage
    stays: force the malformed value past ``__post_init__`` with
    ``object.__setattr__`` (the frozen dataclass's own escape hatch) so
    ``traceability._normalise_evidence``'s own guard against a bare str
    stays exercised -- see ``raw_matrix_bounds_bare_evidence``."""
    import segfacet.traceability as traceability

    md = traceability.render_markdown(raw_matrix_bounds_bare_evidence)
    lines = md.splitlines()
    row = _row_for_rule(lines, "bounds")
    assert row is not None, "expected a rendered row for bounds"
    assert "corpus-derived" in row
    assert "c, o, r" not in row


# =========================================================================== #
# AC28: nothing environment-dependent
# =========================================================================== #


def _authored_source_text() -> str:
    """Every authored Python source file under ``src/segfacet`` concatenated.

    The ISO-date check below reads it (item 150, 2026-09-14). Item 138 could
    assert an artifact carried no ``YYYY-MM-DD`` at all, because no authored
    string that reached one held a date. The maintainer sign-off put dates
    into authored prose -- every mechanism sentence and rule ``mode_less_reason``
    that cites "the catalogue signed off at item 150 (2026-09-14)" -- so a
    blanket ban would now forbid provenance rather than a clock reading. The
    claim that survives, and is the one AC28 is actually about, is that no
    date in the artifact came from the *machine*: every one of them must be
    findable verbatim in the authored source the generator renders from. A
    generation timestamp is not."""
    src_dir = _REPO_ROOT / "src" / "segfacet"
    sources = sorted(src_dir.rglob("*.py"))
    assert sources, "expected authored sources under src/segfacet"
    return "\n".join(path.read_text(encoding="utf-8") for path in sources)


def _assert_no_environment_dependent_content(text: str, authored: str):
    dates = set(re.findall(r"\d{4}-\d{2}-\d{2}", text))
    unauthored = sorted(d for d in dates if d not in authored)
    assert unauthored == [], unauthored
    assert _REPO_ROOT.as_posix() not in text
    assert not re.search(r"[A-Za-z]:\\", text)
    import socket

    hostname = socket.gethostname()
    if hostname:
        assert hostname not in text


def test_ac28_committed_artifacts_carry_nothing_environment_dependent():
    json_text = _COMMITTED_JSON.read_text(encoding="utf-8")
    md_text = _COMMITTED_MD.read_text(encoding="utf-8")

    payload = json.loads(json_text)
    assert payload, "expected a non-empty JSON payload"

    def _walk(node):
        if isinstance(node, float):
            raise AssertionError(f"unexpected float leaf: {node!r}")
        if isinstance(node, dict):
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for value in node:
                _walk(value)

    _walk(payload)

    authored = _authored_source_text()
    _assert_no_environment_dependent_content(json_text, authored)
    _assert_no_environment_dependent_content(md_text, authored)

    # Non-vacuity: the date check above only says something if the artifacts
    # actually carry dates (they do -- the sign-off provenance) and if an
    # unauthored one would be caught.
    assert re.search(r"\d{4}-\d{2}-\d{2}", json_text), "expected >=1 authored date to check"
    with pytest.raises(AssertionError):
        _assert_no_environment_dependent_content(json_text + " 1999-01-02", authored)


# =========================================================================== #
# AC29 (item 138): the committed-artifact guard stays clean, six-ground.
# Reconciled (item 149, 2026-09-04, AC27): GROUNDS grows to six (the
# "unextended" pin moves from five to six), and the "no allowlist entry
# mentions traceability_matrix" assertion inverts -- item 149 adds exactly
# that entry, under "no-float-leaf" (AC24). This also proves this item's
# root-idiom normalisation (Implementation Step 1) actually landed: before
# it, ``iter_violations`` could not see the comparisons this module's own
# AC15-equivalent byte checks make (item 149's AC25 is the dedicated
# non-vacuity proof; this is the "guard is clean now" half).
# =========================================================================== #


def test_ac29_committed_artifact_guard_clean_and_grounds_at_six_members():
    import committed_artifact_guard as guard

    violations = list(guard.iter_violations(_REPO_ROOT / "tests"))
    assert violations == [], [guard.violation_message([v]) for v in violations]
    assert len(guard.GROUNDS) == 6

    assert any("traceability_matrix" in entry.path for entry in guard.ALLOWLIST), guard.ALLOWLIST


# =========================================================================== #
# AC30: the matrix is inert at evaluation time
# =========================================================================== #


def test_ac30_build_matrix_is_inert_and_deterministic_at_evaluation_time(inertness_probe):
    """Item 149 (2026-09-04): still true now that the builder drives 13
    corpus cases through the pipeline (AC32) -- the mechanism itself is
    unchanged, only ``inertness_probe`` now houses the two ``build_matrix()``
    calls (AC28)."""
    before, after, d1, d2 = inertness_probe
    assert isinstance(before, list)
    assert after == before
    assert d1 == d2


def test_adv_matrix_to_dict_mutation_does_not_leak_into_a_later_call(raw_matrix):
    import segfacet.traceability as traceability

    d1 = traceability.matrix_to_dict(raw_matrix)
    assert d1, "expected a non-empty dict"

    d1["modes"] = "deliberately corrupted by this test"
    d2 = traceability.matrix_to_dict(raw_matrix)
    assert d2["modes"] != "deliberately corrupted by this test"


# =========================================================================== #
# AC31: every mode's mechanism names a resolvable live token; no
# character-count threshold anywhere in this module
# =========================================================================== #


def _live_token_candidates(record, mode) -> set:
    """The live tokens a mode's mechanism sentence may resolve against: the
    mode's Stage-18 metric anchors, the committed corpus case ids designated
    for it, and the rule ids that declare it.

    Reconciled (item 150, 2026-09-14): ``MODE_ANCHOR_PATHS`` no longer has a
    key for every mode (six of ten have a metric anchor), so the lookup is a
    ``.get``; the caller is what asserts the union is non-empty."""
    import segfacet.feature_docs as feature_docs_module

    case_ids_for_mode = {c["case_id"] for c in _manifest_cases() if c.get("failure_mode") == mode}
    anchors = set(feature_docs_module.MODE_ANCHOR_PATHS.get(mode, ()))
    return anchors | case_ids_for_mode | set(record["rules"])


@pytest.mark.parametrize("mode", MODES)
def test_ac31_mode_mechanism_names_a_resolvable_live_token(mode, matrix):
    """Reconciled (item 150, 2026-09-14): a ``proposed`` mode has no anchor,
    no corpus case and no declaring rule, so it has no token of that kind to
    name -- and both of the sign-off's proposed entries carry an authored
    sentence that names its hypothesised input as a real record leaf path
    instead. The claim is therefore split, not weakened: a mode with rules
    must still name an anchor, a case or one of its own rules; a proposed
    mode must name a path the feature catalogue actually carries.

    Reconciled again (item 150, 2026-09-15 revision): seven proposed modes now.
    Five name a catalogued path. Mode 5 (holes) cannot: none of its
    hypothesised candidate features is extracted, and its authored sentence
    says so. The claim is split once more rather than weakened: a proposed
    mode with a catalogued candidate feature must name a catalogued path; a
    proposed mode with none must have a mechanism stating the feature layer
    extracts none, and which modes those are is pinned as a witness."""
    import segfacet.failure_modes as failure_modes_module

    record = _mode_record(matrix, mode)
    mechanism = record["mechanism"]
    assert mechanism, mode

    if mode in PROPOSED_MODES:
        import segfacet.catalogue as catalogue_module

        assert record["rules"] == [], mode
        catalogue_paths = {e.path for e in catalogue_module.build_catalogue(strict=True).entries}
        assert catalogue_paths, "expected a non-empty feature catalogue"
        candidate_paths = {
            f.path for f in failure_modes_module.SPECIFICATION[mode].candidate_features
        }
        assert candidate_paths, mode
        if candidate_paths & catalogue_paths:
            named = {path for path in catalogue_paths if path and path in mechanism}
            assert named, (mode, mechanism)
        else:
            assert mode == 5, (mode, sorted(candidate_paths))
            assert "extracts neither" in mechanism, (mode, mechanism)
        return

    candidate_tokens = _live_token_candidates(record, mode)
    assert candidate_tokens, mode
    assert any(_token_in_mechanism(token, mechanism) for token in candidate_tokens), (
        mode,
        mechanism,
        candidate_tokens,
    )


# A14's forbidden shape, widened: the original pattern matched only a
# length call first with a strict inequality, so an equality-style floor on
# a mechanism sentence's character count, or the same comparison spelled
# with the call on the right of a leading number, both slipped through
# undetected. Both operand orders, and equality alongside the inequalities,
# are covered now. Scoped to the prose-content fields A14 is actually about
# (mechanism, rung label, qualifier, evidence, title) -- via a name/key
# fragment inside the length call's parens, not to every such comparison in
# the module, so an unrelated structural count elsewhere in this file (e.g.
# a same-tag-only invariant, or another module's fixed-vocabulary length)
# is not swept in
# by a widening aimed at mechanism-sentence floors.
_LENGTH_THRESHOLD_CONTENT_RE = r"(?:mechanism|evidence|rung\w*|qualifier\w*|label\w*|title\w*)"
_LENGTH_THRESHOLD_RE = re.compile(
    r"len\([^)\n]*\b" + _LENGTH_THRESHOLD_CONTENT_RE + r"\b[^)\n]*\)\s*(==|>=|<=|>|<)\s*\d+"
    r"|\d+\s*(==|>=|<=|>|<)\s*len\([^)\n]*\b" + _LENGTH_THRESHOLD_CONTENT_RE + r"\b[^)\n]*\)"
)


def test_ac31_no_character_count_threshold_assertions_in_this_module():
    """A14 -- item 137's own defect was exactly this shape (a character-count
    floor standing in for a content check on a mechanism sentence). This
    module inspects its own source and must contain no such pattern for any
    mechanism, rung label, qualifier, evidence, or title string -- in either
    operand order and under any of ``==``/``>=``/``<=``/``>``/``<``."""
    source = Path(__file__).read_text(encoding="utf-8")
    offenders = _LENGTH_THRESHOLD_RE.findall(source)
    assert offenders == [], offenders


def test_adv_ac31_stale_mechanism_naming_no_live_identifier_is_detectable(
    matrix_overlap_mode_bogus_mechanism,
):
    """Re-pointed (item 150) from mode 8 to mode 15 -- the sign-off's
    2026-09-15 revision assigns "Overlapping segments" id 15."""
    record = _mode_record(matrix_overlap_mode_bogus_mechanism, _OVERLAP_MODE)
    assert record["rules"], "expected the overlap mode to still declare a rule"

    candidate_tokens = _live_token_candidates(record, _OVERLAP_MODE)
    assert candidate_tokens, "expected at least one live token candidate"
    assert not any(_token_in_mechanism(token, record["mechanism"]) for token in candidate_tokens)


def test_adv_ac31_stale_mechanism_one_character_off_the_real_case_id_is_detectable(
    matrix_overlap_mode_typo_mechanism,
):
    """Re-pointed (item 150) from mode 8 to mode 15 (2026-09-15 revision);
    the corpus case id (``mode8_force_overlap``) is historical and
    unchanged."""
    case_ids = {
        c["case_id"] for c in _manifest_cases() if c.get("failure_mode") == _OVERLAP_MODE
    }
    assert case_ids, "expected at least one overlap-mode corpus case"
    assert "mode8_force_overlap" in case_ids

    record = _mode_record(matrix_overlap_mode_typo_mechanism, _OVERLAP_MODE)
    assert record["rules"], "expected the overlap mode to still declare a rule"

    candidate_tokens = _live_token_candidates(record, _OVERLAP_MODE)
    assert candidate_tokens, "expected at least one live token candidate"
    assert not any(_token_in_mechanism(token, record["mechanism"]) for token in candidate_tokens)


# =========================================================================== #
# AC31 (real checks) -- item 138's own defect (0db0fca, 2026-09-03): the
# token-presence test above proves a mechanism names *something* resolvable,
# never that the claim built around that token is true. Four of eight
# mechanism sentences shipped false despite passing every AC31 test above --
# a code review, not this suite, caught them. These two checks verify the
# two claim shapes a mechanism sentence actually makes that this codebase
# can decide:
#
# 1. "rule R reads feature path P" -- cross-checked against the catalogue's
#    own consuming_rules derivation (via each rule's AC23 feature_paths,
#    itself catalogue-derived), never against MODE_ANCHOR_PATHS. Mode 4's
#    pre-fix sentence named the mode's anchor path
#    (stage3.monotonic_consistency.is_monotonic) as what mislabel reads;
#    mislabel.py only ever reads non_monotonic_pairs, so that anchor path
#    sits outside mislabel's catalogue-derived feature_paths -- exactly what
#    this check would have failed on.
# 2. "the corpus case demonstrates end-to-end, driving exactly these rules"
#    -- verified by driving the named corpus case through
#    segfacet.synth.regression.pipeline_findings (the same public harness
#    tests/test_041_regression_suite.py drives) and comparing the fired
#    rule_id set against the sentence's own machine-checkable
#    "(measured: findings == [...])" annotation, the idiom 0db0fca's fix
#    introduced. Modes 1 and 2's pre-fix sentences each claimed a rule fired
#    (reference_delta / bounds) that cannot fire without an attached
#    reference, which plain run_qc never attaches -- exactly what this
#    check would have failed on.
#
# What this deliberately leaves unasserted: modes 5 and 6's pre-fix
# sentences named the *correct* rule (coverage / border) against a real,
# genuinely-consumed sibling path (present_levels[] instead of
# missing_levels[]; touches_left instead of touches_anterior) -- both
# siblings sit in that rule's own catalogue-derived feature_paths (coverage
# reads present_levels[] unconditionally even though its consumer is an
# opt-in check that ships disabled; border reads every face symmetrically),
# so no path-consumption or rule-identity check this codebase can run
# distinguishes "the field that happens to be read" from "the field that
# drives detection for this corpus case". That distinction is a judgement
# about the code's intent, not a measurable fact, so it is not asserted
# here -- see the module docstring's discipline (Testing Strategy: "anything
# checkable is checked, and nothing else is dressed up as checked").
# =========================================================================== #


def _paths_named_in_mechanism(mechanism: str, paths) -> set:
    """Real (non-empty-string) catalogue paths that appear verbatim as a
    substring of *mechanism*. Paths are already distinctive dotted/bracketed
    strings (e.g. ``stage3.monotonic_consistency.non_monotonic_pairs[]``),
    so plain substring containment is specific enough -- unlike a bare
    rule_id or case_id, which needs the word-boundary guard in
    :func:`_token_in_mechanism`."""
    return {p for p in paths if p and p in mechanism}


def test_ac31_named_feature_path_is_consumed_by_one_of_the_modes_declared_rules(matrix):
    """Real check (1) above. The search universe per mode is that mode's own
    ``anchor_paths`` (so a mechanism naming the anchor -- the pre-fix mode-4
    shape -- is still recognised as a *named* path, not silently skipped
    because no rule happens to consume it) union every rule's AC23
    ``feature_paths`` (so a genuinely rule-consumed path is recognised too).
    For every path a mechanism names from that universe, at least one of the
    mode's own declared rules must actually consume it -- a path that is
    only the mode's anchor, and consumed by none of the mode's declared
    rules, fails here."""
    d = matrix
    modes = _mode_records(d)
    rules = _rule_records(d)
    assert modes and rules

    all_rule_consumed_paths = {p for r in rules.values() for p in r["feature_paths"]}
    assert all_rule_consumed_paths, "expected at least one rule-consumed feature path"

    import segfacet.failure_modes as failure_modes_module

    checked_any_path = False
    checked_any_co_detection = False
    for mode, record in modes.items():
        mechanism = record["mechanism"]
        declared_rules = set(record["rules"])
        if mode in PROPOSED_MODES:
            # Reconciled (item 147, 2026-09-04): a `proposed` mode carries an
            # authored mechanism sentence (naming its hypothesised inputs and
            # why no rule exists yet -- AC9) even though it has zero declared
            # rules, by design. "Check (1)" above (a named path must be
            # consumed by one of the mode's declared rules) is therefore
            # structurally inapplicable here: skip the consumption check, but
            # assert the mechanism is non-empty now rather than the
            # empty-string absence this test asserted before item 147
            # authored one. Reconciled again (item 150, 2026-09-14): which
            # modes those are is derived, not the hardcoded "10".
            assert declared_rules == set(), mode
            assert mechanism, mode
            continue
        assert declared_rules, mode

        # Reconciled (item 150, 2026-09-14): a mechanism sentence may also
        # name a path belonging to a rule that CO-DETECTS the mode -- the
        # sign-off records co-detection rather than suppressing it, and modes
        # 1 and 2 are authored precisely to say "what fires today is another
        # mode's detector, recorded, not this mode's own". A co-detecting
        # rule is one the specification names in one of this mode's corpus
        # cases' ``expected_firing``; it is still a live, checkable identity,
        # so the check widens to that set rather than being switched off.
        co_detecting_rules = {
            rule_id
            for case in failure_modes_module.SPECIFICATION[mode].corpus_cases
            for rule_id in case.expected_firing
        }
        permitted_rules = declared_rules | co_detecting_rules

        search_universe = set(record["anchor_paths"]) | all_rule_consumed_paths
        named_paths = _paths_named_in_mechanism(mechanism, search_universe)
        for path in named_paths:
            checked_any_path = True
            consuming = {rid for rid in permitted_rules if path in rules[rid]["feature_paths"]}
            assert consuming, (mode, path, sorted(permitted_rules))
            if not consuming & declared_rules:
                checked_any_co_detection = True

    assert checked_any_path, "expected >=1 mode mechanism to name a real, resolvable feature path"
    assert checked_any_co_detection, (
        "expected >=1 mechanism to name a co-detecting rule's path -- the "
        "widening above asserts nothing if nothing exercises it"
    )


def test_adv_ac31_named_anchor_path_not_consumed_by_declared_rule_is_detectable(
    matrix, matrix_anchor_not_consumed_bogus_mechanism
):
    """Reproduces the pre-fix mode-4 defect directly: naming a real,
    resolvable path (the mode's own anchor) that none of the mode's declared
    rules actually consumes must be distinguishable from a genuine claim --
    demonstrating check (1) above would have failed it. Re-pointed (item 150)
    onto mode 8, which carries that configuration after the sign-off's
    2026-09-15 revision; see ``matrix_anchor_not_consumed_bogus_mechanism``.

    The fixture assumptions are asserted, not assumed: the mode's anchor
    exists, its declared rules do not consume it, and -- since check (1) now
    also permits a co-detecting rule's paths -- the mode designates no corpus
    case at all, so the widening cannot rescue the bogus claim either."""
    import segfacet.failure_modes as failure_modes_module

    mode = _ANCHOR_NOT_CONSUMED_MODE
    before = _mode_record(matrix, mode)
    declared_rules = set(before["rules"])
    assert declared_rules == {"reference_delta"}, declared_rules
    assert failure_modes_module.SPECIFICATION[mode].corpus_cases == (), mode

    assert before["anchor_paths"], mode
    bogus_path = before["anchor_paths"][0]
    assert bogus_path == "stage3.monotonic_consistency.is_monotonic", bogus_path

    rules_before = _rule_records(matrix)
    assert bogus_path not in rules_before["reference_delta"]["feature_paths"], (
        "fixture assumption violated: reference_delta now consumes this anchor path"
    )

    d = matrix_anchor_not_consumed_bogus_mechanism
    patched = _mode_record(d, mode)
    rules = _rule_records(d)
    named_paths = _paths_named_in_mechanism(patched["mechanism"], set(patched["anchor_paths"]))
    assert bogus_path in named_paths

    consuming = {rid for rid in patched["rules"] if bogus_path in rules[rid]["feature_paths"]}
    assert not consuming, (
        "check (1) must fail here: the mechanism names a path none of the "
        "mode's declared rules consume"
    )


_MEASURED_FINDINGS_RE = re.compile(r"measured:\s*findings\s*==\s*\[([^\]]*)\]")


def _parse_measured_findings_claim(mechanism: str):
    """Extract the rule_id set from a mechanism's ``(measured: findings ==
    [...])`` annotation -- the machine-checkable idiom 0db0fca's fix
    introduced for modes 1 and 2 -- or ``None`` if the mechanism carries no
    such annotation."""
    match = _MEASURED_FINDINGS_RE.search(mechanism)
    if match is None:
        return None
    inner = match.group(1)
    return {item.strip().strip("'\"") for item in inner.split(",") if item.strip()}


def test_ac31_measured_findings_claim_matches_the_live_pipeline_firing_set(matrix):
    """Real check (2) above. For every mode whose mechanism carries a
    ``(measured: findings == [...])`` claim, drive the corpus case the
    mechanism names through the same public harness
    tests/test_041_regression_suite.py drives
    (segfacet.synth.regression.pipeline_findings) and assert the live fired
    rule_id set equals exactly what the sentence claims. Modes 1 and 2 carry
    this annotation today; a future mode's sentence adopting the same idiom
    is verified automatically, with no per-mode literal in this test.

    Reconciled (item 150, 2026-09-14): no shipped mechanism carries the idiom
    any more -- the sign-off re-authored every sentence -- so the ">= 1
    shipped claim" non-vacuity guard would fail on an authoring choice rather
    than a regression. It is replaced by a liveness check on the checker
    itself (see the comment at the end of the body), which keeps the test
    able to fail; the verification loop is unchanged and picks up the first
    mechanism that adopts the idiom again."""
    from segfacet.synth.corpus import load_manifest
    from segfacet.synth.regression import pipeline_findings

    manifest = load_manifest()
    cases_by_id = {c["case_id"]: c for c in manifest.get("cases", [])}
    assert cases_by_id, "expected a non-empty corpus manifest"

    d = matrix
    modes = _mode_records(d)
    assert modes

    for mode, record in modes.items():
        claim = _parse_measured_findings_claim(record["mechanism"])
        if claim is None:
            continue

        case_ids_for_mode = {
            cid for cid, case in cases_by_id.items() if case.get("failure_mode") == mode
        }
        named_case_ids = {
            cid for cid in case_ids_for_mode if _token_in_mechanism(cid, record["mechanism"])
        }
        assert named_case_ids, (mode, record["mechanism"])

        for case_id in named_case_ids:
            case = cases_by_id[case_id]
            if case.get("detection") != "pipeline":
                continue
            actual_rule_ids = {f.rule_id for f in pipeline_findings(case)}
            assert actual_rule_ids == claim, (mode, case_id, sorted(actual_rule_ids), sorted(claim))

    # Liveness (item 150, 2026-09-14). The loop above is conditional on a
    # mechanism carrying the idiom, and after the sign-off re-authored every
    # mechanism sentence no shipped one does -- the two sentences that
    # introduced it (the old modes 1 and 2) were replaced by sentences that
    # say what fires as a co-detection in prose instead. Asserting ">= 1
    # shipped claim" would now pin an authoring style the catalogue is free
    # not to use; asserting nothing would leave a silently dead checker. So
    # the check itself is exercised here against a claim built from a live
    # measurement, in both directions: a true claim passes, and the same
    # claim with one rule added fails.
    pipeline_case = next(
        case
        for case_id, case in sorted(cases_by_id.items())
        if case.get("detection") == "pipeline" and case.get("failure_mode")
    )
    measured = {f.rule_id for f in pipeline_findings(pipeline_case)}
    assert measured, (pipeline_case["case_id"], "expected a firing set to build a claim from")

    truthful = "(measured: findings == [%s])" % ", ".join(sorted(repr(r) for r in measured))
    assert _parse_measured_findings_claim(truthful) == measured, truthful

    overclaimed = "(measured: findings == [%s])" % ", ".join(
        sorted(repr(r) for r in measured | {"__no_such_rule__"})
    )
    assert _parse_measured_findings_claim(overclaimed) != measured, overclaimed


def test_adv_ac31_measured_findings_claim_overclaiming_a_rule_is_detectable(monkeypatch):
    """Reproduces the pre-fix mode-2 defect directly: claiming a rule
    ('bounds', 'reference_delta') fires on the plain-pipeline corpus case
    when it structurally cannot without an attached reference --
    demonstrating check (2) above would have failed it."""
    from segfacet.synth.corpus import load_manifest
    from segfacet.synth.regression import pipeline_findings

    manifest = load_manifest()
    cases_by_id = {c["case_id"]: c for c in manifest.get("cases", [])}
    case = cases_by_id["mode2_fragment"]
    assert case.get("detection") == "pipeline"

    actual_rule_ids = {f.rule_id for f in pipeline_findings(case)}
    assert actual_rule_ids == {"fragmentation"}, actual_rule_ids

    overclaiming_mechanism = (
        "caught independently by bounds' magnitude thresholds, "
        "fragmentation's component-count checks, and reference_delta's "
        "cohort-relative scoring on mode2_fragment (measured: findings == "
        "['bounds', 'fragmentation', 'reference_delta'])."
    )
    claim = _parse_measured_findings_claim(overclaiming_mechanism)
    assert claim == {"bounds", "fragmentation", "reference_delta"}
    assert claim != actual_rule_ids, (
        "check (2) must fail here: the mechanism claims a firing set the "
        "live pipeline does not produce"
    )


# =========================================================================== #
# Completeness gap (0db0fca): a rule declaring only modes outside
# MODE_ANCHOR_PATHS' key set must make rule_to_mode report a hole, never
# complete: true
# =========================================================================== #


def test_adv_rule_declaring_only_an_uncatalogued_mode_makes_rule_to_mode_a_hole(
    matrix_uncatalogued_mode_rule_registered,
):
    """Before 0db0fca, a rule declaring only modes outside
    feature_docs.MODE_ANCHOR_PATHS' key set (e.g. modes=(9,)) was
    'declared' by declaration_state alone, so rule_to_mode reported it
    complete though the rule targets no catalogued mode -- exactly this
    module's own definition of a rule -> mode hole. Registering such a rule
    now must report the hole, naming the rule.

    Reconciled (item 146, 2026-09-03): mode 9 is now a key of
    failure_modes.SPECIFICATION (item 146's A7 moves catalogue.py's
    known-mode source there, from feature_docs.MODE_ANCHOR_PATHS), so a rule
    declaring modes=(9,) is no longer outside the catalogue and
    rule_declaration_conflicts() stops reporting it -- rule_to_mode would
    stay complete. The stub moves to a mode absent from *both*
    SPECIFICATION and MODE_ANCHOR_PATHS, derived live rather than assumed by
    literal, so this test tracks whichever id is actually free (see
    ``matrix_uncatalogued_mode_rule_registered``)."""
    d, uncatalogued_mode = matrix_uncatalogued_mode_rule_registered
    assert d["directions"]["rule_to_mode"]["complete"] is False
    holes = d["directions"]["rule_to_mode"]["holes"]
    assert any("__item138_uncatalogued_mode__" in str(hole) for hole in holes), holes

    rules = _rule_records(d)
    record = rules["__item138_uncatalogued_mode__"]
    assert record["declaration_state"] == "declared"
    assert record["modes"] == [uncatalogued_mode]

    # The mode -> rule direction is untouched by this defect: the picked
    # mode is not catalogued at all, so it never appears as a mode -> rule
    # hole (that direction's holes are catalogued-mode ids and unregistered
    # corpus-designated rule ids, neither of which this mode is).
    assert str(uncatalogued_mode) not in d["directions"]["mode_to_rule"]["holes"]


# =========================================================================== #
# AC32: mode 1's rule list contains every rule a feature-level derivation
# requires
# =========================================================================== #


def test_ac32_mode1_rule_list_contains_every_feature_derived_required_rule(matrix):
    """Reconciled for item 154: mode 1's anchor no longer includes
    ``stage3.per_label_offsets[].offset_mm`` (only ``mislabel`` consumed it,
    declared ``bookkeeping``, not ``signal`` -- it serves no mode), so no
    ``reference_delta``-tracked feature anchors any mode any more and
    ``required_modes`` is empty. The derivation and the loops over
    ``required_modes`` stay so a future anchor change is still caught; the
    loops are vacuously satisfied today."""
    import segfacet.feature_docs as feature_docs_module
    import segfacet.reference.delta as delta_module

    tracked = delta_module.INGESTED_FEATURES
    assert tracked, "expected a non-empty reference_delta tracked-feature vocabulary"

    feature_record_path = {
        name: "per_label.{label}.geometry." + name for name in tracked if name != "spline_offset_mm"
    }
    feature_record_path["spline_offset_mm"] = "stage3.per_label_offsets[].offset_mm"
    assert set(feature_record_path) == set(tracked)

    anchor_modes_by_path: dict = {}
    for mode, paths in feature_docs_module.MODE_ANCHOR_PATHS.items():
        for path in paths:
            anchor_modes_by_path.setdefault(path, set()).add(mode)

    required_modes: set = set()
    for feature_name in tracked:
        required_modes |= anchor_modes_by_path.get(feature_record_path[feature_name], set())
    # Item 154: no tracked feature anchors any mode now that mode 1's
    # offset_mm anchor is dropped. Asserted as equality (not skipped) so a
    # later anchor change that re-populates this set is still caught.
    assert required_modes == set(), required_modes

    d = matrix
    for mode in required_modes:
        record = _mode_record(d, mode)
        assert "reference_delta" in record["rules"], (mode, record["rules"])

    reference_delta_record = _rule_records(d)["reference_delta"]
    for mode in required_modes:
        assert mode in reference_delta_record["modes"], (mode, reference_delta_record["modes"])


def test_adv_ac32_renarrowed_reference_delta_declaration_fails_the_matrix_level_check(
    matrix_reference_delta_renarrowed,
):
    """The false-premised shape commit b1c593c corrected -- narrowing
    reference_delta back to modes=(2,) must make the matrix under-report
    mode 1's rule list, from the feature-level derivation rather than any
    literal."""
    mode1 = _mode_record(matrix_reference_delta_renarrowed, 1)
    assert "reference_delta" not in mode1["rules"], mode1["rules"]


# =========================================================================== #
# AC33 (item 138) -- reconciled (item 149, 2026-09-04, AC11): the mode ->
# read-path list no longer declares rule granularity. ``granularity`` moves
# from ``"rule"`` to ``"signal"`` -- a path's presence in ``read_paths``
# means a declaring rule classifies that path ``"signal"``, not merely that
# some declaring rule reads it at all -- and the qualifier field (renamed
# ``read_paths_qualifier``, since ``feature_paths`` itself is gone, AC8)
# carries the new sentence. The retired rule-granular sentence must appear
# in neither the JSON qualifier nor the committed markdown.
# =========================================================================== #


@pytest.mark.parametrize("mode", MODES)
def test_ac33_mode_read_path_list_declares_signal_granularity(mode, matrix):
    record = _mode_record(matrix, mode)
    assert record["granularity"] == "signal", mode
    qualifier = record["read_paths_qualifier"]
    assert "signal" in qualifier, mode
    assert "a rule that targets this mode reads this path" not in qualifier, mode


def test_ac33_committed_markdown_prints_the_signal_qualifier_beside_the_mode_table():
    """Reconciled (item 149, 2026-09-04, AC11): the committed markdown's
    qualifier sentence changes from the retired rule-granular claim to the
    signal-classification one, and states the anchor column is a separate
    one never merged in."""
    lines = _md_lines()
    text = "\n".join(lines)

    mode_header_idx = None
    rule_header_idx = None
    for idx, line in enumerate(lines):
        if mode_header_idx is None and "Pipeline-detected" in line:
            mode_header_idx = idx
        if rule_header_idx is None and "Declared modes" in line:
            rule_header_idx = idx
    assert mode_header_idx is not None, "expected a mode table header"
    assert rule_header_idx is not None, "expected a rule table header"
    assert rule_header_idx > mode_header_idx

    section = "\n".join(lines[mode_header_idx:rule_header_idx])
    assert "a rule that targets this mode reads this path" not in section
    assert "signal" in section
    assert "never merged in" in section
    assert text  # keep the joined text referenced for clarity of the slice above


# =========================================================================== #
# Edge cases
# =========================================================================== #


def test_adv_singleton_declaring_rule_mode_renders_a_well_formed_row(matrix):
    """A mode whose declaring-rule set is a singleton still renders a
    well-formed row. Item 138 named mode 5 (``coverage`` only); the item-150
    sign-off re-assigned the ids, so the singleton mode is found rather than
    named -- the claim was never about which mode it happened to be."""
    modes = _mode_records(matrix)
    singletons = {mode: r for mode, r in modes.items() if len(r["rules"]) == 1}
    assert singletons, "expected at least one mode declared by exactly one rule"
    for mode, record in sorted(singletons.items()):
        assert record["title"], mode
        assert record["rung"] in RUNGS, (mode, record["rung"])
        assert record["read_paths"], (
            mode,
            "expected a non-empty signal-classified read-path union",
        )


def test_adv_rule_consuming_zero_catalogued_paths_renders_empty_feature_list(
    matrix_zero_read_rule_registered,
):
    """A rule consuming zero catalogued paths renders an empty feature list
    rather than raising."""
    d = matrix_zero_read_rule_registered
    record = _rule_records(d)["__item138_zero_read__"]
    assert record["feature_paths"] == []


# =========================================================================== #
# AC28/AC29 (item 149, 2026-09-04): this module's own call-site budget.
# The cross-module claim (every ``build_matrix()`` call site in *both*
# ``test_138_traceability_matrix.py`` and ``test_149_conformance_report.py``
# sits inside a ``@pytest.fixture``) is asserted once, over both files, in
# ``tests/test_149_conformance_report.py`` -- this test is this module's own
# local half: its AST call-site count equals its own budget constant and
# that constant is ``<= 20``.
# =========================================================================== #


def _is_fixture_decorator(node: ast.expr) -> bool:
    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Attribute):
        return target.attr == "fixture"
    if isinstance(target, ast.Name):
        return target.id == "fixture"
    return False


def _is_build_matrix_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr == "build_matrix"
    if isinstance(func, ast.Name):
        return func.id == "build_matrix"
    return False


def _build_matrix_call_sites(tree: ast.Module):
    """Yield ``(lineno, enclosing_is_fixture)`` for every ``build_matrix()``
    call in *tree*, at any nesting depth."""
    results = []

    def _walk(node, enclosing_is_fixture):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_fixture = any(_is_fixture_decorator(d) for d in child.decorator_list)
                _walk(child, is_fixture)
            else:
                if _is_build_matrix_call(child):
                    results.append((child.lineno, enclosing_is_fixture))
                _walk(child, enclosing_is_fixture)

    _walk(tree, False)
    return results


def test_ac29_build_matrix_call_site_budget_holds_and_all_sites_are_fixtured():
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    sites = _build_matrix_call_sites(tree)

    assert len(sites) == _BUILD_MATRIX_CALL_SITE_BUDGET, (
        len(sites),
        _BUILD_MATRIX_CALL_SITE_BUDGET,
    )
    assert _BUILD_MATRIX_CALL_SITE_BUDGET <= 20, _BUILD_MATRIX_CALL_SITE_BUDGET

    non_fixtured = [lineno for lineno, in_fixture in sites if not in_fixture]
    assert non_fixtured == [], non_fixtured
