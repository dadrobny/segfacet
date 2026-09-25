<!-- aide-template: item 2 -->
# Item 182 — The catalogue's corpus-derived rule→mode map read from the committed cases

> **Created:** 2026-09-25 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (maintenance)
> **Queue:** [`../queue/queue-024.md`](../queue/queue-024.md) · Item 182
> **Objectives:** G8
> **Suggested branch:** `aide/182-the-catalogue-s-corpus-derived`

---

## Description

`segfacet.catalogue._scan_synth_rule_mode_map` (public wrapper
`scan_synth_rule_mode_map`) is the "corpus-derived" `rule_id -> failure
mode(s)` map. Two consumers read it: mechanism C of `build_catalogue` (the
`"rule_mode_map"` evidence term) and the corpus → declaration direction of
`rule_declaration_conflicts`. Today it is built by an AST scan of literal
`Expectation(failure_mode=<int>, expected_rule_ids=frozenset({...}))` calls in
`src/segfacet/synth/*.py`, not from the corpus cases that are committed. Two
consequences follow (`insights.md`, `gap` entry of item 176, 2026-09-24):

- An operator branch that no committed case applies still designates
  rule→mode pairs. Measured 2026-09-24: `fuse`'s unbridged literal (mode 2 →
  `coverage`, `fragmentation`) beside a `fuse_adjacent` case expecting `()`
  gave two false `rule_declaration_conflicts`. Item 176 worked around it by
  making `fuse`'s `expected_rule_ids` a branch-computed local, which the scan
  cannot read.
- A designation that is not a literal drops out in silence. That is the same
  workaround seen from the other side.

This item re-derives the map from the committed geometric manifest
(`tests/corpus/manifest.json`, read through `segfacet.synth.corpus.load_manifest`).
Every **failure-kind** case contributes each rule in its `expected_rule_ids`,
mapped to that case's `failure_mode`. The function names stay, so every
existing caller and every monkeypatch of `_scan_synth_rule_mode_map` still
works.

**Not in scope:**

- The intensity manifest. The map stays geometric-only (A1).
- Any change to `rule_declaration_conflicts`'s logic, including the
  co-detection exemption. Only the map it reads changes source.
- Any change to an operator's runtime `Expectation`.
- Regenerating `docs/aide/feature_catalogue.generated.*`. The derived map is
  equal to today's on the shipped tree (A2), so both artifacts stay byte-unchanged.

## Acceptance Criteria

- [ ] **AC1: The map equals the committed manifest's failure-case designations.**
  `catalogue.scan_synth_rule_mode_map()` equals the dict the test recomputes
  from `segfacet.synth.corpus.load_manifest()["cases"]`. The recomputation
  takes every case whose `segfacet.synth.perturbation.corpus_case_kind(case)`
  is `"failure"` and maps each `rule_id` in its `expected_rule_ids` to the
  sorted tuple of distinct `failure_mode` values across those cases. A rule
  that no failure case designates is absent.
- [ ] **AC2: Dropping a committed case's expected rule removes its pair.** Take a
  `(rule_id, mode)` pair that exactly one committed failure case designates.
  Patch `segfacet.synth.corpus.load_manifest` to return a deep copy of the
  committed manifest with that `rule_id` removed from that case's
  `expected_rule_ids`. `mode` is then absent from
  `scan_synth_rule_mode_map().get(rule_id, ())`.
- [ ] **AC3: An `Expectation` literal in synth source that no case applies adds no pair.**
  Point `segfacet.synth.__file__` at a temporary directory. That directory holds
  a module containing `Expectation(failure_mode=2, expected_rule_ids=frozenset({"coverage", "fragmentation"}))`,
  the shape of `fuse`'s pre-item-176 unbridged literal. `scan_synth_rule_mode_map()`
  then still equals the AC1 recomputation from the committed manifest.
- [ ] **AC4: The planted `fuse` literal causes no conflict.** Under the same planted
  directory as AC3, `catalogue.rule_declaration_conflicts()` equals its value
  without the plant.
- [ ] **AC5: `rule_declaration_conflicts` reads the manifest-derived map.** Patch
  `segfacet.synth.corpus.load_manifest` to return the committed manifest plus
  one appended failure-kind case whose `expected_rule_ids` is `[R]` and whose
  `failure_mode` is `M`. R is a registered rule with a declaration. M is a key
  of `failure_modes.SPECIFICATION` that R does not declare, and R is in no
  `expected_firing` of M's `corpus_cases`. The test selects R and M from live
  state. `rule_declaration_conflicts()` then contains a message naming R and
  reading `corpus designates failure mode M`.
