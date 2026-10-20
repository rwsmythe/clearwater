# WP2.4 — Phase 3 brief frame (CHARC, DRAFT 2026-10-20)

**Purpose.** Every Phase 3 brief (WP3.1 to WP3.20) is written by the orchestrator in the plan
section 4.6 format against this frame, so the fifteen build packages share one set of rules and
cite the same frozen inputs. CHARC approves each brief before dispatch. This frame is FINAL when
spec v0.5.4 is approved at CP4 (`docs/reports/spec-v0.5.4-proposal.md`); until then briefs may be
drafted against it with v0.5.3 cited and the v0.5.4 items named as "proposed".

## 1. Inputs every brief cites

| Input | Where | Use |
|---|---|---|
| Spec | `docs/underwater-correction-spec.md` v0.5.4 (or v0.5.3 + proposal until CP4) | the clauses in the package's plan row, quoted |
| Architecture | `docs/architecture.md` (DRAFT 0.1; FINAL at CP4) | the module's responsibility, data flow, section for the package |
| Decisions | `docs/decisions.md` AD-1..AD-24 | every AD the package implements, cited by number |
| Interfaces | `src/clearwater/interfaces/` (WP2.2, `b288533`, FROZEN) | consumed and provided interfaces by module and name; stubs from `stubs.py` until a dependency merges |
| Fixtures | `tests/fixtures/` + `tools/fixtures/` (WP2.3) and `tests/fixture_plugin.py` | the samples the package's tests use, by manifest name |
| Prototype | `tools/prototype/` (read-only reference) | numerical reference for WP3.1-3.4 (bit-identity or tolerance tests against recorded outputs, DR-19); evidence code only, never imported by `src/` |
| Gate report | `docs/reports/wp1.6-gate-report.md` | the measured figures a package is held to (speed, memory, tolerances) |
| Debt | `docs/debt-register.md` | the DR items the package closes or must not re-open |

## 2. Rules common to every Phase 3 brief

1. **Owned files only.** A package creates and changes files under its module path, its tests
   and its report; `interfaces/` is never changed (a needed change is a STOP to CHARC, AD-20);
   `pyproject.toml` only where the brief grants a dependency line (section 4).
2. **Stubs until merge.** A package depending on another unmerged package builds against the
   WP2.2 stub and its tests use the stub; the brief names which.
3. **One code path, CPU and GPU** (D107) for anything touching arrays: through IF-2 only; no
   direct `cupy` import outside `clearwater.core`.
4. **Tolerances** are AD-11's; a package proposes no looser one without a STOP.
5. **Dependency rule** (plan 8.1): `core` and `methods` import nothing from `io`, `jobs`, `gui`;
   `gui` and `jobs` reach methods only through IF-3. A test enforces it in every package that
   adds a module.
6. **Footage** stays read-only and outside the repo; tests that need it are `footage`-marked and
   skip when absent; outputs go under `work/`.
7. **Hardware flags** per plan 4.3: `gpu` for CuPy paths, `footage`, and EXCLUSIVE for any
   timing or memory figure (one at a time, best effort per the owner's 2026-10-19 ruling, strays
   and clocks recorded, contaminated rows kept as spread).
8. **Docstrings and gates** per CLAUDE.md: Google style on every public name; ruff, format,
   mypy strict, pytest green; the suite now runs 8-15 min, so the gate runs it in the background.
9. **Reviewer A STRONG; Reviewer B at the orchestrator's seat;** five-round gate; depth read at
   dispatch, every yield and before any ruling; ~250K evaluation point; ~400K stop.
10. **Reports:** `docs/reports/wp3.N-<slug>.md` with claims, evidence paths and limits; the
    ledger in `docs/proofs/wp3.N-ledger.md`; accept record by the orchestrator.
11. **STOP conditions:** an interface change; a dependency not granted; an OS-specific path not in
    AD-23; a spec clause the brief and the code disagree on; anything owner-reserved.

## 3. Package order and parallelism

| Wave | Packages | Why |
|---|---|---|
| 1 | WP3.1 core (opus-high), WP3.13 naming (sonnet-high), WP3.15 presets/settings (sonnet-high), WP3.7 probe (sonnet-high) | no build dependency beyond interfaces |
| 2 | WP3.2, WP3.3 (opus-high; after WP3.1), WP3.5 colour (opus-high; after WP3.1), WP3.6 photo (sonnet-high), WP3.12 cache (sonnet-high), WP3.16 shell (sonnet-high, against stubs) | |
| 3 | WP3.4 assembly (opus-high), WP3.9 decode, WP3.10 encode (opus-high; AD-2/AD-23 transport), WP3.11 analysis (opus-high), WP3.17-3.20 GUI (sonnet-high) | |
| 4 | WP3.14 export and batch (opus-high) | needs 3.4, 3.9-3.11, 3.13 |

Exclusive timing lives only in WP3.1's and WP3.10's reports (speed rows) and in the Phase 3
optimisation package if the owner approves one at Gate 1.

## 4. Dependency grants (pyproject)

Moved from the dev group to product dependencies by the package that first imports them in
`src/`: `numpy` (WP3.1), `scipy` if still needed after WP3.1 (prefer own kernels on IF-2),
`cupy-cuda12x` as an optional extra `[gpu]` (WP3.1), `pillow` and `pillow-heif` (WP3.6),
`PySide6` (WP3.16). Nothing else without a CHARC grant; `av` stays dev-only (spike use).

## 5. Spec-to-package map for v0.5.4 items

| v0.5.4 item | Package |
|---|---|
| D106 interim N6 / V16 | WP3.14 (export timing row), WP5.2 re-measure |
| D100 caps kept, nullable | WP3.2 |
| D98 one stage permitted | WP3.4, WP3.11 |
| D94 reading (AD-22) | WP3.10 |
| G12 force-CPU and defaults | WP3.15, WP3.20 |
| D75 names and mapping | WP3.10, WP3.20 |
| 6.3 defaults | WP3.2, WP3.3, WP3.4 |
| 7.2 smoothing default, step-aware task | WP3.11 |
| N1 pipe exception (AD-23) | WP3.9, WP3.10 |
| D63 HEIC rule (AD-24) | WP3.6 |
