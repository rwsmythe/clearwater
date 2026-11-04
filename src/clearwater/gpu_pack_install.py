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
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
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
_BUSY = "another GPU pack operation is in progress"
_PENDING = "GPU support will be removed at the next start"
REPLACE_TEXT = "An existing GPU pack is not usable and will be replaced"
"""The notice shown before replacing a pack rejected by the cheap check."""


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


def replacement_notice() -> str | None:
    """Describe replacement of an existing rejected pack, without modifying it.

    Returns:
        The replacement notice, or None when no rejected pack folder exists.
    """
    root = gpu_pack.pack_root()
    if root is not None:
        folder = root / gpu_pack.STAMP
        if folder.is_dir() and gpu_pack.check_pack(folder) is not None:
            return REPLACE_TEXT
    return None


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
        or parts[0].endswith(".data")
        or any(
            part in ("", ".", "..") or ":" in part or part.endswith((".", " ")) for part in parts
        )
        or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
        or (stat.S_ISDIR(mode) and not member.is_dir())
    ):
        raise _InstallError(f"wheel member not allowed: {_ascii(name)}")
    target = site.joinpath(*path.parts)
    if not target.resolve().is_relative_to(site.resolve()):
        raise _InstallError(f"wheel member outside site-packages: {_ascii(name)}")
    return target


def _unpack(archive: Path, site: Path, reporter: _Reporter, completed: int) -> None:
    """Unpack plain files only, with all member names validated before the first write."""
    with zipfile.ZipFile(archive) as wheel:
        members = [(member, _member_path(site, member)) for member in wheel.infolist()]
        for member, target in members:
            _cancel(reporter.progress)
            if member.is_dir():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with wheel.open(member) as source, target.open("wb") as output:
                while block := source.read(_CHUNK_SIZE):
                    _cancel(reporter.progress)
                    output.write(block)
            reporter.report(completed, f"Unpacking {archive.name}: {member.orig_filename}")


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
    """Under the operation lock, remove plain staging folders left by a dead process."""
    for folder in root.glob(f"{stamp}.partial-*"):
        try:
            info = folder.lstat()
            reparse = False
            if sys.platform == "win32":
                reparse = bool(info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode) or reparse:
                _LOG.warning("skipping non-directory or linked partial: %s", _ascii(folder))
                continue
            _remove_tree(root, folder)
        except PermissionError as error:
            _LOG.warning("GPU pack partial still in use: %s: %s", _ascii(folder), _ascii(error))


