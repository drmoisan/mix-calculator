# Baseline — Qt Runtime Preconditions

Timestamp: 2026-05-27T20-59

Command: poetry run python -c "import PySide6; from PySide6 import QtWidgets; print(PySide6.__version__)"
EXIT_CODE: 0
Output: 6.11.1

Command: QT_QPA_PLATFORM=offscreen poetry run python -c "from PySide6.QtWidgets import QApplication; import sys; app = QApplication(sys.argv); print('offscreen-ok')"
EXIT_CODE: 0
Output: offscreen-ok

Output Summary:
- PySide6 version: 6.11.1 (matches spec constraint `^6.11.1`).
- The `offscreen` Qt platform plugin loads: a `QApplication` was constructed successfully
  under `QT_QPA_PLATFORM=offscreen` and printed `offscreen-ok` with exit code 0.
- Spec risk "offscreen platform plugin (unverified)" is RESOLVED: the plugin is present and
  functional. Phase outcome is PASS (not remediation-required).
