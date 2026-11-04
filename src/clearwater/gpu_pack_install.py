"""Download, verify and publish the per-user GPU pack on an explicit request (N14).

Only the standard library and the loader are imported. Downloads and extraction stay in
one staging folder under the pack root. Full verification precedes the manifest write;
the written manifest passes the cheap check before the final same-volume rename.
"""

from __future__ import annotations

import hashlib
import http.client
import json
import logging
import math
import os
import shutil
import ssl
import stat
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import IO, Protocol

from clearwater import __version__, gpu_pack

_LOG = logging.getLogger(__name__)
_CHUNK_SIZE = 1 << 20
_DOWNLOAD_ORIGIN = ("https", "files.pythonhosted.org", 443)
_RETRY_DELAY = 2.0
# Round up the measured 2,412.6 MiB Windows pack; failures still clean up if space changes.
_INSTALLED_SIZE = 2413 * (1 << 20)


class Progress(Protocol):
    """Structural reporting and cancellation, compatible with IF-8 without importing it."""

    def report(self, done: int, total: int | None, message: str) -> None:
        """Report completed bytes, total download bytes and the current wheel filename."""
        ...

    def cancelled(self) -> bool:
        """Return whether the caller has requested cancellation."""
        ...


@dataclass(frozen=True)
class Wheel:
    """One selected locked wheel.

    Attributes:
        name: Distribution name.
        version: Locked distribution version.
        filename: Wheel archive basename.
        sha256: Recorded SHA-256 hex digest.
        url: Exact locked download URL.
        size: Recorded compressed byte count.
    """

    name: str
    version: str
    filename: str
    sha256: str
    url: str
    size: int


@dataclass(frozen=True)
class InstallPlan:
    """The current platform's ordered pack plan.

    Attributes:
        stamp: Final pack folder name.
        wheels: One compatible wheel per locked distribution.
        download_size: Sum of compressed wheel sizes, in bytes.
        installed_size: Conservative installed-space estimate, in bytes.
    """

    stamp: str
    wheels: tuple[Wheel, ...]
    download_size: int
    installed_size: int

    @property
    def required_space(self) -> int:
        """Installed estimate plus the largest archive, with ten percent spare space."""
        largest = max((wheel.size for wheel in self.wheels), default=0)
        return math.ceil((self.installed_size + largest) * 1.1)


@dataclass(frozen=True)
class PackResult:
    """The shared headless and GUI outcome, without any GUI or interface imports.

    Attributes:
        ok: True when the requested state holds.
        message: One ASCII-safe success or failure message.
        path: Installed pack path on successful installation, otherwise None.
        cancelled: True when cancellation stopped the operation.
    """

    ok: bool
    message: str
    path: Path | None = None
    cancelled: bool = False


class _InstallError(Exception):
    """A readable refusal or integrity error that must not be retried."""


class _CancelledError(Exception):
    """Cooperative cancellation, caught only after staging cleanup."""


def _ascii(value: object) -> str:
    """Keep messages on one line and printable on a Windows console."""
    return " ".join(str(value).split()).encode("ascii", errors="backslashreplace").decode("ascii")


def _wheel_tags(filename: str) -> frozenset[str]:
    """Expand the final three fields of a wheel filename into its declared tags."""
    if not filename.endswith(".whl") or len(filename.split("-")) < 5:
        raise ValueError(f"not a wheel file name: {filename!r}")
    python, abi, platform = (part.split(".") for part in filename[:-4].split("-")[-3:])
    return frozenset(f"{p}-{a}-{s}" for p in python for a in abi for s in platform)


def plan() -> InstallPlan:
    """Return the ordered compatible wheels and calculated sizes without I/O.

    Returns:
        The current lock's install plan.

    Raises:
        ValueError: A distribution has no unique compatible wheel.
    """
    interpreter, platform = gpu_pack.platform_tags()
    wheels: list[Wheel] = []
    for distribution in gpu_pack.LOCKED_DISTRIBUTIONS:
        matches = [
            row
            for row in distribution.wheels
            if any(gpu_pack.tag_fits(tag, interpreter, platform) for tag in _wheel_tags(row[0]))
        ]
        if len(matches) != 1:
            raise ValueError(f"{distribution.name}: {len(matches)} compatible locked wheels")
        filename, digest, url, size = matches[0]
        wheels.append(Wheel(distribution.name, distribution.version, filename, digest, url, size))
    return InstallPlan(gpu_pack.STAMP, tuple(wheels), sum(w.size for w in wheels), _INSTALLED_SIZE)


