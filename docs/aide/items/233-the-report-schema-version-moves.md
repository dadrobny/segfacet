<!-- aide-template: item 3 -->
# Item 233 — The report schema version moves whenever a feature path moves

> **Created:** 2026-10-18 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 35 — Programme Interface: the SegFACET Side
> **Queue:** [`../queue/queue-031.md`](../queue/queue-031.md) · Item 233
> **Objectives:** G7
> **Suggested branch:** `aide/233-the-report-schema-version-moves`

---

## Description

This item is the schema half of Stage 35's fourth deliverable, artefact
versioning. The deliverable asks for "a report `schema_version` that moves
whenever a feature path moves". Item 232 delivered the other half, the
`facet_revision` block.

The per-case report's `schema_version` is the module constant
`_REPORT_SCHEMA_VERSION = "0.1"` in `src/segfacet/report.py`. The bundled
schema `src/segfacet/report_schema_v0.json` fixes it with `"const": "0.1"`.
Items 215 and 216 moved nearly every feature path and left the value at
`"0.1"`. Nothing in the suite ties the version to the paths, so a reader
such as `spinelab` cannot tell a pre-215 report from a current one by its
version.

The item delivers four things:

1. **One bump, now.** The report schema version becomes `"0.2"`, in the
   constant and in the schema's `const`. The constant becomes public as
   `segfacet.report.REPORT_SCHEMA_VERSION`.
2. **A committed pin**, `src/segfacet/report_schema_pin.json`. It holds one
   pair: the report schema version, and the sorted set of feature leaf paths
   that version describes. The set is the one the generated catalogue is
   built from: the union of `segfacet.catalogue.iter_leaf_paths(record)`
   over `segfacet.catalogue.iter_driver_records()`.
3. **A guard**, `segfacet.report_schema_pin.pin_conflicts()`. It compares
   the live pair with the pin and returns one readable message per
   disagreement. It returns nothing when they agree. The suite calls it on
   the shipped tree, so a path added, removed or renamed without re-pinning
   fails the suite.
4. **A re-pin route**, `python -m segfacet.report_schema_pin`. It rewrites
   the pin from live state. It **refuses** when the leaf-path set changed
   and the report schema version did not, so the documented route can only
   move a pinned set together with a new version.

**Not in scope.**
- The evaluation report's `EVAL_REPORT_SCHEMA_VERSION` and the
  `HeuristicConfig` `SUPPORTED_SCHEMA_VERSION` stay `"0.1"`. Neither carries
  feature paths.
- `features_version`, `image_features_version` and the other per-block
  version fields are untouched.
- The schema file keeps its name, `report_schema_v0.json`, because about
  twenty test modules load it by that name.
- Report keys outside the feature record, such as `facet_revision` and
  `run_manifest`, are not guarded (see Left open).

## Acceptance Criteria

- [ ] **AC1: The committed pin is the live pair.** Read through
  `segfacet.synth.golden.assert_matches_committed_artifact`,
  `src/segfacet/report_schema_pin.json` equals
  `{"schema_version": <the schema_version of a report segfacet.report.serialize_report builds>, "feature_leaf_paths": <the sorted union of segfacet.catalogue.iter_leaf_paths(record) over every segfacet.catalogue.iter_driver_records() record>}`.
- [ ] **AC2: The shipped tree has no pin conflict.**
  `segfacet.report_schema_pin.pin_conflicts()`, called with its defaults,
  returns `()`.
- [ ] **AC3: An added feature path without a version change is a
  conflict.** `segfacet.catalogue.iter_driver_records` is replaced by a
  wrapper that yields the real records, with one extra top-level leaf key
  added to a deep copy of the first. The report schema version is left
  unchanged. `pin_conflicts()`, called with its defaults, then returns a
  non-empty tuple, and one of its strings contains the added key.
  *(closes Stage 35 criterion 3)*
- [ ] **AC4: A renamed feature path without a version change is a
  conflict.** Take the live leaf set, remove one real path `P` and add a new
  path `Q`. `pin_conflicts(live_paths=<that set>)`, with the report version
  left at its default, returns a non-empty tuple whose joined text contains
  both `P` and `Q`. *(closes Stage 35 criterion 3)*
- [ ] **AC5: Re-pinning a changed set under an unchanged version is
  refused.** Create a pin file under `tmp_path` with
  `repin(pin_path=..., live_paths=<live set>, report_version=<current version>)`.
  A second `repin` with a renamed set and the same version then raises
  `segfacet.report_schema_pin.PinError`. After the refusal, the pin file's
  text equals its text before the call.
