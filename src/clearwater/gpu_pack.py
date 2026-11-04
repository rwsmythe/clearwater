"""The GPU pack loader: CuPy and the CUDA wheels from a per-user folder (WP6.1, AD-33).

A packaged (frozen) Clearwater never bundles CuPy or the NVIDIA wheels (the owner's D-C
amendment; spec N14). They may instead be installed, once, into a per-user folder, the *GPU
pack*::

    <pack root>/<stamp>/manifest.json
    <pack root>/<stamp>/site-packages/      cupy/, cupyx/, cuda/, nvidia/, *.dist-info/

:func:`pack_root` names the root for this platform. The stamp (:data:`STAMP`, for example
``14.2.0-cu12``) is the locked ``cupy-cuda12x`` version plus the CUDA major version.

At start-up, before anything imports ``cupy``, :func:`activate` checks the pack's manifest
against the lock (:data:`LOCKED_DISTRIBUTIONS`) and, when it passes, puts its
``site-packages`` at the front of ``sys.path``. On Windows it also adds each
``site-packages/nvidia/*/bin`` folder to the DLL search path (``os.add_dll_directory``), because
CuPy's library finder does not search ``sys.path`` for the CUDA DLLs. It logs one line:
``gpu pack <stamp>: loaded``, ``absent`` or ``rejected: <reason>``. An absent or rejected
pack changes nothing: the backend probe then reports the CPU path exactly as 1.0.0 does.

The loader only acts in a frozen build (``sys.frozen``); a source install takes CuPy from its
own environment (the ``gpu`` extra). It never writes, creates or deletes anything: the pack
folder is read-only to it. It imports only the standard library, so it can run first.

The manifest check guards against a partial, corrupt or wrong-version install, not against a
local attacker who can already write the user's own folder. It checks the manifest and each
distribution's ``RECORD`` file, not every file the ``RECORD`` lists (that is the installer's
job at install time).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

_LOG = logging.getLogger(__name__)

Outcome = Literal["loaded", "absent", "rejected"]
"""What the loader found: a valid pack, no pack, or a pack that failed a check."""

MANIFEST_NAME = "manifest.json"
"""The manifest's file name inside ``<pack root>/<stamp>/``."""

SITE_PACKAGES_NAME = "site-packages"
"""The folder inside ``<pack root>/<stamp>/`` that goes on ``sys.path``."""

MANIFEST_FORMAT = 1
"""The manifest format this loader reads."""

PACK_FOLDER_NAME = "gpu-pack"
"""The pack root's last folder name, inside the application's data folder."""

WINDOWS_APP_FOLDER = "Clearwater"
"""The application's folder name under ``%LOCALAPPDATA%`` (as ``config.paths`` names it)."""

POSIX_APP_FOLDER = "clearwater"
"""The application's folder name under ``$XDG_DATA_HOME`` (as ``config.paths`` names it)."""

CUPY_DISTRIBUTION = "cupy-cuda12x"
"""The CuPy distribution whose locked version (and CUDA major) names the stamp."""


@dataclass(frozen=True)
class LockedDistribution:
    """One distribution of the pack, at its ``uv.lock`` version, with the lock's wheels.

    Attributes:
        name: The distribution name as the lock spells it (``nvidia-cublas-cu12``).
        version: The locked version.
        wheels: Every locked wheel of that version: (file name, sha256 hex) pairs.
    """

    name: str
    version: str
    wheels: tuple[tuple[str, str], ...]

    @property
    def dist_info_name(self) -> str:
        """The installed metadata folder: ``<escaped name>-<version>.dist-info``."""
        return f"{re.sub(r'[-_.]+', '_', self.name)}-{self.version}.dist-info"