def manifest_document(folder: Path) -> dict[str, object]:
    """Construct the shared manifest from installed WHEEL tags and unchanged RECORD files.

    Args:
        folder: Pack or staging folder containing site-packages.

    Returns:
        Manifest format, stamp and per-distribution lock and installed RECORD hashes.

    Raises:
        OSError: Installed metadata cannot be read.
        ValueError: An installed distribution does not select exactly one locked wheel.
    """
    site = folder / gpu_pack.SITE_PACKAGES_NAME
    rows: list[dict[str, str]] = []
    for locked in gpu_pack.LOCKED_DISTRIBUTIONS:
        dist_info = site / locked.dist_info_name
        record = dist_info / "RECORD"
        if not record.is_file():
            raise FileNotFoundError(f"{locked.name} {locked.version}: no {record}")
        tags = frozenset(
            line.split(":", 1)[1].strip()
            for line in (dist_info / "WHEEL").read_text(encoding="utf-8").splitlines()
            if line.startswith("Tag:")
        )
        matches = [row for row in locked.wheels if _wheel_tags(row[0]) & tags]
        if len(matches) != 1:
            raise ValueError(f"{locked.name}: {len(matches)} locked wheels match {sorted(tags)}")
        wheel, digest, _url, _size = matches[0]
        rows.append(
            {
                "name": locked.name,
                "version": locked.version,
                "wheel": wheel,
                "wheel_sha256": digest,
                "record_sha256": gpu_pack.file_sha256(record),
            }
        )
    return {"format": gpu_pack.MANIFEST_FORMAT, "stamp": gpu_pack.STAMP, "distributions": rows}


def write_staging_manifest(folder: Path, document: dict[str, object]) -> Path:
    """Write the already fully verified document inside the installer's staging folder.

    Args:
        folder: The validated staging folder (or the hand-filled stamp folder).
        document: The document used by the preceding in-memory full check.

    Returns:
        The written manifest path.

    Raises:
        OSError: The manifest could not be written.
    """
    path = folder / gpu_pack.MANIFEST_NAME
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def write_manifest(folder: Path) -> Path:
    """Write a hand-filled pack's manifest, preserving the tooling's stamp-name refusal.

    Args:
        folder: Pack folder named exactly for this build's stamp.

    Returns:
        The written manifest path.

    Raises:
        ValueError: The folder name differs from STAMP or metadata selects no unique wheel.
        OSError: Metadata cannot be read or the manifest cannot be written.
    """
    if folder.name != gpu_pack.STAMP:
        raise ValueError(f"the pack folder must be named {gpu_pack.STAMP!r}, not {folder.name!r}")
    return write_staging_manifest(folder, manifest_document(folder))


def _check_url(url: str, *, redirect: bool = False) -> None:
    """Refuse any origin other than the pinned HTTPS package host, including downgrades."""
    parts = urllib.parse.urlsplit(url)
    port = parts.port or (443 if parts.scheme == "https" else 80)
    if (
        (parts.scheme, parts.hostname, port) != _DOWNLOAD_ORIGIN
        or parts.username is not None
        or parts.password is not None
    ):
        prefix = "redirect refused" if redirect else "download URL refused"
        raise _InstallError(f"{prefix}: {_ascii(url)}")


