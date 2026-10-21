# WP3.12 report: proxy cache

Package `clearwater.cache` (`src/clearwater/cache/`), tests `tests/test_cache_store.py`,
`tests/test_cache_robust.py`, `tests/test_cache_jpeg.py`, instrument `tools/cache_store_test.py`.
Spec v0.5.4 (7.3, D59, D71, D95, D113; G12; V17), architecture FINAL 1.0 (IF-7, AD-5 as ruled
2026-10-20, AD-7, AD-15, AD-20, AD-25). Base `2c5540a`. Nothing under `src/clearwater/interfaces/`
was changed. The review ledger is `docs/proofs/wp3.12-ledger.md`. Figures are on disk under the
main tree's `work/wp3.12/` (gitignored): `results.json`, `readcost.json`, and `meansize.txt` and
`signed-bounds.txt`, which the instrument's `meansize` and `signed` modes write.

## Public API (what WP3.11, WP3.18, WP3.20, WP4.2 and WP4.3 consume)

All names are exported from `clearwater.cache`.

| Area | Names |
|---|---|
| The store (IF-7) | `DiskProxyCache(folder, limit_bytes=DEFAULT_CACHE_LIMIT_BYTES, *, codec=DEFAULT_CODEC, clock=time.time_ns)`; it satisfies `clearwater.interfaces.cache.ProxyCache` exactly: `lookup`, `store_proxy`, `proxy`, `store_source_statistics`, `source_statistics`, `mark_complete`, `limit_bytes`, `set_limit_bytes`, `clear` |
| Extras (not in IF-7) | `DiskProxyCache.cache_version` (property), `.key_for(path)`, `.close()`, context-manager use |
| Keys | `cache_key(path, codec=DEFAULT_CODEC) -> CacheKey`, `CACHE_FORMAT_VERSION = 1`, `codec_cache_version(codec)`, `entry_name(key)`, `parse_entry_name(name)` |
| Codecs | `ProxyCodec`, `DEFLATE` (lossless), `JPEG_Q75_444` (id 2, the default), `JPEG_Q80_420` (id 3), `CODECS`, `DEFAULT_CODEC`, `jpeg_identity()`, `round_trip(proxy, codec)` |

The class takes its folder and limit as arguments and never resolves the app-data folder (a test
monkeypatches `clearwater.config.paths.app_locations` and asserts it is not called). Production
wiring (WP4.3) passes `app_locations().cache_dir` and `Settings.cache_limit_bytes`.

## On-disk layout

One folder per key in the cache folder, named `e_<size>_<mtime_ns>_<cache_version>` (all three key
fields in the name, so a different size, modification time or version is a different folder:
`keys.entry_name`). An entry folder holds `data.pack` (32-byte header repeating the key, then
append-only records), `complete` (the completeness marker, written only by `mark_complete`) and
`meta.json` (the last-use stamp). A record is a 24-byte header (kind proxy or statistics, codec id,
pts, payload length, CRC-32 over header, stage name and payload), the stage name and the payload
(`layout.py`). There is no separate index file: the in-memory index is rebuilt by walking the record
headers the first time a key is touched in an instance. Statistics records hold name, `dtype.str`,
shape and the raw bytes of each array (no pickle).

Crash model (`store.py` module docstring): a record is appended and flushed, never synced per
record; `mark_complete` syncs the pack and then writes the marker atomically, last. A torn tail is
found by length or checksum and cut off by the next writer; an entry left by a crash has no marker
and is never complete; a damaged record is a miss (`KeyError`), never a wrong picture; `lookup`
never raises on damaged files. When the cache opens, `*.tmp` leftovers and entries of another cache
version are removed, and an entry whose pack header is unreadable or names another key is removed.

## The AD-5 measured test and the choice

