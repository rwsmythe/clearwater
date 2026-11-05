# WP6.3a accept record (orchestrator generation 47, 2026-11-05)

**Package:** WP6.3a, the GPU pack downloader. From Tools > Install GPU support... or the headless `--install-gpu-pack` row, Clearwater downloads the eleven locked wheels (1.725 GB) from `files.pythonhosted.org`, checks each against the lock's sha256, unpacks into staging with an fsync per file, runs the full check against the in-memory manifest, writes the manifest, runs the cheap check on disk, and renames into `<pack root>/<stamp>`. Tools > Remove GPU support and `--remove-gpu-pack` remove it; a pack that is loaded (this process or another, found by write-open, never by rename) gets a pending-removal marker that the next GUI start applies. One install lock per pack root. The loader (AD-33) is unchanged except for the S3 reparse-point rule and the cancel hook.

**The record:**
- **Brief:** `docs/briefs/wp6.3a-brief.md`, FINAL by CHARC (gen 15), with CHARC gen 16's rulings: Round 0 (S1-S3; DR-128 opened), Reviewer A r1, the Turn-4 STOP ruling (the cancel hook), Reviewer A r2 (the three layers), Reviewer A r3, the Delta-review ruling (the `__main__` sweep condition), Reviewer B r1 (F1 fsync, F2, F5, the N13 line), and the B-fold delta ruling (A4, the corrected N13 wording).
- **Lane: Codex `implementer-codex-sol-high`**, the lower weekly pace at commission (Codex 2 % / 0.464; Claude 39 % / 1.183; read 2026-11-04 17:21Z). Four sessions, each depth read at the turn end, of 475,000:
  - `01a1a7a2-8204-7da1-93fa-d27f5371cf9d`: turns 1-2 (round 0; build part 1). 119,874 (t1), 189,696 (t2); retired.
  - `01a1a7b8-97bb-7451-bb5a-adeb5a5c6387`: turns 3-4 (build part 2; the read-only turn-4 STOP on A r1 finding 8). 140,581 (t3), 192,162 (t4); retired by the Turn-4 ruling.
  - `01a1a842-6a14-78c0-984e-95b8ca1035e8`: turns 5-6 (the A r1 and A r2 fold-ins). 160,597 (t5), 229,611 (t6); retired.
  - `01a1a8c0-d4d8-79d3-9058-286f5c95ee6b`: turns 7-11 (the A r3, delta, B r1 and B-fold folds; the N13 wording). 109,576 (t7), 137,204 (t8), 198,141 (t9), 217,268 (t10), 226,196 (t11); retired at the package's end.
