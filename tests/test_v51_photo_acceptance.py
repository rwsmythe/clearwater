"""V5 two-reader pose and V11 real-writer failure/crash acceptance through main.

The independent pose oracles follow CHARC's round-0 ruling: oriented source
decode for JPEG, the existing AD-24 landscape recipe for HEIC. A dropped pose,
pending output Orientation, missing ENOSPC handling or leftover partial fails.
"""

from __future__ import annotations

import errno
import os
import re
import shutil
import subprocess
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from types import TracebackType
from typing import Any, BinaryIO, cast

import numpy as np
import pillow_heif
import pytest
from numpy.typing import NDArray
from PIL import Image as PILImage
from PIL import ImageOps

from acceptance_support import (
    RunnerResult,
    assert_names_only,
    assert_output_orientation,
    ffmpeg_png_rgb,
    file_md5,
    only_output,
    pillow_rgb,
    run_main,
    runner_arguments,
    runner_command,
)
from clearwater.app.startup import WriteJournal, clean_leftovers
from clearwater.interfaces import Settings
from clearwater.jobs.naming import is_temporary_name
from spike_io import photo as spike

type Sample = Callable[[str], Path]
type RecordProperty = Callable[[str, object], None]

JPEG_POSES = [f"{scene}-o{pose}" for scene in ("land", "port") for pose in (1, 3, 6, 8)]
HEIC_POSES = ["both", "irot-only", "exif-only", "neither"]


def _assert_jpeg_pose(got: NDArray[Any], expected: NDArray[Any]) -> None:
    assert got.shape == expected.shape, "JPEG upright geometry differs"
    assert float(np.abs(got.astype(np.float64) - expected).max()) <= 2.0, (
        "JPEG neutral oriented-source max exceeds 2/255"
    )


def _assert_ad24_pose(got: NDArray[Any], reference: NDArray[Any]) -> None:
    # The existing test_wp41_photo_path.py AD-24 oracle, including its bound.
    assert got.shape == reference.shape, "HEIC AD-24 upright geometry differs"
    assert float(np.abs(got.astype(np.float64) - reference).mean()) < 6.0, (
        "HEIC AD-24 pose is not upright"
    )
    for pose in range(2, 9):
        other = spike.apply_orientation(reference, pose)
        if other.shape == reference.shape:
            assert float(np.abs(got.astype(np.float64) - other).mean()) > 10.0, (
                "HEIC AD-24 is an incorrect alternative pose"
            )


def _assert_wrong_pose_detected(got: NDArray[Any], stored: NDArray[Any]) -> None:
    assert (
        got.shape != stored.shape
        or float(np.abs(got.astype(np.float64) - stored.astype(np.float64)).max()) > 64.0
    ), "untransposed source is indistinguishable from the output"


def _two_readers(output: Path, scratch: Path) -> NDArray[np.uint8]:
    got = pillow_rgb(output)
    other = ffmpeg_png_rgb(output, scratch, width=got.shape[1], height=got.shape[0])
    np.testing.assert_array_equal(got, other, err_msg="Pillow and FFmpeg PNG readers disagree")
    assert_output_orientation(output)
    return got


