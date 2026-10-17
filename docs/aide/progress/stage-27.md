> Stage 27's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 27`, run on the main or queue branch, moves it back.

## Stage 27 — Feature Schema Taxonomy & Coordinate System (G8) — ✅

**Goal.** Give the feature record a deliberately designed structure instead of the current
grouping by *which extractor module happened to compute a field* — the single recurring
theme behind roughly two-thirds of item 106's 111-entry steering review verdicts. **This
stage designs the taxonomy rather than inheriting one**: the maintainer's scope × kind
framing is the starting proposal and the quality bar, and deviation is allowed where it is
justified in writing.

**Deliverables.**

- ✅ The taxonomy, written down with rationale, alternatives considered, and every deviation
  from the starting proposal justified — reviewed with the maintainer before migration (a
  human-checkpoint stage in the same sense Stage 19 was). *(Item 214)*
- ✅ The per-label migration applied: every identity copy merged onto `per_label.{label}.label` / `.level_name`, the per-label fields of `stage3`, `image_features` and `reference_delta` moved under `per_label.{label}.*`, the feature catalogue (`docs/aide/feature_catalogue.generated.md`) regenerated, its drift test (`tests/test_104_feature_catalogue_drift.py`) as the safety net. *(Item 215)*
- ✅ The migration applied, the feature catalogue
  (`docs/aide/feature_catalogue.generated.md`) regenerated, its drift test
  (`tests/test_104_feature_catalogue_drift.py`) as the safety net. *(Item 216)*
- ✅ Answers for the known instances: duplicated `label`/`level_name` identity fields across
  four containers; `stage3.*` / `image_features.*` parallel to `per_label.{label}.*`;
  image-axis-relative shape features (bbox/extent, `principal_axis`) awaiting a vertebra
  coordinate system; reference-delta hardcoded to `physical_volume_mm3`. *(Item 214)*
- ✅ **Maintenance** `test_155`'s tracked-shape scan: nested scopes reported once, walrus,
  `match` and `>= 1.0` shapes covered, value defaults let through. *(Item 209)*
- ✅ **Maintenance** The monotonicity check's reference curve made label-free and
  direction-robust. *(Item 210)*
- ✅ **Maintenance** `fused_label` judges the pair of adjacent spacings together.
  *(Item 211)*
- ✅ **Maintenance** `crop_at_border` re-authored as a true anterior crop. *(Item 212)*
- ✅ **Maintenance** The Windows CI leg runs a pinned OS-sensitive subset. *(Item 213)*
- ✅ Stage validation from a clean clone. *(Item 217)*

**Acceptance.**

