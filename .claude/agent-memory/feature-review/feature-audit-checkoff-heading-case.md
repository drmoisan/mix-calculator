---
name: feature-audit-checkoff-heading-case
description: feature-audit validator requires '## Acceptance Criteria Check-off' (lowercase off) but the MCP template ships 'Check-Off'
metadata:
  type: feedback
---

The `validate_orchestration_artifacts` tool for `feature-audit` requires the exact
heading `## Acceptance Criteria Check-off` (lowercase "off"). The bundled MCP
`feature-audit-template` asset ships the heading as `## Acceptance Criteria Check-Off`
(capital "Off"), which fails validation.

**Why:** Verified 2026-05-27 on issue #18 review — writing the artifact verbatim from
the template produced `Feature audit missing required heading: ## Acceptance Criteria Check-off`.

**How to apply:** After copying the feature-audit template, rename the check-off
heading to lowercase `Check-off` before validating. The five required headings the
validator checks are: `## Scope and Baseline`, `## Acceptance Criteria Inventory`,
`## Acceptance Criteria Evaluation`, `## Summary`, `## Acceptance Criteria Check-off`.
See also [[policy-audit-required-structure]].
