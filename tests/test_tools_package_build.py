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
import builtins
import hashlib
import importlib.metadata
import importlib.util
import inspect
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
from collections.abc import Callable, Sequence
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
    # The name build.py reads; Windows folds the case of environment names, POSIX does not
    # (the darwin runner's win32-simulated ids failed on SystemRoot; WP6.5 G3, C11).
    monkeypatch.setenv("SYSTEMROOT", str(windows))
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


@pytest.mark.skipif(
    sys.platform != "win32", reason="PE bootloader checks; pefile is win32-only (uv.lock)"
)
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


@pytest.mark.skipif(
    sys.platform != "win32", reason="PE bootloader checks; pefile is win32-only (uv.lock)"
)
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
@pytest.mark.skipif(
    sys.platform != "win32",
    reason="the Windows FFmpeg bundle contract (ffmpeg.lock.json, Clearwater.exe); its "
    "_on_darwin counterpart checks the committed ffmpeg-macos.lock.json on every host",
)
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


@pytest.mark.skipif(
    sys.platform != "win32", reason="PE bootloader checks; pefile is win32-only (uv.lock)"
)
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


# WP6.5 run 4: literal names/links from work/wp6.5/run4-stage/app-listing.txt.
# Keep these small fixtures here, independent of the uncommitted runner evidence.
RUN4_EXTENSIONS = (
    "numpy/random/_generator.cpython-312-darwin.so",
    "scipy/linalg/_flapack.cpython-312-darwin.so",
    "PIL/_imaging.cpython-312-darwin.so",
    "PySide6/QtCore.abi3.so",
    "_pillow_heif.cpython-312-darwin.so",
)
RUN4_MIRRORS = (
    ("numpy", "../Frameworks/numpy", True),
    ("scipy", "../Frameworks/scipy", True),
    ("PIL", "../Frameworks/PIL", True),
    ("PySide6/QtCore.abi3.so", "../../Frameworks/PySide6/QtCore.abi3.so", False),
    (
        "_pillow_heif.cpython-312-darwin.so",
        "../Frameworks/_pillow_heif.cpython-312-darwin.so",
        False,
    ),
)


def app_content_paths(root: Path, app: Path) -> list[str]:
    """Use the explicit app form, or the old API for the parent's RED record."""
    if "app" in inspect.signature(build.forbidden_paths).parameters:
        return build.forbidden_paths(root, app=app)
    return build.forbidden_paths(root)


def run4_content_release(tmp_path: Path, names=RUN4_EXTENSIONS) -> tuple[Path, Path]:
    """Physical Frameworks extensions and their run-4 Resources mirror symlinks."""
    root = tmp_path / "Clearwater-1.1.1-macos-onedir"
    app = root / "Clearwater.app"
    tree(app, ["Contents/MacOS/Clearwater", "Contents/Info.plist", "Contents/PkgInfo"])
    tree(app, [f"Contents/Frameworks/{name}" for name in names], LINK_BLOB)
    packages = {PurePosixPath(name).parts[0] for name in names}
    for name, target, folder in RUN4_MIRRORS:
        if PurePosixPath(name).parts[0] in packages:
            _symlink(app / "Contents/Resources" / name, target, folder=folder)
    return root, app


@pytest.mark.parametrize("name", RUN4_EXTENSIONS)
@pytest.mark.parametrize("root_is_app", [False, True], ids=["release", "app"])
def test_run4_content_allows_framework_modules_and_resource_links(tmp_path, name, root_is_app):
    """Frozen dependencies use their package name, for release and smoke roots."""
    root, app = run4_content_release(tmp_path, [name])
    assert app_content_paths(app if root_is_app else root, app) == []


@pytest.mark.parametrize(
    "where",
    [
        "Contents/Frameworks/cupy/runtime.so",
        "Contents/Frameworks/numpy/cupy/runtime.so",
        "Contents/Resources/PIL/cupy/runtime.so",
        "Contents/MacOS/cupy/runtime.so",
        "Contents/_CodeSignature/cupy/runtime.so",
        "Contents/cupy/runtime.so",
    ],
)
def test_run4_content_still_refuses_gpu_names_at_every_depth(tmp_path, where):
    """Mapping and metadata exemptions never exempt the GPU-name rule."""
    root, app = run4_content_release(tmp_path, [])
    tree(app, [where])
    assert hits(app_content_paths(root, app), f"{where} (gpu-module)")


@pytest.mark.parametrize("where", ["Contents/MacOS/numpy.so", "Contents/numpy.so"])
def test_run4_content_refuses_modules_outside_frozen_path_folders(tmp_path, where):
    """Even an allowed package's extension cannot sit beside the executable."""
    root, app = run4_content_release(tmp_path, [])
    tree(app, [where])
    assert hits(app_content_paths(root, app), f"{where} (unexpected-module)")


@pytest.mark.parametrize("folder", [False, True], ids=["file", "folder"])
def test_run4_content_checks_the_links_own_gpu_name(tmp_path, folder):
    """An admitted alias cannot conceal a forbidden name behind an allowed target."""
    root, app = run4_content_release(tmp_path, ["numpy/random/_generator.cpython-312-darwin.so"])
    name = "cupy" if folder else "cupy.so"
    target = "../Frameworks/numpy" + ("" if folder else "/random/_generator.cpython-312-darwin.so")
    _symlink(app / "Contents/Resources" / name, target, folder=folder)
    assert hits(app_content_paths(root, app), f"Resources/{name} (gpu-module)")


def test_run4_content_metadata_exempts_only_the_module_root_rule(tmp_path):
    """Info/PkgInfo and signature metadata are allowed; other name rules remain."""
    root, app = run4_content_release(tmp_path, [])
    tree(app, ["Contents/_CodeSignature/private.so"])
    assert app_content_paths(root, app) == []
    tree(app, ["Contents/_CodeSignature/libnvrtc.so"])
    assert hits(app_content_paths(root, app), "_CodeSignature/libnvrtc.so (cuda-library)")


def test_run4_content_checks_only_physical_archives(tmp_path, monkeypatch):
    """ZIP suffix/magic checks open physical files; mirror links are never opened."""
    root, app = run4_content_release(tmp_path, [])
    archive = app / "Contents/Frameworks/base_library.zip"
    archive.parent.mkdir(parents=True)
    archive.write_bytes(zip_bytes({"cupy/__init__.pyc": b"x"}))
    alias = app / "Contents/Resources/base_library.zip"
    _symlink(alias, "../Frameworks/base_library.zip", folder=False)
    recorder = _FsRecorder()
    with pytest.MonkeyPatch.context() as patch:
        recorder.install(patch)
        found = app_content_paths(root, app)
    assert hits(found, "Frameworks/base_library.zip!cupy/__init__.pyc (gpu-module)")
    assert not hits(found, "Resources/base_library.zip!")
    assert not [call for call in recorder.calls if call[0] in _OPENS and call[1] == str(alias)]
    assert recorder.violations(root, tmp_path / "outside") == []


def test_run4_content_recorder_on_extensions_and_resource_mirrors(tmp_path):
    """Covered shape 5: content checks on run-4 Frameworks files and mirror links."""
    root, app = run4_content_release(tmp_path)
    recorder = _FsRecorder()
    with pytest.MonkeyPatch.context() as patch:
        recorder.install(patch)
        found = app_content_paths(root, app)
    assert found == []
    assert recorder.calls
    assert set(recorder.admitted(app)) == {
        f"Contents/Resources/{name}" for name, _, _ in RUN4_MIRRORS
    }
    assert recorder.violations(root, tmp_path / "outside") == []


def test_run4_content_refuses_a_linked_app_before_entering_it(tmp_path):
    """A linked .app child of the release root is never used as the walk boundary."""
    root = tmp_path / "release"
    outside = tree(tmp_path / "outside", ["Contents/Frameworks/numpy/core.so"])
    app = root / "Clearwater.app"
    _symlink(app, "../outside", folder=True)
    recorder = _FsRecorder()
    with pytest.MonkeyPatch.context() as patch:
        recorder.install(patch)
        found = app_content_paths(root, app)
    assert found
    assert recorder.violations(root, outside) == []


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
@pytest.mark.skipif(
    sys.platform != "win32",
    reason="the PyInstaller stand-in writes the Windows Clearwater.exe; the macOS build "
    "seals a .app (codesign) and scans no GPU pack (AD-33), WP6.5 part 3",
)
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


