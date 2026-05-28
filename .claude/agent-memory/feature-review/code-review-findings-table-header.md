---
name: code-review-findings-table-header
description: code-review validator requires exact 7-column findings table header (Severity File Location Finding Recommendation Rationale Evidence)
metadata:
  type: feedback
---

`validate_orchestration_artifacts` for `code-review` requires this exact
findings-table header string (any other column set fails):

`| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |`

**Why:** Verified 2026-05-28 on issue #20 R4 re-review — used a different
`| ID | Severity | Status | Location | Description |` table and got
`Code review missing the required findings table header.` The validator does a
literal substring check (`if table_header not in text`).

**How to apply:** Always emit the 7-column header verbatim. For PASS reviews
with no findings, use a single N/A row that fills each column with N/A or a
short justification, e.g. `| N/A | N/A | N/A | No code-quality issues identified. | ... |`.

See also [[policy-audit-required-structure]] and [[feature-audit-checkoff-heading-case]].
