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

## Ruling f2d35c83 (CHARC, received about 17:40 HST): proceed under conditions

Adopted as written: an idle gate before each window; samplers without CIM or WMI; probes
opening and closing each window; contaminated means probe drift > 5 % or a non-system process
above 25 % of a logical CPU, sustained; one re-run; W5 only if W1-W4 close clean; a window
contaminated twice is a STOP.

**Samplers (condition 2), all without CIM/WMI.** Before W1 two record helpers DID reach WMI,
once per record and after the timed loop (neither was a sampler):
- `_cpu_brand` used py-cpuinfo, which runs `wmic` in a child Python on Windows;
- `_machine` used `platform.platform()`, which is Python 3.12's `_wmi_query`.
Both were replaced in `2c2856a` (`PROCESSOR_IDENTIFIER`, `sys.getwindowsversion()`).

The samplers now are:
- the stray check, `bench.stray_processes`: psutil `cpu_percent` over a 10 s sample. psutil uses
  the native process APIs, not WMI. MsMpEng.exe and WmiPrvSE.exe are always listed.
- the RSS sampler: psutil `memory_info` every 50 ms, children listed every 2 s.
- device memory: the CUDA runtime's `memGetInfo`.
- card state: `nvidia-smi` every 60 s.
- the idle gate, `work/wp1.2b/gate/idle_gate.ps1`:
  `Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 10 -MaxSamples 1`, taken 6
  times, plus `nvidia-smi --query-gpu=utilization.gpu`, plus two `Get-Process` snapshots. The
  gate's records are in `work/wp1.2b/gate/gate.jsonl`.

A Python 3.12 process on Windows may still issue one WMI query when a library first calls
`platform.uname()` at import. That is a one-off per process, not a sampler. WmiPrvSE.exe
(PID 14516) has run at 20-91 % of a CPU since 11:12, before this package's first run.

**Idle gates:**

| Start | Median CPU | GPU | Result |
|---|---|---|---|
| 17:41:00 | 77.7 % | 0 % | FAILED: a swing-trading pytest-xdist run, 16 workers at 29-50 % each |
| 17:52:30 | 16.9 % | 0 % | OPEN, so W1a ran |
| 18:08:24 | 18.6 % | 0 % | OPEN, so W1b ran |

The 17:41 run was `python -m pytest -m "not slow" -q -p no:cacheprovider` in
`C:\Users\rwsmy\swing-trading\.worktrees\d79-exec`, workers
`python -u -c import sys;exec(eval(...))`, started 17:39:51 under claude.exe PID 9632, the
`swing-orchestrator-20261018-1515` session.

## W1 (claim 2) -- contaminated twice: STOP (condition 4)

Window estimate (recorded above): about 8 min, under the cap. Head `2c2856a`, clean tree. The
records are in `work/wp1.2b/core/W1a-contaminated/` and `W1b-contaminated/`.

| | W1a 17:54-18:07 | W1b 18:10-18:21 |
|---|---|---|
| probe open (GX011627 GPU ancuti2018 N=12) | 0.4167 s | 0.4208 s |
| 4K GPU ancuti2018 N=60 (the baseline) | 0.4183 s, p95 0.4434, drift +3.6 % | 0.4558 s, p95 0.5008, drift +6.9 % |
| probe close | 0.4140 s (-1.0 %) | 0.4993 s (**+9.5 %**) |
| 4K GPU c3 N=60 | 0.8477 s (**strays**: 15-17 python.exe at 44-77 % before and after) | 0.7077 s (clean strays) |
| 4K CPU ancuti2018 N=10 | 9.992 s, p95 15.71 (**strays** before) | 8.808 s, p95 9.498 (clean) |
| 1080p60 GPU ancuti2018 N=60 | 0.1396 s (clean) | 0.0993 s (clean) |
| 1080p60 GPU c3 N=60 | 0.1223 s (clean) | 0.1247 s, drift -19.7 % (**strays** before: python.exe 93 %, 72 %) |
| 1080p60 CPU ancuti2018 N=10 | 2.037 s (clean) | 1.956 s (clean) |
| verdict | CONTAMINATED (stray checks) | CONTAMINATED (probe +9.5 %; stray checks) |

Per-run conditions (all records): plugged in, battery 80 %, scheme Balanced, overlay Best
performance, MsMpEng.exe 1-279 % of a CPU (about 100 % in most checks), WmiPrvSE.exe 3-91 %.
The 4K frames were GX011627 frames 205-264, pts 205205..264264 at 1/30000, from 30 % of the
clip. The 1080p frames were compilation frames 3236-3295, pts 3239236..3298295 at 1/60000.

