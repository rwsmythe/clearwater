# WP5.2 accept record (orchestrator generation 35, 2026-11-02)

**Package:** WP5.2, performance and memory runs: V16 and V15 on full clips at the shipped defaults, the first real witness of the automatic CPU fallback (D111), the figures of record for the N6 re-set, DR-72 (the bench stops on a memory breach).
- **Brief:** `docs/briefs/wp5.2-brief.md` (FINAL by CHARC gen 12; three rulings folded: round 0 `6e0128fd`, WDDM `eade11c9`, W52-2 hang `a171ca08`).
- **Lane: CODEX**, `implementer-codex-sol-high`, four sessions, eight turns (session 1 `01a19bc5-...` round 0, retired at 169,581; session 2 `01a19bd1-...` turns 2-3, retired at 179,121; session 3 `01a19bf9-b056-7b61-8cdb-82396b6160d6` turns 4-6, retired at 194,184; session 4 `01a19d5c-ab8d-7522-8618-1a1b3117639e` turns 7-8, at **143,083** after turn 8). Both nets Claude (`claude -p --model opus --effort high`), the other model.
- **Report:** `docs/reports/wp5.2-performance-memory.md`. **Ledger:** `docs/proofs/wp5.2-ledger.md`. **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp5.2\` (`cell`, `r1`, `r2`, `B`, `gate`). **Window records:** `C:\Users\rwsmy\clearwater\work\wp5.2\` (`v16\W52-1\`, `W52-2\`, `W52-3\`, `photo\`, `scripts\`; never committed).

**Candidate:** branch `wp5.2`, rebased onto main `174b92b7` and gated as **`61d7b661`**; `git patch-id --stable` over the 13 branch commits (the 11 package commits and the brief's own fill and FINAL commits) equal before and after the rebase (`work/orch-g35/wp52-patchid-pre-gate.txt`, `-gate.txt`). This record's commit adds this file and the report's accept-time Limits paragraph (section 6, notes (a)-(f)) and its Reviewer B and Gate lines (docs only); the harness leg re-ran on it (below).

**Footprint** (`git diff --name-only main..wp5.2`, 9 paths plus this record): `tools/export_bench.py` (DR-72 only: exit 3 on `memory_check.passes == false`, `record["failed"]` kept, the docstring); NEW `tools/device_hold.py`, `tools/photo_memory.py` (R0-F3); NEW `tests/test_export_bench_breach.py` (parallel), `tests/test_device_hold.py` (`gpu`), `tests/test_photo_memory.py` (parallel); the brief, report and ledger. No product module, no dependency, no frozen interface, no fixture. Every changed blob 0 CR; the brief's 6 non-ASCII bytes predate the package.

## Nets

| Net | Result |
|---|---|
| Round 0 (turn 1) | anchors, holder and breach designs, Q1-Q4, run requests; CHARC `6e0128fd` (R1 flags, records in the main tree's work, `tools/photo_memory.py`, the whole GX011627). |
| T2 / T3 (turns 2-3) | DR-72 stop, the holder, the photo adapter, RED then GREEN; the WDDM STOP (each process sees its own free figure) ruled `eade11c9`, DR-114. |
| Reviewer A round 1 (`26f02528`; `...\r1\`) | **NEW_CRITICAL_MAJOR_FOUND**: the tool code sound; 2 MAJOR in the W52-2 run requests (shell state across fenced blocks; a failed held export cancelling the free and cpu legs), 7 MINOR, 6 ADVISORY; all dispositioned by the orchestrator, fixed in turn 4 (`959083eb`, fresh session 3). |
| Reviewer A round 2 (`959083eb`; `...\r2\`) | **NO_NEW_CRITICAL_MAJOR**, CONVERGED; 2 MINOR + 4 ADVISORY in the run-request text, fixed in turn 5 (R1 and R3 self-contained scripts, holder `--timeout-s 3600`, the held export under `timeout 2400`, the comparison always writing its JSON, R3's generator via a temporary name). |
| **Reviewer B** (Claude pass at the orchestrator's seat on `16c58b0e`, EXECUTING; `...\B\`) | **NO_NEW_CRITICAL_MAJOR**, 51 turns, `is_error` false, worktree clean after. Executed: the light tests 40 passed; `tests/test_device_hold.py` (gpu) 1 passed; a DR-72 mutation probe (stop removed: 6 failed, 4 passed). Every W52-1 row, the N6 figures, R2, R3, W52-3 and the cited baselines checked against the records: all equal. 6 ADVISORY, 0 MINOR: B-1 the W52-3 item wall exceeds the shell `time` by 0.34 s (clocks ~52 ppm apart); B-2 the ruled `timeout 7200` margin was 8.5 %; B-3 / B-4 `photo_memory.py`'s `None` RAM verdict and unprojected record keys (paths not reached); B-5 the "663 MiB after" label (checked: correct); B-6 the D111 witness leg has no AD-11 comparison (none can exist on this card). B-1..B-4 and B-6 written into the report's Limits at this accept; none needs a code change. |

## Windows (EXCLUSIVE, at the orchestrator's seat, from `.worktrees/wp5.2`; each opened and closed to CHARC)

- **W52-1** 12:48:16Z-14:55:15Z (127 min), R1 (the V16 plan): 8 runs, all ok, every memory check passing. GX011627 c3 NVENC cold 11.78 / 10.77 / 10.89 (median **10.889 min/min**; WP3.21 9.78, +11.3 %), warm 9.639, ancuti2018 9.959, libx265 20.44; synthetic 5.3K 8:7 40.33 (best effort; RSS 5,340 MiB, device 7,085 MiB); GX011625 sustained **10.779** (14,938 frames, 5,373 s; WP3.21 9.58, +12.5 %). Record `W52-1-export-bench-v16-20261102T124817Z.json` (sha256 `e93f0603...0495`).
- **W52-2** 15:03:59Z-17:42:42Z, R2 + R3. R2: holder 5,861 MiB, device-wide free 1,421 MiB during the hold; the HELD export ran ON THE GPU, exit 0, 4:04 (DR-114 on a real export); free exit 0, 4:03; held vs free 30 frames identical (seat-run after the window). The force-cpu export HUNG inside NVENC at about 670 of 681 frames (encoder main thread spinning, zero I/O; evidence `work\orch-g35\w52-2-cpu-hang.txt`); the orchestrator ended only the encoder at 17:38:10Z; the product failed the job and removed the partial (D85). STOP to CHARC; ruling `a171ca08`: **DR-115 opened**, W52-3 ruled. R3: the 48 MP PNG16, default device **"CPU: estimate 11,649 MiB exceeds free 7,064 MiB" = the D111 engagement witness**, RSS 6,635,884,544 B; forced CPU RSS 6,168,494,080 B; both exit 0, no failed check.
- **W52-3** 17:54:10Z-19:44:14Z, the force-cpu re-run under `timeout 7200` with a 60 s progress poll: COMPLETED, exit 0, 6,585 s (9.67 s/frame; a CPU-route rate, not a target); no hang (DR-115 intermittent). Free vs cpu, 30 frames post-encode: mean 3.329 / 255 (the WP5.1 characterisation, 3.5: passes), max 85 / 255; AD-11's numeric bounds not met through the encoder; the pre-encode AD-11 bound not proved by this leg.
- The three kept `_corrected.mp4` outputs (held, free, W52-3 cpu) were DELETED after the comparison as ruled (md5s in `work\orch-g35\kept-outputs-deleted.txt`); the 158 MB whole-clip stream copy (an input) stays in `work\wp5.2\W52-2\` until a prune ruling.

## Gate

The TWO-leg gate (GATE_CHECKS: no fullclip-marked test added and no fullclip node reads the changed tools), WP-T7's flags and redirects (`work/orch-g35/gate.sh`), on `61d7b661`, run id `w52`, Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`; no window open and nothing else running; stall watch armed throughout. C: 60 GB free at the start.
- **Static:** `ruff check` passed; `ruff format --check` 311 files already formatted; `mypy` no issues in 156 source files.
- **Collection:** all **7,877** = parallel 6,598 + serial 1,272 + fullclip 7; no duplicates; union identical to collect-all.
- **PARALLEL** (`-n 4 --timeout 600`): **6,597 passed, 1 skipped, 0 failed**, EXIT 0, 509 s. The skip is the standing swscale refusal (`test_color_roundtrip.py:123`). The 25 breach and photo-adapter nodes ran here, max 0.225 s. Log md5 `37ba279c94aaa5959a86c688f55e7b40`.
- **SERIAL** (`--timeout 1200`): **1,261 passed, 11 skipped, 0 failed**, EXIT 0, 1,974 s. The 11 skips are the standing look-check frames archived to D: (as d112 and dr113). `tests/test_device_hold.py::test_device_hold_releases_on_stop_file` passed (1.3 s). Log md5 `ebfef95299dcd0bce8afda795a8ca236`. C: 57 GB free at the end (20:47:48Z).
- **Harness gate:** 382 tests OK (1 skipped), 21 s on `61d7b661`; re-run on this record's commit (below the Merge heading).

## Dispositions (for CHARC at this accept)

- **N6:** CHARC writes the proposal to the owner from the report's section 2 (the GX011627 cold median 10.889, the GX011625 sustained 10.779, the GUI-path margin cited from WP4.6); the owner rules (spec D106 / N6 change, owner-reserved).
- **DR-72 CLOSED** (the bench stops with exit 3 on a memory-check failure; witnessed by the breach test and its mutation probe).
- **D111:** the first real engagement witness (R3) recorded; no D111 row needed (it engaged; its AD-11 comparison cannot exist on this card, B-6).
- **DR-114:** the held export's GPU route is its real-export evidence. **DR-115:** the W52-2 hang evidence and the W52-3 non-recurrence. **DR-70** note: the analysis-share re-read (report section 7). **AD-21** CLOSED note once N6 is set. Plan section 7 completion pointer for V15 / V16. An estimate-margin row only if CHARC reads section 5's ratios as warranting one (the 48 MP RSS ratio is 1.84x; no owner mode fell back falsely).

## Merge

`main` fast-forwarded to the rebased package plus this record's commit, by the orchestrator. The worktree `.worktrees/wp5.2` is released after the merge (its `work/` pruned only on the owner's word).
