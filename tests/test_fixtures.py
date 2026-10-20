"""Tests of the shared fixtures (WP2.3): the manifest, the samples, the generators, the plugin.

What is measured here is measured from the files, not read from the command that made them:
PNG headers by ``struct``, profiles by byte comparison, Orientation and ``irot`` from the
containers, tags, rotation, pts and truncation by ffprobe, the clip by an FFmpeg decode.
Each control that can fail has a planted defect that must fail it by name.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import io
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pillow_heif
import pytest
from PIL import ExifTags, Image, ImageCms, ImageOps

from fixture_plugin import (
    FIXTURES_DIR,
    REPO_ROOT,
    SKIP_NO_FFMPEG,
    SampleProvider,
    load_manifest,
    verify_generated,
    writable_dir,
)
from fixtures import files, flicker, generate, manifest, stills, video
from spike_io import photo
from spike_io.guard import WriteGuard

MANIFEST = json.loads((FIXTURES_DIR / "manifest.json").read_text(encoding="ascii"))
ENTRIES = {item["id"]: item for item in MANIFEST["samples"]}
STILL_IDS = [i for i, e in ENTRIES.items() if e["group"] == "stills"]
VIDEO_IDS = [i for i, e in ENTRIES.items() if e["group"] == "video"]
TOOLS_DIR = REPO_ROOT / "tools"
GENERATOR_SOURCES = sorted((TOOLS_DIR / "fixtures").glob("*.py"))

needs_ffmpeg = pytest.mark.skipif(not video.tools_available(), reason=SKIP_NO_FFMPEG)


def _guard(root: Path) -> WriteGuard:
    """Return a write guard rooted at an existing folder."""
    return WriteGuard(root=root.resolve())


# --- The manifest -------------------------------------------------------------------------


def test_fixture_package_resolves_to_tools() -> None:
    """``import fixtures`` finds tools/fixtures, never the tests/fixtures data folder."""
    assert Path(stills.__file__).resolve().parent == (TOOLS_DIR / "fixtures").resolve()
    assert (TOOLS_DIR / "fixtures" / "__init__.py").is_file()
    assert not (FIXTURES_DIR / "__init__.py").exists()


def test_committed_manifest_is_valid() -> None:
    assert manifest.validate(MANIFEST) == []
    assert load_manifest() == MANIFEST


def test_manifest_file_is_ascii_json_with_sorted_ids() -> None:
    raw = (FIXTURES_DIR / "manifest.json").read_bytes()
    raw.decode("ascii")
    ids = [item["id"] for item in MANIFEST["samples"]]
    assert ids == sorted(ids)
    assert raw == (json.dumps(MANIFEST, indent=2) + "\n").encode("ascii")


def test_committed_files_match_the_manifest() -> None:
    assert manifest.check_files(MANIFEST, FIXTURES_DIR) == []


def test_sample_inventory_matches_the_brief() -> None:
    wanted = set()
    for content in stills.CONTENTS:
        for icc in stills.ICC_KINDS:
            for prefix in ("png8", "png16", "jpeg", "tiff8", "heic8", "heic10"):
                wanted.add(f"{prefix}-{content}-{icc}")
    for shape in ("land", "port"):
        for orientation in (1, 3, 6, 8):
            wanted.add(f"jpeg-orient-{shape}-o{orientation}")
    wanted |= {f"heic-ad24-{case}" for case in ("both", "irot-only", "exif-only", "neither")}
    wanted |= {"dng-by-extension", "dng-by-tag", "dng-extension-only", "ad14-mask", "ad14-flicker"}
    wanted |= {spec.sample_id for spec in video.SPECS}
    for case in ("upper", "lower"):
        for name in files.GOPRO_NAMES:
            wanted.add(f"gopro-{case}-{name.lower().replace('.', '-')}")
    assert set(ENTRIES) == wanted
    assert {spec.sample_id for spec in video.SPECS} == {
        "vid-hevc8-bt709-full",
        "vid-hevc10",
        "vid-hlg",
        "vid-pq",
        "vid-untagged",
        "vid-truncated",
        "vid-vfr",
        "vid-rotated",
    }
    assert [o["what"] for o in MANIFEST["omitted"]] == ["tiff16-*: 16-bit RGB TIFF"]


def test_expected_faults_use_wp22_names_exactly() -> None:
    faulted = {
        "vid-hlg": [("hlg", "refuse")],
        "vid-pq": [("pq", "refuse")],
        "vid-untagged": [("missing_tags", "warn")],
        "vid-truncated": [("truncated", "warn")],
        "gopro-upper-gl010001-lrv": [("sidecar", "exclude")],
        "gopro-upper-gx010001-thm": [("sidecar", "exclude")],
        "gopro-lower-gl010001-lrv": [("sidecar", "exclude")],
        "gopro-lower-gx010001-thm": [("sidecar", "exclude")],
    }
    for sample_id, entry in ENTRIES.items():
        got = [(f["kind"], f["severity"]) for f in entry["expect"]["faults"]]
        assert got == faulted.get(sample_id, []), sample_id
    assert set(manifest.fault_kinds()) >= {k for v in faulted.values() for k, _ in v}


def test_refusals_are_not_invented_fault_kinds() -> None:
    for sample_id in ("dng-by-extension", "dng-by-tag", "dng-extension-only"):
        expect = ENTRIES[sample_id]["expect"]
        assert expect["faults"] == []
        assert expect["refusal"]["clause"] == "D116"
    assert ENTRIES["dng-by-tag"]["expect"]["refusal"]["by"] == "tag"
    assert ENTRIES["dng-by-extension"]["expect"]["refusal"]["by"] == "extension"


# --- Planted defects: every control fails by name ------------------------------------------


def _mutated(change: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    data = copy.deepcopy(MANIFEST)
    change(data)
    return data


def _sample(data: dict[str, Any], sample_id: str) -> dict[str, Any]:
    return next(item for item in data["samples"] if item["id"] == sample_id)


PLANTED_MANIFESTS = [
    (
        lambda m: _sample(m, "vid-hlg")["expect"]["faults"].append(
            {"kind": "bogus_kind", "severity": "warn"}
        ),
        "sample 'vid-hlg': fault kind 'bogus_kind' is not defined by clearwater.interfaces",
    ),
    (
        lambda m: _sample(m, "vid-pq")["expect"]["faults"].__setitem__(
            0, {"kind": "pq", "severity": "shrug"}
        ),
        "sample 'vid-pq': fault severity 'shrug' is not defined",
    ),
    (
        lambda m: _sample(m, "png8-uniform-none").__setitem__("group", "audio"),
        "sample 'png8-uniform-none': group 'audio'",
    ),
    (
        lambda m: _sample(m, "ad14-flicker").__setitem__("command", None),
        "sample 'ad14-flicker': a generated sample needs its regeneration command",
    ),
    (
        lambda m: _sample(m, "png8-uniform-none").__setitem__("md5", None),
        "sample 'png8-uniform-none': a byte-reproducible sample needs a 32-digit md5",
    ),
    (
        lambda m: _sample(m, "png8-uniform-none").__setitem__("path", "../escape.png"),
        "sample 'png8-uniform-none': path '../escape.png'",
    ),
    (
        lambda m: _sample(m, "png8-uniform-none").__setitem__("size", 2_000_001),
        "sample 'png8-uniform-none': committed size 2000001 exceeds 2000000",
    ),
    (
        lambda m: m["samples"].append(copy.deepcopy(_sample(m, "png8-uniform-none"))),
        "sample 'png8-uniform-none': duplicate id",
    ),
    (
        lambda m: _sample(m, "png8-uniform-none").pop("serves"),
        "sample 'png8-uniform-none': lacks 'serves'",
    ),
    (
        lambda m: _sample(m, "png8-uniform-srgb")["expect"]["photo"]["image"]["color"].__setitem__(
            "colour_space", "srgb"
        ),
        "photo.image.color key 'colour_space' is not a ColorDescription field",
    ),
    (
        lambda m: _sample(m, "png8-uniform-srgb")["expect"]["photo"]["metadata"].__setitem__(
            "bit_depth", 8
        ),
        "photo.metadata key 'bit_depth' is not a PhotoMetadata field",
    ),
    (
        lambda m: _sample(m, "vid-vfr")["expect"]["probe"]["video"].__setitem__("tag_state", "x"),
        "probe.video key 'tag_state' is not a VideoStreamInfo field",
    ),
    (
        lambda m: _sample(m, "vid-vfr")["expect"]["probe"].__setitem__("frames", 30),
        "probe key 'frames' is not a ProbeResult field",
    ),
]


@pytest.mark.parametrize(("change", "message"), PLANTED_MANIFESTS)
def test_planted_manifest_defect_fails_by_name(
    change: Callable[[dict[str, Any]], None], message: str
) -> None:
    problems = manifest.validate(_mutated(change))
    assert any(message in problem for problem in problems), problems


def _copy_tree(tmp_path: Path) -> Path:
    target = tmp_path / "fixtures"
    shutil.copytree(FIXTURES_DIR, target)
    return target


def test_planted_oversize_file_fails_the_limits_check(tmp_path: Path) -> None:
    root = _copy_tree(tmp_path)
    (root / "stills" / "big.bin").write_bytes(b"\0" * (manifest.MAX_FILE_BYTES + 1))
    problems = manifest.check_files(MANIFEST, root)
    assert any("stills/big.bin" in p and "exceeds the 2000000 byte limit" in p for p in problems)
    assert any("stills/big.bin: not listed in the manifest" in p for p in problems)


def test_planted_total_over_the_cap_fails(tmp_path: Path) -> None:
    root = _copy_tree(tmp_path)
    for number in range(6):
        (root / f"filler{number}.bin").write_bytes(b"\0" * 1_900_000)
    problems = manifest.check_files(MANIFEST, root)
    assert any("not under 10000000" in p for p in problems), problems


def test_planted_changed_and_missing_files_fail_by_name(tmp_path: Path) -> None:
    root = _copy_tree(tmp_path)
    target = root / ENTRIES["png8-gradient-srgb"]["path"]
    data = bytearray(target.read_bytes())
    data[-20] ^= 0xFF
    target.write_bytes(bytes(data))
    (root / ENTRIES["dng-by-tag"]["path"]).unlink()
    problems = manifest.check_files(MANIFEST, root)
    assert any("'png8-gradient-srgb'" in p and "does not match its md5" in p for p in problems)
    assert any("'dng-by-tag'" in p and "is missing" in p for p in problems)


def test_limits_are_the_ruling_4_figures() -> None:
    assert manifest.MAX_FILE_BYTES == 2_000_000
    assert manifest.MAX_TOTAL_BYTES == 10_000_000
    sizes = [f.stat().st_size for f in FIXTURES_DIR.rglob("*") if f.is_file()]
    assert max(sizes) <= manifest.MAX_FILE_BYTES
    assert sum(sizes) < manifest.MAX_TOTAL_BYTES


# --- Stills, measured from the files ------------------------------------------------------


def _png_header(data: bytes) -> tuple[int, int, int, int]:
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    width, height, depth, colour = struct.unpack(">IIBB", data[16:26])
    return width, height, depth, colour


def _png_icc(data: bytes) -> bytes | None:
    at = 8
    while at < len(data):
        (length,) = struct.unpack(">I", data[at : at + 4])
        kind, body = data[at + 4 : at + 8], data[at + 8 : at + 8 + length]
        if kind == b"iCCP":
            return zlib.decompress(body[body.index(b"\0") + 2 :])
        at += 12 + length
    return None


def _heic_orientation(raw: bytes | None) -> int | None:
    """Return the EXIF Orientation inside a HEIC's EXIF block, or None."""
    if not raw:
        return None
    exif = Image.Exif()
    exif.load(raw if raw.startswith(b"Exif\x00\x00") else b"Exif\x00\x00" + raw)
    return exif.get(int(ExifTags.Base.Orientation))


