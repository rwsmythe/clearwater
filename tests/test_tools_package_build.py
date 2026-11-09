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
import re
import shutil
import stat
import struct
import subprocess
import sys
import zipfile
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

import clearwater
import test_tools_package_ffmpeg as ffmpeg_support
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


@pytest.fixture
def verified_ffmpeg_archive(tmp_path, monkeypatch):
    """Reuse the real archive/transport fixture with this module's build instance."""
    real_run = build.subprocess.run
    monkeypatch.setattr(ffmpeg_support, "build", build)
    fixture = ffmpeg_support.synthetic_bundle.__wrapped__(tmp_path, monkeypatch)
    launch_tool = build.subprocess.run

    def launch(args, **kwargs):
        # PyInstaller's archive writers may query the OS ("ver") before bundling.
        if (
            isinstance(args, (list, tuple))
            and args
            and Path(args[0]).name
            in {
                "ffmpeg.exe",
                "ffprobe.exe",
            }
        ):
            return launch_tool(args, **kwargs)
        return real_run(args, **kwargs)

    monkeypatch.setattr(build.subprocess, "run", launch)
    return fixture


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


DARWIN_SYSTEM_PATH = ["/usr/bin", "/bin", "/usr/sbin", "/sbin"]


@pytest.mark.parametrize("platform", ["win32", "darwin", "linux"])
@pytest.mark.parametrize("outcome", ["success", "failure"])
def test_analysis_uses_only_sanitized_path_and_restores_it(
    tmp_path, monkeypatch, platform, outcome
):
    """A foreign resolver candidate must disappear even when analysis fails.

    win32: the interpreter root and DLLs, venv Scripts, System32 and the Windows root.
    darwin (AD-36 form, CHARC note 2): the interpreter and venv ``bin``, then the four
    system directories; every ``DYLD_*`` variable removed and the two fallbacks pinned
    to the system locations for the analysis. Everything is restored after success and
    after failure. Any other platform (Linux) is refused before PyInstaller is imported.
    """
    foreign = tree(tmp_path / "foreign", ["foreign.dll", "libforeign.dylib"])
    base = tree(tmp_path / "python", ["DLLs/trusted.dll", "bin/python3.12"])
    venv = tmp_path / "venv"
    windows = tmp_path / "Windows"
    original = str(foreign)
    monkeypatch.setenv("PATH", original)
    monkeypatch.setenv("SystemRoot", str(windows))
    inherited_dyld = {
        "DYLD_LIBRARY_PATH": str(foreign),
        "DYLD_FRAMEWORK_PATH": str(foreign),
        "DYLD_INSERT_LIBRARIES": str(foreign / "libforeign.dylib"),
        "DYLD_FALLBACK_LIBRARY_PATH": str(foreign),
    }
    for name, value in inherited_dyld.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("DYLD_FALLBACK_FRAMEWORK_PATH", raising=False)
    monkeypatch.setattr(build.sys, "base_prefix", str(base))
    monkeypatch.setattr(build.sys, "prefix", str(venv))
    monkeypatch.setattr(build.sys, "platform", platform)
    seen = []

    def analysis(args):
        seen.append(dict(os.environ))
        resolved = next(
            (
                Path(part) / leaf
                for part in os.environ["PATH"].split(os.pathsep)
                for leaf in ("foreign.dll", "libforeign.dylib")
                if (Path(part) / leaf).is_file()
            ),
            None,
        )
        assert resolved is None
        if outcome == "failure":
            raise RuntimeError("analysis failed")

    real_import = build.importlib.import_module
    monkeypatch.setattr(
        build.importlib,
        "import_module",
        lambda name: (
            SimpleNamespace(run=analysis) if name == "PyInstaller.__main__" else real_import(name)
        ),
    )
    before = dict(os.environ)
    if platform == "linux":
        with pytest.raises(build.BuildEnvironmentError, match=r"linux.*Linux.*not supported"):
            build.run_pyinstaller([])
        assert seen == []
    elif outcome == "failure":
        with pytest.raises(RuntimeError, match="analysis failed"):
            build.run_pyinstaller([])
    else:
        build.run_pyinstaller([])
    assert dict(os.environ) == before
    assert os.environ["PATH"] == original
    if platform == "linux":
        return
    (environment,) = seen
    path = environment["PATH"].split(os.pathsep)
    if platform == "win32":
        assert path == [
            str(base),
            str(base / "DLLs"),
            str(venv / "Scripts"),
            str(windows / "System32"),
            str(windows),
        ]
        assert {k: v for k, v in environment.items() if k.startswith("DYLD_")} == inherited_dyld
    else:
        assert path == [str(base / "bin"), str(venv / "bin"), *DARWIN_SYSTEM_PATH]
        assert {k: v for k, v in environment.items() if k.startswith("DYLD_")} == {
            "DYLD_FALLBACK_LIBRARY_PATH": "/usr/lib",
            "DYLD_FALLBACK_FRAMEWORK_PATH": "/System/Library/Frameworks",
        }


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


@pytest.mark.parametrize("tampered", [False, True])
def test_build_enforces_origin_after_all_native_copies(
    tmp_path, monkeypatch, capsys, tampered, verified_ffmpeg_archive
):
    """Verified tool bytes pass, but a post-extraction change fails the real gate."""
    pin, _source, destination, _out, members, *_ = verified_ffmpeg_archive
    out = destination.parent
    monkeypatch.setattr(build, "release_dir", lambda *a: destination)
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr(build, "pack_sources", lambda: [])
    check = build.native_origin_violations
    _fake_pyinstaller(monkeypatch, out, ["graphlib"], {})
    monkeypatch.setattr(build, "native_origin_violations", check)
    monkeypatch.setattr(build, "_native_origin_hashes", lambda: set())
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True)
    real_bundle = build.bundle_ffmpeg

    def bundle(*args, **kwargs):
        result = real_bundle(*args, **kwargs)
        if tampered:
            (destination / "ffmpeg.exe").write_bytes(b"changed after extraction")
        return result

    monkeypatch.setattr(build, "bundle_ffmpeg", bundle)
    foreign = tree(tmp_path / "foreign", ["ffmpeg.exe"])
    monkeypatch.setenv("PATH", str(foreign))
    assert build.build(
        "onefile", out=out, ffmpeg_from=pin["asset_url"], ffmpeg_sha256=pin["github_sha256"]
    ) == int(tampered)
    if not tampered:
        assert (destination / "ffmpeg.exe").read_bytes() == members[
            pin["archive_root"] + "/bin/ffmpeg.exe"
        ]
    output = capsys.readouterr().out
    assert ("native origin check: PASS" in output) == (not tampered)
    if tampered:
        assert str(foreign / "ffmpeg.exe") in output


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
    """F6: a stale ``ffmpeg.exe`` from an earlier bundle is gone."""
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    out = tmp_path / "out"
    release = build.release_dir(out, "onefile", build.app_version())
    tree(release, ["Clearwater.exe", "ffmpeg.exe", "ffprobe.exe"])
    beside = tree(out, ["keep.txt"])
    seen: dict[str, Any] = {}
    _stopping_build(monkeypatch, out, seen)
    assert "ffmpeg.exe" not in seen["release"]
    assert (beside / "keep.txt").is_file()  # only the release folder is cleaned


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


def test_retired_with_ffmpeg_option_is_unknown(monkeypatch, capsys):
    """The retired PATH-copy option cannot select a build path."""
    monkeypatch.setattr(build, "build", lambda *a, **kw: 0)
    with pytest.raises(SystemExit) as caught:
        build.main(["--form", "onedir", "--with-ffmpeg"])
    assert caught.value.code == 2
    assert "unrecognized arguments: --with-ffmpeg" in capsys.readouterr().err


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
        "ffmpeg_from": "https://github.com/fixture/archive.zip",
        "ffmpeg_sha256": "a" * 64,
        "notices": False,
        "smoke": False,
        "zip_release": False,
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

    def fetched(destination, *, out, url, sha256, verified_hashes):
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
    monkeypatch, tmp_path, capsys, fails, verified_ffmpeg_archive
):
    """Notices see the verified archive's material; a notice failure still refuses the build."""
    pin, _source, destination, _out, members, *_ = verified_ffmpeg_archive
    out = destination.parent
    monkeypatch.setattr(build, "release_dir", lambda *a: destination)
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr(build, "native_origin_violations", lambda *a, **kw: [])
    monkeypatch.setattr(build, "pack_sources", lambda: [])

    def build_folder(args):
        folder = Path(args[args.index("--distpath") + 1])
        folder.mkdir(parents=True, exist_ok=True)
        source = make_exe(out / "synthetic", [], modules=["clearwater", "graphlib"])
        shutil.copyfile(source, folder / "Clearwater.exe")

    monkeypatch.setattr(build, "run_pyinstaller", build_folder)

    def notices(folder):
        for tool in ("ffmpeg", "ffprobe"):
            assert (folder / f"{tool}.exe").read_bytes() == members[
                pin["archive_root"] + f"/bin/{tool}.exe"
            ]
        assert pin["github_sha256"] in (folder / "ffmpeg-BUILD.txt").read_text()
        if fails:
            raise ValueError("planted notice coverage failure")
        path = folder / "THIRD_PARTY_NOTICES.md"
        path.write_text("generated notices")
        return path

    monkeypatch.setattr(build, "write_artifact_notices", notices, raising=False)
    assert build.build(
        "onedir",
        out=out,
        ffmpeg_from=pin["asset_url"],
        ffmpeg_sha256=pin["github_sha256"],
        notices=True,
    ) == int(fails)
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


def test_zip_option_selects_only_a_checked_onedir_build(monkeypatch, tmp_path):
    """The workflow's --zip must parse and reach the release build."""
    seen = {}

    def run(form, **kwargs):
        seen.update(form=form, **kwargs)
        return 7

    monkeypatch.setattr(build, "build", run)
    pin = build.load_ffmpeg_lock()
    assert (
        build.main(
            [
                "--form",
                "onedir",
                "--notices",
                "--smoke",
                "--zip",
                "--out",
                str(tmp_path),
                "--ffmpeg-from",
                pin["asset_url"],
                "--ffmpeg-sha256",
                pin["github_sha256"],
            ]
        )
        == 7
    )
    assert seen["zip_release"] is True
    assert seen["ffmpeg_from"] == pin["asset_url"]
    assert seen["ffmpeg_sha256"] == pin["github_sha256"]
    for args in (
        ["--form", "onefile", "--zip"],
        ["--verify", "pack", "--zip"],
        ["--smoke", "folder", "--zip"],
        ["--form", "onedir", "--zip"],
        ["--form", "onedir", "--zip", "--notices"],
        ["--form", "onedir", "--zip", "--smoke"],
    ):
        with pytest.raises(SystemExit) as caught:
            build.parse_args(args)
        assert caught.value.code == 2


def test_zip_requires_verified_ffmpeg_arguments_and_refuses_before_build(
    tmp_path, monkeypatch, capsys
):
    """A release zip must not publish a distribution without the verified FFmpeg pair."""
    with pytest.raises(SystemExit, match="2"):
        build.parse_args(["--form", "onedir", "--notices", "--smoke", "--zip"])
    assert "--zip requires --ffmpeg-from and --ffmpeg-sha256" in capsys.readouterr().err
    monkeypatch.setattr(build, "pack_sources", lambda: pytest.fail("scan reached"))
    assert build.build("onedir", out=tmp_path, notices=True, smoke=True, zip_release=True) == 1
    assert "--zip requires --ffmpeg-from and --ffmpeg-sha256" in capsys.readouterr().out


def test_release_zip_is_deterministic_and_has_fixed_metadata(tmp_path):
    """Neither creation order, file mode nor filesystem mtime may alter release bytes."""
    payloads = {
        "Clearwater/Clearwater.exe": b"synthetic executable",
        "Clearwater/_internal/native.dll": b"synthetic native",
        "Clearwater/THIRD_PARTY_NOTICES.md": b"synthetic notices\n",
    }
    snapshots = []
    for index, names in enumerate((list(payloads), list(reversed(payloads)))):
        root = tmp_path / str(index) / "Clearwater-1.1.0-windows-onedir"
        for name in names:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payloads[name])
            os.utime(path, (946684800 + index * 10000, 946684800 + index * 10000))
            path.chmod(0o666 if index else 0o444)
        archive = build.write_release_zip(root, out=root.parent, source_epoch=1793908801)
        snapshots.append(archive.read_bytes())
        assert archive == root.parent / (root.name + ".zip")
        with zipfile.ZipFile(archive) as packed:
            assert packed.namelist() == sorted(root.name + "/" + name for name in payloads)
            assert len(packed.infolist()) == sum(p.is_file() for p in root.rglob("*")) == 3
            assert packed.testzip() is None
            for info in packed.infolist():
                assert info.date_time == (2026, 11, 5, 20, 0, 0)
                assert info.create_system == 3
                assert info.external_attr == (stat.S_IFREG | 0o644) << 16
                assert info.compress_type == zipfile.ZIP_DEFLATED
                assert info.extra == info.comment == b""
                assert info.internal_attr == 0
                assert packed.read(info) == payloads[info.filename.removeprefix(root.name + "/")]
        sidecar = archive.with_suffix(".zip.sha256")
        expected = (
            hashlib.sha256(snapshots[-1]).hexdigest().encode() + b"  " + archive.name.encode()
        )
        assert sidecar.read_bytes() == expected + b"\n"
        # Add-Content -Encoding ascii appends its value and a platform newline.
        with sidecar.open("ab") as stream:
            stream.write(b"# source-commit: " + b"a" * 40 + b"\r\n")
        assert sidecar.read_bytes().splitlines() == [expected, b"# source-commit: " + b"a" * 40]
        for path in root.rglob("*"):
            if path.is_file():
                path.chmod(0o666)
    assert snapshots[0] == snapshots[1]


@pytest.mark.parametrize("epoch", [0, 4354819200])
def test_release_zip_refuses_unrepresentable_commit_time(tmp_path, epoch):
    """Out-of-range source dates fail before publishing instead of inheriting today's date."""
    root = tree(tmp_path / "release", ["Clearwater/Clearwater.exe"])
    with pytest.raises(ValueError, match=r"ZIP.*(time|date)"):
        build.write_release_zip(root, out=tmp_path, source_epoch=epoch)
    assert not list(tmp_path.glob("*.zip*"))


def test_source_commit_epoch_uses_a_bounded_read_only_git_query(monkeypatch):
    """Build timestamps come from the checked-out commit, never filesystem metadata."""

    def git(args, **kwargs):
        assert args == ["git", "log", "-1", "--format=%ct", "HEAD"]
        assert kwargs["cwd"] == build.REPO_ROOT
        assert kwargs["timeout"] <= 30
        assert kwargs["check"] is True
        return subprocess.CompletedProcess(args, 0, "1793908801\n", "")

    monkeypatch.setattr(build.subprocess, "run", git)
    assert build.source_commit_epoch() == 1793908801


