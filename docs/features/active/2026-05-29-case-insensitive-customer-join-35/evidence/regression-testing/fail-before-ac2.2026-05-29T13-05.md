# Fail-before — AC2 (build_aop_norm / build_le_norm strip whitespace)

Timestamp: 2026-05-29T13-05
Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py::test_build_aop_norm_strips_customer_whitespace tests/test_mix_lookups.py::test_build_le_norm_strips_customer_whitespace -v`
EXIT_CODE: 1

Output Summary:
- Both tests FAIL before the production change.
- `test_build_aop_norm_strips_customer_whitespace`: `result["Customer"].tolist()` returns `['Winco ']` (trailing whitespace preserved) instead of `['Winco']`.
- `test_build_le_norm_strips_customer_whitespace`: `result["Customer"].tolist()` returns `[' Winco']` (leading whitespace preserved) instead of `['Winco']`.
