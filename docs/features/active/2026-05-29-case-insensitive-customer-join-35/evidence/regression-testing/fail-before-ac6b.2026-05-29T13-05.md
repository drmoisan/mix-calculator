# Fail-before — AC6b (whitespace stripping)

Timestamp: 2026-05-29T13-05
Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py::test_build_aop_vs_le_casefold_strips_whitespace -v`
EXIT_CODE: 1

Output Summary:
- Test `test_build_aop_vs_le_casefold_strips_whitespace` FAILS before the production change.
- Failure mode: leading and trailing whitespace on the LE-side `Customer` (`'Winco '`, `' Winco'`) prevents the join; the result has three rows instead of two with a mix of `'Winco'`, `'Winco '`, and `' Winco'` displayed Customer values.
