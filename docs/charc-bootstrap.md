# CHARC Bootstrap -- the literal first-run flow

**Audience:** a fresh CHARC, the FIRST time it is launched in a freshly-cloned
harness. This is CHARC's literal first session. Do this in order, then run the
application-definition interview.

> **The staged guarantee.** CHARC operation (comms + the charter) works on a
> BARE clone -- you can verify comms and reach the interview with no further
> setup. Orchestrator + implementer operation works after **step 5** brings an
> orchestrator up. The interview drives steps 1-3; steps 4-5 are mechanical.

## The first session, in order

### 1. Read the current state, THEN the charter

First read `docs/charc-state.md` -- the single current-state pointer (the
read-me-first state file, overwritten each session). On a BARE clone it is the
shipped placeholder: it tells you there is no prior state and points you onward.
On a live project it tells you the current phase, the live workstreams, and the
pending items -- so you resume an accurate present rather than reconstructing it.

THEN read `docs/charc-charter.md` in full -- your authority, the disciplines, the
tripwire concept, the debt-register posture, the custodian-of-FORM boundary, the
comms routing, and (under section 5) the state-pointer convention itself.

(If you cloned this repo WITH its git history rather than starting fresh per
README instantiate step 1, the `git log` you see is the scaffold's OWN build
history -- the TEMPLATE's, not your project's. Don't mistake those scaffold-build
commits for prior project state; an instantiated project's commit-zero should be
yours. Proceed with the interview.)

### 2. Verify comms (PRE-step-5 -- only what works WITHOUT a live orchestrator)

Run a CHARC-side round-trip on the singular inboxes (no orchestrator is live yet
-- that is step 5):

```
python scripts/role_mail.py post --from operator --to charc --type fyi \
  --subject "bootstrap ping" --body "verifying comms"
python scripts/role_mail.py read --role charc --all
python scripts/role_mail.py post --from charc --to operator --type fyi \
  --subject "bootstrap ack" --body "comms verified"
python scripts/role_mail.py read --role operator --all
```

`charc`, `operator`, and `orchestrator` are ALL single, role-owned
inboxes (the uniform singular-inbox model -- ARC-8 dropped the per-generation
orchestrator registry). Then verify the hook plumbing loads cleanly (the two
hooks -- `user_prompt_submit.py` + `stop.py` -- import + exit 0) and, if you want
the UI, the optional mail UI runs (`python scripts/comms_ui.py`, the `[web]`
extra).

