<#
.SYNOPSIS
    Cold-start (or resume) a long-lived Claude Code CLI session for a harness
    role (CHARC the director, or an orchestrator generation).

.DESCRIPTION
    Opens a long-lived Claude Code CLI session per role in a plain PowerShell
    window, running the role's bootstrap prompt. The load-bearing job is to set
    HARNESS_ROLE=<role> INSIDE the spawned shell so the comms hooks know which
    role they are running for (the UserPromptSubmit hook records the role for
    resume recovery + gates the unread notice on it), and DISABLE_AUTOUPDATER=1
    so no role session moves the claude binary as a side effect (see
    $script:SpawnEnv). Fresh mode dispatches the
    role's bootstrap; resume mode reopens the recorded named session by display
    name.

    The launcher does NOT own mailbox routing or liveness state. The HOOKS own
    the session -> role recovery record (under comms/roles/, hook-written); ARC-8
    retired the per-generation orchestrator registry, so every role -- the
    orchestrator included -- drains its own singular comms/<role>/inbox. The
    launcher's comms responsibilities are narrow: set HARNESS_ROLE so the hook
    can record the role, and own the resume display-name map
    (comms/.launch-sessions.json) -- a launch-convenience map, NOT a mailbox
    routing / liveness registry.

    CONTEXT RESET = FRESH MODE. When a role's context fills, run a fresh start;
    it mints a new dated session name and leaves the old session untouched.

.PARAMETER Role
    charc | orchestrator | both  (default: both; both = charc + orchestrator)

.PARAMETER Resume
    Switch. Reopen the recorded named session for the role(s) instead of a
    fresh start.

.PARAMETER NoWT
    Switch. Force the SEPARATE-WINDOW spawn path (one 'powershell -NoExit' window
    per role). DEFAULT (without -NoWT) opens each role as a NEW TAB in the existing
    Windows Terminal window (wt -w 0 new-tab). -NoWT -- or Windows Terminal (wt.exe)
    not being on PATH -- falls back to a separate window.

.PARAMETER NoPsmux
    Switch. Force the byte-equivalent FALLBACK vehicle (today's wt-tab / plain
    'powershell -NoExit' windows) instead of launching role windows inside the
    shared psmux session. -NoPsmux short-circuits to the fallback BEFORE any
    psmux resolution/preflight, so it never depends on psmux being installed.

.PARAMETER SessionName
    The shared psmux session name role windows are launched into (the session the
    operator attaches from an SSH client). DEFAULT: REPO-DERIVED -- the sanitized
    repo basename via Get-DefaultSessionName ('<repo-basename>' for this repo; 'agents'
    if the basename sanitizes empty). The per-repo default is exactly what stops
    concurrent harnesses in different checkouts from colliding in one
    machine-global session -- each checkout gets its own session. VALIDATED
    conservative (^[A-Za-z0-9._-]+$): spaces / quotes / ':' / ';' / tmux target
    syntax in a session name are spawn/attach hazards. -SessionName is the
    explicit override.

.PARAMETER DryRun
    Switch. Run the preflight, compute the session name(s) and the exact claude
    command line(s) + the spawn blob, print them, and exit WITHOUT launching
    anything or writing the display-name map.

.NOTES
    REMOTE ATTACH (the psmux vehicle's purpose): the launcher opens role sessions
    as WINDOWS of a shared psmux session. From another machine (or a phone SSH
    client): ssh into this host, then
        psmux attach -t <repo-basename>
    and switch between role windows tmux-style; detach leaves the <repo-basename> session
    (and every role) running untouched. A local attach view is auto-opened once
    per launch (never per-role). -NoPsmux (or psmux unresolvable / failing its
    command-set preflight) reverts to the byte-equivalent wt-tab / plain-window
    fallback.

    DIAGNOSIS (Phase-0 finding): a psmux role window runs 'powershell -NoExit', so
    the window PERSISTS at the shell prompt even if the inner claude command exits
    -- an instantly-failing launch is visible (attach and read it), not silently
    gone. List live windows with 'psmux list-windows -t <repo-basename>'; re-run with
    -DryRun to print the exact spawn line without launching.

    SEAM 4 (per-role model/effort defaults): $LaunchArgsByRole ships TUNABLE
    STARTERS (not canonical values; tune per project) with ONE fixed exception --
    CHARC is the top-capability tier current in the harness (the architect/
    bootstrap role; not tunable). All roles are EXPLICIT so no generation
    inherits the session/CLI default model; the concrete values live ONLY in
    the $LaunchArgsByRole table below (single source -- prose here once carried
    a stale figure that got quoted; see docs/model-prompting-standard.md).
    NOT a bootstrap blocker. Every flag is preflight-verified against the
    installed CLI's --help (verify-don't-assume).

    PowerShell 5.1 compatible: no '&&', no ternary, no null-coalescing.
    ASCII-only console output (Windows cp1252 stdout). Roles are launched
    SERIALLY (the display-name map read-modify-write is not concurrency-safe).

    RESUME: a session started by hand (claude --resume <id>) bypasses this
    launcher, so HARNESS_ROLE is unset; the UserPromptSubmit hook recovers the
    role from a session-keyed record written at the original launch. To re-set
    it explicitly (the deliberate path):
        $env:HARNESS_ROLE='<role>'; claude --resume <id>
#>

