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

import base64
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import marshal
import os
import shutil
import sys
import zipfile
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

import clearwater
from clearwater import gpu_pack, gpu_pack_install

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


@pytest.mark.parametrize("variable", ["PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE"])
def test_build_refuses_python_environment_overrides(tmp_path, monkeypatch, capsys, variable):
    """Untrusted Python search paths fail before any pack scan or analysis."""
    monkeypatch.setenv(variable, "foreign")
    monkeypatch.setattr(build, "pack_sources", lambda: pytest.fail("scan reached"))
    assert build.build("onedir", out=tmp_path) == 1
    assert f"FAILED: build environment: {variable} is set" in capsys.readouterr().out


@pytest.mark.parametrize("duplicate", [False, True])
def test_origin_trust_refuses_foreign_locked_distribution(tmp_path, monkeypatch, duplicate):
    """A matching lock version and self-authored RECORD do not establish venv origin."""
    site = tmp_path / "foreign"
    info = site / "numpy-2.5.4.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text("Name: numpy\nVersion: 2.5.4\n")
    (info / "RECORD").write_text("numpy/foreign.dll,,\n")
    monkeypatch.syspath_prepend(str(site))
    if not duplicate:
        original = build.importlib.metadata.distributions
        monkeypatch.setattr(
            build.importlib.metadata,
            "distributions",
            lambda **kwargs: original(path=[str(site)]),
        )
    with pytest.raises(ValueError, match=r"(outside.*venv|resolves more than once)"):
        build._locked_native_distributions()


def test_analysis_uses_only_sanitized_path_and_restores_it(tmp_path, monkeypatch):
    """A foreign resolver candidate must disappear even when analysis fails."""
    foreign = tree(tmp_path / "foreign", ["foreign.dll"])
    base = tree(tmp_path / "python", ["DLLs/trusted.dll"])
    venv = tmp_path / "venv"
    windows = tmp_path / "Windows"
    original = str(foreign)
    monkeypatch.setenv("PATH", original)
    monkeypatch.setenv("SystemRoot", str(windows))
    monkeypatch.setattr(build.sys, "base_prefix", str(base))
    monkeypatch.setattr(build.sys, "prefix", str(venv))
    monkeypatch.setattr(build.sys, "platform", "win32")
    seen = []

    def analysis(args):
        seen.append(os.environ["PATH"].split(os.pathsep))
        resolved = next(
            (
                Path(part) / "foreign.dll"
                for part in os.environ["PATH"].split(os.pathsep)
                if (Path(part) / "foreign.dll").is_file()
            ),
            None,
        )
        assert resolved is None
        raise RuntimeError("analysis failed")

    real_import = build.importlib.import_module
    monkeypatch.setattr(
        build.importlib,
        "import_module",
        lambda name: (
            SimpleNamespace(run=analysis) if name == "PyInstaller.__main__" else real_import(name)
        ),
    )
    with pytest.raises(RuntimeError, match="analysis failed"):
        build.run_pyinstaller([])
    assert seen == [
        [
            str(base),
            str(base / "DLLs"),
            str(venv / "Scripts"),
            str(windows / "System32"),
            str(windows),
        ]
    ]
    assert os.environ["PATH"] == original


def test_missing_systemroot_is_a_named_build_failure(tmp_path, monkeypatch, capsys):
    """A3: missing Windows resolver roots fail before importing PyInstaller."""
    monkeypatch.setattr(build.sys, "platform", "win32")
    monkeypatch.delenv("SYSTEMROOT", raising=False)
    monkeypatch.setenv("PATH", "unchanged path")
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr(build, "pack_sources", lambda: [])
    real_import = build.importlib.import_module

    def guarded_import(name):
        assert name != "PyInstaller.__main__", "missing SYSTEMROOT must stop analysis"
        return real_import(name)

    monkeypatch.setattr(build.importlib, "import_module", guarded_import)
    assert build.build("onedir", out=tmp_path / "out") == 1
    assert "FAILED: PyInstaller: SYSTEMROOT is unset" in capsys.readouterr().out
    assert os.environ["PATH"] == "unchanged path"


def test_pyinstaller_hook_valueerror_keeps_its_traceback(tmp_path, monkeypatch):
    """Only the explicit build-environment error becomes a one-line failure."""
    monkeypatch.setattr(build, "pack_sources", lambda: [])
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "config"))

    def broken_hook(args):
        raise ValueError("real hook failure")

    monkeypatch.setattr(build, "run_pyinstaller", broken_hook)
    with pytest.raises(ValueError, match="real hook failure"):
        build.build("onedir", out=tmp_path / "out")


@pytest.mark.parametrize(
    "magic",
    [
        b"MZ",
        b"\x7fELF",
        b"\xfe\xed\xfa\xce",
        b"\xce\xfa\xed\xfe",
        b"\xfe\xed\xfa\xcf",
        b"\xcf\xfa\xed\xfe",
        b"\xca\xfe\xba\xbe",
        b"\xbe\xba\xfe\xca",
        b"\xca\xfe\xba\xbf",
        b"\xbf\xba\xfe\xca",
    ],
)
def test_native_origin_refuses_renamed_native_magic(tmp_path, monkeypatch, magic):
    """A1: a PE/ELF/Mach-O file cannot evade origin checks by changing its suffix."""
    home = tree(tmp_path / "dist", ["Clearwater.exe"])
    tree(home, ["_internal/foreign.bin"], magic + b"foreign native")
    monkeypatch.setattr(build, "_native_origin_hashes", lambda: set())
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True)
    monkeypatch.setattr(build, "read_package", lambda _: SimpleNamespace(toc={}))
    found = build.native_origin_violations(home / "Clearwater.exe", original_path="")
    assert len(found) == 1 and "_internal/foreign.bin" in found[0]


