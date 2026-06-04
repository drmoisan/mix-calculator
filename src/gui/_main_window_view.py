"""Adapter that bridges :class:`MainWindow` to the pipeline view protocol.

Purpose:
    Provide a thin adapter so the pipeline presenter can drive the main
    window's status bar and control-button enablement without depending
    on :class:`MainWindow` directly. Hosting the adapter in its own
    module keeps :mod:`src.gui.app` under the 500-line file-size cap.

Responsibilities:
    Implement the small set of view operations the pipeline presenter
    invokes:

    * ``set_running`` / ``show_result`` / ``show_error`` route to the
      main window's status bar.
    * ``set_import_button_enabled`` routes per-input button enablement
      and recomputes the Import-All disjunction.
    * ``set_run_button_enabled`` / ``set_save_button_enabled`` /
      ``set_export_button_enabled`` route to the corresponding control
      buttons on the main window.

Usage:
    Constructed by :func:`src.gui.app.build_application` and wrapped
    around the freshly-constructed :class:`MainWindow`. Tests
    construct it directly with a real main window when exercising the
    pipeline presenter against the adapter.

Side Effects:
    Mutates the wrapped :class:`MainWindow` only through its public
    setters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow

# Maximum status-bar summary length; the full diagnostic lives in the modal so
# the status bar stays a concise one-line summary (WS4).
_STATUS_SUMMARY_MAX = 120

# Dialog title used for the modal error surface (WS4).
_ERROR_DIALOG_TITLE = "Error"


class MainWindowPipelineView:
    """Thin adapter from :class:`MainWindow` to :class:`PipelineViewProtocol`.

    Purpose:
        Bridge the pipeline presenter's view contract onto the main window's
        status bar and result/error surfaces without modifying ``MainWindow``.

    Responsibilities:
        Implement ``set_running``/``show_result``/``show_error`` by routing to
        the main window's status bar.

    Attributes:
        _window: The wrapped main window.
    """

    def __init__(self, window: MainWindow) -> None:
        """Initialize the adapter with the main window it routes to."""
        self._window = window

    def set_running(self, is_running: bool) -> None:
        """Reflect the running flag in the main window's status bar."""
        self._window.set_status("Working..." if is_running else "")

    def show_result(self, summary: str) -> None:
        """Show a success summary in the main window's status bar."""
        self._window.set_status(summary)

    def show_error(self, message: str) -> None:
        """Surface an error through BOTH a modal dialog and a status summary (WS4).

        Per WS4 (issue #48): every import/run error is shown as a
        ``QMessageBox.critical`` modal carrying the full diagnostic AND a concise
        status-bar summary. This keeps the full detail readable while the status
        bar reflects the last failure at a glance.

        Args:
            message: The full human-readable error text.

        Returns:
            ``None``.

        Side effects:
            Shows a modal error dialog and writes a truncated summary to the
            main window's status bar.
        """
        # Drive the modal with the full diagnostic, then write a concise summary
        # to the status bar so both surfaces reflect the failure.
        self.show_dialog_error(_ERROR_DIALOG_TITLE, message)
        self._window.set_status(f"Error: {self._summarize(message)}")

    def show_dialog_error(self, title: str, message: str) -> None:
        """Show a modal error dialog carrying the full diagnostic (WS4).

        Args:
            title: The dialog title (a short failure category).
            message: The full human-readable diagnostic text.

        Returns:
            ``None``.

        Side effects:
            Shows a blocking ``QMessageBox.critical`` modal the user must
            acknowledge.
        """
        QMessageBox.critical(self._window, title, message)

    @staticmethod
    def _summarize(message: str) -> str:
        """Return a concise one-line status summary of an error message.

        Collapses the message to its first line and truncates it to
        :data:`_STATUS_SUMMARY_MAX` characters so the status bar stays a short
        summary; the full text remains in the modal.

        Args:
            message: The full error message.

        Returns:
            A single-line, length-bounded summary suitable for the status bar.
        """
        # Use only the first line so a multi-line diagnostic does not overflow
        # the status bar; the modal already carries the full text.
        first_line = message.splitlines()[0] if message else ""
        if len(first_line) > _STATUS_SUMMARY_MAX:
            return first_line[: _STATUS_SUMMARY_MAX - 1] + "…"
        return first_line

    def set_import_button_enabled(self, key: str, enabled: bool) -> None:
        """Route to the matching per-input import button and recompute Import-All.

        Args ``key`` is ``"LE"``, ``"aop"``, or ``"sku_lu"``; ``enabled`` is
        the new enabled state. Updates the keyed button and recomputes the
        Import-All button as the disjunction over the three per-input
        buttons (per spec section 2 / research Q3).
        """
        # Routing table for the three per-input import buttons. Import-All is
        # set to True iff any of the three per-input buttons is currently
        # enabled. An unknown key is a no-op so the adapter is permissive in
        # the same way the presenter's _import_one_frame KeyError boundary is.
        if key == "LE":
            self._window.import_le_btn.setEnabled(enabled)
        elif key == "aop":
            self._window.import_aop_btn.setEnabled(enabled)
        elif key == "sku_lu":
            self._window.import_skulu_btn.setEnabled(enabled)
        else:
            return
        any_enabled = (
            self._window.import_le_btn.isEnabled()
            or self._window.import_aop_btn.isEnabled()
            or self._window.import_skulu_btn.isEnabled()
        )
        self._window.import_all_btn.setEnabled(any_enabled)

    def set_run_button_enabled(self, enabled: bool) -> None:
        """Set the Run button's enabled state on the wrapped main window."""
        self._window.run_btn.setEnabled(enabled)

    def set_save_button_enabled(self, enabled: bool) -> None:
        """Set the Save button's enabled state on the wrapped main window."""
        self._window.save_btn.setEnabled(enabled)

    def set_export_button_enabled(self, enabled: bool) -> None:
        """Set the Export button's enabled state on the wrapped main window."""
        self._window.export_btn.setEnabled(enabled)
