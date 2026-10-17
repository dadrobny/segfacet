"""Item 239: the corpus regeneration CLI writes the corpus sheet with the manifest.

Every regeneration writes under ``tmp_path``/``tmp_path_factory``; AC2 and the
explicit-out case monkeypatch ``CORPUS_DIR`` and ``SHEET_PATH`` to temporary
paths first, so the committed ``tests/corpus/`` and
``docs/aide/corpus_sheet.png`` are never written.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import sys
from pathlib import Path

import pytest
from run_process import run_utf8

from segfacet.synth import corpus, corpus_sheet


def _source_chunk(png_path: Path) -> str:
    from PIL import Image

    with Image.open(png_path) as img:
        return img.text["Source"]


def _expected_source(out_dir: Path) -> str:
    manifest_path = out_dir / "manifest.json"
    h = hashlib.sha256()
    h.update(manifest_path.read_bytes())
    for case in corpus.load_manifest(manifest_path)["cases"]:
        h.update((out_dir / case["seg_fixture"]).read_bytes())
    return "sha256:" + h.hexdigest()


@pytest.fixture(scope="module")
def no_matplotlib_run(tmp_path_factory):
    out = tmp_path_factory.mktemp("no_matplotlib")
    stderr = io.StringIO()
    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "matplotlib", None)
        with contextlib.redirect_stderr(stderr):
            rc = corpus.main(["--out", str(out)])
    return out, rc, stderr.getvalue()


def test_ac1_regeneration_writes_a_sheet_matching_its_manifest(tmp_path):
    corpus.main(["--out", str(tmp_path)])

    sheet = tmp_path / "corpus_sheet.png"
    assert sheet.is_file()
    assert _source_chunk(sheet) == _expected_source(tmp_path)


def test_ac2_default_regeneration_writes_the_committed_sheet_path(tmp_path, monkeypatch):
    c = tmp_path / "corpus"
    s = tmp_path / "sheet" / "corpus_sheet.png"
    s.parent.mkdir()
    monkeypatch.setattr(corpus, "CORPUS_DIR", c)
    monkeypatch.setattr(corpus_sheet, "SHEET_PATH", s)

    corpus.main([])

    assert s.is_file()
    assert _source_chunk(s) == _expected_source(c)


def test_ac3_without_matplotlib_the_manifest_is_still_written(no_matplotlib_run):
    out, _rc, _stderr = no_matplotlib_run

    manifest = out / "manifest.json"
    assert manifest.is_file()
    written = {c["case_id"] for c in corpus.load_manifest(manifest)["cases"]}
    committed = {c["case_id"] for c in corpus.load_manifest()["cases"]}
    assert committed
    assert written == committed


def test_ac4_without_matplotlib_the_run_names_the_sheet_it_did_not_write(no_matplotlib_run):
    out, _rc, stderr = no_matplotlib_run

    assert str(out / "corpus_sheet.png") in stderr


def test_ac5_without_matplotlib_the_run_exits_non_zero(no_matplotlib_run):
    _out, rc, _stderr = no_matplotlib_run

    assert rc == 1


def test_ac6_importing_the_corpus_module_does_not_import_matplotlib():
    result = run_utf8(
        [
            sys.executable,
            "-c",
            "import sys, segfacet.synth.corpus; print('matplotlib' in sys.modules)",
        ]
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False"


def test_explicit_out_naming_corpus_dir(tmp_path, monkeypatch):
    c = tmp_path / "corpus"
    s = tmp_path / "sheet" / "corpus_sheet.png"
    s.parent.mkdir()
    monkeypatch.setattr(corpus, "CORPUS_DIR", c)
    monkeypatch.setattr(corpus_sheet, "SHEET_PATH", s)

    corpus.main(["--out", str(c)])

    assert s.is_file()
    assert (c / "manifest.json").is_file()
    assert not (c / "corpus_sheet.png").exists()
