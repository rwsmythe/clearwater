# WP7.1 accept -- Insta360 Studio exports as Clearwater input

**Accepted by:** CHARC gen 21 (session `clearwater-charc-20261108-2037`), 2026-11-10 ~13:30Z.

**Package:** WP7.1. Brief `docs/briefs/wp7.1-brief.md` (FINAL 2026-11-09 by CHARC gen 20; scope corrected at round 0 to the three HEVC exports, CHARC ruling on gen 60's verified STOP). Lane: Codex (`implementer-codex-sol-high`), both reviewer nets Claude. Report `docs/reports/wp7.1-insta360-exports.md` (sections 1-8 the package report; section 9 the re-runs after WP7.2 and the owner's words).

**Merged:** fast-forward of `wp7.1` onto main, main = `5f684e58` (orchestrator gen 66, return_report `4ac88fbf`). Rebase onto main: 11 commits, `git range-diff` all `=` (`work/orch-g66/wp71-range-diff.txt`); the only tree change from main was AD-22 in `docs/decisions.md`. Not pushed.

## What the package established

- **Inventory of record:** `docs/reports/inventory-2026-11-09.md`: seven Insta360 files, 224,253,936,407 bytes; 135 rows (62 videos, 73 photos), zero error rows.
- **Probe and decode:** the three HEVC Main `.mp4` exports (two `yuvj420p` full range, one `yuv420p`) are admitted and decoded as tagged; the full-range reading is correct against the plain-FFmpeg ProRes reference (no double expansion); the three ProRes `.mov` exports are refused under spec 5.2 with the message recorded.
- **Throughput of record (window 2, quiet GPU):** leg D 10.35 min/min, leg E 11.04 min/min (62 s and 439 s exports) against N6 10.84 (N6 = 12, D106 12.0). No product performance debt. Window-1 figures are host-confounded (a game loaded the GPU) and of no record; window-3 figures are not exclusive and of no record.
- **V4 fidelity:** the historical finding (section 4) was one class: the output video track ended +1 tick (1/30000 s) on every export, because the edit list is written in a coarse movie timescale rounded up and `frame_end` ceiled the fractional edit end. Fixed by WP7.2 (`e438123c`, accepted 2026-11-09; AD-22 extended). On the 62 s re-exports (window 3, 2026-11-10) all three V4 records PASS: MANDATORY 0 / REQUIRED 0 / BEST-EFFORT 5 (the known classes: camera atoms, `ftyp` brands, container tags, stream tags, sample-entry children); the video stream duration SAME exactly; the four movie-level rows SAME under the owner's reading.
- **Long clip:** decode-only projection 2.49 h for the 37.7 min export; total export wall unestablished; no long export ran (owner's word only).
- **Look pack:** `work/wp7.1/look/index.html` (six pairs), exhibits kept at `clearwater-review-evidence\wp7.1\seat\look-exhibits\`.

## Owner's words (all 2026-11-10, verbatim; project log)

- "push; reading" -- the movie-level reading accepted (AD-22 record, `docs/decisions.md:31`).
- "Pass with notes 8999/150: relatively strong blueish halo around scuba diver on left side; 16499/75: slight blue halo around scuba diver legs in the bottom right." -- the look verdict: PASS WITH NOTES (DR-160).
- "No for ProRes / 4:2:2 input" -- spec 5.2 stands; no Phase 7 candidate.
- "quiet window" -- window 3.
- "add" -- the report's section 7 note went into spec 5.2 as the Insta360 source note, spec v0.6.3 (CHARC, same day).

## Instrument: the movie-level reading (`tools/video_fidelity.py`, branch `wp7.1-instrument` folded into `wp7.1`)

- Codex turns I1-I6 (`09838991` .. `65c28219`): one helper, V = (mdhd duration - media_time) / mdhd timescale; a row is SAME iff V_src == V_out and each side lies within one tick of its own mvhd timescale; `Fraction` only; applied to mvhd, video as written, effect, and the best-effort non-video row; a source without an edit list uses the identity value (AD-22 extended), only where the output has a list. D86 paths unchanged.
- Claude Reviewer A r1-r4 and Reviewer B: converged, zero findings at r4 (5,000-case per-key oracle; differential census 0 tightenings against `4ddf4841`, `ad36c021`, `8eac86d1`; B proved the pre-fix `bench-hevc62q` header still DIFFERENT and a post-fix counterfactual SAME).

## Nets on the package

| Net | Result |
|---|---|
| Reviewer A (Claude) on turns 1-15 | converged (turn 14 fold `5d917534`); on section 9 (`ae62caef`): `NO_NEW_CRITICAL_MAJOR`, 1 MINOR + 3 NITs folded `0d459d9a` |
| Reviewer B (Claude) | `NO_NEW_CRITICAL_MAJOR`, single remediation folded (turn 15) |

## Gate (seat, on `5f684e58`; `work/orch-g64/gate-w71g/summary.txt`)

| Leg | Result |
|---|---|
| static | ruff 0; format 339 files; mypy and mypy --platform darwin clean |
| collect | 9,993 = parallel 8,649 + serial 1,337 + fullclip 7; dup 0 |
| parallel | 8,442 passed / 207 skipped / 0 failed (582 s) |
| serial | 1,318 passed / 19 skipped / 0 failed (2,264 s; the footage-marked V4 tests) |
| harness | 423 OK (1 skipped) |

## Debt opened at this accept (`docs/debt-register.md`)

- DR-160: blue halo at a foreground diver's edge on SCUBA footage (owner's look note; watched; Phase 7 candidate).
- DR-161: the WP7.1 instrument record (seat supervision defects found and fixed in frozen-t7/t8; the supervisor cost finding 57.4 % -> 1.24 % of a core; V16 idle not subtracted on a host-confounded record; the leg-D cleanup near-miss).
- DR-162: exclusive windows and serial gate legs are gated on NO live cell (second occurrence: gen 61, gen 65); a hold message to a mid-turn cell only queues.

## Cell and seat

- Codex cell turns 1-17 (`scripts/codex_cell.py`), frozen drivers t6 -> t7 -> t8 (`v4_admission()` in `seat_common.py`); worktrees `wp7.1`, `wp7.1-instrument`, `wp7.1-iA`, `wp7.1-rA` kept until the owner's prune word; records and the look pack under `.worktrees/wp7.1/work/wp7.1/` (gitignored).
- Window records: `export-hevc62r2`, `bench-hevc62r`, `v4-bench-hevc62r`, `v4-hevc62r2` (2026-11-10 09:26-10:03Z); seat log and raw gate archive at `clearwater-review-evidence\wp7.1\seat\window3\`.

## Open after this accept

- WP6.5 continues (run 5 after the `.app` content-check fix; F0-2 next).
- CHARC's Phase 7 proposals from the register, with DR-160 among them.
