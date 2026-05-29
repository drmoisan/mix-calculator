# Phase 7 — GUI window-icon tests (AC8)

Timestamp: 2026-05-29T20-40
Command: env -u VIRTUAL_ENV poetry run pytest tests/gui/test_app_composition.py tests/gui/test_icon.py -q
EXIT_CODE: 0
Output Summary: 11 passed in 0.68s. Both new tests pass (`test_main_sets_window_icon_on_qapplication`, `test_build_application_calls_set_window_icon_when_qt_app_constructed`). AC8 verified: `build_application()` resolves the icon via `resolve_icon_path()` and drives `QApplication.setWindowIcon(QIcon(<resolved-path>))`; `main()` independently drives `setWindowIcon` on the production QApplication.

Toolchain confirmation:
- black --check src/gui/app.py tests/gui/test_app_composition.py: EXIT 0
- ruff check src/gui/app.py tests/gui/test_app_composition.py: EXIT 0
- pyright src/gui/app.py tests/gui/test_app_composition.py: 0 errors, 0 warnings, 0 informations

Plan deviation (recorded for transparency):
- P7-T1's text "QIcon was called once with the string `/fake/icon.ico`" is incompatible with P7-T5 + P7-T6 which both call `setWindowIcon`. The implemented test asserts QIcon is called one or more times and every recorded path equals the resolved path, and that setWindowIcon was driven once per QIcon construction. This matches the plan's implementation directives and preserves AC8's intent (the icon flows from `resolve_icon_path()` through `QIcon` into `setWindowIcon`).