Instrument: `tools/cache_store_test.py` (FFmpeg CLI through `clearwater.io.video.find_tool`, used by
the instrument only). Clips: GX011627 (shallow, all 681 frames, 4K, 30000/1001) and GX011625 (deep,
300 frames: 5 windows of 60 at 30, 130, 230, 330 and 430 s), each reduced to a 960 x 540 proxy by
the exact 4 x 4 block mean; the float proxy is `block sum / 4080` and the 8-bit proxy is
`floor((block sum + 8) / 16)`. Statistics (`prototype.temporal.measure`, c3 `Params()`, CPU) on
every 8th frame (86 and 38 frames); sizes on every frame. A size is the bytes of the stored
payload of one frame (the product adds a 24-byte record header and an 8-byte codec header per
frame; the stream candidates count packet payloads without container overhead). 60-minute figure
= frames per hour at 29.97 fps (107,892) times the frame size, shown for the median and the 95th
percentile.
"bounds" is the maximum over frames of the N{} bound deviation relative to each bound, with the
deviation relative to the bounds' range in brackets (a bound near zero makes the first ill-defined;
the deep clip's range is 0.010-0.116, median 0.033). "vs 8-bit" is the same range-relative
deviation against the 8-bit proxy. "max err" is the maximum absolute pixel error against the 8-bit
proxy, in levels, over the statistics frames only (86 and 38), not over every sized frame. Full table (all 32 candidates and sweeps): `results.json` and the instrument's
`report` mode.

| candidate | clip | KB per frame, median / p95 | 60 min GB, median / p95 | max err | means | gains | bounds vs float | bounds vs 8-bit |
|---|---|---|---|---|---|---|---|---|
| deflate-L1 (lossless) | GX011627 | 748.7 / 1119.7 | 80.8 / 120.8 | 0 | 2.7e-04 | 2.6e-05 | 1.3 % (0.5 %) | 0.0 % |
| deflate-L1 (lossless) | GX011625 | 261.4 / 457.8 | 28.2 / 49.4 | 0 | 1.9e-04 | 2.4e-06 | 6.0 % (3.1 %) | 0.0 % |
| ffv1-intra (lossless) | GX011627 | 447.4 / 758.2 | 48.3 / 81.8 | 0 | 2.7e-04 | 2.6e-05 | 1.3 % (0.5 %) | 0.0 % |
| ffv1-intra (lossless) | GX011625 | 119.0 / 228.6 | 12.8 / 24.7 | 0 | 1.9e-04 | 2.4e-06 | 6.0 % (3.1 %) | 0.0 % |
| utvideo-median (lossless) | GX011627 | 550.1 / 820.7 | 59.4 / 88.5 | 0 | 2.7e-04 | 2.6e-05 | 1.3 % (0.5 %) | 0.0 % |
| utvideo-median (lossless) | GX011625 | 237.6 / 328.5 | 25.6 / 35.4 | 0 | 1.9e-04 | 2.4e-06 | 6.0 % (3.1 %) | 0.0 % |
| x264rgb-intra-crf22 | GX011627 | 88.6 / 156.8 | 9.6 / 16.9 | 81 | 1.9e-03 | 6.5e-04 | 15.0 % (8.9 %) | 8.7 % |
| x264rgb-intra-crf22 | GX011625 | 22.3 / 45.8 | 2.4 / 4.9 | 35 | 4.6e-04 | 4.2e-05 | 24.3 % (12.7 %) | 14.1 % |
| mjpeg-444-q4 | GX011627 | 86.3 / 175.2 | 9.3 / 18.9 | 43 | 1.9e-03 | 1.7e-03 | 11.2 % (6.6 %) | 6.4 % |
| mjpeg-444-q4 | GX011625 | 13.1 / 30.2 | 1.4 / 3.3 | 36 | 1.8e-03 | 1.6e-03 | 18.7 % (10.1 %) | 10.5 % |
| jpeg-q85-444 | GX011627 | 116.6 / 216.2 | 12.6 / 23.3 | 45 | 6.9e-04 | 1.9e-04 | 12.4 % (5.1 %) | 4.5 % |
| jpeg-q85-444 | GX011625 | 22.9 / 48.7 | 2.5 / 5.3 | 25 | 7.1e-04 | 3.2e-04 | 21.5 % (11.1 %) | 8.0 % |
| jpeg-q80-444 | GX011627 | 97.4 / 181.9 | 10.5 / 19.6 | 52 | 8.8e-04 | 1.9e-04 | 14.0 % (5.7 %) | 5.2 % |
| jpeg-q80-444 | GX011625 | 18.3 / 39.5 | 2.0 / 4.3 | 39 | 8.7e-04 | 3.1e-04 | 20.7 % (10.0 %) | 7.6 % |
| **jpeg-q80-420** | GX011627 | 78.2 / 148.6 | 8.4 / 16.0 | 89 | 8.2e-04 | 2.8e-04 | 11.9 % (4.9 %) | 4.5 % |
| **jpeg-q80-420** | GX011625 | 14.4 / 33.6 | 1.6 / 3.6 | 40 | 9.5e-04 | 4.1e-04 | 20.8 % (10.3 %) | 7.8 % |
| **jpeg-q75-444 (default)** | GX011627 | 83.8 / 157.2 | 9.0 / 17.0 | 61 | 9.0e-04 | 3.6e-04 | 16.1 % (6.5 %) | 6.0 % |
| **jpeg-q75-444 (default)** | GX011625 | 15.1 / 33.1 | 1.6 / 3.6 | 36 | 8.8e-04 | 6.6e-04 | 22.3 % (10.5 %) | 8.3 % |
| jpeg-q70-444 | GX011627 | 75.1 / 140.9 | 8.1 / 15.2 | 66 | 1.4e-03 | 5.1e-04 | 18.6 % (7.7 %) | 7.2 % |
| jpeg-q70-444 | GX011625 | 13.4 / 29.4 | 1.4 / 3.2 | 40 | 1.9e-03 | 8.7e-04 | 31.6 % (15.6 %) | 12.9 % |

