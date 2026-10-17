> Stage 31's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 31`, run on the main or queue branch, moves it back.

## Stage 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update (G7, G8) — ✅

**Goal.** Clear what item 150's re-organisation of the catalogue left behind before any mode
is refined against it: an eval harness still keyed by the pre-sign-off ids, a `vision.md`
§6 whose numbered list no longer matches the specification, open `insights.md` defects in
the surfaces Stage 32 edits, and an AIDE engine 15 minor versions behind (1.37.0 vs
1.52.1, measured 2026-09-15). **No failure mode's definition, rule or expected firing set
changes here.**

**Deliverables.**

- ✅ **D0** AIDE engine updated to the framework's current version as its own reviewed PR
  (process work, not an item), before this stage's queue is planned; the two open
  `framework` insights checked against it, and Stage 20's summary status restored to 🚧.
- ✅ **D1** `vision.md` §6 re-issued through `/aide-create-vision` (human-gated, not an
  item): principles plus a pointer to the specification, no numbered mode list, the new
  observability classes and the FOV-truncation condition named, the "two-descent" wording
  corrected. Human gate `gate-d024` approved 2026-09-16 at `7d800a2`; PR #77 merged 2026-09-17.
- ✅ **D2** The seed-conformance check (`vision_seed_titles` / `VISION_SEED_DISPOSITION` /
  `vision_seed_conflicts`) re-pointed or retired to follow the re-issue. *(Item 152)*
- ✅ **D3** The Stage-18/29 eval harness (`eval.per_mode`, `severity_ladder`,
  `per_mode_cohort`, schemas, pins) re-keyed off the retired `LEGACY_STAGE18_MODE_NAMES`
  map onto its own metric/operator names, with the specification's mode ids carried in a
  nullable `failure_mode` field derived live from `SPECIFICATION`/`CONDITIONS`; every
  ladder constant, baseline and coupling value carried over unchanged. *(Item 153)*
- ✅ **D3** Re-measures the cross-mode constants item 153 carried over unchanged; absorbs
  Stage 20's deferred mode-1 ladder-base deliverable; `MODE_ANCHOR_PATHS[1]` re-anchored;
  the false `rank(v) == v - 1` claim in `severity_ladder.py` corrected; resolves the four
  recorded-not-resolved disagreements from item 153's Description. *(Item 154)*
- ✅ **D4** A corpus case is a clean control, a condition case, or a failure case, never
  `failure_mode == 0` alone: `case_kind`/`corpus_case_kind` in `synth/perturbation.py`
  derive and read a closed three-value `kind` on every manifest case, both committed
  manifests regenerate carrying it, and every production consumer
  (`regression.verify_case`, `failure_modes._corpus_case_conflicts`,
  `traceability._build_conformance`) moves onto it — an AST scan confirms no comparison
  against zero is left. *(Item 155)*
- ✅ **D4** Three unclosed conformance seams in the specification checks: a rule
  declaring a known mode with no mirroring `IntendedRule` edge and no corpus case
  passes every check unreported, `catalogue.scan_synth_rule_mode_map` stays blind
  to the intensity corpus, and the retired "mode → rule complete, always" claim is
  handed back to the next roadmap revision with the measurement that refutes it.
  *(Item 156)*
- ✅ **D4** Drops the stale `modeN_` corpus case-id prefixes that no longer name
  the mode they carry after the item-150 re-keying, renaming the eight affected
  geometric case ids and updating every pin (manifests, generator, rule/synth/
  eval modules, both conformance artifacts) to match. *(Item 157)*