The swing-trading test batches are periodic: about 17:27, 17:39, 17:57 and 18:18, each lasting
several minutes, about every 15-20 min. Every window of this block longer than about 10 min will
meet one. Two runs the stray checks call clean still differ by 40 % (1080p GPU ancuti2018
0.1396 vs 0.0993 s), so this machine's figures are not reproducible at present.

STOP at 18:22 HST. W2-W5 have not run. GX011625's W5 estimate is not re-fixed, because there is
no clean W1 median.

Record md5s:
```
9ba1c4cb1f87e9525713d5fe05b177ce W1a/bench-cpu-GX011627-ancuti2018-20261018-180309.json
20d9e7638e8b4177dfe5e155055e89a1 W1a/bench-cpu-compilation-...-ancuti2018-20261018-180636.json
584d8bbe7c019d57fb1e59e90ede97ea W1a/bench-gpu-GX011627-ancuti2018-20261018-175511.json (probe open)
36837388d74d337136e8534a18dce4f9 W1a/bench-gpu-GX011627-ancuti2018-20261018-175711.json
1cce480a7307efd7b6097972a1ca62f3 W1a/bench-gpu-GX011627-ancuti2018-20261018-180740.json (probe close)
c00c194cf4bfb99415962465f1e27cd9 W1a/bench-gpu-GX011627-c3-20261018-180025.json
f8ef6f344be3520442ae62848900dccf W1a/bench-gpu-compilation-...-ancuti2018-20261018-180431.json
6fc8af10bb93479aeffd44bf2678a504 W1a/bench-gpu-compilation-...-c3-20261018-180546.json
445106afabce93511e2005b7bf72b616 W1b/bench-cpu-GX011627-ancuti2018-20261018-181713.json
89fa000871bb15f053162379ac808d41 W1b/bench-cpu-compilation-...-ancuti2018-20261018-182016.json
a083b062fb5c441e909511eac98897fa W1b/bench-gpu-GX011627-ancuti2018-20261018-181051.json (probe open)
a683d37030733548b39c8b9456534dec W1b/bench-gpu-GX011627-ancuti2018-20261018-181243.json
43f7e1d09f60f2359baa1fb440b74ab6 W1b/bench-gpu-GX011627-ancuti2018-20261018-182141.json (probe close)
6a6ec7a59ff2d31d7a3db4f1455307c6 W1b/bench-gpu-GX011627-c3-20261018-181509.json
4303f5e61dcc8c860ce9df6e0849f37f W1b/bench-gpu-compilation-...-ancuti2018-20261018-181819.json
6aedf02ecb6c667e40420d0a0c2ceb8c W1b/bench-gpu-compilation-...-c3-20261018-181929.json
```

## Release, best effort (owner, decision request e2c53e6a, relayed by CHARC d4188563639bc453)

The owner: "I am not concerned about contaminated figures as the actual program itself will run in
a non-ideal state. Best effort is fine." Condition 4 is withdrawn. Each window runs once; a short
window may be re-run once, if the next gate opens within 10 min. The idle gate is advisory.
Contaminated figures are reported as measured spread.

| Window | Gate (median CPU) | Probes (baseline 0.3948 s) | Verdict |
|---|---|---|---|
| W1c, 20:40-20:52 (run of record) | 16.6 % | open 0.3775 (-4.4 %), close 0.4242 (+7.4 %) | contaminated; strays from about 20:47 |
| W1d, 20:55-21:11 (re-run) | 21.2 % | 0.4515 / 0.5167 | contaminated throughout |
| W2, 21:13-22:14 (never re-run) | 99.3 % | in `core/W2-probes` | contaminated (strays before and after both runs) |
| W3, 22:16-22:20 | 74.4 % | 0.4241 / 0.6178 | contaminated |
| W3b, 22:29-22:32 (re-run) | 23.8 % | 0.3801 (-3.7 %) / 0.4073 (+3.2 %) | CLEAN |
| W4, 22:33-23:00 | 14.5 % | 0.3754 / 0.4853 (+23 %) | contaminated from 22:42 on; the production export row (22:34-22:40) had clean strays |
| W4 re-run | 78.9 % at 23:00, 72.3 % at 23:07 | -- | not run: the gate did not open within 10 min |

