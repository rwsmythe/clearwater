# WP5.5 accept record (orchestrator generation 40, 2026-11-04)

## Package

WP5.5, release preparation for Clearwater 1.0.0:
- the third-party notices (N13);
- the user guide;
- the README application section;
- the version `1.0.0`;
- the release checklist;
- DR-119 (a)-(b), paid down.

**Brief:** `docs/briefs/wp5.5-brief.md`, FINAL by CHARC at `e2cf4752` on gen 40's fill addendum `2345f7cd`.

CHARC rulings carried by the ledger:
- Round-0 R1-R4 (`ce6094d108b9546f`):
  - R1: the cuda-toolkit metadata-only row;
  - R2: PySide6 / shiboken6 CC under LGPL-3.0;
  - R3: FFmpeg via PATH, which corrects the brief's outline 2;
  - R4: the `uv.lock` one-line grant.
- The DR-117 owner ruling "defer" (`56d6a473`): the guide says a fix is deferred to a later release.
- The B1 MSVC runtime / Mesa position (`df16a115aec924ca`): concurred, with the DLL names listed per wheel and the evidence being each wheel's `RECORD`.
- B3: guide wording only.
- B4: DR-119 (e).

**Lane: CODEX** (`implementer-codex-sol-high`, GPT-6.1 Sol / high). Paces at dispatch: Codex 22 % / 0.235, Claude 17 % / 0.766.

Three sessions:

| Session | Turns | Depth at end |
|---|---|---|
| `01a1a3b6` | turn 1, round 0 | 178,295 of 475,000 |
| `01a1a3bf` | turns 2-3 | 192,011 of 258,400 |
| `01a1a3eb` | turns 4-6 | 196,594 of 258,400 |

Each re-seat was fresh from the ledger. Both nets are Claude (`claude-opus-5-5`, high), the other model, run read-only at the orchestrator's seat.

