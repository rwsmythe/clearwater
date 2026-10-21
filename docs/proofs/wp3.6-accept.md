# WP3.6 — Accept record (photo input and output: `clearwater.io.photo`)

**Accepted 2026-10-21 by the orchestrator** (generation 8, session
`clearwater-orchestrator-20261020-1556`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG. Wave 2, tranche B; stacked gate with WP3.12 (WP3.12 merges first; this package is the
stack's top).
- Brief approval and rulings: CHARC `53b752a4d7fac4fc` (ruling 1 amended: stdlib non-interlaced
  16-bit PNG decoder, `tifffile` granted; X-B1..X-B3; question 11 WP3.6P queued). Round-0 ruling:
  orchestrator gen 7. Item 2 (built-in ICC profiles): CHARC `d06ed7c969d6249f`, read as clarified
  by `aa1219fb3145208b` (nclx sRGB/P3 sources only; untagged keeps question 3; "no output ever
  lacks iCCP" withdrawn). Later rulings: orchestrator gen 8 (in the ledger).

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp3.6-brief.md` (FINAL). Spec v0.5.4, architecture FINAL 1.0, AD-17/AD-18 as amended, AD-24 PROVISIONAL. |
| Base SHA | `4b4da9b` |
| Author head | `404281f` (Reviewer A converged at R2; terminating cleanup `cc41451`; ONE Reviewer B remediation `1823b20..404281f`). |
| Cells and depth | `wp36-cell` (sonnet-high, gen 7): 96,178 / 18 at the R0 yield; 300,809 / 107 at its checkpoint (01:44Z, build complete). `wp36-cell2` (sonnet-high, gen 8): 116,528 / 38 at the first window request (02:06Z); 154,740 / 66 (02:09Z); 222,405 / 105 at the R1 yield (03:16Z), then stood down (the R1 remediation was a multi-finding load). `wp36-cell3` (sonnet-high): 179,295 / 84 at the R2 yield (03:30Z); 193,831 / 94 at the Reviewer B remediation dispatch (03:46Z); 236,865 / 123 at its last return. |
| Rulings at this seat that shaped the code | The built-in profile was first chosen in the READER (synthesised `icc_profile` bytes for nclx sources). That contradicts IF-1's frozen docstring ("the embedded ICC profile") and forced 11 manifest-test edits, so it was MOVED TO THE WRITER (`1c718c9`). The writer embeds a built-in profile only when `source_format == "heic"`, there is no ICC, `assumed=False`, and (primaries, transfer) is (display-p3 or bt709, srgb) (`983bff1`). An explicit-sRGB-chunk PNG keeps N-2 (no `iCCP`). Only the sRGB curve gets a built-in (nclx BT.709 transfer codes 1/6 get none). |
| Merged head | `wp3.6-mc2` = `c491c61` rebased onto the WP3.12 candidate (`wp3.6-mc` `97d1e9b`), the five B-remediation commits cherry-picked (`1b2943e`), rebased onto main after WP3.12's accept, plus this record, the report erratum and DR-42; main fast-forwarded to the commit that adds this record. X-B3: the `pyproject.toml` / `uv.lock` conflict with WP3.12 was resolved by re-running `uv lock`, with no hand merge (one `pillow` line in `[project]` citing both grants, `pillow-heif`, `tifffile` 2026.10.15 as on the author branch). |
| Byte identity | `git patch-id --stable`: 31 commits `MB..c491c61` vs `a620cba..97d1e9b`, identical except the X-B3 build commit (re-locked); the five remediation commits identical (`e6d7fdf8...` sorted-set md5) on `c491c61..404281f` and `97d1e9b..1b2943e`; the package's files byte-identical to `404281f`. No CR or NUL in any changed blob. |
| Gates on the candidate | Full pytest on the stack top `1b2943e`: **3440 passed, 2 skipped, 2 warnings, 884 s, exit 0**; CuPy unimportable **2922 passed, 520 skipped, 1 warning, 598 s, exit 0** (see the WP3.12 record for the reaped first attempt). The cell-seat window on `983bff1` (02:39Z): 3308 passed / 2 skipped; 2790 / 520 with CuPy unimportable. Static: on `1b2943e`: `ruff check` clean, `ruff format --check` clean (155 files), `mypy` strict clean (96 source files). The merged tree differs from `1b2943e` only by WP3.12's docs-only accept commit `3aaf395`. |
| Gates on main | On main `d0f00ee` (both packages merged), after `uv sync` (tifffile 2026.10.15 installed): harness gate `unittest discover -s tests/harness` **Ran 366, OK (skipped=1)**; `ruff check` clean; `ruff format --check` clean (155 files); `mypy` strict clean (96 source files); full pytest **3440 passed, 2 skipped, 2 warnings (CuPy CUDA_PATH; the planted corrupt-EXIF test), 779 s, exit 0** (basetemp `work/pt-main`). 3440 = main 2904 + WP3.12 97 + WP3.6 439. |
| Reviewer A | gpt-5.6-sol / high, WSL, codex-cli 0.162.1. R1 on `983bff1`: the reviewer reported 0/8/4; adjudicated 0 critical / 3 major / 9 minor (all NEW); #1 (HEIC `rICC`) and #5 (TIFF Interop IFD) blocking; 8 fixed, 4 banked as limits. R2 on `171332b`: adjudicated 0/0/3 minor + 1 not a finding (question 8), CONVERGED; terminating cleanup `cc41451` (WhiteIsZero grey TIFF accepted; source byte order carried). Evidence `clearwater-review-evidence\wp3.6\r1`, `r2`. Ledger `docs/proofs/wp3.6-ledger.md`. |
| Reviewer B | Pass 1 on `97d1e9b`: BLOCKING (B2, B3) -> ONE remediation -> pass 2 on `1b2943e` (first attempt reaped, restarted alone): BLOCKING again (B2-1), ADJUDICATED AT THE GATE. |

## The package

`src/clearwater/io/photo/` (`reader`, `writer`, `color`, `icc`, `exif`, `orientation`, `png`, `tiff`,
`heif_boxes`, `errors`, `p3_profile`, `srgb_profile`, `__init__`), `src/clearwater/io/__init__.py`,
`tests/test_io_photo_*.py`, `tests/test_photo_check.py`, `tools/photo_check.py`; report
`docs/reports/wp3.6-photo-io.md`. `PhotoReader` / `PhotoWriter` on IF-6 unchanged; `PhotoReadError`
(`748ac75`, X-B2) ships first so WP3.16 can catch it by name. `pyproject.toml`: `pillow` and
`pillow-heif` to `[project]`, `tifffile>=2025.1,<2027` (granted). `interfaces/` unchanged.

## Reviewer B

Pass 1 on `97d1e9b` (`clearwater-review-evidence\wp3.6\reviewB\`, md5s in `md5s.txt`): 0 `^ERROR`;
15 `succeeded in`; tokens 192,329; VERDICT anchored; 13 withheld-path mentions, all exclusion
globs. `NEW_CRITICAL_MAJOR_FOUND`. B2 MAJOR (associated TIFF alpha not un-premultiplied) and B3
MAJOR (an unparseable EXIF block kept, then re-parsed unprotected at write; TIFF lost all EXIF on
one bad IFD) REMEDIATED with B4 (truncated tiny files' kind) and B6 (`photo_check` summary keyed by
basename). B1 (`cICP`/`cHRM`/`gAMA`/TIFF colorimetry unread, read as untagged with the G10 warning
as question 3 rules) adjudicated MINOR and banked; B5 out of envelope, banked. Adjudication
`reviewB\adjudication-B.md`.

Pass 2 on `1b2943e` (`reviewB2\`; first attempt reaped ~03:50Z; restarted alone, exit 0 03:58:59Z):
0 `^ERROR`; 16 `succeeded in`; tokens 164,350; VERDICT anchored; exclusions only.
`NEW_CRITICAL_MAJOR_FOUND`; adjudicated at the gate (`reviewB2\adjudication-B2.md`):
- B2-1 MAJOR (REOPENED B2): a TIFF that is BOTH WhiteIsZero and grey with associated alpha is
  inverted including its alpha. Exotic TIFF (question 8, out of envelope). NON-BLOCKING, banked
  DR-42 (c), report limit; one-line fix at the next touch of `tiff.py`.
- B2-2, B2-3, B2-4 MINOR: errata at the gate (a HEIC cut before 8 bytes is still "unsupported";
  an unparseable EXIF block logs two warnings; the grey-ICC limit added to Limits).

## Erratum at the gate

Appended to the report (section "Erratum at the gate"): the four items above.

## Debt

- **DR-42** NEW: (a) colour descriptions other than ICC and HEIC nclx are not read; (b) IHDR
  method fields not validated (out of envelope); (c) WhiteIsZero + associated alpha grey TIFF.
- Report limits (no DR): first `ipma` box only; no pixel cap on the 16-bit PNG path; DNG walk skips
  BigTIFF; palette 16-bit map to 8 bits; grey ICC not carried; 12-bit HEIC, LZW and JPEG-in-TIFF
  refused; MakerNote survival, AD-24 and the largest-photo figures wait for WP3.6P.
- For WP3.16 (consumer): catch `PhotoReadError` by name at its rebase onto this package.
