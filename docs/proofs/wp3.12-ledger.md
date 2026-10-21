# WP3.12 ledger -- proxy cache

Cell: wp312-cell (implementer-sonnet-high), tier STRONG. Worktree `.worktrees/wp3.12`, branch
`wp3.12`, base main `2c5540a`. Brief `docs/briefs/wp3.12-brief.md` (FINAL, rulings CHARC
`53b752a4d7fac4fc`).

## Round 0 -- design table (brief task 1)

Grounded at the base: `interfaces/cache.py` (IF-7 as amended: `source_statistics`,
`mark_complete`, `CacheEntry.complete` required), `stubs.StubProxyCache` (a stage "covers" when
its pts set is a superset of the proxy pts set, vacuously so with no proxies), `config.atomic_write_text`
(temporary sibling, flush, fsync, `os.replace`), `clearwater.config` imports only the standard library
and `interfaces` (so the cache may import it under the dependency rule), `io.video.probe.find_tool`
(for the instrument), `tools/local_config.find_footage_file` (GX011627 and GX011625 both resolve under
`Snorkel/`), `tools/prototype/temporal.measure/proxy` (the float proxy and the statistics to compare).
Pillow is in the `dev` group only, NOT in `project.dependencies` (see question A).

### 1. Layout: one folder per key, one append-only pack file per folder

```
<cache_dir>/e_<size>_<mtime_ns>_<version>/     entry folder (name = the whole key)
    data.pack        header + records, append-only
    complete         present only after mark_complete: {"valid_length": N, "records": R}
    meta.json        {"last_used_ns": T}  (the oldest-first stamp, question 4)
    *.tmp            only transient (atomic_write_text temporaries)
```

`data.pack` = 32-byte header (magic `CWPK`, pack format 1, then `size`, `mtime_ns`,
`cache_version` as int64/int64/int32) followed by records. Record = fixed 24-byte header
(`magic u16`, `kind u8` P=proxy / S=statistics, `codec u8`, `stage_len u16`, pad, `pts i64`, `payload_len u32`,
`crc32 u32` over header-without-crc + stage + payload) then the stage name (S only) then the payload.
The `codec` byte makes the container independent of the AD-5 outcome (task 2 picks the codec, not the layout).
One file per entry (not one file per frame): 108,000 files per hour of footage would cost NTFS metadata, make
`clear` and eviction slow and defeat a single append handle. Random access by pts = an in-memory
`{(kind, stage, pts): (offset, length, crc)}` index, rebuilt by scanning record headers (seek over payloads, no
payload read) the first time a key is touched in an instance (about 108,000 seeks for a full hour, well under a second).
There is NO persistent index file: nothing can go out of step with the pack, and "a corrupt index" is a bad record
header, handled in section 3.

### 2. Key to name, version mismatch

All three fields are in the folder name (`e_<size>_<mtime_ns>_<version>`, integers, `mtime_ns` may carry a minus
sign; a negative size is a `ValueError`). A different size, `mtime_ns` or version is a different folder, so a version
mismatch can never match. The pack header repeats the triple and the scan refuses a pack whose header differs from its
folder name (a moved or foreign file is a miss, never served). `cache_key(path) -> CacheKey` reads `os.stat`
(`st_size`, `st_mtime_ns`) with `CACHE_FORMAT_VERSION = 1`; the source is never opened.

### 3. Write sequence and crash behaviour (question 3)

- `store_proxy` / `store_source_statistics`: build the payload (and crc) outside any lock; then, under the instance lock,
  append header + payload to the entry's pack through one persistent append handle (opened on the first store of a key,
  closed on `mark_complete`, when another key is written, on `clear`/`close`), flush the Python buffer, then publish the
  record in the in-memory index. No `fsync` and no temporary file per record. A reader therefore never sees an index
  offset whose bytes are not yet in the file.
- A torn tail (crash mid-append, disk full, kill) is a record whose header is short, whose length runs past the file, or whose
  crc fails; the scan stops there, and the writer truncates the pack to the last valid offset before the next append. An
  append that raises (`OSError`) truncates back to the last valid offset, then re-raises.
- Every payload read checks the crc; a mismatch drops that record from the index and raises `KeyError` (a miss, not a corrupt
  result). `lookup` never reads payloads and never raises on a damaged file: any `OSError`/`struct` failure in the scan makes
  the entry a miss.
- `mark_complete(key)`: flush, `fsync` the pack, then `atomic_write_text` of the `complete` marker (valid length and record
  count) -- the marker is written and synced last. At scan time `complete` is True only if the marker parses, its length is
  `<=` the valid length of the pack and its key agrees; an entry left by a crash or cancel has no marker, so it is never
  complete. `mark_complete` on a key with nothing stored raises `KeyError` (the IF is silent; see question B).
- Storing a NEW or CHANGED proxy into a complete entry first unlinks the marker (before the append, so a crash cannot leave
  a marker plus later proxies): the entry is incomplete again. Statistics stores never clear it (statistics may be stored
  after the pass; completeness is about the proxy pass). A re-store of a (kind, stage, pts) already present with
  byte-identical payload is skipped (read-and-compare, only on this rare path); a differing payload appends a new record
  and the index points at the newer one (the old bytes are dead space, counted in `size_bytes`, until the entry is evicted;
  no compaction in v1).
