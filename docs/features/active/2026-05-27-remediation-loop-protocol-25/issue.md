# Bug: remediation-loop-protocol (Issue #25)

- **Issue:** #25
- **Issue URL:** https://github.com/drmoisan/mix-calculator/issues/25
- **Work Mode:** full-bug
- **Owner:** drmoisan
- **Last Updated:** 2026-05-28T12-52
- **Status:** Active

> Source of truth: this file is a verbatim lift of the GitHub issue body for #25, captured at active-folder creation. The issue body itself remains the canonical record on GitHub.

## Summary

The orchestrator agent does not enforce the required remediation-loop delegation chain. It can write `remediation-inputs.<ts>.md` and then call typed-engineer worker subagents directly, skipping `atomic-planner` (which must produce `remediation-plan.<ts>.md`) and `atomic-executor` (which must clear preflight and execute the plan). This violates the documented audit-and-remediation protocol and produces feature folders that are missing the `remediation-plan.<ts>.md` artifact for every remediation cycle.

## Environment

- OS/version: Windows 11 + WSL-compatible toolchain; orchestration runs in Claude Code main thread.
- Command/flags used: `/goal` invocation that triggers an audit-and-remediation cycle on an open feature branch.
- Data source or fixture: any feature folder under `docs/features/active/<slug>-<issue>/` that requires post-audit remediation.

## Steps to Reproduce

1. Run the orchestrator against a feature branch that has been rebased and re-audited and where the audit finds at least one issue (blocking or material non-blocking).
2. Observe that the orchestrator writes `remediation-inputs.<entry-ts>.md` to the active feature folder.
3. Observe the orchestrator's next delegation: it invokes a typed-engineer worker (for example `python-typed-engineer`) directly with a free-form prompt describing the fixes, rather than handing the inputs to `atomic-planner`.
4. Observe that no `remediation-plan.<entry-ts>.md` is ever written to the feature folder.
5. Observe that `atomic-executor` is never invoked for preflight clearance before the worker starts changing files.
6. Observe that when execution surfaces a new constraint (an unauthorized suppression, a 500-line file-size cap, a CI failure on a missing system library), the orchestrator re-prompts the same worker with additional instructions instead of starting a new remediation cycle.
7. Observe that the post-PR CI-failure remediation is committed directly by the orchestrator with no remediation-inputs, no remediation-plan, and no audit set.

