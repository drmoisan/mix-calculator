"""Widget tests for :class:`src.gui.main_window.MainWindow` public attributes.

Verifies the eight control buttons promoted in v2 are addressable as public
attributes on a constructed ``MainWindow`` instance (per spec section 2). The
public attribute surface is the seam the v2 ``MainWindowPipelineView`` adapter
uses to push enable/disable state in response to presenter pushes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.main_window import MainWindow

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_main_window_exposes_import_le_btn_publicly(qtbot: QtBot) -> None:
    """The LE import button is a public, initially-enabled attribute."""
    # Arrange
    window = MainWindow()
    qtbot.addWidget(window)

    # Act + Assert
    assert hasattr(window, "import_le_btn")
    assert window.import_le_btn.isEnabled() is True


def test_main_window_exposes_import_aop_btn_publicly(qtbot: QtBot) -> None:
    """The AOP import button is a public, initially-enabled attribute."""
    window = MainWindow()
    qtbot.addWidget(window)

    assert hasattr(window, "import_aop_btn")
    assert window.import_aop_btn.isEnabled() is True


def test_main_window_exposes_import_skulu_btn_publicly(qtbot: QtBot) -> None:
    """The SKU_LU import button is a public, initially-enabled attribute."""
    window = MainWindow()
    qtbot.addWidget(window)

    assert hasattr(window, "import_skulu_btn")
    assert window.import_skulu_btn.isEnabled() is True


def test_main_window_exposes_import_all_btn_publicly(qtbot: QtBot) -> None:
    """The Import-All button is a public, initially-enabled attribute."""
    window = MainWindow()
    qtbot.addWidget(window)

    assert hasattr(window, "import_all_btn")
    assert window.import_all_btn.isEnabled() is True


def test_main_window_exposes_run_btn_publicly(qtbot: QtBot) -> None:
    """The Run button is a public, initially-enabled attribute."""
    window = MainWindow()
    qtbot.addWidget(window)

    assert hasattr(window, "run_btn")
    assert window.run_btn.isEnabled() is True


def test_main_window_exposes_save_btn_publicly(qtbot: QtBot) -> None:
    """The Save button is a public, initially-enabled attribute."""
    window = MainWindow()
    qtbot.addWidget(window)

    assert hasattr(window, "save_btn")
    assert window.save_btn.isEnabled() is True


def test_main_window_exposes_open_btn_publicly(qtbot: QtBot) -> None:
    """The Open button is a public, initially-enabled attribute."""
    window = MainWindow()
    qtbot.addWidget(window)

    assert hasattr(window, "open_btn")
    assert window.open_btn.isEnabled() is True


def test_main_window_exposes_export_btn_publicly(qtbot: QtBot) -> None:
    """The Export button is a public, initially-enabled attribute."""
    window = MainWindow()
    qtbot.addWidget(window)

    assert hasattr(window, "export_btn")
    assert window.export_btn.isEnabled() is True


def test_per_input_import_buttons_live_in_source_widgets_not_control_row(
    qtbot: QtBot,
) -> None:
    """AC12/AC13: per-input Import buttons are children of their source widgets.

    The three per-input Import buttons must be owned by their source widgets
    (so they render beside each input) rather than the global control row, while
    Import All remains a direct child of the main window's central area.
    """
    # Arrange
    from PySide6.QtWidgets import QPushButton

    window = MainWindow()
    qtbot.addWidget(window)

    # Assert: each per-input button is a descendant of its own source widget.
    assert window.import_le_btn in window.le_widget.findChildren(QPushButton)
    assert window.import_aop_btn in window.aop_widget.findChildren(QPushButton)
    assert window.import_skulu_btn in window.skulu_widget.findChildren(QPushButton)

    # Assert: the per-input buttons are NOT owned by any other source widget,
    # confirming they were removed from the shared control row.
    assert window.import_le_btn not in window.aop_widget.findChildren(QPushButton)
    assert window.import_aop_btn not in window.skulu_widget.findChildren(QPushButton)

    # Assert: Import All is not inside any source widget (it stays in the row).
    for widget in (window.le_widget, window.aop_widget, window.skulu_widget):
        assert window.import_all_btn not in widget.findChildren(QPushButton)
