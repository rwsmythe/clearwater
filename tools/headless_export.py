"""Headless export runner: drive a photo export or batch without the interface (WP4.1, test tool).

A test tool, not a product feature (plan section 6, WP4.1): acceptance tests (WP5.1) and manual
runs drive the product's composition root (:mod:`clearwater.app.composition`) through one
:func:`clearwater.jobs.run_batch` on the caller's thread, one job at a time (DR-62). Every write
goes through the export engine and ``SafeWrite``; this tool writes nothing itself but the record
file it is asked for (``--settings-dir``'s loader, ``clearwater.config.load_settings``, renames a
corrupt ``settings.json`` beside itself, D89). It loads no PySide6, and with ``--force-cpu`` no
CuPy.

Library API: :func:`route`, :func:`requests_for`, :func:`parameters_for`,
:func:`write_target_refusal`, :func:`check_outputs`, :func:`run`, :func:`record_json`,
:func:`exit_status` and :func:`main`. Command line::

    uv run python tools/headless_export.py PATH [PATH ...] (--out DIR | --beside-source)
        [--suffix S] [--bit-depth {8,16}] [--no-provenance] [--force-cpu] [--encoder NAME]
        [--quality {high,standard,draft}] [--ten-bit] [--cache-limit-bytes N] [--method ID]
        [--parameters FILE | --neutral] [--settings-dir DIR] [--record FILE]

Kinds are decided by extension exactly as ``clearwater.gui.sources.route`` decides them; a
sidecar (D83) or an unknown extension is a failed item with the interface's text and the batch
goes on (D81). In WP4.1 a video item fails with ``UNAVAILABLE_TEXT`` (WP4.2 adds video).

Exit status: 0 when every item is done (with or without warnings); 1 when any item failed, was
cancelled or was not run; 2 for a usage refusal, with nothing run (a bad flag, a missing
``--out`` folder, an invalid suffix (given or loaded), an unknown method, a parameter file that
is unreadable, over the importer's 1 MiB cap or not valid for its method, a settings file that
cannot be used, an unreadable local configuration, a write target the footage check refuses
when a footage folder is configured (:func:`write_target_refusal`: an output folder, the folder
beside a source, the settings folder and file, or the record file inside the footage folder
however spelled, reached through a link, junction or short 8.3 name, or spelled as a stream,
extended-length or device path), a ``--record`` file that exists or does not end in ``.json``).
A record file that appears during the run is not written, and one that cannot be written is
removed if this run created it (absent a concurrent replacement of the path by another
process): a message, status 1.
Ctrl-C sets the batch's cancel flag: the running job stops at its next check and leaves no
partial output (D44), the rest are not run (D45), and the exit status is 1. A Ctrl-C after the
last item's last check (in its commit) leaves its output and still gives status 1 with
``"cancelled": true``; one while the record is written leaves the record whole and gives
status 1.

The record (``--record FILE``, JSON, ``"schema": 1``, fields additive only) names sources and
outputs by file name only, never by full path (as AD-13 rules for provenance), and adds no
location tag and no EXIF content of its own. It carries the engine's failure texts verbatim
apart from folder redaction (DR-35 (a)), and a reader failure text (``clearwater.io.photo``,
for example a malformed TIFF Orientation) may quote the malformed tag's value; so may the
summary line and the batch WARNING that carry the same text. The summary lines go to stdout
and the ``[i/n]`` progress messages to stderr. Every folder the run knows (the output folder,
each source's folder, the settings, record and parameter folders, and the local
configuration's folder) is shown by its NAME in every record field and printed line, one
:class:`Redactor` applied at each exit point: an engine text such as the D87 free-space refusal
names its folder; an ``argparse`` refusal is redacted against the paths its arguments name. This
tool installs no logging handler, so ``run_batch``'s INFO report (which names full output paths)
is not emitted; Python's last-resort handler prints WARNING lines only, and while :func:`main`
runs a filter on that handler passes them through the same redactor and prints no tag value
from the EXIF module's own WARNINGs (each of their arguments, and every ``%r`` argument, is
shown as ``...``); :func:`run` does the same while its batch runs. A process that installs its
own logging handlers (a host program, pytest) receives the engine's records as they are logged,
full paths and tag values included: the runner redacts what it prints and records, not another
program's logging.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import json
import logging
import os
import re
import signal
import sys
import threading
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Any, Final, Literal, NoReturn, cast

import clearwater
from clearwater.app import composition
from clearwater.config import (
    SETTINGS_FILE_NAME,
    check_parameter_set_keys,
    load_settings,
    migrate,
    new_parameter_set,
)
from clearwater.config.presets import MAX_PRESET_BYTES
from clearwater.interfaces import (
    JobResult,
    ParameterSet,
    Progress,
    Settings,
    validate_parameter_set,
)
from clearwater.interfaces.parameters import loads_object
from clearwater.io.video.inputs import ascii_text, is_sidecar, sidecar_fault
from clearwater.jobs import BatchReport, MediaKind, final_output_path, run_batch, validate_suffix
from clearwater.jobs.export_seam import ExportJobs, ExportRequest
from local_config import LocalConfigError, default_config_path, load_local_config

SCHEMA: Final = 1
"""The record's schema number; fields are only ever added under it."""

PHOTO_SUFFIXES: Final = frozenset(
    {".heic", ".heif", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".dng"}
)
"""Photo extensions, equal to ``clearwater.gui.sources.PHOTO_SUFFIXES`` (a ``gui`` test pins it)."""

VIDEO_SUFFIXES: Final = frozenset({".mp4"})
"""Video extensions, equal to ``clearwater.gui.sources.VIDEO_SUFFIXES`` (a ``gui`` test pins it)."""

