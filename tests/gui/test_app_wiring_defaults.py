"""Unit tests for the default file-dialog chooser/runner factories.

Covers :func:`src.gui.app.default_save_chooser`,
:func:`src.gui.app.default_open_chooser`, and
:func:`src.gui.app.default_export_runner` — the production-side adapters that
:func:`src.gui.app.wire_control_signals` defaults to when callers do not supply
their own chooser/runner callables.

Each test monkeypatches the :class:`QFileDialog` static factory (or the
:class:`ExportDialog.exec` method) at the import location used by the unit
under test, then asserts the normalization rules:

* a chosen file path becomes the return value,
* an empty path is normalized to ``None``,
* a rejected dialog short-circuits before the destination chooser fires.

Companion module :mod:`tests.gui.test_app_wiring` covers signal routing for
:func:`wire_control_signals`. Shared test doubles live in
:mod:`tests.gui._wiring_test_doubles`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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
    """Stand in for ``QFileDialog.getSaveFileName`` returning ``dest.xlsx``."""
    return ("dest.xlsx", "")


def _stub_filename_cancelled(*_args: object, **_kwargs: object) -> tuple[str, str]:
    """Stand in for a cancelled ``QFileDialog`` returning empty strings."""
    return ("", "")


def test_default_save_chooser_returns_path_on_selection(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The production save chooser returns the path from QFileDialog.getSaveFileName."""
    # Arrange: a QApplication exists via qtbot; patch the static factory at the
    # location the chooser imports it from.
    del qtbot
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getSaveFileName",
        staticmethod(_stub_filename_chosen_db),
    )

    # Act + Assert
    assert app_module.default_save_chooser() == "chosen.db"


def test_default_save_chooser_returns_none_on_cancel(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty path from QFileDialog is normalized to None."""
    # Arrange
    del qtbot
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getSaveFileName",
        staticmethod(_stub_filename_cancelled),
    )

    # Act + Assert
    assert app_module.default_save_chooser() is None


def test_default_open_chooser_returns_path_on_selection(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The production open chooser returns the path from QFileDialog.getOpenFileName."""
    # Arrange
    del qtbot
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getOpenFileName",
        staticmethod(_stub_filename_chosen_existing_db),
    )

    # Act + Assert
    assert app_module.default_open_chooser() == "existing.db"


def test_default_open_chooser_returns_none_on_cancel(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty path from QFileDialog is normalized to None for Open."""
    # Arrange
    del qtbot
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getOpenFileName",
        staticmethod(_stub_filename_cancelled),
    )

    # Act + Assert
    assert app_module.default_open_chooser() is None


def test_default_export_runner_returns_tuple_on_accept(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The production runner returns (format, path) when both dialogs accept."""
    # Arrange: real ExportDialog with one format; patch its exec to return
    # truthy, and the destination chooser to return a path.
    dialog = ExportDialog(["Excel"])
    qtbot.addWidget(dialog)
    monkeypatch.setattr(ExportDialog, "exec", _accept_exec)
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getSaveFileName",
        staticmethod(_stub_filename_chosen_xlsx),
    )

    # Act
    result = app_module.default_export_runner(dialog)

    # Assert
    assert result == ("Excel", "dest.xlsx")


def test_default_export_runner_returns_none_when_dialog_rejected(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rejected export dialog (exec returns falsy) skips the destination chooser."""
    # Arrange
    dialog = ExportDialog(["Excel"])
    qtbot.addWidget(dialog)
    monkeypatch.setattr(ExportDialog, "exec", _reject_exec)

    # Act + Assert
    assert app_module.default_export_runner(dialog) is None


def test_default_export_runner_returns_none_when_destination_cancelled(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An accepted export dialog with a cancelled destination returns None."""
    # Arrange
    dialog = ExportDialog(["Excel"])
    qtbot.addWidget(dialog)
    monkeypatch.setattr(ExportDialog, "exec", _accept_exec)
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getSaveFileName",
        staticmethod(_stub_filename_cancelled),
    )

    # Act + Assert
    assert app_module.default_export_runner(dialog) is None
