"""Behavioral integration test for AC-10 (composition smoke).

Verifies that every control button is reachable as a public attribute on the
wired ``MainWindow`` and that ``SynchronousRunner`` is the injected runner.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.app import build_application
from src.gui.runners import SynchronousRunner
from tests.gui.fakes.fake_services import FakePipelineService, FakeWorkbookReader

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_composition_smoke_all_control_buttons_addressable(qtbot: QtBot) -> None:
    """AC-10: each control button is a public attribute and Runner is injected."""
    service = FakePipelineService()
    reader = FakeWorkbookReader(sheet_names=["AOP1"])
    wired = build_application(
        runner=SynchronousRunner(),
        pipeline_service=service,
        workbook_reader=reader,
        save_path_chooser=lambda: None,
        open_path_chooser=lambda: None,
        export_dialog_runner=lambda _dialog: None,
    )
    qtbot.addWidget(wired.window)

    # Every control button reachable as a public attribute.
    for attr in (
        "import_le_btn",
        "import_aop_btn",
        "import_skulu_btn",
        "import_all_btn",
        "run_btn",
        "save_btn",
        "open_btn",
        "export_btn",
    ):
        assert hasattr(wired.window, attr)

    # The injected runner is the SynchronousRunner instance.
    assert isinstance(wired.runner, SynchronousRunner)


def test_composition_clicking_run_save_open_export_does_not_raise(
    qtbot: QtBot,
) -> None:
    """AC-10: clicking Run/Save/Open/Export does not raise for the wired handlers.

    Skips the import-button clicks here because the FakePipelineService's
    import_one paths require a configured import_result; the import-button
    click coverage is provided by ``test_behavioral_import_buttons.py``.
    """
    import pandas as pd

    service = FakePipelineService(
        import_result={
            "LE": pd.DataFrame({"K": [1]}),
            "aop": pd.DataFrame({"K": [1]}),
            "sku_lu": pd.DataFrame({"K": [1]}),
        }
    )
    reader = FakeWorkbookReader(sheet_names=["AOP1"])
    wired = build_application(
        runner=SynchronousRunner(),
        pipeline_service=service,
        workbook_reader=reader,
        save_path_chooser=lambda: None,
        open_path_chooser=lambda: None,
        export_dialog_runner=lambda _dialog: None,
    )
    qtbot.addWidget(wired.window)

    # Each button has a wired handler. Save/Open/Export each return early when
    # the chooser/runner returns None. Run/Import surface a guard error via the
    # status bar but do not raise.
    wired.window.run_btn.click()
    wired.window.save_btn.click()
    wired.window.open_btn.click()
    wired.window.export_btn.click()
    # Import-All is covered: with import_result configured it actually loads.
    wired.window.le_widget.set_path("le.xlsx")
    wired.window.aop_widget.set_path("aop.xlsx")
    wired.window.skulu_widget.set_path("sku.xlsx")
    wired.window.import_all_btn.click()
