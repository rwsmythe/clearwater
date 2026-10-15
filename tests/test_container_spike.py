from __future__ import annotations

import shutil
import struct
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from container_spike import compare, spike
from container_spike.compare import (
    BEST_EFFORT,
    DIFFERENT,
    MANDATORY,
    REQUIRED,
    SAME,
    Edit,
    Movie,
    OutputPathError,
    Track,
)
from local_config import load_local_config

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe not on PATH",
)


def _ffmpeg(folders: tuple[Path, Path], output: Path, *arguments: str) -> None:
    """Run FFmpeg writing ``output``, after the spike's own check on the output path."""
    spike_root, footage = folders
    compare.check_output_path(output, spike_root, footage)
    subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-y", *arguments, str(output)],
        check=True,
        stdin=subprocess.DEVNULL,
        capture_output=True,
    )


def _synthetic(
    folders: tuple[Path, Path],
    path: Path,
    offset: str = "0.5",
    video_filter: str | None = None,
    rotation: str | None = None,
) -> Path:
    """2 s testsrc2 + sine, 30 fps, yuv420p H.264 + AAC, start offset ``offset`` seconds.

    The colour tags are set (BT.709, limited range, the D54 assumption): an untagged
    source re-encoded by libx265 gains a ``tv`` range tag, which the spike records
    separately.
    """
    filters = ["-vf", video_filter, "-fps_mode", "passthrough"] if video_filter else []
    _ffmpeg(
        folders,
        path,
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=320x240:rate=30:duration=2",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:sample_rate=48000:duration=2",
        *filters,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-colorspace",
        "bt709",
        "-color_range",
        "tv",
        "-c:a",
        "aac",
        "-output_ts_offset",
        offset,
    )
    if rotation is not None:
        rotated = path.with_name(f"{path.stem}-rot{path.suffix}")
        _ffmpeg(folders, rotated, "-display_rotation", rotation, "-i", str(path), "-c", "copy")
        return rotated
    return path


def _items(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["name"]: item for item in record["items"]}


def _different(record: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in record["items"] if item["status"] == DIFFERENT]


