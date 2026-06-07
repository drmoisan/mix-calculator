---
name: policy-audit-section7-row-label-parser
description: policy-audit validator misreads certain section-7 "Code Quality Checks" row labels as per-language coverage rows; keep cycle-1 phrasing
metadata:
  type: feedback
---

The THIS-repo policy-audit validator (`validate_orchestration_artifacts --artifact-type policy-audit`) scans `## 7. Code Quality Checks` table row labels and will treat an unrecognized label as a per-language coverage row, then demand numeric Baseline/Post-change/new-code coverage + a `### 1.2.1` comparison line for it.

**Why:** On issue #50 cycle-2 exit, the row label `Suppression scan, cycle-2 added lines` triggered four false "missing numeric coverage for Suppression scan" errors. Renaming back to the cycle-1 form `Suppression scan (added lines)` (parenthetical, no extra comma-delimited words) cleared it.

**How to apply:** In section 7 of a policy-audit, keep row labels short and reuse the exact cycle-1 wording: `Confidentiality masking scan`, `Suppression scan (added lines)`, `Workflow change scan`. Avoid comma-separated qualifiers in the label cell; put cycle/commit detail in the Command or Result cell instead. See [[policy-audit-validator-uses-full-template]] and [[policy-audit-comparison-line-schema]].
