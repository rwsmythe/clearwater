# WP4.5 accept record (orchestrator generation 23, 2026-10-29)

**Package:** WP4.5, EXIF byte fidelity through the photo writer (spec D24, D63, 8.1).
- **Commission:** CHARC `ec87b18228de2958`, on the stacked gate's red serial test `tests/test_photo_check.py::test_the_real_photo_leg_reads_and_round_trips_the_owners_photos`. The test failed on main too, so the defect was pre-existing. The trigger was the inventory's NUL-filled Make/Model/Software group of the owner's phone JPGs: one holds bytes above 0x7F in an ASCII-typed field, and Pillow's EXIF writer re-encoded them as `?`.
- **Brief:** `docs/briefs/wp4.5-brief.md`, FINAL on CHARC `f34420e1c8ff5d29`. Its Q1 was RE-RULED (b), a byte-level IFD rewrite, at the round-0 STOP (`c64900357c363330`).
- **Later rulings** (each quoted in the ledger):
  - R1 `980818fc01eb77ea` (entry-level damage dropped alone; F2-F9);
  - R2 `72fc47f6a4ecfd91` (re-seat; parse once; cut arrays keep whole entries; pointer types 3/4/13);
  - R3 `85978ce0cd76c577` (DESIGN GUARD: each carried pointer tag followed once per parent, at most four tables);
  - the test-bound erratum, ruled at this seat and concurred `d2a0f7f2db4a1302` (written entries <= 4 x len / 12 + 5).
- **GRANT:** `tests/test_io_photo_r1.py::test_a_tiff_with_an_unreadable_gps_ifd_keeps_its_other_fields` only. CHARC `1d9f88948f4350c4`, mechanism amended by `8dd13704a85f2237`: the three assertions are verbatim, and a placeholder tag 65000 is patched to a past-EOF GPS pointer 34853, with a presence assertion. Reviewer A R1 F9 and Reviewer B claim 9 both confirm the edit is within the grant.
- **Lane: CODEX**, `implementer-codex-sol-high` (`gpt-6.1-sol`/high), turns driven by `scripts/codex_cell.py`. Commits were made at this seat with the GPT-6.1 Sol footer.
  - Seat 1, session `01a18907-d527-7991-9206-583842d8187a`: turns 1-5 (round 0, build, grant, report, R1 remediation); retired at 188,902 input tokens on CHARC's R2 re-seat line.
  - Seat 2, session `01a18942-c5d9-7cf2-94f7-56cb053b33ce`: turns 1-4 (R2 remediation, R3 STOP and remediation, R4 cleanup); 185,757 at its last yield (window 258,400).
  - Paces: Codex 0.359 vs Claude 1.433 at drafting (18:55Z); 0.347 vs 1.433 at the seat-2 dispatch (20:03Z).
- **Both nets** are the Claude pass (`claude-opus-5-5`/high, read-only), the other model.
- **Report:** `docs/reports/wp4.5-exif-bytes.md`. **Ledger:** `docs/proofs/wp4.5-ledger.md`.

**Candidate:**
- Branch `wp4.5-mc` at `3e16f06` = the author branch `wp4.5` `fdf6f4e` rebased onto main `f27368b` with `git -c core.autocrlf=false`. `git patch-id --stable` is `c3872d4e` on `5a1538a..wp4.5` and on `f27368b..3e16f06`.
- The gate edits (this record, the report's Verification and errata, the brief's trailing blank line) are docs only, on top of `3e16f06`.

**Footprint:**
- `src/clearwater/io/photo/exif.py`;
- NEW `tests/test_io_photo_exif_bytes.py` (288 cases with the r1 file);
- the granted test in `tests/test_io_photo_r1.py`;
- the brief, report and ledger.

No `writer.py`, `reader.py`, `png.py`, `interfaces/`, `tools/`, `pyproject.toml` or `uv.lock` change, and no new dependency. Every changed blob has 0 CR bytes. Every test is synthetic and writes under `tmp_path`. No real photo's EXIF bytes, GPS values or MakerNote content are in any committed file.

## Nets