- Leftovers when the cache opens: `*.tmp` files inside entry folders deleted; an entry folder with no pack, or a pack whose
  header is unreadable or disagrees with its name, is removed (bytes reclaimed); an entry with a valid prefix but no marker is
  kept as an incomplete entry (its proxies are readable for AD-15; a later analysis stores over it).

### 4. Eviction (questions 4, 5; unit, order, trigger)

- Unit: a whole entry folder; size counted = bytes on disk of the cache's own named files (`st_size` of `data.pack`,
  `complete`, `meta.json`; not cluster rounding), maintained in memory (updated by each append) and summed at open from `stat`.
- Order: smallest `last_used_ns` first, ties broken by the key. The stamp is refreshed (and `meta.json` rewritten) by a
  `lookup` hit, by `mark_complete`, and set on entry creation. `proxy`/`source_statistics` reads and per-record stores do NOT
  refresh it (write rate). Stamps come from an injectable clock (constructor argument, default `time.time_ns`) so tests control
  order; a corrupt or missing `meta.json` reads as stamp 0 (evicted first).
- Trigger: after every store, in `set_limit_bytes`, and when the cache opens, until total <= limit or only pinned entries remain.
- Never evicted: the entry of the current store call, the entry of the most recent store in this instance, and the most recent
  `lookup` hit. If the pinned entries alone exceed the limit, the cache keeps them, evicts everything else, logs one warning on
  `logging.getLogger("clearwater.cache")` per transition into that state, and storing continues (ruling on question 5).
- Deletion removes only the files the cache names (`data.pack`, `complete`, `meta.json`, `*.tmp`) found as regular files
  (`lstat`, never following a link), then `rmdir` the folder; a foreign file left in an entry folder stays (and the folder with
  it). A `PermissionError` (a reader has the pack open on Windows) skips that entry this round and tries the next oldest.

### 5. Entries of another cache version (question 6)

Removed when the cache opens: an entry folder whose name parses but whose version is not `CACHE_FORMAT_VERSION` can never match
again (D113). Names that do not parse (not `e_<int>_<int>_<int>`), symlinks and junctions are not entries: never counted,
touched or deleted (also by `clear`).

### 6. Thread-safety model (question 8)

One `threading.RLock` per cache instance guards the entry table, the in-memory indexes, the append handle, the stamps and eviction.
Proxy and statistics payload reads happen OUTSIDE it (open, seek, read, close, crc), using offsets copied under the lock. "One
writer at a time per key": a non-blocking per-key writer lock is taken for the duration of a store call; a second store call on the
same key that overlaps in time raises `RuntimeError` (see question C for the reading). A reader that finds the file gone
(eviction/clear) gets `KeyError`. Two processes sharing a folder are out of envelope.

### 7. Statistics encoding (question 9)

One record per (stage, pts); payload = `u16` array count, then per array: `u8` name length + UTF-8 name, `u8` length + the
`dtype.str` (byte order explicit, for example `<f8`), `u8` ndim, `u32` dims, raw C-order bytes. Only numeric/bool kinds (`b`, `i`, `u`,
`f`) are accepted (object, string, structured dtypes refused with `ValueError`); no `pickle`, no `.npy`. Decoding checks the declared
sizes against the payload and returns a fresh `dict` of owned (writable) arrays: dtype, shape and bytes exactly, names in stored
order. A stage name is a non-empty `str` of at most 65,535 UTF-8 bytes.

### 8. How the amended IF-7 is met

- `complete`: the `complete` marker file (section 3); durable across instances; False until `mark_complete`.
- `stages`: from the index, a stage is listed iff its set of stored pts is a superset of the entry's proxy pts (the stub's rule, so
  an entry with statistics but no proxies lists them vacuously); sorted; `pts_ticks` ascending; `size_bytes` the bytes of section 4.
- `lookup` returns in-progress entries (AD-15 needs their proxies); it returns None for any key that differs in size, `mtime_ns` or
  `cache_version`, and for an entry with no valid record.

### 9. Measured-test plan (task 2; `tools/cache_store_test.py`, outputs under `work/wp3.12/`)

