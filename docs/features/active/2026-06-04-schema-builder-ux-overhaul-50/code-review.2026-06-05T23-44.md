# Code Review: schema-builder-ux-overhaul (Issue #50) — Remediation Cycle 4 EXIT Reaudit

**Review Date:** 2026-06-05
**Timestamp:** 2026-06-05T23-44
**Branch:** `feature/schema-builder-ux-overhaul-50` | **Base:** `main` | **Head:** `a45a987` | **Merge-base:** `5e659f2`
**Work Mode:** full-feature
**Scope:** full branch diff `main...HEAD`; cycle-4 delta `cc5b282..a45a987`

## Executive Summary

Cycle 4 fixes a single latent formula-engine defect (C1). The change is confined to `src/schema_formula.py._build_symtable` and a new regression test in `tests/test_schema_formula.py`. The fix reorders symbol-table construction so column aliases are bound first and the whitelisted callables (`safe_div`, `sum`, `col`) are bound last, preventing a column whose identifier alias equals `col`/`sum`/`safe_div` from shadowing the helper. Because the `col` accessor closes over the row `context` rather than reading `symtable`, `col("col")` still resolves the exact-name column value, so the fix preserves both invariants (helper callable + exact-name access for every column name).

Code quality is consistent with prior cycles: the change is minimal, well-commented with intent (not narration), the docstring was updated to describe the bind-last ordering, and the regression test follows Arrange-Act-Assert with a descriptive docstring naming the defect. The full toolchain is green (Black/Ruff/Pyright EXIT 0; Pytest 942 passed, 0 failed). No suppressions were added, no file exceeds 500 lines, and no public API signature changed. `validate()` did not need to change because its `allowed_names` already covers the alias set.

No best-practice, correctness, or maintainability findings rise to FAIL or blocking-PARTIAL. The two informational notes below are non-blocking.

**Verdict: PASS (0 blocking findings).**

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|----------|------|----------|---------|----------------|-----------|----------|
| Info | src/schema_formula.py | 312-314 | Whitelisted callables are bound by explicit per-name assignment after the alias loop. A future addition to `WHITELISTED_FUNCTIONS` would require remembering to add a matching `symtable[...] =` line here. | Optional: derive the post-loop bindings from a single `{"safe_div": safe_div, "sum": formula_sum, "col": col}` mapping applied after the loop, to keep the whitelist and the rebind set in one place. | Reduces the chance of a future whitelist entry being shadowable again; not a current defect. | `src/schema_formula.py:312-314` |
| Info | tests/test_schema_formula.py | 249-269 | The regression test covers `col`, `sum`, and `safe_div` collisions in one test function (three asserts). | Optional: `pytest.mark.parametrize` over the three colliding names would isolate failures per name. | Single-behavior-per-test is better served by parametrization; current form is acceptable and readable. | `tests/test_schema_formula.py:249-269` |

## Detailed Observations

### C1 fix — correctness and design

The root cause was an ordering bug: the prior `_build_symtable` seeded the whitelisted `col` callable first, then the alias loop `symtable[alias] = context[column]` could overwrite `symtable["col"]` with a scalar when a source column was literally named `col`. The Hypothesis falsifying example `{'col': 0.0}` then made `col(name)` evaluate `0.0(...)`.

The fix is the minimal correct change: bind aliases first, bind callables last. It is preferable to the alternative (skipping/renaming colliding aliases) because it requires no change to `validate()` and keeps `col(name)` working for every column name via the closed-over `context`. The updated Returns docstring (lines 272-278) and the two inline comment blocks (lines 301-303, 307-311) document the ordering and the rationale without narrating individual lines, consistent with `self-explanatory-code-commenting.md`.

Coverage of the changed code is complete: `src/schema_formula.py` is 100% line / 100% branch post-change, and the three added production statements are exercised by both the now-passing property test and the new regression test.

### No regression in prior work

The cycle-4 delta (`cc5b282..a45a987`) touches only the formula module and its test file plus agent-memory docs. B1/B2 cycle-3 guards (`source_selection_presenter.py:237`, `workbook_reader.py:164-165`) and R1–R6 wiring (`app.py:327-349`, `app.py:430`, `schema_builder_dialog.py:98`, `_schema_open_helpers.py:159`) are present and unchanged at HEAD. AC-2 auto-selection remains proven by `test_ac2_full_match_through_build_application_auto_selects_and_enables`.

### Toolchain and hygiene

- Black `--check`: 222 files unchanged, EXIT 0.
- Ruff: all checks passed, EXIT 0.
- Pyright: 0 errors, EXIT 0.
- Pytest: 942 passed, 0 failed, EXIT 0.
- Suppression scan on the delta: `NO_SUPPRESSIONS_ADDED`.
- File sizes: `src/schema_formula.py` 315 lines, `tests/test_schema_formula.py` 379 lines; no `.py` file in the branch diff over 500 lines.

## Verdict

**PASS.** The C1 fix is minimal, correct, well-documented, and fully covered. No blocking findings; the two notes above are informational. The full toolchain is green and no prior work regressed.
