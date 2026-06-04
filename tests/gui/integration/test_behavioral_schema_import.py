"""Behavioral schema-import integration tests (Feature D, AC1 + AC2).

Exercises the schema-aware import path end-to-end through the composition root
with fakes. The AC1 parity assertion confirms the known-file path is unchanged:
for a known AOP fixture and a known LE fixture, the schema-aware import flow
produces a frame identical to the current default loader output on the same
fixture. The AC2 assertion confirms a non-matching header set surfaces the
mismatch report and offers the resolve (manual-match / build) path. Uses in-repo
fixtures only; no temp files, no network, no real DB.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pandas.testing import assert_frame_equal

from src import load_aop, normalize_le
from src.gui._schema_wiring import discover_schema
from src.gui.pipeline_service import PipelineService
from src.pandas_io import read_excel_sheet
from src.schema_matching import MatchResult, MismatchReport, UnmatchedColumn
from src.schema_registry import DiskSchemaFileStore, SchemaRegistry

# The in-memory fixtures live in the tests package and import as package modules.
from tests import aop_fixtures, le_fixtures
from tests.gui.fakes.fake_services import FakeSchemaService

if TYPE_CHECKING:
    import pytest
    from pytestqt.qtbot import QtBot

    from src.schema_model import SchemaDefinition

_MONTHS_A: list[float] = [
    10.0,
    20.0,
    30.0,
    40.0,
    50.0,
    60.0,
    70.0,
    80.0,
    90.0,
    100.0,
    110.0,
    120.0,
]
_MONTHS_B: list[float] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]


def _default(name: str) -> SchemaDefinition:
    """Load a bundled default schema by name through a real disk store.

    Args:
        name: The bundled schema name (``"default_aop"`` or ``"default_le"``).

    Returns:
        The parsed :class:`SchemaDefinition`.
    """
    registry = SchemaRegistry(Path("."), DiskSchemaFileStore())
    return registry.load_bundled_default(name)


def test_ac1_known_aop_file_parity() -> None:
    """The schema-aware AOP import matches the default loader output (AC1)."""
    # Arrange: a known AOP fixture workbook and its default-loader output.
    rows = [
        aop_fixtures.make_aop_row(customer="A", sku="1", type_="Net", months=_MONTHS_A),
        aop_fixtures.make_aop_row(customer="B", sku="2", type_="Net", months=_MONTHS_B),
    ]
    protected = load_aop.load_aop(
        aop_fixtures.build_aop_workbook(rows), sheet="AOP1", key_mismatch="overwrite"
    )
    raw_frame = read_excel_sheet(
        aop_fixtures.build_aop_workbook(rows), sheet_name="AOP1", header=2
    )

    # Act: drive the schema-aware path with the bundled default AOP schema.
    service = PipelineService()
    schema_output = service.import_with_schema(raw_frame, _default("default_aop"))

    # Assert: the schema-aware output is identical to the default loader output.
    assert_frame_equal(schema_output, protected, check_dtype=True)


def test_ac1_known_le_file_parity() -> None:
    """The schema-aware LE import matches the default loader output (AC1)."""
    # Arrange: a known LE fixture workbook and its default-loader output.
    rows = [
        le_fixtures.make_row(
            customer="A", sku="1", type_="Net", ppg="P1", months=_MONTHS_A
        ),
        le_fixtures.make_row(
            customer="A", sku="1", type_="Net", ppg="P1", months=_MONTHS_B
        ),
        le_fixtures.make_row(
            customer="B", sku="2", type_="Net", ppg="P2", months=_MONTHS_A
        ),
        le_fixtures.make_row(
            customer="B", sku="2", type_="Net", ppg="P2", months=_MONTHS_B
        ),
    ]
    protected = normalize_le.normalize(
        normalize_le.load_source(
            le_fixtures.build_workbook(rows), "LE-8 + 4", key_mismatch="overwrite"
        )
    )
    raw_frame = read_excel_sheet(
        le_fixtures.build_workbook(rows), sheet_name="LE-8 + 4", header=2
    )

    # Act
    service = PipelineService()
    schema_output = service.import_with_schema(raw_frame, _default("default_le"))

    # Assert
    assert_frame_equal(schema_output, protected, check_dtype=True)


def test_ac2_non_matching_headers_surface_mismatch_and_resolve() -> None:
    """A non-matching header set surfaces the report and offers the resolve path."""
    # Arrange: a no-match result naming an unmatched required column.
    report = MismatchReport(
        unmatched_required=(
            UnmatchedColumn(canonical_name="Sales", aliases=(), candidates=()),
        ),
        unrecognized_actual=("Mystery Column",),
    )
    service = FakeSchemaService(
        match_result=MatchResult(schema=None, score=0.0, report=report)
    )

    # Act: discovery on an unrelated header set.
    decision = discover_schema(service, ["Mystery Column"])

    # Assert: the import flow must resolve, and the rendered explanation names
    # both the unmatched required column and the unrecognized header (AC2).
    assert decision.action == "resolve"
    assert "Sales" in decision.explanation
    assert "Mystery Column" in decision.explanation


def test_build_new_schema_button_opens_builder(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WS2/AC-13: a per-tab 'Build new schema' button opens the builder dialog.

    Patches the schema builder dialog at its import location so no real dialog
    opens; asserts that clicking a source tab's build button constructs the
    builder and retains its presenter on the window (the open path).
    """
    from src.gui.app import build_application
    from src.gui.runners import SynchronousRunner

    # Arrange: record dialog construction by patching the dialog at its (lazy)
    # import location used by the wiring's default factories.
    opened: list[object] = []

    class _FakeDialog:
        def __init__(self) -> None:
            opened.append(self)

        def show(self) -> None:
            return None

    monkeypatch.setattr(
        "src.gui.widgets.schema_builder_dialog.SchemaBuilderDialog",
        _FakeDialog,
        raising=True,
    )
    wired = build_application(
        runner=SynchronousRunner(), schema_service=FakeSchemaService()
    )
    qtbot.addWidget(wired.window)

    # Act: click the AOP tab's "Build new schema" button.
    wired.window.aop_widget.build_schema_btn.click()

    # Assert: exactly one builder dialog was opened and a presenter retained.
    assert len(opened) == 1
    assert wired.window.schema_builder_presenter is not None


