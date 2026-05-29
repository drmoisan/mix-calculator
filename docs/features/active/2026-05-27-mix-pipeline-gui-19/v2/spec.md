# 2026-05-27-mix-pipeline-gui — Spec (v2)

- **Issue:** #19 (https://github.com/drmoisan/mix-calculator/issues/19)
- **Owner:** drmoisan
- **Status:** Active
- **Version:** 2.0
- **Last Updated:** 2026-05-28
- **Supersedes:** Version 1.0 (PR #24; unit tests passed at 100% coverage but the assembled application's buttons did not deliver the user-facing behaviors).

## Overview

v1 shipped 333 passing tests at 100% line and branch coverage but the
assembled application's buttons did not deliver the user-visible behaviors.
v1 ACs were unit-anchored; no test asserted that clicking a button on the
assembled `MainWindow` produced the documented outcome. Three Export defects
surfaced: ExportDialog displayed an empty checklist (available tables set
after the dialog returned), the Save dialog had an empty filter, and
`CsvExporter` did not distribute multi-table output. The Render Tab path
never reached the shared `PreviewWidget`. Import buttons did not change
state on success. Run was not wired through a worker.

v2 reframes the feature around button-driven behavioral ACs: each AC must
pass at both the unit/integration level AND at the button-driven level (a
`qtbot` test clicks the actual button on the assembled `MainWindow` and
asserts user-visible state). v2 fixes the three Export defects, introduces a
runner abstraction so AC-6 is deterministic without polling, adds
view-protocol methods so the presenter drives button enable state, and
routes worksheet previews to the shared `PreviewWidget`. v2 is additive over
v1; no v1 commit is reverted.

## Behavior

Each subsection names the files that change and the behavioral-test
assertion. v2 retains v1 separation: presenters plain Python; widgets thin;
services and choosers injected at the composition root. Per-input source
selection (file + worksheet via `SourceInputWidget` /
`SourceSelectionPresenter` / `WorkbookReaderProtocol`) is unchanged from v1.

### 1. Render Tab preview with tab-change re-render (AC-1)

Per research Q1, the gap is wiring, not the widget. `PreviewWidget` is a
`QTableView` backed by a `QStandardItemModel`; the readable grid is the
user-visible "image" the AC requires.

- `src/gui/presenters/source_selection_presenter.py`: add optional
  `preview_sink: SourceSelectionViewProtocol | None` constructor parameter.
  `on_render_tab` additionally calls `preview_sink.show_preview(rows)` when
  set. The clear path (checkbox unchecked) calls
  `preview_sink.show_preview([])`.
- `src/gui/widgets/source_input_widget.py`: add `_on_tab_changed(sheet)`
  connected to `_tab_combo.currentTextChanged`. When the checkbox is checked
  and a path is set, emit `render_tab_requested(path, sheet)`. No new
  signal.
- `src/gui/app.py`: `build_application` passes `window.preview_widget` as
  `preview_sink` to each `SourceSelectionPresenter` and wires
  checkbox-unchecked to clear the preview.

Behavioral assertion (per research Q1, model-based pattern): checking the
Render Tab box leaves `window.preview_widget.model.rowCount() > 0`; changing
the tab combo while checked changes `model.item(0, 0).text()`; unchecking
leaves `model.rowCount() == 0`.

### 2. Per-input Import buttons with enable/disable on file-path change (AC-2, AC-3, AC-4)

Per research Q3, the presenter drives button state via an extended view
protocol; file-path change detection is held in the presenter.

- `src/gui/protocols.py`: add four methods to `PipelineViewProtocol` (see
  API surface).
- `src/gui/main_window.py`: promote four import buttons to public.
- `src/gui/presenters/pipeline_presenter.py`: add `_last_imported_path:
  dict[str, str | None]` initialized to all-`None`. Add
  `on_file_path_changed(key, path)`: when `path !=
  _last_imported_path[key]`, call `set_import_button_enabled(key, True)`.
  `on_import_one` / `on_import_all`: on success, set
  `_last_imported_path[key] = path` and call
  `set_import_button_enabled(key, False)`; on `ValueError`, surface and
  leave state unchanged.
- `src/gui/app.py`: extend `MainWindowPipelineView` with the four methods;
  `set_import_button_enabled(key, enabled)` routes to the public button and
  recomputes Import All as `any(...)`. Add three new connections: each
  per-input widget's `file_selected` binds via lambda to
  `on_file_path_changed(key, p)`.

Behavioral assertion: `qtbot.mouseClick(window.import_le_btn, ...)` leaves
the button disabled and `"LE" in pipeline_presenter.imported_tables`.
`set_path("different.xlsx")` re-enables; same path does not. Same pattern
for AOP and SKU_LU.

### 3. Import All disable-all rule (AC-5)

- `src/gui/presenters/pipeline_presenter.py`: `on_import_all` iterates the
  three loaders. On full success, all three `_last_imported_path` entries
  are set and `set_import_button_enabled(key, False)` is called for each.
  The adapter's Import All recompute then disables `import_all_btn`. On
  partial success, only successful keys are disabled; Import All stays
  enabled. `ValueError` is surfaced via `show_error`.

Behavioral assertion: after `qtbot.mouseClick(window.import_all_btn,
Qt.LeftButton)` with valid selections, all four import buttons are disabled.
After `set_path("new.xlsx")` on `le_widget`, only `import_le_btn` and
`import_all_btn` re-enable.

### 4. Run executes the transformation via an injected runner (AC-6)

Per Decision 3 and research Q6: v2 introduces `RunnerProtocol` so behavioral
tests inject a `SynchronousRunner` and assert post-run state without polling.

- New file `src/gui/runners.py`: `RunnerProtocol`, `ThreadedRunner`,
  `SynchronousRunner` (see API surface).
- `src/gui/app.py`: `build_application` accepts optional `runner:
  RunnerProtocol | None`. `ThreadedRunner` is the production default. The
  Run signal handler dispatches through the runner. `WiredApplication`
  exposes it.
- `src/gui/presenters/pipeline_presenter.py`: `can_run()` evaluates
  `working_tables` so Open also enables Run. Run-start calls
  `set_run_button_enabled(False)`; run-end calls
  `set_run_button_enabled(True)`.
- `tests/gui/test_pipeline_worker.py` remains unchanged and continues to
  prove the worker mechanism runs off-thread.

Behavioral assertion: with a `SynchronousRunner` injected,
`qtbot.mouseClick(window.run_btn, Qt.LeftButton)` leaves
`pipeline_presenter.derived_tables != {}` immediately. No wait primitive.

### 5. Save persists the working tables to a `.db` (AC-7)

- `src/gui/app.py`: `_handle_save` reads via
  `pipeline_presenter.working_tables`.
- `src/gui/presenters/pipeline_presenter.py`: pushes
  `set_save_button_enabled(True)` when working set is non-empty;
  `set_save_button_enabled(False)` when empty.

Behavioral assertion: with a fake `save_path_chooser` returning
`"results.db"`, `qtbot.mouseClick(window.save_btn, Qt.LeftButton)` records
the save call on the fake `PipelineService`.

### 6. Open loads tables and reflects load state on import buttons (AC-8)

Per research Q4: `on_open_db` calls `set_import_button_enabled(key, False)`
for each key matching a loaded table, calls `set_run_button_enabled(True)`,
and sets `_last_imported_path[key] = f"db:{db_path}"` as a sentinel so any
later `on_file_path_changed` with a real path re-enables the button.

Behavioral assertion: with a fake `open_path_chooser` returning `"test.db"`
and a fake `open_db` returning `{"LE": ..., "aop": ..., "sku_lu": ...}`,
`qtbot.mouseClick(window.open_btn, Qt.LeftButton)` leaves all four import
buttons disabled and `window.run_btn.isEnabled() == True`. A subsequent
`set_path("new.xlsx")` on `le_widget` re-enables only `import_le_btn` and
`import_all_btn`.

### 7. Export with checklist populated, Save dialog filter, CSV name-mangling (AC-9)

Per Decision 2 and research Q5, three v1 wiring defects are repaired.

- **Defect 1 (checklist-empty-when-shown).** v1
  `_handle_export` calls `set_available_tables(list(tables))` AFTER
  `export_dialog_runner(export_dialog)` returns. v2 calls it BEFORE invoking
  the dialog runner. ExportDialog checklist retained.
- **Defect 2 (missing Excel/CSV filter).** v1 passes an empty filter to
  `QFileDialog.getSaveFileName`. v2 passes
  `"Excel (*.xlsx);;CSV (*.csv)"` and parses the second tuple element
  (`"*.xlsx"` in `selected_filter` → `"Excel"`; `"*.csv"` → `"CSV"`).
  ExportDialog's format combo is removed; format lives in one place (the
  Save dialog filter). Dialog retains checklist and Export All.
