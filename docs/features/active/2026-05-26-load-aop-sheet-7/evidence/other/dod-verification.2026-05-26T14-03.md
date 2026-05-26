# Definition of Done Verification

Timestamp: 2026-05-26T14-03

Work Mode: full-feature. AC sources: `user-story.md` and `spec.md` (Definition
of Done), mirrored in `issue.md`. Each criterion is mapped to its satisfying
evidence below. All criteria are PASS.

| # | Acceptance criterion | Status | Evidence |
|---|---|---|---|
| 1 | `load_aop`, `persist_aop`, `main` exposed; file < 500 lines (helpers extracted if needed) | PASS | `src/load_aop.py` (322 lines) exposes all three; AOP helpers extracted to `src/_load_aop_helpers.py` (340 lines). P4-T5 file-size check: all files < 500. |
| 2 | Shared leaves renamed to etl_columns/etl_key/etl_totals; normalize_le + LE tests import new names; LE suite green | PASS | `src/etl_*.py` exist; old `le_*` gone (P1-T13 zero residual hits). LE-green gate `evidence/qa-gates/phase1-le-green.2026-05-26T14-03.md` (77 passed). |
| 3 | `fill_blank_totals` accepts dict mapping; LE tie-outs still pass; AOP uses {YTD, quarters, YTG} | PASS | `src/etl_totals.py` signature `(frame, totals_to_months)`; LE call site `{"FY": MONTH_COLUMNS, **QUARTER_TO_MONTHS}`; AOP call site `{"YTD": MONTHS, **QUARTER_TO_MONTHS, "YTG": YTG_MONTHS}`. Phase 1 + Phase 4 green. |
| 4 | `load_aop` reuses coerce_sku/rebuild_key/decide_key_action/resolve_key/resolve_columns/normalize_name/fill_blank_totals/total_vs_months_violations + pandas_io (no re-implementation) | PASS | `src/load_aop.py` imports from `src.etl_columns`, `src.etl_key`, `src.etl_totals`, `src.pandas_io`; `_load_aop_helpers` imports `total_vs_months_violations`. No helper re-implemented. |
| 5 | Position-independent resolution: exact/reordered/fuzzy>=0.85/missing-required halt/extras warn; optional KEY by name only | PASS | Tests in `tests/test_load_aop.py`: `test_resolution_exact_by_position`, `_reordered_columns`, `_fuzzy_match_above_threshold`, `_missing_required_column_raises`, `_extra_column_warns_and_continues`, `test_optional_key_located_by_name_only`. |
| 6 | Per-row validation YTD/Q1..Q4/YTG (tol 1e-6); row-count >= 1; duplicate KEYs warn (not fail); single ValueError lists all | PASS | `validate_aop` in `_load_aop_helpers.py`; tests `test_validation_*` (passing/aggregated-failure/empty-frame/duplicate-warn). |
| 7 | Numeric coerce before validation; Super Category/PPG sentinels -> None; no LE quirk; no row collapse | PASS | `coerce_numeric` precedes `validate_aop` in `load_aop`; tests `test_numeric_coercion_precedes_validation`, `test_clean_label_sentinels_*`, `test_aop_does_not_apply_le_super_category_quirk`, `test_aop_does_not_collapse_rows_by_key`. |
| 8 | CLI: --output required; flag defaults per spec; main 0/1; basicConfig once; summary to stdout | PASS | `build_parser` defaults match spec; tests `test_main_missing_output_exits_nonzero`, `_validation_error_returns_one`, `_success_prints_summary_and_confirmation`, `_diverging_key_prompt_non_tty_returns_one`, `_custom_sheet_and_table_name`. |
| 9 | SQLite persist via write_table; quoted lowercase indexes (space->_, #->num); if_exists passthrough; replace no duplication; --snake-case before writing | PASS | `persist_aop` routes through `write_table`; tests `test_persist_aop_roundtrip_columns_and_rows`, `_replace_no_duplication`, `_creates_safe_lookup_indexes`, `test_main_snake_case_renames_before_writing`. |
| 10 | Console-script `load-aop = "src.load_aop:main"` registered; module tier-classified T2-Core | PASS | `pyproject.toml [tool.poetry.scripts]` has both entries (P4-T5 diff); `quality-tiers.yml` classifies `src/load_aop.py: T2`. |
| 11 | Tests added (test_load_aop.py, test_load_aop_io.py) in-memory only (no temp files) | PASS | Both files present; fixtures use `io.BytesIO` and in-memory `PersistentConnection`; no `tempfile`/disk paths. |
| 12 | Full toolchain green single pass: Black, Ruff, Pyright strict, Pytest line>=85%/branch>=75%; no new dependency | PASS | `evidence/qa-gates/phase4-final-qa.2026-05-26T14-03.md` (all 0 exit, 100%/100%); `pyproject.toml` diff shows only the scripts table changed (no dependency added). |

## Constraint checks

- File-size limit (< 500 lines): PASS. Largest file `src/normalize_le.py` = 495
  lines; all `src` and `tests` files under 500.
- No new third-party dependency: PASS. `git diff pyproject.toml` shows only the
  `[tool.poetry.scripts]` `load-aop` line added; `[tool.poetry.dependencies]`
  and the dev group are unchanged. `hypothesis` and `pandas-stubs` were already
  present.
- No runtime temp files in tests: PASS. Tests use `io.BytesIO` workbooks and
  `sqlite3.connect(":memory:")` via the shared `PersistentConnection`.
- No Pyright suppressions added: PASS. Pyright strict reports 0 errors with no
  `# type: ignore` added; unknown-typed pandas members route through
  `src/pandas_io.py`.
