<!-- aide-template: item 3 -->
# Item 238 — Threshold literals in pinned reasons compared exactly

> **Created:** 2026-10-17 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-032.md`](../queue/queue-032.md) · Item 238
> **Objectives:** G7
> **Suggested branch:** `aide/238-threshold-literals-in-pinned-reasons`

---

## Description

Item 224 gave `tests/test_098_stray_components.py` the reason comparison
`_assert_reason_matches`. It masks every decimal token (`\d+\.\d+`) for an
exact text comparison, then accepts each decimal token within one unit of the
pinned token's last place. That tolerance is meant for **measured** values,
which can move one digit between platforms (a spline fit's last ULP). It also
covers the **threshold literals** that rule reasons render from their config.
A threshold renders identically on every platform, and a change to one is a
recalibration, which the snapshot should catch.

The case the insight records (`2026-10-14-1dd0`) is the pinned `remove_level`
reason, emitted by `centroid_spacing`'s `missing_level` detector
(`src/segfacet/heuristics/centroid_spacing.py`, the f-string after the
`gap_ratio > gap_thr` check):

> "... reads 1.887x the spacing beside it, strictly above 1.5, between labels
> of normal size (at most 1.5x their larger neighbour) ..."

`1.887` is measured. The two `1.5`s are `DEFAULT_GAP_RATIO` and
`DEFAULT_SIZE_RATIO`, rendered with `.6g`. Today a recalibration of either to
`1.4`, `1.6` or `1.55` still passes `test_ac15_golden_verdict_and_findings_unchanged("remove_level")`,
because the difference is at most one unit of the pinned token's last place.
No other test pins either value: `test_218::test_gap_threshold_read_from_own_section`
checks only that the parameter is read. The other threshold literals in the
constant are `threshold 0.75` (`fragment`), `threshold 13.0 mm`
(`sequence_break`) and the `displace` clause built from the live
`_DEFAULT_MAX_OFFSET_MM`. The insight records `0.75` as pinned by test_035
AC3 and `13.0` by test_129's config text. This item compares all of them
exactly anyway, because one rule for every threshold clause costs nothing
extra.

**The change.** `_assert_reason_matches` compares **threshold clauses**
exactly and removes them before the tolerant decimal comparison. A threshold
clause is a decimal token directly after one of the phrasings the pinned
reasons use for a threshold: `threshold `, `above ` or `at most ` (A1). Every
other decimal token keeps item 224's one-unit tolerance, and everything else
in the comparison is unchanged.

**Who edits what.** This is a test-only item, because the defect is in a
shipped test helper:

- the **builder** changes the helper in `tests/test_098_stray_components.py`,
  which is this item's deliverable;
- the **test-writer** writes `tests/test_238_threshold_clauses_exact.py`, the
  AC tests.

No production code changes.

**Not in scope:**

- The tolerance width for measured tokens (item 224 A1) is unchanged.
- No entry of `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS` changes.
- `test_102::test_ac5` and `test_123::test_ac28` are not edited. They call the
  helper, so they inherit the exact threshold comparison with no change of
  their own.
- No direct pin of `DEFAULT_GAP_RATIO == 1.5` is added (Decisions).

## Acceptance Criteria

- [ ] **AC1: A gap-ratio threshold reading 1.4 fails AC15.** `test_098::test_ac15_golden_verdict_and_findings_unchanged("remove_level")` raises `AssertionError` when the pinned `missing_level` reason has `strictly above 1.5` replaced by `strictly above 1.4`, with nothing else changed.
- [ ] **AC2: A gap-ratio threshold reading 1.6 fails AC15.** `test_ac15_golden_verdict_and_findings_unchanged("remove_level")` raises `AssertionError` when the pinned `missing_level` reason has `strictly above 1.5` replaced by `strictly above 1.6`, with nothing else changed.
- [ ] **AC3: A last-digit difference in a measured value still passes, next to a threshold clause.** `test_ac15_golden_verdict_and_findings_unchanged("remove_level")` returns without raising when the pinned `missing_level` reason has `1.887x` replaced by `1.888x`, with nothing else changed.

## Assumptions

- **A1: what counts as a threshold clause.** A threshold clause is a match of
  `(?:threshold|above|at most) \d+\.\d+`. These are the three phrasings the
  reasons in `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS` use for a threshold
  (`strictly below threshold 0.75`, `strictly above 1.5`, `at most 1.5x`,
  `threshold 13.0 mm`, `threshold {_DEFAULT_MAX_OFFSET_MM:.1f} mm`). No
  measured token in the constant follows one of them: `14.6`, `33.8` and
  `1.887` follow `lies ` and `reads `, and `0.52579` and `0.9986128236744759`
  follow `=` (checked 2026-10-17). A phrasing a future reason adds, such as
  `below 2.0`, would fall back to item 224's tolerance. That is no worse than
  today, and widening the set is a one-word edit.
- **A2: an exact threshold comparison holds on every platform.** Each
  threshold is a config literal (`DEFAULT_GAP_RATIO`, `DEFAULT_SIZE_RATIO`,
  the fragmentation `0.75`, `_DEFAULT_MAX_OFFSET_MM`), rendered by a fixed
  format (`.6g` or `.1f`) without arithmetic. So the platform ULP drift that
  item 224 tolerates cannot reach it.
- **A3: mutating the pinned side stands in for a recalibration.** A
  recalibration moves the fresh reason. The tests move the pinned reason
  instead, as item 224's tests do. The comparison is symmetric in which side
  differs, and mutating the pinned side avoids rebuilding the fresh report
  under a patched config.
- **A4: the defaults are chosen under `loop.clarify = "assume"`.** The queue
  line lets the spec choose between masking threshold clauses and pinning
  `1.5` directly. This spec masks them. A direct pin of `DEFAULT_GAP_RATIO`
  makes no snapshot fail, and the queue's testable line asks that the reason
  comparison fail.

## Implementation Steps

1. **`tests/test_098_stray_components.py`, next to `_DECIMAL_TOKEN`** (builder):
   - Add `_THRESHOLD_CLAUSE = re.compile(r"(?:threshold|above|at most) \d+\.\d+")`.
     `\d+` is greedy from just after the space, so `above 11.5` matches whole
     and never leaves a tolerant `1.5` behind.
   - In `_assert_reason_matches(got, pinned)`, before the existing two steps:
     1. Assert `_THRESHOLD_CLAUSE.findall(got) == _THRESHOLD_CLAUSE.findall(pinned)`,
        using the existing `msg`, which names both reasons.
     2. Replace each threshold clause on both sides with one placeholder that
        contains no digit, then run the existing masked-text and per-token
        tolerance steps on the replaced strings.
   - Keep the function's name and `(got, pinned)` signature, and keep
     `_assert_findings_match` unchanged. `test_102` and `test_123` import both.
   - Extend the `# Item 224:` comment above `_DECIMAL_TOKEN` by one sentence:
     threshold clauses are config literals, so they are compared exactly
     (item 238).

