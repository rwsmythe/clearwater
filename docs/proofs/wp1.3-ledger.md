# WP1.3 -- Reviewer A cumulative round ledger

Cell: implementer (Sonnet 5.5), worktree `.worktrees/wp1.3`, branch `wp1.3`, base `a1c073c`.
Reviewer A: Codex CLI via WSL, codex-cli 0.162.1, per call `-m gpt-5.6-sol -c model_reasoning_effort=high
-s read-only --skip-git-repo-check`, tier STRONG (brief). Probe before round 1: banner v0.162.1 / gpt-5.6-sol /
high / read-only, one `^ succeeded in`, `^tokens used` present. Evidence (outside every repo tree):
`C:\Users\rwsmy\clearwater-review-evidence\wp1.3\r1\` and `\r2\` (prompt, diff, full transcript, final message,
per-finding adjudication, md5sums.txt) and the probe transcript in `r1\probe-transcript.txt`. Staging files
(`wp13-*`) were kept in the session scratchpad, never in the worktree.

| Round | Head reviewed | Transport / CLI | Critical | Major | Minor | In envelope | NEW | REOPENED | Reverts | Fix kind | Context depth (dispatcher) | Mechanical assertions | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `72bdf9e` | WSL / 0.162.1 | 0 | 1 | 5 | 6 of 6 | 6 | 0 | 0 | product (frames.py, pack.py) + tests + text | dispatcher fills | banner OK; `^ERROR` 0; `ERROR codex_core` 2 (1 prompt echo, 1 the reviewer's own `mktemp /tmp` rejected by the read-only sandbox); footer 1; `^ succeeded in` 23; VERDICT anchored; no withheld access | NEW_CRITICAL_MAJOR_FOUND |
| 2 | `9addcd0` | WSL / 0.162.1 | 0 | 0 | 3 | 3 of 3 | 3 | 0 | 0 | product (pack.py) + tests | dispatcher fills | banner OK; `^ERROR` 0; `ERROR codex_core` 1 (echo of the brief); footer 1; `^ succeeded in` 30; VERDICT anchored; no withheld access | NO_NEW_CRITICAL_MAJOR |

Round 1 major: the open-blue-water case marked PENDING while the `GX011628` stills are water-dominant. REJECTED by the
brief ("Pending cases are named, not approximated"; claim 6 pre-fills the three spec section 12 cases PENDING),
MITIGATED by text (the PENDING entry and report section 7 say what those frames are and give their numbers) and raised
to the orchestrator as an open question; round 2 did not re-raise it. Round 1's minors included a defect worse than the
reviewer described: the corrected-frame MP4 had lost the source's primaries and transfer tags (they had reached the
source clip only through FFmpeg's PNG colour chunks); fixed with `setparams`, asserted end to end.

Convergence: round 2 had zero NEW blocking findings; its three minors were fixed once in the cleanup (`f697f63`) and
opened no round. FIVE_ROUND_GATE not reached (2 rounds). Commits: `5833dff` feat, `652b1fd` fix, `72bdf9e` docs,
`4c37dc3` fix (round 1), `c51b020` fix (round 1), `9addcd0` docs, `f697f63` fix (round 2 cleanup); this ledger and the
report's section 8 follow.

## Verification loop (cell's own; suspect -> confirm independently -> fix -> repeat)

| # | Suspected | Confirmed? | How | Disposition |
|---|---|---|---|---|
| 1 | FFmpeg's default scaler decodes limited-range YUV dark | yes | known-colour clip: error 3.0 levels without `accurate_rnd`, 0.70 with | fixed (`flags=accurate_rnd`) |
| 2 | the "full range" control clip was not full range (FFmpeg converted before the encoder) | yes | error 27 levels on the full clip | fixed (frames flagged with the range they are tagged with) |
| 3 | `in_range` is inert for `yuvj` pixel formats | yes | mutation: ignoring the range tag left the full-range test green | documented in the module docstring and report; pixel-format/tag contradiction refused; tag-driven control added for non-`yuvj` |
| 4 | `ffprobe -read_intervals` returns frames from the keyframe before the start | yes | listing vs full probe | fixed (filtered by exact tick) |
| 5 | `showinfo` sits before `-frames:v` and reports more frames than written | yes | `-frames:v 3` printed 4 | fixed (first N compared) |
| 6 | concat demuxer + `setpts` gives non-monotonic pts (0, 1, 1001, 2002, 4004 ...) | yes | ffprobe of the encode | fixed (numbered image sequence, `naming="index"`) |
| 7 | `avg_frame_rate` 0/0 raises a bare ZeroDivisionError | yes | unit test | fixed |
| 8 | a seek one frame late would mislabel frames | guarded | mutation: both pts tests fail by name | none needed |
| 9 | the gray quadrant read 126 vs 128 means swscale RGB->YUV is wrong | rejected (false positive) | the lavfi `color` source's own conversion; stored YUV matched the independent calculation exactly | none |
| 10 | unsmoothed MP4 lacks the source's primaries and transfer | yes (found by round 1's finding 3 and a stricter `verify_clip`) | ffprobe of the clips | fixed (`setparams`) |
