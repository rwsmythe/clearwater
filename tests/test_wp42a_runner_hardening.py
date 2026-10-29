"""WP4.2a runner guard, quoted-folder redaction and bit-pattern regression controls.

All writable inputs, outputs and filesystem links are per-test stand-ins under
``tmp_path``. No test reads the configured footage folder or requires Qt or a GPU.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import headless_export as he
from clearwater.app import composition
from clearwater.config import new_parameter_set
from clearwater.interfaces import JobResult, Settings


class _Jobs:
    """Count jobs without opening a source or writing an output."""

    def __init__(self, inner=None, failure="stand-in failure"):
        self.calls = []
        self.inner = inner
        self.failure = failure

    def job(self, request):
        self.calls.append(request)
        if self.inner is not None:
            return self.inner.job(request)

        def job(progress):
            return JobResult(False, (), (), self.failure, "none", 0.0)

        return job


def _folders(tmp_path):
    footage, out, src = (tmp_path / name for name in ("footage", "out", "src"))
    for folder in (footage, out, src):
        folder.mkdir()
    return footage, out, src


def _requests(source, out, **changes):
    return he.requests_for(
        [source],
        parameters=new_parameter_set("c3", {}),
        settings=Settings(output_folder=out, force_cpu=True, **changes),
    )


def _assert_stream_refusal(source, out, footage, api, jobs, monkeypatch, capsys):
    if api == "main":
        monkeypatch.setattr(he, "configured_footage_folder", lambda: footage)
        where = ["--beside-source"] if out is None else ["--out", str(out)]
        status = he.main([str(source), *where, "--force-cpu"], exports=jobs)
        assert status == 2, "stream output must be refused before jobs"
        text = capsys.readouterr().err
    else:
        try:
            he.run(_requests(source, out), footage_folder=footage, exports=jobs)
        except he.RunnerRefusalError as exc:
            text = str(exc)
        else:
            pytest.fail("stream output must be refused before jobs")
    assert source.name in text and he.REFUSED_FORM in text
    assert str(source.parent) not in text
    assert not jobs.calls


@pytest.mark.parametrize("api", ["run", "main"])
@pytest.mark.parametrize("extension", ["jpg", "mp4"])
@pytest.mark.parametrize("beside", [False, True], ids=["explicit-out", "beside-source"])
def test_stream_named_output_is_refused_before_jobs(
    tmp_path, monkeypatch, capsys, api, extension, beside
):
    footage, out, src = _folders(tmp_path)
    source = src / f"carrier:input.{extension}"
    _assert_stream_refusal(
        source, None if beside else out, footage, api, _Jobs(), monkeypatch, capsys
    )
    assert not list(out.iterdir()) and not list(src.iterdir())


@pytest.mark.parametrize("api", ["run", "main"])
@pytest.mark.parametrize("extension", ["jpg", "mp4"])
@pytest.mark.parametrize("beside", [False, True], ids=["relative-out", "beside-source"])
def test_drive_relative_output_is_refused_before_jobs(
    tmp_path, monkeypatch, capsys, api, extension, beside
):
    if sys.platform != "win32":
        pytest.skip("drive-relative output planning requires Windows paths")
    footage, out, src = _folders(tmp_path)
    own_drive = src.drive[0].lower()
    other_drive = "z" if own_drive != "z" else "y"
    letter = other_drive if beside else own_drive
    source = Path(f"{src / letter}:input.{extension}")
    assert source.name == f"{letter}:input.{extension}"
    output_folder = None if beside else Path(os.path.relpath(out, footage))
    monkeypatch.chdir(footage)
    requests = _requests(source, output_folder)
    planned = he.final_output_path(source, requests[0].settings, he.MediaKind(requests[0].kind))
    checked = source.parent if beside else output_folder
    assert planned.parent != checked  # RED cause: the joined filename reinterprets its drive
    jobs = _Jobs()
    if api == "run":
        with pytest.raises(he.RunnerRefusalError) as caught:
            he.run(requests, footage_folder=footage, exports=jobs)
        text = str(caught.value)
    else:
        monkeypatch.setattr(he, "configured_footage_folder", lambda: footage)
        where = ["--beside-source"] if beside else ["--out", str(output_folder)]
        assert he.main([str(source), *where, "--force-cpu"], exports=jobs) == 2
        text = capsys.readouterr().err.removeprefix("headless_export: ").strip()
    assert text == f"the output for {source.name} would leave its checked output folder."
    assert not jobs.calls
    assert not list(footage.iterdir()) and not list(out.iterdir()) and not list(src.iterdir())


def _one_letter_jpeg_stream(sample, src):
    """Build a JPEG ADS whose carrier letter matches this test folder's drive."""
    if sys.platform != "win32":
        pytest.skip("the real one-letter carrier requires Windows NTFS")
    carrier = src / src.drive[0].lower()
    carrier.write_bytes(b"source carrier")
    source = Path(f"{carrier}:input.jpg")
    data = sample("jpeg-gradient-srgb").read_bytes()
    try:
        source.write_bytes(data)
        assert source.read_bytes() == data
    except OSError as exc:
        pytest.skip(f"alternate data stream creation unavailable: {type(exc).__name__}")
    return source


