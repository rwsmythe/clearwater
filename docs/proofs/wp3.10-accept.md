# WP3.10 accept record (orchestrator generation 12, 2026-10-27)

**Package:** WP3.10 video encode, mux and timing.
- **Modules:** `clearwater.io.video.encode` (IF-5 `FFmpegVideoSink`, `VideoEncodeError`, the AD-12 tables and the NVENC rate ceiling), `capability` (D74 detection, `resolve_encoder`), `nut` (the pts carrier), `verify` (the packet table, the output check, the completeness rule).
- **Instruments:** `tools/video_fidelity.py` (V4, DR-18) and `tools/video_io_bench.py` (the export floor row).
- **Brief:** `docs/briefs/wp3.10-brief.md` (FINAL, CHARC rulings `53d1d906e47fe2c9`).
- **Rulings since:**
  - P8, the non-square sample aspect ratio refused at `open`;
  - the AD-12 NVENC ceiling O3 (`17f12f9dc7eba3ae`, AD-12 amended `ccaecd7`);
  - the AD-12 mapping RULED (`c1d67b39bb72cc1f`, AD-12 amended `759f0d0`);
  - the DR-48 disposition (`759f0d0`).

Nine seats (implementer-opus-high, STRONG; depths are the dispatcher's figures):

| Seat | Work | Depth |
|---|---|---|
| 1 | round 0 | 219,455 |
| 2 | build, R1 | -- |
| 3 | R1 remediation, R2 | 361K at the pause |
| 4 | R3, R4 | 279,801 |
| 5 | floor-row instrument, R5, R6 | 286,315 |
| 6 | R7, R8 | 204,725 |
| 7 | footage and pre-fix NVENC figures | -- |
| 8 | the NVENC ceiling, R9, R10, footage window | 252K at R10; 305K at stand-down |
| 9 | the AD-12 mapping, the exclusive floor row, the report, B pass-1 remediation, the B pass-2 gate fix | 339,190 at the gate-fix yield |

**Candidate:**
- **Author branch:** `wp3.10` (`2b8cd29`, base `718324b`).
- **Merge candidate:** `wp3.10-mc` (`7f98848`, rebased onto main `59049a9`; the accept chain `wp3.10-acc` `831fb8d` is the same rebased onto main `ceec6b9`). Every owned file is byte-identical to the author branch (`git diff`, 0 lines). The file set is 15 files.
- **Kept B-reviewed trees:** `wp3.10-mc1` (`78ae77a`, B pass 1) and `wp3.10-mc2` (`da33e63`, B pass 2).
- **Merged:** one `git merge --ff-only` of the accept chain onto main; this record's commit follows the package's last commit.

**Footprint (checked at this seat):**
- **Owned files only:** `src/clearwater/io/video/{encode,capability,nut,verify}.py`, `__init__.py` (exports appended), `tests/test_io_video_encode{,_units,_bench}.py`, `tests/test_video_fidelity.py`, `tests/test_io_video_probe_rules.py` (four module names added), `tools/video_fidelity.py`, `tools/video_io_bench.py`, `tools/container_spike/spike.py` (DR-26 only), the report `docs/reports/wp3.10-video-encode.md`, the ledger.
- **Untouched:** `interfaces/`, `color/`, `jobs/`, WP3.9's and WP3.7's modules, `pyproject.toml`, `uv.lock`.
- **Line endings:** 0 CR bytes in every owned blob.

## Results

- **Structure:** IF-5 as frozen. One FFmpeg process, with the frames on a NUT carrier (sentinel plus the setts/noise input BSF).
- **Timing preserved and verified at `close`:** per-frame pts, start offset, edit list (AD-22 by presentation effect), audio packet pts, display rotation (D94, D95, D105).
- **Completeness:** `close` refuses an output that is not the source's whole readable video (B pass 1 #1). On a truncated source, readable = the packets listed before the first corrupt packet in decode order (B pass 2 #1).
- **Colour:** tags, pixel format and chroma match the source (D55, D114). The D54 fallback is warned.
- **Provenance:** in the MP4 `comment` tag (D91, Q5).
- **AD-12, RULED:**
  - NVENC `-cq` 22/26/30 and libx265 `-crf` 21/26/30.
  - The NVENC ceiling: 0.24 bit/pixel High, with Standard at 1/2 and Draft at 1/4, under an explicit `-tier main -level L`.
  - Busy GX011627 NVENC came out at 1.018 / 0.515 / 0.258 x camera at 5.2 / 5.1 / 5.0 Main, against 0.356 / 0.350 / 0.338 before the fix.
- **V4:** every MANDATORY and REQUIRED item SAME on every WP2.3 sample, the synthetic offset, B-frame and 5.3K clips, and GX011627. The exception is the Edits compilation's two coarse-timescale rows, an accepted limit.
- **Export floor row** (exclusive window, `e04a7cb`, OPEN/CLOSE posted to CHARC):
  - NVENC 8-bit 0.154-0.156 s/frame at 4K. Added to WP3.4's 0.4392 c3 core this gives 0.594 of D106's 0.834, so it FITS.
  - NVENC 10-bit 0.174 and libx265 0.279 also fit.
  - Record `clearwater-review-evidence\wp3.10\s9-floor\`.
- **`QUALITY_RATIO` figures (Q13):** in report section 7.2, for WP3.14 with DR-48 as ruled.

## Nets

| Net | Result |
|---|---|
| Reviewer A (cells, STRONG, WSL codex-cli 0.162.1 / gpt-5.6-sol high) | Ten rounds. Product converged at R4; the floor-row instrument at R8 (scoped R5-R8); the NVENC ceiling R9 (1 MAJOR, from the then-ruled 20 Mb/s floor) and R10 (0/0/2) TERMINATED at the five-round gate (test-only cleanup `0b76301`). The mapping commit `e04a7cb` is values-only and owed no round (CHARC). Evidence `clearwater-review-evidence\wp3.10\r0..r10`; the ledger table carries each round's figures |
| Reviewer B pass 1 (this seat, `78ae77a`; kept as `wp3.10-mc1`) | NEW_CRITICAL_MAJOR_FOUND. Banner gpt-5.6-sol / high, read-only; 0 `^ERROR`; 31 "succeeded in"; 318,111 tokens. Six reviewer-MAJOR findings: #1 UPHELD (`close` verified against the pts written, not the source's readable pts); #2 NOT UPHELD (reproduced at the cell: a one-byte audio `elst` change FAILS `check_output`); #3 and #5 limits; #4, #6 (CHARC-ruled `b238bd27`: the `gpmd` byte hash in an uncommitted record is within the owner's rule) and #9 not new; #7 and #8 MINOR upheld. ONE remediation by seat 9: `673f958`, `b7953a8`, `48dd4b2`, plus a test-only flake fix `4537881` (two bench timing tolerances, each with a planted negative). Adjudication `reviewB\adjudication.md`; md5 `review-B.txt` cc1eb9d55df9... (`reviewB\md5sums.txt`) |
| Reviewer B pass 2 (this seat, `da33e63`; kept as `wp3.10-mc2`) | NEW_CRITICAL_MAJOR_FOUND. Banner gpt-5.6-sol / high, read-only; 0 `^ERROR`; 32 "succeeded in"; 242,942 tokens. SECOND BLOCKING PASS, ADJUDICATED AT THE GATE by irreversibility; CHARC UPHELD every row (`b4e4a184`). #1 UPHELD, a regression of the pass-1 remedy: a truncated B-frame source's complete export was refused. EXECUTED at this seat: WP3.9 yields 59 frames, the numeric rule wanted 58. Gate fix `39bc9ac`: one helper shared by `_plan_tracks` and `missing_frames`. #2 and #4 limits; #3 not new; #5 test-strength note; #6 out of envelope; #7 erratum (`eda4e98`). VERIFIED BY EXECUTION at this seat: the two new tests FAILED on `da33e63`'s code (the false refusal at pts 30208; the old rule's set missing 6006; `gate\before-at-da33e63.log`) and pass on the candidate. md5 `review-B.txt` 5dea3cb91025... (`reviewB2\md5sums.txt`) |
| Candidate full pytest (this seat, `7f98848` = main `59049a9` + WP3.10) | 4766 passed, 2 skipped, 2715 s, exit 0 (CuPy as installed, offscreen, one background process, footage tests included; log `.worktrees/wp3.10-mc/work/g12-full-wp310.log`). The first run of this suite is VOID, not counted: the worktree lacked the uncommitted `clearwater.local.toml`, so `test_lookcheck_deep.py` failed on `LocalConfigError` (11 failed, 2 errors) and the footage tests skipped (27). The rerun had the main tree's config copied in, as the tranche-B stack had. Main's figure by code identity: the accept chain `831fb8d` (rebased onto main `ceec6b9`) differs from `7f98848` in main's six docs files only (0 lines in src, tests, tools, `pyproject.toml`, `uv.lock`) |
| Harness gate | 379 OK (1 skipped) on `7f98848` and on the accept chain `831fb8d` (main moved kernel docs: the Reviewer B pin `fac53e9`, the implementer lane `3c230e4`); ruff clean, 227 formatted, mypy 132 clean; CR check 0 on every owned blob |

## Disclosed and ruled

- **Leg (a):** the GX011627 M+R check ran on `0b76301` (cq 23), not on the final values. CHARC pre-ruled NO re-run: the MANDATORY and REQUIRED items are container, timing and metadata properties, and `nvenc_proof.tied` held on every floor leg on `e04a7cb`.
- **R10 gate:** termination at the five-round gate ACCEPTED (orchestrator; CHARC QA). Two choices beyond the O3 ruling were ACCEPTED as out of envelope: the ceiling clamp to 6.2's 240 Mb/s, and the refusal of a picture no level holds.
- **The pass-1 order** named the function `_video_options`; it is `_encoder_options`. Same intent (CHARC).
- **A bench timing bound** (`-0.05 < offsets["telemetry_origin"]`) failed twice for seat 9 while another load ran on the host. It passed every isolated and quiet run. The candidate full suite passed it. If it flakes on a loaded host, CHARC may want a DR row (test-only tolerance).

## Debt

- **CLOSED:** DR-17, DR-18 (1)-(4), DR-20 (4) and (6), DR-26, DR-39 (a). DR-18 (1) closes on `tied`; CHARC writes the row at the accept.
- **Open or partial:** DR-15's iPhone leg stays OPEN; DR-39 (c) PARTLY.
- **DR-48:** CHARC-ruled, for WP3.14's brief.
- **Rows by CHARC at QA:**
  - B pass 2 #2: `close` does not compare the audio edit-list duration or the last packet duration;
  - the limit rows in report section 9 (B pass 1 #3, #4, #5, B pass 2 #4);
  - banked R5 #10 (several GPUs);
  - WP3.7's `probe.py` inheriting `FFREPORT`;
  - D75's parenthetical, a spec erratum for v0.5.5.

## Consumer notes

- **WP3.14:**
  - Hands `SafeWrite`'s temporary to `open`.
  - Calls `abort` for a cancel. A `close` after a partial write is refused by design.
  - Applies `QUALITY_RATIO` with DR-48.
  - Keeps provenance well under 16 KiB.
- **WP3.20 and WP3.14:** call `resolve_encoder` (the ONE "auto" rule). WP3.20's interim stub is swapped at WP4.3.
- **WP4.3:** the shared CREATE_NO_WINDOW spawn helper.
- **WP3.21:** the floor row is its baseline.
