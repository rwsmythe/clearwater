# Acceptance spec -- `scripts/launch_role.ps1` (Task E.1)

PowerShell is not unit-tested by the stdlib `unittest` runner; the launcher's
acceptance is this checklist + the `-DryRun` evidence (machine-checkable
content is also asserted by `tests/test_launch_role_content.py`).

## Content checklist

- [x] `param([ValidateSet('charc','orchestrator','both')] ...)` -- roles are
  **charc + orchestrator** (NOT the legacy charc + second-director set).
- [x] Sets **`HARNESS_ROLE=<role>`** inside the spawned shell (via the
  `Build-LaunchCommand` inner command + the `EncodedCommand` blob) so the role
  reaches the comms hook regardless of how the window was spawned.
- [x] The **single shipped spawn path is a plain `powershell -NoExit` window**
  (no Windows-Terminal-tab surface); `-NoWT` is accepted as a no-op.
- [x] **SEAM 4** model/effort/permission default ships as a tuned starter
  (`$LaunchArgs`), clearly marked tunable -- NOT a bootstrap blocker.
- [x] **Preflight** verifies the `claude` CLI + the exact flags it uses
  (`-n`, `--resume`, `--permission-mode`, the `auto` choice) against `--help`;
  throws on a missing flag (verify-don't-assume).
- [x] Fresh mode dispatches the role's bootstrap (`docs/charc-bootstrap.md` for
  charc; `docs/orchestrator-context.md` for orchestrator). Resume reopens the
  recorded named session by display name.
- [x] **The launcher does NOT own the liveness registry** -- the HOOKS own the
  one-file-per-session registry under `comms/sessions/`. The launcher only sets
  `HARNESS_ROLE` (and keeps a display-name map for resume, NOT the liveness
  registry).

## `-DryRun` evidence (run after the kernel docs land -- C/H)

```
pwsh -File scripts/launch_role.ps1 -Role orchestrator -DryRun
pwsh -File scripts/launch_role.ps1 -Role charc -DryRun
```

Each prints the computed `claude` command, the inner launch command (with
`$env:HARNESS_ROLE='<role>'` set), and the `EncodedCommand` spawn blob, then
exits WITHOUT launching a window or writing the session map. The preflight runs
first (and throws if a used flag is absent from the installed CLI). This is the
operator's bootstrap-step-5 evidence (the fully-live launch is the operator
witness gate).
