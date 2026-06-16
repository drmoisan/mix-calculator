"""Qt offscreen tests for the ColumnsTabWidget responsive layout and scroll area.

These tests verify that the QSplitter / QScrollArea layout introduced in issue #68
functions correctly: canonical rows are wrapped in a scrollable area, derived rows
appear after regular rows, the splitter switches between wide and narrow orientations
at the configured threshold, and drag-and-drop data-access seams survive orientation
changes.

Tests run headless under ``QT_QPA_PLATFORM=offscreen``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QScrollArea

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_columns_tab_scroll_area_wraps_rows_panel(qtbot: QtBot) -> None:
    """AC-1: canonical rows are wrapped in a resizable QScrollArea.

    A QScrollArea with widgetResizable=True must be present inside the widget
    and all ColumnDropRows added via set_rows must be descendants of its inner
    widget, ensuring rows beyond the visible height are reachable by scrolling.
    """
    # Arrange
    from src.gui.widgets._columns_tab_drag import ColumnDropRow, ColumnsTabWidget

    widget = ColumnsTabWidget()
    qtbot.addWidget(widget)

    # Act
    widget.set_rows([("Col1", "", None), ("Col2", "", None), ("Col3", "", None)])

    # Assert: a resizable QScrollArea is present inside the widget.
    scroll_areas = widget.findChildren(QScrollArea)
    assert len(scroll_areas) >= 1
    scroll = scroll_areas[0]
    assert scroll.widgetResizable() is True

    # Assert: all ColumnDropRows are descendants of the scroll area's inner widget.
    inner = scroll.widget()
    assert inner is not None
    drop_rows = inner.findChildren(ColumnDropRow)
    canonical_names = {r.canonical for r in drop_rows}
    assert canonical_names == {"Col1", "Col2", "Col3"}


def test_derived_row_appears_in_row_canonicals(qtbot: QtBot) -> None:
    """AC-2: derived column rows appear after regular rows in row_canonicals().

    Derived rows (tuples with description "derived") must appear at the end of
    the canonical rows list in the order they were added.
    """
    # Arrange
    from src.gui.widgets._columns_tab_drag import ColumnsTabWidget

    widget = ColumnsTabWidget()
    qtbot.addWidget(widget)

    # Act: three regular rows followed by two derived rows.
    rows: list[tuple[str, str, str | None]] = [
        ("RegA", "", None),
        ("RegB", "", None),
        ("RegC", "", None),
        ("DerX", "derived", None),
        ("DerY", "derived", None),
    ]
    widget.set_rows(rows)

    # Assert: all five appear in insertion order; derived rows are last.
    assert widget.row_canonicals() == ["RegA", "RegB", "RegC", "DerX", "DerY"]


def test_wide_layout_rows_left_pool_right(qtbot: QtBot) -> None:
    """AC-3: wide layout places rows scroll at splitter index 0, pool at index 1."""
    # Arrange
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QResizeEvent

    from src.gui.widgets._columns_tab_drag import ColumnsTabWidget

    widget = ColumnsTabWidget(width_threshold=400)
    qtbot.addWidget(widget)
    widget.set_source_pool(["a"])
    widget.set_rows([("X", "", None)])

    # Act: simulate a wide resize event (width > threshold).
    e = QResizeEvent(QSize(500, 300), QSize(300, 300))
    widget.resizeEvent(e)

    # Assert: rows scroll (index 0 = left) and pool panel (index 1 = right).
    assert widget.splitter.widget(0) is widget.rows_scroll
    assert widget.splitter.widget(1) is widget.pool_panel


def test_narrow_layout_pool_top_rows_bottom(qtbot: QtBot) -> None:
    """AC-4: narrow layout places pool panel at index 0, rows scroll at index 1."""
    # Arrange
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QResizeEvent

    from src.gui.widgets._columns_tab_drag import ColumnsTabWidget

    widget = ColumnsTabWidget(width_threshold=400)
    qtbot.addWidget(widget)
    widget.set_source_pool(["b"])
    widget.set_rows([("Y", "", None)])

    # Act: simulate a narrow resize event (width < threshold).
    e = QResizeEvent(QSize(300, 600), QSize(500, 600))
    widget.resizeEvent(e)

    # Assert: pool panel (index 0 = top) and rows scroll (index 1 = bottom).
    assert widget.splitter.widget(0) is widget.pool_panel
    assert widget.splitter.widget(1) is widget.rows_scroll


def test_layout_switch_preserves_drag_functionality(qtbot: QtBot) -> None:
    """AC-5: set_rows and set_source_pool work correctly after orientation switches.

    Simulate wide → narrow → wide transitions and verify that token_names() and
    row_canonicals() still return the correct values after each switch, confirming
    that _rows and _tokens collections are unaffected by the layout refactor.
    """
    # Arrange
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QResizeEvent

    from src.gui.widgets._columns_tab_drag import ColumnsTabWidget

    widget = ColumnsTabWidget(width_threshold=400)
    qtbot.addWidget(widget)
    widget.set_source_pool(["c", "d"])
    widget.set_rows([("D", "", None), ("E", "", None)])

    # Act: wide → narrow → wide.
    widget.resizeEvent(QResizeEvent(QSize(500, 300), QSize(300, 300)))
    widget.resizeEvent(QResizeEvent(QSize(300, 600), QSize(500, 600)))
    widget.resizeEvent(QResizeEvent(QSize(600, 300), QSize(300, 300)))

    # Assert: data-access seams are unaffected by orientation changes.
    assert widget.token_names() == ["c", "d"]
    assert widget.row_canonicals() == ["D", "E"]
