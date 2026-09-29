<!-- aide-template: item 3 -->
# Item 196 — Stale prose after items 189, 190 and 195 brought up to date

> **Created:** 2026-09-29 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (maintenance)
> **Queue:** [`../queue/queue-026.md`](../queue/queue-026.md) · Item 196
> **Objectives:** G7
> **Suggested branch:** `aide/196-stale-prose-after-items-189`

---

## Description

Four passages of prose describe corpus cases or counts that later items
changed. No test reads any of them, so each drifted silently. This item
rewrites each one against the live corpus, with every number or example it
quotes re-measured, and adds one test for the only passage that states a
live count.

1. **`tests/test_120_leave_one_out_offset.py`,
   `test_ac24_corpus_pipeline_detection_is_nine_of_nine`'s docstring**
   (insight 2026-09-28-15eb). It is a chain of dated re-measurements, and its
   2026-09-15 sentence still files the records under "0 (crop)",
   "1 (displace, fragment)", "2 (fuse; until item 176)" and
   "15 (overlap, the miss)". Since item 189 `displace` is a
   `displaced_vertebra` condition case, since item 190 condition cases have
   their own buckets, and since item 195 there is no mode-15 case. The
   docstring's closing sentence about the test name keeping an old value is
   also stale, since the name now reads `nine_of_nine`. The docstring is
   rewritten to state the current state: the nine expected-failure records
   and the bucket each one scores under, which is what the test body asserts.
   The dated `# Item NNN` comments inside the body stay as the history.
2. **`tests/committed_artifact_guard.py`, the `ALLOWLIST` reason for
   `tests/corpus/094_pre_migration_snapshot.json`** (insight 2026-09-28-ebb9).
   It says "285 float leaves". The committed snapshot holds 323 (A1).
3. **`src/segfacet/heuristics/neighbour_contact.py`, the "Stray components
   only" design decision in the module docstring** (insight 2026-09-28-0b6c).
   It cites `force_overlap`'s labels 20/21 as a live example of a largest
   component touching a neighbour, and item 195 removed that case. The
   example list is rewritten from the live measurement (A2).
4. **`src/segfacet/synth/golden.py`, the "Cross-platform numeric comparison
   (item 078)" comment block** (insight 2026-09-28-922d). It lists
   "inject_islands, crop_at_border, force_overlap" as the asymmetric-geometry
   cases. `force_overlap` is gone. The list is also stale in the other
   direction: since item 173's lordotic base every corpus case has off-grid
   centroids (A3), so the rewrite does not enumerate a subset.

