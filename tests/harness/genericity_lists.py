"""The genericity guard's three explicit lists (denylist-as-data).

This file CONTAINS every forbidden term BY DESIGN (it is the guard's data), so
the guard MUST exclude this file from its scan -- see SELF_EXCLUDE_RELPATHS and
the self-exclusion test. Do not "fix" a guard failure by editing the words here
out; they are the contract.

The guard realizes the spec's three lists (design spec section 8):

  (a) FORBIDDEN_TERMS    -- swing-isms + app/domain example terms; appear NOWHERE
                            in the reusable CORE (matched as case-insensitive
                            word-boundary tokens).
  (b) FORBIDDEN_TICKERS  -- the CLOSED realization of the spec's "finance
                            tickers" class: the named swing benchmark/universe
                            tickers (matched case-SENSITIVE uppercase whole-words
                            so they do not trip on lowercase English).
  (c) ALLOWED_SUBSTRATE  -- substrate vocabulary permitted because the scaffold
                            is substrate-coupled; permitted everywhere EXCEPT the
                            mechanism-agnostic seam doc (SUBSTRATE_FORBIDDEN_RELPATHS).
                            There is no exception-allowlist -- substrate is not
                            forbidden by default.

B-9 scoping: the (a) vocabulary + (b) ticker bans are scoped to the reusable CORE
-- they protect the clean-room extraction belt + keep the upstreamable kernel
application-agnostic. The germination INSTANCE surface (section (d) below,
is_instance_surface) is application content by design and is EXEMPT from (a)+(b).
This is "run once at authoring, or CORE-only -- not a permanent tree-wide gate":
the bans stay as a cheap CORE hygiene belt (a residue copy-paste into role_mail.py
or a generic contract doc still FAILS) without snagging the application content the
seams exist to carry. The (c) substrate scoping is unchanged (the seam doc is CORE).

WHY the ticker class is CLOSED and not a universal uppercase matcher: the
scaffold is authored clean-room (design spec section 2 -- zero swing residue,
zero swing git history), so the ONLY vector for a finance ticker to leak in is a
swing-residue copy-paste, which is finite + enumerable (the named swing
tickers). A universal uppercase-symbol detector is REJECTED: the set of all
tickers is unbounded (every 1-5-letter uppercase token), producing unbounded
false positives (README, HTTP, JSON, CHARC itself) -> a non-deterministic,
cry-wolf guard that gets disabled, defeating the section-8 intent. The closed
list IS the complete, deterministic matcher for the clean-room contamination
surface. A future amendment routes through the harness's architecture owner like
any tracked-denylist change; the SHIPPED list is fixed + closed.
"""

from __future__ import annotations

# --- (a) forbidden vocabulary ----------------------------------------------
# The design-spec section-8 literal forbidden set (verbatim) PLUS the concrete
# finance vocabulary that realizes the "finance tickers" class. Matched
# case-INSENSITIVE as word-boundary tokens (\bterm\b). htmx/fastapi/jinja2/
# uvicorn are deliberately NOT here (the spec ships an htmx UI in the [web]
# extra -- forbidding htmx would contradict the spec).
FORBIDDEN_TERMS: tuple[str, ...] = (
    # --- design-spec section-8 literal set ---
    "swing",
    "trading",
    "trade",
    "trades",
    "finviz",
    "schwab",
    "sqlite",
    "pytest",
    "ruff",
    "chess",
    "coa",
    "course-of-action",
    "course of action",
    # --- the finance vocabulary realizing the "finance tickers" class ---
    "finance",
    "ticker",
    "yfinance",
)

# --- (b) the CLOSED finance-ticker denylist --------------------------------
# Matched case-SENSITIVE as uppercase whole-words (so the verb "spy" / the noun
# "spx" in lowercase English never trip). These are the named swing
# benchmark/universe tickers the clean-room extraction could carry.
FORBIDDEN_TICKERS: tuple[str, ...] = (
    "SPY",
    "QQQ",
    "NDX",
    "SPX",
    "RUT",
)

# --- the removed swing role (one director ships; no rd analog) --------------
# `rd` (swing's research-director) has no scaffold analog (design spec section
# 9). Matched as a case-insensitive word-boundary token. Kept separate from
# FORBIDDEN_TERMS only for clarity in the role-removal assertion.
FORBIDDEN_ROLE_TERMS: tuple[str, ...] = (
    "rd",
)