def test_native_origin_checks_mixed_case_extensions(tmp_path, monkeypatch):
    """A4 claim 4: deleting extension casefold must let this foreign DLL escape."""
    home = tree(tmp_path / "dist", ["Clearwater.exe"])
    tree(home, ["_internal/foreign.DlL"], b"foreign without magic")
    monkeypatch.setattr(build, "_native_origin_hashes", lambda: set())
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True)
    monkeypatch.setattr(build, "read_package", lambda _: SimpleNamespace(toc={}))
    found = build.native_origin_violations(home / "Clearwater.exe", original_path="")
    assert len(found) == 1 and "_internal/foreign.DlL" in found[0]


@pytest.mark.parametrize("archived", [False, True])
def test_native_origin_refuses_foreign_bytes_and_names_original_path(
    tmp_path, monkeypatch, archived
):
    """Unknown natives at any depth, including nested ZIPs, fail closed."""
    home = tree(tmp_path / "dist", ["Clearwater.exe"])
    foreign = tree(tmp_path / "foreign", ["foreign.dll"], b"foreign")
    if archived:
        tree(
            home,
            ["_internal/nested.zip"],
            zip_bytes({"inner.zip": zip_bytes({"pkg/foreign.dll": b"foreign"})}),
        )
    else:
        tree(home, ["_internal/pkg/foreign.dll"], b"foreign")
    monkeypatch.setattr(build, "_native_origin_hashes", lambda: set(), raising=False)
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True, raising=False)
    monkeypatch.setattr(build, "read_package", lambda _: SimpleNamespace(toc={}))
    found = build.native_origin_violations(home / "Clearwater.exe", original_path=str(foreign))
    assert len(found) == 1
    assert "foreign.dll" in found[0] and str(foreign / "foreign.dll") in found[0]


def test_native_origin_accepts_interpreter_and_hash_verified_locked_record(tmp_path, monkeypatch):
    """Interpreter bytes and a locked wheel's verified RECORD are independent origins."""
    base = tree(tmp_path / "python", ["DLLs/python312.dll"], b"interpreter")
    site = tree(tmp_path / "site", ["fixture/native.dll"], b"wheel")
    info = site / "fixture-1.0.dist-info"
    info.mkdir()
    (info / "METADATA").write_text("Name: fixture\nVersion: 1.0\n")
    digest = base64.urlsafe_b64encode(hashlib.sha256(b"wheel").digest()).decode().rstrip("=")
    (info / "RECORD").write_text(f"fixture/native.dll,sha256={digest},5\n")
    dist = importlib.metadata.PathDistribution(info)
    monkeypatch.setattr(build.sys, "base_prefix", str(base))
    monkeypatch.setattr(build, "_locked_native_distributions", lambda: [dist], raising=False)
    home = tree(tmp_path / "dist", ["Clearwater.exe"])
    tree(home, ["_internal/python312.dll"], b"interpreter")
    tree(home, ["_internal/nested/native.dll"], b"wheel")
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True, raising=False)
    monkeypatch.setattr(build, "read_package", lambda _: SimpleNamespace(toc={}))
    assert build.native_origin_violations(home / "Clearwater.exe", original_path="") == []
    (site / "fixture/native.dll").write_bytes(b"modified wheel")
    with pytest.raises(ValueError, match="RECORD"):
        build.native_origin_violations(home / "Clearwater.exe", original_path="")


def test_record_native_hash_refuses_correct_digest_with_wrong_record_size(tmp_path):
    """M3: the RECORD's size must match independently of a correct SHA-256."""
    site = tree(tmp_path / "site", ["fixture/native.dll"], b"wheel")
    info = site / "fixture-1.0.dist-info"
    info.mkdir()
    digest = base64.urlsafe_b64encode(hashlib.sha256(b"wheel").digest()).decode().rstrip("=")
    (info / "RECORD").write_text(f"fixture/native.dll,sha256={digest},4\n")
    dist = importlib.metadata.PathDistribution(info)
    with pytest.raises(ValueError, match="differs from locked wheel RECORD"):
        build._record_native_hash(dist, dist.files[0])


def test_bootloader_refuses_executable_resource_section(tmp_path):
    """M5: replaceable resources must never introduce executable code."""
    import pefile
    from PyInstaller.utils.win32 import winmanifest

    target = tmp_path / "Clearwater.exe"
    target.write_bytes(build._locked_bootloader().read_bytes())
    winmanifest.write_manifest_to_executable(str(target), winmanifest.create_application_manifest())
    with pefile.PE(str(target)) as pe:
        resource = next(
            section for section in pe.sections if section.Name.rstrip(b"\0") == b".rsrc"
        )
        resource.Characteristics |= 0x20000000
        changed = pe.write()
    target.write_bytes(changed)
    assert not build._is_clearwater_bootloader(target)


def test_bootloader_identity_allows_resources_and_archive_but_refuses_code_changes(tmp_path):
    """Verify immutable PE sections from the locked windowed bootloader, never a name."""
    import pefile

    source = build._locked_bootloader()
    target = tmp_path / "Clearwater.exe"
    target.write_bytes(source.read_bytes() + b"synthetic appended archive")
    assert build._is_clearwater_bootloader(target)
    from PyInstaller.utils.win32 import winmanifest

    winmanifest.write_manifest_to_executable(str(target), winmanifest.create_application_manifest())
    assert build._is_clearwater_bootloader(target)
    with pefile.PE(str(target)) as pe:
        code = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".text")
        data = bytearray(target.read_bytes())
        data[code.PointerToRawData + 20] ^= 1
    target.write_bytes(data)
    assert not build._is_clearwater_bootloader(target)


