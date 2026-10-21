# WP3.6 -- Photo input and output: report

Branch `wp3.6`, base main `4b4da9b`. Module `clearwater.io.photo` (`src/clearwater/io/photo/`),
instrument `tools/photo_check.py`, ledger `docs/proofs/wp3.6-ledger.md` (round-0 design table, rulings,
Reviewer A rounds). Spec v0.5.4; AD-11, AD-17 (amended 2026-10-20), AD-24 (PROVISIONAL), D53, D63, D91,
D116.

## Claims

1. **IF-6 satisfied exactly as frozen**: `PhotoReader.read(path) -> (Image, PhotoMetadata)` and
   `PhotoWriter.write(image, meta, out_path, *, bit_depth, provenance) -> None`; both pass
   `isinstance` against the runtime-checkable protocols. `read_photo` / `write_photo` are the same on
   default instances. `src/clearwater/interfaces/` is unchanged (`git diff main -- src/clearwater/interfaces`
   is empty).
2. **Read path** (every format returns float32 `(H, W, 3)` RGB in [0, 1], `device="cpu"`,
   `orientation_applied=True`, `matrix="identity"`, `range="full"`):

   | Format | Read path | Depth kept | Orientation |
   |---|---|---|---|
   | JPEG (and MPO, first image) | Pillow, full `load()` | 8 | EXIF tag, once |
   | PNG 8-bit and below | Pillow, full `load()`; chunks by the stdlib scanner (CRCs, `iCCP`, `eXIf`, `sRGB`) | 8 | EXIF `eXIf` tag, once |
   | PNG 16-bit | stdlib decoder (`png.py`): five filters by an anti-diagonal wavefront, colour types 0, 2, 4, 6; Adam7 refused by name | 16 | `eXIf` tag, once |
   | TIFF 8/16-bit | `tifffile` (none, Deflate, PackBits, LZMA; striped or tiled; chunky or planar; predictor 1 or 2) | 8 / 16 | IFD0 tag 274, once |
   | HEIC 8/10-bit | `pillow_heif.open_heif(convert_hdr_to_8bit=False)`; 10-bit normalised `(v >> 6) / 1023` | 8 / 10 | AD-24, below |

   HEIC (AD-24): libheif applies `irot`/`imir`; `heif_boxes.py` reads `pitm` -> `ipma` -> `ipco` for the
   primary item; the EXIF tag is applied additionally only when the primary has no `irot`; the primary's
   `ispe` (or `clap`), turned by a 90/270 `irot`, must equal the decoded size or the file is refused as
   unreadable. `PhotoMetadata.orientation` is the source tag. Auxiliary images and thumbnails are never
   read. DNG is refused before any decode (extension `.dng`, or DNGVersion 50706 in IFD0 of any classic
   TIFF-structured file); unknown formats are refused; format is detected by content.
3. **Writer**: one stdlib writer for 8 and 16 bit (`png.py`): `IHDR`, `iCCP` (source profile
   byte-identical, name the profile's own description when it obeys the PNG keyword rule else
   `ICC profile`), `eXIf`, the provenance `iTXt` (`clearwater-provenance`, UTF-8 JSON, `allow_nan=False`,
   `sorted keys`, after `check_string_keys`), `IDAT` (filter 0, deflate level 6, at most 1 MiB per chunk,
   streamed in 256-row blocks), `IEND`. Quantisation (the only one in the photo path): clip to [0, 1],
   `rint(x * (2**d - 1))` in float64, big-endian 16-bit, no dithering. The file is opened `"wb"` once and
   closed before return; a `.png` suffix (case-insensitive) is required; `ValueError` for another bit
   depth, a non-CPU image (naming the device), a non-float32 `(H, W, 3)` array, NaN or infinity.
