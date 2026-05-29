# gui-render-import-ux — Spec

- **Issue:** #27
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-28T23-25
- **Status:** Draft
- **Version:** 0.2

## Overview / Goal

The mix-pipeline PySide6 GUI has four usability gaps that reduce clarity and
responsiveness. This feature closes those gaps without altering pipeline
computation or persisted output:

1. The three per-input "Render tab" checkboxes (LE, AOP, SKU_LU) toggle
   independently, so more than one preview source can appear selected at once.
   The preview surface is shared, so only one render selection is meaningful at
   a time.
2. A per-input import (notably "Import AOP") runs the workbook read on the UI
   thread, so the Qt event loop is blocked for the duration of the read and the
   window appears to freeze.
3. Per-input Import and Import-All complete silently. There is no consistent
   status-bar confirmation that the action finished, unlike Run/Save/Open.
4. The per-input Import buttons sit in the bottom control row, separated from
   the file/tab/Render-tab controls they act on.

The goal is to make render selection unambiguous (single-selection), keep the
window responsive during imports, give every completing control action a
factual completion message, and co-locate each per-input Import button with the
controls it operates on. The change is confined to the GUI presentation and
composition layers; no transform, loader, or persistence logic changes.

## Scope

### In scope

- Mutually-exclusive Render-tab checkbox behavior across the three source
  widgets, wired at the composition root.
- Dispatch of per-input import and import-all through the existing
  `RunnerProtocol` seam so the workbook read runs off the UI thread.
- Status-bar completion messages for import-one and import-all (success path).
- Relocation of each per-input Import button into its `SourceInputWidget`,
  leaving only Import All in the global control row.
- Presenter task/callback methods supporting off-thread import dispatch.
- Unit and behavioral tests covering the four changes, deterministic via the
  `SynchronousRunner` seam.

### Out of scope

- Per-input tab discovery (`SourceSelectionPresenter.on_file_selected`) and tab
  preview reads (`SourceSelectionPresenter.on_render_tab`) remain on the UI
  thread. Both call the workbook reader synchronously and can block on a large
  file. Moving these off the UI thread is recorded as a **follow-up work item**
  and is explicitly not delivered by issue #27.
- Cancellation of an in-flight import (the in-flight button is disabled; a
  second dispatch for the same key is not initiated).
- Partial-success semantics for import-all; the operation remains all-or-nothing
  (a service `ValueError` fails the whole import-all), matching current
  on-thread behavior.
