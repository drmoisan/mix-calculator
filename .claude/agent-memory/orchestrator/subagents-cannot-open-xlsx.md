---
name: subagents-cannot-open-xlsx
description: Subagents cannot open binary .xlsx; the orchestrator must extract Excel logic via openpyxl and transcribe it into issue.md/spec
metadata:
  type: feedback
---

The delegated subagents (`atomic-planner`, `atomic-executor`, `feature-review`,
`task-researcher`) cannot open binary Excel workbooks — they lack a Python/Bash
path to `openpyxl`, and the Read tool does not parse `.xlsx`. This repo's work
frequently means replicating logic from the confidential
`LE v AOP Gross to Net Decomp.xlsx`.

**Why:** During issue #15 the planner/executor could not inspect the `NRR_Summary`
tab themselves; the orchestrator had to extract the formula grid first.

**How to apply:** When a feature replicates Excel-tab logic, the orchestrator does
the reconnaissance up front: use `env -u VIRTUAL_ENV poetry run python` with
`openpyxl` to extract formulas/labels/table ranges (formulas, labels, table and
column names are schema, not confidential — see [[derived-aggregates-are-confidential]]),
verify against the built `.db`, and transcribe the complete logic into `issue.md`
(or `spec.md`) as the authoritative, value-free source for downstream agents. Mask
literal numeric values. This reconnaissance is legitimate orchestrator change-budget
sizing, not "deep implementation."
