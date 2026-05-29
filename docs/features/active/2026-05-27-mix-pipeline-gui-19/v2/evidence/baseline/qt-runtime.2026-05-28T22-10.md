# Baseline — Qt Runtime Preconditions

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run python -c "import PySide6; print(PySide6.__version__)"` and `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run python -c "from PySide6.QtWidgets import QApplication; import sys; app = QApplication(sys.argv); print('offscreen-ok')"`
EXIT_CODE: 0
Output Summary: PySide6 6.11.1 installed. QApplication constructed successfully under `QT_QPA_PLATFORM=offscreen` (printed "offscreen-ok"). Qt offscreen plugin is available.