[CmdletBinding()]
param(
    [ValidateSet('charc', 'orchestrator', 'both')]
    [string]$Role = 'both',
    [switch]$Resume,
    [switch]$NoWT,
    [switch]$NoPsmux,
    [ValidatePattern('^[A-Za-z0-9._-]+$')]
    [string]$SessionName = 'agents',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# psmux session names this invocation has already emitted a 'create' for -- so a
# serial '-Role both' windows the second role into the first role's new session
# (in-memory, on top of the read-only has-session probe; write-free under DryRun).
$script:CreatedSessions = @{}

# --- paths -----------------------------------------------------------------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$CommsDir = Join-Path $RepoRoot 'comms'
$SessionsPath = Join-Path $CommsDir '.launch-sessions.json'

# --- project token (launcher-naming commission, 2026-09-15T07:25Z item 1) --
function Resolve-MainCheckoutRoot($repoRoot) {
    # Reviewer B r1 finding B-1 (MAJOR): $repoRoot is $RepoRoot -- in a LINKED
    # WORKTREE that is the WORKTREE's own folder, not the main checkout, so a
    # naive Split-Path -Leaf on it mints a DIFFERENT <project> token per
    # worktree. `git rev-parse --git-common-dir` resolves to the ONE shared
    # .git dir regardless of which worktree (or the main tree itself) invokes
    # it, so its PARENT is always the SAME main checkout root -- the single
    # source every worktree + the main tree must agree on. Falls back to
    # $repoRoot itself (today's behavior) if git is unavailable (command not
    # found -- a terminating error PowerShell throws regardless of
    # $ErrorActionPreference, caught here) or the call fails (a non-repo path,
    # non-zero exit, or empty output).
    try {
        $commonDir = & git -C $repoRoot rev-parse --path-format=absolute --git-common-dir 2>$null
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($commonDir)) { return $repoRoot }
        $mainRoot = Split-Path -Parent ([string]$commonDir).Trim()
        if ([string]::IsNullOrWhiteSpace($mainRoot)) { return $repoRoot }
        return $mainRoot
    }
    catch {
        return $repoRoot
    }
}

function Get-DefaultProject($repoRoot) {
    # The DEFAULT <project> token for New-SessionName's <project>-<role>-<stamp>
    # session-name shape: the sanitized MAIN-CHECKOUT folder name's segment
    # BEFORE ITS FIRST '-' (a hyphenated folder name uses only its leading
    # word as the project token; an un-hyphenated one uses the whole name).
    # Resolve-MainCheckoutRoot normalizes $repoRoot to the main checkout FIRST
    # (B-1: every worktree must mint the SAME token as the main tree).
    # Sanitize the leaf the same way as Get-DefaultSessionName (replace
    # invalid-char runs with '-', never strip; collapse repeats; trim) BEFORE
    # splitting, so the returned token is already pattern-valid; a leaf with
    # no '-' (after sanitizing) uses the whole sanitized name; empty falls
    # back to 'agents', matching the session-name default's own fallback.
    $mainRoot = Resolve-MainCheckoutRoot $repoRoot
    $leaf = Split-Path -Leaf $mainRoot
    $name = [regex]::Replace($leaf, '[^A-Za-z0-9._-]+', '-')
    $name = [regex]::Replace($name, '-{2,}', '-')
    $name = $name.Trim('-')
    if ([string]::IsNullOrEmpty($name)) { return 'agents' }
    $token = $name.Split('-')[0]
    if ([string]::IsNullOrEmpty($token)) { return 'agents' }
    return $token
}

# ONE SOURCE for New-SessionName's <project> segment -- never a literal inside
# the function. Unlike -SessionName, there is no CLI override for $project;
# ONLY this constant overrides the derived default -- edit it directly.
$script:Project = Get-DefaultProject $RepoRoot

# The role's bootstrap doc the fresh prompt points at. CHARC reads its first-run
# flow; an orchestrator generation reads the operating model (its bring-up block
# lives in charc-bootstrap step-5 by default).
$BootstrapFiles = @{
    'charc'        = 'docs/charc-bootstrap.md'
    'orchestrator' = 'docs/orchestrator-context.md'
}
$RoleTitles = @{ 'charc' = 'CHARC'; 'orchestrator' = 'ORCHESTRATOR' }

# SEAM 4 -- per-role model / effort / permission-mode defaults. TUNABLE STARTERS
# (tune per project), NOT canonical values, with ONE fixed exception:
#   - CHARC is FIXED at the TOP-CAPABILITY TIER current in the harness -- the
#     architect/bootstrap role needs top capability regardless of project. The
#     tier is an INTENT (as of 2026-08: fable); the MODEL tier is not tunable,
#     the EFFORT is a per-project operator choice.
# Rationale for every assignment + the operating economy they serve:
# docs/model-prompting-standard.md sec 10 (operator-approved 2026-08-02).
# Clearwater (owner-directed 2026-10-14): CHARC fable/medium -- higher effort
# over-deliberates on routine routing and rulings, the director lane's bulk.
# The orchestrator is opus/high (agentic coordination, accept-time review
# precision). Implementer tiers are per-cell frontmatter (.claude/agents).
# All roles share '--permission-mode auto' (a sensible generic default).
$LaunchArgsCommon = @('--permission-mode', 'auto')
$LaunchArgsByRole = @{
    # FIXED -- CHARC is the top-capability tier in any harness (B-3).
    'charc'        = @('--model', 'fable', '--effort', 'medium')
    # Opus/high (operator-approved 2026-08-02; 'opus' is the CLI ALIAS and
    # tracks the latest Opus -- 5.5 as of 2026-09-22, operator-directed): the
    # delivery-manager lane is the Opus profile -- agentic coordination, review
    # precision at accepts, multi-agent management. The EFFORT is explicit so it
    # never drifts with a model's own default (Opus 5.5 defaults to medium and
    # ignores a saved effortLevel). Drop effort per-pass for mechanical work.
    'orchestrator' = @('--model', 'opus', '--effort', 'high')
}

$FreshPromptFmt = 'Read and follow {0} -- it is your role bootstrap. Begin now.'
$ResumePrompt = 'Resuming your {0} session: re-read your role doc, drain your inbox with role_mail, then report current state and await the operator.'

# --- helpers ---------------------------------------------------------------

function Write-Info($msg) { Write-Host "[launch-role] $msg" }
function Write-Err($msg) { Write-Host "[launch-role] ERROR: $msg" }

# The ten CLAUDE* session markers a spawned successor must not inherit (docs/
# briefs/2026-09-08-launcher-marker-scrub.md sec 1): a Claude session's shell
# carries ELEVEN CLAUDE* markers, and a successor that inherits all of them
# gets no transcript (no --resume, nothing for scripts/cell_depth.py to read)
# and the PARENT's messaging identity. Deliberately EXCLUDED:
# CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS (a harmless global feature flag, not a
# session marker) and HARNESS_ROLE (load-bearing -- set right after by both
# blob builders below).
$script:SessionMarkersToScrub = @(
    'CLAUDE_CODE_CHILD_SESSION', 'CLAUDE_CODE_SESSION_ID',
    'CLAUDECODE', 'CLAUDE_PID',
    'CLAUDE_CODE_MESSAGING_SOCKET', 'CLAUDE_CODE_MESSAGING_TOKEN',
    'CLAUDE_CODE_BRIDGE_SESSION_ID', 'CLAUDE_CODE_ENTRYPOINT',
    'CLAUDE_CODE_EXECPATH', 'CLAUDE_EFFORT'
)

