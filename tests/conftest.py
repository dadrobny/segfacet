"""Shared pytest fixtures exposing the synthetic NIfTI cases (item 002).

These are thin wrappers over the framework-agnostic builders in
``tests/synthetic.py``. Every test module — in this item and in later items
(loader, label convention, CLI, empty detection, …) — can request these
fixtures by name without importing ``synthetic`` directly.

In-memory fixtures yield a :class:`synthetic.SyntheticCase` bundle. The
``*_files`` fixtures additionally materialise the case under pytest's
``tmp_path`` and yield ``(scan_path, seg_path)`` so on-disk consumers (e.g. the
CLI in item 006) get real ``.nii.gz`` files to load.

Also hosts the shared Docker-gating helpers and the session-scoped item-066
image-build fixture (promoted here from ``tests/test_066_dockerfile.py`` by
item 069) so every Docker-gated test module in the suite -- item 066's own
image-contract checks and item 069's container smoke test -- builds the
``segfacet:test-066`` image **at most once** per test session.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from synthetic import (
    SyntheticCase,
    anisotropic_case,
    empty_case,
    labelled_blocks_case,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


# --- In-memory case bundles -------------------------------------------------


@pytest.fixture
def labelled_blocks() -> SyntheticCase:
    """Labelled-blocks case: >=3 separated labels, isotropic 1 mm spacing."""
    return labelled_blocks_case()


@pytest.fixture
def empty_labelmap() -> SyntheticCase:
    """Empty case: an all-zero label map (no foreground) + matching scan."""
    return empty_case()


@pytest.fixture
def anisotropic() -> SyntheticCase:
    """Anisotropic case: labelled volume with non-uniform (1,1,3) mm spacing."""
    return anisotropic_case()


# --- On-disk variants (function-scoped, written under tmp_path) -------------


@pytest.fixture
def labelled_blocks_files(labelled_blocks, tmp_path):
    """Write the labelled-blocks case and yield ``(scan_path, seg_path)``."""
    return labelled_blocks.write(tmp_path, suffix=".nii.gz")


@pytest.fixture
def empty_labelmap_files(empty_labelmap, tmp_path):
    """Write the empty case and yield ``(scan_path, seg_path)``."""
    return empty_labelmap.write(tmp_path, suffix=".nii.gz")


@pytest.fixture
def anisotropic_files(anisotropic, tmp_path):
    """Write the anisotropic case and yield ``(scan_path, seg_path)``."""
    return anisotropic.write(tmp_path, suffix=".nii.gz")


# --- Docker-gating helpers & shared image-build fixture (items 066/069) ----


def _docker_available() -> bool:
    """True iff a Docker daemon is reachable **and** can run Linux containers.

    The image under test (item 066) is a Linux image (``FROM python:3.11-slim``),
    so a daemon in *Windows-containers* mode -- which the Windows GitHub
    runners default to -- cannot build it (``docker build`` fails with "no
    matching manifest for windows/amd64"). That is an environmental
    limitation, not a Dockerfile defect, so it must gate these tests to a
    clean skip rather than letting the build fail. We therefore require the
    server OS to be ``linux``; the dedicated Linux CI job (and Linux/macOS dev
    hosts with Docker Desktop in Linux-container mode) satisfies this, while a
    Windows-container daemon reports ``windows`` and is treated as unavailable.
    """
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Os}}"],
            capture_output=True,
            timeout=15,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    return result.stdout.strip() == "linux"


requires_docker = pytest.mark.skipif(
    not _docker_available(),
    reason="docker CLI/daemon not available on this host",
)


@pytest.fixture(scope="session")
def docker_image_tag():
    """Build the item-066 image once per test session and yield its tag.

    Shared by ``test_066_dockerfile.py`` and ``test_069_container_smoke.py``
    (item 069) so the two modules trigger a single ``docker build`` per
    session rather than one each.

    Skips (does not fail) when Docker is unavailable, or when the build
    itself fails for environmental reasons (e.g. no network to pull the
    base image) -- the goal is to keep the default suite Docker-optional
    and green, while still failing loudly on a genuine Dockerfile defect
    when Docker *is* available and functioning.
    """
    if not _docker_available():
        pytest.skip("docker CLI/daemon not available on this host")

    tag = "segfacet:test-066"
    try:
        result = subprocess.run(
            ["docker", "build", "-t", tag, "."],
            cwd=str(REPO_ROOT),
            capture_output=True,
            timeout=1800,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        pytest.skip(f"docker build could not run in this environment: {exc}")

    if result.returncode != 0:
        pytest.fail(
            "docker build failed (AC9):\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    return tag


# --- Session-scoped work fixtures (item 170, insight 2026-09-18) -----------
#
# The 2026-09-18 measurement in docs/aide/insights.md found 11 in-process
# `aide check` runs (11-13s each) and 33 specification/traceability
# regenerations (7-27s each) across the suite. Each of the three fixtures
# below does its expensive work at most once per pytest worker; the logic
# lives in tests/session_artifacts.py and these are thin wrappers over it.


@pytest.fixture(scope="session")
def aide_check_result():
    """One in-process ``aide check`` run, shared by every consumer (item 170,
    insight 2026-09-18)."""
    import session_artifacts

    return session_artifacts.load_aide_check_result()


@pytest.fixture(scope="session")
def regenerated_failure_modes(tmp_path_factory):
    """Two runs of ``segfacet.failure_modes.main``, shared by every consumer
    (item 170, insight 2026-09-18)."""
    import session_artifacts
    import segfacet.failure_modes as fm

    return session_artifacts.regenerate(
        fm.main, fm.JSON_PATH, fm.MD_PATH, tmp_path_factory.mktemp("failure_modes")
    )


@pytest.fixture(scope="session")
def regenerated_traceability(tmp_path_factory):
    """Two runs of ``segfacet.traceability.main``, shared by every consumer
    (item 170, insight 2026-09-18)."""
    import session_artifacts
    import segfacet.traceability as traceability

    return session_artifacts.regenerate(
        traceability.main,
        traceability.JSON_PATH,
        traceability.MD_PATH,
        tmp_path_factory.mktemp("traceability"),
    )