What the figures say, as measured:

1. **No lossless candidate fits 10 GB** (best, FFV1: 48.3 GB on the shallow clip at the median).
2. **No 8-bit store, lossless or not, meets AD-5's original 1 % N{} bounds criterion against the
   float proxy**: the lossless rows (max err 0) already deviate 6.0 % per bound on the deep clip. AD-5
   was ruled accordingly on 2026-10-20 (the analysis proxy IS the stored, decoded proxy; criteria:
   means and gains within 1e-3 against the float proxy, the bounds deviation beyond the 8-bit floor
   reported). Against those: jpeg-q75-444 means 9.0e-04 and gains 6.6e-04 (met); the range-relative
   bounds deviation beyond the 8-bit floor is 6.0 % (shallow) and 8.3 % (deep) (under the ruled
   10 %). q80-420: 4.5 % and 7.8 %.
3. **Size against the 10 GB figure.** CHARC ruled (2026-10-21) that the 10 GB figure is a cache
   sizing target read on the MEDIAN frame size: 9.0 GB per hour for q75-444 and 8.4 GB for q80-420
   on the shallow clip. The whole-clip MEAN, computed with the product codecs over all 681 frames
   (`meansize.txt`), is 10.2 GB for q75-444 and 9.7 GB for q80-420; at the 95th percentile the
   shallow clip is 17.0 and 16.0 GB, and the deep clip gives 2.0 and 1.9 GB by the mean. These are
   recorded, not a failure: the user-facing limit is D71's 20 GB with oldest-first eviction. The
   shallow clip is 22.7 s of one dive site, so all of this is a sample, not a statement about an
   hour of footage.
4. **The bounds change has either sign.** AD-5's ruling text says the stored proxy's N{} bounds
   are narrower than the float proxy's. A signed check (`signed-bounds.txt`, every 2nd statistics
   frame: 43 shallow, 19 deep, c3, CPU) of the bounds RANGE of the decoded q75-444 proxy against
   the float proxy shows: shallow median +0.9 %, min -0.9 %, max +7.6 % (7 of 43 negative); deep
   median +2.9 %, min -3.5 %, max +19.8 % (9 of 19 negative). The 8-bit proxy alone moves the range
   by at most +0.4 % (shallow) and +5.6 % (deep). CHARC ruled (2026-10-21): the range differs by
   up to 10 % of the range beyond the 8-bit floor, of either sign, the median slightly wider, so
   the AD-4 floor (DR-14) binds slightly less often; AD-5's wording is to be amended on main. The
   figures are information for CP5; nothing in the code depends on the direction.

