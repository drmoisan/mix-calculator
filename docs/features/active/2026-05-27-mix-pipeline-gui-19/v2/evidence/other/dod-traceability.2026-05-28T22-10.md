# DoD Traceability Matrix — v2

Timestamp: 2026-05-28T22-10

Each acceptance criterion in `v2/issue.md` is verified by at least one passing
unit/integration test and (where applicable) at least one behavioral
integration test under `tests/gui/integration/`. The confidentiality invariant
(no `SKU Description`, `Category`, customer names, real SKU numbers, prices, or
discounts) has been confirmed across every new source, test, fixture, and doc
file in v2: only fabricated values such as `"SKU-001"`, `"k1"`, `"AOP1"`,
`"LE-8 + 4"`, and `"results.csv"` appear.

## Mapping

| AC | Verifying unit/integration test(s) | Verifying behavioral test (tests/gui/integration/) | Status |
|---|---|---|---|
| AC-1 Render Tab renders an image of the selected worksheet | `tests/gui/test_source_selection_presenter.py` (`preview_sink` paths), `tests/gui/test_source_input_widget.py` (`_on_tab_changed` slot), `tests/gui/test_preview_widget.py` (unchanged from v1) | `tests/gui/integration/test_behavioral_preview.py` (5 tests covering toggle-on, tab-change, toggle-off cycles for LE, AOP, SKU_LU) | PASS |
| AC-2 Import LE wires to pipeline and disables on success | `tests/gui/test_pipeline_presenter_v2.py` (`on_import_one` LE, file-path tracking) | `tests/gui/integration/test_behavioral_import_buttons.py` (LE success, same-path no-op, different-path re-enable, LE failure leaves button enabled) | PASS |
| AC-3 Import AOP wires to pipeline and disables on success | `tests/gui/test_pipeline_presenter_v2.py` (AOP path tracking) | `tests/gui/integration/test_behavioral_import_buttons.py` (AOP success, different-path re-enable) | PASS |
| AC-4 Import SKU_LU wires to pipeline and disables on success | `tests/gui/test_pipeline_presenter_v2.py` (SKU_LU path tracking), `tests/gui/test_pipeline_service.py` (unchanged SKU_LU default behavior) | `tests/gui/integration/test_behavioral_import_buttons.py` (SKU_LU success, different-path re-enable) | PASS |
| AC-5 Import All runs all three and disables all four | `tests/gui/test_pipeline_presenter_v2.py` (`on_import_all` full success, path recording for all three keys) | `tests/gui/integration/test_behavioral_import_buttons.py` (full-success disables all four, LE re-enable after Import-All restores LE and Import-All) | PASS |
| AC-6 Run executes transformation end-to-end | `tests/gui/test_runners.py` (`SynchronousRunner` success/error routing, `ThreadedRunner` protocol structural check), `tests/gui/test_pipeline_presenter_v2.py` (`on_run_success`, `on_run_error` callbacks), `tests/gui/test_pipeline_worker.py` (unchanged off-thread proof) | `tests/gui/integration/test_behavioral_pipeline_run.py` (Run records derived tables, Run failure preserves imports) | PASS |
| AC-7 Save persists working tables to SQLite `.db` | `tests/gui/test_pipeline_presenter.py` (Save flow using working_tables), `tests/gui/test_app_wiring.py` (chooser injection) | `tests/gui/integration/test_behavioral_dialogs.py` (Save with chosen path, cancel) | PASS |
| AC-8 Open loads tables and reflects load state | `tests/gui/test_pipeline_presenter_v2.py` (Open sets `db:<path>` sentinel and pushes button states; subsequent file-path change re-enables only the matching key) | `tests/gui/integration/test_behavioral_dialogs.py` (Open disables imports and enables Run, LE path change re-enables LE/All only) | PASS |
| AC-9 Export opens dialog and exports through registry | `tests/gui/test_export_dialog.py` (combo removed, checklist populates), `tests/gui/test_app_wiring_defaults.py` (Excel/CSV filter parse), `tests/gui/test_csv_exporter.py` (name-mangling rule), `tests/gui/test_export_presenter.py` (unchanged) | `tests/gui/integration/test_behavioral_dialogs.py` (set_available_tables called before runner; CSV path routes through registry; empty working set produces empty checklist) | PASS |
| AC-10 Composition root wires all signals | `tests/gui/test_app_wiring.py` (build_application injection: runner/choosers/services), `tests/gui/test_app_composition.py` (SynchronousRunner smoke + registry formats) | `tests/gui/integration/test_behavioral_composition.py` (every control button reachable as public attribute; clicking Run/Save/Open/Export/ImportAll does not raise) | PASS |
| AC-11 Presentation logic testable without a live Qt event loop | All `test_*_presenter.py` files run without a `QApplication`; `tests/gui/test_runners.py` SynchronousRunner tests run without a `QApplication`; pyright-strict enforces no `Any` introduction | n/a (unit invariant; confirmed by passing test suite under offscreen) | PASS |
| AC-12 Full toolchain passes and coverage thresholds hold | `v2/evidence/qa-gates/final-black.2026-05-28T22-10.md`, `final-ruff.2026-05-28T22-10.md`, `final-pyright.2026-05-28T22-10.md`, `final-pytest-coverage.2026-05-28T22-10.md`, `coverage-delta.2026-05-28T22-10.md` | n/a (gate) | PASS |

## Confidentiality invariant

Confirmed across every new source, test, fixture, and doc file in v2. Every
fabricated value uses placeholders such as `Acme Foods`, `SKU-1001`,
`Example-A`, `Category X` (none appear in v2), or simple keys (`k1`, `AOP1`,
`LE-8 + 4`, `results.csv`). The `Country` values `US` and `Canada` are not
secret (they are valid in test data per the spec).

## Outcome

All AC-1 through AC-12 verified; no DoD item unverified. The confidentiality
invariant holds across the entire v2 contribution.
