<!-- aide-template: item 2 -->
# Item 191 — A condition-flagged label is excluded from every rule that does not opt in

> **Created:** 2026-09-28 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-025.md`](../queue/queue-025.md) · Item 191
> **Objectives:** G2, G7, G8
> **Suggested branch:** `aide/191-a-condition-flagged-label-is`

---

## Description

This item implements roadmap Stage 33 D3's fourth bullet ("A label in a
condition ... is excluded from every rule unless that rule explicitly opts in to
the condition"). It closes the `docs/aide/insights.md` `gap` entry dated
2026-09-22 (queue-022 review) on `bounds`: `bounds`, and `reference_delta`'s
size features, fire on a label that touches the image border, because a
truncated vertebra is small by construction.

**What is inverted.** Today a condition is a record only.
`ConditionSpec.exempting_rules` lists the rules whose own code exempts the
condition's labels (`coverage`'s border-aware span, `spline_offset`'s terminal
skip), and every other rule applies to those labels unchanged. After this item
the gate belongs to the condition and runs in one place, the rule runner
(`segfacet.heuristics.run_rules`):

- a finding that names a label in a condition is dropped, unless the rule that
  produced it opts in to that condition;
- a rule opts in by declaring a `ConditionOptIn` on its class, naming the
  condition, the features that stay valid on such a label, and why;
- `ConditionSpec.exempting_rules` becomes `ConditionSpec.opting_in_rules`, the
  specification's record of which rules opt in, and it must agree with the
  registry.

**Which labels are in a condition** (A2):

- `fov_truncation`: every label whose `per_label.{label}.geometry` carries a
  true `touches_*` flag, on any of the six faces.
- `displaced_vertebra`: every label named by a `spline_offset` finding that
  survives the `fov_truncation` gate. The FOV gate runs first: a truncated
  label's centroid is displaced by the crop, so it cannot be judged displaced.

**Which rules opt in** (A3). Only each condition's recording rule: `border`
opts in to `fov_truncation`, and `spline_offset` opts in to
`displaced_vertebra`. `spline_offset` does not opt in to `fov_truncation`,
because the crop displaces the truncated label's centroid. No other rule opts in
to anything.

**What moves on the corpus** (A5, measured). Without a reference, two cases
change and nothing else:

- `crop_at_border` loses its `spline_offset` finding on label 22 and keeps
  `border` on 22;
- `crop_fov_si` loses both `bounds` findings on label 24, so it fires nothing
  and its verdict becomes `pass`.

With a reference attached, the findings on `displace`'s label 22,
`crop_at_border`'s label 22 and `crop_fov_si`'s label 24 are dropped, apart
from each recording rule's own.

**Not in scope.**

- No change to any rule's `evaluate`. The existing exemptions inside `coverage`
  (border-aware span) and `spline_offset` (terminal skip) stay as they are;
  they are rule logic, not the gate (A6).
- No finding-level record of what the gate dropped: the report does not list
  suppressed findings (Left open).
- No per-detector or per-feature opt-in: an opt-in admits all of a rule's
  findings on the condition's labels (Left open).
- Vertebra-local extents are Stage 27's. `sequence` sub-types are item 192's.
- The severity ladders do not move (A5).

## Acceptance Criteria

Terms used below:

- **"The manifest"** is `segfacet.synth.corpus.load_manifest()`, and **"the
  `X` case"** is its entry whose `case_id == "X"`.
- **`cfg`** is `segfacet.config.bundled_default_config()`.
- **"The production reference"** is
  `segfacet.reference.artifact.bundled_production_reference()`.
- **`rec(X)`** is `segfacet.pipeline.extract_feature_record(segfacet.synth.regression.loaded_seg_image(<the X case>), cfg)`.
- **`gate`** is `segfacet.heuristics.run_rules`.
- **"A planted rule on `L`"** is a `segfacet.heuristics.rule.Rule` subclass
  defined in the test, with `rule_id = "planted"`, whose `evaluate` returns
  exactly one `Finding(rule_id="planted", severity=Severity.FLAG,
  reason="planted", labels=frozenset(L))`.
- **"The FOV opt-in"** is
  `ConditionOptIn(condition="fov_truncation", paths=("per_label.{label}.geometry.physical_volume_mm3",), reason="planted")`.

- [ ] **AC1: the truncated remnant fires nothing.** The findings of
  `segfacet.synth.regression.pipeline_findings(<the crop_fov_si case>)` that
  name label 24 are `[]`.
- [ ] **AC2: the truncated remnant fires nothing against the reference.** The
  findings of `segfacet.pipeline.run_qc_with_reference(loaded_seg_image(<the crop_fov_si case>), cfg, <the production reference>)[0]`
  that name label 24 are `[]`.
- [ ] **AC3: the same volume on an interior label still fires.** With every
  `touches_*` flag of `rec(crop_fov_si)["per_label"]["24"]["geometry"]` set to
  `False` (on a deep copy),
  `{(f.rule_id, f.detector_id) for f in gate(<that record>, cfg) if 24 in f.labels} == {("bounds", "metric_out_of_range")}`.
- [ ] **AC4: a rule that does not opt in is gated.**
  `gate(rec(crop_fov_si), cfg, rules=[<a planted rule on {24}>]) == []`.
- [ ] **AC5: a rule that opts in still fires on a border-touching label.** The
  planted rule on `{24}`, with `condition_opt_ins = (<the FOV opt-in>,)`, gives
  `gate(rec(crop_fov_si), cfg, rules=[<it>])` equal to the one finding its
  `evaluate` returns.
- [ ] **AC6: `crop_at_border` is recorded by `border` alone.** For `c`, the
  `crop_at_border` entry of `CONDITIONS["fov_truncation"].corpus_cases`,
  `set(segfacet.failure_modes.measured_firing(c)) == {"border"}`.
- [ ] **AC7: `crop_fov_si` fires nothing.** For `c`, the `crop_fov_si` entry of
  `CONDITIONS["fov_truncation"].corpus_cases`,
  `set(segfacet.failure_modes.measured_firing(c)) == set()`.
- [ ] **AC8: a displaced label is gated too.** The rule ids of the findings of
  `run_qc_with_reference(loaded_seg_image(<the displace case>), cfg, <the production reference>)[0]`
  that name label 22 are exactly `{"spline_offset"}`.
- [ ] **AC9: `coverage`'s border-aware span holds under the gate.** On a deep
  copy of `rec(clean_control)` with
  `["per_label"]["24"]["geometry"]["touches_inferior"] = True`, and
  `cfg9 = dataclasses.replace(cfg, rules={**cfg.rules, "coverage": {"enabled": True, "params": {"expected_levels": ["L1", "L2", "L3", "L4", "L5", "L6"]}}})`,
  `[f for f in gate(<that record>, cfg9) if f.rule_id == "coverage"] == []`.
- [ ] **AC10: the specification records the registry's opt-ins.** For every id
  `c` in `segfacet.failure_modes.CONDITIONS`,
  `CONDITIONS[c].opting_in_rules == tuple(sorted(r.rule_id for r in segfacet.heuristics.iter_rules() if c in {o.condition for o in r.condition_opt_ins}))`.
- [ ] **AC11: the exemption list is gone.**
  `{f.name for f in dataclasses.fields(segfacet.failure_modes.ConditionSpec)} & {"exempting_rules", "opting_in_rules"} == {"opting_in_rules"}`.
- [ ] **AC12: an opt-in names features its rule reads.** For every registered
  rule `r`, every `o` in `r.condition_opt_ins` and every `p` in `o.paths`, `p` is
  the `path` of an entry of
  `segfacet.catalogue.build_catalogue(strict=True).entries` whose
  `consuming_rules` contains `r.rule_id`.

Why each is written:

- AC1 and AC2 are the queue's "`crop_fov_si`'s L5 remnant fires no size
  finding", once for each size rule: `bounds` fires without a reference, and
  `reference_delta` fires only with one (the insight's "the same suppression
  applies to `reference_delta`'s size features").
- AC3 is "the same volume on an interior label still fires". It fails if the
  gate keys on size, or on anything other than the touch flags.
- AC4 is "excluded from every rule": it fails if the gate special-cases `bounds`
  and `reference_delta` instead of defaulting every rule out. AC5 is "a rule
  that opts in to `fov_truncation` still fires on a border-touching label", on a
  rule other than the recorder.
- AC6 and AC7 are "the expected sets of `crop_fov_si` and `crop_at_border` are
  re-authored". That the authored sets equal the measured ones is the
  specificity ratchet's (`tests/test_163_specificity_ratchet.py`), so it is not
  restated. AC6 also proves the displaced-vertebra membership excludes a
  truncated label: if `crop_at_border`'s label 22 counted as displaced, `border`'s
  finding on it would be dropped too.
- AC8 is "the mechanism covers item 189's displaced-vertebra condition too".
  No corpus case shows it without a reference: on `displace` only the recorder
  fires.
- AC9 is "`coverage`'s border-aware span holds under the new default". It fails
  if the gate is built by masking the condition's labels out of the record
  instead of filtering findings: the masked inferior end would read as not
  truncated, and `coverage` would report L6.
- AC10 and AC11 are the inversion itself. AC10 keeps the specification's
  record and the runtime from disagreeing. AC11 fails if the old list is kept
  beside the new one.
- AC12 is "a rule that opts in says which of its features stay valid": the
  statement must name features the rule reads.
- `spline_offset`'s terminal skip is not restated. The gate can only remove
  findings, the skip lives inside `spline_offset.evaluate`, which this item
  does not change, and `tests/test_033_mislabel.py` and
  `tests/test_120_leave_one_out_offset.py` keep pinning it.

None of these closes a Stage 33 acceptance criterion. Criterion 2 ("every
case's measured firing equals its expected set, across both corpora") is
attested by D6's stage validation over the whole corpus.

**Correction (2026-09-28, after validation round 1): AC13 is added.** AC1–AC12
stand as written. A3's correction of the same date gives the reason.

- [ ] **AC13: a mislabel on a label that reads as displaced still fires.** Let
  `swap` be `loaded_seg_image(<the clean_control case>)` with its voxel values
  20 and 21 exchanged, on the same affine and header, and
  `r = extract_feature_record(swap, cfg)`. Then
  `{(f.rule_id, f.detector_id, f.labels) for f in gate(r, cfg) if f.rule_id in {"mislabel", "spline_offset"}} == {("mislabel", "ordering", frozenset({20, 21})), ("spline_offset", "spline_offset", frozenset({21}))}`.

Why it is written: it fails if `mislabel` does not opt in to
`displaced_vertebra`. The gate then drops the ordering finding, and a genuine
label swap is reported only as an anatomy condition. The `spline_offset` member
of the set is the precondition: if label 21 stopped reading as displaced, the
equality fails instead of passing without exercising the gate.

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
measured value below was taken on 2026-09-28 with `.venv/bin/python` on this
branch. A scratch probe replaced `segfacet.heuristics.run_rules` in-process with
a prototype of Implementation Step 2 and ran the pipeline, the severity harness
and `traceability.build_matrix()` through it. Each probe fixture used by an AC
or a named case was run the same way. The builder re-measures each value on the
real change.

- **A1 (defensible default: the gate filters findings in the runner).**
  - The queue says "excluded from every rule", so the default has to live in
    one place that every rule passes through. That is `run_rules`, which
    `run_qc`, `run_qc_with_reference`, `run_qc_with_intensity`,
    `failure_modes.measured_firing` and the CLI all reach.
  - Findings are filtered after the rules run; the record is not masked. A
    masked label would look absent to `coverage` and `sequence`, which read the
    present-label set (AC9).
  - A finding is dropped when **any** of its labels is in a condition the rule
    does not opt in to. A pair finding (`mislabel`, `sequence`, `overlap`) that
    involves a truncated label rests on that label's features too.
  - A case-level finding (empty `labels`, e.g. `coverage`'s) is never dropped.
  - A direct `SomeRule().evaluate(...)` call is not gated. So the reconstructed
    corpus path (`synth.regression.reconstructed_findings`) is not gated; its
    two cases have no border-touching label.
  - The opt-in is read from a new `Rule` class attribute, `condition_opt_ins`,
    and never from `mode_declaration`.
    `tests/test_136_rule_mode_declarations.py`'s AC14 requires that replacing
    every rule's `mode_declaration` leaves `run_rules` unchanged.
- **A2 (defensible default: condition membership).**
  - `fov_truncation`: the six `touches_*` flags, read the way `border` reads
    them (`bool(geometry.get(face))`), with the label taken from the entry's
    `label` field and falling back to the `per_label` key. A missing or
    malformed `per_label` gives no member.
  - `displaced_vertebra`: the labels of the findings, surviving the FOV gate, of
    the rules in `CONDITIONS["displaced_vertebra"].recording_rules`, i.e.
    `spline_offset`. Its threshold and terminal skip therefore decide
    membership, and nothing re-implements them. If `spline_offset` is disabled
    in the config, no label is displaced.
  - The FOV gate runs first (A3's reason). Measured on `crop_at_border`: label
    22 is in `fov_truncation`, `spline_offset`'s finding on it is dropped, so 22
    is not displaced, and `border`'s finding survives.
- **A3 (defensible default: only the recording rules opt in).**
  - `border` → `fov_truncation`, with paths the six
    `per_label.{label}.geometry.touches_*` paths.
  - `spline_offset` → `displaced_vertebra`, with paths
    `stage3.per_label_offsets[].offset_mm`, `.dx_mm`, `.dy_mm` and `.dz_mm`.
  - `spline_offset` does not opt in to `fov_truncation`. The condition's own
    definition says the missing region displaces the measured centroid, so the
    offset is spoiled on a truncated label.
  - `coverage` does not opt in: its findings are case-level, so the gate never
    reaches them.
  - No other rule opts in. `bounds` and `reference_delta` do not opt in to
    `displaced_vertebra` either, although a rigid displacement leaves volume
    unchanged: the roadmap decides validity per rule when the rule needs it,
    and no case needs it yet (Left open).
  - **Corrected 2026-09-28, after validation round 1: `mislabel` also opts in
    to `displaced_vertebra`.** The default above stands as the record of what
    round 1 was built from. It is wrong for `mislabel`, for two reasons.
    - A genuine mislabel can read as displaced. Measured on this branch with
      `.venv/bin/python`: exchange two labels of the `clean_control` fixture
      and run the real gate. For 20↔21, `spline_offset` fires on 21, and the
      gate drops `mislabel`'s only finding (`ordering` on {20, 21}). The
      report then names an anatomy condition and hides the segmentation
      defect. Of the ten pairwise swaps of labels 20–24, three lose a
      `mislabel` finding this way (20↔21, 20↔22, 22↔24). No other rule's
      finding is dropped on any of them.
    - The ordering signal is not spoiled by a displacement.
      `stage3.monotonic_consistency.non_monotonic_pairs[]` is judged against
      a reference curve fitted in S-sorted traversal order (item 132,
      `compute_monotonic_consistency`). A vertebra moved off the curve keeps
      its place in that order unless it moves past a neighbour, and a label
      order that disagrees with the vertebrae's positions is exactly what the
      rule reports.
  - `mislabel`'s opt-in names one path,
    `stage3.monotonic_consistency.non_monotonic_pairs[]`. The live catalogue
    lists it among `mislabel`'s consumed paths (with `per_label`), so AC12
    holds. `CONDITIONS["displaced_vertebra"].opting_in_rules` becomes
    `("mislabel", "spline_offset")`, sorted as AC10 derives it.
  - `mislabel` still does not opt in to `fov_truncation`: the crop spoils a
    truncated label's centroid, and the ordering is read from centroids.
  - Measured with the opt-in applied in-process: the plain pipeline over every
    geometric-corpus case is unchanged, and so are the reference-backed
    findings of `clean_control`, `displace`, `crop_at_border`, `crop_fov_si`
    and `relabel_swap`. AC8 still reads `{"spline_offset"}`: `mislabel` does
    not fire on `displace`. A5 therefore stands. The three
    `tests/test_033_mislabel.py` tests that went red in round 1 read both
    findings again, on {19, 20} and {20}.
- **A4 (defensible default: the specification record).**
  - `ConditionSpec.exempting_rules` is renamed `opting_in_rules`, validated as a
    tuple like the field it replaces. `fov_truncation` carries `("border",)` and
    `displaced_vertebra` carries `("spline_offset",)`.
  - `specification_to_dict` writes the key `opting_in_rules`, and
    `render_markdown` writes `- Opting-in rules: <ids>` where it wrote
    `- Exempting rules: <ids>`.
  - `ConditionSpec` stays import-light (`failure_modes.py` imports no rule
    module), so AC10 is the check that the literal agrees with the registry.
- **A5 (measured: what moves).**
  - Plain pipeline, both corpora: only two cases change.
    - `crop_at_border`: `border/unexpected_clip` on 22 (kept),
      `spline_offset/spline_offset` on 22 (dropped). Verdict stays
      `flagged-for-review`.
    - `crop_fov_si`: the two `bounds/metric_out_of_range` findings on 24 are
      dropped (volume 6758 mm³ below 8000; `extent_z` 14 mm below 15). Nothing
      fires; the verdict becomes `pass`.
    - Every other case of the geometric and intensity corpora is unchanged. No
      label in any of them touches a face.
  - With a reference, finding counts before → after:

    | Case | `reference_verse_v1` | `reference_default` |
    |---|---|---|
    | `clean_control` | 55 → 55 | 10 → 10 |
    | `displace` | 59 → 46 | 20 → 15 |
    | `crop_at_border` | 61 → 47 | 25 → 15 |
    | `crop_fov_si` | 54 → 43 | 24 → 14 |

    Every one of these verdicts stays `flagged-for-review`.
  - `segfacet.eval.severity_ladder.run_severity_harness()` is byte-identical
    under the prototype (serialised and diffed).
  - `traceability.build_matrix()` moves in two places only, once the expected
    sets are re-authored:
    - the conformance rows of `crop_at_border` (`["border"]`) and `crop_fov_si`
      (`[]`). Conformance stays 18 agreeing, 0 disagreeing;
    - the exercise report: `bounds` is exercised by `split_own_label` only, and
      `spline_offset` by `displace` only. All 12 rules stay exercised or
      unexercised as before.
  - The manifest's `crop_fov_si` entry changes three fields:
    `expected_rule_ids []`, `expected_labels []`, `expected_verdict "pass"`.
    Its `detail` is unchanged. Every fixture's bytes are unchanged, and so is
    every other entry, including `crop_at_border`'s (it designates `border`
    only).
  - The fov_truncation expected-failure bucket of the eval harness shrinks from
    two cases to one, because `crop_fov_si` is no longer expected to fail.
  - `docs/aide/feature_catalogue.generated.json` and
    `docs/aide/golden_evidence.generated.json` do not move.
    `docs/aide/corpus_sheet.png` moves with the manifest digest.
- **A6 (defensible default: the existing exemptions stay where they are).**
  `coverage`'s border-aware span check and `spline_offset`'s terminal skip are
  rule logic that predates the gate. Neither is removed: the terminal skip
  covers a terminal vertebra that does not touch a face, and the span check
  decides which absent level to report, which no finding filter can do.
- **A7: no human gate, and no environment-gated capability.**

## Implementation Steps

1. **`src/segfacet/heuristics/rule.py`.**
   - Add a frozen dataclass `ConditionOptIn(condition: str, paths: Tuple[str, ...], reason: str)`.
     `__post_init__` rejects an empty `condition`, a `paths` that is not a
     tuple (a bare `str` names the field and says a tuple is required, as
     `RuleModeDeclaration` does), an empty `paths` or an empty element, and an
     empty `reason`. Add it to `__all__`.
   - Add the class attribute `condition_opt_ins: Tuple[ConditionOptIn, ...] = ()`
     to `Rule`, with a docstring: read by the runner, never inside `evaluate`,
     and separate from `mode_declaration` (A1).
2. **`src/segfacet/heuristics/fov.py`.** Add
   `border_touching_labels(record) -> FrozenSet[int]` per A2. It reads the same
   six `touches_*` keys `border.py` reads. The helper sits here, the shared FOV
   module `border` and `coverage` already import, so the runner imports no
   rule module.
3. **`src/segfacet/heuristics/runner.py`.** In `run_rules`:
   - collect `(rule, finding)` pairs in the existing order;
   - drop each pair whose finding names a label in
     `border_touching_labels(record)`, unless `"fov_truncation"` is among the
     rule's opt-in conditions (read with `getattr(rule, "condition_opt_ins", ())`,
     so a duck-typed test rule defaults to none);
   - from the survivors, take the labels of findings whose `rule_id` is in
     `segfacet.failure_modes.CONDITIONS["displaced_vertebra"].recording_rules`,
     and drop each pair naming one of them unless the rule opts in to
     `"displaced_vertebra"`;
   - return the surviving findings in their original order. The record is
     never mutated.
   - Update the module docstring's design decisions with the gate (A1, A2).
4. **`src/segfacet/heuristics/border.py`.** Set `condition_opt_ins` per A3, with
   a `reason` saying the touch flags are the condition's own evidence. Add one
   design-decision line to the docstring.
5. **`src/segfacet/heuristics/spline_offset.py`.** Set `condition_opt_ins` per
   A3, with a `reason`. Rewrite the scope fence's "no condition gating of other
   rules" sentence: the gate now exists, in the runner, and this rule opts in
   to `displaced_vertebra` only.
6. **`src/segfacet/failure_modes.py`.**
   - `ConditionSpec`: rename `exempting_rules` to `opting_in_rules` (field,
     validation tuple, class docstring: "the rule(s) that opt in to it").
   - `_CONDITION_FOV_TRUNCATION`:
     - `opting_in_rules=("border",)`;
     - `crop_at_border`'s `expected_firing=("border",)`, with a re-measured,
       dated `reason`. It must still contain `centroid`, and `curve` or
       `spline`: it says `spline_offset` reads the crop-displaced centroid off
       the fitted spinal curve, and that its finding is gated because it does
       not opt in to the condition;
     - `crop_fov_si`'s `expected_firing=()`, with a dated `reason`: `border`
       suppresses the expected FOV-end touch, and the gate drops `bounds`'
       volume and `extent_z` findings on the remnant;
     - rewrite `mechanism`: `border` records the in-plane form on
       `crop_at_border`; the gate drops every other rule's finding on a
       touching label; nothing fires on `crop_fov_si`; `spline_offset`'s own
       terminal skip (`stage3.per_label_offsets[].is_terminal`) stays as rule
       logic. Drop the "bounds fires on the truncated remnant" and
       "spline_offset co-fires" sentences.
   - `_CONDITION_DISPLACED_VERTEBRA`: `opting_in_rules=("spline_offset",)`.
     Rewrite the `mechanism`'s "also co-fires on crop_at_border" sentence: the
     crop does displace that label's centroid, but the FOV gate drops the
     finding, so the label is not counted displaced (A2).
   - `specification_to_dict` and `render_markdown` per A4.
   - Module docstring: append a dated item-191 paragraph. The item-189
     paragraph stays as the record.
7. **`src/segfacet/synth/coverage_border_overlap.py`.** `CropFovPerturbation`'s
   `Expectation`: `expected_rule_ids=frozenset()`, `expected_labels=frozenset()`,
   `expected_verdict="pass"`. The `detail` string is unchanged. The class
   docstring gains one line on why nothing fires.
8. **Regenerate.** Run each of the following twice into temp paths, byte-compare
   the two runs, then write the committed copy:
   - `.venv/bin/python -m segfacet.synth.corpus --out <tmp>`. Copy only
     `manifest.json`. Every fixture must byte-match the committed one (A5); if
     one does not, hand back;
   - `segfacet.synth.corpus_sheet`;
   - `segfacet.failure_modes` and `segfacet.traceability`;
   - `segfacet.catalogue` and `segfacet.golden_evidence`, which must come out
     unchanged.
9. **Reconcile** the tests under Testing Strategy, each change with a dated
   item-191 comment.
10. Run `python .aide/scripts/aide.py scope 191` and
    `python .aide/scripts/aide.py check`. Both must report no error.

No dependency is added.

**Correction (2026-09-28, after validation round 1): one step is added.** Steps
1–10 stand; the builder has already carried them out.

11. **`mislabel` opts in to `displaced_vertebra`** (A3's correction).
    - `src/segfacet/heuristics/mislabel.py`: set `condition_opt_ins` to one
      `ConditionOptIn(condition="displaced_vertebra", paths=("stage3.monotonic_consistency.non_monotonic_pairs[]",), reason=...)`.
      The `reason` says that a mislabelled vertebra can read as displaced, and
      that the ordering is judged against the S-sorted reference curve, which
      a displacement does not spoil. Add one design-decision line to the
      module docstring, dated, naming item 191.
    - `src/segfacet/failure_modes.py`: `_CONDITION_DISPLACED_VERTEBRA`'s
      `opting_in_rules=("mislabel", "spline_offset")`. Add one sentence to its
      `mechanism`: `mislabel` opts in, because a label swap can put a centroid
      off the curve fitted in label order.
    - Regenerate `failure_modes.generated.{json,md}` and
      `traceability_matrix.generated.{json,md}` as step 8 does, with two runs
      byte-compared. `feature_catalogue.generated.json` and
      `golden_evidence.generated.json` must come out unchanged, because the
      catalogue does not read opt-ins. `tests/corpus/manifest.json` and
      `docs/aide/corpus_sheet.png` do not move.
    - Re-run `python .aide/scripts/aide.py scope 191` and
      `python .aide/scripts/aide.py check`.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/rule.py` — `ConditionOptIn` and `Rule.condition_opt_ins` (step 1).