def _read_still(path: Path) -> dict[str, Any]:
    """Measure a still with code that shares nothing with ``stills.measure``."""
    data = path.read_bytes()
    pillow_heif.register_heif_opener()
    if data.startswith(b"\x89PNG"):
        width, height, depth, colour = _png_header(data)
        assert colour == 2  # RGB
        return {"width": width, "height": height, "depth": depth, "icc": _png_icc(data)}
    if data[4:8] == b"ftyp":
        heif = pillow_heif.open_heif(str(path))
        return {
            "width": heif.size[0],
            "height": heif.size[1],
            "depth": heif.info["bit_depth"],
            "icc": heif.info.get("icc_profile"),
            "orientation": _heic_orientation(heif.info.get("exif")),
        }
    with Image.open(path) as image:
        assert image.mode == "RGB"
        return {
            "width": image.width,
            "height": image.height,
            "depth": 8,
            "icc": image.info.get("icc_profile"),
            "orientation": image.getexif().get(int(ExifTags.Base.Orientation)),
        }


@pytest.mark.parametrize("sample_id", STILL_IDS)
def test_still_is_what_the_manifest_says(sample_id: str, sample: Callable[[str], Path]) -> None:
    entry = ENTRIES[sample_id]
    measured = _read_still(sample(sample_id))
    facts, photo_expect = entry["facts"], entry["expect"]["photo"]
    metadata, color = photo_expect["metadata"], photo_expect["image"]["color"]
    assert measured["depth"] == facts["bit_depth"] == color["bit_depth"]
    assert (measured["width"], measured["height"]) == (facts["width"], facts["height"])
    kind = facts.get("icc_kind", "none")
    if kind == "none":
        assert measured["icc"] is None
        assert color["icc_profile"] is None
    else:
        assert measured["icc"] == stills.icc_bytes(kind)
        assert facts["icc_md5"] == hashlib.md5(measured["icc"], usedforsecurity=False).hexdigest()
        assert color["icc_profile"] == kind
        assert color["primaries"] == ("display-p3" if kind == "display-p3" else "bt709")
    if entry["kind"] in ("jpeg", "heic"):
        assert measured["orientation"] == facts["exif_orientation"]
    assert metadata["source_format"] == entry["kind"]
    assert metadata["orientation"] == (measured.get("orientation") or 1)
    assert photo_expect["image"]["orientation_applied"] is True


