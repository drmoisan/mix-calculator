"""Multi-select Key-tab widget (Decision D-2, Option C).

This widget replaces the drag-and-drop Key tab (column tokens + Generic Text
token) with a simple multi-select of the declared canonical columns that compose
the key. The user selects which declared columns form the key, in selection
order; the dialog maps the ordered selection to ``column-ref`` ``KeySpec`` parts
joined by a default literal-text separator (D-2). The ``KeySpec``/``KeyPart``
model and the loader's key resolution are unchanged.

Responsibilities:
    - ``KeyMultiSelectWidget``: render a checkable list of declared canonical
      columns, preserve the order in which columns were selected, and expose the
      ordered selection.

Scope boundaries:
    - View only: no key assembly or validation. The dialog maps the selection to
      ``KeySpec`` parts; the model validates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.gui.widgets._schema_builder_tabs import KeyTabControls

__all__ = [
    "KeyMultiSelectWidget",
    "read_key_controls",
    "set_key_controls",
    "set_key_parts_controls",
]


class KeyMultiSelectWidget(QWidget):
    """A checkable multi-select of declared canonical columns for the key.

    Purpose:
        Let the user pick which declared canonical columns compose the key by
        checking list items, replacing the drag-and-drop column/Generic-Text UI
        (D-2, Option C).

    Responsibilities:
        Render one checkable item per available column, track the order items were
        checked so the composed key preserves selection order, and expose the
        ordered checked selection. It performs no key assembly or validation.

    Usage:
        The dialog calls :meth:`set_available_columns` to populate the list,
        :meth:`set_selected_columns` to render a loaded selection, and
        :meth:`selected_columns` to read the ordered selection for assembly.

    Attributes:
        _list: The checkable list of available canonical column names.
        _selection_order: The canonical names in the order they were checked, so a
            later uncheck/recheck preserves intuitive ordering.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the empty multi-select list with its heading.

        Args:
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        # Track check order so the composed key reflects the order columns were
        # selected rather than list order.
        self._selection_order: list[str] = []
        self._list = QListWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select key columns (in selection order):"))
        layout.addWidget(self._list)
        # Re-derive the ordered selection whenever an item's check state changes.
        self._list.itemChanged.connect(self._on_item_changed)

    def set_available_columns(self, columns: list[str]) -> None:
        """Populate the list with one checkable item per available column.

        Existing checked columns that remain available stay checked and keep their
        selection order; columns no longer available drop out of the selection.

        Args:
            columns: The declared canonical column names to offer, in display order.

        Returns:
            ``None``.

        Side effects:
            Rebuilds the list items and prunes the selection order to the still
            available, still checked columns.
        """
        previously_checked = set(self._ordered_checked())
        # Block signals while rebuilding so repopulation does not fire item-changed
        # for each added item.
        blocked = self._list.blockSignals(True)
        self._list.clear()
        # Add one checkable item per available column, restoring its prior check
        # state so a repopulate preserves the user's selection.
        for name in columns:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = name in previously_checked
            item.setCheckState(
                Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )
            self._list.addItem(item)
        self._list.blockSignals(blocked)
        # Keep only still-available columns in the recorded order, appending any
        # newly-checked columns the rebuild restored.
        available = set(columns)
        self._selection_order = [
            name for name in self._selection_order if name in available
        ]

    def set_selected_columns(self, columns: list[str]) -> None:
        """Check the given columns in order, unchecking all others.

        Args:
            columns: The ordered canonical column names to mark as selected; names
                not present in the list are ignored.

        Returns:
            ``None``.

        Side effects:
            Updates each item's check state and records ``columns`` (restricted to
            present names) as the selection order.
        """
        wanted = list(columns)
        blocked = self._list.blockSignals(True)
        # Check exactly the wanted columns, unchecking everything else so the
        # rendered selection matches the pushed key composition.
        for index in range(self._list.count()):
            item = self._list.item(index)
            checked = item.text() in wanted
            item.setCheckState(
                Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )
        self._list.blockSignals(blocked)
        present = {self._list.item(i).text() for i in range(self._list.count())}
        self._selection_order = [name for name in wanted if name in present]

    def selected_columns(self) -> list[str]:
        """Return the checked columns in selection order.

        Returns:
            The canonical names of the checked items, ordered by when they were
            checked.
        """
        return self._ordered_checked()

    def toggle_column(self, name: str, *, checked: bool) -> None:
        """Check or uncheck one column by name, firing the live change path.

        Programmatic seam mirroring a user's click on a list item: it sets the
        named item's check state, which emits ``itemChanged`` and so re-derives the
        selection order exactly as an interactive toggle would.

        Args:
            name: The canonical column name to toggle.
            checked: ``True`` to check the item, ``False`` to uncheck it.

        Returns:
            ``None``.

        Side effects:
            Updates the item's check state (firing ``itemChanged``); a no-op when
            no item matches ``name``.
        """
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        # Find the matching item by text and toggle it; signals stay connected so
        # the selection-order tracking runs as in the interactive path.
        for index in range(self._list.count()):
            item = self._list.item(index)
            if item.text() == name:
                item.setCheckState(state)
                return

    def _on_item_changed(self, _item: QListWidgetItem) -> None:
        """Re-derive the ordered selection when a check state changes.

        Args:
            _item: The item whose state changed (read from the list, not the arg).

        Returns:
            ``None``.

        Side effects:
            Updates the recorded selection order: appends newly-checked columns and
            drops unchecked ones, preserving the order of still-checked columns.
        """
        checked_now = {
            self._list.item(i).text()
            for i in range(self._list.count())
            if self._list.item(i).checkState() == Qt.CheckState.Checked
        }
        # Drop columns that are no longer checked, preserving prior order.
        order = [name for name in self._selection_order if name in checked_now]
        # Append any newly-checked column not already recorded so it lands last.
        for name in checked_now:
            if name not in order:
                order.append(name)
        self._selection_order = order

    def _ordered_checked(self) -> list[str]:
        """Return currently-checked columns in recorded selection order.

        Returns:
            The checked canonical names, ordered by selection; checked names with
            no recorded order (defensive) are appended in list order.
        """
        checked = {
            self._list.item(i).text()
            for i in range(self._list.count())
            if self._list.item(i).checkState() == Qt.CheckState.Checked
        }
        ordered = [name for name in self._selection_order if name in checked]
        # Defensive: include any checked column missing from the order record.
        for name in checked:
            if name not in ordered:
                ordered.append(name)
        return ordered