**The CP5 line** (to be shown to the owner, as AD-5 requires): "the stored analysis proxy's
normalisation bounds differ from the float proxy's by up to 6.5 % of the range on shallow footage and
10.5 % on deep footage (JPEG q75 4:4:4; 6.0 % and 8.3 % beyond the 8-bit step alone), with mixed sign
and a median change of +1 % to +3 % in the range; on top of AD-4's 11-14 % narrowing from the 540
downscale itself". The AD-4 11-14 % is quoted from AD-4 (WP1.2B claim 6), not measured here.

### Read cost (the EXCLUSIVE row, run by the orchestrator, not by this cell)

`DiskProxyCache.proxy()` = file read + CRC + decode, 25 evenly spaced proxies of GX011627 read 8
rounds (200 reads), file in the OS cache, nothing else heavy running. Dispatcher's record:
`uv run python tools/cache_store_test.py readcost-product` at `82a5dbb`, 2026-10-21
00:20:39-00:20:45Z (the file's own local-time stamp reads `2026-10-20T14:20:44`); output
`work/wp3.12/readcost.json`.

| codec | median ms | p95 ms | max ms | KB per frame (25 frames) |
|---|---|---|---|---|
| deflate (lossless, product) | 8.47 | 10.26 | 15.80 | 797.3 |
| JPEG q75 4:4:4 (default) | 3.39 | 4.27 | 10.22 | 94.0 |
| JPEG q80 4:2:0 | 3.08 | 4.47 | 9.90 | 88.9 |

q80-420 is 9.0 % faster at the median than q75-444, under CHARC's 30 % threshold, so JPEG q75
4:4:4 stays `DEFAULT_CODEC` (the ruling is final; no code change). The 25-frame sample's mean size
(94.0 KB) is consistent with the whole-clip mean of 94.9 KB in finding 3.

### The choice and its conditions (AD-5 as ruled)

`DEFAULT_CODEC = JPEG_Q75_444`: 540 short side, 8-bit, quality 75, 4:4:4, baseline with optimised
Huffman tables (`codec.py`). The four conditions as met on disk: (1) the codec as above; (2) determinism:
`codec_cache_version` = format number `<< 48` | the first 48 bits of the SHA-256 of the codec id and
identity, where the JPEG identity is the Pillow, libjpeg and libjpeg-turbo versions read at runtime
(`codec.jpeg_identity`), so a different decoder gives a different key and the old entries are
removed when the cache opens (`tests/test_cache_jpeg.py::test_a_different_decoder_identity_invalidates_the_cache`);
(3) the criteria and the CP5 line above; (4) Pillow is in `[project] dependencies` (commit `a21a738`,
`pillow>=11,<13`; X-B3: whichever of WP3.6 and WP3.12 merges second re-locks `uv.lock`).

## Eviction rule (D71)

Oldest by LAST USE: a `lookup` hit and `mark_complete` refresh an entry's stamp (`meta.json`, from an
injectable clock); per-record stores and reads do not. Order: smallest stamp first, ties by key
(`store._eviction_key`). Unit: a whole entry; size = bytes on disk of the cache's own files
(`data.pack`, `complete`, `meta.json`), the sum in `size_bytes`. Trigger: after every store, in
`mark_complete`, in `set_limit_bytes` and when the cache opens. Never evicted: the entry of the store
call in progress, the entry stored to last and the entry last found by `lookup`; if those alone
exceed the limit the cache keeps them, evicts everything else, logs one warning on
`logging.getLogger("clearwater.cache")` per transition into that state, and storing continues. A
negative limit is refused. Deletion removes only files the cache names, only as regular files, never
following a link or junction (`store._remove_files`); a foreign file keeps its folder in place.
The default limit is `DEFAULT_CACHE_LIMIT_BYTES` (imported, not restated).

