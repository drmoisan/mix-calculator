# Final QA — Pytest with Coverage

Timestamp: 2026-05-27T20-59
Command: QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0

Output Summary:
- Tests: 279 passed, 0 failed.
- Repository line coverage: 100% (TOTAL 1538 stmts, 0 missed).
- Repository branch coverage: 100% (TOTAL 238 branches, 0 partial).
- Coverage gates satisfied: line 100% >= 85%, branch 100% >= 75%.
- Platform win32, python 3.13.12-final-0.

Per-module coverage for `src/gui/**` (all 100% line and 100% branch):

```
src/gui/__init__.py                                    0 stmts, 100%
src/gui/app.py                                        70 stmts, 100%
src/gui/main_window.py                                63 stmts, 100%
src/gui/pipeline_service.py                           67 stmts, 100%
src/gui/protocols.py                                  18 stmts, 100%
src/gui/exporters/__init__.py                          0 stmts, 100%
src/gui/exporters/base.py                              8 stmts, 100%
src/gui/exporters/registry.py                         14 stmts, 100%
src/gui/exporters/excel_exporter.py                   15 stmts, 100%
src/gui/exporters/csv_exporter.py                     18 stmts, 100%
src/gui/presenters/__init__.py                         0 stmts, 100%
src/gui/presenters/source_selection_presenter.py      31 stmts, 100%
src/gui/presenters/pipeline_presenter.py             106 stmts, 100%
src/gui/presenters/export_presenter.py                24 stmts, 100%
src/gui/services/__init__.py                           0 stmts, 100%
src/gui/services/workbook_reader.py                   26 stmts, 100%
src/gui/services/db_service.py                        26 stmts, 100%
src/gui/widgets/__init__.py                            0 stmts, 100%
src/gui/widgets/source_input_widget.py                56 stmts, 100%
src/gui/widgets/preview_widget.py                     27 stmts, 100%
src/gui/widgets/export_dialog.py                      46 stmts, 100%
src/gui/widgets/progress_dialog.py                    20 stmts, 100%
src/gui/workers/__init__.py                            0 stmts, 100%
src/gui/workers/pipeline_worker.py                    22 stmts, 100%
```