- **Defect 3 (CSV name-mangling).** Per Decision 1, the Save dialog returns
  one path. Excel writes one workbook at that path with one worksheet per
  table. CSV strips `.csv` from the filename to derive a base and writes
  `<base>_<table_name>.csv` per table in the directory of the chosen path.
  Example: `C:/out/results.csv` → `C:/out/results_LE.csv`,
  `C:/out/results_aop.csv`, etc.
- Files: `src/gui/app.py` (reorder; rewrite `default_export_runner`),
  `src/gui/widgets/export_dialog.py` (drop format combo),
  `src/gui/exporters/csv_exporter.py` (implement
  `<base>_<table_name>.csv`).

Behavioral assertion: with a fake `export_dialog_runner` returning
`("Excel", "out.xlsx")`, `qtbot.mouseClick(window.export_btn, ...)` records
one call to the fake exporter with working-set keys and `"out.xlsx"`. With
`("CSV", "out.csv")` and three tables, `CsvExporter.export` writes
`out_<table_name>.csv` per table at the directory of `out.csv`.

### 8. UI conventions and testability (AC-11, carried from v1)

Presenters remain plain Python with no Qt imports. `PipelinePresenter` does
not become a `QObject` (per research Q6). Behavioral tests use `pytest-qt`
under `QT_QPA_PLATFORM=offscreen`; the test seam is `build_application` with
injected fakes for choosers and runner.