- `src/segfacet/heuristics/fov.py` — `border_touching_labels` (step 2).
- `src/segfacet/heuristics/runner.py` — the gate (step 3).
- `src/segfacet/heuristics/border.py` — its opt-in (step 4).
- `src/segfacet/heuristics/spline_offset.py` — its opt-in and scope-fence prose (step 5).
- `src/segfacet/failure_modes.py` — `opting_in_rules`, both conditions (step 6).
- `src/segfacet/synth/coverage_border_overlap.py` — `crop_fov`'s expectation (step 7).
- `tests/corpus/manifest.json` — `crop_fov_si`'s entry (step 8).
- `docs/aide/corpus_sheet.png` — the manifest digest moved (step 8).
- `docs/aide/failure_modes.generated.json` — regenerated.
- `docs/aide/failure_modes.generated.md` — regenerated.
- `docs/aide/traceability_matrix.generated.json` — regenerated.
- `docs/aide/traceability_matrix.generated.md` — regenerated.
- `tests/test_191_condition_gate.py` — **new**: this item's test module.

- `tests/test_175_crop_fov_si.py` — AC9's firing triple becomes empty.
- `tests/test_189_spline_offset_condition.py` — AC11's firing set and AC12's exemption list.
- `tests/test_145_eight_hypothesised_modes.py` — `exempting_rules` renamed; `crop_at_border`'s expectation and co-firing claims.
- `tests/test_149_conformance_report.py` — `crop_at_border`'s conformance row.
- `tests/test_151_stage30_validation.py` — `crop_at_border`'s expected set.
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — `crop_at_border`'s finding pairs.
- `tests/test_125_stage28_validation.py` — AC16's `spline_offset` co-firing.
- `tests/test_123_recalibrate_and_regenerate.py` — AC15's and AC28's `crop_at_border` offset finding.
- `tests/test_120_leave_one_out_offset.py` — AC23's offset finding and AC24's corpus sensitivity.
- `tests/test_116_ras_native_corpus.py` — `_ITEM_120_NEW_MISLABEL_CASES`.
- `tests/test_098_stray_components.py` — `crop_at_border`'s entry in `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`.
- `tests/test_057_acceptance_stage7.py` — the corpus sensitivity.
- `tests/test_049_acceptance_stage6.py` — AC11's `reference_delta` finding on `crop_at_border`'s label 22.

