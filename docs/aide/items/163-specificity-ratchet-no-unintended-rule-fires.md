<!-- aide-template: item 2 -->
# Item 163 — The specificity ratchet: no unintended rule may fire

> **Created:** 2026-09-20 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 32 — Selected-Mode Refinement: one failure mode fully specified end to end (D0; closes Stage 20's held specificity deliverable)
> **Queue:** [`../queue/queue-022.md`](../queue/queue-022.md) · Item 163
> **Objectives:** G2 (a co-detection is allowed only where the specification records it), G7 (the allowlist is derived from the specification on every run, never authored beside it)
> **Suggested branch:** `aide/163-the-specificity-ratchet-no-unintended`

---

## Description

From this item on, **every change in what fires is either authored in the
specification or fails the suite**. That is the whole deliverable: the
refinement items that follow (164 detector ids, 165 mode 4, 166/167 mode 3)
each move rules, thresholds, fixtures and detectors, and without a standing
per-case guard a widened detector that starts firing on a neighbouring case
lands green.

**The comparison already exists; the guard does not.** Item 149's
`traceability.ConformanceReport` already walks both committed manifests, calls
`segfacet.failure_modes.measured_firing` per case and scores the measured set
against the specification's `expected_firing` (measured 2026-09-20: 15 cases —
11 geometric + 4 intensity — all agreeing, `conformant: true`). This item
builds **no second measurement path**. It adopts that comparison as a named,
per-case ratchet, and closes the three gaps that stop today's state from being
one:

1. **No diagnostic.** The only standing assertion over it,
   `tests/test_149_conformance_report.py::test_ac16_committed_tree_agrees_on_every_case_and_is_conformant`,
   is one boolean over the whole report: a real regression prints
   `assert 1 == 0` and names no case. Item 149's "would fail loudly" test
   builds its message from a hand-made disagreement, not from the assertion
   path.
2. **The measured side is never perturbed.** Every adversarial fixture in
   item 149 edits the *expected* side (an altered expected set, an emptied
   `corpus_cases`). Nothing demonstrates that a rule which *starts firing*
   where the specification does not record it is caught — which is the literal
   deliverable, "no unintended rule may fire".
3. **A divergence currently degrades instead of failing.**
   `failure_modes.derive_status` folds case agreement into `"validated"`, so an
   unintended firing silently demotes a mode to `"implemented"`; and it reads
   `SPECIFICATION[*].corpus_cases` only, so the clean controls
   (`clean_control`, `clean_hu`) and the condition case (`crop_at_border`,
   carried by `CONDITIONS`) are outside it altogether.

The allowlist is the specification's and only the specification's.
`crop_at_border` is the worked example: the specification records
`{border, mislabel}` while the **manifest's** `expected_rule_ids` names
`["border"]` alone, and `synth.regression.verify_case` filters findings down to
that manifest field — so the corpus harness can never be this ratchet, and this
item does not change it (see Left open).

### What this item is NOT

- **Not a second measurement path.** No new production measurement, no new
  artifact, no schema change, no CLI change. The only production edit is one
  line of `src/segfacet/traceability.py`'s scope-fence docstring, which still
  says "adopts no specificity ratchet (item 163)" and would otherwise read as
  pending forever.
- **Not a corpus, rule or threshold change.** No corpus case is added, removed
  or regenerated; no rule, detector, declaration or threshold is edited; no
  `ModeSpec`, `IntendedRule` or `expected_firing` is authored or altered. The
  ratchet is adopted against the tree exactly as it stands.
- **Not a regeneration.** Neither committed traceability artifact changes
  (a module docstring is read by nothing — `matrix_to_dict` and
  `render_markdown` never touch `__doc__`), so neither is regenerated.
- **Not per-detector.** Attribution below rule granularity is item 164's.

## Acceptance Criteria

- [ ] **AC1: Every committed corpus case is driven, none exempt.** The set of
  `(corpus, case_id)` pairs the ratchet drives equals, exactly, the union of
  the `case_id`s in `tests/corpus/manifest.json` (as `"geometric"`) and
  `tests/corpus/intensity/manifest.json` (as `"intensity"`), read live in the
  test through `segfacet.synth.corpus.load_manifest()` and
  `segfacet.synth.intensity.load_intensity_manifest()` — with no literal case
  list and no filter on `kind`, `detection` or `failure_mode`. (15 pairs on
  this tree, measured 2026-09-20; the number is recomputed, never pinned.)
- [ ] **AC2: The ratchet.** For every pair AC1 enumerates,
  `set(measured_firing) == set(expected_firing)` on that case's record in
  `segfacet.traceability.build_matrix().conformance.cases`, asserted one
  parametrised test per case so a regression fails under the case id it
  belongs to. *(closes Stage 20 criterion 4)*
