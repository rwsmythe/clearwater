# WP1.3 — Remediation brief (Reviewer B round 1)

**Issued by the orchestrator 2026-10-15.** This is the ONE bounded remediation that
`docs/review-gate-clearwater.md` Part 2 item 2 allows after a blocking Reviewer B.

The original author cell is past its context cap (412K), so a fresh cell carries the author's
loop forward on the same branch. Read these first:
- the package brief, `docs/briefs/wp1.3-brief.md` (FINAL), including both "Decisions fixed at
  issue" blocks;
- the report as it stands, `docs/reports/wp1.3-look-check.md`;
- the spec, `docs/underwater-correction-spec.md` v0.5.2: 6.5, 7.1, D54, D55.

| Field | Content |
|---|---|
| Worktree | `C:\Users\rwsmy\clearwater\.worktrees\wp1.3`, branch `wp1.3`, head `0233a8e`. It holds a copied `clearwater.local.toml` (gitignored; never edit or commit it). |
| Files owned | The same six as the brief: `tools/lookcheck/{__init__,frames,pack}.py`, `tests/test_lookcheck.py`, `docs/reports/wp1.3-look-check.md`, `docs/proofs/wp1.3-ledger.md`. No other file; nothing under `tools/prototype/` or `src/`; no `pyproject.toml` change. |
| Outputs | `C:\Users\rwsmy\clearwater\work\wp1.3\` only. The footage folder `C:\Users\rwsmy\clearwater-footage\` is READ-ONLY input. |
| PATH | Prepend `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` for every ffmpeg, ffprobe and pytest run. |

## Findings to close

The gate seat (orchestrator) has adjudicated every finding below. Reviewer B evidence:
`C:\Users\rwsmy\clearwater-review-evidence\wp1.3\reviewB\review-B.txt`. You may read it (it is
the gate's, not your loop's; your own ledger and `r1`/`r2` evidence stay yours).

| # | Reviewer B finding | Disposition: what to do |
|---|---|---|
| B1 | MAJOR: the tests' `_roots()` fabricates `<tmp_path>/footage` as the footage root, so a `--basetemp` or `TMP`/`TEMP` inside the REAL footage folder lets the synthetic tests write there. | **Fix.** In the tests: (a) when the local configuration loads, the test roots use the REAL footage folder as `footage`, so the production check refuses such a write; (b) an autouse guard fails the test at once if `tmp_path` resolves inside the configured footage folder; (c) any test that writes outside `roots.allowed` (for example to `roots.allowed.parent`) goes through the same check. Add a test that a root under a (monkeypatched) configured footage folder is refused. |
| B2 | MAJOR: `verify_clip()` checks metadata and timing only; the read-back checks frame 0 (and an ad hoc check frames 90 and 179). An encode that duplicates or drops one frame with correct pts passes, and then the intermediates are deleted. | **Fix.** Before ANY intermediate is deleted, read back EVERY frame of BOTH clips and match each to its own PNG. Decoding at a reduced size is allowed (state the method). Record, per frame, the difference to its own PNG and to each neighbour (index -1 and +1) in `flicker\statistics.json`. The check passes only if every frame matches its own PNG within a stated threshold AND better than its neighbours. If real frames are too alike for that to decide, STOP and report the margin. Tests: a clip with one frame duplicated (frame k replaced by k-1), and one with two frames swapped, each FAIL by name; distinct synthetic frames pass. |
| B3 | MAJOR: an exception from verification (ffprobe failure, a timeout, bad JSON, a raising read-back) leaves an unverified MP4 under its final name; a failure on the second clip leaves the first. | **Fix.** No final-named clip exists unless both clips are verified (write to temporary names in `flicker\` and rename both only after both pass, or delete on any exception and re-raise). Tests: `verify_clip` raising leaves no clip; the second encode failing leaves neither clip. |
| B4 | MINOR: the report's "R and B about -1, G +0.35" bias and the frame 90/179 read-back are not in any record. | **Fix.** B2's per-frame read-back goes into the JSON. Record the per-channel bias there too, or remove the sentence. Every number in the report must cite a record or be marked informal. |
| B5 | MINOR (executed): "every output under `work\wp1.3\`" is false for Python bytecode and the CuPy kernel cache. | **Reword only.** State the true scope, as WP1.5 did: "every file the package's FFmpeg runs and writers produce". Bytecode, the pytest cache and the CuPy kernel cache belong to the interpreter and libraries. |
| B11 | MINOR: the range control reads one pixel per quadrant. | **Fix.** Compare the whole interior of each quadrant (a stated margin away from the edges, where chroma upsampling blends colours) and report the worst error over it. The planted failures must still fail by name. |
| B6 | MAJOR, OUT of envelope: D54's fallback is not implemented. An untagged `yuvj420p` stream is taken as `pc`; missing primaries and transfer stay `unknown`; an unexpected range or matrix is refused rather than assumed with a warning; direct `extract`/`excerpt` callers get no warning. | **No code.** The report's section 2 states this plainly, so WP1.4 and WP3.5 know: the instrument does not implement D54's assumed BT.709-limited fallback with a warning. Banked by the orchestrator (DR-20). |
| B7-B10 | MINOR, OUT of envelope: duplicate or non-monotonic pts are de-duplicated; `%` in a root path is expanded by FFmpeg; `verify_clip` accepts `yuvj420p`/`tv` and skips `unknown` tags; `v:0` is taken without checking for cover art. | **No code.** Banked (DR-20). One sentence in the report's limits is enough. |

## Then

1. **Re-run the flicker clip** (`pack.py`'s flicker step) so the delivered clips pass B2's
   full read-back and B3's naming.
   - First keep a copy of the current `flicker\statistics.json` in `work\wp1.3\logs\`.
   - Confirm the 180 frames' statistics are identical to the digit, and the excerpt ticks are
     205205..384384.
   - The stills need no re-run unless your change touches their path. Say which.
2. **Report.** Update sections 2, 5 and 8 and the limits. Fill the ledger's context-depth
   column for the author cell (`wp13-cell`: 412K at return).
3. **Gates.**
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run mypy`
   - `uv run pytest -q -rs` (the `footage` and `gpu` tests RUN; 0 skipped)
   - `uv run pytest -q -m gpu`

   The harness gate stays untouched (no `scripts/`, `.claude/`, kernel-doc or `tests/harness/`
   change).