def _unit_pixels(path: Path) -> np.ndarray[Any, Any]:
    """Decode a still to float RGB in [0, 1] (16-bit PNG through PyAV, the rest through Pillow)."""
    pillow_heif.register_heif_opener()
    data = path.read_bytes()
    if data.startswith(b"\x89PNG") and _png_header(data)[2] == 16:
        pixels, _ = photo.pyav_png(path)
        return pixels.astype(np.float64) / 65535
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.float64) / 255


@pytest.mark.parametrize(
    "sample_id", [i for i in STILL_IDS if not i.startswith(("jpeg-o", "heic-a"))]
)
def test_still_pixels_are_the_named_content(sample_id: str, sample: Callable[[str], Path]) -> None:
    """Uniform is uniform, the gradient rises along x only, low-red is blue-green, red <= 2/255."""
    content = ENTRIES[sample_id]["facts"]["content"]
    lossless = ENTRIES[sample_id]["facts"]["lossless"]
    pixels = _unit_pixels(sample(sample_id))
    tolerance = 0.5 / 255 if lossless else 3.0 / 255  # mean error against the generated content
    if content == "uniform":
        assert np.allclose(pixels.reshape(-1, 3).mean(axis=0), [0.25, 0.50, 0.60], atol=3 / 255)
        if lossless:
            assert np.ptp(pixels.reshape(-1, 3), axis=0).max() < 1.5 / 255  # one colour
    elif content == "gradient":
        columns = pixels.mean(axis=0)  # (width, 3)
        assert columns[0].max() < 0.03 and columns[-1].min() > 0.97  # black to white
        assert np.all(np.diff(columns[:, 1]) > -2 / 255)  # rises left to right
        rows = pixels.mean(axis=1)  # (height, 3): nothing changes down the image
        assert np.ptp(rows[:, 1]) < 3 / 255
        assert np.abs(pixels[..., 0] - pixels[..., 1]).max() < 4 / 255  # grey: R = G = B
    else:
        assert content == "lowred"
        assert pixels[..., 0].max() <= (2 + 0.5) / 255
        assert pixels[..., 1].mean() > 0.4 and pixels[..., 2].mean() > 0.5  # a blue-green scene
        assert pixels[:, -1, 1].mean() > pixels[:, 0, 1].mean() + 0.2  # green rises to the right
        assert pixels[-1, :, 2].mean() > pixels[0, :, 2].mean() + 0.2  # blue rises downwards
    reference = stills.unit_content(content, red_levels=2 if lossless else stills.LOSSY_RED_LEVELS)
    bits = ENTRIES[sample_id]["expect"]["photo"]["image"]["color"]["bit_depth"]
    scale = (1 << bits) - 1
    if bits == 16:
        expected_pixels = np.round(reference * scale) / scale
    else:
        expected_pixels = np.round(reference * 255) / 255
    assert float(np.mean(np.abs(pixels - expected_pixels))) < tolerance, sample_id


@pytest.mark.parametrize("sample_id", [i for i in STILL_IDS if i.startswith(("png8", "png16"))])
def test_png_samples_have_the_documented_chunks_and_depth(
    sample_id: str, sample: Callable[[str], Path]
) -> None:
    data = sample(sample_id).read_bytes()
    _, _, depth, _ = _png_header(data)
    assert depth == (16 if sample_id.startswith("png16") else 8)
    kinds = [k for k, _ in photo.png_chunks(data)]
    assert ("iCCP" in kinds) == (not sample_id.endswith("-none"))
    assert "eXIf" not in kinds


def test_p3_and_srgb_profiles_are_built_not_borrowed() -> None:
    p3, srgb = photo.display_p3_profile(), stills.srgb_profile()
    assert p3 != srgb
    assert photo.PROFILE_DESCRIPTION.encode("utf-16-be") in p3
    ImageCms.ImageCmsProfile(io.BytesIO(p3))  # both open in LittleCMS
    ImageCms.ImageCmsProfile(io.BytesIO(srgb))
    # The header date is pinned, so the profile does not depend on the clock.
    assert srgb[24:36] == struct.pack(">6H", 2026, 10, 20, 0, 0, 0)
    assert stills.srgb_profile() == srgb


@pytest.mark.parametrize("sample_id", [i for i in STILL_IDS if "-lowred-" in i])
def test_low_red_content_keeps_red_at_or_below_two_levels(
    sample_id: str, sample: Callable[[str], Path]
) -> None:
    path = sample(sample_id)
    limit = 514 if sample_id.startswith("png16") else 2  # 2/255 in the file's own scale
    assert stills.red_max(path) <= limit, sample_id  # JPEG and HEIC too, after the codec
    assert ENTRIES[sample_id]["facts"]["red_max"] == stills.red_max(path)


def test_stills_carry_no_gps(sample: Callable[[str], Path]) -> None:
    pillow_heif.register_heif_opener()
    for sample_id in [*STILL_IDS, "dng-by-extension", "dng-by-tag", "dng-extension-only"]:
        path = sample(sample_id)
        data = path.read_bytes()
        if data.startswith(b"\x89PNG"):
            # Only pixels and profile: no eXIf, iTXt, tEXt or XMP chunk could hold a GPS block.
            assert {k for k, _ in photo.png_chunks(data)} <= {"IHDR", "iCCP", "IDAT", "IEND"}
            continue
        if data[4:8] == b"ftyp":
            raw = pillow_heif.open_heif(str(path)).info.get("exif")
            exif = photo.load_exif(raw) if raw else Image.Exif()
        else:
            with Image.open(path) as image:
                exif = image.getexif()
        assert not exif.get_ifd(ExifTags.IFD.GPSInfo), sample_id
        assert int(ExifTags.Base.GPSInfo) not in exif, sample_id


