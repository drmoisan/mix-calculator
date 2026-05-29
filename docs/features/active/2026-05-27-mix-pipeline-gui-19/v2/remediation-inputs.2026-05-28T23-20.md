# Remediation Inputs — mix-pipeline-gui v2 (Issue #19)

- **Timestamp:** 2026-05-28T23-20
- **Source artifacts:**
  - `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/policy-audit.2026-05-28T23-20.md`
  - `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/code-review.2026-05-28T23-20.md`
  - `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/feature-audit.2026-05-28T23-20.md`
- **Handoff:** strict-handoff protocol; the orchestrator will route through `atomic-planner` (no bypass).

## Blocking Remediation Items

### R-1: Behavioral CSV export test leaks real CSV files into the repository working directory

- **AC affected:** AC-9 (Export).
- **File:** `tests/gui/integration/test_behavioral_dialogs.py`
- **Function:** `test_export_csv_routes_destination_to_csv_exporter`
- **Lines:** 150-181
- **Defect text:**

  ```python
  def _runner(dialog: ExportDialog) -> tuple[str, str] | None:
      dialog.select_all_tables()
      return "CSV", "results.csv"

  fake_reader = FakeWorkbookReader(sheet_names=["AOP1"])
  wired = build_application(
      runner=SynchronousRunner(),
      pipeline_service=service,
      workbook_reader=fake_reader,
      save_path_chooser=lambda: None,
      open_path_chooser=lambda: None,
      export_dialog_runner=_runner,
  )
  qtbot.addWidget(wired.window)
  wired.pipeline_presenter.set_imported_tables_for_test(_fake_imports())

  _click(qtbot, wired.window.export_btn)
  ```

- **Why it is a defect:** `build_application` constructs the real `CsvExporter` with the default `_default_open_writer`, which calls `open(path, "w", encoding="utf-8", newline="")`. Clicking `export_btn` with the runner returning `"results.csv"` writes `results_LE.csv`, `results_aop.csv`, and `results_sku_lu.csv` to the test's working directory (the repository root in normal `pytest` invocation). The files are observed in `git status` as untracked artifacts after a test run.
- **Policy violations:**
  1. `.claude/rules/general-unit-test.md`: "Creation and use of temporary files in tests is strictly prohibited."
  2. `.claude/rules/python.md`: "No external dependencies (network, databases, external processes, runtime filesystem temp files) in unit tests."
  3. `v2/spec.md` Constraints & Risks: "Testability without temp files (unchanged from v1). No runtime temp files in unit tests."
- **Suggested remediation paths (the planner chooses one):**
  1. **(Preferred)** Extend `build_application` with an optional `exporter_registry: ExporterRegistry | None = None` keyword parameter. When `None`, default to the v1 production registry; tests inject a registry whose `"CSV"` exporter uses an in-memory `open_writer`. Update the behavioral test to inject the in-memory registry and assert the captured per-table writes.
  2. Replace the click-through with a registry-resolution-only assertion (the test already does this at line 181); delete the line `_click(qtbot, wired.window.export_btn)` and the associated arrange code so the test no longer triggers the real `CsvExporter.export` call.
  3. Inject a custom `CsvExporter(open_writer=...)` directly into the existing registry before `build_application` constructs the wired app (requires either a new injection seam or a monkeypatch on `ExporterRegistry`).
- **Acceptance criteria for the remediation:**
  - The behavioral test for the CSV export click path completes without creating any file on disk.
  - `git status` after the test run shows no untracked `results_*.csv` (or other test-output) files.
  - The user-visible AC-9 surface (registry resolves `"CSV"`, exporter writes per-table files at the configured destination, name-mangling rule) remains verified by `tests/gui/test_csv_exporter.py` and a registry-resolution assertion in the behavioral test.
  - All other v2 tests continue to pass; coverage thresholds (line >= 85%, branch >= 75%) hold.
  - Black, Ruff, and Pyright strict remain at 0/0/0.

## Recommended Non-Blocking Follow-ups (optional for the planner)

The items below are not required for the remediation loop to pass but improve
the v2 surface and may be bundled by the planner if scope allows. None of
these is a merge blocker.

- Remove the production-source test seam `PipelinePresenter.set_imported_tables_for_test` and refactor behavioral tests to bootstrap state via the standard `on_import_one` / `on_open_db` paths.
- Add a small `logger.warning` in `default_export_runner` when the selected filter string matches neither `"*.xlsx"` nor `"*.csv"` (currently a silent default to `"Excel"`).
- Plan a future split of `src/gui/app.py` (492/500 lines) and `src/gui/presenters/pipeline_presenter.py` (496/500 lines) before the next composition or presenter change to preserve cap headroom.
- Reword the docstring on `test_export_csv_routes_destination_to_csv_exporter` to match the assertion that is actually performed (registry resolution, not name-mangling end-to-end).

## Out-of-Scope for Remediation

- Any change to `v1/` artifacts (the v1 audit and evidence set must not be modified).
- Any change to `.github/workflows/_python-quality.yml` (no new v2 workflow drift was introduced; the existing diff is from v1 remediation).
- Any change to pure-transform modules (`src/mix_pipeline.py`, `src/mix_pipeline_run.py`, `src/mix_lookups.py`, `src/mix_transforms.py`).
