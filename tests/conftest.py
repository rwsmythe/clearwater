"""Shared pytest configuration: the footage guard and the footage-test skip.

Temp-root guard (WP-T1, closes DR-21). ``pytest --basetemp=<dir>`` deletes and
recreates ``<dir>``, and ``TMP``/``TEMP``/``TMPDIR``/``PYTEST_DEBUG_TEMPROOT``
decide where pytest makes its folders. Pointed at the owner's footage folder,
a run could delete or write footage. A ``pytest_configure`` hook (``tryfirst``)
therefore refuses to start (``pytest.UsageError``, exit code 4, message naming
the footage folder and the offending root) when the temp root would be:

* ``--basetemp``: inside the footage folder, equal to it, or an ancestor of it
  (pytest removes the whole basetemp tree, which would take the footage with it);
* otherwise the default temp root (``PYTEST_DEBUG_TEMPROOT`` if set, else the one
  directory ``tempfile.gettempdir()`` would pick), inside or equal to the footage
  folder, or when pytest's own ``pytest-of-<user>`` folder under that root (or any
  other ``pytest-of-*`` entry there) is, or leads into, the footage folder.

Paths are compared fully resolved (symlinks and junctions followed; a Windows
extended-length prefix removed) and, on Windows, case-insensitively, then by file
identity (``os.path.samefile``) for any existing ancestor. A legitimate basetemp,
such as a folder under the working folder, passes. The guard is inert, and silent,
when there is no valid local configuration (none, an invalid one, no footage key):
it never fails a run on a machine without footage. A configured footage folder that
does not exist is NOT inert: it may be a disconnected drive, so the guard stays
active (fail safe). If a check it needs cannot be made (an error resolving the temp
root or pytest's own ``pytest-of-<user>`` folder), the guard refuses and says so.

Scope of the guarantee: the guard refuses before pytest creates or clears any
temporary FOLDER; not the TEMP-variable file writes. Pytest starts output capture
before it loads any conftest, and capture (and ``tempfile``'s writability probe)
makes short-lived, randomly named files in the ``TMPDIR``/``TEMP``/``TMP``
directory. A guard in this file cannot stop that, so with those variables pointing
into the footage folder, or with ``TMP`` there next to any other setting, such files
come and go before the refusal; nothing existing is touched (DR-22).

Ordering: this hook runs before pytest's temp-path factory is built
(``_pytest/tmpdir.py`` ``pytest_configure``), and pytest creates or clears a temp
folder only when the first ``tmp_path`` is requested (``getbasetemp``). The cache
provider's ``--cache-clear`` clears only ``.pytest_cache`` subfolders and runs after
this hook (a conftest registers after the built-in plugins and later-registered
hooks run first); tests pin both.

With pytest-xdist 3.8.0 local popen workers, the controller guard configures
before session startup launches workers. ``xdist/workermanage.py:337-341``
derives each worker's ``popen-gwN`` basetemp below the controller's basetemp;
``xdist/remote.py:400,420-427`` assigns it before the worker configures its
plugins and runs this guard again. Controller refusal therefore precedes
worker temp-root creation; the worker checks its assigned child root as well.

When the guard loads (pytest 8.4.2, ``_pytest/config/__init__.py``
``_set_initial_conftests`` and ``_try_load_conftest``): for every existing path
argument (``testpaths`` when none is given) pytest loads the conftest files found at
or above it, up to ``--confcutdir`` (default: the ini file's folder), and in the
``test*`` subfolders of an argument that is a folder. So ``pytest``, ``pytest tests``,
``pytest tests/x.py`` and ``pytest .`` at the repository root load this file;
``pytest tools`` does not. ``--noconftest`` suppresses it; so does a ``--confcutdir``
below ``tests/``; ``--rootdir`` alone and ``-p no:conftest`` do not. With another
ini file (``-c``) that lacks ``pythonpath = ["tools"]`` the import below fails
(out of envelope). See ``docs/reports/wp-t1-pytest-guard.md``.

The session fixtures ``gx011627_trim`` and ``gx011627`` provide a checked stream-copy
trim and lazy trim/full forms of GX011627. The trim stays under the session temp root
and is removed with its folder at teardown; fullclip forms read the original source.
"""

from __future__ import annotations

import getpass
import os
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from local_config import LocalConfigError, footage_available, load_local_config

pytest_plugins = (
    ["fixture_plugin"] if Path(__file__).with_name("fixture_plugin.py").is_file() else []
)

_PYTEST_OF = "pytest-of-"

GX011627_FRAMES = 681
"""Number of video frames in the complete, unmodified GX011627 source."""

