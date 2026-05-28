"""Export dialog (checklist + format selector + export-all).

This passive Qt dialog implements :class:`ExportViewProtocol`. It owns a
per-table checklist (``QListWidget`` with checkable items), a format selector
(``QComboBox``), an export-all control, and accept/cancel buttons. It contains
no service or transform logic.

Responsibilities:
    - Render the table checklist and the format dropdown.
    - Report the user's checked selection.
    - Check every item on export-all.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

__all__ = ["ExportDialog"]


class ExportDialog(QDialog):
    """Passive dialog implementing :class:`ExportViewProtocol`.

    Purpose:
        Let the user pick which tables to export and which format to use.

    Responsibilities:
        Render the checklist, format dropdown, and export-all control; report
        the user's selection via ``get_selected_names``.

    Usage:
        Constructed at the composition root; the export presenter pushes the
        table list and available formats, then drives ``on_export`` against the
        dialog's selection.

    Attributes:
        _list: The checklist of table names.
        _format_combo: The format selector dropdown.
        _select_all_button: The export-all control.
    """

    def __init__(
        self,
        available_formats: list[str],
        parent: QWidget | None = None,
    ) -> None:
        """Build the dialog controls.

        Args:
            available_formats: The format names to show in the dropdown.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Export Tables")

        self._list = QListWidget()
        self._format_combo = QComboBox()
        self._format_combo.addItems(available_formats)
        self._select_all_button = QPushButton("Export All")

        # Standard accept/cancel buttons; the composition root reads the dialog
        # exec result and the selection.
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self._list)
        layout.addWidget(self._format_combo)
        layout.addWidget(self._select_all_button)
        layout.addWidget(self._buttons)

        # Wire the export-all button to check every item and the dialog buttons
        # to the standard accept/reject slots.
        self._select_all_button.clicked.connect(self.select_all_tables)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

    def set_table_list(self, names: list[str]) -> None:
        """Render the exportable table names as a checkable checklist.

        Args:
            names: The table names to display.

        Returns:
            ``None``.

        Side effects:
            Replaces the checklist items.
        """
        self._list.clear()
        # Add one checkable item per name; items start unchecked so the user
        # explicitly opts in or uses export-all.
        for name in names:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self._list.addItem(item)

    def get_selected_names(self) -> list[str]:
        """Return the checked table names in display order.

        Returns:
            The names whose item check state is ``Checked``.
        """
        selected: list[str] = []
        # Walk every item and collect those currently checked, preserving order.
        # The index range is always in bounds, so item() is non-null per the stub.
        for index in range(self._list.count()):
            item = self._list.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected

    def select_all_tables(self) -> None:
        """Check every item in the checklist (export-all).

        Returns:
            ``None``.

        Side effects:
            Sets every item's check state to ``Checked``.
        """
        # Walk every item and mark it checked so a subsequent get_selected_names
        # returns the complete table set. Indices in range are always in bounds.
        for index in range(self._list.count()):
            self._list.item(index).setCheckState(Qt.CheckState.Checked)

    def set_item_checked(self, index: int, checked: bool) -> None:
        """Programmatically set the check state of one checklist item.

        This is the public entry tests use to drive the checklist without
        reaching into private state; it is also the same path the user click
        ultimately takes.

        Args:
            index: Zero-based item index.
            checked: The desired check state.

        Returns:
            ``None``.

        Side effects:
            Updates the item's check state. A no-op when ``index`` is out of
            range.
        """
        # Bounds-check on the count rather than nullness, since the stub types
        # item() as always returning a non-null QListWidgetItem.
        if index < 0 or index >= self._list.count():
            return
        self._list.item(index).setCheckState(
            Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        )

    def selected_format(self) -> str:
        """Return the currently selected format name from the dropdown."""
        return self._format_combo.currentText()

    def available_formats(self) -> list[str]:
        """Return the format names currently shown in the dropdown."""
        return [
            self._format_combo.itemText(i) for i in range(self._format_combo.count())
        ]