@pytest.mark.skipif(sys.platform == "darwin", reason="no GPU pack is scanned on macOS (AD-33)")
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
@pytest.mark.skipif(
    sys.platform != "win32",
    reason="the Windows FFmpeg bundle contract (ffmpeg.lock.json, Clearwater.exe); its "
    "_on_darwin counterpart checks the committed ffmpeg-macos.lock.json on every host",
)
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
@pytest.mark.skipif(
    sys.platform != "win32",
    reason="the Windows FFmpeg bundle contract (ffmpeg.lock.json, Clearwater.exe); its "
    "_on_darwin counterpart checks the committed ffmpeg-macos.lock.json on every host",
)
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
@pytest.mark.skipif(
    sys.platform != "win32",
    reason="the PyInstaller stand-in writes the Windows Clearwater.exe; the macOS build "
    "seals a .app (codesign) and scans no GPU pack (AD-33), WP6.5 part 3",
)
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
@pytest.mark.skipif(
    sys.platform != "win32",
    reason="the Windows FFmpeg bundle contract (ffmpeg.lock.json, Clearwater.exe); its "
    "_on_darwin counterpart checks the committed ffmpeg-macos.lock.json on every host",
)
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
@pytest.mark.skipif(
    sys.platform != "win32",
    reason="the Windows FFmpeg bundle contract (ffmpeg.lock.json, Clearwater.exe); its "
    "_on_darwin counterpart checks the committed ffmpeg-macos.lock.json on every host",
)
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
PYSIDE_LIB = "libpyside6.abi3.6.12.dylib"
"""The library run 3's build refused (``build.log:115``): a Resources -> Frameworks chain."""

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
    # Inside a .app a link to a link is a CHAIN (WP6.5 run 3, ruling (b)): admitted when every
    # hop is relative POSIX text inside Contents and the chain ends in a regular file there.
    "C-app-link-to-a-link": (
        "app",
        ["Contents/Resources/data.txt"],
        [
            ("Contents/Frameworks/data.txt", "../Resources/data.txt", False),
            ("Contents/MacOS/data.txt", "../Frameworks/data.txt", False),
        ],
        None,
    ),
    "C-app-pyinstaller-chain": (
        "app",
        [f"Contents/Frameworks/PySide6/{PYSIDE_LIB}"],
        [
            (f"Contents/Frameworks/{PYSIDE_LIB}", f"PySide6/{PYSIDE_LIB}", False),
            (f"Contents/Resources/{PYSIDE_LIB}", f"../Frameworks/{PYSIDE_LIB}", False),
        ],
        None,
    ),
    "onedir-two-hop-chain": (
        "onedir",
        [f"_internal/PySide6/{PYSIDE_LIB}"],
        [
            (f"_internal/{PYSIDE_LIB}", f"PySide6/{PYSIDE_LIB}", False),
            (f"_internal/sub/{PYSIDE_LIB}", f"../{PYSIDE_LIB}", False),
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
    """(C) a folder target is walked: a bad link inside it refuses the folder link too.

    Inside a .app the escaping link is refused by the component walk, which runs first
    (WP6.5 A r12 #1), so the reason is its chain, not "outside the release folder".
    """
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
    heading = Path(os.path.realpath(folder.parent)) / "outside"
    escape = (
        "link chain leaves the bundle: Contents/Frameworks/pkg/evil -> '../../../../outside'; "
        f"{heading}"
    )
    assert problem == f"evil under the linked folder: {escape}"
    found = link_origin_check(tmp_path, monkeypatch, executable)
    assert len(found) == 2 and all(escape in line for line in found), found


def test_the_pyinstaller_chain_is_admitted_in_the_origin_walk(tmp_path, monkeypatch):
    """Run 3 (b): run 3's exact refusal, ``build.log:115``, is gone for the BUNDLE shape."""
    layout, files, links, _ = LINK_CASES["C-app-pyinstaller-chain"]
    folder, executable = link_release(tmp_path, layout, files, links)
    contents = folder / "Contents/Frameworks"
    for path, _, _ in links:
        assert build.macos_link_problem(folder, contents, folder / path) is None
    assert link_origin_check(tmp_path, monkeypatch, executable) == []


def test_the_onedir_two_hop_chain_keeps_todays_message(tmp_path, monkeypatch):
    """Run 3 (b): outside a .app the one-hop rule and its message are unchanged."""
    layout, files, links, _ = LINK_CASES["onedir-two-hop-chain"]
    _, executable = link_release(tmp_path, layout, files, links)
    link = executable.parent / f"_internal/sub/{PYSIDE_LIB}"
    assert link_origin_check(tmp_path, monkeypatch, executable) == [
        f"native origin: linked file {link}: link to a link (one hop only)"
    ]


CHAIN_REFUSALS: dict[str, tuple[list[str], list[tuple[str, str, bool]], str, list[str]]] = {
    # name: (files, links (path, target, folder), reason prefix, the hops the message lists)
    "leaves-the-release": (
        [],
        [
            ("Contents/Resources/libx.dylib", "../Frameworks/libx.dylib", False),
            ("Contents/Frameworks/libx.dylib", "../../../../outside/libx.dylib", False),
        ],
        "link chain leaves the bundle: ",
        [
            "Contents/Resources/libx.dylib -> '../Frameworks/libx.dylib'",
            "Contents/Frameworks/libx.dylib -> '../../../../outside/libx.dylib'",
        ],
    ),
    "leaves-contents-inside-the-app": (
        ["Info.plist"],
        [
            ("Contents/Resources/Info.plist", "../Frameworks/Info.plist", False),
            ("Contents/Frameworks/Info.plist", "../../Info.plist", False),
        ],
        "link chain leaves the bundle: ",
        [
            "Contents/Resources/Info.plist -> '../Frameworks/Info.plist'",
            "Contents/Frameworks/Info.plist -> '../../Info.plist'",
            "Info.plist",
        ],
    ),
    "dangling": (
        [],
        [
            ("Contents/Resources/libx.dylib", "../Frameworks/libx.dylib", False),
            ("Contents/Frameworks/libx.dylib", "PySide6/libx.dylib", False),
        ],
        "link chain ends in a missing entry: ",
        [
            "Contents/Resources/libx.dylib -> '../Frameworks/libx.dylib'",
            "Contents/Frameworks/libx.dylib -> 'PySide6/libx.dylib'",
            "Contents/Frameworks/PySide6/libx.dylib",
        ],
    ),
    "loop": (
        [],
        [
            ("Contents/Resources/libx.dylib", "../Frameworks/libx.dylib", False),
            ("Contents/Frameworks/libx.dylib", "../Resources/libx.dylib", False),
        ],
        "link chain loops: ",
        [
            "Contents/Resources/libx.dylib -> '../Frameworks/libx.dylib'",
            "Contents/Frameworks/libx.dylib -> '../Resources/libx.dylib'",
            "Contents/Resources/libx.dylib",
        ],
    ),
    "ends-in-a-folder": (
        ["Contents/Frameworks/pkg2/data.txt"],
        [
            ("Contents/Resources/pkg", "../Frameworks/pkg", True),
            ("Contents/Frameworks/pkg", "pkg2", True),
        ],
        "link chain does not end in a regular file: ",
        [
            "Contents/Resources/pkg -> '../Frameworks/pkg'",
            "Contents/Frameworks/pkg -> 'pkg2'",
            "Contents/Frameworks/pkg2",
        ],
    ),
}


@pytest.mark.parametrize("case", sorted(CHAIN_REFUSALS))
def test_a_bad_chain_inside_a_app_is_refused_with_every_hop(tmp_path, monkeypatch, case):
    """Run 3 (b): out of the bundle, dangling, a loop, a folder end; every hop is named."""
    files, links, reason, hops = CHAIN_REFUSALS[case]
    folder, executable = link_release(tmp_path, "app", files, links)
    first = folder / links[0][0]
    problem = build.macos_link_problem(folder, folder / "Contents/Frameworks", first)
    assert problem is not None and problem.startswith(reason), problem
    shown = problem.removeprefix(reason).split("; ")
    assert shown[: len(hops)] == hops, shown
    # Out of the release, the last hop is shown as its absolute path.
    assert len(shown) == len(hops) + (case == "leaves-the-release"), shown
    found = link_origin_check(tmp_path, monkeypatch, executable)
    assert f"native origin: linked file {first}: {problem}" in found


@pytest.mark.parametrize("count", [8, 9])
def test_a_chain_is_bounded_in_length(tmp_path, count):
    """Run 3 (b): eight hops ending in a file are admitted; a ninth is refused, every hop named."""
    links = [
        (f"Contents/Frameworks/c{index}", f"c{index + 1}", False) for index in range(count - 1)
    ]
    links.append((f"Contents/Frameworks/c{count - 1}", "data.bin", False))
    folder, _ = link_release(tmp_path, "app", ["Contents/Frameworks/data.bin"], links)
    problem = build.macos_link_problem(
        folder, folder / "Contents/Frameworks", folder / "Contents/Frameworks/c0"
    )
    if count == 8:
        assert problem is None
    else:
        hops = [f"Contents/Frameworks/c{index} -> 'c{index + 1}'" for index in range(8)]
        assert problem == "link chain is longer than 8 hops: " + "; ".join(
            [*hops, "Contents/Frameworks/c8"]
        )


def test_a_chain_with_an_absolute_hop_is_refused(tmp_path):
    """Run 3 (b): a hop whose stored text is absolute (or not POSIX) refuses the chain."""
    folder, _ = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/libx.dylib"],
        [("Contents/Resources/libx.dylib", "../Frameworks/liby.dylib", False)],
    )
    second = folder / "Contents/Frameworks/liby.dylib"
    _symlink(second, str(folder / "Contents/Frameworks/libx.dylib"), folder=False)
    problem = build.macos_link_problem(
        folder, folder / "Contents/Frameworks", folder / "Contents/Resources/libx.dylib"
    )
    target = os.readlink(second)
    assert problem == (
        f"link chain hop target {target!r} is absolute or not POSIX: "
        f"Contents/Resources/libx.dylib -> '../Frameworks/liby.dylib'; "
        f"Contents/Frameworks/liby.dylib -> {target!r}"
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows junction regression")
def test_a_chain_that_meets_a_junction_is_refused(tmp_path):
    """Run 3 (b): a junction hop refuses the chain even when it stays inside the bundle."""
    import _winapi

    folder, _ = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/pkg2/data.txt"],
        [("Contents/Resources/pkg", "../Frameworks/pkg", True)],
    )
    _winapi.CreateJunction(
        str(folder / "Contents/Frameworks/pkg2"), str(folder / "Contents/Frameworks/pkg")
    )
    problem = build.macos_link_problem(
        folder, folder / "Contents/Frameworks", folder / "Contents/Resources/pkg"
    )
    assert problem == (
        "link chain meets a junction: Contents/Resources/pkg -> '../Frameworks/pkg'; "
        "Contents/Frameworks/pkg (junction)"
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows junction regression")
def test_a_chain_handed_over_as_its_real_path_is_labelled_from_the_real_app(tmp_path):
    """Run 3 (b): a folder link's view hands a nested link over as its REAL path; under a
    release root named through an alias (here a junction; ``/var`` -> ``/private/var`` on a
    Mac) the chain is labelled from the real .app, never a ``relative_to`` error."""
    import _winapi

    real = tmp_path / "real"
    folder, _ = link_release(
        real,
        "app",
        [],
        [
            ("Contents/Resources/libx.dylib", "../Frameworks/libx.dylib", False),
            ("Contents/Frameworks/libx.dylib", "missing.dylib", False),
        ],
    )
    _winapi.CreateJunction(str(real / "wrapper"), str(tmp_path / "alias"))
    alias = tmp_path / "alias" / folder.name
    problem = build._macos_link_chain_problem(alias, folder / "Contents/Resources/libx.dylib")
    assert problem == (
        "link chain ends in a missing entry: "
        "Contents/Resources/libx.dylib -> '../Frameworks/libx.dylib'; "
        "Contents/Frameworks/libx.dylib -> 'missing.dylib'; Contents/Frameworks/missing.dylib"
    )


# --- WP6.5 A r11 #1: the walk is component by component from the canonical Contents ------
# realpath(named.parent) collapsed the traversal, so an alias OUTSIDE the bundle (never
# walked) could carry an escaping hop back inside, and folder links escaped the hop count.


def outside_alias(folder: Path, name: str) -> Path:
    """``outside/<name>`` beside the ``.app`` (in the test's tmp folder), as A's probe had,
    leading back to ``Contents/Frameworks/pkg``.

    Its text uses the host's separator: the alias is outside the bundle, so the rule never
    reads it, and a Windows host follows a folder link only through backslash text.
    """
    alias = folder.parent / "outside" / name
    _symlink(alias, os.path.join("..", folder.name, "Contents", "Frameworks", "pkg"), folder=True)
    assert Path(os.path.realpath(alias)) == Path(
        os.path.realpath(folder / "Contents/Frameworks/pkg")
    )
    return alias


def test_a_chain_through_an_outside_alias_is_refused_where_it_leaves(tmp_path, monkeypatch):
    """A r11's exact shape: both bundle links refused, the outside hop named in the message."""
    folder, executable = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/pkg/data"],
        [
            ("Contents/Resources/data", "../Frameworks/data", False),
            ("Contents/Frameworks/data", "../../../outside/back/data", False),
        ],
    )
    # The alias really does lead back in: the escaping text names a contained file.
    assert (outside_alias(folder, "back") / "data").is_file()
    heading = str(Path(os.path.realpath(folder.parent)) / "outside" / "back" / "data")
    contents = folder / "Contents/Frameworks"
    outward = "Contents/Frameworks/data -> '../../../outside/back/data'"
    assert build.macos_link_problem(folder, contents, folder / "Contents/Resources/data") == (
        f"link chain leaves the bundle: Contents/Resources/data -> '../Frameworks/data'; "
        f"{outward}; {heading}"
    )
    assert build.macos_link_problem(folder, contents, folder / "Contents/Frameworks/data") == (
        f"link chain leaves the bundle: {outward}; {heading}"
    )
    found = link_origin_check(tmp_path, monkeypatch, executable)
    assert len(found) == 2 and all(heading in line for line in found), found
    with pytest.raises(ValueError, match="release ZIP refuses linked/junction/outside") as error:
        build.write_release_zip(folder, out=tmp_path / "out", source_epoch=1793908801)
    assert heading in str(error.value)
    assert not (tmp_path / "out").exists()


def _outside_contents(folder: Path, path: str) -> bool:
    """Whether a path handed to the filesystem lies (lexically) outside ``Contents`` and is
    not the release root or one of its ancestors (canonicalising the boundary may stat those).
    """
    seen = Path(os.path.normpath(path))
    for root in (folder, Path(os.path.realpath(folder))):
        if seen.is_relative_to(root / "Contents") or root.is_relative_to(seen):
            return False
    return True


@pytest.mark.parametrize("link", ["Contents/Resources/data", "Contents/Frameworks/data"])
def test_the_walk_resolves_nothing_outside_contents(tmp_path, monkeypatch, link):
    """A r12 #1: on A's out-and-back shape the whole rule resolves, reads and stats nothing
    outside ``Contents`` (``os.path.realpath``, ``os.readlink``, ``os.stat``, ``os.lstat``
    recorded): the walk refuses before any call that follows the outside alias."""
    folder, _ = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/pkg/data"],
        [
            ("Contents/Resources/data", "../Frameworks/data", False),
            ("Contents/Frameworks/data", "../../../outside/back/data", False),
        ],
    )
    outside_alias(folder, "back")
    calls: list[tuple[str, str]] = []

    def recorder(name, real):
        def recorded(path, *args, **kwargs):
            calls.append((name, os.fspath(path)))
            return real(path, *args, **kwargs)

        return recorded

    for name in ("readlink", "stat", "lstat"):
        monkeypatch.setattr(build.os, name, recorder(name, getattr(os, name)))
    monkeypatch.setattr(build.os.path, "realpath", recorder("realpath", os.path.realpath))
    try:
        problem = build.macos_link_problem(folder, folder / "Contents/Frameworks", folder / link)
    finally:
        monkeypatch.undo()
    assert problem is not None and problem.startswith("link chain leaves the bundle: "), problem
    assert calls
    assert [call for call in calls if _outside_contents(folder, call[1])] == []


@pytest.mark.parametrize("link", ["Contents/Resources/data", "Contents/Frameworks/data"])
def test_a_missing_return_file_still_refuses_with_the_chain(tmp_path, link):
    """A r12 #1: with the file the alias returns to removed, the shape is still refused as
    leaving the bundle, with its chain, never as a bare "dangling link"."""
    folder, _ = link_release(
        tmp_path,
        "app",
        [],
        [
            ("Contents/Resources/data", "../Frameworks/data", False),
            ("Contents/Frameworks/data", "../../../outside/back/data", False),
        ],
    )
    (folder / "Contents/Frameworks/pkg").mkdir(parents=True)
    outside_alias(folder, "back")
    heading = Path(os.path.realpath(folder.parent)) / "outside" / "back" / "data"
    hops = ["Contents/Frameworks/data -> '../../../outside/back/data'", str(heading)]
    if link == "Contents/Resources/data":
        hops.insert(0, "Contents/Resources/data -> '../Frameworks/data'")
    problem = build.macos_link_problem(folder, folder / "Contents/Frameworks", folder / link)
    assert problem == "link chain leaves the bundle: " + "; ".join(hops)


# --- WP6.5 A r13: no FOLLOWING call before the walk admits every link on the path ----------
# The invariant (CHARC 4ed56fcb): inside a .app no filesystem call that follows a link
# (stat, realpath, exists, is_file / is_dir with following, DirEntry.is_dir() by default,
# open) is made on a path at or under the release root until every link on that path has
# been admitted by the component walk; only lstat / readlink / is_symlink / is_junction and
# non-following DirEntry queries precede admission.

_REAL_FS: dict[str, Any] = {
    "stat": os.stat,
    "lstat": os.lstat,
    "readlink": os.readlink,
    "scandir": os.scandir,
    "listdir": os.listdir,
    "realpath": os.path.realpath,
    "exists": os.path.exists,
    "isfile": os.path.isfile,
    "isdir": os.path.isdir,
    "open": builtins.open,
    "io.open": io.open,
    "os.open": os.open,
}


