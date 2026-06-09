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

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

__all__ = [
    "SourceInputControls",
    "apply_schema_list",
    "assemble_source_input_layout",
    "build_edit_schema_button",
    "build_source_input_controls",
    "is_real_schema",
    "select_schema",
    "set_edit_enabled",
    "set_import_enabled",
]


@dataclass(frozen=True)
class SourceInputControls:
    """The child Qt controls of one :class:`SourceInputWidget`.

    Purpose:
        Carry the constructed child controls back to the widget so control
        construction can live in this helper module (keeping the widget under the
        500-line cap) while the widget retains ownership of the controls.

    Responsibilities:
        Hold references only; it performs no Qt work and no gating. The widget
        assigns these onto its own attributes and wires their signals.

    Attributes:
        path_edit: The read-only workbook-path display field.
        browse_button: The "Select File..." button.
        tab_combo: The worksheet-tab dropdown.
        render_checkbox: The "Render tab" checkbox.
        schema_combo: The schema-selection dropdown (placeholder first).
        build_schema_button: The "Build new schema" button.
        edit_schema_button: The "Edit Schema" button (disabled until a real
            schema is selected).
        error_label: The per-input error message label.
        import_button: The optional per-input Import button, or ``None`` when the
            widget was built without an ``import_label``.
    """

    path_edit: QLineEdit
    browse_button: QPushButton
    tab_combo: QComboBox
    render_checkbox: QCheckBox
    schema_combo: QComboBox
    build_schema_button: QPushButton
    edit_schema_button: QPushButton
    error_label: QLabel
    import_button: QPushButton | None


def build_source_input_controls(
    *,
    default_sheet: str,
    schema_placeholder: str,
    import_label: str | None,
) -> SourceInputControls:
    """Construct the child controls for a source-input widget.

    Args:
        default_sheet: A default sheet name pre-filled in the tab dropdown when
            non-empty.
        schema_placeholder: The ``<Choose Schema>`` placeholder kept as the first
            item of the schema dropdown.
        import_label: The label for the optional per-input Import button, or
            ``None`` to construct no import button.

    Returns:
        A :class:`SourceInputControls` holding the constructed controls. The Edit
        button is disabled and, when constructed, the Import button is disabled
        (both gate on a real schema selection).

    Side effects:
        Constructs Qt controls (no layout assembly or signal wiring).
    """
    path_edit = QLineEdit()
    path_edit.setReadOnly(True)
    tab_combo = QComboBox()
    # Pre-fill the default sheet only when one is supplied so an empty default
    # leaves the dropdown blank rather than adding an empty item.
    if default_sheet:
        tab_combo.addItem(default_sheet)
    schema_combo = QComboBox()
    schema_combo.addItem(schema_placeholder)
    # Construct the optional Import button only when the caller opts in; widgets
    # without an import label get no in-widget import control.
    import_button = QPushButton(import_label) if import_label is not None else None
    # Decision 8: the Import button starts disabled and enables only when a
    # non-placeholder schema is selected for this tab.
    if import_button is not None:
        import_button.setEnabled(False)
    return SourceInputControls(
        path_edit=path_edit,
        browse_button=QPushButton("Select File..."),
        tab_combo=tab_combo,
        render_checkbox=QCheckBox("Render tab"),
        schema_combo=schema_combo,
        build_schema_button=QPushButton("Build new schema"),
        edit_schema_button=build_edit_schema_button(),
        error_label=QLabel(""),
        import_button=import_button,
    )


def assemble_source_input_layout(
    parent: QWidget, input_label: str, controls: SourceInputControls
) -> None:
    """Assemble the source-input widget's layout from its controls.

    Builds the vertical layout: a labeled file row, the tab dropdown, the schema
    dropdown with the build/edit button row beside it, the render checkbox, the
    optional Import button, and the error label.

    Args:
        parent: The widget the top-level layout is installed on.
        input_label: The input's display label (for example ``"LE"``).
        controls: The constructed child controls to place into the layout.

    Returns:
        ``None``.

    Side effects:
        Installs a :class:`QVBoxLayout` on ``parent`` and adds the controls.
    """
    file_row = QHBoxLayout()
    file_row.addWidget(QLabel(input_label))
    file_row.addWidget(controls.path_edit)
    file_row.addWidget(controls.browse_button)

    layout = QVBoxLayout(parent)
    layout.addLayout(file_row)
    layout.addWidget(controls.tab_combo)
    # Issue #60 Defect 1: the "Edit Schema" button sits beside "Build new schema"
    # in a row so the per-tab schema controls (build/edit) are grouped.
    layout.addWidget(controls.schema_combo)
    schema_button_row = QHBoxLayout()
    schema_button_row.addWidget(controls.build_schema_button)
    schema_button_row.addWidget(controls.edit_schema_button)
    layout.addLayout(schema_button_row)
    layout.addWidget(controls.render_checkbox)
    # Place the optional Import button beside the render checkbox so the per-input
    # import control lives inside this widget (issue #27 AC11).
    if controls.import_button is not None:
        layout.addWidget(controls.import_button)
    layout.addWidget(controls.error_label)


def build_edit_schema_button() -> QPushButton:
    """Build the per-input "Edit Schema" button, disabled by default.

    Constructs the "Edit Schema" :class:`QPushButton` used beside the per-input
    Import button (issue #60 Defect 1). The button starts disabled because no
    real schema is selected at construction time; it is enabled only when a real
    (non-placeholder) schema is selected, mirroring the Import button's gating.

    Returns:
        A new disabled "Edit Schema" :class:`QPushButton`.

    Side effects:
        None beyond constructing the Qt button.
    """
    button = QPushButton("Edit Schema")
    # Start disabled: the Edit button is gated on a real schema selection, and at
    # construction the dropdown is on the placeholder, so nothing is editable yet.
    button.setEnabled(False)
    return button


def set_edit_enabled(button: QPushButton, enabled: bool) -> None:
    """Toggle the "Edit Schema" button's enabled state.

    Mirrors :func:`set_import_enabled` for the always-present Edit button. Unlike
    the optional Import button, the Edit button is always constructed, so this
    helper takes a non-optional button.

    Args:
        button: The "Edit Schema" button to toggle.
        enabled: ``True`` to enable the button, ``False`` to disable it.

    Returns:
        ``None``.

    Side effects:
        Sets ``button``'s enabled state.
    """
    button.setEnabled(enabled)


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
