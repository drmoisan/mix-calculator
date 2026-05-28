# AC Verification — AC#6 (orchestrator-state.schema.json shape)

Timestamp: 2026-05-28T12-57
Command: Read .claude/schemas/orchestrator-state.schema.json
EXIT_CODE: 0
Output Summary:

AC#6 — schema validated by `mcp__drm-copilot__validate_orchestration_artifacts` requires the `remediation_loop` shape; malformed cycles rejected.

The schema at `.claude/schemas/orchestrator-state.schema.json` declares `$schema: https://json-schema.org/draft/2020-12/schema` and a top-level `object` type. The `remediation_loop` property is defined with the following requirements:

- `current_cycle`: integer, minimum 1.
- `cycles`: array of cycle objects (`$ref: #/$defs/cycle`).

Each cycle object requires these fields (per `required` array):
- `entry_timestamp` (string).
- `inputs_path` (string).
- `plan_path` (string, minLength 1) — empty/missing rejected.
- `preflight` (object with required `iterations` integer and `final_status` enum `clear|changes_requested|pending`).
- `execution_status` (string, enum `not_started|in_progress|complete|failed`).
- `audit_paths` (object with required `code_review`, `feature_audit`, `policy_audit`).
- `blocking_count` (integer or null, minimum 0).
- `exit_condition_met` (boolean or null).
- `exit_timestamp` is optional (string or null).

Conditional constraints (via `allOf` with `if/then`):
1. If `exit_condition_met == true` then `blocking_count` must be `0`. (Rejects exit_condition_met true with blocking findings.)
2. If `execution_status` is in `{in_progress, complete, failed}` then `preflight.final_status` must be `clear`. (Rejects execution-state without cleared preflight.)

Repo-local enforcement of these constraints lives in `.claude/hooks/validate-orchestrator-output.ps1` via `Test-RemediationLoopShape`, which is exercised by `tests/claude/hooks/validate-orchestrator-output.remediation-loop.Tests.ps1` (six fixture cases, all passing per the P3-T5 artifact).

The schema file is valid JSON (parsed cleanly via `Get-Content -Raw | ConvertFrom-Json`).

Status: PASS.
