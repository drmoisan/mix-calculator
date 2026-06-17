# Final QA — AOP/LE SchemaLoader Parity (P3-T6, CF1 cycle 3, #74)

Timestamp: 2026-06-17T13-40
Command: poetry run pytest "tests/test_default_schemas.py" -v
EXIT_CODE: 0

Output Summary: PASS. 25 passed in 0.22s. All `default_aop` and `default_le`
structural/parity tests pass unchanged with the AOP file reverted to on-disk 2.0. Zero output
regression: the on-load forward migration (version -> SCHEMA_FORMAT_VERSION, required = required
AND in_output) keeps the loaded AOP schema functionally identical to the 3.0-on-disk variant
because every AOP measure is in_output:true. The LE required-output assertions
(test_default_le_required_set_is_output_identity_under_3_0,
test_default_le_required_output_columns_accessor) pass and are unaltered.