ALLOWED_TAG_DIFFS = {
    "format": frozenset({"major_brand", "minor_version", "compatible_brands", "encoder"}),
    "stream": frozenset({"handler_name", "language"}),
    "audio": frozenset({"timecode"}),
}
"""Muxer-written tag keys allowed to differ, restricted to their ruled scopes."""


def _canonical(path: str | os.PathLike[str]) -> Path:
    """Return ``path`` made absolute, fully resolved and case-normalised.

    Args:
        path: A path that need not exist.

    Returns:
        The path as ``os.path.abspath`` then ``Path.resolve`` leave it (pytest's own
        order for ``--basetemp``), with any Windows extended-length prefix removed and
        the case normalised on Windows.

    Raises:
        OSError: If the path cannot be resolved.
        RuntimeError: If resolving meets a symlink loop.
    """
    text = str(Path(os.path.abspath(os.fspath(path))).resolve())
    if os.name == "nt":
        # resolve() keeps an extended-length prefix that was in the input; strip it to compare.
        # Other forms (\\?\Volume{GUID}\...) stay as they are; samefile() covers them.
        extended, unc = "\\\\?\\", "\\\\?\\UNC\\"
        if text.startswith(unc):
            text = "\\\\" + text[len(unc) :]
        elif text.startswith(extended) and text[4:5].isalpha() and text[5:6] == ":":
            text = text[len(extended) :]
    return Path(os.path.normcase(text))


def _inside_or_equal(candidate: Path, folder: Path) -> bool:
    """Report whether ``candidate`` equals ``folder`` or lies below it.

    The canonical-path comparison is backed by file identity: an existing
    ancestor of ``candidate`` (or ``candidate`` itself) that is the same file as
    ``folder`` counts, which catches spellings the text comparison misses (8.3
    short names, subst or mapped drives, bind mounts).
    """
    if candidate == folder or folder in candidate.parents:
        return True
    for ancestor in (candidate, *candidate.parents):
        try:
            if os.path.samefile(ancestor, folder):
                return True
        except OSError:
            continue  # absent (a not-yet-existing tail) or unreadable
    return False


def _holds_pytest_of(root: Path, folder: Path) -> bool:
    """Report whether ``folder`` lies inside ``root/pytest-of-*``, where pytest writes."""
    try:
        parts = folder.relative_to(root).parts
    except ValueError:
        return False
    return bool(parts) and os.path.normcase(parts[0]).startswith(_PYTEST_OF)


def _pytest_user() -> str:
    """Return the user name pytest puts in ``pytest-of-<user>`` (``tmpdir.py`` ``get_user``)."""
    try:
        return getpass.getuser() or "unknown"
    except (ImportError, OSError, KeyError):
        return "unknown"


def _pytest_of_child_in(root: Path, footage: Path) -> Path | None:
    """Return a ``root/pytest-of-*`` entry that is, or leads into, ``footage``, if any.

    pytest writes its numbered folders into ``root/pytest-of-<user>``
    (``tmpdir.py:160``; ``pytest-of-unknown`` is its fallback, ``:165``). Those two
    children are checked DIRECTLY, listed or not, so a link there is found even when
    the root cannot be listed or the link's spelling differs in case. An error
    resolving them propagates: the check could not be made. Any other ``pytest-of-*``
    entry found by listing the root is a best-effort extra; a listing error is ignored.

    Args:
        root: The canonical temp root.
        footage: The canonical footage folder.

    Returns:
        The offending entry, or None.

    Raises:
        OSError: If pytest's own child cannot be resolved.
        RuntimeError: If resolving it meets a symlink loop.
        ValueError: If a path is not usable.
    """
    direct = [root / f"{_PYTEST_OF}{name}" for name in (_pytest_user(), "unknown")]
    for child in direct:
        if _inside_or_equal(_canonical(child), footage):
            return child
    try:
        listed = [c for c in root.iterdir() if os.path.normcase(c.name).startswith(_PYTEST_OF)]
    except OSError:
        return None
    for child in listed:
        try:
            if _inside_or_equal(_canonical(child), footage):
                return child
        except (OSError, RuntimeError, ValueError):
            continue
    return None