PROVENANCE_KEYS: Final = ("source", "settings")
"""The provenance keys a parameter file's set drops, as ``PresetStore`` import drops them."""

STATES_DONE: Final = frozenset({"done", "done with warnings"})
"""The item states that give exit status 0."""

EXTENDED_PREFIXES: Final = (("\\\\?\\UNC\\", "\\\\"), ("\\\\?\\", ""))
"""Windows extended-length prefixes and what each stands for, longest first (:func:`plain_path`)."""

TAG_VALUE_LOGGER: Final = "clearwater.io.photo.exif"
"""The logger whose WARNING arguments may carry EXIF content; none is printed (:func:`main`)."""


class RunnerRefusalError(Exception):
    """A usage refusal: nothing is run and the command line exits with status 2."""


class _Configured:
    """The type of :data:`CONFIGURED`."""


CONFIGURED: Final = _Configured()
"""Read the footage folder from ``clearwater.local.toml`` (:func:`configured_footage_folder`)."""


@dataclass(frozen=True)
class RefusedRequest(ExportRequest):
    """A request for a path the runner refuses as the interface does (a sidecar, an unknown type).

    It goes through the batch like any item and fails at once with :attr:`refusal`, opening no
    file. ``kind`` is a placeholder no engine sees.

    Attributes:
        refusal: The failure text, the interface's refusal text for the path.
    """

    refusal: str = ""


class RunnerProgress:
    """The batch's ``Progress``: a cancel flag, and the report messages passed to a callback."""

    def __init__(self, on_report: Callable[[str], None] | None = None) -> None:
        """Create the flag, not set.

        Args:
            on_report: Called with each report message; none when None.
        """
        self._event = threading.Event()
        self._on_report = on_report

    def report(self, done: int, total: int | None, message: str) -> None:
        """Pass the message on (IF-8 ``Progress.report``)."""
        if self._on_report is not None:
            self._on_report(message)

    def cancelled(self) -> bool:
        """Return whether :meth:`cancel` was called (IF-8 ``Progress.cancelled``)."""
        return self._event.is_set()

    def cancel(self) -> None:
        """Ask the running job and the batch to stop (any thread; a signal handler)."""
        self._event.set()


class _WithRefusals:
    """The ``ExportJobs`` the batch runs: a :class:`RefusedRequest` fails, the rest pass on."""

    def __init__(self, exports: ExportJobs) -> None:
        self._exports = exports

    def job(self, request: ExportRequest) -> Callable[[Progress], JobResult]:
        """Return a failing job for a refused request, else the wrapped engine's job."""
        if isinstance(request, RefusedRequest):
            text = request.refusal

            def refuse(progress: Progress) -> JobResult:
                return JobResult(
                    ok=False, outputs=(), warnings=(), failure=text, device="none", elapsed_s=0.0
                )

            return refuse
        return self._exports.job(request)


@dataclass(frozen=True)
class RunRecord:
    """What one run did.

    Attributes:
        report: The batch report, one item per request in order.
        routes: Each item's route: ``"photo"``, ``"video"`` or ``"refused"``.
        parameters_from: Where the parameters came from: ``"defaults"``, ``"file"``,
            ``"neutral"`` or ``"given"`` (a library caller's own set).
        elapsed_s: The batch's wall time in seconds (information only).
        folders: The folders the record's texts show by name only (:class:`Redactor`).
        cancel_requested: The cancel flag was set when the batch ended, even after the last
            item's last check (a Ctrl-C in its commit), so the run counts as cancelled.
    """

    report: BatchReport
    routes: tuple[str, ...]
    parameters_from: str
    elapsed_s: float
    folders: tuple[Path, ...] = ()
    cancel_requested: bool = False


class Redactor:
    r"""Replace every spelling of known folders in a text by the folder's name (case-insensitive).

    The spellings are the path as given, resolved and without a Windows extended-length prefix
    (:func:`plain_path`), plus a UNC path's extended spelling; each with backslashes, with doubled
    backslashes (an ``OSError`` or ``argparse`` text quotes the path's ``repr``) and with forward
    slashes; and each of those also with its non-ASCII characters escaped as :func:`ascii_text`
    escapes them (engine texts are escaped before they reach the runner), and that escaped form
    with its backslashes doubled (the ``repr`` of an escaped path). Every form also matches
    with apostrophes escaped as ``\'`` by ``repr``. Each escape matches the
    escape of any letter case of its character (``\xe9`` and ``\xc9`` alike, Reviewer B B2):
    ``re.IGNORECASE`` alone cannot equate two escapes. A spelling without a separator says
    nothing a name does not, so it is not replaced; nor is a folder without a name (a drive
    root).
    """

    def __init__(self, folders: Iterable[Path]) -> None:
        """Build the patterns, the longest spelling first.

        Args:
            folders: The folders to show by name only.
        """
        forms: dict[str, tuple[int, str]] = {}  # pattern -> (the literal's length, name)
        quoted_forms: dict[str, tuple[int, str]] = {}
        for folder in folders:
            resolved = Path(folder).resolve()
            paths = [Path(folder), resolved, plain_path(resolved)]
            if str(paths[2]).startswith("\\\\"):  # a UNC path: also its extended spelling
                paths.append(Path("\\\\?\\UNC\\" + str(paths[2])[2:]))
            for path in paths:
                if not path.name:
                    continue
                text, name = str(path), ascii_text(path.name)
                for base in (text, text.replace("\\", "\\\\"), path.as_posix()):
                    if "\\" not in base and "/" not in base:
                        continue
                    escaped = ascii_text(base)
                    for pattern, length, quoted_length in (
                        (re.escape(base), len(base), len(base)),
                        (_escaped_pattern(base, doubled=False), len(escaped), len(escaped)),
                        (
                            _escaped_pattern(base, doubled=True),
                            len(escaped) * 2,
                            len(escaped) + escaped.count("\\"),
                        ),
                    ):
                        forms.setdefault(pattern, (length, name))
                        if "'" in base:
                            quoted = pattern.replace("'", re.escape(r"\'"))
                            quoted_forms.setdefault(quoted, (quoted_length + base.count("'"), name))
        # Match the escaped-apostrophe spellings before an ordinary parent-folder
        # spelling can replace their prefix. Keep the original forms' ordering.
        self._patterns = [
            (re.compile(pattern, re.IGNORECASE), name)
            for pattern, (_, name) in (
                sorted(quoted_forms.items(), key=lambda item: -item[1][0])
                + sorted(forms.items(), key=lambda item: -item[1][0])
            )
        ]

    def __call__(self, text: str) -> str:
        """Return ``text`` with every known folder shown by its name, ASCII-safe."""
        for pattern, name in self._patterns:
            text = pattern.sub(name.replace("\\", r"\\"), text)  # the name, literally
        return ascii_text(text)


