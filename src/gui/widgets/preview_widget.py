"""Tab-preview widget backed by a QTableView and QStandardItemModel.

This passive Qt widget renders a ``list[list[str]]`` preview of a worksheet tab
into a ``QTableView``. It holds no logic beyond model population and exposes a
``grab()``-based ``QPixmap`` accessor for an image-style preview.

Responsibilities:
    - ``show_preview`` populates the table model from the preview rows.
    - ``preview_pixmap`` returns a rendered image of the current preview.
"""

from __future__ import annotations

from PySide6.QtGui import QPixmap, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QTableView, QVBoxLayout, QWidget

__all__ = ["PreviewWidget"]


class PreviewWidget(QWidget):
    """Passive view rendering a string-grid preview of a worksheet tab.

    Purpose:
        Display a bounded ``list[list[str]]`` preview in a ``QTableView``.

    Responsibilities:
        Populate the backing ``QStandardItemModel`` from preview rows and provide
        a ``QPixmap`` rendering. It holds no service or transform logic.

    Usage:
        Constructed by the composition root; ``show_preview`` is called with the
        reader's preview rows (typically via the source-selection presenter).

    Key invariants:
        The model's row/column counts match the supplied preview; an empty rows
        list yields an empty model.

    Attributes:
        _model: The backing item model populated by ``show_preview``.
        _table: The table view rendering the model.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the table view and its backing model.

        Args:
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self._model = QStandardItemModel()
        self._table = QTableView()
        self._table.setModel(self._model)

        layout = QVBoxLayout(self)
        layout.addWidget(self._table)

    @property
    def model(self) -> QStandardItemModel:
        """Return the backing item model (for inspection/tests)."""
        return self._model

    def show_preview(self, rows: list[list[str]]) -> None:
        """Populate the table model from the preview rows.

        Args:
            rows: The preview rows, each a list of string cell values. An empty
                list clears the model.

        Returns:
            ``None``.

        Side effects:
            Replaces the model contents with ``rows``.
        """
        self._model.clear()
        if not rows:
            return
        # Set the grid dimensions from the widest row, then fill each cell with a
        # QStandardItem so the table view renders the full preview.
        column_count = max(len(row) for row in rows)
        self._model.setRowCount(len(rows))
        self._model.setColumnCount(column_count)
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self._model.setItem(row_index, column_index, QStandardItem(value))

    def preview_pixmap(self) -> QPixmap:
        """Return a ``QPixmap`` rendering of the current preview table.

        Returns:
            A ``QPixmap`` grabbed from the table view (non-null once the widget
            has a size).

        Side effects:
            Renders the table view into an off-screen pixmap.
        """
        return self._table.grab()
