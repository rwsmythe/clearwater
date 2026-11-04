# Clearwater 1.0.0 release checklist

The orchestrator executes this checklist at acceptance. WP5.5's implementer does
not merge, tag, push or write the final release record. No installer, PyPI release,
signing or packaged executable is part of this release.

1. Confirm Reviewer A converged and Reviewer B is clean or its permitted bounded
   remediation is dispositioned under [the review/gate fill](review-gate-clearwater.md).
   Check the final candidate's version, notices, guide walkthrough, ownership and
   root-only lockfile diff. DR-119 (a)-(b) are paid down by this package;
   CHARC closes those parts at accept. DR-119 (c)-(d) remain Phase 6.
2. Check disk space in Git Bash before the release gate. At least **25 GB free**
   on C: is required; STOP below that floor. Do not prune without an explicit
   owner grant.

   ```bash
   df -h /c
   ```

3. Run the release gate on the final candidate, using the current commands and
   collection rules in [the gate fill](review-gate-clearwater.md). The order is
   **static checks, collection identity, parallel, serial, fullclip, harness**.
   Run one leg at a time with the stall watch; nothing else heavy runs beside
   serial or fullclip. Keep stdout/stderr logs, exit codes and JUnit files.
   Collection must prove disjoint parallel/serial/fullclip sets whose union is
   all tests, with removed IDs explained. Check selected counts against outcomes
   and account for new/moved skips. The harness runs separately under unittest.
   These fresh release-gate figures supersede earlier package-gate figures for
   the 1.0.0 release record. A failed gate is a STOP for acceptance.
4. Archive those logs, collection lists, JUnits and the run conditions to
   **<evidence-folder>\release-1.0.0\**. This is the harness's review-evidence
   folder outside the repository. Record their hashes and candidate commit.
   Preserve the package review evidence under the separate wp5.5 evidence folder.
5. Merge the accepted candidate to main at the orchestrator's seat. Record the
   base, candidate and merge commit; prove patch identity over any rebase and
   run the integration verification required by the gate fill. A changed final
   candidate needs the applicable checks again before tagging.
6. Obtain the owner's explicit **"tag 1.0.0"** through CHARC. WP5.5 acceptance
   may precede that instruction; do not infer tag permission from acceptance.
   The owner has deferred DR-117, so no halo-fix package precedes this tag.
7. On that word, create the annotated tag on the actual merge commit, replacing
   the placeholder below. The tag message is exactly **Clearwater 1.0.0**.

   ```bash
   git tag -a v1.0.0 <merge-commit> -m "Clearwater 1.0.0"
   ```

   Do not push. Any remote action needs the owner's separate word.
8. CHARC writes **docs/proofs/release-1.0.0.md** with the tag/merge commit, owner's
   instruction, archived release-gate locations/hashes and figures of record,
   both review verdicts, and open debt carried into v1 with the owner's
   acknowledgement. CHARC records **N13 SATISFIED** citing
   [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md), closes DR-119 (a)-(b), adds
   the plan's Phase 5 CLOSED pointer and updates CLAUDE.md's current state.

Evidence is a local archive, not a publication. Keep original footage read-only
and out of every release artifact. The source remains GPL-2.0-or-later; the
notices and user guide ship with the repository.