@pytest.mark.parametrize("shape", ["land", "port"])
@pytest.mark.parametrize("orientation", [1, 3, 6, 8])
def test_jpeg_orientation_samples(
    shape: str, orientation: int, sample: Callable[[str], Path]
) -> None:
    path = sample(f"jpeg-orient-{shape}-o{orientation}")
    display = (96, 64) if shape == "land" else (64, 96)
    with Image.open(path) as image:
        assert image.getexif().get(int(ExifTags.Base.Orientation)) == orientation
        stored = (image.width, image.height)
        upright = np.asarray(ImageOps.exif_transpose(image).convert("RGB"), dtype=np.float64)
    assert stored == (display[::-1] if orientation in (6, 8) else display)
    reference = photo.upright_image(8, *display).astype(np.float64)
    assert upright.shape == reference.shape
    assert float(np.mean(np.abs(upright - reference))) < 4.0  # lossy JPEG, upright once


@pytest.mark.parametrize(
    ("case", "irot", "tag", "stored"),
    [
        ("both", 270, 6, (64, 96)),
        ("irot-only", 270, 1, (64, 96)),
        ("exif-only", None, 6, (64, 96)),
        ("neither", None, 1, (96, 64)),
    ],
)
def test_ad24_heic_cases_differ_as_named(
    case: str, irot: int | None, tag: int, stored: tuple[int, int], sample: Callable[[str], Path]
) -> None:
    path = sample(f"heic-ad24-{case}")
    data = path.read_bytes()
    assert photo.heif_transforms(data)["irot"] == irot
    raw = pillow_heif.open_heif(str(path)).info.get("exif")
    assert photo.load_exif(raw).get(int(ExifTags.Base.Orientation)) == tag
    pillow_heif.register_heif_opener()
    upright = photo.upright_image(8, 96, 64)
    with Image.open(path) as image:
        decoded = np.asarray(image.convert("RGB"))
    # libheif applied any irot, so only the tag-only file comes out still turned (64 x 96 stored).
    assert decoded.shape[:2] == ((96, 64) if case == "exif-only" else (64, 96))
    facts = ENTRIES[f"heic-ad24-{case}"]["facts"]
    assert (facts["stored_width"], facts["stored_height"]) == stored
    # AD-24 rule: apply the tag only when the file has no irot; the result is upright for all four.
    applied = decoded
    if tag != 1 and irot is None:
        applied = photo.apply_orientation(decoded, tag)
    assert photo.pose(applied, 8, upright, 8, 6 if case != "neither" else 1) == "upright"
    # The two naive readers each fail one case: that is what makes the cases different.
    always = photo.apply_orientation(decoded, tag)
    never = decoded
    if case == "both":
        assert photo.pose(always, 8, upright, 8, 6) == "twice"
    if case == "exif-only":
        assert photo.pose(never, 8, upright, 8, 6) == "stored"
    if case == "irot-only":
        assert photo.pose(never, 8, upright, 8, 6) == "upright"
    if case == "neither":
        assert photo.pose(always, 8, upright, 8, 1) == "upright"


def test_heic_ten_bit_arrives_as_sixteen_bit_samples(sample: Callable[[str], Path]) -> None:
    heif = pillow_heif.open_heif(str(sample("heic10-gradient-none")), convert_hdr_to_8bit=False)
    pixels = np.asarray(heif)
    assert heif.info["bit_depth"] == 10
    assert pixels.dtype == np.uint16
    assert not np.any(pixels & 0x3F)  # ten bits shifted left by six


def test_planted_profile_mismatch_is_reported(sample: Callable[[str], Path]) -> None:
    """A Display P3 file measured against the sRGB profile must say it differs."""
    path = sample("png8-gradient-display-p3")
    assert stills.measure(path, stills.srgb_profile())["icc"] == "differs"
    assert stills.measure(path, photo.display_p3_profile())["icc"] == "match"


# --- Dummy files and DNG ------------------------------------------------------------------


def test_dng_samples_carry_or_lack_the_tag(sample: Callable[[str], Path]) -> None:
    for sample_id in ("dng-by-extension", "dng-by-tag"):
        with Image.open(sample(sample_id)) as image:
            assert tuple(image.tag_v2[50706]) == (1, 4, 0, 0), sample_id
    with Image.open(sample("dng-extension-only")) as image:
        assert 50706 not in image.tag_v2
    assert sample("dng-by-extension").suffix == ".dng"
    assert sample("dng-by-tag").suffix == ".tif"
    assert sample("dng-extension-only").suffix == ".dng"
    # The tag is in the file's own bytes, not only in what Pillow reports: TIFF type BYTE (1),
    # count 4, value 1 4 0 0 (DNGVersion as the DNG specification defines it).
    for sample_id in ("dng-by-extension", "dng-by-tag"):
        assert files.dng_entry(sample(sample_id)) == (1, 4, bytes((1, 4, 0, 0))), sample_id
        assert ENTRIES[sample_id]["facts"]["dng_version_type"] == 1
        assert ENTRIES[sample_id]["facts"]["dng_version_count"] == 4
    assert files.dng_entry(sample("dng-extension-only")) is None
    for sample_id in STILL_IDS:
        if sample_id.startswith("tiff8"):
            with Image.open(sample(sample_id)) as image:
                assert 50706 not in image.tag_v2, sample_id


def test_gopro_placeholders(sample: Callable[[str], Path]) -> None:
    for case in ("upper", "lower"):
        folder = {sample(i).parent for i in ENTRIES if i.startswith(f"gopro-{case}-")}
        assert len(folder) == 1
    upper = sorted(p.name for p in sample("gopro-upper-gx010001-mp4").parent.iterdir())
    lower = sorted(p.name for p in sample("gopro-lower-gx010001-mp4").parent.iterdir())
    assert upper == sorted(files.GOPRO_NAMES)
    assert lower == sorted(n.lower() for n in files.GOPRO_NAMES)
    for sample_id, entry in ENTRIES.items():
        if entry["kind"] != "placeholder":
            continue
        path = sample(sample_id)
        assert b"\n" not in path.read_bytes()  # nothing for git's CRLF conversion to touch
        assert entry["facts"]["sidecar"] == path.name.lower().endswith((".lrv", ".thm"))
    assert files.SIDECAR_SUFFIXES == (".lrv", ".thm")


# --- Video, measured with ffprobe and a decode --------------------------------------------


