Timestamp: 2026-05-28T23-20

# v2 Definition of Done — Post-Remediation Traceability

| AC | Title | Verifying unit / widget test(s) | Verifying behavioral integration test(s) | Pass |
|---|---|---|---|---|
| AC-1 | Render Tab renders an image of the selected worksheet | `tests/gui/test_source_selection_presenter.py`, `tests/gui/test_source_input_widget.py`, `tests/gui/test_preview_widget.py` | `tests/gui/integration/test_behavioral_preview.py` | yes |
| AC-2 | Import LE wires to pipeline and disables on success | `tests/gui/test_pipeline_presenter.py` | `tests/gui/integration/test_behavioral_import_buttons.py` | yes |
| AC-3 | Import AOP wires to pipeline and disables on success | `tests/gui/test_pipeline_presenter.py` | `tests/gui/integration/test_behavioral_import_buttons.py` | yes |
| AC-4 | Import SKU_LU wires to pipeline and disables on success | `tests/gui/test_pipeline_presenter.py` | `tests/gui/integration/test_behavioral_import_buttons.py` | yes |
| AC-5 | Import All runs all three imports and disables all four | `tests/gui/test_pipeline_presenter.py` | `tests/gui/integration/test_behavioral_import_buttons.py` | yes |
| AC-6 | Run executes transformation end-to-end | `tests/gui/test_runners.py`, `tests/gui/test_pipeline_presenter.py`, `tests/gui/test_pipeline_worker.py`, `tests/gui/test_pipeline_service.py` | `tests/gui/integration/test_behavioral_pipeline_run.py` (Cycle-1: imports now bootstrap via `on_import_all(_import_spec())`) | yes |
| AC-7 | Save persists working tables to SQLite `.db` | `tests/gui/test_pipeline_presenter.py`, `tests/gui/test_app_wiring.py` | `tests/gui/integration/test_behavioral_dialogs.py::test_save_button_calls_service_with_working_tables`, `test_save_cancel_records_no_call` (Cycle-1: imports bootstrap via `on_import_all`) | yes |
| AC-8 | Open loads tables and reflects load state on import buttons | `tests/gui/test_pipeline_presenter.py`, `tests/gui/test_app_wiring.py` | `tests/gui/integration/test_behavioral_dialogs.py::test_open_button_loads_tables_and_disables_imports`, `test_open_then_le_path_change_re_enables_le_button` | yes |
| AC-9 | Export opens file dialog with Excel/CSV format choices and exports through registry | `tests/gui/test_export_dialog.py`, `tests/gui/test_app_wiring_defaults.py`, `tests/gui/test_csv_exporter.py` (name-mangling unit contract), `tests/gui/test_export_presenter.py`, `tests/gui/test_app_wiring.py::test_build_application_uses_injected_exporter_registry` (Cycle-1: registry injection seam) | `tests/gui/integration/test_behavioral_dialogs.py::test_export_csv_routes_destination_to_csv_exporter` — **disk-free**; per-table writes captured via injected in-memory `open_writer` (Cycle-1 rewrite) | yes |
| AC-10 | Composition root wires all signals to behavioral handlers | `tests/gui/test_app_wiring.py`, `tests/gui/test_app_composition.py` | `tests/gui/integration/test_behavioral_composition.py` | yes |
| AC-11 | Presentation logic remains testable without a live Qt event loop | every `tests/gui/test_*_presenter.py`; `tests/gui/test_runners.py` (Cycle-1 strengthening: production-source test seam `PipelinePresenter.set_imported_tables_for_test` removed; all behavioral tests now bootstrap via the standard injectable service path) | n/a (unit invariant) | yes |
| AC-12 | Full toolchain passes and coverage thresholds hold | `v2/evidence/qa-gates/final-black.2026-05-28T23-20.md`, `final-ruff.2026-05-28T23-20.md`, `final-pyright.2026-05-28T23-20.md`, `final-pytest-coverage.2026-05-28T23-20.md`, `coverage-delta.2026-05-28T23-20.md` | n/a (gate) | yes |

## Cycle-1 specific notes

- **AC-9 disk-free verification path:** the rewritten behavioral test
  injects an `ExporterRegistry` whose `"CSV"` entry is a
  `CsvExporter(open_writer=_capture_open_writer)`. The capture closure
  routes each per-table write into a `_CapturingStringIO` that snapshots
  its content into `captured_writes` on `close()`. Assertions verify:
  (a) the per-table file name set `{results_LE.csv, results_aop.csv,
  results_sku_lu.csv}` under `C:/tmp` (built via `os.path.join`); and
  (b) each captured payload is non-empty.
- **AC-11 strengthening:** the production-source seam
  `PipelinePresenter.set_imported_tables_for_test` was removed in P2-T1.
  All six previous call sites across the two integration test files now
  bootstrap state through `pipeline_presenter.on_import_all(_import_spec())`,
  routed through `FakePipelineService.import_sources`.
- **Confidentiality:** All modified test files use only fabricated values
  (`SKU-001`, `k1`, fictitious workbook paths like `le.xlsx`). No real
  `SKU Description`, `Category`, customer, SKU number, price, or discount
  values appear in the diff. Verified by spot-check.

## Outcome

Every AC-1 through AC-12 is verified by at least one passing test in the
post-remediation toolchain run. AC-9's behavioral row records the disk-free
verification path. No DoD item is unverified.
