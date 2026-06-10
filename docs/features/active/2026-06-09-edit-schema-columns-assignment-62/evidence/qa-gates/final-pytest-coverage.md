# Phase 2 — Final Pytest + Coverage (Issue #62, Cycle 1, P2-T4)

Timestamp: 2026-06-10T09-25
Command: $env:QT_QPA_PLATFORM='offscreen'; poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0

Output Summary:
- Result: 1037 passed, 0 failed, 3 warnings in 29.83s.
- The Phase 0 baseline flaky Hypothesis test
  (tests/test_normalize_le_io.py::test_validate_tieouts_property_roundtrip)
  passed in this run; the full suite is green on a single pass.
- Coverage TOTAL: statements 4903, missed 44, branches 922, partial 54.
- Line coverage: (4903-44)/4903 = 99.10%.
- Branch coverage: (922-54)/922 = 94.14%.
- Both above thresholds (line >= 85%, branch >= 75%).

Changed-file coverage (this cycle):
- src/gui/_schema_discovery_wiring.py: 100% (46 stmts, 0 missed; 14 branches, 0 partial).
- src/gui/presenters/source_selection_presenter.py: 99% (96 stmts, 0 missed;
  28 branches, 1 partial 399->401, a pre-existing branch in the unchanged
  _apply_activation_decision routing, not part of this cycle's edits).
- src/gui/widgets/_schema_builder_tabs.py: 100% (90 stmts, 0 missed).
- src/gui/widgets/_schema_builder_window_setup.py: 100% (9 stmts, 0 missed) — new file.
- src/gui/widgets/schema_builder_dialog.py: 98% (113 stmts, 1 missed line 378;
  1 partial branch 481->exit — both in unchanged set_derived/_handle_new_derived
  paths, not this cycle's edits).
- The lines added by this cycle (window-flag application, scroll-area wrap,
  read_worksheet_header_columns, edit preview-slice wiring) are fully covered.
