# Fail-Before Exception Dossier — enforce-pr-author-skill provenance enforcement

Timestamp: 2026-05-27T08-25

Issue: #11
Branch: fix/pr-author-provenance-enforcement-11
In-scope production file: `.claude/hooks/enforce-pr-author-skill.ps1`
Regression test (new on this branch): `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1`

## WhyFailingRunImpossible

The provenance-enforcement fix and its Pester suite are already implemented and
committed on the branch head (commit `e79c183 fix(hooks): enforce pr-author
provenance on gh pr create/edit (#11)`). A fresh fail-before run cannot be
reproduced because there is no point on the branch head where the new tests
exist but the fix does not: the test file is new on this branch and was
introduced together with the hardened hook. Reverting the hook to reproduce the
pre-fix `allow` decision would require deleting committed production code on the
branch head, which is outside the scope of this minor-audit remediation and is
prohibited by the no-replanning constraint. Per
`.claude/skills/evidence-and-timestamp-conventions/SKILL.md`, a schema-valid
fail-before exception dossier satisfies the fail-before requirement in this case.

## Alternative Proof (documented pre-fix behavior)

The defect and its pre-fix behavior are documented in
`docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/issue.md`:

- Summary (issue.md lines 13-17): the hook allowed any command carrying a
  `--body-file` while `artifacts/pr_context.summary.txt` existed, so a
  self-authored body at an ad-hoc path passed without the pr-author skill
  running. PR #10 was created this way.
- Logs / Screenshots (issue.md lines 46-49):
  - Pre-fix: `gh pr create ... --body-file /tmp/pr_body_9.md` -> `{"decision":"allow"}`
- Actual Behavior (issue.md lines 41-44): the hook checked command shape only
  (inline `--body`, no body, or `--body-file` with the context file present).
  With `--body-file` and an existing context file it returned `allow`,
  regardless of whether pr-author produced the body or what path was used.

This documents the exact failing condition the fix addresses: a non-canonical
`--body-file` path (`/tmp/pr_body_9.md`) that previously returned
`{"decision":"allow"}`.

## Pass-After Evidence (post-fix behavior)

The committed hook now returns the block reason `PR_BODY_PATH_NONCANONICAL` for a
non-canonical `--body-file` path (Case D in
`Get-PrAuthorProvenanceReason`/`Get-PrAuthorBypassReason`). The behavior change
is exercised by the Pester suite in
`tests/claude/hooks/enforce-pr-author-skill.Tests.ps1`, including dedicated
scenarios for each reason code (D `PR_BODY_PATH_NONCANONICAL`, E
`PR_AUTHOR_RECEIPT_MISSING`, G `PR_AUTHOR_RECEIPT_NUMBER_MISMATCH`, F
`PR_AUTHOR_RECEIPT_HASH_MISMATCH`, H `PR_AUTHOR_RECEIPT_STALE`) and the preserved
shape-only cases A/B/C plus the metadata-only `gh pr edit` allow path. The
Phase 4 final-QC test artifact records the passing run with coverage.

## Schema Fields

- Timestamp: 2026-05-27T08-25
- Command: N/A (no failing-run command is reproducible on branch head; see WhyFailingRunImpossible)
- EXIT_CODE: N/A (fail-before run not reproducible; documented pre-fix behavior cited as alternative proof)
- Output Summary: Pre-fix behavior `gh pr create ... --body-file /tmp/pr_body_9.md` -> `{"decision":"allow"}` is documented in issue.md (Summary, Logs/Screenshots, Actual Behavior). The committed fix now blocks that command with `PR_BODY_PATH_NONCANONICAL`. Fail-before requirement satisfied via this exception dossier per evidence-and-timestamp-conventions.

## SearchScope / SearchPatterns / SearchResult (failing-run search)

- SearchScope: `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/regression-testing/`
- SearchPatterns: failing-run artifacts (`*.md`) recording a pre-fix failing Pester run
- SearchResult: none (no failing-run artifact exists; this exception dossier is the fail-before evidence)
