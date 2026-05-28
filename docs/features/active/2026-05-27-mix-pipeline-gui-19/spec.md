# 2026-05-27-mix-pipeline-gui — Spec

- **Issue:** #19
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-27T20-59
- **Status:** Draft
- **Version:** 0.1

## Overview

The mix decomposition pipeline (`src/mix_pipeline.py`) is currently driven only
through a CLI. Running the pipeline end-to-end requires assembling the correct
Excel workbook, knowing the source-sheet names for each input table, and invoking
the command with the right flags. There is no interactive way to select input
files, confirm the correct worksheet tab for each input table, preview the source
data before import, run the pipeline, persist results, reopen a prior result
database, or export derived tables to other formats. A desktop GUI would make the
pipeline usable by non-CLI users and make input selection, preview, and export
self-service.

This feature adds a PySide6 desktop application that drives the existing pipeline
end-to-end. The agreed design follows the architecture research for Issue #19: an
MVP (Model-View-Presenter) passive-view structure, constructor-injected services,
a `PipelineService` seam around the existing loaders and transforms, a
`WorkbookReaderProtocol` for tab discovery and preview, and an extensible exporter
registry. The existing `mix-pipeline` CLI is unchanged.

## Behavior

The application drives the existing mix pipeline through PySide6 while preserving
the pure-transform / I/O-boundary separation already established in `src/`. Each
capability is realized through a passive Qt view (thin signal/slot wiring) and a
plain-Python presenter that holds the logic and calls injected services.

1. **Per-input-table source selection.** For each pipeline input table (LE, AOP,
   SKU_LU), a `SourceInputWidget` lets the user select an Excel file and choose
   the correct worksheet tab. The `SourceSelectionPresenter` records the
   per-input file path and selected sheet name into an `ImportSpec`.
2. **Tab discovery.** When a file is selected, the presenter calls
   `WorkbookReaderProtocol.get_sheet_names(path)` and pushes the result to the
   view via `set_tab_list(tabs)`. The widget renders the names in a dropdown.
3. **Optional tab preview.** A per-input "render tab" checkbox triggers
   `WorkbookReaderProtocol.read_sheet_preview(path, sheet_name, max_rows=200)`.
   The returned `list[list[str]]` populates a `QStandardItemModel` rendered in a
   `QTableView` (`PreviewWidget`). The preview reads at most `max_rows` rows to
   bound rendering cost for large tabs. A `QPixmap` rendering of the table can be
   produced with `widget.grab()` when an image-style preview is required.
4. **Import.** The `PipelinePresenter` imports one selected input or all selected
   inputs through the `PipelineService` seam. Per-input import uses
   `import_le` / `import_aop` / `import_skulu`; importing all uses
   `import_sources(spec)`. Imported frames are held in memory; import does not
   persist to disk.
5. **Run pipeline.** A Run control invokes `PipelineService.run_pipeline(tables)`
   off the UI thread via the `PipelineWorker` (a `QObject` moved to a `QThread`).
   The worker emits `finished(dict)` on success and `error(str)` on failure. The
   presenter updates view state on each signal and reports success or failure.
6. **Save to DB.** A Save control calls `PipelineService.save_to_db(tables, db_path)`,
   which writes every working table to a SQLite `.db` file through the
   `src/pandas_io.py` write boundary. This is the existing pipeline output sink.
7. **Open DB.** An Open control calls `PipelineService.open_db(db_path)`, which
   reads the known tables back through the `src/pandas_io.py` read boundary and
   loads them into the in-memory table set.
8. **Export.** An Export control opens an `ExportDialog` with a per-table
   checklist and an "export all" control. The `ExportPresenter` resolves the
   chosen format from the `ExporterRegistry` and calls
   `ExporterProtocol.export(tables, selected_names, destination_path)`. Excel and
   CSV are supported initially; additional formats are added by registering a new
   exporter, with no change to the presenter.
9. **UI conventions and testability.** All presentation logic lives in plain
   Python presenters with no Qt imports, exercised in pytest without a
   `QApplication`. Qt widgets are thin and exercised with `pytest-qt` under
   `QT_QPA_PLATFORM=offscreen`. Services are injected via constructor parameters
   at the composition root (`src/gui/app.py`); no DI framework is used.

## Inputs / Outputs

### Inputs

- **LE input:** an Excel workbook path plus the LE worksheet name. Default sheet
  name: `"LE-8 + 4"`.
- **AOP input:** an Excel workbook path plus the AOP worksheet name. Default
  sheet name: `"AOP1"`.