class _FsRecorder:
    """Record the filesystem calls the link rule's callers make, with the walk's admissions.

    EVIDENCE FOR ITS COVERED SHAPES, not a proof of every following call (WP6.5 A r14 #2).
    It records, as ``(call, path, following)`` in one ordered sequence:

    - ``os.stat`` (its ``follow_symlinks``), ``os.lstat``, ``os.readlink``,
      ``os.path.realpath``, ``os.scandir`` and ``os.listdir``;
    - ``os.path.exists`` / ``isfile`` / ``isdir`` (the Windows fast paths bypass ``os.stat``);
    - every ``DirEntry`` of a recorded listing: ``is_dir`` / ``is_file`` / ``stat`` with
      their ``follow_symlinks``;
    - ``Path.exists`` / ``is_file`` / ``is_dir`` / ``resolve`` / ``open`` (``read_bytes``
      and ``read_text`` open through ``Path.open`` and ``io.open``);
    - the real opens: ``builtins.open``, ``io.open`` and ``os.open`` (the final component
      not followed under ``O_NOFOLLOW``);
    - ``admit``: the component walk (``build._macos_link_chain_problem``) admitting a link,
      at the moment it returns.

    ``following`` says whether the FINAL component is followed; every call follows its
    ancestors, so :meth:`violations` checks them for every call, the non-following ones
    (``lstat``, ``readlink``, ``O_NOFOLLOW``, ``DirEntry`` queries with
    ``follow_symlinks=False``) included (A r15 #3). A relative path is recorded joined to
    the working folder at the moment of the call, ``..`` kept as written (A r15 #1).

    Not covered: opens made in C below these names (``io.FileIO`` constructed directly, an
    extension module's own ``fopen``), child processes, calls on a file descriptor or with
    ``dir_fd``, and ``DirEntry.is_symlink`` / ``is_junction`` (cached from the listing, whose
    ``scandir`` is recorded).
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, bool]] = []

    def note(self, name: str, path: Any, following: bool) -> None:
        if not isinstance(path, int):
            raw = os.fspath(path)
            if not os.path.isabs(raw):
                raw = os.path.join(os.getcwd(), raw)  # joined, never normalised
            self.calls.append((name, raw, following))

    def install(self, patch: pytest.MonkeyPatch) -> None:
        recorder = self

        def stat_(path, *args, follow_symlinks=True, **kwargs):
            recorder.note("stat", path, follow_symlinks)
            return _REAL_FS["stat"](path, *args, follow_symlinks=follow_symlinks, **kwargs)

        def plain(name: str, following: bool) -> Any:
            def call(path=".", *args, **kwargs):
                recorder.note(name, path, following)
                return _REAL_FS[name](path, *args, **kwargs)

            return call

        def os_open_(path, flags, *args, **kwargs):
            recorder.note("os.open", path, not flags & getattr(os, "O_NOFOLLOW", 0))
            return _REAL_FS["os.open"](path, flags, *args, **kwargs)

        class Entry:
            def __init__(self, entry: os.DirEntry) -> None:
                self._entry, self.name, self.path = entry, entry.name, entry.path

            def __getattr__(self, name: str) -> Any:
                return getattr(self._entry, name)

            def is_dir(self, *, follow_symlinks: bool = True) -> bool:
                recorder.note("DirEntry.is_dir", self.path, follow_symlinks)
                return self._entry.is_dir(follow_symlinks=follow_symlinks)

            def is_file(self, *, follow_symlinks: bool = True) -> bool:
                recorder.note("DirEntry.is_file", self.path, follow_symlinks)
                return self._entry.is_file(follow_symlinks=follow_symlinks)

            def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
                recorder.note("DirEntry.stat", self.path, follow_symlinks)
                return self._entry.stat(follow_symlinks=follow_symlinks)

        class Listing:
            def __init__(self, listing: Any) -> None:
                self._listing = listing

            def __enter__(self) -> Listing:
                return self

            def __exit__(self, *exc: object) -> None:
                self._listing.close()

            def __iter__(self) -> Listing:
                return self

            def __next__(self) -> Entry:
                return Entry(next(self._listing))

            def close(self) -> None:
                self._listing.close()

        def scandir_(path=".", *args, **kwargs):
            recorder.note("scandir", path, True)
            return Listing(_REAL_FS["scandir"](path, *args, **kwargs))

        def following(name: str, real: Any) -> Any:
            def query(self, *args, **kwargs):
                recorder.note(f"Path.{name}", self, kwargs.get("follow_symlinks", True))
                return real(self, *args, **kwargs)

            return query

        real_walk = build._macos_link_chain_problem

        def walk_(root: Path, physical: Path) -> str | None:
            problem = real_walk(root, physical)
            if problem is None:
                recorder.note("admit", physical, False)
            return problem

        patch.setattr(os, "stat", stat_)
        patch.setattr(os, "lstat", plain("lstat", False))
        patch.setattr(os, "readlink", plain("readlink", False))
        patch.setattr(os, "scandir", scandir_)
        patch.setattr(os, "listdir", plain("listdir", True))
        patch.setattr(os, "open", os_open_)
        patch.setattr(os.path, "realpath", plain("realpath", True))
        for name in ("exists", "isfile", "isdir"):
            patch.setattr(os.path, name, plain(name, True))
        patch.setattr(builtins, "open", plain("open", True))
        patch.setattr(io, "open", plain("io.open", True))
        for name in ("exists", "is_file", "is_dir", "resolve", "open"):
            patch.setattr(Path, name, following(name, getattr(Path, name)))
        patch.setattr(build, "_macos_link_chain_problem", walk_)

    @staticmethod
    def _bases(root: Path) -> list[Path]:
        return [root, Path(_REAL_FS["realpath"](root))]

    def admitted(self, root: Path) -> list[str]:
        """The links the walk admitted, in order, relative to the release root."""
        found = []
        for name, raw, _ in self.calls:
            if name != "admit":
                continue
            path = Path(os.path.normpath(raw))
            for base in self._bases(root):
                if path.is_relative_to(base):
                    found.append(path.relative_to(base).as_posix())
                    break
        return found

    def violations(self, root: Path, zone: Path) -> list[tuple[str, str]]:
        """Calls, in their recorded order, that break the invariant on this shape.

        A call is a violation when it touches ``zone`` (outside the bundle) at all, or when
        the system's reading of its path FOLLOWS a link (a symlink, or a junction by
        ``os.path.isjunction``, looked up per call) that is either:

        - under the release root and not admitted by the walk EARLIER in the sequence (an
          admission after the call does not excuse it; a link met while following an
          admitted link's text was validated by that walk); or
        - outside the release root with text leading STRICTLY under it (a host alias into
          the bundle, A r14's residual). An alias to the root or above it (macOS ``/var``)
          is not one.

        The path is read as the system reads it (:meth:`_followed`): from its anchor, every
        ancestor followed, the final component only when the call follows (A r15 #3); a link
        is replaced by its text at its PHYSICAL position, so a component after an allowed
        alias is still recognised under the release root (A r15 #2), and ``..`` steps from
        the physical position. A relative path (a hand-built call) is joined to the working
        folder (A r15 #1).
        """
        bases = self._bases(root)
        admitted: set[str] = set()
        found = []

        def inside(path: Path) -> str | None:
            for base in bases:
                if path != base and path.is_relative_to(base):
                    return path.relative_to(base).as_posix()
            return None

        for name, raw, follows in self.calls:
            written = raw if os.path.isabs(raw) else os.path.join(os.getcwd(), raw)
            if name == "admit":
                admitted.add(inside(Path(os.path.normpath(written))) or written)
                continue
            if Path(os.path.normpath(written)).is_relative_to(zone):
                found.append((name, raw))
                continue
            if self._followed(Path(written), follows, inside, admitted):
                found.append((name, raw))
        return found

    @staticmethod
    def _followed(
        written: Path,
        follows: bool,
        inside: Callable[[Path], str | None],
        admitted: set[str],
    ) -> bool:
        """Whether reading ``written`` follows a forbidden link (see :meth:`violations`).

        Uses the unpatched ``lstat`` / ``readlink`` only; a component that cannot be read
        ends the reading, as the system's lookup ends there.
        """
        position = Path(written.anchor)
        # (component, origin): origin "covered" = from an admitted link's text, "alias" =
        # from a link's text outside the release root.
        pending: list[tuple[str, str]] = [(part, "") for part in reversed(written.parts[1:])]
        hops = 0
        while pending:
            part, origin = pending.pop()
            if part in {"", "."}:
                continue
            if part == "..":
                position = position.parent
                continue
            step = position / part
            if origin == "alias" and inside(step) is not None:
                return True  # an outside link whose text leads under the release root
            if not pending and not follows:
                return False  # the final component is not followed
            try:
                mode = _REAL_FS["lstat"](step).st_mode
            except OSError:
                return False
            if not (stat.S_ISLNK(mode) or os.path.isjunction(step)):
                position = step
                continue
            relative = inside(step)
            if relative is not None and origin != "covered" and relative not in admitted:
                return True
            hops += 1
            if hops > 40:
                return False  # a loop: the system gives up too
            target = _REAL_FS["readlink"](step)
            for prefix in ("\\\\?\\", "\\??\\"):
                target = target.removeprefix(prefix)
            text_ = Path(target)
            tag = "covered" if relative is not None else "alias"
            if origin == "covered":
                tag = "covered"
            if text_.is_absolute():
                position = Path(text_.anchor)
                parts = text_.parts[1:]
            else:
                position = step.parent
                parts = text_.parts
            pending.extend((piece, tag) for piece in reversed(parts))
        return False


def _shape_out_and_back(tmp_path: Path) -> tuple[Path, list[str], set[str]]:
    folder, _ = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/pkg/data"],
        [
            ("Contents/Resources/data", "../Frameworks/data", False),
            ("Contents/Frameworks/data", "../../../outside/back/data", False),
        ],
    )
    outside_alias(folder, "back")
    return folder, ["Contents/Resources/data", "Contents/Frameworks/data"], set()


def _shape_nested_evil(tmp_path: Path) -> tuple[Path, list[str], set[str]]:
    folder, _ = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/pkg/data"],
        [
            ("Contents/Resources/pkg", "../Frameworks/pkg", True),
            ("Contents/Frameworks/pkg/evil", "../../../../outside/back/data", False),
        ],
    )
    outside_alias(folder, "back")
    # The folder cross-link is admitted by its own walk; only evil, under it, is refused.
    return (
        folder,
        ["Contents/Resources/pkg", "Contents/Frameworks/pkg/evil"],
        {"Contents/Resources/pkg"},
    )


def _shape_linked_contents(tmp_path: Path) -> tuple[Path, list[str], set[str]]:
    folder = tmp_path / "wrapper" / "Clearwater.app"
    folder.mkdir(parents=True)
    payload = tmp_path / "wrapper" / "outside" / "payload"
    tree(payload, ["MacOS/Clearwater"], b"bootloader stand-in")
    tree(payload, ["Frameworks/data"], LINK_BLOB)
    _symlink(payload.parent / "back", os.path.join("..", "payload"), folder=True)
    _symlink(folder / "Contents", "../outside/back", folder=True)
    return folder, ["Contents"], set()


LINK_SHAPES = {
    "r11-out-and-back": _shape_out_and_back,
    "r13-nested-evil": _shape_nested_evil,
    "r13-linked-contents": _shape_linked_contents,
}


def _recorded_entry_points(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, folder: Path, links: list[str], path: str
) -> tuple[_FsRecorder, list[str], list[str | None]]:
    """The public entry points on a ``.app`` under the recorder: the origin check (with
    ``original_path=path``), the release ZIP (which must refuse) and the shared rule on each
    link, plus the content check. The bootloader comparison and ``read_package`` are stubs
    that record an ``open``."""
    executable = folder / "Contents/MacOS/Clearwater"
    contents = folder / "Contents/Frameworks"
    empty = tmp_path / "python"
    empty.mkdir()
    recorder = _FsRecorder()

    def opener(result: Any) -> Any:
        def opened(path: Path) -> Any:  # the real ones read the file
            recorder.note("open", path, True)
            return result

        return opened

    monkeypatch.setattr(build.sys, "base_prefix", str(empty))
    monkeypatch.setattr(build, "_locked_native_distributions", lambda: [])
    monkeypatch.setattr(build, "_is_clearwater_bootloader", opener(True))
    monkeypatch.setattr(build, "read_package", opener(SimpleNamespace(toc={})))
    monkeypatch.setattr(build.sys, "platform", "darwin")
    trusted = {hashlib.sha256(LINK_BLOB).hexdigest()}
    with pytest.MonkeyPatch.context() as patch:
        recorder.install(patch)
        found = build.native_origin_violations(
            executable, original_path=path, ffmpeg_hashes=trusted
        )
        with pytest.raises(ValueError, match="release ZIP refuses linked/junction/outside"):
            build.write_release_zip(folder, out=tmp_path / "out", source_epoch=1793908801)
        problems = [build.macos_link_problem(folder, contents, folder / link) for link in links]
        assert app_content_paths(folder, folder)
    return recorder, found, problems


@pytest.mark.parametrize("shape", sorted(LINK_SHAPES))
def test_no_following_call_before_the_walk_admits_the_links(tmp_path, monkeypatch, shape):
    """A r13 / A r14 #2: the public entry points (the origin check, the release ZIP, the
    shared rule, content check) under the recorder (:class:`_FsRecorder`), on the COVERED
    SHAPES: r11's out-and-back, r13's nested ``pkg/evil`` (the folder cross-link admitted) and r13's
    linked ``Contents``; A r14's linked PATH directory is
    :func:`test_a_linked_path_candidate_is_never_followed`. Each refuses; no call FOLLOWS a
    path under the release root through a link before the walk's admission of that link
    (in the recorded order), and none touches the outside alias. The walk admits exactly the
    shape's admitted links. Evidence for these shapes, not a proof of every following call.
    The notices inventory is onedir-only (it requires ``_internal``), so it never
    enumerates a ``.app``. The run-4 content-only shape (Frameworks extensions and Resources
    mirror links) is :func:`test_run4_content_recorder_on_extensions_and_resource_mirrors`."""
    folder, links, admitted = LINK_SHAPES[shape](tmp_path)
    zone = tmp_path / "wrapper" / "outside"
    executable = folder / "Contents/MacOS/Clearwater"
    recorder, found, problems = _recorded_entry_points(tmp_path, monkeypatch, folder, links, "")
    assert found and all(line.startswith("native origin: ") for line in found), found
    assert all(problem is not None for problem in problems), problems
    assert recorder.calls
    assert set(recorder.admitted(folder)) == admitted
    assert recorder.violations(folder, zone) == []
    if shape == "r13-linked-contents":
        assert problems == ["link chain meets a linked boundary: Contents -> '../outside/back'"]
        assert found == [
            f"native origin: {executable} lies behind a link in the bundle; not read",
            f"native origin: linked file {folder / 'Contents'}: {problems[0]}",
        ]
        assert not [
            call
            for call in recorder.calls
            if call[0] in _OPENS and Path(call[1]).is_relative_to(folder)
        ]


_OPENS = {"open", "io.open", "os.open", "Path.open"}


@pytest.mark.parametrize(
    "case",
    [
        "linked-only",
        "linked-then-host",
        "through-dotdot",
        "host-alias-into-bundle",
        "host-link-elsewhere",
    ],
)
def test_a_linked_path_candidate_is_never_followed(tmp_path, monkeypatch, case):
    """A r14 #1 and its residual: the origin check's diagnostic PATH lookup (``likely PATH
    source``) never follows a link. A's shape: an unknown native ``Contents/Aaa.dylib`` met
    before ``Contents/Resources/bin -> ../../../outside/bin``. A candidate with a link
    ANYWHERE on its path is skipped unresolved: the linked folder (as written, or through
    ``..`` past the link), a host alias leading into the bundle
    (``<tmp>/alias -> <root>/Contents/Resources``, then ``<tmp>/alias/bin``) and a host link
    that does not. A physical host PATH entry holding the file is still queried and named
    (built under ``realpath(tmp_path)``: macOS's ``$TMPDIR`` lies under the ``/var``
    link). The bundle link itself is refused exactly as before."""
    folder, _ = link_release(
        tmp_path, "app", [], [("Contents/Resources/bin", "../../../outside/bin", True)]
    )
    tree(folder, ["Contents/Aaa.dylib"], b"payload")
    tree(folder.parent, ["outside/bin/Aaa.dylib"], b"unknown")
    real = Path(os.path.realpath(tmp_path))
    host = tree(real / "host" / "bin", ["Aaa.dylib"], b"unknown")
    alias = real / "alias"
    _symlink(alias, str(Path(os.path.realpath(folder)) / "Contents" / "Resources"), folder=True)
    hostlink = real / "hostlink"
    _symlink(hostlink, str(host), folder=True)
    assert (hostlink / "Aaa.dylib").is_file()
    linked = folder / "Contents/Resources/bin"
    entries = {
        "linked-only": [linked],
        "linked-then-host": [linked, host],
        "through-dotdot": [linked / ".." / "bin"],
        "host-alias-into-bundle": [alias / "bin"],
        "host-link-elsewhere": [hostlink],
    }[case]
    recorder, found, problems = _recorded_entry_points(
        tmp_path,
        monkeypatch,
        folder,
        ["Contents/Resources/bin"],
        os.pathsep.join(str(entry) for entry in entries),
    )
    heading = Path(os.path.realpath(folder.parent)) / "outside" / "bin"
    refusal = (
        f"link chain leaves the bundle: Contents/Resources/bin -> '../../../outside/bin'; {heading}"
    )
    source = f"; likely PATH source: {host / 'Aaa.dylib'}" if case == "linked-then-host" else ""
    assert problems == [refusal]
    assert found == [
        f"native origin unknown: Contents/Aaa.dylib{source}",
        f"native origin: linked file {linked}: {refusal}",
    ]
    assert recorder.admitted(folder) == []
    assert recorder.violations(folder, tmp_path / "wrapper" / "outside") == []
    if case == "linked-then-host":
        assert ("Path.is_file", str(host / "Aaa.dylib"), True) in recorder.calls
    for watched in (alias, hostlink):
        through = [
            call for call in recorder.calls if call[2] and Path(call[1]).is_relative_to(watched)
        ]
        assert through == [], through


def test_a_path_candidate_with_any_link_on_it_is_skipped(tmp_path):
    """A r14 #1 and its residual: a PATH candidate counts as linked when a link or junction
    lies ANYWHERE on its path, read as written from the anchor by ``lstat`` alone: in the
    bundle, through ``..`` past it, through an alias above the release root, or through a
    host link outside it. A physical path (built under ``realpath(tmp_path)``), a missing
    component and an absent host folder are not."""
    folder, _ = link_release(
        tmp_path, "app", [], [("Contents/Resources/bin", "../../../outside/bin", True)]
    )
    real = Path(os.path.realpath(folder))
    alias = Path(os.path.realpath(tmp_path)) / "alias"
    _symlink(alias, str(real.parent), folder=True)
    behind = build._macos_candidate_behind_a_link
    linked = "Contents/Resources/bin/Aaa.dylib"
    assert behind(real / linked)
    assert behind(real / "Contents/Resources/bin/../bin/Aaa.dylib")
    # Out through the link and lexically back outside: still found at the link.
    assert behind(real / "Contents/Resources/bin/../../../../host/Aaa.dylib")
    assert behind(alias / "Clearwater.app/Contents/MacOS/Aaa.dylib")  # an alias above the root
    if os.path.exists(str(real).upper()):  # a case-insensitive volume (macOS, Windows)
        assert behind(Path(str(real / linked).upper()))
    try:
        relative = Path(os.path.relpath(real / linked))
    except ValueError:  # another drive than the working folder's
        pass
    else:
        assert not relative.is_absolute() and behind(relative)
    assert not behind(real / "Contents/MacOS/Aaa.dylib")
    assert not behind(real / "Contents/Missing/bin/Aaa.dylib")
    assert not behind(real.parent.parent / "host" / "Aaa.dylib")


# --- A r14 #2: the recorder's own three gaps, each shown caught -----------------------------


def test_the_recorder_records_an_ordinary_read(tmp_path):
    """A r14 #2 gap 1: a real read is recorded as a following ``open``, whichever API makes
    it (A's probe was ``Path.read_bytes()``, invisible to the A r13 recorder)."""
    path = tree(tmp_path, ["data.bin"], b"payload") / "data.bin"
    reads = {
        "Path.read_bytes": lambda: path.read_bytes(),
        "Path.read_text": lambda: path.read_text(encoding="ascii"),
        "builtins.open": lambda: builtins.open(path, "rb").close(),
        "io.open": lambda: io.open(path, "rb").close(),  # noqa: UP020 (io.open itself)
        "os.open": lambda: os.close(os.open(path, os.O_RDONLY)),
    }
    for api, read in reads.items():
        recorder = _FsRecorder()
        with pytest.MonkeyPatch.context() as patch:
            recorder.install(patch)
            read()
        opens = [call for call in recorder.calls if call[0] in _OPENS]
        assert opens and all(call[1:] == (str(path), True) for call in opens), (api, opens)


def test_the_recorder_orders_admission_events(tmp_path):
    """A r14 #2 gap 2: a following call through a link BEFORE the walk admits it is a
    violation, though the link is admitted later; after the admission it is not."""
    folder, _ = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/pkg/data"],
        [("Contents/Resources/pkg", "../Frameworks/pkg", True)],
    )
    link = str(folder / "Contents/Resources/pkg")
    zone = tmp_path / "wrapper" / "outside"
    recorder = _FsRecorder()
    recorder.calls = [("realpath", link, True), ("admit", link, False)]
    assert recorder.violations(folder, zone) == [("realpath", link)]
    recorder.calls.reverse()
    assert recorder.violations(folder, zone) == []
    assert recorder.admitted(folder) == ["Contents/Resources/pkg"]


def test_the_recorder_records_the_walks_admissions(tmp_path):
    """A r14 #2 gap 2: the admission events come from the component walk itself, in the
    sequence of the filesystem calls, after the walk's own calls."""
    folder, _ = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/pkg/data"],
        [("Contents/Resources/pkg", "../Frameworks/pkg", True)],
    )
    recorder = _FsRecorder()
    with pytest.MonkeyPatch.context() as patch:
        recorder.install(patch)
        problem = build.macos_link_problem(
            folder, folder / "Contents/Frameworks", folder / "Contents/Resources/pkg"
        )
    assert problem is None
    names = [call[0] for call in recorder.calls]
    assert names.count("admit") == 1
    assert names.index("admit") > names.index("readlink")
    assert recorder.admitted(folder) == ["Contents/Resources/pkg"]
    assert recorder.violations(folder, tmp_path / "wrapper" / "outside") == []


@pytest.mark.parametrize("kind", ["modeled", "real"])
def test_the_recorder_sees_a_junction_as_a_link(tmp_path, monkeypatch, kind):
    """A r14 #2 gap 3: a directory junction on a followed path is a link (A's modeled
    ``Contents/MacOS`` junction, and a real one where the host makes junctions)."""
    folder = tmp_path / "wrapper" / "Clearwater.app"
    executable = folder / "Contents/MacOS/Clearwater"
    if kind == "modeled":
        tree(executable.parent, [executable.name], b"bootloader stand-in")
        # Both spellings: the checker reads the physical path (macOS /var -> /private/var).
        junctions = {executable.parent, Path(os.path.realpath(executable.parent))}
        real = os.path.isjunction
        monkeypatch.setattr(os.path, "isjunction", lambda path: path in junctions or real(path))
    else:
        if sys.platform != "win32":
            pytest.skip("Windows junction regression")
        import _winapi

        target = tree(tmp_path / "elsewhere", ["Clearwater"], b"bootloader stand-in")
        (folder / "Contents").mkdir(parents=True)
        _winapi.CreateJunction(str(target), str(executable.parent))
    recorder = _FsRecorder()
    recorder.calls = [("open", str(executable), True)]
    assert recorder.violations(folder, tmp_path / "wrapper" / "outside") == [
        ("open", str(executable))
    ]


# --- A r15: the recorder's reading of a path, three more gaps -------------------------------


def _pkg_release(tmp_path: Path) -> tuple[Path, Path]:
    """A ``.app`` with the folder link ``Contents/Resources/pkg -> ../Frameworks/pkg``."""
    folder, _ = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/pkg/data"],
        [("Contents/Resources/pkg", "../Frameworks/pkg", True)],
    )
    return folder, folder / "Contents/Resources/pkg"


def test_the_recorder_reads_a_relative_path_from_the_working_folder(tmp_path, monkeypatch):
    """A r15 #1: a relative followed path through an unadmitted link is a violation (A's
    probe: the working folder beside the ``.app``), and a relative call is recorded joined
    to the working folder of the moment."""
    folder, _ = _pkg_release(tmp_path)
    monkeypatch.chdir(folder.parent)
    relative = os.path.join("Clearwater.app", "Contents", "Resources", "pkg", "data")
    recorder = _FsRecorder()
    recorder.calls = [("open", relative, True)]
    assert recorder.violations(folder, tmp_path / "wrapper" / "outside") == [("open", relative)]
    recorder = _FsRecorder()
    with pytest.MonkeyPatch.context() as patch:
        recorder.install(patch)
        os.lstat("Clearwater.app")
    assert recorder.calls == [("lstat", os.path.join(os.getcwd(), "Clearwater.app"), False)]


def test_the_recorder_reads_on_from_an_allowed_alias_physical_target(tmp_path):
    """A r15 #2: an alias ABOVE the release root is allowed, and the components after it are
    read at its physical target, so an unadmitted bundle link behind it is still caught
    (A's probe: ``alias -> <wrapper>``, then ``Contents/Resources/bin``)."""
    folder, _ = link_release(
        tmp_path, "app", [], [("Contents/Resources/bin", "../../../outside/bin", True)]
    )
    tree(folder.parent, ["outside/bin/data"], b"payload")
    alias = Path(os.path.realpath(tmp_path)) / "alias"
    _symlink(alias, str(Path(os.path.realpath(folder.parent))), folder=True)
    through = str(alias / "Clearwater.app/Contents/Resources/bin/data")
    physical = str(alias / "Clearwater.app/Contents/MacOS/Clearwater")
    recorder = _FsRecorder()
    recorder.calls = [("open", through, True), ("open", physical, True)]
    assert recorder.violations(folder, tmp_path / "wrapper" / "outside") == [("open", through)]


def test_the_recorder_checks_the_ancestors_of_a_non_following_call(tmp_path, monkeypatch):
    """A r15 #3: ``O_NOFOLLOW`` (like ``lstat``) spares only the FINAL component; an
    ancestor link is still followed. Modeled flags and a stubbed open backend (A's probe);
    ``lstat`` of the link itself follows nothing."""
    folder, link = _pkg_release(tmp_path)
    monkeypatch.setattr(os, "O_NOFOLLOW", getattr(os, "O_NOFOLLOW", 0x20000), raising=False)
    monkeypatch.setitem(_REAL_FS, "os.open", lambda *args, **kwargs: 7)
    target = str(link / "data")
    recorder = _FsRecorder()
    with pytest.MonkeyPatch.context() as patch:
        recorder.install(patch)
        assert os.open(target, os.O_RDONLY | os.O_NOFOLLOW) == 7
    assert recorder.calls == [("os.open", target, False)]
    recorder.calls += [("lstat", target, False), ("lstat", str(link), False)]
    assert recorder.violations(folder, tmp_path / "wrapper" / "outside") == [
        ("os.open", target),
        ("lstat", target),
    ]


@pytest.mark.parametrize("kind", ["link", "junction"])
def test_a_linked_contents_boundary_is_refused_by_its_text(tmp_path, kind):
    """A r13 #2: a ``Contents`` that is a link (or junction) is refused without resolving it,
    naming Contents and its text; an alias above the release root stays untouched (above)."""
    folder = tmp_path / "wrapper" / "Clearwater.app"
    folder.mkdir(parents=True)
    target = tree(tmp_path / "elsewhere", ["Frameworks/data"], LINK_BLOB)
    if kind == "link":
        _symlink(folder / "Contents", "../elsewhere", folder=True)
        expected = "link chain meets a linked boundary: Contents -> '../elsewhere'"
    else:
        if sys.platform != "win32":
            pytest.skip("Windows junction regression")
        import _winapi

        _winapi.CreateJunction(str(target), str(folder / "Contents"))
        expected = "junction"  # the rule's first check, before any walk
        # A link reached through the junction is refused at the boundary, unresolved.
        _symlink(target / "Frameworks/lnk", "data", folder=False)
        assert build._macos_link_chain_problem(folder, folder / "Contents/Frameworks/lnk") == (
            "link chain meets a linked boundary: Contents (junction)"
        )
    problem = build.macos_link_problem(folder, folder / "Contents/Frameworks", folder / "Contents")
    assert problem == expected


def test_the_app_listing_never_follows_and_matches_the_walk(tmp_path):
    """A r13 #1: the .app listing classifies a link before any folder query; on a physical
    tree it lists exactly what the onedir ``os.walk`` lists (files, links, no folders)."""
    folder, _ = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/pkg/data", "Contents/Resources/x.txt"],
        [
            ("Contents/Resources/pkg", "../Frameworks/pkg", True),
            ("Contents/Frameworks/data", "pkg/data", False),
        ],
    )
    assert build._macos_entries(folder) == build._macos_entries(folder, in_app=False)
    kinds = {
        path.relative_to(folder).as_posix(): kind for path, kind in build._macos_entries(folder)
    }
    assert kinds == {
        "Contents/Frameworks/data": "link",
        "Contents/Frameworks/pkg/data": "file",
        "Contents/MacOS/Clearwater": "file",
        "Contents/Resources/pkg": "link",
        "Contents/Resources/x.txt": "file",
    }


