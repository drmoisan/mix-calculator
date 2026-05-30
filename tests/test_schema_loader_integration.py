"""Integration tests: SchemaLoader output through pipeline transforms (Issue #43).

Feeds the SchemaLoader output and the protected-loader output through the same
existing pipeline transforms (``mix_transforms.pivot_aop`` and ``pivot_le``) and
asserts the transform produces the same result either way (AC8). This confirms
the configurable loader is a drop-in for the protected loaders downstream. Uses
in-memory fixtures only; no temp files, no network.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pandas.testing import assert_frame_equal

from src import load_aop, mix_transforms, normalize_le
from src.pandas_io import read_excel_sheet
from src.schema_loader import SchemaLoader
from src.schema_registry import DiskSchemaFileStore, SchemaRegistry

# The in-memory fixtures live in the tests package and import as package modules.
from tests import aop_fixtures, le_fixtures

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
        name: The bundled schema name.

    Returns:
        The parsed :class:`SchemaDefinition`.
    """
    registry = SchemaRegistry(Path("."), DiskSchemaFileStore())
    return registry.load_bundled_default(name)


def test_le_loader_output_through_pivot_le_matches_protected() -> None:
    """pivot_le yields the same result from SchemaLoader and normalize outputs (AC8)."""
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
    raw_frame = read_excel_sheet(
        le_fixtures.build_workbook(rows), sheet_name="LE-8 + 4", header=2
    )
    protected = normalize_le.normalize(
        normalize_le.load_source(
            le_fixtures.build_workbook(rows), "LE-8 + 4", key_mismatch="overwrite"
        )
    )
    loader_output = SchemaLoader(_default("default_le")).load(raw_frame)
    # The transform output must be identical whichever loader produced the input.
    assert_frame_equal(
        mix_transforms.pivot_le(loader_output),
        mix_transforms.pivot_le(protected),
        check_dtype=True,
    )


def test_aop_loader_output_through_pivot_aop_matches_protected() -> None:
    """pivot_aop yields the same result from SchemaLoader and load_aop outputs (AC8)."""
    rows = [
        aop_fixtures.make_aop_row(customer="A", sku="1", type_="Net", months=_MONTHS_A),
        aop_fixtures.make_aop_row(customer="B", sku="2", type_="Net", months=_MONTHS_B),
    ]
    raw_frame = read_excel_sheet(
        aop_fixtures.build_aop_workbook(rows), sheet_name="AOP1", header=2
    )
    protected = load_aop.load_aop(
        aop_fixtures.build_aop_workbook(rows), sheet="AOP1", key_mismatch="overwrite"
    )
    loader_output = SchemaLoader(_default("default_aop")).load(raw_frame)
    assert_frame_equal(
        mix_transforms.pivot_aop(loader_output),
        mix_transforms.pivot_aop(protected),
        check_dtype=True,
    )
