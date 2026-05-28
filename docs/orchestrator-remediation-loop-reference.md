# Orchestrator Remediation Loop — Reference Walkthrough

This document demonstrates one fully conformant remediation cycle from start to finish. It is the canonical reference cited by `.claude/agents/orchestrator.md` (Remediation Loop Protocol section) and by `.claude/skills/remediation-handoff-atomic-planner/SKILL.md`. The example uses a fictitious feature folder `docs/features/active/example-feature-99/` with a single seeded blocking finding. Timestamps follow the `yyyy-MM-ddTHH-mm` format defined in `.claude/skills/evidence-and-timestamp-conventions/SKILL.md`.

## Cycle Overview

```
Entry timestamp: 2026-06-01T09-15
Exit timestamp:  2026-06-01T10-45
Trigger:         feature-audit.2026-06-01T08-50.md reported one blocking FAIL
Outcome:         exit_condition_met = true, blocking_count = 0
```

## State Transitions

| Step | Actor              | Action                                                                                        | next_step                                  |
|------|--------------------|-----------------------------------------------------------------------------------------------|--------------------------------------------|
| 1    | orchestrator       | Writes `remediation-inputs.2026-06-01T09-15.md` enumerating the FAIL                          | `remediation.cycle_1.plan`                 |
| 2    | atomic-planner     | Authors `remediation-plan.2026-06-01T09-15.md` per `atomic-plan-contract`                     | `remediation.cycle_1.preflight`            |
| 3    | atomic-executor    | Runs preflight under `DIRECTIVE: PREFLIGHT VALIDATION ONLY`; returns `PREFLIGHT: REVISIONS REQUIRED` with a plan delta | `remediation.cycle_1.plan`                 |
| 4    | atomic-planner     | Revises plan in place (same file, per the plan-path continuity contract)                      | `remediation.cycle_1.preflight`            |
| 5    | atomic-executor    | Re-runs preflight; returns `PREFLIGHT: ALL CLEAR`                                             | `remediation.cycle_1.execute`              |
| 6    | atomic-executor    | Executes the plan task-by-task; invokes one worker (`python-typed-engineer`) internally       | `remediation.cycle_1.reaudit`              |
| 7    | feature-review     | Writes the three reaudit artifacts at exit timestamp `2026-06-01T10-45`                       | `remediation.cycle_1.exit_check`           |
| 8    | orchestrator       | Computes `blocking_count = 0`; sets `exit_condition_met = true`                               | (loop complete; next normal step resumes)  |

## Artifacts Produced (Five Required)

All paths are relative to the example feature folder `docs/features/active/example-feature-99/`.

1. `remediation-inputs.2026-06-01T09-15.md` — orchestrator-authored.
2. `remediation-plan.2026-06-01T09-15.md` — atomic-planner-authored.
3. `code-review.2026-06-01T10-45.md` — feature-review-authored.
4. `feature-audit.2026-06-01T10-45.md` — feature-review-authored.
5. `policy-audit.2026-06-01T10-45.md` — feature-review-authored.

Note that the entry timestamp `2026-06-01T09-15` is used for the inputs and plan artifacts, and the exit timestamp `2026-06-01T10-45` is used for the three reaudit artifacts. This is the entry-ts / exit-ts rule defined in `.claude/skills/remediation-handoff-atomic-planner/SKILL.md`.

## Sample Checkpoint Fragment

The `artifacts/orchestration/orchestrator-state.json` checkpoint records the cycle in a `remediation_loop` object that conforms to `.claude/schemas/orchestrator-state.schema.json`. The shape below shows the state after step 8 of the cycle.

```json
{
  "objective": "Fix issue #99 — example feature",
  "next_step": "remediation.cycle_1.exit_check",
  "completed_steps": [
    "remediation.cycle_1.inputs",
    "remediation.cycle_1.plan",
    "remediation.cycle_1.preflight",
    "remediation.cycle_1.execute",
    "remediation.cycle_1.reaudit",
    "remediation.cycle_1.exit_check"
  ],
  "last_updated": "2026-06-01T10-47-00Z",
  "remediation_loop": {
    "current_cycle": 1,
    "cycles": [
      {
        "entry_timestamp": "2026-06-01T09-15",
        "exit_timestamp": "2026-06-01T10-45",
        "inputs_path": "docs/features/active/example-feature-99/remediation-inputs.2026-06-01T09-15.md",
        "plan_path": "docs/features/active/example-feature-99/remediation-plan.2026-06-01T09-15.md",
        "preflight": {
          "iterations": 2,
          "final_status": "clear"
        },
        "execution_status": "complete",
        "audit_paths": {
          "code_review": "docs/features/active/example-feature-99/code-review.2026-06-01T10-45.md",
          "feature_audit": "docs/features/active/example-feature-99/feature-audit.2026-06-01T10-45.md",
          "policy_audit": "docs/features/active/example-feature-99/policy-audit.2026-06-01T10-45.md"
        },
        "blocking_count": 0,
        "exit_condition_met": true
      }
    ]
  }
}
```

## Validator Pass

The checkpoint above passes the constraints defined in `.claude/schemas/orchestrator-state.schema.json` and enforced by `.claude/hooks/validate-orchestrator-output.ps1`:

- `plan_path` is present.
- `preflight.final_status == "clear"` matches `execution_status == "complete"` (no malformed execution-without-cleared-preflight).
- `exit_condition_met == true` is paired with `blocking_count == 0` (no malformed exit gate).
- `preflight.final_status` is one of `clear|changes_requested|pending`; `execution_status` is one of `not_started|in_progress|complete|failed`.

## Failure Mode: Why a Single Cycle Was Sufficient

The example assumes the seeded FAIL was fully addressed by the executed plan and that the reaudit produced no new findings. If the reaudit had surfaced a new blocking finding, the orchestrator would not have re-prompted the worker. Instead, the orchestrator would:

1. Mark `exit_condition_met = false` for cycle 1.
2. Increment `current_cycle` to `2`.
3. Author a new `remediation-inputs.<new-ts>.md` at the new entry timestamp.
4. Delegate to `atomic-planner` for a new `remediation-plan.<new-ts>.md`.
5. Run the full chain again.

This is the scope-change rule and the exit gate together. They are the load-bearing constraints that prevent the historical PR #24 / issue #19 defect documented in issue #25.
