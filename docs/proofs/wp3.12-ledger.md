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
3. **Every lossy candidate that fits 10 GB on the worse clip deviates from the 8-bit proxy's bounds by 11-27 % of the range**
   (x264rgb-crf22 14 %, mjpeg-q4 11 %, x264-444-crf14 13 %); the cheapest JPEG that is close to fitting (q85/444: 12.6 GB shallow) 8 %. Compression
   removes high-pass energy, so the N{} bounds narrow systematically. Means and gains stay near the limit (JPEG 7e-4 / 3e-4; x264/mjpeg 1.5e-3 to 2.4e-3 fail 1e-3).
4. The deep clip compresses far better (13-31 KB/frame lossy) than the shallow one; the bound is set by sharp shallow footage.
5. The stdlib quantised-deflate candidate (question D) misses by a wide margin (means 1.2e-2 to 3.6e-2 from the bit-drop bias).

**STOP (brief task 2).** No candidate meets both AD-5's statistics criteria and the 10 GB bound, and the bounds criterion is unattainable
for the lossless 8-bit proxy itself. CHARC chooses (options in the dispatcher message).

## Ledger (cumulative rounds)

| Round | Critical | Major | Minor | In-envelope vs out | NEW / REOPENED | Reverts | Product / test-only fixes | Depth |
|---|---|---|---|---|---|---|---|---|
| (no review round yet) | | | | | | | | |
