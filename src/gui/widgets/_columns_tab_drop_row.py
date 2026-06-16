"""Canonical drop row for the Columns tab (Decision 4, research G).

This module holds :class:`ColumnDropRow`, the canonical row that composes a
descriptive label, a drag-and-drop assignment slot, and a dtype/value indicator.
It is extracted from :mod:`src.gui.widgets._columns_tab_drag` so that module
stays under the repository's 500-line cap while the Columns-tab row chooser and
masked value display are added (AC-6).

Responsibilities:
    - ``ColumnDropRow``: build and lay out the label, assignment slot, and
      indicator; delegate assignment/dtype/value-display state to its children.

Scope boundaries:
    - View only: no matching, no dtype logic. The presenter computes state and
      pushes it; the slot owns all drag-and-drop event handling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from src.gui.widgets._column_assignment_slot import ColumnAssignmentSlot
from src.gui.widgets._dtype_check_widget import DtypeCheckWidget

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ["ColumnDropRow"]


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

    def set_value_display(self, value: str) -> None:
        """Render a chosen source value on this row's indicator (AC-6).

        Args:
            value: The already-masked source cell value to display in place of the
                dtype glyph.

        Returns:
            ``None``.

        Side effects:
            Switches the embedded indicator to value-display mode.
        """
        self._indicator.set_value_display(value)

    def indicator_text(self) -> str:
        """Return the indicator's current text (public test seam).

        Returns:
            The dtype glyph / failing example / value-display text on the row's
            indicator.
        """
        return self._indicator.text()