@pytest.mark.parametrize("failure", ["none", "notices", "smoke", "timestamp"])
def test_zip_is_published_only_after_successful_notices_and_smoke(
    tmp_path, monkeypatch, capsys, failure
):
    """The smoke early return must fall through to zip only on success."""
    out = tmp_path / "out"
    monkeypatch.setattr(build, "pack_sources", lambda: [])
    _fake_pyinstaller(monkeypatch, out, ["graphlib"], {})
    root = build.release_dir(out, "onedir", build.app_version())
    monkeypatch.setattr(build, "release_dir", lambda *a: root)
    stale = out / (root.name + ".zip")
    out.mkdir(parents=True, exist_ok=True)
    stale.write_bytes(b"previous release")
    stale.with_suffix(".zip.sha256").write_bytes(b"previous checksum\n")
    original_sources = build.pack_sources

    def checked_sources():
        assert not stale.exists() and not stale.with_suffix(".zip.sha256").exists()
        return original_sources()

    monkeypatch.setattr(build, "pack_sources", checked_sources)
    order = []

    def notices(folder):
        order.append("notices")
        if failure == "notices":
            raise ValueError("planted notices failure")
        path = folder / "THIRD_PARTY_NOTICES.md"
        path.write_text("synthetic notices\n")
        return path

    def smoke(folder, *, out):
        assert (folder / "THIRD_PARTY_NOTICES.md").is_file()
        order.append("smoke")
        return int(failure == "smoke")

    def epoch():
        assert order == ["notices", "smoke"]
        if failure == "timestamp":
            raise ValueError("planted source timestamp failure")
        return 1793908801

    monkeypatch.setattr(build, "write_artifact_notices", notices)
    monkeypatch.setattr(build, "smoke_artifact", smoke)
    monkeypatch.setattr(build, "source_commit_epoch", epoch, raising=False)
    pin = build.load_ffmpeg_lock()
    # Bundle validation is exercised by the synthetic-archive cases; this case
    # isolates zip ordering/publication from executable loading and transport.
    monkeypatch.setattr(build, "bundle_ffmpeg", lambda *a, **kw: [])
    status = build.build(
        "onedir",
        out=out,
        notices=True,
        smoke=True,
        zip_release=True,
        ffmpeg_from=pin["asset_url"],
        ffmpeg_sha256=pin["github_sha256"],
    )
    assert status == int(failure != "none")
    assert order == (["notices"] if failure == "notices" else ["notices", "smoke"])
    archive = out / (root.name + ".zip")
    assert archive.exists() == archive.with_suffix(".zip.sha256").exists() == (failure == "none")
    if failure == "none":
        with zipfile.ZipFile(archive) as packed:
            assert root.name + "/THIRD_PARTY_NOTICES.md" in packed.namelist()
    if failure == "timestamp":
        assert "FAILED: release zip: planted source timestamp failure" in capsys.readouterr().out


@pytest.mark.skipif(sys.platform != "win32", reason="Windows junction regression")
def test_release_zip_refuses_junctions(tmp_path):
    """A junction must never import another directory's bytes into the release."""
    import _winapi

    root = tree(tmp_path / "release", ["Clearwater/Clearwater.exe"])
    outside = tree(tmp_path / "outside", ["secret.txt"])
    junction = root / "Clearwater/j"
    _winapi.CreateJunction(str(outside), str(junction))
    assert junction.is_junction() and not junction.is_symlink()
    with pytest.raises(ValueError, match=r"(junction|linked|outside)"):
        build.write_release_zip(root, out=tmp_path, source_epoch=1793908801)
    assert not list(tmp_path.glob("*.zip*"))
    assert (outside / "secret.txt").is_file()


@pytest.mark.parametrize("mutation", ["added", "removed", "changed"])
def test_release_zip_refuses_smoke_mutations(tmp_path, monkeypatch, capsys, mutation):
    """The published file set and identities must equal the pre-smoke inventory."""
    out = tmp_path / "out"
    monkeypatch.setattr(build, "pack_sources", lambda: [])
    _fake_pyinstaller(monkeypatch, out, ["graphlib"], {})
    root = build.release_dir(out, "onedir", build.app_version())
    monkeypatch.setattr(build, "release_dir", lambda *a: root)

    def notices(folder):
        target = folder / "THIRD_PARTY_NOTICES.md"
        target.write_bytes(b"covered bytes\n")
        return target

    def smoke(folder, *, out):
        target = folder / "THIRD_PARTY_NOTICES.md"
        assert target.read_bytes() == b"covered bytes\n"
        if mutation == "added":
            (folder / "new-file.txt").write_bytes(b"uncovered bytes")
        elif mutation == "removed":
            target.unlink()
        else:
            # Same size, so a path/size-only snapshot would fail this control.
            target.write_bytes(b"altered bytes\n")
        return 0

    monkeypatch.setattr(build, "write_artifact_notices", notices)
    monkeypatch.setattr(build, "smoke_artifact", smoke)
    monkeypatch.setattr(build, "source_commit_epoch", lambda: 1793908801)
    pin = build.load_ffmpeg_lock()
    # Keep this test focused on the pre-smoke snapshot rather than transport.
    monkeypatch.setattr(build, "bundle_ffmpeg", lambda *a, **kw: [])
    assert (
        build.build(
            "onedir",
            out=out,
            notices=True,
            smoke=True,
            zip_release=True,
            ffmpeg_from=pin["asset_url"],
            ffmpeg_sha256=pin["github_sha256"],
        )
        == 1
    )
    message = capsys.readouterr().out
    assert "release zip" in message and mutation in message
    assert ("new-file.txt" if mutation == "added" else "THIRD_PARTY_NOTICES.md") in message
    assert not (out / (root.name + ".zip")).exists()
    assert not (out / (root.name + ".zip.sha256")).exists()


@pytest.mark.parametrize("mutation", ["none", "changed-tool", "unknown", "unextracted"])
def test_verified_archive_origin_accepts_only_extracted_tool_bytes(
    monkeypatch, verified_ffmpeg_archive, mutation
):
    """Hashing all archive entries or the destination files would grant false trust."""
    pin, _source, destination, out, members, *_ = verified_ffmpeg_archive
    hashes = set()
    build.bundle_ffmpeg(
        destination,
        out=out,
        url=pin["asset_url"],
        sha256=pin["github_sha256"],
        verified_hashes=hashes,
    )
    assert hashes == {
        hashlib.sha256(members[pin["archive_root"] + "/bin/" + tool + ".exe"]).hexdigest()
        for tool in ("ffmpeg", "ffprobe")
    }
    if mutation == "changed-tool":
        (destination / "ffmpeg.exe").write_bytes(b"changed bytes")
    elif mutation == "unknown":
        (destination / "unknown.dll").write_bytes(b"unknown native")
    elif mutation == "unextracted":
        (destination / "renamed.dll").write_bytes(members[pin["archive_root"] + "/bin/ffplay.exe"])
    monkeypatch.setattr(build, "_native_origin_hashes", lambda: set())
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True)
    monkeypatch.setattr(build, "read_package", lambda _: SimpleNamespace(toc={}))
    errors = build.native_origin_violations(
        destination / "Clearwater.exe", original_path="", ffmpeg_hashes=hashes
    )
    if mutation == "none":
        assert errors == []
    else:
        label = {
            "changed-tool": "ffmpeg.exe",
            "unknown": "unknown.dll",
            "unextracted": "renamed.dll",
        }[mutation]
        assert len(errors) == 1 and label in errors[0]


@pytest.mark.parametrize("failure", ["digest", "download", "inventory", "version"])
def test_unverified_or_rejected_archive_never_publishes_origin_hashes(
    monkeypatch, verified_ffmpeg_archive, failure
):
    """Neither a failed archive check nor a partial tool check can bless native bytes."""
    pin, source, destination, out, _members, write, *_ = verified_ffmpeg_archive
    if failure == "download":
        payload = bytearray(source.read_bytes())
        payload[-1] ^= 1
        source.write_bytes(payload)
    elif failure == "inventory":
        write(extra=[("../escape.dll", b"unsafe")])
    elif failure == "version":

        def refuse(*args):
            raise RuntimeError("planted tool version failure")

        monkeypatch.setattr(build, "_pinned_ffmpeg_version", refuse)
    hashes = set()
    with pytest.raises((ValueError, RuntimeError)):
        build.bundle_ffmpeg(
            destination,
            out=out,
            url=pin["asset_url"],
            sha256="0" * 64 if failure == "digest" else pin["github_sha256"],
            verified_hashes=hashes,
        )
    assert hashes == set()
    (destination / "ffmpeg.exe").write_bytes(b"unverified tool")
    monkeypatch.setattr(build, "_native_origin_hashes", lambda: set())
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True)
    monkeypatch.setattr(build, "read_package", lambda _: SimpleNamespace(toc={}))
    assert any(
        "ffmpeg.exe" in error
        for error in build.native_origin_violations(
            destination / "Clearwater.exe", original_path="", ffmpeg_hashes=hashes
        )
    )


def test_verified_member_hashes_come_from_archive_streams_not_destination_files(
    monkeypatch, verified_ffmpeg_archive
):
    """A corrupted extraction write must not be promoted into a trusted identity."""
    from contextlib import contextmanager

    pin, _source, destination, out, members, *_ = verified_ffmpeg_archive
    real_open = Path.open

    @contextmanager
    def opened(path, mode="r", *args, **kwargs):
        with real_open(path, mode, *args, **kwargs) as stream:
            if path == destination / "ffmpeg.exe" and mode == "wb":

                class CorruptingOutput:
                    def write(self, data):
                        return stream.write(b"MZ" + data[2:])

                yield CorruptingOutput()
            else:
                yield stream

    monkeypatch.setattr(Path, "open", opened)
    # Isolate identity collection from the native execution boundary. The other
    # fixture tests run the real bounded version/configuration checks.
    monkeypatch.setattr(build, "_pinned_ffmpeg_version", lambda path, lock: "version stub")
    hashes = set()
    build.bundle_ffmpeg(
        destination,
        out=out,
        url=pin["asset_url"],
        sha256=pin["github_sha256"],
        verified_hashes=hashes,
    )
    archive_bytes = members[pin["archive_root"] + "/bin/ffmpeg.exe"]
    assert (destination / "ffmpeg.exe").read_bytes() != archive_bytes
    assert hashlib.sha256(archive_bytes).hexdigest() in hashes
    assert hashlib.sha256((destination / "ffmpeg.exe").read_bytes()).hexdigest() not in hashes


# --- macOS Mach-O origin identity (WP6.5, CHARC note 2) ---------------------------------
# Synthetic thin and fat Mach-O images written with struct from the Mach-O layout
# (<mach-o/loader.h>, <mach-o/fat.h>); the constants are this test's own, not build.py's.

MH_MAGIC_64 = 0xFEEDFACF
FAT_MAGIC = 0xCAFEBABE
CPU_ARM64 = 0x0100000C
CPU_X86_64 = 0x01000007
MH_DYLIB = 6
MH_EXECUTE = 2
LC_SYMTAB = 0x2
LC_LOAD_DYLIB = 0xC
LC_ID_DYLIB = 0xD
LC_SEGMENT_64 = 0x19
LC_UUID = 0x1B
LC_CODE_SIGNATURE = 0x1D
LC_SOURCE_VERSION = 0x2A
LC_BUILD_VERSION = 0x32
LC_RPATH = 0x8000001C
TEXT_OFFSET = 0x400
ARM64_CODE = bytes.fromhex("1f2003d5") * 16
X86_CODE = b"\x90" * 64


def _load_command(cmd: int, payload: bytes) -> bytes:
    padded = payload + bytes(-(8 + len(payload)) % 8)
    return struct.pack("<II", cmd, 8 + len(padded)) + padded


def _dylib(cmd: int, name: str) -> bytes:
    return _load_command(cmd, struct.pack("<IIII", 24, 2, 0x10000, 0x10000) + name.encode() + b"\0")


def _segment(name: bytes, fileoff: int, filesize: int, sections: Sequence[Any] = ()) -> bytes:
    payload = struct.pack(
        "<16sQQQQiiII",
        name,
        0x100000000 + fileoff,
        filesize,
        fileoff,
        filesize,
        7,
        5,
        len(sections),
        0,
    )
    for sectname, offset, size in sections:
        payload += struct.pack(
            "<16s16sQQIIIIIIII",
            sectname,
            name,
            0x100000000 + offset,
            size,
            offset,
            2,
            0,
            0,
            0x80000400,
            0,
            0,
            0,
        )
    return _load_command(LC_SEGMENT_64, payload)


def macho(
    *,
    cpu: int = CPU_ARM64,
    filetype: int = MH_DYLIB,
    code: bytes = ARM64_CODE,
    linkedit: bytes = b"symbols\0strings\0",
    names: Sequence[str] = (),
    dylib_id: str | None = None,
    rpaths: Sequence[str] = (),
    signature: bytes | None = None,
    uuid: bytes = b"\x11" * 16,
    sdk: int = 0x000E0000,
    strsize: int | None = None,
    extra: Sequence[bytes] = (),
) -> bytes:
    """A thin 64-bit Mach-O image: __TEXT (header + one section), __LINKEDIT, commands."""
    linkedit_offset = TEXT_OFFSET + len(code)
    end = linkedit_offset + len(linkedit) + len(signature or b"")
    symtab = (linkedit_offset, 1, linkedit_offset, len(linkedit) if strsize is None else strsize)
    commands = [
        _segment(b"__TEXT", 0, linkedit_offset, [(b"__text", TEXT_OFFSET, len(code))]),
        _segment(b"__LINKEDIT", linkedit_offset, end - linkedit_offset),
        _load_command(LC_SYMTAB, struct.pack("<IIII", *symtab)),
        _load_command(LC_UUID, uuid),
        _load_command(LC_BUILD_VERSION, struct.pack("<IIII", 1, 0x000B0000, sdk, 0)),
    ]
    if dylib_id is not None:
        commands.append(_dylib(LC_ID_DYLIB, dylib_id))
    commands += [_dylib(LC_LOAD_DYLIB, name) for name in names]
    commands += list(extra)
    commands += [
        _load_command(LC_RPATH, struct.pack("<I", 12) + path.encode() + b"\0") for path in rpaths
    ]
    if signature is not None:
        signed = struct.pack("<II", linkedit_offset + len(linkedit), len(signature))
        commands.append(_load_command(LC_CODE_SIGNATURE, signed))
    body = b"".join(commands)
    header = struct.pack(
        "<IiiIIIII", MH_MAGIC_64, cpu, 0, filetype, len(commands), len(body), 0x85, 0
    )
    image = header + body
    assert len(image) <= TEXT_OFFSET
    return image + bytes(TEXT_OFFSET - len(image)) + code + linkedit + (signature or b"")


def fat(*slices: tuple[int, bytes]) -> bytes:
    """A universal file: FAT_MAGIC header, then each slice at a 16 KiB boundary."""
    table = b""
    offset = 0x4000
    placed = []
    for cpu, image in slices:
        table += struct.pack(">iiIII", cpu, 0, offset, len(image), 14)
        placed.append((offset, image))
        offset += -(-len(image) // 0x4000) * 0x4000
    data = bytearray(offset)
    data[: 8 + len(table)] = struct.pack(">II", FAT_MAGIC, len(slices)) + table
    for start, image in placed:
        data[start : start + len(image)] = image
    return bytes(data)


ORIGINAL_NAMES = ("/opt/homebrew/opt/foo/lib/libfoo.1.dylib", "/usr/lib/libSystem.B.dylib")
BUILT_NAMES = ("@rpath/libfoo.1.dylib", "/usr/lib/libSystem.B.dylib")


def original_native(**changes: Any) -> bytes:
    """A wheel's dylib as installed: absolute names, its own rpaths, a linker signature."""
    fields: dict[str, Any] = {
        "names": ORIGINAL_NAMES,
        "dylib_id": "/opt/build/lib/libbar.dylib",
        "rpaths": ("/opt/homebrew/lib", "@loader_path/.dylibs"),
        "signature": b"S" * 32,
    }
    return macho(**{**fields, **changes})


def built_native(depth: int = 0, **changes: Any) -> bytes:
    """What PyInstaller writes: @rpath names and id, one rpath of the depth, re-signed."""
    fields: dict[str, Any] = {
        "names": BUILT_NAMES,
        "dylib_id": "@rpath/libbar.dylib",
        "rpaths": ("@loader_path" + "/.." * depth,),
        "signature": b"T" * 48,
    }
    return macho(**{**fields, **changes})


def macos_origin_check(tmp_path, monkeypatch, platform, original, built, *, relative, name):
    """Run the real origin check with ``original`` as the only interpreter native."""
    base = tree(tmp_path / "python", [f"lib/{name}"], original)
    monkeypatch.setattr(build.sys, "base_prefix", str(base))
    monkeypatch.setattr(build, "_locked_native_distributions", lambda: [])
    monkeypatch.setattr(build.sys, "platform", platform)
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True)
    monkeypatch.setattr(build, "read_package", lambda _: SimpleNamespace(toc={}))
    home = tree(tmp_path / "dist" / "Clearwater", ["Clearwater"], b"bootloader stand-in")
    tree(home, [relative], built)
    return build.native_origin_violations(home / "Clearwater", original_path="")


