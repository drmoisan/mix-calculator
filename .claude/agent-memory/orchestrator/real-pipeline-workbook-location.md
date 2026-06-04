---
name: real-pipeline-workbook-location
description: The user's real pipeline workbook (gitignored) lives at artifacts/LE_NEW v LE_ORIG Gross to Net Decomp.xlsx — use it for end-to-end loader checks
metadata:
  type: reference
---

The user's real source workbook is `artifacts/LE_NEW v LE_ORIG Gross to Net
Decomp.xlsx` (gitignored — confirmed never staged). Relevant sheets: `AOP1`,
`SKU_LU`, `LE-8 + 4` / `LE84Data`. The `AOP1` sheet has its header at Excel row 3
(pandas `header=2`) with the canonical AOP columns.

**How to use:** When a change touches the loaders or validation, the orchestrator
can run the real loader against this file (subagents cannot open `.xlsx`) to
verify behavior end-to-end, e.g.
`load_aop.load_aop(path, sheet="AOP1", key_mismatch="trust")`. Report only
qualitative results / counts; never commit or surface confidential figures (see
[[derived-aggregates-are-confidential]]). The file shape is the "8+4" partial-year
convention described in [[aop-partial-year-8plus4-convention]].
