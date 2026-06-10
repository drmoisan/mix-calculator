"""Tests for the Edit-Schema composition wiring (issue #60 Defect 1).

Verifies that :func:`wire_edit_schema_buttons` connects each source tab's
``edit_schema_requested`` signal to a handler that opens the schema builder and
seeds it from the tab's currently-selected schema via
``schema_builder_presenter.load_existing(<selected name>)``. Also verifies the
guard paths: a placeholder/empty selection short-circuits (no builder opens, no
crash), exercising the #50 no-schema seam. Runs headless under
``QT_QPA_PLATFORM=offscreen`` from :mod:`tests.gui.conftest`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui._schema_discovery_wiring import wire_edit_schema_buttons
from src.gui.main_window import MainWindow
from src.gui.presenters.schema_builder_presenter import SchemaBuilderPresenter
from src.gui.presenters.source_selection_presenter import SourceSelectionPresenter
from src.gui.widgets._columns_tab_drag import ColumnsTabWidget
from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog
from src.schema_matching import MatchResult, MismatchReport
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition, column_ref
from tests.gui.fakes.fake_services import FakeSchemaService, FakeWorkbookReader
from tests.gui.fakes.fake_views import FakeSourceSelectionView

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtWidgets import QWidget
    from pytestqt.qtbot import QtBot

    from src.gui.presenters._schema_builder_state import PreviewSlice


class _RecordingPresenter:
    """Recording schema-builder presenter capturing ``load_existing`` calls.

    Purpose:
        Stand in for the production ``SchemaBuilderPresenter`` so the Edit-Schema
        wiring tests can assert that the selected schema name was seeded via
        ``load_existing`` without constructing the real presenter.

    Attributes:
        loaded: The schema names passed to :meth:`load_existing`, in call order.
    """

    def __init__(self) -> None:
        """Initialize the recorder with an empty call log."""
        self.loaded: list[str] = []

    def load_existing(self, name: str) -> None:
        """Record a ``load_existing`` call.

        Args:
            name: The schema name the wiring seeded the builder from.

        Returns:
            ``None``.
        """
        self.loaded.append(name)


class _RecordingDialog(SchemaBuilderDialog):
    """Schema-builder dialog that records each seeded preview slice.

    Purpose:
        Let the Edit-Schema wiring tests assert which ``preview_slice`` the open
        path seeds into the Columns tab without monkeypatching a bound method.

    Responsibilities:
        Capture every slice passed to :meth:`set_columns_preview_slice` (in call
        order) while still delegating to the real seeding behavior.

    Attributes:
        seeded_slices: The preview slices seeded via the open path, in order.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the recording dialog with an empty capture log.

        Args:
            parent: Optional Qt parent widget forwarded to the base dialog.
        """
        super().__init__(parent)
        self.seeded_slices: list[PreviewSlice | None] = []

    def set_columns_preview_slice(self, preview_slice: PreviewSlice | None) -> None:
        """Record the seeded slice, then delegate to the real seeding behavior.

        Args:
            preview_slice: The preview slice the open path seeds, or ``None``.

        Returns:
            ``None``.
        """
        self.seeded_slices.append(preview_slice)
        super().set_columns_preview_slice(preview_slice)


def _dialog_factory(qtbot: QtBot) -> Callable[[], SchemaBuilderDialog]:
    """Return a recording dialog factory that registers each dialog with qtbot.

    Args:
        qtbot: The pytest-qt bot used to manage dialog lifetime.

    Returns:
        A zero-argument factory building a fresh :class:`SchemaBuilderDialog`.
    """

    def _factory() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        return dialog

    return _factory


def test_edit_with_real_schema_opens_builder_and_calls_load_existing(
    qtbot: QtBot,
) -> None:
    """AC-2: clicking Edit with a real schema opens the builder via load_existing.

    The wiring opens a blank builder through the shared open path (retaining the
    presenter on the window) and then seeds it from the selected schema name via
    ``schema_builder_presenter.load_existing(<name>)``.
    """
    # Arrange: a window whose LE tab has a real schema selected, wired with a
    # recording presenter factory.
    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    presenters: list[_RecordingPresenter] = []

    def presenter_factory(_dialog: object, _service: object) -> object:
        presenter = _RecordingPresenter()
        presenters.append(presenter)
        return presenter

    wire_edit_schema_buttons(
        window,
        service,
        dialog_factory=_dialog_factory(qtbot),
        presenter_factory=presenter_factory,
    )
    window.le_widget.set_schema_list(["le_v1"])
    window.le_widget.set_selected_schema("le_v1")

    # Act: trigger the Edit button exactly as the user would.
    window.le_widget.edit_schema_requested.emit()

    # Assert: a presenter was retained and seeded from the selected schema name.
    assert len(presenters) == 1
    assert window.schema_builder_presenter is presenters[0]
    assert presenters[0].loaded == ["le_v1"]


def test_edit_with_placeholder_short_circuits_without_opening(qtbot: QtBot) -> None:
    """AC-3/AC-9: an Edit emit on the placeholder opens no builder and does not crash.

    Defense in depth alongside the widget-level disabled state: even if the
    ``edit_schema_requested`` signal fires while the placeholder is selected, the
    wiring short-circuits so no builder opens and no presenter is retained.
    """
    # Arrange: a window left on the placeholder selection.
    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    opened: list[object] = []

    def presenter_factory(_dialog: object, _service: object) -> object:
        presenter = _RecordingPresenter()
        opened.append(presenter)
        return presenter

    wire_edit_schema_buttons(
        window,
        service,
        dialog_factory=_dialog_factory(qtbot),
        presenter_factory=presenter_factory,
    )
    assert window.le_widget.current_schema() == "<Choose Schema>"

    # Act: emit the Edit signal while the placeholder is selected.
    window.le_widget.edit_schema_requested.emit()

    # Assert: the guard short-circuited — no builder opened, no presenter retained.
    assert opened == []
    assert window.schema_builder_presenter is None


def test_edit_no_schema_seam_does_not_crash_on_each_tab(qtbot: QtBot) -> None:
    """AC-9: emitting Edit on every tab with no schema selected never crashes (seam).

    Drives the no-schema seam for all three source tabs: with no schema selected,
    each tab's Edit emit short-circuits without opening a builder or raising.
    """
    # Arrange: wire all three tabs with no schema selected on any.
    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    wire_edit_schema_buttons(
        window,
        service,
        dialog_factory=_dialog_factory(qtbot),
        presenter_factory=lambda _d, _s: _RecordingPresenter(),
    )

    # Act: emit Edit on each tab with no schema selected (the no-schema seam).
    window.le_widget.edit_schema_requested.emit()
    window.aop_widget.edit_schema_requested.emit()
    window.skulu_widget.edit_schema_requested.emit()

    # Assert: no builder opened on any tab and no exception propagated.
    assert window.schema_builder_presenter is None


def test_edit_with_stub_presenter_lacking_load_existing_does_not_crash(
    qtbot: QtBot,
) -> None:
    """A retained presenter without ``load_existing`` is tolerated (getattr guard).

    The wiring seeds via ``getattr(presenter, "load_existing", None)`` so a
    recording stub that does not expose the seeding contract simply skips
    seeding rather than raising, mirroring the established ``_seed_presenter``
    tolerance for minimal test factories.
    """

    # Arrange: a presenter factory returning a bare stub with no load_existing.
    class _BarePresenter:
        """A minimal presenter stub exposing no ``load_existing`` method."""

    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    built: list[_BarePresenter] = []

    def presenter_factory(_dialog: object, _service: object) -> object:
        presenter = _BarePresenter()
        built.append(presenter)
        return presenter

    wire_edit_schema_buttons(
        window,
        service,
        dialog_factory=_dialog_factory(qtbot),
        presenter_factory=presenter_factory,
    )
    window.le_widget.set_schema_list(["le_v1"])
    window.le_widget.set_selected_schema("le_v1")

    # Act: trigger Edit with a real schema; the stub lacks load_existing.
    window.le_widget.edit_schema_requested.emit()

    # Assert: the builder still opened (presenter retained) and no crash occurred
    # despite the absent load_existing seeding contract.
    assert len(built) == 1
    assert window.schema_builder_presenter is built[0]


# --- Issue #62: Edit Schema seeds the source pool from real worksheet headers ---


def _matching_schema() -> SchemaDefinition:
    """Return a schema whose canonical names equal the synthetic worksheet headers.

    Returns:
        A :class:`SchemaDefinition` named ``aop_synth`` with Customer/SKU/Jan
        columns matching the synthetic worksheet header tokens used in the tests.
    """
    return SchemaDefinition(
        name="aop_synth",
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="SKU", role="dimension"),
            ColumnSpec(canonical_name="Jan", role="measure", numeric=True),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("Customer", "SKU"))),
    )


def _full_match(schema: SchemaDefinition) -> MatchResult:
    """Return a full-coverage match result selecting ``schema``.

    The Edit open path runs ``best_header_row`` over the preview rows, which calls
    ``service.find_best_match`` per row; the fake returns this configured result so
    the synthetic header row scores above the stray data row and is selected.

    Args:
        schema: The schema the match result selects as the best candidate.

    Returns:
        A :class:`MatchResult` selecting ``schema`` with full coverage and an
        empty mismatch report.
    """
    return MatchResult(
        schema=schema,
        score=1.0,
        report=MismatchReport(unmatched_required=(), unrecognized_actual=()),
    )


def _presenter_with_headers(headers: list[str]) -> SourceSelectionPresenter:
    """Build a source-selection presenter whose reader returns synthetic headers.

    Args:
        headers: The synthetic worksheet header tokens the fake reader returns on
            the first preview row.

    Returns:
        A :class:`SourceSelectionPresenter` carrying a
        :class:`FakeWorkbookReader` configured to return ``headers`` as the
        header row.
    """
    reader = FakeWorkbookReader(preview_rows=[list(headers), ["1", "X", "10"]])
    return SourceSelectionPresenter(FakeSourceSelectionView(), reader)


def test_edit_populates_preview_slice_from_real_worksheet_headers(qtbot: QtBot) -> None:
    """AC-5: Edit reads the selected worksheet's headers into the source pool.

    With a tab presenter carrying a reader that returns synthetic headers and a
    non-blank selected file/sheet, the Edit open path builds a ``preview_slice``
    whose header equals those synthetic headers and seeds the Columns-tab pool.
    """
    # Arrange: synthetic headers that also match the loaded schema's canonical
    # names; the schema service serves that schema by name.
    headers = ["Customer", "SKU", "Jan"]
    schema = _matching_schema()
    service = FakeSchemaService(
        schema_names=[schema.name],
        schemas={schema.name: schema},
        match_result=_full_match(schema),
    )
    window = MainWindow()
    qtbot.addWidget(window)
    presenter = _presenter_with_headers(headers)

    dialogs: list[_RecordingDialog] = []

    def _recording_dialog_factory() -> SchemaBuilderDialog:
        """Build a dialog that records the preview slice the open path seeds."""
        dialog = _RecordingDialog()
        qtbot.addWidget(dialog)
        dialogs.append(dialog)
        return dialog

    wire_edit_schema_buttons(
        window,
        service,
        aop_presenter=presenter,
        dialog_factory=_recording_dialog_factory,
        presenter_factory=lambda dialog, svc: SchemaBuilderPresenter(dialog, svc),
    )
    window.aop_widget.set_schema_list([schema.name])
    window.aop_widget.set_selected_schema(schema.name)
    window.aop_widget.set_path("synthetic.xlsx")
    window.aop_widget.set_current_sheet("AOP1")

    # Act
    window.aop_widget.edit_schema_requested.emit()

    # Assert: a non-empty preview slice carrying the synthetic headers was seeded.
    assert len(dialogs) == 1
    captured = dialogs[0].seeded_slices
    assert len(captured) == 1
    assert captured[0] is not None
    assert captured[0].header == ("Customer", "SKU", "Jan")


def test_edit_renders_matching_canonical_rows_as_assigned(qtbot: QtBot) -> None:
    """AC-6: with a populated pool, name-matching canonical rows render assigned.

    Drives the real dialog + presenter: Edit seeds the Columns-tab source pool
    from the synthetic worksheet headers, then ``load_existing`` re-renders the
    loaded schema's columns; the drag binder rebuilds the pool from the seeded
    slice and fuzzy-prepopulates, so each name-matching canonical row renders its
    matched source column in the assignment label (what the user sees).
    """
    # Arrange: synthetic headers equal to the schema's canonical names.
    headers = ["Customer", "SKU", "Jan"]
    schema = _matching_schema()
    service = FakeSchemaService(
        schema_names=[schema.name],
        schemas={schema.name: schema},
        match_result=_full_match(schema),
    )
    window = MainWindow()
    qtbot.addWidget(window)
    presenter = _presenter_with_headers(headers)
    dialogs: list[SchemaBuilderDialog] = []

    def _dialog_factory_real() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        dialogs.append(dialog)
        return dialog

    wire_edit_schema_buttons(
        window,
        service,
        aop_presenter=presenter,
        dialog_factory=_dialog_factory_real,
        presenter_factory=lambda dialog, svc: SchemaBuilderPresenter(dialog, svc),
    )
    window.aop_widget.set_schema_list([schema.name])
    window.aop_widget.set_selected_schema(schema.name)
    window.aop_widget.set_path("synthetic.xlsx")
    window.aop_widget.set_current_sheet("AOP1")

    # Act
    window.aop_widget.edit_schema_requested.emit()

    # Assert: the rendered Columns tab shows each name-matching canonical row
    # assigned to its synthetic source column (the user-facing assignment).
    assert len(dialogs) == 1
    columns_widget = dialogs[0].findChild(ColumnsTabWidget)
    assert columns_widget is not None
    assert columns_widget.row_assignment_text("Customer") == "Customer"
    assert columns_widget.row_assignment_text("SKU") == "SKU"
    assert columns_widget.row_assignment_text("Jan") == "Jan"


def test_edit_no_file_no_sheet_opens_with_empty_pool_no_reader_call(
    qtbot: QtBot,
) -> None:
    """AC-9: Edit with no file/sheet selected opens an empty pool, no reader call.

    The reader must not be called when the path/sheet are blank, the seeded
    ``preview_slice`` must be ``None`` (empty source pool), and the handler must
    complete without raising — preserving the issue #50 no-file/no-sheet seam.
    """
    # Arrange: a reader that records calls; the widget leaves path/sheet blank.
    reader = FakeWorkbookReader(preview_rows=[["Customer", "SKU", "Jan"]])
    presenter = SourceSelectionPresenter(FakeSourceSelectionView(), reader)
    schema = _matching_schema()
    service = FakeSchemaService(
        schema_names=[schema.name],
        schemas={schema.name: schema},
        match_result=_full_match(schema),
    )
    window = MainWindow()
    qtbot.addWidget(window)

    dialogs: list[_RecordingDialog] = []

    def _recording_dialog_factory() -> SchemaBuilderDialog:
        dialog = _RecordingDialog()
        qtbot.addWidget(dialog)
        dialogs.append(dialog)
        return dialog

    wire_edit_schema_buttons(
        window,
        service,
        aop_presenter=presenter,
        dialog_factory=_recording_dialog_factory,
        presenter_factory=lambda dialog, svc: SchemaBuilderPresenter(dialog, svc),
    )
    window.aop_widget.set_schema_list([schema.name])
    window.aop_widget.set_selected_schema(schema.name)
    # Deliberately leave path/sheet unset (blank) to exercise the no-file seam.

    # Act: this must complete without raising on the blank selection.
    window.aop_widget.edit_schema_requested.emit()

    # Assert: the reader was never called and the seeded slice is None (empty pool).
    assert reader.preview_calls == []
    assert len(dialogs) == 1
    assert dialogs[0].seeded_slices == [None]
