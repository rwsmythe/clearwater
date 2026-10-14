# WP0.1 — Repository, scaffolding and environment report (dispatch brief, FINAL)

**Status:** FINAL, issued by the orchestrator 2026-10-14 from CHARC's draft on CHARC's
commission (msg `e6c9aa020250139a`). Cell: `implementer-sonnet-high`. Worktree
`.worktrees/wp0.1`, branch `wp0.1`, base = the main commit that carries this file.

| Field | Content |
|---|---|
| ID and title | WP0.1 — Repository, scaffolding and environment report |
| Goal | Finish Phase 0 scaffolding so every later package builds, tests and lints under uv; record the laptop's hardware in the working folder. |
| Spec clauses | D93 "Distribution: free, open source, GPL-2.0-or-later"; N1 "Windows 11 officially supported; no OS-specific code"; N13 bundled licenses checked at packaging; D117 "the owner's laptop, 32 GB RAM. CPU and graphics card are to be confirmed (Section 14.2)" -- this package closes that item by reading the machine. Plan §4.1, §4.2, PD8–PD10. |
| Already done at bootstrap | Git repository + private GitHub `rwsmythe/clearwater`; `pyproject.toml` (uv, Python 3.12, ruff/mypy/pytest config, the four markers), `.python-version`, `uv.lock`, `LICENSE`, `src/clearwater/__init__.py` stub, `.gitignore` (already ignores `clearwater.local.toml`, `.codex-*`, `.worktrees/`). |
| Files owned | `clearwater.local.example.toml`, `tools/local_config.py`, `tools/environment_report.py`, `tests/conftest.py`, `tests/test_local_config.py`, `tests/test_environment_report.py`, `src/clearwater/py.typed`, `uv.lock`, `docs/proofs/wp0.1-ledger.md`; and in `pyproject.toml` ONLY: (a) the two dev-group grants below, (b) `"tools"` added to `[tool.mypy] files` (drop the trailing comment), (c) `pythonpath = ["tools"]` in `[tool.pytest.ini_options]`, (d) if and only if mypy strict rejects the untyped imports, one `[[tool.mypy.overrides]]` block naming exactly `psutil` and `cpuinfo` with `ignore_missing_imports = true`. |
| Interfaces consumed | None (no frozen interfaces exist yet). |
| Interfaces provided | See "Interfaces" below. `tools/` is NOT a package (no `__init__.py`): tools import siblings as top-level modules (`from local_config import ...`), which works both for `uv run python tools/<x>.py` and for pytest via `pythonpath = ["tools"]`. WP0.2 follows the same pattern. |
| Dependencies | None merged first. Grants (dev group ONLY, CHARC-approved): `psutil` (BSD-3) for RAM and core counts, `py-cpuinfo` (MIT) for the CPU model. Nothing else: stub packages such as `types-psutil` are new dependencies and OUT of envelope. |
| Tests | `tests/test_local_config.py`, `tests/test_environment_report.py` (roster below). All non-hardware; feed no V test. |
| Hardware flags | None. |
| Out of scope | Choosing the product's video library (FFmpeg is a dev tool here; D104 decides at the container spike); any `src/clearwater` module beyond `py.typed`; the inventory tool (WP0.2); CI; creating `clearwater.local.toml`; guessing the owner's paths; any edit to `tests/harness/`, `scripts/`, `.claude/`, kernel docs, `.gitignore`, `CLAUDE.md`. |
| Done | Plan §4.5, plus: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run pytest` green on the final head; harness gate `uv run python -m unittest discover -s tests/harness` still green; the return report names the FFmpeg build and version installed. |

## Interfaces

`tools/local_config.py`

- `class LocalConfigError(Exception)` -- every message names `clearwater.local.example.toml`.
- `@dataclass(frozen=True) class LocalConfig` with `footage_path: Path`, `working_path: Path`.
- `default_config_path() -> Path` -- `<repo root>/clearwater.local.toml`, repo root located
  from this file's own location (never the current working directory).
- `load_local_config(path: Path | None = None) -> LocalConfig` -- parses TOML with stdlib
  `tomllib`. Raises `LocalConfigError` when: the file is missing; it is not valid TOML; a key
  is missing or not a string; a path is relative (rejected, never resolved against cwd); or
  `working_path` equals or lies inside `footage_path` (plan §4.2). Does NOT require either
  path to exist.
- `footage_available(path: Path | None = None) -> bool` -- True only when the config loads
  and `footage_path` is an existing directory; never raises.

`tests/conftest.py` -- `pytest_collection_modifyitems` adds a skip (reason names the config
template) to every `footage`-marked test when `footage_available()` is False.

`tools/environment_report.py` -- `main(argv: list[str] | None = None) -> int`; options
`--config PATH` (override the config path) and `--out DIR` (override the working folder; when
given, the config is NOT read, so the tool runs with no local config). Writes
`<working>/reports/environment-<YYYYMMDDTHHMMSSZ>.json` (creates `reports/`), prints the path,
returns 0. JSON keys, exactly:

| key | source |
|---|---|
| `report_version` | integer `1`, first key (amended 2026-10-14 on CHARC's advisory, msg `9fd533ea0fe6e3e8`) |
| `timestamp_utc` | ISO 8601 with `Z` |
| `cpu_model` | `cpuinfo.get_cpu_info()["brand_raw"]` |
| `cpu_physical_cores`, `cpu_logical_cores` | `psutil.cpu_count(logical=False/True)` |
| `ram_total_bytes` | `psutil.virtual_memory().total` |
| `gpu_model`, `gpu_memory_bytes`, `gpu_driver_version` | `nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits` via `subprocess` (no shell); first line only; memory is MiB -> bytes |
| `os_name`, `os_release`, `os_version` | `platform.system()`, `platform.release()`, `platform.version()` |
| `python_version`, `python_executable` | `platform.python_version()`, `sys.executable` |
| `uv_version` | first line of `uv --version` |
| `ffmpeg_version` | first line of `ffmpeg -version` |
| `clearwater_commit` | `git rev-parse HEAD` run in the repo root |
| `unavailable` | object mapping each null field's key to a one-line reason; `{}` when none |

Any probe that fails (tool absent, non-zero exit, unparsable output, timeout) sets its field(s)
to `null` and records the reason in `unavailable`; the report is still written. No `wmic`, WMI,
registry, or `shell=True` (N1). Every subprocess call has a timeout.

## Required end state (the claim list Reviewer B checks first)

1. `clearwater.local.example.toml` exists with `footage_path` and `working_path`, each
   documented inline (footage read-only; working folder outside the footage folder and outside
   version control), and it loads through `load_local_config` once its placeholder paths are
   replaced with absolute paths.
2. `uv run python tools/environment_report.py --out <dir>` writes the JSON above and prints its
   path; with a filled `clearwater.local.toml` and no `--out`, it writes under `working_path`.
3. Graphics data degrades to `null` + reason when `nvidia-smi` is absent; no OS-specific API.
4. FFmpeg CLI tools are installed as development tools and `ffmpeg -version` / `ffprobe
   -version` resolve; the version is in the cell's own report run and in the return report.
5. Google-style docstrings on every public function, class and module; mypy strict passes on
   `src/clearwater` and `tools`.

## Test roster

`tests/test_local_config.py`: the committed template parses once its placeholders are replaced
(write a tmp copy with absolute tmp paths); missing file, invalid TOML, missing key, non-string
value, relative path, and working-inside-footage each raise `LocalConfigError` whose message
names the template; `footage_available` is False for a missing config and for a missing footage
directory, True for an existing one.

`tests/test_environment_report.py`: `main(["--out", tmp])` returns 0 and writes exactly one
`reports/environment-*.json` with every key above; with `nvidia-smi` stubbed absent
(`FileNotFoundError` from the subprocess layer) the three gpu keys are `null` and `unavailable`
names them; a stubbed nvidia-smi line parses to the right model / bytes / driver; a stubbed
`ffmpeg` failure yields `ffmpeg_version: null` with a reason. Stub `cpuinfo` (it is slow) in
every test. No test touches the real config or the owner's paths.

## FFmpeg install

`winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements`
(winget is present on this machine; FFmpeg is not installed as of dispatch). If the install
needs an elevation prompt, fails, or `winget` misbehaves: STOP and return with what you found.
Your process PATH predates the install; to verify, read the User PATH from the registry ONLY for
verification (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','User')"`)
and run your end-to-end report with PATH extended accordingly. Name the build and version
(first line of `ffmpeg -version`) in the return report.

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- Tier: **fast** (tools with no shipped output). Transport: **WSL** (pinned). Per-call flags,
  never `-p`: `-m gpt-5.6-luna -c model_reasoning_effort=medium -s read-only --skip-git-repo-check`.
  Banner assertion: `gpt-5.6-luna` / `medium`.