def _escaped_pattern(text: str, *, doubled: bool) -> str:
    """A pattern matching ``text`` as :func:`ascii_text` escapes it, in any letter case.

    Each non-ASCII character matches the escape of any of its case forms; with ``doubled`` every
    backslash (an escape's or a separator's) is doubled, as a ``repr`` quotes it.
    """
    parts = []
    for char in text:
        if char.isascii():
            parts.append(re.escape(char * 2 if doubled and char == "\\" else char))
            continue
        cases = sorted({char, char.lower(), char.upper(), char.casefold(), char.title()})
        escapes = [ascii_text(case) for case in cases]
        if doubled:
            escapes = [escape.replace("\\", "\\\\") for escape in escapes]
        parts.append("(?:" + "|".join(re.escape(escape) for escape in escapes) + ")")
    return "".join(parts)


def folders_of(requests: Sequence[ExportRequest]) -> tuple[Path, ...]:
    """Return the folders a run's texts may name: each output folder and each source's folder.

    Args:
        requests: The run's requests.

    Returns:
        The folders, in first-seen order, without repeats.
    """
    found: dict[str, Path] = {}
    for request in requests:
        for folder in (request.settings.output_folder, request.source.parent):
            if folder is not None:
                found.setdefault(str(folder), Path(folder))
    return tuple(found.values())


class _RedactingFilter(logging.Filter):
    """A filter on the last-resort handler that redacts each record's text (:func:`main`).

    No tag value is printed: every argument of a :data:`TAG_VALUE_LOGGER` record, and every
    ``%r`` argument (the photo modules log a tag value with ``%r``), is shown as ``...``.
    """

    def __init__(self, redact: Redactor) -> None:
        super().__init__()
        self._redact = redact

    def filter(self, record: logging.LogRecord) -> bool:
        """Replace the record's message by its redacted text; keep the record."""
        record.msg = self._redact(_without_tag_values(record))
        record.args = None
        return True


def _without_tag_values(record: logging.LogRecord) -> str:
    """Return the record's message with its tag-value arguments shown as ``...``."""
    message, args = str(record.msg), record.args
    if not args:  # logging formats nothing without arguments
        return message
    if not isinstance(args, tuple):  # a mapping (not used by the photo modules)
        return record.getMessage() if record.name != TAG_VALUE_LOGGER else message
    conversions = list(re.finditer(r"%[-#0 +]*\d*(?:\.\d+)?[a-zA-Z%]", message))
    if sum(match.group() != "%%" for match in conversions) != len(args):
        return message  # not a plain %-format: the fixed text, no argument
    pieces: list[str] = []
    start, given = 0, iter(args)
    for match in conversions:
        pieces.append(message[start : match.start()])
        start = match.end()
        if match.group() == "%%":
            pieces.append("%")
            continue
        arg = next(given)
        if record.name == TAG_VALUE_LOGGER or match.group().endswith("r"):
            pieces.append("...")
            continue
        try:
            pieces.append(match.group() % (arg,))
        except (TypeError, ValueError):
            return message  # a malformed record: the fixed text, no argument
    return "".join(pieces) + message[start:]


@contextlib.contextmanager
def _redacted_last_resort(redact: Redactor) -> Iterator[None]:
    """Redact what Python's last-resort handler prints while the block runs (no handler added)."""
    handler = logging.lastResort
    if handler is None:
        yield
        return
    log_filter = _RedactingFilter(redact)
    handler.addFilter(log_filter)
    try:
        yield
    finally:
        handler.removeFilter(log_filter)


def route(path: Path) -> Literal["photo", "video"] | str:
    """Decide an item's kind by extension, as ``clearwater.gui.sources.route`` does.

    Args:
        path: The source path (not opened).

    Returns:
        ``"photo"`` or ``"video"``, or the refusal text (the interface's) for a sidecar (D83) or
        an extension that is neither a photo's nor a video's.
    """
    if is_sidecar(path):
        return sidecar_fault(path).message
    suffix = path.suffix.lower()
    if suffix in PHOTO_SUFFIXES:
        return "photo"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    return f"{ascii_text(path.name)} is not a supported photo or video file."


