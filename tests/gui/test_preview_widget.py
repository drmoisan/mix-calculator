"""Qt tests for :mod:`src.gui.widgets.preview_widget`.

Runs under ``QT_QPA_PLATFORM=offscreen``. Verifies that ``show_preview``
populates the backing ``QStandardItemModel`` with the expected rows/columns, an
empty rows list yields an empty model, and the ``preview_pixmap`` accessor
returns a non-null ``QPixmap``. No banned timing APIs. Fabricated data only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.widgets.preview_widget import PreviewWidget

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_show_preview_populates_model(qtbot: QtBot) -> None:
    """show_preview populates the model with the expected row/column counts."""
    # Arrange
    widget = PreviewWidget()
    qtbot.addWidget(widget)

    # Act
    widget.show_preview([["a", "b", "c"], ["d", "e", "f"]])

    # Assert
    assert widget.model.rowCount() == 2
    assert widget.model.columnCount() == 3
    item = widget.model.item(0, 1)
    assert item is not None
    assert item.text() == "b"


def test_show_preview_empty_rows_clears_model(qtbot: QtBot) -> None:
    """An empty rows list yields an empty model (zero rows and zero columns)."""
    # Arrange: a widget with prior content.
    widget = PreviewWidget()
    qtbot.addWidget(widget)
    widget.show_preview([["x"]])

    # Act
    widget.show_preview([])

    # Assert
    assert widget.model.rowCount() == 0
    assert widget.model.columnCount() == 0


def test_show_preview_handles_ragged_rows(qtbot: QtBot) -> None:
    """Rows of varying widths are accommodated by the widest column count."""
    # Arrange
    widget = PreviewWidget()
    qtbot.addWidget(widget)

    # Act: a 3-wide row followed by a 2-wide row.
    widget.show_preview([["a", "b", "c"], ["d", "e"]])

    # Assert: the model is 3 columns wide; the missing cell is None.
    assert widget.model.columnCount() == 3
    missing = widget.model.item(1, 2)
    assert missing is None


def test_preview_pixmap_returns_non_null_pixmap(qtbot: QtBot) -> None:
    """preview_pixmap returns a non-null QPixmap from the table grab."""
    # Arrange
    widget = PreviewWidget()
    qtbot.addWidget(widget)
    widget.resize(200, 100)
    widget.show_preview([["a", "b"], ["c", "d"]])

    # Act
    pixmap = widget.preview_pixmap()

    # Assert: a QPixmap is returned and is not null.
    assert not pixmap.isNull()
