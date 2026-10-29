# Real footage inventory, 2026-10-29

Commission: CHARC `fddf5c88`, phone-footage refresh. No product pipeline code changed;
no category assigned to included files. The inventory tool adds only the
authorized top-level exclusion option and its regression test. This is a read-only mechanical instrument run;
independent orchestrator re-run plus five spot checks plus CHARC QA substitute
for Reviewers A and B (CHARC `a9fc36da`; precedent `inventory-2026-10-18`).
Those acceptance checks are pending at handoff, not claimed complete here.

**Commissioned scope:** the footage tree minus `Insta360/`, excluded by exact
top-level name under CHARC `0fd08f9f` (superseding `481d63d8`): arriving;
separate owner input; scope undecided. The owner's category for that excluded
input is SCUBA (CHARC `4096c6d3`); no package consumes it. At re-run start,
2026-10-29 17:37:51.733678 UTC, it held 17 files and 9 subdirectories (26
descendant entries, excluding its root), totaling 24,304,558,148 file bytes.
This is a plain stat-only observation, not an inventory or completion claim;
no excluded-folder rows or stream facts are reported. The excluded re-run
is row-identical to 17:17:52Z, so that original included-tree snapshot stands.
The historical whole-tree test failure is retained in section 8.

The Codex read-only footage grant applies to this package only: selected
headers, boxes and tags in the configured footage folder, without pixel/frame
decoding. The sandbox's writable roots are the worktree, its temp and the uv
cache, so no write path to the footage folder exists.

## 1. Run

- Original command: `uv run python tools/inventory.py --out work`. Exit 0.
- Excluded re-run: `uv run python tools/inventory.py --exclude Insta360 --out work`.
  Exit 0, stamp `20261029T173803Z`. The single-name option prunes the top-level
  folder before traversal or probing, case-insensitively on Windows. No filtered
  stand-in tree, links or post-filtered inventory were used.
- `--out work` was authorized because the configured working folder lies outside
  the sandbox. The output destination is the only difference from the
  2026-10-18 command for the original run; the later re-run additionally uses
  the expressly ruled exclusion. The config was not changed.
- Worktree: `.worktrees/inventory-1029`, head `1c59f15`.
  The baseline inventory tool was last committed at `34abd10` (2026-10-18
  report: `e930685`). This worktree adds only `--exclude` under CHARC `0fd08f9f`;
  its current LF checksum is listed in section 11. The tool used at 17:17:52Z
  had md5 `a9ab4756159481b884b50b3790d45008`.
- Run stamp (UTC): `20261029T171752Z`. The input tree now includes `Phone/`.
- ffprobe: `9.0.2-full_build-www.gyan.dev`.
- Actual output paths below are relative to this worktree root,
  `C:/Users/rwsmy/clearwater/.worktrees/inventory-1029/`.

| Output | md5 |
|---|---|
| `work/reports/inventory-20261029T171752Z.csv` | `60e6ce4bbc954166df529f79a0eb7350` |
| `work/reports/inventory-20261029T171752Z-summary.md` | `f94e90b6bb3cc79d0985ba6694dba662` |
| `work/reports/inventory-20261029T173803Z.csv` | `60e6ce4bbc954166df529f79a0eb7350` |
| `work/reports/inventory-20261029T173803Z-summary.md` | `744f094c988ae1d827e16558615669b0` |

The re-run comparison parses both CSVs with `csv.DictReader`, indexes by full
relative path and compares each complete field dictionary, including size,
error, category and every probe fact: **128 rows vs 128, 0 differing rows**.
The CSV md5s also match, confirming byte identity. For stability, separate
before/after dictionaries capture `(st_size, st_mtime_ns)` for every entry in
Phone, Snorkel, SCUBA and edits, including those four roots: **132 entries,
0 changes**. The excluded folder and the footage root's own stamp are not in
that assertion. Only aggregate stats of the excluded folder were observed.
Commands/method and results are retained in
`work/inventory-1029/run-excluded.py`, `included-before.json`,
`included-after.json`, `excluded-observation.json` and `excluded-comparison.json`.

## 2. Counts per folder

Summed from the CSV. Duration sums video `duration_seconds` (rounded to
milliseconds per row); photos have no duration.

