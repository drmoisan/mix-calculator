# Feature Audit — etl-le-topline-input (#2)

- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Work Mode: full-feature
- Audit timestamp: 2026-05-25T21-11

## Scope and Baseline

- Base branch (resolved): `main`
- Merge-base SHA: `2d86e836f89f43df011ed7528ac8decbd82cd761`
- Head SHA: `74743671ae26e42e74e039fa5f33e90d2e4b3294`
- Range audited: `2d86e836f89f43df011ed7528ac8decbd82cd761..74743671ae26e42e74e039fa5f33e90d2e4b3294`
- Scope: full branch diff vs base (not a plan/task subset).
- AC sources (full-feature): `user-story.md` `## Acceptance Criteria` and `spec.md`
  `## Definition of Done`. The same nine acceptance-criteria items also appear in
  `issue.md` `## Acceptance Criteria` and are tracked there for consistency.

## Acceptance Criteria Inventory

User-story / spec acceptance criteria (AC1–AC9):

- AC1: `src/normalize_le.py` exposes the documented CLI with listed defaults; `--output`
  required and must be a SQLite path; SQLite is the only output sink.
- AC2: Source load uses `header=2`, drops blank-`Customer` rows, validates the 26 source
  columns A..Z in exact order, failing with a clear error naming missing/extra columns.
- AC3: `KEY` rebuilt from `Customer + coerce_sku(SKU #) + Type`; whole-number SKUs render
  as integer strings; non-numeric SKU codes preserved verbatim.
- AC4: Output has 26 columns A..Z in target order, one row per unique KEY, in
  first-appearance order; `YTD/YTG` absent; derived `YTG` after `Q4`, before
  `Super Category`.
- AC5: Text columns taken from first source row per KEY; `Jan..Dec`, `FY`, `Q1..Q4`
  summed across rows sharing a KEY (blanks treated as 0).
- AC6: `YTG = sum(May..Dec)` computed on the output row, not from source.
- AC7: `Super Category` and `PPG` both populated from source `PPG` (as-built quirk),
  identical per row.
- AC8: Validation enforces output-row-count == unique keys, per-column source/output
  tie-outs within `1e-6`, and `FY == sum(months)` per row; failures raise and exit
  non-zero.
- AC9: stdout prints source rows, unique keys, output rows, per-month/FY/quarter
  tie-outs, and first/middle/last output rows.
- AC10 (spec Definition of Done — persistence): normalized DataFrame persisted via
  `to_sql(table, conn, if_exists="replace", index=False)`; existing table dropped and
  rewritten; row index not persisted; 26 columns in exact order, one row per unique KEY.

Spec Definition-of-Done checklist items (process-level): AC documented and mapped to
tests; behavior matches in documented environments; tests added; edge/error cases
covered; docs updated; telemetry N/A; toolchain pass completed.

## Acceptance Criteria Evaluation

| AC | Verdict | Evidence |
|---|---|---|
| AC1 | PASS | `_build_parser` requires `--output` (`src/normalize_le.py:449-453`); `write_sqlite` is the only sink (`363-392`); missing `--output` asserted non-zero by `test_main_missing_output_exits_nonzero`. |
| AC2 | PASS | `load_source` reads `header=2` and drops blank `Customer` (`src/normalize_le.py:230-240`); `validate_schema` names missing/extra/out-of-order (`164-199`); tests `test_load_source_*`, `test_validate_schema_*`, `test_main_schema_mismatch_exits_nonzero`. |
| AC3 | PASS | `rebuild_key` + `coerce_sku` (`95-161`); whole-number and non-numeric SKU asserted by `test_rebuild_key_*`, `test_coerce_sku_branches`, `test_normalize_non_numeric_sku_preserved`. |
| AC4 | PASS | `TARGET_COLUMNS` order with `YTG` after `Q4` before `Super Category` (`79-92`); `normalize` returns `output[TARGET_COLUMNS]` in first-appearance order via `groupby(sort=False)` (`288-312`); `test_normalize_column_order_and_no_ytd_ytg`, `test_normalize_first_appearance_order_preserved`. |
| AC5 | PASS | First-row text via `drop_duplicates(keep="first")`; numeric `SUM_COLUMNS` summed with default `min_count=0` (NaN->0) (`287-303`); `test_normalize_two_row_pair_sums_numeric`, `test_normalize_three_rows_sum_and_nan_as_zero`. |
| AC6 | PASS | `compute_ytg` sums `YTG_MONTHS` (May..Dec) on the output frame (`253-267`, applied at `307`); `test_compute_ytg_sums_may_through_dec`, `test_compute_ytg_property`. |
| AC7 | PASS | Both `Super Category` and `PPG` assigned from `first_rows["PPG"]` (`308-309`); `test_normalize_super_category_ppg_quirk` asserts equality and that source Super Category is ignored. |
| AC8 | PASS | `validate_tieouts` checks row count, per-column `1e-6` tie-out, and `FY == sum(months)` (`315-360`); `main` maps `ValueError` to exit 1 (`484-490`); `test_validate_tieouts_*` (pass + 3 failure paths), property round-trip. |
| AC9 | PASS | `print_summary` prints source/unique/output rows, per-column tie-outs, and first/middle/last rows (`395-433`); `test_main_end_to_end_success` asserts all summary lines; empty-output branch via `test_print_summary_empty_output_omits_row_samples`. |
| AC10 | PASS | `write_sqlite` uses `to_sql(table_name, con, if_exists="replace", index=False)` (`388-390`); `test_write_sqlite_roundtrip_columns_and_rows`, `test_write_sqlite_replace_if_exists_no_duplication` assert 26 columns in order, row count, and no duplication on re-run. |

Spec Definition-of-Done process items: PASS — AC mapped to tests (spec L229-245), tests
added (3 modules), edge/error cases covered, docs updated (README + feature docs),
telemetry N/A (CLI `print` by design), toolchain pass completed and independently
re-verified by the auditor (policy-audit Appendix B).

## Summary

All ten acceptance criteria evaluate PASS with concrete code anchors and passing tests.
The toolchain passes in a single clean pass (Black, Ruff, Pyright, Pytest) with 100% line
and branch coverage. Anti-requirements (no Super Category from source column, no YTD/YTG
in output, no alphabetical sorting, no rounding, preserve `SKU Descripiton` typo) are
encoded as invariants and asserted.

No PARTIAL, FAIL, or UNVERIFIED criteria. Remediation is not required on
acceptance-criteria grounds.

Recommendation: go for PR readiness.

## Acceptance Criteria Check-off

All nine `## Acceptance Criteria` items in `user-story.md`, all nine in `issue.md`, and
the persistence Definition-of-Done item in `spec.md` were already checked off `[x]` by
the executor. The reviewer evaluation above confirms each as PASS; no additional check-off
changes were required (no item needed to be flipped from `[ ]` to `[x]`, and no passing
item was found unchecked).

### Acceptance Criteria Status
- Source: `user-story.md`, `spec.md` (Definition of Done), mirrored in `issue.md`
- Total AC items: 9 (user-story) + 1 persistence DoD item (spec) = 10 evaluated
- Checked off (delivered): 10
- Remaining (unchecked): 0
- Items remaining: none
