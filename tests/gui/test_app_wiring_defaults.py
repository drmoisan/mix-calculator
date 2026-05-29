"""Unit tests for the default file-dialog chooser/runner factories.

Covers :func:`src.gui.app.default_save_chooser`,
:func:`src.gui.app.default_open_chooser`, and
:func:`src.gui.app.default_export_runner` — the production-side adapters that
:func:`src.gui.app.wire_control_signals` defaults to when callers do not supply
their own chooser/runner callables.

v2 Decision 2: the export runner no longer reads the format off
``ExportDialog``; it parses the Save dialog's filter string
("Excel (*.xlsx);;CSV (*.csv)") to decide the format. These tests stub
``QFileDialog.getSaveFileName`` to return the filter the user picked and
assert the runner returns the matching format tuple.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui import _wiring as wiring_module
from src.gui import app as app_module
from src.gui.widgets.export_dialog import ExportDialog

if TYPE_CHECKING:
    import pytest
    from pytestqt.qtbot import QtBot


def _accept_exec(_self: ExportDialog) -> int:
    """Stand in for ``ExportDialog.exec`` returning the accept code."""
    return 1


def _reject_exec(_self: ExportDialog) -> int:
    """Stand in for ``ExportDialog.exec`` returning the reject code."""
    return 0


def _stub_filename_chosen_db(*_args: object, **_kwargs: object) -> tuple[str, str]:
    """Stand in for ``QFileDialog.getSaveFileName`` returning ``chosen.db``."""
    return ("chosen.db", "")


def _stub_filename_chosen_existing_db(
    *_args: object, **_kwargs: object
) -> tuple[str, str]:
    """Stand in for ``QFileDialog.getOpenFileName`` returning ``existing.db``."""
    return ("existing.db", "")


def _stub_filename_chosen_xlsx(*_args: object, **_kwargs: object) -> tuple[str, str]:
    """Stand in for ``QFileDialog.getSaveFileName`` returning an xlsx path/filter."""
    return ("C:/out.xlsx", "Excel (*.xlsx)")


def _stub_filename_chosen_csv(*_args: object, **_kwargs: object) -> tuple[str, str]:
    """Stand in for ``QFileDialog.getSaveFileName`` returning a csv path/filter."""
    return ("C:/out.csv", "CSV (*.csv)")


def _stub_filename_cancelled(*_args: object, **_kwargs: object) -> tuple[str, str]:
    """Stand in for a cancelled ``QFileDialog`` returning empty strings."""
    return ("", "")


def test_default_save_chooser_returns_path_on_selection(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The production save chooser returns the path from QFileDialog.getSaveFileName."""
    del qtbot
    monkeypatch.setattr(
        wiring_module.QFileDialog,
        "getSaveFileName",
        staticmethod(_stub_filename_chosen_db),
    )

    assert app_module.default_save_chooser() == "chosen.db"


def test_default_save_chooser_returns_none_on_cancel(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty path from QFileDialog is normalized to None."""
    del qtbot
    monkeypatch.setattr(
        wiring_module.QFileDialog,
        "getSaveFileName",
        staticmethod(_stub_filename_cancelled),
    )

    assert app_module.default_save_chooser() is None


def test_default_open_chooser_returns_path_on_selection(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The production open chooser returns the path from QFileDialog.getOpenFileName."""
    del qtbot
    monkeypatch.setattr(
        wiring_module.QFileDialog,
        "getOpenFileName",
        staticmethod(_stub_filename_chosen_existing_db),
    )

    assert app_module.default_open_chooser() == "existing.db"


def test_default_open_chooser_returns_none_on_cancel(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty path from QFileDialog is normalized to None for Open."""
    del qtbot
    monkeypatch.setattr(
        wiring_module.QFileDialog,
        "getOpenFileName",
        staticmethod(_stub_filename_cancelled),
    )

    assert app_module.default_open_chooser() is None


def test_default_export_runner_returns_excel_for_xlsx_filter(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An ``"Excel (*.xlsx)"`` filter resolves to ``("Excel", path)``."""
    dialog = ExportDialog()
    qtbot.addWidget(dialog)
    monkeypatch.setattr(ExportDialog, "exec", _accept_exec)
    monkeypatch.setattr(
        wiring_module.QFileDialog,
        "getSaveFileName",
        staticmethod(_stub_filename_chosen_xlsx),
    )

    result = app_module.default_export_runner(dialog)

    assert result == ("Excel", "C:/out.xlsx")


def test_default_export_runner_returns_csv_for_csv_filter(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ``"CSV (*.csv)"`` filter resolves to ``("CSV", path)``."""
    dialog = ExportDialog()
    qtbot.addWidget(dialog)
    monkeypatch.setattr(ExportDialog, "exec", _accept_exec)
    monkeypatch.setattr(
        wiring_module.QFileDialog,
        "getSaveFileName",
        staticmethod(_stub_filename_chosen_csv),
    )

    result = app_module.default_export_runner(dialog)

    assert result == ("CSV", "C:/out.csv")


def test_default_export_runner_returns_none_when_dialog_rejected(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rejected export dialog (exec returns falsy) skips the destination chooser."""
    dialog = ExportDialog()
    qtbot.addWidget(dialog)
    monkeypatch.setattr(ExportDialog, "exec", _reject_exec)

    assert app_module.default_export_runner(dialog) is None


def test_default_export_runner_returns_none_when_destination_cancelled(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An accepted export dialog with a cancelled destination returns None."""
    dialog = ExportDialog()
    qtbot.addWidget(dialog)
    monkeypatch.setattr(ExportDialog, "exec", _accept_exec)
    monkeypatch.setattr(
        wiring_module.QFileDialog,
        "getSaveFileName",
        staticmethod(_stub_filename_cancelled),
    )

    assert app_module.default_export_runner(dialog) is None
