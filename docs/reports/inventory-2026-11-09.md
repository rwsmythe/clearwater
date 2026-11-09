# Real footage inventory, 2026-11-09

WP7.1, build turn 2, base `626e30f0c9e730516f612c8d00adb7f5a31e7311`.
The inventory includes the complete configured footage tree without exclusions.
Insta360 Studio HEVC exports are the product-validation scope; ProRes rows
are descriptive inventory records, not a claim of product admission.

## 1. Run

```powershell
uv run python work/wp7.1/inventory_driver.py
```

The isolated child calls `tools.inventory.main()` with
`--config clearwater.local.toml --out work/wp7.1/inventory` (absolute paths
are passed). No `--exclude` is supplied. The local configuration is unchanged.
The footage root comes from that config; the working-root override is the
authorized worktree destination. Supervisor: 1,800 s; inventory exit 0.

- Final snapshot: `20261109T063504Z` (UTC).
- ffprobe: `ffprobe version 9.0.2-full_build-www.gyan.dev Copyright (c) 2007-2026 the FFmpeg developers`.
- Evidence paths are relative to this worktree; `work/` is gitignored.

| Evidence | md5 |
|---|---|
| `work/wp7.1/inventory/reports/inventory-20261109T063504Z.csv` | `03f302a6f98fef2ae49ce073aa3bca45` |
| `work/wp7.1/inventory/reports/inventory-20261109T063504Z-summary.md` | `6cc84083526ade2ee99f2008dd086b08` |
| `work/wp7.1/inventory/reconciliation.json` | `7bbb6028750a1f940612c40b0ade2430` |

## 2. Counts per folder

| Folder | Videos | Photos | Files | Size (bytes) | Duration (s) |
|---|---:|---:|---:|---:|---:|
| `Snorkel/` | 26 | 0 | 26 | 5,058,259,868 | 1694.493 |
| `SCUBA/` | 8 | 0 | 8 | 24,122,034,711 | 2889.353 |
| `edits/` | 1 | 0 | 1 | 318,648,117 | 179.930 |
| `Phone/` | 20 | 73 | 93 | 1,359,540,146 | 876.269 |
| `Insta360/` | 7 | 0 | 7 | 224,253,936,407 | 7779.077 |
| Total | 62 | 73 | 135 | 255,112,419,249 | 13419.122 |

