# WP1.1 — Independent review (Reviewer B) brief

**Issued by the orchestrator 2026-10-15.** Plan §4.5 item 7; `docs/review-gate-clearwater.md`
Part 2 item 2. You did NOT write WP1.1. Review it against its brief
(`C:\Users\rwsmy\clearwater\docs\briefs\wp1.1-brief.md`, FINAL, amended c9e7b58) and the spec
clauses it names (spec `docs/underwater-correction-spec.md` sections 6.1–6.7 and 14.1; read
nothing else of the spec unless a clause there points to it). Never review against the author's
completion report, which you are not given.

| Field | Content |
|---|---|
| Artifact | Branch `wp1.1` in `C:\Users\rwsmy\clearwater\.worktrees\wp1.1`; base `46a10b9`; head = the branch tip named in your dispatch (verify with `git -C`). |
| Mode | READ-ONLY on the worktree: no edits, commits, staging or branch switches. Running tests and `run.py` is allowed. Outputs go to a temp folder or the evidence folder only. |
| Footage | None. Do not read `C:\Users\rwsmy\clearwater-footage`. Synthetic images only. |
| Evidence | `C:\Users\rwsmy\clearwater-review-evidence\wp1.1\B\` (pass 1), `B2\` (a re-check pass, if one is ordered). |
| Withheld | `docs/proofs/wp1.1-ledger.md` and the `probe`/`r1`/`r2`/`r3`/`analysis` evidence folders (the author's loop). Do not read them. |
| Hardware | No timing or memory figure is a result (brief "Hardware flags"). Keep runs small; no 48 MP runs. |

## Order of work

1. **Top-level claims first, end to end on running code.** For each of the brief's six claims,
   measure it on running code and record each command with its output:
   - Claim 1: generate a synthetic photo (a blue-green cast, gradients plus texture, around
     1–2 MP) with Pillow in a temp folder. Run `uv run python tools/prototype/run.py` with
     `--method ancuti2018` and with `--method c3`, with and without `--dump`. Check that the
     output is 16-bit RGB of the right shape and that the intermediates were written. Also check
     exit 2 and a one-line error for a bad argument and for an unreadable file.
   - Claim 3: your own 2x check with your own scene. Confirm that every spatial parameter passes
     through `spatial_sigma`, by grep and by reading.
   - Claims 2, 4 and 5: see items 3 and 4 below.
   - Claim 6: all five gate commands, run in the worktree:
     - `uv run ruff check .`
     - `uv run ruff format --check .`
     - `uv run mypy`
     - `uv run pytest -q -rs`
     - `uv run python -m unittest discover -s tests/harness`
2. **Locks.**
   - `git -C <worktree> diff --stat 46a10b9..HEAD` touches only owned files.
   - The `pyproject.toml` diff is the numpy and scipy dev-group grants plus at most one mypy
     override naming exactly `scipy`.
   - `uv.lock` adds only numpy and scipy (report any transitive additions).
   - No import of `local_config`, `inventory` or `environment_report`.
   - Nothing under `src/`.
   - The only `sys.path` manipulation is the `__package__`-guarded bootstrap in `run.py`.
   - No OpenCV, scikit-image, CuPy or PyTorch.
3. **Equation fidelity (the core of this review).** Check every step in `pipeline.py` against
   spec 6.2 and 6.3.1/6.3.2 symbol for symbol, with the papers as authority where the spec
   summarises (6.1).
   - The steps: Ancuti 2018 red/blue compensation with alpha and the gain caps; 3C in BT.709
     YCbCr with kappa/lambda, the mask M and the large-support Gaussian; gray-world white
     balance with the D99 clamp; the two fusion inputs and N{}; the three weight maps; the
     regularised normalisation `(W_k + delta) / (sum W_k + K * delta)`; the pyramid
     decomposition, blend and collapse.
   - Where you rely on your knowledge of a paper, say so and state the equation.
   - **Specific question:** the Laplacian contrast weight is implemented as
     `|sigma^2 * Lap(G_sigma * L)|` (sigma from `laplacian_fraction`), not the paper's per-pixel
     `|Lap(L)|`. Give your independent judgement: is it a faithful reading of spec 6.6/D56, what
     does it change in practice at photo and 4K sizes? CHARC has RULED it accepted
     (`ad686b8b65a71061`, spec-driven departure from [A18]), so the form is not itself a finding.
     Report a defect only in how it is implemented, or a concrete harm the ruling did not weigh.
4. **The two reports.**
   - `docs/reports/wp1.1-3c-correspondence.md`: check the kappa -> Cr / lambda -> Cb
     derivation, and reproduce its synthetic red-deficient demonstration.
   - `docs/reports/wp1.1-open-values.md`: check that every value spec 14.1 lists, plus those
     claim 5 names, is present with a source. Check each numeric figure the reports quote
     against your own run where feasible (neutral-set tolerance, the 2x figures).
5. **Code-level review** of the diff against the brief's Interfaces section and test roster.
   - Measure each departure from the stated signatures or semantics. For each, say whether it is
     additive or changes a stated behaviour.
   - Check that each roster test would fail on the wrong implementation it targets. Spot-check at
     least three by mutating a COPY of the code in a temp folder, never the worktree.
6. **Codex pass** (same tier as Reviewer A): STRONG, WSL, per-call
   `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`.
   - Working directory and diff: cwd `/mnt/c/Users/rwsmy/clearwater/.worktrees/wp1.1`. Generate
     the diff Windows-side with
     `git -C <worktree> diff -U8 46a10b9..HEAD -- . ':!uv.lock' ':!docs/proofs'`; WSL never runs
     git.
   - Wrapper:
     `wsl.exe bash -ilc 'export PATH="$HOME/.local/node22/bin:$PATH"; cd <wsl worktree> && cat <prompt> <diff> | codex exec <flags> - > <transcript> 2>&1'`.
   - Probe first through the exact invocation; expect one `^ succeeded in` line.
   - **Prompt, built neutrally:**
     - the brief's claim list and declared envelope, asking the reviewer to TAG
       out-of-envelope findings;
     - `CORRECTNESS REVIEW` / `WHAT TO EXAMINE` framing, where WHAT TO EXAMINE names equation
       fidelity to spec 6.2/6.3 and the two papers;
     - "report every finding with a severity tag (critical/major/minor)";
     - the read-only-sandbox EXECUTED/REASONED paragraph verbatim from
       `docs/codex-reviewer.md`.

     No ledger, no author notes.
   - **ONE pass.** Assert on the transcript, all with `grep -a`:
     - banner `gpt-5.6-sol` / `high`;
     - `^ERROR` and `ERROR codex_core` lines, each classified by provenance;
     - a `^tokens used` footer;
     - an anchored VERDICT line;
     - a `^ succeeded in` count of at least 1.
   - **Evidence:** copy the prompt, diff and transcript to the evidence folder with md5s.
7. **Reproduce before reporting.**
   - Every finding carries a reproduction (a command and its output), or is marked REASONED with
     the trace.
   - Adjudicate each Codex finding: adopt it with your own reproduction, or reject it with a cited
     ground.
   - A disagreement on what a paper says that you cannot settle is reported with both readings,
     not adjudicated.

## Return (your FINAL message; it reaches the orchestrator directly; under about 70 lines)

- the head SHA reviewed;
- claims 1–6, each PASS/FAIL with the measuring command and its output line;
- the lock results;
- equation fidelity, step by step (OK, or the finding);
- your Laplacian judgement;
- the report checks;
- departures from the brief, each marked additive or behaviour-changing;
- findings, each with severity, in/out of envelope, EXECUTED/REASONED, the reproduction and
  file:line;
- the Codex pass: banner, assertions, verdict, evidence md5s;
- the verdict, NO_BLOCKING or BLOCKING.

Never post to a mailbox.