def test_a_folder_link_that_leaves_and_comes_back_is_refused(tmp_path):
    """A folder link in mid-path whose target leaves Contents is refused before it returns."""
    folder, _ = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/pkg/x.dylib"],
        [
            ("Contents/Resources/x.dylib", "../Frameworks/F/x.dylib", False),
            ("Contents/Frameworks/F", "../../../outside/back", True),
        ],
    )
    assert (outside_alias(folder, "back") / "x.dylib").is_file()
    heading = Path(os.path.realpath(folder.parent)) / "outside" / "back" / "x.dylib"
    problem = build.macos_link_problem(
        folder, folder / "Contents/Frameworks", folder / "Contents/Resources/x.dylib"
    )
    assert problem == (
        "link chain leaves the bundle: Contents/Resources/x.dylib -> '../Frameworks/F/x.dylib'; "
        f"Contents/Frameworks/F -> '../../../outside/back'; {heading}"
    )


def test_a_single_hop_that_steps_out_of_contents_and_back_is_refused(tmp_path):
    """No link outside at all: the hop's own ``..`` above Contents refuses at that point."""
    folder, _ = link_release(
        tmp_path,
        "app",
        ["Contents/Frameworks/y.dylib"],
        [("Contents/Resources/y.dylib", "../../Contents/Frameworks/y.dylib", False)],
    )
    problem = build.macos_link_problem(
        folder, folder / "Contents/Frameworks", folder / "Contents/Resources/y.dylib"
    )
    assert problem == (
        "link chain leaves the bundle: "
        "Contents/Resources/y.dylib -> '../../Contents/Frameworks/y.dylib'; "
        "Contents/Frameworks/y.dylib"
    )


@pytest.mark.parametrize("met", [8, 9])
def test_folder_links_count_against_the_hop_bound(tmp_path, met):
    """Five file hops through four folder links are nine links: refused; eight are admitted."""
    links = [("Contents/Frameworks/c0", "f1/c1", False)]
    links += [(f"Contents/Frameworks/f{index}", "lib", True) for index in range(1, 5)]
    links += [
        (f"Contents/Frameworks/lib/c{index}", f"../f{index + 1}/c{index + 1}", False)
        for index in range(1, 3)
    ]
    if met == 9:
        links += [
            ("Contents/Frameworks/lib/c3", "../f4/c4", False),
            ("Contents/Frameworks/lib/c4", "data.bin", False),
        ]
    else:
        links.append(("Contents/Frameworks/lib/c3", "../f4/data.bin", False))
    folder, _ = link_release(tmp_path, "app", ["Contents/Frameworks/lib/data.bin"], links)
    problem = build.macos_link_problem(
        folder, folder / "Contents/Frameworks", folder / "Contents/Frameworks/c0"
    )
    if met == 8:
        assert problem is None
        return
    shown = ["Contents/Frameworks/c0 -> 'f1/c1'"]
    for index in range(1, 4):
        shown.append(f"Contents/Frameworks/f{index} -> 'lib'")
        shown.append(f"Contents/Frameworks/lib/c{index} -> '../f{index + 1}/c{index + 1}'")
    shown += ["Contents/Frameworks/f4 -> 'lib'", "Contents/Frameworks/lib/c4"]
    assert problem == "link chain is longer than 8 hops: " + "; ".join(shown)


def test_an_alias_above_the_release_root_is_untouched(tmp_path, monkeypatch):
    """The boundary is canonicalised once: a release root named through a link above it
    (macOS ``/var`` -> ``/private/var``) still admits the PyInstaller chain and a plain hop.

    The chain is checked through the walk itself: on a Windows host ``realpath`` cannot
    follow a POSIX-text file link under an alias (the host, not the rule), so the whole
    rule and the origin walk take the single-hop cross-link, which needs no such follow.
    """
    _, files, links, _ = LINK_CASES["C-app-pyinstaller-chain"]
    _, more, plain, _ = LINK_CASES["C-data-file-cross-link"]
    link_release(tmp_path / "real", "app", [*files, *more], [*links, *plain])
    _symlink(tmp_path / "alias", "real", folder=True)
    folder = tmp_path / "alias/wrapper/Clearwater.app"
    for path, _, _ in links:
        assert build._macos_link_chain_problem(folder, folder / path) is None
    (hop, _, _) = plain[0]
    assert build._macos_link_chain_problem(folder, folder / hop) is None
    contents = folder / "Contents/Frameworks"
    assert build.macos_link_problem(folder, contents, folder / hop) is None
    for path, _, _ in links:  # the chain, removed so the origin walk sees the plain hop only
        (tmp_path / "real/wrapper/Clearwater.app" / path).unlink()
    assert link_origin_check(tmp_path, monkeypatch, folder / "Contents/MacOS/Clearwater") == []


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