- Clips: GX011627 (all 681 frames, 4K, 30000/1001) and 5 windows x 60 frames of GX011625 (498 s; windows spread across the clip,
  300 frames), each decoded by the FFmpeg CLI to a 3840x2160 `rgb24` pipe, then the exact 4x4 block mean in float64 (the
  prototype's `temporal.proxy`) giving the float proxy; the 8-bit proxy is `round(255 * float)` clipped (the stored form of AD-5).
  Everything under `work/wp3.12/`; footage opened read-only through `find_footage_file`.
- Candidates (each parameter swept so the curve is visible): (a) per-frame deflate = PNG-style row filter (Sub/Up chosen per frame) +
  zlib at levels 1/6/9, stdlib; (b) FFV1 and UT Video intra streams via FFmpeg (rgb); (c) lossy: x264 all-intra (`-g 1`, yuv444p,
  crf sweep), MJPEG (`-q:v` sweep) via FFmpeg, and JPEG (Pillow in the instrument, quality sweep 85..98); (d) proposed addition,
  question D: a stdlib lossy "quantised deflate" (drop 1..3 low bits, then (a)).
- Figures per candidate: bytes per frame (median, p95, max, per clip); 60-minute extrapolation at 107,892 frames from the median of the
  WORSE clip, plus the same from the p95 as headroom, against 10 GB (92.7 KB per frame, 16.8:1); statistics deviation against the
  FLOAT proxy: `measure()` (c3 `Params()`) on float and on decoded/255 proxies: means and gains max relative error per frame (max over
  frames and channels, criterion 1e-3), N{} bounds relative error (criterion 1 %: reported both per bound and relative to the range, since a
  bound near 0 makes "relative" ill-defined; the primary figure is per-bound, and if the two disagree on a verdict I raise it), also the
  saliency means and the Ancuti cap statistic `mean((1 - I_c) I_g)` (information; AD-7); max and mean abs error against the 8-bit proxy in levels
  (for CP5); random access by pts (per-frame blob vs whole stream); read cost per proxy (decode of one blob; for FFmpeg candidates a process
  per read) ONLY in the EXCLUSIVE window.
- Reference: the prototype's own measurements (`docs/reports/wp1.2a-speed-memory.md` section 8 and Part B claim 6) are the cross-check for the
  float side.
- Expectation, stated so it can be falsified: (a) lossless deflate lands far above 92.7 KB (order of several hundred KB), FFV1/UT likewise,
  so the real contest is lossy; JPEG/x264-intra can plausibly reach 15:1 but may miss the N{} bound criterion because they remove high-pass
  energy. The instrument decides; no figure is assumed.

### Questions and STOP items (recommended answer first)

- **A. A dependency, flagged early, not a STOP yet.** Pillow is dev-only (`pyproject.toml`), so if JPEG is the only candidate meeting
  criteria and bound, the choice needs Pillow as a product dependency (the brief: a dependency STOP). Recommended: no ruling now; the
  figures decide, and I STOP then with them. If CHARC prefers to pre-grant Pillow for the cache (AD-17 already grants it for photos;
  it would need to move to `project.dependencies`, which this brief does not own), say so now.
- **B. `mark_complete` on a key with nothing stored.** Recommended: `KeyError` (nothing to complete; the stub silently accepts). Alternative: create an empty complete entry.
- **C. "Second writer to the same key is a RuntimeError."** Recommended reading: two store calls on one key overlapping in time (non-blocking per-key writer lock),
  so a restarted analysis on a new thread after a cancel is never locked out. Alternative: ownership by thread, with takeover when the owner thread has ended
  (rejected: pooled worker threads never end, so a restart could be locked out).
- **D. Add one lossy candidate not named in ruling 2:** the stdlib "quantised deflate" (drop low bits, then PNG filter + zlib). It is the only lossy form needing no
  dependency and no process per read, so it keeps the choice open if JPEG needs Pillow. Recommended: yes, add it to the measured test (no product effect unless it wins).
- **E. Store after `mark_complete`** clears completeness for proxies only (statistics stores do not). Recommended as designed; stated because WP3.11 may store statistics
  after the pass.
- No change needed in `src/clearwater/interfaces/`; no OS-specific code (the `junction` check uses `os.path.isjunction`, portable); no write to footage; no mailbox post.

Stop-and-ask count: 0 blocking; A to D are for the dispatcher's ruling at this yield, each with a recommended answer.

## Measured test (task 2) -- interim result, STOP raised 2026-10-20

Instrument `tools/cache_store_test.py`; data and logs under `C:/Users/rwsmy/clearwater/work/wp3.12/` (`results.json`,
`prepare.log`, `sizes*.log`; the working folder is the main tree's `work/`, gitignored). GX011627 all 681 frames; GX011625
5 x 60 frames at 30/130/230/330/430 s. Statistics measured with `prototype.temporal.measure` (c3 `Params()`, CPU) on every 8th
frame (86 + 38 frames); sizes on every frame (png-pillow-opt: the 124 statistics frames only). Reference = the FLOAT proxy
(`block sum / 4080`, checked equal to `temporal.proxy` within 1e-6); the 8-bit proxy is `floor((block sum + 8) / 16)`.
"max err" is against the 8-bit proxy on the statistics frames. Deviations are the maximum over frames and both clips.
"bounds (value)" is relative to each bound; "bounds (range)" relative to the bounds' range (a bound near zero makes the first ill-defined).
60-minute figure = worse clip's median bytes per frame x 107,892 frames (p95 figures in `results.json`).

| candidate | shallow KB (median) | deep KB (median) | 60-min GB (worst median) | fits 10 GB | max err (levels) | means | gains | bounds (value) | bounds (range) | bounds vs 8-bit (range) |
|---|---|---|---|---|---|---|---|---|---|---|
| deflate-L1 | 748.7 | 261.4 | 80.8 | no | 0 | 2.7e-04 | 2.6e-05 | 6.0e-02 | 3.1e-02 | 0.0e+00 |
| deflate-L6 | 695.0 | 195.1 | 75.0 | no | 0 | 2.7e-04 | 2.6e-05 | 6.0e-02 | 3.1e-02 | 0.0e+00 |
| deflate-L9 | 682.3 | 178.1 | 73.6 | no | 0 | 2.7e-04 | 2.6e-05 | 6.0e-02 | 3.1e-02 | 0.0e+00 |
| png-pillow-opt | 654.3 | 172.1 | 70.6 | no | 0 | 2.7e-04 | 2.6e-05 | 6.0e-02 | 3.1e-02 | 0.0e+00 |
| ffv1-intra | 447.4 | 119.0 | 48.3 | no | 0 | 2.7e-04 | 2.6e-05 | 6.0e-02 | 3.1e-02 | 0.0e+00 |
| utvideo-median | 550.1 | 237.6 | 59.4 | no | 0 | 2.7e-04 | 2.6e-05 | 6.0e-02 | 3.1e-02 | 0.0e+00 |
| x264rgb-intra-crf0 | 690.2 | 206.5 | 74.5 | no | 0 | 2.7e-04 | 2.6e-05 | 6.0e-02 | 3.1e-02 | 0.0e+00 |
| x264rgb-intra-crf10 | 290.8 | 121.8 | 31.4 | no | 33 | 6.6e-04 | 7.2e-05 | 6.9e-02 | 3.6e-02 | 8.2e-03 |
| x264rgb-intra-crf14 | 202.5 | 73.2 | 21.8 | no | 41 | 9.6e-04 | 2.0e-04 | 6.9e-02 | 3.5e-02 | 1.6e-02 |
| x264rgb-intra-crf18 | 134.3 | 42.0 | 14.5 | no | 61 | 1.3e-03 | 2.9e-04 | 7.6e-02 | 4.0e-02 | 5.7e-02 |
| x264rgb-intra-crf22 | 88.6 | 22.3 | 9.6 | yes | 81 | 1.9e-03 | 6.5e-04 | 2.4e-01 | 1.3e-01 | 1.4e-01 |
| x264-444-intra-crf6 | 163.4 | 80.3 | 17.6 | no | 36 | 2.4e-03 | 1.5e-03 | 2.8e-01 | 1.4e-01 | 1.1e-01 |
| x264-444-intra-crf10 | 117.3 | 48.4 | 12.7 | no | 44 | 2.4e-03 | 1.6e-03 | 3.0e-01 | 1.5e-01 | 1.2e-01 |
| x264-444-intra-crf14 | 81.2 | 28.9 | 8.8 | yes | 58 | 2.4e-03 | 1.6e-03 | 3.2e-01 | 1.6e-01 | 1.3e-01 |
| x264-444-intra-crf18 | 53.7 | 17.3 | 5.8 | yes | 77 | 2.3e-03 | 1.5e-03 | 2.7e-01 | 1.4e-01 | 1.1e-01 |
| mjpeg-444-q2 | 141.5 | 19.5 | 15.3 | no | 25 | 1.9e-03 | 1.7e-03 | 2.1e-01 | 1.1e-01 | 7.5e-02 |
| mjpeg-444-q4 | 86.3 | 13.1 | 9.3 | yes | 43 | 1.9e-03 | 1.7e-03 | 1.9e-01 | 1.0e-01 | 1.1e-01 |
| mjpeg-444-q8 | 50.7 | 11.1 | 5.5 | yes | 70 | 1.9e-03 | 1.7e-03 | 2.8e-01 | 1.5e-01 | 1.5e-01 |
| jpeg-q85-444 | 116.6 | 22.9 | 12.6 | no | 45 | 7.1e-04 | 3.2e-04 | 2.2e-01 | 1.1e-01 | 8.0e-02 |
| jpeg-q90-444 | 148.1 | 30.9 | 16.0 | no | 34 | 7.4e-04 | 2.7e-04 | 2.7e-01 | 1.3e-01 | 1.1e-01 |
| jpeg-q95-444 | 212.5 | 50.3 | 22.9 | no | 26 | 7.2e-04 | 2.7e-04 | 1.9e-01 | 9.6e-02 | 6.6e-02 |
| jpeg-q98-444 | 309.0 | 75.2 | 33.3 | no | 11 | 7.1e-04 | 2.7e-04 | 1.9e-01 | 9.9e-02 | 6.8e-02 |
| jpeg-q90-420 | 119.4 | 25.6 | 12.9 | no | 70 | 7.2e-04 | 2.9e-04 | 1.7e-01 | 8.8e-02 | 5.8e-02 |
| jpeg-q95-420 | 172.1 | 43.4 | 18.6 | no | 63 | 7.0e-04 | 2.9e-04 | 1.5e-01 | 7.6e-02 | 5.1e-02 |
| qdeflate-drop1-L6 | 558.0 | 170.5 | 60.2 | no | 2 | 1.2e-02 | 6.1e-04 | 3.3e-01 | 1.6e-01 | 1.4e-01 |
| qdeflate-drop2-L6 | 419.9 | 119.0 | 45.3 | no | 4 | 2.1e-02 | 1.0e-03 | 1.2e+00 | 6.0e-01 | 5.5e-01 |
| qdeflate-drop3-L6 | 307.1 | 75.1 | 33.1 | no | 8 | 3.6e-02 | 2.0e-03 | 2.8e+00 | 1.4e+00 | 1.3e+00 |

Criteria: means and gains <= 1e-3, bounds <= 1e-2, 60 minutes <= 10 GB. Read cost not yet measured (EXCLUSIVE window).

**Findings.**
1. **The lossless 8-bit proxy itself fails the bounds criterion.** Rows with max err 0 (every lossless candidate, which reproduce the 8-bit proxy
   exactly) deviate from the FLOAT proxy by 6.0 % per bound (3.1 % of the range) on the deep clip and 1.3 % (0.55 %) on the shallow
   one, p95 5.3 % / 0.5 %. The cause is the 8-bit rounding of the proxy (a step of 0.0039), against an N{} range that is only
   0.010-0.116 (median 0.033) on the deep clip's 540 proxy; the criterion therefore cannot be met by ANY 8-bit store, whatever its container.
   Means (2.7e-4) and gains (2.6e-5) pass.
2. **No lossless candidate fits 10 GB**: best FFV1 447 KB/frame shallow (48 GB) and 119 KB deep (12.8 GB); 4.8:1 and 3.7:1 against the 16.8:1 needed.
3. **Every lossy candidate that fits 10 GB on the worse clip deviates from the 8-bit proxy's bounds by 11-15 % of the range (20-28 % per bound)**
   (x264rgb-crf22 14 %, mjpeg-q4 11 %, x264-444-crf14 13 %); the cheapest JPEG that is close to fitting (q85/444: 12.6 GB shallow) 8 %. Compression
   removes high-pass energy, so the N{} bounds narrow systematically. Means and gains stay near the limit (JPEG 7e-4 / 3e-4; x264/mjpeg 1.5e-3 to 2.4e-3 fail 1e-3).
4. The deep clip compresses far better (13-31 KB/frame lossy) than the shallow one; the bound is set by sharp shallow footage.
5. The stdlib quantised-deflate candidate (question D) misses by a wide margin (means 1.2e-2 to 3.6e-2 from the bit-drop bias).

**STOP (brief task 2).** No candidate meets both AD-5's statistics criteria and the 10 GB bound, and the bounds criterion is unattainable
for the lossless 8-bit proxy itself. CHARC chooses (options in the dispatcher message).

## State at the orchestrator rollover (2026-10-20) -- resume here

**AD-5 ruled by CHARC (AD-5 amended on main a6ba740, option 1): the analysis proxy IS the stored decoded JPEG proxy.** The four conditions as applied:
1. Codec: JPEG q75 4:4:4 is `DEFAULT_CODEC` (id 2); q80 4:2:0 (id 3) exists; the dispatcher picks q80 only if the EXCLUSIVE read-cost row shows it > 30 % faster
   per `proxy()` call (a NON-official smoke run on a shared laptop gave q75 5.4 ms, q80 4.5 ms, deflate 9.5 ms).
2. Determinism: `codec_cache_version(codec)` = format number << 24 | CRC-24 of `codec_id:identity`; JPEG identity = Pillow + libjpeg + libjpeg-turbo versions read at
   runtime (`codec.jpeg_identity`). A cache opened with another identity removes the old entries; stores under the old key are refused. Test:
   `tests/test_cache_jpeg.py::test_a_different_decoder_identity_invalidates_the_cache`.
3. Criteria: means and gains <= 1e-3 against the float proxy (met: JPEG q75 4:4:4 means 9.0e-4, gains 6.6e-4 worst clip); bounds deviation beyond the 8-bit floor
   bounded at 10 % of the range (met: 8.3 % q75 4:4:4, 7.8 % q80 4:2:0). The report must carry the per-clip table (`results.json` in the main tree's `work/wp3.12/`) and
   the CP5 line "proxy bounds are X % narrower than full-frame float bounds (AD-4 11-14 % + AD-5 ~8 %)".
4. Pillow moved from the dev group to `[project] dependencies` and `uv.lock` re-locked (commit a21a738); X-B3: whichever of WP3.6 / WP3.12 merges second re-locks.
Consumer note for WP3.11 (put it in the report): at first analysis the proxy is encoded and decoded in memory (`clearwater.cache.round_trip`, or `store_proxy` then
`proxy`) BEFORE any statistic is measured; the float proxy is never a statistics source. DR-14: JPEG narrows the high-pass range, so the AD-4 floor binds slightly more
often (intended direction).

**Done (commits on branch wp3.12):** round-0 table; instrument `tools/cache_store_test.py` (modes prepare, sizes, readcost, readcost-product, report) and the measured figures;
the store (`src/clearwater/cache/`: keys, codec, layout, store), 60 tests (`tests/test_cache_store.py`, `test_cache_robust.py`, `test_cache_jpeg.py`; planted defects; crash
child process; threads; dependency rule); ruff check, ruff format --check and mypy green on the whole repo at a21a738.
**Next:** (1) EXCLUSIVE window (dispatcher grants): `uv run python tools/cache_store_test.py readcost-product` -> `work/wp3.12/readcost.json`; dispatcher decides q75 vs q80;
(2) report `docs/reports/wp3.12-proxy-cache.md` (public API, layout, AD-5 table per clip, choice, eviction rule, the CP5 line, stub-vs-product `mark_complete` difference
(stub accepts an unknown key, product raises KeyError), the WP3.11 consumer notes: measure on the stored proxy; a new or changed proxy un-completes an entry; a second
concurrent store on a key, statistics included, is a RuntimeError); (3) full-pytest window ("WINDOW REQUEST"); (4) Reviewer A at the cell's seat (runner/prompt shape from
`C:/Users/rwsmy/clearwater-review-evidence/wp3.1/r2/`, evidence in `.../wp3.12/rN/`), STRONG tier, yield at each adjudicated verdict.
Deviations from the brief: store refuses a key whose version is not the instance's (ValueError); `close()`, context manager, `key_for`, `round_trip` and `codec_cache_version` are extras.

## wp312-cell2 (resumed 2026-10-21 at `82a5dbb`, tree clean)

**Read-cost row (EXCLUSIVE, run by the orchestrator; closes step (1)).** `readcost-product` at `82a5dbb`, 2026-10-21 00:20:39-00:20:45Z (file stamp
`2026-10-20T14:20:44` local), clip GX011627, 25 frames x 8 rounds = 200 reads of `proxy()` (read + CRC + decode, file in the OS cache), output
`work/wp3.12/readcost.json`: deflate median 8.47 / p95 10.26 / max 15.80 ms, 797.3 KB per frame; JPEG q75 4:4:4 3.39 / 4.27 / 10.22 ms, 94.0 KB; JPEG q80 4:2:0
3.08 / 4.47 / 9.90 ms, 88.9 KB. q80 is 9.0 % faster at the median, under CHARC's 30 % threshold: q75 4:4:4 STAYS `DEFAULT_CODEC` (FINAL). Not re-run.

**Two findings from the report work (non-timing, CPU, sizes and statistics only), for the dispatcher and CHARC:**
1. Whole-clip MEAN size (`work/wp3.12/meansize.txt`, product codecs, all 681 frames of GX011627): q75 4:4:4 mean 94.9 KB = 10.2 GB per 60 minutes (the ruling
   used the median, 9.0 GB); q80 4:2:0 mean 89.7 KB = 9.7 GB. So by the mean the default is 2 % over AD-5's 10 GB bound on the sharp shallow clip; the deep
   clip is 2.0 GB. Disclosed in the report (finding 3); no code change made.
2. Signed bounds change (`work/wp3.12/signed-bounds.txt`): the decoded q75 4:4:4 proxy's N{} range against the float proxy has mixed sign, median +0.9 % shallow
   and +2.9 % deep (max +7.6 % / +19.8 %), not "narrower" as AD-5's ruling text and ledger finding 3 above say; the AD-4 floor would bind slightly less, not
   more. Disclosed in the report (finding 4) and the CP5 line is worded from the measured figures.

**Done this window:** report `docs/reports/wp3.12-proxy-cache.md`; `codec.py` constant docstring made true to the figures; own tests 60 pass; ruff check, ruff format
--check and mypy green on the whole repo. **Next:** WINDOW REQUEST (full pytest, normal and cupy-unimportable forms), then Reviewer A.

**CHARC rulings relayed 2026-10-21 (FINAL, no code change).** Q1: q75 4:4:4 stays; the 10 GB figure is a cache sizing target read on the MEDIAN frame size (9.0 GB/h); the mean-basis
10.2 GB/h on the sharpest shallow footage is recorded, not a failure (D71's 20 GB with oldest-first eviction is the user-facing limit). Q2: the stored proxy's N{} range differs from the
float proxy's by up to 10 % of the range beyond the 8-bit floor, of EITHER sign, median slightly wider, the AD-4 floor binds slightly less often; the CP5 line carries the measured
figures; CHARC amends AD-5 on main later. The report's findings 3 and 4 were reworded to this (one docs commit after the round-1 yield). This supersedes the two "finding" paragraphs
above where they say "over the bound" and "not narrower".

**Round 1 remediation (this window).** F1 `_forget` of a damaged proxy makes the entry incomplete (marker unlinked; a corrupt record is still found only on read, no checksum pass at open:
open item for the dispatcher); F2 `store._unlink` retries a refused delete (6 tries, 10 ms); F3 `_evict` pins every key in `_writing`; F5 statistics store claims the key slot before encoding;
F8 `codec_cache_version` = format << 48 | first 48 bits of SHA-256 (pack header field int64, `PACK_FORMAT` 2); F9 `pack_size` re-read after a failed rollback; F10 thread test fails on any
proxy `KeyError`; F4 instrument `report` judges the ruled criteria (original 1 % shown as information); F7 `meansize` and `signed` modes added and re-run (identical figures to the scratch
runs); F6 report text. F11 first banked, then FIXED under the orchestrator's ruling below (temporary-name pattern tightened).
Own tests 67 pass; ruff check, ruff format --check, mypy green at the fix head.

**Round 2 (head b3e60ed, gpt-5.6-sol high; evidence `.../wp3.12/r2/`):** 0 critical, 2 major, 2 minor, all REASONED (the sandbox could not run pytest: read-only /tmp), VERDICT
NEW_CRITICAL_MAJOR_FOUND; mechanical assertions passed (14 succeeded lines, no ERROR, tokens footer). R2-1 MAJOR `clear()` gives up after the 50 ms retry of F2 (accepted: a reader can hold the
pack longer; the F2 test asserted the nonconforming result); R2-2 MAJOR if the marker cannot be deleted the F1 fix leaves it valid on reopen (accepted); R2-3 MINOR PNG sized on statistics
frames only, `bytes_max` not in the report (accepted, text + column); R2-4 MINOR `prepare` does not check the ffmpeg exit code or frame counts (accepted; the check is NOT executed, `prepare`
is a footage decode I did not re-run, mypy and ruff only). Fixes (commits 28d6fab store, then the instrument and report): removal sets `closing` (new reads miss), waits up to 5 s on a
Condition for the entry's readers (`_reading`), pack removed first and nothing else touched if it stays, a marker that cannot be deleted is overwritten with `{}`; instrument refuses a short
read, a non-zero exit and a wrong frame count (681 and 300), shows max size; report table has max KB. Three new tests, each failing on the pre-fix store (verified with a stash).
Own tests 70 pass.

**Orchestrator ruling on round 1 (FINAL, applied; the cell's depth at the R1 yield: 157,637 tokens / 40 turns, 00:43:29Z).** F1 as planned with NO verify-on-open (residual named in the report: a corrupt
record is detected when read, not when the entry is opened); F2 bounded retry, then a logged failure that leaves the entry marked for removal (`removing` file; first at the next eviction or
`clear`; removed at the next open; a store into it removes it or raises): done in the round-3 fix commit; F8 cache format number bumped to 2 with a test; F11 FIXED (one pattern, `_TEMP_NAME`
= the shape `tempfile` gives `atomic_write_text`'s temporaries; residual: a foreign file of that exact shape is still deleted, out of envelope); F7 figures regenerated by the instrument modes and
IDENTICAL to the scratch figures. Note on the order: round 2 (head b3e60ed) ran on a head that did not yet carry the F2-marked / F8-bump / F11 items of this ruling (the ruling reached the cell
after the remediation was under way) and its findings were remediated without a yield; a further round (round 3, evidence `.../r3/`) runs on the head with everything. Own tests 73 pass.

**Round 3 (head 8f202ae; evidence `.../r3/`):** 0 critical, 3 major, 1 minor, all REASONED, VERDICT NEW_CRITICAL_MAJOR_FOUND; assertions passed (5 succeeded lines, no ERROR, footer). The majors are
paths on which cache-owned marker files resist delete AND replace, or a crash lands between a removal and its mark: each fixed (`_write_small`: atomic then in place; `_void_marker` used on
every path; `removing` temporaries cleaned) with a test failing on the old code. R3-3's remainder is inherent (an entry the cache wanted gone and could not mark may be served again after a
restart: valid data, an unfulfilled removal) and is a stated limit. Own tests 77 pass; ruff, format, mypy green. Residual hostile-filesystem classes remain possible; the cell recommends the
dispatcher judge convergence on the envelope (these need two failing file operations on a file the cache itself owns).

**Round 4 (head 9b2890d; REVIEW ONLY; evidence `.../r4/`):** 0 critical, 3 major, 1 minor, all REASONED, VERDICT NEW_CRITICAL_MAJOR_FOUND; assertions passed (7 succeeded lines, no ERROR, footer).
Nothing was changed after the verdict. R4-1 (REOPENED, marker / removal / scan family): `_discover`/`_register` ignore a failed `_remove_files` for wrong-version and unreadable entries (untracked, not retried,
no `removing` mark), and `_entry_for_write` rewrites a pack with "wb" leaving any old `complete` marker; a stale marker revalidating needs equal record count and byte length plus a crash: negligible, but
the report's "every failed removal is marked" is false for discovery. R4-2 (NEW, executed, `r4-2-probe.py`): `scan_pack`/`_forget` keep `index.shape` after the only proxy is dropped, so a later store of
another shape is refused (the shape of one key is constant in practice; bites only on a damaged shape prefix). R4-3 (NEW, tool): `baseline_stats` and `sizes_mode` reuse baseline/results files without a run
identity; for the committed figures the files are in one sequence (proxies 12:58-13:00, baselines 13:07, results 13:53 on 2026-10-20). R4-4 (NEW, minor): a constructor codec that is not the registered one
for its id is decoded by the module `CODECS`. PLANNED FIXES FOR A FRESH CELL: register a failed discovery removal as a `closing` entry with the `removing` mark; void a stale `complete`/`removing` file when
`_entry_for_write` creates a pack; clear `index.shape` when no proxy remains (`_drop_last`, `_forget`); validate the constructor codec against `CODECS` (ValueError); a run identity (stride, proxy hash,
Pillow/libjpeg identity) in the instrument's baseline and results with a refusal on mismatch; a test for each. The F7 regenerated figures equal the scratch figures (same numbers; `signed-bounds.txt` byte-identical).

**Orchestrator ruling on round 4 and stand-down (FINAL, gen 7, 2026-10-21):** the R4 adjudication is accepted as committed (3c7c457); the planned fixes above are the brief for a FRESH cell dispatched from this ledger; this cell's work in the package is done (depth 283,367 / 108 turns at the R4 yield, 01:23:11Z).

## wp312-cell3 (fresh cell, resumed 2026-10-21 at `2b486a0`, tree clean)

**R4 remediation (commits 8bcb39a product, 052c8e3 instrument; no `git stash` used: each test was run on the unfixed code BEFORE the fix was written, output kept in the scratchpad `r4-before.txt`).**
R4-1: `_discover` and `_register` route a failed removal (another cache version, unreadable pack) through `_remove_or_retain`: the entry is kept as a `closing` entry with the `removing`
mark, counted in the total, never served, first to be evicted and retried; `_entry_for_write` calls `_void_stale_marks` when it creates a pack (deletes a leftover `removing`, refusing the write
with `OSError` if it cannot; voids a leftover `complete`). Tests: `test_a_removal_that_fails_while_opening_is_marked_counted_and_retried` (2 params), `test_a_new_pack_is_not_made_valid_or_condemned_by_a_stale_marker_file`
(3 params), `test_a_stale_removal_mark_that_cannot_be_deleted_refuses_the_new_pack`: 6 failures on the unfixed code (no `removing` mark; `complete` True on a pack that was never completed; entry removed by
a stale `removing`; no OSError). The report's "never a silent keep" now holds for discovery too (stated in the report). R4-2: `index.shape` cleared in `_drop_last` and in `_forget` when no proxy remains; two tests
(torn tail, damaged on read) failed with `ValueError: proxy shape ... differs from the entry's`. R4-4: the constructor requires `CODECS[codec_id]` with the same `decode`, `shape` and `identity` (ValueError); a
codec that differs only in `encode` (the hook codecs of the existing tests) is accepted; two failing params plus one accepting control. R4-3: instrument `run_identity` (jpeg identity; per clip stride, frames,
proxy SHA-256), `require_identity`, `read_results`/`write_results`, new file forms `{"identity", "statistics"}` and `{"identity", "rows"}`; `sizes` refuses a file of another identity or of none; `report` only prints the
identity (a legacy `results.json` prints "no run identity"). The committed figures come from legacy files; a re-run of `sizes` needs them deleted. The stale reuse was reproduced on the old tool (scratch probe: the
baseline of proxy A returned for proxy B, True). `tests/test_cache_instrument.py`: 4 tests. Own tests 92 pass (88 cache + 4 instrument); `ruff check .`, `ruff format --check .`, `mypy` green at 052c8e3. Edited files were
converted to LF (the index is LF; the worktree files had been checked out CRLF) so the commits carry no line-ending noise. No full pytest was run (no window granted).

## Ledger (cumulative rounds)

| Round | Critical | Major | Minor | In-envelope vs out | NEW / REOPENED | Reverts | Product / test-only fixes | Depth |
|---|---|---|---|---|---|---|---|---|
| R1 (head 1b4da4e, gpt-5.6-sol high, WSL codex) | 0 | 4 (F1 stale `complete` after a corrupt middle record, executed; F2 `clear` vs an open reader on Windows; F3 `_writing` entry not eviction-pinned; F4 instrument report judges the superseded criterion) | 7 (F5 stats slot claimed after encode, out of envelope; F6 sizes are payload bytes, error on statistics frames; F7 meansize / signed figures not from the instrument; F8 CRC-24 identity collides, executed; F9 pack_size after a failed rollback; F10 thread test swallows every KeyError; F11 foreign `*.tmp` name, out of envelope) | 9 in / 2 out | 11 NEW / 0 REOPENED | none | remediated after the yield, all 11 handled except F11 (banked, out of envelope): product code F1 F2 F3 F5 F8 F9 (commits c5c6338, d232ab5), test-only F10, instrument F4 F7 (83f47a9), text F6 (docs commit); every new test fails on the unfixed code (8 failures on stashed src) | (dispatcher) |
| R2 (head b3e60ed, gpt-5.6-sol high, WSL codex) | 0 | 2 (R2-1 clear gives up on a slow reader; R2-2 undeletable marker valid on reopen: both REOPENED in substance from R1 F2 / F1) | 2 (PNG sampled sizes and no max column; prepare unchecked) | 4 in / 0 out | 2 NEW (minors) / 2 REOPENED (majors) | none | remediated (not yielded before fixing: see return report): 2 product-code, 1 tool, 1 text; 3 new tests | (dispatcher) |
| R3 (head 8f202ae, gpt-5.6-sol high, WSL codex) | 0 | 3 (R3-1 undeletable AND unreplaceable marker; R3-2 stale marker delete suppressed in scan; R3-3 removal mark best-effort, `removing.*.tmp` not cleaned: all double-failure or crash-timing conditions) | 1 (prepare width) | 3 in (kind) / 1 partly out | 4 NEW / 0 REOPENED | none | remediated in f1bce46 (product code, instrument, 4 tests failing on the unfixed code); not yielded before fixing | (dispatcher) |
| R4 (head 9b2890d, gpt-5.6-sol high, WSL codex; REVIEW ONLY) | 0 | 3 (R4-1 discovery ignores a failed removal, marker/removal family: REOPENED; R4-2 stale `index.shape` after the only proxy is dropped, executed: NEW; R4-3 instrument reuses baseline/results without provenance: NEW, tool) | 1 (R4-4 constructor codec vs module `CODECS`) | 4 in | 3 NEW / 1 REOPENED | none | NOT remediated (past the re-seat line; planned for a fresh cell: 3 product-code, 1 tool) | 283,367 / 108 turns at the R4 yield, 01:23:11Z (dispatcher) |

Round 1 evidence: `C:/Users/rwsmy/clearwater-review-evidence/wp3.12/r1/` (prompt, diff, `review.txt`, `adjudication.md` with the per-finding table and planned fixes, md5sums). Mechanical assertions passed (model and effort, no transport ERROR, tokens footer, 6 succeeded lines, VERDICT NEW_CRITICAL_MAJOR_FOUND).
