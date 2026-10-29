"""WP4.3a: real writer provenance acceptance and failure-text redaction regressions."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image as PILImage

import headless_export as he
from clearwater.app import composition
from clearwater.interfaces import ParameterSet, Settings
from clearwater.io.photo.png import PROVENANCE_KEYWORD


def _writer_provenance(sample, tmp_path: Path) -> tuple[Path, ParameterSet, Path]:
    """Export a synthetic nclx HEIC on CPU and extract its actual PNG iTXt provenance."""
    source = sample("heic8-gradient-none")
    out = tmp_path / "first-export"
    out.mkdir()
    parameters = he.parameters_for()
    requests = he.requests_for(
        [source], parameters=parameters, settings=Settings(output_folder=out, force_cpu=True)
    )
    record = he.run(requests, exports=composition.export_jobs(), footage_folder=None)
    (item,) = record.report.items
    assert item.result is not None and item.result.ok, item.result and item.result.failure
    (output,) = item.result.outputs
    with PILImage.open(output) as image:
        text = image.text[PROVENANCE_KEYWORD]
    written = json.loads(text)
    assert written["profile"] == "built-in sRGB"
    assert written["method"] == parameters.method and written["parameters"]
    expected = ParameterSet(
        written["method"],
        written["parameters"],
        datetime.fromisoformat(written["created"]),
        written["app_version"],
    )
    sidecar = tmp_path / "writer-provenance.json"
    sidecar.write_text(text, encoding="utf-8")
    return sidecar, expected, source


def test_parameters_accept_writer_provenance(sample, tmp_path: Path, monkeypatch, capsys) -> None:
    """DR-76: --parameters must accept the same actual writer provenance the store imports."""
    sidecar, parameters, source = _writer_provenance(sample, tmp_path)
    out = tmp_path / "cli-export"
    out.mkdir()
    monkeypatch.setattr(he, "configured_footage_folder", lambda: None)
    record = tmp_path / "record.json"
    status = he.main(
        [
            str(source),
            "--out",
            str(out),
            "--force-cpu",
            "--parameters",
            str(sidecar),
            "--record",
            str(record),
        ],
        exports=composition.export_jobs(),
    )
    assert status == 0, capsys.readouterr().err
    assert he.read_parameter_file(sidecar) == parameters
    assert len(list(out.glob("*.png"))) == 1
    assert json.loads(record.read_text(encoding="ascii"))["parameters_from"] == "file"


def _mixed_path(folder: Path) -> str:
    """Spell a known path using alternating slash and backslash separators."""
    parts = folder.as_posix().split("/")
    text = parts[0]
    for index, part in enumerate(parts[1:]):
        text += ("/" if index % 2 == 0 else "\\") + part
    assert "/" in text and "\\" in text
    return text


@pytest.mark.parametrize("form", ["raw", "doubled", "ascii", "ascii-doubled", "quoted"])
def test_redactor_matches_mixed_separators(tmp_path: Path, form: str) -> None:
    """DR-81 (a): every separator varies independently, including quoted/escaped text."""
    folder = tmp_path / "private-parent" / "priv\u00e9's-out"
    mixed = _mixed_path(folder)
    spelling = {
        "raw": mixed,
        "doubled": mixed.replace("\\", "\\\\"),
        "ascii": he.ascii_text(mixed),
        "ascii-doubled": he.ascii_text(mixed).replace("\\", "\\\\"),
        "quoted": mixed.replace("'", r"\'"),
    }[form]
    redact = he.Redactor([folder.parent, folder])
    assert redact(f"refused {spelling}/child.png") == (
        f"refused {he.ascii_text(folder.name)}/child.png"
    )


def test_argparse_redacts_mixed_separators(tmp_path: Path, monkeypatch, capsys) -> None:
    """DR-81 (a): argparse's quoted invalid value must hide a known folder's parent."""
    folder = tmp_path / "private-parent" / "out"
    folder.mkdir(parents=True)
    mixed = _mixed_path(folder)

    def unexpected():
        pytest.fail("argparse refusal must precede configuration lookup")

    monkeypatch.setattr(he, "configured_footage_folder", unexpected)
    assert he.main([str(tmp_path / "missing.jpg"), "--out", str(folder), "--bit-depth", mixed]) == 2
    captured = capsys.readouterr()
    assert "invalid int value" in captured.err and folder.name in captured.err
    assert "private-parent" not in captured.err
    assert not captured.out and "Traceback" not in captured.err


@pytest.mark.parametrize("error", [OSError, RuntimeError])
def test_raising_footage_resolution_is_a_usage_refusal(
    tmp_path: Path, monkeypatch, capsys, error
) -> None:
    """DR-81 (b): resolving an unknown footage folder must refuse without its raw path."""
    private = tmp_path / "hidden-private-parent" / "footage"
    out = tmp_path / "out"
    out.mkdir()
    real_resolve = Path.resolve

    def resolve(path, *args, **kwargs):
        if path == private:
            raise error(f"cannot resolve {private}")
        return real_resolve(path, *args, **kwargs)

    def configured():
        return private.resolve()

    def unexpected(*args, **kwargs):
        pytest.fail("no request or export may begin after a footage resolution failure")

    monkeypatch.setattr(Path, "resolve", resolve)
    monkeypatch.setattr(he, "configured_footage_folder", configured)
    monkeypatch.setattr(he, "requests_for", unexpected)
    monkeypatch.setattr(he, "run", unexpected)
    assert he.main([str(tmp_path / "missing.jpg"), "--out", str(out)]) == 2
    captured = capsys.readouterr()
    assert "headless_export" in captured.err and "footage" in captured.err
    assert "hidden-private-parent" not in captured.err and str(tmp_path) not in captured.err
    assert "Traceback" not in captured.err and captured.err.isascii()
    assert not captured.out and not list(out.iterdir())
