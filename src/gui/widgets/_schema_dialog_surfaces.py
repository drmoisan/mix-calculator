"""Error and preview message-surface helpers for the schema-builder dialog.

This module isolates the thin error/preview message-surface accessors for the
:class:`~src.gui.widgets.schema_builder_dialog.SchemaBuilderDialog` so that file
stays under the repository's 500-line cap. Each function operates on the Derived
and Preview tab control bundles; the dialog delegates its surface methods here.

Responsibilities:
    - ``show_general_error``: render an error on the Derived + Preview surfaces.
    - ``set_formula_error`` / ``clear_formula_error`` / ``formula_error_text``:
      manage the inline Derived-tab formula error.
    - ``preview_message_text``: read the Preview-tab message label.

Scope boundaries:
    - Thin Qt-label accessors. No service, assembly, or transform logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.gui.widgets._schema_builder_tabs import (
        DerivedTabControls,
        PreviewTabControls,
    )

__all__ = [
    "clear_formula_error",
    "formula_error_text",
    "preview_message_text",
    "set_formula_error",
    "show_general_error",
]


def show_general_error(
    derived: DerivedTabControls, preview: PreviewTabControls, message: str
) -> None:
    """Render a general (non-formula) error on the error surfaces (AC-10).

    The message is shown on the Derived-tab error label (existing behavior) and
    mirrored to the Preview-tab message area so a preview failure is visible on the
    Preview tab rather than rendering nothing.

    Args:
        derived: The Derived-tab controls (error label).
        preview: The Preview-tab controls (message label).
        message: The error text to display.

    Returns:
        ``None``.

    Side effects:
        Updates the Derived-tab error label and the Preview-tab message label.
    """
    derived.error_label.setText(message)
    preview.message_label.setText(message)


def set_formula_error(derived: DerivedTabControls, message: str) -> None:
    """Display an inline formula-validation error on the Derived tab.

    Args:
        derived: The Derived-tab controls (error label).
        message: The descriptive formula error text.

    Returns:
        ``None``.

    Side effects:
        Updates the Derived-tab error label.
    """
    derived.error_label.setText(message)


def clear_formula_error(derived: DerivedTabControls) -> None:
    """Clear the inline formula-validation error surface.

    Args:
        derived: The Derived-tab controls (error label).

    Returns:
        ``None``.

    Side effects:
        Resets the Derived-tab error label.
    """
    derived.error_label.setText("")


def formula_error_text(derived: DerivedTabControls) -> str:
    """Return the inline formula/general error text (public test seam).

    Args:
        derived: The Derived-tab controls (error label).

    Returns:
        The Derived-tab error label text.
    """
    return derived.error_label.text()


def preview_message_text(preview: PreviewTabControls) -> str:
    """Return the Preview-tab message text (public test seam, AC-10).

    Args:
        preview: The Preview-tab controls (message label).

    Returns:
        The Preview-tab message label text (the missing-input / failure message or
        the "no rows" note; empty when a preview rendered).
    """
    return preview.message_label.text()
