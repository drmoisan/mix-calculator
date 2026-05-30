"""Unit and property tests for :mod:`src.schema_serialization`.

Covers a positive JSON round-trip on a representative schema, descriptive
error handling for malformed JSON / missing fields / unknown keys (top-level and
nested), and a ``hypothesis`` property asserting the round-trip is lossless for
generated valid schemas. All tests are pure string transforms; no temp files,
network, or filesystem access is used.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.schema_model import (
    ColumnSpec,
    DedupPolicy,
    DerivedColumnSpec,
    FillRule,
    KeySpec,
    MeasureAggregation,
    SchemaDefinition,
)
from src.schema_serialization import (
    SchemaSerializationError,
    schema_from_json,
    schema_to_json,
)


def _representative_schema() -> SchemaDefinition:
    """Return a schema exercising every nested shape for round-trip tests.

    Returns:
        A ``SchemaDefinition`` with columns, a multi-column key, a collapse
        dedup policy with an additive measure aggregation, a derived column with
        ``copy_from``, a fill rule, and a drop column.
    """
    return SchemaDefinition(
        name="representative",
        version="1.0",
        description="exercises every nested shape",
        source_sheet_hints=("Sheet1", "Data"),
        header_row=2,
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension", aliases=("Cust",)),
            ColumnSpec(canonical_name="Type", role="discriminator"),
            ColumnSpec(canonical_name="Jan", role="measure", numeric=True),
            ColumnSpec(canonical_name="PPG", role="dimension", sentinel_clean=True),
        ),
        key=KeySpec(columns=("Customer", "Type"), sku_coercion=True),
        dedup=DedupPolicy(
            mode="collapse",
            discriminator_column="Type",
            measure_aggregations=(MeasureAggregation(measure="Jan", mode="additive"),),
        ),
        derived_columns=(DerivedColumnSpec(name="Super Category", copy_from="PPG"),),
        fill_rules=(FillRule(total="Jan", components=("Jan",)),),
        drop_columns=("Type",),
    )


def test_round_trip_is_lossless() -> None:
    """A representative schema survives a JSON round-trip unchanged."""
    # Arrange
    schema = _representative_schema()

    # Act
    restored = schema_from_json(schema_to_json(schema))

    # Assert
    assert restored == schema


def test_malformed_json_raises() -> None:
    """Non-JSON text raises a descriptive serialization error."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaSerializationError, match="malformed"):
        schema_from_json("{not valid json")


def test_missing_required_field_raises() -> None:
    """A schema object missing 'version' raises a field-named error."""
    # Arrange
    text = '{"name": "x", "key": {"columns": ["x"]}, ' '"columns": []}'

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="missing required field 'version'"
    ):
        schema_from_json(text)


def test_unknown_top_level_key_raises() -> None:
    """An unknown top-level key is rejected and named in the message."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "key": {"columns": ["x"]}, '
        '"columns": [{"canonical_name": "x", "role": "dimension"}], '
        '"bogus": 1}'
    )

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="unknown key.*bogus"):
        schema_from_json(text)


def test_unknown_nested_key_raises() -> None:
    """An unknown key inside a nested column object is rejected and named."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "key": {"columns": ["x"]}, '
        '"columns": [{"canonical_name": "x", "role": "dimension", '
        '"surprise": true}]}'
    )

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="unknown key.*surprise"):
        schema_from_json(text)


def test_root_not_object_raises() -> None:
    """A JSON value that is not an object is rejected at the root."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaSerializationError, match="must be a JSON object"):
        schema_from_json("[1, 2, 3]")


def test_string_field_wrong_type_raises() -> None:
    """A non-string value for a required string field is rejected by name."""
    # Arrange
    text = '{"name": 5, "version": "1.0", "key": {"columns": ["x"]}}'

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="field 'name' must be a string"):
        schema_from_json(text)


def test_optional_string_field_wrong_type_raises() -> None:
    """A non-string value for an optional string field is rejected by name."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "description": 7, '
        '"key": {"columns": ["x"]}}'
    )

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="field 'description' must be a string"
    ):
        schema_from_json(text)


def test_bool_field_wrong_type_raises() -> None:
    """A non-boolean value for a boolean field is rejected by name."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "key": {"columns": ["x"]}, '
        '"columns": [{"canonical_name": "x", "role": "dimension", '
        '"numeric": 1}]}'
    )

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="field 'numeric' must be a boolean"
    ):
        schema_from_json(text)


def test_int_field_wrong_type_raises() -> None:
    """A non-integer (and bool) value for header_row is rejected by name."""
    # Arrange: a boolean is explicitly not accepted for the integer field.
    text = (
        '{"name": "x", "version": "1.0", "header_row": true, '
        '"key": {"columns": ["x"]}}'
    )

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="field 'header_row' must be an integer"
    ):
        schema_from_json(text)


def test_str_tuple_field_wrong_type_raises() -> None:
    """A non-list value where a list of strings is expected is rejected."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "drop_columns": "nope", '
        '"key": {"columns": ["x"]}}'
    )

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="field 'drop_columns' must be a list of strings"
    ):
        schema_from_json(text)


def test_str_tuple_non_string_element_raises() -> None:
    """A non-string element inside a string-list field is rejected."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "drop_columns": [1], '
        '"key": {"columns": ["x"]}}'
    )

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="must contain only strings"):
        schema_from_json(text)


def test_nullable_string_wrong_type_raises() -> None:
    """A non-string, non-null value for a nullable string field is rejected."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "key": {"columns": ["x"]}, '
        '"columns": [{"canonical_name": "x", "role": "dimension"}], '
        '"derived_columns": [{"name": "d", "copy_from": 9}]}'
    )

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="field 'copy_from' must be a string or null"
    ):
        schema_from_json(text)


