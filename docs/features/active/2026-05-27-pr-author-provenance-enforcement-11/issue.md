# pr-author-provenance-enforcement (Issue #11)

- Date captured: 2026-05-27
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/pr-author-provenance-enforcement/ (Issue #11)

> Automation note: Keep the section headings below unchanged; the promotion tooling maps each of them into the GitHub bug issue template.

- Issue: #11
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/11
- Last Updated: 2026-05-27
- Work Mode: full-bug

## Summary

The `enforce-pr-author-skill.ps1` PreToolUse hook fails to block `gh pr create` /
`gh pr edit` commands that bypass the pr-author skill. It allows any command that
merely carries a `--body-file` while `artifacts/pr_context.summary.txt` exists, so
a self-authored body at an ad-hoc path (e.g. `/tmp/pr_body_9.md`) passes without
the pr-author skill ever running. PR #10 was created this way.

## Environment

- OS/version: Windows, PowerShell 7+
- Python version: n/a (PowerShell hook + Markdown skill)
- Command/flags used: `gh pr create --base main --title ... --body-file /tmp/pr_body_9.md`
- Data source or fixture: n/a

## Steps to Reproduce

1. Run `mcp__drm-copilot__collect_pr_context` so `artifacts/pr_context.summary.txt` exists.
2. Hand-write a PR body to a non-canonical path (e.g. `/tmp/pr_body_9.md`).
3. Run `gh pr create ... --body-file /tmp/pr_body_9.md`.
4. The hook returns `{"decision":"allow"}` and the PR is created without pr-author.

## Expected Behavior

The hook should only allow a PR whose body was produced by the pr-author handoff:
a canonical body path `artifacts/pr_body_<N>.md` with a verifiable provenance
receipt (`artifacts/pr_body_<N>.receipt.json`) whose `sha256` matches the body and
whose `created_at` is newer than the PR-context summary.

## Actual Behavior

The hook checks command shape only (inline `--body`, no body, or `--body-file`
with the context file present). With `--body-file` and an existing context file it
returns `allow`, regardless of whether pr-author produced the body or what path is used.

## Logs / Screenshots

- [x] Snippet:
- Pre-fix: `gh pr create ... --body-file /tmp/pr_body_9.md` -> `{"decision":"allow"}`

## Impact / Severity

- [ ] Blocker
- [x] High
- [ ] Medium
- [ ] Low

Governance guardrail does not enforce its stated policy; PRs can be produced
without the pr-author handoff.

## Suspected Cause / Notes

`Get-PrAuthorBypassReason` keys on the presence of `--body-file` plus the context
artifact, neither of which proves pr-author ran or constrains the body path.
Files: `.claude/hooks/enforce-pr-author-skill.ps1`, `.claude/skills/orchestrate/SKILL.md`,
`.claude/skills/pr-author/SKILL.md`.

## Proposed Fix / Validation Ideas

- [x] Add provenance checks: canonical path `artifacts/pr_body_<N>.md`, sibling
      receipt present, receipt `number` matches, `sha256(body) == receipt.sha256`,
      receipt `created_at` newer than `pr_context.summary.txt`.
- [x] Isolate I/O behind mockable seams; pure decision core; Pester coverage of every branch.
- [x] Document the PR Authoring (pr-author handoff) step + receipt schema in the orchestrate skill and add it to the PR Creation Gate.
- [x] Manual verification: the original `/tmp` command is now blocked (returns
      `PR_BODY_PATH_NONCANONICAL`); canonical path without a receipt returns
      `PR_AUTHOR_RECEIPT_MISSING`; metadata-only `gh pr edit --title` stays allowed.

## Next Step

- [ ] Promote to GitHub issue (bug-report template)
- [ ] Move to active fix folder / branch