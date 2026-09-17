<!-- aide-template: item 1 -->
# Item 152 — Retire the vision §6 seed-conformance check

> **Created:** 2026-09-16 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update
> **Queue:** [`../queue/queue-021.md`](../queue/queue-021.md) · Item 152
> **Objectives:** G8
> **Suggested branch:** `aide/152-retire-the-vision-6-seed`

---

## Description

Roadmap Stage 31 D2. Vision v4 (PR #77, branch `docs/vision-v4-section-6`, human
gate 6 approved 2026-09-16 at commit `7d800a2`) re-issues `vision.md` §6 as
principles plus a pointer to `segfacet.failure_modes.SPECIFICATION`, with **no
numbered mode list**. Three symbols in `src/segfacet/failure_modes.py` exist only
to conform against that list, and against v4 they fail: `vision_seed_titles()`
parses §6's numbered lines and returns `{}`, so `vision_seed_conflicts()` reports
all eight `VISION_SEED_DISPOSITION` titles as absent. Measured 2026-09-16 on the
v4 branch: nine tests red (`docs/aide/insights.md`, knowledge entry dated
2026-09-16 beginning "removing `vision.md` §6's numbered seed list").

This item:

1. **Brings v4 onto the item branch** by merging commit
   `7d800a20c8cf779f2ef1b93d5ba65d48652e2b2e` (see A4).
2. **Retires `vision_seed_titles()` and `vision_seed_conflicts()`.** No module
   under `src/segfacet/` reads `vision.md` any more.
3. **Keeps `VISION_SEED_DISPOSITION` as frozen provenance**: the literal record of
   what each of v3 §6's eight titles became (`mode:<id>`, `condition:<id>` or
   `retired`), with no live parse behind it. Its value does not change.
4. **Rewrites the prose that describes §6 as a seed list**: the module docstring,
   the two section comments, `_NOTE`, and the generated Markdown's
   `## Vision section 6 seed disposition` section. The rewritten prose calls §6
   the principles document that points at this module, and the disposition map
   the provenance of its v3 list.
5. **Reconciles the ten tests** that call the retired functions or parse §6's
   numbered form. Each is re-pointed at the provenance shape or retired together
   with the function it tests. The ten are the nine the insight names plus
   `test_151::test_adv_ac27_unresolvable_disposition_is_flagged`, which passes
   against v4 only because the check fails anyway. It stops working once the
   function is removed.
6. **Regenerates** `docs/aide/failure_modes.generated.{json,md}`.

**Not in scope:** no `ModeSpec` or `ConditionSpec` field changes. No mode, rule,
corpus case or `expected_firing` is added, removed or moved. `SCHEMA_VERSION`
stays `"2.1"`. `vision.md` and `roadmap.md` are not edited by any commit of this
item: `vision.md` changes on the branch only through the merge of the
gate-approved commit. `traceability.py`'s own `_NOTE` and the
"mode → rule complete, always" wording belong to item 156. The eval harness's
`LEGACY_STAGE18_MODE_NAMES` belongs to item 153. The historical records under
`docs/aide/items/` are not rewritten.

## Acceptance Criteria

The heading line of §6 (below) is the line in `docs/aide/vision.md` that starts
with `## 6.`. §6 is the text from that line up to the next line that starts with
`## ` followed by a digit, or up to the end of the file.

- [ ] **AC1: §6 carries no numbered list.** The number of lines in §6 of
  `docs/aide/vision.md` that match `^\d+\.\s` equals 0.
  *(closes Stage 31 criterion 2)*
- [ ] **AC2: §6 names the specification as the catalogue.** §6 of
  `docs/aide/vision.md` contains the substring
  `segfacet.failure_modes.SPECIFICATION`. *(closes Stage 31 criterion 2)*
- [ ] **AC3: no production module reads `vision.md`.** The set of `.py` files
  under `src/segfacet/`, `failure_modes.py` included, that hold a non-docstring
  `str` constant containing `vision.md` is empty. The check is an AST walk over
  every file, with the same semantics as
  `test_147_specification_is_the_record._references_vision_md`, and it does not
  use a hand-listed set of files. *(closes Stage 31 criterion 2)*
