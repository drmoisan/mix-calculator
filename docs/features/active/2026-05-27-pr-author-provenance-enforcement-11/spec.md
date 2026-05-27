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

## Root Cause Analysis
`Get-PrAuthorBypassReason` keys on the presence of `--body-file` plus the context
artifact, neither of which proves pr-author ran or constrains the body path.
Files: `.claude/hooks/enforce-pr-author-skill.ps1`, `.claude/skills/orchestrate/SKILL.md`,
`.claude/skills/pr-author/SKILL.md`.


## Proposed Fix

### Design summary (what changes where):
Add provenance enforcement to `Get-PrAuthorBypassReason` in the hook. For
`gh pr create`/`gh pr edit` with `--body-file`, after the existing shape checks,
require (in order): canonical body path `artifacts/pr_body_<N>.md`; a sibling
receipt `artifacts/pr_body_<N>.receipt.json`; `receipt.number == <N>`;
`sha256(body) == receipt.sha256`; and `receipt.created_at` strictly newer than
the last-write time of `artifacts/pr_context.summary.txt`.

### Boundaries and invariants to preserve:
- Hook output contract unchanged: read `$env:CLAUDE_TOOL_INPUT`, emit compact
  `{"decision":"allow"}` or `{"decision":"block","reason":...}`, exit 0 (exit 1
  on malformed JSON); missing input/command = allow; dot-source guard preserved.
- Existing block cases A/B/C and the allowed metadata-only `gh pr edit` remain.

### Dependencies or blocked work: none.

### Implementation strategy (what changes, not sequencing):

#### Files/modules to change:
- `.claude/hooks/enforce-pr-author-skill.ps1` (production).
- `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1` (new tests).
- `.claude/skills/orchestrate/SKILL.md` (process documentation).

#### Functions/classes/CLI commands impacted:
- Pure parser `Get-PrBodyFilePath` (handles `--body-file <v>`, `=<v>`, quoting).
- Pure decision core `Get-PrAuthorProvenanceReason` over injected facts.
- Mockable I/O seams: `Get-PrContextWriteTime`, `Test-PrBodyReceiptPresence`,
  `Get-PrBodyReceipt`, `Get-PrBodyFileHash` (plus existing
  `Get-PrContextArtifactExistence`); orchestrated by `Get-PrAuthorBypassReason`.

#### Data flow and validation changes:
Command text -> parse `--body-file` -> resolve facts via seams -> pure decision.
Reason codes: `PR_BODY_PATH_NONCANONICAL`, `PR_AUTHOR_RECEIPT_MISSING`,
`PR_AUTHOR_RECEIPT_NUMBER_MISMATCH`, `PR_AUTHOR_RECEIPT_HASH_MISMATCH`,
`PR_AUTHOR_RECEIPT_STALE`.

#### Error handling and logging updates:
Block reasons are actionable strings referencing the pr-author handoff.
Malformed `$env:CLAUDE_TOOL_INPUT` still raises/exits per the existing contract.

#### Rollback/feature-flag considerations (if applicable):
Rollback = revert the hook commit; no flag. The gate fails closed (a missing or
mismatched receipt blocks, never silently allows).

### Technical specifications (interfaces/contracts):

#### Inputs/outputs and formats:
Input: `$env:CLAUDE_TOOL_INPUT` JSON with `.command`. Output: compact decision
JSON. Receipt schema `artifacts/pr_body_<N>.receipt.json`:
`{ skill, pr_body_path, number, sha256 (lowercase hex), context_summary_path, created_at (ISO-8601) }`.

#### Required configuration keys and defaults:
Canonical body path regex `^artifacts[/\\]pr_body_(\d+)\.md$`; context summary
path `artifacts/pr_context.summary.txt`.

#### Backward-compatibility expectations:
Pre-existing allowed/blocked shapes are unchanged; only `--body-file` paths gain
the additional provenance requirement.

#### Performance constraints (latency/throughput/memory):
Negligible (one hash of a small Markdown file per PR command).

## Assumptions, Constraints, Dependencies
- Assumptions (environment, data, access): PowerShell 7+; the orchestrator writes the body and receipt at PR time per the documented handoff.
- Constraints (budget, performance, compatibility): small path (1 production hook + 1 test + skill doc); ≤500 lines/file; PowerShell 7+ compatibility.
- External dependencies (services, libraries, releases): none new (Pester 5.x, PSScriptAnalyzer/PoshQC already in repo).

