<!-- aide-template: item 1 -->
# Item 156 — The three unclosed conformance seams in the specification checks

> **Created:** 2026-09-16 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update
> **Queue:** [`../queue/queue-021.md`](../queue/queue-021.md) · Item 156
> **Objectives:** G7, G8
> **Suggested branch:** `aide/156-the-three-unclosed-conformance-seams`

---

## Description

Roadmap Stage 31 D4, second part. Three Stage-30 residues in the checks that
guard `segfacet.failure_modes.SPECIFICATION`. Each is a located `insights.md`
entry, and each is closed here or handed on with a recorded reason.

### Seam 1: the unmirrored declaration

Absorbs the `gap` entry dated 2026-09-04 (item 147) that begins "after item 147
nothing reports a rule declaring a **known** mode".

Two checks exist today, one per direction:

- `failure_modes._intended_rule_conflicts` checks **specification →
  declaration**: every `IntendedRule` edge must be declared by its rule.
- `catalogue.rule_declaration_conflicts` checks **corpus → declaration**, and
  reports a declared mode outside `SPECIFICATION`'s key set.

Nothing checks **declaration → specification** for a mode that *is* in the key
set. A rule can declare a listed mode that no `IntendedRule` edge mirrors, and
every check passes. `traceability.build_matrix()` then lists that rule under the
mode, and the committed matrix states a claim that no check made.

Measured on this branch (2026-09-16), with `reference_delta`'s declared modes
replaced by the ones shown:

