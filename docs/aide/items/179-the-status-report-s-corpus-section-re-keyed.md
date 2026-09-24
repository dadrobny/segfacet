<!-- aide-template: item 2 -->
# Item 179 — The status report's corpus section re-keyed off the generated specification

> **Created:** 2026-09-24 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-023.md`](../queue/queue-023.md) · Item 179
> **Objectives:** G2, G7
> **Suggested branch:** `aide/179-the-status-report-s-corpus`

---

## Description

`scripts/aide_status_report.py` renders the Synthetic Failure Corpus section
of the project-status dashboard. Its failure-mode wording still describes the
catalogue as it stood before item 150's sign-off:

- `FAILURE_MODES_LEGEND` is a hand-typed dict of the eight vision-era modes
  (1 = "Label not aligned with the vertebra it names" … 8 = "Overlapping
  segments");
- the note says "Each of the eight catalogued segmentation failure modes";
- the coverage card renders `N/8`;
- the footnote names "modes 1/4/8" as the reconstructed-record modes.

The manifest rows the section tabulates beside that legend carry the
sixteen-mode numbering of `src/segfacet/failure_modes.py` (`split` = 3,
`force_overlap` = 15), so the legend mislabels its own table's Mode column
(`insights.md`, queue-022, 2026-09-21, routed to roadmap Stage 33 D1).

This item re-keys that wording off the two committed, generated documents:

- `docs/aide/failure_modes.generated.json` supplies every mode's id, title
  and derived lifecycle status, and which modes have a committed corpus case;
- `docs/aide/traceability_matrix.generated.json` supplies the conformance
  counts: how many corpus cases have a measured firing equal to their
  expected set.

Both are read with the stdlib `json` module only, the way the Feature Catalog
section already reads `feature_catalogue.generated.json`. The script stays
import-clean of `segfacet`.

**Not in scope:**

- the manifest table itself: it stays keyed on `tests/corpus/manifest.json`
  rows, whose `failure_mode_name` is already written from the specification
  (A3);
- the intensity corpus's rows in that table (see Left open);
- embedding `docs/aide/corpus_sheet.png` (item 178) in the report;
- any other section of the report, including the Feature Catalog section's
  "§6 failure mode(s)" phrase;
- any change to `src/segfacet/**`, the generated JSON, or the corpus.

## Acceptance Criteria

In every AC, "the committed JSON" means the file the test reads itself with
`json.loads(path.read_text(encoding="utf-8"))`, never through the script.
"The real model" is
`asr.ReportModel(generated_at="now", corpus=asr.parse_corpus_manifest(<repo>/tests/corpus/manifest.json))`.

- [ ] **AC1: the legend is the specification's mode list.** In
  `asr.render_html(<the real model>)`, the text between
  `<ul class="legend">` and the next `</ul>`, split by
  `re.findall(r"<li>.*?</li>", ...)`, equals, in order, the list built from
  the committed `docs/aide/failure_modes.generated.json`'s `modes` array in
  file order:
  `f'<li><strong>{m["id"]}</strong> — {html.escape(m["name"])} <span class="b-pill">{html.escape(m["status_derived"])}</span></li>'`.
- [ ] **AC2: the coverage card counts the specification's modes.**
  `asr.render_html(<the real model>)` contains
  `f'<div class="n">{covered}/{total}</div><div class="l">Failure modes with a committed case</div>'`,
  where `total` is the length of the committed `failure_modes.generated.json`'s
  `modes` array and `covered` is the number of its entries whose
  `corpus_cases` list is non-empty.
- [ ] **AC3: the conformance card reads the traceability matrix.**
  `asr.render_html(<the real model>)` contains
  `f'<div class="n">{a}/{a + d}</div><div class="l">Cases whose measured firing equals the expected set</div>'`,
  where `a` and `d` are the committed
  `traceability_matrix.generated.json`'s `conformance.agree_count` and
  `conformance.disagree_count`.
- [ ] **AC4: a title edited in a copy of the JSON changes the rendering.**
  The test copies both committed JSON files into `tmp_path`, and in the copy
  of `failure_modes.generated.json` sets the `name` of the mode whose `id` is
  `3` to `"Sentinel title 179"`. Then
  `asr._render_corpus_section(<the real model>, asr.load_failure_mode_spec(<fm copy>, <tm copy>))`
  contains `"<strong>3</strong> — Sentinel title 179 "`.
- [ ] **AC5: no hand-typed mode title remains in the script.** No
  `ast.Constant` whose value is a `str`, anywhere in the parsed
  `scripts/aide_status_report.py` (f-string parts included), contains, under
  `str.casefold()`, the `name` of any mode in the committed
  `failure_modes.generated.json`.
- [ ] **AC6: no eight-mode wording remains in the script.** No `ast.Constant`
  whose value is a `str`, anywhere in the parsed `scripts/aide_status_report.py`
  (f-string parts included), matches the regular expression
  `(?i)\beight\b|1/4/8`.

None of these ACs closes a Stage 33 acceptance criterion.

## Assumptions

- **A1 (measured 2026-09-24: the two JSON shapes this item reads).** On the
  base branch after item 178:
  - `docs/aide/failure_modes.generated.json` (`schema_version` `"2.2"`) is an
    object whose `modes` is a list of 16 objects. Each carries an `int` `id`
    (1–16), a `str` `name` (for example `"Split vertebra segment"`), a `str`
    `status_derived` (`validated` / `implemented` / `proposed`), and a list
    `corpus_cases`. Eight modes have a non-empty `corpus_cases`: 1, 2, 3, 4,
    6, 9, 15 and 16. So AC2 renders `8/16` today. The list spans both corpora
    (mode 16's cases are intensity cases).
  - `docs/aide/traceability_matrix.generated.json` (`schema_version` `"1.2"`)
    is an object whose `conformance` object carries `int` `agree_count` (18)
    and `disagree_count` (0), over 14 geometric and 4 intensity cases. So AC3
    renders `18/18` today.
  - Both are regenerated by `python -m segfacet.failure_modes` and
    `python -m segfacet.traceability`, and both are pinned `text eol=lf` in
    `.gitattributes`. This item changes neither.
- **A2 (defensible default: no `schema_version` pin).** `load_feature_catalog`
  rejects any `schema_version` but one. This loader does not: it reads the
  keys it needs and degrades on their absence. Both schemas have been bumped
  repeatedly (the failure-mode JSON is at 2.2), and a version pin would turn
  each bump into a silently-placeholdered section with no failing test.
- **A3 (measured 2026-09-24: the table already speaks the specification).**
  Each manifest row's `failure_mode_name` is written by the corpus generator
  from `FAILURE_MODE_NAMES` (or the FOV-truncation condition's name), so the
  table's Mode and Failure-mode columns already agree with the specification.
  Only the legend, note, card and footnote are hand-typed. Mode-0 rows are the
  clean control and the FOV-truncation condition's cases (`crop_at_border`,
  `crop_fov_si`), which are not failure modes.
- **A4 (measured 2026-09-24: the stdlib-only contract is already guarded).**
  `tests/test_103_feature_catalogue.py::test_ac21_stdlib_only_imports_still_hold`
  AST-scans this script's imports and fails on any `segfacet` import. It
  covers the new loader unchanged, so no AC of this item restates it.
- **A5 (measured 2026-09-24: what AC5 and AC6 see today).** Today AC5 fails on
  `FAILURE_MODES_LEGEND`'s value `"Overlapping segments"` (mode 15's name) and
  AC6 on the note's f-string (`"Each of the eight"`) and the footnote
  (`"modes 1/4/8"`). The word "eight" occurs nowhere else in the script's
  string constants (`height` in the CSS does not match `\beight\b`). The
  comment block above `FAILURE_MODES_LEGEND` is not an `ast.Constant`, but it
  goes with the dict.

## Implementation Steps

All changes are in `scripts/aide_status_report.py`. No dependency is added,
and nothing under `src/segfacet/` is imported.

1. **Paths.** Beside `FEATURE_CATALOGUE_PATH`, add
   `FAILURE_MODES_PATH = AIDE_DIR / "failure_modes.generated.json"` and
   `TRACEABILITY_PATH = AIDE_DIR / "traceability_matrix.generated.json"`.
2. **Loader.** Add two frozen dataclasses and one function:
   - `ModeEntry(id: int, name: str, status: str, case_count: int)`;
   - `FailureModeSpec(modes: Tuple[ModeEntry, ...], agree_count: int, disagree_count: int)`;
   - `load_failure_mode_spec(failure_modes_path: Path = FAILURE_MODES_PATH, traceability_path: Path = TRACEABILITY_PATH) -> Optional[FailureModeSpec]`.

   It reads each file with `Path.read_text(encoding="utf-8")` and
   `json.loads`, in the shape of `load_feature_catalog`. It returns `None`,
   never raises, when either file is missing, a directory, or unparseable,
   when either top level is not a `dict`, when `modes` is not a `list`, or
   when `conformance` is not a `dict` with `int` `agree_count` and
   `disagree_count`. A mode entry whose `id` is not an `int` or whose `name`
   is not a non-empty `str` is skipped. `status` reads `status_derived`
   through the existing `_str_field` helper. `case_count` is
   `len(corpus_cases)` when that is a list, else 0. No `schema_version` check
   (A2).
3. **Render.** Change `_render_corpus_section(model)` to
   `_render_corpus_section(model, spec: Optional[FailureModeSpec])`, and in
   `render_html` call it as
   `_render_corpus_section(model, load_failure_mode_spec())`, the same way
   the Feature Catalog section is loaded.
   - The empty-`model.corpus` placeholder stays. Reword its "one row per
     catalogued segmentation failure mode (project vision §6)" to name the
     specification instead.
   - **Legend:** one `<li>` per `spec.modes` entry, in the exact form AC1
     states (the existing `b-pill` class), inside the existing collapsed
     `<details class="fold">` + `<ul class="legend">`. The summary names the
     source, `failure_modes.generated.json`, and the regeneration command
     `python -m segfacet.failure_modes`.
   - **Note:** one sentence with no count and no mode names. It says that the
     legend is the authored specification (`src/segfacet/failure_modes.py`)
     with each mode's derived status, that the table is the geometric
     manifest, and that mode-0 rows are the clean control and condition cases.
   - **Cards:** keep "Committed cases" and "Reconstructed-record" as they
     are. Replace the `N/8` card with AC2's card. Add AC3's card.
   - **Footnote:** drop the "(modes 1/4/8)" list. The Detection column
     already marks which rows are reconstructed-record.
   - When `spec` is `None`, render the table and the two manifest cards, and
     in place of the legend and the two spec cards a
     `<p class="placeholder">` naming both JSON paths and the two
     regeneration commands.
4. **Delete** `FAILURE_MODES_LEGEND` and the comment block above it.
5. The module docstring's section list is unchanged, since it does not name
   the corpus section.

## Authorised paths

**May change:**

- `scripts/aide_status_report.py` — the loader and the re-keyed section
  (steps 1–4).
- `tests/test_179_status_report_corpus.py` — **new**: this item's test
  module.
- `tests/test_aide_status_report.py` — two existing tests pin the old
  wording and are reconciled (Testing Strategy).

**Asserts against:**

- `docs/aide/failure_modes.generated.json` — AC1, AC2, AC4 and AC5 read its
  `modes`.
- `docs/aide/traceability_matrix.generated.json` — AC3 and AC4 read its
  `conformance`.
- `tests/corpus/manifest.json` — the real model's rows, for AC1–AC4.

## Testing Strategy

**The new module is `tests/test_179_status_report_corpus.py`**, with one test
per AC (AC1–AC6). It loads the script by path with
`importlib.util.spec_from_file_location`, registering it in `sys.modules`
before `exec_module`, exactly as `tests/test_aide_status_report.py` does
(dataclass introspection needs the registration). It reads the committed JSON
itself with `json.loads`, never through `load_failure_mode_spec`, so AC1–AC3
recompute every expected value from the primary source. AC5 and AC6 walk
`ast.walk(ast.parse(source))` for `ast.Constant` nodes with `str` values,
which covers f-string literal parts. AC4 writes only under `tmp_path`.

Adversarial cases, each written once:

- **`mode-count-follows-the-json`**: from a `tmp_path` copy of
  `failure_modes.generated.json` with its last mode removed,
  `_render_corpus_section(<the real model>, load_failure_mode_spec(<copy>, <committed tm>))`
  contains `f"/{total - 1}</div>"` in the coverage card and one fewer legend
  `<li>`. This guards a `total` hard-coded to 16, which AC2 on live state
  cannot tell apart from a derived one.
- **`conformance-disagreement-shows`**: from a `tmp_path` copy of
  `traceability_matrix.generated.json` with `agree_count` lowered by 1 and
  `disagree_count` raised by 1, the conformance card reads
  `f"{a - 1}/{a + d}"`. This guards a card that renders `agree/agree`, which
  is indistinguishable from the real one while every case agrees (A1: 18/18).
- **`missing-json-degrades`**: `load_failure_mode_spec(tmp_path / "absent.json", <committed tm>)`
  returns `None`, and `_render_corpus_section(<the real model>, None)` returns
  a string that contains the case id `clean_control` and
  `python -m segfacet.failure_modes`. This guards the whole status report
  crashing when a generated artifact is absent mid-regeneration.
- **`legend-name-is-escaped`**: with a copied spec whose mode-3 `name` is
  `"<b>x</b>"`, the rendered section contains `"&lt;b&gt;x&lt;/b&gt;"` and not
  `"<b>x</b>"`. This guards an unescaped JSON field injecting markup into the
  dashboard.

**Existing tests to reconcile** (grep of `tests/` for `FAILURE_MODES_LEGEND`,
`/8`, `eight`, `vision.md §6` and `_render_corpus_section`, 2026-09-24). Both
are in `tests/test_aide_status_report.py`:

- `test_render_corpus_section_populated_shows_coverage_and_badges` asserts
  `"1/8" in doc`. That card is now AC2's and reads the live JSON (`8/16`).
  Delete that one assertion and keep the rest of the test.
- `test_corpus_legend_spells_out_failure_modes` asserts `"vision.md §6" in doc`
  (and `"Overlapping segments"`). Delete the test: AC1 is its successor, and
  pins every mode title against the live JSON rather than one literal.

`test_render_corpus_section_placeholder_when_absent`,
`test_render_html_is_self_contained_and_escaped` and
`test_render_html_deterministic` stay unchanged, and must stay green. In
particular the no-`http://` assertion means that the new text must not carry
a URL.

## Validation

Run `.venv/bin/python scripts/aide_status_report.py --out <scratch>/status.html`
and open the Synthetic Failure Corpus section. Check three things:

- The legend lists 16 modes, from 1 "Segmentation accuracy
  (over-/under-segmentation)" to 16 "Implausible tissue under a label", each
  with its derived status.
- The cards read `8/16` and `18/18` (A1).
- The Mode column's `3` and `15` rows (`split`, `split_own_label`,
  `force_overlap`) agree with the legend's entries 3 and 15.

## Dependencies

- Item 173 (✅): the lordotic base and the regenerated specification and
  traceability JSON this item reads (A1 is measured on the base after it).

**Downstream:** Stage 33's D5 gate reads the status report beside the corpus
sheet, but no item in this queue consumes the section.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether the manifest table should also list the intensity
  corpus's rows (`tests/corpus/intensity/manifest.json`, mode 16). The cards
  already count both corpora through the JSON. The queue line re-keys the
  wording, not the table's scope.