def _temp_root_candidates() -> list[str]:
    """Return the temp-root candidates to check, without touching disk.

    ``tempfile.gettempdir()`` picks the first candidate in which it can create and
    delete a probe file, which would write inside a footage folder named by
    ``TMPDIR``/``TEMP``/``TMP``. The guard mirrors the candidate list
    (``tempfile._candidate_tempdir_list``, Python 3.12) and approximates the probe
    with "an existing directory that ``os.access`` accepts for writing", stopping
    there. Candidates before the chosen one are still returned, so the approximation
    can only over-refuse, never miss the root CPython would use.

    Returns:
        The cached ``tempfile.tempdir`` alone if already chosen, else every
        candidate up to and including the first usable one.
    """
    if tempfile.tempdir is not None:
        return [os.fsdecode(tempfile.tempdir)]
    candidates = [value for name in ("TMPDIR", "TEMP", "TMP") if (value := os.getenv(name))]
    if os.name == "nt":
        candidates += [
            os.path.expanduser(r"~\AppData\Local\Temp"),
            os.path.expandvars(r"%SYSTEMROOT%\Temp"),
            r"c:\temp",
            r"c:\tmp",
            r"\temp",
            r"\tmp",
        ]
    else:
        candidates += ["/tmp", "/var/tmp", "/usr/tmp"]
    candidates.append(os.getcwd())
    chosen: list[str] = []
    for candidate in candidates:
        chosen.append(candidate)
        if os.path.isdir(candidate) and os.access(candidate, os.W_OK):
            break
    return chosen


def _offending_root(config: pytest.Config, footage: Path) -> str | None:
    """Return a description of the temp root that threatens ``footage``, if any.

    Mirrors ``_pytest.tmpdir.TempPathFactory`` (pytest 8.4): ``__init__`` takes
    ``os.path.abspath(basetemp)``; ``getbasetemp`` removes and recreates a given
    basetemp, else uses ``PYTEST_DEBUG_TEMPROOT`` or ``tempfile.gettempdir()``
    as the root of ``pytest-of-<user>/``.

    Args:
        config: The pytest configuration.
        footage: The canonical footage folder.

    Returns:
        A short description of the offending root, or None when all is clear.
    """
    basetemp = config.option.basetemp
    if basetemp:
        root = _canonical(basetemp)
        if _inside_or_equal(root, footage) or _inside_or_equal(footage, root):
            return f"--basetemp {basetemp}"
        return None
    from_env = os.environ.get("PYTEST_DEBUG_TEMPROOT")
    if from_env:
        origin, roots = "PYTEST_DEBUG_TEMPROOT", [from_env]
    else:
        origin, roots = (
            "a default temp-root candidate (TMPDIR/TEMP/TMP or a system default)",
            _temp_root_candidates(),
        )
    for root_text in roots:
        root = _canonical(root_text)
        # pytest makes pytest-of-<user>/ under the root, so a footage folder there is hit too.
        if _inside_or_equal(root, footage) or _holds_pytest_of(root, footage):
            return f"{origin} {root_text}"
        if (child := _pytest_of_child_in(root, footage)) is not None:
            return (
                f"{origin} {root_text} (its {child.name} entry is or leads into the footage folder)"
            )
    return None


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Refuse to start when pytest's temp root would lie in the footage folder.

    Runs before pytest's own ``pytest_configure`` builds the temp-path factory, and
    so before the first ``tmp_path`` creates or clears any temp folder (see the
    module docstring for what this does not cover). Inert without a valid local
    configuration.

    Args:
        config: The pytest configuration.

    Raises:
        pytest.UsageError: If the temp root equals, lies inside (or, for
            ``--basetemp``, contains) the configured footage folder, or the check
            could not be made (an error resolving the temp root).
    """
    try:
        footage_raw = load_local_config().footage_path
    except (LocalConfigError, OSError):
        return
    try:
        footage = _canonical(footage_raw)
    except ValueError:
        return  # not a usable path (embedded NUL): an invalid configuration, so inert
    except (OSError, RuntimeError):
        # Unresolvable (e.g. a symlink loop): compare its absolute spelling and file identity.
        footage = Path(os.path.normcase(os.path.abspath(footage_raw)))
    try:
        offending = _offending_root(config, footage)
    except (OSError, RuntimeError, ValueError) as exc:
        raise pytest.UsageError(
            f"footage guard: the check could not be made (cannot resolve the pytest temp "
            f"root: {exc}); refusing to run with a footage folder configured at {footage_raw}"
        ) from None
    if offending is not None:
        raise pytest.UsageError(
            f"footage guard: refusing to run, {offending} is inside, equal to or above the "
            f"read-only footage folder {footage_raw}; pytest would write or delete there. "
            "Use a folder outside the footage folder (the working folder is fine)."
        )


def _footage_skip_reason() -> str | None:
    """Return why footage-marked tests must be skipped, or None when they can run.

    Returns:
        None if the footage folder is configured and present; otherwise a reason
        that distinguishes "not configured" from "configured but not an existing folder".
    """
    if footage_available():
        return None
    try:
        footage = load_local_config().footage_path
    except (LocalConfigError, OSError):
        return (
            "footage folder not configured; copy clearwater.local.example.toml "
            "to clearwater.local.toml and set footage_path"
        )
    return f"footage folder configured but not an existing folder: {footage}"


MACOS_SKIP_REASON = "macOS native leg (WP6.5)"
"""The skip reason of every ``macos`` test off darwin (AD-36; WP6.4)."""


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip ``macos`` tests off macOS, and ``footage`` tests when no footage folder exists.

    The ``macos`` policy backs up each module's explicit ``skipif``: a ``macos``-marked test
    is collected on every platform (strict markers; the gate's collection identity counts it)
    and skipped off darwin with :data:`MACOS_SKIP_REASON`, so no gate expression changes.
    """
    if sys.platform != "darwin":
        macos_skip = pytest.mark.skip(reason=MACOS_SKIP_REASON)
        for item in items:
            if item.get_closest_marker("macos") is not None:
                item.add_marker(macos_skip)
    reason = _footage_skip_reason()
    if reason is None:
        return
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if "footage" in item.keywords:
            item.add_marker(skip)