No dependency is added. `re` is already imported.

## Authorised paths

**May change:**

- `tests/test_098_stray_components.py` — the threshold-clause regex and the change to `_assert_reason_matches` (builder)
- `tests/test_238_threshold_clauses_exact.py` — this item's AC tests (test-writer)

**Asserts against:**

None.

## Testing Strategy

The tests go in the new module `tests/test_238_threshold_clauses_exact.py`,
one test per AC. As in `tests/test_224_platform_tolerant_snapshots.py`, each
test drives the **real** `test_098::test_ac15_golden_verdict_and_findings_unchanged`:

- `monkeypatch.setitem` puts a `copy.deepcopy` of the `remove_level` entry
  into `test_098_stray_components._PRE_098_GOLDEN_VERDICT_AND_FINDINGS`, with
  one mutation applied. The shared constant is never mutated in place, because
  eight modules import it.
- The test then calls `test_ac15_golden_verdict_and_findings_unchanged("remove_level")`
  and expects either a clean return or `pytest.raises(AssertionError)`.
- The test finds the `missing_level` finding by `detector_id`, not by index,
  and replaces the **full phrase** (`strictly above 1.5`, `1.887x`, `at most
  1.5x`). The reason holds two `1.5`s, so a bare `"1.5"` replacement would
  move both.
