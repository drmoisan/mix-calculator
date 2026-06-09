# Phase 1 — 500-Line Cap Scan (Issue #60)

Timestamp: 2026-06-09T14-05

Command: wc -l src/gui/presenters/source_selection_presenter.py tests/gui/test_source_selection_presenter.py tests/gui/test_source_selection_presenter_header_row.py
EXIT_CODE: 0

Output Summary (per-file line counts; all <= 500):
- src/gui/presenters/source_selection_presenter.py: 379 lines (<= 500) — OK
- tests/gui/test_source_selection_presenter.py: 500 lines (<= 500) — OK
- tests/gui/test_source_selection_presenter_header_row.py: 260 lines (<= 500) — OK (new)

Extraction note:
- The Defect-3 multi-row-header discovery tests were added to
  test_source_selection_presenter.py, which pushed it to 725 lines (over the
  cap). They were extracted into a new sibling module
  tests/gui/test_source_selection_presenter_header_row.py with its own
  self-contained _schema() helper and _PerRowSchemaService fake, restoring the
  original test file to its 500-line cap state.
- Full Python loop re-passed after the extraction: black clean, ruff clean,
  pyright 0 errors, pytest 1004 passed.
