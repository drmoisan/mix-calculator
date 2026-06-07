# Baseline — Cap-Sensitive File Sizes

Timestamp: 2026-06-05T11-08
Command: wc -l src/schema_model.py src/gui/app.py src/gui/widgets/source_input_widget.py
EXIT_CODE: 0

500-line cap applies to all production, test, and reusable script files.

| File | Lines | Cap | Headroom |
|---|---|---|---|
| src/schema_model.py | 487 | 500 | 13 |
| src/gui/app.py | 500 | 500 | 0 (at limit) |
| src/gui/widgets/source_input_widget.py | 472 | 500 | 28 |

Output Summary: schema_model.py and app.py must be decomposed before additions per plan
Phase 1 (model split) and Phase 6 (app split). source_input_widget.py decomposed in Phase 6.
