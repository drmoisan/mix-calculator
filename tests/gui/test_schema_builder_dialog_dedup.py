"""Dedup-tab Qt tests for :mod:`src.gui.widgets.schema_builder_dialog`.

Runs under ``QT_QPA_PLATFORM=offscreen`` (pinned by the GUI conftest). Covers the
Dedup tab: mode switching, the discriminator dropdown (Decision 6), the new
``auto`` mode default and its no-discriminator assembly (AC-8/D-3), and the
preserved invariant that aggregate without a discriminator still raises. Split
from ``test_schema_builder_dialog.py`` to keep each test file under the
repository's 500-line cap. Fabricated/masked data only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


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


def test_dedup_default_mode_is_auto(qtbot: QtBot) -> None:
    """AC-8/D-3: a fresh Dedup tab shows auto selected with no discriminator."""
    # Arrange / Act
    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)

    # Assert: the dedup mode defaults to auto, which carries no discriminator (D-3).
    mode, discriminator = dialog.get_dedup()
    assert mode == "auto"
    assert discriminator is None


def test_dedup_auto_assembles_without_discriminator(qtbot: QtBot) -> None:
    """AC-8/D-3: selecting auto assembles a no-discriminator DedupPolicy(mode=auto).

    The relaxed invariant applies only to auto: selecting auto assembles cleanly
    with no discriminator, while aggregate with no discriminator still raises the
    existing ``SchemaValidationError``.
    """
    # Arrange
    import pytest

    from src.gui.presenters._schema_builder_state import (
        SchemaBuilderState,
        assemble_schema,
    )
    from src.schema_model import SchemaValidationError

    dialog = SchemaBuilderDialog()
    qtbot.addWidget(dialog)
    dialog.set_columns(
        [
            ("Region", "dimension", True, True, ()),
            ("Sales", "measure", True, True, ()),
        ]
    )

    # Act: read the default (auto) dedup from the dialog and assemble a schema.
    dialog.set_dedup("auto", None)
    mode, discriminator = dialog.get_dedup()
    state = SchemaBuilderState(
        name="aop",
        version="1.0",
        columns=[
            ("Region", "dimension", True, True, ()),
            ("Sales", "measure", True, True, ()),
        ],
        key_columns=("Region",),
        dedup_mode=mode,
        discriminator=discriminator,
    )
    schema = assemble_schema(state)

    # Assert: the auto schema assembles with no discriminator.
    assert schema.dedup.mode == "auto"
    assert schema.dedup.discriminator_column is None

    # Assert: aggregate with no discriminator still raises (invariant unchanged).
    aggregate_state = SchemaBuilderState(
        name="aop",
        version="1.0",
        columns=[("Region", "dimension", True, True, ())],
        key_columns=("Region",),
        dedup_mode="aggregate",
        discriminator=None,
    )
    with pytest.raises(SchemaValidationError):
        assemble_schema(aggregate_state)


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


def test_key_multiselect_tracks_check_order_interactively(qtbot: QtBot) -> None:
    """AC-7/D-2: checking items interactively records the selection order.

    Exercises the multi-select widget's ``itemChanged`` path via the public
    ``toggle_column`` seam: checking items in a specific order yields that order
    from ``selected_columns``, and unchecking one drops it while preserving order.
    """
    # Arrange
    from src.gui.widgets._key_multiselect_widget import KeyMultiSelectWidget

    widget = KeyMultiSelectWidget()
    qtbot.addWidget(widget)
    widget.set_available_columns(["Customer", "SKU #", "Region"])

    # Act: check Region then Customer (non-list order) through the live item path.
    widget.toggle_column("Region", checked=True)
    widget.toggle_column("Customer", checked=True)

    # Assert: selection order reflects the order columns were checked.
    assert widget.selected_columns() == ["Region", "Customer"]

    # Act: uncheck Region; Customer remains, order preserved.
    widget.toggle_column("Region", checked=False)

    # Assert
    assert widget.selected_columns() == ["Customer"]