- Export completion messaging (handled by `ExportPresenter`, outside this
  presenter's view contract).
- Any change to pipeline computation, derived-table contents, or persisted
  database/export output.

## Functional Requirements

### Change 1 — Mutually-exclusive Render-tab checkboxes

- Checking any one of the three Render-tab checkboxes (LE, AOP, SKU_LU) must
  uncheck the other two.
- The displaced checkboxes must not emit spurious side effects when they are
  programmatically unchecked. Specifically, the existing `_make_preview_clear`
  closure (which calls `on_clear_preview()` on `toggled(False)`) and the
  widget-internal `_on_render_toggled` handler must not fire for the two boxes
  the exclusivity handler clears. The shared preview that the newly-checked
  widget is about to render must not be cleared as a side effect of the
  displacement.
- The zero-checked state must remain reachable: the user can uncheck the
  currently-active checkbox by clicking it, leaving all three unchecked and the
  preview cleared. The exclusivity behavior does not force one box to stay
  checked.
- The exclusivity handler fires only on a check-to-`True` transition. Unchecking
  (a `toggled(False)`) invokes only the existing clear-preview path, unchanged.

### Change 2 — Off-UI-thread imports

- A per-input import request and an import-all request must be dispatched through
  the injected `RunnerProtocol` (production `ThreadedRunner`, deterministic
  `SynchronousRunner` in tests), so the workbook read runs off the UI thread in
  production. The pattern mirrors the existing Run dispatch in
  `wire_control_signals._handle_run`.
- The import task callable returns `dict[str, pd.DataFrame]` to match the runner
  task signature: a one-entry dict `{name: frame}` for import-one and a
  three-entry dict for import-all. No change to `RunnerProtocol` is required.
- The following existing semantics must be preserved across the move:
  - **Import-button enable/disable.** The keyed import button is disabled on
    successful import; on failure it remains enabled so the user can retry. The
    Import-All disjunction recompute in `set_import_button_enabled` is preserved.
    To prevent a double-dispatch, the keyed button (and Import All for
    import-all) is disabled at dispatch time, before the task runs.
  - **Derived-table invalidation.** A successful import clears `_derived_tables`
    so a downstream Run rebuilds. This rule applies to both import-one and
    import-all and now lives in the success callbacks.
  - **`ValueError` → `show_error` routing.** A loader/service `ValueError` raised
    inside the task callable is caught at the runner boundary and routed to the
    error callback, which calls `view.show_error`. Non-`ValueError` exceptions
    are also caught at the runner boundary and surfaced as a stringified message,
    so the UI thread always receives a string.
  - **Busy/idle state.** The view reflects a busy state while an import is in
    flight and returns to idle on completion (success or error), consistent with
    the Run path's `set_running` behavior.
- Per-input tab discovery and preview reads remain synchronous on the UI thread
  (see Out of scope / follow-up).

### Change 3 — Completion feedback

- On a successful import-one, the view must display a factual completion message
  in the status bar via `show_result`, parallel to the existing Run/Save/Open
  messages. Recommended wording: `"Imported {name}."` (for example
  `"Imported LE."`).
- On a successful import-all, the view must display a completion message via
  `show_result`. Recommended wording: `"Imported all 3 sources."`.
- Messages must be factual and professional per `.claude/rules/tonality.md`: no
  exclamation, no hyperbole, no filler. The message is emitted only on the
  success path; the error path continues to route through `show_error`.
- Run, Save, and Open already emit completion messages; this change does not
  alter their wording. Export messaging is out of scope.

### Change 4 — Layout relocation

- Each per-input Import button (`Import LE`, `Import AOP`, `Import SKU_LU`) must
  render inside its corresponding `SourceInputWidget`, co-located with that
  widget's file row, tab dropdown, and Render-tab checkbox.
- Import All must remain in the global control row alongside Run, Save, Open, and
  Export. The three per-input Import buttons must be absent from the global
  control row.
- The relocation must preserve the existing
  `MainWindowPipelineView.set_import_button_enabled` contract, which addresses
  the buttons through `window.import_le_btn` / `import_aop_btn` /
  `import_skulu_btn`. These attributes are re-exposed as `MainWindow` properties
  that delegate to the widget-owned buttons, so the adapter and existing tests
  resolve unchanged.
- The `import_one_requested` signal continues to be emitted with the import key
  (`"LE"`, `"aop"`, `"sku_lu"`) when the per-input button is clicked; the wiring
  reads the button from the widget.

## Architecture / Design

- **MVP passive-view boundary.** Presenters hold no Qt and are testable without a
  `QApplication`. Widgets are passive views implementing the Protocols in
  `src/gui/protocols.py`. Cross-widget checkbox coordination (Change 1) and
  off-thread dispatch (Change 2) are behaviors that span widgets or the
  execution context, so they are wired at the composition root
  (`build_application` / `wire_control_signals` in `src/gui/app.py`), not inside
  a presenter or a widget.
- **Runner seam.** `RunnerProtocol` (`src/gui/runners.py`) is the single
  injection point for execution strategy. `ThreadedRunner` runs the task on a
  worker `QThread` via `PipelineWorker`; `SynchronousRunner` runs it in-process
  on the calling thread and is injected in tests. Import dispatch reuses this
  seam unchanged — the import task is a `Callable[[], dict[str, pd.DataFrame]]`,
  exactly the signature the runner already accepts. `PipelineWorker` is reused
  without modification.
- **Composition-root wiring for exclusivity.** Change 1 uses signal wiring with
  `blockSignals` re-entrancy guards rather than `QButtonGroup`. `QButtonGroup`
  exclusive mode would forbid the zero-checked state and would not suppress the
  existing `_make_preview_clear` path, producing spurious preview clears on the
  two displaced boxes. A composition-root closure connected to each checkbox's
  `toggled` signal, which unchecks the other two while their signals are blocked,
  satisfies the requirement and preserves the zero-checked state.
- **Presenter task/callback symmetry.** The import path mirrors the Run path's
  `make_run_task` / `on_run_success` / `on_run_error` structure. State mutation
  (recording the frame, path tracking, derived-table invalidation, button-state
  pushes, completion message) moves into the success callbacks; the task
  callable performs only the loader call and returns the frame dict.
- **Layout ownership.** `SourceInputWidget` gains an optional import button as a
  layout child (a passive UI element with no logic). Domain routing stays at the
  composition root (`MainWindow` signal lambda → presenter). `MainWindow`
  re-exports the widget buttons via properties so the existing attribute-based
  contract is unchanged.

## API / Signature Changes

### `PipelinePresenter` (`src/gui/presenters/pipeline_presenter.py`)

New public methods supporting off-thread import dispatch:

- `make_import_one_task(name: str, spec: ImportSpec) -> Callable[[], dict[str, pd.DataFrame]]`
  — returns a zero-argument callable that loads the frame for `name` and returns
  `{name: frame}`. Raises `ValueError` from the loader inside the callable (the
  runner boundary catches and routes it).
- `on_import_one_success(result: dict[str, pd.DataFrame]) -> None` — records the
  imported frame, updates `_last_imported_path`, invalidates `_derived_tables`,
  disables the keyed import button, recomputes Run/Save/Export states, clears the
  busy state, and emits the import-one completion message via `show_result`.
- `on_import_one_error(message: str) -> None` — routes to `view.show_error`,
  clears the busy state, and leaves the import button enabled for retry.
- `make_import_all_task(spec: ImportSpec) -> Callable[[], dict[str, pd.DataFrame]]`
  — returns a callable that calls `service.import_sources(spec)` and returns the
  three-entry dict.
- `on_import_all_success(result: dict[str, pd.DataFrame]) -> None` — records the
  imported frames, updates per-key paths, invalidates `_derived_tables`, disables
  the keyed buttons, recomputes Run/Save/Export states, clears the busy state,
  and emits the import-all completion message via `show_result`.
- `on_import_all_error(message: str) -> None` — routes to `view.show_error` and
  clears the busy state.

The existing synchronous `on_import_one` / `on_import_all` may be retained as
internal helpers invoked by the task callables or refactored so their success
logic lives in the new callbacks; the public surface grows but does not break.
The `PipelineViewProtocol` is unchanged — `show_result`, `show_error`,
`set_running`, and `set_import_button_enabled` already exist.

### `SourceInputWidget` (`src/gui/widgets/source_input_widget.py`)

- Constructor gains an optional parameter, recommended `import_label: str | None = None`.
  When supplied (or defaulted from `input_label`), the widget constructs an
  import `QPushButton` and adds it to its `QVBoxLayout`. When `None`, no import
  button is created (backward-compatible construction).
- New read-only attribute/property `import_btn: QPushButton` exposing the
  widget's import button, used by `MainWindow` for signal wiring and re-export.

### `MainWindow` (`src/gui/main_window.py`)

- Removes per-input import button construction from `__init__` and from the
  global `controls_row` (Import All, Run, Save, Open, Export remain).
- Adds read-only properties delegating to the widget-owned buttons:
  - `import_le_btn -> QPushButton` → `self.le_widget.import_btn`
  - `import_aop_btn -> QPushButton` → `self.aop_widget.import_btn`
  - `import_skulu_btn -> QPushButton` → `self.skulu_widget.import_btn`
- Wires each widget button's `clicked` signal to emit `import_one_requested` with
  the matching key, reading the button through the widget.

### `app.py` composition root (`src/gui/app.py`)

- `build_application` adds the exclusivity handler wiring for the three Render-tab
  checkboxes (composition-root closure with `blockSignals` guards), layered after
  the existing `_make_preview_clear` wiring.
- `wire_control_signals._handle_import_one` and `_handle_import_all` are updated
  to build the presenter task and dispatch through the injected `runner`,
  disabling the relevant button(s) before dispatch and routing success/error to
  the new presenter callbacks. No signature change to `wire_control_signals`
  (the `runner` parameter already exists).

## Test Strategy

Tests follow `.claude/rules/general-unit-test.md` and `.claude/rules/python.md`:
Arrange–Act–Assert, one behavior per test, deterministic, no runtime temp files,
no external services. Coverage must remain ≥ 85% line and ≥ 75% branch with no
regression on changed lines.

### Unit tests (presenter, no `QApplication`)

- `make_import_one_task` returns a callable producing `{name: frame}` for each
  key; the callable raises `ValueError` when the loader fails.
- `on_import_one_success` records the frame, sets the last-imported path,
  invalidates derived tables, disables the keyed button, recomputes
  Run/Save/Export, clears busy state, and emits the expected completion message
  via the fake view's `show_result`.
- `on_import_one_error` routes the message to `show_error`, clears busy state,
  and leaves the import button enabled.
- `make_import_all_task` / `on_import_all_success` / `on_import_all_error`
  equivalents, asserting the three-entry result, per-key path tracking, and the
  import-all completion message.
- Completion-message wording assertions parallel to the existing Run/Save/Open
  message tests.

### Behavioral / integration tests (fully wired, `SynchronousRunner`)

- Mutual exclusion: checking each Render-tab checkbox in turn leaves exactly that
  box checked and the other two unchecked; checking one box does not clear a
  preview the checked widget produces (no spurious `on_clear_preview`).
- Zero-checked reachable: unchecking the active box leaves all three unchecked
  and clears the preview.
- Import dispatch through the runner seam: clicking a per-input Import button (and
  Import All) with `SynchronousRunner` populates the imported tables
  synchronously, disables the keyed button on success, and shows the completion
  message; a loader `ValueError` routes to `show_error` and leaves the button
  enabled.
- Busy/idle: the view reflects busy during dispatch and idle after completion.
- Layout: each `SourceInputWidget` exposes `import_btn`; `MainWindow` exposes
  `import_le_btn` / `import_aop_btn` / `import_skulu_btn` resolving through the
  widget; Import All is present in the control row; the three per-input Import
  buttons are absent from the control row.
- Existing `set_import_button_enabled` adapter tests and
  `test_behavioral_import_buttons` tests continue to pass unchanged through the
  re-export properties.

### Determinism

- All import and run dispatch in tests uses `SynchronousRunner` so callbacks fire
  in-process before assertions. No `QThread`, no sleeps, no timing hacks.
- `blockSignals`-guarded exclusivity is verified by asserting checkbox states and
  the absence of spurious clear-preview calls on a recording fake, not by timing.

## Risks & Mitigations

- **Spurious preview clear on exclusivity (Change 1).** Programmatically
  unchecking the displaced boxes could trigger `_make_preview_clear` and
  `_on_render_toggled`, clearing the preview the newly-checked widget renders.
  Mitigation: guard the `setChecked(False)` calls with `blockSignals(True/False)`
  so the displaced boxes emit no signals; verify with a behavioral test that the
  preview is not cleared on a cross-checkbox switch.
- **Double-dispatch of an import (Change 2).** A user could click an Import
  button again before an in-flight import completes. Mitigation: disable the
  keyed button at dispatch time; re-enable only on the relevant outcome per
  existing rules. Cancellation is out of scope.
- **Regression in button-state or path-tracking semantics (Change 2).** Moving
  success logic into callbacks risks dropping a state push. Mitigation: keep the
  callback logic a direct extraction of the current `on_import_one` /
  `on_import_all` success paths; cover each pushed state with a unit test.
- **Breaking the `set_import_button_enabled` attribute contract (Change 4).**
  Relocating buttons could break the adapter and ~30 test references.
  Mitigation: re-export via `MainWindow` properties so `window.import_le_btn`
  resolves unchanged; no test rewrite required.
- **Hidden UI-thread blocking remains (out of scope).** Tab discovery and preview
  reads still block on the UI thread for large files. Mitigation: explicitly
  documented as a follow-up; not claimed as resolved by #27.

## Acceptance Criteria

1. - [ ] Checking any one Render-tab checkbox (LE, AOP, or SKU_LU) unchecks the
     other two, leaving exactly one checked.
2. - [ ] Programmatically unchecking the two displaced checkboxes during an
     exclusivity switch does not invoke `on_clear_preview` and does not clear the
     preview produced by the newly-checked widget.
3. - [ ] The user can uncheck the currently-active Render-tab checkbox, leaving
     all three unchecked (zero-checked state) and clearing the shared preview.
4. - [ ] Per-input import is dispatched through the injected `RunnerProtocol`
     (verified deterministically with `SynchronousRunner`), not called directly
     on the presenter from the signal handler.
5. - [ ] Import-all is dispatched through the injected `RunnerProtocol`
     (verified deterministically with `SynchronousRunner`).
6. - [ ] A successful import disables its keyed import button; a failed import
     (loader `ValueError`) leaves the keyed import button enabled and routes the
     message to `show_error`.
7. - [ ] A successful import invalidates the derived-table set so a downstream
     Run rebuilds.
8. - [ ] The view reflects a busy state while an import is in flight and returns
     to idle on completion (success or error).
9. - [ ] A successful import-one displays a factual completion message in the
     status bar via `show_result` (for example `"Imported LE."`).
10. - [ ] A successful import-all displays a factual completion message in the
      status bar via `show_result` (for example `"Imported all 3 sources."`).
11. - [ ] Each per-input Import button renders inside its `SourceInputWidget`,
      and `SourceInputWidget` exposes the button via an `import_btn` attribute.
12. - [ ] Import All remains in the global control row, and the three per-input
      Import buttons are absent from the global control row.
13. - [ ] `MainWindow.import_le_btn`, `import_aop_btn`, and `import_skulu_btn`
      resolve to the widget-owned buttons so
      `MainWindowPipelineView.set_import_button_enabled` and existing tests work
      unchanged.
14. - [ ] The toolchain passes (format → lint → type-check → test) with line
      coverage ≥ 85% and branch coverage ≥ 75%, no regression on changed lines.