| Replacement modes | `rule_declaration_conflicts()` | `specification_conflicts()` |
|---|---|---|
| `(1, 2, 3, 4, 6, 8)` | `()` | `()` — fully silent; mode 6 is `specified` and has only a `coverage` edge |
| `(1, 2, 5)` (the insight's control) | `()` | 4 messages: proposed-drift for mode 5, plus spec → declaration for modes 3, 4, 8. **None of them names `reference_delta` together with mode 5.** |

The insight's `(1, 2, 5)` control is no longer fully silent. The item-150
re-keying made mode 5 a `proposed` mode, so the proposed-drift check now fires
on it. That check names the mode and not the rule, so the seam is still open.

**The fix** adds the missing direction to
`catalogue.rule_declaration_conflicts()`. For every registered rule, and every
mode `m` it declares that is a key of `SPECIFICATION`, the rule must appear
among `SPECIFICATION[m].intended_rules`. If it does not, the check reports one
message naming both the rule and the mode. On the shipped tree the declarations
and the edges already agree exactly (measured, see AC1), so the new direction
reports nothing today.

### Seam 2: the geometric-only attribution scan

Absorbs the `gap` entry dated 2026-09-04 (item 148) on the rule-attribution
column, and the dated 2026-09-15 trail line under it.

`catalogue.scan_synth_rule_mode_map()` is an AST scan. It matches only
`Expectation(...)` literals in `src/segfacet/synth/*.py`, so it never sees the
intensity corpus, whose cases are `_RecipeEntry(...)` literals. Item 149
moved the matrix's `attribution` column off this scan. The scan still feeds
`TraceabilityMatrix.corpus_designated_unregistered_rule_ids`, so that direction
cannot see an intensity case that names a rule no rule registers.

**The fix:** `build_matrix()` derives `corpus_designated_unregistered_rule_ids`
from the two committed manifests, which it already loads:

- `expected_rule_ids` for each geometric case;
- `expected_firing` for each intensity case.

It stops reading the scan. The scan itself does not change, and it keeps two
consumers:

- mechanism C of `build_catalogue`, whose output is the committed feature
  catalogue;
- the corpus → declaration direction of `rule_declaration_conflicts`.

Both are fenced in docstrings that name the intensity corpus as unread (see
A4).

### Seam 3: the retired "complete, always" contract

Absorbs the `defect` entry dated 2026-09-04 (item 146), which says the "mode →
rule is complete, always" contract survives in the documents it was authored
in.

`src/segfacet/traceability.py`'s `_NOTE` and module docstring already say both
directions are *scored*. They also say a `proposed` mode is a legitimate mode →
rule hole. A grep on 2026-09-16 found no complete-always phrasing anywhere under
`src/segfacet/` or in `docs/aide/*.generated.*`. This item pins that state with
a tree-wide check.

Two sentences still assert the retired contract: the two "**Yes, always**" rows
of `docs/aide/roadmap.md`, at lines 919 and 920. They are **handed back to the
next roadmap revision** and not edited here, because `roadmap.md` is a root
document. The refuting measurement goes into `insights.md`, as a dated trail line
under the item-146 entry (Implementation Step 7). Measured 2026-09-16 at
`f14fcc0`:

- `build_matrix().mode_to_rule` → `complete=False`,
  `holes=('10', '11', '12', '13', '14', '5', '7')`. These are exactly the modes
  whose `derive_status` is `proposed`. This refutes row 919.
- `build_matrix().rule_to_mode` → `complete=True`, `holes=()`. The direction is
  complete today, but only by measurement: a `pending` declaration makes a hole.
  The row's "Four rules sit here today" measures zero. So row 920 is refuted as
  a contract ("always") and as a count, but not as today's value.

`progress.md` lines 967–968 restate the same contract. They are a dated
2026-08-11 record and are kept as written, as the queue decides.

**Not in scope:**

- No `ModeSpec` or `ConditionSpec` field changes. No rule's `mode_declaration`,
  threshold, verdict or firing set changes. No corpus case's `expected_firing`
  or `expected_rule_ids` changes. No manifest is regenerated.
- `catalogue.scan_synth_rule_mode_map()` returns the same mapping as before. The
  feature catalogue (`docs/aide/feature_catalogue.generated.*`) is not
  regenerated and does not change.
- The committed traceability artifacts (`docs/aide/traceability_matrix.generated.*`)
  do not change. None of the three fixes alters a rendered value on the shipped
  tree, and `_NOTE` is already correct.
- `roadmap.md` and `progress.md` prose are not edited.

## Acceptance Criteria

- [ ] **AC1: the declarations mirror the specification's edges on the shipped
  tree.** The set of `(rule_id, mode)` pairs is the same from both sides:
  - from declarations: each rule in `heuristics.rule.iter_rule_declarations()`
    with a non-`None` declaration, and each mode it declares that is a key of
    `failure_modes.SPECIFICATION`;
  - from the specification: each `(edge.rule_id, mode_id)` over
    `SPECIFICATION.items()` and each mode's `intended_rules`.

  The test computes both sets live.
- [ ] **AC2: an unmirrored declaration on a `specified` mode is reported, naming
  rule and mode.** Monkeypatch `reference_delta`'s `mode_declaration` to
  `dataclasses.replace(original, modes=(1, 2, 3, 4, 6, 8))`. Then
  `set(catalogue.rule_declaration_conflicts()) - set(baseline)` holds exactly one
  message, and that message contains both `'reference_delta'` and `6`.
  `baseline` is the tuple from before the patch.
- [ ] **AC3: the queue's `(1, 2, 5)` control is reported, naming rule and
  mode.** Monkeypatch `reference_delta`'s declared modes to `(1, 2, 5)`. Then
  `catalogue.rule_declaration_conflicts()` contains a message that includes both
  `'reference_delta'` and `5`.
- [ ] **AC4: the check is unconditional on corpus evidence.** Monkeypatch
  `fragmentation`'s declared modes to `(1, 2, 4)`. Mode 2's committed case
  `fuse_adjacent` expects `fragmentation`, but `SPECIFICATION[2].intended_rules`
  has no `fragmentation` edge. Then `catalogue.rule_declaration_conflicts()`
  contains a message that includes both `'fragmentation'` and `2`.
- [ ] **AC5: the new message is not read as a rule → mode hole.** Under AC2's
  perturbation, `traceability.build_matrix().rule_to_mode.holes == ()`.
- [ ] **AC6: a mode outside the key set is reported once, not twice.**
  Monkeypatch `bounds`'s declared modes to `(999,)`. Then exactly one message
  in `catalogue.rule_declaration_conflicts()` contains both `'bounds'` and
  `999`.
- [ ] **AC7: the shipped tree designates no unregistered rule.**
  `traceability.build_matrix().corpus_designated_unregistered_rule_ids` equals a
  sorted tuple the test recomputes from primary sources: every rule id in a
  geometric case's `expected_rule_ids` (from `synth.corpus.load_manifest()`) or
  an intensity case's `expected_firing` (from
  `synth.intensity.load_intensity_manifest()`), minus the ids of
  `heuristics.rule.iter_rules()`.
