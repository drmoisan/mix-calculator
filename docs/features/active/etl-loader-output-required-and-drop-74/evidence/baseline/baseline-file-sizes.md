# Baseline — Near-cap file line counts

Timestamp: 2026-06-17T14-06
Command: wc -l src/schema_serialization.py src/_schema_model_specs.py
EXIT_CODE: 0
Output Summary:
- src/schema_serialization.py: 497 lines (3 below the 500-line cap).
- src/_schema_model_specs.py: 486 lines (14 below the 500-line cap).
- src/_schema_loader_helpers.py: 464 lines (for reference; touched in Phase 2).
- Extraction decision (P1-T1/P1-T4): schema_serialization.py at 497 has only 3 lines of headroom; adding a _COLUMN_KEYS entry, the _column_to_object emit line, and the migration-seeding logic plus docstring will exceed 500. Extraction of migration/column logic into a helper module is therefore likely required and will be evaluated per the projected count in P1-T1/P1-T4.
