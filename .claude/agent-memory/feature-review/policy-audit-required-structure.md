---
name: policy-audit-required-structure
description: policy-audit validator hard requirements - Appendix A heading, full TS/PS coverage checklist lines, and a numeric Python comparison line
metadata:
  type: feedback
---

`validate_orchestration_artifacts` for `policy-audit` enforces several structural
items that are easy to drop when trimming the template:

- The heading `## Appendix A: Test Inventory` must be present (not just Appendix B).
- The Coverage Evidence Checklist must keep all four lines verbatim even when those
  languages are out of scope: `TypeScript baseline coverage artifact:`,
  `TypeScript post-change coverage artifact:`, `PowerShell baseline coverage artifact:`,
  `PowerShell post-change coverage artifact:` (value `N/A - out of scope` is accepted).
- The Section 1.2.1 per-language comparison line for an in-scope language must contain
  a numeric baseline, a numeric post-change value, and an explicit `Disposition: PASS`
  (the validator looks for `Baseline:`/`Post-change:`/`Disposition:` tokens with numbers).
  Phrasing like "100% line / 100% branch" passes as long as numerals are present in
  the Baseline/Post-change segments.
- The validator's `_extract_policy_audit_comparison_lines` keeps reading `- ` bullets after
  the `### 1.2.1` heading until it hits the NEXT `### ` heading. Any later
  `- Python: ...` bullet (e.g. under `**Language-specific policies evaluated:**`)
  OVERWRITES the comparison-line entry and breaks validation. Fix: put a `### 1.2.2`
  heading immediately after the three comparison bullets so the scan terminates.

**Why:** Verified 2026-05-27 on issue #18 review — first write failed with all of the
above as missing-heading / missing-checklist-line / missing-numeric errors.

**How to apply:** Keep the template's Appendix A and the full coverage checklist;
for out-of-scope languages use `N/A - out of scope` rather than deleting the line.
See also [[feature-audit-checkoff-heading-case]].
