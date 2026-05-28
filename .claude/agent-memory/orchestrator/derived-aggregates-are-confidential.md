---
name: derived-aggregates-are-confidential
description: Derived financial aggregates from the source workbook are confidential too; never write them to committed files, describe qualitatively
metadata:
  type: feedback
---

The repo confidentiality policy covers not just raw source values, SKU
descriptions, and category names, but also **derived aggregate figures** computed
from the confidential workbook (for example mix totals, net-revenue sums, rate
impacts). These must never appear in any version-controlled file: production code,
tests, docs, evidence under `docs/features/**`, or agent-memory.

**Why:** During issue #15 the executor recorded the actual computed mix totals
(e.g. exact Category/Customer mix figures) into its agent-memory dossier, which is
committed and shared via version control. The orchestrator had to sanitize it to
qualitative terms ("differ by orders of magnitude and sign") before committing.

**How to apply:** When recording findings, comparisons, or evidence about real
runs, describe magnitudes/relationships qualitatively and cite the gitignored
source (the workbook or `mix.db`) for the numbers. Schema is fine to record:
table names, column names, formula labels, and `US`/`Canada` country values are
not secret. Before any `git add -A`, scan staged content for stray numeric
figures. Related: [[subagents-cannot-open-xlsx]].