LOCKED_DISTRIBUTIONS: tuple[LockedDistribution, ...] = (
    LockedDistribution(
        "cupy-cuda12x",
        "14.2.0",
        (
            (
                "cupy_cuda12x-14.2.0-cp312-cp312-manylinux2014_aarch64.whl",
                "b74340aa7271f0f081f77e2e5107bac75af19b86df29213db7ada90e14428efe",
            ),
            (
                "cupy_cuda12x-14.2.0-cp312-cp312-manylinux2014_x86_64.whl",
                "f82141761f2c81905d49387464ae29438887956d99063381c93a1d5d1b7d32e8",
            ),
            (
                "cupy_cuda12x-14.2.0-cp312-cp312-win_amd64.whl",
                "c9571d3b5f2e65758137e210f7fb3c3b34767f0af6b6ca04035a244b6141ee12",
            ),
        ),
    ),
    LockedDistribution(
        "cuda-pathfinder",
        "1.8.3",
        (
            (
                "cuda_pathfinder-1.8.3-py3-none-any.whl",
                "e29e59829c297a7a5233bd9cc71094fc5bddbd076951482670178f9eade39b1f",
            ),
        ),
    ),
    LockedDistribution(
        "cuda-toolkit",
        "12.9.2.0",
        (
            (
                "cuda_toolkit-12.9.2.0-py2.py3-none-any.whl",
                "b54b8f2fd4200090b44843d48fc5411198e8b3e47a3db56e2518ab588c0ef1e0",
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-cublas-cu12",
        "12.9.2.10",
        (
            (
                "nvidia_cublas_cu12-12.9.2.10-py3-none-manylinux_2_27_aarch64.whl",
                "5572131a59c3eebeeb1c4c8144f772d49372c20124916e072a0e3fc30df421d5",
            ),
            (
                "nvidia_cublas_cu12-12.9.2.10-py3-none-manylinux_2_27_x86_64.whl",
                "e4f53a8ca8c5d6e8c492d0d0a3d565ecb59a751b19cfdaa4f6da0ab2104c1702",
            ),
            (
                "nvidia_cublas_cu12-12.9.2.10-py3-none-win_amd64.whl",
                "623f43027d40d44ceadf0043f002bd25cf353e8f13ce90b9a87057019f560661",
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-cuda-nvrtc-cu12",
        "12.9.86",
        (
            (
                "nvidia_cuda_nvrtc_cu12-12.9.86-py3-none-manylinux2010_x86_64.manylinux_2_12_x86_64.whl",
                "210cf05005a447e29214e9ce50851e83fc5f4358df8b453155d5e1918094dcb4",
            ),
            (
                "nvidia_cuda_nvrtc_cu12-12.9.86-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                "096d4de6bda726415dfaf3198d4f5c522b8e70139c97feef5cd2ca6d4cd9cead",
            ),
            (
                "nvidia_cuda_nvrtc_cu12-12.9.86-py3-none-win_amd64.whl",
                "72972ebdcf504d69462d3bcd67e7b81edd25d0fb85a2c46d3ea3517666636349",
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-cuda-runtime-cu12",
        "12.9.79",
        (
            (
                "nvidia_cuda_runtime_cu12-12.9.79-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                "83469a846206f2a733db0c42e223589ab62fd2fabac4432d2f8802de4bded0a4",
            ),
            (
                "nvidia_cuda_runtime_cu12-12.9.79-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
                "25bba2dfb01d48a9b59ca474a1ac43c6ebf7011f1b0b8cc44f54eb6ac48a96c3",
            ),
            (
                "nvidia_cuda_runtime_cu12-12.9.79-py3-none-win_amd64.whl",
                "8e018af8fa02363876860388bd10ccb89eb9ab8fb0aa749aaf58430a9f7c4891",
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-cufft-cu12",
        "11.4.1.4",
        (
            (
                "nvidia_cufft_cu12-11.4.1.4-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                "1a28c9b12260a1aa7a8fd12f5ebd82d027963d635ba82ff39a1acfa7c4c0fbcf",
            ),
            (
                "nvidia_cufft_cu12-11.4.1.4-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
                "c67884f2a7d276b4b80eb56a79322a95df592ae5e765cf1243693365ccab4e28",
            ),
            (
                "nvidia_cufft_cu12-11.4.1.4-py3-none-win_amd64.whl",
                "8e5bfaac795e93f80611f807d42844e8e27e340e0cde270dcb6c65386d795b80",
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-curand-cu12",
        "10.3.10.19",
        (
            (
                "nvidia_curand_cu12-10.3.10.19-py3-none-manylinux_2_27_aarch64.whl",
                "de663377feb1697e1d30ed587b07d5721fdd6d2015c738d7528a6002a6134d37",
            ),
            (
                "nvidia_curand_cu12-10.3.10.19-py3-none-manylinux_2_27_x86_64.whl",
                "49b274db4780d421bd2ccd362e1415c13887c53c214f0d4b761752b8f9f6aa1e",
            ),
            (
                "nvidia_curand_cu12-10.3.10.19-py3-none-win_amd64.whl",
                "e8129e6ac40dc123bd948e33d3e11b4aa617d87a583fa2f21b3210e90c743cde",
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-cusolver-cu12",
        "11.7.5.82",
        (
            (
                "nvidia_cusolver_cu12-11.7.5.82-py3-none-manylinux_2_27_aarch64.whl",
                "62efa83e4ace59a4c734d052bb72158e888aa7b770e1a5f601682f16fe5b4fd2",
            ),
            (
                "nvidia_cusolver_cu12-11.7.5.82-py3-none-manylinux_2_27_x86_64.whl",
                "15da72d1340d29b5b3cf3fd100e3cd53421dde36002eda6ed93811af63c40d88",
            ),
            (
                "nvidia_cusolver_cu12-11.7.5.82-py3-none-win_amd64.whl",
                "77666337237716783c6269a658dea310195cddbd80a5b2919b1ba8735cec8efd",
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-cusparse-cu12",
        "12.5.10.65",
        (
            (
                "nvidia_cusparse_cu12-12.5.10.65-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                "221c73e7482dd93eda44e65ce567c031c07e2f93f6fa0ecd3ba876a195023e83",
            ),
            (
                "nvidia_cusparse_cu12-12.5.10.65-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
                "73060ce019ac064a057267c585bf1fd5a353734151f87472ff02b2c5c9984e78",
            ),
            (
                "nvidia_cusparse_cu12-12.5.10.65-py3-none-win_amd64.whl",
                "9e487468a22a1eaf1fbd1d2035936a905feb79c4ce5c2f67626764ee4f90227c",
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-nvjitlink-cu12",
        "12.9.86",
        (
            (
                "nvidia_nvjitlink_cu12-12.9.86-py3-none-manylinux2010_x86_64.manylinux_2_12_x86_64.whl",
                "e3f1171dbdc83c5932a45f0f4c99180a70de9bd2718c1ab77d14104f6d7147f9",
            ),
            (
                "nvidia_nvjitlink_cu12-12.9.86-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                "994a05ef08ef4b0b299829cde613a424382aff7efb08a7172c1fa616cc3af2ca",
            ),
            (
                "nvidia_nvjitlink_cu12-12.9.86-py3-none-win_amd64.whl",
                "cc6fcec260ca843c10e34c936921a1c426b351753587fdd638e8cff7b16bb9db",
            ),
        ),
    ),
)
"""The pack's eleven distributions, copied from ``uv.lock`` (a test keeps them equal).

``numpy`` is not here: the pack uses the bundle's own (CuPy 14.2.0 needs ``>=2.0,<2.6``).
"""


def stamp_for(distribution: str, version: str) -> str:
    """Return the pack stamp for a CuPy distribution and version.

    Args:
        distribution: The CuPy distribution name, for example ``cupy-cuda12x``.
        version: Its version, for example ``14.2.0``.

    Returns:
        ``<version>-cu<CUDA major>``, for example ``14.2.0-cu12``.

    Raises:
        ValueError: The name carries no ``cuda<major>x`` part.
    """
    match = re.fullmatch(r"cupy-cuda(\d+)x", distribution)
    if match is None:
        raise ValueError(f"not a CUDA CuPy distribution: {distribution!r}")
    return f"{version}-cu{match.group(1)}"


def _locked_cupy_version() -> str:
    """Return the locked ``cupy-cuda12x`` version from :data:`LOCKED_DISTRIBUTIONS`."""
    for locked in LOCKED_DISTRIBUTIONS:
        if locked.name == CUPY_DISTRIBUTION:
            return locked.version
    raise LookupError(f"{CUPY_DISTRIBUTION} is not in LOCKED_DISTRIBUTIONS")


STAMP = stamp_for(CUPY_DISTRIBUTION, _locked_cupy_version())
"""This build's pack stamp (``14.2.0-cu12``): the only pack folder the loader reads."""


def _absolute(environ: Mapping[str, str], name: str) -> Path | None:
    """Return the variable as an absolute path, or None when unset, empty or relative."""
    value = environ.get(name, "")
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else None


def pack_root(
    *,
    environ: Mapping[str, str] | None = None,
    platform: str | None = None,
    home: Path | None = None,
) -> Path | None:
    """Return the folder that holds the GPU packs on this platform. Creates nothing.

    - Windows: ``%LOCALAPPDATA%/Clearwater/gpu-pack`` (``<home>/AppData/Local`` when the
      variable is unset, empty or relative);
    - macOS: None (no CUDA there; the loader does nothing);
    - Linux and any other platform: ``$XDG_DATA_HOME/clearwater/gpu-pack``
      (``<home>/.local/share`` when the variable is unset, empty or relative).

    Args:
        environ: The environment to read; ``os.environ`` when None.
        platform: A ``sys.platform`` value; the running one when None.
        home: The home folder used by the fallbacks; ``Path.home()`` when None.

    Returns:
        The pack root, or None on macOS.
    """
    env = os.environ if environ is None else environ
    kind = sys.platform if platform is None else platform
    if kind == "darwin":
        return None
    if kind == "win32":
        local = _absolute(env, "LOCALAPPDATA")
        if local is None:
            local = (Path.home() if home is None else home) / "AppData" / "Local"
        return local / WINDOWS_APP_FOLDER / PACK_FOLDER_NAME
    data = _absolute(env, "XDG_DATA_HOME")
    if data is None:
        data = (Path.home() if home is None else home) / ".local" / "share"
    return data / POSIX_APP_FOLDER / PACK_FOLDER_NAME


def file_sha256(path: Path) -> str:
    """Return a file's sha256 as lower-case hex.

    Args:
        path: The file.

    Returns:
        The digest.

    Raises:
        OSError: The file cannot be read.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class PackStatus:
    """What the loader found and did.

    Attributes:
        stamp: The stamp looked for (:data:`STAMP`).
        outcome: ``"loaded"``, ``"absent"`` or ``"rejected"``.
        reason: Why a pack was rejected; None otherwise.
        site_packages: The folder put on ``sys.path`` when loaded; None otherwise.
        dll_directories: The folders added to the DLL search path (Windows, when loaded).
    """

    stamp: str
    outcome: Outcome
    reason: str | None = None
    site_packages: Path | None = None
    dll_directories: tuple[Path, ...] = ()

    @property
    def line(self) -> str:
        """The one log line: ``gpu pack <stamp>: loaded`` / ``absent`` / ``rejected: <why>``."""
        if self.outcome == "rejected":
            return f"gpu pack {self.stamp}: rejected: {self.reason}"
        return f"gpu pack {self.stamp}: {self.outcome}"


_CONTROL_CHARACTER = re.compile(r"[\x00-\x1f\x7f]")
"""An ASCII control character (newline, tab, carriage return and the rest)."""


def _safe(value: object) -> str:
    """Return a value from the manifest as short one-line ASCII text for a reason.

    Non-ASCII characters and ASCII control characters (newline, tab, carriage return and the
    rest) become backslash escapes (``e`` with an acute accent as backslash-``xe9``, a newline
    as backslash-``x0a``), so a reason is always one printable log line (at most 80
    characters of the value; Reviewer A r2 #12).
    """
    text = value if isinstance(value, str) else repr(value)
    ascii_text = text.encode("ascii", "backslashreplace").decode("ascii")
    one_line = _CONTROL_CHARACTER.sub(lambda m: f"\\x{ord(m.group()):02x}", ascii_text)
    return one_line[:80]


def _manifest_entries(document: object) -> list[dict[str, str]] | str:
    """Return the manifest's distribution entries, or the reason it is malformed.

    Args:
        document: The parsed manifest.

    Returns:
        The entries (each a mapping of string fields), or a rejection reason.
    """
    if not isinstance(document, dict):
        return "manifest malformed: not an object"
    found = document.get("format")
    if type(found) is not int or found != MANIFEST_FORMAT:
        return f"manifest format {_safe(found)}, expected {MANIFEST_FORMAT}"
    if document.get("stamp") != STAMP:
        return f"manifest stamp {_safe(repr(document.get('stamp')))}, expected {STAMP!r}"
    raw = document.get("distributions")
    if not isinstance(raw, list):
        return "manifest malformed: no distributions list"
    fields = ("name", "version", "wheel", "wheel_sha256", "record_sha256")
    entries: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict) or not all(isinstance(item.get(f), str) for f in fields):
            return "manifest malformed: a distribution entry lacks a string field"
        entries.append({f: str(item[f]) for f in fields})
    return entries


def check_pack(folder: Path) -> str | None:
    """Check one pack folder (``<pack root>/<stamp>``) against the lock. Reads only.

    The checks, in order: the manifest parses, its format is :data:`MANIFEST_FORMAT` and its
    stamp is :data:`STAMP`; ``site-packages`` exists; the distributions are exactly
    :data:`LOCKED_DISTRIBUTIONS`, each at its locked version and naming one of its locked
    wheels with that wheel's sha256; and each distribution's installed ``RECORD`` file exists
    with the sha256 the manifest records. A file-system error on any check (an existence or
    type check included) is a rejection, never an exception out of start-up.

    Args:
        folder: The pack folder.

    Returns:
        None when the pack passes, else the first failed check as a short ASCII reason.
    """
    try:
        return _check_pack(folder)
    except OSError as error:
        return f"pack unreadable: {type(error).__name__}"


def _check_pack(folder: Path) -> str | None:
    """Run :func:`check_pack`'s checks; an ``OSError`` from a path check propagates to it.

    Args:
        folder: The pack folder.

    Returns:
        None when the pack passes, else the first failed check.
    """
    manifest = folder / MANIFEST_NAME
    if not manifest.is_file():
        return f"no {MANIFEST_NAME}"
    try:
        document = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        return f"{MANIFEST_NAME} unreadable: {type(error).__name__}"
    entries = _manifest_entries(document)
    if isinstance(entries, str):
        return entries
    site = folder / SITE_PACKAGES_NAME
    if not site.is_dir():
        return f"no {SITE_PACKAGES_NAME} folder"
    expected = {locked.name: locked for locked in LOCKED_DISTRIBUTIONS}
    seen: set[str] = set()
    for entry in entries:
        name = entry["name"]
        if name not in expected:
            return f"unexpected distribution {_safe(name)}"
        if name in seen:
            return f"duplicate distribution {name}"
        seen.add(name)
    missing = sorted(set(expected) - seen)
    if missing:
        return f"missing distribution {missing[0]}"
    for entry in entries:
        locked = expected[entry["name"]]
        if entry["version"] != locked.version:
            return f"{locked.name} version {_safe(entry['version'])}, expected {locked.version}"
        if (entry["wheel"], entry["wheel_sha256"].lower()) not in locked.wheels:
            wheel = _safe(entry["wheel"])
            return f"{locked.name} wheel {wheel} with that sha256 is not in the lock"
        record = site / locked.dist_info_name / "RECORD"
        if not record.is_file():
            return f"{locked.name} RECORD missing"
        try:
            actual = file_sha256(record)
        except OSError as error:
            return f"{locked.name} RECORD unreadable: {type(error).__name__}"
        if actual != entry["record_sha256"].lower():
            return f"{locked.name} RECORD sha256 mismatch"
    return None


_DLL_HANDLES: list[object] = []
"""The ``os.add_dll_directory`` handles, kept for the process's life (closing one removes it)."""


def _add_dll_directories(site: Path) -> tuple[Path, ...] | str:
    """On Windows, add each ``site/nvidia/*/bin`` folder to the DLL search path.

    Args:
        site: The pack's ``site-packages`` folder.

    Returns:
        The folders added (none on other platforms), or a rejection reason when they cannot
        be listed or one cannot be added (the ones already added are removed again).
    """
    try:
        folders = tuple(sorted(p for p in (site / "nvidia").glob("*/bin") if p.is_dir()))
    except OSError as error:
        return f"DLL folders unreadable: {type(error).__name__}"
    if sys.platform == "win32":
        added: list[object] = []
        for folder in folders:
            try:
                added.append(os.add_dll_directory(str(folder)))
            except OSError as error:
                for handle in added:
                    close = getattr(handle, "close", None)
                    if callable(close):
                        close()
                return f"DLL folder nvidia/{folder.parent.name}/bin: {type(error).__name__}"
        _DLL_HANDLES.extend(added)
        return folders
    else:
        return ()


def _load_folder(folder: Path) -> PackStatus:
    """Check one existing pack folder and, when it passes, load it.

    Args:
        folder: ``<pack root>/<stamp>``.

    Returns:
        A ``loaded`` or ``rejected`` status.
    """
    reason = check_pack(folder)
    if reason is not None:
        return PackStatus(STAMP, "rejected", reason=reason)
    site = folder / SITE_PACKAGES_NAME
    dlls = _add_dll_directories(site)
    if isinstance(dlls, str):
        return PackStatus(STAMP, "rejected", reason=dlls)
    entry = str(site)
    if entry not in sys.path:
        sys.path.insert(0, entry)
    return PackStatus(STAMP, "loaded", site_packages=site, dll_directories=dlls)


def _find_and_load(folder: Path) -> PackStatus:
    """Load ``<pack root>/<stamp>`` when it is a folder; absent when it is not.

    Args:
        folder: ``<pack root>/<stamp>``.

    Returns:
        ``absent``, ``loaded`` or ``rejected`` (also when the folder cannot even be looked at:
        a file-system error is a rejection, never an exception out of start-up).
    """
    try:
        present = folder.is_dir()
    except OSError as error:
        return PackStatus(STAMP, "rejected", reason=f"pack unreadable: {type(error).__name__}")
    return _load_folder(folder) if present else PackStatus(STAMP, "absent")


def load(root: Path | None) -> PackStatus:
    """Look for this build's pack under ``root``, load it when it passes, and log one line.

    Loading = ``site-packages`` at the front of ``sys.path`` (once) and, on Windows, the
    ``nvidia/*/bin`` DLL folders. Absent or rejected = nothing changes. Never writes.

    Args:
        root: The pack root (:func:`pack_root`; tests pass a folder under ``tmp_path``), or
            None when the platform has no pack.

    Returns:
        The status (its :attr:`PackStatus.line` is the line logged).
    """
    status = PackStatus(STAMP, "absent") if root is None else _find_and_load(root / STAMP)
    _LOG.info("%s", status.line)
    return status


def activate() -> PackStatus | None:
    """Load the pack from :func:`pack_root` in a frozen build; do nothing otherwise (D4).

    Call it before anything imports ``cupy`` (``clearwater.__main__`` does, on both its
    branches).

    Returns:
        The status in a frozen build; None in a source run (nothing checked, nothing logged).
    """
    if not getattr(sys, "frozen", False):
        return None
    return load(pack_root())