@pytest.mark.parametrize("trusted", [False, True])
def test_build_enforces_origin_after_all_native_copies(tmp_path, monkeypatch, capsys, trusted):
    """A native introduced after analysis still goes through the origin gate."""
    out = tmp_path / "out"
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr(build, "pack_sources", lambda: [])
    check = build.native_origin_violations
    _fake_pyinstaller(monkeypatch, out, ["graphlib"], {})
    monkeypatch.setattr(build, "native_origin_violations", check)
    monkeypatch.setattr(
        build,
        "_native_origin_hashes",
        lambda: {hashlib.sha256(b"native copy").hexdigest()} if trusted else set(),
    )
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True)
    foreign = tree(tmp_path / "foreign", ["foreign.dll"], b"native copy")
    monkeypatch.setenv("PATH", str(foreign))

    def copy_native(folder):
        tree(folder, ["_internal/foreign.dll"], b"native copy")
        return []

    monkeypatch.setattr(build, "copy_ffmpeg", copy_native)
    assert build.build("onefile", out=out, with_ffmpeg=True) == (0 if trusted else 1)
    output = capsys.readouterr().out
    assert ("native origin check: PASS" in output) == trusted
    if not trusted:
        assert str(foreign / "foreign.dll") in output


def test_bootloader_rejects_a_changed_loader_import_directory(tmp_path):
    """Identical code bytes do not excuse an executable with redirected imports."""
    import pefile

    target = tmp_path / "Clearwater.exe"
    target.write_bytes(build._locked_bootloader().read_bytes())
    with pefile.PE(str(target)) as pe:
        pe.OPTIONAL_HEADER.DATA_DIRECTORY[1].VirtualAddress += 1
        data = pe.write()
    target.write_bytes(data)
    assert not build._is_clearwater_bootloader(target)


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
    folder: Path,
    entries: list[tuple[str, bytes, str]],
    modules: Sequence[str] = (),
    pyz_name: str = "PYZ.pyz",
) -> Path:
    """Write a real CArchive (and, with ``modules``, its PYZ) as ``folder/Clearwater.exe``.

    Args:
        folder: Where the archive and its source files go.
        entries: (archive name, data, CArchive typecode) for each entry.
        modules: Dotted module names for an embedded PYZ.
        pyz_name: The PYZ's own entry name in the CArchive (PyInstaller writes ``PYZ.pyz``).

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
        rows.append((pyz_name, str(pyz), False, "z"))
    executable = folder / "Clearwater.exe"
    writers.CArchiveWriter(str(executable), rows, "python312.dll")
    return executable


def hits(found: list[str], needle: str) -> list[str]:
    """Return the violations that mention ``needle``."""
    return [line for line in found if needle in line]


@pytest.mark.parametrize(
    ("platform", "filename"), [("win32", "Clearwater.exe"), ("darwin", "Clearwater")]
)
@pytest.mark.parametrize("nested", [False, True])
def test_executable_finder_preserves_both_layouts_and_platforms(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, platform: str, filename: str, nested: bool
) -> None:
    home = tmp_path / "Clearwater" if nested else tmp_path
    home.mkdir(exist_ok=True)
    expected = home / filename
    expected.write_bytes(b"synthetic executable")
    monkeypatch.setattr(build.sys, "platform", platform)
    assert build.find_executable(tmp_path) == expected


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
    monkeypatch.setattr(build, "pack_sources", list)  # no pack scan: the F-C2 tests cover it
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


# Reviewer A round 2.


def _locked_pack_binaries() -> list[str]:
    """Every ``.dll`` / ``.pyd`` path the eleven locked pack wheels install, from their RECORD.

    Read-only, from this environment's installed metadata (``importlib.metadata`` reads each
    distribution's ``RECORD``). Skips when the pack is not installed here at the lock's
    versions.
    """
    paths: list[str] = []
    for locked in gpu_pack.LOCKED_DISTRIBUTIONS:
        try:
            dist = importlib.metadata.distribution(locked.name)
        except importlib.metadata.PackageNotFoundError:
            pytest.skip(f"{locked.name} is not installed in this environment")
        if dist.version != locked.version:
            pytest.skip(f"{locked.name} {dist.version} is installed, not {locked.version}")
        files = dist.files or []
        paths += [f.as_posix() for f in files if f.name.lower().endswith((".dll", ".pyd"))]
    return sorted(paths)


def test_every_dll_the_locked_pack_wheels_install_is_flagged(tmp_path: Path) -> None:
    """#4: each locked DLL (``nvblas64_12.dll`` included) by its name alone, anywhere.

    Planted outside any GPU-named folder: nested in the one-folder bundle, beside the
    executable, inside a ZIP, and as a one-file archive entry. ``cudnn64_9.dll`` (CuPy's
    optional cuDNN, not in the lock) too.
    """
    dlls = sorted({PurePosixPath(p).name for p in _locked_pack_binaries() if p.endswith(".dll")})
    assert "nvblas64_12.dll" in dlls
    names = [*dlls, "cudnn64_9.dll"]
    tree(tmp_path, [f"{INTERNAL}/scipy.libs/{n}" for n in names])
    tree(tmp_path, [f"Clearwater/{n}" for n in names])
    zipped = zip_bytes({f"deep/{n}": b"x" for n in names})
    tree(tmp_path, [f"{INTERNAL}/extra.zip"], data=zipped)
    found = build.forbidden_paths(tmp_path)
    executable = make_exe(tmp_path / "pkg", [(f"scipy.libs/{n}", b"x", "b") for n in names])
    entries = build.forbidden_entries(executable)
    for name in names:
        assert hits(found, f"{INTERNAL}/scipy.libs/{name} (cuda-library)"), name
        assert hits(found, f"dist:Clearwater/{name} (cuda-library)"), name
        assert hits(found, f"extra.zip!deep/{name} (cuda-library)"), name
        assert hits(entries, f"pkg:scipy.libs/{name} (cuda-library)"), name


def test_every_extension_module_the_locked_pack_wheels_install_is_flagged(tmp_path: Path) -> None:
    """#4: each locked ``.pyd`` at its installed path, at the bundle root and the release root."""
    pyds = [p for p in _locked_pack_binaries() if p.endswith(".pyd")]
    assert pyds
    names = sorted({PurePosixPath(p).name for p in pyds})
    tree(tmp_path, [f"{INTERNAL}/{p}" for p in pyds])
    tree(tmp_path, [f"{INTERNAL}/{n}" for n in names])
    tree(tmp_path, names)
    found = build.forbidden_paths(tmp_path)
    for path in pyds:
        assert hits(found, f"dist:{INTERNAL}/{path} (gpu-module)"), path
    for name in names:  # unexpected-module, or shadow for a clearwater name such as core
        assert hits(found, f"dist:{INTERNAL}/{name} ("), name
        assert hits(found, f"dist:{name} ("), name


