# Feature Audit — mix-pipeline-gui v2 EXIT (Issue #19)

- **Timestamp:** 2026-05-29T00-02
- **Cycle:** 1 EXIT audit (post-remediation)
- **Branch:** feature/mix-pipeline-gui-19
- **AC Source (mode-resolved):** `v2/issue.md` (authoritative checkbox set), cross-referenced with `v2/spec.md` Definition of Done and `v2/user-story.md`.
- **Work Mode:** full-feature.

## Scope and Baseline

Audit scope: the full feature branch working-tree state vs. the resolved base branch `main`, including the cycle-1 remediation. The cycle-1 changes are: (a) an additive `exporter_registry` keyword on `build_application`; (b) removal of `PipelinePresenter.set_imported_tables_for_test`; (c) a rewritten CSV behavioral test using an in-memory `_CapturingStringIO` capture seam; (d) migration of three other behavioral-test call sites to the standard import path; (e) one new positive test for the registry-injection seam. AC verification is taken from `v2/issue.md` and cross-referenced with `v2/spec.md` and `v2/user-story.md`.

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

Each acceptance criterion is evaluated against the working-tree code under `src/gui/` and the test surface under `tests/gui/` (including `tests/gui/integration/`). Coverage and toolchain evidence is read from the cycle-1 post-remediation evidence artifacts under `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/`. The cycle-0 entry audit's PARTIAL verdict on AC-9 was driven solely by the verification-surface defect (disk leak); the cycle-1 remediation closes that defect.

## AC Evaluation Table

| AC | Title | Implementation evidence (production) | Behavioral evidence (test) | Verdict |
|---|---|---|---|---|
| AC-1 | Render Tab renders an image of the selected worksheet | `src/gui/widgets/source_input_widget.py` `_on_tab_changed`; `src/gui/presenters/source_selection_presenter.py` `preview_sink` parameter and `on_render_tab`; `src/gui/app.py` wires `window.preview_widget` as `preview_sink` | `tests/gui/integration/test_behavioral_preview.py`; `tests/gui/test_source_input_widget.py`; `tests/gui/test_source_selection_presenter.py` | PASS |
| AC-2 | Import LE wires to pipeline and disables on success | `src/gui/presenters/pipeline_presenter.py` `on_import_one`; `MainWindowPipelineView` routes to `import_le_btn` | `tests/gui/integration/test_behavioral_import_buttons.py`; `tests/gui/test_pipeline_presenter_v2.py` | PASS |
| AC-3 | Import AOP wires to pipeline and disables on success | Same `on_import_one` path with `key="aop"` | `tests/gui/integration/test_behavioral_import_buttons.py`; `tests/gui/test_pipeline_presenter_v2.py` | PASS |
| AC-4 | Import SKU_LU wires to pipeline and disables on success | Same `on_import_one` path with `key="sku_lu"` | `tests/gui/integration/test_behavioral_import_buttons.py`; `tests/gui/test_pipeline_presenter_v2.py`; `tests/gui/test_pipeline_service.py` | PASS |
| AC-5 | Import All runs all three and disables all four | `on_import_all` iterates loaders; `MainWindowPipelineView` recomputes `import_all_btn` | `tests/gui/integration/test_behavioral_import_buttons.py`; `tests/gui/test_pipeline_presenter_v2.py` | PASS |
| AC-6 | Run executes the transformation end-to-end and updates state | `src/gui/runners.py` `RunnerProtocol` / `ThreadedRunner` / `SynchronousRunner`; `src/gui/app.py` `_handle_run`; `pipeline_presenter.on_run_success`/`on_run_error` | `tests/gui/integration/test_behavioral_pipeline_run.py` (cycle-1 migrated to `on_import_all`/`on_import_one` bootstrap); `tests/gui/test_runners.py`; `tests/gui/test_pipeline_worker.py` | PASS |
| AC-7 | Save persists working tables to SQLite `.db` | `src/gui/app.py` `_handle_save`; `pipeline_presenter.on_save` routes through `PipelineService.save_to_db` | `tests/gui/integration/test_behavioral_dialogs.py` (Save tests bootstrap via `on_import_all`); `tests/gui/test_pipeline_presenter.py`; `tests/gui/test_app_wiring.py` | PASS |
| AC-8 | Open loads tables and reflects load state on import buttons | `pipeline_presenter.on_open_db` | `tests/gui/integration/test_behavioral_dialogs.py`; `tests/gui/test_pipeline_presenter_v2.py` | PASS |
| AC-9 | Export opens dialog with Excel/CSV format choices and exports through registry | `src/gui/app.py` `_handle_export` (Defect 1 fix preserved); `src/gui/_wiring.py` `default_export_runner` (Defect 2 fix preserved); `src/gui/widgets/export_dialog.py` (format combo removed); `src/gui/exporters/csv_exporter.py` (`<base>_<table>.csv` mangling — Defect 3 fix preserved); `src/gui/app.py` `build_application(exporter_registry=...)` injection seam added in cycle 1 | `tests/gui/test_csv_exporter.py`; `tests/gui/test_app_wiring_defaults.py`; `tests/gui/test_export_dialog.py`; `tests/gui/integration/test_behavioral_dialogs.py::test_export_csv_routes_destination_to_csv_exporter` (rewritten in cycle 1 to use in-memory `_CapturingStringIO` capture; no disk writes); `tests/gui/test_app_wiring.py::test_build_application_uses_injected_exporter_registry` (new in cycle 1) | PASS |
| AC-10 | Composition root wires all signals to behavioral handlers | `src/gui/app.py` `build_application` constructs real collaborators, wires every `MainWindow` signal, supports injection of runner, choosers, and (cycle 1) exporter registry | `tests/gui/integration/test_behavioral_composition.py`; the full `tests/gui/integration/` suite | PASS |
| AC-11 | Presentation logic remains testable without a live Qt event loop | Every presenter under `src/gui/presenters/` has no Qt import; `tests/gui/test_runners.py` SynchronousRunner tests run without a `QApplication`. Cycle-1 removal of `set_imported_tables_for_test` strengthens this property by removing a test-only seam from production code. | All `test_*_presenter.py` files run without instantiating `QApplication`; `tests/gui/test_runners.py` likewise | PASS |
| AC-12 | Full toolchain passes and coverage thresholds hold | Black 0 / Ruff 0 / Pyright strict 0/0/0 / Pytest 417 passed; coverage 99% line, 99% branch; coverage-delta confirms no regression on changed lines | `v2/evidence/qa-gates/final-black.2026-05-28T23-20.md`, `final-ruff`, `final-pyright`, `final-pytest-coverage`, `coverage-delta` | PASS |