@pytest.fixture(scope="module")
def folders(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """A test spike folder (``work/wp1.5``) and an empty test footage folder."""
    root = tmp_path_factory.mktemp("folders")
    footage, spike_root = root / "footage", root / "work" / "wp1.5"
    footage.mkdir()
    spike_root.mkdir(parents=True)
    return spike_root, footage


@pytest.fixture(scope="module")
def clips(folders: tuple[Path, Path]) -> dict[str, Path]:
    """The synthetic sources, written under the test spike folder like every other output."""
    root = folders[0] / "clips"
    root.mkdir()
    return {
        "base": _synthetic(folders, root / "base.mp4"),
        "shifted": _synthetic(folders, root / "shifted.mp4", offset="0.25"),
        # Frames 10-14 dropped with their timestamps kept: a variable-frame-rate gap.
        "vfr": _synthetic(folders, root / "vfr.mp4", video_filter="select='not(between(n,10,14))'"),
        "rotated": _synthetic(folders, root / "rot.mp4", rotation="90"),
    }


@pytest.fixture(scope="module")
def reencoded(clips: dict[str, Path], folders: tuple[Path, Path]) -> dict[str, dict[str, Any]]:
    spike_root, footage = folders
    runs = {}
    for name in ("base", "vfr", "rotated"):
        run = spike.reencode(clips[name], spike_root / name, "libx265", spike_root, footage)
        runs[name] = compare.compare_files(clips[name], Path(run["output"])) | {"run": run}
    return runs


class TestSelfComparison:
    def test_clip_against_itself_is_all_same(self, clips: dict[str, Path]) -> None:
        record = compare.compare_files(clips["base"], clips["base"])
        assert _different(record) == []
        assert record["summary"]["mandatory_all_same"] is True

    def test_synthetic_has_the_start_offset_and_an_edit_list(self, clips: dict[str, Path]) -> None:
        items = _items(compare.compare_files(clips["base"], clips["base"]))
        assert items["start offset: first video frame pts"]["source"].startswith("0.500000")
        edits = items["edit lists as written (all tracks; media_time in media seconds)"]["source"]
        assert edits["vide#0"][0]["media_time"] == "empty"  # the 0.5 s dwell


class TestReencodedSynthetic:
    def test_mandatory_items_same_and_differences_best_effort(
        self, reencoded: dict[str, dict[str, Any]]
    ) -> None:
        record = reencoded["base"]
        items = _items(record)
        for name in (
            "video frame count",
            "video stream duration",
            "audio streams present",
            "video per-frame pts (presentation, exact, full sequence)",
            "audio sync: first audio pts minus first video pts",
        ):
            assert items[name]["status"] == SAME, name
        assert items["video frame count"]["source"] == 60
        assert items["audio streams present"]["source"]  # an audio stream is there
        assert {item["class"] for item in _different(record)} <= {BEST_EFFORT}
        assert record["info"]["output"]["codec"] == "hevc"

    def test_variable_frame_rate_gap_is_kept(self, reencoded: dict[str, dict[str, Any]]) -> None:
        item = _items(reencoded["vfr"])["video per-frame pts (presentation, exact, full sequence)"]
        assert item["status"] == SAME
        assert item["source"]["count"] == 55
        assert len(item["source"]["steps"]) == 2  # the regular step and the gap
        assert {i["class"] for i in _different(reencoded["vfr"])} <= {BEST_EFFORT}

    def test_display_rotation_is_kept(self, reencoded: dict[str, dict[str, Any]]) -> None:
        items = _items(reencoded["rotated"])
        side = items["display orientation: display matrix (ffprobe side data)"]
        assert side["source"]["rotation"] in (90, -90)
        assert side["status"] == SAME
        assert items["display orientation: video tkhd matrix"]["status"] == SAME
        assert items["frame size and sample aspect ratio"]["status"] == SAME

    def test_run_record_and_outputs_stay_in_the_spike_folder(
        self, reencoded: dict[str, dict[str, Any]], folders: tuple[Path, Path]
    ) -> None:
        spike_root, footage = folders
        run = reencoded["base"]["run"]
        assert Path(run["output"]).name == "base_corrected.mp4"
        for key in ("output", "compare_json", "compare_md", "run_json"):
            assert Path(run[key]).resolve().is_relative_to(spike_root.resolve())
        assert list(footage.iterdir()) == []
        assert float(run["psnr"]["y"]) > 35


class TestMandatoryDifferences:
    def test_changed_start_offset_is_different_and_mandatory(self, clips: dict[str, Path]) -> None:
        record = compare.compare_files(clips["base"], clips["shifted"])
        items = _items(record)
        for name in (
            "start offset: first video frame pts",
            "start offset: video and audio stream start_pts",
            "start offset: container start (earliest stream start, exact)",
        ):
            assert items[name]["status"] == DIFFERENT, name
            assert items[name]["class"] == MANDATORY
        assert record["summary"]["mandatory_all_same"] is False

    def test_dropped_frames_make_pts_different_and_mandatory(self, clips: dict[str, Path]) -> None:
        items = _items(compare.compare_files(clips["base"], clips["vfr"]))
        pts = items["video per-frame pts (presentation, exact, full sequence)"]
        assert (pts["status"], pts["class"]) == (DIFFERENT, MANDATORY)
        assert "index 10" in pts["note"]


class TestEditEffect:
    def _track(self, edits: tuple[Edit, ...] | None, earliest: int) -> Track:
        return Track(
            track_id=1,
            flags=3,
            handler="vide",
            handler_name="",
            sample_entry="hvc1",
            sample_entry_boxes=(),
            media_timescale=30000,
            media_duration=60060,
            matrix=(65536, 0, 0, 0, 65536, 0, 0, 0, 1 << 30),
            edits=edits,
            earliest_composition=earliest,
        )

    def _movie(self) -> Movie:
        return Movie((), "isom", (), 1000, 0, (), ())

    def test_reorder_shift_reads_as_starting_at_zero(self) -> None:
        shifted = self._track((Edit(2002, 3003, Fraction(1)),), earliest=3003)
        plain = self._track((Edit(2002, 0, Fraction(1)),), earliest=0)
        assert compare.edit_effect(self._movie(), shifted) == compare.edit_effect(
            self._movie(), plain
        )

    def test_head_trim_is_kept(self) -> None:
        trimmed = self._track((Edit(2002, 3003 + 1001, Fraction(1)),), earliest=3003)
        effect = compare.edit_effect(self._movie(), trimmed)
        assert effect[0]["media_start"] == compare.exact(Fraction(1001, 30000))

    def test_absent_edit_list_is_the_implicit_identity(self) -> None:
        effect = compare.edit_effect(self._movie(), self._track(None, earliest=0))
        assert effect == [
            {
                "duration": compare.exact(Fraction(60060, 30000)),
                "media_start": compare.exact(Fraction(0)),
                "rate": "1",
            }
        ]

    def test_empty_edit_keeps_its_dwell(self) -> None:
        track = self._track((Edit(500, -1, Fraction(1)), Edit(2002, 0, Fraction(1))), 0)
        effect = compare.edit_effect(self._movie(), track)
        assert effect[0]["media_start"] == "empty"
        assert effect[0]["duration"] == compare.exact(Fraction(1, 2))


class TestOutputPathCheck:
    def test_inside_the_spike_folder_passes(self, tmp_path: Path) -> None:
        allowed, footage = tmp_path / "work" / "wp1.5", tmp_path / "footage"
        target = allowed / "reencode" / "x.mp4"
        assert compare.check_output_path(target, allowed, footage) == target.resolve()

    def test_outside_the_spike_folder_is_refused(self, tmp_path: Path) -> None:
        allowed, footage = tmp_path / "work" / "wp1.5", tmp_path / "footage"
        with pytest.raises(OutputPathError, match="outside the spike folder"):
            compare.check_output_path(tmp_path / "work" / "other.mp4", allowed, footage)

    def test_inside_the_footage_folder_is_refused(self, tmp_path: Path) -> None:
        footage = tmp_path / "footage"
        # Even when the spike folder is (mis)configured inside the footage folder.
        with pytest.raises(OutputPathError, match="inside the footage folder"):
            compare.check_output_path(footage / "wp1.5" / "x.mp4", footage / "wp1.5", footage)

    def test_link_into_the_footage_folder_is_refused(self, tmp_path: Path) -> None:
        footage, allowed = tmp_path / "footage", tmp_path / "work" / "wp1.5"
        footage.mkdir()
        allowed.mkdir(parents=True)
        link = allowed / "link"
        try:
            link.symlink_to(footage, target_is_directory=True)
        except OSError:
            pytest.skip("cannot create a directory link here")
        with pytest.raises(OutputPathError, match="inside the footage folder"):
            compare.check_output_path(link / "x.mp4", allowed, footage)

    def test_reencode_refuses_before_running_ffmpeg(
        self, clips: dict[str, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def no_run(*_: object, **__: object) -> tuple[int, str]:
            raise AssertionError("ffmpeg must not run")

        monkeypatch.setattr(spike, "run_tool", no_run)
        with pytest.raises(OutputPathError):
            spike.reencode(
                clips["base"], tmp_path / "elsewhere", "libx265", tmp_path / "w", tmp_path
            )

    def test_compare_cli_refuses_an_out_folder_outside_the_spike_folder(
        self, clips: dict[str, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        config = tmp_path / "local.toml"
        config.write_text(
            f"footage_path = '{tmp_path / 'footage'}'\nworking_path = '{tmp_path / 'work'}'\n",
            encoding="utf-8",
        )
        code = compare.main(
            [
                str(clips["base"]),
                str(clips["base"]),
                "--config",
                str(config),
                "--out",
                str(tmp_path),
            ]
        )
        assert code == 2
        assert "outside the spike folder" in capsys.readouterr().err

    def test_compare_cli_writes_json_and_table(
        self, clips: dict[str, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        config = tmp_path / "local.toml"
        config.write_text(
            f"footage_path = '{tmp_path / 'footage'}'\nworking_path = '{tmp_path / 'work'}'\n",
            encoding="utf-8",
        )
        assert compare.main([str(clips["base"]), str(clips["base"]), "--config", str(config)]) == 0
        written = sorted(p.name for p in (tmp_path / "work" / "wp1.5").iterdir())
        assert written == ["base.compare.json", "base.compare.md"]
        table = (tmp_path / "work" / "wp1.5" / "base.compare.md").read_text(encoding="utf-8")
        assert "| video per-frame pts (presentation, exact, full sequence) | MANDATORY |" in table
        assert "every MANDATORY item SAME: True" in capsys.readouterr().out

    def test_a_record_file_linked_into_the_footage_folder_is_refused(
        self, clips: dict[str, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        footage, spike_root = tmp_path / "footage", tmp_path / "work" / "wp1.5"
        footage.mkdir()
        spike_root.mkdir(parents=True)
        config = tmp_path / "local.toml"
        config.write_text(
            f"footage_path = '{footage}'\nworking_path = '{tmp_path / 'work'}'\n", encoding="utf-8"
        )
        try:
            (spike_root / "base.compare.json").symlink_to(footage / "planted.json")
        except OSError:
            pytest.skip("cannot create a file link here")
        assert compare.main([str(clips["base"]), str(clips["base"]), "--config", str(config)]) == 2
        assert "inside the footage folder" in capsys.readouterr().err
        assert list(footage.iterdir()) == []

    def test_reencode_refuses_a_run_record_linked_into_the_footage_folder(
        self, clips: dict[str, Path], tmp_path: Path
    ) -> None:
        footage, spike_root = tmp_path / "footage", tmp_path / "work" / "wp1.5"
        footage.mkdir()
        (spike_root / "r").mkdir(parents=True)
        try:
            (spike_root / "r" / "base_corrected.run.json").symlink_to(footage / "planted.json")
        except OSError:
            pytest.skip("cannot create a file link here")
        with pytest.raises(OutputPathError, match="inside the footage folder"):
            spike.reencode(clips["base"], spike_root / "r", "libx265", spike_root, footage)
        assert list(footage.iterdir()) == []


class TestCapabilityListing:
    ENCODERS = """Encoders:
 V..... = Video
 ------
 V....D libx265              libx265 H.265 / HEVC (codec hevc)
 V....D av1_nvenc            NVIDIA NVENC av1 encoder (codec av1)
"""
    DECODERS = """Decoders:
 ------
 VFS..D hevc                 HEVC (High Efficiency Video Coding)
 V..... hevc_cuvid           Nvidia CUVID HEVC decoder (codec hevc)
"""
    HWACCELS = "Hardware acceleration methods:\ncuda\nd3d11va\n\n"

    def test_documented_keys_and_absent_entries(self, monkeypatch: pytest.MonkeyPatch) -> None:
        listings = {"-encoders": self.ENCODERS, "-decoders": self.DECODERS}
        monkeypatch.setattr(
            spike, "_ffmpeg_output", lambda args: listings.get(args[0], self.HWACCELS)
        )
        record = spike.capability_listing()
        assert set(record) == {"encoders", "decoders", "hwaccels"}
        assert set(record["encoders"]) == set(spike.LISTED_ENCODERS)
        assert set(record["decoders"]) == set(spike.LISTED_DECODERS)
        assert set(record["hwaccels"]) == set(spike.LISTED_HWACCELS)
        assert record["encoders"]["hevc_nvenc"] is False
        assert record["encoders"]["libx265"] is True
        assert record["decoders"]["hevc_cuvid"] is True
        assert record["decoders"]["av1_cuvid"] is False
        assert record["hwaccels"] == {
            "cuda": True,
            "d3d11va": True,
            "dxva2": False,
            "d3d12va": False,
            "vulkan": False,
        }

    def test_legend_lines_are_not_codecs(self) -> None:
        assert spike._codec_names(self.ENCODERS) == {"libx265", "av1_nvenc"}


class TestEncodeProofs:
    @staticmethod
    def _prove(tmp_path: Path, encoder: str, pix_fmt: str, profile: str) -> dict[str, Any]:
        allowed, footage = tmp_path / "work" / "wp1.5", tmp_path / "footage"
        # The proof folder does not exist yet: the proof creates it.
        return spike.encode_proof(
            encoder, pix_fmt, profile, allowed / "capability", allowed, footage
        )

    @staticmethod
    def _fake_nvenc_run(monkeypatch: pytest.MonkeyPatch, gpu_rows: list[list[str]] | None) -> None:
        """An NVENC encode and ffprobe reading that succeed, with the given nvidia-smi rows."""
        monkeypatch.setattr(spike, "run_tool", lambda *_, **__: (0, ""))
        stream = {"codec_name": "hevc", "profile": "Main 10", "pix_fmt": "yuv420p10le"}
        monkeypatch.setattr(
            spike, "run_ffprobe", lambda _: {"streams": [{**stream, "nb_frames": "60"}]}
        )

        def query() -> list[list[str]]:
            if gpu_rows is None:
                raise spike.SpikeError("nvidia-smi exited with status 9")
            return gpu_rows

        monkeypatch.setattr(spike, "_gpu_query", query)

    def test_nvenc_proof_needs_nvidia_smi(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._fake_nvenc_run(monkeypatch, None)
        proof = self._prove(tmp_path, "hevc_nvenc", "p010le", "main10")
        assert proof["gpu"]["available"] is False
        assert proof["gpu"]["error"] == "nvidia-smi exited with status 9"
        assert proof["proven"] is False

    def test_nvenc_proof_needs_a_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._fake_nvenc_run(monkeypatch, [["NVIDIA GeForce", "0", "0", "0"]])
        assert self._prove(tmp_path, "hevc_nvenc", "p010le", "main10")["proven"] is False

    def test_nvenc_proof_holds_with_a_named_gpu_and_a_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._fake_nvenc_run(monkeypatch, [["NVIDIA GeForce", "35", "0", "1"]])
        proof = self._prove(tmp_path, "hevc_nvenc", "p010le", "main10")
        assert proof["gpu"]["names"] == ["NVIDIA GeForce"]
        assert proof["proven"] is True

    def test_software_ten_bit_proof_holds(self, tmp_path: Path) -> None:
        proof = self._prove(tmp_path, "libx265", "yuv420p10le", "main10")
        assert proof["exit_status"] == 0
        assert proof["ffprobe"]["pix_fmt"] == "yuv420p10le"
        assert proof["ffprobe"]["profile"] == "Main 10"
        assert proof["proven"] is True

    def test_proof_fails_when_the_reading_does_not_match(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real = spike.run_ffprobe

        def eight_bit(arguments: list[str]) -> dict[str, Any]:
            data = real(arguments)
            data["streams"][0]["pix_fmt"] = "yuv420p"
            return data

        monkeypatch.setattr(spike, "run_ffprobe", eight_bit)
        assert self._prove(tmp_path, "libx265", "yuv420p10le", "main10")["proven"] is False

    @pytest.mark.gpu
    @pytest.mark.parametrize(("pix_fmt", "profile"), [("p010le", "main10"), ("yuv420p", "main")])
    def test_nvenc_proofs_hold(self, tmp_path: Path, pix_fmt: str, profile: str) -> None:
        proof = self._prove(tmp_path, "hevc_nvenc", pix_fmt, profile)
        assert proof["proven"] is True, proof.get("stderr_tail")
        assert proof["gpu"]["available"] is True


class TestReencodeCommand:
    def _probe(self, pix_fmt: str, **colour: str) -> dict[str, Any]:
        video = {"index": 0, "codec_type": "video", "pix_fmt": pix_fmt, **colour}
        return {
            "streams": [
                video,
                {"index": 1, "codec_type": "audio"},
                {"index": 2, "codec_type": "data", "codec_tag_string": "tmcd"},
                {"index": 3, "codec_type": "data", "codec_tag_string": "gpmd"},
            ]
        }

    def test_maps_audio_and_gpmf_but_not_tmcd(self) -> None:
        command = spike.reencode_command(
            Path("in.MP4"), Path("out.MP4"), self._probe("yuvj420p"), "hevc_nvenc"
        )
        maps = [command[i + 1] for i, arg in enumerate(command) if arg == "-map"]
        assert maps == ["0:0", "0:1", "0:3"]
        assert command[command.index("-pix_fmt") + 1] == "yuv420p"
        assert command[command.index("-profile:v") + 1] == "main"
        assert command[:4] == ["ffmpeg", "-nostdin", "-hide_banner", "-y"]
        assert command[-1] == "out.MP4"

    def test_ten_bit_source_gets_a_ten_bit_encode(self) -> None:
        command = spike.reencode_command(
            Path("in.MP4"), Path("o.MP4"), self._probe("yuv420p10le"), "hevc_nvenc"
        )
        assert command[command.index("-pix_fmt") + 1] == "p010le"
        assert command[command.index("-profile:v") + 1] == "main10"

    def test_colour_tags_copied_only_when_known(self) -> None:
        probe = self._probe(
            "yuvj420p", color_range="pc", color_primaries="bt709", color_transfer="unknown"
        )
        command = spike.reencode_command(Path("i.MP4"), Path("o.MP4"), probe, "libx265")
        assert command[command.index("-color_range") + 1] == "pc"
        assert command[command.index("-color_primaries") + 1] == "bt709"
        assert "-color_trc" not in command
        assert "-colorspace" not in command

    def test_four_two_two_is_outside_the_spike(self) -> None:
        with pytest.raises(spike.SpikeError, match="outside the spike"):
            spike.reencode_command(
                Path("i.MP4"), Path("o.MP4"), self._probe("yuv422p10le"), "hevc_nvenc"
            )


class TestCompositionOffsets:
    def test_ctts_offsets_read_signed_as_ffmpeg_reads_them(self) -> None:
        # A version-0 ctts whose first offset is 0xFFFFFC17. ISO/IEC 14496-12 reads a
        # version-0 offset unsigned (4294966295); FFmpeg's demuxer, which produces the pts
        # the comparison checks, reads it signed (-1001) in both versions, and so does the
        # walker, keeping the edit-list effect on the demuxer's timeline (deliberate).
        payload = struct.pack(">I I II II", 0, 2, 1, (-1001) & 0xFFFFFFFF, 2, 0)
        assert compare._runs(payload, (0, len(payload)), signed=True) == [(1, -1001), (2, 0)]

    def test_earliest_composition_includes_negative_offsets(self) -> None:
        assert compare._earliest_composition([(3, 1001)], [(1, -1001), (2, 0)]) == -1001
        assert compare._earliest_composition([(3, 1001)], []) == 0
        assert compare._earliest_composition([], []) is None


class TestSmallParsers:
    @pytest.mark.parametrize(
        ("pix_fmt", "expected"),
        [
            ("yuvj420p", ("4:2:0", 8)),
            ("yuv420p", ("4:2:0", 8)),
            ("yuv420p10le", ("4:2:0", 10)),
            ("yuv422p10le", ("4:2:2", 10)),
            ("p010le", ("4:2:0", 10)),
            ("nv12", ("4:2:0", 8)),
            ("rgb24", (None, None)),
            (None, (None, None)),
        ],
    )
    def test_pix_fmt_shape(self, pix_fmt: str | None, expected: tuple[Any, Any]) -> None:
        assert compare.pix_fmt_shape(pix_fmt) == expected

    @staticmethod
    def _klv(key: bytes, kind: bytes, value: bytes) -> bytes:
        padded = value + b"\0" * (-len(value) % 4)
        size, repeat = (1, len(value)) if kind == b"c" else (len(value), 1)
        return key + kind + struct.pack(">BH", size, repeat) + padded

    def test_gpmf_settings_reads_only_the_named_keys(self) -> None:
        inner = (
            self._klv(b"CASN", b"c", b"C1234567890")
            + self._klv(b"MINF", b"c", b"HERO13 Black\0\0")
            + self._klv(b"PTCL", b"c", b"NATURAL\0")
            + self._klv(b"HDRV", b"c", b"N")
        )
        payload = b"DEVC" + b"\0" + struct.pack(">BH", 1, len(inner)) + inner
        settings = spike.gpmf_settings(payload)
        assert settings == {"MINF": "HERO13 Black", "PTCL": "NATURAL", "HDRV": "N"}

    def test_output_name_follows_spec_8_3(self) -> None:
        assert spike.output_name(Path("GX011627.MP4")) == "GX011627_corrected.MP4"


@pytest.mark.footage
@pytest.mark.slow
def test_footage_smallest_chapter_against_itself_is_all_same() -> None:
    chapter = load_local_config().footage_path / "GX011628.MP4"
    if not chapter.is_file():
        pytest.skip("GX011628.MP4 is not in the footage folder")
    record = compare.compare_files(chapter, chapter)
    assert _different(record) == []
    items = _items(record)
    assert items["video frame count"]["source"] > 0
    assert items["GPMF track gpmd (pts, duration, size, MD5) [meta#0]"]["status"] == SAME
    assert {i["class"] for i in record["items"]} == {MANDATORY, REQUIRED, BEST_EFFORT}