def test_script_and_boot_module_entries_are_checked_for_gpu_names(tmp_path: Path) -> None:
    """#5: script entries are named-checked; the boot exemption covers the allowlist only."""
    executable = make_exe(
        tmp_path,
        [
            ("cupy/__init__.py", b"pass\n", "s"),
            ("tests/accidental.py", b"pass\n", "s"),
            ("pyimod_accidental.cupy", pyc("pyimod_accidental.cupy"), "m"),
            # What a real bundle holds: no violation.
            ("pyiboot01_bootstrap", b"pass\n", "s"),
            ("pyi_rth_pyside6", b"pass\n", "s"),
            ("__main__", b"pass\n", "s"),
            ("pyimod01_archive", pyc("pyimod01_archive"), "m"),
            ("pyi-contents-directory _internal", b"", "o"),
        ],
    )
    found = build.forbidden_entries(executable)
    assert hits(found, "pkg:cupy/__init__.py (gpu-module)")
    assert hits(found, "pkg:tests/accidental.py (tests)")
    assert hits(found, "pkg:pyimod_accidental.cupy (gpu-module)")
    assert len(found) == 3, found


def test_runtime_options_are_checked_by_name_without_a_module_allowlist(tmp_path: Path) -> None:
    """Reviewer B #1: options live outside the TOC but still meet every-entry name rules."""
    executable = make_exe(tmp_path, [("cupy/runtime.pyd", b"", "o")])
    assert build.forbidden_entries(executable) == ["pkg:cupy/runtime.pyd (gpu-module)"]
    clean = make_exe(
        tmp_path / "clean",
        [("pyi-runtime-tmpdir work/tmp", b"", "o"), ("u", b"", "o")],
    )
    assert build.forbidden_entries(clean) == []


@pytest.mark.parametrize("suffix", [".dist-info", ".data", ".egg-info"])
@pytest.mark.parametrize(
    "name",
    [
        "nvidia-cublas-cu12-12.9.2.10",
        "nvidia.cublas.cu12-12.9.2.10",
        "NvIdIa_-CuBlAs.Cu12-12.9.2.10",
        "CuPy-CuDa12x-14.2.0",
        "CUDA.PathFinder-1.8.3",
        "cuda-toolkit-12.9.2.0",
    ],
)
def test_gpu_metadata_names_use_pep503_normalization(name: str, suffix: str) -> None:
    """Reviewer B #6: hyphens, dots, underscores and case cannot hide GPU metadata."""
    assert "gpu-metadata" in build.name_violations([name + suffix, "RECORD"], module_root=False)
    assert build.name_violations(["numpy-2.x" + suffix, "RECORD"], module_root=False) == []


def test_an_extension_module_beside_the_executable_is_found(tmp_path: Path) -> None:
    """#8: ``av.pyd`` at the release root or beside the executable meets the allowlist."""
    tree(tmp_path, ["av.pyd", "Clearwater/av.pyd", "Clearwater/yaml/__init__.pyc"])
    found = build.forbidden_paths(tmp_path)
    assert hits(found, "dist:av.pyd (unexpected-module)")
    assert hits(found, "dist:Clearwater/av.pyd (unexpected-module)")
    assert hits(found, "dist:Clearwater/yaml/__init__.pyc (unexpected-module)")


def test_each_copied_tool_is_run_from_the_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#13: ``copy_ffmpeg`` runs ``tool_version`` on each copy and returns its line."""
    tree(tmp_path / "bin", ["ffmpeg-9.exe", "ffprobe-9.exe"])
    monkeypatch.setattr(build.shutil, "which", lambda tool: str(tmp_path / "bin" / f"{tool}-9.exe"))
    ran: list[Path] = []

    def version(path: Path) -> str:
        ran.append(path)
        return f"{path.stem} version test"

    monkeypatch.setattr(build, "tool_version", version)
    destination = tmp_path / "dist"
    destination.mkdir()
    copied = build.copy_ffmpeg(destination, ["ffmpeg", "ffprobe"])
    expected = [destination / build.tool_file_name(t) for t in ("ffmpeg", "ffprobe")]
    assert ran == expected
    assert copied == [(expected[0], "ffmpeg version test"), (expected[1], "ffprobe version test")]


# F-C2 (CHARC's ruling 1): the GPU pack's standard-library needs, scanned and checked.

