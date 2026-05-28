# QA Gate — test_app_wiring.py file-size split

Timestamp: 2026-05-28T12-56

## Scope

Split `tests/gui/test_app_wiring.py` (561 lines, over the 500-line cap from
`.claude/rules/general-code-change.md`) into three files, all under 500 lines.

Files touched:

- `tests/gui/_wiring_test_doubles.py` — new private helper module (220 lines)
  hosting `AutoCheckAllExportPresenter`, `build_wired`, `populate_widget_paths`,
  `fabricated_imports`, and `seed_import_spec`.
- `tests/gui/test_app_wiring.py` — rewritten to 244 lines covering signal
  routing for `wire_control_signals` (12 tests).
- `tests/gui/test_app_wiring_defaults.py` — new module at 181 lines covering
  the `default_save_chooser`, `default_open_chooser`, and `default_export_runner`
  factories (7 tests).

Production code is unchanged.

## Commands and results

### black

Command: `poetry run black .`
EXIT_CODE: 0
Output Summary: All done. 94 files left unchanged.

### ruff

Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: All checks passed.

### pyright

Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

### pytest with coverage

Command: `poetry run pytest --cov --cov-branch --cov-report=term`
EXIT_CODE: 0
Output Summary: 333 passed in 18.65s. TOTAL coverage: 1793 statements,
0 missed, 262 branches, 0 partial — 100% line and 100% branch.

## File-size verification

Largest test file under `tests/gui/` after the split:
`tests/gui/test_pipeline_service.py` at 424 lines. All other test files,
including the three modified by this change, are below 500 lines.

## Deltas vs. baseline

- Ruff: 0 new findings.
- Pyright: 0 new diagnostics.
- Pytest: 333 passed (no failing tests; same total as baseline).
- Coverage: 100% line, 100% branch (unchanged).
- No new `# noqa` or `# type: ignore` suppressions introduced.
