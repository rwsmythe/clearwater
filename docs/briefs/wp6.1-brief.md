# WP6.1 — Packaging spike (Windows): one-folder and one-file forms, the GPU pack from a per-user folder (dispatch brief, FINAL)

**Status:** FINAL 2026-11-04 ~08:30Z by CHARC (generation 14) on gen 40's dispatch fill `dadf3013`, with Q5 and Q6 ruled below (the fill's last bullet) and design item 3 corrected. Earlier: DRAFT 2026-11-04 by CHARC (generation 14) on the owner's Phase 6 ruling (`docs/briefs/phase6-proposal.md`, D-B spike, D-C amended to the on-demand GPU download, D-D bundle FFmpeg). The orchestrator fills the dispatch section after the owner-approved prune (the builds need the disk); CHARC marks it FINAL. Spike: evidence, not product. Owner decisions inside the package: none (the owner picks the artifact shape at CP6a from this package's figures).

| Field | Content |
|---|---|
| ID and title | WP6.1 — Packaging spike: a PyInstaller build of Clearwater 1.0.0's tree in the one-folder and the one-file forms, measured; the GPU pack (CuPy + the CUDA wheels) loaded at run time from a per-user folder, proved in the frozen build; the report that CP6a reads |
| Lane | **Claude opus-high** (`implementer-opus-high`): PyInstaller hooks for PySide6, hidden imports and the frozen `sys.path` are reasoning-dense. Reviewer A = Codex at the cell's seat; Reviewer B = Codex at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp6.1\`. |
| Tier and size | STANDARD. Size S (one build script, one loader module, one report). Evaluate at about 250K, STOP near 400K. |
| Base | main after the prune. Worktree `.worktrees/wp6.1`, branch `wp6.1`. Builds and timings under `work/wp6.1/` (gitignored); at least 25 GB free before each build. |
| Goal | Facts for CP6a: for each form (one-folder; one-file self-extracting), the zipped size, the unpacked size, the cold start to the first window, the warm start, and the time to the first photo export, on the owner's laptop; whether every PySide6 plugin, the HEIC / TIFF / ICC / EXIF paths, the write journal and the spawned export worker (AD-23, AD-31: a frozen `multiprocessing` spawn must re-enter the frozen executable, not a Python interpreter) work from the frozen build; and the GPU pack mechanism proved: with CuPy and the CUDA wheels installed into a per-user folder (outside the bundle), the frozen application finds them, the CUDA path runs an export, and without the folder the CPU path runs with the D111 message, unchanged. |
| Sources | `src/clearwater/` at 1.0.0 (`__main__`, `app/`, `jobs/export_process.py`, `io/`), `pyproject.toml` and `uv.lock` (the pinned versions of `cupy-cuda12x` and every `nvidia-*` wheel are THE versions of the pack), `tools/environment_report.py`, the owner's reference build `rwsmythe/TTS160-Alpyca` (`TTS160_pyinstaller`: `PyInstaller.__main__.run([...])`, data files copied beside the executable), PyInstaller's PySide6 hook documentation. |
| Files owned | NEW `tools/package/build.py` (the build script: both forms from one spec, `--onefile` / `--onedir`, the exclude list, the version from `clearwater.__version__`, output under `work/wp6.1/dist-<form>/`); NEW `tools/package/README.md`; NEW `src/clearwater/gpu_pack.py` (the loader: the per-user folder `%LOCALAPPDATA%\Clearwater\gpu-pack\<lock-version-stamp>\site-packages`, an integrity manifest check, `sys.path` insertion BEFORE the first `cupy` import, a one-line report of what was found; NO download code in this package: the downloader is WP6.3's); the one call site that wires the loader before backend detection (name it in round 0; expected `src/clearwater/__main__.py` or the composition root); `tests/test_gpu_pack.py` (the loader against synthetic folders under `tmp_path`: found / absent / wrong stamp / tampered manifest); report `docs/reports/wp6.1-packaging-spike.md`. |
| NOT owned | Every other product file; `pyproject.toml` and `uv.lock` (PyInstaller is a `dev` group addition: STOP to CHARC with the version for the N13 check before adding it; expected GPL-2.0-with-bootloader-exception, compatible); the GUI (no new panel: the loader's one-line report goes to the existing start-up log); the spec; FFmpeg bundling (the spike copies the laptop's FFmpeg beside the executable to prove the PATH-less run, and the report states the licence consequence; the real bundle rule is WP6.3's). |
| Locks | The product's behaviour is unchanged when no pack folder exists (the 1.0.0 tests stay green: the loader is a no-op then). Frozen interfaces IF-1..IF-10 untouched. The pack folder is READ-ONLY to the loader. No network access anywhere in this package. Every timing on the owner's laptop, nothing else heavy running (exclusive), three runs each, median reported with the spread. 0 CR blobs; Google docstrings; ruff / mypy on `src` and `tools`. |
| Markers | `tests/test_gpu_pack.py` parallel-leg (synthetic, under a second). No new serial test. The frozen-build checks are the report's, run by hand at the cell's seat and recorded with their commands; not pytest. |
| Hardware flags | EXCLUSIVE for the timing runs (start-up and first export). The GPU pack proof needs the laptop's NVIDIA card. |
| Out of scope | The downloader (WP6.3); the GitHub Actions workflow (WP6.3); macOS (WP6.2 / WP6.4); code signing; an installer; any change to the correction; the Qt plugin set beyond what the application loads today. |
| Debt and decided items | At the accept CHARC records: the PyInstaller dependency row (N13), the chosen form's figures in the spec's N14 (at CP6a), AD-33 "GPU pack loader" (the folder layout, the stamp rule, the manifest) and AD-34 "frozen spawn re-entry" if the export worker needs a `multiprocessing.freeze_support()` or equivalent. Any frozen-build failure that is a product defect (not a packaging matter) = a DR row, not a fix here. |
| Done | Both forms build from the script on the laptop and start; the measured table (size, cold / warm start, first export) for both forms; the frozen export worker exports the fixture video and the fixture photo (HEIC in, PNG and JPEG out, EXIF carried: the WP4.5 round trip on the fixture); the GPU pack proof (with the folder: CUDA path, an export, the loader's line; without: the CPU path, D111's line); the loader's tests green; the 1.0.0 gate legs touched by the loader call site green (parallel + the serial tests of the start-up path); the report with a RECOMMENDATION for CP6a (one form, with reasons) and the failure list; Reviewer A converged; Reviewer B clean. |

## The design (fixed where it is; the cell proposes the rest in round 0)

1. **One spec, two forms.** `tools/package/build.py --form onedir|onefile` builds `Clearwater-<version>-windows-<form>` under `work/wp6.1/`. Entry point `clearwater.__main__`. Data: the Qt platform plugin set the application loads, the ICC profiles the photo path reads, nothing from `work/` or the footage. Excludes: `tests`, `tools` (except the package's own), `cupy` / `nvidia` (NEVER in the bundle, by the owner's D-C amendment), the dev and comms groups.
2. **The GPU pack loader** (`src/clearwater/gpu_pack.py`): at start-up, before the backend probe, if `<pack root>/<stamp>/manifest.json` exists and lists the expected wheels at the lock's versions with matching hashes of their `RECORD`-level content, insert `<pack root>/<stamp>/site-packages` at the front of `sys.path` and log one line (`gpu pack <stamp>: loaded` / `absent` / `rejected: <reason>`). The stamp is the lock's `cupy-cuda12x` version plus the CUDA major (`14.2.0-cu12`). A rejected or absent pack = the CPU path, exactly 1.0.0's behaviour. For the spike the folder is filled by hand with `uv pip install --target` of the lock's wheels and a manifest written by a helper in `build.py`; the WP6.3 downloader will write the same layout.
3. **Frozen spawn.** *(Corrected at FINAL, Q5: the worker is a `subprocess.Popen` of `[sys.executable, "-m", "clearwater.app.export_worker"]` built in `app/composition.py`, not a `multiprocessing` spawn; `freeze_support()` does not apply.)* The export worker is a spawned process (AD-23 / AD-31). In a frozen build `sys.executable` is the bundle's executable: the spawn must re-enter it with the worker entry selected (PyInstaller's `multiprocessing.freeze_support()` pattern or the helper's own `-m`-free re-entry). Round 0 names the exact mechanism; a change inside `jobs/export_process.py` or the AD-23 helper is a STOP to CHARC before it is made.
4. **Measurements.** Cold start = first launch after a reboot or a dropped file cache (state the method); warm = the second launch; first export = the fixture photo through the GUI's export path, headless where the runner allows. Three runs each.
5. **FFmpeg beside the executable** for the PATH-less proof only; the report records the binary's version, build and licence, and that the real bundle rule is WP6.3's.

## Questions (CHARC's recommended answers)

- **Q1 PyInstaller version.** Recommended: the current release at dispatch, pinned in the `dev` group after CHARC's N13 row (GPL-2.0-or-later with the bootloader exception: compatible; the bootloader is not a derived work of the application under its exception).
- **Q2 Where the loader runs.** Recommended: the first lines of `clearwater.__main__` (before any `clearwater.core` import that touches CuPy) and the same call at the top of the export worker's entry (a spawned process starts a fresh interpreter).
- **Q3 One-file temp folder.** Recommended: PyInstaller's default (`_MEIxxxx` under `%TEMP%`); the report measures its extraction time and size and states the disk it needs; no custom runtime folder in the spike.
- **Q4 What CP6a sees.** Recommended: the report's one table plus two screenshots (the first window from each form); CHARC presents it to the owner.

## Completion report (`docs/reports/wp6.1-packaging-spike.md`)

The build commands; the measured table (both forms); the plugin / path check list with pass or fail; the GPU pack proof's commands and lines; the frozen spawn mechanism; the exclude list and the bundle's manifest size by top-level folder; the failures and what they imply for WP6.3; the recommendation for CP6a; limits (one machine; the laptop's FFmpeg; the hand-filled pack).

## Yields and depth

Turn 1 = round 0 (read the entry points, the spawn helper, PyInstaller's hooks; the build plan; Q1-Q4; the PyInstaller N13 STOP) and YIELD; turn 2 = the script, both builds, the plugin / path checks, YIELD for Reviewer A; turn 3 = the loader + tests + the pack proof; turn 4 = the timings (exclusive window) and the report; the nets.

## Orchestrator dispatch fill (for CHARC to finalise)

- Lane paces at dispatch; base commit (after the prune); worktree; evidence folder; disk free before each build (25 GB floor).
- GATE_CHECKS: parallel leg + the serial tests of the start-up path on the final candidate; `ruff` / `mypy`; `git diff --name-only main` = the owned paths; the loader is a no-op on the gate machine (no pack folder present during the gate).

## Dispatch fill (orchestrator gen 40, 2026-11-04 ~08:20Z; after the prune)

This section fills the one above. Where it differs from the table, the design or the questions, it governs once CHARC marks it FINAL. Corrections to the brief's text are marked **[corr]**.

- **Precondition met.** The owner-approved prune is done (record `031c7cb8`). Nothing runs: no cell, no gate, no pytest. C: has **97 GB free**, well over the 25 GB floor per build. `df -h /c` is read before each build and each timing window.
- **Base, worktree and evidence.**
  - Base = main at dispatch: `031c7cb8` plus this fill's commit and CHARC's FINAL.
  - Worktree `.worktrees/wp6.1`, branch `wp6.1`, with `clearwater.local.toml` copied in (FFmpeg location and the footage guard).
  - Builds, packs and timings go under the worktree's `work/wp6.1/`.
  - Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp6.1\` (`cell\`, `A\`, `B\`, `gate\`, `timings\`). The report's figures are copied there before the merge, because a later prune deletes `work/`.
- **Lane paces at 08:17Z.**
  - Codex: 23 % used, pace 0.233. The window resets at 10:07Z.
  - Claude: 22 % used, pace 0.799.
  - The brief's lane stands: **Claude opus-high** (`implementer-opus-high`, an Agent-tool subagent at my seat, a FRESH cell). The work is reasoning-dense (PyInstaller hooks, the frozen `sys.path`, the spawn).
  - WP6.2 and WP-T8 go on Codex, which balances the lanes.
  - **Reviewer A** = a Codex pass (`codex exec -p strong -s read-only`, the WP5.7 form). **Reviewer B** = the WSL Codex script at my seat (the WP5.7 B form). In both nets the reviewer is the other model.
  - Cell depth is read with the new `scripts/cell_depth.py --agent <name>` at every yield: evaluate at about 250K, STOP near 400K.
- **The GPU pack contents, read from `uv.lock` at the base.** These distributions, at these versions, are the pack (NEVER in the bundle, per D-C):
  - `cupy-cuda12x` 14.2.0
  - `cuda-pathfinder` 1.8.3
  - `cuda-toolkit` 12.9.2.0 (a metadata-only meta-package, per WP5.5's R1)
  - `nvidia-cublas-cu12` 12.9.2.10
  - `nvidia-cuda-nvrtc-cu12` 12.9.86
  - `nvidia-cuda-runtime-cu12` 12.9.79
  - `nvidia-cufft-cu12` 11.4.1.4
  - `nvidia-curand-cu12` 10.3.10.19
  - `nvidia-cusolver-cu12` 11.7.5.82
  - `nvidia-cusparse-cu12` 12.5.10.65
  - `nvidia-nvjitlink-cu12` 12.9.86

  The design's stamp `14.2.0-cu12` matches the lock. `numpy` is shared with the bundle and is NOT duplicated in the pack. Round 0 confirms that list against `importlib.metadata` in the worktree's environment and names any transitive dependency missing from it.
- **[corr] The frozen spawn (design item 3) is NOT a `multiprocessing` spawn.**
  - The export worker is a `subprocess.Popen` of a command built at `src/clearwater/app/composition.py:461`: `[sys.executable, "-m", "clearwater.app.export_worker"]`, unless a command is injected, which tests do.
  - `jobs/export_process.py` only runs the command it is given (`:224`, `:292`).
  - In a frozen build, `sys.executable` is `Clearwater.exe`, which ignores `-m`, so the worker would start a SECOND GUI. `multiprocessing.freeze_support()` does not apply.
  - **Q5 (new; CHARC to rule at FINAL).** Recommended: a frozen-aware worker command and an argv dispatch in the entry.
    - (a) `composition.py:461` builds `[sys.executable, "--export-worker"]` when `getattr(sys, "frozen", False)`, and the unchanged `-m` command otherwise. That is one expression and its docstring.
    - (b) `src/clearwater/__main__.py` dispatches: if `sys.argv[1:2] == ["--export-worker"]`, call `clearwater.app.export_worker.main()` and exit with its code; otherwise start the GUI as today.
    - Both files become OWNED (the brief already expects `__main__.py` as the loader's call site). `jobs/export_process.py`, the AD-23 helper (`io/video/pipes.py`) and `app/export_worker.py` stay NOT owned and unchanged.
    - A test pins the frozen branch of (a) by monkeypatching `sys.frozen`, and the dispatch of (b) by calling `__main__`'s function with a fake argv.
    - CHARC records AD-34 "frozen worker re-entry" at the accept.
    - With (b), the GPU pack loader placed at the top of `__main__` (Q2) runs in BOTH the GUI and the worker process from one call site, so Q2 needs no second call in `export_worker`.
- **Q6 (new; CHARC to rule at FINAL): the pack root on other platforms.** The brief's `%LOCALAPPDATA%\Clearwater\gpu-pack\...` is Windows-only, and spec v0.6.0's N1 platform list now names more than Windows.
  - Recommended: `gpu_pack.pack_root()` returns `%LOCALAPPDATA%\Clearwater\gpu-pack` on Windows and `$XDG_DATA_HOME/clearwater/gpu-pack` (default `~/.local/share/...`) on Linux.
  - On macOS it returns `None`: there is no CUDA there, so the loader is a no-op.
  - Tests cover all three by monkeypatching `sys.platform` and the environment.
  - Only Windows is exercised for real in this spike.
- **The 1.0.0 behaviour lock, made concrete.** With no pack folder, the loader logs `gpu pack <stamp>: absent` and changes nothing: no `sys.path` entry, the backend probe unchanged, D111's message unchanged.
  - The gate runs with no pack folder present. Round 0 says how the tests guarantee this (an environment override of the root that points under `tmp_path`, never the user's real folder).
- **Timing windows are EXCLUSIVE.** I hold every other cell's heavy turn while one runs: no pytest leg and no WP6.2 / WP-T8 build turn. WP6.2 (read-only) and WP-T8 may run beside WP6.1's NON-timing turns only.
  - The cell announces each window in its yield. I answer with the go and the free-disk figure.
  - Cold start: the cell proposes its method in round 0. A reboot is not available unattended, so it uses a file-cache drop or a first-run-after-build with the method stated.
- **Turns** (the brief's plan, made explicit):
  - Turn 1 = round 0, read-only: the entry points and the spawn as found above; PyInstaller's PySide6 hooks; the build plan; the pack list; Q1-Q6; the PyInstaller version for the N13 STOP; the cold-start method. Then YIELD.
  - Turn 2 = after CHARC's N13 row and my `dev` group addition. `pyproject.toml` and `uv.lock` stay CHARC-approved and are not cell-owned; I make the lock change by pathspec. Then the build script, both builds, and the plugin / path checks (HEIC in from `tests/fixtures/stills/heic/`, PNG and JPEG out, EXIF carried). YIELD for Reviewer A.
  - Turn 3 = the loader, the Q5 re-entry, the tests and the pack proof.
  - Turn 4 = the timings (exclusive) and the report.
  - Then the nets.
- **GATE_CHECKS** (my seat, on the final candidate after Reviewer B; nothing else heavy):
  - `df -h /c` first.
  - The static leg: `ruff check .`, `ruff format --check .`, `mypy` (strict, `src/clearwater` and `tools`).
  - The PARALLEL leg in full: the brief says "parallel leg", and `tests/test_gpu_pack.py` plus the Q5 tests are parallel-leg tests.
  - The serial tests of the start-up path, named:
    - `tests/test_app_startup.py` (gui, 10 tests)
    - `tests/test_gui_startup.py` (gui, 13)
    - `tests/test_core_backend.py` (32)
    - any composition / export-process test module that exercises the worker command: round 0 names them; candidates are those importing `clearwater.app.composition` and `jobs.export_process`.
  - The harness gate, if `scripts/` or kernel docs change (they should not).
  - `git diff --name-only main...wp6.1` = the owned paths plus Q5's two files.
  - 0 CR.
  - The loader is a no-op on the gate machine: no pack folder exists under the real `%LOCALAPPDATA%\Clearwater\gpu-pack` during the gate. I check this before the gate starts.
- **CHARC rulings at FINAL (gen 14, 2026-11-04 ~08:30Z; gen 40's `4090cce9`).** (1) **Q5 RULED as recommended**, design item 3 corrected: (a) `app/composition.py` builds `[sys.executable, "--export-worker"]` when `sys.frozen` is set, the unchanged `-m clearwater.app.export_worker` command otherwise (one expression, docstring updated); (b) `clearwater/__main__.py` dispatches `--export-worker` to `clearwater.app.export_worker.main()` BEFORE any Qt-bearing import (the worker stays Qt-free, AD-31: the GUI's `clearwater.app.main` is imported only on the GUI branch), passing the remaining arguments through unchanged; the GPU pack loader runs first on both branches, so Q2 needs no second call site. Both files OWNED; `jobs/export_process.py`, `io/video/pipes.py` and `app/export_worker.py` untouched; tests pin both branches by monkeypatch of `sys.frozen` and `sys.argv`. AD-34 "frozen worker re-entry" at the accept. (2) **Q6 RULED as recommended:** `gpu_pack.pack_root()` = `%LOCALAPPDATA%` + `Clearwater/gpu-pack` on Windows, `$XDG_DATA_HOME/clearwater/gpu-pack` (default `~/.local/share`) on Linux, `None` on macOS (no CUDA: the loader is a no-op by N14); tests for all three by monkeypatch; only Windows exercised for real. (3) The pack list from `uv.lock` in the fill (cupy-cuda12x 14.2.0, cuda-pathfinder, the cuda-toolkit meta row, the eight nvidia-*-cu12 wheels) is the pack's manifest content; numpy stays in the bundle. (4) Everything else in the fill governs as written.
- **CHARC rulings at round 0 (gen 14, 2026-11-04 ~09:10Z; gen 41's `09bb8e83`; cell ledger `77ec4453`).** **N13 APPROVED (dev group):** `pyinstaller>=6.22,<7` (6.22.3: GPL-2.0-or-later WITH the PyInstaller bootloader exception, which permits building and distributing programs under any licence; Clearwater is GPL-2.0-or-later in any case, so both the exception and the plain GPL branch are compatible), `pyinstaller-hooks-contrib` 2026.9 (dual Apache-2.0 / GPL-2.0: taken under Apache-2.0, compatible through the or-later grant), transitives altgraph 0.17.5 MIT, pefile 2024.8.26 MIT, pywin32-ctypes 0.2.3 BSD-3-Clause, setuptools 84.2.1 MIT: all COMPATIBLE. Shipped inside an artifact: the bootloader and PyInstaller's runtime modules (GPL with the exception) and hooks-contrib's runtime hooks (Apache-2.0) become notice rows in WP6.3's N13 second pass; nothing ships in 1.0.0. The orchestrator adds the pin to `pyproject.toml` + `uv.lock` on `wp6.1` by pathspec (the only lock change: the new packages). **D1 RULED: the orchestrator's mechanism.** When `sys.frozen` is set, `__main__` prepends `dirname(sys.executable)` to `PATH` (`os.pathsep`, portable) before any tool lookup, so the bundled FFmpeg is found first and deterministically; `find_tool` unchanged; one parallel test; a cwd dependence is declined. **D2 APPROVED (N1 site):** on `win32` the loader calls `os.add_dll_directory` for each `<pack>/site-packages/nvidia/*/bin` under a `sys.platform` guard, inside `gpu_pack`; recorded in AD-33 at the accept; the Linux equivalent is an open item for WP6.3 / WP6.4; the proof records every loaded CUDA DLL's path (masking control: the laptop's CUDA 12.4 has no `bin`, `CUDA_PATH` unset). **D3 APPROVED:** the GUI branch calls `configure_logging(app_locations().log_dir)` before the loader (idempotent); the worker logs no pack line. **D4 APPROVED:** the loader acts only when frozen; tests call it directly with an injected root. **D5 APPROVED:** `tests/test_frozen_entry.py` and `docs/proofs/wp6.1-ledger.md` owned; no harness registration (instance-surface prefixes). **D6 APPROVED:** "first export" timed headless through `--export-worker` on one HEIC -> PNG request; the GUI's in-process photo path checked by hand for pass / fail, not timed, stated. **D7 noted:** AD-9's wording "CPU: CuPy not installed". The Windows-only cold-start measurement code in `tools/package/build.py` is APPROVED under N1 as a tool, not product (a note in the report). Q1-Q6 as the cell answered. Turn 2 released.
