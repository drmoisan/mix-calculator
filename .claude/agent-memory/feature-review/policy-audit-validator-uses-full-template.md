---
name: policy-audit-validator-uses-full-template
description: The mix-calculator policy-audit validator requires the FULL bundled template heading set (## Executive Summary + ## 1..## 7), not the trimmed Appendix-A/1.2.1 structure
metadata:
  type: feedback
---

`validate_orchestration_artifacts` for `policy-audit` in THIS repo
(mix-calculator) enforces the full bundled template heading set, not the trimmed
structure described in [[policy-audit-required-structure]] (that note was for a
different/older validator and produced a first-write failure on issue #50).

Required headings (literal, all must be present):
- `## Executive Summary`
- `## 1. General Unit Test Policy Compliance`
- `## 2. General Code Change Policy Compliance`
- `## 3. Language-Specific Code Change Policy Compliance`
- `## 4. Language-Specific Unit Test Policy Compliance`
- `## 5. Test Coverage Detail`
- `## 6. Test Execution Metrics`
- `## 7. Code Quality Checks`

The `### 1.2.1 Per-Language Coverage Comparison` bullets and the
`### Coverage Evidence Checklist` four TS/PS lines are STILL required within that
structure (see [[policy-audit-comparison-line-schema]]). The fastest path is to
resolve the bundled template via the MCP `resolve_policy_audit_template_asset`
(asset `template`), then fill it in and delete the instruction block.

**Why:** On issue #50 review (2026-06-05) my first policy-audit used a custom
heading set and failed with eight "missing required heading" errors for exactly
the headings above. code-review and feature-audit validated first try.

**How to apply:** For mix-calculator, author policy-audit against the full
template heading set. Validate all three artifacts before reporting paths.
