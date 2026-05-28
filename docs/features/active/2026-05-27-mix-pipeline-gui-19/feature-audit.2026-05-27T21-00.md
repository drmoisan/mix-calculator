# Feature Audit: mix-pipeline-gui (Issue #19)

**Audit Date:** 2026-05-27
**Feature Folder:** `docs/features/active/2026-05-27-mix-pipeline-gui-19/`
**Base Branch:** `main`
**Head Branch:** `feature/mix-pipeline-gui-19`
**Work Mode:** `full-feature`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `703de5170c37dadb8189eecc01398730d5c50e8d` resolved as the merge-base)
- **Head branch/commit:** `feature/mix-pipeline-gui-19` (commit `ad8c84fa25aa52296360284ff39ba5176ac1494d`)
- **Merge base:** `703de5170c37dadb8189eecc01398730d5c50e8d`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/**`
  - Additional evidence: `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/other/dod-traceability.2026-05-27T20-59.md` for AC-to-test mapping
- **Feature folder used:** `docs/features/active/2026-05-27-mix-pipeline-gui-19/`
- **Requirements source:** Multiple files — `spec.md` (Definition of Done) and `user-story.md` (`## Acceptance Criteria`), per the `full-feature` work mode rule.
- **Work mode resolution note:** `issue.md` carries the persisted marker `- Work Mode: full-feature` (line 10). For this marker the authoritative AC sources are `spec.md` and `user-story.md`. `issue.md` `## Acceptance Criteria (early draft)` is a secondary view and is not authoritative for full-feature work.
- **Scope note:** The audit scope is the full branch diff between the merge-base and the head. The CI green gate is the orchestrator's S9 responsibility and is not in scope for this audit.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/spec.md` — primary (Definition of Done section, 11 items)
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/user-story.md` — primary (## Acceptance Criteria section, 10 items)

The two source files describe the same set of capabilities at different abstraction levels. The user-story criteria are the user-visible behaviors (10 items); the spec Definition of Done adds the traceability mapping to verifying test modules and a final toolchain gate (11 items). The audit evaluates the user-story criteria as the primary set and treats the spec Definition of Done items as the verifying evidence for each.

### From `user-story.md` (`## Acceptance Criteria`, 10 items)

1. For each input table (LE, AOP, SKU_LU) the user can select an Excel file and pick the worksheet tab for that input.
2. Selecting an Excel file populates a dropdown of that workbook's worksheet tabs.
3. An optional per-input "render tab" checkbox shows a preview image of the selected worksheet's contents when checked.
4. The user can import one selected file or all selected files.
5. After import, a Run button executes the mix pipeline against the imported inputs and reports success/failure.
6. A Save button persists the working data to a SQLite `.db` file.
7. An Open button loads tables from an existing `.db` file.
8. An Export action exports selected tables to Excel and CSV, with a per-table checklist and an "export all" control; the export format set is extensible.
9. Presentation logic is separated from Qt widgets and services are injected, so view-models/controllers are unit-testable without a live Qt event loop where practical, and Qt widgets are tested with the project's Qt test facility.
10. The full toolchain (Black, Ruff, Pyright strict, Pytest with coverage thresholds) passes, and coverage meets the repository thresholds (>= 85% line, >= 75% branch).

### From `spec.md` (`## Definition of Done`, 11 items)

The Definition of Done restates each user-story item with explicit verifying test references:

1. Per-input (LE, AOP, SKU_LU) select Excel file and pick worksheet tab — verified by `test_source_selection_presenter.py`, `test_source_input_widget.py`, `test_workbook_reader.py`.
2. Selecting a file populates the tab dropdown — verified by `test_source_selection_presenter.py`.
3. Optional per-input "render tab" checkbox shows a preview — verified by `test_source_selection_presenter.py` and `test_preview_widget.py`.
4. Import one or all selected files — verified by `test_pipeline_presenter.py` and `test_pipeline_service.py`.
5. Run button executes the pipeline and reports success/failure — verified by `test_pipeline_presenter.py`, `test_pipeline_worker.py`, and `test_pipeline_service.py`.
6. Save button persists to a SQLite `.db` — verified by `test_pipeline_presenter.py` and `test_pipeline_service.py`.
7. Open button loads tables from an existing `.db` — verified by `test_pipeline_presenter.py`.
8. Export: per-table checklist, export-all, Excel + CSV, extensible — verified by `test_export_presenter.py`, `test_exporter_registry.py`, `test_excel_exporter.py`, `test_csv_exporter.py`, and `test_export_dialog.py`.
9. Presentation logic testable without a live Qt event loop — verified by all `test_*_presenter.py` running with no `QApplication`.
10. Qt widgets tested with the Qt test facility — verified by `test_*_widget.py`, `test_export_dialog.py`, and `test_pipeline_worker.py` using `pytest-qt` under `QT_QPA_PLATFORM=offscreen`.
11. Full toolchain passes and coverage meets repository thresholds — verified by the final QA artifacts under `evidence/qa-gates/`.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | Per-input (LE/AOP/SKU_LU) select Excel file and pick worksheet tab | PASS | `src/gui/widgets/source_input_widget.py` (238 lines), `src/gui/presenters/source_selection_presenter.py` (156 lines), `src/gui/services/workbook_reader.py` (162 lines). Tests: `tests/gui/test_source_input_widget.py`, `tests/gui/test_source_selection_presenter.py`, `tests/gui/test_workbook_reader.py`. | `QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_source_input_widget.py tests/gui/test_source_selection_presenter.py tests/gui/test_workbook_reader.py` (per `final-pytest-coverage.2026-05-27T20-59.md`, all pass) | Three concrete `SourceInputWidget` instances are constructed by `MainWindow` for the LE/AOP/SKU_LU inputs (verified in `src/gui/main_window.py`). |
| 2 | Selecting an Excel file populates a tab-list dropdown | PASS | `SourceSelectionPresenter.on_file_selected` calls `WorkbookReader.get_sheet_names` and pushes to `view.set_tab_list`. Tests cover the happy path and the FakeWorkbookReader exception path. | Same pytest invocation as item 1. | The presenter is tested with `FakeWorkbookReader` returning known sheet names; the widget test verifies the dropdown model updates. |
| 3 | Optional per-input "render tab" checkbox shows a preview | PASS | `src/gui/widgets/preview_widget.py` (97 lines) + `SourceSelectionPresenter.on_render_tab` calling `WorkbookReader.read_sheet_preview` with `max_rows=200`. Tests: `tests/gui/test_preview_widget.py`. | Same pytest invocation as item 1. | The spec's "preview image" wording is realized as a `QTableView`-backed grid rendered from `list[list[str]]`; a `QPixmap` rendering via `widget.grab()` is available when an image-style preview is required. |
| 4 | Import one or all selected files | PASS | `PipelinePresenter.on_import_one` and `on_import_all`; service methods `import_le`, `import_aop`, `import_skulu`, and `import_sources`. Tests: `test_pipeline_presenter.py` (336 lines) and `test_pipeline_service.py` (424 lines). | `QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_pipeline_presenter.py tests/gui/test_pipeline_service.py` (all pass) | Loader `ValueError` is propagated to `view.show_error`; the SKU_LU default path (same workbook as LE/AOP) is exercised. |
| 5 | Run button executes the pipeline and reports success/failure | PASS | `PipelinePresenter.on_run` (synchronous path) and `make_run_task` + `apply_run_result` + `PipelineWorker` (off-UI-thread path). Tests: `test_pipeline_presenter.py`, `test_pipeline_worker.py`, `test_pipeline_service.py`. | Same pytest invocation as item 4, plus `test_pipeline_worker.py`. | Both paths are implementation-complete and tested. Worker tests use `qtbot.waitSignal` (event-driven). |
| 6 | Save button persists to a SQLite `.db` | PASS | `PipelinePresenter.on_save` → `PipelineService.save_to_db` → `DbService.save_tables` over `src/pandas_io.py`. Tests: `test_pipeline_presenter.py`, `test_pipeline_service.py`, `test_db_service.py`. | `QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_db_service.py tests/gui/test_pipeline_presenter.py tests/gui/test_pipeline_service.py` (all pass) | `sqlite3.connect(":memory:")` is used in tests; no temp files. |
| 7 | Open button loads tables from an existing `.db` | PASS | `PipelinePresenter.on_open_db` → `PipelineService.open_db` → `DbService.open_tables`. Tests: `test_pipeline_presenter.py`, `test_db_service.py`. | Same pytest invocation as item 6. | Reopened tables populate the in-memory working set; the integration scenario in `test_gui_integration.py` exercises the full save→reopen cycle. |
| 8 | Export to Excel and CSV with checklist and export-all; extensible | PASS | `ExportPresenter`, `ExporterRegistry`, `ExcelExporter`, `CsvExporter`, `ExportDialog`. Tests: `test_export_presenter.py`, `test_exporter_registry.py`, `test_excel_exporter.py`, `test_csv_exporter.py`, `test_export_dialog.py`. | `QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_export_presenter.py tests/gui/test_exporter_registry.py tests/gui/test_excel_exporter.py tests/gui/test_csv_exporter.py tests/gui/test_export_dialog.py` (all pass) | Extensibility verified by the registry-driven design: adding a third format requires only `registry.register(NewExporter())` at the composition root. Empty-selection rejection is enforced before any exporter call. |
| 9 | Presentation logic separable from Qt; services injected; widgets tested with Qt facility | PASS | All three presenters live in `src/gui/presenters/**` and import no Qt symbols at runtime. Tests for presenters run with no `QApplication`. Qt widgets are tested with `pytest-qt` `qtbot` under `QT_QPA_PLATFORM=offscreen`. Constructor injection is used everywhere; no DI framework. | The presenter tests (`test_*_presenter.py`) do not request the `qapp` or `qtbot` fixtures; the widget tests (`test_*_widget.py`, `test_export_dialog.py`, `test_pipeline_worker.py`) do. | Verified by grep over `src/gui/presenters/**`: no `PySide6` import. |
| 10 | Full toolchain (Black, Ruff, Pyright strict, Pytest) passes; coverage meets repo thresholds | PASS | `evidence/qa-gates/final-black.2026-05-27T20-59.md` (EXIT 0), `final-ruff.2026-05-27T20-59.md` (EXIT 0), `final-pyright.2026-05-27T20-59.md` (EXIT 0, strict), `final-pytest-coverage.2026-05-27T20-59.md` (EXIT 0, 279 pass, 100% line / 100% branch). | `poetry run black .`, `poetry run ruff check .`, `poetry run pyright`, `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing`. | Thresholds (line >= 85%, branch >= 75%) cleared with significant margin. New code at 100%/100%. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 10 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None. Every user-story acceptance criterion is satisfied with verified evidence.

**Recommended follow-up verification steps:**

1. Confirm or extend the `# noqa: N802` suppression authorization in `.claude/rules/python-suppressions.md` (referenced in the companion `code-review.2026-05-27T21-00.md`). This is a Minor governance follow-up and does not affect feature acceptance.
2. Optionally wire `PipelineWorker` into the production `MainWindow.on_run_clicked` so the Run button uses the off-UI-thread path in production. The current sync path is tested and functional; the worker exists and is independently tested.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules, the AC source files contain markdown checkboxes that the executor pre-checked during plan execution. The reviewer verified that each `[x]` corresponds to a PASS evaluation above. No state change was required because every checkbox was already `[x]` and every evaluation is PASS.

### AC Status Summary

- Source: `docs/features/active/2026-05-27-mix-pipeline-gui-19/spec.md` (Definition of Done, 11 items) and `docs/features/active/2026-05-27-mix-pipeline-gui-19/user-story.md` (## Acceptance Criteria, 10 items)
- Total AC items: 21 (10 user-story + 11 spec DoD)
- Checked off (delivered): 21
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `docs/features/active/2026-05-27-mix-pipeline-gui-19/user-story.md` | 10 | 10 | 0 | Checkbox-backed. All items already `[x]` (executor pre-checked during plan execution); reviewer verified each maps to a PASS evaluation in this audit. |
| `docs/features/active/2026-05-27-mix-pipeline-gui-19/spec.md` | 11 | 11 | 0 | Checkbox-backed (Definition of Done). All items already `[x]`; reviewer verified each maps to a PASS evaluation. The 11th item (full toolchain + coverage thresholds) is the consolidated toolchain check, covered by item 10 in the user-story set. |

No source-file checkbox state change was made by the reviewer because every item was already `[x]` at audit time and every reviewer evaluation is PASS, so the existing state matches the audit outcome. `issue.md` `## Acceptance Criteria (early draft)` is a secondary view and is not authoritative for full-feature work; its checkboxes are also all `[x]`.