# --- (c) allowed substrate vocabulary --------------------------------------
# Permitted because the scaffold is substrate-coupled (design spec section 8(b):
# these terms "do NOT fail the build -- they are the same-substrate
# constraint"). They appear legitimately across the tree -- in the operating
# docs (the dispatch-recipe names a git worktree as the substrate default), in
# config (.gitignore), and in the test machinery (which shells out to git and
# names the Claude Code substrate). The ONE place a substrate term is FORBIDDEN
# is the mechanism-agnostic seam doc (below). Matched case-insensitive as
# word-boundary tokens; multi-word entries (e.g. "Claude Code") match as a
# phrase.
ALLOWED_SUBSTRATE: tuple[str, ...] = (
    "Claude Code",
    "Claude",
    "WSL",
    "Windows",
    "PowerShell",
    "Codex",
    "git",
)

# The mechanism-agnostic seam doc -- the ONE file the guard requires to carry
# ZERO substrate token (word OR substrate-named path). This is the binding,
# distinguishing substrate check: spec section 8(c) "FORBIDDEN in
# review-gate-seam.md's protocol section." Everywhere else substrate vocabulary
# is permitted (8(b)); HERE it is a build failure, keeping the review/gate
# contract mechanism-agnostic (it defers to seam 3 + the optional reviewer
# reference, named in the dispatch-recipe + bootstrap, never in the seam doc).
# Substrate vocabulary is permitted EVERYWHERE except here; there is no
# exception-allowlist because substrate is not forbidden by default (the
# scaffold is substrate-coupled -- spec section 8(b)).
SUBSTRATE_FORBIDDEN_RELPATHS: tuple[str, ...] = (
    "docs/review-gate-seam.md",
)

# A substrate-named PATH token that must not appear in the seam doc (it names
# the abstract REVIEWER slot generically and never points at the codex file).
SUBSTRATE_PATH_TOKENS: tuple[str, ...] = (
    "codex-reviewer.md",
    "codex-reviewer",
)

# --- the test-infrastructure scan-EXCLUDE set ------------------------------
# NOT a content allowance -- the unavoidable "a grep test cannot scan the file
# that holds its own grep patterns" exclusion. This file (the denylist-as-data)
# and the planted-term fixtures the distinguishing self-tests create are
# excluded from the scan. Named here so the exclude set is auditable and cannot
# silently grow. (Per-test fixture temp dirs are excluded structurally -- the
# scan only walks tracked files; see the guard's scan-target.)
SELF_EXCLUDE_RELPATHS: tuple[str, ...] = (
    "tests/harness/genericity_lists.py",
    # The guard test itself plants forbidden terms inline (the distinguishing
    # self-tests build fixtures containing "swing", a substrate term in the
    # seam doc, etc.) and discusses the finance-ticker class in its docstrings --
    # so it carries forbidden vocabulary BY DESIGN, exactly like the list file.
    # Excluding it is the same "a grep test cannot scan the file that holds its
    # own grep patterns / planted terms" necessity, not a content allowance.
    "tests/harness/test_genericity_guard.py",
    # The instance-surface predicate tests (B-9) discuss the ticker ban in their
    # docstrings and use a peer-director example role (`rd`) in fixtures like
    # docs/rd-state.md / docs/rd-context.md -- so the file carries forbidden
    # vocabulary BY DESIGN, the same "a grep test cannot scan its own planted
    # terms" necessity as the guard test above. Not a content allowance.
    "tests/harness/test_instance_surface.py",
)

