"""Private wiring helpers for :mod:`src.gui.app`.

This module hosts the default file-dialog chooser factories and the export
dialog runner that ``build_application`` defaults to when the caller does not
inject its own. Splitting these out of :mod:`src.gui.app` keeps both modules
under the repository's 500-line cap (per
``.claude/rules/general-code-change.md``).

The underscore prefix marks the module as private to the ``src/gui``
package; production code outside the GUI composition root must not depend on
it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFileDialog

if TYPE_CHECKING:
    from src.gui.widgets.export_dialog import ExportDialog

__all__ = [
    "default_export_runner",
    "default_open_chooser",
    "default_save_chooser",
]

# SQLite filter used by the Save/Open file dialogs so the chooser narrows the
# user's view to ``.db`` files (matching the pipeline's SQLite output format).
_SQLITE_FILTER = "SQLite Databases (*.db)"

# Export Save-dialog filter carrying the format choice. Per v2 Decision 2 /
# research Q5, format selection lives in the Save dialog's filter string, not
# in the ExportDialog. ``default_export_runner`` parses the selected filter to
# decide whether to return ``"Excel"`` or ``"CSV"`` to the presenter.
_EXPORT_FILTER = "Excel (*.xlsx);;CSV (*.csv)"


def default_save_chooser() -> str | None:
    """Production save-path chooser backed by ``QFileDialog.getSaveFileName``.

    Returns:
        The chosen ``.db`` path, or ``None`` when the user cancels.
    """
    # QFileDialog returns (path, selected_filter); the filter element is not
    # used. An empty path indicates the user cancelled the dialog.
    path, _ = QFileDialog.getSaveFileName(None, "Save Database", "", _SQLITE_FILTER)
    return path or None


def default_open_chooser() -> str | None:
    """Production open-path chooser backed by ``QFileDialog.getOpenFileName``.

    Returns:
        The chosen ``.db`` path, or ``None`` when the user cancels.
    """
    # An empty path indicates the user cancelled the file dialog.
    path, _ = QFileDialog.getOpenFileName(None, "Open Database", "", _SQLITE_FILTER)
    return path or None


def default_export_runner(dialog: ExportDialog) -> tuple[str, str] | None:
    """Production export-dialog runner: ExportDialog + Save dialog filter parse.

    Per v2 Decision 2 / research Q5: the ExportDialog no longer carries a
    format selector. Format choice is made through the Save dialog's filter
    ("Excel (*.xlsx);;CSV (*.csv)"); ``"*.xlsx" in selected_filter`` resolves
    to ``"Excel"`` and ``"*.csv" in selected_filter`` resolves to ``"CSV"``.

    Args:
        dialog: The export dialog to show modally.

    Returns:
        A ``(format_name, destination_path)`` tuple on accept, or ``None``
        when either the export dialog or the Save dialog is cancelled.
    """
    accepted = dialog.exec()
    # ``exec`` returns truthy on accept and falsy on reject; an explicit truthy
    # check avoids depending on the Qt-specific QDialog.DialogCode integer.
    if not accepted:
        return None
    destination_path, selected_filter = QFileDialog.getSaveFileName(
        dialog, "Export Destination", "", _EXPORT_FILTER
    )
    if not destination_path:
        return None
    # Parse the selected filter string. The Save dialog returns the substring
    # the user picked (for example "Excel (*.xlsx)" or "CSV (*.csv)"); fall
    # back to "Excel" when the filter is empty so unknown environments default
    # to the v1 production format.
    if "*.csv" in selected_filter:
        format_name = "CSV"
    else:
        format_name = "Excel"
    return format_name, destination_path
