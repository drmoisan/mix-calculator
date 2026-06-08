# Phase 1 — Implementation Handoff Confirmation

Timestamp: 2026-06-07T20-45

Locked design handed off and confirmed. Scope is limited to:
- src/_normalize_le_columns.py (constants REQUIRED_COLUMNS, OPTIONAL_BY_NAME; redefine EXPECTED_COLUMNS = REQUIRED_COLUMNS; __all__; rewrite resolve_le_columns)
- src/normalize_le.py (load_source select/rename block + header-detection intent comment only; __all__ re-export of REQUIRED_COLUMNS)
- tests/test_normalize_le_columns.py (new), tests/test_normalize_le.py, tests/test_normalize_le_header.py, tests/test_etl_columns.py

Confirmed untouched:
- src/load_aop.py (and its EXPECTED_COLUMNS)
- the schema loader
- normalize() and validate_tieouts() in normalize_le.py
- the CLI surface

Batch policy confirmed: per-batch cap 3 production + 3 test files; 500-line cap;
parity invariant for the standard full-column LE source is the top priority.