@pytest.mark.parametrize("pose", JPEG_POSES)
def test_v5_jpeg_two_readers_and_pose(
    sample: Sample, tmp_path: Path, ffmpeg_tools: None, record_property: RecordProperty, pose: str
) -> None:
    """Catch a wrong exported JPEG pose or a viewer-dependent pending EXIF rotation."""
    source = sample(f"jpeg-orient-{pose}")
    before = file_md5(source)
    try:
        root = tmp_path / "runner"
        result = run_main([source], root, extra=("--force-cpu", "--neutral", "--bit-depth", "8"))
        output = only_output(result, root / "out")
        got = _two_readers(output, tmp_path / "ffmpeg")
        with PILImage.open(source) as image:
            expected = np.array(ImageOps.exif_transpose(image).convert("RGB"), dtype=np.float64)
            stored = np.array(image.convert("RGB"), dtype=np.uint8)
        _assert_jpeg_pose(got, expected)
        width, height = (96, 64) if pose.startswith("land") else (64, 96)
        recipe = spike.upright_image(8, width, height).astype(np.float64)
        record_property("recipe_mean_255", float(np.abs(got - recipe).mean()))
        record_property("neutral_source_max_255", float(np.abs(got - expected).max()))
        if not pose.endswith("o1"):
            _assert_wrong_pose_detected(got, stored)
        # Also exercise the identity cases' oracle with a planted reversed pose.
        with pytest.raises(AssertionError, match="JPEG neutral oriented-source"):
            _assert_jpeg_pose(got[::-1, ::-1], expected)
        record_property("mutation_probe", "reversed output pose rejected")
    finally:
        assert file_md5(source) == before, "JPEG source changed"


@pytest.mark.parametrize("pose", HEIC_POSES)
def test_v5_heic_two_readers_and_ad24(
    sample: Sample, tmp_path: Path, ffmpeg_tools: None, record_property: RecordProperty, pose: str
) -> None:
    """Catch a doubled or omitted HEIC rotation under AD-24 in independent PNG readers."""
    source = sample(f"heic-ad24-{pose}")
    before = file_md5(source)
    try:
        root = tmp_path / "runner"
        result = run_main([source], root, extra=("--force-cpu", "--neutral", "--bit-depth", "8"))
        got = _two_readers(only_output(result, root / "out"), tmp_path / "ffmpeg")
        reference = spike.upright_image(8, 96, 64).astype(np.float64)
        _assert_ad24_pose(got, reference)
        record_property("recipe_mean_255", float(np.abs(got - reference).mean()))
        if pose != "neither":
            # libheif already applies irot. Undo only that known container turn
            # to obtain a stored-pose control; do not transpose its EXIF tag.
            stored = np.asarray(pillow_heif.open_heif(source))
            if pose in ("both", "irot-only"):
                stored = np.rot90(stored, 1)
            _assert_wrong_pose_detected(got, stored)
        with pytest.raises(AssertionError, match="HEIC AD-24 pose"):
            _assert_ad24_pose(got[::-1, ::-1], reference)
        record_property("mutation_probe", "reversed output pose rejected")
    finally:
        assert file_md5(source) == before, "HEIC source changed"


class _DiskFullFile:
    """A real binary file that accepts exactly 1 KiB before raising ENOSPC."""

    def __init__(self, inner: BinaryIO, path: Path) -> None:
        self.inner, self.path = inner, path
        self.written = 0
        self.fired = False

    def __enter__(self) -> _DiskFullFile:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.inner.close()

    def write(self, data: bytes) -> int:
        """Split the crossing write, flush actual bytes, and fail the remainder."""
        remaining = 1024 - self.written
        if len(data) <= remaining:
            count = self.inner.write(data)
            self.written += count
            return count
        if remaining:
            self.written += self.inner.write(data[:remaining])
        self.inner.flush()
        assert self.path.stat().st_size >= 1024, "disk-full probe did not write 1 KiB"
        self.fired = True
        raise OSError(errno.ENOSPC, "No space left on device", self.path.name)


def _assert_disk_full(result: RunnerResult, output: Path, source: Path) -> None:
    assert result.status == 1, "disk-full export did not fail with exit status 1"
    (item,) = result.record["items"]
    assert item["state"] == "failed", "disk-full item did not fail"
    assert item["failure"] and source.name in item["failure"], (
        "disk-full failure did not name its source"
    )
    assert item["outputs"] == [], "disk-full item reported a final output"
    assert list(output.iterdir()) == [], "disk-full export left a final or temporary output"


