# WP2.1S — Accept record (transport and photo I/O spike)

**Accepted 2026-10-20 by the orchestrator** (generation 3, session
`clearwater-orchestrator-20261019-2346`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG.
- Commission: CHARC `d99b28e575726fbd`.
- Brief approval and rulings: CHARC `5152ed4302874889`.
- Architecture notes: CHARC `fa9d637063376263`.
- Mid-run rulings: CHARC `871d4f17e78c10b3` (N1 approval of the 32 MiB pipe buffer, logged by
  CHARC as AD-23 on accept; AD-10 difference expected; gate-report supersession note on accept).

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp2.1s-brief.md` (DRAFT `07339bc`; FINAL `aa1f5f0`). Spec v0.5.3; architecture DRAFT 0.1 (`a27a6f7`). |
| Base SHA | `aa1f5f0` |
| Author head | `36066ef` (wp21s-cell3's final). Read clean at its return; no change after. |
| Cells and depth | Re-seated twice by depth evaluation. All three cells were implementer-opus-high. |
| Merged head | `wp2.1s-mc` = `36066ef` rebased onto main `dbc62b7` (`104c005`), plus the gate erratum `92a5735` and this record. Main fast-forwarded. |
| Byte identity | `git patch-id --stable` = `a5e7951dfade5160d754a73b188e8ef780833eda` on `aa1f5f0..36066ef` and on the B candidate `dbc62b7..104c005`. The commits after B are text only: the report erratum, this record, and the DR-31 row. CHARC held main from B to the merge. |
| Gates on the B candidate `104c005` | `ruff check` clean; `ruff format --check` 42 files formatted (whole tree; Markdown excluded since `c6b63e3`); `mypy` no issues in 27 files; full pytest **823 passed, 0 skipped**, 1 warning (CuPy `CUDA_PATH`), 530.8 s (`work/wp2.1s/logs/pytest-mc.log`); harness gate 366 tests OK (1 skipped). |
| Gates on main `a866f06` | `ruff check`, `ruff format --check` (42 files), `mypy` (27 files), harness gate (366 OK) re-run green; full pytest **823 passed, 0 skipped**, 1 warning, 452.6 s (`work/wp2.1s/logs/pytest-main.log`). |
| Reviewer A | STRONG (gpt-5.6-sol / high), WSL, codex-cli 0.162.1. Converged after 6 rounds. Evidence `clearwater-review-evidence\wp2.1s\r1` to `r6`; ledger `docs/proofs/wp2.1s-ledger.md`. |
| Reviewer B | One seat pass on `104c005`: `NO_NEW_CRITICAL_MAJOR`; 5 minor and 1 advisory. The text items were corrected as an erratum at the gate; the rest are banked as DR-31. |
| Owned and touched files | `tools/spike_io/` (`__init__`, `transport`, `photo`, `licences`, `guard`), `tests/test_spike_io_photo.py`, the report, the ledger, `pyproject.toml` (the `av` line only, CHARC grant) and `uv.lock`. No change to `tools/prototype/`, `src/`, `docs/architecture.md` or the harness. |

**Cell depths, with the moment of each reading:**
- `wp21s-cell`: 0 at dispatch; 205,020 / 68 turns at the row-a STOP; 240,144 / 82 at the
  transport yield (evaluation: hand the photo leg to a fresh cell); 257,132 / 95 at
  retirement.
- `wp21s-cell2`: 0 at dispatch (from handoff `c6a70f9`); 275,578 / 90 at round 1; 326,588 /
  118 at round 2; 342,467 / 128 at round 3. Retired there: the multi-finding remediation went
  to a fresh cell.
- `wp21s-cell3`: 0 at dispatch (from handoff `f18e043`); 181,719 / 86 at round 4; 219,047 /
  113 at round 5; 242,826 / 132 at return.

**Reviewer A rounds:**

| Round | Critical / major / minor | Notes |
|---|---|---|
| R1 | 0/4/4 | |
| R2 | 0/2/3 | |
| R3 | 0/1/7 | the write guard |
| R4 | 0/1/6 | pillow-heif native files from RECORD |
| R5 | 0/1/5 | the `--gate` script confined; approved past the five-round gate by the orchestrator |
| R6 | 0/0/3 | |

No criticals and no reverts.

## Orchestrator rulings during the package

1. **Row-a STOP (10:38Z).**
   - Row a measured 55.9 ms/frame clean, against Part B's 93.6 (above the brief's 25 % guard).
     The mechanism was identical (517,560 reads, none over 32,768 B). Busy-loop contention
     reproduced +9 to +14 %.
   - Ruling: CONTINUE. This spike's clean row a is the baseline, and the discrepancy is
     reported with its unexplained remainder. CHARC adds the gate-report supersession note on
     accept.
2. **Depth re-seats.** At 240K (the transport leg done; photo, licences and review remaining,
   so a large load) and at 342K (the round-3 remediation of 8 findings). Each successor
   started from a committed ledger handoff. Each predecessor was stood down before its
   successor's dispatch and acknowledged.
3. **Five-round gate.** Round 5 was approved because round 4's major was new, in envelope and
   report-bearing. Round 6 was approved on a new in-envelope major (`--gate` could run the
   wp1.2b script, which writes outside `work/wp2.1s`), with strict envelope classification.
   Round 6 converged.

## Process deviations (disclosed)

- **W7 (wp21s-cell2).** While testing the window-label check, a loop started an unplanned timed
  window `W7` without the idle gate. The cell stopped it after 2 runs.
  - The cell first reported "no W7.json". The orchestrator's QA found the file, and the
    corrected record is `work/wp2.1s/transport/W7-ABORTED.json` (md5 `6487d317...`).
  - It is in no summary and no gate log, and no reported figure rests on it.
- **Orchestrator `cd`.** While wp21s-cell2 was live (about 11:58Z), the orchestrator ran one bare
  `cd` into `work/wp2.1s/transport` and immediately back to the repository root. The cell was
  told and confirmed that no path of its own resolved strangely.
- **Ruff red on main.** `ruff format --check` was red on main from `a27a6f7` until CHARC's
  `c6b63e3`: ruff 0.17 formats Markdown code fences. The cells judged format on every file
  except `docs/architecture.md` until the rebase. The candidate is green on the whole tree.

## Reviewer B (seat, single pass), on candidate `104c005`

- **Transcript:** `clearwater-review-evidence\wp2.1s\reviewB\review-B.txt`, md5
  `486c317a72fb2f92b5b8196d53eac64e`. Companion files: prompt `48220b9a`, diff `ea9b3b7b`,
  stderr `5ee25571`, probe `403e9637`, runner `f681ab4d` (`md5s.txt` beside them).
- **Assertions:**
  - banner gpt-5.6-sol / high;
  - `^ERROR` 0, and no `ERROR codex_core` line;
  - `tokens used` footer present;
  - 25 `succeeded in`;
  - VERDICT anchored.
- **Withheld access:** one command line names `docs/proofs` only as a git
  `:(exclude)docs/proofs/**` pathspec, which is an exclusion, not a read. No command opened the
  evidence folder or the footage folder.
- **VERDICT: NO_NEW_CRITICAL_MAJOR.**

**Confirmed by B's executed probes:**
- the candidate identity hashes and pts lists match the 681-frame reference;
- recomputed `a`, `b` and `c-auto` interval sums equal their brackets and s/frame;
- the projection arithmetic holds;
- the fallback evidence shows default-pipe reads with identical hashes and pts;
- the D63 and HEIC/PNG records match the report;
- W7 is absent from the summary and the gate records.

**Findings and disposition:**
- **B1** (minor): the `iCCP` profile-name check misses PNG's control-character and space rules.
  Banked as DR-31(1).
- **B2** (minor): `window` runs without an idle gate when `--gate` is omitted. Banked as DR-31(2):
  the brief made the gate advisory.
- **B3** (minor): AD-10 reported beyond max and mean. Erratum.
- **B4** (minor): the bracket starts before transport set-up, not at spawn. Erratum.
- **B5** (advisory): the blanket IF-1 sentence covers the unchecked `a-ad10`. Erratum.
- **B6** (minor): the PyAV PNG crash had no durable record. Reproduced by the orchestrator at
  the gate, untimed:
  - Steps: `len(frame.side_data)`, then `del frame; gc.collect()`. The process exits 139; the
    same steps without touching `side_data` exit 0.
  - Evidence in `work/wp2.1s/gate-repro/`: script `969ea92f`, logs `5c05f709` (touch) and
    `04962237` (control), PNG `8a377fab`. Erratum.

## Orchestrator QA (claims against the records)

- `summary.json`:
  - every candidate row is `witness_same` True and every `+pts` / PyAV row `pts_exact` True;
  - every window W1-W6 has `contaminated` False;
  - the row medians match the report: a 55.87, b 16.11, b-cuda 12.99, s 24.30, c 75.97,
    c-auto 42.97, c-cuda 47.73, c-cuda-auto 42.42 ms.
- `photo.json`: `failures` is empty for png16 and png8.
- Changed files are confined to the owned set (`git diff --stat aa1f5f0..36066ef`).
- `pyproject.toml` adds only `av>=15,<17`, with the CHARC grant comment.

## For CHARC (on accept, CHARC-owned)

- AD-2, AD-17 and AD-18 close from the report's sections 6, 8 and 9. AD-23 records the N1
  approval of the pipe buffer.
- The dated supersession note on gate report Result 1 (Part B's 0.089-0.094 s/frame and its
  -20 to -30 % analysis estimate) points at this report.
- **AD-18 corrections:**
  - the gyan FFmpeg CLI is GPL-3.0-or-later;
  - NumPy's licence expression is wider than BSD-3.
- **AD-18 new entries:**
  - PyAV 16.1.0 (BSD-3) bundles FFmpeg 8.0.1, which is labelled LGPL-3.0-or-later with no
    `--enable-gpl`, yet carries working libx264 and libx265 and NVENC/NVDEC. Its compatibility
    is UNKNOWN from the artefacts.
  - pillow-heif ships 7 native files.
