"""Preview-table population for the schema-builder Preview tab (AC-9).

This helper isolates the :class:`QTableWidget` population for the Preview tab so
the :class:`~src.gui.widgets.schema_builder_dialog.SchemaBuilderDialog` stays
under the repository's 500-line cap. It renders the applied-schema result rows
into the table, including a header row when one is supplied.

Responsibilities:
    - ``populate_preview_table``: fill a ``QTableWidget`` from string result rows.

Scope boundaries:
    - Thin Qt-table population. No service, assembly, or transform logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QTableWidgetItem

if TYPE_CHECKING:
    from collections.abc import Sequence

    from PySide6.QtWidgets import QTableWidget

    from src.gui.widgets._schema_builder_tabs import PreviewTabControls

__all__ = ["populate_preview_table", "read_table_text", "render_preview"]


def render_preview(controls: PreviewTabControls, rows: Sequence[Sequence[str]]) -> None:
    """Render result rows into the Preview tab and set its message (AC-9/AC-10).

    Populates the Preview-tab table from ``rows`` and clears the message area; an
    empty result leaves the table cleared with a "no rows" note so the tab never
    renders blank without explanation (AC-10).

    Args:
        controls: The Preview-tab controls (table + message label).
        rows: The applied-schema result rows, each a sequence of string cells.

    Returns:
        ``None``.

    Side effects:
        Replaces the Preview-tab table contents and message label text.
    """
    populate_preview_table(controls.table, rows)
    # An empty result is not an error, but blank rendering is confusing; state
    # plainly that the applied schema produced no rows (AC-10).
    controls.message_label.setText("" if rows else "Preview produced no rows.")


def populate_preview_table(
    table: QTableWidget,
    rows: Sequence[Sequence[str]],
    headers: Sequence[str] | None = None,
) -> None:
    """Populate ``table`` from string result rows, optionally with column headers.

    Clears the table, sets its dimensions from the widest row (and the header when
    given), and fills each cell with a :class:`QTableWidgetItem`. An empty ``rows``
    leaves the table cleared so the caller's message area can explain why no rows
    rendered.

    Args:
        table: The :class:`QTableWidget` to populate in place.
        rows: The result rows, each a sequence of string cell values.
        headers: Optional column header labels; when omitted no horizontal header
            labels are set.

    Returns:
        ``None``.

    Side effects:
        Replaces the table's contents, row/column counts, and header labels.
    """
    table.clear()
    table.setRowCount(0)
    table.setColumnCount(0)
    if not rows:
        return
    # Size the grid from the widest row and the header so every cell is reachable.
    column_count = max(len(row) for row in rows)
    if headers is not None:
        column_count = max(column_count, len(headers))
    table.setRowCount(len(rows))
    table.setColumnCount(column_count)
    if headers is not None:
        table.setHorizontalHeaderLabels(list(headers))
    # Fill each cell with a table item so the view renders the full result grid.
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            table.setItem(row_index, column_index, QTableWidgetItem(value))


def read_table_text(table: QTableWidget) -> str:
    """Return all populated cell texts of ``table`` joined with spaces (test seam).

    Walks every cell row by row so a test can assert a value appears anywhere in
    the rendered preview table without depending on its exact position.

    Args:
        table: The :class:`QTableWidget` to read.

    Returns:
        The populated cell texts joined with spaces; empty when the table has no
        populated cells.
    """
    values: list[str] = []
    # Collect every populated cell's text in row-major order.
    for row in range(table.rowCount()):
        for column in range(table.columnCount()):
            item = table.item(row, column)
            if item is not None:
                values.append(item.text())
    return " ".join(values)
