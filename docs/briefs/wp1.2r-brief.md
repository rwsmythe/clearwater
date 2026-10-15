# WP1.2R — Prototype remediation (retroactive Reviewer B) — dispatch brief (FINAL)

**Issued by the orchestrator 2026-10-15** on CHARC's confirmation `2b3066dac88ed847`.

| Field | Content |
|---|---|
| Spec | **v0.5.1**. |
| Cell | `implementer-sonnet-high`. |
| Worktree | `.worktrees/wp1.2r`, branch `wp1.2r`, base = the main commit named in the dispatch, which carries this file. |

**Context.** WP1.1 and WP1.2 Part A were accepted with Reviewer B run as a cell, which was the
old form. The orchestrator's retroactive seat-run Reviewer B over `tools/prototype` found:
- two introduced majors, M1 and M2;
- one spec-interpretation major, M3, now ruled;
- two minors to fix, m5 and m7.

This package closes them. It is a bounded remediation: it is NOT WP1.2 Part B, and it is NOT an
optimisation.

The Reviewer B transcript is
`C:\Users\rwsmy\clearwater-review-evidence\prototype-retroB\review-B.txt`; you may read it.

| Field | Content |
|---|---|
| Files owned | `tools/prototype/backend.py`, `tools/prototype/params.py`, `tools/prototype/run.py` (only if the M2 clean-error path needs it), `tools/prototype/pipeline.py` (ONLY the M3 docstrings and, if the dtype test needs one, a minimal hook that changes no behaviour), `tests/test_prototype_backend.py` and `tests/test_prototype_pipeline.py` (ADDITIONS ONLY: every existing test stays byte-unchanged), `docs/reports/wp1.2a-speed-memory.md` (m5 wording), `docs/reports/wp1.1-open-values.md` (the M3 note), `docs/proofs/wp1.2r-ledger.md`. |
| Not touched | The pipeline's mathematics and defaults; `bench.py`'s timed path (`bench.py` is not owned); `pyproject.toml` and `uv.lock`; anything under `src/`. No timing or memory figure changes. |
| Hardware | `gpu` tests must RUN (CuPy and the RTX 4070 are present). Not timing-exclusive. |

## Findings to close (dispositions confirmed by CHARC; do not re-decide)

1. **M1, `backend.py` `_probe_gpu`.**
   - The problem: `import cupy` is guarded by `except ImportError` only. An `OSError("DLL load
     failed")` or any other initialisation exception escapes `select_backend("auto")`, which
     breaks the documented "auto never raises" contract.
   - Fix: catch any exception at the import (`except Exception`), return `None` with the reason
     logged verbatim (the `_one_line(exc)` pattern), and fall back to the CPU.
   - Test (CPU-only, unmarked): monkeypatch `importlib.import_module` so the `cupy` import raises
     `OSError("DLL load failed")`. Then `select_backend("auto")` returns the CPU backend, and the
     logged reason contains the message.
2. **M2, derived-value validation.**
   - The problem: `--set sharpen_blur_fraction=1e308` is accepted, and its derived sigma
     (fraction x short side) becomes `inf`. The result is an uncaught traceback instead of
     `run.py`'s one-line error and exit 2.
   - Fix: validate the DERIVED values before processing.
     - Every spatial sigma from `spatial_sigma` must be finite and positive.
     - Every control that is cast to float32 must lie within float32's finite range.
   - On failure, raise the error type `run.py` already reports as one line with exit 2, and NAME
     the offending parameter.
   - Choose the site: `Params` validation where the value alone decides; a pre-processing check
     where the image size is needed. Document the choice.
   - Tests:
     - a finite fraction whose derived sigma overflows gives a one-line error naming the
       parameter, with exit status 2 from `run.main([...])`;
     - the same check through `correct()` raises the documented error type.
3. **M3, RULED by CHARC; carry it out as written.**

   > **M3 RULED: option (a).** Spec 6.4 / D39 ("Internal processing in 32-bit float;
   > quantization only at export") governs the image data and every per-pixel operation; its
   > purpose is to forbid intermediate quantisation, not to cap the width of a scalar reduction.
   > Scalar reductions (channel means, the Ancuti cap statistic, the saliency mean) MAY
   > accumulate in float64 provided (1) the result is cast to float32 before it touches image
   > data or a parameter, (2) both backends use the same accumulator dtype so CPU/GPU agreement
   > rests on a stable reduction, and (3) the choice is stated in the docstring of each
   > reduction and once in `docs/reports/wp1.1-open-values.md` as an interpretation note citing
   > 6.4/D39. This is an interpretation, not a spec change ... WP1.2R adds one test that
   > asserts the accumulator dtype and the float32 cast at each of the three sites (cheap,
   > locks the ruling).

   - **The sites,** per Reviewer B: `pipeline.py:294` (`shape.mean(dtype=np.float64)`, the Ancuti
     cap statistic), `pipeline.py:831` (the saliency Lab mean) and `pipeline.py:869-870`
     (`_channel_means`).
   - **Verify every site, and find any others.** Look for every `float64` or `dtype=` reduction
     in `pipeline.py`. `pipeline.py:77` and `run.py:118/121` are not reductions on image data
     inside the pipeline; classify them in the ledger.
   - **Condition (1):** each result is cast to float32, or to a Python float that is then used
     as a float32 scalar, before it touches image data or a parameter. Where the code does not
     do so, that is a finding: report it and STOP before changing any arithmetic.
   - **Condition (2):** the GPU backend uses the same accumulator dtype through the same
     `xp`-generic call. Show this from the code, plus one `gpu`-marked assertion.
   - **Condition (3):** add the docstring notes, and one interpretation note in
     `wp1.1-open-values.md` citing 6.4/D39 and this ruling.
   - **Test:** assert the accumulator dtype and the float32 cast at each site, on CPU, and on
     GPU under the `gpu` mark. A spy on the array's `mean`, or a minimal no-behaviour hook, is
     acceptable; say which.
4. **m5, report wording.** The bench's 50 ms RSS sampler reads 4 to 9 MiB below the OS peak
   working set in three records.
   - In `docs/reports/wp1.2a-speed-memory.md`, the column header becomes "peak RSS (sampled at
     50 ms)".
   - Add one note: a sampler can miss a short peak; the gap seen was 4 to 9 MiB, against the
     16 GB limit.
   - No figure changes.
