"""WP4.1 photo legs through the headless runner: V5, V9, V10, N10 and the CPU-vs-GPU leg.

Every export goes through ``tools/headless_export.py`` over the composition root, on the CPU
(``force_cpu``) except the one ``gpu`` leg; every output is under ``tmp_path`` and the committed
stills are only read. The PNG, ICC, EXIF and provenance checks parse the written file here,
independently of ``clearwater.io.photo``; orientation is checked against Pillow's own decode of
the source (JPEG) and the AD-24 expectation (HEIC). "In multiple viewers" (V5) is WP5.1's leg.
Each claim has a planted control that fails it by name.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import zlib
from pathlib import Path
from typing import Any

import numpy as np
import pillow_heif
import pytest
from PIL import ExifTags, ImageOps
from PIL import Image as PILImage

import headless_export as he
from clearwater import core
from clearwater.app import composition
from clearwater.config import new_parameter_set
from clearwater.interfaces import ParameterSet, Settings
from clearwater.io.photo import PhotoReader, PhotoWriter
from clearwater.io.photo import png as png_tools
from clearwater.io.photo.png import PROVENANCE_KEYWORD
from clearwater.jobs.batch import BatchItem
from fixture_plugin import load_manifest
from spike_io import photo as spike

_MANIFEST = load_manifest()
ENTRIES = {e["id"]: e for e in _MANIFEST["samples"]}
STILL_IDS = [e["id"] for e in _MANIFEST["samples"] if e["group"] == "stills"]
ORIENT_IDS = [i for i in STILL_IDS if i.startswith("jpeg-orient-")]
AD24_IDS = [i for i in STILL_IDS if i.startswith("heic-ad24-")]

SRGB_BUILT_IN_MD5 = "ca34a0279325928fc9fd3fc7eff99eb9"
"""The D53 built-in sRGB profile's md5, as `tests/test_io_photo_srgb.py` pins it."""

BUILT_IN_SRGB_IDS = frozenset(
    [*AD24_IDS, *(f"heic{d}-{c}-none" for d in (8, 10) for c in ("gradient", "lowred", "uniform"))]
)
"""The stills tagged sRGB by ``nclx`` without an ICC profile: the export embeds the D53 built-in
(pinned here, not derived through the writer's own ``built_in_profile``)."""

ORIENTATION = int(ExifTags.Base.Orientation)
SOFTWARE = int(ExifTags.Base.Software)
PIXEL_X = int(ExifTags.Base.ExifImageWidth)
PIXEL_Y = int(ExifTags.Base.ExifImageHeight)
POINTERS = {int(ExifTags.IFD.Exif), int(ExifTags.IFD.GPSInfo), int(ExifTags.IFD.Interop)}


# --- the written PNG, parsed here -----------------------------------------------------------------


def png_chunks(path: Path) -> list[tuple[bytes, bytes]]:
    """Return the ``(type, data)`` of every chunk of a PNG, in file order."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a PNG"
    chunks, at = [], 8
    while at < len(data):
        length = int.from_bytes(data[at : at + 4], "big")
        kind = data[at + 4 : at + 8]
        chunks.append((kind, data[at + 8 : at + 8 + length]))
        at += 12 + length
    return chunks


def bit_depth(path: Path) -> int:
    """The IHDR bit depth."""
    kind, data = png_chunks(path)[0]
    assert kind == b"IHDR"
    return data[8]


def icc_of(path: Path) -> bytes | None:
    """The inflated ``iCCP`` profile, or None."""
    found = [data for kind, data in png_chunks(path) if kind == b"iCCP"]
    assert len(found) <= 1
    if not found:
        return None
    name_end = found[0].index(b"\0")
    assert found[0][name_end + 1] == 0  # compression method 0
    return zlib.decompress(found[0][name_end + 2 :])


def provenance_of(path: Path) -> dict[str, Any] | None:
    """The provenance ``iTXt`` object (D91), or None."""
    found = []
    for kind, data in png_chunks(path):
        if kind != b"iTXt":
            continue
        keyword, rest = data.split(b"\0", 1)
        if keyword.decode("latin-1") != PROVENANCE_KEYWORD:
            continue
        assert rest[:2] == b"\0\0"  # not compressed
        _language, _translated, text = rest[2:].split(b"\0", 2)
        found.append(json.loads(text.decode("utf-8")))
    assert len(found) <= 1
    return found[0] if found else None


def exif_of(path: Path) -> PILImage.Exif | None:
    """The output's ``eXIf`` block parsed by Pillow, or None."""
    found = [data for kind, data in png_chunks(path) if kind == b"eXIf"]
    if not found:
        return None
    exif = PILImage.Exif()
    exif.load(found[0])
    return exif