- [ ] **AC4: the two functions are retired from the module.** The set of names
  in `{"vision_seed_titles", "vision_seed_conflicts"}` for which
  `hasattr(segfacet.failure_modes, name)` is true is empty.
- [ ] **AC5: no source text names a retired function.** The set of `.py` files
  under `src/segfacet/` whose raw text contains `vision_seed_titles` or
  `vision_seed_conflicts` is empty. Comments and docstrings count, so the stale
  comment at `traceability.py:270-273` is caught.
- [ ] **AC6: the provenance map is frozen at its v3 value.**
  `dict(segfacet.failure_modes.VISION_SEED_DISPOSITION)` equals this literal,
  which is typed by hand in the test:
  `{"Label not aligned with the anatomical vertebra it names": "retired",
  "Over-/under-segmentation — fused or fragmented vertebra segments": "mode:1",
  "Disconnected components / islands, especially tiny rogue segments": "mode:4",
  "Semantic mislabelling (wrong vertebra identification)": "mode:8",
  "Not all vertebrae in the image are segmented": "mode:6",
  "Partial vertebra at the image border whose appearance changes": "condition:fov_truncation",
  "Non-continuous label sequence (e.g. L1 → T12 → L2 → L5)": "mode:9",
  "Overlapping segments": "mode:15"}`.
- [ ] **AC7: every provenance disposition resolves.** The set of
  `VISION_SEED_DISPOSITION` values that are none of the following is empty:
  `"retired"`; `mode:<n>` where `int(n)` is a key of `SPECIFICATION`;
  `condition:<k>` where `k` is a key of `CONDITIONS`. The test recomputes this
  from `SPECIFICATION` and `CONDITIONS`, not from any function of the module.
- [ ] **AC8: the module docstring drops the stale §6 claims.** Collapse every
  whitespace run in `segfacet.failure_modes.__doc__` to one space. The set of
  these phrases that occur in the result is empty:
  `is the **seed**, not the record`,
  `re-issue through the create-vision entry point is owed`,
  `still equal §6's list`, `the only reader of that document`, and the
  Python string `"reads ``vision.md``"`, where the double backticks are
  literal characters in the docstring.
- [ ] **AC9: `_NOTE` does not use the word "seed".**
  `"seed" in segfacet.failure_modes._NOTE.lower()` is `False`.
- [ ] **AC10: the fresh rendering's §6 heading is the provenance heading.**
  Take the lines of `render_markdown()` that start with `## ` and contain
  `section 6`. That set equals
  `{"## Provenance: vision.md v3 section 6 seed titles"}`.
- [ ] **AC11: the provenance section opens with its explanatory sentence.** In
  `render_markdown()`, the first non-empty line after
  `## Provenance: vision.md v3 section 6 seed titles` equals:
  `vision.md section 6 states the catalogue's principles and points at this specification; the numbered list its v3 carried seeded the catalogue, and what became of each title is recorded below.`
- [ ] **AC12: the committed Markdown carries the provenance heading.** Take the
  lines of `docs/aide/failure_modes.generated.md` (read as text and split into
  lines) that start with `## ` and contain `section 6`. That set equals
  `{"## Provenance: vision.md v3 section 6 seed titles"}`.
- [ ] **AC13: the committed JSON's note is the module's note.**
  `json.loads(docs/aide/failure_modes.generated.json)["note"]` equals
  `segfacet.failure_modes._NOTE`.
- [ ] **AC14: the payload's top-level shape is unchanged.** The key set of the
  parsed committed `docs/aide/failure_modes.generated.json` equals
  `{"schema_version", "note", "modes", "conditions", "vision_seed_disposition"}`.
- [ ] **AC15: the committed JSON's provenance equals the frozen literal.** The
  `vision_seed_disposition` value of the parsed committed
  `docs/aide/failure_modes.generated.json` equals the AC6 literal.
- [ ] **AC16: no test parses §6 by its heading outside this item's module.** The
  set of `.py` files under `tests/`, excluding `tests/test_152_*.py`, that hold a
  non-docstring `str` constant containing `Segmentation Failure Modes` is empty.
  The check is an AST walk, so comments do not count.

