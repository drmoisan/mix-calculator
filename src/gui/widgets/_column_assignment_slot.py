"""Qt widget providing a styled drop-zone slot for one canonical column assignment.

This module defines :class:`ColumnAssignmentSlot`, a :class:`QFrame` subclass that
serves as both the visual drop zone and drag source for a single canonical-column row
in the Columns tab.  It encapsulates all drag-and-drop event handling that was
previously spread across ``ColumnDropRow``, keeping ``_columns_tab_drag.py`` within
the 500-line file-size limit while giving the slot its own testable surface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent

__all__ = ["CANONICAL_ORIGIN_MIME", "ColumnAssignmentSlot"]

# Secondary MIME key identifying the canonical row a drag originated from.
# Present only on drags that start from an assigned ColumnAssignmentSlot; absent on
# plain pool-token drags so ColumnsTabWidget.dragEnterEvent can distinguish the two
# drag sources.
CANONICAL_ORIGIN_MIME = "application/x-canonical-origin"

# Stylesheet applied to the slot when no source column is assigned.
_UNASSIGNED_STYLE = (
    "ColumnAssignmentSlot { border: 2px dashed #aaa;"
    " border-radius: 4px; min-height: 26px; }"
)

# Stylesheet applied to the slot when a source column is assigned.
_ASSIGNED_STYLE = (
    "ColumnAssignmentSlot { border: 2px solid #4a75c0; border-radius: 4px;"
    " min-height: 26px; background: #e8f0fd; }"
)

# Stylesheet for the source-name button inside an assigned slot.
_BUTTON_STYLE = (
    "background: #5c88d4; color: white; border-radius: 3px; padding: 2px 6px;"
)


class ColumnAssignmentSlot(QFrame):
    """A styled drop-zone for one canonical column assignment.

    Purpose:
        Render the right-hand side of a canonical drop row as either a dashed
        placeholder (when unassigned) or a solid-bordered panel containing a
        draggable source-name button (when assigned).

    Responsibilities:
        - Accept any ``text/plain`` drag (pool tokens and re-assigns both carry
          plain text) via :meth:`dragEnterEvent`.
        - Deliver drops to the injected ``on_drop`` callback via :meth:`dropEvent`.
        - Initiate a drag carrying both ``text/plain`` (source name) and
          ``CANONICAL_ORIGIN_MIME`` (canonical name) when the slot is assigned and
          the left mouse button is moved (:meth:`mouseMoveEvent`).
        - Toggle visual state between unassigned (dashed border, placeholder label)
          and assigned (solid border, source button) via :meth:`set_assignment`.

    Attributes:
        canonical: The canonical column name this slot belongs to.
        _current_source: The currently assigned source column name, or ``None``
            when unassigned.
        _on_drop: Callback invoked with ``(source_name, canonical)`` on a drop.
        _placeholder: ``QLabel`` showing "(drop here)" when unassigned.
        _button: ``QPushButton`` showing the source name when assigned.

    Lifecycle:
        Construct with the canonical name and drop callback.  The slot starts in
        the unassigned state.  Call :meth:`set_assignment` to toggle state.
    """

    def __init__(
        self,
        canonical: str,
        on_drop: Callable[[str, str], None],
        parent: QWidget | None = None,
    ) -> None:
        """Build the slot controls, configure drop acceptance, and apply initial style.

        Args:
            canonical: The canonical column name this slot represents.
            on_drop: Callback invoked with ``(source_name, canonical)`` when a
                source column is dropped onto this slot.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.canonical = canonical
        self._on_drop = on_drop
        # None when unassigned; updated by set_assignment for drag payload.
        self._current_source: str | None = None
        # Enable this slot as a drop target; pool drops are handled by ColumnsTabWidget.
        self.setAcceptDrops(True)

        # Build a compact horizontal layout to hold the placeholder or button.
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        # Placeholder label shown when no source is assigned.
        self._placeholder = QLabel("(drop here)")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._placeholder)

        # Button shown when a source is assigned; hidden initially.
        self._button = QPushButton("")
        self._button.setStyleSheet(_BUTTON_STYLE)
        self._button.setVisible(False)
        layout.addWidget(self._button)

        # Start in the unassigned visual state.
        self.setStyleSheet(_UNASSIGNED_STYLE)

    def set_assignment(self, source: str | None) -> None:
        """Toggle the slot between unassigned and assigned visual states.

        When assigned: shows the source-name button with solid-border styling.
        When cleared (``source`` is ``None``): shows the placeholder with dashed-border
        styling and clears ``_current_source``.

        Args:
            source: The source column name to assign, or ``None`` to clear the
                current assignment.

        Side effects:
            Updates ``_current_source``, widget visibility, button text, and
            stylesheet.
        """
        if source is not None:
            # Transition to the assigned state: record the source, show the button.
            self._current_source = source
            self._button.setText(source)
            self._button.setVisible(True)
            self._placeholder.setVisible(False)
            self.setStyleSheet(_ASSIGNED_STYLE)
        else:
            # Transition to the unassigned state: clear the source, show placeholder.
            self._current_source = None
            self._button.setVisible(False)
            self._placeholder.setVisible(True)
            self.setStyleSheet(_UNASSIGNED_STYLE)

    def assignment_text(self) -> str:
        """Return the currently displayed assignment text (public test seam).

        Returns:
            The assigned source-column name when assigned, or ``"(drop here)"``
            when unassigned.
        """
        return (
            self._current_source if self._current_source is not None else "(drop here)"
        )

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:  # type: ignore[override]
        """Accept any drag carrying ``text/plain`` so a drop can land here.

        Both pool-token drags (plain text only) and re-assign drags from another
        assigned slot (plain text + ``CANONICAL_ORIGIN_MIME``) carry ``text/plain``,
        so accepting on ``hasText()`` captures both sources.

        Args:
            e: The Qt drag-enter event.

        Side effects:
            Accepts the proposed action when the payload carries text.
        """
        if e.mimeData().hasText():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent) -> None:  # type: ignore[override]
        """Deliver the dropped source column to the assignment callback.

        Delegates the entire assignment decision to ``on_drop``; the slot itself
        holds no matching or dtype logic.

        Args:
            e: The Qt drop event whose ``text/plain`` is the source column name.

        Side effects:
            Calls ``on_drop(source_name, canonical)`` exactly once and accepts the
            proposed action.
        """
        # Single-seam delegation: translate the drop gesture into one callback
        # call so the presenter (and its tests) never simulate drag events.
        self._on_drop(e.mimeData().text(), self.canonical)
        e.acceptProposedAction()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        """Start a drag carrying the assigned source and this slot's canonical name.

        No-ops when ``_current_source`` is ``None`` (nothing to drag) or when the
        left button is not held (accidental moves should not initiate a drag).

        The drag payload carries two MIME keys:
        - ``text/plain``: the source column name, so a drop target can read it.
        - ``CANONICAL_ORIGIN_MIME``: the canonical name encoded as UTF-8 bytes,
          so the pool-area drop handler can identify which row to unassign.

        Args:
            e: The Qt mouse-move event.
        """
        # Guard: only drag when a source is assigned and the left button is held.
        if self._current_source is None or not (
            e.buttons() & Qt.MouseButton.LeftButton
        ):
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self._current_source)
        mime.setData(CANONICAL_ORIGIN_MIME, self.canonical.encode())
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)
