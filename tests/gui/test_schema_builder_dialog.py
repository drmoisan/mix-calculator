"""Qt tests for :mod:`src.gui.widgets.schema_builder_dialog`.

Runs under ``QT_QPA_PLATFORM=offscreen`` (pinned by the GUI conftest). Verifies
each tab renders the pushed state and reports edits back through the protocol
getters: identity round-trip, a column-row round-trip, key selection, dedup mode
switch with discriminator, derived/formula entry with the inline error surface,
and ``show_preview`` rendering. Fabricated data only; no temp files or network.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_identity_round_trip(qtbot: QtBot) -> None:
    """set_identity then get_identity round-trips the identity fields."""
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.set_identity("aop", "1.0", "AOP schema")

    # Assert
    assert dialog.get_identity() == ("aop", "1.0", "AOP schema")


def test_column_row_round_trip(qtbot: QtBot) -> None:
    """A column row round-trips through set_columns/get_columns."""
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)
    rows = [
        ("Customer", "dimension", True, ("Cust",)),
        ("Sales", "measure", False, ()),
    ]

    # Act
    dialog.set_columns(rows)

    # Assert: both rows, with role/required/aliases, survive the round-trip.
    assert dialog.get_columns() == rows


def test_key_selection_round_trip(qtbot: QtBot) -> None:
    """The key columns and SKU coercion round-trip."""
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.set_key(("Customer", "SKU #"), sku_coercion=True)

    # Assert
    assert dialog.get_key() == (("Customer", "SKU #"), True)


def test_dedup_mode_switch_reveals_discriminator(qtbot: QtBot) -> None:
    """Switching dedup to collapse carries the discriminator through the getter."""
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.set_dedup("collapse", "YTD/YTG")

    # Assert
    assert dialog.get_dedup() == ("collapse", "YTD/YTG")


def test_dedup_none_yields_no_discriminator(qtbot: QtBot) -> None:
    """A blank discriminator reads back as None."""
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.set_dedup("none", None)

    # Assert
    assert dialog.get_dedup() == ("none", None)


def test_derived_entry_round_trip(qtbot: QtBot) -> None:
    """A derived/formula row round-trips through set_derived/get_derived."""
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.set_derived([("YTG", "FY - YTD")])

    # Assert
    assert dialog.get_derived() == [("YTG", "FY - YTD")]


def test_formula_error_surface_and_clear(qtbot: QtBot) -> None:
    """show_formula_error sets the inline label; clear_formula_error resets it."""
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Act / Assert: error is rendered, then cleared.
    dialog.show_formula_error("unknown column 'X'")
    assert dialog.formula_error_text() == "unknown column 'X'"
    dialog.clear_formula_error()
    assert dialog.formula_error_text() == ""


def test_show_preview_renders_rows(qtbot: QtBot) -> None:
    """show_preview renders the preview rows on the Preview tab."""
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.show_preview([["A", "10"], ["B", "20"]])

    # Assert: both rows are present in the rendered preview text.
    text = dialog.preview_text()
    assert "A" in text
    assert "20" in text


def test_show_error_renders_on_error_surface(qtbot: QtBot) -> None:
    """show_error renders a general error on the inline error surface."""
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.show_error("name must be non-empty")

    # Assert
    assert dialog.formula_error_text() == "name must be non-empty"
