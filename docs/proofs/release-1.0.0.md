# Clearwater 1.0.0 release record (CHARC generation 14, 2026-11-04)

The release record required by `docs/release-checklist.md` step 8. Written by
CHARC after the owner's word and the orchestrator's tag report. The tag is not
pushed; this repository is private, and any remote action needs the owner's
separate word.

## Tag

| Item | Value |
|---|---|
| Tag | `v1.0.0` (annotated, unsigned), message exactly `Clearwater 1.0.0` |
| Tagged commit | `40d2ce04` = the WP5.5 accept-record commit, the branch `wp5.5` head fast-forwarded onto `main` (the "merge commit" of checklist step 7 in the fast-forward case; the gated `--no-ff` merge `4742f69f` and the accept-time merge `d6bed59d` are its ancestors) |
| Tagger / date | Reid Smythe, 2026-11-04 05:45:31Z (Tue Nov 3 19:45:31 2026 -1000); `git cat-file -t v1.0.0` = tag; `v1.0.0^{commit}` = `40d2ce049301a9fff665c1ab36cbd5139ed33e33`, verified at CHARC's seat |
| Applied by | the orchestrator (generation 40, `clearwater-orchestrator-20261103-1316`) at the main checkout, nothing else running; report `6c80a894` |
| Owner's instruction | 2026-11-04 ~02:50Z, in chat to CHARC, verbatim: "tag 1.0.0" (relayed to the orchestrator in CHARC's post `6f4f9fa0`) |
| Push | NONE |

Commits after the tag on `main` are documentation only (the orchestrator's state
`50d51bfb`, CHARC's accept-time register / state commit `ee3a00c4`, this record, the
plan pointer and CLAUDE.md).
The product content of 1.0.0 is exactly the tree at `40d2ce04`.

## What 1.0.0 is

- Clearwater, a desktop tool (Python 3.12, PySide6, CuPy on CUDA with a CPU
  fallback, FFmpeg as a separate process) that corrects colour cast, contrast
  loss and haze in amateur underwater photos and video, built to
  `docs/underwater-correction-spec.md` v0.5.8 (decisions D1-D117; N6 set by the
  owner at about 12 min/min at 4K).
- Delivered as a repository that installs with uv (plan Phase 5, WP5.5): no
  installer, packaged executable, PyPI release or signing.
- Version `1.0.0` in `src/clearwater/__init__.py`, `pyproject.toml` and the
  installed metadata; carried in export provenance; `tests/test_version.py`.
- Licence: GPL-2.0-or-later (`LICENSE`). **N13 SATISFIED** (ruled by CHARC at
  the WP5.5 accept, post `f03da9d7`): `THIRD_PARTY_NOTICES.md` is the notice of
  record: 18 runtime distributions (the dependencies plus the gpu extra and every
  selected transitive dependency) each with its `uv.lock` version, licence,
  evidence, source URL and verdict; no INCOMPATIBLE row; 44 licence texts (35
  byte-equal to the installed files, 9 upstream at pinned tags re-verified by the
  orchestrator against the live URLs); the Microsoft Visual C++ runtime DLLs
  bundled by numpy, PySide6 and shiboken6, PySide6's Mesa `opengl32sw.dll` and
  the uv-managed CPython's bundled DLLs named per wheel. Positions of record:
  cuda-toolkit metadata-only; PySide6 / shiboken6 compatible under LGPL-3.0 (only
  QtCore, QtGui and QtWidgets are imported); FFmpeg GPL-3.0-or-later as a
  separate process on PATH, not redistributed; the MSVC runtime as platform
  runtime libraries under Microsoft's redistributable terms and the GPL's
  system-library provisions; x265 (GPLv2-or-later) attributed for pillow-heif.
- User guide `docs/user-guide.md` (installation including the lean CPU form,
  the walkthrough, known limitations including the deferred halo item DR-117);
  README application section; `docs/release-checklist.md`.

## Release gate: the figures of record

Gate `p55`, run by the orchestrator (generation 40) at its seat on candidate
`4742f69f` (the package plus main merged `--no-ff`), one leg at a time, stall
watch armed, nothing else heavy running, `PYTEST_ADDOPTS` unset,
`QT_QPA_PLATFORM=offscreen`. Full table in
`docs/reports/wp5.5-release-prep.md`, section "Release gate".

| Leg | Result | Wall |
|---|---|---|
| static | ruff clean; format 317 files; mypy clean on 158 files | - |
| collection | 8,067 = 6,787 parallel + 1,273 serial + 7 fullclip; 0 duplicates; identity exact | - |
| parallel | 6,786 passed, 1 skipped (the standing swscale refusal) | 591 s |
| serial | 1,262 passed, 11 skipped (the standing look-check frames archived to D:) | 2,053 s |
| fullclip | 7 passed | 1,583 s |
| harness | first run 2 FAILED (the three new release files unregistered as instance surface); after `8e83fa76` 382 OK, 1 skipped, on the final head `d6bed59d` and again at the accept head | - |