def test_run4_content_printer_keeps_all_violations_in_runner_log(tmp_path, monkeypatch, capsys):
    """The runner tees stdout to build.log; the macOS list must not stop at 50."""
    bad = [f"dist:Clearwater.app/Contents/Frameworks/cupy/bad{i:03}.so" for i in range(115)]
    monkeypatch.delenv("PYTHONPATH", raising=False)
    monkeypatch.setattr(build, "REPO_ROOT", REPO_ROOT)
    monkeypatch.setattr(build, "forbidden_entries", lambda _: bad)
    status, _ = darwin_app_build(
        monkeypatch, tmp_path, seal=lambda _: None, origin=lambda *a, **kw: []
    )
    printed = capsys.readouterr().out
    assert status == 1
    assert "FORBIDDEN in the bundle (115):" in printed
    assert all(f"  {name}\n" in printed for name in bad)


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
        "--disable-encoder='aac,libx265'",  # configure prints a list quoted (sh_quote)
        "--disable-encoder='libx26*'",
        "--disable-encoder='aac|libx265'",
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


@pytest.mark.parametrize(
    "change",
    [
        "--disable-encoder=aac",
        "--disable-encoder='aac,mp3'",
        "--disable-encoder=libx265_encoder",  # configure: libx265_encoder_encoder, no match
        "--disable-encoder=LIBX265",  # case patterns are case-sensitive
        "--disable-libx264",
        "--disable-doc",
    ],
)
def test_macos_lock_admits_a_disable_that_leaves_the_required_set_on(change):
    """The rule is about the required switches and the libx265 encoder, not every disable:
    a literal encoder list not naming ``libx265`` is admitted."""
    data = macos_lock()
    _configure(data, change)
    assert build.validate_ffmpeg_lock(data, platform="darwin") is data


def _sh_quote(value: str) -> str:
    """FFmpeg configure's ``sh_quote``: as is when every byte is in [A-Za-z0-9_/.+-]."""
    escaped = value.replace("'", "'\\''")
    return escaped if re.fullmatch(r"[A-Za-z0-9_/.+-]*", escaped) else f"'{escaped}'"


A4_F1_PATTERNS = [
    "libx265_encoder|aac",  # the reviewer's: configure builds libx265_encoder|aac_encoder
    "libx26[[:digit:]]",  # the reviewer's: a POSIX class fnmatch does not know
    "libx265|aac",  # the reviewer's reverse case (no match in configure): REFUSED as intended
    "[[:digit:]]",
    "libx26?",
    "*265*",
    "\\l\\i\\b\\x\\2\\6\\5",
]


@pytest.mark.parametrize("pattern", A4_F1_PATTERNS)
@pytest.mark.parametrize("form", ["printed", "bare"])
def test_macos_lock_refuses_an_encoder_pattern_whose_effect_is_not_literal(pattern, form):
    """A4-F1: configure turns ``--disable-encoder=<value>`` into ONE shell ``case`` pattern
    (``,`` -> ``_encoder|``, then ``_encoder`` appended once) and evals it; its effect is
    not reproduced: any value that is not a literal list of names is REFUSED, including
    patterns that would not match ``libx265_encoder`` (the conservative rule). In the
    printed (sh-quoted) form the encoder rule refuses it; bare, it is not configure's
    printed form at all."""
    data = macos_lock()
    value = _sh_quote(pattern) if form == "printed" else pattern
    _configure(data, f"--disable-encoder={value}")
    match = "disabled" if form == "printed" else "disabled|printed form"
    with pytest.raises(ValueError, match=match):
        build.validate_ffmpeg_lock(data, platform="darwin")


def test_macos_lock_refuses_every_non_literal_byte_in_an_encoder_list():
    """A4-F1's class: every printable byte other than a name byte or ``,`` (each pattern
    metacharacter, quote, space and the rest), in the printed form, at each position."""
    names = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_,")
    admitted = []
    for byte in range(0x20, 0x7F):
        char = chr(byte)
        if char in names:
            continue
        for value in (f"aac{char}", f"{char}aac", f"aac{char}mp3", char):
            data = macos_lock()
            _configure(data, "--disable-encoder=" + _sh_quote(value))
            try:
                build.validate_ffmpeg_lock(data, platform="darwin")
            except ValueError:
                continue
            admitted.append(value)
    assert admitted == []


@pytest.mark.parametrize(
    "value", ["libx265", "aac,libx265", "libx265,aac", "aac,libx265,mp3", "", "aac,,mp3", ",aac"]
)
def test_macos_lock_refuses_a_literal_list_naming_libx265_or_an_empty_item(value):
    """A literal list reaches ``libx265_encoder`` only through the item ``libx265``; an
    empty item is not a literal name (refused). The empty value is printed bare
    (``sh_quote`` leaves an empty string unquoted)."""
    data = macos_lock()
    _configure(data, "--disable-encoder=" + _sh_quote(value))
    with pytest.raises(ValueError, match="disabled"):
        build.validate_ffmpeg_lock(data, platform="darwin")


@pytest.mark.parametrize(
    "change",
    [
        "--disable-encoder=aac,mp3",  # configure would print the list quoted
        "--extra-cflags=-O2 -g",  # a space outside quotes splits it into two arguments
        "'--disable-libx265 '",  # a quoted option name: configure's eval strips the space
        "'--disable-encoders'",
        "--extra-cflags='-O2",  # unbalanced quote
        "--extra-cflags='a'b'",
        "--extra-cflags=\t-O2",
        "--enable-libass\t--disable-libx265",
        "",  # a trailing space: an empty argument
        "--en'able'-gpl",
    ],
)
def test_macos_lock_refuses_a_line_that_is_not_configures_printed_form(change):
    """A4-F1's neighbour: the rules judge configure's PRINTED arguments (``l`` as given,
    the value after the first ``=`` through ``sh_quote``, joined by single spaces). A line
    not in that form could hide an option from them (``'--disable-libx265 '`` disables
    libx265: configure's ``eval`` drops the space), so it is refused."""
    data = macos_lock()
    _configure(data, change)
    with pytest.raises(ValueError, match="printed form"):
        build.validate_ffmpeg_lock(data, platform="darwin")


@pytest.mark.parametrize(
    "change",
    [
        "--extra-cflags='-I/Users/José/include'",  # A4-F3's UTF-8 path, quoted as printed
        "--extra-cflags='-DNAME='\\''x'\\'''",  # an embedded quote, sh_quote's escape
        "--extra-ldflags='-L/opt/a b'",
        "--extra-cflags=",
    ],
)
def test_macos_lock_admits_the_printed_quoting_forms(change):
    data = macos_lock()
    _configure(data, change)
    assert build.validate_ffmpeg_lock(data, platform="darwin") is data


A5_REDUNDANT_QUOTES = [
    ("--extra-version=20261110", "--extra-version='20261110'"),  # the reviewer's
    ("--extra-version=20261110", "extra-version='20261110'"),
    ("--extra-version=20261110", "extra_version='20261110'"),
    ("--extra-version=20261110", "--extra_version='20261110'"),
    ("--pkg-config-flags=--static", "--pkg-config-flags='--static'"),
    ("--prefix=/Users/", "--prefix='/Users/"),  # the whole prefix value quoted (below)
    ("append", "--disable-encoder='aac'"),  # the reviewer's
    ("append", "--disable-encoder='aac_at'"),
    ("append", "--extra-cflags=''"),  # sh_quote prints an empty value bare
    ("append", "--extra-cflags='-O2'"),
]


@pytest.mark.parametrize(("spelling", "quoted"), A5_REDUNDANT_QUOTES)
def test_macos_lock_refuses_quoting_configure_would_not_print(spelling, quoted):
    """A r5 minor: configure quotes a value only when ``sh_quote`` must (a byte outside
    ``[A-Za-z0-9_/.+-]``), so a quoted value that would print bare is not the printed form
    and is refused; each admitted option in the fixture's line and the admitted appended
    forms, given redundant quotes. (Every one was ACCEPTED at ``87df4840``.)"""
    data = macos_lock()
    line = data["configure_line"]
    if spelling == "append":
        data["configure_line"] = line + " " + quoted
    elif spelling == "--prefix=/Users/":
        start = line.index(spelling)
        end = line.index(" ", start)
        value = line[start + len("--prefix=") : end]
        assert _sh_quote(value) == value  # the fixture prints it bare
        data["configure_line"] = line[:start] + f"--prefix='{value}'" + line[end:]
    else:
        assert line.count(spelling) == 1
        data["configure_line"] = line.replace(spelling, quoted)
    with pytest.raises(ValueError, match="printed form"):
        build.validate_ffmpeg_lock(data, platform="darwin")


def test_macos_lock_admits_exactly_sh_quote_s_spelling_of_each_value():
    """The positive side of the canonical-quoting rule: for values that need quoting
    (a UTF-8 byte, a space, a quote, a comma) and values that do not, the ``sh_quote``
    spelling is admitted and the other spelling refused."""
    for value in ["-I/Users/José/include", "-L/opt/a b", "-DNAME='x'", "a,b", "-O2", ""]:
        printed = _sh_quote(value)
        other = value if printed != value else "'" + value.replace("'", "'\\''") + "'"
        data = macos_lock()
        _configure(data, f"--extra-cflags={printed}")
        assert build.validate_ffmpeg_lock(data, platform="darwin") is data, printed
        if value == "-L/opt/a b":
            continue  # bare, it is two printed arguments (the stated limit), not one
        data = macos_lock()
        _configure(data, f"--extra-cflags={other}")
        with pytest.raises(ValueError, match="printed form"):
            build.validate_ffmpeg_lock(data, platform="darwin")


@pytest.mark.parametrize(
    "change",
    [
        "extra-version=20261110",
        "extra_version=20261111",
        "--extra_version=20261111",
        "--extra-version=20261110",
    ],
)
def test_macos_lock_counts_every_spelling_of_extra_version(change):
    """configure's ``*)`` branch takes ``[--]name=value`` with ``-`` and ``_`` alike, so each
    spelling sets ``extra_version`` (the last one wins): exactly one is admitted."""
    data = macos_lock()
    _configure(data, change)
    with pytest.raises(ValueError, match="--extra-version"):
        build.validate_ffmpeg_lock(data, platform="darwin")


def test_macos_lock_admits_the_recipes_own_configure_line():
    """The patch's configure call (``build-ffmpeg.sh``) with the recipe's enables, printed
    as configure prints it: the fixture's line, rebuilt from the patch, is admitted."""
    patch = MACOS_FORK_PATCH.read_text(encoding="utf-8")
    assert '+./configure --prefix="$OUT_DIR" --pkg-config-flags="--static" ' in patch
    data = macos_lock()
    body = data["configure_line"].removeprefix("configuration: ")
    assert body.startswith("--prefix=") and "'" not in body
    for switch in body.split():
        if switch.startswith("--enable-"):
            assert f" {switch}" in patch or f'"{switch} ' in patch, switch
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
        ("census", "complete", "census must be pending or a complete census object"),
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


# --- WP6.5 part 3b: the macOS lock's complete census -------------------------------------

MACOS_FLAGS = {
    "fontconfig": ["--enable-fontconfig"],
    "freetype": ["--enable-libfreetype"],
    "harfbuzz": ["--enable-libharfbuzz"],
    "libass": ["--enable-libass"],
    "libxml2": ["--enable-libxml2"],
    "openssl": ["--enable-openssl"],
    "x264": ["--enable-libx264"],
    "x265": ["--enable-libx265"],
}
"""The configure switch each component answers in the recipe's line (the rest: null)."""

APPLE_CLANG = "Apple clang version 21.0.0 (clang-2100.1.1.101)"


def macos_text(folder: Path, name: str, body: bytes | None = None) -> dict[str, str]:
    """Write ``<name>--COPYING`` into ``folder``; its text record (member in a tarball)."""
    body = f"{name} synthetic licence text\n".encode() if body is None else body
    (folder / f"{name}--COPYING").write_bytes(body)
    return {
        "path": f"{name}--COPYING",
        "sha256": hashlib.sha256(body).hexdigest(),
        "member": f"{name}-1.0/COPYING",
    }


def complete_macos_lock(folder: Path) -> dict[str, Any]:
    """The fixture with a SYNTHETIC complete census; its texts are written to ``folder``."""
    data = macos_lock()
    folder.mkdir(parents=True, exist_ok=True)
    components = []
    for name in sorted(build.FFMPEG_MACOS_COMPONENTS):
        row: dict[str, Any] = {
            "stage": f"build-{name}",
            "name": name,
            "repository": f"https://example.org/{name}-1.0.tar.gz",
            "pin": hashlib.sha256(name.encode()).hexdigest(),
            "pin_kind": "sha256",
            "extra_repositories": [],
            "configure_flag": MACOS_FLAGS.get(name),
            "licence": "MIT",
            "licence_basis": "pinned-source-text",
            "gpl3_compatible": "yes",
            "licence_note": "synthetic",
            "texts": [macos_text(folder, name)],
            "chosen": None,
        }
        if name in build.FFMPEG_MACOS_UNLINKED:
            row["status"] = "built-not-linked"
        components.append(row)
    data["census"] = {
        "state": "complete",
        "job_url": data["build_run_url"] + "/job/1",
        "log": "synthetic",
        "linkage_step": "Check the binaries",
        "linkage_lines": "618-659",
        "version_lines": "660-662",
        "toolchain_step": "Record and check the runner",
        "toolchain_lines": "157-163",
        "external_libraries": "build/logs/build-ffmpeg.log:144-153",
    }
    data["components"] = components
    data["toolchain"] = {
        "compiler": APPLE_CLANG,
        "xcode": "26.6 (17F113)",
        "sdk": "26.5",
        "target": "arm64-apple-darwin25.6.0",
        "deployment_target": "14.0",
        "census_build_commit": data["build_repository_commit"],
        "census_asset_sha256": data["github_sha256"],
    }
    data["toolchain_runtime"] = [
        {
            "name": "Apple clang 21.0.0 (clang-2100.1.1.101), Xcode 26.6, SDK 26.5, "
            "deployment target 14.0",
            "version": "clang-2100.1.1.101",
            "kind": "apple-clang-runtime",
            "reached_via": "toolchain",
            "repository": "https://github.com/llvm/llvm-project",
            "pin": APPLE_CLANG,
            "pin_kind": "toolchain-marker",
            "source_url": "https://github.com/llvm/llvm-project/tree/" + "3" * 40,
            "licence": "Apache-2.0 WITH LLVM-exception",
            "licence_basis": "upstream-text",
            "gpl3_compatible": "yes",
            "licence_note": "synthetic",
            "texts": [macos_text(folder, "llvm-project")],
            "evidence": "synthetic",
            "basis": "toolchain-marker",
            "basis_note": "synthetic",
            "chosen": None,
            "linkage": "inferred",
        }
    ]
    return data