class _LockedRedirect(urllib.request.HTTPRedirectHandler):
    """Keep every redirect on the pinned package origin before urllib connects."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: http.client.HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        """Validate the redirect's origin, then retain urllib's ordinary redirect behavior."""
        _check_url(newurl, redirect=True)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _cancel(progress: Progress) -> None:
    """Stop at a cooperative boundary if requested."""
    if progress.cancelled():
        raise _CancelledError


@dataclass
class _Reporter:
    progress: Progress
    total: int
    high_water: int = 0

    def report(self, done: int, filename: str) -> None:
        self.high_water = max(self.high_water, done)
        self.progress.report(self.high_water, self.total, filename)


def _pause(progress: Progress) -> None:
    """Wait between transport attempts while continuing to observe cancellation."""
    deadline = time.monotonic() + _RETRY_DELAY
    while time.monotonic() < deadline:
        _cancel(progress)
        time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))


def _download(wheel: Wheel, downloads: Path, reporter: _Reporter, completed: int) -> Path:
    """Stream and verify one pinned archive; retry only transport errors, three attempts total."""
    _check_url(wheel.url)
    part = downloads / (wheel.filename + ".part")
    final = downloads / wheel.filename
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ssl.create_default_context()), _LockedRedirect()
    )
    for attempt in range(3):
        _cancel(reporter.progress)
        digest = hashlib.sha256()
        received = 0
        request = urllib.request.Request(
            wheel.url, headers={"User-Agent": f"Clearwater/{__version__}"}
        )
        try:
            with opener.open(request, timeout=30) as response, part.open("wb") as output:
                if response.status != 200:
                    raise urllib.error.URLError(f"HTTP {response.status}")
                length = response.headers.get("Content-Length")
                expected = int(length) if length is not None else None
                while True:
                    _cancel(reporter.progress)
                    block = response.read(_CHUNK_SIZE)
                    if not block:
                        if expected is not None and received < expected:
                            raise http.client.IncompleteRead(b"", expected - received)
                        break
                    received += len(block)
                    if received > wheel.size:
                        raise _InstallError(
                            f"the download of {wheel.filename} did not match its recorded hash"
                        )
                    output.write(block)
                    digest.update(block)
                    reporter.report(completed + received, wheel.filename)
                    _cancel(reporter.progress)
        except (
            urllib.error.URLError,
            TimeoutError,
            http.client.HTTPException,
            ConnectionError,
            ssl.SSLError,
        ) as error:
            part.unlink(missing_ok=True)
            if attempt == 2:
                raise _InstallError(
                    f"the download of {wheel.filename} failed: {_ascii(error)}"
                ) from error
            _pause(reporter.progress)
            continue
        if received != wheel.size or digest.hexdigest() != wheel.sha256:
            part.unlink(missing_ok=True)
            raise _InstallError(f"the download of {wheel.filename} did not match its recorded hash")
        part.replace(final)
        return final
    raise AssertionError("unreachable download attempt")


def _member_path(site: Path, member: zipfile.ZipInfo) -> Path:
    """Validate a wheel member before any member is extracted."""
    # filename is normalized on Windows, and has already lost any NUL suffix.
    name = member.orig_filename
    path = PurePosixPath(name)
    windows = PureWindowsPath(name)
    mode = member.external_attr >> 16
    parts = name.removesuffix("/").split("/")
    if (
        not name
        or "\\" in name
        or "\x00" in name
        or path.is_absolute()
        or windows.drive
        or windows.root
        or any(
            part in ("", ".", "..")
            or ":" in part
            or part.endswith((".", " "))
            or part.endswith(".data")
            for part in parts
        )
        or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
        or (stat.S_ISDIR(mode) and not member.is_dir())
    ):
        raise _InstallError(f"wheel member not allowed: {_ascii(name)}")
    target = site.joinpath(*path.parts)
    if not target.resolve().is_relative_to(site.resolve()):
        raise _InstallError(f"wheel member outside site-packages: {_ascii(name)}")
    return target


def _unpack(archive: Path, site: Path, progress: Progress) -> None:
    """Unpack plain files only, with all member names validated before the first write."""
    with zipfile.ZipFile(archive) as wheel:
        members = [(member, _member_path(site, member)) for member in wheel.infolist()]
        for member, target in members:
            _cancel(progress)
            if member.is_dir():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with wheel.open(member) as source, target.open("wb") as output:
                while block := source.read(_CHUNK_SIZE):
                    _cancel(progress)
                    output.write(block)


def _contained(root: Path, folder: Path) -> None:
    """Limit destructive operations to direct, non-linked children of the pack root."""
    if folder.parent.resolve() != root.resolve() or folder.resolve().parent != root.resolve():
        raise _InstallError(f"pack path is outside the pack root: {_ascii(folder)}")
    if folder.is_symlink():
        raise _InstallError(f"pack path is a link: {_ascii(folder)}")


def _remove_tree(root: Path, folder: Path) -> None:
    """Remove a validated pack child without following a substituted root entry."""
    _contained(root, folder)
    if folder.exists():
        shutil.rmtree(folder, onexc=_retry_read_only)


def _retry_read_only(function: Callable[..., object], path: str, error: BaseException) -> None:
    """Clear an owned file's read-only bit, then retry the failed removal operation once."""
    mode = os.lstat(path).st_mode
    if not isinstance(error, PermissionError) or mode & stat.S_IWUSR:
        raise error
    os.chmod(path, mode | stat.S_IWUSR)
    function(path)


