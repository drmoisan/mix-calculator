# QA Gate — AOP Test Reconciliation (R2 / P2-T1, CF1 cycle 3, #74)

Timestamp: 2026-06-17T13-40
File inspected: tests/test_default_schemas.py

## AOP-related tests inspected
- test_aop_columns_and_order_match_canonical (line 126)
- test_aop_key_dedup_and_no_derived (line 135)
- test_aop_sentinel_clean_labels (line 148)
- test_aop_fill_rules_cover_ytd_quarters_and_ytg (line 158)
- test_aop_fill_rules_empty_and_header_row_two_round_trips (line 172)
- test_bundled_defaults_are_current_format_with_structured_key_parts (line 396; covers both default_le and default_aop)
- test_default_schema_registry_lists_bundled (line ~382; lists default_aop)
- parametrized round-trip test (line ~385; includes default_aop)

## Finding
No on-disk-3.0 or AOP-required-false assertion present.

Details:
- The version check in `test_bundled_defaults_are_current_format_with_structured_key_parts`
  asserts `schema.version == SCHEMA_FORMAT_VERSION` on the LOADED schema (via `_load_bundled`
  -> `schema_from_json`), which applies the on-load forward migration. It does NOT read the
  raw file's `"version"` field, so it holds with the bundled file at on-disk 2.0.
- Every `required is False` assertion in the module is scoped to `default_le`
  (test_le_drops_ytd_ytg_source_column line 259; test_default_le_required_set_is_output_identity_under_3_0
  lines 439-461; test_default_le_required_output_columns_accessor lines 465-480). No AOP test
  asserts AOP measures are `required: false`.

## Constraints honored
- No LE assertion altered.
- AOP `required_output_columns()` accessor test NOT added (deferred to CF2).

## Result
No change required. tests/test_default_schemas.py is unchanged.