4. **D63 EXIF** (`exif.py`, built on Pillow's `Image.Exif`):

   | Field | Result |
   |---|---|
   | IFD0 Orientation | 1 |
   | IFD1 (thumbnail) | removed |
   | Exif IFD PixelXDimension / PixelYDimension | written size |
   | IFD0 Software | `Clearwater` (the version is in the provenance chunk) |
   | every other IFD0, Exif, Interop, GPS field | kept (test: Make, Model, DateTime, DateTimeOriginal, FNumber, GPS ref) |
   | source without EXIF | minimal block: Orientation 1, dimensions, Software |
   | HEIC auxiliary images | dropped by construction (a PNG holds one image) |
5. **DR-31 (1) closes**: the full PNG keyword rule (1-79 Latin-1 bytes, none in 0-31 or 127-160, no
   leading, trailing or consecutive spaces) is one validator, `png.keyword_problem`, with a test per rule
   (`tests/test_io_photo_units.py`).

## Sample table (WP2.3 manifest `expect`, all met; `tests/test_io_photo_read.py`)

| Manifest ids | Expectation | Result |
|---|---|---|
| 54 `{png16,png8,jpeg,tiff8,heic8,heic10}-{uniform,gradient,lowred}-{none,srgb,display-p3}` | metadata, colour (matrix, range, depth, `primaries`/`transfer` where listed), ICC present and byte-identical (md5 of the manifest), `orientation_applied` | pass |
| `png16-*`, `png8-*`, `tiff8-*` (lossless) | pixels equal the quantised content exactly at their own depth; no 8-bit read of a 16-bit file | pass |
| `jpeg-orient-{land,port}-o{1,3,6,8}` | upright after the read, every other pose clearly different | pass |
| `heic-ad24-{both,exif-only,irot-only,neither}` | rotated exactly once; `PhotoMetadata.orientation` 6/6/1/1 | pass |
| `dng-by-extension`, `dng-by-tag`, `dng-extension-only` | refused, kind `unsupported`, message names the file and says DNG/ProRAW | pass |

Built under `tmp_path` (no fixture has them): 16-bit RGB TIFF (none, Deflate, predictor, tiled, planar,
ICC, Orientation 6), grey, palette and RGBA TIFF, multi-page TIFF, PackBits and LZW/JPEG/Zstd/JPEG2000
compression tags (hand-written baseline TIFF writer), interlaced 16-bit PNG (refused), `sRGB`-chunk PNG,
MPO JPEG, HEIC with alpha, 12-bit HEIC (refused), a 10-bit HEIC whose maximum code reads 1.0,
truncated JPEG, PNG, 16-bit PNG, HEIC and TIFF, a missing, empty, unknown and directory path.

## Verification and gates

- V9 I/O legs: every one of the 54+ stills, read -> write 16-bit -> read, max abs difference
  <= 0.5/65535 (AD-11 V9 asks <= 2/255 max, <= 0.2/255 mean; the tighter bound is what is asserted too);
  exact for 8- and 16-bit sources.
- Written PNGs checked by readers other than the writer: samples exact through the FFmpeg CLI
  (`rgb48be`, `rgb24`), `eXIf`/`iTXt` through Pillow, `iCCP` bytes equal to the source profile,
  chunk order and every CRC through a stdlib walker.
- Planted wrong implementations fail by name (`tests/test_io_photo_planted.py`, each also run
  un-planted): EXIF always honoured (double rotation), never honoured, `irot` from `ipco` without
  `ipma`, `ispe` unchecked, a 16-bit source read as 8, 16-bit written as 8, a stale Orientation, a kept
  thumbnail, a changed ICC byte, a trailing-space profile name, a decoder that ignores Paeth, altered
  pixel values.
- Safe-write composition (X-B1, N8): `plan_output` -> `SafeWrite` -> `PhotoWriter.write(temp_path)` ->
  `commit`; an exception inside `write` leaves no partial and no final; the source's bytes and mtime
  are unchanged.
- Dependency rule: importing `clearwater.io.photo` in a fresh interpreter loads nothing from
  `clearwater.gui/.jobs/.methods/.core`, `PySide6`, `cupy`, `av` (subprocess test), and no module names
  them (AST test).
- `uv run ruff check .`, `ruff format --check .`, `mypy` (strict) clean; photo tests 404 passed, 1
  skipped (the footage leg). Full-suite result: see the ledger's gate section (run in the
  dispatcher's window).
- 48 MP informational figures (a 8000 x 6000 16-bit RGB PNG with filters 0-4 cycling by row, built
  in scratch, not a product test; shared laptop, untimed by the hardware rule): read 10.6 s,
  process peak 1.67 GiB (result float32 549 MiB); write 11.1 s with no peak increase.

## pyproject and lock (X-B3)

Mine: in `[project] dependencies`, `pillow>=11,<13` and `pillow-heif>=0.20,<2` (moved from the `dev`
group, the same form WP3.12 uses) and `tifffile>=2025.1,<2027` (new; resolves 2026.10.15, BSD-3; it ships
type information, no mypy override). `uv.lock` was regenerated with `uv lock`; re-lock at the second
merge, never a hand merge.

## Deviations and decisions the dispatcher ruled

- ICC classification is read by a stdlib tag reader, with `ImageCms` only opening the profile (Q4 said
  "through `ImageCms`": it exposes colorants but no tone curve). Same labels.
- nclx colour data (HEIC without an ICC profile, the form of every `*-none` HEIC fixture) is read as
  equivalent colour data (6.5) with `icc_profile=None` (IF-1: the file carries none; the WP2.3
  manifest agrees). Built-in profiles (CHARC ruling `d06ed7c969d6249f`, clarified by
  `aa1219fb3145208b`, applied in the WRITER by the dispatcher's ruling): `writer.built_in_profile`
  embeds a built-in profile when the source is a HEIC with no ICC profile, `assumed` is False and
  (primaries, transfer) is Display P3 + sRGB curve (built-in Display P3, `p3_profile.py`, isolated
  commit `23fdfd9`) or BT.709 + sRGB curve (built-in sRGB, `srgb_profile.py`, its own commit); the
  writer records `"profile": "built-in <name>"` in the provenance chunk. Reverting either leg means
  removing one entry from the writer's `_BUILT_IN_PROFILES` table (the builder module may stay or go).
  A source ICC profile is copied byte-identical and provenance says nothing about a profile (a
  Clearwater PNG read back included). Each profile's bytes are pinned by md5 (Display P3
  `ee27975c71b9ed10be950a696f6fe6f4`, 620 bytes; sRGB `ca34a0279325928fc9fd3fc7eff99eb9`, 608 bytes).
  With provenance off (D91) the profile is still embedded and nothing is recorded; a caller's
  provenance that already has a `profile` key is refused (`ValueError`) when a built-in is embedded.
  Four classes are tested on the WRITTEN PNG (`tests/test_io_photo_srgb.py`): source ICC
  (byte-identical), nclx P3, nclx sRGB, and untagged JPEG/PNG/TIFF (`bt709`/`srgb`, `assumed=True`,
  question 3 as ruled) or an nclx source outside the set (BT.2020; HLG/PQ; any non-sRGB curve) -> NO
  `iCCP`, description carried; plus reader tests that nclx gives `icc_profile=None`.
- Reading of the set (accepted): only the sRGB curve gets a built-in profile, since both profiles
  carry the sRGB tone curve; nclx BT.709 primaries with the BT.709 curve (transfer codes 1 and 6) get
  no `iCCP`.
- A PNG with an `sRGB` chunk and no `iCCP` (explicit sRGB, round-0 note N-2) is also `assumed=False`
  with no ICC profile, like an nclx HEIC. Built-in profiles are for nclx sources only, so the writer's
  condition includes `meta.source_format == "heic"` (nclx exists only in HEIC) and that PNG is written
  without `iCCP`, as N-2 ruled; a test pins it.
- LZW and JPEG-in-TIFF are refused by name (no `imagecodecs`); Zstd is refused by name before decode.

## Limits

- Out of envelope as briefed: hostile files, CMYK and exotic TIFF (refused), network shares.
- A 12-bit HEIC is refused (the vocabulary has no 12-bit); HLG/PQ-tagged photos read with
  `transfer="unknown"`; alpha is dropped with a warning; multi-page TIFF reads page one with a warning.
- Orientation for a HEIC with `imir` and no `irot` follows AD-24 literally (the tag is applied when
  `irot` is absent).
- The 16-bit PNG reader holds the whole file and two decoded copies (about 1.7 GiB at 48 MP).

## Waits for real photos (WP3.6P, question 11)

Nothing in this package waits; these claims need an owner photo and `tools/photo_check.py`:
the AD-24 layout of a real iPhone HEIC (grid primary, `ipma`, tag and `irot` together; AD-24 stays
PROVISIONAL), MakerNote and GPS survival through Pillow's EXIF writer, the Display P3 classification of
Apple's own profile, the largest photo for the Result 2 photo leg and V15, and the photo look check.
The instrument writes its records under `<working>/wp3.6/photo-check/<run>/` and never writes beside a
source; its real-photo test skips while the footage folder has no photos.
