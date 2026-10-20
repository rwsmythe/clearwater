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
| W3 `pipes-apts` (gate, 5 stray checks, 2 probes, a+pts x 3) | timed window | 5.5 min | 4.4 min | ~33.1 min |
| W4 `pipes-b` (gate, 14 stray checks, 2 probes, b/b+pts/b-cuda/b-cuda+pts x 3) | timed window | 6.5 min | 6.5 min | ~39.6 min |
| W5 `others-s` (gate, 11 stray checks, 2 probes, s/s+pts/c x 3) | timed window | 8.5 min | 8.1 min | ~47.7 min |
| W6 `others-c` (gate, 11 stray checks, 2 probes, c-auto/c-cuda/c-cuda-auto x 3) | timed window | 8 min | 8.3 min | ~56.0 min |
| Re-runs (one per window at most) | timed window | up to 43.5 min | none needed (all windows clean) | ~56.0 min |

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
Ruling (orchestrator, 2026-10-20): CONTINUE; this spike's clean row a (W2, 55.9 ms) is the
baseline; the report states the discrepancy under its own heading (report section 3).

| Window | Local | Gate | Probes open / close (s/frame) | Drift | Strays | Verdict |
|---|---|---|---|---|---|---|
| W3 pipes-apts | 2026-10-20 00:40-00:44 | median CPU 9.4 %, GPU 0 %, open | 0.0579 / 0.0587 | +1.4 % | none (WmiPrvSE 56.9 % at start is system) | clean |
| W4 pipes-b | 2026-10-20 00:45-00:50 | median CPU 4.25 %, GPU 0 %, open | 0.0573 / 0.0577 | +0.7 % | none | clean |
| W5 others-s | 2026-10-20 00:52-00:59 | median CPU 4.4 %, GPU 0 %, open | 0.0550 / 0.0560 | +1.9 % | none | clean |
| W6 others-c | 2026-10-20 01:00-01:07 | median CPU 5.6 %, GPU 0 %, open | 0.0539 / 0.0558 | +3.6 % | none | clean |

Transport leg CLOSED: all six windows clean, no re-run, ~56 min of the 120 min cap used.

CHARC rulings `871d4f17e78c10b3` (relayed 2026-10-20) applied: `BIG_PIPE_BYTES` documented as the
one constant with its measurement; automatic fallback to the default pipe added and demonstrated
(row `b-fallback+pts`, identity: same 681 hashes, 681/681 pts exact); `lockstep_difference` now
reports the mean absolute difference (a-ad10: max 19, mean 0.50). Untimed re-runs 3.5 min:
cumulative machine time ~60 min.

## Successor handoff (state at the transport yield)

- Committed: instrument `tools/spike_io/transport.py`; `av` 16.1.0 in the dev group; report
  `docs/reports/wp2.1s-io-spike.md` sections 1-7 (claim 1 complete); sections 8-9 PENDING.
- Records: `C:\Users\rwsmy\clearwater\work\wp2.1s\transport\` -- `reference.json`,
  `identity-<row>.json` (17 rows), `W1.json`-`W6.json`, `summary.json` (made by
  `transport.py summary`), `attribution.json`, `gate.jsonl`; logs in `work\wp2.1s\logs\`;
  helpers (uncommitted) `work\wp2.1s\show.py`, `work\wp2.1s\attribution.py`.
- Remaining: claim 2 (photo leg: `tools/spike_io/photo.py`, `tests/test_spike_io_photo.py`),
  claim 3 (licences; evidence gathered so far below), then ruff/format/mypy/pytest on the
  whole tree, then Reviewer A (STRONG, WSL codex, evidence in
  `C:\Users\rwsmy\clearwater-review-evidence\wp2.1s\rN\`).
- Photo exploration already done (not committed): Pillow 12.3.0 cannot write 16-bit RGB PNG
  (`fromarray` uint16 x3 raises TypeError; `frombytes(..., "RGB;16B")` gives mode RGB, IHDR bit
  depth 8). pillow-heif 1.8.1's public save writes `irot` from EXIF Orientation AND keeps the EXIF
  tag (file EXIF still 6); its read applies `irot` and resets EXIF Orientation to 1
  (`info["original_orientation"]` = 6). 10-bit HEIC: `open_heif(convert_hdr_to_8bit=False)` gives
  `RGB;16` (values << 6), default gives 8-bit. An EXIF-only or irot-only HEIC needs the private
  `pillow_heif.misc.CtxEncode` (`image_orientation` kwarg). libheif 1.23.6, x265 4.3 encoder,
  libde265 1.1.3 decoder.
- Licence evidence gathered (from the installed artefacts): PyAV 16.1.0 BSD-3-Clause; its FFmpeg
  8.0.1 configuration has `--enable-version3`, `--enable-libx264 --enable-libx265`, `--enable-nvenc
  --enable-nvdec`, NO `--enable-gpl`, NO `--enable-nonfree`; libavutil reports "LGPL version 3 or
  later" although libx264/libx265 DLLs are bundled in `av.libs`; codecs hevc, h264, hevc_nvenc,
  h264_nvenc, hevc_cuvid, h264_cuvid present. pillow-heif `LICENSES_bundled.txt`: binary wheel
  "GPLv2"; libheif LGPLv3, libde265 LGPLv3, x265 GPLv2. Pillow MIT-CMU. NumPy BSD-3-Clause AND
  0BSD AND MIT AND Zlib AND CC0-1.0. gyan 9.0.2 `--enable-gpl --enable-version3`, no nonfree.


## Reviewer A rounds (cumulative)

| Round | Transport / CLI | Critical | Major | Minor | In-envelope / out | NEW / REOPENED | Reverts | Fixes: product / test-only | Depth (dispatcher) | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
