# WP0.1 -- cumulative review round ledger (Reviewer A)

Tier fast; transport WSL; codex-cli 0.162.1; flags `-m gpt-5.6-luna -c model_reasoning_effort=medium -s read-only --skip-git-repo-check`.
Bring-up probe: one `^ succeeded in` line before round 1. Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp0.1\rN\` (prompt, diff, transcript, adjudication, md5s).

| Round | Head reviewed | crit / major / minor | In / out envelope | NEW / REOPENED | Reverts | Fixes changed | Assertions | Verdict | Depth |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 37af41f | 0 / 1 / 3 | all in | 4 NEW / 0 | 0 | product (psutil containment) + tests + 1 docstring | banner ok; ^ERROR 0; `ERROR codex_core` 1 = echoed brief text, not transport; footer 1; succeeded 5 | BLOCKING_FINDINGS | (dispatcher) |
| 2 | a305c85 | 0 / 0 / 2 | all in | 2 NEW / 0 | 0 | cleanup only: 1 product line (negative GPU memory) + tests | banner ok; ^ERROR 0; codex_core 0; footer 1; succeeded 3 | NO_NEW_CRITICAL_MAJOR (converged) | (dispatcher) |

## Findings and adjudication

Round 1: (1) major, EXECUTED, `psutil.virtual_memory()` failure aborted the report -- confirmed, fixed. (2) minor, `ffprobe` not probed -- rejected: the brief's JSON key list is exact and `ffprobe` resolution is an install claim, verified by hand. (3) minor, conftest hook docstring -- fixed. (4) minor, test coverage gaps -- RAM-failure test added; OS-specific path variants (case, UNC, drive) banked.

Round 2: (1) minor, EXECUTED, negative nvidia-smi memory accepted -- fixed. (2) minor, Windows path-variant tests -- trailing-separator and `a/../work` cases added; OS-specific variants banked.

Banked (out of loop, nominal minor): no tests for Windows-only path forms (case folding, UNC, drive-relative); `parse_nvidia_smi` multi-GPU behaviour is first-line-only by brief.
