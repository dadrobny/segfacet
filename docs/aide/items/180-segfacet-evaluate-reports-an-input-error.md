<!-- aide-template: item 2 -->
# Item 180 — `segfacet evaluate` reports an input error instead of a traceback

> **Created:** 2026-09-25 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (maintenance)
> **Queue:** [`../queue/queue-024.md`](../queue/queue-024.md) · Item 180
> **Objectives:** G4, G7
> **Suggested branch:** `aide/180-segfacet-evaluate-reports-an-input`

---

## Description

`src/segfacet/cli.py`'s `_handle_evaluate` catches `FacetInputError` only while
loading the cohort (its step 1). The call to
`segfacet.eval.harness.evaluate_cohort` (its step 2) sits outside every `try`,
yet `evaluate_cohort` documents `FacetInputError` as a raise, both its own
duplicate-`case_id` check and, through `evaluate_case`, `compute_overlap`'s
shape check and `classify_outcome`'s check of a malformed `expected`. So a
cohort manifest that passes `load_cohort_manifest` but pairs a candidate and a
GT of different array shapes ends in an uncaught exception and a traceback,
where every other caller error in the handler prints `Error: <message>` to
stderr and returns 1 (`insights.md`, `defect` entry of item 175, 2026-09-24).

This item routes that exception the way `_handle_run` routes `load_case`'s:
the `evaluate_cohort` call is wrapped in `try/except FacetInputError`, which
prints `Error: {exc}` to stderr and returns 1 before any report is written.

**Not in scope.** No other exception type is caught. A `ValueError`, a
`RuntimeError` or any other error out of the harness is a code defect, not a
caller error, and must still surface as a traceback. The item does not make
`load_cohort_manifest` check shapes eagerly, since that would mean loading
every volume twice. It changes no other subcommand, and it changes nothing on
the success path.

## Acceptance Criteria

- [ ] **AC1: Exit code 1.** Given a cohort manifest of two cases, where case 1
  pairs a candidate with a GT of the same shape and case 2 pairs a candidate
  with a GT of a different shape, `segfacet.cli.main(["evaluate", "--cohort",
  <manifest>, "--out", <dir>])` returns `1` and does not raise.
- [ ] **AC2: The error message on stderr.** On the AC1 cohort, the captured
  stderr contains the line `Error: {exc}`, where `exc` is the
  `FacetInputError` that `segfacet.eval.overlap.compute_overlap` raises when
  called directly on case 2's candidate and GT arrays.
- [ ] **AC3: No report written.** On the AC1 cohort, `<dir>` holds neither
  `eval_report.json` nor `eval_report.txt` after the call.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

- **A1:** "The way the `run` handler does" means the handler's existing
  shape, `except FacetInputError as exc: print(f"Error: {exc}",
  file=sys.stderr); return 1`, as `_handle_run` does around `load_case` and
  `_handle_evaluate` already does around `load_cohort_manifest`. It does not
  mean `_handle_compare_runs`'s broad `except Exception`, which would report a
  code defect as a caller error.
- **A2:** The one-liner's "no traceback" is observed in-process as `main`
  returning rather than raising, the convention `test_057`'s AC7 tests use
  (`cli.main([...])` plus `capsys`). The console-script wrapper turns a
  returned int into the exit status, so no subprocess test is needed. The
  Validation section runs the real console script once.
- **A3:** Only the `evaluate_cohort` call needs the guard. With `--calibrate`,
  `calibrate_thresholds` re-evaluates the same `cases` only after
  `evaluate_cohort` has returned. By then every case has passed
  `compute_overlap`'s shape check, which does not depend on the config, and
  `classify_outcome`'s check of `expected`. Wrapping the calibration call too
  would guard a path this defect cannot reach.
- **A4:** `load_cohort_manifest` checks eagerly that each `gt`/`candidate` path
  exists (`segfacet/eval/cohort.py`, `_resolve_path`). So no `OSError` from a
  missing file reaches `evaluate_cohort`, and the new `except` names
  `FacetInputError` alone.

## Implementation Steps

1. In `src/segfacet/cli.py` `_handle_evaluate`, wrap the step-2
   `evaluate_cohort(...)` call in `try: ... except FacetInputError as exc:`,
   print `f"Error: {exc}"` to `sys.stderr` and `return 1`. `FacetInputError`
   is already imported in the handler from `segfacet.io`. Leave
   `compute_cohort_metrics` and everything after it outside the `try`.
2. Update `_handle_evaluate`'s docstring so the "Returns 1 (writing no
   report)" sentence also names an input error raised while evaluating a
   case, for example a candidate/GT shape mismatch.

No new helper, no new module, no new dependency.

## Authorised paths

**May change:**

- `src/segfacet/cli.py` — the `try/except` around `evaluate_cohort` and the
  docstring sentence.
- `tests/test_180_evaluate_input_error.py` — the AC tests and the adversarial
  case below.

**Asserts against:**

- `src/segfacet/eval/overlap.py` — AC2 recomputes the expected message by
  calling `compute_overlap` on case 2's arrays. It reads the module and never
  changes it.

## Testing Strategy

Module: `tests/test_180_evaluate_input_error.py`.

**Fixture.** Build the four label maps under `tmp_path` with
`tests/synthetic.py`'s `make_labelmap` and `write_nifti`. Case 1 is a GT and
candidate of equal shape, for example the default shape with one labelled
block. Case 2 is a GT of that shape and a candidate of a different shape, for
example one axis shorter. Write a `manifest_version: 1` manifest beside them
with paths relative to it (the shape `test_057`'s `_write_manifest` uses, with
`"expected": {"expected_verdict": "pass"}` on each case). Case 2 comes second
on purpose: the error then arrives after one case has already been evaluated,
which is the position where a partially built report could leak out. AC3
guards that.

**AC2's expected message** is produced by `compute_overlap` itself, called on
the two case-2 arrays read back with `nibabel` inside
`pytest.raises(FacetInputError)`, and is formatted as `f"Error: {exc}"`. The
test never hand-copies the message text.

**Adversarial case (one):**

- `non-input-error-propagates`: `monkeypatch` swaps
  `segfacet.eval.harness.evaluate_cohort` for a stub that raises
  `RuntimeError`, then asserts that `cli.main(["evaluate", ...])` raises
  `RuntimeError` on a valid one-case cohort. It guards against a broad
  `except Exception` or `except (FacetInputError, Exception)` that would
  report a code defect as a caller error (A1). The handler imports
  `evaluate_cohort` inside the function body, so patching the module
  attribute takes effect.

**Existing tests to reconcile:** none. A grep of `tests/` for
`pytest.raises` around an `evaluate` invocation found nothing that pins the
old raise. The success path does not change, so `test_057`, `test_092` and
`test_087`'s `evaluate` tests stand as they are.

## Validation  <!-- OPTIONAL: how to OBSERVE this working, beyond the tests -->

Replay the defect through the real console script, not `main()`. In a
scratch directory, write the AC1 two-case cohort (four NIfTI files and
`cohort.json`, built as in the Testing Strategy), then run
`.venv/bin/segfacet evaluate --cohort <scratch>/cohort.json --out <scratch>/out`
(on Windows, `.venv/Scripts/segfacet`). Observe:

- the exit status is 1;
- stderr is a single `Error: compute_overlap: candidate and gt must have
  identical shape; ...` line, and `Traceback` appears nowhere in it;
- `<scratch>/out` holds no `eval_report.json`.

No `[validation]` profile is needed.

## Dependencies

None.

## Decisions & Trade-offs

To be updated during implementation.
