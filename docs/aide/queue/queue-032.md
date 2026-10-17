<!-- aide-template: queue 1 -->
# FACET — Work Queue 032

> **Created:** 2026-10-17
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).
> **Maintenance queue** (roadmap Stage 34) at the queue-030 boundary. It runs
> **before** [`queue-031.md`](queue-031.md) (Stage 35) by owner decision
> (2026-10-17), even though it is numbered after it. `aide claim` defaults to
> the lowest-numbered open queue, which is 031, so this queue is claimed with
> `--queue 032` (`/aide-run-queue 032`).

---

## Scope of this queue

This queue batches the open `defect`, `gap` and `automation` entries in
`insights.md` that were written after queue 030 was planned, grouped as the
owner grouped them on 2026-10-17
(`.aide/conventions.md` §1 → `insights-maintenance-queue.md`). It holds five
items. One open entry, `2026-10-12-76ac`, is passed over: it is a Stage 16
scoring decision, not a repair of shipped work, and it stays open until
Stage 16 is planned.

**Prioritisation.** Item 236 goes first. It makes the stage archive safe and
then runs it, and the other items' diffs are smaller to review once 19 stage
sections have left `progress.md` and `roadmap.md`. Items 237–240 are
independent of each other and can be claimed in any order after it.

**Build posture (`prototype`).** Every item fixes a recorded defect or gap in
a shipped script, shipped code or a shipped test, or adds the automation an
`automation` entry asks for. None is preparatory.

**Numbering.** Continues at the next free integer: **236–240**.

---

## Work items

### Item 236: Stage archive made safe, then run

