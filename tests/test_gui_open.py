"""WP3.16 file open (G1) and the G10 messages, through the stub engines.

Covers brief task 4 and the task-8 rows "open" and the planted "a refusal shown as a warning".
"""

# The shared fixture ``make_window`` is imported from gui_support and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import importlib
import subprocess
import time
from pathlib import Path

import pytest

import gui_support
from clearwater.gui import messages, sources
from clearwater.gui.engines import stub_probe
from clearwater.interfaces import ColorDescription, Fault
from clearwater.io.photo import PhotoReader, PhotoReadError
from clearwater.io.video import VideoProbeError
from gui_support import (
    UNTAGGED,
    frame,
    image,
    make_window,
    open_and_wait,
    photo_engines,
    presenter_of,
    video_engines,
)

pytestmark = pytest.mark.gui

VIDEO_UNTAGGED = ColorDescription("bt709", "bt709", "bt709", "limited", 8, True, None)


class RaisingPhotoSource:
    def __init__(self, error: BaseException) -> None:
        self.error = error

    def read(self, path: Path):
        raise self.error


def _with_photo_source(engines, source):
    object.__setattr__(engines, "photo_source", source)
    return engines


def assert_refused(window, path: Path, previous) -> str:
    """The file was refused by a modal-class message naming it and the previous source stayed."""
    presenter = presenter_of(window)
    refusals = presenter.of("refusal")
    assert refusals, f"no refusal for {path}: {presenter.messages}"
    assert refusals[-1].text and messages.file_name(path) in refusals[-1].text
    assert window.session.source() is previous
    return refusals[-1].text


def test_open_a_photo(make_window, qtbot) -> None:
    path = Path("reef.jpg")
    window = make_window(photo_engines({path: image(30, 40)}))
    open_and_wait(qtbot, window, path)
    source = window.session.source()
    assert source is not None and source.kind == "photo" and source.path == path
    assert source.metadata is not None and source.probe is None and source.warnings == ()
    assert presenter_of(window).messages == []
    assert window.file_label.text() == "reef.jpg" and window.size_label.text() == "40 x 30"


def test_open_a_video_shows_its_first_frame(make_window, qtbot) -> None:
    frames = [frame(48, 64, ticks=t * 3000, seed=t) for t in range(3)]
    window = make_window(video_engines(frames))
    open_and_wait(qtbot, window, Path("GX010001.MP4"))
    source = window.session.source()
    assert source is not None and source.kind == "video" and source.probe is not None
    assert source.image is frames[0] and window.session.position() == 0
    assert window._timeline.isVisibleTo(window)


def test_file_dialog_route_uses_the_injected_chooser(make_window, qtbot) -> None:
    path = Path("a.png")
    window = make_window(photo_engines({path: image(10, 10)}), choose_file=lambda parent: path)
    window.shell_actions.open.trigger()
    qtbot.waitUntil(lambda: window.session.source() is not None, timeout=5000)
    cancelled = make_window(photo_engines({}), choose_file=lambda parent: None)
    cancelled.shell_actions.open.trigger()
    assert not cancelled.opening() and cancelled.session.source() is None
    filt = sources.file_filter()
    for suffix in ("*.heic", "*.jpg", "*.png", "*.tif", "*.dng", "*.mp4", "*.mov", "All files (*)"):
        assert suffix in filt


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("a.HEIC", "photo"),
        ("a.heif", "photo"),
        ("a.JPG", "photo"),
        ("a.jpeg", "photo"),
        ("a.png", "photo"),
        ("a.tif", "photo"),
        ("a.TIFF", "photo"),
        ("a.dng", "photo"),
        ("a.MP4", "video"),
        ("a.mov", "video"),
        ("a.MOV", "video"),
        ("a.txt", "refusal"),
        ("noextension", "refusal"),
        ("GX010001.LRV", "refusal"),
        ("GX010001.THM", "refusal"),
    ],
)
def test_routing_by_extension(name: str, expected: str) -> None:
    routed = sources.route(Path(name))
    assert (routed if isinstance(routed, str) else routed.severity) == expected


