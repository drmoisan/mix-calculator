"""Passive dtype-check indicator widget (Decision 4).

This widget renders the result of the pure dtype check as a passive indicator: a
green check when the matched source values coerce to the column's expected type, or
a red X with a concrete failing example when they do not. It holds no logic; the
:class:`~src.gui.presenters._columns_tab_presenter.ColumnsTabPresenter` computes the
state (via :mod:`src.dtype_check`) and pushes it here. Every displayed example value
is already masked by the caller; the widget displays it verbatim.

Responsibilities:
    - ``DtypeCheckWidget.set_state``: render coercible (green check) or
      not-coercible (red X plus the masked failing example).

Scope boundaries:
    - View only. No coercion logic, no I/O. The example text is masked upstream.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget

__all__ = ["DtypeCheckWidget"]

# Glyphs for the coercible/non-coercible states. Plain text keeps the widget
# font-agnostic.
_OK_GLYPH = "✓"  # check mark
_BAD_GLYPH = "✗"  # ballot X


class DtypeCheckWidget(QWidget):
    """A passive green-check / red-X dtype indicator with a failing example.

    Purpose:
        Show whether a matched source column coerces to its expected data type,
        driven entirely by presenter-pushed state.

    Responsibilities:
        Render a green check for the coercible state and a red X plus a masked
        failing example for the non-coercible state. It computes nothing.

    Usage:
        Construct it inside a Columns-tab row; call :meth:`set_state` whenever the
        presenter recomputes the dtype check.

    Attributes:
        _label: The single label carrying the glyph and any failing example.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the indicator in a neutral (empty) state.

        Args:
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        from PySide6.QtWidgets import QHBoxLayout

        self._label = QLabel("")
        layout = QHBoxLayout(self)
        layout.addWidget(self._label)

    def set_state(self, coercible: bool, failing_example: str | None) -> None:
        """Render the dtype-check state.

        Args:
            coercible: ``True`` to show the green check; ``False`` to show the red
                X with the failing example.
            failing_example: The masked example value that failed to coerce, shown
                only when ``coercible`` is ``False``. Ignored when coercible.

        Returns:
            ``None``.

        Side effects:
            Updates the indicator label's text and color.
        """
        # The coercible state shows only the green check; the non-coercible state
        # shows the red X plus the (already-masked) failing example so the user
        # sees a concrete value that cannot convert.
        if coercible:
            self._label.setText(_OK_GLYPH)
            self._label.setStyleSheet("color: green;")
            return
        example = failing_example if failing_example is not None else ""
        self._label.setText(f"{_BAD_GLYPH} {example}".strip())
        self._label.setStyleSheet("color: red;")

    def set_value_display(self, value: str) -> None:
        """Render a chosen source value in place of the dtype glyph (AC-6).

        Switches the indicator from dtype-glyph mode to value-display mode: the
        already-masked source cell value for the chosen preview row is shown to the
        right of the blue assignment object instead of the green check / red X. The
        value arrives pre-masked from ``PreviewSlice.rows``; the widget displays it
        verbatim.

        Args:
            value: The already-masked source cell value to display.

        Returns:
            ``None``.

        Side effects:
            Updates the indicator label's text and resets its color to neutral so
            the value reads as data rather than a pass/fail signal.
        """
        self._label.setText(value)
        # Neutral color: the value is data, not a coercion pass/fail signal.
        self._label.setStyleSheet("")

    def text(self) -> str:
        """Return the indicator's current text (test/inspection seam).

        Returns:
            The label text, including the glyph and any failing example.
        """
        return self._label.text()
