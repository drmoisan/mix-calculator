"""Per-input source-selection widget (file + worksheet tab + render checkbox).

This passive Qt widget implements :class:`SourceSelectionViewProtocol`. It owns a
file-select button, a tab dropdown, a "render tab" checkbox, and an error label.
It contains no transform or service logic; user actions are exposed as Qt signals
that the composition root wires to a ``SourceSelectionPresenter``.

Responsibilities:
    - Let the user pick a workbook file and choose a worksheet tab.
    - Render the tab list, render an error message, and forward user actions as
      signals (``file_selected``, ``render_tab_requested``).

The widget holds no logic beyond view state; the presenter decides what to do.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QPushButton,
    QWidget,
)

from src.gui.widgets._source_input_button_wiring import (
    apply_schema_list,
    assemble_source_input_layout,
    build_source_input_controls,
    is_real_schema,
    select_schema,
    set_edit_enabled,
    set_import_enabled,
)

__all__ = ["SourceInputWidget"]

# File dialog filter restricting selection to Excel workbooks.
_EXCEL_FILTER = "Excel Workbooks (*.xlsx)"

# Placeholder shown as the first item of the schema dropdown when no schema is
# selected (WS2 / issue #48). Auto-select replaces the current selection; the
# no-match path leaves this placeholder selected.
_SCHEMA_PLACEHOLDER = "<Choose Schema>"


class SourceInputWidget(QWidget):
    """Passive view for selecting one input's workbook file and worksheet tab.

    Purpose:
        Provide the per-input (LE/AOP/SKU_LU) file picker, tab dropdown, and
        render-tab checkbox, implementing :class:`SourceSelectionViewProtocol`.

    Responsibilities:
        Render tab names and errors; emit signals for file selection and
        render-tab requests. It holds no service or transform logic.

    Usage:
        Constructed with an input label and a default sheet name; the composition
        root connects ``file_selected`` and ``render_tab_requested`` to the
        presenter. The current file path and selected sheet are read via
        ``current_path`` and ``current_sheet``.

    Attributes:
        file_selected: Emitted with the chosen workbook path when a file is
            picked.
        render_tab_requested: Emitted with ``(path, sheet)`` when the render-tab
            checkbox is checked with a selected tab.
        schema_selected: Emitted with the selected schema name when the user
            picks a real schema (not the ``<Choose Schema>`` placeholder) in the
            schema dropdown (WS2 / issue #48).
        build_schema_requested: Emitted when the user clicks the per-tab "Build
            new schema" button (WS2 / issue #48).
        edit_schema_requested: Emitted when the user clicks the per-tab "Edit
            Schema" button (issue #60 Defect 1). The composition root opens the
            schema builder seeded from the currently-selected schema.
        _import_button: The optional per-input Import button, constructed only
            when an ``import_label`` is supplied (issue #27 AC11). ``None`` when
            the widget is built without an import button.
    """

    file_selected: Signal = Signal(str)
    render_tab_requested: Signal = Signal(str, str)
    # WS2 (issue #48): emitted with the selected schema name when the user picks
    # a schema in the dropdown (the placeholder selection is suppressed).
    schema_selected: Signal = Signal(str)
    # WS2: emitted when the user clicks the per-tab "Build new schema" button.
    build_schema_requested: Signal = Signal()
    # Issue #60 Defect 1: emitted when the user clicks the per-tab "Edit Schema"
    # button so the composition root opens the builder seeded from the selection.
    edit_schema_requested: Signal = Signal()

    def __init__(
        self,
        input_label: str,
        default_sheet: str = "",
        parent: QWidget | None = None,
        *,
        import_label: str | None = None,
    ) -> None:
        """Build the widget controls.

        Args:
            input_label: The input's display label (for example ``"LE"``).
            default_sheet: A default sheet name pre-filled in the tab dropdown.
            parent: Optional Qt parent widget.
            import_label: Optional label for a per-input Import button. When
                supplied (for example ``"Import LE"``), an Import button is
                constructed inside this widget beside the render checkbox and
                exposed via :attr:`import_btn` (issue #27 AC11). When ``None``
                (the default), no import button is constructed.

        Returns:
            ``None``.

        Side effects:
            Constructs the child controls and, when ``import_label`` is
            supplied, an additional Import :class:`QPushButton` added to the
            widget's layout.
        """
        super().__init__(parent)
        self._path = ""

        # Construct the child controls and assemble the layout via the helper
        # module so this widget stays under the 500-line cap (issue #60 Defect 1
        # adds the Edit Schema button). The widget retains ownership of the
        # controls by assigning them onto its own attributes below.
        controls = build_source_input_controls(
            default_sheet=default_sheet,
            schema_placeholder=_SCHEMA_PLACEHOLDER,
            import_label=import_label,
        )
        self._path_edit = controls.path_edit
        self._browse_button = controls.browse_button
        self._tab_combo = controls.tab_combo
        self._render_checkbox = controls.render_checkbox
        self._schema_combo = controls.schema_combo
        self._build_schema_button = controls.build_schema_button
        self._edit_schema_button = controls.edit_schema_button
        self._error_label = controls.error_label
        self._import_button = controls.import_button
        assemble_source_input_layout(self, input_label, controls)

        # Wire internal controls to the widget's signal-emitting handlers.
        self._browse_button.clicked.connect(self.open_file_dialog)
        self._render_checkbox.toggled.connect(self._on_render_toggled)
        # v2 (AC-1): when the user changes the worksheet tab while the render
        # checkbox is checked, re-request a preview for the new sheet.
        self._tab_combo.currentTextChanged.connect(self._on_tab_changed)
        # WS2: forward schema selection and build-new requests as signals.
        self._schema_combo.currentTextChanged.connect(self._on_schema_changed)
        self._build_schema_button.clicked.connect(self.build_schema_requested.emit)
        # Issue #60 Defect 1: forward Edit-Schema clicks as a signal the
        # composition root wires to open the builder seeded from the selection.
        self._edit_schema_button.clicked.connect(self.edit_schema_requested.emit)

    @property
    def import_btn(self) -> QPushButton:
        """Return the per-input Import button.

        Exposed read-only so the composition root can connect the button's
        ``clicked`` signal and toggle its enabled state (issue #27 AC11). The
        button exists only when the widget was constructed with an
        ``import_label``.

        Returns:
            The Import :class:`QPushButton` owned by this widget.

        Raises:
            AttributeError: When the widget was constructed without an
                ``import_label`` and therefore has no import button.
        """
        if self._import_button is None:
            msg = (
                "This SourceInputWidget was constructed without an import_label, "
                "so it has no import button."
            )
            raise AttributeError(msg)
        return self._import_button

    @property
    def build_schema_btn(self) -> QPushButton:
        """Return the per-tab "Build new schema" button (WS2).

        Exposed read-only so the composition root can connect the button (in
        addition to the ``build_schema_requested`` signal) and tests can click it
        deterministically.

        Returns:
            The "Build new schema" :class:`QPushButton` owned by this widget.
        """
        return self._build_schema_button

    @property
    def edit_schema_btn(self) -> QPushButton:
        """Return the per-tab "Edit Schema" button (issue #60 Defect 1).

        Exposed read-only so the composition root can connect the button (in
        addition to the ``edit_schema_requested`` signal) and tests can click it
        and assert its enabled state deterministically. The button is disabled
        until a real (non-placeholder) schema is selected.

        Returns:
            The "Edit Schema" :class:`QPushButton` owned by this widget.
        """
        return self._edit_schema_button

    @property
    def tab_combo(self) -> QComboBox:
        """Return the worksheet-tab dropdown (Decision 9 discovery seam).

        Returns:
            The worksheet-tab :class:`QComboBox` owned by this widget.
        """
        return self._tab_combo

    @property
    def render_checkbox(self) -> QCheckBox:
        """Return the underlying render-tab checkbox.

        Exposed read-only so the composition root can connect to its
        ``toggled`` signal (per spec section 1) without reaching into private
        state. Tests use this seam to drive the toggle deterministically.
        """
        return self._render_checkbox

    def current_path(self) -> str:
        """Return the currently selected workbook path (empty if none)."""
        return self._path

    def current_sheet(self) -> str:
        """Return the currently selected worksheet tab (empty if none)."""
        return self._tab_combo.currentText()

    def error_text(self) -> str:
        """Return the current error-label text (empty when none shown)."""
        return self._error_label.text()

    def set_current_sheet(self, sheet: str) -> None:
        """Programmatically change the selected worksheet in the dropdown.

        This is the public test seam used to drive ``_on_tab_changed`` without
        reaching into private state. In production the user changes the tab
        through the dropdown widget.

        Args:
            sheet: The worksheet name to select. Must be present in the current
                tab list; absent names are appended to the dropdown so the
                selection still takes effect.

        Returns:
            ``None``.

        Side effects:
            Updates the dropdown selection, which triggers
            ``QComboBox.currentTextChanged`` and routes to ``_on_tab_changed``.
        """
        # Find the matching index; append the sheet if it is not present so the
        # current selection always reflects the requested name.
        index = self._tab_combo.findText(sheet)
        if index < 0:
            self._tab_combo.addItem(sheet)
            index = self._tab_combo.findText(sheet)
        self._tab_combo.setCurrentIndex(index)

    def set_render_tab_checked(self, checked: bool) -> None:
        """Programmatically toggle the render-tab checkbox.

        Args:
            checked: The desired checked state.

        Returns:
            ``None``.

        Side effects:
            Sets the checkbox state, which triggers the same toggled-handler the
            user click would trigger (potentially emitting
            ``render_tab_requested``).
        """
        self._render_checkbox.setChecked(checked)

    def set_path(self, path: str) -> None:
        """Set the current workbook path and emit ``file_selected``.

        This is the programmatic entry the file dialog uses; it is also callable
        directly in tests to drive selection without a real dialog.

        Args:
            path: The chosen workbook path.

        Returns:
            ``None``.

        Side effects:
            Updates the path field and emits ``file_selected``.
        """
        self._path = path
        self._path_edit.setText(path)
        self.file_selected.emit(path)

    def set_tab_list(self, tabs: list[str]) -> None:
        """Render the worksheet-tab names in the dropdown.

        Args:
            tabs: The worksheet-tab names to display.

        Returns:
            ``None``.

        Side effects:
            Replaces the dropdown items with ``tabs``.
        """
        self._tab_combo.clear()
        self._tab_combo.addItems(tabs)

    def set_schema_list(self, names: list[str]) -> None:
        """Populate the schema dropdown with the placeholder plus ``names`` (WS2).

        The ``<Choose Schema>`` placeholder is always the first item so the combo
        can return to "no schema selected"; the supplied schema names follow.

        Args:
            names: The schema names to offer, in display order.

        Returns:
            ``None``.

        Side effects:
            Replaces the dropdown items with the placeholder followed by
            ``names`` and leaves the placeholder selected.
        """
        apply_schema_list(self._schema_combo, _SCHEMA_PLACEHOLDER, names)

    def set_selected_schema(self, name: str) -> None:
        """Select a schema by name in the dropdown (WS2 auto-select).

        Args:
            name: The schema name to select. Appended to the dropdown when not
                already present so the selection always takes effect.

        Returns:
            ``None``.

        Side effects:
            Updates the dropdown selection, which emits ``schema_selected`` when
            the selected name is not the placeholder.
        """
        select_schema(self._schema_combo, name)

    def set_import_button_enabled(self, enabled: bool) -> None:
        """Toggle this tab's Import button enabled state (Decision 8).

        Args:
            enabled: ``True`` to enable Import, ``False`` to disable it; a no-op
                when the widget has no import button.

        Returns:
            ``None``.
        """
        set_import_enabled(self._import_button, enabled)

    def current_schema(self) -> str:
        """Return the currently selected schema name (the placeholder if none).

        Returns:
            The selected schema name, or ``"<Choose Schema>"`` when no schema is
            selected.
        """
        return self._schema_combo.currentText()

    def show_preview(self, rows: list[list[str]]) -> None:
        """No-op preview sink for protocol completeness.

        The preview is rendered by a separate :class:`PreviewWidget`; this widget
        forwards a render request via ``render_tab_requested`` and does not draw
        the grid itself. The method exists so the widget satisfies
        :class:`SourceSelectionViewProtocol`.

        Args:
            rows: The preview rows (ignored here; rendered by PreviewWidget).

        Returns:
            ``None``.
        """
        # The dedicated PreviewWidget renders the grid; this view only triggers
        # the request, so the preview payload is intentionally not drawn here.
        del rows

    def show_error(self, message: str) -> None:
        """Display an error message in the widget's error label.

        Args:
            message: The error text to display.

        Returns:
            ``None``.

        Side effects:
            Sets the error label text.
        """
        self._error_label.setText(message)

    def open_file_dialog(self) -> None:
        """Open the modal file dialog and apply the chosen path.

        This is the public entry point the browse button's ``clicked`` signal
        triggers; tests call it directly (with the dialog's static method
        patched) to exercise the handler deterministically.

        Returns:
            ``None``.

        Side effects:
            Opens a modal file dialog; on a non-empty selection sets the path
            (which emits ``file_selected``).
        """
        # QFileDialog returns (path, selected_filter); the filter element is not
        # used, so it is consumed into a throwaway name.
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Workbook", "", _EXCEL_FILTER
        )
        if path:
            self.set_path(path)

    def _on_render_toggled(self, checked: bool) -> None:
        """Emit a render-tab request when the checkbox is checked.

        Args:
            checked: The new checkbox state.

        Returns:
            ``None``.

        Side effects:
            Emits ``render_tab_requested`` with the current path and sheet when
            checked and both are present.
        """
        # Only request a preview when the box is checked and we have a file and a
        # selected tab; unchecking or missing selections do nothing.
        if checked and self._path and self.current_sheet():
            self.render_tab_requested.emit(self._path, self.current_sheet())

    def _on_tab_changed(self, sheet: str) -> None:
        """Re-request a preview when the user switches tabs with render on.

        Per AC-1 / spec section 1: while the render checkbox is checked and the
        widget has a valid path, switching the worksheet tab in the dropdown
        re-emits ``render_tab_requested`` so the preview reflects the new
        sheet.

        Args:
            sheet: The newly-selected worksheet name (may be empty when the
                dropdown is cleared, in which case the re-render is suppressed).

        Returns:
            ``None``.

        Side effects:
            Emits ``render_tab_requested`` with the current path and the new
            sheet when the checkbox is checked, the path is non-empty, and the
            sheet is non-empty.
        """
        # The uncheck-clears-preview path is wired at the composition root, not
        # here, so this slot only fires the positive-flow re-render request.
        if self._render_checkbox.isChecked() and self._path and sheet:
            self.render_tab_requested.emit(self._path, sheet)

    def _on_schema_changed(self, name: str) -> None:
        """Emit ``schema_selected`` when a real schema (not the placeholder) is picked.

        Per WS2: selecting the ``<Choose Schema>`` placeholder is the unselected
        state and must not emit a selection; only a real schema name is
        forwarded so downstream wiring acts on an actual choice.

        Args:
            name: The newly-selected dropdown text (the placeholder or a schema
                name).

        Returns:
            ``None``.

        Side effects:
            Self-gates the Import and Edit-Schema buttons (enable for a real
            schema, disable on the placeholder) and emits ``schema_selected``
            only for a real schema.
        """
        # Decision 8: a real schema selection enables Import; returning to the
        # placeholder (or empty) re-disables it. The widget self-gates so the
        # enable/disable state always tracks the dropdown, and only a genuine
        # choice propagates to the presenter/composition root. Issue #60 Defect 1:
        # the Edit Schema button tracks the same real-vs-placeholder gate as
        # Import so it is editable only for a real schema.
        is_real = is_real_schema(name, _SCHEMA_PLACEHOLDER)
        set_import_enabled(self._import_button, is_real)
        set_edit_enabled(self._edit_schema_button, is_real)
        if is_real:
            self.schema_selected.emit(name)
