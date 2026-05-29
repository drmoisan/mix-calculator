# Remediation Inputs — Cycle Entry 2026-05-28T17-31 (issue #25)

- **Feature folder:** `docs/features/active/remediation-loop-protocol-25/`
- **Audit set producing these inputs:**
  - `docs/features/active/remediation-loop-protocol-25/policy-audit.2026-05-28T17-31.md`
  - `docs/features/active/remediation-loop-protocol-25/code-review.2026-05-28T17-31.md`
  - `docs/features/active/remediation-loop-protocol-25/feature-audit.2026-05-28T17-31.md`
- **Audit blocking count:** 1 Blocker + 1 Minor (recorded; remediation focuses on the Blocker; the Minor is bundled because it cites the same artifact and is a one-line documentation fix).

## Findings Requiring Remediation

### Finding 1 — Blocking: file-level Pester line coverage on changed PowerShell hook is 42.1% (vs uniform 85% threshold)

- **File:** `.claude/hooks/validate-orchestrator-output.ps1`
- **Policy:** `.claude/rules/quality-tiers.md` Authoritative Decision #2 (uniform 85% line / 75% branch coverage across all tiers); `.claude/rules/general-unit-test.md` (no regression on changed lines).
- **Measured:**
  - Targeted Pester run (`Invoke-Pester -CodeCoverage .claude/hooks/validate-orchestrator-output.ps1`) on the new test file: file-level LINE covered=32, missed=44, total=76 = 42.1%. Reported in `artifacts/pester/targeted-cov.xml` (class `hooks/validate-orchestrator-output`, INSTRUCTION 54/132, LINE 32/76, METHOD 2/4, CLASS 1/1).
  - Per-function: `Test-RemediationLoopShape` at 29/30 lines = 96.67%. `Invoke-OrchestratorOutputValidation` is uncovered including the newly added `Test-RemediationLoopShape -RemediationLoop $remediationLoop` call on lines 200-207.
- **Expected behavior after fix:** file-level line coverage on `.claude/hooks/validate-orchestrator-output.ps1` is >= 85% as reported by a fresh targeted Pester coverage run using the same command shown in `policy-audit.2026-05-28T17-31.md` Appendix A.
- **Verification commands:**
  - `mcp__drm-copilot__run_poshqc_format` returns `ok: true`.
  - `mcp__drm-copilot__run_poshqc_analyze` with `scan_folders=[".claude/hooks","tests/claude/hooks"]` returns `ok: true`.
  - `mcp__drm-copilot__run_poshqc_test` with `scan_folders=["tests/claude/hooks"]` returns `ok: true`.
  - Targeted Pester (verbatim from policy-audit Appendix A) reports file-level LINE coverage >= 85% and BRANCH (CommandsExecutedCount / CommandsAnalyzedCount) >= 75%.
- **Implementation guidance (do not over-specify):**
  - Add Pester tests that exercise `Invoke-OrchestratorOutputValidation` directly. The existing seam `Get-CheckpointFileContent` already isolates the I/O boundary; mock it via Pester `Mock` (`-ModuleName` not required because the function is dot-sourced into the test scope) and synthesize `CLAUDE_HOOK_INPUT` JSON.
  - Cover at minimum these payload/checkpoint pairings:
    1. Payload empty -> Ok=false, message references "CLAUDE_HOOK_INPUT is empty".
    2. Payload not JSON -> Ok=false, message references "failed to parse".
    3. Payload `{ output: "" }` -> Ok=false, message references "agent output is empty".
    4. Payload valid, checkpoint absent -> Ok=false, message references "does not exist".
    5. Payload valid, checkpoint empty content -> Ok=false, message references "is empty".
    6. Payload valid, checkpoint not JSON -> Ok=false, message references "is not valid JSON".
    7. Payload valid, checkpoint missing one of required fields (objective/completed_steps/next_step/last_updated) -> Ok=false, message references "missing required field(s)".
    8. Payload valid, checkpoint objective empty -> Ok=false, message references "empty 'objective' field".
    9. Payload valid, checkpoint without `remediation_loop` -> Ok=true.
    10. Payload valid, checkpoint with conformant `remediation_loop` -> Ok=true.
    11. Payload valid, checkpoint with malformed `remediation_loop.cycles[0].plan_path` missing -> Ok=false, message matches "missing required field 'plan_path'".
    12. Payload valid, checkpoint with malformed cycle exit_condition_met=true blocking_count=2 -> Ok=false, message matches "'exit_condition_met' is true" + "blocking_count' is '2'".
    13. Payload valid, checkpoint with execution_status=in_progress preflight pending -> Ok=false, message matches "'execution_status' is 'in_progress'" + "'preflight.final_status' is 'pending'".
  - Keep the test file under 500 lines; if growth would exceed, split into a sibling `validate-orchestrator-output.invoke.Tests.ps1` file alongside the existing remediation-loop test file.
  - Reuse the `New-ConformantCycle` / `New-ConformantLoop` helpers by moving them into a shared `BeforeAll` helper if needed, or by duplicating the minimal subset into the new test file. Do not introduce a shared utility module under `tests/`.