def test_drive_relative_stream_cannot_write_into_footage_cwd(sample, tmp_path, monkeypatch, capsys):
    footage, out, src = _folders(tmp_path)
    source = _one_letter_jpeg_stream(sample, src)
    before = source.read_bytes()
    relative_out = Path(os.path.relpath(out, footage))
    monkeypatch.chdir(footage)
    monkeypatch.setattr(he, "configured_footage_folder", lambda: footage)
    jobs = _Jobs(composition.export_jobs())
    status = he.main([str(source), "--out", str(relative_out), "--force-cpu"], exports=jobs)
    observed = sorted(path.name for path in footage.iterdir())
    assert status == 2, f"drive-relative output escaped into stand-in footage: {observed}"
    assert not jobs.calls and not observed and not list(out.iterdir())
    assert "would leave its checked output folder" in capsys.readouterr().err
    assert source.read_bytes() == before


@pytest.mark.parametrize("beside", [False, True], ids=["absolute-out", "beside-source"])
def test_same_drive_stream_output_keeps_checked_parent(sample, tmp_path, beside, record_property):
    footage, out, src = _folders(tmp_path)
    source = _one_letter_jpeg_stream(sample, src)
    requests = _requests(source, None if beside else out)
    planned = he.final_output_path(source, requests[0].settings, he.MediaKind.PHOTO)
    checked = source.parent if beside else out
    assert planned.parent == checked and planned.name == "input_corrected.png"
    he.check_outputs(requests, footage)  # the safe same-drive join must not be refused
    record = he.run(requests, footage_folder=footage, exports=composition.export_jobs())
    item = record.report.items[0]
    assert item.state == "done", item.result.failure
    assert item.result.outputs == (planned,) and planned.is_file()
    assert not list(footage.iterdir())
    record_property("actual_output", str(planned))
    print(f"SAME_DRIVE_OUTPUT {planned}")


def _streams(path):
    """List every NTFS stream and its size independently of the runner."""
    quoted = str(path).replace("'", "''")
    command = (
        "$ErrorActionPreference='Stop'; "
        f"@(Get-Item -LiteralPath '{quoted}' -Stream * | "
        "Select-Object Stream,Length) | ConvertTo-Json -Compress"
    )
    done = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert done.returncode == 0, (
        f"NTFS stream enumeration failed (exit {done.returncode}): {done.stderr}"
    )
    data = json.loads(done.stdout)
    rows = [data] if isinstance(data, dict) else data
    return sorted((row["Stream"], row["Length"]) for row in rows)


@pytest.mark.parametrize("after_refusal", [False, True], ids=["initial", "after-refusal"])
def test_stream_enumeration_failure_is_not_a_skip(tmp_path, monkeypatch, after_refusal):
    def enumerate_streams(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="planted enumeration failure")

    if after_refusal:
        footage, out, src = _folders(tmp_path)
        with pytest.raises(he.RunnerRefusalError):
            he.run(
                _requests(src / "carrier:input.jpg", out), footage_folder=footage, exports=_Jobs()
            )
    monkeypatch.setattr(subprocess, "run", enumerate_streams)
    try:
        with pytest.raises(AssertionError, match="stream enumeration failed"):
            _streams(tmp_path / "original.jpg")
    except pytest.skip.Exception:
        pytest.fail("stream enumeration failure must fail, not skip")


