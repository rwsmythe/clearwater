"""E.1 -- machine-checkable content assertions for scripts/launch_role.ps1.

PowerShell is not run by the unittest runner; the tier-1 tests assert the
load-bearing CONTENT (HARNESS_ROLE, the role set, the seam-4 default, the
wt-tab-default + plain-window-fallback spawn path, the preflight, the psmux
vehicle, hooks-own-the-registry). Tier 2 is a skip-guarded golden `-DryRun`
subprocess matrix (spec sec 5, two-tier so the harness suite stays
machine-portable): each case runs only where its prerequisites are present
(win32 + powershell [+ claude] [+ psmux]); a machine missing them SKIPS (a skip
is not a failure -- the pass/fail SET stays unchanged).
"""

from __future__ import annotations

import base64
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

try:
    import winreg  # type: ignore
except ImportError:  # non-Windows
    winreg = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LAUNCHER = REPO_ROOT / "scripts" / "launch_role.ps1"

# The 8 role-enum/coverage tier-1 methods that MUST survive verbatim (spec sec 5).
_PRESERVED_METHODS = (
    "test_validateset_is_the_role_enum",
    "test_bootstrap_file_for_orchestrator",
    "test_sets_harness_role_env",
    "test_seam4_default_marked_tunable",
    "test_wt_tab_default_with_plain_window_fallback",
    "test_preflight_verifies_flags",
    "test_notes_document_resume_command",
    "test_hooks_own_the_registry_not_the_launcher",
)


# --------------------------------------------------------------------------- #
# tier-2 skip-guard helpers + subprocess driver (spec sec 5; critic R2-MAJOR-3)
# --------------------------------------------------------------------------- #
def _powershell_ok() -> bool:
    return sys.platform == "win32" and bool(shutil.which("powershell"))


def _claude_ok() -> bool:
    return bool(shutil.which("claude"))


def _wt_ok() -> bool:
    # Windows Terminal presence gates the wt-tab attach path: the spaces-downgrade
    # reason is printed ONLY when a spaces path forces a downgrade OFF the wt-tab
    # path (i.e. wt is available); with wt absent the attach is already plain.
    return sys.platform == "win32" and bool(shutil.which("wt"))


def _resolve_psmux() -> str | None:
    """Mirror the launcher's Resolve-Psmux ORDER: the process PATH with the
    Machine+User registry Path entries APPENDED, resolved via which() FIRST, and
    only THEN the winget glob (deterministic newest-mtime pick). Returns a
    resolved path or None."""
    effective = os.environ.get("PATH", "")
    if winreg is not None:
        for hive, sub in (
            (winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            (winreg.HKEY_CURRENT_USER, "Environment"),
        ):
            try:
                with winreg.OpenKey(hive, sub) as k:
                    val, _ = winreg.QueryValueEx(k, "Path")
            except OSError:
                continue
            for seg in str(val).split(";"):
                seg = os.path.expandvars(seg.strip())
                if seg:
                    effective += os.pathsep + seg
    p = shutil.which("psmux", path=effective)
    if p:
        return p
    la = os.environ.get("LOCALAPPDATA", "")
    if la:
        hits = glob.glob(
            os.path.join(
                la, r"Microsoft\WinGet\Packages\marlocarlo.psmux_*\psmux.exe"))
        if hits:
            return max(hits, key=os.path.getmtime)
    return None


def _psmux_ok() -> bool:
    """psmux is available iff it resolves AND its list-commands advertises the
    required command set (critic R1-minor-1 + R2-MAJOR-4). NOT implemented via
    the launcher -DryRun (which returns success through the fallback)."""
    if sys.platform != "win32":
        return False
    p = _resolve_psmux()
    if not p:
        return False
    try:
        # match Test-PsmuxCommands: --version must run AND list-commands must
        # advertise the full required set (incl. has-session).
        ver = subprocess.run(
            [p, "--version"], capture_output=True, text=True, timeout=30)
        if ver.returncode != 0:
            return False
        out = subprocess.run(
            [p, "list-commands"], capture_output=True, text=True, timeout=30)
    except Exception:
        return False
    txt = (out.stdout or "") + (out.stderr or "")
    return all(c in txt for c in
               ("new-session", "new-window", "attach-session", "list-windows",
                "has-session"))


def _psmux_hideable() -> bool:
    """True iff psmux can be hermetically HIDDEN by env masking -- i.e. it is NOT
    on the registry Path as a LITERAL (non-%VAR%) segment. Reads the RAW registry
    Path (winreg.QueryValueEx does NOT expand REG_EXPAND_SZ). A literal psmux
    segment survives any env mask (a registry read ignores the process PATH), so
    the true-absence golden (A) cannot be simulated hermetically -> not hideable
    (it SKIPS; the preflight-miss golden (B) covers the fallback outcome)."""
    if sys.platform != "win32" or winreg is None:
        return False
    for hive, sub in (
        (winreg.HKEY_LOCAL_MACHINE,
         r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        (winreg.HKEY_CURRENT_USER, "Environment"),
    ):
        try:
            with winreg.OpenKey(hive, sub) as k:
                val, _ = winreg.QueryValueEx(k, "Path")
        except OSError:
            continue
        for seg in str(val).split(";"):
            s = seg.strip()
            if not s or "%" in s:  # a %VAR% token is redirectable
                continue
            if os.path.exists(os.path.join(s, "psmux.exe")):
                return False  # literal psmux presence -> NOT hideable
    return True


def _run_launcher(*args: str, env: dict | None = None, dryrun: bool = True):
    """Invoke launch_role.ps1 [-DryRun] <args> and capture (rc, stdout, stderr)."""
    cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(LAUNCHER),
    ]
    if dryrun:
        cmd.append("-DryRun")
    cmd.extend(args)
    child_env = os.environ.copy()
    if env:
        child_env.update(env)
    return subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(REPO_ROOT),
        env=child_env, timeout=120)


def _decode_blob(spawn_line: str) -> str | None:
    """Extract the Base64 -EncodedCommand token from a spawn line and return
    the decoded UTF-16LE inner command (the behavioral assertion surface)."""
    m = re.search(r"-EncodedCommand\s+(\S+)", spawn_line)
    if not m:
        return None
    return base64.b64decode(m.group(1)).decode("utf-16-le")