## Inputs / Outputs

### Inputs

- **LE / AOP / SKU_LU:** Excel workbook path + worksheet name. Defaults
  `"LE-8 + 4"`, `"AOP1"`, `"SKU_LU"`. SKU_LU workbook defaults to LE/AOP.
- **Save:** `.db` path via Save dialog filtered to `.db`.
- **Open:** existing `.db` path via Open dialog filtered to `.db`.
- **Export:** a single path via Save dialog filter
  `"Excel (*.xlsx);;CSV (*.csv)"`. Per Decision 1, format is resolved from
  the filter selection.

### Outputs

- **In-memory tables:** imported (`LE`, `aop`, `sku_lu`) and derived from
  `run_pipeline`.
- **SQLite `.db`:** every working table written through `src/pandas_io.py`
  on Save.
- **Excel export:** one workbook at the chosen path; one worksheet per
  table.
- **CSV export:** `<directory_of_chosen_path>/<base>_<table_name>.csv` per
  table, where `<base>` is the chosen filename with `.csv` stripped.

### Working set (new in v2)

The dict that Save, Export, and Run operate on:

- Post-import only: `imported_tables`.
- Post-run: `derived_tables` (includes `LE`, `aop`, `sku_lu` per v1).
- Post-open: `imported_tables` (loaded from `.db`).
- New import after a run clears `derived_tables`; Run must run again.
  Rationale: derived tables become stale when their inputs change.

`mix-pipeline` CLI unchanged. SQLite schema matches the CLI's; databases
remain interchangeable.

## API / CLI Surface

The v1 surfaces (`ImportSpec`, `PipelineServiceProtocol`,
`WorkbookReaderProtocol`, `ExporterProtocol`, `ExporterRegistry`,
view protocols, `build_application`, console entry point) are preserved. The
v2 additions follow.

### `RunnerProtocol` and concrete runners (new, per Decision 3)

New module `src/gui/runners.py` defines:

```python
class RunnerProtocol(Protocol):
    def run(
        self,
        task: Callable[[], dict[str, pd.DataFrame]],
        on_success: Callable[[dict[str, pd.DataFrame]], None],
        on_error: Callable[[str], None],
    ) -> None: ...
```

`ThreadedRunner` (production): constructs `PipelineWorker(task)`, moves it
to a `QThread`, wires `worker.finished` → `on_success` and `worker.error` →
`on_error`, starts the thread. `SynchronousRunner` (test): invokes `task()`
directly; calls `on_success` on return, `on_error(str(exc))` on exception.
`build_application(runner=None, ...)` constructs `ThreadedRunner()` when
`runner is None`. The runner is exposed on `WiredApplication`.