def _partials(root: Path, stamp: str) -> None:
    """Remove staging folders left by a dead process before starting a new transaction."""
    for folder in root.glob(f"{stamp}.partial-*"):
        _remove_tree(root, folder)


def install(progress: Progress) -> PackResult:
    """Install the locked pack transactionally on the user's explicit request.

    Args:
        progress: Byte reporting and cooperative cancellation supplied by the caller.

    Returns:
        Success with the installed path, or one readable failure/cancellation message.
        Cleanup errors are logged and disclosed in the result rather than raised.
    """
    root = gpu_pack.pack_root()
    if root is None:
        return PackResult(False, "GPU support is not available on this platform")
    staging: Path | None = None
    try:
        wanted = plan()
        root.mkdir(parents=True, exist_ok=True)
        _partials(root, wanted.stamp)
        destination = root / wanted.stamp
        _contained(root, destination)
        if destination.is_dir() and gpu_pack.check_pack(destination) is None:
            return PackResult(True, "GPU support is already installed", destination)
        free = shutil.disk_usage(root).free
        if free < wanted.required_space:
            raise _InstallError(
                f"GPU support needs {wanted.required_space:,} bytes required "
                f"({wanted.installed_size:,} installed + "
                f"{max((w.size for w in wanted.wheels), default=0):,} download + 10%); "
                f"only {free:,} bytes free"
            )
        _cancel(progress)
        _remove_tree(root, destination)
        staging = root / f"{wanted.stamp}.partial-{uuid.uuid4().hex}"
        staging.mkdir()
        site = staging / gpu_pack.SITE_PACKAGES_NAME
        site.mkdir()
        downloads = staging / "downloads"
        downloads.mkdir()
        reporter = _Reporter(progress, wanted.download_size)
        completed = 0
        for wheel in wanted.wheels:
            archive = _download(wheel, downloads, reporter, completed)
            _unpack(archive, site, progress)
            archive.unlink()
            completed += wheel.size
        downloads.rmdir()
        _cancel(progress)
        document = manifest_document(staging)
        problem = next(gpu_pack.pack_problems(staging, full=True, manifest=document), None)
        if problem is not None:
            raise _InstallError(problem)
        _cancel(progress)
        write_staging_manifest(staging, document)
        problem = gpu_pack.check_pack(staging)
        if problem is not None:
            raise _InstallError(problem)
        _cancel(progress)
        os.replace(staging, destination)
        return PackResult(
            True, "GPU support is installed. Restart Clearwater to use it.", destination
        )
    except (_CancelledError, KeyboardInterrupt):
        result = PackResult(False, "GPU support installation cancelled", cancelled=True)
    except Exception as error:
        result = PackResult(False, _ascii(error))
    if staging is not None:
        try:
            _remove_tree(root, staging)
        except Exception as error:
            detail = f"could not remove {_ascii(staging)}: {_ascii(error)}"
            _LOG.warning("%s", detail)
            result = PackResult(False, f"{result.message}; {detail}", cancelled=result.cancelled)
    return result


def remove(folder: Path | None = None) -> PackResult:
    """Remove the current stamp and dead-process staging folders, effective next start.

    Args:
        folder: Optional current-stamp path; any other target is refused. The default
            is computed from pack_root(), never from a user-selected directory.

    Returns:
        Success, including an already absent pack, or a readable removal failure.
    """
    root = gpu_pack.pack_root()
    if root is None:
        return PackResult(False, "GPU support is not available on this platform")
    destination = root / gpu_pack.STAMP
    try:
        target = destination if folder is None else folder
        _contained(root, target)
        if target != destination:
            raise _InstallError("only the current GPU pack can be removed")
        present = destination.exists()
        _remove_tree(root, destination)
        _partials(root, gpu_pack.STAMP)
        message = (
            "GPU support is removed; takes effect at the next start"
            if present
            else "no GPU pack is installed"
        )
        return PackResult(True, message)
    except Exception as error:
        return PackResult(False, _ascii(error))