- [ ] **AC6: A renamed path with a version change and a re-pinned set
  passes.** Create a pin under `tmp_path` as in AC5. Call `repin` again with
  a renamed set and a report version different from the pinned one. Then
  `pin_conflicts(live_paths=<renamed set>, report_version=<that version>, pin_path=<same file>)`
  returns `()`.
- [ ] **AC7: The report schema version has moved off the pre-215 value.**
  The `schema_version` of a report `segfacet.report.serialize_report`
  builds is not `"0.1"`. `"0.1"` is the value that described the feature
  paths before items 215 and 216 moved them.

## Assumptions

- **A1 (the new version string, a defensible default).** The bump is
  `"0.1"` to `"0.2"`. It follows the minor-increment style of the record's
  other version fields: `features_version` went `0.2` to `0.3` and
  `image_features_version` went `1.0` to `1.1` in item 215. Nothing in this
  repository branches on the report value. The schema's `const` moves with
  it, because `serialize_report` validates every report against the schema.
- **A2 (which leaf-path set is pinned).** "The leaf-path set the catalogue
  already generates" is the union of `iter_leaf_paths(record)` over
  `iter_driver_records()`. `build_catalogue` builds one entry per element of
  exactly that union (`src/segfacet/catalogue.py`, the `for path in
  sorted(leaf_union)` loop, read 2026-10-18). `tests/test_104_feature_catalogue_drift.py`
  already keeps the committed `docs/aide/feature_catalogue.generated.json`
  equal to that build. The pin is therefore computed from the primitives
  and not from the committed catalogue file or from `build_catalogue`. A
  derived file would be a second-hand source, and `build_catalogue` also
  computes observed ranges and rule attribution, which the pin does not
  need. Paths are relative to the transient rule-evaluation record, as in
  the catalogue: `per_label.{label}.…`, `case.…`, `image_features.…`,
  `reference_delta.…`. They are not the report's `features.` prefix, and
  that prefix is fixed, so it cannot move a leaf.