def test_every_g10_source_once(make_window, qtbot) -> None:
    good = Path("good.png")
    window = make_window(photo_engines({good: image(20, 20)}))
    open_and_wait(qtbot, window, good)
    previous = window.session.source()
    presenter = presenter_of(window)

    # Unknown extension and sidecar: refused at routing, nothing read.
    for path, fragment in [
        (Path("notes.txt"), "not a supported photo or video"),
        (Path("GX010001.LRV"), "camera proxy or thumbnail"),
    ]:
        open_and_wait(qtbot, window, path)
        assert fragment in assert_refused(window, path, previous)

    # A DNG: the reader's unsupported refusal (D116), shown with its own text.
    dng = Path("IMG_0001.DNG")
    _with_photo_source(
        window._engines,
        RaisingPhotoSource(PhotoReadError("unsupported", "IMG_0001.DNG is ProRAW/DNG")),
    )
    open_and_wait(qtbot, window, dng)
    assert assert_refused(window, dng, previous) == "IMG_0001.DNG is ProRAW/DNG"

    # The reader's unreadable kind, and any other exception (unreadable with its text).
    bad = Path("broken.heic")
    _with_photo_source(
        window._engines,
        RaisingPhotoSource(PhotoReadError("unreadable", "broken.heic is damaged")),
    )
    open_and_wait(qtbot, window, bad)
    assert assert_refused(window, bad, previous) == "broken.heic is damaged"
    _with_photo_source(window._engines, RaisingPhotoSource(ValueError("bad marker")))
    open_and_wait(qtbot, window, bad)
    assert assert_refused(window, bad, previous) == "broken.heic could not be read: bad marker"
    assert len(presenter.of("warning")) == 0


