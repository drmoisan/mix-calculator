# GUI Suite Regression Run (P11-T3)

Timestamp: 2026-06-05T13-05
Command: QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui -q
EXIT_CODE: 0
Output Summary: 415 passed. The full GUI test directory runs green headless under
QT_QPA_PLATFORM=offscreen, covering the schema-builder presenter/dialog, the
columns/key drag widgets and presenters, dedup defaults, import gating, schema
discovery + activation wiring, and the behavioral schema-import integration paths.