def fat_original() -> bytes:
    return fat(
        (CPU_X86_64, original_native(cpu=CPU_X86_64, code=X86_CODE)),
        (CPU_ARM64, original_native()),
    )


ADMITTED_TRANSFORMS = {
    "re-signed": (original_native(), built_native(), "libbar.dylib", "_internal/libbar.dylib"),
    "dylib-names-rewritten": (
        original_native(rpaths=("@loader_path/..",)),
        built_native(2),
        "libbar.dylib",
        "_internal/pkg/sub/libbar.dylib",
    ),
    "rpath-replaced": (
        original_native(rpaths=("/opt/x", "/opt/y", "@loader_path/../lib")),
        built_native(1),
        "libbar.dylib",
        "_internal/pkg/libbar.dylib",
    ),
    "unsigned-original": (
        original_native(signature=None),
        built_native(),
        "libbar.dylib",
        "_internal/libbar.dylib",
    ),
    "fat-original-arm64-slice": (
        fat_original(),
        built_native(),
        "libbar.dylib",
        "_internal/libbar.dylib",
    ),
    "framework-binary-without-suffix": (
        original_native(dylib_id="/opt/qt/lib/QtCore.framework/Versions/A/QtCore"),
        built_native(6, dylib_id="@rpath/QtCore"),
        "QtCore",
        "_internal/PySide6/Qt/lib/QtCore.framework/Versions/A/QtCore",
    ),
}


@pytest.mark.parametrize("case", sorted(ADMITTED_TRANSFORMS))
def test_macho_identity_admits_each_pyinstaller_transformation(tmp_path, monkeypatch, case):
    """Each PyInstaller rewrite passes on darwin and fails under the whole-file rule (win32)."""
    original, built, name, relative = ADMITTED_TRANSFORMS[case]
    old = macos_origin_check(
        tmp_path / "old", monkeypatch, "win32", original, built, relative=relative, name=name
    )
    assert old == [f"native origin unknown: {relative}"]
    new = macos_origin_check(
        tmp_path / "new", monkeypatch, "darwin", original, built, relative=relative, name=name
    )
    assert new == []


REFUSED_IMAGES = {
    "changed-text-byte": built_native(code=ARM64_CODE[:-1] + b"\x00"),
    "added-load-command": built_native(
        extra=(_load_command(LC_SOURCE_VERSION, struct.pack("<Q", 1)),)
    ),
    "different-basename": built_native(names=("@rpath/libother.1.dylib", BUILT_NAMES[1])),
    "system-dependency-redirected": built_native(
        names=(BUILT_NAMES[0], "@rpath/libSystem.B.dylib")
    ),
    "changed-linkedit": built_native(linkedit=b"symbols\0strings\1"),
    "x86_64-slice-transformed": macho(
        cpu=CPU_X86_64,
        code=X86_CODE,
        names=BUILT_NAMES,
        dylib_id="@rpath/libbar.dylib",
        rpaths=("@loader_path",),
        signature=b"T" * 48,
    ),
    "x86_64-slice-untouched": original_native(cpu=CPU_X86_64, code=X86_CODE),
    "foreign-file": macho(
        code=bytes.fromhex("000080d2") * 16, names=BUILT_NAMES, rpaths=("@loader_path",)
    ),
    # A r1 #2: the string table's final terminator dropped under the same declared strsize.
    "dropped-final-string-terminator": built_native(linkedit=b"symbols\0strings", strsize=16),
    # A r1 #3: bytes after the declared segments (and the signature) are unexplained.
    "appended-trailer": built_native() + b"unexplained trailer",
    # The declared signature reaches past __LINKEDIT's (and the file's) end.
    "signature-outside-linkedit": built_native(
        signature=None,
        extra=(
            _load_command(
                LC_CODE_SIGNATURE,
                struct.pack("<II", TEXT_OFFSET + len(ARM64_CODE) + 8, 64),
            ),
        ),
    ),
}


@pytest.mark.parametrize("case", sorted(REFUSED_IMAGES))
def test_macho_identity_refuses_changed_or_foreign_images(tmp_path, monkeypatch, case):
    """Code, commands, names, slices and foreign files outside the normalisation are refused."""
    found = macos_origin_check(
        tmp_path,
        monkeypatch,
        "darwin",
        fat_original(),
        REFUSED_IMAGES[case],
        relative="_internal/libbar.dylib",
        name="libbar.dylib",
    )
    assert found == ["native origin unknown: _internal/libbar.dylib"]


LOCATION_FAULTS = {
    "rpath-depth-too-shallow": (
        "_internal/pkg/sub/libbar.dylib",
        built_native(0),
        "LC_RPATH ['@loader_path'] is not the one '@loader_path/../..' of its location",
    ),
    "rpath-depth-too-deep": (
        "_internal/libbar.dylib",
        built_native(1),
        "LC_RPATH ['@loader_path/..'] is not the one '@loader_path' of its location",
    ),
    "two-rpaths": (
        "_internal/libbar.dylib",
        built_native(rpaths=("@loader_path", "@executable_path")),
        "LC_RPATH ['@loader_path', '@executable_path'] is not the one '@loader_path'",
    ),
    "no-rpath-for-rpath-dependency": (
        "_internal/libbar.dylib",
        built_native(rpaths=()),
        "LC_RPATH [] is not the one '@loader_path' of its location",
    ),
    "foreign-rpath": (
        "_internal/libbar.dylib",
        built_native(rpaths=("/usr/local/lib",)),
        "LC_RPATH ['/usr/local/lib'] is not the one '@loader_path'",
    ),
    "absolute-dependency-name": (
        "_internal/libbar.dylib",
        built_native(names=("/usr/local/lib/libfoo.1.dylib", BUILT_NAMES[1])),
        "dylib name '/usr/local/lib/libfoo.1.dylib' is not @rpath/<basename>",
    ),
    "id-not-rpath": (
        "_internal/libbar.dylib",
        built_native(dylib_id="/opt/build/lib/libbar.dylib"),
        "dylib name '/opt/build/lib/libbar.dylib' is not @rpath/<basename>",
    ),
}


@pytest.mark.parametrize("case", sorted(LOCATION_FAULTS))
def test_macho_rpath_and_names_must_fit_the_location(tmp_path, monkeypatch, case):
    """One LC_RPATH of @loader_path plus one /.. per folder below the contents root."""
    relative, built, message = LOCATION_FAULTS[case]
    found = macos_origin_check(
        tmp_path,
        monkeypatch,
        "darwin",
        original_native(),
        built,
        relative=relative,
        name="libbar.dylib",
    )
    assert len(found) == 1 and found[0].startswith(f"native origin: {relative}: ")
    assert message in found[0]


def test_macho_without_rpath_dependency_may_carry_no_rpath(tmp_path, monkeypatch):
    """PyInstaller adds the rpath only when a dependency uses @rpath (utils/osx.py:574)."""
    original = original_native(names=(ORIGINAL_NAMES[1],), rpaths=("/opt/x",))
    for rpaths in ((), ("@loader_path/..",)):
        built = built_native(1, names=(BUILT_NAMES[1],), rpaths=rpaths)
        found = macos_origin_check(
            tmp_path / str(len(rpaths)),
            monkeypatch,
            "darwin",
            original,
            built,
            relative="_internal/pkg/libbar.dylib",
            name="libbar.dylib",
        )
        assert found == []


def test_macho_outside_the_contents_root_needs_the_whole_file(tmp_path, monkeypatch):
    """Beside the executable only exact copies are admitted (no transformed identity)."""
    found = macos_origin_check(
        tmp_path,
        monkeypatch,
        "darwin",
        original_native(),
        built_native(),
        relative="libbar.dylib",
        name="libbar.dylib",
    )
    assert found == ["native origin unknown: libbar.dylib"]


BOOT_CODE = bytes.fromhex("fd7bbfa9") * 32
BOOT_LINKEDIT = b"bootloader symbols\0strings\0"
PKG = b"MEI\x0c\x0b\x0a\x0b\x0e" + b"appended PKG archive" * 8


def locked_runw() -> bytes:
    """PyInstaller's universal2 ``runw`` as shipped: both slices linker-signed."""
    x86 = macho(cpu=CPU_X86_64, filetype=MH_EXECUTE, code=X86_CODE, signature=b"x" * 16)
    arm = macho(
        filetype=MH_EXECUTE,
        code=BOOT_CODE,
        linkedit=BOOT_LINKEDIT,
        names=("/usr/lib/libSystem.B.dylib",),
        signature=b"L" * 32,
    )
    return fat((CPU_X86_64, x86), (CPU_ARM64, arm))


def built_bootloader(**changes: Any) -> bytes:
    """``runw`` thinned, unsigned, re-identified, SDK set, PKG appended, re-signed."""
    linkedit = BOOT_LINKEDIT + PKG
    fields: dict[str, Any] = {
        "filetype": MH_EXECUTE,
        "code": BOOT_CODE,
        "linkedit": linkedit,
        "names": ("/usr/lib/libSystem.B.dylib",),
        "signature": b"A" * 64,
        "uuid": b"\x22" * 16,
        "sdk": 0x000F0200,
        "strsize": len(linkedit),
    }
    return macho(**{**fields, **changes})


BOOTLOADER_CASES = {
    "pyinstaller-transformations": (built_bootloader(), True),
    "changed-code-byte": (built_bootloader(code=BOOT_CODE[:-1] + b"\x00"), False),
    "added-dependency": (
        built_bootloader(names=("/usr/lib/libSystem.B.dylib", "@rpath/x.dylib")),
        False,
    ),
    "changed-linkedit-prefix": (
        built_bootloader(linkedit=b"Bootloader" + BOOT_LINKEDIT[10:] + PKG),
        False,
    ),
    "added-rpath": (built_bootloader(rpaths=("@loader_path",)), False),
    "x86_64-slice": (
        macho(cpu=CPU_X86_64, filetype=MH_EXECUTE, code=X86_CODE, signature=b"A" * 64),
        False,
    ),
    "still-fat": (fat((CPU_ARM64, built_bootloader())), False),
    # A r1 #2: every original string-table byte, its final terminator included, must stay.
    "changed-final-string-terminator": (
        built_bootloader(linkedit=BOOT_LINKEDIT[:-1] + b"X" + PKG),
        False,
    ),
    # A r1 #3: nothing may follow the re-signed image's segments.
    "appended-trailer": (built_bootloader() + b"after the signature", False),
}


@pytest.mark.parametrize("case", sorted(BOOTLOADER_CASES))
def test_macos_bootloader_identity(tmp_path, monkeypatch, case):
    """The allowed bootloader differences pass on darwin; the old prefix rule refused even those."""
    built, admitted = BOOTLOADER_CASES[case]
    source = tmp_path / "runw"
    source.write_bytes(locked_runw())
    executable = tmp_path / "Clearwater"
    executable.write_bytes(built)
    monkeypatch.setattr(build, "_locked_bootloader", lambda: source)
    monkeypatch.setattr(build.sys, "platform", "darwin")
    assert build._is_clearwater_bootloader(executable) is admitted
    monkeypatch.setattr(build.sys, "platform", "linux")
    assert build._is_clearwater_bootloader(executable) is False


PADDING = b"\0" * 8


@pytest.mark.parametrize(
    "gap, built_linkedit, admitted",
    [
        # Proven alignment padding (< 16 zero bytes after the string table) may be dropped
        # with the signature or kept: both admitted.
        (PADDING, BOOT_LINKEDIT + PKG, True),
        (PADDING, BOOT_LINKEDIT + PADDING + PKG, True),
        # 16 zero bytes are not alignment padding: they must stay.
        (b"\0" * 16, BOOT_LINKEDIT + PKG, False),
        (b"\0" * 16, BOOT_LINKEDIT + b"\0" * 16 + PKG, True),
        # Non-zero bytes after the string table are never padding.
        (b"junk\0\0\0\0", BOOT_LINKEDIT + PKG, False),
        (b"junk\0\0\0\0", BOOT_LINKEDIT + b"junk\0\0\0\0" + PKG, True),
        # The boundary itself: the final string-table terminator changed.
        (PADDING, BOOT_LINKEDIT[:-1] + b"X" + PKG, False),
    ],
    ids=[
        "padding-dropped",
        "padding-kept",
        "sixteen-zeros-dropped",
        "sixteen-zeros-kept",
        "junk-dropped",
        "junk-kept",
        "terminator-changed",
    ],
)
def test_bootloader_linkedit_excludes_only_proven_alignment_padding(
    tmp_path, monkeypatch, gap, built_linkedit, admitted
):
    """A r1 #2: only < 16 zero bytes between the string table's end and the signature."""
    arm = macho(
        filetype=MH_EXECUTE,
        code=BOOT_CODE,
        linkedit=BOOT_LINKEDIT + gap,
        strsize=len(BOOT_LINKEDIT),
        names=("/usr/lib/libSystem.B.dylib",),
        signature=b"L" * 32,
    )
    source = tmp_path / "runw"
    source.write_bytes(arm)
    executable = tmp_path / "Clearwater"
    executable.write_bytes(built_bootloader(linkedit=built_linkedit))
    monkeypatch.setattr(build, "_locked_bootloader", lambda: source)
    monkeypatch.setattr(build.sys, "platform", "darwin")
    assert build._is_clearwater_bootloader(executable) is admitted


@pytest.mark.parametrize("kept", [False, True])
def test_native_linkedit_alignment_padding_may_go_with_the_signature(tmp_path, monkeypatch, kept):
    """A r1 #2 for ordinary natives: proven padding only; the strings stay exact."""
    original = original_native(linkedit=b"symbols\0strings\0" + PADDING, strsize=16)
    built = built_native(linkedit=b"symbols\0strings\0" + (PADDING if kept else b""), strsize=16)
    found = macos_origin_check(
        tmp_path,
        monkeypatch,
        "darwin",
        original,
        built,
        relative="_internal/libbar.dylib",
        name="libbar.dylib",
    )
    assert found == []


# --- macOS framework links (WP6.5, F0-9) -------------------------------------------------
# PyInstaller's collect_files_from_framework_bundles (utils/osx.py:671-692) makes, in every
# collected .framework: Versions/Current -> <version>, <fw>/<name> -> Versions/Current/<name>,
# <fw>/Resources (and Helpers, Headers, ...) -> Versions/Current/<dir>.

FRAMEWORK = "_internal/PySide6/Qt/lib/QtCore.framework"
APP_FRAMEWORK = "Clearwater.app/Contents/Frameworks/PySide6/Qt/lib/QtCore.framework"

ADMITTED_LINKS = [
    (f"{FRAMEWORK}/Versions/Current", "A"),
    (f"{FRAMEWORK}/Versions/Current", "5"),
    (f"{FRAMEWORK}/QtCore", "Versions/Current/QtCore"),
    (f"{FRAMEWORK}/Resources", "Versions/Current/Resources"),
    (f"{FRAMEWORK}/Helpers", "Versions/Current/Helpers"),
    (f"{APP_FRAMEWORK}/Versions/Current", "A"),
    (f"{APP_FRAMEWORK}/QtCore", "Versions/Current/QtCore"),
    (
        "_internal/Outer.framework/Versions/A/Frameworks/Inner.framework/Inner",
        "Versions/Current/Inner",
    ),
]

