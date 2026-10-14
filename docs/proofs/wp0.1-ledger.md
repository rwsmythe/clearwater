# WP0.1 -- cumulative review round ledger (Reviewer A)

Tier fast; transport WSL; codex-cli 0.162.1; flags `-m gpt-5.6-luna -c model_reasoning_effort=medium -s read-only --skip-git-repo-check`.
Bring-up probe: one `^ succeeded in` line before round 1. Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp0.1\rN\` (prompt, diff, transcript, adjudication, md5s).

| Round | Head reviewed | crit / major / minor | In / out envelope | NEW / REOPENED | Reverts | Fixes changed | Assertions | Verdict | Depth |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 37af41f | 0 / 1 / 3 | all in | 4 NEW / 0 | 0 | product (psutil containment) + tests + 1 docstring | banner ok; ^ERROR 0; `ERROR codex_core` 1 = echoed brief text, not transport; footer 1; succeeded 5 | BLOCKING_FINDINGS | 82K at return (dispatcher-read) |
| 2 | a305c85 | 0 / 0 / 2 | all in | 2 NEW / 0 | 0 | cleanup only: 1 product line (negative GPU memory) + tests | banner ok; ^ERROR 0; codex_core 0; footer 1; succeeded 3 | NO_NEW_CRITICAL_MAJOR (converged) | 82K at return (dispatcher-read) |
| 3 | f2a5526 (delta ad1acd5..f2a5526) | 0 / 0 / 1 | all in | 1 REOPENED (banked Windows-path-test item) / 0 NEW | 0 | none needed; input was Reviewer B's F1-F5 (1 major, 4 minor, all fixed before the round: product code + tests + template docs) | banner ok; ^ERROR 0; `ERROR codex_core` 1 = echoed brief text; footer 1; succeeded 2 (reviewer could not run uv/pytest/git; author ran 40 tests) | NO_NEW_CRITICAL_MAJOR (converged) | 82K at round-3 dispatch (dispatcher-read) |

## Findings and adjudication

Round 1: (1) major, EXECUTED, `psutil.virtual_memory()` failure aborted the report -- confirmed, fixed. (2) minor, `ffprobe` not probed -- rejected: the brief's JSON key list is exact and `ffprobe` resolution is an install claim, verified by hand. (3) minor, conftest hook docstring -- fixed. (4) minor, test coverage gaps -- RAM-failure test added; OS-specific path variants (case, UNC, drive) banked.

Round 2: (1) minor, EXECUTED, negative nvidia-smi memory accepted -- fixed. (2) minor, Windows path-variant tests -- trailing-separator and `a/../work` cases added; OS-specific variants banked.

Banked (out of loop, nominal minor): no tests for Windows-only path forms (case folding, UNC, drive-relative); `parse_nvidia_smi` multi-GPU behaviour is first-line-only by brief.

Post-convergence amendment (0fa8315): `report_version` (integer 1, first key) added to the environment report; no review round (reason: CHARC ruling, brief amendment).

Round 3 (post-Reviewer-B): B returned BLOCKING on ad1acd5 (F1 major EXECUTED: UTF-16 config -> uncaught UnicodeDecodeError; F2-F5 minor: key order and --out tests, probe decoding and report overwrite, report write errors, template docs). All five confirmed and fixed in 3d12831, 90dc168, f2a5526. Reviewer A round 3 on the delta converged. Evidence: clearwater-review-evidence\wp0.13\.
