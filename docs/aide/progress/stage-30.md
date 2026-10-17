> Stage 30's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 30`, run on the main or queue branch, moves it back.

## Stage 30 — Failure-Mode Specification: the §6 catalogue as an authored source (G2, G7, G8) — ✅

> **Read after item 150's sign-off** *(roadmap v3.1, 2026-09-15; full note in
> [`roadmap.md`](../roadmap.md))*. D6's review re-organised the catalogue into sixteen modes
> in a one-tier hierarchy plus the FOV-truncation condition
> ([`items/150-maintainer-sign-off-of-the-specification.md`](../items/150-maintainer-sign-off-of-the-specification.md)).
> Item 151 validates the acceptance below against these readings, wording unchanged:
> criterion 2's `mode6_crop_at_border` is the condition's fixture (`failure_mode` 0,
> still `{border, mislabel}`); criterion 3's "mode 8" is **mode 15**; criterion 5's
> "ninth mode" is **mode 16**, and "the eight seed names equal §6's list" is replaced by
> `failure_modes.vision_seed_conflicts()` returning `()` over `VISION_SEED_DISPOSITION`.
> Seed-to-mode mapping: seed 1 → retired; 2 → 1 (2, 3 split from it); 3 → 4; 4 → 8;
> 5 → 6; 6 → condition; 7 → 9 (10, 11 split from it); 8 → 15; D3's ninth → 16; D3's
> collapsed or duplicated → 13 and 14. Follow-ups are Stages 31 and 32's, not item 151's.

**Goal.** Queue-019 produced three defects of one class in four items — a factual claim
about the failure modes authored as prose, shipped into a committed artifact, and accepted
by a check that tested the claim's shape rather than its truth — because no document
defines the modes: they exist as five partial sources (`vision.md` §6's list,
`FAILURE_MODE_NAMES`, `MODE_ANCHOR_PATHS`, the `Expectation` literals, `MODE_RUNGS`) that
the generated matrix cross-checks without being able to adjudicate. This stage authors the
specification [`vision.md`](../vision.md) v3 §6 describes — one authored source per mode,
from which every generated artifact becomes a conformance report — collapses the five
sources onto it, and closes with a maintainer sign-off that gates the remainder of Stage
20. It writes no new rules and adds no corpus cases beyond what the ninth mode needs.

**Deliverables.**

- ✅ **D0** Synthetic corpus S-axis stacking corrected before anything is measured
  (`build_clean_spine` advances caudally like real VerSe input), every committed corpus
  value and both reference artifacts regenerated, expected firing sets recorded only
  after it. Carried defect recorded 2026-08-31 (spec 131). *(Item 143)*
- ✅ **D1** The specification module (one frozen declaration per mode with vision §6's
  fields; `implemented`/`validated` derived, `proposed`/`specified` authored) and its
  byte-reproducible, LF-pinned rendering `docs/aide/failure_modes.generated.{md,json}`.
  *(Item 144)*
- ✅ **D2** The eight hypothesised modes specified with discriminators; gate `gate-0fdd`'s decisions
  encoded as data — `mode6_crop_at_border` expects `{border, mislabel}` with reason,
  evidence rungs authored per mode ↔ rule edge with the mode's rung derived, mode 8
  structurally-unobservable, mode 7's single-descent cap recorded. *(Item 145)*
- ✅ **D3** The ninth mode, implausible tissue under a label, entered through the lifecycle
  (`intensity` / `intensity_reference_delta` declare it; the intensity manifest gains
  `failure_mode` and expected firing fields; the intensity sibling of
  `pipeline_findings` built in `synth/regression.py`), plus the catalogue's first
  `proposed` entry — collapsed or duplicated label set, candidate feature
  `stage3_unavailable`, no rule (carried defect, spec 129). *(Item 146)*
- ✅ **D4** The five partial sources collapsed onto the specification; `Expectation` and
  `RuleModeDeclaration` checked against it in both directions; the three declaration-seam
  defects (the `"corpus"` tag membership test, the untyped `evidence`/`modes`, the
  corpus-to-declaration blindness; `insights.md`, spec 136) closed by replacement. *(Item 147)*
