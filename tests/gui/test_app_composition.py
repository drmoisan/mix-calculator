"""Composition-root smoke test for :mod:`src.gui.app`.

Runs under ``QT_QPA_PLATFORM=offscreen``. Calls :func:`build_application` (a
thin composition helper that constructs and wires every collaborator without
entering the blocking event loop) and asserts the ``MainWindow`` constructs
with the real collaborators and the ``ExporterRegistry`` reports
``["Excel", "CSV"]``. Event-driven (no waits).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from src.gui.app import build_application

if TYPE_CHECKING:
    import pytest
    from pytestqt.qtbot import QtBot

    from src.gui.services.db_service import DbService


def test_build_application_wires_real_collaborators(qtbot: QtBot) -> None:
    """build_application constructs MainWindow with the real services and exporters."""
    # Arrange / Act: build the wired application without entering the event loop.
    wired = build_application()
    qtbot.addWidget(wired.window)

    # Assert: the registry holds both concrete exporters in registration order.
    assert wired.registry.available_formats() == ["Excel", "CSV"]

    # Assert: the main window exposes the three per-input source widgets and the
    # preview. Per v2 Decision 2 the ExportDialog no longer carries a format
    # selector; the registry still reports the supported formats above.
    assert wired.window.le_widget is not None
    assert wired.window.aop_widget is not None
    assert wired.window.skulu_widget is not None
    assert wired.window.preview_widget is not None

    # Assert: the presenters are wired (constructed without raising).
    assert wired.le_presenter is not None
    assert wired.aop_presenter is not None
    assert wired.skulu_presenter is not None
    assert wired.pipeline_presenter is not None
    assert wired.export_presenter is not None


def test_pipeline_presenter_uses_status_bar_via_adapter(qtbot: QtBot) -> None:
    """The MainWindowPipelineView adapter routes pipeline outcomes to the bar.

    Exercises the adapter's set_running, show_result, and show_error paths
    directly through a fresh PipelinePresenter wired over the adapter.
    """
    import pandas as pd

    from src.gui.app import MainWindowPipelineView
    from src.gui.main_window import MainWindow
    from src.gui.pipeline_service import PipelineService
    from tests.gui.fakes.fake_services import FakeDbService, FakePipelineService

    # Arrange: a fresh window, the public adapter, and a fake pipeline service
    # with a successful run result so on_run can set/clear the running flag.
    window = MainWindow()
    qtbot.addWidget(window)
    adapter = MainWindowPipelineView(window)
    service = FakePipelineService(
        import_result={
            "LE": pd.DataFrame({"KEY": ["k1"]}),
            "aop": pd.DataFrame({"KEY": ["k1"]}),
            "sku_lu": pd.DataFrame({"SKU": ["SKU-001"]}),
        },
        run_result={"mix_rollup_4": pd.DataFrame({"value": [1.0]})},
    )
    presenter_view = adapter
    from src.gui.presenters.pipeline_presenter import PipelinePresenter

    presenter = PipelinePresenter(presenter_view, service)

    # Act 1 — guarded Run with no imports reports an error via show_error.
    presenter.on_run()

    # Assert 1
    assert "Run is unavailable" in window.statusBar().currentMessage()

    # Act 2 — import then run; the adapter must set_running(True) then (False)
    # and finally show_result via the success summary.
    from src.gui.pipeline_service import ImportSpec

    presenter.on_import_all(
        ImportSpec(
            le_path="le.xlsx",
            le_sheet="LE-8 + 4",
            aop_path="aop.xlsx",
            aop_sheet="AOP1",
            skulu_path="sku.xlsx",
            skulu_sheet="SKU_LU",
        )
    )
    presenter.on_run()

    # Assert 2: show_result routed a success summary to the status bar.
    assert "Run complete" in window.statusBar().currentMessage()

    # Act 3 — drive on_save with a FakeDbService so the adapter's show_result
    # branch is exercised for save too (FakePipelineService doesn't call DbService).
    # FakeDbService is structurally compatible with DbService (save_tables,
    # open_tables); cast at the injection point since DbService isn't a Protocol.
    # The `DbService` name is referenced only in the cast's string form, so it
    # lives in the TYPE_CHECKING import block.
    presenter_with_db = PipelinePresenter(
        adapter, PipelineService(db_service=cast("DbService", FakeDbService()))
    )
    presenter_with_db.on_save("results.db")

    # Assert 3: save success summary surfaced via the adapter.
    assert "Saved" in window.statusBar().currentMessage()
    # Keep references to silence type checks that complain about unused names.
    del service


def test_main_window_set_status_updates_status_bar(qtbot: QtBot) -> None:
    """set_status updates the QStatusBar message text directly."""
    # Arrange
    wired = build_application()
    qtbot.addWidget(wired.window)

    # Act
    wired.window.set_status("Ready")

    # Assert
    assert wired.window.statusBar().currentMessage() == "Ready"


def test_build_application_synchronous_runner_smoke(qtbot: QtBot) -> None:
    """Smoke test for the v2 SynchronousRunner-injected composition path."""
    from src.gui.app import build_application
    from src.gui.runners import SynchronousRunner

    wired = build_application(
        runner=SynchronousRunner(),
        save_path_chooser=lambda: None,
        open_path_chooser=lambda: None,
        export_dialog_runner=lambda _dialog: None,
    )
    qtbot.addWidget(wired.window)

    # (a) The runner is the injected SynchronousRunner.
    assert isinstance(wired.runner, SynchronousRunner)
    # (b) All four import buttons start enabled.
    assert wired.window.import_le_btn.isEnabled() is True
    assert wired.window.import_aop_btn.isEnabled() is True
    assert wired.window.import_skulu_btn.isEnabled() is True
    assert wired.window.import_all_btn.isEnabled() is True
    # (c) The preview model starts empty.
    assert wired.window.preview_widget.model.rowCount() == 0
    # (d) The exporter registry still reports both formats.
    assert wired.registry.available_formats() == ["Excel", "CSV"]


class _RecorderVelopackApp:
    """Stub for ``velopack.App`` that records calls to ``run`` in a shared log.

    Purpose:
        Allow the GUI bootstrap tests to assert that ``velopack.App().run()``
        is invoked exactly once, before ``QApplication`` construction, per AC10.

    Attributes:
        events: The shared ordered event log appended to by ``run`` so
            tests can assert call ordering relative to ``QApplication``
            construction.
    """

    def __init__(self, events: list[str]) -> None:
        """Bind the recorder to a shared call-order log."""
        self._events = events

    def run(self) -> None:
        """Record the Velopack bootstrap call in the shared log."""
        # The single sentinel marker tests look for when asserting that the
        # Velopack run() happens before QApplication construction.
        self._events.append("velopack_run")


def test_main_entry_point_runs_event_loop(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main() bootstraps Qt and enters the event loop, returning its exit code.

    Exercises the ``main`` entry without actually blocking by patching the
    Qt ``QApplication.exec`` to return immediately and reusing the pytest-qt
    managed application instance. Per AC10 this test now also asserts
    ``velopack.App().run()`` is called before ``QApplication`` construction.
    """
    # Arrange: the qtbot fixture ensures a QApplication exists; patch exec on it
    # to return immediately, and patch QApplication construction in main to
    # return that same instance instead of creating a second one.
    del qtbot  # qtbot ensures QApplication exists for pytest-qt

    from PySide6.QtWidgets import QApplication

    from src.gui import app as app_module

    raw_instance = QApplication.instance()
    assert raw_instance is not None
    instance = cast("QApplication", raw_instance)

    def _instant_exec(_self: QApplication) -> int:
        return 0

    # Shared ordered call-log to verify Velopack runs before QApplication.
    events: list[str] = []

    def _existing_qapp(_args: list[str]) -> QApplication:
        events.append("qapplication_init")
        return instance

    def _velopack_app_factory() -> _RecorderVelopackApp:
        return _RecorderVelopackApp(events)

    monkeypatch.setattr(QApplication, "exec", _instant_exec)
    monkeypatch.setattr(app_module, "QApplication", _existing_qapp)
    # Patch the velopack.App constructor so the bootstrap call is observable
    # and inert. The recorder appends "velopack_run" to the shared log.
    monkeypatch.setattr("velopack.App", _velopack_app_factory)

    # Act
    exit_code = app_module.main([])

    # Assert: exit code is 0 (no event loop crash) and AC10 ordering holds.
    assert exit_code == 0
    assert events == ["velopack_run", "qapplication_init"]


