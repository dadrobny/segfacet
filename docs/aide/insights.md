<!--
  AIDE insight inbox. Any role captures ONE line here, at any time, when it
  learns something true but out of scope for its task — by running
  `python .aide/scripts/aide.py insights add`, which writes the entry shape
  below — and returns to that task. The engine creates
  docs/aide/insights.md from this file, byte for byte, the first time
  `aide check`, `claim`, `queue start`, `insights list` or `insights add`
  finds it missing; nobody copies it by hand.
  The rules — what is captured, what is immutable, what each verb does — are
  conventions.md §1 → insights.md and `python .aide/scripts/aide.py insights
  -h`. This comment is the shapes; the aide-template line below it names
  the template version this inbox was created from.

  Entry:
    - [ ] <type> — <one line> *(<provenance>, YYYY-MM-DD, engine X.Y.Z)*
  The date is required; the provenance before it and the engine version
  after it are free-form and optional. Conventional provenance spellings:
    *(item 099, 2026-07-26)*           one item
    *(items 099-101, 2026-07-27)*      a finding that spans several
    *(queue-014, 2026-07-26)*          planning or spec-authoring, before any item
    *(2026-07-26)*                     no item or queue to name
    *(item 099, 2026-07-26, engine 1.22.0)*   with the engine it was observed under
  Types:
    knowledge  — true fact worth documenting
    defect     — something is wrong and needs a fix item
    gap        — something is missing and needs planning
    automation — a recurring manual/agent action that code could replace
    framework  — belongs to AIDE itself, not this project

  A triaged entry, ticked in place with a pointer:
    - [x] <type> — <one line> *(item NNN, YYYY-MM-DD, engine X.Y.Z)* → <where it landed>
  A status trail, appended under an entry after triage, newest last:
    - [x] framework — <the original claim, never touched> *(2026-08-20)*
      - **2026-08-20** → aide-loop issue #50
      - **2026-10-11** → resolved in engine 1.16.0
-->
<!-- aide-template: insights 2 -->
# Insight Inbox

_Entries below, newest last._

- [ ] gap — In the first spinelab VerSe20 review pass (2026-10-06) the reviewer called two sacralised or fully fused L5 levels a mode 2 (fused-vertebra-segments) tool error, while FACET treats transitional lumbosacral anatomy as a numbering variant (mode 11, sequence/transitional). Before Stage 16 scores modes 2 and 3 against the rl1 labels, decide whether these levels count as mode 2 positives, mode 11 cases or exclusions, since each choice moves the specificity figure *(Stage 16 scoping, 2026-10-12, 2026-10-12, engine 2.47.3)*
  - **2026-10-12** → owner decision: keep fused labels and fused vertebrae distinct. Fused vertebrae (congenital, surgical, sacralised) are still several vertebrae, and each one gets its own label; that is the segmentation tool's job. A fused label is a tool that did not separate vertebrae, always a tool error (mode 2). So a sacralised L5 is mode 2 when VerSe GT holds a separate lumbar vertebra where SPINEPS shows (part of) the sacrum; Stage 16 checks the GT for the two reviewed levels. Stays open for Stage 16
- [x] defect — src/segfacet/heuristics/coverage.py _find_entry_by_level_name has no caller (the live lookup is fov.py copy via derive_fov_coverage); dead code that kept coverage level_name attribution alive under the last-segment catalogue scan *(item 223, 2026-10-13, engine 2.47.3)* → item 237
- [x] defect — nit — tests/test_039_identity_ordering_alignment_perturbations.py:401 (test_ac11 docstring) and tests/test_040_synthetic_corpus.py:102 and :314 still credit relabel_swap detection to the item-132 traversal-ordered reference fit, but since item 210 the monotonicity check fits no curve and reads position along a label-free MST path. Item 227 corrected the matching production descriptions and left these test comments by maintainer decision. *(item 227, 2026-10-13, engine 2.47.3)* → item 237
- [ ] automation — tests/test_178_corpus_sheet.py AC7 ties docs/aide/corpus_sheet.png to a sha256 of tests/corpus/manifest.json plus fixtures, so every item that regenerates the manifest must also rerun segfacet.synth.corpus_sheet; three of four queue-030 manifest-regenerating specs missed it. Having segfacet.synth.corpus write the sheet in the same run would remove the step. *(queue-030, 2026-10-13, engine 2.47.3)*
- [ ] defect — minor — item 220 cites VerSe19 centroid-distance figures (12.542/32.695/11.082 mm) in collapsed_labels.py, default_config.yaml and the mode-13 mechanism as measured facts, but its Validation step 1 replay was not re-run in the build (recorded Unverified); the figures are the spec-time measurement at 2a1491d. Replay is slow because compute_centroid reloads the volume per label. *(item 220, 2026-10-13, engine 2.47.3)*
  - **2026-10-16** → owner decision 2026-10-16: queue in maintenance queue-032, paired with 2026-10-13-3619 as one VerSe19-probe item (VerSe19 is available locally)