REFUSED_LINKS = [
    (f"{FRAMEWORK}/QtCore", "/usr/lib/libz.dylib", "absolute or not POSIX"),
    (f"{FRAMEWORK}/QtCore", "C:/Windows/x.dll", "absolute or not POSIX"),
    (f"{FRAMEWORK}/QtCore", "..\\..\\x", "absolute or not POSIX"),
    (f"{FRAMEWORK}/QtCore", "", "absolute or not POSIX"),
    ("_internal/libQt6Core.dylib", "PySide6/Qt/lib/libQt6Core.dylib", "outside a .framework"),
    ("_internal/PySide6/Qt/lib/QtCore.framework", "../../QtCore.framework", "outside a .framework"),
    ("Clearwater.app/Contents/Resources/base_library.zip", "../Frameworks/x", "outside"),
    (f"{FRAMEWORK}/Versions/Current", "A/../../..", "not a sibling version folder"),
    (f"{FRAMEWORK}/Versions/Current", "Current", "not a sibling version folder"),
    (f"{FRAMEWORK}/Versions/Current", "..", "not a sibling version folder"),
    (f"{FRAMEWORK}/QtCore", "Versions/A/QtCore", "not a framework structure link"),
    (f"{FRAMEWORK}/QtCore", "Versions/Current/QtGui", "not a framework structure link"),
    (f"{FRAMEWORK}/QtCore", "../../../../../../etc/passwd", "not a framework structure link"),
    (f"{FRAMEWORK}/Versions/A/Resources/x", "y", "not a framework structure link"),
    (f"{FRAMEWORK}/Versions/A", "../../QtGui.framework/Versions/A", "not a framework"),
]


@pytest.mark.parametrize("link, target", ADMITTED_LINKS)
def test_framework_link_rule_admits_pyinstaller_framework_links(link, target):
    """Pure rule over path strings (runs everywhere): the shapes PyInstaller makes."""
    assert build.framework_link_problem(PurePosixPath(link), target) is None


@pytest.mark.parametrize("link, target, reason", REFUSED_LINKS)
def test_framework_link_rule_refuses_every_other_link(link, target, reason):
    """Absolute, escaping, outside a framework or another shape: refused with the reason."""
    problem = build.framework_link_problem(PurePosixPath(link), target)
    assert problem is not None and reason in problem


def _symlink(path: Path, target: str, *, folder: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(target, path, target_is_directory=folder)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"os.symlink unavailable here (needs the symlink privilege): {error}")


def macos_framework_release(home: Path, framework: str = FRAMEWORK) -> list[Path]:
    """A collected QtCore.framework with PyInstaller's three links under ``home``."""
    root = home / framework
    tree(root, ["Versions/A/QtCore"], built_native(6, dylib_id="@rpath/QtCore"))
    tree(root, ["Versions/A/Resources/Info.plist"], b"<plist/>")
    links = [root / "Versions/Current", root / "QtCore", root / "Resources"]
    _symlink(links[0], "A", folder=True)
    _symlink(links[1], "Versions/Current/QtCore", folder=False)
    _symlink(links[2], "Versions/Current/Resources", folder=True)
    return links


def framework_origin_check(tmp_path, monkeypatch, platform, *, extra=None):
    original = original_native(dylib_id="/opt/qt/lib/QtCore.framework/Versions/A/QtCore")
    base = tree(tmp_path / "python", ["lib/QtCore"], original)
    monkeypatch.setattr(build.sys, "base_prefix", str(base))
    monkeypatch.setattr(build, "_locked_native_distributions", lambda: [])
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True)
    monkeypatch.setattr(build, "read_package", lambda _: SimpleNamespace(toc={}))
    home = tree(tmp_path / "dist" / "Clearwater", ["Clearwater"], b"bootloader stand-in")
    links = macos_framework_release(home)
    if extra is not None:
        extra(home)
    monkeypatch.setattr(build.sys, "platform", platform)
    return links, build.native_origin_violations(home / "Clearwater", original_path="")


def test_origin_walk_admits_framework_links_on_macos_only(tmp_path, monkeypatch):
    """darwin: the three links pass and the binary behind them is admitted; win32 unchanged.

    Under win32 (today's rule) every link is refused and the transformed binary is unknown.
    """
    _, found = framework_origin_check(tmp_path / "mac", monkeypatch, "darwin")
    assert found == []
    links, found = framework_origin_check(tmp_path / "win", monkeypatch, "win32")
    assert sorted(found) == sorted(
        [
            *(f"native origin: linked file {link}" for link in links),
            f"native origin unknown: {FRAMEWORK}/Versions/A/QtCore",
        ]
    )


@pytest.mark.parametrize(
    "link, target, folder, reason",
    [
        # A (B)-shaped top-level link whose target does not exist.
        ("_internal/libQt6Core.dylib", "PySide6/Qt/lib/libQt6Core.dylib", False, "dangling"),
        (f"{FRAMEWORK}/Headers", "/usr/include", True, "absolute"),
        (f"{FRAMEWORK}/Helpers", "Versions/Current/Helpers", True, "dangling link"),
        (f"{FRAMEWORK}/Versions/B", "../../../../../../../..", True, "outside the release"),
    ],
)
def test_origin_walk_refuses_other_links_on_macos(
    tmp_path, monkeypatch, link, target, folder, reason
):
    """Each refused link is named with its reason; the admitted ones beside it stay quiet."""
    _, found = framework_origin_check(
        tmp_path,
        monkeypatch,
        "darwin",
        extra=lambda home: _symlink(home / link, target, folder=folder),
    )
    assert len(found) == 1
    assert found[0].startswith(f"native origin: linked file {home_of(tmp_path) / link}: ")
    assert reason in found[0]


def home_of(tmp_path: Path) -> Path:
    return tmp_path / "dist" / "Clearwater"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows junction regression")
def test_origin_walk_refuses_a_junction_on_the_macos_path(tmp_path, monkeypatch):
    """A junction is never a framework link."""
    import _winapi

    outside = tree(tmp_path / "outside", ["secret.dylib"])

    def junction(home: Path) -> None:
        _winapi.CreateJunction(str(outside), str(home / FRAMEWORK / "Headers"))

    _, found = framework_origin_check(tmp_path, monkeypatch, "darwin", extra=junction)
    headers = home_of(tmp_path) / FRAMEWORK / "Headers"
    assert found == [f"native origin: linked file {headers}: junction"]


def test_release_zip_stores_framework_links_as_links_on_macos(tmp_path, monkeypatch):
    """S_IFLNK members carry the link text; files keep 0644; two writes are byte-identical."""
    root = tmp_path / "Clearwater-1.2.0-macos-onedir"
    tree(root, ["Clearwater/Clearwater"], b"bootloader")
    macos_framework_release(root / "Clearwater")
    monkeypatch.setattr(build.sys, "platform", "darwin")
    archives = []
    for run in ("a", "b"):
        archive = build.write_release_zip(root, out=tmp_path / run, source_epoch=1793908801)
        archives.append(archive.read_bytes())
    assert archives[0] == archives[1]
    prefix = f"{root.name}/Clearwater/{FRAMEWORK}"
    with zipfile.ZipFile(io.BytesIO(archives[0])) as packed:
        infos = {info.filename: info for info in packed.infolist()}
        expected_links = {
            f"{prefix}/Versions/Current": b"A",
            f"{prefix}/QtCore": b"Versions/Current/QtCore",
            f"{prefix}/Resources": b"Versions/Current/Resources",
        }
        for name, text in expected_links.items():
            info = infos[name]
            assert stat.S_ISLNK(info.external_attr >> 16)
            assert info.external_attr >> 16 == stat.S_IFLNK | 0o755
            assert info.compress_type == zipfile.ZIP_STORED
            assert packed.read(info) == text
        files = sorted(set(infos) - set(expected_links))
        assert files == sorted(
            [
                f"{root.name}/Clearwater/Clearwater",
                f"{prefix}/Versions/A/QtCore",
                f"{prefix}/Versions/A/Resources/Info.plist",
            ]
        )
        for name in files:
            assert infos[name].external_attr >> 16 == stat.S_IFREG | 0o644


def test_release_zip_link_rule_is_unchanged_on_windows(tmp_path, monkeypatch):
    """win32: the same framework links are refused with today's text."""
    root = tmp_path / "Clearwater-1.2.0-windows-onedir"
    tree(root, ["Clearwater/Clearwater.exe"], b"bootloader")
    macos_framework_release(root / "Clearwater")
    monkeypatch.setattr(build.sys, "platform", "win32")
    with pytest.raises(ValueError, match="release ZIP refuses linked/junction/outside member: "):
        build.write_release_zip(root, out=tmp_path / "out", source_epoch=1793908801)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize(
    "link, target, folder",
    [
        ("Clearwater/_internal/libQt6Core.dylib", "PySide6/libQt6Core.dylib", False),
        (f"Clearwater/{FRAMEWORK}/Headers", "../../../../../../../outside", True),
    ],
)
def test_release_zip_refuses_other_links_on_macos(tmp_path, monkeypatch, link, target, folder):
    """Outside a framework or escaping: refused before any ZIP byte is written."""
    root = tmp_path / "Clearwater-1.2.0-macos-onedir"
    tree(root, ["Clearwater/Clearwater"], b"bootloader")
    tree(tmp_path, ["outside/secret.txt"])
    macos_framework_release(root / "Clearwater")
    _symlink(root / link, target, folder=folder)
    monkeypatch.setattr(build.sys, "platform", "darwin")
    with pytest.raises(ValueError, match="release ZIP refuses linked/junction/outside member: "):
        build.write_release_zip(root, out=tmp_path / "out", source_epoch=1793908801)
    assert not (tmp_path / "out").exists()


def test_release_snapshot_records_links_by_their_text(tmp_path, monkeypatch):
    """A retargeted framework link after the snapshot is a change, as a changed file is."""
    root = tmp_path / "release"
    tree(root, ["Clearwater/Clearwater"], b"bootloader")
    links = macos_framework_release(root / "Clearwater")
    tree(links[0].parent, ["B/QtCore", "B/Resources/Info.plist"], b"other")
    monkeypatch.setattr(build.sys, "platform", "darwin")
    before = build._release_snapshot(root)
    assert before[links[0].relative_to(root).as_posix()] == ("link:A", 0)
    links[0].unlink()
    _symlink(links[0], "B", folder=True)
    with pytest.raises(ValueError, match=r"changed after pre-smoke snapshot: .*Versions/Current"):
        build._check_release_snapshot(root, before)


# --- WP6.5 G1-F1 as ruled: link classes (B) and (C), ONE shared predicate -----------------
# (B) PyInstaller's bindepend top-level link (depend/bindepend.py:196-210): in the contents
# root, named as its target's basename, resolving there to a regular file. (C) BUNDLE's
# cross-links between Contents/Frameworks, Resources and MacOS (building/osx.py:400-425,
# :456-461, :537-547). ONE HOP: a link naming a link is refused. The same case table runs
# through every caller: the origin walk, the release ZIP and (onedir) the artifact notices.

LINK_BLOB = b"\xcf\xfa\xed\xfe trusted here by its whole-file hash"
QT_BINARY = "PySide6/Qt/lib/QtCore.framework/Versions/A/QtCore"
NOT_ADMITTED = "not a top-level dependency link or a bundle cross-link"

LINK_CASES: dict[str, tuple[str, list[str], list[tuple[str, str, bool]], str | None]] = {
    # name: (layout, files, links (path, target, folder), refusal reason or None)
    "B-top-level-dependency": (
        "onedir",
        [f"_internal/{QT_BINARY}"],
        [("_internal/QtCore", QT_BINARY, False)],
        None,
    ),
    "B-app-through-a-dotted-folder-link": (
        "app",
        ["Contents/Frameworks/scipy/__dot__dylibs/libgfortran.5.dylib"],
        [
            ("Contents/Frameworks/scipy/.dylibs", "__dot__dylibs", True),
            ("Contents/Frameworks/libgfortran.5.dylib", "scipy/.dylibs/libgfortran.5.dylib", False),
            ("Contents/Resources/scipy", "../Frameworks/scipy", True),
            ("Contents/Resources/libgfortran.5.dylib", "scipy/.dylibs/libgfortran.5.dylib", False),
        ],
        None,
    ),
    "C-data-file-cross-link": (
        "app",
        ["Contents/Resources/data.txt"],
        [("Contents/Frameworks/data.txt", "../Resources/data.txt", False)],
        None,
    ),
    "C-binary-folder-cross-link": (
        "app",
        [f"Contents/Frameworks/{QT_BINARY}", "Contents/Frameworks/PySide6/Qt/lib/libx.dylib"],
        [
            ("Contents/Resources/PySide6/Qt/lib", "../../../Frameworks/PySide6/Qt/lib", True),
            ("Contents/Frameworks/QtCore", QT_BINARY, False),
            ("Contents/Resources/QtCore", QT_BINARY, False),
        ],
        None,
    ),
    "B-name-is-not-the-target-basename": (
        "onedir",
        [f"_internal/{QT_BINARY}"],
        [("_internal/QtGui", QT_BINARY, False)],
        NOT_ADMITTED,
    ),
    "B-not-directly-in-the-contents-root": (
        "onedir",
        ["_internal/pkg/libbar.dylib"],
        [("_internal/sub/libbar.dylib", "../pkg/libbar.dylib", False)],
        NOT_ADMITTED,
    ),
    "B-target-is-a-folder": (
        "onedir",
        ["_internal/pkg/sub/libbar.dylib"],
        [("_internal/sub", "pkg/sub", True)],
        NOT_ADMITTED,
    ),
    "B-target-outside-the-contents-root": (
        "onedir",
        [],
        [("_internal/Clearwater", "../Clearwater", False)],
        NOT_ADMITTED,
    ),
    "planted-escaping-link": (
        "onedir",
        [],
        [("_internal/libx.dylib", "../../../outside/libx.dylib", False)],
        "link resolves outside the release folder",
    ),
    "planted-link-to-a-link": (
        "onedir",
        [f"_internal/{QT_BINARY}"],
        [
            ("_internal/PySide6/Qt/lib/QtCore.framework/Versions/Current", "A", True),
            (
                "_internal/PySide6/Qt/lib/QtCore.framework/QtCore",
                "Versions/Current/QtCore",
                False,
            ),
            ("_internal/QtCore", "PySide6/Qt/lib/QtCore.framework/QtCore", False),
        ],
        "link to a link (one hop only)",
    ),
    "C-app-link-to-a-link": (
        "app",
        ["Contents/Resources/data.txt"],
        [
            ("Contents/Frameworks/data.txt", "../Resources/data.txt", False),
            ("Contents/MacOS/data.txt", "../Frameworks/data.txt", False),
        ],
        "link to a link (one hop only)",
    ),
    "C-outside-the-three-folders": (
        "app",
        ["Contents/Resources/data.txt"],
        [("Contents/Info2.plist", "Resources/data.txt", False)],
        NOT_ADMITTED,
    ),
    "C-into-the-signature-folder": (
        "app",
        ["Contents/_CodeSignature/CodeResources"],
        [("Contents/Resources/CodeResources", "../_CodeSignature/CodeResources", False)],
        NOT_ADMITTED,
    ),
    "cross-link-shape-in-a-onedir": (
        "onedir",
        ["_internal/other/data.txt"],
        [("_internal/pkg/data.txt", "../other/data.txt", False)],
        NOT_ADMITTED,
    ),
}


def link_release(tmp_path: Path, layout: str, files, links) -> tuple[Path, Path]:
    """Build a release under ``tmp_path/wrapper``; return (the ZIP folder, the executable)."""
    wrapper = tmp_path / "wrapper"
    if layout == "app":
        home = wrapper / "Clearwater.app"
        executable = home / "Contents/MacOS/Clearwater"
        zip_folder = home
    else:
        home = wrapper / "Clearwater"
        executable = home / "Clearwater"
        zip_folder = wrapper
    tree(executable.parent, [executable.name], b"bootloader stand-in")
    tree(home, files, LINK_BLOB)
    tree(tmp_path, ["outside/libx.dylib"], LINK_BLOB)
    for path, target, folder in links:
        _symlink(home / path, target, folder=folder)
    return zip_folder, executable