def requests_for(
    paths: Sequence[Path], *, parameters: ParameterSet, settings: Settings
) -> list[ExportRequest]:
    """Build one export request per path, in order.

    Args:
        paths: The sources.
        parameters: The parameter set every item renders with.
        settings: The settings every item exports with.

    Returns:
        The requests; a refused path (see :func:`route`) gives a :class:`RefusedRequest`.
    """
    requests: list[ExportRequest] = []
    for path in paths:
        source = Path(path)
        kind = route(source)
        if kind == "photo":
            requests.append(ExportRequest(source, "photo", parameters, settings))
        elif kind == "video":
            requests.append(ExportRequest(source, "video", parameters, settings))
        else:
            requests.append(RefusedRequest(source, "photo", parameters, settings, kind))
    return requests


def read_parameter_file(path: Path) -> ParameterSet:
    """Read an AD-13 preset JSON file as a parameter set.

    A file over the importer's cap (``MAX_PRESET_BYTES``, 1 MiB) is refused unread. The
    document is decoded as the importer decodes it (``loads_object``: one JSON object, no
    non-finite number anywhere), migrated (``clearwater.config.migrate``), its ``source`` and
    ``settings`` provenance keys dropped and its keys checked (``check_parameter_set_keys``): the
    forms ``PresetStore.import_preset`` reads, a preset and a preset with only those two keys added.
    Any other key is refused, as the importer refuses it; so is the provenance text the photo
    writer embeds when it adds ``profile`` for a built-in profile (an open item owned by CHARC).

    Args:
        path: The JSON file.

    Returns:
        The parameter set.

    Raises:
        RunnerRefusalError: The file cannot be read or is not a parameter set.
    """
    name = ascii_text(Path(path).name)
    try:
        size = Path(path).stat().st_size
        if size > MAX_PRESET_BYTES:  # the importer's cap
            raise ValueError(f"the file is {size} bytes; the cap is {MAX_PRESET_BYTES} bytes")
        data = loads_object(Path(path).read_text(encoding="utf-8"))
        data = migrate("preset", data)
        kept = {key: value for key, value in data.items() if key not in PROVENANCE_KEYS}
        parameter_set = ParameterSet.from_dict(kept)
        check_parameter_set_keys(parameter_set, name)
    except (OSError, UnicodeDecodeError, ValueError, RecursionError, OverflowError) as exc:
        raise RunnerRefusalError(
            f"{name} is not a readable parameter file: {ascii_text(str(exc))}"
        ) from exc
    return parameter_set


def parameters_for(
    method_id: str | None = None, *, file: Path | None = None, neutral: bool = False
) -> ParameterSet:
    """Return the parameter set of a run: a file's, the method's neutral values, or its defaults.

    Args:
        method_id: The method; ``"c3"`` (D16) when None. Must be None when ``file`` is given (the
            file names its method).
        file: An AD-13 preset or provenance JSON file (:func:`read_parameter_file`).
        neutral: Every parameter of the method at its IF-3 ``neutral`` value (V9).

    Returns:
        The parameter set; for the defaults an empty one (the engine fills in the defaults).

    Raises:
        RunnerRefusalError: ``file`` with ``method_id`` or with ``neutral``, an unknown method,
            an unreadable file, or a file's set that does not match its method's schema
            (``validate_parameter_set``, as the importer validates it).
    """
    methods = composition.correction_methods()
    if file is not None:
        if method_id is not None:
            raise RunnerRefusalError(
                "--method cannot be combined with --parameters: the parameter file names its "
                "method."
            )
        if neutral:
            raise RunnerRefusalError("--neutral cannot be combined with --parameters.")
        parameter_set = read_parameter_file(file)
        method_id = parameter_set.method
        method = methods.get(method_id)
        if method is None:
            raise RunnerRefusalError(_unknown_method(method_id, methods))
        problems = validate_parameter_set(parameter_set, method_id, method.parameters)
        if problems:  # the importer's schema step
            raise RunnerRefusalError(
                f"{ascii_text(Path(file).name)} does not match method {ascii_text(method_id)!r}: "
                + "; ".join(ascii_text(problem.message) for problem in problems)
            )
        return parameter_set
    method_id = "c3" if method_id is None else method_id
    method = methods.get(method_id)
    if method is None:
        raise RunnerRefusalError(_unknown_method(method_id, methods))
    values = {p.name: p.neutral for p in method.parameters} if neutral else {}
    return new_parameter_set(method_id, values)


def _unknown_method(method_id: str, methods: Mapping[str, object]) -> str:
    """The refusal text of an unknown method id."""
    return (
        f"unknown correction method {ascii_text(method_id)!r}; "
        f"the methods are {', '.join(methods)}."
    )


def configured_footage_folder(config: Path | None = None) -> Path | None:
    """Return the footage folder of the local configuration, or None when there is none.

    Args:
        config: The configuration file; ``local_config.default_config_path()`` when None.

    Returns:
        The configured footage folder, or None when the configuration file does not exist.

    Raises:
        RunnerRefusalError: The configuration file exists but cannot be read.
    """
    path = default_config_path() if config is None else config
    if not path.exists():
        return None
    try:
        return load_local_config(path).footage_path
    except LocalConfigError as exc:
        raise RunnerRefusalError(
            f"the local configuration cannot be read, so the footage folder is unknown: {exc}"
        ) from exc


def plain_path(path: Path) -> Path:
    r"""Return ``path`` without a Windows extended-length prefix (``\\?\`` or ``\\?\UNC\``).

    Only a path whose text begins with the prefix changes; a resolved path on another operating
    system begins with ``/`` and never does.

    Args:
        path: Any path.

    Returns:
        The same path in its ordinary spelling.
    """
    text = str(path)
    for prefix, replacement in EXTENDED_PREFIXES:
        if text[: len(prefix)].upper() == prefix.upper():
            return Path(replacement + text[len(prefix) :])
    return Path(path)