def test_macos_complete_census_validates_against_its_text_folder(tmp_path):
    folder = tmp_path / "texts"
    data = complete_macos_lock(folder)
    assert build.validate_ffmpeg_lock(data, platform="darwin", component_texts_path=folder) is data
    assert set(data["census"]) == set(build.FFmpegMacCensus.__annotations__)
    assert set(data["toolchain"]) == set(build.FFmpegMacToolchain.__annotations__)
    assert set(data["toolchain_runtime"][0]) == set(build.FFmpegMacRuntime.__annotations__)
    assert build.FFMPEG_MACOS_TEXTS_PATH.name == "ffmpeg-macos-components"
    assert build.FFMPEG_MACOS_TEXTS_PATH.parent == build.FFMPEG_COMPONENT_TEXTS_PATH.parent


def test_macos_complete_census_reads_the_macos_text_folder_by_default(tmp_path, monkeypatch):
    """No folder argument: the macOS folder, read at call time (never the Windows one)."""
    folder = tmp_path / "texts"
    data = complete_macos_lock(folder)
    monkeypatch.setattr(build, "FFMPEG_MACOS_TEXTS_PATH", folder)
    assert build.validate_ffmpeg_lock(data, platform="darwin") is data
    monkeypatch.setattr(build, "FFMPEG_MACOS_TEXTS_PATH", tmp_path / "absent")
    with pytest.raises(ValueError, match="macOS text missing/unsafe"):
        build.validate_ffmpeg_lock(data, platform="darwin")


def component(data: dict[str, Any], name: str) -> dict[str, Any]:
    return next(row for row in data["components"] if row["name"] == name)


def change_census(data: dict[str, Any], folder: Path, change: str) -> None:
    """Apply one named damage to a complete census (and its text folder)."""
    zlib, libogg = component(data, "zlib"), component(data, "libogg")
    runtime = data["toolchain_runtime"][0]
    if change == "census-string":
        data["census"] = "complete"
    elif change == "census-state":
        data["census"]["state"] = "partial"
    elif change == "census-field":
        data["census"]["otool"] = "618-659"
    elif change == "census-job":
        data["census"]["job_url"] = "https://github.com/rwsmythe/FFmpeg-Builds/actions/runs/1/job/2"
    elif change == "census-lines":
        data["census"]["version_lines"] = "662-660"
    elif change == "census-libraries":
        data["census"]["external_libraries"] = "build/logs/build-x265.log:1-2"
    elif change == "no-components":
        data["components"] = []
    elif change == "missing-component":
        data["components"].remove(zlib)
    elif change == "invented-component":
        data["components"].append({**zlib, "name": "libvpx", "stage": "build-libvpx"})
    elif change == "duplicate-component":
        data["components"].append(dict(zlib))
    elif change == "stage":
        zlib["stage"] = "scripts.d/20-zlib.sh"
    elif change == "via":
        zlib["via"] = "shaderc git-sync-deps"
    elif change == "http":
        zlib["repository"] = "http://www.zlib.net/fossils/zlib-1.3.2.tar.gz"
    elif change == "pin-kind":
        zlib["pin_kind"] = "tag"
    elif change == "tarball-pin":
        zlib["pin"] = "1.3.2"
    elif change == "commit-pin":
        zlib["pin_kind"] = "commit"
    elif change == "extra-repositories":
        zlib["extra_repositories"] = [{"repository": "https://example.org/x.git"}]
    elif change == "basis":
        zlib["licence_basis"] = "seat-verified"
    elif change == "incompatible":
        zlib["gpl3_compatible"] = "no"
    elif change == "licence":
        zlib["licence"] = "GPL-2.0-only"
    elif change == "chosen":
        zlib["chosen"] = "Apache-2.0"
    elif change == "unlinked-built":
        del libogg["status"]
    elif change == "linked-unlinked":
        zlib["status"] = "built-not-linked"
    elif change == "status-list":
        zlib["status"] = []  # A r6 minor 1: a non-string status was a TypeError
    elif change == "status-dict":
        zlib["status"] = {}
    elif change == "unlinked-flag":
        libogg["configure_flag"] = ["--enable-libogg"]
    elif change == "unmapped":
        component(data, "x265")["configure_flag"] = None
    elif change == "absent":
        zlib["configure_flag"] = ["--enable-zlib"]
    elif change == "twice":
        component(data, "x264")["configure_flag"] = ["--enable-libx264", "--enable-libx265"]
    elif change == "member-parent":
        zlib["texts"][0]["member"] = "../COPYING"
    elif change == "member-absolute":
        zlib["texts"][0]["member"] = "/zlib-1.0/COPYING"
    elif change == "member-backslash":
        zlib["texts"][0]["member"] = "zlib-1.0\\COPYING"
    elif change == "path":
        zlib["texts"][0]["path"] = "zlib/COPYING"
    elif change == "excerpt":
        zlib["texts"][0]["member"] = "zlib-1.0/COPYING#L5-1"
    elif change == "excerpt-name":
        zlib["texts"][0]["member"] = "zlib-1.0/COPYING#L1-5"
    elif change == "text-fields":
        del zlib["texts"][0]["member"]
    elif change == "no-texts":
        zlib["texts"] = []
    elif change == "no-toolchain":
        data["toolchain"] = None
    elif change == "compiler":
        data["toolchain"]["compiler"] = "clang version 21.0.0"
    elif change == "xcode":
        data["toolchain"]["xcode"] = "26.6"
    elif change == "target":
        data["toolchain"]["target"] = "x86_64-apple-darwin25.6.0"
    elif change == "deployment":
        data["toolchain"]["deployment_target"] = "13.0"
    elif change == "census-commit":
        data["toolchain"]["census_build_commit"] = "f" * 40
    elif change == "census-sha":
        data["toolchain"]["census_asset_sha256"] = "f" * 64
    elif change == "no-runtime":
        data["toolchain_runtime"] = []
    elif change == "two-runtimes":
        data["toolchain_runtime"].append(dict(runtime))
    elif change.startswith("runtime-"):
        key, value = {
            "runtime-pin": ("pin", "Apple clang version 21.0.1 (clang-2100.1.1.101)"),
            "runtime-name": ("name", "compiler-rt"),
            "runtime-version": ("version", "21.0.0"),
            "runtime-licence": ("licence", "Apache-2.0"),
            "runtime-linkage": ("linkage", "proven"),
            "runtime-kind": ("kind", "gcc-runtime"),
            "runtime-chosen": ("chosen", "Apache-2.0 WITH LLVM-exception"),
            "runtime-source": ("source_url", "https://github.com/llvm/llvm-project"),
            "runtime-repository": ("repository", "https://github.com/apple/llvm-project"),
            "runtime-basis": ("basis", "binary"),
        }[change]
        runtime[key] = value
    elif change == "bytes":
        (folder / "zlib--COPYING").write_bytes(b"other\n")
    elif change == "deleted":
        (folder / "zlib--COPYING").unlink()
    elif change == "stray":
        (folder / "stray--COPYING").write_bytes(b"x\n")
    elif change == "two-digests":
        component(data, "x264")["texts"][0]["path"] = "zlib--COPYING"
    elif change == "not-utf8":
        zlib["texts"][0] = macos_text(folder, "zlib", b"caf\xe9\n")
    else:
        raise AssertionError(change)


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        ("census-string", "census must be pending or a complete census object"),
        ("census-state", "census state must be complete"),
        ("census-field", "invalid census fields"),
        ("census-job", "census job_url must be a job of the build run"),
        ("census-lines", "invalid census version_lines"),
        ("census-libraries", "invalid census external_libraries"),
        ("no-components", "components must be a nonempty list"),
        ("missing-component", "components must be exactly the build's; missing ['zlib']"),
        ("invented-component", "unknown ['libvpx']"),
        ("duplicate-component", "duplicate component zlib"),
        ("stage", "zlib: stage must be build-zlib"),
        ("via", "via is Windows-only"),
        ("http", "zlib: source repository must use HTTPS"),
        ("pin-kind", "zlib: pin_kind must be sha256 or commit"),
        ("tarball-pin", "zlib: invalid tarball sha256 pin"),
        ("commit-pin", "zlib: invalid source commit"),
        ("extra-repositories", "zlib: extra_repositories must be empty"),
        ("basis", "licence_basis must be pinned-source-text"),
        ("incompatible", "gpl3_compatible yes"),
        ("licence", "incompatible/invalid component licence"),
        ("chosen", "invalid component chosen licence"),
        ("unlinked-built", "libogg: invalid component status 'built'"),
        ("linked-unlinked", "zlib: invalid component status 'built-not-linked'"),
        ("status-list", "zlib: invalid component status []"),
        ("status-dict", "zlib: invalid component status {}"),
        ("unlinked-flag", "libogg: configure_flag must be null or nonempty"),
        ("unmapped", "unmapped=['--enable-libx265']"),
        ("absent", "absent=['--enable-zlib']"),
        ("twice", "configure flag --enable-libx265 mapped twice"),
        ("member-parent", "unsafe component zlib text member"),
        ("member-absolute", "unsafe component zlib text member"),
        ("member-backslash", "unsafe component zlib text member"),
        ("path", "unsafe component zlib text path"),
        ("excerpt", "invalid component zlib text excerpt"),
        ("excerpt-name", "invalid component zlib text excerpt"),
        ("text-fields", "invalid component zlib text fields"),
        ("no-texts", "component zlib texts must be nonempty"),
        ("no-toolchain", "invalid toolchain fields"),
        ("compiler", "invalid toolchain compiler"),
        ("xcode", "invalid toolchain xcode"),
        ("target", "invalid toolchain target"),
        ("deployment", "toolchain deployment_target differs from macos_deployment_target"),
        ("census-commit", "census_build_commit differs from build_repository_commit"),
        ("census-sha", "census_asset_sha256 differs from github_sha256"),
        ("no-runtime", "exactly one toolchain_runtime row"),
        ("two-runtimes", "exactly one toolchain_runtime row"),
        ("runtime-pin", "runtime pin must be"),
        ("runtime-name", "runtime name must be"),
        ("runtime-version", "runtime version must be"),
        ("runtime-licence", "runtime licence must be"),
        ("runtime-linkage", "runtime linkage must be 'inferred'"),
        ("runtime-kind", "runtime kind must be 'apple-clang-runtime'"),
        ("runtime-chosen", "runtime chosen must be None"),
        ("runtime-source", "runtime source_url must be an llvm-project commit tree"),
        ("runtime-repository", "runtime repository must be"),
        ("runtime-basis", "runtime basis must be 'toolchain-marker'"),
        ("bytes", "macOS text sha256 mismatch: zlib--COPYING"),
        ("deleted", "macOS text missing/unsafe: zlib--COPYING"),
        ("stray", "unlisted ['stray--COPYING']"),
        ("two-digests", "text zlib--COPYING carries two digests"),
        ("not-utf8", "macOS text is not strict UTF-8: zlib--COPYING"),
    ],
)
def test_macos_complete_census_refuses(tmp_path, change, refusal):
    folder = tmp_path / "texts"
    data = complete_macos_lock(folder)
    change_census(data, folder, change)
    with pytest.raises(ValueError, match=re.escape(refusal)):
        build.validate_ffmpeg_lock(data, platform="darwin", component_texts_path=folder)


def test_macos_complete_census_admits_shared_texts_excerpts_and_a_commit_pin(tmp_path):
    """One file may serve two rows (same digest); an excerpt names its line range."""
    folder = tmp_path / "texts"
    data = complete_macos_lock(folder)
    x264 = component(data, "x264")
    (folder / "x264--COPYING").unlink()
    x264["texts"] = [dict(component(data, "zlib")["texts"][0], member="COPYING")]
    x264.update(
        repository="https://code.videolan.org/videolan/x264.git", pin="0" * 40, pin_kind="commit"
    )
    body = b"line 1\nline 2\n"
    (folder / "libxml2--dict.c-L1-2.txt").write_bytes(body)
    component(data, "libxml2")["texts"].append(
        {
            "path": "libxml2--dict.c-L1-2.txt",
            "sha256": hashlib.sha256(body).hexdigest(),
            "member": "libxml2-1.0/dict.c#L1-2",
        }
    )
    assert build.validate_ffmpeg_lock(data, platform="darwin", component_texts_path=folder)


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


def scan_tool(tmp_path: Path, lock: dict[str, Any], payload: bytes) -> str:
    """``_macos_ffmpeg_version`` on ``payload`` as a file (bytes only; nothing runs)."""
    target = tmp_path / "ffmpeg"
    target.write_bytes(payload)
    return build._macos_ffmpeg_version(target, lock)


def scan_verdict(tmp_path: Path, lock: dict[str, Any], payload: bytes) -> str:
    try:
        scan_tool(tmp_path, lock, payload)
    except RuntimeError as error:
        return f"REFUSED {error}"
    return "ACCEPTED"


def tool_strings(lock: dict[str, Any]) -> tuple[bytes, bytes, bytes]:
    """``(version token, configuration body, a minimal well-formed tool's bytes)``."""
    version = lock["version"].encode()
    body = lock["configure_line"].removeprefix("configuration: ").encode("utf-8")
    return version, body, b"\0%s version %s\0" + version + b"\0" + body + b"\0"


def test_macos_scan_admits_the_minimal_tool(tmp_path):
    assert scan_tool(tmp_path, macos_lock(), tool_strings(macos_lock())[2]).startswith("ffmpeg")


@pytest.mark.parametrize(
    "case",
    [
        "second-cc-configuration",
        "unterminated-configuration",
        "control-byte-in-configuration",
        "version-extra-words",
        "version-at-eof",
    ],
)
def test_macos_scan_refuses_the_reviewers_a4_cases(tmp_path, case):
    """A4-F2 / A4-F3, the reviewer's probe: each was ACCEPTED at ``ae96a4e2``."""
    lock = macos_lock()
    version, body, good = tool_strings(lock)
    payload = {
        "second-cc-configuration": good
        + b"\0cc=clang --prefix=/other --enable-gpl --enable-libx265\0",
        "unterminated-configuration": b"\0" + version + b"\0" + body,
        "control-byte-in-configuration": b"\0" + version + b"\0" + body + b"\x01junk\0",
        "version-extra-words": b"\0" + version + b" extra words\0" + body + b"\0",
        "version-at-eof": b"\0" + body + b"\0" + version,
    }[case]
    assert scan_verdict(tmp_path, lock, payload).startswith("REFUSED")


def test_macos_scan_judges_the_whole_c_string_around_the_token(tmp_path):
    """A4-F3's class: EVERY byte after the token, before its NUL (and every non-NUL byte
    before it, after the previous NUL), makes the C string something other than the token;
    the token at EOF (no NUL) is unterminated. Bare, and inside the banner array (whose
    START is const data, not judged, but whose END is)."""
    lock = macos_lock()
    version, body, _good = tool_strings(lock)
    tail = b"\0" + body + b"\0"
    admitted = []
    for byte in range(1, 256):
        mark = bytes([byte])
        for label, payload in (
            ("after", b"\0" + version + mark + b"\0" + tail),
            ("after-words", b"\0" + version + mark + b"words\0" + tail),
            ("before", b"\0" + mark + version + b"\0" + tail),
            ("banner-after", b"\0FFmpeg version " + version + mark + b"\0" + tail),
        ):
            if label == "banner-after":  # the bare token is needed for an accept at all
                payload = b"\0" + version + payload
            if scan_verdict(tmp_path, lock, payload) == "ACCEPTED":
                admitted.append((label, byte))
    assert admitted == []
    for payload in (
        tail + b"\0" + version,
        tail + b"\0" + version + b"\0FFmpeg version " + version,
    ):
        assert "unterminated" in scan_verdict(tmp_path, lock, payload)


