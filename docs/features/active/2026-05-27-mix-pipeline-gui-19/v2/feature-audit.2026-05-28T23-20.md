# Feature Audit — mix-pipeline-gui v2 (Issue #19)

- **Timestamp:** 2026-05-28T23-20
- **Branch:** feature/mix-pipeline-gui-19
- **AC Source (mode-resolved):** `v2/issue.md` (authoritative checkbox set), cross-referenced with `v2/spec.md` Definition of Done and `v2/user-story.md`.
- **Work Mode:** full-feature.

## Scope and Baseline

Audit scope: the full feature branch working-tree state vs. the resolved
base branch `main` (merge-base used by the PR context generators). The v2
execution layer is additive over the v1 PR #24 module set; no v1 commit is
reverted. The acceptance criteria evaluated below are taken verbatim from
`v2/issue.md` and cross-referenced with the Definition of Done table in
`v2/spec.md` and the persona walkthroughs in `v2/user-story.md`. Baseline
coverage (P0-T5) and post-change coverage (P11-T4) are read from the
canonical v2 evidence artifacts.

## Acceptance Criteria Inventory

The v2 acceptance criteria source (`v2/issue.md`) lists twelve criteria:

- AC-1 Render Tab renders an image of the selected worksheet
- AC-2 Import LE wires to the pipeline and disables on success
- AC-3 Import AOP wires to the pipeline and disables on success
- AC-4 Import SKU_LU wires to the pipeline and disables on success
- AC-5 Import All runs all three imports and disables all four
- AC-6 Run executes the transformation end-to-end and updates state
- AC-7 Save persists the working tables to a SQLite `.db`
- AC-8 Open loads tables from a `.db` and reflects load state
- AC-9 Export opens a file dialog and exports through the registry
- AC-10 Composition root wires all signals to behavioral handlers
- AC-11 Presentation logic remains testable without a live Qt event loop
- AC-12 Full toolchain passes and coverage thresholds hold

## Acceptance Criteria Evaluation

See the AC Evaluation Table below.

## Method

Each acceptance criterion is evaluated against the working-tree code under
`src/gui/` and the test surface under `tests/gui/` (including
`tests/gui/integration/`). Coverage and toolchain evidence is read from the
v2 evidence artifacts under
`docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/`. Where the
working-tree behavior is unambiguous from code and tests, the AC is verified
as PASS; where a delivery exists but is partially defective, the AC is
flagged PARTIAL; otherwise FAIL or UNVERIFIED.

## AC Evaluation Table

