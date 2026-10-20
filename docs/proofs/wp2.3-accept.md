# WP2.3 — Accept record (shared test fixtures)

**Accepted 2026-10-20 by the orchestrator** (generation 4, session
`clearwater-orchestrator-20261020-0524`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG.
- Commission: CHARC `9fb52c00bbb58a9b`. Brief approval and rulings: CHARC `8d7880255daf7c79`.
- Round-1 ruling: CHARC `ef7b272564ddeb9d` (AD-14 centre track; the conditional conftest
  statement; `.gitattributes`). R1-2 layout deviation upheld: CHARC `9a4d10e2d27a4323`.
- Brief FINAL `da074f4`.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp2.3-brief.md` (DRAFT `020ed86`; FINAL `da074f4`). Spec v0.5.3 at dispatch (v0.5.4 applied on main `9cf16c5` during the package; no clause the package serves changed). |
| Base SHA | `da074f4` |
| Author heads | `d495b57` (first cell, R1 remediated); `cea7a7e` (Reviewer A converged at R2, cleanup); `f56bec0` (the ONE Reviewer B remediation, code `1d0e04d`). |
| Cells and depth | **`wp23-cell`** (implementer-sonnet-high): 0 at dispatch; 216,593 / 62 turns mid-build; 379,109 / 145 mid-R1-remediation; **406,816 / 164 at its R1 yield, PAST the 400K cap**; stood down 16:34Z. It ran R1 AND its remediation in one turn without yielding at the R1 boundary or at the ~250K evaluation point (CHARC: the corrective is a brief that names the R1 yield explicitly; the successor's prompt did, and it worked). **`wp23-cell2`** (implementer-sonnet-high), successor from `d495b57`: 0 at dispatch; 96,313 / 55 at the R2 yield; 109,025 / 65 at its FINAL return (read twice, 17:07:54Z and 17:09:28Z, unchanged); 196,003 / 117 at the Reviewer B remediation yield. |
| Merged head | `wp2.3-mc` = `f56bec0` rebased onto main `ed6f6d9` (`137d5ca`), plus this record and DR-33. Main fast-forwarded. CHARC held main from B to the merge. |
| Byte identity | `git patch-id --stable` = `6712360de3e5...` on `da074f4..f56bec0` and on `ed6f6d9..137d5ca`. (Pass-1 candidate `a32e5fb`: `6859c9e2b3b4...` on both its ranges.) |
| Gates on the candidate `137d5ca` | `ruff check` clean; `ruff format --check` 65 files; `mypy` strict 46 files clean; harness gate 366 OK (1 skipped); **full pytest 1138 passed, 1 warning (CuPy CUDA_PATH), 527 s, exit 0.** Pass-1 candidate `a32e5fb`: 1130 passed, exit 0 (after the seat setup fix below). |
| Gates on main | Main fast-forwarded to `d605925`; `uv sync`; `ruff check` clean; `mypy` 46 files clean; harness gate 366 OK (1 skipped); **full pytest 1138 passed, 1 warning, 506 s, exit 0**; `git ls-files --eol tests/fixtures` all `-text`, manifest i/lf w/lf. |
| Reviewer A | gpt-5.6-sol / high, WSL. R1 on `4ffc8b1`: 7 major / 4 minor, all fixed. R2 on `1e2d2f6`: 0 major / 3 minor, `NO_NEW_CRITICAL_MAJOR`; the 3 minors fixed as post-convergence cleanup (`e5ea4f9`). No reverts. Evidence `clearwater-review-evidence\wp2.3\r1`, `r2`. |
| Reviewer B | Pass 1 on `a32e5fb`: `NEW_CRITICAL_MAJOR_FOUND` (4 major, 1 advisory), ONE remediation (`1d0e04d`). Re-run on `137d5ca`: `NEW_CRITICAL_MAJOR_FOUND` (3 major, 1 minor), adjudicated at the gate NOT BLOCKING (below; DR-33). |

## The package

87 manifest samples (`tests/fixtures/manifest.json`): 66 stills, 8 video clips, 2 flicker
(the AD-14 clip is generated on demand into `work/fixtures/generated`, 89 MB FFV1, never
committed; its mask is committed), 11 dummy files (GoPro-style names, three DNG variants).
Committed total 894,960 bytes, largest file 151,041 bytes (limits 10 MB / 2 MB, enforced by a
test). Omitted and listed: 16-bit RGB TIFF (Pillow 12.3.0 cannot write it). New repo-root
`.gitattributes` (`tests/fixtures/** -text`, owned by WP2.3; later lines only by a CHARC grant).
`tests/conftest.py` gains only the ruled conditional `pytest_plugins` statement (ruff's layout).

## Reviewer B

**Pass 1** (on `a32e5fb`). Transcript `clearwater-review-evidence\wp2.3\reviewB\review-B.txt`,
md5 `955da98e`; stderr `8d7a88b5`; prompt `8dbef413`; diff `cf7a2a5d`; `md5s.txt` beside them.
- Assertions: banner gpt-5.6-sol / high, read-only; `^ERROR` 0; footer 431,906 tokens; 24
  `succeeded in`; VERDICT anchored (line 102). The two command lines naming withheld paths are
  `--glob '!docs/proofs/**'` exclusions and the brief's own text; no read.
- Findings and adjudication (orchestrator):
  - **B1 MAJOR, BLOCKING (EXECUTED):** `vid-vfr`'s last frame was 1001 ticks against the
    manifest's stated 1001,1001,2002 cycle (track 39039 vs 40040); measure() used pts deltas
    and the test compared a set.
  - **B2 MAJOR, BLOCKING:** TIFF bit depth hard-coded 8 in measure and test (circular).
  - **B3 MAJOR as classed, not blocking (ruling 2 asked for the decoded-frame hash),
    strengthened:** the flicker gate checked decoded hash and count only.
  - **B4 MAJOR as classed, not blocking (synthetic samples, no owner data path; B's raw scan
    clean), strengthened:** no-GPS checks missed XMP and raw `udta`.
  - **B5 advisory, out of envelope:** the manifest records encoder-dependent video sizes;
    banked in the ledger.
- ONE remediation (`1d0e04d`): FFmpeg writes the last VFR frame as 2002 (`setts`), measure
  records ffprobe packet durations, `stts` durations and the track duration, exact-list test
  (intended avg rate now 22500/1001); TIFF tag 258 read from the bytes, planted 16,16,16 copy;
  flicker identity (container, codec, pix_fmt, size, rates, time base, packet-pts count and
  hash) before the frame hash, cache hits verified; raw XMP/GPS scan and an MP4 `udta` walk.
  Each regression test fails on the pre-fix code (cell evidence `work/fixtures/runs/b*-prefix.txt`).
  Only `vfr.mp4` and `manifest.json` changed bytes.

**Re-run** (on `137d5ca`). Transcript `...\wp2.3\reviewB2\review-B.txt`, md5 `9895f977`;
stderr `bd1cc68e`; prompt `6d1ce301` (with a "THIS IS THE RE-RUN" section); diff `29f6bfd5`;
`md5s.txt` beside them.
- Assertions: banner; `^ERROR` 0; footer 257,461 tokens; 25 `succeeded in`; VERDICT anchored
  (line 32). The one command naming a withheld path is a `find` for FFmpeg binaries with
  `-not -path '*/docs/proofs/*'`; no read.
- B verified B1 and B2 end to end by EXECUTION against the committed bytes and the pre-fix blob
  (stts 30 durations in the cycle, last 2002, total 40040; all nine TIFFs 8,8,8), B3 by
  reasoning, and re-verified AD-14 geometry, AD-24's four HEIC cases, the 10-bit `pixi`, the
  inventory, sizes and md5s, the conftest diff and the `-text` attribute.
- New findings: (1) MAJOR: a still's container format is not measured from the file; (2) MAJOR
  (EXECUTED on the predicate): the XMP scan misses XMP with another prefix carrying only
  `GPSLongitude`/`GPSAltitude`; (3) MAJOR: `irot` presence is read without its `ipma`
  association, and stored size is not checked against `ispe`; (4) minor: the flicker identity
  omits `ffprobe_errors` and packet durations.

**Adjudication at the gate (orchestrator): NOT BLOCKING; banked as DR-33.** This is the second
blocking B, so it is adjudicated here, per the established practice.
- Every finding concerns detecting a FUTURE generator regression on regeneration, not the
  delivered artifact. The delivered samples are correct: B's own raw probes confirm (2) and (3)
  on the committed bytes (no XMP; `irot` associated with the primary item), and the orchestrator
  checked (1) on all 66 committed stills by magic bytes against extension and manifest kind:
  0 mismatches.
- No generator writes XMP or reads owner material (static check and audit hook).
- DR-33 binds the fixes to the next change of `tools/fixtures/` or any regeneration of committed
  stills or the flicker clip; WP3.6 independently exercises (3) when it tests its AD-24 reading
  against these samples.

## Seat notes (orchestrator; not package defects)

- The first candidate pytest showed 11 failed / 107 errors: the fresh `-mc` worktree had no
  `work/` (pytest's `--basetemp` parent), and `clearwater.local.toml` was not re-copied after the
  worktree was rebuilt. With both fixed: 1130 passed.
- The first `-mc` rebase stopped when `.gitattributes` landed mid-range over a CRLF checkout of
  `manifest.json` (`core.autocrlf=true` from the system gitconfig). Rebuilt with
  `-c core.autocrlf=false`. A stray `core.autocrlf=false` written to the shared `.git/config` by
  that step was removed at once (`git config --local --unset`); the system value is unchanged.

## Rulings during the package

In the ledger (`docs/proofs/wp2.3-ledger.md`): R1-1 AD-14 geometry (centre track; upper half
never touched; AD-14 wording clarified on main by CHARC); R1-2 the conditional `pytest_plugins`
statement in ruff's layout (102 columns > 100; upheld); R1-3 `.gitattributes` granted, raw-byte
manifest comparison.

## Open items carried

- DR-33 (above).
- B5: manifest byte-identity depends on the encoder build's video sizes (out of envelope; a
  second FFmpeg build would need video sizes moved out of the byte-identical manifest).
- No 16-bit RGB TIFF (Pillow limit). DNG refusal is `expect.refusal` (no `Fault` kind; D116).
- The truncated clip expects `truncated` / warn (WP3.7 ruling 7.4 defines `truncated`).
- The untagged clip is H.264 (x265 always writes a video signal type).
- HEIC is written through pillow-heif's private `misc.CtxEncode` (as WP2.1S).
- Phase 3 briefs cite samples by these manifest ids (wave-1 ruling X3).