- [ ] **AC6: `build_catalogue`'s mechanism C reads the manifest-derived map.** Patch
  `segfacet.synth.corpus.load_manifest` to return the committed manifest with
  every case's `expected_rule_ids` emptied. No entry of
  `build_catalogue(strict=True)` then carries `"rule_mode_map"` in its
  `mode_evidence`.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

- **A1: Geometric manifest only.** "The cases that are actually committed" is
  read as the cases of `tests/corpus/manifest.json`, the corpus the literal
  scan covered. The intensity manifest is not read, for three reasons:
  - Its cases carry `expected_firing`, not `expected_rule_ids`.
  - Adding its `intensity: (16,)` pair changes `catalogue_to_dict(build_catalogue())`,
    as item 156 A4 measured on 2026-09-16. That would regenerate both
    `docs/aide/feature_catalogue.generated.*` files and re-pin
    `tests/test_103_feature_catalogue.py`'s `_RULE_MODE_MAP`.
  - On the shipped tree it has nothing for `rule_declaration_conflicts` to
    find, because `intensity` declares 16 (item 156 A4).

  The docstrings keep stating the geometric-only limit. See **Left open**.
- **A2: The derived map is unchanged on the shipped tree.** Measured
  2026-09-25 on this branch's base, both sources give the same map:
  `{fragmentation: (1, 3, 4), bounds: (3,), coverage: (6,), overlap: (15,),
  mislabel: (1, 9), sequence: (9,)}`. The literal scan reads it from the
  synth sources, and the failure-kind cases of the committed manifest give the
  same thing. `rule_declaration_conflicts()` is `()` under both. So
  `test_103`'s `_RULE_MODE_MAP` pin, the committed catalogue artifacts and
  every existing conflicts test stay green with no edit. The builder hands
  back if a fresh regeneration of the catalogue differs.
- **A3: "Failure-kind" is decided by `corpus_case_kind`, never by comparing `failure_mode` with 0.**
  The two `condition` cases (`crop_at_border` → `border`, `crop_fov_si` →
  `bounds`) and the `clean_control` case carry `failure_mode == 0`. Letting them
  contribute would add a mode-0 designation and create false conflicts.
  `tests/test_155_corpus_case_kind.py` scans `src/segfacet/**` and rejects any
  zero comparison on a `failure_mode` access outside
  `synth/perturbation.py`. `corpus_case_kind` raises `ValueError` on a missing
  or unknown `kind`. That is propagated, not caught.
- **A4: The manifest is looked up at call time.** The implementation reaches
  `load_manifest` through the `segfacet.synth.corpus` module at call time, not
  through a name bound at import. That way a test's
  `monkeypatch.setattr(segfacet.synth.corpus, "load_manifest", ...)` is seen
  (AC2, AC5, AC6). Heavy imports stay deferred into the function body, per the
  module's determinism contract.
- **A5: Both function names are kept.** `tests/test_137_*`,
  `tests/test_147_*` and `tests/test_156_*` monkeypatch
  `_scan_synth_rule_mode_map`. `tests/test_103_*`, `test_136_*` and
  `test_148_*` call one of the two names. Renaming either (the "scan" in the
  name is now a misnomer) is churn that no consumer needs.

## Implementation Steps

1. In `src/segfacet/catalogue.py`, replace the body of
   `_scan_synth_rule_mode_map`:
   - Import `segfacet.synth.corpus` and `corpus_case_kind` /
     `CASE_KIND_FAILURE` from `segfacet.synth.perturbation` inside the
     function.
   - Iterate `corpus.load_manifest().get("cases", [])`. Skip any case where
     `corpus_case_kind(case) != CASE_KIND_FAILURE`.
   - For each `rule_id` in `case.get("expected_rule_ids", ())`, add
     `case["failure_mode"]` to a `defaultdict(set)`.
   - Return `{rule_id: tuple(sorted(modes))}` as today.

   This reuses the existing `load_manifest` and `corpus_case_kind`. It adds
   no dependency and no new helper.
2. Delete `_extract_frozenset_string_elements`. Its only caller was the
   literal scan.
3. Rewrite the docstrings that describe the literal scan:
   - Mechanism C in the module docstring (lines ~30–38).
   - `_scan_synth_rule_mode_map` and `scan_synth_rule_mode_map`.
   - The `# Mechanism C` comment in `build_catalogue`.

   Say that the map is read from the committed geometric manifest's
   failure-kind cases, and that it stays geometric-only (A1). Keep the item
   156 consumer note. Leave `rule_declaration_conflicts`'s code unchanged.