FIXTURE_FILES: dict[str, str] = {
    "fixpkg/__init__.py": (
        "from __future__ import annotations\n"
        "import json\n"
        "import os.path\n"
        "import numpy\n"
        "from . import sibling\n"
        "from .sibling import thing\n"
        "from ctypes import wintypes\n"
        "from collections import OrderedDict, abc\n"
    ),
    "fixpkg/sibling.py": (
        "import sys\n"
        "try:\n"
        "    import tomllib\n"
        "except ImportError:\n"
        "    tomllib = None\n"
        "if sys.platform == 'win32':\n"
        "    import winreg\n"
        "else:\n"
        "    import fcntl\n"
        "def later():\n"
        "    import graphlib\n"
        "    import importlib\n"
        "    importlib.import_module('csv')\n"
        "    importlib.import_module('.relative', __package__)\n"
        "    importlib.import_module(later.__name__)\n"
        "    __import__('zlib')\n"
        "    from fcntl import flock\n"
        "    from xml.etree import ElementTree\n"
        "    import scipy.ndimage\n"
        "thing = 1\n"
    ),
}
"""A fixture package with a known import set (each rule of :func:`build.import_candidates`)."""

EXPECTED_STDLIB = {
    "__future__",  # a real import at run time (IMPORT_NAME __future__)
    "json",
    "os",  # ``import os.path``: path is an attribute of the module os
    "ctypes",
    "ctypes.wintypes",  # ``from ctypes import wintypes``: a submodule
    "collections",
    "collections.abc",  # ``from collections import abc``; OrderedDict is an attribute
    "sys",  # a built-in
    "tomllib",  # inside try / except: counted
    "graphlib",  # inside a function: counted
    "importlib",
    "csv",  # importlib.import_module with a literal
    "zlib",  # __import__ with a literal
    "xml.etree",
    "xml.etree.ElementTree",
}
"""Exactly what the scan must report as needed (relative, third-party and non-literal skipped)."""

PLATFORM_GUARDED = {"winreg", "fcntl"}
"""Each exists on one platform only: needed where it exists, ``unavailable`` elsewhere."""


def _fixture_files(root: Path) -> list[tuple[str, Path]]:
    """Write :data:`FIXTURE_FILES` under ``root`` and return them as scan input."""
    for name, text in FIXTURE_FILES.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return [(f"fixture:{name}", root / name) for name in sorted(FIXTURE_FILES)]


def test_the_scan_of_a_fixture_package_returns_exactly_its_stdlib_imports(
    tmp_path: Path,
) -> None:
    """(b): relative, third-party and non-literal imports skipped; the rest exactly."""
    scan = build.scan_stdlib_imports(_fixture_files(tmp_path))
    here = {name for name in PLATFORM_GUARDED if build.stdlib_kind(name) is not None}
    assert set(scan.modules) == EXPECTED_STDLIB | here
    assert set(scan.unavailable) == PLATFORM_GUARDED - here
    assert here == ({"winreg"} if sys.platform == "win32" else {"fcntl"})
    assert scan.unparsable == []
    assert scan.modules["ctypes.wintypes"] == ["fixture:fixpkg/__init__.py:7"]
    assert scan.modules["graphlib"] == ["fixture:fixpkg/sibling.py:11"]


def test_a_file_that_cannot_be_parsed_is_reported(tmp_path: Path) -> None:
    """An unparsable pack file is listed (the build then fails: its imports are unknown)."""
    bad = tmp_path / "bad.py"
    bad.write_text("def broken(:\n", encoding="utf-8")
    scan = build.scan_stdlib_imports([("fixture:bad.py", bad)])
    assert scan.unparsable == ["fixture:bad.py: SyntaxError"]
    assert scan.modules == {}


def test_the_hidden_import_set_marks_each_member_by_its_source(tmp_path: Path) -> None:
    """(a): the scanned names and the committed list, each marked; one member can be both."""
    scan = build.scan_stdlib_imports(_fixture_files(tmp_path))
    wanted = {row.name: row for row in build.hidden_imports(scan, committed=("graphlib", "x1"))}
    assert wanted["graphlib"].sources == ("committed", "scan")
    assert wanted["x1"].sources == ("committed",)
    assert wanted["json"].sources == ("scan",)
    assert wanted["json"].named_by == ("fixture:fixpkg/__init__.py:2",)
    assert list(wanted) == sorted(wanted)


def test_the_committed_list_is_graphlib() -> None:
    """``graphlib`` is imported by a CuPy extension module only (no ``.py`` names it)."""
    assert build.PACK_EXTENSION_STDLIB_NEEDS == ("graphlib",)


def test_every_hidden_import_is_passed_to_pyinstaller(tmp_path: Path) -> None:
    """Each member becomes one ``--hidden-import`` argument, in order, in both forms."""
    for form in build.FORMS:
        args = build.pyinstaller_args(form, out=tmp_path, version="1", hidden=["a.b", "c"])
        assert args[-4:] == ["--hidden-import", "a.b", "--hidden-import", "c"]
    assert "--hidden-import" not in build.pyinstaller_args("onedir", out=tmp_path, version="1")


@pytest.mark.parametrize("form", ["onedir", "onefile"])
def test_pyinstaller_disables_its_windowed_traceback_dialog(tmp_path: Path, form) -> None:
    """Uncaught errors must reach the product reporter without a bootloader dialog."""
    args = build.pyinstaller_args(form, out=tmp_path, version="1")
    assert args.count("--disable-windowed-traceback") == 1


