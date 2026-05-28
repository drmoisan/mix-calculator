# mix-pipeline-gui (Issue #19)

- **Date captured:** 2026-05-27
- **Author:** Dan Moisan
- **Status:** Promoted -> docs/features/active/mix-pipeline-gui/ (Issue #19)
- **Issue:** #19
- **Issue URL:** https://github.com/drmoisan/mix-calculator/issues/19
- **Last Updated:** 2026-05-28
- **Work Mode:** full-feature
- **Version:** 1.0

## Problem / Why

The mix decomposition pipeline (`src/mix_pipeline.py`) is currently driven only
through a CLI. Running the pipeline end-to-end requires assembling the correct
Excel workbook, knowing the source-sheet names for each input table, and invoking
the command with the right flags. There is no interactive way to select input
files, confirm the correct worksheet tab for each input table, preview the source
data before import, run the pipeline, persist results, reopen a prior result
database, or export derived tables to other formats. A desktop GUI would make the
pipeline usable by non-CLI users and make input selection, preview, and export
self-service.

## Proposed Behavior

Provide a PySide6 desktop application that drives the existing mix pipeline
end-to-end while preserving the pure-transform / I/O-boundary separation already
established in `src/`. High-level capabilities:

1. **Per-input-table source selection.** For each pipeline input table (LE, AOP,
   SKU_LU), allow the user to select an Excel file and choose the correct
   worksheet tab for that input.
2. **Tab discovery.** When an Excel file is selected, populate a dropdown of the
   worksheet tabs available in that workbook for the user to choose from.
3. **Optional tab preview.** Provide an optional checkbox per input to render the
   selected tab; when checked, show an image/preview of the spreadsheet contents
   on that tab.
4. **Import.** Once source tables are selected, provide an option to import one or
   all of the selected files into the working dataset.
5. **Run pipeline.** After import, provide a button that triggers the mix pipeline
   to run against the imported inputs.
6. **Save to DB.** A Save button persists the working data into a SQLite `.db`
   file (the existing pipeline output sink).
7. **Open DB.** A button to open an existing `.db` file and load its tables.
8. **Export.** An Export button that supports exporting to Excel with a checklist
   of tables to export, plus an "export all" control that checks all tables.
   Export must support Excel and CSV initially and be extensible to additional
   formats.
9. **UI conventions & testability.** The GUI is built in PySide6, follows standard
   desktop UI conventions, and is explicitly designed for testability:
   dependency injection of services, mockable GUI components, and a presentation
   layer separable from Qt widgets so the suite is fully testable.

## Acceptance Criteria (early draft)

- [x] For each input table (LE, AOP, SKU_LU) the user can select an Excel file
      and pick the worksheet tab for that input.
- [x] Selecting an Excel file populates a dropdown of that workbook's worksheet
      tabs.
- [x] An optional per-input "render tab" checkbox shows a preview image of the
      selected worksheet's contents when checked.
- [x] The user can import one selected file or all selected files.
- [x] After import, a Run button executes the mix pipeline against the imported
      inputs and reports success/failure.
- [x] A Save button persists the working data to a SQLite `.db` file.
- [x] An Open button loads tables from an existing `.db` file.
- [x] An Export action exports selected tables to Excel and CSV, with a
      per-table checklist and an "export all" control; the export format set is
      extensible.
- [x] Presentation logic is separated from Qt widgets and services are injected,
      so view-models/controllers are unit-testable without a live Qt event loop
      where practical, and Qt widgets are tested with the project's Qt test
      facility.
- [x] The full toolchain (Black, Ruff, Pyright strict, Pytest with coverage
      thresholds) passes, and coverage meets the repository thresholds
      (>= 85% line, >= 75% branch).

## Constraints & Risks

- **PySide6 already declared** in `pyproject.toml` (`^6.11.1`); no new top-level
  dependency is expected. A Qt test facility (for example `pytest-qt`) and a
  preview-rendering approach may require a dev dependency; adding any new
  dependency requires explicit approval per repo policy.
- **I/O boundary discipline.** All Excel/SQLite I/O must continue to flow through
  `src/pandas_io.py`-style typed boundaries; transforms remain pure. The GUI must
  not embed transform logic.
- **Testability without temp files.** Repo policy prohibits runtime temp files in
  unit tests and external dependencies in unit tests; the design must enable
  testing file/DB/Excel interactions behind injectable seams.
- **File size limit.** No production/test/script file may exceed 500 lines; a GUI
  suite must be decomposed into cohesive modules.
- **Confidentiality.** `SKU Description` and `Category` values are confidential
  and must never appear in tests, fixtures, or docs; only fabricated examples are
  permitted. Source workbooks and `.db` outputs remain gitignored.
- **Determinism.** GUI/preview rendering and any async work must be deterministic
  under test (controllable clock, no wall-clock sleeps) per the unit-test policy.
- **Pyright strict** applies to GUI code, including Qt signal/slot typing, which
  can be a source of unknown member types and may require typed adapter views.
- **Spreadsheet-to-image rendering** has no obviously approved library in the
  current dependency set; the rendering approach is an open design question for
  research.

## Test Conditions to Consider

- [ ] Unit coverage: view-models/controllers for source selection, tab discovery,
      import, run, save, open, and export — exercised with mocked services.
- [ ] Negative flows: invalid/unreadable Excel file, workbook with no usable tab,
      pipeline run failure, save/open to an invalid path, export with no tables
      selected.
- [ ] Edge cases: workbook with a single tab, duplicate tab names, very large
      tab for preview, export-all vs. partial-checklist selection.
- [ ] Boundary adapters: Excel tab enumeration, preview rendering, SQLite open,
      and multi-format export each tested behind their injected seam.
- [ ] Qt widget tests using the project's Qt test facility for signal/slot wiring
      and widget state transitions.
- [ ] Integration scenario: end-to-end select → import → run → save → reopen →
      export against fabricated fixtures.

## Next Step

- [ ] Promote to GitHub issue (feature request template)
- [ ] Create `docs/features/active/mix-pipeline-gui/` folder from the template