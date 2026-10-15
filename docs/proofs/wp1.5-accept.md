# WP1.5 — Accept record (container spike)

**Accepted 2026-10-15 by the orchestrator** (session `clearwater-orchestrator-20261014-1258`),
on CHARC's commission `9ea69283f746b163`. Gate per `docs/review-gate-clearwater.md` Part 2, as
corrected at `30483f2`: Reviewer B is the orchestrator's own Codex pass at its seat. This is the
first package accepted under that form. Result 6 of the prototype gate; Gate 6 is CHARC's, at
WP1.6.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp1.5-brief.md` (FINAL `8ad93b8`), plus the remediation brief `docs/briefs/wp1.5-remediation-brief.md` (`d2c2b9a`). CHARC rulings: `bdae7c6214ae1247` (pre-rulings 1-4), `9452fe94b5465abb` (ruling 1 stands; DR-15), `2b6dae230aa9749a` (Reviewer B form) and `978f1d2576b23c0a` (B dispositions accepted; DR-16 and DR-17). |
| Base SHA | `7048fd7` |
| Author heads | `97d40df` (first return; author depth 363K), `82e5cfc` (rework; author depth 478K, past its cap), `9c656e7` (remediation by the fresh cell `wp15-fix`; depth 253K). Branch `wp1.5`. |
| Merged head | `3242679`: branch `wp1.5-mc` = `wp1.5` rebased onto main `1f387ae`, then main fast-forwarded. |
| Byte identity | `git patch-id --stable` = `1712112b310abb1d116e36f5a98d2bfc7b224a37`, both before (`7048fd7..9c656e7`) and after (`1f387ae..3242679`). |
| Merge integration | Main's intervening commits are docs only: briefs, state pointers, the debt register, the review-gate fill and `CLAUDE.md`. No file overlaps the arc. |
| Reviewer A | Codex STRONG (gpt-5.6-sol / high), WSL, codex-cli 0.162.1. Four rounds, all converged: r1 BLOCKING (2 majors fixed), r2, r3 (rework delta) and r4 (remediation delta), each 0 crit / 0 major / minors fixed. Ledger `docs/proofs/wp1.5-ledger.md`. Depths (dispatcher-read): author 363K at r2, 478K at r3; `wp15-fix` 253K at r4. |
| Reviewer B | The orchestrator's own pass, STRONG, WSL. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp1.5\reviewB\` (`run_review_B.sh`, `review-prompt-B.md`, `review-diff-B.txt`, `review-B.txt`, `review-B.stderr.txt`, `md5s.txt`; pass 1 under `r1\`). See below. |
| Verification QA | Cell `wp15-revb` (implementer-opus-high; depth 184K). It was dispatched as "Reviewer B" under the old fill; CHARC reclassified its work as QA evidence. Brief `docs/briefs/wp1.5-review-brief.md`; evidence `...\wp1.5\B\`; outputs `C:\Users\rwsmy\clearwater\work\wp1.5-B\`. |

## Reviewer B (orchestrator seat)

**Pass 1, on candidate `7a490c7`** (author head `82e5cfc` rebased onto `bd358df`): **BLOCKING**.

Assertions:
- the banner reads gpt-5.6-sol / high;
- `^ERROR` 0;
- one `ERROR codex_core` line, an echo of the brief;
- footer 1;
- 21 `succeeded in` lines;
- an anchored `VERDICT: NEW_CRITICAL_MAJOR_FOUND`.

Withheld-path hits were echoes or exclusion globs, so the pass is valid. Transcript md5 `b4810683deb7a9f0e417825c0c81227a`.

| # | Finding | Disposition (accepted by CHARC) |
|---|---|---|
| B1 | CRIT, reasoned: an NTFS hard link at an output or record path, or a check/use race with a junction, can bypass containment. | The static hard link is FIXED (`st_nlink > 1` refused, with tests). The race needs a concurrent hostile process, outside the threat model: BANKED as **DR-16** (product safe writing, 8.4/D85). |
| B2 | MAJOR: the test helper's ffmpeg calls inherit FFREPORT. | FIXED, with a test that sets FFREPORT before a clip is built. The pycache part was rejected (out of scope); the report's safety sentence was reworded to its true scope. |
| B3 | MAJOR, executed: an H.264 output passes as all SAME, because codec and container were informational only. | FIXED: REQUIRED (D55/D114) items for 8.2's HEVC and MP4, with tests. **This is the first finding of a seat-run Reviewer B (CHARC):** neither Reviewer A nor the QA cell caught it. |
| B4 | MAJOR: no 8.3 collision suffix; a re-run overwrites its outputs. | Not a defect of the spike (the brief claims the base name only). Stated in the report; the product owns 8.3 collisions and 8.4. |
| B5 | MAJOR, out of envelope: an untagged source gets no colour options and no warning (the D54 fallback). | No code. Stated in the report's section 9. BANKED as **DR-17** (WP3.10). |
| B6 | minor | The "container start_time" item did not read `format.start_time`. FIXED by a new MANDATORY item, with a test. |
| B7 | minor | The proof criteria lacked the frame size, and a stale utilisation reading could gate. FIXED: the gate is the size, the encoder tag and the GPU named during the encode; session count and utilisation are supporting only. This also settles the author's post-r3 change `44ef28b`. |
| B8 | minor | Report claims not backed by records. FIXED: each is cited to a file under `work\wp1.5\`, marked informal, or removed. SAR was added to the camera record. |
| B9 | advisory, out of envelope | `ctts` v0 read signed. No action. |
| B10 | advisory, out of envelope | Audio "present" is SAME when both files lack audio. A note was added. |

**Pass 2, on candidate `3242679`** (remediated head `9c656e7` rebased onto `1f387ae`, the merged tree): **VERDICT: NO_NEW_CRITICAL_MAJOR**.

Assertions:
- the banner reads gpt-5.6-sol / high;
- `^ERROR` 0;
- one `ERROR codex_core` line, an echo of the brief;
- footer 1;
- 15 `succeeded in` lines;
- an anchored VERDICT line.

The only accesses are the permitted `work\wp1.5\` records and an exclusion glob. Its sandbox could not run pytest or ffmpeg, which it stated; those findings are REASONED.

md5s:

| File | md5 |
|---|---|
| prompt | `bcc51f75ef9496cc87887551bf811744` |
| diff | `5a61563b242bc157f6b1b5e7bb6626e3` |
| transcript | `bdd09812bfe5cad265915e8e622cbd5b` |
| stderr | `2667dc4e9bfe590ada0976b682031b60` |
| script | `8ceb744cac0a1adef712995d848c4505` |

Its four minors and the advisories are RECORDED and not fixed. They are instrument hardening, carried to WP3.10, which reuses `compare.py` in spirit:
1. The GPU sample is not tied to the encode window, the GPU UUID or the FFmpeg PID.
2. AAC decoder configuration, priming and side data are not compared.
3. `build_record` has no roster invariant, so an incomplete item list summarises as all SAME.
4. The camera record does not count missing pts.

The out-of-envelope advisories (None-versus-None compared as SAME; `ctts` v0; MD5 rather than a byte comparison) and the test-suite blind-spot list stand as written in the transcript.

## Verification QA (the separate half of the gate)

- **Cell `wp15-revb` on `97d40df`:** NO_BLOCKING.
  - Every claim reproduced. Its re-encodes are BYTE-IDENTICAL to the author's.
  - `compare.py` on the author's outputs equals the author's JSON on all 36 items.
  - Its own pts, packet and `elst` cross-check agrees.
  - All 5 of 5 deliberate breaks were flagged MANDATORY: audio shift, timestamp reset, dropped frame, added rotation, start offset.
  - The footage snapshot was unchanged.
  - Its F1-F5 went into the rework (`d072698`, `3ca3e98`).
- **Orchestrator gate checks, on candidate `3242679` and again on main after `uv sync`:**

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 61 files already formatted
uv run mypy                    -> Success: no issues found in 13 source files
uv run pytest -q -rs           -> 398 passed, 1 warning (0 skipped: WP1.5 footage test, NVENC gpu tests and the WP0.2 footage test all RUN)
uv run pytest -q -m gpu        -> 19 passed, 379 deselected
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

  On candidate `7a490c7` the WP0.2 test `test_real_footage_has_one_row_per_media_file` failed once: `SCUBA/GX011598 (1).mp4.crswap` grew from 832,515,439 to 834,058,272 bytes during the owner's download. That is environmental (CHARC), and it passed on the final candidate and on main.
- **Witness (orchestrator, main):**
  - `uv run python tools/container_spike/compare.py <GX011628.MP4> <work\wp1.5\reencode\GX011628_corrected.MP4> --out work\wp1.5\witness-orch` reports 41 items: MANDATORY 0, REQUIRED 0, BEST-EFFORT 8 DIFFERENT, with `mandatory_and_required_all_same` True.
  - Its `items` equal the recorded `GX011628_corrected.compare.json` exactly.
  - `spike.py --help` lists `capability`, `camera` and `reencode`.
- **Locks:**
  - Only the six owned files changed (`__init__.py` is untouched by the remediation).
  - No `pyproject.toml` or `uv.lock` change; no PyAV; nothing under `src/`.
  - The footage folder was input only: the QA snapshot and the remediation cell's size and mtime check were both unchanged.
  - All outputs are under `work\wp1.5\` (and `work\wp1.5-B\` for QA).

## Result (records `C:\Users\rwsmy\clearwater\work\wp1.5\`; report `docs/reports/wp1.5-container-spike.md`)

- **Recommendation: SIMPLE.** One FFmpeg process decodes, encodes with NVENC and muxes. On GX011627 (primary) and GX011628 (fast check), each of 41 items:
  - MANDATORY 0 DIFFERENT, including:
    - the full per-frame pts sequence, exact;
    - the video edit list AS WRITTEN;
    - the edit-list presentation effect;
    - the start offset in four forms;
    - the audio packets, byte-identical by MD5, and audio sync;
    - orientation.
  - REQUIRED (D55/D114) 0 DIFFERENT: BT.709 full range, 4:2:0 8-bit, HEVC, MP4.
  - BEST-EFFORT 8 DIFFERENT:
    - the `udta` camera atoms;
    - the `firmware` tag;
    - the audio stream's timecode tag;
    - brands;
    - the encoder and handler tags;
    - the track order and flags;
    - the added sample-entry boxes;
    - the identity edits the muxer adds to the non-video tracks.
  - Kept: the GPMF track (byte-equal), the timecode track and the creation time.
- **Capability (D74):** each proven from its output by ffprobe:
  - NVENC and libx265 at 8 and 10 bits;
  - `-hwaccel cuda` decode, 681 of 681 frames.

  RTX 4070 Laptop GPU, driver 610.62.
- **Camera (D54/D73):**
  - HERO13 Black, firmware H24.01.02.10.00;
  - HEVC Main 8-bit `yuvj420p`, BT.709 FULL range;
  - CFR 30000/1001, start 0;
  - HDR video off; GP-Log not exercised.
- **D60:** no `.LRV`, so it stays open.
- Frame access for the correction is NOT exercised; that is WP2.1's question.

## Dispositions

| Item | Disposition |
|---|---|
| Edit-list reading | RULED (CHARC). The video `elst` as written is MANDATORY. The muxer-added identity edits are BEST-EFFORT. B-frame sources are out of envelope: **DR-15** (WP2.1, with CHARC's lean recorded in the report). |
| The `udta` atoms and `firmware` tag lost | BEST-EFFORT; banked by CHARC (debt register). |
| Containment races | **DR-16**. |
| D54's untagged fallback | **DR-17**. |
| Reviewer B pass-2 minors 1-4 | RECORDED for WP3.10's instrument (above). |
| Author slip: `psnr27.log` written to the main tree root by a relative `stats_file` | Moved to `work\wp1.5\explore\` at once; no footage contact. CHARC: no action. |
| Remediation cell slip: one `git stash push`/`pop` in the worktree, against the instance's stash rule | Popped at once; the stash list is empty. Recorded. |
| QA-cell slip: an FFREPORT probe wrote `C;C` into the worktree | Preserved as evidence (`B\ffreport\`), then deleted; the worktree is clean. This was the B2 / F2 repro. |
| The first three gates ran Reviewer B as a cell (WP1.1, WP1.2A, WP1.5's first pass) | Fill corrected at `30483f2`. A retroactive seat-run Reviewer B over `tools/prototype` (WP1.1 and WP1.2A) comes next (CHARC `2b6dae230aa9749a`). |