**Correction (2026-09-16, builder hand-back) — AC3 is contradicted by AC10/AC11;
AC3 was wrong, and it is narrowed to path-shaped constants.** AC3 as written
flags any non-docstring `str` constant *containing* `vision.md` anywhere under
`src/segfacet/`, `failure_modes.py` included. AC10 and AC11 (pinned by A3) require
`render_markdown()` to emit a heading and a sentence that both contain `vision.md`.
With the live read retired, `render_markdown()` can only produce them from string
literals in `failure_modes.py`, so no implementation satisfies all three.
AC10/AC11 are the side that holds: they pin authored provenance text the item
exists to write. AC3 is the side that over-reached. Its claim is "no production
module **reads** `vision.md`", and a substring match is a proxy for that claim
which also matches prose *about* the document. Splitting the literal to dodge the
substring would pass the test while defeating it, so the predicate changes, not
the literal. What a read needs is a constant that *names the file as a path*:
measured 2026-09-16 on this branch, the one live read (`failure_modes.py:2167`,
`(_REPO_ROOT / "docs" / "aide" / "vision.md")`) holds the constant `"vision.md"`,
and every other `vision.md`-bearing non-docstring constant in `src/segfacet/` is
prose in which `vision.md` is followed by more text. AC3 is read as follows from
this date on; the original text above is the record of what the tests were first
written from.

- [ ] **AC3 (corrected 2026-09-16): no production module names `vision.md` as a
  path.** The set of `.py` files under `src/segfacet/`, `failure_modes.py`
  included and enumerated with `rglob` (never hand-listed), that hold a
  non-docstring `str` constant whose value matches
  `re.search(r"(?:^|[/\\])vision\.md$", value)` is empty. Docstring position is
  the same as in the committed `_docstring_constant_ids` helper (the first
  statement of a module, class or function body). The match is case-sensitive,
  is applied to the constant's exact value with no stripping, and visits the
  `Constant` parts of f-strings as `ast.walk` yields them. *(closes Stage 31
  criterion 2)*

The corrected AC3's controls, each a planted temp `.py` file fed to the same
predicate:

- **Flagged:** `open("docs/aide/vision.md")`; `Path(root) / "docs" / "aide" /
  "vision.md"`; `os.path.join(root, "vision.md")`; `f"{root}/vision.md"`; a
  Windows-separator constant `"docs\\aide\\vision.md"`.
- **Not flagged:** the AC10 heading literal
  `"## Provenance: vision.md v3 section 6 seed titles"`; the AC11 sentence
  literal; a docstring-only mention `"""See docs/aide/vision.md."""`; a comment
  `# see docs/aide/vision.md`.

Two consequences for the Testing Strategy, also corrected 2026-09-16. The
AC3/AC16 bullet's "same AST walker" now holds only for AC16: AC16 keeps its
substring needle `Segmentation Failure Modes`, and AC3 uses the path predicate
above. And reconcile entry 6 (`test_147::test_ac4_vision_parse_has_one_home`),
if re-pointed rather than retired, must use the corrected AC3 predicate and not
`test_147._references_vision_md`'s substring semantics, which the AC10/AC11
literals in `failure_modes.py` would trip. See A8.

## Assumptions

- **A1: retire the two functions, keep the map.** The queue allows either
  outcome. `vision_seed_titles()` and `vision_seed_conflicts()` are **retired**,
  because nothing is left to parse. `VISION_SEED_DISPOSITION` is **kept** under
  its current name, as a frozen literal. It is the only record of how the v3 seed
  list became the signed-off catalogue, and both committed artifacts already
  render it. Keeping the name keeps the JSON key `vision_seed_disposition`, so
  `SCHEMA_VERSION` stays `"2.1"` and
  `test_145_eight_hypothesised_modes.py:1408` stays green unchanged.
- **A2: no production function replaces `vision_seed_conflicts()`.** The map's
  one remaining invariant is that every disposition resolves (AC7). That is a
  claim about `SPECIFICATION` and `CONDITIONS`, and the suite holds it. The
  invariant is not folded into `specification_conflicts()`: that would add a
  direction to a function many tests pin as `== ()`, for a map that never
  changes.
- **A3: exact replacement text.** The generated Markdown heading is
  `## Provenance: vision.md v3 section 6 seed titles`. Its opening sentence is
  the AC11 literal. `_NOTE` loses only the word `seed`: "edit the seed ModeSpec
  entries" becomes "edit the ModeSpec entries". `_NOTE` makes no §6 claim today,
  and after this change "seed" in the generated documents refers only to the v3
  provenance section. The builder may reword the docstring freely within AC8.
  The two literals above are pinned.