def test_the_real_readers_photo_read_error_is_refused_naming_the_file(
    make_window, qtbot, tmp_path: Path
) -> None:
    # X-B2: a truncated JPEG through WP3.6's real reader reaches the refusal by name.
    from PIL import Image as PILImage

    whole = tmp_path / "whole.jpg"
    PILImage.new("RGB", (64, 48), (20, 120, 200)).save(whole, quality=90)
    cut = tmp_path / "cut.jpg"
    cut.write_bytes(whole.read_bytes()[: whole.stat().st_size // 2])
    with pytest.raises(PhotoReadError) as raised:
        PhotoReader().read(cut)
    good = Path("good.png")
    window = make_window(photo_engines({good: image(20, 20)}))
    open_and_wait(qtbot, window, good)
    previous = window.session.source()
    _with_photo_source(window._engines, PhotoReader())
    open_and_wait(qtbot, window, cut)
    assert assert_refused(window, cut, previous) == str(raised.value)
    assert presenter_of(window).of("warning") == []


def test_only_a_photo_read_error_by_name_is_shown_with_its_own_text(make_window, qtbot) -> None:
    # X-B2: an exception that merely carries a ``kind`` is not the reader's error.
    class LookAlikeError(Exception):
        kind = "unreadable"

    good, bad = Path("good.png"), Path("broken.heic")
    window = make_window(photo_engines({good: image(20, 20)}))
    open_and_wait(qtbot, window, good)
    previous = window.session.source()
    _with_photo_source(
        window._engines, RaisingPhotoSource(LookAlikeError("broken.heic is damaged"))
    )
    open_and_wait(qtbot, window, bad)
    text = assert_refused(window, bad, previous)
    assert text == "broken.heic could not be read: broken.heic is damaged"


def test_video_probe_errors_and_faults(make_window, qtbot) -> None:
    good = Path("good.png")
    frames = [frame(48, 64, ticks=0)]
    engines = photo_engines({good: image(20, 20)}, frames=frames)
    window = make_window(engines)
    open_and_wait(qtbot, window, good)
    previous = window.session.source()
    clip = Path("clip.mp4")

    for kind in ("unreadable", "unsupported", "sidecar", "missing_tool"):

        def raising(path: Path, kind: str = kind):
            raise VideoProbeError(kind, f"clip.mp4 {kind} text")

        object.__setattr__(window._engines, "video_probe", raising)
        open_and_wait(qtbot, window, clip)
        assert assert_refused(window, clip, previous) == f"clip.mp4 {kind} text"

    for kind, severity in [("hlg", "refuse"), ("pq", "refuse"), ("sidecar", "exclude")]:
        fault = Fault(kind, severity, f"clip.mp4 {kind} refused")  # type: ignore[arg-type]
        object.__setattr__(
            window._engines, "video_probe", lambda path, f=fault: stub_probe(path, faults=(f,))
        )
        open_and_wait(qtbot, window, clip)
        assert assert_refused(window, clip, previous) == f"clip.mp4 {kind} refused"

    object.__setattr__(window._engines, "video_probe", stub_probe)
    object.__setattr__(window._engines.video_source, "_frames", ())
    open_and_wait(qtbot, window, clip)
    assert "no frame could be read" in assert_refused(window, clip, previous)

    # Warnings: the file opens and each warn fault is a banner while it stays open.
    warn = [
        Fault("truncated", "warn", "clip.mp4 is truncated"),
        Fault("unreadable_tail", "warn", "clip.mp4 tail unreadable"),
        Fault("missing_tags", "warn", "clip.mp4 has no colour tags"),
        Fault("gp_log", "warn", "clip.mp4 may be GP-Log"),
    ]
    object.__setattr__(
        window._engines.video_source, "_frames", (frame(48, 64, ticks=0, color=VIDEO_UNTAGGED),)
    )
    object.__setattr__(window._engines, "video_probe", lambda path: stub_probe(path, faults=warn))
    open_and_wait(qtbot, window, clip)
    source = window.session.source()
    assert source is not None and source.path == clip
    texts = [m.text for m in presenter_of(window).of("warning")]
    assert texts == [f.message for f in warn]  # no second untagged warning (missing_tags said it)
    assert source.warnings == tuple(texts)


def test_refusals_whose_text_omits_the_file_name_it(
    make_window, qtbot, monkeypatch, tmp_path: Path
) -> None:
    """Round-1 F4: the real probe's missing-tool and timeout texts carry no file name."""
    probe_module = importlib.import_module("clearwater.io.video.probe")
    good = Path("good.png")
    window = make_window(photo_engines({good: image(20, 20)}, frames=[frame(48, 64, ticks=0)]))
    open_and_wait(qtbot, window, good)
    previous = window.session.source()
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"not a video")
    object.__setattr__(window._engines, "video_probe", probe_module.probe)

    monkeypatch.setattr(probe_module.shutil, "which", lambda name: None)
    open_and_wait(qtbot, window, clip)
    text = assert_refused(window, clip, previous)
    assert text.startswith("clip.mp4: ffprobe was not found on the PATH.")

    def too_slow(*args, **kwargs):
        raise subprocess.TimeoutExpired("ffprobe", 1.0)

    monkeypatch.setattr(probe_module.shutil, "which", lambda name: "ffprobe")
    monkeypatch.setattr(probe_module.subprocess, "run", too_slow)
    open_and_wait(qtbot, window, clip)
    text = assert_refused(window, clip, previous)
    assert text == "clip.mp4: The file took too long to read and was given up on."

    fault = Fault("hlg", "refuse", "HLG video is not supported.")
    object.__setattr__(
        window._engines, "video_probe", lambda path: stub_probe(path, faults=(fault,))
    )
    open_and_wait(qtbot, window, clip)
    assert assert_refused(window, clip, previous) == "clip.mp4: HLG video is not supported."


def test_an_exception_escaping_the_open_task_is_a_refusal_naming_the_file(
    make_window, qtbot, monkeypatch
) -> None:
    # Round-4 R4-1: an open that raises past the per-kind catches still names the file.
    good = Path("good.png")
    window = make_window(photo_engines({good: image(20, 20)}))
    open_and_wait(qtbot, window, good)
    previous = window.session.source()

    def explode(path: Path, engines):
        raise RuntimeError("engine fault")

    monkeypatch.setattr(sources, "open_photo", explode)
    bad = Path("odd.jpg")
    open_and_wait(qtbot, window, bad)
    assert assert_refused(window, bad, previous) == "odd.jpg could not be opened: engine fault"
    assert presenter_of(window).of("warning") == []


class SlowPhotoSource:
    """Serves one photo after a delay (an open still in flight when the next file is chosen)."""

    def __init__(self, path: Path, delay_s: float) -> None:
        self.path = path
        self.delay_s = delay_s

    def read(self, path: Path):
        time.sleep(self.delay_s)
        return image(20, 20, seed=9), gui_support.META


def test_a_routed_refusal_invalidates_the_open_in_flight(make_window, qtbot) -> None:
    # Reviewer B #1: A is still opening when B is refused at routing; A must never be shown.
    good, slow = Path("good.png"), Path("slow.jpg")
    window = make_window(photo_engines({good: image(20, 20)}))
    open_and_wait(qtbot, window, good)
    previous = window.session.source()
    _with_photo_source(window._engines, SlowPhotoSource(slow, 0.4))
    window.open_path(slow)
    qtbot.wait(50)
    refused = Path("notes.txt")
    window.open_path(refused)
    assert "not a supported photo or video" in assert_refused(window, refused, previous)
    qtbot.waitUntil(lambda: not window.opening(), timeout=5000)
    qtbot.wait(600)
    assert window.session.source() is previous


def test_a_refusal_names_the_file_only_when_the_name_stands_alone() -> None:
    # Round-3 R3-4: "a.mp4" inside "data.mp4" does not name a.mp4.
    path = Path("a.mp4")
    assert messages.refusal(path, "data.mp4 is damaged.").text == "a.mp4: data.mp4 is damaged."
    assert messages.refusal(path, "a.mp4 is damaged.").text == "a.mp4 is damaged."
    assert messages.refusal(path, "Cannot read a.mp4.").text == "Cannot read a.mp4."
    assert messages.refusal(path, "x-a.mp4 is damaged.").text == "a.mp4: x-a.mp4 is damaged."


def test_untagged_photo_and_untagged_video_frame_warn_once(make_window, qtbot) -> None:
    photo = Path("flat.png")
    window = make_window(
        photo_engines(
            {photo: image(20, 20, color=UNTAGGED)},
            frames=[frame(48, 64, ticks=0, color=VIDEO_UNTAGGED)],
        )
    )
    open_and_wait(qtbot, window, photo)
    warnings = presenter_of(window).of("warning")
    assert [m.text for m in warnings] == ["flat.png has no colour description; sRGB is assumed."]
    open_and_wait(qtbot, window, Path("clip.mp4"))
    warnings = presenter_of(window).of("warning")
    assert [m.text for m in warnings] == [
        "clip.mp4 has no colour tags; BT.709 limited range is assumed."
    ]


def test_opening_a_new_file_clears_the_previous_files_warnings(make_window, qtbot) -> None:
    flat, good = Path("flat.png"), Path("good.png")
    window = make_window(photo_engines({flat: image(20, 20, color=UNTAGGED), good: image(20, 20)}))
    open_and_wait(qtbot, window, flat)
    assert presenter_of(window).of("warning")
    open_and_wait(qtbot, window, good)
    assert presenter_of(window).of("warning") == []


def test_non_ascii_file_names_are_escaped(make_window, qtbot) -> None:
    path = Path("récif.txt")
    window = make_window()
    open_and_wait(qtbot, window, path)
    text = presenter_of(window).of("refusal")[-1].text
    assert text.isascii() and "r\\xe9cif.txt" in text


def test_planted_refusal_shown_as_a_warning_fails(make_window, qtbot, monkeypatch) -> None:
    good = Path("good.png")
    window = make_window(photo_engines({good: image(20, 20)}))
    open_and_wait(qtbot, window, good)
    previous = window.session.source()
    real = sources.open_photo

    def planted(path: Path, engines):
        outcome = real(path, engines)
        if outcome.source is None:
            msg = outcome.messages[0]
            fake = sources.OpenOutcome(previous, (gui_support.Message("warning", msg.text, path),))
            return fake
        return outcome

    monkeypatch.setattr(sources, "open_photo", planted)
    missing = Path("missing.png")
    open_and_wait(qtbot, window, missing)
    with pytest.raises(AssertionError):
        assert_refused(window, missing, previous)


def test_the_real_dialog_presenter_is_non_blocking(qtbot, tmp_path: Path) -> None:
    from clearwater.gui.shell import MainWindow

    window = MainWindow(photo_engines({}), gui_support.locations(tmp_path))
    qtbot.addWidget(window)
    window.show()
    window.open_path(Path("x.txt"))  # a refusal: a window-modal box, opened without exec
    boxes = window.presenter._boxes  # type: ignore[attr-defined]
    assert len(boxes) == 1 and boxes[0].isVisible() and "x.txt" in boxes[0].text()
    boxes[0].done(0)
    qtbot.waitUntil(lambda: not window.presenter._boxes, timeout=2000)  # type: ignore[attr-defined]
    window.presenter.present(gui_support.Message("warning", "a banner"))
    assert window.banner.texts() == ["a banner"] and window.banner.isVisibleTo(window)
    window.presenter.clear("warning")
    assert window.banner.texts() == []