def set_key_controls(
    controls: KeyTabControls, columns: tuple[str, ...], sku_coercion: bool
) -> None:
    """Render the key selection and SKU flag onto the Key-tab controls (D-2).

    Args:
        controls: The Key-tab controls (multi-select widget + SKU checkbox).
        columns: The ordered key column names to mark as selected.
        sku_coercion: Whether SKU coercion is enabled.

    Returns:
        ``None``.

    Side effects:
        Checks the selected columns in the multi-select and updates the SKU
        checkbox.
    """
    controls.key_widget.set_selected_columns(list(columns))
    controls.sku_coercion.setChecked(sku_coercion)


def read_key_controls(controls: KeyTabControls) -> tuple[tuple[str, ...], bool]:
    """Return the live key selection and SKU flag from the Key-tab controls (D-2).

    Args:
        controls: The Key-tab controls (multi-select widget + SKU checkbox).

    Returns:
        A ``(columns, sku_coercion)`` tuple; ``columns`` are the checked canonical
        columns in selection order, and the SKU flag is read from the checkbox.
    """
    columns = tuple(controls.key_widget.selected_columns())
    return (columns, controls.sku_coercion.isChecked())


def set_key_parts_controls(
    controls: KeyTabControls, parts: list[tuple[str, str]]
) -> None:
    """Select the ordered column-ref parts on the Key-tab multi-select (D-2).

    Interleaved literal-text separators are ignored (re-derived at assembly).

    Args:
        controls: The Key-tab controls (multi-select widget + SKU checkbox).
        parts: One ``(kind, value)`` tuple per key part, in order.

    Returns:
        ``None``.

    Side effects:
        Selects the ordered column-ref columns in the multi-select.
    """
    # Select only the column-ref parts, in order; literal-text separators are not
    # user-selectable in the multi-select (D-2).
    columns = [value for kind, value in parts if kind == "column-ref"]
    controls.key_widget.set_selected_columns(columns)
