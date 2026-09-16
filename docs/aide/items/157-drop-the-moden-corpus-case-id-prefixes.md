<!-- aide-template: item 1 -->
# Item 157 — Drop the `modeN_` corpus case-id prefixes

> **Created:** 2026-09-17 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update
> **Queue:** [`../queue/queue-021.md`](../queue/queue-021.md) · Item 157
> **Objectives:** G7, G8
> **Suggested branch:** `aide/157-drop-the-moden-corpus-case`

---

## Description

Roadmap Stage 31 D4, the case-id part. Eight geometric corpus case ids still
carry `modeN_` prefixes from the Stage 5 catalogue. After item 150 re-keyed the
modes, those prefixes no longer name the mode the case carries. The manifest's
`failure_mode` field is the authority, and the prefix is a second copy of it
that goes wrong whenever a case moves:

| Old id | Manifest `failure_mode` / `kind` (2026-09-17) | New id |
|---|---|---|
| `mode1_displace` | 1 / failure | `displace` |
| `mode2_fragment` | 1 / failure | `fragment` |
| `mode3_inject_islands` | 4 / failure | `inject_islands` |
| `mode4_relabel_swap` | 9 / failure | `relabel_swap` |
| `mode5_remove_level` | 6 / failure | `remove_level` |
| `mode6_crop_at_border` | 0 / condition | `crop_at_border` |
| `mode7_sequence_break` | 9 / failure | `sequence_break` |
| `mode8_force_overlap` | 15 / failure | `force_overlap` |

**Decided by the maintainer at queue-021's review (2026-09-16): rename, dropping
the prefix.** Re-prefixing with the signed-off ids was declined: a prefix would
still copy the manifest field, would not be unique (modes 1, 6 and 9 each have
two cases), and has no form for the condition case. Each new id is the name of
the case's perturbation operator. That matches the six ids that already carry no
mode (`fuse_adjacent`, `remove_level_relabel`, `clean_hu`, `implausible_metal`,
`implausible_soft_tissue`, `degenerate_uniform`).

This item changes corpus values in one pass: the generator's `CASE_RECIPE`, the
committed geometric manifest, the eight `_seg.nii.gz` fixture file names, every
live pin of the ids, and the generated artifacts that render them.

### The measured pin set (2026-09-17, at `b30b91e`)

The queue's count ("79 files") was taken before items 152–156. Measured again
with an exact-token `grep -rlE` for the eight old ids across the working tree
(`.venv` and `.git` excluded):

- **66 tracked files outside the loop's records**, plus **8 fixture file names**:
  - `src/segfacet/` — **10** modules: `failure_modes.py` (8 `CorpusCaseExpectation.case_id`
    values and 9 mechanism/reason strings, all rendered into the generated
    artifacts, plus 6 docstring mentions); `heuristics/{border,coverage,fragmentation,mislabel,overlap,sequence}.py`
    (declaration evidence strings rendered into the traceability matrix, plus
    `mislabel.py` docstring); `heuristics/rule.py` (docstring);
    `synth/corpus.py` (`CASE_RECIPE`); `synth/golden.py` (comment).
  - `tests/` — **44** test modules plus **2** committed JSON fixtures
    (`tests/corpus/manifest.json`, `tests/corpus/094_pre_migration_snapshot.json`).
  - `scripts/rebuild_verse_reference.py` — **1** comment.
  - Generated artifacts — **5**: `docs/aide/failure_modes.generated.{json,md}`,
    `docs/aide/traceability_matrix.generated.{json,md}`,
    `docs/aide/golden_evidence.generated.json`.
  - Hand-written docs — **4**: `docs/aide/golden-decision-table.md`,
    `docs/corpus-s-axis-correction.md`, `docs/reference-build.md`,
    `docs/aide/failure-mode-taxonomy-handover.md`.
  - `tests/corpus/fixtures/mode{1..8}_*_seg.nii.gz` — **8** file names.
- **Zero** hits in `.gitattributes`, `README.md`, `CLAUDE.md`, `.github/`,
  `tests/corpus/intensity/`, `docs/aide/feature_catalogue.generated.*`, and
  `tests/corpus/119_pre_119_digests.json`.