- ✅ **D5** Closes two blind spots in `tests/committed_artifact_guard.py`'s resolver:
  an arbitrary `parents[N]` chain and a name-carried root reached through two hops
  (a name assigned from another name's `.parent`) were both invisible to
  `iter_violations`, silently passing a comparison the guard is meant to catch.
  *(Item 158)*
- ✅ **D5** Per `docs/aide/queue/queue-021.md` item 159, the prerequisite test and
  import defects in the surfaces Stage 32 edits (dead `aide/queue-018` base-ref
  skips, committed-artifact guard gaps, eager NiBabel import in
  `segfacet/__init__.py`, tests still exercising the retired `"corpus"` tag);
  entries already fixed are ticked with a pointer. *(Item 159)*
- ✅ **D6** Insight triage: every open `defect` and `gap` entry at the stage's start ticked,
  re-homed with a pointer, or left open with a dated reason. *(Item 160)*
- ✅ **D7** Stage validation: full suite green, eval harness re-run from a clean tree with
  re-measured constants recorded here, triage counts recorded as measured numbers.
  *(Item 161)*

**Acceptance.**

- [x] The installed engine version equals the framework's at the time the stage's queue was *(AC2 verified 2026-09-17 in clone 6bf417d: clone's .aide/VERSION reads 1.52.1 (X); queue-021 planning commit 99520a9 (2026-09-16T17:20:06+01:00) resolved fresh by subject; on aide-loop, git log origin/main --before=<that date> -1 -- core/VERSION names 5e305c5 whose core/VERSION is 1.52.1, equal to X. Framework's current origin/main core/VERSION is 1.53.1 (informational, does not affect this criterion).)*
  planned, or the gap and its reason are recorded.
- [x] `vision.md` §6 names the specification as the catalogue and carries no numbered mode *(verified 2026-09-17 on aide/queue-021 after fix commit 0197190, superseding the not-attested note: the maintainer ruled the module prose in scope for Stage 31, and 0197190 rewrote it to cite failure_modes.SPECIFICATION with current ids (prose-only, AST-identical with docstrings stripped); item 161's prose scan now matches only failure_modes.py:117, which names v3 as history; pinned by test_161_stage31_validation.py::test_criterion2_no_module_attributes_a_numbered_mode_to_section6 and its adversarial companion; test_152 AC1-AC3/AC5 still pass; full suite 8767 passed, 63 skipped, 0 failed)*
  list, and no module under `src/segfacet/` asserts that it does (**G8**). *(not attested 2026-09-17, item 161: AC3/AC4 pass in clone 6bf417d (test_152_retire_vision_seed.py test_ac1/test_ac2/test_ac3/test_ac5, 4 passed), but AC5's prose scan under reading R2 (A4) counts 42 raw hits across 16 files of `§6 mode N` / `§6's numbered` under src/segfacet/ (excluding the one line naming v3 as history, 41 count against the zero threshold), so the count is non-zero and criterion 2 stays unticked per AC5.)*
- [x] No module or test under `src/segfacet/` or `tests/` references *(AC6-AC9 verified 2026-09-17 in clone 6bf417d: test_153_eval_harness_rekey.py test_ac1/test_ac2/test_ac5/test_ac17/test_ac20/test_ac21/test_ac26/test_ac27/test_ac30 pass (9 passed); test_154_ladder_remeasurement.py test_ac8/test_ac9/test_ac10 pass (3 passed); harness re-run via score_harness(run_severity_harness()) prints passed=True. Re-measured constants (segfacet.eval.severity_ladder, clone 6bf417d, replayed 2026-09-17): RECORDED_MARGINS displace inf, fragment inf, inject_islands 112.0, relabel_swap inf, remove_level inf, crop_at_border 0.3585, sequence_break inf, force_overlap 1.038; KNOWN_CROSS_MODE_COUPLINGS crop_at_border -> unanchored_foreground_fraction 2.79, force_overlap -> unanchored_foreground_fraction 0.9629; provenance corpus=geometric, base_params={levels: (L1,L2,L3,L4,L5), spacing: (1.0,1.0,1.0), curve_amplitude_mm: 6.0}, measured_on=2026-09-16.)*
  `LEGACY_STAGE18_MODE_NAMES` or keys a per-mode metric, ladder or cohort count by an id
  outside `failure_modes.SPECIFICATION`; the re-measured cross-mode constants are recorded
  with what they were measured on (**G7**).
- [x] No consumer distinguishes a clean control from a condition-only case by *(AC12 verified 2026-09-16: tree-wide AST scan (test_ac12_no_tree_wide_zero_comparison_of_failure_mode_remains, tests/test_155_corpus_case_kind.py) over every *.py under src/segfacet/ and tests/ returns zero violations of a failure_mode == 0 comparison outside case_kind's own body; full suite green (8511 passed, .venv/bin/python -m pytest -n auto).)*
  `failure_mode == 0` alone.
  - **2026-09-17** → AC10 replayed 2026-09-17 in clone 6bf417d: test_155_corpus_case_kind.py::test_ac12_no_tree_wide_zero_comparison_of_failure_mode_remains and every parametrisation of ::test_ac13_scan_detects_each_forbidden_shape pass (8 passed) — item 161 replay confirms the 2026-09-16 attestation.
- [x] Every open `defect` and `gap` insight present at the stage's start is ticked, *(AC11-AC13 verified 2026-09-17 in clone 6bf417d: test_160_insight_triage.py test_ac1_ through test_ac8_ parametrisations pass (125 passed). AC12 re-measured via aide insights list --trail (89 entries, 24 open): stage-start defect/gap entries: 29 -- ticked 18, re-homed 10, left open 1. in-queue: 6 -- ticked 2, re-homed 0, left open 4. Counts match item 160's recorded 18/10/1 and 2/0/4 exactly; re-homed pointer count (10) and left-open trail-line count (5 = 1 + 4) independently confirmed by grep over docs/aide/insights.md.)*
  re-homed with a pointer, or left open with a dated reason; the three counts are recorded
  here (**G7**).
