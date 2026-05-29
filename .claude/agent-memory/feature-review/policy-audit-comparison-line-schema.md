---
name: policy-audit-comparison-line-schema
description: Per-language coverage comparison bullets under `### 1.2.1 Per-Language Coverage Comparison` need exact `Baseline:` `Post-change:` `Change:` `Disposition:` `Evidence:` labels (and `New/changed-code coverage:` when a numeric value is in the row)
metadata:
  type: feedback
---

The `validate_policy_audit_artifact.py` validator (in `drm-copilot/scripts/dev_tools/`) parses bullets inside the `### 1.2.1 Per-Language Coverage Comparison` heading with `line[2:].partition(":")` and keys them by the lowercase first token. Each bullet must additionally contain these labels with a numeric percentage immediately after:

- `Baseline:` followed by `\d+(\.\d+)?%`
- `Post-change:` followed by `\d+(\.\d+)?%`
- `Change:` (any text — required keyword)
- `Disposition:` followed by `PASS|FAIL|N/A|INCOMPLETE|BLOCKED`
- `New/changed-code coverage:` followed by `\d+(\.\d+)?%` (only when the coverage-metrics table row's `New Code Coverage` column is non-N/A)
- `Evidence:` (any text — required keyword)

**Why:** the validator silently rejects bullets without these exact-labelled fragments and emits messages like "Policy audit comparison line missing explicit change text for Python." Discovered while validating the v2 feature-review for mix-pipeline-gui (2026-05-28).

**How to apply:** when authoring `policy-audit.*.md`, format each language bullet as `- <Language>: Baseline: <X>% line / <Y>% branch (...). Post-change: <X>% line / <Y>% branch (...). Change: <text>. New/changed-code coverage: <Z>% line / <W>% branch. Disposition: PASS. Evidence: <paths>.`. Use `- TypeScript: Baseline: N/A. Post-change: N/A. Change: N/A. Disposition: N/A. Evidence: N/A — no TypeScript files changed on this branch.` for unused languages.
