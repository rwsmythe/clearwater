# WP1.2 Part B — Accept record (real-footage speed and memory)

**Accepted 2026-10-19 by the orchestrator** (generation 2, session
`clearwater-orchestrator-20261018-1442`). Gate per `docs/review-gate-clearwater.md` Part 2. Tier
STRONG. Rulings:
- CHARC `d40217a81696cc03`: GX011625 is the long clip; 4 h cap per window.
- CHARC `f2d35c83ac139a14`: the contamination rule and conditions.
- The owner's best-effort release, relayed by CHARC `d4188563639bc453`, on decision request
  `e2c53e6a`.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp1.2b-brief.md` (FINAL `f7e4cac`, amended `ead378c`); remediation `docs/briefs/wp1.2b-remediation-brief.md` (`f1d2be7`). Spec v0.5.2 at issue; v0.5.3 changes nothing measured here. |
| Base SHA | `f7e4cac` |
| Author heads | Return `2fa0ac8`; after the remediation `7ea9eb6` (`wp12b-cell`, implementer-opus-high). The second head read twice across a turn boundary (20:06:27Z, 20:07:37Z), unchanged and clean. |
| Cell depth | At dispatch: fresh. **At retirement: 931,878 tokens, 428 turns (PAST-CAP).** DEPTH BREACH, the orchestrator's: see below. |
| Merged head | `2dd06cf` (`wp1.2b-mc` = `7ea9eb6` rebased onto main `5226c55`; main fast-forwarded). |
| Byte identity | `git patch-id --stable` = `3c25c6566d9d57fe4f8d42499f6399963bb3075b` on `f7e4cac..7ea9eb6`, on the B #2 candidate `5226c55..2dd06cf`, and on main `5226c55..2dd06cf`. Nothing landed on main during B #2, so the merged tree IS the reviewed tree. (Corrected after CHARC QA `cb61a4e41f625d73`: the first version of this line quoted `4781bbe0`, which is not the patch-id of any of these ranges; re-computed at this seat as `git diff <range> \| git patch-id --stable`. The identity claim was unaffected.) |
| Reviewer A | STRONG (gpt-5.6-sol / high), WSL, codex-cli 0.162.1. Code R1-R3 converged; report R4-R5, terminating at the five-round gate. Remediation: rem1 not counted (a transport ERROR line), rem2 (1 major fixed, 2 out-of-envelope minors banked), rem3 `NO_NEW_CRITICAL_MAJOR`. Ledger `docs/proofs/wp1.2b-ledger.md`; evidence `clearwater-review-evidence\wp1.2b\r1-r5`, `rem1-rem3`. |
| Reviewer B | Seat pass #1 on `6e538d7`: BLOCKING, 4 major and 5 minor, all valid, one remediation. Seat pass #2 (final) on `2dd06cf`: `NO_NEW_CRITICAL_MAJOR`, 6 minor and 1 advisory, banked (DR-28) and given errata. |
| Owned files | The brief's five exactly (`git diff --stat`): `tools/prototype/clip.py` (new), `tools/prototype/bench.py`, `tests/test_prototype_clip.py`, the report, the ledger. No change to `pipeline.py`, `params.py`, `backend.py` or `pyproject.toml`. |

## The windows (best effort)

Every timed figure was measured on a SHARED, NON-IDLE laptop:
- other projects' 16-worker test batches every 15-20 min;
- Defender at about one logical CPU;
- WmiPrvSE at about 0.9 of one.

The owner released the block best effort: "I am not concerned about contaminated figures as
the actual program itself will run in a non-ideal state. Best effort is fine." How the report
handles that:
- It opens with the caveat. The figures are an UPPER BOUND on the cost on an idle machine.
- Contaminated windows are labelled, and their figures are given as per-frame min / median /
  max.
- Every window carries the SM clocks, P-state, power draw, throttle reasons and the power
  scheme.
- No sampler uses CIM or WMI (`2c2856a`).
- The amendment was acknowledged at `3c5f73b`, and GX011600 was never opened.
- Every window's estimate was recorded before it opened. W5 was estimated at 2.0 h and ran
  3.48 h, under the 4 h cap.

The remediation re-ran NO timed window and rewrote no window record.

## Reviewer B #1 (seat), on candidate `6e538d7`

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp1.2b\reviewB\` (`md5s.txt` there). Assertions:
- banner gpt-5.6-sol / high, probe READY 13:49Z;
- `^ERROR` 0; footer 1; 40 `succeeded in`;
- an anchored `VERDICT: NEW_CRITICAL_MAJOR_FOUND`;
- withheld access none: a WSL `git status --short` NAME listing of the tree, and footage paths
  only inside record contents (FFmpeg command lines).

Transcript md5 `4f6ed9f6ffe6188c3e544b65ad0ee04f`.

| # | Finding | Disposition (remediation) |
|---|---|---|
| 1 | MAJOR: W3b labelled CLEAN with a 53 % python.exe in its close check (confirmed at my seat) | FIXED: CONTAMINATED, propagated to claim 4 and candidate #6 |
| 2 | MAJOR: contaminated rows given as points | FIXED: per-frame min / median / max by `work/wp1.2b/remediation/per_frame_spread.py` |
| 3 | MAJOR: the content witness is decode-side only | FIXED: the wording, plus an untimed output witness on both exports (below) |
| 4 | MAJOR: a partial MP4 left at the final name; `-y` overwrite | FIXED: `.partial.mp4`, rename on success after the bracket, no overwrite, tested |
| 5 | MINOR: provenance omits the decode command, time_base, frame_rate and bit depth | FIXED, with a refusal test each |
| 6 | MINOR: the bracket's end mis-stated | FIXED (wording; which child exited first was not recorded) |
| 7 | MINOR: the stderr temp file in the OS temp folder | FIXED (a pipe, tested) |
| 8 | MINOR: the sampler cadence mis-stated | FIXED (62-81 ms from the records) |
| 9 | MINOR: two conclusions not established | FIXED (a HYPOTHESIS and an ESTIMATE, with the arithmetic corrected) |

## The output witness: criterion history and adjudication

The witness compares output frame i with `correct(source i, statistics_i)` through the export's
conversions, untimed, at 24 indices per export including the first and last. It required:
- own_i at or above a floor;
- own_i STRICTLY better than the score against the expected i-1 and i+1 (the order rule).

The criterion changed four times. Each change was set before the next re-scoring, and every row
keeps all four verdicts:
1. **28 dB absolute** (the cell's first, based on WP1.5's identity re-encode). Frame 30 of
   GX011627 failed at 27.79 dB. The encoder's own loss on that frame is 28.76 dB, by
   reproduction.
2. **A 3-frame relative reference** (my first ruling). Unrepresentative: the export is GOP 250
   with B and P frames, and the reference coded i next to a fresh I-frame.
3. **A GOP-start reference through i+1** (my second ruling).
4. **(ADOPTED, the cell's extension, raised by its rem2 Reviewer A)** The GOP-start reference
   through the next I/P anchor after i, because a B-frame is predicted from that anchor. On
   GX011627 frame 30 it reproduces the export exactly (`export_vs_anchor_reference_db = inf`).
   The thresholds did not change: ref - 2.0 dB, a 20 dB sanity floor, the strict order.

**Ruling on (4): ACCEPTED.** It models the encoder's real prediction structure; B #2 judged it
"a principled correction for B-frame prediction -- not a newly fitted threshold".

**Results under (4):**
- GX011625: 24 of 24.
- GX011627: 23 of 24.
- Order is correct on all 48 rows, and the reference picture types match on all 48.

**Frame 503 (GX011627, a B-frame), adjudicated NOT BLOCKING at the gate.** Own 35.39 dB against
a reference of 38.74 dB (-3.35 dB against the 2 dB margin). The grounds:
- the order rule holds: neighbours score 22.2 / 22.3 dB, against own 35.4;
- the 20 dB sanity floor holds by 15 dB;
- the container is SAME by `compare.py`;
- the reference restarts the encoder at frame 500, while the export carried 500 frames of
  rate-control state. That is stated as a hypothesis; in the first GOP, where both start fresh,
  the scores agree.

Part B's deliverable is timing and memory evidence. `clip.py` is a prototype draft whose output
ships nowhere, so nothing irreversible rides on the frame. A product-grade full-coverage output
verification is a forward requirement for the export engine (DR-28).

## Reviewer B #2 (seat, final), on candidate `2dd06cf`

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp1.2b\reviewB2\` (`md5s.txt` there). The
prompt carries the first-pass findings and the criterion history. Assertions:
- banner gpt-5.6-sol / high, probe READY 20:07Z;
- `^ERROR` 0; footer 1; 42 `succeeded in`;
- an anchored `VERDICT: NO_NEW_CRITICAL_MAJOR`;
- withheld access none: its file listings exclude `docs/proofs` explicitly, and the only
  footage hit is the prompt's own withholding line.

Transcript md5 `89f98c2cef6b27e1251b4664ef135ab4`.

B #2 confirms every first-pass finding closed end to end. On finding 4, the overwrite defect is
closed; its residual is item 3 below.

| # | Finding | Disposition |
|---|---|---|
| 1 | MINOR: the witness samples 24 indices; a localised swap, drop-and-duplicate or wrong-statistics interval between them is invisible; there is no wrong-matrix/range or ±1-index control; the docstring's "fails" is categorical | BANKED, DR-28(1). The report already says 24 indices; erratum on the scope |
| 2 | MINOR: "Reference = export bit for bit" for nine plus one rows; equal PSNR does not prove pixel equality, and only frame 30 is shown equal | ERRATUM at the gate (report section 6) |
| 3 | MINOR: a stale `.partial.mp4` is left when an export is refused at start because the final exists | BANKED, DR-28(2) |
| 4 | MINOR: "hardware decode saves 7 %" states a cause; the measured fact is that the CUDA run was 7.4 % faster under its conditions. "Smoothing 52-61 s per clip" is GX011625's figure | ERRATUM at the gate (report section 7) |
| 5 | MINOR: provenance ignores the stored `proxy.method` | BANKED, DR-28(3) |
| 6 | MINOR: while waiting on the decoder, the main loop does not poll the encoder or `writer.error`; an encoder failure surfaces as a decoder stall | BANKED, DR-28(4) |
| 7 | ADVISORY, out of envelope: `resolve_clip` accepts a path outside the footage folder without the stem lookup | BANKED, DR-28(5) |

## Verification QA (orchestrator seat)

**Gate checks on the B #1 candidate `6e538d7`:**

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 102 files already formatted
uv run mypy                    -> Success: no issues found in 19 source files
uv run pytest -q -rs           -> 672 passed, 1 warning (0 skipped)
uv run pytest -q -m gpu        -> 30 passed, 642 deselected
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

**Gate checks on the final candidate `2dd06cf`:**

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 103 files already formatted
uv run mypy                    -> Success: no issues found in 19 source files
uv run pytest -q -rs           -> 690 passed, 1 warning (0 skipped)
uv run pytest -q -m gpu        -> 34 passed, 656 deselected
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

**Gate checks on main `2dd06cf`** after `uv sync`: ruff check "All checks passed!"; ruff format
"103 files already formatted"; mypy "Success: no issues found in 19 source files". The pytest,
gpu and harness legs were NOT completed: Claude Code stopped the background re-gate for
system-wide low memory during the pytest leg (not a test failure; no result was produced). Main
is the gated candidate commit itself (`git merge --ff-only`; `main` = `wp1.2b-mc` = `2dd06cf`),
so the candidate's green pytest / gpu / harness lines above apply to this tree. The full re-gate
on main is OWED and runs when the owner clears it or at the next accept, whichever comes first.

**Report read at my seat:**
- the caveat opens the report;
- the windows table matches the cell's return;
- the photo leg is PENDING (D102);
- the claim-7 candidates are listed, not tried;
- the 32 KB pipe finding is recorded as a WP2.1 transport candidate.

The W3b stray reading was confirmed in its record:
`core/W3b-probes/bench-gpu-GX011627-ancuti2018-20261018-223214.json`,
`ambient.stray_processes_after`, python.exe PID 17192 at 53.0 %.

## Headline results (for WP1.6; upper bound, shared laptop)

N6 is 3.3 min/min, which is 0.1101 s per 4K frame at 29.97 fps.

| Measure | Result |
|---|---|
| Core, 4K GPU, real frames | ancuti2018 0.395 s (3.6x); c3 0.639 s (5.8x); within 2 % of Part A's synthetic |
| Export GX011627, production | 0.4856 s/frame, 14.55 min/min (4.41x; stray-clean row) |
| Export GX011627, device-resident | 3.25x (contaminated) |
| Export GX011625, full clip | 0.8386 s/frame, 25.13 min/min (7.62x; contaminated, thermal slowdown) |
| Analysis GX011625 | 3.57 / 3.30 min/min, software / CUDA decode (contaminated); pipe-bound |
| Memory | Process tree 3,682 MiB against 16 GB; device 2,860 MiB against 8,188 MiB; photo leg PENDING |
| Conclusion | N6 is not met at 4K on this laptop. No listed candidate reaches it; the combined estimate is about 2.3x. Gate 1 needs CHARC's options or an owner N6 decision. |

## Process deviations (the orchestrator's)

- **Cell depth not read (owner catch, 2026-10-19).** I never read `scripts/cell_depth.py` at the
  return, at the three STOPs or before the remediation. I ordered a nine-finding remediation
  into a cell already far past the re-seat line (about 250K), and then sent it two rulings. The
  cell was at 858K when the owner caught it, and it retired at 932K. The remediation should have
  gone to a fresh cell built from the ledger.
- **The witness criterion changed under my rulings.** My first ruling (the 3-frame reference)
  was the wrong model of the encoder, and it cost one STOP cycle. The record keeps every
  verdict.
- **A bare `cd` at my seat** moved the session's directory into the `-mc` worktree, and later
  into a records folder, while the cell was idle. Each was reset at once.

## Follow-ons

| Item | Disposition |
|---|---|
| B #2 findings 1, 3, 5, 6, 7 | BANKED, DR-28 (owner: the export engine, WP3.14 / WP3.9 / WP3.10, which reads `clip.py` as its first draft) |
| B #2 findings 2, 4 | Errata in the report at the gate |
| The 32 KB raw-pipe transport | A WP2.1 transport candidate (claim 7 #6) |
| The photo half of claim 5 | PENDING: queued for the first photo in the inventory (D102) |
| Gate 1 (N6) and Gate 2 (N4) | CHARC at WP1.6, on these figures with the shared-laptop caveat |

Branches kept:
- `wp1.2b` (`7ea9eb6`, the author head);
- `wp1.2b-b1` (`6e538d7`, B #1's candidate).

B #2's candidate `2dd06cf` is main.