**The reconciliation fence.** Every edit to an existing test is one of:

- a moved literal: a firing set, a finding count, a sensitivity, or an
  expected field of the crop_fov_si case;
- the exemption list renamed to opting_in_rules, with the new value;
- a co-firing claim (spline_offset on crop_at_border, bounds or
  reference_delta on a truncated label) inverted to the gated measurement.

Each carries a dated item-191 comment. No test is retired, skipped,
`xfail`-marked or loosened. A red test in a file not listed here is a
hand-back to spec-author.

**Asserts against:**

- `tests/corpus/fixtures/crop_fov_si_seg.nii.gz` — AC1–AC4, AC5 and AC7 read it; its bytes must not move.
- `tests/corpus/fixtures/crop_at_border_seg.nii.gz` — AC6 reads it unchanged.
- `tests/corpus/fixtures/displace_seg.nii.gz` — AC8 reads it unchanged.
- `tests/corpus/fixtures/clean_control_seg.nii.gz` — AC9 builds its record from it.
- `src/segfacet/reference/reference_verse_v1.json` — AC2 and AC8 read it.
- `docs/aide/feature_catalogue.generated.json` — must not move (A5); AC12 reads the live catalogue.
- `docs/aide/golden_evidence.generated.json` — must not move (A5).
- `tests/test_163_specificity_ratchet.py` — must stay green; red unless step 6 re-authors both expected sets.
- `tests/test_136_rule_mode_declarations.py` — its AC14 must stay green unedited (A1).
- `tests/test_102_stage18_validation.py` — parametrised over `test_098`'s `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`; green once that constant is reconciled, unedited.
- `tests/test_190_condition_keyed_eval_bucket.py` — derives every bucket count from the manifest; green unedited once `crop_fov_si` expects `pass`.
- `tests/test_041_regression_suite.py` — `verify_case` over the regenerated manifest; green unedited.

