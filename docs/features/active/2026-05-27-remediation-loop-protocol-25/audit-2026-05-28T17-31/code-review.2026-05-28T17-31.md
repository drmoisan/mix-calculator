# Code Review: remediation-loop-protocol (#25)

**Review Date:** 2026-05-28
**Reviewer:** feature-review
**Feature Folder:** `docs/features/active/remediation-loop-protocol-25/`
**Feature Folder Selection Rule:** Resolved by caller via `feature-folder` field in the orchestrator state.
**Base Branch:** `main` @ `7836c24ed350ebe654b924373335aa606c1fa215`
**Head Branch:** `mix-calculator-wt-2026-05-28-12-52` @ `c23ed87b1a527ddacaa10ea24af9ecfa44cebf6a`
**Review Type:** Initial review (Phase 6 reaudit equivalent)

## Executive Summary

This branch fixes issue #25 by adding a "Remediation Loop Protocol" to the orchestrator agent, documenting the full handoff chain in the dedicated skill, recording an orchestrator memory citing the strict-handoff constraint, publishing a repo-local JSON Schema for `orchestrator-state.json`, extending the `SubagentStop` validator hook to enforce the new `remediation_loop` shape, and shipping a fixture-based Pester suite for the new validation function. The work also produces a reference walkthrough under `docs/`.

**What changed:**
- PowerShell hook gained a new `Test-RemediationLoopShape` validator function and a one-line invocation from the entrypoint `Invoke-OrchestratorOutputValidation`. The hook grew from 141 lines to 223 lines.
- A new Pester test file delivers six fixture-based unit tests across positive and negative paths for `Test-RemediationLoopShape`. Pure functions, no I/O, no temp files.
- A new JSON Schema at `.claude/schemas/orchestrator-state.schema.json` captures the `remediation_loop` shape (current_cycle + cycles[]), with required fields, enum domains, and `allOf/if/then` conditional rejections matching the schema described in issue #25 Proposed Fix item 3.
- Markdown updates: orchestrator agent definition gained sections for `Remediation Loop Protocol`, `Prohibited Delegations`, `Required Artifacts Per Cycle`, `Preflight Sub-State Semantics`, `Scope-change Rule`, `Exit Gate`, and `Citations`. The handoff skill documents the chain and the entry-ts/exit-ts contract.
- A reference walkthrough at `docs/orchestrator-remediation-loop-reference.md` carries one full conformant cycle, including a sample checkpoint fragment and validator pass.

**Top 3 risks:**
1. The hook's entrypoint `Invoke-OrchestratorOutputValidation` is not directly tested. The new `Test-RemediationLoopShape` call path inside it can fail under realistic checkpoint payloads in ways the fixture-based tests cannot detect (for example a payload where `checkpoint.remediation_loop` is a string instead of an object, or a malformed nested cycle the JSON parser surfaces as `$null`). File-level coverage sits at 42.1%.
2. The MCP tool `mcp__drm-copilot__validate_orchestration_artifacts` with `artifact_type: "orchestrator-state"` uses its own built-in schema, not the new repo-local schema. AC#6's literal text names the MCP tool as the enforcement point, but enforcement actually happens through the hook validator and the schema-on-disk. Future readers may expect the MCP tool itself to enforce the constraint.
3. The hook is invoked only at SubagentStop time. A bad `remediation_loop` shape recorded mid-cycle is not detected until the orchestrator next terminates, by which point downstream tools may have already consumed the malformed state. This is a design choice already present in the pre-change hook and is therefore not a new risk, but it is worth noting because the new validator increases the surface area of state the hook depends on.

