# Clearwater

Desktop tool (Python, PySide6) that corrects color cast, contrast loss and haze in amateur underwater photos (iPhone) and video (GoPro). Visual quality is the goal, not physically exact color. Single owner, Windows 11 laptop, open source (GPL-2.0-or-later), private repository for now.

## Read these first, in this order

1. `docs/clearwater-implementation-plan.md` — how the work is organized: roles, working rules, work packages (WP0.1 onward), owner checkpoints, interfaces to freeze.
2. `docs/underwater-correction-spec.md` — v0.5.3. The source of truth for what Clearwater does. Decisions are numbered D1–D117, tests V1–V18, GUI requirements G1–G13, non-functional requirements N1–N13.
3. `docs/underwater-imagery-correction-research.md` — background on the method family; not normative.

If the plan and the spec disagree, the spec wins; raise the disagreement to the owner.

## Current state

- **Harness bootstrapped (2026-10-14).** The repository is a live multi-agent harness instance (see "The harness" below) with the application defined in `APPLICATION.md`, three implementer cells under `.claude/agents/`, the review/gate fill in `docs/review-gate-clearwater.md`, and the uv project skeleton (`pyproject.toml`, Python 3.12, `src/clearwater/`, `tests/`, `tools/`).
- **No product code yet.** `src/clearwater/__init__.py` is a stub. Prototype code (evidence, not product) lives under `tools/prototype/`.
- **Done:** WP0.1 (local config, environment report, FFmpeg dev tools; accepted 2026-10-14), WP0.2 (footage inventory tool `tools/inventory.py`; accepted 2026-10-15), WP1.1 (reference pipeline prototype `tools/prototype/`, reports `docs/reports/wp1.1-*.md`; accepted 2026-10-15, main `9711faf`), WP1.2 Part A (CuPy backend, `bench.py`, synthetic speed and memory report `docs/reports/wp1.2a-speed-memory.md`; accepted 2026-10-15, main `f6d998a`), WP1.5 (container spike `tools/container_spike/`, report `docs/reports/wp1.5-container-spike.md`; recommendation SIMPLE, one FFmpeg process with NVENC; accepted 2026-10-15, main `3242679`, the first accept with Reviewer B run at the orchestrator's seat), WP1.2R (prototype remediation after a retroactive seat-run Reviewer B over `tools/prototype`; accepted 2026-10-15, main `996274e`), WP1.3 shallow part (look-check instrument `tools/lookcheck/`, report `docs/reports/wp1.3-look-check.md`, pack at `work/wp1.3/index.html` ready for CP2; accepted 2026-10-15, main `7178540`; its second blocking Reviewer B was adjudicated at the gate, DR-20 and DR-21), WP-T1 (pytest temp-root footage guard in `tests/conftest.py`; accepted 2026-10-15, main `f6a34a4`; DR-21 closed, limits DR-22), WP1.4 shallow part (statistics and smoothing experiments `tools/prototype/temporal.py`, report `docs/reports/wp1.4-statistics.md`; accepted 2026-10-19, main `91f5775`; D98 no visible staged/flat difference; the 2 s smoothing default is PROVISIONAL per DR-25(3)), real footage inventory (`docs/reports/inventory-2026-10-18.md`, main `b1fd289`: 35 videos, Snorkel 26 / SCUBA 8 / edits 1, no chaptered recordings, photos pending). Accept records in `docs/proofs/`; open debt in `docs/debt-register.md`.
- **In flight:** WP-T2 (footage locator `find_footage_file` in `tools/local_config.py`; closes DR-24: three footage tests skip since the owner's 2026-10-18 folder layout `Snorkel/`, `SCUBA/`, `edits/`). Then WP1.2 Part B (exclusive). CP1 (categories, chapter handling in v1) is with the owner; the deeper look-check cases and the gain-cap noise test (WP1.4b) follow CP1. Gate 1 (N6 speed) is decided at WP1.6 with Part B.

## Inputs the owner has supplied

Both were owner-set on 2026-10-14; do not substitute other paths.

- Footage folder: SUPPLIED 2026-10-14 by the owner (in chat to CHARC: \"concur with footage location\"): `C:\Users\rwsmy\clearwater-footage\`, OUTSIDE the repository so no git command in this tree can reach it. Treated as **read-only**, never committed. The owner is still downloading into it. No `.LRV`/`.THM` sidecars exist for this footage (owner, 2026-10-15: deleted from the camera at cloud upload), so D60's proxy leg is not testable here.
- Working folder: SUPPLIED 2026-10-14 by the owner (in chat to the orchestrator: "let's create a working folder within clearwater", confirmed as ignored by git): `C:\Users\rwsmy\clearwater\work\`, gitignored as `work/` (69311b1). Outputs, caches and reports go there; never committed. Never run `git clean -x` in this tree (it deletes ignored files).

Both go into the uncommitted `clearwater.local.toml` (template: `clearwater.local.example.toml`, created by WP0.1).

## Conventions (plan §2, §4)

- Environment: **uv** with a lock file. Python **3.12** (`.python-version`); confirmed against the chosen GPU and video libraries at the prototype gate. `uv sync` creates `.venv` with the `dev` and `comms` groups.
- Layout: `src/clearwater/` package, `tests/` (product tests; `tests/harness/` is the harness's own suite and is excluded from pytest), `tools/`, `docs/`.
- Tests: `uv run pytest`, markers `gpu`, `footage`, `gui`, `slow` (`--strict-markers`). Footage-marked tests skip when the footage path is absent.
- Lint and format: `uv run ruff check .` and `uv run ruff format --check .` (Google docstring convention). Type checking: `uv run mypy` (strict, on `src/clearwater` and `tools`).
- Docstrings: Google style on every public function, class and module. Verify comments against the code they describe.
- Dependencies are added only through `pyproject.toml` and the lock file; a dependency not named in the architecture document needs the chief architect's approval (license check, spec N13).
- Keep code portable; nothing specific to one operating system without approval (spec N1).
- The footage folder is never written to, renamed in, or deleted from. All outputs go to the working folder. `tests/conftest.py` refuses to start pytest when its temp root (`--basetemp`, `PYTEST_DEBUG_TEMPROOT`, or the derived TMP/TEMP root) lies inside the configured footage folder (WP-T1, DR-21 closed; limits in DR-22). Never point a temp root there; `work/` is the legitimate basetemp.
- No CI service, installer or packaged executable is planned. Raise it if wanted.
- Commit by pathspec (`git commit -m "..." -- <paths>`); every role shares the main tree's index. Conventional commits carrying the work-package id.

## Definition of done (plan §4.5)

A work package is done only when: scope met within its owned files with frozen interfaces unchanged; docstrings complete; ruff, mypy and pytest pass; the verification loop has run until a full pass finds nothing new (suspect → confirm independently → fix → repeat); no assumptions were made where the brief or spec was ambiguous (stop and ask instead); a completion report is written; and an independent reviewer has checked it against the brief and spec. The concrete review and gate mechanism is `docs/review-gate-clearwater.md`.

## Roles (plan §3)

Chief architect (harness role **CHARC**, the director) directs an orchestrator, which runs implementer cells in git worktrees. Only the orchestrator merges to main. Owner-reserved decisions: footage categories, the look check and V2 visual review, scope decisions (chapter handling, gain caps, anything relaxing a mandatory requirement), and any change to the spec. The owner is the harness's **operator**, the only `decision_request` recipient.

**Standing owner direction (2026-10-14, verbatim):** "intent is for this development to run as unattended as possible. orchestrator will send you operator related questions. Answer for operator unless the question truly requires my input." So the orchestrator routes every operator-bound question to CHARC (`--to charc`, type query, recommended answer first); CHARC answers in the operator's stead. "Truly requires the owner" = the owner-reserved list above (footage categories, the look check and V2 visual review, anything relaxing a mandatory requirement, any spec change); only those become a `decision_request`, and the orchestrator holds that item while continuing everything else.

## The harness

The repository doubles as a multi-agent harness instance (template: `rwsmythe/harness-template`, comms core from the coa-chess lineage). The kernel docs are `docs/charc-charter.md`, `docs/charc-bootstrap.md`, `docs/orchestrator-context.md`, `docs/dispatch-recipe.md`, `docs/review-gate-seam.md`, `docs/codex-reviewer.md`, `docs/model-prompting-standard.md`; CHARC's state pointer is `docs/charc-state.md` (read first, overwritten each session).

- **Comms:** file mailboxes under `comms/` (gitignored), one singular inbox per role (`charc`, `orchestrator`, `operator`): `uv run python scripts/role_mail.py post|list|peek|read ...`. Drain to a file, re-list before every post, bodies via `--body-file`, subjects under 120 characters. After every post, one cross-session `SendMessage` cue to the exact session name in `comms/.launch-sessions.json`.
- **Comms UI:** `uv run python scripts/comms_ui.py` serves on **port 8775** (the sibling harnesses on this machine use 8765).
- **Launcher:** `powershell -NoProfile -File scripts/launch_role.ps1 -Role charc|orchestrator` (psmux session `clearwater`, session names `clearwater-<role>-<stamp>`; `-DryRun` to preview). CHARC fable/medium, orchestrator opus/high, permission-mode auto (seam 4; owner-set 2026-10-14).
- **Harness gate:** `uv run python -m unittest discover -s tests/harness` — run it whenever `scripts/`, `.claude/`, the kernel docs or `tests/harness/` change. The harness core stays stdlib-only and application-agnostic; application vocabulary lives on the instance surface registered in `tests/harness/genericity_lists.py`.

## Hardware rule (plan §4.3)

Agents run on the owner's laptop with direct access to the graphics card. Packages that record timing or memory figures are exclusive: one at a time, nothing else heavy running, timed on a full clip rather than one frame.
