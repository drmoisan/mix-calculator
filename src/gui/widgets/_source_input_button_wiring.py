"""Schema-combo and import-button helpers for :class:`SourceInputWidget`.

This helper module holds the schema-dropdown population and the per-tab import
button gating logic for the source-input widget, extracted so
``source_input_widget.py`` stays under the repository's 500-line cap before the
import-gating behavior (Decision 8) is added. The functions operate on the
widget's Qt controls passed in by the widget; they hold no widget state of their
own.

Responsibilities:
    - ``apply_schema_list``: rebuild a schema dropdown with the placeholder first.
    - ``select_schema``: select a schema by name, appending it when absent.
    - ``set_import_enabled``: toggle an optional import button's enabled state.

Scope boundaries:
    - Operates on injected Qt controls only; no presenter, service, or transform
      logic. The widget owns the controls and forwards signals.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QComboBox, QPushButton

__all__ = [
    "apply_schema_list",
    "is_real_schema",
    "select_schema",
    "set_import_enabled",
]


def is_real_schema(name: str, placeholder: str) -> bool:
    """Return whether a dropdown selection is a real schema (not the placeholder).

    Args:
        name: The selected dropdown text.
        placeholder: The ``<Choose Schema>`` placeholder text.

    Returns:
        ``True`` when ``name`` is non-empty and not the placeholder; ``False``
        for the placeholder or an empty selection.
    """
    return bool(name) and name != placeholder


def apply_schema_list(combo: QComboBox, placeholder: str, names: list[str]) -> None:
    """Rebuild a schema dropdown with the placeholder first, then ``names``.

    Args:
        combo: The schema dropdown to repopulate.
        placeholder: The ``<Choose Schema>`` placeholder kept as the first item so
            the dropdown can return to "no schema selected".
        names: The schema names to offer, in display order.

    Returns:
        ``None``.

    Side effects:
        Clears and repopulates ``combo`` and leaves the placeholder selected.
    """
    # Rebuild with the placeholder first so the no-match path can always return to
    # the unselected state; the supplied schema names follow it.
    combo.clear()
    combo.addItem(placeholder)
    combo.addItems(names)
    combo.setCurrentIndex(0)


def select_schema(combo: QComboBox, name: str) -> None:
    """Select ``name`` in the dropdown, appending it when not already present.

    Args:
        combo: The schema dropdown to update.
        name: The schema name to select.

    Returns:
        ``None``.

    Side effects:
        Updates ``combo``'s selection (which emits ``currentTextChanged``);
        appends ``name`` first when it is not in the list so the selection always
        takes effect.
    """
    # Find the matching index; append the name when missing so the selection
    # always reflects the requested schema.
    index = combo.findText(name)
    if index < 0:
        combo.addItem(name)
        index = combo.findText(name)
    combo.setCurrentIndex(index)


def set_import_enabled(button: QPushButton | None, enabled: bool) -> None:
    """Toggle an optional import button's enabled state.

    Args:
        button: The per-input import button, or ``None`` when the widget was
            constructed without one.
        enabled: ``True`` to enable the button, ``False`` to disable it.

    Returns:
        ``None``.

    Side effects:
        Sets ``button``'s enabled state when the button exists; a no-op when the
        widget has no import button.
    """
    # Only toggle when an import button exists; widgets built without an import
    # label have no button to gate.
    if button is not None:
        button.setEnabled(enabled)