4. In `src/segfacet/synth/component_shape.py`, rewrite only the two-line
   comment above `FusePerturbation.apply`'s `Expectation(...)` call ("no
   literal here designates mode 2 to a rule, so catalogue's literal-only scan
   reads none from `fuse`"). It becomes false once the map stops reading
   literals. State that the designation is branch-computed and the catalogue
   reads the committed cases (item 182). Do not change the runtime values.
5. Do not regenerate `docs/aide/feature_catalogue.generated.*`. Run
   `python -m segfacet.catalogue` into a scratch directory, confirm it is
   byte-identical to the committed pair (A2), and hand back if it is not.

## Authorised paths

**May change:**

- `src/segfacet/catalogue.py` — the map's derivation, the deleted helper, and the docstrings
- `src/segfacet/synth/component_shape.py` — the comment above `fuse`'s `Expectation` call only
- `tests/test_182_corpus_derived_rule_mode_map.py` — the AC tests and the named adversarial case
- `tests/test_103_feature_catalogue.py` — comment reconciliation only (the AC13 section header and the `_RULE_MODE_MAP` comment say the map is read from `synth/*.py` literals)
- `tests/test_136_rule_mode_declarations.py` — comment reconciliation only (the item-150 note above AC8 says the same)

**Asserts against:**

- `tests/corpus/manifest.json` — AC1 recomputes the expected map live from it, and AC2/AC5/AC6 patch a deep copy of it
- `docs/aide/feature_catalogue.generated.json` — must stay byte-unchanged (A2); `test_103`'s AC19 compares it with a fresh regeneration
- `docs/aide/feature_catalogue.generated.md` — as above

## Testing Strategy

New module `tests/test_182_corpus_derived_rule_mode_map.py`, one test per AC:

- Every patch uses `monkeypatch`. Import `segfacet.synth.corpus` before
  patching `segfacet.synth.__file__`, so the corpus module's `MANIFEST_PATH` is
  already bound.
- For AC3/AC4, the planted directory is a `tmp_path` holding an `__init__.py`
  and one `.py` file with the literal. The test also checks its own premise:
  with the plant in place, the file really does contain an `Expectation(...)`
  call with a literal `failure_mode=2` and a literal `frozenset` of the two ids.
- AC6 calls `build_catalogue` once, inside the one test that needs it.
- AC2 and AC5 pick their pair (AC2) and their R and M (AC5) from live state,
  never from literals. Each asserts that a qualifying choice exists before it
  uses one. A corpus change in queue-025 can then change which pair is
  chosen, but it cannot make the test vacuous.

Adversarial case (write this one and no other):

- `missing-kind-raises`: patch `load_manifest` to add a case that has no
  `kind` key but has `expected_rule_ids`. `scan_synth_rule_mode_map()` then
  raises `ValueError`, and the message names that `case_id`. This guards
  against a malformed case being skipped in silence, which is the failure
  shape this item exists to remove (A3).

**Existing tests to reconcile:** none needs an assertion change (A2). Stale
comments only:

- `tests/test_103_feature_catalogue.py`: the AC13 section header "derived
  from synth/", and the `_RULE_MODE_MAP` comment "the modes `synth/*.py`'s
  `Expectation(...)` literals attribute".
- `tests/test_136_rule_mode_declarations.py`: the item-150 note, "from the
  `Expectation(...)` literals in `src/segfacet/synth/*.py`".

Grep made 2026-09-25: no test plants an `Expectation` literal or asserts that
the scan reads synth sources.

## Dependencies

None. The `fuse` workaround this item makes unnecessary is already merged.

**Downstream:** queue-025's D3 items change rule→mode declarations and corpus
designations. Their `rule_declaration_conflicts` results read this map, so the
queue orders item 182 first.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether the map should also read the intensity manifest's
  `expected_firing`. Doing so changes the committed catalogue artifacts and
  `test_103`'s pinned map (A1). The only gain is an `intensity: (16,)`
  evidence term that the rule's own declaration already supplies. A later item
  can take it together with a catalogue regeneration.
- **Left open:** whether `fuse`'s branch-computed `expected_rule_ids` should
  go back to literals now that literals no longer feed the map. It does not
  matter to any consumer, and item 183 is editing the same method.