function Get-MarkerScrubPrefix() {
    # The ten Remove-Item statements (joined + terminated) that PREFIX a
    # spawned shell's blob BEFORE the claude invocation, on EVERY vehicle that
    # builds a blob (both Build-PsmuxLaunchCommand and Build-LaunchCommand
    # call this) -- defense in depth: the psmux vehicle is already clean by
    # construction (a psmux window inherits the psmux SERVER's environment,
    # not the launching session's), but the Start-Process fallback is not, and
    # scrubbing both means neither vehicle depends on that isolation holding.
    # -ErrorAction SilentlyContinue: an absent marker (e.g. a shell that never
    # had it) must not fail the spawn.
    $stmts = foreach ($m in $script:SessionMarkersToScrub) {
        "Remove-Item Env:$m -ErrorAction SilentlyContinue"
    }
    return (($stmts -join '; ') + '; ')
}

# The environment every spawned ROLE session runs under, SET (not scrubbed) in
# the blob right after the marker scrub and before HARNESS_ROLE, on BOTH
# vehicles. DISABLE_AUTOUPDATER=1 (operator-directed 2026-09-09): the claude
# CLI self-updates on an incidental invocation, and it did so TWICE in eight
# hours under a live ten-seed tranche -- one game spanned two binaries mid-
# game and was faulted for it. A role session must never move the binary as a
# side effect; the operator updates the CLI deliberately, between tranches,
# with `claude update`, so each update is an EVENT with a timestamp.
# CLAUDE_CODE_GIT_BASH_PATH (CHARC 2026-09-14, comms/orchestrator/read/
# 20260914T091454Z-charc-bash-fault-resolved-by-workaround-*.md): on this box
# ONE file path, C:\Program Files\Git\usr\bin\bash.exe, costs seconds per
# launch (3-9 s measured), while a byte-identical same-directory copy,
# bash-cc.exe, is instant (0.04-0.78 s). Root cause is UNPROVEN and closed as
# such. CLAUDE_CODE_GIT_BASH_PATH points a session's Bash tool at the fast
# copy; it reaches a session only at its NEXT LAUNCH, so every role session
# must set it at spawn. A Git for Windows reinstall wipes the same-directory
# copy silently, so the same path is fail-loud preflighted (see
# Invoke-BashCcPreflight) before any spawn.
# CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1 (operator-directed 2026-09-22): force
# the CLASSIC renderer regardless of the saved user-level `tui` setting. The
# fullscreen renderer draws on the alternate screen and keeps only visible
# messages, so a long-running cell's history leaves the pane and the native
# scrollback is empty; classic keeps the conversation in scrollback with the
# inline subagent progress line. Fullscreen's benefits (flat memory past
# ~400K, mouse capture, post-compaction scrollback) do not apply to a role
# session that rolls at ~400K and is read from its transcript file. Applies at
# the NEXT launch of each role; a live session is untouched.
$script:SpawnEnv = @(
    'DISABLE_AUTOUPDATER=1',
    'CLAUDE_CODE_GIT_BASH_PATH=C:\Program Files\Git\usr\bin\bash-cc.exe',
    'CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1'
)

# The bash-cc.exe path Invoke-BashCcPreflight checks -- DERIVED from
# $script:SpawnEnv's own entry (single source, so the spawned value and the
# preflight check can never drift apart) rather than a second literal. The
# @(...) wrap forces an ARRAY before Where-Object (a single-match filter
# returns a bare scalar STRING, not a 1-element array, so an un-wrapped [0]
# would index the string's first CHARACTER, not select the element).
$bashCcEntry = @($script:SpawnEnv | Where-Object { $_ -like 'CLAUDE_CODE_GIT_BASH_PATH=*' })[0]
$script:BashCcPath = ($bashCcEntry -split '=', 2)[1]

function Get-BashCcCheckPath {
    # The path Invoke-BashCcPreflight checks. A REAL (non-DryRun) launch ALWAYS
    # checks $script:BashCcPath -- a leaked env var can never bypass the real
    # refusal check. -DryRun MAY read HARNESS_BASH_CC_PATH (hermetic test
    # override ONLY, mirroring Get-LaunchMapPath's HARNESS_LAUNCH_MAP) so the
    # refusal control can point at a nonexistent path without touching or
    # renaming the real bash-cc.exe.
    if ($DryRun -and $env:HARNESS_BASH_CC_PATH) { return $env:HARNESS_BASH_CC_PATH }
    return $script:BashCcPath
}

function Invoke-BashCcPreflight {
    # FAIL LOUDLY, before any spawn (DryRun included -- the DryRun is the
    # rehearsal and must fail the same way): if the bash-cc.exe workaround copy
    # is absent (a Git for Windows reinstall wipes it silently), name the path
    # and the remedy, and exit non-zero rather than spawn a role session whose
    # Bash tool points at a missing file.
    $path = Get-BashCcCheckPath
    # -PathType Leaf (launcher-naming commission item 4, the banked
    # launcher-bash residual): a DIRECTORY at this path must fail loudly too --
    # without it, Test-Path -LiteralPath alone returns $true for a directory
    # named bash-cc.exe, and the spawned Bash tool would point at something
    # that is not a runnable file.
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Write-Err "CLAUDE_CODE_GIT_BASH_PATH target not found: $path -- the fast bash-cc.exe copy is missing (a Git for Windows reinstall wipes it silently). Remedy: re-create it as a same-directory copy of bash.exe (C:\Program Files\Git\usr\bin\bash.exe -> bash-cc.exe), then re-run."
        exit 1
    }
}