### `PipelineViewProtocol` extension (per research Q3/Q4)

Four new methods: `set_import_button_enabled(key, enabled)`,
`set_run_button_enabled(enabled)`, `set_save_button_enabled(enabled)`,
`set_export_button_enabled(enabled)`. `MainWindowPipelineView` implements all
four. `FakePipelineView` adds matching recording methods.

### `MainWindow` public-attribute promotion (per research Q3)

`_import_le_btn` → `import_le_btn`, `_import_aop_btn` → `import_aop_btn`,
`_import_skulu_btn` → `import_skulu_btn`, `_import_all_btn` →
`import_all_btn`. Removes name-mangling; enables direct addressing from both
the adapter and behavioral tests.

### `SourceSelectionPresenter.preview_sink` parameter (per research Q1)

Constructor gains keyword-only optional `preview_sink:
SourceSelectionViewProtocol | None = None`. `on_render_tab` calls
`preview_sink.show_preview(rows)` after `self._view.show_preview(rows)` when
the sink is set. Clear path calls `preview_sink.show_preview([])`.

### `SourceInputWidget._on_tab_changed` handler (per research Q1)

```python
self._tab_combo.currentTextChanged.connect(self._on_tab_changed)

def _on_tab_changed(self, sheet: str) -> None:
    if self._render_checkbox.isChecked() and self._path and sheet:
        self.render_tab_requested.emit(self._path, sheet)
```

### `PipelinePresenter.on_file_path_changed(key, path)` slot (per research Q3)

Re-enables the import button for `key` when `path !=
_last_imported_path[key]`. No-op on identical path. Connected per input in
`build_application`.

### `build_application` injectable parameters (per research Q6)

`build_application` gains keyword-only optional `save_path_chooser`,
`open_path_chooser`, `export_dialog_runner`, and `runner` parameters.
Production defaults when any is `None`. Behavioral tests pass a
`SynchronousRunner` and fake choosers.

### `default_export_runner` rewritten (Decision 2 / research Q5)

The v2 implementation runs `dialog.exec()` (returns `None` on cancel), then
calls `QFileDialog.getSaveFileName(dialog, "Export Destination", "",
"Excel (*.xlsx);;CSV (*.csv)")`. The returned `(path, selected_filter)` is
parsed: `"*.xlsx" in selected_filter` → `("Excel", path)`; `"*.csv"` →
`("CSV", path)`. `set_available_tables` MUST be called BEFORE
`dialog.exec()` (Defect 1).

## Data & State

### Presenter state (extended in v2)

| Field | Type | Description |
|---|---|---|
| `_import_specs` | `dict[str, ImportSpec \| None]` | Per-input selections (v1) |
| `_imported_tables` | `dict[str, pd.DataFrame]` | Imported frames (v1) |
| `_derived_tables` | `dict[str, pd.DataFrame]` | Derived frames; cleared on new import (v2) |
| `_db_path` | `str \| None` | Working DB path (v1) |
| `_is_running` | `bool` | In-flight job flag (v1) |
| `_last_imported_path` | `dict[str, str \| None]` | Per-input last-imported path; sentinel `"db:<path>"` after Open (v2) |

### `working_tables` property (new, per research Q2)

```python
@property
def working_tables(self) -> dict[str, pd.DataFrame]:
    return self._derived_tables if self._derived_tables else self._imported_tables
```

All callers (`on_save`, `_handle_export`, `on_export`, `can_run`) use this
property; v1 inline expressions are removed.

### Derived-table invalidation rule (new in v2)

When any new per-input import succeeds (`on_import_one`,
`on_import_all`), the presenter immediately sets `self._derived_tables = {}`.
The working set reverts to imported-only. Save and Export must not silently
emit stale derived data.

### State transitions

- `on_import_one` / `on_import_all`: imported_tables updated; derived
  cleared; `_last_imported_path[key] := path`;
  `set_import_button_enabled(key, False)`.
- `on_open_db`: imported_tables loaded; derived cleared;
  `_last_imported_path[k] := "db:<path>"` per loaded k;
  `set_import_button_enabled(k, False)` per loaded k;
  `set_run_button_enabled(True)` if any loaded.
- `on_run` [requires `working_tables` non-empty]: `runner.run(task,
  on_success, on_error)`. on_success: derived_tables populated. on_error:
  imported preserved, error surfaced.