**Post + cue wakes the recipient (2026-09-15, CHARC ruling `657c0506`, superseding "arm the inbox
monitor").** After every `role_mail.py post`, send ONE cross-session `SendMessage` cue to the action
owner -- the rule is verbatim in `docs/orchestrator-context.md`, "Comms routing"; read it there. It
binds every seat, including this bootstrap. The persistent-`Monitor` form survives only as a named
exception, also documented there.

**Bash-launch gauge (2026-09-14, the bash-cc.exe workaround).** At bring-up, time one bash launch --
PowerShell `Measure-Command { & $env:CLAUDE_CODE_GIT_BASH_PATH -c true }` -- record the figure in
`docs/charc-state.md`, and flag anything over 1 s before dispatching anything.

**Do NOT attempt an orchestrator round-trip yet** -- no orchestrator generation
exists until step 5. Posting to `comms/orchestrator/inbox` before a generation
is live would leave the message undrained. The orchestrator round-trip (a live
generation draining the singular `comms/orchestrator/inbox`) is the POST-step-5
verification (below, step 5), consistent with the staged guarantee.

### 3. The application-definition interview (fills seams 1-3)

With the operator, fill the three definition seams:

- **Seam 1 -- the application** -> `APPLICATION.md` (what the project does, its
  domain, success criteria, constraints).
- **Seam 2 -- the domain cells** -> author the domain implementer cells from
  `.claude/agents/implementer-template.md` (one per model/effort tier the
  project needs; fill the `<application>` placeholder + the model/effort
  frontmatter).
- **Seam 3 -- the review/gate mechanism** -> fill the `docs/review-gate-seam.md`
  extension points, or accept its shipped minimal defaults (operable minute one),
  optionally adopting `docs/codex-reviewer.md` as the `REVIEWER` plug-in. The
  CONCRETE seam-3 fill (naming the project's real reviewer/gate) goes in a NEW
  `docs/review-gate-<app>.md` instance doc, NOT in `docs/review-gate-seam.md` --
  the agnostic contract stays pristine; `review-gate-seam.md` keeps the generic
  contract + the replaceable defaults.

### 4. Commission the first arc(s)

With the application defined and the cells authored, commission the first
arc(s): a brief + an inline prompt the operator dispatches to an implementer
cell.

## The 5-step bootstrap checklist (every file CHARC touches)

So the no-engine design carries no hidden coordination debt, here is every file
CHARC touches at bootstrap:

1. `APPLICATION.md` -- define the application domain (seam 1).
2. `.claude/agents/` -- author the domain implementer cells from
   `implementer-template.md` (seam 2).
3. `docs/review-gate-seam.md` -- fill the extension points, or accept the
   shipped defaults, optionally adopting `docs/codex-reviewer.md` (seam 3). The
   concrete fill goes in a new `docs/review-gate-<app>.md` instance doc, leaving
   `review-gate-seam.md` mechanism-agnostic.
4. `scripts/launch_role.ps1` -- (optional) tune the per-role model / effort /
   permission-mode default (seam 4); a tuned starter ships, so this is NOT a
   blocker. When you bring a role up, recommend a COMPLETE per-role config to the
   operator -- model AND effort AND permission-mode, not model alone -- as a
   per-project choice the operator applies (the seam-4 launcher default, or a
   manual launch). **EXCEPTION:** CHARC is fixed at **the top-capability model
   tier current in the harness** (the one non-negotiable role config -- the
   architect/bootstrap role needs top capability regardless of project; the tier
   is an INTENT, never a frozen model string -- amended 2026-08 when a hardcoded
   "opus / max" here outlived the model landscape). Other directors are
   negotiable; orchestrators + implementers are per-project. Model/effort
   rationale + the harness-wide operating economy:
   `docs/model-prompting-standard.md`.
5. **Bring up the orchestrator + the POST-step-5 verification.** Launch an
   orchestrator session via `.\scripts\launch_role.ps1 -Role orchestrator` (it
   sets `HARNESS_ROLE=orchestrator`). THEN do the orchestrator-side comms
   verification step 2 deferred: confirm a director -> orchestrator round-trip
   works via `--to orchestrator` and that the live generation drains the
   singular `comms/orchestrator/inbox`. Confirm this live state before
   commissioning the first arc.

### Resuming a session (the role-on-resume note)

A session's role is set at launch via `HARNESS_ROLE` (the launcher does this).
A RESUMED session started by hand (`claude --resume <id>`) bypasses the launcher,
so `HARNESS_ROLE` is unset. The UserPromptSubmit hook RECOVERS the role from a
session-keyed record (`comms/roles/<session_id>`) it wrote at the original
launch, so the unread notice keeps working on a resume automatically for every
role. To re-set the role EXPLICITLY (the deliberate path -- or if the recovery
record is unavailable), launch the resume with the env var set:

    $env:HARNESS_ROLE='<role>'; claude --resume <id>

(`<role>` is the session's role; `<id>` is the resume target. The automatic
recovery is the safety net for a forgotten/crash resume; this is the simple
deliberate path.)

## The orchestrator bring-up prompt (paste this into the orchestrator session)

Step 5 launches an orchestrator generation; paste THIS block into that session
to bring it online (this is the realized-inbox bring-up -- the orchestrator has
a singular inbox, unlike a send-only model):

```
You are a new orchestrator generation (delivery-manager lane) for this harness's
application. The operator (or CHARC) is bringing you up. Bootstrap yourself, then
STOP and await the operator.

1. Read docs/orchestrator-context.md end-to-end: the role + operating pattern,
   the dispatch model, QA-the-implementer-product, own-the-accept, the comms
   routing.

2. Orient to live state:
       git log --oneline -20
       git status

3. The orchestrator inbox is the SINGULAR comms/orchestrator/inbox (+ read/) --
   the same shape as a director's -- which YOU drain. A director addresses you
   with a plain --to orchestrator (no session_id, no registry). When your
   context fills you roll over: write docs/orchestrator-state.md and announce to
   CHARC, then STOP draining (use peek, not read) so your successor is the sole
   drainer from pickup -- there is always exactly one drainer.

4. Announce online to CHARC, then cue CHARC (post + cue -- docs/orchestrator-context.md,
   "Comms routing": the rule is there):
       python scripts/role_mail.py post --from orchestrator --to charc \
         --type status --subject "New orchestrator generation online" \
         --body "Fresh orchestrator session spun up. Awaiting operator. HEAD: <sha>."
       python scripts/role_mail.py read --role orchestrator --all

Then report to the operator the live state + the next action you believe is
queued, and AWAIT the operator. Honor the binding conventions (conventional
commits, no co-author footer, no verification-skipping).
```

*(By default this bring-up block lives HERE, in this bootstrap doc's step-5
section -- no separate file. CHARC MAY instead split it into a standalone
`scripts/orchestrator_bootstrap.md` at execute-time, an explicit choice that
adds one file beyond the shipped manifest.)*
