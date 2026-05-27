# Phase 3 — Toolchain QA Gate (Issue #9)

Timestamp: 2026-05-26T20-00
Scope: `src/mix_rate_impacts.py`, `tests/test_mix_rate_impacts.py`.

Command: `poetry run black .`
EXIT_CODE: 0
Output Summary: PASS. 29 files left unchanged.

Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: PASS. All checks passed; 0 errors; no suppressions.

Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: PASS. 0 errors, 0 warnings, 0 informations (strict).

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary: PASS. 167 passed. Line coverage TOTAL 100%; branch coverage 100%. `mix_rate_impacts.py` 100%/100%. No regression on changed lines.

File-size check: `mix_rate_impacts.py` 123, `test_mix_rate_impacts.py` 159 — both <= 500.

Confidentiality: only fabricated values appear (Acme Foods, Globex Market, SKU-001/002, Widget A, Category X). The six derived impact columns match the hand-computed expected values within 1e-9; `stack_pivot` is reused from `src.mix_transforms`.
