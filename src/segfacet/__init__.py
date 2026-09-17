"""segfacet — automated quality control for vertebra instance segmentations.

This package provides an explainable, reference-grounded heuristic QC gate for
spine-segmentation label maps. See ``docs/aide/vision.md`` for the full vision.

This module is the single source of truth for the package version; the build
backend reads ``__version__`` from here (see ``[tool.hatch.version]`` in
``pyproject.toml``).

``check_empty``/``CheckResult`` and ``compute_fragmentation_index`` are
resolved lazily (PEP 562) because their defining modules pull in NumPy/SciPy/
NiBabel; the other re-exports below are cheap and stay eager.
"""

import importlib

__version__ = "0.0.1"

from segfacet.verdict import Reason, Severity, Verdict  # noqa: E402
from segfacet.report import serialize_report, serialize_report_json  # noqa: E402
from segfacet.human_report import render_feature_table, render_human_report  # noqa: E402
from segfacet.feature_report import build_features_block  # noqa: E402

_LAZY_ATTRS = {
    "check_empty": "segfacet.empty",
    "CheckResult": "segfacet.empty",
    "compute_fragmentation_index": "segfacet.features.fragmentation",
}


def __getattr__(name):
    module_name = _LAZY_ATTRS.get(name)
    if module_name is None:
        raise AttributeError(f"module 'segfacet' has no attribute {name!r}")
    module = importlib.import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


__all__ = [
    "__version__",
    "Severity",
    "Reason",
    "Verdict",
    "CheckResult",
    "check_empty",
    "serialize_report",
    "serialize_report_json",
    "render_human_report",
    "render_feature_table",
    "build_features_block",
    "compute_fragmentation_index",
]
