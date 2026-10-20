# WP1.3D ledger (implementer cell, worktree `.worktrees/wp1.3d`, branch `wp1.3d`, base `c80725b`)

Cell: implementer-sonnet-high. Spec v0.5.3. Brief `docs/briefs/wp1.3d-brief.md`.
Output root: `C:\Users\rwsmy\clearwater\work\wp1.3d\` (the MAIN tree's work folder).

## Progress (update at every commit)

Re-seated cell (second) took over at head `663cc64`, 2026-10-20 00:08Z.

| Step | State |
|---|---|
| scan.py (measures, picker, deep-frames.json, per-chapter cache and resume) + tests 1-4, 7 | committed `644c8fe` |
| scan run over the eight SCUBA chapters | DONE: 289 frames, 0 excluded; `scan.json`, `deep-frames.json` in the output root |
| pack.py `deep` command (stills, page, clip) + test 5 + clip tests | committed `3824bd8`, `145135c`, `0cd25e6` |
| tests for orchestrator ruling 3 (render equals correct) and flicker bound 3.0 | committed `07cebd9` |
| cap-tolerance fix (see Facts, DEVIATION 4) + test | committed `69d6c1f` |
| deep stills + page (`pack.py deep --part stills`) | DONE 776 s: 60 frames x 3 variants, `index.html`, `statistics.json` |
| deep clip (GX011600, 179 frames, c3 + ancuti2018) | third run DONE and checked (1336 s); a FOURTH run (`deep --part clip`, log `work/wp1.3d/deep-clip-run4.log`) was started after commit `82343ad` because the clip statistics now carry PNG hashes and the MP4 hashes (review round 2); CHECK it finished (`clip/statistics.json` has `checks` with four ok records and `clips`) |
| report `docs/reports/wp1.3d-deep-look-check.md` | committed; REGENERATE with `python work/wp1.3d/cell-scripts/report_gen.py` after the clip and scan finish (it reads the records, `gate-record.md` and `round-record.md` beside it); update those two files first |
| review rounds (Reviewer A, STRONG, gpt-5.6-sol, per brief) | rounds 1 and 2 done, both NEW_CRITICAL_MAJOR_FOUND; fixes committed through `82343ad` and `deep page writes a pts with the whole time base`; round 3 not started |
| full gate | last full pytest 730 passed on `8120b28`-era code; MUST be re-run on the final head (foreground, once, `--basetemp`) |

## NEXT STEPS (written at the round 2 yield; re-seat from here)

1. A scan re-run (`uv run python tools/lookcheck/scan.py`, log `work/wp1.3d/scan-run5.log`, CPU only, ~45 min) and the clip
   re-render (`deep --part clip`, log `deep-clip-run4.log`, GPU, ~25 min) were started in parallel after `82343ad`. Wait for both
   (poll the logs in bounded `sleep 5` loops: the scan ends with the path of `deep-frames.json`, the clip with `elapsed N s`).
   Compare the new `scan.json` frames with `work/wp1.3d/scan-before-cache-identity/scan.json` (must be identical value for value;
   `deep-frames.json` identical apart from `written`). If the clip's `statistics.json` has `checks` null or not ok, run
   `deep --part encode` or STOP and report.
2. Rebuild the page once with `deep --part stills` (13 min GPU): it exercises `clip_files` on the real clip. Not before step 1.
3. Full gate: ruff, ruff format --check, mypy, then pytest in the foreground (about 8 min); update `work/wp1.3d/cell-scripts/gate-record.md`.
4. Round 3: `python work/wp1.3d/cell-scripts/wp13d_build_prompt.py 3` and the diff (`git diff -U8 c80725b..HEAD -- . ':!uv.lock' ':!docs/proofs' > <SP>/wp13d-diff-r3.txt`), then `MSYS_NO_PATHCONV=1 wsl.exe bash -c "bash <SP>/wp13d_run_review.sh 3"` in the background. The two scripts in `cell-scripts` have the previous session's scratchpad path in a variable `SP` (edit it, or copy them to your own scratchpad). Transcript goes to `$SP/wp13d-review-r3.err` (banner and tool calls) and `.txt` (final message); `cat` them into `-all.txt` and run the five assertions; copy to `C:\Users\rwsmy\clearwater-review-evidence\wp1.3d\r3\` with md5s. Do not tell the reviewer what earlier rounds found.
5. Adjudicate. The loop's findings so far hardened the integrity of working-folder records against stale or replaced files; judge each new one envelope-relative (the envelope is a single operator running the steps in order, not tampering) and say so in the ledger. Converge on zero NEW in-envelope blocking findings; at round 5 yield for approval.
6. Regenerate the report (round-record.md gets each round), commit the report and ledger, then send the return report (under about 70 lines, brief section 'Notes for the cell') with SendMessage to `team-lead` AND as the final message.
7. Cleanup at the end: delete nothing under `work/wp1.3d/` except what the brief allows; the helper files in the scratchpad may go.

## Orchestrator ruling on the envelope line (received at the third seat, 2026-10-20 02:06Z)

- The envelope is ONE operator running the documented steps in order, on an untampered working folder. Findings needing a hand-edited,
  self-consistent record, a deliberately replaced file, or steps run out of order are OUT OF ENVELOPE: banked, disclosed in the
  report's limits, never loop-driving. The two remaining gaps of round 2 (hand-edited self-consistent cache record; duration/proxy
  text not re-derived at encode) are out of envelope by this rule.
- IN envelope and blocking: anything showing the owner the wrong thing at CP2 (wrong frame or pts, wrong variant label or
  parameters, wrong colour range, a candidate presented as fact, statistics not from the frame shown, a clip that is not the
  excerpt's frames in order, any write outside `work/wp1.3d/` or into the footage folder).
- No further integrity machinery for out-of-envelope findings. A round whose majors are all out of envelope converges.
- Round 5: yield for approval.

## How to resume

1. `cd` is forbidden; use `git -C C:\Users\rwsmy\clearwater\.worktrees\wp1.3d`. PATH needs
   `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` for ffmpeg. pytest `--basetemp` under
   `C:/Users/rwsmy/clearwater/work/pytest-wp1.3d`.
2. Commands: `uv run python tools/lookcheck/scan.py [--chapters ...]` (cached per chapter, resumable),
   `uv run python tools/lookcheck/pack.py deep --part render|encode|clip|stills|all`.
   `render` writes the PNG sets and `clip/statistics.json` (checks null); `encode` encodes, verifies,
   updates the statistics and prunes PNGs to first/middle/last of each set.
3. Any command over 10 min is moved to the background by the tool: run with nohup to a log file under
   `work/wp1.3d/` and wait with a bounded `for ... grep ... sleep 5` loop (no `pgrep` on this shell;
   `sleep N` alone is blocked).

## Facts learned (all measured)

- GX011589 is a 6.4 s chapter (one scan frame, at 5 s); the others run 42 s to 1047 s (GX011600).
- Scan cost 3.6-6 s per frame (probe + 4K HEVC seek/decode); the whole scan took about 55 min of wall time.
- Scan result: 289 frames, none excluded; W histogram (tenths from 0.0): 145, 39, 34, 24, 19, 8, 7, 8, 3, 2.
- Deepest frame: GX011600 at 665.031 s, D = 0.209 (centre of the clip). 4 candidates per case found
  without lowering any bar (see `deep-frames.json`).
- DEVIATION 1: the first clip render (179 frames) FAILED the read-back at the shallow clip's own-PNG
  bound of 3.0 levels: measured on the corrected c3 frames own = 1.00 min / 1.92 mean / 3.85 max
  (28 of 179 frames over 3.0), source frames 0.60 / 1.42 / 3.03 (2 over 3.0); the margin to the
  neighbour frames stayed at least 1.6 (c3 2.15, source 1.63) and the channel bias within +-0.9
  (limit 2.0). Cause: noisy deep footage, lossy NVENC CQ 20. Remedy: `max_own` became a parameter of
  `readback_clip` / `encode_verified_pair` (default 3.0, so `flicker` is unchanged), the deep clip uses
  `DEEP_READBACK_MAX_OWN = 5.0`; the neighbour test and the bias bound are unchanged. Also split the
  clip into `render_deep_clip` / `encode_deep_clip` so the statistics survive a failed encode.
  The probe numbers are from a scratch script (`readback_probe.py` in the session scratchpad) run on
  the kept PNGs of that failed render; the render is now being redone, and the final read-back
  records in `clip/statistics.json` supersede them.
- DEVIATION 2: `run_deep_clip` / `render_deep_clip` call `prototype.pipeline.correct(..., statistics=)`
  directly instead of `temporal.render` (the same call; `render` returns only the image and the Result
  is needed for the bound record).
- The candidate spacing (30 s, 10 s for the deepest list) is measured on the scan GRID (`grid_s`)
  within one chapter, not on pts (jitter of one frame period would make "30 s" ambiguous); candidates
  of different chapters are different recordings and are not compared. Report this.
- GPU timing noise: first full-resolution `correct` in a fresh process took 242 s once (other agents'
  jobs on the host); a 1080p synthetic clip test ran 12 min once and 19-70 s otherwise. Not product.
- Working tree files are CRLF on disk (autocrlf), LF in the index. Heredocs with apostrophes break the
  Bash tool here: write scripts with the Write tool to the scratchpad and run them.

- DEVIATION 3 (orchestrator ruling 3, test): `test_correct_with_supplied_statistics_equals_temporal_render_bit_for_bit`
  (c3 and ancuti2018, synthetic, CPU) and `test_the_flicker_path_keeps_the_shallow_readback_bound_of_three_levels`.
- DEVIATION 4 (found by this cell on the second clip render): `statistics_record` flagged a gain cap bound when
  `effective < requested`; the Gaussian-smoothed alpha of a constant 1.0 is 0.9999999999999999, so every one of
  the 179 ancuti2018 clip frames read "red cap bound" (including frames with alpha 1.0). Fix: `cap_tolerance`
  parameter (default 0.0, so the shallow pack and `flicker` are unchanged), the deep clip passes
  `DEEP_CAP_TOLERANCE = 1e-9`; test `test_a_smoothed_alpha_one_ulp_below_one_...`. The clip was re-rendered (third
  run): ancuti2018 red cap bound on 104 of 179 frames, c3 on none. The first-run statistics are kept as
  `work/wp1.3d/clip-statistics-run2-before-cap-fix.json`. The deep stills compute alpha directly (exact 1.0 when
  uncapped), so they were not affected and were not re-run.
- Orchestrator rulings 1 and 2 are stated in the report (section 2 for the spacing, section 6 for the read-back bound
  with measured own min/mean/max and smallest neighbour margin).

## Round ledger

Transport WSL, codex-cli 0.162.1, banner `gpt-5.6-sol` / `high` / `read-only` every round. Evidence
`C:\Users\rwsmy\clearwater-review-evidence\wp1.3d\rN\` (prompt, diff, transcript, scripts, md5s). Depth column: filled by the dispatcher.

| Round | Head reviewed | Findings (crit/major/minor) | In / out of envelope | NEW / REOPENED | Reverts | Fix kind | Assertions | Depth | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `3ca1cf5` | 0 / 2 / 3 | 2 major + 1 minor in; 2 minor out | 5 NEW / 0 | 0 | product code (scan.py, pack.py) + tests | banner ok; `^ERROR` 0; `ERROR codex_core` 2, both echoes of the brief text in the reviewer's file reads; footer; verdict anchored; 24 `^ succeeded in`; 13 `docs/proofs`/ledger hits, all echoes (the brief and prompt quote the words; no command opened them) | | NEW_CRITICAL_MAJOR_FOUND |
| 2 | `8120b28` | 0 / 3 / 2 | 3 major in (hardening of the same two controls); 2 minor out | 3 NEW (CR2-01..03 deepen the round-1 controls: REOPENED in spirit, new in detail) / 0 strictly | 0 | product code (scan.py, pack.py) + tests | banner ok; `^ERROR` 0; `ERROR codex_core` 1, an echo of the brief text; footer; verdict anchored; 26 `^ succeeded in`; proofs/ledger hits are echoes | | NEW_CRITICAL_MAJOR_FOUND |
| 3 | `3a38965` | 0 / 3 / 4 | R3-01, R3-02 major + R3-03..05 minor in; R3-06, R3-07 major OUT (ruling) | 7 NEW / 0 | 0 | product code (pack.py) + test; report wording | banner ok; `^ERROR` 0; no `ERROR codex_core` line (one echo of the prompt text); footer; verdict anchored; 30 `^ succeeded in`; proofs hits are the prompt/brief echoes and a `git status` name listing (no file under docs/proofs opened) | | NEW_CRITICAL_MAJOR_FOUND |

Round 1 adjudication (fixed in `81187ee`, `018f3a8`, `2883592`):
- F1 major (scan cache had no identity; `finish` could certify a stale or incomplete scan; `--rescan` kept a partial): ACCEPTED. A cache and a partial carry `rules` and
  the declared `timestamps`; `cache_problem` refuses a stale, foreign, subset or incomplete one, `finish` raises, `--rescan` deletes both files. The scan was re-run in
  full (the old caches were refused as unrecorded): 289 records identical value for value, `deep-frames.json` identical apart from `written`.
- F2 major (encode and page trusted whatever PNGs and MP4s were on disk): ACCEPTED. `render_deep_clip` clears the clip folder first (`clear_clip`);
  `encode_deep_clip` runs `clip_inputs_problem` before any tool; `clip_files` links only a clip whose statistics record ok checks and which is centred on the
  current deepest frame.
- F3 minor (usage docstring): fixed. F4 minor OUT-OF-ENVELOPE (zero-green frame excluded; D undefined): kept, a test pins it, stated in report section 2.
  F5 minor OUT-OF-ENVELOPE (footage and gpu tests skip when their inputs are absent): the repository's convention; the gate records none skipped.

Round 2 adjudication (fixed in `82343ad` and the commit after it):
- CR2-01 major (cache lacks source and record identity): ACCEPTED in part, fixed. The cache records the footage file's name and size, `main` compares the size with the
  file on disk, and every cached record is re-checked (`record_problem`: chapter, name from pts, pts not before the grid point, measures in range, exclusion equal to
  `exclusion_reason`). NOT done, stated as a limit: a hand-edited record whose values are in range and self-consistent cannot be told from a measured one
  (deliberate editing of the working folder; outside the envelope). Cost: every cache was refused as unrecorded and the scan was run a third time.
- CR2-02 major (`deep-frames.json` not tied to `scan.json`): ACCEPTED, fixed. `_load_deep_frames` rebuilds the file from `scan.json` with
  `deep_frames_document` and refuses any difference other than `written`.
- CR2-03 major (clip frames, statistics and MP4s not bound): ACCEPTED in part, fixed. SHA-256 of every source and corrected PNG is recorded at render and re-checked
  before the encode; the source video's size and the STAGED analysis are checked; `clip_files` requires all four check records (`c3`, `ancuti2018`, `source`,
  `readback`) to be present and ok, and the three MP4s to equal the SHA-256 recorded when they were verified. Cost: the clip was rendered a fourth time.
  NOT done, stated as a limit: the 6 s duration, proxy text and start are not re-derived from the source at encode time.
- CR2-04 minor OUT-OF-ENVELOPE (a scan grid point in the last second is omitted): the 1 s end margin is `SCAN_END_MARGIN_S`, stated in the report; none of the eight
  chapters has such a point. Banked.
- CR2-05 minor OUT-OF-ENVELOPE (page prints a pts without the time-base numerator): fixed anyway (`tick_text`), the text for 1/30000 is unchanged.

Round 3 adjudication (fixed in `37ff131` and the report text; evidence `r3/`):
- R3-01 major in envelope (report: "a dim open-water frame", "noisy deep footage": a candidate described as fact and a look judgement): ACCEPTED, text fixed
  (report generator, and the DEEP_READBACK_MAX_OWN docstring in pack.py).
- R3-02 major in envelope (the clip's `rendered.normalisation` was recomputed on the full-resolution white-balanced frame, not the smoothed proxy bounds the
  render applied; c3 spread 0.2124-0.4088 applied against 0.2063-0.4783 reported): ACCEPTED, fixed: `statistics_record(..., applied_normalisation=)`, the
  deep render passes the smoothed pair; shallow pack unchanged (default None); tests. Cost: the clip was rendered a fifth time (`deep-clip-run5.log`).
- R3-03 minor (elapsed figures beside "timing: none recorded"): the elapsed sentence is removed. R3-04 minor (file-name pattern): fixed. R3-05 minor ("nearest
  frame"): reworded to the first frame at or after the grid point.
- R3-06 major REASONED, OUT OF ENVELOPE by the orchestrator's ruling (source identity is the byte count): banked, disclosed in report section 7.
- R3-07 major REASONED, OUT OF ENVELOPE (the 6 s duration is not re-checked at encode; only a programmatic non-default render could be linked): banked, disclosed.

Round 3 state: both in-envelope majors fixed; the clip re-render (fifth) is running (GPU). NEXT: when `deep-clip-run5.log` ends with `elapsed N s`, check `clip/statistics.json`
checks (four ok), rebuild the page (`deep --part stills`, 13 min), full gate (ruff, format, mypy, foreground pytest), regenerate the report (`report_gen.py`, reads
`cell-scripts/gate-record.md` and `round-record.md`), commit, round 4 (`wp13d_build_prompt.py 4`, diff, `wp13d_run_review.sh 4`).
