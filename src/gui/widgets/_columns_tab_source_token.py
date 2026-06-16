"""Draggable source-column token for the Columns tab (Decision 4, research G).

This module holds :class:`SourceColumnToken`, the draggable button that
represents one source column in the Columns-tab pool. It is extracted from
:mod:`src.gui.widgets._columns_tab_drag` so that module stays under the
repository's 500-line cap while the row-chooser controls are added (AC-6).

Responsibilities:
    - ``SourceColumnToken``: a draggable button labeled with a source column name
      that starts a :class:`QDrag` carrying its name as MIME text.

Scope boundaries:
    - View only: it holds no matching, dtype, or assignment logic; a drop target
      reads the carried name and reports the gesture elsewhere.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QPushButton, QWidget

if TYPE_CHECKING:
    from PySide6.QtGui import QMouseEvent

__all__ = ["SourceColumnToken"]


class SourceColumnToken(QPushButton):
    """A draggable button representing one source column in the pool.

    Purpose:
        Render one source column as a draggable token; starting a drag carries the
        column's name as MIME text so a drop target can read it.

    Responsibilities:
        Initiate a :class:`QDrag` on mouse-move carrying its column name. It holds
        no logic beyond the drag payload.

    Attributes:
        column_name: The source column name this token represents and carries.
    """

    def __init__(self, column_name: str, parent: QWidget | None = None) -> None:
        """Build a token labeled with and carrying ``column_name``.

        Args:
            column_name: The source column name to display and drag.
            parent: Optional Qt parent widget.
        """
        super().__init__(column_name, parent)
        self.column_name = column_name
        self.setStyleSheet(
            "background: #5c88d4; color: white; border-radius: 3px; padding: 4px 8px;"
            " font-weight: bold;"
        )

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        """Start a drag carrying the column name when the mouse moves.

        Args:
            e: The Qt mouse-move event.

        Returns:
            ``None``.

        Side effects:
            Constructs and executes a :class:`QDrag` whose MIME text is the
            token's column name.
        """
        # Only the left button initiates a drag, matching standard drag affordance.
        if not (e.buttons() & Qt.MouseButton.LeftButton):
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.column_name)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)
