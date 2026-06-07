# Fail-Before / Pass-After — Cycle 3 (B1 + B2)

Timestamp: 2026-06-05T23-08

## Method

The three source files (`source_selection_presenter.py`, `_schema_discovery_wiring.py`,
`workbook_reader.py`) were temporarily reverted via `git stash` (source only; the new
tests retained), the new tests were run to prove they fail against pre-fix code, then the
fixes were restored via `git stash pop`.

## Fail-before (pre-fix code, new tests present)

Command: env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest <7 new tests>
EXIT_CODE: 1
Output Summary: 7 failed.

Failing tests (all expected to fail pre-fix):
- B1 wiring-level (primary): tests/gui/test_schema_discovery_wiring.py::test_tab_activation_no_file_selected_does_not_call_reader
- B1 wiring-level (file, no worksheet): tests/gui/test_schema_discovery_wiring.py::test_tab_activation_file_but_no_worksheet_never_calls_reader_blank_sheet
- B2 reader contract (unknown sheet): tests/gui/test_workbook_reader.py::test_read_sheet_preview_unknown_sheet_raises_value_error
- B2 reader contract (blank sheet): tests/gui/test_workbook_reader.py::test_read_sheet_preview_blank_sheet_name_raises_value_error
- B1 presenter guard (blank path): tests/gui/test_source_selection_presenter.py::test_on_schema_discovery_blank_path_is_noop
- B1 presenter guard (blank sheet): tests/gui/test_source_selection_presenter.py::test_on_schema_discovery_blank_sheet_is_noop
- B1 presenter guard (whitespace sheet): tests/gui/test_source_selection_presenter.py::test_on_schema_discovery_whitespace_sheet_is_noop

Representative pre-fix failure (whitespace sheet): the reader WAS called with a blank
sheet — `reader.preview_calls == [('workbook.xlsx', '   ', 1)]` — exactly the defect.

## Pass-after (fixes restored)

Command: env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_schema_discovery_wiring.py tests/gui/test_workbook_reader.py tests/gui/test_source_selection_presenter.py
EXIT_CODE: 0
Output Summary: 38 passed.

## B2 presenter routing test (already passing post-fix, regression check)

- tests/gui/test_source_selection_presenter.py::test_on_schema_discovery_stale_sheet_value_error_routes_to_show_error

Note: the B2 presenter-routing test ([P2-T4]) is a positive-path test that exercises the
presenter's existing ValueError catch; it does not depend on the source guard being absent,
so it passes both pre- and post-fix. The reader-contract tests above ([P2-T3]) carry the
fail-before proof for B2.
