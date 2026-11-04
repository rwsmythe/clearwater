"""The GPU pack loader against synthetic pack folders under ``tmp_path`` (WP6.1, AD-33).

Parallel leg: no GPU, no footage, no real ``%LOCALAPPDATA%``. Every pack is built here with
the loader's layout; its ``manifest.json`` is written by the build script's helper
(``tools/package/build.py``), so the writer and the loader are checked against each other.
``os.add_dll_directory`` is always replaced by a recorder, so no test changes this process's
DLL search path.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import logging
import os
import site
import sys
import sysconfig
import tomllib
import warnings
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from clearwater import gpu_pack
from clearwater.config import paths as config_paths

REPO_ROOT = Path(__file__).resolve().parents[1]

PACK_NAMES = {
    "cupy-cuda12x",
    "cuda-pathfinder",
    "cuda-toolkit",
    "nvidia-cublas-cu12",
    "nvidia-cuda-nvrtc-cu12",
    "nvidia-cuda-runtime-cu12",
    "nvidia-cufft-cu12",
    "nvidia-curand-cu12",
    "nvidia-cusolver-cu12",
    "nvidia-cusparse-cu12",
    "nvidia-nvjitlink-cu12",
}
"""The pack's eleven distributions as the brief's dispatch fill lists them."""

NVIDIA_LIBS = (
    "cublas",
    "cuda_nvrtc",
    "cuda_runtime",
    "cufft",
    "curand",
    "cusolver",
    "cusparse",
    "nvjitlink",
)
"""The ``site-packages/nvidia/<lib>`` folders the real wheels install (each with ``bin``)."""


def _load_build_script() -> ModuleType:
    """Import ``tools/package/build.py`` by its path (it is not a package).

    ``WP61_BUILD_SCRIPT`` may name another copy (an earlier commit's, for the ledger's
    before / after record), as in ``tests/test_tools_package_build.py``.
    """
    default = REPO_ROOT / "tools" / "package" / "build.py"
    path = Path(os.environ.get("WP61_BUILD_SCRIPT", default))
    spec = importlib.util.spec_from_file_location("wp61_package_build", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = _load_build_script()


def _lock() -> dict[str, dict[str, Any]]:
    """Return ``uv.lock``'s packages by name."""
    document = tomllib.loads((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
    return {package["name"]: package for package in document["package"]}


def _windows_wheel(locked: gpu_pack.LockedDistribution) -> str:
    """Return the locked wheel a Windows install uses (the platform one, else the pure one)."""
    names = [row[0] for row in locked.wheels]
    for name in names:
        if name.endswith("win_amd64.whl"):
            return name
    (pure,) = names
    return pure


WINDOWS_TAGS = ("cp312", "win_amd64")
"""The (interpreter, platform) tags the synthetic Windows packs are checked against."""


def _payload(locked: gpu_pack.LockedDistribution) -> dict[str, bytes]:
    """Return the files (relative to ``site-packages``) a synthetic install of one wheel holds.

    The shapes follow the real wheels: CuPy's three packages, ``cuda/pathfinder``, nothing
    but metadata for ``cuda-toolkit``, and ``nvidia/<lib>/bin/<dll>`` for each NVIDIA wheel
    (cuBLAS also has an ``include`` folder, which is never a DLL folder).
    """
    if locked.name == "cupy-cuda12x":
        return {
            "cupy/__init__.py": b"# cupy\n",
            "cupyx/__init__.py": b"# cupyx\n",
            "cupy_backends/__init__.py": b"# cupy_backends\n",
        }
    if locked.name == "cuda-pathfinder":
        return {"cuda/pathfinder/__init__.py": b"# pathfinder\n"}
    if locked.name == "cuda-toolkit":
        return {}
    lib = locked.name.removeprefix("nvidia-").removesuffix("-cu12").replace("-", "_")
    files = {f"nvidia/{lib}/bin/{lib}64.dll": b"MZ" + lib.encode()}
    if lib == "cublas":
        files["nvidia/cublas/include/cublas.h"] = b"/* cublas */\n"
    return files


def record_hash(data: bytes) -> str:
    """Return ``data``'s hash in ``RECORD``'s form, computed here (not by the product)."""
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    return "sha256=" + digest.decode("ascii")


def record_text(rows: list[tuple[str, bytes]], own: str) -> str:
    """Return a ``RECORD`` file's text for ``(path, content)`` rows plus its own row."""
    lines = [f"{path},{record_hash(data)},{len(data)}" for path, data in rows]
    return "\n".join([*lines, f"{own},,"]) + "\n"


def install(
    site: Path, locked: gpu_pack.LockedDistribution, wheel: str, files: dict[str, bytes]
) -> None:
    """Install one synthetic wheel into ``site`` the way an installer does (with ``RECORD``)."""
    dist_info = locked.dist_info_name
    tags = sorted(build.wheel_file_tags(wheel))
    metadata = {
        f"{dist_info}/METADATA": f"Name: {locked.name}\nVersion: {locked.version}\n".encode(),
        f"{dist_info}/WHEEL": (
            "Wheel-Version: 1.0\n" + "".join(f"Tag: {t}\n" for t in tags)
        ).encode(),
        f"{dist_info}/INSTALLER": b"uv\n",
    }
    everything = {**files, **metadata}
    for name, data in everything.items():
        path = site / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    record = record_text(sorted(everything.items()), f"{dist_info}/RECORD")
    (site / dist_info / "RECORD").write_text(record, encoding="utf-8", newline="\n")


def make_pack(
    root: Path, choose: Callable[[gpu_pack.LockedDistribution], str] | None = None
) -> Path:
    """Fill ``root/<STAMP>`` like a hand-filled Windows pack and write its manifest.

    Args:
        root: The pack root.
        choose: Picks each distribution's locked wheel; the Windows one when None.

    Returns:
        The pack folder.
    """
    folder = root / gpu_pack.STAMP
    site = folder / gpu_pack.SITE_PACKAGES_NAME
    site.mkdir(parents=True)
    for locked in gpu_pack.LOCKED_DISTRIBUTIONS:
        install(site, locked, (choose or _windows_wheel)(locked), _payload(locked))
    build.write_manifest(folder)
    return folder


def locked_named(name: str) -> gpu_pack.LockedDistribution:
    """Return the locked distribution called ``name``."""
    return {d.name: d for d in gpu_pack.LOCKED_DISTRIBUTIONS}[name]


def add_record_rows(folder: Path, name: str, rows: list[str]) -> None:
    """Append raw rows to one distribution's ``RECORD`` and rewrite the manifest to match.

    So a test plants a ``RECORD`` an installer could have written: only the planted rows,
    not a stale manifest, can make the check fail.
    """
    record = folder / gpu_pack.SITE_PACKAGES_NAME / locked_named(name).dist_info_name / "RECORD"
    text = record.read_text(encoding="utf-8") + "".join(f"{row}\n" for row in rows)
    record.write_text(text, encoding="utf-8", newline="\n")
    build.write_manifest(folder)


def edit_manifest(folder: Path, change: Any) -> None:
    """Apply ``change(document)`` to a pack's manifest and write it back."""
    path = folder / gpu_pack.MANIFEST_NAME
    document = json.loads(path.read_text(encoding="utf-8"))
    change(document)
    path.write_text(json.dumps(document), encoding="utf-8")


def entry(document: dict[str, Any], name: str) -> dict[str, Any]:
    """Return the manifest's entry for one distribution."""
    rows: list[dict[str, Any]] = document["distributions"]
    (found,) = [row for row in rows if row["name"] == name]
    return found


def snapshot(root: Path) -> list[tuple[str, int, int]]:
    """Return every path under ``root`` with its size and modification time."""
    return sorted(
        (p.relative_to(root).as_posix(), p.stat().st_size, p.stat().st_mtime_ns)
        for p in root.rglob("*")
    )


@pytest.fixture
def isolated(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Keep ``sys.path`` and the DLL search path of this process untouched.

    Returns:
        The folders the loader asked ``os.add_dll_directory`` to add.
    """
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(site, "PREFIXES", list(site.PREFIXES))  # F-F: never this process's
    added: list[str] = []

    class Handle:
        def __init__(self, folder: str) -> None:
            self.folder = folder

        def close(self) -> None:
            added.remove(self.folder)

    def record(folder: str) -> Handle:
        added.append(folder)
        return Handle(folder)

    monkeypatch.setattr(os, "add_dll_directory", record, raising=False)
    monkeypatch.setattr(gpu_pack, "_DLL_HANDLES", [])
    # The synthetic packs hold Windows wheels: check them as Windows does, on any host.
    monkeypatch.setattr(gpu_pack, "platform_tags", lambda: WINDOWS_TAGS, raising=False)
    return added


# The lock and the stamp.


def test_locked_distributions_equal_the_lock() -> None:
    """The constant is the lock's pack closure, at the lock's versions, with its wheels."""
    lock = _lock()
    closure: set[str] = set()
    pending: list[tuple[str, tuple[str, ...]]] = [("cupy-cuda12x", ("ctk",))]
    while pending:
        name, extras = pending.pop()
        if name == "numpy" or name in closure:
            continue
        closure.add(name)
        package = lock[name]
        requirements = list(package.get("dependencies", []))
        for extra in extras:
            requirements += package.get("optional-dependencies", {}).get(extra, [])
        for requirement in requirements:
            pending.append((requirement["name"], tuple(requirement.get("extra", ()))))
    assert closure == PACK_NAMES
    constant = {locked.name: locked for locked in gpu_pack.LOCKED_DISTRIBUTIONS}
    assert set(constant) == PACK_NAMES
    assert len(gpu_pack.LOCKED_DISTRIBUTIONS) == len(PACK_NAMES)
    for name in PACK_NAMES:
        package = lock[name]
        wheels = {
            (w["url"].rsplit("/", 1)[1], w["hash"].removeprefix("sha256:"), w["url"], w["size"])
            for w in package["wheels"]
        }
        assert constant[name].version == package["version"], name
        assert set(constant[name].wheels) == wheels, name


def test_the_bundle_numpy_satisfies_cupys_requirement() -> None:
    """numpy is not in the pack: the locked numpy must satisfy CuPy's own bound."""
    packaging_requirements = pytest.importorskip("packaging.requirements")
    try:
        requires = importlib.metadata.requires("cupy-cuda12x") or []
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("cupy-cuda12x is not installed in this environment")
    (numpy_line,) = [r for r in requires if r.startswith("numpy")]
    requirement = packaging_requirements.Requirement(numpy_line)
    assert requirement.specifier.contains(_lock()["numpy"]["version"])


def test_the_stamp_is_the_cupy_version_and_the_cuda_major() -> None:
    """``14.2.0-cu12`` from the locked ``cupy-cuda12x``; the major comes from the name."""
    assert gpu_pack.STAMP == "14.2.0-cu12"
    locked_version = _lock()["cupy-cuda12x"]["version"]
    assert gpu_pack.stamp_for("cupy-cuda12x", locked_version) == gpu_pack.STAMP
    assert gpu_pack.stamp_for("cupy-cuda11x", "13.6.0") == "13.6.0-cu11"
    with pytest.raises(ValueError):
        gpu_pack.stamp_for("cupy", "14.2.0")


def test_dist_info_names_follow_the_wheel_escaping() -> None:
    """``nvidia-cuda-nvrtc-cu12`` 12.9.86 installs ``nvidia_cuda_nvrtc_cu12-12.9.86.dist-info``."""
    names = {locked.name: locked.dist_info_name for locked in gpu_pack.LOCKED_DISTRIBUTIONS}
    assert names["nvidia-cuda-nvrtc-cu12"] == "nvidia_cuda_nvrtc_cu12-12.9.86.dist-info"
    assert names["cupy-cuda12x"] == "cupy_cuda12x-14.2.0.dist-info"


# pack_root (Q6).


def test_pack_root_on_windows(tmp_path: Path) -> None:
    """``%LOCALAPPDATA%\\Clearwater\\gpu-pack``; the home fallback when unset or relative."""
    local = tmp_path / "local"
    got = gpu_pack.pack_root(environ={"LOCALAPPDATA": str(local)}, platform="win32", home=tmp_path)
    assert got == local / "Clearwater" / "gpu-pack"
    fallback = tmp_path / "AppData" / "Local" / "Clearwater" / "gpu-pack"
    assert gpu_pack.pack_root(environ={}, platform="win32", home=tmp_path) == fallback
    relative = {"LOCALAPPDATA": "relative"}
    assert gpu_pack.pack_root(environ=relative, platform="win32", home=tmp_path) == fallback


def test_pack_root_on_linux(tmp_path: Path) -> None:
    """``$XDG_DATA_HOME/clearwater/gpu-pack``; ``~/.local/share`` when unset or relative."""
    data = tmp_path / "xdg-data"
    got = gpu_pack.pack_root(environ={"XDG_DATA_HOME": str(data)}, platform="linux", home=tmp_path)
    assert got == data / "clearwater" / "gpu-pack"
    fallback = tmp_path / ".local" / "share" / "clearwater" / "gpu-pack"
    assert gpu_pack.pack_root(environ={}, platform="linux", home=tmp_path) == fallback
    relative = {"XDG_DATA_HOME": "rel"}
    assert gpu_pack.pack_root(environ=relative, platform="linux", home=tmp_path) == fallback


def test_pack_root_on_macos_is_none(tmp_path: Path) -> None:
    """No CUDA on macOS: no pack root, whatever the environment says."""
    environ = {"XDG_DATA_HOME": str(tmp_path), "LOCALAPPDATA": str(tmp_path)}
    assert gpu_pack.pack_root(environ=environ, platform="darwin", home=tmp_path) is None


def test_pack_root_reads_the_running_platform_and_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no arguments it reads ``sys.platform`` and ``os.environ`` (by monkeypatch)."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "win"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(sys, "platform", "win32")
    assert gpu_pack.pack_root() == tmp_path / "win" / "Clearwater" / "gpu-pack"
    monkeypatch.setattr(sys, "platform", "linux")
    assert gpu_pack.pack_root() == tmp_path / "xdg" / "clearwater" / "gpu-pack"
    monkeypatch.setattr(sys, "platform", "darwin")
    assert gpu_pack.pack_root() is None


def test_the_app_folder_names_match_config_paths() -> None:
    """The loader repeats ``config.paths``'s folder names (it imports only the stdlib)."""
    assert gpu_pack.WINDOWS_APP_FOLDER == config_paths.WINDOWS_FOLDER_NAME
    assert gpu_pack.POSIX_APP_FOLDER == config_paths.POSIX_FOLDER_NAME


# load(): found, absent, rejected.


def test_a_valid_pack_is_loaded(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """Found: ``site-packages`` first on ``sys.path``, one ``loaded`` line, nothing written."""
    root = tmp_path / "gpu-pack"
    folder = make_pack(root)
    site = folder / gpu_pack.SITE_PACKAGES_NAME
    before = snapshot(root)
    with caplog.at_level(logging.INFO, logger="clearwater.gpu_pack"):
        status = gpu_pack.load(root)
    assert status.outcome == "loaded"
    assert status.site_packages == site
    assert sys.path[0] == str(site)
    assert sys.path.count(str(site)) == 1
    assert [r.getMessage() for r in caplog.records] == ["gpu pack 14.2.0-cu12: loaded"]
    assert snapshot(root) == before  # the pack is read-only to the loader
    gpu_pack.load(root)
    assert sys.path.count(str(site)) == 1  # a second load does not add it twice


def test_the_dll_folders_are_added_on_windows(
    tmp_path: Path, isolated: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """win32: each ``site-packages/nvidia/*/bin`` is added (D2); nothing else."""
    monkeypatch.setattr(sys, "platform", "win32")
    folder = make_pack(tmp_path)
    nvidia = folder / gpu_pack.SITE_PACKAGES_NAME / "nvidia"
    expected = [nvidia / lib / "bin" for lib in sorted(NVIDIA_LIBS)]
    status = gpu_pack.load(tmp_path)
    assert status.outcome == "loaded"
    assert list(status.dll_directories) == expected
    assert isolated == [str(p) for p in expected]
    assert len(gpu_pack._DLL_HANDLES) == len(expected)  # kept for the process's life


def test_no_dll_folder_is_added_on_linux(
    tmp_path: Path, isolated: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Off Windows the loader never calls ``os.add_dll_directory``."""
    monkeypatch.setattr(sys, "platform", "linux")
    make_pack(tmp_path)
    status = gpu_pack.load(tmp_path)
    assert status.outcome == "loaded"
    assert status.dll_directories == ()
    assert isolated == []


def test_a_failing_dll_folder_rejects_the_pack(
    tmp_path: Path, isolated: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """An ``os.add_dll_directory`` failure: rejected, the folders already added removed."""
    monkeypatch.setattr(sys, "platform", "win32")
    real = vars(os)["add_dll_directory"]  # the isolated fixture's recorder, on any platform
    calls = {"n": 0}

    def flaky(folder: str) -> Any:
        calls["n"] += 1
        if calls["n"] == 3:
            raise OSError("refused")
        return real(folder)

    monkeypatch.setattr(os, "add_dll_directory", flaky)
    make_pack(tmp_path)
    path_before = list(sys.path)
    status = gpu_pack.load(tmp_path)
    assert status.outcome == "rejected"
    assert status.reason == "DLL folder nvidia/cuda_runtime/bin: OSError"
    assert isolated == []  # the two added before the failure were closed again
    assert sys.path == path_before


@pytest.mark.parametrize("root_kind", ["missing", "empty", "none"])
def test_no_pack_is_absent_and_changes_nothing(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture, root_kind: str
) -> None:
    """Absent: no root, an empty root, or no root on this platform; nothing created."""
    root: Path | None = {
        "missing": tmp_path / "missing",
        "empty": tmp_path,
        "none": None,
    }[root_kind]
    before = list(sys.path)
    with caplog.at_level(logging.INFO, logger="clearwater.gpu_pack"):
        status = gpu_pack.load(root)
    assert status.outcome == "absent"
    assert status.line == "gpu pack 14.2.0-cu12: absent"
    assert [r.getMessage() for r in caplog.records] == [status.line]
    assert sys.path == before
    assert isolated == []
    assert not (tmp_path / "missing").exists()
    assert list(tmp_path.iterdir()) == []


def test_a_pack_under_another_stamp_is_absent(tmp_path: Path, isolated: list[str]) -> None:
    """Wrong stamp folder: an older pack is not this build's pack."""
    folder = make_pack(tmp_path)
    folder.rename(tmp_path / "14.1.0-cu12")
    status = gpu_pack.load(tmp_path)
    assert status.outcome == "absent"
    assert isolated == []


def _rejected(tmp_path: Path, folder: Path, reason: str, caplog: pytest.LogCaptureFixture) -> None:
    """Load ``tmp_path`` and assert a rejection with ``reason`` that changes nothing."""
    before = list(sys.path)
    with caplog.at_level(logging.INFO, logger="clearwater.gpu_pack"):
        status = gpu_pack.load(tmp_path)
    assert status.outcome == "rejected"
    assert status.reason == reason
    assert status.line == f"gpu pack 14.2.0-cu12: rejected: {reason}"
    assert [r.getMessage() for r in caplog.records] == [status.line]
    assert sys.path == before
    assert str(folder / gpu_pack.SITE_PACKAGES_NAME) not in sys.path


def test_a_manifest_naming_another_stamp_is_rejected(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """Wrong stamp inside the manifest."""
    folder = make_pack(tmp_path)
    edit_manifest(folder, lambda d: d.update(stamp="14.1.0-cu12"))
    _rejected(tmp_path, folder, "manifest stamp '14.1.0-cu12', expected '14.2.0-cu12'", caplog)
    assert isolated == []


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (lambda d: d.update(format=2), "manifest format 2, expected 1"),
        (lambda d: d.update(format=True), "manifest format True, expected 1"),
        (lambda d: d.pop("distributions"), "manifest malformed: no distributions list"),
        (
            lambda d: entry(d, "cuda-pathfinder").pop("record_sha256"),
            "manifest malformed: a distribution entry lacks a string field",
        ),
        (
            lambda d: entry(d, "nvidia-cufft-cu12").update(version="11.4.1.5"),
            "nvidia-cufft-cu12 version 11.4.1.5, expected 11.4.1.4",
        ),
        (
            lambda d: entry(d, "nvidia-cublas-cu12").update(wheel_sha256="0" * 64),
            "nvidia-cublas-cu12 wheel nvidia_cublas_cu12-12.9.2.10-py3-none-win_amd64.whl"
            " with that sha256 is not in the lock",
        ),
        (
            lambda d: entry(d, "cupy-cuda12x").update(wheel="cupy_cuda12x-14.2.0-x.whl"),
            "cupy-cuda12x wheel cupy_cuda12x-14.2.0-x.whl with that sha256 is not in the lock",
        ),
        (
            lambda d: entry(d, "nvidia-curand-cu12").update(record_sha256="f" * 64),
            "nvidia-curand-cu12 RECORD sha256 mismatch",
        ),
    ],
    ids=[
        "format",
        "format-bool",
        "no-list",
        "lacks-field",
        "version",
        "wheel-hash",
        "wheel-name",
        "record",
    ],
)
def test_a_tampered_manifest_is_rejected(
    tmp_path: Path,
    isolated: list[str],
    caplog: pytest.LogCaptureFixture,
    change: Any,
    reason: str,
) -> None:
    """Tampered manifest: each field the check reads, changed alone."""
    folder = make_pack(tmp_path)
    edit_manifest(folder, change)
    _rejected(tmp_path, folder, reason, caplog)
    assert isolated == []


def test_a_changed_record_file_is_rejected(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """The installed ``RECORD`` changed after the manifest was written (a partial reinstall)."""
    folder = make_pack(tmp_path)
    locked = {d.name: d for d in gpu_pack.LOCKED_DISTRIBUTIONS}["nvidia-cusolver-cu12"]
    record = folder / gpu_pack.SITE_PACKAGES_NAME / locked.dist_info_name / "RECORD"
    record.write_text("changed\n", encoding="utf-8")
    _rejected(tmp_path, folder, "nvidia-cusolver-cu12 RECORD sha256 mismatch", caplog)


def test_unreadable_or_missing_manifest_is_rejected(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """No manifest (an interrupted install), then a manifest that is not JSON."""
    folder = make_pack(tmp_path)
    manifest = folder / gpu_pack.MANIFEST_NAME
    manifest.unlink()
    _rejected(tmp_path, folder, "no manifest.json", caplog)
    caplog.clear()
    manifest.write_text("{not json", encoding="utf-8")
    _rejected(tmp_path, folder, "manifest.json unreadable: JSONDecodeError", caplog)
    caplog.clear()
    manifest.write_text("[]", encoding="utf-8")
    _rejected(tmp_path, folder, "manifest malformed: not an object", caplog)


def test_a_missing_site_packages_is_rejected(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """The manifest without the installed folder."""
    folder = make_pack(tmp_path)
    site = folder / gpu_pack.SITE_PACKAGES_NAME
    site.rename(folder / "elsewhere")
    _rejected(tmp_path, folder, "no site-packages folder", caplog)


def test_a_missing_distribution_is_rejected(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """Missing from the manifest, then present in it but not installed."""
    folder = make_pack(tmp_path)
    original = (folder / gpu_pack.MANIFEST_NAME).read_text(encoding="utf-8")

    def drop(document: dict[str, Any]) -> None:
        document["distributions"].remove(entry(document, "nvidia-nvjitlink-cu12"))

    edit_manifest(folder, drop)
    _rejected(tmp_path, folder, "missing distribution nvidia-nvjitlink-cu12", caplog)
    caplog.clear()
    (folder / gpu_pack.MANIFEST_NAME).write_text(original, encoding="utf-8")
    locked = {d.name: d for d in gpu_pack.LOCKED_DISTRIBUTIONS}["cuda-pathfinder"]
    (folder / gpu_pack.SITE_PACKAGES_NAME / locked.dist_info_name / "RECORD").unlink()
    _rejected(tmp_path, folder, "cuda-pathfinder RECORD missing", caplog)


def test_an_extra_or_duplicated_distribution_is_rejected(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """The set must be exactly the lock's eleven."""
    folder = make_pack(tmp_path)
    original = (folder / gpu_pack.MANIFEST_NAME).read_text(encoding="utf-8")

    def extra(document: dict[str, Any]) -> None:
        row = dict(entry(document, "cuda-pathfinder"), name="fastrlock")
        document["distributions"].append(row)

    edit_manifest(folder, extra)
    _rejected(tmp_path, folder, "unexpected distribution fastrlock", caplog)
    caplog.clear()
    (folder / gpu_pack.MANIFEST_NAME).write_text(original, encoding="utf-8")

    def duplicate(document: dict[str, Any]) -> None:
        document["distributions"].append(dict(entry(document, "cuda-pathfinder")))

    edit_manifest(folder, duplicate)
    _rejected(tmp_path, folder, "duplicate distribution cuda-pathfinder", caplog)
    caplog.clear()
    (folder / gpu_pack.MANIFEST_NAME).write_text(original, encoding="utf-8")

    def non_ascii(document: dict[str, Any]) -> None:
        document["distributions"].append(dict(entry(document, "cuda-pathfinder"), name="cupyé"))

    edit_manifest(folder, non_ascii)
    _rejected(tmp_path, folder, "unexpected distribution cupy\\xe9", caplog)  # ASCII-safe


def test_a_reason_is_always_one_line(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """Reviewer A r2 #12: newline, tab and CR in manifest text are escaped, not logged raw."""
    folder = make_pack(tmp_path)

    def control(document: dict[str, Any]) -> None:
        name = "cupy\nsecond log line\t\r\x7f"
        document["distributions"].append(dict(entry(document, "cuda-pathfinder"), name=name))

    edit_manifest(folder, control)
    reason = "unexpected distribution cupy\\x0asecond log line\\x09\\x0d\\x7f"
    _rejected(tmp_path, folder, reason, caplog)
    assert all(ch.isprintable() for ch in caplog.records[0].getMessage())


def _refusing(monkeypatch: pytest.MonkeyPatch, method: str, target: Path, error: OSError) -> None:
    """Make ``Path.<method>()`` raise ``error`` for ``target`` alone (a locked folder or file)."""
    real = getattr(Path, method)

    def refuse(self: Path, *args: Any, **kwargs: Any) -> Any:
        if self == target:
            raise error
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, method, refuse)


@pytest.mark.parametrize(
    ("method", "where", "reason"),
    [
        ("is_dir", ".", "pack unreadable: PermissionError"),
        ("is_file", "manifest.json", "pack unreadable: PermissionError"),
        ("is_dir", "site-packages", "pack unreadable: PermissionError"),
        (
            "is_file",
            "site-packages/cupy_cuda12x-14.2.0.dist-info/RECORD",
            "pack unreadable: PermissionError",
        ),
        ("is_dir", "site-packages/nvidia/cufft/bin", "DLL folders unreadable: PermissionError"),
    ],
)
def test_a_file_system_error_is_a_rejection_not_an_exception(
    tmp_path: Path,
    isolated: list[str],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    where: str,
    reason: str,
) -> None:
    """Reviewer A r2 #9: an existence or type check that raises means the CPU path, not a crash."""
    monkeypatch.setattr(sys, "platform", "win32")
    folder = make_pack(tmp_path)
    target = folder if where == "." else folder / where
    _refusing(monkeypatch, method, target, PermissionError(13, "Access is denied"))
    _rejected(tmp_path, folder, reason, caplog)
    assert isolated == []


def test_an_unreadable_record_is_rejected(
    tmp_path: Path,
    isolated: list[str],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A RECORD that exists but cannot be read is not reported as missing."""
    folder = make_pack(tmp_path)
    record = folder / "site-packages" / locked_named("nvidia-cufft-cu12").dist_info_name / "RECORD"
    for method in ("read_bytes", "open"):  # however the loader reads it
        _refusing(monkeypatch, method, record, PermissionError(13, "locked"))
    _rejected(tmp_path, folder, "nvidia-cufft-cu12 RECORD unreadable: PermissionError", caplog)


# The cheap check at every start-up (CHARC's ruling 2 on Reviewer A r2, with #7).


def _site(folder: Path) -> Path:
    """Return a pack folder's ``site-packages``."""
    return folder / gpu_pack.SITE_PACKAGES_NAME


def test_a_clean_pack_passes_the_cheap_and_the_full_check(
    tmp_path: Path, isolated: list[str]
) -> None:
    """The synthetic pack is clean: no problem with or without hashing."""
    folder = make_pack(tmp_path)
    assert gpu_pack.check_pack(folder) is None
    assert list(gpu_pack.pack_problems(folder, full=True, tags=WINDOWS_TAGS)) == []


def test_cancel_hook_default_and_cheap_path_are_unchanged(tmp_path, isolated):
    """Omitting the hook preserves the full result; cheap checks never consult it."""
    folder = make_pack(tmp_path)
    baseline = list(gpu_pack.pack_problems(folder, full=True, tags=WINDOWS_TAGS))
    assert (
        list(gpu_pack.pack_problems(folder, full=True, tags=WINDOWS_TAGS, cancelled=None))
        == baseline
    )

    def forbidden():
        pytest.fail("cheap path consulted cancellation")

    assert list(gpu_pack.pack_problems(folder, tags=WINDOWS_TAGS, cancelled=forbidden)) == []
    assert gpu_pack.check_pack(folder) is None


def test_cancel_hook_stops_before_second_file_hash(tmp_path, isolated, monkeypatch):
    """A flag set during one file's hash prevents every later file hash."""
    folder = make_pack(tmp_path)
    digest = gpu_pack._file_digest
    hashes = []

    def observed(path):
        hashes.append(path)
        return digest(path)

    monkeypatch.setattr(gpu_pack, "_file_digest", observed)
    with pytest.raises(gpu_pack.PackCheckCancelled):
        list(
            gpu_pack.pack_problems(
                folder, full=True, tags=WINDOWS_TAGS, cancelled=lambda: bool(hashes)
            )
        )
    assert len(hashes) == 1


def test_cancel_hook_escapes_problem_conversion(tmp_path, isolated):
    """Cancellation is an exception, never a 'pack check failed' problem string."""
    folder = make_pack(tmp_path)
    problems = []
    with pytest.raises(gpu_pack.PackCheckCancelled):
        for problem in gpu_pack.pack_problems(
            folder, full=True, tags=WINDOWS_TAGS, cancelled=lambda: True
        ):
            problems.append(problem)
    assert problems == []


def test_a_listed_file_that_is_missing_is_rejected(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """(a) A file that a RECORD lists is gone (a partial install or a clean-up tool)."""
    folder = make_pack(tmp_path)
    (_site(folder) / "cupyx" / "__init__.py").unlink()
    _rejected(tmp_path, folder, "cupy-cuda12x file cupyx/__init__.py missing", caplog)


def test_a_listed_file_of_another_size_is_rejected(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """(a) A listed file whose size is not RECORD's (a truncated download)."""
    folder = make_pack(tmp_path)
    dll = _site(folder) / "nvidia" / "cufft" / "bin" / "cufft64.dll"
    dll.write_bytes(dll.read_bytes()[:-1])
    reason = "nvidia-cufft-cu12 file nvidia/cufft/bin/cufft64.dll size 6, RECORD says 7"
    _rejected(tmp_path, folder, reason, caplog)


def test_a_listed_folder_where_a_file_should_be_is_rejected(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """(a) The listed name exists but is a folder."""
    folder = make_pack(tmp_path)
    path = _site(folder) / "cuda" / "pathfinder" / "__init__.py"
    path.unlink()
    path.mkdir()
    reason = "cuda-pathfinder file cuda/pathfinder/__init__.py is not a file"
    _rejected(tmp_path, folder, reason, caplog)


def test_a_row_without_a_size_is_checked_for_existence_only(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """(a) A size-less row (RECORD's own) needs only its file: present passes, absent fails."""
    folder = make_pack(tmp_path)
    (_site(folder) / "cupy" / "extra.py").write_bytes(b"any size at all")
    add_record_rows(folder, "cupy-cuda12x", ["cupy/extra.py,,", "cupy/gone.py,,"])
    _rejected(tmp_path, folder, "cupy-cuda12x file cupy/gone.py missing", caplog)


def test_the_cheap_check_hashes_no_listed_file(
    tmp_path: Path, isolated: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """No hashing at start-up: a same-size content change passes the cheap check only."""
    folder = make_pack(tmp_path)
    (_site(folder) / "cupy" / "__init__.py").write_bytes(b"# CUPY\n")  # the same 7 bytes

    def forbidden(path: object) -> bytes:
        raise AssertionError(f"the cheap check hashed {path}")

    monkeypatch.setattr(gpu_pack, "_file_digest", forbidden, raising=False)
    assert gpu_pack.check_pack(folder) is None


MALFORMED_8 = "RECORD malformed: row 8:"
NOT_ALLOWED = "RECORD row path not allowed ("
TRAILING = "a part ending in '.' or a space"


@pytest.mark.parametrize(
    ("row", "reason"),
    [
        ("../escape.py,,", "RECORD row outside site-packages: ../escape.py"),
        ("/abs/olute.py,,", "RECORD row outside site-packages: /abs/olute.py"),
        ("C:/drive.py,,", "RECORD row outside site-packages: C:/drive.py"),
        ("cupy/a.py,sha256=x", "RECORD malformed: row 8: not 3 fields"),
        ("cupy/a.py,sha256=x,big", "RECORD malformed: row 8: a size not of 1-20 digits"),
        # Reviewer A r3 #4: one row per probe, each a rejection with its reason
        (".,,1", "RECORD row path not allowed (an empty or '.' part): ."),
        ("cupy/a.py\x00,,1", "RECORD malformed: row 8: a NUL character"),
        ("cupy/a.py,," + "9" * 5000, "RECORD malformed: row 8: a size not of 1-20 digits"),
        ("cupy/a.py,not-a-hash,1", f"{MALFORMED_8} a hash not of the form algorithm=base64"),
        # Reviewer A r3 #5: Windows spellings that resolve to another name
        (
            "file:stream,,1",
            f"{NOT_ALLOWED}a ':' (a drive or an alternate data stream)): file:stream",
        ),
        ("cupy/__init__.py.,,7", f"{NOT_ALLOWED}{TRAILING}): cupy/__init__.py."),
        ("cupy/__init__.py ,,7", f"{NOT_ALLOWED}{TRAILING}): cupy/__init__.py "),
        ("cupy//__init__.py,,7", f"{NOT_ALLOWED}an empty or '.' part): cupy//__init__.py"),
    ],
    ids=[
        "dotdot",
        "absolute",
        "drive",
        "two-fields",
        "bad-size",
        "dot-row",
        "nul",
        "5000-digit-size",
        "hash-form",
        "ads",
        "trailing-dot",
        "trailing-space",
        "empty-part",
    ],
)
def test_a_malformed_or_escaping_record_row_is_rejected(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture, row: str, reason: str
) -> None:
    """(a) A row that is not ``path,hash,size`` or names a file outside ``site-packages``."""
    folder = make_pack(tmp_path)
    add_record_rows(folder, "cupy-cuda12x", [row])
    _rejected(tmp_path, folder, f"cupy-cuda12x {reason}", caplog)


@pytest.mark.parametrize(
    ("planted", "name"),
    [
        ("numpy/__init__.py", "numpy"),
        ("shadow.py", "shadow.py"),
        ("zz-startup.pth", "zz-startup.pth"),
        ("stray.dist-info/RECORD", "stray.dist-info"),
    ],
    ids=["package", "module", "pth", "dist-info"],
)
def test_an_unlisted_top_level_entry_is_rejected(
    tmp_path: Path,
    isolated: list[str],
    caplog: pytest.LogCaptureFixture,
    planted: str,
    name: str,
) -> None:
    """(b) Nothing that no RECORD owns may sit in ``site-packages`` (it could shadow numpy)."""
    folder = make_pack(tmp_path)
    path = _site(folder) / planted
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    _rejected(tmp_path, folder, f"unlisted entry in site-packages: {name}", caplog)


def test_ownership_is_the_first_component_of_any_record_row(
    tmp_path: Path, isolated: list[str]
) -> None:
    """(b) ``nvidia`` is owned by eight RECORDs; an unlisted file INSIDE an owned folder passes.

    The cheap (start-up) check looks at the top level only; a nested extra file cannot shadow
    a top-level module. The FULL check (``--verify``) does list it, as an unlisted file (Q2;
    ``test_the_full_verify_lists_every_unlisted_nested_file``).
    """
    folder = make_pack(tmp_path)
    (_site(folder) / "cupy" / "__pycache__").mkdir()
    (_site(folder) / "cupy" / "__pycache__" / "x.pyc").write_bytes(b"")
    assert gpu_pack.check_pack(folder) is None


def test_ownership_ignores_case_where_the_platform_does(
    tmp_path: Path, isolated: list[str]
) -> None:
    """(b) On Windows ``CUPY`` and ``cupy`` are one folder; elsewhere they are two."""
    folder = make_pack(tmp_path)
    (_site(folder) / "cupy").rename(_site(folder) / "CuPy")
    reason = gpu_pack.check_pack(folder)
    if os.path.normcase("A") == "a":
        assert reason is None
    else:
        assert reason == "cupy-cuda12x file cupy/__init__.py missing"


def _linux_cupy(locked: gpu_pack.LockedDistribution) -> str:
    """Pick the Linux x86-64 CuPy wheel, the Windows wheel for everything else."""
    if locked.name == "cupy-cuda12x":
        return "cupy_cuda12x-14.2.0-cp312-cp312-manylinux2014_x86_64.whl"
    return _windows_wheel(locked)


def test_a_locked_wheel_for_another_platform_is_rejected(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """(c) #7: the Linux CuPy wheel, installed whole and with a true manifest, on Windows."""
    folder = make_pack(tmp_path, choose=_linux_cupy)
    reason = "cupy-cuda12x wheel tag cp312-cp312-manylinux2014_x86_64 is not for win_amd64"
    _rejected(tmp_path, folder, reason, caplog)


def test_a_wheel_file_without_a_usable_tag_is_rejected(
    tmp_path: Path, isolated: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """(c) The WHEEL file gone, then present with no ``Tag:`` line."""
    folder = make_pack(tmp_path)
    wheel = _site(folder) / locked_named("nvidia-curand-cu12").dist_info_name / "WHEEL"
    wheel.unlink()
    _rejected(tmp_path, folder, "nvidia-curand-cu12 WHEEL missing", caplog)
    caplog.clear()
    wheel.write_text("Wheel-Version: 1.0\n", encoding="utf-8")
    _rejected(tmp_path, folder, "nvidia-curand-cu12 WHEEL has no Tag line", caplog)


@pytest.mark.parametrize(
    ("tag", "interpreter", "platform", "fits"),
    [
        ("cp312-cp312-win_amd64", "cp312", "win_amd64", True),
        ("py3-none-win_amd64", "cp312", "win_amd64", True),
        ("py3-none-any", "cp312", "linux_x86_64", True),
        ("py2.py3-none-any", "cp312", "win_amd64", True),
        ("cp312-abi3-win_amd64", "cp312", "win_amd64", True),
        ("cp312-cp312-manylinux2014_x86_64", "cp312", "linux_x86_64", True),
        ("py3-none-manylinux_2_27_x86_64", "cp312", "linux_x86_64", True),
        ("cp312-cp312-manylinux2014_x86_64", "cp312", "win_amd64", False),
        ("py3-none-manylinux_2_27_aarch64", "cp312", "linux_x86_64", False),
        ("cp312-cp312-win_amd64", "cp312", "win_arm64", False),
        ("cp311-cp311-win_amd64", "cp312", "win_amd64", False),
        ("py2-none-any", "cp312", "win_amd64", False),
        ("not-a-tag", "cp312", "win_amd64", False),
    ],
)
def test_tag_fits(tag: str, interpreter: str, platform: str, fits: bool) -> None:
    """The platform rule, by injection, for Windows and Linux machines."""
    assert gpu_pack.tag_fits(tag, interpreter, platform) is fits


def test_platform_tags_name_the_running_interpreter_and_platform() -> None:
    """``cp312`` and, on 64-bit Windows, ``win_amd64`` (the pack's locked wheel)."""
    interpreter, platform = gpu_pack.platform_tags()
    assert interpreter == f"cp{sys.version_info.major}{sys.version_info.minor}"
    assert platform == sysconfig.get_platform().replace("-", "_").replace(".", "_").lower()
    if sysconfig.get_platform() == "win-amd64":
        assert platform == "win_amd64"


def test_an_os_error_during_the_walk_is_a_rejection(
    tmp_path: Path,
    isolated: list[str],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A listed file that cannot be examined, then a ``site-packages`` that cannot be listed."""
    folder = make_pack(tmp_path)
    target = os.path.join(_site(folder), "cupy", "__init__.py")
    real_stat = os.stat

    def stat(path: Any, *args: Any, **kwargs: Any) -> os.stat_result:
        if os.fspath(path) == target:
            raise PermissionError(13, "Access is denied")
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", stat)
    reason = "cupy-cuda12x file cupy/__init__.py unreadable: PermissionError"
    _rejected(tmp_path, folder, reason, caplog)
    monkeypatch.setattr(os, "stat", real_stat)
    caplog.clear()
    real_scandir = os.scandir
    site = os.fspath(_site(folder))

    def scandir(path: Any = ".") -> Any:
        if os.fspath(path) == site:
            raise PermissionError(13, "Access is denied")
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", scandir)
    _rejected(tmp_path, folder, "pack unreadable: PermissionError", caplog)


def test_any_exception_in_the_walk_is_a_rejection_at_start_up_and_in_verify(
    tmp_path: Path,
    isolated: list[str],
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reviewer A r3 #4: an exception no row check foresaw ends the walk as ONE reason."""
    folder = make_pack(tmp_path)

    def broken(*_: Any, **__: Any) -> Any:
        raise IndexError("an input no validation foresaw")

    monkeypatch.setattr(gpu_pack, "_row_problems", broken)
    _rejected(tmp_path, folder, "pack check failed: IndexError", caplog)
    status, lines = _verify(folder, capsys)
    assert status == 1
    assert "pack check failed: IndexError" in "\n".join(lines)


def test_an_unlistable_nvidia_folder_rejects_the_pack(
    tmp_path: Path,
    isolated: list[str],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reviewer A r3 #7: listing ``nvidia`` refused is a rejection, not "no DLL folders"."""
    monkeypatch.setattr(sys, "platform", "win32")
    folder = make_pack(tmp_path)
    nvidia = os.fspath(_site(folder) / "nvidia")
    real_scandir = os.scandir

    def scandir(path: Any = ".") -> Any:
        if os.fspath(path) == nvidia:
            raise PermissionError(13, "Access is denied")
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", scandir)
    _rejected(tmp_path, folder, "DLL folders unreadable: PermissionError", caplog)
    assert isolated == []


def test_a_failing_non_ascii_dll_folder_is_named_in_ascii(
    tmp_path: Path, isolated: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reviewer A r3 #8: the DLL-folder failure reason escapes the folder name."""
    monkeypatch.setattr(sys, "platform", "win32")
    folder = make_pack(tmp_path)
    (_site(folder) / "nvidia" / "é" / "bin").mkdir(parents=True)  # a tool-made folder
    real = vars(os)["add_dll_directory"]

    def refuse_it(path: str) -> Any:
        if "é" in path:
            raise OSError("refused")
        return real(path)

    monkeypatch.setattr(os, "add_dll_directory", refuse_it)
    status = gpu_pack.load(tmp_path)
    assert status.outcome == "rejected"
    assert status.reason == "DLL folder nvidia/\\xe9/bin: OSError"
    assert status.line.isascii()


# build.py --verify: the full check for a hand-filled pack.


def _verify(folder: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, list[str]]:
    """Run ``build.py --verify <folder>`` in this process; return its status and lines."""
    status = build.main(["--verify", str(folder)])
    return status, capsys.readouterr().out.splitlines()


def test_verify_passes_a_clean_pack_with_one_line(
    tmp_path: Path, isolated: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """Exit 0 and one summary line naming the rows and files checked."""
    folder = make_pack(tmp_path)
    status, lines = _verify(folder, capsys)
    assert status == 0
    (line,) = lines
    assert line.startswith(f"verify {folder}: PASS (11 distributions; ")
    rows = sum(1 + len(_payload(d)) + 3 for d in gpu_pack.LOCKED_DISTRIBUTIONS)
    assert f"{rows} RECORD rows" in line


def test_verify_lists_every_mismatch(
    tmp_path: Path, isolated: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """Content changed (same size), size changed, a file missing, an unlisted entry: all four."""
    folder = make_pack(tmp_path)
    site = _site(folder)
    (site / "cupy" / "__init__.py").write_bytes(b"# CUPY\n")  # same size, other content
    (site / "nvidia" / "curand" / "bin" / "curand64.dll").write_bytes(b"MZcurand+")
    (site / "cuda" / "pathfinder" / "__init__.py").unlink()
    (site / "numpy").mkdir()
    status, lines = _verify(folder, capsys)
    assert status == 1
    assert lines[0] == f"verify {folder}: FAIL (5 problems)"
    assert lines[1:] == [
        "  cupy-cuda12x file cupy/__init__.py sha256 mismatch",
        "  cuda-pathfinder file cuda/pathfinder/__init__.py missing",
        "  nvidia-curand-cu12 file nvidia/curand/bin/curand64.dll size 9, RECORD says 8",
        "  nvidia-curand-cu12 file nvidia/curand/bin/curand64.dll sha256 mismatch",
        "  unlisted entry in site-packages: numpy",
    ]


def test_verify_also_runs_the_start_up_checks(
    tmp_path: Path, isolated: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """The manifest against the lock (d) and the platform tags (c) are part of the full check."""
    folder = make_pack(tmp_path, choose=_linux_cupy)
    edit_manifest(folder, lambda d: entry(d, "nvidia-cufft-cu12").update(version="0"))
    status, lines = _verify(folder, capsys)
    assert status == 1
    assert lines[1:] == [
        "  cupy-cuda12x wheel tag cp312-cp312-manylinux2014_x86_64 is not for win_amd64",
        "  nvidia-cufft-cu12 version 0, expected 11.4.1.4",
    ]


def test_verify_flags_a_listed_file_without_a_hash(
    tmp_path: Path, isolated: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """Only RECORD's own row may lack a hash in the full check (the cheap one allows it)."""
    folder = make_pack(tmp_path)
    (_site(folder) / "cupy" / "extra.py").write_bytes(b"x")
    add_record_rows(folder, "cupy-cuda12x", ["cupy/extra.py,,1"])
    assert gpu_pack.check_pack(folder) is None
    status, lines = _verify(folder, capsys)
    assert status == 1
    assert lines[1:] == ["  cupy-cuda12x file cupy/extra.py has no hash in RECORD"]


@pytest.mark.parametrize("other", [["--form", "onedir"], ["--write-manifest", "x"]])
def test_verify_is_exclusive_with_the_other_actions(
    tmp_path: Path, other: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """``--verify`` with ``--form`` or ``--write-manifest`` is a usage error (exit 2)."""
    with pytest.raises(SystemExit) as raised:
        build.parse_args(["--verify", str(tmp_path), *other])
    assert raised.value.code == 2
    assert "not allowed with argument" in capsys.readouterr().err


# activate() (D4).


def test_activate_does_nothing_in_a_source_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Not frozen: no check, no line, no ``sys.path`` change; returns None."""
    monkeypatch.delattr(sys, "frozen", raising=False)

    def forbidden(root: Path | None) -> gpu_pack.PackStatus:
        raise AssertionError("load() must not run when not frozen")

    monkeypatch.setattr(gpu_pack, "load", forbidden)
    assert gpu_pack.activate() is None


@pytest.mark.parametrize("outcome", ["loaded", "absent", "rejected"])
def test_activation_status_exposes_last_outcome_without_io(monkeypatch, outcome):
    """Removal can consult the immutable process outcome without rechecking any pack."""
    monkeypatch.setattr(gpu_pack, "_ACTIVATION_STATUS", None, raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(gpu_pack, "pack_root", lambda: None)
    status = gpu_pack.PackStatus(gpu_pack.STAMP, outcome)
    monkeypatch.setattr(gpu_pack, "load", lambda _: status)
    assert gpu_pack.activate() is status
    monkeypatch.setattr(gpu_pack, "pack_root", lambda: pytest.fail("status getter performed I/O"))
    assert gpu_pack.activation_status() is status


def test_activate_loads_from_the_pack_root_when_frozen(
    tmp_path: Path, isolated: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Frozen: the pack under the platform's root (here a redirected one) is loaded."""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    root = tmp_path / "local" / "Clearwater" / "gpu-pack"
    status = gpu_pack.activate()
    assert status is not None and status.outcome == "absent"
    make_pack(root)
    status = gpu_pack.activate()
    assert status is not None and status.outcome == "loaded"
    assert sys.path[0] == str(root / gpu_pack.STAMP / gpu_pack.SITE_PACKAGES_NAME)


def test_a_frozen_activation_puts_the_pack_folder_first_in_site_prefixes(
    tmp_path: Path, isolated: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """CHARC's F-F ruling: ``getsitepackages()[0]`` is ``<pack>/site-packages``, exactly.

    The FOLDER is the prefix (never ``<pack>``); ``site.ENABLE_USER_SITE`` is unchanged; and
    ``sys.path`` gains the one pack entry only. A second activation adds nothing.
    """
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    root = tmp_path / "local" / "Clearwater" / "gpu-pack"
    make_pack(root)
    folder = root / gpu_pack.STAMP
    entry = str(folder / gpu_pack.SITE_PACKAGES_NAME)
    path_before, prefixes_before = list(sys.path), list(site.PREFIXES)
    user_site_before = site.ENABLE_USER_SITE
    status = gpu_pack.activate()
    assert status is not None and status.outcome == "loaded"
    assert [entry, *prefixes_before] == site.PREFIXES
    assert str(folder) not in site.PREFIXES
    if os.sep == "\\":  # the Windows spelling of getsitepackages() (P, P/Lib/site-packages)
        assert site.getsitepackages()[0] == entry
        assert site.getsitepackages()[1] == os.path.join(entry, "Lib", "site-packages")
    assert site.ENABLE_USER_SITE is user_site_before
    assert [p for p in sys.path if p not in path_before] == [entry]
    gpu_pack.activate()
    assert site.PREFIXES.count(entry) == 1
    assert sys.path.count(entry) == 1


@pytest.mark.skipif(os.name != "nt", reason="case and '/' fold to one folder on Windows only")
def test_another_spelling_of_the_pack_folder_is_replaced_not_kept(isolated: list[str]) -> None:
    """Reviewer A r4 #2, its exact input: a trailing-slash, upper-case, ``/`` spelling goes."""
    site.PREFIXES[:] = ["C:/PACK/site-packages/", "C:/bundle"]
    assert gpu_pack.add_site_prefix(Path("C:/pack/site-packages")) is True
    assert site.PREFIXES == ["C:\\pack\\site-packages", "C:/bundle"]
    assert gpu_pack.add_site_prefix(Path("C:/pack/site-packages")) is False
    assert site.PREFIXES == ["C:\\pack\\site-packages", "C:/bundle"]


def test_every_existing_equivalent_prefix_is_removed_before_the_one_canonical_entry(
    tmp_path: Path, isolated: list[str]
) -> None:
    """Reviewer A r4 #2: two equivalent duplicates already present (and the exact entry once
    more) all go; the canonical entry is first, once; the other prefixes keep their order."""
    folder = tmp_path / "pack" / "site-packages"
    entry = str(folder)
    doubled = str(tmp_path / "pack") + os.sep + os.sep + "site-packages"
    site.PREFIXES[:] = ["/bundle-a", entry + os.sep, entry, doubled, "/bundle-b", entry]
    prefixes = site.PREFIXES
    assert gpu_pack.add_site_prefix(folder) is True
    assert [entry, "/bundle-a", "/bundle-b"] == site.PREFIXES
    assert site.PREFIXES is prefixes  # changed in place
    assert gpu_pack.add_site_prefix(folder) is False
    assert [entry, "/bundle-a", "/bundle-b"] == site.PREFIXES


def test_a_source_run_leaves_site_prefixes_untouched(
    tmp_path: Path, isolated: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-F, the 1.0.0 lock: not frozen, ``activate()`` changes no ``site.PREFIXES``."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    make_pack(tmp_path / "local" / "Clearwater" / "gpu-pack")
    before = list(site.PREFIXES)
    assert gpu_pack.activate() is None
    assert before == site.PREFIXES


def test_a_rejected_pack_adds_no_site_prefix(
    tmp_path: Path, isolated: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-F: only a LOADED pack becomes a prefix."""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    folder = make_pack(tmp_path / "local" / "Clearwater" / "gpu-pack")
    (_site(folder) / "stray.pth").write_text("", encoding="utf-8")  # an unowned entry
    before = list(site.PREFIXES)
    status = gpu_pack.activate()
    assert status is not None and status.outcome == "rejected"
    assert before == site.PREFIXES


def test_the_full_verify_lists_every_unlisted_nested_file(
    tmp_path: Path, isolated: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """CHARC's Q2 ruling: ``--verify`` fails on a nested ``.pyc`` and ``.py`` no RECORD names.

    The start-up check stays top-level (both files sit inside the owned ``cupy``), so it still
    passes; ``__pycache__`` is not excluded.
    """
    folder = make_pack(tmp_path)
    cache = _site(folder) / "cupy" / "__pycache__"
    cache.mkdir()
    (cache / "__init__.cpython-312.pyc").write_bytes(b"pyc")
    (_site(folder) / "cupy" / "planted.py").write_text("# planted\n", encoding="utf-8")
    assert gpu_pack.check_pack(folder) is None
    status, lines = _verify(folder, capsys)
    assert status == 1
    text = "\n".join(lines)
    assert "unlisted file in site-packages: cupy/__pycache__/__init__.cpython-312.pyc" in text
    assert "unlisted file in site-packages: cupy/planted.py" in text


# The build script's manifest helper.


def test_the_manifest_helper_records_the_installed_wheel(tmp_path: Path) -> None:
    """One row per distribution: the matching locked wheel and the RECORD's sha256."""
    folder = make_pack(tmp_path)
    document = json.loads((folder / gpu_pack.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert document["format"] == 1 and document["stamp"] == "14.2.0-cu12"
    rows = {row["name"]: row for row in document["distributions"]}
    assert set(rows) == PACK_NAMES
    cupy = rows["cupy-cuda12x"]
    assert cupy["wheel"] == "cupy_cuda12x-14.2.0-cp312-cp312-win_amd64.whl"
    locked = {d.name: d for d in gpu_pack.LOCKED_DISTRIBUTIONS}["cupy-cuda12x"]
    assert (cupy["wheel"], cupy["wheel_sha256"]) in {(w[0], w[1]) for w in locked.wheels}
    record = folder / gpu_pack.SITE_PACKAGES_NAME / locked.dist_info_name / "RECORD"
    assert cupy["record_sha256"] == gpu_pack.file_sha256(record)
    assert rows["cuda-toolkit"]["wheel"] == "cuda_toolkit-12.9.2.0-py2.py3-none-any.whl"


def test_the_manifest_helper_refuses_a_folder_not_named_for_the_stamp(tmp_path: Path) -> None:
    """A hand-filled pack must land under this build's stamp."""
    with pytest.raises(ValueError, match=r"14\.2\.0-cu12"):
        build.write_manifest(tmp_path / "14.1.0-cu12")


def test_wheel_file_tags_expand_compressed_tag_sets() -> None:
    """``py2.py3-none-any`` is two tags; a platform wheel is one."""
    assert build.wheel_file_tags("cuda_toolkit-12.9.2.0-py2.py3-none-any.whl") == {
        "py2-none-any",
        "py3-none-any",
    }
    assert build.wheel_file_tags("cupy_cuda12x-14.2.0-cp312-cp312-win_amd64.whl") == {
        "cp312-cp312-win_amd64"
    }
    with pytest.raises(ValueError):
        build.wheel_file_tags("cupy.tar.gz")


def _symlink_or_skip(link: Path, target: Path, *, directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except OSError as error:
        pytest.skip(f"host refuses os.symlink: {error!r}")


def test_full_check_rejects_a_listed_file_symlink(tmp_path: Path, isolated: list[str]) -> None:
    folder = make_pack(tmp_path / "root")
    payload = folder / "site-packages/cupy/__init__.py"
    target = tmp_path / "original.py"
    payload.replace(target)
    _symlink_or_skip(payload, target)
    try:
        assert gpu_pack.check_pack(folder) is None
        assert any("link or reparse point" in p for p in gpu_pack.pack_problems(folder, full=True))
    finally:
        payload.unlink()


def test_full_check_rejects_a_symlinked_directory(tmp_path: Path, isolated: list[str]) -> None:
    folder = make_pack(tmp_path / "root")
    target = tmp_path / "empty"
    target.mkdir()
    link = folder / "site-packages/cupy/linked"
    _symlink_or_skip(link, target, directory=True)
    try:
        assert gpu_pack.check_pack(folder) is None
        assert any("link or reparse point" in p for p in gpu_pack.pack_problems(folder, full=True))
    finally:
        link.unlink()


@pytest.mark.skipif(sys.platform != "win32", reason="NTFS junctions are Windows-only")
def test_full_check_rejects_a_junction(tmp_path: Path, isolated: list[str]) -> None:
    import _winapi

    folder = make_pack(tmp_path / "root")
    target = tmp_path / "empty"
    target.mkdir()
    link = folder / "site-packages/cupy/junction"
    _winapi.CreateJunction(str(target), str(link))
    try:
        assert gpu_pack.check_pack(folder) is None
        assert any("link or reparse point" in p for p in gpu_pack.pack_problems(folder, full=True))
    finally:
        link.rmdir()


def test_full_check_uses_an_in_memory_manifest_without_reading_disk(
    tmp_path: Path, isolated: list[str]
) -> None:
    folder = make_pack(tmp_path)
    manifest = folder / "manifest.json"
    document = json.loads(manifest.read_text(encoding="utf-8"))
    manifest.unlink()
    assert list(gpu_pack.pack_problems(folder, full=True, manifest=document)) == []
    assert gpu_pack.check_pack(folder) == "no manifest.json"
    document["stamp"] = "wrong"
    assert "manifest stamp" in next(gpu_pack.pack_problems(folder, full=True, manifest=document))


@pytest.mark.parametrize("frozen", [False, True])
def test_activate_filters_only_the_cuda_path_userwarning_when_frozen(
    monkeypatch: pytest.MonkeyPatch, frozen: bool
) -> None:
    monkeypatch.setattr(sys, "frozen", frozen, raising=False)
    monkeypatch.setattr(gpu_pack, "pack_root", lambda: None)
    calls = []

    def load(root: Path | None) -> gpu_pack.PackStatus:
        calls.append(root)
        warnings.warn("CUDA path could not be detected. test", UserWarning, stacklevel=1)
        warnings.warn("unrelated warning", UserWarning, stacklevel=1)
        warnings.warn(
            "CUDA path could not be detected. other category", RuntimeWarning, stacklevel=1
        )
        return gpu_pack.PackStatus(gpu_pack.STAMP, "absent")

    monkeypatch.setattr(gpu_pack, "load", load)
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        before = list(warnings.filters)
        gpu_pack.activate()
        if frozen:
            assert [str(w.message) for w in seen] == [
                "unrelated warning",
                "CUDA path could not be detected. other category",
            ]
            assert calls == [None]
        else:
            assert warnings.filters == before
            assert calls == []
