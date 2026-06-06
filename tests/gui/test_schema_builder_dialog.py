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
    """Switching dedup to collapse carries an existing-column discriminator."""
    # Arrange: declare the discriminator column so it is a selectable dropdown
    # option (Decision 6: the discriminator must reference an existing column).
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)
    dialog.set_columns([("YTD/YTG", "discriminator", True, ())])

    # Act
    dialog.set_dedup("collapse", "YTD/YTG")

    # Assert
    assert dialog.get_dedup() == ("collapse", "YTD/YTG")


def test_dedup_discriminator_defaults_to_key(qtbot: QtBot) -> None:
    """The discriminator dropdown offers the Key sentinel as the default."""
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Act: with aggregate mode and no explicit discriminator, the Key is default.
    dialog.set_dedup("aggregate", None)

    # Assert: the Key sentinel is the resolved default discriminator.
    assert dialog.get_dedup() == ("aggregate", "Key")


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


def test_tab_order_matches_decision_10(qtbot: QtBot) -> None:
    """Decision 10: tabs are Identity, Derived, Columns, Key, Dedup, Preview."""
    # Arrange / Act
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Assert: the tab labels appear in the specified order.
    assert dialog.tab_labels() == [
        "Identity",
        "Derived",
        "Columns",
        "Key",
        "Dedup",
        "Preview",
    ]


def test_dedup_default_mode_is_aggregate(qtbot: QtBot) -> None:
    """Decision 1: a freshly-opened Dedup tab shows aggregate selected by default."""
    # Arrange / Act
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Assert: the dedup mode defaults to aggregate.
    mode, _discriminator = dialog.get_dedup()
    assert mode == "aggregate"


def test_dedup_discriminator_is_dropdown_of_existing_columns(qtbot: QtBot) -> None:
    """Decision 6: the discriminator dropdown contains only existing names + Key."""
    # Arrange: declare two columns and a derived column.
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)
    dialog.set_columns(
        [("Customer", "dimension", True, ()), ("Sales", "measure", True, ())]
    )
    dialog.set_derived([("Revenue", "Sales * 2")])

    # Act: repopulate the dropdown by setting dedup.
    dialog.set_dedup("aggregate", None)

    # Assert: the dropdown offers the Key plus the existing canonical/derived names.
    assert dialog.discriminator_options() == ["Key", "Customer", "Sales", "Revenue"]


def test_dedup_unknown_discriminator_is_rejected(qtbot: QtBot) -> None:
    """Decision 6: an unknown discriminator cannot be selected (no free-text)."""
    # Arrange: only one declared column.
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)
    dialog.set_columns([("Customer", "dimension", True, ())])

    # Act: attempt to set a discriminator that is not an existing column.
    dialog.set_dedup("aggregate", "Nonexistent")

    # Assert: the unknown value was not selected; the dropdown stays on a valid one.
    _mode, discriminator = dialog.get_dedup()
    assert discriminator != "Nonexistent"
    assert discriminator in ("Key", "Customer")
