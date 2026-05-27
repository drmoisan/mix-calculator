# pr-author-provenance-enforcement (Issue #11)

- Date captured: 2026-05-27
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/pr-author-provenance-enforcement-11/
- Issue: #11
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/11
- Last Updated: 2026-05-27
- Work Mode: minor-audit

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

## Scope & Non-Goals

- In scope:
  - Harden `.claude/hooks/enforce-pr-author-skill.ps1` to verify pr-author
    provenance (canonical body path + hash-matched, fresh receipt).
  - Author the Pester suite for the hook (none existed).
  - Document the PR Authoring (pr-author handoff) step, receipt schema, and the
    new PR Creation Gate condition in `.claude/skills/orchestrate/SKILL.md`.
- Out of scope / non-goals:
  - Changing the `pr-author` skill itself (`.claude/skills/pr-author/SKILL.md`).
  - Cleaning up the pre-existing non-compliant `scripts/dev-tools/evidence/`
    location (separate concern; predates this work).
  - Cryptographic non-repudiation of the receipt (impossible when one actor
    writes both body and receipt; the gate raises friction and creates an audit
    trail, not unforgeable proof).
- Explicitly excluded systems, integrations, or datasets: none (PowerShell hook
  and Markdown skill only; no Python, no data).

## Proposed Fix / Validation Ideas

- [x] Add provenance checks: canonical path `artifacts/pr_body_<N>.md`, sibling
      receipt present, receipt `number` matches, `sha256(body) == receipt.sha256`,
      receipt `created_at` newer than `pr_context.summary.txt`.
- [x] Isolate I/O behind mockable seams; pure decision core; Pester coverage of every branch.
- [x] Document the PR Authoring (pr-author handoff) step + receipt schema in the orchestrate skill and add it to the PR Creation Gate.
- [x] Manual verification: the original `/tmp` command is now blocked (returns
      `PR_BODY_PATH_NONCANONICAL`); canonical path without a receipt returns
      `PR_AUTHOR_RECEIPT_MISSING`; metadata-only `gh pr edit --title` stays allowed.

### Design summary (what changes where)

Add provenance enforcement to `Get-PrAuthorBypassReason` in the hook. For
`gh pr create`/`gh pr edit` with `--body-file`, after the existing shape checks,
require (in order): canonical body path `artifacts/pr_body_<N>.md`; a sibling
receipt `artifacts/pr_body_<N>.receipt.json`; `receipt.number == <N>`;
`sha256(body) == receipt.sha256`; and `receipt.created_at` strictly newer than
the last-write time of `artifacts/pr_context.summary.txt`.

Boundaries and invariants to preserve:

- Hook output contract unchanged: read `$env:CLAUDE_TOOL_INPUT`, emit compact
  `{"decision":"allow"}` or `{"decision":"block","reason":...}`, exit 0 (exit 1
  on malformed JSON); missing input/command = allow; dot-source guard preserved.
- Existing block cases A/B/C and the allowed metadata-only `gh pr edit` remain.

New reason codes: `PR_BODY_PATH_NONCANONICAL`, `PR_AUTHOR_RECEIPT_MISSING`,
`PR_AUTHOR_RECEIPT_NUMBER_MISMATCH`, `PR_AUTHOR_RECEIPT_HASH_MISMATCH`,
`PR_AUTHOR_RECEIPT_STALE`.

## Test Strategy

- Regression tests to add or update: `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1`
  (new; none existed before this fix).
- Unit tests for the fixed behavior and boundaries: every reason code, the
  staleness equality boundary (older/equal/newer), hash case-insensitivity, and
  the `--body-file`/`=`/quoted parser.
- Edge cases and negative scenarios: non-canonical path, missing receipt, number
  mismatch, hash mismatch, stale receipt, malformed `CLAUDE_TOOL_INPUT`, empty
  input, metadata-only `gh pr edit`.
- Coverage impact and targets for changed lines/modules: changed hook line
  coverage >= 85% (gate); branch obligation met via explicit per-branch scenarios.
- Toolchain commands to run (PowerShell: format -> analyze -> test): PoshQC
  `run_poshqc_format` -> `run_poshqc_analyze` -> `run_poshqc_test`. Type-check is
  n/a for PowerShell.

## Acceptance Criteria

- [x] Repro steps now produce the expected behavior: the original `--body-file /tmp/pr_body_9.md` command is blocked with `PR_BODY_PATH_NONCANONICAL`.
- [x] Regression test(s) added and passing: `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1` (52 tests, all passing).
- [x] Edge cases and invalid inputs handled: missing/stale/number-mismatch/hash-mismatch receipt, malformed and empty `CLAUDE_TOOL_INPUT`, metadata-only `gh pr edit`.
- [x] No unintended behavior changes outside scope: existing block cases A/B/C and the metadata-only `gh pr edit` allow path are preserved.
- [x] Required logs/telemetry updated and validated: block reasons are actionable; output contract unchanged (n/a beyond decision JSON).
- [x] Performance constraints met: one small-file hash per PR command; negligible.
- [x] Full toolchain pass completed (PowerShell format -> analyze -> test; type-check n/a): PoshQC `format`/`analyze`/`test` all `ok`; changed-file line coverage >= 85%.
- [x] Docs/config references updated: `.claude/skills/orchestrate/SKILL.md` documents the pr-author handoff, receipt schema, and PR Creation Gate condition 5.

## Next Step

- [x] Promote to GitHub issue (bug-report template)
- [x] Move to active fix folder / branch
