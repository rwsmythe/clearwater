# WP3.13 — Accept record (output naming and safe writing: `clearwater.jobs`)

**Accepted 2026-10-20 by the orchestrator** (generation 5, session
`clearwater-orchestrator-20261020-0802`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG. Wave 1 of Phase 3.
- Brief approval and rulings: CHARC `871a371855bb1630`. Round-0 rulings (orchestrator) upheld:
  CHARC `799b83d4fe11bed8`. Round-1 temporary-name token ruling upheld: CHARC `0e0e3618be926b63`.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp3.13-brief.md` (FINAL `e357e56`). Spec v0.5.4, architecture FINAL 1.0. |
| Base SHA | `9735282` |
| Author head | `fa30c30` (Reviewer A converged at R3; terminating cleanup; report). No Reviewer B remediation. |
| Cell and depth | **`wp313-cell`** (implementer-sonnet-high): 0 at dispatch; 62,046 / 9 turns at the R0 yield; 118,143 / 28 at the build yield; 143,034 / 47 at the R1 yield; 169,145 / 63 at the R1-remediation yield; 182,256 / 77 at the R2 yield; 189,425 / 84 at the R2-remediation yield; 198,280 / 94 at the R3 yield. |
| Merged head | `wp3.13-mc` = `fa30c30` rebased onto `wp3.15-mc` `6a3ba24` (`3205cd9`), second of the stack; then rebased onto main `da54a47` after the WP3.15 accept commit (`4a570f5`), plus this record, the report erratum and DR-35. Main fast-forwarded. CHARC held main. |
| Byte identity | `git patch-id --stable` = `83cb89d887f5...` on `9735282..fa30c30`, on `4f122ec..b16e642` (the B candidate), on `6a3ba24..3205cd9` (the stack) and on the final rebase. |
| Gates on the candidate | `ruff check` clean; `ruff format --check` 72 files; `mypy` strict 50 files clean (on `b16e642`). Full pytest on the stack top `d898157`: **1671 passed, 1 warning (CuPy CUDA_PATH), 599 s, exit 0** (basetemp `work/pt-stack` in `.worktrees/wp3.7-mc`). The cell's final-head run was replaced by this gate run (orchestrator, to save a serialised window); the last run at the cell's seat was 1272 passed on `f4f14f8`. |
| Gates on main | Main is gated ONCE, at the stack's final head, after all three fast-forwards and accept commits: see `docs/proofs/wp3.7-accept.md` "Gates on main" (the intermediate heads each carried this candidate gate; CHARC `99e73cf967e2d559` accepted the stacked form). |
| Reviewer A | gpt-5.6-sol / high, WSL, codex-cli 0.162.1. R1 on `c701a04`: 1 critical / 4 major / 1 minor, all fixed (`d92ea8d`). R2 on `114b322`: 3 major / 1 minor; one major (`import clearwater.jobs` needs NumPy via `clearwater.interfaces`, `git log -S` -> `bf76136`, NumPy locked) BANKED as pre-existing and out of envelope with NO cleanup (it would bind WP3.14's IF-3 modules); two fixed (`d9562fc`). R3 on `f4f14f8`: 1 finding ruled MINOR (deliberate input only), fixed as cleanup (`fa30c30`). No reverts; every fix with a test that fails on the unfixed code. Evidence `clearwater-review-evidence\wp3.13\r1`, `r2`, `r3`. Full pytest at the cell's seat: 1252 (`c701a04`), 1270 (`114b322`), 1272 (`f4f14f8`). |
| Reviewer B | ONE pass on `b16e642`: `NO_NEW_CRITICAL_MAJOR` (2 minor, 2 advisory). |

## The package

`src/clearwater/jobs/` (`__init__`, `naming`, `safe_write`, `disk_space`) and
`tests/test_jobs_*.py`; report `docs/reports/wp3.13-naming-safe-writing.md`. Stdlib only; no
interface, pyproject or conftest change. N8's naming and safe-write half: final names per 8.3
(`_corrected`, `_2`...), the filesystem decides every "exists" (`os.path.lexists`, case folding);
the temporary `<base>.clearwater-partial-<12 hex>[.ext]` with a fresh token per write, created
empty and exclusively by `begin()`; commit = `os.link` + unlink (no window), else re-check +
`os.rename` (Windows refuses to replace); never `os.replace`; mandatory source guard
(`samefile`); a missing output folder raises `MissingFolderError` and creates nothing.

Rulings applied (orchestrator; upheld by CHARC): R0 ruling 1 (exclusive empty temporary; FFmpeg
`-y` on the temporary path, WP3.10), ruling 2 amended (no folder creation), ruling 3, ruling 4
amended (mandatory source guard). R1: the tokened temporary name (supersedes the round-0
pattern); no (st_dev, st_ino) identity check. R2: NumPy-import finding banked, no cleanup. R3:
a temporary-shaped final name counts as taken in both functions.

## Reviewer B

ONE pass (on `b16e642`). `clearwater-review-evidence\wp3.13\reviewB\review-B.txt` md5
`86856ca2fd4b6281e509c6db56765b8c`; stderr `e25136b7`; prompt `d40d60a8`; diff `feb16193`;
`md5s.txt` beside them. Assertions: banner gpt-5.6-sol / high; `^ERROR` 0; `tokens used` footer;
12 `succeeded in`; VERDICT anchored; ledger mentions are path text only (diff, report, brief).
`VERDICT: NO_NEW_CRITICAL_MAJOR`. Dispositions:
- B#1 MINOR (in envelope, REASONED): a valid suffix plus a valid stem can form a Windows reserved
  device name (`NU.MP4` + `L` -> `NUL.MP4`); the export fails, nothing is overwritten. BANKED
  (DR-35 a): the suffix and folder settings are validated where they are set (WP3.20) and at
  export start (WP3.14).
- B#2 MINOR (in envelope, EXECUTED): `Reservations` track no owner; a second, unbegun `SafeWrite`
  built on job A's plan and registry can release A's reservation (API misuse; the commit-time
  re-check still prevents an overwrite). BANKED (DR-35 b).
- B#3 ADVISORY: `remove_leftovers` deletes a live job's temporary if called while a job runs; the
  documented precondition holds it. Consumer note for WP4.3 (DR-35 c).
- B#4 ADVISORY (out of envelope): the link path falls back to re-check-then-rename on ANY
  `OSError`, so the report's "POSIX with links: no window" is too absolute. ERRATUM at the gate.

## Erratum at the gate

Appended to the report: the "POSIX with links" row holds only while `os.link` succeeds; any
`OSError` from it (not only "links unsupported") takes the re-check-then-rename fallback, whose
residual POSIX race stays under DR-16 (B#4).

## Follow-ons

- DR-35 (a)-(c) BANKED; owner CHARC; trigger: WP3.14's brief (it passes one `Reservations` to both
  `plan_output` and `SafeWrite`, validates the folder and suffix at export start) and WP4.3's
  (start-up clean-up before any job).
- Banked at R2: the `clearwater.interfaces` NumPy import (`bf76136`), out of envelope.
- Consumer notes in the report: folder validated at set and at export start; WP3.10 gives FFmpeg
  the TEMPORARY path with `-y`.
- The IF-5 `VideoSink.abort` docstring D84 -> D44/D85 at the next interface touch (ruling 13.6).
