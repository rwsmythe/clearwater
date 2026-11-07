# WP6.3e accept record (orchestrator generation 58, 2026-11-07)

**Package:** WP6.3e "Release workflow fresh-tree fix" (brief `docs/briefs/wp6.3e-brief.md` FINAL `ea4d6a36`, CHARC gen 19 on the release-run failure STOP: gen 57 query `31986d18`, ruling `1f1c6436`).

**Why:** release run `42387791040` on the pushed tag `v1.1.0` (head `356f2e4d`) failed 3 s into "Run parallel tests": `release.yml` passed `--basetemp=work/ci-parallel`, `work/` is gitignored, and pytest does not create the basetemp's parent. No draft was created; `v1.1.0` stays on origin with no release and is never moved (the record is under `clearwater-review-evidence\release-1.1.0\workflow\run-42387791040\`). The fix ships as 1.1.1 with identical product code.

**It delivers:**
- **`.github/workflows/release.yml`:** `New-Item -ItemType Directory -Force -Path work | Out-Null` inside "Run parallel tests" before the pytest line; `-rs` on that pytest line; `-Force` on the staging `New-Item work/release-assets`. No `uses:` line, uv pin / checksum, version or tag gate, permission, trigger or draft-only publication changed. `actionlint` 1.7.12 clean (seat, `wp6.3e\seat\actionlint-9d4d0258.txt`).
- **`tests/test_release_workflow.py`:** pins for the parent mkdir (the parent derived from the `--basetemp=` value), the staging `-Force` and the `-rs` argv. RED against `d14a09c1`'s workflow (`3 failed`), GREEN on HEAD (`59 passed`, real git), executed by Reviewer B.
- **The toml fold** (`tests/test_lookcheck_deep.py`, turn 2; CHARC `a0df6f36`): `_footage_root(tmp_path)` returns the configured footage path when a valid `clearwater.local.toml` exists, else an empty `footage-stand-in` under the test's temp root. No marker change.
- **The runner-PATH guard fold** (turns 3-5; CHARC `3b0e47f3` + grant `875e398a`, `616c87d6`): the runner image `windows-2025-vs2026` has NO FFmpeg / ffprobe (Reviewer A r1 F-1, confirmed from `actions/runner-images`). 157 parallel-leg nodes in 15 modules now SKIP with `SKIP_NO_FFMPEG` (the existing `ffmpeg_tools` fixture or the module's existing skip style) when the tools are absent; 96 guard sites, test-only, no assertion, logic, parameter-set or selection-marker change.
- `docs/release-checklist.md` step 9 (a workflow-only failure after a tag is pushed = a new patch version on a fixed commit; the failed tag stays on origin with no release and is named in the next notes; `docs/release-notes-<version>.md`); `docs/reports/wp6.3e-release-workflow-fresh-tree.md`.

**Candidate:** branch `wp6.3e` off main `d14a09c1`: `e9cde49d` (t1), `c66af644` (t2), `8a30d6d4` (t3), `d6db4a0f` (t4), `f3de8b0c` (t5), `9d4d0258` (seat: the report's rehearsal and spy fact lines, CHARC ruling on `b7cd30a3`), `48b08d91` (seat: B's F-1 / F-2 / F-6 report text after the gate, CHARC ruling on `0017b712`).

**Footprint** (`git diff --name-only d14a09c1..48b08d91`, 19 paths, all owned): `.github/workflows/release.yml`, `docs/release-checklist.md`, `docs/reports/wp6.3e-release-workflow-fresh-tree.md`, and 16 test modules (`test_app_composition`, `test_color_swscale`, `test_fixtures`, `test_headless_export`, `test_io_video_encode_units`, `test_io_video_probe`, `test_io_video_spawn`, `test_lookcheck_deep`, `test_photo_verify`, `test_release_workflow`, `test_reviewpack`, `test_wp321_bench`, `test_wp321_device_frames`, `test_wp321_fft_release`, `test_wp42_composition`, `test_wp44_mov_input`). Nothing under `src/clearwater/` or `tools/`; 0 CR in the diff.

**Lane: Codex `implementer-codex-sol-high`** (brief). Depth at yield (`depth_input_tokens`): t1 FRESH `01a1b6b8` 150,480; t2 RESUMED 176,751; t3 FRESH `01a1b71b` 156,835; t4 RESUMED 183,639; t5 FRESH `01a1b750` 95,620. No STOP.

**Reviewers: the other model (Claude) in both nets**, read-only `claude -p` at the seat through `codex_cell.py review` on the detached copy `.worktrees/wp6.3e-rA` (NO toml, on purpose); every prompt banned `run_in_background`; every `review.txt` a full report.

**Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp6.3e\`: `cell\` (dispatches, prompts, returns, transcripts, driver stdout 1-5); `A\r1`-`A\r3`; `B\r1`; `seat\rehearsal\` (every rehearsal and the causal split), `seat\spy\` (the spy runs), `seat\actionlint-9d4d0258.txt`; `gate\` (copied from `work/orch-g58/gate-p63e*` at this accept).

## Nets

| Net | Head | Verdict | Disposition |
| --- | --- | --- | --- |
| A r1 (full `d14a09c1..c66af644`) | `c66af644` | NEW_CRITICAL_MAJOR: F-1 MAJOR (the runner has no FFmpeg; the rehearsal inherited the laptop PATH) + F-2..F-4 | F-1 -> the runner-PATH rehearsal, causal split and the guard fold (t3); F-2 / F-4 corrected in t3; F-3 no change (CHARC) |
| A r2 (delta, t3) | `8a30d6d4` | NO_NEW_CRITICAL_MAJOR; F-1 CLOSED by execution; R2-1 / R2-2 MINOR (passes for the wrong reason), R2-3 adv | R2-1 / R2-2 folded in t4; R2-3 no action |
| A r3 (FINAL, delta t4) | `d6db4a0f` | **NO_NEW_CRITICAL_MAJOR**, no findings | A CONVERGED |
| Seat spy (CHARC `616c87d6` item 2) | `d6db4a0f` | 17 passing nodes spawned: 15 (a), 2 (b) in `test_reviewpack.py` (R2-2's class) | (b) guarded in t5 (fresh session); the spy repeated on `f3de8b0c`: ZERO (b) |
| B r1 (full `d14a09c1..9d4d0258`, turn 5 explicitly) | `9d4d0258` | **NO_NEW_CRITICAL_MAJOR**; F-1 / F-2 MINOR (report text), F-3..F-6 adv; nothing inside turn 5's diff | F-1 / F-2 / F-6 folded by the seat (`48b08d91`); F-3 -> DR-157; F-4 no action (hosted runners are fresh VMs); F-5 -> the limits below |

## The CI-shaped rehearsals (seat)

The driver `work/orch-g58/rehearsal.py` (from gen 57's) runs the workflow's own `run:` blocks extracted from the clone's `release.yml` on a fresh `git clone` (no `work/`, no toml, no footage), under redirected APPDATA / LOCALAPPDATA / XDG; `--runner-path` drops every PATH entry holding `ffmpeg.exe` / `ffprobe.exe` and sets `CUDA_VISIBLE_DEVICES=-1`.
- `e9cde49`: the predicted 12 toml failures (all `test_lookcheck_deep.py`); build + staging PASS.
- `c66af64` (laptop PATH): PASS, `8367 passed, 210 skipped`. `c66af64-runnerpath`: `149 failed + 3 errors`, all FFmpeg-absent; causal split (`c66af64-causesplit\`): FFmpeg dropped -> the same 152 fail; GPU hidden -> 152 pass.
- `8a30d6d-runnerpath` (pre-fold, t3): PASS, parallel `7522 passed, 1055 skipped`.
- **The rehearsal of record, `f3de8b0-runnerpath` (t5; the later seat commits change only the report), a NEW fresh clone, runner PATH for every step: PASS.** Sync exit 0 (1,040.7 s); Run parallel tests exit 0, `7517 passed, 1060 skipped, 5 warnings in 241.29s`; build under the UIA watch exit 0 (239.7 s, no window, 13 Clearwater pids sampled); staging exit 0 (zip, `.sha256`, `THIRD_PARTY_NOTICES.md`).

**The spy** (seat tooling `work/orch-g58/spy/ffspy.py`, NOT committed; installed by copy into the rehearsal clone's venv and removed after, PYTHONPATH unset): `d6db4a0-r2` `7519 passed, 1058 skipped`, 17 spawning passes (15 (a), 2 (b)); `f3de8b0-r1` `7517 passed, 1060 skipped`, the same 15 (a), ZERO (b). Run `d6db4a0` is INVALID (it set PYTHONPATH, which `build.py` refuses: 253 instrument failures).

## Gate p63e (seat, `work/orch-g58/gate-p63e/`, on `9d4d0258`; toml present)

- static: ruff 0; format 0 (`337 files already formatted`); mypy 0 (`Success: no issues found in 166 source files`); `mypy --platform darwin` `Success`, 166 files.
- collect: all 9,921 = parallel 8,577 + serial 1,337 + fullclip 7; duplicates 0; diff against all 0.
- **parallel: exit 0, `8370 passed, 207 skipped` in 618 s** (the laptop floor; the toml-less clone's 8,367 / 210 differs by exactly the three toml-absent skips `test_app_leftovers.py:458`, `test_lookcheck.py:937`, `test_photo_memory.py:32`).
- **serial: exit 1, `1 failed, 1317 passed, 19 skipped` in 2,287 s.** The one failure: `tests/test_app_v8_v18.py::test_v8_video_pre_encode_through_the_harness_on_the_shells_frame` (`:336`, `pts_ticks` 0 vs 10,010: the shell's frame lagged the position, a GUI timing race), outside the package (no change to that module or to any product code). Re-run alone three times in the gate's environment: `1 passed` each (3.52-3.55 s). It passed in the 1.1.0 release gate. CHARC ruled ACCEPT WITH A WATCH ROW, no serial re-run (**DR-158**, DR-140's form): the node waits on `session.position()` (`:328`) and a fixed render wait, never on the shown frame's `pts_ticks`, so a late frame fails it. A second failure of this node in ANY gate is a STOP (bisect first; then a defect row or the test fix: wait on `current_image().pts_ticks == ticks[10]` before `:336`). The 1.1.1 step-6 gate re-runs the whole serial leg before the tag (`gate-p63e/v8-rerun.txt`).
- harness: `Ran 423 / OK (skipped=1)`.
- **On `48b08d91`** (the delta is one `.md`): collect identical; harness `Ran 423 / OK (skipped=1)`.

## Limits

- The rehearsal ran the step blocks under Windows PowerShell 5.1; the runner runs pwsh 7.
- `CUDA_VISIBLE_DEVICES=-1` stands in for "no NVIDIA driver at all"; CuPy with no `nvcuda.dll` may fail differently (B F-5; three `nvidia-smi` bench tests pass with the tool hidden). The real `v1.1.1` run is the proof of the driverless path.
- The spy sees spawns in the pytest processes only, and not a `which` lookup that raises before any spawn; Reviewer B closed both by execution (0 passing `which` misses; no child-process candidate in the parallel leg).
- Builds are not byte-reproducible across trees (zip digests differ for the same commit; notices byte-identical); release asset checks compare member sets.

## Dispositions (CHARC gen 20)

- **WP6.3e ACCEPTED on `48b08d91`** (CHARC gen 20 return_report, 2026-11-07T20:44Z): A converged at r3 (no findings); the seat spy's two (b) guarded in turn 5 and the spy repeated with ZERO (b); B r1 NO_NEW_CRITICAL_MAJOR with nothing inside turn 5's diff, so no A delta was owed; the rehearsal of record PASS; `actionlint` clean; gate p63e green apart from the DR-158 transient.
- **CHARC's accept writes on main `3dc61671`:** AD-38 item (17) (the fresh-tree rule: every path the workflow writes under `work/` is created by the workflow first; the CI-shaped rehearsal before every tag, in the runner-PATH shape; the guards; the spy; the limits; the gate figures); DR-154 (RECORD, closed: the 1.1.0 workflow failure, cause and lesson); DR-155 (the workflow's test leg runs without FFmpeg, so the FFmpeg-dependent tests skip on the runner and run only at the laptop gate; putting the locked FFmpeg on PATH before the tests is an OPEN Phase 7 candidate); DR-156 (RECORD: the release zip is not byte-reproducible across trees; compare member sets); DR-157 (B F-3: `find_tool`-gated units that skip without ffprobe although their logic needs no tool; stubbing `find_tool` is a logic change, not for a patch release); DR-158 (WATCH: the serial transient above); the `CLAUDE.md` state bullet.
- **Seat note** (CHARC: a harness item for WP-H, not a package item): the package worktree's own `.venv` was an empty shell from worktree creation (the cell ran from the shared environment). The seat's first darwin mypy there showed 81 import errors; `uv sync --frozen` filled it in 6 s from the warm cache, and the gate ran on the synced venv.
- **Owed prunes (the owner's word only; nothing removed while a gate runs):** `.worktrees/wp6.3e` (its `work/` holds the cell's and the gate's basetemps); `.worktrees/wp6.3e-rA` (the review copy; DR-148: check for live processes under it first); `work/ci-rehearsal/` (the rehearsal clones `e9cde49`, `c66af64`, `8a30d6d`, `f3de8b0` with their venvs and builds).
- **Next:** the 1.1.1 bump on a branch from the ff head (the five version places + the installer User-Agent pin `Clearwater/1.1.1` and its test; the notes on main `848701ce`); ONE read-only Codex pass over the bump diff + the whole `docs/release-notes-1.1.1.md` (a finding = STOP to CHARC); on a clean read ff + FREEZE, the release build + proofs, the CI-shaped rehearsal on the bump head, the FULL step-6 gate, the annotated tag `v1.1.1`, the tag report. No push; `v1.1.0` is never moved.

## Merge

- `d96f8d95`: main `3dc61671` (CHARC's accept writes: `CLAUDE.md`, `docs/charc-state.md`, `docs/debt-register.md`, `docs/decisions.md`; docs only) merged into `wp6.3e`.
- On the merged head with this record: the harness re-run at the seat (figure in the ff post to CHARC); main fast-forwarded to it (`git merge --ff-only wp6.3e`); every changed blob 0 CR.
