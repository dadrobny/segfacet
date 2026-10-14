<!-- aide-template: item 3 -->
# Item 224 — Platform-sensitive comparisons tolerant, determinism checks exact

> **Created:** 2026-10-12 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-030.md`](../queue/queue-030.md) · Item 224
> **Objectives:** G6, G7
> **Suggested branch:** `aide/224-tolerant-snapshots-exact-determinism`

---

## Description

Two kinds of shipped test comparison are set to the wrong strictness. This item fixes both and changes no production code.

**1. Frozen reason snapshots are compared too strictly.**
`tests/test_098_stray_components.py` holds the frozen snapshot `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`. Its finding `reason` strings contain rendered floats. One is the `displace` offset `"14.6 mm"`, rendered with `.1f` from a spline fit (measured 14.615923). A spline fit can differ in its last ULP between platforms. If the value sits on a rounding boundary, that difference moves the rendered digit. Three tests compare a fresh reason with a pinned one character for character:

- `test_098::test_ac15_golden_verdict_and_findings_unchanged`
- `test_102_stage18_validation::test_ac5_report_verdict_and_findings_match_pre_098_snapshot`, which uses test_098's `_finding_summary` and then `==`
- `test_123_recalibrate_and_regenerate::test_ac28_pinned_snapshot_reasons_equal_committed_golden_reasons`, which compares the `displace` reason with `==`

On another platform, each of the three fails on a one-digit difference that is not a real change (insight `2026-10-05-87c9`).

This item adds one comparison helper to test_098, `_assert_findings_match`, together with the reason-level check it is built on, `_assert_reason_matches`. All three comparisons route through them; test_123 compares a single reason, so it calls `_assert_reason_matches` directly. The comparison checks:

- verdict, finding count and order, `rule_id`, `severity`, `labels`, integer tokens and all non-numeric reason text **exactly**;
- each **decimal token** in a reason within one unit of the last rendered decimal place of the pinned token.

**2. A determinism check is too loose.**
`tests/test_082_verse_build_recipe.py::test_adv_determinism_two_builds_produce_equal_parsed_artifacts` compares two `segfacet build-reference` builds from the same session with `reports_close`, which applies a numeric tolerance. Every sibling determinism test asserts byte identity. With the tolerance, run-to-run nondeterminism in the CLI build path passes unnoticed (insight `2026-10-09-bc75`). This item changes it to `read_bytes()` byte identity.

**Not in scope:**
- `test_098::test_ac12_hand_set_fragmentation_findings_match_frozen_snapshot` stays exact. Its floats are integer ratios of voxel counts (`9796/18631`, `19437/19464`), and IEEE division gives the same result on every platform. Only a voxel-count change can move them, and that is a real change.
- The other readers of the constant are not touched. 089 and 108 compare border/coverage findings without floats, 090 and 094 compare the verdict only, 143 compares `(rule_id, severity, labels)` triples, 132 checks the constant's structure, and 102's `test_ac6` asserts *inequality*.
- `tests/committed_artifact_guard.py` (item 225) is not touched. Neither change reads a committed path.

## Acceptance Criteria

- [ ] **AC1: A last-digit difference in a rendered decimal passes AC15.** `test_098::test_ac15_golden_verdict_and_findings_unchanged("displace")` returns without raising when the pinned `displace` reason has its `14.6` token replaced by `14.7`, which is one unit in the last rendered place.
- [ ] **AC2: A changed verdict fails AC15.** `test_ac15_golden_verdict_and_findings_unchanged("displace")` raises `AssertionError` when the pinned `displace` verdict is replaced by `"pass"`.
- [ ] **AC3: A decimal token more than one unit off fails AC15.** `test_ac15_golden_verdict_and_findings_unchanged("displace")` raises `AssertionError` when the pinned `14.6` token is replaced by `14.8`.
- [ ] **AC4: An integer token changed by one fails AC15.** `test_ac15_golden_verdict_and_findings_unchanged("fragment")` raises `AssertionError` when the pinned `fragment` reason has `9796` replaced by `9797`.
- [ ] **AC5: Changed non-numeric reason text fails AC15.** `test_ac15_golden_verdict_and_findings_unchanged("displace")` raises `AssertionError` when the pinned reason has `left-right` replaced by `anterior-posterior`.
- [ ] **AC6: A changed finding label fails AC15.** `test_ac15_golden_verdict_and_findings_unchanged("displace")` raises `AssertionError` when the pinned `displace` finding's `labels` is replaced by `[21]`.
- [ ] **AC7: test_102's snapshot comparison tolerates a last-digit difference.** `test_102_stage18_validation::test_ac5_report_verdict_and_findings_match_pre_098_snapshot` returns without raising when it is called with `case_id="displace"` and a `block_b` mapping whose `displace` report is the pinned verdict plus the pinned findings with `14.6` replaced by `14.7`.
- [ ] **AC8: test_123's AC28 tolerates a last-digit difference.** `test_123_recalibrate_and_regenerate::test_ac28_pinned_snapshot_reasons_equal_committed_golden_reasons` returns without raising when the pinned `displace` reason has `14.6` replaced by `14.7`.
- [ ] **AC9: A one-byte build difference fails the determinism test.** `test_082_verse_build_recipe::test_adv_determinism_two_builds_produce_equal_parsed_artifacts` raises `AssertionError` when the second `build-reference` artifact differs from the first only by one extra trailing newline byte. The two files still parse to equal JSON.

## Assumptions

- **A1 (owner, 2026-10-12): the tolerance width.** The owner chose this width in the clarify round. A decimal token passes when `|got - pinned| <= 10**-d`, where `d` is the number of digits after the point in the **pinned** token. Integer tokens and all non-numeric text stay exact. Item 078's `GOLDEN_REL_TOL`/`GOLDEN_ABS_TOL` were rejected: 14.6 and 14.7 differ by about 0.7%, which fails at a relative tolerance of 1e-9.
- **A2 (owner, 2026-10-12): the scope.** The owner chose to cover the three exact-reason comparisons of the constant (098 AC15, 102 `test_ac5`, 123 AC28). AC12 stays exact.
- **A3: what counts as a decimal token.** A decimal token is a match of `\d+\.\d+`, a digit run, a point, and a digit run. An integer followed by sentence punctuation (`"label 22 (L3)."`) is not one, so it stays exact. The rule also covers the threshold clause `(threshold {_DEFAULT_MAX_OFFSET_MM:.1f} mm)`. That clause is built from the live constant, so it cannot drift from the code, and tolerating it costs nothing.
- **A4: the same format renders both sides.** The fresh reason and the pinned reason render each decimal with the same format, so they have the same number of places. The width is taken from the pinned token. If a fresh token has more places, its value is still compared within that width.
- **A5 (measured 2026-10-12, Linux, `.venv`): byte identity already holds.** Two `build-reference` runs from one process, made through test_082's own `_write_verse_shaped_cohort` and `_run_build_reference`, wrote byte-identical artifacts (48750 bytes). Neither artifact contains the out path or the cohort path, and `--build-date` is pinned. So the tightened test passes on today's code, and this item needs no production change.
- **A6 (grep 2026-10-12): these exact-reason comparisons are the only ones.** No other comparison of a fresh reason against `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS` is exact. The other readers are listed in the Description's scope fence.

## Implementation Steps

1. **Add the helpers to `tests/test_098_stray_components.py`**, next to `_finding_summary`.
   - Add a module-level regex `_DECIMAL_TOKEN = re.compile(r"\d+\.\d+")`.
   - Add `_assert_reason_matches(got: str, pinned: str) -> None`:
     - Compare the two strings with every decimal token replaced by one placeholder; they must be equal exactly.
     - Pair the tokens from `_DECIMAL_TOKEN.findall` on each side.
     - Assert `abs(Decimal(g) - Decimal(p)) <= Decimal(1).scaleb(-d)`, where `d = len(p.split(".")[1])`. Use `decimal.Decimal` (stdlib), not float subtraction: in floats, `14.7 - 14.6` is `0.10000000000000142 > 0.1`.
     - The `AssertionError` message names both reasons and the token that differs.
   - Add `_assert_findings_match(got_findings, pinned_findings, *, include_reason) -> None`:
     - Build `_finding_summary`-shaped dicts with the reason left out.
     - Assert the structure with `segfacet.synth.golden.reports_close`, item 078's helper, reused rather than re-implemented. Its leaves here are strings and integer lists, which it compares exactly, and it also fixes list length and order.
     - Then, when `include_reason` is true, call `_assert_reason_matches` on each pair.
2. **Route `test_ac15_golden_verdict_and_findings_unchanged` through the new helper.**
   - Keep `assert fresh["verdict"] == expected["verdict"]` exact.
   - Replace the `got_findings == expected_findings` comparison with `_assert_findings_match(fresh["findings"], expected["findings"], include_reason=...)`.
   - Keep the function name, its `(case_id)` signature, its `_FACE_NAME_SENSITIVE_CASES` handling, and the `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS` name inside its source.
3. **Fix the stale AC16 bullet in test_098's module docstring.** The bullet currently reads "``reports_close`` against the committed goldens still hold". Item 126 retired those goldens and discharged the tolerance test. Restate the bullet as the surviving intra-run byte-determinism check, and keep the docstring's AC18 bullet (the one naming `reference_verse_v1.json`) unchanged.
4. **Update `tests/test_102_stage18_validation.py` `test_ac5_report_verdict_and_findings_match_pre_098_snapshot`.**
   - Replace its `got_findings == expected_findings` with `_assert_findings_match`, imported from `test_098_stray_components` next to the existing imports.
   - Keep `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS` imported and named in this module.
5. **Update `tests/test_123_recalibrate_and_regenerate.py` `test_ac28_pinned_snapshot_reasons_equal_committed_golden_reasons`.** Replace `assert mode1_actual == mode1_expected` with `_assert_reason_matches(mode1_actual, mode1_expected)`, imported from `test_098_stray_components` inside the function. That is where the constant is already imported.
6. **Update `tests/test_082_verse_build_recipe.py`.**
   - Replace the two `json.loads(...)` plus `reports_close(parsed1, parsed2)` with `assert out_path1.read_bytes() == out_path2.read_bytes()`.
   - Replace the eigenvalue_ratio tolerance comment with one line saying that two builds in one process must be byte-identical (the item 078 tolerance is for comparisons across platforms).
   - Delete the `from segfacet.synth.golden import reports_close` import if nothing else in the module uses it.
   - Keep the test's name.

No dependency is added. `re` and `decimal` are stdlib, and `reports_close` is already in `segfacet.synth.golden`.

## Authorised paths

**May change:**

- `tests/test_098_stray_components.py`: the two helpers, AC15 rerouted, and the docstring bullet. Siblings 218 and 219 also edit this module's constant.
- `tests/test_102_stage18_validation.py`: `test_ac5` routed through `_assert_findings_match`.
- `tests/test_123_recalibrate_and_regenerate.py`: AC28 routed through `_assert_reason_matches`.
- `tests/test_082_verse_build_recipe.py`: the determinism test changed to byte identity, and the unused import dropped.
- `tests/test_224_platform_tolerant_snapshots.py`: this item's AC tests.

**Asserts against:**

None.

## Testing Strategy

The tests for this item go in a new module, `tests/test_224_platform_tolerant_snapshots.py`, with one test per AC. Each test drives the **real** test function rather than the helper alone. That way it proves that the shipped comparison is the one that tolerates or catches the change.

- **AC1–AC6:**
  - `monkeypatch.setitem` sets `test_098_stray_components._PRE_098_GOLDEN_VERDICT_AND_FINDINGS[case_id]` to a `copy.deepcopy` of the entry with the one mutation applied. The test never mutates the shared constant in place, because eight modules import it.
  - The test then calls `test_ac15_golden_verdict_and_findings_unchanged(case_id)` and expects either a clean return or `pytest.raises(AssertionError)`.
- **AC7:** call test_102's `test_ac5_report_verdict_and_findings_match_pre_098_snapshot(block_b, "displace")` directly, with a hand-built `block_b = {"displace": {"verdict": ..., "findings": [...]}}`. This avoids the nine-CLI-run fixture.
- **AC8:** monkeypatch the `displace` entry as in AC1, then call test_123's AC28 function.
- **AC9:**
  - `monkeypatch.setattr` replaces test_082's module-level `_run_build_reference` with a wrapper. The wrapper calls the original and, on its second call, appends `b"\n"` to the file it wrote, using `open(path, "ab")`.
  - The test calls `test_adv_determinism_two_builds_produce_equal_parsed_artifacts(tmp_path)` under `pytest.raises(AssertionError)`.
  - It also asserts that the two files' `json.loads(p.read_text(encoding="utf-8"))` results are equal, which shows the mutation is invisible to the old `reports_close` comparison.

**Keep `tests/test_224_platform_tolerant_snapshots.py` off the Windows subset.** `tests/test_213_windows_ci_subset.py` walks the AST of every `tests/test_*.py` module. A module that shows any of its signals must be listed in `ci.yml`'s `WINDOWS_TESTS`, and this item does not authorise `ci.yml`. So the new module must not contain any of the following:

- `.read_bytes`, a `newline=` keyword, or a `.gitattributes` string;
- an import of `segfacet.cli`, or a string starting with `segfacet.cli`;
- `subprocess`, `run_process` or `sys.executable`;
- `.as_posix`, `os.sep` or `PureWindowsPath`.

It reaches the CLI only indirectly, by importing `test_082_verse_build_recipe` and calling its function. That leaves test_224 with no signal in its own AST.

**Adversarial cases:**

- **pinned-precision width:** in the `fragment` reason, `0.52579` → `0.52581` (two units at `d=5`) makes AC15 raise. This guards against a width fixed at `0.1`, or one derived from the coarsest token.
- **integer-stands-in-for-decimal:** in the `displace` reason, the pinned `14.6` replaced by the integer `15` makes AC15 raise. This guards against a placeholder substitution that lets an integer token fill a decimal slot.
- **extra-finding:** appending a copy of the first pinned `relabel_swap` finding makes AC15 raise. After the append the pinned list has `len(pinned) + 1` findings and the fresh one has `len(pinned)`, where `len(pinned)` is the length of the entry as it stands when the test runs. Item 219 changes that length, so the test computes it and hard-codes no count. This guards against a pairwise `zip` that silently truncates to the shorter list.

No other adversarial case, and no AC, depends on a count taken from the constant. Each one mutates a single named token or field of an entry (`displace`, `fragment`) that neither item 218 nor item 219 changes.

**Existing tests to reconcile** (each found by grep, and none expected to need an edit):

- **The constant's name, and the `test_ac15_…` name and signature, are kept.** These tests depend on them:
  - `tests/test_105_golden_decision_table.py` (`_PRE_098_*` identifiers in test_098 and test_102 source)
  - `tests/test_107_item_scope_check.py` (three test_098 `def` names)
  - `tests/test_126_golden_retirement.py` AC6, AC7 and AC13 (AC15 source names the constant and no golden marker; test_123 AC28 has no golden marker)
  - `tests/test_135_stage29_validation.py` (the same check as test_126 on AC15)
  - `tests/test_132_monotonicity_against_traversal_order.py` AC26, which calls `test_ac15_…("relabel_swap")` directly
- **No golden marker is introduced.** `_GOLDEN_MARKERS_WITH_PATH` covers `GOLDEN_DIR`, `load_golden`, `read_golden_text`, `check_case_golden` and `tests/corpus/golden`. The new helpers are called from AC15 and test_123 AC28, so their bodies and call sites must use none of these.
- **The new byte comparison in test_082 is not a fence.** It compares `tmp_path` files with `read_bytes()` and uses no `sha256`, so `tests/test_115_stage26_validation.py`'s fence scanner does not see it. `tests/committed_artifact_guard.py` does not see it either, because neither path is committed.
- **The Windows CI subset is unchanged (checked 2026-10-13).** `tests/test_213_windows_ci_subset.py::test_ac5_list_is_exactly_the_os_sensitive_set` scans existing modules too. Once this item lands, test_082 contains `read_bytes()`, which is a `bytes` signal. But test_082 is already in `WINDOWS_TESTS` (`.github/workflows/ci.yml` line 122), because its `from segfacet.cli import main` gives the `cli` signal. So its membership does not change. test_098, test_102 and test_123 are already listed too, and none of them loses a signal. The comparison therefore stays in its plain `read_bytes()` form, and `ci.yml` is not authorised.
- **Items 218 and 219 also edit test_098's constant.** Whichever item merges later rebases its constant edits onto the other's. This item changes no entry of the constant.

## Dependencies

None.

## Decisions & Trade-offs

- Implemented as specified; no production code changed. `_assert_findings_match` zips the reason check after `reports_close` has fixed list length and order, so a length mismatch fails before the pairwise loop. `_assert_reason_matches` normalises decimal tokens to a placeholder, which makes an integer standing in for a decimal fail the exact-text step.

- **Left open:** whether a real 0.1 mm move of the `displace` offset should be caught by a test that pins the offset value directly. Under A1 the reason comparison tolerates one unit in the last place, and no test pins the number today outside its reason string. The verdict, rule and labels stay exact. A direct pin on the value is a new assertion that no recorded defect asks for.