| AC | Title | Implementation evidence (production) | Behavioral evidence (test) | Verdict |
|---|---|---|---|---|
| AC-1 | Render Tab renders an image of the selected worksheet | `src/gui/widgets/source_input_widget.py` `_on_tab_changed`; `src/gui/presenters/source_selection_presenter.py` `preview_sink` parameter and `on_render_tab`; `src/gui/app.py` wires `window.preview_widget` as `preview_sink` and connects checkbox-toggled-False to `preview_widget.show_preview([])` | `tests/gui/integration/test_behavioral_preview.py` (toggle-on, tab-change, toggle-off across LE/AOP/SKU_LU); `tests/gui/test_source_input_widget.py`; `tests/gui/test_source_selection_presenter.py` | PASS |
| AC-2 | Import LE wires to pipeline and disables on success | `src/gui/presenters/pipeline_presenter.py` `on_import_one` updates `_imported_tables`, sets `_last_imported_path["LE"]`, calls `set_import_button_enabled("LE", False)`; `MainWindowPipelineView` routes to `import_le_btn` | `tests/gui/integration/test_behavioral_import_buttons.py` (LE click, same-path no-op, different-path re-enable, ValueError leaves enabled); `tests/gui/test_pipeline_presenter_v2.py` | PASS |
| AC-3 | Import AOP wires to pipeline and disables on success | Same `on_import_one` path with `key="aop"`; adapter routes to `import_aop_btn` | `tests/gui/integration/test_behavioral_import_buttons.py` (AOP path); `tests/gui/test_pipeline_presenter_v2.py` | PASS |
| AC-4 | Import SKU_LU wires to pipeline and disables on success | Same `on_import_one` path with `key="sku_lu"`; SKU_LU workbook defaults to LE/AOP retained from v1 in `SourceSelectionPresenter`/`PipelineService` | `tests/gui/integration/test_behavioral_import_buttons.py` (SKU_LU path); `tests/gui/test_pipeline_presenter_v2.py`; `tests/gui/test_pipeline_service.py` (unchanged from v1 default-path coverage) | PASS |
| AC-5 | Import All runs all three and disables all four | `src/gui/presenters/pipeline_presenter.py` `on_import_all` iterates three loaders, on full success calls `set_import_button_enabled(key, False)` per key; `MainWindowPipelineView` recomputes `import_all_btn` as `any(...)`; on partial success only successful keys disabled | `tests/gui/integration/test_behavioral_import_buttons.py` (full-success disables four; LE re-enable restores LE and Import-All; partial-success leaves Import-All enabled); `tests/gui/test_pipeline_presenter_v2.py` | PASS |
| AC-6 | Run executes the transformation end-to-end and updates state | `src/gui/runners.py` `RunnerProtocol` / `ThreadedRunner` / `SynchronousRunner`; `src/gui/app.py` `_handle_run` dispatches `runner.run(task, on_success, on_error)`; `pipeline_presenter.on_run_success` populates `_derived_tables` and re-enables Run; `on_run_error` surfaces and re-enables | `tests/gui/integration/test_behavioral_pipeline_run.py` uses `SynchronousRunner` injection and asserts `derived_tables` immediately after click (no polling); failure-path preserves imports; `tests/gui/test_runners.py` covers SynchronousRunner success/error; `tests/gui/test_pipeline_worker.py` retains the off-thread proof | PASS |
| AC-7 | Save persists working tables to SQLite `.db` | `src/gui/app.py` `_handle_save` reads `pipeline_presenter.working_tables` and calls `pipeline_presenter.on_save(path)`; `pipeline_presenter.on_save` routes through `PipelineService.save_to_db` (unchanged v1); enable-state pushed via `set_save_button_enabled`; cancel returns early on empty path | `tests/gui/integration/test_behavioral_dialogs.py` (Save with chosen path, cancel, disabled-when-empty); `tests/gui/test_pipeline_presenter.py`; `tests/gui/test_app_wiring.py` | PASS |
| AC-8 | Open loads tables and reflects load state on import buttons | `src/gui/presenters/pipeline_presenter.py` `on_open_db` calls `set_import_button_enabled(key, False)` per loaded key, sets `_last_imported_path[key] = f"db:{path}"`, calls `set_run_button_enabled(True)` when any loaded | `tests/gui/integration/test_behavioral_dialogs.py` (Open disables all imports, enables Run, LE path change re-enables LE/Import-All only); `tests/gui/test_pipeline_presenter_v2.py` | PASS |
| AC-9 | Export opens dialog with Excel/CSV format choices and exports through registry | `src/gui/app.py` `_handle_export` calls `set_available_tables(...)` BEFORE `export_dialog_runner(dialog)` (Defect 1 fix); `src/gui/_wiring.py` `default_export_runner` uses `"Excel (*.xlsx);;CSV (*.csv)"` filter and parses selected filter (Defect 2 fix); `src/gui/widgets/export_dialog.py` format combo removed; `src/gui/exporters/csv_exporter.py` implements `<base>_<table>.csv` mangling (Defect 3 fix) | `tests/gui/test_csv_exporter.py` (mangling rule, six scenarios, in-memory writer); `tests/gui/test_app_wiring_defaults.py` (filter parse for Excel and CSV); `tests/gui/test_export_dialog.py` (checklist; combo removed); `tests/gui/integration/test_behavioral_dialogs.py` (checklist before dialog; CSV path resolves through registry; empty-set empty-checklist) | PARTIAL — see note below |
| AC-10 | Composition root wires all signals to behavioral handlers | `src/gui/app.py` `build_application` constructs real collaborators, wires every `MainWindow` signal, supports injection of runner and choosers; `WiredApplication` exposes `runner` | `tests/gui/integration/test_behavioral_composition.py` (every control button reachable; clicks do not raise); plus the full `tests/gui/integration/` suite asserting AC-1..AC-9 by clicking actual buttons | PASS |
| AC-11 | Presentation logic remains testable without a live Qt event loop | Every presenter under `src/gui/presenters/` has no Qt import (verified by grep); `tests/gui/test_runners.py` SynchronousRunner tests run without a `QApplication`; `pytest` collects all unit tests under `QT_QPA_PLATFORM=offscreen` | All `test_*_presenter.py` files run without instantiating `QApplication`; `tests/gui/test_runners.py` SynchronousRunner tests likewise | PASS |
| AC-12 | Full toolchain passes and coverage thresholds hold | Black 0 / Ruff 0 / Pyright strict 0/0/0 / Pytest 416 passed; coverage 99% line, 99% branch; coverage-delta confirms no regression on changed lines | `v2/evidence/qa-gates/final-black.2026-05-28T22-10.md`, `final-ruff`, `final-pyright`, `final-pytest-coverage`, `coverage-delta` | PASS |

