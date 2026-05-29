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
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

__all__ = ["SourceInputWidget"]

# File dialog filter restricting selection to Excel workbooks.
_EXCEL_FILTER = "Excel Workbooks (*.xlsx)"


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
    """

    file_selected: Signal = Signal(str)
    render_tab_requested: Signal = Signal(str, str)

    def __init__(
        self,
        input_label: str,
        default_sheet: str = "",
        parent: QWidget | None = None,
    ) -> None:
        """Build the widget controls.

        Args:
            input_label: The input's display label (for example ``"LE"``).
            default_sheet: A default sheet name pre-filled in the tab dropdown.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self._path = ""

        # Build the controls: a labeled file row, the tab dropdown, the render
        # checkbox, and an error label.
        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        self._browse_button = QPushButton("Select File...")
        self._tab_combo = QComboBox()
        if default_sheet:
            self._tab_combo.addItem(default_sheet)
        self._render_checkbox = QCheckBox("Render tab")
        self._error_label = QLabel("")

        file_row = QHBoxLayout()
        file_row.addWidget(QLabel(input_label))
        file_row.addWidget(self._path_edit)
        file_row.addWidget(self._browse_button)

        layout = QVBoxLayout(self)
        layout.addLayout(file_row)
        layout.addWidget(self._tab_combo)
        layout.addWidget(self._render_checkbox)
        layout.addWidget(self._error_label)

        # Wire internal controls to the widget's signal-emitting handlers.
        self._browse_button.clicked.connect(self.open_file_dialog)
        self._render_checkbox.toggled.connect(self._on_render_toggled)
        # v2 (AC-1): when the user changes the worksheet tab while the render
        # checkbox is checked, re-request a preview for the new sheet.
        self._tab_combo.currentTextChanged.connect(self._on_tab_changed)

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