Compared with [2026-10-29](inventory-2026-10-29.md#2-counts-per-folder),
Snorkel, SCUBA, edits and Phone have unchanged video/photo counts, total
bytes and summed durations. Insta360 adds seven videos and 224,253,936,407
bytes. Total rows increase from 128 (55 videos, 73 photos) to 135
(62 videos, 73 photos). The historical CSV is not present in this worktree:
this is aggregate reconciliation, not a complete historical row-identity or
payload-checksum assertion.

## 3. Recording modes (tool summary)

Width x height @ frame rate, codec, bit depth, chroma format (files without errors).

- 3840x2160 @ 29.97 hevc 8-bit 4:2:0: 38
- 1920x1440 @ 30 hevc 8-bit 4:2:0: 15
- 3840x2160 @ 29.97 prores 10-bit 4:2:2: 3
- 1920x1080 @ 29.995 h264 8-bit 4:2:0: 1
- 1920x1080 @ 29.995 hevc 10-bit 4:2:0: 1
- 1920x1080 @ 30 hevc 10-bit 4:2:0: 1
- 1920x1080 @ 30 hevc 8-bit 4:2:0: 1
- 1920x1080 @ 59.94 h264 8-bit 4:2:0: 1
- 1920x1440 @ 29.985 hevc 8-bit 4:2:0: 1

Variable frame rate: 0

The VFR figure is the inventory's header-rate heuristic, not a full timing
acceptance result. Photos remain HEIF 62 and JPEG 11; dimensions and
orientation facts are carried by reference to the previous report.

## 4. Chaptered recordings

None in the current tool summary. GoPro coverage is unchanged by count;
see [2026-10-29, section 4](inventory-2026-10-29.md#4-chaptered-recordings).
Insta360 files have no GoPro recording/chapter fields.

## 5. Error rows and skipped files

The tool reports zero probe errors, ignored files, sidecars, AppleDouble
files and skipped entries. Every recognized media file has exactly one CSV
row: 0 duplicates, 0 missing media and 0 extra rows. All seven exact
Insta360 names match the brief. Inventory success does not prove complete
payload integrity or product codec support.

## 6. Uncovered GoPro names

The previous 21 video names outside GoPro naming remain covered by the
[previous report](inventory-2026-10-29.md#6-uncovered-gopro-names). Seven
Insta360 exports add seven names without GoPro chapter fields (28 total).
No .LRV coverage: 0 of 62 videos.

## 7. Notes and scope

Insta360 exports are flat 3840x2160 at nominal 30000/1001 fps, BT.709
tagged, with AAC audio. The owner reports stabilization on, Studio H.265
export near 71-73 Mbps for the main three MP4s, no ProRes bitrate control,
and camera mode 'HDR video'. Those statements are owner input, not
facts established by this inventory. The seventh MP4 is a second, lower
bitrate export, inventoried and probed only. Native .insv is out of scope.

## 8. Instrument validation in this turn

The original wrapper import failed because the tools directory was absent
from PYTHONPATH; the bootstrap was corrected. Its next scan completed,
but wrapper reconciliation needed `utf-8-sig` for the CSV's BOM. The final
scan and reconciliation exited 0. These were driver issues; product and
inventory-tool code were not changed. The earlier CSVs and diagnostic logs
remain under `work/wp7.1/`.

No pytest, export, timing leg, frozen build or GUI was run. Report-only
accept checks and independent reviews remain at the orchestrator's seat.
Local static checks exited 0: `uv run ruff check .` (all checks passed),
`uv run ruff format --check .` (337 files already formatted), and both
`uv run mypy` and `uv run mypy --platform darwin` (166 source files each).
Logs are `logs/repo-ruff.log`, `repo-format.log`, `repo-mypy-win.log` and
`repo-mypy-darwin.log` beneath the package work area. No harness result is
claimed for this build turn.

## 9. Owner category attribution

Insta360 is SCUBA by the owner's category ruling. Phone and GoPro
categories remain by reference to the previous inventory and owner records.
The raw inventory tool deliberately leaves category cells blank; this
report does not rewrite them or infer per-file scene categories.

## 10. Phone

Unchanged aggregate counts, bytes and duration: 20 videos, 73 photos,
1,359,540,146 bytes and 876.269 s. See
[2026-10-29, section 10](inventory-2026-10-29.md#10-phone) for selected
header facts, the two HLG refusals and the raw-EXIF correction. Those
supplemental checks were not repeated here. Historical per-row identity
is not claimed.

## 11. Insta360

All rows below are from the new inventory. Category: SCUBA (owner).
All dimensions: 3840x2160; nominal rate: 30000/1001; rotation: 0.

| File | Bytes | Duration (s) | Codec/profile | Pixel format | Depth/chroma | Range |
|---|---:|---:|---|---|---|---|
| `SCUBA vids 2.mov` | 4,147,033,418 | 61.795 | prores / Standard | `yuv422p10le` | 10-bit / 4:2:2 | tv |
| `SCUBA vids 3.mov` | 28,688,898,652 | 438.905 | prores / Standard | `yuv422p10le` | 10-bit / 4:2:2 | tv |
| `SCUBA vids 3.mp4` | 3,902,405,419 | 438.906 | hevc / Main | `yuvj420p` | 8-bit / 4:2:0 | pc |
| `SCUBA vids(1).mov` | 152,128,238,670 | 2259.224 | prores / Standard | `yuv422p10le` | 10-bit / 4:2:2 | tv |
| `SCUBA vids(1).mp4` | 20,658,042,496 | 2259.226 | hevc / Main | `yuv420p` | 8-bit / 4:2:0 | tv |
| `SCUBA vids.mp4` | 14,161,538,465 | 2259.226 | hevc / Main | `yuv420p` | 8-bit / 4:2:0 | tv |
| `SCUBA vids2.mp4` | 567,779,287 | 61.795 | hevc / Main | `yuvj420p` | 8-bit / 4:2:0 | pc |

All seven carry `bt709` primaries / transfer / matrix and one AAC audio
stream; no data stream is recorded. Raw track roster and exact average rates:

| File | Tracks | Exact average frame rate | Product probe |
|---|---|---|---|
| `SCUBA vids 2.mov` | `0:video:prores;1:audio:aac` | `30000/1001` | SCUBA vids 2.mov uses the codec prores; H.265 and H.264 only. |
| `SCUBA vids 3.mov` | `0:video:prores;1:audio:aac` | `30000/1001` | SCUBA vids 3.mov uses the codec prores; H.265 and H.264 only. |
| `SCUBA vids 3.mp4` | `0:video:hevc;1:audio:aac` | `394620000/13167167` | accepted |
| `SCUBA vids(1).mov` | `0:video:prores;1:audio:aac` | `30000/1001` | SCUBA vids(1).mov uses the codec prores; H.265 and H.264 only. |
| `SCUBA vids(1).mp4` | `0:video:hevc;1:audio:aac` | `677090000/22592259` | accepted |
| `SCUBA vids.mp4` | `0:video:hevc;1:audio:aac` | `677090000/22592259` | accepted |
| `SCUBA vids2.mp4` | `0:video:hevc;1:audio:aac` | `27780000/926927` | accepted |

Product refusal kind for every ProRes file is `unsupported`, before pixel
format admission. No decode path is chosen for them. This is the expected
spec 5.2 restriction; Studio's H.265 export is the supported input path.
The four HEVC probes are accepted with no faults. The two yuvj420p files
resolve to full range; the other two resolve to limited. The probe
driver records software and requested-CUDA commands; only the selected
software decode is exercised by this turn's frame check. CUDA execution
and end-to-end validation are not claimed by the inventory.

## 12. Method, reconciliation, checks and limits

`tools/inventory.py` is unchanged. It recursively reads selected headers,
sorts relative paths and keeps error rows. The driver invokes the actual
CLI function; it does not filter an already scanned tree or fabricate rows.
Its independent stat walk captures `(st_size, st_mtime_ns)` for every
descendant entry before and after the scan; no entries changed.
The root's own metadata and access times are not part of that comparison.
No source payload checksums were taken and no media was copied.

Evidence includes `inventory/source-before.json`, `source-after.json`,
`reconciliation.json`, `probe/results.json` and the per-source probe records
beneath `work/wp7.1/`. Python roots are redirected under `roots/<run>`
before product imports; PySide6/shiboken6 are blocked in the parent and
in inherited `sitecustomize` in Python children. Per-PID guard proofs and
finite-deadline supervisor records are retained. A disposable stub proved
that nested Python children load the block and that timeout cleanup kills
only the supervised tree; its record is `logs/isolation-check.json`.

The verification loop confirmed and fixed the two wrapper issues above;
the final inventory pass found no unresolved coverage, stat-stability or
aggregate-count mismatch. The footage, owner's profile, local config,
product, tools, tests and dependencies remain unchanged. Only this report
is a committed-file candidate. No complete WP7.1 acceptance is claimed.