def link_origin_check(tmp_path, monkeypatch, executable: Path) -> list[str]:
    """The real darwin origin walk; every planted file is trusted by its whole-file hash."""
    empty = tmp_path / "python"
    empty.mkdir(exist_ok=True)
    monkeypatch.setattr(build.sys, "base_prefix", str(empty))
    monkeypatch.setattr(build, "_locked_native_distributions", lambda: [])
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True)
    monkeypatch.setattr(build, "read_package", lambda _: SimpleNamespace(toc={}))
    monkeypatch.setattr(build.sys, "platform", "darwin")
    return build.native_origin_violations(
        executable, original_path="", ffmpeg_hashes={hashlib.sha256(LINK_BLOB).hexdigest()}
    )


def link_notices_inventory(monkeypatch, wrapper: Path, platform: str = "darwin") -> None:
    """The artifact notices' inventory over a onedir folder, the build tool's archive stubbed."""
    spec = importlib.util.spec_from_file_location(
        "wp65_notices_links", Path(build.__file__).with_name("notices.py")
    )
    assert spec is not None and spec.loader is not None
    notices = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(notices)
    monkeypatch.setattr(build, "read_package", lambda _: SimpleNamespace(toc={}))
    monkeypatch.setattr(notices, "_build_tool", lambda: build)
    monkeypatch.setattr(build.sys, "platform", platform)
    notices._inventory(wrapper)


@pytest.mark.parametrize("case", sorted(LINK_CASES))
def test_shared_link_rule_in_the_origin_walk(tmp_path, monkeypatch, case):
    """Admitted classes pass; each refused link is named once with its reason."""
    layout, files, links, reason = LINK_CASES[case]
    _, executable = link_release(tmp_path, layout, files, links)
    found = link_origin_check(tmp_path, monkeypatch, executable)
    if reason is None:
        assert found == []
    else:
        assert len(found) == 1, found
        assert found[0].startswith("native origin: linked file ") and reason in found[0]


@pytest.mark.parametrize("case", sorted(LINK_CASES))
def test_shared_link_rule_in_the_release_zip(tmp_path, monkeypatch, case):
    """The ZIP stores admitted links as links and refuses the rest before writing."""
    layout, files, links, reason = LINK_CASES[case]
    folder, _ = link_release(tmp_path, layout, files, links)
    monkeypatch.setattr(build.sys, "platform", "darwin")
    out = tmp_path / "out"
    if reason is None:
        archive = build.write_release_zip(folder, out=out, source_epoch=1793908801)
        with zipfile.ZipFile(archive) as packed:
            stored = {
                info.filename: packed.read(info)
                for info in packed.infolist()
                if stat.S_ISLNK(info.external_attr >> 16)
            }
        prefix = folder.name + "/" + ("" if layout == "app" else "Clearwater/")
        assert stored == {prefix + path: target.encode() for path, target, _ in links}
    else:
        with pytest.raises(
            ValueError, match="release ZIP refuses linked/junction/outside"
        ) as error:
            build.write_release_zip(folder, out=out, source_epoch=1793908801)
        assert reason in str(error.value)
        assert not out.exists()


@pytest.mark.parametrize(
    "case", sorted(name for name, row in LINK_CASES.items() if row[0] == "onedir")
)
def test_shared_link_rule_in_the_artifact_notices(tmp_path, monkeypatch, case):
    """G1-F2: the notices inventory uses the same rule (an admitted link carries no entry)."""
    _, files, links, reason = LINK_CASES[case]
    wrapper, _ = link_release(tmp_path, "onedir", files, links)
    if reason is None:
        link_notices_inventory(monkeypatch, wrapper)
    else:
        with pytest.raises(ValueError, match="notices: unsafe linked entry") as error:
            link_notices_inventory(monkeypatch, wrapper)
        assert reason in str(error.value)


def test_notices_still_refuse_every_link_on_windows(tmp_path, monkeypatch):
    """win32: a link the macOS rule admits is still refused with today's text."""
    _, files, links, _ = LINK_CASES["B-top-level-dependency"]
    wrapper, _ = link_release(tmp_path, "onedir", files, links)
    tree(wrapper / "Clearwater", ["Clearwater.exe"], b"bootloader stand-in")
    with pytest.raises(ValueError, match=r"^notices: unsafe linked entry QtCore$"):
        link_notices_inventory(monkeypatch, wrapper, "win32")


def test_folder_link_checks_nested_links_as_if_at_its_location(tmp_path, monkeypatch):
    """(C) a folder target is walked: a bad link inside it refuses the folder link too."""
    folder, executable = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/pkg/data.txt"],
        [
            ("Contents/Resources/pkg", "../Frameworks/pkg", True),
            ("Contents/Frameworks/pkg/evil", "../../../../outside", True),
        ],
    )
    problem = build.macos_link_problem(
        folder, folder / "Contents/Frameworks", folder / "Contents/Resources/pkg"
    )
    assert problem == "evil under the linked folder: link resolves outside the release folder"
    found = link_origin_check(tmp_path, monkeypatch, executable)
    assert len(found) == 2 and all("outside the release folder" in line for line in found)


def test_folder_link_files_are_checked_at_the_links_location(tmp_path, monkeypatch):
    """A transformed native seen through a cross-link must fit the mirrored location."""
    base = tree(tmp_path / "python", ["lib/libbar.dylib"], original_native())
    monkeypatch.setattr(build.sys, "base_prefix", str(base))
    monkeypatch.setattr(build, "_locked_native_distributions", lambda: [])
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True)
    monkeypatch.setattr(build, "read_package", lambda _: SimpleNamespace(toc={}))
    monkeypatch.setattr(build.sys, "platform", "darwin")
    app = tmp_path / "Clearwater.app"
    tree(app, ["Contents/MacOS/Clearwater"], b"bootloader stand-in")
    tree(app, ["Contents/Frameworks/pkg/libbar.dylib"], built_native(1))
    # Mirrored (PyInstaller's shape): the same relative path, so the same depth.
    _symlink(app / "Contents/Resources/pkg", "../Frameworks/pkg", folder=True)
    executable = app / "Contents/MacOS/Clearwater"
    assert build.native_origin_violations(executable, original_path="") == []
    # Not mirrored: seen one folder deeper, the rpath no longer fits.
    _symlink(app / "Contents/Resources/deeper/pkg", "../../Frameworks/pkg", folder=True)
    found = build.native_origin_violations(executable, original_path="")
    assert len(found) == 1
    assert found[0].startswith(
        "native origin: Contents/Resources/deeper/pkg/libbar.dylib: LC_RPATH"
    )


@pytest.mark.parametrize("denied", ["root", "nested"])
def test_unreadable_folder_fails_the_macos_walks(tmp_path, monkeypatch, denied):
    """A r1 #1: a folder that cannot be listed fails the origin check, the ZIP and notices."""
    folder, executable = link_release(
        tmp_path, "onedir", [f"_internal/{QT_BINARY}", "_internal/pkg/libbar.dylib"], []
    )
    home = executable.parent
    target = home if denied == "root" else home / "_internal/pkg"
    real_scandir = os.scandir

    def scandir(path: Any = ".") -> Any:
        if os.path.normcase(os.fspath(path)) == os.path.normcase(str(target)):
            raise PermissionError(13, "planted: permission denied", os.fspath(path))
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", scandir)
    with pytest.raises(PermissionError, match="planted"):
        link_origin_check(tmp_path, monkeypatch, executable)
    zip_root = folder if denied == "nested" else home
    with pytest.raises(PermissionError, match="planted"):
        build.write_release_zip(zip_root, out=tmp_path / "out", source_epoch=1793908801)
    assert not (tmp_path / "out").exists()
    with pytest.raises(PermissionError, match="planted"):
        link_notices_inventory(monkeypatch, folder)


# --- WP6.5 G1-F3 and the .app release shape ------------------------------------------------

MIXED_WINDOWS_PAYLOADS = {
    "Clearwater/Clearwater.exe": b"synthetic executable",
    "Clearwater/ffmpeg.exe": b"synthetic tool",
    "Clearwater/run.bat": b"@echo off\r\n",
    "Clearwater/_internal/native.dll": b"synthetic native",
    "Clearwater/_internal/Clearwater": b"no suffix",
    "Clearwater/THIRD_PARTY_NOTICES.md": b"synthetic notices\n",
}
# sha256 of the archive the base (8ca7aeaf, before the darwin exec-bit rule) writes for the
# payloads above on the laptop's pinned interpreter (deflate output is zlib's: pinned there).
WINDOWS_MIXED_ZIP_SHA256 = "0d3bfbfb13332df42f0180e90556ccf7d7d43602b8b2ea04c924df21788d6d10"


def test_windows_release_zip_bytes_unchanged_by_the_darwin_exec_rule(tmp_path, monkeypatch):
    """G1-F3: every Windows member stays 0644 whatever its mode; the bytes are the base's."""
    monkeypatch.setattr(build.sys, "platform", "win32")
    root = tmp_path / "Clearwater-1.1.0-windows-onedir"
    for name, payload in MIXED_WINDOWS_PAYLOADS.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        path.chmod(0o755 if name.endswith((".exe", ".bat", "/Clearwater")) else 0o644)
    assert any(p.stat().st_mode & 0o111 for p in root.rglob("*") if p.is_file())
    archive = build.write_release_zip(root, out=tmp_path, source_epoch=1793908801)
    with zipfile.ZipFile(archive) as packed:
        assert {info.external_attr for info in packed.infolist()} == {(stat.S_IFREG | 0o644) << 16}
    if sys.platform == "win32":
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == WINDOWS_MIXED_ZIP_SHA256


def test_macos_release_zip_keeps_execute_bits_from_the_file_mode(tmp_path, monkeypatch):
    """G1-F3: on darwin a member with an execute bit is 0755, every other file 0644."""
    app = tmp_path / "Clearwater.app"
    executables = [
        "Contents/MacOS/Clearwater",
        "Contents/MacOS/ffmpeg",
        "Contents/MacOS/helper.exe",  # executable by its suffix on a Windows host too
        "Contents/Frameworks/libx.dylib",
    ]
    tree(app, [*executables, "Contents/Resources/notes.txt"], b"payload")
    for name in executables:
        (app / name).chmod(0o755)
    (app / "Contents/Resources/notes.txt").chmod(0o644)
    expected = {
        f"Clearwater.app/{path.relative_to(app).as_posix()}": (
            0o755 if path.stat().st_mode & 0o111 else 0o644
        )
        for path in app.rglob("*")
        if path.is_file()
    }
    assert expected["Clearwater.app/Contents/MacOS/helper.exe"] == 0o755
    assert expected["Clearwater.app/Contents/Resources/notes.txt"] == 0o644
    if sys.platform == "darwin":
        assert sorted(k for k, v in expected.items() if v == 0o755) == sorted(
            f"Clearwater.app/{name}" for name in executables
        )
    monkeypatch.setattr(build.sys, "platform", "darwin")
    archive = build.write_release_zip(
        app, out=tmp_path / "out", source_epoch=1793908801, name="Clearwater-1.2.0-macos"
    )
    assert archive.name == "Clearwater-1.2.0-macos.zip"
    assert archive.with_suffix(".zip.sha256").read_text().endswith("  Clearwater-1.2.0-macos.zip\n")
    with zipfile.ZipFile(archive) as packed:
        modes = {info.filename: info.external_attr >> 16 for info in packed.infolist()}
    assert {name.split("/", 1)[0] for name in modes} == {"Clearwater.app"}
    assert modes == {name: stat.S_IFREG | mode for name, mode in expected.items()}


@pytest.mark.parametrize(
    "platform, stem, folder",
    [
        ("win32", "Clearwater-1.2.0-windows-onedir", "."),
        ("darwin", "Clearwater-1.2.0-macos", "Clearwater.app"),
    ],
)
def test_release_zip_name_and_folder_per_platform(tmp_path, monkeypatch, platform, stem, folder):
    """Windows unchanged; macOS packs the .app as Clearwater-<version>-macos.zip."""
    assert build.release_zip_name("onedir", "1.2.0", platform) == stem
    monkeypatch.setattr(build.sys, "platform", platform)
    assert build.release_zip_name("onedir", "1.2.0") == stem
    assert build.release_zip_folder(tmp_path) == tmp_path / folder


def test_find_executable_prefers_the_app_bundle_on_macos(tmp_path, monkeypatch):
    """PyInstaller leaves the onedir COLLECT beside the BUNDLE; the release is the .app."""
    tree(tmp_path, ["Clearwater/Clearwater", "Clearwater.app/Contents/MacOS/Clearwater"])
    monkeypatch.setattr(build.sys, "platform", "darwin")
    assert build.find_executable(tmp_path) == tmp_path / "Clearwater.app/Contents/MacOS/Clearwater"
    monkeypatch.setattr(build.sys, "platform", "win32")
    with pytest.raises(FileNotFoundError, match=r"no Clearwater.exe under"):
        build.find_executable(tmp_path)


def test_place_macos_tools_puts_code_in_macos_and_texts_in_resources(tmp_path):
    """The hook: verified bytes copied unchanged, code beside the bootloader, texts apart."""
    app = tree(tmp_path / "Clearwater.app", ["Contents/MacOS/Clearwater"])
    sources = tree(tmp_path / "verified", ["ffmpeg", "ffprobe", "LICENSE.txt"], b"bytes")
    written = build.place_macos_tools(
        app,
        {"ffmpeg": sources / "ffmpeg", "ffprobe": sources / "ffprobe"},
        {"ffmpeg-LICENSE.txt": sources / "LICENSE.txt"},
    )
    assert written == [
        app / "Contents/MacOS/ffmpeg",
        app / "Contents/MacOS/ffprobe",
        app / "Contents/Resources/ffmpeg-LICENSE.txt",
    ]
    assert all(path.read_bytes() == b"bytes" for path in written)
    if sys.platform != "win32":
        assert [path.stat().st_mode & 0o777 for path in written] == [0o755, 0o755, 0o644]


@pytest.mark.parametrize(
    "bundle, executables, message",
    [
        ("Clearwater", {"ffmpeg": "ffmpeg"}, "needs a built .app bundle"),
        ("Clearwater.app", {"../ffmpeg": "ffmpeg"}, "is not a plain file name"),
        ("Clearwater.app", {"a\\b": "ffmpeg"}, "is not a plain file name"),
        ("Clearwater.app", {"Clearwater": "ffmpeg"}, "already exists"),
    ],
)
def test_place_macos_tools_refuses_unsafe_placement(tmp_path, bundle, executables, message):
    app = tree(tmp_path / bundle, ["Contents/MacOS/Clearwater"])
    source = tree(tmp_path / "verified", ["ffmpeg"])
    with pytest.raises(ValueError, match=re.escape(message)):
        build.place_macos_tools(app, {k: source / v for k, v in executables.items()})


def test_seal_macos_bundle_re_signs_without_deep_then_verifies(tmp_path):
    """Ad-hoc re-sign (nested code keeps its bytes), then a strict deep verify."""
    app = tree(tmp_path / "Clearwater.app", ["Contents/MacOS/Clearwater"])
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "", "")

    build.seal_macos_bundle(app, run=run)
    assert [command for command, _ in calls] == [
        ["/usr/bin/codesign", "--sign", "-", "--force", "--timestamp=none", str(app)],
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", "--verbose=2", str(app)],
    ]
    assert all(
        kwargs
        == {
            "stdin": subprocess.DEVNULL,
            "capture_output": True,
            "text": True,
            "timeout": 300,
            "check": False,
        }
        for _, kwargs in calls
    )
    assert "--deep" not in calls[0][0]


