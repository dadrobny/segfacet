<!-- aide-template: item 1 -->
# Item 155 — A corpus case is a clean control or a condition case, never `failure_mode == 0` alone

> **Created:** 2026-09-16 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update
> **Queue:** [`../queue/queue-021.md`](../queue/queue-021.md) · Item 155
> **Objectives:** G7
> **Suggested branch:** `aide/155-a-corpus-case-is-a`

---

## Description

Roadmap Stage 31 D4, first part. It absorbs the `insights.md` gap entry dated
2026-09-14 (item 150): "`failure_mode == 0` in a corpus manifest now means two
things".

Since the item-150 sign-off, `failure_mode == 0` in the committed corpus
manifests has two meanings:

- a **clean control** (`clean_control` in `tests/corpus/manifest.json`,
  `clean_hu` in `tests/corpus/intensity/manifest.json`);
- a **condition-only case**: `failure_mode == 0` plus a non-empty `condition`
  (today only the FOV-truncation crop case in the geometric manifest).

Three production consumers tell the two apart by hand, each with its own
comparison against zero:

- `synth.regression.verify_case` (`regression.py:343`);
- `traceability._build_conformance` (`traceability.py:335`, `:354`);
- `failure_modes._corpus_case_conflicts` (`failure_modes.py:2502`).

Seven test modules filter on `failure_mode != 0`. A filter that forgets the
`condition` clause drops the crop case without any error. `test_040`'s rebuild
sweep did exactly that until it was fixed.

**The discriminator is an explicit `kind` field on every manifest case**, with a
closed vocabulary of three values:

| `kind` | `failure_mode` | `condition` |
|---|---|---|
| `"clean_control"` | `0` | `""` |
| `"condition"` | `0` | non-empty |
| `"failure"` | a specification mode id (≠ 0) | `""` |

Two functions in `segfacet.synth.perturbation` own it. It is the module that
already holds `CLEAN_CONTROL_MODE` and `Expectation`:

- `case_kind(failure_mode, condition) -> str` **derives** the kind. It is the
  one place in the tree that compares a failure mode with zero. The generators
  call it when they write a manifest, so `kind` is written by the generator and
  never by hand.
- `corpus_case_kind(case) -> str` **reads** `case["kind"]` from a manifest case
  dict and checks it against the vocabulary. It is the one documented answer to
  "what kind of case is this?", and every consumer calls it.

Both manifests are regenerated with the new field. Every consumer, in
production and in tests, moves onto `corpus_case_kind`. An AST scan of the whole
tree then shows that no comparison against zero is left.

**Not in scope:**

- No `ModeSpec` or `ConditionSpec` field changes, and no case's
  `expected_firing`, `expected_rule_ids`, `failure_mode`, `failure_mode_name`
  or `condition` value changes. The new field is added; nothing else moves.
- No case id changes. Item 157 renames the ids, and nothing in this item
  selects a case by id.
- No change to the generated conformance artifacts
  (`docs/aide/traceability_matrix.generated.*`, `docs/aide/failure_modes.generated.*`).
  Their `expected_source` column (`manifest-clean-control` /
  `specification-condition`) already renders the distinction, and it keeps
  rendering the same values (A4).
- No change to the eval harness's per-mode grouping. It reads attribute-form
  `failure_mode` on `CaseOutcome`/`PerModeMetrics`, not manifest dicts (A6).

## Acceptance Criteria

- [ ] **AC1: `case_kind` derives the three kinds.** `case_kind(0, "")` returns
  `"clean_control"`. `case_kind(0, "fov_truncation")` returns `"condition"`.
  For every key `m` of `failure_modes.SPECIFICATION`, `case_kind(m, "")` returns
  `"failure"`.
- [ ] **AC2: `case_kind` refuses a mode together with a condition.** For every
  key `m` of `failure_modes.SPECIFICATION`, `case_kind(m, "fov_truncation")`
  raises `ValueError`.
- [ ] **AC3: the vocabulary is closed.** `perturbation.CASE_KINDS ==
  frozenset({"clean_control", "condition", "failure"})`.
