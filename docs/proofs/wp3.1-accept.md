# WP3.1 — Accept record (array backend and image operations: `clearwater.core`)

**Accepted 2026-10-20 by the orchestrator** (generation 6, session
`clearwater-orchestrator-20261020-1134`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG. Wave 1 of Phase 3 (the last of its four packages).
- Brief approval and rulings: CHARC `871a371855bb1630`. Round-0 rulings (orchestrator gen 5)
  upheld with three additions: CHARC `799b83d4fe11bed8`. Round-1 and round-2 rulings:
  orchestrator gen 5 (ledger).

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp3.1-brief.md` (FINAL at dispatch, with the Gate 1 section). Spec v0.5.4, architecture FINAL 1.0. |
| Base SHA | `9735282` |
| Author head | `2bf0aff` (code-final `ea60356`; Reviewer A terminated at R2 with a cleanup; the later commits are ledger and report only: the final-head window, the speed row and its overlap note). No Reviewer B remediation. |
| Cells and depth | **`wp31-cell`** (implementer-opus-high): 108,729 / 24 turns at the R0 yield; 228,618 / 74 at the window-request yield; 237,795 / 81 at the queue yield; 275,011 at the R1 yield (retired there, before remediating: depth evaluation). **`wp31-cell2`** (successor, implementer-opus-high, fresh context from `c6314e9`): 182,305 / 68 at the remediation yield; 205,771 / 88 at the R2 yield; 252,301 / 136 at its final report (after the speed row). |
| Merged head | `wp3.1-mc` = `2bf0aff` rebased onto main `eb88134` (`1cf9564`, clean rebase, 32 commits), plus the report erratum and DR-37 (`c1fd6ce`, docs only). Main fast-forwarded to `c1fd6ce`, gated, then this record committed on main. CHARC held main from the start of the gate (msg `6fe35cd213a469dc`). |
| Byte identity | `git patch-id --stable` = `392da34a1461...` on `9735282..2bf0aff` and on `eb88134..1cf9564` (the B candidate). |
| Gates on the candidate | On `1cf9564`: `ruff check` clean; `ruff format --check` 105 files; `mypy` strict 69 files clean; harness gate 366 OK (1 skipped). Full pytest **1844 passed, 1 warning (CuPy CUDA_PATH), 618 s, exit 0** (basetemp `work/pt-mc-normal`); with `cupy` and `cupyx` unimportable (`sys.modules[...] = None`, then `pytest.main`) **1738 passed, 106 skipped, 361 s, exit 0** (basetemp `work/pt-mc-nocupy`). 1844 = main's 1671 + WP3.1's 173. The cell's own final-head runs on `ea60356`: 1311 passed; 1205 passed / 106 skipped. |
| Gates on main | On `c1fd6ce` after `uv sync`: `ruff check` clean; `ruff format --check` 105 files; `mypy` strict 69 files clean; harness gate 366 OK (1 skipped); full pytest **1844 passed, 1 warning (CuPy CUDA_PATH), 538 s, exit 0** (basetemp `work/pt-main-wp31`). |
| Reviewer A | gpt-5.6-sol / high, WSL, codex-cli 0.162.1. R1: 3 major / 4 minor (F1-F7), all fixed by the successor cell, each with a test that fails on the unfixed code (`312b31e`, `1f38687`, `761bf51`, `804d7db`, `e999076`, `00dfe98`, `a46dac0`). R2: 1 major (R2-1, a REOPENED F4 residual in the speed instrument, not product code) / 2 minor (R2-2 REOPENED F6, R2-3 NEW); zero NEW blocking; fixed as the terminating cleanup (`142566e`, `adcd922`, `7293766`). No reverts. Evidence `clearwater-review-evidence\wp3.1\r1`, `r2`. |
| Reviewer B | ONE pass on `1cf9564`: `NO_NEW_CRITICAL_MAJOR` (4 minor, 2 advisory). |
| Speed row | Run 20:57-21:30Z on code equal to `ea60356`, GX011627 4K. Medians s/frame, product / prototype: GPU (n=680) c3 0.5351 / 0.5355, ancuti2018 0.2370 / 0.2368, upload 0.0144; CPU (n=10, ruled subsample) c3 16.15 / 16.06, ancuti2018 6.58 / 6.63. GPU leg CONTAMINATED from ~frame 350 by CHARC's QA pytest (named in the report); ruled at gen 5: no re-run (an op-mix row; the whole-core row is WP3.4's). |

## The package

`src/clearwater/core/` (`__init__`, `backend` (NumPy and CuPy backends, `select_backend`),
`memory` (the AD-1 estimate), `ops` (the helpers of ruling 1)), `tools/core_speed.py` (the
speed-row instrument, X1), `tests/test_core_*.py` (six files); report
`docs/reports/wp3.1-array-backend.md`. `pyproject.toml`: numpy and scipy moved to
`[project] dependencies` (frame section 4; SciPy kept on task 3's measurement), the
`gpu = ["cupy-cuda12x[ctk]>=14.2,<15"]` extra (ruling 7), the `dev` CuPy line kept; `uv.lock`
regenerated. No interface, prototype or conftest change (checked: empty diff on
`src/clearwater/interfaces`, `tools/prototype`, `tests/conftest.py`, `tests/fixture_plugin.py`).

**The one change outside the grant lines:** the comment on the `dev` group's CuPy line, which
said "Prototype only: product adoption is WP2.1's", now says the product names CuPy as the
`[gpu]` extra (WP3.1) and that the line is kept so the developer environment has CuPy (ruling 7).
The old comment had become false; the dependency line itself is unchanged. ACCEPTED (the report's
"Deviations and limits" states it).

QA checks at this seat (beyond the gates): the reason strings in `backend.py` are the round-0
list exactly; `select_backend` catches a `free_device_bytes()` failure after the cached probe; the
estimate at 4K is 1,982 MiB (50 1/12 planes x 1.25 x 4 bytes x 8,294,400 px + 1 MiB);
`test_gpu_methods_return_device_arrays` derives its method set from IF-2's `-> Array`
annotations, so a new method cannot be missed; the SciPy dependency is in the frame section 4
grant and AD-18's licence list.

## Reviewer B

ONE pass (on `1cf9564`). `clearwater-review-evidence\wp3.1\reviewB\review-B.txt` md5
`863b2b023af1b60fe349ad8cb91e3a17`; stderr `0eb78c39`; prompt `e923b2da`; diff `467e4e14`;
`md5s.txt` beside them. Assertions: banner gpt-5.6-sol / high, read-only; `^ERROR` 0; `tokens
used` footer; 20 `succeeded in`, 2 non-zero exits (both environment probes: no NumPy in WSL's
Python; the Windows venv under WSL failed `UtilBindVsockAnyPort`); VERDICT anchored; every
`docs/proofs` or evidence-path mention on a command line is an exclusion glob, and ledger mentions
in output are path text from the brief. `VERDICT: NO_NEW_CRITICAL_MAJOR`. Dispositions:
- B#1 MINOR (in envelope, EXECUTED): an installed CuPy whose DLL load raises `ImportError` is
  reported `CPU: CuPy not installed` rather than `CPU: CuPy failed to load`; the fallback is right,
  the reason misnames the cause. BANKED (DR-37 a).
- B#2 MINOR (in envelope, REASONED): the `core.ops` helpers are typed `ArrayBackend` but accept only
  a `CoreBackend` (they need `xp`, ruling 1.1); a protocol-only wrapper is refused with a clear
  TypeError. The shipped backends are unaffected. BANKED (DR-37 b); consumer note for WP3.2/3.3
  tests (use a core backend, not a protocol double).
- B#3 MINOR (in envelope as a config, EXECUTED): `tools/local_config.py` refuses a working folder
  inside the footage folder but not the reverse, so `core_speed.py`'s output under `working_path`
  could land inside a footage folder nested in the working folder. Pre-existing in
  `local_config` (every tool writing under `working_path` shares it); the owner's config is not
  nested. BANKED (DR-37 c).
- B#4 MINOR (EXECUTED): report claim 1 ("every IF-2 method and helper is bit-identical to the
  prototype") is too broad: YCbCr is compared in `bt709` full only and `pyramid_levels` differs
  for `min_level_size < 1`. ERRATUM at the gate.
- B#5 ADVISORY (EXECUTED): `core_speed.probe_clip` raises `IndexError`, not `SpeedError`, on
  ffprobe JSON with no stream. BANKED (DR-37 d).
- B#6 ADVISORY (out of envelope): `gpu_snapshot` records the first `nvidia-smi` row regardless of
  the CuPy device. BANKED (DR-37 e; DR-2 family).

## Erratum at the gate

Appended to the report: claim 1's bit identity holds for the methods and helpers with a prototype
counterpart on the tested inputs; YCbCr `bt709` limited and `bt601` have no counterpart (R0-1);
`pyramid_levels` agrees only for `min_level_size >= 1`; `memory_estimate_bytes` equals the
prototype's; `select_backend` and `free_device_bytes` are pinned by their own tests (B#4).

## Follow-ons

- DR-37 (a)-(e) BANKED; triggers: the next `clearwater.core` touch (WP3.4 or WP3.21) or WP3.16's
  status bar for (a)/(b); the next `tools/local_config.py` touch for (c); WP3.4's whole-core row
  for (d)/(e).
- Open items from the cell's report: WP3.4 re-checks the product memory peak (counting allocator)
  and records the whole-core speed row; WP3.21 takes the device-to-host sync-point list (ledger
  "Device-to-host sync points"); WP3.3 receives float32 `percentile` bounds (within AD-11 of the
  prototype, DR-14).
- Consumer notes carried to the wave-2 briefs (orchestrator state item 3).
