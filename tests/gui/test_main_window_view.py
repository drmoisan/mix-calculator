"""Offscreen tests for the WS4 modal-plus-status error surface (issue #48).

Verifies that :class:`~src.gui._main_window_view.MainWindowPipelineView` drives
BOTH a ``QMessageBox.critical`` modal (carrying the full diagnostic) AND a
concise status-bar summary when an error is surfaced (AC-7). ``QMessageBox`` is
patched at its import location in ``_main_window_view`` so no real dialog opens.
Runs headless under ``QT_QPA_PLATFORM=offscreen`` from :mod:`tests.gui.conftest`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui._main_window_view import MainWindowPipelineView
from src.gui.main_window import MainWindow

if TYPE_CHECKING:
    import pytest
    from pytestqt.qtbot import QtBot


class _CriticalRecorder:
    """Recording stand-in for ``QMessageBox.critical``.

    Purpose:
        Capture the modal invocations without opening a real dialog so the test
        can assert the full diagnostic was routed to the modal surface.

    Attributes:
        calls: Each call recorded as ``(title, message)`` in call order.
    """

    def __init__(self) -> None:
        """Initialize with no recorded calls."""
        self.calls: list[tuple[str, str]] = []

    def __call__(self, _parent: object, title: str, message: str) -> None:
        """Record a critical-modal invocation (title, message)."""
        self.calls.append((title, message))


def test_show_error_drives_modal_and_status_summary(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """show_error shows a modal with the full text and a status-bar summary."""
    # Arrange: patch QMessageBox.critical at its import location in the view.
    recorder = _CriticalRecorder()
    monkeypatch.setattr(
        "src.gui._main_window_view.QMessageBox.critical", recorder, raising=True
    )
    window = MainWindow()
    qtbot.addWidget(window)
    view = MainWindowPipelineView(window)

    # Act
    view.show_error("AOP validation failed: YTD != sum(months).")

    # Assert: the modal received the full diagnostic, and the status bar shows a
    # concise summary prefixed with "Error:".
    assert recorder.calls == [("Error", "AOP validation failed: YTD != sum(months).")]
    assert window.statusBar().currentMessage().startswith("Error:")
    assert "YTD != sum(months)" in window.statusBar().currentMessage()


def test_show_dialog_error_shows_modal_with_title_and_message(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """show_dialog_error routes the title and full message to the modal."""
    # Arrange
    recorder = _CriticalRecorder()
    monkeypatch.setattr(
        "src.gui._main_window_view.QMessageBox.critical", recorder, raising=True
    )
    window = MainWindow()
    qtbot.addWidget(window)
    view = MainWindowPipelineView(window)

    # Act
    view.show_dialog_error("Import failed", "Full diagnostic detail line.")

    # Assert: the modal carries the supplied title and full message.
    assert recorder.calls == [("Import failed", "Full diagnostic detail line.")]


def test_show_error_status_summary_truncates_multiline(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The status summary collapses a multi-line diagnostic to its first line."""
    # Arrange
    recorder = _CriticalRecorder()
    monkeypatch.setattr(
        "src.gui._main_window_view.QMessageBox.critical", recorder, raising=True
    )
    window = MainWindow()
    qtbot.addWidget(window)
    view = MainWindowPipelineView(window)

    # Act: a multi-line message; the modal gets it all, the status bar gets line 1.
    view.show_error("First line summary.\nSecond line detail.\nThird line.")

    # Assert: the status bar shows only the first line; the modal has the full text.
    status = window.statusBar().currentMessage()
    assert "Second line detail" not in status
    assert "First line summary" in status
    assert recorder.calls[0][1].count("\n") == 2


def test_show_error_status_summary_truncates_long_first_line(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A very long first line is truncated with an ellipsis in the status bar."""
    # Arrange
    recorder = _CriticalRecorder()
    monkeypatch.setattr(
        "src.gui._main_window_view.QMessageBox.critical", recorder, raising=True
    )
    window = MainWindow()
    qtbot.addWidget(window)
    view = MainWindowPipelineView(window)

    # Act: a single line longer than the 120-char status summary bound.
    long_message = "x" * 200
    view.show_error(long_message)

    # Assert: the status summary is truncated with an ellipsis; the modal is full.
    status = window.statusBar().currentMessage()
    assert status.endswith("…")
    assert len(status) < len("Error: ") + 200
    assert recorder.calls[0][1] == long_message