def test_macos_scan_judges_the_whole_c_string_around_the_configuration(tmp_path):
    """A4-F3's class for the configuration: every byte glued after or before the body, and
    the body at EOF, are refused (one C string, compared whole)."""
    lock = macos_lock()
    version, body, _good = tool_strings(lock)
    head = b"\0" + version + b"\0"
    admitted = []
    for byte in range(1, 256):
        mark = bytes([byte])
        for label, payload in (
            ("after", head + body + mark + b"\0"),
            ("after-words", head + body + mark + b"junk\0"),
            ("before", head + b"\0" + mark + body + b"\0"),
        ):
            if scan_verdict(tmp_path, lock, payload) == "ACCEPTED":
                admitted.append((label, byte))
    assert admitted == []
    assert "unterminated" in scan_verdict(tmp_path, lock, head + body)


@pytest.mark.parametrize(
    "first",
    ["cc=clang", "--cc=clang", "extra-version=x", "--prefix=/other", "--enable-gpl", "x"],
)
@pytest.mark.parametrize(
    "marker",
    [
        "--enable-gpl",
        "--enable-version3",
        "--enable-nonfree",
        "--disable-gpl",
        "--enable-libx265",
        "--disable-libx265",
        "--enable-libx264",
        "--extra-version=20261110",
        "extra_version=20261110",
        "--pkg-config-flags=--static",
    ],
)
def test_macos_scan_sees_a_second_configuration_by_any_ffmpeg_switch(tmp_path, first, marker):
    """A4-F2's class: a C string carrying ANY of FFmpeg's own configure switches (licence,
    libx264 / libx265, extra-version, pkg-config-flags), whatever its first argument, is a
    configuration candidate; a second, different one is refused."""
    lock = macos_lock()
    good = tool_strings(lock)[2]
    other = f"{first} --prefix=/other {marker}".encode()
    assert "configuration" in scan_verdict(tmp_path, lock, good + b"\0" + other + b"\0")


@pytest.mark.parametrize(
    "library",
    [
        b"--prefix=/Volumes/ffmpeg_arm64/tool --disable-unit-tests",  # libvpx's, real
        b"Rate distribution information input.It requires --enable-rate-guide-deltaq=1.",
        b"--prefix=/usr/local --enable-shared --disable-static --enable-libs",
        b"see --enable-gpl-compat-mode",  # not FFmpeg's switch (whole token)
        b"(--enable-gpl)",  # not a token of its own
    ],
)
def test_macos_scan_leaves_other_libraries_configurations_alone(tmp_path, library):
    """The exclusion rule, stated: a configuration-like C string with NONE of FFmpeg's own
    switches (as whole space-separated tokens) is another component's (libvpx's in a real
    arm64 ffmpeg, SVT-AV1's help text), not an FFmpeg configuration."""
    lock = macos_lock()
    payload = tool_strings(lock)[2] + b"\0" + library + b"\0"
    assert scan_verdict(tmp_path, lock, payload) == "ACCEPTED"


def test_macos_scan_reads_a_utf8_configuration_as_one_string(tmp_path):
    """A4-F3: a configure line with a UTF-8 include path is ONE C string (accepted when the
    lock carries it); the same line in another encoding is malformed evidence, refused."""
    lock = macos_lock()
    lock["configure_line"] += " --extra-cflags='-I/Users/José/include'"
    assert build.validate_ffmpeg_lock(lock, platform="darwin") is lock
    version, body, good = tool_strings(lock)
    assert scan_tool(tmp_path, lock, good).startswith("ffmpeg")
    latin = body.replace("é".encode(), b"\xe9")
    verdict = scan_verdict(tmp_path, lock, b"\0" + version + b"\0" + latin + b"\0")
    assert "not UTF-8" in verdict
    verdict = scan_verdict(tmp_path, lock, good + b"\0" + latin + b"\0")
    assert "not UTF-8" in verdict


def test_macos_scan_refuses_oversized_evidence(tmp_path):
    """A candidate whose C string runs past the bound (no NUL within it) is refused as
    oversized, never truncated into an acceptable prefix."""
    lock = macos_lock()
    version, body, good = tool_strings(lock)
    filler = b"x" * 8192  # the bound (``_FFMPEG_STRING_LIMIT``)
    for payload in (
        good + b"\0" + body + b" " + filler + b"\0",
        good + b"\0" + filler + b" --enable-gpl\0",
        good + b"\0" + version + filler + b"\0",
        good + b"\0FFmpeg version " + version + filler + b"\0",
    ):
        assert "oversized" in scan_verdict(tmp_path, lock, payload)
    # Controls: within the bound, and the token as the file's first string (file start is
    # a boundary), are admitted.
    long = macos_lock()
    long["configure_line"] += " --extra-cflags=-D" + "X" * (8000 - len(body))
    assert build.validate_ffmpeg_lock(long, platform="darwin") is long
    assert 7900 < len(tool_strings(long)[1]) <= 8192
    assert scan_verdict(tmp_path, long, tool_strings(long)[2]) == "ACCEPTED"
    first = version + b"\0" + body + b"\0"
    assert scan_verdict(tmp_path, lock, first) == "ACCEPTED"


READ_BOUNDARIES = (1024 * 1024, 1024 * 1024 - 8193, 1024 * 1024 - 8192, 2 * 1024 * 1024 - 8193)
"""The block boundary and the judged-region edges (the bound 8192 plus the NUL)."""


