# WP3.6 -- Photo input and output: ledger

Cell: wp36-cell (implementer-sonnet-high, tier STRONG). Worktree `.worktrees/wp3.6`, branch `wp3.6`,
base main `4b4da9b`. Brief `docs/briefs/wp3.6-brief.md` (FINAL, CHARC rulings `53b752a4d7fac4fc`).

## Cumulative round ledger

| Round | Depth (dispatcher fills) | Critical / Major / Minor | In envelope vs out | NEW vs REOPENED | Reverts | Product vs test-only fixes |
|---|---|---|---|---|---|---|
| 0 (design table, no product code) | | n/a | n/a | n/a | 0 | n/a |

## Round 0: the design table (task 1)

Probes behind the table (scratch only, nothing committed): `uv run --with tifffile` in a scratch
environment (tifffile 2026.10.15 resolves; BSD-3); the WP2.3 fixtures read with `pillow_heif.open_heif`
and by a stdlib ICC tag reader; `tests/fixtures/manifest.json` `expect` blocks.

### A. Detection, DNG test, refusals (before any decode)

- **Format by content (magic bytes), not extension**: JPEG `FF D8 FF`; PNG 8-byte signature; TIFF
  `II*\0` / `MM\0*`; HEIF `ftyp` box with a major or compatible brand in {heic, heix, heim, heis, hevc,
  hevx, mif1, msf1}. Anything else: `PhotoReadError("unsupported", ...)` ("not a photo format
  Clearwater reads"). `PhotoMetadata.source_format` is the content-detected format.
- **DNG test** (D116), in this order, before any decode: (1) extension `.dng`, case-insensitive;
  (2) a TIFF-structured file whose IFD0 carries tag 50706 (DNGVersion), found by a bounded stdlib
  IFD0 walk (both byte orders; classic TIFF; a malformed IFD0 offset is "not DNG", the later
  decode then refuses it as unreadable). Message names the file and says ProRAW/DNG is not supported
  in this version. Kind `"unsupported"`.
- Missing file, directory, unreadable bytes, truncated or corrupt data: kind `"unreadable"` (spec 5.4).
  A zero-length file is `"unreadable"`.

### B. Per-format read path (all produce float32 `(H, W, 3)` RGB `[0, 1]`, `device="cpu"`, `orientation_applied=True`)

| Format | Read path | Mode / depth | Normalisation |
|---|---|---|---|
| JPEG | Pillow `Image.open`, `load()` (full decode) | `RGB` 8; `L`/`LA`/`P`/`RGBA` -> `convert("RGB")` with a warning (Q8); `CMYK`/`YCCK` -> `"unsupported"` | `u8 / 255` |
| PNG 8-bit (and 1/2/4-bit) | Pillow, `load()` | as JPEG (palette, grey, alpha converted; bit_depth reported 8) | `u8 / 255` |
| PNG 16-bit | stdlib decoder `png.py`: IHDR read first; depth 16 and not interlaced -> own decoder; interlace 1 -> `"unsupported"` naming Adam7 | colour types 2, 6 (alpha dropped), 0, 4 (grey expanded to RGB); all five filter types; every chunk CRC checked, IDAT concatenated, `IEND` required, decompressed size must equal exactly `H * (1 + W*bpp)`; trailing/short data -> `"unreadable"` | `u16 / 65535` |
| TIFF (8 and 16 bit) | `tifffile` (`pages[0].asarray()`), dtype must be uint8 or uint16 | RGB (photometric 2, chunky or planar, tiled or striped), RGBA (extra sample dropped), grey (expanded), palette (colormap applied, 16-bit map entries `>> 8`); float, uint32, CMYK/separated, YCbCr -> `"unsupported"` | `u8/255` or `u16/65535` |
| HEIC 8-bit | `pillow_heif.open_heif(path)` (`convert_hdr_to_8bit` irrelevant), `np.asarray` | `RGB` (or `RGBA`, alpha dropped, warning) | `u8 / 255` |
| HEIC 10-bit | `open_heif(path, convert_hdr_to_8bit=False)`; mode `RGB;16`, samples left-shifted 6 (probed: max 65472 = 1023 << 6) | true depth from `info["bit_depth"]` | `(u16 >> (16 - depth)) / (2**depth - 1)`, so code 1023 -> 1.0 |

**TIFF compressions** (probed in a scratch env with only `tifffile`, a random-content 16-bit RGB array
written with `imagecodecs` and read back without it, exact equality): decoded without further
packages: none, Deflate/zlib (predictor 1 or 2), PackBits, LZMA; chunky and planar; striped and tiled.
**Refused by name** (`"unsupported"`, message names the compression): **LZW** (tifffile raises
`ValueError ... requires the 'imagecodecs' package`), JPEG, Zstd (tifffile raises a bare
`ModuleNotFoundError: compression`; the reader maps it, never lets it escape), and every other
compression. See STOP-or-note N-1 about LZW.

**Full decode at read**: each reader forces the whole decode (`load()`, `asarray()`, the stdlib
inflate); Pillow `OSError`/`SyntaxError`/`ValueError`, tifffile and pillow-heif errors, `zlib.error`
and the decoder's own checks all become `PhotoReadError("unreadable", ...)`, message names the file
(DR-6 trigger). The reader checks the pixel count (from the header) against one constant (150 MP, above
D117's 48 MP and below Pillow's own 179 MP error) before decoding and refuses a larger image as
`"unsupported"`, for every format; a test covers the refusal.

### C. Orientation (D63, AD-24)

- **JPEG, PNG, TIFF**: EXIF Orientation read from the source EXIF block (JPEG `info["exif"]`, PNG
  `eXIf`, TIFF IFD0 tag 274 through tifffile); valid 1-8, applied once by one numpy function
  `apply_orientation(pixels, tag)` (the standard 8-way table: 2 flip-x, 3 rot180, 4 flip-y, 5
  transpose, 6 rot90 cw, 7 anti-transpose, 8 rot90 ccw), checked against the `jpeg-orient-*` samples.
  An out-of-range value (0, 9+) or a malformed block is treated as 1 with a warning.
  `PhotoMetadata.orientation` is the SOURCE tag (1 when absent).
- **HEIC** (AD-24, provisional): (1) libheif (inside `open_heif`) applies the primary item's
  `irot`/`imir`; (2) the raw EXIF Orientation is read from `info["exif"]`; (3) our own stdlib box
  parser (`heif_boxes.py`) reads `meta` -> `pitm` (primary item id) -> `ipma` (that item's property
  indices) -> `ipco` (the 1-based property list), collecting `irot`/`imir`/`ispe` ONLY if the primary
  item's `ipma` entry names them (an `ipco` entry on another item or on none never counts); (4) if
  the tag is not 1 and the primary item has NO `irot`, `apply_orientation(pixels, tag)` is applied
  additionally; (5) the primary item's `ispe` (width, height; for a grid the grid item's `ispe`) is
  compared with the decoded size, swapped when the primary's `irot` is 90 or 270; a mismatch is
  `"unreadable"`. The `imir`-without-`irot` case follows AD-24 literally (the tag is applied when
  `irot` is absent, imir does not count). The `heic-ad24-{both,exif-only,irot-only,neither}` samples
  are the test; `PhotoMetadata.orientation` is 6/6/1/1 per the manifest (source tag, not derived).
  A missing or unparseable `pitm`/`ipma` while pillow-heif decodes fine: `"unreadable"` (cannot
  establish the rule; an actual iPhone layout is the follow-on's evidence, AD-24 stays PROVISIONAL).
- Auxiliary images (gain map, depth, thumbnails) are never read: only `open_heif`'s primary is used,
  `info["depth_images"]`, `info["aux"]` and `info["thumbnails"]` are not touched.

### D. Colour (6.5, D53; question 3 and 4)

- The ICC profile (JPEG `info["icc_profile"]`; PNG `iCCP` inflated by us or by Pillow; TIFF tag
  34675; HEIC `info["icc_profile"]` when `icc_profile_type == "prof"`) is carried byte-identical in
  `ColorDescription.icc_profile` and never applied to pixels.
- **Classification** (`icc.py`): a small stdlib ICC reader (header 128 bytes, tag table) returns the
  `rXYZ/gXYZ/bXYZ` colorants (D50 PCS) and the `rTRC/gTRC/bTRC` curves (`curv`: count 0 identity,
  count 1 gamma, N-entry table; `para` types 0-4). Primaries: each colorant within 0.001 (absolute,
  XYZ) of the reference sRGB/BT.709 D50 colorants -> `bt709`; of Display P3 D50 colorants ->
  `display-p3`; else `unknown`. Transfer: the three curves sampled at 0.02..0.98 step 0.02 within
  0.005 (absolute) of the sRGB EOTF -> `srgb`; of BT.709 -> `bt709`; else `unknown`. Probed on the
  fixtures: sRGB profile colorants (0.43604, 0.22249, 0.01392), (0.38512, 0.71690, 0.09706),
  (0.14305, 0.06061, 0.71391) and `para` type 3 TRC; Display P3 colorants (0.51512, 0.24120,
  -0.00105), (0.29198, 0.69225, 0.04189), (0.15710, 0.06657, 0.78407) with the same sRGB `para` TRC.
  `chad` need not be undone: colorants are already D50-adapted in both v2 and v4 profiles, and the
  references are D50 values. `ImageCms.ImageCmsProfile` is used only to confirm that a profile opens
  (an invalid profile is carried, classified `unknown`, warned). **Deviation from Q4's wording**:
  Q4 says "through `ImageCms`"; `ImageCms` exposes colorants but no TRC, so the stdlib reader does
  both (one code path, one tolerance). Output is the same as Q4 specifies.
- **No ICC profile** (Q3): JPEG/PNG/TIFF -> `bt709`/`srgb`, `assumed=True`, `icc_profile=None`; output
  PNG written WITHOUT `iCCP`. A PNG with an `sRGB` chunk and no `iCCP` is explicit sRGB:
  `bt709`/`srgb`, `assumed=False`, `icc_profile=None` (note N-2). `gAMA`/`cHRM` alone are ignored
  (untagged).
- **HEIC without ICC profile** (note N-3, found by probe): the fixtures `heic8-*-none` and every
  `heic-ad24-*` carry an `nclx_profile` (primaries 1, transfer 13, full range), not an ICC profile.
  6.5 says "or equivalent color data". Rule: nclx `color_primaries` 1 -> `bt709`, 12 -> `display-p3`,
  else `unknown`; `transfer_characteristics` 13 -> `srgb`, 1/6 -> `bt709`, else `unknown`;
  `assumed=False`, `icc_profile=None`. A Display-P3 nclx-only file would then be written WITHOUT an
  `iCCP` and be read as sRGB by every viewer, which violates D53. Recommended fix: `icc.py` also holds
  a built-in Display P3 profile builder (a port of the ~50-line `display_p3_profile` of
  `tools/spike_io/photo.py`, reference reading only), used ONLY for nclx-only `display-p3` input; its
  bytes go into `ColorDescription.icc_profile` at read time so the writer needs no special case. No
  fixture has this layout (tests build one under `tmp_path`); real iPhone files carry a Display P3 ICC
  profile. If you rule against: such a file is read `display-p3` with `icc_profile=None` and the
  writer warns that no profile is embedded. Needs a ruling (STOP item 2).
- `matrix="identity"`, `range="full"`, `bit_depth` = source depth (8, 10 or 16; HEIC 12-bit and TIFF
  other depths -> `"unsupported"`, the vocabulary has no 12).
- Grey ICC profile (Q8): not carried (cannot describe RGB), warning.

### E. Byte form of `PhotoMetadata.exif`

The bare TIFF-structured EXIF block (starts `II*\0` or `MM\0*`), any `Exif\0\0` prefix stripped on
read; None when the source carries none. JPEG: `info["exif"]`; PNG: the `eXIf` chunk body; HEIC:
`info["exif"]` (prefix stripped; the 4-byte offset header is already removed by pillow-heif, verified at
build against the fixtures); TIFF: built from the source IFD0 tags with the structural tags removed
(ImageWidth, ImageLength, BitsPerSample, Compression, Photometric, FillOrder, StripOffsets,
SamplesPerPixel, RowsPerStrip, StripByteCounts, PlanarConfiguration, Predictor, ColorMap, TileWidth,
TileLength, TileOffsets, TileByteCounts, ExtraSamples, SampleFormat, SubIFDs, JPEGTables, YCbCr tags,
NewSubfileType) plus the ICC (34675), XMP (700), IPTC (33723) and Photoshop (34377) blobs, together
with the Exif and GPS IFDs; built with `PIL.Image.Exif` (Pillow opens the TIFF lazily for tags only,
never for pixels; probed: Pillow lists the structural tags in `getexif()`, so the filter is needed).

### F. D63 edit list (writer, `exif.py`), field by field

| Field | Rule |
|---|---|
| IFD0 Orientation (274) | set to 1 |
| IFD1 (embedded thumbnail) | removed (Pillow's `Exif.tobytes` writes IFD0 and sub-IFDs only; test asserts no IFD1 in the written block) |
| Exif IFD PixelXDimension (40962), PixelYDimension (40963) | set to the written width and height (after orientation; they are the pixel dimensions of the image written) |
| IFD0 Software (305) | set to the bare `Clearwater` (Q5: version lives in provenance) |
| every other IFD0, Exif IFD, Interop and GPS field | kept (values byte-for-byte as Pillow round-trips them; MakerNote kept as UNDEFINED bytes, survival on a real iPhone photo waits for the follow-on) |
| Source without EXIF | a minimal block: Orientation 1, PixelX/YDimension, Software (D63 says Software is set; the written file records Clearwater processed it). |
| HEIC auxiliary images | dropped by construction (PNG holds one image; nothing is read from them) |

### G. PNG writer (`png.py`; one writer for 8 and 16 bit, Q6)

- Chunk order: `IHDR` (colour type 2, no interlace) | `iCCP` (when the source has a profile) |
  `eXIf` | `iTXt` provenance (when `provenance` is not None) | `IDAT`... | `IEND`. All before `IDAT`
  per the PNG rules for iCCP; the spike's walker checks it.
- Streaming: rows quantised and filter-0 framed in blocks of 256 rows, fed to `zlib.compressobj`
  (level 6), IDAT chunks of at most 1 MiB with an incremental CRC; peak memory is small beside the
  image at 48 MP. Single `open(out_path, "wb")` closed before return; any error leaves a partial
  `out_path` (the caller's `SafeWrite` owns discarding it, X-B1).
- **`iCCP` profile name** (DR-31 (1)): the profile's own `desc` description if it satisfies the rule,
  else `ICC profile`; rule enforced by one validator (also applied to any name): 1-79 bytes, Latin-1
  encodable, bytes in 32-126 or 161-255 only (no control characters, no 127-160), no leading,
  trailing or consecutive spaces, a `ValueError` for a name that fails when passed explicitly.
  Compression method 0. The profile bytes are deflated, never altered.
- **Provenance** (Q5, D91): one `iTXt` (keyword `clearwater-provenance`, compression flag 0, method 0,
  empty language tag and translated keyword) holding `json.dumps(provenance, allow_nan=False,
  sort_keys=True)` as UTF-8, after `clearwater.config.check_string_keys` (a non-string key is
  refused with the `FormatError` it raises, as the brief says; test asserts the type).
- Quantisation (Q7): `np.clip(x, 0, 1)` then `np.rint(x.astype(float64) * (2**d - 1))`, big-endian for
  16 bit; any NaN (or inf) in the image -> `ValueError` before the file is opened. Exhaustive test:
  every code 0..65535 and 0..255 survives normalise -> quantise exactly.
- Refusals before opening the file (`ValueError`): `bit_depth` not 8 or 16; `image.device != "cpu"`
  naming the device (Q9; no CuPy import); pixels not float32 `(H, W, 3)`; `out_path` suffix not
  `.png` (case-insensitive).

### H. Error class (X-B2), COMMITTED here

```python
PhotoErrorKind = Literal["unsupported", "unreadable"]

class PhotoReadError(Exception):
    """A photo cannot be read: unsupported (DNG/ProRAW, CMYK, an unknown format, ...) or unreadable."""
    def __init__(self, kind: PhotoErrorKind, message: str) -> None: ...   # .kind, str(e) = message
```

In `clearwater/io/photo/errors.py`, re-exported by `clearwater.io.photo`; messages are ASCII and name
the file. "Untagged" is `ColorDescription.assumed`, not an error. The public API:
`PhotoReader` (PhotoSource), `PhotoWriter` (PhotoSink), `PhotoReadError`, `read_photo`, `write_photo`
(thin functions over default instances). Modules: `errors.py`, `reader.py`, `heif_boxes.py`,
`png.py`, `tiff.py`, `exif.py`, `icc.py`, `orientation.py`, `__init__.py`.

### I. Remaining questions answered

| Q | Answer |
|---|---|
| 2 (X-B1) | the caller opens `SafeWrite`; `io.photo` imports nothing from `clearwater.jobs`; task 7 test composes it |
| 3, 4, 5 | as D, G above |
| 6 | stdlib writer for both depths; Pillow for EXIF bytes only |
| 7 | G above |
| 8 | as the table B and D: grey/grey+alpha/palette/RGBA converted with a `logging` warning (`clearwater.io.photo`; the read API returns no log text); CMYK/other -> unsupported; multi-page TIFF reads page 1 with a warning |
| 9 | `ValueError` naming the device |
| 10 | H above |
| 11 | as ruled: WP3.6P queued; the real-photo leg of the `photo_check` test skips |
| 12 | one sentence appended to `io/__init__.py` |
| 13 | `pyproject.toml` lines mine: move `pillow>=11,<13` and `pillow-heif>=0.20,<2` from `dev` to `[project] dependencies`; add `tifffile` bounded `>=2025.1,<2027` (resolves 2026.10.15; no type info -> mypy override only if `uv run mypy` complains); `uv lock`, never a hand merge |

### J. 16-bit PNG decoder: speed note (design choice, no ruling needed)

Sub is a per-lane cumulative sum, Up is row-vectorised, but Average and Paeth depend on the left
neighbour, so a naive per-pixel loop would take minutes at 48 MP. The decoder uses an
anti-diagonal wavefront: pixels with equal `x + y` are independent, so each step is one numpy
operation set over at most `min(H, W)` pixels, with a fast path when every row is filter 0 (this
writer's own output) or filter 2. Cost is measured on a 48 MP planted PNG at build and recorded in
the report; if it is unacceptable it is raised, not hidden.

## STOP items (recommended answer first)

1. **Ship the error class now? (X-B2.)** The brief says the read-error class is "shipped at the
   round-0 yield" so WP3.16 can catch it by name; the dispatch says no product code before your
   ruling. Recommended: rule "yes" and I make the first commit exactly the `errors.py` +
   `__init__.py` export of H (a few lines, one test), which you may cherry-pick for WP3.16 at once.
   Otherwise the class ships with the reader at the end of my build.
2. **nclx-only Display P3 HEIC (D, note N-3).** Recommended: embed a built-in Display P3 profile in the
   output for such an input (a port of the spike's builder, reference only; `icc.py`). Alternative:
   no profile embedded plus a warning. Not blocking for the fixtures (none has this layout).

## Notes (default accepted unless amended; none blocks the build)

- **N-1 LZW TIFF refused.** LZW is the most common compression from other software; tifffile cannot
  decode it without `imagecodecs`, which is not granted (and a hand-written LZW decoder is excluded by
  ruling 1). Recommended: accept, refuse LZW by name with a message that tells the user to re-save
  the TIFF uncompressed or with Deflate. If the owner wants LZW, that is a dependency grant
  (`imagecodecs`, BSD-3, a ~18 MiB wheel) for CHARC.
- **N-2 PNG `sRGB` chunk** treated as explicit sRGB (assumed False), output without `iCCP`.
- **N-3 HEIC nclx** read as equivalent colour data per 6.5 (D above); the fixtures need it.
- Detection is by content, not extension (a `.jpg` that is a PNG reads as PNG). A HEIC 12-bit and
  HLG/PQ-tagged photos: 12-bit refused `unsupported`; an HLG/PQ nclx transfer is classified
  `transfer="unknown"` (the vocabulary has no value for it) and carried, not refused, because the
  spec's HLG/PQ refusal (D73) is for video.
- `ColorDescription.bit_depth` for a grey/paletted 1-4 bit source is 8 (the converted samples).
- Environment: `tifffile` is not installed in the worktree's `.venv` yet (I add it to
  `pyproject.toml` and run `uv lock` + `uv sync` as the first build step after the ruling).

## Rounds

(Reviewer A rounds are recorded here, one section per round, from round 1.)
