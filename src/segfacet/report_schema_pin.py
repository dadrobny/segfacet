"""Pin tying the report schema version to the feature leaf paths (item 233).

``report_schema_pin.json`` holds one pair: the report ``schema_version`` and the
sorted set of feature leaf paths that version describes (the union of
``catalogue.iter_leaf_paths(record)`` over ``catalogue.iter_driver_records()``).
:func:`pin_conflicts` compares the live pair with the pin; the suite calls it,
so a path added, removed or renamed without re-pinning fails.

Re-pin only with ``python -m segfacet.report_schema_pin``: it refuses when the
path set changed and the version did not. Limit: a hand edit of the pin file
under an unchanged version is not detectable without git history, so ``repin``
is the only documented route, not an enforced one.

Scope fence: changes no extractor, rule, catalogue or report shape.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

__all__ = ["PIN_PATH", "PinError", "live_leaf_paths", "pin_conflicts", "repin", "main"]

PIN_PATH = Path(__file__).resolve().parent / "report_schema_pin.json"

_REMEDY = (
    "Bump REPORT_SCHEMA_VERSION and the schema const, then run "
    "`python -m segfacet.report_schema_pin`, then regenerate "
    "tests/golden/report_format_contract.json with "
    "`python -m tests.report_format_fixture`."
)


class PinError(ValueError):
    """Raised when a re-pin would change the path set under an unchanged version."""


def live_leaf_paths() -> frozenset[str]:
    from segfacet import catalogue

    paths: set[str] = set()
    for _name, record in catalogue.iter_driver_records():
        paths |= catalogue.iter_leaf_paths(record)
    return frozenset(paths)


def _defaults(live_paths, report_version):
    if live_paths is None:
        live_paths = live_leaf_paths()
    if report_version is None:
        from segfacet.report import REPORT_SCHEMA_VERSION

        report_version = REPORT_SCHEMA_VERSION
    return frozenset(live_paths), report_version


def _diff(pinned: frozenset[str], live: frozenset[str]) -> str:
    return f"added {sorted(live - pinned)}, removed {sorted(pinned - live)}"


def _read_pin(pin_path: Path) -> tuple[str, frozenset[str]]:
    data = json.loads(Path(pin_path).read_text(encoding="utf-8"))
    return data["schema_version"], frozenset(data["feature_leaf_paths"])


def pin_conflicts(*, live_paths=None, report_version=None, pin_path=PIN_PATH) -> tuple[str, ...]:
    live, version = _defaults(live_paths, report_version)
    try:
        pinned_version, pinned = _read_pin(pin_path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return (f"report schema pin {pin_path} is missing or unreadable ({exc}). {_REMEDY}",)
    out = []
    if not live:
        out.append(f"the live feature leaf-path set is empty. {_REMEDY}")
    if pinned_version != version:
        out.append(
            f"pinned report schema version {pinned_version!r} differs from "
            f"REPORT_SCHEMA_VERSION {version!r}. {_REMEDY}"
        )
    if pinned != live:
        out.append(f"pinned feature leaf paths differ from live: {_diff(pinned, live)}. {_REMEDY}")
    return tuple(out)


def repin(*, live_paths=None, report_version=None, pin_path=PIN_PATH) -> None:
    live, version = _defaults(live_paths, report_version)
    pin_path = Path(pin_path)
    if pin_path.exists():
        try:
            pinned_version, pinned = _read_pin(pin_path)
        except (OSError, ValueError, KeyError, TypeError):
            pinned_version, pinned = None, live
        if pinned_version == version and pinned != live:
            raise PinError(
                f"feature leaf paths changed under unchanged report schema version "
                f"{version!r}: {_diff(pinned, live)}. Bump REPORT_SCHEMA_VERSION and "
                "the schema const first."
            )
    text = json.dumps({"schema_version": version, "feature_leaf_paths": sorted(live)}, indent=2) + "\n"
    pin_path.write_bytes(text.encode("utf-8"))


def main(argv=None) -> int:
    try:
        repin()
    except PinError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
