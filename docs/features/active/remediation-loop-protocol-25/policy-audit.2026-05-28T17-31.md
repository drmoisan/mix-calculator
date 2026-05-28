# Policy Compliance Audit: remediation-loop-protocol (#25)

**Audit Date:** 2026-05-28
**Reviewer:** feature-review
**Feature Folder:** `docs/features/active/remediation-loop-protocol-25/`
**Base Branch:** `main` @ `7836c24ed350ebe654b924373335aa606c1fa215`
**Head Branch:** `mix-calculator-wt-2026-05-28-12-52` @ `c23ed87b1a527ddacaa10ea24af9ecfa44cebf6a`
**Code Under Test:** PowerShell hook `.claude/hooks/validate-orchestrator-output.ps1`; Pester test `tests/claude/hooks/validate-orchestrator-output.remediation-loop.Tests.ps1`; JSON schema `.claude/schemas/orchestrator-state.schema.json`; markdown updates to `.claude/agents/orchestrator.md`, `.claude/skills/remediation-handoff-atomic-planner/SKILL.md`, `.claude/agent-memory/orchestrator/remediation-loop-strict-handoff.md`, `.claude/agent-memory/orchestrator/MEMORY.md`, and `docs/orchestrator-remediation-loop-reference.md`; feature-folder docs and evidence under `docs/features/active/remediation-loop-protocol-25/`.

## Scope Note

Scope is the full branch diff `7836c24..c23ed87`. No caller narrowing was applied. The branch diff includes Markdown, PowerShell, Pester, and JSON. No Python, TypeScript, or C# production files have changed.