- [ ] **AC4: `corpus_case_kind` returns the recorded kind.** For each member `k`
  of `CASE_KINDS`, `corpus_case_kind({"kind": k})` returns `k`.
- [ ] **AC5: `corpus_case_kind` refuses a case with no kind.**
  `corpus_case_kind({"failure_mode": 0, "condition": ""})` raises `ValueError`.
- [ ] **AC6: `corpus_case_kind` refuses an unknown kind.**
  `corpus_case_kind({"kind": "clean"})` raises `ValueError`.
- [ ] **AC7: every geometric manifest case records its derived kind.** For every
  case in the committed `tests/corpus/manifest.json`,
  `case["kind"] == case_kind(case["failure_mode"], case["condition"])`.
- [ ] **AC8: every intensity manifest case records its derived kind.** For every
  case in the committed `tests/corpus/intensity/manifest.json`,
  `case["kind"] == case_kind(case["failure_mode"], case.get("condition", ""))`.
- [ ] **AC9: the geometric manifest regenerates byte-identically.** The bytes
  `synth.corpus.write_corpus(tmp)` writes to `manifest.json` equal the bytes of
  the committed `tests/corpus/manifest.json`. The existing
  `test_040::test_ac16_regeneration_is_byte_identical_across_runs_and_vs_committed`
  already asserts this and meets the AC. It must pass unchanged in its
  assertions.
- [ ] **AC10: the intensity manifest regenerates byte-identically.** The bytes
  `synth.intensity.write_intensity_corpus(tmp)` writes to `manifest.json` equal
  the bytes of the committed `tests/corpus/intensity/manifest.json`. The
  existing `test_058::test_ac19_regeneration_is_byte_identical_across_runs_and_vs_committed`
  meets the AC and must pass unchanged in its assertions.
- [ ] **AC11: both manifests stay LF-pinned.** For each of
  `tests/corpus/manifest.json` and `tests/corpus/intensity/manifest.json`,
  `git check-attr eol -- <path>` reports `eol: lf`.
- [ ] **AC12: no consumer compares a manifest case's `failure_mode` with zero.**
  The tree-wide scan defined under Testing Strategy, run over every `*.py` file
  under `src/segfacet/` and `tests/`, returns an empty violation list. The body
  of `segfacet.synth.perturbation.case_kind` is the only exemption.
  *(closes Stage 31 criterion 4)*
- [ ] **AC13: the scan detects each forbidden shape.** On synthetic source
  strings, the same scan function returns exactly one violation for each of:
  - `if case["failure_mode"] != 0: pass`
  - `xs = [c for c in cs if c.get("failure_mode") == 0]`
  - `m = case.get("failure_mode")` followed by `if m == 0: pass` in the same
    function
  - `if not case["failure_mode"]: pass`
  - `if case["failure_mode"] == CLEAN_CONTROL_MODE: pass`

  It returns zero violations for `assert case["failure_mode"] == 0` and for
  `if c.get("failure_mode") == mode: pass`.
- [ ] **AC14: `verify_case` classifies a condition-only case by its kind.** Take
  the committed `kind == "clean_control"` geometric case and make a copy with
  `kind` set to `"condition"`, `condition` set to `"fov_truncation"` and
  `expected_rule_ids` set to `["border"]`. Every other field is unchanged,
  including `failure_mode == 0` and `expected_verdict == "pass"`.
  `verify_case(copy)` returns `False`: the case is judged as a condition case
  whose designated rule did not fire, not as a clean control with no findings.
- [ ] **AC15: `verify_case` refuses a pipeline case with no kind.** A copy of
  the committed `kind == "clean_control"` geometric case with the `kind` key
  removed makes `verify_case` raise `ValueError`.
- [ ] **AC16: the specification's corpus check classifies a condition-only case
  by its kind.** Substitute a geometric manifest whose only case is the AC14
  copy, by monkeypatching `segfacet.synth.corpus.load_manifest`. Then the
  output of `failure_modes.specification_conflicts()` contains one message
  that names both the copy's `case_id` and `'fov_truncation'`.
- [ ] **AC17: the specification's corpus check refuses a case with no kind.**
  Substitute a geometric manifest whose only case is the AC15 copy, in the same
  way. Then `failure_modes.specification_conflicts()` raises `ValueError`.
