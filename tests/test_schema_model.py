"""Unit tests for the schema-definition model in :mod:`src.schema_model`.

Covers positive construction of a minimal valid ``SchemaDefinition`` and the
``__post_init__`` invariants that reject structurally inconsistent schemas with
a descriptive :class:`SchemaValidationError`. Each test follows Arrange-Act-Assert
and asserts on a specific message substring so a failure identifies the violated
invariant. No temp files, network, or filesystem access is used.
"""

from __future__ import annotations

import pytest

from src.schema_model import (
    ColumnSpec,
    DedupPolicy,
    DerivedColumnSpec,
    FillRule,
    KeySpec,
    MeasureAggregation,
    SchemaDefinition,
    SchemaValidationError,
)


def _minimal_columns() -> tuple[ColumnSpec, ...]:
    """Return a small declared-column set reused across the model tests.

    Returns:
        A tuple of three ``ColumnSpec`` columns: a ``Customer`` dimension, a
        numeric ``Jan`` measure, and a ``Type`` dimension.
    """
    return (
        ColumnSpec(canonical_name="Customer", role="dimension"),
        ColumnSpec(canonical_name="Jan", role="measure", numeric=True),
        ColumnSpec(canonical_name="Type", role="dimension"),
    )


def test_minimal_schema_constructs() -> None:
    """A minimal valid schema with consistent references constructs cleanly."""
    # Arrange
    columns = _minimal_columns()

    # Act
    schema = SchemaDefinition(
        name="minimal",
        version="1.0",
        columns=columns,
        key=KeySpec(columns=("Customer", "Type")),
    )

    # Assert
    assert schema.name == "minimal"
    assert schema.key.columns == ("Customer", "Type")
    assert schema.dedup.mode == "none"


def test_empty_name_raises() -> None:
    """An empty schema name is rejected with a name-specific message."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="name must be non-empty"):
        SchemaDefinition(
            name="",
            version="1.0",
            columns=_minimal_columns(),
            key=KeySpec(columns=("Customer",)),
        )


def test_missing_version_raises() -> None:
    """A blank version is rejected with a version-specific message."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="version must be non-empty"):
        SchemaDefinition(
            name="x",
            version="",
            columns=_minimal_columns(),
            key=KeySpec(columns=("Customer",)),
        )


def test_key_references_undeclared_column_raises() -> None:
    """A key column that names an undeclared column is rejected by name."""
    # Arrange / Act / Assert
    with pytest.raises(
        SchemaValidationError, match="KeySpec references undeclared column 'Nope'"
    ):
        SchemaDefinition(
            name="x",
            version="1.0",
            columns=_minimal_columns(),
            key=KeySpec(columns=("Nope",)),
        )


def test_derived_copy_from_undeclared_raises() -> None:
    """A derived column copying from an undeclared column is rejected by name."""
    # Arrange / Act / Assert
    with pytest.raises(
        SchemaValidationError, match="copy_from references undeclared column 'Ghost'"
    ):
        SchemaDefinition(
            name="x",
            version="1.0",
            columns=_minimal_columns(),
            key=KeySpec(columns=("Customer",)),
            derived_columns=(DerivedColumnSpec(name="Derived", copy_from="Ghost"),),
        )


def test_fill_rule_references_undeclared_column_raises() -> None:
    """A fill rule whose component is undeclared is rejected by name."""
    # Arrange / Act / Assert
    with pytest.raises(
        SchemaValidationError, match="references undeclared component column 'Feb'"
    ):
        SchemaDefinition(
            name="x",
            version="1.0",
            columns=_minimal_columns(),
            key=KeySpec(columns=("Customer",)),
            fill_rules=(FillRule(total="Jan", components=("Feb",)),),
        )


def test_dedup_measure_aggregation_undeclared_raises() -> None:
    """A dedup aggregation naming an undeclared measure is rejected by name."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="undeclared measure 'Mar'"):
        SchemaDefinition(
            name="x",
            version="1.0",
            columns=_minimal_columns(),
            key=KeySpec(columns=("Customer",)),
            dedup=DedupPolicy(
                mode="collapse",
                discriminator_column="Type",
                measure_aggregations=(MeasureAggregation(measure="Mar"),),
            ),
        )


def test_collapse_without_discriminator_raises() -> None:
    """Collapse mode without a discriminator column is rejected at DedupPolicy."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="requires a discriminator_column"):
        DedupPolicy(mode="collapse")


def test_collapse_with_undeclared_discriminator_raises() -> None:
    """Collapse mode with an undeclared discriminator is rejected by name."""
    # Arrange / Act / Assert
    with pytest.raises(
        SchemaValidationError,
        match="discriminator_column 'Missing' is not a declared column",
    ):
        SchemaDefinition(
            name="x",
            version="1.0",
            columns=_minimal_columns(),
            key=KeySpec(columns=("Customer",)),
            dedup=DedupPolicy(mode="collapse", discriminator_column="Missing"),
        )


def test_column_spec_empty_name_raises() -> None:
    """A blank column canonical_name is rejected at ColumnSpec construction."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="canonical_name must be non-empty"):
        ColumnSpec(canonical_name="  ", role="dimension")


def test_column_spec_invalid_role_raises() -> None:
    """An unrecognized column role is rejected with the offending value named."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="invalid role 'bogus'"):
        ColumnSpec(canonical_name="X", role="bogus")


def test_measure_aggregation_empty_measure_raises() -> None:
    """A blank measure name is rejected at MeasureAggregation construction."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="measure must be non-empty"):
        MeasureAggregation(measure="")


def test_measure_aggregation_invalid_mode_raises() -> None:
    """An unrecognized aggregation mode is rejected by name."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="invalid mode 'avg'"):
        MeasureAggregation(measure="Jan", mode="avg")


def test_measure_aggregation_select_from_without_values_raises() -> None:
    """select_from mode without select_values is rejected."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="declares no select_values"):
        MeasureAggregation(measure="Jan", mode="select_from")


def test_dedup_policy_invalid_mode_raises() -> None:
    """An unrecognized dedup mode is rejected by name."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="invalid mode 'merge'"):
        DedupPolicy(mode="merge")


def test_derived_column_empty_name_raises() -> None:
    """A blank derived column name is rejected at construction."""
    # Arrange / Act / Assert
    with pytest.raises(
        SchemaValidationError, match="DerivedColumnSpec.name must be non-empty"
    ):
        DerivedColumnSpec(name="")


def test_key_spec_empty_columns_raises() -> None:
    """An empty key column tuple is rejected at KeySpec construction."""
    # Arrange / Act / Assert
    with pytest.raises(
        SchemaValidationError, match="KeySpec.columns must declare at least one"
    ):
        KeySpec(columns=())


def test_fill_rule_empty_total_raises() -> None:
    """A blank fill-rule total is rejected at FillRule construction."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="FillRule.total must be non-empty"):
        FillRule(total="", components=("Jan",))


def test_fill_rule_empty_components_raises() -> None:
    """A fill rule with no components is rejected at construction."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="must declare components"):
        FillRule(total="YTD", components=())


def test_fill_rule_undeclared_total_raises() -> None:
    """A fill rule whose total names an undeclared column is rejected by name."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="undeclared total column 'Ghost'"):
        SchemaDefinition(
            name="x",
            version="1.0",
            columns=_minimal_columns(),
            key=KeySpec(columns=("Customer",)),
            fill_rules=(FillRule(total="Ghost", components=("Jan",)),),
        )
