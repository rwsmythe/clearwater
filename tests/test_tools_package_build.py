"""The packaging script's bundle checks and build hygiene (WP6.1, Reviewer A round 1).

Parallel leg, synthetic: release folders are small trees under ``tmp_path``, package
archives are real PyInstaller CArchive / PYZ files written by PyInstaller's own writers into
``tmp_path``, and ZIP archives are built in memory. Nothing is planted in a real dist, and
PyInstaller is never run (``run_pyinstaller`` is replaced where ``build()`` is called).

``WP61_BUILD_SCRIPT`` may name another copy of ``build.py`` (the turn-2 one, for the
ledger's before / after record); by default the tree's own ``tools/package/build.py`` is
tested.
"""

from __future__ import annotations

import importlib.util
import io
import marshal
import os
import shutil
import sys
import zipfile
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

import clearwater

REPO_ROOT = Path(__file__).resolve().parents[1]

INTERNAL = "Clearwater/_internal"
"""The one-folder release's bundle root, relative to the release folder."""


def _load_build_script() -> ModuleType:
    """Import ``build.py`` by its path (it is not a package)."""
    default = REPO_ROOT / "tools" / "package" / "build.py"
    path = Path(os.environ.get("WP61_BUILD_SCRIPT", default))
    spec = importlib.util.spec_from_file_location("wp61_package_build_checks", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = _load_build_script()


def tree(root: Path, names: list[str], data: bytes = b"x") -> Path:
    """Create each relative file name under ``root`` (parents included)."""
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return root


def zip_bytes(members: dict[str, bytes]) -> bytes:
    """Return a ZIP archive, built in memory, holding ``members``."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return buffer.getvalue()


def pyc(name: str) -> bytes:
    """Return a compiled empty module as ``.pyc`` bytes (a CArchive module entry's source)."""
    header = importlib.util.MAGIC_NUMBER + bytes(12)
    return header + marshal.dumps(compile("", name, "exec"))


def make_exe(
    folder: Path, entries: list[tuple[str, bytes, str]], modules: Sequence[str] = ()
) -> Path:
    """Write a real CArchive (and, with ``modules``, its PYZ) as ``folder/Clearwater.exe``.

    Args:
        folder: Where the archive and its source files go.
        entries: (archive name, data, CArchive typecode) for each entry.
        modules: Dotted module names for an embedded PYZ.

    Returns:
        The archive.
    """
    writers = pytest.importorskip("PyInstaller.archive.writers")
    sources = folder / "sources"
    sources.mkdir(parents=True)
    rows: list[tuple[str, str, bool, str]] = []
    for index, (name, data, typecode) in enumerate(entries):
        source = sources / f"entry{index}"
        source.write_bytes(data)
        rows.append((name, str(source), True, typecode))
    if modules:
        pyz = folder / "PYZ.pyz"
        code = {m: compile("", m, "exec") for m in modules}
        writers.ZlibArchiveWriter(
            str(pyz), [(m, str(sources / "m.py"), "PYMODULE") for m in modules], code_dict=code
        )
        rows.append(("PYZ.pyz", str(pyz), False, "z"))
    executable = folder / "Clearwater.exe"
    writers.CArchiveWriter(str(executable), rows, "python312.dll")
    return executable


def hits(found: list[str], needle: str) -> list[str]:
    """Return the violations that mention ``needle``."""
    return [line for line in found if needle in line]


# F1: nested GPU content, at any depth.


def test_a_nested_cuda_library_in_the_dist_is_found(tmp_path: Path) -> None:
    """F1: ``_internal/scipy.libs/nvrtc64_120_0.dll`` (turn 2: only the first folder looked at)."""
    tree(tmp_path, [f"{INTERNAL}/scipy.libs/nvrtc64_120_0.dll"])
    assert hits(build.forbidden_paths(tmp_path), "nvrtc64_120_0.dll")


def test_a_nested_gpu_package_in_the_dist_is_found(tmp_path: Path) -> None:
    """F1: CuPy collected beneath another package."""
    tree(tmp_path, [f"{INTERNAL}/PySide6/cupy_backends/cuda/api/runtime.cp312-win_amd64.pyd"])
    assert hits(build.forbidden_paths(tmp_path), "cupy_backends")


def test_nested_gpu_entries_in_the_package_archive_are_found(tmp_path: Path) -> None:
    """F1: the same two files as one-file CArchive entries, and a nested PYZ module."""
    executable = make_exe(
        tmp_path,
        [
            ("scipy.libs/nvrtc64_120_0.dll", b"x", "b"),
            ("PySide6/cupy_backends/cuda/api/runtime.cp312-win_amd64.pyd", b"x", "b"),
        ],
        modules=["PySide6", "PySide6.cupy_backends", "PySide6.cupy_backends.cuda"],
    )
    found = build.forbidden_entries(executable)
    assert hits(found, "nvrtc64_120_0.dll")
    assert hits(found, "pkg:PySide6/cupy_backends")
    assert hits(found, "pyz:PySide6.cupy_backends")


# F2: case.


def test_gpu_names_in_another_case_are_found_in_the_dist(tmp_path: Path) -> None:
    """F2: ``Cupy`` and ``NVIDIA`` (Windows file names are case-insensitive)."""
    tree(
        tmp_path, [f"{INTERNAL}/Cupy/__init__.pyc", f"{INTERNAL}/NVIDIA/cublas/bin/cublas64_12.dll"]
    )
    found = build.forbidden_paths(tmp_path)
    assert hits(found, "Cupy/__init__.pyc")
    assert hits(found, "NVIDIA/cublas/bin/cublas64_12.dll")


def test_gpu_names_in_another_case_are_found_in_the_package_archive(tmp_path: Path) -> None:
    """F2: the same names as CArchive entries."""
    executable = make_exe(
        tmp_path,
        [("Cupy/__init__.pyc", b"x", "x"), ("NVIDIA/cublas/bin/cublas64_12.dll", b"x", "b")],
    )
    found = build.forbidden_entries(executable)
    assert hits(found, "Cupy/__init__.pyc")
    assert hits(found, "NVIDIA/cublas")


# F3: ZIP members, recursively, in memory.


def test_a_gpu_module_inside_base_library_zip_is_found(tmp_path: Path) -> None:
    """F3: one-folder ``_internal/base_library.zip`` holding ``cupy/__init__.pyc``."""
    zipped = zip_bytes({"encodings/__init__.pyc": b"x", "cupy/__init__.pyc": b"x"})
    tree(tmp_path, [f"{INTERNAL}/base_library.zip"], data=zipped)
    found = build.forbidden_paths(tmp_path)
    assert hits(found, "base_library.zip!cupy/__init__.pyc")
    assert not hits(found, "encodings")


def test_a_gpu_module_inside_an_archived_zip_is_found(tmp_path: Path) -> None:
    """F3: the same ZIP as a one-file CArchive data entry."""
    zipped = zip_bytes({"cupy/__init__.pyc": b"x"})
    executable = make_exe(tmp_path, [("base_library.zip", zipped, "x")])
    assert hits(build.forbidden_entries(executable), "base_library.zip!cupy/__init__.pyc")


def test_zips_are_found_by_magic_and_opened_recursively(tmp_path: Path) -> None:
    """F3: a ZIP without a ZIP name, and a ZIP inside a ZIP inside a ZIP."""
    inner = zip_bytes({"nvrtc64_120_0.dll": b"x"})
    middle = zip_bytes({"inner.zip": inner})
    tree(tmp_path, [f"{INTERNAL}/PySide6/data.bin"], data=middle)
    found = build.forbidden_paths(tmp_path)
    assert hits(found, "data.bin!inner.zip!nvrtc64_120_0.dll (cuda-library)")


def test_an_unreadable_zip_fails_closed(tmp_path: Path) -> None:
    """F3: a ``.zip`` that cannot be opened is a violation, not a pass."""
    tree(tmp_path, [f"{INTERNAL}/broken.zip"], data=b"not a zip at all")
    assert hits(build.forbidden_paths(tmp_path), "broken.zip (unreadable-zip)")


def test_zip_members_are_never_extracted_to_disk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F3: the checks read member names and bytes in memory; extraction would raise."""

    def refuse(*_: Any, **__: Any) -> None:
        raise AssertionError("extracted to disk")

    monkeypatch.setattr(zipfile.ZipFile, "extract", refuse)
    monkeypatch.setattr(zipfile.ZipFile, "extractall", refuse)
    zipped = zip_bytes({"x.zip": zip_bytes({"cupy/__init__.pyc": b"x"})})
    tree(tmp_path, [f"{INTERNAL}/base_library.zip"], data=zipped)
    assert hits(build.forbidden_paths(tmp_path), "x.zip!cupy/__init__.pyc")
    assert sorted(p.name for p in (tmp_path / INTERNAL).iterdir()) == ["base_library.zip"]


# F5: the allowlist for loose modules and extension modules.


def test_an_unexpected_extension_module_in_the_dist_is_found(tmp_path: Path) -> None:
    """F5: ``av/_core.pyd`` and a loose ``yaml`` package (turn 2 checked PYZ names only)."""
    tree(tmp_path, [f"{INTERNAL}/av/_core.cp312-win_amd64.pyd", f"{INTERNAL}/yaml/__init__.pyc"])
    found = build.forbidden_paths(tmp_path)
    assert hits(found, "av/_core.cp312-win_amd64.pyd (unexpected-module)")
    assert hits(found, "yaml/__init__.pyc (unexpected-module)")


def test_an_unexpected_extension_module_in_the_package_archive_is_found(tmp_path: Path) -> None:
    """F5: the same as a one-file CArchive binary entry."""
    executable = make_exe(tmp_path, [("av/_core.cp312-win_amd64.pyd", b"x", "b")])
    assert hits(build.forbidden_entries(executable), "av/_core.cp312-win_amd64.pyd")


def test_the_products_own_modules_and_the_stdlib_pass(tmp_path: Path) -> None:
    """No false positive on what a real bundle holds (and SciPy's ``cupy`` adapter)."""
    names = [
        f"{INTERNAL}/numpy/_core/_multiarray_umath.cp312-win_amd64.pyd",
        f"{INTERNAL}/PySide6/QtCore.pyd",
        f"{INTERNAL}/PySide6/plugins/platforms/qwindows.dll",
        f"{INTERNAL}/_ssl.pyd",
        f"{INTERNAL}/_pillow_heif.cp312-win_amd64.pyd",
        f"{INTERNAL}/numpy-2.5.4.dist-info/RECORD",
        f"{INTERNAL}/python312.dll",
        "Clearwater/Clearwater.exe",
        "Clearwater/ffmpeg.exe",
    ]
    tree(tmp_path, names)
    zipped = zip_bytes({"encodings/__init__.pyc": b"x", "collections/abc.pyc": b"x"})
    tree(tmp_path, [f"{INTERNAL}/base_library.zip"], data=zipped)
    assert build.forbidden_paths(tmp_path) == []
    executable = make_exe(
        tmp_path / "pkg",
        [("PySide6/QtCore.pyd", b"x", "b"), ("pyimod01_archive", pyc("pyimod01_archive"), "m")],
        modules=[
            "clearwater",
            "clearwater.io",
            "io",
            "scipy._external.array_api_compat.cupy",
            "scipy._external.array_api_compat.cupy._aliases",
        ],
    )
    assert build.forbidden_entries(executable) == []


def test_the_scipy_adapter_exception_is_narrow(tmp_path: Path) -> None:
    """Only the adapter's own ``cupy`` component is excepted; nothing else beside it."""
    tree(
        tmp_path,
        [
            f"{INTERNAL}/scipy/_external/array_api_compat/cupy/nvrtc64_120_0.dll",
            f"{INTERNAL}/scipy/cupy/__init__.pyc",
        ],
    )
    found = build.forbidden_paths(tmp_path)
    assert hits(found, "array_api_compat/cupy/nvrtc64_120_0.dll (cuda-library)")
    assert hits(found, "scipy/cupy/__init__.pyc (gpu-module)")


def test_shadowing_top_level_modules_are_found(tmp_path: Path) -> None:
    """A ``clearwater`` subpackage, or a package ``io``, frozen at the top level."""
    executable = make_exe(tmp_path, [], modules=["core", "core.backend", "io.video"])
    found = build.forbidden_entries(executable)
    assert hits(found, "pyz:core.backend (shadow)")
    assert hits(found, "pyz:io.video (shadow)")


# F11: Linux library names.


def test_linux_cuda_library_names_are_found(tmp_path: Path) -> None:
    """F11: ``libnvrtc.so`` and the versioned ``libcudart.so.12``."""
    tree(tmp_path, [f"{INTERNAL}/libnvrtc.so", f"{INTERNAL}/libcudart.so.12"])
    found = build.forbidden_paths(tmp_path)
    assert hits(found, "libnvrtc.so")
    assert hits(found, "libcudart.so.12")


# F4, F6: what a build touches.


class _StopBuildError(Exception):
    """Raised by the PyInstaller stand-in: the test needs only what happened before it."""


def _stopping_build(monkeypatch: pytest.MonkeyPatch, out: Path, seen: dict[str, Any]) -> None:
    """Run ``build.build`` up to PyInstaller, recording the state PyInstaller would see."""

    def stand_in(args: Any) -> None:
        seen["config"] = os.environ.get("PYINSTALLER_CONFIG_DIR")
        seen["release"] = sorted(p.name for p in out.rglob("*"))
        raise _StopBuildError

    monkeypatch.setattr(build, "run_pyinstaller", stand_in)
    with pytest.raises(_StopBuildError):
        build.build("onefile", out=out)


def test_pyinstallers_cache_is_kept_under_the_output_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F4: ``PYINSTALLER_CONFIG_DIR`` points under ``out`` before PyInstaller runs."""
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", "restored-after-the-test")
    monkeypatch.delenv("PYINSTALLER_CONFIG_DIR")
    seen: dict[str, Any] = {}
    _stopping_build(monkeypatch, tmp_path / "out", seen)
    assert seen["config"] is not None
    assert Path(seen["config"]).is_relative_to(tmp_path / "out")


def test_a_rebuild_starts_from_an_empty_release_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F6: a stale ``ffmpeg.exe`` from an earlier ``--with-ffmpeg`` build is gone."""
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    out = tmp_path / "out"
    release = build.release_dir(out, "onefile", build.app_version())
    tree(release, ["Clearwater.exe", "ffmpeg.exe", "ffprobe.exe"])
    beside = tree(out, ["keep.txt"])
    seen: dict[str, Any] = {}
    _stopping_build(monkeypatch, out, seen)
    assert "ffmpeg.exe" not in seen["release"]
    assert (beside / "keep.txt").is_file()  # only the release folder is cleaned


# F7: FFmpeg under its canonical name, and working.


def test_ffmpeg_is_copied_under_its_canonical_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F7: a PATH entry resolving to ``ffmpeg-9.0.2.exe`` lands as ``ffmpeg.exe``."""
    source = tree(tmp_path / "bin", ["ffmpeg-9.0.2.exe"]) / "ffmpeg-9.0.2.exe"
    monkeypatch.setattr(build.shutil, "which", lambda tool: str(source))
    monkeypatch.setattr(build, "tool_version", lambda path: "ffmpeg version test", raising=False)
    destination = tmp_path / "dist"
    destination.mkdir()
    build.copy_ffmpeg(destination, ["ffmpeg"])
    expected = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    assert sorted(p.name for p in destination.iterdir()) == [expected]


def test_a_copied_tool_that_does_not_run_as_ffmpeg_is_refused(tmp_path: Path) -> None:
    """F7: ``tool_version`` needs a zero exit and a ``version`` line (Python fails ``-version``)."""
    copy = tmp_path / Path(sys.executable).name
    shutil.copy2(sys.executable, copy)
    with pytest.raises(RuntimeError, match="-version"):
        build.tool_version(copy)


# F8 (and F10): the version without importing.


def test_the_version_is_read_without_importing_the_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F8 / F10: an already-imported (stale) ``clearwater`` does not change the answer."""
    stale = ModuleType("clearwater")
    stale.__version__ = "stale-installed"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "clearwater", stale)
    assert build.app_version() == clearwater.__version__
    init = tmp_path / "__init__.py"
    init.write_text('"""doc."""\n\n__version__ = "9.8.7"\n', encoding="utf-8")
    assert build.app_version(init) == "9.8.7"