- [ ] **AC8: an intensity case naming an unregistered rule is reported.** Patch
  `synth.intensity.load_intensity_manifest` to return a deep copy whose
  `implausible_metal` case has `"__item156_unregistered__"` appended to
  `expected_firing`. Then that id is a member of
  `build_matrix().corpus_designated_unregistered_rule_ids`.
- [ ] **AC9: a geometric case naming an unregistered rule is reported.** Patch
  `synth.corpus.load_manifest` to return a deep copy with
  `"__item156_unregistered__"` appended to one failure case's
  `expected_rule_ids`. Then that id is a member of
  `build_matrix().corpus_designated_unregistered_rule_ids`.
- [ ] **AC10: the matrix field is not derived from the AST scan.** Patch both
  `catalogue.scan_synth_rule_mode_map` and `catalogue._scan_synth_rule_mode_map`
  to return the real mapping plus `"__item156_scan_only__": (6,)`. Then
  `"__item156_scan_only__"` is not a member of
  `build_matrix().corpus_designated_unregistered_rule_ids`.
- [ ] **AC11: no production source or generated artifact asserts a
  complete-always direction.** Apply the phrase matcher defined under Testing
  Strategy to every `*.py` file under `src/segfacet/` and every file matching
  `docs/aide/*.generated.*`. It returns an empty list of hits.
- [ ] **AC12: the phrase matcher detects each forbidden phrasing.** Run the
  AC11 matcher on synthetic strings. It returns at least one hit for each
  member of the forbidden phrase set, for the same phrase in upper case, and
  for `"complete,\n    always"` split across a line break.
- [ ] **AC13: every `proposed` mode is a mode → rule hole.** For every mode id
  `m` in `failure_modes.SPECIFICATION` where
  `failure_modes.derive_status(SPECIFICATION[m]) == "proposed"`, `str(m)` is a
  member of `traceability.build_matrix().mode_to_rule.holes`.
- [ ] **AC14: the committed conformance report is unchanged by this item.** The
  JSON and Markdown that `python -m segfacet.traceability` writes are
  byte-identical to the committed `docs/aide/traceability_matrix.generated.json`
  and `.md`. The existing
  `tests/test_149_conformance_report.py::test_ac20_fresh_matches_committed_byte_for_byte`
  meets this AC and must pass without changes to its assertions.

No AC here closes a Stage 31 acceptance criterion. None of the stage's five
criteria is about these seams.

## Assumptions

- **A1: the new direction goes in `catalogue.rule_declaration_conflicts()`, not
  `failure_modes.specification_conflicts()`.** `specification_conflicts(modes)`
  accepts a partial mode tuple, and tests call it on hand-built single-mode
  probes:
  `test_144::test_ac11_forced_status_past_post_init_is_reported_naming_the_mode`
  asserts `len(conflicts) == 1` for a mode-4 probe with only a `fragmentation`
  edge. A declaration → specification check there would add
  `bounds`/`reference_delta` messages to that probe, because both rules declare
  mode 4 in the real registry. `rule_declaration_conflicts()` takes no mode
  argument and already owns the neighbouring "declared mode outside the key
  set" check. It reads `SPECIFICATION` through the module object, so a
  monkeypatched specification is honoured.
- **A2: the mirror is unconditional.** The queue's wording is "no mirroring
  `IntendedRule` edge **and** no corpus case". The check reports any declared
  known mode that has no edge, whether or not a corpus case fires the rule.
  The specification is the record: a rule that co-detects on a mode's case
  without being intended for that mode is recorded in the case's
  `expected_firing` and is not declared. Declarations and edges become an exact
  mirror, which AC1 measures as already true. **Consequence for Stage 32:** a
  rule that gains a declared mode needs a matching `IntendedRule` edge in the
  same change, or `rule_declaration_conflicts()` reports it.
- **A3: the new message is worded so `build_matrix()`'s regex cannot match it.**
  The regex `^rule '([^']+)': declared §6 mode \d+ is outside` reads out
  uncatalogued-mode rule ids. Suggested form:
  `rule '<id>': declares §6 mode <m>, but SPECIFICATION[<m>].intended_rules
  carries no IntendedRule edge for it (edges: [<ids>]).` The exact text is the
  builder's choice, within AC2–AC6 and AC5.
