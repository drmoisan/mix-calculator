---
name: orchestrator-state-validator-divergence
description: The MCP orchestrator-state validator is stricter than the real SubagentStop hook; conform to the canonical JSON schema's remediation_loop, not the MCP enums
metadata:
  type: reference
---

`mcp__drm-copilot__validate_orchestration_artifacts` with
`artifact_type: orchestrator-state` enforces a stricter, legacy checkpoint shape
(demands `step7_status`, specific `step5..step10_status` enum values,
`delegation_receipts` as a list, and canonical keys like `promotion-type`,
`short-name`, `plan-path`). This diverges from both the actual gate and the
documented schema.

**Why:** The authoritative termination gate is the SubagentStop hook
`.claude/hooks/validate-orchestrator-output.ps1`, which only requires
`objective`, `completed_steps`, `next_step`, `last_updated` (objective
non-empty) plus a well-formed `remediation_loop` (its `Test-RemediationLoopShape`
checks `plan_path` non-empty, `exit_condition_met==true => blocking_count==0`,
and non-`not_started` execution requires `preflight.final_status=="clear"`). The
canonical `remediation_loop` contract is `.claude/schemas/orchestrator-state.schema.json`,
where each cycle's `audit_paths` is an OBJECT `{code_review, feature_audit,
policy_audit}` (not an array) and `exit_timestamp` is allowed.

**How to apply:** Make the checkpoint satisfy the SubagentStop hook and the
canonical JSON schema (especially the `remediation_loop` cycle shape — use the
object form for `audit_paths`). Do not contort the checkpoint to the MCP tool's
extra undocumented enum demands; treat that tool's orchestrator-state mode as
advisory/legacy. The plan/policy-audit/code-review/feature-audit artifact_types
of the MCP validator are reliable and should still be used.
