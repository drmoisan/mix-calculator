# Phase 0 — Pytest + coverage baseline

Timestamp: 2026-05-29T10-15

Command: `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

Output Summary:
- 457 tests passed; 0 failed; 0 skipped.
- Total coverage: 99% line; statements 2124, missed 14, branches 322, partial 1.
- src/build_exe.py is part of the coverage scope; no build_velopack.py file yet exists.
- src/gui/runners.py at 66% (lines 131-147 not executed; pre-existing pattern unchanged by this feature).
- src/gui/widgets/source_input_widget.py at 97%.
- All other modules at 100% line.