5. **m7, test.** No test makes the blue gain cap (D52) bind, so ignoring `blue_gain_cap`, or
   using the red cap for blue, would pass.
   - Add a test with blue compensation on, where the blue cap binds and the red cap does not.
   - Assert that the blue gain equals the blue cap and that the red channel is unaffected by
     it.

Not in scope:
- **M4** (scale matching at a short side of 128 px or less): pre-ruled; the orchestrator
  records it in an addendum.
- **m6** (the transfer guard cannot see `ndarray.get()`/`set()`): already recorded.

## Gates and review

- **Gates:** `uv sync`, then each of the following, with
  `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` prepended to PATH:
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run mypy`
  - `uv run pytest -q -rs` (no `gpu` skips)
  - `uv run pytest -q -m gpu`
  - `uv run python -m unittest discover -s tests/harness`

  The WP0.2 footage-snapshot test may fail while a `.crswap` file in
  `clearwater-footage\SCUBA` grows. If it fails, record the differing file and do not fix it.
- **ONE Reviewer A round, STRONG**, per `docs/review-gate-clearwater.md` Part 1:
  - Transport: WSL, codex-cli 0.162.1, with the per-call flags
    `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`.
  - Probe first.
  - Diff generated Windows-side:
    `git -C <worktree> diff -U8 <base>..HEAD -- . ':!uv.lock' ':!docs/proofs'`.
  - The prompt carries:
    - the five fixes above as the claim list;
    - the M3 ruling verbatim, stated as settled;
    - the envelope (WP1.1's and WP1.2's, below) with the TAG request;
    - the EXECUTED/REASONED paragraph verbatim from `docs/codex-reviewer.md`;
    - its own paragraph: "Do NOT read `docs/proofs/` or anything under
      `clearwater-review-evidence`. Never read or list `C:\Users\rwsmy\clearwater-footage`."
  - The six assertions:
    - the banner;
    - `^ERROR` and `ERROR codex_core` lines, classified by provenance;
    - the `^tokens used` footer;
    - an anchored VERDICT line;
    - `^ succeeded in`;
    - `grep -a -n 'docs/proofs\|wp1.2r-ledger'`, with every hit classified.
  - Fix minors once.
  - A NEW in-envelope critical or major is fixed if this package introduced it; otherwise
    report it.
  - Evidence goes to `C:\Users\rwsmy\clearwater-review-evidence\wp1.2r\r1\` with md5s.
  - Ledger: `docs/proofs/wp1.2r-ledger.md`, with the depth column left to the dispatcher.
- **Envelope:**
  - Windows 11, Python 3.12 under uv, this machine (RTX 4070 Laptop 8 GB, driver 610.62).
  - One image at a time, short side above 128 px at the default parameters, up to a 48 MP
    photo or a 5.3K frame.
  - Display-encoded 8/16-bit input in [0, 1].
  - CPU (NumPy) and GPU (CuPy) on synthetic frames.
  - Out of envelope: linear or HDR input, video, multi-GPU, the product's fallback policy, and
    speed.
- **Reviewer B:** run afterwards by the orchestrator at its own seat on the merge candidate.
  It is not your job.

## Return (your FINAL message, under about 50 lines)

- the head and a per-commit list;
- each of M1, M2, M3, m5 and m7: what changed, and the test that covers it, shown failing on the
  pre-fix code where that applies;
- the M3 site table: site, accumulator dtype, cast point, and the GPU path;
- **`git diff --stat <base>..HEAD -- tests/test_prototype_pipeline.py tests/test_prototype_backend.py`
  together with a statement that the diff is additions only**, with no existing line changed
  (CHARC addition (ii));
- the gate lines (`-m gpu` count; skips 0);
- round 1's result with its assertions;
- the locks.

STOP for:
- any change to the pipeline's arithmetic or defaults;
- an M3 site whose result reaches image data uncast;
- a needed edit to an existing test;
- any dependency change.

**Working rules:**
- Commit by pathspec with conventional messages (`fix(wp1.2r): ...`) and the
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` footer.
- Never use a bare `cd`.
- Never post to a mailbox.
