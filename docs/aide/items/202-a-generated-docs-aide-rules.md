<!-- aide-template: item 3 -->
# Item 202 — A generated `docs/aide/rules.generated.md`

> **Created:** 2026-09-29 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (D4)
> **Queue:** [`../queue/queue-027.md`](../queue/queue-027.md) · Item 202
> **Objectives:** G4, G8
> **Suggested branch:** `aide/202-a-generated-docs-aide-rules`

---

## Description

No document says what each rule *decides*. `docs/aide/failure_modes.generated.md`
and the conformance report say which mode a rule serves. The decision itself
(what is compared, against which default) is written only in the module
docstrings under `src/segfacet/heuristics/` and in
`src/segfacet/default_config.yaml` (`insights.md`, queue-022 review,
2026-09-22). Roadmap Stage 33 D4 asks for a generated table with one row per
detector: the question it asks, the path it reads, when it fires, its default,
and the modes it serves. Item 203's maintainer sign-off of modes 3 and 4 reads
that table.

**The change.**

- `RuleDetector` (`src/segfacet/heuristics/rule.py`) gains three additive
  fields, all defaulted so every existing construction still builds:
  `question` and `fires_when` (authored one-line prose) and `params` (the
  config keys the detector's decision reads, each with the code default
  `evaluate` passes). Every registered detector across the 12 rule modules
  fills all three.
- A new generator module `src/segfacet/rule_table.py` sits beside
  `failure_modes.py`. It renders the table from the rule registry, the bundled
  config and `failure_modes.modes_for_detector`, and writes it through
  `main(argv)`.
- `docs/aide/rules.generated.md` is committed, pinned `text eol=lf`, and
  stale-checked byte for byte against a fresh render.

**Not in scope.** There is no JSON twin, since nothing parses one. The table
has no severity column, and it does not render `bounds`' per-group hand-set
fallback bounds or any rule's condition opt-ins (all three are Left open). No
rule's behaviour, threshold or mode declaration changes, and no other
generated artifact moves.

## Acceptance Criteria

Terms used below:

- **"The committed file"** is `docs/aide/rules.generated.md` as read from disk.
- **"A row"** is a line of the file's single Markdown table below its header
  and separator lines. Its cells are the line's segments between unescaped
  `|` characters (split on `(?<!\\)\|`, then outer segments dropped and each
  cell stripped). The seven columns, in order, are **Rule**, **Detector**,
  **Question**, **Reads**, **Fires when**, **Default** and **Modes**. The Rule
  and Detector cells are the backticked ids, `` `rule_id` `` and
  `` `detector_id` ``.
- **"The registered detectors"** is the set of `(rule.rule_id,
  detector.detector_id)` pairs over `segfacet.heuristics.rule.iter_rules()`
  (after `import segfacet.heuristics`) and each rule's
  `mode_declaration.detectors`.
- **"The bundled config"** is `segfacet.config.bundled_default_config()`.
- **"Severity keys"** are config keys whose name ends in `severity`
  (`severity`, `end_severity`).

- [ ] **AC1: One row per registered detector.** The multiset of
  `(Rule cell, Detector cell)` pairs over the committed file's rows, with
  backticks stripped, equals the registered detectors, each exactly once.
- [ ] **AC2: The committed file is a fresh render.**
  `docs/aide/rules.generated.md`'s bytes equal
  `segfacet.rule_table.render_markdown().encode("utf-8")`.
- [ ] **AC3: `main` writes the render.** After
  `segfacet.rule_table.main(["--md", str(p)])` with `p` under `tmp_path`,
  `p.read_bytes()` equals `render_markdown().encode("utf-8")`.
- [ ] **AC4: A changed config default makes the committed file stale.** The
  test picks a `(rule_id, key)` that some registered detector declares in
  `params` and that the bundled config's `rule_params(rule_id)` carries with a
  non-bool `int` or `float` value, read live. It builds a config equal to the
  bundled one except that this value is incremented by 1. Under that config,
  `render_markdown(config).encode("utf-8")` is not equal to the committed
  file's bytes.
- [ ] **AC5: The Default cell is the effective default.** For every row, the
  Default cell equals `"; ".join(f"`{key}` = {json.dumps(bundled.rule_param(rule_id, key, default=code_default))}" for key, code_default in detector.params)`,
  or `(none)` when `detector.params` is empty.
