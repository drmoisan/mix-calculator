"""Shared test doubles and builders for the app-wiring test modules.

This private helper module exists to keep the per-file size of the wiring
tests below the repository's 500-line cap (see
``.claude/rules/general-code-change.md``). It hosts the typed ``ExportPresenter``
subclass and the ``_build_wired`` factory so both
``test_app_wiring`` and ``test_app_wiring_defaults`` (and any future wiring
slice) can import a single canonical seam.

The underscore prefix marks the module as private to the ``tests/gui``
package; production code must not depend on it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from src.gui.app import wire_control_signals
from src.gui.exporters.registry import ExporterRegistry
from src.gui.main_window import MainWindow
from src.gui.pipeline_service import ImportSpec
from src.gui.presenters.export_presenter import ExportPresenter
from src.gui.presenters.pipeline_presenter import PipelinePresenter
from src.gui.widgets.export_dialog import ExportDialog
from tests.gui.fakes.fake_exporters import FakeExporter
from tests.gui.fakes.fake_services import FakePipelineService
from tests.gui.fakes.fake_views import FakePipelineView

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def fabricated_imports() -> dict[str, pd.DataFrame]:
    """Return a controlled three-table import set for the wiring tests.

    Returns:
        Mapping of import key (``"LE"``, ``"aop"``, ``"sku_lu"``) to a
        single-row :class:`pandas.DataFrame`. The shapes are intentionally
        trivial because the wiring tests only inspect routing, not data.
    """
    return {
        "LE": pd.DataFrame({"KEY": ["k1"]}),
        "aop": pd.DataFrame({"KEY": ["k1"]}),
        "sku_lu": pd.DataFrame({"SKU": ["SKU-001"]}),
    }


def populate_widget_paths(window: MainWindow) -> None:
    """Drive the three widgets so ``current_path``/``current_sheet`` are non-empty.

    Args:
        window: The main window whose widgets are being seeded.

    Returns:
        ``None``.

    Side effects:
        Mutates each source-input widget's current path. The sheet selection
        defaults applied by the widget remain in place.
    """
    # set_path mirrors the file-dialog selection path used in production code.
    window.le_widget.set_path("le.xlsx")
    window.aop_widget.set_path("aop.xlsx")
    window.skulu_widget.set_path("sku.xlsx")


class AutoCheckAllExportPresenter(ExportPresenter):
    """Test subclass that auto-checks every table after ``set_available_tables``.

    Purpose:
        Provide a typed seam for the wiring tests that need a non-empty
        selection after a single signal emission. Subclassing preserves the
        full ``ExportPresenter`` type contract (no instance method assignment,
        no monkey-patching) so the test surface stays Pyright-clean without
        any ``# type: ignore`` suppression.

    Responsibilities:
        Forward ``set_available_tables`` to the base implementation and then
        ask the dialog to select every table the wiring helper just staged.

    Usage:
        Substituted for :class:`ExportPresenter` in tests that need the
        export-signal flow to end with a non-empty selection.

    Attributes:
        _dialog: The export dialog whose ``select_all_tables`` is invoked
            after the base presenter pushes the available names.
    """

    def __init__(
        self,
        view: ExportDialog,
        registry: ExporterRegistry,
        dialog: ExportDialog,
    ) -> None:
        """Initialize the auto-check-all presenter.

        Args:
            view: The view passed through to the base presenter.
            registry: The exporter registry passed through to the base.
            dialog: The export dialog to auto-check after each
                ``set_available_tables`` call.
        """
        super().__init__(view, registry)
        self._dialog = dialog

    def set_available_tables(self, names: list[str]) -> None:
        """Push the names through the base presenter, then check every table.

        Args:
            names: The table names being staged for export.

        Returns:
            ``None``.

        Side effects:
            Updates the dialog's checklist and then selects every entry so the
            wiring's downstream ``on_export`` reads a non-empty selection.
        """
        super().set_available_tables(names)
        self._dialog.select_all_tables()


def build_wired(
    qtbot: QtBot,
    *,
    save_path: str | None = "results.db",
    open_path: str | None = "existing.db",
    export_result: tuple[str, str] | None = ("Fake", "out.xlsx"),
    auto_check_all_on_set: bool = False,
) -> tuple[
    MainWindow,
    PipelinePresenter,
    FakePipelineService,
    FakeExporter,
    ExportPresenter,
    ExportDialog,
]:
    """Build a wired main window with fake collaborators for signal tests.

    Args:
        qtbot: pytest-qt fixture used to manage the window's lifetime.
        save_path: Value the save-path chooser returns; ``None`` simulates a
            cancelled file dialog.
        open_path: Value the open-path chooser returns; ``None`` simulates a
            cancelled file dialog.
        export_result: Tuple ``(format_name, destination_path)`` the export
            dialog runner returns on accept, or ``None`` to simulate cancel.
        auto_check_all_on_set: When ``True``, install the
            :class:`AutoCheckAllExportPresenter` so the dialog auto-checks
            every item after the handler populates the checklist. This seam
            lets a single signal emission both populate the list and produce
            a non-empty selection for ``on_export``.

    Returns:
        ``(window, pipeline_presenter, pipeline_service, exporter,
        export_presenter, export_dialog)``.
    """
    window = MainWindow()
    qtbot.addWidget(window)
    populate_widget_paths(window)

    pipeline_service = FakePipelineService(
        import_result=fabricated_imports(),
        run_result={"mix_rollup_4": pd.DataFrame({"value": [1.0]})},
        open_result=fabricated_imports(),
    )
    pipeline_presenter = PipelinePresenter(FakePipelineView(), pipeline_service)

    registry = ExporterRegistry()
    exporter = FakeExporter("Fake")
    registry.register(exporter)
    export_dialog = ExportDialog(registry.available_formats())
    qtbot.addWidget(export_dialog)
    # Choose the test subclass for the auto-check-all path so the wiring's
    # set_available_tables call also produces a non-empty selection. The
    # subclass preserves ExportPresenter's typed contract and keeps Pyright
    # clean without any instance-method monkey-patch.
    export_presenter: ExportPresenter = (
        AutoCheckAllExportPresenter(export_dialog, registry, export_dialog)
        if auto_check_all_on_set
        else ExportPresenter(export_dialog, registry)
    )

    wire_control_signals(
        window,
        pipeline_presenter,
        export_presenter,
        export_dialog,
        save_path_chooser=lambda: save_path,
        open_path_chooser=lambda: open_path,
        export_dialog_runner=lambda _dialog: export_result,
    )
    return (
        window,
        pipeline_presenter,
        pipeline_service,
        exporter,
        export_presenter,
        export_dialog,
    )


def seed_import_spec() -> ImportSpec:
    """Return the canonical import spec the wiring helper would build.

    Returns:
        The :class:`ImportSpec` matching the paths/sheets that
        :func:`populate_widget_paths` seeds onto the main window.
    """
    return ImportSpec(
        le_path="le.xlsx",
        le_sheet="LE-8 + 4",
        aop_path="aop.xlsx",
        aop_sheet="AOP1",
        skulu_path="sku.xlsx",
        skulu_sheet="SKU_LU",
    )
