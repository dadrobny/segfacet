<!-- aide-template: item 2 -->
# Item 194 — Mode 1 attributed only as the catch-all, with the review's vocabulary

> **Created:** 2026-09-28 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-025.md`](../queue/queue-025.md) · Item 194
> **Objectives:** G2, G8
> **Suggested branch:** `aide/194-mode-1-attributed-only-as`

---

## Description

This item implements roadmap Stage 33 D3's seventh bullet: "Mode 1 is
attributed only when no other mode applies, and the rendering says so. The
vocabulary is applied as the review defined it: a mode describes the
vertebra, and 'fragmentation' is one label in several parts." Its source is
the `gap` entry in `docs/aide/insights.md` dated 2026-09-22 (queue-022
review, the presentation and naming decision), already routed to this item.

**Why.** Mode 1 (segmentation accuracy) is the parent of modes 2–7. A case
that is inaccurate but meets no sub-mode's rule is classified there. So a
case, or a detector's mode edge, belongs to mode 1 only when no other mode
applies. Today one edge breaks that, measured on this branch on 2026-09-28:

- `bounds`' single detector `metric_out_of_range` carries an `IntendedRule`
  edge on modes 1, 2, 3 and 4, so `failure_modes.modes_for_detector("bounds",
  "metric_out_of_range") == (1, 2, 3, 4)`. It is the only detector that
  serves mode 1 beside another mode. `fragmentation`'s `components` detector
  serves mode 1 alone, and its `islands` detector serves mode 4 alone.
- Through that edge a committed case carries mode 1 beside other modes. On
  `split_own_label` (mode 3), the live findings are the pair
  `("bounds", "metric_out_of_range")`, which serves modes `[1, 2, 3, 4]`.
  Every other case in both manifests maps to at most one mode.
- The traceability matrix renders `bounds | 1, 2, 3, 4` in its
  rules → modes table, which lists mode 1 beside the modes it is the
  catch-all for.

The vocabulary half: mode 3's definition still reads "a substantial part of
one ground-truth vertebra is covered by the label of a neighbouring
vertebra". That excludes sub-type (b), a part under a label of its own, which
item 174 added as `split_own_label`. The review's wording is the vertebra's:
mode 2 is one label over parts of several vertebrae, and mode 3 is one
vertebra under more than one label.

**What this item changes.**

- `bounds` declares modes `(2, 3, 4)` and mode 1 loses its `bounds` edge.
  Mode 1 keeps its `fragmentation` edge (detector `components`,
  `synthetic-demonstrable`) and its `fragment` case, so its derived status
  (`validated`) and rung (`synthetic-demonstrable`) do not move.
- Mode 1's definition states the catch-all rule for cases and for detector
  edges, and uses "fragmentation" for one label in several parts. Its
  discriminator's mode-3 clause covers both sub-types. Its mechanism no
  longer names `bounds`' proxy path.
- Mode 2's and mode 3's definitions lead with the vertebra wording.
- The three generated document pairs are regenerated. Stage 30 criterion 3's
  per-edge count clause is amended. The test pins listed under Testing
  Strategy are reconciled.

**Not in scope.**

- No change to `bounds`' `evaluate`, thresholds, detector ids or findings. No
  corpus change: no case's firing set moves.
- No new conformance check in `specification_conflicts()` or
  `catalogue.py` (Decisions, Left open).
- No rendering change in `traceability.py` or in `render_markdown()`'s code:
  the rendering changes through the authored text it prints.
- `fragmentation` keeps declaring `(1, 4)` at rule level. Detector
  granularity already separates the two edges, and the per-detector rule
  table is Stage 33 D4's `rules.generated.md` (Left open).
- Mode 8, the identity catch-all, is not touched: it has no edge and no case.
- No mode `name` or `short_name` changes, so no manifest moves.

## Acceptance Criteria

Terms used below:

- **"The detector groups"** maps each `(rule_id, detector_id)` pair to the set
  of mode ids whose `IntendedRule` edges name that `rule_id` and carry that
  `detector_id`. It is computed over every entry of
  `segfacet.failure_modes.SPECIFICATION`.
- **"A case's served modes"** is the union of
  `failure_modes.modes_for_detector(f.rule_id, f.detector_id)` over the case's
  live findings. The findings come from the harness its manifest entry's
  `detection` field names: `segfacet.synth.regression.pipeline_findings`
  (`"pipeline"`), `reconstructed_findings` (`"reconstructed_record"`) or
  `intensity_pipeline_findings` (`"intensity_pipeline"`).
- **"S"** is the sentence
  `The catch-all for accuracy defects: a corpus case, or a detector's edge, is attributed to this mode only when no other mode applies, and never beside another mode.`

