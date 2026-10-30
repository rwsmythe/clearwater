# WP4.4 accept record (orchestrator generation 25, 2026-10-30)

**Package:** WP4.4, `.MOV` input (spec v0.5.7 5.2 and 8.3; D25, D105, V4).
- **Commission:** CHARC `4096c6d3b96cee21`. **Brief:** `docs/briefs/wp4.4-brief.md`, FINAL on CHARC `197131faf8764ebd` (Q1-Q5).
- **Later rulings** (each quoted in the brief or the ledger):
  - round-0 GRANT `73d2797750c57625`: `tests/test_io_video_encode_units.py:80`, one token `meta` -> `gpmd`;
  - turn-2 STOP ruling `093384f126589674`: the qt fixture's audio is stereo;
  - footage STOP GRANT `9c8f461b73ec8c05`: `tools/container_spike/compare.py`, three V4 equivalences (orientation without translation; unset SAR = 1:1; mono = absent at one channel), each RED-first with planted controls. This folded the mono-layout row the turn-2 ruling had opened;
  - seat ruling (gen 24, CONFIRMED by CHARC): the footage test asserts `done with warnings` with exactly two `data track mebx`;
  - CHARC `5a8339db3b9c6b4a`: the case-only NTFS collision answered with committed tests;
  - R1 ruling `fd2269acf257054d`: a docstring-only GRANT on `src/clearwater/io/video/encode.py` `:6` and `:703`; Q-B: `verify.py`'s positional pairing is a Limit plus a row at this accept;
  - gate ruling `e3a7a4ea2dc9477f`: a GRANT on `tests/test_io_video_probe_rules.py`, the token guard ONLY (exactly one whole allowlist line exempted, with controls); re-gate = the full parallel leg plus the serial leg's two failed nodes alone; Reviewer B stands; B F5 controls fixed in the same turn.
- **Lane: CODEX**, `implementer-codex-sol-high` (`gpt-6.1-sol`/high), turns driven by `scripts/codex_cell.py`; commits made at this seat with the GPT-6.1 Sol footer.
  - Seat 1, session `01a189a6-2d4f-7052-8502-9af3dcb6a415`: turns 1-4 (round 0, build, stereo fixture, footage test); retired at 206,634 input tokens (window 258,400).
  - Seat 2, session `01a189d8-65d4-72f2-b952-bb2f40445a7e`: turns 1-3 (the compare.py equivalences; the R1 cleanup and the report; the guard exemption and B F5 controls); 100,267 at its last yield.
  - Paces: Codex 0.376 vs Claude 1.423 at seat 1's dispatch (21:51Z); 0.368 vs 1.429 at seat 2's (22:37Z).
- **Both nets** are the Claude pass (`claude-opus-5-5`/high, read-only), the other model.
- **Report:** `docs/reports/wp4.4-mov-input.md` (with its errata at the gate). **Ledger:** `docs/proofs/wp4.4-ledger.md`.

**Candidate:** `wp4.4-mc` = the author branch `wp4.4` rebased onto main `acde834` with `git -c core.autocrlf=false` (`b70efcf`), then my report errata at the gate (`b901d7f`, docs only), then seat 2 turn 3 cherry-picked (`0db74f6` = `952afd6`). `git patch-id --stable` excluding the report: `33f93664` on `5e3537d..wp4.4` and on `acde834..wp4.4-mc`.