@pytest.mark.parametrize("api", ["run", "main"])
def test_stream_output_on_hard_link_leaves_original_unchanged(
    sample, tmp_path, monkeypatch, capsys, api
):
    if sys.platform != "win32":
        pytest.skip("the real alternate-data-stream reproduction requires Windows NTFS")
    footage, out, src = _folders(tmp_path)
    original = footage / "original.jpg"
    original.write_bytes(sample("jpeg-gradient-srgb").read_bytes())
    carrier = src / "carrier"
    carrier.write_bytes(b"source carrier")
    source = src / "carrier:input.jpg"
    try:
        os.link(original, out / "carrier")
        source.write_bytes(original.read_bytes())
        assert source.read_bytes() == original.read_bytes()
    except OSError as exc:
        pytest.skip(f"hard links / alternate data streams unavailable: {type(exc).__name__}")
    before_bytes, before_streams = original.read_bytes(), _streams(original)
    assert before_streams  # enumerator must see at least the unnamed data stream
    _assert_stream_refusal(
        source, out, footage, api, _Jobs(composition.export_jobs()), monkeypatch, capsys
    )
    assert original.read_bytes() == before_bytes
    assert _streams(original) == before_streams
    assert sorted(path.name for path in out.iterdir()) == ["carrier"]


def test_output_file_form_check_has_a_planted_control(
    tmp_path, monkeypatch, capsys, record_property
):
    footage, out, src = _folders(tmp_path)
    source = src / "carrier:input.jpg"
    real = he._write_form_refusal
    monkeypatch.setattr(
        he, "_write_form_refusal", lambda target: None if target.suffix == ".png" else real(target)
    )
    with pytest.raises(AssertionError, match="stream output must be refused") as caught:
        _assert_stream_refusal(source, out, footage, "main", _Jobs(), monkeypatch, capsys)
    record_property("caught_failure", str(caught.value))
    assert "assert 1 == 2" in str(caught.value)
    line = caught.traceback[-1].lineno + 1
    record_property("caught_assertion_line", line)
    print(f"PLANTED_CONTROL caught stream-refusal assertion at line {line}: {caught.value}")


def test_no_footage_still_skips_output_checks(tmp_path, monkeypatch):
    _, out, src = _folders(tmp_path)

    def unexpected(*args):
        pytest.fail("no-footage check called naming or form predicate")

    monkeypatch.setattr(he, "final_output_path", unexpected)
    monkeypatch.setattr(he, "_write_form_refusal", unexpected)
    jobs = _Jobs()
    record = he.run(_requests(src / "carrier:input.jpg", out), footage_folder=None, exports=jobs)
    assert len(jobs.calls) == 1 and record.report.items[0].state == "failed"


def test_refused_request_does_not_plan_an_output(tmp_path, monkeypatch):
    footage, out, src = _folders(tmp_path)

    def unexpected(*args):
        pytest.fail("a RefusedRequest must not plan an output")

    monkeypatch.setattr(he, "final_output_path", unexpected)
    jobs = _Jobs()
    record = he.run(_requests(src / "carrier:notes.txt", out), footage_folder=footage, exports=jobs)
    assert not jobs.calls and record.report.items[0].state == "failed"


def test_invalid_suffix_stays_an_engine_refusal(tmp_path, monkeypatch, capsys):
    footage, out, src = _folders(tmp_path)
    source = src / "missing.jpg"
    record = he.run(
        _requests(source, out, output_suffix="bad/suffix"),
        footage_folder=footage,
        exports=composition.export_jobs(),
    )
    assert record.report.items[0].state == "failed"
    assert "forbidden characters" in record.report.items[0].result.failure
    monkeypatch.setattr(he, "configured_footage_folder", lambda: footage)
    assert he.main([str(source), "--out", str(out), "--suffix", "bad/suffix"]) == 2
    assert "forbidden characters" in capsys.readouterr().err
    assert not list(out.iterdir())


def test_apostrophe_folder_in_refused_suffix_is_hidden(tmp_path, monkeypatch, capsys):
    out = tmp_path / "owner's-out"
    out.mkdir()
    suffix = str(out) + '/"'  # both quotes force repr to escape the apostrophe
    assert r"\'" in repr(suffix)
    record = tmp_path / "record.json"
    monkeypatch.setattr(he, "configured_footage_folder", lambda: None)
    status = he.main(
        [
            str(tmp_path / "missing.jpg"),
            "--out",
            str(out),
            "--suffix",
            suffix,
            "--record",
            str(record),
        ],
        exports=_Jobs(),
    )
    assert status == 2
    text = capsys.readouterr().err
    assert "forbidden characters" in text and out.name in text
    assert str(tmp_path) not in text.replace("\\\\", "\\")
    assert not record.exists() and not list(out.iterdir())