**Not in scope.** No behaviour change anywhere: no rule, operator, fixture,
manifest, ALLOWLIST path or ground changes. The other `force_overlap`
mentions in `src/` and `tests/` are dated removal annotations ("removed by
item 195"), which are accurate history, and they are left alone. The
`check_case_golden` docstring in `golden.py` says "the asymmetric-geometry
cases" without naming any, so it is not stale and is left alone.

## Acceptance Criteria

- [ ] **AC1: the snapshot's allowlist count equals its live float count.**
  The integer that opens the `ALLOWLIST` reason for
  `tests/corpus/094_pre_migration_snapshot.json` in
  `tests/committed_artifact_guard.py` equals the number of `float` leaves in
  that committed snapshot, counted recursively over dict values and list
  items after `json.loads`.

  *Why this is a criterion:* the count is the one passage of the four that
  states a live fact a test can recompute from the primary source, and it
  already drifted twice with no test reading it (items 174/175 added keys,
  item 195 removed one). The other three passages are prose whose truth no
  test can recompute (see Decisions & Trade-offs). The validator checks them
  through the Validation section.

## Assumptions

- **A1:** The committed snapshot `tests/corpus/094_pre_migration_snapshot.json`
  holds **323** float leaves over 17 top-level keys (measured 2026-09-29 with
  `json.loads` and a recursive count over dict values and list items). The
  insight's 342 was the count before item 195 removed one key. The builder
  re-measures at build time and writes the measured value, not this one.
- **A2:** On both committed corpora, with `DEFAULT_CONTACT_FRACTION == 0.1`,
  the labels whose largest component or whole label touches a neighbour are
  (measured 2026-09-29 with `compute_components` under
  `bundled_default_config()`):
  - `split` label 23: largest component 0.186, label scope 0.186 (the donor);
  - `split` label 24: largest component 0.0, label scope 0.102 (the stray
    piece makes the label-scope reading);
  - `split_own_label` label 22: 0.186 at both scopes;
  - `split_own_label` label 23: 0.332 at both scopes.

  No intensity-corpus label touches a neighbour. So the design decision
  still holds: reading the largest component or the label scope would fire
  on `split_own_label` (sub-type (b)), outside sub-type (a). But "well above
  the stray threshold" is not true of every such reading, because `split`'s
  label 24 reads 0.102 at label scope. The rewrite states the measured values
  and their date, and does not claim a margin the numbers do not show. The
  builder re-measures, and if the values moved, the rewrite follows them.
- **A3:** Every committed geometric corpus case has off-grid centroids: in
  every case, all labels but one have a voxel-index centroid that is not on
  the half-voxel grid (measured 2026-09-29, 13 cases). So after item 173 the
  numeric tolerance guards every case, not a named subset, and the rewritten
  comment says so with the measurement date instead of listing cases.
- **A4:** The queue line names the test as
  `test_ac24_corpus_pipeline_detection_is_nine_of_ten`. Item 195 renamed it
  `..._nine_of_nine`, and this item edits the docstring under its current
  name. The test's name and body are not changed.
- **A5:** The current buckets (read from `tests/corpus/manifest.json` and the
  test body's asserts on 2026-09-29) are: mode 1 `fragment`; mode 3 `split`,
  `split_own_label`; mode 4 `inject_islands`; mode 6 `remove_level`; mode 9
  `relabel_swap`, `sequence_break`; condition `fov_truncation`
  `crop_at_border`; condition `displaced_vertebra` `displace`. That is nine
  records, all detected. `fuse_adjacent`, `remove_level_relabel` and
  `crop_fov_si` expect "pass" and are not expected-failure records. The
  builder re-reads the manifest rather than copying this list.
- **A6:** Clarify mode is `assume`. The queue's *Testable* line asks for a
  check that none of the four passages names `force_overlap`, the retired
  buckets or the 285 count. That is a token-absence check. Deleting the
  sentence would satisfy it, so it cannot show that the rewritten prose is
  true, and §1 → items rules that shape out as a criterion. The token check
  is therefore a Validation step the validator runs, not a suite test.

## Implementation Steps

1. **Re-measure** A1–A3 and A5 before writing anything: the snapshot float
   count, the `component_contacts[0].contact_fraction` and
   `label_contact_fraction` of every label on both manifests (the loop in
   `tests/test_187_neighbour_contact_rule.py::test_threshold_margin_on_the_committed_corpora`
   is the reference shape: `load_manifest`, `load_intensity_manifest`,
   `loaded_seg_image`, `loaded_intensity_case`, `compute_components`), and
   the manifest's cases with their `failure_mode`/`condition`/expected
   verdict. Use scratch scripts only. Nothing is committed from this step.
2. **`tests/committed_artifact_guard.py`:** replace "285" in the snapshot
   entry's `reason` with the measured count. Keep the reason a single line,
   which `test_127`'s AC12 requires, and keep it opening with the integer so
   AC1's test can read it.
3. **`src/segfacet/heuristics/neighbour_contact.py`:** in the "Stray
   components only" bullet, replace the parenthetical example list with the
   live labels from step 1, their values, and "measured 2026-09-29" (or the
   build date). Drop `force_overlap`. Keep the conclusion: only the stray
   reading fires on `split` alone. Do not claim "well above" for a reading
   that step 1 shows is not (A2).
4. **`src/segfacet/synth/golden.py`:** in the item-078 comment block, replace
   "for the asymmetric-geometry cases (inject_islands, crop_at_border,
   force_overlap)" with a statement that every corpus case now produces
   off-grid floats (item 173's lordotic base tilts every vertebra), with the
   measurement date. Leave the rest of the block as it is.
5. **`tests/test_120_leave_one_out_offset.py`:** replace
   `test_ac24_corpus_pipeline_detection_is_nine_of_nine`'s docstring with a
   current-state statement: overall sensitivity is 9/9 over nine
   expected-failure records, then each record and its bucket from step 1,
   and which cases expect "pass" and are therefore not records. Point to the
   body's dated `# Item NNN` comments for how the numbers moved. Do not touch
   the body.
6. **`tests/test_196_stale_prose.py`:** not the builder's. The test-writer
   writes it (Testing Strategy).

No new dependency. No production behaviour changes, because steps 3 and 4
touch a docstring and a comment only.

## Authorised paths

**May change:**

- `tests/committed_artifact_guard.py` — the snapshot entry's reason count (step 2).
- `src/segfacet/heuristics/neighbour_contact.py` — module-docstring example list (step 3).
- `src/segfacet/synth/golden.py` — the item-078 comment block (step 4).
- `tests/test_120_leave_one_out_offset.py` — AC24's docstring (step 5).
- `tests/test_196_stale_prose.py` — AC1's test (new).

**Asserts against:**

- `tests/corpus/094_pre_migration_snapshot.json` — AC1 counts its float leaves live.

## Testing Strategy

Module: `tests/test_196_stale_prose.py`.

- **AC1:** import `ALLOWLIST` from `committed_artifact_guard` (the tests
  directory is on `sys.path`, as `test_187`'s `from synthetic import ...`
  shows). Select the one entry whose `path` is
  `tests/corpus/094_pre_migration_snapshot.json`, and assert exactly one
  matches. Read the leading integer of its `reason` with a regex, and assert
  the match is not `None` before comparing, so that a reworded reason fails
  rather than passing vacuously (§6: assert a derived value is recognisable).
  Load the snapshot from the repo root derived from `Path(__file__)` with
  `read_text(encoding="utf-8")` and `json.loads`, count `float` instances
  recursively (dict values, list items; `bool` is not a float), and assert
  the two integers are equal. The snapshot is already on `ALLOWLIST`, so the
  static guard does not flag this read.

No adversarial cases: nothing in this item branches.

**Existing tests to reconcile:** none. The sweep ran on 2026-09-29: grep of
`tests/` for "285", "float leaves, all affine", "labels 20/21" and
"asymmetric-geometry". No test pins any of the four passages.
`test_127_committed_artifact_tolerance.py`'s AC12 requires each reason to be
non-empty and single-line, and step 2 keeps both.

## Validation

The validator runs these on the branch, in addition to the suite:

1. `grep -n "force_overlap" src/segfacet/heuristics/neighbour_contact.py src/segfacet/synth/golden.py`
   finds nothing.
2. Read `test_ac24_corpus_pipeline_detection_is_nine_of_nine`'s docstring.
   It names no mode-0, mode-2 or mode-15 bucket, does not place `displace`
   under mode 1, and lists each of the nine records under the bucket the
   test body asserts, per the manifest.
3. Read the `neighbour_contact.py` "Stray components only" bullet against a
   fresh run of Implementation Step 1's contact measurement. Each label and
   value it quotes matches, and it claims no margin the values do not show.
4. Read the `golden.py` item-078 block. It names no case subset, and its
   claim that every corpus case has off-grid centroids matches a fresh
   measurement.

## Dependencies

None. Items 189, 190 and 195, whose changes made the prose stale, are all
merged (✅).

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** Whether the three prose passages should carry a live-state
  test, for example "every case the neighbour_contact comment names is a
  manifest case". This item does not add one. Such a check is a token check
  that a deleted sentence also satisfies, and the passages now quote dated
  measurements, which a later corpus change leaves as accurate history
  rather than a false present-tense claim.
