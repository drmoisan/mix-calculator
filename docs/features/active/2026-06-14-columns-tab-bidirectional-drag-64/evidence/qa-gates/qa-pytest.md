---
Timestamp: 2026-06-15T00-58
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
  Tests: 1041 passed, 0 failed, 5 warnings (4 new tests added vs baseline 1037)
  Overall line coverage: ~99% (4881/4927 statements)
  Overall branch coverage: ~94% (871/926 branches)
  Key module (_columns_tab_drag.py): 94% line, ~77% branch (126 stmts, 4 missed)
  Key module (_schema_builder_drag_tabs.py): 96% line (62 stmts, 1 missed)
  All 4 new tests: PASSED
    - test_assigned_row_mousemove_starts_drag_carrying_source_and_origin
    - test_unassigned_row_mousemove_does_not_start_drag
    - test_pool_dropEvent_with_canonical_origin_calls_clear_row
    - test_pool_dragEnterEvent_rejects_missing_canonical_origin
---