| Folder | Videos | Photos | Files | Size (bytes) | Duration (s) |
|---|---:|---:|---:|---:|---:|
| `Snorkel/` | 26 | 0 | 26 | 5,058,259,868 | 1694.493 |
| `SCUBA/` | 8 | 0 | 8 | 24,122,034,711 | 2889.353 |
| `edits/` | 1 | 0 | 1 | 318,648,117 | 179.930 |
| `Phone/` | 20 | 73 | 93 | 1,359,540,146 | 876.269 |
| Total | 55 | 73 | 128 | 30,858,482,842 | 5640.045 |

The existing folders are unchanged against 2026-10-18: all 35 CSV rows match
in every field, including relative names, byte sizes and probe facts. The
baseline CSV md5 is `d86ed6bd071312d5f67540766f4e5edb`, matching that report.
This is a row comparison, not a claim that media payload checksums were taken.
`edits/` is lowercase on disk.

## 3. Recording modes (tool summary)

Counts: videos 55, photos 73, probe errors 0, ignored 0, sidecars 0, skipped 0.

```text
3840x2160 @ 29.97 hevc 8-bit 4:2:0: 34
1920x1440 @ 30 hevc 8-bit 4:2:0: 15
1920x1080 @ 29.995 h264 8-bit 4:2:0: 1
1920x1080 @ 29.995 hevc 10-bit 4:2:0: 1
1920x1080 @ 30 hevc 10-bit 4:2:0: 1
1920x1080 @ 30 hevc 8-bit 4:2:0: 1
1920x1080 @ 59.94 h264 8-bit 4:2:0: 1
1920x1440 @ 29.985 hevc 8-bit 4:2:0: 1
Variable frame rate: 0
```

The VFR figure is the tool's header heuristic (nominal and average rate differ
by more than 0.5%), not a packet-duration scan or proof of constant timing.
Exact Phone rate fractions are retained below.

Snorkel 26 and SCUBA 8 remain HEVC 3840x2160, 8-bit 4:2:0 at about 29.97 fps.
The one edits file remains H.264 1920x1080, 8-bit 4:2:0 at about 59.94 fps.
All existing videos retain bt709/bt709/bt709, `pc` range and rotation 0.

Photo counts: HEIF 62, JPEG 11; all primary images 8-bit. Stored dimensions:
5712x4284 (38), 4032x3024 (25), 3213x5712 (8), 3024x4032 (1),
3520x1980 (1). Apply the orientation facts in section 10 for display.

## 4. Chaptered recordings

None. All 34 GoPro-named files are chapter 1 (`GX01xxxx`); no `GX02xxxx` exists.
Snorkel recordings 1603-1628 (26); SCUBA recordings 1589, 1590, 1591, 1592,
1593, 1598, 1600, 1601 (8). The 20 Phone videos have no GoPro chapter fields.

## 5. Error rows and skipped files

None: zero error rows, zero skipped, zero ignored. The supplemental probe also
completed for all 93 Phone files without errors. Headers were probed, not
payload integrity: DR-6 still applies to an intact header over truncated media.

## 6. Uncovered GoPro names

Among videos, 21 have empty recording/chapter fields:
`edits/compilation-20261010-1080p60.mp4` plus all 20 Phone video names listed
in section 10. All other 34 videos follow the GoPro naming scheme.
The 73 photos have no GoPro recording/chapter fields by design.

## 7. Notes

- No `.LRV` or `.THM` sidecars: 0 of 55 videos have `.LRV` coverage.
- The previously pending photos are now present: Phone has 62 HEIC and 11 JPG,
  plus 19 MOV and 1 mp4. It totals 1,359,540,146 bytes.
- The existing compilation remains 318,648,117 bytes and 179.930 s. Its known
  role as a later smoothing stress case is unchanged.
- The owner supplied Phone as snorkel-depth footage with a couple of
  above-surface files and possibly corrected files. These are the owner's
  statements; no per-file scene judgement was made here.
- All work outputs stay under this worktree's `work/`. The local configuration,
  source footage, product code, interfaces and dependencies were not changed.

## 8. WP0.2 footage test

Command (PowerShell):

```powershell
$env:PYTHONPATH='scripts'
uv run pytest -q -rs --basetemp=work/inventory-1029/pt -p sandbox_mkdir_shim -p no:cacheprovider tests -k test_real_footage_has_one_row_per_media_file
```

The full-tree invocation was interrupted before producing a test result. A
narrowed invocation of the same test then completed:

```powershell
$env:PYTHONPATH='scripts'
uv run pytest -q -rs --basetemp=work/inventory-1029/pt-direct -p sandbox_mkdir_shim -p no:cacheprovider tests/test_inventory.py::test_real_footage_has_one_row_per_media_file
```

**Exit 1: `1 failed in 9.18s`.** The two media-row coverage assertions passed;
the final `_snapshot(root) == before` assertion at `tests/test_inventory.py:1138`
failed. During the scan, newly appearing `.insv` files in `Insta360/` changed
from 0 bytes to non-zero sizes and acquired different modification stamps.
This was concurrent growth in the folder now excluded by name, outside the
included-tree snapshot. No per-file excluded-folder rows are reported.
The stability failure was caused by the in-progress Insta360 download,
confirmed by CHARC. It is **not a DR-6 finding** for the folders this report
claims. CHARC `0fd08f9f` requires the included-folder assertion across the
excluded re-run, which passed as recorded in section 1. This test itself
reads the whole configured tree: it was not changed and was not re-run.
Selected original output (the source line number is from that earlier run):

```text
>       assert _snapshot(root) == before
...
tests\test_inventory.py:1138: AssertionError
1 failed in 9.18s
```

The test checks one row per media file and compares source file sizes and
modification stamps before/after the scan. Logs: `work/inventory-1029/pytest.log`
(interrupted) and `work/inventory-1029/pytest-direct.log` (failed).

## 9. Nothing assigned

The CSV `category` column is empty in all 128 rows. No categories, corrections,
scene labels or package assignments were added by this refresh.

## 10. Phone

All names in this section are relative to `Phone/`. A range in a HEIC row is
inclusive; every number listed denotes a separate `IMG_<number>.HEIC` file.
Rows group only files sharing every selected photo fact.

### Photos: HEIC

Common to all 62: container HEIF/HEIC, brand `heic`, codec HEVC, primary 8-bit,
ICC description `Display P3`, primary `nclx` absent, EXIF `Make=Apple`,
`Model=iPhone 15 Pro`, `Software=26.6.2`, `ColorSpace=65535` (uncalibrated).
The ICC supplies the named colour profile. Dimensions are stored primary
`ispe` dimensions, before `irot`; rotations below are counterclockwise degrees.
An absent EXIF orientation is distinguished from identity value 1.

| IMG numbers (.HEIC) | Count | Stored dimensions | irot CCW | EXIF orientation |
|---|---:|---|---:|---|
| 6690-6701, 6706-6710, 6748-6750 | 20 | 5712x4284 | 180 | 3 |
| 6703, 6711-6715, 6752-6753, 6761 | 9 | 4032x3024 | 0 | absent |
| 6705, 6754-6759 | 7 | 5712x4284 | 0 | absent |
| 6718-6719, 6747 | 3 | 4032x3024 | 90 | 8 |
| 6720-6726, 6730, 6732, 6737, 6739 | 11 | 4032x3024 | 270 | 6 |
| 6740, 6743-6744, 6746, 6763 | 5 | 5712x4284 | 270 | 6 |
| 6764-6770 | 7 | 3213x5712 | 0 | absent |

Easy HEIC spot checks: `IMG_6690.HEIC` is 5712x4284 with `irot=180`,
EXIF 3; `IMG_6703.HEIC` is 4032x3024 with `irot=0`, EXIF orientation absent.
These facts concern the primary image; auxiliary images and gain maps were not
examined, and this is not a claim that all photo HDR mechanisms were excluded.

### Photos: JPG

All 11 are JPEG container/codec, 8-bit, EXIF orientation 1. `irot` and `nclx`
are not applicable. Tag groups:

- A: `Make=Apple`, `Model=iPhone 15 Pro`, `Software=26.6.2`, ICC description
  `Display P3`, EXIF `ColorSpace=65535`.
- Z: Make consists of 5 NUL characters, Model 13 NUL characters, Software 6 NUL
  characters. These are present but unusable strings, not camera/editor names.
  No ICC profile; EXIF `ColorSpace=1` (sRGB).
- M: Make, Model and Software absent. No ICC profile;
  EXIF `ColorSpace=1` (sRGB).