- [ ] **AC1: no detector serves mode 1 beside another mode.** Every set in the
  detector groups that contains `1` equals `{1}`.
- [ ] **AC2: no committed case is served by mode 1 beside another mode.** For
  every case in `tests/corpus/manifest.json` and
  `tests/corpus/intensity/manifest.json`, if its served modes contain `1`
  they equal `{1}`.
- [ ] **AC3: no case is carried by mode 1 and by another entry.** The set of
  `case_id`s in `SPECIFICATION[1].corpus_cases` is disjoint from the union of
  the `case_id`s in every other `SPECIFICATION` entry's `corpus_cases` and
  every `failure_modes.CONDITIONS` entry's `corpus_cases`.
- [ ] **AC4: the rendering states mode 1's catch-all rule.** In
  `failure_modes.render_markdown()`, the text from the line starting
  `## Mode 1:` up to the next line starting `## ` contains S.
- [ ] **AC5: mode 2's definition uses the vertebra wording.**
  `SPECIFICATION[2].definition` starts with
  `One label covers substantial parts of two or more adjacent ground-truth vertebrae:`.
- [ ] **AC6: mode 3's definition uses the vertebra wording.**
  `SPECIFICATION[3].definition` starts with
  `One ground-truth vertebra is covered by more than one label:`.

Why each is written:

- AC1 is the edge half of "attributed only when no other mode applies". It
  fails on the pre-item tree: `("bounds", "metric_out_of_range")` groups to
  `{1, 2, 3, 4}`.
- AC2 is the queue line's first *Testable* sentence, "no case carries mode 1
  beside another mode", measured on the live findings. It fails on the
  pre-item tree for `split_own_label` (served modes `[1, 2, 3, 4]`).
- AC3 is the specification half of the same sentence. It holds on the
  pre-item tree, but nothing else guards it: measured on the prototype,
  listing `split`'s `CorpusCaseExpectation` under mode 1 as well as mode 3
  leaves `specification_conflicts()` at `()`, because `ModeSpec` refuses a
  duplicate `case_id` only within one entry.
- AC4 is the queue line's second *Testable* sentence. AC5 and AC6 are its
  third. Each is a claim about wording, so each is checked against the
  wording.

