"""The genericity guard -- the no-app-contamination build gate (spec section 8).

A grep-based test with three explicit lists (tests/genericity_lists.py):
  (a) forbidden vocabulary -> appears NOWHERE in the tracked tree;
  (b) forbidden finance tickers -> the closed swing-residue set;
  (c) allowed substrate vocabulary -> permitted ONLY in two named files; the
      mechanism-agnostic seam doc carries NO substrate token at all.

The scan target is the TRACKED tree (git ls-files) MINUS the named exclude set
(the denylist-as-data file + the planted-term fixtures). Matching is
word-boundary (\bterm\b) so an unrelated word containing a forbidden substring
does not false-fail; tickers are matched case-sensitive uppercase.

F.1 ships the guard + the three lists + the four distinguishing self-tests (over
a planted fixture tree). F.2 runs it over the REAL tracked tree (the binding
build gate).
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

import genericity_lists as gl

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# The guard scans EVERY tracked file that decodes as UTF-8 text -- it does NOT
# allowlist suffixes (an allowlist is a hole: a future tracked .sh/.rst/.lock
# UTF-8 file could carry forbidden vocab and slip through). Only files that fail
# to decode as text (binary blobs) are skipped, on the read.


def _tracked_files(root: Path) -> list[str]:
    """Repo-relative paths of all git-tracked files under root."""
    out = subprocess.run(
        ["git", "ls-files"], cwd=str(root), capture_output=True, text=True,
        check=True).stdout
    return [line for line in out.splitlines() if line]


def _compile_word(term: str) -> re.Pattern:
    # Word-boundary, case-insensitive. For multi-word phrases, collapse internal
    # whitespace to \s+ so "course of action" matches across newlines/spaces.
    escaped = re.escape(term)
    escaped = re.sub(r"\\\s+|\s+", r"\\s+", escaped)
    return re.compile(r"\b" + escaped + r"\b", re.IGNORECASE)


_FORBIDDEN_PATTERNS = [
    (term, _compile_word(term))
    for term in (gl.FORBIDDEN_TERMS + gl.FORBIDDEN_ROLE_TERMS)
]
# Tickers: case-SENSITIVE uppercase whole-word (so lowercase English is safe).
_TICKER_PATTERNS = [
    (t, re.compile(r"\b" + re.escape(t) + r"\b"))
    for t in gl.FORBIDDEN_TICKERS
]
# Substrate words: case-insensitive word-boundary; longest-first so "Claude
# Code" is reported as the phrase, not bare "Claude".
_SUBSTRATE_PATTERNS = [
    (term, _compile_word(term))
    for term in sorted(gl.ALLOWED_SUBSTRATE, key=len, reverse=True)
]


def scan_tree(root: Path, relpaths: list[str],
              exclude: tuple[str, ...] = gl.SELF_EXCLUDE_RELPATHS) -> list[str]:
    """Return a list of human-readable violation strings (empty == clean).

    Checks each tracked text file (minus the exclude set) for:
      - any forbidden term / role term (in CORE files -- app/domain contamination
        is forbidden across the reusable CORE; B-9);
      - any forbidden ticker (in CORE files);
      - a substrate term (word OR substrate-named path) in the mechanism-agnostic
        seam doc (docs/review-gate-seam.md) ONLY -- the one denied scope.

    B-9 scoping: the vocabulary + ticker bans apply to the reusable CORE only.
    The germination INSTANCE surface (gl.is_instance_surface -- APPLICATION.md,
    the domain implementer cells, the briefs, the seam-3 fill, a peer director's
    state/context docs) is application content BY DESIGN and is EXEMPT from the
    vocabulary + ticker bans (skipped before those loops). The CORE keeps the
    FULL ban; an app term OR finance/extraction residue in a CORE file still
    FAILS (see test_vocab_bans_are_core_only + test_over_broad_exemption_guard).

    Substrate vocabulary is PERMITTED everywhere else (spec section 8(b): the
    scaffold is substrate-coupled, so substrate terms "do NOT fail the build").
    The single substrate denial is the seam doc, which must stay mechanism-
    agnostic (spec section 8(c)); it is a CORE file, never instance surface.
    """
    exclude_set = set(exclude)
    violations: list[str] = []
    for rel in relpaths:
        if rel in exclude_set:
            continue
        path = root / rel
        # Scan EVERY tracked file that decodes as UTF-8 text (no suffix
        # allowlist); skip only undecodable/binary files (the strict decode
        # raises UnicodeDecodeError on a binary blob, which is the only skip).
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        norm = rel.replace("\\", "/")

        # Instance surface = application content; exempt from the vocabulary +
        # ticker bans entirely (those protect the reusable CORE). The CORE below
        # still carries the FULL ban; the substrate-seam check targets review-
        # gate-seam.md (core), never an instance-surface file.
        if gl.is_instance_surface(norm):
            continue

        for term, pat in _FORBIDDEN_PATTERNS:
            if pat.search(text):
                violations.append(f"{norm}: forbidden term {term!r}")
        for term, pat in _TICKER_PATTERNS:
            if pat.search(text):
                violations.append(f"{norm}: forbidden ticker {term!r}")

        if norm in gl.SUBSTRATE_FORBIDDEN_RELPATHS:
            # The mechanism-agnostic seam doc: NO substrate term (word) AND NO
            # substrate-named path token. This is the binding substrate scoping.
            for term, pat in _SUBSTRATE_PATTERNS:
                if pat.search(text):
                    violations.append(
                        f"{norm}: substrate term {term!r} in the mechanism-"
                        "agnostic seam doc (must stay substrate-free)")
            for tok in gl.SUBSTRATE_PATH_TOKENS:
                if tok in text:
                    violations.append(
                        f"{norm}: substrate-named path token {tok!r} in the "
                        "mechanism-agnostic seam doc")
    return violations


# --- the four distinguishing self-tests (over a planted fixture tree) -------

class GuardSelfTest(unittest.TestCase):
    """Prove the guard DISTINGUISHES -- it catches a plant and clears clean."""

    def _scan_fixture(self, files: dict[str, str]) -> list[str]:
        # Build a throwaway tree and scan exactly its relpaths (no git needed --
        # scan_tree takes the relpath list directly).
        import tempfile
        tmp = Path(tempfile.mkdtemp())
        for rel, content in files.items():
            p = tmp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        return scan_tree(tmp, list(files.keys()))

    def test_plants_a_forbidden_term_then_clears(self) -> None:
        # 1: a forbidden term in a normal file FAILS; removing it passes.
        dirty = self._scan_fixture({"docs/x.md": "this mentions swing trading"})
        self.assertTrue(
            any("swing" in v for v in dirty),
            "guard must catch a planted forbidden term")
        clean = self._scan_fixture({"docs/x.md": "this mentions the harness"})
        self.assertEqual(clean, [], "clean text must pass")

    def test_substrate_file_scoping(self) -> None:
        # 2: a substrate term in the seam doc FAILS (the one denied scope); the
        #    SAME term in codex-reviewer.md PASSES (substrate is allowed
        #    everywhere except the seam doc).
        out_of_scope = self._scan_fixture(
            {"docs/review-gate-seam.md": "the reviewer runs under Codex"})
        self.assertTrue(
            any("review-gate-seam.md" in v and "Codex" in v
                for v in out_of_scope),
            "a substrate term in the seam doc must fail")
        in_scope = self._scan_fixture(
            {"docs/codex-reviewer.md": "the reviewer runs under Codex on WSL"})
        self.assertEqual(
            in_scope, [],
            "substrate terms in codex-reviewer.md must pass")

    def test_allowed_substrate_term_in_normal_file_does_not_fail(self) -> None:
        # 3: an allowed substrate term (WSL/git) in a normally-substrate-OK file
        #    (any file other than the seam doc) passes -- the scaffold is
        #    substrate-coupled, so substrate vocabulary does not blanket-fail.
        clean = self._scan_fixture(
            {"docs/dispatch-recipe.md": "the substrate default uses a git "
             "worktree for isolation on WSL",
             "docs/orchestrator-context.md": "coordinate the Claude Code cells"})
        self.assertEqual(
            clean, [],
            "substrate terms in non-seam files must pass (substrate-coupled)")

    def test_forbidden_term_in_non_whitelisted_extension_fails(self) -> None:
        # The guard scans by text-decodability, NOT a suffix allowlist: a
        # forbidden term in a .sh / .rst / .lock file must still FAIL (the R1
        # suffix-skip hole). Distinguishing: a suffix-allowlist guard would PASS
        # these (the bug); the decode-based guard catches them.
        for rel in ("scripts/x.sh", "docs/x.rst", "deps.lock"):
            dirty = self._scan_fixture({rel: "this mentions swing"})
            self.assertTrue(
                any("swing" in v for v in dirty),
                f"a forbidden term in {rel} must fail (no suffix allowlist)")

    def test_seam_doc_rejects_substrate_named_path(self) -> None:
        # 2b: the seam doc must carry no substrate-named PATH token either.
        out = self._scan_fixture(
            {"docs/review-gate-seam.md": "see docs/codex-reviewer.md for the "
             "reviewer"})
        self.assertTrue(
            any("codex-reviewer" in v for v in out),
            "a substrate-named path in the seam doc must fail")

    def test_vocab_bans_are_core_only(self) -> None:
        # B-9 points 1+2+3: the vocabulary + ticker bans protect the reusable
        # CORE; the instance surface is application content and is EXEMPT.
        # Distinguishing:
        #   - an app term OR residue term in a CORE file FAILS (full teeth);
        #   - the SAME terms on the instance surface PASS (app content by design).
        core_app = self._scan_fixture(
            {"scripts/role_mail.py": "# a comment about chess strategy"})
        self.assertTrue(any("chess" in v for v in core_app),
                        "an app term leaking into a core file must STILL fail")
        core_residue = self._scan_fixture(
            {".claude/hooks/user_prompt_submit.py": "# mentions swing trading"})
        self.assertTrue(any("swing" in v for v in core_residue),
                        "a residue term leaking into a core file must STILL fail")
        core_ticker = self._scan_fixture(
            {"docs/charc-charter.md": "the SPY benchmark"})
        self.assertTrue(any("SPY" in v for v in core_ticker),
                        "a residue ticker in a core file must STILL fail")
        surface = self._scan_fixture(
            {"APPLICATION.md": "this is about chess and even mentions swing and SPY"})
        self.assertEqual(
            surface, [],
            "the instance surface is exempt from the vocabulary+ticker bans")

    def test_over_broad_exemption_guard(self) -> None:
        # The registered CORE docs are NOT exempted even though some match an
        # instance suffix pattern: an app term in the mechanism-agnostic seam
        # contract, the generic orchestrator kernel, OR any other CORE_DOC_RELPATHS
        # member still FAILS (the future-safe registry gate, not a 2-item denylist).
        for core_doc in ("docs/review-gate-seam.md", "docs/orchestrator-context.md"):
            out = self._scan_fixture({core_doc: "about chess"})
            self.assertTrue(any("chess" in v for v in out),
                            f"{core_doc} is core (registered), not instance surface")
        # Every registered core doc stays core-scanned (the two sets are disjoint,
        # so no exception needed -- charc-state.md is an instance stub, not core).
        for core_doc in gl.CORE_DOC_RELPATHS:
            self.assertFalse(gl.is_instance_surface(core_doc),
                             f"{core_doc} is registered core, must stay scanned")
        # An UNregistered docs/ doc matching a suffix pattern IS instance surface
        # (the designed exempt-until-registered boundary):
        self.assertTrue(gl.is_instance_surface("docs/comms-context.md"),
                        "an unregistered docs/*-context.md is instance surface")


class WholeTreeGuardTest(unittest.TestCase):
    """F.2 -- the guard, run over the ACTUAL tracked tree, MUST be green.

    This is the binding no-application-contamination build gate. It fails the
    build if any tracked file carries a forbidden term / ticker, or a substrate
    term leaks into the mechanism-agnostic seam doc. Re-gated in J.2.
    """

    def test_whole_tracked_tree_is_clean(self) -> None:
        violations = scan_tree(REPO_ROOT, _tracked_files(REPO_ROOT))
        self.assertEqual(
            violations, [],
            "the genericity guard must be green over the whole tracked tree; "
            "found:\n  " + "\n  ".join(violations))


class GuardSelfExclusionTest(unittest.TestCase):
    """The guard, over the REAL tree, must NOT trip on its own list file."""

    def test_list_file_is_excluded_from_the_scan(self) -> None:
        # tests/genericity_lists.py CONTAINS every forbidden term as data, and
        # tests/test_genericity_guard.py plants forbidden terms in its self-test
        # fixtures. A guard with no self-exclusion would fail on both. Assert the
        # scan EXCLUDES them (and that the exclude set names them).
        self.assertIn(
            "tests/harness/genericity_lists.py", gl.SELF_EXCLUDE_RELPATHS,
            "the denylist-as-data file must be in the self-exclude set")
        self.assertIn(
            "tests/harness/test_genericity_guard.py", gl.SELF_EXCLUDE_RELPATHS,
            "the guard test (which plants forbidden terms) must be excluded")
        tracked = _tracked_files(REPO_ROOT)
        violations = scan_tree(REPO_ROOT, tracked)
        # If either guard-machinery file were scanned, these would appear.
        leaked = [v for v in violations
                  if "genericity_lists.py" in v
                  or "test_genericity_guard.py" in v]
        self.assertEqual(
            leaked, [],
            "the guard must not trip on its own machinery files")

    def test_guard_without_exclusion_would_have_tripped(self) -> None:
        # Distinguishing: scanning the list file WITHOUT excluding it DOES trip,
        # proving the exclusion is load-bearing (not a no-op).
        unguarded = scan_tree(REPO_ROOT, ["tests/harness/genericity_lists.py"],
                              exclude=())
        self.assertTrue(
            unguarded,
            "scanning the denylist-as-data file with NO exclusion must trip -- "
            "this proves the self-exclusion is doing real work")


class GuardRunsInDefaultInvocationTest(unittest.TestCase):
    """F.3 -- the guard runs in the default test invocation (not skip-marked)."""

    def test_guard_test_is_discoverable_and_not_skipped(self) -> None:
        # The guard test module matches the default discover pattern test_*.py
        # under tests/, so `python -m unittest discover -s tests` runs it. Assert
        # the whole-tree gate exists + is not decorated skip (a guard that is
        # skip-marked is a silent hole).
        import inspect
        src = inspect.getsource(WholeTreeGuardTest)
        self.assertNotIn("@unittest.skip", src,
                         "the whole-tree guard gate must not be skip-marked")
        # And the README documents the validation command that runs it.
        readme_rel = next(
            (rel for rel in ("docs/harness-readme.md", "README.md") if (REPO_ROOT / rel).exists()),
            "README.md",
        )
        readme = (REPO_ROOT / readme_rel).read_text(encoding="utf-8")
        self.assertIn("python -m unittest discover", readme)


if __name__ == "__main__":
    unittest.main()