@pytest.mark.parametrize("failure", ["sign-status", "verify-status", "timeout", "os-error"])
def test_seal_macos_bundle_failures_are_named(tmp_path, failure):
    app = tree(tmp_path / "Clearwater.app", ["Contents/MacOS/Clearwater"])

    def run(command, **kwargs):
        step = "sign" if "--sign" in command else "verify"
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 300)
        if failure == "os-error":
            raise OSError("planted: codesign missing")
        if failure == f"{step}-status":
            return subprocess.CompletedProcess(
                command, 1, "", "first\na sealed resource is missing\n"
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    with pytest.raises(RuntimeError, match=r"^bundle seal: /usr/bin/codesign --(sign|verify)") as e:
        build.seal_macos_bundle(app, run=run)
    if failure.endswith("status"):
        assert str(e.value).endswith("exited 1: a sealed resource is missing")
    with pytest.raises(ValueError, match=r"needs a built .app bundle"):
        build.seal_macos_bundle(tmp_path, run=run)


def darwin_app_build(monkeypatch, tmp_path, *, seal, origin):
    """``build()`` on darwin with PyInstaller, the seal and the origin check stubbed."""
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr(build, "pack_sources", lambda: [])
    monkeypatch.setattr(build, "native_origin_violations", origin)
    monkeypatch.setattr(build, "seal_macos_bundle", seal)
    out = tmp_path / "out"
    # Built (and PyInstaller imported) BEFORE sys.platform reads darwin: PyInstaller's
    # compat module reads the macOS version at import time.
    source = make_exe(out / "synthetic", [], modules=["clearwater", "graphlib"])

    def build_folder(args):
        folder = Path(args[args.index("--distpath") + 1])
        for name in ("Clearwater/Clearwater", "Clearwater.app/Contents/MacOS/Clearwater"):
            (folder / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, folder / name)

    monkeypatch.setattr(build, "run_pyinstaller", build_folder)
    monkeypatch.setattr(build.sys, "platform", "darwin")
    return build.build("onedir", out=out), out


@pytest.mark.parametrize("outcome", ["sealed", "seal-fails", "origin-after-seal-fails"])
def test_darwin_build_seals_the_app_and_rechecks_origin(tmp_path, monkeypatch, capsys, outcome):
    """The .app is sealed after every placement and its origin checked again after."""
    events = []

    def seal(bundle):
        events.append(("seal", bundle.name))
        if outcome == "seal-fails":
            raise RuntimeError("bundle seal: /usr/bin/codesign --verify exited 1: planted")

    def origin(executable, **kwargs):
        events.append(("origin", executable.relative_to(executable.parents[2]).as_posix()))
        sealed = any(event[0] == "seal" for event in events)
        return ["planted after seal"] if sealed and outcome.startswith("origin") else []

    status, _ = darwin_app_build(monkeypatch, tmp_path, seal=seal, origin=origin)
    printed = capsys.readouterr().out
    assert events[:2] == [("origin", "Contents/MacOS/Clearwater"), ("seal", "Clearwater.app")]
    if outcome == "sealed":
        assert status == 0 and events[2:] == [("origin", "Contents/MacOS/Clearwater")]
        assert "bundle seal: PASS" in printed
    elif outcome == "seal-fails":
        assert status == 1 and len(events) == 2
        assert "FAILED: bundle seal: /usr/bin/codesign --verify exited 1: planted" in printed
    else:
        assert status == 1 and "FAILED: after seal: planted after seal" in printed


def test_darwin_build_scans_no_gpu_pack(tmp_path, monkeypatch, capsys):
    """AD-33: the CPU-only macOS environment has no pack distributions to scan."""

    def no_pack():
        raise importlib.metadata.PackageNotFoundError("cupy-cuda12x")

    def origin(executable, **kwargs):
        return []

    monkeypatch.setattr(build, "pack_sources", no_pack)
    monkeypatch.setattr(build, "seal_macos_bundle", lambda bundle: None, raising=False)
    monkeypatch.setattr(build, "native_origin_violations", origin)
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    out = tmp_path / "out"
    source = make_exe(out / "synthetic", [], modules=["clearwater", "graphlib"])

    def build_folder(args):
        folder = Path(args[args.index("--distpath") + 1])
        target = folder / "Clearwater.app/Contents/MacOS/Clearwater"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    monkeypatch.setattr(build, "run_pyinstaller", build_folder)
    monkeypatch.setattr(build.sys, "platform", "darwin")
    assert build.build("onedir", out=out) == 0
    assert " hidden imports from 0 pack files; " in capsys.readouterr().out
    monkeypatch.setattr(build.sys, "platform", "win32")
    assert build.build("onedir", out=out) == 1
    assert "FAILED: the pack sources cannot be scanned" in capsys.readouterr().out


def test_windows_build_never_seals(tmp_path, monkeypatch):
    """win32: no codesign step exists on the Windows path."""
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr(build, "pack_sources", lambda: [])
    monkeypatch.setattr(build, "native_origin_violations", lambda *a, **kw: [])
    monkeypatch.setattr(build, "seal_macos_bundle", lambda *a: pytest.fail("sealed on win32"))
    out = tmp_path / "out"

    def build_folder(args):
        folder = Path(args[args.index("--distpath") + 1])
        folder.mkdir(parents=True, exist_ok=True)
        source = make_exe(out / "synthetic", [], modules=["clearwater", "graphlib"])
        shutil.copyfile(source, folder / "Clearwater.exe")

    monkeypatch.setattr(build, "run_pyinstaller", build_folder)
    monkeypatch.setattr(build.sys, "platform", "win32")
    assert build.build("onedir", out=out) == 0


# --- WP6.5 group 2a part 2: the macOS FFmpeg lock and bundle_ffmpeg's darwin path ---------

MACOS_LOCK_FIXTURE = REPO_ROOT / "tests" / "ffmpeg_lock" / "ffmpeg-macos.fixture.json"
"""A SYNTHETIC macOS lock (census pending); the real lock is written from the fork run."""

MACOS_FORK_PATCH = REPO_ROOT / "tools" / "package" / "ffmpeg-fork-macos.patch"


def macos_lock() -> dict[str, Any]:
    return json.loads(MACOS_LOCK_FIXTURE.read_text(encoding="utf-8"))


def test_macos_lock_fixture_validates_with_the_platform_discriminator():
    data = macos_lock()
    assert build.validate_ffmpeg_lock(data, platform="darwin") is data
    assert set(data) == set(build.FFmpegMacLock.__annotations__)


def recipe_skips() -> set[str]:
    """The fork recipe's component switches: its ``-SKIP_<NAME>=YES`` less TEST / BUNDLE."""
    patch = MACOS_FORK_PATCH.read_text(encoding="utf-8")
    return set(re.findall(r"-(SKIP_[A-Z0-9_]+)=YES", patch)) - {"SKIP_TEST", "SKIP_BUNDLE"}


def test_macos_lock_excluded_rows_are_exactly_the_recipe_skips():
    """The VALIDATOR's required set (and the fixture's rows) is the recipe's component skips."""
    switches = recipe_skips()
    assert switches == build.FFMPEG_MACOS_EXCLUDED_STAGES
    assert {row["stage"] for row in macos_lock()["excluded"]} == switches
    assert len(switches) == 21


@pytest.mark.parametrize("stage", sorted(row["stage"] for row in macos_lock()["excluded"]))
def test_macos_lock_refuses_each_missing_recipe_skip(stage):
    """A3-F4: deleting any one of the 21 required exclusion rows is refused."""
    data = macos_lock()
    data["excluded"] = [row for row in data["excluded"] if row["stage"] != stage]
    with pytest.raises(ValueError, match=r"must be excluded|exactly the recipe's component skips"):
        build.validate_ffmpeg_lock(data, platform="darwin")


@pytest.mark.parametrize("rows", ["invented", "two-only", "two-only-plus-invented"])
def test_macos_lock_refuses_an_excluded_set_other_than_the_recipes(rows):
    """A3-F4 (the reviewer's probe): an invented row, or only zvbi + DeckLink, is refused."""
    data = macos_lock()
    invented = {"stage": "SKIP_DOES_NOT_EXIST", "status": "not-built(disabled)", "reason": "x"}
    if rows != "invented":
        data["excluded"] = data["excluded"][:2]
    if rows != "two-only":
        data["excluded"].append(invented)
    with pytest.raises(ValueError, match="exactly the recipe's component skips"):
        build.validate_ffmpeg_lock(data, platform="darwin")


def _configure(data: dict[str, Any], change: str) -> None:
    line = data["configure_line"]
    if change.startswith("---"):  # "---<flag>" removes <flag>; anything else is appended
        data["configure_line"] = line.replace(" " + change[1:], "")
    else:
        data["configure_line"] = line + " " + change


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        ("---enable-gpl", "GPL, version3 and libx265 are required"),
        ("---enable-version3", "GPL, version3 and libx265 are required"),
        ("---enable-libx265", "GPL, version3 and libx265 are required"),
        ("--enable-nonfree", "nonfree, libfdk, zvbi or decklink is forbidden"),
        ("--enable-libfdk-aac", "nonfree, libfdk, zvbi or decklink is forbidden"),
        ("--enable-libfdk_aac", "nonfree, libfdk, zvbi or decklink is forbidden"),
        ("--enable-libzvbi", "nonfree, libfdk, zvbi or decklink is forbidden"),
        ("--enable-decklink", "nonfree, libfdk, zvbi or decklink is forbidden"),
        ("--extra-version=20261111", "version date must match --extra-version"),
    ],
)
def test_macos_lock_configure_line_must_and_must_not(change, refusal):
    data = macos_lock()
    _configure(data, change)
    with pytest.raises(ValueError, match=re.escape(refusal)):
        build.validate_ffmpeg_lock(data, platform="darwin")


@pytest.mark.parametrize(
    "change",
    [
        "--disable-gpl",
        "--disable-version3",
        "--disable-libx265",
        "before:--disable-libx265",
        "before:--disable-gpl",
        "--disable-encoder=libx265",
        "--disable-encoder=aac,libx265",
        "--disable-encoder=libx26*",
        "--disable-encoder=aac|libx265",
        "--disable-encoders",
        "--disable-everything",
        "--disable-all",
        "--disable-avcodec",
        "--enable-random",
        "--disable-random",
        "--disable-random=encoders",
    ],
)
def test_macos_lock_refuses_a_required_switch_or_the_x265_encoder_disabled(change):
    """A3-F3: configure applies options left to right, the last enable / disable winning,
    so a disabling counterpart AFTER the enable defeats it; one anywhere is refused."""
    data = macos_lock()
    if change.startswith("before:"):
        flag = change.removeprefix("before:")
        data["configure_line"] = data["configure_line"].replace(
            "--extra-version=", f"{flag} --extra-version="
        )
    else:
        _configure(data, change)
    with pytest.raises(ValueError, match=r"disabled"):
        build.validate_ffmpeg_lock(data, platform="darwin")


@pytest.mark.parametrize("change", ["--disable-encoder=aac", "--disable-libx264", "--disable-doc"])
def test_macos_lock_admits_a_disable_that_leaves_the_required_set_on(change):
    """The rule is about the required switches and the libx265 encoder, not every disable."""
    data = macos_lock()
    _configure(data, change)
    assert build.validate_ffmpeg_lock(data, platform="darwin") is data


def test_macos_lock_configure_line_keeps_its_printed_prefix_and_one_date():
    data = macos_lock()
    data["configure_line"] = data["configure_line"].removeprefix("configuration: ")
    with pytest.raises(ValueError, match="printed prefix"):
        build.validate_ffmpeg_lock(data, platform="darwin")
    data = macos_lock()
    data["configure_line"] = data["configure_line"].replace(" --extra-version=20261110", "")
    with pytest.raises(ValueError, match="--extra-version"):
        build.validate_ffmpeg_lock(data, platform="darwin")


WINDOWS_ROOT = "ffmpeg-n9.0.2-47-gb204e94e90-win64-gpl-9.0"


def _windows_shaped(data: dict[str, Any], how: str) -> None:
    tag = data["release_tag"]
    if how == "url-only":
        data["asset_url"] = data["asset_url"].replace("macos-arm64", "win64")
    elif how == "asset":
        data["archive_root"] = WINDOWS_ROOT
        data["asset_name"] = WINDOWS_ROOT + ".zip"
        data["asset_url"] = data["asset_url"].rsplit("/", 1)[0] + "/" + data["asset_name"]
    elif how == "windows-lock-url":
        windows = json.loads((REPO_ROOT / "tools/package/ffmpeg.lock.json").read_text("utf-8"))
        data["asset_url"] = windows["asset_url"]
    elif how == "tag":
        data["release_tag"] = tag.replace("-macos-arm64", "")
        data["asset_url"] = data["asset_url"].replace(tag, data["release_tag"])


@pytest.mark.parametrize("how", ["url-only", "asset", "windows-lock-url", "tag"])
def test_macos_lock_refuses_a_windows_shaped_asset(how):
    data = macos_lock()
    _windows_shaped(data, how)
    with pytest.raises(ValueError, match=r"asset URL|archive_root|release tag"):
        build.validate_ffmpeg_lock(data, platform="darwin")


@pytest.mark.parametrize(
    ("field", "value", "refusal"),
    [
        ("schema_version", 3, "unsupported schema_version"),
        ("provider", "BtbN/FFmpeg-Builds", "provider must be the owner's fork"),
        ("size_bytes", 0, "invalid size_bytes"),
        ("seat_sha256", "1" * 64, "sha256 readings differ"),
        ("github_sha256", "A" * 64, "sha256 readings differ"),
        ("build_repository_commit", "deadbeef", "invalid build repository commit"),
        ("ffmpeg_commit", "b204e94e" + "0" * 32, "version hash differs"),
        ("ffmpeg_ref", "n9.0.2", "FFmpeg ref must be release/9.0"),
        ("ffmpeg_repository", "https://git.ffmpeg.org/ffmpeg.git", "FFmpeg repository"),
        ("version", "n8.0.1-47-gb204e94e90-20261110", "FFmpeg major must be 9"),
        ("licence", "GPL-2.0-or-later", "GPL-3.0-or-later"),
        (
            "extract_members",
            ["bin/ffmpeg.exe", "bin/ffprobe.exe", "LICENSE.txt"],
            "extract_members",
        ),
        ("source_record_url", "https://github.com/rwsmythe/FFmpeg-Builds", "source record URL"),
        ("build_run_url", "https://github.com/BtbN/FFmpeg-Builds/actions/runs/1", "build run URL"),
        (
            "build_run_url",
            "https://github.com/rwsmythe/FFmpeg-Builds/actions/runs/x",
            "build run URL",
        ),
        ("macos_deployment_target", "26.0", "deployment target must be 14.0"),
        ("runner_label", "macos-latest", "runner label must be macos-26"),
        ("runner_image_version", "latest", "invalid runner_image_version"),
        ("retention_note", "", "invalid retention_note"),
        ("census", "complete", "census rules are WP6.5 part 3's"),
        ("census", "partial", "census must be pending"),
        ("components", [{"stage": "build-x265.sh"}], "census pending: components"),
        ("toolchain_runtime", [{"name": "libc++"}], "census pending: components"),
        ("toolchain", {"clang": "21.0.0"}, "census pending: components"),
        ("build_script", {"repository": "https://example.invalid/x.git"}, "build_script fields"),
    ],
)
def test_macos_lock_refuses_inconsistent_provenance(field, value, refusal):
    data = macos_lock()
    data[field] = value
    with pytest.raises(ValueError, match=re.escape(refusal)):
        build.validate_ffmpeg_lock(data, platform="darwin")


