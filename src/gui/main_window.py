"""Main window shell hosting the three source widgets and the control buttons.

This passive Qt main window assembles the GUI: three :class:`SourceInputWidget`
instances (LE/AOP/SKU_LU), a preview panel, and the Import / Import-All / Run /
Save / Open / Export controls. It is a thin shell — collaborators are constructor
injected; no services are constructed inside it.

The shell exposes:
    - ``le_widget``, ``aop_widget``, ``skulu_widget`` for the three per-input
      source widgets.
    - ``preview_widget`` for the shared tab preview.
    - Signals fired by the control buttons: ``import_one_requested`` (per input),
      ``import_all_requested``, ``run_requested``, ``save_requested``,
      ``open_db_requested``, ``export_requested``.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.gui.widgets.preview_widget import PreviewWidget
from src.gui.widgets.source_input_widget import SourceInputWidget

__all__ = ["MainWindow"]

# Spec defaults for the three per-input source widgets.
_LE_DEFAULT_SHEET = "LE-8 + 4"
_AOP_DEFAULT_SHEET = "AOP1"
_SKULU_DEFAULT_SHEET = "SKU_LU"


class MainWindow(QMainWindow):
    """Composition shell for the mix-pipeline GUI.

    Purpose:
        Lay out the three per-input source widgets, the preview panel, and the
        Import/Run/Save/Open/Export control row; emit signals for each button.

    Responsibilities:
        Build the UI and expose collaborator widgets and signals; it constructs
        no services and holds no transform logic.

    Usage:
        Constructed at the composition root with an optional pre-built
        :class:`PreviewWidget` (test injection) or a default one.
        Presenters/workers are wired in :mod:`src.gui.app`.

    Attributes:
        le_widget, aop_widget, skulu_widget: The three per-input source widgets.
            Each owns its per-input Import button (issue #27 AC11).
        preview_widget: The shared tab-preview widget.
        import_le_btn, import_aop_btn, import_skulu_btn: Read-only properties
            resolving to each widget's owned Import button (issue #27 AC13), so
            existing callers (the view adapter, tests) keep working unchanged.
        import_one_requested: Emitted with the import key on a per-input import.
        import_all_requested: Emitted on Import-All.
        run_requested: Emitted on Run.
        save_requested: Emitted on Save.
        open_db_requested: Emitted on Open.
        export_requested: Emitted on Export.
        schema_builder_requested: Emitted when the "Schema Builder..." menu
            action is triggered (Feature D, AC6).
    """

    import_one_requested: Signal = Signal(str)
    import_all_requested: Signal = Signal()
    run_requested: Signal = Signal()
    save_requested: Signal = Signal()
    open_db_requested: Signal = Signal()
    export_requested: Signal = Signal()
    schema_builder_requested: Signal = Signal()

    def __init__(self, preview_widget: PreviewWidget | None = None) -> None:
        """Build the main window UI.

        Args:
            preview_widget: Optional pre-built preview widget. When ``None`` a
                default :class:`PreviewWidget` is constructed so tests can drive
                the shell without supplying one.
        """
        super().__init__()
        self.setWindowTitle("Mix Pipeline GUI")

        # Per-input source widgets with the spec default sheet names pre-filled.
        # Each widget owns its per-input Import button (issue #27 AC11); the
        # button label matches the prior standalone control's text.
        self.le_widget = SourceInputWidget(
            "LE", default_sheet=_LE_DEFAULT_SHEET, import_label="Import LE"
        )
        self.aop_widget = SourceInputWidget(
            "AOP", default_sheet=_AOP_DEFAULT_SHEET, import_label="Import AOP"
        )
        self.skulu_widget = SourceInputWidget(
            "SKU_LU", default_sheet=_SKULU_DEFAULT_SHEET, import_label="Import SKU_LU"
        )

        # Shared preview panel; tests can inject a fake-equivalent.
        self.preview_widget = (
            preview_widget if preview_widget is not None else PreviewWidget()
        )

        # Control buttons drive the pipeline actions via signals. The three
        # per-input Import buttons now live inside their source widgets (issue
        # #27 AC12); only Import All and the global actions remain in the row.
        self.import_all_btn = QPushButton("Import All")
        self.run_btn = QPushButton("Run")
        self.save_btn = QPushButton("Save...")
        self.open_btn = QPushButton("Open...")
        self.export_btn = QPushButton("Export...")

        sources_column = QVBoxLayout()
        sources_column.addWidget(self.le_widget)
        sources_column.addWidget(self.aop_widget)
        sources_column.addWidget(self.skulu_widget)

        controls_row = QHBoxLayout()
        controls_row.addWidget(self.import_all_btn)
        controls_row.addWidget(self.run_btn)
        controls_row.addWidget(self.save_btn)
        controls_row.addWidget(self.open_btn)
        controls_row.addWidget(self.export_btn)

        body = QVBoxLayout()
        body.addLayout(sources_column)
        body.addWidget(self.preview_widget)
        body.addLayout(controls_row)

        central = QWidget()
        central.setLayout(body)
        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

        # Additive menu surface (Feature D): a Tools menu with a "Schema
        # Builder..." action that emits schema_builder_requested. The action is
        # stored so tests can trigger it directly without driving the menu bar UI.
        self.schema_builder_action = QAction("Schema Builder...", self)
        tools_menu = self.menuBar().addMenu("Tools")
        tools_menu.addAction(self.schema_builder_action)
        self.schema_builder_action.triggered.connect(self.schema_builder_requested.emit)
        # Holder for the schema-builder presenter retained while its dialog is
        # open (set by the composition root's _schema_wiring). Declared here so
        # the attribute is typed rather than dynamically attached.
        self.schema_builder_presenter: object | None = None

        # Wire each widget-owned Import button to emit import_one_requested with
        # its key, and each global control button to its named signal, so the
        # composition root connects a single emitter per action.
        self.le_widget.import_btn.clicked.connect(
            lambda: self.import_one_requested.emit("LE")
        )
        self.aop_widget.import_btn.clicked.connect(
            lambda: self.import_one_requested.emit("aop")
        )
        self.skulu_widget.import_btn.clicked.connect(
            lambda: self.import_one_requested.emit("sku_lu")
        )
        self.import_all_btn.clicked.connect(self.import_all_requested.emit)
        self.run_btn.clicked.connect(self.run_requested.emit)
        self.save_btn.clicked.connect(self.save_requested.emit)
        self.open_btn.clicked.connect(self.open_db_requested.emit)
        self.export_btn.clicked.connect(self.export_requested.emit)

    @property
    def import_le_btn(self) -> QPushButton:
        """Return the LE Import button (owned by ``le_widget``, issue #27 AC13)."""
        return self.le_widget.import_btn

    @property
    def import_aop_btn(self) -> QPushButton:
        """Return the AOP Import button (owned by ``aop_widget``, issue #27 AC13)."""
        return self.aop_widget.import_btn

    @property
    def import_skulu_btn(self) -> QPushButton:
        """Return the SKU_LU Import button (owned by ``skulu_widget``, AC13)."""
        return self.skulu_widget.import_btn

    def set_status(self, message: str) -> None:
        """Display a status-bar message.

        Args:
            message: The message to show in the status bar.

        Returns:
            ``None``.

        Side effects:
            Sets the status bar text.
        """
        status_bar = self.statusBar()
        status_bar.showMessage(message)