Between `4742f69f` and `d6bed59d` only `tests/harness/genericity_lists.py`
(outside every pytest leg) and `docs/orchestrator-state.md` changed, so the
pytest legs stand for the tagged tree. Disk: C: 39 GB free at the start,
37 GB at the end.

**Archive:** `C:\Users\rwsmy\clearwater-review-evidence\release-1.0.0\` (outside
the repository): `summary.txt`, the three logs, the three junits
(`g40-p55-*.xml`), the collection lists, the static-check outputs, the harness
outputs and `MD5SUMS.txt`. Hashes of record (from `MD5SUMS.txt`):

| File | md5 |
|---|---|
| `parallel.log` | `d4e374f232f937b56375fc61ce371c94` |
| `serial.log` | `7f2904df5bceb8840ef8df293a7341ac` |
| `fullclip.log` | `c211d119cd01f990129332a61f684ed4` |
| `harness-final.txt` | `10f087366205f37d80b2250cd72421fe` |
| `g40-p55-parallel.xml` | `4d0d4528d2556ac17a87552a8e32912f` |
| `g40-p55-serial.xml` | `93beab292d38c7c7b28dcfc22100f242` |
| `g40-p55-fullclip.xml` | `66e6b3f249bbafa04620bd9b4b53d03e` |
| `summary.txt` | `b3bf21a9ee8bc95df7cd54cfbcbc6c68` |

`harness-accept.txt` (the harness re-run at the accept head) was added after
`MD5SUMS.txt` was written; its md5 is `4531120168ce3315558773d0da5b0e3b`
(computed by CHARC 2026-11-04).

Earlier figures of record that 1.0.0 carries unchanged: V15 / V16
(`docs/reports/wp5.2-performance-memory.md`: 10.89 min/min cold median and
10.78 sustained at 4K against N6 = 12), V7 (`docs/proofs/wp4.6-accept.md`),
V2 at CP5 (`docs/proofs/cp5-visual-review.md`, 111 / 115 preferred), the
Phase 5 gate report `docs/reports/wp5.6-gate-report.md`.

## Review verdicts (WP5.5)

Both nets Claude (`claude-opus-5-5`, high), the other model from the Codex
implementer, read-only at the orchestrator's seat; accept record
`docs/proofs/wp5.5-accept.md`, ledger `docs/proofs/wp5.5-ledger.md`.

| Net | Verdict |
|---|---|
| Reviewer A r1 (`e7876912`) | NEW_CRITICAL_MAJOR_FOUND: two licence texts mis-decoded through cp1252; a wrong menu path. Fixed in `6135c496`. |
| Reviewer A r2 (`6135c496`) | NO_NEW_CRITICAL_MAJOR = CONVERGED; minors fixed in `51afce88`. |
| Reviewer B (`51afce88`) | NEW_CRITICAL_MAJOR_FOUND: the MSVC runtime and Mesa DLLs absent from the notices (B1). The single permitted remediation `795a496c` with CHARC's concurrence (`dac67830`). |
| Reviewer B re-run (`795a496c`) | NO_NEW_CRITICAL_MAJOR; minors closed in `61b1fd58`, verified at the seat. |

## Open debt carried into 1.0.0

The register `docs/debt-register.md` is the authority; every OPEN row at
`ee3a00c4` is carried. The owner acknowledged the two items that touch the
shipped look or the release itself:

- **DR-117** (halos on some high-contrast edges against open water, five CP5
  observations): investigated in WP5.7 (`docs/reports/wp5.7-halo-investigation.md`);
  the cause is the paper's global normalisation of the sharpened fusion input,
  not an implementation defect; the one change that removes them costs +13.6 %
  over N6 and softens fine texture. **Owner ruled 2026-11-03 "defer"**: 1.0.0
  ships with the shipped defaults; a Phase 6 item (an edge-aware clip inside N6
  that keeps texture). The user guide says so.
- **DR-119 (c)-(e)**, **DR-120**, **DR-116**, **DR-118**, **DR-114**: tools,
  tests and gate-cost items, none in the product's behaviour; Phase 6.
- Everything else OPEN in the register is LOW or recorded-only (limits of the
  spec's envelope, triggers not fired), unchanged by this release.

Limits of the release-preparation evidence (report, "Limits"): one Windows 11
machine class; only the named FFmpeg build (9.0.2 gyan.dev full build); the lean
GPU sync, the lean GUI and the lean video export not exercised; GUI evidence is
the offscreen start-up smoke plus source-checked guide text; the MinGW /
winpthreads version is not recorded by the wheel; the upstream-only licence
texts are dated 2026-11-03.

## Phase 5 CLOSED

Phase 5 (verification and release) closed at the WP5.5 accept (`40d2ce04`):
WP5.1, WP5.2, WP5.3, WP5.5, WP5.6 (gate report), the follow-ons WP5.7 and
WP-DR25, and WP5.8 (the DR-115 watchdog) accepted; WP5.4 not triggered. The
plan's Phase 5 completion pointer and CLAUDE.md's current state were updated with
this record. Next: WP-H1 (the harness-side cell-depth second pass, hold lifted),
then CHARC's Phase 6 proposals to the owner.
