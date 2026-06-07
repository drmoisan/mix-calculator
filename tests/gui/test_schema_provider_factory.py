"""Tests for the production :class:`BuildSpecProvider` factory (R4 / AC 5).

Verifies that ``build_spec_provider`` resolves each source key to a distinct
:class:`CallerBuildSpec` carrying that source's required/optional specs, a default
key pattern rendered from the schema's structured key, and a synthetic masked
preview slice; an unmapped source (no bundled default) resolves to a blank spec.
All schemas are fabricated; no disk or network access.
"""

from __future__ import annotations

from src.gui._schema_provider_factory import build_spec_provider
from src.schema_model import (
    ColumnSpec,
    KeySpec,
    SchemaDefinition,
    column_ref,
    literal_text,
)
from tests.gui.fakes.fake_services import FakeSchemaService


def _le_schema() -> SchemaDefinition:
    """Return a fabricated LE-like schema with required and optional columns.

    Returns:
        A :class:`SchemaDefinition` with one required and one optional column and a
        two-part key interleaving a literal separator.
    """
    return SchemaDefinition(
        name="default_le",
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension", required=True),
            ColumnSpec(canonical_name="Notes", role="dimension", required=False),
        ),
        key=KeySpec(
            parts=(column_ref("Customer"), literal_text("-"), column_ref("Notes"))
        ),
    )


def _aop_schema() -> SchemaDefinition:
    """Return a fabricated AOP-like schema distinct from the LE schema.

    Returns:
        A :class:`SchemaDefinition` with a single required column and a one-part key.
    """
    return SchemaDefinition(
        name="default_aop",
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Account", role="dimension", required=True),
        ),
        key=KeySpec(parts=(column_ref("Account"),)),
    )


def _service() -> FakeSchemaService:
    """Return a fake schema service holding the LE and AOP schemas.

    Returns:
        A :class:`FakeSchemaService` with ``default_le`` and ``default_aop``.
    """
    return FakeSchemaService(
        schema_names=["default_le", "default_aop"],
        schemas={"default_le": _le_schema(), "default_aop": _aop_schema()},
    )


def test_each_key_resolves_to_a_distinct_spec() -> None:
    """The three source keys resolve to distinct, source-specific build specs."""
    # Arrange
    provider = build_spec_provider(_service())

    # Act
    le_spec = provider.build_spec_for("LE")
    aop_spec = provider.build_spec_for("aop")
    sku_spec = provider.build_spec_for("sku_lu")

    # Assert: LE and AOP carry their own required columns; the specs differ.
    le_required = tuple(c.canonical_name for c in le_spec.required_specs)
    aop_required = tuple(c.canonical_name for c in aop_spec.required_specs)
    assert le_required == ("Customer",)
    assert aop_required == ("Account",)
    assert le_spec != aop_spec
    # sku_lu has no bundled default, so it resolves to a blank spec.
    assert sku_spec.required_specs == ()
    assert sku_spec.optional_specs == ()
    assert sku_spec.preview_slice is None


def test_le_spec_splits_required_and_optional_and_renders_key_pattern() -> None:
    """The LE spec splits required/optional columns and renders the key pattern."""
    # Arrange
    provider = build_spec_provider(_service())

    # Act
    le_spec = provider.build_spec_for("LE")

    # Assert: required vs optional split is preserved, and the key pattern renders
    # the structured key (column-refs as {name}, literal verbatim, in order).
    assert tuple(c.canonical_name for c in le_spec.required_specs) == ("Customer",)
    assert tuple(c.canonical_name for c in le_spec.optional_specs) == ("Notes",)
    assert le_spec.default_key_pattern == "{Customer}-{Notes}"


def test_preview_slice_is_synthetic_and_masked() -> None:
    """The preview slice header mirrors the columns and rows are masked placeholders."""
    # Arrange
    provider = build_spec_provider(_service())

    # Act
    le_spec = provider.build_spec_for("LE")

    # Assert: the slice exists, its header is the canonical names, and every cell is
    # an obviously-synthetic "masked_*" placeholder (no real workbook value).
    slice_ = le_spec.preview_slice
    assert slice_ is not None
    assert slice_.header == ("Customer", "Notes")
    assert slice_.rows != ()
    for row in slice_.rows:
        for cell in row:
            assert isinstance(cell, str)
            assert cell.startswith("masked_")


def test_missing_schema_degrades_to_blank_spec() -> None:
    """A mapped key whose schema is missing degrades to a blank spec, not a raise."""
    # Arrange: a service with no schemas, so load_schema raises for every name.
    provider = build_spec_provider(FakeSchemaService())

    # Act
    le_spec = provider.build_spec_for("LE")

    # Assert: the open path stays blank rather than failing.
    assert le_spec.required_specs == ()
    assert le_spec.preview_slice is None


def test_real_bundled_le_ytd_ytg_is_in_optional_specs() -> None:
    """The real bundled LE schema's YTD/YTG (required:false) lands in optional specs.

    After the #54 change, the LE discriminator is required:false, so the
    provider-factory split (which keys on column.required) must place it in the
    optional specs, not the required specs (AC-7).
    """
    from pathlib import Path

    from src.schema_registry import DiskSchemaFileStore, SchemaRegistry

    # Arrange: load the real bundled LE schema and provide it to the factory under
    # the LE source key via a fake service.
    registry = SchemaRegistry(Path("."), DiskSchemaFileStore())
    bundled_le = registry.load_bundled_default("default_le")
    service = FakeSchemaService(
        schema_names=["default_le"], schemas={"default_le": bundled_le}
    )
    provider = build_spec_provider(service)

    # Act
    le_spec = provider.build_spec_for("LE")

    # Assert: YTD/YTG is optional (not required), reflecting the new flags.
    optional_names = tuple(c.canonical_name for c in le_spec.optional_specs)
    required_names = tuple(c.canonical_name for c in le_spec.required_specs)
    assert "YTD/YTG" in optional_names
    assert "YTD/YTG" not in required_names
