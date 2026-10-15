# WP1.5 — Independent review (Reviewer B) brief

**Issued by the orchestrator 2026-10-15.** Plan §4.5 item 7; `docs/review-gate-clearwater.md`
Part 2 item 2. You did NOT write WP1.5. Review it against its brief
(`C:\Users\rwsmy\clearwater\docs\briefs\wp1.5-brief.md`, FINAL) and against the spec clauses it
names (spec **v0.5.1**, `C:\Users\rwsmy\clearwater\docs\underwater-correction-spec.md`: 6.5, 7.5,
8.2, 8.3, D54, D55, D60, D73, D74, D94, D95, D104, D105, D114). Never review against the
author's completion report, which you are not given. The report
`docs/reports/wp1.5-container-spike.md` IS a deliverable under review.

| Field | Content |
|---|---|
| Artifact | Branch `wp1.5` in `C:\Users\rwsmy\clearwater\.worktrees\wp1.5`; base `7048fd7`; head = the tip named in your dispatch (verify with `git -C`). |
| Mode | READ-ONLY on the worktree: no edits, commits, staging or branch switches. Running the tests, `spike.py` and `compare.py` is allowed. |
| Footage | `C:\Users\rwsmy\clearwater-footage\` is READ-ONLY and input only. Never write, rename or delete there; never pass it as an output, a log or a stats path. The owner may still be downloading into its `SCUBA` subfolder; ignore that subfolder. |
| Your outputs | Run `spike.py` with `--config <your toml>`, where your toml (kept in your evidence folder) has the same `footage_path` and `working_path = 'C:\Users\rwsmy\clearwater\work\wp1.5-B'`. Your files then land in `C:\Users\rwsmy\clearwater\work\wp1.5-B\wp1.5\`. Never write into the author's `C:\Users\rwsmy\clearwater\work\wp1.5\`. Evidence goes to `C:\Users\rwsmy\clearwater-review-evidence\wp1.5\B\`. |
| Withheld | `docs/proofs/wp1.5-ledger.md` and the `probe`, `r1` and `r2` evidence folders under `clearwater-review-evidence\wp1.5\` (the author's loop). Do not read them. The author's records in `C:\Users\rwsmy\clearwater\work\wp1.5\` are NOT withheld: you compare against them. |
| PATH | Prepend `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` for every ffmpeg, ffprobe and pytest run, or the tests skip. |
| Running alone | You are the only cell running. Nothing here is a timing result. |

## Order of work

1. **Top-level claims first, on running code.** Record each command with its output.
   - **Claim 1, capability.** Run `spike.py capability` with your config. Every proof must hold:
     NVENC 10-bit and 8-bit, libx265 10-bit and 8-bit, and the `-hwaccel cuda` decode. Confirm
     the NVENC 10-bit proof yourself with your own `ffprobe` call on your proof file (profile
     Main 10, `yuv420p10le`, 60 frames). Compare your record with the author's
     `capability.json`.
   - **Claim 2, camera.** Run `spike.py camera GX011627.MP4 GX011628.MP4` with your config.
     Compare each property with the author's `camera.json` and with the report's section 3.
     Check by your own ffprobe call that the range really is `pc` (full) on GX011627.
   - **Claim 3, re-encode.** Run `spike.py reencode` on `GX011628.MP4` and `GX011627.MP4` with
     your config. The command line must match the report's section 4. Your output need not be
     byte-identical to the author's; say whether it is.
   - **Claim 4, comparison reproduces.**
     - Run `compare.py` on the author's two outputs (source against the author's
       `GX0116xx_corrected.MP4`), with `--out` in your folder. Every item's status and values
       must equal the author's JSON (paths and run stamps aside).
     - Run it on your own two outputs and give the summary.
   - **Claims 5-7.** Check the `.LRV` statement against the footage listing (top level only),
     check the recommendation (step 3), and run the gates (step 5).
2. **Is the instrument trustworthy? (The core of this review.)** Do not take `compare.py` on
   trust.
   - **Independent cross-check.** By your own commands, not `compare.py`, on the author's
     GX011628 pair, check:
     - the full presentation pts sequence of every video frame, from `ffprobe -show_frames`, in
       both files, diffed;
     - every audio packet's pts, duration, size and MD5 (`-show_packets -show_data_hash MD5`),
       in both files, diffed;
     - the `elst` of each track as written, read with your own box dump (a short script of
       yours in your evidence folder, or `ffprobe -v trace` lines). Then decide whether the
       report's "presentation effect" reading of the edit list is computed correctly.
   - **It must catch the failures it exists to catch.** Make at least three deliberately broken
     re-encodes of GX011628, each written only into `work\wp1.5-B\wp1.5\broken\`, and check
     that `compare.py` reports each as a MANDATORY DIFFERENT:
     - audio shifted, for example `-itsoffset 0.1` on the audio input;
     - timestamps reset, without `-copyts` and with `-fps_mode cfr` at another rate, or with a
       dropped frame;
     - a rotation added (`-display_rotation` or a display-matrix side-data option on the
       output).
     If your FFmpeg cannot build one of these, say so and choose another MANDATORY failure.
   - **Output-path safety.**
     - Read `check_output_path` and `write_checked`, and every ffmpeg argument list in
       `spike.py`.
     - Look for any option that writes a side file outside the checked path: `-report`,
       `-passlogfile`, `stats_file`, x265 or NVENC logs, two-pass files, or the PSNR filter's
       `stats_file`.
     - Snapshot the four top-level chapters before and after your runs (name, size, mtime) and
       confirm nothing changed.
3. **The recommendation, against the table and the spec.**
   - Does SIMPLE follow from the comparison table under D105 and 7.5 as written?
   - Two readings in the report are open to challenge. Give your view of each; CHARC rules:
     - the edit-list item compared by presentation effect (MANDATORY), with the as-written
       form BEST-EFFORT;
     - a separate REQUIRED class for the colour and format items (D55, D114, 8.2), outside
       D105's two classes.
   - Is any D105 MANDATORY item missing from the comparison, or weaker than the brief's claim
     4 (exact, full sequence, not sampled)?
   - Is the camera's full-range (`pc`) tagging handled correctly against D54 and D55? It
     differs from D54's limited assumption for untagged streams.
   - Is the "frame access for the correction is NOT exercised" statement plain and correct?
4. **Locks.**
   - `git -C <wt> diff --stat 7048fd7..HEAD` touches only the six owned files.
   - No `pyproject.toml` or `uv.lock` change; no PyAV import; nothing under `src/`.
   - The footage folder is input only (step 2 snapshot, plus a grep of the code for writes).
5. **Gates.**
   - `uv run ruff check .`, `uv run ruff format --check .` and `uv run mypy`.
   - `uv run pytest -q -rs`, with the WP1.5 `footage` test and both NVENC `gpu` tests RUN, not
     skipped.
   - `uv run python -m unittest discover -s tests/harness`.
   - The author saw one failure outside this package:
     `tests/test_inventory.py::test_real_footage_has_one_row_per_media_file` (WP0.2). Its
     before/after footage snapshot differed while the owner was downloading into `SCUBA`. If
     you see it, show the cause (for example, a `.crswap` file whose size changed) and classify
     it. Do not fix it.
6. **Codex pass**, ONE pass at the same tier as Reviewer A: STRONG, WSL, per-call
   `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`.
   - **Setup:** cwd `/mnt/c/Users/rwsmy/clearwater/.worktrees/wp1.5`. Generate the diff
     Windows-side with
     `git -C <worktree> diff -U8 7048fd7..HEAD -- . ':!uv.lock' ':!docs/proofs'`; WSL never
     runs git. The report is in the diff.
   - **Wrapper:**
     `wsl.exe bash -ilc 'export PATH="$HOME/.local/node22/bin:$PATH"; cd <wsl worktree> && cat <prompt> <diff> | codex exec <flags> - > <transcript> 2>&1'`.
   - **Probe first.**
   - **The prompt, built neutrally:**
     - the brief's claim list, and the envelope with a request to TAG out-of-envelope
       findings;
     - `CORRECTNESS REVIEW` / `WHAT TO EXAMINE` framing: completeness against D105's list,
       exactness of the timestamp comparison, whether the capability proofs are proofs,
       whether the recommendation follows from the table, and whether any ffmpeg flag could
       write outside the working folder;
     - "report every finding with a severity tag (critical/major/minor)";
     - the read-only-sandbox EXECUTED/REASONED paragraph verbatim from `docs/codex-reviewer.md`;
     - its own paragraph: "Do NOT read `docs/proofs/` or anything under
       `clearwater-review-evidence`; those are withheld from this review. Never read or list
       `C:\Users\rwsmy\clearwater-footage` (`/mnt/c/Users/rwsmy/clearwater-footage`)."
   - **Assertions** (all `grep -a`):
     - the banner reads `gpt-5.6-sol` / `high`;
     - `^ERROR` and `ERROR codex_core` lines are classified by provenance;
     - a `^tokens used` line is present;
     - there is an anchored VERDICT line;
     - `^ succeeded in` appears at least once;
     - `grep -a -n 'docs/proofs\|wp1.5-ledger'`: classify every hit as an echo or an access.
       Any access voids the pass; report it and do not retry.
   - **Evidence:** the prompt, diff and transcript, each with its md5.
7. **Reproduce before reporting.**
   - Every finding carries a reproduction (the command and its output), or is marked REASONED
     with the trace.
   - Adjudicate every Codex finding: adopt it with your own reproduction, or reject it with a
     cited ground.

## Return (your FINAL message; it reaches the orchestrator directly; under about 70 lines)

- the head SHA reviewed;
- claims 1-7, each PASS/FAIL with the command and its output line;
- the reproduction results: capability, camera, your re-encode, and compare on the author's
  outputs (identical: yes/no, with any difference named);
- the instrument checks: the independent cross-check and each broken re-encode (caught: yes/no);
- output-path safety and the footage snapshot;
- your view on the recommendation and on the two readings;
- the lock results;
- findings, each with severity, in/out of envelope, EXECUTED/REASONED, reproduction and
  file:line;
- the Codex pass: banner, assertions, verdict, evidence md5s;
- the verdict: NO_BLOCKING or BLOCKING.

Never post to a mailbox.
