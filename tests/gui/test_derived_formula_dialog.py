"""Qt offscreen tests for the derived-column sub-dialog (Decision 7).

These tests run headless under ``QT_QPA_PLATFORM=offscreen``. They verify the
dialog lists the available names (declared + prior-derived), accepts a name and
expression, and validates the expression live through the Feature C evaluator:
an invalid expression surfaces a FormulaError message and a valid one clears it.
All fixture values are synthetic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.widgets._derived_formula_dialog import DerivedFormulaDialog

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_dialog_lists_available_names_and_accepts_expression(qtbot: QtBot) -> None:
    """The dialog lists the available names and accepts a name + expression."""
    # Arrange: declared columns plus a prior-derived name in the available set.
    dialog = DerivedFormulaDialog(["Sales", "Units", "PriorDerived"])
    qtbot.addWidget(dialog)

    # Assert: the available names include the prior-derived column.
    assert "PriorDerived" in dialog.available_names()

    # Act: author a name and a valid expression.
    dialog.set_name("Revenue")
    dialog.set_expression("Sales * Units")

    # Assert: the authored values are exposed.
    assert dialog.derived_name() == "Revenue"
    assert dialog.derived_expression() == "Sales * Units"


def test_dialog_surfaces_formula_error_for_invalid_expression(qtbot: QtBot) -> None:
    """An invalid expression surfaces a FormulaError message inline."""
    # Arrange
    dialog = DerivedFormulaDialog(["Sales"])
    qtbot.addWidget(dialog)

    # Act: an unknown-column reference is invalid.
    dialog.set_expression("Unknown_Column + 1")
    valid = dialog.validate_current()

    # Assert: invalid with a descriptive inline message.
    assert valid is False
    assert dialog.error_text() != ""


def test_dialog_clears_error_for_valid_expression(qtbot: QtBot) -> None:
    """A valid expression clears the inline error."""
    # Arrange: start from an invalid expression that sets the error.
    dialog = DerivedFormulaDialog(["Sales"])
    qtbot.addWidget(dialog)
    dialog.set_expression("Unknown_Column + 1")
    assert dialog.error_text() != ""

    # Act: replace with a valid expression.
    dialog.set_expression("Sales * 2")
    valid = dialog.validate_current()

    # Assert: valid and the error is cleared.
    assert valid is True
    assert dialog.error_text() == ""
