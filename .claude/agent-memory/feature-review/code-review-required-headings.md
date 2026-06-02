---
name: code-review-required-headings
description: code-review validator requires literal headings ## Executive Summary and ## Findings Table; feature-audit requires ## Acceptance Criteria Inventory and ## Acceptance Criteria Evaluation
metadata:
  type: feedback
---

The `validate_orchestration_artifacts` schema check enforces exact section headings.

- **code-review**: requires literal `## Executive Summary` and `## Findings Table` headings. A 7-column findings table alone (see [[code-review-findings-table-header]]) is not enough; the heading text must be `## Findings Table`, not `## Findings`.
- **feature-audit**: requires `## Acceptance Criteria Inventory` and `## Acceptance Criteria Evaluation` headings (in addition to `## Acceptance Criteria Check-off`, lowercase off — see [[feature-audit-checkoff-heading-case]]). A heading like `## Remediation Acceptance Criteria Evaluation` does NOT satisfy the `## Acceptance Criteria Evaluation` requirement; keep the exact heading and add a subsection beneath it.

**Why:** On the #48 remediation cycle exit (2026-06-01T23-52), both artifacts failed schema validation on first write because I used `## Findings` and `## Remediation Acceptance Criteria Evaluation`. policy-audit passed first try.

**How to apply:** When authoring code-review and feature-audit artifacts, use these exact headings up front; validate all three artifacts before reporting paths.