| File | Stored dimensions | Tag group |
|---|---|---|
| `IMG_6751.JPG` | 4032x3024 | A |
| `IMG_6771.JPG` | 3520x1980 | A |
| `IMG_6791.JPG` | 3213x5712 | Z |
| `IMG_6793.JPG` | 5712x4284 | Z |
| `IMG_6794.JPG` | 5712x4284 | M |
| `IMG_6795.JPG` | 5712x4284 | Z |
| `IMG_6798.JPG` | 5712x4284 | Z |
| `IMG_6799.JPG` | 5712x4284 | Z |
| `IMG_6800.JPG` | 5712x4284 | Z |
| `IMG_6801.JPG` | 3024x4032 | Z |
| `IMG_6802.JPG` | 4032x3024 | Z |

### Videos: format, rates, colour and rotation

The 19 `.MOV` files are QuickTime (`major_brand=qt`, compatible `qt`),
HEVC `hvc1`, with stream encoder `HEVC` and format tags
`com.apple.quicktime.make=Apple`, `com.apple.quicktime.model=iPhone 15 Pro`,
`com.apple.quicktime.software=26.6.2`. Each has `has_b_frames=2`, header evidence
of frame reordering. This does not count decoded B pictures.

`dp_color_video_1791675261.mp4` is MP4 (`major_brand=mp42`, compatible
`isommp41mp42`), H.264 `avc1`, `has_b_frames=0`; all selected Make/Model/Software
and encoder tags are absent. ffprobe's format family name for all 20 is
`mov,mp4,m4a,3gp,3g2,mj2`.

Colour groups (primaries / transfer / matrix / range, verbatim ffprobe names):

| Group | Tags | Depth/pixel format | HDR evidence |
|---|---|---|---|
| C1 | smpte432 / bt709 / smpte170m / pc | 8 / yuvj420p | No HDR transfer or DV record in selected fields |
| C2 | bt2020 / arib-std-b67 / bt2020nc / tv | 10 / yuv420p10le | HLG; Dolby Vision configuration v1.0, profile 8, level 4, compatibility ID 4 |
| C3 | bt709 / bt709 / bt709 / pc | 8 / yuvj420p | No HDR transfer or DV record in selected fields |
| C4 | bt709 / bt709 / smpte170m / tv | 8 / yuv420p | No HDR transfer or DV record in selected fields |

Both C2 files have DV flags RPU=1, enhancement layer=0, base layer=1.
Rotation is the signed ffprobe display-matrix value; 0 means no rotation side
data was reported. Rate columns are exact header fractions, nominal `r_frame_rate`
and average `avg_frame_rate`; they need not be identical.
Quoted major-brand strings preserve padding: `"qt  "` has two trailing spaces.

| File | Major brand (ftyp) | Dimensions | Colour | Nominal fps | Average fps | Rotation |
|---|---|---|---|---|---|---:|
| `dp_color_video_1791675261.mp4` | `"mp42"` | 1920x1080 | C4 | 30/1 | 198300/6611 | 0 |
| `IMG_6702.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -180 |
| `IMG_6704.MOV` | `"qt  "` | 1920x1080 | C2 | 30/1 | 30/1 | 0 |
| `IMG_6716.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6717.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6727.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6728.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6729.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6731.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6733.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6734.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6735.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6736.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6738.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6741.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6742.MOV` | `"qt  "` | 1920x1440 | C1 | 30000/1001 | 60600/2021 | -90 |
| `IMG_6745.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | -90 |
| `IMG_6760.MOV` | `"qt  "` | 1920x1440 | C1 | 30/1 | 30/1 | 0 |
| `IMG_6762.MOV` | `"qt  "` | 1920x1080 | C3 | 30/1 | 30/1 | 90 |
| `IMG_6772.MOV` | `"qt  "` | 1920x1080 | C2 | 30/1 | 99225/3308 | -180 |

### Video edit lists as written: DR-15 input

Every video has exactly one version-0 video-track `elst` segment, rate 1.
Duration is in movie time-scale ticks; `media_time` is in video media ticks.
Scales and integer entries below are raw file values, not normalized or
reconstructed from presentation timestamps. Seconds = duration / movie scale.

