# WP1.2 Part B -- cell ledger (Reviewer A loop, verification loop, timed windows)

Brief `docs/briefs/wp1.2b-brief.md` (FINAL, main `f7e4cac`). Worktree `.worktrees/wp1.2b`, branch
`wp1.2b`, base `f7e4cac`. Cell model: Claude Opus 5.5. Reviewer A: Codex over WSL, codex-cli
0.162.1, per call `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only
--skip-git-repo-check`, STRONG tier. Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp1.2b\rN\`
(prompt, diff, transcript, adjudication; md5s below). Staging files lived in the session
scratchpad under `wp12b-` names, never in the worktree.

## Bring-up probe

`probe.txt`: banner `gpt-5.6-sol` / `high` / `read-only`, 1 `^ succeeded in`, VERDICT `PROBE_OK`.

## Cumulative round ledger

| Round | Head reviewed | Verdict (anchored) | Critical | Major | Minor | In / out of envelope | NEW / REOPENED | Valid / rejected / banked | Reverts | Fixes changed | Assertions | Depth (dispatcher) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `3e62149` | NEW_CRITICAL_MAJOR_FOUND | 0 | 8 | 0 | 7 / 1 | 8 / 0 | 7 valid (F1 sequencing), 1 out-of-envelope fixed by refusal | 0 | product + tests (`80b5b43`, `e13aaae`) | banner ok; `^ERROR` 0; `ERROR codex_core` 0; footer 1; succeeded 19 | -- |
| 2 | `e13aaae` | NEW_CRITICAL_MAJOR_FOUND | 0 | 4 | 2 | 6 / 0 | 6 / 0 | 5 valid, 1 banked (R2-3, pre-existing `fedb8c9`) | 0 | product + tests (`3d871db`, `e1f47d6`) | banner ok; 0; 0; 1; 15 | -- |
| 3 | `e1f47d6` | NEW_CRITICAL_MAJOR_FOUND | 0 | 1 | 2 | 3 / 0 | 3 / 0 | 2 valid minors; the major REJECTED with an executed reproduction | 0 | product (one line moved, a clamp, spool lifetime) + tests (`b163ba9`, `1df3de0`) | banner ok; 0; 0; 1; 33 | -- |

Round 3 has zero valid new blocking findings: the loop CONVERGED on the code at round 3
(ROUND_TERMINATION); its minors were fixed in that round's cleanup. A further round reviews the
report once the timed windows have produced it. The `docs/proofs` hits of every round are the
prompt's own prohibition, the brief's text, and a WSL `git status` file listing (CRLF phantom
churn): no proofs content was read in any round.

### Round 1 findings (adjudication-r1.md)

F1 report absent (sequencing; closed by the report). F2 first wait counted from before the
bracket (fixed: `_bracketed`). F3 single `write()` per frame (fixed: `write_frame` loops; short-
and zero-write tests). F4 unbounded waits on a stalled process (fixed: stall timeouts, thread
release; stalled-decoder, stalled-encoder and core-failure tests). F5 record provenance unchecked
(fixed: STAGED, proxy 540, smoother, exact statistic names). F6 real-frame records anywhere
(fixed: confined to `<working>/wp1.2b`). F7 window times and resident conditions (fixed). F8
OUT-OF-ENVELOPE rotation/SAR (rotation already refused by `lookcheck.frames.probe_stream`;
non-square SAR now refused).

### Round 2 findings (adjudication-r2.md)

R2-1 memory omitted FFmpeg children and NVENC (fixed: process-tree RSS and device-wide CUDA used
memory sampled every 50 ms). R2-2 three frames alive after the core (fixed: two output slots;
EXECUTED control with the slot disabled fails `assert 5 == 2`). R2-3 synthetic `--out` free
(BANKED: since `fedb8c9`, WP1.2A; the unowned Part A tests depend on it; Part B writes no
synthetic record). R2-4 pass-through is not encode-only (fixed: `spool` + `encode_only`, bench
`--mode encode-only`). R2-5 minor, EOF wait unaccounted (fixed: last hand-off ends the loop;
`residual_s`). R2-6 minor, resident conditions (fixed).

### Round 3 findings (adjudication-r3.md)

R3-1 major, H2D race on the analysis buffer: REJECTED, EXECUTED reproduction (CuPy 14.2.0 stages
host data before `asarray` returns: device held the original values with 0.5 s of work queued,
3 of 3 trials); hardened at zero cost. R3-2 minor, witness of the true last frame (fixed: clamp).
R3-3 minor, spool lifetime (fixed: removed in a `finally`).

### Evidence md5s

```
4ea83f0264ad263bad12b1b84b3a052f r1/adjudication-r1.md
c6ed3233cfce75d9acaa7dad014e942f r1/diff-r1.txt
fcf996278118d5018d7b17dcf525713f r1/probe-prompt.md
e9f61c663b6433f22702398435014666 r1/probe.txt
b6604b767be4a7f247f9bb83b91684b8 r1/review-prompt-r1.md
0edf5c2226330ab569e52c050044d88b r1/review-r1.txt
6976d15437177c287cbf2159e9e5899c r2/adjudication-r2.md
db7c148bae40bbe5b763d2ea513ffeaa r2/control-slots-disabled.txt
040c23b62c75f023a5d313fae14c9469 r2/diff-r2.txt
7bd4e0d1cdc90012fd8f158e8e47665c r2/review-prompt-r2.md
759b09555214e1003e4fe4d17aa34313 r2/review-r2.txt
d9279815878013bcc0fa9649187c2e4d r2/wp12b_control_slots.py
14996b78b565beab61ea952998640dd2 r3/adjudication-r3.md
bc39867ccbed6a4759264afbd0043ac2 r3/diff-r3.txt
c4f84b48b827ea4c46ee2162f27169ed r3/review-prompt-r3.md
6d3677cb3b2e1fcb8a7c35add3cdbf31 r3/review-r3.txt
```

## Own verification loop (suspected -> confirmed / rejected -> fixed)

| Item | Status | Evidence / fix |
|---|---|---|
| Raw pipe throughput | CONFIRMED (a result, not a defect) | decode-only through the Python pipe 57-58 ms per 4K rgb24 frame vs 12.4 ms decoding to NUL; FFmpeg writes 32 KB per write (45,600 reads of at most 32,768 bytes for 60 frames; `-avioflags direct` no change); a Python child writing 1 MB / 25 MB chunks reaches 4.4 / 6.0 GB/s (5.6 / 4.2 ms per frame). Measured, not tuned (brief) |
| Output primaries/transfer lost (REQUIRED DIFFERENT on GX011628 dev run) | CONFIRMED, FIXED | raw frames carry no primaries/trc; `setparams` on the encode chain; dev compare then REQUIRED SAME |
| Analysis proxy on the 320x240 test clip | CONFIRMED (test premise), FIXED | test clip 960x540 (proxy factor 1) |
| Test clip 59 frames (`-shortest`) | CONFIRMED, FIXED | `-shortest` dropped |
| Neutral export identity | VERIFIED | the bytes fed to the encoder equal the decoded source frames (test); PSNR Y 49.2 / U 43.5 / V 41.4 dB; the same output shifted one frame: Y 23.7 dB (floor 40 dB stated in the test) |
| StagedStream equals analyse_staged | VERIFIED | bit-for-bit over 3 smoothers x 2 methods (24 frames), and the planted radius-1 control differs |
| Frame size off by one | VERIFIED | `PartialFrameError` for +-1 byte; `frame size mismatch` for a planted `frame_bytes`; `FrameCountError` for a source one frame short |

## Timed windows

| Window | Local time (HST) | Head | Runs | Status |
|---|---|---|---|---|
| W1 (claim 2, 4K mode, GX011627) | 2026-10-18 17:26:49-17:32:03 | `1df3de0` (clean) | GPU ancuti2018 N=60, GPU c3 N=60, CPU ancuti2018 N=10 | DISCARDED: sibling-harness load. Records kept as `work/wp1.2b/core/DISCARDED-sibling-harness-load-*.json.txt` |

W1 stray readings (from the records): before the GPU ancuti2018 loop, 16 `python.exe` processes
at 45-80 % of a logical CPU each, `MsMpEng.exe` 90 %, `WmiPrvSE.exe` 63 %, `SearchIndexer.exe` 49 %;
after it, 17 `python.exe` at 14-79 %, `MsMpEng.exe` 108 %; before c3, 15 `python.exe` at 17-94 %,
`MsMpEng.exe` 172 %; after c3 and around the CPU run, `MsMpEng.exe` 100-102 %, `WmiPrvSE.exe` 84-98 %.
GPU ancuti2018 median 0.4989 s, drift +10.0 % (Part A synthetic: 0.389 s); c3 0.6254 s.
At 17:33 the batch of python processes was gone. Resident processes seen: the comms UIs of the
three harnesses (8765 swing-trading, 8770 coa-chess at 46 % of a CPU, 8775 clearwater), `swing
web`, and live Claude sessions of the swing-trading and coa-chess harnesses (orchestrators,
directors). Pre-window check at 17:24-17:26: `WmiPrvSE.exe` 87-91 % of a CPU throughout (running
since 11:12), transient `python.exe` up to 81 %.

## Brief amendment (orchestrator, CHARC ruling d40217a81696cc03), received 2026-10-18 ~17:34 HST

Reached the cell while STOPPED after the discarded W1 (claim 2), before any re-run. Binding before
claim 3: (1) the long full clip of claim 3 is GX011625 (Snorkel, 498.43 s, 14,938 frames), not
GX011600; GX011627 stays the short clip; GX011625 also carries claim 4 (one clip, both legs, said
in the report); claim 5's memory figures come from the GX011625 run; GX011600 only where file
length does not matter, if at all. (2) 4-hour cap: every exclusive window's estimate is recorded
here before it opens; a run estimated above 4 h is a STOP.

## Window estimates (recorded before any window opens; provisional per-frame figures)

Per-frame figures until the clean claim-2 re-run fixes them: core 0.389 s (Part A synthetic) to
0.499 s (discarded W1); end to end about 0.50 s (GX011628 development run); analysis about
0.065-0.070 s (development runs, pipe-bound).

| Window | Runs | Estimate | Under the 4 h cap |
|---|---|---|---|
| W1 re-run (claim 2) | GX011627 GPU x2 (N=60), CPU (N=10); compilation GPU x2, CPU (N=10) | about 8 min | yes |
| W2 (claim 4) | GX011625 analysis sw, then hw (14,938 frames each) | 14,938 x 0.07 s = 17 min each, 35 min | yes |
| W3 | GX011627 analysis (681 frames) | under 1 min | yes |
| W4 (claim 3 short + split) | GX011627 export, resident export, decode-only, encode-only (16 GB spool), passthrough | about 15 min | yes |
| W5 (claim 3 long, claim 5) | GX011625 export | 14,938 x 0.389-0.50 s = 1.6-2.1 h, then compare about 5 min | yes |

The GX011625 analysis of W2 (software decode) is the statistics record W5 applies. The W5 estimate
is fixed again from the clean claim-2 median before W5 opens.

## Superseded: GX011600 estimate (the amendment moves the long clip to GX011625)

Not yet fixed: it needs claim 2's clean 4K GPU `ancuti2018` median. Provisional, for scheduling
only: Part A synthetic 0.389 s x 31,364 frames = 3.39 h; the contaminated W1 0.499 s x 31,364 =
4.35 h; the development export of GX011628 (2026-10-18, not a timed window) ran at 0.498 s per
frame end to end, which would be 4.34 h.

## STOP (2026-10-18 17:33 HST)

Premise mismatch: the declared envelope has "the machine otherwise idle", but sessions of the
sibling harnesses on this laptop (swing-trading, coa-chess) run heavy batches outside the
Clearwater orchestrator's scheduling (W1, above), and `WmiPrvSE.exe` holds about one logical CPU.
The timed windows are halted; nothing after W1 has run. Fresh reading 17:35 HST (after the
amendment): load 13-20 % of all CPUs, `MsMpEng.exe` 104-107 % of a CPU in three samples over
30 s, `WmiPrvSE.exe` 20-87 %. Still stopped pending the ruling on machine load.
