"""Qt tests for :mod:`src.gui.widgets.column_matching_dialog`.

Runs under ``QT_QPA_PLATFORM=offscreen`` (pinned by the GUI conftest). Verifies
that the dialog renders the unmatched-required and source lists, shows fuzzy
suggestions with scores, gates the Ignore control to optional columns, reports
assignments through ``get_assignments``, and reflects the accept-and-save
checkbox. Fabricated data only; no temp files or network.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.widgets.column_matching_dialog import ColumnMatchingDialog

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_renders_unmatched_and_source_lists(qtbot: QtBot) -> None:
    """The dialog renders the unmatched-required and source-column lists."""
    # Arrange
    dialog = ColumnMatchingDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.set_unmatched_required([("Sales", ("Revenue",))])
    dialog.set_source_columns(["Customer", "Net Sales"])

    # Assert: one unmatched row (with aliases) and two source rows are rendered.
    unmatched = dialog.unmatched_texts()
    assert len(unmatched) == 1
    assert "Sales" in unmatched[0]
    assert "Revenue" in unmatched[0]
    assert len(dialog.source_texts()) == 2


def test_shows_fuzzy_suggestions_with_scores(qtbot: QtBot) -> None:
    """The dialog renders fuzzy suggestions including the numeric score."""
    # Arrange
    dialog = ColumnMatchingDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.set_fuzzy_suggestions({"Sales": [("Net Sales", 0.62)]})

    # Assert: the suggestion text names the candidate and its two-decimal score.
    text = dialog.suggestions_text()
    assert "Net Sales" in text
    assert "0.62" in text


def test_ignore_control_gated_to_optional_columns(qtbot: QtBot) -> None:
    """is_ignorable is True only for columns marked optional."""
    # Arrange
    dialog = ColumnMatchingDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.set_optional_required({"Notes"})

    # Assert: optional column is ignorable; a required one is not.
    assert dialog.is_ignorable("Notes") is True
    assert dialog.is_ignorable("Sales") is False


def test_reports_assignments(qtbot: QtBot) -> None:
    """get_assignments returns assignments recorded via the assign seam."""
    # Arrange
    dialog = ColumnMatchingDialog()
    qtbot.addWidget(dialog)
    dialog.set_unmatched_required([("Sales", ())])
    dialog.set_source_columns(["Customer", "Net Sales"])

    # Act
    dialog.assign("Sales", "Net Sales")

    # Assert
    assert dialog.get_assignments() == {"Sales": "Net Sales"}


def test_reflects_accept_and_save_checkbox(qtbot: QtBot) -> None:
    """The accept-and-save checkbox state is readable."""
    # Arrange
    dialog = ColumnMatchingDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.set_accept_and_save(True)

    # Assert
    assert dialog.is_accept_and_save_checked() is True


def test_mark_ignored_clears_prior_assignment(qtbot: QtBot) -> None:
    """mark_ignored removes a prior assignment for the same column."""
    # Arrange
    dialog = ColumnMatchingDialog()
    qtbot.addWidget(dialog)
    dialog.set_unmatched_required([("Notes", ())])
    dialog.assign("Notes", "Comment")

    # Act
    dialog.mark_ignored("Notes")

    # Assert: the assignment was cleared by the ignore.
    assert dialog.get_assignments() == {}


def test_show_error_renders_message(qtbot: QtBot) -> None:
    """show_error displays the message on the error surface."""
    # Arrange
    dialog = ColumnMatchingDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.show_error("Assignment is incomplete.")

    # Assert
    assert dialog.error_text() == "Assignment is incomplete."
