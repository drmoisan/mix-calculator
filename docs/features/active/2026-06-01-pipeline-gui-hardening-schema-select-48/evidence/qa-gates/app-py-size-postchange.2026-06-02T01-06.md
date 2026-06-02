# Post-change Size Check — src/gui/app.py (Cycle 2, Issue #48)

Timestamp: 2026-06-02T01-06

File: src/gui/app.py
Line count: 500
Cap: 500
Result: WITHIN CAP (<= 500).

Notes:
- P2-T2 added exactly one import (`from src.gui._shutdown_wiring import wire_shutdown_cleanup`) and one call site (`wire_shutdown_cleanup(application, runner_resolved)` plus a 2-line intent comment) inside `build_application`.
- The net +line cost of the import and call was offset by tightening three pre-existing multi-line explanatory comments (QApplication resolution, window-icon, Schema Builder) without removing their decision-logic rationale, keeping the file at the 500-line cap per `.claude/rules/general-code-change.md`.
- Verified after `env -u VIRTUAL_ENV poetry run black src/gui/app.py` (file left unchanged).
