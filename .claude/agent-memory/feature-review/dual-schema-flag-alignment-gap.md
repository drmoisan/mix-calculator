---
name: dual-schema-flag-alignment-gap
description: When a flag-semantics change touches both bundled schemas (default_le + default_aop), verify BOTH were updated; executors tend to fully edit LE and only version-bump AOP
metadata:
  type: feedback
---

When an epic-#74-style change redefines a schema flag's meaning (e.g. `required`
3.0 = "required OUTPUT identity column"), independently confirm BOTH bundled
schemas were aligned, not just `default_le`.

**Why:** On the CF1 review (issue #74, branch
`refactor/etl-required-output-model-semantics-74`, head `02e1579`,
merge-base `0a47fef`), `default_le.schema.json` was fully edited (months/FY/
quarters set `required: false`, `Super Category` too) but
`default_aop.schema.json` only got its `version` bumped `2.0 -> 3.0` — its
measure columns `Jan`–`Dec`/`YTD`/`Q1`–`Q4` stayed `required: true` (old
input-presence meaning). The spec Scope explicitly said "align `required` flags
to the new meaning" for AOP. The DoD checklist enumerated only LE columns, and
output parity held for both, so every quality gate passed and the DoD looked
green; the gap was only visible by dumping the AOP file's flags directly. Rated
Major / material PARTIAL (non-blocking: zero output regression).

**How to apply:** For any change that names two or more bundled schemas, dump
each file's flags (`python -c "import json; ..."`), not just the one the DoD
spells out column-by-column. A passing parity test proves output is unchanged;
it does NOT prove the input-side flag semantics were applied. Cross-check spec
Scope bullets per-file against the actual diff: a file that appears in the diff
with only a version-line change is a red flag when the spec asked for flag
alignment. Related: [[tested-but-unwired-seam-pattern]] (coverage/parity green
is not evidence the intended change was actually made).

**Resolution (cycle 3, head `1182cad`, 2026-06-17):** the CF1 AOP gap was NOT
fixed by aligning AOP flags — it was descoped. Remediation established that
flipping AOP measures to `required: false` reorders SchemaLoader output on the
`none`-dedup path because `_schema_loader_helpers.py` couples emitted column
ORDER and which-columns-to-keep to `required` (`resolve_and_rename` builds
`required_expected` and the `columns_to_keep`/`selection` order from
`column.required`). Decoupling needs a CF2 loader change + a new located-by-name/
presence-optional schema-model signal. So `spec.md` rescoped AC #3 to `default_le`
only, `initiative.md` moved AOP minimization to CF2, and the cycle-3 remediation
REVERTED the CF1 AOP version bump so CF1 makes zero AOP schema-file change
(`git diff main -- src/schemas/default_aop.schema.json` is empty). The on-load
migration `required = required AND in_output` keeps loaded AOP identical (every
AOP measure is `in_output: true`). CF1 re-audit verdict: FULLY COMPLIANT / Go.
When reviewing CF2, expect the AOP minimization + loader decouple to land there;
re-check the AOP file flags THEN.