function Get-SpawnEnvPrefix() {
    # One `$env:NAME='VALUE'` per SpawnEnv entry (NAME=VALUE), joined +
    # terminated like Get-MarkerScrubPrefix so the two prefixes concatenate.
    $stmts = foreach ($kv in $script:SpawnEnv) {
        $k, $v = $kv -split '=', 2
        "`$env:$k='$v'"
    }
    return (($stmts -join '; ') + '; ')
}

function Get-DefaultSessionName($repoRoot) {
    # Derive the shared psmux -SessionName DEFAULT from the repo basename so
    # concurrent harnesses in different checkouts stop colliding in one
    # machine-global session. This is a COMPUTED default -- ValidatePattern guards
    # only BOUND param values (D3-M1) -- so the RESULT is re-validated here before
    # use. REPLACE every run of chars outside the validated alphabet with a single
    # '-' (D3-m2: replace, never strip -- 'foo bar' -> 'foo-bar', NOT 'foobar');
    # collapse the introduced consecutive '-' and trim; fall back to 'agents' on
    # empty (spec sec 1 requires the agents fallback). '.'/'_' are valid and left
    # intact (a 'my.app'/'my_app' repo keeps its name).
    $leaf = Split-Path -Leaf $repoRoot
    $name = [regex]::Replace($leaf, '[^A-Za-z0-9._-]+', '-')
    $name = [regex]::Replace($name, '-{2,}', '-')
    $name = $name.Trim('-')
    if ([string]::IsNullOrEmpty($name)) { return 'agents' }
    if ($name -notmatch '^[A-Za-z0-9._-]+$') { return 'agents' }
    return $name
}

function Invoke-Preflight {
    # Verify the claude CLI exists and carries the flags this launcher uses.
    $cmd = Get-Command claude -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        throw "claude CLI not found on PATH. Install Claude Code or open a shell where 'claude' resolves."
    }
    # Resolve-Claude: capture the resolved claude path from the ORIGINAL inherited
    # PATH NOW -- before Resolve-Psmux augments $env:Path -- so the psmux blob can
    # call-operator-invoke the EXPLICIT claude path (a psmux window inherits the
    # psmux SERVER's environment, which may not carry this shell's PATH).
    $script:ClaudePath = $cmd.Source
    $version = ''
    try { $version = (claude --version | Out-String).Trim() }
    catch { throw "could not run 'claude --version': $($_.Exception.Message)" }

    $help = ''
    try { $help = (claude --help | Out-String) }
    catch { throw "could not run 'claude --help': $($_.Exception.Message)" }

    if (-not ($help -match '(?m)(^|\s)-n[,\s]')) {
        throw "this claude CLI ($version) does not advertise the -n flag in --help (fresh launch uses 'claude -n'); refusing to launch with a guessed flag."
    }
    if (-not ($help -match '--resume')) {
        throw "this claude CLI ($version) does not advertise --resume in --help; refusing to launch with a guessed flag."
    }
    if (-not ($help -match '--permission-mode')) {
        throw "this claude CLI ($version) does not advertise --permission-mode in --help (the seam-4 default uses '--permission-mode auto'); update `$LaunchArgs or refuse."
    }
    if (-not ($help -match '"auto"')) {
        throw "this claude CLI ($version) does not list 'auto' as a --permission-mode choice in --help; update the launcher's `$LaunchArgs to a mode the installed CLI accepts."
    }
    if (-not ($help -match '--model')) {
        throw "this claude CLI ($version) does not advertise --model in --help (the CHARC seam-4 default uses '--model fable'); update `$LaunchArgsByRole or refuse."
    }
    if (-not ($help -match '--effort')) {
        throw "this claude CLI ($version) does not advertise --effort in --help (the CHARC seam-4 default uses '--effort max'); update `$LaunchArgsByRole or refuse."
    }
    return $version
}

