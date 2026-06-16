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
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.widgets._columns_tab_drag import ColumnsTabWidget
from src.gui.widgets._key_multiselect_widget import KeyMultiSelectWidget

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
    "read_identity_controls",
    "set_identity_controls",
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
    description: QPlainTextEdit


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
    """Key-tab container and its multi-select key widget plus SKU coercion.

    Attributes:
        widget: The tab container widget.
        key_widget: The :class:`KeyMultiSelectWidget` multi-select of declared
            canonical columns that compose the key (D-2, Option C). It replaces the
            prior drag-and-drop column/Generic-Text key UI.
        sku_coercion: The SKU-coercion checkbox (retained).
    """

    widget: QWidget
    key_widget: KeyMultiSelectWidget
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
            ``name = expression``.
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
    """Preview-tab container, result table, and message area (AC-9/AC-10).

    Attributes:
        widget: The tab container widget.
        table: The :class:`QTableWidget` rendering the applied-schema result rows
            with column headers.
        message_label: The label surfacing a missing-input / assembly-failure
            message when the preview cannot render (AC-10).
    """

    widget: QWidget
    table: QTableWidget
    message_label: QLabel


def build_identity_tab() -> IdentityTabControls:
    """Build the Identity tab.

    Returns:
        The identity-tab controls bundle.
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    # Name and version stay in a fixed-height form layout; the multi-line
    # description is added below in the outer VBox so it can expand vertically
    # with the window (AC-2).
    form = QFormLayout()
    name = QLineEdit()
    version = QLineEdit()
    form.addRow("Name", name)
    form.addRow("Version", version)
    layout.addLayout(form)
    # The description is a wrapping multi-line editor with an Expanding vertical
    # size policy so it grows and shrinks with the window (AC-2). A stretch factor
    # in addWidget lets it claim the available vertical space below the form.
    layout.addWidget(QLabel("Description"))
    description = QPlainTextEdit()
    description.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
    description.setSizePolicy(
        QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
    )
    layout.addWidget(description, stretch=1)
    return IdentityTabControls(
        widget=widget, name=name, version=version, description=description
    )


def set_identity_controls(
    controls: IdentityTabControls, name: str, version: str, description: str
) -> None:
    """Render the identity fields onto the Identity-tab controls (AC-2).

    Args:
        controls: The Identity-tab controls bundle.
        name: The schema name.
        version: The schema version.
        description: The multi-line schema description.

    Returns:
        ``None``.

    Side effects:
        Updates the Identity-tab name/version line edits and the multi-line
        description editor.
    """
    controls.name.setText(name)
    controls.version.setText(version)
    controls.description.setPlainText(description)


def read_identity_controls(controls: IdentityTabControls) -> tuple[str, str, str]:
    """Return the entered identity fields from the Identity-tab controls.

    Args:
        controls: The Identity-tab controls bundle.

    Returns:
        A ``(name, version, description)`` tuple read from the controls, with the
        description read via the multi-line plain-text API.
    """
    return (
        controls.name.text(),
        controls.version.text(),
        controls.description.toPlainText(),
    )


def build_columns_tab() -> ColumnsTabControls:
    """Build the Columns tab around the drag-and-drop columns widget (Decision 4).

    The plain-text "one column per line" editor is replaced by
    :class:`ColumnsTabWidget`: a draggable source-column token pool over the
    required/optional canonical rows, each carrying its expected dtype and a
    pass/fail dtype-check indicator. The dialog binds a ``ColumnsTabPresenter`` to
    this widget so a drop assigns a source column to a canonical row.

    The :class:`ColumnsTabWidget` is wrapped in a resizable :class:`QScrollArea`
    (issue #62, AC-7) so every canonical row is reachable by scrolling when the
    rows exceed the visible height (the AOP schema has 26 columns). The returned
    ``columns_widget`` still references the real :class:`ColumnsTabWidget` so the
    binder wiring is unaffected.

    Returns:
        The columns-tab controls bundle exposing the drag-and-drop columns widget.
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    columns_widget = ColumnsTabWidget()
    # Wrap the columns widget in a resizable scroll area so all canonical rows are
    # reachable when they exceed the visible height (AC-7). setWidgetResizable lets
    # the inner widget grow/shrink with the viewport while still scrolling when
    # content overflows. The bundle keeps columns_widget as the real widget so the
    # binder and existing tests bind to the same instance.
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(columns_widget)
    layout.addWidget(scroll_area)
    return ColumnsTabControls(widget=widget, columns_widget=columns_widget)


def build_key_tab() -> KeyTabControls:
    """Build the Key tab around a multi-select of declared columns (D-2, Option C).

    The drag-and-drop column/Generic-Text key UI is replaced by
    :class:`KeyMultiSelectWidget`: a checkable list of the declared canonical
    columns the user selects, in order, to compose the key. The SKU-coercion
    checkbox is retained below the multi-select. The dialog maps the ordered
    selection to ``column-ref`` ``KeySpec`` parts joined by a default separator;
    the ``KeySpec`` model and the loader are unchanged.

    Returns:
        The key-tab controls bundle exposing the multi-select key widget and the
        retained SKU-coercion checkbox.
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    key_widget = KeyMultiSelectWidget()
    sku_coercion = QCheckBox("Coerce SKU")
    layout.addWidget(key_widget)
    layout.addWidget(sku_coercion)
    return KeyTabControls(
        widget=widget, key_widget=key_widget, sku_coercion=sku_coercion
    )


def build_dedup_tab() -> DedupTabControls:
    """Build the Dedup tab.

    Decision 1/6 and D-3: the mode combo offers ``auto`` (the new default, no
    discriminator required), ``aggregate``, ``collapse``, and ``none``. The
    discriminator is a dropdown (no free-text entry) so a non-existent column
    cannot be chosen; it is not required when ``auto`` is selected. The dropdown is
    populated by the dialog from the existing canonical and derived column names
    plus the schema ``Key`` sentinel.

    Returns:
        The dedup-tab controls bundle.
    """
    widget = QWidget()
    layout = QFormLayout(widget)
    mode = QComboBox()
    # Auto is listed first so it is the default selection (D-3): it groups by
    # dimension roles and sums measure roles with no discriminator required.
    mode.addItems(["auto", "aggregate", "collapse", "none"])
    discriminator = QComboBox()
    layout.addRow("Mode", mode)
    layout.addRow("Discriminator column", discriminator)
    return DedupTabControls(widget=widget, mode=mode, discriminator=discriminator)


def build_derived_tab() -> DerivedTabControls:
    """Build the Derived/Formula tab with the PowerQuery-style add button.

    The tab retains the plain-text ``name = expression`` editor (which renders the
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
    layout.addWidget(QLabel("One derived column per line: name = expression"))
    editor = QPlainTextEdit()
    error_label = QLabel("")
    layout.addWidget(editor)
    layout.addWidget(error_label)
    return DerivedTabControls(
        widget=widget, editor=editor, error_label=error_label, new_button=new_button
    )


def build_preview_tab() -> PreviewTabControls:
    """Build the Preview tab with a result table and a message area (AC-9/AC-10).

    The plain rows label is replaced by a :class:`QTableWidget` that renders the
    applied-schema result with column headers (AC-9); a separate message label
    surfaces a specific missing-input / assembly-failure message when the preview
    cannot render (AC-10).

    Returns:
        The preview-tab controls bundle exposing the result table and message area.
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.addWidget(QLabel("Preview:"))
    table = QTableWidget()
    message_label = QLabel("")
    layout.addWidget(table)
    layout.addWidget(message_label)
    return PreviewTabControls(widget=widget, table=table, message_label=message_label)
