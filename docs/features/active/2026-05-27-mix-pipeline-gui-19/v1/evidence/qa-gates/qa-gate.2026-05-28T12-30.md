# QA Gate — 2026-05-28T12-30 (post-remediation)

Timestamp: 2026-05-28T12-30
Command: poetry run black --check . ; poetry run ruff check . ; poetry run pyright ; poetry run pytest --cov --cov-branch --cov-report=term
EXIT_CODE: 0
Output Summary:
- Black: 92 files would be left unchanged.
- Ruff: All checks passed.
- Pyright: 0 errors, 0 warnings, 0 informations.
- Pytest: 333 passed in 18.86s (314 baseline + 19 new tests in tests/gui/test_app_wiring.py).
- Coverage: 1793/1793 lines (100%) and 262/262 branches (100%).
- Delta vs baseline (2026-05-28T12-30 baseline.md): zero new findings; coverage unchanged at 100%/100% with 51 added statements and 10 added branches accounted for by the new wiring helper and default chooser/runner functions in src/gui/app.py, all covered by tests/gui/test_app_wiring.py.

## Scope
- src/gui/app.py — added wire_control_signals + default_save_chooser/default_open_chooser/default_export_runner; build_application now calls wire_control_signals.
- src/gui/exporters/excel_exporter.py — replaced _PandasExcelWriters Protocol with Callable[..., _ExcelWriter]; removed the # noqa: N802 suppression.
- tests/gui/test_app_wiring.py (new) — 19 tests covering the six MainWindow signal routes, the cancel paths, and the three default chooser/runner helpers.

## Suppressions
- One `# type: ignore[method-assign]` on the test seam that wraps `ExportPresenter.set_available_tables` to auto-check the dialog list. This is a test-only monkey-patch using mypy's documented escape hatch; not in src code.
- `# noqa: N802` removed from src/gui/exporters/excel_exporter.py — refactor eliminates the need.
