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
| 3 (remediation, after Reviewer B round 1) | `6a5aec0` (delta `0233a8e..6a5aec0`) | WSL / 0.162.1 | 0 | 1 | 5 | 6 of 6 | 6 | 0 | 0 | product (pack.py) + tests + text | author cell `wp13-cell`: 412K at its return; remediation cell: dispatcher fills | probe: banner v0.162.1 / gpt-5.6-sol / high / read-only, footer present; review: banner OK; `^ERROR` 0; `ERROR codex_core` 0 (one match of the string ERROR is the brief's own assertion text, an echo); footer 1; `^ succeeded in` 21; VERDICT anchored; `docs/proofs` hits all classified: the prompt (echo), the report and brief text (echo of files the reviewer was allowed to read), and one reviewer command using `:(exclude)docs/proofs/**` as a pathspec exclusion; no access to a withheld path | NEW_CRITICAL_MAJOR_FOUND |

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


## Round 3 (remediation after Reviewer B round 1; the ONE bounded remediation, no further round)

Cell: remediation cell (Sonnet 5.5), same worktree and branch, from head `0233a8e`. Reviewer B (the orchestrator's seat
pass) found B1-B3 and B6 major, B4, B5, B7-B11 minor; B6-B10 are banked as out of envelope (DR-20) and are not in this
round's code. Closed here: B1, B2, B3, B4, B5, B11 (report section 8 and the return report). Evidence:
`C:\Users\rwsmy\clearwater-review-evidence\wp1.3\r3\` (prompt, diff, transcript, adjudication, md5sums.txt).

Round 3 reviewed `6a5aec0`: one major (REASONED), five minors, all in envelope, all adjudicated CONFIRMED
(`adjudication-r3.md`). The major was introduced by this remediation (the cleanup of `encode_verified_pair` stopped at the
first removal that raised) and is FIXED in `2b0e77a`; the five minors are fixed once in the same cleanup. The remediation
allows one Reviewer A round, so the fixes are not re-reviewed; this is stated plainly here and in the report.

| # | Finding (round 3) | Tag | Kind | Disposition |
|---|---|---|---|---|
| 1 | cleanup stops at the first failing removal and masks the original error | major, REASONED | product | fixed: `discard`, best effort with notes; new test (fails against the old loop) |
| 2 | direct `mkdir` of a fabricated footage in a refusal test; report wording | minor | test + text | fixed |
| 3 | quadrant interior not proved by a test | minor | test | fixed: planted pixel off the centre and in the margin |
| 4 | read-back scratch not cleared, `rmtree` errors silent | minor | product + test | fixed: cleared on entry, warning on failure, stale-frame test |
| 5 | "dropped frame fails by name" false (fails on the count) | minor | text | fixed |
| 6 | report cites g3 gates as green, `g3-ruff.log` holds one error | minor, EXECUTED | text | fixed: error fixed, gates re-run as `g4-*.log` |

Remediation commits: `01784a9` fix (read-back, naming), `7470ec8` test (guard, interior, read-back, naming), `6a5aec0`
docs (report), `2b0e77a` fix (round 3 cleanup), `d2ac044` docs (report text); this ledger follows.

## Verification loop (remediation cell)

| # | Suspected | Confirmed? | How | Disposition |
|---|---|---|---|---|
| 11 | a lossy encode's frames are too alike to tell apart on the real clip | rejected (false positive) | per-frame read-back of the 180 frames of both clips: smallest margin to a neighbour 6.41 levels (source clip) and 7.60 (unsmoothed), worst own difference 2.52 and 2.85 | none; recorded in `flicker\statistics.json` |
| 12 | converting and resizing in one `scale` step is accurate enough for the read-back | no | lossless test frames: 4.2 levels of error against 0.12 when the colour conversion is done first and the reduction second | fixed (two-stage chain, `reduced_clip_command`) |
| 13 | the 180 frames' statistics change on the re-run | rejected | parsed `frames`, `summary`, `bound_counts`, `excerpt` equal to the kept first-run copy; both MP4s byte-identical (md5) | none |
| 14 | the 3.0-level bound on the own difference is too tight for the real clip | partly | worst real value 2.85 | left at 3.0 (set before the run; the margin to the neighbours is the discriminator); disclosed |
