# WP6.4 accept record (orchestrator generation 47, 2026-11-05)

**Package:** WP6.4, the macOS adaptation. Every product and tool site in the WP6.2 audit's tables is implemented or validated on Windows:
- the VideoToolbox roster, trials and command branch with the AD-35 rate mapping (both Q1 candidates selectable, neither chosen);
- the Library paths of AD-25(a);
- AD-37's `start_new_session` off win32;
- AD-36's guard form everywhere, with `mypy --platform darwin` green beside the default run;
- the identity-based queue and containment checks (DR-121 / DR-122);
- the AppleDouble exclusion;
- the platform-parameterised W tests;
- the `macos` marker with its M tests written and skipped on Windows;
- the CPU-only Mac dependency markers.

No Mac was run; WP6.5 runs the M tests natively.

**The record:**
- **Brief:** `docs/briefs/wp6.4-brief.md`, FINAL by CHARC gen 16 on gen 45's fill `c56f6272`. Then the Round-0 rulings, Group-A and Group-B yield rulings, the Turn-4 STOP ruling, Reviewer A r2 rulings (with the turn-5 note), Reviewer B rulings and the Reviewer A r4 ruling, all by CHARC gen 16.
- **Lane: Claude `implementer-opus-high`, by task fit.** The package edits a frozen-interface docstring (`interfaces/settings.py`, under CHARC's grant), so it is never Codex. Paces at the fill (20:26Z): Codex 4 % / 0.652, Claude 44 % / 1.265. Seven Agent-tool cells, each depth read with `scripts/cell_depth.py` at its yield:
  - `wp64-cell1`: round 0, 247,937.
  - `wp64-cell2`: group A, 392,066.
  - `wp64-cell3`: group B and the export grant, 416,156. **PAST the cap: a discipline breach recorded in the ledger.**
  - `wp64-cell4`: turn 4 (S-B1, M-TOOL, the P30 pair, the report), 175,078.
  - `wp64-cell5`: turn 5 (the A r2 fold-in), 314,460. Past the dispatch's 250K yield point but under the cap; a ledger deviation, no rework.
  - `wp64-cell6`: turn 6 (the A r3 fold), 168,651.
  - `wp64-cell7`: turn 7 (the Reviewer B fold), 183,979.
- **Reviewers were the other model (Codex) in both nets**, read-only, at the seat:
  - Reviewer A ran on the detached copy `.worktrees/wp6.4-rA`;
  - Reviewer B ran under WSL Linux (`wp6.4\B\run_review_B.sh`).
- **Report:** `docs/reports/wp6.4-macos-adaptation.md`.
- **Ledger:** `docs/proofs/wp6.4-ledger.md`.
- **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp6.4\`:
  - `cell\`: dispatches 1-7, the snapshots, the VT argument lists, the `uv lock` record, the darwin mypy record;
  - `A\r1`..`A\r4`;
  - `B\`;
  - `gate\`.

**Candidate:** branch `wp6.4`, base `c1458747`.
- The final code head is `54456365` (turn 7); `740910e4` fills the depth (docs only).
- `e2db371c` merges main `f1ab5057` (WP6.3a's accept) before the gate. The user guide's two sections merged cleanly: section 2 is 6.3a's and section 7 is 6.4's, so this package merged the guide second, as CHARC ruled.
- The gate p64 ran on `e2db371c`. Its serial leg failed (below); the seat reconciliation `f4ff6c88` (P31) followed, the serial re-run p64-s ran on it, and `e65ab384` (the COCOA_PROBE filter and the P31 docstring, both granted with no re-run) followed. `857140a1` merges main `a0e9106e` (docs only) before this record.

**Footprint** (`git diff --name-only main...wp6.4`), every path owned by the brief or granted by a ruling:
- **product:**
  - `config/paths.py`, `config/presets.py`;
  - `core/backend.py` (the one reason string);
  - `gui/batch_panel.py`, `gui/preview.py`, `gui/settings_dialog.py`;
  - `interfaces/settings.py` (the docstring grant);
  - `io/video/capability.py`, `encode.py`, `pipes.py`, `probe.py`;
  - `jobs/export.py` (the group-A ruling's one edit), `jobs/naming.py`.
- **tests:**
  - `conftest.py`;
  - NEW `tests/ffmpeg_text/` (S1);
  - `test_app_startup.py`, `test_gui_startup.py` (the redirection);
  - `test_config_paths.py` (S2's one edit);
  - `test_environment_report.py` (exactly three granted edits);
  - `test_export_oracle.py` (D4 (b)'s one edit);
  - `test_gui_batch_panel.py`, `test_interfaces.py` (the docstring assertion);
  - NEW `test_macos_portability.py`, NEW `test_portability.py`.
- **tools:**
  - `footage_guard.py` and its five callers (`inventory.py`, `lookcheck/frames.py`, `container_spike/compare.py`, `analysis_breakdown.py`, `export_oracle.py`);
  - `environment_report.py`;
  - D4 (a)'s eight docstring-only modules;
  - `prototype/bench.py`, `spike_io/transport.py`.
- `pyproject.toml` and `uv.lock` (the platform markers only; the eleven pack wheels unchanged).
- `docs/user-guide.md` section 7 (B6's one notice).
- The report, the ledger and this record.

## Nets

| Net | Head | Verdict | Disposition |
|---|---|---|---|
| A r1 (group A) | `27505be4` | NO_NEW_CRITICAL_MAJOR; 1 MINOR (already granted), 1 ADVISORY (the P30 pair) | turn 4 |
| A r2 (group B) | `107e6c77` | NEW_CRITICAL_MAJOR_FOUND: 6 MAJOR, 2 MINOR, 3 ADVISORY. Item 1 was the footage guard's `realpath(abspath())` collapsing `..` before the link, confirmed by CHARC; item 2 the borrowed-case monkeypatch leaks | CHARC rulings: items 1-5 and 9-11 folded; item 6 split (fold the Windows-boundable checks, bank the native ones to WP6.5); item 7 REJECTED; item 8 a report sentence. Turn 5 |
| A r3 (delta, turns 4 + 5) | `d55573f1` | NO_NEW_CRITICAL_MAJOR; 2 MINOR, 2 ADVISORY. **Converged at r3** | turn 6 (the test instruments) |
| B r1 (WSL Linux, full) | `d55573f1` | NEW_CRITICAL_MAJOR_FOUND: 3 MAJOR, 3 MINOR, 2 ADVISORY. B1 queue identities cached at add time, confirmed by CHARC; B2 four env-report tests fail on darwin; B3 a bind mount invisible to `realpath` | CHARC rulings: B1, B2 (the third edit), B4-B7 folded in turn 7; B3 BANKED; B8 no change |
| A r4 (delta, turns 6 + 7) | `740910e4` | NO_NEW_CRITICAL_MAJOR; 2 MINOR, both test-instrument evasions (W-GUARD exempting an unpatched launch operation; the borrowed-case pin missing an enclosing live patch context) | CHARC: BANKED, one register row of their own |

| P31 one-hunk delta (Codex) | `f4ff6c88` | NO_NEW_CRITICAL_MAJOR; four executed mutants die; MAJOR, the same conflict in `COCOA_PROBE` (`tests/test_macos_portability.py:1495`, the M side); MINOR, the docstring | CHARC `a0e9106e`: both fixed at the seat in `e65ab384`; no re-run, no further review |

Seat QA of every turn:
- the diff read against its dispatch;
- owned and granted files only;
- 0 CR in every changed blob;
- every cell-written script grepped for desktop input (none).

The Reviewer B WSL run was the instrument that found B1: it checked real POSIX `realpath` semantics directly, which two Windows-run A rounds missed.

## The P31 merge reconciliation (seat; CHARC `2ab52526`, `a0e9106e`)

WP6.4's `_gui_p31` pinned `tools.actions()` text == `["&Settings..."]`. WP6.3a, accepted first and merged at `e2db371c`, added "Install GPU support..." and "Remove GPU support" to Tools (`gui/shell.py:505-506`). Neither package's own gate could see the interaction. `_update_gpu_actions` (`shell.py:537-538`) hides both GPU actions when `gpu_pack.pack_root()` is None, as it always is on darwin, so P31's macOS premise holds for the VISIBLE actions. The seat rewrote the one test function:
- `pack_root` is monkeypatched BEFORE the window is built (the constructor probes it), and in both legs;
- leg 1, a tmp_path root, gives Settings and the two GPU actions;
- leg 2, None (the darwin form), gives Settings alone;
- both legs sit in one node, so collection stays at 9,002.

The Codex one-hunk delta found the same conflict on the native side: `COCOA_PROBE` serialized every Tools action, hidden ones included. `e65ab384` filters it by `isVisible()`; the `:1548` assertion is unchanged. The P31 docstring's first line says "when no pack root exists". CHARC's exact wording, naming `gpu_pack.pack_root()`, does not fit the 100-column line, so the docstring body names the call.

Checks on `e65ab384`: ruff and format clean on both files; the two portability modules whole, 185 passed / 224 skipped (W 168 + 17, M 205 + 19); collect 9,002; harness 423 OK.

## Gate (`p64` on `e2db371c`, serial re-run `p64-s` on `f4ff6c88`, alone on the machine, the stall watch on every leg)

| Check | Result |
|---|---|
| `df -h /c` | 73 GB free at p64's start; 71 GB at p64-s's end |
| static | ruff exit 0; format exit 0 (330 files); mypy exit 0 (164 source files) |
| `mypy --platform darwin` (the brief's W-STATIC) | exit 0: no issues found in 164 source files (run at the seat on `e2db371c` just before the gate) |
| collection identity | 7,658 + 1,337 + 7 = 9,002 = all; 0 duplicates; 0 differences |
| parallel | exit 0, 612 s: 7,452 passed, 206 skipped (205 parallel-leg M cases and the by-design yuvj case) |
| serial, p64 (`e2db371c`) | **exit 1, 3,182 s: 26 failed, 7 errors, 1,211 passed, 93 skipped.** P31 (above), plus 25 failures and 7 errors that were all `CUDA_ERROR_UNKNOWN` / `cudaErrorUnknown` from `test_prototype_backend` onward in that one pytest process |
| serial, p64-s (`f4ff6c88`) | **exit 0, 2,089 s: 1,318 passed, 19 skipped (the `macos` + `gui` M cases)**, 0 CUDA errors |
| harness | exit 0: Ran 423 tests, OK (skipped=1) |
| footprint | owned and granted paths only (above); 0 CR in every changed blob |
| the real `%LOCALAPPDATA%\Clearwater` | ABSENT after the gate |

**The CUDA fault (CHARC: a STOP if it recurred; it did not).** The error is sticky for the life of a process. A fresh process ran a CuPy kernel right after the leg. The System log held no nvlddmkm / Display / TDR event. Two reproductions on `e2db371c` with the gate's flags found P31 alone and 0 CUDA errors: portability + prototype_backend, then the exact serial order from photo_check through prototype_clip, including the 309 s real-photo GPU leg. p63a-s had run the same GPU tests green an hour earlier. The first log, `repro1.log` and `repro2.log` are kept in `wp6.4\gate\`. CHARC opens ONE watch row at this accept: a sticky per-process CUDA fault, not reproduced.

The fullclip leg was not run: the brief names no fullclip check. The Windows NVENC and x265 command lines are pinned byte-identical by the W-CODEC snapshot tests, which ran in this gate, and no correction code changed.

Summary, verbatim:

```
head e2db371c start 01:31:01Z free 73G
leg static start 01:31:02Z free 73G
ruff exit 0
format exit 0 330 files already formatted
mypy exit 0 Success: no issues found in 164 source files
leg collect start 01:31:22Z free 73G
collect-all exit 0 ids 9002 uniq 9002: 9002 tests collected in 11.29s
collect-parallel exit 0 ids 7658 uniq 7658: 7658/9002 tests collected (1344 deselected) in 2.88s
collect-serial exit 0 ids 1337 uniq 1337: 1337/9002 tests collected (7665 deselected) in 2.78s
collect-fullclip exit 0 ids 7 uniq 7: 7/9002 tests collected (8995 deselected) in 2.65s
identity: union 9002 dup 0 diff-vs-all 0
leg parallel start 01:31:51Z free 73G
parallel exit 0 612 s: 7452 passed, 206 skipped, 5 warnings in 610.37s (0:10:10)
leg serial start 01:42:04Z free 71G
serial exit 1 3182 s: Original exception was:
leg harness start 02:35:07Z free 71G
harness exit 0 Ran 423 tests in 27.182s OK (skipped=1) 
end 02:35:36Z free 71G
head f4ff6c88 start 02:50:00Z free 72G
leg serial start 02:50:02Z free 72G
serial exit 0 2089 s: 1318 passed, 19 skipped, 7665 deselected, 1 warning in 2084.16s (0:34:44)
end 03:24:50Z free 71G
```

## Dispositions (for CHARC at this accept; the brief's "Debt and decided items" plus the rulings)

- **DR-121, DR-122, DR-124: CLOSE.**
- **DR-34(a): note.** P73's no-replace rename; the APFS corpus runs at WP6.5.
- **AD-35, AD-36, AD-37: BUILT** (file:line in the report). **AD-25(a): built. AD-12: note** (the rate helper exposes `nvenc_rate`'s numeric R).
- **The gate fill** gains the W-STATIC darwin line (`uv run mypy --platform darwin`).
- **The WP6.1 fold-in POSIX-portability advisory (A r5 #4): CLOSE** (the test runs on macOS at WP6.5).
- **Register rows (the next free numbers):**
  1. The partial rows. P09 / P10 / P12 / P14 / P59 are VT by argument list only, on a SYNTHETIC listing; P01 / P25 / P26 injected; P03 / P74 stubbed; P22 a patched platform; P29; P73's POSIX branches stubbed; P71 synthetic events. Each is listed with its Windows-side proof and the WP6.5 native check that closes it.
  2. The banked M work (A r2 item 6), WP6.5's owned work: M-DEVICE's AD-11 comparison; M-SPAWN / M-BUNDLE's worker protocol, cancel and descendant clean-up; M-GUI's app-menu merge, native dialog and Retina mapping.
  3. B3: a bind mount of the footage tree is invisible to `realpath`. Pre-existing, out of the owner's envelope; one line in the report's limits.
  4. The A r4 test-instrument evasions (CHARC: a row of their own).
  5. P71, opened and closed: the pre-existing Windows wheel-zoom defect (a full step per sub-notch delta), fixed by the 120-unit accumulator.
  6. The order-dependent `test_prototype_clip` failure (also on main).
- **Incident note:** a W-GUI run by `wp64-cell3` with `QT_QPA_PLATFORM` unset showed windows briefly; no input was sent. This falls under the GUI clause of the Entry-point isolation rule. The module now forces offscreen, which is the fix.
- **User guide:** merged second, as ruled (above).
- **Watch row (CHARC):** the p64 sticky `CUDA_ERROR_UNKNOWN`, not reproduced (above).
- **Owed prunes, on the owner's word:**
  - the reviewers' probe folders under `.worktrees/wp6.4-rA/work/`;
  - after this accept, `.worktrees/wp6.4-rA` itself.

## Merge

The harness gate was run with this record in the worktree (the code unchanged since `e65ab384`): `uv run python -m unittest discover -s tests/harness` -> Ran 423 tests, OK (skipped=1). No registration is needed (`docs/proofs/` is an instance-surface prefix). The record is committed on `wp6.4` by pathspec, and `main` is fast-forwarded to `wp6.4` by the orchestrator. `.worktrees/wp6.4-rA` is released after the merge, except for any probe folder it cannot delete, which joins the owed prune. Main is ahead of `origin/main`; a push needs the owner's word.
