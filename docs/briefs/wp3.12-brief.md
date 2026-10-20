# WP3.12 — Proxy cache (dispatch brief, FINAL)

**Status:** FINAL 2026-10-20, approved by CHARC 53b752a4d7fac4fc with rulings; base = the pre-dispatch main commit named at dispatch. Owner decisions:
none inside the package (the 20 GB default and "oldest removed first" are spec text, D71).
- Spec **v0.5.4**. Architecture FINAL 1.0 section 3 IF-7, section 5 ("Proxy cache (WP3.12):
  key (size, mtime, version); uint8 proxies in the store chosen by the measured test of AD-5;
  source-only statistics beside them; 20 GB default, oldest first, clear") and section 10
  ("Proxy store container | WP3.12 brief's measured test (AD-5)"); AD-5, AD-7, AD-20, AD-25 (a).
  Frame `docs/briefs/wp2.4-phase3-frame.md`. WP3.15 report
  `docs/reports/wp3.15-presets-settings-logging.md` "Public API" ("WP3.12 takes
  `app_locations().cache_dir` and `Settings.cache_limit_bytes`").
- Cell: `implementer-sonnet-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.12`, branch `wp3.12`, base = the main commit named at dispatch.

**Why.** Spec 7.3: parameter changes recompute statistics "from the proxy cache rather than by
re-decoding the source (D59)", and "Reopening a clip skips the decode pass". The analysis engine
(WP3.11), the scrubber (WP3.18, D72 "proxy frames while dragging"), the settings panel's
clear-cache button (WP3.20, G12) and the video path end to end (WP4.2, V17) all sit on IF-7.
AD-5 left the on-disk container to this brief's measured test.

| Field | Content |
|---|---|
| ID and title | WP3.12 — Proxy cache; plan section 6 Phase 3 row WP3.12 (size M); module `clearwater.cache` (plan 8.1: "Proxy cache") |
| Goal | A size-limited, crash-safe store in the app-data cache folder that satisfies IF-7 `ProxyCache`: proxies and source-only statistics stored and fetched by `CacheKey` (file size, modification time, cache format version) and pts ticks, the oldest entries evicted first at the limit, everything removed on request; with the AD-5 container chosen by a measured test. |
| Spec / decision clauses | 7.3 "**Cache (D71, D113):** Stored in app data, identified by source file size, modification date, and a cache format version. A version mismatch triggers re-analysis."; "Holds only results that depend on the source file alone: the proxies, and any statistics that depend on neither parameters nor other frames."; "Smoothing, and statistics that depend on parameters or earlier stages, are always recomputed from the cache."; "Reopening a clip skips the decode pass."; "Default limit 20 GB, editable in settings; oldest entries removed first; a clear-cache button is provided." D59 "Parameter changes recompute statistics from a low-resolution proxy cache built during analysis"; D71 "*(amended by D113)* Analysis proxies and source-only statistics cached in app data, keyed with a cache format version; default limit 20 GB, editable; oldest removed first; clear-cache button"; D113 "Cache key includes a cache format version; the cache holds only results that depend on the source file alone; smoothing is always recomputed"; D95 (statistics keyed by pts). Feeds V17 "reopening an unchanged clip skips the decode pass; a cache format version mismatch triggers re-analysis" (the cache side; WP4.2 the end-to-end side). AD-5 "short side 540, area-averaged ... stored 8-bit per channel. The on-disk container is chosen in WP3.12's brief by a measured test: candidates lossless per-frame (PNG) or a lossless intra video stream (FFV1 / UT Video); the chosen store must reproduce the float proxy's statistics within 1e-3 relative on means and gains and 1 % on N{} bounds, and a 60-minute 4K clip must fit under 10 GB." AD-7 (source-only statistics: "Ancuti stage 1 means and the cap statistic `mean((1 - I_c) I_g)`" cached with the proxies). AD-25 (a) (cache location `%LOCALAPPDATA%\Clearwater\cache`, resolved only in `clearwater.config.paths`). |
| Depends on | WP2.2 merged (IF-7 frozen). WP3.15 merged (X2: `clearwater.config.app_locations().cache_dir`; `Settings.cache_limit_bytes`, default `DEFAULT_CACHE_LIMIT_BYTES = 20 * 10**9`). No WP2.3 sample is needed for the store; the measured test (task 2) reads real footage. No other Phase 3 package: the cache is fed by whoever calls it; tests feed synthetic uint8 arrays and `Statistics` mappings. |
| Files owned | `src/clearwater/cache/` (NEW: `__init__.py` and modules the round-0 table names, for example `store.py` (the IF-7 class), `keys.py` (key derivation, `CACHE_FORMAT_VERSION`), `layout.py` (entry files, index, completeness marker)); `tests/test_cache_*.py` (NEW); `docs/reports/wp3.12-proxy-cache.md`; `docs/proofs/wp3.12-ledger.md`. X1-style owned outside the module path: `tools/cache_store_test.py` (the AD-5 measured-test instrument, question 10). NOT owned: `src/clearwater/interfaces/` (frozen; IF-7 amended by CHARC before dispatch, ruling 1), `src/clearwater/config/` (consumed), `pyproject.toml` (no dependency), `tests/conftest.py`. |
| Interfaces provided | IF-7: a class satisfying `clearwater.interfaces.cache.ProxyCache` exactly as frozen: `lookup(key) -> CacheEntry | None`, `store_proxy(key, pts_ticks, proxy: NDArray[np.uint8]) -> None`, `proxy(key, pts_ticks) -> NDArray[np.uint8]`, `store_source_statistics(key, stage, pts_ticks, stats) -> None`, `source_statistics(key, stage, pts_ticks) -> Statistics` (`KeyError` when absent), `mark_complete(key) -> None`, `limit_bytes() -> int`, `set_limit_bytes(n) -> None`, `clear() -> None`; `CacheEntry(key, pts_ticks, stages, size_bytes, complete)` as returned, where `stages` lists only stages whose statistics cover every pts in `pts_ticks` and `complete` is True only once the proxy pass for the whole clip is stored (`mark_complete`). This is IF-7 as amended under AD-20 on 2026-10-20 (ruling 1), already in the base: read `src/clearwater/interfaces/cache.py` and `stubs.StubProxyCache`; `interfaces/` stays outside your ownership. Outside the IFs: a key helper (for example `cache_key(path) -> CacheKey` from `os.stat`, `CACHE_FORMAT_VERSION = 1`). The class takes its folder and limit as constructor arguments; it never resolves the app-data folder itself. |
| Interfaces consumed | IF-7 `CacheKey(size, mtime_ns, cache_version)`, `CacheEntry`; IF-3 `Statistics` (`Mapping[str, numpy.ndarray]`); stdlib (`os`, `pathlib`, `threading`, `zlib`, `json`), NumPy. Production wiring (WP4.3, not here) passes `app_locations().cache_dir` and `Settings.cache_limit_bytes`. |
| Wave-2 consumers | None in wave 2 builds on it. Wave 3: WP3.11 (stores proxies during the decode pass, reads them for staged statistics; AD-7), WP3.18 (proxy frames while scrubbing), WP3.20 (clear cache, the limit). Phase 4: WP4.2 (V17), WP4.3 (wiring). Stub until this merges: `stubs.StubProxyCache()` (dict-backed; "the size limit is stored, not enforced"; `proxy` raises `KeyError` if absent). |
| Hardware flags | `footage` (read only, through `tools/local_config.find_footage_file`) on the measured test (task 2); **EXCLUSIVE**, best effort (frame rule 7, plan 4.3), only for the per-proxy read-cost figure of that test, in a window the dispatcher grants; storage sizes are not timing. No `gpu`. Product tests use `tmp_path` only. |
| Out of scope | Making proxies (decode and the area-averaged 540 downscale are WP3.11's, AD-5); the statistics themselves and deciding which stage is source-only (IF-3 `Stage.source_only`, WP3.4); smoothing (always recomputed, D113); the clear-cache button and the limit setting's GUI (WP3.20); resolving the app-data folder (WP3.15, AD-25 (a)); changing IF-7 (amended by CHARC before dispatch, ruling 1; any further change is a STOP); a lossy store that fails AD-5's statistics criteria (ruling 2); two processes sharing one cache; reading GoPro `.LRV` proxies (D60, closed). |
| Debt and decided items | Spec 7.3 cache sentence "Stored in app data, identified by source file size, modification date, and a cache format version. A version mismatch triggers re-analysis." with the next bullet "Holds only results that depend on the source file alone: the proxies, and any statistics that depend on neither parameters nor other frames.", and V17 "reopening an unchanged clip skips the decode pass; a cache format version mismatch triggers re-analysis" -- IMPLEMENTS, READ AS single-clip in v1 -- chapter handling is deferred to v2 (5.5, v0.5.3: "In v1 every input file is its own clip"), so one cache entry is one source file. On disk in v0.5.4 neither sentence (spec lines 338-339 and 495) still names chapter groups: the change log says "chapter- and recording-group remnants removed from 7.3, V10 and V17"; the one group remnant near them is 7.2's "Smoothing spans chapter boundaries within a consecutive recording group and resets at breaks (Section 5.5)" (line 325, WP3.11's), read the same way. AD-13 (the parameter-set / provenance object), as the commission's "key = the provenance object plus source identity" -- NOT implemented, raised as question 11 -- it conflicts with the frozen IF-7 `CacheKey(size, mtime_ns, cache_version)` and with D113 ("the cache holds only results that depend on the source file alone"); the key here is source identity plus cache version. G12 "cache size limit, clear cache" (first-run default "cache 20 GB") -- PARTLY -- this package provides `limit_bytes`/`set_limit_bytes` and `clear`; the setting and the button are WP3.20's. AD-5 as amended 2026-10-20 (store container "chosen in WP3.12's brief by a measured test"; lossy intra candidates admitted, judged by the statistics criteria against the float proxy; lossless where it fits the bound) -- CLOSES -- task 2 (architecture section 10 open item). AD-20 amendment 2026-10-20 (IF-7 `source_statistics`, `mark_complete`, `CacheEntry.complete`, covering `stages`) -- IMPLEMENTS -- tasks 3 and 6. AD-7 (source-only statistics cached with the proxies) -- IMPLEMENTS -- stored and read back here (`source_statistics`, ruling 1). DR-16 -- must not reopen -- the cache writes no user output. |
| Done | Plan 4.5; frame section 2 rules 1-11 apply; ruff check, ruff format --check, mypy strict, full pytest green (in a dispatcher window); AD-5's measured test recorded and the container chosen within its criteria (or a STOP); the cache side of V17 proven; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: the design table.** Before product code, write in the ledger: the on-disk
   layout (entry folder or pack file per key, index, completeness marker); the key-to-name rule
   (all three key fields in the name, so a version mismatch never matches); the write sequence
   and its crash behaviour (question 3); the eviction order, trigger and unit (bytes on disk;
   questions 4 and 5); what happens to entries of another cache version (question 6); the
   thread-safety model (question 8); the statistics encoding (question 9); the measured-test
   plan (candidates, clips, frame counts, figures, question 10); and how the amended IF-7 is
   met (where the completeness marker lives, when `stages` counts a stage as covering).
   YIELD for the dispatcher.
2. **AD-5 measured test (`tools/cache_store_test.py`).**
   - Proxies from real footage: GX011627 (all 681 frames, 4K, 30000/1001) and a sample of
     GX011625 (deep, 498 s), decoded through the FFmpeg CLI to 960 x 540 `rgb24` by area
     averaging (AD-5: "area-averaged (block mean) from the full decoded frame"; 3840 x 2160 is
     an exact 4 x 4 block), and the float proxy beside each for the statistics check.
   - Candidates (AD-5 as amended, ruling 2): lossless: per-frame deflate (PNG filtering +
     zlib, stdlib), FFV1 and UT Video intra streams through the FFmpeg CLI; lossy: an FFmpeg
     intra stream at a near-lossless quality setting, and JPEG at high quality.
   - Figures per candidate: bytes per frame (median, max), extrapolated to a 60-minute clip at
     29.97 fps (107,892 frames), against AD-5's 10 GB; the statistics criteria (means and
     gains within 1e-3 relative, N{} bounds within 1 %, measured against the float proxy with
     the prototype's measurements as reference, `tools/prototype` read-only); random access
     by pts (the IF reads one frame at a time); the per-proxy read cost (EXCLUSIVE window);
     and, per candidate, the max abs error against the 8-bit proxy (information for CP5).
   - **The arithmetic risk, stated up front:** a 960 x 540 x 3 proxy is 1,555,200 bytes raw;
     10 GB over 107,892 frames is about 92.7 KB per frame, a lossless ratio of about 16.8:1.
   - **The choice (ruling 2):** a lossless candidate where one fits the 10 GB bound;
     otherwise the best lossy candidate that meets AD-5's statistics criteria against the
     FLOAT proxy. The store feeds the statistics and the scrub-time display only (G4: at rest
     the preview is the full-resolution corrected frame). STOP to CHARC with the figures only
     if NO candidate meets both the criteria and the bound (CHARC then chooses the bound or the
     270 proxy). A chosen candidate that needs a library in `src/` (Pillow for JPEG) is a
     dependency STOP unless CHARC extends the grant; one that needs an FFmpeg process per read
     carries its read cost into the choice.
3. **The store (IF-7).**
   - `store_proxy` refuses anything but `uint8` `(H, W, 3)`, and a shape that differs from the
     entry's first proxy; `proxy` returns the stored array bit-identical for a lossless store,
     within the measured error of task 2 for a lossy one, `KeyError` when absent (as the stub).
   - `store_source_statistics` stores each named array with dtype and shape exactly;
     `source_statistics` returns them exactly, `KeyError` when nothing is stored for that key,
     stage and pts.
   - `lookup` returns None for an unknown key or a key differing in any of size, `mtime_ns`,
     `cache_version`; otherwise a `CacheEntry` with `pts_ticks` ascending, `stages` sorted and
     only those covering every pts in `pts_ticks`, `size_bytes` the bytes on disk, and
     `complete` True only after `mark_complete` (durable: it survives a new instance; an entry
     left by a crash or cancel is never complete).
   - Proxies stored earlier in a running analysis are readable before the entry completes
     (AD-15: scrubbing shows the provisional preview while analysis runs).
4. **Limit and eviction (D71).** `limit_bytes`/`set_limit_bytes` (a negative limit refused);
   eviction runs on store and on `set_limit_bytes`, oldest first per question 4, never the
   entry being written (question 5); the total stays at or under the limit except as
   question 5 rules.
5. **Clear and crash safety.** `clear()` removes every cache entry and nothing else (it never
   follows a link, never deletes a file the cache did not name, never leaves the folder);
   leftovers of a crash (half-written files, an entry without its completeness marker) are
   removed or ignored when the cache opens; a corrupt index makes its entry a miss, never an
   exception from `lookup`.
6. **Tests** (all under `tmp_path`; the real `cache_dir` is never resolved: a test
   monkeypatches `clearwater.config.paths.app_locations` and asserts it is not called):
   - V17, cache side: store, `mark_complete`, reopen a new instance on the same folder,
     `lookup` finds the entry with `complete` True and every proxy reads back as the store
     promises (bit-identical if lossless); without `mark_complete`, `complete` is False; a changed size, `mtime_ns` or
     `cache_version` gives None; a key from `cache_key(path)` changes when the file is
     touched;
   - statistics round trip exact through `source_statistics` (float64 bits, shapes, names);
     `stages` omits a stage stored for only some pts;
   - eviction order with controlled stamps; lowering the limit evicts; the entry being
     written survives; the 20 GB default is `DEFAULT_CACHE_LIMIT_BYTES`, not restated;
   - `clear()` with a foreign file and a symlink planted in the folder (both survive);
   - crash: a child process killed mid-entry, then a new instance: no exception, the partial
     is never reported `complete`, its bytes are counted (or reclaimed), and a fresh store to
     the same key completes it;
   - one writer thread storing while reader threads call `proxy` and `lookup`;
   - a planted wrong implementation fails by name: newest-first eviction, a key that ignores
     `mtime_ns`, a round trip outside the chosen store's promise, `clear()` deleting a
     non-cache file, `lookup` returning a half-written entry as complete, `stages` listing a
     partly covered stage;
   - IF conformance: an `isinstance(store, ProxyCache)` check and a mypy assignment as in
     `stubs.py`;
   - dependency rule (plan 8.1, frame rule 5): importing `clearwater.cache` loads nothing from
     `clearwater.gui`, `.jobs`, `.methods`, `.io`, `.core`, nor `PySide6`, `cupy`, `PIL`.

## Declared operating envelope

Windows 11; the cache folder on the local NTFS system volume (`%LOCALAPPDATA%\Clearwater\cache`,
AD-25 (a)); sources on local NTFS or exFAT volumes (an exFAT modification time is coarser than
NTFS, but stable between reads); one Clearwater process, with one analysis writer and the
preview's readers on other threads of that process; cache files written only by Clearwater.
Out of envelope: two processes sharing a cache folder, a roaming or network profile, a
hand-edited or foreign file posing as a cache entry, two different source files with equal
size and modification time (they share a key by D71's definition; stated as a limit), other
operating systems (portable, N1, not run there).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.12\rN\`; ledger `docs/proofs/wp3.12-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r2\`
  (`run_review.sh`, `review-prompt.md`; the round also keeps `probe.txt`, `review-diff.txt`,
  `review.txt`, `adjudication.md`, `md5sums.txt`, `test-summary.txt` as there); the reviewer
  excludes `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - a stale entry can never be served: every key field in the identity, the version mismatch,
    a half-written entry, a corrupt index;
  - the round trip as the chosen store promises (bit-identical if lossless, within the
    recorded error if lossy) for proxies, and exact for statistics;
  - `complete` and `stages` exactly as the amended IF-7 docstrings say;
  - eviction: oldest first as ruled, bounded total, the in-use entry safe, no file deleted that
    the cache did not write;
  - crash and concurrency: no torn read, no exception escaping `lookup` on damaged files;
  - the measured test's figures against AD-5's criteria, and whether its extrapolation holds;
  - no path to the real app-data folder from a test; nothing in `interfaces/` changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Yields.** Round 0: read and table, then YIELD before product code. After each review
  round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating. Yield
  at every round boundary; the dispatcher reads your depth (~250K evaluation point, ~400K
  stop).
- **Full-pytest windows (X5).** The full suite (about 1844 tests, 9-11 min) runs ONLY in a
  window the dispatcher grants by message, in the background with output to a file under
  `work/`; send `WINDOW RELEASED: <summary>` when it finishes and carry on. Inner loops run only
  your own tests. The EXCLUSIVE read-cost window of task 2 is a separate grant; do not start it
  unasked.
- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the public API, the on-disk layout, the AD-5 table (candidate, bytes per frame,
  60-minute extrapolation, statistics deviation, read cost), the choice and why, the eviction
  rule, the gates, the Reviewer A rounds and verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20; IF-7 is already
  amended, ruling 1); no candidate meeting both AD-5's criteria and the bound; a dependency (none is granted; FFmpeg
  is a CLI tool, used by the instrument only); any OS-specific code; a test that would touch
  the real app-data folder; any write to the footage folder; the round-0 table showing a
  choice the brief left open.
- **Working rules:** `uv sync`. Commit by pathspec, `feat(wp3.12): ...` (conventional commits
  carrying the WP id), with a `Co-Authored-By:` footer naming your model. Never a bare `cd`.
  Never post to a mailbox. Gates: ruff check, ruff format --check, mypy strict, full pytest (in
  a window); no harness gate. Report `docs/reports/wp3.12-proxy-cache.md` (claims, evidence
  paths, limits). Outputs of the instrument go under `work/wp3.12/`. GoPro IMU/GPS data is out
  of scope everywhere.

## Rulings (CHARC `53b752a4d7fac4fc`, 2026-10-20)

CHARC `53b752a4d7fac4fc`, 2026-10-20: every recommended answer is the ruling unless amended here.
- **1 (IF-7, AD-20 amended on main `718da66`):** ALREADY APPLIED by the orchestrator on main
  before dispatch, in the base: `ProxyCache.source_statistics(key, stage, pts_ticks) ->
  Statistics` (`KeyError` when absent), `ProxyCache.mark_complete(key)`, `CacheEntry.complete:
  bool` (True only once the proxy pass for the whole clip is stored; a required field, no
  default), `CacheEntry.stages` lists only stages whose statistics cover every pts in
  `pts_ticks`; stubs updated. `interfaces/` stays out of the cell's ownership; the cell
  implements the amended protocol. The IF-5 `VideoSink.abort` docstring rode on the same touch.
- **2 AMENDED (AD-5 amended on main `718da66`):** the measured test ALSO admits lossy intra
  candidates (an FFmpeg intra stream at a near-lossless quality setting, or JPEG at high
  quality), judged by AD-5's statistics criteria against the FLOAT proxy; lossless is chosen
  where it fits 10 GB, otherwise the best lossy candidate meeting the criteria. The max abs
  error against the 8-bit proxy is reported per candidate (information for CP5). STOP with the
  figures only if NO candidate meets criteria and bound (CHARC then chooses the bound or the 270
  proxy). Ground: G4 makes the full-resolution corrected frame the preview at rest, so the
  store feeds statistics and scrub-time display only.
- **X-B1:** as drafted.
- **11:** CHARC accepted the correction: `CacheKey` stays as frozen; parameter binding is IF-4
  `schema_hash`. The chapter-group cache sentences are gone in v0.5.4; spec 7.2 line 325 goes on
  the owner's next-revision list.

### Questions as drafted (recommended answer first)

1. **SUPERSEDED by ruling 1 (applied as recommended, except that `complete` is a required
   field with no default).** **Two gaps in the frozen IF-7 (needs a CHARC ruling before
   dispatch: AD-20, frame rule 11).** (a) There is `store_source_statistics` but no way to READ
   them back, so AD-7's cached Ancuti stage-1 statistics could be written and never used. (b)
   Nothing marks an entry complete: after a cancelled or crashed analysis, `lookup` returns a
   `CacheEntry` that looks like a finished one, and V17's "skips the decode pass" would skip it
   wrongly. Recommended: a CHARC amendment under AD-20 before dispatch, adding to
   `ProxyCache` `source_statistics(key, stage, pts_ticks) -> Statistics` (`KeyError` if absent)
   and `mark_complete(key) -> None`, and to `CacheEntry` a trailing `complete: bool = False`,
   with `StubProxyCache` updated; `lookup` keeps returning in-progress entries (AD-15 needs
   their proxies) and WP3.11 skips the decode pass only on `complete`. For CHARC, not the cell:
   that amendment is "the next interface touch", so the pending IF-5 `VideoSink.abort`
   docstring erratum (D84 → D44/D85) can ride on it. Alternative: no amendment; WP3.12 adds
   both as public methods of its concrete class and WP3.11 consumes the class, not the
   protocol.
2. **SUPERSEDED by ruling 2.** **The AD-5 container, and what if none fits.** Recommended: the measured test of task 2;
   among candidates that meet both criteria, the one with per-frame random access and the lower
   read cost (expected: per-frame deflate in a pack file per entry, stdlib only, no FFmpeg
   process per scrub step). If none meets 10 GB per 60 minutes (the arithmetic needs about
   16.8:1 lossless), STOP with the figures; CHARC then chooses between a lossy store held to
   AD-5's statistics tolerances, a looser size bound, or a different proxy size (AD-5 change).
3. **X-B1 (cross-brief, WP3.6 and WP3.12): write semantics for cache files.** `clearwater.jobs`
   offers `SafeWrite`, built for user outputs: it numbers a taken name `_2` and its
   `.clearwater-partial-` temporaries are what `remove_leftovers` scans in output folders; a
   renumbered cache file would be orphaned. A cache entry needs atomic REPLACE inside a folder
   the cache owns, not no-overwrite. Recommended: no `SafeWrite`; a temporary in the cache
   folder then `os.replace` (as `clearwater.config.atomic_write_text` does for text), no
   `fsync` per proxy (about 108,000 per hour of footage), durability from the completeness
   marker (`mark_complete`, ruling 1) written and synced last; the cache's own leftovers cleaned when it
   opens. N8 is untouched: no user file can be in the cache folder's entry names.
4. **"Oldest entries removed first".** Recommended: oldest by LAST USE (a `lookup` hit and a
   completed store refresh the entry's stamp), so the clip being worked on survives a batch of
   others. Alternative: the literal reading, oldest by creation.
5. **The entry in use, and one entry larger than the limit.** A 60-minute clip may exceed a
   lowered limit on its own. Recommended: the entry being written and the most recently
   looked-up entry are never evicted; if they alone exceed the limit, the cache keeps them,
   logs a warning and evicts everything else; storing continues (refusing would break the
   analysis mid-clip).
6. **Entries of another cache version.** Recommended: removed when the cache opens (they can
   never match again, D113), not left to eviction.
7. **Key derivation and the version constant.** Recommended: `cache_key(path)` reads
   `os.stat(path)` (`st_size`, `st_mtime_ns`) with `CACHE_FORMAT_VERSION = 1` in
   `clearwater.cache`; the source is opened by nobody here. The equal-size-and-mtime limit is
   stated in the report.
8. **Threads.** Recommended: one lock per cache instance around index and eviction updates;
   proxy file reads outside it; one writer at a time per key (a second writer to the same key
   is a `RuntimeError`). Two processes are out of envelope.
9. **Statistics encoding.** Recommended: a small binary or JSON record per (stage, pts) holding
   name, dtype, shape and the raw bytes; never `pickle` (`numpy.load` with
   `allow_pickle=False` if `.npy` is used).
10. **Where the measured test lives.** Frame rule 1 owns no `tools/` file. Recommended: one
    instrument `tools/cache_store_test.py` (owned, X1-style; mypy-checked; FFmpeg CLI through
    `clearwater.io.video.find_tool`), its figures in the report, its outputs under
    `work/wp3.12/`, the read-cost figure only in a dispatcher-granted EXCLUSIVE window.
11. **"Keyed by the provenance object (AD-13) plus source identity" (CHARC addition, 2026-10-20
    22:06Z).** This conflicts with the frozen IF-7 `CacheKey(size, mtime_ns, cache_version)`,
    with D113 ("the cache holds only results that depend on the source file alone") and with
    7.3 ("statistics that depend on parameters or earlier stages, are always recomputed"): the
    AD-13 object carries the method and parameters, so a key containing it would split one
    clip's proxies per parameter state and break V17's "reopening an unchanged clip skips the
    decode pass" after any parameter change. Recommended: the key stays source identity plus
    cache version, exactly as frozen; the provenance object enters nothing in the cache. If the
    intent was that parameter-dependent statistics are tied to the parameters that shaped
    them, that is IF-4's `schema_hash` ("method id + params that shaped the stats"), WP3.11's.
    A key change would be an IF-7 change (AD-20) in any case.