- **A4: Seam 2 is fixed for the matrix field and fenced for the scan's other two
  consumers.** The queue allows either "reads both corpora" or "fenced with the
  limit rendered beside the value".
  - The rendered value, `corpus_designated_unregistered_rule_ids`, moves to both
    manifests.
  - Making the scan itself read the intensity recipes would change mechanism C's
    `mode_evidence`. Measured 2026-09-16: adding `intensity: (16,)` to the scan's
    output changes `catalogue_to_dict(build_catalogue())`. That would regenerate
    `docs/aide/feature_catalogue.generated.*` and re-pin
    `tests/test_103_feature_catalogue.py`, which item 159 also edits. So the scan
    is left as it is.
  - The corpus → declaration direction of `rule_declaration_conflicts` stays
    geometric-only too. On the shipped tree it has nothing to find for the
    intensity corpus: `intensity` declares 16, and all three intensity failure
    cases expect only `intensity`. An intensity case naming an unregistered rule
    is now reported by the matrix (AC8).
  - The scan's docstrings say what they cannot see. No artifact renders this,
    since the only artifact value the scan fed no longer reads it.
- **A5: the phrase set for AC11/AC12.** The forbidden set is
  `("complete, always", "complete-always", "always complete", "yes, always")`.
  Matching is case-insensitive and runs after every run of whitespace, including
  newlines and indentation, collapses to one space. The 2026-09-16 grep found
  none of these phrases under `src/segfacet/` or in `docs/aide/*.generated.*`,
  so AC11 holds today without a production edit. The set covers the phrasings
  the two retired sources actually used (`roadmap.md:919–920`,
  `progress.md:967–968`). It does not try to catch paraphrase.
- **A6: the roadmap hand-back is a dated trail line, not a new inbox entry.** The
  item-146 `defect` entry (2026-09-04) already carries this claim and is ticked
  `→ item 156`. The builder adds an indented trail line under it, dated
  2026-09-16 or the date of the build. The line records that item 156 did not
  fix it and hands both rows to the next roadmap revision, with the two
  measurements given in the Description. A new entry about an old one would
  split the claim from its history.
- **A7: `progress.md` is not hand-edited.** Status changes go through the
  `aide progress` verbs only. The D4 deliverable bullet for item 156 already
  describes this item, so no deliverable prose is added or duplicated. A
  duplicated bullet raises an `aide check` warning class, which reds
  `test_146`/`test_150`.
- **A8 (engine 1.52.1, re-checked 1.59.0):** a tree-wide scan test that reads every file under a
  directory is not declared under **Asserts against**, following item 155's
  AC12 precedent. Listing `src/segfacet/**` or `docs/aide/*.generated.*` there
  would conflict under `aide check --queue` with the May-change globs of item
  157, which renames case ids inside those artifacts. The matched phrases are
  unrelated to case ids, so 157's edits cannot break AC11.

## Implementation Steps

1. **`src/segfacet/catalogue.py` — `rule_declaration_conflicts()`.** Inside the
   existing loop over `sorted(declarations.items())`, just after the "outside
   the key set" check, add the declaration → specification direction:
   - For each `mode in sorted(set(decl.modes) & known_modes)`, read
     `edges = {e.rule_id for e in SPECIFICATION[mode].intended_rules}`.
   - If `rule_id not in edges`, append one message naming the rule and the mode
     (form per A3).
   - Read `SPECIFICATION` through `_failure_modes_module`, as the function
     already does.
   - Update the docstring's bullet list with the new direction.
   - Correct the module docstring passage (`catalogue.py:52-58`) that says
     declared modes are "never" checked in the reverse direction.
2. **`src/segfacet/catalogue.py` — the scan's docstrings.** In
   `_scan_synth_rule_mode_map` and `scan_synth_rule_mode_map`, state that the
   scan matches geometric `Expectation(...)` literals only and cannot see the
   intensity corpus's `_RecipeEntry` cases. Name its two remaining consumers
   (mechanism C of `build_catalogue`, and the corpus → declaration direction of
   `rule_declaration_conflicts`). Name `traceability.build_matrix()` as the
   reader of both manifests for unregistered designations. Add the same
   limitation to mechanism C's description in the module docstring
   (`catalogue.py:30-34`).