- **A4: v4 arrives by merge, because PR #77 was not on `main` at spec time.**
  Measured 2026-09-16: `git log origin/main` has head `c5a73c8`, and
  `git branch -r --contains origin/docs/vision-v4-section-6` lists only
  `origin/docs/vision-v4-section-6`, whose head is
  `7d800a20c8cf779f2ef1b93d5ba65d48652e2b2e`. That is the sha gate 6 approved,
  and neither `main` nor `origin/aide/queue-021` contains it. The builder's
  **first act** is `git merge --no-ff 7d800a20c8cf779f2ef1b93d5ba65d48652e2b2e`
  on the item branch. It merges that exact sha, not the branch tip, and uses a
  merge, not a cherry-pick. The builder records the merge commit's sha in
  Decisions & Trade-offs. `git diff --stat origin/main...7d800a2` shows the
  branch changes only `docs/aide/vision.md`. **If** PR #77 has merged into
  `aide/queue-021`'s history by build time (`git merge-base --is-ancestor 7d800a2
  HEAD` exits 0 after `aide sync`), no merge is made, and Decisions records that
  instead. **If** the branch head has moved past `7d800a2`, the extra text was
  never gate-approved: the builder merges `7d800a2` only and records the newer
  head as an open finding. It does not merge the newer head.
- **A5: `test_137::test_ac17_vision_section_six_still_has_exactly_eight_modes`
  is retired, not re-pointed.** Item 137's claim ("§6 was recorded against, not
  grown") is false by design under v4. AC1 in the item-152 module carries the v4
  claim, and a re-pointed copy would duplicate it.
- **A6: `test_138`'s hand-typed `VISION_SECTION_SIX_MODE_TITLES` is kept** as the
  independent second copy of the v3 titles. Its re-pointed test compares the
  key set of `VISION_SEED_DISPOSITION` against that dict instead of against a
  live parse. The dict's comment is updated to say it transcribes v3's §6, which
  is in git history before `7d800a2`.
- **A7: `specification_to_dict()` needs no argument change.** Only the `note`
  string inside it changes, plus the Markdown section in `render_markdown()`.
- **A8 (added 2026-09-16, correction to AC3, `loop.clarify = "assume"`): a read
  is detected by a path-shaped constant.** A module that reads `vision.md` has
  to spell the file name as a path: either the whole constant `vision.md` or a
  constant ending in `/vision.md` or `\vision.md`. That shape is the narrowest
  predicate that still flags the retired read and every ordinary path spelling
  (`open`, `pathlib` joins, `os.path.join`, f-strings), while leaving authored
  prose that names the document alone. A deliberately obfuscated read
  (`"vision" + ".md"` built at runtime) is not caught. The original substring
  check did not catch it either, so the correction loses nothing. Rejected
  alternatives: (i) exempting `failure_modes.py`, which reopens the one file
  that held the read; (ii) exempting the two A3 literals by value, which pins
  the check to wording that A3 already pins elsewhere and flags the next
  provenance sentence anyone writes; (iii) splitting the literals, which leaves
  a check that passes on text written to evade it.

## Implementation Steps

1. **Merge v4** (A4): `git merge --no-ff 7d800a20c8cf779f2ef1b93d5ba65d48652e2b2e
   -m "Merge vision v4 section 6 (PR #77, gate 6) into item 152"`. Record the
   resulting sha in Decisions.
2. **`src/segfacet/failure_modes.py`:**
   - Delete `vision_seed_titles()` (~`:2145-2185`, with its section banner) and
     `vision_seed_conflicts()` (~`:2641-2677`). Remove both from `__all__`.
   - Rewrite the banner comment above `VISION_SEED_DISPOSITION` (~`:2026-2031`)
     as provenance. It records what v3 §6's numbered titles became. v4 §6
     carries no list, and nothing reads the document.
   - Rewrite the comment at ~`:744-745` so it no longer calls §6 "the list".
   - `_NOTE`: "the seed ModeSpec entries" becomes "the ModeSpec entries" (A3).
   - `render_markdown()`: replace the `## Vision section 6 seed disposition`
     heading with the A3 heading. Add a blank line, then the AC11 sentence, then
     a blank line, then the existing bullet list, unchanged.
   - Module docstring: rewrite the "Taxonomy as signed off" sentence (~`:26-29`)
     and the item-147 bullet (~`:179-183`) to describe the current state: §6 is
     principles plus a pointer, and `VISION_SEED_DISPOSITION` is frozen
     provenance of v3's list. Remove the Public API entry for
     `vision_seed_titles()` (~`:238-240`), or replace it with a
     `VISION_SEED_DISPOSITION` entry. Qualify the item-146 history paragraph
     (~`:114-117`, "§6's numbered eight") as v3's. The historical sections stay
     history: date them, do not delete them. Stay within AC8.
