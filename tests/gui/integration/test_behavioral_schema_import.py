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
