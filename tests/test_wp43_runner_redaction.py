"""WP4.3a: real writer provenance acceptance and failure-text redaction regressions."""

from __future__ import annotations

import json
import logging
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


@pytest.mark.parametrize(
    ("route", "error"),
    [
        (route, error)
        for route in (
            "main-settings",
            "main-record",
            "main-cache",
            "main-output",
            "main-late-run",
            "run-output",
            "run-configured",
            "run-cache",
        )
        for error in (OSError, RuntimeError, ValueError)
        # A NUL fails the first real check, so only transient OS/runtime failures can be delayed.
        if not (route == "main-late-run" and error is ValueError)
    ],
)
def test_raising_footage_resolution_is_a_usage_refusal(
    tmp_path: Path, monkeypatch, capsys, error, route: str
) -> None:
    """DR-81 (b): the real write-target resolve must refuse before any export."""
    private = (
        tmp_path / "hidden-private-parent" / ("footage\0" if error is ValueError else "footage")
    )
    out, cache, settings = (tmp_path / name for name in ("out", "cache", "settings"))
    for folder in (out, cache, settings):
        folder.mkdir()
    source = tmp_path / "input.jpg"
    PILImage.new("RGB", (8, 8), (24, 48, 72)).save(source)
    requests = he.requests_for(
        [source],
        parameters=he.parameters_for(),
        settings=Settings(output_folder=out, force_cpu=True),
    )
    real_resolve, real_run = Path.resolve, he.run
    armed = route != "main-late-run"
    reached = []

    def resolve(path, *args, **kwargs):
        if path == private and armed:
            reached.append(path)
            if error is ValueError:
                return real_resolve(path, *args, **kwargs)  # actual embedded-NUL failure
            raise error(f"cannot resolve {private}")
        return real_resolve(path, *args, **kwargs)

    def late_run(*args, **kwargs):
        nonlocal armed
        armed = True
        return real_run(*args, **kwargs)

    def unexpected(*args, **kwargs):
        pytest.fail("no export engine may be constructed after a footage resolution failure")

    monkeypatch.setattr(Path, "resolve", resolve)
    monkeypatch.setattr(he, "configured_footage_folder", lambda: private)
    monkeypatch.setattr(he.composition, "export_jobs", unexpected)
    if route == "main-late-run":
        monkeypatch.setattr(he, "run", late_run)
    if route.startswith("main"):
        argv = [str(source), "--out", str(out), "--force-cpu"]
        argv += {
            "main-settings": ["--settings-dir", str(settings)],
            "main-record": ["--record", str(tmp_path / "record.json")],
            "main-cache": ["--cache-dir", str(cache)],
        }.get(route, [])
        assert he.main(argv) == 2
        captured = capsys.readouterr()
        text = captured.err
        assert "headless_export" in text and not captured.out
    else:
        with pytest.raises(he.RunnerRefusalError) as caught:
            if route == "run-cache":
                he.run([], footage_folder=private, cache_folder=cache)
            elif route == "run-configured":
                he.run(requests)
            else:
                he.run(requests, footage_folder=private)
        text = str(caught.value)
    assert reached, "the product's real Path.resolve check was not reached"
    assert "footage" in text and text.isascii()
    assert "hidden-private-parent" not in text and str(tmp_path) not in text
    assert "Traceback" not in text
    assert not list(out.iterdir()) and not list(cache.iterdir()) and not list(settings.iterdir())
    assert not (tmp_path / "record.json").exists()


@pytest.mark.parametrize("corrupt", ["year-one", "plain-json"])
def test_settings_warning_is_printed_with_file_names_only(
    sample, tmp_path: Path, monkeypatch, capsys, corrupt
) -> None:
    """A CLI-owned warning handler must show corrupt settings by basename and then detach."""
    from clearwater.config import new_parameter_set, save_settings

    folder = tmp_path / "private-settings-parent" / "settings"
    folder.mkdir(parents=True)
    path = save_settings(folder, Settings(last_parameters=new_parameter_set("c3", {})))
    if corrupt == "year-one":
        data = json.loads(path.read_text(encoding="utf-8"))
        data["last_parameters"]["created"] = "0001-01-01T00:00:00+01:00"
        path.write_text(json.dumps(data), encoding="utf-8")
    else:
        path.write_text("{not json", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    logger = logging.getLogger("clearwater")
    before_handlers = tuple(logger.handlers)
    monkeypatch.setattr(he, "configured_footage_folder", lambda: None)
    assert (
        he.main(
            [
                str(sample("jpeg-gradient-srgb")),
                "--out",
                str(out),
                "--force-cpu",
                "--settings-dir",
                str(folder),
            ],
            exports=composition.export_jobs(),
        )
        == 0
    )
    err = capsys.readouterr().err
    assert "settings file settings.json " in err and "using defaults" in err
    assert err.count("settings file settings.json ") == 1
    assert "private-settings-parent" not in err and str(tmp_path) not in err
    assert "settings\\settings.json" not in err and "settings/settings.json" not in err
    assert tuple(logger.handlers) == before_handlers


def test_unusable_settings_output_warning_hides_the_private_value(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """R3-1 (ii): the per-field warning must not disclose a path unknown to Redactor."""
    settings_folder, out = tmp_path / "settings", tmp_path / "out"
    settings_folder.mkdir()
    out.mkdir()
    data = json.loads(Settings(output_suffix="_kept", force_cpu=True).to_json())
    data["output_folder"] = str(tmp_path / "unknown-private-output-parent" / "out\0")
    settings_file = settings_folder / "settings.json"
    original = json.dumps(data).encode("utf-8")
    settings_file.write_bytes(original)
    source = tmp_path / "input.jpg"
    PILImage.new("RGB", (8, 8), (24, 48, 72)).save(source)
    monkeypatch.setattr(he, "configured_footage_folder", lambda: None)
    assert (
        he.main(
            [str(source), "--out", str(out), "--settings-dir", str(settings_folder)],
            exports=composition.export_jobs(),
        )
        == 0
    )
    captured = capsys.readouterr()
    assert captured.err.count("settings: output_folder=") == 1
    assert "is out of range; using the default" in captured.err
    assert "unknown-private-output-parent" not in captured.err and str(tmp_path) not in captured.err
    assert "\x00" not in captured.err and r"\x00" not in captured.err
    assert settings_file.read_bytes() == original
    assert not list(settings_folder.glob("settings.json.bad-*"))
    assert [p.name for p in out.iterdir()] == ["input_kept.png"]
