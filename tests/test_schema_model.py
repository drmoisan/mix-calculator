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
    DEDUP_MODES,
    SCHEMA_FORMAT_VERSION,
    ColumnSpec,
    DedupPolicy,
    DerivedColumnSpec,
    FillRule,
    KeyPart,
    KeySpec,
    MeasureAggregation,
    SchemaDefinition,
    SchemaValidationError,
    column_ref,
    derive_expected_dtype,
    literal_text,
)


def _key(*names: str) -> KeySpec:
    """Build a column-ref-only ``KeySpec`` from the given column names.

    Args:
        names: Canonical column names that become ordered column-ref parts.

    Returns:
        A ``KeySpec`` whose parts are column-ref parts for ``names``.
    """
    return KeySpec(parts=tuple(column_ref(name) for name in names))


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
        key=_key("Customer", "Type"),
    )

    # Assert
    assert schema.name == "minimal"
    assert schema.key.column_names == ("Customer", "Type")
    assert schema.dedup.mode == "none"


def test_empty_name_raises() -> None:
    """An empty schema name is rejected with a name-specific message."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="name must be non-empty"):
        SchemaDefinition(
            name="",
            version="1.0",
            columns=_minimal_columns(),
            key=_key(
                "Customer",
            ),
        )


def test_missing_version_raises() -> None:
    """A blank version is rejected with a version-specific message."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="version must be non-empty"):
        SchemaDefinition(
            name="x",
            version="",
            columns=_minimal_columns(),
            key=_key(
                "Customer",
            ),
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
            key=_key(
                "Nope",
            ),
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
            key=_key(
                "Customer",
            ),
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
            key=_key(
                "Customer",
            ),
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
            key=_key(
                "Customer",
            ),
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
            key=_key(
                "Customer",
            ),
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


def test_key_spec_empty_parts_raises() -> None:
    """An empty key parts tuple is rejected at KeySpec construction."""
    # Arrange / Act / Assert
    with pytest.raises(
        SchemaValidationError, match="KeySpec.parts must declare at least one"
    ):
        KeySpec(parts=())


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
            key=_key("Customer"),
            fill_rules=(FillRule(total="Ghost", components=("Jan",)),),
        )


# --- expected_dtype field (P1-T3, P1-T4, P1-T5) ---


def test_expected_dtype_valid_value_constructs() -> None:
    """A ColumnSpec with a vocabulary expected_dtype constructs cleanly."""
    # Arrange / Act
    column = ColumnSpec(canonical_name="Amount", role="measure", expected_dtype="float")

    # Assert
    assert column.expected_dtype == "float"


def test_expected_dtype_invalid_value_raises() -> None:
    """An expected_dtype outside the vocabulary is rejected by name."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="invalid expected_dtype 'decimal'"):
        ColumnSpec(canonical_name="Amount", role="measure", expected_dtype="decimal")


def test_numeric_derives_to_float_when_dtype_absent() -> None:
    """A numeric column with no explicit dtype derives an effective float dtype."""
    # Arrange
    column = ColumnSpec(canonical_name="Jan", role="measure", numeric=True)

    # Act
    effective = column.effective_dtype()

    # Assert
    assert column.expected_dtype is None
    assert effective == "float"


def test_derive_expected_dtype_prefers_explicit_over_numeric() -> None:
    """An explicit dtype wins over the legacy numeric flag in derivation."""
    # Arrange / Act
    resolved = derive_expected_dtype(numeric=True, expected_dtype="integer")

    # Assert
    assert resolved == "integer"


def test_derive_expected_dtype_returns_none_for_non_numeric() -> None:
    """A non-numeric column with no explicit dtype derives no dtype."""
    # Arrange / Act
    resolved = derive_expected_dtype(numeric=False, expected_dtype=None)

    # Assert
    assert resolved is None


# --- structured key parts (P1-T6, P1-T7, P1-T10) ---


def test_key_parts_preserve_order_and_types() -> None:
    """A mixed-part key preserves part order and distinguishes part kinds."""
    # Arrange
    parts = (column_ref("Customer"), literal_text("-"), column_ref("SKU"))

    # Act
    key = KeySpec(parts=parts)

    # Assert
    assert [part.kind for part in key.parts] == [
        "column-ref",
        "literal-text",
        "column-ref",
    ]
    assert key.column_names == ("Customer", "SKU")


def test_literal_text_part_carries_arbitrary_value() -> None:
    """A literal-text part may carry any string value, including symbols."""
    # Arrange / Act
    part = literal_text(" | ")

    # Assert
    assert part.kind == "literal-text"
    assert part.value == " | "
    assert part.is_column_ref is False


def test_column_ref_part_requires_non_empty_name() -> None:
    """A column-ref part with a blank value is rejected at construction."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="must reference a non-empty"):
        KeyPart(kind="column-ref", value="   ")


def test_key_part_invalid_kind_raises() -> None:
    """An unrecognized key-part kind is rejected by name."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="invalid kind 'separator'"):
        KeyPart(kind="separator", value="x")


def test_all_literal_key_raises() -> None:
    """A key with no column-ref part is rejected as not a business key."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="at least one column-ref part"):
        KeySpec(parts=(literal_text("a"), literal_text("b")))


# --- aggregate dedup mode (P1-T8, P1-T10) ---


def test_aggregate_mode_is_a_dedup_mode() -> None:
    """The aggregate mode is registered in DEDUP_MODES alongside the originals."""
    # Assert
    assert DEDUP_MODES == {"none", "collapse", "aggregate"}


def test_aggregate_dedup_policy_constructs_with_discriminator() -> None:
    """An aggregate DedupPolicy with a discriminator constructs cleanly."""
    # Arrange / Act
    policy = DedupPolicy(mode="aggregate", discriminator_column="Type")

    # Assert
    assert policy.mode == "aggregate"
    assert policy.discriminator_column == "Type"


def test_aggregate_without_discriminator_raises() -> None:
    """Aggregate mode without a discriminator column is rejected."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaValidationError, match="requires a discriminator_column"):
        DedupPolicy(mode="aggregate")


def test_aggregate_dedup_in_schema_validates_discriminator() -> None:
    """An aggregate schema validates its discriminator against declared columns."""
    # Arrange / Act
    schema = SchemaDefinition(
        name="agg",
        version="1.0",
        columns=_minimal_columns(),
        key=_key("Customer"),
        dedup=DedupPolicy(mode="aggregate", discriminator_column="Type"),
    )

    # Assert
    assert schema.dedup.mode == "aggregate"


# --- format version constant (P1-T9) ---


def test_schema_format_version_value() -> None:
    """The current write-format version constant is the required-output bump (3.0)."""
    # Assert
    assert SCHEMA_FORMAT_VERSION == "3.0"
