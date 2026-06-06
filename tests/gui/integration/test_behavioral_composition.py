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
    import pytest
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


def test_composed_import_path_never_reaches_stdin(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: the composed GUI import path never reaches stdin (AC-1/AC-3).

    Builds the production pipeline service (no injected service) so the
    composition root's injected example-aware KEY-mismatch resolver is in force,
    then imports AOP and LE through it. The loaders are patched to record the
    forwarded resolver CALLABLE (the divergence-only seam under issue #52) and
    ``builtins.input`` is patched to fail, proving no GUI import path reaches the
    stdin prompt. Invoking each recorded resolver confirms the composed modal
    (forced to "Keep existing") maps to the "trust" policy.
    """
    import pandas as pd

    # Arrange: record the resolver each loader receives and fail on any stdin read.
    recorded: list[tuple[str, object]] = []

    def _input(_prompt: str = "") -> str:
        raise AssertionError("real stdin input() was reached in a GUI session")

    def _fake_load_aop(
        _path: str,
        *,
        sheet: str = "AOP1",
        resolver: object = None,
        **_kwargs: object,
    ) -> pd.DataFrame:
        recorded.append(("aop", resolver))
        return pd.DataFrame({"KEY": ["k1"]})

    def _fake_load_source(
        _path: str, _sheet: str, *, resolver: object = None, **_kwargs: object
    ) -> pd.DataFrame:
        recorded.append(("LE", resolver))
        return pd.DataFrame({"KEY": ["k1"]})

    def _passthrough_normalize(frame: pd.DataFrame) -> pd.DataFrame:
        return frame

    def _noop_validate(_source: pd.DataFrame, _output: pd.DataFrame) -> None:
        return None

    monkeypatch.setattr("builtins.input", _input)
    monkeypatch.setattr("src.load_aop.load_aop", _fake_load_aop)
    monkeypatch.setattr("src.normalize_le.load_source", _fake_load_source)
    monkeypatch.setattr("src.normalize_le.normalize", _passthrough_normalize)
    monkeypatch.setattr("src.normalize_le.validate_tieouts", _noop_validate)

    # Build the production service (no injected pipeline_service) under the
    # composition root's modal resolver, forced to "Keep existing" -> trust.
    from src.gui import _key_mismatch_dialog

    class _AutoKeepBox:
        class Icon:
            Question = object()

        class ButtonRole:
            AcceptRole = object()
            DestructiveRole = object()

        def __init__(self, _parent: object) -> None:
            self._keep: object | None = None

        def setWindowTitle(self, _title: str) -> None:
            return None

        def setText(self, _text: str) -> None:
            return None

        def setIcon(self, _icon: object) -> None:
            return None

        def addButton(self, label: str, _role: object) -> object:
            button = object()
            if label == _key_mismatch_dialog.KEEP_EXISTING_LABEL:
                self._keep = button
            return button

        def setDefaultButton(self, _button: object) -> None:
            return None

        def exec(self) -> None:
            return None

        def clickedButton(self) -> object | None:
            return self._keep

    monkeypatch.setattr(_key_mismatch_dialog, "QMessageBox", _AutoKeepBox, raising=True)
    wired = build_application(runner=SynchronousRunner())
    qtbot.addWidget(wired.window)

    # Act: import AOP and LE through the composed production service.
    wired.pipeline_service.import_aop("aop.xlsx", "AOP1")
    wired.pipeline_service.import_le("le.xlsx", "LE-8 + 4")

    # Assert: both loaders received a resolver CALLABLE (the divergence-only seam,
    # not an eager policy string), and invoking each composed resolver maps the
    # "Keep existing" modal choice to the "trust" policy; stdin was never reached.
    by_source = dict(recorded)
    aop_resolver = by_source["aop"]
    le_resolver = by_source["LE"]
    assert callable(aop_resolver)
    assert callable(le_resolver)
    assert aop_resolver([("LEGACY", "REBUILT")]) == "trust"
    assert le_resolver([("LEGACY", "REBUILT")]) == "trust"
