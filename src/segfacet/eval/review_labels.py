"""The ``rl1`` review-label table read against a pinned schema (item 231).

``spine-failure-lab`` (package ``spinelab``) owns the schema of the review-label
table, tag ``rl1``: the ``review-label-fields`` table of its
``docs/project/facet-interface.md``, vendored here as
``review_label_schema_rl1.json`` at the commit that file names. The consumer
refuses an instance whose version differs, so every row's ``schema`` cell is
checked against :data:`RL1_SCHEMA_TAG`.

Design (item 231 Assumptions A1-A7):

* The table is a CSV with a header row (the format ``spinelab``'s collation
  already writes). The header is compared as a set of names, in any order;
  an unlisted, missing or duplicated column is refused.
* Conversion is by the schema's type only: ``integer`` -> ``int``, an empty
  ``string or null`` cell -> ``None``.
* :func:`apply_review_labels` turns each reviewed case's rows into the
  ``(label_id, mode_id)`` expectation of
  :func:`segfacet.eval.label_outcome.label_mode_expectation`. A cohort case with
  no row is dropped (not looked at is not clean); a row naming no cohort case is
  ignored. A case's role goes into ``EvaluationCase.metadata["role"]``.
* :func:`refuse_test_role` is the interface's rule that a test-role label is
  never used to fit or calibrate.

Scope fence: no pairing of a candidate descriptor with a ground-truth
descriptor (Stage 16), no use of the ``call`` field, and no writing of an
``rl1`` table.
"""

from __future__ import annotations

import csv
import dataclasses
import importlib.resources as _pkg_resources
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Union

from segfacet.eval.harness import EvaluationCase
from segfacet.eval.label_outcome import label_mode_expectation
from segfacet.io import FacetInputError

#: The pinned review-label schema tag.
RL1_SCHEMA_TAG: str = "rl1"

#: The interface's three dataset roles.
REVIEW_ROLES = ("development", "calibration", "test")

#: ``EvaluationCase.metadata`` key carrying a case's dataset role.
ROLE_METADATA_KEY: str = "role"


def load_rl1_schema() -> dict:
    """Return the vendored ``rl1`` schema (tag, source and typed fields)."""
    import segfacet.eval as _eval_pkg  # noqa: PLC0415

    ref = _pkg_resources.files(_eval_pkg).joinpath("review_label_schema_rl1.json")
    return json.loads(ref.read_text(encoding="utf-8"))


def read_review_label_table(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Read an ``rl1`` CSV into one mapping per data row, in file order.

    Raises
    ------
    segfacet.io.FacetInputError
        On an unreadable file, a header that differs from the vendored field
        names, a row whose schema tag is not ``rl1``, an ``integer`` cell that
        does not parse, or a role outside :data:`REVIEW_ROLES`.
    """
    fields = load_rl1_schema()["fields"]
    names = [f["name"] for f in fields]
    try:
        fh = open(path, newline="", encoding="utf-8")  # noqa: SIM115
    except OSError as exc:
        raise FacetInputError(f"review-label table: cannot read {path}: {exc}") from exc
    with fh:
        reader = csv.DictReader(fh)
        try:
            header = list(reader.fieldnames or [])
        except csv.Error as exc:
            raise FacetInputError(f"review-label table {path}: {exc}") from exc
        for col in dict.fromkeys(header):
            if header.count(col) > 1:
                raise FacetInputError(
                    f"review-label table {path}: column {col!r} is named twice."
                )
        for col in header:
            if col not in names:
                raise FacetInputError(
                    f"review-label table {path}: column {col!r} is not a field of "
                    f"schema {RL1_SCHEMA_TAG!r}."
                )
        for name in names:
            if name not in header:
                raise FacetInputError(
                    f"review-label table {path}: field {name!r} of schema "
                    f"{RL1_SCHEMA_TAG!r} is missing from the header."
                )
        rows: List[Dict[str, Any]] = []
        try:
            for raw in reader:
                where = f"review-label table {path}, line {reader.line_num}"
                if raw["schema"] != RL1_SCHEMA_TAG:
                    raise FacetInputError(
                        f"{where}: schema tag {raw['schema']!r} found, but only "
                        f"{RL1_SCHEMA_TAG!r} is pinned."
                    )
                row: Dict[str, Any] = {}
                for f in fields:
                    cell = raw[f["name"]]
                    if f["type"] == "integer":
                        try:
                            row[f["name"]] = int(cell)
                        except (TypeError, ValueError):
                            raise FacetInputError(
                                f"{where}: field {f['name']!r} is not an integer: {cell!r}."
                            ) from None
                    elif f["type"].endswith("or null") and cell == "":
                        row[f["name"]] = None
                    else:
                        row[f["name"]] = cell
                if row["role"] not in REVIEW_ROLES:
                    raise FacetInputError(
                        f"{where}: role {row['role']!r} is not one of {list(REVIEW_ROLES)}."
                    )
                rows.append(row)
        except csv.Error as exc:
            raise FacetInputError(f"review-label table {path}: {exc}") from exc
    return rows


def apply_review_labels(
    cases: Sequence[EvaluationCase], rows: Iterable[Mapping[str, Any]]
) -> List[EvaluationCase]:
    """Give each reviewed case its table expectation and role; drop the rest.

    Returns the input cases, in order, that some row's ``case_id`` names, each
    rebuilt with ``expected = label_mode_expectation(pairs)`` and
    ``metadata["role"]``. Rows naming no input case are ignored.

    Raises
    ------
    segfacet.io.FacetInputError
        If one case's rows carry different roles, or its pairs are refused by
        ``label_mode_expectation``. The message names the case id.
    """
    groups: Dict[str, List[Mapping[str, Any]]] = {}
    for r in rows:
        groups.setdefault(r["case_id"], []).append(r)
    out: List[EvaluationCase] = []
    for case in cases:
        group = groups.get(case.case_id)
        if not group:
            continue
        roles = sorted({r["role"] for r in group})
        if len(roles) > 1:
            raise FacetInputError(
                f"case {case.case_id!r}: review-label rows carry different roles {roles}."
            )
        try:
            expected = label_mode_expectation(
                [(r["label_id"], r["mode_id"]) for r in group]
            )
        except FacetInputError as exc:
            raise FacetInputError(f"case {case.case_id!r}: {exc}") from exc
        metadata = dict(case.metadata or {})
        metadata[ROLE_METADATA_KEY] = roles[0]
        out.append(dataclasses.replace(case, expected=expected, metadata=metadata))
    return out


def refuse_test_role(cases: Sequence[EvaluationCase], *, purpose: str) -> None:
    """Raise ``FacetInputError`` naming every test-role case in *cases*.

    A label's use follows its case's role: a test-role label is never used to
    fit or calibrate. A case with no metadata passes.
    """
    held_out = [
        c.case_id
        for c in cases
        if (c.metadata or {}).get(ROLE_METADATA_KEY) == "test"
    ]
    if held_out:
        raise FacetInputError(
            f"{purpose}: test-role case(s) {held_out} may not be used to fit or calibrate."
        )