@pytest.mark.parametrize("form", ["raw", "slashes", "doubled", "ascii", "ascii-doubled"])
def test_apostrophe_folder_in_record_and_summary_is_hidden(tmp_path, form):
    out = tmp_path / "priv\u00e9's-out"
    out.mkdir()
    text = str(out)
    forms = {
        "raw": text,
        "slashes": out.as_posix(),
        "doubled": text.replace("\\", "\\\\"),
        "ascii": he.ascii_text(text),
        "ascii-doubled": he.ascii_text(text).replace("\\", "\\\\"),
    }
    quoted = forms[form].replace("'", r"\'")
    record = he.run(
        _requests(tmp_path / "missing.jpg", out),
        exports=_Jobs(failure=f"refused suffix '{quoted}/\"'"),
        footage_folder=None,
    )
    expected = f"refused suffix '{he.ascii_text(out.name)}/\"'"
    assert he.record_object(record)["items"][0]["failure"] == expected
    assert json.loads(he.record_json(record))["items"][0]["failure"] == expected
    assert he.summary_lines(record)[-1] == f"   failure: {expected}"


def _break_resolve(monkeypatch, folder, error):
    real = Path.resolve

    def resolve(path, *args, **kwargs):
        if str(path) == str(folder):
            raise error(f"cannot resolve {folder}")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)


@pytest.mark.parametrize("error", [OSError, RuntimeError])
@pytest.mark.parametrize("route", ["parsed", "argument-error", "argument-discovery"])
def test_resolve_failure_is_a_cli_usage_refusal(tmp_path, monkeypatch, capsys, error, route):
    _, out, src = _folders(tmp_path)
    sibling_cwd = tmp_path / "cwd"
    sibling_cwd.mkdir()
    monkeypatch.chdir(sibling_cwd)  # no known cwd spelling can hide a dropped sibling folder
    monkeypatch.setattr(he, "configured_footage_folder", lambda: None)
    if route == "argument-error":
        # Let discovery succeed once, then fail in Redactor itself.
        real = Path.resolve
        calls = 0

        def resolve(path, *args, **kwargs):
            nonlocal calls
            if path == out:
                calls += 1
                if calls > 1:
                    raise error(f"cannot resolve {out}")
            return real(path, *args, **kwargs)

        monkeypatch.setattr(Path, "resolve", resolve)
    else:
        _break_resolve(monkeypatch, out, error)
    argv = [str(src / "missing.jpg"), "--out", str(out)]
    if route != "parsed":
        argv += ["--bit-depth", str(out)]  # parser refusal itself would quote the path
    jobs = _Jobs()
    assert he.main(argv, exports=jobs) == 2
    captured = capsys.readouterr()
    assert not jobs.calls
    assert "Traceback" not in captured.err and not captured.out
    assert "headless_export" in captured.err
    assert str(tmp_path) not in captured.err.replace("\\\\", "\\")


@pytest.mark.parametrize("error", [OSError, RuntimeError])
@pytest.mark.parametrize("surface", ["run", "record_object"])
def test_resolve_failure_is_a_library_refusal(tmp_path, monkeypatch, error, surface):
    _, out, src = _folders(tmp_path)
    jobs = _Jobs()
    requests = _requests(src / "missing.jpg", out)
    if surface == "record_object":
        record = he.run(requests, exports=jobs, footage_folder=None)
        jobs.calls.clear()
    _break_resolve(monkeypatch, out, error)
    with pytest.raises(he.RunnerRefusalError) as caught:
        if surface == "run":
            he.run(requests, exports=jobs, footage_folder=None)
        else:
            he.record_object(record)
    assert str(tmp_path) not in str(caught.value)
    assert not jobs.calls


