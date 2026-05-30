# Fail-before — AC6c (AOP-side casing wins)

Timestamp: 2026-05-29T13-05
Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py::test_build_aop_vs_le_display_aop_casing_wins -v`
EXIT_CODE: 1

Output Summary:
- Test `test_build_aop_vs_le_display_aop_casing_wins` FAILS before the production change.
- Failure mode: the pre-change pivot keys literally on `Customer`, producing two rows (one `'Winco'`, one `'WINCO'`) instead of one. The assertion that the single displayed `Customer` is `'Winco'` cannot hold because two rows are emitted.
