---
name: pyside6-ci-system-libs
description: PySide6 / pytest-qt suites need libEGL/libGL/libxkbcommon/libdbus/libfontconfig installed on Ubuntu CI runners before pytest can collect.
metadata:
  type: project
---

PySide6 wheels link dynamically against `libEGL.so.1`, `libGL.so.1`, `libxkbcommon.so.0`, `libdbus-1.so.3`, and `libfontconfig.so.1`. The Ubuntu GitHub Actions runner image does not include these. pytest-qt imports `PySide6.QtGui` at `pytest_configure` time, so a missing `libEGL.so.1` aborts collection with `ImportError: libEGL.so.1: cannot open shared object file` before any test runs.

**Why:** Discovered in PR #24 (issue #19, mix-pipeline-gui). Local Pytest passed because the workstation has Qt platform libs; CI failed deterministically on both py3.12 and py3.13 because the Ubuntu runner is bare.

**How to apply:** For any branch that adds or changes PySide6 / pytest-qt tests in this repo, ensure `.github/workflows/_python-quality.yml` installs the five packages via apt-get before the pytest step, and that the pytest step sets `QT_QPA_PLATFORM=offscreen` at the workflow level (not just in conftest.py — workflow-level is the load-bearing line). The fix landed in commit 553547d. The five packages are sufficient for `offscreen`; XCB is not required.

Related: see `tests/gui/conftest.py` for the session-scoped offscreen harness; `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/baseline/qt-runtime.2026-05-27T20-59.md` for the local verification baseline; `.claude/rules/ci-workflows.md` for the broader CI workflow policy this fix conforms to.
