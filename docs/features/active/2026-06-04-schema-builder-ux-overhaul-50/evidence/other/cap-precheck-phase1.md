# Cap Precheck — Phase 1 (Columns/Key/Derived drag wiring)

Timestamp: 2026-06-05T20-28
Cap: 500 lines per file.

Pre-change line counts:
- src/gui/widgets/schema_builder_dialog.py: 452
- src/gui/widgets/_schema_builder_tabs.py: 241

Projected additions across Phases 1-3 wiring:
- schema_builder_dialog.py would gain drag-widget storage, columns/key/derived
  routing, sub-presenter binding, and a Derived-button handler — roughly
  +120-160 lines, projecting to ~570-610 lines (OVER the 500 cap).
- _schema_builder_tabs.py would gain ColumnsTabWidget/KeyTabWidget construction
  and a Derived button — roughly +30-50 lines, projecting to ~270-290 (under cap).

Decision: EXTRACTION REQUIRED for the dialog. The drag-tab binding/routing logic
is extracted into a new helper module `src/gui/widgets/_schema_builder_drag_tabs.py`
(a `DragTabBinder` that owns the ColumnsTabPresenter/KeyTabPresenter binding and
the column/key/dtype routing), imported by `schema_builder_dialog.py`, so both
files stay <= 500 lines. `_schema_builder_tabs.py` stays under the cap without
extraction; its tab builders gain only the widget construction.

Re-verification of final line counts is performed in P7-T8.
