# Feature Audit: mix-pipeline-gui (Issue #19) — Final Post-Remediation Audit

**Audit Date:** 2026-05-28
**Feature Folder:** `docs/features/active/2026-05-27-mix-pipeline-gui-19/`
**Base Branch:** `main` @ `7836c24ed350ebe654b924373335aa606c1fa215`
**Head Branch:** `feature/mix-pipeline-gui-19` @ `e68ea3d` + uncommitted working-tree edits to `src/gui/app.py`, `src/gui/exporters/excel_exporter.py`, plus new `tests/gui/test_app_wiring.py`.
**Work Mode:** `full-feature` (per `issue.md` line 10)
**Audit Type:** Final post-remediation audit.
**Prior Audits Superseded:**
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/feature-audit.2026-05-27T21-00.md`
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/feature-audit.2026-05-28T12-17.md`

---

## Scope and Baseline

- **Base branch:** `main` @ `7836c24` (resolved by `git merge-base main HEAD`).
- **Head branch/commit:** `feature/mix-pipeline-gui-19` @ `e68ea3d` + uncommitted working-tree edits.
- **Merge base:** `7836c24ed350ebe654b924373335aa606c1fa215`.
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt` (regenerated against current live refs: base `7836c24`, head `e68ea3d`).
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt` (regenerated against current live refs).
  - Feature evidence: `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/**`, including the remediation-start baseline at `evidence/baseline/baseline.2026-05-28T12-30.md` and the post-remediation qa-gate at `evidence/qa-gates/qa-gate.2026-05-28T12-30.md`.
  - Reviewer-reproduced live toolchain on the working tree: Black/Ruff/Pyright 0 issues; Pytest 333 pass / 0 fail; coverage 100% line / 100% branch (1793/1793 line, 262/262 branch).
