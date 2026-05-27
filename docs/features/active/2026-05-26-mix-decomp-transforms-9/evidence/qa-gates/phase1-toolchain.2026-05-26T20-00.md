# Phase 1 — Toolchain QA Gate (Issue #9)

Timestamp: 2026-05-26T20-00
Scope: `src/mix_transforms.py`, `src/_mix_transforms_helpers.py`, `src/load_skulu.py`, `tests/test_mix_transforms.py`, `tests/test_mix_pivots.py`, `tests/test_load_skulu.py`.

Commands run in order (single clean pass):

Command: `poetry run black .`
EXIT_CODE: 0
Output Summary: PASS. 25 files left unchanged.

Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: PASS. All checks passed; 0 errors; no suppressions added.

Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: PASS. 0 errors, 0 warnings, 0 informations (strict).

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary: PASS. 154 passed. Line coverage TOTAL 100%; branch coverage 100%. New modules: `mix_transforms.py` 100%/100%, `_mix_transforms_helpers.py` 100%/100%, `load_skulu.py` 100%/100%. No regression on changed lines.

File-size check: `mix_transforms.py` 210, `_mix_transforms_helpers.py` 379, `load_skulu.py` 143, `test_mix_transforms.py` 374, `test_mix_pivots.py` 165, `test_load_skulu.py` 172 — all <= 500.

Confidentiality: only fabricated values appear in new files (Acme Foods, Globex Market, Initech Grocers, SKU-001/002/003, Widget A/B, Category X/Y, PPG-1); US/Canada country values are not secret. No real customer/SKU/category values present.

Deviation note: `src/mix_transforms.py` reached 538 lines as initially written, exceeding the 500-line limit. Per the plan's `_load_aop_helpers.py` split guidance, the lower-level primitives were moved to `src/_mix_transforms_helpers.py` and re-exported from `src/mix_transforms.py`. The pivot tests were likewise split into `tests/test_mix_pivots.py` to keep that test file under 500 lines.
