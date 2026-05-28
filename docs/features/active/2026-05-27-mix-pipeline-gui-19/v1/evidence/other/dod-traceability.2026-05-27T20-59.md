# Definition-of-Done Traceability

Timestamp: 2026-05-27T20-59

Every Definition-of-Done checkbox in `spec.md` and every `## Acceptance Criteria`
item in `user-story.md` and `issue.md` maps to at least one passing test. The
mapping below is taken from the spec DoD section and the
`Acceptance-Criteria Coverage Map` table in the plan. Every entry corresponds to
tests that passed in the final QA run (`final-pytest-coverage.2026-05-27T20-59.md`,
279 passed).

| Acceptance Criterion | Verifying Tests | Status |
|---|---|---|
| Per-input (LE, AOP, SKU_LU) select Excel file and pick worksheet tab | `tests/gui/test_source_selection_presenter.py`, `tests/gui/test_source_input_widget.py`, `tests/gui/test_workbook_reader.py`, `tests/gui/test_pipeline_service.py` | PASS |
| Selecting a file populates the tab dropdown | `tests/gui/test_source_selection_presenter.py`, `tests/gui/test_source_input_widget.py`, `tests/gui/test_workbook_reader.py` | PASS |
| Optional per-input "render tab" checkbox shows a preview | `tests/gui/test_source_selection_presenter.py`, `tests/gui/test_preview_widget.py`, `tests/gui/test_source_input_widget.py` | PASS |
| Import one or all selected files | `tests/gui/test_pipeline_presenter.py`, `tests/gui/test_pipeline_service.py`, `tests/gui/test_gui_integration.py` | PASS |
| Run executes pipeline and reports success/failure | `tests/gui/test_pipeline_presenter.py`, `tests/gui/test_pipeline_worker.py`, `tests/gui/test_pipeline_service.py`, `tests/gui/test_gui_integration.py` | PASS |
| Save persists to SQLite `.db` | `tests/gui/test_db_service.py`, `tests/gui/test_pipeline_presenter.py`, `tests/gui/test_pipeline_service.py`, `tests/gui/test_gui_integration.py` | PASS |
| Open loads tables from existing `.db` | `tests/gui/test_db_service.py`, `tests/gui/test_pipeline_presenter.py`, `tests/gui/test_gui_integration.py` | PASS |
| Export: per-table checklist, export-all, Excel + CSV, extensible | `tests/gui/test_exporter_registry.py`, `tests/gui/test_excel_exporter.py`, `tests/gui/test_csv_exporter.py`, `tests/gui/test_export_presenter.py`, `tests/gui/test_export_dialog.py`, `tests/gui/test_gui_integration.py` | PASS |
| Presentation logic testable without a live Qt event loop | `tests/gui/test_source_selection_presenter.py`, `tests/gui/test_pipeline_presenter.py`, `tests/gui/test_export_presenter.py`, `tests/gui/test_app_composition.py` (all presenter tests run with no `QApplication`) | PASS |
| Qt widgets tested with the Qt test facility | `tests/gui/test_pipeline_worker.py`, `tests/gui/test_source_input_widget.py`, `tests/gui/test_preview_widget.py`, `tests/gui/test_export_dialog.py`, `tests/gui/test_app_composition.py` (all use `pytest-qt` `qtbot` under `QT_QPA_PLATFORM=offscreen`) | PASS |
| Full toolchain passes; coverage >= 85% line / >= 75% branch, no regression | `evidence/qa-gates/final-black`, `evidence/qa-gates/final-ruff`, `evidence/qa-gates/final-pyright`, `evidence/qa-gates/final-pytest-coverage`, `evidence/qa-gates/coverage-delta` | PASS |

## Confidentiality verification

A grep of `src/gui/` for `SKU Description` and `Category` returned no matches.
A grep of `tests/gui/` returned only schema column-name headers used to build
fabricated SKU_LU workbooks (the schema labels are not confidential per the
`load_skulu` policy; only the VALUES are). The SKU_LU values across all new
source/test files are fabricated only: `SKU-001`/`SKU-002`/`Widget A`/`Widget B`/
`Category X`/`Category Y`. No real customer names, SKU numbers, prices, or
discounts appear. The Country values `US`/`Canada` are not secret.

## Banned timing APIs verification

A grep of `tests/gui/` for `time.sleep`, `QThread.sleep`, `QTest.qWait`, and
`qWait(` returned one match — a docstring in `test_pipeline_worker.py` stating
the APIs are absent. No actual usage. All Qt tests use only event-driven
`qtbot.waitSignal` or main-thread synchronous calls.

## Outcome

Every acceptance criterion in `spec.md` Definition of Done, `user-story.md`
`## Acceptance Criteria`, and `issue.md` `## Acceptance Criteria (early draft)`
maps to passing tests. Confidentiality and banned-timing-API invariants are
preserved across all new source, test, fixture, and doc files. No DoD item is
unverified.
