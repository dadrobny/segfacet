<!-- aide-template: item 3 -->
# Item 226 — Two owner-decided retirements

> **Created:** 2026-10-13 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-030.md`](../queue/queue-030.md) · Item 226
> **Objectives:** G4, G7
> **Suggested branch:** `aide/226-two-owner-decided-retirements`

---

## Description

This item carries out two retirements the owner decided on 2026-10-09. It also corrects every line of live text that the two retirements would otherwise make false.

**1. `sagittal_projection` (insight `2026-10-09-2c9f`).**
`src/segfacet/features/sagittal_projection.py` (item 021) renders a matplotlib sagittal plot of centroids and spline. Nothing reaches it except its own test, `tests/test_021_sagittal_projection.py`. This item deletes both files. Three other places describe the module as current, and this item corrects them:

- The status-report generator `scripts/aide_status_report.py` prints a QC-images placeholder. It says the images appear "once cases have been run and their sagittal projections (roadmap item 021) are written out". The placeholder is reworded so it no longer names a retired deliverable. The generator's `--qc-images <dir>` option is unchanged.
- Stage 3 of `progress.md` has the ✅ deliverable bullet "Optional sagittal projection of centroids + spline for the human report. *(Item 021)*". It gains the suffix "; retired by owner decision 2026-10-09" through `aide progress reword --item 021`. The bullet stays ✅: item 021 shipped, and the reword records that it was later retired.
- `docs/aide/status/index.html` is a snapshot that `/aide-status-report` regenerates. It is **not** regenerated here, because regenerating it would rewrite unrelated live status. The next run of that skill picks up the new placeholder.

No generated catalogue or traceability document lists the module (Assumption A3), so nothing there is regenerated.

**2. The CI `scope-check` job (insight `2026-10-09-ed9b`).**
`.github/workflows/ci.yml`'s `scope-check` job fires only on a pull request whose head is an `aide/NNN-` claim branch. This repo runs `[git] mode = "auto-merge"`, so no claim branch ever becomes a PR and the job always resolves to nothing. A green `item scope check` therefore means "skipped". This item:

- deletes the job and the comment block above it;
- deletes the shipped tests that pin the job's shape;
- rewrites the two `CLAUDE.md` passages that describe the job. They will say that the per-item scope gate is the in-loop validator running `aide scope`. The owner approved this edit (Assumption A1).
- updates the two other live texts that name the job: `REVIEW.md`'s authorised-paths bullet and the docstring of `tests/test_aide_check_no_errors.py`.

**Not in scope:**
- The framework verb `aide scope`, `.claude/agents/validator.md` and every other `.aide/**` / `.claude/**` file. They are framework-owned and unchanged.
- Provenance documents that name either retired artefact: item specs 017, 021, 072, 107, 117, 119 and 178, queue-002, queue-016, `docs/aide/roadmap.md` and the insight archives. They stay as written.
- matplotlib stays in the `dev` extra and in `constraints.txt`, because `src/segfacet/synth/corpus_sheet.py` still uses it.
- The `CLAUDE.md` heading "Branching, and what it means for the scope check" stays. Line 333 cross-references it, and the in-loop `aide scope` run is still a scope check.

## Acceptance Criteria

- [ ] **AC1: The module is gone.** `importlib.util.find_spec("segfacet.features.sagittal_projection")` returns `None`.
- [ ] **AC2: Nothing imports it.** An `ast` walk over every `*.py` file under `src/`, `tests/` and `scripts/` finds no `Import` or `ImportFrom` node naming `segfacet.features.sagittal_projection`. That covers both `from segfacet.features import sagittal_projection` and any dotted import of the module.
- [ ] **AC3: The QC placeholder names no retired deliverable.** `asr.render_html(model)` is the status-report generator's own render, called with a model built without QC images. In its output, the `<p class="placeholder">` paragraph that contains `--qc-images` contains neither `sagittal` (case-insensitive) nor `021`.
- [ ] **AC4: The workflow has no `scope-check` job.** The `jobs` mapping of `yaml.safe_load` over `.github/workflows/ci.yml` has no key `scope-check`.
- [ ] **AC5: No CI step runs the scope verb.** No step in any job of `.github/workflows/ci.yml` has a `run` value containing `aide.py scope`.
- [ ] **AC6: `CLAUDE.md` no longer describes the job.** `CLAUDE.md`'s text contains neither `scope-check` nor `item scope check`.
- [ ] **AC7: `CLAUDE.md` names the in-loop scope gate.** In `CLAUDE.md`, the section running from the `## Branching` heading to the next `## ` heading has at least one paragraph that contains both `aide scope` and `validator`.
- [ ] **AC8: `REVIEW.md` no longer names the job.** `REVIEW.md`'s text does not contain `scope-check`.

## Assumptions

- **A1 (owner approval, 2026-10-12): the `CLAUDE.md` edit is approved for exactly two hunks.** The owner gave this approval during the `/aide-spec-queue 030` session of 2026-10-12. It authorises the builder to edit `CLAUDE.md` in these two places and nowhere else. The builder may treat the edit as already approved and make it without handing back. The change reaches `main` through the queue-030 PR, which is the reviewed PR that `CLAUDE.md`'s Branching section requires for process files. The two hunks are:
  1. The bullet that begins "**One project-specific note on `aide scope`:**", lines 205–207 at the base of this item.
  2. The Branching section's "consequence for CI" text. It runs from the paragraph that begins "**The consequence for CI.**" through the end of the following paragraph, which ends "…switching to `pr` mode is one of the things that would resolve it." These are lines 455–470 at the base of this item.

  An edit to any other part of `CLAUDE.md`, the line-414 heading included, is outside this approval and needs the usual hand-back.
- **A2 (pinned against item 224): `test_107` AC13's three names survive item 224.** `tests/test_107_item_scope_check.py` AC13 asserts that three functions are defined in `tests/test_098_stray_components.py`: `test_ac12_hand_set_fragmentation_findings_match_frozen_snapshot`, `test_ac13_reference_derived_excess_finding_matches_frozen_snapshot` and `test_ac15_golden_verdict_and_findings_unchanged`. Item 224 edits test_098 and keeps these names, so this item edits test_107's AC11 block only and leaves AC13 as it is. This records an expectation about a sibling, not an ordering, so 224 is deliberately not a Dependency. If 224 lands with a renamed function, test_107 AC13 goes red on whichever branch merges second. That is 224's reconciliation, not this item's.
- **A3 (measured 2026-10-12): only its own test reaches the module.** A grep for `sagittal_projection` under `src/`, `tests/`, `scripts/` and `.github/` matched only the module and `tests/test_021_sagittal_projection.py`. None of the generated documents mentions it: `docs/aide/feature_catalogue.generated.*`, `traceability_matrix.generated.*`, `failure_modes.generated.*`, `rules.generated.md` and `golden_evidence.generated.json`. The catalogue is built from feature records, not from modules (`src/segfacet/catalogue.py`). So the queue's clause "generated docs that listed it are regenerated" is met with nothing to regenerate, and their drift tests are unaffected. The one generated file that mentions the deliverable is `docs/aide/status/index.html`, and the owner chose to leave it for the next `/aide-status-report` run.
- **A4 (engine 2.47.3): what `aide progress reword --item` does.** It rewrites the first-line prose of the one deliverable bullet whose trailing marker names the item, whatever that bullet's status. It keeps the icon and the `*(Item 021)*` marker and writes only `progress.md`. It refuses text that is empty, starts with a status icon or ends with an item reference. `progress.md` is authorised for every item, so the reword needs no Authorised-paths entry.
- **A5 (measured 2026-10-12): which shipped tests pin the job.** Two tests in `tests/test_107_item_scope_check.py` assert on it: `test_ac11_ci_workflow_runs_the_checker_on_pull_requests` (`.aide/scripts/aide.py scope` in `ci.yml`) and `test_ac11_ci_workflow_scope_job_uses_the_pr_base_ref` (`base_ref`). Five tests in `tests/test_117_scope_verb_swap.py` assert on it: AC5–AC9, reached through `_scope_check_job_text`. The other `ci.yml` readers do not depend on the job: test_095, test_113, test_133 and test_213. One caveat applies to test_113's `_job_comment_and_body`. It attaches to a job every comment and blank line directly above it, so the comment block above `scope-check` has to go with the job, or it attaches itself to the `test` job.
- **A6 (measured 2026-10-12): the Windows subset is unaffected.** Neither `tests/test_021_sagittal_projection.py` nor any file this item adds is in `ci.yml`'s `WINDOWS_TESTS`. test_107 still trips `as_posix` and test_117 still trips `subprocess` after their edits, so `tests/test_213_windows_ci_subset.py`'s classifier and the list stay in agreement.

## Implementation Steps

No dependency is added. No production module other than the deleted one changes.

1. **Delete** `src/segfacet/features/sagittal_projection.py` and `tests/test_021_sagittal_projection.py` with `git rm`.
2. **Reword the placeholder** in `scripts/aide_status_report.py` `_render_highlights_section`, in the `qc_block` text. Keep the leading `<strong>Extension point.</strong>`, because `tests/test_aide_status_report.py` asserts on it three times. Keep the `--qc-images &lt;dir&gt;` pointer. Drop the clause naming sagittal projections and item 021. Something like "QC overlay images populate here when the generator is pointed at a folder of them with `--qc-images <dir>`" is enough.
3. **Reword the progress bullet:** `python .aide/scripts/aide.py progress reword --item 021 --text "Optional sagittal projection of centroids + spline for the human report; retired by owner decision 2026-10-09."` The verb commits `progress.md` itself.
4. **Delete the CI job** in `.github/workflows/ci.yml`. Remove the comment block that opens with "# Item 107 built this as a diff-based scope check" and the whole `scope-check:` job beneath it, down to the blank line before `  test:` (Assumption A5 explains why the comment has to go too). Leave every other job and the top-of-file comment as they are.
5. **Reconcile the tests that pin the job** (A5):
   - In `tests/test_107_item_scope_check.py`, delete both `test_ac11_*` functions and their section banner. In the module docstring, replace the AC11 clause with a dated note: AC11 was retired with the `scope-check` job (item 226, 2026-10-13).
   - In `tests/test_117_scope_verb_swap.py`, delete `test_ac5_*` through `test_ac9_*`, `_scope_check_job_text`, `_JOB_KEY_RE`, `_CI_YML` and the "AC5-AC9" section banner. Amend the docstring's "Covers AC1-AC3, AC5-AC9, …" line to name what still covers, with a dated note that AC5–AC9 were retired with the job (item 226). `re` stays imported, because AC18 uses it.
6. **Edit `CLAUDE.md`**, inside Assumption A1's two hunks only:
   - **Hunk 1:** state that `aide scope` runs in the item loop, at the validator's step 3, and that CI runs no scope check. Point to "Branching" below. Name no CI job.
   - **Hunk 2:** replace the "consequence for CI" text with a paragraph saying three things. (a) The per-item scope gate is the in-loop validator running `aide scope` on the claim branch before `aide merge`. (b) CI runs no scope check: under `auto-merge` no claim branch becomes a PR, so the job item 107 built and item 117 retargeted matched nothing, and it was retired by owner decision 2026-10-09 (item 226). (c) Switching `[git] mode` to `pr` would make a CI scope job meaningful again, and it is in git history. Neither `scope-check` nor `item scope check` may appear in the new text (AC6).
7. **Edit `REVIEW.md`**, in the authorised-paths bullet at line 60: drop the clause "under `auto-merge` the CI `scope-check` job is no signal, so". Say instead that CI runs no scope check, so the in-loop validator's `aide scope` and a reviewer reading the queue PR are the only enforcement. Keep the bullet's remaining sentences. `REVIEW.md` is project-owned and not in CLAUDE.md's PR-gated list. `AGENTS.md` restates nothing about scope, so it needs no change.
8. **Edit the docstring of `tests/test_aide_check_no_errors.py`.** Replace "Nothing else in CI plays this role: the `scope-check` job only runs `aide scope`." with a sentence that names no job, for example: "Nothing else in CI plays this role: the workflow invokes no `aide` verb directly, so this test is how `aide check` runs there." That is true of `ci.yml` once step 4 has removed the only `aide.py` invocation in it. The test body does not change.

## Authorised paths

**May change:**

- `src/segfacet/features/sagittal_projection.py` — deleted (step 1)
- `tests/test_021_sagittal_projection.py` — deleted with the module (step 1)
- `scripts/aide_status_report.py` — the QC placeholder reworded (step 2)
- `.github/workflows/ci.yml` — the `scope-check` job and its comment block removed (step 4)
- `tests/test_107_item_scope_check.py` — the AC11 tests and docstring clause retired (step 5)
- `tests/test_117_scope_verb_swap.py` — AC5–AC9 and their helpers retired (step 5)
- `CLAUDE.md` — Assumption A1's two hunks only, owner-approved (step 6)
- `REVIEW.md` — the authorised-paths bullet (step 7)
- `tests/test_aide_check_no_errors.py` — docstring only (step 8)
- `tests/test_aide_status_report.py` — AC3's test, beside the existing `render_html` tests that already build `_model()`
- `tests/test_226_owner_decided_retirements.py` — the tests for AC1, AC2 and AC4–AC8

**Asserts against:**

None outside the files above. AC3 asserts against the final state of `scripts/aide_status_report.py`, and AC4–AC8 against the final state of `ci.yml`, `CLAUDE.md` and `REVIEW.md`, all of which this item writes.

## Testing Strategy

Two test modules carry the AC tests:

- **`tests/test_226_owner_decided_retirements.py`** (new) holds AC1, AC2 and AC4–AC8.
  - Read `ci.yml` with `yaml.safe_load`, as `tests/test_213_windows_ci_subset.py` does.
  - Read `CLAUDE.md` and `REVIEW.md` with `read_text(encoding="utf-8")`.
  - Do AC2's walk with `ast`.
  - Write the module so it trips none of test_213's five OS signals: no `subprocess`, no `read_bytes`, no `newline=`, no `.as_posix`/`os.sep`, no `aide_check_result`. If it does trip one, add it to `WINDOWS_TESTS` in `ci.yml`, which this item may change; otherwise test_213 fails.
- **`tests/test_aide_status_report.py`** gains AC3's test. It builds the model with that module's existing `_model()`, calls `asr.render_html`, isolates the `<p class="placeholder">` paragraph that contains `--qc-images`, and asserts on that paragraph only. The rest of the page renders the real `progress.md`, whose reworded item-021 bullet legitimately says "sagittal".

**Adversarial cases:**

- `import-from-package-form`: AC2's sweep helper, run on the planted source `from segfacet.features import sagittal_projection`, reports it. Guards against a sweep that matches only `ImportFrom.module` and so misses the module when it is imported as a name from its package.
- `renamed-job`: AC5's step scan, run on a planted parsed workflow whose job is keyed `scope-gate` but whose step runs `python .aide/scripts/aide.py scope 042`, reports it. Guards against AC4 being met by renaming the job while CI keeps running the verb.

**Existing tests to reconcile** (step 5; A5):

- `tests/test_107_item_scope_check.py::test_ac11_ci_workflow_runs_the_checker_on_pull_requests`: delete.
- `tests/test_107_item_scope_check.py::test_ac11_ci_workflow_scope_job_uses_the_pr_base_ref`: delete.
- `tests/test_117_scope_verb_swap.py::test_ac5_ci_resolves_an_item_number_with_the_anchored_expression`, `test_ac6_ci_invokes_the_scope_verb_with_an_origin_base`, `test_ac7_ci_always_passes_a_positional_item_number`, `test_ac8_ci_keeps_full_history` and `test_ac9_ci_pins_a_python_with_tomllib`: delete, together with `_scope_check_job_text`, `_JOB_KEY_RE` and `_CI_YML`.
- `tests/test_021_sagittal_projection.py`: the whole module is deleted (step 1).
- `tests/test_aide_status_report.py`: its three `"Extension point" in …` asserts stay green as long as step 2 keeps that prefix.
- `tests/test_113_ci_numpy_matrix_scope.py::_job_comment_and_body`: no edit needed, as long as step 4 removes the comment block with the job (A5).

## Validation

The validator runs these and reads the output, beyond the suite:

1. `git grep -n "sagittal_projection" -- src scripts .github` prints nothing. Under `tests/`, only `tests/test_226_owner_decided_retirements.py` may name it, as AC1's and AC2's subject; AC2's import walk covers the rest of `tests/`.
2. `git grep -n -e "scope-check" -e "item scope check" -- .github CLAUDE.md REVIEW.md` prints nothing.
3. The `CLAUDE.md` diff against the base touches only Assumption A1's two hunks. Any other changed line fails the item: it is outside the owner's approval.
4. `progress.md`'s Stage 3 bullet for item 021 reads "✅ Optional sagittal projection of centroids + spline for the human report; retired by owner decision 2026-10-09. *(Item 021)*", and Stage 3's header is still ✅.

## Dependencies

None.

**Downstream:** none. Item 224's edit to `tests/test_098_stray_components.py` is recorded as Assumption A2, not as an ordering.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether a CI scope check comes back if the repo ever moves to `[git] mode = "pr"`. The owner's 2026-10-09 decision retires the job under `auto-merge` only. A switch of mode is its own decision, and the retired job can be restored from git history then.
- No AC covers the docstring of `tests/test_aide_check_no_errors.py` (step 8). It is prose inside a test, nothing reads it, and the validator reads the diff.