- Diff Windows-side: `git -C <worktree> diff -U8 <base>..HEAD > <scratch>/.codex-wp0.1-diff.txt`.
  WSL never runs git. Invocation shape (stage the prompt in a file; cwd = the worktree so Codex
  can read it):
  `wsl.exe bash -ilc 'export PATH="$HOME/.local/node22/bin:$PATH"; cd /mnt/c/Users/rwsmy/clearwater/.worktrees/wp0.1 && cat <prompt> <diff> | codex exec -m gpt-5.6-luna -c model_reasoning_effort=medium -s read-only --skip-git-repo-check - > <transcript> 2>&1'`
  (WSL paths for the scratch files). Cross-check any line-ending finding against Windows
  `git diff --numstat`.
- Before round 1: a one-command probe through this exact invocation; require one
  `^ succeeded in` line.
- Prompt contents per the fill: the claim list above, the operating envelope below with a
  request to TAG out-of-envelope findings, `CORRECTNESS REVIEW` / `WHAT TO EXAMINE` framing,
  the read-only-sandbox EXECUTED/REASONED paragraph verbatim from `docs/codex-reviewer.md`, and
  "report every finding with a severity tag".
- Per-round assertions (all `grep -a`): banner; `^ERROR` and `ERROR codex_core` classified by
  provenance; `^tokens used` footer; anchored VERDICT; `^ succeeded in` >= 1.
