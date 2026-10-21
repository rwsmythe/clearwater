# WP3.12 — Accept record (proxy cache: `clearwater.cache`)

**Accepted 2026-10-21 by the orchestrator** (generation 8, session
`clearwater-orchestrator-20261020-1556`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG. Wave 2; stacked gate with WP3.6 (this package merges first).
- Brief approval and rulings: CHARC `53b752a4d7fac4fc` (ruling 1 IF-7 as amended under AD-20;
  ruling 2 lossy candidates admitted). AD-5 measured-test STOP ruled by CHARC (q75 4:4:4 JPEG
  `DEFAULT_CODEC`, Pillow to `[project]`); AD-5 wording amended on main `d971ee7` (the 10 GB bound
  read on the median frame size; N{} range of either sign). Round rulings: orchestrator
  generations 6, 7 and 8 (in the ledger); the five-round gate per CHARC `d06ed7c969d6249f`.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp3.12-brief.md` (FINAL). Spec v0.5.4, architecture FINAL 1.0, AD-5 as amended. |
| Base SHA | `2c5540a` |
| Author head | `b7d694d` (Reviewer A converged at the R5 gate; terminating cleanup `00dd29c`; ONE Reviewer B remediation `b7d694d`). |
| Cells and depth | `wp312-cell` (sonnet-high): round 0, the measured test and its STOP (depth in the ledger). `wp312-cell2` (sonnet-high): 157,637 / 40 turns at the R1 yield (00:43:29Z); 283,367 / 108 at the R4 yield (01:23:11Z, REVIEW ONLY at 269K, then stood down). `wp312-cell3` (sonnet-high, gen 8): dispatched ~02:00Z; 191,195 / 68 at the R5 yield (02:21Z); 216,373 / 82 at the window grant (03:06Z); 221,553 / 88 at the Reviewer B remediation dispatch (03:23Z); 246,012 / 98 at its last return (03:24Z). |
| Process breaches (CHARC: recorded here) | `wp312-cell2` remediated rounds 2 and 3 without yielding first (two yield breaches; both rounds' rulings were then applied in a later round), and used `git stash` four times (the stash stack is shared by every worktree; forbidden in every dispatch prompt since). |
| Merged head | `wp3.12-mc` = `b7d694d` rebased onto main `3129c17` (`a620cba`), plus this record, the report erratum and DR-41; main fast-forwarded to the commit that adds this record. CHARC held main from the gate to the release. |
| Byte identity | `git patch-id --stable` over the 34 commits: the sorted set's md5 `068af41570b785f3920d0898e5c369b9` on `2c5540a..b7d694d` and on `3129c17..a620cba`. No CR in any changed blob (`git cat-file -p`). |
| Gates on the candidate | Full pytest on the FINAL stack top `wp3.6-mc2` `1b2943e` (WP3.12 + WP3.6): **3440 passed, 2 skipped, 2 warnings (CuPy CUDA_PATH; Pillow "Corrupt EXIF data" from a WP3.6 test that plants it), 884 s, exit 0** (basetemp `work/pt-mc`); with `cupy` and `cupyx` unimportable **2922 passed, 520 skipped, 1 warning (CuPy CUDA_PATH), 598 s, exit 0** (basetemp `work/pt-mc-nocupy`). An earlier stack run on `wp3.6-mc` `97d1e9b` was STOPPED by the host's memory-pressure reaper at ~91 % of its normal leg (~03:50Z, no failure seen; it does not count); restarted one job at a time on CHARC's approval (`2e6feaf538c411f4`). The cell's own full runs on `afde3ff` (window 03:06Z): 1939 passed; 1833 passed / 106 skipped with CuPy unimportable (its base predates tranche A). Static: on `1b2943e`: `ruff check` clean, `ruff format --check` clean (155 files), `mypy` strict clean (96 source files). |
| Gates on main | Recorded in the WP3.6 accept record (`docs/proofs/wp3.6-accept.md`), the stack's top. |
| Reviewer A | gpt-5.6-sol / high, WSL, codex-cli 0.162.1, five rounds: R1 0/4/7, R2 0/2/2, R3 0/3/1, R4 0/3/1 (REVIEW ONLY), R5 0/4/4. Every R5 major is a REOPENED family, so the five-round gate CONVERGED it (CHARC: the gate reads the REOPENED column). Terminating cleanup (`00dd29c`): R5-1, R5-3, R5-4 fixed, each with a test failing on the old code; R5-6/7/8 fixed; R5-2 and R5-5 banked as report limits. Evidence `clearwater-review-evidence\wp3.12\r1`..`r5`. Ledger `docs/proofs/wp3.12-ledger.md`. |
| Reviewer B | Pass 1 on `5fc3358`: BLOCKING (B1, B2) -> ONE remediation `b7d694d` -> pass 2 on `a620cba`: BLOCKING again (B2-R), ADJUDICATED AT THE GATE (below). |

## The package

`src/clearwater/cache/` (`__init__`, `codec`, `keys`, `layout`, `store`), `tests/test_cache_*.py`
(97 tests), `tools/cache_store_test.py` (the AD-5 measured test), report
`docs/reports/wp3.12-proxy-cache.md`. `DiskProxyCache` satisfies IF-7 as amended: one append-only
pack per key folder, CRC per record, an atomic completeness marker written last, oldest-first
eviction in bytes on disk, `clear()` removing only cache-named files, crash leftovers removed or
ignored at open. `DEFAULT_CODEC = JPEG_Q75_444`; `cache_key(path)` carries `codec_cache_version`
(format number 2 plus codec identity). Pillow moved to `[project]` dependencies (CHARC grant);
`import clearwater.cache` loads no `PIL`. `interfaces/` unchanged.

## Reviewer B

Pass 1 on `5fc3358` (`clearwater-review-evidence\wp3.12\reviewB\`, md5s in `md5s.txt`;
review-B.txt `6d8b3b42e7c79e9fdd80e5607d825631`): banner gpt-5.6-sol / high; 0 `^ERROR`; 13
`succeeded in`; tokens footer; VERDICT anchored; every withheld-path mention an exclusion glob.
`NEW_CRITICAL_MAJOR_FOUND`. B1 MAJOR (`mark_complete` accepted statistics only) and B2 (a
non-registered encoder wrote under the registered version) REMEDIATED; B3 (run identity without the
float reference), B4 (guard import order), B5 (report base) fixed in the same commit. Adjudication
`reviewB\adjudication-B.md`.

Pass 2 on `a620cba` (`reviewB2\`, md5s beside it; review-B.txt md5 in `md5s.txt`): 0 `^ERROR`; 14
`succeeded in`; tokens 169,055; VERDICT anchored; exclusions only. B1, B3, B4, B5 CLOSED.
`NEW_CRITICAL_MAJOR_FOUND` on B2-R; adjudicated at the gate (`reviewB2\adjudication-B2.md`; CHARC
accepted provisionally, `ffa4852f35892897`):
- B2-R MAJOR (REOPENED B2): `id(codec.encode)` can be reused after an encoder is freed, so two
  different custom encoders in one process can share a version. Reachable only through
  non-registered (test-hook) codecs; production passes registered codecs. NON-BLOCKING, banked
  DR-41, report limit.
- B2-2 MINOR (exception precedence for a wrong-shape overlapping store) and B2-3 ADVISORY (97
  tests, not 95): errata at the gate.

## Erratum at the gate

Appended to the report: the exception-precedence sentence corrected; the test count 97; the
DR-41 limit.

## Debt

- **DR-41** NEW (above).
- Report limits (no DR): the R5-2 read-error rule, R5-5 argument order, the first-record shape
  prefix, no compaction, the 10 GB figure extrapolated from two clips, no checksum pass at open.
- Consumer notes for WP3.11/WP3.18/WP3.20/WP4.2/WP4.3 are in the report ("Differences between
  the stub and the product"); a second concurrent store on one key is a `RuntimeError`.