def source_exif(path: Path, source_format: str) -> PILImage.Exif | None:
    """The source's EXIF read by Pillow or pillow-heif (not by ``clearwater.io.photo``)."""
    if source_format == "heic":
        raw = pillow_heif.open_heif(str(path)).info.get("exif")
    else:
        with PILImage.open(path) as image:
            raw = image.info.get("exif")
    if not raw:
        return None
    exif = PILImage.Exif()
    exif.load(raw)
    return exif


# --- running exports ----------------------------------------------------------------------------


def export(
    sources: list[Path],
    out: Path | None,
    *,
    parameters: ParameterSet | None = None,
    exports: Any = None,
    progress: he.RunnerProgress | None = None,
    **settings: Any,
) -> list[BatchItem]:
    """Export through the runner's library API on the CPU; return the batch items."""
    chosen = Settings(output_folder=out, force_cpu=True, **settings)
    requests = he.requests_for(
        sources, parameters=parameters or he.parameters_for(), settings=chosen
    )
    record = he.run(requests, exports=exports, progress=progress, footage_folder=None)
    return list(record.report.items)


def only_output(items: list[BatchItem]) -> Path:
    """The single output of a one-item batch that must be done."""
    (item,) = items
    assert item.result is not None and item.result.ok, item.result and item.result.failure
    (output,) = item.result.outputs
    return output


def upright(scene: str) -> np.ndarray:
    """The upright image an orientation fixture was made from (WP2.3, ``spike_io``)."""
    width, height = 96, 64
    if scene == "landscape":
        return spike.upright_image(8, width, height).astype(np.float64)
    return spike.upright_image(8, height, width).astype(np.float64)


class DropIccp(PhotoWriter):
    """Planted writer double: writes as the product does, then removes the ``iCCP`` chunk."""

    def write(self, image, meta, out_path, *, bit_depth, provenance) -> None:
        super().write(image, meta, out_path, bit_depth=bit_depth, provenance=provenance)
        data = Path(out_path).read_bytes()
        kept, at = [data[:8]], 8
        while at < len(data):
            length = int.from_bytes(data[at : at + 4], "big")
            if data[at + 4 : at + 8] != b"iCCP":
                kept.append(data[at : at + 12 + length])
            at += 12 + length
        Path(out_path).write_bytes(b"".join(kept))


class Recording(PhotoWriter):
    """A writer that keeps a copy of the host pixels it is asked to write (pre-encode)."""

    def __init__(self) -> None:
        super().__init__()
        self.pixels: list[np.ndarray] = []

    def write(self, image, meta, out_path, *, bit_depth, provenance) -> None:
        self.pixels.append(np.array(image.pixels, dtype=np.float32, copy=True))
        super().write(image, meta, out_path, bit_depth=bit_depth, provenance=provenance)


# --- V5 -----------------------------------------------------------------------------------------


def assert_v5_icc(output: Path, sample_id: str, source: Path) -> None:
    """``iCCP``: the source's profile bytes, the D53 built-in for a tagged HEIC, else none."""
    facts = ENTRIES[sample_id]["facts"]
    got = icc_of(output)
    if facts.get("icc_md5"):
        assert got is not None, f"iCCP missing: {sample_id} carries an ICC profile"
        assert hashlib.md5(got).hexdigest() == facts["icc_md5"], f"iCCP differs: {sample_id}"
        return
    if sample_id in BUILT_IN_SRGB_IDS:
        assert got is not None, f"iCCP missing: {sample_id} gets the D53 built-in sRGB"
        assert hashlib.md5(got).hexdigest() == SRGB_BUILT_IN_MD5, f"not the built-in: {sample_id}"
    else:
        assert got is None, f"iCCP present for an untagged source: {sample_id}"