def _probe_view(facts: dict[str, Any]) -> dict[str, Any]:
    """Derive the ``expect.probe`` shape from measured ffprobe facts, independently of the spec.

    An HLG or PQ stream has no ``color`` (refused at probe); a stream whose bitstream has no video
    signal type gets the D54 defaults and ``assumed``; the rest is ffprobe's words in WP2.2's.
    """
    v = facts["video"]
    view: dict[str, Any] = {
        "codec": v["codec"],
        "width": v["width"],
        "height": v["height"],
        "bit_depth": 10 if "10" in v["pix_fmt"] else 8,
        "frame_rate": v["avg_frame_rate"],
        "time_base": v["time_base"],
        "nb_frames": v["nb_frames"],
        "rotation": v["rotation"],
        "vfr": facts["pts"]["variable"],
    }
    bits = view["bit_depth"]
    if v["vui"].get("video_signal_type_present_flag") == 0:
        view["color"] = {
            "primaries": "bt709",
            "transfer": "bt709",
            "matrix": "bt709",
            "range": "limited",
            "assumed": True,
            "bit_depth": bits,
        }
    elif v["color_transfer"] not in ("arib-std-b67", "smpte2084"):
        view["color"] = {
            "primaries": v["color_primaries"],
            "transfer": v["color_transfer"],
            "matrix": v["color_space"],
            "range": {"pc": "full", "tv": "limited"}[v["color_range"]],
            "bit_depth": bits,
            "assumed": False,
        }
    return {
        "container": facts["container"],
        "video": view,
        "audio": [
            {"codec": a["codec"], "sample_rate": a["sample_rate"], "channels": a["channels"]}
            for a in facts["audio"]
        ],
        "data": facts["data_streams"],
    }


@needs_ffmpeg
@pytest.mark.parametrize("sample_id", VIDEO_IDS)
def test_video_is_what_the_manifest_says(sample_id: str, sample: Callable[[str], Path]) -> None:
    entry = ENTRIES[sample_id]
    facts = video.measure(sample(sample_id))
    for key, value in facts.items():
        assert entry["facts"][key] == value, f"{sample_id}: {key}"
    spec = next(s for s in video.SPECS if s.sample_id == sample_id)
    assert video.mismatches(spec, facts) == []
    assert entry["expect"]["probe"] == video.expectation(spec)
    # The expectation also equals what the measured file says, read through WP2.2's names.
    assert entry["expect"]["probe"] == _probe_view(facts), sample_id


@needs_ffmpeg
def test_video_tags_are_actually_in_the_streams(sample: Callable[[str], Path]) -> None:
    seen = {}
    for sample_id in VIDEO_IDS:
        v = video.measure(sample(sample_id))["video"]
        seen[sample_id] = (
            v["color_range"],
            v["color_space"],
            v["color_transfer"],
            v["color_primaries"],
        )
    assert seen["vid-hevc8-bt709-full"] == ("pc", "bt709", "bt709", "bt709")
    assert seen["vid-hlg"] == ("tv", "bt2020nc", "arib-std-b67", "bt2020")
    assert seen["vid-pq"] == ("tv", "bt2020nc", "smpte2084", "bt2020")
    assert seen["vid-untagged"] == ("unknown", "unknown", "unknown", "unknown")
    untagged = video.measure(sample("vid-untagged"))["video"]
    assert untagged["vui"] == {"video_signal_type_present_flag": 0}  # no signal type at all
    assert untagged["codec"] == "h264"
    for sample_id in VIDEO_IDS:  # every other clip does carry the signal type it claims
        flags = video.measure(sample(sample_id))["video"]["vui"]
        if sample_id != "vid-untagged":
            assert flags["video_signal_type_present_flag"] == 1, sample_id
            assert flags["colour_description_present_flag"] == 1, sample_id
    assert video.measure(sample("vid-hevc10"))["video"]["bit_depth"] == 10
    assert video.measure(sample("vid-hevc8-bt709-full"))["video"]["bit_depth"] == 8


@needs_ffmpeg
def test_vfr_is_really_variable(sample: Callable[[str], Path]) -> None:
    pts = video.measure(sample("vid-vfr"))["pts"]
    assert pts["ticks"] == video.vfr_ticks()
    assert pts["durations"] == [1001, 2002]
    assert pts["variable"] is True
    assert video.measure(sample("vid-hevc8-bt709-full"))["pts"]["durations"] == [1001]


@needs_ffmpeg
def test_rotation_is_in_the_display_matrix(sample: Callable[[str], Path]) -> None:
    assert video.measure(sample("vid-rotated"))["video"]["rotation"] == 90
    for sample_id in VIDEO_IDS:
        if sample_id != "vid-rotated":
            assert video.measure(sample(sample_id))["video"]["rotation"] == 0, sample_id


@needs_ffmpeg
def test_truncated_clip_has_a_readable_part_and_a_fault(sample: Callable[[str], Path]) -> None:
    facts = video.measure(sample("vid-truncated"))
    assert facts["video"]["nb_frames"] == video.FRAMES
    assert 0 < facts["decoded"]["frames"] < video.FRAMES
    assert any("partial file" in line for line in facts["ffprobe_errors"])
    source = sample("vid-hevc8-bt709-full").stat().st_size
    kept = sample("vid-truncated").stat().st_size
    assert kept == int(source * video.TRUNCATE_KEEP)
    cut = ENTRIES["vid-truncated"]["facts"]
    assert cut["cut_bytes"] == source - kept
    assert cut["source_bytes"] == source


@needs_ffmpeg
def test_video_has_audio_and_no_data_streams_or_location(sample: Callable[[str], Path]) -> None:
    for sample_id in VIDEO_IDS:
        facts = video.measure(sample(sample_id))
        assert [a["codec"] for a in facts["audio"]] == ["aac"], sample_id
        assert facts["data_streams"] == [], sample_id  # no gpmd, no tmcd
        assert facts["has_location_tag"] is False, sample_id


@needs_ffmpeg
def test_planted_video_defects_are_caught_by_name(tmp_path: Path) -> None:
    """A mis-tagged, a constant-rate and an untruncated file fail the specs they pretend to be."""
    guard = _guard(tmp_path)
    scratch = tmp_path / "s"
    scratch.mkdir()
    hevc8, vfr, truncated = video.SPECS[0], video.SPECS[6], video.SPECS[5]
    hlg = next(s for s in video.SPECS if s.sample_id == "vid-hlg")
    target = tmp_path / "mistagged.mp4"
    video.run_ffmpeg(
        guard, [*video._lavfi_inputs(video.DURATION_S), *video._encode_args(hlg)], target, scratch
    )
    wrong = video.mismatches(hevc8, video.measure(target))
    assert any("color_transfer is 'arib-std-b67', intended 'bt709'" in w for w in wrong), wrong
    assert any("bit depth is 10, intended 8" in w for w in wrong), wrong
    constant = video.measure(target)
    assert any("variable frame rate" in w for w in video.mismatches(vfr, constant))
    assert any("partial file" in w for w in video.mismatches(truncated, constant))
    # x265 with no tags still writes a video signal type: it is not an untagged sample.
    plain = video.Spec("x", "yuv420p", video.UNTAGGED, (), "plain x265")
    target = tmp_path / "plain.mp4"
    video.run_ffmpeg(
        guard, [*video._lavfi_inputs(video.DURATION_S), *video._encode_args(plain)], target, scratch
    )
    untagged = next(s for s in video.SPECS if s.sample_id == "vid-untagged")
    wrong = video.mismatches(untagged, video.measure(target))
    assert any("VUI video_signal_type_present_flag is 1, intended 0" in w for w in wrong), wrong
    assert any("codec is 'hevc', intended 'h264'" in w for w in wrong), wrong