3. **`src/segfacet/traceability.py` — `build_matrix()`.**
   - Move the loading of both manifests (`manifest_cases_all`) above the
     `unregistered_designated` computation.
   - Derive `unregistered_designated` as the sorted rule ids found in any
     case's `expected_rule_ids` or `expected_firing`, minus `registered_rule_ids`.
   - Remove the `corpus_map = scan_synth_rule_mode_map()` line and the
     `scan_synth_rule_mode_map` import.
   - Update the item-149 comment (`traceability.py:580-584`) and the module
     docstring (`:50-59`, "The scan is still read, for
     `corpus_designated_unregistered_rule_ids` only") to say the field is read
     from both committed manifests.
   - Do not touch `_NOTE`, any serialiser, or `SCHEMA_VERSION`. The rendered
     output must stay byte-identical (AC14).
4. **Regenerate to confirm, do not commit a change.** Run
   `.venv/bin/python -m segfacet.traceability --json <scratch>/m.json --md <scratch>/m.md`
   and compare both files with the committed ones. A difference means a rendered
   value moved, which is out of scope: stop and hand back.
5. **Reconcile the stale fixture** in `tests/test_138_traceability_matrix.py`
   (the test-writer does this; see Testing Strategy).
6. **No production edit for Seam 3.** AC11 already holds. The new test module
   pins it.
7. **`docs/aide/insights.md` — the hand-back (A6).** Under the item-146
   `defect` entry dated 2026-09-04, which starts "item 146's first `proposed`
   mode retired the "mode → rule is complete, always" contract", append one
   indented, dated trail line. It says:
   - item 156 does not edit `roadmap.md`, and the two "**Yes, always**" rows
     (`roadmap.md:919`, `:920`) are handed to the next roadmap revision;
   - the measurements, with commit and date: `mode_to_rule complete=False` with
     holes at exactly the `proposed` modes; `rule_to_mode complete=True`,
     `holes=()`, against row 920's "four rules sit here today";
   - the revision should describe both directions as *scored*, with a
     `proposed` mode as an expected hole.

   Never reword or re-tick the entry.
8. **Record the out-of-scope finding** as one new `knowledge` line in
   `insights.md`: the insight's `(1, 2, 5)` control stopped being fully silent
   after item 150 made mode 5 `proposed`, because proposed-drift fires first. Do
   this only if the finding is not already captured.

## Authorised paths

**May change:**

- `src/segfacet/catalogue.py` — the new declaration → specification direction in `rule_declaration_conflicts`, and the scan and module docstrings
- `src/segfacet/traceability.py` — `build_matrix` derives `corpus_designated_unregistered_rule_ids` from both manifests; module docstring and comment
- `tests/test_156_conformance_seams.py` — new module for AC1–AC13
- `tests/test_138_traceability_matrix.py` — the `matrix_unregistered_designated_rule` fixture (`:349-362`) re-pointed from the scan to the geometric manifest loader

**Asserts against:**

- `docs/aide/traceability_matrix.generated.json` — AC14, byte-compared by the existing `test_149::test_ac20_fresh_matches_committed_byte_for_byte`
- `docs/aide/traceability_matrix.generated.md` — AC14, same test

## Testing Strategy

**New module: `tests/test_156_conformance_seams.py`**, with one focused test per
AC. Resolve the repo root with `Path(__file__).resolve().parents[1]`.

- **AC1** builds both pair sets from live sources: `iter_rule_declarations()`
  and `SPECIFICATION`. It asserts equality and shows the two set differences in
  the failure message. Never hand-type a pair.
- **AC2–AC6** use `monkeypatch.setattr(rule, "mode_declaration",
  dataclasses.replace(original, modes=...))` on `heuristics.rule._RULES[<id>]`.
  `modes` must be strictly ascending, or `RuleModeDeclaration` raises. Take the
  baseline before patching. AC2 and AC6 compare set differences and counts.
  AC3 and AC4 use `any(...)` over the conflicts, requiring both tokens in one
  message. For AC3 and AC4, check each token as a whole word: use
  `re.search(r"\b5\b", msg)` so that `15` cannot satisfy `5`.
- **AC5, AC7–AC10, AC13** call `build_matrix()`, which is slow because it
  builds the catalogue and runs every corpus case. Build the unpatched matrix
  once in a module-scoped fixture for AC7 and AC13. The patched variants each
  build their own.
- **AC8/AC9** patch the loader on the module object with
  `monkeypatch.setattr(intensity_module, "load_intensity_manifest", lambda *a, **k: patched)`,
  where `patched` is a `copy.deepcopy`. `measured_firing` reads the committed
  NIfTI files, not the manifest, so the conformance section still builds. For
  AC9, pick the target case with `synth.perturbation.corpus_case_kind(c) ==
  CASE_KIND_FAILURE` (item 155). Never select by case id, because item 157
  renames them.
- **AC11/AC12 — the phrase matcher.** Define it once in the module as
  `_complete_always_hits(text: str) -> list`. It lowercases the text, collapses
  `\s+` to one space, and returns each member of
  `_FORBIDDEN = ("complete, always", "complete-always", "always complete",
  "yes, always")` that occurs. AC11 walks `sorted((root / "src" /
  "segfacet").rglob("*.py"))` and `sorted((root / "docs" /
  "aide").glob("*.generated.*"))`, and asserts no file has hits, naming each
  offending file in the failure message. It also asserts that the glob matched
  at least one generated file and at least one `.py` file, so an empty walk
  cannot pass vacuously. AC12 is parametrised over the phrase set plus the
  upper-case and line-wrapped variants.
- **Adversarial / edge cases:**
  - a rule declaring a known mode *and* an unknown mode, e.g. `bounds` →
    `(1, 999)`: the unknown mode gets only the "outside" message, and mode 1
    (mirrored) gets none;
  - calling `rule_declaration_conflicts()` twice returns equal tuples;
  - after `monkeypatch.undo()`, `rule_declaration_conflicts()` equals the
    baseline;
  - a stub rule registered under `isolated_registry` that declares a proposed
    mode, e.g. 13, gets the new message naming the stub and mode 13.

**Existing tests to reconcile:**

- `tests/test_138_traceability_matrix.py::matrix_unregistered_designated_rule`
  (fixture, `:349-362`) patches `catalogue_module.scan_synth_rule_mode_map` to
  add `"boundary"`. After Step 3 the matrix no longer reads the scan, so
  `test_ac25_unregistered_designated_rule_id_is_reported_and_fails_completeness`
  would go red. Re-point the fixture: patch `segfacet.synth.corpus.load_manifest`
  with a deep copy that appends `"boundary"` to one failure case's
  `expected_rule_ids`. The test's two assertions (`"boundary"` is reported;
  `mode_to_rule.complete is False`) stay unchanged.