def _spawn_line(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if "spawn :" in line:
            return line.split("spawn :", 1)[1].strip()
    return None


def _session_name(stdout: str, role: str) -> str | None:
    m = re.search(
        r"(?:fresh|resume) " + re.escape(role) +
        r" -> session name '([^']+)'", stdout)
    return m.group(1) if m else None


def _all_spawn_lines(stdout: str) -> list:
    return [line.split("spawn :", 1)[1].strip()
            for line in stdout.splitlines() if "spawn :" in line]


def _isolated_session() -> str:
    # a -SessionName guaranteed ABSENT (ValidatePattern-legal) for deterministic
    # goldens: has-session absent -> new-session, BASE window name, no probes.
    return "ztest-" + uuid.uuid4().hex[:10]


def _info_lines(stdout: str) -> list:
    """The launcher's '[launch-role] ' output lines, prefix stripped, in order."""
    pfx = "[launch-role] "
    return [ln[len(pfx):] for ln in stdout.splitlines() if ln.startswith(pfx)]


def _blob(inner: str) -> str:
    """The Base64(UTF-16LE) EncodedCommand blob for an inner command (the same
    construction Get-EncodedCommand uses) -- lets a golden rebuild the EXACT
    fallback spawn line self-contained, including the blob."""
    return base64.b64encode(inner.encode("utf-16-le")).decode("ascii")


def _fallback_mode_line(lines: list, nowt: bool = False) -> str:
    """Today's spawn-mode line for the fallback path. Three arms: wt-tab default
    (wt present, no -NoWT); '-NoWT' plain windows (-NoWT forced); and 'wt not
    found' plain windows (wt absent). wt-vs-plain is inferred from the printed
    spawn; the two plain arms are distinguished by the known -NoWT flag."""
    is_wt = any(ln.startswith("  spawn : wt -w 0 new-tab") for ln in lines)
    if is_wt:
        return ("spawn mode: NEW TAB in the current Windows Terminal window "
                "(wt -w 0 new-tab); use -NoWT for separate windows.")
    if nowt:
        return "spawn mode: separate plain windows (-NoWT)."
    return ("spawn mode: separate plain windows "
            "(Windows Terminal 'wt' not found on PATH).")


def _fallback_spawn_display(inner: str, is_wt: bool) -> str:
    blob = _blob(inner)
    if is_wt:
        return "wt -w 0 new-tab powershell -NoExit -EncodedCommand " + blob
    return "powershell -NoExit -EncodedCommand " + blob


def _psmux_display(path: str) -> str:
    """Mirror the launcher's Format-PsmuxPathDisplay: a SPACES-bearing psmux path
    is rendered `& "<path>"` (call operator, copy-pasteable) in printed spawn/attach
    lines, with the path escaped for a PS double-quoted literal (backtick first,
    then '$'/'"'); a spaceless path is BARE. Lets the psmux goldens assert the
    correct prefix on BOTH a spaceless ambient path (this machine) and a
    hypothetical spaces-ambient one -- so a correct launcher is never falsely
    rejected. (For the real machine's metacharacter-free path the escape chain is a
    no-op, so the common quoted form is exactly `& "<path>"`.)"""
    if " " in path:
        esc = path.replace("`", "``").replace("$", "`$").replace('"', '`"')
        return '& "' + esc + '"'
    return path


def _expected_default_session(repo_root_name: str) -> str:
    """Mirror the launcher's Get-DefaultSessionName sanitizer so a runtime golden
    can assert the DERIVED default without hardcoding a checkout-specific basename
    (the build worktree's basename differs from the merged main tree's). REPLACE
    invalid runs with '-' (never strip), collapse consecutive '-', trim, then fall
    back to 'agents' on empty / re-validate failure."""
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", repo_root_name)
    name = re.sub(r"-{2,}", "-", name)
    name = name.strip("-")
    if not name:
        return "agents"
    if not re.match(r"^[A-Za-z0-9._-]+$", name):
        return "agents"
    return name


def _expected_default_project(repo_root_name: str) -> str:
    """Mirror the launcher's Get-DefaultProject (launcher-naming commission
    item 1) so a runtime golden can assert New-SessionName's <project> segment
    without hardcoding a checkout-specific basename -- same sanitizer as
    _expected_default_session, then the segment BEFORE the first '-'."""
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", repo_root_name)
    name = re.sub(r"-{2,}", "-", name)
    name = name.strip("-")
    if not name:
        return "agents"
    token = name.split("-")[0]
    if not token:
        return "agents"
    return token


def _main_checkout_root() -> Path:
    """The MAIN checkout root as git itself reports it (the parent of the
    shared .git dir via `rev-parse --git-common-dir`) -- resolves identically
    whether invoked from the main tree or ANY linked worktree (Reviewer B r1
    finding B-1). Mirrors the launcher's own Resolve-MainCheckoutRoot."""
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse",
         "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return Path(out.stdout.strip()).parent


def _extract_ps_function(src: str, name: str) -> str | None:
    """Extract a brace-balanced PowerShell `function <name>(...) { ... }` block
    from source text (so a golden can dot-source ONLY that function, not the whole
    launcher). Returns the full function text or None. The param list is
    OPTIONAL (`(...)` ) -- some helpers in this file (Invoke-Preflight,
    Resolve-Psmux among them) are declared with no parens at all."""
    m = re.search(
        r"function\s+" + re.escape(name) + r"\s*(\([^)]*\))?\s*\{", src)
    if not m:
        return None
    depth = 0
    open_brace = m.end() - 1  # index of the opening '{'
    for i in range(open_brace, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[m.start():i + 1]
    return None


def _extract_ps_array_block(src: str, name: str) -> str | None:
    """Extract a paren-balanced `$script:<name> = @( ... )` array literal from
    source text, mirroring _extract_ps_function's technique -- lets a golden
    dot-source the REAL scrub list, not a mirrored copy of it."""
    m = re.search(r"\$script:" + re.escape(name) + r"\s*=\s*@\(", src)
    if not m:
        return None
    depth = 0
    open_paren = m.end() - 1
    for i in range(open_paren, len(src)):
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
            if depth == 0:
                return src[m.start():i + 1]
    return None


# -- marker-scrub positive control (launcher-marker-scrub brief sec 3 test 2) - #
# The TEN CLAUDE* session markers Get-MarkerScrubPrefix removes, and the ONE
# global flag it deliberately leaves alone (mirrors the launcher's own list --
# the control below runs the SHIPPED list+function extracted from source, so
# this tuple only drives what the test SETS in the child env, never what it
# trusts to be removed).
_MARKERS_TO_SCRUB = (
    "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_SESSION_ID",
    "CLAUDECODE", "CLAUDE_PID",
    "CLAUDE_CODE_MESSAGING_SOCKET", "CLAUDE_CODE_MESSAGING_TOKEN",
    "CLAUDE_CODE_BRIDGE_SESSION_ID", "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_EXECPATH", "CLAUDE_EFFORT",
)
_GLOBAL_FLAG = "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"


def _marker_scrub_prefix() -> str:
    """Mirror the launcher's Get-MarkerScrubPrefix output textually (order +
    joiner), for goldens that assert the COMPLETE built blob -- the actual
    scrub behavior is what test_marker_scrub_positive_control_* verify."""
    return "; ".join(
        "Remove-Item Env:%s -ErrorAction SilentlyContinue" % m
        for m in _MARKERS_TO_SCRUB) + "; "


# The env the launcher SETS in every spawned blob (mirrors $script:SpawnEnv;
# the launcher-side content assertion is test_spawn_env_sets_disable_autoupdater).
# CLAUDE_CODE_GIT_BASH_PATH (2026-09-14, the bash-cc.exe launch-path workaround):
# points a spawned session's Bash tool at the fast same-directory copy instead
# of the slow C:\...\bin\bash.exe (see Invoke-BashCcPreflight, the fail-loud
# refusal when the copy is absent).
# CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN (2026-09-22, operator-directed): force the
# classic renderer so a role session's history stays in native scrollback.
_SPAWN_ENV = (
    ("DISABLE_AUTOUPDATER", "1"),
    ("CLAUDE_CODE_GIT_BASH_PATH", "C:\\Program Files\\Git\\usr\\bin\\bash-cc.exe"),
    ("CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN", "1"),
)


def _expected_claude_survivors() -> list:
    """The CLAUDE* env-var NAMES a spawned blob's marker-scrub positive control
    must show surviving: the global flag (deliberately never scrubbed) PLUS
    every _SPAWN_ENV entry whose name is itself CLAUDE*-prefixed (deliberately
    SET by Get-SpawnEnvPrefix, not a scrub-list gap). DERIVED from _SPAWN_ENV
    (2026-09-14 remediation) rather than hand-listed, so a future SpawnEnv
    entry cannot silently desync this expectation."""
    return sorted(
        [_GLOBAL_FLAG] + [name for name, _ in _SPAWN_ENV if name.startswith("CLAUDE")])


def _spawn_env_prefix() -> str:
    """Mirror the launcher's Get-SpawnEnvPrefix output textually (order +
    joiner), placed between the marker scrub and HARNESS_ROLE in every
    built blob."""
    return "; ".join("$env:%s='%s'" % kv for kv in _SPAWN_ENV) + "; "


def _blob_prefix_before_claude(inner: str) -> str:
    """Cut a builder's output (built with an EMPTY argList) at the exact point
    the claude invocation would begin, so a probe command can be substituted
    for it -- proving what runs BEFORE claude (REACHABILITY_AND_ORDER) without
    ever touching what claude itself would see. Handles both shipped shapes:
    the fallback's bare '...; claude ' and the psmux call-operator
    "...; & '<path>' "."""
    if inner.endswith("claude "):
        return inner[: -len("claude ")]
    idx = inner.rfind("& '")
    if idx != -1 and inner.endswith("' "):
        return inner[:idx]
    raise AssertionError("unrecognized builder output shape: " + repr(inner))


def _run_ps_file(lines: list) -> "subprocess.CompletedProcess":
    """Write `lines` to a temp .ps1 and run it (-File, not -Command, so a
    multi-line dot-sourced function body needs no escaping) in an otherwise
    unmodified child environment."""
    fd, tmp = tempfile.mkstemp(suffix=".ps1", prefix="markerscrub-build-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", tmp],
            capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(tmp)


def _surviving_claude_env_names(inner_prefix: str) -> list:
    """THE POSITIVE CONTROL: run `inner_prefix` (everything a builder emits
    before the claude invocation) in a FRESH child process whose env has the
    ten session markers AND the global flag SET, then probe with
    `Get-ChildItem Env:CLAUDE*` -- the ACTUAL post-removal environment a
    successor would inherit, never the blob's string content. Returns the
    surviving CLAUDE* variable names, sorted."""
    probe = (inner_prefix +
             "Get-ChildItem Env:CLAUDE* | Select-Object -ExpandProperty Name")
    child_env = os.environ.copy()
    # HERMETIC (2026-09-14 remediation): drop every CLAUDE* key inherited from
    # THIS process's own environment before seeding the ten markers + the
    # global flag -- a host-set CLAUDE* variable (e.g. the operator's
    # user-scope CLAUDE_CODE_GIT_BASH_PATH, set for the bash-cc.exe launch-path
    # workaround) would otherwise leak into the "fresh" child and be
    # indistinguishable from a real scrub-list gap.
    for k in list(child_env):
        if k.startswith("CLAUDE"):
            del child_env[k]
    for m in _MARKERS_TO_SCRUB:
        child_env[m] = "x"
    child_env[_GLOBAL_FLAG] = "1"
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-Command", probe],
        capture_output=True, text=True, env=child_env, timeout=60)
    assert r.returncode == 0, r.stderr  # CONTROL_FOR_THE_RIGHT_REASON: the
    # spawn itself must succeed -- a nonzero exit here would make a later
    # empty-survivor reading indistinguishable from "the probe never ran".
    return sorted(ln.strip() for ln in r.stdout.splitlines() if ln.strip())


class LaunchRoleContentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = (REPO_ROOT / "scripts" / "launch_role.ps1").read_text(
            encoding="utf-8")

    # -- Step 1.0: self-referential preservation meta-test (critic R6-MAJOR-4) --
    def test_role_coverage_methods_preserved(self) -> None:
        loaded = set(
            unittest.TestLoader().getTestCaseNames(LaunchRoleContentTest))
        self.assertTrue(
            set(_PRESERVED_METHODS).issubset(loaded),
            "a preserved role-enum/coverage test method was removed/renamed")
        # load-bearing substrings must still be present in the module source
        src = Path(__file__).read_text(encoding="utf-8")
        for token in (
            "ValidateSet('charc', 'orchestrator', 'both')",
            "docs/orchestrator-context.md",
            "HOOKS own",
            ".launch-sessions.json",
        ):
            self.assertIn(token, src,
                          "a preserved load-bearing substring was dropped")

    # -- the 8 preserved tier-1 methods (VERBATIM; spec sec 5) --------------- #
    def test_validateset_is_the_role_enum(self) -> None:
        self.assertIn(
            "ValidateSet('charc', 'orchestrator', 'both')", self.text)

    def test_bootstrap_file_for_orchestrator(self) -> None:
        self.assertIn("docs/orchestrator-context.md", self.text)

    def test_sets_harness_role_env(self) -> None:
        self.assertIn("HARNESS_ROLE", self.text)
        self.assertNotIn("SWING_ROLE", self.text)  # the legacy env var is gone

    def test_seam4_default_marked_tunable(self) -> None:
        self.assertIn("SEAM 4", self.text)
        self.assertIn("$LaunchArgs", self.text)

    def test_wt_tab_default_with_plain_window_fallback(self) -> None:
        # DEFAULT: open each role as a NEW TAB in the existing Windows Terminal
        # window (wt -w 0 new-tab). -NoWT, or wt not on PATH, falls back to a
        # separate plain 'powershell -NoExit' window (Use-WtTab gates the choice).
        self.assertIn("-FilePath 'wt'", self.text)   # the wt-tab spawn path
        self.assertIn("new-tab", self.text)
        self.assertIn("Use-WtTab", self.text)        # default-on / fallback gate
        self.assertIn("'powershell'", self.text)     # the plain-window fallback
        self.assertIn("-NoExit", self.text)

    def test_preflight_verifies_flags(self) -> None:
        self.assertIn("Invoke-Preflight", self.text)
        self.assertIn("--permission-mode", self.text)
        self.assertIn("--resume", self.text)

    def test_notes_document_resume_command(self) -> None:
        # B-16 part (b): the .NOTES block documents the manual deliberate-resume
        # command (placeholder-only; no concrete role/project term).
        self.assertIn("--resume <id>", self.text)
        self.assertIn("$env:HARNESS_ROLE='<role>'", self.text)

    def test_spawn_env_sets_disable_autoupdater(self):
        """Operator-directed 2026-09-09: every spawned role session runs with
        DISABLE_AUTOUPDATER=1 (the CLI self-updated twice under a live tranche;
        one game spanned two binaries mid-game). Both blob builders must call
        Get-SpawnEnvPrefix, and the table must carry the flag."""
        self.assertIn("'DISABLE_AUTOUPDATER=1'", self.text)
        self.assertEqual(self.text.count("(Get-MarkerScrubPrefix) + (Get-SpawnEnvPrefix) + "), 2,
                         "both Build-PsmuxLaunchCommand and Build-LaunchCommand set the spawn env")

    def test_spawn_env_sets_bash_cc_path(self):
        """2026-09-14 (the bash-cc.exe launch-path workaround): every spawned
        role session sets CLAUDE_CODE_GIT_BASH_PATH to the fast same-directory
        copy beside DISABLE_AUTOUPDATER, in the SAME $script:SpawnEnv table (so
        test_spawn_env_sets_disable_autoupdater's "both builders call
        Get-SpawnEnvPrefix" assertion already covers this entry's reachability)."""
        self.assertIn(
            "'CLAUDE_CODE_GIT_BASH_PATH=C:\\Program Files\\Git\\usr\\bin\\bash-cc.exe'",
            self.text)

    def test_bash_cc_preflight_fails_loud_before_spawn(self):
        """The fail-loud refusal (brief sec 1 item 2): Test-Path -LiteralPath
        checks the bash-cc.exe copy BEFORE any spawn, and Invoke-BashCcPreflight
        is called before the role loop (the vehicle/role-spawn code) in main."""
        self.assertIn("Test-Path -LiteralPath $path", self.text)
        self.assertIn("function Invoke-BashCcPreflight", self.text)
        preflight_idx = self.text.index("Invoke-BashCcPreflight\n")
        role_loop_idx = self.text.index("foreach ($r in $roles)")
        self.assertLess(preflight_idx, role_loop_idx,
                         "the fail-loud preflight must run before any role is spawned")

    def test_hooks_own_the_registry_not_the_launcher(self) -> None:
        # The launcher must NOT WRITE the liveness registry (the hooks do). It
        # may MENTION comms/sessions/ to explain the hooks own it, but it must
        # not save an entry there -- its only persisted map is the display-name
        # convenience map (comms/.launch-sessions.json), NOT comms/sessions/.
        self.assertIn("HOOKS own", self.text)
        self.assertIn(".launch-sessions.json", self.text)
        # No Save call targets the hook registry dir.
        self.assertNotIn("Join-Path $CommsDir 'sessions'", self.text)
        self.assertNotIn('comms/sessions/<session_id>.json"', self.text)

    # -- Step 1.2 (cycle 1a): the psmux param surface (FAILING before 1.3) --- #
    def test_sessionname_param_validated(self) -> None:
        # the REAL param-block spelling (critic R8-MAJOR-6), not a docs mention.
        self.assertIn("[ValidatePattern('^[A-Za-z0-9._-]+$')]", self.text)
        self.assertIn("[string]$SessionName = 'agents'", self.text)

    def test_nopsmux_switch_present(self) -> None:
        self.assertIn("[switch]$NoPsmux", self.text)

    def test_fallback_start_process_shape_pinned(self) -> None:
        # the fallback Start-RoleWindow live argv (critic R8-MAJOR-2), not just
        # the printed spawn line -- so a build cannot drift Start-RoleWindow
        # while keeping Format-Spawn identical. Today's shapes.
        self.assertIn("-FilePath 'wt' -ArgumentList @(", self.text)
        self.assertIn(
            "'-w', '0', 'new-tab', 'powershell', '-NoExit', '-EncodedCommand'",
            self.text)
        self.assertIn(
            "-FilePath 'powershell' -ArgumentList @('-NoExit', "
            "'-EncodedCommand', $encoded)", self.text)

    # -- Phase 2: psmux resolution + preflight + APPEND-not-prepend contract -- #
    def test_psmux_resolution_refreshes_path_and_globs_winget(self) -> None:
        self.assertIn("[Environment]::GetEnvironmentVariable('Path', $scope)",
                      self.text)
        self.assertIn("'Machine'", self.text)
        self.assertIn("'User'", self.text)
        self.assertIn("marlocarlo.psmux_*", self.text)
        self.assertIn("psmux.exe", self.text)
        self.assertIn("LOCALAPPDATA", self.text)

    def test_psmux_preflight_verifies_command_set(self) -> None:
        self.assertIn("list-commands", self.text)
        # the preflight required set INCLUDES has-session (it is used to plan
        # new-session vs new-window), so a psmux lacking it falls back.
        self.assertIn(
            "@('new-session', 'new-window', 'attach-session', 'list-windows', "
            "'has-session')", self.text)

    def test_psmux_registry_entries_expanded_against_process_env(self) -> None:
        # On this platform [Environment]::ExpandEnvironmentStrings is absent, but
        # GetEnvironmentVariable('Path',<scope>) already returns REG_EXPAND_SZ
        # values EXPANDED against the process env -- the equivalent property that
        # makes a %LOCALAPPDATA% token collapse under a redirect (critic
        # R3-CRITICAL-1 / R4-MAJOR-2; relevant to the skip-guarded true-absence
        # golden). Assert the file uses that expanding read + documents it.
        self.assertIn("GetEnvironmentVariable('Path'", self.text)
        self.assertIn("process env", self.text)

    def test_psmux_path_refresh_appends_registry_after_process_path(self) -> None:
        # NEW SHIPPED CONTRACT (amended ed56074): registry-only entries are
        # APPENDED after the existing $env:Path (never prepended/replaced), so an
        # explicitly set env PATH (e.g. the preflight-miss stub dir) keeps
        # precedence -- what lets the (B) stub win resolution.
        self.assertIn("$env:Path = $env:Path + ';' + ($tail -join ';')",
                      self.text)
        self.assertNotIn("($tail -join ';') + ';' + $env:Path", self.text)

    # -- Phase 3: the psmux spawn shape + call-operator blob + window name ---- #
    def test_psmux_spawn_has_session_new_session_new_window(self) -> None:
        self.assertIn("has-session -t", self.text)
        self.assertIn("new-session -d -s", self.text)
        self.assertIn("new-window -t", self.text)

    def test_psmux_blob_uses_call_operator_resolved_claude(self) -> None:
        # the psmux blob call-operator-invokes the resolved claude path (single-
        # quote-escaped); the FALLBACK blob still uses BARE claude (both present).
        self.assertIn("& '$claudeQ'", self.text)           # psmux call operator
        self.assertIn("$script:ClaudePath = $cmd.Source", self.text)  # resolved
        self.assertIn("Set-Location '$RepoRoot'; claude ", self.text)  # fallback

    def test_window_name_is_session_name_with_suffix_via_list_windows(self) -> None:
        self.assertIn("Get-PsmuxWindowName", self.text)
        self.assertIn("list-windows -t $session -F '#{window_name}'", self.text)
        self.assertIn('"$baseName-$i"', self.text)          # collision suffix
        # New-SessionName's stamp format is unchanged (minute format)
        self.assertIn("(Get-Date).ToString('yyyyMMdd-HHmm')", self.text)

    def test_psmux_suffix_probe_gates_on_real_existence(self) -> None:
        # the list-windows suffix probe must gate on has-session-derived REAL
        # existence ($realExists), NOT the merged in-memory create flag -- else a
        # -DryRun -Role both would list-windows an ABSENT target (Reviewer B).
        self.assertIn("$realExists = ($LASTEXITCODE -eq 0)", self.text)
        self.assertIn(
            "Get-PsmuxWindowName $psmux $session $baseName $realExists",
            self.text)
        self.assertIn(
            "$exists = ($realExists -or "
            "$script:CreatedSessions.ContainsKey($session))", self.text)
        # inside the helper, the probe is guarded by (-not $realExists) -> baseName
        self.assertIn("if (-not $realExists) { return $baseName }", self.text)

    def test_resume_validates_recorded_session_name(self) -> None:
        # the recorded resume name is validated against the -SessionName pattern
        # before it flows into the spawn line / argv (Reviewer B).
        self.assertIn("if ($name -notmatch '^[A-Za-z0-9._-]+$')", self.text)
        self.assertIn("is malformed", self.text)

    def test_psmux_spawn_is_synchronous_with_exit_check(self) -> None:
        # the psmux create runs SYNCHRONOUSLY (native &, not async Start-Process)
        # so '-Role both' never races and a CLI failure is FATAL (exits 1), not
        # merely logged (copowers R1 + R3).
        self.assertIn(
            "& $psmux new-session -d -s $plan.Session -n $plan.Window "
            "powershell -NoExit -EncodedCommand $plan.Blob", self.text)
        self.assertIn(
            "& $psmux new-window -t $plan.Session -n $plan.Window "
            "powershell -NoExit -EncodedCommand $plan.Blob", self.text)
        self.assertIn("if ($LASTEXITCODE -ne 0)", self.text)
        # a failed create is FATAL (fail-loud), and the spawn precedes the map save
        self.assertIn("-- aborting.", self.text)

    # -- Phase 4: HARNESS_LAUNCH_MAP override is DryRun-only (structural) ----- #
    def test_harness_launch_map_override_dryrun_only(self) -> None:
        # (i) the env var is read EXACTLY ONCE in the whole file.
        self.assertEqual(self.text.count("$env:HARNESS_LAUNCH_MAP"), 1)
        lines = self.text.splitlines()
        idx = [i for i, ln in enumerate(lines)
               if "$env:HARNESS_LAUNCH_MAP" in ln]
        self.assertEqual(len(idx), 1)
        # (ii) that single read sits just after an `if ($DryRun` (line-proximity,
        # not a brace parse) -- i.e. inside the DryRun guard of the helper.
        window = "\n".join(lines[max(0, idx[0] - 3):idx[0] + 1])
        self.assertIn("if ($DryRun", window)
        # (iii) it is localized to the dedicated helper.
        self.assertIn("Get-LaunchMapPath", self.text)
        # (iv) comms/.launch-sessions.json is the UNCONDITIONAL production default.
        self.assertIn("return $SessionsPath", self.text)
        self.assertIn(".launch-sessions.json", self.text)

    # -- Phase 5: idempotent local attach (degraded just-created gate) -------- #
    def test_local_attach_degraded_just_created_gate(self) -> None:
        # OPERATIVE decision = the just-created signal (NOT list-clients, which is
        # PHANTOM/unreliable on this psmux -- amended ed56074).
        self.assertIn(
            "$justCreated = $script:CreatedSessions.ContainsKey($session)",
            self.text)
        self.assertIn("already exists; attach with:", self.text)  # pre-existing
        self.assertIn("would open", self.text)                    # DryRun open
        self.assertIn("opening", self.text)                       # real open
        # the primary list-clients arm is DOCUMENTED but not load-bearing here.
        self.assertIn("list-clients", self.text)
        self.assertIn("PHANTOM", self.text)

    def test_local_attach_uses_spec_attach_command(self) -> None:
        # spec-literal `attach -t <session>` in both vehicles (spec sec 3).
        self.assertIn(
            "@('-w', '0', 'new-tab', $psmux, 'attach', '-t', $session)",
            self.text)
        self.assertIn(
            "-FilePath $psmux -ArgumentList @('attach', '-t', $session)",
            self.text)

    def test_local_attach_helper_invoked_once_post_loop(self) -> None:
        # a dedicated Open-LocalAttach helper CALLED once AFTER the role loop, with
        # the real Start-Process attach shapes in its body (so a build can't ship
        # only the DryRun print and never wire the real attach).
        self.assertGreaterEqual(self.text.count("Open-LocalAttach"), 2)
        lines = self.text.splitlines()
        loop_idx = next(i for i, ln in enumerate(lines)
                        if "foreach ($r in $roles)" in ln)
        call_idxs = [i for i, ln in enumerate(lines)
                     if ln.strip() == "Open-LocalAttach"]
        self.assertTrue(any(i > loop_idx for i in call_idxs),
                        "Open-LocalAttach is not called after the role loop")
        self.assertIn(
            "Start-Process -FilePath 'wt' -ArgumentList @('-w', '0', "
            "'new-tab', $psmux, 'attach', '-t', $session)", self.text)
        self.assertIn(
            "Start-Process -FilePath $psmux -ArgumentList "
            "@('attach', '-t', $session)", self.text)

    def test_remote_attach_documented_in_synopsis(self) -> None:
        # Step 2.2, corrected by the suite-review arc A ruling: the synopsis
        # remote-attach example must document the RULE, not a literal repo name
        # -- a hardcoded literal here could drift from the real derivation with
        # nothing to catch it. It shows the PLACEHOLDER form; the coupling this
        # test used to hold (docstring == real derived default) is NOT dropped,
        # it is STRENGTHENED at test_get_default_session_name_sanitizes (below),
        # which extracts the shipped Get-DefaultSessionName function and runs it
        # over synthetic inputs -- so the derivation stays behaviorally tested
        # for ANY repo, not just this one. This method is NOT one of the 8
        # preserved role-enum/coverage methods, so updating it is in-bounds.
        self.assertIn("psmux attach -t <repo-basename>", self.text)
        self.assertIn("detach leaves", self.text)

    # -- Phase 2: per-repo default via the validated Get-DefaultSessionName ---- #
    def test_default_session_name_is_repo_derived(self) -> None:
        # the -SessionName DEFAULT derives from the repo basename through a
        # dedicated validated sanitizer (D3-M1: ValidatePattern guards BOUND
        # values, so a computed default needs its own re-validated path), and the
        # body gate derives it only when the param was NOT explicitly bound.
        self.assertIn("function Get-DefaultSessionName", self.text)
        self.assertIn("Split-Path -Leaf", self.text)
        # REPLACE invalid runs with '-' (D3-m2: replace, never strip)
        self.assertIn(
            "[regex]::Replace($leaf, '[^A-Za-z0-9._-]+', '-')", self.text)
        # empty -> 'agents' fallback (spec sec 1 REQUIRES the agents fallback)
        self.assertIn(
            "if ([string]::IsNullOrEmpty($name)) { return 'agents' }", self.text)
        # RE-VALIDATE the derived result before use (D3-M1)
        self.assertIn(
            "if ($name -notmatch '^[A-Za-z0-9._-]+$') { return 'agents' }",
            self.text)
        # the body gate derives only when -SessionName was NOT explicitly bound
        self.assertIn(
            "if (-not $PSBoundParameters.ContainsKey('SessionName')) { "
            "$SessionName = Get-DefaultSessionName $RepoRoot }", self.text)
        # PLACEMENT is load-bearing (PS 5.1 runs function statements top-to-bottom;
        # $SessionName must derive AFTER Get-DefaultSessionName is defined and
        # BEFORE its first use at Get-Vehicle). Pin the source order here so a
        # psmux-less machine (where the runtime golden SKIPS) still catches a
        # mis-placed derivation that would leave planning on the 'agents' default.
        fn_def = self.text.index("function Get-DefaultSessionName")
        gate = self.text.index(
            "if (-not $PSBoundParameters.ContainsKey('SessionName'))")
        vehicle = self.text.index("$script:Vehicle = Get-Vehicle")
        self.assertLess(fn_def, gate, "gate precedes the helper definition")
        self.assertLess(gate, vehicle, "gate does not precede first use")

    def test_new_session_name_is_project_role_stamp(self) -> None:
        # launcher-naming commission item 1 (2026-09-15T07:25Z): New-SessionName
        # (the per-role claude DISPLAY name) mints '<project>-<role>-<stamp>',
        # $project read from the ONE constant $script:Project -- never a literal
        # inside the function. New-SessionName is NOT the shared psmux session
        # name (that stays Get-DefaultSessionName/-SessionName, D3-m1); the
        # minute-format stamp is unchanged by this rung.
        self.assertIn("(Get-Date).ToString('yyyyMMdd-HHmm')", self.text)
        self.assertIn('return "$script:Project-$role-$stamp"', self.text)
        self.assertIn("function Get-DefaultProject", self.text)
        self.assertIn("$script:Project = Get-DefaultProject $RepoRoot", self.text)
        self.assertNotIn('return "$role-$stamp"', self.text)

    def test_project_constant_assigned_before_first_use(self) -> None:
        # Reviewer A r1 finding #2 (initialization-ordering half): PowerShell
        # 5.1 executes top-to-bottom, so $script:Project must be ASSIGNED
        # after Get-DefaultProject is DEFINED and before New-SessionName (its
        # only reader) is ever CALLED. Source-order pin (mirrors
        # test_default_session_name_is_repo_derived's ordering assertions for
        # the sibling $SessionName derivation).
        fn_def = self.text.index("function Get-DefaultProject")
        assign = self.text.index("$script:Project = Get-DefaultProject $RepoRoot")
        reader_def = self.text.index("function New-SessionName")
        reader_call = self.text.index("$name = New-SessionName $role")
        self.assertLess(fn_def, assign,
                        "the constant is assigned before its helper is defined")
        self.assertLess(assign, reader_def,
                        "the constant is assigned after New-SessionName is defined")
        self.assertLess(reader_def, reader_call,
                        "New-SessionName is defined before it is ever called")

    # -- Phase 3: spaces-family hardening + conditional psmux-path quoting ----- #
    def test_psmux_path_quoted_only_when_spaces(self) -> None:
        # a dedicated display helper renders the psmux path COPY-PASTEABLE: a
        # spaces-bearing path via the call operator + quotes (& "..."), the only
        # form that RUNS as-is at a PS prompt (Phase-1-proven); a spaceless path is
        # left BARE so every current spawn/attach golden stays byte-identical.
        self.assertIn("function Format-PsmuxPathDisplay", self.text)
        self.assertIn("if ($psmux -match ' ')", self.text)
        # the quoted form escapes PS double-quoted metacharacters (backtick FIRST,
        # then '$'/'"') so a legal path with '$'/backtick stays literal on paste.
        self.assertIn(
            "$psmux.Replace('`', '``').Replace('$', '`$').Replace('\"', '`\"')",
            self.text)
        self.assertIn("return '& \"' + $escaped + '\"'", self.text)
        # both the spawn display and the printed attach command route THROUGH it
        # (definition + Format-PsmuxSpawn + Open-LocalAttach = >= 3 occurrences),
        # AND the exact LIVE call sites are pinned so a build cannot keep the helper
        # yet bypass it in the real command construction.
        self.assertGreaterEqual(self.text.count("Format-PsmuxPathDisplay"), 3)
        self.assertIn(
            "$psmux = Format-PsmuxPathDisplay $script:PsmuxPath", self.text)
        self.assertIn("$psmuxDisplay = Format-PsmuxPathDisplay $psmux", self.text)
        # and the plain-attach printed command actually CONSUMES $psmuxDisplay (a
        # broken build could compute it yet print raw $psmux). The wt-tab display
        # DELIBERATELY keeps bare $psmux -- it is spaceless-only ($useWtAttach) and
        # a nested wt arg, where the call-operator `& "..."` form would be wrong.
        self.assertIn(
            '$attachCmd = "$psmuxDisplay attach -t $session"', self.text)

    def test_local_attach_spaces_hardened(self) -> None:
        # the SPACELESS wt-tab attach argv is preserved byte-for-byte (today's
        # shape); a SPACES-bearing psmux path is guarded off the wt-nested path and
        # uses the plain-window attach (-FilePath $psmux -- spaces-safe by
        # construction, no nested parser) WITH a printed reason (never a silent
        # broken tab). Phase-1 decision: wt-nested carrying is not assumed across
        # wt versions (spec: never assume wt's nested parser).
        self.assertIn(
            "@('-w', '0', 'new-tab', $psmux, 'attach', '-t', $session)",
            self.text)                                       # spaceless preserved
        self.assertIn(
            "-FilePath $psmux -ArgumentList @('attach', '-t', $session)",
            self.text)                                       # plain fallback argv
        self.assertIn("$hasSpace = ($psmux -match ' ')", self.text)  # spaces guard
        self.assertIn(
            "$useWtAttach = ((Use-WtTab) -and (-not $hasSpace))", self.text)
        self.assertIn("psmux path contains spaces", self.text)      # printed reason
        self.assertIn("plain attach window", self.text)
        # the REAL attach must dispatch on $useWtAttach (NOT bare Use-WtTab), else a
        # spaces path could still be routed through the unsafe wt nested parser
        # while the printed dry-run line looked correct. Both the display-command
        # choice AND the real Start-Process choice gate on $useWtAttach (>= 2).
        self.assertGreaterEqual(self.text.count("if ($useWtAttach) {"), 2)
        # and the real wt attach Start-Process lives under that guard (not the
        # legacy `if (Use-WtTab)` for the attach dispatch).
        wt_start = self.text.index(
            "Start-Process -FilePath 'wt' -ArgumentList @('-w', '0', "
            "'new-tab', $psmux, 'attach', '-t', $session)")
        guard = self.text.rindex("if ($useWtAttach) {", 0, wt_start)
        between = self.text[guard:wt_start]
        self.assertNotIn("if (Use-WtTab)", between,
                         "the real wt attach is not guarded by $useWtAttach")

    # -- launcher-naming commission item 2: downstream items ASSERTED, one ---- #
    # -- test each (the display-name shape change must not leak past what it --
    # -- is scoped to touch: the map key, the psmux -n arg, HARNESS_ROLE, the --
    # -- role-recovery store, and role_mail addressing). ----------------------- #
    def test_downstream_launch_map_keyed_by_role_not_name(self) -> None:
        # comms/.launch-sessions.json stays keyed by ROLE (both Start-Fresh
        # write sites use $map[$role], never the minted $name).
        self.assertEqual(self.text.count("$map[$role] = $entry"), 2,
                         "both Start-Fresh write sites must key the map by role")
        self.assertNotIn("$map[$name]", self.text)

    def test_downstream_psmux_receives_new_session_name(self) -> None:
        # psmux -n gets $name (New-SessionName's return value, now
        # '<project>-<role>-<stamp>') -- the '-n' argv entry is built from $name,
        # not a role-only literal (both Start-Fresh and the vehicle-agnostic
        # argList feed the SAME $plan/$argList into the psmux spawn).
        self.assertIn(
            r"""@('-n', "`"$name`"", "`"$prompt`"")""", self.text)
        self.assertIn("$name = New-SessionName $role", self.text)

    def test_downstream_harness_role_stays_bare_role(self) -> None:
        # HARNESS_ROLE is set from $role (bare), never from $name, on BOTH blob
        # builders (fallback + psmux).
        self.assertEqual(
            self.text.count("`$env:HARNESS_ROLE='$role';"), 2,
            "both Build-LaunchCommand and Build-PsmuxLaunchCommand set "
            "HARNESS_ROLE from the bare $role")
        self.assertNotIn("HARNESS_ROLE='$name'", self.text)

    def test_downstream_comms_roles_dir_untouched_by_launcher(self) -> None:
        # comms/roles/<session_id> is hook-written (session_id -> bare role),
        # never touched by the launcher -- it only mentions the dir in prose to
        # explain who owns it (mirrors test_hooks_own_the_registry_not_the_launcher
        # for the sibling comms/sessions/ claim).
        self.assertIn("comms/roles/", self.text)  # prose mention only
        self.assertNotIn("Join-Path $CommsDir 'roles'", self.text)
        self.assertNotIn('comms/roles/<session_id>.json"', self.text)

    def test_downstream_role_mail_addressing_unmoved(self) -> None:
        # role_mail.py addresses every role by its bare, fixed inbox
        # (comms/<role>/inbox) -- it carries no dependency on the launcher's
        # session-NAME shape (no session_name / .launch-sessions.json
        # reference), so the display-name change cannot move it.
        role_mail_src = (REPO_ROOT / "scripts" / "role_mail.py").read_text(
            encoding="utf-8")
        self.assertIn("comms/<role>/inbox", role_mail_src)
        self.assertNotIn("session_name", role_mail_src)
        self.assertNotIn(".launch-sessions.json", role_mail_src)

    # -- launcher-naming commission item 3: resume compatibility -------------- #
    def test_resume_shape_check_accepts_both_old_and_new_name_shapes(self) -> None:
        # Start-Resume validates the recorded name against the SAME conservative
        # pattern as -SessionName ('^[A-Za-z0-9._-]+$'); both the OLD shape
        # ('<role>-<stamp>') and the NEW shape ('<project>-<role>-<stamp>')
        # match it -- the check does not encode a fixed segment count, so it
        # accepts either. (Behavioral proof: test_dryrun_psmux_resume_hermetic_
        # seeded_map and test_dryrun_nopsmux_resume_byte_equivalent above, both
        # seeded with an OLD-shape recorded name.)
        self.assertRegex("charc-20260101-0000",
                          r"^[A-Za-z0-9._-]+$")   # old shape
        self.assertRegex("proj-charc-20260101-0000",
                          r"^[A-Za-z0-9._-]+$")   # new shape
        self.assertIn("if ($name -notmatch '^[A-Za-z0-9._-]+$')", self.text)

    def test_no_code_parses_a_session_name_back_into_a_role(self) -> None:
        # commission item 3: "find any code that PARSES a name back into a
        # role ... if none exists, say so and quote the grep command and its
        # empty result." Grepped (launcher-naming ledger, re-run at every
        # gate): the launcher itself, scripts/, .claude/hooks/, and
        # comms_ui.py never split a session DISPLAY name to recover a role --
        # comms/roles/<session_id> is keyed by the CLI session_id (a hook-side,
        # launcher-independent concept), never by the display name
        # New-SessionName mints. The REPO-WIDE claim is the grep in the ledger
        # (re-verified at each gate), not this test alone (Reviewer A r1
        # finding #3: a blanket cross-file split/regex guard here would be
        # fragile -- comms_ui.py embeds a large third-party JS blob riddled
        # with unrelated `.split(`, so a naive ban there false-positives).
        # This test pins two NARROWER, SAFE invariants instead:
        # (i) launch_role.ps1's own name-splitting surface is exactly the ONE
        #     '.Split('-')' in Get-DefaultProject's REPO-NAME derivation (a
        #     different string than a minted session name) -- a second
        #     splitting call here would be the launcher itself growing a
        #     parser, caught immediately;
        # (ii) the two hook files (small, no embedded blob, safe to scan
        #      exactly) never reference 'session_name' at all -- the
        #      role-recovery store they own is keyed by session_id only.
        self.assertEqual(self.text.count(".Split('-')"), 1,
                         "an unexpected name-splitting call was introduced")
        self.assertIn("$token = $name.Split('-')[0]", self.text)
        for rel in (".claude/hooks/user_prompt_submit.py",
                    ".claude/hooks/stop.py"):
            hook_src = (REPO_ROOT / rel).read_text(encoding="utf-8")
            self.assertNotIn("session_name", hook_src)

    # -- launcher-naming commission item 4: -PathType Leaf --------------------- #
    def test_bash_cc_preflight_uses_pathtype_leaf(self) -> None:
        self.assertIn("Test-Path -LiteralPath $path -PathType Leaf", self.text)


# --------------------------------------------------------------------------- #
# tier 2 -- golden -DryRun subprocess matrix (skip-guarded per prerequisites)
# --------------------------------------------------------------------------- #
class LaunchRoleDryRunGoldenTest(unittest.TestCase):

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude")
    def test_dryrun_nopsmux_byte_equivalent_to_today(self) -> None:
        # -NoPsmux routes through today's EXACT fallback spawn path. Assert the
        # COMPLETE [launch-role] output line set equals today's lines (rebuilt
        # self-contained from the parsed session name + repo root) PLUS EXACTLY
        # ONE added vehicle/reason line -- so any future extra/rewritten fallback
        # line fails the golden. The rebuilt spawn line includes the blob (bare
        # claude, NOT a call-operator path), so byte-equivalence is enforced.
        r = _run_launcher("-NoPsmux", "-Role", "charc")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = _info_lines(r.stdout)
        name = _session_name(r.stdout, "charc")
        self.assertIsNotNone(name, r.stdout)
        version_line = next(
            (ln for ln in lines if ln.startswith("claude CLI OK: ")), None)
        self.assertIsNotNone(version_line, r.stdout)
        is_wt = any(ln.startswith("  spawn : wt -w 0 new-tab") for ln in lines)
        prompt = ("Read and follow docs/charc-bootstrap.md -- it is your role "
                  "bootstrap. Begin now.")
        args = ('--permission-mode auto --model fable --effort medium -n "' + name +
                '" "' + prompt + '"')
        inner = (_marker_scrub_prefix() + _spawn_env_prefix() + "$env:HARNESS_ROLE='charc'; Set-Location '" + str(REPO_ROOT) +
                 "'; claude " + args)
        expected = [
            _fallback_mode_line(lines),
            version_line,
            "vehicle: fallback (-NoPsmux).",          # the ONE added line
            "DRY RUN -- no windows launched, session map not written.",
            "fresh charc -> session name '" + name + "'",
            "  cmd: claude " + args,
            "  launch: " + inner,
            "  spawn : " + _fallback_spawn_display(inner, is_wt),
            "done.",
        ]
        self.assertEqual(lines, expected)
        self.assertNotIn("& '", inner)  # NOT the psmux call-operator blob

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude")
    def test_dryrun_nopsmux_nowt_byte_equivalent_to_today(self) -> None:
        # -NoWT forces the PLAIN-window fallback arm (its own '-NoWT' mode line +
        # a bare 'powershell -NoExit -EncodedCommand ...' spawn) -- pinned via the
        # complete-output contract so a wt-bearing machine still behaviorally
        # covers the plain arm (Reviewer B r3 coverage pin).
        r = _run_launcher("-NoPsmux", "-NoWT", "-Role", "charc")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = _info_lines(r.stdout)
        name = _session_name(r.stdout, "charc")
        self.assertIsNotNone(name, r.stdout)
        version_line = next(
            (ln for ln in lines if ln.startswith("claude CLI OK: ")), None)
        self.assertIsNotNone(version_line, r.stdout)
        is_wt = any(ln.startswith("  spawn : wt -w 0 new-tab") for ln in lines)
        self.assertFalse(is_wt, "-NoWT must not print a wt-tab spawn")
        prompt = ("Read and follow docs/charc-bootstrap.md -- it is your role "
                  "bootstrap. Begin now.")
        args = ('--permission-mode auto --model fable --effort medium -n "' + name +
                '" "' + prompt + '"')
        inner = (_marker_scrub_prefix() + _spawn_env_prefix() + "$env:HARNESS_ROLE='charc'; Set-Location '" + str(REPO_ROOT) +
                 "'; claude " + args)
        expected = [
            _fallback_mode_line(lines, nowt=True),
            version_line,
            "vehicle: fallback (-NoPsmux).",          # the ONE added line
            "DRY RUN -- no windows launched, session map not written.",
            "fresh charc -> session name '" + name + "'",
            "  cmd: claude " + args,
            "  launch: " + inner,
            "  spawn : " + _fallback_spawn_display(inner, False),
            "done.",
        ]
        self.assertEqual(lines, expected)
        self.assertNotIn("& '", inner)

    def _seed_map(self, session_name: str = "charc-20260101-0000") -> str:
        fd, path = tempfile.mkstemp(suffix=".json", prefix="launchmap-")
        with os.fdopen(fd, "w") as f:
            json.dump({"charc": {"session_name": session_name}}, f)
        return path

    @unittest.skipUnless(_powershell_ok() and _claude_ok() and _psmux_ok(),
                         "needs win32 + powershell + claude + psmux")
    def test_dryrun_local_attach_would_open(self) -> None:
        # a fresh psmux launch into an ISOLATED absent session: the session is
        # JUST CREATED this invocation, so the degraded gate prints "would open" +
        # NAMES the attach command; ONE view (never per-role); opens nothing.
        session = _isolated_session()
        r = _run_launcher("-Role", "charc", "-SessionName", session)
        self.assertEqual(r.returncode, 0, r.stderr)
        # ONE attach VIEW per invocation (never per-role); a spaces-ambient path
        # may add a separate "psmux path contains spaces" reason line, which is a
        # diagnostic, NOT a view -- filter to the actual view line.
        views = [ln for ln in r.stdout.splitlines()
                 if "local attach" in ln and "would open" in ln]
        self.assertEqual(len(views), 1, r.stdout)   # ONE view, never per-role
        self.assertIn("attach -t " + session, views[0])

    @unittest.skipUnless(_powershell_ok() and _claude_ok() and _psmux_ok(),
                         "needs win32 + powershell + claude + psmux")
    def test_dryrun_psmux_resume_hermetic_seeded_map(self) -> None:
        # resume windows into the shared psmux session; the resume NAME comes from
        # a SEEDED temp map via the DryRun-only HARNESS_LAUNCH_MAP override -- never
        # the operator's real map or repo comms state. The seeded name is the OLD
        # shape (no project prefix) -- doubles as commission item 3's "an OLD-
        # shape map entry resumes" test row: resume flows the recorded name
        # through unvalidated-for-shape (only pattern-validated), so it works
        # unchanged for either shape.
        session = _isolated_session()
        mp = self._seed_map("charc-20260101-0000")
        try:
            r = _run_launcher(
                "-Resume", "-Role", "charc", "-SessionName", session,
                env={"HARNESS_LAUNCH_MAP": mp})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('--resume "charc-20260101-0000"', r.stdout)
            spawn = _spawn_line(r.stdout)
            self.assertIsNotNone(spawn, r.stdout)
            psmux = _resolve_psmux()
            self.assertIsNotNone(psmux)
            self.assertTrue(
                spawn.lower().startswith(
                    (_psmux_display(psmux) + " new-session -d -s " + session +
                     " -n charc-20260101-0000 ").lower()),
                spawn)
        finally:
            os.unlink(mp)

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude")
    def test_dryrun_resume_malformed_map_aborts(self) -> None:
        # a recorded session name that violates the conservative pattern must
        # ABORT (nonzero exit, error line, no spawn) -- it would otherwise flow
        # into the printed spawn line AND the real -n/--resume argv. Hermetic via
        # the DryRun-only HARNESS_LAUNCH_MAP override + a seeded temp map.
        fd, mp = tempfile.mkstemp(suffix=".json", prefix="badmap-")
        with os.fdopen(fd, "w") as f:
            json.dump({"charc": {"session_name": "bad; rm -rf"}}, f)
        try:
            r = _run_launcher("-NoPsmux", "-Resume", "-Role", "charc",
                              env={"HARNESS_LAUNCH_MAP": mp})
            self.assertNotEqual(r.returncode, 0, r.stdout)
            self.assertRegex(
                r.stdout + r.stderr,
                r"recorded session name for 'charc' is malformed")
            self.assertNotIn("spawn :", r.stdout)
        finally:
            os.unlink(mp)

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude")
    def test_dryrun_nopsmux_resume_byte_equivalent(self) -> None:
        # the FALLBACK resume path (Start-Resume's separate --resume arg build)
        # stays byte-equivalent to today. Assert the COMPLETE output line set
        # (today's resume lines rebuilt from the SEEDED map name + repo root, incl.
        # the '(--resume opens the picker...)' line) plus EXACTLY ONE added
        # vehicle/reason line; the rebuilt spawn line pins the bare-claude blob.
        # The seeded name is the OLD shape -- commission item 3's second "an
        # OLD-shape map entry resumes" test row (fallback vehicle).
        mp = self._seed_map("charc-20260101-0000")
        try:
            r = _run_launcher(
                "-NoPsmux", "-Resume", "-Role", "charc",
                env={"HARNESS_LAUNCH_MAP": mp})
            self.assertEqual(r.returncode, 0, r.stderr)
            lines = _info_lines(r.stdout)
            version_line = next(
                (ln for ln in lines if ln.startswith("claude CLI OK: ")), None)
            self.assertIsNotNone(version_line, r.stdout)
            is_wt = any(
                ln.startswith("  spawn : wt -w 0 new-tab") for ln in lines)
            name = "charc-20260101-0000"
            prompt = ("Resuming your charc session: re-read your role doc, drain "
                      "your inbox with role_mail, then report current state and "
                      "await the operator.")
            args = ('--permission-mode auto --model fable --effort medium --resume "' +
                    name + '" "' + prompt + '"')
            inner = (_marker_scrub_prefix() + _spawn_env_prefix() + "$env:HARNESS_ROLE='charc'; Set-Location '" +
                     str(REPO_ROOT) + "'; claude " + args)
            expected = [
                _fallback_mode_line(lines),
                version_line,
                "vehicle: fallback (-NoPsmux).",       # the ONE added line
                "DRY RUN -- no windows launched, session map not written.",
                "resume charc -> session name '" + name + "'",
                "  cmd: claude " + args,
                "  launch: " + inner,
                "  spawn : " + _fallback_spawn_display(inner, is_wt),
                "  (--resume opens the picker filtered to this name; select it "
                "to re-enter.)",
                "done.",
            ]
            self.assertEqual(lines, expected)
            self.assertNotIn("& '", inner)
        finally:
            os.unlink(mp)

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude")
    def test_dryrun_nopsmux_resume_new_shape(self) -> None:
        # Reviewer A r2 finding #2: the NEW <project>-<role>-<stamp> shape
        # needs its OWN behavioral resume proof, not just a regex-on-two-
        # literals check (test_resume_shape_check_accepts_both_old_and_new_
        # name_shapes) -- the sibling goldens above/below all seed the OLD
        # shape. Seed a NEW-shape recorded name via the same DryRun-only
        # HARNESS_LAUNCH_MAP override and confirm it resumes: the printed
        # resume line carries the exact seeded name, and the real --resume
        # argv is built from it.
        new_shape_name = _expected_default_project(REPO_ROOT.name) + "-charc-20260101-0000"
        mp = self._seed_map(new_shape_name)
        try:
            r = _run_launcher(
                "-NoPsmux", "-Resume", "-Role", "charc",
                env={"HARNESS_LAUNCH_MAP": mp})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(
                "resume charc -> session name '" + new_shape_name + "'",
                r.stdout)
            self.assertIn('--resume "' + new_shape_name + '"', r.stdout)
        finally:
            os.unlink(mp)

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude")
    def test_dryrun_nopsmux_nowt_resume_byte_equivalent(self) -> None:
        # the -NoWT PLAIN-window arm on the resume path, pinned the same way.
        mp = self._seed_map("charc-20260101-0000")
        try:
            r = _run_launcher(
                "-NoPsmux", "-NoWT", "-Resume", "-Role", "charc",
                env={"HARNESS_LAUNCH_MAP": mp})
            self.assertEqual(r.returncode, 0, r.stderr)
            lines = _info_lines(r.stdout)
            version_line = next(
                (ln for ln in lines if ln.startswith("claude CLI OK: ")), None)
            self.assertIsNotNone(version_line, r.stdout)
            is_wt = any(
                ln.startswith("  spawn : wt -w 0 new-tab") for ln in lines)
            self.assertFalse(is_wt, "-NoWT must not print a wt-tab spawn")
            name = "charc-20260101-0000"
            prompt = ("Resuming your charc session: re-read your role doc, drain "
                      "your inbox with role_mail, then report current state and "
                      "await the operator.")
            args = ('--permission-mode auto --model fable --effort medium --resume "' +
                    name + '" "' + prompt + '"')
            inner = (_marker_scrub_prefix() + _spawn_env_prefix() + "$env:HARNESS_ROLE='charc'; Set-Location '" +
                     str(REPO_ROOT) + "'; claude " + args)
            expected = [
                _fallback_mode_line(lines, nowt=True),
                version_line,
                "vehicle: fallback (-NoPsmux).",       # the ONE added line
                "DRY RUN -- no windows launched, session map not written.",
                "resume charc -> session name '" + name + "'",
                "  cmd: claude " + args,
                "  launch: " + inner,
                "  spawn : " + _fallback_spawn_display(inner, False),
                "  (--resume opens the picker filtered to this name; select it "
                "to re-enter.)",
                "done.",
            ]
            self.assertEqual(lines, expected)
            self.assertNotIn("& '", inner)
        finally:
            os.unlink(mp)

    @unittest.skipUnless(_powershell_ok() and _claude_ok() and _psmux_ok(),
                         "needs win32 + powershell + claude + psmux")
    def test_dryrun_psmux_fresh_isolated_session(self) -> None:
        # fresh psmux launch into an ISOLATED absent session (deterministic: no
        # suffix, no list-windows probe). The spawn line is the new-session shape;
        # the window -n EQUALS the parsed claude session name; the blob call-
        # operator-invokes the resolved claude path.
        session = _isolated_session()
        r = _run_launcher("-Role", "charc", "-SessionName", session)
        self.assertEqual(r.returncode, 0, r.stderr)
        name = _session_name(r.stdout, "charc")
        self.assertIsNotNone(name, r.stdout)
        spawn = _spawn_line(r.stdout)
        self.assertIsNotNone(spawn, r.stdout)
        # the spawn prefix is the RESOLVED psmux path (not bare 'psmux'), matching
        # the real Start-PsmuxWindow -- computed via the launcher-mirroring helper.
        psmux = _resolve_psmux()
        self.assertIsNotNone(psmux)
        # Windows paths are case-insensitive (which() returns PATHEXT-cased .EXE,
        # Get-Command returns on-disk .exe), so compare the prefix case-insensitively.
        self.assertTrue(
            spawn.lower().startswith(
                (_psmux_display(psmux) + " new-session -d -s " + session +
                 " -n " + name +
                 " powershell -NoExit -EncodedCommand ").lower()),
            spawn)
        decoded = _decode_blob(spawn)
        self.assertIsNotNone(decoded, spawn)
        # call operator + resolved claude path (NOT bare claude, NOT a literal)
        self.assertRegex(decoded, r"& '[^']*claude(\.exe)?' --permission-mode")
        self.assertIn("$env:HARNESS_ROLE='charc'; Set-Location '", decoded)
        self.assertIn('-n "' + name + '"', decoded)

    @unittest.skipUnless(_powershell_ok() and _claude_ok() and _psmux_ok(),
                         "needs win32 + powershell + claude + psmux")
    def test_dryrun_psmux_both_creates_then_windows(self) -> None:
        # -Role both into an isolated session: the FIRST role creates the session
        # (new-session), the SECOND windows into it (new-window) -- the in-memory
        # intra-invocation create set on top of read-only has-session. Write-free.
        session = _isolated_session()
        r = _run_launcher("-Role", "both", "-SessionName", session)
        self.assertEqual(r.returncode, 0, r.stderr)
        spawns = _all_spawn_lines(r.stdout)
        self.assertEqual(len(spawns), 2, r.stdout)
        psmux = _resolve_psmux()
        self.assertIsNotNone(psmux)
        # Reviewer B r1 finding B-1: expected against _main_checkout_root(),
        # not REPO_ROOT.name (this worktree's own folder).
        project = _expected_default_project(_main_checkout_root().name)
        self.assertTrue(
            spawns[0].lower().startswith(
                (_psmux_display(psmux) + " new-session -d -s " + session +
                 " -n " + project + "-charc-").lower()),
            spawns[0])
        self.assertTrue(
            spawns[1].lower().startswith(
                (_psmux_display(psmux) + " new-window -t " + session +
                 " -n " + project + "-orchestrator-").lower()),
            spawns[1])

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude (stub supplies psmux)")
    def test_real_psmux_spawn_failure_aborts_nonzero(self) -> None:
        # a REAL (non-DryRun) launch whose stub psmux PASSES preflight
        # (--version + full list-commands) but returns NONZERO from new-session:
        # the launcher must exit NONZERO, NOT print 'done.', and NOT open a local
        # attach view (no misleading resume map, no attach on a failed create).
        # The stub never runs the blob, so nothing real is spawned.
        stub_dir = tempfile.mkdtemp(prefix="psmux-failstub-")
        try:
            with open(os.path.join(stub_dir, "psmux.bat"), "w",
                      newline="\r\n") as f:
                f.write("@echo off\n")
                f.write('if "%~1"=="--version" echo tmux 3.3.6\n')
                f.write('if "%~1"=="list-commands" echo new-session new-window '
                        "attach-session list-windows has-session\n")
                f.write('if "%~1"=="has-session" exit /b 1\n')   # absent
                f.write('if "%~1"=="new-session" exit /b 1\n')   # FAIL create
            session = _isolated_session()
            env = {"PATH": stub_dir + os.pathsep + os.environ.get("PATH", "")}
            r = _run_launcher("-Role", "charc", "-SessionName", session,
                              env=env, dryrun=False)
            self.assertNotEqual(r.returncode, 0, r.stdout)
            self.assertNotIn("done.", r.stdout)
            self.assertNotIn("local attach: opening", r.stdout)
            self.assertNotIn("local attach: would open", r.stdout)
        finally:
            shutil.rmtree(stub_dir, ignore_errors=True)

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude (stub supplies psmux)")
    def test_dryrun_psmux_preflight_miss_falls_back(self) -> None:
        # (B, the CORE hermetic golden; amended ed56074): a STUB psmux placed
        # FIRST on the child PATH whose list-commands OMITS a required command
        # (list-windows) -> the launcher declares psmux unavailable via preflight
        # -> fallback + reason line + byte-equivalent fallback blob. The stub wins
        # resolution because the registry refresh APPENDS (never prepends).
        stub_dir = tempfile.mkdtemp(prefix="psmux-stub-")
        try:
            with open(os.path.join(stub_dir, "psmux.bat"), "w",
                      newline="\r\n") as f:
                f.write("@echo off\n")
                f.write('if "%~1"=="--version" echo tmux 3.3.6\n')
                # advertises new-session/new-window/attach-session, OMITS
                # list-windows -> a preflight miss on list-windows.
                f.write('if "%~1"=="list-commands" '
                        "echo new-session new-window attach-session\n")
            env = {"PATH": stub_dir + os.pathsep + os.environ.get("PATH", "")}
            r = _run_launcher("-Role", "charc", env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertRegex(
                r.stdout,
                r"vehicle: fallback \(psmux preflight miss: list-windows\)")
            spawn = _spawn_line(r.stdout)
            self.assertIsNotNone(spawn, r.stdout)
            decoded = _decode_blob(spawn)
            self.assertIsNotNone(decoded, spawn)
            self.assertNotIn("& '", decoded)  # fallback bare claude
            self.assertIn("; claude --permission-mode", decoded)
        finally:
            shutil.rmtree(stub_dir, ignore_errors=True)

    @unittest.skipUnless(
        _powershell_ok() and _claude_ok() and _psmux_hideable(),
        "psmux is on the registry PATH as a literal segment on this machine; "
        "true absence cannot be simulated hermetically -- covered by the "
        "preflight-miss golden")
    def test_dryrun_psmux_true_absence_both_legs_masked(self) -> None:
        # (A) the ORIGINAL both-legs-masked true-absence golden, retained for
        # HIDEABLE machines: child PATH minus any dir containing psmux.exe, and
        # LOCALAPPDATA -> an empty temp dir (kills the winget glob). Asserts the
        # launcher fell back with a "psmux not resolved" reason.
        claude = shutil.which("claude")
        self.assertIsNotNone(claude)
        claude_dir = os.path.dirname(claude)
        keep = []
        for seg in os.environ.get("PATH", "").split(os.pathsep):
            if not seg:
                continue
            if os.path.exists(os.path.join(seg, "psmux.exe")):
                # critic R7-MAJOR-5: if claude shares that dir, we cannot mask
                if os.path.normcase(seg.rstrip("\\")) == os.path.normcase(
                        claude_dir.rstrip("\\")):
                    self.skipTest("claude+psmux share a dir; cannot hide psmux")
                continue
            keep.append(seg)
        masked = os.pathsep.join(keep)
        # the red must never be a spurious "claude not found"
        if not shutil.which("claude", path=masked):
            self.skipTest("claude not resolvable under the masked PATH")
        empty = tempfile.mkdtemp(prefix="empty-localappdata-")
        try:
            r = _run_launcher(
                "-Role", "charc",
                env={"PATH": masked, "LOCALAPPDATA": empty})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertRegex(r.stdout, r"vehicle: fallback \(psmux not resolved\)")
            spawn = _spawn_line(r.stdout)
            decoded = _decode_blob(spawn)
            self.assertNotIn("& '", decoded)
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    @unittest.skipUnless(_powershell_ok(), "needs win32 + powershell")
    def test_dryrun_sessionname_rejects_illegal(self) -> None:
        # ValidatePattern fires at PARAM BINDING (before preflight), so this
        # needs only powershell. A space is illegal.
        r = _run_launcher("-Role", "charc", "-SessionName", "bad name")
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("spawn :", r.stdout)
        self.assertRegex(
            r.stderr, r"ValidatePattern|does not match|\^\[A-Za-z0-9")

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude")
    def test_bash_cc_preflight_refusal_positive_control(self) -> None:
        # 2026-09-14 remediation (Reviewer A finding #2): drive the fail-loud
        # refusal through a LIVE subprocess -DryRun run, pointed at a
        # guaranteed-nonexistent path via the test/DryRun-only
        # HARNESS_BASH_CC_PATH override -- never the real bash-cc.exe.
        # Invoke-BashCcPreflight runs before any vehicle/spawn planning, so no
        # "vehicle:"/"launch:" line should appear.
        missing = "Z:\\definitely-missing\\bash-cc.exe"
        r = _run_launcher("-Role", "orchestrator",
                           env={"HARNESS_BASH_CC_PATH": missing})
        self.assertEqual(r.returncode, 1, (r.stdout, r.stderr))
        self.assertIn("CLAUDE_CODE_GIT_BASH_PATH target not found: " + missing,
                       r.stdout)
        self.assertNotIn("launch:", r.stdout)
        self.assertNotIn("vehicle:", r.stdout)

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude")
    def test_bash_cc_preflight_directory_fails_pathtype_leaf(self) -> None:
        # launcher-naming commission item 4 -- POSITIVE CONTROL: a DIRECTORY at
        # the checked path (handed in through the DryRun-only
        # HARNESS_BASH_CC_PATH override) must FAIL loudly. Before -PathType
        # Leaf, Test-Path -LiteralPath alone returns $true for a directory, so
        # this is the exact case the fix closes.
        bad_dir = tempfile.mkdtemp(prefix="bash-cc-is-a-dir-")
        try:
            r = _run_launcher("-Role", "orchestrator",
                               env={"HARNESS_BASH_CC_PATH": bad_dir})
            self.assertEqual(r.returncode, 1, (r.stdout, r.stderr))
            self.assertIn(
                "CLAUDE_CODE_GIT_BASH_PATH target not found: " + bad_dir,
                r.stdout)
            self.assertNotIn("launch:", r.stdout)
            self.assertNotIn("vehicle:", r.stdout)
        finally:
            shutil.rmtree(bad_dir, ignore_errors=True)

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude")
    def test_bash_cc_preflight_accepts_a_real_file(self) -> None:
        # launcher-naming commission item 4 -- NEGATIVE CONTROL: a real FILE at
        # the checked path still PASSES -PathType Leaf (the fix narrows the
        # check to reject directories, it must not reject files it used to
        # accept). Preflight succeeds and the run reaches the vehicle/launch
        # lines.
        fd, real_file = tempfile.mkstemp(prefix="bash-cc-is-a-file-")
        os.close(fd)
        try:
            r = _run_launcher("-NoPsmux", "-Role", "charc",
                               env={"HARNESS_BASH_CC_PATH": real_file})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("target not found", r.stdout)
            self.assertIn("vehicle:", r.stdout)
        finally:
            os.unlink(real_file)

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude")
    def test_dryrun_nopsmux_session_name_has_project_role_stamp_shape(self) -> None:
        # Reviewer A r1 finding #1: name minting is VEHICLE-INDEPENDENT
        # (New-SessionName does not consult $script:Vehicle), so this shape
        # assertion should not be gated on psmux -- unlike the psmux-specific
        # 'vehicle: psmux' claim (test_dryrun_session_name_has_project_role_
        # stamp_shape below), this variant runs on any win32+powershell+claude
        # machine via -NoPsmux, independent of psmux availability.
        # Reviewer B r1 finding B-1: <project> derives from the MAIN checkout
        # (not $RepoRoot, which is THIS worktree's own folder when tests run
        # from a linked worktree) -- expected against _main_checkout_root(),
        # not REPO_ROOT.name.
        r = _run_launcher("-NoPsmux", "-Role", "charc")
        self.assertEqual(r.returncode, 0, r.stderr)
        name = _session_name(r.stdout, "charc")
        self.assertIsNotNone(name, r.stdout)
        project = _expected_default_project(_main_checkout_root().name)
        self.assertRegex(
            name, r"^" + re.escape(project) + r"-charc-\d{8}-\d{4}$", name)

    @unittest.skipUnless(_powershell_ok() and _claude_ok() and _psmux_ok(),
                         "needs win32 + powershell + claude + psmux")
    def test_dryrun_session_name_has_project_role_stamp_shape(self) -> None:
        # launcher-naming commission item 1, end-state claim 6: a fresh -DryRun
        # from a role session prints 'vehicle: psmux' and a name in the NEW
        # <project>-<role>-<stamp> shape. Expected against _main_checkout_root()
        # (Reviewer B r1 finding B-1), not REPO_ROOT.name.
        session = _isolated_session()
        r = _run_launcher("-Role", "charc", "-SessionName", session)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"vehicle: psmux")
        name = _session_name(r.stdout, "charc")
        self.assertIsNotNone(name, r.stdout)
        project = _expected_default_project(_main_checkout_root().name)
        self.assertRegex(
            name, r"^" + re.escape(project) + r"-charc-\d{8}-\d{4}$", name)

    @unittest.skipUnless(_powershell_ok() and _claude_ok(),
                         "needs win32 + powershell + claude")
    def test_dryrun_project_token_derives_from_main_checkout_not_worktree(self) -> None:
        # Reviewer B r1 finding B-1 -- POSITIVE CONTROL: run from THIS
        # worktree (.worktrees/launcher-naming, whose own folder leaf is NOT
        # the main checkout's) and show the minted name carries the MAIN
        # checkout's token, computed HERE via _main_checkout_root() (never a
        # literal token in a core file). Before the fix this would have
        # derived from REPO_ROOT.name (this worktree's own leaf) instead.
        main_root = _main_checkout_root()
        expected_project = _expected_default_project(main_root.name)
        r = _run_launcher("-NoPsmux", "-Role", "charc")
        self.assertEqual(r.returncode, 0, r.stderr)
        name = _session_name(r.stdout, "charc")
        self.assertIsNotNone(name, r.stdout)
        self.assertRegex(
            name, r"^" + re.escape(expected_project) + r"-charc-\d{8}-\d{4}$",
            name)
        # negative half: if this worktree's OWN leaf differs from the main
        # checkout's, prove the minted name does NOT carry the worktree's
        # token (the exact regression this fix closes).
        worktree_project = _expected_default_project(REPO_ROOT.name)
        if worktree_project != expected_project:
            self.assertFalse(
                name.startswith(worktree_project + "-charc-"),
                "minted name used the WORKTREE's token, not the main "
                "checkout's: " + name)

    # -- Phase 2: the derived-default RUNTIME behavior + sanitizer edge cases -- #
    @unittest.skipUnless(_powershell_ok() and _claude_ok() and _psmux_ok(),
                         "needs win32 + powershell + claude + psmux")
    def test_dryrun_default_session_name_is_repo_derived(self) -> None:
        # run with NO -SessionName: the default is DERIVED from the repo basename
        # via Get-DefaultSessionName, so the session name printed in the vehicle
        # reason + the local-attach line is the sanitized basename -- NOT the old
        # machine-global 'agents'. Worktree-agnostic: the expected name is the
        # sanitized basename of THIS checkout's root (d3-launcher in the build
        # worktree; the repo's own basename in the merged main tree), computed
        # by the SAME rule.
        expected = _expected_default_session(REPO_ROOT.name)
        self.assertNotEqual(expected, "agents", REPO_ROOT.name)  # a real derive
        r = _run_launcher("-Role", "charc")
        self.assertEqual(r.returncode, 0, r.stderr)
        vehicle = [ln for ln in r.stdout.splitlines() if "vehicle:" in ln]
        self.assertEqual(len(vehicle), 1, r.stdout)
        self.assertIn("shared psmux session '" + expected + "'", vehicle[0])
        # ONE attach VIEW per invocation (never per-role). Filter to the view line
        # (would open / already exists) so an optional spaces-downgrade reason line
        # is not miscounted, and so a live derived-name session (which flips the
        # view to "already exists") does not break the count.
        views = [ln for ln in r.stdout.splitlines()
                 if "local attach" in ln
                 and ("would open" in ln or "already exists" in ln)]
        self.assertEqual(len(views), 1, r.stdout)
        self.assertIn("attach -t " + expected, views[0])
        # and NOT the retired machine-global default
        self.assertNotIn("session 'agents'", r.stdout)
        self.assertNotIn("attach -t agents", r.stdout)

    @unittest.skipUnless(_powershell_ok(), "needs win32 + powershell")
    def test_get_default_session_name_sanitizes(self) -> None:
        # Behavioral witness: EXTRACT the shipped Get-DefaultSessionName function
        # (brace-balanced) from the launcher, dot-source ONLY it, and run it over
        # the edge inputs -- so the required sanitizer behavior (D3-m2 replace,
        # empty->fallback, collapse) is exercised, not merely pinned as literals.
        src = LAUNCHER.read_text(encoding="utf-8")
        body = _extract_ps_function(src, "Get-DefaultSessionName")
        self.assertIsNotNone(body, "Get-DefaultSessionName not found")
        fd, tmp = tempfile.mkstemp(suffix=".ps1", prefix="getdefault-")
        try:
            with os.fdopen(fd, "w", encoding="ascii") as f:
                f.write(body)
            cases = [
                (r"C:\r\sample-app", "sample-app"), # unchanged valid basename
                (r"C:\r\foo bar", "foo-bar"),       # D3-m2: REPLACE (not foobar)
                (r"C:\r\###", "agents"),            # all-invalid -> empty -> fallback
                (r"C:\r\foo--bar", "foo-bar"),      # collapse consecutive '-'
            ]
            script = (". '" + tmp + "'; " + "; ".join(
                "Write-Output (Get-DefaultSessionName '" + inp + "')"
                for inp, _ in cases))
            r = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", script],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            got = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
            self.assertEqual(got, [exp for _, exp in cases], r.stdout)
        finally:
            os.unlink(tmp)

    @unittest.skipUnless(_powershell_ok(), "needs win32 + powershell")
    def test_get_default_project_sanitizes(self) -> None:
        # Reviewer A r1 finding #2 + Reviewer B r1 finding B-3: an independent
        # regression test for Get-DefaultProject's edge rules -- EXTRACT the
        # shipped function (brace-balanced) AND its Resolve-MainCheckoutRoot
        # dependency (B-1: Get-DefaultProject now calls it) and run both over
        # invalid-character runs, repeated hyphens, an all-invalid leaf (the
        # 'agents' fallback), a no-hyphen leaf, leading/trailing hyphens,
        # dots, and non-ASCII, mirroring test_get_default_session_name_sanitizes.
        # None of these fake paths is a real git repo, so
        # Resolve-MainCheckoutRoot's git call fails for every case and falls
        # back to the input path unchanged (B-1's fallback path) -- exactly
        # today's pre-B-1 sanitizer behavior on a synthetic leaf.
        src = LAUNCHER.read_text(encoding="utf-8")
        resolve_body = _extract_ps_function(src, "Resolve-MainCheckoutRoot")
        body = _extract_ps_function(src, "Get-DefaultProject")
        self.assertIsNotNone(resolve_body, "Resolve-MainCheckoutRoot not found")
        self.assertIsNotNone(body, "Get-DefaultProject not found")
        fd, tmp = tempfile.mkstemp(suffix=".ps1", prefix="getdefaultproject-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(resolve_body + "\n" + body)
            cases = [
                (r"C:\r\sample-app", "sample"),      # segment before 1st '-'
                (r"C:\r\plain", "plain"),             # no '-' -> whole name
                (r"C:\r\foo bar", "foo"),             # D3-m2 REPLACE ' '->'-', THEN split
                (r"C:\r\###", "agents"),              # all-invalid -> fallback
                (r"C:\r\foo--bar", "foo"),            # collapse '--'->'-', THEN split
                (r"C:\r\a-b-c", "a"),                 # multi-hyphen -> FIRST segment
                # -- Reviewer B r1 finding B-3: additional edge classes -----
                (r"C:\r\-lead", "lead"),               # leading '-' trimmed first
                (r"C:\r\-lead-foo", "lead"),           # ditto, then split on '-'
                (r"C:\r\trail-", "trail"),              # trailing '-' trimmed first
                (r"C:\r\foo-trail-", "foo"),            # ditto, first segment wins
                (r"C:\r\.foo.bar.", ".foo.bar."),       # dots are LEGAL chars,
                                                         # never sanitized/split away
                ("C:\\r\\caf\u00e9-bar", "caf"),        # mixed non-ASCII: the
                                                         # invalid char becomes '-',
                                                         # collapses, THEN splits
                ("C:\\r\\\u65e5\u672c\u8a9e", "agents"),  # ALL non-ASCII -> one
                                                           # invalid run -> empty -> fallback
                (r"C:\r\---", "agents"),                # only hyphens -> empty -> fallback
            ]
            script = (". '" + tmp + "'; " + "; ".join(
                "Write-Output (Get-DefaultProject '" + inp + "')"
                for inp, _ in cases))
            r = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", script],
                capture_output=True, text=True, timeout=60, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            got = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
            self.assertEqual(got, [exp for _, exp in cases], r.stdout)
        finally:
            os.unlink(tmp)

    @unittest.skipUnless(_powershell_ok(), "needs win32 + powershell")
    def test_get_default_project_resolves_main_checkout_from_any_worktree(self) -> None:
        # Reviewer B r1 finding B-1 -- test row (b): "the main checkout still
        # derives the same token." EXTRACT Resolve-MainCheckoutRoot +
        # Get-DefaultProject and call Get-DefaultProject with TWO different
        # repoRoot inputs -- THIS worktree's own root, and the resolved main
        # checkout root -- both must return the IDENTICAL token, because
        # Resolve-MainCheckoutRoot normalizes either input to the one shared
        # main checkout via `git rev-parse --git-common-dir`.
        main_root = _main_checkout_root()
        src = LAUNCHER.read_text(encoding="utf-8")
        resolve_body = _extract_ps_function(src, "Resolve-MainCheckoutRoot")
        body = _extract_ps_function(src, "Get-DefaultProject")
        self.assertIsNotNone(resolve_body, "Resolve-MainCheckoutRoot not found")
        self.assertIsNotNone(body, "Get-DefaultProject not found")
        fd, tmp = tempfile.mkstemp(suffix=".ps1", prefix="mainroot-")
        try:
            with os.fdopen(fd, "w", encoding="ascii") as f:
                f.write(resolve_body + "\n" + body)
            script = (
                ". '" + tmp + "'; "
                "Write-Output (Get-DefaultProject '" + str(REPO_ROOT) + "'); "
                "Write-Output (Get-DefaultProject '" + str(main_root) + "')")
            r = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", script],
                capture_output=True, text=True, timeout=60,
                cwd=str(REPO_ROOT))
            self.assertEqual(r.returncode, 0, r.stderr)
            got = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
            self.assertEqual(len(got), 2, r.stdout)
            self.assertEqual(got[0], got[1],
                             "worktree-root input and main-checkout-root "
                             "input must derive the SAME <project> token: "
                             + r.stdout)
        finally:
            os.unlink(tmp)

    @unittest.skipUnless(_powershell_ok(), "needs win32 + powershell")
    def test_resolve_main_checkout_root_falls_back_when_git_unavailable_or_fails(self) -> None:
        # Reviewer B r1 finding B-1 -- test row (c): "the git-failure
        # fallback." EXTRACT Resolve-MainCheckoutRoot alone and exercise BOTH
        # documented fallback triggers: (i) git IS on PATH but the CALL FAILS
        # (the input path is not inside any git repo -- non-zero exit); (ii)
        # git is UNAVAILABLE (masked off PATH -- PowerShell's command-not-
        # found is a terminating error regardless of $ErrorActionPreference,
        # caught by the function's try/catch). Both must fall back to the
        # INPUT path unchanged, matching pre-B-1 behavior.
        src = LAUNCHER.read_text(encoding="utf-8")
        body = _extract_ps_function(src, "Resolve-MainCheckoutRoot")
        self.assertIsNotNone(body, "Resolve-MainCheckoutRoot not found")
        fd, tmp = tempfile.mkstemp(suffix=".ps1", prefix="resolvemain-")
        non_repo = tempfile.mkdtemp(prefix="not-a-git-repo-")
        try:
            with os.fdopen(fd, "w", encoding="ascii") as f:
                f.write(body)

            # (i) the call FAILS: non_repo is a real directory but not inside
            # any git repository, so `git -C non_repo rev-parse ...` exits
            # non-zero.
            script1 = (". '" + tmp + "'; Write-Output "
                       "(Resolve-MainCheckoutRoot '" + non_repo + "')")
            r1 = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", script1],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(r1.returncode, 0, r1.stderr)
            got1 = r1.stdout.strip()
            self.assertEqual(
                got1.rstrip("\\").lower(), non_repo.rstrip("\\").lower(),
                r1.stdout)

            # (ii) git is UNAVAILABLE: mask every PATH segment that carries a
            # git executable, keeping everything else (incl. System32, so
            # `powershell` itself still resolves) intact. Self-skip if this
            # machine cannot be hermetically hidden (mirrors the harness's
            # own _psmux_hideable() convention for a hard-to-hide binary).
            segs = os.environ.get("PATH", "").split(os.pathsep)
            keep = [s for s in segs
                    if not os.path.exists(os.path.join(s, "git.exe"))
                    and not os.path.exists(os.path.join(s, "git.cmd"))]
            masked_path = os.pathsep.join(keep)
            if shutil.which("git", path=masked_path):
                self.skipTest(
                    "could not hide git from PATH hermetically on this "
                    "machine")
            if not shutil.which("powershell", path=masked_path):
                self.skipTest(
                    "masking git also hid powershell on this machine")
            child_env = os.environ.copy()
            child_env["PATH"] = masked_path
            script2 = (". '" + tmp + "'; Write-Output "
                       "(Resolve-MainCheckoutRoot '" + str(REPO_ROOT) + "')")
            r2 = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", script2],
                capture_output=True, text=True, timeout=60, env=child_env)
            self.assertEqual(r2.returncode, 0, r2.stderr)
            got2 = r2.stdout.strip()
            self.assertEqual(
                got2.rstrip("\\").lower(), str(REPO_ROOT).rstrip("\\").lower(),
                r2.stdout)
        finally:
            os.unlink(tmp)
            shutil.rmtree(non_repo, ignore_errors=True)

    @unittest.skipUnless(_powershell_ok(), "needs win32 + powershell")
    def test_format_psmux_path_display_escapes(self) -> None:
        # Behavioral witness for the copy-pasteable quoting: EXTRACT the shipped
        # Format-PsmuxPathDisplay, dot-source ONLY it, and run it over paths with a
        # space + PS double-quoted metacharacters ('$', backtick) -- proving the
        # escaping actually round-trips (a spaceless path stays bare; a spaces path
        # is `& "<escaped>"`). Inputs are short so captured PS output is not wrapped.
        src = LAUNCHER.read_text(encoding="utf-8")
        body = _extract_ps_function(src, "Format-PsmuxPathDisplay")
        self.assertIsNotNone(body, "Format-PsmuxPathDisplay not found")
        inputs = [
            r"C:\a\psmux.exe",            # spaceless -> bare
            r"C:\a b\psmux.exe",          # space, no metachar -> & "..."
            r"C:\a $b\psmux.exe",         # space + '$' -> '$' escaped
            "C:\\dir a\\ps`x.exe",       # space + backtick -> backtick doubled
        ]
        fd, tmp = tempfile.mkstemp(suffix=".ps1", prefix="pathdisp-")
        try:
            with os.fdopen(fd, "w", encoding="ascii") as f:
                f.write(body + "\n")
                for inp in inputs:
                    # PS single-quoted literal: '$' and backtick reach the function
                    # verbatim (no interpolation), so we test the function's own
                    # escaping, not the caller's.
                    f.write("Write-Output (Format-PsmuxPathDisplay '" + inp + "')\n")
            r = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", tmp],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            got = [ln for ln in r.stdout.splitlines() if ln.strip()]
            expected = [_psmux_display(inp) for inp in inputs]
            self.assertEqual(got, expected, r.stdout)
            # concrete spot-checks so the intent is unmistakable
            self.assertEqual(got[0], r"C:\a\psmux.exe")           # bare
            self.assertEqual(got[2], '& "C:\\a `$b\\psmux.exe"')  # '$' escaped
        finally:
            os.unlink(tmp)

    # -- Phase 3: the spaces-path golden (temp psmux COPY under a spaces dir) -- #
    @unittest.skipUnless(_powershell_ok() and _claude_ok() and _psmux_ok(),
                         "needs win32 + powershell + claude + psmux")
    def test_dryrun_spaces_psmux_path_quoted(self) -> None:
        # copy the resolved psmux package dir into a SPACES-bearing temp dir,
        # PREPEND it to the child PATH (the launcher's APPEND-not-prepend registry
        # refresh keeps the prepended dir's precedence, so the spaces copy WINS
        # resolution), and run -DryRun. The spawn line renders the spaces psmux
        # path via the call operator (& "..."), and the local-attach line shows the
        # plain-window fallback reason + the quoted plain attach command. The
        # current machine's real psmux path is spaceless, so this is the ONLY
        # golden exercising the spaces branch; the temp tree is cleaned in finally.
        src = _resolve_psmux()
        self.assertIsNotNone(src)
        src_dir = os.path.dirname(src)
        base = tempfile.mkdtemp(prefix="psmux-spaces-")
        spaces_dir = os.path.join(base, "psmux dir")
        try:
            # copy the WHOLE package tree (not just top-level regular files) so a
            # psmux that needs sibling DLLs / subdirs still passes preflight -- a
            # preflight miss here would be unrelated to the quoting under test.
            shutil.copytree(src_dir, spaces_dir)
            # the resolved psmux may be a non-.exe shim; derive the expected copied
            # path from the ORIGINAL resolved basename, not a hardcoded psmux.exe.
            expected = os.path.join(spaces_dir, os.path.basename(src))
            self.assertIn(" ", expected)  # sanity: the copy path has a space
            session = _isolated_session()
            env = {"PATH": spaces_dir + os.pathsep + os.environ.get("PATH", "")}
            r = _run_launcher("-Role", "charc", "-SessionName", session, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            # the spaces copy won resolution (not the spaceless registry psmux)
            self.assertIn("vehicle: psmux", r.stdout, r.stdout)
            spawn = _spawn_line(r.stdout)
            self.assertIsNotNone(spawn, r.stdout)
            # spawn line: the psmux path is QUOTED via the call operator
            self.assertIn(('& "' + expected + '"').lower(), spawn.lower(), spawn)
            # local attach: the quoted plain attach command is ALWAYS rendered for
            # a spaces path (via Format-PsmuxPathDisplay); the downgrade REASON is
            # printed only when wt is available (a spaces path forcing a downgrade
            # OFF the wt-tab path) -- with wt absent the attach is already plain, so
            # gate the reason assertion on wt availability.
            attach = [ln for ln in r.stdout.splitlines() if "local attach" in ln]
            joined = "\n".join(attach)
            self.assertIn(
                ('& "' + expected + '" attach -t ' + session).lower(),
                joined.lower(), joined)
            if _wt_ok():
                self.assertIn("psmux path contains spaces", joined, joined)
                self.assertIn("plain attach window", joined, joined)
        finally:
            shutil.rmtree(base, ignore_errors=True)

    # -- launcher-marker-scrub brief sec 3 test 2: THE POSITIVE CONTROL ------ #
    @unittest.skipUnless(_powershell_ok(), "needs win32 + powershell")
    def test_marker_scrub_positive_control_fallback(self) -> None:
        # From a shell that HAS the ten session markers (+ the global flag)
        # SET, spawn the SHIPPED Build-LaunchCommand's output (argList empty)
        # with the claude invocation swapped for a Get-ChildItem Env:CLAUDE*
        # probe: the ACTUAL environment a Start-Process fallback successor
        # would see, never the blob's string content. Only the global flag
        # (deliberately never removed) and any CLAUDE*-prefixed _SPAWN_ENV
        # entry (deliberately SET, not leaked) may survive -- see
        # _expected_claude_survivors.
        src = LAUNCHER.read_text(encoding="utf-8")
        array_block = _extract_ps_array_block(src, "SessionMarkersToScrub")
        prefix_fn = _extract_ps_function(src, "Get-MarkerScrubPrefix")
        spawn_env_block = _extract_ps_array_block(src, "SpawnEnv")
        spawn_env_fn = _extract_ps_function(src, "Get-SpawnEnvPrefix")
        build_fn = _extract_ps_function(src, "Build-LaunchCommand")
        self.assertIsNotNone(array_block, "SessionMarkersToScrub not found")
        self.assertIsNotNone(prefix_fn, "Get-MarkerScrubPrefix not found")
        self.assertIsNotNone(spawn_env_block, "SpawnEnv not found")
        self.assertIsNotNone(spawn_env_fn, "Get-SpawnEnvPrefix not found")
        self.assertIsNotNone(build_fn, "Build-LaunchCommand not found")
        r = _run_ps_file([
            array_block, prefix_fn, spawn_env_block, spawn_env_fn, build_fn,
            "$RepoRoot = '" + str(REPO_ROOT) + "'",
            "Write-Output (Build-LaunchCommand 'charc' @())",
        ])
        self.assertEqual(r.returncode, 0, r.stderr)
        inner = r.stdout.rstrip("\r\n")
        prefix = _blob_prefix_before_claude(inner)
        survivors = _surviving_claude_env_names(prefix)
        self.assertEqual(survivors, _expected_claude_survivors(), (inner, r.stdout))

    @unittest.skipUnless(_powershell_ok(), "needs win32 + powershell")
    def test_marker_scrub_positive_control_psmux(self) -> None:
        # SAME control against Build-PsmuxLaunchCommand -- defense in depth
        # (brief sec 0: the psmux vehicle is clean by construction -- a psmux
        # window inherits the psmux SERVER's environment, not the launching
        # session's -- but its blob is scrubbed too, and this proves that
        # scrub independently rather than trusting the shared helper alone
        # via only the fallback control above).
        src = LAUNCHER.read_text(encoding="utf-8")
        array_block = _extract_ps_array_block(src, "SessionMarkersToScrub")
        prefix_fn = _extract_ps_function(src, "Get-MarkerScrubPrefix")
        spawn_env_block = _extract_ps_array_block(src, "SpawnEnv")
        spawn_env_fn = _extract_ps_function(src, "Get-SpawnEnvPrefix")
        quote_fn = _extract_ps_function(src, "ConvertTo-PsSingleQuoted")
        build_fn = _extract_ps_function(src, "Build-PsmuxLaunchCommand")
        for fn, name in ((array_block, "SessionMarkersToScrub"),
                         (prefix_fn, "Get-MarkerScrubPrefix"),
                         (spawn_env_block, "SpawnEnv"),
                         (spawn_env_fn, "Get-SpawnEnvPrefix"),
                         (quote_fn, "ConvertTo-PsSingleQuoted"),
                         (build_fn, "Build-PsmuxLaunchCommand")):
            self.assertIsNotNone(fn, name + " not found")
        r = _run_ps_file([
            array_block, prefix_fn, spawn_env_block, spawn_env_fn, quote_fn, build_fn,
            "$RepoRoot = '" + str(REPO_ROOT) + "'",
            "$script:ClaudePath = 'C:\\fake\\claude.exe'",
            "Write-Output (Build-PsmuxLaunchCommand 'charc' @())",
        ])
        self.assertEqual(r.returncode, 0, r.stderr)
        inner = r.stdout.rstrip("\r\n")
        prefix = _blob_prefix_before_claude(inner)
        survivors = _surviving_claude_env_names(prefix)
        self.assertEqual(survivors, _expected_claude_survivors(), (inner, r.stdout))


if __name__ == "__main__":
    unittest.main()