- **SKU_LU input:** an Excel workbook path (may be the same workbook as LE/AOP or
  a different one) plus the SKU lookup worksheet name. Default sheet name:
  `"SKU_LU"`.
- **Target database path:** a `.db` filesystem path for Save.
- **Open database path:** an existing `.db` filesystem path for Open.
- **Export selection:** a destination path, a chosen export format (Excel or
  CSV), and a per-table checklist (or "export all").

### Outputs

- **In-memory tables:** imported frames (`LE`, `aop`, `sku_lu`) and the full set
  of derived tables produced by `run_pipeline`.
- **SQLite `.db` file:** all working tables persisted through the
  `src/pandas_io.py` write boundary on Save (equivalent to the CLI output sink).
- **Exported files:** an Excel workbook (one sheet per selected table) or CSV
  files (one file per selected table) at the chosen destination.

### Config keys and defaults

- LE sheet default: `"LE-8 + 4"`.
- AOP sheet default: `"AOP1"`.
- SKU_LU sheet default: `"SKU_LU"`.
- SKU_LU workbook default: the LE/AOP workbook path when no separate SKU_LU file
  is selected (mirrors the CLI `--skulu-input` default).
- Preview row cap default: `max_rows=200`.

### Versioning or backward-compatibility constraints

- The existing `mix-pipeline` CLI surface (`build_parser`, `main`, and the
  `_import_sources` / `_persist_all` / `_print_summary` helpers) is unchanged.
- The SQLite schema written by Save matches the table set written by the CLI so
  databases remain interchangeable between the CLI and the GUI.

## API / CLI Surface

New programmatic surfaces are added under `src/gui/`. The existing
`mix-pipeline` CLI is unchanged.

### `ImportSpec` (dataclass)

`@dataclass(frozen=True)` carrying the per-input selections:

- `le_path: str`, `le_sheet: str`
- `aop_path: str`, `aop_sheet: str`
- `skulu_path: str`, `skulu_sheet: str`

### `PipelineServiceProtocol`

```python
class PipelineServiceProtocol(Protocol):
    def import_sources(self, spec: ImportSpec) -> dict[str, pd.DataFrame]: ...
    def import_le(self, path: str, sheet: str) -> pd.DataFrame: ...
    def import_aop(self, path: str, sheet: str) -> pd.DataFrame: ...
    def import_skulu(self, path: str, sheet: str) -> pd.DataFrame: ...
    def run_pipeline(self, tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]: ...
    def save_to_db(self, tables: dict[str, pd.DataFrame], db_path: str) -> None: ...
    def open_db(self, db_path: str) -> dict[str, pd.DataFrame]: ...
```

- `import_sources` and the per-input `import_*` methods call the existing loaders
  (`normalize_le.load_source` → `normalize` → `validate_tieouts`,
  `load_aop.load_aop`, `load_skulu.load_skulu`) and return in-memory frames. They
  do not write to disk. `import_sources` returns `{"LE": ..., "aop": ..., "sku_lu": ...}`.
- `run_pipeline` mirrors the topological run already in `mix_pipeline.main`
  (`pivot_le`, `pivot_aop`, `build_customer_lu`, `build_aop_norm`, `build_le_norm`,
  `build_aop_vs_le`, `build_mix_base`, then `run_transforms`) and returns the full
  derived table dict. It performs no I/O.
- `save_to_db` writes each frame through `src.pandas_io.write_table` on a single
  connection (equivalent to `_persist_all`).
- `open_db` reads the known tables through `src.pandas_io.read_table` and returns
  them keyed by table name.

### `WorkbookReaderProtocol`

```python
class WorkbookReaderProtocol(Protocol):
    def get_sheet_names(self, path: str) -> list[str]: ...
    def read_sheet_preview(self, path: str, sheet_name: str, max_rows: int = 200) -> list[list[str]]: ...
```

The real implementation enumerates sheets and reads cell values via
`openpyxl.load_workbook(path, read_only=True)` in-process (no temp files).

### `ExporterProtocol` and `ExporterRegistry`

```python
class ExporterProtocol(Protocol):
    @property
    def format_name(self) -> str: ...
    def export(self, tables: dict[str, pd.DataFrame], selected_names: list[str], destination_path: str) -> None: ...

class ExporterRegistry:
    def register(self, exporter: ExporterProtocol) -> None: ...
    def get(self, format_name: str) -> ExporterProtocol: ...
    def available_formats(self) -> list[str]: ...
```

Concrete exporters: `ExcelExporter` (one sheet per table via the openpyxl
engine) and `CsvExporter` (one file per table into a directory). Both wrap their
pandas calls through the typed-boundary style used in `src/pandas_io.py`.

### View Protocols

