# Phase 0 — Authoritative Inputs Read

Timestamp: 2026-06-07T20-45

Files read and confirmed:
- docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/spec.md (FINAL v1.0)
- docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/issue.md (AC-1..AC-8)
- src/_normalize_le_columns.py (EXPECTED_COLUMNS, resolve_le_columns)
- src/normalize_le.py (load_source select/rename + header-detection comment)
- src/load_aop.py (reference pattern lines 200-247 for optional-by-name + columns_to_keep)
- tests/le_fixtures.py (build_workbook supports header= pruning and leading_rows=)

Work Mode confirmation: Work Mode is `full-bug` (per issue.md metadata block line 10 and plan line 5). Scope: src/_normalize_le_columns.py + src/normalize_le.py load_source selection only, plus named test files. load_aop and the schema loader are NOT touched.
