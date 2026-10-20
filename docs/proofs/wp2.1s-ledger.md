# WP2.1S ledger -- transport and photo I/O spike

Cell: implementer-opus-high, worktree `.worktrees/wp2.1s`, branch `wp2.1s`, base `aa1f5f0`.
Brief: `docs/briefs/wp2.1s-brief.md` (FINAL). Records under `C:\Users\rwsmy\clearwater\work\wp2.1s\`.

## Machine time (transport leg; cap 2 h)

Idle gate: Part B's `work/wp1.2b/gate/idle_gate.ps1` copied to `work/wp2.1s/idle_gate.ps1`,
md5 `cf3a33c0ab7da54bf7a8a4386f632e90` (identical to the source).

| Step | Kind | Estimate | Actual | Cumulative actual |
|---|---|---|---|---|
| Exploration (knob write sizes, 10-60 frames; PyAV conversion check, 5 frames) | untimed dev | -- | ~3 min | ~3 min |
| `reference` (ffprobe frame pts + row a per-frame SHA-256) | untimed | -- | 1.4 min | ~4.4 min |
| Dev runs (6 rows x 60 frames) | untimed dev | -- | ~1 min | ~5.4 min |
| `identity` (17 rows, full clip, every frame hashed; a-ad10 lockstep diff) | untimed | -- | 11.2 min | ~16.6 min |
| W1 `explore` (gate 60 s, 8 stray checks, 2 probes, 6 single runs) | timed window | 8 min | 5.6 min | ~22.2 min |
| W2 `pipes-a` (gate, 8 stray checks, 2 probes, n x 3, a x 3) | timed window | 7 min | 5.5 min | ~27.7 min |
| Attribution probe (row a, 120 frames, 0/2/4/0 busy loops; `work/wp2.1s/attribution.py`) | untimed, outside windows | 1 min | ~1 min | ~28.7 min |
| W3 `pipes-apts` (gate, 5 stray checks, 2 probes, a+pts x 3) | timed window | 5.5 min | | |
| W4 `pipes-b` (gate, 14 stray checks, 2 probes, b/b+pts/b-cuda/b-cuda+pts x 3) | timed window | 6.5 min | | |
| W5 `others-s` (gate, 11 stray checks, 2 probes, s/s+pts/c x 3) | timed window | 8.5 min | | |
| W6 `others-c` (gate, 11 stray checks, 2 probes, c-auto/c-cuda/c-cuda-auto x 3) | timed window | 8 min | | |
| Re-runs (one per window at most) | timed window | up to 43.5 min | | |

Each window is kept under the 10-minute tool call (one foreground call per window).
Estimated total with every re-run: ~16.6 + 43.5 + 43.5 = ~104 min, under the 120 min cap.

## Windows

| Window | Local | Gate | Probes open / close (s/frame) | Drift | Strays | Verdict |
|---|---|---|---|---|---|---|
| W1 explore | 2026-10-20 00:26-00:31 | median CPU 4.4 %, GPU 0 %, open | 0.0567 / 0.0574 | +1.2 % | none (WmiPrvSE 36.9 % is system) | clean |
| W2 pipes-a | 2026-10-20 00:32-00:37 | median CPU 6.4 %, GPU 0 %, open | 0.0570 / 0.0594 | +4.1 % | none (WmiPrvSE 23-27 %) | clean |

STOP (brief: row a more than 25 % off Part B's 93.6 ms/frame). Row a 55.2 / 55.9 / 56.0 ms
(W2) and 54.7-54.9 ms for the three knob variants (W1): -41 %, re-run done (W2 is the re-run of
W1's figure). Calibration n (decode + conversion to the null muxer) 13.2-13.9 ms against Part
B's 16.2 ms to NUL (-17 %). Attribution probe (120 frames): 0 / 2 / 4 / 0 busy loops give 57.1 /
62.3 / 65.3 / 57.4 ms: contention slows the 32 KB pipe (+9 % / +14 %) but does not reach
93.6 ms. Part B's transport record was taken with WmiPrvSE 60-73 % and vmmemWSL 85 % in its
stray checks (report section 2). Cause partly attributed only; yielded for a ruling.

## Reviewer A rounds (cumulative)

| Round | Transport / CLI | Critical | Major | Minor | In-envelope / out | NEW / REOPENED | Reverts | Fixes: product / test-only | Depth (dispatcher) | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