### AC-9 verdict change (cycle 0 PARTIAL -> cycle 1 PASS)

The cycle-0 entry audit recorded AC-9 as PARTIAL because the production surface was delivered (dialog ordering, filter string, combo removal, CSV name-mangling) but the verification path leaked `results_LE.csv`, `results_aop.csv`, and `results_sku_lu.csv` to the repository working directory. Cycle 1 closes that defect by injecting an `ExporterRegistry` whose `"CSV"` entry is `CsvExporter(open_writer=<in-memory _CapturingStringIO factory>)`. After the rewritten test runs, `captured_writes` holds the three expected per-table paths (`results_LE.csv`, `results_aop.csv`, `results_sku_lu.csv` rooted under `C:/tmp`) with non-empty content, and `git status` shows no untracked files. AC-9 is now PASS at both the surface and the verification levels.

## Acceptance Criteria Check-off

The AC source file (`v2/issue.md`) already shows all twelve criteria checked-off. Per the acceptance-criteria-tracking skill, the reviewer leaves check-offs intact when an AC verdict is PASS. All twelve verdicts are PASS in this EXIT audit; no source-file edits are required.

## DoD Traceability

Each AC maps to at least one passing test at both the unit/integration and behavioral integration levels, per `dod-traceability.2026-05-28T23-20.md`. AC-9's row in that artifact explicitly notes "disk-free; per-table writes captured via injected in-memory `open_writer`."

## Out-of-Scope Confirmation

- `src/mix_pipeline.py` (CLI), `src/mix_pipeline_run.py`, `src/mix_lookups.py`, `src/mix_transforms.py`: unchanged in cycle 1.
- No packaging or installer changes.
- No exporter formats beyond Excel and CSV added.
- No revert of v1 PR #24; v2 (and cycle 1) is additive over the v1 module set.
- No change to `.github/workflows/_python-quality.yml` in cycle 1.

## Working-Set Semantics

Unchanged from cycle-0 entry audit: `PipelinePresenter.working_tables` is `self._derived_tables if self._derived_tables else self._imported_tables` and is used by `on_save`, `_handle_export`, and `can_run`. Derived-table invalidation on new import is implemented.

## Confidentiality

All test data uses fabricated values (`SKU-001`, `k1`, `AOP1`, `LE-8 + 4`, `results.csv`). No `SKU Description`, `Category`, customer names, SKU numbers, prices, or discounts appear in any new file.

## Acceptance Criteria Status

- Source: `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/issue.md`
- Total AC items: 12
- Checked off (delivered): 12
- PARTIAL: 0
- FAIL: 0
- UNVERIFIED: 0
- Items remaining: none

## Overall Feature Verdict

**PASS** — every acceptance criterion is delivered at both the production-surface and the verification-surface levels. Cycle-1 exit condition `blocking_count == 0` is met. Recommendation: MERGE.

## Summary

- Total acceptance criteria: 12.
- PASS: 12 (AC-1 through AC-12).
- PARTIAL: 0.
- FAIL: 0.
- UNVERIFIED: 0.
- Recommendation: MERGE.