# --- (d) INSTANCE customization: the instance surface (vocab bans are CORE-only) -
# The template's vocabulary + ticker bans keep the reusable CORE application-
# agnostic and free of extraction residue, so they are scoped to the CORE. The
# instance SURFACE -- the files that ARE the germinated application (APPLICATION.md,
# the domain implementer cells, the briefs, the seam-3 fill, a peer director's
# state / context docs) -- is application content BY DESIGN and is EXEMPT from the
# vocabulary + ticker bans entirely (see scan_tree). The CORE keeps FULL teeth: an
# app term OR finance/extraction residue in role_mail.py, the hooks, or the generic
# contract docs still FAILS (distinguishing test test_vocab_bans_are_core_only).
# These are PATTERNS (the template ships no concrete app/role name): <app> and
# <role> are filled at germination.
#
# FUTURE-SAFE SCOPING: the instance PATTERNS below (docs/<role>-state.md /
# docs/<role>-context.md / docs/review-gate-<app>.md) are gated by the EXPLICIT
# CORE-doc registry CORE_DOC_RELPATHS. A docs/*.md file is instance surface ONLY
# when it matches an instance pattern AND is NOT a shipped CORE doc. So adding a
# NEW core doc named, e.g., docs/comms-context.md does NOT silently stop being
# scanned -- a new core doc MUST be added to CORE_DOC_RELPATHS (a deliberate,
# reviewed act the manifest gate ALSO forces), and being registered keeps it
# CORE-scanned. The pattern matcher never exempts a registered core doc.
# Two DISJOINT sets, never blurred:
#   CORE_DOC_RELPATHS      = the reusable-kernel docs/ files (NEVER instance surface).
#   INSTANCE_STUB_RELPATHS = docs/ files that ship as a template stub but ARE
#                            instance surface (filled/overwritten at germination).
# charc-state.md is an INSTANCE STUB, NOT core -- it lives in INSTANCE_STUB_RELPATHS
# only. The manifest cross-check (test_manifest_accounting) accounts for BOTH sets
# against the manifest's docs/*.md, so neither blurs the other.
CORE_DOC_RELPATHS: frozenset[str] = frozenset({
    "docs/charc-charter.md",
    "docs/charc-bootstrap.md",
    "docs/model-prompting-standard.md",
    "docs/orchestrator-context.md",
    "docs/dispatch-recipe.md",
    "docs/review-gate-seam.md",
    "docs/codex-reviewer.md",
    # ARC-8 retired docs/comms-orchestrator-registry.md (the per-generation
    # registry it documented was deleted); the uniform singular-inbox model is
    # documented in orchestrator-context.md + charc-bootstrap.md.
})

# docs/ files shipped as a template stub but that ARE instance surface once filled.
INSTANCE_STUB_RELPATHS: tuple[str, ...] = (
    "docs/charc-state.md",  # the section-5.1 state pointer (overwritten with state)
)

# INSTANCE FILL (Clearwater): the explicit instance relpaths beyond APPLICATION.md.
# Clearwater is a Python application (src/ layout, a uv-managed project file,
# a tools/ folder, project tests under tests/) living in the same tree as the
# harness core. Everything the APPLICATION owns is instance surface: it carries
# domain vocabulary and an application-chosen toolchain by design. The reusable
# harness core (scripts/, .claude/hooks, the kernel docs, tests/harness/) stays
# application-agnostic + stdlib-only.
INSTANCE_SURFACE_RELPATHS: tuple[str, ...] = (
    "APPLICATION.md",
    # the project's agent-facing entry doc (names the application toolchain).
    "CLAUDE.md",
    # the concrete seam-3 fill (also matches the review-gate-<app> pattern).
    "docs/review-gate-clearwater.md",
    # the project's technical-debt register (charter section 4: the concrete
    # register lives in the project's own docs, CHARC-maintained).
    "docs/debt-register.md",
    # the orchestrator generation's read-me-first state pointer (also matches the
    # <role>-state pattern). Overwritten each generation (charter 5.1 convention).
    "docs/orchestrator-state.md",
    # the application's planning record (the implementation plan, the spec and
    # the research notes the owner supplied; the architecture document, decision
    # log and gate report the plan says live in docs/).
    "docs/clearwater-implementation-plan.md",
    "docs/underwater-correction-spec.md",
    "docs/underwater-imagery-correction-research.md",
    "docs/architecture.md",
    "docs/decisions.md",
    "docs/gate-report.md",
    # the application's project file + toolchain pins: the root pyproject is the
    # APPLICATION's (uv-managed; it also carries the optional mail-UI extra), so
    # it names the application test runner / linter by design. Still listed in
    # the manifest gate's support set; exempt from the vocabulary scan only.
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    "LICENSE",
    # the local-configuration template (footage + working folder paths).
    "clearwater.local.example.toml",
) + INSTANCE_STUB_RELPATHS
INSTANCE_SURFACE_PREFIXES: tuple[str, ...] = (
    "docs/briefs/",
    # superpowers process artifacts (brainstorming specs + implementation plans).
    "docs/superpowers/",
    # per-arc proofs, accept records, round ledgers, completion reports.
    "docs/proofs/",
    "docs/reports/",
    # The application SOURCE surface: the package, its tools and its tests.
    # tests/harness/ is the HARNESS suite and stays core-scanned (see
    # is_instance_surface, which carves it out of the tests/ prefix).
    "src/",
    "tools/",
    "tests/",
)
# The harness suite's own directory: NEVER instance surface even though it sits
# under the instance tests/ prefix (carved out in is_instance_surface).
HARNESS_TESTS_PREFIX = "tests/harness/"