**Swept and found unaffected** (grep on 2026-09-16 for
`rule_declaration_conflicts(`, `specification_conflicts(`,
`scan_synth_rule_mode_map`, and `monkeypatch` of `SPECIFICATION`):

- Every perturbation test in `test_136`, `test_137`, `test_146` and `test_147`
  that calls `rule_declaration_conflicts()` asserts with `any(...)` or against
  a baseline taken on the same tree. None pins an exact count under a
  perturbation that also creates an unmirrored declaration.
- The shipped-tree `== ()` assertions stay true by AC1: `test_136:359`,
  `test_137:420`, `test_146:511`, `test_147:850`, `test_148:1094`.
- `test_137::test_adv_future_corpus_case_still_binds_analytic_declaration`
  patches the scan and reads only `rule_declaration_conflicts()`, which still
  reads the scan.
- `test_103` and `test_136`'s AC4 pair read `scan_synth_rule_mode_map()`
  directly. Its output is unchanged.
- Tests that monkeypatch `fm.SPECIFICATION` to a reduced map (`test_146:1132`)
  get no new message, because the new direction only considers modes inside the
  patched key set.

## Validation

The validator executes these steps. None needs a special environment.

1. **The conformance report is unchanged.** Regenerate to a scratch directory
   with `.venv/bin/python -m segfacet.traceability --json <scratch>/m.json --md <scratch>/m.md`,
   then `cmp` each file against its committed copy. Expected: identical.
2. **Replay the Seam 1 positive controls outside the suite.** Use a short script
   that swaps `reference_delta`'s declaration to `(1, 2, 3, 4, 6, 8)` and then
   to `(1, 2, 5)`, printing `catalogue.rule_declaration_conflicts()` each time.
   Record the printed message that names `reference_delta` with 6, and the one
   that names it with 5. Before this item, both calls printed `()` (measured
   2026-09-16, Description).
3. **Confirm the hand-back is recorded.** Run
   `python .aide/scripts/aide.py insights list` and confirm the dated trail line
   from Step 7 sits under the item-146 (2026-09-04) entry. Confirm
   `docs/aide/roadmap.md` is not in the branch diff (`aide scope`).
4. **Tree health.** `python .aide/scripts/aide.py check` reports no error, and
   no warning class that this branch's `insights.md` or spec edits introduce.

