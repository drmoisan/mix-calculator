# Fail-before — AC6a (three casings collapse)

Timestamp: 2026-05-29T13-05
Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py::test_build_aop_vs_le_casefold_collapses_three_casings -v`
EXIT_CODE: 1

Output Summary:
- Test `test_build_aop_vs_le_casefold_collapses_three_casings` FAILS before the production change.
- Failure mode: the pre-change pivot produces three separate rows (one per casing) instead of one collapsed row; `len(result) == 1` is false.
