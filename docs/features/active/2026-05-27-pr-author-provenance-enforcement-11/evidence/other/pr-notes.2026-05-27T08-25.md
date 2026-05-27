# PR Notes (prepared content for pr-author handoff) — Issue #11

Timestamp: 2026-05-27T08-25

Note: This is prepared PR-body content only. This executor does NOT create or
edit the GitHub PR. The orchestrator routes this through the pr-author handoff per
`.claude/skills/orchestrate/SKILL.md` PR Creation Gate condition 5 (canonical
`artifacts/pr_body_<N>.md` + matching `artifacts/pr_body_<N>.receipt.json`).

## Title

fix(hooks): enforce pr-author provenance on gh pr create/edit (#11)

## Summary

Harden `.claude/hooks/enforce-pr-author-skill.ps1` so `gh pr create` / `gh pr edit`
are allowed only when the PR body was produced by the pr-author handoff. The hook
previously allowed any `--body-file` command while `artifacts/pr_context.summary.txt`
existed, so a self-authored body at an ad-hoc path (e.g. `/tmp/pr_body_9.md`) passed
without pr-author running. The hook now requires a canonical body path
`artifacts/pr_body_<N>.md` with a sibling receipt `artifacts/pr_body_<N>.receipt.json`
whose `number` matches, whose `sha256` matches the body, and whose `created_at` is
strictly newer than the PR-context summary write time.

## In-scope files

- Production (modified): `.claude/hooks/enforce-pr-author-skill.ps1`
- Test (new): `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1`
- Docs (modified): `.claude/skills/orchestrate/SKILL.md`

In-scope language: PowerShell only. No Python, TypeScript, or C# changed.

## New reason codes

`PR_BODY_PATH_NONCANONICAL`, `PR_AUTHOR_RECEIPT_MISSING`,
`PR_AUTHOR_RECEIPT_NUMBER_MISMATCH`, `PR_AUTHOR_RECEIPT_HASH_MISMATCH`,
`PR_AUTHOR_RECEIPT_STALE`. Existing shape-only cases A/B/C and the metadata-only
`gh pr edit` allow path are preserved; the hook output contract is unchanged.

## Fail-before rationale

The fix and its test suite were committed together (`e79c183`), so a fresh
fail-before run is not reproducible on the branch head. The fail-before requirement
is satisfied by a schema-valid exception dossier
(`evidence/regression-testing/fail-before-exception.2026-05-27T08-25.md`) citing the
documented pre-fix behavior `gh pr create ... --body-file /tmp/pr_body_9.md` ->
`{"decision":"allow"}` recorded in `issue.md`.

## Toolchain and coverage

- PoshQC format: `ok` (no file changes).
- PoshQC analyze: `ok` (0 findings, 0 regression vs baseline).
- Pester test: 52 passed, 0 failed, 0 skipped.
- Type-check: N/A for PowerShell.
- Changed-file coverage: 91.59% command (98/107); JaCoCo LINE 92.05% (81/88).
  Gate >= 85% line: PASS. Branch obligation met via explicit per-branch scenarios.
- Machine-readable coverage artifact `artifacts/pester/powershell-coverage.xml`
  regenerated to include `enforce-pr-author-skill.ps1`.

## Evidence links

- `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/qa-gates/2026-05-27T08-25/format.md`
- `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/qa-gates/2026-05-27T08-25/analyze.md`
- `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/qa-gates/2026-05-27T08-25/test.md`
- `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/qa-gates/2026-05-27T08-25/coverage-comparison.md`
- `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/regression-testing/fail-before-exception.2026-05-27T08-25.md`
- `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/issue-updates/issue-11.2026-05-27T08-25.md`
- Acceptance criteria: `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/issue.md` `## Acceptance Criteria` (all 8 checked).
- Coverage artifact: `artifacts/pester/powershell-coverage.xml`.