- [ ] **AC18: the conformance report classifies a condition-only case by its
  kind.** Substitute a geometric manifest whose only case is the AC14 copy, in
  the same way. Then `traceability._build_conformance(failure_modes)` returns a
  report whose `ConformanceCase` for `("geometric", copy's case_id)` has
  `expected_source == "unspecified"` and `agrees is False`, and whose
  `unspecified_cases` contains `("geometric", copy's case_id)`.
- [ ] **AC19: the conformance report refuses a case with no kind.** Substitute
  a geometric manifest whose only case is the AC15 copy, in the same way. Then
  `traceability._build_conformance(failure_modes)` raises `ValueError`.

## Assumptions

- **A1: a `kind` field rather than a sentinel `failure_mode`.** The queue lets
  the spec choose. A sentinel means writing `null` (or `-1`) into the condition
  case's `failure_mode`. That would change an existing manifest value, the
  conformance artifact's `mode` column (`traceability_matrix.generated.json`
  renders `"mode": 0` for that case), and the eval harness's per-mode bucket
  that `test_116::test_ac8_mode6_crop_at_border_sensitivity_is_restored_to_one`
  reads. A `kind` field adds one key and moves no existing value. **Neither
  option changes a signed-off `ModeSpec` field or any case's `expected_firing`.**
- **A2: `kind` is derived, not authored.** Each generator computes it with
  `case_kind(failure_mode, condition)` at write time. The combination "mode ≠ 0
  plus a condition" is refused (`ValueError`), not given a fourth kind. No
  committed case has that combination. Whether a failure case may also carry a
  condition is a Stage 32 decision, and refusing it now makes the decision
  explicit when it comes.