- **Feature folder used:** `docs/features/active/2026-05-27-mix-pipeline-gui-19/`.
- **Requirements source:** Multiple files — `spec.md` (Definition of Done, 11 items) and `user-story.md` (## Acceptance Criteria, 10 items), per the `full-feature` work mode rule.
- **Work mode resolution note:** `issue.md` carries the persisted marker `- Work Mode: full-feature` (line 10). For this marker the authoritative AC sources are `spec.md` and `user-story.md`.
- **Scope note:** The audit scope is the full branch diff between the merge-base and the head + working tree. The CI green gate is the orchestrator's S9 responsibility and is not in scope for this audit.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/spec.md` — primary (Definition of Done section, 11 items).
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/user-story.md` — primary (## Acceptance Criteria section, 10 items).

The two source files describe the same set of capabilities at different abstraction levels; the user-story criteria are the user-visible behaviors, and the spec Definition of Done adds the verifying-test traceability and the final toolchain gate.

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

The Definition of Done restates each user-story item with explicit verifying test references; the 11th item is the consolidated toolchain check.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | Per-input (LE/AOP/SKU_LU) select Excel file and pick worksheet tab | PASS | `src/gui/widgets/source_input_widget.py`, `src/gui/presenters/source_selection_presenter.py`, `src/gui/services/workbook_reader.py`. Tests: `tests/gui/test_source_input_widget.py`, `tests/gui/test_source_selection_presenter.py`, `tests/gui/test_workbook_reader.py`. | `QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_source_input_widget.py tests/gui/test_source_selection_presenter.py tests/gui/test_workbook_reader.py` — pass within the 333-test suite. | The per-input `file_selected` signal is connected to the source-selection presenter in `build_application` (lines 302-307), so this AC is satisfied through the wired production path. |
| 2 | Selecting an Excel file populates a tab-list dropdown | PASS | `SourceSelectionPresenter.on_file_selected` calls `WorkbookReader.get_sheet_names` and pushes to `view.set_tab_list`. Tests cover the happy path and the exception path. | Same pytest invocation as item 1. | Production-wired: `window.le_widget.file_selected.connect(le_presenter.on_file_selected)` (and the two siblings) in `build_application`. |
| 3 | Optional per-input "render tab" checkbox shows a preview | PASS | `src/gui/widgets/preview_widget.py` + `SourceSelectionPresenter.on_render_tab`. Tests: `tests/gui/test_preview_widget.py`. | Same pytest invocation as item 1. | Production-wired: `window.le_widget.render_tab_requested.connect(le_presenter.on_render_tab)` (and the two siblings) in `build_application`. |
| 4 | Import one or all selected files | PASS | `PipelinePresenter.on_import_one` and `on_import_all`; service methods `import_le`, `import_aop`, `import_skulu`, `import_sources`. Tests cover the presenter directly, through the integration scenario, AND through the wired production signal path. | `QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_pipeline_presenter.py tests/gui/test_pipeline_service.py tests/gui/test_app_wiring.py` (all pass) | Production-wired (post-remediation): `MainWindow.import_one_requested` and `import_all_requested` signals are connected to `pipeline_presenter.on_import_one` / `on_import_all` via `wire_control_signals` in `build_application`. Verified by `test_import_one_signal_routes_to_presenter_with_live_spec` and `test_import_all_signal_routes_to_presenter` in `tests/gui/test_app_wiring.py`. The wiring also reads the live widget state into the `ImportSpec` at emit time (verified by `test_wire_helper_reads_live_widget_state_into_spec`). |
| 5 | Run button executes the pipeline and reports success/failure | PASS | `PipelinePresenter.on_run` (synchronous) and `make_run_task` + `apply_run_result` + `PipelineWorker` (off-UI-thread). Tests: `test_pipeline_presenter.py`, `test_pipeline_worker.py`, `test_pipeline_service.py`, `test_app_wiring.py`. | Same pytest invocation as item 4. | Production-wired (post-remediation): `MainWindow.run_requested` is connected to `pipeline_presenter.on_run` via `wire_control_signals`. Verified by `test_run_signal_routes_to_presenter_when_imports_present` and `test_run_signal_with_no_imports_surfaces_guard_error` (Run-guard path). The production composition uses the synchronous `on_run` path; the worker path remains available for callers that explicitly route through it (tested by `test_pipeline_worker.py`). |
| 6 | Save button persists to a SQLite `.db` | PASS | `PipelinePresenter.on_save` -> `PipelineService.save_to_db` -> `DbService.save_tables` over `src/pandas_io.py`. Tests: `test_pipeline_presenter.py`, `test_pipeline_service.py`, `test_db_service.py`, `test_app_wiring.py`. | Same pytest invocation as item 4. | Production-wired (post-remediation): `MainWindow.save_requested` is connected via `wire_control_signals` and routes through `save_path_chooser` (default-backed by `QFileDialog.getSaveFileName`) before calling `pipeline_presenter.on_save(path)`. Verified by `test_save_signal_routes_to_presenter_with_chosen_path` (happy path) and `test_save_signal_skips_presenter_when_chooser_cancels` (cancel path). |
| 7 | Open button loads tables from an existing `.db` | PASS | `PipelinePresenter.on_open_db` -> `PipelineService.open_db` -> `DbService.open_tables`. Tests: `test_pipeline_presenter.py`, `test_db_service.py`, `test_app_wiring.py`. | Same pytest invocation as item 4. | Production-wired (post-remediation): `MainWindow.open_db_requested` is connected via `wire_control_signals` and routes through `open_path_chooser` (default-backed by `QFileDialog.getOpenFileName`). Verified by `test_open_db_signal_routes_to_presenter_and_records_path` and `test_open_db_signal_skips_presenter_when_chooser_cancels`. |
| 8 | Export to Excel and CSV with checklist and export-all; extensible | PASS | `ExportPresenter`, `ExporterRegistry`, `ExcelExporter`, `CsvExporter`, `ExportDialog`. Tests: `test_export_presenter.py`, `test_exporter_registry.py`, `test_excel_exporter.py`, `test_csv_exporter.py`, `test_export_dialog.py`, `test_app_wiring.py`. | `QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_export_presenter.py tests/gui/test_exporter_registry.py tests/gui/test_excel_exporter.py tests/gui/test_csv_exporter.py tests/gui/test_export_dialog.py tests/gui/test_app_wiring.py` — all pass. | Production-wired (post-remediation): `MainWindow.export_requested` is connected via `wire_control_signals` to a handler that runs the export dialog through `export_dialog_runner` (default-backed by `dialog.exec()` + `QFileDialog.getSaveFileName`), selects derived tables (post-run) or imported tables (pre-run), populates the export presenter via `set_available_tables`, and calls `on_export(tables, format_name, destination_path)`. Verified by `test_export_signal_invokes_exporter_on_full_selection` (post-run path), `test_export_signal_uses_imported_tables_when_no_run` (pre-run fallback), and `test_export_signal_skips_exporter_when_dialog_cancels` (cancel path). Extensibility is verified by the registry-driven design (existing tests). |
| 9 | Presentation logic separable from Qt; services injected; widgets tested with Qt facility | PASS | All three presenters live in `src/gui/presenters/**` and import no Qt symbols at runtime. Presenter tests do not request `qapp` or `qtbot`. Widget tests use `pytest-qt` `qtbot` under `QT_QPA_PLATFORM=offscreen`. The new `wire_control_signals` helper is a small composition seam that injects `Callable` choosers/runners rather than calling `QFileDialog` statics directly, which preserves the architectural separation. | Verified by grep over `src/gui/presenters/**`: no `PySide6` import. | The chooser/runner injection seams allow non-Qt composition variants (for example, a headless CLI mode that supplies argument-driven choosers) without modifying the helper. |
| 10 | Full toolchain (Black, Ruff, Pyright strict, Pytest) passes; coverage meets repo thresholds | PASS | Reviewer-reproduced live this audit: Black "92 files would be left unchanged"; Ruff "All checks passed!"; Pyright "0 errors, 0 warnings, 0 informations"; Pytest "333 passed in 18.38s"; coverage 1793/1793 line (100%) and 262/262 branch (100%). Persisted artifacts: `evidence/qa-gates/qa-gate.2026-05-28T12-30.md` records the same verdict post-remediation. | `poetry run black --check .`, `poetry run ruff check .`, `poetry run pyright`, `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term`. | Thresholds (line >= 85%, branch >= 75%) cleared with substantial margin. New code (the wiring helper and three default choosers/runners) at 100% line / 100% branch. |

---

## Summary

**Overall Feature Readiness:** PASS — every acceptance criterion is satisfied at both the contract level and the production-wired level. The button-wiring gap recorded in the prior audit is closed; the unauthorized `# noqa: N802` is removed; the PR-context artifacts are current.

**Criteria summary:**
- **PASS:** 10 criteria (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing full PASS:** None at the acceptance-criteria level.

**Non-blocking observations (already detailed in `policy-audit.2026-05-28T13-15.md` and `code-review.2026-05-28T13-15.md`):**

1. `tests/gui/test_app_wiring.py` at 561 lines exceeds the 500-line policy cap by 61 lines. The file is well-organized and the violation is a maintainability concern, not an acceptance-criteria gap. Optional follow-up: split into two files along the natural seam (signal-routing tests vs default chooser/runner tests).
2. T2 property test density on `pipeline_service.py`, `exporters/registry.py`, `exporters/base.py` remains an INFO-level note. Not required for AC PASS.
3. `PipelineWorker.run` broad-catch remains an INFO-level note. Documented worker boundary; within policy guidance.

**Recommended follow-up verification steps:**

1. Optional: split `tests/gui/test_app_wiring.py` into two files to bring each under 500 lines.
2. Optional: file a follow-up issue for the T2 property test density note (an `ExporterRegistry.register/get/available_formats` round-trip property test is the natural candidate).

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules, AC source files use markdown checkboxes that the executor pre-checked during plan execution.

For this final audit, the reviewer has confirmed that every acceptance criterion is PASS at both the contract and the production-wired level. The persisted `[x]` checkboxes in `user-story.md` and `spec.md` accurately reflect the implementation state and require no modification.

### AC Status Summary

- Source: `docs/features/active/2026-05-27-mix-pipeline-gui-19/spec.md` (Definition of Done, 11 items) and `docs/features/active/2026-05-27-mix-pipeline-gui-19/user-story.md` (## Acceptance Criteria, 10 items).
- Total AC items: 21 (10 user-story + 11 spec DoD).
- Checked off in source files (executor-recorded): 21.
- Reviewer disposition this run: PASS on all 21 at both contract and production-wired levels.
- Items remaining: 0.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `docs/features/active/2026-05-27-mix-pipeline-gui-19/user-story.md` | 10 | 10 | 0 | All items already `[x]`. Reviewer verified each maps to a PASS in this audit at both contract and production-wired levels. |
| `docs/features/active/2026-05-27-mix-pipeline-gui-19/spec.md` | 11 | 11 | 0 | All items already `[x]`. Reviewer verified each maps to a PASS in this audit at both contract and production-wired levels. The 11th item (full toolchain + coverage thresholds) is the consolidated toolchain check, covered by item 10 in the user-story set and confirmed by the live toolchain run in this audit. |

The reviewer did not change source-file checkbox state. `issue.md` `## Acceptance Criteria (early draft)` is a secondary view and is not authoritative for full-feature work; its checkboxes are also all `[x]`.