All view interfaces are `typing.Protocol` definitions in `src/gui/protocols.py`,
for example:

- `SourceSelectionViewProtocol`: `set_tab_list(tabs: list[str]) -> None`,
  `show_preview(rows: list[list[str]]) -> None`, `show_error(message: str) -> None`.
- `PipelineViewProtocol`: `set_running(is_running: bool) -> None`,
  `show_result(summary: str) -> None`, `show_error(message: str) -> None`.
- `ExportViewProtocol`: `set_table_list(names: list[str]) -> None`,
  `get_selected_names() -> list[str]`, `select_all_tables() -> None`.

Presenters receive the matching view Protocol and the required services via
constructor parameters. Tests substitute fakes implementing the same Protocols.

### GUI launch entry point

`src/gui/app.py` provides the `QApplication` bootstrap and composition root. It
constructs the real widgets, the `WorkbookReader`, the `PipelineService`, and the
`ExporterRegistry` (with `ExcelExporter` and `CsvExporter` registered), wires the
presenters, and shows the `MainWindow`. A console entry point launches this
function.

### Example flow (concise)

- Select LE/AOP/SKU_LU files and tabs → import all → run → save to
  `results.db` → reopen `results.db` → export selected tables to
  `export.xlsx` (Excel) or to a directory (CSV).

### Contracts and validation rules

- Loader validation (`ValueError` on unresolved columns, KEY mismatch, or tie-out
  failures) propagates from the loaders; the presenter surfaces it via
  `show_error`. The pipeline run does not raise `ValueError` for these cases.
- Export with no tables selected is rejected at the presenter before any exporter
  call.
- `run_pipeline` requires non-empty imported tables; Run is unavailable until
  import completes or a database is opened.

## Data & State

### Presenter state model

The `PipelinePresenter` owns the working state:

| State field | Type | Description |
|---|---|---|
| `_import_specs` | `dict[str, ImportSpec \| None]` | Per-input (LE/AOP/SKULU) current file+sheet selection |
| `_imported_tables` | `dict[str, pd.DataFrame]` | In-memory imported frames |
| `_derived_tables` | `dict[str, pd.DataFrame]` | Derived frames from `run_pipeline` |
| `_db_path` | `str \| None` | Current working DB path |
| `_is_running` | `bool` | Whether a pipeline or import job is in flight |

### State transitions

```
IDLE
  -> on_import(spec)  -> IMPORTING (worker in flight)
  -> on_open_db(path) -> LOADED   (db tables in memory)
  -> on_run() [requires imported_tables] -> RUNNING (worker in flight)

IMPORTING
  -> worker.finished -> IDLE (imported_tables populated, view updated)
  -> worker.error    -> IDLE (view shows error)

RUNNING
  -> worker.finished -> IDLE (derived_tables populated, view updated)
  -> worker.error    -> IDLE (view shows error)

LOADED / IDLE
  -> on_save(path)    -> persists working tables to SQLite
  -> on_export(spec)  -> ExportPresenter handles
```

### Data transformations and invariants

- Transforms remain pure functions in the existing `src/mix_*` modules. The GUI
  embeds no transform logic; `run_pipeline` orchestrates only.
- All Excel and SQLite I/O routes through typed boundaries: Excel reads through
  `WorkbookReaderProtocol` (preview) and the existing loaders / `src/pandas_io.py`
  (import), SQLite reads/writes through `src/pandas_io.py`.
- The in-memory table set is a `dict[str, pd.DataFrame]` keyed by SQLite table
  name; the same keying is used for import, run, save, open, and export.

### Caching or persistence details

- Working tables live in memory in the presenter until Save persists them.
- Save uses `if_exists="replace"` table semantics (matching `_persist_all`), so a
  Save overwrites prior table contents in the target `.db`.
- Open repopulates the in-memory set from a `.db` without modifying the file.

### Migration or backfill requirements

- None. The GUI writes the same SQLite table set as the CLI; existing databases
  remain readable.

## Constraints & Risks

- **PySide6 already declared** in `pyproject.toml` (`^6.11.1`); no new top-level
  dependency is expected. The Qt test facility `pytest-qt` is approved as a dev
  dependency (see Implementation Strategy).
- **I/O boundary discipline.** All Excel/SQLite I/O must continue to flow through
  `src/pandas_io.py`-style typed boundaries; transforms remain pure. The GUI must
  not embed transform logic.
- **Testability without temp files.** Repo policy prohibits runtime temp files in
  unit tests and external dependencies in unit tests; the design tests
  file/DB/Excel interactions behind injectable seams (`WorkbookReaderProtocol`,
  `PipelineServiceProtocol`, `ExporterProtocol`) using `BytesIO` and
  `sqlite3.connect(":memory:")`.
