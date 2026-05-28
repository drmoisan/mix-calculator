# `2026-05-27-mix-pipeline-gui` — User Story

- **Issue:** #19
- **Owner:** drmoisan
- **Status:** Superceded by 2.0
- **Version:** 2.0
- **Last Updated:** 2026-05-27T20-59

## Story Statement

- As a finance analyst who does not use the command line, I want to select my
  source workbooks and worksheet tabs in a desktop application, so that I can run
  the mix decomposition pipeline without assembling CLI flags or memorizing sheet
  names.
- As an analyst preparing inputs, I want to preview the contents of a selected
  worksheet before importing it, so that I can confirm I picked the correct tab
  before running the pipeline.
- As an operator producing results, I want to save the pipeline output to a
  database file and reopen a prior result later, so that I can persist and revisit
  runs without rerunning the pipeline.
- As an analyst sharing results, I want to export selected output tables to Excel
  or CSV, so that I can hand off the derived tables in formats my colleagues use.

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

## Personas & Scenarios

### Persona: Maria, mix-decomposition analyst

- **Who:** A finance analyst responsible for the monthly LE-versus-AOP
  gross-to-net mix decomposition.
- **What she cares about:** Producing correct, reproducible results and confirming
  she selected the right worksheet tabs before running.
- **Constraints:** She is not comfortable on the command line, does not memorize
  sheet names, and receives workbooks whose tab names and layouts vary slightly
  month to month.
- **Goals and frustrations:** She wants to run the pipeline and export results
  without help from an engineer. Her current frustration is that a wrong sheet
  name or flag silently produces a confusing CLI error.
- **Context and motivations:** She runs the pipeline on a recurring schedule and
  needs to revisit prior results and share derived tables with colleagues.

### Scenario: End-to-end monthly run

1. Maria opens the desktop application.
2. For the LE input she selects her workbook; the tab dropdown populates with the
   workbook's worksheet names, and she picks `"LE-8 + 4"`.
3. For the AOP input she selects the same workbook and picks `"AOP1"`; for the
   SKU_LU input she picks `"SKU_LU"` (defaults are pre-filled, so she only adjusts
   what differs this month).
4. She checks the "render tab" box on the AOP input and reviews the preview grid
   to confirm the data looks right. The preview shows fabricated example rows such
   as `SKU=1001, Category=Example-A, Country=US`; no confidential values are
   relied upon for this story.
5. She clicks Import All. The application imports the three inputs into memory and
   reports completion.
6. She clicks Run. A progress indicator shows while the pipeline runs off the UI
   thread, then the application reports success.
7. She clicks Save and chooses `results.db`. The working tables are written to the
   SQLite database.
8. A week later she clicks Open and selects `results.db`; the tables load back
   into the application without rerunning the pipeline.
9. She clicks Export, checks the tables she needs (or uses "export all"), chooses
   Excel, and exports to `export.xlsx` (one sheet per selected table).

- **Trigger:** the monthly mix-decomposition deliverable is due.
- **Obstacles/decisions:** confirming the correct tab per input via preview;
  choosing which tables to export.
- **Expected outcome:** a persisted result database and an exported Excel workbook
  of the selected derived tables, produced without the CLI.

## Acceptance Criteria

- [x] For each input table (LE, AOP, SKU_LU) the user can select an Excel file and
      pick the worksheet tab for that input.
- [x] Selecting an Excel file populates a dropdown of that workbook's worksheet
      tabs.
- [x] An optional per-input "render tab" checkbox shows a preview image of the
      selected worksheet's contents when checked.
- [x] The user can import one selected file or all selected files.
- [x] After import, a Run button executes the mix pipeline against the imported
      inputs and reports success/failure.
- [x] A Save button persists the working data to a SQLite `.db` file.
- [x] An Open button loads tables from an existing `.db` file.
- [x] An Export action exports selected tables to Excel and CSV, with a per-table
      checklist and an "export all" control; the export format set is extensible.
- [x] Presentation logic is separated from Qt widgets and services are injected,
      so view-models/controllers are unit-testable without a live Qt event loop
      where practical, and Qt widgets are tested with the project's Qt test
      facility.
- [x] The full toolchain (Black, Ruff, Pyright strict, Pytest with coverage
      thresholds) passes, and coverage meets the repository thresholds
      (>= 85% line, >= 75% branch).

## Non-Goals

- Editing or correcting source data within the GUI. The application selects,
  previews, imports, runs, persists, and exports; it does not edit source cells.
- Input formats other than Excel. Source inputs are Excel workbooks; other input
  formats are out of scope for this iteration.
- Export formats beyond Excel and CSV in this iteration. The exporter registry is
  designed to be extensible, but only Excel and CSV are delivered now.
- Packaging, installers, or distribution. Building a standalone installer or
  bundled executable is out of scope.
- Changes to the pipeline transforms or the `mix-pipeline` CLI. The GUI drives the
  existing pipeline; the CLI surface is unchanged.
- A spreadsheet-to-image rendering library. The preview renders through a Qt table
  view within the approved dependency set; no image-rendering dependency is added.