- [ ] **AC6: A rule's declared keys are the keys it reads.** For every
  registered rule, the union of `key` over its detectors' `params` equals the
  set of string-literal key arguments (the second positional argument) of
  every `rule_param(...)` call in the rule's module source, parsed with
  `ast`, minus the severity keys.
- [ ] **AC7: The Modes cell is the modes the detector serves.** For every row,
  the Modes cell equals
  `", ".join(str(m) for m in failure_modes.modes_for_detector(rule_id, detector_id))`,
  or `none` when that tuple is empty.
- [ ] **AC8: The Reads cell is the detector's declared paths.** For every row,
  the Reads cell equals `", ".join(f"`{p}`" for p in paths)`. Here `paths` is
  the detector's `signal_paths` when non-empty. Otherwise it is the `path` of
  every `ConsumedPath` with `role == "condition-signal"` in the rule's
  `mode_declaration.consumed_paths`, in declaration order. The cell is
  `(none declared)` when both are empty.
- [ ] **AC9: The Question cell is the detector's authored question.** Every
  row's Question cell is a non-empty string equal to
  `failure_modes._md_escape(detector.question)`.
- [ ] **AC10: The Fires-when cell is the detector's authored firing
  condition.** Every row's Fires-when cell is a non-empty string equal to
  `failure_modes._md_escape(detector.fires_when)`.
- [ ] **AC11: The committed file is pinned LF.**
  `git check-attr eol -- docs/aide/rules.generated.md` reports `eol: lf`.

No AC here closes a Stage 33 acceptance criterion.

## Assumptions

- **A1 (defensible default: the question and firing condition are authored
  on the detector).** The queue line says every fact is already
  machine-readable. That holds for the detector ids, paths, modes and config
  values. It does not hold for "the question it asks" or "when it fires":
  `RuleDetector.description` is the finding's message tag for 24 of the 25
  registered detectors (for example `"Fragmentation:"`), and `bounds`'
  description is a one-line design note. So both are authored as new
  `RuleDetector` fields, `question: str = ""` and `fires_when: str = ""`, in
  each rule module beside the `evaluate` they describe. A rule change then
  shows its prose in the same diff. A separate prose table keyed by id
  strings would drift out of sight.
- **A2 (defensible default: "its default" is the effective default of the
  keys the detector reads).** Config params are per rule, not per detector.
  Five rules (`intensity`, `intensity_reference_delta`, `neighbour_contact`,
  `reference_delta` and `spline_offset`) have no active section in
  `default_config.yaml`, so their defaults exist only as the `default=` their
  `evaluate` passes to `config.rule_param`. So each detector declares
  `params: Tuple[Tuple[str, object], ...] = ()`, as
  `(key, code_default)` pairs. `code_default` is the same module constant or
  literal `evaluate` passes, and the renderer shows
  `config.rule_param(rule_id, key, default=code_default)`. A key that gates
  several detectors (`source`, `reference_*`, `expected_*`, `border_aware`)
  is declared on each detector it gates. Severity keys are left out, since
  they set a finding's severity and not whether it fires. A value must be
  hashable and JSON-serialisable: a scalar, `None` or a tuple.
  `RuleDetector` is a frozen dataclass, and coverage's `expected_levels`
  default `[]` is declared as `()`, which `json.dumps` renders as `[]`.
- **A3 (defensible default: "the path it reads").** Every mode-serving
  detector carries non-empty `signal_paths`, and the Reads cell renders them.
  The four mode-less rules' detectors carry none. For `border` and
  `spline_offset` the cell falls back to the rule's `condition-signal`
  paths. For `reference_delta` and `intensity_reference_delta` it falls back
  to `(none declared)`, because their consumed paths are all `bookkeeping` or
  `not-read`. That is what the declaration says, and the Question and
  Fires-when prose names what they compare.