@pytest.mark.parametrize("needle", ["second-configuration", "glued-configuration", "token-tail"])
def test_macos_scan_judges_c_strings_across_the_read_boundary(tmp_path, needle):
    """The bounded C-string rule holds where a string straddles a read or judging boundary
    (1, half its length and len - 1 bytes of it before the boundary)."""
    lock = macos_lock()
    version, body, good = tool_strings(lock)
    candidate = {
        "second-configuration": b"cc=clang --prefix=/other --enable-gpl",
        "glued-configuration": body + b"\x01",
        "token-tail": version + b" extra",
    }[needle]
    for boundary in READ_BOUNDARIES:
        for split in (1, len(candidate) // 2, len(candidate) - 1):
            pad = boundary - split - len(good) - 1
            payload = good + b"\0" * pad + b"\0" + candidate + b"\0" + b"\0" * 64
            assert payload.index(candidate, len(good)) == boundary - split
            verdict = scan_verdict(tmp_path, lock, payload)
            assert verdict.startswith("REFUSED"), (boundary, split)


def test_macos_scan_admits_the_tool_strings_across_the_read_boundary(tmp_path):
    lock = macos_lock()
    version, body, good = tool_strings(lock)
    for boundary in READ_BOUNDARIES:
        for needle in (version, body):
            pad = boundary - good.index(needle) - len(needle) // 2
            assert scan_verdict(tmp_path, lock, b"\0" * pad + good + b"\0" * 64) == "ACCEPTED"


MARKER = APPLE_CLANG.encode()


def complete_bundle(case, folder: Path, monkeypatch, payload: bytes) -> None:
    """Give ``macos_bundle``'s lock a complete census and its tools ``payload``."""
    complete = complete_macos_lock(folder)
    for key in ("census", "components", "toolchain", "toolchain_runtime"):
        case.data[key] = complete[key]
    monkeypatch.setattr(build, "FFMPEG_MACOS_TEXTS_PATH", folder)
    root = case.data["archive_root"]
    for tool in ("ffmpeg", "ffprobe"):
        case.members[f"{root}/bin/{tool}"] = fake_macho(case.data, extra=payload)
    case.write()
    case.data["toolchain"]["census_asset_sha256"] = case.data["github_sha256"]
    case.pin.write_text(json.dumps(case.data), encoding="utf-8")


@pytest.mark.parametrize(
    ("payload", "admitted"),
    [
        (b"\0" + MARKER + b"\0", True),
        (b"\x01" + MARKER + b"\0", True),
        (b"", False),
        (b"\0X" + MARKER + b"\0", False),
        (b"\0" + MARKER + b"X\0", False),
        (b"\0" + MARKER.replace(b"21.0.0", b"21.0.1") + b"\0", False),
        (b"\0" + MARKER.replace(b"2100.1.1.101", b"2100.1.1.10") + b"\0", False),
    ],
)
def test_macos_bundle_requires_the_census_toolchain_marker(
    macos_bundle, tmp_path, monkeypatch, payload, admitted
):
    """The tools must carry the toolchain object's compiler as a COMPLETE C string (CC_IDENT,
    printed ``built with ...``); otherwise nothing is placed and nothing is trusted."""
    case = macos_bundle
    complete_bundle(case, tmp_path / "texts", monkeypatch, payload)
    trusted: set[str] = set()
    macos = case.app / "Contents" / "MacOS"
    if admitted:
        assert len(bundle_macos(case, verified_hashes=trusted)) == 2
        assert sorted(p.name for p in macos.iterdir()) == ["Clearwater", "ffmpeg", "ffprobe"]
        return
    with pytest.raises(ValueError, match="ffmpeg: missing the Apple toolchain marker"):
        bundle_macos(case, verified_hashes=trusted)
    assert sorted(p.name for p in macos.iterdir()) == ["Clearwater"]
    assert not (case.app / "Contents" / "Resources").exists() or not any(
        (case.app / "Contents" / "Resources").iterdir()
    )
    assert trusted == set()


def test_macos_marker_is_judged_across_the_read_boundary(tmp_path):
    """Every split of the marker across a 1 MiB block is found; a printable byte glued
    before it in the previous block is still seen (and refused)."""
    folder = tmp_path / "texts"
    lock = complete_macos_lock(folder)
    path = tmp_path / "tool"
    boundary = 1024 * 1024
    for split in (0, 1, len(MARKER) // 2, len(MARKER), len(MARKER) + 1):
        for prefix, found in ((b"\0", True), (b"Z", False)):
            start = boundary - split
            body = b"\0" * (start - 1) + prefix + MARKER + b"\0" + b"\0" * 64
            assert body.index(MARKER) == start
            path.write_bytes(body)
            if found:
                build._check_macos_toolchain_marker(path, lock)
            else:
                with pytest.raises(ValueError, match="missing the Apple toolchain marker"):
                    build._check_macos_toolchain_marker(path, lock)
    path.write_bytes(MARKER + b"\0")
    build._check_macos_toolchain_marker(path, lock)
    lock["toolchain"] = None
    path.write_bytes(b"\0")
    build._check_macos_toolchain_marker(path, lock)  # a pending census carries no marker


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


# --- WP6.5 part 3c: the committed macOS lock, its texts, its transport family and the C13
# darwin contracts. The switch (MACOS_FFMPEG_BUNDLED) stays OFF: the .app notices are the
# F0-2 group's (CHARC, 2026-11-09).

REAL_MACOS_LOCK = REPO_ROOT / "tools" / "package" / "ffmpeg-macos.lock.json"
"""The committed macOS lock: fork run 42661533922 attempt 3, its asset and its census."""

REAL_MACOS_ASSET_SHA256 = "e3f251dc281a71e46e1464436c8cb281994af7fe4ed4978d95922ad82bb176e4"


def real_macos_lock() -> dict[str, Any]:
    return json.loads(REAL_MACOS_LOCK.read_text(encoding="utf-8"))


def lock_texts(data: dict[str, Any]) -> dict[str, str]:
    """Every text the lock names (components and toolchain runtime): path -> sha256."""
    rows = [*data["components"], *data["toolchain_runtime"]]
    return {text["path"]: text["sha256"] for row in rows for text in row["texts"]}


def test_the_real_macos_lock_pins_the_artifact_and_validates():
    """Condition 1: the lock pins the ARTIFACT (tag, fork commit, asset, size, both digests)."""
    data = real_macos_lock()
    assert build.load_macos_ffmpeg_lock() == data
    tag = "ffmpeg-9.0-gb204e94e-macos-arm64-nozvbi-9cb0fa8"
    asset = "ffmpeg-n9.0.2-47-gb204e94e90-macos-arm64-gpl-9.0.zip"
    assert data["release_tag"] == tag
    assert data["build_repository_commit"] == "9cb0fa81871f09ae3f750d6845874c26a871b985"
    assert data["asset_name"] == asset
    assert data["asset_url"] == (
        f"https://github.com/rwsmythe/FFmpeg-Builds/releases/download/{tag}/{asset}"
    )
    assert data["size_bytes"] == 37_978_871
    assert data["github_sha256"] == data["seat_sha256"] == REAL_MACOS_ASSET_SHA256
    assert data["toolchain"]["census_asset_sha256"] == REAL_MACOS_ASSET_SHA256
    assert data["census"]["state"] == "complete"
    assert data["build_run_url"] == (
        "https://github.com/rwsmythe/FFmpeg-Builds/actions/runs/42661533922"
    )


def test_the_macos_component_texts_are_exactly_the_locks_and_rehash_to_it():
    """R1 / R2 / Q2: one folder, EXACTLY the lock's 36 texts, each byte-equal to its pin."""
    wanted = lock_texts(real_macos_lock())
    folder = build.FFMPEG_MACOS_TEXTS_PATH
    assert folder == REPO_ROOT / "tools/package/native-licences/ffmpeg-macos-components"
    assert len(wanted) == 36
    assert sorted(path.name for path in folder.iterdir()) == sorted(wanted)
    for name, digest in wanted.items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest, name


@pytest.mark.parametrize("damage", ["byte", "missing", "extra"])
def test_the_real_macos_lock_refuses_a_damaged_texts_folder(tmp_path, damage):
    """The re-hash is also the validator's: a copy of the folder, damaged once, is refused."""
    folder = tmp_path / "ffmpeg-macos-components"
    shutil.copytree(build.FFMPEG_MACOS_TEXTS_PATH, folder)
    data = real_macos_lock()
    build.validate_ffmpeg_lock(data, component_texts_path=folder, platform="darwin")
    if damage == "byte":
        target = folder / "llvm-project--LICENSE.TXT"
        body = bytearray(target.read_bytes())
        body[100] ^= 1
        target.write_bytes(bytes(body))
    elif damage == "missing":
        (folder / "fribidi--COPYING").unlink()
    else:
        (folder / "unlisted--COPYING").write_bytes(b"text\n")
    with pytest.raises(ValueError):
        build.validate_ffmpeg_lock(data, component_texts_path=folder, platform="darwin")


def bump(hex_digest: str, index: int) -> str:
    """``hex_digest`` with the digit at ``index`` moved by one (``f`` wraps to ``0``)."""
    digit = (int(hex_digest[index], 16) + 1) % 16
    return hex_digest[:index] + format(digit, "x") + hex_digest[index + 1 :]


@pytest.fixture
def real_lock_transport(tmp_path, monkeypatch):
    """The real lock with its transport fields (size, digests, URL; the census digest follows)
    moved to a synthetic zip: the seat's zip is not in the repository."""
    data = real_macos_lock()
    source = tmp_path / data["asset_name"]
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(f"{data['archive_root']}/LICENSE.txt", b"synthetic\n")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    data["size_bytes"] = source.stat().st_size
    data["github_sha256"] = data["seat_sha256"] = digest
    data["toolchain"]["census_asset_sha256"] = digest
    data["asset_url"] = source.as_uri()
    monkeypatch.setattr(build, "_TEST_ALLOW_FILE_URLS", True)
    return data


def _transport_mutation(data: dict[str, Any], mutation: str) -> str:
    """Apply ``mutation`` to ``data``; return the sha256 argument the caller passes."""
    argument: str = data["github_sha256"]
    kind, _, where = mutation.partition(" ")
    if kind == "size":
        data["size_bytes"] += int(where)
    elif kind in {"github_sha256", "seat_sha256"}:
        data[kind] = bump(data[kind], int(where))
    elif kind == "both":  # the two digests together: a self-consistent pair
        data["github_sha256"] = data["seat_sha256"] = bump(argument, int(where))
    elif kind == "all":  # the two digests and the census digest: past every lock rule
        moved = bump(argument, int(where))
        data["github_sha256"] = data["seat_sha256"] = moved
        data["toolchain"]["census_asset_sha256"] = moved
        argument = moved
    elif kind == "argument":
        argument = bump(argument, int(where))
    return argument


@pytest.mark.parametrize(
    ("mutation", "refusal"),
    [
        ("none", None),
        ("size +1", "download size differs from lock"),
        ("size -1", "download size exceeds lock"),
        ("github_sha256 0", "sha256 readings differ"),
        ("github_sha256 63", "sha256 readings differ"),
        ("seat_sha256 0", "sha256 readings differ"),
        ("seat_sha256 63", "sha256 readings differ"),
        ("all 0", "download sha256 mismatch; archive was not opened"),
        ("all 63", "download sha256 mismatch; archive was not opened"),
        ("argument 0", "sha256 argument differs from the lock"),
        ("argument 63", "sha256 argument differs from the lock"),
        ("both 0", "census_asset_sha256 differs from github_sha256"),
        ("both 63", "census_asset_sha256 differs from github_sha256"),
    ],
)
def test_the_real_macos_lock_refuses_each_transport_mutation(
    real_lock_transport, tmp_path, mutation, refusal
):
    """Condition 1's family: every size / digest field off by one (first and last digit) is
    RED; the unmutated lock is GREEN. ``all`` moves both digests and the census digest (the
    self-consistent lock reaches the download's own digest check); ``both`` moves the two
    digests only (the census binds the asset)."""
    data = json.loads(json.dumps(real_lock_transport))
    argument = _transport_mutation(data, mutation)
    out = tmp_path / "dl"

    def attempt() -> None:
        checked = build.validate_ffmpeg_lock(data, platform="darwin")
        build._download_ffmpeg(data["asset_url"], argument, out, checked)

    if refusal is None:
        attempt()
        return
    with pytest.raises((ValueError, RuntimeError), match=re.escape(refusal)):
        attempt()
    assert not (out / data["archive_root"]).exists()


# The C13 darwin contracts (G3 classification rows 43-44, 49-52, 55-61): build() on its darwin
# path against the committed macOS lock. On Windows sys.platform reads "darwin" for the build
# call only (the stand-in executable is written first, as in darwin_app_build); on the macOS
# runner the platform is native.


def darwin_release_build(monkeypatch, tmp_path, *, origin=None, seal=None) -> Path:
    """Prepare ``build()``'s darwin path: PyInstaller writes the .app; returns ``out``."""
    monkeypatch.setenv("PYINSTALLER_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr(build, "pack_sources", lambda: [])
    if origin is not None:
        monkeypatch.setattr(build, "native_origin_violations", origin)
    monkeypatch.setattr(build, "seal_macos_bundle", seal or (lambda bundle: None))
    out = tmp_path / "out"
    # Built (and PyInstaller imported) BEFORE sys.platform reads darwin (darwin_app_build).
    source = make_exe(out / "synthetic", [], modules=["clearwater", "graphlib"])

    def build_folder(args):
        target = Path(args[args.index("--distpath") + 1]) / "Clearwater.app/Contents/MacOS"
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target / "Clearwater")

    monkeypatch.setattr(build, "run_pyinstaller", build_folder)
    monkeypatch.setattr(build.sys, "platform", "darwin")
    return out


def real_lock_bundle(case) -> SimpleNamespace:
    """``macos_bundle`` on the REAL lock: every field but the transport (size, digests, URL; the
    census digest follows) is the committed lock's, and the tools carry its version, its
    configure line and its toolchain marker."""
    real = real_macos_lock()
    case.data.clear()
    case.data.update(real)
    marker = b"\0" + real["toolchain"]["compiler"].encode() + b"\0"
    for tool in ("ffmpeg", "ffprobe"):
        case.members[f"{real['archive_root']}/bin/{tool}"] = fake_macho(real, extra=marker)
    case.write()
    case.data["toolchain"]["census_asset_sha256"] = case.data["github_sha256"]
    case.pin.write_text(json.dumps(case.data), encoding="utf-8")
    return case


@pytest.mark.parametrize("tampered", [False, True])
def test_build_enforces_origin_after_all_native_copies_on_darwin(
    tmp_path, monkeypatch, capsys, macos_bundle, tampered
):
    """C13 (``:383``'s darwin contract): the real bundling and the real darwin origin walk;
    tool bytes verified from the archive pass, a post-extraction change fails the build."""
    case = real_lock_bundle(macos_bundle)
    monkeypatch.setattr(build.subprocess, "run", case.real_run)
    monkeypatch.setattr(build, "_native_origin_hashes", lambda: set())
    monkeypatch.setattr(build, "_is_clearwater_bootloader", lambda _: True)
    real_bundle = build.bundle_ffmpeg
    changed = fake_macho(case.data, extra=b"changed after extraction")

    def bundle(destination, **kwargs):
        result = real_bundle(destination, **kwargs)
        if tampered:
            (destination / "ffmpeg").write_bytes(changed)
        return result

    monkeypatch.setattr(build, "bundle_ffmpeg", bundle)
    out = darwin_release_build(monkeypatch, tmp_path)
    foreign = tree(tmp_path / "foreign", ["ffmpeg"])
    monkeypatch.setenv("PATH", str(foreign))
    status = build.build(
        "onedir",
        out=out,
        ffmpeg_from=case.data["asset_url"],
        ffmpeg_sha256=case.data["seat_sha256"],
    )
    output = capsys.readouterr().out
    assert status == int(tampered), output
    assert ("native origin check: PASS" in output) == (not tampered)
    macos = next(out.rglob("Clearwater.app")) / "Contents" / "MacOS"
    root = case.data["archive_root"]
    if not tampered:
        for tool in ("ffmpeg", "ffprobe"):
            assert (macos / tool).read_bytes() == case.members[f"{root}/bin/{tool}"]
    else:
        assert "Contents/MacOS/ffmpeg" in output and str(foreign / "ffmpeg") in output


@pytest.mark.parametrize("fail", [False, True])
def test_release_bundle_is_checked_in_the_built_executable_folder_on_darwin(
    monkeypatch, tmp_path, capsys, fail
):
    """C13 (``:1301``'s darwin contract): build() takes the workflow's pair (``asset_url``,
    ``seat_sha256``) from the committed lock, bundles into Contents/MacOS, and fails on the
    bundle's failure; a pair off the lock is refused before PyInstaller."""
    pin = real_macos_lock()
    calls = []

    def fetched(destination, *, out, url, sha256, verified_hashes, platform):
        assert platform == "darwin"
        assert destination.as_posix().endswith("Clearwater.app/Contents/MacOS")
        assert (destination / "Clearwater").is_file()
        calls.append((url, sha256))
        if fail:
            raise RuntimeError("planted FFmpeg configuration mismatch")
        return [(destination / "ffmpeg", f"ffmpeg version {pin['version']}")]

    monkeypatch.setattr(build, "bundle_ffmpeg", fetched)
    out = darwin_release_build(monkeypatch, tmp_path, origin=lambda *a, **kw: [])
    status = build.build(
        "onedir", out=out, ffmpeg_from=pin["asset_url"], ffmpeg_sha256=pin["seat_sha256"]
    )
    printed = capsys.readouterr().out
    assert status == int(fail), printed
    assert calls == [(pin["asset_url"], REAL_MACOS_ASSET_SHA256)]
    if fail:
        assert "FAILED: FFmpeg bundle: planted FFmpeg configuration mismatch" in printed
        assert "bundle check: PASS" not in printed
    else:
        assert "bundle check: PASS" in printed
    off = bump(REAL_MACOS_ASSET_SHA256, 63)
    assert build.build("onedir", out=out, ffmpeg_from=pin["asset_url"], ffmpeg_sha256=off) == 1
    assert "FFmpeg URL/sha256 differ from the lock" in capsys.readouterr().out
    assert len(calls) == 1


@pytest.mark.parametrize("fails", [False, True])
def test_notices_writing_follows_ffmpeg_and_fails_the_build_on_error_on_darwin(
    tmp_path, monkeypatch, capsys, macos_bundle, fails
):
    """C13 (``:1356``'s darwin contract): with the real (complete) census, --notices is
    admitted; notices see the verified archive's material; a notice failure refuses the build
    before the seal. The notices writer is a stand-in (the .app notices are the F0-2 group's)."""
    case = real_lock_bundle(macos_bundle)
    monkeypatch.setattr(build.subprocess, "run", case.real_run)
    events = []
    out = darwin_release_build(
        monkeypatch,
        tmp_path,
        origin=lambda *a, **kw: [],
        seal=lambda bundle: events.append("seal"),
    )
    root = case.data["archive_root"]

    def notices(folder):
        events.append("notices")
        assert folder.as_posix().endswith("Clearwater.app/Contents/MacOS")
        for tool in ("ffmpeg", "ffprobe"):
            assert (folder / tool).read_bytes() == case.members[f"{root}/bin/{tool}"]
        record = (folder.parent / "Resources" / "ffmpeg-BUILD.txt").read_text(encoding="utf-8")
        assert case.data["github_sha256"] in record and case.data["release_tag"] in record
        if fails:
            raise ValueError("planted notice coverage failure")
        path = folder.parent / "Resources" / "THIRD_PARTY_NOTICES.md"
        path.write_text("generated notices", encoding="utf-8")
        return path

    monkeypatch.setattr(build, "write_artifact_notices", notices)
    status = build.build(
        "onedir",
        out=out,
        ffmpeg_from=case.data["asset_url"],
        ffmpeg_sha256=case.data["seat_sha256"],
        notices=True,
    )
    printed = capsys.readouterr().out
    assert status == int(fails), printed
    assert "census pending" not in printed
    assert events == (["notices"] if fails else ["notices", "seal"])
    if fails:
        assert "FAILED: artifact notices: planted notice coverage failure" in printed
    else:
        assert "wrote" in printed and "THIRD_PARTY_NOTICES.md" in printed


def _darwin_release_names(out: Path) -> tuple[Path, Path]:
    """The darwin release folder and the release ZIP path (call after the platform is set)."""
    version = build.app_version()
    root = build.release_dir(out, "onedir", version)
    return root, out / (build.release_zip_name("onedir", version) + ".zip")


@pytest.mark.parametrize("failure", ["none", "notices", "smoke", "timestamp"])
def test_zip_is_published_only_after_successful_notices_and_smoke_on_darwin(
    tmp_path, monkeypatch, capsys, failure
):
    """C13 (``:1572``'s darwin contract): on the committed lock the zip is written only after
    notices, the seal and the smoke all pass; a stale zip is removed first."""
    pin = real_macos_lock()
    order = []
    out = darwin_release_build(
        monkeypatch, tmp_path, origin=lambda *a, **kw: [], seal=lambda b: order.append("seal")
    )
    root, archive = _darwin_release_names(out)
    out.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(b"previous release")
    archive.with_suffix(".zip.sha256").write_bytes(b"previous checksum\n")

    def checked_bundle(*args, **kwargs):
        assert not archive.exists() and not archive.with_suffix(".zip.sha256").exists()
        return []

    def notices(folder):
        order.append("notices")
        if failure == "notices":
            raise ValueError("planted notices failure")
        path = folder.parent / "Resources" / "THIRD_PARTY_NOTICES.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic notices\n", encoding="utf-8")
        return path

    def smoke(folder, *, out):
        assert (folder.parent / "Resources" / "THIRD_PARTY_NOTICES.md").is_file()
        order.append("smoke")
        return int(failure == "smoke")

    def epoch():
        assert order == ["notices", "seal", "smoke"]
        if failure == "timestamp":
            raise ValueError("planted source timestamp failure")
        return 1793908801

    monkeypatch.setattr(build, "bundle_ffmpeg", checked_bundle)
    monkeypatch.setattr(build, "write_artifact_notices", notices)
    monkeypatch.setattr(build, "smoke_artifact", smoke)
    monkeypatch.setattr(build, "source_commit_epoch", epoch)
    status = build.build(
        "onedir",
        out=out,
        notices=True,
        smoke=True,
        zip_release=True,
        ffmpeg_from=pin["asset_url"],
        ffmpeg_sha256=pin["seat_sha256"],
    )
    printed = capsys.readouterr().out
    assert status == int(failure != "none"), printed
    assert order == (["notices"] if failure == "notices" else ["notices", "seal", "smoke"])
    assert archive.exists() == archive.with_suffix(".zip.sha256").exists() == (failure == "none")
    if failure == "none":
        with zipfile.ZipFile(archive) as packed:
            assert "Clearwater.app/Contents/Resources/THIRD_PARTY_NOTICES.md" in packed.namelist()
    if failure == "timestamp":
        assert "FAILED: release zip: planted source timestamp failure" in printed
    assert root.is_dir()


@pytest.mark.parametrize("mutation", ["added", "removed", "changed"])
def test_release_zip_refuses_smoke_mutations_on_darwin(tmp_path, monkeypatch, capsys, mutation):
    """C13 (``:1662``'s darwin contract): on the committed lock the published .app equals the
    pre-smoke inventory; a file the smoke adds, removes or changes refuses the zip."""
    pin = real_macos_lock()
    out = darwin_release_build(monkeypatch, tmp_path, origin=lambda *a, **kw: [])
    _root, archive = _darwin_release_names(out)

    def notices(folder):
        target = folder.parent / "Resources" / "THIRD_PARTY_NOTICES.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"covered bytes\n")
        return target

    def smoke(folder, *, out):
        target = folder.parent / "Resources" / "THIRD_PARTY_NOTICES.md"
        assert target.read_bytes() == b"covered bytes\n"
        if mutation == "added":
            (folder / "new-file.txt").write_bytes(b"uncovered bytes")
        elif mutation == "removed":
            target.unlink()
        else:
            # Same size, so a path/size-only snapshot would fail this control.
            target.write_bytes(b"altered bytes\n")
        return 0

    monkeypatch.setattr(build, "bundle_ffmpeg", lambda *a, **kw: [])
    monkeypatch.setattr(build, "write_artifact_notices", notices)
    monkeypatch.setattr(build, "smoke_artifact", smoke)
    monkeypatch.setattr(build, "source_commit_epoch", lambda: 1793908801)
    status = build.build(
        "onedir",
        out=out,
        notices=True,
        smoke=True,
        zip_release=True,
        ffmpeg_from=pin["asset_url"],
        ffmpeg_sha256=pin["seat_sha256"],
    )
    message = capsys.readouterr().out
    assert status == 1, message
    assert "release zip" in message and mutation in message
    assert ("new-file.txt" if mutation == "added" else "THIRD_PARTY_NOTICES.md") in message
    assert not archive.exists()
    assert not archive.with_suffix(".zip.sha256").exists()
