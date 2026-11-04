# WP6.1 accept record (orchestrator generation 44, 2026-11-04)

**Package:** WP6.1, the packaging spike (Windows). Clearwater 1.0.0's tree is built with PyInstaller in the one-folder and the one-file forms, and both are measured. The GPU pack (CuPy plus the CUDA wheels) is loaded at run time from a per-user folder, proved in the frozen build. The report is what CP6a reads.

- **Brief:** `docs/briefs/wp6.1-brief.md`, FINAL by CHARC (gen 14), plus the "CHARC rulings at ..." bullets.
- **Lane: Claude `implementer-opus-high`**, cells wp61-cell1 to wp61-cell9. The rulings, incidents and retirements are in the ledger.
  - Retirement depths, as read by the dispatcher at each retirement:
    - wp61-cell3: 296,797;
    - wp61-cell4: 300,127;
    - wp61-cell5: 304,242;
    - wp61-cell7: 371,271;
    - wp61-cell8: 321,383;
    - wp61-cell9: 277,694, at its final report.
  - **The Reviewer B fold-in was one Codex turn** (`implementer-codex-sol-high`, fresh session `01a1a74f-bfb3-7880-a926-1c1927bcdd64`, 117,846 / 475,000 at the turn's end). It touched tests and the build tool only; `src/` was not touched.
- **Reviewers were the other model in both nets:**
  - Reviewer A: Codex, at the dispatcher's seat on a detached copy.
  - Reviewer B: Codex, at the orchestrator's seat (WSL script).
  - The fold-in delta was reviewed by Claude at the seat (`codex_cell.py review`).
- **Report:** `docs/reports/wp6.1-packaging-spike.md` (form-neutral, CHARC `85e45a92`).
- **Ledger:** `docs/proofs/wp6.1-ledger.md`.
- **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp6.1\`:
  - `cell\`: dispatches 1-12, 14 and 15 (13 was an inline message); turns `t3f`..`t3i`; `t3i\seat-run\` holds the seat-run script copies with their md5s; `codex-b\` holds the fold-in turn, `review-1\` and `bundle-recheck.txt`;
  - `A\r1`..`r5`;
  - `B\`;
  - `timings\t4\`;
  - `d6\`;
  - `gate\` (gate `p61`).

**Candidate:** branch `wp6.1`. The code is FINAL at `dc784b4f`; then the report at `68cc1f33`, the B fold-in at `7316b3ce`, and the merge of main `2503f196` at `e0bb6136` (the gate's head). This record and the ledger's depth fills follow.

**Footprint** (`git diff --name-only main...wp6.1`), every path owned by the brief:
- the product:
  - `src/clearwater/__main__.py` (the frozen re-entry handler and the F-E shim);
  - `src/clearwater/gpu_pack.py` (NEW, the loader);
  - `src/clearwater/app/composition.py`;
- the tests: `tests/test_frozen_entry.py`, `tests/test_gpu_pack.py`, `tests/test_tools_package_build.py`;
- the tools: `tools/package/build.py`, `tools/package/README.md`;
- the PyInstaller `dev` pin, after the N13 STOP: `pyproject.toml`, `uv.lock`;
- the report, the ledger and this record.

0 CR in every changed blob.

## Nets

| Net | Head | Result |
|---|---|---|
| Reviewer A r1 (Codex) | the turn-3 group-1 head | NEW_CRITICAL_MAJOR_FOUND. Folded in group 2a (ledger, "Reviewer A round 1 adjudication") |
| Reviewer A r2 | `526f3a8f` | NEW_CRITICAL_MAJOR_FOUND. Folded in 2b-1 / 2b-2 |
| Reviewer A r3 | `1e043cfc` | NEW_CRITICAL_MAJOR_FOUND, four MAJOR. Folded in the 2b-3 r3 batch (F-F and Q2 as CHARC ruled) |
| Reviewer A r4 | `e0a90bc5` | NEW_CRITICAL_MAJOR_FOUND, one MAJOR (the re-entry grammar). Folded in 2b-5 (`08a96243`, `09cbba2c`); CHARC `bae5dba5` |
| **Reviewer A r5** | `49150ccf` | **NO_NEW_CRITICAL_MAJOR (converged)**. One minor and three advisories, folded at `dc784b4f` (2c-a) |
| **Reviewer B** (WSL Codex, gpt-6.1-sol / high) | `dc784b4f` | **NO_NEW_CRITICAL_MAJOR**. Four MINOR and two ADVISORY, all six fixed in the Codex fold-in `7316b3ce` (CHARC `c85d332f`) |
| **Claude review of the fold-in** (`68cc1f33..7316b3ce`, opus, 42 turns, `is_error` false, worktree clean after) | `7316b3ce` | **NO_NEW_CRITICAL_MAJOR**. All six FIXED. Mutants caught: options walk removed 1 failed; bytecode restore removed 2 failed, success-path-only 1 failed; pre-fix matcher 16/18 failed, underscore prefixes 18/18 failed. `test_tools_package_build.py` 63 passed; `test_frozen_entry.py` 167 passed. Marker split 165 parallel / 2 serial. Isolation of every entry-point call read and confirmed before the run. Five advisories, below. Its 4 permission denials were compound shell lines it re-ran in allowed forms |

**Bundle re-check with the fold-in's checker.** `build.py` has no CLI checker, so the seat called `forbidden_paths(root)` and `forbidden_entries(find_executable(root))` read-only, from the wp6.1 venv, on both existing builds of `dc784b4f`:
- onedir: 0 path / 0 entry violations;
- onefile: 0 / 0.

Record: `codex-b\bundle-recheck.txt`.

## The frozen checks of record (seat-run, gen 43, from md5-checked copies)

- **GUI check: PASS.** Both forms were run with the pack present and with it absent:
  - first window 1.09 / 1.20 s (onedir) and 2.68 / 2.71 s (onefile);
  - the loader line `gpu pack 14.2.0-cu12: loaded` / `absent` verbatim;
  - clean `WM_CLOSE`, exit 0, no leftovers, no `_MEI` left;
  - `--verify` PASS before and after (2701 files, 2412.6 MiB);
  - the owner-log md5 `69ed0432...` unchanged.

  Ledger: "Group 2c". Evidence: `cell\t3i\`.
- **Timings: COMPLETE** (exclusive window from 15:46Z). Medians:

  | Form | Cold start | Warm start | First GPU export, warm cache | First GPU export, empty cache | CPU export, no pack |
  |---|---|---|---|---|---|
  | onedir | 4.469 s | 0.893 s | 1.285 s | 15.460 s | 0.531 s |
  | onefile | 2.771 s | 3.170 s | 3.220 s | 18.284 s | 2.728 s |

  Release sizes with FFmpeg: 668.3 MiB onedir, 523.9 MiB onefile. Evidence: `timings\t4\`; report section 2.
- **The GPU pack proof: PASS on both forms.** With the pack: `device GPU`, all CUDA files from the pack or the driver. Without it: `CPU: CuPy not installed` (AD-9's text). Ledger 2b-4 and 2b-6.

## The owner's checks

- **D6, the owner's hand check: PASS.** Run by the owner by hand on the onedir build of `dc784b4f`, 2026-11-04 16:11-16:51Z, from the seat-run script `gui_check.py owner --form onedir` (md5 `0e05e8e7171f73c74ece4715f87a75eb`).
  - The owner's words (via CHARC `810ee33b`, verbatim): "heid-ad24-both.png is black and white, other than that everything worked."
  - **Fixture note (CHARC):** `heic-ad24-both` is the AD-24 orientation fixture: 96x64, manifest content "ramp", no ICC, irot 270 plus EXIF orientation 6. It is a synthetic grey ramp with no colour, so a black-and-white output is the input's content, not a defect.
  - The seat's record (`d6\d6-onedir.stdout`, exit 0):
    - `export heic-ad24-both.heic: ok; device GPU`;
    - `export jpeg-gradient-display-p3.jpg: ok; device GPU`;
    - `export vfr.mp4: ok; device GPU` (through the export worker);
    - 6 / 3 EXIF entries on the two PNGs;
    - `Clearwater closed`, nothing left running;
    - owner-log md5 `69ed0432c562db9445daecbe8f15fe27` before = after;
    - no DR-125 exit code.
  - Onefile was not hand-checked: the owner's CP6a ruling chose onedir first.
  - **Lesson (CHARC) for WP6.3 / WP6.4 hand checks:** stage a REAL colour photo from the footage folder, copied under `work/` (the footage folder is read-only), so the owner judges the correction and not a fixture.
- **CP6a: ONEDIR** for 1.1.0, ruled by the owner (CHARC `c4b790e9`, verbatim "onedir; go; prune") on CHARC's recommendation. N14's figures are onedir's (the table above).

## DR-125 occurrences (the export worker crashes at exit after its result line, exit 3221225477)

- 1 of 12 frozen worker runs across 2b-4 and 2b-6;
- 0 of 12 in the timing window;
- 0 in the GUI check;
- 0 in D6.

CHARC writes the brief after this accept (Codex lane): the F-E stdin isolation moves into the worker and the `__main__` shim is removed, with fail-closed inherited.

## Gate (`p61`, on `e0bb6136`, alone on the machine, the stall watch on every leg)

| Check | Result |
|---|---|
| `df -h /c` | 86 GB free at the start, 84 GB at the end |
| static | ruff exit 0; format exit 0 (323 files); mypy exit 0 (161 source files) |
| collection identity | 7,134 + 1,275 + 7 = 8,416 = all; 0 duplicates; 0 differences |
| parallel | exit 0, 591 s: 7,133 passed, 1 skipped (`test_color_roundtrip.py:123`, the by-design yuvj case) |
| startup (the brief's GATE_CHECKS: the serial start-up modules plus the three owned test modules) | exit 0, 100 s: 545 passed |
| harness | exit 0: Ran 423 tests, OK (skipped=1) |
| footprint | the owned paths only (above); 0 CR in every changed blob |
| the real `%LOCALAPPDATA%\Clearwater` | ABSENT before and after the gate |

The serial and fullclip legs were not run: the brief's GATE_CHECKS name the start-up modules, and no correction, I/O or encode code changed.

Summary, verbatim:

```
head e0bb6136 start 16:59:53Z free 86G
leg static start 16:59:55Z free 86G
ruff exit 0
format exit 0 323 files already formatted
mypy exit 0 Success: no issues found in 161 source files
leg collect start 16:59:56Z free 86G
collect-all exit 0 ids 8416 uniq 8416: 8416 tests collected in 10.48s
collect-parallel exit 0 ids 7134 uniq 7134: 7134/8416 tests collected (1282 deselected) in 2.40s
collect-serial exit 0 ids 1275 uniq 1275: 1275/8416 tests collected (7141 deselected) in 2.40s
collect-fullclip exit 0 ids 7 uniq 7: 7/8416 tests collected (8409 deselected) in 2.43s
identity: union 8416 dup 0 diff-vs-all 0
leg parallel start 17:00:23Z free 86G
parallel exit 0 591 s: 7133 passed, 1 skipped, 5 warnings in 587.77s (0:09:47)
leg startup start 17:10:13Z free 84G
startup exit 0 100 s: 545 passed, 1 warning in 98.49s (0:01:38)
leg harness start 17:11:54Z free 84G
harness exit 0 Ran 423 tests in 22.365s OK (skipped=1) 
end 17:12:18Z free 84G
```

Archive: `clearwater-review-evidence\wp6.1\gate\`.

## Prune (owner's word "prune", via CHARC `c4b790e9` / `daee01fd`; done by the orchestrator at gen 44 pickup, 2026-11-04 ~16:56Z)

| Deleted | Size |
|---|---|
| `.worktrees\wp6.1\work\wp6.1\cold-onedir-1..3` (the timing window's cold copies) | 3 x 670 MiB |
| `.worktrees\wp6.1\work\wp6.1\cold-onefile-1..3` | 3 x 524 MiB |
| `.worktrees\wp-t8\work\` (WP-T8's gate basetemps and outputs), then `git worktree remove .worktrees\wp-t8` (branch `wp-t8` kept) | 9.3 GiB |

C: free went from 74,766 MiB to 87,906 MiB (+13.1 GB). Before the deletion, `grep` showed that no file under `tests/`, `src/` or `tools/` names these paths (DR-126's lesson). Nothing else was pruned on this word.

The following stay until a later word:
- `work\wp6.1\dist-on{dir,file}` and the builds' working folders;
- the hand-filled pack under the redirected `LOCALAPPDATA` (`work\wp6.1\t3c\appdata`);
- the D6 staging folders;
- the detached review copy `.worktrees\wp6.1-rA`, released at this accept as a worktree; it holds no `work/`.

## Dispositions (for CHARC at this accept)

- **AD-33** (the GPU pack loader) and **AD-34** (frozen spawn re-entry): material in report sections 7 and 6.
- **N13:** the PyInstaller row (`dev` group pin, GPL-2.0 with the bootloader exception).
- **N14:** the onedir figures (the table above).
- **DR-125:** the brief, as above.
- **Banked advisories from the Claude review of the fold-in**, for WP6.3, which next owns `build.py`, or the register:
  - (a) normalise `FORBIDDEN_DIST_INFO_PREFIXES` at definition, and test it against every `gpu_pack.LOCKED_DISTRIBUTIONS` row;
  - (b) the metadata rule misses `cupy-*`, `cuda_python-*` and `cuda_bindings-*` dist-info (only a metadata-only leak escapes; the code folders trip `gpu-module`);
  - (c) `test_frozen_entry.py:748-751`: a `TimeoutExpired` in the `finally` skips later children, and a late daemon-thread spawn after teardown is possible. Neither can touch app data (checked);
  - (d) `test_frozen_entry.py:638` / `:547`: a 10 s grandchild timeout is a parallel-leg wall-clock signal that predates the fold-in; raise it to 30 s or mark the test `slow`;
  - (e) out of envelope: option strings are split only on `/` and `\`; no custom options are set today.
- **Owed prunes:** the wp6.1 worktree's builds and the hand-filled pack, after WP6.3 no longer needs them; `.worktrees/wp6.2`'s copy.

## Merge

Harness gate run with this record and the ledger fills in the worktree (the package code unchanged since the gate head `e0bb6136`): `uv run python -m unittest discover -s tests/harness` -> Ran 423 tests, OK (skipped=1). No registration needed (`docs/proofs/` is an instance-surface prefix). The record and the fills are committed on `wp6.1` by pathspec; `main` is fast-forwarded to `wp6.1` by the orchestrator. Worktrees released after the merge: `.worktrees/wp6.1-rA` (the detached review copy). `.worktrees/wp6.1` is kept for WP6.3 (its builds and the hand-filled pack, pruned on the owner's word). Main is ahead of `origin/main`; a push needs the owner's word.
