"""Qt drag-and-drop widgets for the Columns tab (Decision 4, research G).

This module holds the passive Qt widgets for the Columns tab: a pool of draggable
source-column tokens and a set of required/optional canonical rows that accept a
drop. The widgets are deliberately thin: a drop translates into a single
``assign_column(source, target)`` call on an injected callback, so the
:class:`~src.gui.presenters._columns_tab_presenter.ColumnsTabPresenter` (and its
tests) never simulate Qt drag events. The drag payload is the source column name
carried as MIME text.

Responsibilities:
    - ``SourceColumnToken``: a draggable button labeled with a source column name.
    - ``ColumnDropRow``: a canonical row that accepts a dropped token and reports
      the assignment plus its dtype-check indicator.
    - ``ColumnsTabWidget``: composes the token pool and the rows, implementing the
      pool/row/assignment/dtype setters and routing drops to the seam callback.

Scope boundaries:
    - View only: no matching, no dtype logic. The presenter owns all decisions;
      the widget reports the drop gesture and renders pushed state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.gui.widgets._dtype_check_widget import DtypeCheckWidget

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent

__all__ = [
    "CANONICAL_ORIGIN_MIME",
    "ColumnDropRow",
    "ColumnsTabWidget",
    "SourceColumnToken",
]

# MIME type carrying the dragged source column name as plain text.
_SOURCE_MIME = "text/plain"

# Secondary MIME key identifying the canonical row a drag originated from.
# Present only on drags that start from an assigned ColumnDropRow; absent on
# plain pool-token drags so ColumnsTabWidget.dragEnterEvent can distinguish
# the two drag sources.
CANONICAL_ORIGIN_MIME = "application/x-canonical-origin"


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


class ColumnDropRow(QWidget):
    """A canonical row that accepts dropped source tokens and can initiate drags.

    Purpose:
        Display one canonical column and accept dropped :class:`SourceColumnToken`
        instances. When a source column is assigned, also acts as a drag source so
        the user can drag it back to the pool or onto another canonical row.

    Responsibilities:
        Accept drops and call ``on_drop(source, canonical)``; render the assigned
        source and the dtype indicator; initiate a drag carrying the source name
        and origin canonical when an assigned row is dragged. No matching or dtype
        logic.

    Attributes:
        canonical: The canonical column name this row targets.
        _current_source: The currently assigned source column name, or ``None``
            when unassigned. Updated by :meth:`set_assignment`.
    """

    def __init__(
        self,
        canonical: str,
        description: str,
        expected_dtype: str | None,
        on_drop: Callable[[str, str], None],
        parent: QWidget | None = None,
    ) -> None:
        """Build the row controls and accept drops.

        Args:
            canonical: The canonical column name this row targets.
            description: The column description text (may be empty).
            expected_dtype: The expected dtype label, or ``None``.
            on_drop: Callback invoked with ``(source_name, canonical)`` on a drop.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.canonical = canonical
        self._on_drop = on_drop
        # None when unassigned; set by set_assignment so mouseMoveEvent can carry it.
        self._current_source: str | None = None
        self.setAcceptDrops(True)
        self._label = QLabel(self._row_text(canonical, description, expected_dtype))
        self._assignment = QLabel("(unassigned)")
        self._indicator = DtypeCheckWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        layout.addWidget(self._assignment)
        layout.addWidget(self._indicator)

    @staticmethod
    def _row_text(canonical: str, description: str, expected_dtype: str | None) -> str:
        """Compose the row's display text from its parts.

        Args:
            canonical: The canonical column name.
            description: The description (may be empty).
            expected_dtype: The expected dtype label, or ``None``.

        Returns:
            A single display string combining the parts.
        """
        dtype_text = expected_dtype if expected_dtype is not None else "any"
        # Include the description only when present so empty descriptions do not
        # leave a dangling separator.
        if description:
            return f"{canonical} — {description} [{dtype_text}]"
        return f"{canonical} [{dtype_text}]"

    def label_text(self) -> str:
        """Return this row's display label text (public test seam).

        Returns:
            The row label text (name, description, expected dtype).
        """
        return self._label.text()

    def assignment_text(self) -> str:
        """Return the assignment label text (public test seam).

        Returns:
            The assigned source-column name, or ``"(unassigned)"`` when unbound.
        """
        return self._assignment.text()

    def set_assignment(self, source_column: str | None) -> None:
        """Update ``_current_source`` and the assignment label.

        Args:
            source_column: The assigned source name, or ``None`` when cleared.
        """
        self._current_source = source_column
        self._assignment.setText(
            source_column if source_column is not None else "(unassigned)"
        )

    def set_indicator(self, coercible: bool, failing_example: str | None) -> None:
        """Render the dtype-check result on this row's indicator.

        Args:
            coercible: Whether the matched values coerce to the expected dtype.
            failing_example: A masked failing example when not coercible.

        Returns:
            ``None``.

        Side effects:
            Updates the embedded dtype indicator widget.
        """
        self._indicator.set_state(coercible, failing_example)

    def dragEnterEvent(self, e: QDropEvent) -> None:
        """Accept a drag carrying source text so a drop can land.

        Args:
            e: The Qt drag-enter event.

        Returns:
            ``None``.

        Side effects:
            Accepts the proposed action when the payload carries text.
        """
        if e.mimeData().hasText():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent) -> None:
        """Report the dropped source column to the assignment callback.

        Args:
            e: The Qt drop event whose MIME text is the source column name.

        Returns:
            ``None``.

        Side effects:
            Calls ``on_drop(source_name, canonical)`` exactly once and accepts the
            action.
        """
        source = e.mimeData().text()
        # The single assignment seam: translate the drop gesture into one callback
        # call so the presenter (and its tests) never simulate drag events.
        self._on_drop(source, self.canonical)
        e.acceptProposedAction()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        """Start a drag carrying the assigned source and this row's canonical name.

        No-ops when ``_current_source`` is ``None`` or the left button is not held.
        Sets ``text/plain`` (source name) and ``CANONICAL_ORIGIN_MIME`` (this
        canonical) so both the re-assign and the unassign paths can read them.

        Args:
            e: The Qt mouse-move event.
        """
        # Only initiate a drag when a source is assigned and the left button is held.
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