None of these closes a Stage 33 acceptance criterion. Criterion 3 waits on
D4's detector-granular bar checker.

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`, engine
2.1.0. Every measured value below was taken on this branch on 2026-09-28 with
`.venv/bin/python`, on a scratch copy of the tree (`git archive HEAD`) with
Implementation Steps 1 and 2 applied. The editable install's finder was
removed from `sys.meta_path`, so the copy's `src/` was the one imported (the
CLAUDE.md gotcha). The three generators and `segfacet.golden_evidence` were
run in that copy and diffed against the committed documents. The builder
re-measures each value on the real change.

- **A1 (defensible default: the edge goes, and so does the declaration).**
  The maintainer's rule is that an edge is attributed to mode 1 only when no
  other mode applies. `bounds`' volume/extent proxy is authored for modes 2, 3
  and 4, so its mode-1 edge goes. The declaration must follow: measured, with
  the edge removed and `bounds` still declaring `(1, 2, 3, 4)`,
  `catalogue.rule_declaration_conflicts()` reports
  `rule 'bounds': declares failure mode 1, but SPECIFICATION[1].intended_rules carries no IntendedRule edge for it (edges: ['fragmentation']).`
  With the edge re-added and the declaration at `(2, 3, 4)`,
  `specification_conflicts()` reports
  `mode 1: intended rule 'bounds' is registered but its RuleModeDeclaration does not declare mode 1 (declared modes: [2, 3, 4]).`
  So the existing mirror tests (`tests/test_156_conformance_seams.py`'s AC1
  and the conflicts-are-empty tests) hold the two together.
- **A2 (defensible default: "carries" is measured at detector granularity).**
  A finding carries its `detector_id` (`tests/test_191_condition_gate.py`'s
  AC3 reads it), and `modes_for_detector` is the specification's own
  derivation of which modes a detector serves. Rule granularity cannot be
  used: `fragmentation` declares `(1, 4)`, so `inject_islands` (mode 4) would
  "carry" mode 1 through a rule whose firing detector, `islands`, serves
  mode 4 alone.
- **A3 (defensible default: the rendering changes through authored text).**
  `render_markdown()` prints each mode's `definition` verbatim (through
  `_md_escape`, which changes nothing in S). S is authored as the last
  sentence of mode 1's definition, replacing "The catch-all for accuracy
  defects no more specific sub-mode claims: a case that is inaccurate but
  meets no sub-mode's rule is classified here." Adding a schema field or a
  rendered line would move `SCHEMA_VERSION` and the JSON key sets several
  tests pin, and no consumer reads a flag. Measured on the prototype: S
  appears in the mode-1 section of `render_markdown()`.
- **A4 (measured: what moves).**
  - Detector groups containing 1: `("fragmentation", "components") → {1}`
    only. `bounds`' group becomes `{2, 3, 4}`.
  - Served modes per case: `split_own_label` `[1, 2, 3, 4]` → `[2, 3, 4]`.
    Every other case is unchanged: `fragment` `[1]`, `inject_islands` `[4]`,
    `relabel_swap` `[9]`, `sequence_break` `[9]`, `remove_level` `[10]`,
    `split` `[3]`, `force_overlap` `[15]`, the three intensity failure cases
    `[16]`, and `[]` for `clean_control`, `clean_hu`, `displace`,
    `crop_at_border`, `crop_fov_si`, `fuse_adjacent` and
    `remove_level_relabel`.
  - Mode 1's matrix record: `rules` `["bounds", "fragmentation"]` →
    `["fragmentation"]`; `rule_attribution` `{"bounds": "analytic",
    "fragmentation": "corpus"}` → `{"fragmentation": "corpus"}`; `read_paths`
    loses the four `per_label.{label}.geometry.{extent_x_mm, extent_y_mm,
    extent_z_mm, physical_volume_mm3}` paths and keeps the five
    `per_label.{label}.components.*` paths. Modes 2, 3 and 4 do not move.
  - `bounds`' matrix row: `modes` `[1, 2, 3, 4]` → `[2, 3, 4]`.
  - Status and rung: no mode's derived status or rung moves. Derived status
    counts stay validated 6, implemented 3, specified 2, proposed 5. Derived
    mode rung counts stay synthetic-demonstrable 5, needs-real-data 3,
    structurally-unobservable 1, none 7.
  - Edges: 14 → 13. Per-edge rungs: synthetic-demonstrable 5,
    needs-real-data 8 → 7, structurally-unobservable 1.
  - Every matrix direction keeps its completeness and holes (`mode_to_rule`
    holes stay `12, 13, 14, 5, 6, 7, 8`). `bar_conditions(m)` for modes 1–4
    returns the same met vector and subjects as before (condition 4 excludes
    `PROXY_RULE_IDS`).
  - `specification_conflicts()`, `rule_declaration_conflicts()` and
    `path_classification_conflicts()` stay `()`. Conformance stays conformant.
  - Catalogue (145 entries, no path added or removed): the four geometry
    paths' `failure_modes` `(1, 2, 3, 4)` → `(2, 3, 4)`. Their `mode_evidence`
    stays `("rule_mode_map", "rule_declaration")`, because the corpus scan
    still maps `bounds` to `(3,)` through `split_own_label`. Entries carrying
    mode 1 go 9 → 5. Entries carrying modes 2, 3, 4 and 16 stay 4, 5, 9 and 2.
    The `mode_evidence` bucket table does not move.
  - Documents: `failure_modes.generated.{json,md}`,
    `traceability_matrix.generated.{json,md}` and
    `feature_catalogue.generated.{json,md}` move.
    `docs/aide/golden_evidence.generated.json` regenerates byte-identical. No
    manifest, fixture or `docs/aide/corpus_sheet.png` moves.
- **A5 (defensible default: mode 1's mechanism names no `bounds` path).**
  `tests/test_138_traceability_matrix.py::test_ac31_named_feature_path_is_consumed_by_one_of_the_modes_declared_rules`
  fails on any rule-consumed catalogue path in a mechanism that no declared
  or co-detecting rule of the mode consumes. Mode 1's permitted rules become
  `{"fragmentation"}`, so its mechanism may not contain
  `per_label.{label}.geometry.` or `reference_delta.`, nor the bare words
  `relationships` or `overlaps[]`. The word `bounds` is allowed, since it is
  not a catalogue path. The mechanism keeps the lowercase tokens `fragment`
  and `fragmentation` that `test_138`'s AC31 token check and `test_147`'s AC9
  need. The draft in Implementation Step 2 was checked on the prototype
  against both rules.
- **A6 (defensible default: mode 1's candidate features stay).**
  `per_label.{label}.geometry.physical_volume_mm3` and the
  `reference_delta` `robust_z` path stay `hypothesised` candidate features of
  mode 1. They are inputs someone might use against ground truth, not rule
  claims (item 193's A8 is the precedent).
- **A7: no human gate, and no environment-gated capability.**

## Implementation Steps

1. **`src/segfacet/heuristics/bounds.py`.**
   - `mode_declaration`: `modes=(1, 2, 3, 4)` → `modes=(2, 3, 4)`. Replace the
     second `evidence` element with the prototype's text:
     > per-label physical volume and x/y/z extent are compared against
     > level-aware plausible ranges: a fused pair reads over the maximum, a
     > split or island-depleted vertebra reads under the minimum -- the volume
     > proxy for modes 2 (fused), 3 (split) and 4 (islands) of the catalogue
     > signed off at item 150 (2026-09-14, revised 2026-09-15); every edge
     > needs-real-data. Not mode 1: mode 1 is the catch-all, attributed only
     > where no other mode applies, and this detector serves modes 2-4
     > (item 194).

     Keep the first element exactly `"analytic"`
     (`tests/test_137_mode_less_rule_disposition.py`'s AC4).
   - Rewrite the module docstring's "Targets failure modes 1 (segmentation
     accuracy), 2 (fused), 3 (split) and 4 (islands)" bullet to name modes 2,
     3 and 4, with a dated item-194 clause saying why mode 1 left. Keep the
     `S1`, `S6`, `Cocc` and `prefix` mentions that
     `tests/test_114_documentation_corrections.py` requires.
   - Add a dated item-194 sentence to the "Disposition" comment above
     `mode_declaration`. Its earlier history stays.
   - `evaluate`, `consumed_paths` and `detectors` do not change.
2. **`src/segfacet/failure_modes.py`.**
   - `_MODE_1.intended_rules`: remove the `bounds` `IntendedRule`. Keep the
     `fragmentation` edge.
   - `_MODE_1.definition`: replace the sentence "This includes a vertebra cut
     into large same-label pieces by a missing slab of its own body: the
     pieces carry no neighbour's label and are not small islands." with
     "This includes fragmentation -- one label in several parts -- where the
     parts are large pieces of the vertebra's own body cut apart by a missing
     slab: they carry no neighbour's label and are not small islands." Replace
     the last sentence with S (A3).
   - `_MODE_1.discriminator`: "mode 3 when a substantial part of the vertebra
     carries a neighbour's label" → "mode 3 when a substantial part of the
     vertebra carries another label". The discriminator must still contain the
     digit `2` (`tests/test_145_eight_hypothesised_modes.py`'s AC19 pairs).
   - `_MODE_1.mechanism`: delete the sentence "The label-map proxy is the
     bounds rule's per-label volume/extent range
     (per_label.{label}.geometry.physical_volume_mm3), declared at
     needs-real-data." Inside the closing parenthesis, after the item-193
     note, append: "Item 194, 2026-09-28: bounds' per-label volume/extent
     range is no longer this mode's proxy -- it serves modes 2, 3 and 4, and a
     detector that serves another mode is never also attributed to this
     catch-all." (A5.)
   - `_MODE_2.definition`: "One predicted segment covers a substantial part of
     two or more adjacent ground-truth vertebrae:" → "One label covers
     substantial parts of two or more adjacent ground-truth vertebrae:". The
     rest of the definition stays.
   - `_MODE_3.definition`: replace its first two sentences with "One
     ground-truth vertebra is covered by more than one label: a substantial
     part of it carries a neighbouring vertebra's label (sub-type a) or a
     label of its own (sub-type b), such that giving that part the vertebra's
     own label gives a better prediction. Typically a mostly correct vertebra
     that loses a part to another label." Then "Sub-type: transitional
     lumbosacral anatomy …" becomes "A further sub-type: transitional
     lumbosacral anatomy …".
   - No `expected_firing`, case `reason`, status or other mode changes.
   - Append a dated item-194 paragraph to the module docstring's history,
     after the item-193 one. Cite `failure_modes.SPECIFICATION`, never
     vision.md §6: `tests/test_161_stage31_validation.py`'s criterion-2 test
     rejects `§6 mode N`-shaped lines under `src/segfacet/`.
3. **Regenerate** each of the following twice with `--json <tmp> --md <tmp>`,
   byte-compare the two runs, then run it once more with no flags to write the
   committed copies:
   - `.venv/bin/python -m segfacet.failure_modes`;
   - `.venv/bin/python -m segfacet.traceability`;
   - `.venv/bin/python -m segfacet.catalogue`.

   The expected diffs are A4's. Do **not** regenerate the corpus or the
   corpus sheet. If a fresh `.venv/bin/python -m segfacet.golden_evidence`
   into a temp path differs from the committed copy, hand back.
4. **Amend Stage 30 criterion 3** with one call. Re-measure the numbers live
   first; the values below are A4's.
   `python .aide/scripts/aide.py progress amend 30 --criterion 3 --evidence "<text>"`,
   where the text is
   `Item 194 (2026-09-28): bounds no longer declares mode 1 and mode 1 loses its bounds edge, so mode 1 is attributed only as the catch-all. Re-measured live: derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7; per-edge rung counts over 13 edges: synthetic-demonstrable 5, needs-real-data 7, structurally-unobservable 1.`
   `tests/test_151_stage30_validation.py::test_ac35_rung_counts_note_matches_live_derivation`
   reads the last match in the `## Stage 30` section. The mode-rung clause and
   the per-edge clause must sit in one string joined by `; `. Stage 30
   criterion 1 and Stage 20 criterion 5 are **not** amended: their numbers do
   not move.