- [ ] **AC3: The allowlist is the specification's, recomputed from the primary
  source.** For every case AC1 enumerates, the conformance record's
  `expected_firing` equals the expected set recomputed in the test directly
  from `segfacet.failure_modes`, dispatched on the record's
  `expected_source`: the matching `SPECIFICATION[mode].corpus_cases` entry for
  `"specification"`, the matching
  `CONDITIONS[<the manifest case's condition>].corpus_cases` entry for
  `"specification-condition"`, and the empty set for
  `"manifest-clean-control"` (a case whose
  `segfacet.synth.perturbation.corpus_case_kind` is `clean_control`). A case
  whose `expected_source` is `"unspecified"` has no primary-source set to
  recompute and fails this criterion — it is never exempt from the ratchet.
- [ ] **AC4: An unintended rule firing is caught.** With a stub `Rule`
  registered that emits one `Finding` carrying its own `rule_id` on every
  record, the ratchet's comparison for the geometric case `fragment`,
  recomputed live through `segfacet.failure_modes.measured_firing`, reports a
  violation whose unintended set (`measured - expected`) is exactly that stub
  rule's id.
- [ ] **AC5: The violation names the case and both sets.** The text the
  ratchet passes as the assertion message for a violating case contains the
  corpus, the case id, the expected set and the measured set — produced by the
  same helper AC2's per-case test uses as its message, so a real regression
  prints all four.
- [ ] **AC6: A rule that stops firing is caught.** With the registered
  `fragmentation` rule patched to return no findings, the same comparison for
  the geometric case `fragment` reports a violation whose missing set
  (`expected - measured`) is exactly `{"fragmentation"}`.

## Assumptions

- **A1 (the ratchet reads item 149's `ConformanceReport`, and pins it at the
  level this item reads it):** `segfacet.traceability.build_matrix().conformance.cases`
  is a tuple of records each carrying `corpus`, `case_id`, `mode`,
  `expected_firing`, `measured_firing`, `agrees` and `expected_source`, with
  `expected_source` drawn from
  `{"specification", "specification-condition", "manifest-clean-control", "unspecified"}`;
  the loop always walks the two manifests, never `SPECIFICATION`, so a
  manifest case cannot fall out of the report. Read from the merged code on
  this branch's base, 2026-09-20 — item 149 has merged, so this is live state,
  not a forward pin.
- **A2 (the ratchet is a suite guard, not a production API):**
  `matrix.conformance.disagreements` already *is* the violation list, so no
  production function is added for it and the comparison plus its message
  formatting live in the test module. A production helper would be a second
  name for a derivation `_build_conformance` already performs, and item 169
  drives this guard by running the suite, not by calling an API.
- **A3 (the adversarial perturbations drive one case, not a second
  `build_matrix()`):** each `build_matrix()` runs all 15 cases through the
  pipeline and costs 7–27 s (`insights.md`, 2026-09-18, the suite wall-clock
  entry). AC4 and AC6 therefore register/patch a rule and call
  `measured_firing` on one named case — the same function `_build_conformance`
  calls, so the path proved is the ratchet's own.
- **A4 (the manifest's `expected_rule_ids` is not the allowlist, and is not
  touched):** measured 2026-09-20, the two fields diverge for exactly one case
  — `crop_at_border`, manifest `["border"]` against the specification's
  `("border", "mislabel")`. `synth.regression.verify_case` filters to the
  manifest field and so passes co-detections silently; tightening it is a
  separate change with its own blast radius and is left open below.
