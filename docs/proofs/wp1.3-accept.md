# WP1.3 — Accept record (look check pack, shallow part)

**Accepted 2026-10-15 by the orchestrator** (session `clearwater-orchestrator-20261014-1258`).
Gate per `docs/review-gate-clearwater.md` Part 2 (corrected `30483f2`): the cell's Reviewer A
loop, my own seat Reviewer B on the merge candidate, and my verification QA.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp1.3-brief.md` (FINAL `a1c073c`); remediation `docs/briefs/wp1.3-remediation-brief.md` (`9c2e487`). |
| Base SHA | `a1c073c` |
| Author head | `0233a8e` (`wp13-cell`, implementer-sonnet-high; 412K at return, PAST-CAP, retired) |
| Remediation head | `28ac2de` (`wp13-fix`, implementer-sonnet-high; 229K at return) |
| Merged head | `7178540` (`wp1.3-mc` = `wp1.3` rebased onto main `324fbf4`; main fast-forwarded). |
| Byte identity | `git patch-id --stable` = `7720832d70bbc271c557729c58fba30368ba50ed` on `a1c073c..28ac2de`, on the candidate and on main `324fbf4..7178540`. The first candidate (`d27c53f`, before the remediation) was `08a4d57a...` on both sides. |
| Reviewer A | Codex STRONG (gpt-5.6-sol / high), WSL, codex-cli 0.162.1. 3 rounds, ledger `docs/proofs/wp1.3-ledger.md`, evidence `clearwater-review-evidence\wp1.3\r1..r3\`. r1: 1 major (rejected by the brief: the open-water case stays PENDING) + 5 minors fixed; r2: 3 minors fixed, converged; r3 (remediation delta, the one allowed round): 1 introduced major + 5 minors, all fixed in `2b0e77a`, which my Reviewer B re-run then reviewed. |
| Reviewer B | My own seat passes: pass 1 on `d27c53f`, BLOCKING; ONE remediation; re-run on `7178540`, BLOCKING again, so the second block was adjudicated at the gate (below). |

## Reviewer B pass 1 (seat), on candidate `d27c53f`

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp1.3\reviewB\`. Assertions:
- the banner reads gpt-5.6-sol / high;
- `^ERROR` 0;
- one `ERROR codex_core` hit, an echo of the brief;
- footer 1;
- 22 `succeeded in`;
- an anchored `VERDICT: NEW_CRITICAL_MAJOR_FOUND`;
- no command touched a withheld path.

| File | md5 |
|---|---|
| prompt | `6a265975706df001537dde607df8a19b` |
| diff | `eb9edb6314aacac368830985850f1e2a` |
| transcript | `a9f1f1852fd40816eb2e9619e6d144d0` |
| stderr | `f726cb11aad298af4fe5ca890d24a81a` |

| # | Finding | Disposition |
|---|---|---|
| B1 | MAJOR: the test roots fabricated the footage root under `tmp_path`; a basetemp inside the real footage folder let the synthetic tests write there. | Introduced. REMEDIATED (`7470ec8`): the real configured footage root, an autouse guard, and checked writes. See DR-21 for the residual. |
| B2 | MAJOR: the flicker clips were checked on metadata and frame 0 only, so a duplicated or dropped frame passed, and the intermediates were then deleted. | Introduced. REMEDIATED (`01784a9`): every frame of both clips is read back against its own PNG and both neighbours before any deletion. The flicker step was re-run. |
| B3 | MAJOR: a verification exception left an unverified final-named clip. | Introduced. REMEDIATED (`01784a9`, `2b0e77a`): `.partial` names, renamed only after both clips pass. |
| B4, B5, B11 | MINOR: report figures were not in any record; the safety wording's scope; the range control read one pixel per quadrant. | REMEDIATED. |
| B6 | MAJOR, out of envelope: D54's fallback is not implemented. | BANKED, DR-20(1). The report states it. |
| B7-B10 | MINOR, out of envelope. | BANKED, DR-20(2)-(5). |

## Reviewer B re-run (seat), on candidate `7178540`

Evidence `...\wp1.3\reviewB\rerun\`. Assertions:
- the banner reads gpt-5.6-sol / high;
- `^ERROR` 0;
- one `ERROR codex_core` hit, an echo;
- footer 1;
- 20 `succeeded in`;
- an anchored `VERDICT: NEW_CRITICAL_MAJOR_FOUND`;
- no withheld access (the transcript states it did not list the footage, proofs or evidence
  folders; the command grep agrees).

| File | md5 |
|---|---|
| prompt | `36ec5858b677007ed083f5d9907604e9` |
| diff | `678417335595590781557e4375a19494` |
| transcript | `280c0fa3741317fe6896a237bd470de3` |
| stderr | `b77f25dfa99f2848d522c03422e872f9` |

This is the package's SECOND blocking B. The fill allows no third remediation, so each blocking
finding is adjudicated at the gate by irreversibility.

| # | Finding | Disposition |
|---|---|---|
| 1 | CRITICAL (reasoned): `pytest --basetemp=<footage folder>` lets pytest delete and recreate that folder before the test file's guard runs; `TMP`/`TEMP` likewise. | **NOT BLOCKING for WP1.3; ESCALATED.** pytest's own temp-folder handling runs before any test code, and every `tmp_path` test in the repository already shares this exposure (WP0.2, WP1.1, WP1.2, WP1.5). It is not reachable through this package's interface: it needs an operator command that names the footage folder. WP1.3's B1 fix closes what a test file can close. The consequence is irreversible, so the fix belongs in the repo-wide `tests/conftest.py` (a `pytest_configure` guard), which this package does not own. Banked as **DR-21** and raised to CHARC for immediate commissioning. |
| 2 | MAJOR: inside `encode_clip`, a cleanup removal that raises replaces the encode or verify error. | NOT BLOCKING. It fails loudly (an exception, non-zero exit) only when a removal itself fails; it is instrument-only and reversible. DR-20(6). |
| 3 | MAJOR: earlier clips are removed only when the encode step starts, and the record writes after the rename sit outside the transaction. | NOT BLOCKING. A failed re-run exits non-zero; the delivered pack is complete and consistent (QA below); instrument-only, reversible. DR-20(7). The report's overclaiming sentence is corrected (errata). |
| 4 | MINOR: the report's WP1.4 record shape conflates the `FrameFile` attributes with the `record()` keys. | ERRATUM at the gate (text). The WP1.4 brief carries the correct keys. |
| 5 | MINOR: some report figures are not in a record (range-control errors; the one-step scale error; the MP4 md5 identity). | The md5 identity is confirmed at this seat (below). The rest is banked, DR-20(8). |
| 6 | MINOR: `means` in the report is `white_balance.channel_means` in the JSON. | ERRATUM at the gate. |
| 7 | MINOR (executed): a stray carriage return in the report's read-back path. | ERRATUM at the gate. |
| 8 | ADVISORY: tests do not pin JPEG quality, the resize call-site, extra-stream rejection or junctions. | BANKED, DR-20(9). |

**Errata at the gate.** The report was corrected in four places, text only, with no code or
record changed; it now says so in section 8. This commit carries them.

## Verification QA (orchestrator seat)

**Gate checks.** On candidate `7178540` and again on main `7178540` after `uv sync`, with the
WinGet links on PATH:

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 77 files already formatted
uv run mypy                    -> Success: no issues found in 16 source files
uv run pytest -q -rs           -> 495 passed, 1 warning (0 skipped; footage and gpu ran)
uv run pytest -q -m gpu        -> 21 passed, 474 deselected
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

The first candidate `d27c53f` was also green: 481 passed, gpu 21, harness 366. Logs are under
`work\wp1.3-mc-gate\` and `work\wp1.3-main-gate\`.

**Claims re-run against the records:**
- All 24 rows of the report's still table (pts ticks and six gains each) agree with
  `statistics.json` to the printed digit. No `bound` flag is true on any frame or variant.
- An independent `ffprobe` of both delivered flicker clips: HEVC, `yuvj420p`,
  `pc`/BT.709/BT.709/BT.709, 30000/1001, time base 1/30000, 180 frames counted by decode, one
  video stream, no audio.
- After the remediation re-run:
  - both MP4s have the same md5 as the pre-remediation copies the cell kept in
    `work\wp1.3\logs\before-remediation\`: source `0014ec998c4fc420f0b9ef1c118c98d4`,
    unsmoothed `53f8c671b1ba9831ba0143e56aa380a9`;
  - `frames`, `summary`, `bound_counts` and `excerpt` in `flicker\statistics.json` equal the
    kept copy;
  - the full read-back passes on all 180 frames of both clips. The worst difference to a
    frame's own PNG is 2.85 levels (unsmoothed) and 2.52 (source), against a limit of 3.0. The
    smallest margin to a neighbour is 7.60 and 6.41 levels.

**Witness on main.** Main's `tools/lookcheck` re-extracted two delivered stills from the
footage (`GX011628` pts 178178, `GX011627` pts 35035) into `work\wp1.3-witness\` and re-ran
the three variants on the GPU:
- the source PNG pixels are **bit-identical** to the pack's;
- all six corrected PNGs are **bit-identical** to the pack's;
- all six statistics records are identical to `statistics.json`.

Script `scratchpad\witness13.py`; result `work\wp1.3-witness\witness.json`.

**Locks:**
- Only the six owned files changed (`git diff --name-only a1c073c..28ac2de`).
- `tools/prototype/`, `pyproject.toml`, `uv.lock`, `src/` and the harness are untouched.
- The footage folder was read only.
- Every pack output is under `work\wp1.3\`.

## Follow-ons

- **DR-20:** the instrument's out-of-envelope and banked limits, D54 included. WP1.4 reads the
  same extraction path and must not take it for D54.
- **DR-21:** the repo-wide pytest temp-root guard; raised to CHARC.
- **For WP3.5 and export:** with `yuvj` formats the scaler takes the range from the pixel format;
  without `accurate_rnd`, limited range decodes about 2-3 levels dark; the encoder takes primaries
  and transfer from the frames, so `setparams` is needed. These are in the report's section 2.
- **CP2:** the pack is ready for the owner. The open-water row stays PENDING (CHARC
  `b6ca554def97ab7d`); the report's section 7 notes the blue-water `GX011628` frames.
