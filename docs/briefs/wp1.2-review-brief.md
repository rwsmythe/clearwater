# WP1.2 Part A — Independent review (Reviewer B) brief

**Issued by the orchestrator 2026-10-15.** Plan §4.5 item 7; `docs/review-gate-clearwater.md`
Part 2 item 2. You did NOT write WP1.2. Review it against its brief
(`C:\Users\rwsmy\clearwater\docs\briefs\wp1.2-brief.md`, FINAL) and CHARC's rulings, and against
the spec clauses it names. Never review against the author's completion report, which you are
not given.

**CHARC rulings in force** (do not re-litigate; report only a defect in how they are carried out):
- `22f68342748b43f2`: the `cupy-cuda12x[ctk]` extra is within the grant.
- `4db6db642c117b1e`:
  - Option A: float32 GPU Gaussians. The 2e-5 / 2e-6 tolerance applies on the textured scene at
    64x96 and 97x65 and on the 1024 image. The near-flat pair has its own bound of
    1e-4 / 1e-5, with the cause documented.
  - `run.py` defaults to `--device cpu`.
  - `correct(..., backend=None)` and a public `normalisation_bounds()` are accepted.
  - The pipeline is NOT to be optimised in this package; a slow result is a result.

| Field | Content |
|---|---|
| Artifact | Branch `wp1.2` in `C:\Users\rwsmy\clearwater\.worktrees\wp1.2`; base `d27f909`; head = the branch tip named in your dispatch (verify with `git -C`). The author's figures were measured on `d3d9555`; later commits do not touch the timed path (verify). |
| Mode | READ-ONLY on the worktree: no edits, commits, staging or branch switches. Running tests, `run.py` and `bench.py` is allowed. |
| Outputs | Bench records to `C:\Users\rwsmy\clearwater\work\wp1.2a-B\`; evidence to `C:\Users\rwsmy\clearwater-review-evidence\wp1.2\B\` (pass 1), `B2\` (a re-check, if ordered). |
| Withheld | `docs/proofs/wp1.2-ledger.md` and the `probe`, `r1` and `analysis` evidence folders (the author's loop). Do not read them. The bench records in `C:\Users\rwsmy\clearwater\work\wp1.2a\` are NOT withheld: you compare against them. |
| Exclusive | You are the only cell running. Do not run your Codex pass while `bench.py` runs. |
| Machine note | A stray `python.exe` (PID 33616, an orphan from an earlier session) has kept one CPU core busy since 2026-10-14, including through the author's measurements. It is still running. Do not stop it. Record whether it is present (`tasklist /FI "PID eq 33616"`) before your bench runs; it keeps conditions the same as the author's. |

## Order of work

1. **Top-level claims first, on running code.** Measure each of the brief's 8 claims and record
   each command with its output.
   - **Claim 1:** CuPy version and device count. Record whether `[ctk]` was needed, from
     `pyproject.toml` and `uv.lock`. Do not re-create `.venv`; the installation footprint is
     checked from the lock.
   - **Claims 2–4:**
     - the WP1.1 suite, unchanged, with `git -C <wt> diff d27f909..HEAD -- tests/test_prototype_pipeline.py`
       empty;
     - `pytest -q -rs` with the `gpu` tests RUN (count them; a skip fails claim 8);
     - your OWN agreement measurement on your own textured image, about 1–2 MP, both methods,
       CPU against GPU, max-abs and mean-abs;
     - the `auto` fallback, by reading the code and running the tests.
   - **Claim 5, reproduction.** The author's figures are from 60 frames at 4K and 30 at 5.3K. Run:
     - all four GPU cells (4K and 5.3K, both methods) at the brief's N;
     - the CPU cells `4k ancuti2018` and `5.3k ancuti2018` with `--frames 11`. That is enough
       for a median; the full CPU matrix takes over an hour and is not needed.

     Compare each median with the author's JSON record for the same cell in
     `C:\Users\rwsmy\clearwater\work\wp1.2a\`. PASS means within 10%. For peak graphics memory
     and peak RSS, also check within 10%. Note the power source and power mode you ran under.
   - **Claim 6:** re-run `--proxy` once at 4K and compare its relative errors with the report's.
   - **Claim 7:** check that the estimate is at or above the measured pool peak in every one of
     your GPU records.
   - **Claim 8:** run the five gates:
     - `uv run ruff check .`
     - `uv run ruff format --check .`
     - `uv run mypy`
     - `uv run pytest -q -rs`
     - `uv run python -m unittest discover -s tests/harness`
2. **Locks.**
   - `git -C <wt> diff --stat d27f909..HEAD` touches only owned files.
   - The `pyproject.toml` diff is the one grant line, plus at most one mypy override.
   - `uv.lock` adds only cupy-cuda12x, its `ctk` packages and cuda-pathfinder; list any other
     additions.
   - No import of `local_config`, `inventory` or `environment_report`, and nothing under `src/`.
   - No machine-wide environment change in the code (grep for `CUDA_PATH` and `os.environ`
     writes).
3. **Mechanism review (the core of this review).**
   - **One code path:** the namespace comes from `backend.of(array)`. Look for `if gpu`-style
     branches in the mathematics, duplicated mathematics in `backend.py`, and hidden host round
     trips (`.get()`, `asnumpy` or `to_host` inside pipeline functions). Check that
     `correct()` moves data once in and once out.
   - **Timing soundness:** `synchronize()` inside the timed region, warm-up discarded,
     transfers included, `perf_counter`.
   - **Memory provenance:** the pool high-water mark, the `nvidia-smi` readings and when they are
     taken, and the RSS sampler at 50 ms.
   - **Agreement test strength:** check that each test fails on the wrong implementation it
     targets. Spot-check at least three by mutating a COPY in a temp folder, never the worktree.
4. **The report** (`docs/reports/wp1.2a-speed-memory.md`):
   - every claim-5 row is SYNTHETIC-labelled and carries its JSON path and head SHA;
   - the budget arithmetic is right (median / 0.111 and median / 0.056), and the report makes
     no Gate 1 verdict;
   - the installation record is present (plain CuPy insufficient, the reason, each package's
     license);
   - both sets of agreement figures are given, with the cause;
   - both interface deviations are recorded.
5. **Codex pass**, ONE pass at the same tier as Reviewer A: STRONG, WSL, per-call
   `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`.
   - **Setup:** cwd `/mnt/c/Users/rwsmy/clearwater/.worktrees/wp1.2`. Generate the diff
     Windows-side with
     `git -C <worktree> diff -U8 d27f909..HEAD -- . ':!uv.lock' ':!docs/proofs'`; WSL never runs
     git.
   - **Wrapper:**
     `wsl.exe bash -ilc 'export PATH="$HOME/.local/node22/bin:$PATH"; cd <wsl worktree> && cat <prompt> <diff> | codex exec <flags> - > <transcript> 2>&1'`.
   - **Probe first.**
   - **The prompt, built neutrally:**
     - the brief's claim list, and the envelope with a request to TAG out-of-envelope findings;
     - the CHARC rulings above, stated as settled;
     - `CORRECTNESS REVIEW` / `WHAT TO EXAMINE` framing: mechanism, timing soundness, memory
       provenance and agreement-test strength;
     - "report every finding with a severity tag (critical/major/minor)";
     - the read-only-sandbox EXECUTED/REASONED paragraph verbatim from `docs/codex-reviewer.md`;
     - its own paragraph: "Do NOT read `docs/proofs/` or anything under
       `clearwater-review-evidence`; those are withheld from this review."
   - **Assertions** (all `grep -a`):
     - the banner reads `gpt-5.6-sol` / `high`;
     - `^ERROR` and `ERROR codex_core` lines are classified by provenance;
     - a `^tokens used` line is present;
     - there is an anchored VERDICT line;
     - `^ succeeded in` appears at least once;
     - `grep -a -n 'docs/proofs\|wp1.2-ledger'`: classify every hit as an echo or an access.
       Any access voids the pass; report it and do not retry.
   - **Evidence:** the prompt, diff and transcript, each with its md5.
6. **Reproduce before reporting.**
   - Every finding carries a reproduction (the command and its output), or is marked REASONED
     with the trace.
   - Adjudicate every Codex finding: adopt it with your own reproduction, or reject it with a
     cited ground.

## B2 re-check (ordered 2026-10-15)

Pass 1 on `9408d18` was BLOCKING on F1 (the GPU c3 cells were -14% and -16.6% against the
author's first window), with minors F2–F4. The author's fixes, now at head `873ae6d`:
- `41538bf`: `ambient` records the power-mode overlay and the GPU state (nvidia-smi clocks,
  temperature, power, P-state, throttle reasons) at the start and end of each loop.
- `f234dbf`: F3, a transfer guard in the device tests and a GPU check of the 2-D `expand`.
- `72c19cc`: the `gpu` marks restored.
- The report and ledger updated for F2 and F4.
- The GPU cells were re-measured with no stray process (PID 33616 was stopped about 05:20Z on
  the owner's direction). The first window is kept in a spread table.
- One window-3 cell overlapped an orchestrator harness run, so it was discarded (renamed
  `DISCARDED-...json.txt`) and re-run.

B2 runs in an exclusive window. Evidence goes in `B2\`; bench records in
`C:\Users\rwsmy\clearwater\work\wp1.2a-B2\`.

1. **Reproduction.**
   - Confirm PID 33616 is absent and that no Codex run or other cell is running.
   - Re-run all four GPU cells at the brief's N on the head.
   - Compare each median with the author's current report rows (the records the report cites).
     PASS is within 10%.
   - Record your ambient: the overlay and the GPU state, now in the record.
   - The CPU cells are NOT re-run: pass 1 reproduced them, and the timed path is unchanged
     (verify that `git -C <wt> diff 9408d18..HEAD -- tools/prototype/pipeline.py` is empty, and
     that the `bench.py` changes sit outside the timed region).
2. **F2–F4 RESOLVED, by reproduction.**
   - F2: recompute the context-and-libraries figure from a record.
   - F3: the guard catches the host-round-trip `white_balance` mutant (run on a COPY), and the
     2-D `expand` is now exercised on the GPU.
   - F4: the supplementary table's labels are correct.
3. **The new report text** is consistent with the cited records:
   - the scheme is distinguished from the overlay;
   - the spread table is correct;
   - the discard note names the cell, the renamed file and the replacement record;
   - no figure from an overlapped or stray-present window is presented as clean.
4. **Gates and markers.**
   - Run the five gates once your bench runs have finished.
   - `-m gpu` must run 17 tests with none skipped.
   - Check that every GPU test carries its `gpu` mark; the author reported a slip there.
5. **No new Codex pass**, unless a fix changed the pipeline mathematics (it should not). Say
   whether one was needed.

## Return (your FINAL message; it reaches the orchestrator directly; under about 70 lines)

- the head SHA reviewed;
- claims 1–8, each PASS/FAIL with the command and its output line;
- the reproduction table, one row per cell: yours, the author's, % difference, PASS/FAIL;
- the lock results;
- the mechanism review;
- the report checks;
- findings, each with severity, in/out of envelope, EXECUTED/REASONED, reproduction and file:line;
- the Codex pass: banner, assertions, verdict, evidence md5s;
- the verdict: NO_BLOCKING or BLOCKING.

Never post to a mailbox.
