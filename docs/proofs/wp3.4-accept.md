# WP3.4 accept record (orchestrator generation 10, 2026-10-26)

**Package:** WP3.4 method assembly (`clearwater.methods.ancuti_fusion`, `clearwater.methods.schema`, the registry
`available_methods`, `clearwater.core.backend_for` and the DR-37/DR-38 core fixes, `tools/core_speed.py --whole/--memory`),
brief `docs/briefs/wp3.4-brief.md` (FINAL). Four seats (implementer-opus-high): cell 1 round 0 (192,064); cell 2 build
(346,044) and full pytest (368,709); cell 3 Reviewer A R1 (98,061; 133K at the pause); cell 4 after the pause: exclusive
windows (53,053 at the close), full pytest (64,087), Reviewer B remediation (119,850). Every figure dispatcher-read at a
yield.

**Candidate:** branch `wp3.4-mc`, the author branch `wp3.4` (`1db9a43`, base `de206e2`) rebased onto main `ac4be92`
(WP3.9 underneath) with `git -c core.autocrlf=false`; 31 commits; whole-diff patch-id
`6b661264124ecb912310931863700e2c8dd3ba1d` on both `de206e2..wp3.4` and `ac4be92..5ec4442` (identical), plus one
orchestrator docs commit `c1bf077` (erratum at the gate).

**Footprint (checked at this seat):** owned files only, plus the granted edits: `backend_for` (Q2); DR-37 (b) type-only
call sites; `compensation.py` docstring-only (R1 F2: 3+/2-; the CRLF blob that commit `7089198` stored was found at
this gate and restored to LF by `478ecab`); `tests/test_core_select.py` one token (B-1); the two `__cause__` lines in
`test_methods_compensation.py` / `test_methods_fusion.py` (B-2 option A). `interfaces/`, `pyproject.toml`, `uv.lock`
untouched; every changed blob LF.

**Y-1:** the report's text is the reference; WP3.11's report carries it byte-identical (checked with `cmp`).

**Speed and memory (EXCLUSIVE window 2026-10-26 ~14:43-15:37Z, OPEN/CLOSE posted to CHARC):** memory no STOP (pool
reserved peak 1044 / 1982 MiB at 4K, 1998 / 3792 MiB at 5312 x 2988); GPU core medians c3 0.4392 s/frame (13.16
min/min), ancuti2018 0.1987 (5.96) against D106's 0.834; the CPU 10-frame subsample (708.98 / 305.70 min/min) ruled
evidence only, not the STOP (orchestrator, upheld by CHARC `fda4d203c6c0e559`). Records
`work/wp3.4/core-whole-GX011627-20261026T144318Z.json` and `...T144757Z.json`. CHARC's note for WP3.21/WP3.10: the c3
core takes 53 % of the 4K budget.

## Nets

| Net | Result |
|---|---|
| Reviewer A (cells, STRONG, codex 0.162.1 / gpt-5.6-sol high) | R1 0/0/3, terminating (F1 `c21ae64`, F2 `7089198`, F3 `fdc9f94`; `assert_same_bits` `75e04fa`); evidence `clearwater-review-evidence\wp3.4\r1` |
| Cell's windows | full pytest at `84ad0ef` 3868 passed, 2 skipped; at `877d122` no-CuPy 3316 passed, 554 skipped; CuPy 3867 passed, 1 failed (`test_footage_smoke_gx011628`, FFmpeg "Cannot allocate memory" while two other cells started; outside the diff; passed alone, 50 s) |
| Reviewer B pass 1 (this seat, `1dcfdaf`) | NEW_CRITICAL_MAJOR_FOUND; banner gpt-5.6-sol / high, read-only; 0 `^ERROR`; 18 "succeeded in"; 175,240 tokens; withheld paths only as exclusions. B1 MAJOR (bool/str/object/complex records coerced to float64 and accepted; CONFIRMED BY EXECUTION here), B2 report MINOR, B3 signed-zero wording ADVISORY -> ONE remediation `062d4d2` (dtype kind "iuf", failing first on `478ecab`), `a85f9eb` docs |
| Reviewer B pass 2 (this seat, `5ec4442`, the re-run) | NO_NEW_CRITICAL_MAJOR; banner as above; 0 `^ERROR`; 26 "succeeded in"; 224,883 tokens. Pass-1 #1 and #3 fixed; #2 REOPENED as a precision MINOR and a contamination-by-leg MINOR -> ERRATUM AT THE GATE (`c1bf077`, figures recomputed here from the record by device); a mixed list `[True, 1.0, 1.0]` passing the dtype check, OUT of envelope -> DR-46 |
| Candidate full pytest (this seat) | at `8c35149` (code = the CRLF head): 3968 passed, 2 skipped, 1600 s; at `c1bf077`: CuPy 3970 passed, 2 skipped, 1753 s, exit 0; no-CuPy 3418 passed, 554 skipped, 1211 s, exit 0 (offscreen) |
| Harness gate (this seat, `c1bf077`) | 366 OK (1 skipped) |

**Debt:** DR-19 CLOSES; DR-37 (a)(b)(d)(e) CLOSE, (c) not this package's; DR-38 (a)(b) addressed by tests, (c)(d) CLOSE;
DR-40 (a) CLOSES by test, (b) recorded from the RECORD line (fix with WP3.21); DR-13 placement only, OPEN (register rows
updated at CHARC's QA). DR-46 NEW.

**Consumer notes:** WP3.11 records are float64 from the store (its `put` now refuses dtype kinds outside "iuf", the same
rule); WP3.17 shows `blend_with_original` 0-100 with its label; WP3.14 calls `backend_for`.