**PR readiness recommendation:** **Needs Revision** — one Blocking finding (file-level coverage 42.1% vs 85% threshold) prevents Go. A second non-blocking item asks for a clarifying note in `evidence/qa-gates/ac-6-schema-shape.2026-05-28T12-57.md`.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Blocker | `.claude/hooks/validate-orchestrator-output.ps1` | whole file (lines 133-209 in particular) | File-level Pester line coverage is 42.1% (32/76), below the uniform 85% threshold in `.claude/rules/quality-tiers.md` Authoritative Decision #2. The new `Test-RemediationLoopShape` is at 96.67%, but `Invoke-OrchestratorOutputValidation` lacks any direct tests, including the newly added call to `Test-RemediationLoopShape` on lines 200-207. | Add Pester tests for `Invoke-OrchestratorOutputValidation` that synthesize `CLAUDE_HOOK_INPUT` JSON payloads and mock `Get-CheckpointFileContent` (existing seam) to drive at minimum: (a) valid payload + conformant checkpoint with `remediation_loop`; (b) valid payload + checkpoint with malformed `remediation_loop.cycles[0]` for each of the three rejection paths. Re-run the targeted Pester coverage command in Appendix A of the policy audit and confirm file-level line coverage >= 85%. | Coverage is mandatory for every language with changed files. The qa-gate's 96.67% figure measures only the new function, not the modified file. | `artifacts/pester/targeted-cov.xml` (this audit) shows LINE covered=32 missed=44; qa-gate `docs/features/active/remediation-loop-protocol-25/evidence/qa-gates/poshqc-test-final.2026-05-28T12-57.md` (interpretation paragraph). |
| Minor | `docs/features/active/remediation-loop-protocol-25/evidence/qa-gates/ac-6-schema-shape.2026-05-28T12-57.md` | Status block at file end | The qa-gate records PASS based on repo-local enforcement (schema + hook), but AC#6's literal text says the constraint is enforced by `mcp__drm-copilot__validate_orchestration_artifacts`. The MCP tool's built-in schema is unchanged. The divergence is not flagged in the qa-gate. | Append a one-line note: "Enforcement realized via repo-local `.claude/schemas/orchestrator-state.schema.json` + `.claude/hooks/validate-orchestrator-output.ps1::Test-RemediationLoopShape`. The MCP tool's built-in `orchestrator-state` schema is owned by the upstream `@danmoisan/drm-copilot-mcp` package and was not modified by this PR." | Reviewer auditability: a future reader running the MCP tool will see it not enforcing `remediation_loop` and may file a duplicate bug. | Live verification this audit: `mcp__drm-copilot__validate_orchestration_artifacts artifact_type=orchestrator-state artifact_path=artifacts/orchestration/orchestrator-state.json` returned `ok: false` complaining about `relativeFile`, `long-name`, `work-mode`, `plan-path`, and `delegation_receipts must be a list` — none of these are `remediation_loop` constraints. |
| Info | `.claude/agents/orchestrator.md` | Lines 91-95, 110-157 | The `Remediation Loop Protocol` section is internally consistent, names exactly the three permitted delegates, lists exactly five required artifacts per cycle, and documents the preflight sub-state and exit gate. Footnote at line 157 confirms the `feature-audit.<ts>.md` naming decision. | None. | Documents the load-bearing constraint that prevents recurrence of the PR #24/issue #19 defect. | Direct read of file. |
| Info | `tests/claude/hooks/validate-orchestrator-output.remediation-loop.Tests.ps1` | Lines 17-69 | `BeforeAll` builds in-memory `pscustomobject` fixtures via `New-ConformantCycle` and `New-ConformantLoop`. No real disk access, no temp files, no network. Dot-sources the hook via `$PSScriptRoot` resolution. | None. | Confirms fixture-based approach declared in research note section 4 and AC#9 qa-gate. | Direct read of file. |
| Info | `.claude/schemas/orchestrator-state.schema.json` | Lines 92-126 (`allOf/if/then`) | Conditional rejections express AC#6's invariants in pure JSON Schema. Constraints: `exit_condition_met == true` requires `blocking_count == 0`; any execution_status in `{in_progress, complete, failed}` requires `preflight.final_status == "clear"`. | None. | The schema-on-disk is the source of truth; the hook validator implements the same constraints in PowerShell for runtime enforcement. | Direct read of file. |

No additional Blocker findings.

