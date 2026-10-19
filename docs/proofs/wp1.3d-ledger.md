# WP1.3D ledger (implementer cell, worktree `.worktrees/wp1.3d`, branch `wp1.3d`, base `c80725b`)

Cell: implementer-sonnet-high. Spec v0.5.3. Brief `docs/briefs/wp1.3d-brief.md`.

## Progress

| Step | State |
|---|---|
| scan.py (measures, picker, deep-frames.json, per-chapter cache and resume) + tests 1-4, 7 | committed (see log) |
| scan run over the eight SCUBA chapters | in progress: GX011589-92 done; 93, 98, 600, 601 to do |
| pack.py `deep` command (stills, pages) + test 5 | not started |
| deep clip (STAGED, gaussian 2.0 s, c3 + ancuti2018) | not started |
| report, CP2 deep sheet | not started |
| review rounds | not started |

## Facts learned

- GX011589 is a 6.4 s chapter (one scan frame at 5 s); the others run 42 s to 1047 s.
- The scan costs about 6 s per frame (probe plus 4K HEVC seek and decode): GX011600 (104 frames) is
  over the 10 minute tool limit, hence the batch-and-resume in `scan_chapter`.
- Working tree files are CRLF on disk (autocrlf), LF in the index.

## Round ledger

(no review round yet)
