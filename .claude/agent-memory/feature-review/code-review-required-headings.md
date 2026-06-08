---
name: code-review-required-headings
description: code-review validator requires literal headings ## Executive Summary and ## Findings Table; feature-audit requires ## Acceptance Criteria Inventory and ## Acceptance Criteria Evaluation
metadata:
  type: feedback
---

The `validate_orchestration_artifacts` schema check enforces exact section headings.

- **code-review**: requires literal `## Executive Summary` and `## Findings Table` headings. A 7-column findings table alone (see [[code-review-findings-table-header]]) is not enough; the heading text must be `## Findings Table`, not `## Findings`.
- **feature-audit**: requires `## Acceptance Criteria Inventory`, `## Acceptance Criteria Evaluation`, `## Scope and Baseline`, and `## Summary` headings (in addition to `## Acceptance Criteria Check-off`, lowercase off — see [[feature-audit-checkoff-heading-case]]). A heading like `## Remediation Acceptance Criteria Evaluation` does NOT satisfy the `## Acceptance Criteria Evaluation` requirement; keep the exact heading and add a subsection beneath it. A final `## Verdict` does NOT satisfy `## Summary`; use `## Summary`.
- **policy-audit** (full bundled template, see [[policy-audit-validator-uses-full-template]]): beyond `## Executive Summary` + `## 1`..`## 7`, the validator ALSO requires `## Appendix A: Test Inventory` and `## Appendix B: Toolchain Commands Reference`. The bundled template ships these; do not delete them when filling it in.

**Why:** On the #48 remediation cycle exit (2026-06-01T23-52), both artifacts failed schema validation on first write because I used `## Findings` and `## Remediation Acceptance Criteria Evaluation`. On issue #58 (2026-06-08T17-39), feature-audit failed first write missing `## Scope and Baseline` + `## Summary`, and policy-audit failed missing the two Appendix headings.

**How to apply:** When authoring code-review and feature-audit artifacts, use these exact headings up front; validate all three artifacts before reporting paths.
