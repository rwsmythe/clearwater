# Bootstrap dry-run walkthrough (Task J.3) + final acceptance

A fresh-clone walkthrough confirming CHARC can verify comms and reach the
application-definition interview with NO further setup (the staged guarantee's
CHARC-operation half), plus the step-5 orchestrator bring-up that brings the
registry to a live state. The bootstrap is a human/agent procedure; the
executable evidence is the automated suite (cited below).

## CHARC operation works on a bare clone (steps 1-4)

1. **Read the charter** -- `docs/charc-charter.md` exists and is generic.
2. **Verify comms (PRE-step-5)** -- the CHARC-side round-trip works on a bare
   clone:
   ```
   python scripts/role_mail.py post --from operator --to charc --type fyi \
     --subject "ping" --body "x"
   python scripts/role_mail.py read --role charc --all
   python scripts/role_mail.py post --from charc --to operator --type fyi \
     --subject "ack" --body "x"
   python scripts/role_mail.py read --role operator --all
   ```
   Automated evidence: `tests/test_comms_roundtrip.py` (the three-role
   round-trip) + `tests/test_role_mail.py`.
3. **The application-definition interview** -- the seam files exist + are
   fillable: `APPLICATION.md` (seam 1 stub), `.claude/agents/implementer-template.md`
   (seam 2), `docs/review-gate-seam.md` (seam 3, with the shipped defaults
   operable minute one -- `tests/test_seam3_defaults.py`).
4. **Commission the first arc** -- the dispatch protocol exists
   (`docs/dispatch-recipe.md`) + the orchestrator operating model
   (`docs/orchestrator-context.md`).

## Orchestrator + implementer operation works after step 5 (EXECUTABLE)

Step 5 is executable as written, not just prose:

- **(a) The launch command is dry-run-verifiable.** Run:
  ```
  powershell -NoProfile -File scripts/launch_role.ps1 -Role orchestrator -DryRun
  ```
  It prints the exact `claude` command with `$env:HARNESS_ROLE='orchestrator'`
  set in the inner command + the EncodedCommand spawn, and exits WITHOUT
  launching. (The preflight runs first and throws if a used flag is absent.)
- **(b) The register path is proven.** After a real launch, the orchestrator's
  first prompt fires the `UserPromptSubmit` hook, which registers the generation
  + creates its per-generation inbox. Proven by the registry suite
  (`tests/test_registry_suite.py`, `tests/test_registry_selfheal.py`,
  `tests/test_user_prompt_submit_hook.py`).
- **(c) The bring-up block is a concrete paste.** The literal copy-paste block
  the operator pastes into the orchestrator session lives in
  `docs/charc-bootstrap.md` step 5.

So step 5 is executable end-to-end: a dry-run-verified launch command + a
register path proven by the registry suite + a concrete paste block. The
fully-live launch is the operator's bootstrap-witness gate.

## Final acceptance (the section-1 success criterion)

- After cloning + launching CHARC: comms works (the round-trip suite is green);
  the role-protocol + dispatch + review/gate docs are present + runnable (the
  seam defaults are operable -- the seam-3 test); the bootstrap reaches the
  interview with no further setup.
- Step 5 is executable as written (the dry-run command + the proven register
  path + the paste block).
- The three definition seams (1-3) are marked + fillable; seam 4 ships a tuned
  default.
- The whole-tree genericity guard is green (`tests/test_registry_suite.py`'s
  re-gate + `tests/test_genericity_guard.py`).
- Zero hard runtime deps in the core (`tests/test_dependency_posture.py`); the
  UI is `[web]`-gated + import-isolated.
- Manifest accounting is exact (`tests/test_manifest_accounting.py`): every
  tracked file is either a section-4 shipped-manifest file OR a repository-
  support appendix file (tests + config) -- one accounting model, no dual count.

Run the full automated evidence:

```
python -m unittest discover -s tests
```
