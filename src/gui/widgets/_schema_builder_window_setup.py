"""Window-flag and default-size setup for the schema-builder dialog (issue #62).

This small helper applies the top-level window flags and default size to the
:class:`~src.gui.widgets.schema_builder_dialog.SchemaBuilderDialog` so the dialog
is resizable and exposes the standard minimize and maximize/restore controls in
addition to close (AC-8). It lives in its own module so the dialog file stays
under the repository's 500-line cap.

Responsibilities:
    - ``apply_schema_builder_window_flags``: set the resizable + min/max/close
      window flags and a default size on a dialog.

Scope boundaries:
    - Pure Qt window-flag/geometry setup. No service, matching, or transform
      logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDialog

__all__ = ["apply_schema_builder_window_flags"]

# Default dialog size chosen so the Identity/Columns/Key tabs and the AOP
# schema's 26 columns are reachable (with the Columns-tab scroll area) without
# immediately resizing. The user can still resize, minimize, and maximize.
_DEFAULT_WIDTH = 900
_DEFAULT_HEIGHT = 700


def apply_schema_builder_window_flags(dialog: QDialog) -> None:
    """Make the dialog a resizable top-level window with min/max/close controls.

    Sets the window flags so the dialog is a top-level ``Qt.Window`` exposing the
    minimize, maximize/restore, and close hints (AC-8), and sets a sensible
    default size so all rows are reachable with the Columns-tab scroll area.

    Args:
        dialog: The schema-builder dialog (or any ``QDialog``) to configure.

    Returns:
        ``None``.

    Side effects:
        Replaces the dialog's window flags and resizes it to the default size.
    """
    # A plain QDialog defaults to a fixed dialog frame without min/max buttons;
    # declaring it a top-level Window with the explicit min/max/close hints gives
    # the user the standard resizable window controls (AC-8).
    dialog.setWindowFlags(
        Qt.WindowType.Window
        | Qt.WindowType.WindowMinimizeButtonHint
        | Qt.WindowType.WindowMaximizeButtonHint
        | Qt.WindowType.WindowCloseButtonHint
    )
    dialog.resize(_DEFAULT_WIDTH, _DEFAULT_HEIGHT)
