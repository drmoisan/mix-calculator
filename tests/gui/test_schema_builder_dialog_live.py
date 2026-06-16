"""Production-path (live) Qt tests for the schema-builder dialog.

Runs under ``QT_QPA_PLATFORM=offscreen`` (pinned by the GUI conftest). These
tests drive the production ``open_schema_builder`` path (real dialog + real
presenter) and assert the live Columns, Key, and Derived tabs render the
redesigned controls — the drag Columns tab, the Key multi-select (D-2), and the
"New derived column" flow. Split from ``test_schema_builder_dialog.py`` to keep
each test file under the repository's 500-line cap. Fabricated/masked data only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.widgets._columns_tab_drag import ColumnsTabWidget
from src.gui.widgets._dtype_check_widget import DtypeCheckWidget
from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog

if TYPE_CHECKING:
    import pytest
    from pytestqt.qtbot import QtBot

    from src.gui.widgets._derived_formula_dialog import DerivedFormulaDialog


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


def test_live_key_tab_is_multiselect_with_seeded_selection(qtbot: QtBot) -> None:
    """AC-7/D-2: the live dialog renders the Key tab as a multi-select.

    Drives the production ``open_schema_builder`` path (real dialog + real presenter)
    seeded with a default key pattern, then asserts the live Key tab is a
    ``KeyMultiSelectWidget`` whose ordered selection reflects the seeded
    column-ref parts — not the removed drag-and-drop / Generic Text token UI.
    """
    # Arrange: a real shell, a fake service, and seed inputs including a default key
    # pattern naming the two key columns in order.
    from src.gui._schema_wiring import open_schema_builder
    from src.gui.main_window import MainWindow
    from src.gui.presenters._schema_builder_state import PreviewSlice
    from src.gui.widgets._key_multiselect_widget import KeyMultiSelectWidget
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

    # Assert: the live Key tab is the multi-select, not the removed drag UI.
    assert len(captured) == 1
    dialog = captured[0]
    key_widget = dialog.findChild(KeyMultiSelectWidget)
    assert key_widget is not None
    # The seeded default pattern's column-refs are selected in order; the literal
    # separator between them is not a selectable column (D-2).
    assert key_widget.selected_columns() == ["Customer", "SKU #"]
    # The dialog's get_key reports the ordered selection composing the key.
    columns, _sku = dialog.get_key()
    assert columns == ("Customer", "SKU #")


def test_live_preview_tab_renders_table_from_masked_slice(qtbot: QtBot) -> None:
    """AC-9: navigating to the Preview tab renders the result table (wired path).

    Drives the production ``open_schema_builder`` path, then switches the real
    ``QTabWidget`` to the Preview tab so the production ``currentChanged`` seam
    fires ``presenter.update_preview`` with the masked slice rows. Asserts the
    Preview ``QTableWidget`` is populated from the masked values — without calling
    ``update_preview`` directly and without a synthetic alias path.
    """
    # Arrange: a real shell/service and a masked preview slice whose dimension
    # columns the schema declares so the applied loader produces a result table.
    from PySide6.QtWidgets import QTableWidget, QTabWidget

    from src.gui._schema_wiring import open_schema_builder
    from src.gui.main_window import MainWindow
    from src.gui.presenters._schema_builder_state import PreviewSlice
    from src.schema_model import ColumnSpec
    from tests.gui.fakes.fake_services import FakeSchemaService

    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    preview = PreviewSlice(
        header=("Customer", "SKU #", "Type"),
        rows=(
            ("CUST_AAA", "SKU-1", "T1"),
            ("CUST_BBB", "SKU-2", "T2"),
        ),
    )
    required = (
        ColumnSpec(canonical_name="Customer", role="dimension"),
        ColumnSpec(canonical_name="SKU #", role="dimension"),
        ColumnSpec(canonical_name="Type", role="dimension"),
    )
    captured: list[SchemaBuilderDialog] = []

    def dialog_factory() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        captured.append(dialog)
        return dialog

    open_schema_builder(
        window,
        service,
        dialog_factory=dialog_factory,
        required_specs=required,
        default_key_pattern="{Customer}",
        preview_slice=preview,
    )
    assert len(captured) == 1
    dialog = captured[0]
    # Provide a non-empty identity so the schema assembles (assembly is part of the
    # wired update_preview path the user would complete before previewing).
    dialog.set_identity("aop", "1.0", "")

    # Act: switch the real tab widget to the Preview tab so the production
    # currentChanged seam fires update_preview (the wired path, not a direct call).
    tab_widget = dialog.findChild(QTabWidget)
    assert tab_widget is not None
    preview_index = dialog.tab_labels().index("Preview")
    tab_widget.setCurrentIndex(preview_index)

    # Assert: the Preview table is populated from the masked slice values, and the
    # old label path is gone (a QTableWidget exists and carries the masked data).
    table = dialog.findChild(QTableWidget)
    assert table is not None
    rendered = dialog.preview_text()
    assert "CUST_AAA" in rendered
    assert "CUST_BBB" in rendered


def test_live_preview_shows_no_source_message_for_blank_slice(qtbot: QtBot) -> None:
    """AC-10: the Preview tab shows a specific message when no source data exists.

    Opens the blank menu path (no preview slice), navigates to the Preview tab via
    the production seam, and asserts the specific "no source data" message renders
    rather than an empty table.
    """
    # Arrange: open the builder with no caller specs and no preview slice.
    from PySide6.QtWidgets import QTabWidget

    from src.gui._schema_wiring import open_schema_builder
    from src.gui.main_window import MainWindow
    from tests.gui.fakes.fake_services import FakeSchemaService

    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    captured: list[SchemaBuilderDialog] = []

    def dialog_factory() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        captured.append(dialog)
        return dialog

    open_schema_builder(window, service, dialog_factory=dialog_factory)
    assert len(captured) == 1
    dialog = captured[0]

    # Act: navigate to the Preview tab so the wired seam fires.
    tab_widget = dialog.findChild(QTabWidget)
    assert tab_widget is not None
    tab_widget.setCurrentIndex(dialog.tab_labels().index("Preview"))

    # Assert: the specific no-source message renders, not an empty table.
    assert dialog.preview_message() == "No source data available to preview"


def test_live_preview_shows_specific_missing_input_message(qtbot: QtBot) -> None:
    """AC-10: a missing required input surfaces a specific assembly-failure message.

    Opens with a masked slice but leaves the identity name blank, navigates to the
    Preview tab via the production seam, and asserts the specific
    ``SchemaValidationError`` message (empty name) renders rather than nothing.
    """
    # Arrange
    from PySide6.QtWidgets import QTabWidget

    from src.gui._schema_wiring import open_schema_builder
    from src.gui.main_window import MainWindow
    from src.gui.presenters._schema_builder_state import PreviewSlice
    from src.schema_model import ColumnSpec
    from tests.gui.fakes.fake_services import FakeSchemaService

    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    preview = PreviewSlice(
        header=("Customer", "SKU #", "Type"),
        rows=(("CUST_AAA", "SKU-1", "T1"),),
    )
    required = (
        ColumnSpec(canonical_name="Customer", role="dimension"),
        ColumnSpec(canonical_name="SKU #", role="dimension"),
        ColumnSpec(canonical_name="Type", role="dimension"),
    )
    captured: list[SchemaBuilderDialog] = []

    def dialog_factory() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        captured.append(dialog)
        return dialog

    open_schema_builder(
        window,
        service,
        dialog_factory=dialog_factory,
        required_specs=required,
        default_key_pattern="{Customer}",
        preview_slice=preview,
    )
    dialog = captured[0]
    # Leave the identity name blank so assembly fails with a specific message.
    dialog.set_identity("", "1.0", "")

    # Act: navigate to the Preview tab so the wired seam fires update_preview.
    tab_widget = dialog.findChild(QTabWidget)
    assert tab_widget is not None
    tab_widget.setCurrentIndex(dialog.tab_labels().index("Preview"))

    # Assert: the specific missing-name message renders (not nothing).
    assert "name must be non-empty" in dialog.preview_message()


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
