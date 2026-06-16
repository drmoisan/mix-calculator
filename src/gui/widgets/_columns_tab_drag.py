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
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.gui.widgets._column_assignment_slot import (
    CANONICAL_ORIGIN_MIME,
    ColumnAssignmentSlot,
)
from src.gui.widgets._columns_tab_layout import (
    apply_splitter_orientation,
    build_columns_panels,
)
from src.gui.widgets._dtype_check_widget import DtypeCheckWidget

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent, QResizeEvent

__all__ = [
    "CANONICAL_ORIGIN_MIME",
    "ColumnDropRow",
    "ColumnsTabWidget",
    "SourceColumnToken",
]

# MIME type carrying the dragged source column name as plain text.
_SOURCE_MIME = "text/plain"


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


class ColumnDropRow(QWidget):
    """A canonical row composing a label, an assignment slot, and a dtype indicator.

    Purpose:
        Display one canonical column as a horizontal row: a descriptive label on
        the left, a :class:`ColumnAssignmentSlot` in the middle that owns all
        drag-and-drop event handling, and a dtype indicator on the right.

    Responsibilities:
        Build and lay out child widgets; delegate assignment state and
        assignment-text queries to ``_slot``; forward dtype-check state to
        ``_indicator``. No matching, dtype, or drag/drop logic lives here — all
        drag-and-drop handling has moved to :class:`ColumnAssignmentSlot`.

    Attributes:
        canonical: The canonical column name this row targets.
        _current_source: The currently assigned source column name, or ``None``
            when unassigned. Updated by :meth:`set_assignment`.
        slot: The embedded :class:`ColumnAssignmentSlot` that owns drop acceptance
            and drag initiation for this row (public property, test seam).
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
        # None when unassigned; updated by set_assignment.
        self._current_source: str | None = None
        self._label = QLabel(self._row_text(canonical, description, expected_dtype))
        # The slot owns drop acceptance and drag initiation for this row.
        self._slot = ColumnAssignmentSlot(canonical, on_drop)
        self._indicator = DtypeCheckWidget()
        # Horizontal layout: label (stretches) | slot | indicator (fixed).
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(8)
        row.addWidget(self._label, 2)
        row.addWidget(self._slot, 1)
        row.addWidget(self._indicator, 0)

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

    @property
    def slot(self) -> ColumnAssignmentSlot:
        """Return the embedded assignment slot (public test seam).

        Exposes ``_slot`` under a public name so test code can deliver drag
        events directly to the slot without triggering Pyright
        ``reportPrivateUsage``.

        Returns:
            The :class:`ColumnAssignmentSlot` embedded in this row.
        """
        return self._slot

    def assignment_text(self) -> str:
        """Return the assignment slot's displayed text (public test seam).

        Delegates to :meth:`ColumnAssignmentSlot.assignment_text`.

        Returns:
            The assigned source-column name, or ``"(drop here)"`` when unbound.
        """
        return self._slot.assignment_text()

    def set_assignment(self, source_column: str | None) -> None:
        """Update ``_current_source`` and delegate visual state to the slot.

        Args:
            source_column: The assigned source name, or ``None`` when cleared.
        """
        self._current_source = source_column
        self._slot.set_assignment(source_column)

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
        width_threshold: int = 700,
    ) -> None:
        """Build the empty pool and rows containers.

        Args:
            on_assign: Optional assignment seam callback invoked with
                ``(source, canonical)`` on a drop; defaults to a no-op until the
                composition root wires the presenter.
            parent: Optional Qt parent widget.
            width_threshold: Pixel width at which the layout switches between
                wide (horizontal splitter) and narrow (vertical splitter) modes.
                Defaults to 700.
        """
        super().__init__(parent)
        # Pixel width boundary: >= threshold is wide mode, < threshold is narrow mode.
        self._width_threshold = width_threshold
        self._on_assign: Callable[[str, str], None] = on_assign or (lambda _s, _c: None)
        # Pool-area drops reach this widget; row-targeted drops reach ColumnDropRow.
        self.setAcceptDrops(True)
        # Monkey-patched by DragTabBinder to the presenter's clear_row.
        self._on_release: Callable[[str], None] = lambda _c: None
        self._pool_box = QVBoxLayout()
        self._pool_box.setSpacing(4)
        self._rows_box = QVBoxLayout()
        self._rows_box.setSpacing(2)
        self._rows_box.setContentsMargins(0, 0, 0, 0)
        self._rows: dict[str, ColumnDropRow] = {}
        self._tokens: list[SourceColumnToken] = []

        # Construct the two splitter panels via the layout helper so this file
        # stays under the 500-line limit while keeping logic in a documented module.
        self.pool_panel, self.rows_scroll = build_columns_panels(
            self._pool_box, self._rows_box
        )

        # Wide mode (initial): left = canonical rows (scrollable), right = pool.
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.rows_scroll)
        self.splitter.addWidget(self.pool_panel)

        # Single top-level layout holds only the splitter.
        outer = QVBoxLayout(self)
        outer.addWidget(self.splitter)

    def resizeEvent(self, e: QResizeEvent) -> None:  # type: ignore[override]
        """Switch the splitter orientation when the widget crosses the width threshold.

        Wide (>= threshold): horizontal splitter, rows left, pool right.
        Narrow (< threshold): vertical splitter, pool top, rows bottom.
        No-ops when the mode is already correct to avoid redundant reordering.

        Args:
            e: The Qt resize event carrying the new widget size.
        """
        wide = e.size().width() >= self._width_threshold
        current_is_horizontal = self.splitter.orientation() == Qt.Orientation.Horizontal

        # Only reorder panels when the mode actually changes to avoid redundant work.
        if wide == current_is_horizontal:
            super().resizeEvent(e)
            return

        # Delegate panel detach and re-insert to the extracted layout helper.
        apply_splitter_orientation(
            self.splitter, self.pool_panel, self.rows_scroll, wide
        )

        super().resizeEvent(e)

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

        Clears existing tokens and recreates one per entry in ``columns``.

        Args:
            columns: The unconsumed source column names, in source order.
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

        Clears existing rows and recreates one per entry, wired to ``assign_column``.

        Args:
            rows: One ``(canonical_name, description, expected_dtype)`` tuple per
                row, in display order.
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

        Updates the matching row's assignment label when the row exists.

        Args:
            target_canonical: The canonical row whose assignment changed.
            source_column: The assigned source, or ``None`` when cleared.
        """
        row = self._rows.get(target_canonical)
        if row is not None:
            row.set_assignment(source_column)

    def set_dtype_indicator(
        self, target_canonical: str, coercible: bool, failing_example: str | None
    ) -> None:
        """Reflect the dtype-check result for one row.

        Updates the matching row's dtype indicator when the row exists.

        Args:
            target_canonical: The canonical row whose dtype state changed.
            coercible: Whether the matched values coerce to the expected dtype.
            failing_example: A masked failing example when not coercible.
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