### Finding 2 — Minor: AC#6 qa-gate does not document the MCP-tool / repo-local enforcement divergence

- **File:** `docs/features/active/remediation-loop-protocol-25/evidence/qa-gates/ac-6-schema-shape.2026-05-28T12-57.md`
- **Policy:** `.claude/skills/evidence-and-timestamp-conventions/SKILL.md` (evidence must accurately reflect the verification command and result).
- **Expected behavior after fix:** the qa-gate carries a one-line note explicitly stating that AC#6 enforcement is realized via `.claude/schemas/orchestrator-state.schema.json` + `.claude/hooks/validate-orchestrator-output.ps1::Test-RemediationLoopShape`, and that the MCP tool `mcp__drm-copilot__validate_orchestration_artifacts` retains its upstream-owned built-in schema unchanged.
- **Verification command:** `Grep -n "Enforcement realized via repo-local"` against the qa-gate file returns one hit.
- **Implementation guidance:** append a "## Enforcement Channel" subsection or extend the existing Status block. Do not alter the original verification timestamp.

## Do Not Do

- Do not lower the 85% coverage threshold in `.claude/rules/quality-tiers.md` or `.claude/rules/general-unit-test.md`. Threshold edits are policy weakening.
- Do not modify the existing six Pester tests in `tests/claude/hooks/validate-orchestrator-output.remediation-loop.Tests.ps1` to game coverage; add a sibling test file or extend coverage with new tests.
- Do not edit any agent definition other than what is strictly required (none should be required for this remediation).
- Do not edit policy documents under `.claude/rules/` or `.github/instructions/`.
- Do not edit any file under `docs/features/active/2026-05-27-mix-pipeline-gui-19/` (the historical PR #24 folder).
- Do not introduce temporary files in tests. Mocks and inline JSON literals are acceptable.
- Do not re-prompt a typed-engineer worker directly from the orchestrator. This remediation is itself subject to the `## Remediation Loop Protocol` newly documented in `.claude/agents/orchestrator.md`: delegate to `atomic-planner` -> `atomic-executor` -> `feature-review`.
- Do not regenerate `evidence/baseline/*` artifacts. Baselines are frozen at 2026-05-28T12-57.

## Cycle Tracking

- **Cycle entry timestamp (`<entry-ts>`):** `2026-05-28T17-31`
- **Expected artifacts in this cycle:**
  1. `docs/features/active/remediation-loop-protocol-25/remediation-inputs.2026-05-28T17-31.md` (this file).
  2. `docs/features/active/remediation-loop-protocol-25/remediation-plan.2026-05-28T17-31.md` (atomic-planner output).
  3. `docs/features/active/remediation-loop-protocol-25/code-review.<exit-ts>.md` (feature-review at cycle exit).
  4. `docs/features/active/remediation-loop-protocol-25/feature-audit.<exit-ts>.md` (feature-review at cycle exit).
  5. `docs/features/active/remediation-loop-protocol-25/policy-audit.<exit-ts>.md` (feature-review at cycle exit).
- **Exit gate:** the next-cycle `feature-review` must report `blocking_count == 0` across the three reaudit artifacts.

## Pointer to Audit Artifacts

- Policy audit: `docs/features/active/remediation-loop-protocol-25/policy-audit.2026-05-28T17-31.md`
- Code review: `docs/features/active/remediation-loop-protocol-25/code-review.2026-05-28T17-31.md`
- Feature audit: `docs/features/active/remediation-loop-protocol-25/feature-audit.2026-05-28T17-31.md`
