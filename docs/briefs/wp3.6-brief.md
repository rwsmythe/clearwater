# WP3.6 — Photo input and output (dispatch brief, FINAL)

**Status:** FINAL 2026-10-20, approved by CHARC 53b752a4d7fac4fc with rulings; base = the pre-dispatch main commit named at dispatch. Owner decisions:
none inside the package. The owner has supplied NO photos yet: AD-24 is PROVISIONAL until an
owner photo is read, and the gate report's Result 2 photo leg ("Photo size limit (Result 2) ...
PENDING photos") and the photo look check stay pending. Both wait for the named follow-on of
question 11, not for this package.
- Spec **v0.5.4**. Architecture FINAL 1.0 section 3 IF-1 and IF-6, section 6 ("Photos
  (WP3.6)"); AD-11, AD-13, AD-17, AD-18, AD-20, AD-24. Frame `docs/briefs/wp2.4-phase3-frame.md`
  (section 4 grants pillow and pillow-heif here; section 5 maps "D63 HEIC rule (AD-24)" here).
  WP2.1S report `docs/reports/wp2.1s-io-spike.md` section 8 (claim 2) and its gate erratum;
  instrument `tools/spike_io/photo.py` (`encode_png16`, `edit_exif`, `png_chunks`) as reference
  reading. WP3.13 report `docs/reports/wp3.13-naming-safe-writing.md` "Consumer notes".
- Cell: `implementer-sonnet-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.6`, branch `wp3.6`, base = the main commit named at dispatch.

**Why.** Every photo enters and leaves Clearwater through this package: architecture section 2,
"photo: io.photo.read -> Image (IF-1, float32 RGB [0,1], profile kept) -> ... -> io.photo.write
(PNG16 + ICC + EXIF)". The photo path end to end (WP4.1, plan "Depends on WP3.4, WP3.6, WP3.13,
WP3.14, WP3.15") and the shell's G10 messages for photos (WP3.16) need it. WP2.1S found that
AD-17's Pillow path cannot write a 16-bit RGB PNG and closed the writer as a stdlib chunk writer.

| Field | Content |
|---|---|
| ID and title | WP3.6 — Photo input and output; plan section 6 Phase 3 row WP3.6 (size M); module `clearwater.io.photo` (plan 8.1: "Photo read and write, profiles, EXIF") |
| Goal | A reader that turns a HEIC, JPEG, PNG or TIFF file into an IF-1 `Image` and IF-6 `PhotoMetadata`, with the colour profile honoured and the orientation applied to the pixels, and that refuses ProRAW/DNG with a clear message; and a writer that writes an 8- or 16-bit PNG with the matching ICC profile, EXIF per D63 and provenance. |
| Spec / decision clauses | 5.1 table: HEIC "iPhone default; requires a HEIC-capable reader. Auxiliary images (gain map, depth) ignored"; JPEG; PNG "8- and 16-bit"; TIFF "8- and 16-bit"; "Embedded color profiles are honored (Section 6.5)."; "Orientation metadata is applied by rotating pixels on load (Section 8.1)."; "ProRAW and DNG files are refused with a clear message in v1 (D116)." 6.4 "All processing in 32-bit floating point, normalized to [0, 1]; quantization only at export." 6.5 Photos: "embedded ICC profiles (or equivalent color data) are read. Source primaries are kept end to end; Display P3 sources stay Display P3. The PNG output embeds a matching ICC profile (D53)." 8.1 "**Format:** PNG, user-selectable 8-bit or 16-bit, with an embedded ICC profile matching the source primaries."; "**Metadata:** all EXIF preserved except fields made invalid by processing (D63): pixels are physically rotated per the source orientation, and the Orientation tag is set to normal; the embedded thumbnail is removed; pixel dimensions are updated; Software is set to Clearwater; HEIC auxiliary images (HDR gain map, depth map) are dropped."; "**Provenance:** Clearwater version and parameters embedded in metadata; on by default, can be turned off (D91)." D22 "Photo output: PNG, user-selectable 8-bit or 16-bit"; D24 "*(amended by D63)* EXIF metadata preserved, except fields made invalid by processing"; D53 "Photos keep source primaries end to end (e.g., Display P3); matching ICC profile embedded in PNG output"; D63 "Photo orientation: pixels rotated, Orientation tag reset; thumbnail dropped, dimensions updated, Software set, HEIC gain/depth maps dropped. HEIC rule (0.5.4, AD-24, provisional until an owner photo is read): the file's `irot`/`imir` transforms are applied by the reader; the EXIF Orientation tag is applied additionally only when no `irot` transform is present"; D91 "Clearwater version and parameters embedded in output metadata; on by default, can be turned off"; D116 "ProRAW/DNG input deferred to a later version; refused with a clear message in v1". N8 "source files never modified". Feeds V5 "EXIF preserved except D63 fields; orientation correct for rotated and portrait sources in multiple viewers; ICC profile present and matching; selected bit depth honored", V6 "ProRAW/DNG refused with a clear message", V9 (photos: the read and write legs of "the full decode → process → encode path, including color tags and ICC handling"; AD-11 V9 "max abs diff ≤ 2/255, mean ≤ 0.2/255"). AD-17 (closed by WP2.1S: stdlib `IHDR/iCCP/eXIf/IDAT/IEND` writer fed EXIF bytes from Pillow's `Image.Exif`; "10-bit HEIC arrives as 16-bit samples (`RGB;16`, left-shifted 6)"; "ProRAW/DNG refused by extension and by the DNG tag (D116)"); AD-24 (HEIC rule, PROVISIONAL); AD-13 (the provenance object: "the same object plus `source` and `settings`"). DR-31 (1) closes here ("WP3 photo writer (D53, 8.1): enforce the full PNG keyword rule if the stdlib writer is adopted"). DR-33 (c) is covered independently ("WP3.6 ... tests its own `irot`/EXIF reading against these samples"). DR-6's trigger applies ("any package that reads photo pixels (it must validate the file itself)"). |
| Depends on | WP2.2 merged (IF-1, IF-6 frozen). WP2.3 merged: stills (group "stills") manifest ids `<prefix>-{uniform,gradient,lowred}-{none,srgb,display-p3}` for each prefix `png16`, `png8`, `jpeg`, `tiff8`, `heic8`, `heic10` (54 ids), `jpeg-orient-{land,port}-o{1,3,6,8}`, `heic-ad24-both`, `heic-ad24-exif-only`, `heic-ad24-irot-only`, `heic-ad24-neither`; files group `dng-by-extension`, `dng-by-tag` (a `.tif` with DNGVersion 50706), `dng-extension-only`; each entry's `expect.photo` / `expect.refusal` is the expected value. The manifest's `omitted` list records no 16-bit TIFF (`tests/fixtures/manifest.json` line 6114, `omitted[0].reason`, also `tools/fixtures/stills.py` line 77: "Pillow 12.3.0 cannot write a 16-bit-per-channel RGB TIFF"), and no fixture carries GPS, an EXIF thumbnail (IFD1) or a HEIC auxiliary image: tests build those under `tmp_path`. WP3.13 merged (`clearwater.jobs.SafeWrite`, used by tests only, question 2). No stub needed: nothing this package calls is unmerged. |
| Files owned | `src/clearwater/io/photo/` (NEW: `__init__.py`, and modules the round-0 table names, for example `reader.py`, `heif_boxes.py` (the `pitm`/`ipma`/`ipco` reader for AD-24), `png.py` (the stdlib PNG writer and the 16-bit PNG reader), `tiff.py` (the `tifffile` read, ruling 1), `exif.py` (the D63 edit), `icc.py`); `tests/test_io_photo_*.py` (NEW); `docs/reports/wp3.6-photo-io.md`; `docs/proofs/wp3.6-ledger.md`. X1-style owned outside the module path: `tools/photo_check.py` (the follow-on instrument, task 8). `pyproject.toml`: ONLY the frame section 4 grant (move `pillow` and `pillow-heif` from the `dev` group to `[project] dependencies`; question 13), `tifffile` added to `[project] dependencies` (ruling 1; AD-17, AD-18 amended 2026-10-20; a bounded range from the locked version; a mypy override only if it ships no type information), and `uv.lock` as `uv lock` regenerates it. Possibly one sentence in `src/clearwater/io/__init__.py` (question 12). NOT owned: `src/clearwater/interfaces/`, `src/clearwater/io/video/`, `tools/spike_io/` and `tools/fixtures/` (reference reading; `src/` never imports `tools/`), `tests/conftest.py`, `tests/fixture_plugin.py`, `tests/fixtures/`. |
| Interfaces provided | IF-6: a class satisfying `clearwater.interfaces.photo.PhotoSource` (`read(path) -> tuple[Image, PhotoMetadata]`) and one satisfying `PhotoSink` (`write(image, meta, out_path, *, bit_depth, provenance) -> None`), exactly as frozen. Outside the IFs: the read-error class of question 10 (`PhotoReadError` with a `kind` and a user-readable message, mirroring `clearwater.io.video.VideoProbeError`), shipped at the round-0 yield (X-B2). |
| Interfaces consumed | IF-1 `Image` (`pixels` float32 `(H, W, 3)` RGB `[0, 1]`, `device`, `color`, `orientation_applied`) and `ColorDescription` (vocabulary: primaries `bt709`/`display-p3`/`unknown`, transfer `bt709`/`srgb`/`unknown`, matrix `identity` for photos, range `full`, `bit_depth` 8/10/16, `assumed`, `icc_profile`); IF-6 `PhotoMetadata` (`source_format` `"heic"`/`"jpeg"`/`"png"`/`"tiff"`, `exif: bytes | None`, `orientation` 1-8, the SOURCE tag). Pillow 12.3 (`Image`, `ImageOps`, `Image.Exif`, `ImageCms`), pillow-heif 1.8.1 (`open_heif`, the Pillow opener), `tifffile` (TIFF at every depth, ruling 1), stdlib `zlib`/`struct`. Optionally `clearwater.config.check_string_keys` on the provenance object before embedding (DR-32's helper, WP3.15). |
| Wave-2 consumers | WP3.16 (shell, wave 2) opens photos through IF-6 and shows G10 messages; it builds against `stubs.StubPhotoSource` and catches the read-error class of X-B2 by name. Phase 4: WP4.1 (the photo path end to end), WP3.14 (photo export: it plans the name, opens `SafeWrite` and hands `temp_path` to `PhotoSink.write`). WP5.1 checks V5 and D91. Stubs until this merges: `stubs.StubPhotoSource(photos)` (raises `FileNotFoundError` for an unknown path) and `stubs.StubPhotoSink()` (records `out_path`). |
| Hardware flags | None timed; no `gpu`. `footage` only on the optional real-photo leg of `tools/photo_check.py`'s test (skips when the footage folder or any photo in it is absent). The footage folder is read only, never written. |
| Out of scope | ProRAW/DNG decoding (refused, D116); any correction or array work beyond the [0, 1] normalisation and the final quantisation; choosing the output name or folder and the temporary/rename sequence (WP3.13 and the caller, question 2); the photo statistics basis for preview and export (WP3.16 question 5, WP4.1); video; colour-space conversion of pixel values (the profile is carried, never applied; 6.5 "Source primaries are kept end to end"); the visual "multiple viewers" leg of V5 (WP5.1); sidecar files; any write to the footage folder or beside the source; reading GoPro data; the real-photo verification itself (the follow-on of question 11). |
| Debt and decided items | AD-24 (HEIC orientation rule, "PROVISIONAL until an owner photo is read") -- IMPLEMENTS -- as written in decisions.md; stays PROVISIONAL; reopened only by the WP3.6P follow-on (question 11) on an owner photo. DR-33 (c) ("AD-24 `irot` presence is read from `ipco` without its `ipma` association to the primary item, and `stored_width`/`stored_height` are not checked against `ispe`") -- PARTLY (covers it for the product) -- the entry itself says "WP3.6 ... tests its own `irot`/EXIF reading against these samples, which covers (c) independently": task 3 reads `irot`/`imir` through `pitm` → `ipma` → `ipco` and checks the primary item's `ispe`; the entry stays OPEN for the fixture generator and `tests/test_fixtures.py` (not owned). DR-31 (1) ("enforce the full PNG keyword rule if the stdlib writer is adopted") -- CLOSES -- task 5, a test per rule. DR-6 ("A truncated JPEG/HEIC with an intact header is inventoried as a success row"; trigger "any package that reads photo pixels (it must validate the file itself)") -- PARTLY (meets the trigger) -- the full decode at read refuses such a file (task 2, tested); the entry concerns `tools/inventory.py` and stays OPEN. DR-7 ("HEIC `orientation` column is the EXIF value, not derived from the container `irot`; Apple files carry both and agree"; trigger "A non-Apple HEIC in the footage") -- must not reopen -- it is the inventory tool's column; the product never takes HEIC orientation from the EXIF tag where an `irot` is present (AD-24), so the inventory's simplification is not inherited; a non-Apple HEIC is the follow-on's case. DR-11 ("The prototype's input reader (Pillow 12.3) reads 16-bit RGB at 8-bit precision") -- must not reopen -- the prototype is read-only reference and keeps the entry OPEN; the product keeps 16-bit and 10-bit precision (ruling 1) and a planted 8-bit read fails by name. AD-17 as amended 2026-10-20 ("16-bit PNG is read by a stdlib decoder in `io.photo` ... non-interlaced only, interlaced refused by name ... TIFF at every depth by `tifffile`") -- IMPLEMENTS -- task 2. AD-11 (V9: "max abs diff ≤ 2/255, mean ≤ 0.2/255") -- IMPLEMENTS -- the only tolerance used; none looser (frame rule 4). DR-32, DR-35 -- must not reopen -- `config` and `jobs` are consumed, not changed. |
| Done | Plan 4.5; frame section 2 rules 1-11 apply; ruff check, ruff format --check, mypy strict, full pytest green (in a dispatcher window); every expectation of the WP2.3 photo samples met; V5's machine-checkable parts, V6's DNG part and V9's I/O legs shown by named tests; DR-31 (1) closed; the follow-on instrument committed; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: the design table.** Before product code, write in the ledger:
   - per format, the read path (library call, image mode, bit depth, normalisation to [0, 1]);
   - per format, how the orientation is found and applied, and the AD-24 sequence for HEIC
     with the `ipma` association to the primary item;
   - the ICC handling and the `primaries`/`transfer` classification (question 4);
   - the byte form of `PhotoMetadata.exif` (recommended: the TIFF-structured block as an
     `eXIf` chunk holds it, any `Exif\0\0` prefix stripped on read);
   - the D63 edit list field by field;
   - the PNG chunk order, the `iCCP` profile-name rule (DR-31 (1)) and the provenance chunk
     (question 5);
   - the DNG test (extension `.dng` case-insensitive, or DNGVersion tag 50706 in IFD0 of any
     TIFF-structured file);
   - the error class and its kinds (question 10), COMMITTED at this yield (X-B2);
   - the answers to the other open questions.

   YIELD for the dispatcher. Anything the table cannot settle is a STOP.
2. **Reader (5.1, 6.4, 6.5).**
   - HEIC through pillow-heif, 8- and 10-bit; 10-bit read without the 8-bit conversion
     (`convert_hdr_to_8bit=False`, AD-17) and normalised by its true depth (question 1);
     auxiliary images (gain map, depth) never read.
   - JPEG and 8-bit PNG through Pillow. 16-bit PNG through the stdlib decoder in `io.photo`
     (the writer's counterpart), NON-INTERLACED only: an interlaced (Adam7) PNG is refused by
     name as unsupported (ruling 1). TIFF at every depth through `tifffile` (ruling 1); the
     compressions it decodes without further packages are listed in the round-0 table, and any
     other is refused by name (no `imagecodecs`, no hand-written TIFF reader). Pillow 12.3
     reads 16-bit PNG and TIFF as 8-bit (DR-11 records the PNG case; a scratch check at
     drafting time showed the same for an uncompressed 16-bit RGB TIFF, max 237 where 60836 was
     written), so Pillow is never used for either.
   - The full image is decoded at read time, so a truncated or corrupt file is refused as
     unreadable, not returned half-decoded (spec 5.4 "Files that cannot be read at all are
     refused with a clear message"; DR-6's trigger).
   - The result: `Image(pixels=float32 (H, W, 3), device="cpu", color=..., orientation_applied=True)`.
   - DNG and ProRAW refused before any decode, with the D116 message.
3. **Orientation (D63, AD-24).**
   - JPEG, PNG, TIFF: the EXIF Orientation (1-8) is applied once to the pixels.
   - HEIC: libheif applies `irot`/`imir`; the raw EXIF Orientation is read through
     `open_heif`; when the file carries a tag other than 1 and the PRIMARY item has no `irot`,
     the tag is applied. `irot`/`imir` presence is read through `pitm` → `ipma` → `ipco`, not
     from `ipco` alone (WP2.1S section 8.1: "`heif_transforms` ... does NOT read `ipma` ... A
     real iPhone HEIC (a grid, thumbnails, auxiliary images) needs the primary item's `ipma`
     entries"; DR-33 (c)), and the primary item's `ispe` is checked against the decoded size
     (swapped for a 90/270 `irot`); a mismatch is refused as unreadable.
   - `PhotoMetadata.orientation` is the SOURCE tag (the manifest expects 6 for
     `heic-ad24-both` and `heic-ad24-exif-only`).
4. **Colour (6.5, D53).** The embedded ICC profile is carried byte-identical in
   `ColorDescription.icc_profile` and never applied to the pixels; `primaries`/`transfer`
   per question 4; an untagged photo per question 3; `matrix "identity"`, `range "full"`,
   `bit_depth` the source's.
5. **Writer (8.1, D22, D53, D91).**
   - PNG, 8 or 16 bits per channel, RGB; any other `bit_depth` is a `ValueError`.
   - Quantisation per question 7, the only quantisation in the photo path (6.4).
   - `iCCP` with the source profile byte-identical; the profile name obeys the full PNG
     keyword rule (1-79 Latin-1 bytes, no control characters, no leading, trailing or
     consecutive spaces; DR-31 (1)).
   - `eXIf` per task 6; the provenance chunk per question 5 when `provenance` is not None,
     none when it is None.
   - Writes `out_path` and nothing else: opened `"wb"` (the WP3.13 consumer note: "The PNG
     writer opens it `"wb"`. The writer must close the file before `commit()`."), closed
     before return; a non-`.png` suffix (case-insensitive) is refused; no sidecar, no
     temporary of its own; nothing is ever written beside the source.
   - An image not on the host per question 9.
6. **EXIF (D63).** On the source block: Orientation set to 1; IFD1 (the embedded thumbnail)
   removed; `PixelXDimension`/`PixelYDimension` set to the written size; `Software` set to
   `Clearwater`; every other field kept, GPS included. A source without EXIF gets a minimal
   block carrying Orientation 1, the dimensions and `Software` (or none: the round-0 table
   says which). HEIC auxiliary images are dropped by construction (PNG has one image); say so
   in the report.
7. **Safe-write composition (X-B1, N8).** A test proves the product composition WP3.14 will
   use: `plan_output(source, settings, MediaKind.PHOTO)` → `with SafeWrite(plan) as w:
   sink.write(..., w.temp_path, ...); w.commit()`, including an exception inside `write`
   (no partial left, no final created) and the source byte-identical with its mtime unchanged.
8. **Follow-on instrument `tools/photo_check.py` (question 11).** Given photo files or a
   folder (default: the configured footage folder, read only, walked for the four photo
   formats and `.dng`), it writes a record under `work/` per photo: format, pixel and stored
   size, bit depth, HEIC primary-item layout (`irot`/`imir`/EXIF tag via `ipma`, grid or
   not, auxiliary images present), ICC description and classification, EXIF tag list, the
   read verdict, and a round trip (write a 16-bit PNG under `work/`, re-read it, compare
   samples, ICC and the D63 fields). It never writes outside `work/`. mypy-checked
   (`tools` is in mypy's `files`).
9. **Tests.**
   - Every WP2.3 still and DNG sample against its manifest `expect` (metadata, colour,
     orientation, refusal), by manifest id through the `sample` / `sample_entry` fixtures.
   - The orientation samples: `jpeg-orient-{land,port}-o{1,3,6,8}` upright after the read;
     the four `heic-ad24-*` cases rotated exactly once (none twice, none lost).
   - 16-bit samples survive the read at full precision (`png16-*`, and 16-bit RGB TIFFs
     written under `tmp_path` with `tifffile`, with and without an ICC profile and an
     Orientation tag; WP2.3 has none); the `tiff8-*` samples read through `tifffile` match
     their manifest `expect`; an interlaced 16-bit PNG built under `tmp_path` is refused by
     name; 10-bit HEIC reaches 1.0 at its maximum code value.
   - Written PNGs verified by a reader other than the writer: samples exact through the
     FFmpeg CLI (`-f rawvideo -pix_fmt rgb48be` / `rgb24`; the `ffmpeg_tools` fixture),
     `iCCP` bytes equal to the source profile and `eXIf` through Pillow, chunk order through a
     stdlib walker.
   - D63 on a test-built EXIF with Orientation 6, an IFD1 thumbnail (as
     `tools/spike_io/photo.py` builds one), GPS, Make/Model/DateTimeOriginal: each D63 change
     made, everything else kept.
   - V9 I/O legs: read → write 16-bit → read is exact to the 16-bit quantisation for 8- and
     16-bit sources, and within AD-11 V9 (≤ 2/255 max) for every sample.
   - Refusals: the three DNG samples (by extension, by tag, extension only); a truncated copy
     of a JPEG, a PNG and a HEIC sample made under `tmp_path`; an unknown format; each with
     its kind and a message naming the file.
   - Provenance: present and parseable when given, absent when None; a non-string key refused.
   - A planted wrong implementation fails by name: HEIC EXIF always honoured (double
     rotation), HEIC EXIF never honoured (`heic-ad24-exif-only` unrotated), `irot` read from
     `ipco` without `ipma`, `ispe` not checked, a 16-bit source read as 8, 16-bit written as 8, a stale Orientation, the thumbnail kept, an
     ICC byte changed, a profile name with a trailing space accepted.
   - Dependency rule (plan 8.1, frame rule 5): a subprocess test that importing
     `clearwater.io.photo` loads nothing from `clearwater.gui`, `.jobs`, `.methods`, `.core`,
     nor `PySide6`, `cupy`, `av`.

## Declared operating envelope

Windows 11; Python 3.12; Pillow 12.3, pillow-heif 1.8.1 (libheif 1.23.6) and `tifffile` as
locked; photos
from an iPhone camera (HEIC, JPEG) and from other software (PNG, TIFF), up to 48 MP (spec 12,
D117); local NTFS or exFAT volumes; one Clearwater process. Out of envelope: deliberately
crafted or hostile files beyond Pillow's and libheif's own checks; CMYK and exotic TIFF
features (question 8); network shares; other operating systems (portable, N1, not run there).
The real-iPhone verdicts (AD-24 layout, grids, MakerNote survival, the largest photo) are
OUTSIDE what this package can show: they wait for the follow-on of question 11.

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.6\rN\`; ledger `docs/proofs/wp3.6-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r2\`
  (`run_review.sh`, `review-prompt.md`; the round also keeps `probe.txt`, `review-diff.txt`,
  `review.txt`, `adjudication.md`, `md5sums.txt`, `test-summary.txt` as there); the reviewer
  excludes `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - orientation: every EXIF value 1-8 once; AD-24 on all four HEIC layouts; `ipma`, not `ipco`
    alone; `PhotoMetadata.orientation` is the source tag;
  - precision: no silent 8-bit read of a 16-bit or 10-bit source; normalisation and
    quantisation exact at 0 and at the maximum code value;
  - the ICC profile byte-identical in and out; never applied to pixels;
  - every D63 field, and nothing else changed in the EXIF;
  - the PNG is valid (chunk CRCs, order, keyword rule) as read by other readers;
  - DNG refused before decode by extension and by tag; truncated files refused, not
    half-read;
  - the writer writes only `out_path`, never beside the source;
  - the pyproject lines exactly as granted; nothing in `interfaces/` changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Yields.** Round 0: read and table, then YIELD before product code. After each review
  round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating. Yield
  at every round boundary; the dispatcher reads your depth (~250K evaluation point, ~400K
  stop).
- **Full-pytest windows (X5).** The full suite (about 1844 tests, 9-11 min) runs ONLY in a
  window the dispatcher grants by message, in the background with output to a file under
  `work/`; send `WINDOW RELEASED: <summary>` when it finishes and carry on. Inner loops run only
  your own tests.
- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the public API, the per-format table (read path, orientation, precision), the
  sample table (manifest id, expectation, result), the D63 field table, the pyproject diff,
  what waits for real photos, the gates, the Reviewer A rounds and verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20); a dependency
  beyond pillow, pillow-heif and tifffile (piexif, imagecodecs, exiftool, pypng: none is
  granted); a 16-bit
  input you can only read at 8 bits; any OS-specific code; inventing or downloading a photo
  (every test input is a WP2.3 sample or built under `tmp_path`); any write to the footage
  folder; the round-0 table showing a choice the brief left open.
- **Working rules:** `uv sync`. Commit by pathspec, `feat(wp3.6): ...` (conventional commits
  carrying the WP id), with a `Co-Authored-By:` footer naming your model. Never a bare `cd`.
  Never post to a mailbox. Gates: ruff check, ruff format --check, mypy strict, full pytest (in
  a window); no harness gate (you touch no `scripts/`, `.claude/`, kernel doc or
  `tests/harness/`). Report `docs/reports/wp3.6-photo-io.md` (claims, evidence paths, limits,
  and a section "Waits for real photos"). GoPro IMU/GPS data is out of scope everywhere.

## Rulings (CHARC `53b752a4d7fac4fc`, 2026-10-20)

CHARC `53b752a4d7fac4fc`, 2026-10-20: every recommended answer is the ruling unless amended here.
- **1 AMENDED (AD-17, AD-18 amended on main `718da66`):** the stdlib 16-bit PNG decoder in
  `io.photo` reads NON-INTERLACED PNG only; Adam7 is refused by name (dropped from the decoder
  scope). `tifffile` (BSD-3) is GRANTED as a product dependency for TIFF at every depth; no
  hand-written TIFF reader. Pillow keeps JPEG and 8-bit PNG; pillow-heif HEIC. Spec 5.1 stands.
  Part (c) (10-bit HEIC normalised by its true depth) stands as drafted.
- **X-B1, X-B2, X-B3:** as drafted.
- **11:** WP3.6P "Real-photo verification" APPROVED as a queued sonnet-medium package,
  dispatched when the owner supplies photos.
- CHARC accepted the drafter's corrections to its debt list; DR-7 is disposed as in the
  "Debt and decided items" row.

### Questions as drafted (recommended answer first)

1. **SUPERSEDED by ruling 1 (parts (a) and (b); (c) stands).** **16-bit inputs that Pillow
   truncates.** Pillow 12.3 reads a 16-bit RGB PNG and a 16-bit RGB
   TIFF as 8-bit `RGB` (DR-11 for PNG; a drafting-time check for TIFF). Spec 5.1 requires both.
   Recommended: (a) a stdlib 16-bit PNG decoder in `io.photo.png` (zlib, the five filter types,
   Adam7, colour types 2 and 6 with alpha dropped, 0 and 4 expanded to RGB), used for every
   16-bit PNG; (b) a stdlib 16-bit TIFF reader for the baseline forms (uncompressed, Deflate,
   LZW, PackBits; predictor 1 or 2; strips; chunky or planar), anything else refused with a
   message naming the feature, tested on TIFFs built by a test-local writer (WP2.3 has none);
   (c) 10-bit HEIC normalised by its true depth, `(v >> 6) / 1023`, so white is 1.0. Alternatives
   for (b): a CHARC grant of `tifffile` (BSD-3; licence check per N13), or the owner relaxes
   5.1's 16-bit TIFF (owner-reserved: it relaxes a mandatory requirement).
2. **X-B1 (cross-brief, WP3.6 and WP3.12): who calls `SafeWrite`.** IF-6 `PhotoSink.write` takes
   an `out_path`, not an `OutputPlan`. Recommended: the CALLER (WP3.14's photo export, WP4.1)
   plans the name, opens `SafeWrite` and passes `temp_path`; the sink writes only the path it is
   given, `"wb"`, as the WP3.13 consumer note says; `io.photo` imports nothing from
   `clearwater.jobs` (io stays below jobs), and task 7's test proves the composition. DR-35's
   "folder and suffix validated at export start" stays WP3.14's. Alternative: a convenience
   `write_photo_safely(...)` in `io.photo` that wraps `SafeWrite` (io then imports jobs).
3. **An untagged photo.** Spec 6.5 has no photo default (D54 is video). G10 asks for a message
   on "untagged inputs". Recommended: no ICC → `primaries "bt709"`, `transfer "srgb"` (the
   de-facto reading of an untagged photo), `assumed=True` (the shell's G10 warning), and the
   PNG written WITHOUT `iCCP`, so the output is read as the source was. Alternative: embed a
   built-in sRGB profile.
4. **`primaries` and `transfer` from an ICC profile.** Recommended: read the colorant and TRC
   tags through `ImageCms` (undoing `chad` as WP2.1S did); within 0.001 of BT.709/sRGB →
   `bt709`/`srgb`; of Display P3 → `display-p3`/`srgb`; otherwise `unknown` with the profile
   still carried byte-identical (an Adobe RGB photo stays Adobe RGB, 6.5). No pixel value is
   converted in any case.
5. **Provenance in the PNG (D91).** Recommended: one `iTXt` chunk, keyword
   `clearwater-provenance`, uncompressed UTF-8, holding the provenance mapping as JSON
   (`allow_nan=False`, after `clearwater.config.check_string_keys`), placed before `IDAT`;
   `Software` stays the bare `Clearwater` of 8.1 (the version lives in provenance, which can be
   turned off). Alternative: EXIF `UserComment` (size-limited, less readable).
6. **The 8-bit writer.** WP2.1S showed Pillow writes 8-bit PNG with ICC and EXIF. Recommended:
   the stdlib writer for BOTH depths (one writer, one chunk order, one keyword rule), Pillow
   used for EXIF bytes only. Alternative: Pillow for 8-bit.
7. **Quantisation.** Recommended: clip to [0, 1], then `rint(x * (2**d - 1))` (round half to
   even), big-endian samples for 16 bits; no dithering. A NaN in the image is a `ValueError`.
8. **Pixel modes other than RGB.** Recommended: grey, grey+alpha, palette and RGBA are converted
   to RGB (alpha dropped, a warning in the result's log line); a grey ICC profile cannot
   describe RGB output and is not carried (warned); CMYK and multi-sample TIFF beyond RGB are
   refused as unsupported; a multi-page TIFF reads page 1 with a warning.
9. **An `Image` on the GPU.** `PhotoSink.write` may receive `device="cuda:0"`; `io.photo` may
   not import CuPy (frame rule 3). Recommended: the sink refuses a non-`"cpu"` image with
   `ValueError` naming the device; the caller calls `backend.to_host` first (WP3.14).
10. **X-B2 (cross-brief, WP3.6 and WP3.16): the read-error vocabulary.** Recommended:
    `clearwater.io.photo.PhotoReadError(kind, message)` mirroring
    `clearwater.io.video.VideoProbeError`, kinds `"unsupported"` (DNG/ProRAW, CMYK, an unknown
    format) and `"unreadable"` (missing, truncated, corrupt); "untagged" is not an error but
    `ColorDescription.assumed`. Committed at WP3.6's round-0 yield so WP3.16 catches it by name
    (as X2 shipped `clearwater.config.paths` early).
11. **What waits for real photos, and who does it.** Nothing in this package waits: it is
    tested on WP2.3 fixtures and test-built inputs. Waiting for the owner's photos: the AD-24
    layout of a real iPhone HEIC (grid primary, `ipma`, tag and `irot` together), MakerNote and
    GPS survival through Pillow's EXIF writer, Display P3 classification of Apple's profile,
    the largest photo for the Result 2 photo leg and V15, and the photo look check.
    Recommended: a named follow-on **WP3.6P "Real-photo verification"** (sonnet-medium, a
    mechanical run of `tools/photo_check.py` from task 8 on the owner's photos, plus any fix it
    proves), commissioned when photos arrive; not a blocker for WP3.6's accept or WP4.1.
12. **`src/clearwater/io/__init__.py`.** WP3.7 created it, docstring only ("``video`` is the
    video probe and input validation (WP3.7)"). Recommended: WP3.6 appends one sentence naming
    `photo`, nothing else (as X1 ruled for `jobs/__init__.py`).
13. **X-B3 (cross-brief, WP3.6 and WP3.16): the two dependency grants.** Both edit
    `pyproject.toml` and `uv.lock` in parallel worktrees. Recommended: each moves or adds only
    its own lines; whichever merges second rebases and regenerates `uv.lock` with `uv lock` (no
    hand merge of the lock), and its report says so. `pillow` and `pillow-heif` leave the `dev`
    group when they enter `[project] dependencies` (the frame's "moved").