def test_a_planted_removal_from_the_committed_list_fails_the_bundle_check_by_name(
    tmp_path: Path,
) -> None:
    """A build from the list WITHOUT ``graphlib`` lacks it; the check names it, by source."""
    scan = build.StdlibScan()
    scan.modules["ctypes.wintypes"] = ["cuda-pathfinder:x.py:7"]
    wanted = build.hidden_imports(scan)
    planted = build.hidden_imports(scan, committed=())  # graphlib removed from the list
    args = build.pyinstaller_args(
        "onefile", out=tmp_path, version="1", hidden=[r.name for r in planted]
    )
    assert "graphlib" not in args
    bundled = [row.name for row in planted]  # what that build's PYZ would hold
    without = make_exe(tmp_path / "without", [], modules=["ctypes", *bundled])
    assert build.missing_hidden_imports(without, wanted) == [
        "hidden-import missing from the bundle: graphlib (committed)"
    ]
    full = make_exe(tmp_path / "full", [], modules=["ctypes", *bundled, "graphlib"])
    assert build.missing_hidden_imports(full, wanted) == []


def test_the_bundle_check_looks_in_every_place_pyinstaller_puts_a_module(tmp_path: Path) -> None:
    """PYZ, the archive's module entries, ``base_library.zip``, extension modules, built-ins."""
    base = zip_bytes({"encodings/__init__.pyc": b"", "codecs.pyc": b""})
    executable = make_exe(
        tmp_path / "onefile",
        [
            ("struct", pyc("struct"), "m"),
            ("base_library.zip", base, "x"),
            ("_ctypes.pyd", b"MZ", "b"),
            ("unicodedata.cp312-win_amd64.pyd", b"MZ", "b"),
        ],
        modules=["json", "ctypes", "ctypes.wintypes"],
    )
    have = build.bundled_modules(executable)
    for name in ("json", "ctypes.wintypes", "struct", "encodings", "codecs", "_ctypes"):
        assert name in have, name
    assert "unicodedata" in have
    assert "sys" in have  # built into the interpreter's DLL
    onedir = tmp_path / "onedir" / "Clearwater"
    tree(onedir / "_internal", ["select.pyd", "lib-dynload/_bz2.so"])
    (onedir / "_internal" / "base_library.zip").write_bytes(zip_bytes({"abc.pyc": b""}))
    exe = make_exe(onedir, [], modules=["os"])
    have = build.bundled_modules(exe)
    for name in ("select", "_bz2", "abc", "os"):
        assert name in have, name
    wanted = [build.HiddenImport(n, ("scan",)) for n in ("select", "abc", "graphlib")]
    assert build.missing_hidden_imports(exe, wanted) == [
        "hidden-import missing from the bundle: graphlib (scan)"
    ]


def _fake_pyinstaller(
    monkeypatch: pytest.MonkeyPatch, out: Path, modules: Sequence[str], seen: dict[str, Any]
) -> None:
    """Replace PyInstaller with a writer of a one-file release whose PYZ holds ``modules``."""

    def stand_in(args: Sequence[str]) -> None:
        seen["args"] = list(args)
        root = build.release_dir(out, "onefile", build.app_version())
        root.mkdir(parents=True, exist_ok=True)
        made = make_exe(tmp := out / "fake-sources", [], modules=["clearwater", *modules])
        shutil.move(str(made), root / "Clearwater.exe")
        shutil.rmtree(tmp)

    monkeypatch.setattr(build, "run_pyinstaller", stand_in)
    monkeypatch.setattr(build, "native_origin_violations", lambda *a, **kw: [])


@pytest.mark.parametrize(("bundle_has", "status"), [(["graphlib", "json"], 0), (["json"], 1)])
def test_a_missing_member_fails_the_build_and_the_set_is_written_to_the_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    bundle_has: list[str],
    status: int,
) -> None:
    """A build whose bundle lacks a member of the set exits 1 (a FAILURE, never a warning)."""
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    out = tmp_path / "out"
    source = tmp_path / "pack" / "mod.py"
    source.parent.mkdir(parents=True)
    source.write_text("import json\n", encoding="utf-8")
    monkeypatch.setattr(build, "pack_sources", lambda: [("pack:mod.py", source)])
    seen: dict[str, Any] = {}
    _fake_pyinstaller(monkeypatch, out, bundle_has, seen)
    assert build.build("onefile", out=out) == status
    printed = capsys.readouterr().out
    hidden = [seen["args"][i + 1] for i, a in enumerate(seen["args"]) if a == "--hidden-import"]
    assert hidden == ["graphlib", "json"]
    report = json.loads((out / "hidden-imports-onefile.json").read_text(encoding="utf-8"))
    assert report["hidden_imports"]["graphlib"]["sources"] == ["committed"]
    assert report["hidden_imports"]["json"]["sources"] == ["scan"]
    assert report["hidden_imports"]["json"]["named_by"] == ["pack:mod.py:1"]
    missing = "hidden-import missing from the bundle: graphlib (committed)"
    assert (missing in printed) == (status == 1)
    assert ("hidden-import check: PASS" in printed) == (status == 0)


