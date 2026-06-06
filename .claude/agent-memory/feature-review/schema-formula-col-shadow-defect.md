---
name: schema-formula-col-shadow-defect
description: Latent col()-shadowing defect in src/schema_formula.py makes the pytest suite RED on issue #50; pre-existing, out of feature scope
metadata:
  type: project
---

`tests/test_schema_formula.py::test_property_col_round_trips_values` fails (Hypothesis falsifying example `{'col': 0.0}`) with `TypeError: '0.0' is not callable`. A column literally named `col` shadows the whitelisted `col()` helper.

**Why:** `src/schema_formula.py._build_symtable` (lines ~301-307) seeds `symtable["col"]` with the callable, then the alias loop `symtable[alias] = context[column]` overwrites it with the column scalar. Same risk exists for `sum`/`safe_div`.

**How to apply:** This defect is NOT in the `main...HEAD` diff for issue #50 (schema_formula.py untouched by the feature branch) — it predates the branch. When reviewing issue #50 cycles, classify the RED suite as a BLOCKING toolchain-not-green finding but attribute it to `src/schema_formula.py:301-307`, NOT to the cycle's changes. Fix path: bind whitelisted callables AFTER the alias loop, or skip aliasing names in `WHITELISTED_FUNCTIONS`. Scoped into cycle 4 via remediation-inputs.2026-06-05T23-23.md. The rest of the issue-#50 toolchain (Black/Ruff/Pyright) is green and coverage is ~98% line.
