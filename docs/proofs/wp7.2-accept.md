# WP7.2 accept -- last-sample end on coarse-edit-list sources

**Accepted by:** the orchestrator, generation 63, 2026-11-09 ~22:25Z.

**Package:** WP7.2. Brief `docs/briefs/wp7.2-brief.md` (FINAL, CHARC gen 21, `61c1aae3`).

**Rulings:** CHARC `708c3a6b`: Q1 (a) build; (b) the movie-level reading held for the owner; (c) refused.

**Merged:** fast-forward of `wp7.2` onto main.
- Gated head `14f68e2a`; after the rebase onto main it is `06107b9c`.
- `git range-diff 83d7c9ed..14f68e2a main..wp7.2`: all five commits `=`.
- The tree diff against the gated head is empty apart from main's own state docs (`docs/charc-state.md`, `docs/orchestrator-state.md`).

## What changed

- `src/clearwater/io/video/verify.py`:
  - `frame_end`'s last-frame branch only. `_track_end` (`start_pts + duration_ts`) is returned when the track ends after `last_pts` and lies less than one tick from `presentation_end`; otherwise today's ceil applies.
  - A new private helper, `_track_end`.
  - `presentation_end` and `readable_end` unchanged, and every signature and caller unchanged (frozen interfaces held).
- `tests/test_io_video_verify_end.py`: new.
  - RED on the base: 5 failed. The base gave 12015 / 1853855 / 13167168 / 4005 / 4005 where 12014 / 1853854 / 13167167 / 4004 / 4004 is expected.
  - 8 pinned cases unchanged.
- `tests/test_io_video_encode_units.py:631-632`: re-pointed to the no-track-end case (ceil 4005 kept), per seat ruling (a).
- `docs/reports/wp7.2-last-sample-end.md`: round 0, the fix, RED / GREEN, and the movie-level rows held per Q1 (b).

## Nets

| Net | Where | Result |
|---|---|---|
| Reviewer A | Codex at the cell's seat | r1 (`83d7c9ed..74a1dbf2`): 1 NIT ("coarser" -> finer, wording), fixed `b772f63d`. r2 (delta): no findings. CONVERGED. Evidence `clearwater-review-evidence\wp7.2\A\r1`, `r2`. |
| Reviewer B | Codex at the orchestrator's seat, whole package | `NO_NEW_CRITICAL_MAJOR`, zero findings, 7 CHECKs PASS: the D86 cut-file case (the `later` branch returns first), the exact `< 1` boundary, the time-base guard, and GoPro / no-edit / exact-edit cases identical to base. Evidence `...\wp7.2\B\r1`. |

## Gate (seat, at `14f68e2a`; `work/orch-g63/gate-w72a/`, `gate-w72s/`)

| Leg | Result |
|---|---|
| static | ruff 0; format: 338 files clean; mypy: 166 files clean |
| collect | all 9933 = parallel 8589 + serial 1337 + fullclip 7; dup 0 |
| parallel | 8382 passed, 207 skipped (656 s) |
| serial | 1318 passed, 19 skipped (2003 s); includes the footage-marked V4 tests `tests/test_video_fidelity.py` and `tests/test_v51_video_acceptance.py` |
| harness | 423 OK (1 skipped) |

## Cell

- `wp72-cell1` (opus-high), retired.
- Depth: 106,020 at the round-0 STOP; 150,961 at the build return.

## Open after this accept (owner and seat)

- **The post-package V4 re-run.** Two re-exports of the 62 s Insta360 clip on the fixed main (the WP7.1 run-A and leg-D settings), about 25 min of exclusive GPU, in an owner quiet window that CHARC asks for. Then V4 runs with the WP7.1 frozen drivers under new ids.
  - Expected: the video stream duration SAME.
  - The three movie-level rows are judged per the owner's word on CHARC's Q1(b) reading.
  - The record goes to the WP7.1 accept.
- **The owner's word on the movie-level reading** (CHARC asks). No instrument change before it.
- **CHARC's accept note:** one line added to AD-22's record (`docs/decisions.md`): the last frame's end is the track's own last sample end; the edit-list end is a fallback only.