**Footprint:**
- `src/clearwater/gui/sources.py` (`VIDEO_SUFFIXES` and docstring); `tools/headless_export.py` (its suffix set and docstring); `src/clearwater/jobs/naming.py` (the `.mov` -> `.mp4` rule and its docstrings); `src/clearwater/io/video/encode.py` (`MP4_DATA_CODEC_TAGS` and the data-track map; the granted docstrings `:6`, `:703`); `tools/container_spike/compare.py` (the three granted equivalences, with R1 F1's widening to every non-translation term);
- tests: NEW `tests/test_wp44_mov_input.py`, NEW `tests/test_container_spike_compare_equivalences.py`; new cases in `tests/test_jobs_naming.py` (plus `:64-66` per Q1); `tests/test_gui_open.py` `:93`, `:109` (Q1); `tests/test_io_video_encode_units.py:80` (one token); `tests/test_io_video_probe_rules.py` (the guard exemption and its controls);
- the brief, report, ledger and this record.

No `src/clearwater/interfaces/`, no other `io/video/` line, no `verify.py`, no `pyproject.toml` or `uv.lock` change, no new dependency. Every changed blob has 0 CR bytes. No location value, device serial or EXIF value in any committed file (the location line names keys only).

## Nets

| Net | Result |
|---|---|
| Reviewer A R1 (on `wp4.4` `d427dc9`, base `5e3537d`; `clearwater-review-evidence\wp4.4\r1\`, `md5sums.txt`, review `ff078af6`) | **NO_NEW_CRITICAL_MAJOR**: 4 minor + 5 advisory; 53 turns, model ok, worktree clean after. The case-only collision EXECUTED both orders (numbered, never overwritten). F1 (u, v, w uncompared), F3 (two stale docstrings, under `fd2269ac`), F4, F6, F9 fixed in seat 2 turn 2; F2 out of envelope -> Limit + row; F5, F7 report lines; F8 (iPhone location in the MP4) SETTLED at this seat: the source carries two location keys, the output none (key names only). **Converged at R1.** |
| **Reviewer B** (a process at this seat, on `wp4.4-mc` `b70efcf`, base `acde834`; prompt from the brief and the later rulings, without A's findings; `clearwater-review-evidence\wp4.4\reviewB\`, `md5sums.txt`) | **NO_NEW_CRITICAL_MAJOR**: 3 minor + 5 advisory; 50 turns, model ok, worktree clean after, 6 permission denials (pytest refused at its seat; it called the 33 synthetic tests directly against the candidate and the base `compare.py`). F1 (Q4 edit-list rows) and F2 (the allowlist reaches MP4 sources too) fixed as report errata at the gate (`b901d7f`; the rows extracted at this seat, format facts only). F5 fixed in seat 2 turn 3 (8 controls). F3 + F4 -> one row (CHARC). F6-F8 advisory, recorded. md5s: review `dc6273f8`, prompt `d38330c5`, diff `cb39e949`. Its verdict STANDS for the later one-file guard exemption (CHARC `e3a7a4ea`), whose diff CHARC read before the merge. |

## Gate

- **Static** on the candidate: `ruff check` clean; `ruff format --check` 273 files already formatted; `mypy` no issues in 141 source files; 0 CR bytes in every changed blob.
- **First two-leg gate** on `b901d7f` (Git Bash, `PYTEST_ADDOPTS` unset, local config copied): PARALLEL 1 failed, 5,958 passed, 1 skipped, EXIT 1, 786.21 s (00:15:59Z-00:29:08Z); SERIAL 2 failed, 1,127 passed, 10 skipped, EXIT 1, 1,722.77 s (to 00:57:53Z).
  - The parallel failure was WP4.4's: `tests/test_io_video_probe_rules.py::test_no_module_names_an_imu_gps_or_telemetry_token[encode.py]` (`['gpmd']`), the ruled allowlist line against the io/video token guard. No net had run that file. Fixed under `e3a7a4ea2dc9477f`.
  - The two serial failures are load flakes in other packages' tests, both passing alone on `b901d7f` (`2 passed in 64.57s`): `tests/test_gui_startup.py::test_shutdown_stops_every_worker_when_one_overruns_its_timeout` (WP3.16's 0.05 s timeout vs 1.0 s delay; its second failure under load -> a row, CHARC) and `tests/test_prototype_backend.py::test_bench_gpu_records_graphics_memory` (`ratio_to_gpu_pool_reserved` 0.514 < 1.0; WP-DR87's scope as an observation).
  - The serial skips: the standing look-check frames absent (the CP2 packs are archived on D:).
- **Re-gate** on `0db74f6` as ruled: PARALLEL **5,970 passed, 1 skipped (the standing swscale refusal), EXIT 0, 839.46 s** (01:07:06Z-01:21:07Z; +12 collected against the first run = the 3 guard controls, 8 F5 controls and the guard's own count); the two serial nodes alone **2 passed, EXIT 0, 65.35 s** (to 01:22:16Z). CHARC approved the guard diff before the merge (`4d5f590ed25240f1`).
- **Footage figure of record:** `tests/test_wp44_mov_input.py::test_phone_mov_runner_and_v4` on the final product code (`c804f47`): 1 passed in 65.28 s, EXIT 0 (the serial leg on `b901d7f` ran it again green).
- No harness gate (no harness file changed).

## For CHARC at the release

Owed by CHARC at this accept (its rulings): the `verify.py` positional-pairing row (R1 F2); the `test_gui_startup` overrun race row; the V4 record raw-values row (B F3 + F4); the DV/HDR fact line if warranted (the report names `IMG_6704.MOV` and `IMG_6772.MOV`, transfer `arib-std-b67`, refused by `probe.py:443-452`, from code and the inventory, not a real-file run). DR-15 stays OPEN (IMG_6702's edit-list rows are corroboration only). The bench ratio observation goes to WP-DR87's round 0.
