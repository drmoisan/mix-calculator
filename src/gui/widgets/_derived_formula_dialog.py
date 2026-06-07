"""Sub-dialog for authoring one derived column (Decision 7).

This passive Qt dialog lets the user author a single derived column: it lists the
available column names (declared columns plus prior-derived columns), accepts a
name and an expression, and validates the expression live through the existing
Feature C :class:`~src.schema_formula.FormulaEvaluator` (no new engine). The dialog
holds no schema-assembly logic; it returns the authored ``(name, expression)`` pair
and surfaces validation errors inline.

Responsibilities:
    - List the available names a formula may reference.
    - Validate the current expression on demand, surfacing
      :class:`~src.schema_formula.FormulaError` inline and clearing it on success.
    - Expose the authored name and expression.

Scope boundaries:
    - View plus a thin call into the existing evaluator. No persistence, no schema
      assembly, no new dependency.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

from src.schema_formula import FormulaError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from src.schema_formula import FormulaEvaluator

__all__ = ["DerivedFormulaDialog"]


class DerivedFormulaDialog(QDialog):
    """Passive sub-dialog for authoring and validating one derived column.

    Purpose:
        Let the user name a derived column, enter an expression, see the available
        column names it may reference, and validate the expression live through the
        Feature C evaluator before accepting.

    Responsibilities:
        Render the available-name list and the name/expression inputs; validate the
        expression on demand and surface or clear an inline error; expose the
        authored name and expression. It performs no persistence and builds no
        schema.

    Usage:
        Construct with the available names and an optional evaluator (a default is
        created when none is injected). Call :meth:`validate_current` to validate;
        read :meth:`derived_name`/:meth:`derived_expression` on accept.

    Attributes:
        _available: The column names a formula may reference.
        _evaluator: The Feature C evaluator used for validation.
    """

    def __init__(
        self,
        available_names: Sequence[str],
        *,
        formula_evaluator: FormulaEvaluator | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Build the dialog and populate the available-name list.

        Args:
            available_names: The column names (declared + prior-derived) a formula
                may reference, in display order.
            formula_evaluator: The evaluator used for live validation. When
                ``None``, a default
                :class:`~src.schema_formula.FormulaEvaluator` is created.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Add Derived Column")
        self._available = list(available_names)
        # Create a default evaluator lazily so callers that inject one avoid the
        # import at construction; reuse the existing engine (no new engine).
        if formula_evaluator is None:
            from src.schema_formula import FormulaEvaluator as _FormulaEvaluator

            formula_evaluator = _FormulaEvaluator()
        self._evaluator = formula_evaluator

        # Available-name list so the user sees what the expression may reference,
        # including columns derived earlier in the schema.
        self._names_list = QListWidget()
        self._names_list.addItems(self._available)
        self._name_input = QLineEdit()
        self._expression_input = QLineEdit()
        self._error_label = QLabel("")

        form = QFormLayout()
        form.addRow("Name", self._name_input)
        form.addRow("Expression", self._expression_input)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Available columns:"))
        layout.addWidget(self._names_list)
        layout.addLayout(form)
        layout.addWidget(self._error_label)
        layout.addWidget(self._buttons)

        # Validate live as the user edits the expression so the error surface
        # tracks the current text without an explicit button.
        self._expression_input.textChanged.connect(self._on_expression_changed)

    def available_names(self) -> list[str]:
        """Return the available column names offered to the formula.

        Returns:
            The available names in display order (test/inspection seam).
        """
        return list(self._available)

    def derived_name(self) -> str:
        """Return the authored derived-column name.

        Returns:
            The trimmed name input text.
        """
        return self._name_input.text().strip()

    def derived_expression(self) -> str:
        """Return the authored expression.

        Returns:
            The trimmed expression input text.
        """
        return self._expression_input.text().strip()

    def set_name(self, name: str) -> None:
        """Set the derived-column name (test/programmatic seam).

        Args:
            name: The name to place in the name input.

        Returns:
            ``None``.

        Side effects:
            Updates the name input.
        """
        self._name_input.setText(name)

    def set_expression(self, expression: str) -> None:
        """Set the expression text (test/programmatic seam).

        Args:
            expression: The expression to place in the input, which triggers live
                validation.

        Returns:
            ``None``.

        Side effects:
            Updates the expression input (firing live validation).
        """
        self._expression_input.setText(expression)

    def error_text(self) -> str:
        """Return the current inline error text.

        Returns:
            The error label text (empty when the expression is valid).
        """
        return self._error_label.text()

    def validate_current(self) -> bool:
        """Validate the current expression against the available names.

        Validates through the Feature C evaluator. On a
        :class:`~src.schema_formula.FormulaError` the descriptive message is shown
        inline and ``False`` is returned; on success the inline error is cleared
        and ``True`` is returned.

        Returns:
            ``True`` when the expression is valid; ``False`` otherwise.

        Side effects:
            Updates the inline error label.
        """
        expression = self.derived_expression()
        # An empty expression is not validated as an error here; the empty error
        # surface reflects "nothing to validate yet".
        if not expression:
            self._error_label.setText("")
            return False
        # FormulaError carries a descriptive message in args[0]; surface exactly
        # that text so the operator sees the construct/column at fault.
        try:
            self._evaluator.validate(expression, self._available)
        except FormulaError as error:
            message = str(error.args[0]) if error.args else str(error)
            self._error_label.setText(message)
            return False
        self._error_label.setText("")
        return True

    def _on_expression_changed(self, _text: str) -> None:
        """Re-validate live when the expression text changes.

        Args:
            _text: The new expression text (read via the input, not the argument).

        Returns:
            ``None``.

        Side effects:
            Runs :meth:`validate_current`, updating the inline error.
        """
        self.validate_current()