@pytest.mark.parametrize(
    ("repository", "commit", "refusal"),
    [
        ("https://github.com/BtbN/FFmpeg-Builds.git", "f" * 40, "invalid build script repository"),
        (
            "https://git.martin-riedl.de/ffmpeg/build-script.git",
            "main",
            "invalid build script commit",
        ),
    ],
)
def test_macos_lock_pins_the_build_script(repository, commit, refusal):
    data = macos_lock()
    data["build_script"] = {"repository": repository, "commit": commit}
    with pytest.raises(ValueError, match=re.escape(refusal)):
        build.validate_ffmpeg_lock(data, platform="darwin")


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        ("no-zvbi", "SKIP_ZVBI and SKIP_DECKLINK must be excluded"),
        ("no-decklink", "SKIP_ZVBI and SKIP_DECKLINK must be excluded"),
        ("zvbi-built", "status must be not-built(disabled)"),
        ("bad-stage", "invalid excluded stage"),
        ("duplicate", "duplicate excluded stage"),
        ("extra-field", "invalid excluded stage fields"),
        ("empty-reason", "invalid excluded reason"),
    ],
)
def test_macos_lock_excluded_rows_fail_closed(change, refusal):
    data = macos_lock()
    rows = data["excluded"]
    if change == "no-zvbi":
        rows[:] = [row for row in rows if row["stage"] != "SKIP_ZVBI"]
    elif change == "no-decklink":
        rows[:] = [row for row in rows if row["stage"] != "SKIP_DECKLINK"]
    elif change == "zvbi-built":
        rows[0]["status"] = "built"
    elif change == "bad-stage":
        rows[0]["stage"] = "scripts.d/50-zvbi.sh"
    elif change == "duplicate":
        rows.append(dict(rows[0]))
    elif change == "extra-field":
        rows[0]["licence"] = "GPL-2.0-only"
    else:
        rows[0]["reason"] = ""
    with pytest.raises(ValueError, match=re.escape(refusal)):
        build.validate_ffmpeg_lock(data, platform="darwin")


@pytest.mark.parametrize("change", ["missing", "unknown"])
def test_macos_lock_field_set_is_exact(change):
    data = macos_lock()
    if change == "missing":
        del data["runner_image_version"]
    else:
        data["toolchain_census"] = "later"
    with pytest.raises(ValueError, match="invalid macOS document fields"):
        build.validate_ffmpeg_lock(data, platform="darwin")


def test_lock_platform_discriminator_refuses_the_other_platform():
    """A Windows lock is never a macOS lock and the reverse; Linux has no lock."""
    windows = json.loads((REPO_ROOT / "tools/package/ffmpeg.lock.json").read_text("utf-8"))
    with pytest.raises(ValueError, match="not a macOS lock"):
        build.validate_ffmpeg_lock(windows, platform="darwin")
    with pytest.raises(ValueError, match="is not the Windows lock"):
        build.validate_ffmpeg_lock(macos_lock())
    with pytest.raises(ValueError, match="is not the Windows lock"):
        build.validate_ffmpeg_lock(macos_lock(), platform="win32")
    with pytest.raises(ValueError, match="no FFmpeg lock for platform 'linux'"):
        build.validate_ffmpeg_lock(windows, platform="linux")
    assert build.validate_ffmpeg_lock(windows)["provider"] == "rwsmythe/FFmpeg-Builds"


