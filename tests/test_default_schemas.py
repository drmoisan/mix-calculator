"""Structural parity tests for the bundled default AOP and LE schemas.

Asserts that ``default_aop.schema.json`` and ``default_le.schema.json`` parse
into ``SchemaDefinition`` objects whose declared columns, column order, key,
dedup policy, derived definitions, fill rules, drop columns, and sentinel-clean
labels match the canonical AOP/LE sets documented in ``_load_aop_helpers.py`` and
``normalize_le.py`` (AC7).

The bundled JSON text is read once via a packaged-resource read at module load
(the committed ``src/schemas/*.json`` files are fixtures, not temp files), then
served to the registry through an in-memory file store so no SQLite/Excel I/O or
temp files occur during the tests themselves.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.schema_model import SchemaDefinition
from src.schema_registry import SCHEMA_SUFFIX, SchemaRegistry

# Canonical column order for AOP, mirroring SOURCE_COLUMNS in _load_aop_helpers.py
# (KEY, identity/dimensions, the twelve months, YTD, the four quarters, YTG, and
# the two label columns).
_MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
_QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

_AOP_COLUMNS = [
    "KEY",
    "Customer",
    "SKU Descripiton",
    "SKU #",
    "Customer Master",
    "Type",
    *_MONTHS,
    "YTD",
    *_QUARTERS,
    "YTG",
    "Super Category",
    "PPG",
]

# Canonical declared column set for LE, mirroring SOURCE_COLUMNS in
# normalize_le.py (the leading YTD/YTG discriminator is declared so it can be the
# dedup discriminator and a drop column).
_LE_COLUMNS = [
    "KEY",
    "YTD/YTG",
    "Customer",
    "SKU Descripiton",
    "SKU #",
    "Type",
    "GtN Mapping",
    *_MONTHS,
    "FY",
    *_QUARTERS,
    "Super Category",
    "PPG",
]

# The packaged schemas directory beside the source modules. Reading these
# committed JSON fixtures once is the only allowed read in this test module.
_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "src" / "schemas"


def _load_bundled(name: str) -> SchemaDefinition:
    """Load a bundled schema by reading its committed JSON text into a fake store.

    Args:
        name: The bundled schema name (without the ``.schema.json`` suffix).

    Returns:
        The parsed ``SchemaDefinition``.
    """

    # Minimal in-memory store seeded from the committed package resource so the
    # registry parses the same bytes that ship in the package without disk I/O
    # inside the registry itself.
    class _Store:
        def __init__(self, text: str, path: Path) -> None:
            self._text = text
            self._path = path.as_posix()

        def list_files(
            self, directory: Path
        ) -> list[str]:  # noqa: ARG002 - match SchemaFileStore API
            return [f"{name}{SCHEMA_SUFFIX}"]

        def read_text(
            self, path: Path
        ) -> str:  # noqa: ARG002 - match SchemaFileStore API
            return self._text

        def write_text(
            self, path: Path, text: str
        ) -> None:  # noqa: ARG002 - match SchemaFileStore API
            raise AssertionError("bundled-default tests do not write")

        def exists(self, path: Path) -> bool:
            return path.as_posix() == self._path

    bundled_dir = Path("/bundled")
    bundled_path = bundled_dir / f"{name}{SCHEMA_SUFFIX}"
    text = (_SCHEMAS_DIR / f"{name}{SCHEMA_SUFFIX}").read_text(encoding="utf-8")
    store = _Store(text, bundled_path)
    registry = SchemaRegistry(Path("/reg"), store, bundled_dir=bundled_dir)
    return registry.load_bundled_default(name)


def test_aop_columns_and_order_match_canonical() -> None:
    """The AOP schema declares the canonical columns in source order."""
    # Arrange / Act
    schema = _load_bundled("default_aop")

    # Assert
    assert [column.canonical_name for column in schema.columns] == _AOP_COLUMNS


def test_aop_key_dedup_and_no_derived() -> None:
    """AOP uses the Customer/SKU #/Type key, no collapse, and no derived columns."""
    # Arrange / Act
    schema = _load_bundled("default_aop")

    # Assert
    assert schema.key.column_names == ("Customer", "SKU #", "Type")
    assert schema.key.sku_coercion is True
    assert schema.dedup.mode == "none"
    assert schema.derived_columns == ()
    assert schema.drop_columns == ()


def test_aop_sentinel_clean_labels() -> None:
    """AOP marks the Super Category and PPG label columns for sentinel cleaning."""
    # Arrange / Act
    schema = _load_bundled("default_aop")

    # Assert
    sentinel = {c.canonical_name for c in schema.columns if c.sentinel_clean}
    assert sentinel == {"Super Category", "PPG"}


def test_aop_fill_rules_cover_ytd_quarters_and_ytg() -> None:
    """AOP fill rules cover YTD (Jan..Dec), each quarter, and YTG (May..Dec)."""
    # Arrange / Act
    schema = _load_bundled("default_aop")

    # Assert
    rules = {rule.total: rule.components for rule in schema.fill_rules}
    assert rules["YTD"] == tuple(_MONTHS)
    assert rules["Q1"] == ("Jan", "Feb", "Mar")
    assert rules["Q4"] == ("Oct", "Nov", "Dec")
    assert rules["YTG"] == tuple(_MONTHS[4:])


