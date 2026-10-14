# WP0.1 — Repository, scaffolding and environment report (dispatch brief, DRAFT)

**Status:** draft by CHARC, 2026-10-14. Dispatch waits on the owner's two paths
(footage folder, working folder) only for the end-to-end run; everything else can
start. The orchestrator issues the final brief in the plan's section 4.6 format.

| Field | Content |
|---|---|
| ID and title | WP0.1 — Repository, scaffolding and environment report |
| Goal | Finish Phase 0 scaffolding so every later package builds, tests and lints under uv; record the laptop's hardware in the working folder. |
| Spec clauses | D93 (license), N1 (portability), N13 (license check at packaging); plan §4.1, §4.2, PD8–PD10; spec §14.2 open item "laptop CPU and graphics card". |
| Already done at bootstrap | Local git repository and the private GitHub repository `rwsmythe/clearwater`; `pyproject.toml` (uv, Python 3.12, ruff/mypy/pytest config with the four markers), `.python-version`, `uv.lock`, `LICENSE` (GPL-2.0-or-later text), `src/clearwater/__init__.py` stub, `.gitignore` rules for the local config and caches. |
| Files owned | `pyproject.toml` (the dependency grants below and adding `tools` to `[tool.mypy] files` only), `uv.lock`, `clearwater.local.example.toml`, `tools/local_config.py`, `tools/environment_report.py`, `tests/conftest.py`, `tests/test_local_config.py`, `tests/test_environment_report.py`, `src/clearwater/py.typed`. |
| Interfaces consumed | None (no frozen interfaces exist yet). |
| Interfaces provided | `tools/local_config.py`: `load_local_config(path: Path | None = None) -> LocalConfig` with fields `footage_path: Path` and `working_path: Path`; a missing file or missing key raises a clear error naming the template. The `footage` pytest marker skips when the footage path is absent (`tests/conftest.py`). |
| Dependencies | None merged before it. Dependency grants (dev group only, not product): `psutil` (BSD-3) for RAM, `py-cpuinfo` (MIT) for the CPU model. No product dependency. |
| Tests | `tests/test_local_config.py` (template parses; missing file/key errors name the template; paths are absolute). `tests/test_environment_report.py` (runs the report into a tmp working folder; the JSON carries every field below; the graphics fields degrade to `null` with a reason when `nvidia-smi` is absent, exercised by stubbing the command). All non-hardware. |
| Hardware flags | None. (The report itself reads the real machine when the owner runs it; the test uses a tmp folder and stubs.) |
| Out of scope | The product's video library choice (FFmpeg here is a development tool only, plan §6 WP0.1); any `src/clearwater` module beyond `py.typed`; the inventory tool (WP0.2); CI. |
| Done | Plan §4.5, plus: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run pytest` all green on the final head; the harness gate `uv run python -m unittest discover -s tests/harness` still green; the completion report names the FFmpeg build and version installed. |

## Required end state (the claim list Reviewer B checks first)

1. `clearwater.local.example.toml` exists with `footage_path` and `working_path`
   keys, both documented inline (read-only footage; working folder outside the
   footage folder and outside version control); `clearwater.local.toml` is
   gitignored (already in `.gitignore`).
2. `uv run python tools/environment_report.py` (with a filled local config) writes
   `<working_path>/reports/environment-<UTC stamp>.json` and prints its path. The
   JSON records: CPU model, physical and logical core counts, total RAM (bytes),
   graphics card model, dedicated graphics memory (bytes), driver version, Windows
   version and build, Python version and executable, uv version, FFmpeg version
   (or `null` with a reason), the Clearwater commit SHA, and the timestamp.
   Invocation path: the script's `main()`; `--config` overrides the config path;
   `--out` overrides the working folder for tests.
3. Graphics data comes from `nvidia-smi --query-gpu=name,memory.total,driver_version
   --format=csv,noheader,nounits` run through `subprocess` (portable invocation;
   degrades to `null` with a reason when the tool is missing). No `wmic`, no WMI,
   no registry access (N1).
4. FFmpeg command-line tools (`ffmpeg`, `ffprobe`) are installed as development
   tools (`winget install Gyan.FFmpeg` is the proposed route) and `ffprobe
   -version` resolves from a fresh shell; the version is recorded in the report
   and the completion report. This is not a decision on the product's video
   library (D104 decides that at the container spike).
5. Every public function, class and module has a Google-style docstring; `mypy`
   strict passes on `tools/` and `src/clearwater`.

## Declared operating envelope (for the review loop)

Windows 11 laptop, one NVIDIA card or none, Python 3.12 under uv, `nvidia-smi`
present or absent. Findings reachable only on other operating systems or with
multiple GPUs are out of envelope: banked, not loop-driving.

## Notes for the cell

- Run `uv sync` first; commit by pathspec; do not touch `tests/harness/`.
- The owner may not have supplied the real paths when you run: use `--out` with a
  tmp folder for your own end-to-end run and say so in the report; the owner runs
  the real report once `clearwater.local.toml` is filled.
- STOP and ask if `winget` is unavailable or FFmpeg installation needs an
  elevation prompt you cannot answer; report what you found.
