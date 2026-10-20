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

## Ledger (cumulative rounds)

| Round | Critical | Major | Minor | In-envelope vs out | NEW / REOPENED | Reverts | Product / test-only fixes | Depth |
|---|---|---|---|---|---|---|---|---|
| (no review round yet) | | | | | | | | |