## Dependencies

- **Item 155** (✅) — `synth.perturbation.corpus_case_kind` and the manifest
  `kind` field. The AC9 test and the reconciled `test_138` fixture use them to
  pick a failure case without naming a case id.

**Downstream:** item 157 renames the corpus case ids that the committed
traceability artifacts carry. AC14 is met by an existing fresh-vs-committed
test, which 157 regenerates consistently. Nothing in this item selects a case
by id. Item 159 edits `test_136`/`test_146`/`test_147` checks that this item
leaves unchanged. Item 160 counts the three entries this item absorbs.

## Decisions & Trade-offs

- **D1: message wording (A3).** The new declaration → specification message
  reads `rule '<id>': declares §6 mode <m>, but SPECIFICATION[<m>].intended_rules
  carries no IntendedRule edge for it (edges: [<ids>]).` — deliberately using
  "declares" rather than "declared" so `traceability.build_matrix()`'s
  `_uncatalogued_mode_re` (`^rule '([^']+)': declared §6 mode \d+ is outside`)
  cannot match it (AC5).
- **D2: manifest field lookup in `traceability.build_matrix()`.** Both
  geometric and intensity cases are read uniformly via
  `case.get("expected_rule_ids", ())` and `case.get("expected_firing", ())`
  unioned per case, rather than branching on which corpus a case came from —
  a geometric case has no `expected_firing` key and an intensity case has no
  `expected_rule_ids` key, so `.get(..., ())` on the absent key is always
  empty and the union is exactly "whichever field this case actually
  carries." This matches AC7/AC8/AC9 without a corpus-name branch.
- **D3: `manifest_cases_all` loaded once.** Moved to the top of
  `build_matrix()` (before `corpus_designated_unregistered_rule_ids` is
  derived) and reused unchanged by the later `cases_by_mode` /
  `pipeline_detected_by_mode` computation, per Implementation Step 3 — no
  behavioural change there, only a hoisted, shared load.
- **D4: `scan_synth_rule_mode_map` import removed from `build_matrix()`.**
  The function no longer calls the scan at all; its other two callers
  (`catalogue.build_catalogue`'s mechanism C, and the corpus → declaration
  direction of `catalogue.rule_declaration_conflicts()`) are untouched and
  still geometric-only, per A4 — confirmed by AC10's monkeypatch of both
  `scan_synth_rule_mode_map` and `_scan_synth_rule_mode_map`.
- **Verification (Validation steps 1-3), measured 2026-09-16/17:**
  - Regenerating with `python -m segfacet.traceability --json/--md` to a
    scratch directory and `cmp`-ing against the committed
    `docs/aide/traceability_matrix.generated.{json,md}` shows **no
    difference** — both files are byte-identical, confirming AC14 and that
    none of the three fixes moves a rendered value.
  - Replaying the two Seam-1 controls outside the suite:
    `reference_delta` widened to `(1, 2, 3, 4, 6, 8)` prints exactly one new
    message naming mode 6 (`edges: ['coverage']`); widened to `(1, 2, 5)`
    prints exactly one message naming mode 5 (`edges: []`). Both are `()`
    before this item's change, matching the Description's measurement.
    `fragmentation` widened to `(1, 2, 4)` prints a message naming mode 2
    (`edges: ['bounds', 'reference_delta']`); `bounds` widened to `(999,)`
    prints exactly the one pre-existing "outside the key set" message, naming
    999 only.
  - `build_matrix()` on the shipped tree: `corpus_designated_unregistered_rule_ids
    == ()`; `mode_to_rule.holes == ('10', '11', '12', '13', '14', '5', '7')`,
    exactly the modes with `derive_status(...) == "proposed"` (AC13).
  - `python .aide/scripts/aide.py scope` reports only `src/segfacet/catalogue.py`
    and `src/segfacet/traceability.py` changed among the two May-change
    source paths.
  - The A6 hand-back is recorded as a dated (2026-09-17) trail line under the
    item-146 (2026-09-04) `insights.md` entry via
    `aide insights tick 42 --pointer "..."`; a second, new `knowledge` line
    (dated 2026-09-16) records the out-of-scope `(1, 2, 5)`-control finding
    from the Description (Step 8) — not previously captured verbatim.
  - `roadmap.md` and `progress.md` prose are untouched; `progress.md`'s only
    edit is the CLI-driven status flip to `in-progress` (A7).
