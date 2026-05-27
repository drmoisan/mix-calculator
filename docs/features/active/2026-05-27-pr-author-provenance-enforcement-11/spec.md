# pr-author-provenance-enforcement (Spec)

- **Issue:** #11
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-27T08-25
- **Status:** Draft
- **Version:** 0.1

## Context
The `enforce-pr-author-skill.ps1` PreToolUse hook fails to block `gh pr create` /
`gh pr edit` commands that bypass the pr-author skill. It allows any command that
merely carries a `--body-file` while `artifacts/pr_context.summary.txt` exists, so
a self-authored body at an ad-hoc path (e.g. `/tmp/pr_body_9.md`) passes without
the pr-author skill ever running. PR #10 was created this way.

Environment:
- OS/version: Windows, PowerShell 7+
- Python version: n/a (PowerShell hook + Markdown skill)
- Command/flags used: `gh pr create --base main --title ... --body-file /tmp/pr_body_9.md`
- Data source or fixture: n/a

Impact / Severity:
- [ ] Blocker
- [x] High
- [ ] Medium
- [ ] Low

Governance guardrail does not enforce its stated policy; PRs can be produced
without the pr-author handoff.


## Repro & Evidence
Steps to Reproduce:
1. Run `mcp__drm-copilot__collect_pr_context` so `artifacts/pr_context.summary.txt` exists.
2. Hand-write a PR body to a non-canonical path (e.g. `/tmp/pr_body_9.md`).
3. Run `gh pr create ... --body-file /tmp/pr_body_9.md`.
4. The hook returns `{"decision":"allow"}` and the PR is created without pr-author.

Expected:
The hook should only allow a PR whose body was produced by the pr-author handoff:
a canonical body path `artifacts/pr_body_<N>.md` with a verifiable provenance
receipt (`artifacts/pr_body_<N>.receipt.json`) whose `sha256` matches the body and
whose `created_at` is newer than the PR-context summary.

Actual:
The hook checks command shape only (inline `--body`, no body, or `--body-file`
with the context file present). With `--body-file` and an existing context file it
returns `allow`, regardless of whether pr-author produced the body or what path is used.

Logs / Screenshots:
- [x] Snippet:
- Pre-fix: `gh pr create ... --body-file /tmp/pr_body_9.md` -> `{"decision":"allow"}`


## Scope & Non-Goals
- In scope:
- Out of scope / non-goals:
- Explicitly excluded systems, integrations, or datasets:

## Root Cause Analysis
`Get-PrAuthorBypassReason` keys on the presence of `--body-file` plus the context
artifact, neither of which proves pr-author ran or constrains the body path.
Files: `.claude/hooks/enforce-pr-author-skill.ps1`, `.claude/skills/orchestrate/SKILL.md`,
`.claude/skills/pr-author/SKILL.md`.


## Proposed Fix

### Design summary (what changes where):

### Boundaries and invariants to preserve:

### Dependencies or blocked work:

### Implementation strategy (what changes, not sequencing):
	
#### Files/modules to change:

#### Functions/classes/CLI commands impacted:

#### Data flow and validation changes:

#### Error handling and logging updates:

#### Rollback/feature-flag considerations (if applicable):

### Technical specifications (interfaces/contracts):

#### Inputs/outputs and formats:

#### Required configuration keys and defaults:

#### Backward-compatibility expectations:

#### Performance constraints (latency/throughput/memory):

## Assumptions, Constraints, Dependencies
- Assumptions (environment, data, access):
- Constraints (budget, performance, compatibility):
- External dependencies (services, libraries, releases):

## Data / API / Config Impact
- User-facing or API changes:
- Data or migration considerations:
- Logging/telemetry updates (if any):
- Compatibility notes (CLI flags, config schemas, versioning):

## Test Strategy
Seeded from issue:

- [x] Add provenance checks: canonical path `artifacts/pr_body_<N>.md`, sibling
      receipt present, receipt `number` matches, `sha256(body) == receipt.sha256`,
      receipt `created_at` newer than `pr_context.summary.txt`.
- [x] Isolate I/O behind mockable seams; pure decision core; Pester coverage of every branch.
- [x] Document the PR Authoring (pr-author handoff) step + receipt schema in the orchestrate skill and add it to the PR Creation Gate.
- [ ] Manual verification: the original `/tmp` command is now blocked.

- Regression tests to add or update:
- Unit tests (pytest) for the fixed behavior and boundaries:
- Edge cases and negative scenarios (invalid inputs, missing data, boundary values):
- Error handling and logging verification:
- Coverage impact and targets for changed lines/modules:
- Toolchain commands to run (format → lint → type-check → test):
- Manual validation steps (if required):


## Acceptance Criteria
- [ ] Repro steps now produce the expected behavior in all documented environments.
- [ ] Regression test(s) added and passing (list file path and test name).
- [ ] Edge cases and invalid inputs are handled with correct errors or fallbacks.
- [ ] No unintended behavior changes outside the defined scope.
- [ ] Required logs/telemetry updated and validated (if applicable).
- [ ] Performance constraints met or explicitly waived with rationale.
- [ ] Full toolchain pass completed (format → lint → type-check → test).
- [ ] Docs/config references updated to match the new behavior.

## Risks & Mitigations
- Technical or operational risks:
- Mitigations and rollbacks:

## Rollout & Follow-up
- Release/rollout steps:
- Post-fix monitoring or clean-up tasks:
- Links: issue, PRs, related docs
