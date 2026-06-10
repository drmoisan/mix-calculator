# Remediation Inputs — Issue #62, Cycle 1

- Entry timestamp: 2026-06-10T12-24
- Issue: #62
- Branch: fix/edit-schema-columns-assignment
- PR: #63 (open, not merged)
- Trigger: Functional FAIL discovered by user verification after the PR was opened. The delivered fix (AC-1..AC-4, alias-seeding in `ColumnsTabPresenter.prepopulate()`) passed local audit and CI but does not fix the user-observable behavior. The user also added two adjacent UI requirements for the same dialog.

## Canonical issue number

Canonical issue number for this feature is 62. All artifact content, file paths, and cross-references must use this number.

## Evidence (verified by code inspection + user screenshot)

User screenshot (editing the AOP schema): the Schema Builder "Columns" tab shows the 26 canonical columns (Super Category, KEY, YTD/YTG, Customer, SKU Descripiton, SKU #, Type, GtN Mapping, Jan, Feb, ...) each labelled "(unassigned)", and the "Source columns" pool is empty.

Root cause (two compounding defects):

1. **The bundled default schemas carry empty aliases.** `src/schemas/default_aop.schema.json` declares every column with `"aliases": []`; the source→canonical mapping is implicit (the `canonical_name` equals the worksheet header, e.g. "Customer", "SKU #", "Jan"). The cycle-0 fix seeded assignments only from persisted aliases, so for the default schemas it seeds nothing. The alias-seeding change is valid but addresses a case (user-customized schemas with aliases) that the default schemas do not exercise.

2. **The Edit Schema path provides no source columns.** `wire_edit_schema_buttons` in `src/gui/_schema_discovery_wiring.py` opens the builder via `open_schema_builder(window, service, ...)` with **no `preview_slice`**, then calls `load_existing(name)`. With no preview slice, `DragTabBinder.set_columns` rebuilds an empty source pool and `ColumnsTabPresenter.prepopulate()` has nothing to fuzzy-match against. By contrast, the "Build/Edit schema" button (`wire_build_schema_buttons` → `_SchemaBuildSpecProvider.build_spec_for` → `_masked_preview_slice`) DOES seed a source pool, which is why the build path renders assignments. The two buttons diverge: edit loads the real schema but no source pool; build seeds a (synthetic) source pool but a fresh/seeded schema.

## Relevant verified seams (for planning)

- `SourceSelectionPresenter` (`src/gui/presenters/source_selection_presenter.py`) holds a `WorkbookReaderProtocol` (`.reader` property) and reads `read_sheet_preview(path, sheet, max_rows=_HEADER_PREVIEW_ROWS)`. The module-level helper `_best_header_row(rows, service)` selects the real header row (handles the AOP1 stray-leading-rows / header-row-2 layout). This is the exact path that must produce the Edit builder's source columns.
- `wire_edit_schema_buttons(window, service)` is invoked from `wire_schema_discovery_and_gating`, which already receives `le_presenter`, `aop_presenter`, `skulu_presenter` (each carries `.reader`). The edit wiring can be given the per-tab presenter (or a header-provider callable) without changing the external composition-root call.
- `open_schema_builder(..., preview_slice=...)` already accepts a `preview_slice`; it seeds the dialog/binder via `seed_dialog_preview_slice` before `load_existing` runs, and `DragTabBinder` retains the slice across `set_columns`. So passing the real-header `preview_slice` into the edit open path makes `prepopulate()` match canonical columns to the real headers. The widget exposes `current_path()`, `current_sheet()`, `current_schema()`.
- `SchemaBuilderDialog` (`src/gui/widgets/schema_builder_dialog.py`) is a `QDialog`. It sets only `setWindowTitle`; it does not set min/max window flags. Default `QDialog` on Windows shows only the close button (resizable but no min/max). Adding `Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint` (keeping the close hint and `Qt.Window`) provides the controls.
- `build_columns_tab()` (`src/gui/widgets/_schema_builder_tabs.py`) places `ColumnsTabWidget` directly in a `QVBoxLayout`. No `QScrollArea` is used anywhere in `src/gui` today. Wrapping the columns content in a `QScrollArea` with `setWidgetResizable(True)` provides vertical scrolling.

## Required outcomes (map to issue.md acceptance criteria)

- AC-5: Edit Schema populates the source-column pool from the selected worksheet's real headers (reader + best-header-row, honoring the detected header row).
- AC-6: With the pool populated, matching canonical columns render as assigned (name / persisted alias / fuzzy threshold). Editing `default_aop` against the AOP worksheet shows Customer→Customer, SKU #→SKU #, Jan→Jan, etc.
- AC-7: Columns tab is vertically scrollable (26 AOP columns must all be reachable).
- AC-8: Schema Builder window is resizable with minimize and maximize/restore controls.
- AC-9: Edit path degrades gracefully with no file/worksheet selected (no crash; empty pool), preserving the issue #50 no-file/no-sheet seam guard.

Retain the cycle-0 AC-1..AC-4 behavior and tests (alias-seeding remains a valid fallback for schemas that do carry aliases). Do not regress the "Build/Edit schema" build path or the schema-discovery flow.

## Constraints

- Python toolchain: Black → Ruff → Pyright → Pytest. Coverage >= 85% line / >= 75% branch, no regression on changed lines.
- 500-line file-size cap on ALL changed production AND test files. `src/gui/widgets/source_input_widget.py` is near the cap — do not add to it. `_schema_discovery_wiring.py` and `schema_builder_dialog.py` must be checked against the cap after edits; extract helpers if needed.
- GUI/Qt tests require the PySide6 offscreen environment (QT_QPA_PLATFORM=offscreen and the Ubuntu system libs in CI per the pyside6-ci-system-libs memory). Presenter/wiring logic must stay testable without a live QApplication where possible (the reader/header path is Qt-free).
- No new dependency. No suppressions without authorization.

## Severity

- Defect 2 (no source pool on edit) — **Blocking**: the primary reported bug is not fixed.
- AC-7 (scroll) and AC-8 (window controls) — required feature additions requested by the user, delivered in this same cycle/PR (same dialog files; splitting would churn the same files).