This section was amended on 2026-09-28, after the test-writer's commit
`d3d68d7` and before any production code, when a read-only sweep found three
pins outside the reconciliation list above. The lists above stand as written;
this note adds two paths and nothing else. Two of the pins run
`run_qc_with_reference` on `crop_at_border` and require a `bounds` finding on
label 22, which touches the anterior face, so the gate drops it. The third is
`tests/test_189_spline_offset_condition.py`'s AC14 (the file is already
listed): it would pass for the wrong reason. The exact edits are under the
Testing Strategy's correction of the same date. The reconciliation fence gains
two shapes, and only for these edits. The first is a reference-liveness pin
re-pointed from the crop_at_border case to the clean_control case, which has no
label on a face. The second is test_189 AC14's "fires", computed from the
ungated rule's evaluate instead of from pipeline_findings.

**May change:**

- `tests/test_128_reference_verse_v1_integrity.py` — the load-and-score companion's case becomes `clean_control` (amended 2026-09-28).
- `tests/test_128_relocation_checks.py` — `test_ac8_companion_actually_runs_and_finds_label_22_bounds_finding`'s case becomes `clean_control` (amended 2026-09-28).

A second amendment, dated 2026-09-28 and made after validation round 1, adds
one path to each list. The lists above stand. `mislabel` opts in to
`displaced_vertebra` (A3's correction, step 11). `tests/test_033_mislabel.py`
is not edited: its three round-1 failures pass again once the opt-in exists.

**May change:**

- `src/segfacet/heuristics/mislabel.py` — its `displaced_vertebra` opt-in (step 11, amended 2026-09-28).

**Asserts against:**

- `tests/test_033_mislabel.py` — AC15's two tests and `test_adv_offset_findings_ordered_before_order_findings` go green unedited (amended 2026-09-28).

## Testing Strategy

The test module is `tests/test_191_condition_gate.py`, with one test per AC.
AC1, AC6 and AC7 read firing through `pipeline_findings` and
`failure_modes.measured_firing`; AC2 and AC8 through `run_qc_with_reference`.
None re-implements the gate. AC12 asserts that at least one registered rule
carries an opt-in before checking paths, so it cannot pass on an empty
registry walk.

**Probe-verified fixtures (2026-09-28).**

- AC3's record: the two surviving findings on 24 are `bounds` volume (6758 mm³,
  minimum 8000) and `extent_z` (14 mm, minimum 15). The test asserts AC3's
  equality, not those values.
