# QA Gate — Key Test After Revert (AC-R2 / P2-T2, CF1 cycle 3, #74)

Timestamp: 2026-06-17T13-40
Command: poetry run pytest "tests/test_default_schemas.py::test_bundled_defaults_are_current_format_with_structured_key_parts" -v
EXIT_CODE: 0

Output Summary: PASSED (1 passed in 0.21s). With `default_aop.schema.json` reverted to on-disk
2.0, the test still passes: it asserts `schema.version == SCHEMA_FORMAT_VERSION` on the loaded
schema, which the on-load forward migration sets to 3.0 in memory. AC-R2 satisfied.
