"""Tab-widget construction for the schema-builder dialog (Feature D).

This helper module builds the per-tab Qt widget trees used by
:class:`~src.gui.widgets.schema_builder_dialog.SchemaBuilderDialog`, keeping the
dialog file itself under the repository's 500-line cap. Each builder returns a
small dataclass that bundles the constructed container widget with the input
controls the dialog needs to read and write, so the dialog holds references to
the controls without owning their construction.

Responsibilities:
    - Construct the Identity, Columns, Key, Dedup, Derived, and Preview tab
      widget trees and expose their controls via typed control bundles.

Scope boundaries:
    - Pure Qt widget construction. No service, matching, or transform logic; the
      dialog and presenter own behavior.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.gui.widgets._columns_tab_drag import ColumnsTabWidget
from src.gui.widgets._key_tab_drag import KeyTabWidget

__all__ = [
    "ColumnsTabControls",
    "DedupTabControls",
    "DerivedTabControls",
    "IdentityTabControls",
    "KeyTabControls",
    "PreviewTabControls",
    "build_columns_tab",
    "build_dedup_tab",
    "build_derived_tab",
    "build_identity_tab",
    "build_key_tab",
    "build_preview_tab",
]


@dataclass
class IdentityTabControls:
    """Identity-tab container and its name/version/description fields.

    Attributes:
        widget: The tab container widget.
        name: The schema-name input.
        version: The schema-version input.
        description: The schema-description input.
    """

    widget: QWidget
    name: QLineEdit
    version: QLineEdit
    description: QLineEdit


@dataclass
class ColumnsTabControls:
    """Columns-tab container and its drag-and-drop columns widget.

    Attributes:
        widget: The tab container widget.
        columns_widget: The drag-and-drop :class:`ColumnsTabWidget` rendering the
            source-column token pool, the required/optional canonical rows, and the
            per-row dtype-check indicators (Decision 4). It replaces the prior
            plain-text "one column per line" editor.
    """

    widget: QWidget
    columns_widget: ColumnsTabWidget


@dataclass
class KeyTabControls:
    """Key-tab container and its drag-and-drop key widget plus SKU coercion.

    Attributes:
        widget: The tab container widget.
        key_widget: The drag-and-drop :class:`KeyTabWidget` rendering the column
            token pool, the repeatable Generic Text token, and the ordered key
            parts (Decision 2). It replaces the prior comma-separated key editor.
        sku_coercion: The SKU-coercion checkbox (retained).
    """

    widget: QWidget
    key_widget: KeyTabWidget
    sku_coercion: QCheckBox


@dataclass
class DedupTabControls:
    """Dedup-tab container and its mode/discriminator controls.

    Attributes:
        widget: The tab container widget.
        mode: The dedup-mode combo (``none``/``collapse``/``aggregate``).
        discriminator: The discriminator-column dropdown populated from existing
            canonical + derived column names only (no free-text entry).
    """

    widget: QWidget
    mode: QComboBox
    discriminator: QComboBox


@dataclass
class DerivedTabControls:
    """Derived-tab container, formula editor, error label, and add button.

    Attributes:
        widget: The tab container widget.
        editor: The plain-text editor holding one derived column per line as
            ``name|expression``.
        error_label: The inline formula-error surface.
        new_button: The "New derived column" button that opens the PowerQuery-style
            :class:`~src.gui.widgets._derived_formula_dialog.DerivedFormulaDialog`
            (Decision 7). The dialog wires its click handler.
    """

    widget: QWidget
    editor: QPlainTextEdit
    error_label: QLabel
    new_button: QPushButton


@dataclass
class PreviewTabControls:
    """Preview-tab container and its rendered-rows label.

    Attributes:
        widget: The tab container widget.
        rows_label: The label rendering the preview rows.
    """

    widget: QWidget
    rows_label: QLabel


def build_identity_tab() -> IdentityTabControls:
    """Build the Identity tab.

    Returns:
        The identity-tab controls bundle.
    """
    widget = QWidget()
    layout = QFormLayout(widget)
    name = QLineEdit()
    version = QLineEdit()
    description = QLineEdit()
    layout.addRow("Name", name)
    layout.addRow("Version", version)
    layout.addRow("Description", description)
    return IdentityTabControls(
        widget=widget, name=name, version=version, description=description
    )


def build_columns_tab() -> ColumnsTabControls:
    """Build the Columns tab around the drag-and-drop columns widget (Decision 4).

    The plain-text "one column per line" editor is replaced by
    :class:`ColumnsTabWidget`: a draggable source-column token pool over the
    required/optional canonical rows, each carrying its expected dtype and a
    pass/fail dtype-check indicator. The dialog binds a ``ColumnsTabPresenter`` to
    this widget so a drop assigns a source column to a canonical row.

    Returns:
        The columns-tab controls bundle exposing the drag-and-drop columns widget.
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    columns_widget = ColumnsTabWidget()
    layout.addWidget(columns_widget)
    return ColumnsTabControls(widget=widget, columns_widget=columns_widget)