POSIX_HOME_FOLDER = "home"
"""The prefix of the per-test home folder :func:`_posix_home_redirect` makes (WP6.5 A4)."""

POSIX_XDG_FOLDERS = {
    "XDG_CONFIG_HOME": ".config",
    "XDG_DATA_HOME": ".local/share",
    "XDG_CACHE_HOME": ".cache",
    "XDG_STATE_HOME": ".local/state",
}
"""The XDG base-directory names :func:`_posix_home_redirect` sets, each to this folder under
the per-test home (the XDG defaults relative to ``HOME``; WP6.5 QA fix, CHARC ruling). The
folders are not created: the home stays empty until something writes there."""


@pytest.fixture(autouse=True)
def _posix_home_redirect(request: pytest.FixtureRequest) -> Iterator[None]:
    """On POSIX, point ``HOME`` and the XDG names at a fresh per-test folder (WP6.5 A4).

    On macOS ``Path.home() / "Library"`` holds Clearwater's settings and cache
    (``clearwater.config.paths.app_locations``), and on Linux the XDG variables, falling back
    to ``Path.home()``, do; ``Path.home()`` and ``os.path.expanduser`` read ``HOME`` there. So
    a test that reaches those locations without its own redirect would write the real
    account's ``~/Library/Application Support/Clearwater`` (or its XDG folders); this redirect
    makes the isolation structural, one place, for every test function (child processes
    inherit it). The folder is ``tmp_path_factory.mktemp("home")``, beside the test's own
    ``tmp_path`` rather than inside it, so a test that lists its ``tmp_path`` sees nothing
    new; ``XDG_CONFIG_HOME``, ``XDG_DATA_HOME``, ``XDG_CACHE_HOME`` and ``XDG_STATE_HOME``
    point at the :data:`POSIX_XDG_FOLDERS` paths under it. A test that sets ``HOME`` (or an
    XDG name) itself still wins: its ``monkeypatch`` change comes later and is undone first.
    Every name is restored after the test. Session- and module-scoped fixtures run before it
    and are not covered.

    The fixture requests no fixture but ``request`` and uses its OWN ``pytest.MonkeyPatch``,
    undone in a ``finally`` after the ``yield``. Requesting the test's ``monkeypatch`` would
    set that fixture up before :func:`_release_fft_plans` and so undo the test's patches
    AFTER that fixture's finalizer ran (teardown is last-in, first-out); a test that replaced
    ``clearwater.core.backend._probe_gpu`` then broke the release (the WP6.5 QA regression).

    NOT on Windows (``sys.platform == "win32"``): there isolation runs through ``APPDATA`` /
    ``LOCALAPPDATA``, and ``HOME`` feeds git and uv; the fixture yields without touching
    anything.

    Args:
        request: The test's fixture request (for the session temp-path factory).

    Yields:
        Nothing; the test runs with the redirect in place.
    """
    if sys.platform == "win32":
        yield
        return
    factory: pytest.TempPathFactory = request.getfixturevalue("tmp_path_factory")
    home = factory.mktemp(POSIX_HOME_FOLDER)
    patch = pytest.MonkeyPatch()
    try:
        patch.setenv("HOME", str(home))
        for name, relative in POSIX_XDG_FOLDERS.items():
            patch.setenv(name, str(home / relative))
        yield
    finally:
        patch.undo()