class ColumnsTabWidget(QWidget):
    """Composes the source-token pool and the canonical drop rows.

    Purpose:
        Provide the Columns-tab view: a pool of draggable source tokens above the
        required/optional canonical rows, implementing the
        :class:`~src.gui._columns_tab_protocol.ColumnsTabViewProtocol` setters and
        routing each row's drop to the injected assignment seam.

    Responsibilities:
        Build and rebuild the token pool and rows from pushed state; forward each
        drop to ``assign_column``; reflect assignments and dtype indicators; accept
        pool-area drops (outside any :class:`ColumnDropRow`) and route them to
        ``clear_row`` to unassign the dragged row. It holds no matching or dtype
        logic. Qt delivers drops to the deepest accepting widget, so
        :class:`ColumnDropRow` captures row-targeted drops; this widget captures
        the remainder (pool area).

    Attributes:
        assign_column: The seam callback drops are routed to; set by the composition
            root to the presenter's ``assign_column``.
        _on_release: The seam callback invoked with the canonical name when a drag
            from an assigned row is dropped on the pool area; set by the composition
            root via :meth:`clear_row` monkey-patch to the presenter's
            ``clear_row``.
    """

    def __init__(
        self,
        on_assign: Callable[[str, str], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Build the empty pool and rows containers.

        Args:
            on_assign: Optional assignment seam callback invoked with
                ``(source, canonical)`` on a drop; defaults to a no-op until the
                composition root wires the presenter.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self._on_assign: Callable[[str, str], None] = on_assign or (lambda _s, _c: None)
        # Pool-area drops reach this widget; row-targeted drops reach ColumnDropRow.
        self.setAcceptDrops(True)
        # Monkey-patched by DragTabBinder to the presenter's clear_row.
        self._on_release: Callable[[str], None] = lambda _c: None
        self._pool_box = QVBoxLayout()
        self._rows_box = QVBoxLayout()
        self._rows: dict[str, ColumnDropRow] = {}
        self._tokens: list[SourceColumnToken] = []
        outer = QVBoxLayout(self)
        outer.addWidget(QLabel("Source columns"))
        outer.addLayout(self._pool_box)
        outer.addWidget(QLabel("Canonical columns"))
        outer.addLayout(self._rows_box)

    def assign_column(self, source_column: str, target_canonical: str) -> None:
        """Route an assignment to the injected seam callback.

        Args:
            source_column: The dropped source column name.
            target_canonical: The canonical row dropped onto.
        """
        self._on_assign(source_column, target_canonical)

    def clear_row(self, target_canonical: str) -> None:
        """Invoke ``_on_release(target_canonical)`` to unassign the given row.

        Monkey-patched by :class:`DragTabBinder` to the presenter's ``clear_row``.

        Args:
            target_canonical: The canonical row name to unassign.
        """
        self._on_release(target_canonical)

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        """Accept only when both ``text/plain`` and ``CANONICAL_ORIGIN_MIME`` present.

        Plain pool-token drags (no canonical-origin key) are not accepted here.

        Args:
            e: The Qt drag-enter event.
        """
        if e.mimeData().hasText() and e.mimeData().hasFormat(CANONICAL_ORIGIN_MIME):
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent) -> None:
        """Unassign the row identified by ``CANONICAL_ORIGIN_MIME``.

        Reads the canonical name from the secondary MIME key and calls
        :meth:`clear_row` to route the unassign gesture to the presenter.

        Args:
            e: The Qt drop event carrying both MIME keys.
        """
        canonical_origin = e.mimeData().data(CANONICAL_ORIGIN_MIME).toStdString()
        self.clear_row(canonical_origin)
        e.acceptProposedAction()

    def set_source_pool(self, columns: list[str]) -> None:
        """Rebuild the draggable token pool from ``columns``.

        Args:
            columns: The unconsumed source column names, in source order.

        Returns:
            ``None``.

        Side effects:
            Clears and recreates the pool tokens.
        """
        # Clear existing tokens before rebuilding so a re-render reflects the
        # current pool exactly (consumed tokens disappear).
        for token in self._tokens:
            token.setParent(None)
        self._tokens = []
        # Create one draggable token per remaining source column, in order.
        for name in columns:
            token = SourceColumnToken(name)
            self._tokens.append(token)
            self._pool_box.addWidget(token)

    def set_rows(self, rows: list[tuple[str, str, str | None]]) -> None:
        """Rebuild the canonical drop rows from ``rows``.

        Args:
            rows: One ``(canonical_name, description, expected_dtype)`` tuple per
                row, in display order.

        Returns:
            ``None``.

        Side effects:
            Clears and recreates the drop rows, each wired to ``assign_column``.
        """
        # Clear existing rows before rebuilding so the row set matches the state.
        for row in self._rows.values():
            row.setParent(None)
        self._rows = {}
        # Create one drop row per canonical column; each routes its drop to the
        # widget's assign_column seam.
        for canonical, description, expected in rows:
            row = ColumnDropRow(canonical, description, expected, self.assign_column)
            self._rows[canonical] = row
            self._rows_box.addWidget(row)

    def set_assignment(self, target_canonical: str, source_column: str | None) -> None:
        """Reflect the source assigned to one row.

        Args:
            target_canonical: The canonical row whose assignment changed.
            source_column: The assigned source, or ``None`` when cleared.

        Returns:
            ``None``.

        Side effects:
            Updates the matching row's assignment label when the row exists.
        """
        row = self._rows.get(target_canonical)
        if row is not None:
            row.set_assignment(source_column)

    def set_dtype_indicator(
        self, target_canonical: str, coercible: bool, failing_example: str | None
    ) -> None:
        """Reflect the dtype-check result for one row.

        Args:
            target_canonical: The canonical row whose dtype state changed.
            coercible: Whether the matched values coerce to the expected dtype.
            failing_example: A masked failing example when not coercible.

        Returns:
            ``None``.

        Side effects:
            Updates the matching row's indicator when the row exists.
        """
        row = self._rows.get(target_canonical)
        if row is not None:
            row.set_indicator(coercible, failing_example)

    def token_names(self) -> list[str]:
        """Return the current pool token column names (public test seam).

        Returns:
            The source column names of the draggable tokens, in order.
        """
        return [token.column_name for token in self._tokens]

    def row_canonicals(self) -> list[str]:
        """Return the canonical names of the current drop rows (public test seam).

        Returns:
            The canonical names of the rendered rows, in display order.
        """
        return list(self._rows)

    def row_label_text(self, canonical: str) -> str:
        """Return one row's display text (public test seam).

        Args:
            canonical: The canonical row to read.

        Returns:
            The row's label text, or an empty string when the row is absent.
        """
        row = self._rows.get(canonical)
        return row.label_text() if row is not None else ""

    def row_assignment_text(self, canonical: str) -> str:
        """Return one row's rendered source assignment (public test seam).

        Args:
            canonical: The canonical row to read.

        Returns:
            The assigned source-column name, ``"(unassigned)"`` when unbound, or
            ``""`` when the row is absent.
        """
        row = self._rows.get(canonical)
        return row.assignment_text() if row is not None else ""