def test_le_columns_and_order_match_canonical() -> None:
    """The LE schema declares the canonical columns in source order."""
    # Arrange / Act
    schema = _load_bundled("default_le")

    # Assert
    assert [column.canonical_name for column in schema.columns] == _LE_COLUMNS


def test_le_key_and_sku_coercion() -> None:
    """LE uses the Customer/SKU #/Type key with SKU coercion."""
    # Arrange / Act
    schema = _load_bundled("default_le")

    # Assert
    assert schema.key.column_names == ("Customer", "SKU #", "Type")
    assert schema.key.sku_coercion is True


def test_le_collapse_dedup_is_additive_over_sum_columns() -> None:
    """LE aggregates on YTD/YTG with additive aggregation over the SUM_COLUMNS."""
    # Arrange / Act
    schema = _load_bundled("default_le")

    # Assert: Decision 1 renamed the collapsing mode to ``aggregate``.
    assert schema.dedup.mode == "aggregate"
    assert schema.dedup.discriminator_column == "YTD/YTG"
    aggregated = {agg.measure for agg in schema.dedup.measure_aggregations}
    assert aggregated == {*_MONTHS, "FY", *_QUARTERS}
    # Every aggregation is additive, matching the summed collapse in normalize_le.
    assert all(agg.mode == "additive" for agg in schema.dedup.measure_aggregations)


def test_le_derived_ytg_and_super_category_quirk() -> None:
    """LE derives YTG = sum(May..Dec) and copies Super Category from PPG."""
    # Arrange / Act
    schema = _load_bundled("default_le")

    # Assert
    derived = {d.name: d for d in schema.derived_columns}
    # YTG is a computed measure; the expression is stored verbatim (not evaluated
    # here) and names the May..Dec months under the 8+4 rule.
    assert "YTG" in derived
    for month in _MONTHS[4:]:
        assert month in derived["YTG"].expression
    # The as-built quirk: Super Category is populated directly from PPG.
    assert "Super Category" in derived
    assert derived["Super Category"].copy_from == "PPG"


def test_le_drops_ytd_ytg_source_column() -> None:
    """LE excludes YTD/YTG from output by in_output=false, not by drop_columns.

    The discriminator is required:false (located by name, not source-required),
    in_output:false (carried through dedup but excluded from the output by
    inclusion), and drop_columns is empty (no column is required only to be
    dropped).
    """
    # Arrange / Act
    schema = _load_bundled("default_le")

    # Assert: output exclusion is now expressed by in_output, and the schema no
    # longer names the column in drop_columns.
    assert schema.drop_columns == ()
    ytd_ytg = next(c for c in schema.columns if c.canonical_name == "YTD/YTG")
    assert ytd_ytg.required is False
    assert ytd_ytg.in_output is False


def test_le_fill_rules_cover_fy_and_quarters() -> None:
    """LE fill rules cover FY (Jan..Dec) and each quarter from its months."""
    # Arrange / Act
    schema = _load_bundled("default_le")

    # Assert
    rules = {rule.total: rule.components for rule in schema.fill_rules}
    assert rules["FY"] == tuple(_MONTHS)
    assert rules["Q2"] == ("Apr", "May", "Jun")
    # LE has no YTD fill rule (YTD/YTG is a discriminator, not a total).
    assert "YTD" not in rules


@pytest.mark.parametrize("name", ["default_aop", "default_le"])
def test_bundled_schema_parses_without_raising(name: str) -> None:
    """Both bundled schemas parse into SchemaDefinition objects."""
    # Arrange / Act
    schema = _load_bundled(name)

    # Assert
    assert isinstance(schema, SchemaDefinition)
    assert schema.name == name


def test_bundled_defaults_are_format_2_0_with_structured_key_parts() -> None:
    """P12-T4: bundled defaults are version 2.0 with structured column-ref key parts."""
    from src.schema_model import SCHEMA_FORMAT_VERSION

    # Both bundled schemas migrated forward to the current write format.
    for name in ("default_le", "default_aop"):
        schema = _load_bundled(name)
        assert schema.version == SCHEMA_FORMAT_VERSION
        # The structured key carries column-ref parts (not a flat columns list).
        assert all(part.kind == "column-ref" for part in schema.key.parts)
        assert schema.key.column_names == ("Customer", "SKU #", "Type")


def test_le_default_uses_aggregate_dedup_mode() -> None:
    """P12-T4: the migrated LE default uses the aggregate dedup mode (Decision 1)."""
    schema = _load_bundled("default_le")
    assert schema.dedup.mode == "aggregate"


def test_bundled_numeric_columns_have_float_expected_dtype() -> None:
    """P12-T4: numeric columns carry expected_dtype float after migration."""
    schema = _load_bundled("default_le")
    # A representative numeric measure column resolves to the float expected dtype.
    jan = next(c for c in schema.columns if c.canonical_name == "Jan")
    assert jan.expected_dtype == "float"
