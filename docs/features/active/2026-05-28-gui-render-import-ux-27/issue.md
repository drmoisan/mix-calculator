# gui-render-import-ux (Issue #27)

- Date captured: 2026-05-28
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/gui-render-import-ux/ (Issue #27)

- Issue: #27
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/27
- Last Updated: 2026-05-29
- Work Mode: full-feature

## Problem / Why

Four usability gaps in the mix-pipeline GUI reduce clarity and responsiveness:

1. The three per-input "Render tab" checkboxes (LE, AOP, SKU_LU) operate
   independently, so more than one preview source can appear selected at once.
   The preview surface is shared, so only one render selection is meaningful at
   a time.
2. Clicking "Import AOP" appears to freeze the window briefly. The import path
   runs the workbook read on the UI thread, so the event loop is blocked for the
   duration of the read.
3. After a control button completes its work there is no consistent confirmation
   that the action finished. Per-input Import and Import-All currently show no
   success message.
4. The per-input Import buttons (Import LE / Import AOP / Import SKU_LU) sit in
   the bottom control row, separated from the file/tab/checkbox controls they
   act on. Only "Import All" belongs with the global Run/Save/Open/Export
   controls.

## Proposed Behavior

1. Checking one "Render tab" checkbox unchecks the other two (single-selection
   behavior across the three source widgets).
2. Imports execute off the UI thread so the window stays responsive; the UI
   reflects a busy state during the import and returns to idle on completion.
3. Each completed button action reports a clear completion message to the user
   (status bar), including per-input Import and Import-All.
4. Each per-input Import button is co-located with its source widget's file/tab
   controls and Render-tab checkbox. "Import All" remains in the global control
   row with Run/Save/Open/Export.

## Acceptance Criteria

- [x] AC1: Checking any one Render-tab checkbox (LE, AOP, or SKU_LU) unchecks the
      other two, leaving exactly one checked.
- [x] AC2: Programmatically unchecking the two displaced checkboxes during an
      exclusivity switch does not invoke `on_clear_preview` and does not clear the
      preview produced by the newly-checked widget.
- [x] AC3: The user can uncheck the currently-active Render-tab checkbox, leaving
      all three unchecked (zero-checked state) and clearing the shared preview.
- [x] AC4: Per-input import is dispatched through the injected `RunnerProtocol`
      (verified deterministically with `SynchronousRunner`), not called directly
      on the presenter from the signal handler.
- [x] AC5: Import-all is dispatched through the injected `RunnerProtocol`
      (verified deterministically with `SynchronousRunner`).
- [x] AC6: A successful import disables its keyed import button; a failed import
      (loader `ValueError`) leaves the keyed import button enabled and routes the
      message to `show_error`.
- [x] AC7: A successful import invalidates the derived-table set so a downstream
      Run rebuilds.
- [x] AC8: The view reflects a busy state while an import is in flight and returns
      to idle on completion (success or error).
- [x] AC9: A successful import-one displays a factual completion message in the
      status bar via `show_result` (for example `"Imported LE."`).
- [x] AC10: A successful import-all displays a factual completion message in the
      status bar via `show_result` (for example `"Imported all 3 sources."`).
- [x] AC11: Each per-input Import button renders inside its `SourceInputWidget`,
      and `SourceInputWidget` exposes the button via an `import_btn` attribute.
- [x] AC12: Import All remains in the global control row, and the three per-input
      Import buttons are absent from the global control row.
- [x] AC13: `MainWindow.import_le_btn`, `import_aop_btn`, and `import_skulu_btn`
      resolve to the widget-owned buttons so
      `MainWindowPipelineView.set_import_button_enabled` and existing tests work
      unchanged.
- [x] AC14: The toolchain passes (format -> lint -> type-check -> test) with line
      coverage >= 85% and branch coverage >= 75%, no regression on changed lines.

## Constraints & Risks

- MVP passive-view architecture: presenters hold no Qt; widgets are passive.
  Cross-widget checkbox coordination and off-thread dispatch must be wired at
  the composition root, not inside presenters.
- Off-thread import must preserve the existing import button enable/disable and
  derived-table invalidation semantics.
- The existing `MainWindowPipelineView.set_import_button_enabled` references the
  per-input buttons by attribute; relocating the buttons must keep that contract
  intact.
- Test seam parity: the `SynchronousRunner` test seam must remain usable for the
  import path to keep behavioral tests deterministic.

## Test Conditions to Consider

- [x] Mutual-exclusion: checking each checkbox unchecks the others; unchecking
      clears the shared preview.
- [x] Import dispatched through the runner seam (synchronous in tests); success
      and error callbacks update button state and status.
- [x] Completion message shown for import-one, import-all, run, save, open,
      export.
- [x] Layout: per-input Import button present in each source widget; Import All
      present in the control row; per-input Import buttons absent from the
      control row.

## Next Step

- [ ] Promote to GitHub issue (feature request template)
- [ ] Create `docs/features/active/gui-render-import-ux/` folder from the template