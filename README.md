# Clearwater, the application

Clearwater corrects colour cast, contrast loss and haze in underwater photos and
video. Version 1.1.0 ships as a Windows one-folder download (a zip, unsigned, not an
installer) on the GitHub release page, and installs from this repository with uv on any
platform. The macOS code paths are in 1.1.0 but not yet validated on a Mac; there is no
macOS download. Start with the [installation and user guide](docs/user-guide.md).
See [third-party notices](THIRD_PARTY_NOTICES.md) and [LICENSE](LICENSE) for the
GPL-2.0-or-later licence and component terms.

# CHARC Harness

A germinable multi-agent development scaffold: one standing director (CHARC),
rotating orchestrator generations, and ephemeral implementer cells, coordinated
through durable file-based comms and a small set of bootstrap seams. Clone the
repo, `launch charc`, and follow its bootstrap to fill the seams in for your own
project.

> The application this instantiation runs is defined in `APPLICATION.md`.

## Germinate a new project

1. Clone this repo (a bare clone is enough -- see "The staged guarantee" below).
2. Launch CHARC: `.\scripts\launch_role.ps1 -Role charc` (sets
   `HARNESS_ROLE=charc` and points the fresh session at its bootstrap doc).
3. CHARC reads `docs/charc-state.md` then `docs/charc-charter.md`, verifies
   comms, and runs the application-definition interview with the operator --
   see `docs/charc-bootstrap.md` for the literal first-run flow.

## The staged guarantee

CHARC operation -- comms plus the charter -- works on a **bare clone** with no
further setup: you can verify a role's inbox round-trip and reach the
application-definition interview immediately. Orchestrator and implementer
operation come online once the bootstrap's step 5 brings an orchestrator
generation up. `docs/charc-bootstrap.md` documents exactly which steps require
that live generation and which do not.

## The four bootstrap seams

The interview + the bootstrap checklist fill four seams, each a named artifact:

1. **Seam 1 -- the application.** `APPLICATION.md` (repo root): what the
   project does, its domain, success criteria, constraints. This is the ONE
   file that carries instance/domain vocabulary by design; everything else in
   this list stays application-agnostic.
2. **Seam 2 -- the domain implementer cells.** `.claude/agents/`, authored from
   `.claude/agents/implementer-template.md` -- one cell per model/effort tier
   the project needs, filling the `<application>` placeholder and the
   model/effort frontmatter.
3. **Seam 3 -- the review/gate mechanism.** `docs/review-gate-seam.md`: the
   mechanism-agnostic review-to-convergence + gate contract, with named
   extension points and a minimal generic default that is operable from
   minute one. A project's concrete fill (naming its real reviewer/gate) lives
   in its own `docs/review-gate-<app>.md` instance doc, so this contract stays
   pristine. `docs/codex-reviewer.md` is an optional, replaceable `REVIEWER`
   plug-in reference for one substrate; it is not the reviewer, and a
   non-software project ignores it and plugs its own.
4. **Seam 4 -- per-role model/effort/permission-mode defaults.** Tuned inside
   `scripts/launch_role.ps1` -- tunable starters, not canonical values (one
   fixed exception: the director role stays at the harness's top-capability
   tier regardless of project). Optional; a working starter ships.

## Repository layout

- `APPLICATION.md` -- the seam-1 application definition (instance content).
- `docs/` -- the project record: the kernel docs below, the review/gate seam,
  design specs and plans, per-arc dispatch briefs, proofs.
- `docs/charc-bootstrap.md` -- the literal first-run flow + the 5-step
  bootstrap checklist.
- `docs/charc-charter.md` -- CHARC's standing authority, disciplines, and
  comms routing (the director kernel).
- `docs/orchestrator-context.md` -- the generic orchestrator operating model
  (dispatch briefs, QA-the-implementer-product, own-the-accept).
- `docs/dispatch-recipe.md` -- the generic implementer protocol every
  dispatched cell reads first (isolated workspace, produce -> validate ->
  converge, the review-to-convergence loop, the acceptance-transfer return
  report).
- `.claude/agents/` -- the shipped generic cell template plus the project's
  own domain implementer cells authored from it.
- `scripts/` -- the file-comms CLI (`role_mail.py`), the role launcher
  (`launch_role.ps1`), and an optional mail UI (`comms_ui.py`).
- `tests/` -- the harness / infrastructure test suite (this is what the
  validation command below runs); a project's own application suite, if any,
  lives under its own directory and is documented in `APPLICATION.md`.

## Validating the harness

The harness / infrastructure suite runs under the stdlib `unittest` module:

```
python -m unittest discover -s tests
```

This is the review/gate seam's build gate: the doc-acceptance checks above, the
genericity guard (no application vocabulary leaking into the reusable core),
and the rest of the harness machinery tests. A project's own application suite
(if it ships one) is documented separately in `APPLICATION.md`.

## Comms and roles

Roles (CHARC, an orchestrator generation, a peer director, the operator)
coordinate through durable, file-based, per-role inboxes under `comms/` via
`scripts/role_mail.py` -- never in-process message passing, so state survives a
context reset. `docs/orchestrator-context.md` and `docs/charc-charter.md`
document the routing; an implementer cell's return report goes to whoever
dispatched it, never to a role mailbox.

## Review, gate, and acceptance

Every product (code, a plan, a doc) passes through the review-to-convergence
loop defined by `docs/review-gate-seam.md` before a superior accepts it: an
adversarial `REVIEWER` produces severity-classified findings, each is
adjudicated (never blind-fixed), and the loop iterates to its
`CONVERGENCE_CRITERION`. Review is a filter, never the gate -- the accepting
superior verifies the claimed behavior against reality before merging.
`docs/codex-reviewer.md` documents one optional, substrate-coupled `REVIEWER`
plug-in; the seam itself names no concrete mechanism.