W5 estimate, re-fixed before it opens (23:09 HST):
- W1c's median times the frames: 0.3948 s x 14,938 = 5,898 s, 1.64 h (core alone).
- W4's clean production export of GX011627: 0.4856 s per frame x 14,938 = 7,254 s, 2.02 h, plus
  the compare (about 5 min).
- Contaminated upper spread, +23 %: about 2.5 h.
- Under the 4 h cap.

W5 applies the GX011625 software-decode analysis of W2
(`bench/GX011625-analysis-ancuti2018-20261018-211458/GX011625-ancuti2018-none-analysis.json`).

## Reviewer A round 4 (code since round 3 + the report)

Head `13a498f`, diff 4562 lines. Banner `gpt-5.6-sol` / `high` / `read-only`; `^ERROR` 0;
`ERROR codex_core` 0; footer 1; `^ succeeded in` 33; VERDICT `NEW_CRITICAL_MAJOR_FOUND`.
Proofs and footage hits: prompt and report echoes; it read only the permitted `work/wp1.2b`
records. It confirmed the main timing, N6 arithmetic, memory, witness and container figures
against the records. 3 major + 2 minor, all in envelope, NEW, VALID, fixed:

| # | Severity | Finding | Fix |
|---|---|---|---|
| R4-1 | major | claim 6 omitted statistics; the saliency rows gave means only | complete appendix generated from the records, absolute differences beside relative; the reading distinguishes channel means and gains from Lab saliency |
| R4-2 | major | transport figures had no record or conditions; battery shown as 80 % only | recorded measurement `work/wp1.2b/transport/transport-20261019.json` with conditions (decode to NUL 16.2 ms, through the pipe 93.6 ms, child blocks 91.9 / 5.4 / 4.0 ms); battery 80-82 % |
| R4-3 | major | no test proved that the export applies per-frame statistics | test `test_the_export_applies_each_frame_its_own_statistics`; EXECUTED control: with `statistics=supplied` removed the test fails (`assert False`) |
| R4-4 | minor | 61-proxy arithmetic | (3 - 1) x 30 + 1 |
| R4-5 | minor | W3b called an idle indication | reworded: clean under the rule, not idle |

Fixes: report and test (no product code changed in this round).

## Reviewer A round 5 (the revised report) -- terminating round

Head `05d03a0` (diff 4655 lines).
Banner `gpt-5.6-sol` / `high` / `read-only`; `^ERROR` 0; `ERROR codex_core` 0; footer 1;
`^ succeeded in` 29; VERDICT `NEW_CRITICAL_MAJOR_FOUND`. Hits: prompt and report echoes; a footage
path inside a record it read (an echo, no access).

| # | Severity | Finding | Verdict |
|---|---|---|---|
| R5-1 | major | claim 6's proxy statistics lack their own ambient window | REJECTED with the cited constraint. The fill's GATE_CHECKS bind conditions to "a timing or memory figure (plan 4.3)"; the claim-6 values are deterministic statistics of fixed frames and parameters, not timings, and machine load cannot change them. The record still carries head, power and the core loop's conditions. |
| R5-2 | minor | "10 % GPU utilisation" snapshot not in any record | VALID: the sentence is removed (it was a live `nvidia-smi` reading at 01:48, not recorded) |
| R5-3 | minor | "within 1.2e-3" contradicted by 3C at 270 (3.3e-3) | VALID: the reading now gives the maxima per method and size |

Zero valid new blocking findings: the loop terminates at round 5 (ROUND_TERMINATION), and the
minors are fixed in this cleanup. FIVE_ROUND_GATE: round 5 is reached with the loop converged.
Rounds 4 and 5 changed report text and tests only, no product code. Reverts in all rounds: 0.

Evidence md5s, rounds 4 and 5:
```
bcd3f072d8ba57e4d737cc197e55d111 r4/control-statistics-dropped.txt
efaec90301bb4f54b697ed310345cbbe r4/diff-r4.txt
55d32405ca1a655ccf251ee8e80faece r4/review-prompt-r4.md
453d569e5dec8cb925a38e33d805350a r4/review-r4.txt
f0900dded95b3a8a8f642fb96ebaadc3 r5/diff-r5.txt
b7812b58ddbc47a2e3948ed9e04f7c53 r5/review-prompt-r5.md
02c6dc904d8dcff8b13cd4565fb88454 r5/review-r5.txt
```

