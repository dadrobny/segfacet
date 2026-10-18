<!-- aide-template: item 3 -->
# Item 228 — Descriptor subsets as explicit case-id lists

> **Created:** 2026-10-18 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 35 — Programme Interface: the SegFACET Side
> **Queue:** [`../queue/queue-031.md`](../queue/queue-031.md) · Item 228
> **Objectives:** G7
> **Suggested branch:** `aide/228-descriptor-subsets-as-explicit-case`

---

## Description

Stage 35's first deliverable: a dataset descriptor's `subsets` can name a
dataset role as an explicit list of case ids, not only as a directory root.
MSKGSTT's roles in `spine-failure-lab`'s split manifest are case lists, not
directories (`docs/project/facet-interface.md` at `7436b0f`, "Dataset roles").

`segfacet.datasets` (item 086) already carries a list form, the
`{"ids": [...]}` selector, alongside `root`, `csv` and `glob`. What it lacks
is the guarantee a role needs. The resolver drops a listed id that has no
matching mask without saying so, so a role list that has drifted from the
data resolves a smaller cohort and nobody is told. It also takes any selector
shape it is given. A selector carrying both `root` and `ids` resolves the
whole root and ignores the list. A bare YAML list makes `resolve` crash with
a raw `ValueError`.

This item makes the list form safe to name a role with:

- **A listed id that the root does not hold is an error.** `resolve` raises
  `DatasetSchemaError` and names every such id. This covers the `ids`
  selector and the `csv` selector, which is a list of ids read from a file.
- **A selector of the wrong shape is refused when the descriptor is
  constructed.** A selector must be a mapping whose keys are exactly one of
  `{root}`, `{ids}`, `{glob}`, `{csv}` or `{csv, column}`.

The CLI needs no change. `--subset` is already passed through to `resolve`
for `run`, `build-reference` and `evaluate`, and each handler already turns a
`DatasetSchemaError` into exit code 1. One AC checks that the list form
reaches a subcommand.

**Not in scope.** No descriptor is written or edited. The VerSe role subsets
belong to item 229, and MSKGSTT descriptors are written by `spinelab`. There
is no bare-list shorthand for `ids` (see Assumptions), and the `glob`
selector is unchanged.

## Acceptance Criteria

- [ ] **AC1: An `ids` subset resolves exactly the listed cases.** The root
  holds masks for `sub-verse004`, `sub-verse004_split-verse01`,
  `sub-verse005` and `sub-verse006`. Resolving a subset
  `{"ids": ["sub-verse004", "sub-verse006"]}` gives a cohort whose `case_ids`
  equal `("sub-verse004", "sub-verse006")`. The split-subject case, whose id
  begins with a listed id, is not included.
- [ ] **AC2: A listed id with no matching mask raises an error naming it.**
  The root holds `sub-verse004` only. Resolving a subset
  `{"ids": ["sub-verse004", "sub-verse098", "sub-verse099"]}` raises
  `DatasetSchemaError`, and the message contains both `sub-verse098` and
  `sub-verse099`.
- [ ] **AC3: A CSV-listed id with no matching mask raises an error naming
  it.** The root holds `sub-verse004` only. Resolving a
  `{"csv": "<file>"}` subset whose `case_id` column lists `sub-verse004` and
  `sub-verse099` raises `DatasetSchemaError`, and the message contains
  `sub-verse099`.
- [ ] **AC4: A malformed subset selector is refused at construction.**
  `DatasetDescriptor.from_dict` raises `DatasetSchemaError`, with a message
  naming the offending subset, for a subset whose selector is not a mapping
  with key set exactly one of `{root}`, `{ids}`, `{glob}`, `{csv}` or
  `{csv, column}`.
- [ ] **AC5: `--subset` selects an `ids` subset from the CLI.** The root
  holds three real synthetic NIfTI cases (`sub-verse004`, `sub-verse005`,
  `sub-verse006`). The descriptor file declares a subset
  `picked: {ids: [sub-verse004, sub-verse006]}`. `segfacet run
  --dataset-schema <file> --subset picked --out <dir>` then writes per-case
  output directories, and the set of directory names under `<dir>` equals
  `{"sub-verse004", "sub-verse006"}`.

Each AC answers one of the queue line's testable claims or guards the list
form against a failure that line names. AC1 is "exactly those cases and no
others". AC2 and AC3 are "an id the list names that the root does not hold is
reported, not skipped" for both id-list selectors. AC4 stops a selector that
looks like a list from silently resolving a whole root, which would break
AC1's guarantee. AC5 is "`--subset` selects either form from the CLI". The
queue line's "a root subset resolves as before" is already held by existing
tests (see Testing Strategy), so it gets no new AC.

## Assumptions

- **A1:** The list form is the existing `{"ids": [...]}` selector. No new
  bare-list shorthand (`role: [id, ...]`) is added. `facet-interface.md`'s
  "Dataset roles" section says case lists are something "the descriptor
  cannot yet express". The selector already existed when that was written.
  What was missing was the error on a listed id that is absent, and a
  refusal of bad shapes, and this item adds both. A bare list is refused by
  AC4 with a message, so a descriptor written in that shape fails with an
  explanation rather than a traceback.
- **A2:** A `csv` selector is a list of ids read from a file, so it gets the
  same missing-id error (AC3). A `glob` selector names a pattern rather than
  ids, so a glob that matches nothing still resolves an empty cohort, as it
  does today.
- **A3:** Selector validation checks the shape and does not rewrite it. The
  stored `subsets` mapping is kept exactly as given:
  `tests/test_088_stage13_acceptance.py` asserts
  `d.subsets["training"] == {"root": "dataset-verse19training"}`.
