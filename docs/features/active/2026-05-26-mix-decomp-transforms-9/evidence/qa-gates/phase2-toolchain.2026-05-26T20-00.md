# Phase 2 — Toolchain QA Gate (Issue #9)

Timestamp: 2026-05-26T20-00
Scope: `src/mix_lookups.py`, `tests/test_mix_lookups.py`.

Command: `poetry run black .`
EXIT_CODE: 0
Output Summary: PASS. 27 files left unchanged.

Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: PASS. All checks passed; 0 errors; no suppressions.

Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: PASS. 0 errors, 0 warnings, 0 informations (strict).

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary: PASS. 163 passed. Line coverage TOTAL 100%; branch coverage 100%. `mix_lookups.py` 100%/100%. No regression on changed lines.

File-size check: `mix_lookups.py` 220, `test_mix_lookups.py` 360 — both <= 500.

Confidentiality: only fabricated values appear (Acme Foods, Globex Market, Master Group, Other Master, SKU-001/002/003, Widget A, Category X, PPG-1); US/Canada not secret.

Implementation notes: `build_aop_vs_le` applies the `Attribute != "Cases"` filter and `Diff = LE - AOP`, then reuses `classify_table` from `src.mix_transforms` (no re-implementation). `build_mix_base` casts `SKU #` to `str` before the left-join on `SKU # == SKU` and excludes `Classification == "inactive"`.