def assert_v5_exif(output: Path, sample_id: str, source: Path) -> None:
    """EXIF per D63: Orientation 1, no thumbnail, dimensions updated, Software, the rest kept."""
    entry = ENTRIES[sample_id]
    out = exif_of(output)
    assert out is not None, f"eXIf missing: {sample_id}"
    width, height = (int(v) for v in PILImage.open(output).size)
    assert out.get(ORIENTATION) == 1, sample_id
    assert str(out.get(SOFTWARE)).rstrip("\0") == "Clearwater", sample_id
    sub = out.get_ifd(ExifTags.IFD.Exif)
    assert (sub.get(PIXEL_X), sub.get(PIXEL_Y)) == (width, height), sample_id
    assert not out.get_ifd(ExifTags.IFD.IFD1), f"thumbnail kept: {sample_id}"
    fmt = entry["expect"]["photo"]["metadata"]["source_format"]
    src = source_exif(source, fmt) if entry["expect"]["photo"]["metadata"]["exif"] else None
    if src is None:
        assert set(out) - POINTERS == {ORIENTATION, SOFTWARE}, sample_id
        assert set(sub) == {PIXEL_X, PIXEL_Y}, sample_id
        return
    assert_exif_kept(out, src, sample_id)


def interop_of(exif: PILImage.Exif) -> dict[int, Any]:
    """The Interop IFD under the Exif IFD, or an empty one when there is no pointer."""
    if int(ExifTags.IFD.Interop) not in exif.get_ifd(ExifTags.IFD.Exif):
        return {}
    return dict(exif.get_ifd(ExifTags.IFD.Interop))


def assert_exif_kept(out: PILImage.Exif, src: PILImage.Exif, label: str) -> None:
    """D63: every source field but those the export rewrites is kept (IFD0, Exif, GPS, Interop)."""
    sub = out.get_ifd(ExifTags.IFD.Exif)
    for tag, value in src.items():
        if tag not in POINTERS | {ORIENTATION, SOFTWARE}:
            assert out.get(tag) == value, f"IFD0 tag {tag} changed: {label}"
    for tag, value in src.get_ifd(ExifTags.IFD.Exif).items():
        if tag not in POINTERS | {PIXEL_X, PIXEL_Y}:
            assert sub.get(tag) == value, f"Exif tag {tag} changed: {label}"
    assert out.get_ifd(ExifTags.IFD.GPSInfo) == src.get_ifd(ExifTags.IFD.GPSInfo), label
    assert interop_of(out) == interop_of(src), f"Interop IFD changed: {label}"


@pytest.mark.parametrize("sample_id", STILL_IDS)
def test_v5_bit_depth_icc_exif_and_provenance(sample, tmp_path: Path, sample_id: str) -> None:
    source = sample(sample_id)
    for depth in (8, 16):
        out = tmp_path / f"d{depth}"
        out.mkdir()
        output = only_output(export([source], out, png_bit_depth=depth))
        assert bit_depth(output) == depth, sample_id  # D22
        assert_v5_icc(output, sample_id, source)
        assert_v5_exif(output, sample_id, source)
        provenance = provenance_of(output)  # D91, on by default
        assert provenance is not None and provenance["method"] == "c3"
        assert provenance["source"]["name"] == source.name
        assert provenance["settings"]["png_bit_depth"] == depth
    off = tmp_path / "off"
    off.mkdir()
    assert provenance_of(only_output(export([source], off, provenance=False))) is None


@pytest.mark.parametrize("sample_id", ["png16-gradient-display-p3", "jpeg-lowred-srgb"])
def test_v5_planted_writer_dropping_iccp_fails_by_name(sample, tmp_path, sample_id) -> None:
    source = sample(sample_id)
    exports = composition.export_jobs(writer=DropIccp())
    output = only_output(export([source], tmp_path, exports=exports))
    with pytest.raises(AssertionError, match="iCCP missing"):
        assert_v5_icc(output, sample_id, source)


def test_v5_an_interop_ifd_is_kept_and_a_dropped_one_fails_by_name(tmp_path: Path) -> None:
    # No WP2.3 still carries an Interop IFD, so this test-built JPEG gives the D63 leg one.
    exif = PILImage.Exif()
    exif[int(ExifTags.Base.Make)] = "TestMake"
    sub = exif.get_ifd(ExifTags.IFD.Exif)
    sub[int(ExifTags.Base.ExposureTime)] = 0.01
    sub[int(ExifTags.IFD.Interop)] = {1: "R98", 2: b"0100"}
    source = tmp_path / "interop.jpg"
    pixels = (np.arange(32 * 48 * 3) % 251).astype(np.uint8).reshape(32, 48, 3)
    PILImage.fromarray(pixels).save(source, exif=exif.tobytes(), quality=95)
    src = source_exif(source, "jpeg")
    assert src is not None and interop_of(src) == {1: "R98", 2: b"0100"}
    out = tmp_path / "out"
    out.mkdir()
    written = exif_of(only_output(export([source], out)))
    assert written is not None
    assert_exif_kept(written, src, "interop.jpg")
    del written.get_ifd(ExifTags.IFD.Exif)[int(ExifTags.IFD.Interop)]  # planted: Interop dropped
    with pytest.raises(AssertionError, match="Interop IFD changed"):
        assert_exif_kept(written, src, "interop.jpg")