`aide progress archive` (engine 2.50.0) moves each settled stage's section to
`progress/stage-N.md` and its roadmap section to `roadmap/stage-N.md`. Two
things in this repository break when it runs, and the archive was tried and
undone on 2026-10-16 for them. First, `scripts/aide_status_report.py` builds
its stage and item model from `progress.md` alone, so every archived item
drops out of the report (insight `2026-10-16-50cf`). Make it follow the
summary row's archive link. Second, tests read a closed stage's section
straight out of `progress.md` or `roadmap.md` (insight `2026-10-16-c3e4`).
A probe on 2026-10-17 archived the 19 eligible stages in a `git worktree` of
`main` at `5b80c1d` and ran the suite there: 33 failed, 8121 passed and 73
skipped. The failures sit in the entry's 11 files (`test_070`, `test_105`,
`test_106`, `test_110`, `test_115`, `test_125`, `test_135`, `test_150`,
`test_151`, `test_161`, `test_169`) and in
`test_aide_status_report::test_build_report_model_on_real_docs`. The probe did
not archive Stages 0, 1, 32 and 33 (below), so the spec re-probes with those
archived too: tests over Stages 32 and 33, such as `test_203`, `test_204`
and `test_168`, are not yet measured. Most of those tests pin the loop's own attestation state and are
retired under the 2026-09-16 precedent (`CLAUDE.md`, "Updating the
framework", step 4). A test that checks something real is repointed to read
the archive file.

Four more stages stay unarchived for a different reason: an item whose
bullets sit in two stages holds both back. Item 006 has a bullet in Stage 0
and one in Stage 1. Item 204, Stage 33's validation, also carries Stage 32's
D3 bullet. Settle each so one stage holds the item's only bullet, and record
where the other stage's deliverable went.

The archive verb refuses on a claim branch, so it runs on `aide/queue-032`
once this item has merged: `python .aide/scripts/aide.py progress archive`.
The spec names that step and the stages it should archive. *Testable:* the
status report built from an archived tree lists every item the unarchived
tree lists, item 026 included; with every eligible stage archived in a
scratch tree, the suite passes; no test reads a section of an archived
stage from `progress.md` or `roadmap.md`; Stages 0, 1, 32 and 33 are no
longer refused for an item with a bullet outside them.

### Item 237: Dead code and stale comments left by items 210, 223 and 227

Four leftovers, each recorded with its location. Delete
`_find_entry_by_level_name` in `src/segfacet/heuristics/coverage.py`, which
has no caller; the live lookup is `fov.py`'s copy, reached through
`derive_fov_coverage` (insight `2026-10-13-aeec`). Correct the comments that
still credit `relabel_swap` detection to item 132's traversal-ordered
reference fit, in the `test_ac11` docstring of
`tests/test_039_identity_ordering_alignment_perturbations.py` and at
`tests/test_040_synthetic_corpus.py` lines ~102 and ~314. Since item 210 the
monotonicity check fits no curve and reads position along a label-free MST
path (insight `2026-10-13-cc62`). Correct the same claim in the item-191
correction note of `src/segfacet/failure_modes.py`'s module docstring, line
~279 (insight `2026-10-16-50ce`). In `tests/test_103_feature_catalogue.py`
(lines ~84, ~591, ~1325–1349) and the comments of `tests/test_136*` and
`tests/test_137*`, stop describing mechanism B as a last-path-segment match.
Stop allowing the `static-ambiguous` evidence tag, which no mechanism has
emitted since item 223. Make the ambiguity test at ~1325 assert something,
or retire it (insight `2026-10-14-94ec`). *Testable:* nothing imports or
calls `_find_entry_by_level_name`; no test or module docstring credits
`relabel_swap` detection to a fitted reference curve; test_103 no longer
accepts `static-ambiguous`, and its ambiguity test fails when attribution
regresses or is gone; the suite and every generated-doc drift test pass.

### Item 238: Threshold literals in pinned reasons compared exactly

Item 224 gave `tests/test_098_stray_components.py`'s `_assert_reason_matches`
a last-digit tolerance on rendered numbers. The tolerance also covers the
threshold literals in the pinned reasons, so a ±1-unit recalibration of
`remove_level`'s 1.5 ratio threshold is no longer caught by any snapshot.
The 0.75 threshold stays pinned by test_035 AC3, and 13.0 by test_129's
config text (insight `2026-10-14-1dd0`). Compare threshold clauses exactly,
whether by masking them out of the tolerant comparison or by pinning 1.5
directly; the spec chooses. *Testable:* a reason whose measured value
differs in its last digit still passes; a reason whose 1.5 threshold reads
1.4 or 1.6 fails; a changed verdict or a changed finding still fails.

### Item 239: The corpus sheet regenerated with the manifest

`tests/test_178_corpus_sheet.py` AC7 ties `docs/aide/corpus_sheet.png` to a
sha256 of `tests/corpus/manifest.json` plus its fixtures. So every item that
regenerates the manifest must also rerun `segfacet.synth.corpus_sheet`, and
three of queue 030's four manifest-regenerating specs missed that step
(insight `2026-10-13-62d2`). Have the `segfacet.synth.corpus` regeneration
write the sheet in the same run, and remove the separate step from the
prose that names it. Checked 2026-10-17: `corpus_sheet` imports matplotlib
only inside its rendering functions, and matplotlib is a `dev` extra, not a
core dependency (`pyproject.toml`). So `corpus` may call the sheet only where
matplotlib is importable. Where it is not, it must say so, and never write a
manifest whose sheet is silently stale. *Testable:* one corpus regeneration
writes a manifest and a sheet that test_178 AC7 accepts together; with
matplotlib absent the regeneration still writes the manifest and reports that
the sheet was not written; importing `segfacet.synth.corpus` does not import
matplotlib.

### Item 240: VerSe19 probes behind items 218 and 220

Two measurements that items 218 and 220 rely on were not re-run in the
build. Item 220 cites VerSe19 centroid-distance figures (12.542, 32.695 and
11.082 mm) as measured facts in `collapsed_labels.py`, `default_config.yaml`
and the mode-13 mechanism. They are the spec-time measurement at `2a1491d`,
and the Validation step 1 replay was recorded Unverified (insight
`2026-10-13-af10`). Item 218's `centroid_spacing` `missing_level` check has no
sacral or coccygeal exclusion, unlike `fused_label` (its A4). A gap touching
S1 or Cocc beside a small or cropped sacral label (size ratio ≤ 1.5) may
read above 1.5 and emit a false missing-level finding on a real prediction.
Item 218's A7 probe may not have covered gaps at labels 25 or 26 (insight
`2026-10-13-3619`). Replay item 220's figures on VerSe19 at the current
commit, and correct each citation the replay moves. Measure
`missing_level`'s firing on VerSe19 gaps touching labels 25 and 26, and add
the exclusion if any fires falsely. The af10 entry notes that the replay is
slow because `compute_centroid` reloads the volume once per label. Speeding
that up is in scope only if the replay cannot otherwise finish. *Testable:*
each cited figure matches a replay recorded with its commit, or is corrected
to it; a synthetic map with a cropped sacral label beside a sacral gap fires
no missing-level finding if the exclusion is added; the VerSe19-dependent
checks skip cleanly without the data; every corpus case's measured firing
equals its expected set.