- **A4:** An `ids` or `csv` subset is resolved against the effective root.
  That is the `data_root` override passed to `resolve` (the CLI's
  `--data-root`), or the descriptor's own `data_root` when there is no
  override, which is what happens today. A selector is never a combination of
  `root` and `ids`. A role that is a directory uses `root`, and a role that is
  a case list uses `ids`.
- **A5:** An empty list (`{"ids": []}`) names no id, so no id can be missing,
  and it resolves an empty cohort as it does today. `segfacet run`'s batch
  mode already refuses an empty cohort.
- **A6:** The missing-id check runs over the ids the list names. It does not
  run over masks the list leaves out, so a root holding unlisted cases is
  normal (AC1). The existing "case_id regex did not match" and "duplicate
  case_id" errors keep their current behaviour and order.

## Implementation Steps

All changes are in `src/segfacet/datasets/__init__.py`. No dependency is
added.

1. **Selector shape check.** In `DatasetDescriptor.__post_init__`, loop over
   `self.subsets.items()`. Raise `DatasetSchemaError` naming the subset and
   the keys found unless the selector is a `Mapping` whose `set(keys)` is one
   of `{"root"}`, `{"ids"}`, `{"glob"}`, `{"csv"}` or `{"csv", "column"}`. A
   module-level frozenset of those five frozensets is enough. Because the
   check sits in `__post_init__`, it covers both `from_dict` and direct
   construction. Selectors are stored exactly as given (A3).
   `from_dict`'s `dict(data.get("subsets") or {})` copies only the outer
   mapping, so it is unchanged.
2. **Missing-id error.** In `resolve`, after the seg-match loop, when
   `id_filter is not None`: compute `missing = sorted(id_filter -
   seen.keys())`. If it is non-empty, raise `DatasetSchemaError` naming the
   subset, the resolved root and every id in `missing`. `id_filter` is
   already built by the existing `_case_id_filter` for both `ids` and `csv`,
   and `seen` already holds every kept case id. Reuse both and add no second
   pass.
3. **Docstrings.** Update the `subsets` paragraph of `DatasetDescriptor`
   ("exactly one of" is now enforced, plus the `csv`+`column` pair), the
   `Raises` block of `resolve` (a listed id with no mask), and the module
   docstring's scope note: this item makes an `ids` or `csv` subset report a
   missing id.
4. **No CLI edit.** `cli._resolve_cohort_from_args` already passes `--subset`
   through, and `_run_batch`, `_handle_build_reference` and the evaluate
   handler already catch `DatasetSchemaError` and exit 1.

## Authorised paths

**May change:**

- `src/segfacet/datasets/__init__.py` — the selector shape check and the missing-id error
- `tests/test_228_case_id_list_subsets.py` — this item's tests

**Asserts against:**

None.

## Testing Strategy

New module `tests/test_228_case_id_list_subsets.py`, one test per AC. For
AC1–AC4, build the tree with empty files as `tests/test_086_datasets.py`'s
`_touch` / `_nested_verse` do. Copy the few lines and do not import from
another test module. AC5 runs the pipeline, so it needs real NIfTIs. Build
them with `segfacet.synth.clean_gt.build_clean_spine` and
`segfacet.synth.intensity.paint_clean_scan` in the nested VerSe layout, as
`tests/test_087_dataset_cli.py::_build_nested` does. Write the descriptor YAML
with `as_posix()` paths, as that module explains, for Windows. AC5 may pass
`--no-reference` to keep the run off the bundled reference. The assertion is
the set of output directory names, not the verdict.

Adversarial cases, all part of AC4's test, parametrised. Each is a selector
`from_dict` must refuse:

- `root-and-ids` (`{"root": "x", "ids": ["sub-verse004"]}`): guards the
  silent mis-selection where `_select_root` takes `root`, ignores the list and
  resolves the whole directory.
- `bare-list` (`["sub-verse004"]`): guards the raw `ValueError` from
  `dict(selector)` in `_select_root`, which the module promises never to
  raise in place of `DatasetSchemaError`.
- `no-selector-key` (`{"column": "case_id"}`): guards the selector with no
  recognised key, which today falls through `_case_id_filter` as `None` and
  resolves the whole dataset.

AC2 names two missing ids rather than one. This guards an error that reports
only the first missing id, which would leave a person fixing a drifted role
list one id per run.

**Existing tests that must stay green, unmodified.** These are the
regression guard for "a root subset resolves as before" and for valid
selector shapes passing the new check:
`tests/test_086_datasets.py::test_subset_root_folder_split`,
`::test_subset_ids_and_glob`, `::test_subset_csv`,
`tests/test_087_dataset_cli.py::test_cli_build_reference_subset` and
`tests/test_088_stage13_acceptance.py` (the bundled `verse19.yaml` root
subsets).

**Existing tests to reconcile:** none. A sweep of `tests/` for `ids`, `csv`
and `subsets` literals found every listed id present in its fixture and every
selector a single valid key. No test relies on a listed id being skipped
silently, or on a mixed or bare selector.

## Dependencies

None.

**Downstream:** item 229 may express the VerSe role subsets with this list
form, and `spinelab`'s candidate descriptors name MSKGSTT roles with it.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether a `subsets` value that is not itself a mapping
  (e.g. `subsets: [a, b]`) gets a `DatasetSchemaError` rather than the raw
  error from `from_dict`'s `dict(...)` coercion. No descriptor in the batch
  is written that way, and the per-selector check is what the role lists
  need.