- [ ] defect — minor — centroid_spacing missing_level (item 218) has no sacral/coccygeal exclusion unlike fused_label (A4); a gap touching S1/Cocc with a small or cropped sacral label (size ratio <= 1.5) may read > 1.5 and emit a false Missing level on real predictions; unmeasured, the A7 VerSe19 probe may not have covered label 25/26 gaps. *(item 218, 2026-10-13, engine 2.47.3)*
  - **2026-10-16** → owner decision 2026-10-16: queue in maintenance queue-032, paired with 2026-10-13-af10 as one VerSe19-probe item (VerSe19 is available locally)
- [ ] defect — nit — tests/test_103_feature_catalogue.py (lines ~84, 591, 1325-1349) and tests/test_136/137 comments still describe mechanism B as a last-path-segment match and allow a 'static-ambiguous' evidence tag no mechanism emits since item 223; the ambiguity test at ~1325 is now vacuous *(item 223, 2026-10-14, engine 2.47.3)*
- [ ] defect — minor — item 224's last-digit reason tolerance (tests/test_098_stray_components.py _assert_reason_matches) also covers hard-coded threshold literals in pinned reasons, so a +/-1-unit recalibration of the remove_level 1.5 ratio threshold is no longer caught by any snapshot (0.75 stays pinned by test_035 AC3 and 13.0 by test_129's config text); mask or exactly pin threshold clauses, or pin 1.5 directly *(item 224, 2026-10-14, engine 2.47.3)*
- [x] defect — nit — src/segfacet/failure_modes.py line 279 (item 191 correction note, module docstring) still says the mislabel ordering signal is judged against a reference curve fitted in S-sorted label order; since item 210 compute_monotonic_consistency fits no curve (same stale claim item 227 fixed in corpus.py and identity_ordering_alignment.py) *(item 227, 2026-10-16, engine 2.47.3)* → item 237
- [x] gap — Population held-out spline-offset statistics include vertebrae truncated by the FoV: a border-touching label keeps only part of its body in the scan, so its centroid shifts posteriorly and its offset inflates (sub-verse406_split-verse261 T10, 18.51 mm, gate-fac1). The shipped spline_offset max_offset_mm = 13.0 (interior-only p99 12.91 mm, item 123) was set by that value. Exclude border-touching (fov_truncation) labels from the reference's offset statistics, as terminal labels already are in reference/ingest.py, then re-derive the threshold. *(gate-fac1, 2026-10-16, engine 2.47.3)* → withdrawn 2026-10-16, premise wrong: the owner had read the wrong image. sub-verse406_split-verse261 T10 is a rare wedge vertebra with a minuscule, posterior-only body that lets its neighbours' bodies touch anteriorly, not an FoV-truncated label. It is an anatomical outlier to be ignored (gate-fac1). No exclusion of border-touching labels follows from this case.
- [x] defect — scripts/aide_status_report.py builds its stage and item model from progress.md alone and does not follow the progress/stage-N.md archive links aide progress archive (engine 2.50.0) writes, so once stages are archived the report omits every archived item (test_aide_status_report's item-026 assertion fails). Archiving the 19 eligible settled stages was tried and undone on 2026-10-16 for this reason. *(framework update 2.52.2, 2026-10-16, engine 2.52.2)* → item 236
- [x] gap — 32 tests in 11 files (stage-validation tests test_070, test_105, test_106, test_110, test_115, test_125, test_135, test_150, test_151, test_161, test_169) read a closed stage's section straight out of progress.md or roadmap.md, so aide progress archive breaks them all. Most pin the loop's own attestation state and are retirement candidates under the 2026-09-16 precedent, and any that check something real should be repointed to read the archive. Once that lands, run aide progress archive, which made 19 stages eligible on 2026-10-16. *(framework update 2.52.2, 2026-10-16, engine 2.52.2)* → item 236