- **File size limit.** No production/test/script file may exceed 500 lines; the
  GUI suite is decomposed into cohesive modules under `src/gui/` and `tests/gui/`.
- **Confidentiality.** `SKU Description` and `Category` values are confidential
  and must never appear in tests, fixtures, or docs; only fabricated examples are
  permitted. Source workbooks and `.db` outputs remain gitignored.
- **Determinism.** GUI/preview rendering and any async work must be deterministic
  under test (controllable clock, no wall-clock sleeps) per the unit-test policy.
  Worker tests use `qtbot.waitSignal` (event-driven), not wall-clock waits; the
  banned APIs (`time.sleep`, `QThread.sleep`, `QTest.qWait`) must not appear in
  test code.
- **Pyright-strict Qt signal typing (risk).** `Signal` field declarations on
  `QObject` subclasses (for example `finished: Signal = Signal(dict)`) are a known
  challenge with PySide6 6.11 stubs and may surface unknown member types. If they
  do, signal access is wrapped behind a typed Protocol, the same containment
  pattern used in `src/pandas_io.py`. Whether the 6.11 stubs type these cleanly is
  **unverified** at spec time and must be confirmed at implementation.
- **Offscreen platform plugin (unverified).** Headless CI relies on
  `QT_QPA_PLATFORM=offscreen`. Whether PySide6 6.11 ships the `offscreen`
  platform plugin by default is **unverified**; implementation must confirm the
  plugin loads at runtime in CI before relying on it.
- **Spreadsheet preview approach.** The preview renders through a `QTableView`
  backed by data read via `WorkbookReaderProtocol`, within the approved
  dependency set (PySide6 + openpyxl/pandas). No spreadsheet-to-image library is
  added.

## Implementation Strategy

### Implementation scope (what changes, not sequencing)

- Add a new `src/gui/` package containing the composition root, main window, the
  `PipelineService` seam, view Protocols, services, widgets, presenters,
  exporters, and the worker. The existing pipeline and loader modules are not
  modified; `PipelineService` calls their existing programmatic APIs directly.

### `src/gui/` package layout

```
src/
  gui/
    __init__.py               (empty package marker, T4)
    app.py                    (QApplication entry point + composition root, T4)
    main_window.py            (QMainWindow shell, T3)
    pipeline_service.py       (PipelineService + PipelineServiceProtocol + ImportSpec, T2)
    protocols.py              (all view Protocols, T2)
    services/
      __init__.py
      workbook_reader.py      (WorkbookReaderProtocol + openpyxl impl, T3)
      db_service.py           (open_db / list_tables over sqlite3, T3)
    widgets/
      __init__.py
      source_input_widget.py  (per-input file+tab selector, T3)
      preview_widget.py       (QTableView-based tab preview, T3)
      export_dialog.py        (checklist + format selector, T3)
      progress_dialog.py      (indeterminate progress + cancel, T3)
    presenters/
      __init__.py
      source_selection_presenter.py  (T2)
      pipeline_presenter.py          (import / run / save / open, T2)
      export_presenter.py            (T2)
    exporters/
      __init__.py
      base.py                 (ExporterProtocol, T2)
      registry.py             (ExporterRegistry, T2)
      excel_exporter.py       (wraps pandas to_excel, T3)
      csv_exporter.py         (wraps pandas to_csv, T3)
    workers/
      __init__.py
      pipeline_worker.py      (QObject worker moved to QThread, T3)
```

### Mirrored `tests/gui/` layout

```
tests/
  gui/
    __init__.py
    fakes/
      __init__.py
      fake_views.py           (FakeSourceSelectionView, FakePipelineView, FakeExportView)
      fake_services.py        (FakeWorkbookReader, FakePipelineService, FakeDbService)
      fake_exporters.py       (FakeExporter for registry tests)
    test_source_selection_presenter.py
    test_pipeline_presenter.py
    test_export_presenter.py
    test_exporter_registry.py
    test_excel_exporter.py
    test_csv_exporter.py
    test_pipeline_service.py
    test_workbook_reader.py
    test_source_input_widget.py   (Qt; QApplication / qtbot)
    test_preview_widget.py        (Qt)
    test_export_dialog.py         (Qt)
    test_pipeline_worker.py       (Qt)
```

### `quality-tiers.yml` additions (with tiers)

