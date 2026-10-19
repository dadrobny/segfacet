#!/usr/bin/env python3
"""Development-role VerSe reference rebuild tool (items 123, 234).

This is an AIDE *project tool*, not part of the shipped ``segfacet`` package
(follows ``scripts/refresh_reference.py``'s path-loaded, testable-helper
shape). It rebuilds ``reference_verse_v1.json`` from the **development** role
of the two bundled VerSe descriptors (``verse19.yaml``, ``verse20.yaml``;
item 229), the only role ``spine-failure-lab``'s ``facet-interface.md`` lets
build a reference. It:

1. Resolves the two release roots: ``--verse-cohort`` /
   ``SEGFACET_VERSE_COHORT`` (VerSe19) and ``--verse20-cohort`` /
   ``SEGFACET_VERSE20_COHORT`` (VerSe20). Each names a *three-split root*, the
   directory that holds the release's split directories. **Both** are
   required: with either unresolved, missing, or resolving an empty
   development role, the run is a structured skip (exit ``0``, summary
   written, no artifact) -- a one-release build is not the reference the
   stage describes.
2. Refuses to build (``RoleOverlapError``, exit ``1``, no artifact) when any
   development case also resolves in a ``calibration`` or ``test`` role, or
   in two sources (:func:`development_cohort`).
3. Ingests the merged development cohort through
   ``segfacet.reference.ingest.ingest_dataset_cohort`` (``--jobs`` ingests
   cases in parallel; a serial full rebuild takes about 19 CPU-hours).
4. Withholds the readings in :data:`EXCLUDED_OFFSETS` (``gate-fac1``) from the
   ``spline_offset_mm`` distribution, then aggregates and writes
   ``<out>/reference_verse_v1.json`` with the sorted ``case_ids`` in its
   provenance -- never the committed package copy under ``src/segfacet/``.
5. Derives the ``spline_offset.max_offset_mm`` threshold via
   :func:`derive_max_offset_mm`, a pure function of the built
   ``ReferenceDistribution``, and records the calibration evidence.

Every step's outcome is written to ``<out>/verse_rebuild_summary.json`` (see
``tests/test_234_development_role_reference.py`` for the pinned shape).

Usage::

    python scripts/rebuild_verse_reference.py --out out/verse-rebuild \\
        --verse-cohort /path/to/VerSe19 --verse20-cohort /path/to/VerSe20 --jobs 8

Self-contained: imports only ``segfacet.*`` production modules; never imports
the ``tests`` package.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Real-VerSe vertebra-mask filename suffix (docs/aide/dataset-verse19.md).
VERSE_SEG_SUFFIX = "_seg-vert_msk.nii.gz"
#: Real-VerSe CT filename suffix.
VERSE_CT_SUFFIX = "_ct.nii.gz"

#: Machine-local configuration variables naming the two release roots --
#: resolution order is the CLI flag -> this env var -> unresolved. Never a
#: literal dataset path in this file.
ENV_VAR = "SEGFACET_VERSE_COHORT"
ENV_VAR_V20 = "SEGFACET_VERSE20_COHORT"

#: Readings withheld from the reference before aggregation (gate-fac1, owner
#: decision 2026-10-16): ``(case_id, level_name)`` of a ``spline_offset_mm``.
#: sub-verse406_split-verse261 T10 (label 17) is a rare wedge vertebra whose
#: 18.51 mm offset is an anatomical outlier.
EXCLUDED_OFFSETS = frozenset({("sub-verse406_split-verse261", "T10")})

#: The floor `derive_max_offset_mm` never returns below (Assumptions:
#: `relabel_swap`'s 5.143859 mm non-firing ceiling must stay clear).
_FLOOR_MM = 6.0
#: The rounding granularity `derive_max_offset_mm` rounds up to.
_ROUND_STEP_MM = 0.5
#: A qualifying level must carry at least this many `spline_offset_mm`
#: subject-level records (small-sample levels' p99 is one subject's max).
_MIN_QUALIFYING_COUNT = 10

_SUMMARY_NAME = "verse_rebuild_summary.json"
_ROLES = ("development", "calibration", "test")


# =========================================================================== #
# Cohort resolution
# =========================================================================== #


class RoleOverlapError(ValueError):
    """A development case also resolves in a calibration or test role (or in a
    second source), so the reference would not be development-only."""


def resolve_root(cli_value: Optional[str], env_var: str) -> Optional[Path]:
    """*cli_value* if given (non-empty), else the *env_var* environment
    variable if non-empty, else ``None``. Never hard-codes a path."""
    if cli_value:
        return Path(cli_value)
    env_value = os.environ.get(env_var)
    if env_value:
        return Path(env_value)
    return None


def development_cohort(sources: Sequence[Tuple[Any, Any]]):
    """The merged ``development`` cohort of ``(DatasetDescriptor, data_root)``
    *sources*, or :class:`RoleOverlapError` naming every offending case id.

    A development case id is an offender when it also appears in any source's
    ``calibration`` or ``test`` cohort, or in the development cohort of two
    sources (a cross-release duplicate cannot be a single case).
    """
    from segfacet.datasets import Cohort, resolve

    development = []
    offenders = set()
    seen = set()
    for descriptor, data_root in sources:
        by_role = {
            role: resolve(descriptor, data_root=data_root, subset=role) for role in _ROLES
        }
        dev_ids = set(by_role["development"].case_ids)
        offenders |= dev_ids & set(by_role["calibration"].case_ids)
        offenders |= dev_ids & set(by_role["test"].case_ids)
        offenders |= dev_ids & seen
        seen |= dev_ids
        development.extend(by_role["development"].cases)
    if offenders:
        raise RoleOverlapError(
            "development-role case(s) also resolve in a calibration or test role "
            f"(or in a second source): {', '.join(sorted(offenders))}"
        )
    development.sort(key=lambda c: c.case_id)
    return Cohort(cases=tuple(development), name="development")


# =========================================================================== #
# Threshold derivation (AC9-AC11)
# =========================================================================== #


def derive_max_offset_mm(distribution) -> float:
    """Pure derivation of ``spline_offset.max_offset_mm`` from a built
    :class:`~segfacet.reference.schema.ReferenceDistribution`.

    Returns ``max(6.0, S)`` where ``S`` is the smallest positive multiple of
    ``0.5`` strictly greater than ``P``, and ``P`` is the maximum over levels
    whose ``spline_offset_mm.count >= 10`` of that level's
    ``feature_stats["spline_offset_mm"].percentiles["p99"]``. Levels with
    fewer than 10 subjects are excluded. Reads no file, no clock, no
    environment; returns the same value for the same input on repeated
    calls. If no level qualifies (or none carries ``spline_offset_mm``
    stats at all), returns the floor ``6.0``.
    """
    from segfacet.reference import ALL_STRATUM

    p_max: Optional[float] = None
    for strata in distribution.levels.values():
        stats = strata.get(ALL_STRATUM)
        if stats is None:
            continue
        offset_stats = stats.feature_stats.get("spline_offset_mm")
        if offset_stats is None:
            continue
        if offset_stats.count < _MIN_QUALIFYING_COUNT:
            continue
        p99 = offset_stats.percentiles.get("p99")
        if p99 is None:
            continue
        if p_max is None or p99 > p_max:
            p_max = p99

    if p_max is None:
        return _FLOOR_MM

    steps = math.floor(p_max / _ROUND_STEP_MM) + 1
    rounded = steps * _ROUND_STEP_MM
    return max(_FLOOR_MM, rounded)


def _p99_by_level(distribution) -> Dict[str, Dict[str, Any]]:
    from segfacet.reference import ALL_STRATUM

    result: Dict[str, Dict[str, Any]] = {}
    for level_name, strata in distribution.levels.items():
        stats = strata.get(ALL_STRATUM)
        if stats is None:
            continue
        offset_stats = stats.feature_stats.get("spline_offset_mm")
        if offset_stats is None:
            continue
        result[level_name] = {
            "count": offset_stats.count,
            "p99": offset_stats.percentiles.get("p99"),
        }
    return result


def _level_attaining_p(p99_by_level: Dict[str, Dict[str, Any]], qualifying_levels: Sequence[str]) -> Optional[str]:
    best_level = None
    best_p99 = None
    for level_name in qualifying_levels:
        p99 = p99_by_level[level_name]["p99"]
        if best_p99 is None or p99 > best_p99:
            best_p99 = p99
            best_level = level_name
    return best_level


def _population_stats(values: Sequence[float]) -> Dict[str, Any]:
    """Cheap count/max/p99 summary over *values* (empty-safe)."""
    if not values:
        return {"count": 0, "max": None, "p99": None}
    ordered = sorted(values)
    n = len(ordered)
    # Nearest-rank p99 -- adequate for a diagnostic summary (not the
    # artifact's own percentile machinery, which reference/aggregate.py owns).
    rank = max(0, min(n - 1, math.ceil(0.99 * n) - 1))
    return {"count": n, "max": ordered[-1], "p99": ordered[rank]}


def _terminal_interior_counts(cohort_ingest) -> Dict[str, int]:
    """Exact terminal/interior occurrence counts (AC17), derived from
    ``ingest_cohort``'s own per-subject record counts rather than a second
    feature-extraction pass: every subject with `n >= 2` present, recognised
    levels contributes exactly 2 terminal occurrences (its cranial-most and
    caudal-most present level -- or all `n` when `n == 2`,
    `features/spline_offset.py`'s AC37) and `max(0, n - 2)` interior ones.
    A subject with fewer than 2 levels contributes neither (no stage3, hence
    no offset at all)."""
    terminal_count = 0
    interior_count = 0
    for subject in cohort_ingest.subjects:
        n = len(subject.records)
        if n < 2:
            continue
        terminal_count += min(n, 2)
        interior_count += max(0, n - 2)
    return {"terminal_count": terminal_count, "interior_count": interior_count}


def _calibration_block(distribution, cohort_ingest, threshold: float) -> Dict[str, Any]:
    """Build the ``calibration`` summary block (AC17).

    ``p99_by_level`` / ``P`` are read from the built (interior-only, AC41)
    ``distribution``, so the threshold derivation is unaffected by the
    terminal exclusion. ``terminal_count`` / ``interior_count`` make the
    exclusion's evidence regenerable: derived from ``ingest_cohort``'s own
    per-subject record counts (see :func:`_terminal_interior_counts`), since
    ``reference/ingest.py`` deliberately discards a terminal offset's *value*
    before it reaches a ``FeatureRecord`` (AC41). ``interior_stats`` is a
    genuine population summary over the exact values the artifact was built
    from (after the :data:`EXCLUDED_OFFSETS` withholding).
    """
    p99_by_level = _p99_by_level(distribution)
    qualifying_levels = sorted(
        name for name, entry in p99_by_level.items() if entry["count"] >= _MIN_QUALIFYING_COUNT
    )
    p_value = None
    if qualifying_levels:
        p_value = max(p99_by_level[name]["p99"] for name in qualifying_levels)
    level_at_p = _level_attaining_p(p99_by_level, qualifying_levels) if qualifying_levels else None

    subject_level_offsets: List[Dict[str, Any]] = []
    for subject in cohort_ingest.subjects:
        for record in subject.records:
            value = record.features.get("spline_offset_mm")
            if value is not None:
                subject_level_offsets.append(
                    {"subject_id": subject.subject_id, "level_name": record.level_name, "offset_mm": value}
                )

    total = len(subject_level_offsets)
    above = sum(1 for entry in subject_level_offsets if entry["offset_mm"] >= threshold)
    fraction = (above / total) if total else 0.0

    top = sorted(subject_level_offsets, key=lambda e: e["offset_mm"], reverse=True)[:10]
    top_subject_ids = [entry["subject_id"] for entry in top]

    counts = _terminal_interior_counts(cohort_ingest)
    interior_stats = _population_stats([entry["offset_mm"] for entry in subject_level_offsets])

    return {
        "status": "ran" if qualifying_levels or p99_by_level else "skipped",
        "p99_by_level": p99_by_level,
        "qualifying_levels": qualifying_levels,
        "P": p_value,
        "level_at_p": level_at_p,
        "threshold": threshold,
        "subject_levels_above_threshold": {"count": above, "fraction": fraction},
        "top_subject_ids": top_subject_ids,
        "terminal_count": counts["terminal_count"],
        "interior_count": counts["interior_count"],
        "interior_stats": interior_stats,
        "terminal_stats_note": (
            "terminal offset values are excluded before reaching a "
            "FeatureRecord (reference/ingest.py, AC41), so only their "
            "occurrence count is regenerable from this tool; see the item "
            "123 Decisions log for the one-off per-vertebra analysis that "
            "measured their magnitude."
        ),
    }


def _withhold_excluded_offsets(cohort_ingest):
    """Drop the :data:`EXCLUDED_OFFSETS` ``spline_offset_mm`` readings.

    Returns ``(CohortIngest, excluded)`` where ``excluded`` lists each drop as
    ``{case_id, level_name, offset_mm}``. The matching record keeps its other
    features; every other record and level is untouched.
    """
    from dataclasses import replace

    from segfacet.reference.ingest import CohortIngest

    excluded: List[Dict[str, Any]] = []
    subjects = []
    for subject in cohort_ingest.subjects:
        records = []
        for record in subject.records:
            if (
                (subject.subject_id, record.level_name) in EXCLUDED_OFFSETS
                and "spline_offset_mm" in record.features
            ):
                features = dict(record.features)
                excluded.append(
                    {
                        "case_id": subject.subject_id,
                        "level_name": record.level_name,
                        "offset_mm": features.pop("spline_offset_mm"),
                    }
                )
                record = replace(record, features=features)
            records.append(record)
        subjects.append(replace(subject, records=tuple(records)))
    subjects = tuple(subjects)
    return (
        CohortIngest(
            subjects=subjects,
            records=tuple(r for s in subjects for r in s.records),
            size_proxy_name=cohort_ingest.size_proxy_name,
        ),
        excluded,
    )


# =========================================================================== #
# Orchestration
# =========================================================================== #


def _empty_summary(status: str, reason: Optional[str], roots: Dict[str, Optional[str]]) -> Dict[str, Any]:
    """The summary of a run that built nothing (``skipped`` or ``error``)."""
    return {
        "cohort": {
            "status": status,
            "reason": reason,
            "roots": roots,
            "role_counts": {},
            "case_ids": [],
            "subjects_without_scan": [],
        },
        "build": {"status": "skipped", "artifact_path": None, "subject_count": 0, "levels": [], "config_hash": None},
        "calibration": {
            "status": "skipped", "p99_by_level": {}, "qualifying_levels": [], "P": None,
            "level_at_p": None, "threshold": _FLOOR_MM,
            "subject_levels_above_threshold": {"count": 0, "fraction": 0.0},
            "top_subject_ids": [], "terminal_count": 0, "interior_count": 0,
            "interior_stats": {"count": 0, "max": None, "p99": None},
            "excluded_offsets": [],
            "terminal_stats_note": "cohort skipped -- no offsets computed",
        },
    }


def run_rebuild(
    *,
    out_dir: "Path | str",
    verse_cohort: Optional[str] = None,
    verse20_cohort: Optional[str] = None,
    build_date: str = "2026-10-18",
    max_cases: Optional[int] = None,
    jobs: int = 1,
) -> Dict[str, Any]:
    """Orchestrate root resolution, the role-overlap guard, ingest, build and
    calibration.

    An unresolved, missing or empty release is always a structured skip.
    :class:`RoleOverlapError` propagates (``main`` turns it into exit ``1``).
    Writes only under *out_dir*. Returns the summary dict.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    roots = {
        "verse19": resolve_root(verse_cohort, ENV_VAR),
        "verse20": resolve_root(verse20_cohort, ENV_VAR_V20),
    }
    root_strs = {k: (str(v) if v is not None else None) for k, v in roots.items()}

    for key, env_var, flag in (
        ("verse19", ENV_VAR, "--verse-cohort"),
        ("verse20", ENV_VAR_V20, "--verse20-cohort"),
    ):
        root = roots[key]
        if root is None:
            return _empty_summary("skipped", f"no {key} cohort root: pass {flag} or set {env_var}", root_strs)
        if not root.exists():
            return _empty_summary("skipped", f"{key} cohort root does not exist: {root} ({env_var})", root_strs)

    from segfacet.datasets import bundled_descriptor_path, load_descriptor, resolve

    sources = [
        (load_descriptor(bundled_descriptor_path("verse19.yaml")), roots["verse19"]),
        (load_descriptor(bundled_descriptor_path("verse20.yaml")), roots["verse20"]),
    ]
    cohort = development_cohort(sources)  # RoleOverlapError propagates

    role_counts = {
        key: {role: len(resolve(desc, data_root=root, subset=role)) for role in _ROLES}
        for key, (desc, root) in zip(("verse19", "verse20"), sources)
    }
    if any(counts["development"] == 0 for counts in role_counts.values()):
        empty = [k for k, c in role_counts.items() if c["development"] == 0]
        summary = _empty_summary("skipped", f"empty development role: {', '.join(empty)}", root_strs)
        summary["cohort"]["role_counts"] = role_counts
        return summary

    if max_cases is not None:
        from segfacet.datasets import Cohort

        cohort = Cohort(cases=cohort.cases[:max_cases], name=cohort.name)

    from segfacet.config import bundled_default_config
    from segfacet.reference import Provenance, aggregate_reference, config_hash, write_artifact
    from segfacet.reference.ingest import ingest_dataset_cohort

    config = bundled_default_config()
    cohort_ingest = ingest_dataset_cohort(
        cohort,
        config=config,
        with_size_proxy=False,
        with_intensity=True,
        with_morphology=True,
        jobs=jobs,
    )
    cohort_ingest, excluded = _withhold_excluded_offsets(cohort_ingest)

    provenance = Provenance(
        source="verse-v1",
        config_hash=config_hash(config),
        build_date=build_date,
        size_proxy_name=None,
        case_ids=cohort.case_ids,
    )
    distribution = aggregate_reference(cohort_ingest.records, provenance=provenance)

    artifact_path = out_path / "reference_verse_v1.json"
    write_artifact(distribution, artifact_path)

    threshold = derive_max_offset_mm(distribution)
    calibration_block = _calibration_block(distribution, cohort_ingest, threshold)
    calibration_block["excluded_offsets"] = excluded

    return {
        "cohort": {
            "status": "ran",
            "reason": None,
            "roots": root_strs,
            "role_counts": role_counts,
            "case_ids": list(cohort.case_ids),
            "subjects_without_scan": [c.case_id for c in cohort if c.scan_path is None],
        },
        "build": {
            "status": "ran",
            "artifact_path": str(artifact_path),
            "subject_count": distribution.subject_count,
            "levels": sorted(distribution.levels.keys()),
            "config_hash": distribution.provenance.config_hash,
        },
        "calibration": calibration_block,
    }


# =========================================================================== #
# CLI
# =========================================================================== #


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rebuild_verse_reference",
        description=(
            "Rebuild reference_verse_v1.json from the development role of the "
            "VerSe19 and VerSe20 releases, refusing any role overlap, and derive "
            "the spline_offset.max_offset_mm threshold."
        ),
    )
    parser.add_argument("--out", required=True, metavar="<dir>", help="Output directory.")
    parser.add_argument(
        "--verse-cohort",
        default=None,
        metavar="<dir>",
        help=f"VerSe19 three-split root. Defaults to the {ENV_VAR} environment variable.",
    )
    parser.add_argument(
        "--verse20-cohort",
        default=None,
        metavar="<dir>",
        help=f"VerSe20 three-split root. Defaults to the {ENV_VAR_V20} environment variable.",
    )
    parser.add_argument(
        "--build-date",
        default="2026-10-18",
        metavar="<YYYY-MM-DD>",
        help=(
            "Caller-supplied ISO build date stamped into provenance. The fixed "
            "default (%(default)s) keeps test runs deterministic; pass the "
            "actual date for a real rebuild."
        ),
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        metavar="<n>",
        help="Cap the merged development cohort, in case-id order (smoke runs only).",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        metavar="<n>",
        help="Ingest cases in <n> parallel processes (default: %(default)s).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    if args.jobs < 1:
        parser.error("--jobs must be >= 1")

    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)

    from segfacet.datasets import DatasetSchemaError

    code = 0
    try:
        summary = run_rebuild(
            out_dir=out_path,
            verse_cohort=args.verse_cohort,
            verse20_cohort=args.verse20_cohort,
            build_date=args.build_date,
            max_cases=args.max_cases,
            jobs=args.jobs,
        )
    except (RoleOverlapError, DatasetSchemaError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        summary = _empty_summary("error", str(exc), {})
        code = 1

    if summary["build"]["status"] != "ran":
        # Never leave an earlier run's artifact beside a "no artifact" summary.
        (out_path / "reference_verse_v1.json").unlink(missing_ok=True)

    summary_path = out_path / _SUMMARY_NAME
    summary_path.write_bytes(
        (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )

    print(
        "rebuild_verse_reference: cohort={} build={} calibration={} "
        "-> summary written to {}".format(
            summary["cohort"]["status"],
            summary["build"]["status"],
            summary["calibration"]["status"],
            summary_path,
        )
    )

    return code


if __name__ == "__main__":
    raise SystemExit(main())
