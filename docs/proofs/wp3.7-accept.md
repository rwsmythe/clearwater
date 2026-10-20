# WP3.7 — Accept record (video probe and input validation: `clearwater.io.video`)

**Accepted 2026-10-20 by the orchestrator** (generation 5, session
`clearwater-orchestrator-20261020-0802`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG. Wave 1 of Phase 3.
- Brief approval and rulings: CHARC `871a371855bb1630` (7.3 AMENDED: untagged `yuvj` = full).
  Round-0 rulings (orchestrator) upheld: CHARC `799b83d4fe11bed8`. Round-1 reading of IF-5
  `duration_s` (container duration, exact) upheld, docstring tightened on main `4174484`
  (wording only): CHARC `0e0e3618be926b63`.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp3.7-brief.md` (FINAL `e357e56`). Spec v0.5.4, architecture FINAL 1.0. |
| Base SHA | `9735282` |
| Author head | `632e982` (Reviewer A terminated at R2; terminating cleanup; report). No Reviewer B remediation. |
| Cell and depth | **`wp37-cell`** (implementer-sonnet-high): 0 at dispatch; 90,520 / 17 turns at the R0 yield; 189,350 / 68 at the build yield; 215,371 / 86 at the R1 yield (remediation ordered below the 250K line); 246,372 / 111 at the R1-remediation yield; 259,729 / 126 at the R2 yield (past the ~250K evaluation point; only bounded steps remained: cleanup, report, final run, return report). |
| Merged head | `wp3.7-mc` = `632e982` rebased onto `wp3.13-mc` `3205cd9` (`d898157`), the top of the stack; then rebased onto main `6dd5a00` after the WP3.13 accept commit (`9157b62`), plus this record, the report erratum and DR-36. Main fast-forwarded. CHARC held main. |
| Byte identity | `git patch-id --stable` = `c3d3eae71a8e...` on `9735282..632e982`, on `4f122ec..5c05c47` (the B candidate), on `3205cd9..d898157` (the stack) and on the final rebase. |
| Gates on the candidate | `ruff check` clean; `ruff format --check` 74 files; `mypy` strict 52 files clean (on `5c05c47`). Full pytest on the stack top `d898157` (all three packages): **1671 passed, 1 warning (CuPy CUDA_PATH), 599 s, exit 0** (basetemp `work/pt-stack` in `.worktrees/wp3.7-mc`). The cell's own final-head run: 1280 passed, 533 s, exit 0 on `632e982`. |
| Gates on main | Main fast-forwarded to `9157b62` (WP3.15 `6a3ba24` + record `da54a47`, WP3.13 `4a570f5` + record `6dd5a00`, WP3.7 `9157b62`); `uv sync`; `ruff check` clean; `ruff format --check` 94 files; `mypy` strict 64 files clean; harness gate 366 OK (1 skipped); **full pytest 1671 passed, 1 warning (CuPy CUDA_PATH), 526 s, exit 0** (basetemp `work/pt-main-wave1`). This is the main gate for all three wave-1 packages. |
| Reviewer A | gpt-5.6-sol / high, WSL, codex-cli 0.162.1. R1 on `c379284`: 4 major / 2 minor, all fixed (`86c68a5`, tests `5ed305e`), each test failing on the unfixed code. R2 on `beb37a9`: 1 major adjudicated IN-RULING (`mvhd` as the primary duration source; both forms are allowed by ruling 2b and the IF-5 wording, and equal on every sample), 3 minor fixed as cleanup (`ee065b2`). Terminated at R2. Evidence `clearwater-review-evidence\wp3.7\r1`, `r2`. Full pytest at the cell's seat: 1269 (`c379284`), 1279 (`beb37a9`), 1280 (`632e982`). |
| Reviewer B | ONE pass on `5c05c47`: `NO_NEW_CRITICAL_MAJOR` (4 minor, 3 advisory). |

## The package

`src/clearwater/io/__init__.py`, `src/clearwater/io/video/` (`boxes`, `gopro`, `probe`, `inputs`)
and `tests/test_io_video_probe*.py`; report `docs/reports/wp3.7-video-probe.md`. Stdlib plus the
ffprobe 9.0.2 subprocess; no dependency, no interface change. `probe(path) -> ProbeResult` with
exact Fractions, D54 per-field defaults, HLG/PQ refused (no tail decode), rotation
counter-clockwise positive (a non-90 or mirrored matrix refused), VFR, truncation from ffprobe's
own sample-table walk, a bounded last-GOP tail check (`-read_intervals <kf>%+86400`), the
`moov/udta` GPMF settings (FMWR, PRTN, PTCL only; no `gpmd` payload, no IMU or GPS key), the
sidecar filter (D83), and the public locator `find_tool`. All eight WP2.3 video samples probe to
their manifest facts; all 35 owner clips probe with 0 faults, read-only (GX011625, 4K, 14,938
frames: 1.5 s).

## Reviewer B

ONE pass (on `5c05c47`). `clearwater-review-evidence\wp3.7\reviewB\review-B.txt`; md5s in
`md5s.txt` beside it. Assertions: banner gpt-5.6-sol / high; `^ERROR` 0; `tokens used` footer;
25 `succeeded in`; VERDICT anchored; ledger mentions are path text only; the reviewer's one
`find /mnt/c/Users/rwsmy` for executables EXCLUDED the footage and evidence folders
(`-not -path`) and printed nothing from them. 25,800 random inputs per reader raised no
unexpected exception type. `VERDICT: NO_NEW_CRITICAL_MAJOR`. Dispositions (DR-36):
- (a) MINOR in envelope: two structural log warnings interpolate `path.name` without
  `ascii_text`. BANKED.
- (b) MINOR in envelope: the manifest test checks the VFR flag and track duration, not the packet
  pts sha256 that task 8 names. BANKED as a test gap for WP3.9 (which reads every pts).
- (c) MINOR out of envelope: a partial-tag warning says "limited range" when range is explicitly
  full (the resolved data is right). BANKED.
- (d) MINOR out of envelope: an overlong box after `moov`, or 1-7 zero bytes after `moov`, are
  accepted. BANKED; report claim 10 overstated -> ERRATUM.
- (e)-(f) ADVISORY out of envelope: `_fraction` accepts decimal strings; a single-GOP file makes
  the tail check decode the whole file. BANKED.
- (g) ADVISORY: the report says "all four video samples" where the eight WP2.3 samples were read
  (seven `360360/240000`, VFR `320320/240000`). ERRATUM.

## Erratum at the gate

Appended to the report: claim 10's `BoxError` guarantee covers top-level boxes up to `moov`;
boxes after `moov` and short zero tails are not checked (B d); "all four video samples" reads
"all eight WP2.3 video samples" (B g).

## Follow-ons

- DR-36 (a)-(f) BANKED; owner CHARC; trigger: WP3.9's brief (it extends `clearwater.io.video` and
  owns the pts sequence).
- Consumer notes: WP3.9 never uses an open-ended `-read_intervals` for frame counts (19 partial
  lists in 400 runs on ffprobe 9.0.2); WP3.10, on a non-identity edit list `mvhd` and the
  longest-stream duration may differ, and `mvhd` is the presentation form (D94).