@contextmanager
def _operation_lock(root: Path) -> Iterator[None]:
    """Hold an exclusively created pack-root lock, breaking only an unlocked stale file."""
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".install.lock"
    for _ in range(3):
        try:
            handle = path.open("xb")
        except FileExistsError:
            if sys.platform == "win32":
                try:
                    path.unlink()
                except FileNotFoundError:
                    continue
                except OSError as error:
                    raise _InstallError(_BUSY) from error
            else:
                import fcntl

                try:
                    with path.open("rb") as stale:
                        fcntl.flock(stale, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        if os.fstat(stale.fileno()).st_ino == path.stat().st_ino:
                            path.unlink()
                except FileNotFoundError:
                    continue
                except OSError as error:
                    raise _InstallError(_BUSY) from error
            continue
        break
    else:
        raise _InstallError(_BUSY)
    owns_inode = sys.platform == "win32"
    try:
        if sys.platform != "win32":
            import fcntl

            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                raise _InstallError(_BUSY) from error
            # A stale-lock contender may have unlinked this inode before flock won.
            # Never enter an operation holding an orphaned lock.
            try:
                inode = path.stat().st_ino
            except FileNotFoundError:
                inode = None
            if os.fstat(handle.fileno()).st_ino != inode:
                raise _InstallError(_BUSY)
            owns_inode = True
        yield
    finally:
        # Windows forbids unlinking our own open handle; POSIX unlinks while locked.
        if sys.platform == "win32":
            handle.close()
            # A contender can break our now-closed lock and already hold a new one.
            # Its held-open file must remain; our operation is finished.
            with suppress(PermissionError):
                path.unlink(missing_ok=True)
        else:
            try:
                if owns_inode:
                    path.unlink(missing_ok=True)
            finally:
                handle.close()


def _mark_pending() -> None:
    """Write the empty removal marker while the pack-root operation lock is held."""
    marker = gpu_pack.pending_removal_path()
    assert marker is not None
    marker.touch()


def _pack_in_use(folder: Path) -> bool:
    """On Windows, probe mapped images by write-open, never by renaming their folder."""
    if sys.platform == "win32":
        for path in folder.rglob("*"):
            if path.suffix.lower() in (".pyd", ".dll") and path.is_file():
                try:
                    descriptor = os.open(path, os.O_RDWR)
                except PermissionError:
                    return True
                os.close(descriptor)
    return False


def _rename_remove(root: Path) -> bool:
    """Probe then hide and delete under the operation lock; False means deferred removal."""
    destination = root / gpu_pack.STAMP
    _contained(root, destination)
    if destination.exists():
        if _pack_in_use(destination):
            _mark_pending()
            return False
        renamed = root / f"{gpu_pack.STAMP}.partial-{uuid.uuid4().hex}"
        try:
            os.replace(destination, renamed)
            _remove_tree(root, renamed)
        except PermissionError:
            # A mapped image may appear after the probe. Keep the remainder hidden;
            # a future partial sweep can finish it without breaking GUI startup.
            _mark_pending()
            return False
    return True


def defer_removal() -> PackResult:
    """Record the GUI's removal request for a pack already activated in this process.

    Returns:
        Pending success without probing or renaming, or an operation-lock/write failure.
    """
    root = gpu_pack.pack_root()
    if root is None:
        return PackResult(False, "GPU support is not available on this platform")
    try:
        with _operation_lock(root):
            _mark_pending()
            return PackResult(True, _PENDING)
    except Exception as error:
        return PackResult(False, _ascii(error))


def _apply_pending_locked(root: Path) -> PackResult:
    """Apply a pending request under an already-held operation lock."""
    marker = gpu_pack.pending_removal_path()
    assert marker is not None
    if not marker.exists():
        return PackResult(True, "no GPU pack removal is pending")
    try:
        if not _rename_remove(root):
            _LOG.warning("GPU pack removal pending")
            return PackResult(False, "GPU pack removal pending")
        _partials(root, gpu_pack.STAMP)
        marker.unlink()
        return PackResult(True, "GPU support is removed; takes effect at the next start")
    except OSError as error:
        _LOG.warning("GPU pack removal pending: %s", _ascii(error))
        return PackResult(False, "GPU pack removal pending")


def apply_pending_removal() -> PackResult:
    """At GUI startup, retry deferred removal without ever loading the pack.

    Returns:
        Success after clearing the marker, or failure with the marker left for next start.
    """
    root = gpu_pack.pack_root()
    if root is None:
        return PackResult(False, "GPU support is not available on this platform")
    try:
        with _operation_lock(root):
            return _apply_pending_locked(root)
    except Exception as error:
        _LOG.warning("GPU pack removal pending: %s", _ascii(error))
        return PackResult(False, _ascii(error))


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
    try:
        with _operation_lock(root):
            return _install_locked(root, progress)
    except (_CancelledError, KeyboardInterrupt):
        return PackResult(False, "GPU support installation cancelled", cancelled=True)
    except Exception as error:
        return PackResult(False, _ascii(error))


def _install_locked(root: Path, progress: Progress) -> PackResult:
    """Build and clean up the transaction while the pack-root operation lock is held."""
    staging: Path | None = None
    try:
        pending = _apply_pending_locked(root)
        if not pending.ok:
            raise _InstallError(
                "GPU support is loaded by a running Clearwater; close it and try again"
            )
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
        if not _rename_remove(root):
            raise _InstallError(
                "GPU support is loaded by a running Clearwater; close it and try again"
            )
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
            _unpack(archive, site, reporter, completed + wheel.size)
            archive.unlink()
            completed += wheel.size
        downloads.rmdir()
        _cancel(progress)
        document = manifest_document(staging)
        problem = next(
            gpu_pack.pack_problems(
                staging, full=True, manifest=document, cancelled=progress.cancelled
            ),
            None,
        )
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
    except (_CancelledError, gpu_pack.PackCheckCancelled, KeyboardInterrupt):
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
        with _operation_lock(root):
            marker = gpu_pack.pending_removal_path()
            assert marker is not None
            present = destination.exists()
            if not _rename_remove(root):
                return PackResult(True, _PENDING)
            _partials(root, gpu_pack.STAMP)
            marker.unlink(missing_ok=True)
            message = (
                "GPU support is removed; takes effect at the next start"
                if present
                else "no GPU pack is installed"
            )
            return PackResult(True, message)
    except Exception as error:
        return PackResult(False, _ascii(error))