function Resolve-Psmux {
    # Resolve the psmux binary. A freshly-winget-installed PATH entry is invisible
    # to an already-open shell, so first REFRESH $env:Path from the Machine+User
    # registry Path values. [Environment]::GetEnvironmentVariable('Path',<scope>)
    # returns the value with REG_EXPAND_SZ %VAR% tokens ALREADY EXPANDED against
    # the process env (verified: no '%' tokens remain) -- the process-env
    # expansion that lets a %LOCALAPPDATA% token collapse under a redirect on a
    # machine where psmux presence is token-based. Registry-only entries are
    # APPENDED after the existing $env:Path (SHIPPED CONTRACT: never prepend, never
    # replace -- an explicitly set env PATH keeps precedence, and a replace could
    # drop an inherited-only claude). The already-present comparison is
    # case-insensitive and trims a trailing '\'.
    $seen = @{}
    foreach ($seg in ($env:Path -split ';')) {
        if ($seg) { $seen[$seg.TrimEnd('\').ToLowerInvariant()] = $true }
    }
    $tail = @()
    foreach ($scope in @('Machine', 'User')) {
        $raw = [Environment]::GetEnvironmentVariable('Path', $scope)
        if (-not $raw) { continue }
        foreach ($seg in ($raw -split ';')) {
            if (-not $seg) { continue }
            $key = $seg.TrimEnd('\').ToLowerInvariant()
            if (-not $seen.ContainsKey($key)) {
                $seen[$key] = $true
                $tail += $seg
            }
        }
    }
    if ($tail.Count -gt 0) {
        $env:Path = $env:Path + ';' + ($tail -join ';')
    }
    $cmd = Get-Command psmux -ErrorAction SilentlyContinue
    if ($null -ne $cmd) { return $cmd.Source }
    # Fallback: the winget package glob. winget keeps a SINGLE package dir per
    # package (the name is fixed -- marlocarlo.psmux_<source>_<hash>, no version
    # component), so there is normally one hit; pick DETERMINISTICALLY by newest
    # LastWriteTime (primary), dir name descending (tie-break) rather than an
    # unspecified "newest".
    if ($env:LOCALAPPDATA) {
        $glob = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages\marlocarlo.psmux_*\psmux.exe'
        $hits = @(Get-ChildItem -Path $glob -ErrorAction SilentlyContinue)
        if ($hits.Count -gt 0) {
            $sorted = $hits | Sort-Object @{ Expression = { $_.LastWriteTime } }, @{ Expression = { $_.Directory.Name } } -Descending
            return ($sorted | Select-Object -First 1).FullName
        }
    }
    return $null
}

function Test-PsmuxCommands($psmux) {
    # Preflight the psmux CLI the way Invoke-Preflight verifies claude: it must run
    # and its list-commands must advertise the command set this launcher uses
    # (--version + list-commands are SERVERLESS -- safe under -DryRun). Any miss
    # sets $script:PsmuxReason (naming the missing command) and returns $false.
    # Discard stderr (2>$null) so a chatty psmux cannot turn native stderr into a
    # terminating error under the script's EAP=Stop; then check $LASTEXITCODE so a
    # psmux that EXITS NONZERO (broken/wrong build) is rejected even if it printed
    # the command names.
    $script:PsmuxReason = ''
    try { $null = (& $psmux --version 2>$null | Out-String) }
    catch { $script:PsmuxReason = "psmux --version failed"; return $false }
    if ($LASTEXITCODE -ne 0) { $script:PsmuxReason = "psmux --version failed (exit $LASTEXITCODE)"; return $false }
    $lc = ''
    try { $lc = (& $psmux list-commands 2>$null | Out-String) }
    catch { $script:PsmuxReason = "psmux list-commands failed"; return $false }
    if ($LASTEXITCODE -ne 0) { $script:PsmuxReason = "psmux list-commands failed (exit $LASTEXITCODE)"; return $false }
    foreach ($req in @('new-session', 'new-window', 'attach-session', 'list-windows', 'has-session')) {
        if ($lc -notmatch [regex]::Escape($req)) {
            $script:PsmuxReason = "psmux preflight miss: $req"
            return $false
        }
    }
    return $true
}

function Get-Vehicle {
    # Decide the spawn vehicle. -NoPsmux SHORT-CIRCUITS to fallback FIRST -- before
    # ANY psmux resolution/preflight -- so it never depends on psmux being present.
    # In THIS increment the psmux SPAWN path is not wired yet, so a resolved +
    # preflight-passing psmux still returns 'fallback' (report and dispatch never
    # diverge); only the reason differs.
    if ($NoPsmux) {
        $script:VehicleReason = '-NoPsmux'
        return 'fallback'
    }
    $psmux = Resolve-Psmux
    if ($null -eq $psmux) {
        $script:VehicleReason = 'psmux not resolved'
        return 'fallback'
    }
    $script:PsmuxPath = $psmux
    if (-not (Test-PsmuxCommands $psmux)) {
        $script:VehicleReason = $script:PsmuxReason
        return 'fallback'
    }
    $script:VehicleReason = "shared psmux session '$SessionName'"
    return 'psmux'
}

# --- psmux spawn helpers ---------------------------------------------------

function ConvertTo-PsSingleQuoted($s) {
    # Escape a string for embedding INSIDE a single-quoted PowerShell literal:
    # double every apostrophe. Spaces are covered by the surrounding quotes; the
    # apostrophe is the residual hazard for a repo/profile path.
    return ($s -replace "'", "''")
}

function Build-PsmuxLaunchCommand($role, $argList) {
    # The psmux-path inner command. Unlike the fallback (bare 'claude'), the psmux
    # blob invokes the EXPLICIT resolved claude path via the CALL OPERATOR (&) --
    # a psmux WINDOW inherits the psmux SERVER's environment (the tmux server-env
    # gotcha), which may not carry this launcher's PATH. Both the resolved claude
    # path AND $RepoRoot are single-quote-escaped.
    $claudeQ = ConvertTo-PsSingleQuoted $script:ClaudePath
    $repoQ = ConvertTo-PsSingleQuoted $RepoRoot
    return (Get-MarkerScrubPrefix) + (Get-SpawnEnvPrefix) + "`$env:HARNESS_ROLE='$role'; Set-Location '$repoQ'; & '$claudeQ' " + ($argList -join ' ')
}

function Get-PsmuxWindowName($psmux, $session, $baseName, $realExists) {
    # Window name = the claude SESSION name (dated; New-SessionName's stamp
    # format is UNCHANGED by this collision-suffix logic).
    # Uniqueness is a psmux-layer concern ONLY: if a window of that name already
    # exists in the session, append -2, -3, ... to the WINDOW name (the claude
    # session name is untouched). list-windows is queried ONLY when the session
    # EXISTS (never an absent target -- that ERRORs); the parse uses the
    # Phase-0-proven '-F #{window_name}' format flag.
    if (-not $realExists) { return $baseName }
    $names = @()
    try {
        $out = & $psmux list-windows -t $session -F '#{window_name}' 2>$null
        if ($LASTEXITCODE -eq 0) {
            foreach ($line in $out) { if ($line) { $names += ("$line").Trim() } }
        }
    }
    catch { }
    # Best-effort: if list-windows could not be read (empty $names), fall back to
    # the base window name -- psmux tolerates duplicate window names, and aborting
    # the whole launch over a cosmetic collision suffix is worse than a best guess.
    if ($names -notcontains $baseName) { return $baseName }
    $i = 2
    while ($names -contains "$baseName-$i") { $i++ }
    return "$baseName-$i"
}

function Get-PsmuxSpawnPlan($role, $argList, $baseName) {
    # Compute the psmux spawn plan ONCE per role (display + execute share it, so
    # they never diverge). session-exists = an in-memory already-emitted-create
    # set (so serial '-Role both' windows the second role into the first's new
    # session) layered on the READ-ONLY has-session probe (side-effect-free per
    # Phase 0; safe under -DryRun). No write occurs here.
    $psmux = $script:PsmuxPath
    $session = $SessionName
    # ALWAYS probe has-session for the REAL existence (read-only + side-effect-free
    # per Phase 0; one probe per role, as today). 2>$null (not 2>&1) so an
    # absent-session stderr line can never terminate under EAP=Stop.
    & $psmux has-session -t $session 2>$null | Out-Null
    $realExists = ($LASTEXITCODE -eq 0)
    # Verb selection uses REAL existence OR an in-memory create this invocation, so
    # a serial '-Role both' windows role 2 into role 1's new session.
    $exists = ($realExists -or $script:CreatedSessions.ContainsKey($session))
    # The window-suffix probe (list-windows) gates on REAL existence ONLY -- never
    # an in-memory-only (DryRun) session, which would be an ABSENT target that
    # list-windows ERRORs on (critic R7-MAJOR-1). Per-invocation roles have
    # distinct base names, so an in-memory-only role needs no suffix.
    $window = Get-PsmuxWindowName $psmux $session $baseName $realExists
    $blob = Get-EncodedCommand (Build-PsmuxLaunchCommand $role $argList)
    $verb = 'new-window'
    if (-not $exists) {
        $verb = 'new-session'
        $script:CreatedSessions[$session] = $true
    }
    return @{ Verb = $verb; Session = $session; Window = $window; Blob = $blob }
}

function Format-PsmuxPathDisplay($psmux) {
    # Render the resolved psmux path for a PRINTED, COPY-PASTEABLE command line. A
    # SPACES-bearing path is wrapped with the CALL OPERATOR + quotes (& "..."),
    # the only form that RUNS as-is at a PS prompt -- a bare "path" arg is parsed
    # as a string LITERAL and echoed, not executed (Phase-1-proven: `& "<path>"`
    # runs, `"<path>"` throws). A spaceless path is left BARE so every current
    # spawn/attach golden stays byte-identical (the conditional is a no-op there).
    if ($psmux -match ' ') {
        # Escape for a PS DOUBLE-quoted literal so a path containing '$', backtick,
        # or '"' (all legal in a Windows path) stays LITERAL when copy-pasted --
        # the double-quote wrapper would otherwise interpolate '$var' / process the
        # backtick. Escape the backtick FIRST (it is the escape char), then '$'/'"'.
        $escaped = $psmux.Replace('`', '``').Replace('$', '`$').Replace('"', '`"')
        return '& "' + $escaped + '"'
    }
    return $psmux
}

function Format-PsmuxSpawn($plan) {
    # Print the EXACT spawn line -DryRun would execute: the RESOLVED psmux path as
    # the command prefix (NOT a bare 'psmux'), matching Start-PsmuxWindow's
    # `& $script:PsmuxPath ...` -- so an operator copy-pasting the DryRun line from
    # a PATH-less shell runs the same resolved binary the launcher would. The path
    # is rendered QUOTED (call-operator) iff it contains a space (spaceless =
    # bare = byte-stable).
    $psmux = Format-PsmuxPathDisplay $script:PsmuxPath
    if ($plan.Verb -eq 'new-session') {
        return "$psmux new-session -d -s $($plan.Session) -n $($plan.Window) powershell -NoExit -EncodedCommand $($plan.Blob)"
    }
    return "$psmux new-window -t $($plan.Session) -n $($plan.Window) powershell -NoExit -EncodedCommand $($plan.Blob)"
}

function Start-PsmuxWindow($plan) {
    # Run the psmux create SYNCHRONOUSLY (a native call, NOT async Start-Process)
    # so the session is CONFIRMED created before the next serial role windows into
    # it -- a '-Role both' race otherwise: new-window could reach the server before
    # the async new-session finished -- AND so a psmux CLI failure is visible via
    # $LASTEXITCODE, not silently lost. 'new-session -d' is detached, so it returns
    # promptly. (The fallback Start-RoleWindow is UNCHANGED for byte-equivalence.)
    $psmux = $script:PsmuxPath
    if ($plan.Verb -eq 'new-session') {
        & $psmux new-session -d -s $plan.Session -n $plan.Window powershell -NoExit -EncodedCommand $plan.Blob
    }
    else {
        & $psmux new-window -t $plan.Session -n $plan.Window powershell -NoExit -EncodedCommand $plan.Blob
    }
    if ($LASTEXITCODE -ne 0) {
        # FAIL LOUDLY: a failed create must abort the launcher (exit 1) -- not
        # continue to window later roles, write a misleading resume map, or open a
        # local attach view for a session that was never created.
        Write-Err "psmux $($plan.Verb) for window '$($plan.Window)' returned exit $LASTEXITCODE -- aborting."
        exit 1
    }
}

function Get-LaunchMapPath {
    # The sessions-map path to READ. A -DryRun launch MAY read an override path
    # from the HARNESS_LAUNCH_MAP env var (hermetic resume testing ONLY -- the
    # SOLE read of that env var in this file); a REAL launch ALWAYS uses
    # comms/.launch-sessions.json, so a leaked env var can never redirect a
    # production launch's map. Save-SessionMap always WRITES $SessionsPath.
    if ($DryRun) {
        $override = $env:HARNESS_LAUNCH_MAP
        if ($override -and (Test-Path $override)) { return $override }
    }
    return $SessionsPath
}

function Get-SessionMap {
    $map = @{}
    $mapPath = Get-LaunchMapPath
    if (Test-Path $mapPath) {
        $raw = Get-Content -Raw -Path $mapPath
        if ($raw -and $raw.Trim().Length -gt 0) {
            $obj = $raw | ConvertFrom-Json
            foreach ($prop in $obj.PSObject.Properties) {
                $entry = @{}
                foreach ($p in $prop.Value.PSObject.Properties) {
                    $entry[$p.Name] = $p.Value
                }
                $map[$prop.Name] = $entry
            }
        }
    }
    return $map
}

function Save-SessionMap($map) {
    if (-not (Test-Path $CommsDir)) {
        New-Item -ItemType Directory -Path $CommsDir -Force | Out-Null
    }
    $json = $map | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($SessionsPath, $json)
}

function New-SessionName($role) {
    # <project>-<role>-<stamp> (launcher-naming commission item 1): $project
    # comes from $script:Project ONLY -- never a literal here.
    $stamp = (Get-Date).ToString('yyyyMMdd-HHmm')
    return "$script:Project-$role-$stamp"
}

function Build-LaunchCommand($role, $argList) {
    # The inner shell command for a spawned role window. Setting
    # $env:HARNESS_ROLE HERE (inside the spawned shell) is load-bearing so the
    # role reaches the hook regardless of how the window was spawned. The
    # backtick escapes the '$' so the OUTER (launcher) shell passes
    # '$env:HARNESS_ROLE' through literally while it DOES expand $role/$RepoRoot.
    return (Get-MarkerScrubPrefix) + (Get-SpawnEnvPrefix) + "`$env:HARNESS_ROLE='$role'; Set-Location '$RepoRoot'; claude " + ($argList -join ' ')
}

function Get-EncodedCommand($inner) {
    # Base64(UTF-16LE) payload for 'powershell -EncodedCommand'. The robust way
    # to hand a multi-statement command to a window: an EncodedCommand blob
    # carries no ';' or quotes for the spawner to misparse, so the whole command
    # (the HARNESS_ROLE assignment + Set-Location + claude) reaches one shell
    # intact.
    return [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($inner))
}

function Use-WtTab {
    # True iff we should open roles as TABS in the existing Windows Terminal window:
    # default ON, unless -NoWT is set OR wt.exe is not on PATH (graceful fallback to
    # a separate window). The wt-availability probe is cached for the run.
    if ($null -eq $script:WtAvailable) {
        $script:WtAvailable = [bool](Get-Command wt -ErrorAction SilentlyContinue)
    }
    return ((-not $NoWT) -and $script:WtAvailable)
}

function Format-Spawn($role, $argList) {
    # The spawn command line as a display string (DryRun + logging), matching the
    # actual Start-RoleWindow path.
    $encoded = Get-EncodedCommand (Build-LaunchCommand $role $argList)
    if (Use-WtTab) {
        return "wt -w 0 new-tab powershell -NoExit -EncodedCommand $encoded"
    }
    return "powershell -NoExit -EncodedCommand $encoded"
}

function Start-RoleWindow($role, $argList) {
    # DEFAULT: open a NEW TAB in the EXISTING Windows Terminal window
    # ('wt -w 0 new-tab', -w 0 = the current window) so a launched role joins the
    # current terminal instead of popping a separate window. Falls back to a plain
    # 'powershell -NoExit' window when -NoWT is set OR wt.exe is unavailable.
    # EncodedCommand carries no ';', so wt does not mis-split it as a tab/pane
    # delimiter; the env-inheritance fix applies to both paths.
    $encoded = Get-EncodedCommand (Build-LaunchCommand $role $argList)
    if (Use-WtTab) {
        Start-Process -FilePath 'wt' -ArgumentList @(
            '-w', '0', 'new-tab', 'powershell', '-NoExit', '-EncodedCommand', $encoded)
    }
    else {
        Start-Process -FilePath 'powershell' -ArgumentList @('-NoExit', '-EncodedCommand', $encoded)
    }
}

function Format-Cmd($argList) {
    return 'claude ' + ($argList -join ' ')
}

# --- per-role launch -------------------------------------------------------

function Start-Fresh($role, $map) {
    $name = New-SessionName $role
    $bootstrapRel = $BootstrapFiles[$role]
    $bootstrapAbs = Join-Path $RepoRoot $bootstrapRel
    if (-not (Test-Path $bootstrapAbs)) {
        throw "bootstrap file missing for $role at $bootstrapAbs"
    }
    $prompt = [string]::Format($FreshPromptFmt, $bootstrapRel)
    $argList = ($LaunchArgsCommon + $LaunchArgsByRole[$role]) + @('-n', "`"$name`"", "`"$prompt`"")
    Write-Info "fresh $role -> session name '$name'"
    Write-Info "  cmd: $(Format-Cmd $argList)"
    $plan = $null
    if ($script:Vehicle -eq 'psmux') {
        $plan = Get-PsmuxSpawnPlan $role $argList $name
        Write-Info "  launch: $(Build-PsmuxLaunchCommand $role $argList)"
        Write-Info "  spawn : $(Format-PsmuxSpawn $plan)"
    }
    else {
        Write-Info "  launch: $(Build-LaunchCommand $role $argList)"
        Write-Info "  spawn : $(Format-Spawn $role $argList)"
    }
    if ($DryRun) { return $map }

    $entry = @{ session_name = $name; created = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
    if ($null -ne $plan) {
        # psmux: create the window FIRST (Start-PsmuxWindow exits 1 on a psmux
        # failure) so a failed create never writes a misleading resume-map entry
        # nor reaches Open-LocalAttach.
        Start-PsmuxWindow $plan
        $map[$role] = $entry
        Save-SessionMap $map
    }
    else {
        # fallback path UNCHANGED (Start-Process is async; map written as before).
        $map[$role] = $entry
        Save-SessionMap $map
        Start-RoleWindow $role $argList
    }
    return $map
}

function Start-Resume($role, $map) {
    if (-not $map.ContainsKey($role)) {
        Write-Err "no recorded session for '$role'. Use fresh mode: .\scripts\launch_role.ps1 -Role $role"
        return $map
    }
    $name = $map[$role].session_name
    if (-not $name) {
        Write-Err "recorded session for '$role' has no session_name. Use fresh mode."
        return $map
    }
    # The recorded name flows into the printed spawn line AND the real -n/--resume
    # argv, so validate it against the SAME conservative pattern as -SessionName
    # (spaces / quotes / ';' / tmux target syntax are spawn/attach hazards). A
    # malformed recorded name is a hard error -- abort loudly, do not launch.
    if ($name -notmatch '^[A-Za-z0-9._-]+$') {
        Write-Err "recorded session name for '$role' is malformed ('$name'); use fresh mode."
        exit 1
    }
    $prompt = [string]::Format($ResumePrompt, $role)
    $argList = ($LaunchArgsCommon + $LaunchArgsByRole[$role]) + @('--resume', "`"$name`"", "`"$prompt`"")
    Write-Info "resume $role -> session name '$name'"
    Write-Info "  cmd: $(Format-Cmd $argList)"
    $plan = $null
    if ($script:Vehicle -eq 'psmux') {
        $plan = Get-PsmuxSpawnPlan $role $argList $name
        Write-Info "  launch: $(Build-PsmuxLaunchCommand $role $argList)"
        Write-Info "  spawn : $(Format-PsmuxSpawn $plan)"
    }
    else {
        Write-Info "  launch: $(Build-LaunchCommand $role $argList)"
        Write-Info "  spawn : $(Format-Spawn $role $argList)"
    }
    Write-Info "  (--resume opens the picker filtered to this name; select it to re-enter.)"
    if ($DryRun) { return $map }
    if ($null -ne $plan) { Start-PsmuxWindow $plan } else { Start-RoleWindow $role $argList }
    return $map
}

function Open-LocalAttach {
    # ONE local attach view per invocation (never per-role), opened AFTER the role
    # loop. The open/don't-open decision uses the reliable JUST-CREATED signal, NOT
    # list-clients: the PRIMARY spec arm is `psmux list-clients -t <session>` ->
    # "already attached" -> do not open, BUT this psmux reports a PHANTOM client
    # for a fresh detached session (Phase 0.2), so a list-clients gate would
    # permanently see "already attached" and never open -- the UNRELIABLE arm
    # (spec sec 3 amended). Operative here: only a session this invocation JUST
    # CREATED gets an auto-opened view; a PRE-EXISTING session prints the attach
    # command (the recovery) and opens nothing. The fallback (non-psmux) vehicle
    # has no shared session, so there is no local attach view.
    if ($script:Vehicle -ne 'psmux') { return }
    $psmux = $script:PsmuxPath
    $session = $SessionName
    $justCreated = $script:CreatedSessions.ContainsKey($session)
    # SPACES-family hardening (D3-M2): the wt-nested `new-tab <psmux> attach` path
    # cannot be assumed to carry a SPACES-bearing psmux path across wt versions
    # (spec: never assume wt's nested parser), so a spaces-bearing path is guarded
    # OFF the wt-tab path and uses a PLAIN attach window (-FilePath $psmux, which
    # is spaces-safe BY CONSTRUCTION -- no nested parser) with a printed reason.
    # The spaceless path keeps today's wt-tab attach byte-for-byte.
    $hasSpace = ($psmux -match ' ')
    $useWtAttach = ((Use-WtTab) -and (-not $hasSpace))
    $psmuxDisplay = Format-PsmuxPathDisplay $psmux
    if ($useWtAttach) {
        $attachCmd = "wt -w 0 new-tab $psmux attach -t $session"
    }
    else {
        $attachCmd = "$psmuxDisplay attach -t $session"
    }
    # Print the spaces-downgrade reason WHENEVER a spaces-bearing path forced the
    # plain attach off the wt-tab path (both the already-exists recovery hint AND
    # the just-created open use the plain `& "..."` form, so the reason applies to
    # both). Gated on $hasSpace, so a spaceless path prints nothing new (byte-stable).
    if ($hasSpace -and (Use-WtTab)) {
        Write-Info "local attach: psmux path contains spaces; using a plain attach window (wt nested-quoting unsafe)."
    }
    if (-not $justCreated) {
        Write-Info "local attach: session '$session' already exists; attach with: $attachCmd"
        return
    }
    if ($DryRun) {
        Write-Info "local attach: would open ($attachCmd)"
        return
    }
    Write-Info "local attach: opening ($attachCmd)"
    if ($useWtAttach) {
        # spec-literal `wt -w 0 new-tab <psmux> attach -t <session>` for a
        # SPACELESS psmux path (byte-stable). A spaces-bearing path never reaches
        # here (it takes the plain-window branch below).
        Start-Process -FilePath 'wt' -ArgumentList @('-w', '0', 'new-tab', $psmux, 'attach', '-t', $session)
    }
    else {
        # plain attach window: -NoWT, wt absent, OR a spaces-bearing psmux path.
        # $psmux is -FilePath (not nested), so Start-Process quotes it natively --
        # spaces-safe regardless of wt's nested parser.
        Start-Process -FilePath $psmux -ArgumentList @('attach', '-t', $session)
    }
}

# --- main ------------------------------------------------------------------

if (Use-WtTab) {
    Write-Info "spawn mode: NEW TAB in the current Windows Terminal window (wt -w 0 new-tab); use -NoWT for separate windows."
}
elseif ($NoWT) {
    Write-Info "spawn mode: separate plain windows (-NoWT)."
}
else {
    Write-Info "spawn mode: separate plain windows (Windows Terminal 'wt' not found on PATH)."
}

try {
    $version = Invoke-Preflight
}
catch {
    Write-Err $_.Exception.Message
    exit 1
}
Write-Info "claude CLI OK: $version"

Invoke-BashCcPreflight

# Derive the shared psmux -SessionName default from the repo basename UNLESS the
# operator bound -SessionName explicitly (D3-M1: a COMPUTED default, so it needs
# Get-DefaultSessionName's own re-validation -- the ValidatePattern attribute only
# guards a BOUND value). Placed here in the main section: every helper (incl.
# Get-DefaultSessionName) is defined by now (PS 5.1 top-to-bottom), and this
# precedes $SessionName's first USE at Get-Vehicle. Because $SessionName carries
# the ValidatePattern attribute, this assignment re-runs that validation on the
# derived value (Get-DefaultSessionName always returns a pattern-valid value, so it
# never throws); an explicit -SessionName is left untouched.
if (-not $PSBoundParameters.ContainsKey('SessionName')) { $SessionName = Get-DefaultSessionName $RepoRoot }

# The ONE psmux-vehicle reason line (spec sec 2; the only permitted delta on the
# fallback startup output). Get-Vehicle resolves + preflights psmux (Resolve-Claude
# already ran inside Invoke-Preflight, before Resolve-Psmux touches $env:Path).
$script:Vehicle = Get-Vehicle
Write-Info "vehicle: $script:Vehicle ($script:VehicleReason)."
if ($DryRun) { Write-Info "DRY RUN -- no windows launched, session map not written." }

if ($Role -eq 'both') { $roles = @('charc', 'orchestrator') }
else { $roles = @($Role) }

$map = Get-SessionMap
foreach ($r in $roles) {
    if ($Resume) { $map = Start-Resume $r $map }
    else { $map = Start-Fresh $r $map }
}

# ONE idempotent local attach view per invocation, AFTER the role loop (psmux
# vehicle only; the just-created gate decides open vs print-the-attach-command).
Open-LocalAttach

Write-Info 'done.'
exit 0