def test_main_calls_velopack_app_run_before_qapplication(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``velopack.App().run()`` must fire before ``QApplication`` construction (AC10).

    This is a dedicated ordering assertion separate from the broader
    event-loop smoke test so the AC10 invariant is testable in isolation
    and so a future refactor that splits ``main`` cannot silently break
    the bootstrap ordering.
    """
    del qtbot  # qtbot ensures a QApplication exists for pytest-qt

    from PySide6.QtWidgets import QApplication

    from src.gui import app as app_module

    raw_instance = QApplication.instance()
    assert raw_instance is not None
    instance = cast("QApplication", raw_instance)

    def _instant_exec(_self: QApplication) -> int:
        return 0

    events: list[str] = []

    def _existing_qapp(_args: list[str]) -> QApplication:
        events.append("qapplication_init")
        return instance

    def _velopack_app_factory() -> _RecorderVelopackApp:
        return _RecorderVelopackApp(events)

    monkeypatch.setattr(QApplication, "exec", _instant_exec)
    monkeypatch.setattr(app_module, "QApplication", _existing_qapp)
    monkeypatch.setattr("velopack.App", _velopack_app_factory)

    # Act: invoke the entry point; we only care about the call ordering.
    app_module.main([])

    # Assert: the velopack bootstrap must be the very first observable event.
    assert events[:2] == ["velopack_run", "qapplication_init"]


def test_main_sets_window_icon_on_qapplication(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC8: main() resolves the icon path and calls setWindowIcon on the QApplication.

    Patches the QIcon constructor and the resolve_icon_path helper so the
    test asserts the path string flows through unchanged and that
    ``setWindowIcon`` was driven with the QIcon recorder's return value.
    """
    del qtbot  # qtbot ensures a QApplication exists for pytest-qt

    from pathlib import Path

    from PySide6.QtWidgets import QApplication

    from src.gui import app as app_module

    raw_instance = QApplication.instance()
    assert raw_instance is not None
    instance = cast("QApplication", raw_instance)

    fake_icon_path = Path("/fake/icon.ico")
    qicon_calls: list[str] = []
    set_window_icon_args: list[object] = []
    sentinel = object()

    def _fake_qicon(path: str) -> object:
        # Record every QIcon constructor call so the test can verify the
        # exact path string that was passed through from resolve_icon_path.
        qicon_calls.append(path)
        return sentinel

    def _record_set_window_icon(_self: QApplication, icon: object) -> None:
        # The test records the icon argument so it can confirm the QIcon
        # instance produced by the recorded constructor is the value passed
        # to setWindowIcon.
        set_window_icon_args.append(icon)

    def _instant_exec(_self: QApplication) -> int:
        return 0

    def _existing_qapp(_args: list[str]) -> QApplication:
        return instance

    def _no_op_velopack() -> None:
        return None

    monkeypatch.setattr(app_module, "resolve_icon_path", lambda: fake_icon_path)
    monkeypatch.setattr(app_module, "QIcon", _fake_qicon)
    monkeypatch.setattr(QApplication, "setWindowIcon", _record_set_window_icon)
    monkeypatch.setattr(QApplication, "exec", _instant_exec)
    monkeypatch.setattr(app_module, "QApplication", _existing_qapp)
    monkeypatch.setattr(app_module, "run_velopack_bootstrap", _no_op_velopack)

    # Act
    rc = app_module.main([])

    # Assert: exit was clean.
    assert rc == 0
    # AC8: main() drives setWindowIcon on the QApplication. The plan's
    # P7-T5 also drives setWindowIcon inside build_application, so both
    # paths fire here. Each call MUST construct a QIcon from the same
    # resolved path and pass the resulting icon to setWindowIcon, so the
    # title bar / taskbar / Alt-Tab preview pick up the icon regardless
    # of which composition entry the caller used.
    assert len(qicon_calls) >= 1
    for recorded in qicon_calls:
        assert Path(recorded) == fake_icon_path
    assert len(set_window_icon_args) == len(qicon_calls)
    for icon_arg in set_window_icon_args:
        assert icon_arg is sentinel


def test_build_application_calls_set_window_icon_when_qt_app_constructed(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC8: build_application drives setWindowIcon on the resolved QApplication.

    The composition root is responsible for setting the icon on the
    QApplication so the title bar, taskbar, and Alt-Tab preview surface
    it. The test patches resolve_icon_path and QIcon, calls
    build_application without supplying qt_app, and asserts the QIcon
    constructor was driven with the resolved path string.
    """
    from pathlib import Path

    from PySide6.QtWidgets import QApplication

    from src.gui import app as app_module

    raw_instance = QApplication.instance()
    assert raw_instance is not None
    instance = cast("QApplication", raw_instance)

    fake_icon_path = Path("/fake/icon.ico")
    qicon_calls: list[str] = []
    set_window_icon_args: list[object] = []
    sentinel = object()

    def _fake_qicon(path: str) -> object:
        qicon_calls.append(path)
        return sentinel

    def _record_set_window_icon(_self: QApplication, icon: object) -> None:
        set_window_icon_args.append(icon)

    def _existing_qapp(_args: list[str]) -> QApplication:
        return instance

    monkeypatch.setattr(app_module, "resolve_icon_path", lambda: fake_icon_path)
    monkeypatch.setattr(app_module, "QIcon", _fake_qicon)
    monkeypatch.setattr(QApplication, "setWindowIcon", _record_set_window_icon)
    monkeypatch.setattr(app_module, "QApplication", _existing_qapp)

    # Act: build_application without an externally-managed QApplication so
    # the function follows the construction branch and drives setWindowIcon.
    wired = app_module.build_application()
    qtbot.addWidget(wired.window)

    # Assert: the QIcon was constructed once with the resolved string and
    # setWindowIcon was driven once with the resulting icon object.
    assert len(qicon_calls) == 1
    assert Path(qicon_calls[0]) == fake_icon_path
    assert len(set_window_icon_args) == 1
    assert set_window_icon_args[0] is sentinel
