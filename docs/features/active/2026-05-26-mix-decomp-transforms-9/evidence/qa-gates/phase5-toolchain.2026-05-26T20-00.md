# Phase 5 — Toolchain QA Gate (Issue #9)

Timestamp: 2026-05-26T20-00
Scope: `src/mix_q1.py`, `tests/test_mix_q1.py`.

Command: `poetry run black .`
EXIT_CODE: 0
Output Summary: PASS. 32 files left unchanged after reformat pass.

Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: PASS. All checks passed; 0 errors; no suppressions.

Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: PASS. 0 errors, 0 warnings, 0 informations (strict).

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary: PASS. 181 passed. Line coverage TOTAL 100%; branch coverage 100%. `mix_q1.py` 100%/100%. No regression on changed lines.

File-size check: `mix_q1.py` 91, `test_mix_q1.py` 120 — both <= 500.

Confidentiality: only fabricated values appear (Acme Foods, SKU-001, Widget A).

Implementation notes: `build_q1_results_by_sku` derives `Q1 = Jan + Feb + Mar`, pivots `GtN Mapping` on `Q1`, computes the pre-negation `Net Rev = Gross Sales - Off Invoice - Non-Trade - Trade`, renames to `$` names, and reuses `calc_ratios` from `src.mix_transforms`.