@pytest.fixture(autouse=True)
def _release_fft_plans(request: pytest.FixtureRequest) -> None:
    """Release the GPU backend's cuFFT plans after each test (WP3.21, CHARC ruling (A)).

    The FFT Gaussian leaves its plans in the calling thread's plan cache until something calls
    ``CupyBackend.release_fft_plans``; an export job does so at its end, a test calling the core
    directly does not, so the plans (and the pool blocks they hold) would reach the next test.
    After each test this calls that same release on the probed GPU backend, the one
    ``backend_for`` and ``select_backend`` return. The cache is per thread, not per backend
    object, so the release also clears plans made through another ``CupyBackend`` on this
    thread; before the process's first probe it does nothing. It imports nothing: it acts only
    when ``cupy`` and ``clearwater.core.backend`` are already loaded and the GPU has been
    probed, and it never touches ``cupy`` itself. When ``_probe_gpu`` has no ``cache_info``
    (a test replaced the cached probe and its patch is still in place) it returns without
    probing (WP6.5 QA fix).

    Args:
        request: The test's fixture request, which runs the release at teardown.
    """
    import sys

    def release() -> None:
        core_backend = sys.modules.get("clearwater.core.backend")
        if "cupy" not in sys.modules or core_backend is None:
            return
        cache_info = getattr(core_backend._probe_gpu, "cache_info", None)
        if cache_info is None:
            return  # a test replaced the probe: not the cached one, nothing to release
        if cache_info().currsize == 0:
            return  # never probed: no test reached the GPU backend
        gpu, _ = core_backend._probe_gpu()
        if gpu is not None:
            gpu.release_fft_plans()

    request.addfinalizer(release)


# fmt: off
def pair_streams(
    src_streams: list[dict], dst_streams: list[dict],
) -> list[tuple[dict, dict, tuple, int]]:
    """Pair matching stream kinds and codec tags in index order within each key.

    Args:
        src_streams: Source stream dictionaries with container indices.
        dst_streams: Destination stream dictionaries with container indices.

    Returns:
        Source, destination, pairing key and zero-based ordinal for each pair.

    Raises:
        AssertionError: If a pairing key has different source and destination counts.
    """
    src_groups, dst_groups = {}, {}
    for streams, groups in ((src_streams, src_groups), (dst_streams, dst_groups)):
        for stream in sorted(streams, key=lambda s: s["index"]):
            key = (stream.get("codec_type"), stream.get("codec_tag_string"))
            groups.setdefault(key, []).append(stream)
    assert {key: len(rows) for key, rows in src_groups.items()} == {
        key: len(rows) for key, rows in dst_groups.items()
    }, "stream pairing counts differ"
    return [
        (source, destination, key, ordinal)
        for key, sources in src_groups.items()
        for ordinal, (source, destination) in enumerate(zip(sources, dst_groups[key], strict=True))
    ]
# fmt: on