## Remediation after Reviewer B (brief `docs/briefs/wp1.2b-remediation-brief.md`, f1d2be7)

From `2fa0ac8`. No timed window is re-run, and no window record is rewritten.

**Code and tests done:**
- `a876046`: the output witness (B3b); export to `<stem>.partial.mp4` with rename-on-success, no
  overwrite, the partial removed on failure (B4); provenance over time base, frame rate, bit depth
  and the full decode command (B5); `decode_frames` stderr through a pipe, no temporary file (B7);
  the bracket's end documented as both children reaped (B6, docstring).
- `3b853a0`: tests, including the witness controls (a planted frame swap raises
  `OutputOrderError`; a planted 30-frame statistics shift raises `OutputMismatchError`).
- `f33853f`: the witness finds an output beside its moved run record (W4's folders were moved to
  `bench/W4/` after the run).
- Clip tests: 57 passed.
- Finding 1: no record identifies PID 17192 (python.exe at 53.0 % in W3b's closing-probe stray
  check) as the instrument's own tree; it appears in that one record only. W3b is therefore
  CONTAMINATED (text to follow).

**STOP (brief condition): the output witness FAILED on a real export.** Untimed, 2026-10-19.
- GX011627 W4 production (`bench/W4/GX011627-end-to-end-ancuti2018-20261018-223431/output-witness.json`):
  - 24 frames checked, floor 28.0 dB: 23 pass and frame 30 fails at 27.79 dB.
  - Order is correct on every row (own 27.8-39.7 dB against neighbours 14.1-28.3 dB); no frame is
    misplaced.
  - Scores rise from 28-31 dB over the busy opening to 36-40 dB at the end.
- GX011625 W5 (`bench/GX011625-end-to-end-ancuti2018-20261018-231103/output-witness.json`):
  PASSED, 24 frames, minimum 29.67 dB; own above every neighbour.
- Reproduction (`work/wp1.2b/remediation/frame30_repro.py` and `.json`): the expected frames
  29-31 encoded ALONE through the export's own encode chain (same NVENC settings), then decoded,
  against themselves:

  | Frame | Encoded alone, RGB dB (luma dB) | The export, RGB dB (luma dB) |
  |---|---|---|
  | 29 (an I-frame there) | 35.49 (38.99) | 28.59 (30.23) |
  | 30 | 28.76 (30.15) | 27.79 (29.26) |
  | 31 | 30.81 (32.88) | 28.36 (30.00) |

  The export's frame 30 is within 1.0 dB of the encoder's own loss on that frame. The failure is
  the floor's calibration: 28 dB was set from WP1.5's identity re-encode (Y min 32.27 dB), which
  is easier content than the corrected, sharpened frames. It is not a defect of the measured loop.
- The floor is NOT changed by the cell. A ruling is requested.

Record md5s:
```
2bc525e5ab41c91fb455c44bc211c2a1 *bench/W4/GX011627-end-to-end-ancuti2018-20261018-223431/output-witness.json
c131f6cdc0f68d5f3f9709a299cdee54 *bench/GX011625-end-to-end-ancuti2018-20261018-231103/output-witness.json
03427eb01042b7be9ad160c67a2ce88e *remediation/frame30_repro.json
140b8def6a9ec921c73e72a1076f74aa *remediation/frame30_repro.py
```

### Floor ruling (orchestrator) and second witness STOP

- The ruling replaced the absolute floor BEFORE re-scoring with a per-frame relative rule:
  own_i >= ref_i - 2.0 dB, with ref_i the encoder's own loss on the expected frame from a
  3-frame encode through the export's chain (i not the I-frame; at the ends 0-2 and n-3..n-1).
  It also keeps a 20 dB sanity floor and the strict order rule. Code `d6774a9`.
- Planted controls under the new rule still fail BY NAME (margin not tightened): the swap through
  `OutputOrderError`, the 30-frame statistics shift through `OutputMismatchError`, with no
  row matching.
- **Re-score on the real exports: FAILED the relative rule. STOP (ruling item 6).**
  - GX011627: 18 of 24 frames below ref - 2 dB. Own - ref runs from 0.0 (frame 0) to -5.7 dB.
    Order is correct on every row. The first criterion fails only at frame 30.
  - GX011625: 13 of 24 below. Own - ref runs from +0.3 / 0.0 to -6.0 dB. Order is correct on
    every row. The first criterion PASSES on all 24.
  - Records kept: `output-witness-first-criterion-28dB.json` and
    `output-witness-relative-3frame-reference.json` in each run folder.