- **Nothing derives a mode from a case id.** No `startswith`/`split`/slice/regex
  over a case id parses the prefix anywhere in `src/`, `tests/` or `scripts/`.
  The only text operation on a case id is
  `tests/test_088_stage13_acceptance.py:166`'s `startswith("sub-verse")`, which
  is about a real VerSe case.
- **Regex false positives.** A loose `mode[1-8]_(…)` pattern also matches
  `mode4_sequence_break` and `mode5_sequence_break` inside test names at
  `tests/test_099_per_mode_metrics.py:660,706,716`. Those are not case ids. Any
  scan or sed must match the eight exact tokens.
- **Not tracked, so out of scope:** `docs/aide/status/index.html` and
  `docs/aide/permissions/log*.jsonl`. Both are gitignored per-machine output.

### Live pins versus historical references

Most of the 44 test modules look an old id up against the live tree: a
manifest lookup, a fixture path, `CASE_RECIPE`, a `SPECIFICATION` corpus case, a
generated-artifact key, or a `_PRE_*` per-case table whose keys
`_cases_covered_by` must find in the manifest. Those literals become the new ids.

Some references resolve against a record that keeps the old name forever. Those
must **not** change to the new literal. They reach the old name through the
mapping this item adds (`segfacet.synth.corpus.RENAMED_CASE_IDS`, see AC1):

- `tests/test_116_ras_native_corpus.py:343-353` — `git show
  aeb2f55:tests/corpus/golden/{case_id}.json`. The test is parametrised over
  live manifest cases, so the id it passes to git history must be the old one.
- `tests/test_126_golden_retirement.py:67-74` `_CASE_IDS` is used both ways.
  Its manifest and companion lookups (lines 150-158, 1005-1026) are live. Its
  `_RETIRED_PATHS` feed `git log --follow` on deleted files (lines 166-200),
  which is historical. `_AC18_PRE_ITEM_ROW_DIGESTS` (lines 764-776) is keyed by
  retired `tests/corpus/golden/<old>.json` paths, also historical.
- `tests/test_105_golden_decision_table.py:363-373` `_GOLDEN_CASE_IDS` is used
  both ways. The companion and manifest lookups (AC7) are live. The
  `/{cid}.json` suffix match over the decision table's retired rows (AC9, line
  422) is historical.
- `tests/test_134_decision_table_evidence_companion.py:88-98` `_GOLDEN_CASE_IDS`
  is used only for the retired-row suffix match, so it is historical.
- `tests/test_143_s_axis_correction.py:722-730` (AC16) compares live
  manifest fixture paths for equality against the rows of
  `docs/corpus-s-axis-correction.md`, item 143's dated record. The record keeps
  the old names, so the live paths are mapped back to old names before the
  comparison.

### Records that keep the old names

The following are not edited. They record what was true under the old names:

- merged item specs, `insights.md` and its archives, `roadmap.md`,
  `progress.md`, the queue files;
- `docs/corpus-s-axis-correction.md` (item 143's dated comparison record);
- `docs/aide/failure-mode-taxonomy-handover.md` (a dated handover);
- in `docs/aide/golden-decision-table.md`, the eleven **retired** Section-1 rows
  and the `## Retirement execution log`. Those name files deleted under their
  old names, and `test_134`'s AC10 and `test_126`'s AC18 guard them.

A reader meets the mapping in two places: `segfacet.synth.corpus`'s module
docstring and `RENAMED_CASE_IDS`, and one `knowledge` line in `insights.md`.

### Living inventory rows that do change

`docs/aide/golden-decision-table.md` Section 1's eight **keep** rows (lines
174-181) and the matching `## Divergences from the roadmap's working assumption`
bullets (lines 276-291) name the live fixture files. `test_105`'s AC3 and
`test_126`'s AC20 require Section 1 to equal the files on disk, and `test_105`'s
AC13 requires the Divergences section to name exactly the keep rows. So their
fixture paths and the case id in the "what it asserts today" prose are renamed.
Their `disposition` stays `keep` and no judgement cell changes.

### Scope fence

- **No mode content changes.** No `ModeSpec` or `ConditionSpec` field changes
  other than a `CorpusCaseExpectation.case_id` value and the case-id tokens
  inside mechanism and reason strings. No `failure_mode`, `kind`,
  `expected_firing`, `expected_rule_ids`, `expected_labels`, `expected_verdict`,
  `detail` or perturbation parameter changes.
