# Phase 4 — Toolchain QA Gate (Issue #9)

Timestamp: 2026-05-26T20-00
Scope: `src/mix_rollups.py`, `src/_mix_rollups_helpers.py`, `tests/test_mix_rollups.py`.

Command: `poetry run black .`
EXIT_CODE: 0
Output Summary: PASS. 32 files left unchanged.

Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: PASS. All checks passed; 0 errors; no suppressions.

Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: PASS. 0 errors, 0 warnings, 0 informations (strict).

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary: PASS. 176 passed. Line coverage TOTAL 100%; branch coverage 100%. `mix_rollups.py` 100%/100%, `_mix_rollups_helpers.py` 100%/100%. No regression on changed lines.

File-size check: `mix_rollups.py` 317, `_mix_rollups_helpers.py` 224, `test_mix_rollups.py` 338 — all <= 500.

Confidentiality: only fabricated values appear (Acme Foods, Globex Market, SKU-001/002/003, Widget *, Category X/Y, US/Canada).

Implementation notes:
- The nine rollup functions are exposed; the shared reshape body lives in `src/_mix_rollups_helpers.py` (`build_mix_stage`, `group_net_price_impact`, `join_rollup_mix`, `unstack_to_long`) per the `_load_aop_helpers.py` split pattern.
- `build_mix_rollup_4` returns the scalar `float` sum of `mix_3_customer["Calc Net Price Impact"]`.
- `build_mix_3_customer` names its derived column `Customer Mix` (documented deviation from the M-source "Category Mix") and applies `fill_zero_with_avg`; `build_mix_4_country` subtracts the scalar `mix_rollup_4` as a broadcast to produce `Country Mix`; `build_mix_2_category` produces `Category Mix`.
- The Mix-N chain reverses each prior layer's wide stacked form to long via `unstack_to_long` before regrouping at the coarser key.
- `calc_ratios` was made tolerant of absent measure columns (treated as zero) so the later rollup stages, which carry only `Lbs`/`Net Rev Per Lb`/`Net-Revenue $`, can run `add_ratios` without a KeyError while keeping `Net Rev Per Lb` exact. Documented deviation from the strict-all-columns contract.
- Rollup tie-out verified: the customer-layer net price impact sum equals the scalar `mix_rollup_4` within 1e-9.