- **A3 (the pin's location).** The pin lives in `src/segfacet/`, beside the
  schema it versions, and not in `tests/golden/`. There are two reasons:
  - `tests/test_135_stage29_validation.py` asserts that `tests/golden/`
    holds exactly `report_format_contract.json`;
  - `tests/test_105_golden_decision_table.py` AC3 counts every non-`.py`
    file under `tests/` against `docs/aide/golden-decision-table.md`.
  So a pin under `tests/` would break two tests that have nothing to do
  with it. The pin is package data under hatchling's
  `packages = ["src/segfacet"]`, as `report_schema_v0.json` is.
- **A4 (what the refusal protects, and what it cannot).** `repin` refuses
  only the documented route. A hand edit of the pin's path list under an
  unchanged version passes the suite, just as a hand edit of any committed
  artefact does. The suite cannot detect that edit without comparing
  against git history, and a history probe is the guard shape that passes
  vacuously once its base advances (`REVIEW.md`, Important tier). The
  module docstring and the conflict message name `repin` as the only way
  to re-pin.
- **A5 (no CI change expected).** The new test module reads files with
  `read_text` and calls `segfacet.report_schema_pin` in-process. It never
  spawns a process, imports `segfacet.cli`, or calls `.read_bytes`, so
  `tests/test_213_windows_ci_subset.py` flags none of its signals.
  `.github/workflows/ci.yml` is authorised only for the case where the
  module does carry a signal.

## Implementation Steps

1. **`src/segfacet/report.py`.**
   - Rename `_REPORT_SCHEMA_VERSION` to `REPORT_SCHEMA_VERSION`, set it to
     `"0.2"`, and add it to `__all__`. `report.py` is the only file that
     uses the old name (grep, 2026-10-18).
   - Replace the "always '0.1' for v0" comment with a pointer to
     `segfacet.report_schema_pin`.
2. **`src/segfacet/report_schema_v0.json`.**
   - Set `properties.schema_version.const` to `"0.2"`.
   - Reword its description so it states no literal value. It should say
     the version moves whenever a feature leaf path moves, and point to
     `report_schema_pin.json`.
3. **New `src/segfacet/report_schema_pin.py`.** Stdlib `json` and `pathlib`
   only. Heavy imports happen inside the functions: call
   `from segfacet import catalogue` there and read
   `catalogue.iter_driver_records` at call time, so that AC3's replacement
   takes effect.
   - `PIN_PATH`: `Path(__file__).resolve().parent / "report_schema_pin.json"`.
   - `class PinError(ValueError)`.
   - `live_leaf_paths() -> frozenset[str]`: the A2 union, built with
     `catalogue.iter_leaf_paths` and nothing new.
   - `pin_conflicts(*, live_paths=None, report_version=None, pin_path=PIN_PATH) -> tuple[str, ...]`.
     The defaults are `live_leaf_paths()` and
     `segfacet.report.REPORT_SCHEMA_VERSION`, both read at call time. It
     returns one message for each of these cases, and `()` otherwise. It
     never raises:
     - the pin file is missing or unreadable (the message names the path);
     - the live set is empty;
     - the pinned version differs from the report version (the message
       names both);
     - the pinned set differs from the live set (the message lists the
       added and removed paths, sorted).
     Every message ends with the remedy: bump `REPORT_SCHEMA_VERSION` and
     the schema `const`, then run `python -m segfacet.report_schema_pin`.
   - `repin(*, live_paths=None, report_version=None, pin_path=PIN_PATH) -> None`.
     It uses the same defaults. If an existing pin's version equals
     `report_version` and its set differs from `live_paths`, it raises
     `PinError` naming the added and removed paths, and writes nothing.
     Otherwise it writes
     `{"schema_version": ..., "feature_leaf_paths": sorted(...)}` as
     `json.dumps(..., indent=2) + "\n"`, through `write_bytes` of the UTF-8
     encoding.
   - `main(argv=None) -> int`. It calls `repin()`. On `PinError` it prints
     the message to stderr and returns 1. Otherwise it returns 0. It also
     has a `__main__` guard.
   - The module docstring carries the item number, the A4 limit, and a
     scope fence: it changes no extractor, rule, catalogue or report shape.
4. **Generate the pin.** Run `.venv/bin/python -m segfacet.report_schema_pin`
   after step 1, so the first pin records `"0.2"`, and commit
   `src/segfacet/report_schema_pin.json`.
5. **Regenerate the format contract.** Run
   `.venv/bin/python -m tests.report_format_fixture`, which is the only
   source of `tests/golden/report_format_contract.json`. Its
   `schema_version` becomes `"0.2"`. `tests/report_format_fixture.py` is
   not edited.
6. **Reconcile the existing tests** listed under Testing Strategy. Replace
   each report-version literal `"0.1"` with
   `segfacet.report.REPORT_SCHEMA_VERSION`, so the next bump does not
   revisit them. Leave every config-version `"0.1"` (`HeuristicConfig`,
   YAML) unchanged.
7. **`.github/workflows/ci.yml`**: only if
   `tests/test_233_report_schema_pin.py` carries a `test_213` signal, add it
   to `jobs.test.env.WINDOWS_TESTS` in sorted position (A5).

No dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/report.py` — `REPORT_SCHEMA_VERSION`, public and bumped to `"0.2"`
- `src/segfacet/report_schema_v0.json` — the `schema_version` const and description
- `src/segfacet/report_schema_pin.py` — new: live pair, `pin_conflicts`, `repin`, `main`
- `src/segfacet/report_schema_pin.json` — new: the committed pin, written by `repin`
- `tests/golden/report_format_contract.json` — regenerated by `tests.report_format_fixture`
- `tests/test_233_report_schema_pin.py` — new: this item's tests
- `tests/test_009_json_report.py` — report-version literal reconciled
- `tests/test_010_pipeline.py` — report-version literal reconciled
- `tests/test_016_features_json.py` — report-version literal and schema-const literal reconciled
- `tests/test_035_report_integration.py` — schema-const literal reconciled
- `tests/test_042_golden_determinism.py` — report-version literal reconciled
- `tests/test_061_image_features_fusion.py` — report-version literal reconciled
- `tests/test_069_container_smoke.py` — report-version literal reconciled (Docker-gated)
- `tests/test_cli_run.py` — report-version literals reconciled
- `.github/workflows/ci.yml` — only if the new test module carries a `test_213` signal

**Asserts against:**

- `src/segfacet/catalogue.py` — AC1 and AC3 read `iter_driver_records` and `iter_leaf_paths`, and AC3 replaces `iter_driver_records` only through monkeypatch

## Testing Strategy

The new module is `tests/test_233_report_schema_pin.py`, with one test per
AC.
- Compute the live leaf set once in a module-scoped fixture, from
  `segfacet.catalogue.iter_driver_records()` and `iter_leaf_paths`. The test
  computes it itself and never calls `live_leaf_paths()`.
- AC1's test must first assert that set is non-empty, so an empty driver
  set cannot pass by matching an empty pin.
- Build reports with `serialize_report` on a minimal `Verdict` and
  `segfacet.config.default_config()`, the way `tests/test_009_json_report.py`
  does.
- AC5 compares `read_text(encoding="utf-8")` before and after the refused
  call. Do not use `read_bytes`, because it is a `test_213` signal (A5).
- AC3 uses `monkeypatch.setattr(segfacet.catalogue, "iter_driver_records", …)`.
  Its extra key is a name no real record has, such as `"zz_item233_added_leaf"`.
- AC4 and AC6 rename by removing the lexicographically first live path and
  adding `"<that path>_item233_renamed"`.

Adversarial cases. Write these and no others:

- `missing-pin`: `pin_conflicts(pin_path=tmp_path / "absent.json")` returns
  a non-empty tuple naming that path and does not raise. This guards a
  guard that passes vacuously, or crashes the collection, once the file it
  checks against disappears.
- `empty-live-set`: create a pin under `tmp_path` with
  `repin(live_paths=frozenset(), report_version=<current>)`. Then
  `pin_conflicts(live_paths=frozenset(), pin_path=<that file>)` is
  non-empty. This guards a guard that agrees when the driver records stop
  realising any leaf at all, with an empty pin matching an empty live set.

**Existing tests to reconcile.** A grep of `tests/` found these. It
searched for a report `schema_version` compared to `"0.1"` (subscript and
`.get` forms) and for the report schema's `const` compared to `"0.1"`. It
is a lower bound, and the builder's full-suite run is the check.
- `tests/test_009_json_report.py`: lines 551, 683, 709, 889 and 922.
  Line 925's `!=` against `config_version` still holds.
- `tests/test_010_pipeline.py`: line 131.
- `tests/test_016_features_json.py`: line 247 (the report value) and line
  255 (the schema `const`).
- `tests/test_035_report_integration.py`: line 132 (the schema `const`).
  `test_ac10_schema_version_stays_0_1` keeps its name. Its docstring says
  the const equals `REPORT_SCHEMA_VERSION`.
- `tests/test_042_golden_determinism.py`: line 165.
- `tests/test_061_image_features_fusion.py`: line 283.
- `tests/test_069_container_smoke.py`: line 250. It is Docker-gated, and
  the image builds from this tree.
- `tests/test_cli_run.py`: lines 104, 297, 434, 471 and 516.

The following hits pin a different version and stay as they are:
- eval-report versions in `tests/test_056_eval_report.py` (lines 271, 289
  and 310) and `tests/test_101_per_mode_cohort.py` (lines 1314–1315);
- the `"0.1"` eval-report literal in `tests/test_153_eval_harness_rekey.py`
  line 706;
- every `HeuristicConfig`/YAML `schema_version` `"0.1"`, for example in
  `tests/test_035_default_config.py`, `tests/test_005_adversarial.py` and
  `tests/test_090_reference_derived_defaults.py` line 855.

`tests/golden/report_format_contract.json` changes only by
regeneration (step 5). The tests that compare against it
(`test_016`, `test_022`, `test_111`, `test_126`, `test_135`) need no edit.

## Validation

Replay from the repository root on the claim branch:

1. Run `.venv/bin/python -m segfacet.report_schema_pin`. It exits 0, and
   `git status --porcelain` lists nothing afterwards: re-pinning an
   unchanged tree is a no-op.
2. Run `.venv/bin/segfacet run --scan <clean_control scan> --seg <clean_control seg> --out <scratch>/run --no-reference`,
   taking the paths from `tests/corpus/manifest.json`. Check that
   `schema_version` in `<scratch>/run/segfacet_report.json` equals the
   pin's `schema_version`.

No special environment is needed.

## Dependencies

None.

**Downstream:** item 235 (stage validation) attests Stage 35 criterion 3
from item 232's AC1/AC3 together with this item's AC3/AC4.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether a move of a report key outside the feature record
  (`facet_revision`, `run_manifest`, `findings`, top-level keys) also bumps
  the version under a guard. The deliverable names feature paths, and
  `tests/golden/report_format_contract.json` already pins the report's key
  set.
- **Left open:** whether the evaluation report's `schema_version` gets the
  same tie. Its body carries metrics, not feature paths, and no consumer
  in the batch reads it as a feature-shape discriminator.
- **Left open:** a `.gitattributes` `eol=lf` pin for
  `report_schema_pin.json`. Every reader parses it with `json.loads`, and
  nothing compares its bytes, so CRLF on checkout changes nothing the
  suite reads.
- **Left open:** a row for the pin in `docs/aide/golden-decision-table.md`
  Section 2. That section is fixed at seven named artefacts by
  `tests/test_105_golden_decision_table.py` AC9, and the pin is compared
  through `assert_matches_committed_artifact`, not byte-for-byte.