- **No fixture content changes.** The eight `.nii.gz` files are byte-identical
  under their new names. nibabel writes gzip with `mtime=0` and without an FNAME
  header field (the flag byte of the committed files is `0x00`, checked
  2026-09-17), so the file name is not in the bytes.
- **No new committed fixture.** The renamed files fall under the existing
  `tests/corpus/fixtures/*.nii.gz binary` glob, so `.gitattributes` needs no
  edit.
- The intensity corpus carries no `modeN_` id and is not touched.

## Acceptance Criteria

- [ ] **AC1: the mapping is recorded exactly.** `segfacet.synth.corpus.RENAMED_CASE_IDS` equals `{"mode1_displace": "displace", "mode2_fragment": "fragment", "mode3_inject_islands": "inject_islands", "mode4_relabel_swap": "relabel_swap", "mode5_remove_level": "remove_level", "mode6_crop_at_border": "crop_at_border", "mode7_sequence_break": "sequence_break", "mode8_force_overlap": "force_overlap"}`.
- [ ] **AC2: the mapping is a source literal.** In the AST of `src/segfacet/synth/corpus.py`, the module-level assignment to `RENAMED_CASE_IDS` has a `Dict` node whose keys and values are all `str` `Constant` nodes, so reading it performs no I/O and touches no path under `tests/`.
- [ ] **AC3: every new id is a live case.** Each value of `RENAMED_CASE_IDS` equals the `case_id` of exactly one entry in `segfacet.synth.corpus.CASE_RECIPE`.
- [ ] **AC4: no old id is a live case.** No key of `RENAMED_CASE_IDS` equals the `case_id` of any entry in `CASE_RECIPE`.
- [ ] **AC5: no committed manifest id carries a mode prefix.** No `case_id` in `tests/corpus/manifest.json` or `tests/corpus/intensity/manifest.json` matches the regex `^mode\d+_`.
- [ ] **AC6: no corpus file name carries a mode prefix.** No file or directory under `tests/corpus/`, at any depth, has a name matching the regex `^mode\d+_`.
- [ ] **AC7: every geometric seg fixture resolves by its case id.** For every case in `tests/corpus/manifest.json`, `seg_fixture == f"fixtures/{case_id}_seg.nii.gz"` and `tests/corpus/<seg_fixture>` exists as a file.
- [ ] **AC8: every specification corpus reference resolves.** Every `CorpusCaseExpectation.case_id` reachable from `failure_modes.SPECIFICATION` and `failure_modes.CONDITIONS` is the `case_id` of a case in the committed manifest its `corpus` field names (`"geometric"` → `tests/corpus/manifest.json`, `"intensity"` → `tests/corpus/intensity/manifest.json`).
- [ ] **AC9: no live surface names an old id.** A tree-wide scan finds zero matches for any key of `RENAMED_CASE_IDS` as a token (regex `(?<![A-Za-z0-9_])<old id>(?![A-Za-z0-9])`) in every tracked `*.py`/`*.json`/`*.md` file under `src/segfacet/`, `scripts/` and `tests/`, and in `docs/aide/failure_modes.generated.json`, `docs/aide/failure_modes.generated.md`, `docs/aide/traceability_matrix.generated.json`, `docs/aide/traceability_matrix.generated.md` and `docs/aide/golden_evidence.generated.json`. Exactly two files are exempt: `src/segfacet/synth/corpus.py` (the mapping and its docstring) and this item's own test module.
- [ ] **AC10: the decision table's keep rows name only live ids.** In `docs/aide/golden-decision-table.md`, the Section 1 rows whose `disposition` is `keep`, together with the body of `## Divergences from the roadmap's working assumption`, contain no key of `RENAMED_CASE_IDS` as a token (same regex as AC9).
- [ ] **AC11: nothing parses a mode out of a case id.** An AST scan of every `*.py` under `src/segfacet/`, `scripts/` and `tests/` reports no case-id expression (a `Name` `case_id`, an `Attribute` `.case_id`, or a `Subscript` keyed by the string `"case_id"`) in any of these positions: slice or integer-index subscript of it; receiver of `split`/`rsplit`/`partition`/`rpartition`; receiver of `startswith`/`removeprefix`/`find`/`index` called with a string literal starting with `mode`; first positional argument of `re.match`/`re.search`/`re.fullmatch`/`re.findall`/`re.split`/`re.sub` whose pattern literal contains `mode`.
- [ ] **AC12: the renamed fixtures stay pinned binary.** For each value `v` of `RENAMED_CASE_IDS`, `git check-attr binary -- tests/corpus/fixtures/<v>_seg.nii.gz` reports `binary: set`. The test skips cleanly when `git` is unavailable.
- [ ] **AC13: the generator documents the mapping.** For each `(old, new)` pair in `RENAMED_CASE_IDS`, `segfacet.synth.corpus.__doc__` has at least one line containing both `old` and `new` as tokens.
- [ ] **AC14: the mapping is captured as one knowledge insight.** Across `docs/aide/insights.md` and every `docs/aide/insights/archive-*.md`, exactly one entry line starts with `- [ ] knowledge —` or `- [x] knowledge —`, contains `item 157`, and contains every key and every value of `RENAMED_CASE_IDS`.
- [ ] **AC15: the geometric corpus regenerates identically.** `segfacet.synth.corpus.write_corpus(tmp)` produces a `manifest.json` equal to the committed `tests/corpus/manifest.json` under `segfacet.synth.golden.assert_matches_committed_artifact`. It also produces a `fixtures/<case_id>_seg.nii.gz` per case whose bytes equal the committed file's, and the same holds for `base_scan.nii.gz`.
- [ ] **AC16: the specification artifacts regenerate identically.** Regenerating `docs/aide/failure_modes.generated.json` and `docs/aide/failure_modes.generated.md` into a temporary directory through `segfacet.failure_modes`'s writer yields files equal to the committed copies under `assert_matches_committed_artifact`.
- [ ] **AC17: the traceability artifacts regenerate identically.** Regenerating `docs/aide/traceability_matrix.generated.json` and `docs/aide/traceability_matrix.generated.md` into a temporary directory through `segfacet.traceability`'s writer yields files equal to the committed copies under `assert_matches_committed_artifact`.
- [ ] **AC18: the golden evidence companion regenerates identically.** Regenerating `docs/aide/golden_evidence.generated.json` into a temporary directory through `segfacet.golden_evidence`'s writer yields a file equal to the committed copy under `assert_matches_committed_artifact`.
- [ ] **AC19: historical lookups still resolve through the mapping.** For every value `v` of `RENAMED_CASE_IDS`, the inverse mapping gives old id `o`, and `docs/aide/golden-decision-table.md` Section 1 has exactly one row whose `fixture` is `tests/corpus/golden/<o>.json` and whose `disposition` is `retire`.
- [ ] **AC20: the full suite is green.** `.venv/bin/python -m pytest -n auto` from a clean checkout of the item branch exits 0.

## Assumptions

- **A1 (clarify = assume): the mapping lives in code as well as prose.** The
  queue puts the old→new mapping "in the manifest's own documentation". The
  manifest is generated JSON with a fixed top-level shape (`cases`,
  `generator`, `manifest_version`). Adding a key would change its schema and
  every consumer. So the mapping's home is the manifest's generator: a
  module-level literal `RENAMED_CASE_IDS: Dict[str, str]` (old → new) in
  `src/segfacet/synth/corpus.py`, rendered pair by pair in its module
  docstring. The literal is needed in code anyway, because five test modules
  must reach old names without writing them. `manifest_version` stays `1`: the
  schema does not change, only values.
- **A2: keep `RENAMED_CASE_IDS` a frozen historical record.** It is never
  extended by later renames without a new decision, and nothing in `src/`
  reads it at runtime. It exists for documentation and for tests that resolve
  historical artifacts.
- **A3: the decision table's keep rows are a live inventory, not signed
  judgement.** `docs/aide/golden-decision-table.md` is described as
  human-signed. What is guarded as judgement is the retired rows' `what it
  asserts today`/`disposition`/`replacement guarantee` cells (`test_134` AC10,
  `test_126` AC18). Item 134 set the precedent of editing non-judgement cells
  under authorisation. The keep rows' fixture path and case-id prose must track
  the files on disk (`test_105` AC3). Renaming them changes no disposition.
  *Surfaced for audit at the queue boundary. No gate is raised, because the
  maintainer's rename decision implies it.*
- **A4: `docs/corpus-s-axis-correction.md` stays verbatim.** It is item 143's
  dated record of a one-time comparison, and its rows say "sha256 changed" for
  files that then had the old names. `test_143`'s AC16 is reconciled by mapping
  the live paths back through `RENAMED_CASE_IDS` rather than by rewriting the
  record. Item 159 later reworks that test's equality against a live set, and
  it starts from this reconciled form.
- **A5: `tests/corpus/094_pre_migration_snapshot.json` is a live fixture.** Its
  keys (`corpus/fixtures/<id>_seg.nii.gz|seg`) and `path` values are loaded by
  `test_094`'s AC3 against files on disk. Item 143 already re-captured it once
  as a living fixture. Its eight keys and paths are renamed. `data_sha256`,
  `shape`, `affine`, `spacing` and `dtype` do not change, because the arrays
  are byte-identical. It is written with `json.dumps(..., indent=2,
  sort_keys=True) + "\n"` through `write_bytes`. That serialisation matches
  the committed bytes (verify by re-dumping before renaming), and its
  `.gitattributes` `text eol=lf` pin already exists.
- **A6: `docs/reference-build.md` is a living how-to.** Its one mention (line
  262) is renamed. `docs/aide/failure-mode-taxonomy-handover.md` is a dated
  handover and is left verbatim.
- **A7: test function names are left as they are.** Names such as
  `test_ac8_mode6_crop_at_border_sensitivity_is_restored_to_one` embed an old id
  inside a longer identifier. They are not pins: nothing resolves them against
  the corpus. Some are called or quoted across modules (`test_132:552` calls
  `test_125`'s `test_ac7_mode4_relabel_swap_is_monotonic_pinned_true`,
  `test_132:582` calls `test_123`'s, and `test_126:487` quotes `test_042:378`'s
  name as a string), so renaming them would widen the diff for no gain. AC9's
  token regex excludes a match preceded by `_`, so they do not trip it. A
  builder who renames one must rename every caller or quoter in the same
  commit.
- **A8: new ids collide with perturbation names by design.** Every new id is
  the same string as its `perturbation`. `remove_level` is also a prefix of the
  existing `remove_level_relabel`. Every lookup must be an equality on
  `case_id`, never a substring or `startswith`. The tests are listed under
  Testing Strategy.
- **A9: item-number provenance.** Items 152–156 are merged (✅ in `progress.md`,
  2026-09-17). Item 155's `kind` field and `corpus_case_kind`, and item 156's
  conformance checks, are the merged state this item builds on, and none of
  them keys on a case-id prefix.
- **A10 (engine 1.52.1): `aide check` is not given a new warning class.** No new
  fixture path is introduced, so the `.gitattributes` lint is unaffected. The
  new test module reads only already-pinned fixtures. `progress.md` is changed
  only through the CLI verbs, because `test_146`/`test_150` go red on a new
  warning class.

## Implementation Steps

1. **Mapping and generator** (`src/segfacet/synth/corpus.py`). Add
   `RENAMED_CASE_IDS` (AC1/AC2) and export it in `__all__`. Rename the eight
   `CASE_RECIPE` `case_id` values. Rewrite the module docstring's "whose
   `modeN_` case ids are kept as stable identifiers" passage and the
   `CASE_RECIPE` comment at lines 184-186. Say that the prefixes were dropped by
   item 157 on 2026-09-17, and list each `old → new` pair on its own line
   (AC13).
2. **Rename the fixtures** with `git mv tests/corpus/fixtures/<old>_seg.nii.gz
   tests/corpus/fixtures/<new>_seg.nii.gz` ×8. Then regenerate with
   `.venv/bin/python -m segfacet.synth.corpus`. The regenerated `.nii.gz`
   files must leave `git status` showing only the eight renames, and
   `manifest.json` must differ only in `case_id` and `seg_fixture` values.
3. **Specification** (`src/segfacet/failure_modes.py`). Rename the eight
   `CorpusCaseExpectation.case_id` values, the case-id tokens in mechanism and
   reason strings (lines 791, 795, 1100, 1234, 1409, 1470, 1475, 1800, 1986 at
   `b30b91e`), and the docstring mentions (lines 60-96). In the docstring's
   item-150 history, the new id may be followed by "(formerly `modeN_…`)" only
   where the sentence is about the re-keying itself.
4. **Rule declaration evidence strings and docstrings**:
   `heuristics/{border,coverage,fragmentation,mislabel,overlap,sequence,rule}.py`,
   `synth/golden.py` (comment), `scripts/rebuild_verse_reference.py` (comment).
5. **Regenerate** `python -m segfacet.failure_modes`,
   `python -m segfacet.traceability` and `python -m segfacet.golden_evidence`
   through the venv. Check that each diff is only id-token substitutions.
6. **094 snapshot**: rename the eight keys and `path` values (A5).
7. **Tests with live pins**: replace the old literal with the new one in the 44
   modules (list under Authorised paths), matching only the eight exact
   tokens. Leave `mode4_sequence_break`/`mode5_sequence_break` in `test_099`
   alone. `tests/test_138_traceability_matrix.py:466`'s near-miss
   `mode8_force_overlaps` becomes `force_overlaps`, so it still checks a
   one-character-off id.
8. **Tests with historical references**: `test_116`, `test_126`, `test_105`,
   `test_134` and `test_143` reach the old name through `RENAMED_CASE_IDS` or
   its inverse, as described under "Live pins versus historical references".
   Do not write the old literal in them.
9. **Decision table keep rows** (A3): in `docs/aide/golden-decision-table.md`,
   rename the eight keep rows' fixture paths and case-id prose, plus the
   Divergences bullets. Retired rows and the execution log stay
   byte-unchanged.
10. **`docs/reference-build.md`** line 262 (A6).
11. **New test module** `tests/test_157_case_id_prefixes.py` covering AC1–AC19.
12. **Insight** (AC14): append one line with the Write/Edit tool (a heredoc
    trips the hygiene hook on `;`):
    `- [ ] knowledge — corpus case ids dropped their modeN_ prefixes: mode1_displace→displace, mode2_fragment→fragment, mode3_inject_islands→inject_islands, mode4_relabel_swap→relabel_swap, mode5_remove_level→remove_level, mode6_crop_at_border→crop_at_border, mode7_sequence_break→sequence_break, mode8_force_overlap→force_overlap; records dated before this keep the old names, and segfacet.synth.corpus.RENAMED_CASE_IDS holds the map *(item 157, 2026-09-17, engine 1.52.1)*`

## Authorised paths

**May change:**

- `src/segfacet/synth/corpus.py` — `RENAMED_CASE_IDS`, `CASE_RECIPE` ids, docstring mapping
- `src/segfacet/failure_modes.py` — corpus-case ids and id tokens in mechanism/reason strings
- `src/segfacet/heuristics/border.py` — declaration evidence string
- `src/segfacet/heuristics/coverage.py` — declaration evidence string
- `src/segfacet/heuristics/fragmentation.py` — declaration evidence string
- `src/segfacet/heuristics/mislabel.py` — declaration evidence string and docstring
- `src/segfacet/heuristics/overlap.py` — declaration evidence string
- `src/segfacet/heuristics/sequence.py` — declaration evidence string
- `src/segfacet/heuristics/rule.py` — docstring example
- `src/segfacet/synth/golden.py` — comment naming three cases
- `scripts/rebuild_verse_reference.py` — comment naming a case
- `tests/corpus/manifest.json` — regenerated with the new ids
- `tests/corpus/fixtures/*.nii.gz` — the eight `_seg.nii.gz` renames (content unchanged, no other fixture touched)
- `tests/corpus/094_pre_migration_snapshot.json` — eight keys and paths renamed (A5)
- `docs/aide/failure_modes.generated.json` — regenerated
- `docs/aide/failure_modes.generated.md` — regenerated
- `docs/aide/traceability_matrix.generated.json` — regenerated
- `docs/aide/traceability_matrix.generated.md` — regenerated
- `docs/aide/golden_evidence.generated.json` — regenerated, keyed by case id
- `docs/aide/golden-decision-table.md` — keep rows and Divergences bullets only (A3)
- `docs/reference-build.md` — one living mention (A6)
- `tests/test_157_case_id_prefixes.py` — this item's tests
- `tests/test_040_synthetic_corpus.py` — live pins and prose on prefixes
- `tests/test_041_regression_suite.py` — live pins
- `tests/test_042_golden_determinism.py` — live pins
- `tests/test_049_acceptance_stage6.py` — live pins
- `tests/test_053_eval_harness.py` — live pins
- `tests/test_057_acceptance_stage7.py` — prose mentions
- `tests/test_057_evaluate_cli.py` — fixture paths
- `tests/test_090_reference_derived_defaults.py` — live pins
- `tests/test_098_stray_components.py` — `_PRE_098_*` table keys
- `tests/test_099_per_mode_metrics.py` — live pins (exact tokens only)
- `tests/test_100_severity_ladder.py` — prose mention
- `tests/test_101_compare_runs_cli.py` — live pins
- `tests/test_101_per_mode_cohort.py` — live pins
- `tests/test_102_stage18_validation.py` — live pins
- `tests/test_103_feature_catalogue.py` — prose mentions
- `tests/test_105_golden_decision_table.py` — split live and historical use of `_GOLDEN_CASE_IDS`
- `tests/test_110_neighbourhood_wiring.py` — prose mention
- `tests/test_112_overlap_short_circuit.py` — live pins
- `tests/test_116_ras_native_corpus.py` — live pins, historical `git show` through the mapping
- `tests/test_119_curve_formulation.py` — prose mentions
- `tests/test_120_leave_one_out_offset.py` — live pins
- `tests/test_121_tangent_orientation.py` — live pins
- `tests/test_122_signed_curvature.py` — prose mentions
- `tests/test_123_recalibrate_and_regenerate.py` — live pins
- `tests/test_125_stage28_validation.py` — live pins
- `tests/test_126_golden_retirement.py` — split live and historical use of `_CASE_IDS`, retired-path digests through the mapping
- `tests/test_128_reference_verse_v1_integrity.py` — one mention
- `tests/test_128_relocation_checks.py` — one mention
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — `_PRE_129_*` keys
- `tests/test_131_tangent_direction_normalisation.py` — per-case table keys
- `tests/test_132_monotonicity_against_traversal_order.py` — per-case table keys and lookups
- `tests/test_134_decision_table_evidence_companion.py` — retired-row suffix match through the mapping
- `tests/test_135_stage29_validation.py` — live pins
- `tests/test_136_rule_mode_declarations.py` — prose mentions
- `tests/test_138_traceability_matrix.py` — live pins and the near-miss id
- `tests/test_143_s_axis_correction.py` — per-case table keys, AC16 maps live paths back to old names
- `tests/test_144_failure_mode_specification.py` — live pins
- `tests/test_145_eight_hypothesised_modes.py` — live pins
- `tests/test_146_ninth_mode_and_first_proposed.py` — live pins
- `tests/test_147_specification_is_the_record.py` — prose mentions
- `tests/test_148_per_path_mode_attribution.py` — live pins
- `tests/test_149_conformance_report.py` — live pins
- `tests/test_151_stage30_validation.py` — live pins
- `tests/test_aide_status_report.py` — synthetic manifest ids

**Asserts against:**

- `.gitattributes` — AC12 reads the `binary` attribute of the renamed fixtures
- `tests/corpus/intensity/manifest.json` — AC5/AC8 read its case ids
- `docs/corpus-s-axis-correction.md` — kept verbatim, read by `test_143` AC16 through the mapping (A4)
- `docs/aide/insights/*.md` — AC14 searches the archives

## Testing Strategy

New module `tests/test_157_case_id_prefixes.py`, one test per AC1–AC19. AC20 is
the validator's full-suite run.

- **AC9/AC10 scans.** Build the regex from `RENAMED_CASE_IDS`, never from a
  hand-typed list or a `mode[1-8]_…` pattern. Enumerate tracked files with
  `git ls-files` when git is available, else walk the tree skipping
  `__pycache__`. Adversarial checks: a synthetic string
  `"tests/corpus/golden/mode1_displace.json"` must match, and
  `"test_ac1_mode4_relabel_swap_is_non_monotonic"` and `"mode4_sequence_break"`
  must not. This proves the token boundaries are what AC9 says.
- **AC11 AST scan.** Positive controls: parse synthetic snippets
  `case_id[4]`, `case["case_id"].split("_")`, `c.case_id.startswith("mode")`
  and `re.match(r"mode(\d+)_", case_id)`, and assert each is reported. Negative
  control: `case.case_id.startswith("sub-verse")` (the one real occurrence,
  `test_088:166`) and `c["case_id"] == "displace"` are not reported.
- **AC15–AC18.** Compare through
  `segfacet.synth.golden.assert_matches_committed_artifact` so that
  `tests/committed_artifact_guard.py` classifies the new module clean. The
  `.nii.gz` byte comparison follows `test_040`'s existing guard-grounded
  `test_ac16_regeneration_is_byte_identical_across_runs_and_vs_committed`
  shape. If the guard reports the new comparison, add nothing to its
  allowlist: call the existing test's helper instead, or hand back.
- **AC14.** Search the inbox **and** every `docs/aide/insights/archive-*.md`
  (CLAUDE.md Gotchas: an archive sweep must not red the suite).
- **AC19.** Parse Section 1 with the same pipe-table parser shape
  `test_105`/`test_126` use (import it from `tests.test_105_golden_decision_table`
  if importable, else a local copy).
- **Edge cases (A8).**
  - For each new id, exactly one manifest case has `case_id == id`.
  - `remove_level` resolves to `fixtures/remove_level_seg.nii.gz` and never to
    `remove_level_relabel_seg.nii.gz`.
  - An inverse lookup of `RENAMED_CASE_IDS` is total over its values, with no
    two old ids mapping to one new id.
- **Existing tests to reconcile** (they pin the old behaviour, from the measured
  set above):
  - The 44 modules listed under Authorised paths.
  - These historical constructs specifically: `test_116:343-353`,
    `test_126:67-74,166-200,764-776`, `test_105:363-373,422`, `test_134:88-98`,
    `test_143:722-730`.
  - The live-inventory equality checks satisfied by A3's keep-row edit:
    `test_105` AC3 (`test_ac3_section1_fixture_set_equals_filesystem_walk_both_directions`),
    `test_105` AC13 (`test_ac13_divergences_section_names_exactly_the_keep_rows`)
    and `test_126` AC20.
  - `test_094` AC3 through the snapshot rename (A5).
  - `test_138:466`'s near-miss id.

## Validation

Run on the item branch after the builder's last commit. Each item is a diff-time
check, so it lives here and not in the suite:

1. `git diff -M --name-status aide/queue-021...HEAD -- tests/corpus/fixtures` —
   expect exactly eight `R100` lines, `<old>_seg.nii.gz → <new>_seg.nii.gz`, and
   no other fixture line.
2. `git diff aide/queue-021...HEAD -- tests/corpus/manifest.json` — every
   changed line is a `"case_id"` or `"seg_fixture"` value, and each old/new pair
   is in `RENAMED_CASE_IDS`.
3. `git diff --word-diff=porcelain aide/queue-021...HEAD --
   docs/aide/failure_modes.generated.json docs/aide/traceability_matrix.generated.json
   docs/aide/golden_evidence.generated.json` — every removed/added word pair is
   an old/new id substitution, so no mode field, firing set or count moved.
4. `git diff aide/queue-021...HEAD -- docs/aide/golden-decision-table.md` —
   changed lines are only the eight keep rows and the Divergences bullets.
5. `python .aide/scripts/aide.py scope` — clean against the list above.
6. `python .aide/scripts/aide.py check` — no warning class that is absent on
   `aide/queue-021`.

No environment-gated capability is involved, so no `[validation]` profile
applies.

## Dependencies

- Item 155 — the manifest `kind` field and `corpus_case_kind`. The renamed
  manifest must keep them unchanged.
- Item 156 — the conformance checks over corpus-case references that AC8
  relies on staying green.

**Downstream:** item 159 reworks `test_143`'s AC16 equality against a live
artifact set and starts from the mapped form this item leaves. Item 158 edits
`tests/test_138_traceability_matrix.py` and `tests/test_144_failure_mode_specification.py`,
which this item also edits for id literals. The overlap is textual only, and
whichever lands second rebases.

## Decisions & Trade-offs

To be updated during implementation.