- **A5 (`measured_firing` raises rather than degrades, and the raise stays
  unreachable here):** it raises `ValueError` on a `case_id` absent from the
  manifest it resolves against (item 162's recorded trap). Every case
  expectation this item constructs carries a `case_id` read from a manifest,
  so no degradation path is added and none is needed.
- **A6 (the status flips land on two bullets, and this item does not repair
  that):** `progress.md` carries `*(Item 163)*` on its correctly-numbered
  Stage 20 bullet ("Specificity assertion — no unintended rule may fire — as a
  ratchet …") **and**, through the mislabeling recorded in `insights.md`
  (item 162, 2026-09-18), on Stage 32's D1 "MVP mode" bullet, which queue-022
  numbers 165. A status flip for this item lands on both. The repair is not
  assigned by queue-022 and is not attempted here; the captured entry stands.
- **A7 (no human gate):** every input is committed state on this tree and
  every judgement is derived from the signed-off specification or a committed
  manifest. No row is added to `progress.md`'s `## Human gates` table.
- **A8 (engine 1.59.2):** `aide scope`'s §6 check reports a test that names
  neither an acceptance criterion nor a Testing-Strategy case (the finding that
  retired one of item 162's tests on 2026-09-20), so the Testing Strategy below
  names the one extra case with its label and failure mode, and nothing else is
  written.

## Implementation Steps

1. **Re-point one line of `src/segfacet/traceability.py`'s scope fence.** The
   sentence "It adopts no specificity ratchet (item 163) and no detector ids
   (item 164), and does not touch ``eval/severity_ladder.py``." still describes
   the module correctly — the module adopts none — but reads as if item 163 is
   pending. Reword that clause to say the specificity ratchet is enforced by
   `tests/test_163_specificity_ratchet.py` over this module's `conformance`
   report, with the module itself adopting none; leave the detector-ids clause
   (item 164's) and the `eval/severity_ladder.py` clause untouched.
2. **Change nothing else in `src/`.** No new module, no new function, no
   schema or `SCHEMA_VERSION` change; `_build_conformance`,
   `failure_modes.measured_firing` and `synth.regression.verify_case` are
   reused exactly as they stand, and no dependency is added.
3. **Do not regenerate either committed artifact.** `matrix_to_dict` and
   `render_markdown` read no module docstring, so
   `docs/aide/traceability_matrix.generated.{json,md}` are byte-unchanged and
   `tests/test_149_conformance_report.py::test_ac20_fresh_matches_committed_byte_for_byte`
   keeps passing untouched. If a regeneration would change a byte, that is a
   contradiction to hand back, not a file to commit.
4. **The guard itself is test-side** — its shape, its one shared comparison
   helper and its fixtures are specified under Testing Strategy, which the
   test-writer builds from.

## Authorised paths

**May change:**

- `tests/test_163_specificity_ratchet.py` — this item's deliverable: the ratchet and its two adversarial proofs (AC1–AC6).
- `src/segfacet/traceability.py` — one scope-fence docstring clause re-pointed at the guard that now enforces the ratchet (step 1); no code path changes.

**Asserts against:**

- `src/segfacet/failure_modes.py` — `SPECIFICATION`, `CONDITIONS` and `measured_firing`; AC3 recomputes every expected set from them and AC4/AC6 measure through them. Unchanged: no `ModeSpec`, `IntendedRule` or `expected_firing` is edited.
- `tests/corpus/manifest.json` — the eleven geometric cases AC1 enumerates and AC4/AC6 resolve against; read-only, no case added, removed or regenerated.
- `tests/corpus/intensity/manifest.json` — the four intensity cases AC1 enumerates; read-only, same terms.
- `src/segfacet/heuristics/rule.py` — `iter_rules()`/`register_rule` and the module-level registry AC4 registers a stub into inside a restoring fixture; the file itself is unchanged, and no rule, threshold or declaration is edited.
- `src/segfacet/heuristics/fragmentation.py` — the registered rule AC6 patches in-session to emit nothing; the file itself is unchanged.
- `docs/aide/traceability_matrix.generated.json` — pinned-not-changed: step 3 asserts this item regenerates nothing, and item 149's byte comparison stays green untouched.
- `docs/aide/traceability_matrix.generated.md` — same, its rendered form.

## Testing Strategy

**Module:** `tests/test_163_specificity_ratchet.py`.

**Shape.** One module-scoped `build_matrix()` fixture (the pattern
`tests/test_162_corpus_exercise_report.py` and `tests/test_149_conformance_report.py`
use), and **no second `build_matrix()` call anywhere in the module** — A3.
Every `build_matrix()` call sits in a fixture, never in a test body, so item
149's AC28 idiom holds here too.

One **shared comparison helper** is the module's spine: given a corpus, a case
id, an expected set and a measured set it returns the unintended set
(`measured - expected`), the missing set (`expected - measured`) and one
message naming corpus, case id, expected and measured. AC2's per-case test
passes that message as its assertion message; AC4, AC5 and AC6 call the same
helper — so the guard and its proofs share one code path and neither can pass
vacuously while the other is wrong.

**One test per AC.** AC1 and AC3 are single tests iterating the live case set;
AC2 is parametrised over that set, one parametrisation per `(corpus, case_id)`
pair, ids naming the case. AC4 and AC6 each drive the single geometric case
`fragment` through `measured_firing` with the registry perturbed inside a
snapshot-and-restore fixture (item 162's `_isolated_rule_registry` idiom), and
compare through the shared helper. AC5 asserts on the message the helper
returns for AC4's violation.

**Adversarial case beyond the AC tests — exactly one:**

- `unspecified-case-is-not-exempt`: with one mode's `corpus_cases` emptied
  (item 149's `matrix_mode6_corpus_cases_emptied` idiom, a patched
  `SPECIFICATION`), the affected manifest case's record turns
  `expected_source == "unspecified"` and **fails** AC3's recomputation rather
  than dropping out of the ratchet. Guards the failure mode that would make the
  whole guard hollow: a case silently leaving the allowlist's reach by losing
  its specification entry, so that deleting a spec entry becomes a way to
  silence a violation.

**Existing tests to reconcile: none.** No test in the suite fences a
specificity ratchet, asserts its absence, or pins a count this item moves
(grepped 2026-09-20 for `specificity`, `ratchet`, `unintended`, `item 140` and
`163` across `tests/`). The only live statement that item 163 is unadopted is
the `src/segfacet/traceability.py` docstring clause step 1 re-points, and no
test reads it.
`tests/test_149_conformance_report.py::test_ac16_committed_tree_agrees_on_every_case_and_is_conformant`
overlaps AC2 in subject and stays exactly as it is — it is item 149's own
report-schema claim, not an expired fence (see Left open).

## Validation

Run the guard alone and read its parametrisation:

```
.venv/bin/python -m pytest tests/test_163_specificity_ratchet.py -v
```

Confirm by eye that AC2's parametrised test ids name **every** corpus case of
both corpora — all 11 geometric (`clean_control`, `crop_at_border`,
`displace`, `force_overlap`, `fragment`, `fuse_adjacent`, `inject_islands`,
`relabel_swap`, `remove_level`, `remove_level_relabel`, `sequence_break`) and
all 4 intensity (`clean_hu`, `degenerate_uniform`, `implausible_metal`,
`implausible_soft_tissue`) — since the coverage claim is exactly what a
parametrised guard can lose silently. No `[validation]` profile is needed: the
ratchet runs on the committed corpora with no optional dependency.

## Dependencies

- **Item 149** — `traceability.ConformanceReport`: the per-case
  expected-vs-measured comparison this item adopts as a ratchet (A1), and the
  `expected_source` vocabulary AC3 dispatches on.
- **Item 150** — the maintainer-signed-off sixteen-mode specification and
  `CONDITIONS`, the primary source AC3 recomputes every expected set from.
- **Item 155** — the corpus-case `kind` field, which is what makes a clean
  control's empty expected set a scored record rather than a disagreement.
- **Item 157** — the current corpus `case_id`s (no `modeN_` prefix), the ids
  AC1 enumerates and AC4/AC6 name.
- **Item 162** — merged immediately before this item on `aide/queue-022`; it
  owns the `exercise` block in the same module, so step 1's docstring edit must
  land on top of its rewritten scope fence rather than reinstating the older
  text.

**Downstream:** item 164 (detector ids) must keep this ratchet green with no
specification edit to any expected set; items 165, 166 and 167 author each new
or changed expected set in the specification, and this guard is what fails if
they do not; item 169 drives it from a clean clone and attests Stage 20
criteria 3–5.

## Decisions & Trade-offs

- **No production code beyond the one docstring clause.** Verified before
  editing: `_build_conformance` (with `expected_source` in
  `{"specification", "specification-condition", "manifest-clean-control", "unspecified"}`)
  and `build_matrix()` already exist exactly as A1/A2 describe, and
  `tests/test_163_specificity_ratchet.py` (committed by the test-writer) calls
  only that live surface plus `segfacet.failure_modes.measured_firing`,
  `segfacet.synth.corpus.load_manifest`, and
  `segfacet.synth.intensity.load_intensity_manifest`. Implementation is
  therefore exactly Implementation Step 1: re-pointing the scope-fence clause
  in `src/segfacet/traceability.py` so it names the guard
  (`tests/test_163_specificity_ratchet.py`) instead of reading as pending; the
  detector-ids clause (item 164) and the `eval/severity_ladder.py` clause are
  left untouched. No new function, schema, or artifact regeneration.

- **Left open:** whether `synth.regression.verify_case` should be tightened
  from "the designated rules fired" to exact-set equality against the
  specification. It filters findings to the manifest's `expected_rule_ids`,
  which diverges from the specification for `crop_at_border` (A4), so
  tightening it means reconciling the two fields across every corpus case and
  every test that drives the harness — a change with its own blast radius that
  the ratchet does not need. This item leaves the corpus harness untouched and
  enforces specificity above it.
- **Left open:** whether
  `tests/test_149_conformance_report.py::test_ac16_committed_tree_agrees_on_every_case_and_is_conformant`
  should be retired now that AC2 asserts the same property per case with a
  diagnostic. It is a live, true claim of item 149's own module rather than an
  expired fence, so retiring it is a judgement about duplicate coverage, not a
  contradiction this item must resolve; item 169 sees both when it replays the
  stage.
