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

# Minimum window size below the default so the user can drag the window smaller
# than 900x700. Without an explicit minimum below the default, Qt may honor the
# layout's size hint as a hard minimum and suppress the drag-resize grip (AC-1).
_MIN_WIDTH = 400
_MIN_HEIGHT = 400


def apply_schema_builder_window_flags(dialog: QDialog) -> None:
    """Make the dialog a resizable top-level window with min/max/close controls.

    Sets the window flags so the dialog is a top-level ``Qt.Window`` exposing the
    minimize, maximize/restore, and close hints (AC-1), sets a minimum size below
    the default so the user can drag the window smaller, and sets a sensible
    default size so all rows are reachable with the Columns-tab scroll area.

    Args:
        dialog: The schema-builder dialog (or any ``QDialog``) to configure.

    Returns:
        ``None``.

    Side effects:
        Replaces the dialog's window flags, sets its minimum size, and resizes it
        to the default size.
    """
    # A plain QDialog defaults to a fixed dialog frame without min/max buttons;
    # declaring it a top-level Window with the explicit min/max/close hints gives
    # the user the standard resizable window controls (AC-1).
    dialog.setWindowFlags(
        Qt.WindowType.Window
        | Qt.WindowType.WindowMinimizeButtonHint
        | Qt.WindowType.WindowMaximizeButtonHint
        | Qt.WindowType.WindowCloseButtonHint
    )
    # Set a minimum size below the default so the window reports a resizable
    # minimum; without this the layout's size hint can act as a hard floor that
    # blocks drag-resize below 900x700 on some platforms (AC-1).
    dialog.setMinimumSize(_MIN_WIDTH, _MIN_HEIGHT)
    dialog.resize(_DEFAULT_WIDTH, _DEFAULT_HEIGHT)
