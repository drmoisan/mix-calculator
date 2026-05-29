# gui-render-import-ux — User Stories

- **Issue:** #27
- **Owner:** drmoisan
- **Last Updated:** 2026-05-28T23-25
- **Status:** Draft

These four user stories correspond to the four changes in the spec. Each story
uses the As a / I want / So that format with Given/When/Then acceptance
scenarios.

## Story 1 — Mutually-exclusive Render-tab selection

**As a** GUI user comparing source worksheets,
**I want** checking one input's Render-tab checkbox to uncheck the other two,
**so that** the shared preview always reflects a single, unambiguous source
selection.

### Acceptance scenarios

**Scenario 1.1 — Checking one box unchecks the others**

- Given the LE Render-tab checkbox is checked and the AOP and SKU_LU boxes are
  unchecked,
- When I check the AOP Render-tab checkbox,
- Then the AOP box is checked and the LE and SKU_LU boxes are unchecked.

**Scenario 1.2 — Switching selection does not clear the new preview**

- Given the LE Render-tab checkbox is checked and showing a preview,
- When I check the AOP Render-tab checkbox,
- Then the LE box is unchecked without triggering a preview clear, and the
  preview reflects the AOP selection rather than an empty grid.

**Scenario 1.3 — Zero-checked state is reachable**

- Given exactly one Render-tab checkbox is checked,
- When I uncheck that same checkbox,
- Then all three Render-tab checkboxes are unchecked and the shared preview is
  cleared.

## Story 2 — Responsive imports off the UI thread

**As a** GUI user importing a large workbook,
**I want** imports to run without freezing the window,
**so that** the application stays responsive while the workbook is read.

### Acceptance scenarios

**Scenario 2.1 — Per-input import dispatches through the runner**

- Given a valid file and worksheet are selected for an input,
- When I click that input's Import button,
- Then the import is dispatched through the runner seam, the imported table is
  recorded on success, the keyed import button is disabled, and the window
  remains responsive during the read.

**Scenario 2.2 — Import-all dispatches through the runner**

- Given valid files and worksheets are selected for all three inputs,
- When I click Import All,
- Then the import-all is dispatched through the runner seam and all three tables
  are recorded on success.

**Scenario 2.3 — Failed import surfaces an error and allows retry**

- Given a selected file or worksheet that the loader rejects,
- When I click that input's Import button,
- Then the loader's `ValueError` is surfaced as an error message, the keyed
  import button remains enabled so I can retry, and the window returns to idle.

**Scenario 2.4 — Busy state during import**

- Given an import has been dispatched,
- When the import task is in flight,
- Then the view reflects a busy state, and it returns to idle when the import
  completes (whether it succeeds or fails).

**Scenario 2.5 — Derived tables invalidated on re-import**

- Given a prior Run produced derived tables,
- When I successfully import a source again,
- Then the derived-table set is invalidated so a subsequent Run rebuilds it.

## Story 3 — Completion feedback for every control action

**As a** GUI user,
**I want** a clear confirmation message after each control action completes,
**so that** I know the action finished and what it produced.

### Acceptance scenarios

**Scenario 3.1 — Import-one completion message**

- Given a per-input import succeeds,
- When the import completes,
- Then the status bar shows a factual completion message naming the imported
  source (for example `"Imported LE."`).

**Scenario 3.2 — Import-all completion message**

- Given an import-all succeeds,
- When the import-all completes,
- Then the status bar shows a factual completion message indicating all three
  sources were imported (for example `"Imported all 3 sources."`).

**Scenario 3.3 — Error path is unchanged**

- Given an import fails,
- When the failure is reported,
- Then the status bar shows the error via the error surface and no success
  completion message is shown.

## Story 4 — Per-input Import buttons co-located with their controls

**As a** GUI user working with one input at a time,
**I want** each Import button next to the file, tab, and Render-tab controls it
operates on,
**so that** the relationship between a button and its input is visually obvious.

### Acceptance scenarios

**Scenario 4.1 — Per-input Import button inside its source widget**

- Given the main window is built,
- When I inspect a source input widget,
- Then that widget contains its own Import button alongside its file row, tab
  dropdown, and Render-tab checkbox, and the widget exposes the button via an
  `import_btn` attribute.

**Scenario 4.2 — Import All remains in the global control row**

- Given the main window is built,
- When I inspect the global control row,
- Then Import All is present alongside Run/Save/Open/Export, and the three
  per-input Import buttons are absent from that row.

**Scenario 4.3 — Existing enable/disable contract preserved**

- Given the presenter enables or disables a keyed import button through
  `set_import_button_enabled`,
- When the adapter resolves `window.import_le_btn` (or the AOP/SKU_LU
  equivalents),
- Then it resolves to the widget-owned button so the enable/disable behavior and
  existing tests work unchanged.

## Non-Goals

- Per-input tab discovery and tab preview reads remain on the UI thread; moving
  them off-thread is a follow-up, not part of this feature.
- In-flight import cancellation is not provided; the in-flight button is disabled
  to prevent a second dispatch.
- Import-all remains all-or-nothing; partial-success handling is out of scope.
- Export completion messaging is out of scope.
