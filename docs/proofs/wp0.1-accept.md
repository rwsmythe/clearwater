# WP0.1 — Accept record

**Accepted 2026-10-14 by the orchestrator** (session `clearwater-orchestrator-20261014-1258`),
on CHARC's commission `e6c9aa020250139a`. Gate per `docs/review-gate-clearwater.md` Part 2.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp0.1-brief.md` (FINAL + `report_version` amendment, CHARC `9fd533ea0fe6e3e8`) |
| Base SHA | `214f2b2` |
| Author head | `62c8166` (branch `wp0.1`, implementer-sonnet-high, 82K depth at round-3 dispatch) |
| Merged head | `c09f747` (branch `wp0.1-mc` = `wp0.1` rebased onto main `09706af`; main fast-forwarded) |
| Byte identity | `git patch-id --stable` of the arc diff = `0894c6ca54feba4b7ee7708af08655d562bf3aff` before (214f2b2..62c8166) and after (main..c09f747) the rebase |
| Merge integration | Main's intervening commits were docs/CLAUDE.md/.gitignore only (no file overlap); the gate below ran on the merged head itself |
| Reviewer A | Codex fast tier (gpt-5.6-luna / medium), WSL, codex-cli 0.162.1. 3 rounds: r1 BLOCKING (1 major), r2 NO_NEW_CRITICAL_MAJOR, r3 (post-B delta) NO_NEW_CRITICAL_MAJOR. Ledger `docs/proofs/wp0.1-ledger.md` |
| Reviewer B | Independent implementer-sonnet-high cell, brief `docs/briefs/wp0.1-review-brief.md`. Pass 1 on `ad1acd5`: **BLOCKING** (F1 major EXECUTED: UTF-16 config raised uncaught `UnicodeDecodeError`; F2–F5 minor). Pass 2 on `62c8166`: **NO_BLOCKING**, F1–F5 RESOLVED by reproduction; fresh Codex pass on the full arc diff (transcript md5 `003a96facc744e9de3337bd759b91807`) |
| Evidence | `C:\Users\rwsmy\clearwater-review-evidence\wp0.1\` — `r1`, `r2`, `r3` (A), `B`, `B2` (B) |

## Gate checks (orchestrator seat, merged head `c09f747`, main tree)

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 25 files already formatted
uv run mypy                    -> Success: no issues found in 3 source files
uv run pytest -q -rs           -> 40 passed in 0.52s   (0 skipped; no footage-marked tests exist yet)
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

- **Locks:** `git diff --stat main..c09f747` before the merge = exactly the 10 owned files;
  `pyproject.toml` diff = grants (a)–(d) only; `uv.lock` adds only `psutil` 7.2.2 and
  `py-cpuinfo` 9.0.0; no `wmic`/`winreg`/`shell=True`/WMI in `tools/` or `tests/` outside the
  pre-existing harness suite; nothing under the footage path written (it does not exist yet).
- **Docstrings:** ruff `D` (Google) on `tools/` and `src/` green; tests exempt by config.
- **B2 transcript assertions (re-run here, `grep -a`):** banner `gpt-5.6-luna` / `medium`;
  `^ERROR` 0; `ERROR codex_core` 0; `^tokens used` 1; `^ succeeded in` 2; anchored
  `VERDICT: BLOCKING (1, 2)` — both majors adjudicated by B and REJECTED with citations:
  (1) "working-inside-footage check is case-sensitive" — reproduced the opposite at this seat
  on Windows (`c:/footage/Work`, `c:/FOOTAGE`, `C:/Footage/../footage/x` all REJECTED,
  `C:/Work` ACCEPTED); a case-sensitive filesystem is out of envelope. (2) "conftest reads the
  real config" — mandated by the brief's Interfaces section.
- **Witness (orchestrator reality check):** `uv run python tools/environment_report.py --out <tmp>`
  on the merge candidate wrote `environment-20261014T233134Z.json`: `report_version` 1 first;
  AMD Ryzen 9 7940HS w/ Radeon 780M, 8/16 cores, 33515835392 B RAM, NVIDIA GeForce RTX 4070
  Laptop GPU, 8585740288 B, driver 610.62, Windows 11 10.0.26300, Python 3.12.13, uv 0.10.9,
  FFmpeg 9.0.2-full_build-www.gyan.dev; `unavailable` `{}`.
- **FFmpeg dev tools:** winget `Gyan.FFmpeg` 9.0.2 (full build, gyan.dev), user scope, no
  elevation; `ffmpeg`/`ffprobe` resolve via `%LOCALAPPDATA%\Microsoft\WinGet\Links` from a new shell.
- **Local config:** `clearwater.local.toml` created at accept (uncommitted, gitignored) from the
  merged template with the owner-set paths (footage `C:\Users\rwsmy\clearwater-footage`,
  working `C:\Users\rwsmy\clearwater\work`); `load_local_config()` accepts it;
  `footage_available()` is False until the footage folder exists.

## Completion report (author, condensed)

Built: template + loader + footage skip hook (b0cca2b); environment report (37af41f); A-loop
fixes (a305c85, fa4e36c); ledger (1122256); `report_version` (0fa8315, ad1acd5); B fixes
(3d12831 UTF-8 handling, 90dc168 template docs, f2a5526 key order, `--out` test, probe decoding,
exclusive create with `-N` suffix, write-error exit 2); ledger (4a57663, 62c8166). Verification
loop: 11 suspected across A r1–r3 and B pass 1; 9 confirmed and fixed; 2 rejected with cited
reason (ffprobe key not in the exact schema; conftest hook mandated); Windows path-form tests banked.
Deviation: `main()` returns 2 with a template-naming message when neither `--out` nor a valid
config is available (brief silent; accepted).

## Dispositions

| Item | Disposition |
|---|---|
| Tests for Windows-only path forms (case folding, UNC, drive-relative) | BANKED — owner CHARC; trigger: any change to `load_local_config`'s path rule. Case folding measured correct at this seat. |
| Multi-GPU: `parse_nvidia_smi` reads the first line only | BANKED (out of envelope) — owner CHARC; trigger: a second GPU on the target machine. |
| B N1: docstrings name a `-N` collision suffix the brief's filename pattern omits | DECLINED — the suffix is the orchestrator-ordered F3b hardening; the brief's pattern is the no-collision case. |
| B2 Codex finding 4: no non-string test for `working_path` | DECLINED — shared `_read_path` code path, covered by the `footage_path` case. |
| Recipe §5 `Claude-Session:` trailer absent on cell commits | BANKED — owner CHARC (doc question: the recipe asks for it; the session attribution instruction names only `Co-Authored-By`). |
| Codex sandbox could not run pytest/uv/git in r3 and B2 | Noted — those findings are REASONED; behaviour evidenced by the author's, B's and this seat's executed runs. |
| codex-cli at 0.162.1 vs 0.157.0 recorded in the fill | BANKED — owner CHARC (fill update); banner format and values re-probed and held at 0.162.1. |
| Spec §14.2 / D117 open item "CPU and graphics card" | Measured (above). A spec text change is owner-reserved — routed to CHARC. |
