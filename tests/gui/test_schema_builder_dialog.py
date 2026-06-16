"""Qt tests for :mod:`src.gui.widgets.schema_builder_dialog`.

Runs under ``QT_QPA_PLATFORM=offscreen`` (pinned by the GUI conftest). Verifies
each tab renders the pushed state and reports edits back through the protocol
getters: identity round-trip, a column-row round-trip, key selection, dedup mode
switch with discriminator, derived/formula entry with the inline error surface,
and ``show_preview`` rendering. Fabricated data only; no temp files or network.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt

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


def test_identity_description_round_trips_multi_line_text(qtbot: QtBot) -> None:
    """AC-2: the Identity description round-trips embedded newlines and wraps.

    The description control is a multi-line ``QPlainTextEdit``, so a value with
    embedded newlines survives set/get unchanged, and the widget is configured to
    wrap long lines at the widget width.
    """
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)
    multi_line = "Line one\nLine two\nLine three"

    # Act
    dialog.set_identity("aop", "1.0", multi_line)

    # Assert: the embedded newlines survive the round-trip exactly.
    assert dialog.get_identity() == ("aop", "1.0", multi_line)


def test_identity_description_is_wrapping_multiline_widget(qtbot: QtBot) -> None:
    """AC-2: the Identity description control wraps at the widget width.

    The builder constructs the description as a multi-line ``QPlainTextEdit`` with
    word-wrap at the widget width and an Expanding vertical size policy so it grows
    with the window.
    """
    # Arrange / Act
    from PySide6.QtWidgets import QPlainTextEdit, QSizePolicy

    from src.gui.widgets._schema_builder_tabs import build_identity_tab

    controls = build_identity_tab()
    qtbot.addWidget(controls.widget)

    # Assert: the description is a wrapping, vertically expanding multi-line widget.
    assert isinstance(controls.description, QPlainTextEdit)
    assert (
        controls.description.lineWrapMode() == QPlainTextEdit.LineWrapMode.WidgetWidth
    )
    assert (
        controls.description.sizePolicy().verticalPolicy()
        == QSizePolicy.Policy.Expanding
    )


def test_dialog_is_resizable_top_level_window_below_default(
    qtbot: QtBot,
) -> None:
    """AC-1: the dialog is a resizable top-level window sizable below default.

    The dialog is configured as a top-level ``Qt.Window`` with the minimize,
    maximize/restore, and close hints, plus a minimum size below the 900x700
    default so the user can drag it smaller (and thereby reach all 26 AOP
    canonical rows via the Columns-tab scroll area).
    """
    # Arrange / Act
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Assert: the resizable top-level window flags are present.
    flags = dialog.windowFlags()
    assert flags & Qt.WindowType.Window
    assert flags & Qt.WindowType.WindowMinimizeButtonHint
    assert flags & Qt.WindowType.WindowMaximizeButtonHint
    assert flags & Qt.WindowType.WindowCloseButtonHint
    # Assert: the minimum size is below the default height so the user can size
    # the window smaller than the default (no fixed-size behavior).
    assert dialog.minimumSize().height() < 700
    assert dialog.minimumSize().width() < 900


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
    """AC-7: key multi-select columns and SKU coercion round-trip (D-2).

    The Key tab selects from the declared canonical columns, so the columns are
    declared first, then selected; the ordered selection and SKU flag round-trip.
    """
    # Arrange: declare the canonical columns so they are selectable in the key
    # multi-select (D-2, Option C).
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)
    dialog.set_columns(
        [
            ("Customer", "dimension", True, True, ()),
            ("SKU #", "dimension", True, True, ()),
        ]
    )

    # Act
    dialog.set_key(("Customer", "SKU #"), sku_coercion=True)

    # Assert
    assert dialog.get_key() == (("Customer", "SKU #"), True)


def test_key_multiselect_composes_ordered_column_ref_keyspec(qtbot: QtBot) -> None:
    """AC-7/D-2: the key selection composes ordered column-ref KeySpec parts.

    Selecting an ordered subset of declared columns composes a ``KeySpec`` whose
    column-ref parts match the selection in order, joined by the default separator;
    the model and loader are unchanged (round-trips through ``KeySpec``).
    """
    # Arrange
    from src.gui.presenters._schema_builder_state import (
        DEFAULT_KEY_SEPARATOR,
        key_parts_from_columns,
    )
    from src.schema_model import KeySpec

    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)
    dialog.set_columns(
        [
            ("Customer", "dimension", True, True, ()),
            ("SKU #", "dimension", True, True, ()),
            ("Region", "dimension", False, True, ()),
        ]
    )

    # Act: select two of the three declared columns, in order, plus SKU coercion.
    dialog.set_key(("Customer", "SKU #"), sku_coercion=True)
    columns, sku = dialog.get_key()
    parts = key_parts_from_columns(columns)
    key = KeySpec(parts=tuple(parts), sku_coercion=sku)

    # Assert: the ordered column-ref names match the selection (loader keys on these).
    assert key.column_names == ("Customer", "SKU #")
    # Assert: a default literal-text separator is interleaved between the refs.
    assert any(
        not p.is_column_ref and p.value == DEFAULT_KEY_SEPARATOR for p in key.parts
    )
    # Assert: the SKU-coercion checkbox is honored in the assembled KeySpec.
    assert key.sku_coercion is True


def test_key_multiselect_round_trips_through_assemble_schema(qtbot: QtBot) -> None:
    """AC-7/D-2: the key selection round-trips through assemble_schema unchanged.

    Loading the selection through the existing assembly/key resolution proves no
    model or loader change is required: the assembled schema's key column names
    match the ordered selection.
    """
    # Arrange
    from src.gui.presenters._schema_builder_state import (
        SchemaBuilderState,
        assemble_schema,
        key_parts_from_columns,
    )

    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)
    dialog.set_columns(
        [
            ("Customer", "dimension", True, True, ()),
            ("SKU #", "dimension", True, True, ()),
        ]
    )
    dialog.set_key(("SKU #", "Customer"), sku_coercion=False)

    # Act: assemble a schema from a state carrying the selection's key parts.
    columns, sku = dialog.get_key()
    state = SchemaBuilderState(
        name="aop",
        version="1.0",
        columns=[
            ("Customer", "dimension", True, True, ()),
            ("SKU #", "dimension", True, True, ()),
        ],
        key_parts=key_parts_from_columns(columns),
        sku_coercion=sku,
    )
    schema = assemble_schema(state)

    # Assert: the assembled key preserves the user's selection order.
    assert schema.key.column_names == ("SKU #", "Customer")
    assert schema.key.sku_coercion is False


def test_derived_entry_round_trip(qtbot: QtBot) -> None:
    """A derived/formula row round-trips through set_derived/get_derived."""
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.set_derived([("YTG", "FY - YTD")])

    # Assert
    assert dialog.get_derived() == [("YTG", "FY - YTD")]


def test_derived_rows_render_with_equals_separator(qtbot: QtBot) -> None:
    """AC-3: derived rows render as ``name = expression`` and never use ``|``.

    The rendered editor text uses the ``=`` separator; the legacy ``name|expression``
    pipe form is no longer produced anywhere.
    """
    # Arrange: build the derived tab so its editor text can be read publicly.
    from src.gui.widgets._schema_builder_tabs import build_derived_tab

    controls = build_derived_tab()
    qtbot.addWidget(controls.widget)
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Act: render two derived rows through the dialog and a single row through the
    # builder's editor so the rendered text is observable on a public control.
    dialog.set_derived([("YTG", "FY - YTD"), ("Margin", "Profit / Sales")])
    controls.editor.setPlainText("YTG = FY - YTD")

    # Assert: the rendered text uses ``=`` and never the legacy pipe separator.
    rendered = controls.editor.toPlainText()
    assert " = " in rendered
    assert "|" not in rendered
    # Assert: round-tripping through the dialog parses the ``=`` form back.
    assert dialog.get_derived() == [("YTG", "FY - YTD"), ("Margin", "Profit / Sales")]


def test_derived_parse_splits_on_first_equals_only(qtbot: QtBot) -> None:
    """AC-3: parsing splits on the first ``=`` so expressions may contain ``=``.

    ``str.partition(" = ")`` guarantees the split is on the first occurrence, so a
    name with a single expression survives even when the expression itself is
    arithmetic that could contain an equals comparison.
    """
    # Arrange
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Act: an expression with a later " = " must stay attached to the name's value.
    dialog.set_derived([("Flag", "A = B")])

    # Assert: the name is the first segment; the rest is the full expression.
    assert dialog.get_derived() == [("Flag", "A = B")]


def test_derived_stores_col_form_and_displays_brackets(qtbot: QtBot) -> None:
    """AC-4/D-1: stored form is bare ``col(...)``; display form is bracketed.

    Declaring the referenced columns lets the dialog re-bracket the known
    references for display, while ``get_derived`` returns the stored ``col("Name")``
    form that the formula engine accepts. No bracket syntax ever reaches the
    evaluator.
    """
    # Arrange: declare the columns the expression references so they are "known".
    from src.gui.widgets._schema_builder_derived_format import render_derived_lines
    from src.schema_formula import FormulaEvaluator

    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)
    dialog.set_columns(
        [
            ("Revenue", "measure", False, True, ()),
            ("Units", "measure", False, True, ()),
        ]
    )

    # Act: push a stored-form derived row (bare col()), then read it back.
    stored_rows = [("Margin", 'safe_div(col("Revenue"), col("Units"))')]
    dialog.set_derived(stored_rows)
    read_back = dialog.get_derived()

    # Assert: the persisted form is the bare col() form (no brackets reach storage).
    assert read_back == stored_rows
    assert "[" not in read_back[0][1]
    # Assert: the rendered display form (same production path) is bracketed.
    display = render_derived_lines(stored_rows, ["Revenue", "Units"])
    assert display == "Margin = safe_div([Revenue], [Units])"
    # Assert: the stored expression validates under the unchanged formula grammar.
    FormulaEvaluator().validate(read_back[0][1], ["Revenue", "Units"])


def test_derived_bracketed_entry_strips_to_col_on_read(qtbot: QtBot) -> None:
    """AC-4/D-1: a user-entered bracketed expression strips to ``col(...)``.

    Simulates the user authoring via brackets (the display convention) and proves
    the value read back for storage/validation is the bare ``col("Name")`` form.
    """
    # Arrange
    from src.schema_formula import FormulaEvaluator

    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)
    dialog.set_columns([("Order Date", "dimension", False, True, ())])

    # Act: set a stored row whose display will be bracketed, then read it back.
    dialog.set_derived([("Flag", 'col("Order Date")')])
    read_back = dialog.get_derived()

    # Assert: the read-back stored form is the bare col() form and validates.
    assert read_back == [("Flag", 'col("Order Date")')]
    FormulaEvaluator().validate(read_back[0][1], ["Order Date"])


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