## Implementation Audit

### PowerShell implementation audit

#### What changed well

- `Test-RemediationLoopShape` is a pure function (`[CmdletBinding()][OutputType([hashtable])]`) returning `{ Ok; Message }`. It accepts `[AllowNull()]` so the absence of `remediation_loop` is a valid input. The rejection ordering matches the schema's conditional ordering: missing `plan_path` first, then exit-gate consistency, then execution-without-cleared-preflight.
- The function uses `@($RemediationLoop.PSObject.Properties.Name)` to test field presence safely under `Set-StrictMode -Version Latest`, avoiding the trap where `$null.field` access would throw.
- The entrypoint `Invoke-OrchestratorOutputValidation` already returned `{ Ok; Message }`; the new `Test-RemediationLoopShape` call composes naturally, with a single forward of `$loopResult.Message` to the caller.
- The dot-source guard (`if ($MyInvocation.InvocationName -eq '.')`) at lines 213-215 ensures the hook can be sourced into the Pester test scope without executing the entrypoint. This is the right seam for fixture-based testing.

#### API and safety notes

- All three functions declare `[CmdletBinding()]` and `[Parameter(Mandatory = $true)]` where mandatory.
- No global state or script-scoped mutable variables.
- No `Invoke-Expression`, no plaintext secrets, no hard-coded paths beyond `CheckpointPath` (a parameter with a defaulted value).
- Uses approved PowerShell verbs (`Test`, `Invoke`, `Get`, `New`).
- 223 lines, under the 500-line cap.

#### Error handling and logging

- Returns structured `{ Ok; Message }` rather than throwing. The top-level entrypoint converts a failed `Ok` to `Write-Error` + `exit 1` so the hook exit code propagates to Claude Code's SubagentStop machinery.
- No broad `catch`; only `try/catch` around `ConvertFrom-Json -ErrorAction Stop`, which is the smallest necessary surface.
- Error messages name the failed field and the offending value, which is what the test fixtures assert against.

### Markdown implementation audit

#### What changed well

- `.claude/agents/orchestrator.md` (157 lines) — new `## Remediation Loop Protocol` section lists exactly three permitted delegates, prohibits direct typed-engineer worker calls by name, enumerates the five required artifacts, documents the preflight sub-state with the `clear|changes_requested|pending` enum, documents the scope-change rule and exit gate, and adds a `### Citations` subsection pointing at the SKILL and the new memory. The `### CI Monitoring and Post-PR Remediation` subsection ties step 9 to the loop.
- `.claude/skills/remediation-handoff-atomic-planner/SKILL.md` (113 lines) — full chain diagram, trigger conditions, required inputs, required artifacts, timestamp rule, plan-shape citation of `atomic-plan-contract`, preflight sub-loop semantics, and exit-gate computation.
- `.claude/agent-memory/orchestrator/remediation-loop-strict-handoff.md` (14 lines) — frontmatter declares `metadata.type: feedback`; body carries the rule, `**Why:**`, and `**How to apply:**` lines that explicitly reference the PR #24/issue #19 historical incident; links to `[[remediation-handoff-atomic-planner]]`.
- `.claude/agent-memory/orchestrator/MEMORY.md` — one-line index entry under ~150 characters.
- `docs/orchestrator-remediation-loop-reference.md` (101 lines) — narrates a single conformant cycle with a state-transition table, lists the five artifact filenames with both entry-ts and exit-ts, and includes a sample `orchestrator-state.json` fragment that the schema accepts.

#### Notes

- The footnote at line 157 of `orchestrator.md` documents the `feature-audit.<ts>.md` naming decision. The naming is consistent across every changed Markdown file.

### JSON Schema implementation audit