- Convergence: a round with zero NEW blocking (critical/major, in envelope) ends the loop;
  minors fixed once in that round's cleanup. FIVE_ROUND_GATE: at round 5, yield with the ledger.
- Evidence: copy each round's prompt, diff, transcript and adjudication to
  `C:\Users\rwsmy\clearwater-review-evidence\wp0.1\rN\` with md5s. Ledger at
  `docs/proofs/wp0.1-ledger.md` (per round: severity counts, in/out envelope, NEW/REOPENED,
  reverts, product vs test-only fixes, transport + CLI version; leave the depth column for the
  dispatcher), committed in your worktree before you return. Delete `.codex-*` staging files at
  teardown.

## Declared operating envelope

Windows 11 laptop, one NVIDIA card or none, Python 3.12 under uv, `nvidia-smi` and FFmpeg
present or absent. Findings reachable only on other operating systems or with multiple GPUs are
out of envelope: banked, not loop-driving.

## Notes for the cell

- Run `uv sync` in the worktree first. Absolute paths or `git -C`; never a bare `cd`.
- Commit by pathspec, conventional commits `feat(wp0.1): ...` / `test(wp0.1): ...`, with the
  `Co-Authored-By:` attribution footer naming your own model (`<noreply@anthropic.com>`).
- STOP and return (do not work around) on: any dependency beyond the two grants, any need to
  edit a file not owned above, an ambiguity in this brief or the spec, winget/elevation trouble.
- Return report = your FINAL message (you are a subagent; it reaches the orchestrator
  directly). Contents per `docs/dispatch-recipe.md` §4 and plan §4.5 item 6: per-commit change
  list, validation output lines read off the final head (ruff, ruff format, mypy, pytest with
  pass/skip counts, harness gate), the verification-loop record, review rounds + verdict +
  ledger path + evidence folder, each lock stated as honored, the FFmpeg build/version, the
  end-to-end report path and that it used `--out <tmp>`, and every deviation or open question.