- ✅ **D4** The rule-granular attribution (`insights.md`, spec 138) given a per-path form
  the catalogue renders, so a rule's bookkeeping read paths are no longer painted with the
  mode its signal paths serve. *(Item 148)*
- ✅ **D5** The traceability `build_matrix` (spec 138) re-pointed at the specification as primary: derived
  status, per-edge rungs, expected beside measured firing per corpus case with agreement
  scored, metric anchor path and rule read paths as two labelled columns; the
  `build_matrix` fixture discipline set and the `no-float-leaf` guard ground added. The
  exercise columns stay Stage 20's. *(Item 149)*
- ✅ **D6** Maintainer sign-off of `failure_modes.generated.md`, entry by entry, with date
  and outcome recorded in the specification module's docstring. Until recorded, the
  remainder of Stage 20 is not queued. *(Item 150)*
- ✅ **D7** Stage validation: both artifacts regenerated from a clean tree, every corpus
  case across both corpora driven and expected equals measured confirmed, derived
  statuses checked against live state, the per-status / per-rung count recorded here as a
  measured number. *(Item 151)*

**Acceptance.**

- [x] Every mode in the specification carries every schema field, a status from the *(AC17/AC18 in-suite (dataclass fields, vocabularies, independent status recomputation all match); AC19/AC20/AC21 replayed in clone 6464b2e: hand-set status='validated' on _MODE_2 rejected by ModeSpec.__post_init__ (names 'ModeSpec 2'); overlap.py declaring modes=(5,15) makes specification_conflicts() name mode 5 (authored 'proposed' but derives 'implemented'); hand-edited mode 16 status_derived='implemented' in the committed JSON fails test_144's AC19 and test_150's AC11 (names only JSON pointer /modes/15/status_derived, not the mode literally -- logged as a finding, since AC19/AC20 already establish the naming clause); all three mutations restored and cmp-confirmed against the working checkout; derived status counts over 16 modes: validated 6, implemented 3, specified 0, proposed 7; validated through a pipeline-detected case 5, through a reconstructed record only 1)*
  four-state vocabulary and a provenance; `implemented` and `validated` are derived from
  live state, and a hand-set status that disagrees with the registry or the corpus fails
  a test naming the mode (**G8**).
  - **2026-09-20** → Item 167 (2026-09-20): mode 3 gains fragmentation's neighbour_contact detector, moving it from implemented to validated. Re-measured live: derived status counts over 16 modes: validated 7, implemented 2, specified 0, proposed 7; validated through a pipeline-detected case 6, through a reconstructed record only 1.
  - **2026-09-28** → Item 188 (2026-09-28): coverage re-homed from mode 6 to mode 10; mode 6 derives specified with no rule, mode 10 implemented at needs-real-data. Re-measured live: derived status counts over 16 modes: validated 6, implemented 3, specified 1, proposed 6; validated through a pipeline-detected case 5, through a reconstructed record only 1.
  - **2026-09-28** → Item 192 (2026-09-28): sequence serves modes 9-11 by sub-type; mode 11 derives implemented at needs-real-data, mode 10 gains a second edge. Re-measured live: derived status counts over 16 modes: validated 6, implemented 4, specified 1, proposed 5; validated through a pipeline-detected case 5, through a reconstructed record only 1.
  - **2026-09-28** → Item 193 (2026-09-28): reference_delta and intensity_reference_delta made mode-less; mode 8 derives specified with no rule, mode 16 keeps its intensity edge. Re-measured live: derived status counts over 16 modes: validated 6, implemented 3, specified 2, proposed 5; validated through a pipeline-detected case 5, through a reconstructed record only 1.
  - **2026-09-28** → Item 195 (2026-09-28): force_overlap removed; mode 15 keeps the overlap rule's declaration and carries no corpus case, so it derives implemented. Re-measured live: derived status counts over 16 modes: validated 5, implemented 4, specified 2, proposed 5; validated through a pipeline-detected case 5, through a reconstructed record only 0.
  - **2026-09-30** → Item 205 (2026-09-30): mode 2/3 boundary re-drawn at gate-51da; split and neighbour_contact's stray_contact moved to mode 2, which derives validated. Re-measured live: derived status counts over 16 modes: validated 6, implemented 3, specified 2, proposed 5; validated through a pipeline-detected case 6, through a reconstructed record only 0.
  - **2026-10-13** → Item 220 (2026-10-13): mode 13 gains collapsed_labels' needs-real-data edge and derives implemented. Re-measured live: derived status counts over 16 modes: validated 6, implemented 4, specified 2, proposed 4; validated through a pipeline-detected case 6, through a reconstructed record only 0.
  - **2026-10-13** → Item 218 (2026-10-13): mode 6 gains centroid_spacing's missing_level edge (synthetic-demonstrable) and derives validated. Re-measured live: derived status counts over 16 modes: validated 7, implemented 4, specified 1, proposed 4; validated through a pipeline-detected case 7, through a reconstructed record only 0.