### AC-9 PARTIAL note

The Export functional surface is delivered: dialog ordering, filter string,
combo removal, and CSV name-mangling all match the spec. The behavioral test
that exercises the CSV click path
(`test_export_csv_routes_destination_to_csv_exporter`) writes real files to
the working directory because the wired `CsvExporter` is the production
instance with a real-file `open_writer`. This is a test-isolation defect, not
a production-surface defect. The user-visible behavior of AC-9 is delivered
and demonstrable; the verification path violates the no-temp-files invariant.
AC-9 is PARTIAL pending the remediation called out in the policy audit and
code review.

## Acceptance Criteria Check-off

The AC source file (`v2/issue.md`) already shows all twelve criteria
checked-off by the executor. Per the acceptance-criteria-tracking skill, the
reviewer leaves check-offs intact when an AC verdict is PASS and flags any
PARTIAL/FAIL/UNVERIFIED items for the source file. AC-9 is PARTIAL; the
issue checkbox remains as the executor set it, with the partial-status note
recorded here. No source-file edits are required from this audit.

## DoD Traceability

Each AC maps to at least one passing test at both the unit/integration level
and (where applicable) the behavioral integration level, per the
`dod-traceability.2026-05-28T22-10.md` artifact. The mapping is consistent
with the production code reviewed in this audit.

## Out-of-Scope Confirmation

- `src/mix_pipeline.py` (CLI), `src/mix_pipeline_run.py`, `src/mix_lookups.py`,
  `src/mix_transforms.py`: unchanged (verified via diff).
- No packaging or installer changes.
- No exporter formats beyond Excel and CSV added.
- No revert of v1 PR #24; v2 is additive over the v1 module set.

## Working-Set Semantics

`PipelinePresenter.working_tables` is defined as
`self._derived_tables if self._derived_tables else self._imported_tables`
and is used by `on_save`, `_handle_export`, and `can_run`. Derived-table
invalidation on new import (`_derived_tables = {}`) is implemented in
`on_import_one` and `on_import_all` per spec.

## Confidentiality

All new test data uses fabricated values (`SKU-001`, `k1`, `AOP1`,
`LE-8 + 4`, `results.csv`). No `SKU Description`, `Category`, customer names,
SKU numbers, prices, or discounts appear in any new file.

## Acceptance Criteria Status

- Source: `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/issue.md`
- Total AC items: 12
- Checked off (delivered): 11 (PASS at both unit/integration and behavioral levels)
- PARTIAL: 1 (AC-9: surface delivered, behavioral test violates temp-file invariant)
- Items remaining: AC-9 verification path requires remediation; no AC remains structurally undelivered.

## Overall Feature Verdict

**PARTIAL** — the user-visible v2 surface (button-driven behavior of the
mix-pipeline GUI) is delivered as specified. The one Blocking defect is in
the verification surface for AC-9 (test pollution via real CSV file writes
during a behavioral test), not in the production behavior of Export. With
that defect fixed, the feature passes.

## Summary

- Total acceptance criteria: 12.
- PASS: 11 (AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-10, AC-11, AC-12).
- PARTIAL: 1 (AC-9 — production surface delivered; behavioral verification path violates the no-temp-files invariant).
- FAIL: 0.
- UNVERIFIED: 0.
- Recommendation: REMEDIATE — fix the AC-9 verification path, then merge.
