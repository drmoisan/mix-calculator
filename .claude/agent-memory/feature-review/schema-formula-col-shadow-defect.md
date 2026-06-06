---
name: schema-formula-col-shadow-defect
description: col()-shadowing defect in src/schema_formula.py (issue #50) — RESOLVED in cycle 4 at HEAD a45a987 by binding whitelisted callables after the alias loop
metadata:
  type: project
---

RESOLVED (issue #50 cycle 4, HEAD `a45a987`, commit `cc5b282..a45a987`). Previously `tests/test_schema_formula.py::test_property_col_round_trips_values` failed (Hypothesis `{'col': 0.0}` -> `TypeError: '0.0' is not callable`) because a column literally named `col` shadowed the whitelisted `col()` helper.

**Why it happened:** `src/schema_formula.py._build_symtable` seeded `symtable["col"]` with the callable, then the alias loop `symtable[alias] = context[column]` overwrote it with the column scalar. Same risk for `sum`/`safe_div`.

**Fix applied:** `_build_symtable` now binds the column aliases FIRST (into an empty dict), then assigns the whitelisted callables `safe_div`/`sum`/`col` LAST (`src/schema_formula.py:301-314`). The `col` accessor closes over `context`, so `col("col")` still returns the column value. `validate()` needed no change (its `allowed_names` already covers the alias set). Regression test `test_evaluate_column_named_col_round_trips_via_col_callable` covers columns named `col`/`sum`/`safe_div`. Full suite green (942 passed), module 100% line/branch.

**How to apply:** This defect was NOT in the `main...HEAD` diff before cycle 4 (predated the feature branch). It is now closed; future issue-#50 audits should treat the formula engine as clean. If a new whitelisted function is added to `WHITELISTED_FUNCTIONS`, remember to also add a matching post-loop `symtable[...] =` rebind line, or it becomes shadowable again.