def test_an_unparsable_pack_file_fails_the_build_before_pyinstaller(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Imports that cannot be read are unknown needs: the build stops, PyInstaller never runs."""
    bad = tmp_path / "bad.py"
    bad.write_text("def broken(:\n", encoding="utf-8")
    monkeypatch.setattr(build, "pack_sources", lambda: [("pack:bad.py", bad)])
    seen: dict[str, Any] = {}
    _fake_pyinstaller(monkeypatch, tmp_path / "out", [], seen)
    assert build.build("onefile", out=tmp_path / "out") == 1
    assert "args" not in seen
    assert "pack:bad.py: SyntaxError" in capsys.readouterr().out


def test_the_real_pack_scan_finds_ctypes_wintypes() -> None:
    """The locked pack's own ``.py`` files name ``ctypes.wintypes`` (the scan, not the list)."""
    try:
        sources = build.pack_sources()
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("the GPU pack distributions are not installed (the gpu extra)")
    scan = build.scan_stdlib_imports(sources)
    assert scan.unparsable == []
    assert any(p.startswith("cuda-pathfinder:") for p in scan.modules["ctypes.wintypes"])
    assert "graphlib" not in scan.modules  # the extension-only need the list carries


@pytest.mark.parametrize("before", [False, True])
@pytest.mark.parametrize("fails", [False, True])
def test_pack_sources_restores_bytecode_setting_after_success_or_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, before: bool, fails: bool
) -> None:
    """Reviewer B #4: scanning suppresses bytecode only until it returns or raises."""
    monkeypatch.setattr(sys, "dont_write_bytecode", before)

    def distribution(name: str) -> Any:
        assert sys.dont_write_bytecode is True
        if fails:
            raise RuntimeError("injected scan failure")
        return SimpleNamespace(
            version=next(row.version for row in gpu_pack.LOCKED_DISTRIBUTIONS if row.name == name),
            files=[importlib.metadata.PackagePath("sample.py")],
            locate_file=lambda file: tmp_path / file,
        )

    monkeypatch.setattr(importlib.metadata, "distribution", distribution)
    if fails:
        with pytest.raises(RuntimeError, match="injected scan failure"):
            build.pack_sources()
    else:
        rows = build.pack_sources()
        assert len(rows) == 11
        assert all(path == tmp_path / "sample.py" for _, path in rows)
    assert sys.dont_write_bytecode is before


# Reviewer A r3 #9, #11, #12.


def test_the_dependency_allowlist_is_case_folded() -> None:
    """#9: ``pyside6/QtCore.pyd`` and ``NUMPY/x.pyc`` are the allowed packages on Windows."""
    assert build.name_violations(["pyside6", "QtCore.pyd"], module_root=True) == []
    assert build.name_violations(["NUMPY", "x.pyc"], module_root=True) == []
    assert build.name_violations(["JSON.pyc"], module_root=True) == []  # a stdlib name
    assert build.name_violations(["AV", "x.pyd"], module_root=True) == ["unexpected-module"]


def test_a_pyz_containers_own_name_is_checked(tmp_path: Path) -> None:
    """#11: a PYZ entry named like a GPU binary is found, though its modules are clean."""
    executable = make_exe(tmp_path, [], modules=["json"], pyz_name="cupy/runtime.pyd")
    assert hits(build.forbidden_entries(executable), "pkg:cupy/runtime.pyd (gpu-module)")
    clean = make_exe(tmp_path / "clean", [], modules=["json"])
    assert build.forbidden_entries(clean) == []


def test_a_pack_distribution_at_another_version_fails_the_scan_and_the_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """#12: the scan compares each installed distribution's version with the lock."""
    try:
        real = importlib.metadata.distribution("cupy-cuda12x")
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("the GPU pack distributions are not installed (the gpu extra)")
    real_distribution = importlib.metadata.distribution

    class Stale:
        version = "0.0"
        files = real.files

        def locate_file(self, path: Any) -> Any:
            return real.locate_file(path)

    def distribution(name: str) -> Any:
        return Stale() if name == "cupy-cuda12x" else real_distribution(name)

    monkeypatch.setattr(importlib.metadata, "distribution", distribution)
    with pytest.raises(ValueError, match=r"cupy-cuda12x: installed 0.0, the lock has 14.2.0"):
        build.pack_sources()
    assert build.build("onedir", out=tmp_path / "out") == 1
    out = capsys.readouterr().out
    assert "FAILED: the pack sources cannot be scanned: cupy-cuda12x: installed 0.0" in out


def test_manifest_helpers_delegate_to_the_product_writer(tmp_path: Path, monkeypatch) -> None:
    document = {"format": 1, "stamp": gpu_pack.STAMP, "distributions": []}
    folder = tmp_path / gpu_pack.STAMP
    path = folder / "manifest.json"
    monkeypatch.setattr(
        gpu_pack_install, "manifest_document", lambda target: document if target == folder else None
    )
    monkeypatch.setattr(
        gpu_pack_install, "write_manifest", lambda target: path if target == folder else None
    )
    assert build.manifest_document(folder) is document
    assert build.write_manifest(folder) == path


@pytest.mark.parametrize(
    "args",
    [
        [
            "--form",
            "onedir",
            "--with-ffmpeg",
            "--ffmpeg-from",
            "file:///archive.zip",
            "--ffmpeg-sha256",
            "0" * 64,
        ],
        ["--form", "onedir", "--ffmpeg-from", "file:///archive.zip"],
        ["--form", "onedir", "--ffmpeg-sha256", "0" * 64],
        ["--form", "onedir", "--ffmpeg-from", "file:///archive.zip", "--ffmpeg-sha256", "nope"],
        ["--verify", "pack", "--ffmpeg-from", "file:///archive.zip", "--ffmpeg-sha256", "0" * 64],
    ],
)
def test_release_ffmpeg_options_refuse_conflicting_or_incomplete_requests(args):
    with pytest.raises(SystemExit) as caught:
        build.parse_args(args)
    assert caught.value.code == 2