5. Leave `tests/` alone: the test-writer owns every edit listed under Testing
   Strategy.
6. Run `python .aide/scripts/aide.py scope 194` and
   `python .aide/scripts/aide.py check`. Both must report no error.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/bounds.py` — declaration, evidence, docstring and comment (step 1).
- `src/segfacet/failure_modes.py` — mode 1's edge, definition, discriminator and mechanism; modes 2 and 3 definitions; docstring (step 2).
- `docs/aide/failure_modes.generated.json` — regenerated (step 3).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 3).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 3).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `tests/test_194_mode_1_catch_all.py` — **new**: this item's test module.
- `tests/test_137_mode_less_rule_disposition.py` — `_ANALYTIC_DECLARED_MODES`, `mode1_count`, prose.
- `tests/test_138_traceability_matrix.py` — AC20 witness, the narrowing fixture and AC32, prose.
- `tests/test_145_eight_hypothesised_modes.py` — AC9 targets and name.
- `tests/test_149_conformance_report.py` — AC10 control, the narrowing fixture and its two adversarial tests.
- `tests/test_151_stage30_validation.py` — AC12 edge total, AC14 list, AC14 flip re-pointed.
- `tests/test_156_conformance_seams.py` — five perturbation tuples and their docstrings.

**The reconciliation fence.** Every edit to an existing test is one of these:

- a moved literal;
- a perturbation or fixture re-pointed to a subject that still carries the
  premise, with the premise asserted;
- a test renamed so its name states what it now checks, body otherwise as
  listed.

Each edit carries a dated item-194 comment. No test is retired, skipped,
`xfail`-marked or loosened. A red test in a file not listed here is a
hand-back to spec-author.

**Asserts against:**

- `tests/corpus/manifest.json` — AC2 reads every case; no case moves (A4).
- `tests/corpus/intensity/manifest.json` — AC2 reads every case; no case moves.
- `docs/aide/golden_evidence.generated.json` — no finding moves, so it must not move (A4).
- `tests/test_163_specificity_ratchet.py` — must stay green unedited (no firing moves).
- `tests/test_165_mode_4_at_the_bar.py` — stays green unedited; its mode-1 filter becomes a no-op (A4).

## Testing Strategy

The test module is `tests/test_194_mode_1_catch_all.py`, with one test per
AC. AC1 and AC3 are written over a helper that takes an iterable of
`ModeSpec` (and, for AC3, the conditions), so the adversarial cases can pass a
planted tuple. The AC tests pass `failure_modes.iter_modes()` and
`failure_modes.iter_conditions()`, never a literal mode list. AC1's test also
asserts that at least one group contains `1`, so it cannot pass on a
specification with no mode-1 edge at all. AC2 builds its findings once per
module (a module-scoped fixture), dispatching on each manifest case's
`detection` field, and asserts it checked every case of both manifests. AC4
reads `render_markdown()`, never the committed file (the fresh-vs-committed
comparison is already `test_150`'s).

Named adversarial cases, and no others:

- **planted-shared-mode-1-edge:** mode 1 re-planted with
  `IntendedRule(rule_id="bounds", detector_ids=("metric_out_of_range",), evidence_rung="needs-real-data")`
  makes AC1's helper report exactly `{("bounds", "metric_out_of_range")}`. It
  guards a predicate that only iterates mode 1's own edges, or reads an
  unpatched specification, and so can never see a sharing detector.
- **planted-double-carried-case:** mode 1 planted with `split`'s
  `CorpusCaseExpectation` (taken from `SPECIFICATION[3].corpus_cases`) makes
  AC3's helper report exactly `{"split"}`. It guards a disjointness check
  that compares mode 1 against itself, or against conditions only.
- **served-modes-see-a-shared-detector:** with `failure_modes.SPECIFICATION`
  monkeypatched so mode 1 carries the planted `bounds` edge above, the served
  modes of `split_own_label` equal `{1, 2, 3, 4}`. Measured on the pre-item
  tree. It guards AC2 computing served modes at rule granularity or from the
  manifest's `failure_mode`, either of which passes whatever the edges say.

**Existing tests to reconcile.** Three read-only sweeps over `tests/` and
`docs/aide/progress.md` found these. Every new literal was measured on the
prototype (A4, and the fixture measurements below). Each file goes red
without the edit named.

- **`tests/test_137_mode_less_rule_disposition.py`:**
  - `_ANALYTIC_DECLARED_MODES = {"bounds": (2, 3, 4)}`, reconciling
    `test_ac2_ac3_analytic_rule_declares_its_expected_modes`. Add a dated
    line to the history comment above it, and an "(2, 3, 4) since item 194"
    clause to the module docstring's AC2 line.
  - `test_adv_measured_artifact_movement_counts_from_spec`:
    `mode1_count == 5`. Add a dated item-194 paragraph to its docstring: the
    four `per_label.{label}.geometry.*` paths leave mode 1. `len(entries) == 145`,
    `mode2_count == 4`, `mode16_count == 2` and the whole bucket table stay.
- **`tests/test_138_traceability_matrix.py`:**
  - `test_ac20_analytic_edges_equal_edges_the_specification_never_designates_corpus`:
    drop `(1, "bounds")` from `witness`. `mixed == {"bounds", "sequence"}`
    stays true. Re-word the comments that say bounds is analytic for modes 1,
    2 and 4, or declares 1–4.
  - The fixture `matrix_reference_delta_renarrowed` (about line 567) narrows
    `bounds` to `modes=(2, 3)`. Keep its name and its one `build_matrix()`
    call (`_BUILD_MATRIX_CALL_SITE_BUDGET = 16`). Update its docstring.
  - `test_adv_ac32_renarrowed_reference_delta_declaration_fails_the_matrix_level_check`
    asserts on mode 4: `"bounds" in` the unpatched mode-4 `rules`, and
    `"bounds" not in` the patched one. Measured: mode 4's rules go from
    `["bounds", "fragmentation"]` to `["fragmentation"]`.
- **`tests/test_145_eight_hypothesised_modes.py`:**
  `test_ac9_the_three_analytic_only_edges_are_needs_real_data_and_undemonstrated`
  is renamed
  `test_ac9_the_analytic_only_bounds_edges_are_needs_real_data_and_undemonstrated`,
  with `targets = {(2, "bounds"), (4, "bounds")}`. Update its section header
  and docstring. Nothing else names the function (checked under `tests/`,
  `src/`, `.github/` and `docs/aide/`; the two item-193 spec mentions are
  history).
- **`tests/test_149_conformance_report.py`:**
  - `test_ac10_mode1_read_paths_are_signal_classified_only`: the positive
    control becomes
    `"per_label.{label}.components.fragmentation_index" in mode1["read_paths"]`,
    and add
    `"per_label.{label}.geometry.physical_volume_mm3" not in mode1["read_paths"]`.
    The two `reference_delta` `not in` lines stay.
  - The fixture `matrix_reference_delta_renarrowed` (about line 320) narrows
    `bounds` to `modes=(2, 3)`. Keep its name and its one `build_matrix()`
    call (`_BUILD_MATRIX_CALL_SITE_BUDGET = 11`). Update its docstring.
    Measured: the patched matrix differs from the unpatched one, so
    `test_ac31_every_adversarial_fixture_rederives_from_the_shared_unpatched_fixture`
    stays green.
  - `test_adv_ac10_renarrowed_reference_delta_shrinks_mode1_read_paths` is
    renamed `test_adv_ac10_renarrowed_bounds_shrinks_mode4_read_paths` and
    reads mode 4: `after < before`, and
    `"per_label.{label}.geometry.physical_volume_mm3" not in after`. Measured:
    mode 4 loses the four geometry paths and keeps its five components paths.
  - `test_adv_ac19_renarrowed_reference_delta_shrinks_mode1_attribution` is
    renamed `test_adv_ac19_renarrowed_bounds_shrinks_mode4_attribution` and
    reads mode 4: `"bounds" in before` and `"bounds" not in after`. Measured:
    mode 4's attribution goes from `{"bounds": "analytic", "fragmentation":
    "corpus"}` to `{"fragmentation": "corpus"}`.
- **`tests/test_151_stage30_validation.py`:**
  - `test_ac12_every_intended_rule_edge_carries_a_valid_rung`:
    `total_edges == 13`, with a "14 → 13: item 194" line in the comment
    trail.
  - `test_ac14_recorded_analytic_edge_list`: the list becomes
    `[(2, "bounds"), (4, "bounds")]`.
  - `test_adv_ac14_flipped_attribution_is_detected`: re-pointed from mode 1 to
    mode 4. Every hard-coded `1` in the body (`m.mode == 1`,
    `SimpleNamespace(mode=1, …)`, `independent[1]`) and the `pytest.fail`
    message change. Measured: mode 4 carries `bounds` as `analytic`.
  - `test_ac35_rung_counts_note_matches_live_derivation` goes green through
    Implementation Step 4, with no test edit.
- **`tests/test_156_conformance_seams.py`:** every `bounds` perturbation that
  still lists mode 1 now also reports mode 1 as unmirrored. Measured on the
  prototype against the empty baseline:
  - `test_ac2_unmirrored_declaration_on_specified_mode_is_reported`,
    `test_ac5_new_message_is_not_read_as_a_rule_to_mode_hole` and
    `test_adv_monkeypatch_undo_restores_the_baseline_exactly`:
    `modes=(1, 2, 3, 4, 6)` → `(2, 3, 4, 6)`. It gives exactly one new
    message, naming `bounds` and 6, and `rule_to_mode` holes stay `[]`. With
    `(1, 2, 3, 4, 6)` there are two.
  - `test_ac6_mode_outside_key_set_reported_exactly_once` and
    `test_adv_known_and_unknown_mode_only_the_unknown_one_is_reported`:
    `modes=(1, 2, 3, 4, 999)` → `(2, 3, 4, 999)`. It gives exactly one new
    message, the "outside … key set" one naming 999. With `(1, 2, 3, 4, 999)`
    there are two.
  - `test_ac3_queue_control_1_2_5_is_reported` keeps `(1, 2, 5)` (the queue's
    control); it reads with `any`, and measured it now gives three messages
    (modes 1 and 5 unmirrored, mode 3 corpus-designated). Its docstring gains
    one dated sentence saying so.
  - Update the module docstring and the premise comments that say `bounds`
    declares and mirrors modes 1–4.

**Green without an edit** once step 3 regenerates and step 4 amends:

- every fresh-vs-committed artifact test the sweeps listed (`test_136`'s
  AC13, `test_137`'s AC15, `test_138`'s AC2–AC5, `test_145`'s AC23,
  `test_147`'s AC23/AC24, `test_149`'s AC18–AC20, `test_150`'s AC11/AC12,
  `test_151`, `test_157`'s AC16/AC17);
- `test_169_stage32_validation.py`'s AC6–AC8 (Stage 20's numbers do not
  move);
- `test_156`'s AC1 and AC4, `test_164`, `test_165`, `test_191`, and every
  behaviour test that runs `bounds` on a record, since `evaluate` does not
  change;
- `test_138`'s and `test_147`'s mechanism checks (A5).

## Validation

1. Regenerate the three document pairs (step 3), then inspect them:
   - In `docs/aide/failure_modes.generated.md`, mode 1's definition ends with
     S, and its intended rules list `fragmentation` alone. Mode 2's
     definition starts "One label covers …" and mode 3's starts "One
     ground-truth vertebra is covered by more than one label".
   - In `docs/aide/traceability_matrix.generated.md`, the rules → modes row
     for `bounds` reads `2, 3, 4`, and mode 1's row lists
     `fragmentation (corpus)` alone.
2. Run
   `.venv/bin/python -c "import segfacet.heuristics; from segfacet.failure_modes import modes_for_detector as m; print(m('bounds', 'metric_out_of_range'), m('fragmentation', 'components'))"`
   and confirm it prints `(2, 3, 4) (1,)`.
3. Run `python .aide/scripts/aide.py status` and confirm Stage 30 shows
   step 4's amendment.

No environment profile is needed.

## Dependencies

- Item 193: made `reference_delta` mode-less, which left `bounds` as the only
  detector sharing mode 1, and last amended the Stage 30 clause step 4
  amends (✅).
- Item 187: moved `neighbour_contact` out of `fragmentation`, leaving the
  `components` detector on mode 1 alone (✅).

**Downstream:**

- Item 195 (`force_overlap` removed) regenerates the same document pairs and
  re-amends the same Stage 30 clause.
- Stage 33 D4's `rules.generated.md` renders modes per detector, and its
  detector-granular bar checker reads the edges this item leaves.

## Decisions & Trade-offs

Implemented as specified: `bounds` narrows to `modes=(2, 3, 4)` and mode 1's
`bounds` edge is removed together (A1); mode 1's definition, discriminator
and mechanism, and modes 2/3's definitions, were edited exactly as
Implementation Step 2 drafted, with S inserted verbatim as the last sentence
of mode 1's definition (A3). The three generated document pairs were
regenerated twice each (`--json`/`--md` to a scratch path) and byte-compared
before writing the committed copies; a fresh `golden_evidence.generated.json`
compared byte-identical to the committed one, so nothing was regenerated
there. All live-measured values matched A4 exactly: detector groups
containing mode 1 are `{("fragmentation", "components")}` only; mode rung
counts stay synthetic-demonstrable 5, needs-real-data 3,
structurally-unobservable 1, none 7; per-edge rung counts over 13 edges are
synthetic-demonstrable 5, needs-real-data 7, structurally-unobservable 1;
`specification_conflicts()`, `rule_declaration_conflicts()` and
`path_classification_conflicts()` are all `()`. Stage 30 criterion 3 was
amended via `aide progress amend` with those re-measured numbers.

- **Left open:** a production conformance check for the catch-all rule.
  AC1 and AC3 hold the invariant in the suite. A message in
  `specification_conflicts()` would also reach the regenerated documents, but
  no consumer reads one yet, and the check would have to name which mode is a
  catch-all.
- **Left open:** mode 8, the identity catch-all, under the same rule. It has
  no edge and no case today, so there is nothing to attribute. Whether the
  rule is generalised to every parent mode is for the item that gives mode 8
  an edge.
- **Left open:** the rule-granular rules → modes table still renders
  `fragmentation | 1, 4`. The two modes are served by two different
  detectors, which the table cannot show. Stage 33 D4's per-detector
  `rules.generated.md` is where that belongs.
