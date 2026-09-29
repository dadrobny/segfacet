<!-- aide-template: item 3 -->
# Item 200 — The bar checker's condition 2 made existential and detector-granular

> **Created:** 2026-09-29 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (D4)
> **Queue:** [`../queue/queue-027.md`](../queue/queue-027.md) · Item 200
> **Objectives:** G2, G8
> **Suggested branch:** `aide/200-the-bar-checker-s-condition`

---

## Description

`segfacet.traceability.bar_conditions(mode_id)` computes conditions 1–5 of
roadmap Stage 32's "fully specified end to end" bar. Condition 2 reads, in the
roadmap and verbatim in `traceability.BAR_CONDITIONS`: "At least one committed
synthetic fixture expresses the mode, and its expected firing set names at
least one of the mode's own intended rules and agrees with the measured
firing." Today it is computed as:

- every corpus case attached to the mode agrees
  (`failure_modes.case_agrees`), **and**
- at least one case's `expected_firing` intersects the rule ids of the mode's
  `intended_rules`.

That has two defects, both routed to this item by roadmap Stage 33 D4:

1. **Universal where the roadmap is existential** (`insights.md`, insight
   2026-09-20-74f1). An attached case that does not express the mode, and
   disagrees, holds condition 2 down. That every attached case agrees is the
   specificity ratchet's job (item 163), and it also stays inside condition 5
   (`derive_status` requires every case to agree).
2. **Rule-id-granular where condition 4 is detector-granular** (`insights.md`,
   insight 2026-09-20-8462). A case whose firing rule is one of the mode's own
   rules, but which fires only through a detector serving another mode, counts
   as expressing the mode.

**The change.** Condition 2 becomes: at least one corpus case of the mode
both agrees (`case_agrees`) and whose measured findings carry a
`(rule_id, detector_id)` pair that is one of the mode's own intended pairs,
`{(edge.rule_id, d) for edge in mode.intended_rules for d in edge.detector_ids}`.
Its `subjects` are those cases' ids, in `mode.corpus_cases` order. The
measured pairs come from a new public `failure_modes.measured_detector_firing(case)`,
built on the same findings `measured_firing` already obtains.

**Not in scope.** Conditions 1, 3, 4 and 5 are unchanged. `derive_status` and
its `_demonstrates` helper are unchanged: lifecycle status stays rule-id
granular and universal (a separate contract, pinned by
`tests/test_151_stage30_validation.py`). The `BAR_CONDITIONS` text is the
roadmap's and is not edited. No generated artifact reads `bar_conditions`, so
nothing is regenerated. No rule, detector, corpus case or expected set moves.

## Acceptance Criteria

Terms used below:

- **`fm`** is `segfacet.failure_modes`, **`SPEC`** is `fm.SPECIFICATION`.
- **`cat`** is `segfacet.catalogue.build_catalogue(strict=True)`.
- **`c2(m)`** is the element with `number == 2` of
  `segfacet.traceability.bar_conditions(m, catalogue=cat)`.
- **`own(m)`** is
  `{(e.rule_id, d) for e in SPEC[m].intended_rules for d in e.detector_ids}`.
- **`case(m, X)`** is the element of `SPEC[m].corpus_cases` whose
  `case_id == X`.
- **`findings(c)`** is the findings of corpus case `c` through the
  `segfacet.synth.regression` helper its manifest entry's `detection` names
  (`pipeline_findings`, `reconstructed_findings` or
  `intensity_pipeline_findings`), the manifest being
  `segfacet.synth.corpus.load_manifest()` for `c.corpus == "geometric"` and
  `segfacet.synth.intensity.load_intensity_manifest()` for `"intensity"`.
- **`M4(cases)`** means `SPEC` monkeypatched so that entry 4 is
  `dataclasses.replace(SPEC[4], corpus_cases=cases)`.
- **`ISL`** is `case(4, "inject_islands")`. **`FRAG`** is `case(1, "fragment")`,
  whose measured findings fire `fragmentation` only through its `components`
  detector, which serves mode 1 (A3).

