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
    QVBoxLayout,
    QWidget,
)

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
    """Columns-tab container and its newline-delimited column editor.

    Attributes:
        widget: The tab container widget.
        editor: The plain-text editor holding one column per line as
            ``canonical|role|required|alias,alias``.
    """

    widget: QWidget
    editor: QPlainTextEdit


@dataclass
class KeyTabControls:
    """Key-tab container and its key-columns/sku-coercion controls.

    Attributes:
        widget: The tab container widget.
        columns: The comma-separated key-columns input.
        sku_coercion: The SKU-coercion checkbox.
    """

    widget: QWidget
    columns: QLineEdit
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
    """Derived-tab container and its formula editor and error label.

    Attributes:
        widget: The tab container widget.
        editor: The plain-text editor holding one derived column per line as
            ``name|expression``.
        error_label: The inline formula-error surface.
    """

    widget: QWidget
    editor: QPlainTextEdit
    error_label: QLabel


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
    """Build the Columns tab.

    Returns:
        The columns-tab controls bundle. Columns are edited as one line each in
        the form ``canonical|role|required|alias,alias``.
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.addWidget(QLabel("One column per line: canonical|role|required|aliases"))
    editor = QPlainTextEdit()
    layout.addWidget(editor)
    return ColumnsTabControls(widget=widget, editor=editor)


def build_key_tab() -> KeyTabControls:
    """Build the Key tab.

    Returns:
        The key-tab controls bundle.
    """
    widget = QWidget()
    layout = QFormLayout(widget)
    columns = QLineEdit()
    sku_coercion = QCheckBox("Coerce SKU")
    layout.addRow("Key columns (comma-separated)", columns)
    layout.addRow("SKU coercion", sku_coercion)
    return KeyTabControls(widget=widget, columns=columns, sku_coercion=sku_coercion)


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
    """Build the Derived/Formula tab.

    Returns:
        The derived-tab controls bundle. Derived columns are edited as one line
        each in the form ``name|expression``.
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.addWidget(QLabel("One derived column per line: name|expression"))
    editor = QPlainTextEdit()
    error_label = QLabel("")
    layout.addWidget(editor)
    layout.addWidget(error_label)
    return DerivedTabControls(widget=widget, editor=editor, error_label=error_label)


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