- `on_file_path_changed(key, p)`: if `p != _last_imported_path[key]`,
  `set_import_button_enabled(key, True)`.

### Invariants (carried from v1)

Pure transforms. Typed I/O boundaries. Working tables in memory until Save.
Save uses `if_exists="replace"`. Open repopulates without modifying file.
No migration.

## Constraints & Risks

- **No new dependency.** PySide6 (`^6.11.1`) and `pytest-qt` already
  declared.
- **Behavioral test isolation (new).** Per `general-unit-test.md`, polling
  primitives are banned: `qtbot.waitUntil`, `QTest.qWait`, `time.sleep`,
  `QThread.sleep` must not appear in v2 behavioral test code. AC-6 uses
  `SynchronousRunner`; `qtbot.waitSignal` is retained only for the isolated
  worker test.
- **Runner injection point (new).** `RunnerProtocol` / `ThreadedRunner` /
  `SynchronousRunner` in `src/gui/runners.py` is the seam that lets
  behavioral tests assert post-run state without timing primitives. Exposed
  on `WiredApplication`.
- **Button-state semantics** cross widget/presenter/composition. Contract
  defined in the presenter; widgets do not decide they have been imported.
- **Working-set selection.** `working_tables` is the single definition.
- **Carried from v1:** I/O boundary discipline via `src/pandas_io.py`-style
  typed boundaries; no temp files in tests (use `BytesIO` and
  `sqlite3.connect(":memory:")`); 500-line file cap; `SKU Description` and
  `Category` confidential; Pyright strict applies; PR #24 v1 modules are
  the working base and no v1 commit is reverted.

## Implementation Strategy

### Files modified

- `src/gui/app.py` — extend `MainWindowPipelineView` with four new view
  methods; add per-input `file_selected` → `on_file_path_changed`
  connections; pass `window.preview_widget` as `preview_sink`; reorder
  `set_available_tables` and dialog in `_handle_export`; rewrite
  `default_export_runner`; accept optional `runner` and chooser parameters;
  expose `runner` on `WiredApplication`.
- `src/gui/main_window.py` — promote four import buttons to public.
- `src/gui/presenters/pipeline_presenter.py` — add `_last_imported_path`,
  `on_file_path_changed`, `working_tables`; invalidate `_derived_tables` on
  new import; update `on_import_one`, `on_import_all`, `on_open_db`,
  `can_run`, run dispatch, `on_save` for the new view methods.
- `src/gui/presenters/source_selection_presenter.py` — optional
  `preview_sink`; call in `on_render_tab` and clear path.
- `src/gui/widgets/source_input_widget.py` — add `_on_tab_changed`.
- `src/gui/widgets/export_dialog.py` — drop format combo; retain checklist
  and Export All.
- `src/gui/exporters/csv_exporter.py` — implement
  `<base>_<table_name>.csv`.
- `src/gui/protocols.py` — add four methods to `PipelineViewProtocol`.

### Files added

- `src/gui/runners.py` — `RunnerProtocol`, `ThreadedRunner`,
  `SynchronousRunner`. Classified T2 in `quality-tiers.yml`.

### Test files

Behavioral tests live in a new `tests/gui/integration/` directory so the
unit-test isolation invariant is preserved at the directory level.

- `integration/test_behavioral_preview.py` (AC-1),
  `integration/test_behavioral_import_buttons.py` (AC-2/3/4/5),
  `integration/test_behavioral_pipeline_run.py` (AC-6, `SynchronousRunner`),
  `integration/test_behavioral_dialogs.py` (AC-7/8/9),
  `integration/test_behavioral_composition.py` (AC-10).

Existing tests requiring extension (per research Q8):
`test_pipeline_presenter.py`, `test_source_selection_presenter.py`,
`test_source_input_widget.py`, `test_app_wiring.py`,
`test_app_wiring_defaults.py` (replace dialog.exec assertions with
filter-string parse), `test_app_composition.py`, `test_csv_exporter.py`,
`fakes/fake_views.py`, `_wiring_test_doubles.py`.

No new dependency. No feature flags. v2 is additive over v1; CLI remains
the fallback.

## Definition of Done

Each AC from `v2/issue.md` maps to its verifying test(s). AC-1 through AC-12
must pass at both the unit/integration level AND at the button-driven level.