| File | Movie scale | Video scale | Segment count | Segment duration | media_time | has_b_frames | ctts version | Signed offset min..max | Negative offsets |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| `dp_color_video_1791675261.mp4` | 600 | 600 | 1 | 26444 | 0 | 0 | absent | not stored | no (no ctts) |
| `IMG_6702.MOV` | 600 | 600 | 1 | 300 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6704.MOV` | 600 | 600 | 1 | 319 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6716.MOV` | 600 | 600 | 1 | 500 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6717.MOV` | 600 | 600 | 1 | 300 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6727.MOV` | 600 | 600 | 1 | 300 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6728.MOV` | 600 | 600 | 1 | 419 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6729.MOV` | 600 | 600 | 1 | 1680 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6731.MOV` | 600 | 600 | 1 | 1260 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6733.MOV` | 600 | 600 | 1 | 2960 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6734.MOV` | 600 | 600 | 1 | 979 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6735.MOV` | 600 | 600 | 1 | 2099 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6736.MOV` | 600 | 600 | 1 | 2060 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6738.MOV` | 600 | 600 | 1 | 979 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6741.MOV` | 600 | 600 | 1 | 3460 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6742.MOV` | 600 | 600 | 1 | 2021 | 0 | 2 | 0 | -40..61 | yes |
| `IMG_6745.MOV` | 600 | 600 | 1 | 639 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6760.MOV` | 600 | 600 | 1 | 3160 | 0 | 2 | 0 | -40..60 | yes |
| `IMG_6762.MOV` | 44100 | 2400 | 1 | 33032370 | 0 | 2 | 0 | -160..240 | yes |
| `IMG_6772.MOV` | 600 | 600 | 1 | 26463 | 0 | 2 | 0 | -41..61 | yes |

Composition-offset units are video media ticks. All 19 MOVs have `ctts`
version 0, not version 1. Their high-bit offset words are large unsigned
values under the version-0 field definition, but ffprobe interprets them as
signed 32-bit values, including negatives. The table explicitly gives that
signed interpretation; it does not relabel the stored version. The probe JSON
retains the version-defined min/max and the signed min/max separately.
A separate selected ffprobe trace agreed with the raw parser's entry counts,
sample counts and signed offset ranges for every MOV. For `IMG_6702.MOV`,
raw offsets include `4294967256` and `4294967276`; ffprobe reports `-40` and
`-20`, respectively. No whole trace or unselected metadata was written.
The mp4 has no `ctts` box and reports no B-frame reordering.

**DR-15:** no MOV in this set carries a non-zero video `media_time`.
All 19 MOVs report `has_b_frames=2` and negative signed composition offsets,
but write `media_time=0`; the mp4 also writes 0. This set
therefore does not supply the hypothesized non-zero as-written edit example,
and does not resolve the broader encoder-reorder convention question.
`IMG_6762.MOV` has the distinctive scales 44100/2400 and duration 33032370
movie ticks (749.033333... s), still `media_time=0`.

For a simple hand check, `IMG_6702.MOV` has one segment, duration 300 movie
ticks, media_time 0, both scales 600, rate 1. Its raw `elst` payload is
`00000000000000010000012c0000000000010000`.
Note: ffprobe `-show_entries` JSON does not expose raw `elst` entries; the
product box parser reads them. Selected ffprobe start/rate facts cannot by
themselves verify the as-written edit list. An independent direct byte parse
of this payload agreed with the product-parser result.

### (a) Above-surface candidates

None can be named from the selected tags. Those tags describe the camera,
encoding and colour treatment, not whether a scene is above water. All 93
files remain undecided on this question. Leave the identification to WP3.6P
and the owner; no pixels or frames were inspected.

### (b) Pre-corrected candidates

Tag-supported candidates, not proof of underwater colour correction:

- `IMG_6791.JPG`, `IMG_6793.JPG`, `IMG_6794.JPG`, `IMG_6795.JPG`,
  `IMG_6798.JPG`, `IMG_6799.JPG`, `IMG_6800.JPG`, `IMG_6801.JPG`,
  `IMG_6802.JPG`: all nine carry EXIF sRGB with no ICC, in contrast to the
  Apple/P3-tagged photos. Eight have NUL-filled camera/editor strings (group Z);
  `IMG_6794.JPG` lacks those tags entirely (group M). This supports an export
  or metadata-stripping history as a candidate explanation. No surviving
  Software tag names an editor or proves what adjustment occurred.
- `dp_color_video_1791675261.mp4`: selected camera/Software/encoder tags are
  absent; MP4/H.264, limited range, bt709 primaries/transfer and smpte170m matrix
  differ from the Apple-tagged HEVC MOVs. This supports treating it as a
  processing/export candidate; the evidence does not identify an app or prove
  correction. The filename alone is not evidence.

The supplied prior is thus supported as a candidate list for the nine existing
JPGs in that number interval and the one mp4, but cannot be proved as a claim
that they are corrected. The other photos and MOVs retain Apple tags with
Software `26.6.2`; this supplies no affirmative editor evidence and also does
not prove they are untouched. No additional candidate is established by the
selected tags.

### DR-7

All 62 HEICs have EXIF `Make=Apple`; no non-Apple HEIC was found, so the stated
DR-7 trigger is absent. Primary `irot` and present EXIF rotations agree:
180/3 (20), 90/8 (3), 270/6 (16). The remaining 23 have identity `irot=0`
and absent EXIF orientation. DR-7 remains a tool limit, without a new trigger;
DR-6 also remains unchanged.

## 11. Method and checks

The committed evidence script selects only the permitted scalar tags and
format facts. Pillow/pillow-heif opens photo headers without loading pixels;
primary HEIF property associations supply `ispe`, `irot` and `nclx`. The script
reuses inventory helpers and the product box reader's bounded parsing helpers
for the first video track, including `ctts` version, bounded entry counts and
offset ranges, without interpreting other metadata payloads. The tag allowlist
is unchanged; composition-table integers are the only additional selection.
ffprobe uses an explicit `-show_entries` allowlist, no frame or packet scan.
The script records the exact allowlist. Source paths come from the unchanged
local config; the script fences its output to this worktree's `work/`.

```powershell
uv run python docs/reports/inventory-2026-10-29-probe.py
```

Exit 0: `Selected headers: 93; output: work/inventory-1029/phone-probe.json`.
The supplemental Phone-only probe was rerun for the new composition facts;
all previously selected Phone facts match its prior output exactly. The
inventory CSV/summary remain the original 17:17:52Z snapshot.
The script and final JSON use ASCII and LF. md5s (current tool includes the
new exclusion option):

| Evidence | md5 |
|---|---|
| `tools/inventory.py` | `aa0072b5f33590b50f6e650870dbf8a4` |
| `docs/reports/inventory-2026-10-29-probe.py` | `7b6fe2905575881c71a48d10c85ab24a` |
| `work/inventory-1029/phone-probe.json` | `9c5c2391dcf8c4291b95e68bfcaddbef` |

The script checksum is of the LF bytes to be committed. Case-insensitive
privacy grep over both the complete probe JSON and the committed report:
**0 hits in each**. The literal required pattern and results are saved in
`work/inventory-1029/privacy-check.log`. Equivalent executable spelling below
avoids matching the check's own documentation:

```powershell
rg -n -i 'G[P]S|x[y]z|loc[a]tion|Lat[i]tude|Long[i]tude' work/inventory-1029/phone-probe.json docs/reports/inventory-2026-10-29.md
```

No matches means rg exit 1. Other checks:

- `uv run ruff check .`: exit 0, all checks passed, including the evidence script.
- `uv run ruff format --check .`: exit 0, 268 files already formatted.
- `uv run mypy`: exit 0, no issues in 141 source files (configured product/tools
  scope; the evidence script is outside that scope).
- Source-row comparison: 35 old rows, 35 current non-Phone rows, 0 differences.
- Phone coverage: 93 unique probe rows, matching the CSV's 93 Phone names.
- Verification pass 1: suspected missing JPG tags were confirmed as actual
  NUL-filled values by a separate selected EXIF read, not treated as editor
  names. Suspected non-zero MOV media_time was rejected: all are 0; a direct
  independent byte parse of `IMG_6702.MOV` confirmed count/duration/media_time.
  A probe lint issue was fixed before the passing gate. No product fix arose.
- Verification pass 2: the report/probe snapshot agrees on primary dimensions,
  group counts, raw edits and candidate names; ASCII/LF and privacy checks passed.
  The historical whole-tree stability failure concerned the separate arriving
  input. The later formal ruling `0fd08f9f` supersedes the earlier snapshot-only
  direction: exclude that folder and assert stability on the included tree.
- Verification pass 3: supplemental Phone facts unchanged; all 19 MOV brands
  recorded per file, `has_b_frames` beside `media_time`, and `ctts` version and
  negative signed offsets independently confirmed against selected ffprobe
  traces. Final script lint/format and report/probe privacy checks pass; no
  new unresolved in-commission finding. The historical test failure is retained,
  not represented as a pass. Independent orchestrator checks and CHARC QA
  remain the acceptance step.
- Verification pass 4: `--exclude` RED failed on the unrecognized argument;
  GREEN passed all 143 selected inventory tests (1 deliberately deselected).
  The regression checks traversal is pruned, all other rows remain identical,
  nested same-name folders stay included, and excluded ignored/sidecar files
  do not enter counts. The real excluded re-run has 128 identical rows and
  unchanged included-folder stats. Five direct source spot checks passed;
  final privacy checks found no hits. No unresolved in-envelope finding.

Runner logs: `work/inventory-1029/inventory-run.log`, `phone-probe-run.log`,
`pytest.log`, `pytest-direct.log`, `ruff-check.log`, `ruff-format-check.log`, `mypy.log`,
`independent-checks.log`, `privacy-check.log` (all under the same arc folder).
Final supplemental logs: `phone-probe-run-turn3.log`, `probe-ruff-turn3.log`,
`probe-format-turn3.log`, `verify-ctts-all.log`; selected numeric trace evidence
is `ctts-trace-check.json`, also under `work/inventory-1029/`.
Final script checks: `uv run ruff check docs/reports/inventory-2026-10-29-probe.py`
and `uv run ruff format --check docs/reports/inventory-2026-10-29-probe.py`,
both exit 0.
The Turn-4 inventory test-file command (the historical whole-footage test is
explicitly deselected, not rerun):

```powershell
$env:PYTHONPATH='scripts'
uv run pytest -q -rs --basetemp=work/inventory-1029/pt-exclude-green -p sandbox_mkdir_shim -p no:cacheprovider tests/test_inventory.py -k 'not test_real_footage_has_one_row_per_media_file'
```

Exit 0: `143 passed, 1 deselected in 23.28s`. RED for the new named regression
was `1 failed, 143 deselected in 0.52s`, with `unrecognized arguments: --exclude
insta360`. Logs: `exclude-red.log`, `exclude-green.log`. The file is unchanged
at its historical whole-footage test; only the new exclusion regression was
added. Light gates re-run after the tool change: `uv run ruff check .`,
`uv run ruff format --check .` and `uv run mypy`, all exit 0 (268 files formatted;
141 source files without type issues). Logs: `ruff-check-turn4.log`,
`ruff-format-turn4.log`, `mypy-turn4.log`. No full suite or whole-footage test
re-run is claimed.

Five source spot checks were performed by this cell:

| File under Phone | Source facts checked | Result |
|---|---|---|
| `IMG_6690.HEIC` | 5712x4284; primary irot 180; EXIF 3; Apple / iPhone 15 Pro / 26.6.2; Display P3 ICC | Pass |
| `IMG_6703.HEIC` | 4032x3024; primary irot 0; EXIF absent; same camera/software/profile tags | Pass |
| `IMG_6791.JPG` | 3213x5712; Make/Model/Software are 5/13/6 NULs; ColorSpace 1; no ICC | Pass |
| `IMG_6702.MOV` | Independent direct byte parse: elst v0, one segment, duration 300, media_time 0, rate 1; raw payload matches section 10 | Pass |
| `dp_color_video_1791675261.mp4` | Direct selected ffprobe: mp42; H.264 1920x1080; has_b_frames 0; selected camera/software/encoder tags absent | Pass |

The HEIC checks reopen selected headers and inspect the primary property's raw
rotation byte; the JPG check reads only the permitted scalar tags. The MOV
check walks raw box spans separately from the product edit-list parser.
Spot evidence: `work/inventory-1029/five-spot-checks.json`; command:
`uv run python work/inventory-1029/five-spot-checks.py` (exit 0).
The aggregate observation and stability/identity wrapper command was
`uv run python work/inventory-1029/run-excluded.py` (exit 0); it invokes the
exact excluded inventory command in section 1, between the included-tree stat
snapshots. Its log is `work/inventory-1029/run-excluded-wrapper.log`; the actual
inventory runner output is `inventory-excluded-run.log` in that folder.

No adversarial review or ledger was run, per the authorized review form.
Authorized scope changes: output override, committed probe evidence, and the
single-name inventory exclusion plus its test (CHARC `0fd08f9f`). No other
product/tool files, dependencies, source footage or local config were changed.
The report is complete for the commissioned tree minus `Insta360/`, with the
17:17:52Z snapshot confirmed by the excluded re-run. Independent orchestrator
re-run/spot checks and CHARC QA remain the acceptance step. Insta360 scope
remains undecided; no completion-triggered re-run is commissioned for it.
