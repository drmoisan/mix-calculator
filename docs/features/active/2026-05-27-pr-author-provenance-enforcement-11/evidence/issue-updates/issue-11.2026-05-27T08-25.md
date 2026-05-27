# Issue Update Mirror — Issue #11

Timestamp: 2026-05-27T08-25

PostedAs: unknown

Note: This is a local mirror of the issue/AC status update produced during
minor-audit remediation. The orchestrator owns the GitHub PR and issue-comment
handoff; this executor does not post to GitHub. When the orchestrator posts, it
should record the GitHub URL and `IssueUpdatedAt` here or in a follow-up mirror.

## Update text

pr-author provenance enforcement (issue #11) — minor-audit remediation complete.

All eight acceptance criteria in `issue.md` are now checked off and backed by
verified evidence:

1. Repro now blocked with `PR_BODY_PATH_NONCANONICAL` — committed hook Case D
   (`.claude/hooks/enforce-pr-author-skill.ps1`); fail-before exception dossier at
   `evidence/regression-testing/fail-before-exception.2026-05-27T08-25.md`.
2. Regression tests added and passing — 52 tests in
   `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1`; final-QC test artifact
   `evidence/qa-gates/2026-05-27T08-25/test.md`.
3. Edge cases / invalid inputs handled — per-branch and malformed/empty input
   scenarios in the test suite.
4. No unintended behavior changes outside scope — PoshQC analyze 0 findings, 0
   regression (`evidence/qa-gates/2026-05-27T08-25/analyze.md`).
5. Logs/telemetry: output contract unchanged — committed hook diff.
6. Performance: one small-file hash per PR command — committed hook diff.
7. Full toolchain pass (format -> analyze -> test; type-check N/A) and changed-file
   line coverage >= 85% — format/analyze/test all `ok`; changed-file line coverage
   91.59% command / 92.05% JaCoCo LINE; coverage comparison at
   `evidence/qa-gates/2026-05-27T08-25/coverage-comparison.md`.
8. Docs updated — `.claude/skills/orchestrate/SKILL.md` documents the pr-author
   handoff, receipt schema, and PR Creation Gate condition 5.

Coverage artifact: `artifacts/pester/powershell-coverage.xml` was regenerated and
now contains `enforce-pr-author-skill.ps1` (98/107 commands covered = 91.59%;
JaCoCo LINE 81/88 = 92.05%), replacing stale content that omitted the changed hook.

Branch: `fix/pr-author-provenance-enforcement-11`. Fix and tests committed in
`e79c183`.

## Local issue.md mirror

The same AC check-offs were applied to the `## Acceptance Criteria` section of
`docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/issue.md`
(all 8 items now `[x]`).