def _resolved(path: Path) -> Path:
    """Return ``path`` resolved, in its ordinary spelling and resolved again (``..`` collapsed)."""
    resolved = Path(path).resolve()
    plain = plain_path(resolved)
    return resolved if plain == resolved else plain.resolve()


def inside(path: Path, folder: Path) -> bool:
    """Return whether ``path`` is ``folder`` or lies under it, however either is spelled.

    The paths are compared resolved, without an extended-length prefix (:func:`plain_path`) and
    case-normalised; and, when ``folder`` exists, ``path`` or its nearest existing ancestors are
    compared with it by file identity (``os.path.samestat``), which equates the remaining
    spellings of one folder (a share of the same drive, a short 8.3 name).

    Args:
        path: The path to test (need not exist).
        folder: The folder.

    Returns:
        True when ``path`` is inside ``folder``.
    """
    resolved, root = _resolved(path), _resolved(folder)
    texts = PurePath(os.path.normcase(str(resolved))), PurePath(os.path.normcase(str(root)))
    if texts[0] == texts[1] or texts[0].is_relative_to(texts[1]):
        return True
    try:
        root_stat = os.stat(root)
    except (OSError, ValueError):
        return False
    if not root_stat.st_ino:  # a file system without file identities: the text check stands
        return False
    for candidate in (resolved, *resolved.parents):
        try:
            if os.path.samestat(os.stat(candidate), root_stat):
                return True
        except (OSError, ValueError):
            continue
    return False


INSIDE_FOOTAGE: Final = "is inside the footage folder, which is read-only"
"""The refusal reason of a write target whose real place is inside the footage folder."""

THROUGH_A_LINK: Final = (
    "reaches its place through a link (a symbolic link, junction or other reparse point, or a "
    "short 8.3 name), which the footage check refuses"
)
"""The refusal reason of a write target with an existing path on the way that is not real."""

REFUSED_FORM: Final = (
    "is in a form the footage check refuses (a ':' stream name, or a \\\\?\\ or \\\\.\\ path)"
)
"""The refusal reason of a write target spelled as a stream, extended-length or device path."""


def _write_form_refusal(target: Path) -> str | None:
    r"""Return predicate (i)'s refusal for a stream, ``\\?\`` or ``\\.\`` path, else None."""
    text = str(target)
    if text.replace("/", "\\")[:4] in ("\\\\?\\", "\\\\.\\"):
        return REFUSED_FORM
    if ":" in os.path.splitdrive(text)[1]:
        return REFUSED_FORM
    return None


def write_target_refusal(target: Path, footage_folder: Path) -> str | None:
    r"""Return why a planned write to ``target`` is refused, or None when it may go ahead.

    The one footage check of every write the run plans (CHARC Q1 on Reviewer B's B1): a target
    passes only when all three hold:

    (i) after its drive or UNC prefix its text has no ``:`` (an NTFS stream name such as
    ``alias.jpg:record.json``), and it is not in a ``\\?\`` or ``\\.\`` form;
    (ii) every existing path on the way down to it (the target itself when it exists, a
    dangling link included) is its own real path (``os.path.realpath``, compared
    case-normalised): no symbolic link, junction or other reparse point, and no short 8.3 name;
    (iii) the real path of the deepest existing one lies outside the footage folder
    (:func:`inside`: resolved, prefix-free, case-normalised and by file identity).

    Residual: a hard link to a footage file placed outside the footage folder cannot be told
    apart by its path. The runner never writes over an existing file (D84), so only a stream
    name could reach the original, and (i) refuses every stream name.

    Args:
        target: A file or folder the run would write (need not exist).
        footage_folder: The read-only footage folder.

    Returns:
        None when the target passes; otherwise the reason (:data:`INSIDE_FOOTAGE`,
        :data:`THROUGH_A_LINK` or :data:`REFUSED_FORM`), which follows the target's name in the
        refusal text.
    """
    text = str(target)
    path = Path(os.path.abspath(text))
    existing = [p for p in (path, *path.parents) if os.path.lexists(p)]
    deepest = existing[0] if existing else path
    if inside(Path(os.path.realpath(deepest)), footage_folder):  # (iii), named first
        return INSIDE_FOOTAGE
    reason = _write_form_refusal(target)  # (i), shared with each planned output file
    if reason is not None:
        return reason
    for step in existing:
        if os.path.normcase(os.path.realpath(step)) != os.path.normcase(str(step)):
            return THROUGH_A_LINK
    return None


def check_outputs(requests: Sequence[ExportRequest], footage_folder: Path | None) -> None:
    """Refuse a run that would write inside the footage folder (question 9; DR-37 (c)).

    Each request's output folder is the one the export plans (``jobs.naming``): the output
    folder setting, or the source's own folder (``source.parent``, not the target of a linked
    source); each is checked with :func:`write_target_refusal` before anything runs.
    Each planned output file (photo or video) also passes the shared text-form predicate
    (i), :func:`_write_form_refusal`. Refused items plan no output, and an invalid suffix
    is left to the engine's own refusal (the CLI validates it earlier).

    Args:
        requests: The run's requests.
        footage_folder: The read-only footage folder; nothing is checked when None.

    Raises:
        RunnerRefusalError: An output folder, or the folder beside a source the outputs would go
            to, that :func:`write_target_refusal` refuses; or a planned output file in a
            refused text form.
    """
    if footage_folder is None:
        return
    for request in requests:
        folder = request.settings.output_folder
        if folder is not None:
            reason = write_target_refusal(folder, footage_folder)
            if reason is not None:
                raise RunnerRefusalError(f"the output folder {reason}.")
        else:
            reason = write_target_refusal(request.source.parent, footage_folder)
            if reason is not None:
                name = ascii_text(request.source.name)
                where = name if reason == INSIDE_FOOTAGE else f"the folder of {name}"
                raise RunnerRefusalError(
                    f"{where} {reason}: outputs beside it are refused; give --out."
                )
        if isinstance(request, RefusedRequest):
            continue
        try:
            output = final_output_path(
                request.source, request.settings, MediaKind(request.kind)
            )
        except ValueError:
            continue
        reason = _write_form_refusal(output)
        if reason is not None:
            raise RunnerRefusalError(f"the output for {ascii_text(request.source.name)} {reason}.")


