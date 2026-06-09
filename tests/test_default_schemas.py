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
from src.schema_serialization import schema_from_json, schema_to_json

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
    """AOP declares no fill rules; blank source totals pass through (issue #58).

    Decision 2 cleared the derived blank-total fill on the AOP import path so a
    blank total cell coerces to 0 rather than being computed from its month
    components. The schema now declares an empty fill-rule set.
    """
    # Arrange / Act
    schema = _load_bundled("default_aop")

    # Assert: the cleared-rules state replaces the prior six per-total fill rules.
    assert schema.fill_rules == ()


def test_aop_fill_rules_empty_and_header_row_two_round_trips() -> None:
    """AOP has empty fill rules and header_row 2, and round-trips losslessly.

    Verifies the issue #58 schema edits (cleared ``fill_rules`` and the
    informational ``header_row`` set to 2) and that the parsed schema serializes
    and re-parses without error, preserving both fields.
    """
    # Arrange / Act
    schema = _load_bundled("default_aop")

    # Assert: the edited fields are present on the parsed schema.
    assert schema.fill_rules == ()
    assert schema.header_row == 2

    # Act: serialize and re-parse to confirm a lossless round-trip.
    reparsed = schema_from_json(schema_to_json(schema))

    # Assert: the round-tripped schema preserves the edited fields.
    assert reparsed.fill_rules == ()
    assert reparsed.header_row == 2


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


# Canonical declared column set for SKU_LU (issue #60 Defect 2): a flat lookup of
# SKU to its description, category, and country.
_SKU_LU_COLUMNS = ["SKU", "SKU Description", "Category", "Country"]


def test_sku_lu_columns_and_order_match_canonical() -> None:
    """The SKU_LU schema declares SKU, SKU Description, Category, Country in order."""
    # Arrange / Act
    schema = _load_bundled("default_sku_lu")

    # Assert
    assert [column.canonical_name for column in schema.columns] == _SKU_LU_COLUMNS


def test_sku_lu_country_carries_international_alias() -> None:
    """The SKU_LU Country column carries the ``International`` alias (and only it)."""
    # Arrange / Act
    schema = _load_bundled("default_sku_lu")

    # Assert: Country aliases ``International``; the other columns carry no aliases.
    country = next(c for c in schema.columns if c.canonical_name == "Country")
    assert country.aliases == ("International",)
    non_country_aliases = [
        c.aliases for c in schema.columns if c.canonical_name != "Country"
    ]
    assert all(aliases == () for aliases in non_country_aliases)


def test_sku_lu_key_is_sku_without_coercion() -> None:
    """The SKU_LU key is the single SKU column with sku_coercion disabled."""
    # Arrange / Act
    schema = _load_bundled("default_sku_lu")

    # Assert
    assert schema.key.column_names == ("SKU",)
    assert schema.key.sku_coercion is False


def test_sku_lu_header_row_zero_and_no_dedup_or_transforms() -> None:
    """SKU_LU uses header_row 0, no dedup, and no derived/fill/drop transforms."""
    # Arrange / Act
    schema = _load_bundled("default_sku_lu")

    # Assert: a flat lookup — header on row 0, no collapse, no transforms.
    assert schema.header_row == 0
    assert schema.dedup.mode == "none"
    assert schema.derived_columns == ()
    assert schema.fill_rules == ()
    assert schema.drop_columns == ()


def test_sku_lu_schema_does_not_encode_country_code_value_mapping() -> None:
    """AC-6: the country-code value mapping (0->US, 1->Canada) is not in the schema.

    The country-code transform is a loader-side cell-value mapping in
    ``load_skulu`` with no representation in the schema model. This asserts the
    bundled SKU_LU schema encodes no such value mapping structurally: the
    ColumnSpec model exposes no value-map/recode attribute, the Country column's
    only metadata is the ``International`` header-matching alias (not a cell-value
    map), and the schema's structured fields (key/dedup/derived/fill/drop) carry
    no recode of the country codes. The description prose may *document* that the
    mapping stays loader-only; the structural assertions below — not a prose scan
    — are the AC-6 guard.
    """
    # Arrange / Act
    schema = _load_bundled("default_sku_lu")
    country = next(c for c in schema.columns if c.canonical_name == "Country")

    # Assert: the ColumnSpec model has no value-mapping/recode construct at all, so
    # a country-code map cannot be encoded on the column.
    value_map_attrs = ("value_map", "value_mapping", "recode", "code_map", "mapping")
    for attr in value_map_attrs:
        assert not hasattr(country, attr)
    # The only Country metadata is the header-matching alias, not a value map.
    assert country.aliases == ("International",)
    # No transform field recodes the country codes: SKU_LU is a flat lookup with no
    # derived columns, fill rules, drop columns, or dedup.
    assert schema.derived_columns == ()
    assert schema.fill_rules == ()
    assert schema.drop_columns == ()
    assert schema.dedup.mode == "none"


def test_sku_lu_is_auto_discovered_in_registry_listing() -> None:
    """AC-5: a real registry over src/schemas/ lists default_sku_lu (dropdown).

    The schema dropdown is populated from the registry's listed names. A real
    disk-backed registry scanning the packaged ``src/schemas/`` directory must
    surface ``default_sku_lu`` (alongside the existing bundled defaults) so it
    appears in the dropdown at startup, confirming auto-discovery of the new file.
    """
    from src.schema_registry import DiskSchemaFileStore, SchemaRegistry

    # Arrange: a real registry whose bundled directory is the packaged schemas dir.
    registry = SchemaRegistry(
        Path("/nonexistent-registry"),
        DiskSchemaFileStore(),
        bundled_dir=_SCHEMAS_DIR,
    )

    # Act
    listed = registry.list_schemas()

    # Assert: all three bundled defaults are auto-discovered and listed.
    assert "default_sku_lu" in listed
    assert "default_le" in listed
    assert "default_aop" in listed


@pytest.mark.parametrize("name", ["default_aop", "default_le", "default_sku_lu"])
def test_bundled_schema_parses_without_raising(name: str) -> None:
    """Each bundled schema parses into a SchemaDefinition object."""
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