## Data / API / Config Impact
- User-facing or API changes: none (internal PreToolUse guardrail behavior).
- Data or migration considerations: none.
- Logging/telemetry updates (if any): none beyond the decision JSON reasons.
- Compatibility notes: adds a provenance requirement to `gh pr create/edit --body-file`; pre-existing allowed/blocked shapes unchanged.

## Test Strategy
Seeded from issue:

- [x] Add provenance checks: canonical path `artifacts/pr_body_<N>.md`, sibling
      receipt present, receipt `number` matches, `sha256(body) == receipt.sha256`,
      receipt `created_at` newer than `pr_context.summary.txt`.
- [x] Isolate I/O behind mockable seams; pure decision core; Pester coverage of every branch.
- [x] Document the PR Authoring (pr-author handoff) step + receipt schema in the orchestrate skill and add it to the PR Creation Gate.
- [x] Manual verification: the original `/tmp` command is now blocked.

- Regression tests to add or update: `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1` (new, 52 tests).
- Unit tests for the fixed behavior and boundaries: every reason code (D/E/G/F/H), the staleness equality boundary, hash case-insensitivity, and the `--body-file`/`=`/quoted parser.
- Edge cases and negative scenarios: non-canonical path, missing receipt, number mismatch, hash mismatch, stale receipt, malformed `CLAUDE_TOOL_INPUT`, empty input, metadata-only `gh pr edit`.
- Error handling and logging verification: covered by the malformed-input and allow-path tests.
- Coverage impact and targets for changed lines/modules: 91.6% line coverage on the changed hook (≥85% gate); branch obligation met via explicit per-branch scenarios.
- Toolchain commands to run (PowerShell: format → analyze → test): PoshQC `run_poshqc_format` → `run_poshqc_analyze` → `run_poshqc_test` (all `ok` via MCP). Type-check is n/a for PowerShell.
- Manual validation steps: invoke the hook with the original `/tmp` command and a canonical-without-receipt command; confirm block reasons.


## Acceptance Criteria
- [x] Repro steps now produce the expected behavior: the original `--body-file /tmp/pr_body_9.md` command is blocked with `PR_BODY_PATH_NONCANONICAL`.
- [x] Regression test(s) added and passing: `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1` (52 tests, all passing).
- [x] Edge cases and invalid inputs handled: missing/stale/number-mismatch/hash-mismatch receipt, malformed and empty `CLAUDE_TOOL_INPUT`, metadata-only `gh pr edit`.
- [x] No unintended behavior changes outside scope: existing block cases A/B/C and the metadata-only `gh pr edit` allow path are preserved.
- [x] Required logs/telemetry updated and validated: block reasons are actionable; output contract unchanged (n/a beyond decision JSON).
- [x] Performance constraints met: one small-file hash per PR command; negligible.
- [x] Full toolchain pass completed (PowerShell format → analyze → test; type-check n/a): PoshQC `format`/`analyze`/`test` all `ok` via MCP; 91.6% line coverage.
- [x] Docs/config references updated: `.claude/skills/orchestrate/SKILL.md` documents the pr-author handoff, receipt schema, and PR Creation Gate condition 5.

## Risks & Mitigations
- Technical or operational risks: a determined actor could fabricate a matching
  receipt (same actor writes body and receipt); a future change to the canonical
  path scheme would require updating the regex.
- Mitigations and rollbacks: the gate forces a canonical, hash-matched, fresh
  receipt and leaves an audit trail (raising friction beyond the path-of-least-
  resistance bypass that occurred); rollback is a single commit revert.

## Rollout & Follow-up
- Release/rollout steps: merge via PR created through the now-enforced pr-author
  handoff (the first real exercise of the gate).
- Post-fix monitoring or clean-up tasks: re-author PR #10's non-compliant body
  through pr-author; separately remediate the pre-existing
  `scripts/dev-tools/evidence/` location.
- Links: issue #11 (https://github.com/drmoisan/mix-calculator/issues/11);
  related PR #10 (mix-decomp-transforms).