def run(
    requests: Sequence[ExportRequest],
    *,
    exports: ExportJobs | None = None,
    progress: Progress | None = None,
    footage_folder: Path | _Configured | None = CONFIGURED,
    parameters_from: str = "given",
    known_folders: Sequence[Path] = (),
) -> RunRecord:
    """Run one batch over the requests, in order, on the caller's thread (G7; D45, D81; DR-62).

    While the batch runs, Python's last-resort handler prints its WARNING lines through a
    :class:`Redactor` of the run's folders (as :func:`main` does); a caller's own logging
    handlers receive the engine's records as logged.

    Args:
        requests: The items (:func:`requests_for`).
        exports: The export engine; ``composition.export_jobs()`` when None.
        progress: The batch's progress and cancel flag; a :class:`RunnerProgress` when None.
        footage_folder: The folder no output may go into (:func:`check_outputs`);
            :data:`CONFIGURED` reads it from the local configuration; None checks nothing.
        parameters_from: Recorded as :attr:`RunRecord.parameters_from`.
        known_folders: More folders the record shows by name only, beside :func:`folders_of`
            the requests.

    Returns:
        The record.

    Raises:
        RunnerRefusalError: The footage check refused the run, or a known folder could not
            be resolved for redaction; nothing ran.
    """
    folder = (
        configured_footage_folder() if isinstance(footage_folder, _Configured) else footage_folder
    )
    check_outputs(requests, folder)
    engine = _WithRefusals(composition.export_jobs() if exports is None else exports)
    folders = tuple(dict.fromkeys([*folders_of(requests), *map(Path, known_folders)]))
    start = time.perf_counter()
    batch_progress = progress or RunnerProgress()
    try:
        redact = Redactor(folders)
    except (OSError, RuntimeError) as exc:
        raise RunnerRefusalError("a given folder cannot be resolved for redaction.") from exc
    with _redacted_last_resort(redact):
        report = run_batch(engine, list(requests), batch_progress)
    routes = tuple(
        "refused" if isinstance(request, RefusedRequest) else request.kind for request in requests
    )
    elapsed = time.perf_counter() - start
    return RunRecord(report, routes, parameters_from, elapsed, folders, batch_progress.cancelled())


def record_object(record: RunRecord) -> dict[str, Any]:
    """Return the record as a JSON-native object (schema 1; file names only, never full paths).

    Every text field, the settings' included, passes through the run's :class:`Redactor`.

    Args:
        record: The run's record.

    Returns:
        The object.

    Raises:
        RunnerRefusalError: A known folder could not be resolved for redaction.
    """
    try:
        redact = Redactor(record.folders)
    except (OSError, RuntimeError) as exc:
        raise RunnerRefusalError("a given folder cannot be resolved for redaction.") from exc
    items: list[dict[str, Any]] = []
    for index, (item, kind) in enumerate(zip(record.report.items, record.routes, strict=True), 1):
        result = item.result
        items.append(
            {
                "index": index,
                "source": ascii_text(item.request.source.name),
                "kind": kind,
                "state": item.state,
                "outputs": [] if result is None else [ascii_text(p.name) for p in result.outputs],
                "warnings": [] if result is None else list(result.warnings),
                "failure": None if result is None else result.failure,
                "device": None if result is None else ascii_text(result.device),
                "elapsed_s": None if result is None else result.elapsed_s,
            }
        )
    first = record.report.items[0].request if record.report.items else None
    settings = first.settings if first is not None else None
    states = [item.state for item in record.report.items]
    data = {
        "schema": SCHEMA,
        "tool": "headless_export",
        "app_version": clearwater.__version__,
        "method": None if first is None else first.parameters.method,
        "parameters_from": record.parameters_from,
        "settings": None if settings is None else _settings_object(settings),
        "counts": record.report.counts(),
        "cancelled": record.cancel_requested
        or any(state in ("cancelled", "not run") for state in states),
        "elapsed_s": record.elapsed_s,
        "items": items,
    }
    return cast(dict[str, Any], _redacted(data, redact))


def _redacted(value: object, redact: Redactor) -> object:
    """Return a JSON-native value with every string in it passed through ``redact``."""
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [_redacted(entry, redact) for entry in value]
    if isinstance(value, dict):
        return {key: _redacted(entry, redact) for key, entry in value.items()}
    return value


def _settings_object(settings: Settings) -> dict[str, Any]:
    """The record's settings: every IF-10 field but the folder path and ``last_parameters``."""
    return {
        "beside_source": settings.output_folder is None,
        "output_suffix": ascii_text(settings.output_suffix),
        "png_bit_depth": settings.png_bit_depth,
        "provenance": settings.provenance,
        "force_cpu": settings.force_cpu,
        "video_encoder": ascii_text(settings.video_encoder),
        "quality_level": settings.quality_level,
        "ten_bit_for_eight_bit": settings.ten_bit_for_eight_bit,
        "cache_limit_bytes": settings.cache_limit_bytes,
    }