# --- The AD-14 flicker clip ---------------------------------------------------------------


def test_flicker_mask_is_the_upper_half(sample: Callable[[str], Path]) -> None:
    with Image.open(sample("ad14-mask")) as image:
        mask = np.asarray(image)
    assert mask.shape == (540, 960)
    assert set(np.unique(mask)) == {0, 255}
    assert np.all(mask[:270] == 255)
    assert np.all(mask[270:] == 0)
    assert np.array_equal(mask == 255, flicker.region_mask())


def test_disc_never_enters_the_measured_region_and_has_ten_percent_area(
    sample: Callable[[str], Path],
) -> None:
    with Image.open(sample("ad14-mask")) as image:
        region = np.asarray(image) == 255
    frame_area = flicker.WIDTH * flicker.HEIGHT
    first_columns, last_columns = [], []
    for index in range(flicker.FRAMES):
        disc = flicker.disc_mask(index)
        assert not np.any(disc & region), index
        assert abs(disc.sum() / frame_area - 0.10) < 0.0005, index
        columns = np.flatnonzero(disc.any(axis=0))
        first_columns.append(columns[0])
        last_columns.append(columns[-1])
        rows = np.flatnonzero(disc.any(axis=1))
        assert rows[0] >= 270 and rows[-1] < flicker.HEIGHT
        assert 2 * flicker.HEIGHT // 3 <= flicker.DISC_CENTRE_ROW < flicker.HEIGHT
    assert first_columns[0] == 0 or first_columns[0] <= 1
    assert last_columns[-1] >= flicker.WIDTH - 2
    assert first_columns == sorted(first_columns)  # sweeps one way
    # A disc that did enter the region is caught: raise it into the upper half.
    higher = flicker.disc_mask(0).copy()
    higher = np.roll(higher, -200, axis=0)
    assert np.any(higher & region)


def test_flicker_design_facts_are_the_measured_ones() -> None:
    design = ENTRIES["ad14-flicker"]["facts"]["design"]
    assert design["frames"] == 90
    assert design["frame_rate"] == "30000/1001"
    assert design["disc_pixels_in_region"] == 0
    assert design["region_pixels_changed_between_frames"] == 0
    assert design["disc_first_row"] > 269
    assert design["disc_last_row"] < 540
    assert 0.0999 < design["disc_area_fraction_min"] <= design["disc_area_fraction_max"] < 0.1001


def test_flicker_texture_matches_wp1_3_whole_frame_statistics() -> None:
    """Channel means within 0.005 of WP1.3's 180 flicker frames; N{} spread near their mean 0.38."""
    image = flicker.still()
    means = image.reshape(-1, 3).mean(axis=0) / 255
    assert np.allclose(means, [0.426, 0.572, 0.546], atol=0.005), means
    spread = flicker.normalisation_spread(image)
    assert 0.34 <= spread <= 0.42, spread  # WP1.3: 0.27 to 0.52, mean 0.38
    design = ENTRIES["ad14-flicker"]["facts"]["design"]
    assert design["texture_normalisation_spread"] == pytest.approx(spread, abs=0.0006)
    assert design["texture_channel_means"] == pytest.approx(list(means), abs=0.0001)
    assert design["wp1_3_reference"]["channel_means"] == [0.426, 0.572, 0.546]
    assert image.shape == (540, 960, 3)


@needs_ffmpeg
def test_flicker_clip_decodes_to_the_manifest_frames(sample: Callable[[str], Path]) -> None:
    path = sample("ad14-flicker")
    entry = ENTRIES["ad14-flicker"]
    assert verify_generated(entry, path) is None
    facts = flicker.measure_clip(path)
    assert (facts["codec"], facts["decoded_frames"], facts["r_frame_rate"]) == (
        "ffv1",
        90,
        "30000/1001",
    )
    assert (facts["width"], facts["height"]) == (960, 540)
    assert facts["decoded_rgb24_sha256"] == entry["facts"]["design"]["frames_rgb24_sha256"]
    # The measured region is identical in every decoded frame; the disc shows in the lower half.
    command = [
        "ffmpeg",
        "-nostdin",
        "-v",
        "error",
        "-i",
        str(path),
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    ]
    done = subprocess.run(command, capture_output=True, check=True)
    frames = np.frombuffer(done.stdout, dtype=np.uint8).reshape(90, 540, 960, 3)
    assert np.all(frames[:, :270] == frames[0, :270])
    assert np.any(frames[0, 270:] != frames[45, 270:])


@needs_ffmpeg
def test_planted_wrong_clip_fails_the_hash_check(
    sample: Callable[[str], Path], tmp_path: Path
) -> None:
    entry = ENTRIES["ad14-flicker"]
    problem = verify_generated(entry, sample("vid-hevc8-bt709-full"))
    assert problem is not None and "5 frames decode to" in problem
    assert verify_generated(entry, tmp_path / "absent.mkv") is not None
    changed = copy.deepcopy(entry)
    changed["facts"]["design"]["frames_rgb24_sha256"] = "0" * 64
    problem = verify_generated(changed, sample("ad14-flicker"))
    assert problem is not None and "the manifest has 90 frames and " + "0" * 64 in problem


# --- Regeneration is deterministic ---------------------------------------------------------


