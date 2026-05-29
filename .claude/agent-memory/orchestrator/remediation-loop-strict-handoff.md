---
name: remediation-loop-strict-handoff
description: Remediation is a closed atomic-planner -> atomic-executor -> feature-review loop; the orchestrator must not call typed-engineer workers directly during remediation, and every cycle must produce a remediation-plan.<ts>.md.
metadata:
  type: feedback
---

The orchestrator's remediation loop has a strict five-artifact, three-delegate contract. Do not shortcut it.

**Cycle contract (each remediation cycle):**

```
remediation-inputs.<entry-ts>.md     (orchestrator writes from audit findings)
  -> atomic-planner                   produces remediation-plan.<entry-ts>.md
  -> atomic-executor                  preflight verdict
  -> atomic-planner                   plan revisions (loop until preflight clears)
  -> atomic-executor                  executes the plan task-by-task (it calls workers internally)
  -> feature-review                   produces code-review.<exit-ts>.md, feature-audit.<exit-ts>.md, policy-audit.<exit-ts>.md
  -> orchestrator                     exit-check: if blocking_count == 0 exit, else cycle N+1
```

**Why:** Confirmed by user 2026-05-28 after PR #24 (issue #19). In that session I wrote `remediation-inputs.2026-05-28T12-17.md`, then called `python-typed-engineer` directly three times in a row (initial fix, suppression cleanup, file-size split) plus a fourth direct commit (`553547d`) for the CI Qt-libs workflow fix, bypassing the audit set entirely. No `remediation-plan.<ts>.md` was ever produced and no `atomic-executor` preflight was run. The cascading rework happened because there was no plan to constrain scope or anticipate the file-size cap and the unauthorized-suppression policy. The user's correction: the loop is mandatory and exact. See [[remediation-handoff-atomic-planner]] for the full chain and the five-artifact contract.

**How to apply:**

1. During remediation, the orchestrator may delegate only to `atomic-planner`, `atomic-executor`, and `feature-review`. Direct calls to `python-typed-engineer`, `typescript-engineer`, `csharp-typed-engineer`, or `powershell-typed-engineer` are prohibited inside a remediation cycle. Those workers are invoked by `atomic-executor` as it processes plan tasks.

2. Every cycle MUST produce exactly five artifacts at the two timestamps (entry-ts and exit-ts): `remediation-inputs.<entry-ts>.md`, `remediation-plan.<entry-ts>.md`, `code-review.<exit-ts>.md`, `feature-audit.<exit-ts>.md`, `policy-audit.<exit-ts>.md`. Validate file presence before declaring the cycle complete.

3. Treat preflight as a separate state. Record `preflight.outcome` and `preflight.iterations`. A `changes_requested` outcome routes back to `atomic-planner`, never back to the orchestrator or directly to execution.

4. Scope changes discovered during execution (a new unauthorized suppression, a file-size cap hit, a missing policy doc) require a new cycle (write a follow-up `remediation-inputs.<ts>.md`), not a re-prompt of the same worker.

5. A failed required CI check after the PR is open enters the same loop. Workflow changes are implemented by `atomic-executor` running the plan, not by the orchestrator authoring the YAML. This also satisfies `.claude/rules/ci-workflows.md` and the feature-review `modified-workflow-needs-green-run` rule.

6. Persist `remediation_loop.current_cycle` and `remediation_loop.cycles[]` in `orchestrator-state.json`. Each cycle entry holds `timestamp`, `inputs_path`, `plan_path`, `preflight.{iterations, final_status}`, `execution_status`, `audit_paths`, `blocking_count`, and `exit_condition_met`. The `next_step` field uses cycle-aware names: `remediation.cycle_N.plan`, `remediation.cycle_N.preflight`, `remediation.cycle_N.execute`, `remediation.cycle_N.reaudit`, `remediation.cycle_N.exit_check`. The cycle-aware checkpoint shape is defined in `.claude/schemas/orchestrator-state.schema.json` and validated by `.claude/hooks/validate-orchestrator-output.ps1`.

7. Exit the loop only when the most recent cycle's `blocking_count == 0` derived from the post-execution audit artifact, not by visual inspection.
