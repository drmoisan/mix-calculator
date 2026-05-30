# Fail-before — AC6e (five casings collapse)

Timestamp: 2026-05-29T13-05
Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py::test_build_aop_vs_le_five_casings_collapse_to_one -v`
EXIT_CODE: 1

Output Summary:
- Test `test_build_aop_vs_le_five_casings_collapse_to_one` FAILS before the production change.
- Failure mode: the pre-change pivot emits five rows (one per casing) instead of one collapsed row; the sum-aggregation assertion `AOP == 15.0` cannot be verified because each AOP value lives on its own row.
