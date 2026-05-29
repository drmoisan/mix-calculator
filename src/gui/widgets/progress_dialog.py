"""Indeterminate progress dialog with a cancel control.

This passive Qt dialog is shown while a worker job is in flight. It carries an
indeterminate progress indicator (busy bar) and a cancel button. It holds no
logic beyond view state; the composition root wires its ``rejected`` signal to
the worker-cancellation path.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

__all__ = ["ProgressDialog"]


class ProgressDialog(QDialog):
    """Indeterminate-busy dialog with a cancel button.

    Purpose:
        Show that a long-running job (an import or pipeline run) is in flight
        and offer the user a cancel.

    Responsibilities:
        Render a status label, an indeterminate progress bar, and a cancel
        button. It owns no logic; cancellation routing is the caller's job.

    Usage:
        Constructed by the composition root; ``set_message`` updates the label,
        ``rejected`` fires on cancel.

    Attributes:
        _label: The status label.
        _bar: The indeterminate progress bar.
        _buttons: The cancel button container.
    """

    def __init__(
        self,
        message: str = "Working...",
        parent: QWidget | None = None,
    ) -> None:
        """Build the dialog controls.

        Args:
            message: Initial status message.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Pipeline")

        self._label = QLabel(message)
        self._bar = QProgressBar()
        # An indeterminate bar uses range (0, 0); it animates without a value.
        self._bar.setRange(0, 0)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)

        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        layout.addWidget(self._bar)
        layout.addWidget(self._buttons)

        # Cancel routes through the standard reject path so callers can connect
        # to the dialog's rejected signal.
        self._buttons.rejected.connect(self.reject)

    def set_message(self, message: str) -> None:
        """Update the status label.

        Args:
            message: The new status text.

        Returns:
            ``None``.

        Side effects:
            Sets the label text.
        """
        self._label.setText(message)

    def message(self) -> str:
        """Return the current status label text."""
        return self._label.text()
