# Fail-before — AC5 (Winco/WINCO merge)

Timestamp: 2026-05-29T13-05
Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py::test_build_aop_vs_le_casefold_winco_merges -v`
EXIT_CODE: 1

Output Summary:
- Test `test_build_aop_vs_le_casefold_winco_merges` FAILS before the production change.
- Failure mode: the pre-change pivot keys on `Customer` literally, so AOP `'Winco'` and LE `'WINCO'` produce two separate rows per attribute. The actual `Attribute` list contains 6 rows instead of the expected 4.
- AssertionError: `attributes == sorted([...])` mismatch; LE-side `Off Invoice $` and `Non-Trade $` rows appear under `WINCO` and are not collapsed into the AOP-side `Winco` rows.