@pytest.fixture(scope="module")
def regenerated_cheap(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Stills, dummy files and the mask, regenerated without FFmpeg."""
    out = tmp_path_factory.mktemp("regen-cheap")
    guard = _guard(out)
    entries = stills.build(guard, out.resolve()) + files.build(guard, out.resolve())
    entries.append(flicker.build_mask(guard, out.resolve()))
    return out


def test_stills_files_and_mask_regenerate_byte_identically(regenerated_cheap: Path) -> None:
    compared = 0
    for entry in MANIFEST["samples"]:
        if entry["group"] in ("stills", "files") or entry["id"] == "ad14-mask":
            assert entry["byte_reproducible"] is True
            fresh = regenerated_cheap / entry["path"]
            assert fresh.read_bytes() == (FIXTURES_DIR / entry["path"]).read_bytes(), entry["id"]
            assert manifest.md5_of(fresh) == entry["md5"], entry["id"]
            compared += 1
    assert compared == 66 + 11 + 1
    assert {
        p.relative_to(regenerated_cheap).as_posix()
        for p in regenerated_cheap.rglob("*")
        if p.is_file()
    } == {
        e["path"]
        for e in MANIFEST["samples"]
        if e["group"] in ("stills", "files") or e["id"] == "ad14-mask"
    }


@pytest.fixture(scope="module")
def regenerated_full(tmp_path_factory: pytest.TempPathFactory) -> tuple[dict[str, Any], Path, Path]:
    """Everything regenerated (needs FFmpeg): the manifest and the two output folders."""
    if not video.tools_available():
        pytest.skip(SKIP_NO_FFMPEG)
    out = tmp_path_factory.mktemp("regen-full")
    generated = tmp_path_factory.mktemp("regen-generated")
    result = generate.generate(out, generated)
    assert result is not None
    return result, out, generated


def test_regenerated_manifest_is_byte_identical(
    regenerated_full: tuple[dict[str, Any], Path, Path],
) -> None:
    _, out, generated = regenerated_full
    fresh = (out / "manifest.json").read_bytes()
    # Raw bytes on both sides: `.gitattributes` marks tests/fixtures/** as `-text`, so git never
    # converts line endings in the committed fixtures, whatever core.autocrlf says.
    assert fresh == (FIXTURES_DIR / "manifest.json").read_bytes()
    assert [p.name for p in out.iterdir() if p.is_file()] == ["manifest.json"]
    assert not (out / video.SCRATCH).exists()  # intermediates are gone
    assert not (generated / "video").exists()


def test_regenerated_video_matches_by_decoded_frame_hash(
    regenerated_full: tuple[dict[str, Any], Path, Path],
) -> None:
    _, out, generated = regenerated_full
    for sample_id in VIDEO_IDS:
        entry = ENTRIES[sample_id]
        fresh = video.decode_hashes(out / entry["path"])
        assert fresh["frames_sha256"] == entry["facts"]["decoded"]["frames_sha256"], sample_id
        assert fresh["pts_sha256"] == entry["facts"]["decoded"]["pts_sha256"], sample_id
        committed = video.decode_hashes(FIXTURES_DIR / entry["path"])
        assert committed["frames_sha256"] == fresh["frames_sha256"], sample_id
    clip = ENTRIES["ad14-flicker"]
    assert verify_generated(clip, generated / clip["path"]) is None


# --- No owner material, FFmpeg writes only where told ----------------------------------------


FORBIDDEN_MODULES = {"local_config", "footage_locator"}
FORBIDDEN_NAMES = {"find_footage_file", "load_local_config", "footage_available", "footage_path"}


def footage_hits(text: str) -> list[str]:
    """Return what in generator source reaches for the configuration or the footage folder."""
    hits = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            hits += [a.name for a in node.names if a.name.split(".")[0] in FORBIDDEN_MODULES]
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in FORBIDDEN_MODULES:
                hits.append(node.module or "")
            hits += [a.name for a in node.names if a.name in FORBIDDEN_NAMES]
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            hits.append(node.id)
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_NAMES:
            hits.append(node.attr)
    hits += [m for m in ("clearwater.local.toml", "clearwater-footage") if m in text]
    return hits


def test_generators_import_nothing_that_reads_the_footage() -> None:
    assert len(GENERATOR_SOURCES) >= 7, "generator sources not found"
    for source in GENERATOR_SOURCES:
        assert footage_hits(source.read_text(encoding="utf-8")) == [], source.name


@pytest.mark.parametrize(
    "planted",
    [
        "from local_config import LocalConfig\n",
        "import local_config\n",
        "from local_config import find_footage_file\n",
        "def f(c):\n    return c.footage_path\n",
        "root = 'C:/Users/x/clearwater-footage'\n",
    ],
)
def test_planted_footage_access_is_caught_by_the_static_check(planted: str) -> None:
    assert footage_hits(planted) != []


AUDIT_SCRIPT = """
import json, os, shlex, sys
sys.dont_write_bytecode = True
events = {"open": [], "popen": [], "listdir": []}
def hook(event, args):
    if event == "open":
        path, mode, flags = args
        if isinstance(path, (str, bytes, os.PathLike)):
            events["open"].append([os.fsdecode(path), mode, flags])
    elif event in ("os.listdir", "os.scandir"):
        if isinstance(args[0], (str, bytes, os.PathLike)):
            events["listdir"].append(os.fsdecode(args[0]))
    elif event == "subprocess.Popen":
        command = args[1]
        if isinstance(command, str):  # Windows hands the audit hook the joined command line
            command = [part.strip('"') for part in shlex.split(command, posix=False)]
        events["popen"].append({"args": [str(a) for a in command], "cwd": str(args[2])})
sys.addaudithook(hook)
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from fixtures import generate
generate.generate(Path(sys.argv[2]), Path(sys.argv[3]))
with open(sys.argv[4], "w") as handle:
    json.dump(events, handle)
"""


def _inside(path: str, roots: list[Path]) -> bool:
    real = Path(os.path.normcase(os.path.realpath(path)))
    return any(real.is_relative_to(Path(os.path.normcase(os.path.realpath(r)))) for r in roots)


@pytest.fixture(scope="module")
def audited_run(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """Run the whole generator in a fresh interpreter with an audit hook; return its events."""
    if not video.tools_available():
        pytest.skip(SKIP_NO_FFMPEG)
    base = tmp_path_factory.mktemp("audit")
    script, events = base / "audit_run.py", base / "events.json"
    out, generated = base / "out", base / "generated"
    script.write_text(AUDIT_SCRIPT, encoding="ascii")
    done = subprocess.run(
        [sys.executable, "-I", str(script), str(TOOLS_DIR), str(out), str(generated), str(events)],
        capture_output=True,
        check=False,
        cwd=base,
    )
    assert done.returncode == 0, done.stderr.decode()[-800:]
    data: dict[str, Any] = json.loads(events.read_text())
    data["out"], data["generated"], data["base"] = out, generated, base
    return data


def test_generators_write_only_inside_their_output_folders(audited_run: dict[str, Any]) -> None:
    roots = [audited_run["out"], audited_run["generated"]]
    writes = []
    for path, mode, flags in audited_run["open"]:
        wrote = any(c in (mode or "") for c in "wax+") or bool(
            flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND)
        )
        if wrote and Path(path) != audited_run["base"] / "events.json":
            writes.append(path)
    assert writes, "the audit saw no writes at all"
    assert [p for p in writes if not _inside(p, roots)] == []


def test_generators_read_only_their_own_code_and_libraries(audited_run: dict[str, Any]) -> None:
    allowed = [
        TOOLS_DIR,
        REPO_ROOT / "src",  # clearwater.interfaces: the Fault vocabulary
        Path(sys.prefix),
        Path(sys.base_prefix),
        audited_run["out"],
        audited_run["generated"],
        audited_run["base"],
    ]
    reads = [
        p for p, mode, flags in audited_run["open"] if not any(c in (mode or "") for c in "wax+")
    ]
    assert reads
    listed = audited_run["listdir"]
    assert listed
    assert [p for p in reads + listed if not _inside(p, allowed)] == []
    footage = _configured_footage()
    if footage is not None:
        assert [p for p in reads + listed if _inside(p, [footage])] == []


def _configured_footage() -> Path | None:
    from local_config import LocalConfigError, load_local_config

    try:
        return load_local_config().footage_path
    except (LocalConfigError, OSError):
        return None


def test_ffmpeg_is_told_to_write_only_into_the_output_folders(audited_run: dict[str, Any]) -> None:
    roots = [audited_run["out"], audited_run["generated"]]
    runs = [p for p in audited_run["popen"] if Path(p["args"][0]).stem in ("ffmpeg", "ffprobe")]
    assert len(runs) == len(audited_run["popen"])  # nothing else is ever started
    ffmpeg_runs = [p for p in runs if Path(p["args"][0]).stem == "ffmpeg"]
    assert len(ffmpeg_runs) >= 12
    writers = 0
    for run in ffmpeg_runs:
        args = run["args"][1:]
        assert "-report" not in args
        paths = [a for a in args if a.endswith((".mp4", ".mkv", ".png")) or Path(a).is_absolute()]
        assert paths, run
        assert all(_inside(p, roots) for p in paths), run
        if run["cwd"] != "None":
            assert _inside(run["cwd"], roots), run
        if args[-1] not in ("-", "pipe:1"):  # an encoding run: its last argument is its one output
            writers += 1
            assert _inside(args[-1], roots), run
    assert writers >= 8
    for run in runs:
        if Path(run["args"][0]).stem == "ffprobe":
            assert _inside(run["args"][-1], roots), run


# --- The plugin ---------------------------------------------------------------------------


def _provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tools: bool) -> SampleProvider:
    monkeypatch.setattr(video, "tools_available", lambda: tools)
    return SampleProvider(MANIFEST, FIXTURES_DIR, tmp_path / "cache", lambda: tmp_path / "scratch")


def test_plugin_skips_a_generated_sample_when_ffmpeg_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = _provider(tmp_path, monkeypatch, tools=False)
    with pytest.raises(pytest.skip.Exception, match="ffmpeg and ffprobe are not on the PATH"):
        provider.path("ad14-flicker")
    assert not (tmp_path / "cache").exists()  # nothing was attempted


def test_plugin_hands_out_committed_samples_without_ffmpeg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = _provider(tmp_path, monkeypatch, tools=False)
    assert provider.path("vid-hlg") == FIXTURES_DIR / "video" / "hlg.mp4"
    assert provider.path("png8-uniform-none").is_file()
    assert provider.ids("files") == [i for i, e in ENTRIES.items() if e["group"] == "files"]
    with pytest.raises(pytest.fail.Exception, match="no sample 'nonsense'"):
        provider.path("nonsense")


def test_plugin_reports_a_missing_committed_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = SampleProvider(MANIFEST, tmp_path / "empty", tmp_path / "cache", lambda: tmp_path)
    monkeypatch.setattr(video, "tools_available", lambda: True)
    with pytest.raises(pytest.fail.Exception, match="committed sample 'vid-hlg' is missing"):
        provider.path("vid-hlg")


def test_cache_folder_must_really_be_writable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An existing folder that refuses a file is not a cache (mkdir(exist_ok=True) would pass)."""
    assert writable_dir(tmp_path / "fresh" / "deeper")
    blocker = tmp_path / "blocker"
    blocker.write_text("a file", encoding="ascii")
    assert not writable_dir(blocker / "sub")  # cannot make the folder
    existing = tmp_path / "existing"
    existing.mkdir()

    def refuse(*args: object, **kwargs: object) -> None:
        raise PermissionError("read-only folder")

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", refuse)
    assert not writable_dir(existing)  # exists, mkdir passes, a write is refused


@needs_ffmpeg
def test_plugin_regenerates_a_stale_clip_and_verifies_it(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    stale = cache / "flicker" / "ad14-flicker.mkv"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"not a video")
    provider = SampleProvider(MANIFEST, FIXTURES_DIR, cache, lambda: tmp_path / "scratch")
    path = provider.path("ad14-flicker")
    assert path == stale
    assert verify_generated(ENTRIES["ad14-flicker"], path) is None
    # Already present and verified: handed out again without another generation.
    again = SampleProvider(MANIFEST, FIXTURES_DIR, cache, lambda: pytest.fail("regenerated"))
    assert again.path("ad14-flicker") == path


@needs_ffmpeg
def test_plugin_fails_when_regeneration_cannot_match(tmp_path: Path) -> None:
    changed = copy.deepcopy(MANIFEST)
    _sample(changed, "ad14-flicker")["facts"]["design"]["frames_rgb24_sha256"] = "f" * 64
    provider = SampleProvider(changed, FIXTURES_DIR, tmp_path / "cache", lambda: tmp_path / "s")
    with pytest.raises(pytest.fail.Exception, match="does not match the manifest"):
        provider.path("ad14-flicker")


# --- The command line ---------------------------------------------------------------------


def test_cli_builds_one_group_and_writes_no_manifest(tmp_path: Path) -> None:
    assert generate.main(["--out", str(tmp_path / "o"), "--group", "files"]) == 0
    assert (tmp_path / "o" / "files" / "dng" / "dng-by-tag.tif").is_file()
    assert not (tmp_path / "o" / "manifest.json").exists()


def test_cli_rejects_an_unknown_group_and_reports_missing_ffmpeg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        generate.main(["--out", str(tmp_path), "--group", "audio"])
    with pytest.raises(ValueError, match="unknown group 'audio'"):
        generate.generate(tmp_path, None, ["audio"])
    monkeypatch.setattr(video, "tools_available", lambda: False)
    assert generate.main(["--out", str(tmp_path / "v"), "--group", "video"]) == 2
    assert "error: ffmpeg and ffprobe must be on the PATH" in capsys.readouterr().err