**Records:**
- Report: `docs/reports/wp5.5-release-prep.md`.
- Ledger: `docs/proofs/wp5.5-ledger.md`.
- Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp5.5\` (`cell\` dispatches and returns 1-6; `A\r1`, `A\r2`; `B\`, `B\r2`).
- The gate's figures of record: `...\release-1.0.0\`.

## Candidate

Package commits on branch `wp5.5`:

| Commit | What |
|---|---|
| `e7876912` | the build |
| `6135c496` | the A r1 fixes |
| `51afce88` | the A r2 minors and the report |
| `795a496c` | the B remediation |
| `61b1fd58` | the B re-run minors |

- Main was merged INTO the branch `--no-ff` as **`4742f69f`** (gated) and as `d6bed59d`, so every cited hash stays reachable.
- `8e83fa76` is the orchestrator's harness registration of the three new files as instance surface; the harness gate refused them unregistered.
- **The merge to main is a fast-forward.**

**Footprint** (`git diff --name-only main...wp5.5`, plus this record):
- NEW: `THIRD_PARTY_NOTICES.md`, `docs/user-guide.md`, `docs/release-checklist.md`, `tests/test_version.py`, the report, the ledger.
- `README.md`: additions at the top only; the old text is byte-identical.
- `src/clearwater/__init__.py` and `pyproject.toml`: the version only.
- `uv.lock`: exactly the root version row (R4; blob-checked).
- `tools/export_bench.py`: `D106_MIN_PER_MIN = 12.0`, plus docstrings.
- `tests/test_export_bench.py`.
- `tools/halo_part3.py`: one line, `wholeset-list` writes LF.
- `tests/test_tools_halo_part3.py`.
- `tests/harness/genericity_lists.py`: three instance entries.

No other product code; no dependency change; `LICENSE` and the spec unchanged. Every changed blob is 0 CR.

## Result

- **Audit:**
  - 18 runtime distributions (the dependencies plus the gpu extra, Windows / CPython 3.12), each with its `uv.lock` version, licence, evidence, source URL and verdict; no INCOMPATIBLE row.
  - Python and FFmpeg rows; 43 dev / comms packages in a separate table.
  - The MSVC runtime DLLs (numpy 1, PySide6 10, shiboken6 10) and `opengl32sw.dll` named. The uv-managed CPython's bundled DLLs named.
- **Notices:** 44 licence texts.
  - 35 installed-source texts byte-equal to the installed files (Reviewer B, executed).
  - 9 upstream texts copied 2026-11-03 at pinned tags where they exist. The four whole-file upstream texts were re-verified at the seat against the live URLs (bytes and SHA-256 equal).
  - LGPL-3.0 once; the numpy / scipy / Pillow / CuPy aggregates in full.
- **Guide:** eight sections. Every menu, panel, label, setting and message was checked against the source by both nets.
- **Walkthrough as written:**
  - fixture photo (16-bit PNG, ICC, provenance `1.0.0`) and fixture video (HEVC) headless exports;
  - the offscreen start-up smoke;
  - the lean `uv sync --no-default-groups` (8 distributions);
  - the lean photo export;
  - the pinned lean environment report, run at the seat (exit 0, `unavailable` {}).
- **Version:** `1.0.0` in `__version__`, `pyproject.toml` and the installed metadata; carried in provenance. The test catches all three mutations.

## Nets

| Net | Result |
|---|---|
| Round 0 (turn 1, read-only) | STOP: 4 evidence / brief gaps, no INCOMPATIBLE row; ruled R1-R4. |
| Reviewer A r1 (`A\r1\`, on `e7876912`) | **NEW_CRITICAL_MAJOR_FOUND**. F1 MAJOR: two licence texts (NVIDIA EULA, Pillow aggregate) mis-decoded through cp1252 and hashed after the corruption. F2 MAJOR: "File > Settings" (it is Tools > Settings). F3-F6 MINOR, F7-F10 ADVISORY. All fixed but F10 (no change) in `6135c496`. |
| Reviewer A r2 (`A\r2\`, on `6135c496`) | **NO_NEW_CRITICAL_MAJOR = CONVERGED**. All 44 texts re-verified (the 9 upstream ones re-fetched). F7 reopened partial, an F8 regression; N1 MINOR ("File > Export"; the Export panel has no start button); N2-N4 ADVISORY. All fixed in `51afce88`. |
| **Reviewer B** (`B\`, on `51afce88`) | **NEW_CRITICAL_MAJOR_FOUND**. B1 MAJOR: the MSVC runtime bundled by numpy / PySide6 / shiboken6, and `opengl32sw.dll`, missing from the notices. B2 / B3 MINOR: B3 is the guide's claim that Clearwater warns on the CPU choice (it warns on automatic fall-back only). B4-B7 ADVISORY. **The single remediation** `795a496c`, with CHARC's B1 concurrence filled at the seat. |
| **Reviewer B re-run** (`B\r2\`, on `795a496c`) | **NO_NEW_CRITICAL_MAJOR**. B1-B3, B5, B6 FIXED; B7 partial. N-1 MINOR: four upstream texts carried one trailing LF and their hashes were of the padded form. N-2 MINOR: a count. N-3 MINOR: my fill attributed a broader statement to CHARC. N-4..N-7 ADVISORY. Closing tidy `61b1fd58`, verified at the seat (no further round). |

## Gate

The release gate `p55`, figures of record for 1.0.0; full table in the report's "Release gate" section.

**On `4742f69f`:**
- static clean (ruff, format 317, mypy 158);
- collection 8,067 = 6,787 + 1,273 + 7, identity exact;
- **parallel 6,786 passed / 1 skipped** (591 s);
- **serial 1,262 passed / 11 skipped** (2,053 s);
- **fullclip 7 passed** (1,583 s).

The skips are the standing ones: the swscale refusal and the look-check frames archived to D:.

**Harness:** the first run failed 2 (the unregistered release files). After `8e83fa76`: **382 OK (1 skipped) on the final head `d6bed59d`**. Between `4742f69f` and `d6bed59d` only `tests/harness/genericity_lists.py` (outside every pytest leg) and `docs/orchestrator-state.md` changed.

**Disk:** C: 39 GB free at the start, 37 GB at the end.

Logs, junits and `MD5SUMS.txt` are in `clearwater-review-evidence\release-1.0.0\`.

## Dispositions (for CHARC at this accept)

- **N13:** the notices file is ready for CHARC's SATISFIED ruling (`THIRD_PARTY_NOTICES.md`).
- **DR-119 (a)-(b):** paid down here (the constant and its tests; the LF listing and its test). (c)-(e) remain Phase 6.
- **The release record** `docs/proofs/release-1.0.0.md` is CHARC's.
- **The tag** waits for the owner's "tag 1.0.0" relayed by CHARC: `git tag -a v1.0.0 <main head after this accept> -m "Clearwater 1.0.0"`; no push.
- **Report limits carried:**
  - one machine class exercised;
  - only the named FFmpeg build;
  - the lean GPU sync, the lean GUI and the lean video export not exercised;
  - no GUI walkthrough beyond the offscreen smoke;
  - the MinGW / winpthreads version is not recorded by the wheel;
  - the upstream-only texts' copy date.
- **Seat lesson (for the harness):** a package that adds a new root or `docs/` file must register it in `tests/harness/genericity_lists.py`. The harness leg is the only one that catches it. Run the harness gate on the package head BEFORE Reviewer B next time.

## Merge

`main` fast-forwarded to the branch head (this record's commit) by the orchestrator. The worktree `.worktrees/wp5.5` is kept until the owner's word.