def test_end_to_end_schema_flow_auto_select_placeholder_and_build(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end schema flow: auto-select, placeholder, and build-new (AC-11/12/13).

    A matching header preview auto-selects the matched schema; a non-matching
    preview leaves the ``<Choose Schema>`` placeholder; the build button opens
    the existing builder dialog. Driven through the composition root with fakes.
    """
    from src.gui.app import build_application
    from src.gui.runners import SynchronousRunner
    from tests.gui.fakes.fake_services import FakeWorkbookReader

    # Arrange: patch the builder dialog at its lazy import location.
    opened: list[object] = []

    class _FakeDialog:
        def __init__(self) -> None:
            opened.append(self)

        def show(self) -> None:
            return None

    monkeypatch.setattr(
        "src.gui.widgets.schema_builder_dialog.SchemaBuilderDialog",
        _FakeDialog,
        raising=True,
    )
    # A reader returning a header row, and a service that proceeds on a match.
    reader = FakeWorkbookReader(
        sheet_names=["AOP1"], preview_rows=[["Customer", "Sales"]]
    )
    full = MatchResult(
        schema=_match_schema(),
        score=1.0,
        report=MismatchReport(unmatched_required=(), unrecognized_actual=()),
    )
    service = FakeSchemaService(match_result=full)
    wired = build_application(
        runner=SynchronousRunner(),
        workbook_reader=reader,
        schema_service=service,
    )
    qtbot.addWidget(wired.window)

    # Act 1: a matching preview auto-selects the matched schema on the AOP tab.
    wired.aop_presenter.on_schema_discovery("aop.xlsx", "AOP1")

    # Assert 1: the matched schema name is selected in the AOP widget (AC-11).
    assert wired.window.aop_widget.current_schema() == "aop_like"

    # Act 2: a non-matching preview on the LE tab leaves the placeholder.
    reader.preview_rows = [["Customer", "Net Sales"]]
    service.match_result = MatchResult(
        schema=_match_schema(),
        score=0.0,
        report=MismatchReport(
            unmatched_required=(
                UnmatchedColumn(canonical_name="Sales", aliases=(), candidates=()),
            ),
            unrecognized_actual=("Net Sales",),
        ),
    )
    wired.le_presenter.on_schema_discovery("le.xlsx", "LE-8 + 4")

    # Assert 2: the LE widget stays at the placeholder (AC-12).
    assert wired.window.le_widget.current_schema() == "<Choose Schema>"

    # Act 3: the build button opens the existing builder dialog.
    wired.window.skulu_widget.build_schema_btn.click()

    # Assert 3: a builder dialog opened (AC-13).
    assert len(opened) == 1


def _match_schema() -> SchemaDefinition:
    """Return a small valid schema named ``aop_like`` for the auto-select flow."""
    from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition

    return SchemaDefinition(
        name="aop_like",
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="Sales", role="measure", numeric=True),
        ),
        key=KeySpec(columns=("Customer",)),
    )
