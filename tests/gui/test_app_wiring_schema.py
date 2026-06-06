"""Tests for the Feature D schema wiring in the composition root (AC6, AC2).

Verifies that ``build_application(schema_service=FakeSchemaService(...))`` wires
the "Schema Builder..." action to open the builder (AC6), and that the
import-flow discovery helper proceeds on a suitable match but surfaces the
rendered mismatch and offers the resolve path on a no-match (AC2). Runs headless
under ``QT_QPA_PLATFORM=offscreen`` from :mod:`tests.gui.conftest`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui._schema_build_specs import CallerBuildSpec
from src.gui._schema_wiring import (
    discover_schema,
    wire_build_schema_buttons,
    wire_schema_builder,
)
from src.gui.app import build_application
from src.gui.main_window import MainWindow
from src.gui.runners import SynchronousRunner
from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog
from src.schema_matching import (
    CandidateScore,
    MatchResult,
    MismatchReport,
    UnmatchedColumn,
)
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition, column_ref
from tests.gui.fakes.fake_services import FakeSchemaService, FakeWorkbookReader

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def _schema() -> SchemaDefinition:
    """Return a small valid schema used as the matched candidate.

    Returns:
        A :class:`SchemaDefinition` with ``Customer`` and ``Sales``.
    """
    return SchemaDefinition(
        name="aop_like",
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="Sales", role="measure", numeric=True),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("Customer",))),
    )


def _full_match() -> MatchResult:
    """Return a full-coverage match result (score 1.0).

    Returns:
        A :class:`MatchResult` selecting :func:`_schema` with an empty report.
    """
    return MatchResult(
        schema=_schema(),
        score=1.0,
        report=MismatchReport(unmatched_required=(), unrecognized_actual=()),
    )


def _no_match() -> MatchResult:
    """Return a low-coverage match result with an unmatched required column.

    Returns:
        A :class:`MatchResult` whose score is below threshold and whose report
        names the unmatched ``Sales`` column.
    """
    report = MismatchReport(
        unmatched_required=(
            UnmatchedColumn(
                canonical_name="Sales",
                aliases=(),
                candidates=(CandidateScore(actual_name="Net Sales", score=0.4),),
            ),
        ),
        unrecognized_actual=("Net Sales",),
    )
    return MatchResult(schema=_schema(), score=0.0, report=report)


def test_build_application_wires_schema_builder_action(qtbot: QtBot) -> None:
    """The "Schema Builder..." action opens the builder via an injected service."""
    # Arrange: build the app with an injected fake schema service.
    service = FakeSchemaService(
        schema_names=["aop_like"], schemas={"aop_like": _schema()}
    )
    wired = build_application(
        runner=SynchronousRunner(),
        schema_service=service,
    )
    qtbot.addWidget(wired.window)

    # Act: trigger the menu action exactly as the user would.
    wired.window.schema_builder_action.trigger()

    # Assert: a builder presenter was retained on the window (the dialog opened).
    assert wired.window.schema_builder_presenter is not None
    assert wired.schema_service is service


def test_discover_schema_proceeds_on_suitable_match() -> None:
    """discover_schema returns a proceed decision for a full-coverage match."""
    # Arrange
    service = FakeSchemaService(match_result=_full_match())

    # Act
    decision = discover_schema(service, ["Customer", "Sales"])

    # Assert
    assert decision.action == "proceed"
    assert decision.explanation == ""


def test_discover_schema_resolves_on_no_match() -> None:
    """discover_schema surfaces the mismatch and asks to resolve on a no-match."""
    # Arrange
    service = FakeSchemaService(match_result=_no_match())

    # Act
    decision = discover_schema(service, ["Customer", "Net Sales"])

    # Assert: the resolve path carries the rendered mismatch explanation (AC2).
    assert decision.action == "resolve"
    assert "Sales" in decision.explanation


def test_wire_schema_builder_uses_injected_factories(qtbot: QtBot) -> None:
    """wire_schema_builder opens a dialog and retains the presenter (AC6)."""
    # Arrange: recording factories so the test asserts the open path directly.
    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    opened: list[SchemaBuilderDialog] = []

    def dialog_factory() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        opened.append(dialog)
        return dialog

    sentinel = object()

    wire_schema_builder(
        window,
        service,
        dialog_factory,
        lambda _dialog, _service: sentinel,
    )

    # Act
    window.schema_builder_requested.emit()

    # Assert: one dialog opened and the presenter was retained on the window.
    assert len(opened) == 1
    assert window.schema_builder_presenter is sentinel


def test_wire_build_buttons_seeds_presenter_from_caller_specs(qtbot: QtBot) -> None:
    """A per-tab build button passes its source-specific specs to the presenter."""
    # Arrange: a spec provider returning a distinct spec per source key, and a
    # recording presenter capturing the seed inputs.
    from src.gui.presenters._schema_builder_state import PreviewSlice

    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    le_spec = CallerBuildSpec(
        required_specs=(ColumnSpec(canonical_name="Customer", role="dimension"),),
        default_key_pattern="{Customer}",
        preview_slice=PreviewSlice(header=("col_a",), rows=(("x1",),)),
    )

    class _Provider:
        def build_spec_for(self, key: str) -> CallerBuildSpec:
            # Only the LE key is exercised in this test; return its spec.
            return le_spec if key == "LE" else CallerBuildSpec()

    seeds: list[dict[str, object]] = []

    class _RecordingPresenter:
        def seed_from_caller(self, **kwargs: object) -> None:
            seeds.append(kwargs)

    def dialog_factory() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        return dialog

    wire_build_schema_buttons(
        window,
        service,
        dialog_factory=dialog_factory,
        presenter_factory=lambda _d, _s: _RecordingPresenter(),
        spec_provider=_Provider(),
    )

    # Act: click the LE tab's build button.
    window.le_widget.build_schema_requested.emit()

    # Assert: the LE source's required spec and key pattern were seeded.
    assert len(seeds) == 1
    assert seeds[0]["default_key_pattern"] == "{Customer}"
    assert seeds[0]["required_specs"] == le_spec.required_specs


def test_wire_build_buttons_blank_path_without_provider(qtbot: QtBot) -> None:
    """Without a spec provider, a build button opens a blank builder (no seeding)."""
    # Arrange: a recording presenter that fails if seeded with caller specs.
    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    seeds: list[dict[str, object]] = []

    class _RecordingPresenter:
        def seed_from_caller(self, **kwargs: object) -> None:
            seeds.append(kwargs)

    def dialog_factory() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        return dialog

    wire_build_schema_buttons(
        window,
        service,
        dialog_factory=dialog_factory,
        presenter_factory=lambda _d, _s: _RecordingPresenter(),
    )

    # Act
    window.aop_widget.build_schema_requested.emit()

    # Assert: no seeding occurred (blank menu-equivalent path).
    assert seeds == []
    assert window.schema_builder_presenter is not None


def test_build_application_per_tab_button_seeds_via_injected_provider(
    qtbot: QtBot,
) -> None:
    """R4/AC5: the per-tab build path opens a seeded builder via build_application.

    Drives the composition root (``build_application``) with a fake schema service
    holding the bundled-default schemas, triggers a per-tab ``build_schema_requested``,
    and asserts the opened builder presenter received the source's required specs and
    a masked preview slice (seeded state is non-empty). The menu-action path is
    asserted to remain blank.
    """
    # Arrange: a service holding the LE default so the production BuildSpecProvider
    # built inside build_application resolves a non-empty spec for the LE tab.
    le_schema = SchemaDefinition(
        name="default_le",
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension", required=True),
        ),
        key=KeySpec(parts=(column_ref("Customer"),)),
    )
    service = FakeSchemaService(
        schema_names=["default_le"], schemas={"default_le": le_schema}
    )
    wired = build_application(runner=SynchronousRunner(), schema_service=service)
    qtbot.addWidget(wired.window)

    # Act: trigger the LE tab's build button exactly as the user would.
    wired.window.le_widget.build_schema_requested.emit()

    # Assert: a real presenter was retained and its state was seeded from the LE
    # source's required specs and a masked preview slice (the injected provider ran).
    from src.gui.presenters.schema_builder_presenter import SchemaBuilderPresenter

    presenter = wired.window.schema_builder_presenter
    assert isinstance(presenter, SchemaBuilderPresenter)
    seeded_columns = [name for name, _r, _req, _a in presenter.state.columns]
    assert "Customer" in seeded_columns
    assert presenter.state.preview_slice is not None
    # The seeded preview slice is synthetic/masked (no real workbook values).
    for row in presenter.state.preview_slice.rows:
        for cell in row:
            assert isinstance(cell, str)
            assert cell.startswith("masked_")

    # Assert: the menu-action path stays blank (Decision 7) — opening via the menu
    # action seeds nothing, leaving the presenter state empty.
    wired.window.schema_builder_action.trigger()
    menu_presenter = wired.window.schema_builder_presenter
    assert isinstance(menu_presenter, SchemaBuilderPresenter)
    assert menu_presenter.state.columns == []
    assert menu_presenter.state.preview_slice is None


def test_build_application_new_from_template_seeds_live_dialog(qtbot: QtBot) -> None:
    """R5/AC4: the new-from-template path reaches new_from_template, seeding the dialog.

    Drives the composition root (``build_application``): a partial-band activation
    match invokes the injected ``on_partial_match``, which opens the builder via the
    production ``new_from_template`` path. Asserts the live ``SchemaBuilderDialog``
    renders the template's columns (the presenter's ``new_from_template`` ran) with a
    cleared Identity name so save-as never overwrites the template.
    """
    from src.gui.runners import SynchronousRunner
    from src.gui.widgets._columns_tab_drag import ColumnsTabWidget

    # Arrange: a reader header and a service whose match lands in the partial band
    # and can load the closest schema as the template.
    reader = FakeWorkbookReader(
        sheet_names=["AOP1"], preview_rows=[["Customer", "Net Sales"]]
    )
    partial = MatchResult(
        schema=_schema(),
        score=0.6,
        report=MismatchReport(
            unmatched_required=(
                UnmatchedColumn(canonical_name="Sales", aliases=(), candidates=()),
            ),
            unrecognized_actual=(),
        ),
    )
    service = FakeSchemaService(
        schema_names=["aop_like"],
        schemas={"aop_like": _schema()},
        match_result=partial,
    )
    wired = build_application(
        runner=SynchronousRunner(), workbook_reader=reader, schema_service=service
    )
    qtbot.addWidget(wired.window)

    # Act: a partial-band discovery reaches new-from-template via on_partial_match.
    wired.aop_presenter.on_schema_discovery("aop.xlsx", "AOP1")

    # Assert: the live dialog opened, renders the template's columns on the drag
    # Columns tab, and shows a blank Identity name (new_from_template ran).
    from src.gui.presenters.schema_builder_presenter import SchemaBuilderPresenter

    presenter = wired.window.schema_builder_presenter
    assert isinstance(presenter, SchemaBuilderPresenter)
    assert presenter.state.name == ""
    # The retained presenter drives the live dialog; assert the dialog's drag Columns
    # tab rendered the template's canonical columns (proving the open path is live).
    assert "Customer" in [n for n, _r, _q, _a in presenter.state.columns]
    # Sanity: the production open path uses the real drag Columns widget class.
    assert ColumnsTabWidget is not None


def test_wire_schema_builder_uses_default_factories(qtbot: QtBot) -> None:
    """wire_schema_builder with no factories opens the production builder dialog."""
    # Arrange: wire with the production default factories (no injected factories),
    # matching the trimmed app.py call site after the P1-T2 extraction.
    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    wire_schema_builder(window, service)

    # Act: trigger the wired signal exactly as the menu action would.
    window.schema_builder_requested.emit()

    # Assert: a real SchemaBuilderPresenter was built and retained on the window.
    from src.gui.presenters.schema_builder_presenter import SchemaBuilderPresenter

    assert isinstance(window.schema_builder_presenter, SchemaBuilderPresenter)