| Net | Result |
|---|---|
| Reviewer A R1 (on `5a57d9f`; `clearwater-review-evidence\wp4.5\r1\`, review md5 `72d16510`) | NEW_CRITICAL_MAJOR_FOUND: 3 major (entry damage condemned the IFD; type-13 carried pointers lost; D63 duplicates) + 2 minor + 4 advisory. Remediated by seat 1 under R1. |
| Reviewer A R2 (on `3020648`; review `9bb57d92`) | NEW_CRITICAL_MAJOR_FOUND: 1 major (shared children re-parsed per pointer, cubic) + 1 minor + 4 advisory. Re-seat; remediated by seat 2 under R2. |
| Reviewer A R3 (on `c7c7360`; review `8fba9d61`) | NEW_CRITICAL_MAJOR_FOUND: 1 major (distinct overlapping children, quadratic) + 1 minor + 2 advisory. DESIGN GUARD (R3); seat 2 STOPPED on the test-bound arithmetic (erratum), then remediated. |
| Reviewer A R4 (on `2923402`; review `a5c7c242`) | **NO_NEW_CRITICAL_MAJOR**: 3 advisory, cleaned up in seat 2 turn 4 (docs and docstring only). **Converged at R4.** |
| **Reviewer B** (a process at this seat, on `wp4.5-mc` `3e16f06`, base `f27368b`; prompt from the brief and the later rulings, without Reviewer A's findings; `clearwater-review-evidence\wp4.5\reviewB\`, `md5sums.txt`) | **NO_NEW_CRITICAL_MAJOR**: 2 minor + 4 advisory. Model ok, 31 turns, worktree clean after, 7 permission denials (sandbox). F1 and F4 were Limit wording, fixed in the report as errata at the gate. F2 (out of envelope) and F5 (pre-existing, out of scope) are recorded for CHARC. F3 re-measured F7. F6 is hygiene, done. md5s: review `5cd73c47`, prompt `2d0d1aa3`, diff `42ea0191`. |

## Gate (the OWNER's direction governs)

Owner, 2026-10-29 ~18:47Z, verbatim: "full re-run of the serial is not required once the issue with the round-trip test is identified and fixed and that test verifies passed (along with any test impacted by code changed by the fix)." The gate below is CHARC's form of it (`ec87b18228de2958` item 4).

- **Static** on `3e16f06`: `ruff check` exit 0; `ruff format --check` 268 files already formatted; `mypy` no issues in 141 source files; 0 CR bytes in every file of `git diff --name-only f27368b..3e16f06`.
- **PARALLEL** (`-n 4 -m "not gpu and not footage and not gui and not slow and not fullclip"`, `--basetemp=work/wp45-gate-parallel`): **5,566 passed, 1 skipped, EXIT=0, 753.34 s** (20:50:47Z-21:03:26Z). The skip is the standing `test_color_roundtrip.py:123` swscale refusal. Reviewer B ran beside it (the parallel leg has no wall-clock bounds).
- **IMPACTED SERIAL NODES** (`-m "(gpu or footage or gui or slow) and not fullclip"` over `tests/test_photo_check.py tests/test_io_photo_*.py tests/test_wp41_photo_path.py tests/test_wp41_v8.py tests/test_jobs_export_photo.py`; run after Reviewer B returned): **13 passed, 931 deselected, EXIT=0, 300.43 s** (21:03:47Z-21:08:49Z). The nodes:
  - `tests/test_photo_check.py::test_the_real_photo_leg_reads_and_round_trips_the_owners_photos` (the red test; all the owner's Phone photos);
  - `tests/test_wp41_photo_path.py::test_gpu_export_reports_gpu_and_matches_the_cpu`;
  - `tests/test_wp41_v8.py::test_v8a_job_statistics_equal_the_previews[jpeg-gradient-srgb]`, `[heic10-gradient-display-p3]`, `[large]`;
  - `tests/test_wp41_v8.py::test_v8b_k1_is_exact[jpeg-gradient-srgb]`, `[png16-lowred-srgb]`, `[large]`;
  - `tests/test_wp41_v8.py::test_v8b_planted_one_step_off_fails`, `::test_v8c_k_above_1_on_real_sized_content`;
  - `tests/test_jobs_export_photo.py::test_photo_statistics_equal_the_previews_bit_for_bit[jpeg-gradient-srgb]`, `[heic10-gradient-display-p3]`, `[large]`.
- **The red test on every remediated head** (this seat): `5a57d9f` 328.40 s, `3020648` 268.01 s, `c7c7360` 272.04 s, `2923402` 263.93 s; each 1 passed.
- **No full serial leg** (the owner). No harness gate (no harness file changed).

## For CHARC at the release

- No register row from WP4.5 (CHARC's rulings).
- **Reviewer B F2** (minor, out of envelope): `from_tiff` catches `(ValueError, struct.error)` where the base caught `Exception`. A MemoryError from a crafted TIFF of the F7 pattern now escapes `read_photo` instead of degrading to no EXIF. A row or no row is CHARC's call.
- **Reviewer B F5** (pre-existing, out of scope): a TIFF's large non-EXIF blob (Photoshop ImageSourceData 37724) is carried as EXIF into every output, before and after this package. A row or no row is CHARC's call.
- The stack (`stack-g22`: inventory + WP4.3a) now rebases onto this merge and re-runs its red (b) node.