def build_key_tab() -> KeyTabControls:
    """Build the Key tab around the drag-and-drop key widget (Decision 2).

    The comma-separated key editor is replaced by :class:`KeyTabWidget`: a pool of
    draggable column tokens and one repeatable Generic Text token above an ordered
    drop area for the composed key parts. The SKU-coercion checkbox is retained
    below the key widget. The dialog binds a ``KeyTabPresenter`` to this widget so a
    drop appends an ordered key part.

    Returns:
        The key-tab controls bundle exposing the drag-and-drop key widget and the
        retained SKU-coercion checkbox.
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    key_widget = KeyTabWidget()
    sku_coercion = QCheckBox("Coerce SKU")
    layout.addWidget(key_widget)
    layout.addWidget(sku_coercion)
    return KeyTabControls(
        widget=widget, key_widget=key_widget, sku_coercion=sku_coercion
    )


def build_dedup_tab() -> DedupTabControls:
    """Build the Dedup tab.

    Decision 1/6: the mode combo offers ``aggregate`` (the default), and the
    discriminator is a dropdown (no free-text entry) so a non-existent column
    cannot be chosen as discriminator. The default mode is ``aggregate`` and the
    discriminator dropdown is populated by the dialog from the existing canonical
    and derived column names plus the schema ``Key`` sentinel.

    Returns:
        The dedup-tab controls bundle.
    """
    widget = QWidget()
    layout = QFormLayout(widget)
    mode = QComboBox()
    # Aggregate is listed first so it is the default selection (Decision 1).
    mode.addItems(["aggregate", "collapse", "none"])
    discriminator = QComboBox()
    layout.addRow("Mode", mode)
    layout.addRow("Discriminator column", discriminator)
    return DedupTabControls(widget=widget, mode=mode, discriminator=discriminator)


def build_derived_tab() -> DerivedTabControls:
    """Build the Derived/Formula tab with the PowerQuery-style add button.

    The tab retains the plain-text ``name|expression`` editor (which renders the
    accumulated derived rows) and adds a "New derived column" button that opens the
    :class:`~src.gui.widgets._derived_formula_dialog.DerivedFormulaDialog`
    (Decision 7). The dialog wires the button's click handler.

    Returns:
        The derived-tab controls bundle exposing the editor, error label, and the
        "New derived column" button.
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    new_button = QPushButton("New derived column")
    layout.addWidget(new_button)
    layout.addWidget(QLabel("One derived column per line: name|expression"))
    editor = QPlainTextEdit()
    error_label = QLabel("")
    layout.addWidget(editor)
    layout.addWidget(error_label)
    return DerivedTabControls(
        widget=widget, editor=editor, error_label=error_label, new_button=new_button
    )


def build_preview_tab() -> PreviewTabControls:
    """Build the Preview tab.

    Returns:
        The preview-tab controls bundle.
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    rows_label = QLabel("")
    layout.addWidget(QLabel("Preview:"))
    layout.addWidget(rows_label)
    return PreviewTabControls(widget=widget, rows_label=rows_label)