- **Reproduction: the 3-frame reference cannot represent the export's coding.**
  - The export's frame types (`work/wp1.2b/remediation/gx011627-out-pict-types.txt`): I-frames
    at 0, 250 and 500 only (GOP 250); 507 B-frames, 171 P-frames.
  - Most checked frames are B-frames deep in a GOP; the 3-frame reference codes frame i right
    after a fresh I-frame. Own - ref is about 0 where the export's frame is at or near a GOP
    start (frame 0; GX011625 frames 7144 and 11040), and down to -6 dB elsewhere.
- **GOP-start reference test** (`remediation/gop_reference_repro.py` and `.json`): GX011627
  frame 30, the expected frames 0-31 encoded through the export chain from the GOP's I-frame.

  | Comparison against expected frame 30 | PSNR |
  |---|---|
  | GOP-start reference | 28.09 dB |
  | 3-frame reference | 28.76 dB |
  | The export | 27.79 dB |

  The export sits within 0.30 dB of the GOP-start reference (export against reference:
  31.79 dB; not bit-identical, as the encoder's rate-control history differs).

md5s:
```
2bc525e5ab41c91fb455c44bc211c2a1 *bench/W4/GX011627-end-to-end-ancuti2018-20261018-223431/output-witness-first-criterion-28dB.json
9dcd914708071c4910bab6a47b9102c7 *bench/W4/GX011627-end-to-end-ancuti2018-20261018-223431/output-witness-relative-3frame-reference.json
c131f6cdc0f68d5f3f9709a299cdee54 *bench/GX011625-end-to-end-ancuti2018-20261018-231103/output-witness-first-criterion-28dB.json
1ec0f82ceaf5a4887c76f8a4fee92141 *bench/GX011625-end-to-end-ancuti2018-20261018-231103/output-witness-relative-3frame-reference.json
9a5fd7fef3cd86f7ccb1eee2de624ce4 *remediation/gop_reference_repro.json
96e6f50897f78006b6a7bcbc3828e269 *remediation/gop_reference_repro.py
ae81007a183cc9ce9de61453f5a92cfe *remediation/gx011627-out-pict-types.txt
```

### Second floor ruling (orchestrator): the GOP-start reference adopted

- Code `ff91f54`. ref_i comes from the expected frames from the export's GOP start (the last
  I-frame at or before i, read from the OUTPUT's picture types with ffprobe) through i+1,
  streamed through `encode_command`. The rule is unchanged: own >= ref - 2.0 dB, sanity 20 dB,
  strict order. Each row keeps all three verdicts.
- Planted controls under the GOP-start rule: both still fail BY NAME (swap ->
  `OutputOrderError`; 30-frame statistics shift -> `OutputMismatchError`). Witness tests: 9 pass.
- Re-score, untimed (`work/wp1.2b/remediation/witness_both.sh`, 04:32-05:54 HST, nothing timed
  alongside):

  | Export | Order | GOP-start rule | own - ref |
  |---|---|---|---|
  | GX011627 | correct on all 24 | 23 of 24; frame 503 (B) at 35.39 dB against ref 38.74 (-3.35 dB) | -3.35 .. +0.05 dB |
  | GX011625 | correct on all 24 | PASSED 24 of 24 | -1.73 .. +0.31 dB |

  Frame 503 is recorded as measured, per the ruling (no stop; the order is correct).
- Text items B1, B2, B3a, B6, B8 and B9 are done in the report. Per-frame spreads come from
  `work/wp1.2b/remediation/per_frame_spread.py` (output `.md` / `.json`). The sampler's actual
  cadence was 62-81 ms (81 ms in W5).

md5s:
```
c5a09dd35f13f829e39fa6f6870cd239 bench/W4/GX011627-end-to-end-ancuti2018-20261018-223431/output-witness.json
b7b82c539f4ac376132498e8904efae0 bench/GX011625-end-to-end-ancuti2018-20261018-231103/output-witness.json
e2c958860cbd3c4454d78a01b0f2d41a remediation/per_frame_spread.json
c2bbde1c4f083688e1d66e301b44f750 remediation/per_frame_spread.md
94f6bac296f7379f942719922d07596a remediation/per_frame_spread.py
da6f116c9831d624afb9789e480f18eb remediation/witness_both.sh
```