- **A4 (defensible default: the module and its interface).** The module is
  `segfacet.rule_table`, the sibling of `failure_modes.py` and
  `traceability.py`, and it follows their shape. It defines
  `MD_PATH = _REPO_ROOT / "docs" / "aide" / "rules.generated.md"`,
  `render_markdown(config: Optional[HeuristicConfig] = None) -> str` (where
  `None` means the bundled config) and
  `main(argv: Optional[Iterable[str]] = None) -> int` taking `--md PATH`.
  `main` writes through `Path.write_bytes(text.encode("utf-8"))`. Rows are
  ordered by `iter_rules()` and then each rule's detector tuple, which are
  both already ascending. The output ends in exactly one `\n`.
- **A5 (defensible default: the byte comparison's guard ground).** AC2 is a
  byte-exact fresh-vs-committed comparison. `tests/committed_artifact_guard.py`
  reports one as a violation unless the committed path is on its
  `ALLOWLIST` (`tests/test_111_golden_guard.py::test_committed_artifact_guard_reports_zero_violations`).
  The file's only floats are config and code-default literals, rendered with
  `json.dumps` (shortest round-trip `repr`), and it holds no computed
  measurement. So it joins the `ALLOWLIST` under the existing
  `"exact-parameter-floats"` ground. `GROUNDS` gains no member.
- **A6 (measured 2026-09-29, this branch's base).** There are 12 registered
  rules and 25 registered detectors. The string-literal non-severity keys
  per module are as follows. `border`: `report_expected_ends`. `bounds`:
  `source`, `reference_lower_pct`, `reference_upper_pct`, `reference_stratum`
  (its group keys are read through a variable and are outside AC6).
  `coverage`: `border_aware`, `expected_count`, `expected_levels`.
  `fragmentation`: `fragmentation_index_threshold`, `island_min_voxels`,
  `source`, `reference_lower_pct`, `reference_upper_pct`, `reference_stratum`.
  `intensity`: `flag_low`, `flag_high`, `flag_degenerate`,
  `min_plausible_hu`, `max_plausible_hu`, `max_degenerate_std`.
  `reference_delta` and `intensity_reference_delta`: `flag_out_of_range`,
  `flag_robust_z`, `flag_distribution_distance`, `max_robust_z`,
  `max_distribution_distance`. `mislabel`: `flag_order_inconsistency`.
  `neighbour_contact`: `contact_fraction_threshold`. `overlap`:
  `min_overlap_voxels`. `spline_offset`: `max_offset_mm`. `sequence`: none.
  These are inputs for the builder, not pins: AC6 recomputes them live.

## Implementation Steps

1. **`src/segfacet/heuristics/rule.py`.** Add three trailing, defaulted fields
   to `RuleDetector`: `question: str = ""`, `fires_when: str = ""` and
   `params: Tuple[Tuple[str, Any], ...] = ()`. Extend its docstring to say
   the three are read-only documentation metadata, read by
   `segfacet.rule_table` and never by `evaluate`. In
   `RuleModeDeclaration.__post_init__`'s detector loop, reject a
   non-tuple `params` the same way `signal_paths` is rejected. This is the
   class's existing tuple-not-list policy, and it adds no new validation
   surface.
2. **The 12 rule modules** (`border`, `bounds`, `coverage`, `fragmentation`,
   `intensity`, `intensity_reference_delta`, `mislabel`, `neighbour_contact`,
   `overlap`, `reference_delta`, `sequence`, `spline_offset`). For each
   `RuleDetector(...)` in the module's `mode_declaration`:
   - `question`: one sentence, phrased as a question, on what this branch
     judges, for example "Does a stray component of this label press against
     a neighbouring label over a large share of its own surface?".
   - `fires_when`: the comparison exactly as `evaluate` makes it, naming the
     operand, the operator (strict `>` or `>=`, as coded) and the key it
     compares against, for example "`contact_fraction` >
     `contact_fraction_threshold`, per stray component (never index 0)".
     Take it from the branch's code, not from the docstring.
   - `params`: the `(key, code_default)` pairs for the non-severity keys this
     branch's decision reads. `code_default` is the **same name or literal**
     `evaluate` passes as `default=` (`DEFAULT_CONTACT_FRACTION`, `True`,
     `None` and so on). Where the literal is a list, declare the equal tuple.
   The union over a rule's detectors must cover every literal key the module
   reads (AC6). The prose must not contain the retired phrases the standing
   suite bans in `src/segfacet/` (see Testing Strategy).
3. **`src/segfacet/rule_table.py`** (new). Its module docstring names item
   202, the insight, and the scope fence above. It holds `MD_PATH` and
   `render_markdown(config=None)`:
   - Defer imports into the function body per house style:
     `segfacet.heuristics` (registers the rules), `iter_rules`,
     `bundled_default_config`, and `modes_for_detector` / `_md_escape` from
     `segfacet.failure_modes`. Reuse `_md_escape` and do not re-implement it.
   - Output: `# Rule Detectors`, a blank line, one note paragraph saying the
     file is generated by `python -m segfacet.rule_table` from each
     registered rule's `mode_declaration` and the bundled
     `default_config.yaml`, and must not be edited by hand. Then a blank
     line, the header row
     `| Rule | Detector | Question | Reads | Fires when | Default | Modes |`,
     the separator `|---|---|---|---|---|---|---|`, and one row per
     registered detector, with cells as AC5 and AC7–AC10 define them.
   - `main(argv)`: `argparse` with `--md` (default `MD_PATH`), then
     `mkdir(parents=True, exist_ok=True)` and `write_bytes`. It returns 0.
     Add an `if __name__ == "__main__": sys.exit(main())` block.
4. **Generate** `docs/aide/rules.generated.md` with
   `.venv/bin/python -m segfacet.rule_table` and commit it.
5. **`.gitattributes`.** Add `docs/aide/rules.generated.md text eol=lf` with a
   one-line comment naming item 202, beside the `failure_modes.generated.*`
   pins.
6. **`tests/committed_artifact_guard.py`.** Add one `AllowlistEntry` for
   `docs/aide/rules.generated.md`, ground `"exact-parameter-floats"`. Its
   reason says every float is a config or code-default literal rendered by
   `json.dumps`, with no computed measurement (A5).

No dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/rule_table.py` — the new generator (step 3)
- `src/segfacet/heuristics/rule.py` — three `RuleDetector` fields (step 1)
- `src/segfacet/heuristics/border.py` — detector prose and params (step 2)
- `src/segfacet/heuristics/bounds.py` — detector prose and params (step 2)
- `src/segfacet/heuristics/coverage.py` — detector prose and params (step 2)
- `src/segfacet/heuristics/fragmentation.py` — detector prose and params (step 2)
- `src/segfacet/heuristics/intensity.py` — detector prose and params (step 2)
- `src/segfacet/heuristics/intensity_reference_delta.py` — detector prose and params (step 2)
- `src/segfacet/heuristics/mislabel.py` — detector prose and params (step 2)
- `src/segfacet/heuristics/neighbour_contact.py` — detector prose and params (step 2)
- `src/segfacet/heuristics/overlap.py` — detector prose and params (step 2)
- `src/segfacet/heuristics/reference_delta.py` — detector prose and params (step 2)
- `src/segfacet/heuristics/sequence.py` — detector prose and params (step 2)
- `src/segfacet/heuristics/spline_offset.py` — detector prose and params (step 2)
- `docs/aide/rules.generated.md` — the committed table (step 4)
- `.gitattributes` — the LF pin (step 5, AC11)
- `tests/committed_artifact_guard.py` — the `ALLOWLIST` entry (step 6)
- `tests/test_202_rule_table.py` — this item's tests

**Asserts against:**

- `src/segfacet/default_config.yaml` — AC4 and AC5 read it live through
  `bundled_default_config()`
- `src/segfacet/failure_modes.py` — AC7 recomputes `modes_for_detector` from
  `SPECIFICATION`, and AC9 and AC10 call its `_md_escape`

## Testing Strategy

Test module: `tests/test_202_rule_table.py`. One test per AC. Parse the
committed file once per module (a module-level helper or a module-scoped
fixture), keyed by `(rule_id, detector_id)`. Every expected value is
recomputed from the registry, the bundled config and `SPECIFICATION`, never
typed as a literal (item 171's rule). AC4's perturbation is built from the
live value.

Adversarial cases (these and no others):

- **code-default-drift**: for every registered detector and each declared
  `(key, code_default)`, find the `rule_param(..., "<key>", default=<node>)`
  call(s) for that key in the rule's module. The `default=` node must equal
  `code_default`: a literal node compared with `ast.literal_eval`, a list
  compared as a tuple, and a `Name` node resolved as that attribute of the
  imported module. This guards a Default cell that shows a code default
  `evaluate` does not use. For a section-less rule (`neighbour_contact`,
  `spline_offset` and the rest) that value is the whole default, and AC5 and
  AC6 would both pass with it wrong.
- **perturbed-row-names-new-value**: under AC4's perturbed config, the
  Default cell of the row(s) declaring the perturbed key contains
  `f"`{key}` = {json.dumps(new_value)}"`. This guards a render that differs
  from the committed file for some other reason while still showing the old
  default. AC4 alone cannot tell the two apart.

**Existing tests that now read this item's output, and must stay green
unchanged (no reconciliation expected):**

- `tests/test_156_conformance_seams.py::test_ac11_no_complete_always_phrasing_in_source_or_generated_artifacts`
  globs `docs/aide/*.generated.*` and scans `src/segfacet/**/*.py`. The new
  file and the new prose must not contain `complete, always`,
  `complete-always`, `always complete` or `yes, always`.
- `tests/test_131_tangent_direction_normalisation.py::test_ac12_retired_phrase_absent_under_src_segfacet`
  scans `src/segfacet/`. The prose must not contain
  `cranial-to-caudal traversal`.
- `tests/test_111_golden_guard.py::test_committed_artifact_guard_reports_zero_violations`
  fails on AC2's comparison until step 6's `ALLOWLIST` entry lands.
- `ALLOWLIST` length pins: `tests/test_149_conformance_report.py:1211`
  asserts `len(narrowed) == len(guard.ALLOWLIST) - 4` after dropping four
  named paths. `tests/test_158_committed_artifact_guard_resolver.py:346`
  asserts `len(narrowed) < len(guard.ALLOWLIST)`. Both are relative and hold
  with one more entry. `test_127` and `test_135` pin
  `reference_default.json`'s absence, and `test_134` pins
  `golden_evidence.generated.json`'s absence. Neither path is touched.
- `RuleDetector` constructions: `tests/test_164_detector_ids.py` (three
  sites) and `tests/test_165_mode_4_at_the_bar.py` build it by keyword with
  `detector_id` and `description` only. The new fields are trailing and
  defaulted, so these still construct. No test compares a whole
  `RuleDetector` or `RuleModeDeclaration` by equality (grep:
  `detectors ==`, `== RuleDetector`, `mode_declaration ==` return only
  `test_164`'s id-set comparison and `test_136`'s `declaration_for`
  identity).
- No generated artifact other than the new one moves.
  `catalogue.py`, `traceability.py` and `failure_modes.py` read only
  `detector_id` and `signal_paths` (and `mode_less_reason` in
  `traceability`), so the new fields reach none of their serialisations.

## Validation

1. Run `.venv/bin/python -m segfacet.rule_table --md <scratch>/rules.md` and
   confirm the output is byte-identical to `docs/aide/rules.generated.md`.
2. Read the rows item 203's gate turns on, which are
   `neighbour_contact.stray_contact` (mode 3), `fragmentation.islands`
   (mode 4) and `bounds.metric_out_of_range` (modes 2, 3, 4). Check each
   Fires-when cell against its branch of `evaluate`: the operand, the
   operator (strict or not) and the key must match the code. Check each
   Default cell against `default_config.yaml` or the module constant.
   Record any mismatch as a FAIL. The suite cannot see prose that
   misdescribes the code.

## Dependencies

None. Items 200 and 201 (the other D4 deliverables) are independent of this
one and are already merged.

**Downstream:** item 203 (the at-the-bar sign-off of modes 3 and 4) reads
this table at its human gate. Item 204 (Stage 33 validation) regenerates it
from a clean clone and requires it byte-identical.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** `bounds`' per-group hand-set fallback bounds (`cervical`,
  `thoracic`, `lumbar`) are not rendered. They are read through a variable
  key, their defaults are dicts (so not hashable on a frozen `RuleDetector`),
  and under the default `source: reference` they are only the fallback. A
  change to them does not stale this table.
- **Left open:** there is no severity column, and each rule's
  `condition_opt_ins` is not rendered (item 191 said the table *may* render
  them). Nothing in this batch reads either, so no column is added.
- **Left open:** a newly registered detector with empty `question` or
  `fires_when` fails AC9 or AC10 in the suite. The renderer does not refuse
  it itself.