- AC9's config: without the touch flag, the same record and `cfg9` give one
  `coverage/incomplete_span` finding reporting `L6` (see
  `border-aware-span-control`). `L6`, not `S`, is the canonical level adjacent to
  `L5` since item 186. With the flag, `coverage` gives none, through `gate` and
  through `CoverageRule().evaluate` alike.

Named adversarial cases, and no others:

- `any-member-label-gates`: a planted rule on `{23, 24}`, with no opt-in, over
  `rec(crop_fov_si)` gives `[]`. It guards a gate that drops a finding only when
  all of its labels are in the condition, which would let a pair finding on a
  truncated label through (A1).
- `case-level-finding-passes`: a planted rule on `set()` over
  `rec(crop_fov_si)` gives its one finding. It guards a gate that drops every
  finding of a case holding a condition label.
- `opt-in-is-per-condition`: a planted rule on `{24}` that opts in to
  `displaced_vertebra` only gives `[]` over `rec(crop_fov_si)`. It guards a gate
  that admits a rule for opting in to any condition.
- `record-not-mutated`: `rec(crop_fov_si)` compares equal to a deep copy taken
  before `gate(rec(crop_fov_si), cfg)`. It guards a gate that masks or pops the
  condition's labels in place.
- `border-aware-span-control`: AC9's record without the touch flag, under
  `cfg9`, gives exactly one `coverage` finding, with `detector_id ==
  "incomplete_span"` and `"L6"` in its `reason`. It guards AC9 passing because
  `cfg9` never reached the rule.
