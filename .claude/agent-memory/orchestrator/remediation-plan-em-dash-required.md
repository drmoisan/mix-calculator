---
name: remediation-plan-em-dash-required
description: The MCP plan validator rejects `### Phase N (...) — <Title>` headings; only the canonical `### Phase N — <Title>` form passes; do not insert parenthetical sub-qualifiers in remediation-plan phase lines.
metadata:
  type: feedback
---

The `mcp__drm-copilot__validate_orchestration_artifacts` tool with `artifact_type: "plan"` rejects any phase heading that has tokens between `Phase N` and the em-dash, including `(continued)`. The exit message reads `phase heading must match \`### Phase N — <Title>\`` followed by `task appears before a canonical phase heading`.

**Why:** Encountered on the cycle-1 remediation plan for issue #25 (2026-05-28) where the planner introduced `### Phase 1 (continued) — AC#6 qa-gate documentation append` to separate a documentation-append task from the test-file authoring tasks under the same phase number. The validator failed at the offending line. The fix was to delete the `(continued)` sub-heading so the trailing task sat under the original `### Phase 1` heading.

**How to apply:** When delegating to `atomic-planner` for a remediation plan, instruct it to use only canonical `### Phase N — <Title>` headings with no parenthetical qualifiers; either fold related but distinct task groups under a single Phase title (renaming the title to cover both), or split into separate Phase numbers. After the planner returns, always run `mcp__drm-copilot__validate_orchestration_artifacts artifact_type: "plan"` before delegating to `atomic-executor` preflight; the planner's own self-check does not always catch this. Related: [[remediation-loop-strict-handoff]].