- **Reviewers were the other model (Claude) in both nets**, each a read-only `claude -p` process at the seat (`codex_cell.py review`) on the detached copy `.worktrees/wp6.3a-rA`. Every review prompt banned `run_in_background`, and every `review.txt` was checked to be the full report.
- **Report:** `docs/reports/wp6.3a-gpu-pack-downloader.md`.
- **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp6.3a\`: `cell\` (dispatches, prompts, returns and transcripts 1-11); `A\r1`, `A\r2`, `A\r3`, `A\delta`; `B\r1`, `B\delta`, `B\delta2`; `seat\` (the kit, run 2 of record, `run1\`); `gate\` (copied from the seat folder at this accept).

**Candidate:** branch `wp6.3a`, base `73453bdc`.
- The product code is FINAL at `eb80136a` (turn 11). `fb22270e` fills the report's seat re-run and depths (docs only).
- `7a82ce11` merges main `aaa8fc92` (docs only) before the gate; `e005180d` merges main `46508e13` (state docs and CHARC's WP6.4 brief tail only) before this record.
- The gate's head is `7a82ce11`.

**Footprint** (`git diff --name-only main...wp6.3a`), every path owned by the brief or granted by a ruling:
- NEW `src/clearwater/gpu_pack_install.py` (the downloader, the removal, the lock, the probe);
- `src/clearwater/gpu_pack.py` (the URL and size columns; the `activate()` warning filter; S1's `manifest=` parameter; S2's projection; S3's lstat / reparse rule; the Turn-4 cancel hook; the activation status at module level, A r2 layer 1);
- NEW `src/clearwater/gui/gpu_pack_dialog.py`; `src/clearwater/gui/shell.py` (the two Tools actions, their enabling, the pending text, F5's guards);
- `src/clearwater/__main__.py` (the `--install-gpu-pack` / `--remove-gpu-pack` rows; the GUI-start `apply_pending_removal` call and its widened condition, delta F1; the marker skip on the worker and `-m` branches; B F5's `OSError` guards);
- `tests/test_gpu_pack_install.py`, `tests/test_gui_gpu_pack_dialog.py` (new), `tests/test_gpu_pack.py`, `tests/test_frozen_entry.py`, `tests/test_tools_package_build.py`;
- `tools/package/build.py` (the hand-filled manifest writer now delegates to the installer's `manifest_document`, so both routes write one document), `tools/package/README.md` (the hand-filled-pack section; the install recipe);
- `docs/user-guide.md` section 2 (the GPU support paragraph; WP6.4's section-7 notice merges at its own accept);
- the report and this record.

## Nets

| Net | Head | Verdict | Disposition |
|---|---|---|---|
| A r1 | `53748e82` | NEW_CRITICAL_MAJOR_FOUND: CRITICAL the top-level-only `.data` rule; MAJOR remove while loaded; MINOR the 2,679 census; folds 4-6, 8, 9; mutants m2a/m2b/m4a/m4b | CHARC ruling; turn 4 STOP (finding 8, the cancel hook granted); turn 5 |
| A r2 | `92576d2e` | NEW_CRITICAL_MAJOR_FOUND: F1 MAJOR, a mapped image blocks deletion, not the folder rename (reproduced by CHARC); F2, F3 MINOR; F4, F5 | Ruling A (three layers: this-process status, the `O_RDWR` probe, the fail-safe); turn 6 |
| A r3 | `ffb8896e` | NO_NEW_CRITICAL_MAJOR, 2 MINOR + 3 ADVISORY. **Converged at r3** | all five folded, turn 7 |
| A delta | `9c2bdded` | NO_NEW_CRITICAL_MAJOR; F1 the every-start sweep was never reached (`__main__` called it only with the marker); F2 | turn 8 (F1 the second `__main__` grant) |
| B r1 (full) | `273636db` | NEW_CRITICAL_MAJOR_FOUND: F1 MAJOR no fsync before the rename; F2 MINOR read-phase `OSError`; 7 ADVISORY | turn 9 (F1 fsync per file and manifest, directory fsync off win32; F2 + F4; F3, F5 guards, F6, F7; F9 tests and the N13 line); F8 to the register |
| B delta | `f55175b4` | NO_NEW_CRITICAL_MAJOR; all eight B r1 folds held executed, 10 of 10 mutants; six advisories | turn 10 (A1, A3, A5, A6); A2 to the F8 row; A4 the N13 wording, turn 11 |
| B delta 2 | `eb80136a` | NO_NEW_CRITICAL_MAJOR; ADV-1..3 recommended to bank | banked into WP6.3b's fill |

Seat QA of every turn: the diff read against its dispatch; owned and granted files only; 0 CR in every changed blob.

## The seat run of record (gen 46, run 2 on `eb80136a`, 2026-11-05 00:24:16Z-00:28:44Z)

Kit `wp6.3a\seat\seat63a.sh` and helpers, md5-checked 7 of 7; all app data redirected to `.worktrees\wp6.3a\work\wp6.3a\appdata`; no GUI launched and no desktop input sent. Run 1 (on `a76a7723`, before the B r1 fold) is kept in `seat\run1\` with the same outcomes.

- onedir build exit 0, 85 s, both PASS lines.
- Real frozen headless install: exit 0, 123.6 s wall (network-dominated; run 1 was 248.1 s), no window; the corrected N13 line on stdout once, before the download.
- `build.py --verify`: PASS, 11 distributions, 2,679 files, 2,412.6 MiB. Census: 2,679 files, `SET_EQUAL_RECORD` and `SET_EQUAL_HANDFILLED_MINUS_UV` true (WP6.1's hand-filled pack minus uv's 22 `INSTALLER` / `REQUESTED` files).
- Two frozen workers on the downloaded pack: heic 21.3 s and video 12.6 s, both `ok`, device GPU, 67 CUDA files mapped.
- Remove while loaded: a bounded source child loaded the pack (56 images mapped); a frozen `--remove-gpu-pack` from a second process returned exit 0 "will be removed at the next start" with the marker written, the pack intact and not renamed, 0 partials. After the child's exit a second remove deleted the pack: marker, pack and partials absent.
- `--verify` after the loaded remove: 143 unlisted `__pycache__/*.pyc` written by the KIT's source child (no `-B`); every RECORD file intact. A seat-kit gap, not a product defect (the frozen product writes no bytecode; WP6.1's pack holds 0 `.pyc` after many frozen runs). A later kit that maps a pack from a source child adds `-B`.
- The owner log's md5 unchanged; the real `%LOCALAPPDATA%\Clearwater` absent before and after; no Clearwater process left.
- The fsync cost (2,680 fsyncs) is not measurable against a network-dominated install; the report says so.

## Gate (`p63a` + `p63a-s`, on `7a82ce11`, alone on the machine, the stall watch on every leg)

| Check | Result |
|---|---|
| `df -h /c` | 65 GB free at p63a's start; 73 GB at p63a-s's start; 73 GB at its end |
| static | ruff exit 0; format exit 0 (327 files); mypy exit 0 (163 source files) |
| collection identity | 7,285 + 1,298 + 7 = 8,590 = all; 0 duplicates; 0 differences |
| parallel | exit 0, 649 s: 7,284 passed, 1 skipped (the by-design yuvj case) |
| serial (p63a-s) | exit 0, 2,429 s: 1,298 passed |
| harness | exit 0: Ran 423 tests, OK (skipped=1) |
| footprint | owned and granted paths only (above); 0 CR in every changed blob |
| the real `%LOCALAPPDATA%\Clearwater` | ABSENT after the gate |

p63a's static, collect, parallel and harness legs ran at gen 46 (00:33-00:45Z); the serial leg ran at gen 47 as `p63a-s` on the same head with nothing else heavy running. Main moved between the two only by state documents. The fullclip leg was not run: the brief names no fullclip check, and no correction, I/O or encode code changed.

Summaries, verbatim:

```
head 7a82ce11 start 00:33:30Z free 65G
leg static start 00:33:31Z free 65G
ruff exit 0
format exit 0 327 files already formatted
mypy exit 0 Success: no issues found in 163 source files
leg collect start 00:33:32Z free 65G
collect-all exit 0 ids 8590 uniq 8590: 8590 tests collected in 10.93s
collect-parallel exit 0 ids 7285 uniq 7285: 7285/8590 tests collected (1305 deselected) in 2.67s
collect-serial exit 0 ids 1298 uniq 1298: 1298/8590 tests collected (7292 deselected) in 2.56s
collect-fullclip exit 0 ids 7 uniq 7: 7/8590 tests collected (8583 deselected) in 2.47s
identity: union 8590 dup 0 diff-vs-all 0
leg parallel start 00:34:01Z free 65G
parallel exit 0 649 s: 7284 passed, 1 skipped, 5 warnings in 646.90s (0:10:46)
leg harness start 00:44:51Z free 73G
harness exit 0 Ran 423 tests in 20.316s OK (skipped=1) 
end 00:45:12Z free 73G
head 7a82ce11 start 00:47:10Z free 73G
leg serial start 00:47:11Z free 73G
serial exit 0 2429 s: 1298 passed, 7292 deselected, 1 warning in 2425.57s (0:40:25)
end 01:27:40Z free 73G
```

## Dispositions (for CHARC at this accept)

- **DR-128 (the reparse-point / symlink rule absent from the full check): CLOSE.** Built here under S3: `os.lstat` per listed file, `S_ISLNK` refused, `FILE_ATTRIBUTE_REPARSE_POINT` refused on win32 (AD-36 form); the removal probe skips links and reparse points (R3-5).
- **AD-33: amend.** The installer (the plan, staging, fsync per file and manifest, full check on the in-memory manifest, manifest written last, cheap check on disk, rename); "a loaded pack is detected by write-open, never by rename" (A r2); the pending-removal marker and its GUI-start application; the census note (2,679 files; the hand-filled pack carried uv's 22); the cancel hook (full check only, at file boundaries).
- **AD-34: amend.** The `--install-gpu-pack` and `--remove-gpu-pack` rows. **Their exit 2 on extra arguments is AD-34's refusal status and is CORRECT (CHARC's F9 ruling);** the brief's "0 / 1" covered the requested-state and failure outcomes.
- **N13 note:** the dialog and the headless install carry the same one-line statement. The text as built (CHARC A4's correction), **to be shown to the OWNER at this accept** (design item 9; the owner's word may still change it):

  > GPU support downloads CuPy and NVIDIA's CUDA runtime libraries from PyPI into your user folder. The NVIDIA libraries are provided by NVIDIA under the NVIDIA Software License Agreement (the file `License.txt` in each NVIDIA package's `.dist-info` folder after the install); CuPy is MIT. Clearwater does not redistribute them.
- **Register row (B F8, with the delta's A2):** after a deferred removal in a GUI session that still has the pack loaded, that session's later export workers and `-m` children see the marker and run on CPU while the status bar's device line can still say GPU; and the cross-process case, where a marker appearing from another process flips the shell to "CPU: GPU pack removal pending" while this session still has the pack loaded. Fix candidate: the shell's pending text applied to the export device line.
- **Banked advisories:** A r1's 7, 10, 11 (in the report); B delta 2's ADV-1..3 into WP6.3b's fill (post-publication non-`OSError` reporting; the PowerShell recipe's `install.err` and remove form; the A5 fallback that has never run). A3's rest (the N13 line also prints for the GUI install job, "already installed" and `pack_root` None) is disclosed in the report.
- **Owed prunes, on the owner's word:** `.worktrees/wp6.3a/work/` (two onedir builds, `appdata-run1`, `frozen-runs-run1`, run 2's frozen runs; the pack itself was removed by the seat legs); the WP6.1 builds and hand-filled pack, which 6.3a's census no longer needs.

## Merge

The harness gate was run with this record in the worktree after the merge of main (the package code unchanged since the gate head): `uv run python -m unittest discover -s tests/harness` -> Ran 423 tests, OK (skipped=1). No registration is needed (`docs/proofs/` is an instance-surface prefix). The record is committed on `wp6.3a` by pathspec, and `main` is fast-forwarded to `wp6.3a` by the orchestrator. Released after the merge: `.worktrees/wp6.3a-rA`. `.worktrees/wp6.3a` is kept until the owner's word prunes its builds. Main is ahead of `origin/main`; a push needs the owner's word.
