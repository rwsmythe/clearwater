# WP0.2 — Footage inventory tool (dispatch brief, DRAFT)

**Status:** draft by CHARC, 2026-10-14, commissioned to the orchestrator, which issues the
FINAL brief in the plan's section 4.6 format. Build and tests need no footage; the real
inventory run waits for the owner's download into `C:\Users\rwsmy\clearwater-footage\`
(may be absent or incomplete while the cell works: treat the folder as a read-only snapshot).

| Field | Content |
|---|---|
| ID and title | WP0.2 — Footage inventory tool |
| Goal | One command lists every video and photo in the footage folder with the metadata the prototype gate needs, in a table the owner can categorise for CP1, plus a summary of recording modes and photo sizes. |
| Spec clauses | D102 (inventory precedes the prototype gate; gaps filled or the dependent test marked pending); spec section 12 item 1 (the field list); D117 (usage profile); plan section 4.2 (footage read-only; outputs to the working folder); plan section 6 WP0.2 (the full field list and the CP1 categories). |
| Depends on | WP0.1 (merged at c09f747): `tools/local_config.py`, the `footage` marker skip, FFmpeg dev tools (`ffprobe` 9.0.2 on PATH). |
| Files owned | `tools/inventory.py`, `tests/test_inventory.py`, `docs/proofs/wp0.2-ledger.md`, `uv.lock`, and in `pyproject.toml` ONLY the two dev-group grants below. |
| Interfaces consumed | `load_local_config`, `footage_available` (frozen as merged in WP0.1; do not edit `tools/local_config.py`). |
| Interfaces provided | See "Interfaces" below. |
| Dependencies | Video metadata: `ffprobe` via `subprocess` (no shell, timeout; a dev tool, not a product choice: D104 decides the product's video library). Photo metadata, grants (dev group ONLY, CHARC-approved): `Pillow` (HPND) and `pillow-heif` (BSD-3; bundles libheif/libde265, LGPL-3, acceptable for a development tool) for HEIC/JPEG/PNG format, pixel size, bit depth, ICC profile and EXIF orientation. Nothing else. |
| Tests | `tests/test_inventory.py`: synthetic media generated into tmp (tiny MP4/MOV via `ffmpeg -f lavfi testsrc`, JPEG/PNG/HEIC via Pillow + pillow-heif); the GoPro name parser and `.LRV` detection on a synthetic tree; the writer; `main` end to end on the synthetic tree with `--footage` and `--out`. Tests that need `ffmpeg`/`ffprobe` skip with a reason when the tools are absent. ONE `footage`-marked test runs the real folder and asserts one row per media file (skips when the folder is absent). |
| Hardware flags | `footage` (one test). Not exclusive. |
| Out of scope | Any correction or decoding of pixels; thumbnails; the category assignment itself (the owner does it at CP1); editing `tools/local_config.py` or `tools/environment_report.py`; the product's video library; chapter JOINING (only chapter NUMBERING is recorded); ProRAW/DNG (deferred, spec v0.5). |
| Done | Plan section 4.5, plus the four gates and the harness gate green on the final head; the return report says whether the real footage folder existed at run time and, if it did, the counts found. |

## Interfaces

`tools/inventory.py`

- `@dataclass(frozen=True) class VideoRecord`: `path: Path` (relative to the footage root),
  `size_bytes: int`, `container: str`, `codec: str`, `width: int | None`, `height: int | None`,
  `frame_rate: float | None` (average), `frame_rate_variable: bool | None`, `bit_depth: int | None`,
  `chroma_format: str | None` (for example `yuv420p` reported as `4:2:0`), `color_primaries`,
  `color_transfer`, `color_matrix`, `color_range` (all `str | None`), `duration_seconds: float | None`,
  `rotation_degrees: int | None`, `tracks: tuple[str, ...]` (one `"<index>:<type>:<codec>"` per
  stream), `gopro_recording: int | None`, `gopro_chapter: int | None`, `lrv_present: bool`,
  `category: str` (always empty here), `error: str | None` (probe failure reason; the row still exists).
- `@dataclass(frozen=True) class PhotoRecord`: `path`, `size_bytes`, `format: str`, `width`,
  `height`, `bit_depth: int | None`, `color_profile: str | None` (ICC description, or `None`),
  `orientation: int | None` (EXIF 1 to 8), `category: str`, `error: str | None`.
- `parse_gopro_name(name: str) -> tuple[int | None, int | None]`: `(recording, chapter)` from
  GoPro stems `GX<cc><nnnn>` / `GH<cc><nnnn>` (chapter `cc`, recording `nnnn`); `GOPR<nnnn>` /
  `GP<cc><nnnn>` legacy forms if cheap; `(None, None)` otherwise. The cell confirms the real
  footage's naming once the folder exists and reports any pattern it does not cover.
- `lrv_beside(video: Path) -> bool`: an `.LRV` sidecar in the same directory, either the same stem
  or the GoPro form with the first two letters replaced by `GL` (`GX010001.MP4` pairs with
  `GL010001.LRV`); case-insensitive on the extension.
- `probe_video(path: Path) -> VideoRecord`: one `ffprobe -v error -print_format json -show_format
  -show_streams <path>` call; variable frame rate = `r_frame_rate` and `avg_frame_rate` of the first
  video stream differ by more than 0.5 percent; rotation from the stream's `side_data_list` display
  matrix or the `rotate` tag; bit depth from the pixel format (`yuv420p` 8, `yuv420p10le` 10, and so on).
- `probe_photo(path: Path) -> PhotoRecord`: Pillow with `pillow_heif.register_heif_opener()`;
  bit depth from the mode (`RGB` 8, `I;16` 16; HEIC 10-bit reported when pillow-heif exposes it,
  else `None` with a reason in `error`).
- `scan(footage_root: Path) -> list[VideoRecord | PhotoRecord]`: recursive, sorted by relative
  path; video extensions `.mp4 .mov .360`, photo extensions `.heic .heif .jpg .jpeg .png .tif
  .tiff`; `.lrv` and `.thm` files are sidecars, not rows; everything else is ignored but counted.
  Opens files read-only; creates nothing under the root.
- `write_inventory(records, working: Path) -> tuple[Path, Path]`: writes
  `<working>/reports/inventory-<YYYYMMDDTHHMMSSZ>.csv` (one row per record, union of the columns,
  `category` empty, UTF-8 with BOM so Excel opens it) and `inventory-<stamp>-summary.md` (counts by
  kind; recording modes as `<width>x<height> @ <fps> <codec> <bit depth>-bit <chroma>` with counts;
  photo sizes with counts; chaptered recordings (recording numbers with more than one chapter);
  `.LRV` coverage; files with probe errors; ignored-file count). Never overwrites (exclusive create,
  `-N` suffix on collision, as in WP0.1).
- `main(argv) -> int`: `--config PATH`, `--footage DIR` (overrides the configured footage root),
  `--out DIR` (overrides the working folder; with both `--footage` and `--out` given the config is
  not read). Prints the two paths; returns 0; returns 2 with a one-line error on a missing footage
  root or an unwritable working folder. Prints the CP1 category list at the end as a reminder:
  shallow with caustics; deeper; mostly open blue water; photo, shallow; photo, deeper; chaptered
  recording; static shot.

## Required end state (the claim list)

1. `uv run python tools/inventory.py` with the filled local config writes the CSV and the summary
   under `C:\Users\rwsmy\clearwater\work\reports\` and writes NOTHING under the footage root.
2. Every video field of plan WP0.2 appears as a column; every photo field likewise; a probe failure
   yields a row with `error` set, never an aborted run.
3. GoPro recording and chapter numbers and `.LRV` presence are correct on a synthetic tree that
   mirrors the GoPro naming above.
4. The summary names each distinct recording mode and photo size with counts, and lists the
   chaptered recordings.
5. Docstrings complete; the four gates and the harness gate green; the two new dev-group
   dependencies are the only `pyproject.toml` / `uv.lock` change.

## Declared operating envelope

Windows 11, Python 3.12 under uv, `ffprobe`/`ffmpeg` 9.0.2 present (tests skip when absent),
GoPro MP4 (H.264/HEVC, 8- or 10-bit) and iPhone HEIC/JPEG/MOV, a footage folder that may be absent
or mid-download. Other cameras' naming schemes, RAW formats and network paths are out of envelope.

## Notes for the cell

- `uv sync` in the worktree; commit by pathspec; conventional commits `feat(wp0.2): ...` with the
  `Co-Authored-By:` footer; never a bare `cd`.
- STOP and return on: any dependency beyond the two grants; a photo field pillow-heif cannot
  provide (report which); a GoPro naming pattern in the real footage the parser does not cover.