def record_json(record: RunRecord) -> str:
    """Return the record as JSON text (ASCII, indented).

    Args:
        record: The run's record.

    Returns:
        The JSON text.
    """
    return json.dumps(record_object(record), indent=2, ensure_ascii=True)


def exit_status(record: RunRecord) -> int:
    """Return the command line's exit status for a run that ran.

    Args:
        record: The run's record.

    Returns:
        0 when every item is done (with or without warnings) and no cancel was requested,
        else 1.
    """
    if record.cancel_requested:
        return 1
    return 0 if all(item.state in STATES_DONE for item in record.report.items) else 1


def summary_lines(record: RunRecord) -> list[str]:
    """Return the ASCII summary of a run: a count line, then each item with names only.

    Args:
        record: The run's record.

    Returns:
        The lines.
    """
    data = record_object(record)
    counts = ", ".join(f"{n} {state}" for state, n in data["counts"].items() if n)
    lines = [f"Batch of {len(data['items'])}: {counts}"]
    for item in data["items"]:
        lines.append(f"{item['index']}. {item['source']}: {item['state']}")
        lines.extend(f"   saved {name}" for name in item["outputs"])
        lines.extend(f"   warning: {text}" for text in item["warnings"])
        if item["state"] == "failed":
            lines.append(f"   failure: {item['failure']}")
    return lines


class _UsageError(Exception):
    """An ``argparse`` usage refusal, raised instead of printed so the text can be redacted."""


class _Parser(argparse.ArgumentParser):
    """An ``ArgumentParser`` whose usage refusals raise :class:`_UsageError` (:func:`main`)."""

    def error(self, message: str) -> NoReturn:
        """Raise the refusal; :func:`main` prints it redacted after the usage line."""
        raise _UsageError(message)


def _folders_named_in(argv: Sequence[str]) -> list[Path]:
    """Every path an argument could name, and its folder (a ``--flag=value`` value included)."""
    found: list[Path] = []
    for token in argv:
        value = token.split("=", 1)[1] if token.startswith("--") and "=" in token else token
        try:
            path = Path(value)
            path.resolve()
        except (OSError, ValueError):
            continue
        found += [path, path.parent]
    return found


def _parser() -> argparse.ArgumentParser:
    """The command-line parser."""
    parser = _Parser(
        prog="headless_export",
        description="Export photos through Clearwater's export engine without the interface.",
    )
    parser.add_argument("paths", nargs="+", type=Path, metavar="PATH", help="the sources")
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--out", type=Path, metavar="DIR", help="the output folder (must exist)")
    where.add_argument(
        "--beside-source", action="store_true", help="write each output beside its source (D34)"
    )
    parser.add_argument("--suffix", metavar="S", help="the output name suffix (D36)")
    parser.add_argument("--bit-depth", type=int, choices=(8, 16), help="the PNG bit depth (D22)")
    parser.add_argument("--no-provenance", action="store_true", help="embed no provenance (D91)")
    parser.add_argument("--force-cpu", action="store_true", help="process on the CPU (AD-9)")
    parser.add_argument("--encoder", metavar="NAME", help="the video encoder (D26)")
    parser.add_argument(
        "--quality", choices=("high", "standard", "draft"), help="the video quality (D75)"
    )
    parser.add_argument(
        "--ten-bit", action="store_true", help="10-bit video from 8-bit sources (D76)"
    )
    parser.add_argument(
        "--cache-limit-bytes", type=int, metavar="N", help="the proxy-cache limit (D71)"
    )
    parser.add_argument("--method", metavar="ID", help="the correction method (default c3)")
    params = parser.add_mutually_exclusive_group()
    params.add_argument(
        "--parameters",
        type=Path,
        metavar="FILE",
        help="an AD-13 preset JSON file (one with only source and settings added is read too)",
    )
    params.add_argument(
        "--neutral", action="store_true", help="every parameter at its neutral value (V9)"
    )
    parser.add_argument(
        "--settings-dir", type=Path, metavar="DIR", help="load settings.json from this folder"
    )
    parser.add_argument("--record", type=Path, metavar="FILE", help="write the JSON record here")
    return parser


def _settings(args: argparse.Namespace) -> Settings:
    """The run's settings: the loaded or default settings with the given flags overlaid."""
    if args.settings_dir is not None and not args.settings_dir.is_dir():
        raise RunnerRefusalError("the --settings-dir folder does not exist.")
    try:
        base = Settings() if args.settings_dir is None else load_settings(args.settings_dir)
    except (OSError, ValueError, OverflowError) as exc:  # FormatError, an unsupported version,
        # or a stamp that overflows when normalised to UTC (Reviewer B B4)
        raise RunnerRefusalError(
            f"the --settings-dir settings cannot be used: {ascii_text(str(exc))}"
        ) from exc
    if args.out is not None and not args.out.is_dir():
        raise RunnerRefusalError("the --out folder does not exist.")
    changes: dict[str, Any] = {"output_folder": args.out}
    if args.suffix is not None:
        try:
            validate_suffix(args.suffix)
        except ValueError as exc:
            raise RunnerRefusalError(ascii_text(str(exc))) from exc
        changes["output_suffix"] = args.suffix
    if args.bit_depth is not None:
        changes["png_bit_depth"] = args.bit_depth
    if args.no_provenance:
        changes["provenance"] = False
    if args.force_cpu:
        changes["force_cpu"] = True
    if args.encoder is not None:
        changes["video_encoder"] = args.encoder
    if args.quality is not None:
        changes["quality_level"] = args.quality
    if args.ten_bit:
        changes["ten_bit_for_eight_bit"] = True
    if args.cache_limit_bytes is not None:
        if args.cache_limit_bytes < 0:
            raise RunnerRefusalError("--cache-limit-bytes must not be negative.")
        changes["cache_limit_bytes"] = args.cache_limit_bytes
    settings = dataclasses.replace(base, **changes)
    try:  # a suffix loaded from --settings-dir is checked too
        validate_suffix(settings.output_suffix)
    except ValueError as exc:
        raise RunnerRefusalError(ascii_text(str(exc))) from exc
    return settings