Reference session: orchestrator run on `feature/mix-pipeline-gui-19` (PR #24, issue #19) on 2026-05-28.

## Expected Behavior

A remediation cycle must execute this exact delegation chain:

```
orchestrator writes remediation-inputs.<entry-ts>.md
  -> atomic-planner          produces remediation-plan.<entry-ts>.md (atomic-plan-contract compliant)
  -> atomic-executor         returns preflight verdict
  -> atomic-planner          revises remediation-plan.<entry-ts>.md if preflight requested changes (loop until clear)
  -> atomic-executor         executes the plan task-by-task (calls workers internally; orchestrator never calls workers)
  -> feature-review          produces code-review.<exit-ts>.md, feature-audit.<exit-ts>.md, policy-audit.<exit-ts>.md
  -> orchestrator            evaluates exit condition: if latest audit blocking_count == 0 then exit; else start cycle N+1
```

Each remediation cycle must produce exactly five artifacts:

1. `docs/features/active/<slug>/remediation-inputs.<entry-ts>.md`
2. `docs/features/active/<slug>/remediation-plan.<entry-ts>.md`
3. `docs/features/active/<slug>/code-review.<exit-ts>.md`
4. `docs/features/active/<slug>/feature-audit.<exit-ts>.md`
5. `docs/features/active/<slug>/policy-audit.<exit-ts>.md`

A failed required CI check after a PR is open enters the same loop with cycle N+1. The workflow change is implemented through `atomic-executor` running the plan, not by orchestrator-authored YAML commits.

Scope changes discovered during execution start a new remediation cycle with a follow-up `remediation-inputs.<new-ts>.md`; the orchestrator does not re-prompt the same worker.

## Actual Behavior

In the reference session (PR #24, issue #19), the orchestrator:

- Wrote `remediation-inputs.2026-05-28T12-17.md`. (Correct)
- Skipped `atomic-planner` entirely. No `remediation-plan.2026-05-28T12-17.md` exists. (Defect)
- Skipped `atomic-executor` preflight. (Defect)
- Skipped `atomic-executor` execution. (Defect)
- Called `python-typed-engineer` directly three times in succession: (a) implement Findings 1 and 2, (b) remove an unauthorized `# type: ignore[method-assign]` the first call introduced, (c) split a 561-line test file to comply with the 500-line cap. (Defect: each scope change should have triggered a new cycle through atomic-planner.)
- Then invoked `feature-review` for the post-execution audit at `T13-15`. (Correct as the cycle's exit step, but the cycle itself was malformed.)
- On PR #24 CI failure (`libEGL.so.1` missing), edited `.github/workflows/_python-quality.yml` directly and committed `553547d` with no `remediation-inputs`, no `remediation-plan`, and no post-fix audit. (Defect: workflow changes are subject to `.claude/rules/ci-workflows.md` and the feature-review `modified-workflow-needs-green-run` rule, which require their own audit.)

The resulting feature folder under `docs/features/active/2026-05-27-mix-pipeline-gui-19/` contains three sets of audits plus one `remediation-inputs.<ts>.md`. The required `remediation-plan.<ts>.md` is absent.

## Impact / Severity

- High. The defect produces non-conformant feature folders for every remediation cycle and bypasses the preflight gate, the atomic-plan contract, and (for CI failures) the `modified-workflow-needs-green-run` policy rule.

## Suspected Cause / Notes

- `.claude/agents/orchestrator.md` does not list the remediation-loop delegation chain as a constraint. The orchestrator's allowed delegates are documented for the initial cycle (planner -> executor -> review) but the same rule is not restated for remediation cycles.
- `.claude/skills/remediation-handoff-atomic-planner/SKILL.md` exists in the skill catalog but is not cited as a required skill by the orchestrator agent definition, so the chain is undiscoverable from the orchestrator's invocation context.
- `artifacts/orchestration/orchestrator-state.json` schema (validated by `mcp__drm-copilot__validate_orchestration_artifacts` with `artifact_type: "orchestrator-state"`) does not require a `remediation_loop` sub-state with cycle entries.
- The orchestrator agent definition treats `step9` CI monitoring as a terminal verification step; it does not state that a CI failure transitions into a new remediation cycle.
- The orchestrator memory at `.claude/agent-memory/orchestrator/remediation-loop-strict-handoff.md` is expected to record the constraint but is absent on this branch (it was authored on `feature/mix-pipeline-gui-19` and was not carried into `main` or this worktree).

## Proposed Fix / Validation Ideas

Required changes:

1. **Update `.claude/agents/orchestrator.md`** to:
   - Add a "Remediation Loop Protocol" section that states the allowed delegates during a remediation cycle are exactly `atomic-planner`, `atomic-executor`, and `feature-review`.
   - Explicitly prohibit direct invocation of typed-engineer subagents (`python-typed-engineer`, `typescript-engineer`, `csharp-typed-engineer`, `powershell-typed-engineer`) inside a remediation cycle. Workers are invoked by `atomic-executor` only.
   - Document the five required artifacts per cycle (`remediation-inputs`, `remediation-plan`, `code-review`, `feature-audit`, `policy-audit`) with the entry-ts / exit-ts naming contract.
   - Document the preflight sub-state with `preflight.outcome in {clear, changes_requested}` and `preflight.iterations` counters; specify that `changes_requested` routes back to `atomic-planner`, never to the orchestrator or to execution.
   - Document the scope-change rule: any new finding surfaced during execution must trigger a new cycle (a follow-up `remediation-inputs.<new-ts>.md`), not a re-prompt of the same worker.
   - Extend `step9` (CI monitoring) so a failed required check after the PR is open transitions to `remediation.cycle_N+1.inputs` and runs the full loop. Workflow-file changes specifically must be implemented through the loop and trigger the `modified-workflow-needs-green-run` rule.
   - Specify the exit gate: read the latest cycle's audit artifacts, compute `blocking_count == 0`, and only then mark the loop complete.

2. **Update `.claude/skills/remediation-handoff-atomic-planner/SKILL.md`** to:
   - Document the inputs -> plan -> preflight -> execute -> reaudit handoff in full, including the preflight revision sub-loop.
   - List the five required artifact filenames and timestamp rules.
   - Cite `.claude/skills/atomic-plan-contract/SKILL.md` as the schema for `remediation-plan.<ts>.md`.

3. **Extend the `orchestrator-state` schema** validated by `mcp__drm-copilot__validate_orchestration_artifacts` to require a `remediation_loop` object with the following shape when any cycle is in progress or complete:

   ```json
   "remediation_loop": {
     "current_cycle": <int>,
     "cycles": [
       {
         "entry_timestamp": "<ts>",
         "exit_timestamp": "<ts>|null",
         "inputs_path": "<path>",
         "plan_path": "<path>",
         "preflight": {
           "iterations": <int>,
           "final_status": "clear|changes_requested|pending"
         },
         "execution_status": "not_started|in_progress|complete|failed",
         "audit_paths": {
           "code_review": "<path>|null",
           "feature_audit": "<path>|null",
           "policy_audit": "<path>|null"
         },
         "blocking_count": <int|null>,
         "exit_condition_met": <bool|null>
       }
     ]
   }
   ```

   The `next_step` field must use cycle-aware names: `remediation.cycle_N.{plan,preflight,execute,reaudit,exit_check}` while in the loop. Malformed cycles must be rejected: missing `plan_path`, `exit_condition_met: true` with `blocking_count != 0`, execution-state set without a cleared preflight.

4. **Author and cite the orchestrator memory** at `.claude/agent-memory/orchestrator/remediation-loop-strict-handoff.md`; cite it from `.claude/agents/orchestrator.md` so future runs surface the constraint at startup.

5. **Produce a reference walkthrough** under `docs/` demonstrating a fully conformant cycle.

## Acceptance Criteria

- [x] `.claude/agents/orchestrator.md` contains a "Remediation Loop Protocol" section that names exactly `atomic-planner`, `atomic-executor`, and `feature-review` as the only delegates allowed during a remediation cycle, prohibits direct typed-engineer worker calls, lists the five required artifacts, and describes the preflight sub-state semantics (including `changes_requested` routing back to `atomic-planner`).
- [x] `.claude/agents/orchestrator.md` documents the scope-change rule (new findings during execution start a new cycle, not a worker re-prompt).
- [x] `.claude/agents/orchestrator.md` extends step 9 CI monitoring to enter the remediation loop on a failed required check after the PR is open, and explicitly says workflow-file changes are implemented through the loop.
- [x] `.claude/agents/orchestrator.md` specifies that the exit gate reads the latest audit's `blocking_count` and only then sets `exit_condition_met = true`.
- [x] `.claude/skills/remediation-handoff-atomic-planner/SKILL.md` documents the full handoff chain and the five required artifacts with the entry-ts / exit-ts timestamp rule.
- [x] The `orchestrator-state` schema validated by `mcp__drm-copilot__validate_orchestration_artifacts` requires the `remediation_loop` object shape documented in Proposed Fix item 3 whenever a remediation cycle has been started; a malformed cycle (missing `plan_path`, `exit_condition_met: true` with blocking findings, execution-state set without a cleared preflight) is rejected.
- [x] The orchestrator memory at `.claude/agent-memory/orchestrator/remediation-loop-strict-handoff.md` is cited from `.claude/agents/orchestrator.md` so it is surfaced at startup.
- [x] A reference walkthrough document (under `docs/` or the feature folder evidence) demonstrates a full conformant cycle: every artifact present, every state transition recorded, every validator pass.
- [x] Re-running the orchestrator on a sandbox feature folder with a seeded blocking finding produces a folder whose contents match the five-artifact contract and whose `orchestrator-state.json` passes the extended schema. (If a true sandbox harness is impractical, a fixture-based unit test that constructs and validates a sample state file is acceptable; document the choice.)
- [x] The retroactive PR #24 / issue #19 folder is not edited (the missing `remediation-plan.2026-05-28T12-17.md` is documented as a known historical gap; this bug fix prevents recurrence rather than backfilling history).

## Out of Scope

- Backfilling `remediation-plan.<ts>.md` files into historical feature folders.
- Changes to `atomic-planner`, `atomic-executor`, or `feature-review` agent definitions.
- Changes to worker subagent definitions.
- Reverting any commit on `feature/mix-pipeline-gui-19` or PR #24.
