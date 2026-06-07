"""Qt tests for :mod:`src.gui.widgets.schema_builder_dialog`.

Runs under ``QT_QPA_PLATFORM=offscreen`` (pinned by the GUI conftest). Verifies
each tab renders the pushed state and reports edits back through the protocol
getters: identity round-trip, a column-row round-trip, key selection, dedup mode
switch with discriminator, derived/formula entry with the inline error surface,
and ``show_preview`` rendering. Fabricated data only; no temp files or network.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.widgets._columns_tab_drag import ColumnsTabWidget
from src.gui.widgets._dtype_check_widget import DtypeCheckWidget
from src.gui.widgets._key_tab_drag import GenericTextToken, KeyTabWidget
from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog

if TYPE_CHECKING:
    import pytest
    from pytestqt.qtbot import QtBot

    from src.gui.widgets._derived_formula_dialog import DerivedFormulaDialog


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
        ("Customer", "dimension", True, True, ("Cust",)),
        ("Sales", "measure", False, True, ()),
    ]

    # Act
    dialog.set_columns(rows)

    # Assert: both rows, with role/required/in_output/aliases, survive the round-trip.
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
    dialog.set_columns([("YTD/YTG", "discriminator", False, False, ())])

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
        [
            ("Customer", "dimension", True, True, ()),
            ("Sales", "measure", True, True, ()),
        ]
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
    dialog.set_columns([("Customer", "dimension", True, True, ())])

    # Act: attempt to set a discriminator that is not an existing column.
    dialog.set_dedup("aggregate", "Nonexistent")

    # Assert: the unknown value was not selected; the dropdown stays on a valid one.
    _mode, discriminator = dialog.get_dedup()
    assert discriminator != "Nonexistent"
    assert discriminator in ("Key", "Customer")


def test_live_columns_tab_has_drag_tokens_and_dtype_indicators(qtbot: QtBot) -> None:
    """R1: the live dialog opened via the production path renders the drag Columns tab.

    Drives the production ``open_schema_builder`` path (real dialog + real presenter)
    seeded with required specs (carrying expected dtypes) and a masked preview slice,
    then asserts the live Columns tab is a ``ColumnsTabWidget`` with draggable
    source-column tokens and at least one rendered dtype indicator — not the removed
    plain-text editor.
    """
    # Arrange: a real shell, a fake schema service, and a masked preview slice whose
    # header columns become the draggable source-token pool. One column coerces to
    # its expected dtype (green) and one does not (red), so an indicator renders.
    from src.gui._schema_wiring import open_schema_builder
    from src.gui.main_window import MainWindow
    from src.gui.presenters._schema_builder_state import PreviewSlice
    from src.schema_model import ColumnSpec
    from tests.gui.fakes.fake_services import FakeSchemaService

    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    # The header carries an extra unmatched source column ("Region") so the
    # draggable pool still holds a token after the matched columns are consumed.
    preview = PreviewSlice(
        header=("Customer", "Sales", "Region"),
        rows=(
            ("Cust-0001", "not-a-number", "Reg-A"),
            ("Cust-0002", "also-text", "Reg-B"),
        ),
    )
    required = (
        ColumnSpec(
            canonical_name="Customer", role="dimension", expected_dtype="string"
        ),
        ColumnSpec(canonical_name="Sales", role="measure", expected_dtype="integer"),
    )
    captured: list[SchemaBuilderDialog] = []

    def dialog_factory() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        captured.append(dialog)
        return dialog

    # Act: open the builder through the production open path with seed inputs.
    open_schema_builder(
        window,
        service,
        dialog_factory=dialog_factory,
        required_specs=required,
        default_key_pattern="{Customer}",
        preview_slice=preview,
    )

    # Assert: the live Columns tab is the drag widget, not the plain-text editor.
    assert len(captured) == 1
    dialog = captured[0]
    columns_widget = dialog.findChild(ColumnsTabWidget)
    assert columns_widget is not None
    # The draggable source-token pool reflects the seeded masked preview header.
    assert columns_widget.token_names() != []
    # Both seeded canonical rows are rendered on the live tab.
    assert "Customer" in columns_widget.row_canonicals()
    assert "Sales" in columns_widget.row_canonicals()
    # Each canonical row renders its expected dtype label (P1-T4).
    assert "integer" in columns_widget.row_label_text("Sales")
    # At least one matched row shows a populated dtype-check indicator (P1-T5): Sales
    # is integer but the masked values are text, so a red non-coercible indicator
    # with a masked failing example renders.
    indicators = columns_widget.findChildren(DtypeCheckWidget)
    assert any(indicator.text() != "" for indicator in indicators)


def test_live_key_tab_has_drag_widget_with_seeded_parts(qtbot: QtBot) -> None:
    """R2: the live dialog opened via the production path renders the drag Key tab.

    Drives the production ``open_schema_builder`` path (real dialog + real presenter)
    seeded with a default key pattern, then asserts the live Key tab is a
    ``KeyTabWidget`` carrying the rendered structured parts and a placeable Generic
    Text token — not the removed comma-separated ``QLineEdit`` editor.
    """
    # Arrange: a real shell, a fake service, and seed inputs including a default key
    # pattern with a literal separator so the structured parts interleave a literal.
    from src.gui._schema_wiring import open_schema_builder
    from src.gui.main_window import MainWindow
    from src.gui.presenters._schema_builder_state import PreviewSlice
    from src.schema_model import ColumnSpec
    from tests.gui.fakes.fake_services import FakeSchemaService

    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    preview = PreviewSlice(header=("Customer", "SKU #"), rows=(("Cust-1", "SKU-1"),))
    required = (
        ColumnSpec(canonical_name="Customer", role="dimension"),
        ColumnSpec(canonical_name="SKU #", role="dimension"),
    )
    captured: list[SchemaBuilderDialog] = []

    def dialog_factory() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        captured.append(dialog)
        return dialog

    # Act: open the builder through the production open path with a default pattern.
    open_schema_builder(
        window,
        service,
        dialog_factory=dialog_factory,
        required_specs=required,
        default_key_pattern="{Customer}-{SKU #}",
        preview_slice=preview,
    )

    # Assert: the live Key tab is the drag widget, not the QLineEdit editor.
    assert len(captured) == 1
    dialog = captured[0]
    key_widget = dialog.findChild(KeyTabWidget)
    assert key_widget is not None
    # The seeded default pattern is rendered as ordered structured parts including
    # the literal separator between the two column-refs.
    parts = key_widget.parts_text()
    assert "Customer" in parts
    assert "SKU #" in parts
    assert parts.index("Customer") < parts.index("SKU #")
    # The repeatable Generic Text affordance is present on the live tab.
    assert key_widget.findChild(GenericTextToken) is not None
    # The column-token pool reflects the seeded preview-slice header columns (P2-T4).
    assert key_widget.column_token_names() == ["Customer", "SKU #"]


def test_live_derived_button_adds_column_to_columns_tab(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R3: the live Derived button opens the formula dialog and adds a column.

    Drives the production ``open_schema_builder`` path (real dialog + real presenter)
    seeded with a column, triggers the Derived-tab "New derived column" button — which
    opens a real ``DerivedFormulaDialog`` — accepts a valid derived column, and
    asserts the accepted column surfaces on the live drag Columns tab. The modal
    ``exec`` is stubbed to fill the inputs and accept, since offscreen tests cannot
    drive a real modal loop.
    """
    # Arrange: a real shell/service seeded with one column the formula references.
    from PySide6.QtWidgets import QPushButton

    from src.gui._schema_wiring import open_schema_builder
    from src.gui.main_window import MainWindow
    from src.gui.widgets import _derived_formula_dialog as derived_mod
    from src.schema_model import ColumnSpec
    from tests.gui.fakes.fake_services import FakeSchemaService

    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    required = (ColumnSpec(canonical_name="Sales", role="measure"),)
    captured: list[SchemaBuilderDialog] = []
    opened_dialogs: list[DerivedFormulaDialog] = []

    def dialog_factory() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        captured.append(dialog)
        return dialog

    # Stub the modal exec so the derived dialog fills its inputs and "accepts"
    # without entering a real event loop (offscreen cannot run a modal).
    def _fake_exec(self: DerivedFormulaDialog) -> int:
        opened_dialogs.append(self)
        self.set_name("Revenue")
        self.set_expression("Sales * 2")
        return 1

    monkeypatch.setattr(derived_mod.DerivedFormulaDialog, "exec", _fake_exec)

    open_schema_builder(
        window,
        service,
        dialog_factory=dialog_factory,
        required_specs=required,
    )
    assert len(captured) == 1
    dialog = captured[0]

    # Act: click the live Derived-tab "New derived column" button to drive the
    # production handler installed by open_schema_builder. Locate it by its label so
    # the test does not reach into the dialog's private controls.
    new_buttons = [
        button
        for button in dialog.findChildren(QPushButton)
        if button.text() == "New derived column"
    ]
    assert len(new_buttons) == 1
    new_buttons[0].click()

    # Assert: the real DerivedFormulaDialog opened and offered the prior column, and
    # the accepted derived column now appears on the live drag Columns tab.
    assert len(opened_dialogs) == 1
    assert "Sales" in opened_dialogs[0].available_names()
    columns_widget = dialog.findChild(ColumnsTabWidget)
    assert columns_widget is not None
    assert "Revenue" in columns_widget.row_canonicals()