@pytest.mark.parametrize("topology", ["self-junction", "symlink-loop"])
def test_loop_resolution_reproduction(tmp_path, topology, record_property):
    loop = tmp_path / "loop"
    assert loop.parent == tmp_path and tmp_path.is_absolute()
    if topology == "self-junction":
        if sys.platform != "win32":
            pytest.skip("junction reproduction requires Windows")
        done = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(loop), str(loop)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if done.returncode:
            pytest.skip(f"self-junction creation refused (exit {done.returncode}): {done.stderr}")
    else:
        try:
            os.symlink(loop, loop, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"symlink-loop creation refused: {type(exc).__name__}: {exc}")
    code = (
        "import json,sys\nfrom pathlib import Path\n"
        "try:\n result = str(Path(sys.argv[1]).resolve())\n"
        "except (OSError, RuntimeError) as exc:\n result = type(exc).__name__\n"
        "print(json.dumps({'python': sys.version, 'platform': sys.platform, 'result': result}))"
    )
    try:
        done = subprocess.run(
            [sys.executable, "-c", code, str(loop / "x")],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        observed = json.loads(done.stdout)
        record_property("resolve_observation", observed)
        print(f"RESOLVE_OBSERVATION {topology}: {json.dumps(observed)}")
    finally:
        # Remove only the link entry, never recurse through either loop.
        if topology == "self-junction":
            loop.rmdir()
        else:
            loop.unlink()


def _comparison_expressions():
    """Read the actual three pixel assertions without running their fixture-heavy tests."""
    root = Path(__file__).parent
    photo = ast.parse((root / "test_wp41_photo_path.py").read_text(encoding="utf-8"))
    v8 = ast.parse((root / "test_wp41_v8.py").read_text(encoding="utf-8"))
    expressions = []
    for tree, function, names in (
        (photo, "test_n10_the_same_still_twice_is_identical", {"recording", "pixels"}),
        (v8, "test_v8b_k1_is_exact", {"written_pixels"}),
    ):
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function)
        for stmt in node.body:
            if isinstance(stmt, ast.Assert):
                used = {n.id for n in ast.walk(stmt.test) if isinstance(n, ast.Name)}
                array_comparison = any(
                    isinstance(n, ast.Attribute) and n.attr in {"array_equal", "tobytes"}
                    for n in ast.walk(stmt.test)
                )
                if used & names and array_comparison:
                    expressions.append(ast.Expression(stmt.test))
    assert len(expressions) == 3
    return expressions


@pytest.mark.parametrize("site", ["statistics", "pre-encode", "decoded", "preview"])
def test_signed_zero_is_distinct_in_bit_comparisons(tmp_path, site):
    from test_wp41_v8 import equal_statistics

    plus = np.array([0.0, 1.0], dtype=np.float32)
    minus = np.array([-0.0, 1.0], dtype=np.float32)
    assert np.array_equal(plus, minus)
    assert plus.dtype == minus.dtype and plus.shape == minus.shape
    assert plus.tobytes() != minus.tobytes()
    comparisons = _comparison_expressions()
    for other in (plus.copy(), minus, plus.astype(np.float64), plus.reshape(1, 2)):
        expected = other.dtype == plus.dtype and other.shape == plus.shape
        expected = expected and other.tobytes() == plus.tobytes()
        if site == "statistics":
            assert equal_statistics({"stage": [plus]}, {"stage": [other]}) == expected
        else:
            expression = comparisons[["pre-encode", "decoded", "preview"].index(site)]
            namespace = {
                "np": np,
                "recording": SimpleNamespace(pixels=[plus, other]),
                "pixels": [plus, other],
                "preview": plus,
                "written_pixels": other,
            }
            assert eval(compile(expression, str(tmp_path / "comparison"), "eval"), namespace) == (
                expected
            )


@pytest.mark.parametrize("site", ["statistics", "pre-encode", "decoded", "preview"])
def test_nan_remains_unequal_in_all_four_comparisons(tmp_path, site):
    from test_wp41_v8 import equal_statistics

    first = np.array([np.nan, 1.0], dtype=np.float32)
    other = first.copy()
    assert not np.array_equal(first, other)
    assert (first.dtype, first.shape, first.tobytes()) == (
        other.dtype,
        other.shape,
        other.tobytes(),
    )
    if site == "statistics":
        assert not equal_statistics({"stage": [first]}, {"stage": [other]})
    else:
        expression = _comparison_expressions()[["pre-encode", "decoded", "preview"].index(site)]
        namespace = {
            "np": np,
            "recording": SimpleNamespace(pixels=[first, other]),
            "pixels": [first, other],
            "preview": first,
            "written_pixels": other,
        }
        assert not eval(compile(expression, str(tmp_path / "nan-comparison"), "eval"), namespace)