# Shipped CORE .claude/agents/*.md cells (NEVER instance surface) -- the exact
# parallel of CORE_DOC_RELPATHS for the agents namespace. The implementer-*.md
# namespace is shared between the shipped generic cell and the germinated domain
# cells, so a CORE agent file is instance surface ONLY when NOT registered here
# (the same exempt-until-registered gate as the docs registry). Today the one
# shipped core cell is implementer-template.md; a future core agent .md must be
# added here (a deliberate, reviewed act) to stay CORE-scanned.
CORE_AGENT_RELPATHS: frozenset[str] = frozenset({
    ".claude/agents/implementer-template.md",
})


def is_instance_surface(relpath: str) -> bool:
    """True iff relpath is germination instantiation surface (not harness core).

    Exempt from the vocabulary + ticker bans + counted as instance surface in the
    manifest. The explicit RELPATHS/PREFIXES are unconditional; the docs/ suffix
    PATTERNS are gated by CORE_DOC_RELPATHS so a registered core doc is NEVER
    exempted (future-safe -- a new core doc is added to CORE_DOC_RELPATHS, a
    deliberate reviewed act). PATTERNS cover instance files that do not exist on a
    bare clone:
      - docs/review-gate-<app>.md  (the seam-3 concrete fill; NOT review-gate-seam.md)
      - docs/<role>-state.md       (a peer director's state pointer; parallel of charc-state.md)
      - docs/<role>-context.md     (a peer director's instance-authority doc; NOT orchestrator-context.md)
      - .claude/agents/implementer-*.md  (domain cells; NOT a CORE_AGENT_RELPATHS
        member, e.g. the shipped implementer-template.md)
    """
    rel = relpath.replace("\\", "/")
    # REGISTERED CORE ALWAYS WINS: a registered CORE doc OR core agent cell is
    # NEVER instance surface, checked FIRST -- before ANY instance rule (the
    # explicit relpaths/prefixes AND the patterns). So a future core file added to
    # CORE_DOC_RELPATHS / CORE_AGENT_RELPATHS can never be exempted even if it also
    # happens to match an unconditional instance relpath/prefix (auto-review MINOR:
    # the registry-wins invariant, not weakened by check ordering).
    if rel in CORE_DOC_RELPATHS or rel in CORE_AGENT_RELPATHS:
        return False
    # Explicit instance relpaths (incl. the shipped charc-state.md stub) + prefixes.
    if rel in INSTANCE_SURFACE_RELPATHS:
        return True
    if rel.startswith(HARNESS_TESTS_PREFIX):
        return False  # the harness suite is core, carved out of the tests/ prefix
    if any(rel.startswith(p) for p in INSTANCE_SURFACE_PREFIXES):
        return True
    # docs/ suffix patterns (review-gate-<app> / <role>-state / <role>-context),
    # reached ONLY for a docs/ file that is NOT a registered core doc. The match
    # is restricted to a SINGLE path segment directly under docs/ (no further
    # slash, no `.`/`..`) so a NESTED path (docs/core/foo-context.md) is NOT
    # exempted -- a future nested core doc must stay CORE-scanned (Codex R1 M1).
    if _matches_docs_instance_pattern(rel):
        return True
    # Domain implementer cells (seam-2 fills): a single-segment .md cell directly
    # under .claude/agents/ that is NOT a registered CORE agent (CORE_AGENT_RELPATHS,
    # checked above). Markdown-only + single-segment so a non-md sibling or a nested
    # path is NOT a cell (R1 M1).
    if _matches_implementer_cell(rel):
        return True
    return False


def _single_segment_under(rel: str, prefix: str) -> str | None:
    """The single path SEGMENT name if `rel` is exactly `<prefix><name>` with no
    further slash and no `.`/`..` traversal; else None. The future-safe matcher
    for the docs/ + agents/ instance patterns (rejects nested paths)."""
    if not rel.startswith(prefix):
        return None
    name = rel[len(prefix):]
    if not name or "/" in name or name in (".", ".."):
        return None
    return name


def _matches_docs_instance_pattern(rel: str) -> bool:
    name = _single_segment_under(rel, "docs/")
    if name is None or not name.endswith(".md"):
        return False
    return (name.startswith("review-gate-")
            or name.endswith("-state.md")
            or name.endswith("-context.md"))


def _matches_implementer_cell(rel: str) -> bool:
    name = _single_segment_under(rel, ".claude/agents/")
    if name is None or not name.endswith(".md"):
        return False
    # A registered CORE agent cell is never an instance cell (the same exempt-
    # until-registered gate as the docs registry; belt for a direct call).
    if rel in CORE_AGENT_RELPATHS:
        return False
    return name.startswith("implementer-")