- Each test asserts that the phrase it replaces is present in the pinned
  reason before replacing it, so a reworded constant fails the test loudly
  rather than leaving it vacuous.

**Adversarial cases:**

- **size-ratio clause:** in the same reason, `at most 1.5x` replaced by
  `at most 1.6x` makes AC15 raise. This guards against a mask that matches
  only the `above` phrasing, or only the first threshold in a reason.
- **threshold phrasing:** in the `fragment` reason, `threshold 0.75` replaced
  by `threshold 0.76` makes `test_ac15_golden_verdict_and_findings_unchanged("fragment")`
  raise. This guards against a mask that leaves the `threshold N` phrasing
  tolerant.

**Keep the new module off the Windows subset.** `tests/test_213_windows_ci_subset.py`
walks every `tests/test_*.py` module's AST, and a module that shows a signal
must be listed in `.github/workflows/ci.yml`'s `WINDOWS_TESTS`, which this
item does not authorise. So `test_238` must not contain:

- `.read_bytes`, a `newline=` keyword, or a `.gitattributes` string;
- an import of `segfacet.cli`, or a string starting with `segfacet.cli`;
- `subprocess`, `run_process` or `sys.executable`;
- `.as_posix`, `os.sep`, `PureWindowsPath` or `PurePosixPath`.

The change to test_098 adds no signal, and test_098 is already in
`WINDOWS_TESTS`.

**Existing tests to reconcile.** Each was found by grep, and none is expected
to need an edit:

- **`tests/test_224_platform_tolerant_snapshots.py`** must still pass. It
  mutates only measured tokens (`14.6`, `0.52579`), an integer (`9796`),
  text, the verdict, a label list and the finding count, and no threshold
  clause. Its AC2 (changed verdict) and AC6 (changed label) are what keep "a
  changed verdict or finding still fails" measured, so this item does not
  duplicate them.
- **The callers `tests/test_102_stage18_validation.py::test_ac5_…` and
  `tests/test_123_recalibrate_and_regenerate.py::test_ac28_…`** compare fresh
  reasons whose threshold clauses render from the same constants as the
  pinned ones, so the exact comparison holds for them.
- **Source scans of test_098.** `tests/test_105_golden_decision_table.py`,
  `tests/test_107_item_scope_check.py`, `tests/test_126_golden_retirement.py`
  (AC6, AC7, AC13) and `tests/test_135_stage29_validation.py` read test_098's
  names or AC15's source. The constant's name, the `test_ac15_…` name and
  signature are unchanged, and the new code uses none of the golden markers
  (`GOLDEN_DIR`, `load_golden`, `read_golden_text`, `check_case_golden`,
  `tests/corpus/golden`).
- **`tests/test_132_monotonicity_against_traversal_order.py` AC26** calls
  `test_ac15_…("relabel_swap")` directly. That reason has no decimal token, so
  nothing changes for it.

## Review findings

- **raises-unscoped** (minor): the four negative tests used a bare `pytest.raises(AssertionError)`, so any assertion in `test_098::test_ac15_golden_verdict_and_findings_unchanged` (verdict, findings, corpus build) satisfied them, not only the reason comparison; fixed with `match="reason differs"`, the message `_assert_reason_matches` raises. Tests: `test_ac1_gap_ratio_threshold_1_4_fails_ac15`, `test_ac2_gap_ratio_threshold_1_6_fails_ac15`, `test_size_ratio_clause`, `test_threshold_phrasing`.

## Dependencies

None.

## Decisions & Trade-offs

Implemented as specified: `_THRESHOLD_CLAUSE` compared exactly via `findall`, then replaced by `@` (no digit) on both sides before the existing tolerant steps.

- **Masking chosen over a direct pin of 1.5.** A direct
  `assert DEFAULT_GAP_RATIO == 1.5` would catch only the gap ratio. It would
  miss the size ratio, which sits in the same reason and has the same defect,
  and it would duplicate the constant's own value in a test. Masking makes the
  snapshot itself the check, for every threshold clause it carries.
- **Left open:** whether the face-name-sensitive `crop_at_border` case, whose
  reasons AC15 skips entirely, should have its integer and text clauses
  compared. Its reasons carry no threshold literal, and no recorded defect
  asks for it.
