# Phase 9 — File-size cap (AC11)

Timestamp: 2026-05-29T20-50
Command: env -u VIRTUAL_ENV poetry run python -c "import pathlib;files=['src/build_exe.py','src/build_velopack.py','src/gui/app.py','src/gui/_icon.py','src/gui/_main_window_view.py','packaging/velopack/convert_icon.py','tests/test_build_exe.py','tests/test_build_velopack.py','tests/gui/test_app_composition.py','tests/gui/test_icon.py','tests/test_convert_icon.py'];[print(f, sum(1 for _ in pathlib.Path(f).open()), 'PASS' if sum(1 for _ in pathlib.Path(f).open()) < 500 else 'FAIL') for f in files]"
EXIT_CODE: 0
Output Summary: All new and modified files under the 500-line cap:

| File | Lines | Status |
|---|---|---|
| src/build_exe.py | 228 | PASS |
| src/build_velopack.py | 422 | PASS |
| src/gui/app.py | 456 | PASS |
| src/gui/_icon.py | 124 | PASS |
| src/gui/_main_window_view.py | 108 | PASS |
| packaging/velopack/convert_icon.py | 358 | PASS |
| tests/test_build_exe.py | 394 | PASS |
| tests/test_build_velopack.py | 496 | PASS |
| tests/gui/test_app_composition.py | 401 | PASS |
| tests/gui/test_icon.py | 84 | PASS |
| tests/test_convert_icon.py | 151 | PASS |

Note: `src/gui/_main_window_view.py` is a Phase 9 extraction created during the AC11 remediation loop. `MainWindowPipelineView` was relocated from `src/gui/app.py` to drop that file below the 500-line cap; the class is re-exported from `src/gui/app.py` so the public symbol table is unchanged. AC11 verified.