- `opt-in-rejects-bare-string`: `ConditionOptIn(condition="fov_truncation",
  paths="per_label", reason="x")` raises `ValueError`. It guards a bare string
  passing as a tuple of one-character paths, the defect class item 147 closed
  for `RuleModeDeclaration`.

**Existing tests to reconcile.**

This list comes from targeted greps for `crop_at_border` and `crop_fov_si`
beside `spline_offset`, `bounds`, a firing set or a finding pair, and for
`exempting_rules`, cohort sensitivity literals, and reference-backed findings on
label 22. New values were measured by the probes named under Assumptions. A
broader read-only sweep had not reported when this spec was committed, so the
builder treats a red test outside this list as a hand-back.

- **`crop_fov_si` fires nothing:**
  - `test_175`
    `test_ac9_case_fires_bounds_on_the_remnant_and_nothing_else` (line 239):
    the triple set becomes `set()`. The name stays; the docstring and a dated
    comment say the gate drops `bounds` on the truncated remnant.
- **`crop_at_border` fires `border` only:**
  - `test_189` `test_ac11_crop_at_border_firing_is_remeasured` (line 174):
    `{"border"}`.
  - `test_149` line 846: `["border"]`.
  - `test_151` line 417: `{"border"}`.
  - `test_129` `_PRE_129_FINDINGS["crop_at_border"]` (line 728):
    `{("border", (22,))}`.
  - `test_145` `test_ac14_fov_truncation_case_expects_border_and_mislabel_with_reason`
    (line 904): `("border",)`. The `reason` checks stay (step 6 keeps
    `centroid` and `curve`/`spline`). Line 913 becomes
    `"spline_offset" not in condition.opting_in_rules`.
  - `test_145` `test_ac15_fov_truncation_displacement_claim_holds_live`
    (lines 971 and 1001–1006): the expected set is `{"border"}`, and the
    co-firing claim inverts to "no `spline_offset` finding names the label".
    The live-offset half (label 22's interior offset exceeds every other) and
    the `is_terminal`-in-mechanism check stay.
  - `test_145` `test_adv_condition_case_narrowed_expectation_is_a_disagreement`
    (line 1488): the precondition becomes `measured(case) == ("border",)`,
    and the narrowed copy uses `expected_firing=()`, which still disagrees.
  - `test_125` `test_ac16_mode6_fires_both_border_and_mislabel` (line 516):
    `"border" in rule_ids` stays; the second assertion becomes
    `"spline_offset" not in rule_ids`.
  - `test_123` `test_ac15_mode6_crop_at_border_fires_mislabel_and_border_on_label_22`
    (line 779): `offset == []`; the `border` half stays.
  - `test_120` `test_ac23_border_crop_case_gains_mislabel_finding_border_unchanged`
    (line 706): the offset-finding list is empty; the verdict, the `border`
    union `{22}` and the 18.0256 mm offset value stay.
  - `test_116` `_ITEM_120_NEW_MISLABEL_CASES` (line 398) becomes
    `frozenset({"displace"})`. Its test skips when the reference commit is
    absent, so it may not run locally.
  - `test_098` `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS["crop_at_border"]`
    (lines 957–983): the `spline_offset` finding is removed, leaving the
    `border` finding; the verdict stays `flagged-for-review`. `test_102`
    reads the same constant and needs no edit.
  - `test_123` `test_ac28_pinned_snapshot_reasons_name_the_current_threshold`
    and `test_ac28_pinned_snapshot_reasons_equal_committed_golden_reasons`
    (lines 1070–1109): their `crop_at_border` halves read that removed entry.
    Each becomes an assertion that neither the constant nor the fresh
    report carries a `spline_offset` finding for `crop_at_border`. The
    `displace` halves stay.
- **`reference_delta` on a truncated label:**
  - `test_049`
    `test_ac11_size_distorting_perturbation_fires_reference_delta_finding_on_label_22`
    (line 219), `crop_at_border` parameter: `[False, False]`, because the gate
    drops `reference_delta`'s finding on the touching label 22. The
    `inject_islands` parameter and the out-of-range sibling test (which reads
    the delta block, not findings) stay.
- **Corpus sensitivity** (measured: tp 9, fn 1, fp 0, tn 4; fov_truncation
  bucket 1 case at 1.0):
  - `test_120` `test_ac24_corpus_pipeline_detection_is_nine_of_ten`
    (lines 807 and 827): `10.0 / 11.0` → `9.0 / 10.0`, and the per-mode
    `n_cases` sum `11` → `10`. The condition sensitivities stay 1.0.
  - `test_057` `test_overall_corpus_sensitivity_is_nine_of_ten_not_over_claimed`
    (line 215): `10.0 / 11.0` → `9.0 / 10.0`.
- **`exempting_rules` renamed:**
  - `test_145` `test_ac2_condition_fields_are_populated` (line 393):
    `condition.opting_in_rules`.
  - `test_145` `test_ac5_condition_exempting_rules_are_registered_and_distinct`
    (lines 541–553): every id in `recording_rules + opting_in_rules` is
    registered. The disjointness assertion inverts to
    `set(condition.recording_rules) <= set(condition.opting_in_rules)`,
    because the recorder now opts in.
  - `test_189` `test_ac12_terminal_skip_exemption_moves_with_detector`
    (line 184): `set(condition.opting_in_rules) == {"border"}`.
- **Unchanged, checked:** `test_120` AC17's and `test_123`'s
  `_THRESHOLD_CARRYING_CASES` exclusion sets read offsets, which do not move;
  `test_110`'s AC11 is a superset check over designated rules; the severity
  ladders do not move (A5), so `test_100`, `test_102`'s ladder block and
  `test_154` need no edit.

**Correction (2026-09-28): three more tests to reconcile.** A read-only sweep
after `d3d68d7` found them. The list above stands. The builder makes these
edits, each with a dated item-191 comment, and the Authorised paths note of the
same date covers the files. Every value below was measured on 2026-09-28 with
`.venv/bin/python` against the current code. A scratch probe applied A1–A2's
gate by hand to the ungated findings.

- **`test_128`: the reference liveness pin moves to `clean_control`.**
  - `tests/test_128_reference_verse_v1_integrity.py`
    `test_reference_verse_v1_still_loads_and_scores_a_case` (line 72) and
    `tests/test_128_relocation_checks.py`
    `test_ac8_companion_actually_runs_and_finds_label_22_bounds_finding`
    (line 290) both change `"crop_at_border"` to `"clean_control"`. Nothing
    else changes: the call stays `run_qc_with_reference` with the production
    reference, and the filter and the assertion stay
    `f.rule_id == "bounds" and 22 in f.labels` and `len(...) >= 1`.
  - Measured: with `reference_verse_v1`, `bounds` names labels 20–24 on
    `clean_control` both before and after the gate. No `clean_control` label
    touches a face and none is displaced, so the gate reaches none of its
    findings. On `crop_at_border` the same filter goes from label 22 present
    to label 22 absent.
  - The companion's source keeps the tokens `run_qc_with_reference`, `bounds`
    and `22`, so `test_128_relocation_checks.py`'s
    `test_ac8_companion_body_asserts_bounds_finding_on_label_22` (line 260)
    stays green unedited. `clean_control`'s fixture is already under Asserts
    against.
  - The released artifact's sha256 pin in the same file does not move: the
    artifact is not touched.
- **`test_189` AC14: "fires" is read from the rule, not the pipeline.**
  - `test_ac14_recorded_corpus_margins_are_live` (line 213) builds `record`
    first and then sets
    `fires = bool(get_rule("spline_offset").evaluate(record, config))` in
    place of the `pipeline_findings` scan. `get_rule` is already imported.
    Everything else stays.
  - Why: under the gate, `crop_at_border` no longer fires through the
    pipeline. Its interior offsets then join the non-firing pool, so
    `largest_non_firing` becomes 18.025609, `crop_at_border`'s own reading,
    which the docstring already carries. The test would pass while no longer
    checking the non-firing ceiling.
  - Measured with the ungated rule: `displace` and `crop_at_border` fire, and
    no other case does. `largest_non_firing` is 5.624555 (`relabel_swap`,
    label 23), the value the docstring records.
  - The docstring states a margin of the rule's threshold, and the gate sits
    in the runner, not in `evaluate`. So the rule's own `evaluate` is the
    right source for it.
- **Unchanged, checked:**
  - `tests/test_038_coverage_border_overlap_perturbations.py`: two tests
    stay unedited, `test_ac13_crop_at_border_produces_no_spurious_bounds_flag`
    (line 453) and `test_adv_crop_at_border_retains_volume_above_group_minimum`
    (line 760). They are not vacuous today. Measured: the ungated
    `get_rule("bounds").evaluate` returns `[]` on the crop of each of the four
    in-plane faces, so their "no `bounds`" check holds with or without the
    gate. The gate could only hide a future regression on label 22, and the
    second test pins the operator's property directly, with its
    `physical_volume_mm3 >= min_volume_mm3` assertion. They are not tightened,
    and `test_038` is not authorised.
  - `tests/test_178_corpus_sheet.py` AC7 heals when step 8 regenerates the
    sheet.
  - `tests/test_102_stage18_validation.py` and
    `tests/test_143_s_axis_correction.py` AC9 read `test_098`'s reconciled
    constant, which does not name `crop_fov_si`.
- **Builder rewording in `src/segfacet/heuristics/spline_offset.py`**
  (already authorised, step 5). The "Corpus margins" bullet says
  `crop_at_border`'s `18.025609` mm "**must** fire". That is now true of the
  rule's `evaluate` only. Reword it to say that the rule fires on the reading
  and that the runner's `fov_truncation` gate drops the finding, because this
  rule does not opt in to that condition (item 191). Keep the literal
  `18.025609`, and keep `5.624555` and `14.615923`, because
  `test_189` AC14 checks that all three appear in the docstring.

**Correction (2026-09-28, after validation round 1): AC13's test, and no
reconciliation.**

- The test-writer adds one test to `tests/test_191_condition_gate.py` for
  AC13. It builds `swap` with NumPy on `loaded_seg_image`'s data and
  `nibabel.Nifti1Image(data, img.affine, img.header)`, and asserts AC13's
  equality. No adversarial case is added.
- Probe-verified on 2026-09-28, on this branch with `mislabel`'s opt-in
  applied in-process: the gated findings of `mislabel` and `spline_offset` on
  the swapped record are exactly AC13's set. Without the opt-in they are
  `{("spline_offset", "spline_offset", frozenset({21}))}` only.
- `tests/test_033_mislabel.py` is **not** reconciled. Its synthetic record
  (offset 41.3 mm on L1, label 20; ordering pair T12/L1, labels 19 and 20) is
  a small copy of the case AC13 guards: a label that is both displaced and out
  of order. Its round-1 failures show the gate's defect, not a stale
  assertion. Probe-verified with the opt-in: `run_rules` returns
  `mislabel/ordering` on {19, 20} and `spline_offset` on {20}, both `FLAG`
  under the default config, in `mislabel`, `spline_offset` order.
- Other test files checked:
  - `tests/test_191_condition_gate.py` AC10 derives the expected tuple from
    the registry and needs no edit.
  - `tests/test_145_eight_hypothesised_modes.py` AC5 still holds
    (`recording_rules <= opting_in_rules`).
  - `tests/test_189_spline_offset_condition.py` AC12 and `test_145` line 921
    read `fov_truncation`, which does not move.
  - No test pins `displaced_vertebra`'s `opting_in_rules` or `mislabel`'s
    `condition_opt_ins` as a literal.

## Validation

1. Replay `crop_fov_si` through the CLI, without a reference:

   ```
   .venv/bin/segfacet run --scan tests/corpus/fixtures/crop_fov_si_scan.nii.gz --seg tests/corpus/fixtures/crop_fov_si_seg.nii.gz --out <tmp> --no-reference
   ```

   `--no-reference` is needed for the reason `CLAUDE.md` gives. `<tmp>/segfacet_report.json`
   must hold no finding, and the verdict must be `pass`.
2. The same command without `--no-reference` must hold no finding naming label
   24 (AC2 through the CLI).
3. In `docs/aide/failure_modes.generated.md`, the `## Condition fov_truncation`
   section lists `- Opting-in rules: border`, `crop_at_border` expecting
   `border` and `crop_fov_si` expecting nothing.

No environment profile is needed.

## Dependencies

- Item 189: added `spline_offset` and the `displaced_vertebra` condition this
  item gates, and set `fov_truncation.exempting_rules`, which this item
  replaces (✅).
- Item 190: added the condition-keyed eval bucket whose `fov_truncation` count
  this item changes (✅).
- Items 186, 187 and 188: last re-measured the corpus firing sets and the rule
  count this item's ratchet run reads (✅).

**Downstream:**

- Item 192's `sequence` sub-types read labels a condition may now gate; a pair
  finding on a truncated label is dropped (A1).
- Item 194's mode-1 attribution and item 195's `force_overlap` removal
  regenerate the same two artifacts.
- Stage 33 D4's `rules.generated.md` may render each rule's opt-ins.

## Decisions & Trade-offs

Implemented 2026-09-28. The gate lives in `run_rules`
(`src/segfacet/heuristics/runner.py`): every enabled rule's `evaluate` still
runs first, unchanged; the runner then drops a finding when any of its
`labels` is a member of a condition its producing rule does not opt in to,
via a new `Rule.condition_opt_ins` class attribute of `ConditionOptIn`
entries (`src/segfacet/heuristics/rule.py`). `fov_truncation` membership is
`segfacet.heuristics.fov.border_touching_labels(record)` (added to the
existing shared `fov.py`, so the runner imports no rule module);
`displaced_vertebra` membership is derived from the *surviving*
`spline_offset` findings, so the two gates run in that order (A2/A3). `border`
and `spline_offset` each declare `condition_opt_ins` naming their own
recording condition and nothing else. `ConditionSpec.exempting_rules`
(`src/segfacet/failure_modes.py`) is renamed `opting_in_rules`, both
conditions' corpus-case expectations and `mechanism` prose are re-measured,
and `specification_to_dict`/`render_markdown` follow the rename.
`CropFovPerturbation`'s `Expectation` (`src/segfacet/synth/
coverage_border_overlap.py`) now expects nothing on `crop_fov_si` and a
`"pass"` verdict, matching the regenerated `tests/corpus/manifest.json`
(only `crop_fov_si`'s three fields changed; every fixture stayed
byte-identical, confirmed by a two-run byte-compare before committing).
`docs/aide/corpus_sheet.png`, `failure_modes.generated.{json,md}` and
`traceability_matrix.generated.{json,md}` were regenerated; `docs/aide/
feature_catalogue.generated.json` and `golden_evidence.generated.json` came
out byte-identical, as A5 predicted (the catalogue already attributed
`border`'s and `spline_offset`'s opt-in paths to those rules via mechanism A's
dynamic access trace, since the rules already read them in `evaluate` before
this item — the gate adds no new path access). Every AC and named adversarial
case was independently verified against the real change before committing
(not only the Assumptions' scratch-probe values).

- **Left open:** which non-recording rules should opt in to a condition, and
  for which features. `bounds`' volume is unchanged by a rigid displacement,
  and intensity is not spoiled by truncation, but no committed case needs
  either opt-in yet, and the roadmap decides validity per rule when a rule
  needs it.
  - 2026-09-28, after validation round 1: decided for `mislabel`, which opts
    in to `displaced_vertebra` (A3's correction). It stays open for every other
    rule. `sequence` and `overlap` were not measured on a displaced label: no
    case or swap probe put one of their findings there.
- **Left open:** per-detector or per-feature opt-in. An opt-in admits all of a
  rule's findings on a condition's labels; a rule that needs only some of its
  detectors admitted needs a finer grain than this item builds.
- **Left open:** reporting what the gate dropped. A dropped finding leaves no
  trace in the JSON or text report; surfacing it is a report-schema change.