def test_release_ffmpeg_options_reach_the_build(monkeypatch, tmp_path):
    seen = {}

    def run(form, **kwargs):
        seen.update(form=form, **kwargs)
        return 7

    monkeypatch.setattr(build, "build", run)
    assert (
        build.main(
            [
                "--form",
                "onedir",
                "--out",
                str(tmp_path),
                "--ffmpeg-from",
                "https://github.com/fixture/archive.zip",
                "--ffmpeg-sha256",
                "a" * 64,
            ]
        )
        == 7
    )
    assert seen == {
        "form": "onedir",
        "out": tmp_path,
        "with_ffmpeg": False,
        "ffmpeg_from": "https://github.com/fixture/archive.zip",
        "ffmpeg_sha256": "a" * 64,
        "notices": False,
        "smoke": False,
    }


@pytest.mark.parametrize("fail", [False, True])
def test_release_bundle_is_checked_in_the_built_executable_folder(
    monkeypatch, tmp_path, capsys, fail
):
    """Removing the bundle call, or ignoring its failure, must fail this contract."""
    pin = json.loads((REPO_ROOT / "tools/package/ffmpeg.lock.json").read_text(encoding="utf-8"))
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr(build, "pack_sources", lambda: [])
    out = tmp_path / "out"
    _fake_pyinstaller(monkeypatch, out, ["graphlib"], {})
    folder = build.release_dir(out, "onefile", build.app_version())

    def fetched(destination, *, out, url, sha256):
        assert (destination / "Clearwater.exe").is_file()
        if fail:
            raise RuntimeError("planted FFmpeg configuration mismatch")
        (destination / "ffmpeg-BUILD.txt").write_text(f"{out}\n{url}\n{sha256}", encoding="utf-8")
        return []

    monkeypatch.setattr(build, "bundle_ffmpeg", fetched)
    status = build.build(
        "onefile", out=out, ffmpeg_from=pin["asset_url"], ffmpeg_sha256=pin["github_sha256"]
    )
    printed = capsys.readouterr().out
    assert status == (1 if fail else 0)
    if fail:
        assert "FAILED: FFmpeg bundle: planted FFmpeg configuration mismatch" in printed
        assert "bundle check: PASS" not in printed
    else:
        assert (folder / "ffmpeg-BUILD.txt").read_text(encoding="utf-8") == (
            f"{out}\n{pin['asset_url']}\n{pin['github_sha256']}"
        )


def test_notices_option_reaches_build_and_refuses_non_onedir(monkeypatch, tmp_path):
    seen = {}

    def run(form, **kwargs):
        seen.update(form=form, **kwargs)
        return 7

    monkeypatch.setattr(build, "build", run)
    assert build.main(["--form", "onedir", "--notices", "--out", str(tmp_path)]) == 7
    assert seen["notices"] is True
    for args in (["--verify", "pack", "--notices"], ["--form", "onefile", "--notices"]):
        with pytest.raises(SystemExit) as caught:
            build.parse_args(args)
        assert caught.value.code == 2


@pytest.mark.parametrize("fails", [False, True])
def test_notices_writing_follows_ffmpeg_and_fails_the_build_on_error(
    monkeypatch, tmp_path, capsys, fails
):
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr(build, "native_origin_violations", lambda *a, **kw: [])
    monkeypatch.setattr(build, "pack_sources", lambda: [])
    out = tmp_path / "out"

    def build_folder(args):
        folder = Path(args[args.index("--distpath") + 1])
        folder.mkdir(parents=True, exist_ok=True)
        source = make_exe(out / "synthetic", [], modules=["clearwater", "graphlib"])
        shutil.copyfile(source, folder / "Clearwater.exe")

    monkeypatch.setattr(build, "run_pyinstaller", build_folder)

    def copy_tools(folder):
        (folder / "ffmpeg-BUILD.txt").write_text("FFmpeg step completed")
        return []

    def notices(folder):
        assert (folder / "ffmpeg-BUILD.txt").read_text() == "FFmpeg step completed"
        if fails:
            raise ValueError("planted notice coverage failure")
        path = folder / "THIRD_PARTY_NOTICES.md"
        path.write_text("generated notices")
        return path

    monkeypatch.setattr(build, "copy_ffmpeg", copy_tools)
    monkeypatch.setattr(build, "write_artifact_notices", notices, raising=False)
    assert build.build("onedir", out=out, with_ffmpeg=True, notices=True) == int(fails)
    printed = capsys.readouterr().out
    if fails:
        assert "FAILED: artifact notices: planted notice coverage failure" in printed
    else:
        assert "wrote" in printed and "THIRD_PARTY_NOTICES.md" in printed


@pytest.mark.parametrize("status", [0, 1])
def test_smoke_follows_notices_and_propagates_failure(monkeypatch, tmp_path, status):
    """Dropping --smoke or ignoring its result must not produce a successful build."""
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr(build, "native_origin_violations", lambda *a, **kw: [])
    monkeypatch.setattr(build, "pack_sources", lambda: [])
    out = tmp_path / "out"

    def build_folder(args):
        folder = Path(args[args.index("--distpath") + 1])
        folder.mkdir(parents=True, exist_ok=True)
        source = make_exe(out / "synthetic", [], modules=["clearwater", "graphlib"])
        shutil.copyfile(source, folder / "Clearwater.exe")

    monkeypatch.setattr(build, "run_pyinstaller", build_folder)

    def notices(folder):
        path = folder / "THIRD_PARTY_NOTICES.md"
        path.write_text("generated notices")
        return path

    called = []

    def smoke(folder, *, out):
        assert (folder / "THIRD_PARTY_NOTICES.md").read_text() == "generated notices"
        called.append(folder)
        return status

    monkeypatch.setattr(build, "write_artifact_notices", notices)
    monkeypatch.setattr(build, "smoke_artifact", smoke)
    assert build.main(["--form", "onedir", "--notices", "--smoke", "--out", str(out)]) == status
    assert len(called) == 1
