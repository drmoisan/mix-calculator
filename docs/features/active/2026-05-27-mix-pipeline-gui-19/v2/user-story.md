# `2026-05-27-mix-pipeline-gui` — User Story (v2)

- **Issue:** #19
- **Issue URL:** https://github.com/drmoisan/mix-calculator/issues/19
- **Owner:** drmoisan
- **Status:** Active
- **Version:** 2.0
- **Last Updated:** 2026-05-28
- **Supersedes:** Version 1.0 (delivered under PR #24 with passing unit tests and 100% coverage but with the assembled application's buttons not delivering the user-facing behaviors).

## Story Statement

- As a finance analyst who does not use the command line, I want to select my
  source workbooks and worksheet tabs in a desktop application, so that I can
  run the mix decomposition pipeline without assembling CLI flags or memorizing
  sheet names.
- As an analyst preparing inputs, I want to preview the contents of a selected
  worksheet before importing it, so that I can confirm I picked the correct
  tab before running the pipeline.
- As an operator producing results, I want to save the pipeline output to a
  database file and reopen a prior result later, so that I can persist and
  revisit runs without rerunning the pipeline.
- As an analyst sharing results, I want to export selected output tables to
  Excel or CSV, so that I can hand off the derived tables in formats my
  colleagues use.
- **(New in v2)** As an analyst who exercised v1, I expected clicking Import
  LE to actually import LE, clicking Render Tab to render the tab, and
  clicking Export to give me an Excel or CSV file; in v1 the buttons did not
  produce these outcomes despite passing tests. I want every button on the
  assembled application to perform the documented action and for the
  acceptance gates to verify the buttons against the running application, not
  only against isolated presenter and widget units.

## Problem / Why

The mix decomposition pipeline (`src/mix_pipeline.py`) is driven only through
a CLI. v1 of this feature added a PySide6 desktop application intended to make
the pipeline self-service: select files, preview tabs, import, run, save,
reopen, and export. v1 shipped 333 passing tests at 100% line and branch
coverage and a fully decoupled MVP architecture. The assembled application,
however, did not deliver the user-visible behaviors when a user clicked the
buttons. The v1 acceptance criteria were unit-anchored — they required each
presenter, widget, and service to be correct in isolation, and they were —
but they did not require the buttons on the assembled `MainWindow` to produce
the documented user-visible outcomes. v1 therefore shipped with three
concrete Export wiring defects (empty checklist on display, empty Save dialog
filter, missing CSV multi-file rule), a Render Tab path that never reached
the shared `PreviewWidget`, import buttons that did not change state on
success, and a Run flow that did not connect through a worker.

v2 reframes the feature around the user-facing behavior of the running
application. Each acceptance criterion is anchored both to a unit/integration
test AND to a button-driven behavioral check performed against the running
GUI under `QT_QPA_PLATFORM=offscreen`. The behavioral checks click the actual
button on the assembled `MainWindow` and assert the user-visible state. v2
also fixes the three identified Export wiring defects, introduces a runner
abstraction so the Run behavioral test is deterministic without polling, adds
the view-protocol methods that let the presenter drive button enable state,
and routes worksheet previews from the per-input presenters to the shared
`PreviewWidget`.

## Personas & Scenarios

### Persona: Maria, mix-decomposition analyst (carried from v1)

- **Who:** A finance analyst responsible for the monthly LE-versus-AOP
  gross-to-net mix decomposition.
- **What she cares about:** Producing correct, reproducible results and
  confirming she selected the right worksheet tabs before running.
- **Constraints:** She is not comfortable on the command line, does not
  memorize sheet names, and receives workbooks whose tab names and layouts
  vary slightly month to month.
- **Goals and frustrations:** She wants to run the pipeline and export
  results without help from an engineer. A wrong sheet name or flag silently
  producing a confusing CLI error is the original frustration that motivated
  v1; a button that does nothing when clicked is the v1 regression that
  motivated v2.
- **Context and motivations:** She runs the pipeline on a recurring schedule
  and needs to revisit prior results and share derived tables with
  colleagues.

### Scenario: Maria exercises v1 and reports the defects (motivating v2)

1. Maria opens the v1 desktop application built from `feature/mix-pipeline-gui-19`.
2. For the LE input she selects her workbook. The tab dropdown populates. She
   picks `"LE-8 + 4"`.
3. She checks the LE Render Tab box. Nothing appears in the preview area.
   (Defect: the per-input presenter routed `show_preview` to the
   `SourceInputWidget`'s no-op method; the shared `PreviewWidget` was never
   called.)
4. She clicks Import LE. The application reports success but the Import LE
   button remains enabled. She clicks it again, expecting a fresh import or a
   visible state change. There is no way to tell the import has been
   "captured" from the button surface. (Defect: no presenter-driven button
   enable state; the protocol did not expose `set_import_button_enabled`.)
5. She fills in AOP and SKU_LU and clicks Import All. Same outcome: no
   buttons reflect that imports succeeded. She does not know which inputs
   are loaded.
6. She clicks Run. Nothing visible happens. (Defect: the v1 wiring did not
   construct or dispatch through `PipelineWorker`; the Run button's
   `clicked` signal was connected to a presenter slot whose run path did not
   produce derived tables in the assembled application.)
7. She clicks Export. A dialog appears with an empty per-table checklist.
   (Defect 1: `set_available_tables` was called AFTER
   `export_dialog_runner(export_dialog)` returned.)
8. She clicks Export All in the empty dialog, then OK. A Save File dialog
   opens with no format filter at all. (Defect 2: the v1
   `default_export_runner` called `QFileDialog.getSaveFileName(dialog,
   "Export Destination", "", "")` with an empty filter.) She types
   `results.csv`. The application reports it wrote one file of all tables
   concatenated, not one file per table. (Defect 3: `CsvExporter` did not
   implement multi-file output.)
9. Maria reports each defect in the order above. v2 is opened to address
   them and to ensure no future v1-style regression ships behind a green
   unit-test gate.

No confidential values are relied upon in this scenario; the cell content
references are fabricated (e.g., `SKU=1001, Category=Example-A,
Country=US`).

### Scenario: End-to-end monthly run on v2 (button-by-button walkthrough)

1. Maria opens the v2 desktop application.
2. For the LE input she selects her workbook; the tab dropdown populates and
   she picks `"LE-8 + 4"`. She does the same for AOP (`"AOP1"`) and SKU_LU
   (`"SKU_LU"`).
3. She checks the LE Render Tab box. The shared preview area populates with
   a readable grid of cells from `"LE-8 + 4"`. She changes the LE tab
   selection to a different sheet while the box remains checked; the
   preview re-renders for the new sheet. She unchecks the box; the preview
   clears. (AC-1 satisfied at the button-driven behavioral level.)
4. She clicks Import LE. The button greys out. She reselects the same LE
   file path; the button stays disabled. She selects a different LE file;
   the button re-enables. She reselects the original LE file; the button
   re-enables (the path differs from the last-imported path). She clicks
   Import LE again; the button greys out. (AC-2 satisfied.)
5. She fills AOP and SKU_LU and clicks Import All. All four import buttons
   grey out together. She changes the AOP file selection; only the AOP
   import button and Import All re-enable; LE and SKU_LU stay disabled.
   (AC-3, AC-4, AC-5 satisfied.)
6. She clicks Run. The Run button greys out for the duration of the run; on
   completion the application reports success and the derived-table set is
   populated. (AC-6 satisfied via the production `ThreadedRunner`;
   behavioral tests assert the equivalent via the injected
   `SynchronousRunner` without any polling primitive.)
7. She clicks Save and chooses `results.db` from the Save dialog filtered
   to `.db`. The working tables (derived, since she has run) are persisted
   through `PipelineService.save_to_db`. The status surface reports the
   destination and table count. (AC-7 satisfied.)
8. A week later she clicks Open and selects `results.db`. The tables load
   back into the in-memory imported set. The import buttons for `LE`,
   `aop`, and `sku_lu` grey out to reflect that those tables are loaded
   and current. Run is enabled. (AC-8 satisfied.)
9. She clicks Export. The `ExportDialog` opens with the per-table
   checklist already populated with the working-set table names. She
   selects the tables she needs (or clicks Export All), then OK. The Save
   File dialog opens with `"Excel (*.xlsx);;CSV (*.csv)"` as the filter.
   She picks Excel and types `export.xlsx`; the exporter writes one
   workbook with one sheet per selected table. Alternatively she picks CSV
   and types `export.csv`; the exporter writes
   `export_<table_name>.csv` for each selected table in the directory of
   the chosen path. (AC-9 satisfied; Defects 1, 2, and 3 fixed.)

- **Trigger:** the monthly mix-decomposition deliverable is due.
- **Obstacles/decisions:** confirming the correct tab per input via preview;
  choosing which tables to export; confirming which inputs are loaded by
  reading the button state.
- **Expected outcome:** a persisted result database and exported
  Excel/CSV files of the selected derived tables, produced without the CLI
  and with every button reflecting the user-visible state of the application.

## Acceptance Criteria

The acceptance criteria below are reproduced verbatim from `v2/issue.md`. Do
not edit the text here; the issue is the source of truth.

- [ ] **AC-1 Render Tab renders an image of the selected worksheet.** With a
  file and a tab selected, checking the per-input "Render Tab" checkbox
  causes the preview surface to display a visual image of the selected
  worksheet's cells. Selecting a different tab while the checkbox remains
  checked replaces the preview with an image of the newly selected tab.
  Unchecking the checkbox clears the preview. This applies independently to
  the LE, AOP, and SKU_LU inputs.
- [ ] **AC-2 Import LE wires to the pipeline and disables on success.**
  Clicking Import LE with a valid LE file and sheet selection runs
  `PipelineService.import_le` against the current selection, stores the
  resulting frame keyed by `"LE"`, and disables the Import LE button. The
  button stays disabled until the user selects a different LE file path. A
  `ValueError` from the loader surfaces via the status surface and leaves
  the button enabled.
- [ ] **AC-3 Import AOP wires to the pipeline and disables on success.** Same
  behavior as AC-2 but for AOP via `PipelineService.import_aop`, keyed by
  `"aop"`.
- [ ] **AC-4 Import SKU_LU wires to the pipeline and disables on success.**
  Same behavior as AC-2 but for SKU_LU via `PipelineService.import_skulu`,
  keyed by `"sku_lu"`. The SKU_LU workbook defaults to the LE/AOP workbook
  when no separate SKU_LU file is selected (mirrors the CLI
  `--skulu-input` default).
- [ ] **AC-5 Import All runs all three imports and disables all four import
  buttons on success.** Clicking Import All runs
  `PipelineService.import_sources` (or per-input imports in sequence)
  against the current selections. On full success all four import buttons
  (Import LE, Import AOP, Import SKU_LU, Import All) are disabled. Disabled
  buttons re-enable only when their corresponding per-input file selection
  changes; changing one per-input file re-enables only that per-input
  button and Import All. A `ValueError` on any per-input import surfaces
  the error via the status surface, marks only the successfully-imported
  buttons as disabled, and leaves Import All enabled.
- [ ] **AC-6 Run executes the transformation end-to-end and updates state.**
  Clicking Run with a non-empty imported-table set invokes
  `PipelineService.run_pipeline` off the UI thread via `PipelineWorker` +
  `QThread`, populates the derived-table set on success, reports the result
  via the status surface, and surfaces failures via the status surface
  without losing the imported tables. Run is disabled when the
  imported-table set is empty.
- [ ] **AC-7 Save persists the working tables to a SQLite `.db`.** Clicking
  Save opens a Save File dialog filtered to `.db`. On accept it persists the
  working table set through `PipelineService.save_to_db` to the chosen path
  and reports the destination and table count via the status surface.
  Cancel dismisses without writing. Save is disabled when the working set
  is empty.
- [ ] **AC-8 Open loads tables from a `.db` and reflects load state on the
  import buttons.** Clicking Open opens an Open File dialog filtered to
  `.db`. On accept it loads every table found in the `.db` through
  `PipelineService.open_db` into the imported-table set, sets the working
  DB path, and disables every import button whose key matches a loaded
  table. Re-enabling for that input occurs only when the user selects a
  different file. Run becomes enabled when at least one table has been
  loaded.
- [ ] **AC-9 Export opens a file dialog with Excel and CSV format choices
  and exports through the registry.** Clicking Export opens a Save File
  dialog whose filter offers Excel (`*.xlsx`) and CSV (`*.csv`) as
  selectable choices. The selected filter resolves an exporter from the
  `ExporterRegistry` (`ExcelExporter` or `CsvExporter`). The export writes
  the current working set to the chosen destination through
  `ExporterProtocol.export`. Export is disabled when the working set is
  empty.
- [ ] **AC-10 Composition root wires all signals to behavioral handlers.**
  `src/gui/app.py` constructs the real collaborators and wires every
  `MainWindow` signal to a presenter handler that performs the documented
  user-visible behavior. A `qtbot`-driven test against the assembled
  application asserts AC-1 through AC-9 by clicking the actual button or
  toggling the actual checkbox, not by emitting signals on a stand-in.
- [ ] **AC-11 Presentation logic remains testable without a live Qt event
  loop (unchanged from v1).** Presenter tests run with no `QApplication`;
  widget tests run with `pytest-qt` under `QT_QPA_PLATFORM=offscreen`.
- [ ] **AC-12 Full toolchain passes and coverage thresholds hold (unchanged
  from v1).** Black, Ruff, Pyright strict, and Pytest pass; line coverage
  >= 85% and branch coverage >= 75%; no regression on changed lines.

## Non-Goals

- Editing or correcting source data within the GUI (carried from v1). The
  application selects, previews, imports, runs, persists, and exports; it
  does not edit source cells.
- Input formats other than Excel (carried from v1). Source inputs are Excel
  workbooks; other input formats are out of scope for this iteration.
- Export formats beyond Excel and CSV in this iteration (carried from v1).
  The exporter registry is designed to be extensible, but only Excel and CSV
  are delivered now.
- Packaging, installers, or distribution (carried from v1). Building a
  standalone installer or bundled executable is out of scope.
- Changes to the pipeline transforms or the `mix-pipeline` CLI (carried from
  v1). The GUI drives the existing pipeline; the CLI surface is unchanged.
- A spreadsheet-to-image rendering library (carried from v1). The preview
  renders through a Qt table view within the approved dependency set; no
  image-rendering dependency is added.
- **(New in v2)** A revert of v1 PR #24. v2 is additive over the v1 module
  set; no v1 commit is reverted. v2 evolves the existing presenter, widget,
  service, exporter, and composition-root modules and adds the runner
  abstraction.
- **(New in v2)** A new top-level dependency. `pytest-qt` remains the only
  dev dependency added beyond what was already declared at v1.
- **(New in v2)** A `QObject`-based presenter. `PipelinePresenter` remains
  plain Python and does not emit Qt signals. The runner abstraction is the
  mechanism by which behavioral tests assert post-run state.