def test_load_macos_lock_reads_its_own_file(tmp_path, monkeypatch):
    path = tmp_path / "ffmpeg-macos.lock.json"
    path.write_text(MACOS_LOCK_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(build, "FFMPEG_MACOS_LOCK_PATH", path)
    assert build.load_macos_ffmpeg_lock()["platform"] == "macos-arm64"
    assert build.FFMPEG_MACOS_LOCK_PATH.name == "ffmpeg-macos.lock.json"
    path.write_text((REPO_ROOT / "tools/package/ffmpeg.lock.json").read_text("utf-8"), "utf-8")
    with pytest.raises(ValueError, match="not a macOS lock"):
        build.load_macos_ffmpeg_lock()


LC_UUID, LC_BUILD_VERSION, LC_VERSION_MIN_MACOSX = 0x1B, 0x32, 0x24


def macos_version(major: int, minor: int = 0, patch: int = 0) -> int:
    """Mach-O's ``xxxx.yy.zz`` nibble form of a macOS version."""
    return major << 16 | minor << 8 | patch


def build_version(
    minos: int = macos_version(14), *, platform: int = 1, ntools: int = 1, tools: int | None = None
) -> bytes:
    """An LC_BUILD_VERSION command (platform 1 = macOS) carrying ``tools`` ld entries."""
    entries = b"".join(struct.pack("<II", 3, 0x04B00000) for _ in range(ntools))
    size = 24 + len(entries)
    count = ntools if tools is None else tools
    fields = (LC_BUILD_VERSION, size, platform, minos, macos_version(26), count)
    return struct.pack("<IIIIII", *fields) + entries


def uuid_command() -> bytes:
    return struct.pack("<II", LC_UUID, 24) + bytes(range(16))


def macho_image(
    commands: Sequence[bytes] | None = None,
    *,
    cpu: int = 0x0100000C,
    filetype: int = 2,
    magic: int = 0xFEEDFACF,
    ncmds: int | None = None,
    sizeofcmds: int | None = None,
) -> bytes:
    """A STRUCTURALLY VALID thin Mach-O header and load-command table (A3-F1's fixture)."""
    commands = [uuid_command(), build_version()] if commands is None else list(commands)
    table = b"".join(commands)
    count = len(commands) if ncmds is None else ncmds
    size = len(table) if sizeofcmds is None else sizeofcmds
    return struct.pack("<IiiIIIII", magic, cpu, 0, filetype, count, size, 0x00200085, 0) + table


def fake_macho(
    lock: dict[str, Any],
    *,
    cpu=0x0100000C,
    filetype=2,
    magic=0xFEEDFACF,
    extra=b"",
    commands: Sequence[bytes] | None = None,
    image: bytes | None = None,
):
    """A thin Mach-O head and load commands plus the two strings FFmpeg compiles in."""
    body = lock["configure_line"].removeprefix("configuration: ").encode()
    if image is None:
        image = macho_image(commands, cpu=cpu, filetype=filetype, magic=magic)
    strings = b"\0%s version %s\0\0" + lock["version"].encode() + b"\0" + body + b"\0"
    return image + b"\0" * 64 + extra + strings + b"\0" * 32


def test_macos_tool_check_parses_the_load_commands_and_binds_minos_to_the_lock():
    """A3-F1: the reviewer's two images; only minos 14.0 (the lock's target) is admitted."""
    for target, admitted in ((14, True), (26, False)):
        image = struct.pack("<IiiIIIII", 0xFEEDFACF, 0x0100000C, 0, 2, 1, 24, 0, 0)
        image += struct.pack("<IIIIII", 0x32, 24, 1, target << 16, 26 << 16, 0)
        problem = build._macos_tool_problem(image, "14.0")
        assert (problem is None) is admitted, problem
    assert build._macos_tool_problem(macho_image(), "14.0") is None
    problem = build._macos_tool_problem(macho_image()[:32], "14.0")
    assert problem is not None and "load-command table" in problem


@pytest.fixture
def macos_bundle(tmp_path, monkeypatch):
    """A synthetic fork zip, a verified-transport lock and a built .app (never executed)."""
    data = macos_lock()
    root = data["archive_root"]
    members = {
        f"{root}/bin/ffmpeg": fake_macho(data),
        f"{root}/bin/ffprobe": fake_macho(data),
        f"{root}/LICENSE.txt": b"synthetic GPL-3.0 text\n",
        f"{root}/build/toolchain.txt": b"Apple clang (synthetic)\n",
        f"{root}/build/logs/build-ffmpeg.log": b"log\n",
    }
    source = tmp_path / data["asset_name"]
    pin = tmp_path / "ffmpeg-macos.lock.json"
    app = tree(tmp_path / "dist" / "Clearwater.app", ["Contents/MacOS/Clearwater"])
    (app / "Contents" / "Frameworks").mkdir()
    out = tmp_path / "out"

    def write(extra=(), omit=(), infos=()):
        with zipfile.ZipFile(source, "w") as archive:
            for name, payload in members.items():
                if name not in omit:
                    info = zipfile.ZipInfo(name)
                    info.external_attr = (0o100755 if "/bin/" in name else 0o100644) << 16
                    archive.writestr(info, payload)
            for name, payload in extra:
                archive.writestr(name, payload)
            for info, payload in infos:
                archive.writestr(info, payload)
        data["size_bytes"] = source.stat().st_size
        data["github_sha256"] = data["seat_sha256"] = hashlib.sha256(
            source.read_bytes()
        ).hexdigest()
        data["asset_url"] = source.as_uri()
        pin.write_text(json.dumps(data), encoding="utf-8")

    real_run = build.subprocess.run

    def never_run(*args, **kwargs):
        pytest.fail("bundle_ffmpeg's darwin path ran a binary")

    monkeypatch.setattr(build, "FFMPEG_MACOS_LOCK_PATH", pin)
    monkeypatch.setattr(build, "_TEST_ALLOW_FILE_URLS", True)
    monkeypatch.setattr(build.subprocess, "run", never_run)
    monkeypatch.setattr(build.subprocess, "Popen", never_run)
    write()
    return SimpleNamespace(
        data=data,
        members=members,
        write=write,
        app=app,
        out=out,
        pin=pin,
        source=source,
        real_run=real_run,
    )


def bundle_macos(case, **kwargs):
    return build.bundle_ffmpeg(
        case.app / "Contents" / "MacOS",
        out=case.out,
        url=kwargs.pop("url", case.data["asset_url"]),
        sha256=kwargs.pop("sha256", case.data["github_sha256"]),
        platform="darwin",
        **kwargs,
    )


def test_macos_bundle_places_the_verified_tools_and_texts_and_runs_nothing(macos_bundle):
    case = macos_bundle
    trusted: set[str] = set()
    result = bundle_macos(case, verified_hashes=trusted)
    macos, resources = case.app / "Contents/MacOS", case.app / "Contents/Resources"
    assert [(path, line) for path, line in result] == [
        (macos / tool, f"{tool} version {case.data['version']} (read from the binary)")
        for tool in ("ffmpeg", "ffprobe")
    ]
    root = case.data["archive_root"]
    for tool in ("ffmpeg", "ffprobe"):
        assert (macos / tool).read_bytes() == case.members[f"{root}/bin/{tool}"]
    assert trusted == {hashlib.sha256(case.members[f"{root}/bin/ffmpeg"]).hexdigest()}
    assert sorted(p.name for p in macos.iterdir()) == ["Clearwater", "ffmpeg", "ffprobe"]
    assert sorted(p.name for p in resources.iterdir()) == ["ffmpeg-BUILD.txt", "ffmpeg-LICENSE.txt"]
    assert (resources / "ffmpeg-LICENSE.txt").read_bytes() == b"synthetic GPL-3.0 text\n"
    text = (resources / "ffmpeg-BUILD.txt").read_text(encoding="utf-8")
    for field in (
        "provider",
        "release_tag",
        "asset_name",
        "github_sha256",
        "version",
        "ffmpeg_commit",
        "ffmpeg_ref",
        "build_repository_commit",
        "build_run_url",
        "source_record_url",
        "configure_line",
        "macos_deployment_target",
        "runner_image_version",
    ):
        assert str(case.data[field]) in text, field
    assert case.data["build_script"]["commit"] in text
    assert "tools/package/ffmpeg-macos.lock.json" in text
    assert not any(p.name.startswith("build") for p in case.app.rglob("*") if p.is_dir())
    assert (case.out / "ffmpeg" / case.data["asset_name"]).is_file()
    if sys.platform != "win32":
        modes = {p.name: p.stat().st_mode & 0o777 for p in (*macos.iterdir(), *resources.iterdir())}
        assert modes["ffmpeg"] == modes["ffprobe"] == 0o755
        assert modes["ffmpeg-BUILD.txt"] == modes["ffmpeg-LICENSE.txt"] == 0o644


def test_macos_bundle_sets_the_execute_bits_on_exactly_the_two_tools(macos_bundle, monkeypatch):
    """G2a-F4: zipfile drops modes; 0755 goes on ffmpeg / ffprobe and on nothing else."""
    case = macos_bundle
    real_chmod = os.chmod
    modes: list[tuple[str, int]] = []

    def spy(path, mode, *args, **kwargs):
        modes.append((Path(path).name, mode))
        return real_chmod(path, mode, *args, **kwargs)

    monkeypatch.setattr(os, "chmod", spy)
    bundle_macos(case)
    executable = sorted({name for name, mode in modes if mode & 0o111})
    assert executable == ["ffmpeg", "ffprobe"]
    assert {mode for name, mode in modes if name in executable} == {0o755}
    assert {mode for name, mode in modes if name not in executable} == {0o644}
    # staged (out/ffmpeg) then placed (the .app): two 0755 calls per tool
    assert sorted(name for name, mode in modes if mode == 0o755) == ["ffmpeg"] * 2 + ["ffprobe"] * 2


@pytest.mark.parametrize("kind", ["argument", "lock", "download"])
def test_macos_bundle_verifies_before_opening_and_places_nothing(macos_bundle, kind):
    case = macos_bundle
    actual = case.data["github_sha256"]
    if kind == "lock":
        case.data["github_sha256"] = case.data["seat_sha256"] = "0" * 64
        case.pin.write_text(json.dumps(case.data), encoding="utf-8")
    if kind == "download":
        payload = case.source.read_bytes()
        case.source.write_bytes(payload[:-1] + bytes([payload[-1] ^ 1]))
    with pytest.raises(ValueError, match="sha256"):
        bundle_macos(case, sha256="0" * 64 if kind == "argument" else actual)
    assert sorted(p.name for p in case.app.rglob("*")) == [
        "Clearwater",
        "Contents",
        "Frameworks",
        "MacOS",
    ]
    assert not (case.out / "ffmpeg" / (case.data["archive_root"] + ".verified")).exists()


@pytest.mark.parametrize("name", ["../escape", "root/../escape", "C:/escape", "/absolute"])
def test_macos_bundle_refuses_unsafe_members(macos_bundle, name):
    macos_bundle.write(extra=[(name, b"unsafe")])
    with pytest.raises(ValueError, match="unsafe"):
        bundle_macos(macos_bundle)
    assert not (macos_bundle.app / "Contents/MacOS/ffmpeg").exists()


def test_macos_bundle_refuses_a_zip_symlink(macos_bundle):
    info = zipfile.ZipInfo("link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    macos_bundle.write(infos=[(info, b"bin/ffmpeg")])
    with pytest.raises(ValueError, match="unsafe"):
        bundle_macos(macos_bundle)


def test_macos_bundle_refuses_windows_tool_names(macos_bundle):
    root = macos_bundle.data["archive_root"]
    macos_bundle.write(omit=[f"{root}/bin/ffmpeg"], extra=[(f"{root}/bin/ffmpeg.exe", b"MZ")])
    with pytest.raises(ValueError, match="missing members"):
        bundle_macos(macos_bundle)


@pytest.mark.parametrize(
    ("tool", "damage", "error", "refusal"),
    [
        ("ffmpeg", "x86_64", ValueError, "not a thin arm64 Mach-O executable"),
        ("ffprobe", "dylib", ValueError, "not a thin arm64 Mach-O executable"),
        ("ffmpeg", "fat", ValueError, "not a thin arm64 Mach-O executable"),
        ("ffmpeg", "pe", ValueError, "not a thin arm64 Mach-O executable"),
        ("ffmpeg", "version", RuntimeError, "version token"),
        ("ffprobe", "second-version", RuntimeError, "version token"),
        ("ffmpeg", "no-version", RuntimeError, "version token"),
        ("ffmpeg", "configuration", RuntimeError, "configuration differs from the lock"),
        ("ffprobe", "configuration-prefix", RuntimeError, "configuration differs from the lock"),
        ("ffmpeg", "glued-version", RuntimeError, "version token"),
        ("ffmpeg", "older-version", RuntimeError, "version token"),
        ("ffprobe", "older-banner", RuntimeError, "version token"),
        ("ffmpeg", "other-banner", RuntimeError, "version token"),
        ("ffmpeg", "master-version", RuntimeError, "version token"),
        ("ffmpeg", "shallow-version", RuntimeError, "version token"),
        ("ffmpeg", "dated-numeric-version", RuntimeError, "version token"),
        ("ffprobe", "suffixed-version", RuntimeError, "version token"),
        ("ffmpeg", "second-configuration", RuntimeError, "configuration"),
    ],
)
def test_macos_bundle_checks_each_tool_without_running_it(
    macos_bundle, tool, damage, error, refusal
):
    """The F3b token and the configure line are read from the bytes; nothing is placed."""
    case = macos_bundle
    data = case.data
    name = f"{data['archive_root']}/bin/{tool}"
    payload = case.members[name]
    version = data["version"].encode()
    body = data["configure_line"].removeprefix("configuration: ").encode()
    if damage == "x86_64":
        payload = fake_macho(data, cpu=0x01000007)
    elif damage == "dylib":
        payload = fake_macho(data, filetype=6)
    elif damage == "fat":
        payload = b"\xca\xfe\xba\xbe" + payload[4:]
    elif damage == "pe":
        payload = b"MZ" + payload[2:]
    elif damage == "version":
        payload = payload.replace(version, version[:-1] + b"9")
    elif damage == "second-version":
        payload += b"\0n9.0.2-46-gb204e94e90-20261110\0"
    elif damage == "no-version":
        payload = payload.replace(b"\0" + version + b"\0", b"\0" + b"x" * len(version) + b"\0")
    elif damage == "configuration":
        payload = payload.replace(b"--enable-libx265", b"--enable-libx266")
    elif damage == "configuration-prefix":
        payload = payload.replace(b"\0" + body, b"\0X" + body)
    elif damage == "glued-version":
        payload = payload.replace(b"\0" + version, b"\0x" + version)
    elif damage == "older-version":  # A3-F2, the reviewer's probe: another major, then ours
        payload += b"\0n8.0.1-47-gdeadbeef-20261110\0"
    elif damage == "older-banner":  # libav*'s "FFmpeg version " FFMPEG_VERSION, a tarball build
        payload += b"\0FFmpeg version 8.0.1\0"
    elif damage == "other-banner":
        payload += b"\0FFmpeg version n9.0.1-12-gdeadbeef01-20261110\0"
    elif damage == "master-version":
        payload += b"\0N-121234-gdeadbeef01-20261110\0"
    elif damage == "shallow-version":
        payload += b"\0git-2026-01-01-deadbee-20261110\0"
    elif damage == "dated-numeric-version":
        payload += b"\x009.0.1-20261110\0"
    elif damage == "suffixed-version":
        payload += b"\0" + version + b"-x\0"
    else:  # a second FFMPEG_CONFIGURATION (the class sweep of A3-F2)
        payload += b"\0--prefix=/tmp/out --enable-gpl --enable-libx265\0"
    case.members[name] = payload
    case.write()
    trusted: set[str] = set()
    with pytest.raises(error, match=re.escape(refusal)):
        bundle_macos(case, verified_hashes=trusted)
    assert trusted == set()
    assert not (case.app / "Contents/MacOS/ffmpeg").exists()
    assert not (case.app / "Contents/Resources").exists()


def test_macos_bundle_reads_strings_across_the_read_boundary(macos_bundle):
    """Both strings may straddle the 1 MiB read boundary and are still found."""
    case = macos_bundle
    data = case.data
    name = f"{data['archive_root']}/bin/ffmpeg"
    payload = case.members[name]
    for needle in (data["version"].encode(), b"--enable-libass"):
        offset = payload.index(needle)
        pad = 1024 * 1024 - offset - len(needle) // 2
        head = len(macho_image())  # the padding goes after the load commands (A3-F1)
        case.members[name] = payload[:head] + b"\0" * pad + payload[head:]
        case.write()
        result = bundle_macos(case)
        assert result[0][1].startswith("ffmpeg version ")
        shutil.rmtree(case.app / "Contents/Resources")
        for tool in ("ffmpeg", "ffprobe"):
            (case.app / "Contents/MacOS" / tool).unlink()


def test_macos_bundle_admits_the_banner_form_of_the_locked_token(macos_bundle):
    """libav*'s ``"FFmpeg version " FFMPEG_VERSION`` arrays carry the same token: admitted."""
    case = macos_bundle
    name = f"{case.data['archive_root']}/bin/ffmpeg"
    case.members[name] += b"\0FFmpeg version " + case.data["version"].encode() + b"\0"
    case.write()
    assert bundle_macos(case)[0][1].startswith("ffmpeg version ")


def test_macos_bundle_admits_strings_a_real_arm64_ffmpeg_carries(macos_bundle):
    """Read in a real arm64 ffmpeg (Riedl 9.0.2, as data; ledger r1): libavutil's prose
    "Update your FFmpeg version to ..." and libvpx's own build configuration are not FFmpeg
    version / configuration candidates; a banner array after printable data bytes is."""
    case = macos_bundle
    name = f"{case.data['archive_root']}/bin/ffmpeg"
    case.members[name] += (
        b"\0 is not implemented. Update your FFmpeg version to the newest one from Git.\n\0"
        b"\0--prefix=/Volumes/ffmpeg_arm64/tool --disable-unit-tests\0"
        b"\xbfCJQFFmpeg version " + case.data["version"].encode() + b"\0"
    )
    case.write()
    assert bundle_macos(case)[0][1].startswith("ffmpeg version ")


def test_macos_bundle_reads_a_configuration_whatever_its_first_token(macos_bundle):
    """configure also takes ``cc=clang`` (its ``*)`` branch strips an optional ``--``), so
    the line may begin with a non-``--`` token: the lock's own line is still a candidate."""
    case = macos_bundle
    body = case.data["configure_line"].removeprefix("configuration: ")
    case.data["configure_line"] = "configuration: cc=clang " + body
    for tool in ("ffmpeg", "ffprobe"):
        case.members[f"{case.data['archive_root']}/bin/{tool}"] = fake_macho(case.data)
    case.write()
    assert bundle_macos(case)[1][1].startswith("ffprobe version ")


@pytest.mark.parametrize("needle", ["older-version", "older-banner"])
def test_macos_bundle_sees_a_conflicting_version_across_the_read_boundary(macos_bundle, needle):
    """A candidate straddling the 1 MiB block boundary is judged whole, in one block."""
    case = macos_bundle
    name = f"{case.data['archive_root']}/bin/ffmpeg"
    candidate = {
        "older-version": b"n8.0.1-47-gdeadbeef-20261110",
        "older-banner": b"FFmpeg version 8.0.1",
    }[needle]
    payload = case.members[name]
    for split in (1, len(candidate) // 2, len(candidate) - 1):
        pad = 1024 * 1024 - len(payload) - 1 - split
        case.members[name] = payload + b"\0" * pad + b"\0" + candidate + b"\0"
        case.write()
        with pytest.raises(RuntimeError, match="version token"):
            bundle_macos(case)


@pytest.mark.parametrize(
    "damage",
    [
        "minos-26",
        "minos-13",
        "minos-14.0.1",
        "platform-ios",
        "missing",
        "duplicate",
        "version-min-too",
        "version-min-only",
        "truncated-table",
        "short-table",
        "table-past-limit",
        "cmdsize-unaligned",
        "cmdsize-zero",
        "ntools-mismatch",
        "huge-ncmds",
    ],
)
def test_macos_bundle_refuses_a_tool_without_the_locked_deployment_target(macos_bundle, damage):
    """A3-F1: the bounded load-command table must carry ONE LC_BUILD_VERSION, macOS, minos =
    the lock's ``macos_deployment_target``; nothing is placed or trusted otherwise."""
    case = macos_bundle
    data = case.data
    version_min = struct.pack("<IIII", LC_VERSION_MIN_MACOSX, 16, macos_version(14), 0)
    commands: dict[str, Sequence[bytes]] = {
        "minos-26": [uuid_command(), build_version(macos_version(26))],
        "minos-13": [uuid_command(), build_version(macos_version(13))],
        "minos-14.0.1": [uuid_command(), build_version(macos_version(14, 0, 1))],
        "platform-ios": [uuid_command(), build_version(platform=2)],
        "missing": [uuid_command()],
        "duplicate": [uuid_command(), build_version(), build_version()],
        "version-min-too": [uuid_command(), build_version(), version_min],
        "version-min-only": [uuid_command(), version_min],
        "ntools-mismatch": [uuid_command(), build_version(tools=3)],
    }
    unaligned = build_version()[:4] + struct.pack("<I", 28) + build_version()[8:] + bytes(4)
    zero = build_version()[:4] + struct.pack("<I", 0) + build_version()[8:]
    images = {
        "truncated-table": macho_image(sizeofcmds=10_000_000),
        "short-table": macho_image(sizeofcmds=24),
        "table-past-limit": macho_image(sizeofcmds=2 * 1024 * 1024),
        "cmdsize-unaligned": macho_image([uuid_command(), unaligned]),
        "cmdsize-zero": macho_image([uuid_command(), zero]),
        "huge-ncmds": macho_image(ncmds=0xFFFFFFFF),
    }
    image = images.get(damage) or macho_image(commands[damage])
    padding = b"\0" * (3 * 1024 * 1024) if damage == "table-past-limit" else b""
    for tool in ("ffmpeg", "ffprobe"):
        case.members[f"{data['archive_root']}/bin/{tool}"] = fake_macho(data, image=image) + padding
    case.write()
    trusted: set[str] = set()
    with pytest.raises(ValueError, match="ffmpeg: ") as refused:
        bundle_macos(case, verified_hashes=trusted)
    assert "LC_BUILD_VERSION" in str(refused.value) or "load-command" in str(refused.value)
    assert trusted == set()
    assert not (case.app / "Contents/MacOS/ffmpeg").exists()


@pytest.mark.parametrize(
    "outside", ["outside-root/unrelated", "unrelated.txt", "ROOT-CASE/extra.txt", "ROOT"]
)
def test_macos_bundle_refuses_a_member_outside_the_archive_root(macos_bundle, outside):
    """A3-F5: on the macOS path every member lies under ``<archive_root>/``."""
    case = macos_bundle
    root = case.data["archive_root"]
    name = {"ROOT-CASE/extra.txt": root.upper() + "/extra.txt", "ROOT": root}.get(outside, outside)
    case.write(extra=[(name, b"x")])
    with pytest.raises(ValueError, match="outside the archive root"):
        bundle_macos(case)
    assert not (case.app / "Contents/MacOS/ffmpeg").exists()
    assert not (case.out / "ffmpeg" / (root + ".verified") / "ffmpeg").exists()


def test_macos_archive_root_rule_leaves_the_windows_inventory_unchanged(macos_bundle, tmp_path):
    """The Windows path's shared inventory still ignores an unextracted outside-root member."""
    windows = json.loads((REPO_ROOT / "tools/package/ffmpeg.lock.json").read_text("utf-8"))
    archive = tmp_path / "windows.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        for member in windows["extract_members"]:
            stream.writestr(f"{windows['archive_root']}/{member}", b"x")
        stream.writestr("outside-root/unrelated", b"x")
    with zipfile.ZipFile(archive) as stream:
        assert set(build._ffmpeg_archive_members(stream, windows)) == set(
            windows["extract_members"]
        )


def test_macos_bundle_refuses_a_destination_outside_an_app_before_download(macos_bundle, tmp_path):
    folder = tree(tmp_path / "onedir", ["Clearwater/Clearwater"]) / "Clearwater"
    with pytest.raises(ValueError, match=r"Contents/MacOS of a built \.app"):
        build.bundle_ffmpeg(
            folder,
            out=macos_bundle.out,
            url=macos_bundle.data["asset_url"],
            sha256=macos_bundle.data["github_sha256"],
            platform="darwin",
        )
    assert not (macos_bundle.out / "ffmpeg").exists()


def test_bundling_refuses_the_other_platforms_lock(macos_bundle, tmp_path, monkeypatch):
    """The macOS bundling path refuses a Windows lock; the Windows path a macOS lock."""
    windows = REPO_ROOT / "tools" / "package" / "ffmpeg.lock.json"
    monkeypatch.setattr(build, "FFMPEG_MACOS_LOCK_PATH", windows)
    with pytest.raises(ValueError, match="not a macOS lock"):
        bundle_macos(macos_bundle)
    monkeypatch.setattr(build, "FFMPEG_LOCK_PATH", macos_bundle.pin)
    destination = tree(tmp_path / "win", ["Clearwater.exe"])
    with pytest.raises(ValueError, match="is not the Windows lock"):
        build.bundle_ffmpeg(
            destination,
            out=macos_bundle.out,
            url=macos_bundle.data["asset_url"],
            sha256=macos_bundle.data["github_sha256"],
        )
    with pytest.raises(ValueError, match="no FFmpeg bundling for platform 'linux'"):
        build.bundle_ffmpeg(
            destination, out=macos_bundle.out, url="x", sha256="0" * 64, platform="linux"
        )
    assert not (macos_bundle.out / "ffmpeg").exists()


def test_macos_bundle_existing_tool_in_the_app_is_refused(macos_bundle):
    tree(macos_bundle.app, ["Contents/MacOS/ffprobe"])
    with pytest.raises(ValueError, match="already exists"):
        bundle_macos(macos_bundle)
    assert not (macos_bundle.app / "Contents/MacOS/ffmpeg").exists()
    assert not (macos_bundle.out / "ffmpeg").exists()


def test_darwin_build_bundles_from_the_macos_lock_and_refuses_release_while_census_pending(
    tmp_path, monkeypatch, capsys, macos_bundle
):
    """build() on darwin takes the macOS lock and the darwin bundling path."""
    case = macos_bundle
    calls = []

    def fetched(destination, **kwargs):
        calls.append((destination, kwargs))
        return [(destination / "ffmpeg", "ffmpeg version x")]

    seal_calls = []
    monkeypatch.setattr(build, "bundle_ffmpeg", fetched)
    monkeypatch.setattr(build.subprocess, "run", case.real_run)
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr(build, "native_origin_violations", lambda executable, **kwargs: [])
    monkeypatch.setattr(build, "seal_macos_bundle", seal_calls.append)
    out = tmp_path / "build-out"
    # Built (and PyInstaller imported) BEFORE sys.platform reads darwin (darwin_app_build).
    source = make_exe(out / "synthetic", [], modules=["clearwater", "graphlib"])

    def build_folder(args):
        target = Path(args[args.index("--distpath") + 1]) / "Clearwater.app/Contents/MacOS"
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target / "Clearwater")

    monkeypatch.setattr(build, "run_pyinstaller", build_folder)
    monkeypatch.setattr(build.sys, "platform", "darwin")
    status = build.build(
        "onedir",
        out=out,
        ffmpeg_from=case.data["asset_url"],
        ffmpeg_sha256=case.data["github_sha256"],
    )
    assert status == 0, capsys.readouterr().out
    assert len(calls) == 1 and calls[0][1]["platform"] == "darwin"
    assert calls[0][0].as_posix().endswith("Clearwater.app/Contents/MacOS")
    assert calls[0][1]["url"] == case.data["asset_url"]
    for flags in ({"notices": True}, {"notices": True, "smoke": True, "zip_release": True}):
        assert (
            build.build(
                "onedir",
                out=out,
                ffmpeg_from=case.data["asset_url"],
                ffmpeg_sha256=case.data["github_sha256"],
                **flags,
            )
            == 1
        )
        assert "census pending" in capsys.readouterr().out
    assert len(calls) == 1
    assert (
        build.build("onedir", out=out, ffmpeg_from=case.data["asset_url"], ffmpeg_sha256="1" * 64)
        == 1
    )
    assert "FFmpeg URL/sha256 differ from the lock" in capsys.readouterr().out
