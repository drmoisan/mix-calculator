# Phase 11 QA Gate

Phase 11 — MainWindow Shell and App Composition Root. Single clean pass.

## Black
Timestamp: 2026-05-27T20-59
Command: poetry run black .
EXIT_CODE: 0
Output Summary: Pass. 80 files left unchanged (after reformat restart).

## Ruff
Timestamp: 2026-05-27T20-59
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: Pass. 0 errors.

## Pyright
Timestamp: 2026-05-27T20-59
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: Pass. 0 errors, 0 warnings, 0 informations (strict). No new Any.

## Pytest (coverage)
Timestamp: 2026-05-27T20-59
Command: QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 274 passed (no new tests in P11 per the plan; coverage of these modules comes in P12).
- `src/gui/main_window.py`: 0% (covered by P12 test_app_composition.py and test_gui_integration.py).
- `src/gui/app.py`: 0% (P12 test_app_composition.py covers `build_application`; `main`'s blocking
  `qt_app.exec()` is intentionally not invoked under test).
- Repository TOTAL: 93% line, 100% branch. Gate satisfied (>= 85% line, >= 75% branch).
- No regression on changed lines.

## Notes
- `quality-tiers.yml`: added `src/gui/main_window.py: T3`, `src/gui/app.py: T4`.
- MainWindow is a thin shell: hosts the three SourceInputWidgets (default sheets `"LE-8 + 4"`,
  `"AOP1"`, `"SKU_LU"`), the preview, and the Import/Run/Save/Open/Export controls; each control
  emits a named signal.
- `app.py` factors composition into `build_application(qt_app=...)` so a test can construct the wired
  collaborators without entering the event loop; `main()` enters the blocking event loop.
- Constructor injection only; no DI framework.
- Confidentiality: fabricated values only.