- **A3: the functions live in `segfacet.synth.perturbation`.** Both generators
  (`synth.corpus` via `Expectation.to_dict`, `synth.intensity` directly) already
  import that module. `synth.intensity`'s docstring forbids it importing
  `segfacet.failure_modes` ("must not acquire a dependency on the specification
  module it feeds"), so the functions cannot live there. `failure_modes` and
  `traceability` reach them through the deferred, in-function `segfacet.synth`
  imports they already make. No module reads `tests/` at import time. No new
  module is added.
- **A4: the generated conformance artifacts do not change.**
  `ConformanceCase` gains no `kind` field. Its `expected_source` already renders
  the distinction and keeps the same values. The queue's "differ only in the
  new field" is therefore met with an empty diff. `aide scope` proves it: none
  of `docs/aide/*.generated.*` is in May change.
- **A5: `MANIFEST_VERSION` and `INTENSITY_MANIFEST_VERSION` stay unchanged.**
  The field is additive. Item 146 set this precedent when it added `failure_mode`
  to the intensity manifest.
- **A6: the scan covers manifest-dict access only.** It covers
  `x["failure_mode"]`, `x.get("failure_mode")`, and a local name bound to either
  inside the same function (or the same module body). Attribute access
  (`CaseOutcome.failure_mode`, `PerModeMetrics.failure_mode`,
  `Expectation.failure_mode`) is out of scope. That is the eval harness's typed
  record, and its grouping of the condition case under mode 0 is a separate
  question, recorded in `insights.md` (2026-09-16, item 155). Comparisons inside
  an `assert` are exempt: they pin a named case's recorded value and do not
  classify it. The zero side of a comparison is the literal `0` or one of the
  names `CLEAN_CONTROL_MODE` / `_CLEAN_MODE_ID`.
- **A7: `CLEAN_CONTROL_MODE` stays.** It is still the value a clean control's
  `Expectation.failure_mode` carries. Only *comparing* against it outside
  `case_kind` is retired.

## Implementation Steps

1. **`src/segfacet/synth/perturbation.py`.** Add the constants
   `CASE_KIND_CLEAN_CONTROL = "clean_control"`, `CASE_KIND_CONDITION =
   "condition"`, `CASE_KIND_FAILURE = "failure"` and
   `CASE_KINDS = frozenset({...})`.
   - Add `case_kind(failure_mode: int, condition: str) -> str` per the table in
     the Description. It raises `ValueError` when `failure_mode != 0` and
     `condition` is non-empty.
   - Add `corpus_case_kind(case: Mapping) -> str`. It returns `case["kind"]`,
     and raises `ValueError` naming `case.get("case_id")` when the key is
     missing or the value is not in `CASE_KINDS`.
   - Add all of these to `__all__`.
   - `Expectation.to_dict()` gains `"kind": case_kind(self.failure_mode,
     self.condition)`.
   - Update `Expectation`'s docstring to point at `kind` rather than restating
     the zero overload.
2. **`src/segfacet/synth/corpus.py`.** `write_corpus`'s `manifest_case` gains
   `"kind": expectation_dict["kind"]`. Add `kind` and its three values to the
   module docstring's description of the manifest fields.
3. **`src/segfacet/synth/intensity.py`.** `write_intensity_corpus`'s
   `manifest_case` gains `"kind": case_kind(case.failure_mode, "")`, importing
   `case_kind` from `segfacet.synth.perturbation` next to `seeded_rng`.
4. **Regenerate both manifests** with each module's one-command entry point
   (`python -m segfacet.synth.corpus`, `python -m segfacet.synth.intensity`, run
   through the venv). Confirm that the manifest diff adds a `kind` line to each
   case and changes nothing else. The `.nii.gz` fixtures must not change. The
   generators already write with `write_bytes` and `\n`, so no writer change is
   needed.
5. **`src/segfacet/synth/regression.py`.** In `verify_case`'s `pipeline`
   branch, replace `case.get("failure_mode") == 0 and not case.get("condition")`
   with `corpus_case_kind(case) == CASE_KIND_CLEAN_CONTROL`. Update the
   docstring bullet.
6. **`src/segfacet/failure_modes.py`.** In `_corpus_case_conflicts`, dispatch
   on `corpus_case_kind(case)` imported inside the function:
   - `condition` goes to `_condition_case_conflicts`;
   - `clean_control` is skipped;
   - `failure` takes the existing mode path.

   Update the docstrings of `_corpus_case_conflicts` and
   `_condition_case_conflicts`.
7. **`src/segfacet/traceability.py`.** In `_build_conformance`, dispatch the
   same way (`condition` → the `specification-condition` branch, `clean_control`
   → `manifest-clean-control`, `failure` → the existing specification lookup).
   `expected_source` strings stay unchanged. Reword the module docstring's
   "the two `failure_mode == 0`" passage (`:34`) in terms of `kind`.
8. **Run the scan (AC12)** and move every remaining hit onto
   `corpus_case_kind`. Known hits at spec time are listed under Testing
   Strategy, "Existing tests to reconcile". Production hits are steps 5–7.
9. **Regenerate the conformance artifacts** (`python -m segfacet.traceability`,
   `python -m segfacet.failure_modes`, through the venv) and confirm that
   `git status` shows no change under `docs/aide/` (A4). If a change appears,
   stop and hand back: it means a consumer's classification moved.

## Authorised paths

**May change:**

- `src/segfacet/synth/perturbation.py` — `case_kind`, `corpus_case_kind`, the kind constants, `Expectation.to_dict`'s `kind` key
- `src/segfacet/synth/corpus.py` — the manifest writer's `kind` key and the manifest-field docstring
- `src/segfacet/synth/intensity.py` — the intensity manifest writer's `kind` key
- `src/segfacet/synth/regression.py` — `verify_case` onto `corpus_case_kind`
- `src/segfacet/failure_modes.py` — `_corpus_case_conflicts` onto `corpus_case_kind`, docstrings
- `src/segfacet/traceability.py` — `_build_conformance` onto `corpus_case_kind`, module docstring
- `tests/corpus/manifest.json` — regenerated with `kind`
- `tests/corpus/intensity/manifest.json` — regenerated with `kind`
- `tests/test_155_corpus_case_kind.py` — the new module for AC1–AC8 and AC11–AC19
- `tests/test_040_synthetic_corpus.py` — `test_ac17`'s `failure_mode != 0 or condition` filter; `_SCHEMA_KEYS_TYPES` gains `kind: str`
- `tests/test_041_regression_suite.py` — the two `_PIPELINE_CASES` filters (`:75`, `:78`)
- `tests/test_125_stage28_validation.py` — the `failure_mode != 0` pipeline-mode filter (`:437`)
- `tests/test_135_stage29_validation.py` — the `failure_mode != 0` pipeline-mode filter (`:759`)
- `tests/test_146_ninth_mode_and_first_proposed.py` — the `failure_mode != 0 or condition` filter (`:908`)
- `tests/test_147_specification_is_the_record.py` — the three `failure_mode != 0` target selections (`:737`, `:765`, `:790`)

**Asserts against:**

- `.gitattributes` — AC11 reads both manifests' `eol` attribute through `git check-attr`

## Testing Strategy

**New module: `tests/test_155_corpus_case_kind.py`**, with one focused test per
AC. AC9 and AC10 are met by the existing regeneration tests named in those
criteria, and the new module does not duplicate them.

- **AC1–AC6** are pure function calls. AC1 and AC2 iterate over
  `failure_modes.SPECIFICATION`'s live key set, never a hand-typed range.
- **AC7/AC8** load the committed manifests with `synth.corpus.load_manifest()`
  and `synth.intensity.load_intensity_manifest()`, and recompute each kind from
  that case's own fields.
- **AC11** runs `git check-attr eol -- <path>` with `subprocess.run` from the
  repo root (resolve the root with `Path(__file__).resolve().parents[1]`, and
  pass `cwd=`). It skips cleanly if `git` is not on PATH.
- **AC12/AC13: the scan.** Write the scanner once in the module as
  `_zero_comparisons(source: str, filename: str) -> list`. It parses with `ast`
  and walks function bodies and the module body separately. In each scope:
  1. Collect the local names bound by `Assign`/`AnnAssign` whose value is a
     *failure_mode access*. A failure_mode access is `Subscript` with the
     constant slice `"failure_mode"`, or `Call` of attribute `get` whose first
     argument is the constant `"failure_mode"`.
  2. Report every `Compare` with one operator in `Eq/NotEq/Is/IsNot`, where one
     side is a failure_mode access or a collected name, and the other side is
     `Constant(0)` or a `Name`/`Attribute` whose identifier is
     `CLEAN_CONTROL_MODE` or `_CLEAN_MODE_ID`.
  3. Report every `UnaryOp(Not)` whose operand is a failure_mode access or a
     collected name.
  4. Skip any node inside an `Assert` statement's `test`. Skip the whole body
     of the `FunctionDef` named `case_kind` in `src/segfacet/synth/perturbation.py`.
     No other exemption.

  AC12 enumerates files with `Path.rglob("*.py")` under `src/segfacet` and
  `tests`, never from a hand-typed list. The `tests/` walk includes
  `test_155` itself, whose AC13 fixtures are string literals and so are not
  parsed as code. AC13 feeds the scanner the seven literal snippets (each
  wrapped in a `def f(case, cs, c, mode):` where needed) and checks the counts.
- **AC14–AC19** start from `copy.deepcopy` of the committed clean-control case,
  selected by `kind == "clean_control"` in the geometric manifest (never by
  `case_id`, which item 157 renames). AC16–AC19 substitute the manifest with
  `monkeypatch.setattr(segfacet.synth.corpus, "load_manifest", lambda *a, **k:
  {"cases": [probe]})`. `_corpus_case_conflicts` and `_build_conformance` both
  read through that module attribute. AC18 also depends on
  `failure_modes.measured_firing` resolving the probe's `case_id`. The probe
  reuses the clean-control fixture, so it resolves. If `measured_firing` turns
  out to read through the same substituted loader and fail, the test-writer
  hands back rather than widening the probe.
- **Adversarial / edge cases:**
  - `case_kind(0, "")` and `case_kind(0, "x")` for an unknown condition id:
    `case_kind` does not validate condition ids. That is
    `_condition_case_conflicts`' job, and the test records it.
  - `corpus_case_kind({"kind": None})` raises `ValueError`.
  - `corpus_case_kind` does not mutate its input.
  - A `bool` `False` `failure_mode` (`case_kind(False, "")`) is not specified.
    Do not test it.

**Existing tests to reconcile** (step 8; each one moves onto
`corpus_case_kind(...)` / `CASE_KIND_*`, and none is deleted). Spec-time grep
hits that AC12's scan will report:

- `tests/test_040_synthetic_corpus.py:450` — `c["failure_mode"] != 0 or c["condition"]`
- `tests/test_041_regression_suite.py:75` — `(c["failure_mode"] != 0 or c.get("condition")) and c["expected_rule_ids"]`
- `tests/test_041_regression_suite.py:78` — `c["failure_mode"] != 0 and not c["expected_rule_ids"]`
- `tests/test_125_stage28_validation.py:437` — `c["failure_mode"] != 0` in a pipeline mode-set comprehension
- `tests/test_135_stage29_validation.py:759` — the same shape
- `tests/test_146_ninth_mode_and_first_proposed.py:908` — `case.get("failure_mode") != 0 or case.get("condition")`
- `tests/test_147_specification_is_the_record.py:737`, `:765`, `:790` — `c["failure_mode"] != 0` target selection

The scan is the authority. A hit it reports that this list lacks is reconciled
the same way, and the file is added to May change by a dated amendment to this
spec.

Adding a key to `Expectation.to_dict()` and to the manifests can red a test that
pins a case's full key set. Spec-time grep found only
`test_040::_SCHEMA_KEYS_TYPES`, which checks that keys are present, not that the
set is equal. It gains `kind` so AC4 of that module covers the new field.

## Validation

1. Regenerate both manifests (step 4). Then run `git diff --stat` against the
   branch's recorded base, restricted to `tests/corpus/`. It must show exactly
   the two `manifest.json` files and no `.nii.gz`.
2. `git diff` on the two manifests shows only added `"kind": …` lines, one per
   case: 11 geometric and 4 intensity at spec time. No removed line.
3. Regenerate the conformance and specification artifacts (step 9).
   `git status --short -- docs/aide` shows no `*.generated.*` path (A4).
4. `python .aide/scripts/aide.py scope 155` passes.
5. The full suite is green, the validator's gate.

## Dependencies

None.

**Downstream:** item 157 (drop the `modeN_` case-id prefixes) regenerates the
same two manifests. It should land after this item or rebase onto it. Nothing
here keys on a case id, so the two changes compose by regeneration. Item 156
edits `traceability.py` and `failure_modes.py` in different functions. Item 159
edits `test_146` and `test_147` in different tests.

## Decisions & Trade-offs

- **Implemented as specified**, steps 1-9 followed in order; no deviation from
  the Description's table or the Assumptions.
- `_corpus_case_conflicts` (`failure_modes.py`) and `_build_conformance`
  (`traceability.py`) both call `corpus_case_kind(case)` as the very first
  thing done with a manifest case in the loop body, before any other field is
  read. That means a case with no recorded `kind` (or an unknown one) raises
  `ValueError` before `mode_id`/`condition_id` are even inspected -- the
  natural reading of AC17/AC19 ("refuses a case with no kind"), and it costs
  nothing since every real manifest case now carries `kind`.
- Regenerating both manifests (`python -m segfacet.synth.corpus`,
  `python -m segfacet.synth.intensity`) added exactly one `"kind": ...` line
  per case -- 11 geometric, 4 intensity -- and changed nothing else,
  confirmed by `git diff --stat` scoped to `tests/corpus/`. Regenerating the
  conformance/specification artifacts (`python -m segfacet.traceability`,
  `python -m segfacet.failure_modes`) produced an empty `git status --short
  -- docs/aide` diff, confirming A4.
- `corpus_case_kind`'s error message names `case.get("case_id")` per the
  Implementation Steps; verified manually that a case missing `kind`
  (constructed by deleting the key from the committed clean-control case)
  raises `ValueError` naming that case's id.
- 2026-09-16: validation round 1 found `_build_conformance`
  (`traceability.py`) called `corpus_case_kind(manifest_case)` after
  `measured_firing(probe)` instead of before it, contradicting the entry
  above. Moved the `corpus_case_kind` call to immediately after `case_id` is
  read, ahead of the `probe`/`measured_firing` call, matching
  `_corpus_case_conflicts` (`failure_modes.py`) and the entry's original
  claim.