## Differences between the stub and the product (WP3.11 consumer notes)

- `mark_complete` on a key with nothing stored: the stub accepts it silently, the product raises
  `KeyError`.
- Measure statistics on the proxy AS STORED, on the first pass and on reopen alike: at first analysis
  call `clearwater.cache.round_trip(proxy)` (or `store_proxy` then `proxy`) BEFORE any statistic is
  measured; the float proxy is never a statistics source (AD-5 ruling). A re-store of byte-identical
  data is skipped.
- `lookup` returns in-progress entries (AD-15: their proxies are readable); skip the decode pass only
  when `complete` is True.
- Storing a NEW or CHANGED proxy into a complete entry removes the marker first, so the entry is
  incomplete again and `mark_complete` must be called again; storing statistics never changes it.
- A second store call on a key while another is still running (statistics stores and `mark_complete`
  included) is a `RuntimeError` (overlap in time, not thread ownership); readers on other threads are
  unaffected.
- A key must carry the instance's own cache version: derive it with `DiskProxyCache.key_for(path)` or
  `cache_key(path, codec)`; `store_*` with another version is a `ValueError`, and `lookup` of one
  returns None. Because the version folds in the JPEG library identity, a key made on another machine or
  after a library change will not find these entries.
- `stages` lists only stages whose statistics cover every pts that has a proxy (vacuous when no proxy
  is stored, as the stub); `pts_ticks` ascending; `size_bytes` as in the eviction rule.
- `proxy()` returns a new array each call; `source_statistics()` returns new writable arrays with
  dtype, shape and bytes exactly as stored; only boolean, integer and floating-point arrays are stored.

## Deviations from the brief

- `cache_key(path)` returns a `cache_version` that is NOT `CACHE_FORMAT_VERSION`: it is
  `codec_cache_version`, the format number combined with the codec identity (AD-5 ruling, condition 2).
  `CACHE_FORMAT_VERSION = 1` is still exported.
- The proxy store is lossy by default, so the brief's "bit-identical" promise holds for the lossless
  `DEFLATE` codec only; for the default the promise is that the decoded proxy is the analysis proxy and
  is the same every time it is read (`test_the_stored_proxy_is_the_decoded_proxy_and_is_stable`).
- Extras beyond IF-7: `close()`, the context manager, `key_for`, `cache_version`, `round_trip`,
  `codec_cache_version`.
- `pyproject.toml` and `uv.lock` changed (Pillow to `[project]`), as AD-5's ruling directs; not an
  owned file under the brief.
- Round-0 questions B, C and E were implemented as the recommended answers (B: `KeyError`; C: a second
  store call overlapping in time is a `RuntimeError`; E: only proxy stores un-complete an entry); no
  ruling on them is recorded in the ledger.

## Verification

Own tests: 67 pass (`tests/test_cache_*.py`, 2.6 s; `work/wp3.12/own-tests.log`), including V17 on the
cache side, planted defects (newest-first eviction, a key ignoring `mtime_ns`, a lossy round trip
presented as lossless, `clear` deleting a foreign file, a marker always believed, a partly covered
stage listed), a child process killed mid-entry, a writer thread against reader threads, `clear` with a
foreign file and a symlink planted, and the dependency rule (importing `clearwater.cache` loads nothing
from `gui`, `jobs`, `methods`, `io`, `core`, nor PySide6, cupy or PIL). Full pytest, ruff, mypy and the
Reviewer A record: see the ledger and the return report.

## Limits

Two processes sharing one cache folder, a roaming or network profile, hand-edited files posing as
entries, and two different files with equal size and modification time (they share a key by D71's
definition) are outside the declared envelope. No compaction: a re-stored changed proxy leaves dead
bytes in the pack until the entry is evicted. The 10 GB figure is an extrapolation from two clips (see
finding 3). `complete` records that every record was whole when the proxy pass ended; a damaged
proxy is found only when it is read, and from then on the entry is incomplete (the marker is
removed); opening an entry does not re-check every checksum.