def test_v11_png_disk_full_removes_partial_output(
    sample: Sample, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, record_property: RecordProperty
) -> None:
    """Catch missing ENOSPC handling/cleanup after the real PNG writer has written bytes."""
    source = sample("png16-gradient-srgb")
    before = file_md5(source)
    output = tmp_path / "runner" / "out"
    opened: list[_DiskFullFile] = []
    real_open = Path.open

    def open_file(path: Path, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        handle = real_open(path, mode, *args, **kwargs)
        if mode == "wb" and path.is_relative_to(output) and is_temporary_name(path.name):
            faulty = _DiskFullFile(cast(BinaryIO, handle), path)
            opened.append(faulty)
            return faulty
        return handle

    try:
        with monkeypatch.context() as patch:
            patch.setattr(Path, "open", open_file)
            result = run_main(
                [source], tmp_path / "runner", extra=("--force-cpu", "--bit-depth", "16")
            )
        assert len(opened) == 1 and opened[0].fired, "ENOSPC injection did not fire"
        assert opened[0].written >= 1024, "ENOSPC preceded 1 KiB of actual writes"
        _assert_disk_full(result, output, source)
        record_property("bytes_written_before_enospc", opened[0].written)
        # A missing injection really succeeds and the failure oracle rejects it.
        control_root = tmp_path / "no-fault"
        control = run_main([source], control_root, extra=("--force-cpu", "--bit-depth", "16"))
        only_output(control, control_root / "out")
        with pytest.raises(AssertionError, match="disk-full export did not fail"):
            _assert_disk_full(control, control_root / "out", source)
        record_property("mutation_probe", "missing ENOSPC rejected")
    finally:
        assert file_md5(source) == before, "disk-full export changed its source"


def _assert_no_new_outputs(output: Path, before: Mapping[str, str]) -> None:
    assert {path.name: file_md5(path) for path in output.iterdir()} == before, (
        "crash cleanup left a new output or changed an existing output"
    )


def _assert_complete_finals(
    output: Path, sentinels: Mapping[str, str], expected_size: tuple[int, int]
) -> dict[str, str]:
    """Verify and fully decode every final, then retain its byte identity."""
    finals: dict[str, str] = {}
    for path in output.iterdir():
        if path.name in sentinels or is_temporary_name(path.name):
            continue
        try:
            with PILImage.open(path) as image:
                image.verify()
            with PILImage.open(path) as image:
                image.load()
                assert image.size == expected_size, "crash final has unexpected dimensions"
        except (OSError, ValueError) as exc:
            raise AssertionError(f"crash left a partial final: {path.name}") from exc
        finals[path.name] = file_md5(path)
    return finals


def _assert_crash_before_cleanup(
    output: Path, sentinels: Mapping[str, str], expected_size: tuple[int, int], in_flight: Path
) -> dict[str, str]:
    """Require complete finals, with shared identity when an in-flight temporary survives."""
    finals = _assert_complete_finals(output, sentinels, expected_size)
    if in_flight.exists():
        temporaries = [
            path
            for path in output.iterdir()
            if is_temporary_name(path.name)
            and path.name.startswith(f"{in_flight.stem}.clearwater-partial-")
        ]
        if temporaries:
            assert any(
                os.path.samefile(path, in_flight) and file_md5(path) == finals[in_flight.name]
                for path in temporaries
            ), "in-flight final is not the same file as a surviving temporary"
    return finals


def test_d85_same_file_cleanup_preserves_installed_final(
    sample: Sample, tmp_path: Path, record_property: RecordProperty
) -> None:
    """Witness D85 deterministically: cleanup removes a temporary hard link, keeping its final."""
    source = sample("png16-gradient-srgb")
    source_before = file_md5(source)
    output = tmp_path / "out"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_bytes(b"keep the sentinel")
    sentinels = {sentinel.name: file_md5(sentinel)}
    temporary = output / "inflight_corrected.clearwater-partial-0123456789ab.png"
    final = output / "inflight_corrected.png"
    earlier = output / "earlier_corrected.png"
    try:
        shutil.copyfile(source, temporary)
        shutil.copyfile(source, earlier)
        # Equal bytes are insufficient: a distinct file must fail the same oracle.
        shutil.copyfile(temporary, final)
        assert file_md5(temporary) == file_md5(final)
        assert not os.path.samefile(temporary, final)
        with pytest.raises(AssertionError, match="in-flight final is not the same file"):
            _assert_crash_before_cleanup(output, sentinels, (96, 64), final)
        final.unlink()
        record_property("mutation_probe", "byte-identical unrelated final rejected")

        os.link(temporary, final)
        assert os.path.samefile(temporary, final)
        assert file_md5(temporary) == file_md5(final)
        before = _assert_crash_before_cleanup(output, sentinels, (96, 64), final)
        report = clean_leftovers(
            Settings(output_folder=output, force_cpu=True), WriteJournal(tmp_path / "journal")
        )
        assert report.failed == () and report.removed == (temporary,)
        assert not temporary.exists(), "temporary NAME survived cleanup"
        assert final.is_file(), "startup removed the installed final"
        assert file_md5(final) == before[final.name], "startup altered the installed final"
        assert _assert_complete_finals(output, sentinels, (96, 64)) == before
        _assert_no_new_outputs(output, {**sentinels, **before})
        record_property("d85_same_file_cleanup", "temporary name removed; both finals preserved")
    finally:
        assert file_md5(source) == source_before, "D85 probe changed its source"


@pytest.mark.slow(reason="runs the headless runner as a subprocess")
def test_v11_photo_crash_leftovers_are_cleaned_at_start(
    sample: Sample,
    sample_entry: Callable[[str], dict[str, Any]],
    tmp_path: Path,
    fixture_manifest: dict[str, Any],
    record_property: RecordProperty,
) -> None:
    """Preserve complete batch items and installed finals while cleaning crash temporaries."""
    source = sample("png16-gradient-srgb")
    facts = sample_entry("png16-gradient-srgb")["facts"]
    expected_size = (facts["width"], facts["height"])
    # No owner photo is read: this is a maximum-area committed-fixture tie.
    assert facts["width"] * facts["height"] == max(
        entry["facts"].get("width", 0) * entry["facts"].get("height", 0)
        for entry in fixture_manifest["samples"]
        if entry["group"] == "stills"
    )
    copies = tmp_path / "sources"
    copies.mkdir()
    sources = [copies / f"photo-{index:02d}.png" for index in range(40)]
    for copy in sources:
        shutil.copyfile(source, copy)
    hashes = {path: file_md5(path) for path in [source, *sources]}
    try:
        for attempt in range(1, 21):
            root = tmp_path / f"attempt-{attempt:02d}"
            args = runner_arguments(sources, root, extra=("--force-cpu", "--bit-depth", "16"))
            output = root / "out"
            sentinel = output / "keep.txt"
            sentinel.write_bytes(b"existing output must survive")
            sentinels = {sentinel.name: file_md5(sentinel)}
            observed: list[str] = []
            with (
                (root / "stdout.log").open("wb") as stdout,
                (root / "stderr.log").open("wb") as stderr,
            ):
                process = subprocess.Popen(runner_command(args), stdout=stdout, stderr=stderr)
                try:
                    deadline = time.monotonic() + 30.0
                    while process.poll() is None and time.monotonic() < deadline:
                        observed = [p.name for p in output.iterdir() if is_temporary_name(p.name)]
                        if observed:
                            process.kill()
                            break
                        time.sleep(0.01)
                    process.wait(timeout=10)
                finally:
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=10)
            finals = _assert_complete_finals(output, sentinels, expected_size)
            record_property(f"attempt_{attempt:02d}_completed_finals", len(finals))
            leftovers = {p for p in output.iterdir() if is_temporary_name(p.name)}
            record_property(
                f"attempt_{attempt:02d}_surviving_temporaries",
                ",".join(sorted(path.name for path in leftovers)),
            )
            assert file_md5(sentinel) == sentinels[sentinel.name], "export altered the sentinel"
            if not observed:
                assert process.returncode == 0, "runner crashed before a temporary was observed"
            stderr_text = (root / "stderr.log").read_text(encoding="utf-8")
            writing = re.findall(r"^\[(\d+)/40\] Writing (photo-\d{2}\.png)$", stderr_text, re.M)
            assert writing, "runner stderr did not identify an in-flight Writing item"
            item_number, source_name = writing[-1]
            assert sources[int(item_number) - 1].name == source_name
            in_flight_stem = Path(source_name).stem
            record_property(f"attempt_{attempt:02d}_in_flight_source", source_name)
            record_property(f"attempt_{attempt:02d}_observed_temporaries", ",".join(observed))
            in_flight_final = output / f"{in_flight_stem}_corrected.png"
            installed_final = in_flight_final.exists()
            matching_temporaries = [
                path
                for path in leftovers
                if path.name.startswith(f"{in_flight_stem}_corrected.clearwater-partial-")
            ]
            record_property(
                f"attempt_{attempt:02d}_state",
                "no final"
                if not installed_final
                else ("same-file final" if matching_temporaries else "complete with no temporary"),
            )
            assert (
                _assert_crash_before_cleanup(output, sentinels, expected_size, in_flight_final)
                == finals
            )
            assert_names_only(
                [observed, list(finals), stderr_text, (root / "stdout.log").read_text("utf-8")],
                folders=[root, copies, output],
            )
            # A poll may see a temporary whose commit finishes before kill.
            # Record that end state, but never claim cleanup on a clean folder.
            if not observed or not leftovers:
                continue
            record_property("crash_attempt", attempt)
            record_property("in_flight_source", source_name)

            # Keep the real crash state intact for startup cleanup. These
            # independent files exercise the SAME oracle in a scratch folder.
            probes = root / "oracle-probes"
            probes.mkdir()
            probe_temporary = probes / observed[0]
            shutil.copyfile(source, probe_temporary)
            probe_final = probes / in_flight_final.name
            assert _assert_crash_before_cleanup(probes, {}, expected_size, probe_final) == {}
            partial_final = probes / "planted-truncated.png"
            partial_final.write_bytes(source.read_bytes()[:32])
            try:
                with pytest.raises(AssertionError, match="crash left a partial final"):
                    _assert_crash_before_cleanup(probes, {}, expected_size, probe_final)
            finally:
                partial_final.unlink()
            record_property("mutation_probe_partial_final", "truncated final rejected")
            probe_temporary.unlink()

            report = clean_leftovers(
                Settings(output_folder=output, force_cpu=True), WriteJournal(root / "journal")
            )
            assert report.failed == (), "startup could not remove a crash temporary"
            assert set(report.removed) == leftovers, "startup did not remove the real leftovers"
            assert all(not path.exists() for path in leftovers), "temporary NAME survived cleanup"
            if installed_final:
                assert in_flight_final.is_file(), "startup removed the installed in-flight final"
                assert file_md5(in_flight_final) == finals[in_flight_final.name], (
                    "startup altered the installed in-flight final"
                )
            assert _assert_complete_finals(output, sentinels, expected_size) == finals
            before = {**sentinels, **finals}
            _assert_no_new_outputs(output, before)
            # Plant the omission of cleanup and show the same final-state oracle fails.
            planted = output / observed[0]
            planted.write_bytes(b"partial")
            try:
                with pytest.raises(AssertionError, match="crash cleanup left a new output"):
                    _assert_no_new_outputs(output, before)
            finally:
                planted.unlink()
            record_property("mutation_probe", "planted leftover rejected")
            assert_names_only(
                [observed, list(before), stderr_text, (root / "stdout.log").read_text("utf-8")],
                folders=[root, copies, output],
            )
            return
        record_property("crash_observation", "not observable at this size")
        pytest.skip("not observable at this size")
    finally:
        assert all(file_md5(path) == digest for path, digest in hashes.items()), (
            "photo crash changed a source"
        )
