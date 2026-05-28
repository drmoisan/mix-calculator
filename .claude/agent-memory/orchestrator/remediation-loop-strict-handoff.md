---
name: remediation-loop-strict-handoff
description: During remediation cycles the orchestrator must delegate exclusively to atomic-planner, atomic-executor, and feature-review; direct typed-engineer worker calls are prohibited and bypass preflight, the atomic-plan contract, and the modified-workflow-needs-green-run rule.
metadata:
  type: feedback
---

When an audit produces findings, when toolchain checks fail, when acceptance criteria are unmet, or when a required CI check fails after the PR is open, the orchestrator MUST run the full remediation chain `atomic-planner -> atomic-executor (preflight) -> atomic-planner (revise if changes_requested) -> atomic-executor (execute) -> feature-review`. Direct calls to `python-typed-engineer`, `typescript-engineer`, `csharp-typed-engineer`, or `powershell-typed-engineer` from the orchestrator during a remediation cycle are prohibited.

Each cycle must produce exactly five artifacts: `remediation-inputs.<entry-ts>.md`, `remediation-plan.<entry-ts>.md`, `code-review.<exit-ts>.md`, `feature-audit.<exit-ts>.md`, `policy-audit.<exit-ts>.md`. The exit gate is `blocking_count == 0` against the latest reaudit set; otherwise begin cycle N+1 with a new `remediation-inputs.<new-ts>.md`.

**Why:** On 2026-05-28 the orchestrator ran on `feature/mix-pipeline-gui-19` (PR #24, issue #19), wrote `remediation-inputs.2026-05-28T12-17.md`, then called `python-typed-engineer` directly three times in succession (each scope change should have started a new cycle). No `remediation-plan.<ts>.md` was produced, `atomic-executor` preflight was skipped, and a follow-up workflow-file commit (`553547d`) bypassed the audit set entirely. The resulting feature folder is non-conformant. This memory exists so the orchestrator surfaces the strict-handoff constraint at startup. See [[remediation-handoff-atomic-planner]] for the full chain and the five-artifact contract.

**How to apply:** On any orchestrator invocation that resumes or begins a cycle whose `next_step` matches `remediation.cycle_N.*`, refuse to call typed-engineer workers directly. Route plan creation to `atomic-planner`. Route preflight and execution to `atomic-executor`. Route reaudit to `feature-review`. If a new finding appears during execution, do not re-prompt the active worker; close the active cycle and open cycle N+1 with a new `remediation-inputs.<new-ts>.md`. For workflow-file changes specifically, the loop also triggers the `modified-workflow-needs-green-run` rule. The cycle-aware checkpoint shape (`remediation_loop.cycles[]`) is defined in `.claude/schemas/orchestrator-state.schema.json` and validated by `.claude/hooks/validate-orchestrator-output.ps1`.