3. **`src/segfacet/traceability.py:269-274`:** rewrite the comment so it does not
   name the retired function. A mode row's title comes from
   `SPECIFICATION[mode].name`, and no module reads `vision.md`.
4. **Regenerate** with `.venv/bin/python -m segfacet.failure_modes`. Expected
   diff: in `docs/aide/failure_modes.generated.json`, only `note`. In
   `docs/aide/failure_modes.generated.md`, only the note line and the provenance
   section's heading and sentence.
5. **Check for mode-field changes.** No `ModeSpec`, `ConditionSpec`,
   `IntendedRule`, `CorpusCaseExpectation` or rule-declaration literal changes.
   If a step seems to need one, hand back.

## Authorised paths

**May change:**

- `docs/aide/vision.md` — **only** through the step-1 merge of the gate-6-approved
  commit `7d800a2` (PR #77). No commit authored by this item edits it.
- `src/segfacet/failure_modes.py` — the two functions are retired, the provenance
  prose and `_NOTE` are rewritten, and the Markdown section is renamed.
- `src/segfacet/traceability.py` — the stale comment naming
  `vision_seed_titles()` (AC5).
- `docs/aide/failure_modes.generated.json` — regenerated (the `note` changes).
- `docs/aide/failure_modes.generated.md` — regenerated (the note and the
  provenance section change).
- `tests/test_152_retire_vision_seed.py` — the new module for AC1–AC16.
- `tests/test_137_mode_less_rule_disposition.py` — AC17's eight-modes test is
  retired (A5).
- `tests/test_138_traceability_matrix.py` — the AC9 disposition test is
  re-pointed off the live parse (A6).
- `tests/test_144_failure_mode_specification.py` — both AC16 vision tests, the
  private `_vision_mode_titles()` and `_VISION_PATH` are re-pointed or retired.
- `tests/test_145_eight_hypothesised_modes.py` — the AC3 resolving-disposition
  test is re-pointed off `vision_seed_titles()` and `vision_seed_conflicts()`.
- `tests/test_147_specification_is_the_record.py` — AC4 loses its
  `failure_modes.py` exemption and the `vision_seed_titles()` call. AC5 and
  adv-AC5 are re-pointed or retired.
- `tests/test_151_stage30_validation.py` — AC27 and adv-AC27, which call
  `vision_seed_conflicts()`, are retired.

**Asserts against:**

None. The tests assert against the final state of files this item regenerates,
`docs/aide/vision.md` (brought in by the merge) and `src/segfacet/**/*.py` as a
whole. Those files are either listed under May change or read by a tree-wide
scan that pins no single file. The "no mode content changes" claim is a
diff-time check and belongs to Validation step 2 and `aide scope`, not to a pin.

## Testing Strategy

**New module: `tests/test_152_retire_vision_seed.py`**, with one focused test per
AC:

- **AC1/AC2** read `docs/aide/vision.md` live. They locate §6 with a local regex
  anchored on `^## 6\.`. They must not import anything from
  `segfacet.failure_modes`: §6 is the primary source.
- **AC3/AC16** use an AST walker that excludes docstrings, in the same shape as
  `test_147._references_vision_md`. It can be imported from `test_147`, or
  copied, and parameterised on the needle. Add a **positive control** for each.
  A planted temp `.py` file with `open("docs/aide/vision.md")` is flagged. A
  planted docstring-only mention is not flagged. For AC16, a planted
  `re.compile(r"^## 6\. Segmentation Failure Modes")` is flagged. AC16 must
  exclude its own file by `Path(__file__)`, because the module holds the needle.
- **AC4** is a set comprehension over `hasattr`. As a control, a
  `types.ModuleType` stand-in with the attribute set is flagged.
- **AC5** is a raw-text scan of every `src/segfacet/**/*.py`, enumerated with
  `rglob`. It is never hand-listed.
- **AC6** uses a literal dict typed in the test, never derived from the module.
- **AC7** recomputes resolution. Its adversarial cases feed the same resolver
  `mode:9999`, `condition:no_such`, `mode:abc` and `bogus`, and each must be
  reported. Also assert that all three kinds (`retired`, `mode`, `condition`) are
  exercised by the shipped map, so no branch goes dead.
- **AC8** normalises whitespace first, because the phrases in the docstring wrap
  across lines.
- **AC10/AC11** call `render_markdown()` once, in a module-scoped fixture.
  Rendering measures corpus firing and is slow.
- **AC12–AC15** read the committed artifacts. For JSON, use `json.loads`
  and compare only the fields named. For Markdown, use `read_text().splitlines()`
  and a line-set equality. Do **not** compare fresh against committed in this
  module: `test_145_eight_hypothesised_modes.py` already holds that equality
  (JSON and Markdown), and `tests/committed_artifact_guard.py` polices the form.

**Existing tests to reconcile.** Each one below calls a retired symbol or parses
§6's numbered form, and is red against v4 or would be once the functions go:

1. `test_137::test_ac17_vision_section_six_still_has_exactly_eight_modes`:
   retire (A5).
2. `test_138::test_ac9_vision_section_six_titles_are_dispositioned_provenance`:
   re-point. `set(VISION_SEED_DISPOSITION) ==
   set(VISION_SECTION_SIX_MODE_TITLES.values())`, each value resolves against
   the matrix's modes or `CONDITIONS`, and all three kinds are seen. Drop the
   `vision_seed_titles()` and `vision_seed_conflicts()` calls (A6).
3. `test_144::test_ac16_vision_section_six_seed_titles_all_have_a_resolving_disposition`:
   retire (AC6/AC7 carry it), or re-point without the parse.
4. `test_144::test_ac16_vision_seed_conflicts_reports_an_unresolvable_disposition`:
   retire with the function. Also remove `_vision_mode_titles()` and
   `_VISION_PATH` from the module if nothing else uses them (check with grep).
5. `test_145::test_ac3_every_vision_seed_title_has_a_resolving_disposition`:
   re-point off both functions, or retire.
   `test_ac3_retired_seed_title_is_carried_by_no_mode` reads only the map and
   stays.
6. `test_147::test_ac4_vision_parse_has_one_home`: re-point. No exemption for
   `failure_modes.py`, and no call to `vision_seed_titles()`. It then duplicates
   AC3, so it may be retired in favour of AC3; the builder records which.
   `test_adv_ac4_walker_flags_a_planted_real_read` stays.
7. `test_147::test_ac5_every_vision_seed_title_disposes_and_resolves`: re-point
   off both functions, or retire.
8. `test_147::test_adv_ac5_unresolvable_disposition_is_reported`: retire with
   `vision_seed_conflicts()`.
9. `test_151::test_ac27_vision_seed_conflicts_is_empty`: retire.
10. `test_151::test_adv_ac27_unresolvable_disposition_is_flagged`: retire. It is
    not in the 2026-09-16 insight's list, because against v4 it passes vacuously
    (the conflicts are non-empty anyway). It still calls the retired function.

The following stay green unchanged and need no edit:
`test_145_eight_hypothesised_modes.py:1408` (the map's JSON value is unchanged),
the fresh-vs-committed Markdown and JSON equalities in `test_145` (they follow
the regeneration), and `test_102::test_ac24_roadmap_and_vision_docs_are_not_hashed_here_but_present`
(it checks only that the file exists).

**The whole suite is the gate**, run against the merged v4 tree:
`.venv/bin/python -m pytest -n auto` is green.

## Validation

The validator executes these steps. The unit suite cannot observe merge ancestry
or a diff:

1. **v4 is what the tests ran against.**
   `git merge-base --is-ancestor 7d800a20c8cf779f2ef1b93d5ba65d48652e2b2e HEAD`
   exits 0. The Decisions log records either the merge sha or "already in base"
   (A4).
2. **No mode content changed.**
   `git diff aide/queue-021...HEAD -- docs/aide/failure_modes.generated.json`
   changes only the `"note"` line.
   `git diff aide/queue-021...HEAD -- docs/aide/failure_modes.generated.md`
   changes only the note line and the provenance section's heading and sentence,
   with no line under any `## Mode` or `## Condition` heading. Record the two
   `--stat` lines in the validation evidence.
3. **The regeneration is idempotent.** Run
   `.venv/bin/python -m segfacet.failure_modes`, then run
   `python .aide/scripts/aide.py sync --item 152`. It reports a clean tree, so the
   committed artifacts equal a fresh regeneration.
4. **Scope.** `python .aide/scripts/aide.py scope 152` passes. `docs/aide/vision.md`
   appears in the diff only because of the step-1 merge.
   `git log --format=%H aide/queue-021..HEAD -- docs/aide/vision.md` lists only
   `ba8a159` and `7d800a2`, plus the merge commit itself.

## Dependencies

None. Human gate 6, the vision v4 re-issue, is ✅ Approved (2026-09-16) and
reaches this item as its `Blocks` cell. PR #77 is a process deliverable (Stage 31
D1), not an item.

**Downstream:** item 159 touches `test_144`, `test_145` and `test_147`, and the
queue orders it after this item. Item 161 (Stage 31 validation) attests Stage 31
criterion 2 from AC1–AC3.

## Decisions & Trade-offs

- **A4: v4 merge sha.** By the time the builder started, the item branch
  already carried vision v4's content under commits `4b5326a`
  ("re-issue section 6 as v4") and `bd88a61` ("compact section 6..."), whose
  tree for `docs/aide/vision.md` is byte-identical to gate-6-approved commit
  `7d800a20c8cf779f2ef1b93d5ba65d48652e2b2e` (verified: `git diff bd88a61
  7d800a2 -- docs/aide/vision.md` is empty). That sha was not, however, an
  ancestor of `HEAD` (`git merge-base --is-ancestor 7d800a2 HEAD` exited 1) —
  a rebase during `aide sync` had linearised what had briefly been a genuine
  merge into independent commits with new hashes, dropping the merge edge
  from the graph. Per A4's default path, the builder ran
  `git merge --no-ff 7d800a20c8cf779f2ef1b93d5ba65d48652e2b2e -m "Merge
  vision v4 section 6 (PR #77, gate 6) into item 152"`. Because the trees
  already agreed, the merge produced no file changes — only the merge edge
  itself — as commit `cfff59ef29477cc9d1ce6f0fe5ac3f4f88cc42f2`. This
  satisfies Validation step 1 (`7d800a2` is now a genuine ancestor of `HEAD`)
  without altering `docs/aide/vision.md`'s content.
- **AC3 predicate:** implemented exactly per the 2026-09-16 correction (a
  path-shaped `re.search(r"(?:^|[/\\])vision\.md$", value)` over non-docstring
  `str` constants). The one live path read
  (`_REPO_ROOT / "docs" / "aide" / "vision.md"` inside the retired
  `vision_seed_titles()`) is deleted along with the function, so the set is
  empty; every remaining `vision.md` mention in `src/segfacet/` is prose
  (docstrings, comments, or the AC10/AC11 rendered strings) that does not
  match the path predicate.
- **`_REPO_ROOT` kept.** It still backs `JSON_PATH`/`MD_PATH`, unrelated to
  reading `vision.md`; nothing in scope asked to remove it.
- **Public API docstring entry:** replaced the retired
  `vision_seed_titles()` entry with a `VISION_SEED_DISPOSITION` entry (one of
  the two options Implementation Step 2 offered).
- **No mode/condition content changed** by this item: the only diff in
  `docs/aide/failure_modes.generated.json` is the `note` line; the only diff
  in `docs/aide/failure_modes.generated.md` is the note line plus the
  provenance section's heading and opening sentence — verified with
  `git diff` against the pre-regeneration tree.
- Tests were already reconciled (test-writer, commits `d57e717`/`7ce9af2`
  plus the AC3-correction commits): all ten listed reconcile-targets carry
  only comments/docstrings naming the retired functions, no live calls; AC17
  in `test_137` is retired per A5.
