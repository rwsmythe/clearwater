# Real footage inventory, 2026-10-18

Brief: `docs/briefs/inventory-pass-brief.md` (FINAL `cea7170`). Spec v0.5.2. No code changed; no category assigned.

## 1. Run

- Command: `uv run python tools/inventory.py` (worktree `.worktrees/inventory`, PATH with the WinGet `ffprobe`). Exit 0.
- Tool commit: `tools/inventory.py` last changed at `e930685`; worktree head `cea7170`.
- Run time: 2026-10-18 23:55:54 UTC (stamp `20261018T235556Z`).

| Output | md5 |
|---|---|
| `C:\Users\rwsmy\clearwater\work\reports\inventory-20261018T235556Z.csv` | `d86ed6bd071312d5f67540766f4e5edb` |
| `C:\Users\rwsmy\clearwater\work\reports\inventory-20261018T235556Z-summary.md` | `e47d41c0a738f77e01cbe2869ebd172e` |

## 2. Counts per folder

The per-folder figures are summed from the CSV (the tool's summary is not split by folder). Duration is the sum of `duration_seconds`.

| Folder | Files | Size (bytes) | Duration |
|---|---|---|---|
| `Snorkel/` | 26 | 5,058,259,868 | 1694.5 s (28.2 min) |
| `SCUBA/` | 8 | 24,122,034,711 | 2889.4 s (48.2 min) |
| `edits/` | 1 | 318,648,117 | 179.9 s (3.0 min) |
| Total | 35 | 29,498,942,696 | 4763.8 s |

The folder is `edits` (lowercase) on disk and in the CSV `path` column, not `Edits` as the brief writes it.

## 3. Recording modes (tool summary, quoted)

Counts: Videos 35, Photos 0, probe errors 0, ignored 0, sidecars 0, skipped 0.

```
- 3840x2160 @ 29.97 hevc 8-bit 4:2:0: 34
- 1920x1080 @ 59.94 h264 8-bit 4:2:0: 1
Variable frame rate: 0
```

Per folder, from the CSV: `Snorkel` 26 and `SCUBA` 8 are all 3840x2160 @ 29.97 hevc 8-bit 4:2:0. `edits` 1 is 1920x1080 @ 59.94 h264 8-bit 4:2:0. Every file has color tags bt709 / bt709 / bt709, range `pc`, rotation 0. No file carries an HDR or Log tag (the tags are the plain bt709 set). Container for all: `mov,mp4,m4a,3gp,3g2,mj2`. The GoPro files carry four tracks (video hevc, audio aac, two data tracks).

## 4. Chaptered recordings

Tool: "Chaptered recordings ... none". Every GoPro file is chapter 1 (`GX01xxxx`); no `GX02xxxx` exists.
- `Snorkel/`: recordings 1603 to 1628, one chapter each (26).
- `SCUBA/`: recordings 1589, 1590, 1591, 1592, 1593, 1598, 1600, 1601, one chapter each (8).
- Files are lowercase `.mp4`.

## 5. Error rows and skipped files

None. Zero rows with `error` set; zero skipped.

## 6. Uncovered GoPro names

One: `edits/compilation-20261010-1080p60.mp4` (empty `gopro_recording` and `gopro_chapter`). All 34 other files follow the GoPro scheme.

## 7. Notes

- **No `.LRV`/`.THM`:** the column is all-absent (0 of 35), not a gap (owner, 2026-10-15).
- **Photos are PENDING, not absent.** The owner will add stills later. The photo column is empty today; the photo-side checks (the largest photo in Part B, the iPhone HEIC path) stay queued, not dropped.
- **The Edits clip:** `edits/compilation-20261010-1080p60.mp4` is 318,648,117 bytes, H.264 1920x1080 at 59.94 (CSV `59.9401`), 179.9 s. It is a non-GoPro-named compilation with hard scene transitions, renamed by the owner from a misnamed `.json`. The owner keeps it on purpose as a smoothing stress case, for a later WP and not Part B.
- **Folder totals:** 35 files as expected (`Snorkel` 26, `SCUBA` 8, `edits` 1). The tool treats the `edits/` folder like the others: it is scanned and probed as a normal video row. The only difference is the non-GoPro name, which yields empty recording and chapter fields and no `.LRV` lookup result beyond `false`.

## 8. WP0.2 footage test

`uv run pytest -q -rs --basetemp=C:\Users\rwsmy\clearwater\work\pt tests -k test_real_footage_has_one_row_per_media_file`

```
1 passed, 538 deselected, 1 warning in 12.84s
```

The one warning is CuPy's "CUDA path could not be detected", unrelated. No skip.

## 9. Nothing assigned

The CSV `category` column is empty in all 35 rows. Categories are the owner's at CP1.