@pytest.mark.parametrize("sample_id", ORIENT_IDS)
def test_v5_jpeg_orientation_matches_pillows_own_decode(sample, tmp_path, sample_id) -> None:
    source = sample(sample_id)
    output = only_output(export([source], tmp_path, parameters=he.parameters_for(neutral=True),
                                png_bit_depth=8))  # fmt: skip
    with PILImage.open(source) as image:
        expected = np.asarray(ImageOps.exif_transpose(image).convert("RGB"), dtype=np.float64)
        stored = np.asarray(image.convert("RGB"), dtype=np.float64)
    with PILImage.open(output) as image:
        got = np.asarray(image.convert("RGB"), dtype=np.float64)
    assert got.shape == expected.shape, sample_id
    assert float(np.abs(got - expected).max()) <= 3.0, sample_id
    assert float(np.abs(got - upright(ENTRIES[sample_id]["facts"]["scene"])).mean()) < 3.0
    if ENTRIES[sample_id]["facts"]["exif_orientation"] != 1:  # planted: the unrotated decode
        assert got.shape != stored.shape or float(np.abs(got - stored).mean()) > 10.0


@pytest.mark.parametrize("sample_id", AD24_IDS)
def test_v5_heic_orientation_follows_ad24(sample, tmp_path, sample_id) -> None:
    output = only_output(
        export([sample(sample_id)], tmp_path, parameters=he.parameters_for(neutral=True),
               png_bit_depth=8)
    )  # fmt: skip
    with PILImage.open(output) as image:
        got = np.asarray(image.convert("RGB"), dtype=np.float64)
    reference = upright("landscape")
    assert got.shape == reference.shape, sample_id
    assert float(np.abs(got - reference).mean()) < 6.0, f"{sample_id} is not upright"
    for k in range(2, 9):  # every other pose is told apart (the check can fail)
        other = spike.apply_orientation(reference, k)
        if other.shape == reference.shape:
            assert float(np.abs(got - other).mean()) > 10.0, (sample_id, k)


# --- V9 -----------------------------------------------------------------------------------------


def v9_difference(source: Path, output: Path, depth: int) -> tuple[float, float, float, float]:
    """V9 figures in 1/255 units: against the source quantised to ``depth``, then unquantised.

    The quantised reference uses the writer's own rounding rule (``io.photo.png._quantise``:
    clip, round half to even), so the neutral identity shows 0/0 (CHARC S8 ruling, condition 1).
    """
    original, _ = PhotoReader().read(source)
    written, _ = PhotoReader().read(output)
    pixels = original.pixels.astype(np.float64)
    reference = png_tools._quantise(original.pixels, depth).astype(np.float64) / (2**depth - 1)
    quantised = np.abs(reference - written.pixels) * 255
    raw = np.abs(pixels - written.pixels) * 255
    return float(quantised.max()), float(quantised.mean()), float(raw.max()), float(raw.mean())


@pytest.mark.parametrize("method_id", ["c3", "ancuti2018"])
@pytest.mark.parametrize("sample_id", STILL_IDS)
def test_v9_neutral_is_the_identity(
    sample, tmp_path, record_property, sample_id: str, method_id: str
) -> None:
    source = sample(sample_id)
    original, _ = PhotoReader().read(source)
    params = he.parameters_for(method_id, neutral=True)
    for depth in (8, 16):
        out = tmp_path / f"d{depth}"
        out.mkdir()
        output = only_output(export([source], out, parameters=params, png_bit_depth=depth))
        q_max, q_mean, raw_max, raw_mean = v9_difference(source, output, depth)
        record_property(f"v9-raw-{depth}", {"max_255": raw_max, "mean_255": raw_mean})
        assert q_max <= 2.0 and q_mean <= 0.2, (sample_id, depth, q_max, q_mean)  # AD-11
        if depth == 16 or original.color.bit_depth == 8:
            assert raw_max <= 2.0 and raw_mean <= 0.2, (sample_id, depth, raw_max, raw_mean)
        written, _ = PhotoReader().read(output)
        tags = ("primaries", "transfer", "matrix", "range")
        assert [getattr(written.color, t) for t in tags] == [
            getattr(original.color, t) for t in tags
        ]
        if sample_id in BUILT_IN_SRGB_IDS:
            assert original.color.icc_profile is None, sample_id
            got = written.color.icc_profile or b""
            assert hashlib.md5(got).hexdigest() == SRGB_BUILT_IN_MD5, sample_id
        else:
            assert written.color.icc_profile == original.color.icc_profile, sample_id