## Coverage Metrics by Language

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|---------------|-------|-------------|-------------------|----------------------|-------------------|
| PowerShell | 1 production (`.claude/hooks/validate-orchestrator-output.ps1`) + 1 test (`tests/claude/hooks/validate-orchestrator-output.remediation-loop.Tests.ps1`) | 6 new fixture tests | PASS 6/6 | 0.00% lines, 0.00% funcs (baseline JaCoCo `artifacts/pester/powershell-coverage.xml`: `.claude/hooks` package LINE covered=0 missed=141; file not tracked by bundled runner pre-change) | 42.10% lines (32/76), 50.00% funcs (2/4) on file-wide targeted Pester run (this audit, command in Appendix B) | 96.67% on new function `Test-RemediationLoopShape` (29/30 lines per qa-gate); 42.10% file-wide |
| Pester (test file) | 1 | 6 | PASS 6/6 in `artifacts/pester/pester-junit.xml` | N/A (test code) | N/A (test code) | N/A |
| Markdown | 9 changed | N/A | N/A | N/A | N/A | N/A |
| JSON (schema) | 1 new | N/A | N/A (parsed via `ConvertFrom-Json`) | N/A | N/A | N/A |
| Python | 0 | N/A | N/A | N/A | N/A | N/A |
| TypeScript | 0 | N/A | N/A | N/A | N/A | N/A |
| C# | 0 | N/A | N/A | N/A | N/A | N/A |

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - out of scope`
- TypeScript post-change coverage artifact: `N/A - out of scope`
- PowerShell baseline coverage artifact: `docs/features/active/remediation-loop-protocol-25/evidence/baseline/poshqc-test.2026-05-28T12-57.md`
- PowerShell post-change coverage artifact: `docs/features/active/remediation-loop-protocol-25/evidence/qa-gates/poshqc-test-final.2026-05-28T12-57.md` (file-level 42.1% measured this audit via targeted Pester invocation; artifact `artifacts/pester/targeted-cov.xml`)
- Per-language comparison summary: section 1.2.1 below

**Non-negotiable verdict rule:** No policy audit may report PASS unless it includes numeric baseline and post-change coverage metrics for every language in scope.

**Fail-closed rule:** If any required baseline artifact, QA artifact, or coverage-comparison artifact is missing, the verdict must be BLOCKED or INCOMPLETE, never PASS.

## Naming Decision

The plan and orchestrator agent definition use `feature-audit.<ts>.md` for the third reaudit artifact. The user's verbal description referenced `feature-review.<ts>.md`. The repository convention under `docs/features/active/**` is `feature-audit.<ts>.md`. This audit confirms the naming choice and uses `feature-audit.2026-05-28T17-31.md` as the sibling artifact. Confirmation requested.

## Rejected Scope Narrowing

None. The caller prompt explicitly states "Do not narrow scope at the orchestrator's request; the SKILL's invariant governs." No narrowing was attempted.

## Evidence Location Compliance

Git diff scan for `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, `artifacts/coverage/` paths:

```
git diff --name-only 7836c24..HEAD -- 'artifacts/baselines/**' 'artifacts/qa/**' 'artifacts/evidence/**' 'artifacts/coverage/**'
(no output)
```

No non-canonical evidence paths were committed. All evidence resides under `docs/features/active/remediation-loop-protocol-25/evidence/<kind>/`. The repo-local schema sits at `.claude/schemas/orchestrator-state.schema.json` and is a configuration artifact rather than an evidence artifact; placement is appropriate.

The `scripts/validate_evidence_locations.py` Python validator is absent in this repository; only the PowerShell PreToolUse hook exists. A git-diff scan is the practical substitute.

## Executive Summary

The branch implements the remediation-loop-protocol bug fix end-to-end through documentation (orchestrator agent, skill, memory, walkthrough), schema (repo-local JSON Schema), and a validator-hook extension (PowerShell + Pester fixtures). Most policy gates pass: PoshQC format and analyze are clean, all 167 Pester tests pass, all files are under the 500-line cap, no policy documents under `.claude/rules/` or `.github/instructions/` were edited, and no historical-folder edits or constrained-agent edits occurred.

One blocking finding stands: file-level line coverage on the changed production file `.claude/hooks/validate-orchestrator-output.ps1` is 42.1% (32/76 lines), below the uniform 85% threshold in `.claude/rules/quality-tiers.md` (Authoritative Decision #2) and `.claude/rules/general-unit-test.md`. The qa-gates artifact reports 96.67% on the new `Test-RemediationLoopShape` function only; the entrypoint `Invoke-OrchestratorOutputValidation` (which is the larger and modified part of the file) is largely uncovered. Coverage applies to changed files as a whole, not just newly added functions.

One non-blocking PARTIAL stands: AC#6 specifies that the schema validated by `mcp__drm-copilot__validate_orchestration_artifacts` requires the `remediation_loop` object shape. The MCP tool's built-in schema was not (and could not be) modified; the implementer's repo-local schema and hook validator capture the same constraints but are enforced through different channels. The qa-gate `ac-6-schema-shape.2026-05-28T12-57.md` does not document this divergence as a known limitation.

**Policy documents evaluated:**
- PASS `.claude/rules/general-code-change.md`
- PARTIAL `.claude/rules/general-unit-test.md` (coverage on changed file is 42.1% vs 85% threshold)
- PASS `.claude/rules/quality-tiers.md` — tier classification not affected by this docs/hook change; however the uniform 85%/75% coverage thresholds defined here are the policy basis for the coverage FAIL.
- PASS `.claude/rules/powershell.md` — format, analyze, advanced functions with `CmdletBinding`, no broad catches, no globals.
- PASS `.claude/rules/ci-workflows.md` — no workflow YAML files were edited.
- PASS `.claude/rules/tonality.md`.
- N/A Python, TypeScript, C# rules — out of scope.

**Temporary artifacts cleanup:**
- PASS Targeted Pester coverage file `artifacts/pester/targeted-cov.xml` was produced by this audit for evidence verification. The file is gitignored under `artifacts/`; it is verification evidence, not a temp script.

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Independence — Tests run in any order | PASS | `BeforeAll` builds in-memory fixtures via `New-ConformantCycle` and `New-ConformantLoop`; no test mutates shared state. |
| Isolation — Each test targets single behavior | PASS | Six `It` blocks each cover one positive or one negative path on `Test-RemediationLoopShape`. |
| Fast Execution | PASS | Pester JUnit reports the new file completed within the suite's 4.972s aggregate; targeted re-run finished under 5s. |
| Determinism | PASS | No randomness, no time dependency, no I/O. Dot-sources the hook and exercises the pure validation function. |
| Readability & Maintainability | PASS | `Describe/Context/It` structure with descriptive names; `Arrange/Act/Assert` comments inside each `It`. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Baseline Coverage Documented | PASS | `docs/features/active/remediation-loop-protocol-25/evidence/baseline/poshqc-test.2026-05-28T12-57.md` records baseline file size 141 lines, untracked by bundled JaCoCo runner. |
| No Coverage Regression (uniform thresholds) | FAIL | Targeted Pester run on the changed file: file-level LINE covered 32, missed 44, total 76 = 42.1% (`artifacts/pester/targeted-cov.xml`). Threshold per `.claude/rules/quality-tiers.md` Authoritative Decision #2 and `.claude/rules/general-unit-test.md` is 85% line coverage uniform across tiers. The new function `Test-RemediationLoopShape` is at 96.67%; `Invoke-OrchestratorOutputValidation` (modified by adding the `remediation_loop` call) is largely uncovered. |
| New Code Coverage >= 85% (file-wide) | FAIL | Same as above. The qa-gate's 96.67% applies only to the new function. The file-wide gate fails. |
| Comprehensive Coverage | PARTIAL | `Test-RemediationLoopShape`: 3 positive + 3 negative paths. `Invoke-OrchestratorOutputValidation`: no direct tests on the new `remediation_loop` invocation path (no test exercises the branch where `Test-RemediationLoopShape` returns `Ok=$false` from inside the parent function). |
| Positive Flows | PASS | Three positive tests: null input, single conformant cycle, three sequential conformant cycles. |
| Negative Flows | PASS | Three negative tests: missing `plan_path`, exit_condition_met true with non-zero blocking_count, in-progress execution with pending preflight. |
| Edge Cases | PASS | `New-ConformantCycle` parameters allow boundary-case construction; cycle-count = 3 tests sequential cycles. |
| Error Handling | PARTIAL | Returns shape `{ Ok, Message }`. Negative tests verify message wording via regex. Path through `Invoke-OrchestratorOutputValidation` that calls `Test-RemediationLoopShape` is not tested. |
| Concurrency | N/A | Pure validation; not applicable. |
| State Transitions | N/A | Stateless validator. |

### 1.2.1 Per-Language Coverage Comparison

- PowerShell: Baseline: file untracked (LINE 0/141 by bundled JaCoCo) -> Post-change: LINE 32/76 = 42.1% via targeted Pester `artifacts/pester/targeted-cov.xml`. Change: +32 lines covered (from 0 absolute) but file-level 42.1% is below 85% threshold. New/changed-code coverage: 96.67% on `Test-RemediationLoopShape` only; 42.1% file-wide. Disposition: FAIL. Evidence: `artifacts/pester/targeted-cov.xml`; `docs/features/active/remediation-loop-protocol-25/evidence/qa-gates/poshqc-test-final.2026-05-28T12-57.md`.
- TypeScript: `N/A - out of scope` (no TS files changed).
- Python: `N/A - out of scope` (no Python files changed).
- C#: `N/A - out of scope` (no C# files changed).

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Clear Failure Messages | PASS | Each `It` uses `Should -Match` against specific regex tokens that name the failing field. |
| Arrange-Act-Assert Pattern | PASS | `# Arrange`, `# Act`, `# Assert` comments inside each `It`. |
| Document Intent | PASS | `.SYNOPSIS` and `.DESCRIPTION` blocks at file top; descriptive `Describe`/`It` names. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Avoid External Dependencies | PASS | No network, no live disk fixtures, no executables. Dot-sources the hook only. |
| Use Mocks/Stubs | PASS | In-memory `pscustomobject` fixtures; no Pester `Mock` registrations needed. |
| Environment Stability | PASS | No temp files. `Set-StrictMode -Version Latest` in the hook; tests respect strict mode. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Pre-submission Review | PASS | This audit and the sibling `code-review.2026-05-28T17-31.md` and `feature-audit.2026-05-28T17-31.md` constitute the required review. |

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Clarify the objective | PASS | Issue #25 body lifted verbatim into `docs/features/active/remediation-loop-protocol-25/issue.md`. |
| Read existing change plans | PASS | Plan at `docs/features/active/remediation-loop-protocol-25/plan.2026-05-28T12-57.md`. Research at `artifacts/research/2026-05-28-remediation-loop-protocol-mapping.md`. |
| Document the plan | PASS | Plan validated via `mcp__drm-copilot__validate_orchestration_artifacts` (`ok: true`, recorded in plan summary). |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Simplicity first | PASS | `Test-RemediationLoopShape` is a single linear scan over `cycles` with three conditional rejections. No new abstractions. |
| Reusability | PASS | Validation factored into a separate function the entrypoint calls; the same function is exercised by Pester via dot-sourcing. |
| Extensibility | PASS | Adding a new rejection condition is a local edit inside `Test-RemediationLoopShape`. |
| Separation of concerns | PASS | `Get-CheckpointFileContent` isolates I/O. `Test-RemediationLoopShape` is pure. `Invoke-OrchestratorOutputValidation` orchestrates. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Cohesive modules | PASS | Hook file remains focused on validating the orchestrator subagent stop payload. |
| Under 500 lines | PASS | `.claude/hooks/validate-orchestrator-output.ps1` = 223 lines. Test file = 152 lines. `.claude/agents/orchestrator.md` = 157 lines. `.claude/skills/remediation-handoff-atomic-planner/SKILL.md` = 113 lines. `.claude/agent-memory/orchestrator/remediation-loop-strict-handoff.md` = 14 lines. `docs/orchestrator-remediation-loop-reference.md` = 101 lines. `.claude/schemas/orchestrator-state.schema.json` = 146 lines. All under 500. |
| Public vs internal | PASS | The hook is invoked by Claude Code via the `hooks.SubagentStop` frontmatter in `.claude/agents/orchestrator.md`; the new `Test-RemediationLoopShape` function is internal but reachable via dot-source for tests. |
| No circular dependencies | PASS | None. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Descriptive names | PASS | `Test-RemediationLoopShape`, `Invoke-OrchestratorOutputValidation`, `Get-CheckpointFileContent`. Approved PowerShell verbs (`Test`, `Invoke`, `Get`, `New`). |
| Docs/docstrings | PASS | `<#.SYNOPSIS.DESCRIPTION#>` blocks on every function and at the file top. |
| Comment why, not what | PASS | Comments explain the rejection ordering inside `Test-RemediationLoopShape` rather than restating the code. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|-------------|--------|----------|
| 1. Formatting | PASS | `mcp__drm-copilot__run_poshqc_format` returned `ok: true` (qa-gate `poshqc-format-final.2026-05-28T12-57.md`; re-run in this audit returned `ok: true`). |
| 2. Linting | PASS | `mcp__drm-copilot__run_poshqc_analyze` with scan_folders=[`.claude/hooks`, `tests/claude/hooks`] returned `ok: true`. |
| 3. Type checking | N/A | PowerShell. |
| 4. Testing | PASS | `mcp__drm-copilot__run_poshqc_test` with scan_folders=[`tests/claude/hooks`] returned `ok: true`. JUnit shows 6 passed, 0 failed in the new suite; 58 passed across both suites in `tests/claude/hooks/`. |
| Full toolchain loop | PASS | qa-gate `poshqc-test-final.2026-05-28T12-57.md` records that the loop restarted once after PSScriptAnalyzer flagged `PSUseBOMForUnicodeEncodedFile`; second pass clean. |
| Explicit reporting | PASS | All qa-gate artifacts present under `docs/features/active/remediation-loop-protocol-25/evidence/qa-gates/`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Summarize changes | PASS | `plan.2026-05-28T12-57.md` and `evidence/qa-gates/plan-complete.2026-05-28T12-57.md`. |
| Design choices explained | PASS | "Naming Decision" section in plan; "Why" sections in memory file; reference walkthrough documents the chain. |
| Update supporting documents | PASS | `orchestrator.md`, `remediation-handoff-atomic-planner/SKILL.md`, `MEMORY.md`, and the walkthrough were updated; the schema was added. |
| Provide next steps | PASS | Plan's "S6b_pre_review_commit" -> this audit -> orchestrator exit gate. |

## 3. Language-Specific Code Change Policy Compliance

### Section 3B: PowerShell Code Change Policy Compliance

#### 3B.1 Tooling & Baseline

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Formatting with Invoke-Formatter | PASS | `mcp__drm-copilot__run_poshqc_format` ok=true twice. |
| Linting with PSScriptAnalyzer | PASS | `mcp__drm-copilot__run_poshqc_analyze` ok=true after BOM addition (the only finding on first pass). |
| Fix all findings | PASS | `PSUseBOMForUnicodeEncodedFile` was the only finding; resolved. |
| PowerShell 7+ compatible | PASS | `#Requires -Version 7.0` declared on test file. Hook uses `Set-StrictMode -Version Latest`. |

#### 3B.2 PowerShell Design & Safety

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Advanced functions | PASS | All three functions declare `[CmdletBinding()]` and `[OutputType([hashtable])]`. |
| Parameter validation | PASS | `[Parameter(Mandatory = $true)]` on critical inputs; `[AllowNull()]` where null is a valid sentinel. |
| Avoid global state | PASS | No globals or script-scoped mutable state. |
| Error handling | PASS | Returns structured `{ Ok, Message }` hashtables; no broad `catch`. Top-level uses `Write-Error` + `exit 1`. |

#### 3B.3 Structure, Naming, and Comments

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Cohesive and under 500 lines | PASS | 223 / 152 (production/test). |
| Approved verbs | PASS | `Test`, `Invoke`, `Get`, `New`. |
| Comment why | PASS | Rejection-order comment and parameter contract comments explain rationale. |

#### 3B.4 Running the Toolchain

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Step 1: Format | PASS | qa-gate. |
| Step 2: Analyze | PASS | qa-gate. |
| Step 3: Type check | N/A | PowerShell. |
| Step 4: Test | PASS | qa-gate; targeted re-run this audit. |
| Rerun loop if needed | PASS | One loop restart after BOM fix; converged. |

### Section 3D: JSON Configuration Policy Compliance

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Schema validation | PASS | File parses cleanly via `ConvertFrom-Json` (verified during AC#6 qa-gate). |
| Required $schema | PASS | `$schema: https://json-schema.org/draft/2020-12/schema` on line 2. |
| Strict JSON only | PASS | No comments or trailing commas. |
| Deterministic key order | PASS | Hand-authored with stable order; one file, not a generated artifact. |

## 4. Language-Specific Unit Test Policy Compliance

### Section 4B: PowerShell Unit Test Policy Compliance

#### 4B.1 Framework and Scope

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Use Pester v5.x | PASS | `#Requires -Modules @{ ModuleName = 'Pester'; ModuleVersion = '5.0.0' }`. Uses `BeforeAll`, `Describe`, `It`, `Should -Match`. |
| Use PoshQC Configuration | PASS | `mcp__drm-copilot__run_poshqc_test` with `scan_folders=["tests/claude/hooks"]`. |
| PowerShell 5.1 & 7+ Compatible | PARTIAL | Test file declares `#Requires -Version 7.0`. PowerShell 5.1 compatibility is not declared; non-blocking because the orchestrator agent itself runs under PowerShell 7+. |

#### 4B.2 Test Style and Structure

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Focused Unit Tests | PASS | One behavior per `It`. |
| Test Behavior Over Implementation | PASS | Tests assert returned `Ok` and `Message` shape, not internal control flow. |
| Mocking Used Sparingly | PASS | No `Mock`. Pure function tested with in-memory fixtures. |
| Organization | PASS | Test file at `tests/claude/hooks/validate-orchestrator-output.remediation-loop.Tests.ps1` mirrors `.claude/hooks/validate-orchestrator-output.ps1`. |

#### 4B.3 Naming and Readability

| Requirement | Status | Evidence |
|-------------|--------|----------|
| File Naming - *.Tests.ps1 | PASS | Filename ends `.Tests.ps1`. |
| Describe/Context/It Structure | PASS | Two `Describe` blocks split positive and negative paths. |
| Logical Grouping | PASS | Positive vs. negative path grouping is clear. |
| Docstrings/Comments | PASS | File-level `.SYNOPSIS` and `.DESCRIPTION` are present. |

#### 4B.4 Running the Toolchain

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Use PoshQCTest Command | PASS | qa-gate. |
| No Alternative Test Runners | PASS | Pester only. |

## 5. Test Coverage Detail

### `Test-RemediationLoopShape` (6 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|---------------|---------------|--------|
| accepts a state with no remediation_loop field (null input) | Positive (boundary) | 84-86 | PASS |
| accepts a state with a single conformant cycle | Positive | 84-131 | PASS |
| accepts a state with multiple sequential conformant cycles | Positive | 84-131 | PASS |
| rejects a cycle whose plan_path is missing | Negative | 100-102 | PASS |
| rejects a cycle where exit_condition_met is true and blocking_count is not 0 | Negative | 104-111 | PASS |
| rejects a cycle where execution_status is in_progress and preflight.final_status is pending | Negative | 113-127 | PASS |

**Coverage on this function:** 29/30 lines covered = 96.67% per qa-gate `poshqc-test-final.2026-05-28T12-57.md`.

### `Invoke-OrchestratorOutputValidation` (0 direct tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|---------------|---------------|--------|
| (none) | — | 200-207 only by side effect | FAIL (no direct tests in this PR) |

**Coverage on this function:** the targeted run did not exercise it directly; lines 133-209 are largely uncovered. The added call `Test-RemediationLoopShape -RemediationLoop $remediationLoop` on lines 200-207 is only reachable through the parent function and is not tested.

### `Get-CheckpointFileContent` (0 direct tests this PR)

Pre-existing helper; not modified by this PR.

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests in feature scope | 6 (new) | PASS |
| Tests Passed | 6 (100%) | PASS |
| Tests Failed | 0 | PASS |
| Execution Time | ~4.972s aggregate suite | PASS Fast |
| File-level Line Coverage on changed file | 42.1% (32/76) | FAIL |
| Function-level Line Coverage on new function | 96.67% (29/30) | PASS |
| Test File Size | 152 lines | PASS |

## 7. Code Quality Checks

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Invoke-Formatter | `mcp__drm-copilot__run_poshqc_format` | `ok: true` | PASS |
| PSScriptAnalyzer | `mcp__drm-copilot__run_poshqc_analyze` (scan_folders=[`.claude/hooks`, `tests/claude/hooks`]) | `ok: true` | PASS |
| Pester Tests | `mcp__drm-copilot__run_poshqc_test` (scan_folders=[`tests/claude/hooks`]) | `ok: true`; 6/6 passing in new file | PASS |
| Targeted Pester coverage | `Invoke-Pester -CodeCoverage .claude/hooks/validate-orchestrator-output.ps1` | LINE 32/76 = 42.1%, COVERAGE 40.9% | FAIL vs 85% |

## 8. Gaps and Exceptions

### Identified Gaps

1. **File-level coverage on `.claude/hooks/validate-orchestrator-output.ps1` is 42.1%** vs the 85% uniform threshold in `.claude/rules/quality-tiers.md` (Authoritative Decision #2). The qa-gate's 96.67% figure applies only to `Test-RemediationLoopShape`. The parent `Invoke-OrchestratorOutputValidation` is not exercised by the added tests, even though its post-change behavior includes the new `Test-RemediationLoopShape` invocation. Remediation: add Pester tests that drive `Invoke-OrchestratorOutputValidation` end-to-end with synthesized `CLAUDE_HOOK_INPUT` payloads, including at minimum: well-formed payload + valid checkpoint with conformant `remediation_loop`; well-formed payload + checkpoint with malformed cycle (each of the three rejection paths). Tests should mock `Get-CheckpointFileContent` (existing seam) rather than touch the filesystem.

2. **AC#6 literal text says the constraint is enforced by `mcp__drm-copilot__validate_orchestration_artifacts`**, but the MCP tool's built-in schema is unchanged. Repo-local enforcement (schema + hook) satisfies the intent and is documented across the citations chain, but the qa-gate artifact `ac-6-schema-shape.2026-05-28T12-57.md` does not flag the divergence. Remediation: amend the qa-gate (or feature-audit) to record that the constraint is enforced by `.claude/hooks/validate-orchestrator-output.ps1` against the repo-local schema, with a one-line note that the MCP tool's built-in schema is owned upstream by the drm-copilot package and was not modified.

### Approved Exceptions

None.

### Removed/Skipped Tests

None.

## 9. Summary of Changes

### Commits in This PR/Branch

Single-branch summary (no committed work between `7836c24` and the current working tree's HEAD `c23ed87`). Plan execution and final-QA artifacts were committed in sequence; specific commit hashes are out of scope for this audit and visible via `git log 7836c24..HEAD`.

### Files Modified

1. `.claude/agents/orchestrator.md` (MODIFIED, 157 lines) — added `## Remediation Loop Protocol` section, `### CI Monitoring and Post-PR Remediation`, citations to skill and memory, footnote on `feature-audit` naming.
2. `.claude/skills/remediation-handoff-atomic-planner/SKILL.md` (MODIFIED, 113 lines) — documented full handoff chain, five required artifacts, entry-ts/exit-ts rule, citation of `atomic-plan-contract`.
3. `.claude/agent-memory/orchestrator/MEMORY.md` (MODIFIED) — added index line for the new memory.
4. `.claude/agent-memory/orchestrator/remediation-loop-strict-handoff.md` (NEW, 14 lines) — feedback memory recording the strict delegation chain.
5. `.claude/hooks/validate-orchestrator-output.ps1` (MODIFIED, 223 lines) — added `Test-RemediationLoopShape` function and call from `Invoke-OrchestratorOutputValidation`.
6. `.claude/schemas/orchestrator-state.schema.json` (NEW, 146 lines) — repo-local JSON Schema for `orchestrator-state.json` including the `remediation_loop` shape.
7. `tests/claude/hooks/validate-orchestrator-output.remediation-loop.Tests.ps1` (NEW, 152 lines) — six fixture-based Pester tests on `Test-RemediationLoopShape`.
8. `docs/orchestrator-remediation-loop-reference.md` (NEW, 101 lines) — reference walkthrough of a conformant cycle.
9. `docs/features/active/remediation-loop-protocol-25/` (NEW folder) — issue.md, spec.md, plan.2026-05-28T12-57.md, evidence baseline + qa-gates artifacts.

## 10. Compliance Verdict

### Overall Status: PARTIALLY COMPLIANT (one Blocking finding)

The branch satisfies most policy gates and ten of ten acceptance criteria at the literal level documented by the qa-gate artifacts. One Blocking finding (file-level coverage 42.1% vs uniform 85%) prevents PASS. A second PARTIAL finding (AC#6 literal-text divergence) is non-blocking and recordable.

**Fail-closed reminder:** PASS is not permitted while the file-level coverage gate fails.

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- PASS Before Making Changes
- PASS Design Principles
- PASS Module & File Structure (all files under 500 lines)
- PASS Naming, Docs, Comments
- PASS Toolchain Execution
- PASS Summarize & Document

#### Language-Specific Code Change Policy (Section 3)

**PowerShell:**
- PASS Tooling & Baseline
- PASS PowerShell Design & Safety
- PASS Structure & Naming
- PASS Toolchain

**JSON:**
- PASS Schema and structure

#### General Unit Test Policy (Section 1)
- PASS Core Principles
- FAIL Coverage & Scenarios (file-wide 42.1% vs 85%)
- PASS Test Structure
- PASS External Dependencies
- PASS Policy Audit

#### Language-Specific Unit Test Policy (Section 4)

**PowerShell:**
- PASS Framework & Scope
- PASS Test Style & Structure
- PASS Naming & Readability
- PASS Toolchain

### Metrics Summary

- PASS 6/6 new tests passing (100%)
- PASS New function `Test-RemediationLoopShape` at 96.67% line coverage
- FAIL Changed file `.claude/hooks/validate-orchestrator-output.ps1` at 42.1% line coverage (vs 85% threshold)
- PASS All files under 500 lines
- PASS PoshQC format/analyze/test all `ok: true`
- PASS No edits to constrained agents or historical folders
- PASS No evidence-location violations

### Recommendation

**Needs revision.**

Add direct Pester tests for `Invoke-OrchestratorOutputValidation` exercising the `remediation_loop` branch and bring the file-level line coverage on `.claude/hooks/validate-orchestrator-output.ps1` to >= 85%. Once coverage clears, the branch is ready for merge.

## Appendix A: Test Inventory

Complete list of test cases delivered by the changed test file `tests/claude/hooks/validate-orchestrator-output.remediation-loop.Tests.ps1`:

1. `Test-RemediationLoopShape — positive paths` › `accepts a state with no remediation_loop field (null input)` — PASS.
2. `Test-RemediationLoopShape — positive paths` › `accepts a state with a single conformant cycle` — PASS.
3. `Test-RemediationLoopShape — positive paths` › `accepts a state with multiple sequential conformant cycles` — PASS.
4. `Test-RemediationLoopShape — negative paths` › `rejects a cycle whose plan_path is missing` — PASS.
5. `Test-RemediationLoopShape — negative paths` › `rejects a cycle where exit_condition_met is true and blocking_count is not 0` — PASS.
6. `Test-RemediationLoopShape — negative paths` › `rejects a cycle where execution_status is in_progress and preflight.final_status is pending` — PASS.

Aggregate Pester JUnit (`artifacts/pester/pester-junit.xml`) totals across the full `tests/claude/hooks/` scope: 58 tests, 0 failures, 0 errors. Repo-wide PoshQC test run: 167 tests, 0 failures.

## Appendix B: Toolchain Commands Reference

```powershell
# Format / Analyze / Test (final QA)
mcp__drm-copilot__run_poshqc_format
mcp__drm-copilot__run_poshqc_analyze  # scan_folders=[".claude/hooks","tests/claude/hooks"]
mcp__drm-copilot__run_poshqc_test     # scan_folders=["tests/claude/hooks"]

# Targeted coverage on the changed file (run by this audit)
Import-Module Pester
$cfg = New-PesterConfiguration
$cfg.Run.Path = 'tests/claude/hooks/validate-orchestrator-output.remediation-loop.Tests.ps1'
$cfg.Run.PassThru = $true
$cfg.CodeCoverage.Enabled = $true
$cfg.CodeCoverage.Path = '.claude/hooks/validate-orchestrator-output.ps1'
$cfg.CodeCoverage.OutputFormat = 'JaCoCo'
$cfg.CodeCoverage.OutputPath = 'artifacts/pester/targeted-cov.xml'
$cfg.Output.Verbosity = 'None'
$r = Invoke-Pester -Configuration $cfg
# Reported: PassedCount=6, TotalCount=6, FailedCount=0
# Coverage: 40.9% commands; LINE 32/76 = 42.1% (parsed from JaCoCo)

# Coverage interpretation
# Baseline: artifacts/pester/powershell-coverage.xml package .claude/hooks LINE covered=0 missed=284
#   (does not track validate-orchestrator-output.ps1; tracked-classes: check-powershell-test-purity, check-python-test-purity, enforce-powershell-batch-budget, enforce-python-batch-budget, validate-bash)
# Post-change comparison: LINE 0% on bundled package counter (unchanged from baseline; new code added is also not in the bundled tracked-classes set).
# Disposition relies on the targeted file-level run above, which is below the 85% threshold.
```

**Audit Completed By:** feature-review
**Audit Date:** 2026-05-28
**Policy Version:** Current (uniform 85%/75% coverage thresholds per `.claude/rules/quality-tiers.md` Authoritative Decision #2)