def test_object_list_field_not_list_raises() -> None:
    """A non-list value where a list of objects is expected is rejected."""
    # Arrange
    text = '{"name": "x", "version": "1.0", "columns": 3, "key": {"columns": ["x"]}}'

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="field 'columns' must be a list"
    ):
        schema_from_json(text)


def test_object_list_element_not_object_raises() -> None:
    """A non-object element inside an object-list field is rejected."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "columns": [5], ' '"key": {"columns": ["x"]}}'
    )

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="must be a JSON object"):
        schema_from_json(text)


def test_missing_key_field_raises() -> None:
    """A schema object with no 'key' field is rejected by name."""
    # Arrange
    text = '{"name": "x", "version": "1.0", "columns": []}'

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="missing required field 'key'"):
        schema_from_json(text)


def test_dedup_wrong_type_raises() -> None:
    """A non-object 'dedup' value is rejected as not a JSON object."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "dedup": 1, '
        '"columns": [{"canonical_name": "x", "role": "dimension"}], '
        '"key": {"columns": ["x"]}}'
    )

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="dedup must be a JSON object"):
        schema_from_json(text)


def test_full_collapse_dedup_round_trips() -> None:
    """A schema with a select_from measure and nested dedup round-trips."""
    # Arrange
    schema = SchemaDefinition(
        name="sel",
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Type", role="discriminator"),
            ColumnSpec(canonical_name="Jan", role="measure", numeric=True),
        ),
        key=KeySpec(columns=("Type",)),
        dedup=DedupPolicy(
            mode="collapse",
            discriminator_column="Type",
            measure_aggregations=(
                MeasureAggregation(
                    measure="Jan", mode="select_from", select_values=("YTD",)
                ),
            ),
        ),
    )

    # Act
    restored = schema_from_json(schema_to_json(schema))

    # Assert
    assert restored == schema


# --- Property-based round-trip (T2 requirement) ---


# Bound generated names to a small ASCII alphabet and modest length so the
# strategy stays satisfiable and column-name references remain easy to keep
# consistent; the round-trip property is independent of name content.
_NAME = st.text(alphabet="abcdefghijklmnop", min_size=1, max_size=6)


@st.composite
def _valid_schemas(draw: st.DrawFn) -> SchemaDefinition:
    """Generate a structurally valid ``SchemaDefinition``.

    The strategy guarantees ``__post_init__`` invariants hold by deriving every
    cross-reference (key columns, dedup discriminator/measures, derived
    ``copy_from``, fill-rule total/components) from the generated declared column
    names, so generation never raises ``SchemaValidationError``.

    Args:
        draw: The hypothesis draw callable.

    Returns:
        A valid ``SchemaDefinition`` instance.
    """
    # Draw a unique, ordered set of declared column names to reference from the
    # key, dedup, derived, and fill-rule sections.
    names = draw(st.lists(_NAME, min_size=1, max_size=5, unique=True))
    columns = tuple(
        ColumnSpec(
            canonical_name=name,
            role=draw(st.sampled_from(["dimension", "measure", "discriminator"])),
            required=draw(st.booleans()),
            aliases=tuple(draw(st.lists(_NAME, max_size=2))),
            numeric=draw(st.booleans()),
            sentinel_clean=draw(st.booleans()),
        )
        for name in names
    )

    # Key references at least one declared column, in declaration order.
    key_columns = tuple(
        draw(
            st.lists(
                st.sampled_from(names), min_size=1, max_size=len(names), unique=True
            )
        )
    )
    key = KeySpec(columns=key_columns, sku_coercion=draw(st.booleans()))

    # Dedup: either no collapse, or collapse with a declared discriminator and
    # additive aggregations over declared measures.
    collapse = draw(st.booleans())
    if collapse:
        discriminator = draw(st.sampled_from(names))
        measures = draw(
            st.lists(st.sampled_from(names), max_size=len(names), unique=True)
        )
        dedup = DedupPolicy(
            mode="collapse",
            discriminator_column=discriminator,
            measure_aggregations=tuple(
                MeasureAggregation(measure=measure, mode="additive")
                for measure in measures
            ),
        )
    else:
        dedup = DedupPolicy()

    # Derived columns whose copy_from (when present) references a declared column.
    derived = tuple(
        DerivedColumnSpec(
            name=draw(_NAME),
            expression=draw(st.text(max_size=8)),
            copy_from=draw(st.one_of(st.none(), st.sampled_from(names))),
        )
        for _ in range(draw(st.integers(min_value=0, max_value=2)))
    )

    # Fill rules whose total and components reference declared columns.
    fill_rules = tuple(
        FillRule(
            total=draw(st.sampled_from(names)),
            components=tuple(
                draw(st.lists(st.sampled_from(names), min_size=1, max_size=len(names)))
            ),
        )
        for _ in range(draw(st.integers(min_value=0, max_value=2)))
    )

    return SchemaDefinition(
        name=draw(_NAME),
        version=draw(_NAME),
        description=draw(st.text(max_size=8)),
        source_sheet_hints=tuple(draw(st.lists(_NAME, max_size=2))),
        header_row=draw(st.integers(min_value=0, max_value=10)),
        columns=columns,
        key=key,
        dedup=dedup,
        derived_columns=derived,
        fill_rules=fill_rules,
        drop_columns=tuple(draw(st.lists(st.sampled_from(names), max_size=len(names)))),
    )


@given(schema=_valid_schemas())
def test_round_trip_property(schema: SchemaDefinition) -> None:
    """For every generated valid schema, the JSON round-trip is lossless."""
    # Act
    restored = schema_from_json(schema_to_json(schema))

    # Assert (hypothesis prints the failing example on failure)
    assert restored == schema
