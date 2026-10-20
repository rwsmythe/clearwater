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
| W1 `explore` (gate 60 s, 8 stray checks, 2 probes, 6 single runs) | timed window | 8 min | | |
| W2 `pipes-a` (gate, 8 stray checks, 2 probes, n x 3, a x 3) | timed window | 7 min | | |
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

## Reviewer A rounds (cumulative)

| Round | Transport / CLI | Critical | Major | Minor | In-envelope / out | NEW / REOPENED | Reverts | Fixes: product / test-only | Depth (dispatcher) | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