- [x] The taxonomy is documented with its rationale and every deviation justified, and is
  signed off by the maintainer before migration (**G8**). *(Attested from the clean-clone replay of item 217, clone commit 18609089bf27bda29ba16112ca1997859bc39fb2 (fresh clone, own venv, CPython 3.11.15). AC6: gate list prints exactly one gate containing 'Stage 27 feature-record taxonomy sign-off', gate-0080, status Approved (2026-10-06) per progress.md, Decision cell 'Signed 2026-10-06 after review: one anatomical element order stored as case.sequence.order[] ... docs/feature-taxonomy.md @ 2364df4'. AC7: approval commit 00fe6f57259d8a642366d0dcb6c87725c00003f9 'docs: human gate-0080 approved' (2026-10-06T15:19:25+01:00) is an ancestor (git merge-base --is-ancestor exit 0) of the earliest feat(215) commit c09b07dc573c4b518c2cd3af10a3351ed1460697 (2026-10-06T16:08:55+01:00); the migration's first claim, the item 215 in-progress commit 54b1553, is dated 2026-10-06 as well, so the date alone cannot order them and the ancestry check does.)*
- [x] Every feature is addressable under it; no identity field is stored more than once. *(Attested from the clean-clone replay of item 217, clone commit 18609089bf27bda29ba16112ca1997859bc39fb2 (fresh clone, own venv, CPython 3.11.15). AC9: on the clean_control case report (bundled reference, --intensity; 149 leaf paths) exactly 1 leaf path ends 'label' (per_label.{label}.label) and exactly 1 ends 'level_name' (per_label.{label}.level_name). AC10: the catalogue's path set has 154 paths and equals the 153 kept/moved new paths of the 165-row table (80 kept, 73 moved, 12 merged) plus case.sequence.order[] (154), the one stored path with no table row, by the signed note's Deviation 11; the maintainer ruled on 2026-10-06 that it is counted. AC11: of the report's 149 leaf paths 148 lie among the table's kept/moved new paths, the difference against the table alone is exactly {case.sequence.order[]}, and with that path added the difference set has size 0; all 20 report-only `reference_delta.{label}.features.<f>.<s>` new paths are among the leaves. 'Every feature' was read as every leaf of a real bundled-reference report, the 20 report-only reference-delta paths included (maintainer decision, 2026-10-05). Neighbour-pair identity leaf paths the report carries, measured and not counted: pairs.overlaps[] only (clean_control has no overlaps). Label-reference leaf paths, listed and not counted: case.sequence.order[], per_label.{label}.components.component_contacts[].neighbour_label, per_label.{label}.neighbourhood.window_labels[].)*
- [x] The regenerated catalogue and the drift test agree; no rule's behaviour changes on the
  corpus except where a retune is explicitly authorised. *(Attested from the clean-clone replay of item 217, clone commit 18609089bf27bda29ba16112ca1997859bc39fb2 (fresh clone, own venv, CPython 3.11.15), against B 3be6c381e8c986754703d80a32e56cb7e68102d5 (progress(aide): item 214 -> done; separate worktree, own venv). AC12: tests/test_104_feature_catalogue_drift.py 53 passed, no skips; every generated artifact (AC3) regenerates byte-for-byte and the bundled synthetic reference matches under the committed-artifact comparator (AC4). AC13: tests/test_163_specificity_ratchet.py 24 passed; build_matrix().conformance drives 18 cases (14 geometric, 4 intensity) equal to the two manifests' case ids, 0 with agrees False. A retune was explicitly authorised: the maintainer's 2026-10-05 decision to collapse the two adjacent-pair spacing arrays into one in anatomical order, signed in the design note's Deviations at gate-0080 and carried by item 216 as D1, widened by D11, the record-wide anatomical element order signed at gate-0080 on 2026-10-06 ('one anatomical element order stored as case.sequence.order[]'). AC14: no case's findings changed on either corpus: all 18 cases give identical Finding.to_dict() lists in order, reasons included, in B and in the clone. AC15: the touched cases are sequence_break alone, which is also the only case where any kept/moved row (152 compared, features_version excluded) resolves differently, in 37 rows (per-label offsets, orientations and neighbourhood rows, the curvature scalars and arrays, the four spacing statistics, and u_values[] by element order only). Spacing family on sequence_break, base then clone: survivor [33.4940, 32.6952, 33.8724, 36.8400] -> [134.1605, 33.4940, 32.6952, 33.8724]; mean 34.2254 -> 58.5555; cv 0.04582 -> 0.74549; deviations [-0.7314, -1.5302, -0.3530, 2.6146] -> [75.6050, -25.0615, -25.8603, -24.6831]; outlier_pairs [] -> [[T13, L1]]. AC16: the maintainer ruled on 2026-10-06 that the reference-backed change on sequence_break is covered by the gate-0080 sign-off, within D1 widened by D11. clean_control (462 lines) and displace (378 lines) segfacet_report.txt are byte-identical across the two trees; sequence_break (379 lines) differs in exactly the listed 11 base-only and 11 clone-only lines, no others: the spline_offset_mm out-of-range finding moves from label 21 (0.1513) to label 20 (0.0038), and the distribution distances for labels 20-23 go 3.70/3.90/4.07/3.96 -> 3.47/3.89/4.06/4.40. Recorded (rule_id, labels) multisets for sequence_break, 118 findings in both trees: identical except reference_delta, base 20:6 21:8 22:7 23:7 against clone 20:7 21:7 22:7 23:7; the other rules are bounds 4 on each of 20-23, intensity on 22/23/28, mislabel (20,28), sequence (28), intensity_reference_delta 20:17 21:15 22:18 23:19, in both. Insight 2026-10-06-f318 is the reason the bundled VerSe19 reference sits out of step with the new order until it is rebuilt.)*