4. **ONE Reviewer A round** on the delta `0233a8e..HEAD`, per the brief's "Review loop" section.
   - Tier STRONG; WSL; codex-cli 0.162.1; flags
     `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`.
   - Probe first. The diff is generated Windows-side, excluding `uv.lock` and `docs/proofs`.
   - In the prompt: the withheld paths named (`docs/proofs/`, `clearwater-review-evidence`),
     "never read or list the footage folder", and the EXECUTED/REASONED paragraph verbatim from
     `docs/codex-reviewer.md`.
   - The six assertions, including `grep -a -n 'docs/proofs\|wp1.3-ledger'` with every hit
     classified.
   - Fix minors once. Append round 3 to the ledger; evidence to
     `C:\Users\rwsmy\clearwater-review-evidence\wp1.3\r3\` with md5s.
   - A new critical or major found in this round is FIXED if this remediation introduced it;
     otherwise report it.
5. **Commit** by pathspec (`fix(wp1.3): ...`, `docs(wp1.3): ...`), footer `Co-Authored-By:`
   naming the model you actually run as. Never `git stash`.

## STOP for

- a full read-back that cannot tell frames apart on the real clip;
- flicker statistics that differ from the kept copy;
- any need to write outside `work\wp1.3\`, or to touch `tools/prototype/`;
- any dependency change.

## Return (your FINAL message, under about 60 lines)

- the new head and a per-commit list;
- each of B1-B5 and B11 with what was done and the test that covers it, plus the report text
  for B6-B10;
- the read-back results on both clips (the worst own-frame difference, the smallest margin to a
  neighbour), and the statistics-identity result;
- the gate lines;
- round 3's result with its assertions;
- the locks.

**Working rules:** never use a bare `cd`; never post to a mailbox.
