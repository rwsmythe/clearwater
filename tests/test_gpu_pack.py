"""The GPU pack loader against synthetic pack folders under ``tmp_path`` (WP6.1, AD-33).

Parallel leg: no GPU, no footage, no real ``%LOCALAPPDATA%``. Every pack is built here with
the loader's layout; its ``manifest.json`` is written by the build script's helper
(``tools/package/build.py``), so the writer and the loader are checked against each other.
``os.add_dll_directory`` is always replaced by a recorder, so no test changes this process's
DLL search path.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import logging
import os
import sys
import tomllib
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
    """Import ``tools/package/build.py`` by its path (it is not a package)."""
    path = REPO_ROOT / "tools" / "package" / "build.py"
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
    names = [wheel for wheel, _ in locked.wheels]
    for name in names:
        if name.endswith("win_amd64.whl"):
            return name
    (pure,) = names
    return pure


def make_pack(root: Path) -> Path:
    """Fill ``root/<STAMP>`` like a hand-filled Windows pack and write its manifest.

    Args:
        root: The pack root.

    Returns:
        The pack folder.
    """
    folder = root / gpu_pack.STAMP
    site = folder / gpu_pack.SITE_PACKAGES_NAME
    for locked in gpu_pack.LOCKED_DISTRIBUTIONS:
        dist_info = site / locked.dist_info_name
        dist_info.mkdir(parents=True)
        (dist_info / "RECORD").write_text(f"{locked.name}/__init__.py,,\n", encoding="utf-8")
        wheel = _windows_wheel(locked)
        tags = sorted(build.wheel_file_tags(wheel))
        lines = ["Wheel-Version: 1.0"] + [f"Tag: {tag}" for tag in tags]
        (dist_info / "WHEEL").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for lib in NVIDIA_LIBS:
        (site / "nvidia" / lib / "bin").mkdir(parents=True)
    (site / "nvidia" / "cublas" / "include").mkdir()  # not a bin folder: never added
    build.write_manifest(folder)
    return folder


def edit_manifest(folder: Path, change: Any) -> None:
    """Apply ``change(document)`` to a pack's manifest and write it back."""
    path = folder / gpu_pack.MANIFEST_NAME
    document = json.loads(path.read_text(encoding="utf-8"))
    change(document)
    path.write_text(json.dumps(document), encoding="utf-8")


def entry(document: dict[str, Any], name: str) -> dict[str, Any]:
    """Return the manifest's entry for one distribution."""
    (found,) = [row for row in document["distributions"] if row["name"] == name]
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
            (w["url"].rsplit("/", 1)[1], w["hash"].removeprefix("sha256:"))
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
    real = os.add_dll_directory
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


def test_an_unreadable_record_is_rejected(
    tmp_path: Path,
    isolated: list[str],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A RECORD that exists but cannot be read is not reported as missing."""
    folder = make_pack(tmp_path)
    real = gpu_pack.file_sha256

    def refuse(path: Path) -> str:
        if path.parent.name.startswith("nvidia_cufft"):
            raise PermissionError("locked")
        return real(path)

    monkeypatch.setattr(gpu_pack, "file_sha256", refuse)
    _rejected(tmp_path, folder, "nvidia-cufft-cu12 RECORD unreadable: PermissionError", caplog)


# activate() (D4).


def test_activate_does_nothing_in_a_source_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Not frozen: no check, no line, no ``sys.path`` change; returns None."""
    monkeypatch.delattr(sys, "frozen", raising=False)

    def forbidden(root: Path | None) -> gpu_pack.PackStatus:
        raise AssertionError("load() must not run when not frozen")

    monkeypatch.setattr(gpu_pack, "load", forbidden)
    assert gpu_pack.activate() is None


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
    assert (cupy["wheel"], cupy["wheel_sha256"]) in locked.wheels
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
