# Acceptance-Criteria Mapping — Issue #2

Timestamp: 2026-05-25T21-02
Source of criteria: `docs/features/active/2026-05-25-etl-le-topline-input-2/issue.md`
(`## Acceptance Criteria` and `## Test Conditions` sections)
Test files: `tests/test_normalize_le.py`, `tests/test_normalize_le_io.py`
Shared fixtures: `tests/le_fixtures.py`

## Acceptance Criteria

| # | Criterion (abbreviated) | Verifying test(s) |
|---|---|---|
| AC1 | CLI with listed defaults; `--output` required; SQLite is the only sink | `test_main_end_to_end_success`, `test_main_missing_output_exits_nonzero`, `test_main_custom_sheet_and_table_name` (io); module has no Excel/CSV output path (verified by `main` orchestration in `src/normalize_le.py`) |
| AC2 | `header=2`; drop blank `Customer`; validate 26 source columns; clear error naming missing/extra | `test_load_source_header_and_columns`, `test_load_source_drops_blank_customer_rows`, `test_validate_schema_missing_column`, `test_validate_schema_extra_column`, `test_validate_schema_out_of_order_column`, `test_validate_schema_exact_match_returns_none` |
| AC3 | `KEY` rebuilt from `Customer + coerce_sku(SKU #) + Type`; whole-number SKUs as integer strings; non-numeric codes verbatim | `test_coerce_sku_branches`, `test_coerce_sku_integer_property`, `test_rebuild_key_whole_number_sku`, `test_rebuild_key_preserves_non_numeric_sku`, `test_rebuild_key_property`, `test_load_source_rebuilds_key_ignoring_loaded_value`, `test_normalize_non_numeric_sku_preserved` |
| AC4 | 26 columns in target order; one row per unique KEY; first-appearance order; `YTD/YTG` absent; derived `YTG` after `Q4` before `Super Category` | `test_normalize_column_order_and_no_ytd_ytg`, `test_normalize_first_appearance_order_preserved`, `test_normalize_property_row_count_and_sums` |
| AC5 | Text columns from first source row per KEY; `Jan..Dec`/`FY`/`Q1..Q4` summed (blanks as 0) | `test_normalize_two_row_pair_sums_numeric`, `test_normalize_three_rows_sum_and_nan_as_zero`, `test_normalize_singleton_key_passthrough`, `test_normalize_property_row_count_and_sums` |
| AC6 | `YTG = sum(May..Dec)` computed on the output row | `test_compute_ytg_sums_may_through_dec`, `test_compute_ytg_property`, `test_normalize_two_row_pair_sums_numeric` (YTG via FY/months) |
| AC7 | `Super Category` and `PPG` both from source `PPG`; identical per row (as-built quirk) | `test_normalize_super_category_ppg_quirk` |
| AC8 | Validation: output-row-count == unique keys; per-column tie-outs within `1e-6`; `FY == sum(months)`; failures raise and exit non-zero | `test_validate_tieouts_pass_path`, `test_validate_tieouts_row_count_mismatch_raises`, `test_validate_tieouts_column_total_perturbation_raises`, `test_validate_tieouts_fy_mismatch_raises`, `test_validate_tieouts_property_roundtrip`, `test_main_schema_mismatch_exits_nonzero` |
| AC9 | stdout prints source rows, unique keys, output rows, per-month/FY/quarter tie-outs, and first/middle/last rows | `test_main_end_to_end_success` (asserts all summary lines), `test_print_summary_empty_output_omits_row_samples` |
| AC10 | Persist via `to_sql(..., if_exists="replace", index=False)`; existing table dropped-and-rewritten; index not persisted; 26 columns in target order; one row per unique KEY | `test_write_sqlite_roundtrip_columns_and_rows`, `test_write_sqlite_replace_if_exists_no_duplication`, `test_main_end_to_end_success`, `test_main_custom_sheet_and_table_name` |

## Test Conditions

| Condition (abbreviated) | Verifying test(s) |
|---|---|
| `coerce_sku` (int, np.integer, integer-valued float, non-integer float, NaN, string code) | `test_coerce_sku_branches`, `test_coerce_sku_integer_property` |
| KEY rebuild | `test_rebuild_key_*`, `test_load_source_rebuilds_key_ignoring_loaded_value` |
| Schema validation (missing/extra/out-of-order) | `test_validate_schema_missing_column`, `test_validate_schema_extra_column`, `test_validate_schema_out_of_order_column` |
| normalize aggregation (singleton, 2-row YTD+YTG pair, 3+ rows) | `test_normalize_singleton_key_passthrough`, `test_normalize_two_row_pair_sums_numeric`, `test_normalize_three_rows_sum_and_nan_as_zero` |
| `YTG` derivation | `test_compute_ytg_sums_may_through_dec`, `test_compute_ytg_property` |
| Super Category/PPG quirk | `test_normalize_super_category_ppg_quirk` |
| Tie-out validation pass and failure paths | `test_validate_tieouts_pass_path`, `test_validate_tieouts_row_count_mismatch_raises`, `test_validate_tieouts_column_total_perturbation_raises`, `test_validate_tieouts_fy_mismatch_raises` |
| Trailing blank `Customer` rows dropped | `test_load_source_drops_blank_customer_rows` |
| KEY appearing once passes through | `test_normalize_singleton_key_passthrough` |
| KEY appearing 3+ times sums all | `test_normalize_three_rows_sum_and_nan_as_zero` |
| Non-numeric SKU codes preserved | `test_normalize_non_numeric_sku_preserved`, `test_coerce_sku_branches` |
| NaN month cells treated as 0 | `test_normalize_three_rows_sum_and_nan_as_zero` |
| No alphabetical/KEY sorting | `test_normalize_first_appearance_order_preserved` |
| Round-trip persist to SQLite and read back (columns/order/row count) | `test_write_sqlite_roundtrip_columns_and_rows`, `test_main_end_to_end_success` |
| Re-run replaces existing table (no duplication) | `test_write_sqlite_replace_if_exists_no_duplication` |
| Schema-mismatch input -> non-zero exit + descriptive message | `test_main_schema_mismatch_exits_nonzero` |
| Missing `--output` -> non-zero exit | `test_main_missing_output_exits_nonzero` |
| CLI invocation with `--output`; custom `--source-sheet` and `--table-name` | `test_main_end_to_end_success`, `test_main_custom_sheet_and_table_name` |

## Outcome

Every acceptance criterion and every test condition maps to at least one named, passing test. No unmapped criterion remains. Outcome: PASS.