def _gx011627_run(command: list[str]) -> str:
    """Capture tool output in memory, withholding raw diagnostics on failures."""
    import subprocess

    try:
        result = subprocess.run(command, capture_output=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError("GX011627 tool failed; raw diagnostics withheld") from None
    if result.returncode:
        raise RuntimeError("GX011627 tool failed; raw diagnostics withheld")
    return result.stdout.decode("utf-8")


def _gx011627_document(path: Path) -> dict[str, Any]:
    """Return stream facts with location values discarded before comparison."""
    import json

    import video_fidelity as vf
    from clearwater.io.video import find_tool

    raw = json.loads(
        _gx011627_run(
            [
                str(find_tool("ffprobe")),
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    for item in [raw.get("format", {}), *raw.get("streams", [])]:
        tags = item.pop("tags", {})
        item["location_keys"] = sorted(k for k in tags if vf.location_like(k))
        item["tags"] = {k: v for k, v in tags.items() if not vf.location_like(k)}
    return raw


def _gx011627_packets(
    path: Path, stream: str | int, entries: tuple[str, ...]
) -> list[dict[str, Any]]:
    """Keep ordered packet facts and hashes in memory only, without decoding data."""
    import json

    from clearwater.io.video import find_tool

    return json.loads(
        _gx011627_run(
            [
                str(find_tool("ffprobe")),
                "-v",
                "error",
                "-select_streams",
                str(stream),
                "-show_packets",
                "-show_entries",
                "packet=" + ",".join(entries),
                "-show_data_hash",
                "MD5",
                "-of",
                "json",
                str(path),
            ]
        )
    ).get("packets", [])


def _gx011627_packet_rows(
    rows: list[dict[str, Any]], entries: tuple[str, ...]
) -> list[tuple[Any, ...]]:
    """Project packet fields without side data or payloads."""
    return [tuple(row.get(key) for key in entries) for row in rows]


def _gx011627_rotation(stream: dict[str, Any]) -> list[int]:
    """Read rotation from the stream's display matrix or rotation tag."""
    values = [s["rotation"] for s in stream.get("side_data_list", []) if "rotation" in s]
    return values if values else [int(stream.get("tags", {}).get("rotate", 0))]


def gx011627_trim_checks(
    source: Path, trim: Path, count: int, cut_text: str | None = None
) -> dict[str, Any]:
    """Compare a trim with its source using the ruled packet, stream and tag checks.

    Args:
        source: The original GX011627 file, read only.
        trim: The candidate stream copy under the session temp root.
        count: Expected video frame count derived from the source's keyframe cut.
        cut_text: Planned cut PTS, or None to derive the first source keyframe
            at or after three seconds independently of the supplied count.

    Returns:
        Named 4(a)-(e) verdicts and diagnostics containing only counts, booleans,
        stream kinds, codec tags, tag keys and the ruled reasons. Data-packet
        equality is reported separately and must also pass before consumption.
        Pairing-count mismatches fail stream parity, tags and data equality
        without preventing the independent packet checks from returning.
    """
    from collections import Counter
    from fractions import Fraction

    original, copied = _gx011627_document(source), _gx011627_document(trim)
    src, dst = original["streams"], copied["streams"]
    fields = ("pts_time", "duration_time", "size", "flags", "data_hash")
    source_video = _gx011627_packets(source, "v:0", fields)
    if cut_text is None:
        cut_text = next(
            (
                p["pts_time"]
                for p in source_video
                if "K" in p["flags"] and Fraction(p["pts_time"]) >= 3
            ),
            None,
        )
    cut = Fraction(cut_text) if cut_text is not None else None
    cut_on_keyframe = (
        cut is not None
        and 0 <= count < len(source_video)
        and "K" in source_video[count]["flags"]
        and Fraction(source_video[count]["pts_time"]) == cut
    )
    a = source_video[:count]
    b = _gx011627_packets(trim, "v:0", (*fields, "pts"))
    packet_count_equal = len(b) == count
    packets_equal = len(a) == count and _gx011627_packet_rows(a, fields) == _gx011627_packet_rows(
        b[:count], fields
    )
    checks = {
        "4a": count >= 66,
        "4b": packet_count_equal and packets_equal,
    }
    video = next((s for s in dst if s.get("codec_type") == "video"), None)
    checks["4c"] = (
        cut_on_keyframe
        and video is not None
        and Fraction(video["time_base"]) == Fraction(1, 30000)
        and sorted(int(p["pts"]) for p in b) == [k * 1001 for k in range(count)]
    )
    roster = ("codec_type", "codec_name", "codec_tag_string")
    parity = sorted(_gx011627_packet_rows(src, roster), key=repr) == sorted(
        _gx011627_packet_rows(dst, roster), key=repr
    )
    src_counts, dst_counts = (
        Counter((s.get("codec_type"), s.get("codec_tag_string")) for s in streams)
        for streams in (src, dst)
    )
    pairing_equal = src_counts == dst_counts
    pairing_differences = [
        {
            "codec_type": key[0],
            "codec_tag_string": key[1],
            "source_count": src_counts[key],
            "trim_count": dst_counts[key],
        }
        for key in sorted(src_counts.keys() | dst_counts.keys(), key=repr)
        if src_counts[key] != dst_counts[key]
    ]
    paired = pair_streams(src, dst) if pairing_equal else []
    parity = parity and pairing_equal
    details = []
    for left, right, key, ordinal in paired:
        kind = left.get("codec_type")
        keys = (
            (
                "width",
                "height",
                "pix_fmt",
                "color_range",
                "color_space",
                "color_transfer",
                "color_primaries",
            )
            if kind == "video"
            else ("sample_rate", "channels")
            if kind == "audio"
            else ()
        )
        same = all(left.get(k) == right.get(k) for k in keys)
        if kind == "video":
            same = same and _gx011627_rotation(left) == _gx011627_rotation(right)
        parity = parity and same
        details.append(
            {
                "source_index": left["index"],
                "trim_index": right["index"],
                "pairing_key": key,
                "ordinal": ordinal,
                "kind": kind,
                "fields_equal": same,
            }
        )
    for tag in ("gpmd", "tmcd"):
        parity = parity and (
            any(s.get("codec_type") == "data" and s.get("codec_tag_string") == tag for s in src)
            == any(s.get("codec_type") == "data" and s.get("codec_tag_string") == tag for s in dst)
        )
    checks["4d"] = parity
    differences, semantic_checks, location_presence = [], [], True
    pairs = [
        (
            "format",
            original.get("format", {}),
            copied.get("format", {}),
            ALLOWED_TAG_DIFFS["format"],
        )
    ]
    audio_timecode = []
    for left, right, key, ordinal in paired:
        allowed = ALLOWED_TAG_DIFFS["stream"]
        if key[0] == "audio":
            allowed = allowed | ALLOWED_TAG_DIFFS["audio"]
            audio_timecode.append(
                {
                    "pairing_key": key,
                    "ordinal": ordinal,
                    "source_has_key": "timecode" in left["tags"],
                    "trim_has_key": "timecode" in right["tags"],
                    "survives_by_key": "timecode" in left["tags"] and "timecode" in right["tags"],
                }
            )
        scope = "stream-" + str(key[0]) + "-" + str(key[1]) + "-" + str(ordinal)
        pairs.append((scope, left, right, allowed))
    for scope, left, right, allowed in pairs:
        location_presence = location_presence and left["location_keys"] == right["location_keys"]
        lt, rt = left["tags"], right["tags"]
        keys = set(lt) | set(rt) | ({"creation_time"} if scope == "format" else set())
        for key in sorted(keys):
            semantic_allowed = None
            if scope == "format" and key == "creation_time":
                parts = rt[key].split(";") if isinstance(rt.get(key), str) else []
                semantic_allowed = (
                    key in lt
                    and key in rt
                    and bool(parts)
                    and all(part == lt[key] for part in parts)
                )
                semantic_checks.append(
                    {
                        "scope": "format",
                        "key": "creation_time",
                        "parts": len(parts),
                        "every_part_equals_source": semantic_allowed,
                    }
                )
            if (
                lt.get(key) != rt.get(key)
                or (key in lt) != (key in rt)
                or semantic_allowed is False
            ):
                permitted = semantic_allowed if semantic_allowed is not None else key in allowed
                differences.append(
                    {
                        "scope": scope,
                        "key": key,
                        "allowed": permitted,
                        "reason": "format creation_time semantic rule R-e"
                        if semantic_allowed is not None
                        else "muxer-written key ruled in R-c"
                        if permitted
                        else "not allowed by R-c; values withheld",
                    }
                )
    checks["4e"] = (
        pairing_equal and location_presence and not any(not d["allowed"] for d in differences)
    )
    # Data is never decoded: require the source prefix and its full count before T.
    # A failed pairing cannot establish per-stream tags or data-packet equality.
    data_checks = [] if pairing_equal else [{"equal": False, "reason": "pairing counts differ"}]
    data_fields = ("pts_time", "duration_time", "size", "data_hash")
    for left, right, key, ordinal in paired:
        if left.get("codec_type") != "data" or left.get("codec_tag_string") == "tmcd":
            continue
        x = _gx011627_packets(source, left["index"], data_fields)
        y = _gx011627_packets(trim, right["index"], data_fields)
        expected = [p for p in x if cut is not None and Fraction(p["pts_time"]) < cut]
        count_equal = cut is not None and len(y) == len(expected)
        data_packets_equal = bool(y) and _gx011627_packet_rows(
            x[: len(y)], data_fields
        ) == _gx011627_packet_rows(y, data_fields)
        same = count_equal and data_packets_equal
        data_checks.append(
            {
                "codec_tag": left.get("codec_tag_string"),
                "pairing_key": key,
                "ordinal": ordinal,
                "source_index": left["index"],
                "trim_index": right["index"],
                "source_packets": len(x),
                "expected_packets_before_cut": len(expected),
                "trim_packets": len(y),
                "count_equal": count_equal,
                "packets_equal": data_packets_equal,
                "equal": same,
            }
        )
    record = {
        "checks": {k: "PASS" if v else "FAIL" for k, v in checks.items()},
        "4b_count": "PASS" if packet_count_equal else "FAIL",
        "4b_packets": "PASS" if packets_equal else "FAIL",
        "4c_cut_on_keyframe": "PASS" if cut_on_keyframe else "FAIL",
        "pairing_counts_equal": pairing_equal,
        "pairing_failure_reason": None if pairing_equal else "pairing counts differ",
        "pairing_differences": pairing_differences,
        "streams": [
            dict(zip(roster, row, strict=True)) for row in _gx011627_packet_rows(src, roster)
        ],
        "stream_details": details,
        "tag_differences": differences,
        "semantic_tag_checks": semantic_checks,
        "location_key_presence_equal": location_presence,
        "data_packet_checks": data_checks,
        "audio_timecode_key_presence": audio_timecode,
        "allowed_tag_diff_keys": {scope: sorted(keys) for scope, keys in ALLOWED_TAG_DIFFS.items()},
    }
    return record


def _gx011627_source() -> Path:
    """Locate GX011627, skipping only an absent clip in a searched footage folder.

    Returns:
        The read-only source path.

    Raises:
        FootageLookupError: If the folder is missing, unsearchable or ambiguous.
    """
    from local_config import FootageLookupError, find_footage_file

    root = load_local_config().footage_path
    try:
        return find_footage_file("GX011627", root)
    except FootageLookupError as error:
        if error.matches or error.__cause__ is not None or not root.is_dir():
            raise
        pytest.skip("GX011627 is not in the footage folder")


def _gx011627_trim_plan(source: Path, output: Path) -> tuple[int, str, list[str]]:
    """Return the decode-order frame count, cut point and fixed stream-copy command."""
    import csv
    import io
    from fractions import Fraction

    from clearwater.io.video import find_tool, probe

    listing = _gx011627_run(
        [
            str(find_tool("ffprobe")),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "packet=pts_time,flags",
            "-of",
            "csv=p=0",
            "-read_intervals",
            "%+6",
            str(source),
        ]
    )
    rows = list(csv.reader(io.StringIO(listing)))
    choices = [
        (i, row[0])
        for i, row in enumerate(rows)
        if len(row) >= 2 and "K" in row[1] and Fraction(row[0]) >= 3
    ]
    assert choices, "GX011627: no keyframe at or after 3 seconds"
    count, cut_text = choices[0]
    info = probe(source)
    maps = ["-map", "0:v:0"]
    for audio in info.audio:
        maps += ["-map", "0:" + str(audio.index)]
    for data in info.data:
        if data.codec_tag != "tmcd":
            maps += ["-map", "0:" + str(data.index)]
    command = [
        str(find_tool("ffmpeg")),
        "-nostdin",
        "-hide_banner",
        "-v",
        "error",
        "-y",
        "-i",
        str(source),
        *maps,
        "-c",
        "copy",
        "-map_metadata",
        "0",
        "-map_metadata:s:v:0",
        "0:s:v:0",
        "-write_tmcd",
        "1",
        "-video_track_timescale",
        str(info.video.time_base.denominator),
        "-frames:v",
        str(count),
        "-t",
        cut_text,
        "-movflags",
        "use_metadata_tags",
        "-f",
        "mp4",
        str(output),
    ]
    return count, cut_text, command


@pytest.fixture(scope="session")
def gx011627_trim(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Path, int]]:
    """Yield one guarded stream copy of GX011627 and remove its folder at teardown.

    Args:
        tmp_path_factory: Factory for the session's temp root under work/.

    Yields:
        The trim path and its source-derived frame count, after every check passes.
    """
    import shutil

    source = _gx011627_source()
    footage = _canonical(load_local_config().footage_path)
    base = _canonical(tmp_path_factory.getbasetemp())
    assert not _inside_or_equal(base, footage), "GX011627 temp root is inside footage"
    folder = tmp_path_factory.mktemp("gx011627-trim", numbered=False)
    resolved = _canonical(folder)
    assert resolved.is_relative_to(base), "GX011627 trim folder escaped the session root"
    assert not _inside_or_equal(resolved, footage), "GX011627 trim folder is inside footage"
    trim = folder / "GX011627-trim.mp4"
    try:
        count, cut_text, command = _gx011627_trim_plan(source, trim)
        _gx011627_run(command)
        record = gx011627_trim_checks(source, trim, count, cut_text)
        for name in ("4a", "4b", "4c", "4d", "4e"):
            assert record["checks"][name] == "PASS", name
        assert all(item["equal"] for item in record["data_packet_checks"]), "data packets"
        yield trim, count
    finally:
        assert _canonical(folder) == resolved, "GX011627 trim folder changed at teardown"
        assert resolved.is_relative_to(base) and not _inside_or_equal(resolved, footage)
        shutil.rmtree(folder)


@pytest.fixture(
    scope="session",
    params=[
        pytest.param("trim", id="trim"),
        pytest.param("full", id="full", marks=pytest.mark.fullclip),
    ],
)
def gx011627(request: pytest.FixtureRequest) -> Iterator[tuple[Path, int]]:
    """Yield the session trim, or the unchanged full source behind fullclip.

    Args:
        request: Session parameter; the trim fixture is requested only for trim.

    Yields:
        The selected source path and its expected frame count (681 for full).
    """
    if request.param == "trim":
        yield request.getfixturevalue("gx011627_trim")
    else:
        yield _gx011627_source(), GX011627_FRAMES
