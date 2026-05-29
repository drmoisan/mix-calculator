# mix-pipeline-gui (Issue #19) — v2

- **Date captured:** 2026-05-27
- **Author:** Dan Moisan
- **Status:** Active
- **Issue:** #19
- **Issue URL:** https://github.com/drmoisan/mix-calculator/issues/19
- **Last Updated:** 2026-05-28
- **Work Mode:** full-feature
- **Version:** 2.0
- **Supersedes:** Version 1.0 (delivered under PR #24 with the acceptance criteria ticked at the unit-test level but the user-facing button surface non-functional in the assembled application).

## Problem / Why

Version 1.0 of `mix-pipeline-gui` was delivered with a complete unit-test surface, a fully decoupled MVP architecture, and 100% line/branch coverage, but the assembled desktop application does not deliver the behaviors a user actually exercises by clicking the buttons in `MainWindow`. The buttons emit signals and the presenters function in isolation, yet the integrated control flow does not run the pipeline end-to-end, does not render the per-tab preview when the "Render Tab" checkboxes are checked, does not gate the import buttons against their import state, and does not present a file-format dialog on Export. The v1 acceptance criteria were unit-anchored; they did not require that the buttons in the running application produce the user-visible outcome.

Version 2.0 reframes the feature around the user-facing behavior of the running application. Each acceptance criterion is anchored both to a unit/integration test AND to a button-driven behavioral check performed against the running GUI under `QT_QPA_PLATFORM=offscreen` so that "the button does the thing" is an enforced gate, not an inferred consequence.

## Proposed Behavior

The PySide6 desktop application continues to drive the existing mix pipeline end-to-end while preserving the pure-transform / I/O-boundary separation established in `src/`. The user-facing control surface is:

1. **Per-input source selection (unchanged from v1).** For each pipeline input table (LE, AOP, SKU_LU), the user selects an Excel file and chooses the worksheet tab. Selecting a file populates the tab dropdown.

2. **Render Tab preview (defect to fix).** Each per-input "Render Tab" checkbox, when checked with a file and tab selected, renders an image of the selected worksheet. The image updates when the user selects a different tab while the checkbox remains checked. Unchecking the checkbox clears the preview. Switching tabs without unchecking the box re-renders for the new tab. The image is a visual representation of the spreadsheet's cell contents on that tab (a `QTableView`-backed grid rendered via `widget.grab()` to a `QPixmap`, or an equivalent approach validated during research).

3. **Per-input Import buttons (Import LE, Import AOP, Import SKU_LU) (defect to fix).** Each per-input import button executes the corresponding loader through `PipelineService.import_le` / `import_aop` / `import_skulu` against the currently selected file and tab for that input. On success the table is held in the in-memory imported-table set keyed by the input name and the button is disabled (greyed out). The button is re-enabled the next time the user selects a different file in that same input widget. Reselecting the same path, or selecting and then re-selecting the same path, does not re-enable until the path actually changes.

4. **Import All button (defect to fix).** The Import All button runs all three per-input imports in sequence against the current per-input selections. On success it disables all four import buttons (Import LE, Import AOP, Import SKU_LU, Import All) and keeps them disabled until any per-input file selection changes; changing any one of the three per-input files re-enables Import All and the matching per-input button only. Partial success: if any per-input import raises a `ValueError`, the application surfaces the error via the status surface, leaves the per-input button states reflecting which inputs successfully imported, and leaves Import All enabled (so the user can retry after fixing the bad input).

5. **Run button (defect to fix).** The Run button executes the transformation end-to-end through `PipelineService.run_pipeline` over the imported in-memory tables. Run is disabled until at least one import has succeeded (or an existing `.db` has been opened); enabled once the imported-table set is non-empty. On success the derived-table set replaces the prior derived set; on failure the error routes to the status surface and the imported tables are preserved. The run executes off the UI thread via `PipelineWorker` + `QThread` so the window remains responsive.

6. **Save button (defect to fix).** The Save button opens a Save File dialog filtered to `.db`. On accept it persists the working table set (derived tables when a run has completed; otherwise imported tables) to the chosen SQLite path through `PipelineService.save_to_db`. The status surface reports the destination and table count. Save is disabled when the working set is empty.

7. **Open button (defect to fix).** The Open button opens an Open File dialog filtered to `.db`. On accept it loads every table found in the `.db` through `PipelineService.open_db` into the in-memory imported-table set, sets the working DB path, and updates per-input button state: any import-button whose key matches a loaded table is disabled (greyed out) to reflect that the table is loaded and current. Re-enabling occurs by selecting a different file for that input. Run is enabled when at least one table has been loaded.

8. **Export button (defect to fix).** The Export button opens a Save File dialog whose filter offers Excel (`*.xlsx`) and CSV (`*.csv`) as selectable format choices. The selected filter resolves the exporter (`ExcelExporter` for `*.xlsx`, `CsvExporter` for `*.csv`) from the `ExporterRegistry`. The export operates on the current working set (derived tables when a run has completed; otherwise imported tables; otherwise the loaded set from Open). For Excel, every table is written as a worksheet in one workbook. For CSV, every table is written as one `.csv` file at the chosen path (single-table) or one-per-table into the destination directory (multi-table — the exact behavior is a design decision for the research and spec stages). Export is disabled when the working set is empty.

9. **UI conventions and testability (unchanged from v1).** Presentation logic lives in plain-Python presenters with no Qt imports, exercised in pytest without a `QApplication`. Qt widgets are thin and exercised with `pytest-qt` under `QT_QPA_PLATFORM=offscreen`. Services are injected at the composition root (`src/gui/app.py`); no DI framework is introduced.

## Acceptance Criteria

Each criterion below must pass at both a unit/integration level AND a button-driven behavioral level (i.e., a `qtbot`-driven test that clicks the actual button on the actual `MainWindow` and asserts the user-visible state, not only that the signal was emitted).

- [x] **AC-1 Render Tab renders an image of the selected worksheet.** With a file and a tab selected, checking the per-input "Render Tab" checkbox causes the preview surface to display a visual image of the selected worksheet's cells. Selecting a different tab while the checkbox remains checked replaces the preview with an image of the newly selected tab. Unchecking the checkbox clears the preview. This applies independently to the LE, AOP, and SKU_LU inputs.
- [x] **AC-2 Import LE wires to the pipeline and disables on success.** Clicking Import LE with a valid LE file and sheet selection runs `PipelineService.import_le` against the current selection, stores the resulting frame keyed by `"LE"`, and disables the Import LE button. The button stays disabled until the user selects a different LE file path. A `ValueError` from the loader surfaces via the status surface and leaves the button enabled.
- [x] **AC-3 Import AOP wires to the pipeline and disables on success.** Same behavior as AC-2 but for AOP via `PipelineService.import_aop`, keyed by `"aop"`.
- [x] **AC-4 Import SKU_LU wires to the pipeline and disables on success.** Same behavior as AC-2 but for SKU_LU via `PipelineService.import_skulu`, keyed by `"sku_lu"`. The SKU_LU workbook defaults to the LE/AOP workbook when no separate SKU_LU file is selected (mirrors the CLI `--skulu-input` default).
- [x] **AC-5 Import All runs all three imports and disables all four import buttons on success.** Clicking Import All runs `PipelineService.import_sources` (or per-input imports in sequence) against the current selections. On full success all four import buttons (Import LE, Import AOP, Import SKU_LU, Import All) are disabled. Disabled buttons re-enable only when their corresponding per-input file selection changes; changing one per-input file re-enables only that per-input button and Import All. A `ValueError` on any per-input import surfaces the error via the status surface, marks only the successfully-imported buttons as disabled, and leaves Import All enabled.
- [x] **AC-6 Run executes the transformation end-to-end and updates state.** Clicking Run with a non-empty imported-table set invokes `PipelineService.run_pipeline` off the UI thread via `PipelineWorker` + `QThread`, populates the derived-table set on success, reports the result via the status surface, and surfaces failures via the status surface without losing the imported tables. Run is disabled when the imported-table set is empty.
- [x] **AC-7 Save persists the working tables to a SQLite `.db`.** Clicking Save opens a Save File dialog filtered to `.db`. On accept it persists the working table set through `PipelineService.save_to_db` to the chosen path and reports the destination and table count via the status surface. Cancel dismisses without writing. Save is disabled when the working set is empty.
- [x] **AC-8 Open loads tables from a `.db` and reflects load state on the import buttons.** Clicking Open opens an Open File dialog filtered to `.db`. On accept it loads every table found in the `.db` through `PipelineService.open_db` into the imported-table set, sets the working DB path, and disables every import button whose key matches a loaded table. Re-enabling for that input occurs only when the user selects a different file. Run becomes enabled when at least one table has been loaded.
- [x] **AC-9 Export opens a file dialog with Excel and CSV format choices and exports through the registry.** Clicking Export opens a Save File dialog whose filter offers Excel (`*.xlsx`) and CSV (`*.csv`) as selectable choices. The selected filter resolves an exporter from the `ExporterRegistry` (`ExcelExporter` or `CsvExporter`). The export writes the current working set to the chosen destination through `ExporterProtocol.export`. Export is disabled when the working set is empty.
- [x] **AC-10 Composition root wires all signals to behavioral handlers.** `src/gui/app.py` constructs the real collaborators and wires every `MainWindow` signal to a presenter handler that performs the documented user-visible behavior. A `qtbot`-driven test against the assembled application asserts AC-1 through AC-9 by clicking the actual button or toggling the actual checkbox, not by emitting signals on a stand-in.
- [x] **AC-11 Presentation logic remains testable without a live Qt event loop (unchanged from v1).** Presenter tests run with no `QApplication`; widget tests run with `pytest-qt` under `QT_QPA_PLATFORM=offscreen`.
- [x] **AC-12 Full toolchain passes and coverage thresholds hold (unchanged from v1).** Black, Ruff, Pyright strict, and Pytest pass; line coverage >= 85% and branch coverage >= 75%; no regression on changed lines.

## Constraints & Risks

- **PySide6 already declared** in `pyproject.toml` (`^6.11.1`). `pytest-qt` is approved as a dev dependency. The image-render approach for AC-1 is anchored on `QTableView` + `widget.grab()` in v1; whether that pattern produces the user-visible "image of the spreadsheet" the user expects in the running application is the central research question for v2 and may require an alternative widget or rendering strategy.
- **Button-state semantics.** The grey-out / re-enable rules in AC-2 through AC-5 and AC-8 cross widget, presenter, and composition boundaries. A widget cannot decide it has been "imported" without the presenter telling it so; the presenter cannot decide a file selection has "changed" without the widget telling it so. The contract must be defined in the presenter layer and exposed to widgets through signals or view-protocol methods, not embedded in the widget.
- **Working-set semantics.** Several controls (Run, Save, Export) operate on "the working table set." The presenter must define exactly what that set is at each moment: imported only (post-import), derived (post-run), or loaded (post-open). The v1 implementation hand-waved this; v2 must specify it.
- **I/O boundary discipline (unchanged from v1).** All Excel/SQLite I/O continues to flow through `src/pandas_io.py`-style typed boundaries; transforms remain pure; the GUI embeds no transform logic.
- **Testability without temp files (unchanged from v1).** No runtime temp files in unit tests; no external dependencies; file/DB/Excel interactions test behind injectable seams using `BytesIO` and `sqlite3.connect(":memory:")`.
- **File size limit (unchanged from v1).** No production/test/script file exceeds 500 lines.
- **Confidentiality (unchanged from v1).** `SKU Description` and `Category` values are confidential and must never appear in tests, fixtures, or docs.
- **Determinism (unchanged from v1).** No wall-clock sleeps in tests; `qtbot.waitSignal` for event waits; banned APIs (`time.sleep`, `QThread.sleep`, `QTest.qWait`) must not appear in test code.
- **Pyright strict (unchanged from v1).** Applies to GUI code including signal/slot typing.
- **Behavioral test surface.** The unit-anchored AC contract of v1 was insufficient to catch wiring defects. v2 requires `qtbot`-driven button-press tests against the assembled application; the research must determine how to construct that test seam without invoking the blocking event loop (the v1 `build_application` factory is the likely anchor).
- **Backward compatibility with v1 artifacts.** PR #24 merged the v1 modules. v2 is an evolution of the same modules, not a rewrite; the v2 plan must specify which v1 files are modified (likely `src/gui/app.py`, `src/gui/main_window.py`, presenter modules, and the widget signal layer) and which are new.

## Test Conditions to Consider

- [ ] Behavioral (qtbot-driven) tests for every per-input "Render Tab" toggle and tab change, asserting the preview surface contents change in the expected direction.
- [ ] Behavioral tests for every per-input Import button: enabled before click, click triggers the loader, button disabled after success, error path leaves button enabled and surfaces the error.
- [ ] Behavioral test for Import All: enabled before click, click triggers all three imports, all four import buttons disabled after success, changing one per-input file re-enables exactly the corresponding per-input button and Import All only.
- [ ] Behavioral test for Run: disabled before any import or open, enabled after an import/open succeeds, click runs the pipeline off the UI thread, success populates derived tables, failure preserves imported tables.
- [ ] Behavioral test for Save: disabled when working set is empty, enabled when non-empty, click opens a `.db` Save dialog, accept persists, cancel dismisses.
- [ ] Behavioral test for Open: click opens a `.db` Open dialog, accept loads tables and disables the matching import buttons, Run becomes enabled.
- [ ] Behavioral test for Export: disabled when working set is empty, enabled when non-empty, click opens a Save dialog with Excel and CSV filter choices, the chosen filter resolves the matching exporter and the chosen path receives the output.
- [ ] Edge cases: per-input file reselection to the same path does NOT re-enable an import button; selecting a different path DOES; cancelling a Save/Open/Export dialog is a no-op; opening a `.db` with no tables surfaces a clear error and leaves state unchanged.
- [ ] Negative flows: ValueError on any loader; pipeline run failure; invalid `.db` path on Save/Open; export with an empty working set.
- [ ] Unit coverage for the new presenter button-state logic (per-input file-change detection, working-set selection rule, exporter resolution from a dialog filter string).
- [ ] Test seam to invoke the running application without a blocking event loop (likely a `qtbot.addWidget(build_application().window)` pattern that exposes the wired widgets to the test).

## Out of Scope

- Changes to `src/mix_pipeline.py` (CLI), `src/mix_pipeline_run.py`, `src/mix_lookups.py`, `src/mix_transforms.py`, or any pure-transform module. v2 is purely a GUI behavior and wiring evolution.
- Packaging, installers, or distribution.
- Export formats beyond Excel and CSV in this iteration. The registry remains extensible.
- A spreadsheet-to-image rendering library beyond what PySide6 + the existing dependency set supports. If research shows the v1 approach cannot satisfy AC-1, the spec stage proposes an alternative within the approved dependency set and obtains explicit user approval before adding any new dependency.
- Reverting any v1 commit on `feature/mix-pipeline-gui-19` or PR #24. v2 is additive/evolutionary; the v1 module set is the working base.

## Next Step

- [ ] Sync this issue body to GitHub Issue #19.
- [ ] Re-establish orchestration on the large-audit path and delegate to `task-researcher` to determine the best implementation approach for AC-1 (image rendering of a worksheet) and the working-set / button-state contract, then use the research to update `spec.md` and `user-story.md` in normal orchestration order.
- [ ] Delegate to `atomic-planner` to update the v2 atomic plan; rename the placeholder `plan.yyyy-MM-ddThh-mm.md` to the current timestamp.
- [ ] Continue normal orchestration through execution, audit, and (only through the conformant remediation loop) any remediation.
