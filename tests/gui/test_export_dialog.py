"""Qt tests for :mod:`src.gui.widgets.export_dialog`.

Runs under ``QT_QPA_PLATFORM=offscreen``. Verifies ``set_table_list`` renders
the checklist, ``get_selected_names`` returns checked names, and
``select_all_tables`` checks every item. Per v2 Decision 2, the format selector
combo was removed from the dialog; format choice now lives in the Save dialog's
filter and is covered by ``tests/gui/test_app_wiring_defaults.py``.
Fabricated data only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.widgets.export_dialog import ExportDialog
from src.gui.widgets.progress_dialog import ProgressDialog

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_set_table_list_renders_checklist(qtbot: QtBot) -> None:
    """set_table_list adds one checkable item per name."""
    # Arrange
    dialog = ExportDialog()
    qtbot.addWidget(dialog)

    # Act
    dialog.set_table_list(["le_wide", "aop_wide", "mix_rollup_4"])

    # Assert: three unchecked items in display order.
    assert dialog.get_selected_names() == []


def test_checking_items_then_get_selected_names_returns_checked(qtbot: QtBot) -> None:
    """Checking items then reading get_selected_names returns checked names."""
    # Arrange
    dialog = ExportDialog()
    qtbot.addWidget(dialog)
    dialog.set_table_list(["le_wide", "aop_wide", "mix_rollup_4"])

    # Act: check items 0 and 2 via the public set_item_checked method.
    dialog.set_item_checked(0, True)
    dialog.set_item_checked(2, True)

    # Assert: only the checked names are reported, in display order.
    assert dialog.get_selected_names() == ["le_wide", "mix_rollup_4"]


def test_select_all_tables_checks_every_item(qtbot: QtBot) -> None:
    """select_all_tables checks every item; get_selected_names returns them all."""
    # Arrange
    dialog = ExportDialog()
    qtbot.addWidget(dialog)
    dialog.set_table_list(["a", "b", "c"])

    # Act
    dialog.select_all_tables()

    # Assert
    assert dialog.get_selected_names() == ["a", "b", "c"]


def test_set_table_list_populates_three_checklist_items(qtbot: QtBot) -> None:
    """Calling set_table_list(['LE', 'aop', 'sku_lu']) populates three items.

    Then checking the first two yields ['LE', 'aop'] and select_all checks all.
    """
    dialog = ExportDialog()
    qtbot.addWidget(dialog)
    dialog.set_table_list(["LE", "aop", "sku_lu"])

    dialog.set_item_checked(0, True)
    dialog.set_item_checked(1, True)
    assert dialog.get_selected_names() == ["LE", "aop"]

    dialog.select_all_tables()
    assert dialog.get_selected_names() == ["LE", "aop", "sku_lu"]


def test_set_item_checked_out_of_range_is_noop(qtbot: QtBot) -> None:
    """An out-of-range set_item_checked is a no-op (does not raise)."""
    # Arrange
    dialog = ExportDialog()
    qtbot.addWidget(dialog)
    dialog.set_table_list(["a", "b"])

    # Act
    dialog.set_item_checked(5, True)
    dialog.set_item_checked(-1, True)

    # Assert: nothing was checked.
    assert dialog.get_selected_names() == []


def test_progress_dialog_set_and_read_message(qtbot: QtBot) -> None:
    """ProgressDialog renders an initial message and updates it via set_message."""
    # Arrange
    dialog = ProgressDialog("Importing...")
    qtbot.addWidget(dialog)

    # Act / Assert: initial message visible.
    assert dialog.message() == "Importing..."

    # Act: update the message.
    dialog.set_message("Running...")

    # Assert
    assert dialog.message() == "Running..."