def _check_own_paths(args: argparse.Namespace, footage: Path | None) -> None:
    """Refuse a record file that exists, is not ``.json``, has no folder or is in the footage.

    The settings folder, its settings file (the loader may rename a corrupt one, D89) and the
    record file are write targets, each checked with :func:`write_target_refusal`.
    """
    targets: list[tuple[str, Path]] = []
    if args.settings_dir is not None:
        targets += [("--settings-dir", args.settings_dir)]
        targets += [("--settings-dir", args.settings_dir / SETTINGS_FILE_NAME)]
    if args.record is not None:
        targets += [("--record", args.record)]
    for flag, path in targets:
        reason = None if footage is None else write_target_refusal(path, footage)
        if reason is not None:
            raise RunnerRefusalError(f"the {flag} path {reason}.")
    if args.record is not None:
        if args.record.suffix.lower() != ".json":
            raise RunnerRefusalError("the --record file must end in .json.")
        if os.path.lexists(args.record):  # a dangling link counts: it is never written through
            raise RunnerRefusalError("the --record file exists; it is never overwritten.")
        if not args.record.parent.is_dir():
            raise RunnerRefusalError("the folder of the --record file does not exist.")


def main(argv: Sequence[str] | None = None, *, exports: ExportJobs | None = None) -> int:
    """Run the command line.

    Args:
        argv: The arguments; ``sys.argv[1:]`` when None.
        exports: The export engine; ``composition.export_jobs()`` when None (tests only).

    Returns:
        The exit status: 0, 1 or 2 (see the module docstring).
    """
    parser = _parser()
    given = list(sys.argv[1:] if argv is None else argv)
    try:
        args = parser.parse_args(given)
    except _UsageError as exc:  # argparse refused the usage: its text redacted, status 2
        try:
            text = Redactor(_folders_named_in(given))(str(exc))
        except (OSError, RuntimeError):
            text = "a given folder cannot be resolved for redaction."
        print(f"{parser.format_usage()}{parser.prog}: error: {text}", file=sys.stderr)
        return 2
    except SystemExit as exc:  # the help was printed (0)
        return exc.code if isinstance(exc.code, int) else 2
    own = [args.out, args.settings_dir]
    own += [None if args.record is None else args.record.parent]
    own += [None if args.parameters is None else args.parameters.parent]
    known = [Path(p) for p in own if p is not None] + [Path(p).parent for p in args.paths]
    known += [default_config_path().parent]  # a configuration refusal names its file
    try:
        redact = Redactor(known)
    except (OSError, RuntimeError):
        print("headless_export: a given folder cannot be resolved for redaction.", file=sys.stderr)
        return 2
    with _redacted_last_resort(redact):
        try:
            return _main(args, exports, redact, known)
        except RunnerRefusalError as exc:  # a later redactor construction in run / record_object
            print(f"headless_export: {redact(str(exc))}", file=sys.stderr)
            return 2


def _main(
    args: argparse.Namespace, exports: ExportJobs | None, redact: Redactor, known: list[Path]
) -> int:
    """Run the parsed command line with the redactor in place (:func:`main`)."""
    try:
        footage = configured_footage_folder()
        _check_own_paths(args, footage)
        settings = _settings(args)
        if args.parameters is not None:
            parameters = parameters_for(args.method, file=args.parameters)
            source = "file"
        else:
            parameters = parameters_for(args.method, neutral=args.neutral)
            source = "neutral" if args.neutral else "defaults"
        requests = requests_for(args.paths, parameters=parameters, settings=settings)
        check_outputs(requests, footage)
    except RunnerRefusalError as exc:
        print(f"headless_export: {redact(str(exc))}", file=sys.stderr)
        return 2
    progress = RunnerProgress(lambda message: print(redact(message), file=sys.stderr))
    on_main = threading.current_thread() is threading.main_thread()
    previous = signal.signal(signal.SIGINT, lambda *_: progress.cancel()) if on_main else None
    try:  # the handler stays until the record is written: a Ctrl-C then only sets the flag
        record = run(
            requests,
            exports=exports,
            progress=progress,
            footage_folder=footage,
            parameters_from=source,
            known_folders=known,
        )
        for line in summary_lines(record):
            print(line)
        written = args.record is None or _write_record(args.record, record, redact)
    finally:
        if previous is not None:
            signal.signal(signal.SIGINT, previous)
    if not written or progress.cancelled():  # a Ctrl-C while the record was written included
        return 1
    return exit_status(record)


def _write_record(path: Path, record: RunRecord, redact: Redactor) -> bool:
    """Write the record file, never over another; on failure print why (redacted), return False.

    A partial file is removed only when this run created it (absent a concurrent replacement of
    the path by another process).
    """
    created = False
    try:
        with open(path, "x", encoding="ascii", newline="\n") as handle:
            created = True
            handle.write(record_json(record) + "\n")
    except FileExistsError:  # it appeared during the run: never overwritten
        message = "the --record file appeared during the run; it was not written."
        print(f"headless_export: {message}", file=sys.stderr)
        return False
    except OSError as exc:
        if created:
            with contextlib.suppress(OSError):
                Path(path).unlink()
        message = f"the --record file cannot be written: {redact(str(exc))}"
        print(f"headless_export: {message}", file=sys.stderr)
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