- [ ] **AC-1 Render Tab** — `test_source_selection_presenter.py`
  (preview_sink), `test_source_input_widget.py` (_on_tab_changed),
  `test_preview_widget.py`, `integration/test_behavioral_preview.py`.
- [ ] **AC-2 Import LE** — `test_pipeline_presenter.py`,
  `test_pipeline_service.py`, `integration/test_behavioral_import_buttons.py`.
- [ ] **AC-3 Import AOP** — same tests as AC-2, parameterized for AOP.
- [ ] **AC-4 Import SKU_LU** — same tests as AC-2, parameterized for
  SKU_LU.
- [ ] **AC-5 Import All** — `test_pipeline_presenter.py` (full-success and
  partial-success), `integration/test_behavioral_import_buttons.py`.
- [ ] **AC-6 Run** — `test_pipeline_presenter.py`, `test_pipeline_worker.py`
  (off-thread proof, unchanged), `test_pipeline_service.py`,
  `integration/test_behavioral_pipeline_run.py` (`SynchronousRunner`).
- [ ] **AC-7 Save** — `test_pipeline_presenter.py`,
  `test_pipeline_service.py`, `integration/test_behavioral_dialogs.py`.
- [ ] **AC-8 Open** — `test_pipeline_presenter.py`
  (set_import_button_enabled assertions, sentinel),
  `integration/test_behavioral_dialogs.py`.
- [ ] **AC-9 Export** — `test_export_presenter.py`,
  `test_exporter_registry.py`, `test_excel_exporter.py`,
  `test_csv_exporter.py` (multi-file rule),
  `test_app_wiring_defaults.py` (filter-string parse),
  `integration/test_behavioral_dialogs.py` (checklist populated before
  display).
- [ ] **AC-10 Composition root** — `test_app_composition.py`,
  `test_app_wiring.py`, and the full `integration/` suite.
- [ ] **AC-11 Presentation without Qt event loop** — every
  `test_*_presenter.py` runs without a `QApplication`.
- [ ] **AC-12 Toolchain and coverage** — Black, Ruff, Pyright strict,
  Pytest pass; line >= 85%, branch >= 75%; no regression on changed lines
  per `.claude/rules/quality-tiers.md`.

## Seeded Test Conditions

Mirrors `v2/issue.md` "Test Conditions to Consider".

- [ ] **AC-1.** Two-sheet fixture: check Render Tab → `model.rowCount() > 0`;
  switch tab while checked → `model.item(0,0).text()` changes; uncheck →
  `model.rowCount() == 0`. Repeated for LE, AOP, SKU_LU.
- [ ] **AC-2/3/4.** Click runs loader and disables button; reselecting same
  path does NOT re-enable; different path DOES; `ValueError` leaves button
  enabled and surfaces error.
- [ ] **AC-5.** Click Import All disables all four; changing one per-input
  file re-enables exactly that button and Import All; `ValueError` on one
  loader leaves Import All enabled.
- [ ] **AC-6.** Disabled before import/open; enabled after; click populates
  `derived_tables` (via `SynchronousRunner`); failure preserves imported.
- [ ] **AC-7.** Disabled when working set empty; click opens `.db` Save
  dialog; fake chooser returning a path persists; cancel is a no-op.
- [ ] **AC-8.** Click opens `.db` Open dialog; accept loads tables and
  disables matching import buttons; Run becomes enabled; subsequent
  `set_path` re-enables only the changed input's button and Import All.
- [ ] **AC-9.** Checklist populated BEFORE dialog shown (Defect 1); Save
  filter `"Excel (*.xlsx);;CSV (*.csv)"` (Defect 2); `CsvExporter.export`
  writes `<base>_<table_name>.csv` per table (Defect 3).
- [ ] **Edge cases.** Same path no re-enable; cancel Save/Open/Export is
  no-op; `.db` with no tables surfaces clear error.
- [ ] **Negative flows.** `ValueError` on any loader; runner `on_error`;
  invalid `.db` path; empty working-set export rejected at presenter.
- [ ] **Unit coverage for new presenter logic.** `on_file_path_changed`
  (differ/identical/sentinel), `working_tables`, derived invalidation,
  `can_run` against `working_tables`.
- [ ] **Test seam.** `build_application(runner=SynchronousRunner(), ...)`
  yields a `WiredApplication` whose buttons are addressable and presenter
  state is assertable directly after each `qtbot.mouseClick`.
