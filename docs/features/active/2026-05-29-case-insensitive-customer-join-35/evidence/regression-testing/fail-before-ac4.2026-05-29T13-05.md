# Fail-before — AC4 (build_customer_lu strips whitespace)

Timestamp: 2026-05-29T13-05
Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py::test_build_customer_lu_strips_whitespace -v`
EXIT_CODE: 1

Output Summary:
- Test `test_build_customer_lu_strips_whitespace` FAILS before the production change.
- Failure mode: `build_customer_lu` deduplicates on the raw Customer string, so `'Winco '` and `'Winco'` remain as two distinct rows (`len(result) == 2`); the assertion that a single row remains fails.
