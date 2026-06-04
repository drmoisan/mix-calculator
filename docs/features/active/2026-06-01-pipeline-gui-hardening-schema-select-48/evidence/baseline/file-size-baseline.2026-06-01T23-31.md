# Baseline — File Sizes (500-line cap watch)

Timestamp: 2026-06-01T23-31

| File | Line count |
|---|---|
| src/gui/app.py | 494 |
| src/schema_registry.py | 303 |
| src/gui/services/schema_service.py | 245 |
| src/gui/presenters/source_selection_presenter.py | 266 |

Note: src/gui/app.py headroom is 6 lines. Dropdown population wiring is placed in a
new module src/gui/_schema_list_wiring.py; only an import + single call site are added
to app.py per the plan.