- [ ] **AC1: `measured_detector_firing` returns the measured pairs.** For
  every corpus case `c` of `SPEC[3]`, `SPEC[4]` and `SPEC[16]`,
  `fm.measured_detector_firing(c) == tuple(sorted({(f.rule_id, f.detector_id) for f in findings(c)}))`.
- [ ] **AC2: condition 2 is existential.** Under
  `M4((ISL, dataclasses.replace(FRAG, expected_firing=())))`, `c2(4).met is True`.
- [ ] **AC3: a case firing a mode's rule through another mode's detector is
  not a subject.** Under `M4((ISL, FRAG))`, `c2(4).subjects == ("inject_islands",)`.
- [ ] **AC4: such a case alone does not meet condition 2.** Under
  `M4((FRAG,))`, `c2(4).met is False`.
- [ ] **AC5: condition 2 equals its live recomputation for every mode.** For
  every `m` in `SPEC`, `c2(m).subjects == tuple(c.case_id for c in SPEC[m].corpus_cases if fm.case_agrees(c) and own(m) & set(fm.measured_detector_firing(c)))`
  and `c2(m).met == bool(c2(m).subjects)`.

Why each is written:

- AC1 pins the new producer against the findings it is built from. AC5
  recomputes condition 2 through it, so a wrong pair set would pass AC5 and
  fail here. Modes 3, 4 and 16 cover both corpora and both `detection`
  dispatch arms the specification's cases use today (`pipeline` and
  `intensity_pipeline`; see A2).
- AC2 is insight 2026-09-20-74f1. The attached `FRAG` copy expects nothing
  and fires `fragmentation`, so it disagrees; the old universal predicate
  reads `met is False` here.
- AC3 is the queue's "one expressing case and one agreeing, non-expressing
  case". `FRAG` agrees and names `fragmentation`, one of mode 4's own rule
  ids, so the old predicate lists it. It is the only criterion that catches
  `subjects` computed at rule-id granularity while `met` is computed on
  pairs, because on today's live corpus the two granularities coincide for
  every mode (A4).
- AC4 is insight 2026-09-20-8462 and the queue's "a case whose own rule fires
  only through another mode's detector does not meet it". The old predicate
  reads `met is True` here.
- AC5 is the live equality over the shipped specification, the shape later
  consumers (items 203, 204) read.

None of these closes a Stage 33 acceptance criterion. Criterion 1 is closed
by items 203 and 204, which read this checker.

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
measured value was taken on 2026-09-29 with `.venv/bin/python` on this branch
at commit `04b180c` (queue-026 merged, so after item 198), by driving each corpus case
through the `segfacet.synth.regression` helpers and reading
`Finding.detector_id`. The working checkout was not edited.

- **A1 (defensible default: "the mode's own intended detectors").** The queue
  says to intersect the measured pairs "with the mode's own intended
  detectors". This is read as every `(rule_id, detector_id)` on the mode's
  `intended_rules` edges, `own(m)` above, proxies included.
  - Condition 2's roadmap text names "the mode's own intended rules" with no
    proxy exclusion; only condition 4 excludes `bounds` and
    `reference_delta`, and only condition 4 requires a single-mode detector.
  - So condition 2 does not reuse condition 4's `qualifying_pairs`. A mode
    could therefore meet condition 2 through a shared or proxy detector while
    its deciding detector fires on no fixture. On today's corpus that does not
    happen for modes 3 and 4 (A4). See **Left open**.
- **A2 (interface pinned: the findings `measured_firing` obtains).**
  `fm.measured_firing(case)` dispatches on `case.corpus` (`"geometric"` /
  `"intensity"`, anything else raises `ValueError` naming the case), then on
  the manifest case's `detection` (`pipeline`, `reconstructed_record`,
  `intensity_pipeline`), and returns sorted distinct `Finding.rule_id`s.
  `Finding.detector_id` has been set by every registered rule since item 164
  (default `""`). The intensity branch reaches
  `load_intensity_manifest` through the module object, which
  `tests/test_146_*`, `test_147_*`, `test_151_*`, `test_156_*` and
  `test_162_*` monkeypatch; the refactor keeps that access. Today no
  specification case uses `reconstructed_record`.