- [x] For every corpus case across both committed corpora, the measured firing set equals *(AC8 measured all 15 manifest cases (11 geometric + 4 intensity) in clone 6464b2e: every measured firing set equals expected; matrix.conformance.agree_count=15, unspecified_cases=(), disagreements=(); AC10/AC11 mode6_crop_at_border expects {border, mislabel} with reason, measured label 22 touches_anterior=True, offset_mm=17.507 (>13.0 max), is_terminal=False; clean_control label 22 touches_anterior=False. Reading D2 (clean, condition-less cases scored against the empty set) and D3 (mode6_crop_at_border is the fov_truncation condition's fixture, no longer a Stage 20 gate-3 co-detection claim))*
  the specification's expected firing set, and `mode6_crop_at_border` expects
  `{border, mislabel}` with a recorded reason (**G2**).
- [x] Every mode ↔ rule edge carries an authored evidence rung and every mode's rung is *(AC12 all 17 IntendedRule edges carry an evidence_rung in EVIDENCE_RUNGS; AC13 derive_mode_rung matches an independent per-mode recomputation and the committed rendering/matrix row for all 16 modes, weakening a mode's strongest edge changes its derived rung; AC14 10 analytic edges (bounds+reference_delta on modes 1-4, reference_delta on mode 8, intensity_reference_delta on mode 16), measured live in clone 6464b2e, none rung synthetic-demonstrable; AC15/AC16 mode 15 (reading D3: criterion 3's 'mode 8') derives structurally-unobservable, mechanism states the single-channel invariant, mode8_force_overlap: extract_feature_record overlaps=[], pipeline_findings=[], reconstructed_findings=['overlap'], manifest detection=reconstructed_record; derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7; per-edge rung counts over 17 edges: synthetic-demonstrable 5, needs-real-data 11, structurally-unobservable 1)*
  derived from its edges; the analytic-only edges are rendered as such, and mode 8's rung
  names the single-channel mechanism (**G2**).
  - **2026-09-20** → Item 167 (2026-09-20): mode 3's new fragmentation/neighbour_contact edge is synthetic-demonstrable, moving its derived rung from needs-real-data/none to synthetic-demonstrable and adding one edge. Re-measured live: derived mode rung counts: synthetic-demonstrable 6, needs-real-data 2, structurally-unobservable 1, none 7; per-edge rung counts over 18 edges: synthetic-demonstrable 6, needs-real-data 11, structurally-unobservable 1.
  - **2026-09-28** → Item 188 (2026-09-28): coverage re-homed from mode 6 to mode 10; mode 6 derives specified with no rule, mode 10 implemented at needs-real-data. Re-measured live: derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7; per-edge rung counts over 18 edges: synthetic-demonstrable 5, needs-real-data 12, structurally-unobservable 1.
  - **2026-09-28** → Item 192 (2026-09-28): sequence serves modes 9-11 by sub-type; mode 11 derives implemented at needs-real-data, mode 10 gains a second edge. Re-measured live: derived mode rung counts: synthetic-demonstrable 5, needs-real-data 4, structurally-unobservable 1, none 6; per-edge rung counts over 20 edges: synthetic-demonstrable 5, needs-real-data 14, structurally-unobservable 1.
  - **2026-09-28** → Item 193 (2026-09-28): reference_delta and intensity_reference_delta made mode-less; mode 8 derives specified with no rule, mode 16 keeps its intensity edge. Re-measured live: derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7; per-edge rung counts over 14 edges: synthetic-demonstrable 5, needs-real-data 8, structurally-unobservable 1.
  - **2026-09-28** → Item 194 (2026-09-28): bounds no longer declares mode 1 and mode 1 loses its bounds edge, so mode 1 is attributed only as the catch-all. Re-measured live: derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7; per-edge rung counts over 13 edges: synthetic-demonstrable 5, needs-real-data 7, structurally-unobservable 1.
  - **2026-09-28** → Item 195 (2026-09-28): force_overlap removed. Mode 15 keeps its overlap edge at structurally-unobservable and carries no corpus case; the AC15/AC16 force_overlap evidence above is history. test_151's AC16 now asserts that mode 15 carries no corpus case and that no committed geometric case yields an overlap through the pipeline.
  - **2026-09-30** → Item 207 (2026-09-30): mode 2 gains fused_label's synthetic-demonstrable edge, adding one edge. Re-measured live: derived mode rung counts: synthetic-demonstrable 5, needs-real-data 3, structurally-unobservable 1, none 7; per-edge rung counts over 14 edges: synthetic-demonstrable 6, needs-real-data 7, structurally-unobservable 1.
  - **2026-09-30** → Item 208 (2026-09-30): mode 3 gains split_fragment's synthetic-demonstrable edge, moving its derived rung from needs-real-data to synthetic-demonstrable and adding one edge. Re-measured live: derived mode rung counts: synthetic-demonstrable 6, needs-real-data 2, structurally-unobservable 1, none 7; per-edge rung counts over 15 edges: synthetic-demonstrable 7, needs-real-data 7, structurally-unobservable 1.
  - **2026-10-13** → Item 220 (2026-10-13): mode 13 gains collapsed_labels' needs-real-data edge and derives implemented. Re-measured live: derived mode rung counts: synthetic-demonstrable 6, needs-real-data 3, structurally-unobservable 1, none 6; per-edge rung counts over 16 edges: synthetic-demonstrable 7, needs-real-data 8, structurally-unobservable 1.
  - **2026-10-13** → Item 218 (2026-10-13): mode 6 gains centroid_spacing's missing_level edge (synthetic-demonstrable) and derives validated. Re-measured live: derived mode rung counts: synthetic-demonstrable 7, needs-real-data 3, structurally-unobservable 1, none 5; per-edge rung counts over 17 edges: synthetic-demonstrable 8, needs-real-data 8, structurally-unobservable 1.
  - **2026-10-13** → Item 219 (2026-10-13): mode 9 loses sequence's swap/shift edge and mode 10 its skip edge, both needs-real-data. Re-measured live: derived mode rung counts: synthetic-demonstrable 7, needs-real-data 3, structurally-unobservable 1, none 5; per-edge rung counts over 15 edges: synthetic-demonstrable 8, needs-real-data 6, structurally-unobservable 1.
- [x] `failure_modes.generated.{md,json}` and the traceability matrix regenerate *(AC2/AC7 clean-clone regeneration in clone 6464b2e: failure_modes.generated.{json,md} and traceability_matrix.generated.{json,md} cmp exit 0 against committed copies, a second independent regeneration cmp-identical to the first; feature_catalogue.generated.md cmp-identical, .json accepted by assert_matches_committed_artifact and also byte-identical; AC3 matrix primary_source == src/segfacet/failure_modes.py, resolves to the loaded module, per-mode title/authored_status/edge_rungs match SPECIFICATION, row key set == set(SPECIFICATION); AC4 JSON/Markdown notes name the module, modes/conditions lists equal specification_to_dict() live; AC5 matrix header carries both 'Stage-18 metric anchor paths' and 'Rule signal read paths', anchor_paths equals MODE_ANCHOR_PATHS, columns differ for modes 6/8/9/16; AC6 every stage18-metric-anchor candidate renders under the anchor label only, no rule read path under it. Reading D4 (matrix renders the two labelled columns; the specification's own rendering labels anchors only and its 'primary source' reading is via its note + specification_to_dict() equality))*
  byte-identically from a clean tree, name the specification as their primary source, and
  render the metric anchor path and the rule's read paths as separately labelled columns.
- [x] The ninth mode (implausible tissue) is present at `implemented` or `validated`, with *(AC22 mode 16 name='Implausible tissue under a label', observability=needs-paired-scan, derive_status=validated; AC23 both intensity and intensity_reference_delta declare mode 16 in iter_rule_declarations() and SPECIFICATION[16].intended_rules; AC24 intensity manifest cases carry failure_mode/expected_firing (implausible_metal/implausible_soft_tissue/degenerate_uniform at 16 with ['intensity'], clean_hu at 0 with []); AC25 FAILURE_MODE_NAMES == dict(failure_mode_names()), ast shows no Dict literal binding; AC26 no module-level MODE_RUNGS/ModeRung/RUNGS assignment under src/segfacet (ast-parsed), traceability has no MODE_RUNGS attribute; AC27 vision_seed_conflicts() == (), literal seed-title equality measured 2/8 (modes 4 and 8: 'Semantic mislabelling (wrong vertebra identification)', 'Overlapping segments'). Reading D3 (mode 16 is criterion 5's 'ninth mode'; vision_seed_conflicts() replaces the literal eight-seed-name clause, whose count is recorded but not pinned))*
  `intensity` and `intensity_reference_delta` declaring it and the intensity corpus cases
  carrying expected firing sets; `FAILURE_MODE_NAMES` and `MODE_RUNGS` are derived from or
  replaced by the specification, and the eight seed names equal `vision.md` §6's list
  (**G8**).
- [x] The specification's rendering is signed off by the maintainer, with the date and *(AC28 failure_modes.py docstring 'Signed off: 2026-09-15' matches the progress.md gate row whose Gate cell contains 'Stage 30 failure-mode specification sign-off', Status date 2026-09-15, kind approved, parsed via .aide/scripts/aide.py's human_gates(); AC29 outcome sentence's 'sixteen entries' equals len(SPECIFICATION) == 16)*
  outcome recorded in the module (**G8**).
- [x] `build_clean_spine` stacks labels caudally along +S like real VerSe input, every *(item 143 validator round 3: full suite green (6273 passed, 60 environment-gated skips, 0 failed) in 4 foreground chunks 2026-09-03; AC1/AC2 verified via tests/test_143_s_axis_correction.py (build_clean_spine advances caudally along +S for all spans/spacings); AC11-AC13 verified via committed-artifact/determinism tests (corpus manifests, both reference artifacts, feature_catalogue/traceability_matrix/golden_evidence regenerated and matched); AC9 verified via test_098_stray_components.py (no rule firing set moved, corpus predates the specification module which item 144+ builds))*
  - **2026-09-15** → Item 151 re-verified against the built specification (insights.md, item 143, 2026-09-03): AC30 build_clean_spine world-S centroid strictly decreasing in ascending label order (si_axis resolved from the affine); AC31 both corpora regenerated in clone 6464b2e -- manifests accepted by assert_matches_committed_artifact and byte-identical, all 12+5 fixtures byte-identical, path sets equal; AC32 reference_default.json regenerated, accepted by assert_matches_committed_artifact and also byte-identical; AC33 test_128_reference_verse_v1_integrity.py passes (2 passed) in the clone, docs/corpus-s-axis-correction.md's reference_verse_v1.json row reads 'unmoved' with its no-synthetic-input reason (reading D7: not rebuilt from the real cohort); AC34 git rev-list HEAD -- src/segfacet/failure_modes.py (8 commits, correction 513f50b resolved fresh by subject) equals git rev-list 513f50b..HEAD -- same path (8 commits) -- every commit touching the specification module postdates the S-axis correction. All three original clauses hold; 'no expected firing set in the specification predates it' is now independently established (AC8's agreement plus AC34's ancestry), which item 143 could not measure before the specification module existed
  committed corpus value and both reference artifacts were regenerated after the
  correction, and no expected firing set in the specification predates it (**G7**).