- `.claude/schemas/orchestrator-state.schema.json` (146 lines) — uses `https://json-schema.org/draft/2020-12/schema`; declares all required fields per AC#6; uses `enum` for `final_status` and `execution_status`; expresses the two invariants via `allOf/if/then` with `"const"` predicates.
- `additionalProperties: true` at the top level allows the existing orchestrator-state shape to coexist; `additionalProperties: false` on the cycle and preflight sub-objects is appropriately strict.
- `plan_path` carries `minLength: 1`, matching the validator hook's `[string]::IsNullOrWhiteSpace([string]$cycle.plan_path)` check.

## Test Quality Audit

### Reviewed test and QA artifacts

- `tests/claude/hooks/validate-orchestrator-output.remediation-loop.Tests.ps1` (152 lines) — six fixture-based Pester v5 tests across two `Describe` blocks. Verifies that `Test-RemediationLoopShape` accepts a null loop, a single conformant cycle, and three sequential conformant cycles; rejects a cycle whose `plan_path` is missing; rejects an `exit_condition_met == true` with non-zero `blocking_count`; rejects an `execution_status` in `{in_progress}` paired with `preflight.final_status == 'pending'`. Pure function tests, no Mocks, no temp files, no I/O.
- `artifacts/pester/pester-junit.xml` — confirms 6 passed, 0 failed in the new suite.
- `artifacts/pester/powershell-coverage.xml` — package `.claude/hooks` LINE 0/284. The bundled tracked-classes set does not include `validate-orchestrator-output.ps1`; documented in qa-gate.
- `artifacts/pester/targeted-cov.xml` (produced this audit) — file-level LINE covered=32 missed=44 total=76 = 42.1%. INSTRUCTION covered=54 missed=78. METHOD covered=2 missed=2 (the two methods covered are `Test-RemediationLoopShape` and one helper; the entrypoint `Invoke-OrchestratorOutputValidation` is the uncovered method).
- `docs/features/active/remediation-loop-protocol-25/evidence/qa-gates/poshqc-test-final.2026-05-28T12-57.md` — qa-gate; reports per-function 96.67%.

### Quality assessment prompts

- **Determinism:** Tests construct fixtures inline; no time, no random, no I/O. PASS.
- **Isolation:** Each `It` builds its own fixture from `New-ConformantCycle` and asserts a single behavior. PASS.
- **Speed:** Targeted run completed under 5s. PASS.
- **Diagnostics:** Negative tests assert on multiple `Should -Match` patterns naming the specific field; a failure would identify the broken rejection path. PASS for what is tested; gap exists for `Invoke-OrchestratorOutputValidation` (no tests).

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | PASS | Hand-reviewed; no tokens or credentials in any changed file. |
| No unsafe subprocess or command construction | PASS | Hook calls no external processes. No `Invoke-Expression`. |
| Input validation at boundaries | PASS | `Invoke-OrchestratorOutputValidation` validates payload non-empty, JSON-parsable, required fields present, then delegates to `Test-RemediationLoopShape`. |
| Error handling remains explicit | PASS | Structured `{ Ok; Message }` returns; `try/catch` only around `ConvertFrom-Json`. |
| Configuration / path handling is safe | PASS | `CheckpointPath` parameter has safe default; `Test-Path -LiteralPath` used in `Get-CheckpointFileContent`. |
| Schema constraints match code constraints | PASS | Schema's `allOf/if/then` mirrors the hook's three rejection conditions; both reject the same shapes. |

## Research Log

No external research required. The repository's research note at `artifacts/research/2026-05-28-remediation-loop-protocol-mapping.md` was consulted (cited by Phase 0 evidence and by the plan); section 4 of that note documented the fixture-fallback decision underpinning AC#9.

## Verdict

The implementation is internally consistent, satisfies nine of ten acceptance criteria at the literal level and the tenth (AC#6) at the spirit level through repo-local enforcement, and ships with focused tests for the new function. The branch is ready for normal PR flow once the file-level coverage gap on `.claude/hooks/validate-orchestrator-output.ps1` is closed (proposed via direct tests for `Invoke-OrchestratorOutputValidation` as described in the Blocker finding). The Minor finding on the AC#6 qa-gate is a documentation tweak and should be paired with the Blocker remediation but does not block on its own.