- **A3 (measured: the `FRAG` case).** `fragment` is mode 1's only corpus
  case, `expected_firing == ("fragmentation",)`, agrees, and its measured
  pairs are `(("fragmentation", "components"),)`.
  `fm.modes_for_detector("fragmentation", "components") == (1,)`. Mode 4's
  own pairs are `("bounds", "metric_out_of_range")` and
  `("fragmentation", "islands")`, so `FRAG` names a mode-4 rule id and no
  mode-4 pair.
- **A4 (measured: modes 3 and 4 re-measured live, the queue's requirement).**
  Measured pairs per case, and what condition 2 becomes:

  | Mode | Case | Expected | Agrees | Measured pairs | Own pair hit |
  |---|---|---|---|---|---|
  | 3 | `split` | `neighbour_contact` | yes | `(neighbour_contact, stray_contact)` | `(neighbour_contact, stray_contact)` |
  | 3 | `split_own_label` | `bounds` | yes | `(bounds, metric_out_of_range)` | `(bounds, metric_out_of_range)` |
  | 4 | `inject_islands` | `fragmentation` | yes | `(fragmentation, islands)` | `(fragmentation, islands)` |

  - Mode 3: `c2(3).met is True`, subjects `("split", "split_own_label")`,
    unchanged from the rule-id predicate. `split_own_label` counts only
    through the proxy `bounds` (A1). `split` counts through
    `neighbour_contact/stray_contact`, which is mode 3's condition-4
    deciding detector.
  - Mode 4: `c2(4).met is True`, subjects `("inject_islands",)`, unchanged.
    `fragmentation/islands` is mode 4's condition-4 deciding detector.
  - Conditions 1, 3, 4 and 5 were all met for both modes on the same
    measurement.
  - Every other mode with corpus cases (1, 2, 6, 9, 16) gets the same
    `met` and `subjects` under both predicates. The two granularities do not
    diverge anywhere on today's corpus, which is why AC2–AC4 patch the
    specification.
- **A5:** no human gate, and no environment-gated capability.

## Implementation Steps

1. **`src/segfacet/failure_modes.py` — one findings source.** Turn
   `_measured_firing_geometric` and `_measured_firing_intensity` into
   `_measured_findings_geometric(case)` / `_measured_findings_intensity(case)`
   returning the findings tuple the regression helper produced (bodies
   otherwise unchanged, error messages verbatim). Add a private
   `_measured_findings(case)` holding today's `corpus` dispatch and its
   `ValueError`.
2. **Same file — the two public readers.** `measured_firing(case)` returns
   `tuple(sorted({f.rule_id for f in _measured_findings(case)}))`, unchanged
   in behaviour. Add `measured_detector_firing(case) -> Tuple[Tuple[str, str], ...]`
   returning `tuple(sorted({(f.rule_id, f.detector_id) for f in _measured_findings(case)}))`.
   Add it to `__all__` and to the module docstring's API list beside
   `measured_firing`.
3. **`src/segfacet/traceability.py` — condition 2.** In `bar_conditions`,
   replace the condition-2 block: `own_pairs` as `own(m)`, subjects are the
   `case_id`s of `mode.corpus_cases` (in order) for which
   `failure_modes_module.case_agrees(case)` and
   `own_pairs.intersection(failure_modes_module.measured_detector_firing(case))`
   (short-circuit, so a disagreeing case is not re-measured); `met` is
   `bool(subjects)`. The `detail` string names the rule: cases that agree and
   fire one of the mode's own intended `(rule_id, detector_id)` pairs.
   Update the module docstring's `bar_conditions` paragraph to say condition 2
   is existential and detector-granular (item 200). `BAR_CONDITIONS` is not
   edited.

No dependency is added. Nothing else calls the renamed private helpers.

## Authorised paths

**May change:**

- `src/segfacet/failure_modes.py` — steps 1–2: shared findings source and
  `measured_detector_firing`.
- `src/segfacet/traceability.py` — step 3: condition 2.
- `tests/test_200_bar_condition_2.py` — this item's tests.
- `tests/test_165_mode_4_at_the_bar.py` — reconciliation of
  `test_ac3_condition_2_fixture_expresses_mode_recomputed` (Testing Strategy).

**Asserts against:**

- `tests/corpus/manifest.json` — AC1, AC5: read through
  `segfacet.synth.corpus.load_manifest()` to drive the geometric cases.
- `tests/corpus/intensity/manifest.json` — AC1, AC5: read through
  `segfacet.synth.intensity.load_intensity_manifest()` for mode 16's cases.

## Testing Strategy

Test module: `tests/test_200_bar_condition_2.py`. One module-scoped fixture
builds `build_catalogue(strict=True)` once and every `bar_conditions` call
passes it (the idiom of `tests/test_165_mode_4_at_the_bar.py`). AC2–AC4
monkeypatch `segfacet.failure_modes.SPECIFICATION` with a dict copy whose
entry 4 is `dataclasses.replace`d; `ISL` and `FRAG` are read from the live
`SPECIFICATION`, never hand-built. AC3 and AC4 each also assert their
precondition from the primary source, so they cannot pass vacuously:
`fm.case_agrees(FRAG)` is true, `FRAG`'s measured rule ids intersect
`{e.rule_id for e in SPEC[4].intended_rules}`, and its measured pairs do not
intersect `own(4)`.

Adversarial case, beyond one test per AC:

- `expressing-case-that-disagrees-is-not-a-subject`: under
  `M4((dataclasses.replace(ISL, expected_firing=()),))`, `c2(4).met is False`
  and `c2(4).subjects == ()`. Guards an existential rewrite that drops the
  roadmap's "agrees with the measured firing" half, so a case whose own
  detector fires but whose expected set is wrong would count.

**Existing tests to reconcile:**

- `tests/test_165_mode_4_at_the_bar.py::test_ac3_condition_2_fixture_expresses_mode_recomputed`
  recomputes the retired predicate (universal agreement, rule-id
  intersection). It still passes, because mode 4's one case gives the same
  answer under both (A4), but it pins the old semantics. Rewrite its
  recomputation to AC5's predicate for mode 4, keeping its
  `recomputed_met is True` assertion.
- Checked and left alone: `test_co_detection_alone_fails_condition_2` in the
  same module still holds (with `fragmentation` dropped from mode 4's edges,
  `inject_islands`'s only pair `(fragmentation, islands)` is no own pair).
  `tests/test_151_stage30_validation.py`'s rule-id predicates recompute
  `derive_status`, which this item does not change.
  `tests/test_167_mode_3_detector.py::test_ac11_*` and
  `tests/test_187_neighbour_contact_rule.py::test_ac13_*` assert mode 3
  meets conditions 1–5 live, which A4 measures as still true.
  `tests/test_168_*` and `tests/test_169_*` read `.met` only.

## Validation

Replay the live re-measurement for modes 3 and 4 on the built branch and
compare it with A4:

```
.venv/bin/python -c "from segfacet import traceability as t; print([(m, c.met, c.subjects) for m in (3, 4) for c in t.bar_conditions(m) if c.number == 2])"
```

Expected: `[(3, True, ('split', 'split_own_label')), (4, True, ('inject_islands',))]`.
A difference is reported, not silently accepted: item 203's decision brief
quotes these values.

## Dependencies

None.

**Downstream:** the maintenance queue's item 198 (merged) re-measured the
expected sets this item measures on. Item 203 (the maintainer sign-off brief
states each bar condition as measured by this checker) and item 204 (stage
validation) read this checker.

## Decisions & Trade-offs

To be updated during implementation.

**Left open:** whether condition 2 should require the expressing firing to
come from one of condition 4's qualifying (single-mode, non-proxy) detectors
rather than any intended pair. The roadmap's condition 2 names "own intended
rules" without condition 4's proxy exclusion, so A1 follows it. Under A1 a
mode can still meet condition 2 only through a shared or proxy detector, the
residue of insight 2026-09-20-8462. It is not the case for modes 3 and 4
today (A4), and changing the bar's wording is the roadmap's call, not this
checker's.