| Module path | Tier |
|---|---|
| `src/gui/__init__.py` | T4 |
| `src/gui/app.py` | T4 |
| `src/gui/main_window.py` | T3 |
| `src/gui/pipeline_service.py` | T2 |
| `src/gui/protocols.py` | T2 |
| `src/gui/services/workbook_reader.py` | T3 |
| `src/gui/services/db_service.py` | T3 |
| `src/gui/widgets/*.py` | T3 |
| `src/gui/presenters/*.py` | T2 |
| `src/gui/exporters/base.py` | T2 |
| `src/gui/exporters/registry.py` | T2 |
| `src/gui/exporters/excel_exporter.py` | T3 |
| `src/gui/exporters/csv_exporter.py` | T3 |
| `src/gui/workers/pipeline_worker.py` | T3 |

Every new project entry must be classified before CI passes; an unclassified
project fails the tier-classification stage.

### Dependency changes and rationale

- Add `pytest-qt` as a **dev** dependency (approved by the user 2026-05-27). It is
  the single new dependency. It is used with the `qtbot` fixture for widget and
  worker-signal tests and is run with `QT_QPA_PLATFORM=offscreen` for headless CI.
  `qtbot.waitSignal` provides event-driven signal waits and automatic widget
  cleanup, reducing teardown-ordering risk. No other new dependency is added;
  PySide6, openpyxl, and pandas are already declared.

### Logging/telemetry additions and locations

- The GUI uses the standard `logging` module. Presenters log import/run/save/open
  outcomes at `info` and failures at `error`. No `print` statements for permanent
  behavior; user-facing messages route through the view (`show_error`,
  `show_result`).

### Rollout plan

- No feature flags. The GUI is additive and does not alter the CLI. The CLI
  remains the fallback path for running the pipeline.

## Definition of Done

Each acceptance criterion maps to its verifying test(s) per the research's
AC → module/test traceability table.

- [x] **Per-input (LE, AOP, SKU_LU) select Excel file and pick worksheet tab** —
  verified by `test_source_selection_presenter.py`, `test_source_input_widget.py`,
  `test_workbook_reader.py`.
- [x] **Selecting a file populates the tab dropdown** — verified by
  `test_source_selection_presenter.py` (FakeWorkbookReader returns sheet names).
- [x] **Optional per-input "render tab" checkbox shows a preview** — verified by
  `test_source_selection_presenter.py` and `test_preview_widget.py`.
- [x] **Import one or all selected files** — verified by
  `test_pipeline_presenter.py` and `test_pipeline_service.py`.
- [x] **Run button executes the pipeline and reports success/failure** — verified
  by `test_pipeline_presenter.py`, `test_pipeline_worker.py`, and
  `test_pipeline_service.py`.
- [x] **Save button persists to a SQLite `.db`** — verified by
  `test_pipeline_presenter.py` and `test_pipeline_service.py`.
- [x] **Open button loads tables from an existing `.db`** — verified by
  `test_pipeline_presenter.py` (and `db_service` coverage).
- [x] **Export: per-table checklist, export-all, Excel + CSV, extensible** —
  verified by `test_export_presenter.py`, `test_exporter_registry.py`,
  `test_excel_exporter.py`, `test_csv_exporter.py`, and `test_export_dialog.py`.
- [x] **Presentation logic testable without a live Qt event loop** — verified by
  all `test_*_presenter.py` running with no `QApplication`.
- [x] **Qt widgets tested with the Qt test facility** — verified by
  `test_*_widget.py`, `test_export_dialog.py`, and `test_pipeline_worker.py`
  using `pytest-qt` / `qtbot` under `QT_QPA_PLATFORM=offscreen`.
- [x] **Full toolchain passes** (Black, Ruff, Pyright strict, Pytest) and coverage
  meets repository thresholds (>= 85% line, >= 75% branch), with no coverage
  regression on changed lines.

## Seeded Test Conditions

- [ ] Unit coverage for presenters covering source selection, tab discovery,
      import, run, save, open, and export, exercised with mocked services.
- [ ] Negative flows: invalid or unreadable Excel file, workbook with no usable
      tab, pipeline run failure, save or open to an invalid path, and export with
      no tables selected.
- [ ] Edge cases: workbook with a single tab, duplicate tab names, a very large
      tab for preview (bounded by `max_rows`), and export-all versus
      partial-checklist selection.
- [ ] Boundary adapters: Excel tab enumeration, preview rendering, SQLite open,
      and multi-format export each tested behind their injected seam using
      `BytesIO` and `sqlite3.connect(":memory:")` (no temp files).
- [ ] Qt widget tests using `pytest-qt` for signal/slot wiring and widget state
      transitions under `QT_QPA_PLATFORM=offscreen`.
- [ ] Integration scenario: end-to-end select → import → run → save → reopen →
      export against fabricated fixtures.
