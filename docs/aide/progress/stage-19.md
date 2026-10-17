> Stage 19's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 19`, run on the main or queue branch, moves it back.

## Stage 19 — Generated Feature & Rule Catalogue + Steering Review (G7, G8) — ✅

**Goal.** Make the feature set reviewable, then review it. `FEATURE_CATALOG` in
`scripts/aide_status_report.py` is hand-maintained (9 groups / 41 entries, commented
*"keep in sync by hand"*) while a realised record has **185 distinct leaf paths**. Nothing
verifies they agree, and no document records which failure mode each feature serves.

**Deliverables.**

- ✅ Catalogue **generated** from the realised record shape + extractor docstrings, with
  columns for computation, units, scale sensitivity, targeted §6 mode, consuming rules,
  and a keep / retune / retire / unwired status. *(Item 103)*
- ✅ Drift test: every leaf path covered; CI fails on an undocumented feature.
  *(Item 104)*
- ✅ Golden-file decision table — one row per committed golden: what it asserts, keep or
  retire, what replaces it. Working assumption **retire most** (whole-record snapshots of
  a corpus Stage 21 replaces). Byte reproducibility is guarded by the independent
  intra-run `dest1 == dest2` determinism assertions, not by the goldens. *(Item 105)*
- ✅ Stage validation + verification-row closure. *(Item 106)*

**Acceptance.**

- [x] The catalogue is generated, not hand-written; the drift test fails on a deliberately
  undocumented feature (**G7**). *(The zero-argument `python -m segfacet.catalogue`
  regeneration leaves both committed artifacts byte-identical to their pre-call
  content. The count agreed by four independent surfaces is `N = 111`. The
  status report (`scripts/aide_status_report.py`, with `FEATURE_CATALOG` /
  `UNWIRED_EXTRACTORS` deleted per item 103) renders the generated catalogue
  with no manual post-editing and degrades to a placeholder when the artifact
  is hidden. Drift rehearsed at two strengths: (i) hermetic, in-suite —
  injecting one extra key into a real driver record through item 103's AC16
  seam makes both item 104's reporter and the shipped `strict=True` mechanism
  fail, naming the exact undocumented path, and the revert restores green; (ii)
  real-source, manual (item 106 Validation step 3, 2026-08-11) — inserting
  `"zzz_drift_probe": 0.0` into `feature_report.py`'s `geometry_to_dict()` made
  `test_ac8_direction1_clean_on_current_tree`,
  `test_ac12_real_strict_build_succeeds_on_current_tree` and
  `test_ac15_direction3_clean_on_current_tree` fail, naming
  `per_label.{label}.geometry.zzz_drift_probe`; `git checkout --` restored a
  clean, green tree. See item 106's spec, "### Real-source drift rehearsal".)*
- [x] Every feature carries a status and a named failure mode, or is marked `unwired`
  - **2026-09-03** → Re-measured 2026-09-03 on the committed docs/aide/feature_catalogue.generated.json after items 136-138: the artifact now holds 138 entries (not 111), and the 72-entry statused-but-mode-unmapped bucket (mode_evidence == rule_unmapped) is empty - 0 entries. Split: 86 entries carry no mode evidence, 52 carry some (48 name at least one failure mode); 12 are attributed through a rule's recorded mode-less declaration (rule_mode_less: intensity, intensity_reference_delta). Status split: 66 retune, 34 keep, 30 unwired, 8 retire. The bucket shrank first because items 110/120/124/131/132 added leaf paths and moved attributions (138 entries, 18 rule_unmapped measured 2026-09-02 while specifying item 136), then closed because item 137 dispositioned the four mode-less rules. Stage 20's honest-count item should quote this split, not the attestation's.
  (**G8**). *(Measured on the committed artifact, `N = 111`: every entry
  carries a status from `{keep, retune, retire, unwired}`. Three-way partition:
  **35 moded** (statused, `failure_modes` non-empty), **4 unwired**, **72
  statused-but-mode-unmapped** — this last bucket is a real shortfall against
  the criterion's literal wording (a path consumed only by a rule carrying no
  §6 mode mapping — `bounds`, `intensity`, `reference_delta`,
  `intensity_reference_delta` — gets `status == "keep"`, `failure_modes ==
  ()`, `mode_evidence == ("rule_unmapped",)`: statused, not `unwired`, names no
  mode), closed by Stage 20's traceability matrix. **Steering review (2026-07-28,
  item 106):** all 111 `keep`/`unwired` entries (54 `keep`, 57 `unwired` at the
  pre-override build) presented to the maintainer across a 12-group live
  walkthrough; result recorded in `src/segfacet/feature_docs.py::STATUS_OVERRIDES`
  — **66 `retune`, 8 `retire`** (the `keep` bucket is reduced to 33 and
  `unwired` to 4 accordingly; 37 entries confirmed to stay at derived status).
  A `retune`/`retire` status **records** the maintainer's judgment; it does not
  execute it — no threshold moved, no extractor deleted, no feature stopped
  being computed. **Stage 19 decides, Stage 21 executes** — this is item 105's
  golden-file retire dispositions (the 11 rows of `golden-decision-table.md`);
  the *feature* `retire`/`retune` calls this item recorded have no assigned
  executor yet and are not implied to be Stage 21's. All of the above is
  measured on in-package synthetic driver records and the committed artifact,
  never on real data. See item 106's spec, "### Stage-19 steering review".)*
  **Criterion reworded 2026-08-11:** the roadmap's G8 sentence now
  names this third state explicitly — *statused but mode-unmapped, with the
  consuming mode-less rule named* — so it is no longer unsatisfiable-as-written by
  the mechanism this stage shipped, and the 72-entry bucket is a recorded state
  rather than a shortfall. The substantive close stays **Stage 20**'s: map
  `bounds` / `intensity` / `reference_delta` / `intensity_reference_delta` to §6
  modes, or record that they target none. Note the *feature* `retune`/`retire`
  calls recorded above now have an assigned carrier: **Stage 27** (schema
  taxonomy) for the structural two-thirds of them.
- [x] The golden decision table is complete and signed off by the human reviewer.
  *(Signed off 2026-07-28: all 36 rows of `docs/aide/golden-decision-table.md`
  reviewed individually — 11 retire (the 9 corpus-golden whole-record
  snapshots plus, overturning the initial draft, the two report-formatting
  goldens `tests/golden/016_features_report.json`/`022_stage3_report.json`),
  25 keep. See item 105.)*