@pytest.mark.parametrize("sample_id", ["jpeg-gradient-srgb", "png16-lowred-display-p3"])
def test_v9_planted_control_off_neutral_misses_the_bound(sample, tmp_path, sample_id) -> None:
    source = sample(sample_id)
    neutral = he.parameters_for(neutral=True)
    method = composition.correction_methods()["c3"]
    # gamma alone off neutral (its default 1.5): a strength at its default changes nothing while
    # the stage it scales is neutral, so it would not be a control.
    off = next(p for p in method.parameters if p.name == "gamma")
    assert off.neutral != off.default
    params = new_parameter_set("c3", {**neutral.parameters, off.name: off.default})
    output = only_output(export([source], tmp_path, parameters=params, png_bit_depth=16))
    q_max, q_mean, _, _ = v9_difference(source, output, 16)
    assert q_max > 2.0 or q_mean > 0.2, (off.name, q_max, q_mean)


# --- V10 ----------------------------------------------------------------------------------------


def _fingerprint(folder: Path) -> dict[str, tuple[str, int]]:
    return {
        p.name: (hashlib.md5(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
        for p in sorted(folder.iterdir())
    }


@pytest.fixture
def clash(sample, tmp_path: Path) -> Path:
    """A source folder holding ``IMG_1234.HEIC`` and ``IMG_1234.JPG`` (D84)."""
    folder = tmp_path / "src"
    folder.mkdir()
    shutil.copyfile(sample("heic8-gradient-srgb"), folder / "IMG_1234.HEIC")
    shutil.copyfile(sample("jpeg-gradient-srgb"), folder / "IMG_1234.JPG")
    return folder


@pytest.mark.parametrize("beside", [True, False], ids=["beside-source", "output-folder"])
def test_v10_cross_format_clash_is_numbered(clash: Path, tmp_path: Path, beside: bool) -> None:
    sources = [clash / "IMG_1234.HEIC", clash / "IMG_1234.JPG"]
    before = _fingerprint(clash)
    target = clash if beside else tmp_path / "out"
    target.mkdir(exist_ok=True)
    items = export(sources, None if beside else target)
    assert [item.state for item in items] == ["done", "done"]
    assert [p.name for item in items for p in item.result.outputs] == [
        "IMG_1234_corrected.png",
        "IMG_1234_corrected_2.png",
    ]
    assert all(p.parent == target for item in items for p in item.result.outputs)
    after = _fingerprint(clash)
    assert {k: after[k] for k in before} == before  # N8: sources untouched


def test_v10_an_existing_output_is_never_overwritten(clash: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    existing = out / "IMG_1234_corrected.png"
    existing.write_bytes(b"an earlier export")
    os.utime(existing, ns=(1_600_000_000_000_000_000, 1_600_000_000_000_000_000))
    before = _fingerprint(out)
    items = export([clash / "IMG_1234.JPG"], out)
    assert [p.name for p in items[0].result.outputs] == ["IMG_1234_corrected_2.png"]  # D35
    assert _fingerprint(out)["IMG_1234_corrected.png"] == before["IMG_1234_corrected.png"]


def test_v10_custom_suffix(clash: Path, tmp_path: Path) -> None:
    items = export([clash / "IMG_1234.JPG", clash / "IMG_1234.HEIC"], None, output_suffix="-wet")
    assert [p.name for item in items for p in item.result.outputs] == [
        "IMG_1234-wet.png",
        "IMG_1234-wet_2.png",
    ]  # D36


def test_v10_dng_and_sidecar_fail_and_the_batch_continues(sample, clash, tmp_path) -> None:
    shutil.copyfile(sample("dng-by-extension"), clash / "RAW_0001.DNG")
    shutil.copyfile(sample("dng-by-tag"), clash / "RAW_0002.tif")
    (clash / "GX010001.THM").write_bytes(b"\xff\xd8 a thumbnail")
    before = _fingerprint(clash)
    sources = [clash / n for n in ("RAW_0001.DNG", "GX010001.THM", "RAW_0002.tif", "IMG_1234.JPG")]
    out = tmp_path / "out"
    out.mkdir()
    items = export(sources, out)
    assert [item.state for item in items] == ["failed", "failed", "failed", "done"]  # D81
    for item in (items[0], items[2]):  # D116
        assert "ProRAW and DNG files are not read in this version" in item.result.failure
    assert items[1].result.failure == he.route(clash / "GX010001.THM")  # D83
    assert "camera proxy or thumbnail file" in items[1].result.failure
    assert sorted(p.name for p in out.iterdir()) == ["IMG_1234_corrected.png"]
    assert _fingerprint(clash) == before  # N8


def test_v10_a_cancel_after_item_1_keeps_it_and_runs_no_later_item(clash, tmp_path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    progress = he.RunnerProgress()

    def hook(stage: str) -> None:
        if stage == "committed":
            progress.cancel()

    items = export(
        [clash / "IMG_1234.JPG", clash / "IMG_1234.HEIC"],
        out,
        exports=composition.export_jobs(on_stage=hook),
        progress=progress,
    )
    assert [item.state for item in items] == ["done", "not run"]  # D45, G8
    assert sorted(p.name for p in out.iterdir()) == ["IMG_1234_corrected.png"]


# --- N10 ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("sample_id", ["jpeg-gradient-srgb", "heic10-lowred-display-p3"])
def test_n10_the_same_still_twice_is_identical(sample, tmp_path, sample_id) -> None:
    source = sample(sample_id)
    outputs: dict[bool, list[Path]] = {True: [], False: []}
    recording = Recording()  # the writer's incoming pixels, pre-encode (Reviewer B B7)
    for provenance in (False, True):
        for run in range(2):
            out = tmp_path / f"p{int(provenance)}-{run}"
            out.mkdir()
            exports = composition.export_jobs(writer=recording)
            items = export([source], out, exports=exports, provenance=provenance)
            outputs[provenance].append(only_output(items))
    assert len(recording.pixels) == 4
    assert all(
        (recording.pixels[0].dtype, recording.pixels[0].shape, recording.pixels[0].tobytes())
        == (p.dtype, p.shape, p.tobytes())
        for p in recording.pixels[1:]
    )  # pre-encode
    first, second = outputs[False]
    assert first.read_bytes() == second.read_bytes()  # provenance off: byte-identical
    a, b = (png_chunks(p) for p in outputs[True])
    key = PROVENANCE_KEYWORD.encode("latin-1") + b"\0"  # the whole keyword, never a prefix
    plain = [c for c in a if not (c[0] == b"iTXt" and c[1].startswith(key))]
    assert plain == [c for c in b if not (c[0] == b"iTXt" and c[1].startswith(key))]
    assert len(plain) == len(a) - 1  # exactly the provenance chunk was set aside
    pa, pb = (provenance_of(p) for p in outputs[True])
    assert pa is not None and pb is not None
    assert {k: v for k, v in pa.items() if k != "created"} == {
        k: v for k, v in pb.items() if k != "created"
    }
    pixels = [PhotoReader().read(p)[0].pixels for p in outputs[False] + outputs[True]]
    assert all(
        (pixels[0].dtype, pixels[0].shape, pixels[0].tobytes()) == (p.dtype, p.shape, p.tobytes())
        for p in pixels[1:]
    )  # decoded bit-identical


# --- CPU vs GPU ---------------------------------------------------------------------------------


@pytest.mark.gpu
def test_gpu_export_reports_gpu_and_matches_the_cpu(sample, tmp_path: Path) -> None:
    pytest.importorskip("cupy")
    _, reason = core.select_backend(Settings(), 64, 96, "c3")
    if reason != "GPU":
        pytest.skip(f"no usable CUDA device: {reason}")
    source = sample("jpeg-gradient-srgb")
    recorded = {}
    for name, force in (("cpu", True), ("gpu", False)):
        writer = Recording()
        out = tmp_path / name
        out.mkdir()
        requests = he.requests_for(
            [source],
            parameters=he.parameters_for(),
            settings=Settings(output_folder=out, force_cpu=force),
        )
        record = he.run(
            requests, exports=composition.export_jobs(writer=writer), footage_folder=None
        )
        (item,) = record.report.items
        assert item.result.ok, item.result.failure
        assert item.result.device == ("CPU: forced" if force else "GPU")
        recorded[name] = writer.pixels[0]
    diff = np.abs(recorded["cpu"].astype(np.float64) - recorded["gpu"])
    assert float(diff.max()) <= 2e-3 and float(diff.mean()) <= 2e-4  # AD-11 (N10/D92)
