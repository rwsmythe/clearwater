"""WP4.2b: the real export route refuses a stream output name readably."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import headless_export as he
from clearwater.app import composition
from clearwater.config import new_parameter_set
from clearwater.interfaces import Settings


@pytest.mark.parametrize("preflight", [False, True], ids=["engine", "before-jobs"])
def test_naming_refusal_is_readable_and_writes_nothing(
    sample, tmp_path, monkeypatch, capsys, caplog, preflight
):
    """Refuse a real JPEG stream before writing, preserving both source data streams."""
    if sys.platform != "win32":
        pytest.skip("real alternate-data-stream source requires Windows NTFS")
    source_folder, out, cwd, footage = (
        tmp_path / name for name in ("src", "out", "cwd", "footage")
    )
    for folder in (source_folder, out, cwd, footage):
        folder.mkdir()
    carrier = source_folder / "carrier"
    carrier_data = b"source carrier"
    carrier.write_bytes(carrier_data)
    source = Path(f"{carrier}:input.jpg")
    stream_data = sample("jpeg-gradient-srgb").read_bytes()
    try:
        source.write_bytes(stream_data)
        assert source.read_bytes() == stream_data
    except OSError as exc:
        pytest.skip(f"alternate data stream creation unavailable: {type(exc).__name__}")
    assert source.name == "carrier:input.jpg"
    monkeypatch.chdir(cwd)
    requests = he.requests_for(
        [source],
        parameters=new_parameter_set("c3", {}),
        settings=Settings(output_folder=out, force_cpu=True),
    )

    exports = composition.export_jobs()
    if preflight:
        calls = []
        real_job = exports.job

        def job(request):
            calls.append(request)
            return real_job(request)

        monkeypatch.setattr(exports, "job", job)
        monkeypatch.setattr(he, "configured_footage_folder", lambda: footage)
        assert he.main([str(source), "--out", str(out), "--force-cpu"], exports=exports) == 2
        assert not calls
        captured = capsys.readouterr()
        text = "\n".join([captured.out, captured.err, caplog.text])
        assert source.name in text
        assert "must be a single portable name component" in text
    else:
        record = he.run(requests, exports=exports, footage_folder=None)
        assert len(record.report.items) == 1
        item = record.report.items[0]
        assert item.state == "failed", item.result
        assert item.result is not None
        assert not item.result.outputs
        failure = item.result.failure
        assert failure is not None
        assert failure.startswith(f"{source.name}: OutputNameError: "), failure
        captured = capsys.readouterr()
        text = "\n".join(
            [failure, *he.summary_lines(record), captured.out, captured.err, caplog.text]
        )

    assert carrier.read_bytes() == carrier_data
    assert source.read_bytes() == stream_data
    assert not list(out.iterdir())
    assert not list(cwd.iterdir())
    assert not list(footage.iterdir())
    assert str(tmp_path) not in text
    assert "Traceback" not in text
